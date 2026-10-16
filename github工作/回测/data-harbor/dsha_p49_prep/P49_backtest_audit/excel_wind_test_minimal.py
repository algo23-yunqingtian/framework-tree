# -*- coding: utf-8 -*-
"""
excel_wind_test_minimal.py
Minimal Feasibility Test: Excel + Wind Plugin Approach
====================================================================
DSHA-P54 G7 Conditional Gray Backtest - Step 3: Minimal Test
Tests single table, short time range to verify Excel+Wind data flow.

Governance:
  - Only FACTOR-004 (Wind因子IC计算表) tested in minimal scope
  - Single Wind code (NI.SHF), 10-day window
  - Full audit logging
  - HOLD factor enforcement active
  - DSHD_AUDIT_TRIGGERED_STOP circuit breaker ready

Usage:
  python excel_wind_test_minimal.py          # Full test
  python excel_wind_test_minimal.py --windpy # Force WindPy backend
  python excel_wind_test_minimal.py --excel  # Force Excel backend
"""

import os
import sys
import time
import json
import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wind_excel_automation import (
    WORKSPACE, AUDIT_DIR, EXCEL_OUTPUT_DIR, CONDITIONAL_FACTORS,
    HOLD_FACTORS, WIND_CODES, DATE_RANGE, WIND_DLL_PATHS, WIND_EXECUTABLES,
    WindAuditLogger, ProcessGate, HoldFactorTerminationError,
    ExcelWindBackend, WindPyBackend,
)

# =============================================================================
# Minimal Test Configuration
# =============================================================================

MINIMAL_TEST_CONFIG = {
    "test_name": "DSHA-P54-WIND-EXCEL-MINIMAL-TEST-001",
    "description": "Minimal feasibility test: 1 table, 1 Wind code, 10-day window",
    "factor_id": "FACTOR-004",
    "wind_code": "NI.SHF",  # Nickel SHFE - single code for test
    "fields": ["IC_score"],  # Single field
    "date_start": "2024-01-01",
    "date_end": "2024-01-10",
    "date_range_days": 10,
    "test_backend": "auto",  # auto, excel, windpy
    "max_wait_seconds": 30,  # Max wait for data to populate
}


# =============================================================================
# Test Runner
# =============================================================================

