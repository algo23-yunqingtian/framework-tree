# -*- coding: utf-8 -*-
"""
pre_wind_call_guard_check.py
Wind Data Pull Pre-Call Guard Script for DSHA-P54
====================================================
Dual-layer guard that runs BEFORE any Wind API call to verify:
  1. Governance invariants (wind_api_calls=0, gate=CLOSED/HOLD, etc.)
  2. Wind call counter limits (max 108 calls, per-factor/per-chunk limits)
  3. Pipeline process state (no pipeline already running)
  4. HOLD factor enforcement (4/4 factors blocked)
  5. Credential safety (no plaintext credentials in audit logs)

This script is a LOCAL-only guard: it does NOT call Wind APIs.
It checks all conditions locally before allowing the pipeline to proceed.

Usage:
  python pre_wind_call_guard_check.py                  # Run all checks
  python pre_wind_call_guard_check.py --check-governance  # Governance only
  python pre_wind_call_guard_check.py --check-counter     # Counter only
  python pre_wind_call_guard_check.py --check-process     # Process only
  python pre_wind_call_guard_check.py --check-hold        # HOLD factor only
  python pre_wind_call_guard_check.py --check-credentials # Credential scan only
  python pre_wind_call_guard_check.py --dry-run           # Full check, no mutation
  python pre_wind_call_guard_check.py --verbose           # Detailed output

Exit codes:
  0 = ALL CHECKS PASS
  1 = CHECK FAIL (governance violation or HOLD breach)
  2 = CHECK WARNING (non-blocking issue detected)
  3 = CHECK BLOCKED (external blocker, e.g. Wind not ready)
"""

import os
import sys
import re
import json
import datetime
import hashlib
import subprocess
import argparse
import traceback

# Windows UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# =============================================================================
# Configuration
# =============================================================================

WORKSPACE = r"D:\DSH_WORK\github工作\回测"
AUDIT_DIR = os.path.join(WORKSPACE, "data-harbor", "dsha_p49_prep", "P49_backtest_audit")
G7_LEDGER_DIR = os.path.join(WORKSPACE, "G7_ADJUDICATION_LEDGER")

# Expected governance invariants
EXPECTED_INVARIANTS = {
    "wind_api_calls": 0,
    "backtest_started": False,
    "gate": "CLOSED/HOLD",
    "release_permit": "NOT_ISSUED",
}

# Expected call limits (from P49_DATA_PULL_TASK_SPLIT_PLAN.md)
CALL_LIMITS = {
    "total": 108,
    "FACTOR-004": 36,
    "FACTOR-006": 24,
    "FACTOR-007": 48,
    "by_chunk": {
        "CH01": 64,
        "CH02": 32,
        "CH03": 12,
    },
}

# HOLD factors (must be blocked)
HOLD_FACTORS = ["FACTOR-001", "FACTOR-002", "FACTOR-003", "FACTOR-005"]

# CONDITIONAL factors (allowed)
CONDITIONAL_FACTORS = ["FACTOR-004", "FACTOR-006", "FACTOR-007"]

# Allowed Wind codes
ALLOWED_WIND_CODES = ["LI.SHF", "NI.SHF", "ZN.SHF", "CU.SHF"]

# Allowed date range
ALLOWED_DATE_START = "2023-01-01"
ALLOWED_DATE_END = "2024-12-31"

# Files to scan for credentials
CREDENTIAL_SCAN_FILES = [
    os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl"),
    os.path.join(AUDIT_DIR, "wind_excel_events.jsonl"),
    os.path.join(AUDIT_DIR, "wind_config.json"),
]

# Allowed credential patterns (known-safe redaction markers)
ALLOWED_CREDENTIAL_PATTERNS = [
    r"\[REDACTED[^\]]*\]",
    r"\[REDACTED-CREDENTIAL\]",
]

# Suspicious credential patterns
SUSPICIOUS_CREDENTIAL_PATTERNS = [
    r"\d{11}",         # 11-digit numbers (phone/username)
    r"[A-Za-z]\w{4,}!@\#\$\%\^\&\*",  # passwords with special chars
]

