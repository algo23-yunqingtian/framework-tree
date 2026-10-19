# HIGH/LOW Availability Pre-Check Report

> **Workorder:** DSHC-VOL-PREP
> **Baseline:** feature/v88-g1 HEAD=48b248b
> **Token:** DSHC-VOL-PREP-TOKEN
> **Date:** 2026-10-19
> **wind_api_calls:** 0
> **Status:** PREPARED — No execution

---

## 1. Purpose

The F10 ATR% factor (Planned, P2备选) requires:
- **HIGH** — Daily high price
- **LOW** — Daily low price
- **CLOSE** — Daily close price (already available)

ATR formula:
```
TrueRange = max(HIGH - LOW, abs(HIGH - prev_CLOSE), abs(LOW - prev_CLOSE))
ATR = SMA(TrueRange, N)
ATR% = ATR / CLOSE * 100
```

This report assesses HIGH/LOW data availability across all 7 tracked instruments + RB/HC candidates.

---

## 2. Instrument-Level HIGH/LOW Availability Assessment

### 2.1 SHFE Metals (6 Instruments) — LOW Risk ✅

| Instrument | Exchange | HIGH Available? | LOW Available? | Risk | Evidence |
|-----------|----------|-----------------|----------------|------|----------|
| CU.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Standard commodity future — WSD returns all OHLC fields |
| ZN.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Same as CU — SHFE provides complete OHLC |
| PB.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Same as CU |
| AL.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Same as CU |
| SN.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Same as CU |
| NI.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Same as CU |

**Rationale:** SHFE is a major exchange with mature Wind data integration. All OHLC (OPEN/HIGH/LOW/CLOSE) fields are standard WSD fields. The F01 script already successfully collects CLOSE for all 6 metals, and HIGH/LOW should behave identically.

**Confidence:** HIGH — HIGH/LOW are more fundamental than VOL. If VOL has a 27-day gap due to Wind data availability, HIGH/LOW will likely have full history because they are core price data.

---

### 2.2 RB/HC (Shanghai Rebar & Hot-rolled Coil) — LOW Risk ✅

| Instrument | Exchange | HIGH Available? | LOW Available? | Risk | Notes |
|-----------|----------|-----------------|----------------|------|-------|
| RB.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Same SHFE infrastructure as metals |
| HC.SHF    | SHFE     | ✅ Yes          | ✅ Yes         | LOW  | Same as RB |

**Rationale:** RB and HC are standard SHFE commodity futures. They should have the same OHLC data availability as the 6 metals already in the system.

**Note:** RB/HC data has not been collected yet. The first fetch will confirm availability. If any instrument has issues, the template includes a probe-first phase.

---

### 2.3 LC.GFE (Guangzhou Futures Exchange) — HIGH Risk ⚠️

| Instrument | Exchange | HIGH Available? | LOW Available? | Risk | Notes |
|-----------|----------|-----------------|----------------|------|-------|
| LC.GFE    | GFE      | ⚠️ Unknown     | ⚠️ Unknown     | **HIGH** | GFE may not expose HIGH/LOW via Wind WSD |

**Risk Factors:**
1. **GFE is newer than SHFE** — established in 2021. Wind's data integration for GFE may be incomplete.
2. **VOL data gap analogy** — LC.GFE VOL data is currently WIND_EMPTY_SYMBOL. HIGH/LOW may behave similarly.
3. **Different data infrastructure** — GFE may use different data formats or reporting standards.
4. **Wind coverage uncertainty** — Wind's WSD function may not support all fields for GFE instruments.

**Mitigation:**
- Must test HIGH/LOW specifically for LC.GFE before implementing ATR% factor
- If LC.GFE HIGH/LOW fails, ATR% can still be computed for 8 instruments (CU/ZN/PB/AL/SN/NI/RB/HC)
- LC.GFE ATR% can use CLOSE-only approximation as fallback (less accurate)

---

## 3. WSD Field Verification Matrix

| WSD Field | Tested by V1? | HIGH Available? | LOW Available? | Risk | Notes |
|-----------|--------------|-----------------|----------------|------|-------|
| `close`   | ✅ Yes (6 metals) | — | — | LOW  | Full 400-date history |
| `settle`  | ✅ Yes (6 metals) | — | — | LOW  | Full 400-date history |
| `oi`      | ✅ Yes (6 metals) | — | — | LOW  | Full 400-date history |
| `vol`     | ✅ Yes (6 metals) | — | — | **HIGH** | Only 27 dates (2026-09-03 → 2026-10-19) |
| **`high`** | ❌ No | **Unknown** | — | **HIGH** | Not yet tested — must verify before ATR% |
| **`low`** | ❌ No | — | **Unknown** | **HIGH** | Not yet tested — must verify before ATR% |
| `open`    | ❌ No | — | — | LOW  | Expected to work (same as HIGH/LOW) |
| `atr`     | ❌ No | — | — | HIGH  | May not be a direct WSD field — compute manually |

---

## 4. HIGH/LOW vs VOL — Comparative Risk Analysis

