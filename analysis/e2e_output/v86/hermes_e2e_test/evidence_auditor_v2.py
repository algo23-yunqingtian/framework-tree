#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 L1/L2 证据包独立校验器 v2 (evidence_auditor_v2.py)

工单: 工单-HERMES / T3.1 evidence_auditor 自校验加固与用例库扩充
分支: feature/v85-chart-template @ dcf7194
编制方: HERMES (L3 审计方)
日期: 2026-10-15

v2 相对 v1 的三项加固
--------------------
1. --self-test 自回归入口: 每次修改后一键回放全部用例 + 内置断言, 防止
   判定逻辑回归。v1 的开发教训是"首轮 8/11, 3 处缺陷全靠用例回放反查",
   现在把"必须回放"固化为脚本自身能力而非人工习惯。
2. 新增用例大类: 存量旧口径残留 (STATUS.md 170/170 COMPLETED 但真实 0%)、
   DEP 6 状态机流转、跨团队 DEP 台账不一致。
3. 新增契约校验维度: contract_version (EVIDENCE_CONTRACT_V1)、
   dep_registry_id 跨团队一致性、DEP 状态机合法性/非法迁移拦截。

新增校验维度
-----------
- CONTRACT-V1  契约版本与必填字段完整性
- DEP-STATE    DEP 6 状态机合法迁移校验 (ACTIVE/BLOCKED/RECOVERY/
               RECOVERED/ROLLED_BACK/CLOSED)
- DEP-XREG     跨团队 DEP 台账一致性 (DSHB 侧 vs DSHE 侧)
- LEGACY-CAL   存量旧口径残留检测 (声称 COMPLETED 数 > 实测可取数数)

证据包契约: EVIDENCE_CONTRACT_V1.md (本轮新增, 见 T3.2)
DEP 状态机: v86_rc2_dep_registry_common_spec.md §3

用法
----
  python3 evidence_auditor_v2.py --self-test                    # 自回归 (推荐每次改后跑)
  python3 evidence_auditor_v2.py --run-case-library             # 回放用例库
  python3 evidence_auditor_v2.py --file <evidence.json>         # 校验单包
  python3 evidence_auditor_v2.py --file <evidence.json> --json  # 机器可读输出
  python3 evidence_auditor_v2.py --check-md5 <file> [--expect <md5>]
  python3 evidence_auditor_v2.py --run-case-library --persist out.json

约束
----
NO_ZHIJI_API_CALL=FALSE (本校验器纯离线校验, 不发网络请求)
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
v1 evidence_auditor.py 保留不删 (NO_OVERWRITE), v2 为新增版本。
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

AUDITOR_VERSION = "2.0.0"
CONTRACT_VERSION = "EVIDENCE_CONTRACT_V1"
BRANCH_BASELINE = "dcf7194"
CASE_LIB_VERSION = "2.0"

# Gate 准入阈值
GATE_REAL_FETCHABLE_THRESHOLD = 1.0   # G-06 有效桥接率必须 100%

# 审计规则
RULE_DUAL_EVIDENCE = "R-AUDIT-01"
RULE_BRIDGE_RATE = "R-AUDIT-02"
RULE_L2_INDEPENDENT = "R-AUDIT-03"
RULE_GATE_MANDATORY = "R-AUDIT-04"
RULE_CONTRACT = "R-CONTRACT-V1"   # v2 新增
RULE_DEP_STATE = "R-DEP-STATE"    # v2 新增
RULE_LEGACY_CAL = "R-LEGACY-CAL"  # v2 新增

# 告警分级
CRITICAL, HIGH, MEDIUM, LOW = "CRITICAL", "HIGH", "MEDIUM", "LOW"

# 结论
PASS, CONDITIONAL_PASS, FAIL = "PASS", "CONDITIONAL_PASS", "FAIL"

# DEP 6 状态机 (v86_rc2_dep_registry_common_spec.md §3)
DEP_STATES = {"ACTIVE", "BLOCKED", "RECOVERY", "RECOVERED", "ROLLED_BACK", "CLOSED"}

# 合法状态迁移: {(from, event): to}
DEP_TRANSITIONS = {
    (None, "DEP_REGISTER"): "ACTIVE",
    ("ACTIVE", "DEP_BLOCK"): "BLOCKED",
    ("ACTIVE", "DEP_ROLLBACK_TRIGGER"): "ROLLED_BACK",
    ("ACTIVE", "DEP_CLOSE"): "CLOSED",
    ("BLOCKED", "DEP_RECOVERY_DETECT"): "RECOVERY",
    ("BLOCKED", "DEP_PAUSE_UPGRADE"): "BLOCKED",
    ("RECOVERY", "DEP_AUTO_VERIFY_PASS"): "RECOVERED",
    ("RECOVERY", "DEP_AUTO_VERIFY_FAIL"): "BLOCKED",
    ("RECOVERY", "DEP_PAUSE_UPGRADE"): "RECOVERY",
    ("RECOVERED", "DEP_DEGRADE_EXIT"): "ACTIVE",
    ("RECOVERED", "DEP_SWITCH_COMPLETE"): "ACTIVE",
    ("ROLLED_BACK", "DEP_RECOVERY_DETECT"): "RECOVERY",
}

# DSHB 侧状态 -> 统一状态映射 (§3.4)
DSHB_STATE_MAP = {
    "NORMAL": "ACTIVE", "API_ERROR": "BLOCKED", "RECOVERY_DETECTED": "RECOVERY",
    "SWITCHING": "RECOVERED", "ROLLED_BACK": "ROLLED_BACK", "DEPRECATED": "CLOSED",
}

# 跨团队台账交叉比对字段 (§4.1)
XREG_FIELDS = ["dep_registry_id", "current_status", "registration_time",
               "last_change_timestamp", "max_pause_days", "rollback_window_min",
               "risk_level", "impact_scope", "change_log_count"]

