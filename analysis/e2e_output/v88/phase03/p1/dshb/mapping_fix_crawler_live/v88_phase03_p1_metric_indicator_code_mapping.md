# V88 Phase03 P1 — Metric/Indicator/Code Complete Mapping List (MAPPING FIX)

> **TASK_ID**: V88_PHASE03_P1_DSHB_EXPORT_MAPPING_FIX_AND_NEW_CRAWLER_LIVE_DEPLOY_JOB
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **生成时间**: 2026-10-16T15:06:58.437169
> **数据库**: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db`
> **目的**: Complete export of all indicator_id / indicator_id_mapped / commodity mappings
> **版本**: MAPPING_FIX v2 (T0 — min()交集逻辑修复)

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Total unique indicators | 717 |
| Real indicators | 615 |
| Derived indicators | 69 |
| Mapped indicators | 710 (99.0%) |
| Unmapped indicators | 7 (1.0%) |
| Distinct mapped IDs (DSHE meta_chart) | 236 |
| P0-9 denominator | 109 |
| P0-9 numerator (all, real intersection) | 109 |
| P0-9 numerator (raw only, excl. derived) | **98** |
| P0-9 coverage (all, inflated) | 100.00% |
| P0-9 coverage (raw, corrected) | **89.91%** |
| 虚高偏差 (inflated - corrected) | 10.09pp |
| Method | real_set_intersection (no min truncation) |
| Derived/Placeholder excluded from numerator | 11 (of 11) |
| IDENTITY_FORM violations | 3 |
| Fill-in derived indicators | 11 |
| Missing from DSHE 109 | 0 |
| Orphan (in DB not in DSHE 109) | 127 |

## 2. Per-Commodity Mapping Coverage

| Commodity | Total | Real | Derived | Mapped | Unmapped | Coverage % |
|-----------|------:|-----:|--------:|-------:|---------:|-----------:|
|          |     8 |    0 |       8 |      8 |        0 |     100.0% |
| ag       |     5 |    5 |       0 |      5 |        0 |     100.0% |
| al       |    23 |   16 |       7 |     23 |        0 |     100.0% |
| au       |     5 |    5 |       0 |      5 |        0 |     100.0% |
| cu       |    35 |   24 |      11 |     35 |        0 |     100.0% |
| j21      |    12 |    7 |       5 |     12 |        0 |     100.0% |
| j22      |     2 |    2 |       0 |      2 |        0 |     100.0% |
| j23      |     1 |    1 |       0 |      1 |        0 |     100.0% |
| j24      |     2 |    2 |       0 |      2 |        0 |     100.0% |
| j25      |     1 |    1 |       0 |      1 |        0 |     100.0% |
| li       |    88 |   78 |      10 |     87 |        1 |      98.9% |
| ni       |   161 |  156 |       5 |    159 |        2 |      98.8% |
| pb       |     3 |    0 |       3 |      3 |        0 |     100.0% |
| si       |   129 |  124 |       5 |    127 |        2 |      98.4% |
| sn       |   124 |  118 |       6 |    123 |        1 |      99.2% |
| zn       |   118 |  109 |       9 |    117 |        1 |      99.2% |

## 3. Derived Indicators (69 total)

| # | indicator_id | indicator_id_mapped | commodity | records | in_DSHE_109 | is_DERIVED_11 |
|---|-------------|--------------------|-----------|--------:|:-----------:|:-------------:|
| 1 | `lc_top20_net` | `LC_TOP20_NET` |  | 754 |  |  |
| 2 | `ni_month_spread` | `NI_MONTH_SPREAD` |  | 1,655 | ✓ |  |
| 3 | `ni_term_structure` | `NI_TERM_STRUCTURE` |  | 1,655 | ✓ |  |
| 4 | `ni_top20_net` | `NI_TOP20_NET` |  | 2,779 |  |  |
| 5 | `si_month_spread` | `SI_MONTH_SPREAD` |  | 893 | ✓ |  |
| 6 | `si_term_structure` | `SI_TERM_STRUCTURE` |  | 893 | ✓ |  |
| 7 | `sn_top20_net` | `SN_TOP20_NET` |  | 2,496 |  |  |
| 8 | `zn_term_structure` | `ZN_TERM_STRUCTURE` |  | 2,834 | ✓ |  |
| 9 | `al_inv_change` | `AL_INV_CHANGE` | al | 3,040 |  |  |
| 10 | `al_long_short_ratio` | `AL_LONG_SHORT_RATIO` | al | 3,041 | ✓ | ✓ |
| 11 | `al_month_spread` | `AL_MONTH_SPREAD` | al | 3,040 | ✓ | ✓ |
| 12 | `al_premium_change` | `AL_PREMIUM_CHANGE` | al | 3,040 |  |  |
| 13 | `al_price_percentile` | `AL_PRICE_PERCENTILE` | al | 3,022 | ✓ | ✓ |
| 14 | `al_term_structure` | `AL_TERM_STRUCTURE` | al | 3,041 | ✓ | ✓ |
| 15 | `placeholder_comexal` | `COMEX_AL` | al | 1 | ✓ | ✓ |
| 16 | `comex_cu_change` | `COMEX_CU_CHANGE` | cu | 3,040 |  |  |
| 17 | `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | cu | 3,041 |  |  |
| 18 | `cu_inv_change` | `CU_INV_CHANGE` | cu | 3,040 |  |  |
| 19 | `cu_long_short_ratio` | `CU_LONG_SHORT_RATIO` | cu | 3,041 | ✓ |  |
| 20 | `cu_month_spread` | `CU_MONTH_SPREAD` | cu | 3,040 | ✓ |  |
| 21 | `cu_oi_percentile` | `CU_OI_PERCENTILE` | cu | 3,022 |  |  |
| 22 | `cu_premium_change` | `CU_PREMIUM_CHANGE` | cu | 3,040 |  |  |
| 23 | `cu_price_percentile` | `CU_PRICE_PERCENTILE` | cu | 3,022 | ✓ |  |
| 24 | `cu_term_structure` | `CU_TERM_STRUCTURE` | cu | 3,041 | ✓ |  |
| 25 | `cu_top20_net` | `CU_TOP20_NET` | cu | 3,041 |  |  |
| 26 | `placeholder_cubalancesheet` | `CU_BALANCE_SHEET` | cu | 1 | ✓ |  |
| 27 | `pb_long_short_ratio` | `PB_LONG_SHORT_RATIO` | j21 | 3,041 | ✓ |  |
| 28 | `pb_month_spread` | `PB_MONTH_SPREAD` | j21 | 3,040 | ✓ |  |
| 29 | `pb_price_percentile` | `PB_PRICE_PERCENTILE` | j21 | 3,022 | ✓ |  |
| 30 | `pb_term_structure` | `PB_TERM_STRUCTURE` | j21 | 3,041 | ✓ |  |
| 31 | `pb_top20_net` | `PB_TOP20_NET` | j21 | 3,041 |  |  |
| 32 | `li_21_close_2_p09fix` | `LC_FU00015030` | li | 1 | ✓ |  |
| 33 | `li_21_openinterest_2_p09fix` | `LC_HOLD_OPEN` | li | 1 | ✓ |  |
| 34 | `li_basis_change` | `LC_BASIS_CHANGE` | li | 753 |  |  |
| 35 | `li_inv_change` | `LI_INV_CHANGE` | li | 17 |  |  |
| 36 | `li_long_short_ratio` | `LC_LONG_SHORT_RATIO` | li | 754 | ✓ |  |
| 37 | `li_month_spread` | `LC_MONTH_SPREAD` | li | 436 | ✓ |  |
| 38 | `li_oi_percentile` | `LI_OI_PERCENTILE` | li | 735 |  |  |
| 39 | `li_price_percentile` | `LC_PRICE_PERCENTILE` | li | 735 | ✓ |  |
| 40 | `li_term_structure` | `LC_TERM_STRUCTURE` | li | 754 | ✓ |  |
| 41 | `spot_licar_change` | `SPOT_LICAR_CHANGE` | li | 438 |  |  |
| 42 | `ni_basis_change` | `NI_BASIS_CHANGE` | ni | 2,777 |  |  |
| 43 | `ni_inv_change` | `NI_INV_CHANGE` | ni | 499 |  |  |
| 44 | `ni_long_short_ratio` | `NI_LONG_SHORT_RATIO` | ni | 346 | ✓ |  |
| 45 | `ni_price_percentile` | `NI_PRICE_PERCENTILE` | ni | 2,760 | ✓ |  |
| 46 | `placeholder_comexni` | `COMEX_NI` | ni | 1 | ✓ | ✓ |
| 47 | `placeholder_comexpb` | `COMEX_PB` | pb | 1 | ✓ | ✓ |
| 48 | `placeholder_pbtop20long` | `PB_TOP20_LONG` | pb | 1 | ✓ |  |
| 49 | `placeholder_pbtop20short` | `PB_TOP20_SHORT` | pb | 1 | ✓ |  |
| 50 | `placeholder_spotis` | `SPOT_IS` | si | 1 | ✓ |  |
| 51 | `si_inventory_days` | `SI_INV_DAYS` | si | 133 |  |  |
| 52 | `si_long_short_ratio` | `SI_LONG_SHORT_RATIO` | si | 893 | ✓ |  |
| 53 | `si_price_percentile` | `SI_PRICE_PERCENTILE` | si | 874 | ✓ |  |
| 54 | `spot_is_change` | `SPOT_IS_CHANGE` | si | 773 |  |  |
| 55 | `placeholder_comexsn` | `COMEX_SN` | sn | 1 | ✓ | ✓ |
| 56 | `sn_inventory_days` | `SN_INV_DAYS` | sn | 2,496 |  |  |
| 57 | `sn_long_short_ratio` | `SN_LONG_SHORT_RATIO` | sn | 345 | ✓ |  |
| 58 | `sn_month_spread` | `SN_MONTH_SPREAD` | sn | 1,537 | ✓ |  |
| 59 | `sn_price_percentile` | `SN_PRICE_PERCENTILE` | sn | 2,760 | ✓ |  |
| 60 | `sn_term_structure` | `SN_TERM_STRUCTURE` | sn | 1,535 | ✓ |  |
| 61 | `comex_zn_change` | `COMEX_ZN_CHANGE` | zn | 2,832 |  |  |
| 62 | `comex_zn_lme_spread` | `COMEX_ZN_LME_SPREAD` | zn | 1,051 |  |  |
| 63 | `placeholder_comexzn` | `COMEX_ZN` | zn | 1 | ✓ | ✓ |
| 64 | `zn_basis_change` | `ZN_BASIS_CHANGE` | zn | 2,833 |  |  |
| 65 | `zn_inv_change` | `ZN_INV_CHANGE` | zn | 516 |  |  |
| 66 | `zn_long_short_ratio` | `ZN_LONG_SHORT_RATIO` | zn | 345 | ✓ |  |
| 67 | `zn_month_spread` | `ZN_MONTH_SPREAD` | zn | 2,832 | ✓ |  |
| 68 | `zn_oi_percentile` | `ZN_OI_PERCENTILE` | zn | 326 |  |  |
| 69 | `zn_price_percentile` | `ZN_PRICE_PERCENTILE` | zn | 2,814 | ✓ |  |

