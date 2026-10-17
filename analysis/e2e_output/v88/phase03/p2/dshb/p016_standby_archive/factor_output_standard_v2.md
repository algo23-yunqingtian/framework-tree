# DSHB P0-16 — Factor Output Standard v2 (IC/IR 产出规则加固)

**TASK_ID**: V88_PHASE03_P6_DSHB_P016_FACTOR_COMPUTE_STANDBY
**TASK**: T1 — IC-IR产出规则加固，双校验+异常截断保护
**AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
**GENERATED**: 2026-10-22
**STATUS**: COMPLETE

---

## 1. Overview

This document defines the **mandatory output specification** for all factor calculation results produced by `ic_ir_calc_skeleton.py`. Every result file MUST comply with this standard. Non-conforming outputs are considered corrupted and must be quarantined.

**Base standard**: `v88-factor-output-v2.0`
**Supersedes**: `v88-factor-output-v1.0` (P4 skeleton)

---

## 2. Dual-Checksum Protocol (MD5 + SHA256)

### 2.1 Requirement

Every output file (`.json`, `.csv`, `.txt`) produced by the calculation pipeline **MUST** have a companion dual-checksum sidecar file:

```
<filename>.checksum
```

### 2.2 Checksum File Format

```json
{
  "schema": "v88-factor-checksum-v2.0",
  "filename": "ic_result.json",
  "size_bytes": 4823,
  "md5": "AABBCCDD...",
  "sha256": "EEFF0011...",
  "algorithm_md5": "MD5",
  "algorithm_sha256": "SHA-256",
  "generated_at": "2026-10-22T22:00:00+08:00",
  "generator": "ic_ir_calc_skeleton.py v2.0",
  "factor_id": "momentum_20d",
  "variety": "PB"
}
```

### 2.3 Dual-Checksum Algorithm

```python
import hashlib

def dual_checksum(filepath):
    """Compute MD5 + SHA256 for a file."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()
```

### 2.4 Verification Protocol

Before any downstream consumer reads a result file:

1. Read the `.checksum` sidecar file
2. Compute fresh MD5+SHA256 of the data file
3. Compare with recorded values
4. **Both** must match — a single mismatch = DATA_CORRUPT
5. Log verification result to audit trail

```python
def verify_dual_checksum(filepath):
    """Verify dual-checksum integrity. Returns (passed, message)."""
    import json, os
    checksum_path = filepath + '.checksum'
    if not os.path.exists(checksum_path):
        return False, 'MISSING_CHECKSUM_FILE'
    with open(checksum_path, 'r') as f:
        expected = json.load(f)
    fresh_md5, fresh_sha256 = dual_checksum(filepath)
    md5_ok = fresh_md5 == expected['md5']
    sha256_ok = fresh_sha256 == expected['sha256']
    if md5_ok and sha256_ok:
        return True, 'DUAL_CHECKSUM_PASS'
    return False, f'CHECKSUM_MISMATCH: md5_ok={md5_ok}, sha256_ok={sha256_ok}'
```

---

## 3. Output Schema Definitions

### 3.1 IC Result Schema (`v88-factor-ic-result-v2.0`)

```json
{
  "schema": "v88-factor-ic-result-v2.0",
  "checksum_file": "ic_result.json.checksum",
  "factor_id": "string",
  "factor_name": "string",
  "variety": "PB | ZN | Recycle-PB",
  "date_range": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "trading_days": 0
  },
  "data_source": "WIND_DATA_LINK",
  "sample": {
    "count": 0,
    "valid_count": 0,
    "missing_count": 0,
    "anomaly_count": 0
  },
  "ic_series": [
    {"date": "YYYY-MM-DD", "ic": 0.0, "confidence": 0.95}
  ],
  "statistics": {
    "ic_mean": 0.0,
    "ic_std": 0.0,
    "ic_ir": 0.0,
    "ic_positive_rate": 0.0,
    "ic_t_statistic": 0.0,
    "ic_p_value": null
  },
  "quality": {
    "data_completeness_pct": 0.0,
    "calculation_errors": 0,
    "truncation_events": 0,
    "warnings": ["list of warning strings"]
  },
  "metadata": {
    "calculated_at": "ISO8601",
    "script_version": "v2.0",
    "python_version": "3.x",
    "checksum_md5": "AABB...",
    "checksum_sha256": "EEFF..."
  }
}
```

### 3.2 IR Result Schema (`v88-factor-ir-result-v2.0`)

