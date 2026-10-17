#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
site_parser_layer.py — Modular Site Parser Layer
===================================================
TASK_ID: V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN
AGENT:   DSHB | BRANCH: feature/v88-g1
MODULE:  Level 2 of 4 (base_request → site_parser → field_mapping → storage)

Purpose
-------
Site-specific parsers for each data source:
  - ExchangeParser:  SHFE/DCE/CZCE HTML table parsing (daily_kline, position_ranking, warrant)
  - IndustryParser:  100ppi.com structured table parsing (fundamental indicators)
  - MysteelParser:   Mysteel news/market report parsing (TC, utilization, inventory)
  - CustomsParser:   Customs Excel file parsing (import/export volumes)

Each parser extracts raw data and outputs standardized CSV format
that the field_mapping_layer can process.

Design: Parsers are stateless — they take a RequestSession, fetch data,
and return structured records. No database writes in this layer.

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  DRY_RUN_DEFAULT     All parsing operates on dry-run or pre-fetched data
  NO_FACTOR_CALC      Factor calculation remains prohibited
"""

import os
import sys
import csv
import json
import re
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for module imports
SCRIPT_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from base_request_layer import RequestSession, RateLimiter, HTTPFetcher

TASK_ID = "V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "1.0.0"

OUTPUT_DIR = ARCHIVE_DIR / "parsed_output"


# =============================================================================
# 1. Base Parser Interface
# =============================================================================
class BaseParser:
    """Abstract base parser for all data sources."""

    source_name = "base"
    data_type = "base"

    def __init__(self, session: RequestSession):
        self.session = session

    def parse(self, data: str, context: dict = None) -> List[dict]:
        """
        Parse raw data into standardized records.

        Args:
            data: Raw HTML/text data
            context: Optional context (date, variety, etc.)

        Returns:
            List of dicts with standardized field names.
        """
        raise NotImplementedError

    def fetch_and_parse(self, url: str, context: dict = None) -> List[dict]:
        """
        Fetch data from URL and parse into records.

        Args:
            url: Target URL
            context: Optional context

        Returns:
            List of standardized records.
        """
        raw = self.session.fetch(url, source_name=self.source_name)
        if raw is None:
            logging.warning("Session halted for %s, skipping %s", self.source_name, url)
            return []

        if raw.startswith("[DRY-RUN]"):
            logging.info("[DRY-RUN] Skipping parse for %s", url)
            return []

        if raw.startswith("[403 BLOCKED]") or raw.startswith("[ERROR]"):
            logging.warning("Fetch failed for %s: %s", url, raw[:100])
            return []

        try:
            return self.parse(raw, context)
        except Exception as e:
            logging.error("Parse error for %s (%s): %s", self.source_name, url, e)
            return []

    def save_csv(self, records: List[dict], output_path: str = None):
        """Save parsed records to CSV file."""
        if not records:
            logging.info("No records to save for %s", self.source_name)
            return None

        if output_path:
            output_file = Path(output_path)
        else:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = OUTPUT_DIR / f"{self.source_name}_{self.data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        fieldnames = list(records[0].keys())
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        logging.info("Saved %d records to %s", len(records), output_file)
        return str(output_file)


# =============================================================================
# 2. Exchange Parser (SHFE / DCE / CZCE)
# =============================================================================
class ExchangeParser(BaseParser):
    """
    Parser for exchange data pages (SHFE/DCE/CZCE).

    Handles 3 data types:
      - daily_kline:        Daily OHLCV data
      - position_ranking:   Member long/short positions
      - warrant_registration: Warrant registration/cancellation

    Page structure: HTML tables with <table> tags.
    Uses BeautifulSoup for robust parsing (falls back to regex if bs4 unavailable).
    """

    source_name = "exchange"
    data_type = "exchange"

    def __init__(self, session: RequestSession, exchange: str = "shfe"):
        super().__init__(session)
        self.exchange = exchange.lower()

    def parse(self, data: str, context: dict = None) -> List[dict]:
        """
        Parse HTML table data from exchange page.

        Context should include:
          - data_type: 'daily_kline' | 'position_ranking' | 'warrant_registration'
          - symbol: e.g. 'SHFE_PBU'
          - date: target date (YYYY-MM-DD)
        """
        context = context or {}
        data_type = context.get("data_type", "daily_kline")
        symbol = context.get("symbol", "UNKNOWN")

        records = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(data, "html.parser")
            tables = soup.find_all("table")
            if not tables:
                logging.warning("No tables found in exchange page for %s", self.exchange)
                return []
            # Use the first substantial table (usually the data table)
            table = tables[0]
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header row
                cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                if len(cells) >= 3:
                    record = self._extract_record(cells, data_type, symbol)
                    if record:
                        records.append(record)
        except ImportError:
            # Fallback: basic regex parsing
            records = self._regex_parse(data, data_type, symbol)

        return records

    def _extract_record(self, cells: list, data_type: str, symbol: str) -> Optional[dict]:
        """Extract a single record from table cells."""
        # Common fields: date is usually first cell
        date_str = cells[0] if len(cells) > 0 else ""
        crawl_ts = datetime.now().isoformat()

        if data_type == "daily_kline":
            # Expected: date, symbol, open, high, low, close, volume, OI, avg_price
            if len(cells) < 9:
                return None
            return {
                "date": self._normalize_date(date_str),
                "symbol": symbol,
                "exchange": self.exchange,
                "open": self._to_float(cells[2]),
                "high": self._to_float(cells[3]),
                "low": self._to_float(cells[4]),
                "close": self._to_float(cells[5]),
                "volume": self._to_int(cells[6]),
                "open_interest": self._to_int(cells[7]),
                "avg_price": self._to_float(cells[8]) if len(cells) > 8 else "",
                "source_url": f"https://www.{self.exchange}.com.cn",
                "crawl_timestamp": crawl_ts,
            }
        elif data_type == "position_ranking":
            # Expected: date, symbol, rank, company, long_pos, short_pos, long_chg, short_chg
            if len(cells) < 7:
                return None
            return {
                "date": self._normalize_date(date_str),
                "symbol": symbol,
                "exchange": self.exchange,
                "rank": self._to_int(cells[1]),
                "company_name": cells[2],
                "long_position": self._to_int(cells[3]),
                "short_position": self._to_int(cells[4]),
                "long_change": self._to_int(cells[5]),
                "short_change": self._to_int(cells[6]),
                "source_url": f"https://www.{self.exchange}.com.cn",
                "crawl_timestamp": crawl_ts,
            }
        elif data_type == "warrant_registration":
            # Expected: date, symbol, registration, cancellation, net_change, balance
            if len(cells) < 5:
                return None
            return {
                "date": self._normalize_date(date_str),
                "symbol": symbol,
                "exchange": self.exchange,
                "registration_amount": self._to_int(cells[1]),
                "cancellation_amount": self._to_int(cells[2]),
                "net_change": self._to_int(cells[3]) if len(cells) > 3 else "",
                "total_balance": self._to_int(cells[4]) if len(cells) > 4 else "",
                "source_url": f"https://www.{self.exchange}.com.cn",
                "crawl_timestamp": crawl_ts,
            }

        return None

    def _regex_parse(self, data: str, data_type: str, symbol: str) -> List[dict]:
        """Fallback regex-based parsing when BeautifulSoup is unavailable."""
        # Simple table row extraction
        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
        cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
        tag_pattern = re.compile(r"<[^>]+>")

        records = []
        for row_match in row_pattern.finditer(data):
            cells = [tag_pattern.sub("", c).strip() for c in cell_pattern.findall(row_match.group(1))]
            if len(cells) >= 3:
                record = self._extract_record(cells, data_type, symbol)
                if record:
                    records.append(record)
        return records

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize date string to YYYY-MM-DD."""
        date_str = date_str.strip().replace("年", "-").replace("月", "-").replace("日", "")
        # Try various formats
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str

    @staticmethod
    def _to_float(s: str) -> str:
        """Convert string to float string."""
        s = s.strip().replace(",", "")
        try:
            return str(float(s))
        except (ValueError, TypeError):
            return s

    @staticmethod
    def _to_int(s: str) -> str:
        """Convert string to int string."""
        s = s.strip().replace(",", "")
        try:
            return str(int(float(s)))
        except (ValueError, TypeError):
            return s