## 4. Complete Mapping Table (Top 100)

> 717 rows total. Showing first 100 sorted by commodity, then indicator_id.

| # | indicator_id | indicator_id_mapped | commodity | source | records |
|---|-------------|--------------------|-----------|--------|--------:|
| 1 | `lc_top20_net` | `LC_TOP20_NET` |  | derived | 754 |
| 2 | `ni_month_spread` | `NI_MONTH_SPREAD` |  | derived | 1,655 |
| 3 | `ni_term_structure` | `NI_TERM_STRUCTURE` |  | derived | 1,655 |
| 4 | `ni_top20_net` | `NI_TOP20_NET` |  | derived | 2,779 |
| 5 | `si_month_spread` | `SI_MONTH_SPREAD` |  | derived | 893 |
| 6 | `si_term_structure` | `SI_TERM_STRUCTURE` |  | derived | 893 |
| 7 | `sn_top20_net` | `SN_TOP20_NET` |  | derived | 2,496 |
| 8 | `zn_term_structure` | `ZN_TERM_STRUCTURE` |  | derived | 2,834 |
| 9 | `ag_21_close_front` | `AG_FU00014953` | ag | registered | 1 |
| 10 | `ag_21_openinterest` | `AG_HOLD_OPEN` | ag | registered | 1 |
| 11 | `ag_21_premium` | `AG_SPOT_PREMIUM` | ag | registered | 1 |
| 12 | `ag_23_lme_close` | `LME_AG` | ag | registered | 1 |
| 13 | `ag_25_profit` | `AG_SMELTING_PROFIT` | ag | registered | 1 |
| 14 | `al_00_basis` | `AL_BASIS` | al | real | 3,041 |
| 15 | `al_00_close_front` | `AL_FU00014934` | al | real | 3,041 |
| 16 | `al_00_cost_percentile` | `AL_PRICE_PERCENTILE` | al | real | 3,041 |
| 17 | `al_00_lme_close` | `LME_AL` | al | real | 3,041 |
| 18 | `al_00_openinterest_front` | `AL_HOLD_OPEN` | al | real | 3,041 |
| 19 | `al_00_premium` | `AL_SPOT_PREMIUM` | al | real | 3,041 |
| 20 | `al_00_volume` | `AL_VOLUME` | al | registered | 1 |
| 21 | `al_24_lme_spread` | `AL_MONTH_SPREAD` | al | real | 3,041 |
| 22 | `al_25_profit` | `AL_SMELTING_PROFIT` | al | real | 3,041 |
| 23 | `al_26_long_top20` | `AL_TOP20_LONG` | al | real | 3,041 |
| 24 | `al_26_short_top20` | `AL_TOP20_SHORT` | al | real | 3,041 |
| 25 | `al_321_import` | `AL_IMPORT` | al | registered | 1 |
| 26 | `al_321_output` | `AL_REFINING_OUTPUT` | al | registered | 1 |
| 27 | `al_51_util` | `AL_UTILIZATION` | al | registered | 1 |
| 28 | `al_62_export` | `AL_EXPORT` | al | registered | 1 |
| 29 | `al_71_cost` | `AL_REFINING_COST` | al | registered | 1 |
| 30 | `al_inv_change` | `AL_INV_CHANGE` | al | derived | 3,040 |
| 31 | `al_long_short_ratio` | `AL_LONG_SHORT_RATIO` | al | derived | 3,041 |
| 32 | `al_month_spread` | `AL_MONTH_SPREAD` | al | derived | 3,040 |
| 33 | `al_premium_change` | `AL_PREMIUM_CHANGE` | al | derived | 3,040 |
| 34 | `al_price_percentile` | `AL_PRICE_PERCENTILE` | al | derived | 3,022 |
| 35 | `al_term_structure` | `AL_TERM_STRUCTURE` | al | derived | 3,041 |
| 36 | `placeholder_comexal` | `COMEX_AL` | al | derived | 1 |
| 37 | `au_21_close_front` | `AU_FU00014948` | au | registered | 1 |
| 38 | `au_21_openinterest` | `AU_HOLD_OPEN` | au | registered | 1 |
| 39 | `au_21_premium` | `AU_SPOT_PREMIUM` | au | registered | 1 |
| 40 | `au_23_lme_close` | `LME_AU` | au | registered | 1 |
| 41 | `au_25_profit` | `AU_SMELTING_PROFIT` | au | registered | 1 |
| 42 | `comex_cu_change` | `COMEX_CU_CHANGE` | cu | derived | 3,040 |
| 43 | `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | cu | derived | 3,041 |
| 44 | `cu_21_basis` | `CU_BASIS` | cu | real | 3,041 |
| 45 | `cu_21_close_front` | `CU_FU00014941` | cu | real | 3,041 |
| 46 | `cu_21_openinterest` | `CU_HOLD_OPEN` | cu | real | 3,041 |
| 47 | `cu_21_openinterest_longshort` | `CU_LONG_SHORT_RATIO` | cu | real | 3,041 |
| 48 | `cu_21_volume` | `CU_VOLUME` | cu | registered | 1 |
| 49 | `cu_22_premium` | `CU_SPOT_PREMIUM` | cu | real | 3,041 |
| 50 | `cu_23_comex_close` | `COMEX_CU` | cu | real | 3,041 |
| 51 | `cu_23_inv` | `FU00014813` | cu | real | 3,041 |
| 52 | `cu_23_lme_close` | `LME_CU` | cu | real | 3,041 |
| 53 | `cu_24_openinterest_volume` | `CU_MONTH_SPREAD` | cu | real | 3,041 |
| 54 | `cu_25_profit` | `CU_SMELTING_PROFIT` | cu | real | 3,041 |
| 55 | `cu_25_profit_percentile` | `CU_PRICE_PERCENTILE` | cu | real | 3,041 |
| 56 | `cu_25_tc_conc` | `CU_COST_PERCENTILE` | cu | real | 3,041 |
| 57 | `cu_26_openinterest` | `CU_TOP20_SHORT` | cu | real | 3,041 |
| 58 | `cu_26_openinterest_top20_front` | `CU_TOP20_LONG` | cu | real | 3,041 |
| 59 | `cu_321_import` | `CU_IMPORT_321` | cu | registered | 1 |
| 60 | `cu_321_util_capacity_util` | `CU_UTILIZATION` | cu | real | 3,041 |
| 61 | `cu_41_output` | `CU_FU00014935` | cu | real | 3,041 |
| 62 | `cu_41_output_recycle` | `CU_RECYCLE_OUTPUT` | cu | registered | 1 |
| 63 | `cu_42_warrant_reg` | `CU_WARRANT_INVENTORY` | cu | real | 3,041 |
| 64 | `cu_43_social_stock` | `CU_SOCIAL_INV` | cu | real | 3,041 |
| 65 | `cu_61_import` | `CU_IMPORT` | cu | registered | 1 |
| 66 | `cu_62_export` | `CU_EXPORT` | cu | registered | 1 |
| 67 | `cu_71_cost` | `CU_REFINING_COST` | cu | registered | 1 |
| 68 | `cu_inv_change` | `CU_INV_CHANGE` | cu | derived | 3,040 |
| 69 | `cu_long_short_ratio` | `CU_LONG_SHORT_RATIO` | cu | derived | 3,041 |
| 70 | `cu_month_spread` | `CU_MONTH_SPREAD` | cu | derived | 3,040 |
| 71 | `cu_oi_percentile` | `CU_OI_PERCENTILE` | cu | derived | 3,022 |
| 72 | `cu_premium_change` | `CU_PREMIUM_CHANGE` | cu | derived | 3,040 |
| 73 | `cu_price_percentile` | `CU_PRICE_PERCENTILE` | cu | derived | 3,022 |
| 74 | `cu_term_structure` | `CU_TERM_STRUCTURE` | cu | derived | 3,041 |
| 75 | `cu_top20_net` | `CU_TOP20_NET` | cu | derived | 3,041 |
| 76 | `placeholder_cubalancesheet` | `CU_BALANCE_SHEET` | cu | derived | 1 |
| 77 | `j21_close` | `PB_FU00014946` | j21 | real | 3,041 |
| 78 | `j21_oi` | `PB_HOLD_OPEN` | j21 | real | 3,041 |
| 79 | `j26_basis` | `PB_BASIS_2` | j21 | registered | 1 |
| 80 | `j26_close` | `PB_FU00014947` | j21 | registered | 1 |
| 81 | `j26_oi` | `PB_HOLD_OPEN_2` | j21 | registered | 1 |
| 82 | `j26_premium` | `PB_SPOT_PREMIUM` | j21 | registered | 1 |
| 83 | `j26_volume` | `PB_VOLUME` | j21 | registered | 1 |
| 84 | `pb_long_short_ratio` | `PB_LONG_SHORT_RATIO` | j21 | derived | 3,041 |
| 85 | `pb_month_spread` | `PB_MONTH_SPREAD` | j21 | derived | 3,040 |
| 86 | `pb_price_percentile` | `PB_PRICE_PERCENTILE` | j21 | derived | 3,022 |
| 87 | `pb_term_structure` | `PB_TERM_STRUCTURE` | j21 | derived | 3,041 |
| 88 | `pb_top20_net` | `PB_TOP20_NET` | j21 | derived | 3,041 |
| 89 | `j22_premium` | `PB_BASIS` | j22 | real | 3,041 |
| 90 | `j22_spot` | `PB_SPOT_PREMIUM` | j22 | real | 3,041 |
| 91 | `j23_lme_cash` | `LME_PB` | j23 | real | 3,041 |
| 92 | `j24_spread_m` | `PB_MONTH_SPREAD` | j24 | real | 3,041 |
| 93 | `j24_spread_s` | `PB_TERM_STRUCTURE` | j24 | real | 3,041 |
| 94 | `j25_smelt_cost` | `PB_SMELTING_PROFIT` | j25 | real | 3,041 |
| 95 | `li_21_basis` | `LC_BASIS` | li | real | 754 |
| 96 | `li_21_close` | `LME_LC` | li | real | 754 |
| 97 | `li_21_close_2` | `LI_FU00015030` | li | real | 754 |
| 98 | `li_21_close_2_p09fix` | `LC_FU00015030` | li | derived | 1 |
| 99 | `li_21_openinterest_2` | `LI_HOLD_OPEN` | li | real | 754 |
| 100 | `li_21_openinterest_2_p09fix` | `LC_HOLD_OPEN` | li | derived | 1 |

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

## 6. DERIVED_11: Derived/Placeholder Indicators in DSHE 109

> 11 indicators in DSHE 109 that are derived/placeholder (not raw data).
> **Excluded from P0-9 numerator** to prevent虚高. Source: DB analysis.

| # | Indicator ID | Type | DB indicator_id | Records | In Intersection |
|---|-------------|------|----------------|--------:|:---------------:|
| 1 | `AL_LONG_SHORT_RATIO` | derived | `al_long_short_ratio` | 3,041 | ✓ |
| 2 | `AL_MONTH_SPREAD` | derived | `al_24_lme_spread` | 6,081 | ✓ |
| 3 | `AL_PRICE_PERCENTILE` | derived | `al_00_cost_percentile` | 6,063 | ✓ |
| 4 | `AL_TERM_STRUCTURE` | derived | `al_term_structure` | 3,041 | ✓ |
| 5 | `AL_TOP20_LONG` | derived | `al_26_long_top20` | 3,041 | ✓ |
| 6 | `AL_TOP20_SHORT` | derived | `al_26_short_top20` | 3,041 | ✓ |
| 7 | `COMEX_AL` | placeholder | `placeholder_comexal` | 1 | ✓ |
| 8 | `COMEX_NI` | placeholder | `placeholder_comexni` | 1 | ✓ |
| 9 | `COMEX_PB` | placeholder | `placeholder_comexpb` | 1 | ✓ |
| 10 | `COMEX_SN` | placeholder | `placeholder_comexsn` | 1 | ✓ |
| 11 | `COMEX_ZN` | placeholder | `placeholder_comexzn` | 1 | ✓ |

> **Impact**: Excluding these 11 from P0-9 numerator:
> - Inflated: 109/109 = 100.00%
> - **Corrected: 98/109 = 89.91%**
> - 虚高偏差: 10.09pp

## 7. IDENTITY_FORM Violations (3)

> 3 indicators have multiple commodity mappings (IDENTITY_FORM violation).
> Fix: Assign primary commodity; secondary mappings should use distinct indicator IDs.

| # | Indicator ID | Commodities | Primary | Secondary Mappings | Fix |
|---|-------------|:----------:|:-------:|-------------------|-----|
| 1 | `PB_MONTH_SPREAD` | j21, j24 | **j21** | j24_spread_m -> PB_MONTH_SPREAD (j24) | Assign primary=j21; j24_spread_m should map to J24_MONTH_SPREAD |
| 2 | `PB_SPOT_PREMIUM` | j21, j22 | **j22** | j26_premium -> PB_SPOT_PREMIUM (j21) | Assign primary=j22; j26_premium should map to J26_SPOT_PREMIUM |
| 3 | `PB_TERM_STRUCTURE` | j21, j24 | **j21** | j24_spread_s -> PB_TERM_STRUCTURE (j24) | Assign primary=j21; j24_spread_s should map to J24_TERM_STRUCTURE |

## 8. Fill-in Derived Indicators (11)

> 11 derived indicators in DB but NOT in DSHE 109 list.
> These should be registered in meta_chart.yaml for complete coverage.

| # | Mapped ID | Source indicator_id | Commodity | Records |
|---|-----------|-------------------|-----------|--------:|
| 1 | `COMEX_CU_CHANGE` | `comex_cu_change` | cu | 3,040 |
| 2 | `COMEX_CU_LME_SPREAD` | `comex_cu_lme_spread` | cu | 3,041 |
| 3 | `COMEX_ZN_CHANGE` | `comex_zn_change` | zn | 2,832 |
| 4 | `COMEX_ZN_LME_SPREAD` | `comex_zn_lme_spread` | zn | 1,051 |
| 5 | `CU_TOP20_NET` | `cu_top20_net` | cu | 3,041 |
| 6 | `LC_TOP20_NET` | `lc_top20_net` |  | 754 |
| 7 | `NI_TOP20_NET` | `ni_top20_net` |  | 2,779 |
| 8 | `PB_TOP20_NET` | `pb_top20_net` | j21 | 3,041 |
| 9 | `SN_TOP20_NET` | `sn_top20_net` |  | 2,496 |
| 10 | `LC_BASIS_CHANGE` | `li_basis_change` | li | 753 |
| 11 | `NI_BASIS_CHANGE` | `ni_basis_change` | ni | 2,777 |

## 9. P0-9 Coverage Report (Corrected)

| 口径 | 分子 | 分母 | 比率 | 状态 |
|------|:----:|:----:|:----:|:----:|
| DB映射命中率 (all, inflated) | 109 | 109 | 100.00% | PASS |
| DB映射命中率 (raw, corrected) | **98** | **109** | **89.91%** | **PASS** |
| 虚高偏差 | 11 | - | **10.09pp** | CORRECTED |
| IDENTITY_FORM违规 | 3 | - | - | DOCUMENTED |
| DSHE指标数 (distinct_mapped_ids) | 236 | - | - | - |
| 缺失 (DSHE 109 - 交集) | 0 | - | - | - |
| 孤儿 (DB mapped - DSHE 109) | 127 | - | - | - |
| 总指标数 | 717 | - | - | - |
| 派生指标数 | 69 | - | - | - |

---
*Generated by export_mapping_list.py (MAPPING_FIX v2) | 2026-10-16T15:06:58.437169*
*T0: min()交集逻辑修复 | 11项DERIVED_11排除 | 3条IDENTITY_FORM文档化 | 10.09pp虚高收敛*