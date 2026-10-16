# -*- coding: utf-8 -*-
"""
wind_data_pull_pipeline.py
Full 7-Table Wind Data Pull Pipeline for DSHA-P54 G7 Conditional Gray Backtest
================================================================================
Pulls data for FACTOR-004/006/007 (CONDITIONAL_PASS) across all 7 Wind tables.
Chunked execution: 3 chunks (365d each), 2023-01-01 ~ 2024-12-31.

Governance:
  - Only FACTOR-004/006/007 data pulled
  - FACTOR-001/002/003/005 data NEVER touched
  - All calls logged to DSHD audit trail
  - DSHD_AUDIT_TRIGGERED_STOP circuit breaker
  - No cross-table joins, no cross-time queries
  - Read-only, no aggregation exports

Usage:
  python wind_data_pull_pipeline.py --dry-run         # Plan only, no queries
  python wind_data_pull_pipeline.py --factor FACTOR-004  # Single factor
  python wind_data_pull_pipeline.py                    # All 3 factors
"""

import os
import sys
import time
import json
import datetime
import argparse
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wind_excel_automation import (
    WORKSPACE, AUDIT_DIR, EXCEL_OUTPUT_DIR, CONDITIONAL_FACTORS,
    HOLD_FACTORS, WIND_CODES, DATE_RANGE, WIND_DLL_PATHS,
    WindAuditLogger, ProcessGate, HoldFactorTerminationError,
    ExcelWindBackend, WindPyBackend,
)

# =============================================================================
# Table Definitions (7 Wind tables)
# =============================================================================

WIND_TABLES = {
    "Wind持仓量表": {
        "fields": ["OI", "OI_change", "date", "variety"],
        "used_by": ["FACTOR-001"],  # HOLD - do not pull
        "conditional_factors": [],
    },
    "Wind新闻舆情表": {
        "fields": ["sentiment_score", "search_volume", "date", "variety"],
        "used_by": ["FACTOR-002"],  # HOLD - do not pull
        "conditional_factors": [],
    },
    "Wind交易所持仓明细表": {
        "fields": ["exchange_oi", "long_oi", "short_oi", "date", "variety"],
        "used_by": ["FACTOR-003"],  # HOLD - do not pull
        "conditional_factors": [],
    },
    "Wind因子IC计算表": {
        "fields": ["IC_score", "forecast_return", "realized_return", "date", "variety"],
        "used_by": [],
        "conditional_factors": ["FACTOR-004"],
    },
    "Wind因子ICIR计算表": {
        "fields": ["rolling_ICIR", "IC_std", "date", "variery", "factor_id"],
        "used_by": ["FACTOR-005"],  # HOLD - do not pull
        "conditional_factors": [],
    },
    "Wind因子计算管线": {
        "fields": ["leakage_score", "info_score", "date", "variety", "factor_id"],
        "used_by": [],
        "conditional_factors": ["FACTOR-006"],
    },
    "Wind多因子合成表": {
        "fields": ["F19_score", "F20_score", "CF003_score", "decay_score", "date", "variety"],
        "used_by": [],
        "conditional_factors": ["FACTOR-007"],
    },
}

# Map conditional factors to their tables
FACTOR_TABLE_MAP = {
    "FACTOR-004": "Wind因子IC计算表",
    "FACTOR-006": "Wind因子计算管线",
    "FACTOR-007": "Wind多因子合成表",
}


# =============================================================================
# Data Pull Pipeline
# =============================================================================

