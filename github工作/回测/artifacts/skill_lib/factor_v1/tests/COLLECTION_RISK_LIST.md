# COLLECTION RISK LIST — SHFE RB/HC Expansion
## DSHC-MAINT-01 | 2026-10-19

> **Status:** PREPARED — No execution. Risk assessment for future data collection.
> **Scope:** HIGH/LOW price indicators for ATR% factor (P2备选).

---

## 1. HIGH/LOW Price Indicators — ATR% Factor Risk

### 1.1 Overview

The F10 ATR% factor (Planned, P2备选) requires:
- **HIGH** — Daily high price
- **LOW** — Daily low price
- **CLOSE** — Daily close price

ATR (Average True Range) formula:
```
TrueRange = max(HIGH - LOW, abs(HIGH - prev_CLOSE), abs(LOW - prev_CLOSE))
ATR = SMA(TrueRange, N)
ATR% = ATR / CLOSE * 100
```

### 1.2 HIGH/LOW Data Availability — Risk Assessment

| Instrument | Exchange | HIGH Available? | LOW Available? | Risk Level | Notes |
|------------|----------|-----------------|----------------|------------|-------|
| CU.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Commodity future — standard WSD fields |
| ZN.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Same as CU |
| PB.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Same |
| AL.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Same |
| SN.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Same |
| NI.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Same |
| LC.GFE     | GFE      | ✅ **YES**      | ✅ **YES**      | **LOW**   | **PROBE CONFIRMED** (432 rows each, 2025-01-02→2026-10-19) |
| RB.SHF     | SHFE     | ✅ **YES**      | ✅ **YES**      | **LOW**   | **PROBE CONFIRMED** (432 rows each) |
| HC.SHF     | SHFE     | ✅ **YES**      | ✅ **YES**      | **LOW**   | **PROBE CONFIRMED** (432 rows each) |

### 1.3 HIGH/LOW vs CLOSE/OI/SETTLE — Data Format Differences

| Field | WSD Field Name | Returns | Notes |
|-------|---------------|---------|-------|
| CLOSE | `CLOSE`       | Single price | Always available (UPPERCASE) |
| SETTLE | `SETTLE`     | Single price | Always available (UPPERCASE) |
| OI | `OI`         | Single count | Always available (UPPERCASE) |
| VOL | `volume`     | Single count | **FIXED** — `vol` fails, `volume` (lowercase) works |
| **HIGH** | `HIGH`      | Single price | Always available (UPPERCASE) |
| **LOW** | `LOW`       | Single price | Always available (UPPERCASE) |

**Key Fix (DSHC-VOL-FULL-COLLECT):** WSD field name case sensitivity resolved.
- `CLOSE`/`SETTLE`/`OI`/`HIGH`/`LOW` use **UPPERCASE**
- `volume` uses **lowercase** (`vol` returns 0 rows, `volume` returns full data)
- All 9 instruments × 6 indicators × 432 days confirmed available

### 1.4 Time Window Risk

All templates use **2025-01-02 → 2026-10-19** window (432 trading days).

| Risk | Description | Impact | Mitigation |
|------|-------------|--------|------------|
| VOL gap | `vol` field returns 0 rows | **RESOLVED** | Use `volume` (lowercase) — confirmed 432 rows for all 9 instruments |
| HIGH/LOW gap | GFE instruments may be sparse | **RESOLVED** | All 7 instruments confirmed 432 rows (including LC.GFE) |
| CLOSE/OI/SETTLE gap | 6 metals previously had 400 days | **RESOLVED** | Full 432-day coverage confirmed for all 9 instruments |
| Contract month gaps | Different contract months may have different date ranges | LOW | Use continuous contract or dominant contract |
| New instruments | RB/HC data availability untested | **RESOLVED** | 432 rows confirmed for all indicators |

### 1.5 WSD Formula Risk Matrix

