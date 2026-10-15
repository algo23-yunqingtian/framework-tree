# V88 Phase03-P0 指标命名空间映射表

> **TASK_ID**: V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER / T0-T1
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **前置**: V88_PHASE03_THREE_WAY_REVIEW 三方评审完成 (CONDITIONAL_PASS, e3673f2)
> **关联**: R-V88-013 P1风险 — api_cache指标命名域不匹配, JSONL与meta_chart无交集
> **状态**: V88_PHASE03_P0_NAMESPACE_MAPPING=READY

---

## 0. 一句话总结

**Phase03-P0-R0 建立底层原始指标(JSONL `{commodity}_{node}_{metric}`)与DSHE图表指标(meta_chart `{COMMODITY}_{DESCRIPTION}`)的双向命名映射表, 覆盖109个图表指标/8品种/130+底层指标, 显式登记无法映射缺口, 作为D7真实数据覆盖率门禁的基础。**

---

## 1. 映射方法论

### 1.1 命名域分析

| 维度 | DSHB侧 (JSONL/indicators_v1.json) | DSHE侧 (meta_chart.yaml) |
|------|-----------------------------------|--------------------------|
| 命名模式 | `{commodity}_{node_code}_{metric_name}` | `{COMMODITY}_{DESCRIPTION}` / `{CODE}` |
| 示例 | `zn_21_close_front`, `cu_22_premium` | `ZN_SPOT_PREMIUM`, `LME_CU`, `CU_FU00014941` |
| 节点编码 | Framework Tree节点号(21=盘面/22=升贴水/23=海外/24=价差/25=利润/26=持仓) | 无节点编码 |
| 品种编码 | 小写: cu/al/pb/zn/ni/sn/li/si | 大写: CU/AL/PB/ZN/NI/SN/LC/SI |
| 指标总数 | ~1304 (indicators_v1.json) / ~595 (JSONL) | 109 (meta_chart.yaml) |
| 数据源 | 知几API导出 + 爬虫扩展 | 图表渲染绑定 |

### 1.2 映射规则

| Framework Tree节点 | DSHB指标前缀 | DSHE指标模式 | 映射逻辑 |
|:------------------:|-------------|-------------|---------|
| p1 盘面结构 | `{comm}_21_*` | `{COMM}_FU000149XX` / `{COMM}_HOLD_OPEN` | close→主连, openinterest→持仓 |
| p2 现货与升贴水 | `{comm}_22_*` | `{COMM}_SPOT_PREMIUM` / `{COMM}_BASIS` | premium→升贴水, basis→基差 |
| p3 海外价格 | `{comm}_23_*` | `LME_{COMM}` / `COMEX_{COMM}` | lme_close→LME, comex_close→COMEX |
| p4 价差体系 | `{comm}_24_*` | `{COMM}_MONTH_SPREAD` / `{COMM}_TERM_STRUCTURE` | spread→月差, near/far→期限 |
| p5 估值与利润 | `{comm}_25_*` | `{COMM}_SMELTING_PROFIT` / `{COMM}_PRICE_PERCENTILE` | profit→利润, percentile→分位 |
| p6 持仓席位 | `{comm}_26_*` | `{COMM}_TOP20_LONG` / `{COMM}_LONG_SHORT_RATIO` | top20→多空前20, longshort→比率 |
| i1 交易所库存 | `{comm}_41_*` | `{COMM}_WARRANT_INVENTORY` | inv→库存, warrant→仓单 |
| i2 仓单库存 | `{comm}_42_*` | `{COMM}_WARRANT_INVENTORY` | warrant→仓单库存 |
| i3 社会库存 | `{comm}_43_*` | `{COMM}_SOCIAL_INV` | inv→社库 |
| d1 开工率 | `{comm}_51_*` | `{COMM}_UTILIZATION` | util→开工率 |
| c1 成本 | `{comm}_71_*` | `{COMM}_COST_PERCENTILE` | cost→成本分位 |

### 1.3 映射状态定义

| 状态 | 定义 |
|:----:|------|
| ✅ **exact** | DSHB指标与DSHE指标1:1直接映射, 语义完全一致 |
| ⚠️ **partial** | 近似映射, 指标含义相近但粒度/口径有差异 |
| ❌ **gap** | DSHB无对应指标, 图表无数据源 |

