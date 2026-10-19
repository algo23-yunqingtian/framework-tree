#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FACTOR_EXTRACT_V1 — Abnormal Test Suite
=========================================

Three abnormal scenarios for V1 regression testing:

  TC-001: Date misalignment  — CU.SHF has extra dates not in ZN.SHF
  TC-002: Illegal instrument — FOO.SHF (not in whitelist, not blacklisted)
  TC-003: Empty indicators    — CU.SHF missing SETTLE (required indicator)

Expected outcomes:
  TC-001: Script completes, reports date misalignment warnings
  TC-002: Script completes, processes FOO.SHF (no whitelist enforcement at code level)
  TC-003: Script completes, SETTLE column has NaN, spread_cs/spread_pct = NaN

Usage:
  python artifacts/skill_lib/factor_v1/tests/run_abnormal_tests.py

Author: DSHC-MAINT-01
Date:   2026-10-19
"""

from __future__ import annotations

import os
import sys
import tempfile
import hashlib
from pathlib import Path

# Add parent directory to path for import
SCRIPT_DIR = Path(__file__).parent.resolve()
V1_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(V1_DIR))

from factor_extract_v1 import extract_factors, BLACKLIST

# ============================================================================
# Test Case Definitions
# ============================================================================

TEST_CASES = [
    {
        "id": "TC-001",
        "name": "date_misalignment",
        "description": "CU.SHF has dates not present for ZN.SHF; script should complete with misalignment warnings",
        "expected_result": "WARN_MISALIGNMENT",
        "data_csv": "tc001_date_misalignment.csv",
    },
    {
        "id": "TC-002",
        "name": "illegal_instrument",
        "description": "FOO.SHF is not in whitelist and not blacklisted; script processes it silently",
        "expected_result": "COMPLETES_WITH_UNKNOWN_SYMBOL",
        "data_csv": "tc002_illegal_instrument.csv",
    },
    {
        "id": "TC-003",
        "name": "empty_required_indicator",
        "description": "CU.SHF missing SETTLE indicator; spread factors produce NaN",
        "expected_result": "COMPLETES_WITH_NAN_FACTORS",
        "data_csv": "tc003_missing_settle.csv",
    },
]


def generate_tc001_data(outdir: Path) -> str:
    """TC-001: Date misalignment — CU.SHF has 3 extra dates ZN.SHF lacks."""
    rows = [
        # ZN.SHF: 2025-01-02, 2025-01-03, 2025-01-06
        "2025-01-02,ZN.SHF,CLOSE,30000,SHFE",
        "2025-01-02,ZN.SHF,SETTLE,29980,SHFE",
        "2025-01-02,ZN.SHF,OI,50000,SHFE",
        "2025-01-03,ZN.SHF,CLOSE,30100,SHFE",
        "2025-01-03,ZN.SHF,SETTLE,30080,SHFE",
        "2025-01-03,ZN.SHF,OI,51000,SHFE",
        "2025-01-06,ZN.SHF,CLOSE,30200,SHFE",
        "2025-01-06,ZN.SHF,SETTLE,30180,SHFE",
        "2025-01-06,ZN.SHF,OI,52000,SHFE",
        # CU.SHF: 2025-01-02, 2025-01-03, 2025-01-06 + 3 extra (Jan 7, 8, 9)
        "2025-01-02,CU.SHF,CLOSE,78000,SHFE",
        "2025-01-02,CU.SHF,SETTLE,77980,SHFE",
        "2025-01-02,CU.SHF,OI,150000,SHFE",
        "2025-01-03,CU.SHF,CLOSE,78100,SHFE",
        "2025-01-03,CU.SHF,SETTLE,78080,SHFE",
        "2025-01-03,CU.SHF,OI,151000,SHFE",
        "2025-01-06,CU.SHF,CLOSE,78200,SHFE",
        "2025-01-06,CU.SHF,SETTLE,78180,SHFE",
        "2025-01-06,CU.SHF,OI,152000,SHFE",
        "2025-01-07,CU.SHF,CLOSE,78300,SHFE",
        "2025-01-07,CU.SHF,SETTLE,78280,SHFE",
        "2025-01-07,CU.SHF,OI,153000,SHFE",
        "2025-01-08,CU.SHF,CLOSE,78400,SHFE",
        "2025-01-08,CU.SHF,SETTLE,78380,SHFE",
        "2025-01-08,CU.SHF,OI,154000,SHFE",
        "2025-01-09,CU.SHF,CLOSE,78500,SHFE",
        "2025-01-09,CU.SHF,SETTLE,78480,SHFE",
        "2025-01-09,CU.SHF,OI,155000,SHFE",
    ]
    csv_path = outdir / "tc001_date_misalignment.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("date,symbol,indicator,value,source\n")
        for row in rows:
            f.write(row + "\n")
    return str(csv_path)


def generate_tc002_data(outdir: Path) -> str:
    """TC-002: Illegal instrument — FOO.SHF is not blacklisted or whitelisted."""
    rows = [
        "2025-01-02,CU.SHF,CLOSE,78000,SHFE",
        "2025-01-02,CU.SHF,SETTLE,77980,SHFE",
        "2025-01-02,CU.SHF,OI,150000,SHFE",
        "2025-01-03,CU.SHF,CLOSE,78100,SHFE",
        "2025-01-03,CU.SHF,SETTLE,78080,SHFE",
        "2025-01-03,CU.SHF,OI,151000,SHFE",
        # FOO.SHF — unknown, not in blacklist
        "2025-01-02,FOO.SHF,CLOSE,1000,SHFE",
        "2025-01-02,FOO.SHF,SETTLE,998,SHFE",
        "2025-01-02,FOO.SHF,OI,1000,SHFE",
        "2025-01-03,FOO.SHF,CLOSE,1010,SHFE",
        "2025-01-03,FOO.SHF,SETTLE,1008,SHFE",
        "2025-01-03,FOO.SHF,OI,1010,SHFE",
    ]
    csv_path = outdir / "tc002_illegal_instrument.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("date,symbol,indicator,value,source\n")
        for row in rows:
            f.write(row + "\n")
    return str(csv_path)


def generate_tc003_data(outdir: Path) -> str:
    """TC-003: Missing SETTLE — CU.SHF has CLOSE and OI but no SETTLE."""
    rows = [
        "2025-01-02,CU.SHF,CLOSE,78000,SHFE",
        "2025-01-02,CU.SHF,OI,150000,SHFE",
        "2025-01-03,CU.SHF,CLOSE,78100,SHFE",
        "2025-01-03,CU.SHF,OI,151000,SHFE",
        "2025-01-06,CU.SHF,CLOSE,78200,SHFE",
        "2025-01-06,CU.SHF,OI,152000,SHFE",
    ]
    csv_path = outdir / "tc003_missing_settle.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("date,symbol,indicator,value,source\n")
        for row in rows:
            f.write(row + "\n")
    return str(csv_path)


def run_single_test(tc: dict, data_dir: Path, outdir: Path) -> dict:
    """Run a single test case and collect results."""
    import pandas as pd

    csv_path = data_dir / tc["data_csv"]
    test_outdir = outdir / tc["id"]
    test_outdir.mkdir(parents=True, exist_ok=True)

    result = {
        "test_id": tc["id"],
        "test_name": tc["name"],
        "description": tc["description"],
        "expected_result": tc["expected_result"],
        "actual_result": None,
        "exit_code": None,
        "row_count": None,
        "factor_count": None,
        "warning_count": None,
        "error": None,
        "output_files": [],
    }

    try:
        factor_df, report, paths = extract_factors(
            csv_path=str(csv_path),
            outdir=str(test_outdir),
        )

        result["exit_code"] = 0
        result["row_count"] = len(factor_df)

        # Check factor columns exist
        factor_cols = [
            "spread_cs", "oi_level", "oi_change_1d",
            "oi_change_rate_7d", "spread_pct",
            "contract_switch_flag", "momentum_20d",
        ]
        present_factors = [c for c in factor_cols if c in factor_df.columns]
        result["factor_count"] = len(present_factors)

        # Check warnings
        misalignment = report.date_misalignment
        pk_dupes = report.pk_duplicates
        null_vals = report.null_values
        result["warning_count"] = (
            len(misalignment) + len(pk_dupes) + len(null_vals)
        )

        # Determine actual result
        if misalignment and not tc["id"] == "TC-001":
            result["actual_result"] = "UNEXPECTED_MISALIGNMENT"
        elif tc["id"] == "TC-001" and misalignment:
            result["actual_result"] = "WARN_MISALIGNMENT"
        elif tc["id"] == "TC-002":
            # Check if FOO.SHF was processed
            symbols_in_output = set(factor_df["symbol"].unique())
            if "FOO.SHF" in symbols_in_output:
                result["actual_result"] = "COMPLETES_WITH_UNKNOWN_SYMBOL"
            else:
                result["actual_result"] = "FOO_SHF_MISSING"
        elif tc["id"] == "TC-003":
            # Check if spread factors are NaN
            nan_spread = factor_df["spread_cs"].isna().any()
            nan_spread_pct = factor_df["spread_pct"].isna().any()
            if nan_spread and nan_spread_pct:
                result["actual_result"] = "COMPLETES_WITH_NAN_FACTORS"
            else:
                result["actual_result"] = "UNEXPECTED_NON_NAN_FACTORS"
        else:
            result["actual_result"] = "COMPLETED"

        # Check output files
        result["output_files"] = [
            str(csv_path),
            str(test_outdir / "factors_output.csv"),
            str(test_outdir / "factors_metadata.json"),
        ]

    except Exception as e:
        result["exit_code"] = 99
        result["error"] = str(e)
        result["actual_result"] = "EXCEPTION"

    # Calculate SHA256 of output
    output_csv = test_outdir / "factors_output.csv"
    if output_csv.exists():
        with open(output_csv, "rb") as f:
            result["output_sha256"] = hashlib.sha256(f.read()).hexdigest().upper()

    return result


def run_all_tests() -> list:
    """Run all test cases and return results."""
    # Create temp directory for test data
    with tempfile.TemporaryDirectory(prefix="fev1_tests_") as tmp:
        data_dir = Path(tmp) / "data"
        outdir = Path(tmp) / "output"
        data_dir.mkdir(parents=True, exist_ok=True)
        outdir.mkdir(parents=True, exist_ok=True)

        # Generate test data
        print("=" * 60)
        print("Generating test data...")
        for tc in TEST_CASES:
            if tc["id"] == "TC-001":
                generate_tc001_data(data_dir)
            elif tc["id"] == "TC-002":
                generate_tc002_data(data_dir)
            elif tc["id"] == "TC-003":
                generate_tc003_data(data_dir)
        print("=" * 60)

        # Run tests
        results = []
        for tc in TEST_CASES:
            print(f"\nRunning {tc['id']}: {tc['name']}")
            print(f"  Description: {tc['description']}")
            result = run_single_test(tc, data_dir, outdir)
            results.append(result)

            passed = result["actual_result"] == tc["expected_result"]
            status = "PASS" if passed else "FAIL"
            print(f"  Expected: {tc['expected_result']}")
            print(f"  Actual:   {result['actual_result']}")
            print(f"  Exit:     {result['exit_code']}")
            print(f"  Rows:     {result['row_count']}")
            print(f"  Factors:  {result['factor_count']}")
            print(f"  Status:   [{status}]")
            if result["error"]:
                print(f"  Error:    {result['error']}")

        return results


def main() -> int:
    """Run all abnormal tests."""
    print("=" * 60)
    print("FACTOR_EXTRACT_V1 — Abnormal Test Suite")
    print("DSHC-MAINT-01 | 2026-10-19")
    print("=" * 60)

    results = run_all_tests()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r["actual_result"] == r["expected_result"])
    failed = len(results) - passed
    print(f"  Total:  {len(results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print("=" * 60)

    # Write results JSON
    import json
    results_path = SCRIPT_DIR / "abnormal_test_results.json"
    results_output = {
        "test_suite": "FACTOR_EXTRACT_V1_ABNORMAL",
        "version": "1.0.0",
        "test_cases": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
        },
        "note": "V1 frozen. These tests validate V1 behavior with abnormal inputs.",
    }
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written: {results_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())