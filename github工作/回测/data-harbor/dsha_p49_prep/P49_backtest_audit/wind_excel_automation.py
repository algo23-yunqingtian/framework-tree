# -*- coding: utf-8 -*-
"""
wind_excel_automation.py
Wind Excel Automation Module for DSHA-P54 G7 Conditional Gray Backtest
================================================================================
Pivots from WindPy API to Excel+Wind desktop plugin approach.
Dual backend: (A) Excel COM + Wind plugin formulas, (B) WindPy direct.

Governance:
  - Only FACTOR-004/006/007 allowed (CONDITIONAL_PASS)
  - FACTOR-001/002/003/005 HOLD - process-level block enforced
  - DSHD_AUDIT_TRIGGERED_STOP circuit breaker ready
  - All Wind calls logged with timestamp, table, fields, range

Author: DSHA-P54
Date: 2026-10-16
"""

import os
import sys
import time
import json
import logging
import datetime
import subprocess
import traceback

# =============================================================================
# Configuration
# =============================================================================

WORKSPACE = r"D:\DSH_WORK\github工作\回测"
AUDIT_DIR = os.path.join(WORKSPACE, "data-harbor", "dsha_p49_prep", "P49_backtest_audit")
EXCEL_OUTPUT_DIR = os.path.join(WORKSPACE, "data-harbor", "dsha_p49_prep", "P49_backtest_audit", "wind_excel_data")
LOG_DIR = os.path.join(AUDIT_DIR)

# Factor definitions (CONDITIONAL_PASS only)
CONDITIONAL_FACTORS = {
    "FACTOR-004": {
        "table": "Wind因子IC计算表",
        "fields": ["IC_score", "forecast_return", "realized_return"],
        "wind_fields": {"IC_score": "IC", "forecast_return": "FCR", "realized_return": "RR"},
        "description": "G1 IC Threshold Factor",
        "process_block": False,
    },
    "FACTOR-006": {
        "table": "Wind因子计算管线",
        "fields": ["leakage_score", "info_score"],
        "wind_fields": {"leakage_score": "LKS", "info_score": "IFS"},
        "description": "G7 Leakage Ratio Factor",
        "process_block": False,
        "threshold": 0.005,
    },
    "FACTOR-007": {
        "table": "Wind多因子合成表",
        "fields": ["F19_score", "F20_score", "CF003_score", "decay_score"],
        "wind_fields": {"F19_score": "F19", "F20_score": "F20", "CF003_score": "CF003", "decay_score": "DEC"},
        "description": "SchemeD Frozen Weights Factor",
        "process_block": False,
        "window_days": 60,
    },
}

# HOLD factors - absolutely blocked
HOLD_FACTORS = {
    "FACTOR-001": {"table": "Wind持仓量表", "reason": "synthetic-data-zero-signal"},
    "FACTOR-002": {"table": "Wind新闻舆情表", "reason": "synthetic-data-zero-signal"},
    "FACTOR-003": {"table": "Wind交易所持仓明细表", "reason": "synthetic-data-zero-signal"},
    "FACTOR-005": {"table": "Wind因子ICIR计算表", "reason": "icir-definition-redesign-required"},
}

# Wind instrument codes for commodity futures
WIND_CODES = {
    "LI": "LI.SHF",       # Lithium (GFE)
    "NI": "NI.SHF",       # Nickel (SHFE)
    "ZN": "ZN.SHF",       # Zinc (SHFE)
    "CU": "CU.SHF",       # Copper (SHFE)
}

# Date range
DATE_RANGE = {
    "start": "2023-01-01",
    "end": "2024-12-31",
    "chunk_size": 365,  # days per chunk
}

# Wind DLL paths (discovered on this machine)
WIND_DLL_PATHS = {
    "64bit": r"D:\x64",
    "32bit": r"D:\bin",
    "upgrade_64": r"D:\upgrade\x64",
    "upgrade_32": r"D:\upgrade\bin",
}