class WindDataPullPipeline:
    """
    Full data pull pipeline for 3 CONDITIONAL_PASS factors.
    Chunked execution with audit logging.
    """

    def __init__(self, logger=None, dry_run=False):
        self.logger = logger or WindAuditLogger()
        self.gate = ProcessGate(self.logger)
        self.dry_run = dry_run
        self.results = []
        self.pipeline_start = None
        self.pipeline_end = None

    def plan_execution(self):
        """Plan the execution order and chunk boundaries."""
        plan = {
            "date_range": DATE_RANGE,
            "chunks": [],
            "total_wind_calls_estimated": 0,
            "factors": list(CONDITIONAL_FACTORS.keys()),
            "tables": list(FACTOR_TABLE_MAP.values()),
            "wind_codes": list(WIND_CODES.keys()),
        }

        # Generate chunks
        start = datetime.datetime.strptime(DATE_RANGE["start"], "%Y-%m-%d")
        end = datetime.datetime.strptime(DATE_RANGE["end"], "%Y-%m-%d")
        chunk_size = DATE_RANGE["chunk_size"]

        current = start
        chunk_id = 1
        while current <= end:
            chunk_end = current + datetime.timedelta(days=chunk_size - 1)
            if chunk_end > end:
                chunk_end = end
            chunk = {
                "chunk_id": chunk_id,
                "date_start": current.strftime("%Y-%m-%d"),
                "date_end": chunk_end.strftime("%Y-%m-%d"),
                "days": (chunk_end - current).days + 1,
            }
            plan["chunks"].append(chunk)
            current = chunk_end + datetime.timedelta(days=1)
            chunk_id += 1

        # Estimate wind calls
        for chunk in plan["chunks"]:
            for factor_id, table in FACTOR_TABLE_MAP.items():
                factor = CONDITIONAL_FACTORS[factor_id]
                fields = len(factor["fields"])
                codes = len(WIND_CODES)
                calls = fields * codes  # 1 call per field per code
                chunk["wind_calls_estimated"] = calls
                chunk["factors"] = [factor_id]
                plan["total_wind_calls_estimated"] += calls

        self.logger.log_event("PIPELINE_PLAN", plan, result="PLANNED")
        return plan

    def execute_factor(self, factor_id, chunks, backend=None):
        """Execute data pull for a single factor."""
        self.gate.check_factor_access(factor_id)  # Will raise if HOLD

        factor = CONDITIONAL_FACTORS[factor_id]
        table = FACTOR_TABLE_MAP[factor_id]
        fields = factor["fields"]
        wind_fields = factor["wind_fields"]

        factor_results = {
            "factor_id": factor_id,
            "table": table,
            "fields": fields,
            "chunks": [],
            "total_calls": 0,
            "total_rows": 0,
            "success": True,
        }

        for chunk in chunks:
            chunk_result = {
                "chunk_id": chunk["chunk_id"],
                "date_start": chunk["date_start"],
                "date_end": chunk["date_end"],
                "calls": [],
                "success": True,
            }

            for wind_code_name, wind_code in WIND_CODES.items():
                for field_name, wind_field in wind_fields.items():
                    call_record = {
                        "wind_code": wind_code,
                        "wind_code_name": wind_code_name,
                        "field": field_name,
                        "wind_field": wind_field,
                        "date_start": chunk["date_start"],
                        "date_end": chunk["date_end"],
                    }

                    if self.dry_run:
                        call_record["status"] = "DRY_RUN_SKIPPED"
                        call_record["rows"] = 0
                        call_record["filepath"] = None
                        self.logger.logger.info(
                            f"  [DRY RUN] {factor_id} {wind_code} {field_name} "
                            f"{chunk['date_start']}~{chunk['date_end']}"
                        )
                    else:
                        call_record["status"] = "PENDING"
                        call_record["rows"] = 0
                        call_record["filepath"] = None

                        # Try WindPy first, fallback to Excel
                        query_ok = False
                        if backend is None or backend == "windpy":
                            query_ok = self._query_windpy(
                                factor_id, wind_code, wind_field,
                                chunk["date_start"], chunk["date_end"], call_record
                            )
                        if not query_ok and (backend is None or backend == "excel"):
                            query_ok = self._query_excel(
                                factor_id, wind_code, field_name,
                                chunk["date_start"], chunk["date_end"], call_record
                            )
                        call_record["status"] = "SUCCESS" if query_ok else "FAIL"

                    chunk_result["calls"].append(call_record)
                    factor_results["total_calls"] += 1
                    factor_results["total_rows"] += call_record["rows"]

            factor_results["chunks"].append(chunk_result)

        self.results.append(factor_results)
        return factor_results

    def _query_windpy(self, factor_id, wind_code, wind_field, date_start, date_end, record):
        """Query via WindPy backend."""
        try:
            wp = WindPyBackend(self.logger)
            if not wp.check_connection():
                if not wp.start():
                    return False
            result = wp.query_wsd(wind_code, [wind_field], date_start, date_end, factor_id=factor_id)
            if result and hasattr(result, 'ErrorCode') and result.ErrorCode == 0:
                rows = len(result.Data) if hasattr(result, 'Data') else 0
                record["rows"] = rows
                record["backend"] = "windpy"
                return rows > 0
            return False
        except Exception as e:
            self.logger.logger.warning(f"WindPy query failed for {wind_code} {wind_field}: {e}")
            return False

    def _query_excel(self, factor_id, wind_code, field_name, date_start, date_end, record):
        """Query via Excel+Wind plugin backend."""
        try:
            with ExcelWindBackend(self.logger) as ewb:
                output_name = f"{factor_id}_{wind_code}_{field_name}_{date_start}_{date_end}.xlsx"
                filepath, success, error = ewb.create_wsd_workbook(
                    wind_code, field_name, date_start, date_end,
                    output_name=output_name
                )
            if success:
                record["rows"] = "check_file"
                record["filepath"] = filepath
                record["backend"] = "excel"
                return True
            record["error"] = error
            return False
        except Exception as e:
            self.logger.logger.warning(f"Excel query failed for {wind_code} {field_name}: {e}")
            return False

    def execute_all(self, backend=None):
        """Execute full data pull for all 3 conditional factors."""
        self.pipeline_start = datetime.datetime.now()

        self.logger.log_event("PIPELINE_START", {
            "pipeline": "7-table data pull",
            "factors": list(CONDITIONAL_FACTORS.keys()),
            "dry_run": self.dry_run,
            "backend": backend or "auto",
        }, result="STARTING")

        plan = self.plan_execution()

        print("\n" + "=" * 70)
        print("DSHA-P54 WIND DATA PULL PIPELINE")
        print("=" * 70)
        print(f"Mode:      {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        print(f"Factors:   {list(CONDITIONAL_FACTORS.keys())}")
        print(f"Tables:    {list(FACTOR_TABLE_MAP.values())}")
        print(f"Date:      {plan['chunks'][0]['date_start']} ~ {plan['chunks'][-1]['date_end']}")
        print(f"Chunks:    {len(plan['chunks'])}")
        print(f"Est Calls: {plan['total_wind_calls_estimated']}")
        print("=" * 70)

        for factor_id in CONDITIONAL_FACTORS.keys():
            print(f"\n--- Factor: {factor_id} ({CONDITIONAL_FACTORS[factor_id]['description']}) ---")
            self.execute_factor(factor_id, plan["chunks"], backend)
            fr = self.results[-1]
            print(f"  Calls: {fr['total_calls']}, Rows: {fr['total_rows']}, "
                  f"{'SUCCESS' if fr['success'] else 'FAIL'}")

        self.pipeline_end = datetime.datetime.now()
        elapsed = (self.pipeline_end - self.pipeline_start).total_seconds()

        total_calls = sum(r["total_calls"] for r in self.results)
        total_rows = sum(r["total_rows"] for r in self.results)

        self.logger.log_event("PIPELINE_COMPLETE", {
            "elapsed_seconds": elapsed,
            "factors_processed": len(self.results),
            "total_calls": total_calls,
            "total_rows": total_rows,
            "dry_run": self.dry_run,
            "results": [{"factor_id": r["factor_id"], "calls": r["total_calls"], "rows": r["total_rows"]} for r in self.results],
        }, result="DRY_RUN_COMPLETE" if self.dry_run else "COMPLETE")

        print(f"\n{'=' * 70}")
        print(f"PIPELINE {'DRY RUN ' if self.dry_run else ''}COMPLETE")
        print(f"Factors:    {len(self.results)}")
        print(f"Total Calls: {total_calls}")
        print(f"Total Rows:  {total_rows}")
        print(f"Elapsed:     {elapsed:.1f}s")
        print(f"{'=' * 70}")

        return self.results


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DSHA-P54 Wind Data Pull Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Plan only, no queries")
    parser.add_argument("--factor", type=str, choices=list(CONDITIONAL_FACTORS.keys()),
                        help="Execute single factor only")
    parser.add_argument("--backend", type=str, choices=["auto", "excel", "windpy"], default="auto",
                        help="Backend selection (default: auto)")
    args = parser.parse_args()

    logger = WindAuditLogger()
    pipeline = WindDataPullPipeline(logger, dry_run=args.dry_run)

    if args.factor:
        print(f"\nExecuting single factor: {args.factor}")
        plan = pipeline.plan_execution()
        pipeline.execute_factor(args.factor, plan["chunks"], args.backend)
    else:
        pipeline.execute_all(args.backend)
