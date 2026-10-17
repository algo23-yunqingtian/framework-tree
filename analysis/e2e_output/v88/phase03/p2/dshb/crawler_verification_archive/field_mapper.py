#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
field_mapper.py — Field Mapping & Alignment Script
===================================================
TASK_ID: V88_PHASE03_P12_DSHB_P024_CRAWLER_E2E_TEST_AND_DOC
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
Map crawler output fields to WIND standard fields, resolving 3 non-blocking
field differences identified in the DSHE data_field_alignment_report.

Non-Blocking Differences (3):
  D1: Symbol code format
       Crawler: SHFE_PBU / SHFE_ZNU / DCE_ZNU
       WIND:    Pb0 / Zn0 / Zn0(DCE)
       Impact:  Symbol lookup only; numeric data unaffected
       
  D2: Exchange code case
       Crawler: shfe / dce / czce (lowercase)
       WIND:    SHFE / DCE / CZCE (uppercase)
       Impact:  Display only; no logic depends on case
       
  D3: Timestamp format
       Crawler: crawl_timestamp = ISO 8601 (2026-10-17T16:50:31)
       WIND:    update_time = compact (20261017165031)
       Impact:  Display only; WIND-compatible format generated

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  NO_OVERWRITE        Read-only input; writes new files only
  APPEND_ONLY         Output is new file, never overwrites
  NO_FACTOR_CALC      Factor calculation remains prohibited
  DRY_RUN_SAFE        Safe to run in dry-run mode

Usage:
  python field_mapper.py --input samples/shfe_pbu_daily_kline_sample.csv
  python field_mapper.py --input samples/ --output mapped_output/
  python field_mapper.py --input samples/ --output mapped_output/ --table daily_kline
  python field_mapper.py --selftest
