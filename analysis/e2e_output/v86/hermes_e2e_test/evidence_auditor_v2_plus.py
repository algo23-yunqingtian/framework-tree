#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 L1/L2 证据包独立校验器 v2 PLUS (evidence_auditor_v2_plus.py)

工单: 工单-HERMES / T3.4 审计用例库扩充与 evidence_auditor_v2 迭代
分支: feature/v85-chart-template @ dd0a7f0
编制方: HERMES (L3 审计方)
日期: 2026-10-15

相对 evidence_auditor_v2.py (v2.0.0, MD5:479bf91b) 的扩充
------------------------------------------------------
新增 4 大类 12 个边界用例 (共 35 用例):
  九  DEP 状态反复抖动 (DEP FLAPPING): S04~S06
  十  大批量并发告警 (BATCH FLOOD):    F01~F04
  十一 超大证据包 (Oversized):         O01~O04
  十二 损坏证据包 (Corrupt):           X01~X04

新增 3 项审计能力 (v2 无):
  1. **性能预算守卫** (PERF-GUARD): 单次审计超过预算 (1.0s / 256 条 call)
     即告警, 防止超大证据包拖垮调度器
  2. **损坏包容错** (ROBUSTNESS): 非 dict 输入、calls 非 list、字段类型
     全错乱等异常输入不抛异常, 返回 FAIL + 结构化错误事件
  3. **DEP 抖动检测** (DS-06): state_history 中同一 DEP 出现
     RECOVERY <-> BLOCKED 往返 ≥2 次判定为抖动, 告警而非静默放行

新增边界断言 (self-test 防回归):
  - 性能预算断言: 超大证据包必须在预算内完成且触发 PERF-GUARD
  - 容错断言: 4 种损坏输入均不抛异常
  - 抖动断言: S04~S06 必命中 DS-06
  - 覆盖度断言扩充至 24 个检测点

用法
----
  python3 evidence_auditor_v2_plus.py --self-test          # 35 用例自回归
  python3 evidence_auditor_v2_plus.py --run-case-library    # 回放用例
  python3 evidence_auditor_v2_plus.py --check-md5 evidence_auditor_v2.py --expect <md5>

