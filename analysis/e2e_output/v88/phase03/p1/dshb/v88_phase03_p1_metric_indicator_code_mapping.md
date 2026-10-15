# V88 Phase03 P1 — Metric/Indicator/Code Complete Mapping List

> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1
> **生成时间**: 2026-10-15T15:51:07.950515
> **数据库**: `analysis\e2e_output\v88\phase03\p0\phase03_test.db`
> **目的**: Complete export of all indicator_id / indicator_id_mapped / commodity mappings

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Total unique indicators | 674 |
| Real indicators | 615 |
| Derived indicators | 59 |
| Mapped indicators | 667 (99.0%) |
| Unmapped indicators | 7 (1.0%) |
| Distinct mapped IDs (DSHE meta_chart) | 197 |
| P0-9 denominator (restored) | 109 |
| P0-9 numerator | 109 |
| P0-9 coverage | **100.00%** |

## 2. Per-Commodity Mapping Coverage

| Commodity | Total | Real | Derived | Mapped | Unmapped | Coverage % |
|-----------|------:|-----:|--------:|-------:|---------:|-----------:|
| al       |    16 |   10 |       6 |     16 |        0 |     100.0% |
| cu       |    28 |   18 |      10 |     28 |        0 |     100.0% |
| j21      |     7 |    2 |       5 |      7 |        0 |     100.0% |
| j22      |     2 |    2 |       0 |      2 |        0 |     100.0% |
| j23      |     1 |    1 |       0 |      1 |        0 |     100.0% |
| j24      |     2 |    2 |       0 |      2 |        0 |     100.0% |
| j25      |     1 |    1 |       0 |      1 |        0 |     100.0% |
| li       |    83 |   74 |       9 |     82 |        1 |      98.8% |
| ni       |   163 |  156 |       7 |    161 |        2 |      98.8% |
| si       |   131 |  124 |       7 |    129 |        2 |      98.5% |
| sn       |   122 |  116 |       6 |    121 |        1 |      99.2% |
| zn       |   118 |  109 |       9 |    117 |        1 |      99.2% |

## 3. Derived Indicators (59 R-V88-033)

> 59 derived indicators computed from base data.

