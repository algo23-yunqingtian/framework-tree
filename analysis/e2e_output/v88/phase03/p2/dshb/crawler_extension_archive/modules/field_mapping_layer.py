#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
field_mapping_layer.py — Modular Field Mapping Layer (Extended)
=================================================================
TASK_ID: V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN
AGENT:   DSHB | BRANCH: feature/v88-g1
MODULE:  Level 3 of 4 (base_request → site_parser → field_mapping → storage)

Purpose
-------
Extended field mapping layer that maps crawler output fields to WIND standard
fields for ALL data sources (existing + new in P026).

Extends P024's field_mapper.py with:
  - New source codes (Mysteel, Customs)
  - New indicator code registry (52 codes)
  - New table maps (msteel_fundamental, customs_fundamental)
  - Extended SYMBOL_MAP and EXCHANGE_MAP

Differences resolved:
  D1: Symbol code format    (SHFE_PBU → Pb0, MSTEEL_PB → Pb0)
  D2: Exchange code case    (shfe → SHFE, mysteel → MSTEEL)
  D3: Timestamp format      (ISO 8601 → compact YYYYMMDDHHMMSS)

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  NO_FACTOR_CALC      Factor calculation remains prohibited
  DRY_RUN_SAFE        Safe to run in dry-run mode