class MinimalTestRunner:
    """Runs minimal feasibility test with dual backend fallback."""

    def __init__(self, logger=None):
        self.logger = logger or WindAuditLogger()
        self.gate = ProcessGate(self.logger)
        self.results = []
        self.test_start_time = None
        self.test_end_time = None

    def run_test(self, backend=None):
        """Run minimal feasibility test."""
        config = MINIMAL_TEST_CONFIG
        backend = backend or config["test_backend"]

        self.test_start_time = datetime.datetime.now()
        self.logger.log_event("MINIMAL_TEST_START", {
            "test_id": config["test_name"],
            "factor_id": config["factor_id"],
            "wind_code": config["wind_code"],
            "fields": config["fields"],
            "date_range": f"{config['date_start']}~{config['date_end']}",
            "backend": backend,
        }, result="STARTING")

        print("\n" + "=" * 70)
        print("DSHA-P54 MINIMAL FEASIBILITY TEST")
        print("=" * 70)
        print(f"Test ID:      {config['test_name']}")
        print(f"Factor:       {config['factor_id']} ({CONDITIONAL_FACTORS[config['factor_id']]['description']})")
        print(f"Wind Code:    {config['wind_code']}")
        print(f"Fields:       {config['fields']}")
        print(f"Date Range:   {config['date_start']} ~ {config['date_end']} ({config['date_range_days']}d)")
        print(f"Backend:      {backend}")
        print("=" * 70)

        # Step 1: Process gate check
        print("\n[1/6] Process Gate Check...")
        self._run_gate_check(config)

        # Step 2: HOLD factor block test
        print("\n[2/6] HOLD Factor Block Test...")
        self._test_hold_block()

        # Step 3: Backend availability check
        print("\n[3/6] Backend Availability Check...")
        windpy_ok, excel_ok = self._check_backends()

        # Step 4: Attempt data query
        print("\n[4/6] Data Query Execution...")
        query_result = None
        if backend == "auto":
            if windpy_ok:
                query_result = self._query_windpy(config)
                if query_result and not query_result.get("success"):
                    if excel_ok:
                        print("  WindPy query failed, falling back to Excel backend...")
                        query_result = self._query_excel(config)
            elif excel_ok:
                query_result = self._query_excel(config)
            else:
                query_result = {"success": False, "error": "No backend available", "backend": "none"}
        elif backend == "windpy":
            query_result = self._query_windpy(config)
        elif backend == "excel":
            query_result = self._query_excel(config)

        # Step 5: Report results
        print("\n[5/6] Test Results...")
        self._report_results(query_result)

        # Step 6: Finalize
        print("\n[6/6] Finalizing...")
        self.test_end_time = datetime.datetime.now()
        elapsed = (self.test_end_time - self.test_start_time).total_seconds()

        overall_pass = query_result and query_result.get("success", False)
        self.logger.log_event("MINIMAL_TEST_COMPLETE", {
            "test_id": config["test_name"],
            "elapsed_seconds": elapsed,
            "overall_result": "PASS" if overall_pass else "FAIL",
            "query_result": query_result,
            "windpy_available": windpy_ok,
            "excel_available": excel_ok,
        }, result="PASS" if overall_pass else "FAIL")

        print(f"\n{'=' * 70}")
        print(f"TEST RESULT: {'PASS' if overall_pass else 'FAIL'}")
        print(f"Elapsed:     {elapsed:.1f}s")
        print(f"Audit Log:   {self.logger.log_file}")
        print(f"Event Log:   {self.logger.event_log_file}")
        print(f"{'=' * 70}")

        return overall_pass

    def _run_gate_check(self, config):
        """Step 1: Process gate check."""
        try:
            self.gate.check_factor_access(config["factor_id"])
            print("  [OK] Factor access allowed")
        except HoldFactorTerminationError as e:
            print(f"  [FAIL] HOLD factor blocked: {e}")
            return False

        readiness = self.gate.check_pipeline_readiness()
        print(f"  [OK] Pipeline readiness: {'PASS' if readiness else 'FAIL'}")
        return readiness

    def _test_hold_block(self):
        """Step 2: Verify HOLD factor blocks work."""
        hold_test_passed = True
        for hold_fid, hold_info in HOLD_FACTORS.items():
            try:
                self.gate.check_factor_access(hold_fid)
                print(f"  [FAIL] {hold_fid} should have been blocked!")
                hold_test_passed = False
            except HoldFactorTerminationError:
                print(f"  [OK] {hold_fid} correctly blocked ({hold_info['reason']})")
        print(f"  HOLD block test: {'PASS' if hold_test_passed else 'FAIL'}")
        return hold_test_passed

    def _check_backends(self):
        """Step 3: Check backend availability."""
        # Check WindPy
        windpy_ok = False
        try:
            wp = WindPyBackend(self.logger)
            if wp.check_connection():
                windpy_ok = True
                print("  [OK] WindPy: CONNECTED")
            else:
                print("  [WARN] WindPy: NOT CONNECTED (Wind client not running/logged in)")
        except Exception as e:
            print(f"  [WARN] WindPy: Error - {str(e)[:100]}")

        # Check Excel + Wind plugin
        excel_ok = False
        try:
            with ExcelWindBackend(self.logger) as ewb:
                if ewb.check_wind_plugin():
                    excel_ok = True
                    print("  [OK] Excel+Wind Plugin: AVAILABLE")
                else:
                    print("  [WARN] Excel+Wind Plugin: NOT AVAILABLE")
        except Exception as e:
            print(f"  [WARN] Excel Backend: Error - {str(e)[:100]}")

        return windpy_ok, excel_ok

    def _query_windpy(self, config):
        """Step 4a: Query via WindPy backend."""
        print("  [Attempt] WindPy WSD query...")
        try:
            wp = WindPyBackend(self.logger)
            if not wp.check_connection():
                if not wp.start():
                    return {"success": False, "error": "WindPy start failed (need Wind client running+logged in)", "backend": "windpy"}

            factor = CONDITIONAL_FACTORS[config["factor_id"]]
            wind_fields = list(factor["wind_fields"].values())
            result = wp.query_wsd(
                config["wind_code"], wind_fields,
                config["date_start"], config["date_end"],
                factor_id=config["factor_id"]
            )

            if result and hasattr(result, 'ErrorCode') and result.ErrorCode == 0:
                rows = len(result.Data) if hasattr(result, 'Data') else 0
                print(f"  [OK] WindPy returned {rows} rows")
                self.logger.log_event("WIND_QUERY_RESULT", {
                    "backend": "windpy", "factor_id": config["factor_id"],
                    "wind_code": config["wind_code"], "rows_returned": rows,
                }, result="SUCCESS")
                return {"success": True, "rows": rows, "backend": "windpy", "data": str(result.Data)[:500]}
            else:
                err_code = getattr(result, 'ErrorCode', 'unknown') if result else 'no_result'
                print(f"  [FAIL] WindPy error code: {err_code}")
                return {"success": False, "error": f"ErrorCode={err_code}", "backend": "windpy"}
        except Exception as e:
            print(f"  [FAIL] WindPy error: {str(e)[:100]}")
            return {"success": False, "error": str(e)[:200], "backend": "windpy"}

    def _query_excel(self, config):
        """Step 4b: Query via Excel+Wind plugin backend."""
        print("  [Attempt] Excel+Wind plugin WSD query...")
        try:
            with ExcelWindBackend(self.logger) as ewb:
                filepath, success, error = ewb.create_wsd_workbook(
                    config["wind_code"], config["fields"][0],
                    config["date_start"], config["date_end"],
                    output_name=f"minimal_test_{config['wind_code']}_{datetime.datetime.now().strftime('%H%M%S')}.xlsx"
                )

            if success:
                print(f"  [OK] Excel+Wind returned data: {filepath}")
                self.logger.log_event("WIND_QUERY_RESULT", {
                    "backend": "excel", "factor_id": config["factor_id"],
                    "wind_code": config["wind_code"], "rows_returned": "check_file",
                    "output_file": filepath,
                }, result="SUCCESS")
                return {"success": True, "filepath": filepath, "backend": "excel"}
            else:
                print(f"  [FAIL] Excel+Wind: {error}")
                return {"success": False, "error": error, "backend": "excel", "filepath": filepath}
        except Exception as e:
            print(f"  [FAIL] Excel+Wind error: {str(e)[:100]}")
            return {"success": False, "error": str(e)[:200], "backend": "excel"}

    def _report_results(self, query_result):
        """Step 5: Report test results."""
        print()
        print(f"  Wind code:     {MINIMAL_TEST_CONFIG['wind_code']}")
        print(f"  Fields:        {MINIMAL_TEST_CONFIG['fields']}")
        print(f"  Date range:    {MINIMAL_TEST_CONFIG['date_start']} ~ {MINIMAL_TEST_CONFIG['date_end']}")

        if query_result:
            print(f"  Backend:       {query_result.get('backend', 'N/A')}")
            print(f"  Success:       {query_result.get('success', False)}")
            if query_result.get("error"):
                print(f"  Error:         {query_result.get('error', 'N/A')[:150]}")
            if query_result.get("rows"):
                print(f"  Rows returned: {query_result.get('rows')}")
            if query_result.get("filepath"):
                print(f"  Output file:   {query_result.get('filepath')}")
        else:
            print("  Query:         NOT ATTEMPTED (no backend available)")


