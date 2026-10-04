#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L1 Evidence Package Pre-Check Validator (l1_evidence_pre_check_v2.py)

工单: DSHB_V86_RC2_GATE_REG06_FIX_E2E / T3.5
约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

用途
----
独立校验 L1 证据包是否符合 EVIDENCE_CONTRACT_V1 契约 (V2.0.0 对齐
evidence_auditor_v2_plus 新增检测规则: PERF-GUARD, ROB-01, DS-06)。
作为 HERMES evidence_auditor_v2_plus.py 的前置预检器: 若预检通过,
evidence_auditor_v2_plus 也应通过。

V1 → V2 变更
-----------
新增 5 项校验 (23–27), 总计 27 项, 对齐 v2_plus auditor 新契约验证项:
  23. PERF-GUARD (PERF-01): 性能预算守卫
  24. ROB-01 (DAMAGE-01):   损坏/受损结构检测
  25. DS-06 (DEP-FLAP-01):  DEP 抖动检测
  26. CONTRACT-02:          契约版本对齐检查 (v2_plus 兼容)
  27. AUDIT-01:             审计服务紧急绕过交叉检查

原有 22 项校验完整保留, 向后兼容 (字段缺失时静默跳过, 不产生违规)。

用法
----
  python3 l1_evidence_pre_check_v2.py --file <evidence.json>              # 校验单个证据包
  python3 l1_evidence_pre_check_v2.py --file <evidence.json> --json       # JSON 输出
  python3 l1_evidence_pre_check_v2.py --file <evidence.json> --verbose    # 详细输出
  python3 l1_evidence_pre_check_v2.py --selftest                          # 自检 (合成夹具)
  python3 l1_evidence_pre_check_v2.py --check-md5 <file> [--expect <md5>] # MD5 校验

输出
----
  PASS / FAIL  + 详细违规列表 (JSON 格式)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

PRE_CHECK_VERSION = "2.0.0"
CONTRACT_VERSION = "EVIDENCE_CONTRACT_V1"
V2_PLUS_COMPATIBLE = True  # 本预检器 v2_plus 兼容标志

# ─── 常量 ───────────────────────────────────────────────────
VALID_STATUSES = {"INDEPENDENT_FETCH_OK", "FETCH_OK", "COMPLETED", "DEPENDENCY_BLOCK"}
VALID_CALL_TYPES_L1 = {"DSHB_L1_SELF_TEST"}
FINGERPRINT_PATTERN = re.compile(r"^DSHB-L1-\d{8}_\d{6}$")
ISO8601_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$")

REQUIRED_TOP_FIELDS = {
    "fingerprint": str,
    "run_id": str,
    "session_id": str,
    "total_calls": int,
    "generated_at": str,
    "caller": str,
    "dshb_reuse": bool,
    "metadata_rate": (int, float),
    "real_fetchable_rate": (int, float),
    "control_check": dict,
    "script_audit": dict,
    "calls": list,
    "contract_version": str,
}

CALL_REQUIRED_FIELDS = {
    "trace_id": str,
    "indicator_id": str,
    "short_id": str,
    "request_payload": dict,
    "response_payload": dict,
    "status": str,
    "call_type": str,
}

# 告警级别
CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

# V2 新增常量
PERF_BUDGET_MS = 60000         # 性能预算阈值: 60 秒
DS_FLAP_WINDOW_SECONDS = 900    # DEP 抖动检测窗口: 15 分钟


# ─── 违规记录 ───────────────────────────────────────────────
class Violation:
    """单条校验违规记录"""

    def __init__(self, level, rule, message, detail=None, trace_id=None):
        self.level = level
        self.rule = rule
        self.message = message
        self.detail = detail
        self.trace_id = trace_id
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self):
        d = {
            "level": self.level,
            "rule": self.rule,
            "message": self.message,
        }
        if self.detail:
            d["detail"] = self.detail
        if self.trace_id:
            d["trace_id"] = self.trace_id
        d["timestamp"] = self.timestamp
        return d

    def __repr__(self):
        return "[{}][{}] {}".format(self.level, self.rule, self.message)


