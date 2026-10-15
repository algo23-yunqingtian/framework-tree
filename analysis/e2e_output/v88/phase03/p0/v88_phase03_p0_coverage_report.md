# V88 Phase03 P0-R0 Coverage Report

> **Task ID**: V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER
> **Schema**: v88-p0.0.1
> **Generated**: 2026-10-15T11:23:10.549325
> **DB Path**: `scripts\api_cache.db`
> **Gate Phase**: P0

## 1. Overall Coverage Summary

| Metric | Value |
|--------|-------|
| Total DSHE Indicators | 109 |
| Covered (real data) | 48 |
| Coverage Rate | 44.04% |
| Gate Threshold | 60% |
| Gate Status | **FAIL** |

> [FAIL] Coverage 44.0% < 60% threshold

## 2. Per-Commodity Coverage

| Commodity | Total | Covered | Rate | Status |
|-----------|-------|---------|------|--------|
| 铜(CU) | 20 | 0 | 0.0% | FAIL |
| 铝(AL) | 13 | 0 | 0.0% | FAIL |
| 铅(PB) | 13 | 0 | 0.0% | FAIL |
| 锌(ZN) | 13 | 9 | 69.2% | PASS |
| 镍(NI) | 13 | 11 | 84.6% | PASS |
| 锡(SN) | 13 | 11 | 84.6% | PASS |
| 锂(LC) | 13 | 8 | 61.5% | PASS |
| 硅(SI) | 11 | 9 | 81.8% | PASS |

### Coverage Progress

```
[█████████████████░░░░░░░░░░░░░░░░░░░░░░░] 44.0% / 60% threshold
```

### Per-Commodity Bar Chart

```
CU  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/20)
AL  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
PB  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
ZN  [███████████████████████████░░░░░░░░░░░░░]  69.2% (9/13)
NI  [█████████████████████████████████░░░░░░░]  84.6% (11/13)
SN  [█████████████████████████████████░░░░░░░]  84.6% (11/13)
LI  [████████████████████████░░░░░░░░░░░░░░░░]  61.5% (8/13)
SI  [████████████████████████████████░░░░░░░░]  81.8% (9/11)
```

## 3. Gap Analysis

### 3.1 No Mapping (DSHE → DSHB mapping missing)

**Count**: 18

| # | Indicator ID | Commodity | Chart ID | Indicator Name | Mapped To | Reason |
|---|-------------|-----------|----------|---------------|-----------|--------|
| 1 | `AL_LONG_SHORT_RATIO` | 铝(AL) | `al_p1_gauge_01` | 多空持仓比 | `N/A` | No DSHB metric mapping defined |
| 2 | `AL_TERM_STRUCTURE` | 铝(AL) | `al_p4_ts_02` | 期限结构 | `N/A` | No DSHB metric mapping defined |
| 3 | `COMEX_AL` | 铝(AL) | `al_p3_ts_02` | COMEX铝 | `N/A` | No DSHB metric mapping defined |
| 4 | `COMEX_NI` | 镍(NI) | `ni_p3_ts_02` | COMEX镍 | `N/A` | No DSHB metric mapping defined |
| 5 | `COMEX_PB` | 铅(PB) | `pb_p3_ts_02` | COMEX铅 | `N/A` | No DSHB metric mapping defined |
| 6 | `COMEX_SN` | 锡(SN) | `sn_p3_ts_02` | COMEX锡 | `N/A` | No DSHB metric mapping defined |
| 7 | `CU_BALANCE_SHEET` | 铜(CU) | `cu_b2_ts_01` | 年度供需平衡 | `N/A` | No DSHB metric mapping defined |
| 8 | `CU_TERM_STRUCTURE` | 铜(CU) | `cu_p4_ts_02` | 期限结构 | `N/A` | No DSHB metric mapping defined |
| 9 | `LC_PRICE_PERCENTILE` | 锂(LC) | `li_p5_gauge_01` | 价格分位数 | `N/A` | No DSHB metric mapping defined |
| 10 | `LC_TERM_STRUCTURE` | 锂(LC) | `li_p4_ts_02` | 期限结构 | `N/A` | No DSHB metric mapping defined |
| 11 | `NI_TERM_STRUCTURE` | 镍(NI) | `ni_p4_ts_02` | 期限结构 | `N/A` | No DSHB metric mapping defined |
| 12 | `PB_LONG_SHORT_RATIO` | 铅(PB) | `pb_p1_gauge_01` | 多空持仓比 | `N/A` | No DSHB metric mapping defined |
| 13 | `PB_PRICE_PERCENTILE` | 铅(PB) | `pb_p5_gauge_01` | 价格分位数 | `N/A` | No DSHB metric mapping defined |
| 14 | `PB_TOP20_LONG` | 铅(PB) | `pb_p6_bar_01` | 多头前20 | `N/A` | No DSHB metric mapping defined |
| 15 | `PB_TOP20_SHORT` | 铅(PB) | `pb_p6_bar_01` | 空头前20 | `N/A` | No DSHB metric mapping defined |
| 16 | `SI_TERM_STRUCTURE` | 硅(SI) | `si_p4_ts_02` | 期限结构 | `N/A` | No DSHB metric mapping defined |
| 17 | `SN_TERM_STRUCTURE` | 锡(SN) | `sn_p4_ts_02` | 期限结构 | `N/A` | No DSHB metric mapping defined |
| 18 | `ZN_TERM_STRUCTURE` | 锌(ZN) | `zn_p4_ts_02` | 期限结构 | `N/A` | No DSHB metric mapping defined |

