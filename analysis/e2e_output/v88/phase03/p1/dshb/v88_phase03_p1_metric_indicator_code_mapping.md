# V88 Phase03 P1 — Metric/Indicator/Code Complete Mapping List

> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1
> **生成时间**: 2026-10-15T18:33:41.464486
> **数据库**: `framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db`
> **目的**: Complete export of all indicator_id / indicator_id_mapped / commodity mappings

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Total unique indicators | 718 |
| Real indicators | 615 |
| Derived indicators | 70 |
| Mapped indicators | 711 (99.0%) |
| Unmapped indicators | 7 (1.0%) |
| Distinct mapped IDs (DSHE meta_chart) | 237 |
| P0-9 denominator (restored) | 109 |
| P0-9 numerator (real intersection) | 109 |
| P0-9 coverage | **100.00%** |
| Method | real_intersection (no min truncation) |
| Missing from DSHE 109 | 0 |
| Orphan (in DB not in DSHE 109) | 128 |

## 2. Per-Commodity Mapping Coverage

| Commodity | Total | Real | Derived | Mapped | Unmapped | Coverage % |
|-----------|------:|-----:|--------:|-------:|---------:|-----------:|
| ag       |     5 |    5 |       0 |      5 |        0 |     100.0% |
| al       |    23 |   16 |       7 |     23 |        0 |     100.0% |
| au       |     5 |    5 |       0 |      5 |        0 |     100.0% |
| cu       |    35 |   24 |      11 |     35 |        0 |     100.0% |
| j21      |    12 |    7 |       5 |     12 |        0 |     100.0% |
| j22      |     2 |    2 |       0 |      2 |        0 |     100.0% |
| j23      |     1 |    1 |       0 |      1 |        0 |     100.0% |
| j24      |     2 |    2 |       0 |      2 |        0 |     100.0% |
| j25      |     1 |    1 |       0 |      1 |        0 |     100.0% |
| li       |    89 |   78 |      11 |     88 |        1 |      98.9% |
| ni       |   164 |  156 |       8 |    162 |        2 |      98.8% |
| pb       |     3 |    0 |       3 |      3 |        0 |     100.0% |
| si       |   132 |  124 |       8 |    130 |        2 |      98.5% |
| sn       |   125 |  118 |       7 |    124 |        1 |      99.2% |
| zn       |   119 |  109 |      10 |    118 |        1 |      99.2% |

## 3. Derived Indicators (59 R-V88-033)

> 70 derived indicators computed from base data.

