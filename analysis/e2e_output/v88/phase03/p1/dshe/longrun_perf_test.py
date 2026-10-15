#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V88 Phase03-P1 Long-Term Stability & Performance Test
======================================================
TASK_ID: V88_PHASE03_P1_DSHE_MAIN_JOB / T4
AGENT: DSHE | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose: Execute long-term stability test, measure P99 latency,
         CPU usage, and performance delta from indicator expansion.
"""
import json
import os
import sys
import time
import hashlib
import sqlite3
import statistics
import math
import traceback
from datetime import datetime
from typing import Optional, Dict, List, Any

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", "..", ".."))
ENGINE_PATH = os.path.join(REPO_ROOT, "scripts", "node_binding_engine.py")
TEST_DB = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p0", "phase03_test.db")

ENGINE_MD5_FROZEN = "cd73deaeec54a7f1f8bde92c1300a9dc"
LATENCY_P99_THRESHOLD_MS = 500.0
LATENCY_P99_TARGET_MS = 200.0
CPU_FUSE_THRESHOLD_PCT = 2.0
D7_COVERAGE_THRESHOLD_PCT = 60.0

# Phase02 baseline values (from P0 final review)
PHASE02_P99_MS = 39.193
PHASE02_D7_COVERAGE_PCT = 68.3168

OUTPUT_JSON = os.path.join(SCRIPT_DIR, "longrun_perf_results.json")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "longrun_perf_results.md")

SCHEMA_VERSION = "v88-p1.0.0"
TASK_ID = "V88_PHASE03_P1_DSHE_MAIN_JOB / T4"
EXECUTION_TS = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def run_longrun_test(rounds=5, charts_per_round=None):
    """Execute long-term stability test."""
    print("=" * 70)
    print("V88 Phase03-P1 Long-Term Stability & Performance Test")
    print(f"Execution: {EXECUTION_TS}")
    print(f"Rounds: {rounds}, Charts per round: {charts_per_round or 'ALL'}")
    print("=" * 70)

    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    from node_binding_engine import NodeBindingEngine

    # Try to load adapter
    sys.path.insert(0, SCRIPT_DIR)
    try:
        from engine_180indicator_adapter import Engine180IndicatorAdapter
        adapter_available = True
    except Exception:
        adapter_available = False

    # Try to load psutil
    try:
        import psutil
        psutil_available = True
    except Exception:
        psutil_available = False

    # Try to load resource
    try:
        import resource
        resource_available = True
    except Exception:
        resource_available = False

    # Initialize engine
    engine = NodeBindingEngine(repo_root=REPO_ROOT)
    ok, msg = engine.load()
    if not ok:
        print(f"[FATAL] Engine load failed: {msg}")
        return

    total_charts = len(engine.charts)
    matchable = len(engine.get_matchable_charts())

    # Resolve DB
    old_p03 = os.environ.get("V88_PHASE03_TEST_DB", "")
    if os.path.exists(TEST_DB):
        os.environ["V88_PHASE03_TEST_DB"] = str(TEST_DB)

    if charts_per_round is None:
        charts_per_round = total_charts

    # Collect metrics
    round_results = []
    all_latencies = []
    all_cpu_samples = []
    all_wall_times = []
    all_render_counts = {"real": 0, "simulated": 0, "placeholder": 0, "error": 0}

    if psutil_available:
        proc = psutil.Process()
        proc.cpu_percent(None)  # warmup
        time.sleep(0.1)

    print(f"\nStarting {rounds} rounds x {charts_per_round} charts...")
    for r in range(rounds):
        round_start = time.time()
        round_latencies = []
        round_source_counts = {"real": 0, "simulated": 0, "placeholder": 0, "error": 0}

        if psutil_available:
            round_cpu = proc.cpu_percent(None)
        else:
            round_cpu = None

        for cb in engine.charts[:charts_per_round]:
            t1 = time.time()
            try:
                res = engine.render_with_fallback(cb.chart_id)
                lat = (time.time() - t1) * 1000
                round_latencies.append(lat)
                src = res.get("source", "error")
                round_source_counts[src] = round_source_counts.get(src, 0) + 1
                all_render_counts[src] = all_render_counts.get(src, 0) + 1
            except Exception:
                round_source_counts["error"] += 1
                all_render_counts["error"] += 1

        wall_time = (time.time() - round_start) * 1000

        # Collect CPU sample at end of round
        if psutil_available:
            round_cpu = proc.cpu_percent(None)
            time.sleep(0.05)  # allow CPU time to settle

        all_latencies.extend(round_latencies)
        all_wall_times.append(wall_time)
        if round_cpu is not None:
            all_cpu_samples.append(round_cpu)

        # Latency stats for this round
        if round_latencies:
            round_latencies.sort()
            n = len(round_latencies)
            round_p99 = round_latencies[min(int(n * 0.99), n - 1)]
            round_p95 = round_latencies[min(int(n * 0.95), n - 1)]
            round_median = round_latencies[n // 2]
        else:
            round_p99 = round_p95 = round_median = 0

        round_data = {
            "round": r + 1,
            "charts": charts_per_round,
            "wall_time_ms": round(wall_time, 1),
            "latency_median_ms": round(round_median, 3),
            "latency_p95_ms": round(round_p95, 3),
            "latency_p99_ms": round(round_p99, 3),
            "cpu_pct": round(round_cpu, 4) if round_cpu is not None else None,
            "sources": round_source_counts,
        }
        round_results.append(round_data)
        cpu_str = f"{round_cpu:.2f}%" if round_cpu is not None else "N/A"
        print(f"  Round {r+1}/{rounds}: {wall_time:.0f}ms, P99={round_p99:.2f}ms, CPU={cpu_str}, "
              f"real={round_source_counts['real']}, sim={round_source_counts['simulated']}")

    # Restore env
    if old_p03:
        os.environ["V88_PHASE03_TEST_DB"] = old_p03
    else:
        os.environ.pop("V88_PHASE03_TEST_DB", None)

    # Compute overall stats
    total_wall = sum(all_wall_times)
    if all_latencies:
        all_latencies.sort()
        n = len(all_latencies)
        overall_median = all_latencies[n // 2]
        overall_p95 = all_latencies[min(int(n * 0.95), n - 1)]
        overall_p99 = all_latencies[min(int(n * 0.99), n - 1)]
        overall_max = all_latencies[-1]
        overall_mean = sum(all_latencies) / n
    else:
        overall_median = overall_p95 = overall_p99 = overall_max = overall_mean = 0

    if all_cpu_samples:
        cpu_mean = sum(all_cpu_samples) / len(all_cpu_samples)
        cpu_peak = max(all_cpu_samples)
    else:
        cpu_mean = cpu_peak = None

    # RSS memory
    rss_mb = None
    if resource_available:
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_mb = round(rss_kb / 1024.0, 2)

    # D7 coverage: unique charts that ever rendered as 'real' across all rounds
    real_chart_ids = set()
    for rr in round_results:
        for cb in engine.charts[:charts_per_round]:
            t1 = time.time()
            try:
                res = engine.render_with_fallback(cb.chart_id)
                if res.get("source") == "real":
                    real_chart_ids.add(cb.chart_id)
            except Exception:
                pass
    d7_real = len(real_chart_ids)
    d7_coverage_pct = round(d7_real / max(total_charts, 1) * 100, 4)
    total_renders = d7_real + sum(all_render_counts.get(k, 0) for k in ["simulated", "placeholder", "error"])

    # Performance delta vs Phase02
    p99_delta_ms = round(overall_p99 - PHASE02_P99_MS, 3)
    p99_delta_pct = round((overall_p99 - PHASE02_P99_MS) / PHASE02_P99_MS * 100, 2) if PHASE02_P99_MS > 0 else None
    d7_delta_pct_pts = round(d7_coverage_pct - PHASE02_D7_COVERAGE_PCT, 4)

    # Verdict
    if overall_p99 < LATENCY_P99_THRESHOLD_MS and d7_coverage_pct >= D7_COVERAGE_THRESHOLD_PCT:
        verdict = "PASS"
    elif overall_p99 < LATENCY_P99_THRESHOLD_MS * 2:
        verdict = "WARN"
    else:
        verdict = "FAIL"

    # Build report
    report = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "execution_timestamp": EXECUTION_TS,
        "rounds": rounds,
        "charts_per_round": charts_per_round,
        "total_charts": total_charts,
        "matchable_charts": matchable,
        "metrics": {
            "latency": {
                "median_ms": round(overall_median, 3),
                "p95_ms": round(overall_p95, 3),
                "p99_ms": round(overall_p99, 3),
                "max_ms": round(overall_max, 3),
                "mean_ms": round(overall_mean, 3),
                "threshold_p99_ms": LATENCY_P99_THRESHOLD_MS,
                "target_p99_ms": LATENCY_P99_TARGET_MS,
            },
            "cpu": {
                "mean_pct": round(cpu_mean, 4) if cpu_mean is not None else None,
                "peak_pct": round(cpu_peak, 4) if cpu_peak is not None else None,
                "fuse_threshold_pct": CPU_FUSE_THRESHOLD_PCT,
                "caliber": "process-level instantaneous (NOT comparable to Phase02 FUSE 2.0%)",
            },
            "memory": {
                "rss_max_mb": rss_mb,
            },
            "wall_time": {
                "total_ms": round(total_wall, 1),
                "avg_per_round_ms": round(total_wall / max(rounds, 1), 1),
            },
            "coverage": {
                "d7_real": d7_real,
                "d7_total": total_charts,
                "d7_coverage_pct": d7_coverage_pct,
                "threshold_pct": D7_COVERAGE_THRESHOLD_PCT,
            },
            "source_distribution": all_render_counts,
        },
        "phase02_comparison": {
            "phase02_p99_ms": PHASE02_P99_MS,
            "phase02_d7_pct": PHASE02_D7_COVERAGE_PCT,
            "p99_delta_ms": p99_delta_ms,
            "p99_delta_pct": p99_delta_pct,
            "d7_delta_pct_pts": d7_delta_pct_pts,
        },
        "rounds_detail": round_results,
        "verdict": verdict,
        "psutil_available": psutil_available,
        "resource_available": resource_available,
    }

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[Output] {OUTPUT_JSON}")

    # Print summary
    print("\n" + "=" * 70)
    print(f"LONG-RUN STABILITY REPORT")
    print(f"Rounds: {rounds} x {charts_per_round} charts")
    print(f"Total renders: {total_renders}")
    print(f"Latency: median={overall_median:.3f}ms, P95={overall_p95:.3f}ms, P99={overall_p99:.3f}ms, Max={overall_max:.3f}ms")
    print(f"CPU: mean={cpu_mean:.2f}%, peak={cpu_peak:.2f}%" if cpu_mean is not None else "CPU: N/A (psutil unavailable)")
    print(f"RSS: {rss_mb} MB" if rss_mb else "RSS: N/A")
    print(f"D7 Coverage: {d7_real}/{total_charts} = {d7_coverage_pct}%")
    print(f"Phase02 Comparison: P99 delta={p99_delta_ms}ms ({p99_delta_pct}%), D7 delta={d7_delta_pct_pts}pp")
    print(f"VERDICT: {verdict}")
    print("=" * 70)

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="V88 P1 Long-Term Performance Test")
    parser.add_argument("--rounds", "-r", type=int, default=5, help="Number of rounds")
    parser.add_argument("--charts", "-c", type=int, default=None, help="Charts per round")
    args = parser.parse_args()
    run_longrun_test(rounds=args.rounds, charts_per_round=args.charts)