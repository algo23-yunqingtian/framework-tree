#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawler_extension_main.py — Modular Multi-Source Crawler Orchestrator
======================================================================
TASK_ID: V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN
AGENT:   DSHB | BRANCH: feature/v88-g1
VERSION: 2.0.0

Purpose
-------
Main orchestrator for the extended multi-source crawler framework.
Integrates all 4 modular layers:
  1. base_request_layer → HTTP requests with rate limiting
  2. site_parser_layer  → Site-specific data extraction
  3. field_mapping_layer → WIND standard field mapping
  4. storage_layer      → SQLite database storage

Supports 5 data sources:
  - SHFE (exchange)
  - DCE (exchange)
  - 100ppi (industry fundamentals)
  - Mysteel (industry news/market reports) — NEW
  - Customs (import/export statistics) — NEW

Architecture:
  ┌─────────────────────────────────────────┐
  │  crawler_extension_main.py (Orchestrator)│
  ├─────────────────────────────────────────┤
  │  base_request_layer.py (HTTP + RateLimit)│
  │  site_parser_layer.py (4 Parsers)        │
  │  field_mapping_layer.py (WIND Mapping)   │
  │  storage_layer.py (SQLite Storage)       │
  ├─────────────────────────────────────────┤
  │  data_source_config.json (Per-source cfg)│
  └─────────────────────────────────────────┘

Usage:
  python crawler_extension_main.py --list-sources
  python crawler_extension_main.py --source shfe --dry-run
  python crawler_extension_main.py --source 100ppi --dry-run
  python crawler_extension_main.py --source mysteel --dry-run
  python crawler_extension_main.py --source customs --dry-run
  python crawler_extension_main.py --source all --dry-run
  python crawler_extension_main.py --source all --dry-run --selftest

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  NO_OVERWRITE        Never overwrite existing output files
  APPEND_ONLY         Data is append-only
  DRY_RUN_DEFAULT     Default: no actual HTTP requests
  RATE_LIMIT          Minimum 3.0 seconds between requests
  NO_CONCURRENT       Sequential only
  NO_FACTOR_CALC      Factor calculation remains prohibited
  NO_PAID_API_CALLS   No paid API calls
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

# =============================================================================
# 0. Environment setup
# =============================================================================
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

SCRIPT_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = SCRIPT_DIR.parent
MODULES_DIR = SCRIPT_DIR / "modules"

# Add modules directory to path
sys.path.insert(0, str(MODULES_DIR))

TASK_ID = "V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "2.0.0"

CONSTRAINTS = {
    "NO_ZHIJI_API_CALL": True,
    "NO_OVERWRITE": True,
    "APPEND_ONLY": True,
    "DRY_RUN_DEFAULT": True,
    "RATE_LIMIT_ENFORCED": True,
    "NO_CONCURRENT_REQUESTS": True,
    "NO_FACTOR_CALCULATION": True,
    "NO_PAID_API_CALLS": True,
}

# Load configuration
CONFIG_PATH = ARCHIVE_DIR / "data_source_config.json"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    logging.warning("Config file not found or invalid: %s, using defaults", e)
    CONFIG = {"global": {"switch": "OFF", "enable_live": False, "rate_limit_seconds": 3.0},
              "sources": {}}