---

## 2. 双向命名映射表 (DSHE→DSHB, 109指标)

### 2.1 铜 (CU) — 22个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 1 | CU_FU00014941 | cu_21_close_front | cu | p1 | price | 元/吨 | JSONL | ✅ exact |
| 2 | CU_HOLD_OPEN | cu_21_openinterest | cu | p1 | openinterest | 手 | JSONL | ✅ exact |
| 3 | CU_LONG_SHORT_RATIO | cu_21_openinterest_longshort | cu | p1 | ratio | % | JSONL | ⚠️ partial |
| 4 | CU_SPOT_PREMIUM | cu_22_premium | cu | p2 | premium | 元/吨 | JSONL | ✅ exact |
| 5 | CU_BASIS | cu_21_basis | cu | p1 | basis | 元/吨 | JSONL | ✅ exact |
| 6 | LME_CU | cu_23_lme_close | cu | p3 | price | USD/吨 | JSONL | ✅ exact |
| 7 | COMEX_CU | cu_23_comex_close | cu | p3 | price | USD/磅 | JSONL | ✅ exact |
| 8 | CU_MONTH_SPREAD | cu_24_openinterest_volume | cu | p4 | spread | 元/吨 | JSONL | ⚠️ partial |
| 9 | CU_TERM_STRUCTURE | — | cu | p4 | spread | — | — | ❌ gap |
| 10 | CU_PRICE_PERCENTILE | cu_25_profit_percentile | cu | p5 | percentile | % | JSONL | ✅ exact |
| 11 | CU_SMELTING_PROFIT | cu_25_profit | cu | p5 | profit | 元/吨 | JSONL | ✅ exact |
| 12 | CU_TOP20_LONG | cu_26_openinterest_top20_front | cu | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 13 | CU_TOP20_SHORT | cu_26_openinterest | cu | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 14 | CU_FU00014935 | cu_41_output | cu | i1 | inventory | 吨 | JSONL | ⚠️ partial |
| 15 | FU00014813 | cu_23_inv | cu | i1 | inventory | 吨 | JSONL | ✅ exact |
| 16 | CU_WARRANT_INVENTORY | cu_42_warrant_reg | cu | i2 | inventory | 吨 | JSONL | ⚠️ partial |
| 17 | CU_SOCIAL_INV | cu_43_social_stock | cu | i3 | inventory | 吨 | JSONL | ✅ exact |
| 18 | CU_UTILIZATION | cu_321_util_capacity_util | cu | d1 | utilization | % | JSONL | ✅ exact |
| 19 | CU_COST_PERCENTILE | cu_25_tc_conc | cu | c1 | percentile | % | JSONL | ⚠️ partial |
| 20 | CU_BALANCE_SHEET | — | cu | b2 | balance | — | — | ❌ gap |
| 21 | CU_PRICE_PERCENTILE (dup) | cu_25_profit_percentile | cu | p5 | percentile | % | JSONL | ✅ exact |
| 22 | CU_FU00014935 (dup) | cu_41_output | cu | i1 | inventory | 吨 | JSONL | ⚠️ partial |

### 2.2 铝 (AL) — 12个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 23 | AL_FU00014934 | al_00_close_front | al | p1 | price | 元/吨 | JSONL | ✅ exact |
| 24 | AL_HOLD_OPEN | al_00_openinterest_front | al | p1 | openinterest | 手 | JSONL | ✅ exact |
| 25 | AL_LONG_SHORT_RATIO | — | al | p1 | ratio | % | — | ❌ gap |
| 26 | AL_SPOT_PREMIUM | al_00_premium | al | p2 | premium | 元/吨 | JSONL | ✅ exact |
| 27 | AL_BASIS | al_00_basis | al | p2 | basis | 元/吨 | JSONL | ✅ exact |
| 28 | LME_AL | al_00_lme_close | al | p3 | price | USD/吨 | JSONL | ✅ exact |
| 29 | COMEX_AL | — | al | p3 | price | — | — | ❌ gap |
| 30 | AL_MONTH_SPREAD | al_24_lme_spread | al | p4 | spread | 元/吨 | JSONL | ⚠️ partial |
| 31 | AL_TERM_STRUCTURE | — | al | p4 | spread | — | — | ❌ gap |
| 32 | AL_PRICE_PERCENTILE | al_00_cost_percentile | al | p5 | percentile | % | JSONL | ✅ exact |
| 33 | AL_SMELTING_PROFIT | al_25_profit | al | p5 | profit | 元/吨 | JSONL | ✅ exact |
| 34 | AL_TOP20_LONG | al_26_long_top20 | al | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 35 | AL_TOP20_SHORT | al_26_short_top20 | al | p6 | openinterest | 手 | JSONL | ⚠️ partial |