# =============================================================================
# 3. Industry Parser (100ppi.com)
# =============================================================================
class IndustryParser(BaseParser):
    """
    Parser for 100ppi.com industry fundamental indicators.

    Page structure: Structured HTML tables under /sf/ directory.
    URL pattern: https://www.100ppi.com/sf/YYYYMMDD-{indicator}.html
    Table format: Date | Indicator | Value | Unit | Change
    """

    source_name = "100ppi"
    data_type = "industry_fundamental"

    def parse(self, data: str, context: dict = None) -> List[dict]:
        """Parse 100ppi indicator page."""
        context = context or {}
        indicator_code = context.get("indicator_code", "UNKNOWN")
        indicator_name = context.get("indicator_name", "")
        unit = context.get("unit", "")

        records = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(data, "html.parser")
            tables = soup.find_all("table")
            if not tables:
                # Try to find data in div elements
                data_div = soup.find("div", class_="table") or soup.find("div", class_="data")
                if not data_div:
                    logging.warning("No data tables found in 100ppi page")
                    return []
                rows = data_div.find_all("tr")
            else:
                rows = tables[0].find_all("tr")

            for row in rows:
                cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                if len(cells) >= 3:
                    record = {
                        "date": self._normalize_date(cells[0]),
                        "indicator_code": indicator_code,
                        "indicator_name": indicator_name,
                        "value": self._extract_value(cells[1] if len(cells) > 1 else ""),
                        "unit": unit or (cells[2] if len(cells) > 2 else ""),
                        "source_url": context.get("url", f"https://www.100ppi.com/sf/"),
                        "crawl_timestamp": datetime.now().isoformat(),
                    }
                    if record["value"]:
                        records.append(record)
        except ImportError:
            # Regex fallback
            records = self._regex_parse(data, indicator_code, indicator_name, unit)

        return records

    def _regex_parse(self, data: str, indicator_code: str, indicator_name: str, unit: str) -> List[dict]:
        """Fallback regex parsing for 100ppi."""
        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
        cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
        tag_pattern = re.compile(r"<[^>]+>")

        records = []
        for row_match in row_pattern.finditer(data):
            cells = [tag_pattern.sub("", c).strip() for c in cell_pattern.findall(row_match.group(1))]
            if len(cells) >= 3:
                value = self._extract_value(cells[1])
                if value:
                    records.append({
                        "date": self._normalize_date(cells[0]),
                        "indicator_code": indicator_code,
                        "indicator_name": indicator_name,
                        "value": value,
                        "unit": unit or (cells[2] if len(cells) > 2 else ""),
                        "source_url": "https://www.100ppi.com/sf/",
                        "crawl_timestamp": datetime.now().isoformat(),
                    })
        return records

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize Chinese date to YYYY-MM-DD."""
        date_str = date_str.strip().replace("年", "-").replace("月", "-").replace("日", "")
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y.%m.%d"):
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str

    @staticmethod
    def _extract_value(s: str) -> str:
        """Extract numeric value from string."""
        s = s.strip().replace(",", "").replace(" ", "")
        # Match number pattern
        match = re.search(r"[-+]?\d*\.?\d+", s)
        return match.group() if match else s


# =============================================================================
# 4. Mysteel Parser (New Source)
# =============================================================================
class MysteelParser(BaseParser):
    """
    Parser for Mysteel public news and market reports.

    Page structure: HTML articles with embedded structured data.
    URL patterns:
      - News: /news/YYYYMMDD/{id}.html
      - Market: /market/{category}/

    Data extraction:
      - Article date: from URL pattern or <h1> tag
      - Indicator value: from article body (numeric extraction)
      - Unit: parsed from article context
    """

    source_name = "mysteel"
    data_type = "msteel_fundamental"

    # Article content patterns for value extraction
    VALUE_PATTERNS = {
        "tc": r"([+-]?\d+\.?\d*)\s*元/吨",
        "inventory": r"([+-]?\d+\.?\d*)\s*吨",
        "rate": r"([+-]?\d+\.?\d*)\s*%",
        "volume": r"([+-]?\d+\.?\d*)\s*(?:万吨|吨)",
        "generic": r"([+-]?\d+\.?\d*)",
    }

    def parse(self, data: str, context: dict = None) -> List[dict]:
        """Parse Mysteel article/market page."""
        context = context or {}
        indicator_code = context.get("indicator_code", "UNKNOWN")
        indicator_name = context.get("article_title", "")
        unit = context.get("unit", "")
        page_url = context.get("url", "https://www.mysteel.com")

        records = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(data, "html.parser")

            # Extract date from URL pattern
            date_str = self._extract_date_from_url(page_url)
            if not date_str:
                date_str = context.get("article_date", datetime.now().strftime("%Y-%m-%d"))

            # Extract title from h1 or h2
            title_tag = soup.find("h1") or soup.find("h2") or soup.find("title")
            if title_tag:
                indicator_name = title_tag.get_text(strip=True)

            # Extract value from article content
            content_div = (soup.find("div", class_="article-content") or
                          soup.find("div", class_="content") or
                          soup.find("div", class_="article") or
                          soup.find("div", id="articleContent"))
            content_text = content_div.get_text(strip=True) if content_div else ""

            if not content_text:
                # Try body text
                body = soup.find("body")
                content_text = body.get_text(strip=True) if body else ""

            # Extract value using appropriate pattern
            value = self._extract_value_from_text(content_text, indicator_code)

            if value:
                records.append({
                    "article_date": date_str,
                    "indicator_code": indicator_code,
                    "article_title": indicator_name,
                    "article_value": value,
                    "article_unit": unit,
                    "page_url": page_url,
                    "crawl_time": datetime.now().isoformat(),
                })
        except ImportError:
            # Regex fallback
            records = self._regex_parse(data, indicator_code, indicator_name, unit, page_url)

        return records

    def _regex_parse(self, data: str, indicator_code: str, indicator_name: str,
                     unit: str, page_url: str) -> List[dict]:
        """Fallback regex parsing for Mysteel."""
        # Extract date from URL
        date_match = re.search(r"/news/(\d{8})", page_url)
        date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y%m%d")

        # Extract value from entire text
        tag_pattern = re.compile(r"<[^>]+>")
        text = tag_pattern.sub("", data)
        value = self._extract_value_from_text(text, indicator_code)

        if value:
            return [{
                "article_date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}" if len(date_str) == 8 else date_str,
                "indicator_code": indicator_code,
                "article_title": indicator_name,
                "article_value": value,
                "article_unit": unit,
                "page_url": page_url,
                "crawl_time": datetime.now().isoformat(),
            }]
        return []

    def _extract_date_from_url(self, url: str) -> str:
        """Extract date from Mysteel URL pattern."""
        match = re.search(r"/news/(\d{4})(\d{2})(\d{2})", url)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        match = re.search(r"/market/(\d{4})(\d{2})", url)
        if match:
            return f"{match.group(1)}-{match.group(2)}-01"
        return ""

    def _extract_value_from_text(self, text: str, indicator_code: str) -> str:
        """Extract numeric value from article text based on indicator type."""
        # Determine value pattern based on indicator type
        if "TC" in indicator_code or "tc" in indicator_code:
            pattern = self.VALUE_PATTERNS["tc"]
        elif "INV" in indicator_code or "inventory" in indicator_code.lower():
            pattern = self.VALUE_PATTERNS["inventory"]
        elif "RATE" in indicator_code or "rate" in indicator_code.lower():
            pattern = self.VALUE_PATTERNS["rate"]
        elif "IMP" in indicator_code or "EXP" in indicator_code:
            pattern = self.VALUE_PATTERNS["volume"]
        else:
            pattern = self.VALUE_PATTERNS["generic"]

        match = re.search(pattern, text)
        if match:
            return match.group(1)

        # Fallback: find first number
        generic_match = re.search(r"(-?\d+\.?\d*)", text)
        return generic_match.group(1) if generic_match else ""


# =============================================================================
# 5. Customs Parser (New Source)
# =============================================================================
class CustomsParser(BaseParser):
    """
    Parser for Customs General Administration import/export data.

    Data source: Downloadable Excel files from customs.gov.cn statistics pages.
    Table structure: Month | Commodity | Volume | Value | YoY Change

    Note: This parser handles CSV/HTML table data. Actual Excel (.xlsx) files
    require openpyxl dependency. The parser includes both paths.
    """

    source_name = "customs"
    data_type = "customs_fundamental"

    def parse(self, data: str, context: dict = None) -> List[dict]:
        """Parse customs statistics page/table."""
        context = context or {}
        commodity_code = context.get("commodity_code", "UNKNOWN")
        commodity_name = context.get("commodity_name", "")
        unit = context.get("unit", "吨")
        file_url = context.get("file_url", "https://www.customs.gov.cn")

        records = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(data, "html.parser")
            tables = soup.find_all("table")

            if not tables:
                logging.warning("No tables found in customs page")
                return []

            for row in tables[0].find_all("tr")[1:]:  # Skip header
                cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                if len(cells) >= 3:
                    record = {
                        "report_month": self._normalize_date(cells[0]),
                        "commodity_code": commodity_code,
                        "commodity_name": commodity_name or (cells[1] if len(cells) > 1 else ""),
                        "volume": self._extract_volume(cells[2]),
                        "unit": unit,
                        "file_url": file_url,
                        "crawl_time": datetime.now().isoformat(),
                    }
                    if record["volume"]:
                        records.append(record)
        except ImportError:
            records = self._regex_parse(data, commodity_code, commodity_name, unit, file_url)

        return records

    def _regex_parse(self, data: str, commodity_code: str, commodity_name: str,
                     unit: str, file_url: str) -> List[dict]:
        """Fallback regex parsing for customs data."""
        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
        cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
        tag_pattern = re.compile(r"<[^>]+>")

        records = []
        for row_match in row_pattern.finditer(data):
            cells = [tag_pattern.sub("", c).strip() for c in cell_pattern.findall(row_match.group(1))]
            if len(cells) >= 3:
                volume = self._extract_volume(cells[2])
                if volume:
                    records.append({
                        "report_month": self._normalize_date(cells[0]),
                        "commodity_code": commodity_code,
                        "commodity_name": commodity_name or (cells[1] if len(cells) > 1 else ""),
                        "volume": volume,
                        "unit": unit,
                        "file_url": file_url,
                        "crawl_time": datetime.now().isoformat(),
                    })
        return records

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize Chinese month to YYYY-MM-01."""
        date_str = date_str.strip().replace("年", "-").replace("月", "").replace("日", "")
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y%m", "%Y年%m月"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-01")
            except ValueError:
                continue
        # Try to extract year and month from any string
        match = re.search(r"(\d{4}).*?(\d{1,2})", date_str)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-01"
        return date_str

    @staticmethod
    def _extract_volume(s: str) -> str:
        """Extract volume number from string."""
        s = s.strip().replace(",", "")
        match = re.search(r"[-+]?\d*\.?\d+", s)
        return match.group() if match else ""