# EVIDENCE_CONTRACT_V1 必填字段
CONTRACT_REQUIRED_TOP = ["contract_version", "fingerprint", "run_id",
                         "session_id", "caller", "dshb_reuse", "generated_at"]
CONTRACT_REQUIRED_CALL = ["trace_id", "indicator_id", "request_payload",
                          "response_payload", "status", "call_type"]


# ---------------------------------------------------------------------------
# 审计事件
# ---------------------------------------------------------------------------
class AuditEvent:
    def __init__(self, level, rule, detect_point, message,
                 trace_id=None, evidence_index=None,
                 dep_registry_id=None, audit_fingerprint=None,
                 source_team=None):
        self.level = level
        self.rule = rule
        self.detect_point = detect_point
        self.message = message
        self.trace_id = trace_id
        self.evidence_index = evidence_index
        self.dep_registry_id = dep_registry_id
        self.audit_fingerprint = audit_fingerprint
        self.source_team = source_team
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
            "dep_registry_id": self.dep_registry_id,
            "audit_fingerprint": self.audit_fingerprint,
            "source_team": self.source_team,
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
# 校验器
# ---------------------------------------------------------------------------
class EvidenceAuditor:
    """L1/L2 证据包独立校验器 v2"""

    def __init__(self, evidence):
        self.ev = evidence or {}
        self.events = []

    def emit(self, level, rule, dp, msg, trace_id=None, idx=None,
             dep=None, fp=None, team=None):
        e = AuditEvent(level, rule, dp, msg, trace_id, idx, dep, fp, team)
        self.events.append(e)
        return e

    # -- 0. 契约版本与完整性 (v2 新增) --------------------------------------
    def check_contract(self):
        ver = self.ev.get("contract_version")
        if not ver:
            self.emit(HIGH, RULE_CONTRACT, "CV-01",
                      "缺 contract_version 字段 (EVIDENCE_CONTRACT_V1 要求)",
                      fp=self.ev.get("fingerprint"))
        elif ver != CONTRACT_VERSION:
            self.emit(HIGH, RULE_CONTRACT, "CV-02",
                      "契约版本不匹配: %s (期望 %s), 字段语义可能不一致"
                      % (ver, CONTRACT_VERSION), fp=self.ev.get("fingerprint"))

        for f in CONTRACT_REQUIRED_TOP:
            if f not in self.ev:
                self.emit(HIGH, RULE_CONTRACT, "CV-03",
                          "缺必填顶层字段: %s" % f)

        calls = self.ev.get("calls") or []
        for i, c in enumerate(calls):
            for f in CONTRACT_REQUIRED_CALL:
                if f not in c:
                    self.emit(HIGH, RULE_CONTRACT, "CV-04",
                              "calls[%d] 缺必填字段: %s" % (i, f),
                              idx=i, trace_id=c.get("trace_id"))

        # md5 清单 (契约要求证据包自述 md5)
        if not self.ev.get("md5_manifest"):
            self.emit(MEDIUM, RULE_CONTRACT, "CV-05",
                      "缺 md5_manifest 自述校验清单")

    # -- 1. 双证据完整性 (R-AUDIT-01) ---------------------------------------
    def check_dual_evidence(self):
        calls = self.ev.get("calls") or []
        for i, c in enumerate(calls):
            tid = c.get("trace_id")
            claimed = (c.get("status") or "").upper()
            if "COMPLETED" not in claimed and "FETCH_OK" not in claimed:
                continue

            meta = c.get("request_payload") or {}
            resp = c.get("response_payload") or {}

            id_fields = [c.get("indicator_id"), c.get("zhiji_short_id"),
                         resp.get("id")]
            if not all(f not in (None, "") for f in id_fields):
                self.emit(HIGH, RULE_DUAL_EVIDENCE, "D01.1",
                          "COMPLETED 条目元数据证据不完整: %s" % tid, tid, i)

            pts = resp.get("points")
            has_nonzero = any(
                p.get("value") not in (None, "", 0, "0", "0.0")
                for p in (pts or []))
            if not (pts and has_nonzero):
                self.emit(CRITICAL, RULE_DUAL_EVIDENCE, "D01.2",
                          "COMPLETED 条目缺真实取数证据 (无原始 payload 或全 0): %s"
                          % tid, tid, i)

            if not resp:
                self.emit(CRITICAL, RULE_DUAL_EVIDENCE, "D01.3",
                          "桥接表填ID即标 COMPLETED (无响应体): %s" % tid,
                          tid, i)

            req = meta.get("requested_id") or c.get("indicator_id")
            res = resp.get("resolved_id")
            if req and res and req != res:
                self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.2",
                          "requested_id(%s) != resolved_id(%s): %s"
                          % (req, res, tid), tid, i)

    # -- 2. traceID / 审计指纹 (R-AUDIT-03) ---------------------------------
    def check_trace_fingerprint(self):
        for f in ("fingerprint", "run_id", "session_id"):
            if not self.ev.get(f):
                self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.1",
                          "证据包缺审计字段: %s" % f)

        calls = self.ev.get("calls") or []
        seen = set()
        for i, c in enumerate(calls):
            tid = c.get("trace_id")
            if not tid:
                self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.1",
                          "calls[%d] 缺 trace_id" % i, idx=i)
                continue
            if tid in seen:
                self.emit(HIGH, RULE_L2_INDEPENDENT, "D03.1",
                          "trace_id 重复 (不可唯一溯源): %s" % tid, tid, i)
            seen.add(tid)

        if self.ev.get("dshb_reuse") is True:
            self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.2",
                      "dshb_reuse=true 违反 L2-R01 (背书式引用)",
                      team=self.ev.get("caller"))
        if not calls:
            self.emit(CRITICAL, RULE_L2_INDEPENDENT, "D03.2",
                      "calls 为空 (无独立调用链), 结论零价值")

        for i, c in enumerate(calls):
            if c.get("call_type") not in ("DSHE_INDEPENDENT_ZHIJI",
                                          "DSHB_L1_SELF_TEST"):
                self.emit(HIGH, RULE_L2_INDEPENDENT, "D03.2",
                          "call_type 非独立调用链: %s" % c.get("call_type"),
                          c.get("trace_id"), i)

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
        # D02.3 分子虚增
        # 注意: D02.1 与 D02.3 必须独立判定, 不可提前 return 遮蔽,
        # 否则"冒充+虚增"复合造案子仅报一条 (v2 自回归 CASE-C02 反查出的缺陷)
        if mr is not None and rr is not None and mr != rr \
                and claimed is not None and abs(claimed - mr) < 1e-9:
            self.emit(CRITICAL, RULE_BRIDGE_RATE, "D02.1",
                      "元数据完成率(%s)冒充有效桥接率, 实际可取数率=%s"
                      % (mr, rr))

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
        ok = sum(1 for c in calls
                 if any(p.get("value") not in (None, "", 0, "0", "0.0")
                        for p in (c.get("response_payload") or {}).get("points")
                        or []))
        return ok / len(calls)

    # -- 4. 存量旧口径残留检测 (v2 新增) ------------------------------------
    def check_legacy_caliber(self):
        """检测"声称完成数 > 实测可取数数"的存量旧口径残留。

        背景: STATUS.md 存在 DSHB 声称 170/170 COMPLETED、100% 桥接率,
        但真实可取数率 0% 的存量记录。本检测防止此类残留进入新证据包。
        """
        claimed_completed = self.ev.get("claimed_completed_count")
        measured = self._measure_real_fetchable_rate()

        calls = self.ev.get("calls") or []
        actual_ok = sum(1 for c in calls
                        if any(p.get("value") not in (None, "", 0, "0", "0.0")
                               for p in (c.get("response_payload") or {})
                               .get("points") or []))

        if claimed_completed is not None and claimed_completed > actual_ok:
            self.emit(CRITICAL, RULE_LEGACY_CAL, "LC-01",
                      "存量旧口径残留: 声称 COMPLETED=%d, 实测可取数=%d"
                      % (claimed_completed, actual_ok),
                      fp=self.ev.get("fingerprint"))

        # 旧口径术语检测: bridge_rate 与 real_fetchable_rate 不一致
        legacy_terms = ("100% bridge rate", "100%桥接率", "有效桥接率100%")
        blob = json.dumps(self.ev.get("notes", {}), ensure_ascii=False)
        for t in legacy_terms:
            if t in blob:
                self.emit(CRITICAL, RULE_LEGACY_CAL, "LC-02",
                          "检测到旧口径表述: '%s'" % t,
                          fp=self.ev.get("fingerprint"))

        if measured is not None and measured < 0.0001 \
                and self.ev.get("bridge_rate") in (1.0, 1, "100%"):
            self.emit(CRITICAL, RULE_LEGACY_CAL, "LC-03",
                      "桥接率声称100%但实测0% (典型旧口径造假模式)",
                      fp=self.ev.get("fingerprint"))

    # -- 5. DEP 状态机 (v2 新增) -------------------------------------------
    def check_dep_state(self):
        """校验 DEP 状态机迁移合法性 (v86_rc2_dep_registry_common_spec.md §3)"""
        dep = self.ev.get("dep") or {}
        registry = dep.get("registry") or {}
        status = registry.get("current_status")

        if status and status not in DEP_STATES:
            self.emit(HIGH, RULE_DEP_STATE, "DS-01",
                      "非法 DEP 状态: %s (有效: %s)"
                      % (status, "/".join(sorted(DEP_STATES))),
                      dep=registry.get("dep_registry_id"))

        # 状态迁移链校验
        history = registry.get("state_history") or []
        prev = None
        for h in history:
            ev_name = h.get("event")
            claimed_after = h.get("status_after")
            expected = DEP_TRANSITIONS.get((prev, ev_name))
            if expected is None:
                self.emit(CRITICAL, RULE_DEP_STATE, "DS-02",
                          "非法 DEP 状态迁移: %s + %s (无此转换规则)"
                          % (prev or "N/A", ev_name),
                          dep=registry.get("dep_registry_id"))
            elif claimed_after != expected:
                self.emit(CRITICAL, RULE_DEP_STATE, "DS-03",
                          "DEP 状态迁移声明错误: %s+%s 应到 %s, 实际声明 %s"
                          % (prev, ev_name, expected, claimed_after),
                          dep=registry.get("dep_registry_id"))
            prev = claimed_after

        # CLOSED 是终态, 之后不应有迁移
        if status == "CLOSED" and history:
            last_ev = history[-1].get("event")
            if last_ev != "DEP_CLOSE":
                self.emit(HIGH, RULE_DEP_STATE, "DS-04",
                          "CLOSED 为终态, 但末次事件为 %s" % last_ev,
                          dep=registry.get("dep_registry_id"))

    # -- 6. 跨团队 DEP 台账一致性 (v2 新增) ---------------------------------
    def check_dep_xreg(self):
        """DSHB 侧 vs DSHE 侧台账交叉比对 (§4.1)"""
        dep = self.ev.get("dep") or {}
        dshb = dep.get("dshb_view")
        dshe = dep.get("dshe_view")
        if not (dshb and dshe):
            return

        for f in XREG_FIELDS:
            a, b = dshb.get(f), dshe.get(f)
            if a is not None and b is not None and a != b:
                # 状态字段允许映射等价
                if f == "current_status" \
                        and DSHB_STATE_MAP.get(a) == b:
                    continue
                # 台账不一致 = 阻断: DEP 责任归因依赖台账, 不一致会使
                # 阻塞归因错乱, 必须在进入 L3 前拦截 (不可仅记 HIGH)
                self.emit(CRITICAL, RULE_DEP_STATE, "DS-05",
                          "跨团队 DEP 台账不一致: %s DSHB=%s / DSHE=%s"
                          % (f, a, b),
                          dep=dshe.get("dep_registry_id"))

    # -- 7. 脚本审计 (G-09) -------------------------------------------------
    def check_script_audit(self):
        script = self.ev.get("script_audit") or {}
        if not script:
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

    # -- 8. 真实取数校验 (G-10) ---------------------------------------------
    def check_data_fetch(self):
        ctrl = self.ev.get("control_check") or {}
        if ctrl.get("http_status") != 200 or not ctrl.get("has_nonzero_value"):
            self.emit(HIGH, RULE_GATE_MANDATORY, "D04.5",
                      "对照组取数未通过, 无法判定环境健康 -> G-10 不可判定")
        else:
            for c in (self.ev.get("calls") or []):
                claimed = (c.get("status") or "").upper()
                resp = c.get("response_payload") or {}
                if "COMPLETED" in claimed or "FETCH_OK" in claimed:
                    if resp.get("error"):
                        self.emit(CRITICAL, RULE_GATE_MANDATORY, "D04.5",
                                  "标记成功但实测报错: %s / %s"
                                  % (c.get("indicator_id"), resp.get("error")),
                                  c.get("trace_id"))

    # -- 9. DEP 分类 --------------------------------------------------------
    def check_dep_classification(self):
        for i, c in enumerate(self.ev.get("calls") or []):
            cls = (c.get("dep_classification") or "").upper()
            resp = c.get("response_payload") or {}
            err = (resp.get("error") or "")
            dep_id = c.get("dep_registry_id")
            if cls == "DEPENDENCY_BLOCK":
                if "无法识别指标来源" not in err \
                        and "permission_state" not in json.dumps(resp):
                    self.emit(HIGH, RULE_GATE_MANDATORY, "DEP-CLASS",
                              "声称 DEPENDENCY_BLOCK 但无外部阻塞证据, "
                              "降级为内部缺陷: %s" % c.get("indicator_id"),
                              c.get("trace_id"), i, dep_id)
                if not dep_id:
                    self.emit(MEDIUM, RULE_GATE_MANDATORY, "DEP-CLASS",
                              "DEPENDENCY_BLOCK 缺 dep_registry_id 关联: %s"
                              % c.get("indicator_id"), c.get("trace_id"), i)
        if self.ev.get("dep_block_all") is True:
            self.emit(HIGH, RULE_GATE_MANDATORY, "DEP-GATE",
                      "全部条目 DEP 阻塞, 不计入内部 P0/P1, 但 Gate 维持 NOT_READY",
                      dep=self.ev.get("dep", {}).get("registry", {})
                      .get("dep_registry_id"))

    # -- 10. 退回作废标记 (L2-R08) ------------------------------------------
    def check_retire_flag(self):
        if self.ev.get("superseded_by") or self.ev.get("retired") is True:
            self.emit(HIGH, RULE_L2_INDEPENDENT, "L2-R08",
                      "证据包已标记作废 (retired/superseded_by), 禁止复用",
                      fp=self.ev.get("fingerprint"))
        if self.ev.get("reused_from_run_id"):
            self.emit(CRITICAL, RULE_L2_INDEPENDENT, "L2-R08",
                      "引用已退回的旧 run_id=%s, 流水线逐级阻断违规"
                      % self.ev.get("reused_from_run_id"))

    # -- 汇总判定 -----------------------------------------------------------
    def verdict(self):
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

        crit = [e for e in self.events if e.level == CRITICAL]
        high = [e for e in self.events if e.level == HIGH]

        # G-06 硬阻断 (v1 修复项, 保留)
        measured = self._measure_real_fetchable_rate()
        g06_ok = (measured is not None
                  and measured >= GATE_REAL_FETCHABLE_THRESHOLD)
        if measured is not None and not g06_ok:
            self.emit(CRITICAL, RULE_BRIDGE_RATE, "G-06",
                      "有效桥接率 %.4f 未达阈值 %.0f%% -> Gate 强制阻断"
                      % (measured, GATE_REAL_FETCHABLE_THRESHOLD * 100),
                      fp=self.ev.get("fingerprint"))
            crit = [e for e in self.events if e.level == CRITICAL]

        if crit or g09_fail:
            result = FAIL
        elif any(e.detect_point in ("D02.2", "DEP-CLASS", "DEP-GATE",
                                    "L2-R08", "CV-05")
                 for e in self.events):
            result = CONDITIONAL_PASS
        else:
            result = PASS

        return {
            "auditor_version": AUDITOR_VERSION,
            "contract_version": CONTRACT_VERSION,
            "case_lib_version": CASE_LIB_VERSION,
            "baseline": BRANCH_BASELINE,
            "fingerprint": self.ev.get("fingerprint"),
            "run_id": self.ev.get("run_id"),
            "dep_registry_id": (self.ev.get("dep") or {}).get("registry", {})
                              .get("dep_registry_id"),
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
            "events_by_rule": self._group_by_rule(),
            "events": [e.to_dict() for e in self.events],
        }

    def _g10_status(self):
        if any(e.detect_point == "D04.5" for e in self.events):
            return "FAIL"
        measured = self._measure_real_fetchable_rate()
        if measured is None:
            return "INDETERMINATE"
        return "PASS" if measured >= GATE_REAL_FETCHABLE_THRESHOLD else "FAIL"

    def _group_by_rule(self):
        out = {}
        for e in self.events:
            out.setdefault(e.rule, 0)
            out[e.rule] += 1
        return out