| Dimension | VOL | HIGH/LOW |
|-----------|-----|----------|
| Field type | Volume (count) | Price (numeric) |
| Data maturity | May be less mature in Wind | Core OHLC — mature |
| Known gap | Yes (27 days) | Not yet tested |
| Exchange risk | LC.GFE: WIND_EMPTY | LC.GFE: HIGH RISK |
| SHFE risk | 27-day gap (all 6 metals) | Expected full history |
| Alternative proxy | OI change (in V1) | Close approximation (less accurate) |
| Impact on V1 | None (V1 doesn't use VOL) | None (V1 doesn't use HIGH/LOW) |
| Impact on F10 | None | **CRITICAL** — HIGH/LOW required |

**Key insight:** VOL has a known data gap, but HIGH/LOW should be fine for SHFE instruments. The VOL gap may be a Wind data availability issue specific to the `vol` field, not a general WSD problem. HIGH/LOW are more fundamental price data and should have full availability.

---

## 5. LC.GFE HIGH/LOW — Risk Assessment Detail

### 5.1 What We Know About LC.GFE Data

| Field | LC.GFE Status | Evidence |
|-------|--------------|----------|
| CLOSE | ⚠️ WIND_EMPTY_SYMBOL | LC.SHF (wrong exchange) returns nothing; LC.GFE not yet tested |
| SETTLE | ⚠️ Unknown | Not tested |
| OI | ⚠️ Unknown | Not tested |
| VOL | ⚠️ Unknown | Not tested |
| HIGH | ❌ Not tested | — |
| LOW | ❌ Not tested | — |

### 5.2 GFE-specific Risks

1. **Data format:** GFE may use different data formats than SHFE (e.g., different date format, different field naming)
2. **Contract structure:** GFE lithium carbonate contracts may have different expiration cycles
3. **Wind coverage:** GFE is newer (2021) — Wind's coverage may be incomplete for advanced fields
4. **HIGH/LOW reporting:** Some exchanges do not report intraday HIGH/LOW for settlement purposes

### 5.3 Mitigation Plan for LC.GFE

```
Phase 1 — Probe (5 min):
  WSD("LC.GFE","high;low;close","2025-01-02","2025-01-10")
  → If returns data: LC.GFE HIGH/LOW available, proceed
  → If WIND_EMPTY or error: LC.GFE HIGH/LOW not available

Phase 2 — If Phase 1 FAIL:
  Option A: Skip LC.GFE for ATR% factor (compute for 8 instruments only)
  Option B: Use CLOSE-only ATR approximation (less accurate, flagged as degraded)
  Option C: Seek alternative data source for LC.GFE HIGH/LOW

Phase 3 — If Phase 1 PASS:
  Full window collection: WSD("LC.GFE","high;low;close","2025-01-02","2026-10-19")
```

---

## 6. ATR% Factor Pre-Implementation Checklist (Updated)

Before building ATR% as F10 factor, verify:

### 6.1 SHFE Metals (6 instruments)
- [ ] HIGH data returns non-zero for all 6 SHFE metals
- [ ] LOW data returns non-zero for all 6 SHFE metals
- [ ] HIGH ≥ LOW for all rows (sanity check)
- [ ] HIGH ≤ CLOSE × 1.05 (upper bound sanity — 5% tolerance)
- [ ] LOW ≥ CLOSE × 0.95 (lower bound sanity — 5% tolerance)
- [ ] No NULL/NaN values in HIGH/LOW columns
- [ ] Date range: 2025-01-02 → 2026-08-26 (400 dates, matching CLOSE)

### 6.2 RB/HC (2 instruments)
- [ ] HIGH data returns non-zero for RB.SHF and HC.SHF
- [ ] LOW data returns non-zero for RB.SHF and HC.SHF
- [ ] Same sanity checks as above
- [ ] Date range: 2025-01-02 → 2026-10-19 (full window)

### 6.3 LC.GFE (1 instrument)
- [ ] HIGH data probe: WSD("LC.GFE","high","2025-01-02","2025-01-10")
- [ ] LOW data probe: WSD("LC.GFE","low","2025-01-02","2025-01-10")
- [ ] If available: full window collection
- [ ] If unavailable: document gap, compute ATR% for 8 instruments only
- [ ] Decision: accept LC.GFE gap or seek alternative source

### 6.4 Factor Implementation
- [ ] Implement ATR calculation in Python (rolling TrueRange)
- [ ] Validate against manual spot-checks (2-3 instruments)
- [ ] Add to factor_definitions.json (V2, NOT V1)
- [ ] Update manifest.json with new factor
- [ ] Run regression test suite

---

## 7. Summary & Recommendations

| Item | Risk | Action Required | Priority |
|------|------|----------------|----------|
| SHFE metals HIGH/LOW | LOW | Verify with probe test | High |
| RB/HC HIGH/LOW | LOW | Verify with probe test | High |
| LC.GFE HIGH/LOW | HIGH | Probe test + fallback plan | High |
| VOL data gap | HIGH (known) | See vol_root_cause_analysis.md | Medium |
| ATR% factor | N/A (planned) | After HIGH/LOW verification | Low |

**Bottom line:** HIGH/LOW should be available for SHFE instruments (including RB/HC). The primary risk is LC.GFE. VOL has a confirmed gap but doesn't affect ATR%. Proceed with HIGH/LOW probe tests before building ATR%.

---

*Generated by DSHC-VOL-PREP | 2026-10-19 | wind_api_calls=0*
*Status: PREPARED — No execution*
