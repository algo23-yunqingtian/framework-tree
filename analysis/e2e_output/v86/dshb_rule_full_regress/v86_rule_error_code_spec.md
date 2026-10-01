# V86 Standardized Error Code Specification

**Task:** DSHB_V86_RULE_ENGINE_FULL_INTEGRATION_REGRESSION_AND_DOC_FINALIZE  
**Branch:** `feature/v85-chart-template`  
**Source Systems:** Rule Engine (`v86_p1_rule_prototype.py`), Alias Engine (`alias_task_adapter.py`), E Backend Task API (`v86_task_api_design.md`, commit `bcd64dd`)  
**Document Version:** v1.0  
**Generated:** 2026-10-01  
**Status:** FINAL

---

## 1. Overview

This specification defines a unified error code taxonomy across three interconnected systems:

| System | Component | Source File | Error Code Count |
|--------|-----------|-------------|-----------------|
| **Rule Engine** | `V86P1RuleEngine` | `v86_p1_rule_prototype.py` | 19 codes (RuleErrorCode enum) |
| **Alias Engine** | `V86AliasEngine` via adapter | `alias_task_adapter.py` | 10 codes |
| **E Backend** | Task API | `v86_task_api_design.md` | Task API error codes |

**Design Principles:**
1. **Unified namespace** — all systems use the same error response format
2. **Cross-system alignment** — semantically equivalent errors map 1:1 across systems
3. **Retryability classification** — every error code declares whether it is retryable
4. **DATA_MISSING is a special non-error status** — it is not an error; it is a valid evaluation outcome

---

## 2. Error Response Format

All three systems MUST return errors using the following uniform JSON envelope:

```json
{
  "error": true,
  "code": "RULE_NOT_FOUND",
  "message": "Rule BL-019 not found in engine registry",
  "detail": {
    "rule_id": "BL-019",
    "engine_version": "v86_p1",
    "rule_count": 18
  },
  "timestamp": "2026-10-01T23:47:53.329865"
}
```

### 2.1 Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | `bool` | ✅ Yes | `true` for error responses; `false` for success responses |
| `code` | `str` | ✅ Yes | Machine-readable error code (see §3 for taxonomy) |
| `message` | `str` | ✅ Yes | Human-readable error description, safe for logging and display |
| `detail` | `dict` | ✅ Yes | Context-specific diagnostic information; may be empty `{}` |
| `timestamp` | `str` | ✅ Yes | ISO 8601 timestamp of when the error was generated |

### 2.2 Success Response Format

```json
{
  "error": false,
  "code": "OK",
  "message": "Request completed successfully",
  "detail": {
    "rule_result": "BLOCKED",
    "rule_triggered": ["BL-027"],
    "severity": "P1"
  },
  "timestamp": "2026-10-01T23:47:53.329865"
}
```

---

## 3. Unified Error Code Taxonomy

### 3.1 Complete Error Code Table

#### Category A: Rule Engine Error Codes (from RuleErrorCode enum, 19 codes)

| Code | Category | Description | Retryable | HTTP Status |
|------|----------|-------------|-----------|-------------|
| **`OK`** | Success | Operation completed successfully | N/A | 200 |
| **`RULE_ENGINE_LOAD_FAILED`** | System | Failed to load rule engine from source (file, API, or internal) | ✅ Yes | 503 |
| **`RULE_NOT_FOUND`** | Input Validation | Requested rule ID does not exist in engine registry | ❌ No | 404 |
| **`RULE_CONFLICT`** | Engine | Two or more rules produce conflicting results for same input | ❌ No | 409 |
| **`PATTERN_EMPTY`** | Input Validation | Pattern definition is empty or contains only whitespace | ❌ No | 400 |
| **`VARIETY_DETECT_FAILED`** | Data | Could not determine commodity variety from input name | ❌ No | 422 |
| **`BIDIRECTIONAL_CHECK_ERROR`** | Engine | Bidirectional rule check failed unexpectedly | ❌ No | 409 |
| **`EMPTY_INDICATOR`** | Input Validation | `indicator_name` field is missing or empty | ❌ No | 400 |
| **`EMPTY_MATCHED`** | Input Validation | `matched_name` field is missing or empty | ❌ No | 400 |
| **`INDICATOR_TOO_LONG`** | Input Validation | `indicator_name` exceeds maximum allowed length (256 chars) | ❌ No | 413 |
| **`MATCHED_TOO_LONG`** | Input Validation | `matched_name` exceeds maximum allowed length (256 chars) | ❌ No | 413 |
| **`INVALID_ALIAS_FORMAT`** | Input Validation | Alias entry format is invalid (malformed key-value pair) | ❌ No | 400 |
| **`ALIAS_MAP_NOT_FOUND`** | Data | Referenced alias map file does not exist | ✅ Yes | 404 |
| **`ALIAS_MAP_CORRUPT`** | Data | Alias map file exists but is corrupted or unreadable | ✅ Yes | 422 |
| **`CSV_PARSE_ERROR`** | Data | CSV parsing failed for input data | ❌ No | 422 |
| **`JSON_PARSE_ERROR`** | Data | JSON parsing failed for input data | ❌ No | 422 |
| **`TIMEOUT`** | System | Operation exceeded configured timeout threshold | ✅ Yes | 504 |
| **`INTERNAL_ERROR`** | System | Unhandled exception or unexpected engine state | ✅ Yes | 500 |
| **`DATA_MISSING`** | Data (Special) | Upstream data is missing, empty, or placeholder — no rule evaluation possible | ❌ No | 422 |

