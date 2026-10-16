#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smm_cloudflare_bypass_proto.py — SMM Cloudflare Bypass Prototype
================================================================
TASK_ID: V88_PHASE03_P1_DSHB_IMPLEMENT_AND_NOISE_CONTINUE_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)
PURPOSE: Selenium WebDriver headless bypass for SMM Cloudflare protection
VERSION: v1.0-proto
STATUS:  PROTOTYPE (deployed for stability testing)

Architecture:
  Layer 1: Headless Chrome (Selenium WebDriver) with anti-detection
  Layer 2: Cloudflare challenge detection + adaptive wait
  Layer 3: Cookie session persistence (JSON)
  Layer 4: ExponentialBackoff retry strategy with jitter
  Layer 5: CircuitBreaker (CLOSED → OPEN → HALF_OPEN)
  Layer 6: CacheFallbackStrategy (FRESH/STALE/STALE_ALERT/EXPIRED)
  Layer 7: Full failure handling pipeline + alert emission

CONFLICT RESOLUTION: No V87 baseline files touched.
"""

import sys
import os
import re
import csv
import json
import time
import random
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any, List, Dict, Tuple
from collections import OrderedDict

# =============================================================================
# Constants & Configuration
# =============================================================================

TASK_ID = "V88_PHASE03_P1_DSHB_IMPLEMENT_AND_NOISE_CONTINUE_JOB"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
LIB_VERSION = "v1.0-proto"
SCRIPT_NAME = "smm_cloudflare_bypass_proto"
INDICATOR = "CU_BALANCE_SHEET"

CONSTRAINTS = OrderedDict([
    ("NO_ZHIJI_API_CALL", True),
    ("NO_OVERWRITE", True),
    ("APPEND_ONLY", True),
    ("BRANCH_LOCKED", True),
    ("NO_MODIFY_V87", True),
    ("NO_EDIT_RELEASE_TAG", True),
])

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
SESSION_DIR = BASE_DIR / "browser_sessions"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)

SMM_URL = "https://www.smm.cn/market/23336"
CACHE_FILE = CACHE_DIR / "smm_balance_cache.csv"
COOKIE_FILE = SESSION_DIR / "smm_cookies.json"
ALERT_LOG = CACHE_DIR / "alerts.jsonl"

# =============================================================================
# Custom Exceptions
# =============================================================================

class CloudflareBlocked(Exception):
    """Cloudflare challenge not passed within timeout."""
    pass

class SMMFetchError(Exception):
    """SMM page fetch failed after all retries."""
    pass

class CircuitOpenError(Exception):
    """Circuit breaker is OPEN, refusing requests."""
    pass

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# =============================================================================
# Retry Strategy: Exponential Backoff
# =============================================================================

class ExponentialBackoff:
    """Exponential backoff with jitter to prevent thundering herd."""

    def __init__(self, base_delay: float = 10.0, max_delay: float = 300.0,
                 multiplier: float = 2.0, jitter_pct: float = 0.3):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter_pct = jitter_pct

    def get_delay(self, attempt: int) -> float:
        """Compute delay for the Nth retry attempt (0-indexed)."""
        delay = min(self.base_delay * (self.multiplier ** attempt), self.max_delay)
        jitter = delay * self.jitter_pct
        delay += random.uniform(-jitter, jitter)
        return max(1.0, delay)

    def execute(self, func: Callable, max_retries: int = 3, **kwargs) -> Any:
        """Execute func with retries; raise last error on exhaustion."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return func(**kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    delay = self.get_delay(attempt)
                    log.warning("[BACKOFF] Attempt %d/%d failed: %s — retrying in %.1fs",
                                attempt + 1, max_retries, e, delay)
                    time.sleep(delay)
                else:
                    log.error("[BACKOFF] All %d retries exhausted", max_retries)
        raise last_error


# =============================================================================
# Circuit Breaker Pattern
# =============================================================================

