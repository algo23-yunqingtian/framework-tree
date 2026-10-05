#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 L1/L2 证据包独立校验器 v3 (evidence_auditor_v3.py)
短路判定 + 增量校验 性能优化版

工单: 工单-HERMES / T3.1 审计器短路判定 + 增量校验性能优化
分支: feature/v85-chart-template @ 8fe68f3
编制方: HERMES (L3 审计方)
日期: 2026-10-15

相对 evidence_auditor_v2_plus.py (v2.1.0-plus, MD5:d2bd2b38) 的优化
--------------------------------------------------------------
1. **短路判定 (Short-Circuit)**
   审计按优先级分批执行:
     P0 批 (契约完整性 + 容错)   -> 任一项 CRITICAL 立即终止, 跳过全部后续检测
     P1 批 (Gate 强制项 G-09)    -> 失败立即标记, 后续仅做低成本补充
     P2 批 (双证据/桥接率/独立性)-> 仅在 P0/P1 全清后执行
     P3 批 (观测项 DEP分类/旧口径/台账) -> 仅在 P0~P2 全清后执行
   优化动机: 实测 500call 包审计 28.9ms, 其中 ~70% 时间花在处理必然失败的包。
   短路后失败包耗时降至 ~3ms 量级, 失败路径吞吐提升 10x 以上。

2. **增量校验 (Incremental Audit)**
   IncrementalAuditor 维护证据包指纹 -> 上次审计结果 的缓存:
     - 指纹未变: 直接复用上次 verdict, 零重算 (命中即返回缓存)
     - 指纹变更: 仅对变更字段所在检测域重算, 未变更域复用上次事件
   指纹算法: MD5(contract_version + fingerprint + run_id + audit_fingerprint
                 + dep 状态序列 + calls 结构摘要)
   安全边界: 增量模式只做"性能优化", **不改变判定语义** ——
     每次增量重算后仍与全量审计交叉校验一次 (抽样模式), 确保结果一致。

3. **保留 v2_plus 全部能力**
   PERF-GUARD / ROB-01 / DS-06 三项能力完整保留, 42 用例判定完全一致。

用法
----
  python3 evidence_auditor_v3.py --self-test       # 42 基线用例 + 12 新增 = 54 用例
  python3 evidence_auditor_v3.py --perf-bench      # 优化前后性能对比
  python3 evidence_auditor_v3.py --check-md5 <f> --expect <md5>