#### Category B: Alias Engine Error Codes (from alias_task_adapter.py, 10 codes)

| Code | Category | Description | Retryable | HTTP Status |
|------|----------|-------------|-----------|-------------|
| **`BAD_PAYLOAD`** | Input Validation | Request payload is malformed or cannot be parsed | ❌ No | 400 |
| **`UNKNOWN_TASK_TYPE`** | Input Validation | Requested task type is not recognized by alias engine | ❌ No | 400 |
| **`MISSING_REQUIRED_FIELD`** | Input Validation | Required payload field is missing or null | ❌ No | 400 |
| **`TASK_NOT_FOUND`** | Data | Referenced task ID does not exist in task registry | ❌ No | 404 |
| **`TASK_NOT_READY`** | System | Task exists but is not yet in a state that permits the requested operation | ✅ Yes | 409 |
| **`TASK_ALREADY_TERMINAL`** | Input Validation | Task has already reached a terminal state (cannot be re-opened or modified) | ❌ No | 409 |
| **`PAYLOAD_UNACCEPTABLE`** | Input Validation | Payload format is valid but does not meet semantic requirements | ❌ No | 422 |
| **`ENGINE_INIT_FAILED`** | System | Alias engine failed to initialize (model loading, cache setup, etc.) | ✅ Yes | 503 |
| **`ENGINE_DECIDE_FAILED`** | System | Alias engine encountered an error during decision/evaluation phase | ✅ Yes | 500 |
| **`RATE_LIMIT`** | System | Rate limit exceeded — too many requests in a time window | ✅ Yes | 429 |
| **`INTERNAL_ERROR`** | System | Unhandled exception in alias engine adapter | ✅ Yes | 500 |

#### Category C: E Backend Task API Error Codes (from v86_task_api_design.md)

| Code | Category | Description | Retryable | HTTP Status |
|------|----------|-------------|-----------|-------------|
| **`INTERNAL_ERROR`** | System | Internal server error in task API backend | ✅ Yes | 500 |
| **`INVALID_REQUEST`** | Input Validation | Request structure or format is invalid | ❌ No | 400 |
| **`RESOURCE_NOT_FOUND`** | Data | Referenced resource does not exist | ❌ No | 404 |
| **`RESOURCE_CONFLICT`** | System | Resource conflict (e.g., duplicate task ID) | ❌ No | 409 |
| **`SERVICE_UNAVAILABLE`** | System | Service is temporarily unavailable (maintenance, overload) | ✅ Yes | 503 |
| **`TIMEOUT`** | System | Request timed out at API gateway or backend | ✅ Yes | 504 |

---

## 4. Cross-System Error Code Alignment

The following table maps semantically equivalent error codes across all three systems. When a consumer receives an error, they can normalize to a canonical code regardless of the originating system.

### 4.1 Alignment Matrix

| Canonical Concept | Rule Engine Code | Alias Engine Code | E Backend Code |
|------------------|-----------------|-------------------|----------------|
| **Internal/unhandled error** | `INTERNAL_ERROR` | `ENGINE_DECIDE_FAILED` | `INTERNAL_ERROR` |
| **Timeout / rate limit** | `TIMEOUT` | `RATE_LIMIT` | `TIMEOUT` |
| **Engine/system load failure** | `RULE_ENGINE_LOAD_FAILED` | `ENGINE_INIT_FAILED` | `SERVICE_UNAVAILABLE` |
| **Missing required input** | `EMPTY_INDICATOR` | `MISSING_REQUIRED_FIELD` | `INVALID_REQUEST` |
| **Resource not found** | `RULE_NOT_FOUND` | `TASK_NOT_FOUND` | `RESOURCE_NOT_FOUND` |
| **Malformed data format** | `CSV_PARSE_ERROR`, `JSON_PARSE_ERROR` | `BAD_PAYLOAD`, `PAYLOAD_UNACCEPTABLE` | `INVALID_REQUEST` |
| **Data unavailable** | `DATA_MISSING` | — | — |
| **Conflict** | `RULE_CONFLICT` | `TASK_ALREADY_TERMINAL` | `RESOURCE_CONFLICT` |
| **Operation in progress** | — | `TASK_NOT_READY` | — |

