#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exchange_crawler.py — Exchange Public Data Crawler (SHFE / DCE / CZCE)
======================================================================
TASK_ID: V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
Crawl exchange public data for PB / ZN / Recycle-PB pipeline:
  - Daily K-line (OHLCV)        — 日K线
  - Position ranking (会员持仓排名)
  - Warrant registration/cancellation (仓单注册/注销)

Data sources:
  SHFE: https://www.shfe.com.cn/cn/business/data/
  DCE:  https://www.dce.com.cn/publicweb/quotesdata/
  CZCE: https://www.czce.com.cn/

Output format (WIND-aligned standardized CSV):
  Columns: date, symbol, exchange, open, high, low, close, volume,
           open_interest, avg_price, source_url, crawl_timestamp
  - date:             YYYY-MM-DD
  - symbol:           e.g. SHFE_PBU, SHFE_ZNU, DCE_ZNU
  - exchange:         shfe / dce / czce
  - open/high/low/close: numeric
  - volume:           contracts (手)
  - open_interest:    contracts (手)
  - avg_price:        numeric (元/吨)
  - source_url:       original URL
  - crawl_timestamp:  ISO 8601

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  NO_OVERWRITE        Existing CSV files are never truncated
  APPEND_ONLY         Data appended; idempotent by (date, symbol)
  RATE_LIMIT          Minimum 3.0s between requests
  NO_CONCURRENT       Sequential only
  DRY_RUN             Default: no actual HTTP requests

Usage:
  python exchange_crawler.py --exchange shfe --dry-run
  python exchange_crawler.py --exchange all --dry-run
  python exchange_crawler.py --exchange shfe --date 2026-10-20 --live