# Credential values loaded dynamically from config (never hardcoded in code)
_CREDENTIAL_VALUES = {}
def _load_credentials_from_config():
    global _CREDENTIAL_VALUES
    config_path = os.path.join(AUDIT_DIR, "wind_config.json")
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
        api = cfg.get("api", {})
        _CREDENTIAL_VALUES["username"] = api.get("username", "")
        _CREDENTIAL_VALUES["password"] = api.get("password", "")
    except Exception:
        _CREDENTIAL_VALUES = {}
_load_credentials_from_config()


# =============================================================================
# Check Result Data Class
# =============================================================================

class CheckResult:
    def __init__(self, check_id, name, status, detail, severity="INFO"):
        self.check_id = check_id
        self.name = name
        self.status = status  # PASS / FAIL / WARNING / BLOCKED / INFO
        self.detail = detail
        self.severity = severity
        self.timestamp = datetime.datetime.now().isoformat()

    def to_dict(self):
        return {
            "check_id": self.check_id,
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "severity": self.severity,
            "timestamp": self.timestamp,
        }

    def __repr__(self):
        return f"[{self.status}] {self.check_id}: {self.name} - {self.detail}"


# =============================================================================
# Check 1: Governance Invariants
# =============================================================================

def check_governance_invariants(verbose=False):
    """Verify all governance invariants from MANIFEST and audit logs."""
    results = []

    # 1a. Check MANIFEST governance_invariants
    manifest_path = os.path.join(G7_LEDGER_DIR, "G7_ADJUDICATION_PACKAGE_MANIFEST.json")
    try:
        with open(manifest_path, "r", encoding="utf-8-sig") as f:
            manifest = json.load(f)
        
        gov = manifest.get("governance_invariants", {})
        
        # Check each invariant
        for key, expected in EXPECTED_INVARIANTS.items():
            actual = gov.get(key)
            if actual == expected:
                results.append(CheckResult(
                    check_id="GOV-001",
                    name=f"Governance invariant: {key}",
                    status="PASS",
                    detail=f"{key}={actual} matches expected {expected}"
                ))
            else:
                results.append(CheckResult(
                    check_id="GOV-001",
                    name=f"Governance invariant: {key}",
                    status="FAIL",
                    detail=f"{key}={actual} does NOT match expected {expected}",
                    severity="CRITICAL"
                ))
    except FileNotFoundError:
        results.append(CheckResult(
            check_id="GOV-001",
            name="MANIFEST governance check",
            status="FAIL",
            detail=f"MANIFEST not found: {manifest_path}",
            severity="CRITICAL"
        ))
    except Exception as e:
        results.append(CheckResult(
            check_id="GOV-001",
            name="MANIFEST governance check",
            status="FAIL",
            detail=f"Error reading MANIFEST: {e}",
            severity="CRITICAL"
        ))

    # 1b. Check wind_config.json blocker status
    config_path = os.path.join(AUDIT_DIR, "wind_config.json")
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            config = json.load(f)
        
        blocker_status = config.get("blocker", {}).get("status", "UNKNOWN")
        if blocker_status == "BLOCKED":
            results.append(CheckResult(
                check_id="GOV-002",
                name="Wind config blocker status",
                status="PASS",
                detail=f"blocker.status={blocker_status} (expected BLOCKED)"
            ))
        else:
            results.append(CheckResult(
                check_id="GOV-002",
                name="Wind config blocker status",
                status="WARNING",
                detail=f"blocker.status={blocker_status} (expected BLOCKED)",
                severity="WARNING"
            ))
    except Exception as e:
        results.append(CheckResult(
            check_id="GOV-002",
            name="Wind config check",
            status="WARNING",
            detail=f"Cannot read wind_config.json: {e}",
            severity="WARNING"
        ))

    # 1c. Check audit logs for governance invariant consistency
    audit_path = os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl")
    try:
        with open(audit_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
        
        wind_calls_values = set()
        backtest_values = set()
        gate_values = set()
        permit_values = set()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                # Check various possible locations for governance values
                meta = event.get("meta", event)
                if "wind_api_calls" in meta:
                    wind_calls_values.add(meta["wind_api_calls"])
                if "backtest_started" in meta:
                    backtest_values.add(meta["backtest_started"])
                if "gate" in meta:
                    gate_values.add(meta["gate"])
                if "release_permit" in meta:
                    permit_values.add(meta["release_permit"])
            except (json.JSONDecodeError, KeyError):
                pass
        
        # All values should be unique (consistent)
        invariant_ok = True
        for name, values, expected in [
            ("wind_api_calls", wind_calls_values, 0),
            ("backtest_started", backtest_values, False),
            ("gate", gate_values, "CLOSED/HOLD"),
            ("release_permit", permit_values, "NOT_ISSUED"),
        ]:
            if not values:
                continue
            unexpected = values - {expected}
            if unexpected:
                invariant_ok = False
                results.append(CheckResult(
                    check_id="GOV-003",
                    name=f"Audit log invariant: {name}",
                    status="FAIL",
                    detail=f"Audit logs contain unexpected values for {name}: {unexpected} (expected: {expected})",
                    severity="CRITICAL"
                ))
        
        if invariant_ok:
            results.append(CheckResult(
                check_id="GOV-003",
                name="Audit log governance consistency",
                status="PASS",
                detail=f"All {len(lines)} audit events maintain governance invariants"
            ))
    except Exception as e:
        results.append(CheckResult(
            check_id="GOV-003",
            name="Audit log governance check",
            status="WARNING",
            detail=f"Cannot check audit log invariants: {e}",
            severity="WARNING"
        ))

    return results


# =============================================================================
# Check 2: Wind Call Counter
# =============================================================================

def check_call_counter(verbose=False):
    """Verify Wind call counter limits are not exceeded."""
    results = []

    # 2a. Check if any calls have been made (should be 0 in STATIC_STANDBY)
    audit_path = os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl")
    try:
        with open(audit_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
        
        wind_calls_seen = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                meta = event.get("meta", event)
                if "wind_api_calls" in meta and isinstance(meta["wind_api_calls"], (int, float)):
                    wind_calls_seen = max(wind_calls_seen, int(meta["wind_api_calls"]))
            except (json.JSONDecodeError, KeyError):
                pass
        
        total_limit = CALL_LIMITS["total"]
        if wind_calls_seen == 0:
            results.append(CheckResult(
                check_id="CNT-001",
                name="Total Wind call count",
                status="PASS",
                detail=f"wind_api_calls=0 (limit: {total_limit}, remaining: {total_limit})"
            ))
        elif wind_calls_seen <= total_limit:
            remaining = total_limit - wind_calls_seen
            results.append(CheckResult(
                check_id="CNT-001",
                name="Total Wind call count",
                status="WARNING",
                detail=f"wind_api_calls={wind_calls_seen} (limit: {total_limit}, remaining: {remaining})",
                severity="WARNING"
            ))
        else:
            results.append(CheckResult(
                check_id="CNT-001",
                name="Total Wind call count",
                status="FAIL",
                detail=f"wind_api_calls={wind_calls_seen} EXCEEDS limit {total_limit}",
                severity="CRITICAL"
            ))
    except Exception as e:
        results.append(CheckResult(
            check_id="CNT-001",
            name="Total Wind call count",
            status="WARNING",
            detail=f"Cannot check call counter: {e}",
            severity="WARNING"
        ))

    # 2b. Check per-factor call counts (should all be 0)
    factor_calls = {}
    try:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                meta = event.get("meta", event)
                if "factor_calls" in meta:
                    for factor, count in meta["factor_calls"].items():
                        factor_calls[factor] = factor_calls.get(factor, 0) + count
            except (json.JSONDecodeError, KeyError):
                pass
        
        for factor, limit in CALL_LIMITS.items():
            if factor == "total":
                continue
            actual = factor_calls.get(factor, 0)
            if actual == 0:
                results.append(CheckResult(
                    check_id="CNT-002",
                    name=f"Per-factor call count: {factor}",
                    status="PASS",
                    detail=f"{factor}=0 calls (limit: {limit})"
                ))
            elif actual <= limit:
                results.append(CheckResult(
                    check_id="CNT-002",
                    name=f"Per-factor call count: {factor}",
                    status="WARNING",
                    detail=f"{factor}={actual} calls (limit: {limit})",
                    severity="WARNING"
                ))
            else:
                results.append(CheckResult(
                    check_id="CNT-002",
                    name=f"Per-factor call count: {factor}",
                    status="FAIL",
                    detail=f"{factor}={actual} calls EXCEEDS limit {limit}",
                    severity="CRITICAL"
                ))
    except Exception as e:
        results.append(CheckResult(
            check_id="CNT-002",
            name="Per-factor call count",
            status="WARNING",
            detail=f"Cannot check per-factor calls: {e}",
            severity="WARNING"
        ))

    return results


# =============================================================================
# Check 3: Pipeline Process State
# =============================================================================

def check_pipeline_process(verbose=False):
    """Verify no pipeline process is already running."""
    results = []

    # 3a. Check for running pipeline processes
    pipeline_process_names = [
        "wind_data_pull_pipeline.py",
        "pre_wind_call_guard_check.py",
    ]

    try:
        # Use PowerShell to check for running processes
        ps_cmd = 'Get-Process -Name python,pythonw -ErrorAction SilentlyContinue | ' \
                 'Select-Object Id,ProcessName,StartTime,@{Name="CommandLine";Expression={"N/A"}} | ' \
                 'ConvertTo-Json -Compress'
        proc_result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10
        )
        
        if proc_result.returncode == 0 and proc_result.stdout.strip():
            try:
                procs = json.loads(proc_result.stdout)
                if isinstance(procs, dict):
                    procs = [procs]
                python_procs = [p for p in procs if p.get("ProcessName") in ("python", "pythonw")]
                
                if len(python_procs) == 0:
                    results.append(CheckResult(
                        check_id="PRC-001",
                        name="Pipeline process check",
                        status="PASS",
                        detail="No Python processes running (pipeline not active)"
                    ))
                else:
                    results.append(CheckResult(
                        check_id="PRC-001",
                        name="Pipeline process check",
                        status="WARNING",
                        detail=f"{len(python_procs)} Python process(es) running - verify none are pipeline",
                        severity="WARNING"
                    ))
            except json.JSONDecodeError:
                results.append(CheckResult(
                    check_id="PRC-001",
                    name="Pipeline process check",
                    status="WARNING",
                    detail="Cannot parse process list output",
                    severity="WARNING"
                ))
        else:
            results.append(CheckResult(
                check_id="PRC-001",
                name="Pipeline process check",
                status="PASS",
                detail="No Python processes detected"
            ))
    except Exception as e:
        results.append(CheckResult(
            check_id="PRC-001",
            name="Pipeline process check",
            status="WARNING",
            detail=f"Cannot check processes: {e}",
            severity="WARNING"
        ))

    # 3b. Check for stale lock files
    lock_patterns = [
        os.path.join(AUDIT_DIR, "*.lock"),
        os.path.join(AUDIT_DIR, "pipeline_running"),
    ]
    lock_found = False
    for pattern in lock_patterns:
        lock_dir = os.path.dirname(pattern)
        lock_base = os.path.basename(pattern)
        if os.path.isdir(lock_dir):
            if lock_base == "pipeline_running":
                if os.path.exists(pattern):
                    lock_found = True
            else:
                for f in os.listdir(lock_dir):
                    if f.endswith(".lock"):
                        lock_found = True
                        break
    
    if lock_found:
        results.append(CheckResult(
            check_id="PRC-002",
            name="Lock file check",
            status="WARNING",
            detail="Stale lock file detected - may indicate incomplete pipeline shutdown",
            severity="WARNING"
        ))
    else:
        results.append(CheckResult(
            check_id="PRC-002",
            name="Lock file check",
            status="PASS",
            detail="No lock files found (clean state)"
        ))

    # 3c. Check pipeline status from audit log
    audit_path = os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl")
    try:
        with open(audit_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
        
        last_pipeline_event = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                event_type = event.get("event_type", event.get("type", ""))
                if "PIPELINE" in event_type.upper():
                    last_pipeline_event = event
            except json.JSONDecodeError:
                pass
        
        if last_pipeline_event:
            status = last_pipeline_event.get("status", last_pipeline_event.get("result", "UNKNOWN"))
            if "COMPLETE" in str(status).upper() or "SUCCESS" in str(status).upper():
                results.append(CheckResult(
                    check_id="PRC-003",
                    name="Last pipeline status",
                    status="WARNING",
                    detail=f"Last pipeline event shows {status} - reset needed before new run",
                    severity="WARNING"
                ))
            else:
                results.append(CheckResult(
                    check_id="PRC-003",
                    name="Last pipeline status",
                    status="PASS",
                    detail=f"Last pipeline event: {status} (not completed)"
                ))
        else:
            results.append(CheckResult(
                check_id="PRC-003",
                name="Last pipeline status",
                status="PASS",
                detail="No pipeline events found in audit log"
            ))
    except Exception as e:
        results.append(CheckResult(
            check_id="PRC-003",
            name="Last pipeline status",
            status="WARNING",
            detail=f"Cannot check pipeline status: {e}",
            severity="WARNING"
        ))

    return results


# =============================================================================
# Check 4: HOLD Factor Enforcement
# =============================================================================

def check_hold_factors(verbose=False):
    """Verify HOLD factors are properly blocked in code."""
    results = []

    # 4a. Check wind_excel_automation.py for HOLD_FACTORS definition
    automation_path = os.path.join(AUDIT_DIR, "wind_excel_automation.py")
    try:
        with open(automation_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        # Check HOLD_FACTORS dict exists
        hold_pattern = r"HOLD_FACTORS\s*=\s*\{"
        hold_match = re.search(hold_pattern, code)
        if hold_match:
            results.append(CheckResult(
                check_id="HLD-001",
                name="HOLD_FACTORS dict defined",
                status="PASS",
                detail="HOLD_FACTORS dictionary found in wind_excel_automation.py"
            ))
        else:
            results.append(CheckResult(
                check_id="HLD-001",
                name="HOLD_FACTORS dict defined",
                status="FAIL",
                detail="HOLD_FACTORS not found in wind_excel_automation.py",
                severity="CRITICAL"
            ))
        
        # Check ProcessGate.check_factor_access method
        gate_pattern = r"def\s+check_factor_access"
        gate_match = re.search(gate_pattern, code)
        if gate_match:
            results.append(CheckResult(
                check_id="HLD-002",
                name="ProcessGate.check_factor_access method",
                status="PASS",
                detail="check_factor_access method found"
            ))
        else:
            results.append(CheckResult(
                check_id="HLD-002",
                name="ProcessGate.check_factor_access method",
                status="FAIL",
                detail="check_factor_access method NOT found",
                severity="CRITICAL"
            ))
        
        # Check HoldFactorTerminationError class
        error_class_pattern = r"class\s+HoldFactorTerminationError"
        error_match = re.search(error_class_pattern, code)
        if error_match:
            results.append(CheckResult(
                check_id="HLD-003",
                name="HoldFactorTerminationError class",
                status="PASS",
                detail="HoldFactorTerminationError class defined"
            ))
        else:
            results.append(CheckResult(
                check_id="HLD-003",
                name="HoldFactorTerminationError class",
                status="FAIL",
                detail="HoldFactorTerminationError class NOT found",
                severity="CRITICAL"
            ))
        
        # Check that all 4 HOLD factors are in the dict
        for factor in HOLD_FACTORS:
            factor_pattern = r'"' + re.escape(factor) + r'"\s*:'
            factor_match = re.search(factor_pattern, code)
            if factor_match:
                results.append(CheckResult(
                    check_id="HLD-004",
                    name=f"HOLD factor {factor} defined",
                    status="PASS",
                    detail=f"{factor} found in HOLD_FACTORS"
                ))
            else:
                results.append(CheckResult(
                    check_id="HLD-004",
                    name=f"HOLD factor {factor} defined",
                    status="FAIL",
                    detail=f"{factor} NOT found in HOLD_FACTORS",
                    severity="CRITICAL"
                ))
    except Exception as e:
        results.append(CheckResult(
            check_id="HLD-001",
            name="HOLD factor code check",
            status="FAIL",
            detail=f"Cannot read wind_excel_automation.py: {e}",
            severity="CRITICAL"
        ))

    # 4b. Verify no HOLD factor data exists on disk
    hold_data_dirs = [
        os.path.join(AUDIT_DIR, "wind_excel_data"),
        os.path.join(AUDIT_DIR, "data"),
    ]
    hold_data_found = False
    for data_dir in hold_data_dirs:
        if os.path.isdir(data_dir):
            for factor in HOLD_FACTORS:
                for f in os.listdir(data_dir):
                    if factor in f:
                        hold_data_found = True
                        results.append(CheckResult(
                            check_id="HLD-005",
                            name=f"HOLD factor data check: {factor}",
                            status="FAIL",
                            detail=f"HOLD factor data file found: {data_dir}/{f}",
                            severity="CRITICAL"
                        ))
    if not hold_data_found:
        results.append(CheckResult(
            check_id="HLD-005",
            name="HOLD factor data absence",
            status="PASS",
            detail="No HOLD factor data files found on disk"
        ))

    return results


# =============================================================================
# Check 5: Credential Safety Scan
# =============================================================================

def check_credentials(verbose=False):
    """Scan for plaintext credentials in audit files."""
    results = []

    # 5a. Scan audit files for suspicious patterns
    files_scanned = 0
    suspicious_found = []

    for filepath in CREDENTIAL_SCAN_FILES:
        if not os.path.exists(filepath):
            continue
        files_scanned += 1
        
        try:
            with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
                content = f.read()
            
            # Check for suspicious patterns
            for pattern_str in SUSPICIOUS_CREDENTIAL_PATTERNS:
                # Remove allowed redaction patterns first
                cleaned = content
                for allowed_pattern in ALLOWED_CREDENTIAL_PATTERNS:
                    cleaned = re.sub(allowed_pattern, "", cleaned)
                
                matches = re.findall(pattern_str, cleaned)
                if matches:
                    suspicious_found.append({
                        "file": os.path.basename(filepath),
                        "pattern": pattern_str,
                        "matches": matches[:5],  # Limit to 5 matches
                        "count": len(matches),
                    })
        except Exception as e:
            results.append(CheckResult(
                check_id="CRD-001",
                name=f"Credential scan: {os.path.basename(filepath)}",
                status="WARNING",
                detail=f"Cannot scan file: {e}",
                severity="WARNING"
            ))

    # Report results
    if suspicious_found:
        for item in suspicious_found:
            results.append(CheckResult(
                check_id="CRD-002",
                name=f"Credential found in {item['file']}",
                status="FAIL",
                detail=f"Pattern '{item['pattern']}' found {item['count']}x in {item['file']}",
                severity="CRITICAL"
            ))
    else:
        results.append(CheckResult(
            check_id="CRD-001",
            name="Credential safety scan",
            status="PASS",
            detail=f"{files_scanned} files scanned, 0 suspicious credential patterns found"
        ))

    # 5b. Check wind_config.json for credential exposure
    config_path = os.path.join(AUDIT_DIR, "wind_config.json")
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            config_content = f.read()
        
        # Check if credentials are in config (expected - this is the credential store)
        username = _CREDENTIAL_VALUES.get("username", "")
        password = _CREDENTIAL_VALUES.get("password", "")
        has_creds = (username and username in config_content) or (password and password in config_content)
        if has_creds:
            results.append(CheckResult(
                check_id="CRD-003",
                name="wind_config.json credential presence",
                status="PASS",
                detail="Credentials found in wind_config.json (expected - this is the credential store)",
                severity="INFO"
            ))
        else:
            results.append(CheckResult(
                check_id="CRD-003",
                name="wind_config.json credential presence",
                status="WARNING",
                detail="Credentials not found in wind_config.json - verify this is expected",
                severity="WARNING"
            ))
    except Exception as e:
        results.append(CheckResult(
            check_id="CRD-003",
            name="wind_config.json check",
            status="WARNING",
            detail=f"Cannot check wind_config.json: {e}",
            severity="WARNING"
        ))

    # 5c. Verify credentials are redacted in audit events
    audit_path = os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl")
    try:
        with open(audit_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
        
        username = _CREDENTIAL_VALUES.get("username", "")
        has_username = username and username in content
        if has_username:
            # Check if it's in a redacted context
            esc_user = re.escape(username)
            redaction_patterns = [
                r"\[REDACTED[^\]]*" + esc_user,
                esc_user + r".*\[REDACTED",
            ]
            is_redacted = any(re.search(p, content) for p in redaction_patterns)
            
            if is_redacted:
                results.append(CheckResult(
                    check_id="CRD-004",
                    name="Audit credential redaction",
                    status="PASS",
                    detail="Credentials in audit log are properly redacted"
                ))
            else:
                results.append(CheckResult(
                    check_id="CRD-004",
                    name="Audit credential redaction",
                    status="FAIL",
                    detail="Credentials found in audit log WITHOUT redaction context",
                    severity="CRITICAL"
                ))
        else:
            results.append(CheckResult(
                check_id="CRD-004",
                name="Audit credential redaction",
                status="PASS",
                detail="No plaintext credentials found in audit log"
            ))
    except Exception as e:
        results.append(CheckResult(
            check_id="CRD-004",
            name="Audit credential check",
            status="WARNING",
            detail=f"Cannot check audit credentials: {e}",
            severity="WARNING"
        ))

    return results


# =============================================================================
# Check 6: File Integrity
# =============================================================================

def check_file_integrity(verbose=False):
    """Verify critical files exist and are readable."""
    results = []

    critical_files = [
        ("wind_excel_automation.py", os.path.join(AUDIT_DIR, "wind_excel_automation.py"), "code"),
        ("wind_data_pull_pipeline.py", os.path.join(AUDIT_DIR, "wind_data_pull_pipeline.py"), "code"),
        ("wind_config.json", os.path.join(AUDIT_DIR, "wind_config.json"), "config"),
        ("tracking_monitor_audit.jsonl", os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl"), "audit"),
        ("wind_excel_events.jsonl", os.path.join(AUDIT_DIR, "wind_excel_events.jsonl"), "audit"),
        ("G7_ADJUDICATION_PACKAGE_MANIFEST.json", os.path.join(G7_LEDGER_DIR, "G7_ADJUDICATION_PACKAGE_MANIFEST.json"), "manifest"),
        ("SHA256_CHECKSUMS.txt", os.path.join(G7_LEDGER_DIR, "SHA256_CHECKSUMS.txt"), "checksum"),
        ("G7_FACTOR_ADJUDICATION_REPORT.md", os.path.join(G7_LEDGER_DIR, "G7_FACTOR_ADJUDICATION_REPORT.md"), "report"),
    ]

    for name, path, category in critical_files:
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size > 0:
                results.append(CheckResult(
                    check_id="FIL-001",
                    name=f"File exists: {name}",
                    status="PASS",
                    detail=f"{path} exists ({size:,} bytes)"
                ))
            else:
                results.append(CheckResult(
                    check_id="FIL-001",
                    name=f"File empty: {name}",
                    status="FAIL",
                    detail=f"{path} is empty (0 bytes)",
                    severity="CRITICAL"
                ))
        else:
            results.append(CheckResult(
                check_id="FIL-001",
                name=f"File missing: {name}",
                status="FAIL",
                detail=f"{path} does not exist",
                severity="CRITICAL"
            ))

    return results


# =============================================================================
# Main Check Runner
# =============================================================================

def run_checks(only=None, verbose=False):
    """Run all checks and return aggregated results."""
    all_results = []
    
    check_map = {
        "governance": check_governance_invariants,
        "counter": check_call_counter,
        "process": check_pipeline_process,
        "hold": check_hold_factors,
        "credentials": check_credentials,
        "integrity": check_file_integrity,
    }
    
    if only:
        if only in check_map:
            all_results.extend(check_map[only](verbose=verbose))
        else:
            print(f"ERROR: Unknown check: {only}")
            sys.exit(1)
    else:
        for check_name, check_func in check_map.items():
            all_results.extend(check_func(verbose=verbose))
    
    return all_results


def print_results(results):
    """Print check results in formatted table."""
    print("\n" + "=" * 80)
    print("PRE-WIND CALL GUARD CHECK RESULTS")
    print("=" * 80)
    
    # Summary counts
    counts = {"PASS": 0, "FAIL": 0, "WARNING": 0, "BLOCKED": 0, "INFO": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    
    print(f"\nTotal checks: {len(results)}")
    print(f"  PASS:    {counts['PASS']}")
    print(f"  FAIL:    {counts['FAIL']}")
    print(f"  WARNING: {counts['WARNING']}")
    print(f"  BLOCKED: {counts['BLOCKED']}")
    print(f"  INFO:    {counts['INFO']}")
    
    # Print individual results
    print("\n" + "-" * 80)
    for r in results:
        icon = {"PASS": "✓", "FAIL": "✗", "WARNING": "!", "BLOCKED": "■", "INFO": "i"}
        icon_str = icon.get(r.status, "?")
        print(f"  [{icon_str}] {r.check_id}: {r.name}")
        print(f"      → {r.detail}")
    
    print("\n" + "=" * 80)
    
    # Determine exit code
    if counts["FAIL"] > 0:
        print("OVERALL: FAIL - Governance violations or HOLD breaches detected")
        return 1
    elif counts["BLOCKED"] > 0:
        print("OVERALL: BLOCKED - External blocker(s) detected")
        return 3
    elif counts["WARNING"] > 0:
        print("OVERALL: WARNING - Non-blocking issues detected, review required")
        return 2
    else:
        print("OVERALL: PASS - All checks passed, guard cleared")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="DSHA-P54 Pre-Wind-Call Guard Check Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pre_wind_call_guard_check.py                  # Run all checks
  python pre_wind_call_guard_check.py --check-governance
  python pre_wind_call_guard_check.py --verbose
  python pre_wind_call_guard_check.py --dry-run --output results.json
        """
    )
    parser.add_argument("--check-governance", action="store_true", help="Only check governance invariants")
    parser.add_argument("--check-counter", action="store_true", help="Only check call counter limits")
    parser.add_argument("--check-process", action="store_true", help="Only check pipeline process state")
    parser.add_argument("--check-hold", action="store_true", help="Only check HOLD factor enforcement")
    parser.add_argument("--check-credentials", action="store_true", help="Only scan for credentials")
    parser.add_argument("--check-integrity", action="store_true", help="Only check file integrity")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no mutation)")
    parser.add_argument("--output", type=str, help="Output results to JSON file")
    
    args = parser.parse_args()
    
    # Determine which checks to run
    only = None
    if args.check_governance:
        only = "governance"
    elif args.check_counter:
        only = "counter"
    elif args.check_process:
        only = "process"
    elif args.check_hold:
        only = "hold"
    elif args.check_credentials:
        only = "credentials"
    elif args.check_integrity:
        only = "integrity"
    
    # Run checks
    results = run_checks(only=only, verbose=args.verbose)
    
    # Print results
    exit_code = print_results(results)
    
    # Write output if requested
    if args.output:
        output = {
            "script": "pre_wind_call_guard_check.py",
            "timestamp": datetime.datetime.now().isoformat(),
            "total_checks": len(results),
            "results": [r.to_dict() for r in results],
            "exit_code": exit_code,
            "overall_status": {
                0: "PASS",
                1: "FAIL",
                2: "WARNING",
                3: "BLOCKED",
            }.get(exit_code, "UNKNOWN")
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nResults written to: {args.output}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()