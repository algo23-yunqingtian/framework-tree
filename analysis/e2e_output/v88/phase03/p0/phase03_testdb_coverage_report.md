# V88 Phase03 P0-R0 Coverage Report

> **Task ID**: V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER
> **Schema**: v88-p0.0.1
> **Generated**: 2026-10-15T13:14:42.603316
> **DB Path**: `phase03_test.db`
> **Gate Phase**: P0

## 1. Overall Coverage Summary

| Metric | Value |
|--------|-------|
| Total DSHE Indicators | 109 |
| Covered (real data) | 84 |
| Coverage Rate | 77.06% |
| Gate Threshold | 60% |
| Gate Status | **PASS** |

> [PASS] Coverage 77.1% >= 60% threshold

## 2. Per-Commodity Coverage

| Commodity | Total | Covered | Rate | Status |
|-----------|-------|---------|------|--------|
| 铜(CU) | 20 | 18 | 90.0% | PASS |
| 铝(AL) | 13 | 10 | 76.9% | PASS |
| 铅(PB) | 13 | 8 | 61.5% | PASS |
| 锌(ZN) | 13 | 9 | 69.2% | PASS |
| 镍(NI) | 13 | 11 | 84.6% | PASS |
| 锡(SN) | 13 | 11 | 84.6% | PASS |
| 锂(LC) | 13 | 8 | 61.5% | PASS |
| 硅(SI) | 11 | 9 | 81.8% | PASS |

### Coverage Progress

```
[██████████████████████████████░░░░░░░░░░] 77.1% / 60% threshold
```

### Per-Commodity Bar Chart