### 3.2 No Data (Mapped metric not found in DB)

**Count**: 43

| # | Indicator ID | Commodity | Chart ID | Indicator Name | Mapped To | Reason |
|---|-------------|-----------|----------|---------------|-----------|--------|
| 1 | `AL_BASIS` | 铝(AL) | `al_p2_ts_02` | 基差 | `al_00_basis` | Mapped metric not found in database (gap: no_data) |
| 2 | `AL_FU00014934` | 铝(AL) | `al_p1_ts_01` | 主连 | `al_00_close_front` | Mapped metric not found in database (gap: no_data) |
| 3 | `AL_HOLD_OPEN` | 铝(AL) | `al_p1_ts_02` | 持仓量 | `al_00_openinterest_front` | Mapped metric not found in database (gap: no_data) |
| 4 | `AL_MONTH_SPREAD` | 铝(AL) | `al_p4_ts_01` | 月差 | `al_24_lme_spread` | Mapped metric not found in database (gap: no_data) |
| 5 | `AL_PRICE_PERCENTILE` | 铝(AL) | `al_p5_gauge_01` | 价格分位数 | `al_00_cost_percentile` | Mapped metric not found in database (gap: no_data) |
| 6 | `AL_SMELTING_PROFIT` | 铝(AL) | `al_p5_ts_01` | 冶炼利润 | `al_25_profit` | Mapped metric not found in database (gap: no_data) |
| 7 | `AL_SPOT_PREMIUM` | 铝(AL) | `al_p2_ts_01` | 现货升贴水 | `al_00_premium` | Mapped metric not found in database (gap: no_data) |
| 8 | `AL_TOP20_LONG` | 铝(AL) | `al_p6_bar_01` | 多头前20 | `al_26_long_top20` | Mapped metric not found in database (gap: no_data) |
| 9 | `AL_TOP20_SHORT` | 铝(AL) | `al_p6_bar_01` | 空头前20 | `al_26_short_top20` | Mapped metric not found in database (gap: no_data) |
| 10 | `COMEX_CU` | 铜(CU) | `cu_p3_ts_02` | COMEX铜 | `cu_23_comex_close` | Mapped metric not found in database (gap: no_data) |
| 11 | `COMEX_ZN` | 锌(ZN) | `zn_p3_ts_02` | COMEX锌 | `zn_23_comex` | Mapped metric not found in database (gap: no_data) |
| 12 | `CU_BASIS` | 铜(CU) | `cu_p2_ts_02` | 基差 | `cu_21_basis` | Mapped metric not found in database (gap: no_data) |
| 13 | `CU_COST_PERCENTILE` | 铜(CU) | `cu_c1_heatmap_01` | 成本曲线分位 | `cu_25_tc_conc` | Mapped metric not found in database (gap: no_data) |
| 14 | `CU_FU00014935` | 铜(CU) | `cu_i1_ts_01` | 上期所库存 | `cu_41_output` | Mapped metric not found in database (gap: no_data) |
| 15 | `CU_FU00014941` | 铜(CU) | `cu_p1_ts_01` | 主连 | `cu_21_close_front` | Mapped metric not found in database (gap: no_data) |
| 16 | `CU_HOLD_OPEN` | 铜(CU) | `cu_p1_ts_02` | 持仓量 | `cu_21_openinterest` | Mapped metric not found in database (gap: no_data) |
| 17 | `CU_LONG_SHORT_RATIO` | 铜(CU) | `cu_p1_gauge_01` | 多空持仓比 | `cu_21_openinterest_longshort` | Mapped metric not found in database (gap: no_data) |
| 18 | `CU_MONTH_SPREAD` | 铜(CU) | `cu_p4_ts_01` | 月差 | `cu_24_openinterest_volume` | Mapped metric not found in database (gap: no_data) |
| 19 | `CU_PRICE_PERCENTILE` | 铜(CU) | `cu_p5_gauge_01` | 价格分位数 | `cu_25_profit_percentile` | Mapped metric not found in database (gap: no_data) |
| 20 | `CU_SMELTING_PROFIT` | 铜(CU) | `cu_p5_ts_01` | 冶炼利润 | `cu_25_profit` | Mapped metric not found in database (gap: no_data) |
| 21 | `CU_SOCIAL_INV` | 铜(CU) | `cu_i3_ts_01` | 社库 | `cu_43_social_stock` | Mapped metric not found in database (gap: no_data) |
| 22 | `CU_SPOT_PREMIUM` | 铜(CU) | `cu_p2_ts_01` | 现货升贴水 | `cu_22_premium` | Mapped metric not found in database (gap: no_data) |
| 23 | `CU_TOP20_LONG` | 铜(CU) | `cu_p6_bar_01` | 多头前20 | `cu_26_openinterest_top20_front` | Mapped metric not found in database (gap: no_data) |
| 24 | `CU_TOP20_SHORT` | 铜(CU) | `cu_p6_bar_01` | 空头前20 | `cu_26_openinterest` | Mapped metric not found in database (gap: no_data) |
| 25 | `CU_UTILIZATION` | 铜(CU) | `cu_d1_ts_01` | 开工率 | `cu_321_util_capacity_util` | Mapped metric not found in database (gap: no_data) |
| 26 | `CU_WARRANT_INVENTORY` | 铜(CU) | `cu_i2_ts_01` | 仓单库存 | `cu_42_warrant_reg` | Mapped metric not found in database (gap: no_data) |
| 27 | `FU00014813` | 铜(CU) | `cu_i1_ts_01` | LME库存 | `cu_23_inv` | Mapped metric not found in database (gap: no_data) |
| 28 | `LC_FU00015030` | 锂(LC) | `li_p1_ts_01` | 主连 | `li_21_close_front` | Mapped metric not found in database (gap: no_data) |
| 29 | `LC_HOLD_OPEN` | 锂(LC) | `li_p1_ts_02` | 持仓量 | `li_21_openinterest` | Mapped metric not found in database (gap: no_data) |
| 30 | `LC_MONTH_SPREAD` | 锂(LC) | `li_p4_ts_01` | 月差 | `li_24_close_near` | Mapped metric not found in database (gap: no_data) |
| 31 | `LME_AL` | 铝(AL) | `al_p3_ts_01` | LME铝 | `al_00_lme_close` | Mapped metric not found in database (gap: no_data) |
| 32 | `LME_CU` | 铜(CU) | `cu_p3_ts_01` | LME铜 | `cu_23_lme_close` | Mapped metric not found in database (gap: no_data) |
| 33 | `LME_PB` | 铅(PB) | `pb_p3_ts_01` | LME铅 | `j23_lme_cash` | Mapped metric not found in database (gap: no_data) |
| 34 | `PB_BASIS` | 铅(PB) | `pb_p2_ts_02` | 基差 | `j22_premium` | Mapped metric not found in database (gap: no_data) |
| 35 | `PB_FU00014946` | 铅(PB) | `pb_p1_ts_01` | 主连 | `j21_close` | Mapped metric not found in database (gap: no_data) |
| 36 | `PB_HOLD_OPEN` | 铅(PB) | `pb_p1_ts_02` | 持仓量 | `j21_oi` | Mapped metric not found in database (gap: no_data) |
| 37 | `PB_MONTH_SPREAD` | 铅(PB) | `pb_p4_ts_01` | 月差 | `j24_spread_m` | Mapped metric not found in database (gap: no_data) |
| 38 | `PB_SMELTING_PROFIT` | 铅(PB) | `pb_p5_ts_01` | 冶炼利润 | `j25_smelt_cost` | Mapped metric not found in database (gap: no_data) |
| 39 | `PB_SPOT_PREMIUM` | 铅(PB) | `pb_p2_ts_01` | 现货升贴水 | `j22_spot` | Mapped metric not found in database (gap: no_data) |
| 40 | `PB_TERM_STRUCTURE` | 铅(PB) | `pb_p4_ts_02` | 期限结构 | `j24_spread_s` | Mapped metric not found in database (gap: no_data) |
| 41 | `SPOT_IS` | 硅(SI) | `si_p3_ts_02` | 工业硅现货 | `si_24_spot` | Mapped metric not found in database (gap: no_data) |
| 42 | `ZN_LONG_SHORT_RATIO` | 锌(ZN) | `zn_p1_gauge_01` | 多空持仓比 | `zn_21_openinterest_2` | Mapped metric not found in database (gap: no_data) |
| 43 | `ZN_MONTH_SPREAD` | 锌(ZN) | `zn_p4_ts_01` | 月差 | `zn_24_term_struct` | Mapped metric not found in database (gap: no_data) |

