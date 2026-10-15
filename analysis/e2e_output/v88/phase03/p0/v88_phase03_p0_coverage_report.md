# V88 Phase03 P0-R0 Coverage Report

> **Task ID**: V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER
> **Schema**: v88-p0.0.1
> **Generated**: 2026-10-15T11:21:27.246739
> **DB Path**: `scripts\api_cache.db`
> **Gate Phase**: P0

## 1. Overall Coverage Summary

| Metric | Value |
|--------|-------|
| Total DSHE Indicators | 109 |
| Covered (real data) | 0 |
| Coverage Rate | 0.00% |
| Gate Threshold | 60% |
| Gate Status | **FAIL** |

> [FAIL] Coverage 0.0% < 60% threshold

## 2. Per-Commodity Coverage

| Commodity | Total | Covered | Rate | Status |
|-----------|-------|---------|------|--------|
| 铜(CU) | 20 | 0 | 0.0% | FAIL |
| 铝(AL) | 13 | 0 | 0.0% | FAIL |
| 铅(PB) | 13 | 0 | 0.0% | FAIL |
| 锌(ZN) | 13 | 0 | 0.0% | FAIL |
| 镍(NI) | 13 | 0 | 0.0% | FAIL |
| 锡(SN) | 13 | 0 | 0.0% | FAIL |
| 锂(LC) | 13 | 0 | 0.0% | FAIL |
| 硅(SI) | 11 | 0 | 0.0% | FAIL |

### Coverage Progress

```
[░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0.0% / 60% threshold
```

### Per-Commodity Bar Chart

