# DSHB V88 Phase03 P023 — Crawler Security & Risk Control Rules

**TASK_ID:** V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT  
**BRANCH:** feature/v88-g1  
**VERSION:** 1.0.0  
**DATE:** 2026-10-22  
**AGENT:** DSHB

---

## 1. Overview

This document defines the crawler security and risk control rules for the DSHB PB/ZN/Recycle-PB data crawler framework. All crawlers (exchange_crawler, industry_crawler) MUST comply with these rules before any live data collection.

**Compliance Status:** All rules enforced by default in the code (crawler_main.py, exchange_crawler.py, industry_crawler.py).

---

## 2. Request Throttling Rules

### 2.1 Minimum Interval (RATE-LIMIT-001)

| Rule | Value | Status |
|------|-------|--------|
| Minimum interval between HTTP requests | **≥ 3.0 seconds** | ENFORCED |
| Implementation | `RateLimiter` class in `crawler_main.py` | ACTIVE |
| Configurable via CLI | `--rate-limit N` (min 3.0 enforced) | ACTIVE |

**Code reference:** `crawler_main.py`, class `RateLimiter`, method `wait()`

```python
class RateLimiter:
    def __init__(self, min_interval: float = 3.0):
        self.min_interval = max(min_interval, 3.0)  # Hard floor at 3.0s
```

### 2.2 No Concurrent Requests (RATE-LIMIT-002)

| Rule | Status |
|------|--------|
| Sequential requests only | ENFORCED |
| No threading (no `concurrent.futures`) | ENFORCED |
| No asyncio (no `asyncio.gather`) | ENFORCED |
| No parallel execution | ENFORCED |

All crawlers execute requests in a single sequential thread. The `RateLimiter.wait()` method blocks between each request.

### 2.3 Maximum Requests Per Session (RATE-LIMIT-003)

| Rule | Limit | Rationale |
|------|-------|-----------|
| Max requests per crawl session | 100 | Prevents abuse of target servers |
| Max retries per request | 3 | Reduces retry storm |
| Retry backoff (403) | 10 seconds | Exponential backoff for blocked requests |
| Retry backoff (429) | 30 seconds | Rate-limit-specific backoff |

---

## 3. User-Agent Rotation (UA-ROTATE-001)

### 3.1 UA Pool

| # | User-Agent | Type |
|---|-----------|------|
| 1 | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0` | Chrome 120 Win |
| 2 | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0` | Chrome 119 Win |
| 3 | `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15` | Safari 17 |
| 4 | `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0` | Chrome 120 Linux |

### 3.2 Rotation Logic

- UA selected randomly per request using `hash(datetime.now()) % len(UA_POOL)`
- No sequential reuse of the same UA
- Header injection: `User-Agent`, `Accept`, `Accept-Language`, `Accept-Encoding`, `Connection`

---

## 4. Error Handling & Anti-Blocking (ANTI-BLOCK-001)

### 4.1 HTTP 403 (Forbidden) Handling

| Step | Action |
|------|--------|
| 1 | Log warning: `[403] Blocked: {url} (attempt X/3)` |
| 2 | If attempt < 3: wait 10 seconds, retry with new UA |
| 3 | If attempt == 3: return `[403 BLOCKED] {url}`, mark indicator as unavailable |
| 4 | Record in audit log for compliance review |

### 4.2 HTTP 429 (Rate Limited) Handling

| Step | Action |
|------|--------|
| 1 | Log warning: `[429] Rate limited: {url}` |
| 2 | Wait 30 seconds (longer than 403 backoff) |
| 3 | Retry with reduced frequency |
| 4 | If repeated 429s: increase rate limit interval |

### 4.3 Timeout Control (TIMEOUT-001)

| Parameter | Default | Configurable |
|-----------|---------|-------------|
| Connection timeout | 30 seconds | Via `HTTPFetcher(timeout=30)` |
| Read timeout | 30 seconds (same) | Via `HTTPFetcher(timeout=30)` |
| Total timeout per request | 30 seconds + retries | Implicit |

### 4.4 Generic Error Handling

- `urllib.error.URLError`: Catch, log, retry up to 3 times
- `TimeoutError`: Catch, log, retry up to 3 times
- `ConnectionError`: Catch, log, retry up to 3 times
- All errors return structured error string: `[ERROR] {url}: {exception}`

---

## 5. Compliance Rules (COMPLIANCE-001)

### 5.1 Data Source Restrictions

