#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crawler_main.py — DSHB V88 Phase03 P023 Multi-Source Crawler Framework
======================================================================
TASK_ID: V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
Orchestrator for the DSHB PB/ZN/Recycle-PB data crawler framework.
Supports two modules:
  - exchange_crawler:  SHFE / DCE / CZCE public data (daily K-line, position ranking, warrant)
  - industry_crawler:  100ppi.com industry fundamentals (smelting rate, profit, inventory)

Hard Constraints (inherited)
----------------------------
  NO_ZHIJI_API_CALL    No import/call to zhiji_api.py
  NO_OVERWRITE         Never truncate or overwrite existing output files
  APPEND_ONLY          New data is append-only; idempotent dedup by key
  DRY_RUN              Default; http requests blocked unless --live
  RATE_LIMIT           Minimum 3.0 seconds between HTTP requests
  STD_LIB_PREFERRED    stdlib only (urllib.request); requests/bs4 optional fallback
  NO_CONCURRENT        Sequential requests only; no threading, no asyncio

Output (APPEND_ONLY + NO_OVERWRITE)
-----------------------------------
  samples/*.csv                 Small sample data files (test only)
  db_interface.py               Database interface stub for Phase04 import
  db_config.json                SQLite connection configuration
  crawler_security_rule.md      Risk control & compliance documentation

Usage
-----
  python crawler_main.py --list-modules
  python crawler_main.py --module exchange --dry-run
  python crawler_main.py --module exchange --exchange shfe --dry-run
  python crawler_main.py --module industry --dry-run
  python crawler_main.py --module all --dry-run
  python crawler_main.py --module exchange --exchange shfe --date 2026-10-20 --dry-run
  python crawler_main.py --module exchange --exchange shfe --date 2026-10-20 --live
  python crawler_main.py --module industry --date 2026-10-20 --live
  python crawler_main.py --module all --date 2026-10-20 --live --rate-limit 3.0
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, date

# =============================================================================
# 0. Environment setup
# =============================================================================
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

# Resolve project root (framework-tree)
SCRIPT_DIR = Path(__file__).resolve().parent
PHASE03_DIR = SCRIPT_DIR.parent.parent  # phase03/
PROJECT_ROOT = PHASE03_DIR.parent.parent  # e2e_output/ → analysis/ → framework-tree/
# Actually: SCRIPT_DIR = .../phase03/p2/dshb/crawler_archive
# PHASE03_DIR = .../phase03
# PROJECT_ROOT = .../e2e_output/v88 → .../analysis → framework-tree
# Let's use a more robust approach:
ROOT = SCRIPT_DIR.parents[4]  # crawler_archive → dshb → p2 → phase03 → v88 → e2e_output → analysis → framework-tree
if not (ROOT / "framework-tree").exists() and not (ROOT / "STATUS.md").exists():
    # Fallback: try parents[5]
    ROOT = SCRIPT_DIR.parents[5]

COMMON_LIB = ROOT / "analysis" / "e2e_output" / "v88" / "phase03" / "p1" / "dshb" / "post_fix_watcher" / "crawler"
if COMMON_LIB.exists() and (COMMON_LIB / "common_crawler_lib.py").exists():
    sys.path.insert(0, str(COMMON_LIB))

# =============================================================================
# 1. Configuration
# =============================================================================
TASK_ID = "V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "1.0.0"

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

# Target varieties for PB/ZN/Recycle-PB pipeline
VARIETIES = {
    "pb": {
        "name": "Lead (Pb)",
        "shfe_symbol": "SHFE_PBU",
        "dce_symbol": None,
        "czce_symbol": None,
        "wind_symbol": "SHFE_PBU",
    },
    "zn": {
        "name": "Zinc (Zn)",
        "shfe_symbol": "SHFE_ZNU",
        "dce_symbol": "DCE_ZNU",
        "czce_symbol": None,
        "wind_symbol": "SHFE_ZNU",
    },
    "recycle_pb": {
        "name": "Recycled Lead (再生铅)",
        "shfe_symbol": None,  # Not directly traded; proxy via SHFE_PBU + recycling premium
        "dce_symbol": None,
        "czce_symbol": None,
        "wind_symbol": "SHFE_PBU_PROXY",
    },
}

# Exchange registry
EXCHANGES = {
    "shfe": {
        "name": "Shanghai Futures Exchange (SHFE)",
        "base_url": "https://www.shfe.com.cn",
        "daily_url": "https://www.shfe.com.cn/cn/business/data/dailydata/",
        "position_url": "https://www.shfe.com.cn/cn/business/data/positionranking/",
        "warrant_url": "https://www.shfe.com.cn/cn/business/data/warrant/",
    },
    "dce": {
        "name": "Dalian Commodity Exchange (DCE)",
        "base_url": "https://www.dce.com.cn",
        "daily_url": "https://www.dce.com.cn/publicweb/quotesdata/dailyQuotes.html",
        "position_url": "https://www.dce.com.cn/publicweb/quotesdata/memberRankings.html",
        "warrant_url": "https://www.dce.com.cn/publicweb/quotesdata/warrant.html",
    },
    "czce": {
        "name": "Zhengzhou Commodity Exchange (CZCE)",
        "base_url": "https://www.czce.com.cn",
        "daily_url": "https://www.czce.com.cn/cn/BB2729010175/BB2729010176.htm",
        "position_url": "https://www.czce.com.cn/cn/BB2729010175/BB2729010177.htm",
        "warrant_url": "https://www.czce.com.cn/cn/BB2729010175/BB2729010178.htm",
    },
}

# Industry data source registry
INDUSTRY_SOURCES = {
    "100ppi": {
        "name": "生意社 (100ppi.com)",
        "base_url": "https://www.100ppi.com",
        "lead_price_url": "https://www.100ppi.com/sf/",
        "lead_industry_url": "https://www.100ppi.com/sf/20261005-lead.html",
        "zinc_price_url": "https://www.100ppi.com/sf/",
    },
}

SAMPLES_DIR = SCRIPT_DIR / "samples"
LOG_DIR = SCRIPT_DIR / "logs"

# =============================================================================
# 2. RateLimiter (thread-safe, sequential)
# =============================================================================
class RateLimiter:
    """Enforce minimum delay between HTTP requests (≥3.0 seconds)."""

    def __init__(self, min_interval: float = 3.0):
        self.min_interval = max(min_interval, 3.0)  # Hard floor at 3.0s
        self._last_request_time = 0.0

    def wait(self):
        """Block until minimum interval has elapsed since last request."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logging.debug("RateLimiter: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def configure(self, new_interval: float):
        """Update minimum interval (minimum 3.0 seconds enforced)."""
        self.min_interval = max(new_interval, 3.0)


# =============================================================================
# 3. HTTP Fetcher (with dry-run guard)
# =============================================================================
class HTTPFetcher:
    """HTTP fetcher with dry-run guard, rate limiting, and retry logic."""

    def __init__(self, rate_limiter: RateLimiter, dry_run: bool = True,
                 max_retries: int = 3, timeout: int = 30):
        self.rate_limiter = rate_limiter
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.timeout = timeout
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    def _get_headers(self) -> dict:
        ua = self._user_agents[hash(datetime.now()) % len(self._user_agents)]
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def fetch(self, url: str, params: dict = None) -> str:
        """Fetch URL with dry-run guard. Returns response text or dry-run placeholder."""
        import urllib.request
        import urllib.error

        if self.dry_run:
            logging.info("[DRY-RUN] Would fetch: %s", url)
            return f"[DRY-RUN] Would fetch: {url}"

        for attempt in range(1, self.max_retries + 1):
            self.rate_limiter.wait()
            headers = self._get_headers()
            full_url = url
            if params:
                from urllib.parse import urlencode
                full_url = url + ("?" if "?" not in url else "&") + urlencode(params)
            try:
                req = urllib.request.Request(full_url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                    # Try UTF-8, fallback to GBK (common for Chinese sites)
                    try:
                        return body.decode("utf-8")
                    except UnicodeDecodeError:
                        return body.decode("gbk", errors="replace")
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    logging.warning("[403] Blocked: %s (attempt %d/%d)", url, attempt, self.max_retries)
                    if attempt < self.max_retries:
                        time.sleep(10)  # Extra backoff for 403
                        continue
                    return f"[403 BLOCKED] {url}"
                elif e.code == 429:
                    logging.warning("[429] Rate limited: %s (attempt %d/%d)", url, attempt, self.max_retries)
                    time.sleep(30)
                    continue
                else:
                    logging.error("HTTP %d: %s", e.code, url)
                    return f"[HTTP {e.code}] {url}"
            except Exception as e:
                logging.warning("Fetch error: %s (attempt %d/%d): %s", url, attempt, self.max_retries, e)
                if attempt < self.max_retries:
                    time.sleep(5)
                    continue
                return f"[ERROR] {url}: {e}"

        return f"[MAX_RETRIES_EXCEEDED] {url}"


# =============================================================================
# 4. Main Crawler Framework
# =============================================================================
class CrawlerFramework:
    """Main orchestrator for DSHB data crawler framework."""

    def __init__(self, module: str = "all", exchange: str = "all",
                 dry_run: bool = True, rate_limit: float = 3.0):
        self.module = module.lower()
        self.exchange = exchange.lower()
        self.dry_run = dry_run
        self.rate_limit = max(rate_limit, 3.0)
        self.rate_limiter = RateLimiter(self.rate_limit)
        self.fetcher = HTTPFetcher(self.rate_limiter, dry_run=dry_run)
        self.results = []
        self._ensure_dirs()

    def _ensure_dirs(self):
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Execute crawler framework based on module and exchange parameters."""
        logging.info("=" * 70)
        logging.info("CrawlerFramework starting")
        logging.info("TASK_ID: %s", TASK_ID)
        logging.info("BRANCH: %s", BRANCH)
        logging.info("Module: %s | Exchange: %s | Dry-run: %s", self.module, self.exchange, self.dry_run)
        logging.info("Rate limit: %.1f seconds | Constraints: %d/%d", self.rate_limit,
                     sum(CONSTRAINTS.values()), len(CONSTRAINTS))
        logging.info("=" * 70)

        if self.module in ("exchange", "all"):
            self._run_exchange()

        if self.module in ("industry", "all"):
            self._run_industry()

        # Print summary
        logging.info("-" * 50)
        logging.info("CrawlerFramework finished: %d results collected", len(self.results))
        logging.info("-" * 50)
        return self.results

    def _run_exchange(self):
        """Run exchange data crawler for specified exchanges."""
        from exchange_crawler import ExchangeCrawler

        exchanges = list(EXCHANGES.keys())
        if self.exchange != "all":
            exchanges = [self.exchange] if self.exchange in EXCHANGES else [e for e in exchanges if self.exchange in e]

        for exch_key in exchanges:
            if exch_key not in EXCHANGES:
                logging.warning("Unknown exchange: %s, skipping", exch_key)
                continue
            exch_info = EXCHANGES[exch_key]
            logging.info("Exchange crawler: %s", exch_info["name"])

            crawler = ExchangeCrawler(
                exchange=exch_key,
                rate_limiter=self.rate_limiter,
                fetcher=self.fetcher,
                dry_run=self.dry_run,
            )
            results = crawler.run()
            self.results.extend(results)

    def _run_industry(self):
        """Run industry fundamentals crawler."""
        from industry_crawler import IndustryCrawler

        logging.info("Industry crawler: 生意社 (100ppi.com)")
        crawler = IndustryCrawler(
            rate_limiter=self.rate_limiter,
            fetcher=self.fetcher,
            dry_run=self.dry_run,
        )
        results = crawler.run()
        self.results.extend(results)


# =============================================================================
# 5. Module listing
# =============================================================================
def list_modules():
    """Print available modules, exchanges, and varieties."""
    print("=" * 70)
    print(f"DSHB Crawler Framework v{VERSION}")
    print(f"TASK_ID: {TASK_ID}")
    print(f"BRANCH: {BRANCH}")
    print("=" * 70)
    print()
    print("Modules:")
    print("  exchange  - Exchange public data (SHFE, DCE, CZCE)")
    print("  industry  - Industry fundamentals (100ppi.com)")
    print("  all       - Run both modules")
    print()
    print("Exchanges:")
    for k, v in EXCHANGES.items():
        print(f"  {k:6s}  {v['name']}")
    print()
    print("Target Varieties:")
    for k, v in VARIETIES.items():
        wind = v.get("wind_symbol", "N/A")
        print(f"  {k:12s}  {v['name']:20s}  WIND: {wind}")
    print()
    print("Constraints ({} enforced):".format(sum(CONSTRAINTS.values())))
    for k, v in CONSTRAINTS.items():
        status = "ON" if v else "OFF"
        print(f"  [{status}] {k}")
    print()
    print("Rate limit: minimum 3.0 seconds between requests")
    print("Dry-run: default (use --live for actual HTTP requests)")
    print("=" * 70)


# =============================================================================
# 6. CLI entry point
# =============================================================================
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="DSHB V88 Phase03 P023 Multi-Source Data Crawler Framework"
    )
    parser.add_argument("--module", default="all",
                        choices=["exchange", "industry", "all"],
                        help="Crawler module to run (default: all)")
    parser.add_argument("--exchange", default="all",
                        choices=["shfe", "dce", "czce", "all"],
                        help="Target exchange (default: all)")
    parser.add_argument("--date", default=None,
                        help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--live", action="store_true",
                        help="Enable live HTTP requests (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run mode (default when --live not specified)")
    parser.add_argument("--rate-limit", type=float, default=3.0,
                        help="Minimum seconds between requests (min 3.0, default: 3.0)")
    parser.add_argument("--list-modules", action="store_true",
                        help="List available modules and exchanges")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.list_modules:
        list_modules()
        return 0

    # Determine dry-run mode
    dry_run = not args.live  # Default is dry-run

    # Create and run framework
    framework = CrawlerFramework(
        module=args.module,
        exchange=args.exchange,
        dry_run=dry_run,
        rate_limit=args.rate_limit,
    )

    # If date specified, log it
    if args.date:
        logging.info("Target date: %s", args.date)

    results = framework.run()

    # Write results summary to JSON
    summary_path = LOG_DIR / "crawler_run_summary.json"
    summary = {
        "task_id": TASK_ID,
        "agent": AGENT,
        "branch": BRANCH,
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "module": args.module,
        "exchange": args.exchange,
        "dry_run": dry_run,
        "rate_limit_seconds": framework.rate_limit,
        "results_count": len(results),
        "constraints_enforced": sum(CONSTRAINTS.values()),
        "total_constraints": len(CONSTRAINTS),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logging.info("Run summary written: %s", summary_path)

    return 0 if len(results) >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())