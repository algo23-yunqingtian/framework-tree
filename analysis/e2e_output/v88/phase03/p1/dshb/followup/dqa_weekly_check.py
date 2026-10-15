#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dqa_weekly_check.py — V88 Phase03 P1 DSHB DQA周度自动校验脚本
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_FOLLOWUP_JOB (T4)
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  每周自动全量校验测试库，确保DQA 8条规则持续可用。
  调用 verify_testdb.py 执行全套校验，输出周报。

  DQA 8条规则:
    DQA-01: 空值检测
    DQA-02: 重复ID检测
    DQA-03: 时间连续性检测
    DQA-04: 数值越界检测 (3-sigma)
    DQA-05: 映射缺失检测
    DQA-06: 时间漂移检测
    DQA-07: 重复点检测
    DQA-08: 单位不一致检测

Usage:
  python dqa_weekly_check.py [--db path/to/phase03_test.db] [--once]
  python dqa_weekly_check.py --cron  (启动7x24h守护模式)

  调度示例 (Linux cron, 每周一 09:00):
    0 9 * * 1 python /path/to/dqa_weekly_check.py --once
"""

import os
import sys
import platform
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
FOLLOWUP_DIR = SCRIPT_DIR
DHB_DIR = FOLLOWUP_DIR.parent
P1_DIR = DHB_DIR.parent
PHASE03_DIR = P1_DIR.parent
SCRIPTS_DIR = P1_DIR / "scripts"
DB_PATH_DEFAULT = PHASE03_DIR / "p0" / "phase03_test.db"
OUTPUT_DIR = FOLLOWUP_DIR
LOG_FILE = "dqa_weekly_log.jsonl"
CHECKPOINT_FILE = "dqa_weekly_checkpoint.json"

# Weekly check configuration
CHECK_INTERVAL_DAYS = 7
MAX_REPORTS_KEEP = 52  # Keep 1 year of reports

# DQA rules (from P1)
DQA_RULES = [
    ("DQA-01", "NULL detection"),
    ("DQA-02", "Duplicate ID detection"),
    ("DQA-03", "Time continuity"),
    ("DQA-04", "Value out-of-bounds (3-sigma)"),
    ("DQA-05", "Mapping missing"),
    ("DQA-06", "Time drift"),
    ("DQA-07", "Duplicate points (stale)"),
    ("DQA-08", "Unit inconsistency"),
]

# =============================================================================
# Platform Setup
# =============================================================================

def setup_environment():
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

# =============================================================================
# Core Check Functions
# =============================================================================

def run_dqa_check(db_path):
    """Run verify_testdb.py with --dqa flag."""
    verify_script = SCRIPTS_DIR / "verify_testdb.py"
    if not verify_script.exists():
        return {
            "status": "FAIL",
            "reason": "verify_testdb.py not found at %s" % verify_script,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }

    cmd = [sys.executable, str(verify_script), "--db", str(db_path), "--dqa"]
    print("[DQA] Running: %s" % " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300  # 5 minute timeout
        )

        # Parse output for DQA results
        output = result.stdout + result.stderr
        dqa_results = parse_dqa_results(output)

        return {
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "db_path": str(db_path),
            "dqa_results": dqa_results,
            "output_tail": output[-500:] if len(output) > 500 else output
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "FAIL",
            "reason": "Timeout after 300 seconds",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
    except Exception as e:
        return {
            "status": "FAIL",
            "reason": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }


def parse_dqa_results(output):
    """Parse DQA results from verify_testdb.py output."""
    results = {}
    current_rule = None
    for line in output.split("\n"):
        for rule_id, rule_name in DQA_RULES:
            if rule_id in line:
                current_rule = rule_id
                results[rule_id] = {
                    "name": rule_name,
                    "status": "UNKNOWN"
                }
                break

        if current_rule and "[PASS]" in line:
            results[current_rule]["status"] = "PASS"
        elif current_rule and "[FAIL]" in line:
            results[current_rule]["status"] = "FAIL"
        elif current_rule and "[WARN]" in line:
            results[current_rule]["status"] = "WARN"

    return results

# =============================================================================
# State Management
# =============================================================================

def load_checkpoint():
    """Load checkpoint from disk."""
    checkpoint_path = OUTPUT_DIR / CHECKPOINT_FILE
    if checkpoint_path.exists():
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_checkpoint(state):
    """Save checkpoint to disk."""
    checkpoint_path = OUTPUT_DIR / CHECKPOINT_FILE
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def append_log(entry):
    """Append check entry to JSONL log."""
    log_path = OUTPUT_DIR / LOG_FILE
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# =============================================================================
# Report Generation
# =============================================================================

def generate_weekly_report(check_results):
    """Generate weekly DQA check report."""
    total_checks = len(check_results)
    pass_count = sum(1 for c in check_results if c.get("status") == "PASS")
    fail_count = sum(1 for c in check_results if c.get("status") == "FAIL")
    warn_count = sum(1 for c in check_results if c.get("status") == "WARN")

    all_dqa_pass = all(
        dqa.get("status") == "PASS"
        for check in check_results
        for dqa in check.get("dqa_results", {}).values()
    )

    lines = []
    lines.append("# V88 Phase03 P1 — DQA 周度校验报告")
    lines.append("")
    lines.append("> **TASK_ID**: V88_PHASE03_P1_DSHB_FOLLOWUP_JOB (T4)")
    lines.append("> **AGENT**: DSHB | **BRANCH**: feature/v88-g1")
    lines.append("> **生成时间**: %s" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    lines.append("> **总校验次数**: %d" % total_checks)
    lines.append("")
    lines.append("## 1. 校验汇总")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|-----:|")
    lines.append("| 总校验次数 | %d |" % total_checks)
    lines.append("| PASS | %d |" % pass_count)
    lines.append("| FAIL | %d |" % fail_count)
    lines.append("| WARN | %d |" % warn_count)
    lines.append("| DQA 8条规则全PASS | %s |" % ("是" if all_dqa_pass else "否"))
    lines.append("")
    lines.append("## 2. DQA 规则状态")
    lines.append("")
    lines.append("| 规则 | 名称 | 最近状态 |")
    lines.append("|------|------|:--------:|")
    for rule_id, rule_name in DQA_RULES:
        latest_status = "N/A"
        for check in reversed(check_results):
            if rule_id in check.get("dqa_results", {}):
                latest_status = check["dqa_results"][rule_id].get("status", "N/A")
                break
        lines.append("| %s | %s | %s |" % (rule_id, rule_name, latest_status))
    lines.append("")
    lines.append("## 3. 最近5次校验记录")
    lines.append("")
    lines.append("| # | 时间戳 | 状态 | DB行数 | 指标数 |")
    lines.append("|:-:|--------|:----:|------:|------:|")
    for i, check in enumerate(check_results[-5:]):
        dqa_pass = all(
            dqa.get("status") == "PASS"
            for dqa in check.get("dqa_results", {}).values()
        )
        lines.append("| %d | %s | %s | — | — |" % (
            total_checks - len(check_results) + i + 1,
            check["timestamp"],
            "PASS" if dqa_pass else "WARN/FAIL"
        ))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by dqa_weekly_check.py | %s*" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    return "\n".join(lines)

# =============================================================================
# Main
# =============================================================================

def main():
    setup_environment()

    parser = argparse.ArgumentParser(description="V88 Phase03 P1 DSHB DQA weekly check")
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT), help="Path to phase03_test.db")
    parser.add_argument("--once", action="store_true", help="Execute single check and exit")
    parser.add_argument("--cron", action="store_true", help="Start weekly check daemon")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print("[ERROR] DB not found: %s" % db_path)
        sys.exit(1)

    # Load checkpoint
    state = load_checkpoint()
    if state is None:
        state = {
            "task_id": "V88_PHASE03_P1_DSHB_FOLLOWUP_JOB",
            "agent": "DSHB",
            "branch": "feature/v88-g1",
            "started_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "check_count": 0,
            "last_checked_at": None,
            "log_file": LOG_FILE,
            "checkpoint_file": CHECKPOINT_FILE
        }
        save_checkpoint(state)

    if args.once or not args.cron:
        # Single check mode
        print("[DQA] Running single DQA check...")
        result = run_dqa_check(db_path)

        # Log result
        log_entry = {
            "timestamp": result["timestamp"],
            "check_number": state["check_count"] + 1,
            "status": result["status"],
            "exit_code": result.get("exit_code", -1),
            "dqa_results": result.get("dqa_results", {})
        }
        append_log(log_entry)

        state["check_count"] += 1
        state["last_checked_at"] = result["timestamp"]
        save_checkpoint(state)

        # Print summary
        print("\n[DQA] Check #%d: %s" % (state["check_count"], result["status"]))
        print("[DQA] DQA Results:")
        for rule_id, rule_name in DQA_RULES:
            dqa = result.get("dqa_results", {}).get(rule_id, {})
            status = dqa.get("status", "N/A")
            print("  %-8s %-30s %s" % (rule_id, rule_name, status))

        if result["status"] == "FAIL":
            print("\n[DQA] FAIL: %s" % result.get("reason", "See output"))
            print(result.get("output_tail", ""))

        return

    if args.cron:
        # Daemon mode
        print("[DQA] Starting DQA weekly check daemon...")
        print("[DQA] Interval: %d days | Target: verify_testdb.py --dqa" % CHECK_INTERVAL_DAYS)
        print("[DQA] Press Ctrl+C to stop")
        print()

        try:
            while True:
                next_check_time = None
                if state.get("last_checked_at"):
                    last = datetime.fromisoformat(state["last_checked_at"])
                    next_check_time = last + timedelta(days=CHECK_INTERVAL_DAYS)

                now = datetime.now()
                if next_check_time and now < next_check_time:
                    wait_hours = (next_check_time - now).total_seconds() / 3600
                    print("[DQA] Next check at %s (%.1f hours from now)" % (
                        next_check_time.strftime("%Y-%m-%dT%H:%M:%S"),
                        wait_hours
                    ))
                    # Sleep in smaller intervals to allow Ctrl+C
                    sleep_sec = min(wait_hours * 3600, 3600)
                    import time
                    time.sleep(sleep_sec)
                else:
                    print("[DQA] Time for weekly check...")
                    result = run_dqa_check(db_path)
                    log_entry = {
                        "timestamp": result["timestamp"],
                        "check_number": state["check_count"] + 1,
                        "status": result["status"],
                        "exit_code": result.get("exit_code", -1),
                        "dqa_results": result.get("dqa_results", {})
                    }
                    append_log(log_entry)
                    state["check_count"] += 1
                    state["last_checked_at"] = result["timestamp"]
                    save_checkpoint(state)
                    print("[DQA] Check #%d: %s" % (state["check_count"], result["status"]))
        except KeyboardInterrupt:
            print()
            print("[DQA] Stopped by user. Progress saved.")
            sys.exit(0)


if __name__ == "__main__":
    main()