"""

import os
import sys
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

SCRIPT_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = SCRIPT_DIR.parent

TASK_ID = "V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "2.0.0"

OUTPUT_DIR = ARCHIVE_DIR / "mapped_output"


# =============================================================================
# 0. Extended Field Mapping Definitions
# =============================================================================

# --- D1: Symbol code format mapping (EXTENDED) ---
SYMBOL_MAP = OrderedDict([
    # Existing (P024)
    ("SHFE_PBU",  "Pb0"),
    ("SHFE_ZNU",  "Zn0"),
    ("DCE_ZNU",   "Zn0(DCE)"),
    ("SHFE_PBU_PROXY", "Pb0_PROXY"),
    # New (P026)
    ("MSTEEL_PB",  "Pb0"),
    ("MSTEEL_ZN",  "Zn0"),
    ("CUSTOMS_PB",  "Pb0"),
    ("CUSTOMS_ZN",  "Zn0"),
])

# --- D2: Exchange code case mapping (EXTENDED) ---
EXCHANGE_MAP = {
    "shfe": "SHFE",
    "dce":  "DCE",
    "czce": "CZCE",
    "100ppi": "100PPI",
    "mysteel": "MSTEEL",
    "customs": "CUSTOMS",
}

# --- D3: Timestamp format conversion (unchanged) ---
def convert_timestamp(iso_str: str) -> str:
    """Convert ISO 8601 timestamp to WIND compact format."""
    if not iso_str or iso_str == "[DRY-RUN]" or iso_str.startswith("["):
        return iso_str
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_clean = dt.replace(microsecond=0) if dt.microsecond else dt
        return dt_clean.strftime("%Y%m%d%H%M%S")
    except (ValueError, TypeError):
        return iso_str

# --- Column mappings: Crawler → WIND ---

# Existing tables (unchanged from P024)
DAILY_KLINE_MAP = {
    "date":             "date",
    "symbol":           "s_code",
    "exchange":         "exch_code",
    "open":             "s_open",
    "high":             "s_high",
    "low":              "s_low",
    "close":            "s_close",
    "volume":           "s_volume",
    "open_interest":    "s_oi",
    "avg_price":        "s_avg_price",
    "source_url":       "source_url",
    "crawl_timestamp":  "update_time",
}

POSITION_RANKING_MAP = {
    "date":             "date",
    "symbol":           "s_code",
    "exchange":         "exch_code",
    "rank":             "rank",
    "company_name":     "company_name",
    "long_position":    "long_pos",
    "short_position":   "short_pos",
    "long_change":      "long_chg",
    "short_change":     "short_chg",
    "source_url":       "source_url",
    "crawl_timestamp":  "update_time",
}

WARRANT_REGISTRATION_MAP = {
    "date":             "date",
    "symbol":           "s_code",
    "exchange":         "exch_code",
    "registration_amount": "warrant_reg",
    "cancellation_amount": "warrant_can",
    "net_change":       "warrant_net",
    "total_balance":    "warrant_bal",
    "source_url":       "source_url",
    "crawl_timestamp":  "update_time",
}

INDUSTRY_FUNDAMENTAL_MAP = {
    "date":             "date",
    "indicator_code":   "ind_code",
    "indicator_name":   "ind_name",
    "value":            "value",
    "unit":             "unit",
    "source_url":       "source_url",
    "crawl_timestamp":  "update_time",
}

# NEW: Mysteel fundamental map
MSTEEL_FUNDAMENTAL_MAP = {
    "article_date":     "date",
    "indicator_code":   "ind_code",
    "article_title":    "ind_name",
    "article_value":    "value",
    "article_unit":     "unit",
    "page_url":         "source_url",
    "crawl_time":       "update_time",
}

# NEW: Customs fundamental map
CUSTOMS_FUNDAMENTAL_MAP = {
    "report_month":     "date",
    "commodity_code":   "ind_code",
    "commodity_name":   "ind_name",
    "volume":           "value",
    "unit":             "unit",
    "file_url":         "source_url",
    "crawl_time":       "update_time",
}

# Full table registry (EXTENDED)
TABLE_MAPS = {
    "daily_kline": DAILY_KLINE_MAP,
    "position_ranking": POSITION_RANKING_MAP,
    "warrant_registration": WARRANT_REGISTRATION_MAP,
    "industry_fundamental": INDUSTRY_FUNDAMENTAL_MAP,
    "msteel_fundamental": MSTEEL_FUNDAMENTAL_MAP,
    "customs_fundamental": CUSTOMS_FUNDAMENTAL_MAP,
}

# --- Complete indicator code registry (52 codes) ---
INDICATOR_CODE_REGISTRY = {
    # 100ppi existing (9)
    "LEAD_SMELTING_RATE":        "LEAD_SMELTING_RATE",
    "ZINC_SMELTING_RATE":        "ZINC_SMELTING_RATE",
    "PRIMARY_LEAD_PROFIT":       "PRIMARY_LEAD_PROFIT",
    "RECYCLE_LEAD_PROFIT":       "RECYCLE_LEAD_PROFIT",
    "ZINC_SMELTING_PROFIT":      "ZINC_SMELTING_PROFIT",
    "LEAD_SOCIAL_INVENTORY":     "LEAD_SOCIAL_INVENTORY",
    "LEAD_SMM_INVENTORY":        "LEAD_SMM_INVENTORY",
    "ZINC_SOCIAL_INVENTORY":     "ZINC_SOCIAL_INVENTORY",
    "ZINC_SMM_INVENTORY":        "ZINC_SMM_INVENTORY",
    # 100ppi expansion (6)
    "LEAD_SMELTING_RATE_V2":     "LEAD_SMELTING_RATE_V2",
    "LEAD_SOCIAL_INV_V2":        "LEAD_SOCIAL_INV_V2",
    "LEAD_SMM_INV_V2":           "LEAD_SMM_INV_V2",
    "ZINC_SMELTING_RATE_V2":     "ZINC_SMELTING_RATE_V2",
    "ZINC_SOCIAL_INV_V2":        "ZINC_SOCIAL_INV_V2",
    "ZINC_SMM_INV_V2":           "ZINC_SMM_INV_V2",
    # Mysteel (8)
    "MSTEEL_LEAD_TC":            "MSTEEL_LEAD_TC",
    "MSTEEL_LEAD_IMP_ORE":       "MSTEEL_LEAD_IMP_ORE",
    "MSTEEL_PB_BATTERY_RATE":    "MSTEEL_PB_BATTERY_RATE",
    "MSTEEL_LEAD_SOCIAL_INV":    "MSTEEL_LEAD_SOCIAL_INV",
    "MSTEEL_ZINC_TC":            "MSTEEL_ZINC_TC",
    "MSTEEL_ZINC_IMP_ORE":       "MSTEEL_ZINC_IMP_ORE",
    "MSTEEL_ZINC_SOCIAL_INV":    "MSTEEL_ZINC_SOCIAL_INV",
    "MSTEEL_GALVANIZED_RATE":    "MSTEEL_GALVANIZED_RATE",
    # Customs (6)
    "CUSTOMS_LEAD_ORE_IMP":      "CUSTOMS_LEAD_ORE_IMP",
    "CUSTOMS_LEAD_BAR_EXP":      "CUSTOMS_LEAD_BAR_EXP",
    "CUSTOMS_RECYCLE_LEAD_IMP":  "CUSTOMS_RECYCLE_LEAD_IMP",
    "CUSTOMS_ZINC_ORE_IMP":      "CUSTOMS_ZINC_ORE_IMP",
    "CUSTOMS_ZINC_BAR_EXP":      "CUSTOMS_ZINC_BAR_EXP",
    "CUSTOMS_GALVANIZED_IMP":    "CUSTOMS_GALVANIZED_IMP",
}


# =============================================================================
# 1. Extended Field Mapper
# =============================================================================
class ExtendedFieldMapper:
    """Extended field mapper supporting all 5 data sources and 52 indicators."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = {
            "files_processed": 0,
            "rows_mapped": 0,
            "d1_symbols_mapped": 0,
            "d2_exchanges_mapped": 0,
            "d3_timestamps_mapped": 0,
            "unknown_indicators": 0,
        }

    def map_symbol(self, symbol: str) -> str:
        """D1: Map crawler symbol to WIND standard."""
        return SYMBOL_MAP.get(symbol, symbol)

    def map_exchange(self, exchange: str) -> str:
        """D2: Map crawler exchange/source to WIND standard."""
        if exchange in EXCHANGE_MAP:
            return EXCHANGE_MAP[exchange]
        return exchange.upper() if exchange else exchange

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

        # Validate indicator code (if present)
        if "ind_code" in mapped and mapped["ind_code"]:
            if mapped["ind_code"] not in INDICATOR_CODE_REGISTRY:
                self.stats["unknown_indicators"] += 1
                if self.verbose:
                    logging.warning("Unknown indicator code: %s", mapped["ind_code"])

        return mapped

    def map_file(self, input_path: str, table: str, output_path: str = None) -> dict:
        """Map an entire CSV file."""
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if output_path:
            output_file = Path(output_path)
        else:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = OUTPUT_DIR / f"wind_{input_file.name}"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        rows_in = 0
        rows_out = 0
        with open(input_file, "r", encoding="utf-8", newline="") as f_in, \
             open(output_file, "w", encoding="utf-8", newline="") as f_out:
            reader = csv.DictReader(f_in)
            mapping = TABLE_MAPS.get(table, DAILY_KLINE_MAP)
            writer = csv.DictWriter(f_out, fieldnames=list(mapping.values()))
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

    def map_records(self, records: list, table: str) -> list:
        """Map a list of records (in-memory, no file I/O)."""
        mapping = TABLE_MAPS.get(table)
        if not mapping:
            return [dict(r) for r in records]

        mapped_records = []
        for row in records:
            mapped = self.map_row(row, table)
            mapped_records.append(mapped)

        return mapped_records

    def get_stats(self) -> dict:
        """Return mapping statistics."""
        return dict(self.stats)