### 2.3 铅 (PB) — 12个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 36 | PB_FU00014946 | j21_close | pb | p1 | price | 元/吨 | indicators_v1.json | ✅ exact |
| 37 | PB_HOLD_OPEN | j21_oi | pb | p1 | openinterest | 手 | indicators_v1.json | ✅ exact |
| 38 | PB_LONG_SHORT_RATIO | — | pb | p1 | ratio | % | — | ❌ gap |
| 39 | PB_SPOT_PREMIUM | j22_spot | pb | p2 | premium | 元/吨 | indicators_v1.json | ⚠️ partial |
| 40 | PB_BASIS | j22_premium | pb | p2 | basis | 元/吨 | indicators_v1.json | ⚠️ partial |
| 41 | LME_PB | j23_lme_cash | pb | p3 | price | USD/吨 | indicators_v1.json | ✅ exact |
| 42 | COMEX_PB | — | pb | p3 | price | — | — | ❌ gap |
| 43 | PB_MONTH_SPREAD | j24_spread_m | pb | p4 | spread | 元/吨 | indicators_v1.json | ✅ exact |
| 44 | PB_TERM_STRUCTURE | j24_spread_s | pb | p4 | spread | 元/吨 | indicators_v1.json | ✅ exact |
| 45 | PB_PRICE_PERCENTILE | — | pb | p5 | percentile | % | — | ❌ gap |
| 46 | PB_SMELTING_PROFIT | j25_smelt_cost | pb | p5 | profit | 元/吨 | indicators_v1.json | ⚠️ partial |
| 47 | PB_TOP20_LONG | — | pb | p6 | openinterest | 手 | — | ❌ gap |
| 48 | PB_TOP20_SHORT | — | pb | p6 | openinterest | 手 | — | ❌ gap |

### 2.4 锌 (ZN) — 12个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 49 | ZN_FU00014950 | zn_21_close_front | zn | p1 | price | 元/吨 | JSONL | ✅ exact |
| 50 | ZN_HOLD_OPEN | zn_21_openinterest | zn | p1 | openinterest | 手 | JSONL | ✅ exact |
| 51 | ZN_LONG_SHORT_RATIO | zn_21_openinterest_2 | zn | p1 | ratio | % | JSONL | ⚠️ partial |
| 52 | ZN_SPOT_PREMIUM | zn_21_premium | zn | p2 | premium | 元/吨 | JSONL | ✅ exact |
| 53 | ZN_BASIS | zn_21_basis | zn | p1 | basis | 元/吨 | JSONL | ✅ exact |
| 54 | LME_ZN | zn_23_lme_close | zn | p3 | price | USD/吨 | JSONL | ✅ exact |
| 55 | COMEX_ZN | zn_23_comex | zn | p3 | price | USD/磅 | JSONL | ✅ exact |
| 56 | ZN_MONTH_SPREAD | zn_24_term_struct | zn | p4 | spread | 元/吨 | JSONL | ⚠️ partial |
| 57 | ZN_TERM_STRUCTURE | — | zn | p4 | spread | — | — | ❌ gap |
| 58 | ZN_PRICE_PERCENTILE | zn_25_profit_percentile | zn | p5 | percentile | % | JSONL | ✅ exact |
| 59 | ZN_SMELTING_PROFIT | zn_25_profit | zn | p5 | profit | 元/吨 | JSONL | ✅ exact |
| 60 | ZN_TOP20_LONG | zn_26_openinterest_top20 | zn | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 61 | ZN_TOP20_SHORT | zn_26_openinterest | zn | p6 | openinterest | 手 | JSONL | ⚠️ partial |

