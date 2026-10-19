# FACTOR_EXTRACT_V1

**Version:** 1.0.0 (LOCKED)  
**Skill ID:** `FACTOR_EXTRACT_V1`  
**Created:** 2026-10-19  
**Locked by:** DSHC-SKILL-FACTOR01  
**Baseline:** `feature/v88-g1 HEAD=19e80cb`

---

## Purpose

Extracts **7 quantitative market factors** from long-form commodity futures data, providing a clean wide-form dataset for backtesting, correlation analysis, and signal generation.

This skill processes a standardized long-form CSV into a wide-form factor dataset, performing data quality checks and computing rolling-window indicators along the way.

---

## Factor Definitions

| # | Factor ID | Name | Formula | Indicators Used |
|---|-----------|------|---------|-----------------|
| 1 | `spread_cs` | Cross-sectional Spread | `CLOSE - SETTLE` | CLOSE, SETTLE |
| 2 | `oi_level` | Open Interest Level | `OI` | OI |
| 3 | `oi_change_1d` | 1-Day OI Change | `OI(t) - OI(t-1)` | OI |
| 4 | `oi_change_rate_7d` | 7-Day OI Change Rate % | `(OI(t) - OI(t-7)) / OI(t-7) * 100` | OI |
| 5 | `spread_pct` | Spread Percentage % | `(CLOSE - SETTLE) / SETTLE * 100` | CLOSE, SETTLE |
| 6 | `contract_switch_flag` | Contract Switch Flag | `abs(CLOSE(t)-CLOSE(t-1))/CLOSE(t-1) > 0.02` | CLOSE |
| 7 | `momentum_20d` | 20-Day Momentum % | `(CLOSE(t) - CLOSE(t-20)) / CLOSE(t-20) * 100` | CLOSE |

---

## Input Format

### Long-Form CSV

**File:** A single CSV file with the following columns:

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `date` | String (YYYY-MM-DD) | Trading date | Yes |
| `symbol` | String | Futures contract symbol | Yes |
| `indicator` | String | Indicator name | Yes |
| `value` | Numeric | Indicator value | Yes |
| `source` | String | Data source identifier | Yes |

**Example row:**
```
2025-06-01,CU.SHF,CLOSE,78500,SHFE
2025-06-01,CU.SHF,SETTLE,78400,SHFE
2025-06-01,CU.SHF,OI,152300,SHFE
2025-06-01,CU.SHF,VOL,35000,SHFE
```

### Symbol Blacklist

The following symbols are **automatically excluded** (cannot be overridden):

- `LC.GFE`
- `LC.SHF`

### Date Alignment

If a symbol has missing dates compared to the majority of other symbols, these are reported in the data quality diagnostics (date misalignment). The script does **not** impute or fill missing dates.

---

## Output Format

### Wide-Form CSV

**File:** `factors_output.csv`

| Column | Type | Description |
|--------|------|-------------|
| `date` | String (YYYY-MM-DD) | Trading date |
| `symbol` | String | Futures contract symbol |
| `CLOSE` | Float | Closing price |
| `SETTLE` | Float | Settlement price |
| `OI` | Float | Open interest |
| `VOL` | Float | Volume (if available) |
| `spread_cs` | Float | Cross-sectional spread (CLOSE - SETTLE) |
| `oi_level` | Float | Open interest level |
| `oi_change_1d` | Float | 1-day OI change (NaN for first row) |
| `oi_change_rate_7d` | Float | 7-day OI change rate % (NaN for first 7 rows) |
| `spread_pct` | Float | Spread as % of SETTLE (NaN if SETTLE=0) |
| `contract_switch_flag` | Integer (0/1) | Contract switch indicator |
| `momentum_20d` | Float | 20-day momentum % (NaN for first 20 rows) |

### Metadata JSON

**File:** `factors_metadata.json`

Contains full run metadata including:
- Skill version and configuration
- Symbols used and blacklisted
- Date range applied
- Data quality diagnostics (duplicates, nulls, misalignment)
- Output column definitions
- Row counts per symbol

---

## Usage Instructions

### Installation

Requires Python 3.8+ with the following packages:

```bash
pip install pandas numpy
```

### Command Line

