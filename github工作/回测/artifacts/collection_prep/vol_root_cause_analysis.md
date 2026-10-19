# VOL Data Gap Root Cause Analysis

> **Workorder:** DSHC-VOL-PREP
> **Baseline:** feature/v88-g1 HEAD=48b248b
> **Token:** DSHC-VOL-PREP-TOKEN
> **Date:** 2026-10-19
> **wind_api_calls:** 0
> **Status:** PREPARED — No execution

---

## 1. Problem Statement

The aligned CSV `output_sample/wdf_sample_metals_aligned.csv` shows a **critical VOL data gap**:

| Indicator | Date Range | Trading Days |
|-----------|-----------|-------------|
| CLOSE     | 2025-01-02 → 2026-08-26 | 400 |
| OI        | 2025-01-02 → 2026-08-26 | 400 |
| SETTLE    | 2025-01-02 → 2026-08-26 | 400 |
| **VOL**   | **2026-09-03 → 2026-10-19** | **27** |

**Zero date overlap** between VOL and the other three indicators.

VOL data is only available for the last 27 trading days — far from the 400-day history available for CLOSE/OI/SETTLE.

---

## 2. Evidence Summary

### 2.1 F01 Script Configuration

```powershell
# scripts/dshc_f01_gui_fetch.ps1
$symbols    = @("ZN.SHF","CU.SHF","PB.SHF","AL.SHF","SN.SHF","NI.SHF","LC.SHF")
$indicators = @("CLOSE","VOL","OI","SETTLE")
$copyRows   = 600

# Per-combination WSD formula:
$formula = '=WSD("'+$sym+'","'+$ind+'","2025-01-02","2026-10-19","Fill=Previous")'
```

Each indicator is queried **individually** (28 total WSD calls: 7 symbols × 4 indicators).

### 2.2 VOL Row Distribution (from aligned CSV)

| Symbol | VOL Rows | Date Range |
|--------|---------|-----------|
| AL.SHF | 27 | 2026-09-03 → 2026-10-19 |
| CU.SHF | 27 | 2026-09-03 → 2026-10-19 |
| NI.SHF | 27 | 2026-09-03 → 2026-10-19 |
| PB.SHF | 27 | 2026-09-03 → 2026-10-19 |
| SN.SHF | 27 | 2026-09-03 → 2026-10-19 |
| ZN.SHF | 27 | 2026-09-03 → 2026-10-19 |
| LC.SHF | 0 | WIND_EMPTY_SYMBOL (GFE exchange) |

**Uniform gap across all 6 SHFE metals** — suggests a systemic WSD/Wind issue, not a per-symbol problem.

### 2.3 CLOSE/OI/SETTLE vs VOL — Disparity

The fact that CLOSE, OI, and SETTLE all share 400 dates while VOL has only 27 indicates:
- The WSD formula call works identically for all 4 indicators
- The **Wind database itself** has VOL data only from 2026-09-03 onwards for these contract types
- `Fill=Previous` does not help because there is no "previous" value to fill from

---

## 3. Root Cause Candidates (Investigation Checklist)

### Candidate 1: WIND Data Availability (MOST LIKELY) ⭐

**Hypothesis:** Wind's `vol` WSD field for futures contracts only stores recent daily volume data (last ~1 month). Historical volume may not be available through WSD.

**Evidence:**
- Uniform 27-day gap across all 6 metals
- Other indicators (CLOSE/OI/SETTLE) have full history
- This is a Wind database limitation, not a query error

**Verification:**
- [ ] Try `WSD("CU.SHF", "vol", "2024-01-01", "2024-01-10")` — if empty, confirms limited history
- [ ] Check if Wind stores daily volume as `volume` (not `vol`)
- [ ] Check Wind help docs for WSD field availability

**Mitigation:** If confirmed, VOL cannot be backfilled via WSD. Alternative sources needed.

---

### Candidate 2: WSD Field Name Mismatch

**Hypothesis:** `VOL` is not the correct WSD field name for daily trading volume. The correct field might be `volume`, `turnover`, or `vol_amount`.

**Evidence:**
- Wind WSD field names are case-insensitive but the exact name matters
- `VOL` may be an alias that only returns recent data

**Verification:**
- [ ] Try `WSD("CU.SHF", "volume", "2025-01-02", "2026-10-19")`
- [ ] Try `WSD("CU.SHF", "turnover", "2025-01-02", "2026-10-19")`
- [ ] Try `WSD("CU.SHF", "volume_amount", "2025-01-02", "2026-10-19")`
- [ ] Try `WSD("CU.SHF", "settle_vol", "2025-01-02", "2026-10-19")`

**Mitigation:** If a different field name works, update the template with the correct indicator name.

---

### Candidate 3: WSD vs WDP vs Other API Functions

**Hypothesis:** Daily historical volume requires a different Wind API function (e.g., `WDP` for panel data, or `WSD` with different parameters).