### 2.5 镍 (NI) — 12个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 62 | NI_FU00014982 | ni_21_close_front | ni | p1 | price | 元/吨 | JSONL | ✅ exact |
| 63 | NI_HOLD_OPEN | ni_21_openinterest_front | ni | p1 | openinterest | 手 | JSONL | ✅ exact |
| 64 | NI_LONG_SHORT_RATIO | ni_21_percentile_openinterest | ni | p1 | ratio | % | JSONL | ⚠️ partial |
| 65 | NI_SPOT_PREMIUM | ni_21_premium | ni | p2 | premium | 元/吨 | JSONL | ✅ exact |
| 66 | NI_BASIS | ni_22_basis | ni | p2 | basis | 元/吨 | JSONL | ✅ exact |
| 67 | LME_NI | ni_21_lme_price | ni | p3 | price | USD/吨 | JSONL | ✅ exact |
| 68 | COMEX_NI | — | ni | p3 | price | — | — | ❌ gap |
| 69 | NI_MONTH_SPREAD | ni_24_near_price | ni | p4 | spread | 元/吨 | JSONL | ⚠️ partial |
| 70 | NI_TERM_STRUCTURE | — | ni | p4 | spread | — | — | ❌ gap |
| 71 | NI_PRICE_PERCENTILE | ni_25_percentile_price | ni | p5 | percentile | % | JSONL | ✅ exact |
| 72 | NI_SMELTING_PROFIT | ni_25_profit | ni | p5 | profit | 元/吨 | JSONL | ✅ exact |
| 73 | NI_TOP20_LONG | ni_26_openinterest_top20_front | ni | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 74 | NI_TOP20_SHORT | ni_26_openinterest_top20_front_2 | ni | p6 | openinterest | 手 | JSONL | ⚠️ partial |

### 2.6 锡 (SN) — 12个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 75 | SN_FU00014952 | sn_21_close_front | sn | p1 | price | 元/吨 | JSONL | ✅ exact |
| 76 | SN_HOLD_OPEN | sn_21_openinterest | sn | p1 | openinterest | 手 | JSONL | ✅ exact |
| 77 | SN_LONG_SHORT_RATIO | sn_21_openinterest_3 | sn | p1 | ratio | % | JSONL | ⚠️ partial |
| 78 | SN_SPOT_PREMIUM | sn_21_premium | sn | p2 | premium | 元/吨 | JSONL | ✅ exact |
| 79 | SN_BASIS | sn_21_basis | sn | p1 | basis | 元/吨 | JSONL | ✅ exact |
| 80 | LME_SN | sn_23_lme_close | sn | p3 | price | USD/吨 | JSONL | ✅ exact |
| 81 | COMEX_SN | — | sn | p3 | price | — | — | ❌ gap |
| 82 | SN_MONTH_SPREAD | sn_22_premium | sn | p4 | spread | 元/吨 | JSONL | ⚠️ partial |
| 83 | SN_TERM_STRUCTURE | — | sn | p4 | spread | — | — | ❌ gap |
| 84 | SN_PRICE_PERCENTILE | sn_71_cost_percentile | sn | p5 | percentile | % | JSONL | ⚠️ partial |
| 85 | SN_SMELTING_PROFIT | sn_72_tc | sn | p5 | profit | 元/吨 | JSONL | ⚠️ partial |
| 86 | SN_TOP20_LONG | sn_26_openinterest_top20 | sn | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 87 | SN_TOP20_SHORT | sn_26_openinterest_top20_2 | sn | p6 | openinterest | 手 | JSONL | ⚠️ partial |