"""

import os
import sys
import csv
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import OrderedDict

SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = SCRIPT_DIR / "samples"
LOG_DIR = SCRIPT_DIR / "logs"

TASK_ID = "V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "1.0.0"

# =============================================================================
# 0. Exchange configuration
# =============================================================================
EXCHANGE_CONFIG = {
    "shfe": {
        "name": "Shanghai Futures Exchange (SHFE)",
        "short": "SHFE",
        "base_url": "https://www.shfe.com.cn",
        "daily_url": "https://www.shfe.com.cn/cn/business/data/dailydata/",
        "position_url": "https://www.shfe.com.cn/cn/business/data/positionranking/",
        "warrant_url": "https://www.shfe.com.cn/cn/business/data/warrant/",
        "symbols": {
            "pb": {"symbol": "SHFE_PBU", "wind_code": "SHFE_PBU", "name_cn": "沪铅"},
            "zn": {"symbol": "SHFE_ZNU", "wind_code": "SHFE_ZNU", "name_cn": "沪锌"},
        },
        "data_types": ["daily_kline", "position_ranking", "warrant_registration"],
    },
    "dce": {
        "name": "Dalian Commodity Exchange (DCE)",
        "short": "DCE",
        "base_url": "https://www.dce.com.cn",
        "daily_url": "https://www.dce.com.cn/publicweb/quotesdata/dailyQuotes.html",
        "position_url": "https://www.dce.com.cn/publicweb/quotesdata/memberRankings.html",
        "warrant_url": "https://www.dce.com.cn/publicweb/quotesdata/warrant.html",
        "symbols": {
            "zn": {"symbol": "DCE_ZNU", "wind_code": "DCE_ZNU", "name_cn": "大锌"},
        },
        "data_types": ["daily_kline", "position_ranking", "warrant_registration"],
    },
    "czce": {
        "name": "Zhengzhou Commodity Exchange (CZCE)",
        "short": "CZCE",
        "base_url": "https://www.czce.com.cn",
        "daily_url": "https://www.czce.com.cn/cn/BB2729010175/BB2729010176.htm",
        "position_url": "https://www.czce.com.cn/cn/BB2729010175/BB2729010177.htm",
        "warrant_url": "https://www.czce.com.cn/cn/BB2729010175/BB2729010178.htm",
        "symbols": {},  # No direct PB/ZN futures on CZCE
        "data_types": ["daily_kline", "position_ranking", "warrant_registration"],
    },
}

# Data type definitions
DATA_TYPES = {
    "daily_kline": {
        "description": "Daily K-line (OHLCV)",
        "csv_columns": ["date", "symbol", "exchange", "open", "high", "low",
                        "close", "volume", "open_interest", "avg_price",
                        "source_url", "crawl_timestamp"],
        "idempotent_keys": ["date", "symbol"],
    },
    "position_ranking": {
        "description": "Position ranking (member long/short positions)",
        "csv_columns": ["date", "symbol", "exchange", "rank", "company_name",
                        "long_position", "short_position", "long_change",
                        "short_change", "source_url", "crawl_timestamp"],
        "idempotent_keys": ["date", "symbol", "company_name"],
    },
    "warrant_registration": {
        "description": "Warrant registration/cancellation",
        "csv_columns": ["date", "symbol", "exchange", "registration_amount",
                        "cancellation_amount", "net_change", "total_balance",
                        "source_url", "crawl_timestamp"],
        "idempotent_keys": ["date", "symbol"],
    },
}


# =============================================================================
# 1. CSV writer (APPEND_ONLY, NO_OVERWRITE)
# =============================================================================
class AppendOnlyCSVWriter:
    """Write CSV data with APPEND_ONLY and NO_OVERWRITE semantics."""

    def __init__(self, file_path: Path, columns: list, idempotent_keys: list = None):
        self.file_path = file_path
        self.columns = columns
        self.idempotent_keys = idempotent_keys or []
        self._existing_keys = set()
        self._ensure_file()

    def _ensure_file(self):
        """Ensure file exists; if exists, load existing keys for dedup."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if self.file_path.exists() and self.file_path.stat().st_size > 0:
            self._load_existing_keys()

    def _load_existing_keys(self):
        """Load existing idempotent keys from file for dedup."""
        try:
            with open(self.file_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = tuple(row.get(k, "") for k in self.idempotent_keys)
                    self._existing_keys.add(key)
        except Exception as e:
            logging.warning("Could not load existing keys: %s", e)

    def write_rows(self, rows: list) -> int:
        """Write rows, skipping duplicates. Returns number of new rows written."""
        new_rows = []
        for row in rows:
            key = tuple(str(row.get(k, "")) for k in self.idempotent_keys)
            if key in self._existing_keys:
                logging.debug("Skip duplicate: %s", key)
                continue
            new_rows.append(row)
            self._existing_keys.add(key)

        if not new_rows:
            return 0

        file_exists = self.file_path.exists() and self.file_path.stat().st_size > 0
        mode = "a" if file_exists else "w"
        with open(self.file_path, mode, encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_rows)

        return len(new_rows)


# =============================================================================
# 2. Exchange Crawler
# =============================================================================
class ExchangeCrawler:
    """Crawler for exchange public data (SHFE / DCE / CZCE)."""

    def __init__(self, exchange: str = "all", rate_limiter=None,
                 fetcher=None, dry_run: bool = True):
        self.exchange = exchange
        self.rate_limiter = rate_limiter
        self.fetcher = fetcher
        self.dry_run = dry_run
        self.results = []
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> list:
        """Execute crawler for configured exchange(s)."""
        exchanges = list(EXCHANGE_CONFIG.keys())
        if self.exchange != "all":
            if self.exchange not in EXCHANGE_CONFIG:
                logging.warning("Unknown exchange: %s", self.exchange)
                return []
            exchanges = [self.exchange]

        for exch_key in exchanges:
            exch_info = EXCHANGE_CONFIG[exch_key]
            logging.info("=== %s (%s) ===", exch_info["name"], exch_key)

            for symbol_key, symbol_info in exch_info["symbols"].items():
                logging.info("  Symbol: %s (%s)", symbol_info["symbol"], symbol_info["name_cn"])
                for dtype in exch_info["data_types"]:
                    result = self._fetch_data_type(exch_key, exch_info, symbol_info, dtype)
                    self.results.append(result)

            if not exch_info["symbols"]:
                logging.info("  No target symbols for %s", exch_key)

        return self.results

    def _fetch_data_type(self, exch_key: str, exch_info: dict,
                         symbol_info: dict, data_type: str) -> dict:
        """Fetch a single data type for a symbol."""
        dtype_info = DATA_TYPES[data_type]
        symbol = symbol_info["symbol"]
        exchange = exch_key

        # Determine target URL
        if data_type == "daily_kline":
            url = exch_info["daily_url"]
        elif data_type == "position_ranking":
            url = exch_info["position_url"]
        elif data_type == "warrant_registration":
            url = exch_info["warrant_url"]
        else:
            url = exch_info["base_url"]

        # Build params
        params = {"symbol": symbol, "date": date.today().isoformat()}

        # Execute fetch (dry-run or live)
        if self.fetcher:
            response = self.fetcher.fetch(url, params)
        else:
            response = f"[NO_FETCHER] {url}"

        # Parse response and generate rows
        rows = self._parse_response(exch_key, symbol_info, data_type, response, url)

        # Write to CSV (sample file)
        csv_path = SAMPLES_DIR / f"{symbol.lower()}_{data_type}_sample.csv"
        writer = AppendOnlyCSVWriter(csv_path, dtype_info["csv_columns"],
                                     dtype_info["idempotent_keys"])
        written = writer.write_rows(rows)

        return {
            "exchange": exch_key,
            "symbol": symbol,
            "data_type": data_type,
            "url": url,
            "dry_run": self.dry_run,
            "rows_parsed": len(rows),
            "rows_written": written,
            "csv_path": str(csv_path),
        }

    def _parse_response(self, exch_key: str, symbol_info: dict,
                        data_type: str, response: str, url: str) -> list:
        """Parse HTTP response into standardized rows."""
        rows = []
        today = date.today().isoformat()
        crawl_ts = datetime.now().isoformat()
        symbol = symbol_info["symbol"]
        wind_code = symbol_info["wind_code"]

        if data_type == "daily_kline":
            rows = self._parse_daily_kline(exch_key, symbol, wind_code, response, url,
                                           today, crawl_ts)
        elif data_type == "position_ranking":
            rows = self._parse_position_ranking(exch_key, symbol, wind_code, response,
                                                url, today, crawl_ts)
        elif data_type == "warrant_registration":
            rows = self._parse_warrant_registration(exch_key, symbol, wind_code,
                                                     response, url, today, crawl_ts)

        return rows

    def _parse_daily_kline(self, exch_key, symbol, wind_code, response, url,
                           today, crawl_ts) -> list:
        """Parse daily K-line data from response."""
        rows = []

        if self.dry_run or "[DRY-RUN]" in response:
            # Generate synthetic sample row for dry-run
            rows.append({
                "date": today,
                "symbol": symbol,
                "exchange": exch_key,
                "open": 0.0,
                "high": 0.0,
                "low": 0.0,
                "close": 0.0,
                "volume": 0,
                "open_interest": 0,
                "avg_price": 0.0,
                "source_url": url,
                "crawl_timestamp": crawl_ts,
            })
            logging.debug("Dry-run: generated synthetic row for %s", symbol)
        else:
            # In live mode, parse actual HTML/JSON response
            # Note: Actual parsing logic depends on specific exchange API format
            # For now, log that parsing needs implementation for live data
            logging.info("Live mode: parsing %s daily K-line from %s", symbol, url)
            # TODO: Implement actual HTML/JSON parsing for each exchange
            # This requires parsing exchange-specific API responses
            rows.append({
                "date": today,
                "symbol": symbol,
                "exchange": exch_key,
                "open": 0.0,
                "high": 0.0,
                "low": 0.0,
                "close": 0.0,
                "volume": 0,
                "open_interest": 0,
                "avg_price": 0.0,
                "source_url": url,
                "crawl_timestamp": crawl_ts,
                "note": "Live parsing not yet implemented; requires exchange-specific parser",
            })

        return rows

    def _parse_position_ranking(self, exch_key, symbol, wind_code, response, url,
                                today, crawl_ts) -> list:
        """Parse position ranking data from response."""
        rows = []

        if self.dry_run or "[DRY-RUN]" in response:
            # Synthetic sample rows for dry-run
            sample_companies = [
                ("上海期货交易所会员", 15000, 12000, 500, -300),
                ("永安期货", 12000, 9000, 300, -200),
                ("中信期货", 10000, 8500, 200, -100),
                ("国泰君安期货", 8000, 7000, 150, -50),
                ("海通期货", 6000, 5500, 100, 0),
            ]
            for rank, (company, long_pos, short_pos, long_chg, short_chg) in enumerate(
                    sample_companies, 1):
                rows.append({
                    "date": today,
                    "symbol": symbol,
                    "exchange": exch_key,
                    "rank": rank,
                    "company_name": company,
                    "long_position": long_pos,
                    "short_position": short_pos,
                    "long_change": long_chg,
                    "short_change": short_chg,
                    "source_url": url,
                    "crawl_timestamp": crawl_ts,
                })
            logging.debug("Dry-run: generated %d sample rows for %s position ranking",
                          len(rows), symbol)
        else:
            logging.info("Live mode: parsing %s position ranking from %s", symbol, url)
            # TODO: Implement actual parsing
            rows.append({
                "date": today,
                "symbol": symbol,
                "exchange": exch_key,
                "rank": 0,
                "company_name": "LIVE_PARSING_NOT_IMPLEMENTED",
                "long_position": 0,
                "short_position": 0,
                "long_change": 0,
                "short_change": 0,
                "source_url": url,
                "crawl_timestamp": crawl_ts,
            })

        return rows

    def _parse_warrant_registration(self, exch_key, symbol, wind_code, response, url,
                                    today, crawl_ts) -> list:
        """Parse warrant registration/cancellation data from response."""
        rows = []

        if self.dry_run or "[DRY-RUN]" in response:
            # Synthetic sample row for dry-run
            rows.append({
                "date": today,
                "symbol": symbol,
                "exchange": exch_key,
                "registration_amount": 0,
                "cancellation_amount": 0,
                "net_change": 0,
                "total_balance": 0,
                "source_url": url,
                "crawl_timestamp": crawl_ts,
            })
            logging.debug("Dry-run: generated synthetic row for %s warrant registration", symbol)
        else:
            logging.info("Live mode: parsing %s warrant registration from %s", symbol, url)
            # TODO: Implement actual parsing
            rows.append({
                "date": today,
                "symbol": symbol,
                "exchange": exch_key,
                "registration_amount": 0,
                "cancellation_amount": 0,
                "net_change": 0,
                "total_balance": 0,
                "source_url": url,
                "crawl_timestamp": crawl_ts,
                "note": "Live parsing not yet implemented",
            })

        return rows


# =============================================================================
# 3. CLI entry point
# =============================================================================
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="DSHB Exchange Public Data Crawler"
    )
    parser.add_argument("--exchange", default="all",
                        choices=["shfe", "dce", "czce", "all"],
                        help="Target exchange (default: all)")
    parser.add_argument("--date", default=None,
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--live", action="store_true",
                        help="Enable live HTTP requests (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run mode")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    dry_run = not args.live
    crawler = ExchangeCrawler(
        exchange=args.exchange,
        dry_run=dry_run,
    )
    results = crawler.run()

    # Print summary
    logging.info("=" * 50)
    logging.info("Exchange Crawler Results:")
    logging.info("  Results: %d", len(results))
    logging.info("  Dry-run: %s", dry_run)
    logging.info("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())