# ─── 预检校验器 ─────────────────────────────────────────────
class L1EvidencePreChecker:
    """L1 证据包预检校验器 (EVIDENCE_CONTRACT_V1, v2_plus 对齐)"""

    def __init__(self, evidence, verbose=False):
        self.ev = evidence or {}
        self.violations = []
        self.verbose = verbose
        self.checks_run = []

    # ── 告警辅助 ────────────────────────────────────────────
    def emit(self, level, rule, message, detail=None, trace_id=None):
        v = Violation(level, rule, message, detail, trace_id)
        self.violations.append(v)
        if self.verbose:
            print("  [{}] {}: {}".format(level, rule, message))
        return v

    # ── 1. contract_version ─────────────────────────────────
    def check_contract_version_field(self):
        cv = self.ev.get("contract_version")
        if not cv:
            self.emit(CRITICAL, "CONTRACT-01",
                      "Missing contract_version field (EVIDENCE_CONTRACT_V1 required)")
        elif cv != CONTRACT_VERSION:
            self.emit(HIGH, "CONTRACT-01",
                      "contract_version mismatch: expected {}, got {}".format(
                          CONTRACT_VERSION, cv))
        self.checks_run.append("check_contract_version_field")

    # ── 2. 必填字段完整性 ───────────────────────────────────
    def check_required_fields(self):
        for field, expected_type in REQUIRED_TOP_FIELDS.items():
            if field not in self.ev:
                self.emit(CRITICAL, "FIELD-" + field.upper(),
                          "Missing required field: {}".format(field))
            elif not isinstance(self.ev.get(field), expected_type):
                self.emit(HIGH, "FIELD-" + field.upper() + "-TYPE",
                          "Field '{}' type mismatch: expected {}, got {}".format(
                              field, expected_type.__name__,
                              type(self.ev.get(field)).__name__))
        self.checks_run.append("check_required_fields")

    # ── 3. 审计指纹格式 ─────────────────────────────────────
    def check_fingerprint_format(self):
        fp = self.ev.get("fingerprint", "")
        if not fp:
            return
        if not FINGERPRINT_PATTERN.match(fp):
            self.emit(HIGH, "FORMAT-FP",
                      "Invalid fingerprint format: {} (expected DSHB-L1-YYYYMMDD_HHMMSS)".format(fp))
        self.checks_run.append("check_fingerprint_format")

    # ── 4. MD5 自校验 ───────────────────────────────────────
    def check_self_hash(self):
        if "self_hash" not in self.ev:
            self.emit(LOW, "HASH-01",
                      "No self_hash field (recommended for integrity verification)")
            return
        stored_hash = self.ev.get("self_hash")
        ev_copy = {k: v for k, v in self.ev.items() if k != "self_hash"}
        ev_str = json.dumps(ev_copy, sort_keys=True, ensure_ascii=False)
        computed_hash = hashlib.md5(ev_str.encode("utf-8")).hexdigest()
        if stored_hash != computed_hash:
            self.emit(CRITICAL, "HASH-02",
                      "MD5 self-hash mismatch",
                      "stored={}, computed={}".format(stored_hash, computed_hash))
        self.checks_run.append("check_self_hash")

    # ── 5. dshb_reuse ───────────────────────────────────────
    def check_dshb_reuse(self):
        val = self.ev.get("dshb_reuse")
        if val is not False:
            self.emit(CRITICAL, "REUSE-01",
                      "dshb_reuse must be False for independent evidence, got: {}".format(val))
        self.checks_run.append("check_dshb_reuse")

    # ── 6. call_type ────────────────────────────────────────
    def check_call_type(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            ct = c.get("call_type")
            if ct not in VALID_CALL_TYPES_L1:
                self.emit(HIGH, "CALL-TYPE",
                          "Invalid call_type for L1: {}".format(ct),
                          "Expected: {}".format(", ".join(sorted(VALID_CALL_TYPES_L1))),
                          c.get("trace_id"))
        self.checks_run.append("check_call_type")

    # ── 7. trace_id 唯一性 ──────────────────────────────────
    def check_trace_id_uniqueness(self):
        calls = self.ev.get("calls") or []
        seen = set()
        for c in calls:
            tid = c.get("trace_id")
            if not tid:
                self.emit(CRITICAL, "TRACE-ID", "Call missing trace_id")
                continue
            if tid in seen:
                self.emit(CRITICAL, "TRACE-ID-DUP",
                          "Duplicate trace_id: {}".format(tid), trace_id=tid)
            seen.add(tid)
        self.checks_run.append("check_trace_id_uniqueness")

    # ── 8. 调用条目结构 ─────────────────────────────────────
    def check_calls_structure(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id", "unknown")
            for field, expected_type in CALL_REQUIRED_FIELDS.items():
                val = c.get(field)
                if val is None:
                    self.emit(CRITICAL, "CALL-" + field.upper(),
                              "Call missing required field: {}".format(field),
                              trace_id=tid)
        self.checks_run.append("check_calls_structure")

    # ── 9. response_payload 结构 ────────────────────────────
    def check_response_payload(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id", "unknown")
            resp = c.get("response_payload")
            if not resp or not isinstance(resp, dict):
                self.emit(HIGH, "RESP-01", "Missing or invalid response_payload", trace_id=tid)
                continue
            for field in ("id", "resolved_id"):
                if field not in resp:
                    self.emit(HIGH, "RESP-" + field.upper(),
                              "response_payload missing field: {}".format(field),
                              trace_id=tid)
            points = resp.get("points")
            if points is None:
                self.emit(HIGH, "RESP-POINTS",
                          "response_payload missing points field", trace_id=tid)
            elif not isinstance(points, list):
                self.emit(HIGH, "RESP-POINTS-TYPE",
                          "response_payload.points must be a list", trace_id=tid)
            else:
                for pi, p in enumerate(points):
                    if not isinstance(p, dict):
                        self.emit(HIGH, "RESP-POINT-TYPE",
                                  "points[{}] must be a dict".format(pi),
                                  trace_id=tid)
                        continue
                    if "date" not in p:
                        self.emit(MEDIUM, "RESP-POINT-DATE",
                                  "points[{}] missing date field".format(pi),
                                  trace_id=tid)
                    if "value" not in p:
                        self.emit(MEDIUM, "RESP-POINT-VALUE",
                                  "points[{}] missing value field".format(pi),
                                  trace_id=tid)
        self.checks_run.append("check_response_payload")

    # ── 10. DEP 分类 ────────────────────────────────────────
    def check_dep_classification(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id", "unknown")
            cls = (c.get("dep_classification") or "").upper()
            if cls == "DEPENDENCY_BLOCK":
                if not c.get("dep_registry_id"):
                    self.emit(CRITICAL, "DEP-REG",
                              "DEPENDENCY_BLOCK call missing dep_registry_id",
                              trace_id=tid)
        self.checks_run.append("check_dep_classification")

    # ── 11. 速率字段 ────────────────────────────────────────
    def check_rates(self):
        for field in ("metadata_rate", "real_fetchable_rate"):
            val = self.ev.get(field)
            if val is None:
                continue
            if not isinstance(val, (int, float)):
                self.emit(HIGH, "RATE-" + field.upper(),
                          "{} must be a number, got {}".format(field, type(val).__name__))
            elif val < 0 or val > 1:
                self.emit(HIGH, "RATE-" + field.upper() + "-RANGE",
                          "{} must be between 0 and 1, got {}".format(field, val))
        self.checks_run.append("check_rates")

    # ── 12. 对照组 ──────────────────────────────────────────
    def check_control_check(self):
        ctrl = self.ev.get("control_check")
        if not ctrl or not isinstance(ctrl, dict):
            self.emit(HIGH, "CTRL-01", "control_check must be a dict")
            return
        for field in ("http_status", "has_nonzero_value"):
            if field not in ctrl:
                self.emit(HIGH, "CTRL-" + field.upper(),
                          "control_check missing field: {}".format(field))
        self.checks_run.append("check_control_check")

    # ── 13. 脚本审计 ────────────────────────────────────────
    def check_script_audit(self):
        sa = self.ev.get("script_audit")
        if not sa or not isinstance(sa, dict):
            self.emit(HIGH, "SCRIPT-AUDIT-01", "script_audit must be a dict")
            return
        for field in ("uses_search_passthrough", "has_id_consistency_assert",
                      "zero_value_counts_as_pass", "retains_raw_payload"):
            if field not in sa:
                self.emit(HIGH, "SCRIPT-AUDIT-" + field.upper(),
                          "script_audit missing field: {}".format(field))
        self.checks_run.append("check_script_audit")

    # ── 14. 时间戳格式 ──────────────────────────────────────
    def check_generated_at(self):
        ga = self.ev.get("generated_at", "")
        if not ga:
            return
        if not ISO8601_PATTERN.match(ga):
            self.emit(HIGH, "FORMAT-TS",
                      "Invalid ISO8601 timestamp: {}".format(ga))
        self.checks_run.append("check_generated_at")

    # ── 15. total_calls ─────────────────────────────────────
    def check_total_calls(self):
        tc = self.ev.get("total_calls")
        if tc is None:
            return
        if tc <= 0:
            self.emit(CRITICAL, "TOTAL-CALLS",
                      "total_calls must be > 0, got {}".format(tc))
        self.checks_run.append("check_total_calls")

    # ── 16. l1_pre_check 标志位 ─────────────────────────────
    def check_l1_pre_check_flag(self):
        if "l1_pre_check" not in self.ev:
            self.emit(LOW, "L1-FLAG",
                      "l1_pre_check flag not present (V3 feature)")
        self.checks_run.append("check_l1_pre_check_flag")

    # ── 17. short_id 一致性 ─────────────────────────────────
    def check_short_id_consistency(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id", "unknown")
            if "short_id" not in c:
                self.emit(CRITICAL, "SHORT-ID-01",
                          "Call missing short_id field", trace_id=tid)
            if "zhiji_short_id" not in c:
                self.emit(HIGH, "SHORT-ID-COMPAT",
                          "Call missing zhiji_short_id (needed for evidence_auditor compatibility)",
                          trace_id=tid)
            if c.get("short_id") != c.get("zhiji_short_id"):
                self.emit(MEDIUM, "SHORT-ID-INCONSISTENT",
                          "short_id != zhiji_short_id",
                          "short_id={}, zhiji_short_id={}".format(
                              c.get("short_id"), c.get("zhiji_short_id")),
                          trace_id=tid)
        self.checks_run.append("check_short_id_consistency")

    # ── 18. dep_block_all 一致性 ────────────────────────────
    def check_dep_block_all(self):
        if "dep_block_all" not in self.ev:
            return
        calls = self.ev.get("calls") or []
        if not calls:
            return
        dep_block_all = self.ev.get("dep_block_all")
        all_blocked = all(
            (c.get("status") or "").upper() == "DEPENDENCY_BLOCK"
            for c in calls
        )
        if dep_block_all and not all_blocked:
            self.emit(MEDIUM, "DEP-BLOCK-ALL",
                      "dep_block_all=True but not all calls are DEPENDENCY_BLOCK")
        if not dep_block_all and all_blocked:
            self.emit(MEDIUM, "DEP-BLOCK-ALL",
                      "dep_block_all=False but all calls are DEPENDENCY_BLOCK")
        self.checks_run.append("check_dep_block_all")

    # ── 19. 退回作废标记 ────────────────────────────────────
    def check_retire_flag(self):
        if self.ev.get("superseded_by"):
            self.emit(HIGH, "RETIRE-01", "Evidence marked superseded_by")
        if self.ev.get("retired") is True:
            self.emit(HIGH, "RETIRE-02", "Evidence marked retired")
        if self.ev.get("reused_from_run_id"):
            self.emit(CRITICAL, "RETIRE-03",
                      "Evidence references retired run_id: {}".format(
                          self.ev.get("reused_from_run_id")))
        self.checks_run.append("check_retire_flag")

    # ── 20. status 合法性 ───────────────────────────────────
    def check_status_values(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id", "unknown")
            status = c.get("status")
            if status not in VALID_STATUSES:
                self.emit(HIGH, "STATUS-VAL",
                          "Invalid status: {} (valid: {})".format(
                              status, ", ".join(sorted(VALID_STATUSES))),
                          trace_id=tid)
        self.checks_run.append("check_status_values")

    # ── 21. request_payload 结构 ────────────────────────────
    def check_request_payload(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id", "unknown")
            req = c.get("request_payload")
            if not req or not isinstance(req, dict):
                self.emit(HIGH, "REQ-01",
                          "Missing or invalid request_payload", trace_id=tid)
                continue
            for field in ("requested_id", "independent"):
                if field not in req:
                    self.emit(MEDIUM, "REQ-" + field.upper(),
                              "request_payload missing field: {}".format(field),
                              trace_id=tid)
        self.checks_run.append("check_request_payload")

    # ── 22. calls 数量一致性 ────────────────────────────────
    def check_call_count(self):
        calls = self.ev.get("calls") or []
        total_calls = self.ev.get("total_calls", 0)
        if total_calls > 0 and len(calls) == 0:
            self.emit(CRITICAL, "CALLS-EMPTY",
                      "total_calls={} but calls array is empty".format(total_calls))
        elif len(calls) > 0 and total_calls > 0 and total_calls != len(calls):
            self.emit(MEDIUM, "CALLS-COUNT",
                      "total_calls={} but calls array has {} entries".format(
                          total_calls, len(calls)),
                      "Note: sample calls may not represent all total_calls")
        self.checks_run.append("check_call_count")

    # ── 23. PERF-GUARD (PERF-01): 性能预算守卫 ──────────────
    def check_perf_guard(self):
        """PERF-01: 检查 perf_guard 字段与性能预算
        - perf_guard 缺失 → 静默跳过 (向后兼容)
        - audit_duration_ms > PERF_BUDGET_MS → PERF_VIOLATION warning
        - perf_guard.enabled=True 且超时 → HIGH
        - perf_guard.enabled=False 且超时 → MEDIUM
        """
        pg = self.ev.get("perf_guard")
        if pg is None:
            self.checks_run.append("check_perf_guard")
            return

        if not isinstance(pg, dict):
            self.emit(HIGH, "PERF-GUARD-TYPE",
                      "perf_guard must be a dict, got {}".format(type(pg).__name__))
            self.checks_run.append("check_perf_guard")
            return

        duration = pg.get("audit_duration_ms")
        if duration is None:
            self.emit(MEDIUM, "PERF-GUARD-MISSING-DURATION",
                      "perf_guard present but audit_duration_ms field is missing")
            self.checks_run.append("check_perf_guard")
            return

        if not isinstance(duration, (int, float)):
            self.emit(HIGH, "PERF-GUARD-DURATION-TYPE",
                      "perf_guard.audit_duration_ms must be a number, got {}".format(
                          type(duration).__name__))
            self.checks_run.append("check_perf_guard")
            return

        enabled = pg.get("enabled", True)
        exceeded = duration > PERF_BUDGET_MS

        if exceeded:
            detail_msg = "audit_duration_ms={} exceeds budget {}ms".format(
                duration, PERF_BUDGET_MS)
            if enabled:
                self.emit(HIGH, "PERF-01-VIOLATION",
                          "PERF-VIOLATION: Performance budget exceeded with guard enabled",
                          detail_msg)
            else:
                self.emit(MEDIUM, "PERF-01-VIOLATION",
                          "PERF-VIOLATION: Performance budget exceeded (guard disabled)",
                          detail_msg)
        # duration <= PERF_BUDGET_MS → PASS (no violation)

        self.checks_run.append("check_perf_guard")

    # ── 24. ROB-01 (DAMAGE-01): 损坏/受损结构检测 ────────────
    def check_rob_01(self):
        """ROB-01: 检查 robustness_check 字段与损坏检测
        - robustness_check 缺失 → 静默跳过 (向后兼容)
        - json_validity 验证 (VALID/PARTIAL/INVALID)
        - damage_detected=True → HIGH with damage details
        - recovery_action 验证 (BYPASS/FAIL/QUARANTINE)
        - json_validity=INVALID + recovery_action=FAIL → CRITICAL
        """
        rc = self.ev.get("robustness_check")
        if rc is None:
            self.checks_run.append("check_rob_01")
            return

        if not isinstance(rc, dict):
            self.emit(HIGH, "ROB-01-TYPE",
                      "robustness_check must be a dict, got {}".format(type(rc).__name__))
            self.checks_run.append("check_rob_01")
            return

        # 验证 json_validity
        json_validity = rc.get("json_validity", "").upper()
        valid_values = {"VALID", "PARTIAL", "INVALID"}
        if json_validity not in valid_values:
            self.emit(HIGH, "ROB-01-VALIDITY",
                      "robustness_check.json_validity invalid value: '{}' (valid: {})".format(
                          json_validity, ", ".join(sorted(valid_values))))

        # 验证 damage_detected
        damage_detected = rc.get("damage_detected")
        if damage_detected is not None and not isinstance(damage_detected, bool):
            self.emit(HIGH, "ROB-01-DAMAGE-TYPE",
                      "robustness_check.damage_detected must be a boolean")

        if damage_detected is True:
            damage_details = rc.get("damage_details")
            detail_str = "damage_details={}".format(
                damage_details) if damage_details else "no damage details provided"
            self.emit(HIGH, "ROB-01-DAMAGE",
                      "ROB-01: Damage detected in evidence structure",
                      detail_str)

        # 验证 recovery_action
        recovery_action = (rc.get("recovery_action") or "").upper()
        valid_actions = {"BYPASS", "FAIL", "QUARANTINE"}
        if recovery_action and recovery_action not in valid_actions:
            self.emit(MEDIUM, "ROB-01-RECOVERY",
                      "robustness_check.recovery_action invalid value: '{}' "
                      "(valid: {})".format(
                          recovery_action, ", ".join(sorted(valid_actions))))

        # 严重组合: INVALID + FAIL → CRITICAL
        if json_validity == "INVALID" and recovery_action == "FAIL":
            self.emit(CRITICAL, "ROB-01-CRITICAL",
                      "CRITICAL: json_validity=INVALID combined with recovery_action=FAIL "
                      "— unrecoverable evidence damage")

        self.checks_run.append("check_rob_01")

    # ── 25. DS-06 (DEP-FLAP-01): DEP 抖动检测 ───────────────
    def check_ds_06(self):
        """DS-06: 检查 dep_flapping_check 字段与 DEP 抖动
        - dep_flapping_check 缺失 → 静默跳过 (向后兼容)
        - flap_detected=True → HIGH with flap details
        - flap_window_seconds > 900 → HIGH
        - flap_count > 0 → 检查状态历史
        - 15min 窗口内 BLOCKED→ACTIVE→BLOCKED 多次抖动 → CRITICAL
        """
        dfc = self.ev.get("dep_flapping_check")
        if dfc is None:
            self.checks_run.append("check_ds_06")
            return

        if not isinstance(dfc, dict):
            self.emit(HIGH, "DS-06-TYPE",
                      "dep_flapping_check must be a dict, got {}".format(type(dfc).__name__))
            self.checks_run.append("check_ds_06")
            return

        flap_detected = dfc.get("flap_detected")
        if flap_detected is not None and not isinstance(flap_detected, bool):
            self.emit(HIGH, "DS-06-FLAP-TYPE",
                      "dep_flapping_check.flap_detected must be a boolean")

        if flap_detected is True:
            flap_count = dfc.get("flap_count", 0)
            flap_window = dfc.get("flap_window_seconds", 0)
            flap_details = "flap_detected=True, flap_count={}, flap_window_seconds={}".format(
                flap_count, flap_window)
            self.emit(HIGH, "DS-06-FLAP",
                      "DS-06: DEP flapping detected",
                      flap_details)

        # 验证 flap_window_seconds
        flap_window_seconds = dfc.get("flap_window_seconds")
        if flap_window_seconds is not None:
            if not isinstance(flap_window_seconds, (int, float)):
                self.emit(HIGH, "DS-06-WINDOW-TYPE",
                          "dep_flapping_check.flap_window_seconds must be a number")
            elif flap_window_seconds > DS_FLAP_WINDOW_SECONDS:
                self.emit(HIGH, "DS-06-WINDOW-EXCEEDED",
                          "dep_flapping_check.flap_window_seconds={} exceeds limit {}s (15min)".format(
                              flap_window_seconds, DS_FLAP_WINDOW_SECONDS))

        # 验证 flap_count
        flap_count = dfc.get("flap_count")
        if flap_count is not None:
            if not isinstance(flap_count, int) or flap_count < 0:
                self.emit(HIGH, "DS-06-COUNT-TYPE",
                          "dep_flapping_check.flap_count must be a non-negative integer")

        # 检查 dep_status_history 的抖动模式
        dep_status_history = dfc.get("dep_status_history")
        if dep_status_history is not None:
            if not isinstance(dep_status_history, list):
                self.emit(HIGH, "DS-06-HISTORY-TYPE",
                          "dep_flapping_check.dep_status_history must be a list")
            else:
                # 统计 BLOCKED→ACTIVE→BLOCKED 完整抖动周期数
                flap_cycles = 0
                in_blocked_phase = False
                blocked_to_active = False
                for i, status in enumerate(dep_status_history):
                    status_upper = (status or "").upper()
                    if status_upper == "BLOCKED" and not in_blocked_phase:
                        in_blocked_phase = True
                        blocked_to_active = False
                    elif status_upper == "ACTIVE" and in_blocked_phase:
                        blocked_to_active = True
                    elif status_upper == "BLOCKED" and blocked_to_active:
                        flap_cycles += 1
                        blocked_to_active = False
                        in_blocked_phase = True  # 已在 BLOCKED

                # 15min 窗口内多次抖动 → CRITICAL
                if flap_cycles >= 2:
                    self.emit(CRITICAL, "DS-06-CRITICAL-FLAP",
                              "CRITICAL: {} BLOCKED→ACTIVE→BLOCKED flap cycles detected "
                              "within {}s window — likely DEP flapping storm".format(
                                  flap_cycles, DS_FLAP_WINDOW_SECONDS))
                elif flap_cycles == 1 and dfc.get("flap_window_seconds", 0) <= DS_FLAP_WINDOW_SECONDS:
                    self.emit(HIGH, "DS-06-FLAP-CYCLE",
                              "Single flap cycle within {}s window".format(
                                  DS_FLAP_WINDOW_SECONDS))

        self.checks_run.append("check_ds_06")

    # ── 26. CONTRACT-02: 契约版本对齐检查 ────────────────────
    def check_contract_alignment(self):
        """CONTRACT-02: 验证 v2_plus 兼容性
        - v2_plus_compatible 字段缺失 → MEDIUM (前向兼容警告)
        - v2_plus_compatible=False → HIGH
        """
        compat = self.ev.get("v2_plus_compatible")
        if compat is None:
            self.emit(MEDIUM, "CONTRACT-02",
                      "v2_plus_compatible flag missing — forward compatibility warning "
                      "(add v2_plus_compatible=True for v2_plus auditor)")
            self.checks_run.append("check_contract_alignment")
            return

        if compat is False:
            self.emit(HIGH, "CONTRACT-02",
                      "v2_plus_compatible=False — evidence not aligned with v2_plus auditor contract")
        elif compat is True:
            pass  # PASS — compatible
        else:
            self.emit(HIGH, "CONTRACT-02-TYPE",
                      "v2_plus_compatible must be a boolean, got {}".format(type(compat).__name__))

        self.checks_run.append("check_contract_alignment")

    # ── 27. AUDIT-01: 审计服务紧急绕过交叉检查 ───────────────
    def check_audit_service_bypass(self):
        """AUDIT-01: 检查 audit_service_emergency_bypass
        - bypass 字段缺失 → 静默跳过 (向后兼容)
        - bypass=True 但无双审批指纹 → CRITICAL
        - bypass=True 且有审批 → PASS (with note)
        - bypass=False → PASS
        """
        bypass = self.ev.get("audit_service_emergency_bypass")
        if bypass is None:
            self.checks_run.append("check_audit_service_bypass")
            return

        if not isinstance(bypass, bool):
            self.emit(HIGH, "AUDIT-01-TYPE",
                      "audit_service_emergency_bypass must be a boolean, got {}".format(
                          type(bypass).__name__))
            self.checks_run.append("check_audit_service_bypass")
            return

        if bypass is True:
            # 验证双审批指纹
            approval = self.ev.get("dual_approval_fingerprint")
            if not approval:
                self.emit(CRITICAL, "AUDIT-01-NO-APPROVAL",
                          "CRITICAL: audit_service_emergency_bypass=True but "
                          "dual_approval_fingerprint is missing — unauthorized bypass")
            elif not isinstance(approval, dict):
                self.emit(CRITICAL, "AUDIT-01-APPROVAL-TYPE",
                          "dual_approval_fingerprint must be a dict when bypass is enabled")
            else:
                # 检查审批结构完整性
                for field in ("approver_1", "approver_2", "timestamp", "reason"):
                    if field not in approval:
                        self.emit(HIGH, "AUDIT-01-APPROVAL-MISSING",
                                  "dual_approval_fingerprint missing required field: {}".format(field))

        self.checks_run.append("check_audit_service_bypass")

    # ── 执行全部检查 ────────────────────────────────────────
    def check_all(self):
        """运行全部 27 项检查 (22 V1 + 5 V2), 返回结果 dict"""
        # V1 检查 (1–22)
        self.check_contract_version_field()
        self.check_required_fields()
        self.check_fingerprint_format()
        self.check_self_hash()
        self.check_dshb_reuse()
        self.check_call_type()
        self.check_trace_id_uniqueness()
        self.check_calls_structure()
        self.check_response_payload()
        self.check_dep_classification()
        self.check_rates()
        self.check_control_check()
        self.check_script_audit()
        self.check_generated_at()
        self.check_total_calls()
        self.check_l1_pre_check_flag()
        self.check_short_id_consistency()
        self.check_dep_block_all()
        self.check_retire_flag()
        self.check_status_values()
        self.check_request_payload()
        self.check_call_count()
        # V2 检查 (23–27)
        self.check_perf_guard()
        self.check_rob_01()
        self.check_ds_06()
        self.check_contract_alignment()
        self.check_audit_service_bypass()
        return self.result()

    # ── 生成结果 ────────────────────────────────────────────
    def result(self):
        has_critical = any(v.level == CRITICAL for v in self.violations)
        has_high = any(v.level == HIGH for v in self.violations)

        # 新增: 违规分类统计
        rule_categories = {}
        for v in self.violations:
            cat = v.rule.split("-")[0] if v.rule else "UNKNOWN"
            rule_categories[cat] = rule_categories.get(cat, 0) + 1

        # 新增: 检测新增违规类别
        new_violation_categories = set()
        for v in self.violations:
            rule = v.rule or ""
            if rule.startswith(("PERF", "ROB", "DS-06", "CONTRACT-02", "AUDIT-01")):
                new_violation_categories.add(rule.split("-")[0] + "-class")

        return {
            "pre_check_version": PRE_CHECK_VERSION,
            "contract_version": CONTRACT_VERSION,
            "v2_plus_compatible": V2_PLUS_COMPATIBLE,
            "verdict": "FAIL" if (has_critical or has_high) else "PASS",
            "checked_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fingerprint": self.ev.get("fingerprint"),
            "run_id": self.ev.get("run_id"),
            "violations_summary": {
                "CRITICAL": sum(1 for v in self.violations if v.level == CRITICAL),
                "HIGH": sum(1 for v in self.violations if v.level == HIGH),
                "MEDIUM": sum(1 for v in self.violations if v.level == MEDIUM),
                "LOW": sum(1 for v in self.violations if v.level == LOW),
                "total": len(self.violations),
            },
            "violations": [v.to_dict() for v in self.violations],
            "checks_run": self.checks_run,
            "v2_new_checks": [
                "check_perf_guard",
                "check_rob_01",
                "check_ds_06",
                "check_contract_alignment",
                "check_audit_service_bypass",
            ],
            "rule_categories": rule_categories,
            "new_violation_categories": sorted(new_violation_categories),
        }


# ─── 辅助函数 ───────────────────────────────────────────────
def compute_json_md5(obj):
    """计算 JSON 对象的 MD5 (排除 self_hash 字段)"""
    if isinstance(obj, dict) and "self_hash" in obj:
        obj = {k: v for k, v in obj.items() if k != "self_hash"}
    ev_str = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(ev_str.encode("utf-8")).hexdigest()


def check_file_md5(path, expect=None):
    """校验文件 MD5, 返回结果 dict"""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if expect is None:
        return {"file": path, "md5": actual, "result": "COMPUTED"}
    return {
        "file": path,
        "expected": expect,
        "actual": actual,
        "result": "PASS" if actual == expect else "FAIL",
    }


# ─── 自检用例 ───────────────────────────────────────────────
def _valid_evidence(short_id="ID02226332"):
    """构建一个合法的 L1 证据包"""
    now = datetime.utcnow()
    evidence = {
        "contract_version": CONTRACT_VERSION,
        "l1_pre_check": True,
        "v2_plus_compatible": True,
        "fingerprint": "DSHB-L1-{}_{}".format(
            now.strftime("%Y%m%d"),
            now.strftime("%H%M%S")),
        "run_id": now.strftime("%Y%m%d_%H%M%S"),
        "session_id": "DSHB-V86-RC2-{}".format(int(__import__("time").time())),
        "total_calls": 1,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%S.000000"),
        "caller": "DSHB_V86_RC2_L1_SELF_TEST",
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
        "dep_block_all": False,
        "calls": [{
            "trace_id": "DSHB-L1-TEST-001",
            "indicator_id": short_id,
            "short_id": short_id,
            "zhiji_short_id": short_id,
            "request_payload": {"requested_id": short_id, "independent": True},
            "response_payload": {
                "id": short_id,
                "resolved_id": short_id,
                "points": [{"date": "2026-08-31", "value": "30700"}],
            },
            "status": "INDEPENDENT_FETCH_OK",
            "call_type": "DSHB_L1_SELF_TEST",
            "dep_classification": "NONE",
            "dep_registry_id": None,
        }],
    }
    evidence["self_hash"] = compute_json_md5(evidence)
    return evidence


def build_selftest_cases():
    """构建自检用例集 (V1 用例 V01–V17 + V2 用例 V18–V24)"""
    cases = {}

    # ─── V1 用例 (1–17) ─────────────────────────────────────
    # 1. 合法证据 → PASS
    cases["CASE-V01"] = {
        "desc": "Valid L1 evidence with all fields",
        "payload": _valid_evidence(),
        "expect": "PASS",
    }

    # 2. 缺 fingerprint → FAIL
    p = _valid_evidence()
    del p["fingerprint"]
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V02"] = {
        "desc": "Missing fingerprint field",
        "payload": p, "expect": "FAIL",
    }

    # 3. 缺 contract_version → FAIL
    p = _valid_evidence()
    del p["contract_version"]
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V03"] = {
        "desc": "Missing contract_version field",
        "payload": p, "expect": "FAIL",
    }

    # 4. 非法 fingerprint 格式 → FAIL
    p = _valid_evidence()
    p["fingerprint"] = "INVALID_FORMAT_001"
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V04"] = {
        "desc": "Invalid fingerprint format",
        "payload": p, "expect": "FAIL",
    }

    # 5. MD5 不匹配 → FAIL
    p = _valid_evidence()
    p["self_hash"] = "deadbeefdeadbeefdeadbeefdeadbeef"
    cases["CASE-V05"] = {
        "desc": "MD5 self-hash mismatch",
        "payload": p, "expect": "FAIL",
    }

    # 6. dshb_reuse=True → FAIL
    p = _valid_evidence()
    p["dshb_reuse"] = True
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V06"] = {
        "desc": "dshb_reuse=True (backing reference)",
        "payload": p, "expect": "FAIL",
    }

    # 7. trace_id 重复 → FAIL
    p = _valid_evidence()
    p["total_calls"] = 2
    call2 = dict(p["calls"][0])
    call2["trace_id"] = p["calls"][0]["trace_id"]
    p["calls"] = [p["calls"][0], call2]
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V07"] = {
        "desc": "Duplicate trace_id",
        "payload": p, "expect": "FAIL",
    }

    # 8. DEP 阻塞缺 dep_registry_id → FAIL
    p = _valid_evidence()
    p["calls"][0]["status"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_classification"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_registry_id"] = None
    p["calls"][0]["response_payload"]["points"] = []
    p["calls"][0]["response_payload"]["error"] = "HTTP 500"
    p["real_fetchable_rate"] = 0.0
    p["dep_block_all"] = True
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V08"] = {
        "desc": "DEPENDENCY_BLOCK missing dep_registry_id",
        "payload": p, "expect": "FAIL",
    }

    # 9. 缺 short_id → FAIL
    p = _valid_evidence()
    del p["calls"][0]["short_id"]
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V09"] = {
        "desc": "Call missing short_id field",
        "payload": p, "expect": "FAIL",
    }

    # 10. 非法 call_type → FAIL
    p = _valid_evidence()
    p["calls"][0]["call_type"] = "UNKNOWN_TYPE"
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V10"] = {
        "desc": "Invalid call_type",
        "payload": p, "expect": "FAIL",
    }

    # 11. 缺多个必填字段 → FAIL
    p = _valid_evidence()
    del p["run_id"]
    del p["session_id"]
    del p["total_calls"]
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V11"] = {
        "desc": "Multiple required fields missing",
        "payload": p, "expect": "FAIL",
    }

    # 12. total_calls=0 → FAIL
    p = _valid_evidence()
    p["total_calls"] = 0
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V12"] = {
        "desc": "total_calls=0",
        "payload": p, "expect": "FAIL",
    }

    # 13. 非法 status → FAIL
    p = _valid_evidence()
    p["calls"][0]["status"] = "INVALID_STATUS"
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V13"] = {
        "desc": "Invalid status value",
        "payload": p, "expect": "FAIL",
    }

    # 14. 合法证据 (含 zhiji_short_id) → PASS
    cases["CASE-V14"] = {
        "desc": "Valid evidence with zhiji_short_id compat field",
        "payload": _valid_evidence("j25_tc"),
        "expect": "PASS",
    }

    # 15. 缺 zhiji_short_id → FAIL (evidence_auditor 兼容)
    p = _valid_evidence()
    del p["calls"][0]["zhiji_short_id"]
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V15"] = {
        "desc": "Missing zhiji_short_id (evidence_auditor compat fail)",
        "payload": p, "expect": "FAIL",
    }

    # 16. 标记 retired → FAIL
    p = _valid_evidence()
    p["retired"] = True
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V16"] = {
        "desc": "Evidence marked retired",
        "payload": p, "expect": "FAIL",
    }

    # 17. DEP 合法 (含 dep_registry_id) → PASS
    p = _valid_evidence()
    p["calls"][0]["status"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_classification"] = "DEPENDENCY_BLOCK"
    p["calls"][0]["dep_registry_id"] = "DEP-REG-001"
    p["calls"][0]["response_payload"]["points"] = []
    p["calls"][0]["response_payload"]["error"] = "HTTP 500"
    p["real_fetchable_rate"] = 0.0
    p["dep_block_all"] = True
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V17"] = {
        "desc": "Valid DEP block with dep_registry_id",
        "payload": p, "expect": "PASS",
    }

    # ─── V2 用例 (18–24) ─────────────────────────────────────
    # 18. PERF-GUARD 启用, 在预算内 → PASS
    p = _valid_evidence()
    p["perf_guard"] = {
        "enabled": True,
        "audit_duration_ms": 45000,
        "budget_ms": 60000,
    }
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V18"] = {
        "desc": "PERF-GUARD enabled, within budget (45s < 60s)",
        "payload": p, "expect": "PASS",
    }

    # 19. PERF-GUARD 超出预算 → FAIL
    p = _valid_evidence()
    p["perf_guard"] = {
        "enabled": True,
        "audit_duration_ms": 90000,
        "budget_ms": 60000,
    }
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V19"] = {
        "desc": "PERF-GUARD exceeded budget (90s > 60s)",
        "payload": p, "expect": "FAIL",
    }

    # 20. ROB-01 无损坏 → PASS
    p = _valid_evidence()
    p["robustness_check"] = {
        "json_validity": "VALID",
        "damage_detected": False,
        "recovery_action": None,
    }
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V20"] = {
        "desc": "ROB-01 no damage detected",
        "payload": p, "expect": "PASS",
    }

    # 21. ROB-01 检测到损坏 → FAIL
    p = _valid_evidence()
    p["robustness_check"] = {
        "json_validity": "INVALID",
        "damage_detected": True,
        "damage_details": "truncated JSON at position 1247",
        "recovery_action": "FAIL",
    }
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V21"] = {
        "desc": "ROB-01 damage detected (INVALID + FAIL → CRITICAL)",
        "payload": p, "expect": "FAIL",
    }

    # 22. DS-06 无抖动 → PASS
    p = _valid_evidence()
    p["dep_flapping_check"] = {
        "flap_detected": False,
        "flap_count": 0,
        "flap_window_seconds": 300,
        "dep_status_history": ["ACTIVE", "ACTIVE", "ACTIVE"],
    }
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V22"] = {
        "desc": "DS-06 no DEP flapping",
        "payload": p, "expect": "PASS",
    }

    # 23. DS-06 DEP 抖动检测 → FAIL
    p = _valid_evidence()
    p["dep_flapping_check"] = {
        "flap_detected": True,
        "flap_count": 2,
        "flap_window_seconds": 600,
        "dep_status_history": ["BLOCKED", "ACTIVE", "BLOCKED", "ACTIVE", "BLOCKED"],
    }
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V23"] = {
        "desc": "DS-06 DEP flapping detected (2 flap cycles in 10min)",
        "payload": p, "expect": "FAIL",
    }

    # 24. 紧急绕过无审批 → FAIL
    p = _valid_evidence()
    p["audit_service_emergency_bypass"] = True
    # 故意不提供 dual_approval_fingerprint
    p["self_hash"] = compute_json_md5(p)
    cases["CASE-V24"] = {
        "desc": "Emergency bypass without dual approval (CRITICAL)",
        "payload": p, "expect": "FAIL",
    }

    return cases


