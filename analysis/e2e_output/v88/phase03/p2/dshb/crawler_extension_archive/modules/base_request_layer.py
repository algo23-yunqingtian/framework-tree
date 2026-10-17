#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base_request_layer.py — Modular Base Request Layer
====================================================
TASK_ID: V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN
AGENT:   DSHB | BRANCH: feature/v88-g1
MODULE:  Level 1 of 4 (base_request → site_parser → field_mapping → storage)

Purpose
-------
Base HTTP request layer providing:
  - RateLimiter with hard floor (3.0s minimum)
  - HTTPFetcher with dry-run guard, UA rotation, retry logic
  - Compliance enforcement (no concurrent requests, no paid API)
  - Audit logging interface

Design: This module replaces the embedded RateLimiter + HTTPFetcher from
crawler_main.py (P023) with a standalone, reusable module that can be
imported by site-specific parser layers.

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  NO_OVERWRITE        Never truncate or overwrite existing files
  APPEND_ONLY         Data is append-only
  DRY_RUN_DEFAULT     No HTTP requests unless explicitly enabled
  RATE_LIMIT          Minimum 3.0 seconds between requests
  NO_CONCURRENT       Sequential only; no threading, no asyncio
  NO_FACTOR_CALC      Factor calculation remains prohibited
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# =============================================================================
# 0. Environment setup
# =============================================================================
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

TASK_ID = "V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN"
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

# Hard floor for rate limiting
MIN_RATE_LIMIT_SECONDS = 3.0

# Audit log path
AUDIT_LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "audit_log.jsonl"