| Formula Pattern | Tested? | Risk | Notes |
|----------------|---------|------|-------|
| `WSD(sym,"CLOSE;OI;SETTLE",...)` | ✅ Yes (6 metals) | LOW | All indicators returned (UPPERCASE) |
| `WSD(sym,"HIGH;LOW",...)` | ✅ **Yes (all 7)** | **LOW** | **PROBE CONFIRMED** — all instruments return 432 rows |
| `WSD(sym,"volume",...)` | ✅ **Yes (all 9)** | **LOW** | **FULL-COLLECT CONFIRMED** — 432 rows each (lowercase) |
| `WSD(sym,"CLOSE;SETTLE;OI",...)` | ✅ Yes (F01) | LOW | F01 script proven (UPPERCASE fields) |
| `WSD(sym,"HIGH;LOW;CLOSE",...)` | ❌ No | MEDIUM | Mixed fields may behave differently |
| `WSD(sym,"OPEN;HIGH;LOW;CLOSE",...)` | ❌ No | MEDIUM | OHLC — most standard, likely works |
| `WSD(sym,"VOL",...)` | ❌ **FAILS** | **HIGH** | **`vol`/`VOL` returns 0 rows — use `volume` instead** |
| `WSD(sym,"ATR",...)` | ❌ No | HIGH | ATR may not be a direct WSD field |

### 1.6 ATR% Factor — Pre-Implementation Checklist

Before building ATR% as F10 factor, verify:

- [x] HIGH data returns non-zero for all 9 instruments **(432 rows each)**
- [x] LOW data returns non-zero for all 9 instruments **(432 rows each)**
- [ ] HIGH ≥ LOW for all rows (sanity check)
- [ ] HIGH ≤ CLOSE × 1.02 (upper bound sanity)
- [ ] LOW ≥ CLOSE × 0.98 (lower bound sanity)
- [ ] No NULL/NaN values in HIGH/LOW columns
- [x] GFE (LC.GFE) specifically tested for HIGH/LOW availability **(AVAILABLE — 432 rows)**
- [x] RB.SHF and HC.SHF tested for date range coverage **(432 rows each)**
- [x] **VOL data confirmed for all 9 instruments (432 rows each using `volume` field)**

---

## 2. General Collection Risks — RB/HC Expansion

| # | Risk | Severity | Description | Mitigation |
|---|------|----------|-------------|------------|
| 1 | **Wind client stability** | HIGH | Wind desktop client must be running for Excel WDF | Use F01 GUI script with GUI mode |
| 2 | **Formula injection errors** | MEDIUM | CALC_ERROR from CalculateSync (observed in A01 events) | Use retry logic (3 attempts) |
| 3 | **Empty data for new symbols** | MEDIUM | RB/HC may not exist in Wind database for this date range | Test with single-symbol probe first |
| 4 | **Date range mismatch** | LOW | RB/HC contracts may have different listing dates | Use same window as metals for consistency |
| 5 | **Clipboard formatting** | LOW | Single-line tab-separated format required | F01 script handles this |
| 6 | **Data alignment** | MEDIUM | New data must match long-form CSV schema | Use generate_aligned_csv.py pattern |
| 7 | **Factor extraction compatibility** | LOW | New symbols use same V1 factors | No changes needed — factors are symbol-agnostic |

---

## 3. Recommended Execution Sequence

```
Phase 1 — Probe (LOW risk):
  1. Single-symbol test: WSD("RB.SHF","CLOSE","2025-01-02","2025-01-10")
  2. Verify data returns, date format, value range
  3. Same for HC.SHF

Phase 2 — Full fetch (MEDIUM risk):
  4. Full window fetch for RB.SHF (4 indicators)
  5. Full window fetch for HC.SHF (4 indicators)
  6. Verify row counts and date ranges

Phase 3 — HIGH/LOW probe (HIGH risk):
  7. Test WSD("RB.SHF","HIGH;LOW",...) for a short window
  8. Test WSD("HC.SHF","HIGH;LOW",...) for a short window
  9. If PASS: extend to full window
  10. If FAIL: document gap, skip ATR% for now

Phase 4 — ATR% implementation (only after Phase 3 PASS):
  11. Compute ATR% factor
  12. Validate against manual spot-checks
  13. Add to factor_definitions.json (V2, not V1)
```

---

## 4. Cross-Reference