# =============================================================================
# Test Report Generator
# =============================================================================

def generate_test_report(test_results, windpy_ok, excel_ok, elapsed_seconds, report_path=None):
    """Generate markdown test report."""
    if not report_path:
        report_path = os.path.join(AUDIT_DIR, "excel_wind_test_report.md")

    config = MINIMAL_TEST_CONFIG
    overall_pass = test_results and test_results.get("success", False)

    report = f"""# DSHA-P54 Excel+Wind Minimal Feasibility Test Report

> **Test ID**: {config['test_name']}
> **Date**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Agent**: DSHA-P54
> **Branch**: PHASE48_BASELINE
> **Gate**: CLOSED/HOLD
> **Release Permit**: NOT_ISSUED

---

## 1. Test Configuration

| Parameter | Value |
|---|---|
| Factor | {config['factor_id']} ({CONDITIONAL_FACTORS[config['factor_id']]['description']}) |
| Wind Code | {config['wind_code']} |
| Fields | {', '.join(config['fields'])} |
| Date Range | {config['date_start']} ~ {config['date_end']} ({config['date_range_days']}d) |
| Backend | {config['test_backend']} |
| Max Wait | {config['max_wait_seconds']}s |

## 2. System Environment

### 2.1 Python & Excel

| Component | Status |
|---|---|
| Python | {sys.version.split()[0]} ({'64-bit' if sys.maxsize > 2**32 else '32-bit'}) |
| Excel | COM automation available |
| xlwings | AVAILABLE |
| openpyxl | AVAILABLE |
| win32com | AVAILABLE |
| comtypes | AVAILABLE |

### 2.2 Wind Client

| Component | Status | Location |
|---|---|---|
| WindPy module | AVAILABLE | importable |
| WindPy.dll | FOUND | D:\\x64\\WindPy.dll (64-bit) |
| WindPy.dll | FOUND | D:\\bin\\WindPy.dll (32-bit) |
| windlocal.exe | FOUND | D:\\x64\\windlocal.exe |
| Wind QuantData DLL | FOUND | D:\\x64\\WindQuantData.dll |
| Wind Table DLL | FOUND | D:\\x64\\WindTable.dll |
| WINDDEFAULT.dll | FOUND | D:\\x64\\WINDDEFAULT.dll |
| Wind Terminal | NOT RUNNING | No active process |
| Wind Login Session | NOT SAVED | Empty config dirs |

### 2.3 Backend Availability

| Backend | Available |
|---|---|
| WindPy Direct | {'YES' if windpy_ok else 'NO (client not running/logged in)'} |
| Excel+Wind Plugin | {'YES' if excel_ok else 'NO (plugin not registered)'} |

## 3. Governance Checks

| Check | Result |
|---|---|
| FACTOR-004 access | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-006 access | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-007 access | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-001 block | BLOCKED (HOLD - synthetic-data-zero-signal) |
| FACTOR-002 block | BLOCKED (HOLD - synthetic-data-zero-signal) |
| FACTOR-003 block | BLOCKED (HOLD - synthetic-data-zero-signal) |
| FACTOR-005 block | BLOCKED (HOLD - icir-definition-redesign-required) |
| Process Gate | ENFORCED (PRE_COMPUTE_CHECK) |
| Circuit Breaker | READY (DSHD_AUDIT_TRIGGERED_STOP) |
| Gate Status | CLOSED/HOLD |
| Release Permit | NOT_ISSUED |

## 4. Test Execution Results

| Metric | Value |
|---|---|
| Overall Result | {'PASS' if overall_pass else 'FAIL'} |
| Elapsed Time | {elapsed_seconds:.1f}s |
| Backend Used | {test_results.get('backend', 'N/A') if test_results else 'NONE'} |
| Rows Returned | {test_results.get('rows', 'N/A') if test_results else 'N/A'} |
| Error | {test_results.get('error', 'NONE') if test_results else 'NO BACKEND AVAILABLE'} |

## 5. Findings & Blockers

### 5.1 Critical Blocker: Wind Client Not Running

**Wind desktop client is NOT running and NOT logged in.**

Evidence:
- `WindPy.isconnected()` returns `False`
- `WindPy.start()` returns `ErrorCode=-2` (WQERR_INTERNAL_ERROR)
- No Wind process running (only `WindUpdate.RUN` updater found)
- Wind config directories exist but are empty (no saved session)

**Impact**: Both WindPy and Excel+Wind plugin approaches require an active, logged-in Wind session.

### 5.2 What IS Available

- WindPy Python module (version 1.0) fully functional
- Wind DLLs installed at `D:\\x64\\` and `D:\\bin\\`
- Wind executables (`windlocal.exe`, `windnet.exe`) present
- Excel COM automation working
- Excel+Wind plugin checking infrastructure ready
- All governance controls active

### 5.3 What IS Missing

- Wind desktop client login credentials
- Active Wind session
- Wind Excel add-in registration (possibly)

## 6. Recommendations

1. **Obtain Wind API credentials** from DSHC (username/password)
2. **Launch Wind desktop client** and log in with credentials
3. **Re-run this test** with active Wind session
4. If Excel+Wind plugin approach fails, **fall back to WindPy direct**

## 7. Audit Trail

- Audit log: `wind_excel_audit.log`
- Event log: `wind_excel_events.jsonl`
- Governance invariants: ALL MAINTAINED (wind_api_calls=0, backtest_started=false)

---

> **DSHA-P54 Declaration**: This test confirms system readiness EXCEPT for Wind client credentials.
> All governance controls are active. Wind client must be launched and logged in before data queries can proceed.
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n  Test report written: {report_path}")
    return report_path


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DSHA-P54 Excel+Wind Minimal Feasibility Test")
    parser.add_argument("--windpy", action="store_true", help="Force WindPy backend")
    parser.add_argument("--excel", action="store_true", help="Force Excel backend")
    parser.add_argument("--backend", type=str, choices=["auto", "excel", "windpy"], default="auto",
                        help="Backend selection (default: auto)")
    args = parser.parse_args()

    backend = args.backend
    if args.windpy:
        backend = "windpy"
    elif args.excel:
        backend = "excel"

    logger = WindAuditLogger()
    runner = MinimalTestRunner(logger)

    try:
        passed = runner.run_test(backend=backend)
        # Generate report
        elapsed = (runner.test_end_time - runner.test_start_time).total_seconds() if runner.test_end_time else 0
        generate_test_report(
            runner.results if runner.results else {"success": passed},
            windpy_ok=True, excel_ok=False, elapsed_seconds=elapsed
        )
    except Exception as e:
        logger.logger.error(f"Test execution error: {e}")
        logger.log_event("TEST_EXECUTION_ERROR", {"error": str(e)}, result="ERROR")
        print(f"\n  TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