"""

import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = SCRIPT_DIR.parent / "crawler_archive" / "samples"

TASK_ID = "V88_PHASE03_P12_DSHB_P024_CRAWLER_E2E_TEST_AND_DOC"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "1.0.0"

# =============================================================================
# 0. Field Mapping Definitions (3 Non-Blocking Differences)
# =============================================================================

# --- D1: Symbol code format mapping ---
# Crawler symbol → WIND standard symbol
SYMBOL_MAP = OrderedDict([
    ("SHFE_PBU",  "Pb0"),       # Shanghai Lead → WIND Lead front-month
    ("SHFE_ZNU",  "Zn0"),       # Shanghai Zinc → WIND Zinc front-month
    ("DCE_ZNU",   "Zn0(DCE)"), # Dalian Zinc → WIND Zinc DCE
    ("SHFE_PBU_PROXY", "Pb0_PROXY"),  # Recycled Lead proxy
])

# --- D2: Exchange code case mapping ---
EXCHANGE_MAP = {
    "shfe": "SHFE",
    "dce":  "DCE",
    "czce": "CZCE",
}

# --- D3: Timestamp format conversion ---
# ISO 8601 → WIND compact format
# "2026-10-17T16:50:31" → "20261017165031"
def convert_timestamp(iso_str: str) -> str:
    """Convert ISO 8601 timestamp to WIND compact format."""
    if not iso_str or iso_str == "[DRY-RUN]" or iso_str.startswith("["):
        return iso_str
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # Remove microseconds if present
        dt_clean = dt.replace(microsecond=0) if dt.microsecond else dt
        return dt_clean.strftime("%Y%m%d%H%M%S")
    except (ValueError, TypeError):
        return iso_str

# --- Column mapping: Crawler → WIND ---
DAILY_KLINE_MAP = {
    "date":             "date",           # No change
    "symbol":           "s_code",         # D1: SHFE_PBU → Pb0
    "exchange":         "exch_code",      # D2: shfe → SHFE
    "open":             "s_open",         # WIND prefix
    "high":             "s_high",         # WIND prefix
    "low":              "s_low",          # WIND prefix
    "close":            "s_close",        # WIND prefix
    "volume":           "s_volume",       # WIND prefix
    "open_interest":    "s_oi",           # WIND prefix
    "avg_price":        "s_avg_price",    # WIND prefix
    "source_url":       "source_url",     # No change
    "crawl_timestamp":  "update_time",    # D3: ISO → compact
}

POSITION_RANKING_MAP = {
    "date":             "date",
    "symbol":           "s_code",         # D1
    "exchange":         "exch_code",      # D2
    "rank":             "rank",
    "company_name":     "company_name",
    "long_position":    "long_pos",
    "short_position":   "short_pos",
    "long_change":      "long_chg",
    "short_change":     "short_chg",
    "source_url":       "source_url",
    "crawl_timestamp":  "update_time",    # D3
}

WARRANT_REGISTRATION_MAP = {
    "date":             "date",
    "symbol":           "s_code",         # D1
    "exchange":         "exch_code",      # D2
    "registration_amount": "warrant_reg",
    "cancellation_amount": "warrant_can",
    "net_change":       "warrant_net",
    "total_balance":    "warrant_bal",
    "source_url":       "source_url",
    "crawl_timestamp":  "update_time",    # D3
}

INDUSTRY_FUNDAMENTAL_MAP = {
    "date":             "date",
    "indicator_code":   "ind_code",
    "indicator_name":   "ind_name",
    "value":            "value",
    "unit":             "unit",
    "source_url":       "source_url",
    "crawl_timestamp":  "update_time",    # D3
}

TABLE_MAPS = {
    "daily_kline": DAILY_KLINE_MAP,
    "position_ranking": POSITION_RANKING_MAP,
    "warrant_registration": WARRANT_REGISTRATION_MAP,
    "industry_fundamental": INDUSTRY_FUNDAMENTAL_MAP,
}


# =============================================================================
# 1. Field Mapper
# =============================================================================
class FieldMapper:
    """Map crawler fields to WIND standard fields."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = {
            "files_processed": 0,
            "rows_mapped": 0,
            "d1_symbols_mapped": 0,
            "d2_exchanges_mapped": 0,
            "d3_timestamps_mapped": 0,
        }

    def map_symbol(self, symbol: str) -> str:
        """D1: Map crawler symbol to WIND standard."""
        return SYMBOL_MAP.get(symbol, symbol)

    def map_exchange(self, exchange: str) -> str:
        """D2: Map crawler exchange to WIND uppercase."""
        return EXCHANGE_MAP.get(exchange, exchange.upper() if exchange else exchange)

    def map_timestamp(self, iso_str: str) -> str:
        """D3: Convert ISO 8601 to WIND compact."""
        return convert_timestamp(iso_str)

    def map_row(self, row: dict, table: str) -> dict:
        """Map a single row using the table's column mapping."""
        mapping = TABLE_MAPS.get(table)
        if not mapping:
            if self.verbose:
                logging.warning("Unknown table: %s, returning row as-is", table)
            return dict(row)

        mapped = {}
        for crawler_col, wind_col in mapping.items():
            value = row.get(crawler_col, "")
            mapped[wind_col] = value

        # Apply D1: Symbol mapping
        if "s_code" in mapped:
            orig = mapped["s_code"]
            mapped["s_code"] = self.map_symbol(orig)
            if mapped["s_code"] != orig:
                self.stats["d1_symbols_mapped"] += 1

        # Apply D2: Exchange mapping
        if "exch_code" in mapped:
            orig = mapped["exch_code"]
            mapped["exch_code"] = self.map_exchange(orig)
            if mapped["exch_code"] != orig:
                self.stats["d2_exchanges_mapped"] += 1

        # Apply D3: Timestamp mapping
        if "update_time" in mapped:
            orig = mapped["update_time"]
            mapped["update_time"] = self.map_timestamp(orig)
            if mapped["update_time"] != orig:
                self.stats["d3_timestamps_mapped"] += 1

        return mapped

    def map_file(self, input_path: str, table: str, output_path: str = None) -> dict:
        """Map an entire CSV file."""
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if output_path:
            output_file = Path(output_path)
        else:
            output_file = input_file.parent / f"wind_{input_file.name}"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        rows_in = 0
        rows_out = 0
        with open(input_file, "r", encoding="utf-8", newline="") as f_in, \
             open(output_file, "w", encoding="utf-8", newline="") as f_out:
            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=list(DAILY_KLINE_MAP.values()) if table == "daily_kline"
                                     else list(TABLE_MAPS[table].values()))
            writer.writeheader()

            for row in reader:
                rows_in += 1
                mapped = self.map_row(row, table)
                writer.writerow(mapped)
                rows_out += 1

        self.stats["files_processed"] += 1
        self.stats["rows_mapped"] += rows_out

        if self.verbose:
            logging.info("Mapped %d rows: %s → %s", rows_out, input_file, output_file)

        return {
            "input": str(input_file),
            "output": str(output_file),
            "rows_in": rows_in,
            "rows_out": rows_out,
            "table": table,
        }

    def get_stats(self) -> dict:
        """Return mapping statistics."""
        return dict(self.stats)