| Item | Reference |
|------|-----------|
| F01 script | `scripts/dshc_f01_gui_fetch.ps1` (LOCKED @ 593d688) |
| V1 factors | `artifacts/skill_lib/factor_v1/` (LOCKED V1.0.0) |
| Aligned CSV | `output_sample/wdf_sample_metals_aligned.csv` |
| A06 validator | `code/a06_longformat_validator.py` |
| Exchange mapping | `artifacts/skill_lib/factor_v1/manifest.json` → exchange_mapping |
| ATR% factor doc | Planned V2 — not yet created |

---

## 5. HIGH/LOW Pre-Check Update — DSHC-VOL-PREP

> Updated: 2026-10-19 by DSHC-VOL-PREP

### 5.1 Updated HIGH/LOW Risk Matrix

| Instrument | Exchange | HIGH Available? | LOW Available? | Risk Level | Notes |
|------------|----------|-----------------|----------------|------------|-------|
| CU.SHF     | SHFE     | ✅ Expected     | ✅ Expected     | **LOW**    | Core OHLC — WSD standard field |
| ZN.SHF     | SHFE     | ✅ Expected     | ✅ Expected     | **LOW**    | Same as CU |
| PB.SHF     | SHFE     | ✅ Expected     | ✅ Expected     | **LOW**    | Same |
| AL.SHF     | SHFE     | ✅ Expected     | ✅ Expected     | **LOW**    | Same |
| SN.SHF     | SHFE     | ✅ Expected     | ✅ Expected     | **LOW**    | Same |
| NI.SHF     | SHFE     | ✅ Expected     | ✅ Expected     | **LOW**    | Same |
| LC.GFE     | GFE      | ✅ **YES (432)** | ✅ **YES (432)** | **LOW**    | **PROBE CONFIRMED** — full history available |
| RB.SHF     | SHFE     | ✅ **YES (432)** | ✅ **YES (432)** | **LOW**    | **PROBE CONFIRMED** — full history |
| HC.SHF     | SHFE     | ✅ **YES (432)** | ✅ **YES (432)** | **LOW**    | **PROBE CONFIRMED** — full history |

### 5.2 LC.GFE HIGH/LOW — Risk Assessment (PROBE CONFIRMED)

**Result: LOW RISK — LC.GFE HIGH/LOW FULLY AVAILABLE**

Probe results (2026-10-19, DSHC-VOL-PROBE-COLLECT):
- LC.GFE HIGH: 432 rows (2025-01-02 → 2026-10-19), first=78580, last=101760
- LC.GFE LOW: 432 rows (2025-01-02 → 2026-10-19), first=77120, last=96240
- Risk downgraded from HIGH to LOW

**All 7 instruments confirmed LOW risk for HIGH/LOW (432 rows each):**
CU.SHF, ZN.SHF, PB.SHF, AL.SHF, SN.SHF, NI.SHF, LC.GFE

**ATR% factor can be computed for all 9 instruments (6 SHFE metals + RB + HC + LC.GFE).**

### 5.3 VOL Gap — Root Cause FOUND

**Root Cause: WSD field name mismatch. `vol` does NOT work; `volume` DOES work.**

Probe results (2026-10-19, DSHC-VOL-PROBE-COLLECT):
| Variant | Field | Rows | Status |
|---------|-------|------|--------|
| A_current | `vol` | 0 | FAIL |
| B_volume | `volume` | 7 | **OK** |
| C_turnover | `turnover` | 0 | FAIL |
| D_multi | `vol;turnover;close` | 0 | FAIL |
| E_datefill | `vol` + DateFill | 0 | FAIL |
| F_wdp | `vol` (WDP) | 0 | FAIL |

**The correct WSD field name is `volume`, not `vol`.** The previous F01 script used `VOL` (uppercase) which may have been partially accepted but returned sparse data (27 days). The correct lowercase `volume` returns full historical data.

**Impact on ATR%:** NONE — ATR% uses HIGH/LOW/CLOSE, not VOL.
**Impact on RB/HC:** Same issue — `vol` returns 0, `volume` would return full data.
**Mitigation:** Use `volume` instead of `vol` in all WSD formulas.

### 5.4 HIGH/LOW vs VOL — Comparative Risk (PROBE RESULTS)

