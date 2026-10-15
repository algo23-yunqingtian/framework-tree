# V88 Phase03 P1 — DSHE引擎口径一致性检查报告

> 检查时间: 2026-10-15 19:55:13
> 任务ID: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB · T5
> DB路径: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db`
> 映射JSON: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p1\dshb\v88_phase03_p1_metric_indicator_code_mapping.json`

---

## 1. 检查概况

| 指标 | 值 |
|------|-----|
| 新增派生指标 | **70** |
| 已映射 (has_mapping=true) | **70** |
| 未映射 (has_mapping=false) | **0** |
| DSHE meta_chart 总数 | **109** |
| 口径对齐 (caliber_match=true) | **29/70** |
| 口径通过率 | **41.4%** |

### 映射JSON汇总

- total_indicators: 718
- real: 615
- derived: 70
- mapped: 711
- unmapped: 7
- coverage_pct: 99.03%
- distinct_mapped_ids: 237

---

## 2. 逐指标口径检查

| # | indicator_id | mapped_target | has_mapping | meta_chart有效 | DB行数 | 日期范围 | 数值范围 | 口径匹配 |
|---|-------------|--------------|------------|-------------|-------|---------|---------|---------|
| 1 | `al_inv_change` | `AL_INV_CHANGE` | Y | N | Y (3040) | 2015-01-05~2026-08-28 | [-28.20, 31.00] | ❌ |
| 2 | `al_long_short_ratio` | `AL_LONG_SHORT_RATIO` | Y | Y | Y (3041) | 2015-01-02~2026-08-28 | [0.28, 1.00] | ✅ |
| 3 | `al_month_spread` | `AL_MONTH_SPREAD` | Y | Y | Y (3040) | 2015-01-05~2026-08-28 | [-7.53, 6.69] | ✅ |
| 4 | `al_premium_change` | `AL_PREMIUM_CHANGE` | Y | N | Y (3040) | 2015-01-05~2026-08-28 | [-13.61, 13.60] | ❌ |
| 5 | `al_price_percentile` | `AL_PRICE_PERCENTILE` | Y | Y | Y (3022) | 2015-01-29~2026-08-28 | [0.40, 100.00] | ✅ |
| 6 | `al_term_structure` | `AL_TERM_STRUCTURE` | Y | Y | Y (3041) | 2015-01-02~2026-08-28 | [19714.55, 27966.82] | ✅ |
| 7 | `placeholder_comexal` | `COMEX_AL` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 8 | `comex_cu_change` | `COMEX_CU_CHANGE` | Y | N | Y (3040) | 2015-01-05~2026-08-28 | [-78.00, 82.00] | ❌ |
| 9 | `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | Y | N | Y (3041) | 2015-01-02~2026-08-28 | [-760.00, 1429.00] | ❌ |
| 10 | `cu_inv_change` | `CU_INV_CHANGE` | Y | N | Y (3040) | 2015-01-05~2026-08-28 | [-13517.00, 11546.00] | ❌ |
| 11 | `cu_long_short_ratio` | `CU_LONG_SHORT_RATIO` | Y | Y | Y (3041) | 2015-01-02~2026-08-28 | [0.25, 1.00] | ✅ |
| 12 | `cu_month_spread` | `CU_MONTH_SPREAD` | Y | Y | Y (3040) | 2015-01-05~2026-08-28 | [-8696.00, 8685.00] | ✅ |
| 13 | `cu_oi_percentile` | `CU_OI_PERCENTILE` | Y | N | Y (3022) | 2015-01-29~2026-08-28 | [0.40, 100.00] | ❌ |
| 14 | `cu_premium_change` | `CU_PREMIUM_CHANGE` | Y | N | Y (3040) | 2015-01-05~2026-08-28 | [-20.70, 19.80] | ❌ |
| 15 | `cu_price_percentile` | `CU_PRICE_PERCENTILE` | Y | Y | Y (3022) | 2015-01-29~2026-08-28 | [0.40, 100.00] | ✅ |
| 16 | `cu_term_structure` | `CU_TERM_STRUCTURE` | Y | Y | Y (3041) | 2015-01-02~2026-08-28 | [-85979.00, 28134.00] | ✅ |
| 17 | `cu_top20_net` | `CU_TOP20_NET` | Y | N | Y (3041) | 2015-01-02~2026-08-28 | [-11071.00, 67665.00] | ❌ |
| 18 | `placeholder_cubalancesheet` | `CU_BALANCE_SHEET` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 19 | `pb_long_short_ratio` | `PB_LONG_SHORT_RATIO` | Y | Y | Y (3041) | 2015-01-02~2026-08-28 | [0.41, 1.00] | ✅ |
| 20 | `pb_month_spread` | `PB_MONTH_SPREAD` | Y | Y | Y (3040) | 2015-01-05~2026-08-28 | [-8.80, 10.17] | ✅ |
| 21 | `pb_price_percentile` | `PB_PRICE_PERCENTILE` | Y | Y | Y (3022) | 2015-01-29~2026-08-28 | [0.40, 100.00] | ✅ |
| 22 | `pb_term_structure` | `PB_TERM_STRUCTURE` | Y | Y | Y (3041) | 2015-01-02~2026-08-28 | [16529.27, 22069.87] | ✅ |
| 23 | `pb_top20_net` | `PB_TOP20_NET` | Y | N | Y (3041) | 2015-01-02~2026-08-28 | [16480.00, 22000.00] | ❌ |
| 24 | `lc_top20_net` | `LC_TOP20_NET` | Y | N | Y (754) | 2023-07-21~2026-08-28 | [0.00, 0.00] | ❌ |
| 25 | `li_21_close_2_p09fix` | `LC_FU00015030` | Y | Y | Y (1) | 2023-07-21~2023-07-21 | [110644.19, 110644.19] | ✅ |
| 26 | `li_21_openinterest_2_p09fix` | `LC_HOLD_OPEN` | Y | Y | Y (1) | 2023-07-21~2023-07-21 | [481104.47, 481104.47] | ✅ |
| 27 | `li_basis_change` | `LC_BASIS_CHANGE` | Y | N | Y (753) | 2023-07-24~2026-08-28 | [-27520.00, 29040.00] | ❌ |
| 28 | `li_inv_change` | `LI_INV_CHANGE` | Y | N | Y (17) | 2025-03-31~2026-07-31 | [-70000.00, 65000.00] | ❌ |
| 29 | `li_long_short_ratio` | `LC_LONG_SHORT_RATIO` | Y | Y | Y (754) | 2023-07-21~2026-08-28 | [0.01, 1.00] | ✅ |
| 30 | `li_month_spread` | `LC_MONTH_SPREAD` | Y | Y | Y (436) | 2024-11-14~2026-08-28 | [58583.59, 208113.15] | ✅ |
| 31 | `li_oi_percentile` | `LI_OI_PERCENTILE` | Y | N | Y (735) | 2023-08-17~2026-08-28 | [0.40, 100.00] | ❌ |
| 32 | `li_price_percentile` | `LC_PRICE_PERCENTILE` | Y | Y | Y (735) | 2023-08-17~2026-08-28 | [0.40, 100.00] | ✅ |
| 33 | `li_term_structure` | `LC_TERM_STRUCTURE` | Y | Y | Y (754) | 2023-07-21~2026-08-28 | [56693.59, 213902.65] | ✅ |
| 34 | `spot_licar_change` | `SPOT_LICAR_CHANGE` | Y | N | Y (438) | 2024-11-15~2026-08-28 | [-2900.00, 450.00] | ❌ |
| 35 | `ni_basis_change` | `NI_BASIS_CHANGE` | Y | N | Y (2777) | 2015-03-30~2026-08-28 | [-77560.00, 103200.00] | ❌ |
| 36 | `ni_inv_change` | `NI_INV_CHANGE` | Y | N | Y (499) | 2015-02-27~2026-08-28 | [-16200.00, 23403.00] | ❌ |
| 37 | `ni_long_short_ratio` | `NI_LONG_SHORT_RATIO` | Y | Y | Y (346) | 2020-01-03~2026-08-21 | [0.24, 1.00] | ✅ |
| 38 | `ni_month_spread` | `NI_MONTH_SPREAD` | Y | Y | Y (1659) | 2020-01-02~2026-08-28 | [0.00, 0.00] | ❌ |
| 39 | `ni_price_percentile` | `NI_PRICE_PERCENTILE` | Y | Y | Y (2760) | 2015-04-24~2026-08-28 | [0.40, 100.00] | ✅ |
| 40 | `ni_term_structure` | `NI_TERM_STRUCTURE` | Y | Y | Y (1659) | 2020-01-02~2026-08-28 | [0.00, 0.00] | ❌ |
| 41 | `ni_top20_net` | `NI_TOP20_NET` | Y | N | Y (2779) | 2015-03-27~2026-08-28 | [0.00, 0.00] | ❌ |
| 42 | `placeholder_comexni` | `COMEX_NI` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 43 | `placeholder_comexpb` | `COMEX_PB` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 44 | `placeholder_pbtop20long` | `PB_TOP20_LONG` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 45 | `placeholder_pbtop20short` | `PB_TOP20_SHORT` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 46 | `placeholder_spotis` | `SPOT_IS` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 47 | `si_inventory_days` | `SI_INV_DAYS` | Y | N | Y (133) | 2024-01-05~2026-08-28 | [7.00, 35.02] | ❌ |
| 48 | `si_long_short_ratio` | `SI_LONG_SHORT_RATIO` | Y | Y | Y (893) | 2022-12-22~2026-08-28 | [0.01, 1.00] | ✅ |
| 49 | `si_month_spread` | `SI_MONTH_SPREAD` | Y | Y | Y (893) | 2022-12-22~2026-08-28 | [0.00, 0.00] | ❌ |
| 50 | `si_price_percentile` | `SI_PRICE_PERCENTILE` | Y | Y | Y (874) | 2023-01-19~2026-08-28 | [0.40, 100.00] | ✅ |
| 51 | `si_term_structure` | `SI_TERM_STRUCTURE` | Y | Y | Y (893) | 2022-12-22~2026-08-28 | [0.00, 0.00] | ❌ |
| 52 | `si_top20_net` | `SI_TOP20_NET` | Y | N | Y (893) | 2022-12-22~2026-08-28 | [0.00, 0.00] | ❌ |
| 53 | `spot_is_change` | `SPOT_IS_CHANGE` | Y | N | Y (773) | 2023-06-21~2026-08-28 | [-36405.00, 20476.00] | ❌ |
| 54 | `placeholder_comexsn` | `COMEX_SN` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 55 | `sn_inventory_days` | `SN_INV_DAYS` | Y | N | Y (2496) | 2016-07-01~2026-08-28 | [0.00, 72.90] | ❌ |
| 56 | `sn_long_short_ratio` | `SN_LONG_SHORT_RATIO` | Y | Y | Y (345) | 2020-01-03~2026-08-21 | [0.07, 1.00] | ✅ |
| 57 | `sn_month_spread` | `SN_MONTH_SPREAD` | Y | Y | Y (1537) | 2020-05-07~2026-08-28 | [-7000.00, 13000.00] | ✅ |
| 58 | `sn_price_percentile` | `SN_PRICE_PERCENTILE` | Y | Y | Y (2760) | 2015-04-24~2026-08-28 | [0.40, 100.00] | ✅ |
| 59 | `sn_term_structure` | `SN_TERM_STRUCTURE` | Y | Y | Y (1535) | 2020-05-06~2026-08-28 | [124240.00, 452740.00] | ✅ |
| 60 | `sn_top20_net` | `SN_TOP20_NET` | Y | N | Y (2779) | 2015-03-27~2026-08-28 | [0.00, 0.00] | ❌ |
| 61 | `comex_zn_change` | `COMEX_ZN_CHANGE` | Y | N | Y (2832) | 2015-01-06~2026-08-28 | [-2060.85, 2001.00] | ❌ |
| 62 | `comex_zn_lme_spread` | `COMEX_ZN_LME_SPREAD` | Y | N | Y (1051) | 2022-03-21~2026-08-28 | [16676.36, 24227.88] | ❌ |
| 63 | `placeholder_comexzn` | `COMEX_ZN` | Y | Y | Y (1) | 2026-01-01~2026-01-01 | [0.00, 0.00] | ❌ |
| 64 | `zn_basis_change` | `ZN_BASIS_CHANGE` | Y | N | Y (2833) | 2015-01-06~2026-08-28 | [-1650.00, 2380.00] | ❌ |
| 65 | `zn_inv_change` | `ZN_INV_CHANGE` | Y | N | Y (516) | 2016-09-30~2026-08-28 | [-10.25, 26.39] | ❌ |
| 66 | `zn_long_short_ratio` | `ZN_LONG_SHORT_RATIO` | Y | Y | Y (345) | 2020-01-03~2026-08-21 | [0.19, 1.00] | ✅ |
| 67 | `zn_month_spread` | `ZN_MONTH_SPREAD` | Y | Y | Y (2832) | 2015-01-06~2026-08-28 | [-2065.00, 2000.00] | ✅ |
| 68 | `zn_oi_percentile` | `ZN_OI_PERCENTILE` | Y | N | Y (326) | 2020-05-22~2026-08-21 | [12.70, 100.00] | ❌ |
| 69 | `zn_price_percentile` | `ZN_PRICE_PERCENTILE` | Y | Y | Y (2814) | 2015-01-30~2026-08-28 | [0.40, 100.00] | ✅ |
| 70 | `zn_term_structure` | `ZN_TERM_STRUCTURE` | Y | Y | Y (2833) | 2015-01-05~2026-08-28 | [0.00, 0.00] | ❌ |

---

## 3. 口径差异记录

共发现 **45** 个口径问题，涉及 **41** 个指标。

### 3.2 映射目标在DSHB孤儿指标中 (不在meta_chart 109中)

> 这些指标在DSHB DB中存在，但其映射目标不在DSHE meta_chart 109指标中。
> 属于扩展指标，需在DSHE引擎中补充注册后方可渲染。

| indicator_id | mapped_target | 说明 |
|-------------|--------------|------|
| `al_inv_change` | `AL_INV_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `al_premium_change` | `AL_PREMIUM_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `comex_cu_change` | `COMEX_CU_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `comex_cu_lme_spread` | `COMEX_CU_LME_SPREAD` | DSHB孤儿指标，meta_chart未覆盖 |
| `cu_inv_change` | `CU_INV_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `cu_oi_percentile` | `CU_OI_PERCENTILE` | DSHB孤儿指标，meta_chart未覆盖 |
| `cu_premium_change` | `CU_PREMIUM_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `cu_top20_net` | `CU_TOP20_NET` | DSHB孤儿指标，meta_chart未覆盖 |
| `pb_top20_net` | `PB_TOP20_NET` | DSHB孤儿指标，meta_chart未覆盖 |
| `lc_top20_net` | `LC_TOP20_NET` | DSHB孤儿指标，meta_chart未覆盖 |
| `li_basis_change` | `LC_BASIS_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `li_inv_change` | `LI_INV_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `li_oi_percentile` | `LI_OI_PERCENTILE` | DSHB孤儿指标，meta_chart未覆盖 |
| `spot_licar_change` | `SPOT_LICAR_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `ni_basis_change` | `NI_BASIS_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `ni_inv_change` | `NI_INV_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `ni_top20_net` | `NI_TOP20_NET` | DSHB孤儿指标，meta_chart未覆盖 |
| `si_inventory_days` | `SI_INV_DAYS` | DSHB孤儿指标，meta_chart未覆盖 |
| `si_top20_net` | `SI_TOP20_NET` | DSHB孤儿指标，meta_chart未覆盖 |
| `spot_is_change` | `SPOT_IS_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `sn_inventory_days` | `SN_INV_DAYS` | DSHB孤儿指标，meta_chart未覆盖 |
| `sn_top20_net` | `SN_TOP20_NET` | DSHB孤儿指标，meta_chart未覆盖 |
| `comex_zn_change` | `COMEX_ZN_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `comex_zn_lme_spread` | `COMEX_ZN_LME_SPREAD` | DSHB孤儿指标，meta_chart未覆盖 |
| `zn_basis_change` | `ZN_BASIS_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `zn_inv_change` | `ZN_INV_CHANGE` | DSHB孤儿指标，meta_chart未覆盖 |
| `zn_oi_percentile` | `ZN_OI_PERCENTILE` | DSHB孤儿指标，meta_chart未覆盖 |