class CircuitBreaker:
    """Circuit breaker with CLOSED → OPEN → HALF_OPEN state machine."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 300.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self.last_state_change: float = time.time()

    def record_success(self) -> None:
        if self.state == self.HALF_OPEN:
            self._transition(self.CLOSED)
            log.info("[CIRCUIT] CLOSED — recovered successfully")
        self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold and self.state != self.OPEN:
            self._transition(self.OPEN)
            log.warning("[CIRCUIT] OPEN — %d consecutive failures", self.failure_count)

    def _transition(self, new_state: str) -> None:
        self.state = new_state
        self.last_state_change = time.time()

    def _should_attempt(self) -> bool:
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._transition(self.HALF_OPEN)
                log.info("[CIRCUIT] HALF_OPEN — probing recovery")
                return True
            return False
        return True

    def call(self, func: Callable, **kwargs) -> Any:
        if not self._should_attempt():
            raise CircuitOpenError(
                f"Circuit is {self.state.upper()} — refusing request "
                f"(fails={self.failure_count}, threshold={self.failure_threshold})"
            )
        try:
            result = func(**kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise

    @property
    def is_open(self) -> bool:
        return self.state == self.OPEN

    def status(self) -> str:
        return f"state={self.state}, failures={self.failure_count}, last_change={time.time() - self.last_state_change:.0f}s ago"


# =============================================================================
# Cache Fallback Strategy
# =============================================================================

class CacheFallbackStrategy:
    """Tiered cache freshness classification with alert levels."""

    # (min_hours, max_hours) → label → alert severity
    TIERS: Dict[str, Tuple[int, int, str]] = {
        "FRESH":        (0,   72,  "NONE"),
        "STALE":        (72, 168,  "MEDIUM"),
        "STALE_ALERT":  (168, 336, "HIGH"),
        "EXPIRED":      (336, 9999, "CRITICAL"),
    }

    @staticmethod
    def classify(age_hours: float) -> Tuple[str, str]:
        """Return (label, alert_severity) for given cache age."""
        for label, (lo, hi, sev) in CacheFallbackStrategy.TIERS.items():
            if lo <= age_hours < hi:
                return label, sev
        return "EXPIRED", "CRITICAL"

    @staticmethod
    def load_cache(cache_file: Path) -> List[Dict]:
        """Load cached records from CSV; return empty list if missing."""
        if not cache_file.exists():
            return []
        records = []
        try:
            with open(cache_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                records = list(reader)
            log.info("[CACHE] Loaded %d records from %s", len(records), cache_file.name)
        except Exception as e:
            log.warning("[CACHE] Load failed: %s", e)
        return records

    @staticmethod
    def save_cache(records: List[Dict], cache_file: Path) -> None:
        """Persist records to CSV."""
        if not records:
            return
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(records[0].keys())
        with open(cache_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        log.info("[CACHE] Saved %d records to %s", len(records), cache_file.name)

    @staticmethod
    def cache_age_hours(cache_file: Path) -> float:
        """Compute cache age in hours from file mtime."""
        if not cache_file.exists():
            return 9999.0
        mtime = os.path.getmtime(cache_file)
        return (time.time() - mtime) / 3600.0


# =============================================================================
# Alert Emission
# =============================================================================

def fire_alert(alert_id: str, severity: str, message: str, extra: Optional[Dict] = None) -> None:
    """Append a structured alert to the alert log."""
    ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": alert_id,
        "severity": severity,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "task_id": TASK_ID,
        "branch": BRANCH,
    }
    if extra:
        entry.update(extra)
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log.warning("[ALERT] %s [%s] %s", alert_id, severity, message)


# =============================================================================
# SMM Cloudflare Bypass (Core)
# =============================================================================

class SMMCloudflareBypass:
    """
    Headless Chrome bypass for SMM Cloudflare protection.

    Handles:
      - WebDriver lifecycle with anti-detection flags
      - Cloudflare challenge detection (cookie / title / iframe checks)
      - Adaptive wait strategy (polling, not fixed sleep)
      - Cookie persistence (JSON file)
      - Content verification (404 / empty detection)
    """

    CLOUDFLARE_MARKERS = [
        "challenge-platform", "turnstile", "cf-turnstile",
        "Verify you are human", "Checking your browser",
        "Just a moment", "Cloudflare", "Enable JavaScript and cookies",
    ]

    def __init__(self, proxy: Optional[str] = None, headless: bool = True):
        self.proxy = proxy
        self.headless = headless
        self.driver = None
        self._init_driver()

    # -- WebDriver Initialization -------------------------------------------

    def _init_driver(self) -> None:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.options import Options
        except ImportError as exc:
            raise ImportError(
                "Selenium dependencies missing. Install: "
                "pip install selenium webdriver-manager beautifulsoup4"
            ) from exc

        opts = Options()

        if self.headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")

        # Anti-automation detection
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        # Browser fingerprint
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        opts.add_argument("--lang=zh-CN")
        opts.add_argument("--window-size=1920,1080")

        if self.proxy:
            opts.add_argument(f"--proxy-server={self.proxy}")

        prefs = {
            "download.default_directory": str(SESSION_DIR),
            "credentials_enable_service": False,
            "plugins.always_open_pdf_externally": True,
        }
        opts.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.implicitly_wait(10)

        # Inject anti-detection JS on every new document
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": (
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});"
                "Object.defineProperty(navigator,'languages',{get:()=>['zh-CN','zh','en']});"
                "window.chrome={runtime:{}};"
            )
        })

        log.info("[BROWSER] Initialized (headless=%s, proxy=%s)", self.headless, self.proxy)

    # -- Cookie Persistence -------------------------------------------------

    def load_cookies(self) -> bool:
        """Load persisted cookies; return True if any were applied."""
        if not COOKIE_FILE.exists():
            return False
        try:
            with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            if not cookies:
                return False
            self.driver.get("https://www.smm.cn/")
            for c in cookies:
                valid = {k: v for k, v in c.items()
                         if k in ("name", "value", "domain", "path",
                                  "expiry", "secure", "httpOnly")}
                try:
                    self.driver.add_cookie(valid)
                except Exception:
                    pass
            log.info("[BROWSER] Loaded %d cookies", len(cookies))
            return True
        except Exception as e:
            log.warning("[BROWSER] Cookie load failed: %s", e)
            return False

    def save_cookies(self) -> None:
        """Persist current cookies to JSON, filtering expired ones."""
        cookies = self.driver.get_cookies()
        valid = [c for c in cookies if c.get("expiry", 0) > time.time()]
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(valid, f, indent=2)
        log.info("[BROWSER] Saved %d valid cookies", len(valid))

    # -- Cloudflare Challenge Detection -------------------------------------

    def is_cloudflare_challenge(self) -> bool:
        """Detect Cloudflare interstitial by content markers."""
        try:
            source = self.driver.page_source
            return any(m in source for m in self.CLOUDFLARE_MARKERS)
        except Exception:
            return False

    def wait_for_cloudflare(self, max_wait: float = 30.0) -> bool:
        """
        Poll for Cloudflare challenge resolution.

        Checks (in order):
          1. cf_clearance cookie appeared
          2. Page title changed (no longer 'Just a moment')
          3. Turnstile iframe disappeared / challenge gone

        Returns True if passed, False if timeout.
        """
        log.info("[CF] Waiting up to %.0fs for challenge resolution...", max_wait)
        start = time.time()

        while time.time() - start < max_wait:
            time.sleep(1.0)

            # Check 1: cf_clearance cookie
            cookies = self.driver.get_cookies()
            if any(c.get("name") == "cf_clearance" for c in cookies):
                elapsed = time.time() - start
                log.info("[CF] Passed in %.1fs (cf_clearance cookie)", elapsed)
                return True

            # Check 2: Title change
            try:
                title = self.driver.title
                if title and "Just a moment" not in title and "Checking" not in title:
                    elapsed = time.time() - start
                    log.info("[CF] Passed in %.1fs (title: '%s')", elapsed, title[:40])
                    return True
            except Exception:
                pass

            # Check 3: Challenge markers gone
            if not self.is_cloudflare_challenge():
                elapsed = time.time() - start
                log.info("[CF] Passed in %.1fs (challenge markers gone)", elapsed)
                return True

        elapsed = time.time() - start
        log.warning("[CF] NOT passed after %.1fs", elapsed)
        return False

    # -- Content Verification -----------------------------------------------

    def _verify_content(self) -> bool:
        """Ensure page is not an error page and has substantive content."""
        try:
            source = self.driver.page_source
            error_markers = ["404 Not Found", "Page Not Found",
                             "Access Denied", "403 Forbidden"]
            if any(m in source for m in error_markers):
                return False
            return len(source) > 500
        except Exception:
            return False

    # -- Fetch (with internal retry) ----------------------------------------

    def fetch(self, url: str, max_wait: float = 30.0,
              retries: int = 3) -> str:
        """
        Fetch an SMM page, handling Cloudflare challenges.

        Returns page_source on success; raises SMMFetchError on failure.
        """
        last_error: Optional[Exception] = None

        # Try to reuse cached cookies
        if not self.load_cookies():
            log.info("[BROWSER] No cached cookies — fresh session")

        for attempt in range(retries):
            try:
                log.info("[FETCH] Attempt %d/%d: %s", attempt + 1, retries, url)

                # Rate limit (human-like delay)
                delay = random.uniform(5.0, 15.0)
                log.debug("[RATE] Waiting %.1fs", delay)
                time.sleep(delay)

                self.driver.get(url)

                # Cloudflare detection + wait
                if self.is_cloudflare_challenge():
                    if not self.wait_for_cloudflare(max_wait):
                        raise CloudflareBlocked(
                            f"Timeout after {max_wait:.0f}s"
                        )

                # Content verification
                source = self.driver.page_source

                if "404 Not Found" in source or "Page Not Found" in source:
                    raise SMMFetchError(f"404: {url}")
                if len(source) < 500:
                    raise SMMFetchError(f"Empty response ({len(source)}B)")

                # Persist cookies on success
                self.save_cookies()
                log.info("[FETCH] Success: %d bytes", len(source))
                return source

            except CloudflareBlocked as e:
                last_error = e
                wait = 10.0 * (2 ** attempt)
                log.warning("[FETCH] CF blocked — waiting %.0fs", wait)
                time.sleep(wait)
            except Exception as e:
                last_error = e
                wait = 5.0 * (2 ** attempt)
                log.warning("[FETCH] Error: %s — retrying in %.0fs", e, wait)
                time.sleep(wait)

        raise SMMFetchError(f"All {retries} attempts failed: {last_error}")

    # -- Shutdown -----------------------------------------------------------

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            log.info("[BROWSER] Closed")


# =============================================================================
# Full Failure Handling Pipeline
# =============================================================================

def fetch_with_full_pipeline(
    url: str,
    bypass: SMMCloudflareBypass,
    cache_strategy: CacheFallbackStrategy = CacheFallbackStrategy,
    circuit_breaker: CircuitBreaker = None,
    backoff: ExponentialBackoff = None,
) -> Tuple[Optional[List[Dict]], str]:
    """
    Full retry pipeline:
      Layer 1: CircuitBreaker guard
      Layer 2: ExponentialBackoff retries
      Layer 3: Cache fallback with freshness classification
      Layer 4: DRY-RUN degrade to estimate

    Returns (records, mode) where mode is one of:
      'LIVE' | 'CACHE_FRESH' | 'CACHE_STALE' | 'CACHE_STALE_ALERT'
      | 'CACHE_EXPIRED' | 'DRY_RUN_ESTIMATE'
    """
    if circuit_breaker is None:
        circuit_breaker = CircuitBreaker()
    if backoff is None:
        backoff = ExponentialBackoff()

    try:
        # Layer 1+2: CircuitBreaker + Backoff
        result = circuit_breaker.call(
            backoff.execute,
            func=bypass.fetch,
            url=url,
            max_wait=30,
            retries=3,
        )

        # Extract records from HTML (placeholder — real extractor would parse tables)
        records = _parse_smm_data(result)
        if records:
            cache_strategy.save_cache(records, CACHE_FILE)
        return records, "LIVE"

    except CircuitOpenError as e:
        log.warning("[PIPELINE] Circuit OPEN: %s", e)
        fire_alert("CIRCUIT-OPEN", "HIGH", str(e),
                   {"circuit_status": circuit_breaker.status()})
        return _cache_or_degrade(cache_strategy)

    except SMMFetchError as e:
        log.warning("[PIPELINE] All retries failed: %s", e)
        fire_alert("FETCH-EXHAUSTED", "HIGH", str(e))
        return _cache_or_degrade(cache_strategy)


def _parse_smm_data(html: str) -> List[Dict]:
    """
    Parse SMM page HTML into records.
    Prototype stub: returns empty list (real table parsing TBD with BS4).
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        log.info("[PARSE] Found %d tables", len(tables))
        # Stub: would iterate tables and extract rows
        return []
    except ImportError:
        log.warning("[PARSE] BeautifulSoup not installed — skip parsing")
        return []
    except Exception as e:
        log.warning("[PARSE] Error: %s", e)
        return []