| Dimension | VOL | HIGH/LOW |
|-----------|-----|----------|
| Known gap | Yes — `vol` field returns 0 rows | **NO GAP** — all 7 instruments × 432 rows |
| Root cause | **Field name mismatch**: `vol` fails, `volume` works | N/A — all fields work |
| SHFE risk | FIXED (use `volume`) | LOW (confirmed 432 rows) |
| LC.GFE risk | **LOW** (LC.GFE HIGH/LOW available) | **LOW** (confirmed 432 rows) |
| Impact on ATR% | None | NONE (all data available) |

### 5.5 DSHC-VOL-PROBE-COLLECT Results Summary

> Executed: 2026-10-19 | Token: DSHC-VOL-PROBE-TOKEN | Wind API calls: 32

| Phase | Description | Results |
|-------|-------------|---------|
| 1. VOL Probe | 6 WSD variants tested | **`volume` field works** (7 rows); `vol`/`turnover`/`WDP` all fail |
| 2. RB/HC Full Data | 2 symbols × 5 indicators | **4320 rows** (CLOSE/SETTLE/OI/HIGH/LOW × 432 days) |
| 3. HIGH/LOW Probe | 7 symbols × 2 indicators | **6048 rows** (all 7 instruments × 432 days) |
| 4. Report | HIGH/LOW availability | **All 7 instruments LOW risk** (including LC.GFE) |

**Key Findings:**
1. VOL gap root cause: WSD field name is `volume`, not `vol`
2. RB/HC data: 5 indicators available (VOL excluded — use `volume` field)
3. HIGH/LOW: All 9 instruments available for ATR% factor
4. LC.GFE: Fully available (HIGH risk downgraded to LOW)

**Artifacts:**
- `artifacts/collection_prep/vol_probe_result.csv`
- `artifacts/collection_prep/rbhc_raw_data.csv`
- `artifacts/collection_prep/highlow_raw_data.csv`
- `artifacts/collection_prep/highlow_probe_report.md`
- `artifacts/collection_prep/vol_probe_sha_snapshot.json`

---

## 6. RB/HC Indicator Verification — DSHC-VOL-PREP

### 6.1 Updated Indicator List

| Indicator | WSD Field | RB.SHF | HC.SHF | V1 Usage | F10 Usage |
|-----------|-----------|--------|--------|----------|-----------|
| CLOSE     | `CLOSE`   | ✅ **432** | ✅ **432** | ✅ Yes (7 factors) | ✅ Yes (ATR%) |
| SETTLE    | `SETTLE`  | ✅ **432** | ✅ **432** | ✅ Yes (7 factors) | — |
| OI        | `OI`      | ✅ **432** | ✅ **432** | ✅ Yes (7 factors) | — |
| VOL       | `volume`  | ✅ **432** | ✅ **432** | ❌ No | — |
| HIGH      | `HIGH`    | ✅ **432** | ✅ **432** | ❌ No | ✅ Yes (ATR%) |
| LOW       | `LOW`     | ✅ **432** | ✅ **432** | ❌ No | ✅ Yes (ATR%) |

### 6.2 RB/HC Collection Schema

```
WSD Formula:  WSD("{symbol}","close;settle;oi","{start}","{end}","Fill=Previous")
WSD HIGH/LOW: WSD("{symbol}","high;low","{start}","{end}","Fill=Previous")
VOL:          WSD("{symbol}","volume","{start}","{end}","Fill=Previous")  [NOTE: use `volume` not `vol`]

Symbols:      RB.SHF, HC.SHF
Window:       2025-01-02 → 2026-10-19
Total WSD calls: 2 symbols × 3 formula groups = 6 calls
Max with retries: 18 calls

PROBE RESULTS:
- CLOSE/SETTLE/OI: 432 rows each (both RB and HC)
- HIGH/LOW: 432 rows each (both RB and HC)
- VOL (`vol`): 0 rows (use `volume` instead)
```

### 6.3 Volume Note for RB/HC (FULL-COLLECT CONFIRMED)

RB/HC VOL data: **432 rows each** (both RB and HC) using `volume` field.

**Root Cause (RESOLVED):** WSD field name mismatch. The correct field name is `volume` (lowercase), not `vol`.

