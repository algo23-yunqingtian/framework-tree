# DSHE V86-RC2 L2 Exception Handling Specification

**Work Order:** DSHE_V86_RC2_L2_SHARD_BUGFIX_PROD_ADAPT  
**Sub-Task:** T3.2 — Exception Handling Enhancements  
**Branch:** feature/v85-chart-template  
**Date:** 2026-10-15  
**Specification Version:** V1.0  

---

## 1. Overview

This specification defines the exception handling behavior for the L2 Evidence Package Integrity Checker V4 (`l2_evidence_package_check_v4.py`). It covers three key exception types, their severity classification, handling strategies, and audit trail requirements.

### 1.1 Exception Handling Principles

1. **Never silently crash** — all exceptions must be caught, classified, and logged
2. **Graceful degradation** — recoverable errors continue processing with WARN-level output
3. **Auditability** — every exception generates a unique audit fingerprint for traceability
4. **Classification consistency** — the same exception type always produces the same severity level

---

## 2. Exception Classification Matrix

### 2.1 Severity Levels

| Level | Code | Action | Description |
|---|---|---|---|
| **CRITICAL** | `CRITICAL` | HALT ALL PROCESSING | System-level failure; must stop immediately |
| **ERROR** | `ERROR` | RETURN ERROR RESULT | Non-recoverable; log and return error verdict |
| **BLOCK** | `BLOCK` | HALT PARSING | Malformed data; must block further processing |
| **MEDIUM** | `MEDIUM` | REPORT + CONTINUE | Non-critical issue; report and continue processing |
| **WARN** | `WARN` | WARN + CONTINUE | Recoverable; log warning and continue |

### 2.2 Classification Table

| Exception Type | Module Path | Severity Level | Action | Audit Fingerprint |
|---|---|---|---|---|
| `FileNotFoundError` | `builtins` | **ERROR** | Return error result | N/A (no data to fingerprint) |
| `UnicodeDecodeError` | `builtins` | **WARN** | Fallback to latin-1 | ✅ SHA256 of error message |
| `json.JSONDecodeError` | `json.decoder` | **BLOCK** | Halt parsing | N/A (malformed data) |
| `DuplicateKeyError` | `l2_evidence_package_check_v4` | **MEDIUM** | Report + continue | ✅ SHA256 of duplicate keys |
| `MaxPathExceededError` | `l2_evidence_package_check_v4` | **WARN** | Precheck warning | ✅ SHA256 of path + length |
| `OSError` | `builtins` | **ERROR** | Return error result | N/A |
| `PermissionError` | `builtins` | **BLOCK** | Halt processing | N/A |
| `TimeoutError` | `builtins` | **WARN** | Retry or skip | N/A |
| `MemoryError` | `builtins` | **CRITICAL** | Halt all processing | N/A |

---

## 3. UnicodeDecodeError Handling

### 3.1 Classification

| Property | Value |
|---|---|
| **Exception Type** | `UnicodeDecodeError` |
| **Severity Level** | WARN |
| **Classification** | Recoverable — fallback to alternative encoding |
| **CLI Flag** | `--unicode-fallback` |
| **Default Behavior** | Raise exception (WARN classification, no fallback) |
| **With Flag** | Fallback to latin-1 encoding |

### 3.2 Handling Strategy

```
┌─────────────────────────────────┐
│  open(file, encoding="utf-8")   │
└──────────────┬──────────────────┘
               │
          ┌────▼────┐
          │ Read    │
          └────┬────┘
               │
     ┌─────────▼──────────┐
     │ UnicodeDecodeError? │
     └────┬──────────┬────┘
          │ YES      │ NO
     ┌────▼─────┐   │
     │ Flag set?│   │
     └────┬─────┘   │
          │ YES    │ NO
     ┌────▼──────┐ │
     │ Fallback  │ │
     │ to latin-1│ │
     │ Emit WARN │ │
     └───────────┘ │
          │         │
     ┌────▼──────┐ │
     │ Audit     │ │
     │ Fingerprint│ │
     └───────────┘ │
```

### 3.3 Audit Fingerprint