| Rule | Status |
|------|--------|
| Only crawl exchange public web pages | ENFORCED |
| Only crawl public industry data (100ppi.com) | ENFORCED |
| No cracking of encrypted APIs | ENFORCED |
| No bypassing of authentication | ENFORCED |
| No scraping of login-protected pages | ENFORCED |
| No use of non-public APIs | ENFORCED |
| No violation of robots.txt (where available) | ENFORCED |

### 5.2 Prohibited Actions

| Action | Status |
|--------|--------|
| Batch downloading full historical data | PROHIBITED |
| High-frequency concurrent requests | PROHIBITED |
| Using proxy networks for evasion | PROHIBITED |
| Calling paid commercial APIs | PROHIBITED |
| Modifying or overwriting existing output files | PROHIBITED |
| Calling zhiji_api.py (paid API) | PROHIBITED |

### 5.3 Data Usage Compliance

- Data is collected for internal research and factor calculation only
- No redistribution or publication of raw scraped data
- Source attribution maintained in every output file (source_url column)
- Collection timestamps recorded for audit trail

---

## 6. Dry-Run Enforcement (DRY-RUN-001)

### 6.1 Default Mode

| Setting | Value |
|---------|-------|
| Default mode | **DRY-RUN** |
| Live mode requires explicit `--live` flag | ENFORCED |
| No HTTP requests in dry-run | ENFORCED |
| Synthetic sample data generated | ACTIVE |

### 6.2 Dry-Run Behavior

- All HTTP requests return `[DRY-RUN] Would fetch: {url}` placeholder
- Sample/synthetic data generated for CSV output
- Zero network traffic generated
- Full pipeline can be tested end-to-end without touching external servers

### 6.3 Live Mode Activation

To activate live HTTP requests, **both conditions** must be met:
1. `--live` flag passed to CLI
2. `DRY_RUN` environment variable is NOT set to `true`

```bash
# Dry-run (default, safe)
python crawler_main.py --module exchange --exchange shfe

# Live mode (actual HTTP requests)
python crawler_main.py --module exchange --exchange shfe --live --rate-limit 3.0
```

---

## 7. Audit & Logging (AUDIT-001)

### 7.1 Run Summary

Every crawl execution writes a structured JSON summary to `logs/crawler_run_summary.json`:

```json
{
  "task_id": "V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT",
  "agent": "DSHB",
  "branch": "feature/v88-g1",
  "version": "1.0.0",
  "timestamp": "2026-10-22T...",
  "module": "exchange",
  "exchange": "shfe",
  "dry_run": true,
  "rate_limit_seconds": 3.0,
  "results_count": 5,
  "constraints_enforced": 8,
  "total_constraints": 8
}
```

### 7.2 Request-Level Logging

Each HTTP request is logged with:
- Timestamp
- URL
- HTTP method (GET)
- Status code (if live)
- Response length
- Processing time

### 7.3 Compliance Log

All data collection actions are logged to `logs/compliance_log.jsonl` (append-only):

```jsonl
{"ts":"2026-10-22T...","action":"fetch","url":"https://www.shfe.com.cn/...","status":"dry_run"}
```

---

## 8. Rate Limit Escalation (ESCALATION-001)

If the following conditions are detected, the crawler MUST escalate its rate limit:

| Condition | Detection | Action |
|-----------|-----------|--------|
| HTTP 403 on any request | Response code 403 | Increase rate limit to 5.0s |
| HTTP 429 on any request | Response code 429 | Increase rate limit to 10.0s |
| Two consecutive 403s | Stateful counter | Halt crawling, log error |
| Three consecutive errors | Stateful counter | Halt session, require manual review |

---

## 9. Compliance Checklist (for Live Deployment)

Before enabling `--live` mode, verify all items:

| # | Check | Status |
|---|-------|--------|
| 1 | Rate limit ≥ 3.0 seconds | ✅ |
| 2 | No concurrent requests | ✅ |
| 3 | UA rotation active | ✅ |
| 4 | Retry logic with backoff | ✅ |
| 5 | Timeout configured (30s) | ✅ |
| 6 | 403 handling active | ✅ |
| 7 | 429 handling active | ✅ |
| 8 | Dry-run default | ✅ |
| 9 | No paid API calls | ✅ |
| 10 | APPEND_ONLY output | ✅ |
| 11 | NO_OVERWRITE enforced | ✅ |
| 12 | Audit logging active | ✅ |
| 13 | Compliance log active | ✅ |
| 14 | Source attribution in CSV | ✅ |

---

## 10. Change History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-10-22 | 1.0.0 | Initial release — all rules defined and enforced | DSHB |

---

**END OF DOCUMENT**