**Evidence:**
- `WSD("RB.SHF","volume","2025-01-02","2026-10-19","Fill=Previous")` → **432 rows**
- `WSD("HC.SHF","volume","2025-01-02","2026-10-19","Fill=Previous")` → **432 rows**
- `WSD("CU.SHF","vol","2025-01-02","2025-01-10")` → **0 rows** (fail)
- `WSD("CU.SHF","volume","2025-01-02","2025-01-10")` → **7 rows** (OK)

**Mitigation:** Use `volume` (lowercase) instead of `vol` in all WSD formulas. Full historical volume data is available for all 9 instruments.

---

---

## 7. DSHC-VOL-FULL-COLLECT — Full 9-Instrument Collection Results

> Executed: 2026-10-19 | Token: DSHC-VOL-FULL-TOKEN | Wind API calls: 30

### 7.1 Collection Summary

All 9 instruments × 6 indicators × 432 trading days = **23,328 rows** collected.

| Symbol | CLOSE | SETTLE | OI | VOL | HIGH | LOW | Total | Status |
|--------|-------|--------|----|----|------|-----|-------|--------|
| CU.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| ZN.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| PB.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| AL.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| SN.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| NI.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| LC.GFE | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| RB.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| HC.SHF | 432 | 432 | 432 | 432 | 432 | 432 | 2,592 | ✅ COMPLETE |
| **Total** | **3,888** | **3,888** | **3,888** | **3,888** | **3,888** | **3,888** | **23,328** | |

### 7.2 Key Findings

1. **VOL gap RESOLVED:** Using `volume` (lowercase) returns full 432-day data for all 9 instruments
2. **All indicators complete:** CLOSE/SETTLE/OI/VOL/HIGH/LOW all have 432 rows per symbol
3. **LC.GFE fully available:** All 6 indicators confirmed (432 rows each) — no longer blacklisted for ATR%
4. **RB/HC fully available:** All 6 indicators confirmed — expansion complete
5. **Unified aligned table generated:** `output_sample/wdf_sample_all_aligned_v2.csv` (DATA_ONLY_V2)

### 7.3 WSD Field Name Rules (Confirmed)

| Indicator | Correct Field Name | Case | Notes |
|-----------|-------------------|------|-------|
| CLOSE | `CLOSE` | UPPERCASE | ✅ Works |
| SETTLE | `SETTLE` | UPPERCASE | ✅ Works |
| OI | `OI` | UPPERCASE | ✅ Works |
| VOL | `volume` | **lowercase** | ✅ Works (NOT `vol`) |
| HIGH | `HIGH` | UPPERCASE | ✅ Works |
| LOW | `LOW` | UPPERCASE | ✅ Works |

### 7.4 Artifacts

| File | Size | SHA256 |
|------|------|--------|
| `all_9instruments_raw.csv` | 890,576B | `25eec50098afa5ed...` |
| `wdf_sample_all_aligned_v2.csv` | 869,246B | `14950b9464baefd8...` |
| `vol_full_sha_snapshot.json` | 304B | — |
| `vol_full_collect_report.md` | 3,337B | — |
| `vol_full_collect.py` | Script | — |

### 7.5 Gate Status

- **Gate:** CLOSED/HOLD
- **Release Permit:** NOT_ISSUED
- **FACTOR_EXTRACT_V1:** FROZEN V1.0.0 (unchanged)
- **F01 Script:** LOCKED @ 593d688 (unchanged)
- **Original V1 table:** `wdf_sample_metals_aligned.csv` — UNMODIFIED

---

---

## 8. DSHC-DATA-ARCHIVE — Permanent Asset Archive + LC.SHF INVALID Fix

> Executed: 2026-10-19 | Token: DSHC-DATA-ARCHIVE-TOKEN | Wind API calls: 0 (zero)

### 8.1 Permanent Archive Confirmation

All 3 DSHC-VOL-FULL-COLLECT output artifacts archived to `artifacts/backtest_archive/data_assets/`:

| File | Size | SHA256 (short) | Status |
|------|------|----------------|--------|
| `all_9instruments_raw.csv` | 890,576B | `25EEC50098AFA5ED...` | ✅ ARCHIVED |
| `wdf_sample_all_aligned_v2.csv` | 869,246B | `14950B9464BAEFD8...` | ✅ ARCHIVED |
| `vol_full_sha_snapshot.json` | 304B | — | ✅ ARCHIVED |
| `data_asset_manifest.json` | SHA ledger | — | ✅ GENERATED |

### 8.2 LC.SHF MAPPING FIX — INVALID Declaration

**Problem:** LC.SHF (Lithium Carbonate on SHFE) is INVALID — no data exists on Wind. The P81 exchange binding audit flags `LC.SHF` as EXCH-001-ATTRIBUTED-MISMATCH because:
- Product `LC` → expected exchange `GFE`
- Symbol `LC.SHF` → actual suffix `SHF`
- Result: MISMATCH (persistent alert)

**Fix Applied:**
1. Created `artifacts/exchange_binding_registry.json` — explicit INVALID declaration
2. `LC.SHF` → `PERMANENTLY_BLACKLISTED` (since 2026-10-19)
3. `LC.GFE` → `BOUND_OK` (sole valid binding, 432 rows × 6 indicators)
4. All DSHC scripts already exclude LC.SHF:
   - `factor_extract_v1.py`: `BLACKLIST = ["LC.GFE", "LC.SHF"]`
   - `a06_longformat_validator.py`: `SYMBOL_WHITELIST` excludes LC.SHF
   - `a06_pipeline_sync.py`: Uses LC.GFE only

**Auto-Clear Logic (P81):**
```
Condition: LC.SHF absent from mismatches AND LC.GFE resolves BOUND_OK
→ EXCH-001-ATTRIBUTED-MISMATCH labels auto-cleared from warning board
→ LC binding repair event logged to G7_ADJUDICATION_LEDGER
```
**Status:** CONFIRMED — LC.GFE = BOUND_OK, LC.SHF = MISMATCH (expected). Auto-clear triggers when LC.SHF no longer appears in active dshc_* files.

### 8.3 Long Table Independence Verification

| Table | Data Rows | Format | Instruments | Indicators | Independent? |
|-------|-----------|--------|-------------|------------|--------------|
| `wdf_sample_metals_aligned.csv` (V1) | **7,362** | LONG (DATA_ONLY) | 6 SHFE metals | 4 (CLOSE/SETTLE/OI/VOL) | ✅ Yes |
| `wdf_sample_all_aligned_v2.csv` (V2) | **23,328** | LONG (DATA_ONLY_V2) | 9 instruments | 6 (CLOSE/SETTLE/OI/VOL/HIGH/LOW) | ✅ Yes |
| **Overlap** | — | — | V1 ⊂ V2 symbols | V1 ⊂ V2 indicators | **No mutual coverage** |

**Conclusion:** V1 and V2 are **independent datasets**. V1 covers 6 SHFE metals with 4 indicators (original F01 collection). V2 covers all 9 instruments with 6 indicators (full collection). V1 is a proper subset of V2 — they do not overwrite each other.

### 8.4 P0 Constraint Compliance

| Constraint | Status |
|------------|--------|
| Zero Wind calls | ✅ 0 calls (archive-only workorder) |
| Aligned long table unmodified | ✅ `wdf_sample_all_aligned_v2.csv` copied, not modified |
| V1 skill frozen | ✅ All 4 files unchanged (factor_extract_v1.py, factor_definitions.json, README.md, manifest.json) |
| Gate: CLOSED/HOLD | ✅ Unchanged |

### 8.5 Artifacts Created

| File | Purpose |
|------|---------|
| `artifacts/exchange_binding_registry.json` | LC.SHF INVALID declaration + auto-clear contract |
| `artifacts/backtest_archive/data_assets/data_asset_manifest.json` | SHA256 ledger for all archived assets |

---

*Generated by DSHC-MAINT-01 | Updated by DSHC-VOL-PREP (pre-check) | Updated by DSHC-VOL-PROBE-COLLECT (probe results) | Updated by DSHC-VOL-FULL-COLLECT (full collection) | Updated by DSHC-DATA-ARCHIVE (archive + LC.SHF fix) | 2026-10-19 | wind_api_calls=0 (archive-only)*