# =============================================================================
# 1. RateLimiter
# =============================================================================
class RateLimiter:
    """Enforce minimum delay between HTTP requests (hard floor: 3.0 seconds)."""

    def __init__(self, min_interval: float = MIN_RATE_LIMIT_SECONDS):
        self.min_interval = max(min_interval, MIN_RATE_LIMIT_SECONDS)
        self._last_request_time = 0.0
        self.request_count = 0

    def wait(self):
        """Block until minimum interval has elapsed since last request."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logging.debug("RateLimiter: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()
        self.request_count += 1

    def configure(self, new_interval: float):
        """Update minimum interval (minimum 3.0 seconds enforced)."""
        self.min_interval = max(new_interval, MIN_RATE_LIMIT_SECONDS)

    def reset(self):
        """Reset request count (call between sessions)."""
        self.request_count = 0
        self._last_request_time = 0.0


# =============================================================================
# 2. HTTPFetcher
# =============================================================================
class HTTPFetcher:
    """
    HTTP fetcher with:
      - Dry-run guard (no actual requests by default)
      - User-Agent rotation (4 UA pool)
      - Retry with backoff (403→10s, 429→30s)
      - Timeout enforcement (30s default)
      - Audit logging
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self, rate_limiter: RateLimiter, dry_run: bool = True,
                 max_retries: int = 3, timeout: int = 30):
        self.rate_limiter = rate_limiter
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.timeout = timeout
        self._audit_log_path = AUDIT_LOG_PATH
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_headers(self) -> dict:
        """Generate request headers with random UA rotation."""
        ua = self.USER_AGENTS[hash(datetime.now()) % len(self.USER_AGENTS)]
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def fetch(self, url: str, params: dict = None, source_name: str = "unknown") -> str:
        """
        Fetch URL with dry-run guard, rate limiting, and retry logic.

        Args:
            url: Target URL
            params: Optional query parameters
            source_name: Source identifier for audit logging

        Returns:
            Response text or dry-run placeholder string.
        """
        import urllib.request
        import urllib.error
        from urllib.parse import urlencode

        # Dry-run mode: no actual HTTP request
        if self.dry_run:
            logging.info("[DRY-RUN] Would fetch: %s (source: %s)", url, source_name)
            self._audit_log(source_name, url, "DRY_RUN", "no_request")
            return f"[DRY-RUN] Would fetch: {url}"

        for attempt in range(1, self.max_retries + 1):
            self.rate_limiter.wait()
            headers = self._get_headers()
            full_url = url
            if params:
                full_url = url + ("?" if "?" not in url else "&") + urlencode(params)

            try:
                req = urllib.request.Request(full_url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                    # Try UTF-8, fallback to GBK (common for Chinese sites)
                    try:
                        text = body.decode("utf-8")
                    except UnicodeDecodeError:
                        text = body.decode("gbk", errors="replace")
                    self._audit_log(source_name, url, str(resp.status), "success")
                    return text

            except urllib.error.HTTPError as e:
                if e.code == 403:
                    logging.warning("[403] Blocked: %s (attempt %d/%d, source: %s)",
                                    url, attempt, self.max_retries, source_name)
                    self._audit_log(source_name, url, "403", "blocked")
                    if attempt < self.max_retries:
                        time.sleep(10)  # Extra backoff for 403
                        continue
                    return f"[403 BLOCKED] {url}"
                elif e.code == 429:
                    logging.warning("[429] Rate limited: %s (attempt %d/%d, source: %s)",
                                    url, attempt, self.max_retries, source_name)
                    self._audit_log(source_name, url, "429", "rate_limited")
                    time.sleep(30)  # Longer backoff for 429
                    continue
                else:
                    logging.error("HTTP %d: %s (source: %s)", e.code, url, source_name)
                    self._audit_log(source_name, url, str(e.code), "http_error")
                    return f"[HTTP {e.code}] {url}"
            except Exception as e:
                logging.warning("Fetch error: %s (attempt %d/%d, source: %s): %s",
                                url, attempt, self.max_retries, source_name, e)
                self._audit_log(source_name, url, "ERROR", str(e))
                if attempt < self.max_retries:
                    time.sleep(5)
                    continue
                return f"[ERROR] {url}: {e}"

        self._audit_log(source_name, url, "MAX_RETRIES", "max_retries_exceeded")
        return f"[MAX_RETRIES_EXCEEDED] {url}"

    def _audit_log(self, source_name: str, url: str, status: str, message: str):
        """Append audit record to JSONL log."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "source": source_name,
            "url": url,
            "status": status,
            "message": message,
            "task_id": TASK_ID,
        }
        try:
            with open(self._audit_log_path, "a", encoding="utf-8") as f:
                import json
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except (IOError, OSError) as e:
            logging.error("Audit log write failed: %s", e)

    def is_dry_run(self) -> bool:
        """Check if fetcher is in dry-run mode."""
        return self.dry_run


# =============================================================================
# 3. RequestSession (high-level interface)
# =============================================================================
class RequestSession:
    """
    High-level request session with session-level controls.

    Provides:
      - Maximum requests per session enforcement
      - Consecutive error tracking with auto-halt
      - Clean initialization for each crawl session
    """

    def __init__(self, max_requests: int = 100, max_consecutive_errors: int = 3,
                 rate_limit: float = MIN_RATE_LIMIT_SECONDS, dry_run: bool = True):
        self.rate_limiter = RateLimiter(rate_limit)
        self.fetcher = HTTPFetcher(self.rate_limiter, dry_run=dry_run)
        self.max_requests = max_requests
        self.max_consecutive_errors = max_consecutive_errors
        self.requests_made = 0
        self.consecutive_errors = 0
        self.halted = False
        self.halt_reason = None

    def should_proceed(self) -> bool:
        """Check if session should continue."""
        if self.halted:
            return False
        if self.requests_made >= self.max_requests:
            self.halted = True
            self.halt_reason = f"max_requests_exceeded ({self.max_requests})"
            logging.warning("Session halted: %s", self.halt_reason)
            return False
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.halted = True
            self.halt_reason = f"max_consecutive_errors ({self.max_consecutive_errors})"
            logging.warning("Session halted: %s", self.halt_reason)
            return False
        return True

    def fetch(self, url: str, source_name: str = "unknown") -> Optional[str]:
        """
        Fetch URL with session-level guards.

        Returns:
            Response text, or None if session should halt.
        """
        if not self.should_proceed():
            return None

        result = self.fetcher.fetch(url, source_name=source_name)
        self.requests_made += 1

        # Check for error markers
        if any(marker in result for marker in ["[ERROR]", "[403 BLOCKED]", "[HTTP"]):
            self.consecutive_errors += 1
        else:
            self.consecutive_errors = 0

        return result

    def get_session_stats(self) -> dict:
        """Return session statistics."""
        return {
            "requests_made": self.requests_made,
            "max_requests": self.max_requests,
            "consecutive_errors": self.consecutive_errors,
            "max_consecutive_errors": self.max_consecutive_errors,
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            "dry_run": self.fetcher.is_dry_run(),
            "rate_limit": self.rate_limiter.min_interval,
            "total_rate_limited_requests": self.rate_limiter.request_count,
        }


# =============================================================================
# 4. Self-test
# =============================================================================
def selftest():
    """Run self-test of base request layer."""
    print("=" * 60)
    print("Base Request Layer Self-Test")
    print("=" * 60)

    # Test 1: RateLimiter minimum enforcement
    rl = RateLimiter(1.0)
    assert rl.min_interval == MIN_RATE_LIMIT_SECONDS, "RateLimiter floor not enforced"
    print(f"1. RateLimiter min interval floor: PASS ({rl.min_interval}s)")

    # Test 2: RateLimiter configure
    rl2 = RateLimiter(3.0)
    rl2.configure(1.0)
    assert rl2.min_interval == MIN_RATE_LIMIT_SECONDS, "RateLimiter configure floor not enforced"
    print(f"2. RateLimiter configure floor: PASS ({rl2.min_interval}s)")

    # Test 3: HTTPFetcher dry-run
    fetcher = HTTPFetcher(RateLimiter(3.0), dry_run=True)
    result = fetcher.fetch("https://example.com/test", source_name="test_source")
    assert "[DRY-RUN]" in result, "Dry-run marker not in result"
    print(f"3. HTTPFetcher dry-run mode: PASS")

    # Test 4: RequestSession initialization
    session = RequestSession(max_requests=5, max_consecutive_errors=3, dry_run=True)
    assert session.should_proceed() == True, "Session should proceed initially"
    assert session.requests_made == 0, "Initial request count should be 0"
    print(f"4. RequestSession initialization: PASS")

    # Test 5: RequestSession max requests
    session2 = RequestSession(max_requests=0, dry_run=True)
    assert session2.should_proceed() == False, "Session should halt at max_requests=0"
    print(f"5. RequestSession max_requests halt: PASS")

    # Test 6: RequestSession dry-run fetch
    session3 = RequestSession(max_requests=10, dry_run=True)
    result3 = session3.fetch("https://example.com/test", source_name="test")
    assert result3 is not None, "Dry-run fetch should return result"
    assert session3.requests_made == 1, "Request count should be 1"
    print(f"6. RequestSession dry-run fetch: PASS")

    # Test 7: No concurrent imports (check our modules don't import threading/asyncio)
    # Use regex to match actual import statements, not comments/docstrings
    import re as _re
    forbidden_patterns = [
        _re.compile(r"^\s*import\s+threading\s*$", _re.MULTILINE),
        _re.compile(r"^\s*import\s+asyncio\s*$", _re.MULTILINE),
        _re.compile(r"^\s*from\s+threading\s+import", _re.MULTILINE),
        _re.compile(r"^\s*from\s+asyncio\s+import", _re.MULTILINE),
        _re.compile(r"^\s*from\s+concurrent\.futures\s+import", _re.MULTILINE),
        _re.compile(r"^\s*import\s+concurrent\.futures\s*$", _re.MULTILINE),
    ]
    found = False
    for fname in ["base_request_layer.py", "site_parser_layer.py", "field_mapping_layer.py", "storage_layer.py"]:
        try:
            with open(fname, "r", encoding="utf-8") as f:
                content = f.read()
            for pattern in forbidden_patterns:
                if pattern.search(content):
                    found = True
        except FileNotFoundError:
            pass
    assert not found, "Forbidden concurrent module imported in source code"
    print(f"7. No concurrent imports in source: PASS")

    print("=" * 60)
    print("ALL 7 TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    selftest()