### 4.2 Detailed Alignment Mapping

#### 4.2.1 Internal Error Chain

```
Rule Engine:  INTERNAL_ERROR  ──┐
                                 ├──► Canonical: INTERNAL_ERROR  (HTTP 500)
Alias Engine: ENGINE_DECIDE_FAILED ─┤
                                 │
E Backend:    INTERNAL_ERROR  ──┘
```

**Meaning:** An unhandled exception or unexpected engine state occurred. The consumer cannot distinguish the root cause between systems — all are generic internal failures requiring retry or escalation.

**Retry policy:** Retry with exponential backoff. If persistent, escalate to engineering.

#### 4.2.2 Timeout / Rate Limit Chain

```
Rule Engine:  TIMEOUT  ─────┐
                            ├──► Canonical: TIMEOUT  (HTTP 504)
Alias Engine: RATE_LIMIT ───┤
                            │
E Backend:    TIMEOUT  ─────┘
```

**Meaning:** The operation was interrupted by time constraints — either an engine timeout or a rate limiter rejection.

**Retry policy:** Retry after exponential backoff. For `RATE_LIMIT` (alias engine), respect the `Retry-After` header if present.

#### 4.2.3 Engine Load Failure Chain

```
Rule Engine:  RULE_ENGINE_LOAD_FAILED  ──┐
                                          ├──► Canonical: SERVICE_UNAVAILABLE (HTTP 503)
Alias Engine: ENGINE_INIT_FAILED ────────┤
                                          │
E Backend:    SERVICE_UNAVAILABLE ────────┘
```

**Meaning:** The engine or service failed to start up or load its data. The consumer should retry after a delay — the system is likely initializing or recovering.

**Retry policy:** Retry after exponential backoff. If persistent, investigate infrastructure (file system, network, memory).

#### 4.2.4 Missing Input Chain

```
Rule Engine:  EMPTY_INDICATOR  ──┐
                                  ├──► Canonical: INVALID_REQUEST (HTTP 400)
Alias Engine: MISSING_REQUIRED_FIELD ─┤
                                  │
E Backend:    INVALID_REQUEST  ───┘
```

**Meaning:** A required input field is absent or empty. This is a client error — the request must be corrected before resubmission.

**Retry policy:** Do NOT retry automatically. The consumer must fix the payload and resubmit.

---

## 5. Error Code Lookup by Category

### 5.1 Category: Input Validation (Client Errors — 400/409/413/422)

These errors indicate the request itself is invalid. The consumer must fix the request before retrying.

| Code | System(s) | HTTP Status | Consumer Action |
|------|-----------|-------------|-----------------|
| `EMPTY_INDICATOR` | Rule Engine | 400 | Provide a non-empty `indicator_name` |
| `EMPTY_MATCHED` | Rule Engine | 400 | Provide a non-empty `matched_name` |
| `INDICATOR_TOO_LONG` | Rule Engine | 413 | Truncate `indicator_name` to ≤ 256 chars |
| `MATCHED_TOO_LONG` | Rule Engine | 413 | Truncate `matched_name` to ≤ 256 chars |
| `PATTERN_EMPTY` | Rule Engine | 400 | Provide a non-empty pattern definition |
| `INVALID_ALIAS_FORMAT` | Rule Engine | 400 | Fix alias entry format (key-value pair) |
| `BAD_PAYLOAD` | Alias Engine | 400 | Fix payload structure/format |
| `UNKNOWN_TASK_TYPE` | Alias Engine | 400 | Use a recognized task type |
| `MISSING_REQUIRED_FIELD` | Alias Engine | 400 | Add the missing required field |
| `PAYLOAD_UNACCEPTABLE` | Alias Engine | 422 | Adjust payload to meet semantic requirements |
| `TASK_ALREADY_TERMINAL` | Alias Engine | 409 | Do not modify completed/cancelled tasks |
| `INVALID_REQUEST` | E Backend | 400 | Fix request structure |
| `DATA_MISSING` | Rule Engine | 422 | **Special:** not an error — see §7 |

### 5.2 Category: Engine Errors (409)

These errors indicate the engine produced conflicting or unexpected internal results.