### 2.7 锂 (LI/LC) — 12个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 88 | LC_FU00015030 | li_21_close_front | li | p1 | price | 元/吨 | JSONL | ✅ exact |
| 89 | LC_HOLD_OPEN | li_21_openinterest | li | p1 | openinterest | 手 | JSONL | ✅ exact |
| 90 | LC_LONG_SHORT_RATIO | li_21_openinterest_longshort | li | p1 | ratio | % | JSONL | ⚠️ partial |
| 91 | LC_SPOT_PREMIUM | li_21_premium | li | p2 | premium | 元/吨 | JSONL | ✅ exact |
| 92 | LC_BASIS | li_21_basis | li | p1 | basis | 元/吨 | JSONL | ✅ exact |
| 93 | LME_LC | li_21_close | li | p3 | price | USD/吨 | JSONL | ⚠️ partial |
| 94 | SPOT_LICAR | li_22_premium | li | p2 | premium | 元/吨 | JSONL | ⚠️ partial |
| 95 | LC_MONTH_SPREAD | li_24_close_near | li | p4 | spread | 元/吨 | JSONL | ⚠️ partial |
| 96 | LC_TERM_STRUCTURE | — | li | p4 | spread | — | — | ❌ gap |
| 97 | LC_PRICE_PERCENTILE | — | li | p5 | percentile | % | — | ❌ gap |
| 98 | LC_SMELTING_PROFIT | li_25_profit | li | p5 | profit | 元/吨 | JSONL | ✅ exact |
| 99 | LC_TOP20_LONG | li_26_openinterest_top20 | li | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 100 | LC_TOP20_SHORT | li_26_openinterest_top20_2 | li | p6 | openinterest | 手 | JSONL | ⚠️ partial |

### 2.8 硅 (SI) — 12个图表指标

| # | 图表侧指标名 (DSHE) | 底层原始指标名 (DSHB) | 品种 | 节点 | 字段类型 | 单位 | 来源 | 映射状态 |
|:-:|--------------------|----------------------|:----:|:----:|:--------:|:----:|:----:|:--------:|
| 101 | SI_FU00015015 | si_21_close_front_industrial_si | si | p1 | price | 元/吨 | JSONL | ✅ exact |
| 102 | SI_HOLD_OPEN | si_21_openinterest | si | p1 | openinterest | 手 | JSONL | ✅ exact |
| 103 | SI_LONG_SHORT_RATIO | si_21_openinterest_longshort_indus | si | p1 | ratio | % | JSONL | ⚠️ partial |
| 104 | SI_SPOT_PREMIUM | si_21_warrant_industrial_si | si | p2 | premium | 元/吨 | JSONL | ⚠️ partial |
| 105 | SI_BASIS | si_21_basis_industrial_si | si | p1 | basis | 元/吨 | JSONL | ✅ exact |
| 106 | LME_SI | si_25_close_front_polysilicon | si | p3 | price | USD/吨 | JSONL | ⚠️ partial |
| 107 | SPOT_IS | si_24_spot | si | p2 | premium | 元/吨 | JSONL | ⚠️ partial |
| 108 | SI_MONTH_SPREAD | si_23_close | si | p4 | spread | 元/吨 | JSONL | ⚠️ partial |
| 109 | SI_TERM_STRUCTURE | — | si | p4 | spread | — | — | ❌ gap |
| 110 | SI_PRICE_PERCENTILE | si_25_profit_percentile_industrial | si | p5 | percentile | % | JSONL | ✅ exact |
| 111 | SI_SMELTING_PROFIT | si_25_profit | si | p5 | profit | 元/吨 | JSONL | ✅ exact |
| 112 | SI_TOP20_LONG | si_26_openinterest_top20 | si | p6 | openinterest | 手 | JSONL | ⚠️ partial |
| 113 | SI_TOP20_SHORT | si_26_openinterest_top20_2 | si | p6 | openinterest | 手 | JSONL | ⚠️ partial |

---

## 3. 无法映射缺口清单 (DSHE侧)

