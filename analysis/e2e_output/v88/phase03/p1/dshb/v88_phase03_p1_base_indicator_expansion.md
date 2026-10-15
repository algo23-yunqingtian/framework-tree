# V88 Phase03 P1 — 基础指标扩量报告 (146→180)

> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB (T3)
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1
> **生成时间**: 2026-10-15T15:53:54.612244
> **数据库**: `analysis\e2e_output\v88\phase03\p0\phase03_test.db`

---

## 1. 扩量概况

| 指标 | 数值 |
|------|-----:|
| P0 基线指标数 | 146 |
| P1 目标指标数 | 180 |
| 新增指标数 | 34 |
| 实际注册 | 33 |
| 已存在跳过 | 3 |

## 2. 分品种新增指标

### AG (5 项)

| # | indicator_id | indicator_id_mapped | 描述 | 板块 |
|---|-------------|--------------------|------|------|
| 1 | `ag_21_close_front` | `AG_FU00014953` | 白银主力收盘价 | price |
| 2 | `ag_21_openinterest` | `AG_HOLD_OPEN` | 白银持仓量 | oi |
| 3 | `ag_21_premium` | `AG_SPOT_PREMIUM` | 白银升贴水 | premium |
| 4 | `ag_23_lme_close` | `LME_AG` | 白银LME收盘价 | lme |
| 5 | `ag_25_profit` | `AG_SMELTING_PROFIT` | 白银冶炼利润 | profit |

### AL (6 项)

| # | indicator_id | indicator_id_mapped | 描述 | 板块 |
|---|-------------|--------------------|------|------|
| 1 | `al_00_volume` | `AL_VOLUME` | 铝成交量 | volume |
| 2 | `al_321_import` | `AL_IMPORT` | 铝进口量 | import |
| 3 | `al_62_export` | `AL_EXPORT` | 铝出口量 | export |
| 4 | `al_71_cost` | `AL_REFINING_COST` | 铝电解成本 | cost |
| 5 | `al_321_output` | `AL_REFINING_OUTPUT` | 铝产量 | output |
| 6 | `al_51_util` | `AL_UTILIZATION` | 铝开工率 | util |

### AU (5 项)

| # | indicator_id | indicator_id_mapped | 描述 | 板块 |
|---|-------------|--------------------|------|------|
| 1 | `au_21_close_front` | `AU_FU00014948` | 黄金主力收盘价 | price |
| 2 | `au_21_openinterest` | `AU_HOLD_OPEN` | 黄金持仓量 | oi |
| 3 | `au_21_premium` | `AU_SPOT_PREMIUM` | 黄金升贴水 | premium |
| 4 | `au_23_lme_close` | `LME_AU` | 黄金LME收盘价 | lme |
| 5 | `au_25_profit` | `AU_SMELTING_PROFIT` | 黄金冶炼利润 | profit |

### CU (6 项)

| # | indicator_id | indicator_id_mapped | 描述 | 板块 |
|---|-------------|--------------------|------|------|
| 1 | `cu_21_volume` | `CU_VOLUME` | 铜成交量 | volume |
| 2 | `cu_41_output_recycle` | `CU_RECYCLE_OUTPUT` | 铜回收产量 | output |
| 3 | `cu_61_import` | `CU_IMPORT` | 铜进口量 | import |
| 4 | `cu_62_export` | `CU_EXPORT` | 铜出口量 | export |
| 5 | `cu_71_cost` | `CU_REFINING_COST` | 铜精炼成本 | cost |
| 6 | `cu_321_import` | `CU_IMPORT_321` | 铜冶炼进口 | import |

### J21 (5 项)

| # | indicator_id | indicator_id_mapped | 描述 | 板块 |
|---|-------------|--------------------|------|------|
| 1 | `j26_close` | `PB_FU00014947` | 铅次主力收盘价 | price |
| 2 | `j26_oi` | `PB_HOLD_OPEN_2` | 铅次主力持仓 | oi |
| 3 | `j26_volume` | `PB_VOLUME` | 铅成交量 | volume |
| 4 | `j26_premium` | `PB_SPOT_PREMIUM` | 铅次主力升贴水 | premium |
| 5 | `j26_basis` | `PB_BASIS_2` | 铅次主力基差 | basis |

### LI (6 项)

| # | indicator_id | indicator_id_mapped | 描述 | 板块 |
|---|-------------|--------------------|------|------|
| 1 | `li_21_volume` | `LI_VOLUME` | 碳酸锂成交量 | volume |
| 2 | `li_311_output` | `LI_REFINING_OUTPUT` | 碳酸锂产量 | output |
| 3 | `li_61_import` | `LI_IMPORT` | 碳酸锂进口 | import |
| 4 | `li_62_export` | `LI_EXPORT` | 碳酸锂出口 | export |
| 5 | `li_71_cost` | `LI_REFINING_COST` | 碳酸锂成本 | cost |
| 6 | `li_72_profit` | `LI_SMELTING_PROFIT_2` | 碳酸锂利润2 | profit |

### SN (3 项)

| # | indicator_id | indicator_id_mapped | 描述 | 板块 |
|---|-------------|--------------------|------|------|
| 1 | `sn_21_lme_close` | `LME_SN` | 锡LME收盘价 | lme |
| 2 | `sn_41_inv` | `SN_SHFE_INV` | 锡SHFE库存 | inventory |
| 3 | `sn_43_inv` | `SN_SOCIAL_INV` | 锡社会库存 | inventory |