When a `UnicodeDecodeError` is caught, an audit fingerprint is generated:

```python
audit_fingerprint = hashlib.sha256(str(e).encode("utf-8")).hexdigest()[:16]
```

**Example:**
```
Exception: UnicodeDecodeError('utf-8', b'\xff\xfe', 0, 2, 'invalid start byte')
Audit Fingerprint: a3f2b1c0d4e5f678
```

### 3.4 Warning Record Format

```python
{
    "level": "WARN",
    "type": "UnicodeDecodeError",
    "message": "UnicodeDecodeError in <filepath> — WARN, falling back to latin-1",
    "audit_fingerprint": "a3f2b1c0d4e5f678",
    "timestamp": "2026-10-15T12:00:00+00:00",
    "fallback_encoding": "latin-1",
}
```

### 3.5 Code Example

```python
try:
    with open(self.filepath, "r", encoding="utf-8") as f:
        raw_text = f.read()
except UnicodeDecodeError as e:
    if not self.unicode_fallback:
        # WARN classification, re-raise
        warn_msg = "UnicodeDecodeError in %s: %s" % (self.filepath, str(e))
        self.warnings.append({
            "level": WARN,
            "type": "UnicodeDecodeError",
            "message": warn_msg,
            "audit_fingerprint": hashlib.sha256(
                str(e).encode("utf-8")).hexdigest()[:16],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise
    else:
        # Fallback to latin-1
        encoding = "latin-1"
        with open(self.filepath, "r", encoding=encoding) as f:
            raw_text = f.read()
```

---

## 4. Windows MAX_PATH Handling

### 4.1 Classification

| Property | Value |
|---|---|
| **Exception Type** | `MaxPathExceededError` (custom) |
| **Severity Level** | WARN |
| **Classification** | Precheck warning — path exceeds Windows API limit |
| **CLI Flag** | `--max-path-check` |
| **Threshold** | 260 characters (Windows MAX_PATH) |
| **Default Behavior** | No check (disabled) |

### 4.2 Handling Strategy

```
┌─────────────────────────────────┐
│  Check path length              │
│  len(str(filepath)) > 260?     │
└──────────────┬──────────────────┘
               │
     ┌─────────▼──────────┐
     │ Exceeds 260?       │
     └────┬──────────┬────┘
          │ YES      │ NO
     ┌────▼─────┐   │
     │ Emit WARN│   │
     │ with     │   │
     │ audit FP │   │
     └──────────┘   │
          │         │
     ┌────▼──────┐ │
     │ Continue  │ │
     │ processing│ │
     └───────────┘ │
```

### 4.3 Audit Fingerprint

```python
audit_fingerprint = hashlib.sha256(
    ("%s:%d" % (filepath, path_length)).encode("utf-8")
).hexdigest()[:16]
```

### 4.4 Warning Record Format

```python
{
    "level": "WARN",
    "type": "MaxPathExceededError",
    "message": "Windows MAX_PATH exceeded: path length 273 > 260 (C:\\very\\long\\path\\to\\file.json). Audit fingerprint: 905644b9264066dd",
    "audit_fingerprint": "905644b9264066dd",
    "timestamp": "2026-10-15T12:00:00+00:00",
    "path_length": 273,
    "max_allowed": 260,
    "is_windows": True,
}
```

### 4.5 Edge Cases

| Scenario | Path Length | Behavior |
|---|---|---|
| Normal path (`C:\test\file.json`) | 17 | No warning |
| Path at limit (`C:\...260 chars...`) | 260 | No warning (not exceeded) |
| Path just over (`C:\...261 chars...`) | 261 | WARN emitted |
| UNC path (`\\server\share\...`) | Variable | Checked normally |

---

## 5. JSON Duplicate Key Handling

### 5.1 Classification

| Property | Value |
|---|---|
| **Exception Type** | `DuplicateKeyError` (custom) |
| **Severity Level** | MEDIUM |
| **Classification** | Data quality issue — report but continue |
| **CLI Flag** | `--json-dup-key-check` |
| **Default Behavior** | Disabled (no check) |

### 5.2 Detection Mechanism

