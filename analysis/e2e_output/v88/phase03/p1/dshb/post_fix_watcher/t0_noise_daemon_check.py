#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T0: Noise daemon liveness check + patrol
V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB

Checks:
1. Noise daemon process is running
2. Checkpoint file shows progress
3. Log file has recent entries
4. Time series CSV is being written
5. Generates watcher_state_checkpoint.json
"""

import os
import sys
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUNBUFFERED"] = "1"
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
DHB_DIR = SCRIPT_DIR.parent
FOLLOWUP_DIR = DHB_DIR / "followup"
WATCHER_DIR = DHB_DIR / "watcher"
P1_DIR = DHB_DIR.parent
PHASE03_DIR = P1_DIR.parent
DB_PATH = PHASE03_DIR / "p0" / "phase03_test.db"

def check_process():
    """Check if noise_7d_observation.py process is running."""
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine", "/format:list"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        noise_procs = []
        for line in output.split("\n"):
            if "noise_7d_observation" in line.lower():
                noise_procs.append(line.strip())
        return noise_procs
    except Exception as e:
        return ["[ERROR] %s" % str(e)]

def check_checkpoint():
    """Check noise checkpoint file."""
    checkpoint_path = FOLLOWUP_DIR / "noise_7d_checkpoint.json"
    if not checkpoint_path.exists():
        return {"error": "checkpoint file not found"}
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_log():
    """Check noise log file."""
    log_path = FOLLOWUP_DIR / "noise_7d_log.jsonl"
    if not log_path.exists():
        return {"error": "log file not found", "entries": 0}
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return {
        "entries": len(entries),
        "last_entry": entries[-1] if entries else None,
        "first_entry": entries[0] if entries else None,
    }

def check_csv():
    """Check noise time series CSV."""
    csv_path = WATCHER_DIR / "noise_7d_timeseries_log.csv"
    if not csv_path.exists():
        return {"error": "CSV not found", "entries": 0}
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return {
        "entries": len(lines) - 1,  # minus header
        "header": lines[0] if lines else None,
        "last_entry": lines[-1] if lines else None,
    }

def main():
    print("=" * 70)
    print("T0: NOISE DAEMON LIVENESS CHECK")
    print("TASK: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB")
    print("TIME: %s" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    print("=" * 70)

    results = {
        "task_id": "V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB",
        "agent": "DSHB",
        "branch": "feature/v88-g1",
        "check_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "t0_noise_daemon": {},
    }

    # 1. Check processes
    print("\n[1/4] Checking noise daemon process...")
    procs = check_process()
    results["t0_noise_daemon"]["processes_found"] = len(procs)
    results["t0_noise_daemon"]["process_details"] = procs
    if procs and "[ERROR]" not in str(procs[0]):
        print("    ✅ Noise daemon process(es) running: %d" % len(procs))
        results["t0_noise_daemon"]["status"] = "RUNNING"
    else:
        print("    ⚠️  Noise daemon process NOT detected")
        results["t0_noise_daemon"]["status"] = "NOT_DETECTED"

    # 2. Check checkpoint
    print("\n[2/4] Checking checkpoint file...")
    cp = check_checkpoint()
    if "error" in cp:
        print("    ❌ %s" % cp["error"])
        results["t0_noise_daemon"]["checkpoint_status"] = "ERROR"
    else:
        hour = cp.get("observation_hour", 0)
        complete = cp.get("observation_complete", False)
        last_obs = cp.get("last_observed_at", "N/A")
        print("    ✅ Checkpoint: hour=%d/%d, complete=%s, last=%s" % (hour, 168, complete, last_obs))
        results["t0_noise_daemon"]["checkpoint"] = {
            "hour": hour,
            "total_hours": 168,
            "complete": complete,
            "last_observed_at": last_obs,
            "progress_pct": round(hour / 168 * 100, 2)
        }
        results["t0_noise_daemon"]["checkpoint_status"] = "OK"

    # 3. Check log
    print("\n[3/4] Checking log file...")
    log_data = check_log()
    if "error" in log_data:
        print("    ❌ %s" % log_data["error"])
    else:
        entries = log_data["entries"]
        last = log_data["last_entry"]
        first = log_data["first_entry"]
        print("    ✅ Log entries: %d" % entries)
        if last:
            print("       Last: hour=%d, rate=%.4f%%, at=%s" % (
                last.get("observation_hour", 0),
                last.get("global_noise_rate", 0) * 100,
                last.get("timestamp", "N/A")
            ))
        results["t0_noise_daemon"]["log_entries"] = entries
        if last:
            results["t0_noise_daemon"]["latest_noise_rate_pct"] = round(last.get("global_noise_rate", 0) * 100, 4)
            results["t0_noise_daemon"]["latest_hour"] = last.get("observation_hour", 0)
        if first:
            results["t0_noise_daemon"]["first_observation_at"] = first.get("timestamp", "N/A")

    # 4. Check CSV
    print("\n[4/4] Checking time series CSV...")
    csv_data = check_csv()
    if "error" in csv_data:
        print("    ❌ %s" % csv_data["error"])
    else:
        entries = csv_data["entries"]
        print("    ✅ CSV entries: %d" % entries)
        results["t0_noise_daemon"]["csv_entries"] = entries

    # 5. Overall assessment
    print("\n" + "=" * 70)
    print("T0 ASSESSMENT")
    print("=" * 70)
    
    cp_data = check_checkpoint()
    if "error" not in cp_data:
        hour = cp_data.get("observation_hour", 0)
        complete = cp_data.get("observation_complete", False)
        noise_rate_pct = results["t0_noise_daemon"].get("latest_noise_rate_pct", 0)
        
        print("  Observation progress: %d/168 hours (%.2f%%)" % (hour, hour/168*100))
        print("  Noise rate: %.4f%%" % noise_rate_pct)
        print("  Target: < 10.0%")
        print("  Status: %s" % ("✅ PASS (<10%)" if noise_rate_pct < 10 else "⚠️ WARN (>10%)"))
        print("  Complete: %s" % ("YES - 7 days done" if complete else "NO - %d more hours needed" % (168 - hour)))
        
        results["t0_noise_daemon"]["noise_rate_pct"] = noise_rate_pct
        results["t0_noise_daemon"]["target_rate_pct"] = 10.0
        results["t0_noise_daemon"]["at_target"] = noise_rate_pct < 10
        results["t0_noise_daemon"]["remaining_hours"] = 168 - hour
        results["t0_noise_daemon"]["complete"] = complete
        results["t0_noise_daemon"]["p013_status"] = "PENDING_168H" if not complete else ("PASS" if noise_rate_pct < 10 else "FAIL")

    # Save state checkpoint
    state_path = SCRIPT_DIR / "watcher_state_checkpoint.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n  State saved to: %s" % state_path)
    print("\n  ✅ T0 COMPLETE")

if __name__ == "__main__":
    main()