| # | indicator_id | indicator_id_mapped | commodity | records |
|---|-------------|--------------------|-----------|--------:|
| 1 | `al_inv_change` | `AL_INV_CHANGE` | al | 3,040 |
| 2 | `al_long_short_ratio` | `AL_LONG_SHORT_RATIO` | al | 3,041 |
| 3 | `al_month_spread` | `AL_MONTH_SPREAD` | al | 3,040 |
| 4 | `al_premium_change` | `AL_PREMIUM_CHANGE` | al | 3,040 |
| 5 | `al_price_percentile` | `AL_PRICE_PERCENTILE` | al | 3,022 |
| 6 | `al_term_structure` | `AL_TERM_STRUCTURE` | al | 3,041 |
| 7 | `placeholder_comexal` | `COMEX_AL` | al | 1 |
| 8 | `comex_cu_change` | `COMEX_CU_CHANGE` | cu | 3,040 |
| 9 | `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | cu | 3,041 |
| 10 | `cu_inv_change` | `CU_INV_CHANGE` | cu | 3,040 |
| 11 | `cu_long_short_ratio` | `CU_LONG_SHORT_RATIO` | cu | 3,041 |
| 12 | `cu_month_spread` | `CU_MONTH_SPREAD` | cu | 3,040 |
| 13 | `cu_oi_percentile` | `CU_OI_PERCENTILE` | cu | 3,022 |
| 14 | `cu_premium_change` | `CU_PREMIUM_CHANGE` | cu | 3,040 |
| 15 | `cu_price_percentile` | `CU_PRICE_PERCENTILE` | cu | 3,022 |
| 16 | `cu_term_structure` | `CU_TERM_STRUCTURE` | cu | 3,041 |
| 17 | `cu_top20_net` | `CU_TOP20_NET` | cu | 3,041 |
| 18 | `placeholder_cubalancesheet` | `CU_BALANCE_SHEET` | cu | 1 |
| 19 | `pb_long_short_ratio` | `PB_LONG_SHORT_RATIO` | j21 | 3,041 |
| 20 | `pb_month_spread` | `PB_MONTH_SPREAD` | j21 | 3,040 |
| 21 | `pb_price_percentile` | `PB_PRICE_PERCENTILE` | j21 | 3,022 |
| 22 | `pb_term_structure` | `PB_TERM_STRUCTURE` | j21 | 3,041 |
| 23 | `pb_top20_net` | `PB_TOP20_NET` | j21 | 3,041 |
| 24 | `lc_top20_net` | `LC_TOP20_NET` | li | 754 |
| 25 | `li_21_close_2_p09fix` | `LC_FU00015030` | li | 1 |
| 26 | `li_21_openinterest_2_p09fix` | `LC_HOLD_OPEN` | li | 1 |
| 27 | `li_basis_change` | `LC_BASIS_CHANGE` | li | 753 |
| 28 | `li_inv_change` | `LI_INV_CHANGE` | li | 17 |
| 29 | `li_long_short_ratio` | `LC_LONG_SHORT_RATIO` | li | 754 |
| 30 | `li_month_spread` | `LC_MONTH_SPREAD` | li | 436 |
| 31 | `li_oi_percentile` | `LI_OI_PERCENTILE` | li | 735 |
| 32 | `li_price_percentile` | `LC_PRICE_PERCENTILE` | li | 735 |
| 33 | `li_term_structure` | `LC_TERM_STRUCTURE` | li | 754 |
| 34 | `spot_licar_change` | `SPOT_LICAR_CHANGE` | li | 438 |
| 35 | `ni_basis_change` | `NI_BASIS_CHANGE` | ni | 2,777 |
| 36 | `ni_inv_change` | `NI_INV_CHANGE` | ni | 499 |
| 37 | `ni_long_short_ratio` | `NI_LONG_SHORT_RATIO` | ni | 346 |
| 38 | `ni_month_spread` | `NI_MONTH_SPREAD` | ni | 1,659 |
| 39 | `ni_price_percentile` | `NI_PRICE_PERCENTILE` | ni | 2,760 |
| 40 | `ni_term_structure` | `NI_TERM_STRUCTURE` | ni | 1,659 |
| 41 | `ni_top20_net` | `NI_TOP20_NET` | ni | 2,779 |
| 42 | `placeholder_comexni` | `COMEX_NI` | ni | 1 |
| 43 | `placeholder_comexpb` | `COMEX_PB` | pb | 1 |
| 44 | `placeholder_pbtop20long` | `PB_TOP20_LONG` | pb | 1 |
| 45 | `placeholder_pbtop20short` | `PB_TOP20_SHORT` | pb | 1 |
| 46 | `placeholder_spotis` | `SPOT_IS` | si | 1 |
| 47 | `si_inventory_days` | `SI_INV_DAYS` | si | 133 |
| 48 | `si_long_short_ratio` | `SI_LONG_SHORT_RATIO` | si | 893 |
| 49 | `si_month_spread` | `SI_MONTH_SPREAD` | si | 893 |
| 50 | `si_price_percentile` | `SI_PRICE_PERCENTILE` | si | 874 |
| 51 | `si_term_structure` | `SI_TERM_STRUCTURE` | si | 893 |
| 52 | `si_top20_net` | `SI_TOP20_NET` | si | 893 |
| 53 | `spot_is_change` | `SPOT_IS_CHANGE` | si | 773 |
| 54 | `placeholder_comexsn` | `COMEX_SN` | sn | 1 |
| 55 | `sn_inventory_days` | `SN_INV_DAYS` | sn | 2,496 |
| 56 | `sn_long_short_ratio` | `SN_LONG_SHORT_RATIO` | sn | 345 |
| 57 | `sn_month_spread` | `SN_MONTH_SPREAD` | sn | 1,537 |
| 58 | `sn_price_percentile` | `SN_PRICE_PERCENTILE` | sn | 2,760 |
| 59 | `sn_term_structure` | `SN_TERM_STRUCTURE` | sn | 1,535 |
| 60 | `sn_top20_net` | `SN_TOP20_NET` | sn | 2,779 |
| 61 | `comex_zn_change` | `COMEX_ZN_CHANGE` | zn | 2,832 |
| 62 | `comex_zn_lme_spread` | `COMEX_ZN_LME_SPREAD` | zn | 1,051 |
| 63 | `placeholder_comexzn` | `COMEX_ZN` | zn | 1 |
| 64 | `zn_basis_change` | `ZN_BASIS_CHANGE` | zn | 2,833 |
| 65 | `zn_inv_change` | `ZN_INV_CHANGE` | zn | 516 |
| 66 | `zn_long_short_ratio` | `ZN_LONG_SHORT_RATIO` | zn | 345 |
| 67 | `zn_month_spread` | `ZN_MONTH_SPREAD` | zn | 2,832 |
| 68 | `zn_oi_percentile` | `ZN_OI_PERCENTILE` | zn | 326 |
| 69 | `zn_price_percentile` | `ZN_PRICE_PERCENTILE` | zn | 2,814 |
| 70 | `zn_term_structure` | `ZN_TERM_STRUCTURE` | zn | 2,833 |

## 4. Complete Mapping Table (Top 100)

> 718 rows total. Showing first 100 sorted by commodity, then indicator_id.

| # | indicator_id | indicator_id_mapped | commodity | source | records |
|---|-------------|--------------------|-----------|--------|--------:|
| 1 | `ag_21_close_front` | `AG_FU00014953` | ag | registered | 1 |
| 2 | `ag_21_openinterest` | `AG_HOLD_OPEN` | ag | registered | 1 |
| 3 | `ag_21_premium` | `AG_SPOT_PREMIUM` | ag | registered | 1 |
| 4 | `ag_23_lme_close` | `LME_AG` | ag | registered | 1 |
| 5 | `ag_25_profit` | `AG_SMELTING_PROFIT` | ag | registered | 1 |
| 6 | `al_00_basis` | `AL_BASIS` | al | real | 3,041 |
| 7 | `al_00_close_front` | `AL_FU00014934` | al | real | 3,041 |
| 8 | `al_00_cost_percentile` | `AL_PRICE_PERCENTILE` | al | real | 3,041 |
| 9 | `al_00_lme_close` | `LME_AL` | al | real | 3,041 |
| 10 | `al_00_openinterest_front` | `AL_HOLD_OPEN` | al | real | 3,041 |
| 11 | `al_00_premium` | `AL_SPOT_PREMIUM` | al | real | 3,041 |
| 12 | `al_00_volume` | `AL_VOLUME` | al | registered | 1 |
| 13 | `al_24_lme_spread` | `AL_MONTH_SPREAD` | al | real | 3,041 |
| 14 | `al_25_profit` | `AL_SMELTING_PROFIT` | al | real | 3,041 |
| 15 | `al_26_long_top20` | `AL_TOP20_LONG` | al | real | 3,041 |
| 16 | `al_26_short_top20` | `AL_TOP20_SHORT` | al | real | 3,041 |
| 17 | `al_321_import` | `AL_IMPORT` | al | registered | 1 |
| 18 | `al_321_output` | `AL_REFINING_OUTPUT` | al | registered | 1 |
| 19 | `al_51_util` | `AL_UTILIZATION` | al | registered | 1 |
| 20 | `al_62_export` | `AL_EXPORT` | al | registered | 1 |
| 21 | `al_71_cost` | `AL_REFINING_COST` | al | registered | 1 |
| 22 | `al_inv_change` | `AL_INV_CHANGE` | al | derived | 3,040 |
| 23 | `al_long_short_ratio` | `AL_LONG_SHORT_RATIO` | al | derived | 3,041 |
| 24 | `al_month_spread` | `AL_MONTH_SPREAD` | al | derived | 3,040 |
| 25 | `al_premium_change` | `AL_PREMIUM_CHANGE` | al | derived | 3,040 |
| 26 | `al_price_percentile` | `AL_PRICE_PERCENTILE` | al | derived | 3,022 |
| 27 | `al_term_structure` | `AL_TERM_STRUCTURE` | al | derived | 3,041 |
| 28 | `placeholder_comexal` | `COMEX_AL` | al | derived | 1 |
| 29 | `au_21_close_front` | `AU_FU00014948` | au | registered | 1 |
| 30 | `au_21_openinterest` | `AU_HOLD_OPEN` | au | registered | 1 |
| 31 | `au_21_premium` | `AU_SPOT_PREMIUM` | au | registered | 1 |
| 32 | `au_23_lme_close` | `LME_AU` | au | registered | 1 |
| 33 | `au_25_profit` | `AU_SMELTING_PROFIT` | au | registered | 1 |
| 34 | `comex_cu_change` | `COMEX_CU_CHANGE` | cu | derived | 3,040 |
| 35 | `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | cu | derived | 3,041 |
| 36 | `cu_21_basis` | `CU_BASIS` | cu | real | 3,041 |
| 37 | `cu_21_close_front` | `CU_FU00014941` | cu | real | 3,041 |
| 38 | `cu_21_openinterest` | `CU_HOLD_OPEN` | cu | real | 3,041 |
| 39 | `cu_21_openinterest_longshort` | `CU_LONG_SHORT_RATIO` | cu | real | 3,041 |
| 40 | `cu_21_volume` | `CU_VOLUME` | cu | registered | 1 |
| 41 | `cu_22_premium` | `CU_SPOT_PREMIUM` | cu | real | 3,041 |
| 42 | `cu_23_comex_close` | `COMEX_CU` | cu | real | 3,041 |
| 43 | `cu_23_inv` | `FU00014813` | cu | real | 3,041 |
| 44 | `cu_23_lme_close` | `LME_CU` | cu | real | 3,041 |
| 45 | `cu_24_openinterest_volume` | `CU_MONTH_SPREAD` | cu | real | 3,041 |
| 46 | `cu_25_profit` | `CU_SMELTING_PROFIT` | cu | real | 3,041 |
| 47 | `cu_25_profit_percentile` | `CU_PRICE_PERCENTILE` | cu | real | 3,041 |
| 48 | `cu_25_tc_conc` | `CU_COST_PERCENTILE` | cu | real | 3,041 |
| 49 | `cu_26_openinterest` | `CU_TOP20_SHORT` | cu | real | 3,041 |
| 50 | `cu_26_openinterest_top20_front` | `CU_TOP20_LONG` | cu | real | 3,041 |
| 51 | `cu_321_import` | `CU_IMPORT_321` | cu | registered | 1 |
| 52 | `cu_321_util_capacity_util` | `CU_UTILIZATION` | cu | real | 3,041 |
| 53 | `cu_41_output` | `CU_FU00014935` | cu | real | 3,041 |
| 54 | `cu_41_output_recycle` | `CU_RECYCLE_OUTPUT` | cu | registered | 1 |
| 55 | `cu_42_warrant_reg` | `CU_WARRANT_INVENTORY` | cu | real | 3,041 |
| 56 | `cu_43_social_stock` | `CU_SOCIAL_INV` | cu | real | 3,041 |
| 57 | `cu_61_import` | `CU_IMPORT` | cu | registered | 1 |
| 58 | `cu_62_export` | `CU_EXPORT` | cu | registered | 1 |
| 59 | `cu_71_cost` | `CU_REFINING_COST` | cu | registered | 1 |
| 60 | `cu_inv_change` | `CU_INV_CHANGE` | cu | derived | 3,040 |
| 61 | `cu_long_short_ratio` | `CU_LONG_SHORT_RATIO` | cu | derived | 3,041 |
| 62 | `cu_month_spread` | `CU_MONTH_SPREAD` | cu | derived | 3,040 |
| 63 | `cu_oi_percentile` | `CU_OI_PERCENTILE` | cu | derived | 3,022 |
| 64 | `cu_premium_change` | `CU_PREMIUM_CHANGE` | cu | derived | 3,040 |
| 65 | `cu_price_percentile` | `CU_PRICE_PERCENTILE` | cu | derived | 3,022 |
| 66 | `cu_term_structure` | `CU_TERM_STRUCTURE` | cu | derived | 3,041 |
| 67 | `cu_top20_net` | `CU_TOP20_NET` | cu | derived | 3,041 |
| 68 | `placeholder_cubalancesheet` | `CU_BALANCE_SHEET` | cu | derived | 1 |
| 69 | `j21_close` | `PB_FU00014946` | j21 | real | 3,041 |
| 70 | `j21_oi` | `PB_HOLD_OPEN` | j21 | real | 3,041 |
| 71 | `j26_basis` | `PB_BASIS_2` | j21 | registered | 1 |
| 72 | `j26_close` | `PB_FU00014947` | j21 | registered | 1 |
| 73 | `j26_oi` | `PB_HOLD_OPEN_2` | j21 | registered | 1 |
| 74 | `j26_premium` | `PB_SPOT_PREMIUM` | j21 | registered | 1 |
| 75 | `j26_volume` | `PB_VOLUME` | j21 | registered | 1 |
| 76 | `pb_long_short_ratio` | `PB_LONG_SHORT_RATIO` | j21 | derived | 3,041 |
| 77 | `pb_month_spread` | `PB_MONTH_SPREAD` | j21 | derived | 3,040 |
| 78 | `pb_price_percentile` | `PB_PRICE_PERCENTILE` | j21 | derived | 3,022 |
| 79 | `pb_term_structure` | `PB_TERM_STRUCTURE` | j21 | derived | 3,041 |
| 80 | `pb_top20_net` | `PB_TOP20_NET` | j21 | derived | 3,041 |
| 81 | `j22_premium` | `PB_BASIS` | j22 | real | 3,041 |
| 82 | `j22_spot` | `PB_SPOT_PREMIUM` | j22 | real | 3,041 |
| 83 | `j23_lme_cash` | `LME_PB` | j23 | real | 3,041 |
| 84 | `j24_spread_m` | `PB_MONTH_SPREAD` | j24 | real | 3,041 |
| 85 | `j24_spread_s` | `PB_TERM_STRUCTURE` | j24 | real | 3,041 |
| 86 | `j25_smelt_cost` | `PB_SMELTING_PROFIT` | j25 | real | 3,041 |
| 87 | `lc_top20_net` | `LC_TOP20_NET` | li | derived | 754 |
| 88 | `li_21_basis` | `LC_BASIS` | li | real | 754 |
| 89 | `li_21_close` | `LME_LC` | li | real | 754 |
| 90 | `li_21_close_2` | `LI_FU00015030` | li | real | 754 |
| 91 | `li_21_close_2_p09fix` | `LC_FU00015030` | li | derived | 1 |
| 92 | `li_21_openinterest_2` | `LI_HOLD_OPEN` | li | real | 754 |
| 93 | `li_21_openinterest_2_p09fix` | `LC_HOLD_OPEN` | li | derived | 1 |
| 94 | `li_21_openinterest_3` | `LI_HOLD_OPEN` | li | real | 754 |
| 95 | `li_21_openinterest_longshort` | `LC_LONG_SHORT_RATIO` | li | real | 754 |
| 96 | `li_21_premium` | `LC_SPOT_PREMIUM` | li | real | 439 |
| 97 | `li_21_volume` | `(unmapped)` | li | real | 754 |
| 98 | `li_21_warrant` | `LI_WARRANT` | li | real | 662 |
| 99 | `li_22_basis_carbonate_battery` | `LI_BASIS` | li | real | 754 |
| 100 | `li_22_premium` | `SPOT_LICAR` | li | real | 439 |

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
| DB映射命中率 (P0-9, 真实交集) | 109 | 109 | **100.00%** | PASS |
| DSHE指标数 (distinct_mapped_ids) | 237 | - | - | - |
| 缺失 (DSHE 109 - 交集) | 0 | - | - | - |
| 孤儿 (DB mapped - DSHE 109) | 128 | - | - | - |
| 总指标数 | 718 | - | - | - |
| 派生指标数 | 70 | - | - | - |

---
*Generated by export_mapping_list.py | 2026-10-15T18:33:41.464486*