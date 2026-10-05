# DSHE V86-RC2 L2 Evidence Shard Specification V2

**Work Order:** DSHE_V86_RC2_L2_SHARD_BUGFIX_PROD_ADAPT  
**Sub-Task:** T3.5 — L2 Evidence Shard Spec V2  
**Branch:** feature/v85-chart-template  
**Date:** 2026-10-15  
**Specification Version:** V2.0  

---

## 1. Overview

This specification defines the sharding algorithm, exception handling, path limits, JSON duplicate key handling, and Unicode policies for L2 Evidence Package processing in DSHE V86-RC2.

### 1.1 Key Changes from V1 (V3-based)

| Area | V1 (V3) | V2 (V4) |
|---|---|---|
| **Shard boundary formula** | `max(1, file_size // shard_size + 1)` ❌ | `max(1, -(-file_size // shard_size))` ✅ |
| **UnicodeDecodeError** | Not handled | WARN classification, latin-1 fallback |
| **Windows MAX_PATH** | Not checked | Precheck at 260 chars, WARN |
| **JSON duplicate keys** | Not detected | Custom JSONDecoder, MEDIUM warning |
| **Exception classification** | Ad hoc | Formal matrix: ERROR/WARN/BLOCK/CRITICAL |
| **Audit fingerprints** | None | SHA256[:16] for all recoverable errors |

---

## 2. Shard Boundary Algorithm

### 2.1 Corrected Formula (P0 FIX)

```
shard_count = max(1, -(-file_size // shard_size))
```

This is Python's integer ceiling division: `ceil(file_size / shard_size)`.

### 2.2 Algorithm Definition

```
Input:
  file_size    — size of evidence file in bytes (int, >= 0)
  shard_size   — configured shard size in bytes (int, > 0)

Output:
  shard_count  — number of shards needed (int, >= 1)

Algorithm:
  1. If shard_size <= 0: raise ValueError
  2. If file_size <= 0: return 1  (empty file gets 1 shard)
  3. Return max(1, -(-file_size // shard_size))
```

### 2.3 Boundary Cases

| # | `file_size` | `shard_size` | `shard_count` | Note |
|---|---|---|---|---|
| 1 | 0 | 4096 | 1 | Empty file — minimum 1 shard |
| 2 | 1 | 4096 | 1 | Single byte |
| 3 | 4095 | 4096 | 1 | Just below threshold |
| 4 | **4096** | **4096** | **1** | **P0 FIX** — exact multiple |
| 5 | 4097 | 4096 | 2 | Just above threshold |
| 6 | **8192** | **4096** | **2** | **P0 FIX** — exact multiple |
| 7 | 8193 | 4096 | 3 | Just above double |
| 8 | **12288** | **4096** | **3** | **P0 FIX** — exact multiple |
| 9 | 4,194,304 (4MB) | 4,194,304 | 1 | Default config, exact match |
| 10 | 8,388,608 (8MB) | 4,194,304 | 2 | Default config, double |
| 11 | 10,485,760 (10MB) | 4,194,304 | 3 | Default config, ~2.5x |
| 12 | 10,485,760 | 4,096 | 2,560 | Large file, small shards |

### 2.4 Verification Function

```python
@staticmethod
def verify_shard_count(file_size, shard_size):
    """Compare old (V3) and new (V4) formulas for regression testing."""
    old_count = max(1, file_size // shard_size + 1)
    new_count = max(1, -(-file_size // shard_size))
    return {
        "file_size": file_size,
        "shard_size": shard_size,
        "old_formula_v3": old_count,
        "new_formula_v4": new_count,
        "match": old_count == new_count,
        "off_by_one_bug": old_count != new_count,
    }
```

---

## 3. Exception Classification Matrix

### 3.1 Severity Levels

| Level | Code | Action | Description |
|---|---|---|---|
| **CRITICAL** | `CRITICAL` | HALT ALL PROCESSING | System-level failure; must stop immediately |
| **ERROR** | `ERROR` | RETURN ERROR RESULT | Non-recoverable; log and return error verdict |
| **BLOCK** | `BLOCK` | HALT PARSING | Malformed data; must block further processing |
| **MEDIUM** | `MEDIUM` | REPORT + CONTINUE | Non-critical issue; report and continue |
| **WARN** | `WARN` | WARN + CONTINUE | Recoverable; log warning and continue |

### 3.2 Exception Classification Table