# ---------------------------------------------------------------------------
# MD5
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
    return {"file": path, "expected": expect, "actual": actual,
            "result": "PASS" if actual == expect else "FAIL"}


# ---------------------------------------------------------------------------
# 用例夹具 (CASE-LIB v2.0: 11 原有 + 6 新增 = 17)
# ---------------------------------------------------------------------------
def _ok_payload(short_id="ID02226332", **kw):
    ev = {
        "contract_version": CONTRACT_VERSION,
        "fingerprint": "DSHE-TEST_OK-001",
        "run_id": "20260101_000001",
        "session_id": "SES001",
        "total_calls": 1,
        "generated_at": "2026-10-15T00:00:00+08:00",
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
        "md5_manifest": {"evidence_package": "self"},
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
    ev.update(kw)
    return ev


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
            "dep_registry_id": "DEP-REG-001",
        },
    ]
    return ev


def build_case_library():
    cases = {}

    # ============ 大类一: 正向成功 (原 v1) ============
    cases["CASE-A01"] = {
        "cat": "正向成功", "desc": "DEP就绪+双指标达标完整链路",
        "payload": _ok_payload("j25_tc"), "expect": PASS}
    cases["CASE-A02"] = {
        "cat": "正向成功", "desc": "对照组驱动的最小可放行单元",
        "payload": _ok_payload("ID02226332"), "expect": PASS}

    # ============ 大类二: 旧口径造假 (原 v1) ============
    p = _ok_payload("s_001")
    p["bridge_rate"] = 1.0
    p["metadata_rate"] = 1.0
    p["real_fetchable_rate"] = 0.0
    p["calls"][0]["response_payload"] = {
        "id": "s_001", "resolved_id": "s_001", "points": []}
    p["calls"][0]["status"] = "COMPLETED"
    p["script_audit"] = {
        "uses_search_passthrough": True, "has_id_consistency_assert": False,
        "zero_value_counts_as_pass": True, "retains_raw_payload": False}
    cases["CASE-N01"] = {
        "cat": "旧口径造假", "desc": "元数据完成+真实取数0% (虚假桥接率)",
        "payload": p, "expect": FAIL}

    p = _ok_payload()
    p["bridge_rate"] = 0.85
    del p["metadata_rate"]
    del p["real_fetchable_rate"]
    cases["CASE-N02"] = {
        "cat": "旧口径造假", "desc": "桥接率单一数字不拆分",
        "payload": p, "expect": CONDITIONAL_PASS}

    p = _ok_payload()
    p["dshb_reuse"] = True
    p["calls"] = []
    cases["CASE-N03"] = {
        "cat": "旧口径造假", "desc": "L2背书式引用 (零价值)",
        "payload": p, "expect": FAIL}

    p = _ok_payload("s_001")
    p["calls"][0]["response_payload"] = {
        "id": "s_001", "resolved_id": "s_001", "points": [],
        "error": "无法识别指标来源(id前缀): s_001"}
    p["calls"][0]["status"] = "COMPLETED"
    cases["CASE-N04"] = {
        "cat": "旧口径造假", "desc": "伪造ID提交 (不存在于zhiji)",
        "payload": p, "expect": FAIL}

    # ============ 大类三: DEP 全阻塞 (原 v1) ============
    p = _ok_payload("j25_tc")
    p["metadata_rate"] = 1.0
    p["real_fetchable_rate"] = 0.0
    p["dep_block_all"] = True
    p["dep"] = {"registry": {"dep_registry_id": "DEP-REG-001",
                             "current_status": "BLOCKED"}}
    p["calls"][0]["response_payload"] = {
        "id": "j25_tc", "resolved_id": "j25_tc", "points": [],
        "error": "无法识别指标来源(id前缀): j25_tc"}
    p["calls"][0]["status"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_classification"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_registry_id"] = "DEP-REG-001"
    cases["CASE-D01"] = {
        "cat": "DEP全阻塞", "desc": "短ID解析全阻塞 (合规阻塞, Gate不豁免)",
        "payload": p, "expect": FAIL}

    p = _ok_payload("j25_tc")
    p["calls"][0]["response_payload"] = {
        "id": "j25_tc", "resolved_id": "s_001", "points": [],
        "error": "HTTP 500 (伪造日志, 无请求URL/时间戳)"}
    p["calls"][0]["dep_classification"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_registry_id"] = None
    p["script_audit"]["has_id_consistency_assert"] = False
    cases["CASE-D02"] = {
        "cat": "DEP全阻塞", "desc": "借外部阻塞之名伪造日志 (内部P0)",
        "payload": p, "expect": FAIL}

    # ============ 大类四: 部分 DEP 恢复 (原 v1) ============
    cases["CASE-P01"] = {
        "cat": "部分恢复", "desc": "部分短ID就绪 (混合状态, Gate未达阈值)",
        "payload": _part_payload(), "expect": FAIL}

    p = _part_payload()
    p["bridge_rate"] = 1.0
    p["calls"][1]["status"] = "COMPLETED"
    p["calls"][1]["dep_classification"] = None
    p["calls"][1]["dep_registry_id"] = None
    cases["CASE-P02"] = {
        "cat": "部分恢复", "desc": "恢复后残留旧口径 (增量污染)",
        "payload": p, "expect": FAIL}

    p = _part_payload()
    p["dep"] = {"registry": {"dep_registry_id": "DEP-REG-001",
                             "current_status": "RECOVERY"}}
    cases["CASE-P03"] = {
        "cat": "部分恢复", "desc": "DEP状态机迁移 (RECOVERY, Gate不豁免)",
        "payload": p, "expect": FAIL}

    # ============ 大类五: 存量旧口径残留 (v2 新增) ============
    p = _ok_payload()
    p["claimed_completed_count"] = 170   # STATUS.md 存量声称
    p["notes"] = {"summary": "170/170 COMPLETED, 100% bridge rate"}
    p["bridge_rate"] = 1.0
    cases["CASE-L01"] = {
        "cat": "存量旧口径", "desc": "STATUS.md存量170/170声称vs实测0% (LC-01/LC-02)",
        "payload": p, "expect": FAIL}

    p = _ok_payload()
    p["claimed_completed_count"] = 50
    p["real_fetchable_rate"] = 0.3
    cases["CASE-L02"] = {
        "cat": "存量旧口径", "desc": "声称完成数>实测可取数数 (LC-01)",
        "payload": p, "expect": FAIL}

    # ============ 大类六: DEP 状态机流转 (v2 新增) ============
    def _dep_pkg(history, status):
        ev = _ok_payload()
        ev["dep"] = {
            "registry": {
                "dep_registry_id": "DEP-REG-001",
                "current_status": status,
                "state_history": history,
            }}
        return ev

    cases["CASE-S01"] = {
        "cat": "DEP状态机",
        "desc": "合法迁移链 REGISTER→BLOCK→RECOVERY→RECOVERED (DS-02/03)",
        "payload": _dep_pkg([
            {"event": "DEP_REGISTER", "status_after": "ACTIVE"},
            {"event": "DEP_BLOCK", "status_after": "BLOCKED"},
            {"event": "DEP_RECOVERY_DETECT", "status_after": "RECOVERY"},
            {"event": "DEP_AUTO_VERIFY_PASS", "status_after": "RECOVERED"},
        ], "RECOVERED"),
        "expect": PASS}

    cases["CASE-S02"] = {
        "cat": "DEP状态机",
        "desc": "非法迁移: ACTIVE 直接到 RECOVERED (DS-02 阻断)",
        "payload": _dep_pkg([
            {"event": "DEP_REGISTER", "status_after": "ACTIVE"},
            {"event": "DEP_AUTO_VERIFY_PASS", "status_after": "RECOVERED"},
        ], "RECOVERED"),
        "expect": FAIL}

    cases["CASE-S03"] = {
        "cat": "DEP状态机",
        "desc": "迁移声明错误: BLOCKED+RECOVERY_DETECT 应到RECOVERY却声明ACTIVE",
        "payload": _dep_pkg([
            {"event": "DEP_REGISTER", "status_after": "ACTIVE"},
            {"event": "DEP_BLOCK", "status_after": "BLOCKED"},
            {"event": "DEP_RECOVERY_DETECT", "status_after": "ACTIVE"},
        ], "ACTIVE"),
        "expect": FAIL}

    # ============ 大类七: 跨团队 DEP 台账不一致 (v2 新增) ============
    def _xreg_pkg(dshb_view, dshe_view):
        ev = _ok_payload()
        ev["dep"] = {"registry": {"dep_registry_id": "DEP-REG-001",
                                  "current_status": "BLOCKED"},
                     "dshb_view": dshb_view, "dshe_view": dshe_view}
        return ev

    base = {"dep_registry_id": "DEP-REG-001", "current_status": "BLOCKED",
            "risk_level": "P0", "max_pause_days": 30,
            "rollback_window_min": 15, "impact_scope": "178条目"}
    cases["CASE-X01"] = {
        "cat": "跨团队台账", "desc": "台账一致 (DSHB API_ERROR 映射等价 DSHE BLOCKED)",
        "payload": _xreg_pkg(
            dict(base, current_status="API_ERROR"), dict(base)),
        "expect": PASS}

    cases["CASE-X02"] = {
        "cat": "跨团队台账",
        "desc": "台账不一致: DSHB ACTIVE vs DSHE BLOCKED (DS-05)",
        "payload": _xreg_pkg(
            dict(base, current_status="NORMAL"), dict(base)),
        "expect": FAIL}

    cases["CASE-X03"] = {
        "cat": "跨团队台账",
        "desc": "台账不一致: risk_level P1 vs P0 (DS-05)",
        "payload": _xreg_pkg(
            dict(base, risk_level="P1"), dict(base)),
        "expect": FAIL}

    # ============ 大类八: 契约与完整性边界 (v2 新增) ============
    p = _ok_payload()
    del p["md5_manifest"]
    cases["CASE-C01"] = {
        "cat": "契约完整性", "desc": "缺 md5_manifest 自述清单 (CV-05)",
        "payload": p, "expect": CONDITIONAL_PASS}

    p = _ok_payload()
    p["bridge_rate"] = 1.0
    p["metadata_rate"] = 1.0
    p["real_fetchable_rate"] = 0.3
    # 2 条 call: 1 条有效 1 条无效 -> 实测率 0.5, 但声称 1.0
    p["total_calls"] = 2
    p["calls"] = [
        dict(p["calls"][0]),
        {
            "trace_id": "DSHE-TEST_OK-001-002",
            "indicator_id": "s_001", "zhiji_short_id": "s_001",
            "request_payload": {"requested_id": "s_001"},
            "response_payload": {"id": "s_001", "resolved_id": "s_001",
                                 "points": []},
            "status": "DEPENDENCY_BLOCK",
            "call_type": "DSHE_INDEPENDENT_ZHIJI",
            "dep_classification": "DEPENDENCY_BLOCK",
            "dep_registry_id": "DEP-REG-001",
        },
    ]
    cases["CASE-C02"] = {
        "cat": "契约完整性",
        "desc": "桥接率分子虚增: 声称1.0 实测0.5 (D02.3)",
        "payload": p, "expect": FAIL}

    p = _ok_payload()
    del p["calls"][0]["trace_id"]
    cases["CASE-C03"] = {
        "cat": "契约完整性", "desc": "调用缺 trace_id (D03.1 阻断)",
        "payload": p, "expect": FAIL}

    p = _ok_payload()
    p["retired"] = True
    p["reused_from_run_id"] = "20260101_000000"
    cases["CASE-C04"] = {
        "cat": "契约完整性",
        "desc": "复用已退回旧 run_id (L2-R08 阻断)",
        "payload": p, "expect": FAIL}

    return cases


# ---------------------------------------------------------------------------
# 自回归断言 (v2 核心: 防止判定逻辑回归)
# ---------------------------------------------------------------------------
SELFTEST_ASSERTS = [
    # (用例ID, 必须含的检测点, 说明)
    ("CASE-N01", "D04.1", "虚假桥接率必触发 search 中转检测"),
    ("CASE-N01", "G-06", "G-06 阈值未达必强制阻断 (v1 修复项)"),
    ("CASE-D01", "DEP-GATE", "DEP 阻塞必记录 Gate 不豁免"),
    ("CASE-D02", "D04.2", "伪造日志必触发一致性断言失败"),
    ("CASE-P02", "D01.2", "增量污染必触发缺取数证据"),
    ("CASE-L01", "LC-01", "存量旧口径必触发 LC-01"),
    ("CASE-L01", "LC-02", "旧口径表述必触发 LC-02"),
    ("CASE-S01", None, "合法状态迁移链不应产生 DS 告警"),
    ("CASE-S02", "DS-02", "非法状态迁移必阻断"),
    ("CASE-S03", "DS-03", "迁移声明错误必阻断"),
    ("CASE-X01", None, "DSHB API_ERROR 应映射等价 DSHE BLOCKED, 不误报"),
    ("CASE-X02", "DS-05", "跨团队台账状态不一致必阻断"),
    ("CASE-X03", "DS-05", "跨团队台账 risk_level 不一致必阻断"),
    ("CASE-C01", "CV-05", "缺 md5_manifest 必触发契约完整性告警"),
    ("CASE-C02", "D02.3", "桥接率分子虚增必触发 D02.3"),
    ("CASE-C03", "D03.1", "缺 trace_id 必触发 D03.1"),
    ("CASE-C04", "L2-R08", "复用已退回 run_id 必触发 L2-R08"),
]

# 必须无告警的判定 (防误报回归)
NO_ALERT_ASSERTS = ["CASE-A01", "CASE-A02", "CASE-S01", "CASE-X01"]


def run_self_test(cases=None):
    """自回归测试: 用例回放 + 断言校验。失败返回非零。"""
    cases = cases or build_case_library()
    failures = []
    results = {}

    # 1. 全部用例判定符合预期
    for cid in sorted(cases):
        c = cases[cid]
        r = EvidenceAuditor(c["payload"]).verdict()
        ok = r["verdict"] == c["expect"]
        results[cid] = {"expect": c["expect"], "actual": r["verdict"],
                        "ok": ok, "report": r}
        if not ok:
            failures.append("用例判定不符: %s 预期=%s 实测=%s"
                            % (cid, c["expect"], r["verdict"]))

    # 2. 关键检测点断言 (必命中)
    for cid, dp, note in SELFTEST_ASSERTS:
        if cid not in results:
            failures.append("断言引用不存在的用例: %s" % cid)
            continue
        r = results[cid]["report"]
        dps = {e["detect_point"] for e in r["events"]}
        if dp is not None and dp not in dps:
            failures.append("必命中检测点缺失: %s 缺 %s (%s)" % (cid, dp, note))

    # 3. 无告警断言 (防误报)
    for cid in NO_ALERT_ASSERTS:
        if cid not in results:
            failures.append("无告警断言引用不存在用例: %s" % cid)
            continue
        r = results[cid]["report"]
        bad = [e for e in r["events"]
               if e["level"] in (CRITICAL, HIGH)]
        if bad:
            failures.append("误报: %s 应零 CRITICAL/HIGH, 实际 %s"
                            % (cid, [e["detect_point"] for e in bad]))

    # 4. 覆盖度断言
    all_dp = set()
    for cid, r in results.items():
        all_dp.update(e["detect_point"] for e in r["report"]["events"])
    expected_dp = {"D01.2", "D02.1", "D02.3", "D03.1", "D03.2", "D04.1",
                   "D04.2", "G-06", "DEP-GATE", "LC-01", "LC-02", "DS-02",
                   "DS-03", "DS-05", "L2-R08", "CV-05"}
    missing_dp = expected_dp - all_dp
    if missing_dp:
        failures.append("覆盖度不足, 缺检测点: %s" % sorted(missing_dp))

    # 5. 契约版本断言
    if CONTRACT_VERSION != "EVIDENCE_CONTRACT_V1":
        failures.append("契约版本常量异常: %s" % CONTRACT_VERSION)

    # 6. DEP 状态机完整性断言
    if not {"ACTIVE", "BLOCKED", "RECOVERY", "RECOVERED",
            "ROLLED_BACK", "CLOSED"} <= DEP_STATES:
        failures.append("DEP 状态集定义不完整: %s" % sorted(DEP_STATES))

    return failures, results


def render_self_test(failures, results):
    lines = []
    lines.append("=" * 70)
    lines.append("  evidence_auditor_v2 自回归测试  (auditor v%s, contract %s)"
                 % (AUDITOR_VERSION, CONTRACT_VERSION))
    lines.append("=" * 70)
    lines.append("  用例数: %d  |  断言数: %d 必命中 + %d 无误报  |  基线: %s"
                 % (len(results), len(SELFTEST_ASSERTS),
                    len(NO_ALERT_ASSERTS), BRANCH_BASELINE))
    lines.append("-" * 70)
    for cid in sorted(results):
        r = results[cid]
        lines.append("  %-10s 预期=%-16s 实测=%-16s %s"
                     % (cid, r["expect"], r["actual"],
                        "OK" if r["ok"] else "MISMATCH"))
    lines.append("-" * 70)
    lines.append("  关键检测点断言:")
    for cid, dp, note in SELFTEST_ASSERTS:
        ok = dp is None or dp in {e["detect_point"] for e in
                                  results[cid]["report"]["events"]} \
            if cid in results else False
        lines.append("    %-10s %-8s %s" % (cid, dp or "(无告警)",
                                            "PASS" if ok else "FAIL"))
    lines.append("  无告警断言 (防误报):")
    for cid in NO_ALERT_ASSERTS:
        bad = [e for e in results[cid]["report"]["events"]
               if e["level"] in (CRITICAL, HIGH)] if cid in results else []
        lines.append("    %-10s %s" % (cid, "PASS (零CRITICAL/HIGH)"
                                        if not bad else "FAIL"))
    lines.append("-" * 70)
    if failures:
        lines.append("  ❌ 自回归失败 %d 项:" % len(failures))
        for f in failures:
            lines.append("    - %s" % f)
        lines.append("  结论: SELF-TEST FAILED")
    else:
        lines.append("  ✅ 全部通过: %d 用例判定 + %d 必命中断言 + %d 无告警断言"
                     % (len(results), len(SELFTEST_ASSERTS),
                        len(NO_ALERT_ASSERTS)))
        lines.append("  结论: SELF-TEST PASSED")
    lines.append("=" * 70)
    return "\n".join(lines)


def render_report(result):
    lines = []
    lines.append("=" * 70)
    lines.append("  V86-RC2 证据包预审结论  (auditor v%s / %s)"
                 % (AUDITOR_VERSION, CONTRACT_VERSION))
    lines.append("=" * 70)
    mark = {PASS: "[PASS]", CONDITIONAL_PASS: "[CONDITIONAL]",
            FAIL: "[BLOCKED]"}.get(result["verdict"], result["verdict"])
    lines.append("  预审结论       : %s  %s" % (mark, result["verdict"]))
    lines.append("  Gate 结论      : %s" % result["gate_result"])
    lines.append("  G-06 真实可取数率: %s (阈值 %.0f%%)"
                 % (result["gate_g06_real_fetchable_rate"],
                    GATE_REAL_FETCHABLE_THRESHOLD * 100))
    lines.append("  G-09 脚本审计    : %s" % result["gate_g09_script_audit"])
    lines.append("  G-10 真实取数校验: %s" % result["gate_g10_data_fetch"])
    lines.append("  审计指纹       : %s" % result.get("fingerprint"))
    lines.append("  DEP 登记ID     : %s" % result.get("dep_registry_id"))
    s = result["events_summary"]
    lines.append("-" * 70)
    lines.append("  告警统计: CRITICAL=%d HIGH=%d MEDIUM=%d LOW=%d (合计 %d)"
                 % (s["CRITICAL"], s["HIGH"], s["MEDIUM"], s["LOW"],
                    s["total"]))
    if result.get("events_by_rule"):
        lines.append("  按规则: %s" % result["events_by_rule"])
    lines.append("-" * 70)
    if s["total"]:
        for e in result["events"]:
            dep = " DEP=%s" % e["dep_registry_id"] if e["dep_registry_id"] else ""
            lines.append("  %-9s %-14s %-8s %s%s"
                         % ("[%s]" % e["level"], e["rule"],
                            e["detect_point"], e["message"], dep))
    else:
        lines.append("  (无告警)")
    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 L1/L2 证据包独立校验器 v2 (%s)"
                    % CONTRACT_VERSION)
    ap.add_argument("--file", help="证据包 JSON 路径")
    ap.add_argument("--run-case-library", action="store_true",
                    help="回放全部用例")
    ap.add_argument("--self-test", action="store_true",
                    help="自回归测试 (用例回放 + 断言校验, 推荐每次改后执行)")
    ap.add_argument("--check-md5", help="校验文件 MD5")
    ap.add_argument("--expect", help="期望 MD5 (配 --check-md5)")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ap.add_argument("--persist", help="审计事件持久化输出路径")
    args = ap.parse_args(argv)

    if args.check_md5:
        r = check_md5(args.check_md5, args.expect)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["result"] in ("PASS", "COMPUTED") else 1

    if args.self_test:
        failures, results = run_self_test()
        print(render_self_test(failures, results))
        return 1 if failures else 0

    if args.run_case_library:
        cases = build_case_library()
        passed = failed = 0
        records = []
        print("V86-RC2 审计用例库回放 (CASE-LIB v%s, %d 用例)"
              % (CASE_LIB_VERSION, len(cases)))
        print("-" * 70)
        for cid in sorted(cases):
            c = cases[cid]
            r = EvidenceAuditor(c["payload"]).verdict()
            ok = r["verdict"] == c["expect"]
            passed += ok
            failed += (not ok)
            print("%-10s %-8s %-42s 预期=%-16s 实测=%-16s %s"
                  % (cid, c["cat"], c["desc"][:42], c["expect"],
                     r["verdict"], "OK" if ok else "MISMATCH"))
            records.append({"case_id": cid, "cat": c["cat"],
                            "desc": c["desc"], "expect": c["expect"],
                            "actual": r["verdict"], "match": ok,
                            "report": r})
        print("-" * 70)
        print("回放结果: %d/%d 判定符合预期 (%d 不符)"
              % (passed, len(cases), failed))
        if args.persist:
            with open(args.persist, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            print("审计事件已持久化: %s" % args.persist)
        return 0 if failed == 0 else 1

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
        if args.persist:
            with open(args.persist, "w", encoding="utf-8") as f:
                json.dump({"case_id": args.file, "report": r},
                          f, ensure_ascii=False, indent=2)
        return 0 if r["verdict"] != FAIL else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