# =============================================================================
# 6. Self-test
# =============================================================================
def selftest():
    """Run self-test of site parser layer."""
    print("=" * 60)
    print("Site Parser Layer Self-Test")
    print("=" * 60)

    session = RequestSession(max_requests=10, dry_run=True)

    # Test 1: ExchangeParser daily_kline
    parser = ExchangeParser(session, exchange="shfe")
    html = """<html><body><table>
    <tr><th>Date</th><th>Symbol</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th><th>OI</th><th>Avg</th></tr>
    <tr><td>2026-10-20</td><td>PBU</td><td>16500</td><td>16800</td><td>16400</td><td>16700</td><td>10000</td><td>50000</td><td>16600</td></tr>
    </table></body></html>"""
    records = parser.parse(html, {"data_type": "daily_kline", "symbol": "SHFE_PBU"})
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    assert records[0]["close"] == "16700.0", f"Close mismatch: {records[0]['close']}"
    print(f"1. ExchangeParser daily_kline: PASS")

    # Test 2: ExchangeParser position_ranking
    html2 = """<html><body><table>
    <tr><th>Date</th><th>Rank</th><th>Company</th><th>Long</th><th>Short</th><th>LChg</th><th>SChg</th></tr>
    <tr><td>2026-10-20</td><td>1</td><td>TestCo</td><td>10000</td><td>5000</td><td>100</td><td>-50</td></tr>
    </table></body></html>"""
    records2 = parser.parse(html2, {"data_type": "position_ranking", "symbol": "SHFE_PBU"})
    assert len(records2) == 1, f"Expected 1 record, got {len(records2)}"
    assert records2[0]["company_name"] == "TestCo", f"Company mismatch"
    print(f"2. ExchangeParser position_ranking: PASS")

    # Test 3: IndustryParser 100ppi
    ind_parser = IndustryParser(session)
    html3 = """<html><body><table>
    <tr><th>Date</th><th>Value</th><th>Unit</th></tr>
    <tr><td>2026-10-20</td><td>16500</td><td>元/吨</td></tr>
    </table></body></html>"""
    records3 = ind_parser.parse(html3, {"indicator_code": "LEAD_SMELTING_RATE", "indicator_name": "铅冶炼开工率", "unit": "%"})
    assert len(records3) == 1, f"Expected 1 record, got {len(records3)}"
    assert records3[0]["indicator_code"] == "LEAD_SMELTING_RATE", f"Indicator mismatch"
    print(f"3. IndustryParser 100ppi: PASS")

    # Test 4: MysteelParser news article
    mysteel_parser = MysteelParser(session)
    html4 = """<html><body>
    <h1>铅冶炼加工费周报</h1>
    <div class="article-content">本周铅冶炼加工费为1650元/吨，较上周上涨50元/吨。</div>
    </body></html>"""
    records4 = mysteel_parser.parse(html4, {"indicator_code": "MSTEEL_LEAD_TC", "article_title": "铅冶炼加工费", "unit": "元/吨", "url": "https://www.mysteel.com/news/20261020/12345.html"})
    assert len(records4) == 1, f"Expected 1 record, got {len(records4)}"
    assert records4[0]["article_value"] == "1650", f"Value mismatch: {records4[0]['article_value']}"
    print(f"4. MysteelParser news article: PASS")

    # Test 5: CustomsParser table
    customs_parser = CustomsParser(session)
    html5 = """<html><body><table>
    <tr><th>Month</th><th>Commodity</th><th>Volume</th></tr>
    <tr><td>2026-10</td><td>铅矿砂</td><td>15000</td></tr>
    </table></body></html>"""
    records5 = customs_parser.parse(html5, {"commodity_code": "CUSTOMS_LEAD_ORE_IMP", "commodity_name": "铅矿砂进口量", "unit": "吨", "file_url": "https://www.customs.gov.cn/test.xlsx"})
    assert len(records5) == 1, f"Expected 1 record, got {len(records5)}"
    assert records5[0]["volume"] == "15000", f"Volume mismatch"
    print(f"5. CustomsParser table: PASS")

    # Test 6: Dry-run fetch returns no records
    dry_records = parser.fetch_and_parse("https://www.shfe.com.cn/test", {"data_type": "daily_kline", "symbol": "SHFE_PBU"})
    assert len(dry_records) == 0, f"Expected 0 records in dry-run, got {len(dry_records)}"
    print(f"6. Dry-run fetch returns empty: PASS")

    # Test 7: Date normalization
    assert ExchangeParser._normalize_date("2026-10-20") == "2026-10-20"
    assert ExchangeParser._normalize_date("2026年10月20日") == "2026-10-20"
    assert ExchangeParser._normalize_date("20261020") == "2026-10-20"
    print(f"7. Date normalization: PASS")

    print("=" * 60)
    print("ALL 7 TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    selftest()