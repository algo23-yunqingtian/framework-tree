# DSHE V86-RC1 跨Agent交叉核验预准备清单

> **任务**: `DSHE_V86_RC1_PRESENTATION_LAYER_PRE_AUDIT` · T3.4
> **分支**: `feature/v85-chart-template`
> **基线**: DSHE V7-RC1 (commit `f1d444e`), DSHB V86-RC1 (commit `79e34a1`)
> **日期**: 2026-10-03
> **约束**: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED
> **状态**: ✅ **跨端交叉核验清单全部准备完成 — 待DSHB底层巡检结果回填**

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [交叉核验范围与方法](#2-交叉核验范围与方法)
3. [36张图表前端展示指标清单](#3-36张图表前端展示指标清单)
4. [P2缺陷底层引擎核对项](#4-p2缺陷底层引擎核对项)
5. [7项已知限制底层比对清单](#5-7项已知限制底层比对清单)
6. [交叉核验核对表](#6-交叉核验核对表)
7. [DSHB待回填字段说明](#7-dshb待回填字段说明)
8. [交叉核验通过标准](#8-交叉核验通过标准)
9. [附录](#9-附录)

---

## 1. 执行摘要

本报告准备DSHE展示层与DSHB底层引擎之间的跨端交叉核验核对清单, 涵盖36张图表前端展示指标、5项P2缺陷底层核对项、7项已知限制底层比对清单, 并预留DSHB底层巡检结果回填字段。

| 维度 | 值 |
|------|-----|
| **图表前端指标清单** | 36张图表, 逐项列出DSHB比对字段 |
| **P2缺陷底层核对项** | 5项P2 (合并为2类核对) |
| **已知限制底层比对清单** | 7项限制, 全部准备DSHB比对项 |
| **交叉核验核对表** | 完整表格, 预留DSHB回填字段 |
| **待回填字段** | 8个DSHB回填字段 |
| **通过标准定义** | 4项通过标准 |
| **核验裁定** | ✅ **CHECKLIST READY — AWAITING DSHB RESULTS** |

### 1.1 交叉核验总览

```
┌──────────────────────────────────────────────────────────────────┐
│  DSHE-V86-RC1 CROSS-VALIDATION CHECKLIST — PREPARED                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  ║
│  SCOPE:                                                         ║
│  ├─ Chart metrics:      36 charts ✅                             ║
│  ├─ P2 defects:         5 items (2 categories) ✅               ║
│  ├─ Known limits:       7 items ✅                              ║
│  └─ Cross-check table:  Complete ✅                              ║
│                                                                  ║
│  DSHB FILL-BACK FIELDS: 8 fields defined ✅                      ║
│  PASS CRITERIA:        4 criteria defined ✅                     ║
│                                                                  ║
│  STATUS: ✅ CHECKLIST READY — AWAITING DSHB RESULTS                ║
│  ══════════════════════════════════════════════                    ║
│                                                                  ║
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. 交叉核验范围与方法

### 2.1 核验范围

| 核验类别 | 核验项 | 数量 | DSHE侧数据 | DSHB侧数据 |
|----------|--------|------|-----------|-----------|
| **图表指标** | 图表数据点/坐标轴/图例/降级标记 | 36 | 前端展示数据 | 底层指标计算结果 |
| **P2缺陷** | 加载性能/渲染行为 | 5 (2类) | 前端观测数据 | 底层引擎响应时间 |
| **已知限制** | 降级行为/数据缺失/歧义处理 | 7 | 前端观测现象 | 底层引擎行为 |

### 2.2 核验方法

```
┌──────────────────────────────────────────────────────────────────┐
│  CROSS-VALIDATION METHODOLOGY                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  ║
│  DSHE侧 (展示层):                                                 ║
│  ├─ 页面加载耗时 / TTFC / TTI                                    ║
│  ├─ 图表渲染完整性 / 数据点数量                                   ║
│  ├─ 降级标记显示 / 别名解析结果                                   ║
│  └─ 前端观测数据 (本地快照)                                       ║
│                                                                  ║
│  DSHB侧 (底层引擎):                                              ║
│  ├─ 指标计算结果 / 计算耗时                                      ║
│  ├─ 别名引擎解析结果 / 解析耗时                                  ║
│  ├─ 降级策略执行结果 / 降级标记                                   ║
│  └─ 底层引擎行为数据 (DSHB巡检报告)                               ║
│                                                                  ║
│  交叉核验:                                                       ║
│  ├─ DSHE前端展示值 vs DSHB底层计算值 → 一致性                     ║
│  ├─ DSHE前端加载耗时 vs DSHB底层响应时间 → 归因分析               ║
│  ├─ DSHE前端降级标记 vs DSHB底层降级策略 → 正确性                 ║
│  └─ 归因: 前端渲染问题 vs 底层引擎问题                            ║
│                                                                  ║
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 36张图表前端展示指标清单

### 3.1 图表指标清单总表

| # | 图表名称 | 图表类型 | 品种 | 完全匹配 | 降级 | 降级层级 | 前端数据点 | 坐标轴 | 图例 | 降级标记 | DSHE侧状态 | DSHB比对字段 |
|---|----------|----------|------|----------|------|----------|-----------|--------|------|----------|-----------|-------------|
| 1 | 铅价走势 | 折线图 | PB | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 2 | 铅库存总量 | 柱状图 | PB | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 3 | 铅价LME | 折线图 | PB | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 4 | 铜价走势 | 折线图 | CU | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 5 | 铜库存总量 | 柱状图 | CU | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 6 | 铜价LME | 折线图 | CU | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 7 | 铝价走势 | 折线图 | AL | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 8 | 铝库存总量 | 柱状图 | AL | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 9 | 锌价走势 | 折线图 | ZN | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 10 | 锌库存总量 | 柱状图 | ZN | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 11 | 镍价走势 | 折线图 | NI | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 12 | 镍库存总量 | 柱状图 | NI | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 13 | 锡价走势 | 折线图 | SN | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 14 | 锡库存总量 | 柱状图 | SN | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 15 | 碳酸锂价格 | 折线图 | LI | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 16 | 碳酸锂产量 | 柱状图 | LI | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 17 | 硅价走势 | 折线图 | SI | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 18 | 硅产量 | 柱状图 | SI | ✅ | — | — | 312点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 19 | 氧化铝价格 | 折线图 | AO | ✅ | — | — | 266点 | X/Y | 3系列 | — | ✅ | 指标ID/计算值/时间范围 |
| 20 | Gate大盘 | 复合图 | 全局 | ✅ | — | — | — | X/Y | 多系列 | — | ✅ | 指标计算/告警规则 |
| 21 | 风险监控 | 复合图 | 全局 | ✅ | — | — | — | X/Y | 多系列 | — | ✅ | 风险规则/拦截率 |
| 22 | P1跟踪 | 表格图 | 全局 | ✅ | — | — | — | — | — | — | ✅ | P1 SOP指标 |
| 23 | 别名网关 | 仪表盘 | 全局 | ✅ | — | — | — | — | — | — | ✅ | 别名解析率/缓存命中 |
| 24 | 版本状态 | 状态图 | 全局 | ✅ | — | — | — | — | — | — | ✅ | 版本标识/commit |
| 25 | 降级体系 | 状态图 | 全局 | ✅ | — | — | — | — | — | — | ✅ | 降级层级/降级数量 |
| 26 | **工业硅价格** | **折线图** | **SI** | **❌** | **✅** | **L2** | **312点** | **X/Y** | **3系列** | **✅ L2标记** | **✅ 降级正确** | **指标ID/降级标记/缓存值** |
| 27 | **铝土矿产量** | **柱状图** | **AO** | **❌** | **✅** | **L3** | **312点** | **X/Y** | **3系列** | **✅ L3标记** | **✅ 降级正确** | **指标ID/降级标记/缓存值** |
| 28 | **新能源乘用车** | **折线图** | **AL** | **❌** | **✅** | **L1** | **266点** | **X/Y** | **3系列** | **✅ L1标记** | **✅ 降级正确** | **指标ID/降级标记/缓存值** |
| 29 | **LME库存** | **柱状图** | **多** | **❌** | **✅** | **L1** | **312点** | **X/Y** | **3系列** | **✅ L1标记** | **✅ 降级正确** | **指标ID/降级标记/缓存值** |
| 30 | **碳酸锂产量** | **柱状图** | **LI** | **❌** | **✅** | **L2** | **312点** | **X/Y** | **3系列** | **✅ L2标记** | **✅ 降级正确** | **指标ID/降级标记/缓存值** |
| 31 | **硫酸镍价格** | **折线图** | **NI** | **❌** | **✅** | **L2** | **266点** | **X/Y** | **3系列** | **✅ L2标记** | **✅ 降级正确** | **指标ID/降级标记/缓存值** |
| 32 | **不锈钢库存** | **柱状图** | **NI** | **❌** | **✅** | **L3** | **312点** | **X/Y** | **3系列** | **✅ L3标记** | **✅ 降级正确** | **指标ID/降级标记/缓存值** |
| 33 | DSHE别名演示图 | 折线图 | 全局 | ✅ | — | — | — | X/Y | 3系列 | — | ✅ | 别名解析演示 |
| 34 | DSHE演示图表2 | 柱状图 | 全局 | ✅ | — | — | — | X/Y | 3系列 | — | ✅ | 演示数据 |
| 35 | DSHE演示图表3 | 折线图 | 全局 | ✅ | — | — | — | X/Y | 3系列 | — | ✅ | 演示数据 |
| 36 | DSHE演示图表4 | 复合图 | 全局 | ✅ | — | — | — | X/Y | 多系列 | — | ✅ | 演示数据 |

### 3.2 图表比对字段定义

| 比对字段 | 说明 | DSHE侧数据来源 | DSHB侧数据来源 |
|----------|------|---------------|---------------|
| **指标ID** | 图表引用的指标标识 | 图表配置中的zhji_id | 底层引擎指标注册表 |
| **计算值** | 图表展示的数据值 | 前端渲染数据点 | 底层引擎计算结果 |
| **时间范围** | 数据覆盖的时间范围 | 图表X轴范围 | 底层引擎数据时间范围 |
| **数据点数** | 图表渲染的数据点数量 | 前端渲染统计 | 底层引擎序列长度 |
| **降级标记** | 图表是否标记为降级 | 前端降级标签 | 底层引擎降级策略 |
| **降级层级** | 降级级别 (L0-L3) | 前端降级标签颜色 | 底层引擎降级策略层级 |
| **坐标轴** | X轴/Y轴显示是否正确 | 前端渲染检查 | 底层引擎数据维度 |
| **图例** | 系列名称/数量是否正确 | 前端渲染检查 | 底层引擎数据系列数 |
| **别名解析** | 图表中别名→canonical_key | 前端别名网关 | 底层别名引擎 |
| **数据源** | 数据来源标注 | 前端页面标注 | 底层数据源标注 |

---

## 4. P2缺陷底层引擎核对项

### 4.1 P2缺陷核对总表

| 编号 | P2描述 | 前端观测值 | DSHE侧判定 | DSHB核对项 | DSHB回填字段 | 通过标准 |
|------|--------|-----------|-----------|-----------|-------------|----------|
| P2-001 | Gate大盘切换后首次加载耗时增加 | 2.8s (正常2.1s, +33%) | 前端缓存行为 | 底层引擎是否触发重新计算 | DSHB_ENGINE_RECOMPUTE=TRUE/FALSE | DSHB_ENGINE_RECOMPUTE=FALSE (底层无重新计算) |
| P2-002/004 | 并发下Gate大盘加载峰值偏高 | P99=4.9s/4.1s (正常2.4s/2.6s) | 前端DOM渲染竞争 | 底层引擎并发响应时间 | DSHB_CONCURRENT_RESPONSE=___ms | DSHB_CONCURRENT_RESPONSE < 1000ms (底层响应<1s) |
| P2-003/005 | 工业硅门户加载耗时略高 | 3.4s/3.28s (正常1.91s/1.72s) | 前端数据量大 | 底层数据是否为静态缓存 | DSHB_DATA_TYPE=STATIC/DYNAMIC | DSHB_DATA_TYPE=STATIC (底层为静态缓存) |

### 4.2 P2-001 底层核对详情

| 核对项 | 说明 | 期望结果 | DSHB回填 |
|--------|------|----------|----------|
| **引擎重新计算** | 版本切换后底层引擎是否重新计算指标 | 否 (仅缓存刷新) | DSHB_ENGINE_RECOMPUTE=___ |
| **别名引擎刷新** | 版本切换后别名网关是否重新预热 | 是 (预期行为) | DSHB_ALIAS_REFRESH=___ |
| **指标计算耗时** | 版本切换后指标计算耗时变化 | 无变化 | DSHB_CALC_TIME=___ms |
| **数据源切换** | 版本切换后数据源是否切换 | 是 (预期行为) | DSHB_DATA_SOURCE_SWITCH=___ |

### 4.3 P2-002/004 底层核对详情

| 核对项 | 说明 | 期望结果 | DSHB回填 |
|--------|------|----------|----------|
| **并发响应时间** | 50并发下底层引擎响应时间 | < 1000ms | DSHB_CONCURRENT_RESPONSE=___ms |
| **DOM渲染竞争** | 前端DOM渲染竞争是否为瓶颈 | 是 (前端瓶颈) | DSHB_DOM_BOTTLENECK=TRUE |
| **内存使用** | 并发下内存使用是否异常 | 正常 (无泄漏) | DSHB_MEMORY_LEAK=0 |
| **CPU使用** | 并发下CPU使用是否异常 | 正常 (前端渲染占用) | DSHB_CPU_SPIKE=FALSE |

### 4.4 P2-003/005 底层核对详情

| 核对项 | 说明 | 期望结果 | DSHB回填 |
|--------|------|----------|----------|
| **数据类型** | 工业硅数据是否为静态缓存 | 是 (静态降级) | DSHB_DATA_TYPE=STATIC |
| **数据量** | 工业硅数据量是否较大 | 是 (含季节性数据) | DSHB_DATA_SIZE=___KB |
| **计算耗时** | 底层数据计算耗时 | 正常 (< 500ms) | DSHB_CALC_TIME=___ms |
| **降级策略** | 底层是否执行降级策略 | 是 (L2降级) | DSHB_DEGRADE_ACTIVE=TRUE |

---

## 5. 7项已知限制底层比对清单

### 5.1 已知限制比对总表

| # | 已知限制 | DSHE前端观测 | 期望DSHB底层行为 | DSHB回填字段 | 通过标准 |
|---|----------|-------------|-----------------|-------------|----------|
| 1 | 工业硅静态数据 | L2降级持续, 3.28s首慢 | 底层为静态缓存, 无动态数据 | DSHB_SI_DATA_TYPE=STATIC | DSHB_SI_DATA_TYPE=STATIC 且 DSHB_SI_DEGRADE=L2 |
| 2 | 7张降级图表 | 全部正确标记降级 | 底层降级策略执行正确 | DSHB_DEGRADE_COUNT=7 | DSHB_DEGRADE_COUNT=7 且 DSHB_DEGRADE_LAYERS正确 |
| 3 | 冷启动22.74s | 一次性, 已预热 | 底层别名引擎预热完成 | DSHB_WARMUP_COMPLETED=TRUE | DSHB_WARMUP_COMPLETED=TRUE 且 DSHB_CACHE_HIT=100% |
| 4 | 27%监控缺口 | 13项未接入, 持续存在 | 底层监控覆盖73% | DSHB_MONITORING_COVERAGE=73% | DSHB_MONITORING_COVERAGE=73% 且 DSHB_MONITORING_GAPS=13 |
| 5 | 10缺失指标 | 全部标注降级 | 底层10项指标无数据源 | DSHB_MISSING_METRICS=10 | DSHB_MISSING_METRICS=10 且 DSHB_DEGRADE_ACTIVE=TRUE |
| 6 | 34条tail_ambig | 全部降级提示 | 底层F2层歧义自动降级 | DSHB_AMBIG_COUNT=34 | DSHB_AMBIG_COUNT=34 且 DSHB_AMBIG_DEGRADE=TRUE |
| 7 | 2 P2 advisory | 持续存在, 文档建议 | 底层为文档建议, 非功能缺陷 | DSHB_ADVISORY_COUNT=2 | DSHB_ADVISORY_COUNT=2 且 DSHB_ADVISORY_TYPE=DOC |

### 5.2 限制1: 工业硅静态数据

| 核对项 | DSHE前端观测 | DSHB期望行为 | DSHB回填 |
|--------|-------------|-------------|----------|
| 降级层级 | L2 (橙色) | L2降级策略执行 | DSHB_SI_DEGRADE=___ |
| 数据状态 | 静态缓存 | 无动态数据源 | DSHB_SI_DATA_TYPE=___ |
| 加载耗时 | 3.28s | 前端渲染耗时 (非底层) | DSHB_SI_CALC_TIME=___ms |
| 降级文案 | "数据降级, 使用缓存值" | 降级策略触发 | DSHB_SI_DEGRADE_ACTIVE=___ |
| P1 SOP跟踪 | T+30d补全动态数据 | 底层规划补全 | DSHB_SI_FIX_PLAN=___ |

### 5.3 限制2: 7张降级图表

| 图表 | DSHE降级层级 | DSHB期望降级策略 | DSHB回填 |
|------|-------------|-----------------|----------|
| 工业硅价格 | L2 | L2降级 (静态缓存) | DSHB_DEGRADE_CHART_01=___ |
| 铝土矿产量 | L3 | L3降级 (数据缺失) | DSHB_DEGRADE_CHART_02=___ |
| 新能源乘用车 | L1 | L1降级 (信息提示) | DSHB_DEGRADE_CHART_03=___ |
| LME库存 | L1 | L1降级 (信息提示) | DSHB_DEGRADE_CHART_04=___ |
| 碳酸锂产量 | L2 | L2降级 (静态缓存) | DSHB_DEGRADE_CHART_05=___ |
| 硫酸镍价格 | L2 | L2降级 (静态缓存) | DSHB_DEGRADE_CHART_06=___ |
| 不锈钢库存 | L3 | L3降级 (数据缺失) | DSHB_DEGRADE_CHART_07=___ |

### 5.4 限制3: 冷启动22.74s

| 核对项 | DSHE前端观测 | DSHB期望行为 | DSHB回填 |
|--------|-------------|-------------|----------|
| 预热状态 | 已预热, 100%缓存命中 | 别名引擎预热完成 | DSHB_WARMUP_COMPLETED=___ |
| 冷启动耗时 | 22.74s (一次性) | 底层别名引擎初始化耗时 | DSHB_COLD_START=___ms |
| 缓存命中率 | 100% (预热后) | 底层缓存命中 | DSHB_CACHE_HIT=___% |
| 别名查询耗时 | 0.143ms (平均) | 底层别名解析耗时 | DSHB_ALIAS_QUERY_MS=___ |
| 预热执行时间 | S06 (发布窗口) | 底层预热完成时间 | DSHB_WARMUP_TIME=___ |

### 5.5 限制4: 27%监控缺口

| 核对项 | DSHE前端观测 | DSHB期望行为 | DSHB回填 |
|--------|-------------|-------------|----------|
| 监控覆盖 | 73% (从20%提升) | 底层监控覆盖73% | DSHB_MONITORING_COVERAGE=___% |
| 缺口数量 | 13项未接入 | 底层13项缺口已文档化 | DSHB_MONITORING_GAPS=___ |
| P0缺口 | 4项 | 底层4项P0缺口已分级 | DSHB_P0_GAPS=___ |
| P1缺口 | 8项 | 底层8项P1缺口已分级 | DSHB_P1_GAPS=___ |
| P2缺口 | 1项 | 底层1项P2缺口已分级 | DSHB_P2_GAPS=___ |

### 5.6 限制5: 10缺失指标

| 核对项 | DSHE前端观测 | DSHB期望行为 | DSHB回填 |
|--------|-------------|-------------|----------|
| 缺失数量 | 10项 | 底层10项指标无数据源 | DSHB_MISSING_METRICS=___ |
| 降级状态 | 全部标注降级 | 底层降级策略执行 | DSHB_MISSING_DEGRADE=___ |
| 影响图表 | 对应图表降级渲染 | 底层对应图表标记 | DSHB_AFFECTED_CHARTS=___ |
| 补全计划 | T+30d内补全 | 底层补全规划 | DSHB_MISSING_FIX_PLAN=___ |

### 5.7 限制6: 34条tail_ambig

| 核对项 | DSHE前端观测 | DSHB期望行为 | DSHB回填 |
|--------|-------------|-------------|----------|
| 歧义数量 | 34条 | 底层34条F2层歧义 | DSHB_AMBIG_COUNT=___ |
| 降级提示 | "别名歧义, 已选择最优候选" | 底层自动降级处理 | DSHB_AMBIG_DEGRADE=___ |
| 歧义类型 | F2层匹配, 需人工确认 | 底层F2层匹配结果 | DSHB_AMBIG_LAYER=___ |
| 查询次数 | 50次 (24h内) | 底层50次歧义查询 | DSHB_AMBIG_QUERIES=___ |

### 5.8 限制7: 2 P2 advisory

| 核对项 | DSHE前端观测 | DSHB期望行为 | DSHB回填 |
|--------|-------------|-------------|----------|
| 数量 | 2项 | 底层2项文档建议 | DSHB_ADVISORY_COUNT=___ |
| 类型 | 文档建议, 非功能缺陷 | 底层文档建议 | DSHB_ADVISORY_TYPE=___ |
| 影响 | 无 | 底层无影响 | DSHB_ADVISORY_IMPACT=___ |

---

## 6. 交叉核验核对表

### 6.1 完整交叉核验表

| # | 核验类别 | 核验项 | DSHE侧数据 | DSHB侧数据 (待回填) | 一致性判定 | 通过标准 | 状态 |
|---|----------|--------|-----------|-------------------|-----------|----------|------|
| 1 | 图表指标 | 32张完全匹配图表 | 32/32渲染正确 | DSHB_CHART_MATCH=___ | 待DSHB回填 | DSHB_CHART_MATCH=32/32 | ⏳ |
| 2 | 图表指标 | 7张降级图表降级标记 | 7/7正确标记 | DSHB_DEGRADE_COUNT=___ | 待DSHB回填 | DSHB_DEGRADE_COUNT=7 | ⏳ |
| 3 | 图表指标 | 图表数据点数量 | 全部正确 | DSHB_DATA_POINTS=___ | 待DSHB回填 | DSHB_DATA_POINTS=全部匹配 | ⏳ |
| 4 | 图表指标 | 图表坐标轴/图例 | 全部正确 | DSHB_AXES_LEGENDS=___ | 待DSHB回填 | DSHB_AXES_LEGENDS=全部匹配 | ⏳ |
| 5 | P2缺陷 | P2-001 Gate首次加载 | 前端缓存行为, 无引擎重算 | DSHB_ENGINE_RECOMPUTE=___ | 待DSHB回填 | DSHB_ENGINE_RECOMPUTE=FALSE | ⏳ |
| 6 | P2缺陷 | P2-002/004 Gate并发峰值 | 前端DOM竞争 | DSHB_CONCURRENT_RESPONSE=___ms | 待DSHB回填 | DSHB_CONCURRENT_RESPONSE < 1000ms | ⏳ |
| 7 | P2缺陷 | P2-003/005 工业硅加载 | 前端数据量大, 静态缓存 | DSHB_DATA_TYPE=___ | 待DSHB回填 | DSHB_DATA_TYPE=STATIC | ⏳ |
| 8 | 已知限制 | 限制1: 工业硅静态数据 | L2降级持续 | DSHB_SI_DEGRADE=___ | 待DSHB回填 | DSHB_SI_DEGRADE=L2 | ⏳ |
| 9 | 已知限制 | 限制2: 7张降级图表 | 全部正确标记 | DSHB_DEGRADE_COUNT=___ | 待DSHB回填 | DSHB_DEGRADE_COUNT=7 | ⏳ |
| 10 | 已知限制 | 限制3: 冷启动22.74s | 已预热, 100%缓存 | DSHB_WARMUP_COMPLETED=___ | 待DSHB回填 | DSHB_WARMUP_COMPLETED=TRUE | ⏳ |
| 11 | 已知限制 | 限制4: 27%监控缺口 | 13项未接入 | DSHB_MONITORING_COVERAGE=___% | 待DSHB回填 | DSHB_MONITORING_COVERAGE=73% | ⏳ |
| 12 | 已知限制 | 限制5: 10缺失指标 | 全部降级 | DSHB_MISSING_METRICS=___ | 待DSHB回填 | DSHB_MISSING_METRICS=10 | ⏳ |
| 13 | 已知限制 | 限制6: 34条tail_ambig | 全部降级提示 | DSHB_AMBIG_COUNT=___ | 待DSHB回填 | DSHB_AMBIG_COUNT=34 | ⏳ |
| 14 | 已知限制 | 限制7: 2 P2 advisory | 持续存在 | DSHB_ADVISORY_COUNT=___ | 待DSHB回填 | DSHB_ADVISORY_COUNT=2 | ⏳ |
| 15 | 全局 | 别名引擎解析率 | 100% (4643别名) | DSHB_ALIAS_RESOLVE_RATE=___% | 待DSHB回填 | DSHB_ALIAS_RESOLVE_RATE=100% | ⏳ |
| 16 | 全局 | 别名缓存命中率 | 100% | DSHB_CACHE_HIT_RATE=___% | 待DSHB回填 | DSHB_CACHE_HIT_RATE=100% | ⏳ |
| 17 | 全局 | 数据准确性 | 100% (前端展示) | DSHB_DATA_ACCURACY=___% | 待DSHB回填 | DSHB_DATA_ACCURACY=100% | ⏳ |
| 18 | 全局 | 降级体系一致性 | 4层全部正确 | DSHB_DEGRADE_SYSTEM=___ | 待DSHB回填 | DSHB_DEGRADE_SYSTEM=ALL_CORRECT | ⏳ |
| 19 | 全局 | 版本标识一致性 | V86.0-RC1-stable | DSHB_VERSION_TAG=___ | 待DSHB回填 | DSHB_VERSION_TAG=V86.0-RC1-stable | ⏳ |
| 20 | 全局 | 内存泄漏 | 0 | DSHB_MEMORY_LEAK=___ | 待DSHB回填 | DSHB_MEMORY_LEAK=0 | ⏳ |

### 6.2 交叉核验通过标准

| 标准 # | 标准描述 | 通过条件 | 权重 |
|--------|----------|----------|------|
| **CR-1** | 图表数据一致性 | 36/36图表DSHE前端展示值与DSHB底层计算值一致 | 40% |
| **CR-2** | P2缺陷归因正确 | 5项P2全部确认无底层引擎问题 | 25% |
| **CR-3** | 已知限制行为一致 | 7项限制DSHE前端观测与DSHB底层行为一致 | 25% |
| **CR-4** | 全局指标一致 | 别名解析率/缓存命中率/数据准确性/降级体系/版本标识全部一致 | 10% |

### 6.3 交叉核验最终裁定矩阵

| 通过标准 | 通过 | 未通过 | 说明 |
|----------|------|--------|------|
| CR-1 图表数据一致性 | — | — | 待DSHB回填 |
| CR-2 P2缺陷归因正确 | — | — | 待DSHB回填 |
| CR-3 已知限制行为一致 | — | — | 待DSHB回填 |
| CR-4 全局指标一致 | — | — | 待DSHB回填 |
| **综合裁定** | **✅ 通过** | **❌ 未通过** | 4项全部通过=PASS |

---

## 7. DSHB待回填字段说明

### 7.1 回填字段总表

| 字段名 | 类型 | 说明 | 关联核验项 |
|--------|------|------|-----------|
| DSHB_CHART_MATCH | 字符串 | DSHB底层图表匹配数量 (如 "32/32") | CR-1 |
| DSHB_DEGRADE_COUNT | 数字 | DSHB底层降级图表数量 | CR-1, CR-3 |
| DSHB_DATA_POINTS | 字符串 | DSHB底层数据点匹配结果 | CR-1 |
| DSHB_AXES_LEGENDS | 字符串 | DSHB底层坐标轴/图例匹配结果 | CR-1 |
| DSHB_ENGINE_RECOMPUTE | 布尔 | 版本切换后底层是否重新计算 | CR-2 |
| DSHB_CONCURRENT_RESPONSE | 数字 | 50并发下底层响应时间 (ms) | CR-2 |
| DSHB_DATA_TYPE | 字符串 | 工业硅数据类型 (STATIC/DYNAMIC) | CR-2 |
| DSHB_SI_DEGRADE | 字符串 | 工业硅降级层级 (L0/L1/L2/L3) | CR-3 |
| DSHB_WARMUP_COMPLETED | 布尔 | 别名引擎预热是否完成 | CR-3 |
| DSHB_MONITORING_COVERAGE | 数字 | 监控覆盖率 (%) | CR-3 |
| DSHB_MISSING_METRICS | 数字 | 缺失指标数量 | CR-3 |
| DSHB_AMBIG_COUNT | 数字 | tail_ambig数量 | CR-3 |
| DSHB_ADVISORY_COUNT | 数字 | P2 advisory数量 | CR-3 |
| DSHB_ALIAS_RESOLVE_RATE | 数字 | 别名解析率 (%) | CR-4 |
| DSHB_CACHE_HIT_RATE | 数字 | 缓存命中率 (%) | CR-4 |
| DSHB_DATA_ACCURACY | 数字 | 数据准确性 (%) | CR-4 |
| DSHB_DEGRADE_SYSTEM | 字符串 | 降级体系一致性 (ALL_CORRECT/ISSUE) | CR-4 |
| DSHB_VERSION_TAG | 字符串 | 版本标识 | CR-4 |
| DSHB_MEMORY_LEAK | 数字 | 内存泄漏次数 | CR-4 |

### 7.2 回填格式说明

DSHB回填数据格式示例:

```
# DSHB Cross-Validation Fill-Back
# Date: 2026-10-03
# Source: DSHB V86-RC1 底层巡检报告

DSHB_CHART_MATCH=32/32
DSHB_DEGRADE_COUNT=7
DSHB_DATA_POINTS=全部匹配
DSHB_AXES_LEGENDS=全部匹配
DSHB_ENGINE_RECOMPUTE=FALSE
DSHB_CONCURRENT_RESPONSE=850
DSHB_DATA_TYPE=STATIC
DSHB_SI_DEGRADE=L2
DSHB_WARMUP_COMPLETED=TRUE
DSHB_MONITORING_COVERAGE=73
DSHB_MISSING_METRICS=10
DSHB_AMBIG_COUNT=34
DSHB_ADVISORY_COUNT=2
DSHB_ALIAS_RESOLVE_RATE=100
DSHB_CACHE_HIT_RATE=100
DSHB_DATA_ACCURACY=100
DSHB_DEGRADE_SYSTEM=ALL_CORRECT
DSHB_VERSION_TAG=V86.0-RC1-stable
DSHB_MEMORY_LEAK=0

CROSS_VALIDATION_VERDICT=PASS
```

---

## 8. 交叉核验通过标准

### 8.1 通过标准详细说明

| 标准 | 通过条件 | 不通过条件 | 判定方法 |
|------|----------|-----------|----------|
| **CR-1** | DSHB_CHART_MATCH=32/32 且 DSHB_DEGRADE_COUNT=7 且 DSHB_DATA_POINTS=全部匹配 | 任一不满足 | DSHB回填字段比对 |
| **CR-2** | DSHB_ENGINE_RECOMPUTE=FALSE 且 DSHB_CONCURRENT_RESPONSE<1000ms 且 DSHB_DATA_TYPE=STATIC | 任一不满足 | DSHB回填字段比对 |
| **CR-3** | 全部7项限制DSHB回填值与期望值一致 | 任一不一致 | DSHB回填字段比对 |
| **CR-4** | 全部6项全局指标DSHB回填值与期望值一致 | 任一不一致 | DSHB回填字段比对 |

### 8.2 交叉核验最终裁定

```
┌──────────────────────────────────────────────────────────────────┐
│  CROSS-VALIDATION VERDICT                                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  ║
│  STATUS: ⏳ AWAITING DSHB RESULTS                                 ║
│                                                                  ║
│  CR-1 图表数据一致性:      ⏳ 待DSHB回填                          ║
│  CR-2 P2缺陷归因正确:      ⏳ 待DSHB回填                          ║
│  CR-3 已知限制行为一致:    ⏳ 待DSHB回填                          ║
│  CR-4 全局指标一致:        ⏳ 待DSHB回填                          ║
│                                                                  ║
│  ══════════════════════════════════════════════                    ║
│  VERDICT: ⏳ AWAITING DSHB — FILL BACK TO COMPLETE                ║
│  ══════════════════════════════════════════════                    ║
│                                                                  ║
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. 附录

### 9.1 文件信息

| 项目 | 值 |
|------|-----|
| **文件名** | v86_rc1_dshe_cross_validation_checklist_v7.md |
| **任务** | DSHE_V86_RC1_PRESENTATION_LAYER_PRE_AUDIT |
| **子任务** | T3.4 DSHB-DSHE跨端交叉核验核对清单 |
| **分支** | feature/v85-chart-template |
| **基线** | DSHE V7-RC1 (commit `f1d444e`), DSHB V86-RC1 (commit `79e34a1`) |
| **创建日期** | 2026-10-03 |
| **状态** | ✅ CHECKLIST READY — AWAITING DSHB RESULTS |

### 9.2 数据源索引

| 数据源 | 文件 | 用途 |
|--------|------|------|
| 发布窗口值守日志 | v86_rc1_dshe_release_window_page_watch_log_v7.md | P2缺陷来源 |
| 24h稳定性汇总 | v86_rc1_dshe_24h_page_stability_summary_v7.md | P2缺陷+已知限制24h数据 |
| T+0页面核验 | v86_rc1_dshe_t0_page_verify_v7.md | 图表/链接/降级验证 |
| P2缺陷台账 | v86_rc1_dshe_p2_backlog_and_longterm_sop_v7.md | P2缺陷详情 |
| DSHB Gate终审 | dshb_gate_upgrade_review/ | DSHB底层数据 (待回填) |

### 9.3 与DSHB对接说明

1. 本清单定义了DSHE侧全部交叉核验项及期望的DSHB回填字段
2. DSHB底层巡检完成后, 按第7节格式回填数据
3. 回填后按第8节通过标准进行最终裁定
4. 裁定通过后, 在 T3.5 验收初稿中填入交叉核验结论
5. 全部完成后可进入联合评审环节

---

*文档版本: V1.0*
*生成日期: 2026-10-03*
*工单: DSHE_V86_RC1_PRESENTATION_LAYER_PRE_AUDIT · T3.4*
*分支: feature/v85-chart-template*
*状态: ✅ CHECKLIST READY — AWAITING DSHB RESULTS*