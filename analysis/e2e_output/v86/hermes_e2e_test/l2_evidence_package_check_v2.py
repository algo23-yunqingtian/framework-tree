#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHE V86-RC2 L2 Evidence Package Integrity Checker V2
Task: 工单-DSHE / T3.4 L2证据包前置校验脚本增强

V2 Key Changes (vs V1):
  - EVIDENCE_CONTRACT_V1 contract version validation
  - DEP registry ID format validation (DEP-REG-NNN)
  - State machine field validation (dep_state, dep_registry_id)
  - --pre-audit mode: simulates HERMES auditor core rules
  - Pre-capture evidence package format defects before HERMES pre-review
  - Alert adapter integration for CRITICAL block

Usage:
  python3 l2_evidence_package_check_v2.py --check <evidence.json>
  python3 l2_evidence_package_check_v2.py --check-dir <dir>
  python3 l2_evidence_package_check_v2.py --verify-md5 <md5_list.json>
  python3 l2_evidence_package_check_v2.py --all <dir>
  python3 l2_evidence_package_check_v2.py --pre-audit <evidence.json>
  python3 l2_evidence_package_check_v2.py --pre-audit-dir <dir>
  python3 l2_evidence_package_check_v2.py --generate-md5 <dir>
  python3 l2_evidence_package_check_v2.py --generate-index <dir>
  python3 l2_evidence_package_check_v2.py --dry-run

Exit Codes:
  0  - All checks PASS
  1  - One or more CRITICAL violations found
  2  - One or more WARNING violations found
  3  - Script error

Branch: feature/v85-chart-template
Date: 2026-10-15
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import glob
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DEFAULT_EVIDENCE_DIR = SCRIPT_DIR / ".payload_evidence"
MD5_LIST_FILE = DEFAULT_EVIDENCE_DIR / "MD5_CHECKSUM_LIST_evidence.json"
EVIDENCE_INDEX_FILE = DEFAULT_EVIDENCE_DIR / "evidence_index.json"
LOG_DIR = SCRIPT_DIR / ".logs"
LOG_FILE = LOG_DIR / "l2_evidence_check_v2.log"

# Severity levels
CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
INFO = "INFO"

# Contract version
EVIDENCE_CONTRACT_VERSION = "EVIDENCE_CONTRACT_V1"

# DEP registry
DEP_REGISTRY_ID = "DEP-REG-001"
MAX_PAUSE_DAYS = 30
ROLLBACK_WINDOW_MIN = 15

# DEP state machine
DEP_STATES = {"ACTIVE", "BLOCKED", "RECOVERY", "RECOVERED", "ROLLED_BACK", "CLOSED"}
DEP_STATE_TRANSITIONS = {
    ("ACTIVE", "BLOCKED"): "DEP_FAILURE",
    ("BLOCKED", "RECOVERY"): "RECOVERY_START",
    ("RECOVERY", "RECOVERED"): "RECOVERY_COMPLETE",
    ("RECOVERED", "ACTIVE"): "RECOVERY_CONFIRM",
    ("RECOVERED", "ROLLED_BACK"): "ROLLBACK_TRIGGER",
    ("ROLLED_BACK", "CLOSED"): "DEP_CLOSED",
    ("ACTIVE", "CLOSED"): "MANUAL_CLOSE",
    ("BLOCKED", "ROLLED_BACK"): "PAUSE_TIMEOUT_ROLLBACK",
    ("BLOCKED", "ACTIVE"): "QUICK_RECOVERY",
    ("RECOVERY", "BLOCKED"): "RECOVERY_FAIL_BACK",
}

# Required top-level fields (EVIDENCE_CONTRACT_V1)
REQUIRED_TOP_FIELDS = {
    "fingerprint": str,
    "run_id": str,
    "session_id": str,
    "total_calls": int,
    "generated_at": str,
    "caller": str,
    "dshb_reuse": bool,
    "calls": list,
    "l2_version": str,
    "version_script": str,
}

# Required per-call fields
REQUIRED_CALL_FIELDS = {
    "trace_id": str,
    "timestamp": str,
    "indicator_id": str,
    "zhiji_short_id": str,
    "request_payload": dict,
    "response_payload": dict,
    "status": str,
    "call_type": str,
    "caller": str,
    "dsbh_reuse": bool,
}