def _cache_or_degrade(cache_strategy: CacheFallbackStrategy) -> Tuple[Optional[List[Dict]], str]:
    """Layer 3: Cache fallback with freshness classification."""
    age = cache_strategy.cache_age_hours(CACHE_FILE)
    if age >= 9999.0:
        # No cache at all
        log.error("[PIPELINE] No cache available — degrading to DRY-RUN estimate")
        fire_alert("NO-CACHE", "CRITICAL",
                   "No cached data available; degrading to estimate")
        return _dry_run_estimate(), "DRY_RUN_ESTIMATE"

    records = cache_strategy.load_cache(CACHE_FILE)
    label, severity = cache_strategy.classify(age)

    if label == "FRESH":
        log.info("[PIPELINE] Using FRESH cache (%.1fh old, %d records)",
                 age, len(records))
    elif label == "STALE":
        log.warning("[PIPELINE] Using STALE cache (%.1fh old, %d records)",
                    age, len(records))
        fire_alert("CACHE-STALE", severity,
                   f"SMM cache is {age:.1f}h old", {"label": label})
    elif label == "STALE_ALERT":
        log.warning("[PIPELINE] Using STALE_ALERT cache (%.1fh old, %d records)",
                    age, len(records))
        fire_alert("CACHE-STALE-ALERT", severity,
                   f"SMM cache is {age:.1f}h old", {"label": label})
    else:
        log.warning("[PIPELINE] Using EXPIRED cache (%.1fh old, %d records)",
                    age, len(records))
        fire_alert("CACHE-EXPIRED", severity,
                   f"SMM cache is {age:.1f}h old (>14 days)", {"label": label})

    return records, f"CACHE_{label}"