### 3.3 Simulated Only (Entry exists but no real points)

No items in this category. [OK]

### 3.4 Other Gaps

No items in this category. [OK]

## 4. Covered Indicators Detail

**Total covered**: 48 / 109

| # | Indicator ID | Commodity | Chart ID | Records | Date Range |
|---|-------------|-----------|----------|---------|------------|
| 1 | `LC_BASIS` | 锂(LC) | `li_p2_ts_02` | 754 | 2023-07-21 ~ 2026-08-28 |
| 2 | `LC_LONG_SHORT_RATIO` | 锂(LC) | `li_p1_gauge_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 3 | `LC_SMELTING_PROFIT` | 锂(LC) | `li_p5_ts_01` | 891 | 2023-02-01 ~ 2026-08-28 |
| 4 | `LC_SPOT_PREMIUM` | 锂(LC) | `li_p2_ts_01` | 439 | 2024-11-14 ~ 2026-08-28 |
| 5 | `LC_TOP20_LONG` | 锂(LC) | `li_p6_bar_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 6 | `LC_TOP20_SHORT` | 锂(LC) | `li_p6_bar_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 7 | `LME_LC` | 锂(LC) | `li_p3_ts_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 8 | `SPOT_LICAR` | 锂(LC) | `li_p3_ts_02` | 439 | 2024-11-14 ~ 2026-08-28 |
| 9 | `LME_NI` | 镍(NI) | `ni_p3_ts_01` | 1862 | 2018-10-10 ~ 2026-08-28 |
| 10 | `NI_BASIS` | 镍(NI) | `ni_p2_ts_02` | 2778 | 2015-03-27 ~ 2026-08-28 |
| 11 | `NI_FU00014982` | 镍(NI) | `ni_p1_ts_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 12 | `NI_HOLD_OPEN` | 镍(NI) | `ni_p1_ts_02` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 13 | `NI_LONG_SHORT_RATIO` | 镍(NI) | `ni_p1_gauge_01` | 346 | 2020-01-03 ~ 2026-08-21 |
| 14 | `NI_MONTH_SPREAD` | 镍(NI) | `ni_p4_ts_01` | 1659 | 2020-01-02 ~ 2026-08-28 |
| 15 | `NI_PRICE_PERCENTILE` | 镍(NI) | `ni_p5_gauge_01` | 1872 | 2018-10-10 ~ 2026-08-28 |
| 16 | `NI_SMELTING_PROFIT` | 镍(NI) | `ni_p5_ts_01` | 1745 | 2019-08-14 ~ 2026-08-28 |
| 17 | `NI_SPOT_PREMIUM` | 镍(NI) | `ni_p2_ts_01` | 1655 | 2020-01-02 ~ 2026-08-28 |
| 18 | `NI_TOP20_LONG` | 镍(NI) | `ni_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 19 | `NI_TOP20_SHORT` | 镍(NI) | `ni_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 20 | `LME_SI` | 硅(SI) | `si_p3_ts_01` | 406 | 2024-12-26 ~ 2026-08-28 |
| 21 | `SI_BASIS` | 硅(SI) | `si_p2_ts_02` | 893 | 2022-12-22 ~ 2026-08-28 |
| 22 | `SI_FU00015015` | 硅(SI) | `si_p1_ts_01` | 893 | 2022-12-22 ~ 2026-08-28 |
| 23 | `SI_HOLD_OPEN` | 硅(SI) | `si_p1_ts_02` | 893 | 2022-12-22 ~ 2026-08-28 |
| 24 | `SI_LONG_SHORT_RATIO` | 硅(SI) | `si_p1_gauge_01` | 893 | 2022-12-22 ~ 2026-08-28 |
| 25 | `SI_MONTH_SPREAD` | 硅(SI) | `si_p4_ts_01` | 893 | 2022-12-22 ~ 2026-08-28 |
| 26 | `SI_PRICE_PERCENTILE` | 硅(SI) | `si_p5_gauge_01` | 186 | 2022-12-16 ~ 2026-08-28 |
| 27 | `SI_SMELTING_PROFIT` | 硅(SI) | `si_p5_ts_01` | 186 | 2022-12-16 ~ 2026-08-28 |
| 28 | `SI_SPOT_PREMIUM` | 硅(SI) | `si_p2_ts_01` | 774 | 2023-06-20 ~ 2026-08-28 |
| 29 | `LME_SN` | 锡(SN) | `sn_p3_ts_01` | 1122 | 2022-03-21 ~ 2026-08-28 |
| 30 | `SN_BASIS` | 锡(SN) | `sn_p2_ts_02` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 31 | `SN_FU00014952` | 锡(SN) | `sn_p1_ts_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 32 | `SN_HOLD_OPEN` | 锡(SN) | `sn_p1_ts_02` | 345 | 2020-01-03 ~ 2026-08-21 |
| 33 | `SN_LONG_SHORT_RATIO` | 锡(SN) | `sn_p1_gauge_01` | 345 | 2020-01-03 ~ 2026-08-21 |
| 34 | `SN_MONTH_SPREAD` | 锡(SN) | `sn_p4_ts_01` | 1538 | 2020-05-06 ~ 2026-08-28 |
| 35 | `SN_PRICE_PERCENTILE` | 锡(SN) | `sn_p5_gauge_01` | 1686 | 2019-11-06 ~ 2026-08-28 |
| 36 | `SN_SMELTING_PROFIT` | 锡(SN) | `sn_p5_ts_01` | 2362 | 2017-01-03 ~ 2026-08-28 |
| 37 | `SN_SPOT_PREMIUM` | 锡(SN) | `sn_p2_ts_01` | 2834 | 2015-01-05 ~ 2026-08-28 |
| 38 | `SN_TOP20_LONG` | 锡(SN) | `sn_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 39 | `SN_TOP20_SHORT` | 锡(SN) | `sn_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 40 | `LME_ZN` | 锌(ZN) | `zn_p3_ts_01` | 1122 | 2022-03-21 ~ 2026-08-28 |
| 41 | `ZN_BASIS` | 锌(ZN) | `zn_p2_ts_02` | 2834 | 2015-01-05 ~ 2026-08-28 |
| 42 | `ZN_FU00014950` | 锌(ZN) | `zn_p1_ts_01` | 2833 | 2015-01-05 ~ 2026-08-28 |
| 43 | `ZN_HOLD_OPEN` | 锌(ZN) | `zn_p1_ts_02` | 345 | 2020-01-03 ~ 2026-08-21 |
| 44 | `ZN_PRICE_PERCENTILE` | 锌(ZN) | `zn_p5_gauge_01` | 13 | 2015-06-30 ~ 2025-12-31 |
| 45 | `ZN_SMELTING_PROFIT` | 锌(ZN) | `zn_p5_ts_01` | 46 | 2015-03-31 ~ 2026-06-30 |
| 46 | `ZN_SPOT_PREMIUM` | 锌(ZN) | `zn_p2_ts_01` | 2294 | 2017-01-03 ~ 2026-08-28 |
| 47 | `ZN_TOP20_LONG` | 锌(ZN) | `zn_p6_bar_01` | 2833 | 2015-01-05 ~ 2026-08-28 |
| 48 | `ZN_TOP20_SHORT` | 锌(ZN) | `zn_p6_bar_01` | 2833 | 2015-01-05 ~ 2026-08-28 |

## 5. Recommendations

1. Overall coverage (44.0%) is below P0 gate threshold (60%). Need to import 61 more indicators to reach gate.
2. 18 indicators have no DSHB metric mapping. Update INDICATOR_MAPPING in cache_coverage_calc.py to add mappings.
3. 43 mapped indicators are missing from api_cache.db. Run refresh_cache.py or db_import_jsonl.py to import data.

## 6. Gate Decision

| Gate Phase | Threshold | Actual | Status |
|------------|-----------|--------|--------|
| P0 | 60% | 44.04% | **FAIL** |

> **[FAIL] D7 Gate Decision: FAIL**
>
> Coverage rate 44.0% is below the P0 threshold of 60%.
> Need to cover at least 65 indicators to pass.
> Currently 61 indicators are uncovered.
>
> **Required actions**:
> 1. Run `refresh_cache.py` to import missing real data into api_cache.db
> 2. Update INDICATOR_MAPPING for 18 unmapped indicators

---
*Generated by cache_coverage_calc.py · 2026-10-15T11:23:10.549325*