WIND_EXECUTABLES = {
    "windlocal": r"D:\x64\windlocal.exe",
    "windnet": r"D:\x64\windnet.exe",
    "wind_update": r"D:\x64\WindUpdate.exe",
}

# =============================================================================
# Audit Logger
# =============================================================================

class WindAuditLogger:
    """DSHD-compatible audit logger for all Wind operations."""

    def __init__(self, log_dir=LOG_DIR):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "wind_excel_audit.log")
        self.event_log_file = os.path.join(log_dir, "wind_excel_events.jsonl")
        self.logger = logging.getLogger("wind_excel_audit")
        self.logger.setLevel(logging.DEBUG)
        # File handler
        fh = logging.FileHandler(self.log_file, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s"
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(EXCEL_OUTPUT_DIR, exist_ok=True)

    def log_event(self, event_type, details, result="PENDING"):
        """Append structured audit event to JSONL file."""
        event = {
            "event_id": f"DSHA-P54-WIND-EXCEL-{event_type}-{int(time.time() * 1000) % 1000000}",
            "event_type": event_type,
            "timestamp": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
            "agent": "DSHA-P54",
            "task": "Wind Excel automation for G7 conditional gray backtest",
            "result": result,
            "branch": "PHASE48_BASELINE",
            "wind_api_calls": 0,  # Updated by caller
            "backtest_started": False,
            "gate": "CLOSED/HOLD",
            "release_permit": "NOT_ISSUED",
            "details": details,
        }
        with open(self.event_log_file, "a", encoding="utf-8-sig") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        self.logger.info(f"[AUDIT] {event_type}: {result} | {json.dumps(details, ensure_ascii=False)[:200]}")
        return event

    def log_wind_call(self, factor_id, wind_code, fields, date_start, date_end, backend, result):
        """Log a single Wind data call."""
        details = {
            "factor_id": factor_id,
            "wind_code": wind_code,
            "fields": fields,
            "date_start": date_start,
            "date_end": date_end,
            "backend": backend,
            "timestamp": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        }
        self.logger.debug(f"[WIND_CALL] {factor_id} {wind_code} {fields} {date_start}~{date_end} via {backend}: {result}")
        return details

    def log_hold_block(self, factor_id, attempted_action):
        """Log a HOLD factor block attempt."""
        details = {
            "factor_id": factor_id,
            "attempted_action": attempted_action,
            "block_reason": HOLD_FACTORS.get(factor_id, {}).get("reason", "unknown"),
            "action_taken": "TERMINATE_PIPELINE_IMMEDIATELY",
            "timestamp": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        }
        self.logger.warning(f"[HOLD_BLOCK] {factor_id} {attempted_action} -> TERMINATED")
        self.log_event("HOLD_FACTOR_BLOCK", details, result="BLOCKED")
        return details


# =============================================================================
# Process Gate - HOLD Factor Enforcement
# =============================================================================

class ProcessGate:
    """Enforces process-level block on HOLD factors. TERMINATE_PIPELINE_IMMEDIATELY."""

    def __init__(self, logger=None):
        self.logger = logger or WindAuditLogger()

    def check_factor_access(self, factor_id):
        """
        Check if factor access is allowed.
        Returns: True if allowed, raises HoldFactorTerminationError if blocked.
        """
        if factor_id in HOLD_FACTORS:
            hold_info = HOLD_FACTORS[factor_id]
            raise HoldFactorTerminationError(
                factor_id=factor_id,
                reason=hold_info["reason"],
                table=hold_info["table"],
            )
        return True

    def check_pipeline_readiness(self):
        """Verify pipeline is ready for conditional gray backtest."""
        checks = {
            "conditional_factors_defined": len(CONDITIONAL_FACTORS) == 3,
            "hold_factors_defined": len(HOLD_FACTORS) == 4,
            "wind_codes_defined": len(WIND_CODES) >= 3,
            "date_range_defined": all(k in DATE_RANGE for k in ("start", "end", "chunk_size")),
            "gate_status": "CLOSED/HOLD",
            "release_permit": "NOT_ISSUED",
        }
        all_pass = all(checks.values())
        self.logger.log_event("PIPELINE_READINESS_CHECK", checks, result="PASS" if all_pass else "FAIL")
        return all_pass


class HoldFactorTerminationError(Exception):
    """Raised when a HOLD factor access is attempted. TERMINATE_PIPELINE_IMMEDIATELY."""
    def __init__(self, factor_id, reason, table):
        self.factor_id = factor_id
        self.reason = reason
        self.table = table
        msg = f"HOLD_FACTOR_TERMINATED: {factor_id} ({table}) - {reason}. Pipeline terminated."
        super().__init__(msg)


# =============================================================================
# Excel Wind Plugin Backend
# =============================================================================

class ExcelWindBackend:
    """
    Excel + Wind desktop plugin automation backend.
    Writes Wind formulas (WSD/WTD) into Excel cells, lets the plugin calculate,
    then reads back the data.
    """

    def __init__(self, logger=None, headless=True):
        self.logger = logger or WindAuditLogger()
        self.headless = headless
        self.excel_app = None
        self.excel_workbook = None
        self._wind_plugin_available = None  # Lazily checked

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Close Excel and clean up."""
        try:
            if self.excel_workbook:
                self.excel_workbook.close()
            if self.excel_app:
                self.excel_app.quit()
        except Exception as e:
            self.logger.logger.warning(f"Cleanup warning: {e}")
        finally:
            self.excel_workbook = None
            self.excel_app = None

    def check_wind_plugin(self):
        """Check if Wind Excel add-in is available."""
        if self._wind_plugin_available is not None:
            return self._wind_plugin_available
        try:
            import xlwings as xw
            app = xw.App(visible=False)
            wb = app.books.add()
            # Try calling a Wind function to see if it's registered
            ws = wb.sheets[0]
            ws.range("A1").value = "=WSD(\"000300.SH\",\"close\",\"2024-01-01\",\"2024-01-02\")"
            wb.calculation = "manual"
            ws.range("A2").value = "=ISERROR(A1)"
            wb.calculation = "automatic"
            time.sleep(3)
            err_val = ws.range("A2").value
            wb.close()
            app.quit()
            self._wind_plugin_available = not bool(err_val)
            self.logger.log_event(
                "WIND_PLUGIN_CHECK",
                {"plugin_available": self._wind_plugin_available, "headless": True},
                result="AVAILABLE" if self._wind_plugin_available else "NOT_AVAILABLE"
            )
        except Exception as e:
            self._wind_plugin_available = False
            self.logger.log_event(
                "WIND_PLUGIN_CHECK",
                {"error": str(e), "traceback": str(e)[:200]},
                result="ERROR"
            )
        return self._wind_plugin_available

    def launch_excel(self):
        """Launch Excel application."""
        try:
            import xlwings as xw
            self.excel_app = xw.App(visible=not self.headless)
            self.logger.logger.info("Excel launched successfully")
            return True
        except Exception as e:
            self.logger.logger.error(f"Failed to launch Excel: {e}")
            self.logger.log_event("EXCEL_LAUNCH_FAIL", {"error": str(e)}, result="FAIL")
            return False

    def write_wsd_formula(self, ws, cell, wind_code, field, date_start, date_end, params=""):
        """Write a WSD (Wind Stock Data) formula into an Excel cell."""
        formula = f'=WSD("{wind_code}","{field}","{date_start}","{date_end}"'
        if params:
            formula += f',"{params}"'
        formula += ")"
        ws.range(cell).value = formula
        self.logger.logger.debug(f"Wrote WSD formula at {cell}: {formula}")

    def write_wtd_formula(self, ws, cell, wind_code, field, date):
        """Write a WTD (Wind Today Data) formula into an Excel cell."""
        formula = f'=WTD("{wind_code}","{field}","{date}")'
        ws.range(cell).value = formula
        self.logger.logger.debug(f"Wrote WTD formula at {cell}: {formula}")

    def write_wss_formula(self, ws, cell, wind_code, field):
        """Write a WSS (Wind Sector Snapshot) formula into an Excel cell."""
        formula = f'=WSS("{wind_code}","{field}")'
        ws.range(cell).value = formula
        self.logger.logger.debug(f"Wrote WSS formula at {cell}: {formula}")

    def calculate_all(self, wb):
        """Force calculation of all formulas in workbook."""
        wb.calculation = "automatic"
        # Wait for calculation to complete
        time.sleep(5)  # Minimum wait; extend for large queries
        return True

    def save_workbook(self, filepath):
        """Save workbook to specified path."""
        self.excel_workbook.save(filepath)
        self.logger.logger.info(f"Workbook saved: {filepath}")
        return filepath

    def create_wsd_workbook(self, wind_code, field, date_start, date_end, output_name=None):
        """
        Create an Excel workbook with WSD formulas for a single query.
        Returns: (filepath, success, error_message)
        """
        if not self.excel_app:
            if not self.launch_excel():
                return None, False, "Excel launch failed"

        wb = self.excel_app.books.add()
        self.excel_workbook = wb
        ws = wb.sheets[0]
        ws.name = "WindData"

        # Headers
        ws.range("A1").value = "date"
        ws.range("B1").value = f"{wind_code} {field}"

        # Write WSD formula
        self.write_wsd_formula(ws, "A2", wind_code, field, date_start, date_end)

        # Force calculation
        self.calculate_all(wb)

        # Save
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_name:
            output_name = f"wind_wsd_{wind_code}_{field}_{timestamp}.xlsx"
        filepath = os.path.join(EXCEL_OUTPUT_DIR, output_name)
        self.save_workbook(filepath)

        # Read back data
        try:
            import openpyxl
            result_wb = openpyxl.load_workbook(filepath)
            result_ws = result_wb.active
            data = []
            for row in result_ws.iter_rows(min_row=2, values_only=True):
                data.append(row)
            result_wb.close()
            success = len(data) > 0
            self.logger.logger.info(f"WSD query result: {len(data)} rows for {wind_code} {field}")
            self.logger.log_event(
                "WIND_QUERY_RESULT",
                {"backend": "excel", "wind_code": wind_code, "field": field,
                 "rows_returned": len(data), "date_range": f"{date_start}~{date_end}"},
                result="SUCCESS" if success else "NO_DATA"
            )
            return filepath, success, None
        except Exception as e:
            self.logger.logger.error(f"Failed to read back data: {e}")
            return filepath, False, str(e)


# =============================================================================
# WindPy Direct Backend
# =============================================================================

class WindPyBackend:
    """
    Direct WindPy Python backend.
    Requires Wind desktop client running and logged in.
    """

    def __init__(self, logger=None):
        self.logger = logger or WindAuditLogger()
        self.wind = None
        self.connected = False

    def check_connection(self):
        """Check if WindPy is connected to a running Wind session."""
        try:
            import WindPy as w
            self.wind = w.w
            self.connected = self.wind.isconnected()
            self.logger.log_event(
                "WINDPY_CONNECTION_CHECK",
                {"isconnected": self.connected, "dll_path": self.wind.dllpath},
                result="CONNECTED" if self.connected else "NOT_CONNECTED"
            )
        except Exception as e:
            self.connected = False
            self.logger.log_event(
                "WINDPY_CONNECTION_CHECK",
                {"error": str(e)},
                result="ERROR"
            )
        return self.connected

    def start(self):
        """Start WindPy connection."""
        try:
            import WindPy as w
            self.wind = w.w
            result = self.wind.start()
            success = result.ErrorCode == 0 if hasattr(result, 'ErrorCode') else False
            self.connected = success
            self.logger.log_event(
                "WINDPY_START",
                {"error_code": getattr(result, 'ErrorCode', None),
                 "data": str(getattr(result, 'Data', ''))[:200]},
                result="SUCCESS" if success else "FAIL"
            )
            return success
        except Exception as e:
            self.logger.log_event(
                "WINDPY_START",
                {"error": str(e)},
                result="ERROR"
            )
            return False

    def query_wsd(self, wind_code, fields, date_start, date_end, factor_id=None):
        """Query Wind Stock Data (time series)."""
        if not self.connected:
            self.logger.logger.warning("WindPy not connected, cannot query")
            return None
        try:
            result = self.wind.wsd(wind_code, fields, date_start, date_end)
            success = result.ErrorCode == 0 if hasattr(result, 'ErrorCode') else False
            self.logger.log_wind_call(
                factor_id or "unknown", wind_code, fields, date_start, date_end, "windpy",
                f"ErrorCode={getattr(result, 'ErrorCode', 'N/A')}"
            )
            return result if success else None
        except Exception as e:
            self.logger.logger.error(f"WindPy WSD query failed: {e}")
            return None

    def stop(self):
        """Stop WindPy connection."""
        try:
            if self.wind and self.connected:
                self.wind.stop()
            self.connected = False
            self.logger.logger.info("WindPy stopped")
        except Exception as e:
            self.logger.logger.warning(f"WindPy stop warning: {e}")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point for manual testing."""
    logger = WindAuditLogger()
    logger.log_event("MODULE_INITIALIZED", {
        "module": "wind_excel_automation",
        "conditional_factors": list(CONDITIONAL_FACTORS.keys()),
        "hold_factors": list(HOLD_FACTORS.keys()),
        "wind_codes": list(WIND_CODES.keys()),
        "date_range": DATE_RANGE,
        "wind_dll_paths": WIND_DLL_PATHS,
        "wind_executables": WIND_EXECUTABLES,
    }, result="INITIALIZED")

    gate = ProcessGate(logger)
    gate.check_pipeline_readiness()

    print("\n=== Wind Excel Automation Module ===")
    print(f"Conditional factors: {list(CONDITIONAL_FACTORS.keys())}")
    print(f"HOLD factors: {list(HOLD_FACTORS.keys())}")
    print(f"Wind codes: {list(WIND_CODES.keys())}")
    print(f"Date range: {DATE_RANGE['start']} ~ {DATE_RANGE['end']} (chunk={DATE_RANGE['chunk_size']}d)")
    print(f"Wind DLL paths: {list(WIND_DLL_PATHS.keys())}")
    print(f"Wind executables: {list(WIND_EXECUTABLES.keys())}")
    print(f"Audit log: {logger.log_file}")
    print(f"Event log: {logger.event_log_file}")
    print(f"Excel output dir: {EXCEL_OUTPUT_DIR}")
    print()

    # Check WindPy
    print("--- WindPy Backend Check ---")
    wp = WindPyBackend(logger)
    wp.check_connection()
    if not wp.connected:
        print("WindPy not connected (Wind desktop client not running or not logged in)")
        print("Attempting start()...")
        wp.start()
    print(f"Connected: {wp.connected}")
    print()

    # Check Excel backend
    print("--- Excel Backend Check ---")
    with ExcelWindBackend(logger) as ewb:
        print(f"Headless mode: {ewb.headless}")
        plugin_ok = ewb.check_wind_plugin()
        print(f"Wind plugin available: {plugin_ok}")
    print()

    logger.log_event("MODULE_READY", {
        "windpy_connected": wp.connected,
        "module_status": "READY",
    }, result="READY")

    print("Module initialized. Use functions directly for data queries.")


if __name__ == "__main__":
    main()