LOG_DIR = ARCHIVE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 1. Source Registry
# =============================================================================
class SourceRegistry:
    """Registry of available data sources and their parsers."""

    def __init__(self):
        self.sources = {}
        self._register_sources()

    def _register_sources(self):
        """Register all data sources with their parsers."""
        # Exchange sources (SHFE, DCE)
        from site_parser_layer import ExchangeParser
        for exchange in ["shfe", "dce"]:
            source_cfg = CONFIG["sources"].get(exchange, {})
            if source_cfg.get("enabled", True):
                self.sources[exchange] = {
                    "name": source_cfg.get("name", exchange.upper()),
                    "category": "exchange",
                    "parser_class": ExchangeParser,
                    "parser_kwargs": {"exchange": exchange},
                    "config": source_cfg,
                }

        # Industry source (100ppi)
        from site_parser_layer import IndustryParser
        source_cfg = CONFIG["sources"].get("100ppi", {})
        if source_cfg.get("enabled", True):
            self.sources["100ppi"] = {
                "name": source_cfg.get("name", "100ppi"),
                "category": "industry",
                "parser_class": IndustryParser,
                "parser_kwargs": {},
                "config": source_cfg,
            }

        # Mysteel source (new)
        from site_parser_layer import MysteelParser
        source_cfg = CONFIG["sources"].get("mysteel", {})
        if source_cfg.get("enabled", False):
            self.sources["mysteel"] = {
                "name": source_cfg.get("name", "Mysteel"),
                "category": "industry_news",
                "parser_class": MysteelParser,
                "parser_kwargs": {},
                "config": source_cfg,
            }

        # Customs source (new)
        from site_parser_layer import CustomsParser
        source_cfg = CONFIG["sources"].get("customs", {})
        if source_cfg.get("enabled", False):
            self.sources["customs"] = {
                "name": source_cfg.get("name", "Customs"),
                "category": "government_stats",
                "parser_class": CustomsParser,
                "parser_kwargs": {},
                "config": source_cfg,
            }

    def list_sources(self) -> list:
        """List all registered sources."""
        return [(name, info["name"], info["category"], info["config"].get("enabled", False))
                for name, info in self.sources.items()]

    def get_parser(self, source_name: str, session):
        """Get parser instance for a source."""
        if source_name not in self.sources:
            raise ValueError(f"Unknown source: {source_name}")
        info = self.sources[source_name]
        return info["parser_class"](session, **info.get("parser_kwargs", {}))


