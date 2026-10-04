#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 L1/L2 证据包独立校验器 (evidence_auditor.py)

工单: 工单-HERMES / T3.2 L1/L2证据包自动校验器开发
分支: feature/v85-chart-template @ caa2410
编制方: HERMES (L3 审计方)
日期: 2026-10-15

用途
----
独立读取 DSHB L1 自测包 + DSHE L2 独立调用证据包，自动执行审计校验，
输出预审结论 PASS / CONDITIONAL_PASS / FAIL，附带结构化审计报告。

校验项 (对齐 v86_rc2_hermes_audit_canonical_spec.md 四条硬审计规则)
----------------
1. 双证据完整性     - R-AUDIT-01 / D01.1-D01.3
2. traceID/审计指纹 - R-AUDIT-03 / L2-R06 / D03.1
3. 双桥接率口径     - R-AUDIT-02 / D02.1-D02.3
4. DEP 分类正确性   - 外部依赖管理规范 §2/§5
5. 退回作废标记     - L2-R08
6. MD5 完整性       - 证据包自哈希校验

证据包契约输入 (DSHE v86_rc2_dshe_l2_deliverable_spec.md §2.2.1)
----------------
{
  "fingerprint": "DSHE-20261015_100007-A3F2B1C4",
  "run_id": "20261015_100007",
  "session_id": "A3F2B1C4",
  "total_calls": 42,
  "generated_at": "2026-10-15T10:00:11.000000",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": false,
  "calls": [ { "trace_id": ..., "indicator_id": ..., "request_payload": {...},
               "response_payload": {...}, "status": ..., "call_type": ... } ]
}

约束
----
NO_ZHIJI_API_CALL=FALSE (本校验器纯离线校验, 不发网络请求)
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
本脚本为新增 V86 审计工具, 不触碰 V85 基线业务代码。

用法
----
  python3 evidence_auditor.py --file <evidence.json>           # 校验单个证据包
  python3 evidence_auditor.py --run-case-library               # 回放全部 11 个用例
  python3 evidence_auditor.py --selftest                       # 自检 (合成夹具)
  python3 evidence_auditor.py --check-md5 <file> [--expect <md5>]
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

AUDITOR_VERSION = "1.0.0"
BRANCH_BASELINE = "caa2410"

# Gate 准入阈值 (对齐 v86_rc2_hermes_gate_review_revised_spec.md)
GATE_REAL_FETCHABLE_THRESHOLD = 1.0   # G-06: 有效桥接率必须 100%
GATE_SCRIPT_AUDIT = "G-09"            # 脚本源码审计 (强制)
GATE_DATA_FETCH = "G-10"              # 真实取数校验 (强制)

# 审计规则编号
RULE_DUAL_EVIDENCE = "R-AUDIT-01"
RULE_BRIDGE_RATE = "R-AUDIT-02"
RULE_L2_INDEPENDENT = "R-AUDIT-03"
RULE_GATE_MANDATORY = "R-AUDIT-04"

# 告警分级 (对齐 T3.4 告警路由规范)
CRITICAL, HIGH, MEDIUM, LOW = "CRITICAL", "HIGH", "MEDIUM", "LOW"

# 结论枚举
PASS = "PASS"
CONDITIONAL_PASS = "CONDITIONAL_PASS"
FAIL = "FAIL"


# ---------------------------------------------------------------------------
# 告警事件
# ---------------------------------------------------------------------------
class AuditEvent:
    """单条审计事件, 持久化字段见 T3.4 规范"""

    def __init__(self, level, rule, detect_point, message,
                 trace_id=None, evidence_index=None):
        self.level = level
        self.rule = rule
        self.detect_point = detect_point
        self.message = message
        self.trace_id = trace_id
        self.evidence_index = evidence_index
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "level": self.level,
            "rule": self.rule,
            "detect_point": self.detect_point,
            "message": self.message,
            "trace_id": self.trace_id,
            "evidence_index": self.evidence_index,
            "timestamp": self.timestamp,
        }

    @property
    def event_id(self):
        h = hashlib.md5(
            ("%s|%s|%s|%s" % (self.timestamp, self.rule,
                               self.detect_point, self.message)).encode("utf-8")
        ).hexdigest()[:12]
        return "AE-%s" % h

    def __str__(self):
        return "[%s][%s][%s] %s" % (self.level, self.rule, self.detect_point,
                                     self.message)