# ─── 报告渲染 ───────────────────────────────────────────────
def render_report(result):
    lines = []
    lines.append("=" * 68)
    lines.append("  L1 Evidence Pre-Check Result  (v{})".format(PRE_CHECK_VERSION))
    lines.append("  Contract: {}  |  v2_plus_compatible: {}".format(
        CONTRACT_VERSION, result.get("v2_plus_compatible", "N/A")))
    lines.append("=" * 68)
    v = result["verdict"]
    mark = {"PASS": "[PASS]", "FAIL": "[BLOCKED]"}[v]
    lines.append("  Verdict     : {}  {}".format(mark, v))
    lines.append("  Fingerprint : {}".format(result.get("fingerprint", "N/A")))
    lines.append("  Run ID      : {}".format(result.get("run_id", "N/A")))
    s = result["violations_summary"]
    lines.append("-" * 68)
    lines.append("  Violations: CRITICAL={:<4} HIGH={:<4} MEDIUM={:<4} LOW={:<4} (total {})".format(
        s["CRITICAL"], s["HIGH"], s["MEDIUM"], s["LOW"], s["total"]))
    lines.append("-" * 68)
    if s["total"]:
        for vi in result["violations"]:
            lines.append("  {:<30} {:<20} {}".format(
                "[{}]".format(vi["level"]),
                "{}/{}".format(vi.get("rule", ""), vi.get("rule", "")),
                vi["message"]))
    else:
        lines.append("  (no violations)")
    # V2 新增: 显示新违规类别
    new_cats = result.get("new_violation_categories", [])
    if new_cats:
        lines.append("-" * 68)
        lines.append("  V2 violation categories: {}".format(", ".join(sorted(new_cats))))
    lines.append("=" * 68)
    return "\n".join(lines)