# =============================================================================
# 2. Crawler Orchestrator
# =============================================================================
class CrawlerOrchestrator:
    """
    Main orchestrator that coordinates all modular layers.

    Flow:
      1. Initialize RequestSession (rate limiting, dry-run)
      2. For each enabled source:
         a. Create appropriate parser
         b. Fetch data (or dry-run)
         c. Map fields to WIND standard
         d. Save CSV output
         e. Load to database (if live mode)
    """

    def __init__(self, source: str = "all", dry_run: bool = None,
                 rate_limit: float = None, db_path: str = None):
        self.source = source.lower()
        global_cfg = CONFIG.get("global", {})
        self.dry_run = dry_run if dry_run is not None else not global_cfg.get("enable_live", False)
        self.rate_limit = rate_limit if rate_limit else global_cfg.get("rate_limit_seconds", 3.0)
        self.db_path = db_path
        self.registry = SourceRegistry()
        self.mapper = None
        self.db = None
        self.results = []
        self.session_stats = {}

    def run(self) -> dict:
        """Execute the crawler pipeline for configured sources."""
        from base_request_layer import RequestSession
        from field_mapping_layer import ExtendedFieldMapper
        from storage_layer import DatabaseInterface

        # Initialize layers
        session = RequestSession(
            max_requests=CONFIG.get("global", {}).get("max_requests_per_session", 100),
            max_consecutive_errors=CONFIG.get("global", {}).get("max_consecutive_errors", 3),
            rate_limit=self.rate_limit,
            dry_run=self.dry_run,
        )
        self.mapper = ExtendedFieldMapper(verbose=False)

        # Connect to database only in live mode
        if not self.dry_run and self.db_path:
            self.db = DatabaseInterface(self.db_path)
            self.db.connect()
            self.db.create_all_tables()

        # Determine which sources to crawl
        sources_to_crawl = self._get_sources_to_crawl()
        logging.info("Sources to crawl: %s", [s[0] for s in sources_to_crawl])

        # Crawl each source
        total_records = 0
        total_mapped = 0

        for source_name, _, _ in sources_to_crawl:
            logging.info("Processing source: %s", source_name)
            records = self._process_source(source_name, session)
            total_records += len(records)

            if records and not self.dry_run:
                # Map and store
                mapped = self.mapper.map_records(records, self._detect_table(source_name, records))
                total_mapped += len(mapped)
                # Save CSV
                csv_path = self._save_csv(records, source_name)
                # Load to DB
                if self.db:
                    self.db.load_records(mapped, self._detect_table(source_name, records))

        # Collect session stats
        self.session_stats = session.get_session_stats()

        result = {
            "task_id": TASK_ID,
            "agent": AGENT,
            "branch": BRANCH,
            "version": VERSION,
            "dry_run": self.dry_run,
            "sources_processed": [s[0] for s in sources_to_crawl],
            "total_records": total_records,
            "total_mapped": total_mapped,
            "session_stats": self.session_stats,
            "results": self.results,
        }

        if self.db:
            result["db_stats"] = self.db.get_load_stats()
            self.db.close()

        return result

    def _get_sources_to_crawl(self):
        """Determine which sources to process based on --source argument."""
        all_sources = self.registry.list_sources()
        if self.source == "all":
            return [(s[0], s[1], s[2]) for s in all_sources if s[3]]
        else:
            # Filter to specific source
            for s in all_sources:
                if s[0] == self.source:
                    return [(s[0], s[1], s[2])]
            return []

    def _process_source(self, source_name: str, session) -> list:
        """Process a single source: fetch, parse, collect records."""
        parser = self.registry.get_parser(source_name, session)
        records = []
        source_cfg = self.registry.sources[source_name]["config"]

        # Exchange sources: iterate over endpoints
        if source_cfg.get("category") == "exchange":
            for ep_name, ep_cfg in source_cfg.get("endpoints", {}).items():
                if not ep_cfg.get("enabled", True):
                    continue
                url = ep_cfg.get("url", "")
                context = {
                    "data_type": ep_cfg.get("data_type", "daily_kline"),
                    "symbol": ep_cfg.get("variety", "unknown"),
                }
                ep_records = parser.fetch_and_parse(url, context)
                records.extend(ep_records)

        # Industry sources: iterate over indicators
        elif source_cfg.get("category") in ("industry", "industry_news", "government_stats"):
            for ind_code, ind_cfg in source_cfg.get("indicators", {}).items():
                if not ind_cfg.get("enabled", False):
                    continue
                url = ind_cfg.get("url_pattern", "")
                if "{date}" in url:
                    url = url.replace("{date}", datetime.now().strftime("%Y%m%d"))
                context = {
                    "indicator_code": ind_code,
                    "indicator_name": ind_cfg.get("name_cn", ""),
                    "unit": ind_cfg.get("unit", ""),
                    "url": url,
                }
                ind_records = parser.fetch_and_parse(url, context)
                records.extend(ind_records)

        # Store results
        self.results.append({
            "source": source_name,
            "records": len(records),
            "dry_run": self.dry_run,
        })

        return records

    def _detect_table(self, source_name: str, records: list) -> str:
        """Detect the appropriate table for records from a source."""
        if not records:
            return "daily_kline"
        first = records[0]
        if "s_open" in first or "open" in first:
            return "daily_kline"
        if "long_pos" in first or "long_position" in first:
            return "position_ranking"
        if "warrant_reg" in first or "registration_amount" in first:
            return "warrant_registration"
        if "ind_code" in first and "msteel" in str(first.get("ind_code", "")).lower():
            return "msteel_fundamental"
        if "ind_code" in first and "customs" in str(first.get("ind_code", "")).lower():
            return "customs_fundamental"
        if "ind_code" in first:
            return "industry_fundamental"
        return "daily_kline"

    def _save_csv(self, records: list, source_name: str) -> str:
        """Save records to CSV file."""
        if not records:
            return ""
        from site_parser_layer import OUTPUT_DIR
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{source_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = OUTPUT_DIR / filename
        import csv
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        return str(path)


# =============================================================================
# 3. CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="DSHB Extended Multi-Source Crawler Framework (P026)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-sources
  %(prog)s --source shfe --dry-run
  %(prog)s --source 100ppi --dry-run
  %(prog)s --source mysteel --dry-run
  %(prog)s --source all --dry-run --selftest
        """
    )
    parser.add_argument("--source", default="all",
                        choices=["shfe", "dce", "100ppi", "mysteel", "customs", "all"],
                        help="Data source to crawl (default: all)")
    parser.add_argument("--dry-run", action="store_true", default=None,
                        help="Dry-run mode: no HTTP requests (default: True)")
    parser.add_argument("--live", action="store_true",
                        help="Live mode: actual HTTP requests (requires dual-key flags)")
    parser.add_argument("--rate-limit", type=float, default=None,
                        help="Minimum seconds between requests (min 3.0, default: 3.0)")
    parser.add_argument("--db-path", default=None,
                        help="SQLite database path (default: data/factor_data.db)")
    parser.add_argument("--list-sources", action="store_true",
                        help="List available data sources")
    parser.add_argument("--selftest", action="store_true",
                        help="Run self-test of all modules")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / f"crawler_run_{datetime.now().strftime('%Y%m%d')}.log"),
        ]
    )

    print("=" * 60)
    print(f"DSHB Extended Multi-Source Crawler Framework")
    print(f"Task: {TASK_ID}")
    print(f"Version: {VERSION}")
    print(f"Constraints: {len(CONSTRAINTS)} rules enforced")
    print("=" * 60)

    # Handle --list-sources
    if args.list_sources:
        registry = SourceRegistry()
        print(f"\n{'Source':<12} {'Name':<35} {'Category':<15} {'Enabled':<8}")
        print("-" * 75)
        for name, full_name, category, enabled in registry.list_sources():
            print(f"{name:<12} {full_name:<35} {category:<15} {'YES' if enabled else 'NO':<8}")
        return

    # Handle --selftest
    if args.selftest:
        print("\nRunning self-tests for all modules...\n")
        import base_request_layer
        base_request_layer.selftest()
        print()
        import site_parser_layer
        site_parser_layer.selftest()
        print()
        import field_mapping_layer
        field_mapping_layer.selftest()
        print()
        import storage_layer
        storage_layer.selftest()
        print("\n" + "=" * 60)
        print("ALL MODULE SELF-TESTS PASSED")
        print("=" * 60)
        return

    # Determine dry_run mode
    dry_run = True
    if args.live:
        # Check dual-key flags
        key_a = CONFIG.get("global", {}).get("dual_key_a", "NOT_FOUND")
        key_b = CONFIG.get("global", {}).get("dual_key_b", "NOT_FOUND")
        if key_a != "FOUND" or key_b != "FOUND":
            print("WARNING: Dual-key flags not found. Running in dry-run mode.")
            print(f"  Key A: {key_a}, Key B: {key_b}")
            dry_run = True
        else:
            dry_run = False
    elif args.dry_run is not None:
        dry_run = args.dry_run

    # Run orchestrator
    orchestrator = CrawlerOrchestrator(
        source=args.source,
        dry_run=dry_run,
        rate_limit=args.rate_limit,
        db_path=args.db_path,
    )
    result = orchestrator.run()

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Crawler Run Complete")
    print(f"{'=' * 60}")
    print(f"Mode: {'DRY-RUN' if result['dry_run'] else 'LIVE'}")
    print(f"Sources processed: {len(result['sources_processed'])}")
    print(f"Total records: {result['total_records']}")
    print(f"Total mapped: {result['total_mapped']}")
    print(f"Session stats: {json.dumps(result['session_stats'], indent=2)}")
    print(f"Results: {json.dumps(result['results'], indent=2)}")

    # Write summary to JSON
    summary_path = ARCHIVE_DIR / "logs" / f"crawler_run_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()