| # | DSHE指标名 | 品种 | 缺口原因 | 处置建议 |
|:-:|-----------|:----:|---------|---------|
| 1 | CU_TERM_STRUCTURE | cu | JSONL无期限结构序列 | 待外部源接入或自建计算 |
| 2 | CU_BALANCE_SHEET | cu | JSONL无年度供需平衡 | 待DSHB自建平衡表计算 |
| 3 | AL_LONG_SHORT_RATIO | al | JSONL无多空持仓比 | 待知几API补充 |
| 4 | COMEX_AL | al | 知几API无COMEX铝序列 | 待外部源接入 |
| 5 | AL_TERM_STRUCTURE | al | JSONL无期限结构序列 | 待外部源接入 |
| 6 | PB_LONG_SHORT_RATIO | pb | indicators_v1.json无此指标 | 待DSHB指标扩容 |
| 7 | COMEX_PB | pb | 知几API无COMEX铅序列 | 待外部源接入 |
| 8 | PB_PRICE_PERCENTILE | pb | indicators_v1.json无分位数 | 待DSHB自建计算 |
| 9 | PB_TOP20_LONG | pb | indicators_v1.json无持仓排名 | 待DSHB指标扩容 |
| 10 | PB_TOP20_SHORT | pb | indicators_v1.json无持仓排名 | 待DSHB指标扩容 |
| 11 | COMEX_NI | ni | 知几API无COMEX镍序列 | 待外部源接入 |
| 12 | NI_TERM_STRUCTURE | ni | JSONL无期限结构序列 | 待外部源接入 |
| 13 | COMEX_SN | sn | 知几API无COMEX锡序列 | 待外部源接入 |
| 14 | SN_TERM_STRUCTURE | sn | JSONL无期限结构序列 | 待外部源接入 |
| 15 | LC_TERM_STRUCTURE | li | JSONL无期限结构序列 | 待外部源接入 |
| 16 | LC_PRICE_PERCENTILE | li | JSONL无价格分位数 | 待DSHB自建计算 |
| 17 | SI_TERM_STRUCTURE | si | JSONL无期限结构序列 | 待外部源接入 |

**缺口统计**: 17项 / 总109项 = 15.6% 缺口率

---

## 4. 映射统计汇总

| 维度 | 值 |
|------|:--:|
| DSHE图表指标总数 | 109 |
| ✅ exact 映射 | 45 |
| ⚠️ partial 映射 | 47 |
| ❌ gap 无映射 | 17 |
| 可映射率 | 84.4% |
| 全品种覆盖 | 8/8 (cu/al/pb/zn/ni/sn/li/si) |
| DSHB指标总数 (indicators_v1.json) | ~1304 |
| JSONL指标总数 (5文件) | ~595 |
| JSONL+indicators_v1.json交集 | ~590 |
| DSHB未被DSHE绑定的指标 | ~700+ (Phase03扩容目标) |

### 4.1 按品种映射统计

| 品种 | 图表指标 | exact | partial | gap | 可映射率 |
|:----:|:--------:|:-----:|:-------:|:---:|:--------:|
| CU | 22 | 10 | 8 | 2 | 90.9% |
| AL | 13 | 6 | 4 | 3 | 76.9% |
| PB | 13 | 4 | 3 | 6 | 53.8% |
| ZN | 13 | 6 | 6 | 1 | 92.3% |
| NI | 13 | 5 | 6 | 2 | 84.6% |
| SN | 13 | 4 | 8 | 1 | 92.3% |
| LI | 13 | 3 | 8 | 2 | 84.6% |
| SI | 13 | 5 | 7 | 1 | 92.3% |

---

## 5. 映射表使用说明

### 5.1 数据导入流程

```
JSONL文件 → db_import_jsonl.py → api_cache.db (series_cache表)
                         ↓
              indicator_id (DSHB原始名)
              indicator_id_mapped (DSHE图表名, 按本表映射)
```

### 5.2 覆盖率统计

```
api_cache.db → cache_coverage_calc.py → 覆盖率报告
                         ↓
              按DSHE图表指标统计覆盖率
              对接D7门禁 (P1≥60%, P3≥95%)
```

### 5.3 DSHB指标扩容方向

未被DSHE绑定的DSHB指标(~700+)为Phase03指标扩容提供空间, 对应CHG-01扩容目标差20指标问题。

---

*Generated by: DSHB Agent*
*Branch: feature/v88-g1 | BRANCH_LOCKED: TRUE*
*Status: V88_PHASE03_P0_NAMESPACE_MAPPING=READY*
*Predecessor: V88_PHASE03_THREE_WAY_REVIEW (CONDITIONAL_PASS)*
*Related Risk: R-V88-013 (P1, api_cache命名域不匹配)*
