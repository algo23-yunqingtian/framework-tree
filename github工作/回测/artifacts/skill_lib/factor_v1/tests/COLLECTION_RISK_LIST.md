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
| LC.GFE     | GFE      | ⚠️ Unknown     | ⚠️ Unknown     | **HIGH**   | GFE may not expose HIGH/LOW via WSD |
| RB.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Commodity future — should work |
| HC.SHF     | SHFE     | ✅ Yes          | ✅ Yes         | **LOW**    | Same as RB |

### 1.3 HIGH/LOW vs CLOSE/OI/SETTLE — Data Format Differences

| Field | WSD Field Name | Returns | Notes |
|-------|---------------|---------|-------|
| CLOSE | `close`       | Single price | Always available |
| SETTLE | `settle`     | Single price | Always available |
| OI | `oi`         | Single count | Always available |
| VOL | `vol`        | Single count | May have gaps (observed: 27/427 dates for LC) |
| **HIGH** | `high`      | Single price | Standard, but GFE instruments may not report |
| **LOW** | `low`       | Single price | Same as HIGH |

**Key Risk:** GFE (Guangzhou Futures Exchange) may not provide HIGH/LOW data through
Wind's WSD interface. This was observed with VOL data for LC.SHF (27/427 dates).
For HIGH/LOW, the risk is **HIGH** for LC.GFE — may yield zero data.

### 1.4 Time Window Risk

All templates use **2025-01-02 → 2026-10-19** window.

| Risk | Description | Impact | Mitigation |
|------|-------------|--------|------------|
| VOL gap | LC.SHF VOL only covers 2026-09-03→2026-10-19 (27 days) | HIGH for VOL factor | Already documented; not used by V1 factors |
| HIGH/LOW gap | May be similar to VOL — GFE instruments sparse | **HIGH** | Test before building ATR% factor |
| Contract month gaps | Different contract months may have different date ranges | MEDIUM | Use continuous contract or dominant contract |
| New instruments | RB/HC data availability untested in this time window | MEDIUM | First fetch may reveal gaps |

### 1.5 WSD Formula Risk Matrix

| Formula Pattern | Tested? | Risk | Notes |
|----------------|---------|------|-------|
| `WSD(sym,"CLOSE;OI;SETTLE",...)` | ✅ Yes (6 metals) | LOW | All indicators returned |
| `WSD(sym,"HIGH;LOW",...)` | ❌ No | **HIGH** | Not tested — GFE risk |
| `WSD(sym,"HIGH;LOW;CLOSE",...)` | ❌ No | MEDIUM | Mixed fields may behave differently |
| `WSD(sym,"OPEN;HIGH;LOW;CLOSE",...)` | ❌ No | MEDIUM | OHLC — most standard, likely works |
| `WSD(sym,"ATR",...)` | ❌ No | HIGH | ATR may not be a direct WSD field |

### 1.6 ATR% Factor — Pre-Implementation Checklist

Before building ATR% as F10 factor, verify:

- [ ] HIGH data returns non-zero for all 9 instruments
- [ ] LOW data returns non-zero for all 9 instruments
- [ ] HIGH ≥ LOW for all rows (sanity check)
- [ ] HIGH ≤ CLOSE × 1.02 (upper bound sanity)
- [ ] LOW ≥ CLOSE × 0.98 (lower bound sanity)
- [ ] No NULL/NaN values in HIGH/LOW columns
- [ ] GFE (LC.GFE) specifically tested for HIGH/LOW availability
- [ ] RB.SHF and HC.SHF tested for date range coverage

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

*Generated by DSHC-MAINT-01 | 2026-10-19 | wind_api_calls=0*