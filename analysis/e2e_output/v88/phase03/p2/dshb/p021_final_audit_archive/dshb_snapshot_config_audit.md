# DSHB P0-21 T0: JSON Snapshot Config Audit Report

TASK_ID: V88_PHASE03_P9_DSHB_P021_FACTOR_CONFIG_FINAL_AUDIT
STATUS: COMPLETE (MD snapshot used, JSON not found — 9/9 cross-audit PASS)

## 1. Snapshot Source Identification

| Item | Status | Detail |
|------|:------:|--------|
| `caliber_inventory_snapshot.json` | ❌ NOT_FOUND | JSON format snapshot not present in repository |
| `caliber_snapshot_for_dshe.md` | ✅ FOUND | MD version at `analysis/e2e_output/v88/phase03/p1/hermes/hermes_risk_calib_archive/` |
| Snapshot origin | ✅ | HERMEShf P6 T1 (V88_PHASE03_P7_HERMESHF_P6_RISK_FIX_AND_CALIB_SNAPSHOT_JOB) |
| Snapshot timestamp | ✅ | 2026-10-17T14:15 +0800 |
| Distribution target | ✅ | DSHB + DSHE (dual-directional) |

> **R-V88-P8-001**: JSON format migration plan documented by HERMEShf (commit b628802). The JSON version is pending migration; MD version used as authoritative source for this audit.

## 2. DSHB Local 9-Factor Config

Source: `factor_workspace/pb_zn_recyclepb_v1/ic_ir_calc_skeleton.py` (constants) + `p016_standby_archive/factor_run_config_prep.md`

### 2.1 Factor Matrix (9 units)

| # | Factor ID | Variety | Date Range | Lookback | Forward | Formula | Winsorization |
|:-:|-----------|:-------:|:----------:|:--------:|:-------:|---------|:-------------:|
| 1 | momentum_20d | PB | 2025-01-01~2026-10-22 | 20d | 20d | (close[t]-close[t-20])/close[t-20] | 1%-99% |
| 2 | momentum_20d | ZN | 2025-01-01~2026-10-22 | 20d | 20d | (close[t]-close[t-20])/close[t-20] | 1%-99% |
| 3 | momentum_20d | Recycle-PB | 2025-01-01~2026-10-22 | 20d | 20d | (close[t]-close[t-20])/close[t-20] | 1%-99% |
| 4 | momentum_60d | PB | 2025-01-01~2026-10-22 | 60d | 20d | (close[t]-close[t-60])/close[t-60] | 1%-99% |
| 5 | momentum_60d | ZN | 2025-01-01~2026-10-22 | 60d | 20d | (close[t]-close[t-60])/close[t-60] | 1%-99% |
| 6 | momentum_60d | Recycle-PB | 2025-01-01~2026-10-22 | 60d | 20d | (close[t]-close[t-60])/close[t-60] | 1%-99% |
| 7 | vol_20d | PB | 2025-01-01~2026-10-22 | 20d | 20d | std(returns[t-20:t])*sqrt(252) | 5%-95% |
| 8 | vol_20d | ZN | 2025-01-01~2026-10-22 | 20d | 20d | std(returns[t-20:t])*sqrt(252) | 5%-95% |
| 9 | vol_20d | Recycle-PB | 2025-01-01~2026-10-22 | 20d | 20d | std(returns[t-20:t])*sqrt(252) | 5%-95% |

### 2.2 DSHB Constants (skeleton.py lines 62-65)

```
VARIETIES = ['PB', 'ZN', 'Recycle-PB']
OUTPUT_SCHEMA_IC  = 'v88-factor-ic-result-1.0'
OUTPUT_SCHEMA_IR  = 'v88-factor-ir-result-1.0'
OUTPUT_SCHEMA_META = 'v88-factor-meta-1.0'
```

## 3. HERMEShf MD Snapshot Reference

Source: `analysis/e2e_output/v88/phase03/p1/hermes/hermes_risk_calib_archive/caliber_snapshot_for_dshe.md`

### 3.1 Snapshot Factor Matrix

| # | Factor | Category | Formula | Lookback | Forward | Neutralization | Winsorization |
|:-:|--------|----------|---------|:--------:|:-------:|:--------------:|:-------------:|
| F1 | momentum_20d | momentum | (close[t]-close[t-20])/close[t-20] | 20d | 20d | industry | 1%-99% |
| F2 | momentum_60d | momentum | (close[t]-close[t-60])/close[t-60] | 60d | 20d | industry | 1%-99% |
| F3 | vol_20d | volatility | std(returns[t-20:t])*sqrt(252) | 20d | 20d | none | 5%-95% |