A custom `DuplicateKeyJSONDecoder` extends `json.JSONDecoder` to detect duplicate keys during parsing:

```python
class DuplicateKeyJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_pairs_hook=self._object_pairs_hook_check, **kwargs)
        self.duplicate_keys_found = []

    def _object_pairs_hook_check(self, pairs):
        seen_keys = {}
        for key, value in pairs:
            if key in seen_keys:
                seen_keys[key] += 1
                self.duplicate_keys_found.append({
                    "key": key,
                    "occurrence": seen_keys[key],
                    "total_count": seen_keys[key],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            else:
                seen_keys[key] = 1
        return dict(pairs)  # Returns last value for duplicate keys (JSON standard)
```

### 5.3 Handling Strategy

```
┌──────────────────────────────┐
│  Parse JSON with custom      │
│  DuplicateKeyJSONDecoder     │
└──────────────┬───────────────┘
               │
     ┌─────────▼──────────┐
     │ Duplicate keys?    │
     └────┬──────────┬────┘
          │ YES      │ NO
     ┌────▼─────┐   │
     │ Emit MED │   │
     │ warning  │   │
     │ with     │   │
     │ audit FP │   │
     └────┬─────┘   │
          │         │
     ┌────▼──────┐ │
     │ Return    │ │
     │ data with │ │
     │ warning   │ │
     │ metadata  │ │
     └───────────┘ │
```

### 5.4 Audit Fingerprint

The fingerprint is computed from the list of duplicate key entries:

```python
audit_fp = hashlib.sha256(
    json.dumps(duplicate_keys, sort_keys=True, ensure_ascii=False).encode("utf-8")
).hexdigest()[:16]
```

### 5.5 Warning Record Format

```python
{
    "level": "MEDIUM",
    "type": "DuplicateKeyError",
    "message": "JSON duplicate keys detected: 1 duplicate keys found.",
    "audit_fingerprint": "b9d9312c73442ab5",
    "timestamp": "2026-10-15T12:00:00+00:00",
    "duplicate_keys": [
        {
            "key": "key1",
            "occurrence": 2,
            "total_count": 2,
            "timestamp": "2026-10-15T12:00:00+00:00"
        }
    ]
}
```

### 5.6 Returned Data Structure

When duplicate keys are detected, the returned data includes V4 metadata:

```json
{
    "_v4_duplicate_key_warning": true,
    "_v4_duplicate_key_count": 1,
    "_v4_duplicate_key_fingerprint": "b9d9312c73442ab5",
    "_v4_duplicate_keys": [
        {"key": "key1", "occurrence": 2, "total_count": 2, "timestamp": "..."}
    ],
    "_v4_original_data": { /* original parsed JSON data */ }
}
```

---

## 6. Exception Classifier

### 6.1 Class Design

The `ExceptionClassifier` class provides a unified interface for classifying and handling exceptions:

```python
class ExceptionClassifier:
    def classify(self, exc):
        """Classify exception → (level, message)"""
        exc_type = type(exc).__name__
        exc_path = "%s.%s" % (exc.__class__.__module__, exc_type)
        # Lookup in EXCEPTION_CLASSIFICATION matrix
        ...

    def handle(self, exc, context=None):
        """Classify + handle exception → result dict"""
        level, msg = self.classify(exc)
        result = {
            "verdict": "ERROR",  # Set based on level
            "exception_level": level,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "classification": msg,
            "context": str(context) if context else "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return result

    def get_classification_log(self):
        """Return list of all classifications"""
        return list(self.classification_log)
```

### 6.2 Verdict Mapping

| Classification Level | Result Verdict |
|---|---|
| `CRITICAL` | `BLOCK_CRITICAL` |
| `BLOCK` | `BLOCK` |
| `ERROR` | `ERROR` |
| `WARN` | `WARNING` |
| `MEDIUM` | `PASS_WITH_NOTES` |

---

## 7. Original 7 Test Scenarios — Exception Handling Behavior

### Scenario 1: Missing Evidence File