**Evidence:**
- WSD is the "Wind Standard Data" function for time series
- Volume may require a different function like `WSDH` (historical) or `WDP` (panel)
- `Fill=Previous` only fills from the returned series, not from another data source

**Verification:**
- [ ] Try `WDP("CU.SHF", "vol", "2025-01-02", "2026-10-19")`
- [ ] Check Wind function reference for alternatives to WSD for volume
- [ ] Check if `WSD("CU.SHF", "vol;turnover", "2025-01-02", "2026-10-19")` returns different results

**Mitigation:** If another API function works, create a separate template for VOL collection.

---

### Candidate 4: Excel Rendering / copyRows Limit

**Hypothesis:** The Excel WDF output may have rendered VOL data correctly, but the `copyRows=600` parameter or clipboard extraction truncated it.

**Evidence:**
- `copyRows=600` is sufficient for 400 trading days × 1 column
- However, if WSD returns 427 rows and 600 is enough, this is unlikely

**Counter-evidence:**
- CLOSE/OI/SETTLE all returned 400 dates, so the 600-row limit was not a constraint
- The gap is at the **Wind API level**, not the extraction level

**Verification:**
- [ ] Check raw Excel output for VOL — is the data there but not copied?
- [ ] Increase copyRows to 1000 and retry a single VOL query

---

### Candidate 5: Data Permissions / Account Tier

**Hypothesis:** The Wind account has different data permissions for VOL vs CLOSE/OI/SETTLE. Volume data may require a higher subscription tier.

**Evidence:**
- Wind tiering can restrict access to certain indicators
- CLOSE/OI/SETTLE are basic fields; VOL may be premium

**Verification:**
- [ ] Check Wind account subscription level
- [ ] Contact Wind support for VOL field availability
- [ ] Check if other WSD fields (e.g., `OPEN`, `HIGH`, `LOW`, `ATR`) also have gaps

---

### Candidate 6: Contract Type / Dominant Contract Issue

**Hypothesis:** Volume data is only tracked for the dominant contract, and the dominant contract may have changed during the period. If the WSD formula uses a continuous contract code, volume history may be broken.

**Evidence:**
- Futures contracts have different volume tracking per contract month
- Continuous/dominant contract codes may not have historical volume

**Verification:**
- [ ] Check which contract code `CU.SHF` maps to in Wind (main continuous vs specific month)
- [ ] Try specific contract month: `WSD("CU2506.SHF", "vol", "2025-01-02", "2026-10-19")`
- [ ] Compare continuous vs specific month volume availability

---

## 4. Priority Investigation Order

```
Priority 1 — Quick WSD field name check (5 min):
  1. WSD("CU.SHF", "volume", "2025-01-02", "2026-01-10")  → if returns data, field name issue
  2. WSD("CU.SHF", "turnover", "2025-01-02", "2026-01-10")
  3. WSD("CU.SHF", "vol", "2024-01-01", "2024-01-10")      → if empty, confirms limited history

Priority 2 — Alternative API functions (10 min):
  4. WDP("CU.SHF", "vol", "2025-01-02", "2026-10-19")
  5. Check Wind help docs for volume-specific functions

Priority 3 — Contract-level investigation (15 min):
  6. Specific contract month queries
  7. Compare continuous vs specific contract volume

Priority 4 — Account/tier check (manual):
  8. Contact Wind support
  9. Check subscription level
```

---

## 5. Impact Assessment

| Factor | Current State | Impact | Mitigation |
|--------|-------------|--------|-----------|
| FACTOR_EXTRACT_V1 | Uses CLOSE/OI/SETTLE only | **LOW** — VOL not used by V1 factors | No action needed for V1 |
| Volume-based factor (F08) | Planned, not implemented | **MEDIUM** — cannot build without full VOL history | Use alternative volume proxy or defer |
| ATR% factor (F10) | Needs HIGH/LOW/CLOSE | **LOW** — independent of VOL | Proceed with HIGH/LOW pre-check |
| RB/HC expansion | Needs VOL for volume analysis | **MEDIUM** — same gap expected for RB/HC | Template includes VOL with risk note |
| Backtest analysis | Volume confirmation of price moves | **LOW** — CLOSE-based factors sufficient | Defer volume analysis |

---

## 6. Summary

**Most likely root cause:** Wind's WSD `vol` field for futures only provides recent data (~30 days). Historical volume is not available through this API endpoint.

**Recommended action:**
1. Execute the verification checklist above (requires wind_api_calls > 0)
2. If confirmed as Wind limitation, document as known constraint
3. For VOL-dependent factors, use alternative approaches:
   - OI-based volume proxy (`oi_change_1d` already in V1)
   - Turnover if available
   - Third-party volume data sources
4. For future RB/HC collection, include VOL in the same template but flag the expected gap

---

*Generated by DSHC-VOL-PREP | 2026-10-19 | wind_api_calls=0*
*Status: PREPARED — No execution*