| # | indicator_id | indicator_id_mapped | commodity | records |
|---|-------------|--------------------|-----------|--------:|
| 1 | `al_inv_change` | `AL_INV_CHANGE` | al | 3,040 |
| 2 | `al_long_short_ratio` | `AL_LONG_SHORT_RATIO` | al | 3,041 |
| 3 | `al_month_spread` | `AL_MONTH_SPREAD` | al | 3,040 |
| 4 | `al_premium_change` | `AL_PREMIUM_CHANGE` | al | 3,040 |
| 5 | `al_price_percentile` | `AL_PRICE_PERCENTILE` | al | 3,022 |
| 6 | `al_term_structure` | `AL_TERM_STRUCTURE` | al | 3,041 |
| 7 | `comex_cu_change` | `COMEX_CU_CHANGE` | cu | 3,040 |
| 8 | `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | cu | 3,041 |
| 9 | `cu_inv_change` | `CU_INV_CHANGE` | cu | 3,040 |
| 10 | `cu_long_short_ratio` | `CU_LONG_SHORT_RATIO` | cu | 3,041 |
| 11 | `cu_month_spread` | `CU_MONTH_SPREAD` | cu | 3,040 |
| 12 | `cu_oi_percentile` | `CU_OI_PERCENTILE` | cu | 3,022 |
| 13 | `cu_premium_change` | `CU_PREMIUM_CHANGE` | cu | 3,040 |
| 14 | `cu_price_percentile` | `CU_PRICE_PERCENTILE` | cu | 3,022 |
| 15 | `cu_term_structure` | `CU_TERM_STRUCTURE` | cu | 3,041 |
| 16 | `cu_top20_net` | `CU_TOP20_NET` | cu | 3,041 |
| 17 | `pb_long_short_ratio` | `PB_LONG_SHORT_RATIO` | j21 | 3,041 |
| 18 | `pb_month_spread` | `PB_MONTH_SPREAD` | j21 | 3,040 |
| 19 | `pb_price_percentile` | `PB_PRICE_PERCENTILE` | j21 | 3,022 |
| 20 | `pb_term_structure` | `PB_TERM_STRUCTURE` | j21 | 3,041 |
| 21 | `pb_top20_net` | `PB_TOP20_NET` | j21 | 3,041 |
| 22 | `lc_top20_net` | `LC_TOP20_NET` | li | 754 |
| 23 | `li_basis_change` | `LC_BASIS_CHANGE` | li | 753 |
| 24 | `li_inv_change` | `LI_INV_CHANGE` | li | 17 |
| 25 | `li_long_short_ratio` | `LC_LONG_SHORT_RATIO` | li | 754 |
| 26 | `li_month_spread` | `LC_MONTH_SPREAD` | li | 436 |
| 27 | `li_oi_percentile` | `LI_OI_PERCENTILE` | li | 735 |
| 28 | `li_price_percentile` | `LC_PRICE_PERCENTILE` | li | 735 |
| 29 | `li_term_structure` | `LC_TERM_STRUCTURE` | li | 754 |
| 30 | `spot_licar_change` | `SPOT_LICAR_CHANGE` | li | 438 |
| 31 | `ni_basis_change` | `NI_BASIS_CHANGE` | ni | 2,777 |
| 32 | `ni_inv_change` | `NI_INV_CHANGE` | ni | 499 |
| 33 | `ni_long_short_ratio` | `NI_LONG_SHORT_RATIO` | ni | 346 |
| 34 | `ni_month_spread` | `NI_MONTH_SPREAD` | ni | 1,659 |
| 35 | `ni_price_percentile` | `NI_PRICE_PERCENTILE` | ni | 2,760 |
| 36 | `ni_term_structure` | `NI_TERM_STRUCTURE` | ni | 1,659 |
| 37 | `ni_top20_net` | `NI_TOP20_NET` | ni | 2,779 |
| 38 | `si_inventory_days` | `SI_INV_DAYS` | si | 133 |
| 39 | `si_long_short_ratio` | `SI_LONG_SHORT_RATIO` | si | 893 |
| 40 | `si_month_spread` | `SI_MONTH_SPREAD` | si | 893 |
| 41 | `si_price_percentile` | `SI_PRICE_PERCENTILE` | si | 874 |
| 42 | `si_term_structure` | `SI_TERM_STRUCTURE` | si | 893 |
| 43 | `si_top20_net` | `SI_TOP20_NET` | si | 893 |
| 44 | `spot_is_change` | `SPOT_IS_CHANGE` | si | 773 |
| 45 | `sn_inventory_days` | `SN_INV_DAYS` | sn | 2,496 |
| 46 | `sn_long_short_ratio` | `SN_LONG_SHORT_RATIO` | sn | 345 |
| 47 | `sn_month_spread` | `SN_MONTH_SPREAD` | sn | 1,537 |
| 48 | `sn_price_percentile` | `SN_PRICE_PERCENTILE` | sn | 2,760 |
| 49 | `sn_term_structure` | `SN_TERM_STRUCTURE` | sn | 1,535 |
| 50 | `sn_top20_net` | `SN_TOP20_NET` | sn | 2,779 |
| 51 | `comex_zn_change` | `COMEX_ZN_CHANGE` | zn | 2,832 |
| 52 | `comex_zn_lme_spread` | `COMEX_ZN_LME_SPREAD` | zn | 1,051 |
| 53 | `zn_basis_change` | `ZN_BASIS_CHANGE` | zn | 2,833 |
| 54 | `zn_inv_change` | `ZN_INV_CHANGE` | zn | 516 |
| 55 | `zn_long_short_ratio` | `ZN_LONG_SHORT_RATIO` | zn | 345 |
| 56 | `zn_month_spread` | `ZN_MONTH_SPREAD` | zn | 2,832 |
| 57 | `zn_oi_percentile` | `ZN_OI_PERCENTILE` | zn | 326 |
| 58 | `zn_price_percentile` | `ZN_PRICE_PERCENTILE` | zn | 2,814 |
| 59 | `zn_term_structure` | `ZN_TERM_STRUCTURE` | zn | 2,833 |

## 4. Complete Mapping Table (Top 100)

> 674 rows total. Showing first 100 sorted by commodity, then indicator_id.

| # | indicator_id | indicator_id_mapped | commodity | source | records |
|---|-------------|--------------------|-----------|--------|--------:|
| 1 | `al_00_basis` | `AL_BASIS` | al | real | 3,041 |
| 2 | `al_00_close_front` | `AL_FU00014934` | al | real | 3,041 |
| 3 | `al_00_cost_percentile` | `AL_PRICE_PERCENTILE` | al | real | 3,041 |
| 4 | `al_00_lme_close` | `LME_AL` | al | real | 3,041 |
| 5 | `al_00_openinterest_front` | `AL_HOLD_OPEN` | al | real | 3,041 |
| 6 | `al_00_premium` | `AL_SPOT_PREMIUM` | al | real | 3,041 |
| 7 | `al_24_lme_spread` | `AL_MONTH_SPREAD` | al | real | 3,041 |
| 8 | `al_25_profit` | `AL_SMELTING_PROFIT` | al | real | 3,041 |
| 9 | `al_26_long_top20` | `AL_TOP20_LONG` | al | real | 3,041 |
| 10 | `al_26_short_top20` | `AL_TOP20_SHORT` | al | real | 3,041 |
| 11 | `al_inv_change` | `AL_INV_CHANGE` | al | derived | 3,040 |
| 12 | `al_long_short_ratio` | `AL_LONG_SHORT_RATIO` | al | derived | 3,041 |
| 13 | `al_month_spread` | `AL_MONTH_SPREAD` | al | derived | 3,040 |
| 14 | `al_premium_change` | `AL_PREMIUM_CHANGE` | al | derived | 3,040 |
| 15 | `al_price_percentile` | `AL_PRICE_PERCENTILE` | al | derived | 3,022 |
| 16 | `al_term_structure` | `AL_TERM_STRUCTURE` | al | derived | 3,041 |
| 17 | `comex_cu_change` | `COMEX_CU_CHANGE` | cu | derived | 3,040 |
| 18 | `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | cu | derived | 3,041 |
| 19 | `cu_21_basis` | `CU_BASIS` | cu | real | 3,041 |
| 20 | `cu_21_close_front` | `CU_FU00014941` | cu | real | 3,041 |
| 21 | `cu_21_openinterest` | `CU_HOLD_OPEN` | cu | real | 3,041 |
| 22 | `cu_21_openinterest_longshort` | `CU_LONG_SHORT_RATIO` | cu | real | 3,041 |
| 23 | `cu_22_premium` | `CU_SPOT_PREMIUM` | cu | real | 3,041 |
| 24 | `cu_23_comex_close` | `COMEX_CU` | cu | real | 3,041 |
| 25 | `cu_23_inv` | `FU00014813` | cu | real | 3,041 |
| 26 | `cu_23_lme_close` | `LME_CU` | cu | real | 3,041 |
| 27 | `cu_24_openinterest_volume` | `CU_MONTH_SPREAD` | cu | real | 3,041 |
| 28 | `cu_25_profit` | `CU_SMELTING_PROFIT` | cu | real | 3,041 |
| 29 | `cu_25_profit_percentile` | `CU_PRICE_PERCENTILE` | cu | real | 3,041 |
| 30 | `cu_25_tc_conc` | `CU_COST_PERCENTILE` | cu | real | 3,041 |
| 31 | `cu_26_openinterest` | `CU_TOP20_SHORT` | cu | real | 3,041 |
| 32 | `cu_26_openinterest_top20_front` | `CU_TOP20_LONG` | cu | real | 3,041 |
| 33 | `cu_321_util_capacity_util` | `CU_UTILIZATION` | cu | real | 3,041 |
| 34 | `cu_41_output` | `CU_FU00014935` | cu | real | 3,041 |
| 35 | `cu_42_warrant_reg` | `CU_WARRANT_INVENTORY` | cu | real | 3,041 |
| 36 | `cu_43_social_stock` | `CU_SOCIAL_INV` | cu | real | 3,041 |
| 37 | `cu_inv_change` | `CU_INV_CHANGE` | cu | derived | 3,040 |
| 38 | `cu_long_short_ratio` | `CU_LONG_SHORT_RATIO` | cu | derived | 3,041 |
| 39 | `cu_month_spread` | `CU_MONTH_SPREAD` | cu | derived | 3,040 |
| 40 | `cu_oi_percentile` | `CU_OI_PERCENTILE` | cu | derived | 3,022 |
| 41 | `cu_premium_change` | `CU_PREMIUM_CHANGE` | cu | derived | 3,040 |
| 42 | `cu_price_percentile` | `CU_PRICE_PERCENTILE` | cu | derived | 3,022 |
| 43 | `cu_term_structure` | `CU_TERM_STRUCTURE` | cu | derived | 3,041 |
| 44 | `cu_top20_net` | `CU_TOP20_NET` | cu | derived | 3,041 |
| 45 | `j21_close` | `PB_FU00014946` | j21 | real | 3,041 |
| 46 | `j21_oi` | `PB_HOLD_OPEN` | j21 | real | 3,041 |
| 47 | `pb_long_short_ratio` | `PB_LONG_SHORT_RATIO` | j21 | derived | 3,041 |
| 48 | `pb_month_spread` | `PB_MONTH_SPREAD` | j21 | derived | 3,040 |
| 49 | `pb_price_percentile` | `PB_PRICE_PERCENTILE` | j21 | derived | 3,022 |
| 50 | `pb_term_structure` | `PB_TERM_STRUCTURE` | j21 | derived | 3,041 |
| 51 | `pb_top20_net` | `PB_TOP20_NET` | j21 | derived | 3,041 |
| 52 | `j22_premium` | `PB_BASIS` | j22 | real | 3,041 |
| 53 | `j22_spot` | `PB_SPOT_PREMIUM` | j22 | real | 3,041 |
| 54 | `j23_lme_cash` | `LME_PB` | j23 | real | 3,041 |
| 55 | `j24_spread_m` | `PB_MONTH_SPREAD` | j24 | real | 3,041 |
| 56 | `j24_spread_s` | `PB_TERM_STRUCTURE` | j24 | real | 3,041 |
| 57 | `j25_smelt_cost` | `PB_SMELTING_PROFIT` | j25 | real | 3,041 |
| 58 | `lc_top20_net` | `LC_TOP20_NET` | li | derived | 754 |
| 59 | `li_21_basis` | `LC_BASIS` | li | real | 754 |
| 60 | `li_21_close` | `LME_LC` | li | real | 754 |
| 61 | `li_21_close_2` | `LI_FU00015030` | li | real | 754 |
| 62 | `li_21_openinterest_2` | `LI_HOLD_OPEN` | li | real | 754 |
| 63 | `li_21_openinterest_3` | `LI_HOLD_OPEN` | li | real | 754 |
| 64 | `li_21_openinterest_longshort` | `LC_LONG_SHORT_RATIO` | li | real | 754 |
| 65 | `li_21_premium` | `LC_SPOT_PREMIUM` | li | real | 439 |
| 66 | `li_21_volume` | `(unmapped)` | li | real | 754 |
| 67 | `li_21_warrant` | `LI_WARRANT` | li | real | 662 |
| 68 | `li_22_basis_carbonate_battery` | `LI_BASIS` | li | real | 754 |
| 69 | `li_22_premium` | `SPOT_LICAR` | li | real | 439 |
| 70 | `li_22_premium_2` | `LI_SPOT_PREMIUM` | li | real | 439 |
| 71 | `li_22_premium_carbonate_battery` | `LI_SPOT_PREMIUM` | li | real | 439 |
| 72 | `li_22_premium_ratio_carbonate` | `LI_SPOT_PREMIUM` | li | real | 439 |
| 73 | `li_22_premium_ratio_carbonate_2` | `LI_SPOT_PREMIUM` | li | real | 439 |
| 74 | `li_25_profit` | `LC_SMELTING_PROFIT` | li | real | 891 |
| 75 | `li_25_profit_2` | `LI_SMELTING_PROFIT` | li | real | 660 |
| 76 | `li_25_profit_3` | `LI_SMELTING_PROFIT` | li | real | 660 |
| 77 | `li_25_profit_4` | `LI_SMELTING_PROFIT` | li | real | 660 |
| 78 | `li_25_profit_carbonate` | `LI_SMELTING_PROFIT` | li | real | 891 |
| 79 | `li_26_openinterest_longshort` | `LI_LONG_SHORT_RATIO` | li | real | 754 |
| 80 | `li_26_openinterest_longshort_2` | `LI_LONG_SHORT_RATIO` | li | real | 754 |
| 81 | `li_26_openinterest_top20` | `LC_TOP20_LONG` | li | real | 754 |
| 82 | `li_26_openinterest_top20_2` | `LC_TOP20_SHORT` | li | real | 754 |
| 83 | `li_26_openinterest_top20_3` | `LI_TOP20_LONG` | li | real | 754 |
| 84 | `li_26_openinterest_top20_4` | `LI_TOP20_LONG` | li | real | 754 |
| 85 | `li_311_capacity` | `LI_REFINING_CAPACITY` | li | real | 31 |
| 86 | `li_311_capacity_util` | `LI_UTILIZATION` | li | real | 31 |
| 87 | `li_311_output` | `LI_REFINING_OUTPUT` | li | real | 11 |
| 88 | `li_311_output_2` | `LI_REFINING_OUTPUT` | li | real | 55 |
| 89 | `li_312_inv` | `LI_SHFE_INV` | li | real | 68 |
| 90 | `li_312_output` | `LI_REFINING_OUTPUT` | li | real | 11 |
| 91 | `li_312_output_2` | `LI_REFINING_OUTPUT` | li | real | 11 |
| 92 | `li_313_output` | `LI_REFINING_OUTPUT` | li | real | 31 |
| 93 | `li_313_output_2` | `LI_REFINING_OUTPUT` | li | real | 45 |
| 94 | `li_313_output_3` | `LI_REFINING_OUTPUT` | li | real | 31 |
| 95 | `li_314_import` | `LI_IMPORT` | li | real | 19 |
| 96 | `li_314_import_2` | `LI_IMPORT` | li | real | 16 |
| 97 | `li_314_import_3` | `LI_IMPORT` | li | real | 16 |
| 98 | `li_314_import_4` | `LI_IMPORT` | li | real | 16 |
| 99 | `li_321_output` | `LI_REFINING_OUTPUT` | li | real | 103 |
| 100 | `li_321_output_2` | `LI_REFINING_OUTPUT` | li | real | 31 |

## 5. Unmapped Indicators

> 7 indicators have no mapping.

| # | indicator_id | commodity | source | records |
|---|-------------|-----------|--------|--------:|
| 1 | `li_21_volume` | li | real | 754 |
| 2 | `ni_21_volume_front` | ni | real | 2,779 |
| 3 | `ni_21_volume_top20` | ni | real | 2,934 |
| 4 | `si_21_volume_industrial_si` | si | real | 893 |
| 5 | `si_26_volume_industrial_si` | si | real | 893 |
| 6 | `sn_21_volume` | sn | real | 2,779 |
| 7 | `zn_21_volume` | zn | real | 1,128 |

## 6. P0-9 Coverage Report

| 口径 | 分子 | 分母 | 比率 | 状态 |
|------|:----:|:----:|:----:|:----:|
| DB映射命中率 (P0-9) | 109 | 109 | **100.00%** | PASS |
| DSHE指标数 | 197 | - | - | - |
| 总指标数 | 674 | - | - | - |
| 派生指标数 | 59 | - | - | - |

---
*Generated by export_mapping_list.py | 2026-10-15T15:51:07.950515*