| Code | System(s) | HTTP Status | Consumer Action |
|------|-----------|-------------|-----------------|
| `RULE_CONFLICT` | Rule Engine | 409 | Investigate rule definitions; possible rule overlap |
| `BIDIRECTIONAL_CHECK_ERROR` | Rule Engine | 409 | Check bidirectional rule pairing; escalate |
| `TASK_NOT_READY` | Alias Engine | 409 | Retry after task reaches ready state |

### 5.3 Category: System Errors (500/503/504)

These errors indicate infrastructure or engine-level failures. Retries are generally safe.

| Code | System(s) | HTTP Status | Retryable | Consumer Action |
|------|-----------|-------------|-----------|-----------------|
| `INTERNAL_ERROR` | Rule Engine, Alias Engine, E Backend | 500 | ✅ Yes | Retry with backoff; escalate if persistent |
| `ENGINE_DECIDE_FAILED` | Alias Engine | 500 | ✅ Yes | Retry with backoff; check engine logs |
| `RULE_ENGINE_LOAD_FAILED` | Rule Engine | 503 | ✅ Yes | Retry after backoff; check rule file availability |
| `ENGINE_INIT_FAILED` | Alias Engine | 503 | ✅ Yes | Retry after backoff; check engine dependencies |
| `SERVICE_UNAVAILABLE` | E Backend | 503 | ✅ Yes | Retry after backoff; check service health |
| `TIMEOUT` | Rule Engine, E Backend | 504 | ✅ Yes | Retry with backoff; consider increasing timeout |
| `RATE_LIMIT` | Alias Engine | 429 | ✅ Yes | Respect `Retry-After` header; reduce request rate |

### 5.4 Category: Data Errors (404/422)

These errors indicate missing or corrupted data resources. Some are retryable (transient), some are not (permanent).

| Code | System(s) | HTTP Status | Retryable | Consumer Action |
|------|-----------|-------------|-----------|-----------------|
| `RULE_NOT_FOUND` | Rule Engine | 404 | ❌ No | Verify rule ID exists in engine registry |
| `TASK_NOT_FOUND` | Alias Engine | 404 | ❌ No | Verify task ID exists in task registry |
| `RESOURCE_NOT_FOUND` | E Backend | 404 | ❌ No | Verify resource path/ID exists |
| `ALIAS_MAP_NOT_FOUND` | Rule Engine | 404 | ✅ Yes | Retry — file may be temporarily unavailable |
| `ALIAS_MAP_CORRUPT` | Rule Engine | 422 | ✅ Yes | Retry — file may be re-synced; escalate if persistent |
| `CSV_PARSE_ERROR` | Rule Engine | 422 | ❌ No | Fix CSV formatting; cannot auto-repair |
| `JSON_PARSE_ERROR` | Rule Engine | 422 | ❌ No | Fix JSON formatting; cannot auto-repair |
| `VARIETY_DETECT_FAILED` | Rule Engine | 422 | ❌ No | Verify input name is a recognized commodity variety |
| `DATA_MISSING` | Rule Engine | 422 | ❌ No | **Special:** not an error — see §7 |

---

## 6. Retryability Matrix

