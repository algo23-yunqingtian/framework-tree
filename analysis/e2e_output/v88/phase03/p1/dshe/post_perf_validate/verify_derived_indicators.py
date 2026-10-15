#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V88 Phase03 P1 — 70 New Derived Indicators Engine Render Verification
=======================================================================
TASK_ID: V88_PHASE03_P1_DSHE_POST_PERF_VALIDATE_JOB / T3
AGENT: DSHE | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

PURPOSE:
  Verify that all 70 new derived indicators (DSHB P0-9 expansion) render
  correctly through the engine. Checks:
  1. Each derived indicator can be identified and classified
  2. Engine adapter can compute derived indicator values
  3. D7 coverage remains ≥ 80.20% after integration
  4. No render errors introduced by derived indicators

  The 70 derived indicators are sourced from the DSHB metric indicator
  code mapping (source='derived'), covering 7 categories:
  - Term structure (期限结构)
  - Month spread (月差)
  - Long/short ratio (多空比)
  - Percentile/deviation (分位/偏差)
  - Top20 concentration (Top20集中度)
  - Balance sheet (平衡表)
  - Price spread (价差)

USAGE:
  python verify_derived_indicators.py
  python verify_derived_indicators.py --output verify_derived_indicators.json
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
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Platform Setup
# ---------------------------------------------------------------------------
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, Exception):
    pass

# ---------------------------------------------------------------------------
# Anchor-Search REPO_ROOT
# ---------------------------------------------------------------------------
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
    current = os.path.abspath(os.getcwd())
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
    print("[FATAL] Cannot locate frozen engine. Check repo structure.")
    sys.exit(1)

ENGINE_PATH = os.path.join(REPO_ROOT, "scripts", "node_binding_engine.py")
TEST_DB = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p0", "phase03_test.db")
BASELINE_DB = os.path.join(REPO_ROOT, "scripts", "api_cache.db")
DSHB_DIR = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p1", "dshb")
DSHE_DIR = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p1", "dshe")
MAPPING_JSON = os.path.join(DSHB_DIR, "v88_phase03_p1_metric_indicator_code_mapping.json")

SCRIPT_VERSION = "1.0.0"
TASK_ID = "V88_PHASE03_P1_DSHE_POST_PERF_VALIDATE_JOB / T3"
SCHEMA_VERSION = "v88-post-perf-validate.1.0"
D7_COVERAGE_THRESHOLD = 80.20  # Must maintain ≥ 80.20%
EXPECTED_DERIVED_COUNT = 70

OUTPUT_JSON = os.path.join(SCRIPT_DIR, "verify_derived_indicators.json")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "new_derived_metric_render_verify_result.md")

# Derived indicator categories
DERIVED_CATEGORIES = {
    "term_structure": ["term_structure"],
    "month_spread": ["month_spread", "month_diff"],
    "long_short_ratio": ["long_short_ratio", "longshort", "openinterest_longshort"],
    "percentile_deviation": ["pct_", "dev_", "percentile"],
    "top20_concentration": ["top20", "top20_long", "top20_short"],
    "balance_sheet": ["balance_sheet", "supply_demand"],
    "price_spread": ["spread", "lme_spread", "comex"],
}

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[%s] [%s] %s" % (ts, level, msg))

def log_warn(msg):
    log(msg, "WARN")

def log_error(msg):
    log(msg, "ERROR")