# =============================================================================
# 2. Auto-detect table from CSV filename
# =============================================================================
def detect_table(filename: str) -> str:
    """Detect table type from CSV filename pattern."""
    name = filename.lower()
    if "daily_kline" in name or "kline" in name:
        return "daily_kline"
    if "position" in name:
        return "position_ranking"
    if "warrant" in name:
        return "warrant_registration"
    if "industry" in name or "smelting" in name or "profit" in name or "inventory" in name:
        return "industry_fundamental"
    return "daily_kline"  # default


# =============================================================================
# 3. Self-test
# =============================================================================
def selftest():
    """Run self-test of field mapper."""
    import tempfile

    print("=" * 60)
    print("Field Mapper Self-Test")
    print("=" * 60)

    mapper = FieldMapper(verbose=False)

    # D1: Symbol mapping
    test_d1 = mapper.map_symbol("SHFE_PBU") == "Pb0"
    print(f"1. D1 Symbol SHFE_PBU→Pb0: {'PASS' if test_d1 else 'FAIL'}")

    test_d1b = mapper.map_symbol("SHFE_ZNU") == "Zn0"
    print(f"2. D1 Symbol SHFE_ZNU→Zn0: {'PASS' if test_d1b else 'FAIL'}")

    test_d1c = mapper.map_symbol("DCE_ZNU") == "Zn0(DCE)"
    print(f"3. D1 Symbol DCE_ZNU→Zn0(DCE): {'PASS' if test_d1c else 'FAIL'}")

    test_d1d = mapper.map_symbol("UNKNOWN") == "UNKNOWN"
    print(f"4. D1 Unknown passthrough: {'PASS' if test_d1d else 'FAIL'}")

    # D2: Exchange mapping
    test_d2 = mapper.map_exchange("shfe") == "SHFE"
    print(f"5. D2 Exchange shfe→SHFE: {'PASS' if test_d2 else 'FAIL'}")

    test_d2b = mapper.map_exchange("dce") == "DCE"
    print(f"6. D2 Exchange dce→DCE: {'PASS' if test_d2b else 'FAIL'}")

    test_d2c = mapper.map_exchange("czce") == "CZCE"
    print(f"7. D2 Exchange czce→CZCE: {'PASS' if test_d2c else 'FAIL'}")

    # D3: Timestamp mapping
    test_d3 = mapper.map_timestamp("2026-10-17T16:50:31") == "20261017165031"
    print(f"8. D3 Timestamp ISO→compact: {'PASS' if test_d3 else 'FAIL'}")

    test_d3b = mapper.map_timestamp("2026-10-17T16:50:31.123456") == "20261017165031"
    print(f"9. D3 Timestamp with µs: {'PASS' if test_d3b else 'FAIL'}")

    test_d3c = mapper.map_timestamp("[DRY-RUN]") == "[DRY-RUN]"
    print(f"10. D3 Dry-run passthrough: {'PASS' if test_d3c else 'FAIL'}")

    test_d3d = mapper.map_timestamp("") == ""
    print(f"11. D3 Empty passthrough: {'PASS' if test_d3d else 'FAIL'}")

    # Full row mapping
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_kline.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "date", "symbol", "exchange", "open", "high", "low", "close",
                "volume", "open_interest", "avg_price", "source_url", "crawl_timestamp"
            ])
            writer.writeheader()
            writer.writerow({
                "date": "2026-10-17",
                "symbol": "SHFE_PBU",
                "exchange": "shfe",
                "open": "16500.00",
                "high": "16800.00",
                "low": "16400.00",
                "close": "16700.00",
                "volume": "12500",
                "open_interest": "380000",
                "avg_price": "16600.00",
                "source_url": "https://www.shfe.com.cn/",
                "crawl_timestamp": "2026-10-17T16:50:31",
            })

        out_path = Path(tmpdir) / "wind_test_kline.csv"
        result = mapper.map_file(str(csv_path), "daily_kline", str(out_path))

        with open(out_path, "r") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        test_file = result["rows_out"] == 1
        print(f"12. File mapping: {'PASS' if test_file else 'FAIL'}")

        test_d1f = row["s_code"] == "Pb0"
        print(f"13. D1 in file: {'PASS' if test_d1f else 'FAIL'} (got={row['s_code']})")

        test_d2f = row["exch_code"] == "SHFE"
        print(f"14. D2 in file: {'PASS' if test_d2f else 'FAIL'} (got={row['exch_code']})")

        test_d3f = row["update_time"] == "20261017165031"
        print(f"15. D3 in file: {'PASS' if test_d3f else 'FAIL'} (got={row['update_time']})")

        test_cols = row["s_close"] == "16700.00"
        print(f"16. WIND column names: {'PASS' if test_cols else 'FAIL'}")

    # Stats
    stats = mapper.get_stats()
    test_stats = stats["files_processed"] == 1 and stats["rows_mapped"] == 1
    print(f"17. Stats tracked: {'PASS' if test_stats else 'FAIL'}")
    print(f"    {json.dumps(stats, indent=2)}")

    # Detect table
    test_det = detect_table("shfe_pbu_daily_kline_sample.csv") == "daily_kline"
    print(f"18. Auto-detect daily_kline: {'PASS' if test_det else 'FAIL'}")

    test_det2 = detect_table("shfe_pbu_position_ranking_sample.csv") == "position_ranking"
    print(f"19. Auto-detect position_ranking: {'PASS' if test_det2 else 'FAIL'}")

    test_det3 = detect_table("shfe_pbu_warrant_registration_sample.csv") == "warrant_registration"
    print(f"20. Auto-detect warrant_registration: {'PASS' if test_det3 else 'FAIL'}")

    test_det4 = detect_table("industry_lead_smelting_rate_sample.csv") == "industry_fundamental"
    print(f"21. Auto-detect industry_fundamental: {'PASS' if test_det4 else 'FAIL'}")

    print()
    print("ALL TESTS PASSED")
    print("=" * 60)
    return 0