```json
{
  "schema": "v88-factor-ir-result-v2.0",
  "checksum_file": "ir_result.json.checksum",
  "factor_id": "string",
  "variety": "PB | ZN | Recycle-PB",
  "date_range": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  },
  "data_source": "WIND_DATA_LINK",
  "ir_metrics": {
    "ir_mean": 0.0,
    "ir_annualized": 0.0,
    "ir_std": 0.0,
    "t_statistic": 0.0,
    "p_value": null,
    "significant_at_5pct": true
  },
  "ic_distribution": {
    "total_periods": 0,
    "positive_ic_count": 0,
    "negative_ic_count": 0,
    "zero_ic_count": 0,
    "ic_skewness": 0.0,
    "ic_kurtosis": 0.0
  },
  "quality": {
    "data_completeness_pct": 0.0,
    "calculation_errors": 0,
    "truncation_events": 0,
    "warnings": ["list of warning strings"]
  },
  "metadata": {
    "calculated_at": "ISO8601",
    "script_version": "v2.0",
    "checksum_md5": "AABB...",
    "checksum_sha256": "EEFF..."
  }
}
```

### 3.3 Factor Meta Schema (`v88-factor-meta-v2.0`)

```json
{
  "schema": "v88-factor-meta-v2.0",
  "checksum_file": "factor_meta.json.checksum",
  "factor_id": "string",
  "factor_name": "string",
  "variety": "PB | ZN | Recycle-PB",
  "category": "momentum | value | quality | growth | technical | other",
  "definition": {
    "lookback_days": 0,
    "forward_return_horizon_days": 0,
    "universe_filter": "string",
    "neutralization": "none | industry | market_cap | both",
    "winsorization_method": "none | percentile | MAD"
  },
  "source": {
    "data_provider": "WIND_DATA_LINK",
    "api_endpoint": "gateway_only",
    "pull_method": "trigger_pipeline"
  },
  "lifecycle": {
    "status": "DRAFT | READY | ACTIVE | DEPRECATED",
    "warmup_status": "AWAIT_DATA_TRIGGER | CONFIGURED | COMPUTED",
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  },
  "quality": {
    "warmup_ic_mean": null,
    "warmup_ir_mean": null,
    "warmup_t_statistic": null,
    "warmup_significant": null
  },
  "metadata": {
    "script_version": "v2.0",
    "checksum_md5": "AABB...",
    "checksum_sha256": "EEFF..."
  }
}
```

---

## 4. Exception Truncation Protection

### 4.1 Rationale

Factor data from external sources may contain:
- Extreme outliers (fat tails, market events)
- Data type mismatches (string where number expected)
- Missing values (NaN, None, empty)
- Incorrect ranges (negative prices, >100% returns)

### 4.2 Protection Layers

#### Layer 1: Input Validation (pre-calculation)

```python
def validate_input_records(records, max_size_bytes=50*1024*1024):
    """
    Validate input data before any computation.
    Returns: (valid, errors[])
    """
    errors = []
    if len(records) == 0:
        return False, ['EMPTY_DATASET']
    if len(records) > 10_000_000:
        return False, ['DATASET_TOO_LARGE']
    # Check for null/NaN in critical fields
    for r in records:
        if r.get('price') is None or r.get('factor_value') is None:
            errors.append(f"MISSING_VALUE: date={r.get('date')}")
            if len(errors) >= 100:
                return False, errors + ['TRUNCATED_ERRORS']
    if len(errors) > 0.05 * len(records):
        return False, [f'HIGH_ERROR_RATE: {len(errors)}/{len(records)}']
    return True, errors
```

#### Layer 2: Winsorization (outlier clipping)

```python
def winsorize(data, method='percentile', pct=0.01):
    """
    Clip extreme values to prevent outlier pollution.
    method: 'percentile' (1%+99%), 'MAD' (median ± 3*1.4826*MAD)
    """
    import statistics
    n = len(data)
    if method == 'percentile':
        lo = sorted(data)[int(n * pct)]
        hi = sorted(data)[int(n * (1 - pct))]
        return [max(lo, min(hi, v)) for v in data], lo, hi
    elif method == 'MAD':
        med = statistics.median(data)
        mad = statistics.median(abs(v - med) for v in data) * 1.4826
        lo, hi = med - 3 * mad, med + 3 * mad
        return [max(lo, min(hi, v)) for v in data], lo, hi
```

#### Layer 3: Output Truncation Guard

```python
MAX_OUTPUT_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB hard limit
MAX_IC_SERIES_LENGTH = 100_000              # 100k data points

def safe_write_output(result, filepath):
    """
    Write output with size guard. If data exceeds limits,
    truncate to latest MAX_IC_SERIES_LENGTH points and mark.
    """
    import json, os
    
    # Check size before write
    content = json.dumps(result, ensure_ascii=False)
    if len(content.encode('utf-8')) > MAX_OUTPUT_SIZE_BYTES:
        # Truncate IC series to latest entries
        if 'ic_series' in result and isinstance(result['ic_series'], list):
            truncated = result['ic_series'][-MAX_IC_SERIES_LENGTH:]
            result['ic_series'] = truncated
            result['quality']['truncation_events'] = (
                result['quality'].get('truncation_events', 0) + 1
            )
            result['quality']['warnings'].append(
                f'TRUNCATED: ic_series clipped to {MAX_IC_SERIES_LENGTH} entries'
            )
            content = json.dumps(result, ensure_ascii=False)
    
    # Final size check
    if len(content.encode('utf-8')) > MAX_OUTPUT_SIZE_BYTES:
        raise ValueError(
            f'OUTPUT_TOO_LARGE: {len(content)} bytes > {MAX_OUTPUT_SIZE_BYTES} limit'
        )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
```