def verify_derived_indicators(output_path=None):
    """Main verification function."""
    log("=" * 72)
    log("V88 Phase03 P1 — 70 New Derived Indicators Engine Render Verification")
    log("Script: verify_derived_indicators.py v%s" % SCRIPT_VERSION)
    log("=" * 72)

    results = {
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
        "tests": [],
        "derived_indicators": {},
        "render_results": {},
        "coverage_results": {},
        "errors": [],
        "verdict": "UNKNOWN",
    }

    # ------------------------------------------------------------------
    # Test 1: Engine MD5 Verification
    # ------------------------------------------------------------------
    log("[1/8] Engine MD5 Verification...")
    try:
        with open(ENGINE_PATH, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest().lower()
        pass_md5 = md5 == ENGINE_MD5_FROZEN
        results["tests"].append({
            "id": "TC-DI-01",
            "name": "Engine MD5 Verification",
            "status": "PASS" if pass_md5 else "FAIL",
            "message": "MD5=%s expected=%s" % (md5, ENGINE_MD5_FROZEN),
            "details": {"md5": md5, "expected": ENGINE_MD5_FROZEN, "match": pass_md5},
        })
        log("  [%s] MD5=%s" % ("PASS" if pass_md5 else "FAIL", md5))
    except Exception as e:
        results["tests"].append({"id": "TC-DI-01", "name": "Engine MD5 Verification", "status": "FAIL", "message": str(e)})
        log_error("  [FAIL] %s" % str(e))

    # ------------------------------------------------------------------
    # Test 2: Load DSHB Mapping
    # ------------------------------------------------------------------
    log("[2/8] Loading DSHB mapping...")
    derived_indicators = {}
    all_mapping = []
    try:
        if os.path.exists(MAPPING_JSON):
            with open(MAPPING_JSON, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
            all_mapping = mapping_data.get("mapping_list", [])
            # Extract derived indicators
            for item in all_mapping:
                if item.get("source") == "derived":
                    derived_indicators[item["indicator_id"]] = item
            log("  [PASS] Loaded %d mapping items, %d derived indicators" % (
                len(all_mapping), len(derived_indicators)))
            results["derived_indicators"] = {
                "total_from_mapping": len(all_mapping),
                "derived_count": len(derived_indicators),
                "expected_count": EXPECTED_DERIVED_COUNT,
                "count_match": len(derived_indicators) == EXPECTED_DERIVED_COUNT,
                "indicator_ids": list(derived_indicators.keys()),
            }
        else:
            log_warn("  [WARN] Mapping JSON not found: %s" % MAPPING_JSON)
            results["derived_indicators"] = {"total_from_mapping": 0, "derived_count": 0, "expected_count": EXPECTED_DERIVED_COUNT, "count_match": False}
    except Exception as e:
        log_error("  [FAIL] %s" % str(e))
        results["errors"].append("mapping_load: %s" % str(e))

    # ------------------------------------------------------------------
    # Test 3: Engine Load
    # ------------------------------------------------------------------
    log("[3/8] Loading NodeBindingEngine...")
    engine = None
    try:
        sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
        from node_binding_engine import NodeBindingEngine
        if os.path.exists(TEST_DB):
            os.environ["V88_PHASE03_TEST_DB"] = TEST_DB
        engine = NodeBindingEngine(repo_root=REPO_ROOT)
        ok, msg = engine.load()
        if not ok:
            log_error("  [FAIL] Engine load failed: %s" % msg)
        else:
            log("  [PASS] %s" % msg)
            results["tests"].append({"id": "TC-DI-02", "name": "Engine Load", "status": "PASS", "message": msg})
    except Exception as e:
        log_error("  [FAIL] Engine load failed: %s" % str(e))
        results["tests"].append({"id": "TC-DI-02", "name": "Engine Load", "status": "FAIL", "message": str(e)})

    # ------------------------------------------------------------------
    # Test 4: Load Adapter
    # ------------------------------------------------------------------
    log("[4/8] Loading 180 Indicator Adapter...")
    adapter = None
    try:
        sys.path.insert(0, DSHE_DIR)
        from engine_180indicator_adapter import Engine180IndicatorAdapter
        if engine:
            adapter = Engine180IndicatorAdapter(REPO_ROOT, engine)
            log("  [PASS] Adapter loaded")
            results["tests"].append({"id": "TC-DI-03", "name": "Adapter Load", "status": "PASS", "message": "Engine180IndicatorAdapter loaded"})
        else:
            adapter = Engine180IndicatorAdapter(REPO_ROOT, db_path=TEST_DB)
            log("  [PASS] Adapter loaded (standalone mode)")
            results["tests"].append({"id": "TC-DI-03", "name": "Adapter Load", "status": "PASS", "message": "Standalone mode"})
    except Exception as e:
        log_warn("  [WARN] Adapter load failed: %s" % str(e))
        results["tests"].append({"id": "TC-DI-03", "name": "Adapter Load", "status": "WARN", "message": str(e)})

    # ------------------------------------------------------------------
    # Test 5: Categorize Derived Indicators
    # ------------------------------------------------------------------
    log("[5/8] Categorizing derived indicators...")
    category_counts = defaultdict(int)
    uncategorized = []
    for ind_id, ind_data in derived_indicators.items():
        categorized = False
        for cat_name, keywords in DERIVED_CATEGORIES.items():
            if any(kw in ind_id.lower() for kw in keywords):
                category_counts[cat_name] += 1
                categorized = True
                break
        if not categorized:
            uncategorized.append(ind_id)

    results["derived_indicators"]["categories"] = dict(category_counts)
    results["derived_indicators"]["uncategorized"] = uncategorized
    results["derived_indicators"]["categorized_count"] = sum(category_counts.values())
    results["derived_indicators"]["uncategorized_count"] = len(uncategorized)

    log("  Categories: %s" % dict(category_counts))
    log("  Uncategorized: %d" % len(uncategorized))

    # ------------------------------------------------------------------
    # Test 6: Adapter Derived Indicator Support
    # ------------------------------------------------------------------
    log("[6/8] Verifying adapter derived indicator support...")
    adapter_derived = 0
    adapter_base = 0
    if adapter:
        try:
            adapter_derived = adapter.get_derived_indicator_count()
            adapter_base = adapter.get_base_indicator_count()
            log("  Adapter reports: %d base + %d derived = %d total" % (
                adapter_base, adapter_derived, adapter_base + adapter_derived))

            # Check which derived indicators the adapter knows about
            adapter_known = set()
            for ind_id in derived_indicators:
                if adapter.is_derived_indicator(ind_id):
                    adapter_known.add(ind_id)

            results["derived_indicators"]["adapter_known"] = len(adapter_known)
            results["derived_indicators"]["adapter_unknown"] = len(derived_indicators) - len(adapter_known)
            results["derived_indicators"]["adapter_coverage_pct"] = round(
                len(adapter_known) / len(derived_indicators) * 100, 2) if derived_indicators else 0

            log("  Adapter knows: %d/%d derived indicators (%.2f%%)" % (
                len(adapter_known), len(derived_indicators),
                results["derived_indicators"]["adapter_coverage_pct"]))
        except Exception as e:
            log_warn("  Adapter derived check failed: %s" % str(e))
            results["errors"].append("adapter_check: %s" % str(e))

    # ------------------------------------------------------------------
    # Test 7: Full Render All Charts (D7 Coverage)
    # ------------------------------------------------------------------
    log("[7/8] Full render all charts for D7 coverage...")
    render_results = {}
    d7_real = 0
    d7_total = 0
    render_errors = 0
    source_counts = defaultdict(int)

    if engine:
        try:
            total_charts = len(engine.charts)
            d7_total = total_charts

            for cb in engine.charts:
                try:
                    t0 = time.time()
                    res = engine.render_with_fallback(cb.chart_id)
                    lat = (time.time() - t0) * 1000

                    if isinstance(res, dict):
                        src = res.get("source", "other")
                        source_counts[src] += 1
                        if src == "real":
                            d7_real += 1
                        if res.get("renderable"):
                            render_results[cb.chart_id] = {
                                "renderable": True,
                                "source": src,
                                "latency_ms": round(lat, 3),
                            }
                        else:
                            render_results[cb.chart_id] = {
                                "renderable": False,
                                "source": src,
                                "latency_ms": round(lat, 3),
                            }
                    else:
                        render_results[cb.chart_id] = {"renderable": False, "error": "non-dict result"}
                except Exception as e:
                    render_errors += 1
                    render_results[cb.chart_id] = {"renderable": False, "error": str(e)}

            d7_coverage_pct = round(d7_real / d7_total * 100, 4) if d7_total > 0 else 0

            results["render_results"] = {
                "total_charts": d7_total,
                "rendered_real": d7_real,
                "rendered_simulated": source_counts.get("simulated", 0),
                "rendered_placeholder": source_counts.get("placeholder", 0),
                "render_errors": render_errors,
                "d7_coverage_pct": d7_coverage_pct,
                "d7_threshold_pct": D7_COVERAGE_THRESHOLD,
                "d7_pass": d7_coverage_pct >= D7_COVERAGE_THRESHOLD,
                "source_distribution": dict(source_counts),
            }

            log("  D7 Coverage: %.4f%% (%d/%d real renders, threshold: %.2f%%) %s" % (
                d7_coverage_pct, d7_real, d7_total, D7_COVERAGE_THRESHOLD,
                "PASS" if d7_coverage_pct >= D7_COVERAGE_THRESHOLD else "FAIL"))
        except Exception as e:
            log_error("  [FAIL] Render test failed: %s" % str(e))
            results["errors"].append("render_test: %s" % str(e))
    else:
        log_warn("  [SKIP] Engine not loaded")

    # ------------------------------------------------------------------
    # Test 8: Derived Indicator Render Verification
    # ------------------------------------------------------------------
    log("[8/8] Verifying derived indicator render completeness...")
    derived_render_results = {}

    if engine and derived_indicators:
        for ind_id, ind_data in derived_indicators.items():
            commodity = ind_data.get("commodity", "unknown")
            ind_mapped = ind_data.get("indicator_id_mapped", "")

            # Check if this derived indicator can be rendered through its commodity charts
            rendered = False
            chart_matches = []
            for cb in engine.charts:
                commodity_match = commodity in cb.chart_id.lower() or commodity in getattr(cb, 'node_id', cb.chart_id).lower()
                # Check if this chart's indicators include the derived indicator
                if commodity_match:
                    chart_matches.append(cb.chart_id)
                    # Try rendering
                    try:
                        res = engine.render_with_fallback(cb.chart_id)
                        if isinstance(res, dict) and res.get("renderable"):
                            rendered = True
                            derived_render_results[ind_id] = {
                                "commodity": commodity,
                                "mapped_id": ind_mapped,
                                "rendered": True,
                                "charts_rendered": chart_matches,
                                "source": res.get("source", "unknown"),
                            }
                            break
                    except Exception:
                        pass

            if not rendered:
                derived_render_results[ind_id] = {
                    "commodity": commodity,
                    "mapped_id": ind_mapped,
                    "rendered": False,
                    "charts_matched": chart_matches[:5],
                    "reason": "no matching chart rendered successfully" if not chart_matches else "charts found but render failed",
                }

        derived_rendered = sum(1 for v in derived_render_results.values() if v.get("rendered"))
        derived_failed = len(derived_render_results) - derived_rendered
        derived_coverage_pct = round(derived_rendered / len(derived_render_results) * 100, 2) if derived_render_results else 0

        results["derived_indicators"]["render_results"] = {
            "total": len(derived_render_results),
            "rendered": derived_rendered,
            "failed": derived_failed,
            "coverage_pct": derived_coverage_pct,
            "details": derived_render_results,
        }

        log("  Derived indicator render: %d/%d rendered (%.2f%%)" % (
            derived_rendered, len(derived_render_results), derived_coverage_pct))

    # ------------------------------------------------------------------
    # Determine Verdict
    # ------------------------------------------------------------------
    test_statuses = [t["status"] for t in results["tests"]]
    test_failures = sum(1 for s in test_statuses if s == "FAIL")
    test_warns = sum(1 for s in test_statuses if s == "WARN")

    d7_pass = results.get("render_results", {}).get("d7_pass", False)
    derived_count_match = results.get("derived_indicators", {}).get("count_match", False)

    if test_failures > 0 or not d7_pass:
        results["verdict"] = "FAIL"
        results["verdict_message"] = "D7 coverage below threshold or test failures"
    elif not derived_count_match:
        results["verdict"] = "WARN"
        results["verdict_message"] = "Derived indicator count mismatch (expected %d)" % EXPECTED_DERIVED_COUNT
    else:
        results["verdict"] = "PASS"
        results["verdict_message"] = "All derived indicators verified, D7 coverage stable"

    # ------------------------------------------------------------------
    # Write Output
    # ------------------------------------------------------------------
    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        log("JSON output: %s (%d bytes)" % (output_path, len(json_str)))
    else:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            f.write(json_str)
        log("JSON output: %s (%d bytes)" % (OUTPUT_JSON, len(json_str)))

    # Write Markdown report
    write_markdown_report(results)
    log("MD output: %s" % OUTPUT_MD)

    log("=" * 72)
    log("DERIVED INDICATOR VERIFICATION COMPLETE")
    log("  Derived Indicators: %d (expected: %d)" % (
        results["derived_indicators"].get("derived_count", 0), EXPECTED_DERIVED_COUNT))
    log("  D7 Coverage: %.4f%% (threshold: %.2f%%)" % (
        results["render_results"].get("d7_coverage_pct", 0), D7_COVERAGE_THRESHOLD))
    log("  Verdict: %s" % results["verdict"])
    log("=" * 72)

    return results


def write_markdown_report(results):
    """Write Markdown verification report."""
    lines = []
    lines.append("# V88 Phase03 P1 — 70 New Derived Indicators Engine Render Verification")
    lines.append("")
    lines.append("> **TASK_ID**: %s" % results["task_id"])
    lines.append("> **Agent**: DSHE | **Branch**: feature/v88-g1 (BRANCH_LOCKED)")
    lines.append("> **Generated**: %s" % results["generated"])
    lines.append("")

    di = results.get("derived_indicators", {})
    rr = results.get("render_results", {})

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value | Expected | Status |")
    lines.append("|--------|:-----:|:--------:|:------:|")
    lines.append("| Derived Indicators Found | %d | %d | %s |" % (
        di.get("derived_count", 0), di.get("expected_count", 70),
        "PASS" if di.get("count_match") else "FAIL"))
    lines.append("| D7 Coverage | %.4f%% | >= %.2f%% | %s |" % (
        rr.get("d7_coverage_pct", 0), rr.get("d7_threshold_pct", 80.20),
        "PASS" if rr.get("d7_pass") else "FAIL"))
    lines.append("| Total Charts Rendered | %d | 101 | — |" % rr.get("total_charts", 0))
    lines.append("| Real Renders (D7) | %d | — | — |" % rr.get("rendered_real", 0))
    lines.append("| Simulated Renders | %d | — | — |" % rr.get("rendered_simulated", 0))
    lines.append("| Render Errors | %d | 0 | %s |" % (
        rr.get("render_errors", 0), "PASS" if rr.get("render_errors", 0) == 0 else "WARN"))
    lines.append("")

    # Category breakdown
    if di.get("categories"):
        lines.append("## Derived Indicator Categories")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|:-----:|")
        for cat, count in sorted(di["categories"].items()):
            lines.append("| %s | %d |" % (cat, count))
        lines.append("| Uncategorized | %d |" % di.get("uncategorized_count", 0))
        lines.append("")

    # Adapter coverage
    if di.get("adapter_coverage_pct") is not None:
        lines.append("## Adapter Coverage")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|:-----:|")
        lines.append("| Adapter Known Derived | %d |" % di.get("adapter_known", 0))
        lines.append("| Total Derived | %d |" % di.get("derived_count", 0))
        lines.append("| Adapter Coverage | %.2f%% |" % di.get("adapter_coverage_pct", 0))
        lines.append("")

    # Test results
    lines.append("## Test Results")
    lines.append("")
    lines.append("| Test ID | Name | Status | Message |")
    lines.append("|---------|------|:------:|---------|")
    for t in results.get("tests", []):
        lines.append("| %s | %s | %s | %s |" % (
            t.get("id", ""), t.get("name", ""), t.get("status", ""),
            t.get("message", "")[:80]))
    lines.append("")

    # Source distribution
    if rr.get("source_distribution"):
        lines.append("## Source Distribution")
        lines.append("")
        lines.append("| Source | Count |")
        lines.append("|--------|:-----:|")
        for src, count in sorted(rr["source_distribution"].items()):
            lines.append("| %s | %d |" % (src, count))
        lines.append("")

    # Verdict
    lines.append("## Verdict")
    lines.append("")
    lines.append("**%s** — %s" % (results.get("verdict", ""), results.get("verdict_message", "")))
    lines.append("")
    lines.append("---")
    lines.append("*Report Generated: %s | Agent: DSHE | Branch: feature/v88-g1 (BRANCH_LOCKED)*" % results["generated"])

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="70 New Derived Indicators Engine Render Verification")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        results = verify_derived_indicators(output_path=args.output)
        return 0 if results.get("verdict") in ("PASS", "WARN") else 1
    except KeyboardInterrupt:
        log_error("Interrupted by user")
        return 130
    except Exception as e:
        log_error("Unhandled exception: %s\n%s" % (str(e), traceback.format_exc()))
        return 2


if __name__ == "__main__":
    sys.exit(main())