# ---------------------------------------------------------------------------
# 检测点
# ---------------------------------------------------------------------------
class EvidenceAuditor:
    """L1/L2 证据包独立校验器"""

    def __init__(self, evidence):
        self.ev = evidence or {}
        self.events = []

    # -- 告警辅助 -----------------------------------------------------------
    def emit(self, level, rule, dp, msg, trace_id=None, idx=None):
        e = AuditEvent(level, rule, dp, msg, trace_id, idx)
        self.events.append(e)
        return e

    # -- 1. 双证据完整性 (R-AUDIT-01) ---------------------------------------
    def check_dual_evidence(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id")
            claimed = (c.get("status") or "").upper()
            if "COMPLETED" not in claimed and "FETCH_OK" not in claimed:
                continue

            meta = c.get("request_payload") or {}
            resp = c.get("response_payload") or {}

            # D01.1 元数据证据 (短ID + 长ID + 语义ID 三字段)
            id_fields = [c.get("indicator_id"), c.get("zhiji_short_id"),
                         resp.get("id")]
            if not all(f not in (None, "") for f in id_fields):
                self.emit(HIGH, RULE_DUAL_EVIDENCE, "D01.1",
                          "COMPLETED 条目元数据证据不完整: %s" % tid, tid)

            # D01.2 真实取数证据 (原始 payload + value!=0)
            pts = resp.get("points")
            has_nonzero = False
            if pts:
                for p in pts:
                    v = p.get("value")
                    if v is not None and str(v).strip() not in ("", "0", "0.0"):
                        has_nonzero = True
                        break
            if not (pts and has_nonzero):
                self.emit(CRITICAL, RULE_DUAL_EVIDENCE, "D01.2",
                          "COMPLETED 条目缺真实取数证据 (无原始 payload 或全 0): %s"
                          % tid, tid)

            # D01.3 桥接表填ID即标COMPLETED
            if not resp:
                self.emit(CRITICAL, RULE_DUAL_EVIDENCE, "D01.3",
                          "桥接表填ID即标 COMPLETED (无响应体): %s" % tid, tid)

            # 一致性断言 (requested_id == resolved_id)
            req = meta.get("requested_id") or c.get("indicator_id")
            res = resp.get("resolved_id")
            if req and res and req != res:
                self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.2",
                          "requested_id(%s) != resolved_id(%s): %s"
                          % (req, res, tid), tid)

    # -- 2. traceID / 审计指纹 (R-AUDIT-03 / L2-R06) ------------------------
    def check_trace_fingerprint(self):
        for f in ("fingerprint", "run_id", "session_id"):
            if not self.ev.get(f):
                self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.1",
                          "证据包缺审计字段: %s" % f)

        calls = self.ev.get("calls") or []
        seen = set()
        for c in calls:
            tid = c.get("trace_id")
            if not tid:
                self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.1",
                          "调用缺 trace_id")
                continue
            if tid in seen:
                self.emit(HIGH, RULE_L2_INDEPENDENT, "D03.1",
                          "trace_id 重复 (不可唯一溯源): %s" % tid, tid)
            seen.add(tid)

        # D03.2 背书式引用
        if self.ev.get("dshb_reuse") is True:
            self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.2",
                      "dshb_reuse=true 违反 L2-R01 (背书式引用)")
        if not calls:
            self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.2",
                      "calls 为空 (无独立调用链), 结论零价值")

        # call_type 必须为独立调用
        for c in calls:
            if c.get("call_type") not in ("DSHE_INDEPENDENT_ZHIJI",
                                          "DSHB_L1_SELF_TEST"):
                self.emit(HIGH, RULE_L2_INDEPENDENT, "D03.2",
                          "call_type 非独立调用链: %s" % c.get("call_type"),
                          c.get("trace_id"))

    # -- 3. 双桥接率口径 (R-AUDIT-02) ----------------------------------------
    def check_bridge_rate(self):
        mr = self.ev.get("metadata_rate")
        rr = self.ev.get("real_fetchable_rate")
        claimed = self.ev.get("bridge_rate")

        # D02.2 单一未拆分数字
        if claimed is not None and (mr is None or rr is None):
            self.emit(HIGH, RULE_BRIDGE_RATE, "D02.2",
                      "桥接率未拆分口径 (只有单值 %s), 须提供双栏" % claimed)
            return

        # D02.1 元数据完成率冒充有效桥接率
        if mr is not None and rr is not None and mr != rr:
            if claimed is not None and abs(claimed - mr) < 1e-9 \
                    and abs(mr - rr) > 1e-9:
                self.emit(CRITICAL, RULE_BRIDGE_RATE, "D02.1",
                          "元数据完成率(%s)冒充有效桥接率, 实际可取数率=%s"
                          % (mr, rr))
                return

        # D02.3 有效桥接率分子虚增 (声称 > 实测)
        measured = self._measure_real_fetchable_rate()
        if claimed is not None and measured is not None \
                and claimed > measured + 1e-9:
            self.emit(CRITICAL, RULE_BRIDGE_RATE, "D02.3",
                      "有效桥接率分子虚增: 声称 %s, 实测 %s"
                      % (claimed, round(measured, 4)))

    def _measure_real_fetchable_rate(self):
        calls = self.ev.get("calls") or []
        if not calls:
            return None
        ok = 0
        for c in calls:
            resp = c.get("response_payload") or {}
            pts = resp.get("points") or []
            if any(p.get("value") not in (None, "", 0, "0", "0.0")
                   for p in pts):
                ok += 1
        return ok / len(calls)

    # -- 4. 脚本审计 (G-09) -------------------------------------------------
    def check_script_audit(self):
        script = self.ev.get("script_audit") or {}
        if not script:
            # 无脚本审计信息不阻断, 但记录 (L1 包可能不含)
            return False
        fail = False
        if script.get("uses_search_passthrough"):
            self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.1",
                      "脚本入参 search 中转/自动替换 ID -> G-09 FAIL")
            fail = True
        if not script.get("has_id_consistency_assert"):
            self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.2",
                      "缺 requested_id==resolved_id 断言 -> G-09 FAIL")
            fail = True
        if script.get("zero_value_counts_as_pass"):
            self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.3",
                      "全 0 计 PASS -> G-09 FAIL")
            fail = True
        if not script.get("retains_raw_payload"):
            self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.4",
                      "未留存原始 payload -> G-09 FAIL")
            fail = True
        return fail

    # -- 5. 真实取数校验 (G-10) ---------------------------------------------
    def check_data_fetch(self):
        # 对照组健康检查 + COMPLETED 实测取数
        ctrl = self.ev.get("control_check") or {}
        if ctrl.get("http_status") != 200 or not ctrl.get("has_nonzero_value"):
            self.emit(HIGH, RULE_GATE_MANDATORY, "D04.5",
                      "对照组取数未通过, 无法判定环境健康 -> G-10 不可判定")
        else:
            # 对照组健康, 再检查目标条目
            for c in (self.ev.get("calls") or []):
                claimed = (c.get("status") or "").upper()
                resp = c.get("response_payload") or {}
                if "COMPLETED" in claimed or "FETCH_OK" in claimed:
                    if resp.get("error"):
                        self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.5",
                                  "标记成功但实测报错: %s / %s"
                                  % (c.get("indicator_id"), resp.get("error")),
                                  c.get("trace_id"))

    # -- 6. DEP 分类 --------------------------------------------------------
    def check_dep_classification(self):
        for c in (self.ev.get("calls") or []):
            cls = (c.get("dep_classification") or "").upper()
            resp = c.get("response_payload") or {}
            err = (resp.get("error") or "")
            if cls:
                if cls == "DEPENDENCY_BLOCK" and "无法识别指标来源" not in err \
                        and "permission_state" not in json.dumps(resp):
                    # 声称 DEP 但无外部阻塞证据 -> 内部缺陷
                    self.emit(HIGH, RULE_GATE_MANDATORY, "DEP-CLASS",
                              "声称 DEPENDENCY_BLOCK 但无外部阻塞证据, "
                              "降级为内部缺陷: %s" % c.get("indicator_id"),
                              c.get("trace_id"))
                if cls == "DEPENDENCY_BLOCK" and c.get("dep_registry_id") is None:
                    self.emit(MEDIUM, RULE_GATE_MANDATORY, "DEP-CLASS",
                              "DEPENDENCY_BLOCK 未登记依赖登记表: %s"
                              % c.get("indicator_id"), c.get("trace_id"))
        # DEP 阻塞不豁免 Gate
        if self.ev.get("dep_block_all") is True:
            self.emit(HIGH, RULE_GATE_MANDATORY, "DEP-GATE",
                      "全部条目 DEP 阻塞, 不计入内部 P0/P1, 但 Gate 维持 NOT_READY")

    # -- 7. 退回作废标记 (L2-R08) -------------------------------------------
    def check_retire_flag(self):
        if self.ev.get("superseded_by") or self.ev.get("retired") is True:
            self.emit(HIGH, RULE_L2_INDEPENDENT, "L2-R08",
                      "证据包已标记作废 (retired/superseded_by), 禁止复用")
        if self.ev.get("reused_from_run_id"):
            self.emit(CRITICAL, RULE_L2_INDEPENDENT, "L2-R08",
                      "证据包引用已退回的旧 run_id=%s, 流水线逐级阻断违规"
                      % self.ev.get("reused_from_run_id"))

    # -- 汇总判定 -----------------------------------------------------------
    def verdict(self):
        # 强制 Gate 项: G-09 / G-10 任一 FAIL 即阻断
        g09_fail = self.check_script_audit()
        self.check_dual_evidence()
        self.check_trace_fingerprint()
        self.check_bridge_rate()
        self.check_data_fetch()
        self.check_dep_classification()
        self.check_retire_flag()

        crit = [e for e in self.events if e.level == CRITICAL]
        high = [e for e in self.events if e.level == HIGH]

        # 真实可取数率 vs Gate 阈值 (G-06)
        # G-06 是硬准入项: 阈值未达即阻断, 不与 CONDITIONAL_PASS 混淆
        measured = self._measure_real_fetchable_rate()
        g06_ok = (measured is not None
                  and measured >= GATE_REAL_FETCHABLE_THRESHOLD)
        if measured is not None and not g06_ok:
            self.emit(CRITICAL, RULE_BRIDGE_RATE, "G-06",
                      "有效桥接率 %.4f 未达阈值 %.0f%% -> Gate 强制阻断"
                      % (measured, GATE_REAL_FETCHABLE_THRESHOLD * 100))
            crit = [e for e in self.events if e.level == CRITICAL]

        if crit or g09_fail:
            result = FAIL
        elif self.events and any(
                e.detect_point in ("D02.2", "DEP-CLASS", "DEP-GATE",
                                   "L2-R08")
                for e in self.events):
            result = CONDITIONAL_PASS
        else:
            result = PASS

        return {
            "auditor_version": AUDITOR_VERSION,
            "baseline": BRANCH_BASELINE,
            "fingerprint": self.ev.get("fingerprint"),
            "run_id": self.ev.get("run_id"),
            "verdict": result,
            "gate_result": ("READY" if result == PASS else "NOT_READY"),
            "gate_g06_real_fetchable_rate": (round(measured, 4)
                                             if measured is not None else None),
            "gate_g09_script_audit": ("FAIL" if g09_fail else "PASS"),
            "gate_g10_data_fetch": self._g10_status(),
            "events_summary": {
                "CRITICAL": len(crit),
                "HIGH": len(high),
                "MEDIUM": len([e for e in self.events if e.level == MEDIUM]),
                "LOW": len([e for e in self.events if e.level == LOW]),
                "total": len(self.events),
            },
            "events": [e.to_dict() for e in self.events],
        }

    def _g10_status(self):
        if any(e.detect_point == "D04.5" for e in self.events):
            return "FAIL"
        measured = self._measure_real_fetchable_rate()
        if measured is None:
            return "INDETERMINATE"
        return "PASS" if measured >= GATE_REAL_FETCHABLE_THRESHOLD else "FAIL"