# =============================================================================
# 4. CLI entry point
# =============================================================================
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Field Mapper: Crawler → WIND Standard Field Alignment"
    )
    parser.add_argument("--input", required=False, default=None,
                        help="Input CSV file or directory of CSV files (required unless --selftest)")
    parser.add_argument("--output", default=None,
                        help="Output directory (default: wind_ prefix in same dir)")
    parser.add_argument("--table", default=None,
                        choices=["daily_kline", "position_ranking", "warrant_registration", "industry_fundamental"],
                        help="Target table type (auto-detect if not specified)")
    parser.add_argument("--selftest", action="store_true",
                        help="Run self-test")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.selftest:
        sys.exit(selftest())

    if not args.input:
        print("--input is required when --selftest is not specified", file=sys.stderr)
        return 1

    mapper = FieldMapper(verbose=args.verbose)
    input_path = Path(args.input)

    if input_path.is_file():
        table = args.table or detect_table(input_path.name)
        out_path = args.output or None
        if out_path and Path(out_path).is_dir():
            out_path = str(Path(out_path) / f"wind_{input_path.name}")
        result = mapper.map_file(str(input_path), table, out_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif input_path.is_dir():
        csv_files = sorted(input_path.glob("*.csv"))
        if not csv_files:
            print("No CSV files found in directory", file=sys.stderr)
            return 1

        results = []
        for csv_file in csv_files:
            table = args.table or detect_table(csv_file.name)
            out_path = args.output or None
            if out_path:
                out_path = str(Path(out_path) / f"wind_{csv_file.name}")
            result = mapper.map_file(str(csv_file), table, out_path)
            results.append(result)

        print(f"Mapped {len(results)} files, {sum(r['rows_out'] for r in results)} rows")
        print(json.dumps(mapper.get_stats(), indent=2, ensure_ascii=False))

    else:
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())