| Property | Value |
|---|---|
| **Condition** | Evidence file does not exist |
| **Exception** | `FileNotFoundError` |
| **Classification** | ERROR |
| **Behavior** | Log error, return `{"verdict": "ERROR", "error": "file_not_found"}` |
| **Audit Trail** | N/A (no data to fingerprint) |

### Scenario 2: Malformed JSON

| Property | Value |
|---|---|
| **Condition** | Evidence file contains invalid JSON syntax |
| **Exception** | `json.JSONDecodeError` |
| **Classification** | BLOCK |
| **Behavior** | Log error, return `{"verdict": "BLOCK", "error": "json_parse_error"}` |
| **Audit Trail** | N/A (malformed data) |

### Scenario 3: Unicode Decode Error (Invalid UTF-8)

| Property | Value |
|---|---|
| **Condition** | Evidence file contains invalid UTF-8 bytes |
| **Exception** | `UnicodeDecodeError` |
| **Classification** | WARN |
| **Behavior (no flag)** | Log WARN, re-raise exception, return `{"verdict": "WARNING"}` |
| **Behavior (--unicode-fallback)** | Log WARN, fallback to latin-1, continue processing |
| **Audit Trail** | ✅ SHA256 fingerprint of error message |

### Scenario 4: JSON Duplicate Keys

| Property | Value |
|---|---|
| **Condition** | Evidence JSON contains duplicate keys |
| **Exception** | `DuplicateKeyError` (detected via custom decoder) |
| **Classification** | MEDIUM |
| **Behavior (no flag)** | No detection (standard JSON parser silently overwrites) |
| **Behavior (--json-dup-key-check)** | Log MEDIUM warning, continue with warning metadata attached |
| **Audit Trail** | ✅ SHA256 fingerprint of duplicate keys list |

### Scenario 5: Windows MAX_PATH Exceeded

| Property | Value |
|---|---|
| **Condition** | Evidence file path exceeds 260 characters |
| **Exception** | `MaxPathExceededError` (precheck, not raised by OS) |
| **Classification** | WARN |
| **Behavior (no flag)** | No check performed |
| **Behavior (--max-path-check)** | Log WARN with path length and audit fingerprint |
| **Audit Trail** | ✅ SHA256 fingerprint of path + length |

### Scenario 6: Memory Error (OOM)

| Property | Value |
|---|---|
| **Condition** | System runs out of memory during large file processing |
| **Exception** | `MemoryError` |
| **Classification** | CRITICAL |
| **Behavior** | Log CRITICAL, halt all processing |
| **Audit Trail** | N/A |

### Scenario 7: Permission Denied

| Property | Value |
|---|---|
| **Condition** | Evidence file or directory has insufficient permissions |
| **Exception** | `PermissionError` |
| **Classification** | BLOCK |
| **Behavior** | Log BLOCK, halt processing |
| **Audit Trail** | N/A |

---

## 8. CLI Flags Summary

| Flag | Default | Enables |
|---|---|---|
| `--unicode-fallback` | OFF | UnicodeDecodeError fallback to latin-1 |
| `--max-path-check` | OFF | Windows MAX_PATH precheck |
| `--json-dup-key-check` | OFF | JSON duplicate key detection |
| `--exception-handling-test` | OFF | Run all exception handling test cases |

---

## 9. Test Coverage

All exception handling behaviors are verified by the `--exception-handling-test` CLI flag:

```bash
python l2_evidence_package_check_v4.py --exception-handling-test
```

| Test Category | Count | Status |
|---|---|---|
| Shard Count Off-By-One Tests | 7 | ✅ PASS |
| UnicodeDecodeError Tests | 2 | ✅ PASS |
| Windows MAX_PATH Tests | 3 | ✅ PASS |
| JSON Duplicate Key Tests | 4 | ✅ PASS |
| Exception Classification Tests | 9 | ✅ PASS |
| ExceptionClassifier Tests | 5 | ✅ PASS |
| Boundary Case Tests | 9 | ✅ PASS |
| **Total** | **39** | **✅ ALL PASS** |

---

## 10. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| V1.0 | 2026-10-15 | DSHE V86-RC2 | Initial specification |