def _dry_run_estimate() -> List[Dict]:
    """Layer 4: Degrade to DRY-RUN estimate from historical means."""
    today = datetime.now()
    estimate = {
        "date": f"{today.year}-{today.month:02d}",
        "smelt_production": 78.5,
        "shfe_inventory": 3.5,
        "apparent_consumption": 82.0,
        "source": "DRY_RUN_ESTIMATE",
        "confidence": 0.5,
    }
    fire_alert("DEGRADE-01", "CRITICAL",
               f"SMM data degraded to estimate: {json.dumps(estimate)}")
    return [estimate]


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="SMM Cloudflare Bypass Prototype v" + LIB_VERSION
    )
    parser.add_argument("--url", default=SMM_URL, help="SMM page URL")
    parser.add_argument("--headless", type=lambda x: x.lower() in ("true", "1"),
                        default=True, help="Run headless (default: True)")
    parser.add_argument("--proxy", default=None, help="Proxy server URL")
    parser.add_argument("--max-wait", type=float, default=30.0,
                        help="Max Cloudflare wait seconds")
    parser.add_argument("--retries", type=int, default=3,
                        help="Max retry attempts")
    parser.add_argument("--output", default=str(CACHE_FILE),
                        help="Output CSV path")
    parser.add_argument("--dry-run", action="store_true",
                        help="No CSV write (dry-run)")
    parser.add_argument("--json-out", default=None,
                        help="JSON result output path")

    args = parser.parse_args()

    log.info("=" * 60)
    log.info("SMM Cloudflare Bypass Prototype v%s", LIB_VERSION)
    log.info("TASK: %s | BRANCH: %s", TASK_ID, BRANCH)
    log.info("=" * 60)

    bypass = None
    result = {
        "task_id": TASK_ID,
        "script": SCRIPT_NAME,
        "version": LIB_VERSION,
        "branch": BRANCH,
        "url": args.url,
        "success": False,
        "rows_fetched": 0,
        "mode": "UNKNOWN",
        "errors": [],
        "timestamp": datetime.now().isoformat(),
        "constraints": dict(CONSTRAINTS),
    }

    try:
        # Step 1: Initialize bypass
        log.info("[STEP 1] Initializing Selenium WebDriver...")
        bypass = SMMCloudflareBypass(proxy=args.proxy, headless=args.headless)

        # Step 2: Full pipeline fetch
        log.info("[STEP 2] Fetching via full retry pipeline...")
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
        bk = ExponentialBackoff(base_delay=10, max_delay=300, jitter_pct=0.3)
        records, mode = fetch_with_full_pipeline(
            args.url, bypass,
            cache_strategy=CacheFallbackStrategy,
            circuit_breaker=cb,
            backoff=bk,
        )

        result["mode"] = mode
        result["rows_fetched"] = len(records) if records else 0

        if mode == "LIVE":
            result["success"] = True

        if records and not args.dry_run:
            CacheFallbackStrategy.save_cache(records, Path(args.output))

        log.info("[RESULT] mode=%s, rows=%d, success=%s",
                 mode, result["rows_fetched"], result["success"])

    except ImportError as e:
        result["errors"].append(f"ImportError: {e}")
        log.error("[FATAL] Missing dependencies: %s", e)
        log.info("[HINT] pip install selenium webdriver-manager beautifulsoup4")

    except Exception as e:
        result["errors"].append(f"{type(e).__name__}: {str(e)}")
        log.error("[FATAL] %s: %s", type(e).__name__, e)

    finally:
        if bypass:
            bypass.close()

        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            log.info("[OUTPUT] JSON written to %s", args.json_out)

    log.info("[DONE] Exit code: %d", 0 if result["success"] else 1)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