```
CU  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/20)
AL  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
PB  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
ZN  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
NI  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
SN  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
LI  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/13)
SI  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0.0% (0/11)
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

**Count**: 91

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
| 28 | `LC_BASIS` | 锂(LC) | `li_p2_ts_02` | 基差 | `li_21_basis` | Mapped metric not found in database (gap: no_data) |
| 29 | `LC_FU00015030` | 锂(LC) | `li_p1_ts_01` | 主连 | `li_21_close_front` | Mapped metric not found in database (gap: no_data) |
| 30 | `LC_HOLD_OPEN` | 锂(LC) | `li_p1_ts_02` | 持仓量 | `li_21_openinterest` | Mapped metric not found in database (gap: no_data) |
| 31 | `LC_LONG_SHORT_RATIO` | 锂(LC) | `li_p1_gauge_01` | 多空持仓比 | `li_21_openinterest_longshort` | Mapped metric not found in database (gap: no_data) |
| 32 | `LC_MONTH_SPREAD` | 锂(LC) | `li_p4_ts_01` | 月差 | `li_24_close_near` | Mapped metric not found in database (gap: no_data) |
| 33 | `LC_SMELTING_PROFIT` | 锂(LC) | `li_p5_ts_01` | 冶炼利润 | `li_25_profit` | Mapped metric not found in database (gap: no_data) |
| 34 | `LC_SPOT_PREMIUM` | 锂(LC) | `li_p2_ts_01` | 现货升贴水 | `li_21_premium` | Mapped metric not found in database (gap: no_data) |
| 35 | `LC_TOP20_LONG` | 锂(LC) | `li_p6_bar_01` | 多头前20 | `li_26_openinterest_top20` | Mapped metric not found in database (gap: no_data) |
| 36 | `LC_TOP20_SHORT` | 锂(LC) | `li_p6_bar_01` | 空头前20 | `li_26_openinterest_top20_2` | Mapped metric not found in database (gap: no_data) |
| 37 | `LME_AL` | 铝(AL) | `al_p3_ts_01` | LME铝 | `al_00_lme_close` | Mapped metric not found in database (gap: no_data) |
| 38 | `LME_CU` | 铜(CU) | `cu_p3_ts_01` | LME铜 | `cu_23_lme_close` | Mapped metric not found in database (gap: no_data) |
| 39 | `LME_LC` | 锂(LC) | `li_p3_ts_01` | LME锂 | `li_21_close` | Mapped metric not found in database (gap: no_data) |
| 40 | `LME_NI` | 镍(NI) | `ni_p3_ts_01` | LME镍 | `ni_21_lme_price` | Mapped metric not found in database (gap: no_data) |
| 41 | `LME_PB` | 铅(PB) | `pb_p3_ts_01` | LME铅 | `j23_lme_cash` | Mapped metric not found in database (gap: no_data) |
| 42 | `LME_SI` | 硅(SI) | `si_p3_ts_01` | LME硅 | `si_25_close_front_polysilicon` | Mapped metric not found in database (gap: no_data) |
| 43 | `LME_SN` | 锡(SN) | `sn_p3_ts_01` | LME锡 | `sn_23_lme_close` | Mapped metric not found in database (gap: no_data) |
| 44 | `LME_ZN` | 锌(ZN) | `zn_p3_ts_01` | LME锌 | `zn_23_lme_close` | Mapped metric not found in database (gap: no_data) |
| 45 | `NI_BASIS` | 镍(NI) | `ni_p2_ts_02` | 基差 | `ni_22_basis` | Mapped metric not found in database (gap: no_data) |
| 46 | `NI_FU00014982` | 镍(NI) | `ni_p1_ts_01` | 主连 | `ni_21_close_front` | Mapped metric not found in database (gap: no_data) |
| 47 | `NI_HOLD_OPEN` | 镍(NI) | `ni_p1_ts_02` | 持仓量 | `ni_21_openinterest_front` | Mapped metric not found in database (gap: no_data) |
| 48 | `NI_LONG_SHORT_RATIO` | 镍(NI) | `ni_p1_gauge_01` | 多空持仓比 | `ni_21_percentile_openinterest` | Mapped metric not found in database (gap: no_data) |
| 49 | `NI_MONTH_SPREAD` | 镍(NI) | `ni_p4_ts_01` | 月差 | `ni_24_near_price` | Mapped metric not found in database (gap: no_data) |
| 50 | `NI_PRICE_PERCENTILE` | 镍(NI) | `ni_p5_gauge_01` | 价格分位数 | `ni_25_percentile_price` | Mapped metric not found in database (gap: no_data) |
| 51 | `NI_SMELTING_PROFIT` | 镍(NI) | `ni_p5_ts_01` | 冶炼利润 | `ni_25_profit` | Mapped metric not found in database (gap: no_data) |
| 52 | `NI_SPOT_PREMIUM` | 镍(NI) | `ni_p2_ts_01` | 现货升贴水 | `ni_21_premium` | Mapped metric not found in database (gap: no_data) |
| 53 | `NI_TOP20_LONG` | 镍(NI) | `ni_p6_bar_01` | 多头前20 | `ni_26_openinterest_top20_front` | Mapped metric not found in database (gap: no_data) |
| 54 | `NI_TOP20_SHORT` | 镍(NI) | `ni_p6_bar_01` | 空头前20 | `ni_26_openinterest_top20_front_2` | Mapped metric not found in database (gap: no_data) |
| 55 | `PB_BASIS` | 铅(PB) | `pb_p2_ts_02` | 基差 | `j22_premium` | Mapped metric not found in database (gap: no_data) |
| 56 | `PB_FU00014946` | 铅(PB) | `pb_p1_ts_01` | 主连 | `j21_close` | Mapped metric not found in database (gap: no_data) |
| 57 | `PB_HOLD_OPEN` | 铅(PB) | `pb_p1_ts_02` | 持仓量 | `j21_oi` | Mapped metric not found in database (gap: no_data) |
| 58 | `PB_MONTH_SPREAD` | 铅(PB) | `pb_p4_ts_01` | 月差 | `j24_spread_m` | Mapped metric not found in database (gap: no_data) |
| 59 | `PB_SMELTING_PROFIT` | 铅(PB) | `pb_p5_ts_01` | 冶炼利润 | `j25_smelt_cost` | Mapped metric not found in database (gap: no_data) |
| 60 | `PB_SPOT_PREMIUM` | 铅(PB) | `pb_p2_ts_01` | 现货升贴水 | `j22_spot` | Mapped metric not found in database (gap: no_data) |
| 61 | `PB_TERM_STRUCTURE` | 铅(PB) | `pb_p4_ts_02` | 期限结构 | `j24_spread_s` | Mapped metric not found in database (gap: no_data) |
| 62 | `SI_BASIS` | 硅(SI) | `si_p2_ts_02` | 基差 | `si_21_basis_industrial_si` | Mapped metric not found in database (gap: no_data) |
| 63 | `SI_FU00015015` | 硅(SI) | `si_p1_ts_01` | 主连 | `si_21_close_front_industrial_si` | Mapped metric not found in database (gap: no_data) |
| 64 | `SI_HOLD_OPEN` | 硅(SI) | `si_p1_ts_02` | 持仓量 | `si_21_openinterest` | Mapped metric not found in database (gap: no_data) |
| 65 | `SI_LONG_SHORT_RATIO` | 硅(SI) | `si_p1_gauge_01` | 多空持仓比 | `si_21_openinterest_longshort_indus` | Mapped metric not found in database (gap: no_data) |
| 66 | `SI_MONTH_SPREAD` | 硅(SI) | `si_p4_ts_01` | 月差 | `si_23_close` | Mapped metric not found in database (gap: no_data) |
| 67 | `SI_PRICE_PERCENTILE` | 硅(SI) | `si_p5_gauge_01` | 价格分位数 | `si_25_profit_percentile_industrial` | Mapped metric not found in database (gap: no_data) |
| 68 | `SI_SMELTING_PROFIT` | 硅(SI) | `si_p5_ts_01` | 冶炼利润 | `si_25_profit` | Mapped metric not found in database (gap: no_data) |
| 69 | `SI_SPOT_PREMIUM` | 硅(SI) | `si_p2_ts_01` | 现货升贴水 | `si_21_warrant_industrial_si` | Mapped metric not found in database (gap: no_data) |
| 70 | `SN_BASIS` | 锡(SN) | `sn_p2_ts_02` | 基差 | `sn_21_basis` | Mapped metric not found in database (gap: no_data) |
| 71 | `SN_FU00014952` | 锡(SN) | `sn_p1_ts_01` | 主连 | `sn_21_close_front` | Mapped metric not found in database (gap: no_data) |
| 72 | `SN_HOLD_OPEN` | 锡(SN) | `sn_p1_ts_02` | 持仓量 | `sn_21_openinterest` | Mapped metric not found in database (gap: no_data) |
| 73 | `SN_LONG_SHORT_RATIO` | 锡(SN) | `sn_p1_gauge_01` | 多空持仓比 | `sn_21_openinterest_3` | Mapped metric not found in database (gap: no_data) |
| 74 | `SN_MONTH_SPREAD` | 锡(SN) | `sn_p4_ts_01` | 月差 | `sn_22_premium` | Mapped metric not found in database (gap: no_data) |
| 75 | `SN_PRICE_PERCENTILE` | 锡(SN) | `sn_p5_gauge_01` | 价格分位数 | `sn_71_cost_percentile` | Mapped metric not found in database (gap: no_data) |
| 76 | `SN_SMELTING_PROFIT` | 锡(SN) | `sn_p5_ts_01` | 冶炼利润 | `sn_72_tc` | Mapped metric not found in database (gap: no_data) |
| 77 | `SN_SPOT_PREMIUM` | 锡(SN) | `sn_p2_ts_01` | 现货升贴水 | `sn_21_premium` | Mapped metric not found in database (gap: no_data) |
| 78 | `SN_TOP20_LONG` | 锡(SN) | `sn_p6_bar_01` | 多头前20 | `sn_26_openinterest_top20` | Mapped metric not found in database (gap: no_data) |
| 79 | `SN_TOP20_SHORT` | 锡(SN) | `sn_p6_bar_01` | 空头前20 | `sn_26_openinterest_top20_2` | Mapped metric not found in database (gap: no_data) |
| 80 | `SPOT_IS` | 硅(SI) | `si_p3_ts_02` | 工业硅现货 | `si_24_spot` | Mapped metric not found in database (gap: no_data) |
| 81 | `SPOT_LICAR` | 锂(LC) | `li_p3_ts_02` | 碳酸锂现货 | `li_22_premium` | Mapped metric not found in database (gap: no_data) |
| 82 | `ZN_BASIS` | 锌(ZN) | `zn_p2_ts_02` | 基差 | `zn_21_basis` | Mapped metric not found in database (gap: no_data) |
| 83 | `ZN_FU00014950` | 锌(ZN) | `zn_p1_ts_01` | 主连 | `zn_21_close_front` | Mapped metric not found in database (gap: no_data) |
| 84 | `ZN_HOLD_OPEN` | 锌(ZN) | `zn_p1_ts_02` | 持仓量 | `zn_21_openinterest` | Mapped metric not found in database (gap: no_data) |
| 85 | `ZN_LONG_SHORT_RATIO` | 锌(ZN) | `zn_p1_gauge_01` | 多空持仓比 | `zn_21_openinterest_2` | Mapped metric not found in database (gap: no_data) |
| 86 | `ZN_MONTH_SPREAD` | 锌(ZN) | `zn_p4_ts_01` | 月差 | `zn_24_term_struct` | Mapped metric not found in database (gap: no_data) |
| 87 | `ZN_PRICE_PERCENTILE` | 锌(ZN) | `zn_p5_gauge_01` | 价格分位数 | `zn_25_profit_percentile` | Mapped metric not found in database (gap: no_data) |
| 88 | `ZN_SMELTING_PROFIT` | 锌(ZN) | `zn_p5_ts_01` | 冶炼利润 | `zn_25_profit` | Mapped metric not found in database (gap: no_data) |
| 89 | `ZN_SPOT_PREMIUM` | 锌(ZN) | `zn_p2_ts_01` | 现货升贴水 | `zn_21_premium` | Mapped metric not found in database (gap: no_data) |
| 90 | `ZN_TOP20_LONG` | 锌(ZN) | `zn_p6_bar_01` | 多头前20 | `zn_26_openinterest_top20` | Mapped metric not found in database (gap: no_data) |
| 91 | `ZN_TOP20_SHORT` | 锌(ZN) | `zn_p6_bar_01` | 空头前20 | `zn_26_openinterest` | Mapped metric not found in database (gap: no_data) |

### 3.3 Simulated Only (Entry exists but no real points)

No items in this category. [OK]

### 3.4 Other Gaps

No items in this category. [OK]

## 5. Recommendations

1. Overall coverage (0.0%) is below P0 gate threshold (60%). Need to import 109 more indicators to reach gate.
2. 18 indicators have no DSHB metric mapping. Update INDICATOR_MAPPING in cache_coverage_calc.py to add mappings.
3. 91 mapped indicators are missing from api_cache.db. Run refresh_cache.py or db_import_jsonl.py to import data.

## 6. Gate Decision

| Gate Phase | Threshold | Actual | Status |
|------------|-----------|--------|--------|
| P0 | 60% | 0.00% | **FAIL** |

> **[FAIL] D7 Gate Decision: FAIL**
>
> Coverage rate 0.0% is below the P0 threshold of 60%.
> Need to cover at least 65 indicators to pass.
> Currently 109 indicators are uncovered.
>
> **Required actions**:
> 1. Run `refresh_cache.py` to import missing real data into api_cache.db
> 2. Update INDICATOR_MAPPING for 18 unmapped indicators

---
*Generated by cache_coverage_calc.py · 2026-10-15T11:21:27.246739*