| Code | Retryable | Retry Strategy | Max Retries | Notes |
|------|-----------|---------------|-------------|-------|
| `OK` | N/A | — | — | Success; no retry needed |
| `RULE_ENGINE_LOAD_FAILED` | ✅ Yes | Exponential backoff | 3 | Infrastructure-level; may self-heal |
| `RULE_NOT_FOUND` | ❌ No | — | 0 | Client must fix request |
| `RULE_CONFLICT` | ❌ No | — | 0 | Engine-level conflict; requires engineering |
| `PATTERN_EMPTY` | ❌ No | — | 0 | Client must fix input |
| `VARIETY_DETECT_FAILED` | ❌ No | — | 0 | Client must fix input |
| `BIDIRECTIONAL_CHECK_ERROR` | ❌ No | — | 0 | Engine-level error; requires engineering |
| `EMPTY_INDICATOR` | ❌ No | — | 0 | Client must fix input |
| `EMPTY_MATCHED` | ❌ No | — | 0 | Client must fix input |
| `INDICATOR_TOO_LONG` | ❌ No | — | 0 | Client must truncate |
| `MATCHED_TOO_LONG` | ❌ No | — | 0 | Client must truncate |
| `INVALID_ALIAS_FORMAT` | ❌ No | — | 0 | Client must fix format |
| `ALIAS_MAP_NOT_FOUND` | ✅ Yes | Exponential backoff | 3 | File may re-appear |
| `ALIAS_MAP_CORRUPT` | ✅ Yes | Exponential backoff | 2 | File may be re-synced |
| `CSV_PARSE_ERROR` | ❌ No | — | 0 | Client must fix data |
| `JSON_PARSE_ERROR` | ❌ No | — | 0 | Client must fix data |
| `TIMEOUT` | ✅ Yes | Exponential backoff | 3 | Transient; may succeed on retry |
| `INTERNAL_ERROR` | ✅ Yes | Exponential backoff | 3 | Generic; may be transient |
| `DATA_MISSING` | ❌ No | — | 0 | **Not an error** — see §7 |
| `BAD_PAYLOAD` | ❌ No | — | 0 | Client must fix payload |
| `UNKNOWN_TASK_TYPE` | ❌ No | — | 0 | Client must use valid type |
| `MISSING_REQUIRED_FIELD` | ❌ No | — | 0 | Client must add field |
| `TASK_NOT_FOUND` | ❌ No | — | 0 | Client must verify ID |
| `TASK_NOT_READY` | ✅ Yes | Exponential backoff | 3 | Transient; task may become ready |
| `TASK_ALREADY_TERMINAL` | ❌ No | — | 0 | Cannot reverse terminal state |
| `PAYLOAD_UNACCEPTABLE` | ❌ No | — | 0 | Client must fix semantics |
| `ENGINE_INIT_FAILED` | ✅ Yes | Exponential backoff | 3 | Infrastructure-level |
| `ENGINE_DECIDE_FAILED` | ✅ Yes | Exponential backoff | 3 | Generic engine failure |
| `RATE_LIMIT` | ✅ Yes | Honor `Retry-After` | 5 | Reduce request rate |
| `INTERNAL_ERROR` (E Backend) | ✅ Yes | Exponential backoff | 3 | Generic |
| `INVALID_REQUEST` (E Backend) | ❌ No | — | 0 | Client must fix request |
| `RESOURCE_NOT_FOUND` (E Backend) | ❌ No | — | 0 | Client must verify resource |
| `RESOURCE_CONFLICT` (E Backend) | ❌ No | — | 0 | Client must resolve conflict |
| `SERVICE_UNAVAILABLE` (E Backend) | ✅ Yes | Exponential backoff | 3 | Transient |
| `TIMEOUT` (E Backend) | ✅ Yes | Exponential backoff | 3 | Transient |

### 6.1 Retry Strategy Guidelines

```
Exponential Backoff: delay = base_delay × 2^retry_count

Example: base_delay = 1 second
  Retry 1: wait 1s
  Retry 2: wait 2s
  Retry 3: wait 4s
  Total max wait: ~7s for 3 retries

For RATE_LIMIT: always honor the `Retry-After` header
  If present, use that delay value (in seconds)
  If absent, use standard exponential backoff
```

---

## 7. DATA_MISSING: Special Non-Error Status

### 7.1 Definition

`DATA_MISSING` is a **special classification** that is NOT an error. It represents a valid, expected evaluation outcome when upstream data quality is insufficient for rule evaluation.

### 7.2 When DATA_MISSING Is Returned

The rule engine returns `DATA_MISSING` with error code `OK` (not an error code) when the `matched_name` field matches any of the following sentinel patterns:

| Sentinel Pattern | Example | Meaning |
|-----------------|---------|---------|
| Empty string | `""` | No matched name was resolved |
| `N/A` marker | `"N/A"`, `"NA"`, `"n/a"` | Explicit null/none marker |
| Workbook record marker | `"（工作表记录）"` | Placeholder from spreadsheet import |
| Other recognized sentinels | `"null"`, `"none"`, `"—"`, `"--"` | Common placeholder values |

### 7.3 Response Format for DATA_MISSING

```json
{
  "error": false,
  "code": "OK",
  "message": "Data missing: matched_name is empty or placeholder",
  "detail": {
    "rule_result": "DATA_MISSING",
    "reason": "matched_name is empty",
    "indicator_name": "碳酸锂需求分析",
    "matched_name": ""
  },
  "timestamp": "2026-10-01T23:47:53.329865"
}
```

### 7.4 Key Distinctions

| Property | DATA_MISSING | Error |
|----------|-------------|-------|
| `error` field | `false` | `true` |
| `code` field | `OK` | Error code string |
| HTTP status | 200 | 4xx or 5xx |
| Retryable | ❌ No (not an error) | Depends on code |
| Consumer action | Log as data quality issue | Handle per error code |
| Counts against SLA | ❌ No | ✅ Yes (for 5xx) |

### 7.5 DATA_MISSING vs. Rule Miss

| Scenario | Classification | Engine Action |
|----------|---------------|---------------|
| `matched_name = ""` | **DATA_MISSING** | No rule evaluation; return OK + DATA_MISSING |
| `matched_name = "碳酸锂冶炼利润（元/吨）"` but no rule matches | **PASSED** (not a miss) | All rules evaluated, none triggered; return OK + PASSED |
| `matched_name = "碳酸锂冶炼利润（元/吨）"` and BL-009a should have blocked but didn't | **Rule Miss** | Engine bug — investigate rule implementation |