## 3. 全量新增指标清单

| # | indicator_id | indicator_id_mapped | commodity | 描述 | 板块 |
|---|-------------|--------------------|-----------|------|------|
| 1 | `au_21_close_front` | `AU_FU00014948` | au | 黄金主力收盘价 | price |
| 2 | `au_21_openinterest` | `AU_HOLD_OPEN` | au | 黄金持仓量 | oi |
| 3 | `au_21_premium` | `AU_SPOT_PREMIUM` | au | 黄金升贴水 | premium |
| 4 | `au_23_lme_close` | `LME_AU` | au | 黄金LME收盘价 | lme |
| 5 | `au_25_profit` | `AU_SMELTING_PROFIT` | au | 黄金冶炼利润 | profit |
| 6 | `ag_21_close_front` | `AG_FU00014953` | ag | 白银主力收盘价 | price |
| 7 | `ag_21_openinterest` | `AG_HOLD_OPEN` | ag | 白银持仓量 | oi |
| 8 | `ag_21_premium` | `AG_SPOT_PREMIUM` | ag | 白银升贴水 | premium |
| 9 | `ag_23_lme_close` | `LME_AG` | ag | 白银LME收盘价 | lme |
| 10 | `ag_25_profit` | `AG_SMELTING_PROFIT` | ag | 白银冶炼利润 | profit |
| 11 | `cu_21_volume` | `CU_VOLUME` | cu | 铜成交量 | volume |
| 12 | `cu_41_output_recycle` | `CU_RECYCLE_OUTPUT` | cu | 铜回收产量 | output |
| 13 | `cu_61_import` | `CU_IMPORT` | cu | 铜进口量 | import |
| 14 | `cu_62_export` | `CU_EXPORT` | cu | 铜出口量 | export |
| 15 | `cu_71_cost` | `CU_REFINING_COST` | cu | 铜精炼成本 | cost |
| 16 | `cu_321_import` | `CU_IMPORT_321` | cu | 铜冶炼进口 | import |
| 17 | `al_00_volume` | `AL_VOLUME` | al | 铝成交量 | volume |
| 18 | `al_321_import` | `AL_IMPORT` | al | 铝进口量 | import |
| 19 | `al_62_export` | `AL_EXPORT` | al | 铝出口量 | export |
| 20 | `al_71_cost` | `AL_REFINING_COST` | al | 铝电解成本 | cost |
| 21 | `al_321_output` | `AL_REFINING_OUTPUT` | al | 铝产量 | output |
| 22 | `al_51_util` | `AL_UTILIZATION` | al | 铝开工率 | util |
| 23 | `j26_close` | `PB_FU00014947` | j21 | 铅次主力收盘价 | price |
| 24 | `j26_oi` | `PB_HOLD_OPEN_2` | j21 | 铅次主力持仓 | oi |
| 25 | `j26_volume` | `PB_VOLUME` | j21 | 铅成交量 | volume |
| 26 | `j26_premium` | `PB_SPOT_PREMIUM` | j21 | 铅次主力升贴水 | premium |
| 27 | `j26_basis` | `PB_BASIS_2` | j21 | 铅次主力基差 | basis |
| 28 | `sn_21_lme_close` | `LME_SN` | sn | 锡LME收盘价 | lme |
| 29 | `sn_41_inv` | `SN_SHFE_INV` | sn | 锡SHFE库存 | inventory |
| 30 | `sn_43_inv` | `SN_SOCIAL_INV` | sn | 锡社会库存 | inventory |
| 31 | `li_21_volume` | `LI_VOLUME` | li | 碳酸锂成交量 | volume |
| 32 | `li_311_output` | `LI_REFINING_OUTPUT` | li | 碳酸锂产量 | output |
| 33 | `li_61_import` | `LI_IMPORT` | li | 碳酸锂进口 | import |
| 34 | `li_62_export` | `LI_EXPORT` | li | 碳酸锂出口 | export |
| 35 | `li_71_cost` | `LI_REFINING_COST` | li | 碳酸锂成本 | cost |
| 36 | `li_72_profit` | `LI_SMELTING_PROFIT_2` | li | 碳酸锂利润2 | profit |

## 4. 按板块分类

| 板块 | 数量 | 指标IDs |
|------|-----:|---------|
| basis        |  1 | `j26_basis` |
| cost         |  3 | `cu_71_cost`, `al_71_cost`, `li_71_cost` |
| export       |  3 | `cu_62_export`, `al_62_export`, `li_62_export` |
| import       |  4 | `cu_61_import`, `cu_321_import`, `al_321_import`, `li_61_import` |
| inventory    |  2 | `sn_41_inv`, `sn_43_inv` |
| lme          |  3 | `au_23_lme_close`, `ag_23_lme_close`, `sn_21_lme_close` |
| oi           |  3 | `au_21_openinterest`, `ag_21_openinterest`, `j26_oi` |
| output       |  3 | `cu_41_output_recycle`, `al_321_output`, `li_311_output` |
| premium      |  3 | `au_21_premium`, `ag_21_premium`, `j26_premium` |
| price        |  3 | `au_21_close_front`, `ag_21_close_front`, `j26_close` |
| profit       |  3 | `au_25_profit`, `ag_25_profit`, `li_72_profit` |
| util         |  1 | `al_51_util` |
| volume       |  4 | `cu_21_volume`, `al_00_volume`, `j26_volume`, `li_21_volume` |

---
*Generated by expand_base_indicators.py | 2026-10-15T15:53:54.612244*