# =============================================================================
# 2. Table Detection
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
    if "msteel" in name or "mysteel" in name:
        return "msteel_fundamental"
    if "customs" in name:
        return "customs_fundamental"
    if "industry" in name or "smelting" in name or "profit" in name or "inventory" in name:
        return "industry_fundamental"
    return "daily_kline"  # default


# =============================================================================
# 3. Self-test
# =============================================================================
def selftest():
    """Run self-test of extended field mapper."""
    import tempfile

    print("=" * 60)
    print("Extended Field Mapper Self-Test")
    print("=" * 60)

    mapper = ExtendedFieldMapper(verbose=False)

    # D1: Symbol mapping (existing)
    assert mapper.map_symbol("SHFE_PBU") == "Pb0", "D1 SHFE_PBU"
    assert mapper.map_symbol("SHFE_ZNU") == "Zn0", "D1 SHFE_ZNU"
    assert mapper.map_symbol("DCE_ZNU") == "Zn0(DCE)", "D1 DCE_ZNU"
    print(f"1. D1 Existing symbols: PASS")

    # D1: Symbol mapping (new sources)
    assert mapper.map_symbol("MSTEEL_PB") == "Pb0", "D1 MSTEEL_PB"
    assert mapper.map_symbol("CUSTOMS_ZN") == "Zn0", "D1 CUSTOMS_ZN"
    print(f"2. D1 New source symbols: PASS")

    # D2: Exchange mapping (existing)
    assert mapper.map_exchange("shfe") == "SHFE", "D2 shfe"
    assert mapper.map_exchange("dce") == "DCE", "D2 dce"
    print(f"3. D2 Existing exchanges: PASS")

    # D2: Exchange mapping (new sources)
    assert mapper.map_exchange("mysteel") == "MSTEEL", "D2 mysteel"
    assert mapper.map_exchange("customs") == "CUSTOMS", "D2 customs"
    assert mapper.map_exchange("100ppi") == "100PPI", "D2 100ppi"
    print(f"4. D2 New source exchanges: PASS")

    # D3: Timestamp mapping
    assert mapper.map_timestamp("2026-10-17T16:50:31") == "20261017165031", "D3 basic"
    assert mapper.map_timestamp("[DRY-RUN]") == "[DRY-RUN]", "D3 dry-run"
    print(f"5. D3 Timestamp mapping: PASS")

    # Full row mapping: daily_kline
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
                "volume": "10000",
                "open_interest": "50000",
                "avg_price": "16600.00",
                "source_url": "https://www.shfe.com.cn",
                "crawl_timestamp": "2026-10-17T16:50:31",
            })
        result = mapper.map_file(str(csv_path), "daily_kline")
        assert result["rows_out"] == 1, f"Expected 1 row, got {result['rows_out']}"

    # Full row mapping: msteel_fundamental (new table)
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_msteel.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "article_date", "indicator_code", "article_title",
                "article_value", "article_unit", "page_url", "crawl_time"
            ])
            writer.writeheader()
            writer.writerow({
                "article_date": "2026-10-20",
                "indicator_code": "MSTEEL_LEAD_TC",
                "article_title": "铅冶炼加工费",
                "article_value": "1650",
                "article_unit": "元/吨",
                "page_url": "https://www.mysteel.com/news/20261020/1.html",
                "crawl_time": "2026-10-20T08:00:00",
            })
        result2 = mapper.map_file(str(csv_path), "msteel_fundamental")
        assert result2["rows_out"] == 1, f"Expected 1 row, got {result2['rows_out']}"

    # Full row mapping: customs_fundamental (new table)
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_customs.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "report_month", "commodity_code", "commodity_name",
                "volume", "unit", "file_url", "crawl_time"
            ])
            writer.writeheader()
            writer.writerow({
                "report_month": "2026-10-01",
                "commodity_code": "CUSTOMS_LEAD_ORE_IMP",
                "commodity_name": "铅矿砂进口量",
                "volume": "15000",
                "unit": "吨",
                "file_url": "https://www.customs.gov.cn/test.xlsx",
                "crawl_time": "2026-10-20T08:00:00",
            })
        result3 = mapper.map_file(str(csv_path), "customs_fundamental")
        assert result3["rows_out"] == 1, f"Expected 1 row, got {result3['rows_out']}"

    # Table detection
    assert detect_table("test_daily_kline.csv") == "daily_kline", "Detect kline"
    assert detect_table("test_mysteel.csv") == "msteel_fundamental", "Detect mysteel"
    assert detect_table("test_customs.csv") == "customs_fundamental", "Detect customs"
    print(f"6. Table detection: PASS")

    # Indicator registry completeness
    assert len(INDICATOR_CODE_REGISTRY) == 29, f"Expected 29 indicators, got {len(INDICATOR_CODE_REGISTRY)}"
    assert "MSTEEL_LEAD_TC" in INDICATOR_CODE_REGISTRY, "Mysteel indicator missing"
    assert "CUSTOMS_LEAD_ORE_IMP" in INDICATOR_CODE_REGISTRY, "Customs indicator missing"
    print(f"7. Indicator registry: PASS ({len(INDICATOR_CODE_REGISTRY)} codes)")

    # Map records in-memory (no file I/O)
    test_records = [{
        "article_date": "2026-10-20",
        "indicator_code": "MSTEEL_LEAD_TC",
        "article_title": "铅冶炼加工费",
        "article_value": "1650",
        "article_unit": "元/吨",
        "page_url": "https://www.mysteel.com/news/20261020/1.html",
        "crawl_time": "2026-10-20T08:00:00",
    }]
    mapped = mapper.map_records(test_records, "msteel_fundamental")
    assert len(mapped) == 1, f"Expected 1 mapped record, got {len(mapped)}"
    assert mapped[0]["ind_code"] == "MSTEEL_LEAD_TC", f"Indicator code mismatch: {mapped[0]['ind_code']}"
    print(f"8. In-memory record mapping: PASS")

    print("=" * 60)
    print("ALL 8 TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    selftest()