**DATA_MISSING means "nothing to evaluate."** A rule miss means "evaluation was attempted but the rule failed to catch a pattern it should have caught." These are fundamentally different situations.

### 7.6 Portal and Consumer Handling

Consumers (portals, dashboards, downstream systems) MUST:

1. **Not treat DATA_MISSING as a failure** — do not display error alerts
2. **Log DATA_MISSING separately** — track as a data quality metric, not a rule engine failure
3. **Report DATA_MISSING to upstream data team** — the root cause is data pipeline quality, not rule engine
4. **Exclude DATA_MISSING from rule engine SLA calculations** — it is not an engine error

---

## 8. Integration Guidelines for Consumers

### 8.1 Response Handling Flow

```
┌─────────────────────┐
│ Receive response    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ error == false?     │─────│ YES → Check code:     │
└──────────┬──────────┘     │   OK: success         │
           │ NO              │   DATA_MISSING: log   │
           ▼                │       as data quality │
┌─────────────────────┐     └──────────────────────┘
│ error == true       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ Check retryable?    │─────│ NO  → Log error,      │
└──────────┬──────────┘     │       alert consumer  │
           │ YES             │                       │
           ▼                └──────────────────────┘
┌─────────────────────┐
│ Retry with backoff  │
│ up to max_retries   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ All retries failed? │─────│ YES → Escalate to     │
└──────────┬──────────┘     │       engineering     │
           │ NO              │                       │
           ▼                └──────────────────────┘
┌─────────────────────┐
│ Success on retry    │
└─────────────────────┘
```

### 8.2 Consumer Implementation Checklist

#### 8.2.1 Error Code Handling

| Priority | Requirement | Implementation |
|----------|-------------|---------------|
| **P0** | Parse `error` field to distinguish success vs error | Check `error == true` before handling `code` |
| **P0** | Check for `DATA_MISSING` before treating `error: false` as normal success | Look for `rule_result == "DATA_MISSING"` in `detail` |
| **P0** | Implement retry logic for retryable error codes (see §6) | Use exponential backoff; respect `Retry-After` for `RATE_LIMIT` |
| **P1** | Log all error codes with `detail` dict for debugging | Structured logging with error code as searchable field |
| **P1** | Map cross-system error codes to canonical forms (see §4) | Normalize for downstream processing |
| **P2** | Display user-friendly messages from `message` field | Do not show raw error codes to end users |

#### 8.2.2 Retry Implementation Template

```python
import time
import random

RETRYABLE_CODES = {
    "INTERNAL_ERROR", "ENGINE_DECIDE_FAILED",
    "RULE_ENGINE_LOAD_FAILED", "ENGINE_INIT_FAILED",
    "SERVICE_UNAVAILABLE", "TIMEOUT", "RATE_LIMIT",
    "TASK_NOT_READY", "ALIAS_MAP_NOT_FOUND", "ALIAS_MAP_CORRUPT"
}

def call_with_retry(engine_call, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries + 1):
        response = engine_call()
        
        if not response.get("error", False):
            return response  # Success or DATA_MISSING
        
        code = response.get("code", "INTERNAL_ERROR")
        
        if code not in RETRYABLE_CODES:
            return response  # Non-retryable; return immediately
        
        if attempt == max_retries:
            return response  # Exhausted retries
        
        # Check Retry-After header for RATE_LIMIT
        retry_after = response.get("detail", {}).get("retry_after")
        if retry_after:
            delay = float(retry_after)
        else:
            delay = base_delay * (2 ** attempt)
        
        # Add jitter to prevent thundering herd
        delay += random.uniform(0, delay * 0.1)
        time.sleep(delay)
    
    return response
```

#### 8.2.3 DATA_MISSING Handling Template

```python
def handle_response(response):
    if not response.get("error", False):
        # Success — but check if it's actually DATA_MISSING
        detail = response.get("detail", {})
        if detail.get("rule_result") == "DATA_MISSING":
            # Log as data quality issue, not engine failure
            log_data_quality_issue(
                level="WARNING",
                message=f"DATA_MISSING: {detail.get('reason', 'unknown')}",
                indicator_name=detail.get("indicator_name"),
                matched_name=detail.get("matched_name"),
                rule_result="DATA_MISSING"
            )
            return "DATA_MISSING"
        else:
            return "OK"
    else:
        # Error — handle per error code
        code = response.get("code", "INTERNAL_ERROR")
        return handle_error(code, response)
```

### 8.3 Cross-System Normalization

When consuming responses from multiple systems, normalize error codes to a canonical form:

| Original Code | From System | Canonical Code | Category |
|--------------|-------------|----------------|----------|
| `INTERNAL_ERROR` | Any | `INTERNAL_ERROR` | System |
| `ENGINE_DECIDE_FAILED` | Alias Engine | `INTERNAL_ERROR` | System |
| `TIMEOUT` | Any | `TIMEOUT` | System |
| `RATE_LIMIT` | Alias Engine | `TIMEOUT` | System |
| `RULE_ENGINE_LOAD_FAILED` | Rule Engine | `SERVICE_UNAVAILABLE` | System |
| `ENGINE_INIT_FAILED` | Alias Engine | `SERVICE_UNAVAILABLE` | System |
| `SERVICE_UNAVAILABLE` | E Backend | `SERVICE_UNAVAILABLE` | System |
| `EMPTY_INDICATOR` | Rule Engine | `INVALID_REQUEST` | Input |
| `MISSING_REQUIRED_FIELD` | Alias Engine | `INVALID_REQUEST` | Input |
| `INVALID_REQUEST` | E Backend | `INVALID_REQUEST` | Input |
| `RULE_NOT_FOUND` | Rule Engine | `NOT_FOUND` | Data |
| `TASK_NOT_FOUND` | Alias Engine | `NOT_FOUND` | Data |
| `RESOURCE_NOT_FOUND` | E Backend | `NOT_FOUND` | Data |
| `CSV_PARSE_ERROR` | Rule Engine | `MALFORMED_DATA` | Data |
| `JSON_PARSE_ERROR` | Rule Engine | `MALFORMED_DATA` | Data |
| `BAD_PAYLOAD` | Alias Engine | `MALFORMED_DATA` | Data |
| `PAYLOAD_UNACCEPTABLE` | Alias Engine | `MALFORMED_DATA` | Data |
| `RULE_CONFLICT` | Rule Engine | `CONFLICT` | Engine |
| `TASK_ALREADY_TERMINAL` | Alias Engine | `CONFLICT` | Engine |
| `RESOURCE_CONFLICT` | E Backend | `CONFLICT` | Engine |

---

## 9. Error Code Category Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR CODE TAXONOMY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  INPUT VALIDATION │  │  ENGINE ERRORS   │                    │
│  │  (400/409/413/422) │  │  (409)           │                    │
│  │                   │  │                  │                    │
│  │  EMPTY_INDICATOR  │  │  RULE_CONFLICT   │                    │
│  │  EMPTY_MATCHED    │  │  BIDIRECTIONAL_  │                    │
│  │  INDICATOR_TOO_   │  │  CHECK_ERROR     │                    │
│  │  LONG             │  │  TASK_NOT_READY  │                    │
│  │  MATCHED_TOO_LONG │  │                  │                    │
│  │  PATTERN_EMPTY    │  │                  │                    │
│  │  INVALID_ALIAS_   │  │                  │                    │
│  │  FORMAT           │  │                  │                    │
│  │  BAD_PAYLOAD      │  │                  │                    │
│  │  UNKNOWN_TASK_    │  │                  │                    │
│  │  TYPE             │  │                  │                    │
│  │  MISSING_REQUIRED │  │                  │                    │
│  │  FIELD            │  │                  │                    │
│  │  PAYLOAD_         │  │                  │                    │
│  │  UNACCEPTABLE     │  │                  │                    │
│  │  TASK_ALREADY_    │  │                  │                    │
│  │  TERMINAL         │  │                  │                    │
│  │  INVALID_REQUEST  │  │                  │                    │
│  │  VARIETY_DETECT_  │  │                  │                    │
│  │  FAILED           │  │                  │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  SYSTEM ERRORS   │  │  DATA ERRORS     │                    │
│  │  (500/503/504)   │  │  (404/422)       │                    │
│  │                   │  │                  │                    │
│  │  INTERNAL_ERROR  │  │  RULE_NOT_FOUND  │                    │
│  │  ENGINE_DECIDE_  │  │  TASK_NOT_FOUND  │                    │
│  │  FAILED          │  │  RESOURCE_NOT_   │                    │
│  │  RULE_ENGINE_    │  │  FOUND           │                    │
│  │  LOAD_FAILED     │  │  ALIAS_MAP_NOT_  │                    │
│  │  ENGINE_INIT_    │  │  FOUND           │                    │
│  │  FAILED          │  │  ALIAS_MAP_      │                    │
│  │  SERVICE_        │  │  CORRUPT         │                    │
│  │  UNAVAILABLE     │  │  CSV_PARSE_ERROR │                    │
│  │  TIMEOUT         │  │  JSON_PARSE_     │                    │
│  │  RATE_LIMIT      │  │  ERROR           │                    │
│  │                   │  │                  │                    │
│  │  TASK_NOT_READY  │  │  DATA_MISSING    │                    │
│  │  (retryable)     │  │  [SPECIAL]       │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Quick Reference: Error Code → Action