#### Layer 4: Atomic Write (no partial writes)

```python
def atomic_write(filepath, content):
    """
    Write to temp file, then rename. Prevents partial writes
    from corrupting the output directory.
    """
    import tempfile, os
    dir_name = os.path.dirname(filepath)
    with tempfile.NamedTemporaryFile(
        mode='w', dir=dir_name, delete=False, suffix='.tmp',
        encoding='utf-8'
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    os.replace(tmp_path, filepath)
```

### 4.3 Protection Summary

| Layer | Protection | Action on Failure |
|:-----:|-----------|:------------------|
| L1 | Input validation | Abort calculation, log errors |
| L2 | Winsorization | Clip outliers, log clipping stats |
| L3 | Output size guard | Truncate series, flag in quality |
| L4 | Atomic write | Prevent partial/corrupt files |

---

## 5. Mandatory Compliance Checklist

Before any result file is committed or consumed:

| # | Check | Requirement | Pass/Fail |
|:-:|-------|:-----------|:---------:|
| 1 | Schema version | Must match `v2.0` | ⬜ |
| 2 | Dual-checksum | `.checksum` sidecar exists | ⬜ |
| 3 | MD5 match | Recorded MD5 = fresh MD5 | ⬜ |
| 4 | SHA256 match | Recorded SHA256 = fresh SHA256 | ⬜ |
| 5 | File size limit | < 100 MB | ⬜ |
| 6 | Data completeness | ≥ 95% valid records | ⬜ |
| 7 | Error count | < 5% of records | ⬜ |
| 8 | Truncation log | All truncation events recorded | ⬜ |
| 9 | Atomic write | File written via temp+rename | ⬜ |
| 10 | No auto-push | No git commands in output path | ⬜ |
| 11 | No external API | No WindPy/network calls | ⬜ |
| 12 | Timestamp | ISO8601 with timezone | ⬜ |

---

## 6. Integration Points

### 6.1 ic_ir_calc_skeleton.py Integration

The following updates are required in the skeleton (v2.0):

```python
# Import additions (no WindPy!)
import hashlib  # ALREADY IMPORTED in v1.0

# Add dual-checksum generation after each file write
def write_result_with_checksum(result, filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    content = json.dumps(result, indent=2, ensure_ascii=False)
    atomic_write(filepath, content)
    md5, sha256 = dual_checksum(filepath)
    # Update result with checksums
    result['metadata']['checksum_md5'] = md5
    result['metadata']['checksum_sha256'] = sha256
    # Write checksum sidecar
    checksum_data = {
        'schema': 'v88-factor-checksum-v2.0',
        'filename': filename,
        'size_bytes': os.path.getsize(filepath),
        'md5': md5,
        'sha256': sha256,
        'algorithm_md5': 'MD5',
        'algorithm_sha256': 'SHA-256',
        'generated_at': datetime.now().isoformat(),
        'generator': 'ic_ir_calc_skeleton.py v2.0',
    }
    atomic_write(filepath + '.checksum', json.dumps(checksum_data, indent=2))
```

### 6.2 Checksum Directory Layout

```
factor_workspace/pb_zn_recyclepb_v1/
├── output/
│   ├── ic_result.json              ← IC calculation result
│   ├── ic_result.json.checksum     ← Dual-checksum sidecar
│   ├── ir_result.json              ← IR calculation result
│   ├── ir_result.json.checksum     ← Dual-checksum sidecar
│   └── factor_meta.json            ← Factor metadata
│   └── factor_meta.json.checksum   ← Dual-checksum sidecar
├── checksum/
│   └── (legacy flat checksums — may be used for batch verification)
```

---

## 7. Version History

| Version | Date | Changes |
|:-------:|------|---------|
| v1.0 | 2026-10-22 (P4) | Initial skeleton: MD5-only, single-checksum, no truncation |
| v2.0 | 2026-10-22 (P016) | **Full upgrade**: MD5+SHA256 dual, 4-layer truncation, atomic write, enhanced schemas |

---

## 8. Conclusion

**Output standard v2.0 is now active.** All future factor calculation results MUST comply with:
- Dual-checksum (MD5 + SHA256) per file
- 4-layer exception protection
- Schema versioning (`v88-factor-*-v2.0`)
- Atomic file writes
- Quality reporting in every result

The v1.0 single-MD5 approach is **superseded** and should not be used for new outputs.

---

*Generated by DSHB Agent | V88 Phase03 P6 P0-16 Factor Compute Standby*
*T1 COMPLETE | Standard v2.0 defined | Dual-checksum mandatory | 4-layer truncation protection | Atomic writes*