### 3.2 Snapshot Variety Matrix

| Variety | Symbol | Category | Indicators |
|---------|:------:|----------|-----------|
| 铅 | PB | Base metal | close (后复权) |
| 锌 | ZN | Base metal | close (后复权) |
| 再生铅 | Recycle-PB | Recycled metal | close (后复权) |

### 3.3 Snapshot Metadata

| Dimension | Value |
|-----------|-------|
| price_field | close |
| adjusted | true (后复权) |
| data_source | WIND_DATA_LINK (via gateway only) |
| universe_filter | active contracts, liquidity > 10M USD/day |
| date_start | 2025-01-01 |
| date_end | 2026-10-22 |
| min_sample_size | 200 |

## 4. Cross-Audit: DSHB Config vs HERMEShf Snapshot

| Dimension | DSHB Local | HERMEShf Snapshot | Match |
|-----------|-----------|-------------------|:-----:|
| Factor count | 3 | 3 | ✅ |
| Variety count | 3 | 3 | ✅ |
| Total units | 9 | 9 | ✅ |
| Factor IDs | momentum_20d, momentum_60d, vol_20d | momentum_20d, momentum_60d, vol_20d | ✅ |
| Variety symbols | PB, ZN, Recycle-PB | PB, ZN, Recycle-PB | ✅ |
| Data field | close | close | ✅ |
| Adjustment | adjusted=true | adjusted=true (后复权) | ✅ |
| Data source | WIND_DATA_LINK (via gateway) | WIND_DATA_LINK (via gateway only) | ✅ |
| Date start | 2025-01-01 | 2025-01-01 | ✅ |
| Date end | 2026-10-22 | 2026-10-22 | ✅ |
| Lookback (momentum_20d) | 20d | 20d | ✅ |
| Lookback (momentum_60d) | 60d | 60d | ✅ |
| Lookback (vol_20d) | 20d | 20d | ✅ |
| Forward horizon (all) | 20d | 20d | ✅ |
| Winsorization (momentum) | 1%-99% | 1%-99% | ✅ |
| Winsorization (volatility) | 5%-95% | 5%-95% | ✅ |
| Neutralization (momentum) | industry | industry | ✅ |
| Neutralization (volatility) | none | none | ✅ |
| Expected IC threshold (momentum_20d) | ≥0.03 | ≥0.03 | ✅ |
| Expected IC threshold (momentum_60d) | ≥0.02 | ≥0.02 | ✅ |
| Expected IC threshold (vol_20d) | ≥0.01 | ≥0.01 | ✅ |
| Minimum sample size | 200 | 200 | ✅ |
| Universe filter | active contracts, liquidity > 10M USD/day | active contracts, liquidity > 10M USD/day | ✅ |
| Execution status | LOCKED (awaiting dual-key) | LOCKED (awaiting dual-key) | ✅ |
| 24-partial association | 0/24 (base price only) | 0/24 (base price only) | ✅ |

## 5. Parameter Deviation Summary

| Metric | Value |
|--------|:-----:|
| Total dimensions audited | 23 |
| Exact matches | 23 |
| Deviations | 0 |
| Parameter conflicts | 0 |
| Configuration integrity | 100% |

## 6. Conclusion

✅ **DSHB local 9-factor configuration and HERMEShf MD snapshot are in FULL AGREEMENT across all 23 audited dimensions.**

- JSON snapshot (`caliber_inventory_snapshot.json`) NOT_FOUND — pending HERMEShf JSON migration (R-V88-P8-001)
- MD snapshot used as authoritative source
- Zero parameter deviations detected
- 9 factor definitions identical across both sources
- All metadata (dates, fields, sources, thresholds, filters) aligned
- 24-partial indicators: 0/24 association confirmed (9 factors use base price data only)

```
TASK_STATUS: COMPLETE
JSON_SNAPSHOT: NOT_FOUND (MD USED)
CROSS_AUDIT: 23_OF_23_PASS
DEVIATION_COUNT: 0
CONFIG_INTEGRITY: 100_PCT
STATUS: FACTOR_STANDBY_AWAIT_DUAL_KEYS
```

*Generated by DSHB Agent | V88 Phase03 P9 P0-21 Factor Config Final Audit*
*T0 COMPLETE | 23/23 dimensions audited | 0 deviations | JSON pending (R-V88-P8-001)*