```
CU  [████████████████████████████████████░░░░]  90.0% (18/20)
AL  [██████████████████████████████░░░░░░░░░░]  76.9% (10/13)
PB  [████████████████████████░░░░░░░░░░░░░░░░]  61.5% (8/13)
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

**Count**: 7

| # | Indicator ID | Commodity | Chart ID | Indicator Name | Mapped To | Reason |
|---|-------------|-----------|----------|---------------|-----------|--------|
| 1 | `COMEX_ZN` | 锌(ZN) | `zn_p3_ts_02` | COMEX锌 | `zn_23_comex` | Mapped metric not found in database (gap: no_data) |
| 2 | `LC_FU00015030` | 锂(LC) | `li_p1_ts_01` | 主连 | `li_21_close_front` | Mapped metric not found in database (gap: no_data) |
| 3 | `LC_HOLD_OPEN` | 锂(LC) | `li_p1_ts_02` | 持仓量 | `li_21_openinterest` | Mapped metric not found in database (gap: no_data) |
| 4 | `LC_MONTH_SPREAD` | 锂(LC) | `li_p4_ts_01` | 月差 | `li_24_close_near` | Mapped metric not found in database (gap: no_data) |
| 5 | `SPOT_IS` | 硅(SI) | `si_p3_ts_02` | 工业硅现货 | `si_24_spot` | Mapped metric not found in database (gap: no_data) |
| 6 | `ZN_LONG_SHORT_RATIO` | 锌(ZN) | `zn_p1_gauge_01` | 多空持仓比 | `zn_21_openinterest_2` | Mapped metric not found in database (gap: no_data) |
| 7 | `ZN_MONTH_SPREAD` | 锌(ZN) | `zn_p4_ts_01` | 月差 | `zn_24_term_struct` | Mapped metric not found in database (gap: no_data) |

### 3.3 Simulated Only (Entry exists but no real points)

No items in this category. [OK]

### 3.4 Other Gaps

No items in this category. [OK]

## 4. Covered Indicators Detail

**Total covered**: 84 / 109

| # | Indicator ID | Commodity | Chart ID | Records | Date Range |
|---|-------------|-----------|----------|---------|------------|
| 1 | `AL_BASIS` | 铝(AL) | `al_p2_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 2 | `AL_FU00014934` | 铝(AL) | `al_p1_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 3 | `AL_HOLD_OPEN` | 铝(AL) | `al_p1_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 4 | `AL_MONTH_SPREAD` | 铝(AL) | `al_p4_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 5 | `AL_PRICE_PERCENTILE` | 铝(AL) | `al_p5_gauge_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 6 | `AL_SMELTING_PROFIT` | 铝(AL) | `al_p5_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 7 | `AL_SPOT_PREMIUM` | 铝(AL) | `al_p2_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 8 | `AL_TOP20_LONG` | 铝(AL) | `al_p6_bar_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 9 | `AL_TOP20_SHORT` | 铝(AL) | `al_p6_bar_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 10 | `LME_AL` | 铝(AL) | `al_p3_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 11 | `COMEX_CU` | 铜(CU) | `cu_p3_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 12 | `CU_BASIS` | 铜(CU) | `cu_p2_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 13 | `CU_COST_PERCENTILE` | 铜(CU) | `cu_c1_heatmap_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 14 | `CU_FU00014935` | 铜(CU) | `cu_i1_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 15 | `CU_FU00014941` | 铜(CU) | `cu_p1_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 16 | `CU_HOLD_OPEN` | 铜(CU) | `cu_p1_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 17 | `CU_LONG_SHORT_RATIO` | 铜(CU) | `cu_p1_gauge_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 18 | `CU_MONTH_SPREAD` | 铜(CU) | `cu_p4_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 19 | `CU_PRICE_PERCENTILE` | 铜(CU) | `cu_p5_gauge_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 20 | `CU_SMELTING_PROFIT` | 铜(CU) | `cu_p5_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 21 | `CU_SOCIAL_INV` | 铜(CU) | `cu_i3_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 22 | `CU_SPOT_PREMIUM` | 铜(CU) | `cu_p2_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 23 | `CU_TOP20_LONG` | 铜(CU) | `cu_p6_bar_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 24 | `CU_TOP20_SHORT` | 铜(CU) | `cu_p6_bar_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 25 | `CU_UTILIZATION` | 铜(CU) | `cu_d1_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 26 | `CU_WARRANT_INVENTORY` | 铜(CU) | `cu_i2_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 27 | `FU00014813` | 铜(CU) | `cu_i1_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 28 | `LME_CU` | 铜(CU) | `cu_p3_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 29 | `LC_BASIS` | 锂(LC) | `li_p2_ts_02` | 754 | 2023-07-21 ~ 2026-08-28 |
| 30 | `LC_LONG_SHORT_RATIO` | 锂(LC) | `li_p1_gauge_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 31 | `LC_SMELTING_PROFIT` | 锂(LC) | `li_p5_ts_01` | 891 | 2023-02-01 ~ 2026-08-28 |
| 32 | `LC_SPOT_PREMIUM` | 锂(LC) | `li_p2_ts_01` | 439 | 2024-11-14 ~ 2026-08-28 |
| 33 | `LC_TOP20_LONG` | 锂(LC) | `li_p6_bar_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 34 | `LC_TOP20_SHORT` | 锂(LC) | `li_p6_bar_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 35 | `LME_LC` | 锂(LC) | `li_p3_ts_01` | 754 | 2023-07-21 ~ 2026-08-28 |
| 36 | `SPOT_LICAR` | 锂(LC) | `li_p3_ts_02` | 439 | 2024-11-14 ~ 2026-08-28 |
| 37 | `LME_NI` | 镍(NI) | `ni_p3_ts_01` | 1862 | 2018-10-10 ~ 2026-08-28 |
| 38 | `NI_BASIS` | 镍(NI) | `ni_p2_ts_02` | 2778 | 2015-03-27 ~ 2026-08-28 |
| 39 | `NI_FU00014982` | 镍(NI) | `ni_p1_ts_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 40 | `NI_HOLD_OPEN` | 镍(NI) | `ni_p1_ts_02` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 41 | `NI_LONG_SHORT_RATIO` | 镍(NI) | `ni_p1_gauge_01` | 346 | 2020-01-03 ~ 2026-08-21 |
| 42 | `NI_MONTH_SPREAD` | 镍(NI) | `ni_p4_ts_01` | 1659 | 2020-01-02 ~ 2026-08-28 |
| 43 | `NI_PRICE_PERCENTILE` | 镍(NI) | `ni_p5_gauge_01` | 1872 | 2018-10-10 ~ 2026-08-28 |
| 44 | `NI_SMELTING_PROFIT` | 镍(NI) | `ni_p5_ts_01` | 1745 | 2019-08-14 ~ 2026-08-28 |
| 45 | `NI_SPOT_PREMIUM` | 镍(NI) | `ni_p2_ts_01` | 1655 | 2020-01-02 ~ 2026-08-28 |
| 46 | `NI_TOP20_LONG` | 镍(NI) | `ni_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 47 | `NI_TOP20_SHORT` | 镍(NI) | `ni_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 48 | `LME_PB` | 铅(PB) | `pb_p3_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 49 | `PB_BASIS` | 铅(PB) | `pb_p2_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 50 | `PB_FU00014946` | 铅(PB) | `pb_p1_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 51 | `PB_HOLD_OPEN` | 铅(PB) | `pb_p1_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 52 | `PB_MONTH_SPREAD` | 铅(PB) | `pb_p4_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 53 | `PB_SMELTING_PROFIT` | 铅(PB) | `pb_p5_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 54 | `PB_SPOT_PREMIUM` | 铅(PB) | `pb_p2_ts_01` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 55 | `PB_TERM_STRUCTURE` | 铅(PB) | `pb_p4_ts_02` | 3041 | 2015-01-02 ~ 2026-08-28 |
| 56 | `LME_SI` | 硅(SI) | `si_p3_ts_01` | 406 | 2024-12-26 ~ 2026-08-28 |
| 57 | `SI_BASIS` | 硅(SI) | `si_p2_ts_02` | 893 | 2022-12-22 ~ 2026-08-28 |
| 58 | `SI_FU00015015` | 硅(SI) | `si_p1_ts_01` | 893 | 2022-12-22 ~ 2026-08-28 |
| 59 | `SI_HOLD_OPEN` | 硅(SI) | `si_p1_ts_02` | 893 | 2022-12-22 ~ 2026-08-28 |
| 60 | `SI_LONG_SHORT_RATIO` | 硅(SI) | `si_p1_gauge_01` | 893 | 2022-12-22 ~ 2026-08-28 |
| 61 | `SI_MONTH_SPREAD` | 硅(SI) | `si_p4_ts_01` | 893 | 2022-12-22 ~ 2026-08-28 |
| 62 | `SI_PRICE_PERCENTILE` | 硅(SI) | `si_p5_gauge_01` | 186 | 2022-12-16 ~ 2026-08-28 |
| 63 | `SI_SMELTING_PROFIT` | 硅(SI) | `si_p5_ts_01` | 186 | 2022-12-16 ~ 2026-08-28 |
| 64 | `SI_SPOT_PREMIUM` | 硅(SI) | `si_p2_ts_01` | 774 | 2023-06-20 ~ 2026-08-28 |
| 65 | `LME_SN` | 锡(SN) | `sn_p3_ts_01` | 1122 | 2022-03-21 ~ 2026-08-28 |
| 66 | `SN_BASIS` | 锡(SN) | `sn_p2_ts_02` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 67 | `SN_FU00014952` | 锡(SN) | `sn_p1_ts_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 68 | `SN_HOLD_OPEN` | 锡(SN) | `sn_p1_ts_02` | 345 | 2020-01-03 ~ 2026-08-21 |
| 69 | `SN_LONG_SHORT_RATIO` | 锡(SN) | `sn_p1_gauge_01` | 345 | 2020-01-03 ~ 2026-08-21 |
| 70 | `SN_MONTH_SPREAD` | 锡(SN) | `sn_p4_ts_01` | 1538 | 2020-05-06 ~ 2026-08-28 |
| 71 | `SN_PRICE_PERCENTILE` | 锡(SN) | `sn_p5_gauge_01` | 1686 | 2019-11-06 ~ 2026-08-28 |
| 72 | `SN_SMELTING_PROFIT` | 锡(SN) | `sn_p5_ts_01` | 2362 | 2017-01-03 ~ 2026-08-28 |
| 73 | `SN_SPOT_PREMIUM` | 锡(SN) | `sn_p2_ts_01` | 2834 | 2015-01-05 ~ 2026-08-28 |
| 74 | `SN_TOP20_LONG` | 锡(SN) | `sn_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 75 | `SN_TOP20_SHORT` | 锡(SN) | `sn_p6_bar_01` | 2779 | 2015-03-27 ~ 2026-08-28 |
| 76 | `LME_ZN` | 锌(ZN) | `zn_p3_ts_01` | 1122 | 2022-03-21 ~ 2026-08-28 |
| 77 | `ZN_BASIS` | 锌(ZN) | `zn_p2_ts_02` | 2834 | 2015-01-05 ~ 2026-08-28 |
| 78 | `ZN_FU00014950` | 锌(ZN) | `zn_p1_ts_01` | 2833 | 2015-01-05 ~ 2026-08-28 |
| 79 | `ZN_HOLD_OPEN` | 锌(ZN) | `zn_p1_ts_02` | 345 | 2020-01-03 ~ 2026-08-21 |
| 80 | `ZN_PRICE_PERCENTILE` | 锌(ZN) | `zn_p5_gauge_01` | 13 | 2015-06-30 ~ 2025-12-31 |
| 81 | `ZN_SMELTING_PROFIT` | 锌(ZN) | `zn_p5_ts_01` | 46 | 2015-03-31 ~ 2026-06-30 |
| 82 | `ZN_SPOT_PREMIUM` | 锌(ZN) | `zn_p2_ts_01` | 2294 | 2017-01-03 ~ 2026-08-28 |
| 83 | `ZN_TOP20_LONG` | 锌(ZN) | `zn_p6_bar_01` | 2833 | 2015-01-05 ~ 2026-08-28 |
| 84 | `ZN_TOP20_SHORT` | 锌(ZN) | `zn_p6_bar_01` | 2833 | 2015-01-05 ~ 2026-08-28 |

## 5. Recommendations

1. 18 indicators have no DSHB metric mapping. Update INDICATOR_MAPPING in cache_coverage_calc.py to add mappings.
2. 7 mapped indicators are missing from api_cache.db. Run refresh_cache.py or db_import_jsonl.py to import data.

## 6. Gate Decision

| Gate Phase | Threshold | Actual | Status |
|------------|-----------|--------|--------|
| P0 | 60% | 77.06% | **PASS** |

> **[PASS] D7 Gate Decision: PASS**
>
> Coverage rate 77.1% exceeds the P0 threshold of 60%.
> Proceed to next phase (P1) when ready.

---
*Generated by cache_coverage_calc.py · 2026-10-15T13:14:42.603316*