```bash
python artifacts/skill_lib/factor_v1/factor_extract_v1.py \
    --csv PATH \
    [--symbols SYMBOL1,SYMBOL2,...] \
    [--start YYYY-MM-DD] \
    [--end YYYY-MM-DD] \
    [--outdir PATH] \
    [--verbose]
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--csv` | **Yes** | — | Path to input long-form CSV |
| `--symbols` | No | All (minus blacklist) | Comma-separated symbol whitelist |
| `--start` | No | — | Start date filter (inclusive, YYYY-MM-DD) |
| `--end` | No | — | End date filter (inclusive, YYYY-MM-DD) |
| `--outdir` | No | `artifacts/skill_lib/factor_v1/output/` | Output directory |
| `--verbose` | No | — | Enable debug-level logging |

### Examples

**Example 1: Extract all symbols with date filter**
```bash
python artifacts/skill_lib/factor_v1/factor_extract_v1.py \
    --csv output_sample/wdf_sample_metals_aligned.csv \
    --start 2025-01-02 \
    --end 2026-08-26 \
    --outdir artifacts/skill_lib/factor_v1/output/
```

**Example 2: Extract specific symbols (DSHA one-click)**
```bash
python artifacts/skill_lib/factor_v1/factor_extract_v1.py \
    --csv output_sample/wdf_sample_metals_aligned.csv \
    --symbols CU.SHF,ZN.SHF,PB.SHF,AL.SHF,SN.SHF,NI.SHF \
    --start 2025-01-02 \
    --end 2026-08-26 \
    --outdir artifacts/skill_lib/factor_v1/output/
```

**Example 3: Full data, verbose mode**
```bash
python artifacts/skill_lib/factor_v1/factor_extract_v1.py \
    --csv output_sample/wdf_sample_metals_aligned.csv \
    --outdir artifacts/skill_lib/factor_v1/output/ \
    --verbose
```

### Python API

```python
from factor_extract_v1 import extract_factors

factor_df, report, paths = extract_factors(
    csv_path="output_sample/wdf_sample_metals_aligned.csv",
    symbols=["CU.SHF", "ZN.SHF", "PB.SHF"],
    start="2025-01-02",
    end="2026-08-26",
    outdir="artifacts/skill_lib/factor_v1/output/",
)
```

---

## Data Requirements

| Requirement | Value |
|-------------|-------|
| Required indicators | CLOSE, OI, SETTLE |
| Optional indicators | VOL |
| Minimum trading days | 20 (for momentum_20d) |
| Date range reference | 2025-01-02 to 2026-10-19 |
| Primary key | (date, symbol, indicator) — duplicates kept: first |

### Data Quality Checks

The script automatically reports:

1. **Primary key duplicates** — duplicate (date, symbol, indicator) triples (keeps first occurrence)
2. **Null values** — rows with missing values in required columns
3. **Date misalignment** — dates present for one symbol but missing for others (compares against majority calendar)
4. **Symbol blacklist** — LC.GFE and LC.SHF are always excluded

These diagnostics are written to `factors_metadata.json` under the `data_quality` key.

---

## Version Lock Policy

**V1 is FROZEN.** This skill is version-locked and must not be modified in-place.

- **V1.0.0** (current): `factor_extract_v1.py` @ `593d688` — locked, no changes permitted
- **V2** (next): Must be created in `artifacts/skill_lib/factor_v2/` with a new version number
- Direct overwrite of V1 files is **prohibited**

### Iteration Policy

If changes are needed (new factors, bug fixes, feature additions):

1. Create `artifacts/skill_lib/factor_v2/` directory
2. Copy all V1 files as starting point
3. Increment version to `2.0.0`
4. Update `VERSION`, `SKILL_ID`, and all metadata accordingly
5. Document changes in V2's `README.md` changelog
6. Generate a new `manifest.json` with updated lock info

---

## File Structure

```
artifacts/skill_lib/factor_v1/
├── factor_extract_v1.py     # Main skill script (Python)
├── factor_definitions.json  # Factor metadata and definitions
├── README.md                # This documentation
└── manifest.json            # Version lock manifest
```

---

## Constraints

| Constraint | Value |
|------------|-------|
| Wind API calls | 0 (offline only) |
| F01 script locked | true |
| F01 script version | v1.0 @ 593d688 |
| F01 script params only | true |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| V1.0.0 | 2026-10-19 | Initial release. 7 factors, data quality diagnostics, CLI + Python API. |

---

## License

Internal use — DSH project. No redistribution outside team.