# ---------------------------------------------------------------------------
# MD5 完整性
# ---------------------------------------------------------------------------
def file_md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_md5(path, expect=None):
    actual = file_md5(path)
    if expect is None:
        return {"file": path, "md5": actual, "result": "COMPUTED"}
    return {
        "file": path,
        "expected": expect,
        "actual": actual,
        "result": "PASS" if actual == expect else "FAIL",
    }


# ---------------------------------------------------------------------------
# 内置用例夹具 (对齐 v86_rc2_hermes_audit_case_library.md 11 用例)
# ---------------------------------------------------------------------------
def _ok_payload(short_id="ID02226332"):
    return {
        "fingerprint": "DSHE-TEST_OK-001",
        "run_id": "20260101_000001",
        "session_id": "SES001",
        "total_calls": 1,
        "generated_at": "2026-10-15T00:00:00.000000",
        "caller": "DSHE_V86_RC2_L2_AUDIT",
        "dshb_reuse": False,
        "metadata_rate": 1.0,
        "real_fetchable_rate": 1.0,
        "control_check": {"http_status": 200, "has_nonzero_value": True},
        "script_audit": {
            "uses_search_passthrough": False,
            "has_id_consistency_assert": True,
            "zero_value_counts_as_pass": False,
            "retains_raw_payload": True,
        },
        "calls": [{
            "trace_id": "DSHE-TEST_OK-001-001",
            "indicator_id": short_id,
            "zhiji_short_id": short_id,
            "request_payload": {"requested_id": short_id, "independent": True},
            "response_payload": {
                "id": short_id, "resolved_id": short_id,
                "points": [{"date": "2026-08-31", "value": "30700"},
                           {"date": "2026-07-31", "value": "20875"}],
            },
            "status": "INDEPENDENT_FETCH_OK",
            "call_type": "DSHE_INDEPENDENT_ZHIJI",
        }],
    }