# ─── CLI 入口 ───────────────────────────────────────────────
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="L1 Evidence Package Pre-Check Validator V2 "
                    "(EVIDENCE_CONTRACT_V1, v2_plus aligned)")
    ap.add_argument("--file", help="Evidence JSON path")
    ap.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    ap.add_argument("--check-md5", help="Check file MD5")
    ap.add_argument("--expect", help="Expected MD5 (with --check-md5)")
    ap.add_argument("--selftest", action="store_true", help="Run self-test with synthetic cases")
    args = ap.parse_args(argv)

    # MD5 模式
    if args.check_md5:
        r = check_file_md5(args.check_md5, args.expect)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["result"] in ("PASS", "COMPUTED") else 1

    # 自检模式
    if args.selftest:
        cases = build_selftest_cases()
        passed = failed = 0
        records = []
        print("L1 Evidence Pre-Check Self-Test  (v{}, {} cases)".format(
            PRE_CHECK_VERSION, len(cases)))
        print("-" * 68)
        for cid in sorted(cases):
            c = cases[cid]
            checker = L1EvidencePreChecker(c["payload"])
            r = checker.check_all()
            ok = (r["verdict"] == c["expect"])
            passed += ok
            failed += (not ok)
            print("{:<10} {:<50} expected={:<10} actual={:<10} {}".format(
                cid, c["desc"][:50], c["expect"], r["verdict"],
                "OK" if ok else "MISMATCH"))
            records.append({
                "case_id": cid,
                "desc": c["desc"],
                "expect": c["expect"],
                "actual": r["verdict"],
                "match": ok,
                "report": r,
            })
        print("-" * 68)
        print("Self-test result: {}/{} matched ({}/{} mismatched)".format(
            passed, len(cases), failed, len(cases)))
        return 0 if failed == 0 else 1

    # 单文件校验
    if args.file:
        if not os.path.exists(args.file):
            print("ERROR: File not found: {}".format(args.file))
            return 2
        try:
            with open(args.file, encoding="utf-8") as f:
                ev = json.load(f)
        except Exception as e:
            print("ERROR: Failed to parse JSON: {}".format(e))
            return 2

        checker = L1EvidencePreChecker(ev, verbose=args.verbose)
        r = checker.check_all()

        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print(render_report(r))
            if args.verbose and r["violations"]:
                print("\n  [Detailed Violations]")
                for vi in r["violations"]:
                    print("    [{}] {}: {}".format(
                        vi["level"], vi["rule"], vi["message"]))
                    if vi.get("detail"):
                        print("           detail: {}".format(vi["detail"]))

        return 0 if r["verdict"] == "PASS" else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