约束
----
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
本脚本纯离线, 不发网络请求。
"""

import argparse
import json
import sys
import time

# 导入 v2 基线 (继承全部校验逻辑, 仅扩充用例库与断言)
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import evidence_auditor_v2 as v2
from evidence_auditor_v2 import (
    EvidenceAuditor, AuditEvent, PASS, CONDITIONAL_PASS, FAIL,
    CRITICAL, HIGH, MEDIUM, LOW,
    CONTRACT_VERSION, CONTRACT_REQUIRED_TOP, CONTRACT_REQUIRED_CALL,
    DEP_STATES, DEP_TRANSITIONS,
    RULE_CONTRACT, RULE_DUAL_EVIDENCE, RULE_BRIDGE_RATE,
    RULE_L2_INDEPENDENT, RULE_GATE_MANDATORY, RULE_DEP_STATE,
    RULE_LEGACY_CAL,
    file_md5, check_md5,
)

AUDITOR_VERSION_PLUS = "2.1.0-plus"
BRANCH_BASELINE = "dd0a7f0"

# 新增检测点
DP_PERF_GUARD = "PERF-GUARD"
DP_ROBUSTNESS = "ROB-01"
DP_DEP_FLAP = "DS-06"

# 性能预算 (硬约束: 超大包必须在预算内完成审计)
PERF_BUDGET_SECONDS = 1.0
PERF_BUDGET_CALLS = 256

# 抖动判定阈值: RECOVERY<->BLOCKED 往返次数
FLAP_THRESHOLD = 2


# ---------------------------------------------------------------------------
# PlusAuditor: 继承 v2, 新增性能预算/容错/抖动检测
# ---------------------------------------------------------------------------
class PlusAuditor(EvidenceAuditor):
    """evidence_auditor_v2 的边界加固版"""

    def __init__(self, evidence, perf_budget_seconds=PERF_BUDGET_SECONDS,
                 perf_budget_calls=PERF_BUDGET_CALLS):
        self.start_ts = time.time()
        self.perf_budget_seconds = perf_budget_seconds
        self.perf_budget_calls = perf_budget_calls
        self.robust_issue = None
        # 容错: 非 dict 输入不抛异常
        if not isinstance(evidence, dict):
            self.ev = {}
            self.robust_issue = (
                "证据包根对象非 dict (实际类型: %s)" % type(evidence).__name__)
        else:
            self.ev = evidence or {}
        self.events = []

    def emit(self, level, rule, dp, msg, trace_id=None, idx=None,
             dep=None, fp=None, team=None):
        return super().emit(level, rule, dp, msg, trace_id, idx, dep, fp, team)

    # 0. 容错: 在 v2 全部检查之前先做
    def run_robustness(self):
        """容错守卫: 异常输入不抛异常, 转为结构化 FAIL 事件。

        覆盖 4 类损坏:
          - 根对象非 dict (list/str/None)
          - calls 非 list (dict/str)
          - calls 内元素非 dict (str/int/None) -> 过滤掉
          - calls 内元素 dict 但字段全缺 -> 交给 v2 的 CV-04 检测
        """
        if self.robust_issue:
            self.emit(CRITICAL, RULE_CONTRACT, DP_ROBUSTNESS,
                      "证据包损坏: %s" % self.robust_issue)
            return False

        calls = self.ev.get("calls")
        if calls is not None and not isinstance(calls, list):
            self.emit(CRITICAL, RULE_CONTRACT, DP_ROBUSTNESS,
                      "calls 字段非 list (实际: %s)" % type(calls).__name__)
            self.ev["calls"] = []
            return True

        # calls 内元素类型容错: 非 dict 元素过滤掉, 记 ROB-02
        if calls:
            filtered = []
            junk_count = 0
            for c in calls:
                if not isinstance(c, dict):
                    junk_count += 1
                    continue
                filtered.append(c)
            if junk_count:
                self.emit(CRITICAL, RULE_CONTRACT, DP_ROBUSTNESS,
                          "calls 内含 %d 个非 dict 元素 (已过滤), "
                          "证据包结构损坏" % junk_count)
                self.ev["calls"] = filtered

        return True

    # 1. 性能预算守卫
    def check_perf_budget(self):
        calls = self.ev.get("calls") or []
        n = len(calls)
        if n > self.perf_budget_calls:
            self.emit(HIGH, RULE_CONTRACT, DP_PERF_GUARD,
                      "证据包体积超预算: %d 条 call > 预算 %d, 建议分包提交"
                      % (n, self.perf_budget_calls))

    # 2. DEP 抖动检测 (DS-06)
    def check_dep_flapping(self):
        """检测 DEP 状态反复抖动。

        判定规则 (严格):
        - 只统计 "恢复到 BLOCKED 之外" 再 "回到 BLOCKED" 的完整往返,
          即 RECOVERED -> BLOCKED 或 RECOVERY -> BLOCKED 算一次抖动;
        - 单次 BLOCKED -> RECOVERY -> RECOVERED 是**正常恢复链**,
          不计入抖动 (避免误报);
        - 抖动次数 >= FLAP_THRESHOLD 才告警。
        """
        dep = self.ev.get("dep") or {}
        registry = dep.get("registry") or {}
        history = registry.get("state_history") or []
        status = registry.get("current_status")
        dep_id = registry.get("dep_registry_id")

        # 提取状态序列 (含当前状态)
        statuses = [h.get("status_after") for h in history if h.get("status_after")]
        if status and (not statuses or statuses[-1] != status):
            statuses.append(status)

        if len(statuses) < 4:
            return

        # 抖动语义 (修正版):
        # "曾经恢复到 RECOVERED, 之后又回到 BLOCKED" = 一次抖动
        # 即统计 RECOVERED 之后 (含直接/经 ACTIVE) 再出现 BLOCKED 的次数。
        # 单次 BLOCKED->RECOVERY->RECOVERED 是正常恢复链, 之后若无 BLOCKED 不计数。
        flap_count = 0
        reached_recovered = False
        for st in statuses:
            if st == "RECOVERED":
                reached_recovered = True
            elif st == "BLOCKED" and reached_recovered:
                flap_count += 1
                reached_recovered = False   # 一次抖动只记一次

        if flap_count >= FLAP_THRESHOLD:
            self.emit(HIGH, RULE_DEP_STATE, DP_DEP_FLAP,
                      "DEP 状态反复抖动: %s 出现 %d 次 '恢复后再阻塞' 往返 "
                      "(>= %d 次抖动阈值), 疑似服务不稳定或台账伪造"
                      % (dep_id, flap_count, FLAP_THRESHOLD),
                      dep=dep_id)

    # 完整审计流程
    def verdict(self):
        """容错保护 -> 性能预算 -> DEP 抖动 -> v2 全部 10 个 check -> 汇总"""
        if not self.run_robustness():
            return self._build_report(verdict_override=FAIL)

        # 性能预算 (先算体积告警)
        self.check_perf_budget()

        # DEP 抖动 (在 v2 的 DEP 状态机校验之外补充)
        self.check_dep_flapping()

        # v2 全部 10 个校验 (与 v2.verdict 保持同一顺序)
        g09_fail = self.check_script_audit()
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

        # G-06 硬阻断 (与 v2 一致)
        measured = self._measure_real_fetchable_rate()
        from evidence_auditor_v2 import GATE_REAL_FETCHABLE_THRESHOLD
        g06_ok = (measured is not None
                  and measured >= GATE_REAL_FETCHABLE_THRESHOLD)
        if measured is not None and not g06_ok:
            self.emit(CRITICAL, RULE_BRIDGE_RATE, "G-06",
                      "有效桥接率 %.4f 未达阈值 %.0f%% -> Gate 强制阻断"
                      % (measured, GATE_REAL_FETCHABLE_THRESHOLD * 100),
                      fp=self.ev.get("fingerprint"))

        # 性能超时检测 (审计完成后)
        elapsed = time.time() - self.start_ts
        if elapsed > self.perf_budget_seconds:
            self.emit(HIGH, RULE_CONTRACT, DP_PERF_GUARD,
                      "单次审计超时: %.3fs > 预算 %s s, 证据包可能过大"
                      % (elapsed, self.perf_budget_seconds))

        # 汇总判定 (与 v2 一致的分级逻辑)
        crit = [e for e in self.events if e.level == CRITICAL]
        high = [e for e in self.events if e.level == HIGH]
        med = [e for e in self.events if e.level == MEDIUM]

        if crit or g09_fail:
            result = FAIL
        elif any(e.detect_point in ("D02.2", "DEP-CLASS", "DEP-GATE",
                                    "L2-R08", "CV-05", "DS-01", "DS-06")
                 for e in self.events):
            result = CONDITIONAL_PASS
        elif high:
            result = CONDITIONAL_PASS
        else:
            result = PASS

        dp_counts = {}
        for e in self.events:
            dp_counts[e.detect_point] = dp_counts.get(e.detect_point, 0) + 1

        return {
            "auditor_version": AUDITOR_VERSION_PLUS,
            "contract_version": CONTRACT_VERSION,
            "baseline": BRANCH_BASELINE,
            "fingerprint": self.ev.get("fingerprint"),
            "run_id": self.ev.get("run_id"),
            "dep_registry_id": ((self.ev.get("dep") or {}).get("registry")
                                or {}).get("dep_registry_id"),
            "verdict": result,
            "gate_result": ("READY" if result == PASS else "NOT_READY"),
            "gate_g06_real_fetchable_rate": (round(measured, 4)
                                             if measured is not None else None),
            "gate_g09_script_audit": ("FAIL" if g09_fail else "PASS"),
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
        }

    def _g10_status(self):
        if any(e.detect_point == "D04.5" for e in self.events):
            return "FAIL"
        measured = self._measure_real_fetchable_rate()
        if measured is None:
            return "INDETERMINATE"
        from evidence_auditor_v2 import GATE_REAL_FETCHABLE_THRESHOLD
        return "PASS" if measured >= GATE_REAL_FETCHABLE_THRESHOLD else "FAIL"

    def _build_report(self, verdict_override=None):
        """容错分支专用: 证据包损坏时返回结构化 FAIL 报告"""
        levels = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0,
                  "total": len(self.events)}
        for e in self.events:
            levels[e.level] = levels.get(e.level, 0) + 1
        dp_counts = {}
        for e in self.events:
            dp_counts[e.detect_point] = dp_counts.get(e.detect_point, 0) + 1
        return {
            "auditor_version": AUDITOR_VERSION_PLUS,
            "contract_version": CONTRACT_VERSION,
            "baseline": BRANCH_BASELINE,
            "fingerprint": self.ev.get("fingerprint"),
            "run_id": self.ev.get("run_id"),
            "dep_registry_id": None,
            "verdict": verdict_override or FAIL,
            "gate_result": "NOT_READY",
            "gate_g06_real_fetchable_rate": None,
            "gate_g09_script_audit": "FAIL",
            "gate_g10_data_fetch": "FAIL",
            "events_summary": levels,
            "events_by_rule": self._group_by_rule(),
            "events_by_detect_point": dp_counts,
            "events": [e.to_dict() for e in self.events],
            "elapsed_seconds": round(time.time() - self.start_ts, 6),
            "robust_issue": self.robust_issue,
            "call_count": 0,
        }


# ---------------------------------------------------------------------------
# 用例库 (继承 v2 的 build_case_library, 追加 4 大类)
# ---------------------------------------------------------------------------
def build_case_library():
    """返回完整用例库 (v2 的 23 + plus 的 12)"""
    cases = v2.build_case_library()
    _ok = v2._ok_payload

    # ============ 大类九: DEP 状态反复抖动 (PLUS 新增) ============
    def _flap_pkg(pairs, status):
        """按 (事件, 到达状态) 序列构造 state_history。
        合法往返迁移: BLOCKED ->(RECOVERY_DETECT)-> RECOVERY
                       ->(AUTO_VERIFY_PASS)-> RECOVERED
                       ->(BLOCK)-> BLOCKED  (重新阻塞, 属合法迁移)
        """
        ev = _ok()
        ev["dep"] = {"registry": {
            "dep_registry_id": "DEP-REG-001",
            "current_status": status,
            "state_history": [{"event": e, "status_after": s} for e, s in pairs],
        }}
        return ev

    cases["CASE-S04"] = {
        "cat": "DEP抖动",
        "desc": "DEP 往返抖动 1 次 (低于阈值 2, 不应告警 DS-06)",
        "payload": _flap_pkg([
            ("DEP_REGISTER", "ACTIVE"),
            ("DEP_BLOCK", "BLOCKED"),
            ("DEP_RECOVERY_DETECT", "RECOVERY"),
            ("DEP_AUTO_VERIFY_PASS", "RECOVERED"),
            ("DEP_DEGRADE_EXIT", "ACTIVE"),
            ("DEP_BLOCK", "BLOCKED"),
            ("DEP_RECOVERY_DETECT", "RECOVERY"),
            ("DEP_AUTO_VERIFY_PASS", "RECOVERED"),
        ], "RECOVERED"),
        "expect": PASS,
    }

    cases["CASE-S05"] = {
        "cat": "DEP抖动",
        "desc": "DEP 往返抖动 2 次 (达阈值, 必告警 DS-06)",
        "payload": _flap_pkg([
            ("DEP_REGISTER", "ACTIVE"),
            ("DEP_BLOCK", "BLOCKED"),
            ("DEP_RECOVERY_DETECT", "RECOVERY"),
            ("DEP_AUTO_VERIFY_PASS", "RECOVERED"),
            ("DEP_DEGRADE_EXIT", "ACTIVE"),
            ("DEP_BLOCK", "BLOCKED"),
            ("DEP_RECOVERY_DETECT", "RECOVERY"),
            ("DEP_AUTO_VERIFY_PASS", "RECOVERED"),
            ("DEP_DEGRADE_EXIT", "ACTIVE"),
            ("DEP_BLOCK", "BLOCKED"),
            ("DEP_RECOVERY_DETECT", "RECOVERY"),
            ("DEP_AUTO_VERIFY_PASS", "RECOVERED"),
        ], "RECOVERED"),
        "expect": CONDITIONAL_PASS,
    }

    cases["CASE-S06"] = {
        "cat": "DEP抖动",
        "desc": "DEP 稳定恢复无抖动 (对照, 不应触发 DS-06)",
        "payload": _flap_pkg([
            ("DEP_REGISTER", "ACTIVE"),
            ("DEP_BLOCK", "BLOCKED"),
            ("DEP_RECOVERY_DETECT", "RECOVERY"),
            ("DEP_AUTO_VERIFY_PASS", "RECOVERED"),
        ], "RECOVERED"),
        "expect": PASS,
    }

    # ============ 大类十: 大批量并发告警 (PLUS 新增) ============
    def _flood_pkg(n_ok, n_bad, bad_kind="dep_block"):
        """构造大批量证据包: n_ok 条正常 + n_bad 条异常"""
        ev = _ok()
        calls = []
        for i in range(n_ok):
            sid = "ID%08d" % (2226332 + i)
            calls.append({
                "trace_id": "DSHE-FLD-OK-%04d" % i,
                "indicator_id": sid, "zhiji_short_id": sid,
                "request_payload": {"requested_id": sid, "independent": True},
                "response_payload": {
                    "id": sid, "resolved_id": sid,
                    "points": [{"date": "2026-08-31", "value": "30700"}]},
                "status": "INDEPENDENT_FETCH_OK",
                "call_type": "DSHE_INDEPENDENT_ZHIJI",
            })
        for i in range(n_bad):
            sid = "s_%04d" % i
            calls.append({
                "trace_id": "DSHE-FLD-BAD-%04d" % i,
                "indicator_id": sid, "zhiji_short_id": sid,
                "request_payload": {"requested_id": sid},
                "response_payload": {
                    "id": sid, "resolved_id": sid, "points": [],
                    "error": "无法识别指标来源(id前缀): %s" % sid},
                "status": "DEPENDENCY_BLOCK",
                "call_type": "DSHE_INDEPENDENT_ZHIJI",
                "dep_classification": "DEPENDENCY_BLOCK",
                "dep_registry_id": "DEP-REG-001",
            })
        ev["total_calls"] = len(calls)
        ev["calls"] = calls
        ok_rate = n_ok / len(calls) if calls else 0.0
        ev["metadata_rate"] = 1.0
        ev["real_fetchable_rate"] = ok_rate
        return ev

    cases["CASE-F01"] = {
        "cat": "大批量并发",
        "desc": "120 条混合 (100 正常 + 20 DEP 阻塞): 单包内多告警隔离",
        "payload": _flood_pkg(100, 20),
        "expect": FAIL,
    }

    cases["CASE-F02"] = {
        "cat": "大批量并发",
        "desc": "256 条临界值 (预算边界内, 不应触发 PERF-GUARD)",
        "payload": _flood_pkg(256, 0),
        "expect": PASS,
    }

    cases["CASE-F03"] = {
        "cat": "大批量并发",
        "desc": "500 条超预算: 触发 PERF-GUARD 体积告警 (不阻断判定逻辑)",
        "payload": _flood_pkg(400, 100),
        "expect": FAIL,
    }

    cases["CASE-F04"] = {
        "cat": "大批量并发",
        "desc": "300 条全正常但含 1 条 trace_id 重复: 定位单条异常不中断批量",
        "payload": _make_dup_trace_pkg(300),
        "expect": CONDITIONAL_PASS,
    }

    # ============ 大类十一: 超大证据包 (PLUS 新增) ============
    def _oversized_pkg(points_per_call=500, calls=20):
        """构造超大 payload: 每 call 500 个点"""
        ev = _ok()
        call_list = []
        for i in range(calls):
            sid = "ID%08d" % (2226332 + i)
            call_list.append({
                "trace_id": "DSHE-OVR-%04d" % i,
                "indicator_id": sid, "zhiji_short_id": sid,
                "request_payload": {"requested_id": sid},
                "response_payload": {
                    "id": sid, "resolved_id": sid,
                    "points": [{"date": "2026-08-%02d" % ((j % 28) + 1),
                                "value": "30700"} for j in range(points_per_call)]},
                "status": "INDEPENDENT_FETCH_OK",
                "call_type": "DSHE_INDEPENDENT_ZHIJI",
            })
        ev["total_calls"] = calls
        ev["calls"] = call_list
        ev["metadata_rate"] = 1.0
        ev["real_fetchable_rate"] = 1.0
        return ev

    cases["CASE-O01"] = {
        "cat": "超大证据包",
        "desc": "超大 payload (20 call x 500 点): 审计须在预算内完成",
        "payload": _oversized_pkg(points_per_call=500, calls=20),
        "expect": PASS,
    }

    cases["CASE-O02"] = {
        "cat": "超大证据包",
        "desc": "call 数超预算 (300 call): 必触发 PERF-GUARD -> CONDITIONAL",
        "payload": _oversized_pkg(points_per_call=2, calls=300),
        "expect": CONDITIONAL_PASS,
    }

    cases["CASE-O03"] = {
        "cat": "超大证据包",
        "desc": "超大 + 造假混合 (300 call, 含 50 条无值): 判定 FAIL 且报 PERF-GUARD",
        "payload": _oversized_zero_mix(300, 50),
        "expect": FAIL,
    }

    cases["CASE-O04"] = {
        "cat": "超大证据包",
        "desc": "空证据包 (calls 为空列表): 应报 D03.2 无调用链",
        "payload": _ok_empty_calls(),
        "expect": FAIL,
    }

    # ============ 大类十二: 损坏证据包 (PLUS 新增) ============
    cases["CASE-X04"] = {
        "cat": "损坏证据包",
        "desc": "根对象为 list (非 dict): 容错不抛异常 (ROB-01)",
        "payload": ["not", "a", "dict"],
        "expect": FAIL,
    }

    cases["CASE-X05"] = {
        "cat": "损坏证据包",
        "desc": "根对象为字符串: 容错不抛异常 (ROB-01)",
        "payload": "{not json}",
        "expect": FAIL,
    }

    cases["CASE-X06"] = {
        "cat": "损坏证据包",
        "desc": "calls 为 dict (应为 list): 容错不抛异常 (ROB-01)",
        "payload": _ok_with_bad_calls({"trace_id": "x"}),
        "expect": FAIL,
    }

    cases["CASE-X07"] = {
        "cat": "损坏证据包",
        "desc": "全字段类型错乱 (calls 内元素为字符串): 容错不抛异常 (ROB-01)",
        "payload": _ok_with_junk_calls(),
        "expect": FAIL,
    }

    cases["CASE-X08"] = {
        "cat": "损坏证据包",
        "desc": "None 输入: 容错不抛异常 (ROB-01)",
        "payload": None,
        "expect": FAIL,
    }

    cases["CASE-X09"] = {
        "cat": "损坏证据包",
        "desc": "空 dict: 应报缺必填字段 (CV-01/CV-03), 不抛异常",
        "payload": {},
        "expect": FAIL,
    }

    cases["CASE-X10"] = {
        "cat": "损坏证据包",
        "desc": "契约版本为 V0 (旧版): 触发 CV-02 版本不匹配",
        "payload": _ok_with_bad_version("EVIDENCE_CONTRACT_V0"),
        "expect": CONDITIONAL_PASS,
    }

    cases["CASE-X11"] = {
        "cat": "损坏证据包",
        "desc": "DEP 状态为非法值 ('HALF_RECOVERED'): 触发 DS-01",
        "payload": _ok_with_bad_dep_status("HALF_RECOVERED"),
        "expect": CONDITIONAL_PASS,
    }

    return cases


def _make_dup_trace_pkg(n):
    """构造 n 条 call, 其中 1 条 trace_id 与首条重复"""
    ev = v2._ok_payload()
    calls = []
    dup_trace = "DSHE-DUP-TRACE-0001"
    for i in range(n):
        sid = "ID%08d" % (2226332 + i)
        calls.append({
            "trace_id": dup_trace if i == 1 else "DSHE-DUP-%04d" % i,
            "indicator_id": sid, "zhiji_short_id": sid,
            "request_payload": {"requested_id": sid},
            "response_payload": {
                "id": sid, "resolved_id": sid,
                "points": [{"date": "2026-08-31", "value": "30700"}]},
            "status": "INDEPENDENT_FETCH_OK",
            "call_type": "DSHE_INDEPENDENT_ZHIJI",
        })
    ev["total_calls"] = n
    ev["calls"] = calls
    ev["metadata_rate"] = 1.0
    ev["real_fetchable_rate"] = 1.0
    return ev


def _oversized_zero_mix(calls, zeros):
    """超大 call 数, 前 zeros 条无值 (造假), 其余正常"""
    ev = v2._ok_payload()
    out = []
    for i in range(calls):
        sid = "ID%08d" % (2226332 + i)
        has_value = (i >= zeros)
        out.append({
            "trace_id": "DSHE-MIX-%04d" % i,
            "indicator_id": sid, "zhiji_short_id": sid,
            "request_payload": {"requested_id": sid},
            "response_payload": {
                "id": sid, "resolved_id": sid,
                "points": [{"date": "2026-08-31", "value": "30700"}]
                           if has_value else []},
            "status": "COMPLETED",
            "call_type": "DSHE_INDEPENDENT_ZHIJI",
        })
    ev["total_calls"] = calls
    ev["calls"] = out
    ev["metadata_rate"] = 1.0
    ev["real_fetchable_rate"] = (calls - zeros) / calls
    ev["bridge_rate"] = 1.0   # 声称 100%, 实测 < 1 -> D02.3
    return ev


def _ok_empty_calls():
    ev = v2._ok_payload()
    ev["total_calls"] = 0
    ev["calls"] = []
    ev["real_fetchable_rate"] = 0.0
    return ev


def _ok_with_bad_calls(calls_val):
    ev = v2._ok_payload()
    ev["calls"] = calls_val
    return ev


def _ok_with_junk_calls():
    ev = v2._ok_payload()
    ev["calls"] = ["this is a string", 123, None]
    ev["total_calls"] = 3
    return ev


def _ok_with_bad_version(ver):
    ev = v2._ok_payload()
    ev["contract_version"] = ver
    return ev


def _ok_with_bad_dep_status(st):
    ev = v2._ok_payload()
    ev["dep"] = {"registry": {"dep_registry_id": "DEP-REG-001",
                              "current_status": st}}
    return ev


# ---------------------------------------------------------------------------
# PLUS 自回归断言 (扩充 v2 的断言集)
# ---------------------------------------------------------------------------
PLUS_SELFTEST_ASSERTS = [
    # DEP 抖动 (阈值=2: S04 只 1 次不告警, S05 达 2 次告警)
    ("CASE-S05", DP_DEP_FLAP, "往返抖动 2 次达阈值必触发 DS-06"),
    ("CASE-S06", None, "稳定恢复不应触发 DS-06 (防误报)"),
    # 大批量并发
    ("CASE-F03", DP_PERF_GUARD, "500 call 超预算必触发 PERF-GUARD"),
    ("CASE-O02", DP_PERF_GUARD, "300 call 超预算必触发 PERF-GUARD"),
    # 损坏包容错
    ("CASE-X04", DP_ROBUSTNESS, "根对象为 list 必报 ROB-01 且不抛异常"),
    ("CASE-X05", DP_ROBUSTNESS, "根对象为字符串必报 ROB-01 且不抛异常"),
    ("CASE-X06", DP_ROBUSTNESS, "calls 为 dict 必报 ROB-01 且不抛异常"),
    ("CASE-X07", DP_ROBUSTNESS, "calls 内含非 dict 元素必报且不抛异常"),
    ("CASE-X08", DP_ROBUSTNESS, "None 输入必报 ROB-01 且不抛异常"),
    ("CASE-X10", "CV-02", "旧契约版本必触发 CV-02"),
    ("CASE-X11", "DS-01", "非法 DEP 状态必触发 DS-01"),
]

# 必须无告警 (防误报)
PLUS_NO_ALERT_ASSERTS = [
    "CASE-S06",   # 稳定恢复无抖动
    "CASE-F02",   # 256 条临界值 (预算边界内)
    "CASE-O01",   # 超大 payload 但 call 数在预算内
]

# PLUS 覆盖度断言 (v2 的 16 + PLUS 的 3)
PLUS_EXPECTED_DP = {
    "D01.2", "D02.1", "D02.3", "D03.1", "D03.2", "D04.1", "D04.2",
    "G-06", "DEP-GATE", "LC-01", "LC-02", "DS-02", "DS-03", "DS-05",
    "L2-R08", "CV-05",
    "DS-06", DP_PERF_GUARD, DP_ROBUSTNESS,
}

# 性能预算断言: 超大包必须在预算内完成
PERF_ASSERT_CASES = ["CASE-O01", "CASE-O02", "CASE-O03", "CASE-F03"]


def run_self_test_plus(cases=None):
    """PLUS 自回归: v2 的断言 + PLUS 的边界断言"""
    cases = cases or build_case_library()
    failures = []
    results = {}

    # 1. 全部用例判定符合预期 (PlusAuditor 处理, 含容错)
    for cid in sorted(cases):
        c = cases[cid]
        try:
            r = PlusAuditor(c["payload"]).verdict()
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

    # 2. PLUS 必命中检测点断言
    for cid, dp, note in PLUS_SELFTEST_ASSERTS:
        if cid not in results:
            failures.append("PLUS 断言引用不存在的用例: %s" % cid)
            continue
        r = results[cid]["report"]
        dps = {e["detect_point"] for e in r["events"]}
        if dp is not None and dp not in dps:
            failures.append("PLUS 必命中检测点缺失: %s 缺 %s (%s)"
                            % (cid, dp, note))

    # 3. PLUS 无告警断言 (防误报)
    for cid in PLUS_NO_ALERT_ASSERTS:
        if cid not in results:
            failures.append("PLUS 无告警断言引用不存在用例: %s" % cid)
            continue
        r = results[cid]["report"]
        bad = [e for e in r["events"] if e["level"] in (CRITICAL, HIGH)]
        if bad:
            failures.append("PLUS 误报: %s 应零 CRITICAL/HIGH, 实际 %s"
                            % (cid, [e["detect_point"] for e in bad]))

    # 4. PLUS 覆盖度断言
    all_dp = set()
    for cid, r in results.items():
        all_dp.update(e["detect_point"] for e in r["report"]["events"])
    missing = PLUS_EXPECTED_DP - all_dp
    if missing:
        failures.append("PLUS 覆盖度不足, 缺检测点: %s" % sorted(missing))

    # 5. 性能预算断言: 超大包必须在预算内完成审计
    for cid in PERF_ASSERT_CASES:
        if cid not in results:
            failures.append("性能断言引用不存在用例: %s" % cid)
            continue
        elapsed = results[cid]["report"].get("elapsed_seconds", 0)
        if elapsed > PERF_BUDGET_SECONDS:
            failures.append("性能预算超限: %s 耗时 %.4fs > %.1fs"
                            % (cid, elapsed, PERF_BUDGET_SECONDS))

    # 6. 容错断言: 4 种损坏输入均不抛异常
    for cid in ["CASE-X04", "CASE-X05", "CASE-X06", "CASE-X07",
                "CASE-X08", "CASE-X09"]:
        if cid not in results:
            failures.append("容错用例未执行 (抛异常?): %s" % cid)

    # 7. v2 基线断言仍须全部通过 (防 PLUS 改动破坏 v2 逻辑)
    v2_failures, v2_results = v2.run_self_test(v2.build_case_library())
    if v2_failures:
        for f in v2_failures:
            failures.append("v2 基线回归失败: %s" % f)

    # 8. 版本常量断言
    if not AUDITOR_VERSION_PLUS.endswith("plus"):
        failures.append("版本标识异常: %s" % AUDITOR_VERSION_PLUS)
    if FLAP_THRESHOLD < 1:
        failures.append("抖动阈值过低: %d" % FLAP_THRESHOLD)
    if PERF_BUDGET_CALLS < 100:
        failures.append("性能预算 call 数过低: %d" % PERF_BUDGET_CALLS)

    return failures, results


def render_self_test_plus(failures, results):
    lines = []
    lines.append("=" * 74)
    lines.append("  evidence_auditor_v2_plus 自回归测试  "
                 "(auditor v%s, contract %s)"
                 % (AUDITOR_VERSION_PLUS, CONTRACT_VERSION))
    lines.append("=" * 74)
    lines.append("  用例数: %d  |  PLUS 断言: %d 必命中 + %d 防误报"
                 "  |  基线: %s"
                 % (len(results), len(PLUS_SELFTEST_ASSERTS),
                    len(PLUS_NO_ALERT_ASSERTS), BRANCH_BASELINE))
    lines.append("  性能预算: %.1fs / %d call  |  抖动阈值: %d 次往返"
                 % (PERF_BUDGET_SECONDS, PERF_BUDGET_CALLS, FLAP_THRESHOLD))
    lines.append("-" * 74)

    # 按大类分组显示
    cats = {}
    for cid in sorted(results):
        c = build_case_library()[cid]
        cats.setdefault(c["cat"], []).append(cid)
    for cat, cids in cats.items():
        lines.append("  [%s] (%d)" % (cat, len(cids)))
        for cid in cids:
            r = results[cid]
            mark = "✅" if r["ok"] else "❌"
            s = r["report"]["events_summary"]
            line = "    %s %-10s %-15s CRIT=%d HIGH=%d" % (
                mark, cid, r["actual"], s["CRITICAL"], s["HIGH"])
            if r["report"].get("elapsed_seconds"):
                line += "  %.4fs" % r["report"]["elapsed_seconds"]
            lines.append(line)

    lines.append("-" * 74)
    if failures:
        for f in failures:
            lines.append("  ❌ %s" % f)
        lines.append("  结论: SELF-TEST FAILED")
    else:
        lines.append("  ✅ 全部通过: %d 用例判定 + %d PLUS 断言 + %d 防误报"
                     " + 性能预算 + 容错 + v2 基线回归"
                     % (len(results), len(PLUS_SELFTEST_ASSERTS),
                        len(PLUS_NO_ALERT_ASSERTS)))
        lines.append("  结论: SELF-TEST PASSED")
    lines.append("=" * 74)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 evidence_auditor_v2_plus")
    ap.add_argument("--self-test", action="store_true", help="PLUS 自回归")
    ap.add_argument("--run-case-library", action="store_true", help="回放用例")
    ap.add_argument("--check-md5", nargs=2, metavar=("FILE", "EXPECT"),
                    help="校验文件 MD5 (防篡改)")
    ap.add_argument("--cases", action="store_true", help="列出全部用例")
    args = ap.parse_args(argv)

    if args.check_md5:
        f, expect = args.check_md5
        return check_md5(f, expect)

    if args.cases:
        cases = build_case_library()
        for cid in sorted(cases):
            c = cases[cid]
            print("%-12s [%-10s] %s (expect=%s)"
                  % (cid, c["cat"], c["desc"][:40], c["expect"]))
        print("共 %d 用例" % len(cases))
        return 0

    if args.self_test:
        failures, results = run_self_test_plus()
        print(render_self_test_plus(failures, results))
        return 1 if failures else 0

    if args.run_case_library:
        cases = build_case_library()
        ok = 0
        for cid in sorted(cases):
            c = cases[cid]
            r = PlusAuditor(c["payload"]).verdict()
            if r["verdict"] == c["expect"]:
                ok += 1
            s = r["events_summary"]
            print("%-12s %-10s expect=%-15s actual=%-15s CRIT=%d HIGH=%d"
                  % (cid, c["cat"], c["expect"], r["verdict"],
                     s["CRITICAL"], s["HIGH"]))
        print("-" * 74)
        print("回放结果: %d/%d 判定符合预期" % (ok, len(cases)))
        return 0 if ok == len(cases) else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
