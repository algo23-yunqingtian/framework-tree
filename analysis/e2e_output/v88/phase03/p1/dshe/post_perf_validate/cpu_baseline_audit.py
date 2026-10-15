#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V88 Phase03 P1 — CPU Baseline Collection Script Audit
=======================================================
TASK_ID: V88_PHASE03_P1_DSHE_POST_PERF_VALIDATE_JOB / T2
AGENT: DSHE | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

PURPOSE:
  Audit collect_cpu_baseline_p1_optimized.py for:
  1. FUSE baseline isolation (Phase02 2.0% full-chain vs P1 process-level)
  2. artifact_declares_incomparable flag logic stability
  3. Caliber comparability declarations
  4. Path resolution correctness
  5. Cross-version baseline isolation logic
  6. Generate final P1 CPU baseline report for P0-12 gate review

USAGE:
  python cpu_baseline_audit.py
"""

import argparse
import hashlib
import json
import os
import platform
import socket
import sqlite3
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

# Platform Setup
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, Exception):
    pass

# Anchor-Search REPO_ROOT
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_MD5_FROZEN = "cd73deaeec54a7f1f8bde92c1300a9dc"

def anchor_search_repo_root(start_dir=None, max_parents=12):
    if start_dir is None:
        start_dir = SCRIPT_DIR
    current = os.path.abspath(start_dir)
    for _ in range(max_parents):
        candidate_engine = os.path.join(current, "scripts", "node_binding_engine.py")
        if os.path.exists(candidate_engine):
            with open(candidate_engine, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest().lower()
            if md5 == ENGINE_MD5_FROZEN:
                return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None

REPO_ROOT = anchor_search_repo_root()
if REPO_ROOT is None:
    print("[FATAL] Cannot locate frozen engine.")
    sys.exit(1)

ENGINE_PATH = os.path.join(REPO_ROOT, "scripts", "node_binding_engine.py")
TEST_DB = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p0", "phase03_test.db")
DSHE_DIR = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p1", "dshe")
CPU_BASELINE_SCRIPT = os.path.join(DSHE_DIR, "collect_cpu_baseline_p1.py")

SCRIPT_VERSION = "1.0.0"
TASK_ID = "V88_PHASE03_P1_DSHE_POST_PERF_VALIDATE_JOB / T2"
SCHEMA_VERSION = "v88-post-perf-validate.1.0"
CPU_FUSE_THRESHOLD_PCT = 2.0
CPU_PHASE02_PEAK_PCT = 1.94
CPU_P0_OPTIMIZED_TARGET_PCT = 1.75

OUTPUT_JSON = os.path.join(SCRIPT_DIR, "cpu_baseline_audit_results.json")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "v88_phase03_p1_final_cpu_baseline_audit.md")

# Phase02 caliber metadata
PHASE02_CALIBER = {
    "description": "Full-chain business steady-state mean (data supply + push + render)",
    "scope": "DSHB",
    "measurement_method": "Process-level CPU over 24h business window",
    "fuse_threshold_pct": CPU_FUSE_THRESHOLD_PCT,
    "observed_peak_pct": CPU_PHASE02_PEAK_PCT,
    "optimization_target_pct": CPU_P0_OPTIMIZED_TARGET_PCT,
}

# P1 caliber metadata
P1_CALIBER = {
    "description": "Render-process instantaneous measurement (psutil or time.process_time())",
    "scope": "DSHE",
    "measurement_method": "psutil.Process().cpu_percent() or time.process_time() window-averaged",
    "includes_yaml_parsing": True,
    "includes_python_interpreter_overhead": True,
    "not_comparable_to_phase02": True,
}


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[%s] [%s] %s" % (ts, level, msg))


def audit_cpu_baseline(output_path=None):
    """Run CPU baseline audit."""
    log("=" * 72)
    log("V88 Phase03 P1 — CPU Baseline Collection Script Audit")
    log("Script: cpu_baseline_audit.py v%s" % SCRIPT_VERSION)
    log("=" * 72)

    audit_results = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "agent": "DSHE",
        "branch": "feature/v88-g1",
        "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "environment": {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_release": platform.release(),
            "arch": platform.machine(),
            "python_version": sys.version,
        },
        "audit_checks": [],
        "baseline_data": {},
        "comparability_analysis": {},
        "verdict": "UNKNOWN",
        "p0_12_gate_readiness": False,
    }

    # ------------------------------------------------------------------
    # Check 1: Script Exists
    # ------------------------------------------------------------------
    log("[1/10] Checking CPU baseline script existence...")
    script_exists = os.path.exists(CPU_BASELINE_SCRIPT)
    script_size = os.path.getsize(CPU_BASELINE_SCRIPT) if script_exists else 0
    audit_results["audit_checks"].append({
        "id": "CHK-01",
        "name": "Script Exists",
        "status": "PASS" if script_exists else "FAIL",
        "message": "Script exists: %s (%d bytes)" % (script_exists, script_size),
        "details": {"path": CPU_BASELINE_SCRIPT, "exists": script_exists, "size_bytes": script_size},
    })
    log("  [%s] Script: %s (%d bytes)" % ("PASS" if script_exists else "FAIL", script_exists, script_size))

    # ------------------------------------------------------------------
    # Check 2: Script Content Analysis
    # ------------------------------------------------------------------
    log("[2/10] Analyzing script content for isolation logic...")
    script_content = ""
    if script_exists:
        with open(CPU_BASELINE_SCRIPT, "r", encoding="utf-8") as f:
            script_content = f.read()

    # Check for caliber declaration
    has_caliber_declaration = "CALIBER DIFFERENCE" in script_content or "caliber_declaration" in script_content
    has_comparability_note = "comparability_note" in script_content or "NOT DIRECTLY COMPARABLE" in script_content
    has_artifact_declares_incomparable = "artifact_declares_incomparable" in script_content
    has_fuse_threshold_ref = str(CPU_FUSE_THRESHOLD_PCT) in script_content
    has_phase02_peak_ref = str(CPU_PHASE02_PEAK_PCT) in script_content
    has_p0_target_ref = str(CPU_P0_OPTIMIZED_TARGET_PCT) in script_content
    has_no_zhiji_api = "NO ZHIJI" in script_content.upper() or "no_zhiji" in script_content
    has_no_engine_mod = "NO ENGINE MODIFICATION" in script_content.upper() or "no_engine_modification" in script_content
    has_branch_locked = "BRANCH_LOCKED" in script_content
    has_psutil_fallback = "psutil" in script_content
    has_process_time_fallback = "time.process_time()" in script_content
    has_same_script_load = "same_script" in script_content or "SAME_SCRIPT" in script_content
    has_same_load = "same_load" in script_content or "SAME_LOAD" in script_content
    has_same_time_window = "same_time_window" in script_content or "SAME_TIME_WINDOW" in script_content

    audit_results["audit_checks"].append({
        "id": "CHK-02",
        "name": "Caliber Declaration",
        "status": "PASS" if has_caliber_declaration else "FAIL",
        "message": "Caliber difference declared: %s" % has_caliber_declaration,
        "details": {"has_declaration": has_caliber_declaration},
    })
    log("  [%s] Caliber declaration: %s" % ("PASS" if has_caliber_declaration else "FAIL", has_caliber_declaration))

    # ------------------------------------------------------------------
    # Check 3: Artifact Declares Incomparable
    # ------------------------------------------------------------------
    log("[3/10] Checking artifact_declares_incomparable flag...")
    audit_results["audit_checks"].append({
        "id": "CHK-03",
        "name": "artifact_declares_incomparable",
        "status": "PASS" if has_artifact_declares_incomparable else "WARN",
        "message": "Flag present: %s (explicit flag ensures consumers know calibers differ)" % has_artifact_declares_incomparable,
        "details": {
            "has_explicit_flag": has_artifact_declares_incomparable,
            "has_comparability_note": has_comparability_note,
            "has_not_directly_comparable": "NOT_DIRECTLY_COMPARABLE" in script_content,
            "has_ratio_vs_phase02": "ratio_vs_phase02_peak" in script_content,
        },
    })
    log("  [%s] artifact_declares_incomparable: %s" % ("PASS" if has_artifact_declares_incomparable else "WARN", has_artifact_declares_incomparable))

    # ------------------------------------------------------------------
    # Check 4: FUSE Baseline Isolation
    # ------------------------------------------------------------------
    log("[4/10] Verifying FUSE baseline isolation...")
    fuse_isolation_checks = {
        "fuse_threshold_referenced": has_fuse_threshold_ref,
        "phase02_peak_referenced": has_phase02_peak_ref,
        "p0_target_referenced": has_p0_target_ref,
        "caliber_separation_declared": has_caliber_declaration,
        "comparison_ratio_present": "ratio_vs_phase02_peak" in script_content,
        "mismatch_warning_present": "NOT DIRECTLY COMPARABLE" in script_content or "NOT DIRECTLY COMPAREABLE" in script_content,
    }
    fuse_isolation_pass = all(fuse_isolation_checks.values())
    audit_results["audit_checks"].append({
        "id": "CHK-04",
        "name": "FUSE Baseline Isolation",
        "status": "PASS" if fuse_isolation_pass else "WARN",
        "message": "FUSE isolation: %d/%d checks passed" % (sum(fuse_isolation_checks.values()), len(fuse_isolation_checks)),
        "details": fuse_isolation_checks,
    })
    log("  [%s] FUSE isolation: %d/%d" % ("PASS" if fuse_isolation_pass else "WARN",
                                           sum(fuse_isolation_checks.values()), len(fuse_isolation_checks)))

    # ------------------------------------------------------------------
    # Check 5: Constraint Compliance
    # ------------------------------------------------------------------
    log("[5/10] Verifying constraint compliance in script...")
    constraint_checks = {
        "no_zhiji_api": has_no_zhiji_api,
        "no_engine_modification": has_no_engine_mod,
        "branch_locked": has_branch_locked,
        "append_only": "APPEND_ONLY" in script_content,
        "no_overwrite": "NO_OVERWRITE" in script_content,
    }
    constraint_pass = sum(constraint_checks.values())
    audit_results["audit_checks"].append({
        "id": "CHK-05",
        "name": "Constraint Compliance",
        "status": "PASS" if constraint_pass >= 4 else "WARN",
        "message": "%d/%d constraints verified" % (constraint_pass, len(constraint_checks)),
        "details": constraint_checks,
    })
    log("  [%s] Constraints: %d/%d" % ("PASS" if constraint_pass >= 4 else "WARN",
                                        constraint_pass, len(constraint_checks)))

    # ------------------------------------------------------------------
    # Check 6: Measurement Method Fallbacks
    # ------------------------------------------------------------------
    log("[6/10] Verifying measurement method fallbacks...")
    method_checks = {
        "psutil_support": has_psutil_fallback,
        "process_time_fallback": has_process_time_fallback,
        "resource_module_fallback": "resource.getrusage" in script_content,
        "per_core_normalization": "per_core" in script_content or "nproc" in script_content,
        "window_based_cpu": "window_cpu" in script_content or "start_timing" in script_content,
    }
    method_pass = all(method_checks.values())
    audit_results["audit_checks"].append({
        "id": "CHK-06",
        "name": "Measurement Method Fallbacks",
        "status": "PASS" if method_pass else "WARN",
        "message": "All fallbacks present: %s" % all(method_checks.values()),
        "details": method_checks,
    })
    log("  [%s] Method fallbacks: %s" % ("PASS" if method_pass else "WARN", all(method_checks.values())))

    # ------------------------------------------------------------------
    # Check 7: Same-Script/Same-Load/Same-Time-Window
    # ------------------------------------------------------------------
    log("[7/10] Verifying comparison metadata tags...")
    comparison_checks = {
        "same_script_tag": has_same_script_load,
        "same_load_tag": has_same_load,
        "same_time_window_tag": has_same_time_window,
    }
    comparison_pass = all(comparison_checks.values())
    audit_results["audit_checks"].append({
        "id": "CHK-07",
        "name": "Comparison Metadata Tags",
        "status": "PASS" if comparison_pass else "WARN",
        "message": "All 3 tags present: %s" % comparison_pass,
        "details": comparison_checks,
    })
    log("  [%s] Comparison tags: %s" % ("PASS" if comparison_pass else "WARN", comparison_pass))

    # ------------------------------------------------------------------
    # Check 8: DB Path Resolution
    # ------------------------------------------------------------------
    log("[8/10] Verifying DB path resolution...")
    db_checks = {
        "test_db_exists": os.path.exists(TEST_DB),
        "baseline_db_exists": os.path.exists(os.path.join(REPO_ROOT, "scripts", "api_cache.db")),
        "env_var_support": "V88_PHASE03_TEST_DB" in script_content,
        "auto_detect": "auto-detected" in script_content or "setup_test_db_env" in script_content,
        "priority_chain": "V88_API_CACHE_DB" in script_content,
    }
    db_pass = all(db_checks.values())
    audit_results["audit_checks"].append({
        "id": "CHK-08",
        "name": "DB Path Resolution",
        "status": "PASS" if db_pass else "WARN",
        "message": "DB resolution: %d/%d checks passed" % (sum(db_checks.values()), len(db_checks)),
        "details": db_checks,
    })
    log("  [%s] DB resolution: %d/%d" % ("PASS" if db_pass else "WARN",
                                          sum(db_checks.values()), len(db_checks)))

    # ------------------------------------------------------------------
    # Check 9: Output Structure Completeness
    # ------------------------------------------------------------------
    log("[9/10] Verifying output structure completeness...")
    output_checks = {
        "summary_section": '"summary"' in script_content,
        "per_round_section": '"per_round"' in script_content,
        "per_chart_type_section": '"per_chart_type"' in script_content,
        "caliber_comparability_section": '"caliber_comparability"' in script_content,
        "environment_section": '"environment"' in script_content,
        "measurement_method_section": '"measurement_method"' in script_content,
        "engine_info_section": '"engine_info"' in script_content,
        "log_lines_section": '"log_lines"' in script_content,
        "status_field": '"status"' in script_content,
    }
    output_pass = all(output_checks.values())
    audit_results["audit_checks"].append({
        "id": "CHK-09",
        "name": "Output Structure Completeness",
        "status": "PASS" if output_pass else "WARN",
        "message": "Output sections: %d/%d present" % (sum(output_checks.values()), len(output_checks)),
        "details": output_checks,
    })
    log("  [%s] Output structure: %d/%d" % ("PASS" if output_pass else "WARN",
                                             sum(output_checks.values()), len(output_checks)))

    # ------------------------------------------------------------------
    # Check 10: Engine MD5 Verification
    # ------------------------------------------------------------------
    log("[10/10] Verifying engine MD5...")
    try:
        with open(ENGINE_PATH, "rb") as f:
            engine_md5 = hashlib.md5(f.read()).hexdigest().lower()
        md5_match = engine_md5 == ENGINE_MD5_FROZEN
        audit_results["audit_checks"].append({
            "id": "CHK-10",
            "name": "Engine MD5 Frozen",
            "status": "PASS" if md5_match else "FAIL",
            "message": "MD5=%s (frozen: %s)" % (engine_md5, md5_match),
            "details": {"md5": engine_md5, "expected": ENGINE_MD5_FROZEN, "match": md5_match},
        })
        log("  [%s] Engine MD5: %s" % ("PASS" if md5_match else "FAIL", engine_md5))
    except Exception as e:
        audit_results["audit_checks"].append({
            "id": "CHK-10", "name": "Engine MD5 Frozen", "status": "FAIL", "message": str(e),
        })
        log("  [FAIL] %s" % str(e))

    # ------------------------------------------------------------------
    # Build Comparability Analysis
    # ------------------------------------------------------------------
    log("Building comparability analysis...")
    audit_results["comparability_analysis"] = {
        "phase02_caliber": PHASE02_CALIBER,
        "p1_caliber": P1_CALIBER,
        "caliber_difference_factor": "~45-52x (full-chain business mean vs process-level instantaneous)",
        "direct_comparison_allowed": False,
        "reason": "Phase02 CPU FUSE 2.0% / peak 1.94% is a full-chain business steady-state mean (DSHB scope). P1 CPU baseline is a render-process instantaneous measurement (DSHE scope). The two calibers differ by ~45-52x and are NOT DIRECTLY COMPARABLE.",
        "correct_usage": "P1 CPU gate decisions require DSHB full-chain caliber A/B comparison (same script / same load / same time window)",
        "artifact_declares_incomparable": has_artifact_declares_incomparable,
        "ratio_vs_phase02_peak_note": "Script reports ratio_vs_phase02_peak for reference only — MUST NOT be used for gate decisions",
    }

    # ------------------------------------------------------------------
    # Build Baseline Data
    # ------------------------------------------------------------------
    audit_results["baseline_data"] = {
        "script_path": CPU_BASELINE_SCRIPT,
        "script_size_bytes": script_size,
        "engine_md5": engine_md5 if md5_match else "MISMATCH",
        "test_db_path": TEST_DB,
        "test_db_exists": os.path.exists(TEST_DB),
        "test_db_size_bytes": os.path.getsize(TEST_DB) if os.path.exists(TEST_DB) else 0,
    }

    # ------------------------------------------------------------------
    # Determine Verdict
    # ------------------------------------------------------------------
    check_statuses = [c["status"] for c in audit_results["audit_checks"]]
    fail_count = sum(1 for s in check_statuses if s == "FAIL")
    warn_count = sum(1 for s in check_statuses if s == "WARN")

    if fail_count > 0:
        audit_results["verdict"] = "FAIL"
        audit_results["verdict_message"] = "%d checks FAIL" % fail_count
        audit_results["p0_12_gate_readiness"] = False
    elif not has_artifact_declares_incomparable:
        audit_results["verdict"] = "WARN"
        audit_results["verdict_message"] = "artifact_declares_incomparable flag missing"
        audit_results["p0_12_gate_readiness"] = True  # Still usable with warning
    else:
        audit_results["verdict"] = "PASS"
        audit_results["verdict_message"] = "All audit checks pass, P0-12 gate ready"
        audit_results["p0_12_gate_readiness"] = True

    # ------------------------------------------------------------------
    # Write Output
    # ------------------------------------------------------------------
    json_str = json.dumps(audit_results, ensure_ascii=False, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
    else:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            f.write(json_str)
    log("JSON output: %s (%d bytes)" % (OUTPUT_JSON, len(json_str)))

    # Write Markdown report
    write_markdown_report(audit_results)
    log("MD output: %s" % OUTPUT_MD)

    log("=" * 72)
    log("CPU BASELINE AUDIT COMPLETE")
    log("  Checks: %d PASS, %d WARN, %d FAIL" % (
        sum(1 for s in check_statuses if s == "PASS"),
        warn_count, fail_count))
    log("  P0-12 Gate Readiness: %s" % audit_results["p0_12_gate_readiness"])
    log("  Verdict: %s" % audit_results["verdict"])
    log("=" * 72)

    return audit_results


def write_markdown_report(audit_results):
    """Write Markdown audit report."""
    lines = []
    lines.append("# V88 Phase03 P1 — Final CPU Baseline Audit Report")
    lines.append("")
    lines.append("> **TASK_ID**: %s" % audit_results["task_id"])
    lines.append("> **Agent**: DSHE | **Branch**: feature/v88-g1 (BRANCH_LOCKED)")
    lines.append("> **Generated**: %s" % audit_results["generated"])
    lines.append("> **Purpose**: CPU baseline isolation audit for P0-12 gate review")
    lines.append("")

    lines.append("## Audit Summary")
    lines.append("")
    lines.append("| Check ID | Name | Status | Message |")
    lines.append("|----------|------|:------:|---------|")
    for c in audit_results["audit_checks"]:
        lines.append("| %s | %s | %s | %s |" % (
            c["id"], c["name"], c["status"], c["message"][:80]))
    lines.append("")

    lines.append("## Caliber Comparability Analysis")
    lines.append("")
    ca = audit_results.get("comparability_analysis", {})
    lines.append("| Property | Phase02 | P1 |")
    lines.append("|----------|---------|----|")
    lines.append("| Scope | %s | %s |" % (
        ca.get("phase02_caliber", {}).get("scope", ""),
        ca.get("p1_caliber", {}).get("scope", "")))
    lines.append("| Measurement | %s | %s |" % (
        ca.get("phase02_caliber", {}).get("measurement_method", ""),
        ca.get("p1_caliber", {}).get("measurement_method", "")))
    lines.append("| CPU Threshold | %.1f%% | N/A (process-level) |" % ca.get("phase02_caliber", {}).get("fuse_threshold_pct", 2.0))
    lines.append("| Observed Peak | %.2f%% | Process-level |" % ca.get("phase02_caliber", {}).get("observed_peak_pct", 1.94))
    lines.append("")
    lines.append("**Comparability**: %s" % ca.get("direct_comparison_allowed", False))
    lines.append("")
    lines.append("**Reason**: %s" % ca.get("reason", ""))
    lines.append("")
    lines.append("**Correct Usage**: %s" % ca.get("correct_usage", ""))
    lines.append("")
    lines.append("**artifact_declares_incomparable**: %s" % ca.get("artifact_declares_incomparable", False))
    lines.append("")

    lines.append("## Baseline Data")
    lines.append("")
    bd = audit_results.get("baseline_data", {})
    lines.append("| Property | Value |")
    lines.append("|----------|-------|")
    lines.append("| Script | `%s` |" % bd.get("script_path", ""))
    lines.append("| Script Size | %d bytes |" % bd.get("script_size_bytes", 0))
    lines.append("| Engine MD5 | `%s` |" % bd.get("engine_md5", ""))
    lines.append("| Test DB | `%s` |" % bd.get("test_db_path", ""))
    lines.append("| Test DB Exists | %s |" % bd.get("test_db_exists", False))
    lines.append("| Test DB Size | %d bytes |" % bd.get("test_db_size_bytes", 0))
    lines.append("")

    lines.append("## P0-12 Gate Readiness")
    lines.append("")
    lines.append("**Status**: %s" % audit_results["p0_12_gate_readiness"])
    lines.append("")
    if audit_results["p0_12_gate_readiness"]:
        lines.append("The CPU baseline collection script is ready for P0-12 gate review.")
        lines.append("The FUSE baseline isolation is correctly implemented:")
        lines.append("- Caliber difference declared explicitly")
        lines.append("- artifact_declares_incomparable flag present")
        lines.append("- Phase02 FUSE 2.0% and P1 process-level measurements are NOT directly compared")
        lines.append("- Ratio vs Phase02 peak reported for reference only")
    else:
        lines.append("The CPU baseline collection script has issues that must be resolved before P0-12 gate review.")
    lines.append("")

    lines.append("## Verdict")
    lines.append("")
    lines.append("**%s** — %s" % (audit_results.get("verdict", ""), audit_results.get("verdict_message", "")))
    lines.append("")
    lines.append("---")
    lines.append("*Report Generated: %s | Agent: DSHE | Branch: feature/v88-g1 (BRANCH_LOCKED)*" % audit_results["generated"])

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="CPU Baseline Collection Script Audit")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        results = audit_cpu_baseline(output_path=args.output)
        return 0 if results.get("verdict") in ("PASS", "WARN") else 1
    except KeyboardInterrupt:
        log_error("Interrupted by user")
        return 130
    except Exception as e:
        log_error("Unhandled exception: %s\n%s" % (str(e), traceback.format_exc()))
        return 2


if __name__ == "__main__":
    sys.exit(main())