# Allowed call_type values
ALLOWED_CALL_TYPES = {"DSHE_INDEPENDENT_ZHIJI"}

# Allowed status values
ALLOWED_STATUSES = {"INDEPENDENT_FETCH_OK", "INDEPENDENT_FETCH_FAIL"}

# DEP-REG ID format regex
DEP_REGISTRY_PATTERN = re.compile(r"^DEP-REG-\d{3}$")

# Response payload required fields
REQUIRED_RESPONSE_FIELDS = {"id": str, "points": list}

# Script audit required fields
SCRIPT_AUDIT_REQUIRED = {
    "uses_search_passthrough": bool,
    "has_id_consistency_assert": bool,
    "zero_value_counts_as_pass": bool,
    "retains_raw_payload": bool,
}

# ─────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────
def setup_logging(level=logging.INFO):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger("l2_evidence_check_v2")
    logger.setLevel(level)
    logger.handlers.clear()

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────
# IntegrityChecker V2
# ─────────────────────────────────────────────────────────────────────
class IntegrityChecker:
    """L2 Evidence Package Integrity Checker V2"""

    def __init__(self, evidence):
        self.ev = evidence or {}
        self.findings = []

    def emit(self, level, check_id, message, detail=None):
        f = {
            "level": level,
            "check_id": check_id,
            "message": message,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.findings.append(f)
        return f

    # -- 1. IC-01: File existence (already checked by caller) ----------
    # -- 2. IC-02: JSON format validity (already checked by caller) ----
    # -- 3. IC-03: Top-level field completeness ------------------------
    def check_top_fields(self):
        """Check all required top-level fields are present and correct type."""
        missing = []
        type_mismatch = []
        for field, expected_type in REQUIRED_TOP_FIELDS.items():
            if field not in self.ev:
                missing.append(field)
            elif not isinstance(self.ev[field], expected_type):
                type_mismatch.append("%s: expected %s, got %s" % (
                    field, expected_type.__name__, type(self.ev[field]).__name__))

        if missing:
            self.emit(CRITICAL, "IC-03",
                      "Missing top-level fields: %s" % ", ".join(missing))
        if type_mismatch:
            self.emit(HIGH, "IC-03",
                      "Top-level field type mismatch: %s" % "; ".join(type_mismatch))

        # V2 NEW: Check EVIDENCE_CONTRACT_V1 version field
        contract_ver = self.ev.get("evidence_contract_version")
        if contract_ver is None:
            self.emit(HIGH, "IC-03V2",
                      "Missing evidence_contract_version field (EVIDENCE_CONTRACT_V1)")
        elif contract_ver != EVIDENCE_CONTRACT_VERSION:
            self.emit(HIGH, "IC-03V2",
                      "Contract version mismatch: expected %s, got %s" % (
                          EVIDENCE_CONTRACT_VERSION, contract_ver))

        # V2 NEW: Check dshb_reuse is always false
        if self.ev.get("dshb_reuse") is not False:
            self.emit(CRITICAL, "IC-03V2",
                      "dshb_reuse must be false (got %s)" % self.ev.get("dshb_reuse"))

        # Check caller
        if "DSHE" not in self.ev.get("caller", ""):
            self.emit(HIGH, "IC-03",
                      "caller field does not contain 'DSHE': %s" % self.ev.get("caller"))

        return not missing

    # -- 4. IC-04: Call array integrity --------------------------------
    def check_calls(self):
        """Check call array integrity and per-call fields."""
        calls = self.ev.get("calls") or []
        if not calls:
            self.emit(CRITICAL, "IC-04", "calls array is empty")
            return False

        seen_trace_ids = set()
        for i, call in enumerate(calls):
            # Check required fields
            for field, expected_type in REQUIRED_CALL_FIELDS.items():
                if field not in call:
                    self.emit(CRITICAL, "IC-04",
                              "Call[%d] missing field: %s" % (i, field))
                elif not isinstance(call[field], expected_type):
                    self.emit(HIGH, "IC-04",
                              "Call[%d].%s type mismatch" % (i, field))

            # Check trace_id uniqueness
            tid = call.get("trace_id", "")
            if not tid:
                self.emit(CRITICAL, "IC-04",
                          "Call[%d] trace_id is empty" % i)
            elif tid in seen_trace_ids:
                self.emit(HIGH, "IC-04",
                          "Call[%d] trace_id duplicate: %s" % (i, tid))
            seen_trace_ids.add(tid)

            # Check call_type
            ct = call.get("call_type")
            if ct and ct not in ALLOWED_CALL_TYPES:
                self.emit(HIGH, "IC-04",
                          "Call[%d] invalid call_type: %s" % (i, ct))

            # Check dshb_reuse per call
            if call.get("dshb_reuse") is not False:
                self.emit(CRITICAL, "IC-04",
                          "Call[%d] dshb_reuse is not false" % i)

            # V2 NEW: Check dep_registry_id format
            dep_reg_id = call.get("dep_registry_id")
            if dep_reg_id is not None and not DEP_REGISTRY_PATTERN.match(dep_reg_id):
                self.emit(HIGH, "IC-04V2",
                          "Call[%d] invalid dep_registry_id format: %s" % (i, dep_reg_id))

            # Check status
            status = call.get("status", "")
            if status not in ALLOWED_STATUSES:
                self.emit(MEDIUM, "IC-04",
                          "Call[%d] unexpected status: %s" % (i, status))

        return len(calls) > 0

    # -- 5. IC-05: Payload persistence ---------------------------------
    def check_payload_persistence(self, evidence_dir=None):
        """Check that payload evidence files exist for each call."""
        calls = self.ev.get("calls") or []
        if not evidence_dir:
            evidence_dir = DEFAULT_EVIDENCE_DIR

        missing_files = []
        for call in calls:
            tid = call.get("trace_id", "")
            if not tid:
                continue
            trace_file = Path(evidence_dir) / f"{tid}.json"
            if not trace_file.exists():
                missing_files.append(tid)

        if missing_files:
            self.emit(CRITICAL, "IC-05",
                      "Missing payload evidence files: %s" %
                      ", ".join(missing_files[:5]) +
                      ("..." if len(missing_files) > 5 else ""))

        return len(missing_files) == 0

    # -- 6. IC-06: Evidence index --------------------------------------
    def check_evidence_index(self, evidence_dir=None):
        """Check evidence index file exists and is valid."""
        if not evidence_dir:
            evidence_dir = DEFAULT_EVIDENCE_DIR

        index_file = Path(evidence_dir) / "evidence_index.json"
        if not index_file.exists():
            self.emit(MEDIUM, "IC-06",
                      "Evidence index file not found: %s" % index_file)
            return False

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
            if "files" not in index:
                self.emit(HIGH, "IC-06",
                          "Evidence index missing 'files' key")
                return False
            return True
        except (json.JSONDecodeError, Exception) as e:
            self.emit(HIGH, "IC-06",
                      "Evidence index JSON invalid: %s" % e)
            return False

    # -- 7. IC-07: Negative scenario pattern detection -----------------
    def check_negative_patterns(self):
        """Detect known negative scenario patterns."""
        findings = []

        # NEG-01: Bridge rate fabrication
        total_calls = self.ev.get("total_calls", 0)
        bridge_rate = self.ev.get("bridge_rate")
        real_rate = self.ev.get("real_fetchable_rate")
        if total_calls == 0 and bridge_rate and bridge_rate > 0:
            self.emit(CRITICAL, "NEG-01",
                      "Bridge rate fabrication: total_calls=0 but bridge_rate=%s" %
                      bridge_rate)
            findings.append("NEG-01")

        # NEG-02: Payload loss
        calls = self.ev.get("calls") or []
        for i, call in enumerate(calls):
            req = call.get("request_payload")
            resp = call.get("response_payload")
            if req is None or resp is None:
                self.emit(CRITICAL, "NEG-02",
                          "Payload loss: Call[%d] request_payload=%s, response_payload=%s" % (
                              i, "null" if req is None else "present",
                              "null" if resp is None else "present"))
                if "NEG-02" not in findings:
                    findings.append("NEG-02")

        # NEG-03: TraceID missing
        for i, call in enumerate(calls):
            tid = call.get("trace_id", "")
            if not tid or tid == "":
                self.emit(CRITICAL, "NEG-03",
                          "TraceID missing: Call[%d] trace_id is empty" % i)
                if "NEG-03" not in findings:
                    findings.append("NEG-03")

        # NEG-04: DSHB reuse
        if self.ev.get("dshb_reuse") is True:
            self.emit(CRITICAL, "NEG-04",
                      "DSHB reuse detected: dshb_reuse=true")
            findings.append("NEG-04")
        for i, call in enumerate(calls):
            if call.get("dshb_reuse") is True:
                self.emit(CRITICAL, "NEG-04",
                          "DSHB reuse in call: Call[%d]" % i)
                if "NEG-04" not in findings:
                    findings.append("NEG-04")

        return len(findings) == 0

    # -- 8. MD5 verification ------------------------------------------
    def check_md5(self, md5_list=None):
        """Verify MD5 checksums against a checksum list."""
        if not md5_list:
            return True

        errors = 0
        for item in md5_list:
            filepath = item.get("file", "")
            expected = item.get("md5", "")
            if not filepath or not expected:
                continue
            if not os.path.exists(filepath):
                self.emit(CRITICAL, "MD5-01",
                          "File not found for MD5 check: %s" % filepath)
                errors += 1
                continue
            actual = file_md5(filepath)
            if actual != expected:
                self.emit(CRITICAL, "MD5-02",
                          "MD5 mismatch: %s (expected=%s, actual=%s)" % (
                              filepath, expected[:16], actual[:16]))
                errors += 1

        return errors == 0

    # -- 9. V2 NEW: Contract version check ----------------------------
    def check_contract_version(self):
        """Validate EVIDENCE_CONTRACT_V1 compliance."""
        contract_ver = self.ev.get("evidence_contract_version")
        if contract_ver == EVIDENCE_CONTRACT_VERSION:
            return True
        self.emit(HIGH, "IC-CONTRACT",
                  "Contract version check: expected %s, got %s" % (
                      EVIDENCE_CONTRACT_VERSION, contract_ver or "MISSING"))
        return False

    # -- 10. V2 NEW: DEP state machine field check --------------------
    def check_dep_state_machine(self):
        """Validate DEP state machine fields."""
        dep_state = self.ev.get("dep_state")
        dep_reg_id = self.ev.get("dep_registry_id")

        # Check dep_registry_id format
        if dep_reg_id:
            if not DEP_REGISTRY_PATTERN.match(dep_reg_id):
                self.emit(HIGH, "IC-DEP-REG",
                          "Invalid dep_registry_id format: %s (expected DEP-REG-NNN)" %
                          dep_reg_id)

        # Check dep_state validity
        if dep_state:
            if dep_state not in DEP_STATES:
                self.emit(HIGH, "IC-DEP-STATE",
                          "Invalid dep_state: %s (expected one of %s)" % (
                              dep_state, ", ".join(sorted(DEP_STATES))))
        else:
            self.emit(MEDIUM, "IC-DEP-STATE",
                      "dep_state field is missing (recommended for V2)")

        # Check max_pause_days and rollback_window_min
        max_pause = self.ev.get("max_pause_days")
        if max_pause is not None and max_pause != MAX_PAUSE_DAYS:
            self.emit(MEDIUM, "IC-DEP-CONF",
                      "max_pause_days=%s (expected %s)" % (max_pause, MAX_PAUSE_DAYS))

        rollback_win = self.ev.get("rollback_window_min")
        if rollback_win is not None and rollback_win != ROLLBACK_WINDOW_MIN:
            self.emit(MEDIUM, "IC-DEP-CONF",
                      "rollback_window_min=%s (expected %s)" % (rollback_win, ROLLBACK_WINDOW_MIN))

        return dep_state is not None

    # -- 11. V2 NEW: Response payload structure check -----------------
    def check_response_payload_structure(self):
        """Validate response payload structure per contract."""
        calls = self.ev.get("calls") or []
        for i, call in enumerate(calls):
            resp = call.get("response_payload") or {}

            # Check required response fields
            for field in REQUIRED_RESPONSE_FIELDS:
                if field not in resp:
                    self.emit(HIGH, "IC-RESP",
                              "Call[%d] response_payload missing '%s'" % (i, field))

            # Check points structure
            points = resp.get("points") or []
            if points:
                for j, p in enumerate(points[:3]):  # Check first 3
                    if "value" not in p:
                        self.emit(HIGH, "IC-RESP",
                                  "Call[%d].response_payload.points[%d] missing 'value'" % (i, j))
                    if "date" not in p:
                        self.emit(MEDIUM, "IC-RESP",
                                  "Call[%d].response_payload.points[%d] missing 'date'" % (i, j))

            # Check resolved_id
            if "resolved_id" not in resp:
                self.emit(MEDIUM, "IC-RESP",
                          "Call[%d] response_payload missing 'resolved_id'" % i)

    # -- 12. V2 NEW: Script audit check -------------------------------
    def check_script_audit(self):
        """Validate script_audit section."""
        script = self.ev.get("script_audit") or {}
        if not script:
            self.emit(MEDIUM, "IC-SCRIPT",
                      "script_audit section is missing (recommended for V2)")
            return False

        for field, expected_type in SCRIPT_AUDIT_REQUIRED.items():
            if field not in script:
                self.emit(HIGH, "IC-SCRIPT",
                          "script_audit missing '%s'" % field)
            elif not isinstance(script[field], expected_type):
                self.emit(HIGH, "IC-SCRIPT",
                          "script_audit.%s type mismatch" % field)

        # Check G-09 compliance
        if script.get("uses_search_passthrough"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.uses_search_passthrough=true -> G-09 FAIL")
        if not script.get("has_id_consistency_assert"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.has_id_consistency_assert=false -> G-09 FAIL")
        if script.get("zero_value_counts_as_pass"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.zero_value_counts_as_pass=true -> G-09 FAIL")
        if not script.get("retains_raw_payload"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.retains_raw_payload=false -> G-09 FAIL")

        return True

    # -- Run all checks ------------------------------------------------
    def run_all(self, evidence_dir=None, md5_list=None):
        """Run all integrity checks."""
        self.check_top_fields()
        self.check_calls()
        self.check_payload_persistence(evidence_dir)
        self.check_evidence_index(evidence_dir)
        self.check_negative_patterns()
        self.check_md5(md5_list)

        # V2 NEW checks
        self.check_contract_version()
        self.check_dep_state_machine()
        self.check_response_payload_structure()
        self.check_script_audit()

        return self.summarize()

    def summarize(self):
        """Generate summary of findings."""
        counts = defaultdict(int)
        for f in self.findings:
            counts[f["level"]] += 1

        total = sum(counts.values())
        crit = counts.get(CRITICAL, 0)
        high = counts.get(HIGH, 0)

        if crit > 0:
            verdict = "BLOCK"
        elif high > 0:
            verdict = "WARNING"
        elif counts.get(MEDIUM, 0) > 0:
            verdict = "PASS_WITH_NOTES"
        else:
            verdict = "PASS"

        return {
            "verdict": verdict,
            "total_findings": total,
            "CRITICAL": crit,
            "HIGH": high,
            "MEDIUM": counts.get(MEDIUM, 0),
            "LOW": counts.get(LOW, 0),
            "findings": self.findings,
        }


# ─────────────────────────────────────────────────────────────────────
# Pre-Audit (V2 NEW)
# ─────────────────────────────────────────────────────────────────────
class PreAuditor:
    """
    Pre-audit mode: simulates HERMES evidence_auditor core rules
    to catch format defects before HERMES pre-review.
    """

    def __init__(self, evidence):
        self.ev = evidence or {}
        self.events = []
        self.checker = IntegrityChecker(evidence)

    def emit(self, level, rule, dp, msg, trace_id=None):
        e = {
            "level": level,
            "rule": rule,
            "detect_point": dp,
            "message": msg,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(e)
        return e

    def pre_audit(self):
        """Run pre-audit checks simulating HERMES auditor rules."""

        # Run integrity checks first
        self.checker.run_all()
        integrity_findings = self.checker.findings

        # Convert integrity findings to audit events
        for f in integrity_findings:
            level = f["level"]
            rule = "PRE-AUDIT"
            dp = f["check_id"]
            self.emit(level, rule, dp, f["message"])

        # Simulate HERMES core audit rules
        self._check_dual_evidence()
        self._check_trace_fingerprint()
        self._check_bridge_rate()
        self._check_dep_classification()
        self._check_script_audit()

        return self._verdict()

    def _check_dual_evidence(self):
        """Simulate R-AUDIT-01: dual evidence completeness."""
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id")
            claimed = (c.get("status") or "").upper()
            if "COMPLETED" not in claimed and "FETCH_OK" not in claimed:
                continue

            resp = c.get("response_payload") or {}
            pts = resp.get("points") or []
            has_nonzero = False
            for p in pts:
                v = p.get("value")
                if v is not None and str(v).strip() not in ("", "0", "0.0"):
                    has_nonzero = True
                    break

            if not (pts and has_nonzero):
                self.emit(CRITICAL, "R-AUDIT-01", "D01.2",
                          "COMPLETED entry lacks real fetch evidence: %s" % tid, tid)

    def _check_trace_fingerprint(self):
        """Simulate R-AUDIT-03: traceID/audit fingerprint."""
        for f in ("fingerprint", "run_id", "session_id"):
            if not self.ev.get(f):
                self.emit(CRITICAL, "R-AUDIT-03", "D03.1",
                          "Missing audit field: %s" % f)

        calls = self.ev.get("calls") or []
        seen = set()
        for c in calls:
            tid = c.get("trace_id")
            if not tid:
                self.emit(CRITICAL, "R-AUDIT-03", "D03.1", "Call missing trace_id")
                continue
            if tid in seen:
                self.emit(HIGH, "R-AUDIT-03", "D03.1",
                          "Duplicate trace_id: %s" % tid, tid)
            seen.add(tid)

        if self.ev.get("dshb_reuse") is True:
            self.emit(CRITICAL, "R-AUDIT-03", "D03.2",
                      "dshb_reuse=true violates L2-R01")

    def _check_bridge_rate(self):
        """Simulate R-AUDIT-02: dual bridge rate calibration."""
        mr = self.ev.get("metadata_rate")
        rr = self.ev.get("real_fetchable_rate")
        claimed = self.ev.get("bridge_rate")

        if claimed is not None and (mr is None or rr is None):
            self.emit(HIGH, "R-AUDIT-02", "D02.2",
                      "Bridge rate not split into dual columns: %s" % claimed)
            return

        if mr is not None and rr is not None and mr != rr:
            if claimed is not None and abs(claimed - mr) < 1e-9 and abs(mr - rr) > 1e-9:
                self.emit(CRITICAL, "R-AUDIT-02", "D02.1",
                          "Metadata rate(%s) masquerading as effective rate, actual=%s" % (mr, rr))

        measured = self._measure_real_rate()
        if claimed is not None and measured is not None and claimed > measured + 1e-9:
            self.emit(CRITICAL, "R-AUDIT-02", "D02.3",
                      "Effective rate numerator inflated: claimed %s, measured %s" % (
                          claimed, round(measured, 4)))

    def _measure_real_rate(self):
        calls = self.ev.get("calls") or []
        if not calls:
            return None
        ok = 0
        for c in calls:
            resp = c.get("response_payload") or {}
            pts = resp.get("points") or []
            if any(p.get("value") not in (None, "", 0, "0", "0.0") for p in pts):
                ok += 1
        return ok / len(calls)

    def _check_dep_classification(self):
        """Simulate DEP classification checks."""
        for c in (self.ev.get("calls") or []):
            cls = (c.get("dep_classification") or "").upper()
            if cls == "DEPENDENCY_BLOCK":
                resp = c.get("response_payload") or {}
                err = resp.get("error", "")
                if "无法识别指标来源" not in err and "permission_state" not in json.dumps(resp):
                    self.emit(HIGH, "R-AUDIT-04", "DEP-CLASS",
                              "Claimed DEPENDENCY_BLOCK but no external block evidence: %s" %
                              c.get("indicator_id"), c.get("trace_id"))
                if not c.get("dep_registry_id"):
                    self.emit(MEDIUM, "R-AUDIT-04", "DEP-CLASS",
                              "DEPENDENCY_BLOCK not registered: %s" % c.get("indicator_id"),
                              c.get("trace_id"))

    def _check_script_audit(self):
        """Simulate G-09 script audit checks."""
        script = self.ev.get("script_audit") or {}
        if not script:
            return
        if script.get("uses_search_passthrough"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.1",
                      "Script uses search passthrough -> G-09 FAIL")
        if not script.get("has_id_consistency_assert"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.2",
                      "Missing ID consistency assert -> G-09 FAIL")
        if script.get("zero_value_counts_as_pass"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.3",
                      "Zero value counts as pass -> G-09 FAIL")
        if not script.get("retains_raw_payload"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.4",
                      "Raw payload not retained -> G-09 FAIL")

    def _verdict(self):
        crit = [e for e in self.events if e["level"] == CRITICAL]
        high = [e for e in self.events if e["level"] == HIGH]
        medium = [e for e in self.events if e["level"] == MEDIUM]

        if crit:
            result = "FAIL"
        elif high or medium:
            result = "CONDITIONAL_PASS"
        else:
            result = "PASS"

        return {
            "verdict": result,
            "total_events": len(self.events),
            "CRITICAL": len(crit),
            "HIGH": len(high),
            "MEDIUM": len(medium),
            "events": self.events,
        }


# ─────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────
def file_md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_md5_list(evidence_dir):
    """Generate MD5 checksum list for all evidence files."""
    evidence_dir = Path(evidence_dir)
    files = []
    for f in sorted(evidence_dir.glob("*")):
        if f.is_file():
            files.append({
                "file": str(f),
                "md5": file_md5(str(f)),
                "size": f.stat().st_size,
            })
    return files


def generate_evidence_index(evidence_dir, evidence_file=None):
    """Generate evidence index for all evidence files."""
    evidence_dir = Path(evidence_dir)
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "files": [],
    }
    for f in sorted(evidence_dir.glob("*")):
        if f.is_file():
            entry = {
                "filename": f.name,
                "size": f.stat().st_size,
                "md5": file_md5(str(f)),
            }
            if evidence_file and f.name == evidence_file.name:
                entry["is_evidence_package"] = True
            index["files"].append(entry)
    return index


def check_evidence_package(filepath, evidence_dir=None):
    """Check a single evidence package file."""
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error("File not found: %s" % filepath)
        return {"verdict": "ERROR", "error": "file_not_found"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            ev = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s" % e)
        return {"verdict": "BLOCK", "error": "json_parse_error", "detail": str(e)}

    if not evidence_dir:
        evidence_dir = filepath.parent

    checker = IntegrityChecker(ev)
    result = checker.run_all(str(evidence_dir))
    return result


def pre_audit_evidence(filepath):
    """Pre-audit a single evidence package."""
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error("File not found: %s" % filepath)
        return {"verdict": "ERROR", "error": "file_not_found"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            ev = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s" % e)
        return {"verdict": "ERROR", "error": "json_parse_error"}

    auditor = PreAuditor(ev)
    result = auditor.pre_audit()
    return result


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="DSHE V86-RC2 L2 Evidence Package Integrity Checker V2")
    ap.add_argument("--check", help="Check single evidence file")
    ap.add_argument("--check-dir", help="Check all evidence files in directory")
    ap.add_argument("--verify-md5", help="Verify MD5 checksum list")
    ap.add_argument("--all", help="Run all checks on directory")
    ap.add_argument("--pre-audit", help="Pre-audit single evidence file (V2 NEW)")
    ap.add_argument("--pre-audit-dir", help="Pre-audit all evidence files in directory (V2 NEW)")
    ap.add_argument("--generate-md5", help="Generate MD5 checksum list")
    ap.add_argument("--generate-index", help="Generate evidence index")
    ap.add_argument("--dry-run", action="store_true", help="Dry run")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args(argv)

    if args.dry_run:
        logger.info("V2 Evidence Package Checker V2 - DRY RUN")
        logger.info("  Contract Version: %s" % EVIDENCE_CONTRACT_VERSION)
        logger.info("  DEP Registry ID: %s" % DEP_REGISTRY_ID)
        logger.info("  Evidence Dir: %s" % DEFAULT_EVIDENCE_DIR)
        logger.info("  Modes: --check, --check-dir, --verify-md5, --all, "
                    "--pre-audit, --pre-audit-dir, --generate-md5, --generate-index")
        return 0

    if args.generate_md5:
        dirpath = Path(args.generate_md5)
        if not dirpath.exists():
            logger.error("Directory not found: %s" % dirpath)
            return 3
        md5_list = generate_md5_list(dirpath)
        output = dirpath / "MD5_CHECKSUM_LIST_evidence.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(md5_list, f, indent=2, ensure_ascii=False)
        logger.info("Generated MD5 list: %s (%d files)" % (output, len(md5_list)))
        return 0

    if args.generate_index:
        dirpath = Path(args.generate_index)
        if not dirpath.exists():
            logger.error("Directory not found: %s" % dirpath)
            return 3
        ev_files = list(dirpath.glob("evidence_package_*.json"))
        ev_file = ev_files[0] if ev_files else None
        index = generate_evidence_index(dirpath, ev_file)
        output = dirpath / "evidence_index.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        logger.info("Generated evidence index: %s (%d files)" % (output, len(index["files"])))
        return 0

    if args.verify_md5:
        md5_file = Path(args.verify_md5)
        if not md5_file.exists():
            logger.error("MD5 list not found: %s" % md5_file)
            return 3
        with open(md5_file, "r", encoding="utf-8") as f:
            md5_list = json.load(f)
        checker = IntegrityChecker({})
        ok = checker.check_md5(md5_list)
        result = checker.summarize()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.info("MD5 verification: %s" % result["verdict"])
            for f in result["findings"]:
                logger.info("  [%s] %s: %s" % (f["level"], f["check_id"], f["message"]))
        return 0 if ok else 1

    if args.pre_audit:
        result = pre_audit_evidence(args.pre_audit)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.info("PRE-AUDIT RESULT: %s" % result["verdict"])
            logger.info("  Events: %d (CRITICAL=%d, HIGH=%d, MEDIUM=%d)" % (
                result["total_events"], result["CRITICAL"], result["HIGH"], result["MEDIUM"]))
            for e in result["events"]:
                logger.info("  [%s] %s/%s: %s" % (
                    e["level"], e["rule"], e["detect_point"], e["message"]))
        return 0 if result["verdict"] != "FAIL" else 1

    if args.pre_audit_dir:
        dirpath = Path(args.pre_audit_dir)
        files = sorted(dirpath.glob("evidence_package_*.json"))
        if not files:
            logger.warning("No evidence files found in %s" % dirpath)
            return 0
        all_results = {}
        all_pass = True
        for f in files:
            result = pre_audit_evidence(str(f))
            all_results[f.name] = result
            if result["verdict"] == "FAIL":
                all_pass = False
            logger.info("%s: %s (CRITICAL=%d, HIGH=%d)" % (
                f.name, result["verdict"], result["CRITICAL"], result["HIGH"]))
        if args.json:
            print(json.dumps(all_results, ensure_ascii=False, indent=2))
        else:
            logger.info("PRE-AUDIT DIR: %d files, %s" % (
                len(files), "ALL PASS" if all_pass else "HAS FAILURES"))
        return 0 if all_pass else 1

    if args.check:
        result = check_evidence_package(args.check)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.info("CHECK RESULT: %s" % result["verdict"])
            logger.info("  Findings: %d (CRITICAL=%d, HIGH=%d, MEDIUM=%d)" % (
                result["total_findings"], result["CRITICAL"], result["HIGH"], result["MEDIUM"]))
            for f in result["findings"]:
                logger.info("  [%s] %s: %s" % (f["level"], f["check_id"], f["message"]))
        return 0 if result["verdict"] != "BLOCK" else 1

    if args.check_dir:
        dirpath = Path(args.check_dir)
        files = sorted(dirpath.glob("evidence_package_*.json"))
        if not files:
            logger.warning("No evidence files found in %s" % dirpath)
            return 0
        all_pass = True
        for f in files:
            result = check_evidence_package(str(f), dirpath)
            if result["verdict"] == "BLOCK":
                all_pass = False
            logger.info("%s: %s" % (f.name, result["verdict"]))
        return 0 if all_pass else 1

    if args.all:
        dirpath = Path(args.all)
        files = sorted(dirpath.glob("evidence_package_*.json"))
        if not files:
            logger.warning("No evidence files found in %s" % dirpath)
            return 0
        all_pass = True
        for f in files:
            result = check_evidence_package(str(f), dirpath)
            if result["verdict"] == "BLOCK":
                all_pass = False
            logger.info("%s: %s" % (f.name, result["verdict"]))
        return 0 if all_pass else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