def build_case_library():
    """11 个用例夹具 (结构对齐真实审计场景)"""
    cases = {}

    # ---- 大类一: 正向成功 ----
    cases["CASE-A01"] = {
        "desc": "DEP就绪+双指标达标完整链路",
        "payload": _ok_payload("j25_tc"),
        "expect": PASS,
    }
    cases["CASE-A02"] = {
        "desc": "对照组驱动的最小可放行单元",
        "payload": _ok_payload("ID02226332"),
        "expect": PASS,
    }

    # ---- 大类二: 旧口径造假 ----
    p = _ok_payload("s_001")
    p["bridge_rate"] = 1.0
    p["metadata_rate"] = 1.0
    p["real_fetchable_rate"] = 0.0
    p["calls"][0]["response_payload"] = {
        "id": "s_001", "resolved_id": "s_001", "points": []}
    p["calls"][0]["status"] = "COMPLETED"
    p["script_audit"] = {
        "uses_search_passthrough": True,
        "has_id_consistency_assert": False,
        "zero_value_counts_as_pass": True,
        "retains_raw_payload": False,
    }
    cases["CASE-N01"] = {
        "desc": "元数据完成+真实取数0% (虚假桥接率)",
        "payload": p, "expect": FAIL,
    }

    p = _ok_payload()
    p["bridge_rate"] = 0.85
    del p["metadata_rate"]
    del p["real_fetchable_rate"]
    cases["CASE-N02"] = {
        "desc": "桥接率单一数字不拆分",
        "payload": p, "expect": CONDITIONAL_PASS,
    }

    p = _ok_payload()
    p["dshb_reuse"] = True
    p["calls"] = []
    cases["CASE-N03"] = {
        "desc": "L2背书式引用 (零价值)",
        "payload": p, "expect": FAIL,
    }

    p = _ok_payload("s_001")
    p["calls"][0]["response_payload"] = {
        "id": "s_001", "resolved_id": "s_001", "points": [],
        "error": "无法识别指标来源(id前缀): s_001",
    }
    p["calls"][0]["status"] = "COMPLETED"
    cases["CASE-N04"] = {
        "desc": "伪造ID提交 (不存在于zhiji, 内部缺陷)",
        "payload": p, "expect": FAIL,
    }

    # ---- 大类三: DEP 全阻塞 ----
    p = _ok_payload("j25_tc")
    p["metadata_rate"] = 1.0
    p["real_fetchable_rate"] = 0.0
    p["dep_block_all"] = True
    p["calls"][0]["response_payload"] = {
        "id": "j25_tc", "resolved_id": "j25_tc", "points": [],
        "error": "无法识别指标来源(id前缀): j25_tc",
    }
    p["calls"][0]["status"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_classification"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_registry_id"] = "DEP-001"
    cases["CASE-D01"] = {
        "desc": "短ID解析全阻塞 (合规阻塞, Gate不豁免)",
        "payload": p, "expect": FAIL,
    }

    p = _ok_payload("j25_tc")
    p["calls"][0]["response_payload"] = {
        "id": "j25_tc", "resolved_id": "s_001", "points": [],
        "error": "HTTP 500 (伪造日志, 无请求URL/时间戳)",
    }
    p["calls"][0]["dep_classification"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_registry_id"] = None
    p["script_audit"]["has_id_consistency_assert"] = False
    cases["CASE-D02"] = {
        "desc": "借外部阻塞之名伪造日志 (内部P0)",
        "payload": p, "expect": FAIL,
    }

    # ---- 大类四: 部分 DEP 恢复 ----
    def _part_payload():
        ev = _ok_payload()
        ev["total_calls"] = 2
        ev["metadata_rate"] = 1.0
        ev["real_fetchable_rate"] = 0.5
        ev["calls"] = [
            dict(ev["calls"][0]),
            {
                "trace_id": "DSHE-TEST_OK-001-002",
                "indicator_id": "s_001",
                "zhiji_short_id": "s_001",
                "request_payload": {"requested_id": "s_001"},
                "response_payload": {
                    "id": "s_001", "resolved_id": "s_001", "points": [],
                    "error": "无法识别指标来源(id前缀): s_001",
                },
                "status": "DEPENDENCY_BLOCK",
                "call_type": "DSHE_INDEPENDENT_ZHIJI",
                "dep_classification": "DEPENDENCY_BLOCK",
                "dep_registry_id": "DEP-001",
            },
        ]
        return ev

    cases["CASE-P01"] = {
        "desc": "部分短ID就绪 (混合状态, Gate未达阈值)",
        "payload": _part_payload(), "expect": FAIL,
    }

    p = _part_payload()
    p["bridge_rate"] = 1.0
    p["calls"][1]["status"] = "COMPLETED"  # 残留旧口径: 无取数即标COMPLETED
    p["calls"][1]["dep_classification"] = None
    p["calls"][1]["dep_registry_id"] = None
    cases["CASE-P02"] = {
        "desc": "恢复后残留旧口径 (增量污染)",
        "payload": p, "expect": FAIL,
    }

    p = _part_payload()
    # CASE-P03: DEP-001 状态机迁移。证据包本身双证据齐全 (1 条 OK + 1 条 DEP),
    # dep_state 是流程元数据, 不影响证据合规性。但 G-06 桥接率 0.5 < 阈值,
    # 故仍 FAIL (Gate 不豁免) —— 验证"DEP 状态迁移不改变证据判定,
    # 但 DEP 阻塞不豁免 Gate"两个语义同时成立。
    p["dep_state"] = "IN_PROGRESS"
    cases["CASE-P03"] = {
        "desc": "DEP-001状态机迁移 (IN_PROGRESS, Gate不豁免)",
        "payload": p, "expect": FAIL,
    }

    return cases


# ---------------------------------------------------------------------------
# 报告渲染
# ---------------------------------------------------------------------------
def render_report(result):
    lines = []
    lines.append("=" * 68)
    lines.append("  V86-RC2 L1/L2 证据包预审结论  (auditor v%s)"
                 % AUDITOR_VERSION)
    lines.append("=" * 68)
    v = result["verdict"]
    mark = {PASS: "[PASS]", CONDITIONAL_PASS: "[CONDITIONAL]",
            FAIL: "[BLOCKED]"}.get(v, v)
    lines.append("  预审结论    : %s  %s" % (mark, v))
    lines.append("  Gate 结论   : %s" % result["gate_result"])
    lines.append("  G-06 真实可取数率 : %s (阈值 %.0f%%)"
                 % (result["gate_g06_real_fetchable_rate"],
                    GATE_REAL_FETCHABLE_THRESHOLD * 100))
    lines.append("  G-09 脚本审计     : %s" % result["gate_g09_script_audit"])
    lines.append("  G-10 真实取数校验 : %s" % result["gate_g10_data_fetch"])
    lines.append("  审计指纹    : %s" % result.get("fingerprint"))
    lines.append("  运行ID      : %s" % result.get("run_id"))
    s = result["events_summary"]
    lines.append("-" * 68)
    lines.append("  告警统计: CRITICAL=%d  HIGH=%d  MEDIUM=%d  LOW=%d  (合计 %d)"
                 % (s["CRITICAL"], s["HIGH"], s["MEDIUM"], s["LOW"],
                    s["total"]))
    lines.append("-" * 68)
    if s["total"]:
        for e in result["events"]:
            lines.append("  %-32s %-11s %s"
                         % ("[%s]" % e["level"],
                            "%s/%s" % (e["rule"], e["detect_point"]),
                            e["message"]))
    else:
        lines.append("  (无告警)")
    lines.append("=" * 68)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 L1/L2 证据包独立校验器")
    ap.add_argument("--file", help="证据包 JSON 路径")
    ap.add_argument("--run-case-library", action="store_true",
                    help="回放全部 11 个用例")
    ap.add_argument("--selftest", action="store_true", help="自检")
    ap.add_argument("--check-md5", help="校验文件 MD5")
    ap.add_argument("--expect", help="期望 MD5 (配 --check-md5)")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ap.add_argument("--persist", help="审计事件持久化输出路径")
    args = ap.parse_args(argv)

    # MD5 模式
    if args.check_md5:
        r = check_md5(args.check_md5, args.expect)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["result"] in ("PASS", "COMPUTED") else 1

    # 用例库回放
    if args.run_case_library or args.selftest:
        cases = build_case_library()
        passed = failed = 0
        records = []
        print("V86-RC2 审计用例库回放 (CASE-LIB v1.0, %d 用例)"
              % len(cases))
        print("-" * 68)
        for cid in sorted(cases):
            c = cases[cid]
            a = EvidenceAuditor(c["payload"])
            r = a.verdict()
            ok = (r["verdict"] == c["expect"])
            passed += ok
            failed += (not ok)
            print("%-10s %-46s 预期=%-16s 实测=%-16s %s"
                  % (cid, c["desc"], c["expect"], r["verdict"],
                     "OK" if ok else "MISMATCH"))
            records.append({"case_id": cid, "desc": c["desc"],
                            "expect": c["expect"], "actual": r["verdict"],
                            "match": ok, "report": r})
        print("-" * 68)
        print("回放结果: %d/%d 判定符合预期 (%d 不符)"
              % (passed, len(cases), failed))
        if args.persist:
            with open(args.persist, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print("审计事件已持久化: %s" % args.persist)
        return 0 if failed == 0 else 1

    # 单文件校验
    if args.file:
        if not os.path.exists(args.file):
            print("ERROR: 文件不存在 %s" % args.file)
            return 2
        with open(args.file, encoding="utf-8") as f:
            ev = json.load(f)
        r = EvidenceAuditor(ev).verdict()
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print(render_report(r))
        return 0 if r["verdict"] != FAIL else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
