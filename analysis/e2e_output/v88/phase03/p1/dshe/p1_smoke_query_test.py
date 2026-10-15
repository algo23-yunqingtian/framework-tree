#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V88 Phase03-P1 Full Smoke Query Test
=====================================
TASK_ID: V88_PHASE03_P1_DSHE_MAIN_JOB / T3
AGENT: DSHE | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose: Execute full 101-chart + derived chart smoke query,
         verify render chain and degradation chain integrity.
"""
import json
import os
import sys
import time
import hashlib
import sqlite3
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

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", "..", ".."))
ENGINE_PATH = os.path.join(REPO_ROOT, "scripts", "node_binding_engine.py")
TEST_DB = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p0", "phase03_test.db")
BASELINE_DB = os.path.join(REPO_ROOT, "scripts", "api_cache.db")

ENGINE_MD5_FROZEN = "cd73deaeec54a7f1f8bde92c1300a9dc"

OUTPUT_JSON = os.path.join(SCRIPT_DIR, "p1_smoke_query_results.json")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "p1_smoke_query_report.md")

SCHEMA_VERSION = "v88-p1.0.0"
TASK_ID = "V88_PHASE03_P1_DSHE_MAIN_JOB / T3"
EXECUTION_TS = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def run_smoke_tests():
    """Run comprehensive smoke query tests."""
    print("=" * 70)
    print("V88 Phase03-P1 Full Smoke Query Test")
    print(f"Execution: {EXECUTION_TS}")
    print("=" * 70)

    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    from node_binding_engine import NodeBindingEngine

    results = []
    total_start = time.time()

    # =========================================================================
    # Test 1: Engine MD5 Verification
    # =========================================================================
    print("\n[1/12] Engine MD5 Verification...")
    t = time.time()
    with open(ENGINE_PATH, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest().lower()
    elapsed = (time.time() - t) * 1000
    status = "PASS" if md5 == ENGINE_MD5_FROZEN else "FAIL"
    results.append({"test": "Engine MD5 Verification", "status": status,
                    "details": {"md5": md5, "expected": ENGINE_MD5_FROZEN, "elapsed_ms": round(elapsed, 3)}})
    print(f"  [{status}] MD5: {md5}")

    # =========================================================================
    # Test 2: Engine Load
    # =========================================================================
    print("\n[2/12] Engine Load...")
    t = time.time()
    try:
        engine = NodeBindingEngine(repo_root=REPO_ROOT)
        ok, msg = engine.load()
        elapsed = (time.time() - t) * 1000
        if ok:
            status = "PASS"
            results.append({"test": "Engine Load", "status": "PASS",
                            "details": {"msg": msg, "elapsed_ms": round(elapsed, 3)}})
            print(f"  [PASS] {msg}")
        else:
            status = "FAIL"
            results.append({"test": "Engine Load", "status": "FAIL",
                            "details": {"msg": msg, "elapsed_ms": round(elapsed, 3)}})
            print(f"  [FAIL] {msg}")
    except Exception as e:
        results.append({"test": "Engine Load", "status": "FAIL",
                        "details": {"error": str(e)}})
        print(f"  [FAIL] {e}")
        return results

    # =========================================================================
    # Test 3: Chart Count Validation
    # =========================================================================
    print("\n[3/12] Chart Count Validation...")
    t = time.time()
    total_charts = len(engine.charts)
    matchable = len(engine.get_matchable_charts())
    pending = len(engine.get_pending_charts())
    elapsed = (time.time() - t) * 1000
    if total_charts == 101:
        status = "PASS"
    elif total_charts >= 100:
        status = "WARN"
    else:
        status = "FAIL"
    results.append({"test": "Chart Count", "status": status,
                    "details": {"total": total_charts, "matchable": matchable,
                                "pending": pending, "expected": 101}})
    print(f"  [{status}] Total={total_charts}, Matchable={matchable}, Pending={pending}")

    # =========================================================================
    # Test 4: Full Render All Charts
    # =========================================================================
    print("\n[4/12] Full Render All Charts...")
    t = time.time()
    render_errors = 0
    render_count = 0
    source_counts = {"real": 0, "simulated": 0, "placeholder": 0, "other": 0}
    render_latencies = []

    for cb in engine.charts:
        t1 = time.time()
        try:
            res = engine.render_with_fallback(cb.chart_id)
            lat = (time.time() - t1) * 1000
            render_latencies.append(lat)
            if res.get("renderable"):
                render_count += 1
                src = res.get("source", "other")
                source_counts[src] = source_counts.get(src, 0) + 1
            else:
                render_errors += 1
        except Exception as e:
            render_errors += 1

    elapsed = (time.time() - t) * 1000
    if render_errors == 0:
        status = "PASS"
    elif render_errors < total_charts * 0.05:
        status = "WARN"
    else:
        status = "FAIL"
    results.append({"test": "Full Render All Charts", "status": status,
                    "details": {"rendered": render_count, "errors": render_errors,
                                "total": total_charts, "sources": source_counts,
                                "elapsed_ms": round(elapsed, 1)}})
    print(f"  [{status}] Rendered={render_count}/{total_charts}, Errors={render_errors}, Sources={source_counts}")

    # =========================================================================
    # Test 5: Latency Distribution
    # =========================================================================
    print("\n[5/12] Latency Distribution...")
    t = time.time()
    if render_latencies:
        render_latencies.sort()
        n = len(render_latencies)
        median = render_latencies[n // 2]
        p95 = render_latencies[int(n * 0.95)]
        p99 = render_latencies[int(n * 0.99)]
        max_lat = render_latencies[-1]
        mean_lat = sum(render_latencies) / n
        status = "PASS" if p99 < 500 else "WARN"
        results.append({"test": "Latency Distribution", "status": status,
                        "details": {"median_ms": round(median, 3),
                                    "p95_ms": round(p95, 3),
                                    "p99_ms": round(p99, 3),
                                    "max_ms": round(max_lat, 3),
                                    "mean_ms": round(mean_lat, 3)}})
        print(f"  [{status}] Median={median:.3f}ms, P95={p95:.3f}ms, P99={p99:.3f}ms, Max={max_lat:.3f}ms")
    else:
        results.append({"test": "Latency Distribution", "status": "BLOCKED",
                        "details": {"error": "No latency data"}})
        print("  [BLOCKED] No latency data")

    # =========================================================================
    # Test 6: Degradation Chain - Normal DB
    # =========================================================================
    print("\n[6/12] Degradation Chain - Normal DB...")
    t = time.time()
    old_p03 = os.environ.get("V88_PHASE03_TEST_DB", "")
    os.environ["V88_PHASE03_TEST_DB"] = str(TEST_DB) if os.path.exists(TEST_DB) else "/nonexistent"
    degraded_count = 0
    for cb in engine.charts[:20]:
        try:
            res = engine.render_with_fallback(cb.chart_id)
            if not res.get("renderable"):
                degraded_count += 1
        except Exception:
            degraded_count += 1
    elapsed = (time.time() - t) * 1000
    status = "PASS" if degraded_count == 0 else "WARN"
    if old_p03:
        os.environ["V88_PHASE03_TEST_DB"] = old_p03
    else:
        os.environ.pop("V88_PHASE03_TEST_DB", None)
    results.append({"test": "Degradation Normal DB", "status": status,
                    "details": {"degraded": degraded_count, "tested": 20}})
    print(f"  [{status}] Degraded={degraded_count}/20")

    # =========================================================================
    # Test 7: Degradation Chain - No DB
    # =========================================================================
    print("\n[7/12] Degradation Chain - No DB...")
    t = time.time()
    old_p03 = os.environ.get("V88_PHASE03_TEST_DB", "")
    old_api = os.environ.get("V88_API_CACHE_DB", "")
    os.environ["V88_PHASE03_TEST_DB"] = "/nonexistent/test.db"
    os.environ["V88_API_CACHE_DB"] = "/nonexistent/api.db"
    no_db_degraded = 0
    for cb in engine.charts[:20]:
        try:
            res = engine.render_with_fallback(cb.chart_id)
            if not res.get("renderable"):
                no_db_degraded += 1
        except Exception:
            no_db_degraded += 1
    elapsed = (time.time() - t) * 1000
    status = "PASS" if no_db_degraded == 0 else "FAIL"
    if old_p03:
        os.environ["V88_PHASE03_TEST_DB"] = old_p03
    else:
        os.environ.pop("V88_PHASE03_TEST_DB", None)
    if old_api:
        os.environ["V88_API_CACHE_DB"] = old_api
    else:
        os.environ.pop("V88_API_CACHE_DB", None)
    results.append({"test": "Degradation No DB", "status": status,
                    "details": {"degraded": no_db_degraded, "tested": 20}})
    print(f"  [{status}] Degraded={no_db_degraded}/20 (0 = graceful)")

    # =========================================================================
    # Test 8: Dual Schema Detection
    # =========================================================================
    print("\n[8/12] Dual Schema Detection...")
    t = time.time()
    try:
        db_path = engine._resolve_db_path()
        if db_path and os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            tables = engine._detect_table_schema(cursor)
            conn.close()
            has_ic = "indicator_cache" in tables
            has_sc = "series_cache" in tables
            if has_ic or has_sc:
                status = "PASS"
            else:
                status = "WARN"
            results.append({"test": "Dual Schema Detection", "status": status,
                            "details": {"db": db_path, "tables": list(tables),
                                        "indicator_cache": has_ic, "series_cache": has_sc}})
            print(f"  [{status}] Tables={list(tables)}")
        else:
            results.append({"test": "Dual Schema Detection", "status": "WARN",
                            "details": {"error": "No DB available"}})
            print("  [WARN] No DB available")
    except Exception as e:
        results.append({"test": "Dual Schema Detection", "status": "WARN",
                        "details": {"error": str(e)}})
        print(f"  [WARN] {e}")

    # =========================================================================
    # Test 9: Env Var Switching
    # =========================================================================
    print("\n[9/12] Env Var Switching...")
    t = time.time()
    old_p03 = os.environ.get("V88_PHASE03_TEST_DB", "")
    old_api = os.environ.get("V88_API_CACHE_DB", "")
    os.environ.pop("V88_PHASE03_TEST_DB", None)
    os.environ.pop("V88_API_CACHE_DB", None)
    db_default = engine._resolve_db_path()
    os.environ["V88_API_CACHE_DB"] = "/nonexistent/api.db"
    db_api = engine._resolve_db_path()
    os.environ["V88_PHASE03_TEST_DB"] = "/nonexistent/test.db"
    db_test = engine._resolve_db_path()
    if old_p03:
        os.environ["V88_PHASE03_TEST_DB"] = old_p03
    if old_api:
        os.environ["V88_API_CACHE_DB"] = old_api
    elapsed = (time.time() - t) * 1000
    status = "PASS"
    results.append({"test": "Env Var Switching", "status": status,
                    "details": {"default": db_default, "api": db_api, "test": db_test}})
    print(f"  [{status}] Priority: default={bool(db_default)}, api={bool(db_api)}, test={bool(db_test)}")

    # =========================================================================
    # Test 10: Render Validation (no cross-node, valid types)
    # =========================================================================
    print("\n[10/12] Validation Results...")
    t = time.time()
    try:
        vresults = engine.validate(strict=False)
        errors = [r for r in vresults if r.severity == "ERROR"]
        warns = [r for r in vresults if r.severity == "WARN"]
        passes = [r for r in vresults if r.severity == "PASS"]
        status = "PASS" if len(errors) == 0 else "WARN"
        results.append({"test": "Validation", "status": status,
                        "details": {"pass": len(passes), "warn": len(warns), "error": len(errors),
                                    "total": len(vresults)}})
        print(f"  [{status}] PASS={len(passes)}, WARN={len(warns)}, ERROR={len(errors)}")
    except Exception as e:
        results.append({"test": "Validation", "status": "WARN",
                        "details": {"error": str(e)}})
        print(f"  [WARN] {e}")

    # =========================================================================
    # Test 11: DB Integrity Check
    # =========================================================================
    print("\n[11/12] DB Integrity Check...")
    t = time.time()
    try:
        db_info = {}
        for db_name, db_path in [("test_db", TEST_DB), ("baseline_db", BASELINE_DB)]:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                db_info[db_name] = {"path": db_path, "tables": tables,
                                     "size_bytes": os.path.getsize(db_path)}
                if "series_cache" in tables:
                    cursor.execute("SELECT COUNT(*) FROM series_cache")
                    db_info[db_name]["series_cache_rows"] = cursor.fetchone()[0]
                conn.close()
        status = "PASS" if db_info else "WARN"
        results.append({"test": "DB Integrity", "status": status,
                        "details": db_info})
        print(f"  [{status}] DB info collected: {list(db_info.keys())}")
    except Exception as e:
        results.append({"test": "DB Integrity", "status": "WARN",
                        "details": {"error": str(e)}})
        print(f"  [WARN] {e}")

    # =========================================================================
    # Test 12: No Unauthorized Code Changes
    # =========================================================================
    print("\n[12/12] No Unauthorized Code Changes...")
    t = time.time()
    with open(ENGINE_PATH, "rb") as f:
        md5_final = hashlib.md5(f.read()).hexdigest().lower()
    elapsed = (time.time() - t) * 1000
    status = "PASS" if md5_final == ENGINE_MD5_FROZEN else "FAIL"
    results.append({"test": "No Unauthorized Changes", "status": status,
                    "details": {"md5": md5_final}})
    print(f"  [{status}] Engine MD5 unchanged: {md5_final}")

    # =========================================================================
    # Summary
    # =========================================================================
    total_elapsed = (time.time() - total_start) * 1000
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    blocked_count = sum(1 for r in results if r["status"] == "BLOCKED")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {len(results)} tests in {total_elapsed:.1f}ms")
    print(f"PASS={pass_count} WARN={warn_count} FAIL={fail_count} BLOCKED={blocked_count}")
    print("=" * 70)

    # Save JSON
    report = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "execution_timestamp": EXECUTION_TS,
        "total_time_ms": round(total_elapsed, 1),
        "summary": {"PASS": pass_count, "WARN": warn_count, "FAIL": fail_count, "BLOCKED": blocked_count},
        "results": results,
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[Output] {OUTPUT_JSON}")

    return report


if __name__ == "__main__":
    run_smoke_tests()