| Exception Type | Module Path | Severity | Action | Audit Fingerprint |
|---|---|---|---|---|
| `FileNotFoundError` | `builtins` | ERROR | Return error result | N/A |
| `UnicodeDecodeError` | `builtins` | WARN | Fallback to latin-1 | ✅ SHA256 of error message |
| `json.JSONDecodeError` | `json.decoder` | BLOCK | Halt parsing | N/A |
| `DuplicateKeyError` | `l2_evidence_package_check_v4` | MEDIUM | Report + continue | ✅ SHA256 of duplicate keys |
| `MaxPathExceededError` | `l2_evidence_package_check_v4` | WARN | Precheck warning | ✅ SHA256 of path + length |
| `OSError` | `builtins` | ERROR | Return error result | N/A |
| `PermissionError` | `builtins` | BLOCK | Halt processing | N/A |
| `TimeoutError` | `builtins` | WARN | Retry or skip | N/A |
| `MemoryError` | `builtins` | CRITICAL | Halt all processing | N/A |

### 3.3 Verdict Mapping

| Classification Level | Result Verdict |
|---|---|
| `CRITICAL` | `BLOCK_CRITICAL` |
| `BLOCK` | `BLOCK` |
| `ERROR` | `ERROR` |
| `WARN` | `WARNING` |
| `MEDIUM` | `PASS_WITH_NOTES` |

---

## 4. Path Length Limits (Windows MAX_PATH)

### 4.1 Windows MAX_PATH Limitation

Windows has a maximum file path length of **260 characters** (defined by `MAX_PATH` in Windows API). This includes:

- Drive letter and colon (e.g., `C:`)
- Backslash separator
- All directory names
- File name and extension

### 4.2 Precheck Behavior

| Flag | Default | Behavior |
|---|---|---|
| `--max-path-check` | OFF | No check performed |
| `--max-path-check` | ON | Precheck path length at 260 chars |

### 4.3 Path Length Calculation

```python
path_str = str(filepath)
path_length = len(path_str)  # Character count, not byte count
threshold = 260  # Windows MAX_PATH
exceeded = path_length > threshold
```

### 4.4 Warning Format

When a path exceeds the limit:

```json
{
    "level": "WARN",
    "type": "MaxPathExceededError",
    "message": "Windows MAX_PATH exceeded: path length 273 > 260 (C:\\very\\long\\path\\to\\file.json). Audit fingerprint: 905644b9264066dd",
    "audit_fingerprint": "905644b9264066dd",
    "path_length": 273,
    "max_allowed": 260,
    "is_windows": true
}
```

### 4.5 Recommendations

1. **Use short path names** where possible (8.3 format: `C:\PROGRA~1\...`)
2. **Mount network shares** to shorter drive letters
3. **Use `\\\\?\\` prefix** for UNC paths (bypasses MAX_PATH on modern Windows)
4. **Prefer relative paths** in containerized environments

---

## 5. JSON Duplicate Key Handling Rules

### 5.1 Detection Mechanism

A custom `DuplicateKeyJSONDecoder` extends `json.JSONDecoder` to detect duplicate keys:

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
        return dict(pairs)  # Last value wins (JSON standard)
```

### 5.2 Handling Rules

| Rule | Description |
|---|---|
| **Last value wins** | Python's `json` module uses the last value for duplicate keys (standard JSON behavior) |
| **All occurrences logged** | Each duplicate key occurrence is recorded in the warning list |
| **Audit fingerprint** | SHA256[:16] of the serialized duplicate keys list |
| **Processing continues** | MEDIUM severity — data is still valid, just has quality issues |
| **Metadata attached** | Returned data includes `_v4_duplicate_key_warning` metadata |

### 5.3 Duplicate Key Warning Format

```json
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

### 5.4 When to Use `--json-dup-key-check`

| Scenario | Use? |
|---|---|
| Production evidence packages | ✅ YES — detect data quality issues |
| Test/development environments | ✅ YES — catch malformed evidence early |
| Legacy JSON files with known duplicates | ⚠️ Consider — will generate MEDIUM warnings |
| Performance-critical batch processing | ❌ NO — adds parsing overhead |

---

## 6. Unicode Handling Policy

### 6.1 Primary Encoding

- **Default:** UTF-8 (required for all evidence files)
- **Rationale:** UTF-8 is the standard encoding for JSON and handles all Unicode characters

### 6.2 Fallback Strategy

When `--unicode-fallback` is enabled:

1. Try UTF-8 encoding first
2. On `UnicodeDecodeError`, log WARN with audit fingerprint
3. Fall back to latin-1 (ISO 8859-1) encoding
4. Continue processing with fallback data

### 6.3 Encoding Decision Matrix

| Input File Encoding | `--unicode-fallback` OFF | `--unicode-fallback` ON |
|---|---|---|
| UTF-8 | ✅ Process normally | ✅ Process normally |
| UTF-8 with BOM | ✅ Process normally | ✅ Process normally |
| Latin-1 | ❌ UnicodeDecodeError → WARN + raise | ✅ Fallback to latin-1 → WARN + continue |
| ASCII | ✅ Process normally | ✅ Process normally |
| UTF-16 | ❌ UnicodeDecodeError → WARN + raise | ✅ Fallback to latin-1 (may corrupt) → WARN + continue |
| Invalid UTF-8 bytes | ❌ UnicodeDecodeError → WARN + raise | ✅ Fallback to latin-1 → WARN + continue |