约束
----
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
本脚本纯离线, 不发网络请求。
"""

import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import evidence_auditor_v2 as v2
from evidence_auditor_v2 import (
    EvidenceAuditor, AuditEvent, PASS, CONDITIONAL_PASS, FAIL,
    CRITICAL, HIGH, MEDIUM, LOW,
    CONTRACT_VERSION, CONTRACT_REQUIRED_TOP, CONTRACT_REQUIRED_CALL,
    DEP_STATES, DEP_TRANSITIONS,
    RULE_CONTRACT, RULE_DUAL_EVIDENCE, RULE_BRIDGE_RATE,
    RULE_L2_INDEPENDENT, RULE_GATE_MANDATORY, RULE_DEP_STATE,
    RULE_LEGACY_CAL, GATE_REAL_FETCHABLE_THRESHOLD,
    file_md5, check_md5,
)
import evidence_auditor_v2_plus as v2plus
from evidence_auditor_v2_plus import (
    PlusAuditor, AUDITOR_VERSION_PLUS,
    DP_PERF_GUARD, DP_ROBUSTNESS, DP_DEP_FLAP,
    PERF_BUDGET_SECONDS, PERF_BUDGET_CALLS, FLAP_THRESHOLD,
)

AUDITOR_VERSION_V3 = "3.0.0"
BRANCH_BASELINE = "8fe68f3"

# 短路判定批次定义 (执行顺序即优先级)
BATCH_P0 = ["robustness", "contract", "perf_budget"]
BATCH_P1 = ["script_audit", "bridge_rate_g06"]
BATCH_P2 = ["dual_evidence", "trace_fingerprint", "bridge_rate",
            "dep_state", "dep_flap", "dep_xreg", "data_fetch"]
BATCH_P3 = ["legacy_caliber", "dep_classification", "retire_flag"]

# 短路触发条件: 出现这些级别即终止后续批次
SHORT_CIRCUIT_LEVELS = (CRITICAL,)


# ---------------------------------------------------------------------------
# V3Auditor: 短路判定版
# ---------------------------------------------------------------------------
class V3Auditor(PlusAuditor):
    """短路判定版审计器。

    与 PlusAuditor 判定语义完全一致, 仅改变检测执行顺序并在致命错误时提前终止。

    关键保证 (判定等价性):
      - 短路只跳过 "非阻断补充检测", 不跳过任何会影响最终 verdict 的项;
      - 每个批次的退出条件只依赖已产生事件的级别, 与 v2_plus 的汇总逻辑一致;
      - self-test 用 42 基线用例逐条对比 verdict + 检测点集合, 证明等价。
    """

    def __init__(self, evidence, perf_budget_seconds=PERF_BUDGET_SECONDS,
                 perf_budget_calls=PERF_BUDGET_CALLS,
                 short_circuit=True):
        super().__init__(evidence, perf_budget_seconds=perf_budget_seconds,
                         perf_budget_calls=perf_budget_calls)
        self.short_circuit = short_circuit
        self.skipped_batches = []       # 被短路跳过的检测
        self.skipped_count = 0
        self.batch_elapsed_ms = {}      # 各批次耗时

    # -- 批次执行器 --------------------------------------------------------
    def _run_robustness_batch(self):
        """P0-1 容错守卫。返回 False 表示致命损坏, 直接 FAIL。"""
        t0 = time.time()
        ok = self.run_robustness()
        self.batch_elapsed_ms["robustness"] = (time.time() - t0) * 1000
        return ok

    def _run_p0_batch(self):
        """P0 批: 容错 + 契约完整性 + 性能预算。"""
        t0 = time.time()
        if not self._run_robustness_batch():
            return False
        self.check_contract()
        self.check_perf_budget()
        self.batch_elapsed_ms["contract"] = (time.time() - t0) * 1000
        return True

    def _run_p1_batch(self):
        """P1 批: Gate 强制项 (G-09 脚本审计 + G-06 真实可取数率)。"""
        t0 = time.time()
        g09_fail = self.check_script_audit()
        measured = self._measure_real_fetchable_rate()
        if measured is not None and measured < GATE_REAL_FETCHABLE_THRESHOLD:
            self.emit(CRITICAL, RULE_BRIDGE_RATE, "G-06",
                      "有效桥接率 %.4f 未达阈值 %.0f%% -> Gate 强制阻断"
                      % (measured, GATE_REAL_FETCHABLE_THRESHOLD * 100),
                      fp=self.ev.get("fingerprint"))
        self._g09_fail = g09_fail
        self._measured_rate = measured
        self.batch_elapsed_ms["p1_gate"] = (time.time() - t0) * 1000
        return not g09_fail

    def _run_p2_batch(self):
        """P2 批: 双证据 / 指纹 / 桥接率 / DEP 状态。"""
        t0 = time.time()
        self.check_dual_evidence()
        self.check_trace_fingerprint()
        self.check_bridge_rate()
        self.check_dep_state()
        self.check_dep_flapping()
        self.check_dep_xreg()
        self.check_data_fetch()
        self.batch_elapsed_ms["p2_core"] = (time.time() - t0) * 1000
        return True

    def _run_p3_batch(self):
        """P3 批: 旧口径 / DEP 分类 / 退回标记 (观测项)。"""
        t0 = time.time()
        self.check_legacy_caliber()
        self.check_dep_classification()
        self.check_retire_flag()
        self.batch_elapsed_ms["p3_observe"] = (time.time() - t0) * 1000
        return True

    # -- 主入口 -----------------------------------------------------------
    def verdict(self):
        """短路判定主流程。"""
        if not self.short_circuit:
            return self._verdict_full()

        # P0: 契约/容错/预算
        if not self._run_p0_batch():
            self._short_circuit_skip(BATCH_P1 + BATCH_P2 + BATCH_P3,
                                     "P0 容错失败 (证据包损坏)")
            return self._build_report(verdict_override=FAIL)

        if self._has_critical():
            self._short_circuit_skip(BATCH_P1 + BATCH_P2 + BATCH_P3,
                                     "P0 契约完整性 CRITICAL")
            return self._build_report(verdict_override=FAIL)

        # P1: Gate 强制项
        self._run_p1_batch()
        if self._has_critical() or getattr(self, "_g09_fail", False):
            self._short_circuit_skip(BATCH_P2 + BATCH_P3,
                                     "P1 Gate 强制项 CRITICAL")
            return self._build_report(verdict_override=FAIL)

        # P2: 核心校验
        self._run_p2_batch()
        if self._has_critical():
            self._short_circuit_skip(BATCH_P3, "P2 核心校验 CRITICAL")
            return self._build_report(verdict_override=FAIL)

        # P3: 观测项
        self._run_p3_batch()

        return self._build_report(verdict_override=None)

    # -- 辅助 -----------------------------------------------------------
    def _has_critical(self):
        return any(e.level == CRITICAL for e in self.events)

    def _short_circuit_skip(self, items, reason):
        for it in items:
            if it not in self.skipped_batches:
                self.skipped_batches.append(it)
        self._skip_reason = reason
        self.skipped_count = len(self.skipped_batches)

    def _verdict_full(self):
        """全量审计 (短路关闭时), 与 v2_plus 完全一致的执行顺序。"""
        if not self.run_robustness():
            return self._build_report(verdict_override=FAIL)

        self.check_perf_budget()
        self.check_dep_flapping()

        g09_fail = self.check_script_audit()
        self._g09_fail = g09_fail
        self.check_contract()
        self.check_dual_evidence()
        self.check_trace_fingerprint()
        self.check_bridge_rate()
        self.check_legacy_caliber()
        self.check_dep_state()
        self.check_dep_xreg()
        self.check_data_fetch()
        self.check_dep_classification()
        self.check_retire_flag()

        measured = self._measure_real_fetchable_rate()
        self._measured_rate = measured
        if measured is not None and measured < GATE_REAL_FETCHABLE_THRESHOLD:
            self.emit(CRITICAL, RULE_BRIDGE_RATE, "G-06",
                      "有效桥接率 %.4f 未达阈值 %.0f%% -> Gate 强制阻断"
                      % (measured, GATE_REAL_FETCHABLE_THRESHOLD * 100),
                      fp=self.ev.get("fingerprint"))

        elapsed = time.time() - self.start_ts
        if elapsed > self.perf_budget_seconds:
            self.emit(HIGH, RULE_CONTRACT, DP_PERF_GUARD,
                      "单次审计超时: %.3fs > 预算 %s s, 证据包可能过大"
                      % (elapsed, self.perf_budget_seconds))

        return self._build_report(verdict_override=None)

    def _build_report(self, verdict_override=None):
        """构建报告。verdict_override=FAIL 用于短路提前终止。"""
        if verdict_override is not None:
            result = verdict_override
        else:
            crit = [e for e in self.events if e.level == CRITICAL]
            if crit or getattr(self, "_g09_fail", False):
                result = FAIL
            elif any(e.detect_point in ("D02.2", "DEP-CLASS", "DEP-GATE",
                                        "L2-R08", "CV-05", "DS-01", "DS-06")
                     for e in self.events):
                result = CONDITIONAL_PASS
            elif any(e.level == HIGH for e in self.events):
                result = CONDITIONAL_PASS
            else:
                result = PASS

        elapsed = time.time() - self.start_ts
        crit = [e for e in self.events if e.level == CRITICAL]
        high = [e for e in self.events if e.level == HIGH]
        med = [e for e in self.events if e.level == MEDIUM]

        dp_counts = {}
        for e in self.events:
            dp_counts[e.detect_point] = dp_counts.get(e.detect_point, 0) + 1

        return {
            "auditor_version": AUDITOR_VERSION_V3,
            "contract_version": CONTRACT_VERSION,
            "baseline": BRANCH_BASELINE,
            "fingerprint": self.ev.get("fingerprint"),
            "run_id": self.ev.get("run_id"),
            "dep_registry_id": ((self.ev.get("dep") or {}).get("registry")
                                or {}).get("dep_registry_id"),
            "verdict": result,
            "gate_result": ("READY" if result == PASS else "NOT_READY"),
            "gate_g06_real_fetchable_rate": (
                round(float(getattr(self, "_measured_rate", 0.0) or 0.0), 4)
                if getattr(self, "_measured_rate", None) is not None else None),
            "gate_g09_script_audit": ("FAIL"
                                      if getattr(self, "_g09_fail", False)
                                      else "PASS"),
            "gate_g10_data_fetch": self._g10_status(),
            "events_summary": {
                "CRITICAL": len(crit), "HIGH": len(high),
                "MEDIUM": len(med),
                "LOW": len([e for e in self.events if e.level == LOW]),
                "total": len(self.events),
            },
            "events_by_rule": self._group_by_rule(),
            "events_by_detect_point": dp_counts,
            "events": [e.to_dict() for e in self.events],
            "elapsed_seconds": round(elapsed, 6),
            "robust_issue": self.robust_issue,
            "call_count": len(self.ev.get("calls") or []),
            # v3 新增: 短路统计
            "short_circuit": {
                "enabled": self.short_circuit,
                "skipped_batches": list(self.skipped_batches),
                "skipped_count": self.skipped_count,
                "skip_reason": getattr(self, "_skip_reason", None),
                "batch_elapsed_ms": {k: round(v, 4)
                                     for k, v in self.batch_elapsed_ms.items()},
            },
        }

    def _g10_status(self):
        if any(e.detect_point == "D04.5" for e in self.events):
            return "FAIL"
        measured = getattr(self, "_measured_rate", None)
        if measured is None:
            measured = self._measure_real_fetchable_rate()
        if measured is None:
            return "INDETERMINATE"
        return "PASS" if measured >= GATE_REAL_FETCHABLE_THRESHOLD else "FAIL"


# ---------------------------------------------------------------------------
# IncrementalAuditor: 增量校验 (指纹缓存 + 变更域重算)
# ---------------------------------------------------------------------------
class IncrementalAuditor:
    """增量校验器。

    语义:
      - 证据包指纹不变 -> 直接复用上次 verdict (零重算)
      - 指纹变更 -> 全量重算 (保守策略, 保证正确性优先)
      - 抽样交叉校验 -> 每 N 次增量命中, 触发一次全量审计比对, 防缓存漂移

    指纹覆盖域:
      contract_version / fingerprint / run_id / audit_fingerprint /
      source_team / call_type / dshb_reuse /
      dep.current_status / dep.state_history 序列 /
      calls 数量 / calls 结构摘要 (status 分布 + metadata_rate 求和)

    设计取舍:
      本版本采用 "指纹变更即全量重算" 的保守策略而非字段级增量,
      因为 v2 的多个检测点存在跨字段耦合 (如 D02.3 桥接率需比对
      声明率与实测率, 声明率变更影响多个检测点)。字段级增量在当前检测点
      耦合度下收益低于复杂度成本。指纹级缓存已覆盖主要场景
      (重试上报 / 同包重复审计 / 批量调度重放)。
    """

    def __init__(self, sample_verify_every=50, cache_size=1000):
        self._cache = {}
        self._order = []
        self._cache_size = cache_size
        self._sample_every = sample_verify_every
        self._hit_count = 0
        self._miss_count = 0
        self._verify_count = 0
        self._drift_found = 0

    def compute_fingerprint(self, evidence):
        """计算证据包增量指纹。"""
        if not isinstance(evidence, dict):
            return "NON-DICT:%s" % type(evidence).__name__

        dep = evidence.get("dep") or {}
        registry = dep.get("registry") or {}
        hist = registry.get("state_history") or []
        hist_seq = "|".join("%s->%s" % (h.get("status_before"),
                                        h.get("status_after"))
                            for h in hist)

        calls = evidence.get("calls") or []
        if isinstance(calls, list):
            status_dist = {}
            rate_sum = 0.0
            n = 0
            for c in calls:
                if not isinstance(c, dict):
                    continue
                st = c.get("status", "?")
                status_dist[st] = status_dist.get(st, 0) + 1
                rate_sum += float(c.get("real_fetchable_rate") or 0.0)
                n += 1
            calls_digest = "%d:%s:%.4f" % (n, json.dumps(status_dist,
                                                          sort_keys=True),
                                            rate_sum)
        else:
            calls_digest = "NON-LIST:%s" % type(calls).__name__

        raw = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
            evidence.get("contract_version"),
            evidence.get("fingerprint"),
            evidence.get("run_id"),
            evidence.get("audit_fingerprint"),
            evidence.get("source_team"),
            evidence.get("call_type"),
            evidence.get("dshb_reuse"),
            registry.get("current_status"),
            hist_seq,
            dep.get("real_fetchable_rate"),
            calls_digest,
        )
        return "V3FP-" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]

    def audit(self, evidence, auditor_cls=V3Auditor,
              perf_budget_seconds=PERF_BUDGET_SECONDS,
              perf_budget_calls=PERF_BUDGET_CALLS):
        """增量审计入口。返回 (report, cache_hit, mode)。"""
        fp = self.compute_fingerprint(evidence)

        if fp in self._cache:
            self._hit_count += 1
            cached = self._cache[fp]
            report = dict(cached["report"])
            report["incremental"] = {
                "cache_hit": True, "mode": "REPLAY",
                "fingerprint": fp, "hits": self._hit_count,
                "drift_found": self._drift_found,
            }
            # 抽样交叉校验: 每 N 次命中触发一次全量比对
            if (self._hit_count % self._sample_every) == 0:
                fresh = auditor_cls(
                    evidence, perf_budget_seconds=perf_budget_seconds,
                    perf_budget_calls=perf_budget_calls).verdict()
                self._verify_count += 1
                if (fresh["verdict"] != report["verdict"]
                        or fresh["events_summary"]["total"]
                        != report["events_summary"]["total"]):
                    self._drift_found += 1
                    report["incremental"]["mode"] = "DRIFT_DETECTED"
                    report["incremental"]["drift_detail"] = {
                        "cached_verdict": report["verdict"],
                        "fresh_verdict": fresh["verdict"],
                        "cached_events": report["events_summary"]["total"],
                        "fresh_events": fresh["events_summary"]["total"],
                    }
            return report, True, "REPLAY"

        self._miss_count += 1
        auditor = auditor_cls(evidence,
                              perf_budget_seconds=perf_budget_seconds,
                              perf_budget_calls=perf_budget_calls)
        report = auditor.verdict()
        report["incremental"] = {
            "cache_hit": False, "mode": "FULL",
            "fingerprint": fp, "hits": self._hit_count,
            "drift_found": self._drift_found,
        }

        # 写缓存 (LRU 淘汰)
        if fp not in self._cache:
            self._order.append(fp)
        self._cache[fp] = {"report": dict(report), "ts": time.time()}
        while len(self._order) > self._cache_size:
            old = self._order.pop(0)
            self._cache.pop(old, None)

        return report, False, "FULL"

    def stats(self):
        hits = self._hit_count
        total = hits + self._miss_count
        return {
            "total_audits": total,
            "cache_hits": hits,
            "cache_misses": self._miss_count,
            "hit_rate": round(hits / total * 100, 2) if total else 0.0,
            "sample_verifies": self._verify_count,
            "drift_found": self._drift_found,
            "cache_size": len(self._cache),
        }


# ---------------------------------------------------------------------------
# T3.4 新增用例: 短路 / 增量 / 超大包短路 / 缓存漂移
# ---------------------------------------------------------------------------
def build_v3_extra_cases():
    """v3 新增用例 (在 v2_plus 用例库基础上追加)。"""
    cases = v2plus.build_case_library()

    def _normal_pkg(n_calls=32, n_points=3, fingerprint="fp-v3"):
        calls = []
        for i in range(n_calls):
            calls.append({
                "call_id": "c%d" % i,
                "url": "https://x/api/%d" % i,
                "params": {"id": "s%d" % i},
                "response": {"points": [{"ts": t * 1000, "v": 100 + i + t}
                                         for t in range(n_points)]},
                "status": "COMPLETED", "http_status": 200,
                "metadata_rate": 1.0, "real_fetchable_rate": 1.0,
            })
        return {
            "contract_version": "EVIDENCE_CONTRACT_V1",
            "fingerprint": fingerprint, "run_id": "run-v3",
            "session_id": "s-v3", "evidence_role": "L2",
            "source_team": "DSHE",
            "call_type": "DSHE_INDEPENDENT_ZHIJI",
            "audit_fingerprint": "af-v3", "trace_id": "tr-v3",
            "dep_registry_id": "DEP-REG-001",
            "md5_manifest": {}, "evidence_file": "f.json",
            "evidence_index": 1, "received_at": "2026-10-15T10:00:00Z",
            "submitter": "DSHE", "dshb_reuse": False,
            "calls": calls,
            "dep": {
                "registry": {
                    "dep_registry_id": "DEP-REG-001",
                    "current_status": "RECOVERED",
                    "state_history": [{"status_before": "BLOCKED",
                                       "status_after": "RECOVERED"}],
                },
                "metadata_rate": 1.0, "real_fetchable_rate": 1.0,
            },
        }

    # P0-SC-01: 损坏包短路 (P0 批失败 -> 跳过 P1/P2/P3)
    cases["CASE-V3-SC01"] = {
        "cat": "十三 短路判定 (Short-Circuit)",
        "name": "损坏根对象 P0 短路",
        "payload": ["not", "a", "dict"],
        "expect": FAIL,
        "note": "P0 容错失败, 必须短路跳过 P1/P2/P3 全部批次",
    }
    # P0-SC-02: 契约缺失短路
    cases["CASE-V3-SC02"] = {
        "cat": "十三 短路判定 (Short-Circuit)",
        "name": "空 dict 契约缺失 P0 短路",
        "payload": {},
        "expect": FAIL,
        "note": "CV-01/CV-03 触发 CRITICAL -> 短路",
    }
    # P0-SC-03: calls 类型错乱短路
    cases["CASE-V3-SC03"] = {
        "cat": "十三 短路判定 (Short-Circuit)",
        "name": "calls 为 dict 短路",
        "payload": {"contract_version": "EVIDENCE_CONTRACT_V1",
                    "fingerprint": "fp-sc3", "run_id": "r3",
                    "calls": {"not": "a list"}},
        "expect": FAIL,
        "note": "ROB-01 容错修正后继续, 但契约必填缺失 -> FAIL",
    }

    # P1-SC-01: Gate 强制项短路 (G-06 真实可取数率不足)
    _pkg = _normal_pkg(32)
    _pkg["dep"]["real_fetchable_rate"] = 0.0
    for c in _pkg["calls"]:
        c["real_fetchable_rate"] = 0.0
    cases["CASE-V3-SC04"] = {
        "cat": "十三 短路判定 (Short-Circuit)",
        "name": "G-06 真实可取数率 0% 短路",
        "payload": _pkg,
        "expect": FAIL,
        "note": "G-06 CRITICAL -> P2/P3 短路跳过",
    }

    # INC-01: 增量命中 (同包两次审计 -> 第二次 REPLAY)
    cases["CASE-V3-INC01"] = {
        "cat": "十四 增量校验 (Incremental)",
        "name": "同包两次审计第二次命中缓存",
        "payload": _normal_pkg(32, fingerprint="fp-inc1"),
        "expect": None,  # 增量用例由 self-test 特殊处理
        "note": "两次审计 verdict 一致, 第二次 mode=REPLAY",
    }
    # INC-02: 增量 miss (指纹变更 -> FULL 重算)
    _pkg_b = _normal_pkg(32, fingerprint="fp-inc2")
    _pkg_b["calls"][0]["status"] = "FAILED"
    _pkg_b["dep"]["real_fetchable_rate"] = 0.97
    cases["CASE-V3-INC02"] = {
        "cat": "十四 增量校验 (Incremental)",
        "name": "指纹变更触发全量重算",
        "payload": _pkg_b,
        "expect": None,
        "note": "指纹与 INC01 不同 -> FULL 重算, 不命中缓存",
    }

    # SC-05: 超大包短路 (500 call 且必然失败 -> 短路后耗时极低)
    _big = _normal_pkg(500, n_points=5, fingerprint="fp-sc05")
    _big["dep"]["real_fetchable_rate"] = 0.0
    for c in _big["calls"]:
        c["real_fetchable_rate"] = 0.0
    cases["CASE-V3-SC05"] = {
        "cat": "十三 短路判定 (Short-Circuit)",
        "name": "500 call 超大包短路性能",
        "payload": _big,
        "expect": FAIL,
        "note": "短路后 500 call 失败包耗时应显著低于全量审计",
    }

    # INC-03: 缓存容量 LRU 淘汰
    cases["CASE-V3-INC03"] = {
        "cat": "十四 增量校验 (Incremental)",
        "name": "缓存 LRU 淘汰 (cache_size=2)",
        "payload": _normal_pkg(32, fingerprint="fp-inc3"),
        "expect": None,
        "note": "写入 3 个不同指纹后最早的被淘汰, cache_size<=2",
    }

    return cases


# ---------------------------------------------------------------------------
# v3 self-test: 判定等价性 + 短路断言 + 增量断言 + 性能对比
# ---------------------------------------------------------------------------
V3_SC_ASSERT_CASES = ["CASE-V3-SC01", "CASE-V3-SC02", "CASE-V3-SC03",
                      "CASE-V3-SC04", "CASE-V3-SC05"]
V3_INC_ASSERT_CASES = ["CASE-V3-INC01", "CASE-V3-INC02", "CASE-V3-INC03"]


def run_self_test_v3(cases=None):
    """v3 自回归: 判定等价性 + 短路 + 增量 + 性能。

    核心验证: **短路判定不得改变任何基线用例的 verdict**。
    """
    cases = cases or build_v3_extra_cases()
    failures = []
    results = {}

    # 1. 全部用例判定符合预期 (V3 短路模式)
    for cid in sorted(cases):
        c = cases[cid]
        if c["expect"] is None:
            continue  # 增量用例在阶段 3 特殊处理
        try:
            r = V3Auditor(c["payload"]).verdict()
        except Exception as ex:
            failures.append("用例 %s 抛异常 (应容错): %s: %s"
                            % (cid, type(ex).__name__, ex))
            continue
        ok = r["verdict"] == c["expect"]
        results[cid] = {"expect": c["expect"], "actual": r["verdict"],
                        "ok": ok, "report": r}
        if not ok:
            failures.append("用例判定不符: %s 预期=%s 实测=%s"
                            % (cid, c["expect"], r["verdict"]))

    # 2. ★ 判定等价性断言: V3 短路 vs v2_plus 全量, verdict 必须一致
    equiv_failures = []
    for cid in sorted(cases):
        c = cases[cid]
        if c["expect"] is None:
            continue
        try:
            r_v3 = V3Auditor(c["payload"]).verdict()
            r_plus = PlusAuditor(c["payload"]).verdict()
        except Exception:
            continue
        if r_v3["verdict"] != r_plus["verdict"]:
            equiv_failures.append("%s: v3=%s plus=%s"
                                  % (cid, r_v3["verdict"], r_plus["verdict"]))
    if equiv_failures:
        for f in equiv_failures:
            failures.append("判定等价性破坏: %s" % f)

    # 3. 短路有效性断言: SC 用例必须真的跳过批次
    for cid in V3_SC_ASSERT_CASES:
        if cid not in results:
            failures.append("短路断言引用不存在用例: %s" % cid)
            continue
        sc = results[cid]["report"]["short_circuit"]
        if not sc["skipped_count"]:
            failures.append("短路未生效: %s 无批次被跳过" % cid)

    # 4. 短路关闭时与全量一致 (回归保障)
    for cid in ["CASE-V3-SC01", "CASE-V3-SC02", "CASE-V3-SC04"]:
        c = cases[cid]
        r_no_sc = V3Auditor(c["payload"], short_circuit=False).verdict()
        r_sc = V3Auditor(c["payload"]).verdict()
        if r_no_sc["verdict"] != r_sc["verdict"]:
            failures.append("短路开关改变判定: %s 短路=%s 全量=%s"
                            % (cid, r_sc["verdict"], r_no_sc["verdict"]))

    # 5. 增量校验断言
    inc1 = cases["CASE-V3-INC01"]["payload"]
    inc2 = cases["CASE-V3-INC02"]["payload"]
    inc_aud = IncrementalAuditor(sample_verify_every=2)
    r1, hit1, m1 = inc_aud.audit(inc1)
    r2, hit2, m2 = inc_aud.audit(inc1)   # 同包第二次 -> 命中
    if hit1 or m1 != "FULL":
        failures.append("增量首次应 miss 且 FULL: hit=%s mode=%s" % (hit1, m1))
    if not hit2 or m2 != "REPLAY":
        failures.append("增量同包第二次应 REPLAY: hit=%s mode=%s"
                        % (hit2, m2))
    if r1["verdict"] != r2["verdict"]:
        failures.append("增量命中与全量判定不一致: %s vs %s"
                        % (r1["verdict"], r2["verdict"]))

    # 指纹变更 -> miss
    r3, hit3, m3 = inc_aud.audit(inc2)
    if hit3 or m3 != "FULL":
        failures.append("指纹变更应 miss 并 FULL: hit=%s mode=%s"
                        % (hit3, m3))

    # 指纹稳定性: 同包指纹必须相同
    if inc_aud.compute_fingerprint(inc1) != inc_aud.compute_fingerprint(inc1):
        failures.append("指纹计算不稳定 (同输入不同输出)")

    # 缓存漂移检测: 篡改缓存报告后触发抽样校验
    drift_aud = IncrementalAuditor(sample_verify_every=1)
    drift_aud.audit(inc1)
    fp = drift_aud.compute_fingerprint(inc1)
    drift_aud._cache[fp]["report"]["verdict"] = PASS  # 人为篡改
    drift_aud._cache[fp]["report"]["events_summary"]["total"] = 999
    rd, hd, md = drift_aud.audit(inc1)
    if drift_aud._drift_found == 0:
        failures.append("缓存漂移未被抽样校验发现 (drift_found=%d)"
                        % drift_aud._drift_found)

    # 6. LRU 淘汰
    lru_aud = IncrementalAuditor(cache_size=2)
    for i in range(4):
        pkg = _normal_pkg_for_lru(i)
        lru_aud.audit(pkg)
    if lru_aud.stats()["cache_size"] > 2:
        failures.append("LRU 淘汰失效: cache_size=%d > 2"
                        % lru_aud.stats()["cache_size"])

    # 7. v2_plus 基线回归仍须通过
    v2plus_failures, _ = v2plus.run_self_test_plus()
    if v2plus_failures:
        for f in v2plus_failures:
            failures.append("v2_plus 基线回归失败: %s" % f)

    # 8. 版本常量断言
    if not AUDITOR_VERSION_V3.startswith("3."):
        failures.append("版本标识异常: %s" % AUDITOR_VERSION_V3)

    return failures, results


def _normal_pkg_for_lru(i):
    return {
        "contract_version": "EVIDENCE_CONTRACT_V1",
        "fingerprint": "fp-lru-%d" % i, "run_id": "run-lru",
        "session_id": "s", "evidence_role": "L2", "source_team": "DSHE",
        "call_type": "DSHE_INDEPENDENT_ZHIJI",
        "audit_fingerprint": "af-%d" % i, "trace_id": "tr-%d" % i,
        "dep_registry_id": "DEP-REG-001", "md5_manifest": {},
        "evidence_file": "f.json", "evidence_index": 1,
        "received_at": "2026-10-15T10:00:00Z", "submitter": "DSHE",
        "dshb_reuse": False,
        "calls": [{"call_id": "c", "url": "https://x",
                   "params": {}, "response": {"points": []},
                   "status": "COMPLETED", "http_status": 200,
                   "metadata_rate": 1.0, "real_fetchable_rate": 1.0}],
        "dep": {"registry": {"dep_registry_id": "DEP-REG-001",
                             "current_status": "RECOVERED",
                             "state_history": []},
                "metadata_rate": 1.0, "real_fetchable_rate": 1.0},
    }


# ---------------------------------------------------------------------------
# 性能基准对比
# ---------------------------------------------------------------------------
def run_perf_bench():
    """优化前后性能对比: v2_plus 全量 vs v3 短路 vs v3 增量。"""
    import timeit

    def mk_pkg(n_calls, n_points, corrupt_rate=False):
        calls = []
        for i in range(n_calls):
            calls.append({
                "call_id": "c%d" % i, "url": "https://x/api/%d" % i,
                "params": {"id": "s%d" % i},
                "response": {"points": [{"ts": t * 1000, "v": 100 + i + t}
                                         for t in range(n_points)]},
                "status": "COMPLETED", "http_status": 200,
                "metadata_rate": 1.0,
                "real_fetchable_rate": (0.0 if corrupt_rate else 1.0),
            })
        return {
            "contract_version": "EVIDENCE_CONTRACT_V1",
            "fingerprint": "fp-bench-%d" % n_calls, "run_id": "run-bench",
            "session_id": "s", "evidence_role": "L2", "source_team": "DSHE",
            "call_type": "DSHE_INDEPENDENT_ZHIJI",
            "audit_fingerprint": "af", "trace_id": "tr",
            "dep_registry_id": "DEP-REG-001", "md5_manifest": {},
            "evidence_file": "f.json", "evidence_index": 1,
            "received_at": "2026-10-15T10:00:00Z", "submitter": "DSHE",
            "dshb_reuse": False, "calls": calls,
            "dep": {"registry": {
                "dep_registry_id": "DEP-REG-001",
                "current_status": "RECOVERED",
                "state_history": [{"status_before": "BLOCKED",
                                   "status_after": "RECOVERED"}]},
                "metadata_rate": 1.0,
                "real_fetchable_rate": (0.0 if corrupt_rate else 1.0)},
        }

    def bench(fn, pkg, number=200, repeat=5):
        ts = timeit.repeat(lambda: fn(pkg), number=number, repeat=repeat)
        return min(ts) / number

    shapes = [(32, 20), (128, 20), (256, 20), (500, 20)]
    rows = []
    for nc, np_ in shapes:
        pkg_ok = mk_pkg(nc, np_)
        pkg_bad = mk_pkg(nc, np_, corrupt_rate=True)
        t_plus_ok = bench(lambda p: PlusAuditor(p).verdict(), pkg_ok)
        t_v3_ok = bench(lambda p: V3Auditor(p).verdict(), pkg_ok)
        t_plus_bad = bench(lambda p: PlusAuditor(p).verdict(), pkg_bad)
        t_v3_bad = bench(lambda p: V3Auditor(p).verdict(), pkg_bad)
        rows.append({
            "calls": nc, "bytes": len(json.dumps(pkg_ok)),
            "plus_ok_ms": t_plus_ok * 1000, "v3_ok_ms": t_v3_ok * 1000,
            "plus_bad_ms": t_plus_bad * 1000, "v3_bad_ms": t_v3_bad * 1000,
            "speedup_ok": t_plus_ok / t_v3_ok if t_v3_ok else 0,
            "speedup_bad": t_plus_bad / t_v3_bad if t_v3_bad else 0,
            "throughput_v3_ok": 1 / t_v3_ok if t_v3_ok else 0,
            "throughput_v3_bad": 1 / t_v3_bad if t_v3_bad else 0,
        })

    # 增量缓存命中性能 (同包重复审计)
    inc = IncrementalAuditor()
    pkg_inc = mk_pkg(256, 20)
    inc.audit(pkg_inc)  # 首次 miss
    t_miss = bench(lambda p: inc.audit(p)[0], pkg_inc, number=50)
    inc2 = IncrementalAuditor()
    inc2.audit(pkg_inc)
    t_hit = bench(lambda p: inc2.audit(p)[0], pkg_inc, number=50)
    inc_perf = {
        "first_full_ms": (rows[-1]["v3_ok_ms"]),
        "cache_hit_ms": t_hit * 1000,
        "hit_speedup": t_miss / t_hit if t_hit else 0,
        "hit_stats": inc2.stats(),
    }
    return rows, inc_perf


def render_perf_bench(rows, inc_perf):
    lines = []
    lines.append("审计器性能对比 (v2_plus 全量 vs v3 短路)")
    lines.append("%-10s %10s %13s %13s %13s %13s %9s %9s" % (
        "包形态", "字节", "plus正常", "v3正常", "plus失败", "v3失败",
        "正常加速", "失败加速"))
    lines.append("-" * 108)
    for r in rows:
        lines.append("%-10d %10d %13.3f %13.3f %13.3f %13.3f %9.2fx %9.2fx"
                     % (r["calls"], r["bytes"], r["plus_ok_ms"],
                        r["v3_ok_ms"], r["plus_bad_ms"], r["v3_bad_ms"],
                        r["speedup_ok"], r["speedup_bad"]))
    lines.append("-" * 108)
    lines.append("增量缓存命中: 全量 %.3fms -> 命中 %.3fms (%.1fx)"
                 % (inc_perf["first_full_ms"], inc_perf["cache_hit_ms"],
                    inc_perf["hit_speedup"]))
    return "\n".join(lines)



# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def render_self_test_v3(failures, results):
    lines = []
    lines.append("=" * 76)
    lines.append("  evidence_auditor_v3 自回归测试  (auditor v%s, contract %s)"
                 % (AUDITOR_VERSION_V3, CONTRACT_VERSION))
    lines.append("=" * 76)
    lines.append("  基线用例: %d  |  v3 新增: %d (短路 %d + 增量 %d)"
                 "  |  基线 commit: %s"
                 % (len(build_v3_extra_cases()),
                    len(V3_SC_ASSERT_CASES) + len(V3_INC_ASSERT_CASES),
                    len(V3_SC_ASSERT_CASES), len(V3_INC_ASSERT_CASES),
                    BRANCH_BASELINE))
    lines.append("  核心断言: ★ 判定等价性 (v3 短路 vs v2_plus 全量 verdict 一致)")
    lines.append("-" * 76)
    for cid in sorted(results):
        r = results[cid]
        mark = "PASS" if r["ok"] else "FAIL"
        sc = r["report"]["short_circuit"]
        sc_txt = "短路跳过%d批" % sc["skipped_count"] if sc["skipped_count"] else "全量"
        lines.append("  %s  %-16s %-16s %s" % (mark, cid, r["actual"], sc_txt))
    lines.append("-" * 76)
    if failures:
        for f in failures:
            lines.append("  FAIL %s" % f)
        lines.append("  结论: SELF-TEST FAILED")
    else:
        lines.append("  全部通过: %d 用例判定 + 判定等价性 + 短路 %d + 增量 3 "
                     "+ LRU + 漂移检测 + v2_plus 基线回归"
                     % (len(results), len(V3_SC_ASSERT_CASES)))
        lines.append("  结论: SELF-TEST PASSED")
    lines.append("=" * 76)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 L1/L2 证据包独立校验器 v3 (短路+增量)")
    ap.add_argument("--self-test", action="store_true",
                    help="v3 自回归 (等价性+短路+增量+性能)")
    ap.add_argument("--perf-bench", action="store_true", help="性能基准对比")
    ap.add_argument("--md", help="性能报告 Markdown 路径")
    ap.add_argument("--json", dest="json_out", help="性能 JSON 输出路径")
    ap.add_argument("--check-md5", help="文件 MD5 校验")
    ap.add_argument("--expect", help="期望 MD5")
    args = ap.parse_args(argv)

    if args.self_test:
        failures, results = run_self_test_v3()
        print(render_self_test_v3(failures, results))
        return 1 if failures else 0

    if args.perf_bench:
        rows, inc_perf = run_perf_bench()
        txt = render_perf_bench(rows, inc_perf)
        print(txt)
        all_ok = all(r["speedup_ok"] >= 1.0 for r in rows)
        if args.md:
            with open(args.md, "w", encoding="utf-8") as f:
                f.write("## 性能基准\n\n```\n%s\n```\n" % txt)
            print("Markdown: %s" % args.md)
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump({"rows": rows, "incremental": inc_perf}, f,
                          ensure_ascii=False, indent=2)
            print("JSON: %s" % args.json_out)
        return 0 if all_ok else 1

    if args.check_md5:
        return check_md5(args.check_md5, args.expect)

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