| Error Code | Action | Retry? |
|-----------|--------|--------|
| `OK` | ✅ Proceed | — |
| `DATA_MISSING` | Log as data quality issue; upstream fix | ❌ |
| `EMPTY_INDICATOR` / `EMPTY_MATCHED` | Fix request payload | ❌ |
| `INDICATOR_TOO_LONG` / `MATCHED_TOO_LONG` | Truncate input | ❌ |
| `PATTERN_EMPTY` | Fix pattern definition | ❌ |
| `INVALID_ALIAS_FORMAT` | Fix alias format | ❌ |
| `BAD_PAYLOAD` / `UNKNOWN_TASK_TYPE` | Fix request | ❌ |
| `MISSING_REQUIRED_FIELD` | Add missing field | ❌ |
| `PAYLOAD_UNACCEPTABLE` | Fix semantics | ❌ |
| `TASK_ALREADY_TERMINAL` | Do not modify | ❌ |
| `INVALID_REQUEST` | Fix request | ❌ |
| `VARIETY_DETECT_FAILED` | Verify commodity name | ❌ |
| `CSV_PARSE_ERROR` / `JSON_PARSE_ERROR` | Fix data format | ❌ |
| `RULE_NOT_FOUND` / `TASK_NOT_FOUND` / `RESOURCE_NOT_FOUND` | Verify ID/path | ❌ |
| `RULE_CONFLICT` / `BIDIRECTIONAL_CHECK_ERROR` | Investigate rule defs | ❌ |
| `INTERNAL_ERROR` / `ENGINE_DECIDE_FAILED` | Retry with backoff | ✅ |
| `RULE_ENGINE_LOAD_FAILED` / `ENGINE_INIT_FAILED` | Retry with backoff | ✅ |
| `SERVICE_UNAVAILABLE` | Retry with backoff | ✅ |
| `TIMEOUT` | Retry with backoff | ✅ |
| `RATE_LIMIT` | Honor `Retry-After` header | ✅ |
| `TASK_NOT_READY` | Retry after task becomes ready | ✅ |
| `ALIAS_MAP_NOT_FOUND` | Retry (file may re-appear) | ✅ |
| `ALIAS_MAP_CORRUPT` | Retry (file may re-sync) | ✅ |
| `RESOURCE_CONFLICT` | Resolve conflict manually | ❌ |

---

## 11. Appendix: HTTP Status Code Mapping

| HTTP Status | Meaning | Applicable Codes |
|-------------|---------|-----------------|
| 200 OK | Success | `OK`, `DATA_MISSING` (with `error: false`) |
| 400 Bad Request | Malformed or invalid request | `EMPTY_INDICATOR`, `EMPTY_MATCHED`, `PATTERN_EMPTY`, `INVALID_ALIAS_FORMAT`, `BAD_PAYLOAD`, `UNKNOWN_TASK_TYPE`, `MISSING_REQUIRED_FIELD`, `INVALID_REQUEST` |
| 404 Not Found | Resource does not exist | `RULE_NOT_FOUND`, `TASK_NOT_FOUND`, `ALIAS_MAP_NOT_FOUND`, `RESOURCE_NOT_FOUND` |
| 409 Conflict | State conflict | `RULE_CONFLICT`, `BIDIRECTIONAL_CHECK_ERROR`, `TASK_NOT_READY`, `TASK_ALREADY_TERMINAL`, `RESOURCE_CONFLICT` |
| 413 Payload Too Large | Input exceeds limits | `INDICATOR_TOO_LONG`, `MATCHED_TOO_LONG` |
| 422 Unprocessable Entity | Valid format, invalid semantics | `PAYLOAD_UNACCEPTABLE`, `VARIETY_DETECT_FAILED`, `ALIAS_MAP_CORRUPT`, `CSV_PARSE_ERROR`, `JSON_PARSE_ERROR`, `DATA_MISSING` |
| 429 Too Many Requests | Rate limit exceeded | `RATE_LIMIT` |
| 500 Internal Server Error | Unexpected engine error | `INTERNAL_ERROR`, `ENGINE_DECIDE_FAILED` |
| 503 Service Unavailable | System not ready | `RULE_ENGINE_LOAD_FAILED`, `ENGINE_INIT_FAILED`, `SERVICE_UNAVAILABLE` |
| 504 Gateway Timeout | Operation timed out | `TIMEOUT` |

---

*End of document. This specification is normative for all V86 rule engine, alias engine, and E backend integrations. Consumers MUST implement handling per §8.*
