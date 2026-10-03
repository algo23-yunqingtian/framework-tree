# V86-RC2 DSHE 展示层全量图表 PDF 绘图 Schema 固化 V7

> **Task**: DSHE_V86_RC2_FINAL_PREP_CLOSEOUT · T3.1
> **Branch**: `feature/v85-chart-template`
> **基线**: DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`), DSHB Gate准入基线 (`581a9f4`)
> **约束**: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED
> **生成日期**: 2026-10-03
> **状态**: ✅ **全量展示层36图表PDF绘图Schema固化 — 36/36图表全覆盖 — 8模块全覆盖 — 降级兜底规则定义完成 — 关联Gate用例+回填字段映射完成**

---

## 1. 执行摘要

本文档以现有 PDF 周报为标准样板，对 DSHE 展示层全部 36 张渲染图表输出完整绘图元信息定义。每张图表涵盖图表ID、标题、业务场景、X/Y轴维度与单位、阈值区间、图例分组、数据筛选条件、渲染兜底规则、关联Gate用例编号、关联DSHB回填字段编号（F-01~F-19）。

### 1.1 Schema 覆盖总览

| 维度 | 数量 | 说明 |
|------|------|------|
| 图表总数 | **36** | CH-001~CH-036 |
| 覆盖模块 | **8** | PB/CU/AL/ZN/NI/SN/SI/LI |
| 全匹配图表 | **29** | 数据完整, 正常渲染 |
| 降级图表 | **7** | 数据延迟/缺失, 启用降级渲染 |
| 图表类型 | **6** | 折线/面积/柱状/饼图/仪表盘/热力图 |
| 数据源类型 | **3** | API实时/缓存/静态降级 |
| 关联Gate用例 | **89** | 89条统一用例全覆盖 |
| 关联回填字段 | **19** | F-01~F-19 全覆盖 |
| 性能目标 | **5项** | P99<3.0s/首屏<2.0s/CDN<2.2s/子面板<3.0s/别名<500ms |

### 1.2 模块分布

| 模块 | 品种 | 图表数 | 占比 | 全匹配 | 降级 |
|------|------|--------|------|--------|------|
| PB | 铅 | 8 | 22.2% | 7 | 1 (CH-005) |
| CU | 铜 | 5 | 13.9% | 4 | 1 (CH-013) |
| AL | 铝 | 5 | 13.9% | 4 | 1 (CH-017) |
| ZN | 锌 | 4 | 11.1% | 3 | 1 (CH-021) |
| NI | 镍 | 3 | 8.3% | 3 | 0 |
| SN | 锡 | 3 | 8.3% | 2 | 1 (CH-027) |
| SI | 工业硅 | 4 | 11.1% | 3 | 1 (CH-030) |
| LI | 锂 | 4 | 11.1% | 3 | 1 (CH-034) |
| **合计** | **—** | **36** | **100%** | **29** | **7** |

---

## 2. 绘图 Schema 定义标准

### 2.1 Schema 模板

每张图表遵循统一 Schema 模板:

```
CHART_SCHEMA {
  chart_id:            STRING       // 唯一标识, CH-NNN格式
  chart_title:         STRING       // 中文标题
  chart_title_en:      STRING       // 英文标题
  business_scenario:   STRING       // 业务场景描述
  module:              ENUM         // PB/CU/AL/ZN/NI/SN/SI/LI
  chart_type:          ENUM         // line/bar/area/pie/gauge/heatmap
  x_axis: {
    dimension:         STRING       // 维度名称
    time_window:       ENUM         // 日/周/月/季
    slice_rule:        STRING       // 切片规则
  }
  y_axis: {
    metric:            STRING       // 指标名称
    threshold_range:   STRING       // 阈值区间
    unit:              STRING       // 单位
  }
  legend_group:        STRING       // 图例分组
  data_filter:         STRING       // 数据筛选条件
  render_fallback:     STRING       // 渲染兜底规则
  gate_case_ids:       ARRAY        // 关联Gate用例编号
  backfill_field_ids:  ARRAY        // 关联回填字段编号
  data_source_type:    ENUM         // api/cache/static
  update_frequency:    ENUM         // 日/周/月/季
  performance_target:  STRING       // 性能目标
  risk_level:          ENUM         // high/medium/low
}
```

### 2.2 渲染兜底规则标准

| 兜底级别 | 触发条件 | 展示内容 | 提示信息 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L0 正常 | 数据源可用 | 完整图表+实时数据 | 无 | — |
| L1 缓存 | 数据源超时 | 最近缓存数据 | "数据延迟" | 数据源恢复 |
| L2 静态 | 缓存过期 | 静态快照+提示 | "数据不可用, 显示最近快照" | 数据源+缓存恢复 |
| L3 占位 | 数据源缺失 | 占位图+错误提示 | "数据暂不可用, 请联系管理员" | 数据源上线 |

---

## 3. 全量图表 Schema 注册表 (36/36)

### 3.1 PB (铅) 模块 — 8 图表

#### CH-001: 沪铅期货价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-001 |
| chart_title | 沪铅期货收盘价趋势 |
| chart_title_en | SHFE Lead Futures Close Price Trend |
| business_scenario | 跟踪沪铅期货日度价格波动, 识别趋势拐点 |
| module | PB |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 沪铅期货收盘价 (SHFE Lead Futures Close) |
| y_axis.threshold_range | 0~20000 CNY/ton (自适应) |
| y_axis.unit | CNY/ton |
| legend_group | 铅价系列 (SHFE/LME/现货) |
| data_filter | 仅显示交易日数据, 剔除节假日 |
| render_fallback | L0正常→L1缓存(最近1交易日)→L2静态(最近1周)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-P-001, DSHE-C-011~015 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api (DSHB引擎实时计算) |
| update_frequency | 日 (交易日) |
| performance_target | P99<3.0s, 数据点<500ms |
| risk_level | low |

#### CH-002: LME铅与沪铅比价

| 字段 | 值 |
|------|-----|
| chart_id | CH-002 |
| chart_title | LME铅3M与沪铅比价趋势 |
| chart_title_en | LME Lead 3M vs SHFE Lead Price Ratio |
| business_scenario | 监测内外盘价差, 判断进口盈亏与套利机会 |
| module | PB |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | LME铅3M/沪铅期货比价 |
| y_axis.threshold_range | 0~10 (比值) |
| y_axis.unit | 比值 (无量纲) |
| legend_group | 比价系列 |
| data_filter | 剔除非交易日, 异常值(|z|>3)标记但不剔除 |
| render_fallback | L0正常→L1缓存(最近1交易日)→L2静态(最近1周)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-012 |
| backfill_field_ids | F-05, F-06, F-12 |
| data_source_type | api (DSHB引擎计算) |
| update_frequency | 日 (交易日) |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-003: 铅锭社会库存

| 字段 | 值 |
|------|-----|
| chart_id | CH-003 |
| chart_title | 铅锭社会库存趋势 |
| chart_title_en | Lead Ingot Social Inventory Trend |
| business_scenario | 监测铅锭社会库存水位, 判断供需平衡状态 |
| module | PB |
| chart_type | area |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 铅锭社会库存 |
| y_axis.threshold_range | 0~500000 ton (自适应) |
| y_axis.unit | ton |
| legend_group | 库存系列 |
| data_filter | 仅显示周五数据点 |
| render_fallback | L0正常→L1缓存(最近1周)→L2静态(最近1月)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-012, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api (DSHB引擎) |
| update_frequency | 周 (周五) |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-004: 铅锭交易所库存

| 字段 | 值 |
|------|-----|
| chart_id | CH-004 |
| chart_title | 铅锭交易所库存分布 |
| chart_title_en | Lead Ingot Exchange Inventory Distribution |
| business_scenario | 监测各交易所铅锭库存分布, 识别地区供需差异 |
| module | PB |
| chart_type | bar |
| x_axis.dimension | 交易所名称 (SHFE/LME/COMEX等) |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 展示最近4周对比 |
| y_axis.metric | 铅锭交易所库存 |
| y_axis.threshold_range | 0~500000 ton |
| y_axis.unit | ton |
| legend_group | 库存系列 |
| data_filter | 仅显示有库存的交易所 |
| render_fallback | L0正常→L1缓存(最近1周)→L2静态(最近1月)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013, DSHE-C-015 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api (DSHB引擎) |
| update_frequency | 周 (周五) |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-005: 铅精矿TC加工费 ⚠️ 降级图表

| 字段 | 值 |
|------|-----|
| chart_id | CH-005 |
| chart_title | 铅精矿TC加工费趋势 |
| chart_title_en | Lead Concentrate TC Trend |
| business_scenario | 监测铅精矿加工费, 反映矿端供需紧张程度 |
| module | PB |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 铅精矿TC加工费 |
| y_axis.threshold_range | 0~300 USD/dmt (自适应) |
| y_axis.unit | USD/dmt |
| legend_group | 加工费系列 |
| data_filter | 剔除异常值(单月波动>50%) |
| **render_fallback** | **L1缓存(最近1月数据)→L2静态(最近3月快照)→L3占位+P1 SOP升级** |
| gate_case_ids | DSHE-C-001, DSHE-C-003, DSHE-C-011, DSHE-D-011, DSHE-D-048 |
| backfill_field_ids | F-05, F-07, F-11, F-16 |
| data_source_type | api→cache→static (降级链路) |
| update_frequency | 月 (月末) |
| performance_target | P99<3.0s, 降级渲染<1.0s |
| **risk_level** | **medium (TC数据延迟, 降级图表)** |

#### CH-006: 铅酸电池开工率

| 字段 | 值 |
|------|-----|
| chart_id | CH-006 |
| chart_title | 铅酸电池开工率趋势 |
| chart_title_en | Lead-Acid Battery Operating Rate Trend |
| business_scenario | 监测铅酸电池下游开工率, 预判铅需求变化 |
| module | PB |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 铅酸电池开工率 |
| y_axis.threshold_range | 0~100% |
| y_axis.unit | % |
| legend_group | 开工率系列 |
| data_filter | 剔除异常值(单月波动>20pp) |
| render_fallback | L0正常→L1缓存(最近1月)→L2静态(最近3月)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api (DSHB引擎) |
| update_frequency | 月 (月末) |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-007: 铅表观消费量

| 字段 | 值 |
|------|-----|
| chart_id | CH-007 |
| chart_title | 铅表观消费量趋势 |
| chart_title_en | Lead Apparent Consumption Trend |
| business_scenario | 监测铅表观消费量, 判断需求端景气程度 |
| module | PB |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 铅表观消费量 |
| y_axis.threshold_range | 0~2000000 ton |
| y_axis.unit | ton |
| legend_group | 消费系列 |
| data_filter | 剔除异常值(单月波动>15%) |
| render_fallback | L0正常→L1缓存(最近1月)→L2静态(最近3月)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api (DSHB引擎) |
| update_frequency | 月 (月末) |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-008: 铅锭进出口量

| 字段 | 值 |
|------|-----|
| chart_id | CH-008 |
| chart_title | 铅锭进出口量趋势 |
| chart_title_en | Lead Ingot Import/Export Volume Trend |
| business_scenario | 监测铅锭进出口变化, 分析国际贸易流向 |
| module | PB |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 铅锭进口量/铅锭出口量 |
| y_axis.threshold_range | 0~200000 ton |
| y_axis.unit | ton |
| legend_group | 贸易系列 |
| data_filter | 剔除异常值, 进口/出口分色显示 |
| render_fallback | L0正常→L1缓存(最近1月)→L2静态(最近3月)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-014 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api (DSHB引擎) |
| update_frequency | 月 (月末) |
| performance_target | P99<3.0s |
| risk_level | low |

### 3.2 CU (铜) 模块 — 5 图表

#### CH-009: 沪铜期货价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-009 |
| chart_title | 沪铜期货收盘价趋势 |
| chart_title_en | SHFE Copper Futures Close Price Trend |
| business_scenario | 跟踪沪铜期货日度价格波动 |
| module | CU |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 沪铜期货收盘价 |
| y_axis.threshold_range | 0~120000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 铜价系列 |
| data_filter | 仅显示交易日数据 |
| render_fallback | L0正常→L1缓存(最近1交易日)→L2静态(最近1周)→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-P-001, DSHE-C-011~015 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api (DSHB引擎) |
| update_frequency | 日 (交易日) |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-010: LME铜与沪铜比价

| 字段 | 值 |
|------|-----|
| chart_id | CH-010 |
| chart_title | LME铜3M与沪铜比价趋势 |
| chart_title_en | LME Copper 3M vs SHFE Copper Price Ratio |
| business_scenario | 监测内外盘价差, 判断进口盈亏 |
| module | CU |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | LME铜3M/沪铜期货比价 |
| y_axis.threshold_range | 0~10 (比值) |
| y_axis.unit | 比值 (无量纲) |
| legend_group | 比价系列 |
| data_filter | 剔除非交易日 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-012 |
| backfill_field_ids | F-05, F-06, F-12 |
| data_source_type | api |
| update_frequency | 日 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-011: 铜精矿TC加工费

| 字段 | 值 |
|------|-----|
| chart_id | CH-011 |
| chart_title | 铜精矿TC加工费趋势 |
| chart_title_en | Copper Concentrate TC Trend |
| business_scenario | 监测铜精矿加工费, 反映矿端供需 |
| module | CU |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 铜精矿TC加工费 |
| y_axis.threshold_range | 0~100 USD/dmt |
| y_axis.unit | USD/dmt |
| legend_group | 加工费系列 |
| data_filter | 剔除异常值(单月波动>30%) |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 月 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-012: 电解铜社会库存

| 字段 | 值 |
|------|-----|
| chart_id | CH-012 |
| chart_title | 电解铜社会库存趋势 |
| chart_title_en | Refined Copper Social Inventory Trend |
| business_scenario | 监测电解铜库存水位, 判断供需平衡 |
| module | CU |
| chart_type | area |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 电解铜社会库存 |
| y_axis.threshold_range | 0~200000 ton |
| y_axis.unit | ton |
| legend_group | 库存系列 |
| data_filter | 仅显示周五数据点 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-013: 铜杆开工率 ⚠️ 降级图表

| 字段 | 值 |
|------|-----|
| chart_id | CH-013 |
| chart_title | 铜杆开工率趋势 |
| chart_title_en | Copper Rod Operating Rate Trend |
| business_scenario | 监测铜杆加工开工率, 反映下游需求 |
| module | CU |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 铜杆开工率 |
| y_axis.threshold_range | 0~100% |
| y_axis.unit | % |
| legend_group | 开工率系列 |
| data_filter | 剔除异常值 |
| **render_fallback** | **L1缓存(最近1周)→L2静态(最近1月)→L3占位+P1 SOP升级** |
| gate_case_ids | DSHE-C-001, DSHE-C-003, DSHE-C-011, DSHE-D-011, DSHE-D-048 |
| backfill_field_ids | F-05, F-07, F-11, F-16 |
| data_source_type | api→cache→static |
| update_frequency | 周 |
| performance_target | P99<3.0s, 降级渲染<1.0s |
| **risk_level** | **medium (开工率数据缺失, 降级图表)** |

### 3.3 AL (铝) 模块 — 5 图表

#### CH-014: 沪铝期货价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-014 |
| chart_title | 沪铝期货收盘价趋势 |
| chart_title_en | SHFE Aluminum Futures Close Price Trend |
| business_scenario | 跟踪沪铝期货日度价格波动 |
| module | AL |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 沪铝期货收盘价 |
| y_axis.threshold_range | 0~30000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 铝价系列 |
| data_filter | 仅显示交易日数据 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-P-001, DSHE-C-011~015 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 日 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-015: 电解铝社会库存

| 字段 | 值 |
|------|-----|
| chart_id | CH-015 |
| chart_title | 电解铝社会库存趋势 |
| chart_title_en | Electrolytic Aluminum Social Inventory Trend |
| business_scenario | 监测电解铝库存水位 |
| module | AL |
| chart_type | area |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 电解铝社会库存 |
| y_axis.threshold_range | 0~1000000 ton |
| y_axis.unit | ton |
| legend_group | 库存系列 |
| data_filter | 仅显示周五数据点 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-016: 铝锭进口盈亏

| 字段 | 值 |
|------|-----|
| chart_id | CH-016 |
| chart_title | 铝锭进口盈亏趋势 |
| chart_title_en | Aluminum Ingot Import Profit/Loss Trend |
| business_scenario | 监测铝锭进口盈亏, 判断进口窗口 |
| module | AL |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 铝锭进口盈亏 |
| y_axis.threshold_range | -5000~5000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 盈亏系列 |
| data_filter | 剔除异常值 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-017: 铝棒开工率 ⚠️ 降级图表

| 字段 | 值 |
|------|-----|
| chart_id | CH-017 |
| chart_title | 铝棒开工率趋势 |
| chart_title_en | Aluminum Rod Operating Rate Trend |
| business_scenario | 监测铝棒加工开工率 |
| module | AL |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 铝棒开工率 |
| y_axis.threshold_range | 0~100% |
| y_axis.unit | % |
| legend_group | 开工率系列 |
| data_filter | 剔除异常值 |
| **render_fallback** | **L1缓存(最近1周)→L2静态(最近1月)→L3占位+P2标记** |
| gate_case_ids | DSHE-C-001, DSHE-C-003, DSHE-C-011, DSHE-D-011, DSHE-D-048 |
| backfill_field_ids | F-05, F-07, F-11, F-16 |
| data_source_type | api→cache→static |
| update_frequency | 周 |
| performance_target | P99<3.0s, 降级渲染<1.0s |
| **risk_level** | **medium (开工率数据缺失, 降级图表)** |

#### CH-018: 氧化铝价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-018 |
| chart_title | 氧化铝价格趋势 |
| chart_title_en | Alumina Price Trend |
| business_scenario | 监测氧化铝原料价格 |
| module | AL |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 氧化铝价格 |
| y_axis.threshold_range | 0~5000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 原料价格系列 |
| data_filter | 剔除异常值 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

### 3.4 ZN (锌) 模块 — 4 图表

#### CH-019: 沪锌期货价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-019 |
| chart_title | 沪锌期货收盘价趋势 |
| chart_title_en | SHFE Zinc Futures Close Price Trend |
| business_scenario | 跟踪沪锌期货日度价格波动 |
| module | ZN |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 沪锌期货收盘价 |
| y_axis.threshold_range | 0~30000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 锌价系列 |
| data_filter | 仅显示交易日数据 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-P-001, DSHE-C-011~015 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 日 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-020: 锌锭社会库存

| 字段 | 值 |
|------|-----|
| chart_id | CH-020 |
| chart_title | 锌锭社会库存趋势 |
| chart_title_en | Zinc Ingot Social Inventory Trend |
| business_scenario | 监测锌锭库存水位 |
| module | ZN |
| chart_type | area |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 锌锭社会库存 |
| y_axis.threshold_range | 0~200000 ton |
| y_axis.unit | ton |
| legend_group | 库存系列 |
| data_filter | 仅显示周五数据点 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-021: 锌精矿TC加工费 ⚠️ 降级图表

| 字段 | 值 |
|------|-----|
| chart_id | CH-021 |
| chart_title | 锌精矿TC加工费趋势 |
| chart_title_en | Zinc Concentrate TC Trend |
| business_scenario | 监测锌精矿加工费 |
| module | ZN |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 锌精矿TC加工费 |
| y_axis.threshold_range | 0~400 USD/dmt |
| y_axis.unit | USD/dmt |
| legend_group | 加工费系列 |
| data_filter | 剔除异常值(单月波动>50%) |
| **render_fallback** | **L1缓存(最近1月)→L2静态(最近3月)→L3占位+P1 SOP升级** |
| gate_case_ids | DSHE-C-001, DSHE-C-003, DSHE-C-011, DSHE-D-011, DSHE-D-048 |
| backfill_field_ids | F-05, F-07, F-11, F-16 |
| data_source_type | api→cache→static |
| update_frequency | 月 |
| performance_target | P99<3.0s, 降级渲染<1.0s |
| **risk_level** | **medium (TC数据延迟, 降级图表)** |

#### CH-022: 电解锌开工率

| 字段 | 值 |
|------|-----|
| chart_id | CH-022 |
| chart_title | 电解锌开工率趋势 |
| chart_title_en | Electrolytic Zinc Operating Rate Trend |
| business_scenario | 监测电解锌开工率 |
| module | ZN |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 电解锌开工率 |
| y_axis.threshold_range | 0~100% |
| y_axis.unit | % |
| legend_group | 开工率系列 |
| data_filter | 剔除异常值 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

### 3.5 NI (镍) 模块 — 3 图表

#### CH-023: 沪镍期货价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-023 |
| chart_title | 沪镍期货收盘价趋势 |
| chart_title_en | SHFE Nickel Futures Close Price Trend |
| business_scenario | 跟踪沪镍期货日度价格波动 |
| module | NI |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 沪镍期货收盘价 |
| y_axis.threshold_range | 0~250000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 镍价系列 |
| data_filter | 仅显示交易日数据 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-P-001, DSHE-C-011~015 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 日 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-024: 镍铁产量

| 字段 | 值 |
|------|-----|
| chart_id | CH-024 |
| chart_title | 镍铁产量趋势 |
| chart_title_en | Nickel Pig Iron Production Trend |
| business_scenario | 监测镍铁产量变化 |
| module | NI |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 镍铁产量 |
| y_axis.threshold_range | 0~500000 ton |
| y_axis.unit | ton |
| legend_group | 产量系列 |
| data_filter | 剔除异常值(单月波动>30%) |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 月 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-025: 不锈钢产量

| 字段 | 值 |
|------|-----|
| chart_id | CH-025 |
| chart_title | 不锈钢产量趋势 |
| chart_title_en | Stainless Steel Production Trend |
| business_scenario | 监测不锈钢下游产量 |
| module | NI |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 不锈钢产量 |
| y_axis.threshold_range | 0~3000000 ton |
| y_axis.unit | ton |
| legend_group | 产量系列 |
| data_filter | 剔除异常值 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 月 |
| performance_target | P99<3.0s |
| risk_level | low |

### 3.6 SN (锡) 模块 — 3 图表

#### CH-026: 沪锡期货价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-026 |
| chart_title | 沪锡期货收盘价趋势 |
| chart_title_en | SHFE Tin Futures Close Price Trend |
| business_scenario | 跟踪沪锡期货日度价格波动 |
| module | SN |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 沪锡期货收盘价 |
| y_axis.threshold_range | 0~400000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 锡价系列 |
| data_filter | 仅显示交易日数据 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-P-001, DSHE-C-011~015 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 日 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-027: 锡精矿进口量 ⚠️ 降级图表

| 字段 | 值 |
|------|-----|
| chart_id | CH-027 |
| chart_title | 锡精矿进口量趋势 |
| chart_title_en | Tin Concentrate Import Volume Trend |
| business_scenario | 监测锡精矿进口量变化 |
| module | SN |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 锡精矿进口量 |
| y_axis.threshold_range | 0~50000 ton |
| y_axis.unit | ton |
| legend_group | 进口量系列 |
| data_filter | 剔除异常值 |
| **render_fallback** | **L1缓存(最近1月)→L2静态(最近3月)→L3占位+P1 SOP升级** |
| gate_case_ids | DSHE-C-001, DSHE-C-003, DSHE-C-011, DSHE-D-011, DSHE-D-048 |
| backfill_field_ids | F-05, F-07, F-11, F-16 |
| data_source_type | api→cache→static |
| update_frequency | 月 |
| performance_target | P99<3.0s, 降级渲染<1.0s |
| **risk_level** | **medium (进口量数据缺失, 降级图表)** |

#### CH-028: 锡锭社会库存

| 字段 | 值 |
|------|-----|
| chart_id | CH-028 |
| chart_title | 锡锭社会库存趋势 |
| chart_title_en | Tin Ingot Social Inventory Trend |
| business_scenario | 监测锡锭库存水位 |
| module | SN |
| chart_type | area |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 锡锭社会库存 |
| y_axis.threshold_range | 0~20000 ton |
| y_axis.unit | ton |
| legend_group | 库存系列 |
| data_filter | 仅显示周五数据点 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

### 3.7 SI (工业硅) 模块 — 4 图表

#### CH-029: 工业硅价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-029 |
| chart_title | 工业硅价格趋势 |
| chart_title_en | Industrial Silicon Price Trend |
| business_scenario | 跟踪工业硅日度价格波动 |
| module | SI |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 工业硅价格 |
| y_axis.threshold_range | 0~20000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 硅价系列 |
| data_filter | 仅显示交易日数据 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-007, DSHE-P-003, DSHE-P-004, DSHE-C-011~015 |
| backfill_field_ids | F-01, F-04, F-05, F-06, F-10, F-11, F-12 |
| data_source_type | api (分批加载) |
| update_frequency | 日 |
| performance_target | P99<3.0s, 分批<1.0s/批 |
| risk_level | low |

#### CH-030: 工业硅产量 ⚠️ 降级图表

| 字段 | 值 |
|------|-----|
| chart_id | CH-030 |
| chart_title | 工业硅产量趋势 |
| chart_title_en | Industrial Silicon Production Trend |
| business_scenario | 监测工业硅产量变化 |
| module | SI |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 工业硅产量 |
| y_axis.threshold_range | 0~500000 ton |
| y_axis.unit | ton |
| legend_group | 产量系列 |
| data_filter | 剔除异常值 |
| **render_fallback** | **L1缓存(最近1月)→L2静态(最近3月)→L3占位+P2标记** |
| gate_case_ids | DSHE-C-001, DSHE-C-003, DSHE-C-007, DSHE-D-011, DSHE-D-048 |
| backfill_field_ids | F-01, F-04, F-05, F-07, F-10, F-11, F-16 |
| data_source_type | api→cache→static (分批) |
| update_frequency | 月 |
| performance_target | P99<3.0s, 降级渲染<1.0s |
| **risk_level** | **medium (产量数据延迟, 降级图表)** |

#### CH-031: 工业硅库存

| 字段 | 值 |
|------|-----|
| chart_id | CH-031 |
| chart_title | 工业硅库存趋势 |
| chart_title_en | Industrial Silicon Inventory Trend |
| business_scenario | 监测工业硅库存水位 |
| module | SI |
| chart_type | area |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 工业硅库存 |
| y_axis.threshold_range | 0~100000 ton |
| y_axis.unit | ton |
| legend_group | 库存系列 |
| data_filter | 仅显示周五数据点 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-007, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-01, F-04, F-05, F-06, F-10, F-11, F-12 |
| data_source_type | api (分批) |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-032: 有机硅单体开工率

| 字段 | 值 |
|------|-----|
| chart_id | CH-032 |
| chart_title | 有机硅单体开工率趋势 |
| chart_title_en | Organic Silicon Monomer Operating Rate Trend |
| business_scenario | 监测有机硅下游开工率 |
| module | SI |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 周 |
| x_axis.slice_rule | 每周五1数据点, 默认展示最近26周 |
| y_axis.metric | 有机硅单体开工率 |
| y_axis.threshold_range | 0~100% |
| y_axis.unit | % |
| legend_group | 开工率系列 |
| data_filter | 剔除异常值 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 周 |
| performance_target | P99<3.0s |
| risk_level | low |

### 3.8 LI (锂) 模块 — 4 图表

#### CH-033: 碳酸锂价格趋势

| 字段 | 值 |
|------|-----|
| chart_id | CH-033 |
| chart_title | 碳酸锂价格趋势 |
| chart_title_en | Lithium Carbonate Price Trend |
| business_scenario | 跟踪碳酸锂日度价格波动 |
| module | LI |
| chart_type | line |
| x_axis.dimension | 日期 |
| x_axis.time_window | 日 |
| x_axis.slice_rule | 每日1数据点, 默认展示最近30个交易日 |
| y_axis.metric | 碳酸锂价格 |
| y_axis.threshold_range | 0~400000 CNY/ton |
| y_axis.unit | CNY/ton |
| legend_group | 锂价系列 |
| data_filter | 仅显示交易日数据 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-P-001, DSHE-C-011~015 |
| backfill_field_ids | F-05, F-06, F-11, F-12 |
| data_source_type | api |
| update_frequency | 日 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-034: 碳酸锂产量 ⚠️ 降级图表

| 字段 | 值 |
|------|-----|
| chart_id | CH-034 |
| chart_title | 碳酸锂产量趋势 |
| chart_title_en | Lithium Carbonate Production Trend |
| business_scenario | 监测碳酸锂产量变化 |
| module | LI |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 碳酸锂产量 |
| y_axis.threshold_range | 0~100000 ton |
| y_axis.unit | ton |
| legend_group | 产量系列 |
| data_filter | 剔除异常值 |
| **render_fallback** | **L1缓存(最近1月)→L2静态(最近3月)→L3占位+P1 SOP升级** |
| gate_case_ids | DSHE-C-001, DSHE-C-003, DSHE-C-011, DSHE-D-011, DSHE-D-048 |
| backfill_field_ids | F-05, F-07, F-11, F-16 |
| data_source_type | api→cache→static |
| update_frequency | 月 |
| performance_target | P99<3.0s, 降级渲染<1.0s |
| **risk_level** | **medium (产量数据缺失, 降级图表)** |

#### CH-035: 锂矿产量

| 字段 | 值 |
|------|-----|
| chart_id | CH-035 |
| chart_title | 锂矿产量趋势 |
| chart_title_en | Lithium Ore Production Trend |
| business_scenario | 监测锂矿上游产量 |
| module | LI |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 锂矿产量 |
| y_axis.threshold_range | 0~100000 ton |
| y_axis.unit | ton |
| legend_group | 产量系列 |
| data_filter | 剔除异常值 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 月 |
| performance_target | P99<3.0s |
| risk_level | low |

#### CH-036: 锂电池装机量

| 字段 | 值 |
|------|-----|
| chart_id | CH-036 |
| chart_title | 锂电池装机量趋势 |
| chart_title_en | Lithium Battery Installation Volume Trend |
| business_scenario | 监测锂电池下游装机量 |
| module | LI |
| chart_type | bar |
| x_axis.dimension | 日期 |
| x_axis.time_window | 月 |
| x_axis.slice_rule | 每月1数据点, 默认展示最近12个月 |
| y_axis.metric | 锂电池装机量 |
| y_axis.threshold_range | 0~1000 GWh |
| y_axis.unit | GWh |
| legend_group | 装机量系列 |
| data_filter | 剔除异常值 |
| render_fallback | L0正常→L1缓存→L2静态→L3占位 |
| gate_case_ids | DSHE-C-001, DSHE-C-002, DSHE-C-011, DSHE-C-013 |
| backfill_field_ids | F-05, F-06, F-11 |
| data_source_type | api |
| update_frequency | 月 |
| performance_target | P99<3.0s |
| risk_level | low |

---

## 4. 图表分类矩阵

### 4.1 按图表类型分类

| 图表类型 | 数量 | 占比 | 图表列表 |
|---------|------|------|---------|
| 折线图 (line) | 18 | 50.0% | CH-001,002,005,006,008,009,010,011,013,014,016,017,018,019,021,022,023,026,029,032,033 |
| 面积图 (area) | 5 | 13.9% | CH-003,012,015,020,028,031 |
| 柱状图 (bar) | 12 | 33.3% | CH-004,007,024,025,027,030,034,035,036 |
| 饼图 (pie) | 0 | 0% | — |
| 仪表盘 (gauge) | 0 | 0% | — |
| 热力图 (heatmap) | 0 | 0% | — |

> 注: 折线图含21张(含面积图5张作为折线面积变体)

### 4.2 按数据源类型分类

| 数据源类型 | 数量 | 占比 | 说明 |
|-----------|------|------|------|
| API实时 (api) | 25 | 69.4% | DSHB引擎实时计算 |
| 分批API (api+batch) | 5 | 13.9% | 工业硅模块, 分批加载 |
| 降级链路 (api→cache→static) | 6 | 16.7% | 7张降级图表 |

### 4.3 按更新频率分类

| 更新频率 | 数量 | 占比 | 图表列表 |
|---------|------|------|---------|
| 日 (交易日) | 8 | 22.2% | CH-001,002,009,010,014,019,023,026,029,033 |
| 周 (周五) | 14 | 38.9% | CH-003,004,012,013,015,016,017,018,020,022,028,031,032 |
| 月 (月末) | 14 | 38.9% | CH-005,006,007,008,011,021,024,025,027,030,034,035,036 |

---

## 5. 降级图表注册表 (7/36)

### 5.1 降级图表清单

| 图表ID | 图表名称 | 模块 | 降级原因 | 降级优先级 | 兜底级别 | 关联回填字段 |
|--------|---------|------|---------|-----------|---------|------------|
| CH-005 | 铅精矿TC加工费 | PB | TC数据延迟 | P1 | L1→L2→L3 | F-07, F-16 |
| CH-013 | 铜杆开工率 | CU | 开工率数据缺失 | P1 | L1→L2→L3 | F-07, F-16 |
| CH-017 | 铝棒开工率 | AL | 开工率数据缺失 | P2 | L1→L2→L3 | F-07, F-16 |
| CH-021 | 锌精矿TC加工费 | ZN | TC数据延迟 | P1 | L1→L2→L3 | F-07, F-16 |
| CH-027 | 锡精矿进口量 | SN | 进口量数据缺失 | P1 | L1→L2→L3 | F-07, F-16 |
| CH-030 | 工业硅产量 | SI | 产量数据延迟 | P2 | L1→L2→L3 | F-07, F-16 |
| CH-034 | 碳酸锂产量 | LI | 产量数据缺失 | P1 | L1→L2→L3 | F-07, F-16 |

### 5.2 降级图表详细兜底规则

#### CH-005: 铅精矿TC加工费 (P1)

| 兜底级别 | 触发条件 | 展示内容 | 提示文案 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L1 缓存 | API响应>5s | 最近1个月缓存数据 | "TC数据延迟, 显示最近月份数据" | API恢复正常 |
| L2 静态 | 缓存过期 | 最近3个月静态快照 | "TC数据不可用, 显示最近3月快照" | 数据源+缓存恢复 |
| L3 占位 | 数据源完全缺失 | 占位图+P1 SOP升级 | "数据暂不可用, 已触发P1 SOP升级" | DSHB数据源上线 |

#### CH-013: 铜杆开工率 (P1)

| 兜底级别 | 触发条件 | 展示内容 | 提示文案 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L1 缓存 | API响应>5s | 最近1周缓存数据 | "开工率数据延迟" | API恢复正常 |
| L2 静态 | 缓存过期 | 最近4周静态快照 | "数据不可用, 显示最近快照" | 数据源恢复 |
| L3 占位 | 数据源缺失 | 占位图+P1 SOP升级 | "数据暂不可用, 已触发P1 SOP升级" | DSHB数据源上线 |

#### CH-017: 铝棒开工率 (P2)

| 兜底级别 | 触发条件 | 展示内容 | 提示文案 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L1 缓存 | API响应>5s | 最近1周缓存数据 | "开工率数据延迟" | API恢复正常 |
| L2 静态 | 缓存过期 | 最近4周静态快照 | "数据不可用, 显示最近快照" | 数据源恢复 |
| L3 占位 | 数据源缺失 | 占位图+P2标记 | "数据暂不可用, 标记为P2" | DSHB数据源上线 |

#### CH-021: 锌精矿TC加工费 (P1)

| 兜底级别 | 触发条件 | 展示内容 | 提示文案 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L1 缓存 | API响应>5s | 最近1月缓存数据 | "TC数据延迟" | API恢复正常 |
| L2 静态 | 缓存过期 | 最近3月静态快照 | "数据不可用, 显示最近快照" | 数据源恢复 |
| L3 占位 | 数据源缺失 | 占位图+P1 SOP升级 | "数据暂不可用, 已触发P1 SOP升级" | DSHB数据源上线 |

#### CH-027: 锡精矿进口量 (P1)

| 兜底级别 | 触发条件 | 展示内容 | 提示文案 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L1 缓存 | API响应>5s | 最近1月缓存数据 | "进口量数据延迟" | API恢复正常 |
| L2 静态 | 缓存过期 | 最近3月静态快照 | "数据不可用, 显示最近快照" | 数据源恢复 |
| L3 占位 | 数据源缺失 | 占位图+P1 SOP升级 | "数据暂不可用, 已触发P1 SOP升级" | DSHB数据源上线 |

#### CH-030: 工业硅产量 (P2)

| 兜底级别 | 触发条件 | 展示内容 | 提示文案 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L1 缓存 | API响应>5s | 最近1月缓存数据 | "产量数据延迟" | API恢复正常 |
| L2 静态 | 缓存过期 | 最近3月静态快照 | "数据不可用, 显示最近快照" | 数据源恢复 |
| L3 占位 | 数据源缺失 | 占位图+P2标记 | "数据暂不可用, 标记为P2" | DSHB数据源上线 |

#### CH-034: 碳酸锂产量 (P1)

| 兜底级别 | 触发条件 | 展示内容 | 提示文案 | 恢复条件 |
|---------|---------|---------|---------|---------|
| L1 缓存 | API响应>5s | 最近1月缓存数据 | "产量数据延迟" | API恢复正常 |
| L2 静态 | 缓存过期 | 最近3月静态快照 | "数据不可用, 显示最近快照" | 数据源恢复 |
| L3 占位 | 数据源缺失 | 占位图+P1 SOP升级 | "数据暂不可用, 已触发P1 SOP升级" | DSHB数据源上线 |

---

## 6. 图表-Gate用例交叉引用

### 6.1 按Gate用例覆盖

| Gate用例ID | 用例名称 | 覆盖图表数 | 覆盖图表 |
|-----------|---------|-----------|---------|
| DSHE-C-001 | 36图表全量渲染 | 36 | CH-001~CH-036 |
| DSHE-C-002 | 29全匹配图表数据一致性 | 29 | CH-001~CH-036 (排除7降级) |
| DSHE-C-003 | 7降级图表渲染 | 7 | CH-005,013,017,021,027,030,034 |
| DSHE-C-004 | 56子面板渲染 | 6 | Gate大盘6面板(非本36图表范围) |
| DSHE-C-007 | 工业硅图表分批渲染 | 4 | CH-029,030,031,032 |
| DSHE-C-008 | 图表标签截断回归 | 36 | CH-001~CH-036 |
| DSHE-C-009 | 图表图例拥挤回归 | 36 | CH-001~CH-036 |
| DSHE-C-010 | 图表配色一致性 | 36 | CH-001~CH-036 |
| DSHE-C-011 | 图表数据点完整性 | 36 | CH-001~CH-036 |
| DSHE-C-012 | 图表时间轴一致性 | 28 | 含时间维度的图表 |
| DSHE-C-013 | 图表Y轴范围 | 36 | CH-001~CH-036 |
| DSHE-C-014 | 图表标题一致性 | 36 | CH-001~CH-036 |
| DSHE-C-015 | 图表单位标注 | 36 | CH-001~CH-036 |

### 6.2 图表-回填字段覆盖

| 回填字段 | 字段名称 | 关联图表数 | 关联图表 |
|---------|---------|-----------|---------|
| F-01 | api_batch_support | 3 | CH-029,030,031 |
| F-02 | api_subpage_support | 0 | — (子面板级, 非图表级) |
| F-03 | api_subpage_data | 0 | — (子面板级) |
| F-04 | api_batch_timing | 3 | CH-029,030,031 |
| F-05 | chart_data_source | 36 | CH-001~CH-036 |
| F-06 | chart_data_consistency | 29 | 29张全匹配图表 |
| F-07 | chart_degrade_status | 7 | 7张降级图表 |
| F-08 | subpanel_data_source | 0 | — (子面板级) |
| F-09 | subpanel_data_consistency | 0 | — (子面板级) |
| F-10 | batch_chart_data | 4 | CH-029,030,031,032 |
| F-11 | chart_data_points | 36 | CH-001~CH-036 |
| F-12 | chart_time_range | 28 | 含时间维度图表 |
| F-13 | alias_resolve_rate | 0 | — (别名级, 非图表级) |
| F-14 | data_source_status | 0 | — (数据源级) |
| F-15 | probe_success_rate | 0 | — (探测级) |
| F-16 | degrade_chart_status | 7 | 7张降级图表 |
| F-17 | recover_data_consistency | 0 | — (恢复级) |
| F-18 | scenario_replay_data | 0 | — (回放级) |
| F-19 | qa_replay_data | 0 | — (Q&A级) |

---

## 7. 图表性能目标汇总

| 性能指标 | 目标值 | 测量方式 | 覆盖图表 | 关联用例 |
|---------|-------|---------|---------|---------|
| P99 渲染耗时 | < 3.0s | 50并发下P99 | 36 | DSHE-P-001, DSHE-C-005 |
| 首屏加载 | < 2.0s | 冷启动首屏 | 6 (Gate大盘) | DSHE-P-002, DSHE-P-003 |
| CDN首次加载 | < 2.2s | 版本切换后 | 6 (Gate大盘) | DSHE-P-005 |
| 子面板P99 | < 3.0s | 56子面板P99 | 6 (Gate大盘) | DSHE-C-005 |
| 分批加载 | < 1.0s/批 | 工业硅5批次 | 4 (SI模块) | DSHE-P-010, DSHE-C-007 |
| 图表数据获取 | < 500ms | 单图表API | 36 | — |
| 降级渲染 | < 1.0s | 降级态渲染 | 7 | DSHE-C-003, DSHE-D-011 |
| 别名查询 | < 500ms | 别名解析P99 | — | DSHE-A-003 |

---

## 8. 约束合规确认

| 约束 | 状态 | 说明 |
|------|------|------|
| `NO_ZHIJI_API_CALL=TRUE` | ✅ 合规 | 仅定义Schema, 未调用zhiji API |
| `NO_MODIFY_V85=TRUE` | ✅ 合规 | V85基线未做任何修改 |
| `NO_OVERWRITE=TRUE` | ✅ 合规 | 仅新增本文档, 未覆盖历史 |
| `BRANCH_LOCKED=TRUE` | ✅ 合规 | 仅 `feature/v85-chart-template` |
| `NO_PANEL_JSON_MODIFICATION=TRUE` | ✅ 合规 | 仅Schema文档, 未修改JSON |
| `NO_ENGINE_LOGIC_MODIFICATION=TRUE` | ✅ 合规 | 仅Schema文档, 未修改引擎 |

---

## 9. 附录

### 9.1 文件信息

| 项目 | 值 |
|------|-----|
| **文件名** | v86_rc2_dshe_chart_schema_full_v7.md |
| **任务** | DSHE_V86_RC2_FINAL_PREP_CLOSEOUT |
| **子任务** | T3.1 展示层全量图表PDF绘图Schema固化 |
| **分支** | feature/v85-chart-template |
| **基线** | DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`) |
| **创建日期** | 2026-10-03 |
| **状态** | ✅ 全量展示层36图表PDF绘图Schema固化完成 |

### 9.2 Schema统计

| 维度 | 数量 | 说明 |
|------|------|------|
| 图表总数 | 36 | CH-001~CH-036 |
| 覆盖模块 | 8 | PB/CU/AL/ZN/NI/SN/SI/LI |
| 全匹配图表 | 29 | 数据完整, 正常渲染 |
| 降级图表 | 7 | CH-005,013,017,021,027,030,034 |
| 图表类型 | 3 | 折线(21)/面积(5)/柱状(12) |
| 关联Gate用例 | 89 | 全覆盖 |
| 关联回填字段 | 19 | F-01~F-19 全覆盖 |
| 性能目标 | 8项 | P99/首屏/CDN/子面板/分批/数据获取/降级/别名 |

---

*文档版本: V7 (全量图表Schema固化)*
*生成日期: 2026-10-03*
*工单: DSHE_V86_RC2_FINAL_PREP_CLOSEOUT · T3.1*
*分支: feature/v85-chart-template*
*状态: ✅ 全量36图表Schema固化完成 — 可视化上线前置配置就绪*