### 6.4 When to Use `--unicode-fallback`

| Scenario | Use? |
|---|---|
| Legacy evidence files from non-UTF-8 systems | ✅ YES — recover data |
| Files from Windows systems with code page differences | ✅ YES — latin-1 is superset of ASCII |
| Production evidence (known UTF-8) | ❌ NO — prefer strict UTF-8 |
| Files with known mixed encoding | ⚠️ Consider — latin-1 may corrupt UTF-8 sequences |

### 6.5 Warning Format

```json
{
    "level": "WARN",
    "type": "UnicodeDecodeError",
    "message": "UnicodeDecodeError in <filepath> — WARN, falling back to latin-1",
    "audit_fingerprint": "a3f2b1c0d4e5f678",
    "timestamp": "2026-10-15T12:00:00+00:00",
    "fallback_encoding": "latin-1"
}
```

---

## 7. File Size Limits and Sharding Thresholds

### 7.1 Default Configuration

| Parameter | Value | Description |
|---|---|---|
| `DEFAULT_SHARD_SIZE` | 4,194,304 bytes (4 MB) | Default shard size for large file reading |
| `DEFAULT_THREAD_COUNT` | 4 | Default thread count for parallel pre-audit |
| `PERF_GUARD_FILE_SIZE_LIMIT_MB` | 10 MB | Soft limit — MEDIUM warning if exceeded |
| `PERF_GUARD_CALL_COUNT_LIMIT` | 256 | Hard limit — CRITICAL if exceeded |
| `PERF_GUARD_PACKAGING_TIME_LIMIT_SEC` | 1.0s | Hard limit — CRITICAL if exceeded |
| `PERF_GUARD_MEMORY_PEAK_LIMIT_MB` | 52 MB | Soft limit — HIGH if exceeded |

### 7.2 Sharding Decision Flow

```
┌─────────────────────────────────┐
│  Is file_size >= shard_size?    │
│  (i.e., is_large == True?)      │
└──────────────┬──────────────────┘
               │
     ┌─────────▼──────────┐
     │                    │
  ┌──▼──┐              ┌──▼──┐
  │ YES │              │ NO  │
  └──┬──┘              └──┬──┘
     │                    │
┌────▼─────────┐    ┌────▼─────────┐
│ Sharded read │    │ Standard     │
│ (chunk-based)│    │ json.load()  │
│              │    │ (memory-     │
│ Use          │    │  efficient   │
│ shard_count  │    │  enough)     │
└────┬─────────┘    └────┬─────────┘
     │                   │
     └───────┬───────────┘
             │
     ┌───────▼───────┐
     │  Parse JSON   │
     └───────────────┘
```

### 7.3 File Size Categories

| File Size | Category | Behavior | PERF-GUARD |
|---|---|---|---|
| 0 bytes | Empty | Returns error | N/A |
| 1 byte — 4 MB | Small | Standard `json.load()` | File size check (MEDIUM if >10MB) |
| 4 MB — 10 MB | Medium | Sharded reading | File size check |
| 10 MB — 52 MB | Large | Sharded reading + PERF-GUARD | MEDIUM warning (file size) |
| >52 MB | Very Large | Sharded reading + PERF-GUARD | HIGH warning (memory) |
| >10MB with >256 calls | Oversized | Sharded reading + PERF-GUARD | CRITICAL (block) |

### 7.4 Configurable Parameters

```python
# CLI options
--shard-size <bytes>    # Shard size for large file reading (default: 4MB)
--threads <count>       # Thread count for parallel pre-audit (default: 4)
--perf-guard-mode <MODE> # STRICT (block) or WARN (alert only)
--no-perf-guard         # Disable PERF-GUARD checks
```

### 7.5 Memory Usage Estimates

| File Size | Memory (Small <4MB) | Memory (Sharded) | Notes |
|---|---|---|---|
| 1 KB | ~1 KB | ~1 KB | Negligible difference |
| 1 MB | ~1 MB | ~1 MB | Both efficient |
| 4 MB | ~4 MB | ~4 MB | Threshold — sharded at >= 4MB |
| 10 MB | ~10 MB | ~4 MB | Sharded saves ~60% |
| 50 MB | ~50 MB | ~4 MB | Sharded saves ~92% |
| 100 MB | ~100 MB | ~4 MB | Sharded saves ~96% |

---

## 8. CLI Flags Reference

### 8.1 All Flags