### 3.6 占位符指标零值 (预期行为)

> 这些是 `placeholder_*` 派生指标，仅有1行占位数据(值=0)，属于正常预期。

- 占位符指标数: 9

| indicator_id | mapped_target | DB行数 |
|-------------|--------------|-------|
| `placeholder_comexal` | `COMEX_AL` | 1 |
| `placeholder_cubalancesheet` | `CU_BALANCE_SHEET` | 1 |
| `placeholder_comexni` | `COMEX_NI` | 1 |
| `placeholder_comexpb` | `COMEX_PB` | 1 |
| `placeholder_pbtop20long` | `PB_TOP20_LONG` | 1 |
| `placeholder_pbtop20short` | `PB_TOP20_SHORT` | 1 |
| `placeholder_spotis` | `SPOT_IS` | 1 |
| `placeholder_comexsn` | `COMEX_SN` | 1 |
| `placeholder_comexzn` | `COMEX_ZN` | 1 |

### 3.7 实际数据零值异常 (需关注)

> 这些非占位符指标的所有数据值均为零，可能存在派生计算问题。

| indicator_id | mapped_target | DB行数 | 日期范围 |
|-------------|--------------|-------|---------|
| `lc_top20_net` | `LC_TOP20_NET` | 754 | 2023-07-21~2026-08-28 |
| `ni_month_spread` | `NI_MONTH_SPREAD` | 1659 | 2020-01-02~2026-08-28 |
| `ni_term_structure` | `NI_TERM_STRUCTURE` | 1659 | 2020-01-02~2026-08-28 |
| `ni_top20_net` | `NI_TOP20_NET` | 2779 | 2015-03-27~2026-08-28 |
| `si_month_spread` | `SI_MONTH_SPREAD` | 893 | 2022-12-22~2026-08-28 |
| `si_term_structure` | `SI_TERM_STRUCTURE` | 893 | 2022-12-22~2026-08-28 |
| `si_top20_net` | `SI_TOP20_NET` | 893 | 2022-12-22~2026-08-28 |
| `sn_top20_net` | `SN_TOP20_NET` | 2779 | 2015-03-27~2026-08-28 |
| `zn_term_structure` | `ZN_TERM_STRUCTURE` | 2833 | 2015-01-05~2026-08-28 |

---

## 4. 结论

**⚠️ 口径对齐: 29/70 (41.4%)**

- 27 个指标映射目标在DSHB孤儿指标中(meta_chart未覆盖)
- 0 个指标映射目标完全未知
- 9 个占位符指标零值(预期行为)
- 9 个实际数据零值异常(需关注)
- 0 个指标日期范围不一致
- 0 个指标数值范围异常

建议：
1. **孤儿指标补充**: 27 个指标的映射目标在DSHB orphan_ids中，建议扩展DSHE meta_chart以覆盖这些派生指标
2. **零值异常排查**: 9 个非占位符指标数据全为零，需排查派生计算逻辑
3. **日期范围校准**: 如发现日期范围不一致，检查数据导入时的时间偏移
4. **映射维护**: 确保新增派生指标持续同步到DSHE meta_chart

---

*报告由 t5_engine_caliber_check.py 自动生成于 2026-10-15 19:55:13*
