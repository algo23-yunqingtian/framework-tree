# V88 Phase03 P0 — Metric/Indicator/Code Complete Mapping List

> **TASK_ID**: V88_PHASE03_P0_DSHB_ARTIFACT_ARCHIVE
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1
> **Generated**: 2026-10-15T14:06:26.218832
> **Database**: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db`
> **Purpose**: Complete export of all indicator_id / indicator_id_mapped / commodity mappings from phase03_test.db

---

## 1. Summary

| Metric | Value |
|--------|-------|
| Total unique indicators | 615 |
| Mapped indicators | 608 (98.9%) |
| Unmapped indicators | 7 (1.1%) |
| Mapped indicator_id_mapped count (distinct) | 156 |

## 2. Per-Commodity Mapping Coverage

| Commodity | Total | Mapped | Unmapped | Coverage % |
|-----------|------:|-------:|---------:|-----------:|
| al       |    10 |     10 |        0 |     100.0% |
| cu       |    18 |     18 |        0 |     100.0% |
| j21      |     2 |      2 |        0 |     100.0% |
| j22      |     2 |      2 |        0 |     100.0% |
| j23      |     1 |      1 |        0 |     100.0% |
| j24      |     2 |      2 |        0 |     100.0% |
| j25      |     1 |      1 |        0 |     100.0% |
| li       |    74 |     73 |        1 |      98.6% |
| ni       |   156 |    154 |        2 |      98.7% |
| si       |   124 |    122 |        2 |      98.4% |
| sn       |   116 |    115 |        1 |      99.1% |
| zn       |   109 |    108 |        1 |      99.1% |

## 3. Complete Mapping Table

> 615 rows total. Sorted by commodity, then indicator_id.

| # | indicator_id | indicator_id_mapped | commodity | records | date_range |
|---|-------------|--------------------|-----------|--------:|------------|
| 1 | `al_00_basis` | `AL_BASIS` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 2 | `al_00_close_front` | `AL_FU00014934` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 3 | `al_00_cost_percentile` | `AL_PRICE_PERCENTILE` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 4 | `al_00_lme_close` | `LME_AL` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 5 | `al_00_openinterest_front` | `AL_HOLD_OPEN` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 6 | `al_00_premium` | `AL_SPOT_PREMIUM` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 7 | `al_24_lme_spread` | `AL_MONTH_SPREAD` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 8 | `al_25_profit` | `AL_SMELTING_PROFIT` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 9 | `al_26_long_top20` | `AL_TOP20_LONG` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 10 | `al_26_short_top20` | `AL_TOP20_SHORT` | al | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 11 | `cu_21_basis` | `CU_BASIS` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 12 | `cu_21_close_front` | `CU_FU00014941` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 13 | `cu_21_openinterest` | `CU_HOLD_OPEN` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 14 | `cu_21_openinterest_longshort` | `CU_LONG_SHORT_RATIO` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 15 | `cu_22_premium` | `CU_SPOT_PREMIUM` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 16 | `cu_23_comex_close` | `COMEX_CU` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 17 | `cu_23_inv` | `FU00014813` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 18 | `cu_23_lme_close` | `LME_CU` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 19 | `cu_24_openinterest_volume` | `CU_MONTH_SPREAD` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 20 | `cu_25_profit` | `CU_SMELTING_PROFIT` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 21 | `cu_25_profit_percentile` | `CU_PRICE_PERCENTILE` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 22 | `cu_25_tc_conc` | `CU_COST_PERCENTILE` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 23 | `cu_26_openinterest` | `CU_TOP20_SHORT` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 24 | `cu_26_openinterest_top20_front` | `CU_TOP20_LONG` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 25 | `cu_321_util_capacity_util` | `CU_UTILIZATION` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 26 | `cu_41_output` | `CU_FU00014935` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 27 | `cu_42_warrant_reg` | `CU_WARRANT_INVENTORY` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 28 | `cu_43_social_stock` | `CU_SOCIAL_INV` | cu | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 29 | `j21_close` | `PB_FU00014946` | j21 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 30 | `j21_oi` | `PB_HOLD_OPEN` | j21 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 31 | `j22_premium` | `PB_BASIS` | j22 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 32 | `j22_spot` | `PB_SPOT_PREMIUM` | j22 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 33 | `j23_lme_cash` | `LME_PB` | j23 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 34 | `j24_spread_m` | `PB_MONTH_SPREAD` | j24 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 35 | `j24_spread_s` | `PB_TERM_STRUCTURE` | j24 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 36 | `j25_smelt_cost` | `PB_SMELTING_PROFIT` | j25 | 3,041 | 2015-01-02 ~ 2026-08-28 |
| 37 | `li_21_basis` | `LC_BASIS` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 38 | `li_21_close` | `LME_LC` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 39 | `li_21_close_2` | `LI_FU00015030` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 40 | `li_21_openinterest_2` | `LI_HOLD_OPEN` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 41 | `li_21_openinterest_3` | `LI_HOLD_OPEN` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 42 | `li_21_openinterest_longshort` | `LC_LONG_SHORT_RATIO` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 43 | `li_21_premium` | `LC_SPOT_PREMIUM` | li | 439 | 2024-11-14 ~ 2026-08-28 |
| 44 | `li_21_volume` | `(unmapped)` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 45 | `li_21_warrant` | `LI_WARRANT` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 46 | `li_22_basis_carbonate_battery` | `LI_BASIS` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 47 | `li_22_premium` | `SPOT_LICAR` | li | 439 | 2024-11-14 ~ 2026-08-28 |
| 48 | `li_22_premium_2` | `LI_SPOT_PREMIUM` | li | 439 | 2024-11-14 ~ 2026-08-28 |
| 49 | `li_22_premium_carbonate_battery` | `LI_SPOT_PREMIUM` | li | 439 | 2024-11-14 ~ 2026-08-28 |
| 50 | `li_22_premium_ratio_carbonate` | `LI_SPOT_PREMIUM` | li | 439 | 2024-11-14 ~ 2026-08-28 |
| 51 | `li_22_premium_ratio_carbonate_2` | `LI_SPOT_PREMIUM` | li | 439 | 2024-11-14 ~ 2026-08-28 |
| 52 | `li_25_profit` | `LC_SMELTING_PROFIT` | li | 891 | 2023-02-01 ~ 2026-08-28 |
| 53 | `li_25_profit_2` | `LI_SMELTING_PROFIT` | li | 660 | 2024-01-02 ~ 2026-08-28 |
| 54 | `li_25_profit_3` | `LI_SMELTING_PROFIT` | li | 660 | 2024-01-02 ~ 2026-08-28 |
| 55 | `li_25_profit_4` | `LI_SMELTING_PROFIT` | li | 660 | 2024-01-02 ~ 2026-08-28 |
| 56 | `li_25_profit_carbonate` | `LI_SMELTING_PROFIT` | li | 891 | 2023-02-01 ~ 2026-08-28 |
| 57 | `li_26_openinterest_longshort` | `LI_LONG_SHORT_RATIO` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 58 | `li_26_openinterest_longshort_2` | `LI_LONG_SHORT_RATIO` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 59 | `li_26_openinterest_top20` | `LC_TOP20_LONG` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 60 | `li_26_openinterest_top20_2` | `LC_TOP20_SHORT` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 61 | `li_26_openinterest_top20_3` | `LI_TOP20_LONG` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 62 | `li_26_openinterest_top20_4` | `LI_TOP20_LONG` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 63 | `li_311_capacity` | `LI_REFINING_CAPACITY` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 64 | `li_311_capacity_util` | `LI_UTILIZATION` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 65 | `li_311_output` | `LI_REFINING_OUTPUT` | li | 11 | 2015-12-31 ~ 2025-12-31 |
| 66 | `li_311_output_2` | `LI_REFINING_OUTPUT` | li | 55 | 2022-01-31 ~ 2026-07-31 |
| 67 | `li_312_inv` | `LI_SHFE_INV` | li | 68 | 2025-04-25 ~ 2026-08-21 |
| 68 | `li_312_output` | `LI_REFINING_OUTPUT` | li | 11 | 2015-12-31 ~ 2025-12-31 |
| 69 | `li_312_output_2` | `LI_REFINING_OUTPUT` | li | 11 | 2015-12-31 ~ 2025-12-31 |
| 70 | `li_313_output` | `LI_REFINING_OUTPUT` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 71 | `li_313_output_2` | `LI_REFINING_OUTPUT` | li | 45 | 2015-03-31 ~ 2026-03-31 |
| 72 | `li_313_output_3` | `LI_REFINING_OUTPUT` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 73 | `li_314_import` | `LI_IMPORT` | li | 19 | 2025-01-31 ~ 2026-07-31 |
| 74 | `li_314_import_2` | `LI_IMPORT` | li | 16 | 2021-03-31 ~ 2024-12-31 |
| 75 | `li_314_import_3` | `LI_IMPORT` | li | 16 | 2021-03-31 ~ 2024-12-31 |
| 76 | `li_314_import_4` | `LI_IMPORT` | li | 16 | 2021-03-31 ~ 2024-12-31 |
| 77 | `li_321_output` | `LI_REFINING_OUTPUT` | li | 103 | 2018-01-31 ~ 2026-07-31 |
| 78 | `li_321_output_2` | `LI_REFINING_OUTPUT` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 79 | `li_321_output_3` | `LI_REFINING_OUTPUT` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 80 | `li_321_output_4` | `LI_REFINING_OUTPUT` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 81 | `li_321_output_carbonate` | `LI_REFINING_OUTPUT` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 82 | `li_321_output_carbonate_battery` | `LI_REFINING_OUTPUT` | li | 55 | 2022-01-31 ~ 2026-07-31 |
| 83 | `li_321_output_carbonate_industrial` | `LI_REFINING_OUTPUT` | li | 55 | 2022-01-31 ~ 2026-07-31 |
| 84 | `li_323_capacity` | `LI_REFINING_CAPACITY` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 85 | `li_323_capacity_util` | `LI_UTILIZATION` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 86 | `li_323_output` | `LI_REFINING_OUTPUT` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 87 | `li_323_output_recycle` | `LI_RECYCLE_OUTPUT` | li | 103 | 2018-01-31 ~ 2026-07-31 |
| 88 | `li_323_output_recycle_carbonate` | `LI_RECYCLE_OUTPUT` | li | 55 | 2022-01-31 ~ 2026-07-31 |
| 89 | `li_324_capacity` | `LI_REFINING_CAPACITY` | li | 3 | 2021-12-31 ~ 2023-12-31 |
| 90 | `li_324_capacity_util` | `LI_UTILIZATION` | li | 211 | 2022-08-05 ~ 2026-08-28 |
| 91 | `li_41_inv` | `LI_SHFE_INV` | li | 18 | 2025-02-28 ~ 2026-07-31 |
| 92 | `li_41_inv_carbonate_battery` | `LI_SHFE_INV` | li | 34 | 2023-10-31 ~ 2026-07-31 |
| 93 | `li_41_inv_carbonate_industrial` | `LI_SHFE_INV` | li | 34 | 2023-10-31 ~ 2026-07-31 |
| 94 | `li_41_inv_implicit` | `LI_SHFE_INV` | li | 34 | 2023-10-31 ~ 2026-07-31 |
| 95 | `li_41_warrant` | `LI_WARRANT` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 96 | `li_41_warrant_2` | `LI_WARRANT` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 97 | `li_42_inv_warrant_days` | `LI_SHFE_INV` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 98 | `li_42_warrant_carbonate` | `LI_WARRANT` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 99 | `li_42_warrant_carbonate_battery` | `LI_WARRANT` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 100 | `li_42_warrant_carbonate_industrial` | `LI_WARRANT` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 101 | `li_42_warrant_ratio` | `LI_WARRANT` | li | 662 | 2023-12-06 ~ 2026-08-28 |
| 102 | `li_43_inv_days` | `LI_SHFE_INV` | li | 34 | 2023-10-31 ~ 2026-07-31 |
| 103 | `li_43_inv_plant` | `LI_SHFE_INV` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 104 | `li_44_inv_carbonate` | `LI_SHFE_INV` | li | 34 | 2023-10-31 ~ 2026-07-31 |
| 105 | `li_44_inv_carbonate_battery` | `LI_SHFE_INV` | li | 34 | 2023-10-31 ~ 2026-07-31 |
| 106 | `li_44_inv_carbonate_industrial` | `LI_SHFE_INV` | li | 34 | 2023-10-31 ~ 2026-07-31 |
| 107 | `li_44_inv_plant` | `LI_SHFE_INV` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 108 | `li_44_inv_plant_2` | `LI_SHFE_INV` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 109 | `li_44_inv_plant_3` | `LI_SHFE_INV` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 110 | `li_44_inv_plant_days` | `LI_SHFE_INV` | li | 31 | 2024-01-31 ~ 2026-07-31 |
| 111 | `ni_21_close_front` | `NI_FU00014982` | ni | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 112 | `ni_21_far_price` | `NI_FAR_PRICE` | ni | 1,659 | 2020-01-02 ~ 2026-08-28 |
| 113 | `ni_21_front_price` | `NI_FU00014982` | ni | 1,659 | 2020-01-02 ~ 2026-08-28 |
| 114 | `ni_21_lme_price` | `LME_NI` | ni | 1,862 | 2018-10-10 ~ 2026-08-28 |
| 115 | `ni_21_near_price` | `NI_NEAR_PRICE` | ni | 1,659 | 2020-01-02 ~ 2026-08-28 |
| 116 | `ni_21_openinterest_front` | `NI_HOLD_OPEN` | ni | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 117 | `ni_21_percentile_openinterest` | `NI_LONG_SHORT_RATIO` | ni | 346 | 2020-01-03 ~ 2026-08-21 |
| 118 | `ni_21_premium` | `NI_SPOT_PREMIUM` | ni | 1,655 | 2020-01-02 ~ 2026-08-28 |
| 119 | `ni_21_volume_front` | `(unmapped)` | ni | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 120 | `ni_21_volume_top20` | `(unmapped)` | ni | 2,934 | 2015-01-02 ~ 2026-08-28 |
| 121 | `ni_21_warrant` | `NI_WARRANT` | ni | 2,764 | 2015-04-13 ~ 2026-08-28 |
| 122 | `ni_22_basis` | `NI_BASIS` | ni | 2,778 | 2015-03-27 ~ 2026-08-28 |
| 123 | `ni_22_import` | `NI_IMPORT` | ni | 137 | 2015-01-31 ~ 2026-07-31 |
| 124 | `ni_22_premium` | `NI_SPOT_PREMIUM` | ni | 1,655 | 2020-01-02 ~ 2026-08-28 |
| 125 | `ni_22_premium_2` | `NI_SPOT_PREMIUM` | ni | 1,655 | 2020-01-02 ~ 2026-08-28 |
| 126 | `ni_22_premium_percentile` | `NI_SPOT_PREMIUM` | ni | 1,655 | 2020-01-02 ~ 2026-08-28 |
| 127 | `ni_22_price` | `NI_FU00014982` | ni | 881 | 2023-02-14 ~ 2026-08-28 |
| 128 | `ni_22_price_2` | `NI_FU00014982` | ni | 881 | 2023-02-14 ~ 2026-08-28 |
| 129 | `ni_22_price_3` | `NI_FU00014982` | ni | 1,660 | 2019-12-31 ~ 2026-08-28 |
| 130 | `ni_22_price_nickel_powder` | `NI_FU00014982` | ni | 36 | 2026-07-10 ~ 2026-08-28 |
| 131 | `ni_23_premium` | `LME_NI` | ni | 1,655 | 2020-01-02 ~ 2026-08-28 |
| 132 | `ni_24_far_price` | `NI_FAR_PRICE` | ni | 1,659 | 2020-01-02 ~ 2026-08-28 |
| 133 | `ni_24_near_price` | `NI_MONTH_SPREAD` | ni | 1,659 | 2020-01-02 ~ 2026-08-28 |
| 134 | `ni_24_price` | `NI_FU00014982` | ni | 1,659 | 2020-01-02 ~ 2026-08-28 |
| 135 | `ni_24_price_2` | `NI_FU00014982` | ni | 1,659 | 2020-01-02 ~ 2026-08-28 |
| 136 | `ni_25_percentile_price` | `NI_PRICE_PERCENTILE` | ni | 1,872 | 2018-10-10 ~ 2026-08-28 |
| 137 | `ni_25_percentile_price_2` | `NI_PRICE_PERCENTILE` | ni | 1,872 | 2018-10-10 ~ 2026-08-28 |
| 138 | `ni_25_price` | `NI_FU00014982` | ni | 1,872 | 2018-10-10 ~ 2026-08-28 |
| 139 | `ni_25_profit` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 140 | `ni_25_profit_2` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 141 | `ni_26_openinterest_top20_front` | `NI_TOP20_LONG` | ni | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 142 | `ni_26_openinterest_top20_front_2` | `NI_TOP20_SHORT` | ni | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 143 | `ni_26_percentile_openinterest_top2` | `NI_HOLD_PERCENTILE` | ni | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 144 | `ni_311_capacity` | `NI_REFINING_CAPACITY` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 145 | `ni_311_capacity_2` | `NI_REFINING_CAPACITY` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 146 | `ni_311_capacity_3` | `NI_REFINING_CAPACITY` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 147 | `ni_311_output` | `NI_REFINING_OUTPUT` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 148 | `ni_311_output_2` | `NI_REFINING_OUTPUT` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 149 | `ni_311_output_3` | `NI_REFINING_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 150 | `ni_311_output_nickel_ore` | `NI_REFINING_OUTPUT` | ni | 11 | 2015-12-31 ~ 2025-12-31 |
| 151 | `ni_311_output_nickel_ore_2` | `NI_REFINING_OUTPUT` | ni | 11 | 2015-12-31 ~ 2025-12-31 |
| 152 | `ni_311_output_nickel_ore_3` | `NI_REFINING_OUTPUT` | ni | 11 | 2015-12-31 ~ 2025-12-31 |
| 153 | `ni_312_nickel_ore_capacity` | `NI_REFINING_CAPACITY` | ni | 91 | 2019-01-31 ~ 2026-07-31 |
| 154 | `ni_312_nickel_ore_capacity_2` | `NI_REFINING_CAPACITY` | ni | 91 | 2019-01-31 ~ 2026-07-31 |
| 155 | `ni_312_output` | `NI_REFINING_OUTPUT` | ni | 45 | 2015-03-31 ~ 2026-03-31 |
| 156 | `ni_312_output_2` | `NI_REFINING_OUTPUT` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 157 | `ni_312_output_3` | `NI_REFINING_OUTPUT` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 158 | `ni_312_output_nickel_ore` | `NI_REFINING_OUTPUT` | ni | 11 | 2015-12-31 ~ 2025-12-31 |
| 159 | `ni_313_import` | `NI_IMPORT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 160 | `ni_313_import_2` | `NI_IMPORT` | ni | 137 | 2015-01-31 ~ 2026-07-31 |
| 161 | `ni_313_output` | `NI_REFINING_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 162 | `ni_313_output_2` | `NI_REFINING_OUTPUT` | ni | 11 | 2015-12-31 ~ 2025-12-31 |
| 163 | `ni_313_output_3` | `NI_REFINING_OUTPUT` | ni | 32 | 2018-03-31 ~ 2025-12-31 |
| 164 | `ni_313_output_nickel_ore` | `NI_REFINING_OUTPUT` | ni | 32 | 2018-03-31 ~ 2025-12-31 |
| 165 | `ni_313_output_nickel_ore_2` | `NI_REFINING_OUTPUT` | ni | 32 | 2018-03-31 ~ 2025-12-31 |
| 166 | `ni_313_output_nickel_ore_3` | `NI_REFINING_OUTPUT` | ni | 32 | 2018-03-31 ~ 2025-12-31 |
| 167 | `ni_313_output_nickel_ore_4` | `NI_REFINING_OUTPUT` | ni | 32 | 2018-03-31 ~ 2025-12-31 |
| 168 | `ni_313_output_nickel_ore_5` | `NI_REFINING_OUTPUT` | ni | 32 | 2018-03-31 ~ 2025-12-31 |
| 169 | `ni_313_output_nickel_ore_6` | `NI_REFINING_OUTPUT` | ni | 32 | 2018-03-31 ~ 2025-12-31 |
| 170 | `ni_314_import` | `NI_IMPORT` | ni | 138 | 2015-01-31 ~ 2026-06-30 |
| 171 | `ni_314_import_2` | `NI_IMPORT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 172 | `ni_314_import_3` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 173 | `ni_314_import_4` | `NI_IMPORT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 174 | `ni_314_import_5` | `NI_IMPORT` | ni | 130 | 2015-06-30 ~ 2026-07-31 |
| 175 | `ni_314_import_6` | `NI_IMPORT` | ni | 71 | 2015-01-31 ~ 2026-04-30 |
| 176 | `ni_314_import_7` | `NI_IMPORT` | ni | 127 | 2015-01-31 ~ 2026-07-31 |
| 177 | `ni_314_import_8` | `NI_IMPORT` | ni | 127 | 2015-01-31 ~ 2026-07-31 |
| 178 | `ni_314_import_9` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 179 | `ni_315_profit` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 180 | `ni_321_capacity_util` | `NI_UTILIZATION` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 181 | `ni_321_output` | `NI_REFINING_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 182 | `ni_321_output_2` | `NI_REFINING_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 183 | `ni_321_output_3` | `NI_REFINING_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 184 | `ni_321_output_4` | `NI_REFINING_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 185 | `ni_321_output_nickel_powder` | `NI_REFINING_OUTPUT` | ni | 79 | 2020-01-31 ~ 2026-07-31 |
| 186 | `ni_322_util` | `NI_UTILIZATION` | ni | 91 | 2019-01-31 ~ 2026-07-31 |
| 187 | `ni_322_util_2` | `NI_UTILIZATION` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 188 | `ni_322_util_3` | `NI_UTILIZATION` | ni | 36 | 2023-08-31 ~ 2026-07-31 |
| 189 | `ni_322_util_4` | `NI_UTILIZATION` | ni | 103 | 2018-01-31 ~ 2026-07-31 |
| 190 | `ni_322_util_5` | `NI_UTILIZATION` | ni | 103 | 2018-01-31 ~ 2026-07-31 |
| 191 | `ni_323_import` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 192 | `ni_323_import_2` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 193 | `ni_323_import_nickel_powder` | `NI_IMPORT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 194 | `ni_323_output_recycle` | `NI_RECYCLE_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 195 | `ni_41_import` | `NI_IMPORT` | ni | 1,775 | 2019-03-01 ~ 2026-08-28 |
| 196 | `ni_41_lme_inv` | `LME_NI_INV` | ni | 2,954 | 2015-01-02 ~ 2026-08-27 |
| 197 | `ni_42_ratio` | `NI_INV_RATIO` | ni | 281 | 2025-07-21 ~ 2026-08-27 |
| 198 | `ni_43_inv` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 199 | `ni_43_inv_2` | `NI_SHFE_INV` | ni | 43 | 2023-01-31 ~ 2026-07-31 |
| 200 | `ni_43_inv_3` | `NI_SHFE_INV` | ni | 43 | 2023-01-31 ~ 2026-07-31 |
| 201 | `ni_43_inv_4` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 202 | `ni_43_inv_implicit` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 203 | `ni_43_inv_percentile` | `NI_SHFE_INV` | ni | 43 | 2023-01-31 ~ 2026-07-31 |
| 204 | `ni_44_inv` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 205 | `ni_44_inv_2` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 206 | `ni_44_inv_3` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 207 | `ni_44_inv_4` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 208 | `ni_44_inv_5` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 209 | `ni_44_inv_6` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 210 | `ni_44_inv_days` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 211 | `ni_44_inv_percentile` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 212 | `ni_45_import` | `NI_IMPORT` | ni | 137 | 2015-01-31 ~ 2026-07-31 |
| 213 | `ni_45_import_2` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 214 | `ni_45_import_3` | `NI_IMPORT` | ni | 137 | 2015-01-31 ~ 2026-07-31 |
| 215 | `ni_45_import_4` | `NI_IMPORT` | ni | 137 | 2015-01-31 ~ 2026-07-31 |
| 216 | `ni_45_inv` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 217 | `ni_45_inv_implicit` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 218 | `ni_45_inv_implicit_2` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 219 | `ni_45_inv_implicit_3` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 220 | `ni_45_inv_implicit_percentile` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 221 | `ni_45_inv_implicit_ratio` | `NI_SHFE_INV` | ni | 500 | 2015-01-30 ~ 2026-08-28 |
| 222 | `ni_51_util` | `NI_UTILIZATION` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 223 | `ni_51_util_battery` | `NI_UTILIZATION` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 224 | `ni_51_util_cons` | `NI_UTILIZATION` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 225 | `ni_52_output` | `NI_DOWNSTREAM_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 226 | `ni_52_output_2` | `NI_DOWNSTREAM_OUTPUT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 227 | `ni_53_import` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 228 | `ni_53_util` | `NI_UTILIZATION` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 229 | `ni_61_import` | `NI_IMPORT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 230 | `ni_61_import_2` | `NI_IMPORT` | ni | 1,801 | 2019-01-02 ~ 2026-08-21 |
| 231 | `ni_61_import_3` | `NI_IMPORT` | ni | 1,775 | 2019-03-01 ~ 2026-08-28 |
| 232 | `ni_61_import_4` | `NI_IMPORT` | ni | 138 | 2015-01-31 ~ 2026-06-30 |
| 233 | `ni_61_import_5` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 234 | `ni_61_import_6` | `NI_IMPORT` | ni | 54 | 2022-02-28 ~ 2026-07-31 |
| 235 | `ni_61_import_nickel_ore` | `NI_IMPORT` | ni | 101 | 2015-06-30 ~ 2026-04-30 |
| 236 | `ni_61_import_nickel_ore_2` | `NI_IMPORT` | ni | 1,801 | 2019-01-02 ~ 2026-08-21 |
| 237 | `ni_61_import_nickel_ore_3` | `NI_IMPORT` | ni | 101 | 2015-06-30 ~ 2026-04-30 |
| 238 | `ni_61_import_nickel_ore_4` | `NI_IMPORT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 239 | `ni_61_import_nickel_ore_5` | `NI_IMPORT` | ni | 130 | 2015-06-30 ~ 2026-07-31 |
| 240 | `ni_61_import_nickel_powder` | `NI_IMPORT` | ni | 1,801 | 2019-01-02 ~ 2026-08-21 |
| 241 | `ni_62_import` | `NI_IMPORT` | ni | 1,775 | 2019-03-01 ~ 2026-08-28 |
| 242 | `ni_62_import_2` | `NI_IMPORT` | ni | 130 | 2015-06-30 ~ 2026-07-31 |
| 243 | `ni_62_import_3` | `NI_IMPORT` | ni | 61 | 2016-02-29 ~ 2026-07-31 |
| 244 | `ni_63_export` | `NI_EXPORT` | ni | 115 | 2017-01-31 ~ 2026-07-31 |
| 245 | `ni_63_export_2` | `NI_EXPORT` | ni | 139 | 2015-01-31 ~ 2026-07-31 |
| 246 | `ni_63_export_3` | `NI_EXPORT` | ni | 28 | 2024-02-29 ~ 2026-06-30 |
| 247 | `ni_63_export_4` | `NI_EXPORT` | ni | 28 | 2024-02-29 ~ 2026-06-30 |
| 248 | `ni_71_cost` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 249 | `ni_71_cost_2` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 250 | `ni_71_cost_3` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 251 | `ni_71_cost_4` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 252 | `ni_71_cost_5` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 253 | `ni_71_cost_nickel_ore` | `NI_REFINING_COST` | ni | 31 | 2018-12-31 ~ 2026-06-30 |
| 254 | `ni_71_cost_nickel_powder` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 255 | `ni_71_cost_percentile` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 256 | `ni_72_profit` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 257 | `ni_72_profit_2` | `NI_SMELTING_PROFIT` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 258 | `ni_72_profit_3` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 259 | `ni_72_profit_4` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 260 | `ni_72_profit_5` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 261 | `ni_72_profit_nickel_powder` | `NI_SMELTING_PROFIT` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 262 | `ni_72_profit_percentile` | `NI_SMELTING_PROFIT` | ni | 1,745 | 2019-08-14 ~ 2026-08-28 |
| 263 | `ni_73_cost` | `NI_REFINING_COST` | ni | 2,320 | 2017-02-06 ~ 2026-08-28 |
| 264 | `ni_73_cost_2` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 265 | `ni_73_cost_3` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 266 | `ni_73_cost_4` | `NI_REFINING_COST` | ni | 890 | 2023-01-03 ~ 2026-08-28 |
| 267 | `si_21_basis_industrial_si` | `SI_BASIS` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 268 | `si_21_close_front_industrial_si` | `SI_FU00015015` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 269 | `si_21_openinterest` | `SI_HOLD_OPEN` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 270 | `si_21_openinterest_2` | `SI_HOLD_OPEN` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 271 | `si_21_openinterest_industrial_si` | `SI_HOLD_OPEN` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 272 | `si_21_openinterest_industrial_si_2` | `SI_HOLD_OPEN` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 273 | `si_21_openinterest_longshort_indus` | `SI_LONG_SHORT_RATIO` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 274 | `si_21_percentile_openinterest_indu` | `SI_HOLD_PERCENTILE` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 275 | `si_21_volume_industrial_si` | `(unmapped)` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 276 | `si_21_warrant_industrial_si` | `SI_SPOT_PREMIUM` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 277 | `si_22_basis_industrial_si` | `SI_BASIS` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 278 | `si_22_price_industrial_si` | `SI_FU00015015` | si | 114 | 2017-01-31 ~ 2026-06-30 |
| 279 | `si_22_warrant_industrial_si` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 280 | `si_23_close` | `SI_MONTH_SPREAD` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 281 | `si_23_close_2` | `SI_FU00015015` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 282 | `si_24_basis_industrial_si` | `SI_BASIS` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 283 | `si_24_close_far_industrial_si` | `SI_FU00015015` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 284 | `si_24_close_near_industrial_si` | `SI_FU00015015` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 285 | `si_24_warrant_industrial_si` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 286 | `si_25_close_front_polysilicon` | `LME_SI` | si | 406 | 2024-12-26 ~ 2026-08-28 |
| 287 | `si_25_cost_industrial_si` | `SI_REFINING_COST` | si | 187 | 2022-12-16 ~ 2026-08-28 |
| 288 | `si_25_cost_polysilicon` | `SI_REFINING_COST` | si | 148 | 2023-09-15 ~ 2026-08-28 |
| 289 | `si_25_profit` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 290 | `si_25_profit_2` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 291 | `si_25_profit_industrial_si` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 292 | `si_25_profit_percentile_industrial` | `SI_PRICE_PERCENTILE` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 293 | `si_25_profit_polysilicon` | `SI_SMELTING_PROFIT` | si | 1,106 | 2022-03-22 ~ 2026-08-28 |
| 294 | `si_26_openinterest_longshort_indus` | `SI_LONG_SHORT_RATIO` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 295 | `si_26_openinterest_longshort_top20` | `SI_TOP20_LONG` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 296 | `si_26_openinterest_longshort_top20_2` | `SI_TOP20_SHORT` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 297 | `si_26_openinterest_top20` | `SI_TOP20_LONG` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 298 | `si_26_openinterest_top20_2` | `SI_TOP20_SHORT` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 299 | `si_26_openinterest_top20_industria` | `SI_TOP20_LONG` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 300 | `si_26_openinterest_top20_industria_2` | `SI_TOP20_SHORT` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 301 | `si_26_percentile_openinterest_indu` | `SI_HOLD_PERCENTILE` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 302 | `si_26_volume_industrial_si` | `(unmapped)` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 303 | `si_311_capacity_util` | `SI_UTILIZATION` | si | 94 | 2016-08-31 ~ 2026-07-31 |
| 304 | `si_311_output` | `SI_REFINING_OUTPUT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 305 | `si_311_output_recycle` | `SI_RECYCLE_OUTPUT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 306 | `si_311_util` | `SI_UTILIZATION` | si | 320 | 2019-10-11 ~ 2026-08-28 |
| 307 | `si_312_capacity` | `SI_REFINING_CAPACITY` | si | 120 | 2016-06-30 ~ 2026-07-31 |
| 308 | `si_312_capacity_util` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 309 | `si_312_capacity_util_2` | `SI_UTILIZATION` | si | 126 | 2016-01-31 ~ 2026-06-30 |
| 310 | `si_312_import` | `SI_IMPORT` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 311 | `si_312_import_2` | `SI_IMPORT` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 312 | `si_312_output_recycle` | `SI_RECYCLE_OUTPUT` | si | 52 | 2022-04-30 ~ 2026-07-31 |
| 313 | `si_312_output_recycle_2` | `SI_RECYCLE_OUTPUT` | si | 8 | 2015-12-31 ~ 2022-12-31 |
| 314 | `si_312_util` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 315 | `si_312_util_2` | `SI_UTILIZATION` | si | 363 | 2019-07-26 ~ 2026-08-28 |
| 316 | `si_312_util_3` | `SI_UTILIZATION` | si | 363 | 2019-07-26 ~ 2026-08-28 |
| 317 | `si_314_import` | `SI_IMPORT` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 318 | `si_314_import_2` | `SI_IMPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 319 | `si_314_import_3` | `SI_IMPORT` | si | 118 | 2015-03-31 ~ 2026-07-31 |
| 320 | `si_314_import_4` | `SI_IMPORT` | si | 118 | 2015-03-31 ~ 2026-07-31 |
| 321 | `si_314_import_ratio` | `SI_IMPORT` | si | 3 | 2020-12-31 ~ 2024-12-31 |
| 322 | `si_315_capacity_util_industrial_si` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 323 | `si_315_import_industrial_si` | `SI_IMPORT` | si | 118 | 2015-03-31 ~ 2026-07-31 |
| 324 | `si_315_util_industrial_si` | `SI_UTILIZATION` | si | 106 | 2024-08-02 ~ 2026-08-28 |
| 325 | `si_321_capacity` | `SI_REFINING_CAPACITY` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 326 | `si_321_capacity_industrial_si` | `SI_REFINING_CAPACITY` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 327 | `si_321_capacity_polysilicon` | `SI_REFINING_CAPACITY` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 328 | `si_321_capacity_util_industrial_si` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 329 | `si_321_output_polysilicon` | `SI_REFINING_OUTPUT` | si | 126 | 2016-01-31 ~ 2026-06-30 |
| 330 | `si_321_util_industrial_si` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 331 | `si_321_util_polysilicon` | `SI_UTILIZATION` | si | 363 | 2019-07-26 ~ 2026-08-28 |
| 332 | `si_322_util` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 333 | `si_322_util_2` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 334 | `si_322_util_3` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 335 | `si_323_output_recycle_polysilicon` | `SI_RECYCLE_OUTPUT` | si | 126 | 2016-01-31 ~ 2026-06-30 |
| 336 | `si_323_recycle_capacity` | `SI_RECYCLE_CAPACITY` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 337 | `si_323_recycle_capacity_industrial_` | `SI_RECYCLE_CAPACITY` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 338 | `si_323_recycle_capacity_polysilicon` | `SI_RECYCLE_CAPACITY` | si | 11 | 2015-12-31 ~ 2025-12-31 |
| 339 | `si_323_recycle_capacity_util` | `SI_RECYCLE_UTIL` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 340 | `si_323_util_recycle_industrial_si` | `SI_UTILIZATION` | si | 51 | 2022-05-31 ~ 2026-07-31 |
| 341 | `si_323_util_recycle_polysilicon` | `SI_UTILIZATION` | si | 363 | 2019-07-26 ~ 2026-08-28 |
| 342 | `si_324_profit` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 343 | `si_324_profit_2` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 344 | `si_41_inv_polysilicon` | `SI_SHFE_INV` | si | 133 | 2024-01-05 ~ 2026-08-28 |
| 345 | `si_42_warrant` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 346 | `si_42_warrant_2` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 347 | `si_42_warrant_industrial_si` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 348 | `si_42_warrant_polysilicon` | `SI_WARRANT` | si | 343 | 2025-04-03 ~ 2026-08-28 |
| 349 | `si_42_warrant_ratio_industrial_si` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 350 | `si_44_inv_days_polysilicon` | `SI_SHFE_INV` | si | 133 | 2024-01-05 ~ 2026-08-28 |
| 351 | `si_44_inv_polysilicon` | `SI_SHFE_INV` | si | 133 | 2024-01-05 ~ 2026-08-28 |
| 352 | `si_45_inv_implicit_polysilicon` | `SI_SHFE_INV` | si | 133 | 2024-01-05 ~ 2026-08-28 |
| 353 | `si_45_inv_polysilicon` | `SI_SHFE_INV` | si | 133 | 2024-01-05 ~ 2026-08-28 |
| 354 | `si_51_cons` | `SI_CONSUMPTION` | si | 6 | 2017-12-31 ~ 2022-12-31 |
| 355 | `si_51_output_polysilicon` | `SI_DOWNSTREAM_OUTPUT` | si | 126 | 2016-01-31 ~ 2026-06-30 |
| 356 | `si_51_util` | `SI_UTILIZATION` | si | 106 | 2024-08-02 ~ 2026-08-28 |
| 357 | `si_51_util_industrial_si` | `SI_UTILIZATION` | si | 106 | 2024-08-02 ~ 2026-08-28 |
| 358 | `si_52_output_polysilicon` | `SI_DOWNSTREAM_OUTPUT` | si | 126 | 2016-01-31 ~ 2026-06-30 |
| 359 | `si_61_import` | `SI_IMPORT` | si | 118 | 2015-03-31 ~ 2026-07-31 |
| 360 | `si_61_import_2` | `SI_IMPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 361 | `si_61_import_industrial_si` | `SI_IMPORT` | si | 118 | 2015-03-31 ~ 2026-07-31 |
| 362 | `si_61_import_industrial_si_2` | `SI_IMPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 363 | `si_61_import_industrial_si_3` | `SI_IMPORT` | si | 118 | 2015-03-31 ~ 2026-07-31 |
| 364 | `si_61_import_industrial_si_4` | `SI_IMPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 365 | `si_61_import_polysilicon` | `SI_IMPORT` | si | 129 | 2015-01-31 ~ 2026-05-31 |
| 366 | `si_61_import_polysilicon_2` | `SI_IMPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 367 | `si_61_import_shipment_days` | `SI_IMPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 368 | `si_61_import_tariff_industrial_si` | `SI_IMPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 369 | `si_62_export_industrial_si` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 370 | `si_62_export_polysilicon` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 371 | `si_62_export_shipment_days` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 372 | `si_62_export_tariff_industrial_si` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 373 | `si_62_warrant_industrial_si` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 374 | `si_63_export_industrial_si` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 375 | `si_63_export_polysilicon` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 376 | `si_63_export_shipment_days` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 377 | `si_63_export_tariff_industrial_si` | `SI_EXPORT` | si | 139 | 2015-01-31 ~ 2026-07-31 |
| 378 | `si_63_warrant_industrial_si` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 379 | `si_64_warrant_shipment_industrial_` | `SI_WARRANT` | si | 774 | 2023-06-20 ~ 2026-08-28 |
| 380 | `si_71_close_front` | `SI_FU00015015` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 381 | `si_71_cost` | `SI_REFINING_COST` | si | 187 | 2022-12-16 ~ 2026-08-28 |
| 382 | `si_71_cost_2` | `SI_REFINING_COST` | si | 187 | 2022-12-16 ~ 2026-08-28 |
| 383 | `si_71_cost_3` | `SI_REFINING_COST` | si | 187 | 2022-12-16 ~ 2026-08-28 |
| 384 | `si_71_cost_industrial_si_2` | `SI_REFINING_COST` | si | 187 | 2022-12-16 ~ 2026-08-28 |
| 385 | `si_71_cost_industrial_si_3` | `SI_REFINING_COST` | si | 41 | 2025-11-21 ~ 2026-08-28 |
| 386 | `si_71_cost_percentile_industrial_s` | `SI_REFINING_COST` | si | 187 | 2022-12-16 ~ 2026-08-28 |
| 387 | `si_72_profit` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 388 | `si_72_profit_2` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 389 | `si_72_profit_3` | `SI_SMELTING_PROFIT` | si | 186 | 2022-12-16 ~ 2026-08-28 |
| 390 | `si_72_profit_industrial_si` | `SI_SMELTING_PROFIT` | si | 41 | 2025-11-21 ~ 2026-08-28 |
| 391 | `sn_21_basis` | `SN_BASIS` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 392 | `sn_21_close` | `SN_FU00014952` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 393 | `sn_21_close_2` | `SN_FU00014952` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 394 | `sn_21_close_front` | `SN_FU00014952` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 395 | `sn_21_openinterest` | `SN_HOLD_OPEN` | sn | 345 | 2020-01-03 ~ 2026-08-21 |
| 396 | `sn_21_openinterest_2` | `SN_HOLD_OPEN` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 397 | `sn_21_openinterest_3` | `SN_LONG_SHORT_RATIO` | sn | 345 | 2020-01-03 ~ 2026-08-21 |
| 398 | `sn_21_openinterest_4` | `SN_HOLD_OPEN` | sn | 345 | 2020-01-03 ~ 2026-08-21 |
| 399 | `sn_21_premium` | `SN_SPOT_PREMIUM` | sn | 2,834 | 2015-01-05 ~ 2026-08-28 |
| 400 | `sn_21_volume` | `(unmapped)` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 401 | `sn_22_import` | `SN_IMPORT` | sn | 1,587 | 2020-01-02 ~ 2026-08-28 |
| 402 | `sn_22_premium` | `SN_MONTH_SPREAD` | sn | 1,538 | 2020-05-06 ~ 2026-08-28 |
| 403 | `sn_22_premium_2` | `SN_SPOT_PREMIUM` | sn | 1,538 | 2020-05-06 ~ 2026-08-28 |
| 404 | `sn_22_premium_3` | `SN_SPOT_PREMIUM` | sn | 1,538 | 2020-05-06 ~ 2026-08-28 |
| 405 | `sn_22_premium_4` | `SN_SPOT_PREMIUM` | sn | 1,538 | 2020-05-06 ~ 2026-08-28 |
| 406 | `sn_22_price` | `SN_FU00014952` | sn | 1,752 | 2019-04-26 ~ 2026-08-28 |
| 407 | `sn_23_close` | `SN_FU00014952` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 408 | `sn_23_close_2` | `SN_FU00014952` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 409 | `sn_23_import` | `SN_IMPORT` | sn | 1,587 | 2020-01-02 ~ 2026-08-28 |
| 410 | `sn_23_lme_close` | `LME_SN` | sn | 1,122 | 2022-03-21 ~ 2026-08-28 |
| 411 | `sn_23_lme_inv` | `LME_SN_INV` | sn | 43 | 2023-01-31 ~ 2026-07-31 |
| 412 | `sn_25_price` | `SN_FU00014952` | sn | 1,825 | 2019-04-15 ~ 2026-08-28 |
| 413 | `sn_25_recycle_price` | `SN_RECYCLE_OUTPUT` | sn | 821 | 2023-04-14 ~ 2026-08-28 |
| 414 | `sn_26_openinterest_top20` | `SN_TOP20_LONG` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 415 | `sn_26_openinterest_top20_2` | `SN_TOP20_SHORT` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 416 | `sn_26_openinterest_top20_3` | `SN_TOP20_LONG` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 417 | `sn_26_openinterest_top20_4` | `SN_TOP20_LONG` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 418 | `sn_26_openinterest_top20_5` | `SN_TOP20_LONG` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 419 | `sn_311_output` | `SN_REFINING_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 420 | `sn_311_output_2` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 421 | `sn_311_output_3` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 422 | `sn_311_output_tin_ore` | `SN_REFINING_OUTPUT` | sn | 11 | 2015-12-31 ~ 2025-12-31 |
| 423 | `sn_311_output_tin_ore_2` | `SN_REFINING_OUTPUT` | sn | 28 | 2019-06-30 ~ 2026-03-31 |
| 424 | `sn_312_output` | `SN_REFINING_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 425 | `sn_312_output_2` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 426 | `sn_312_output_3` | `SN_REFINING_OUTPUT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 427 | `sn_312_output_4` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 428 | `sn_312_output_5` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 429 | `sn_312_output_6` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 430 | `sn_312_output_ratio` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 431 | `sn_312_output_ratio_2` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 432 | `sn_312_output_ratio_3` | `SN_REFINING_OUTPUT` | sn | 101 | 2018-01-31 ~ 2026-05-31 |
| 433 | `sn_313_import_tin_ore` | `SN_IMPORT` | sn | 139 | 2015-01-31 ~ 2026-07-31 |
| 434 | `sn_313_output` | `SN_REFINING_OUTPUT` | sn | 9 | 2015-12-31 ~ 2023-12-31 |
| 435 | `sn_313_output_tin_ore` | `SN_REFINING_OUTPUT` | sn | 28 | 2019-06-30 ~ 2026-03-31 |
| 436 | `sn_313_tc_tc` | `SN_TC` | sn | 2,333 | 2017-03-09 ~ 2026-08-28 |
| 437 | `sn_313_tc_tc_2` | `SN_TC` | sn | 2,333 | 2017-03-09 ~ 2026-08-28 |
| 438 | `sn_314_import` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 439 | `sn_314_import_2` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 440 | `sn_314_import_3` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 441 | `sn_314_import_4` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 442 | `sn_314_import_5` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 443 | `sn_314_import_tin_ore` | `SN_IMPORT` | sn | 139 | 2015-01-31 ~ 2026-07-31 |
| 444 | `sn_314_import_tin_ore_2` | `SN_IMPORT` | sn | 100 | 2015-08-31 ~ 2026-06-30 |
| 445 | `sn_314_import_tin_ore_3` | `SN_IMPORT` | sn | 104 | 2015-01-31 ~ 2026-06-30 |
| 446 | `sn_314_import_tin_ore_4` | `SN_IMPORT` | sn | 106 | 2017-09-30 ~ 2026-07-31 |
| 447 | `sn_314_import_tin_ore_5` | `SN_IMPORT` | sn | 139 | 2015-01-31 ~ 2026-07-31 |
| 448 | `sn_321_import` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 449 | `sn_321_output` | `SN_REFINING_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 450 | `sn_321_util` | `SN_UTILIZATION` | sn | 64 | 2021-04-30 ~ 2026-07-31 |
| 451 | `sn_321_util_2` | `SN_UTILIZATION` | sn | 64 | 2021-04-30 ~ 2026-07-31 |
| 452 | `sn_323_import_recycle` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 453 | `sn_323_output_recycle` | `SN_RECYCLE_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 454 | `sn_323_output_recycle_2` | `SN_RECYCLE_OUTPUT` | sn | 11 | 2015-12-31 ~ 2025-12-31 |
| 455 | `sn_323_output_recycle_3` | `SN_RECYCLE_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 456 | `sn_323_output_recycle_4` | `SN_RECYCLE_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 457 | `sn_323_recycle_capacity` | `SN_RECYCLE_CAPACITY` | sn | 8 | 2015-12-31 ~ 2024-12-31 |
| 458 | `sn_41_lme_inv` | `LME_SN_INV` | sn | 43 | 2023-01-31 ~ 2026-07-31 |
| 459 | `sn_41_warrant` | `SN_WARRANT` | sn | 3,180 | 2015-01-02 ~ 2026-08-28 |
| 460 | `sn_42_ratio` | `SN_INV_RATIO` | sn | 2,496 | 2016-07-01 ~ 2026-08-28 |
| 461 | `sn_42_warrant` | `SN_WARRANT` | sn | 3,185 | 2015-01-02 ~ 2026-08-28 |
| 462 | `sn_42_warrant_2` | `SN_WARRANT` | sn | 3,185 | 2015-01-02 ~ 2026-08-28 |
| 463 | `sn_43_inv` | `SN_SHFE_INV` | sn | 333 | 2020-01-03 ~ 2026-08-28 |
| 464 | `sn_43_inv_2` | `SN_SHFE_INV` | sn | 333 | 2020-01-03 ~ 2026-08-28 |
| 465 | `sn_43_inv_plant` | `SN_SHFE_INV` | sn | 45 | 2022-11-30 ~ 2026-07-31 |
| 466 | `sn_43_ratio` | `SN_INV_RATIO` | sn | 2,496 | 2016-07-01 ~ 2026-08-28 |
| 467 | `sn_51_cons` | `SN_CONSUMPTION` | sn | 10 | 2015-12-31 ~ 2024-12-31 |
| 468 | `sn_51_output` | `SN_DOWNSTREAM_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 469 | `sn_52_output` | `SN_DOWNSTREAM_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 470 | `sn_52_output_2` | `SN_DOWNSTREAM_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 471 | `sn_52_output_3` | `SN_DOWNSTREAM_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 472 | `sn_52_output_4` | `SN_DOWNSTREAM_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 473 | `sn_52_output_5` | `SN_DOWNSTREAM_OUTPUT` | sn | 41 | 2016-03-31 ~ 2026-03-31 |
| 474 | `sn_61_import` | `SN_IMPORT` | sn | 79 | 2020-01-31 ~ 2026-07-31 |
| 475 | `sn_61_import_2` | `SN_IMPORT` | sn | 79 | 2020-01-31 ~ 2026-07-31 |
| 476 | `sn_61_import_3` | `SN_IMPORT` | sn | 79 | 2020-01-31 ~ 2026-07-31 |
| 477 | `sn_61_import_4` | `SN_IMPORT` | sn | 79 | 2020-01-31 ~ 2026-07-31 |
| 478 | `sn_61_import_5` | `SN_IMPORT` | sn | 9 | 2015-12-31 ~ 2023-12-31 |
| 479 | `sn_61_import_recycle` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 480 | `sn_61_import_recycle_2` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 481 | `sn_61_import_recycle_3` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 482 | `sn_62_export` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 483 | `sn_62_export_3` | `SN_EXPORT` | sn | 139 | 2015-01-31 ~ 2026-07-31 |
| 484 | `sn_62_export_4` | `SN_EXPORT` | sn | 139 | 2015-01-31 ~ 2026-07-31 |
| 485 | `sn_62_export_5` | `SN_EXPORT` | sn | 139 | 2015-01-31 ~ 2026-07-31 |
| 486 | `sn_62_import` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 487 | `sn_62_import_2` | `SN_IMPORT` | sn | 45 | 2015-03-31 ~ 2026-03-31 |
| 488 | `sn_63_export` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 489 | `sn_63_export_2` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 490 | `sn_63_export_3` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 491 | `sn_63_export_4` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 492 | `sn_63_export_5` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 493 | `sn_63_export_6` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-07-31 |
| 494 | `sn_63_export_ratio` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 495 | `sn_63_export_ratio_2` | `SN_EXPORT` | sn | 137 | 2015-01-31 ~ 2026-05-31 |
| 496 | `sn_71_cost` | `SN_REFINING_COST` | sn | 1,686 | 2019-11-06 ~ 2026-08-28 |
| 497 | `sn_71_cost_2` | `SN_REFINING_COST` | sn | 1,686 | 2019-11-06 ~ 2026-08-28 |
| 498 | `sn_71_cost_3` | `SN_REFINING_COST` | sn | 1,686 | 2019-11-06 ~ 2026-08-28 |
| 499 | `sn_71_cost_percentile` | `SN_PRICE_PERCENTILE` | sn | 1,686 | 2019-11-06 ~ 2026-08-28 |
| 500 | `sn_71_tc` | `SN_TC` | sn | 2,362 | 2017-01-03 ~ 2026-08-28 |
| 501 | `sn_71_tc_2` | `SN_TC` | sn | 2,362 | 2017-01-03 ~ 2026-08-28 |
| 502 | `sn_71_tc_3` | `SN_TC` | sn | 2,362 | 2017-01-03 ~ 2026-08-28 |
| 503 | `sn_72_tc` | `SN_SMELTING_PROFIT` | sn | 2,362 | 2017-01-03 ~ 2026-08-28 |
| 504 | `sn_72_tc_2` | `SN_TC` | sn | 2,362 | 2017-01-03 ~ 2026-08-28 |
| 505 | `sn_73_price` | `SN_FU00014952` | sn | 1,825 | 2019-04-15 ~ 2026-08-28 |
| 506 | `sn_73_price_2` | `SN_FU00014952` | sn | 1,825 | 2019-04-15 ~ 2026-08-28 |
| 507 | `zn_21_basis` | `ZN_BASIS` | zn | 2,834 | 2015-01-05 ~ 2026-08-28 |
| 508 | `zn_21_close` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 509 | `zn_21_close_2` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 510 | `zn_21_close_far` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 511 | `zn_21_close_front` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 512 | `zn_21_close_near` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 513 | `zn_21_import` | `ZN_IMPORT` | zn | 2,299 | 2016-12-16 ~ 2026-08-28 |
| 514 | `zn_21_openinterest` | `ZN_HOLD_OPEN` | zn | 345 | 2020-01-03 ~ 2026-08-21 |
| 515 | `zn_21_premium` | `ZN_SPOT_PREMIUM` | zn | 2,294 | 2017-01-03 ~ 2026-08-28 |
| 516 | `zn_21_volume` | `(unmapped)` | zn | 1,128 | 2022-02-28 ~ 2026-08-27 |
| 517 | `zn_22_lme_inv` | `LME_ZN_INV` | zn | 43 | 2023-01-31 ~ 2026-07-31 |
| 518 | `zn_22_premium` | `ZN_SPOT_PREMIUM` | zn | 2,295 | 2017-01-03 ~ 2026-08-28 |
| 519 | `zn_22_premium_2` | `ZN_SPOT_PREMIUM` | zn | 2,294 | 2017-01-03 ~ 2026-08-28 |
| 520 | `zn_22_premium_3` | `ZN_SPOT_PREMIUM` | zn | 2,295 | 2017-01-03 ~ 2026-08-28 |
| 521 | `zn_22_premium_4` | `ZN_SPOT_PREMIUM` | zn | 2,294 | 2017-01-03 ~ 2026-08-28 |
| 522 | `zn_23_close` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 523 | `zn_23_close_2` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 524 | `zn_23_close_front` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 525 | `zn_23_lme_close` | `LME_ZN` | zn | 1,122 | 2022-03-21 ~ 2026-08-28 |
| 526 | `zn_24_close_near` | `ZN_FU00014950` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 527 | `zn_25_cost_conc` | `ZN_REFINING_COST` | zn | 13 | 2015-06-30 ~ 2025-12-31 |
| 528 | `zn_25_profit` | `ZN_SMELTING_PROFIT` | zn | 46 | 2015-03-31 ~ 2026-06-30 |
| 529 | `zn_25_profit_2` | `ZN_SMELTING_PROFIT` | zn | 46 | 2015-03-31 ~ 2026-06-30 |
| 530 | `zn_25_profit_3` | `ZN_SMELTING_PROFIT` | zn | 46 | 2015-03-31 ~ 2026-06-30 |
| 531 | `zn_25_profit_percentile` | `ZN_PRICE_PERCENTILE` | zn | 13 | 2015-06-30 ~ 2025-12-31 |
| 532 | `zn_25_tc_conc` | `ZN_TC` | zn | 946 | 2022-11-15 ~ 2026-08-28 |
| 533 | `zn_25_tc_conc_2` | `ZN_TC` | zn | 1,081 | 2022-04-29 ~ 2026-08-28 |
| 534 | `zn_26_openinterest` | `ZN_TOP20_SHORT` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 535 | `zn_26_openinterest_2` | `ZN_HOLD_OPEN` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 536 | `zn_26_openinterest_3` | `ZN_HOLD_OPEN` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 537 | `zn_26_openinterest_top20` | `ZN_TOP20_LONG` | zn | 2,833 | 2015-01-05 ~ 2026-08-28 |
| 538 | `zn_311_import` | `ZN_IMPORT` | zn | 136 | 2015-01-31 ~ 2026-07-31 |
| 539 | `zn_311_import_2` | `ZN_IMPORT` | zn | 136 | 2015-01-31 ~ 2026-07-31 |
| 540 | `zn_311_output` | `ZN_REFINING_OUTPUT` | zn | 138 | 2015-01-31 ~ 2026-06-30 |
| 541 | `zn_311_output_2` | `ZN_REFINING_OUTPUT` | zn | 35 | 2017-12-31 ~ 2026-06-30 |
| 542 | `zn_311_output_3` | `ZN_REFINING_OUTPUT` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 543 | `zn_311_output_4` | `ZN_REFINING_OUTPUT` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 544 | `zn_311_output_recycle` | `ZN_RECYCLE_OUTPUT` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 545 | `zn_312_import` | `ZN_IMPORT` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 546 | `zn_312_import_2` | `ZN_IMPORT` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 547 | `zn_312_import_3` | `ZN_IMPORT` | zn | 6 | 2019-12-31 ~ 2024-12-31 |
| 548 | `zn_312_import_4` | `ZN_IMPORT` | zn | 122 | 2015-05-31 ~ 2026-07-31 |
| 549 | `zn_312_output` | `ZN_REFINING_OUTPUT` | zn | 11 | 2015-12-31 ~ 2025-12-31 |
| 550 | `zn_312_output_2` | `ZN_REFINING_OUTPUT` | zn | 45 | 2015-03-31 ~ 2026-03-31 |
| 551 | `zn_312_output_3` | `ZN_REFINING_OUTPUT` | zn | 11 | 2015-12-31 ~ 2025-12-31 |
| 552 | `zn_312_output_4` | `ZN_REFINING_OUTPUT` | zn | 9 | 2015-12-31 ~ 2023-12-31 |
| 553 | `zn_312_output_5` | `ZN_REFINING_OUTPUT` | zn | 45 | 2015-03-31 ~ 2026-03-31 |
| 554 | `zn_312_output_6` | `ZN_REFINING_OUTPUT` | zn | 9 | 2015-12-31 ~ 2023-12-31 |
| 555 | `zn_312_output_7` | `ZN_REFINING_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 556 | `zn_312_output_8` | `ZN_REFINING_OUTPUT` | zn | 9 | 2015-12-31 ~ 2023-12-31 |
| 557 | `zn_312_output_9` | `ZN_REFINING_OUTPUT` | zn | 9 | 2015-12-31 ~ 2023-12-31 |
| 558 | `zn_312_output_recycle` | `ZN_RECYCLE_OUTPUT` | zn | 11 | 2015-12-31 ~ 2025-12-31 |
| 559 | `zn_312_output_recycle_2` | `ZN_RECYCLE_OUTPUT` | zn | 11 | 2015-12-31 ~ 2025-12-31 |
| 560 | `zn_312_output_recycle_3` | `ZN_RECYCLE_OUTPUT` | zn | 11 | 2015-12-31 ~ 2025-12-31 |
| 561 | `zn_312_output_recycle_4` | `ZN_RECYCLE_OUTPUT` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 562 | `zn_313_output` | `ZN_REFINING_OUTPUT` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 563 | `zn_313_output_2` | `ZN_REFINING_OUTPUT` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 564 | `zn_313_output_recycle` | `ZN_RECYCLE_OUTPUT` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 565 | `zn_314_import` | `ZN_IMPORT` | zn | 2,299 | 2016-12-16 ~ 2026-08-28 |
| 566 | `zn_314_import_2` | `ZN_IMPORT` | zn | 136 | 2015-01-31 ~ 2026-07-31 |
| 567 | `zn_314_import_3` | `ZN_IMPORT` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 568 | `zn_314_import_4` | `ZN_IMPORT` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 569 | `zn_314_import_5` | `ZN_IMPORT` | zn | 114 | 2015-05-31 ~ 2026-06-30 |
| 570 | `zn_314_import_6` | `ZN_IMPORT` | zn | 114 | 2015-05-31 ~ 2026-06-30 |
| 571 | `zn_315_tc` | `ZN_TC` | zn | 1,081 | 2022-04-29 ~ 2026-08-28 |
| 572 | `zn_315_tc_2` | `ZN_TC` | zn | 1,081 | 2022-04-29 ~ 2026-08-28 |
| 573 | `zn_315_tc_percentile` | `ZN_TC` | zn | 1,081 | 2022-04-29 ~ 2026-08-28 |
| 574 | `zn_321_capacity_util` | `ZN_UTILIZATION` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 575 | `zn_321_import` | `ZN_IMPORT` | zn | 52 | 2018-07-31 ~ 2026-07-31 |
| 576 | `zn_321_import_2` | `ZN_IMPORT` | zn | 52 | 2018-07-31 ~ 2026-07-31 |
| 577 | `zn_321_output` | `ZN_REFINING_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 578 | `zn_321_output_recycle` | `ZN_RECYCLE_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 579 | `zn_323_import_recycle` | `ZN_IMPORT` | zn | 133 | 2015-01-31 ~ 2026-07-31 |
| 580 | `zn_323_import_recycle_2` | `ZN_IMPORT` | zn | 133 | 2015-01-31 ~ 2026-07-31 |
| 581 | `zn_323_import_recycle_3` | `ZN_IMPORT` | zn | 2,299 | 2016-12-16 ~ 2026-08-28 |
| 582 | `zn_323_output` | `ZN_REFINING_OUTPUT` | zn | 91 | 2019-01-31 ~ 2026-07-31 |
| 583 | `zn_323_output_recycle` | `ZN_RECYCLE_OUTPUT` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 584 | `zn_323_recycle_capacity_util` | `ZN_RECYCLE_UTIL` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 585 | `zn_41_inv` | `ZN_SHFE_INV` | zn | 517 | 2016-09-23 ~ 2026-08-28 |
| 586 | `zn_41_inv_2` | `ZN_SHFE_INV` | zn | 517 | 2016-09-23 ~ 2026-08-28 |
| 587 | `zn_41_lme_warrant` | `LME_ZN_INV` | zn | 3,180 | 2015-01-02 ~ 2026-08-28 |
| 588 | `zn_42_inv_implicit` | `ZN_SHFE_INV` | zn | 517 | 2016-09-23 ~ 2026-08-28 |
| 589 | `zn_43_inv` | `ZN_SHFE_INV` | zn | 517 | 2016-09-23 ~ 2026-08-28 |
| 590 | `zn_43_inv_2` | `ZN_SHFE_INV` | zn | 517 | 2016-09-23 ~ 2026-08-28 |
| 591 | `zn_43_premium` | `ZN_INV_RATIO` | zn | 2,294 | 2017-01-03 ~ 2026-08-28 |
| 592 | `zn_44_inv` | `ZN_SHFE_INV` | zn | 517 | 2016-09-23 ~ 2026-08-28 |
| 593 | `zn_44_inv_2` | `ZN_SHFE_INV` | zn | 517 | 2016-09-23 ~ 2026-08-28 |
| 594 | `zn_44_inv_plant` | `ZN_SHFE_INV` | zn | 543 | 2016-01-01 ~ 2026-08-21 |
| 595 | `zn_44_inv_plant_2` | `ZN_SHFE_INV` | zn | 543 | 2016-01-01 ~ 2026-08-21 |
| 596 | `zn_51_cons` | `ZN_CONSUMPTION` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 597 | `zn_51_cons_2` | `ZN_CONSUMPTION` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 598 | `zn_51_cons_3` | `ZN_CONSUMPTION` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 599 | `zn_51_output` | `ZN_DOWNSTREAM_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 600 | `zn_52_cons` | `ZN_CONSUMPTION` | zn | 9 | 2015-12-31 ~ 2023-12-31 |
| 601 | `zn_52_output` | `ZN_DOWNSTREAM_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 602 | `zn_52_output_battery` | `ZN_DOWNSTREAM_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 603 | `zn_52_util` | `ZN_UTILIZATION` | zn | 528 | 2016-07-08 ~ 2026-08-28 |
| 604 | `zn_52_util_2` | `ZN_UTILIZATION` | zn | 139 | 2015-01-31 ~ 2026-07-31 |
| 605 | `zn_61_inv_conc` | `ZN_SHFE_INV` | zn | 227 | 2022-04-01 ~ 2026-08-28 |
| 606 | `zn_62_import` | `ZN_IMPORT` | zn | 52 | 2018-07-31 ~ 2026-07-31 |
| 607 | `zn_62_import_2` | `ZN_IMPORT` | zn | 52 | 2018-07-31 ~ 2026-07-31 |
| 608 | `zn_62_import_3` | `ZN_IMPORT` | zn | 52 | 2018-07-31 ~ 2026-07-31 |
| 609 | `zn_63_output` | `ZN_EXPORT` | zn | 91 | 2019-01-31 ~ 2026-07-31 |
| 610 | `zn_64_inv` | `ZN_SHFE_INV` | zn | 8 | 2017-12-31 ~ 2024-12-31 |
| 611 | `zn_71_cost` | `ZN_REFINING_COST` | zn | 1,860 | 2018-10-25 ~ 2026-08-28 |
| 612 | `zn_71_cost_2` | `ZN_REFINING_COST` | zn | 1,860 | 2018-10-25 ~ 2026-08-28 |
| 613 | `zn_72_output` | `ZN_DOWNSTREAM_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 614 | `zn_72_output_2` | `ZN_DOWNSTREAM_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |
| 615 | `zn_72_output_3` | `ZN_DOWNSTREAM_OUTPUT` | zn | 115 | 2017-01-31 ~ 2026-07-31 |

## 4. Unmapped Indicators Detail

> 7 indicators have no indicator_id_mapped mapping.

| # | indicator_id | commodity | records | date_range |
|---|-------------|-----------|--------:|------------|
| 1 | `li_21_volume` | li | 754 | 2023-07-21 ~ 2026-08-28 |
| 2 | `ni_21_volume_front` | ni | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 3 | `ni_21_volume_top20` | ni | 2,934 | 2015-01-02 ~ 2026-08-28 |
| 4 | `si_21_volume_industrial_si` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 5 | `si_26_volume_industrial_si` | si | 893 | 2022-12-22 ~ 2026-08-28 |
| 6 | `sn_21_volume` | sn | 2,779 | 2015-03-27 ~ 2026-08-28 |
| 7 | `zn_21_volume` | zn | 1,128 | 2022-02-28 ~ 2026-08-27 |

## 5. Key Sample Mappings

The following examples demonstrate the mapping relationship between DSHB indicator_id and DSHE meta_chart indicator_id:

| DSHB indicator_id | DSHE indicator_id_mapped | commodity | Description |
|-------------------|--------------------------|-----------|-------------|
| `zn_21_close_front` | `ZN_FU00014950` | zn | 锌主力收盘价 |
| `cu_22_premium` | `CU_SPOT_PREMIUM` | cu | 铜现货升贴水 |
| `al_00_basis` | `AL_BASIS` | al | 铝基差 |
| `j21_close` | `PB_FU00014946` | j21 | 铅主力收盘价 (legacy j* prefix) |
| `ni_21_lme_price` | `LME_NI` | ni | 镍LME价格 |
| `sn_23_lme_close` | `LME_SN` | sn | 锡LME收盘价 |
| `li_21_basis` | `LC_BASIS` | li | 碳酸锂基差 |
| `si_21_close_front_industrial_si` | `SI_FU00015015` | si | 多晶硅主力收盘价 |

## 6. Notes

1. **Legacy j* prefix**: Lead (PB) uses legacy `j21`, `j22`, `j23`, `j24`, `j25` prefixes instead of `pb_*`. These are mapped correctly to DSHE PB indicators.
2. **Lithium prefix asymmetry**: DSHE uses `LC_` (Li carbonate) while DSHB uses `li_`. Semantic mapping is 1:1.
3. **Commodity code case**: DSHB uses lowercase commodity codes (zn, cu, al, etc.) in the `commodity` column.
4. **Source**: All data has `source='real'` — no simulated data in phase03_test.db.
5. **DB mapping hit rate**: 608/615 = 98.9% of unique indicators have a mapped indicator_id_mapped value.
6. **DSHE coverage rate**: 84/109 = 77.06% of meta_chart indicators have corresponding DSHB data (as reported by cache_coverage_calc.py).

---
*Generated by export_mapping_list.py | 2026-10-15T14:06:26.218832*