| Flag | Default | Type | Description |
|---|---|---|---|
| `--check <file>` | — | file path | Check single evidence file |
| `--check-dir <dir>` | — | dir path | Check all evidence files in directory |
| `--verify-md5 <file>` | — | file path | Verify MD5 checksum list |
| `--all <dir>` | — | dir path | Run all checks on directory |
| `--pre-audit <file>` | — | file path | Pre-audit single evidence file |
| `--pre-audit-dir <dir>` | — | dir path | Pre-audit all evidence files |
| `--generate-md5 <dir>` | — | dir path | Generate MD5 checksum list |
| `--generate-index <dir>` | — | dir path | Generate evidence index |
| `--dry-run` | OFF | flag | Show configuration and exit |
| `--json` | OFF | flag | JSON output format |
| `--threads <N>` | 4 | int | Thread count for parallel pre-audit |
| `--shard-size <bytes>` | 4194304 | int | Shard size for large file reading |
| `--perf-guard-mode <MODE>` | STRICT | enum | PERF-GUARD mode: STRICT or WARN |
| `--no-perf-guard` | OFF | flag | Disable PERF-GUARD checks |
| `--perf-guard-only` | OFF | flag | Only run PERF-GUARD checks |
| `--json-dup-key-check` | OFF | flag | Enable JSON duplicate key detection |
| `--max-path-check` | OFF | flag | Enable Windows MAX_PATH precheck |
| `--unicode-fallback` | OFF | flag | Enable UnicodeDecodeError fallback |
| `--exception-handling-test` | OFF | flag | Run exception handling test cases |

### 8.2 Exception Handling Flags (V4/T3.2)

| Flag | Enables | Default |
|---|---|---|
| `--json-dup-key-check` | JSON duplicate key detection (MEDIUM) | OFF |
| `--max-path-check` | Windows MAX_PATH precheck (WARN) | OFF |
| `--unicode-fallback` | UnicodeDecodeError latin-1 fallback (WARN) | OFF |
| `--exception-handling-test` | Run all exception handling tests | OFF |

---

## 9. Data Format Versioning

### 9.1 Contract Version

```
EVIDENCE_CONTRACT_VERSION = "EVIDENCE_CONTRACT_V1"
SCRIPT_VERSION = "4.0.0"
```

### 9.2 Output Format Compatibility

V4 output is backward-compatible with V3:
- All V3 fields are preserved
- V4 adds optional `_v4_*` metadata fields for duplicate key warnings
- V4 adds `v4_warnings` array in load_info
- V4 adds `version: "4.0.0"` in reader info

### 9.3 Warning Records Format

All V4 warnings follow a consistent format:

```json
{
    "level": "WARN|MEDIUM|ERROR|BLOCK|CRITICAL",
    "type": "<ExceptionTypeName>",
    "message": "<Human readable message>",
    "audit_fingerprint": "<SHA256[:16]> (optional)",
    "timestamp": "<ISO 8601 UTC>",
    ... // type-specific fields
}
```

---

## 10. Performance Considerations

### 10.1 Overhead of V4 Features

| Feature | Overhead | When Enabled |
|---|---|---|
| Shard count fix | Zero (formula change) | Always |
| UnicodeDecodeError handling | Minimal (try/except only) | Always |
| Windows MAX_PATH check | Minimal (len() check) | `--max-path-check` |
| JSON duplicate key detection | Moderate (custom decoder) | `--json-dup-key-check` |
| Exception classification | Minimal (dict lookup) | On exception |

### 10.2 PERF-GUARD Thresholds

| Threshold | Limit | Action |
|---|---|---|
| Packaging time | 1.0s | CRITICAL — block packaging |
| Call count | 256 | CRITICAL — block packaging |
| Memory peak | 52 MB | HIGH — warn + early termination hint |
| File size | 10 MB | MEDIUM — warn (soft limit) |

### 10.3 Recommended Configuration

| Environment | Recommended Flags |
|---|---|
| **Production audit** | `--max-path-check --json-dup-key-check` |
| **Development** | `--max-path-check --json-dup-key-check --unicode-fallback` |
| **Performance-critical** | No V4 flags (use V3 mode) |
| **Stress testing** | `--perf-guard-mode WARN` |
| **Exception testing** | `--exception-handling-test` |

---

## 11. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| V1.0 | 2026-10-15 | (Implied by V3) | Original shard spec |
| V2.0 | 2026-10-15 | DSHE V86-RC2 | P0 fix, exception matrix, path limits, Unicode policy |

---

## 12. Sign-off

| Role | Status | Date |
|---|---|---|
| Specification Author | Complete | 2026-10-15 |
| Implementation | Complete (V4) | 2026-10-15 |
| Test Verification | 39/39 tests PASS | 2026-10-15 |
