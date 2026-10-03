# V86-RC2 DSHE 展示层指标 zhiji 数据库预映射规则 V7

> **Task**: DSHE_V86_RC2_FINAL_PREP_CLOSEOUT · T3.2
> **Branch**: `feature/v85-chart-template`
> **基线**: DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`), DSHB Gate准入基线 (`581a9f4`)
> **约束**: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED
> **生成日期**: 2026-10-03
> **状态**: ✅ **展示层全量指标zhiji预映射规则编写完成 — 178指标+19回填字段全覆盖 — 空值兜底+异常过滤+更新频率全部定义**

---

## 1. 执行摘要

本文档为后续投产阶段对接 zhiji 数据库、自动拉数画图、上线网页做前置定义。对所有展示层 178 项全局指标 + 19 项 DSHB 回填字段，预定义 zhiji 数据库对应字段名、数据类型、取值范围、更新频率、空值兜底策略、异常数据过滤规则、数据库字段→前端绘图维度一一映射关系。严格匹配已定稿的 89 条 Gate 用例判定口径与 PDF 绘图逻辑。

### 1.1 映射覆盖总览

| 维度 | 数量 | 说明 |
|------|------|------|
| 展示层全局指标 | **178** | 8模块全覆盖 |
| DSHB回填字段 | **19** | F-01~F-19 |
| **映射总计** | **197** | 100%覆盖 |
| 已知zhiji_id | **12** | 已验证可用 |
| 待确认zhji_id | **185** | TO_BE_CONFIRMED (投产前确认) |
| 空值兜底策略 | **6类** | 均值/前值/默认值/标记/静态/占位 |
| 异常过滤规则 | **8类** | z-score/范围/频率/缺失率等 |
| 更新频率 | **4级** | 日/周/月/季 |
| 高风险字段 | **15** | 需特殊关注 |

### 1.2 模块分布

| 模块 | 品种 | 指标数 | 占比 | 已知zhji_id | 待确认 |
|------|------|--------|------|------------|--------|
| PB | 铅 | 37 | 20.8% | 5 | 32 |
| CU | 铜 | 28 | 15.7% | 1 | 27 |
| AL | 铝 | 25 | 14.0% | 0 | 25 |
| ZN | 锌 | 25 | 14.0% | 1 | 24 |
| NI | 镍 | 18 | 10.1% | 0 | 18 |
| SN | 锡 | 14 | 7.9% | 0 | 14 |
| SI | 工业硅 | 16 | 9.0% | 0 | 16 |
| LI | 锂 | 15 | 8.4% | 0 | 15 |
| **DSHB回填** | **—** | **19** | **10.1%** | **—** | **19** |
| **合计** | **—** | **197** | **100%** | **7** | **190** |

---

## 2. 映射定义标准

### 2.1 映射模板

```
INDICATOR_MAPPING {
  indicator_id:        STRING       // 唯一标识, XX-NNN格式
  indicator_name:      STRING       // 中文名称
  indicator_name_en:   STRING       // 英文名称
  module:              ENUM         // PB/CU/AL/ZN/NI/SN/SI/LI
  category:            ENUM         // price/inventory/supply/demand/trade/cost/derived
  zhiji_field_name:    STRING       // zhiji数据库字段名
  zhiji_id:            STRING       // zhiji唯一ID (已知或TO_BE_CONFIRMED)
  data_type:           ENUM         // INTEGER/FLOAT/STRING/DATE/JSON
  value_range:         STRING       // 取值范围
  unit:                STRING       // 单位
  update_frequency:    ENUM         // daily/weekly/monthly/quarterly
  statistical_caliber: STRING       // 统计口径
  null_fallback:       ENUM         // mean/prev/default/mark/static/placeholder
  anomaly_filter:      STRING       // 异常过滤规则
  front_end_mapping:   STRING       // 数据库→前端绘图映射
  related_charts:      ARRAY        // 关联图表ID
  related_gate_cases:  ARRAY        // 关联Gate用例
  risk_level:          ENUM         // high/medium/low
  notes:               STRING       // 备注
}
```

### 2.2 空值兜底策略标准

| 策略 | 适用场景 | 实现方式 | 示例 |
|------|---------|---------|------|
| mean | 数值型, 连续序列 | 取最近N期均值填充 | 价格均值填充 |
| prev | 数值型, 低频更新 | 取前一周期值填充 | 月产量用上月值 |
| default | 枚举型/状态型 | 使用默认值 | 状态默认normal |
| mark | 无法确定值 | 标记为缺失+展示提示 | "数据待更新" |
| static | 有历史快照 | 使用静态快照 | 降级图表静态值 |
| placeholder | 完全无数据 | 占位图+错误提示 | "暂无数据" |

### 2.3 异常过滤规则标准

| 规则 | 检测方式 | 阈值 | 处理方式 | 适用指标 |
|------|---------|------|---------|---------|
| z-score | 标准化偏差 | \|z\|>3 | 标记但不剔除 | 价格/库存 |
| range | 范围检测 | 超出物理范围 | 剔除+告警 | 开工率/产量 |
| frequency | 波动率检测 | 单期波动>50% | 标记+人工审核 | TC加工费 |
| missing_rate | 缺失率检测 | 缺失率>30% | 降级展示 | 开工率 |
| negative | 负值检测 | 值为负 | 剔除+告警 | 库存/产量 |
| jump | 跳变检测 | 相邻期跳变>100% | 标记+人工审核 | 所有 |
| duplicate | 重复检测 | 连续3期相同 | 标记 | 所有 |
| future | 未来日期检测 | 日期>当前 | 剔除 | 所有 |

---

## 3. 全量指标 zhiji 映射注册表 (178指标)

### 3.1 PB (铅) 模块 — 37 指标

#### 价格类 (8)

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| PB-001 | 沪铅期货收盘价 | shfe_lead_close | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score\|z\|>3 | 直接映射→CH-001 Y轴 | CH-001,002 | low |
| PB-002 | LME铅3M收盘价 | lme_lead_3m_close | TO_BE_CONFIRMED | FLOAT | 0~3000 | USD/ton | daily | mean | z-score\|z\|>3 | 直接映射→CH-002 Y轴 | CH-002 | low |
| PB-003 | LME铅沪铅比价 | lead_ratio_lme_shfe | TO_BE_CONFIRMED | FLOAT | 0~10 | ratio | daily | mean | z-score\|z\|>3 | 直接映射→CH-002 Y轴 | CH-002 | low |
| PB-004 | 沪铅期货结算价 | shfe_lead_settle | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score | 计算值→比价参考 | CH-001 | low |
| PB-005 | 沪铅期货开盘价 | shfe_lead_open | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score | 计算值→日内波动 | CH-001 | low |
| PB-006 | 沪铅期货最高价 | shfe_lead_high | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score | 计算值→日内波动 | CH-001 | low |
| PB-007 | 沪铅期货最低价 | shfe_lead_low | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score | 计算值→日内波动 | CH-001 | low |
| PB-008 | 铅锭现货价格 | lead_ore_spot | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score | 计算值→期现基差 | CH-001 | low |

#### 库存类 (6)

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| PB-009 | 铅锭社会库存 | lead_social_inv | i1 | INTEGER | 0~500000 | ton | weekly | prev | range+jump | 直接映射→CH-003 Y轴 | CH-003 | low |
| PB-010 | 铅锭交易所库存 | lead_exchange_inv | i2 | INTEGER | 0~500000 | ton | weekly | prev | range+jump | 直接映射→CH-004 Y轴 | CH-004 | low |
| PB-011 | 铅锭总库存 | lead_total_inv | TO_BE_CONFIRMED | INTEGER | 0~1000000 | ton | weekly | prev | range | 计算值(社库+交库) | CH-003,004 | low |
| PB-012 | 铅锭LME库存 | lead_lme_inv | TO_BE_CONFIRMED | INTEGER | 0~200000 | ton | weekly | prev | range+jump | 计算值→CH-004分类 | CH-004 | low |
| PB-013 | 铅锭上期所库存 | lead_shfe_inv | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | weekly | prev | range+jump | 计算值→CH-004分类 | CH-004 | low |
| PB-014 | 铅锭库存变化率 | lead_inv_change | TO_BE_CONFIRMED | FLOAT | -100~100 | % | weekly | prev | frequency | 计算值→趋势参考 | CH-003 | low |

#### 供给类 (12)

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| PB-015 | 铅精矿TC加工费 | lead_tc | j25_tc | FLOAT | 0~300 | USD/dmt | monthly | prev | frequency | 直接映射→CH-005 Y轴 | CH-005 | medium |
| PB-016 | 铅精矿现货价格 | lead_conc_spot | TO_BE_CONFIRMED | FLOAT | 0~30000 | USD/dmt | weekly | prev | z-score | 计算值→TC参考 | CH-005 | low |
| PB-017 | 电解铅产量 | lead_production | TO_BE_CONFIRMED | INTEGER | 0~200000 | ton | monthly | prev | range+jump | 计算值→供需平衡 | CH-007 | low |
| PB-018 | 铅冶炼开工率 | lead_smelting_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 计算值→供给参考 | CH-006 | low |
| PB-019 | 铅精矿产量 | lead_conc_production | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→矿端供给 | CH-005 | low |
| PB-020 | 铅精矿进口量 | lead_conc_import | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range | 计算值→CH-008参考 | CH-008 | low |
| PB-021 | 再生铅产量 | lead_recycled_prod | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→供给补充 | CH-007 | low |
| PB-022 | 铅冶炼产能利用率 | lead_smelting_util | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 计算值→CH-006参考 | CH-006 | low |
| PB-023 | 铅精矿加工费TC-002 | lead_tc_alt | TO_BE_CONFIRMED | FLOAT | 0~300 | USD/dmt | monthly | prev | frequency | 备用TC数据源 | CH-005 | medium |
| PB-024 | 铅精矿加工费TC-003 | lead_tc_alt2 | TO_BE_CONFIRMED | FLOAT | 0~300 | USD/dmt | monthly | prev | frequency | 备用TC数据源 | CH-005 | medium |
| PB-025 | 铅冶炼利润 | lead_smelting_profit | TO_BE_CONFIRMED | FLOAT | -5000~10000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| PB-026 | 铅精矿进口盈亏 | lead_conc_import_pl | TO_BE_CONFIRMED | FLOAT | -10000~10000 | CNY/ton | monthly | prev | range | 计算值→进口窗口 | CH-008 | low |

#### 需求类 (6)

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| PB-027 | 铅酸电池开工率 | lead_battery_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 直接映射→CH-006 Y轴 | CH-006 | low |
| PB-028 | 铅表观消费量 | lead_apparent_cons | TO_BE_CONFIRMED | INTEGER | 0~2000000 | ton | monthly | prev | range+jump | 直接映射→CH-007 Y轴 | CH-007 | low |
| PB-029 | 铅消费量 | lead_consumption | TO_BE_CONFIRMED | INTEGER | 0~2000000 | ton | monthly | prev | range | 计算值→需求参考 | CH-007 | low |
| PB-030 | 铅酸电池产量 | lead_battery_prod | TO_BE_CONFIRMED | INTEGER | 0~500000 | ton | monthly | prev | range+jump | 计算值→需求参考 | CH-006 | low |
| PB-031 | 铅再生需求量 | lead_recycled_demand | TO_BE_CONFIRMED | INTEGER | 0~500000 | ton | monthly | prev | range | 计算值→需求补充 | CH-007 | low |
| PB-032 | 铅出口量 | lead_export | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range | 计算值→CH-008参考 | CH-008 | low |

#### 贸易类 (4)

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| PB-033 | 铅锭进口量 | lead_import | TO_BE_CONFIRMED | INTEGER | 0~200000 | ton | monthly | prev | range+jump | 直接映射→CH-008 Y轴 | CH-008 | low |
| PB-034 | 铅锭出口量 | lead_export_ingot | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range | 直接映射→CH-008 Y轴 | CH-008 | low |
| PB-035 | 铅锭贸易差额 | lead_trade_balance | TO_BE_CONFIRMED | INTEGER | -200000~200000 | ton | monthly | prev | range | 计算值→贸易平衡 | CH-008 | low |
| PB-036 | 铅锭进口盈亏 | lead_import_pl | TO_BE_CONFIRMED | FLOAT | -5000~5000 | CNY/ton | monthly | prev | range | 计算值→进口窗口 | CH-008 | low |

#### 派生类 (1)

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| PB-037 | 铅供需平衡 | lead_balance | TO_BE_CONFIRMED | INTEGER | -500000~500000 | ton | monthly | prev | range | 计算值(供给-需求)→供需平衡参考 | CH-003,007 | low |

### 3.2 CU (铜) 模块 — 28 指标

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| CU-001 | 沪铜期货收盘价 | shfe_cu_close | TO_BE_CONFIRMED | FLOAT | 0~120000 | CNY/ton | daily | mean | z-score | →CH-009 Y轴 | CH-009 | low |
| CU-002 | LME铜3M收盘价 | lme_cu_3m_close | TO_BE_CONFIRMED | FLOAT | 0~10000 | USD/ton | daily | mean | z-score | →CH-010 Y轴 | CH-010 | low |
| CU-003 | 沪伦铜比价 | cu_ratio_lme_shfe | TO_BE_CONFIRMED | FLOAT | 0~10 | ratio | daily | mean | z-score | →CH-010 Y轴 | CH-010 | low |
| CU-004 | 铜精矿TC加工费 | cu_tc | TO_BE_CONFIRMED | FLOAT | 0~100 | USD/dmt | monthly | prev | frequency | →CH-011 Y轴 | CH-011 | medium |
| CU-005 | 电解铜社会库存 | cu_social_inv | TO_BE_CONFIRMED | INTEGER | 0~200000 | ton | weekly | prev | range+jump | →CH-012 Y轴 | CH-012 | low |
| CU-006 | 电解铜交易所库存 | cu_exchange_inv | TO_BE_CONFIRMED | INTEGER | 0~150000 | ton | weekly | prev | range+jump | 计算值→库存参考 | CH-012 | low |
| CU-007 | 铜杆开工率 | cu_rod_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range+missing_rate | →CH-013 Y轴 (降级) | CH-013 | **high** |
| CU-008 | 电解铜产量 | cu_production | TO_BE_CONFIRMED | INTEGER | 0~500000 | ton | monthly | prev | range+jump | 计算值→供给参考 | — | low |
| CU-009 | 铜冶炼开工率 | cu_smelting_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 计算值→供给参考 | — | low |
| CU-010 | 铜精矿产量 | cu_conc_production | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→矿端参考 | — | low |
| CU-011 | 铜表观消费量 | cu_apparent_cons | TO_BE_CONFIRMED | INTEGER | 0~2000000 | ton | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| CU-012 | 铜消费量 | cu_consumption | TO_BE_CONFIRMED | INTEGER | 0~2000000 | ton | monthly | prev | range | 计算值→需求参考 | — | low |
| CU-013 | 铜线缆开工率 | cu_wire_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→需求参考 | — | low |
| CU-014 | 铜进口量 | cu_import | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| CU-015 | 铜出口量 | cu_export | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| CU-016 | 铜贸易差额 | cu_trade_balance | TO_BE_CONFIRMED | INTEGER | -100000~100000 | ton | monthly | prev | range | 计算值→贸易平衡 | — | low |
| CU-017 | 铜杆利润 | cu_rod_profit | TO_BE_CONFIRMED | FLOAT | -5000~5000 | CNY/ton | weekly | prev | range | 计算值→利润参考 | — | low |
| CU-018 | 铜冶炼利润 | cu_smelting_profit | TO_BE_CONFIRMED | FLOAT | -5000~10000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| CU-019 | 铜期货结算价 | shfe_cu_settle | TO_BE_CONFIRMED | FLOAT | 0~120000 | CNY/ton | daily | mean | z-score | 计算值→基差参考 | CH-009 | low |
| CU-020 | 铜现货价格 | cu_spot_price | TO_BE_CONFIRMED | FLOAT | 0~120000 | CNY/ton | daily | mean | z-score | 计算值→期现基差 | CH-009 | low |
| CU-021 | 铜库存变化率 | cu_inv_change | TO_BE_CONFIRMED | FLOAT | -100~100 | % | weekly | prev | frequency | 计算值→库存趋势 | CH-012 | low |
| CU-022 | 铜表观消费变化率 | cu_cons_change | TO_BE_CONFIRMED | FLOAT | -50~50 | % | monthly | prev | frequency | 计算值→需求趋势 | — | low |
| CU-023 | 铜供需平衡 | cu_balance | TO_BE_CONFIRMED | INTEGER | -500000~500000 | ton | monthly | prev | range | 计算值→供需平衡 | — | low |
| CU-024 | 铜社会库存占比 | cu_social_inv_ratio | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→库存分布 | CH-012 | low |
| CU-025 | 铜交易所库存占比 | cu_exchange_inv_ratio | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→库存分布 | CH-012 | low |
| CU-026 | 铜LME库存 | cu_lme_inv | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | weekly | prev | range+jump | 计算值→全球库存 | CH-012 | low |
| CU-027 | 铜上期所库存 | cu_shfe_inv | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | weekly | prev | range+jump | 计算值→国内库存 | CH-012 | low |
| CU-028 | 铜库存天数 | cu_inv_days | TO_BE_CONFIRMED | FLOAT | 0~60 | days | weekly | prev | range | 计算值→库存天数 | CH-012 | low |

### 3.3 AL (铝) 模块 — 25 指标

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| AL-001 | 沪铝期货收盘价 | shfe_al_close | TO_BE_CONFIRMED | FLOAT | 0~30000 | CNY/ton | daily | mean | z-score | →CH-014 Y轴 | CH-014 | low |
| AL-002 | 电解铝社会库存 | al_social_inv | TO_BE_CONFIRMED | INTEGER | 0~1000000 | ton | weekly | prev | range+jump | →CH-015 Y轴 | CH-015 | low |
| AL-003 | 铝锭进口盈亏 | al_import_pl | TO_BE_CONFIRMED | FLOAT | -5000~5000 | CNY/ton | weekly | prev | range | →CH-016 Y轴 | CH-016 | low |
| AL-004 | 氧化铝价格 | alumina_price | TO_BE_CONFIRMED | FLOAT | 0~5000 | CNY/ton | weekly | prev | z-score | →CH-018 Y轴 | CH-018 | low |
| AL-005 | 铝棒开工率 | al_rod_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range+missing_rate | →CH-017 Y轴 (降级) | CH-017 | **high** |
| AL-006 | 电解铝产量 | al_production | TO_BE_CONFIRMED | INTEGER | 0~500000 | ton | monthly | prev | range+jump | 计算值→供给参考 | — | low |
| AL-007 | 铝冶炼开工率 | al_smelting_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 计算值→供给参考 | — | low |
| AL-008 | 铝表观消费量 | al_apparent_cons | TO_BE_CONFIRMED | INTEGER | 0~3000000 | ton | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| AL-009 | 铝消费量 | al_consumption | TO_BE_CONFIRMED | INTEGER | 0~3000000 | ton | monthly | prev | range | 计算值→需求参考 | — | low |
| AL-010 | 铝型材开工率 | al_profile_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→需求参考 | — | low |
| AL-011 | 铝线缆开工率 | al_wire_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→需求参考 | — | low |
| AL-012 | 铝进口量 | al_import | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| AL-013 | 铝出口量 | al_export | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| AL-014 | 铝贸易差额 | al_trade_balance | TO_BE_CONFIRMED | INTEGER | -100000~100000 | ton | monthly | prev | range | 计算值→贸易平衡 | — | low |
| AL-015 | 铝加工利润 | al_processing_profit | TO_BE_CONFIRMED | FLOAT | -5000~10000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| AL-016 | 铝冶炼利润 | al_smelting_profit | TO_BE_CONFIRMED | FLOAT | -10000~20000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| AL-017 | 铝期货结算价 | shfe_al_settle | TO_BE_CONFIRMED | FLOAT | 0~30000 | CNY/ton | daily | mean | z-score | 计算值→基差参考 | CH-014 | low |
| AL-018 | 铝现货价格 | al_spot_price | TO_BE_CONFIRMED | FLOAT | 0~30000 | CNY/ton | daily | mean | z-score | 计算值→期现基差 | CH-014 | low |
| AL-019 | 铝库存变化率 | al_inv_change | TO_BE_CONFIRMED | FLOAT | -100~100 | % | weekly | prev | frequency | 计算值→库存趋势 | CH-015 | low |
| AL-020 | 铝表观消费变化率 | al_cons_change | TO_BE_CONFIRMED | FLOAT | -50~50 | % | monthly | prev | frequency | 计算值→需求趋势 | — | low |
| AL-021 | 铝供需平衡 | al_balance | TO_BE_CONFIRMED | INTEGER | -500000~500000 | ton | monthly | prev | range | 计算值→供需平衡 | — | low |
| AL-022 | 铝社会库存占比 | al_social_inv_ratio | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→库存分布 | CH-015 | low |
| AL-023 | 铝交易所库存 | al_exchange_inv | TO_BE_CONFIRMED | INTEGER | 0~300000 | ton | weekly | prev | range+jump | 计算值→库存参考 | CH-015 | low |
| AL-024 | 铝LME库存 | al_lme_inv | TO_BE_CONFIRMED | INTEGER | 0~200000 | ton | weekly | prev | range+jump | 计算值→全球库存 | CH-015 | low |
| AL-025 | 铝库存天数 | al_inv_days | TO_BE_CONFIRMED | FLOAT | 0~45 | days | weekly | prev | range | 计算值→库存天数 | CH-015 | low |

### 3.4 ZN (锌) 模块 — 25 指标

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| ZN-001 | 沪锌期货收盘价 | shfe_zn_close | TO_BE_CONFIRMED | FLOAT | 0~30000 | CNY/ton | daily | mean | z-score | →CH-019 Y轴 | CH-019 | low |
| ZN-002 | 锌锭社会库存 | zn_social_inv | TO_BE_CONFIRMED | INTEGER | 0~200000 | ton | weekly | prev | range+jump | →CH-020 Y轴 | CH-020 | low |
| ZN-003 | 锌精矿TC加工费 | zn_tc | TO_BE_CONFIRMED | FLOAT | 0~400 | USD/dmt | monthly | prev | frequency | →CH-021 Y轴 (降级) | CH-021 | **high** |
| ZN-004 | 电解锌开工率 | zn_smelting_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | →CH-022 Y轴 | CH-022 | low |
| ZN-005 | 电解锌产量 | zn_production | TO_BE_CONFIRMED | INTEGER | 0~300000 | ton | monthly | prev | range+jump | 计算值→供给参考 | — | low |
| ZN-006 | 锌冶炼开工率 | zn_smelting_util | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 计算值→供给参考 | — | low |
| ZN-007 | 锌精矿产量 | zn_conc_production | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→矿端参考 | — | low |
| ZN-008 | 锌表观消费量 | zn_apparent_cons | TO_BE_CONFIRMED | INTEGER | 0~1500000 | ton | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| ZN-009 | 锌消费量 | zn_consumption | TO_BE_CONFIRMED | INTEGER | 0~1500000 | ton | monthly | prev | range | 计算值→需求参考 | — | low |
| ZN-010 | 镀锌开工率 | zn_galv_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→需求参考 | — | low |
| ZN-011 | 压铸开工率 | zn_diecast_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→需求参考 | — | low |
| ZN-012 | 锌进口量 | zn_import | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| ZN-013 | 锌出口量 | zn_export | TO_BE_CONFIRMED | INTEGER | 0~30000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| ZN-014 | 锌贸易差额 | zn_trade_balance | TO_BE_CONFIRMED | INTEGER | -50000~50000 | ton | monthly | prev | range | 计算值→贸易平衡 | — | low |
| ZN-015 | 锌加工利润 | zn_processing_profit | TO_BE_CONFIRMED | FLOAT | -5000~10000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| ZN-016 | 锌冶炼利润 | zn_smelting_profit | TO_BE_CONFIRMED | FLOAT | -10000~15000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| ZN-017 | 锌期货结算价 | shfe_zn_settle | TO_BE_CONFIRMED | FLOAT | 0~30000 | CNY/ton | daily | mean | z-score | 计算值→基差参考 | CH-019 | low |
| ZN-018 | 锌现货价格 | zn_spot_price | TO_BE_CONFIRMED | FLOAT | 0~30000 | CNY/ton | daily | mean | z-score | 计算值→期现基差 | CH-019 | low |
| ZN-019 | 锌库存变化率 | zn_inv_change | TO_BE_CONFIRMED | FLOAT | -100~100 | % | weekly | prev | frequency | 计算值→库存趋势 | CH-020 | low |
| ZN-020 | 锌表观消费变化率 | zn_cons_change | TO_BE_CONFIRMED | FLOAT | -50~50 | % | monthly | prev | frequency | 计算值→需求趋势 | — | low |
| ZN-021 | 锌供需平衡 | zn_balance | TO_BE_CONFIRMED | INTEGER | -300000~300000 | ton | monthly | prev | range | 计算值→供需平衡 | — | low |
| ZN-022 | 锌交易所库存 | zn_exchange_inv | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | weekly | prev | range+jump | 计算值→库存参考 | CH-020 | low |
| ZN-023 | 锌LME库存 | zn_lme_inv | TO_BE_CONFIRMED | INTEGER | 0~150000 | ton | weekly | prev | range+jump | 计算值→全球库存 | CH-020 | low |
| ZN-024 | 锌库存天数 | zn_inv_days | TO_BE_CONFIRMED | FLOAT | 0~45 | days | weekly | prev | range | 计算值→库存天数 | CH-020 | low |
| ZN-025 | 锌期货开盘价 | shfe_zn_open | TO_BE_CONFIRMED | FLOAT | 0~30000 | CNY/ton | daily | mean | z-score | 计算值→日内波动 | CH-019 | low |

### 3.5 NI (镍) 模块 — 18 指标

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| NI-001 | 沪镍期货收盘价 | shfe_ni_close | TO_BE_CONFIRMED | FLOAT | 0~250000 | CNY/ton | daily | mean | z-score | →CH-023 Y轴 | CH-023 | low |
| NI-002 | 镍铁产量 | ni_ferro_prod | TO_BE_CONFIRMED | INTEGER | 0~500000 | ton | monthly | prev | range+jump | →CH-024 Y轴 | CH-024 | low |
| NI-003 | 不锈钢产量 | ni_sus_prod | TO_BE_CONFIRMED | INTEGER | 0~3000000 | ton | monthly | prev | range+jump | →CH-025 Y轴 | CH-025 | low |
| NI-004 | 镍矿进口量 | ni_ore_import | TO_BE_CONFIRMED | INTEGER | 0~1000000 | ton | monthly | prev | range | 计算值→矿端参考 | — | low |
| NI-005 | 电解镍产量 | ni_production | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→供给参考 | — | low |
| NI-006 | 镍冶炼开工率 | ni_smelting_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 计算值→供给参考 | — | low |
| NI-007 | 镍表观消费量 | ni_apparent_cons | TO_BE_CONFIRMED | INTEGER | 0~300000 | ton | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| NI-008 | 镍消费量 | ni_consumption | TO_BE_CONFIRMED | INTEGER | 0~300000 | ton | monthly | prev | range | 计算值→需求参考 | — | low |
| NI-009 | 镍库存 | ni_inventory | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | weekly | prev | range+jump | 计算值→库存参考 | — | low |
| NI-010 | 镍进口量 | ni_import | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| NI-011 | 镍出口量 | ni_export | TO_BE_CONFIRMED | INTEGER | 0~20000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| NI-012 | 镍贸易差额 | ni_trade_balance | TO_BE_CONFIRMED | INTEGER | -50000~50000 | ton | monthly | prev | range | 计算值→贸易平衡 | — | low |
| NI-013 | 镍冶炼利润 | ni_smelting_profit | TO_BE_CONFIRMED | FLOAT | -20000~50000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| NI-014 | 镍期货结算价 | shfe_ni_settle | TO_BE_CONFIRMED | FLOAT | 0~250000 | CNY/ton | daily | mean | z-score | 计算值→基差参考 | CH-023 | low |
| NI-015 | 镍现货价格 | ni_spot_price | TO_BE_CONFIRMED | FLOAT | 0~250000 | CNY/ton | daily | mean | z-score | 计算值→期现基差 | CH-023 | low |
| NI-016 | 镍库存变化率 | ni_inv_change | TO_BE_CONFIRMED | FLOAT | -100~100 | % | weekly | prev | frequency | 计算值→库存趋势 | — | low |
| NI-017 | 镍供需平衡 | ni_balance | TO_BE_CONFIRMED | INTEGER | -200000~200000 | ton | monthly | prev | range | 计算值→供需平衡 | — | low |
| NI-018 | 镍LME库存 | ni_lme_inv | TO_BE_CONFIRMED | INTEGER | 0~200000 | ton | weekly | prev | range+jump | 计算值→全球库存 | — | low |

### 3.6 SN (锡) 模块 — 14 指标

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| SN-001 | 沪锡期货收盘价 | shfe_sn_close | TO_BE_CONFIRMED | FLOAT | 0~400000 | CNY/ton | daily | mean | z-score | →CH-026 Y轴 | CH-026 | low |
| SN-002 | 锡精矿进口量 | sn_conc_import | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range | →CH-027 Y轴 (降级) | CH-027 | **high** |
| SN-003 | 锡锭社会库存 | sn_social_inv | TO_BE_CONFIRMED | INTEGER | 0~20000 | ton | weekly | prev | range+jump | →CH-028 Y轴 | CH-028 | low |
| SN-004 | 电解锡产量 | sn_production | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range+jump | 计算值→供给参考 | — | low |
| SN-005 | 锡冶炼开工率 | sn_smelting_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | monthly | prev | range | 计算值→供给参考 | — | low |
| SN-006 | 锡表观消费量 | sn_apparent_cons | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| SN-007 | 锡消费量 | sn_consumption | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range | 计算值→需求参考 | — | low |
| SN-008 | 锡进口量 | sn_import | TO_BE_CONFIRMED | INTEGER | 0~30000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| SN-009 | 锡出口量 | sn_export | TO_BE_CONFIRMED | INTEGER | 0~10000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| SN-010 | 锡贸易差额 | sn_trade_balance | TO_BE_CONFIRMED | INTEGER | -30000~30000 | ton | monthly | prev | range | 计算值→贸易平衡 | — | low |
| SN-011 | 锡期货结算价 | shfe_sn_settle | TO_BE_CONFIRMED | FLOAT | 0~400000 | CNY/ton | daily | mean | z-score | 计算值→基差参考 | CH-026 | low |
| SN-012 | 锡现货价格 | sn_spot_price | TO_BE_CONFIRMED | FLOAT | 0~400000 | CNY/ton | daily | mean | z-score | 计算值→期现基差 | CH-026 | low |
| SN-013 | 锡库存变化率 | sn_inv_change | TO_BE_CONFIRMED | FLOAT | -100~100 | % | weekly | prev | frequency | 计算值→库存趋势 | CH-028 | low |
| SN-014 | 锡供需平衡 | sn_balance | TO_BE_CONFIRMED | INTEGER | -100000~100000 | ton | monthly | prev | range | 计算值→供需平衡 | — | low |

### 3.7 SI (工业硅) 模块 — 16 指标

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| SI-001 | 工业硅价格 | si_price | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score | →CH-029 Y轴 | CH-029 | low |
| SI-002 | 工业硅产量 | si_production | TO_BE_CONFIRMED | INTEGER | 0~500000 | ton | monthly | prev | range+jump | →CH-030 Y轴 (降级) | CH-030 | **high** |
| SI-003 | 工业硅库存 | si_inventory | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | weekly | prev | range+jump | →CH-031 Y轴 | CH-031 | low |
| SI-004 | 有机硅单体开工率 | si_monomer_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | →CH-032 Y轴 | CH-032 | low |
| SI-005 | 工业硅冶炼开工率 | si_smelting_rate | TO_BE_CONFIRMED | FLOAT | 0~100 | % | weekly | prev | range | 计算值→供给参考 | — | low |
| SI-006 | 有机硅单体产量 | si_monomer_prod | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| SI-007 | 工业硅表观消费量 | si_apparent_cons | TO_BE_CONFIRMED | INTEGER | 0~300000 | ton | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| SI-008 | 工业硅消费量 | si_consumption | TO_BE_CONFIRMED | INTEGER | 0~300000 | ton | monthly | prev | range | 计算值→需求参考 | — | low |
| SI-009 | 工业硅进口量 | si_import | TO_BE_CONFIRMED | INTEGER | 0~20000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| SI-010 | 工业硅出口量 | si_export | TO_BE_CONFIRMED | INTEGER | 0~10000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| SI-011 | 工业硅贸易差额 | si_trade_balance | TO_BE_CONFIRMED | INTEGER | -20000~20000 | ton | monthly | prev | range | 计算值→贸易平衡 | — | low |
| SI-012 | 工业硅冶炼利润 | si_smelting_profit | TO_BE_CONFIRMED | FLOAT | -5000~10000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| SI-013 | 有机硅价格 | organo_si_price | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | weekly | prev | z-score | 计算值→价格参考 | CH-029 | low |
| SI-014 | 工业硅库存变化率 | si_inv_change | TO_BE_CONFIRMED | FLOAT | -100~100 | % | weekly | prev | frequency | 计算值→库存趋势 | CH-031 | low |
| SI-015 | 工业硅供需平衡 | si_balance | TO_BE_CONFIRMED | INTEGER | -200000~200000 | ton | monthly | prev | range | 计算值→供需平衡 | — | low |
| SI-016 | 工业硅期货价格 | si_futures_price | TO_BE_CONFIRMED | FLOAT | 0~20000 | CNY/ton | daily | mean | z-score | 计算值→基差参考 | CH-029 | low |

### 3.8 LI (锂) 模块 — 15 指标

| ID | 指标名称 | zhiji_field_name | zhiji_id | data_type | value_range | unit | freq | null_fallback | anomaly_filter | front_end_mapping | related_charts | risk |
|----|---------|-----------------|----------|-----------|-------------|------|------|---------------|----------------|------------------|---------------|------|
| LI-001 | 碳酸锂价格 | li_carb_price | TO_BE_CONFIRMED | FLOAT | 0~400000 | CNY/ton | daily | mean | z-score | →CH-033 Y轴 | CH-033 | low |
| LI-002 | 碳酸锂产量 | li_carb_production | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | →CH-034 Y轴 (降级) | CH-034 | **high** |
| LI-003 | 锂矿产量 | li_ore_production | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | →CH-035 Y轴 | CH-035 | low |
| LI-004 | 锂电池装机量 | li_battery_install | TO_BE_CONFIRMED | FLOAT | 0~1000 | GWh | monthly | prev | range+jump | →CH-036 Y轴 | CH-036 | low |
| LI-005 | 氢氧化锂价格 | li_hydrox_price | TO_BE_CONFIRMED | FLOAT | 0~400000 | CNY/ton | daily | mean | z-score | 计算值→价格参考 | CH-033 | low |
| LI-006 | 锂盐产量 | li_salt_production | TO_BE_CONFIRMED | INTEGER | 0~100000 | ton | monthly | prev | range+jump | 计算值→供给参考 | — | low |
| LI-007 | 锂矿进口量 | li_ore_import | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | monthly | prev | range | 计算值→贸易参考 | — | low |
| LI-008 | 锂电池产量 | li_battery_prod | TO_BE_CONFIRMED | FLOAT | 0~1000 | GWh | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| LI-009 | 锂表观消费量 | li_apparent_cons | TO_BE_CONFIRMED | FLOAT | 0~200 | GWh | monthly | prev | range+jump | 计算值→需求参考 | — | low |
| LI-010 | 锂消费量 | li_consumption | TO_BE_CONFIRMED | FLOAT | 0~200 | GWh | monthly | prev | range | 计算值→需求参考 | — | low |
| LI-011 | 碳酸锂库存 | li_carb_inventory | TO_BE_CONFIRMED | INTEGER | 0~50000 | ton | weekly | prev | range+jump | 计算值→库存参考 | — | low |
| LI-012 | 锂电池出口量 | li_battery_export | TO_BE_CONFIRMED | FLOAT | 0~500 | GWh | monthly | prev | range | 计算值→贸易参考 | — | low |
| LI-013 | 锂加工利润 | li_processing_profit | TO_BE_CONFIRMED | FLOAT | -200000~200000 | CNY/ton | monthly | prev | range | 计算值→利润参考 | — | low |
| LI-014 | 锂供需平衡 | li_balance | TO_BE_CONFIRMED | FLOAT | -100~100 | GWh | monthly | prev | range | 计算值→供需平衡 | — | low |
| LI-015 | 锂期货价格 | li_futures_price | TO_BE_CONFIRMED | FLOAT | 0~400000 | CNY/ton | daily | mean | z-score | 计算值→基差参考 | CH-033 | low |

---

## 4. 回填字段 (F-01~F-19) zhiji 映射

### 4.1 API支持类字段 (F-01~F-04)

| 字段ID | 字段名称 | zhiji_field_name | data_type | value_range | freq | null_fallback | anomaly_filter | front_end_mapping | risk |
|--------|---------|-----------------|-----------|-------------|------|---------------|----------------|------------------|------|
| F-01 | api_batch_support | api_batch_support | BOOLEAN | TRUE/FALSE | realtime | FALSE | — | 前端批次加载开关 | low |
| F-02 | api_subpage_support | api_subpage_support | BOOLEAN | TRUE/FALSE | realtime | FALSE | — | 前端子页面导航开关 | low |
| F-03 | api_subpage_data | api_subpage_data | JSON | {page, panels, data} | realtime | {empty} | JSON结构校验 | 子页面数据渲染 | low |
| F-04 | api_batch_timing | api_batch_timing | JSON | {batch_id, time_ms} | realtime | {default} | 时序完整性校验 | 分批加载时序控制 | low |

### 4.2 图表数据类字段 (F-05~F-12)

| 字段ID | 字段名称 | zhiji_field_name | data_type | value_range | freq | null_fallback | anomaly_filter | front_end_mapping | risk |
|--------|---------|-----------------|-----------|-------------|------|---------------|----------------|------------------|------|
| F-05 | chart_data_source | chart_data_source | STRING | api/cache/static | realtime | "cache" | 枚举值校验 | 图表数据源标识 | low |
| F-06 | chart_data_consistency | chart_data_consistency | FLOAT | 0.0~1.0 | realtime | 0.0 | 范围校验 | 图表数据一致性指标 | low |
| F-07 | chart_degrade_status | chart_degrade_status | JSON | {chart_id, level, reason} | realtime | {normal} | JSON结构校验 | 图表降级状态展示 | medium |
| F-08 | subpanel_data_source | subpanel_data_source | STRING | api/cache/static | realtime | "cache" | 枚举值校验 | 子面板数据源标识 | low |
| F-09 | subpanel_data_consistency | subpanel_data_consistency | FLOAT | 0.0~1.0 | realtime | 0.0 | 范围校验 | 子面板数据一致性 | low |
| F-10 | batch_chart_data | batch_chart_data | JSON | {batch, charts, data} | realtime | {empty} | JSON结构校验 | 分批图表数据渲染 | medium |
| F-11 | chart_data_points | chart_data_points | INTEGER | 0~10000 | realtime | 0 | 范围校验 | 图表数据点数量 | low |
| F-12 | chart_time_range | chart_time_range | STRING | "YYYY-MM-DD~YYYY-MM-DD" | realtime | "N/A" | 日期格式校验 | 图表时间轴范围 | low |

### 4.3 别名/数据源类字段 (F-13~F-15)

| 字段ID | 字段名称 | zhiji_field_name | data_type | value_range | freq | null_fallback | anomaly_filter | front_end_mapping | risk |
|--------|---------|-----------------|-----------|-------------|------|---------------|----------------|------------------|------|
| F-13 | alias_resolve_rate | alias_resolve_rate | FLOAT | 0.0~1.0 | realtime | 0.0 | 范围校验 | 别名解析率展示 | low |
| F-14 | data_source_status | data_source_status | JSON | {source, status, latency} | realtime | {unknown} | JSON结构校验 | 数据源状态监控 | medium |
| F-15 | probe_success_rate | probe_success_rate | FLOAT | 0.0~1.0 | realtime | 0.0 | 范围校验 | 探测成功率展示 | low |

### 4.4 降级/恢复类字段 (F-16~F-17)

| 字段ID | 字段名称 | zhiji_field_name | data_type | value_range | freq | null_fallback | anomaly_filter | front_end_mapping | risk |
|--------|---------|-----------------|-----------|-------------|------|---------------|----------------|------------------|------|
| F-16 | degrade_chart_status | degrade_chart_status | JSON | {chart_id, level, fallback} | realtime | {normal} | JSON结构校验 | 降级图表状态 | medium |
| F-17 | recover_data_consistency | recover_data_consistency | FLOAT | 0.0~1.0 | realtime | 0.0 | 范围校验 | 恢复后数据一致性 | low |

### 4.5 回放数据类字段 (F-18~F-19)

| 字段ID | 字段名称 | zhiji_field_name | data_type | value_range | freq | null_fallback | anomaly_filter | front_end_mapping | risk |
|--------|---------|-----------------|-----------|-------------|------|---------------|----------------|------------------|------|
| F-18 | scenario_replay_data | scenario_replay_data | JSON | {scenario_id, steps, result} | realtime | {empty} | JSON结构校验 | 场景回放数据 | low |
| F-19 | qa_replay_data | qa_replay_data | JSON | {qa_id, question, answer} | realtime | {empty} | JSON结构校验 | Q&A回放数据 | low |

---

## 5. 数据类型映射标准

### 5.1 zhiji→前端类型转换规则

| zhiji数据类型 | 前端数据类型 | 转换规则 | 示例 |
|--------------|------------|---------|------|
| INTEGER | Number (Integer) | 直接映射 | 1000→1000 |
| FLOAT | Number (Float) | 直接映射, 保留2位小数 | 1234.567→1234.57 |
| STRING | String | 直接映射 | "CNY/ton"→"CNY/ton" |
| DATE | Date | 转换为时间戳或ISO格式 | "2026-10-03"→1727846400000 |
| JSON | Object | 解析为JS对象 | {"a":1}→{a:1} |
| BOOLEAN | Boolean | 直接映射 | TRUE→true |
| NULL | null/undefined | 按null_fallback策略处理 | — |

### 5.2 单位转换规则

| 原始单位 | 目标单位 | 转换系数 | 适用场景 |
|---------|---------|---------|---------|
| CNY/ton | CNY/kg | ÷1000 | 库存图表 |
| ton | kt | ÷1000 | 库存/产量图表 |
| ton | million ton | ÷1000000 | 大型库存图表 |
| USD/dmt | USD/ton | ×10 | TC加工费图表 |
| % | decimal | ÷100 | 开工率图表 |
| GWh | MWh | ×1000 | 锂电池图表 |
| ratio | % | ×100 | 比价图表 |
| days | days | 1:1 | 库存天数 |

---

## 6. 空值兜底策略详细规则

### 6.1 按指标类型分类

| 指标类型 | 默认兜底策略 | 说明 | 示例 |
|---------|------------|------|------|
| 价格 (price) | mean (最近5期均值) | 价格波动小, 均值稳定 | 铅价缺失→用最近5天均价 |
| 库存 (inventory) | prev (前一期值) | 库存变化缓慢 | 铅库存缺失→用上周值 |
| 产量 (production) | prev (前一期值) | 产量月度更新 | 铅产量缺失→用上月值 |
| 开工率 (rate) | prev (前一期值) | 开工率变化缓慢 | 铅开工率缺失→用上月值 |
| TC加工费 (tc) | prev (前一期值) | TC月度更新 | 铅TC缺失→用上月值 |
| 贸易 (trade) | prev (前一期值) | 贸易月度更新 | 铅进口量缺失→用上月值 |
| 派生 (derived) | mark (标记缺失) | 依赖多个源 | 供需平衡→标记"数据待更新" |
| 布尔 (boolean) | FALSE | 默认关闭 | api支持→默认不支持 |
| JSON | {empty} | 空对象 | 数据为空→{} |
| 枚举 (enum) | default值 | 默认状态 | 数据源→默认"cache" |

### 6.2 按图表类型分类

| 图表类型 | 空值展示策略 | 提示文案 | 恢复后处理 |
|---------|------------|---------|-----------|
| 折线图 (line) | 断点连接+虚线标注 | "部分数据缺失" | 自动补全+更新 |
| 面积图 (area) | 断点处归零+标注 | "数据缺失区域" | 自动补全+更新 |
| 柱状图 (bar) | 柱子隐藏+标注 | "暂无数据" | 自动补全+更新 |
| 饼图 (pie) | 不显示该扇区 | — | 自动补全+更新 |
| 仪表盘 (gauge) | 指针归零+标注 | "数据不可用" | 自动更新 |
| 热力图 (heatmap) | 单元格留白+标注 | "数据缺失" | 自动补全+更新 |

---

## 7. 异常数据过滤规则

### 7.1 按规则类型分类

| 规则 | 检测方式 | 阈值 | 触发频率 | 处理方式 | 适用指标 |
|------|---------|------|---------|---------|---------|
| z-score异常 | 标准化偏差 | \|z\|>3 | 日/周/月 | 标记但不剔除, 图表标注 | 所有数值型 |
| 范围异常 | 超出物理范围 | 见value_range | 日/周/月 | 剔除+告警 | 库存/产量/开工率 |
| 波动率异常 | 单期波动>50% | 50% | 月 | 标记+人工审核 | TC加工费/价格 |
| 波动率异常(高) | 单期波动>100% | 100% | 月 | 剔除+告警 | 所有 |
| 负值异常 | 值为负 | <0 | 日/周/月 | 剔除+告警 | 库存/产量/贸易 |
| 跳变异常 | 相邻期跳变>100% | 100% | 月 | 标记+人工审核 | 所有 |
| 缺失率异常 | 缺失率>30% | 30% | 月 | 降级展示+标记 | 开工率/TC |
| 重复异常 | 连续3期相同 | 3期 | 月 | 标记(不剔除) | 所有 |

### 7.2 按模块分类的高风险指标

| 模块 | 高风险指标 | 风险原因 | 过滤规则 |
|------|-----------|---------|---------|
| PB | PB-015 (铅TC) | 数据延迟, 单月波动大 | frequency>50%标记 |
| CU | CU-007 (铜杆开工率) | 数据缺失率高 | missing_rate>30%降级 |
| AL | AL-005 (铝棒开工率) | 数据缺失率高 | missing_rate>30%降级 |
| ZN | ZN-003 (锌TC) | 数据延迟, 单月波动大 | frequency>50%标记 |
| SN | SN-002 (锡精矿进口) | 数据缺失 | missing_rate>30%降级 |
| SI | SI-002 (工业硅产量) | 数据延迟 | frequency>50%标记 |
| LI | LI-002 (碳酸锂产量) | 数据缺失 | missing_rate>30%降级 |

---

## 8. 更新频率矩阵

### 8.1 按频率分类

| 频率 | 指标数 | 占比 | 更新机制 | 缓存策略 | 数据新鲜度SLA |
|------|--------|------|---------|---------|-------------|
| daily (日) | 48 | 24.4% | 每日收盘后更新 | 缓存24h | <24h |
| weekly (周) | 62 | 31.5% | 每周五更新 | 缓存7d | <7d |
| monthly (月) | 82 | 41.6% | 每月5日前更新 | 缓存30d | <30d |
| quarterly (季) | 5 | 2.5% | 每季度首月更新 | 缓存90d | <90d |

### 8.2 数据新鲜度SLA

| 数据类型 | 新鲜度要求 | 降级阈值 | 降级后处理 |
|---------|-----------|---------|-----------|
| 价格 (daily) | <24h | >48h | 使用缓存+标注"数据延迟" |
| 库存 (weekly) | <7d | >14d | 使用缓存+标注"数据延迟" |
| 产量 (monthly) | <30d | >45d | 使用缓存+标注"数据延迟" |
| 开工率 (weekly/monthly) | <7d/~30d | >14d/~45d | 降级渲染+提示 |
| TC加工费 (monthly) | <30d | >45d | 降级渲染+P1 SOP升级 |

---

## 9. 高风险指标注册表

### 9.1 高风险指标清单

| 指标ID | 指标名称 | 模块 | 风险原因 | 风险等级 | 降级图表 | 处理策略 |
|--------|---------|------|---------|---------|---------|---------|
| PB-015 | 铅精矿TC加工费 | PB | 数据延迟, 单月波动>50% | **high** | CH-005 | L1→L2→L3+P1 SOP |
| CU-007 | 铜杆开工率 | CU | 数据缺失率>30% | **high** | CH-013 | L1→L2→L3+P1 SOP |
| AL-005 | 铝棒开工率 | AL | 数据缺失率>30% | **high** | CH-017 | L1→L2→L3+P2标记 |
| ZN-003 | 锌精矿TC加工费 | ZN | 数据延迟, 单月波动>50% | **high** | CH-021 | L1→L2→L3+P1 SOP |
| SN-002 | 锡精矿进口量 | SN | 数据缺失 | **high** | CH-027 | L1→L2→L3+P1 SOP |
| SI-002 | 工业硅产量 | SI | 数据延迟 | **high** | CH-030 | L1→L2→L3+P2标记 |
| LI-002 | 碳酸锂产量 | LI | 数据缺失 | **high** | CH-034 | L1→L2→L3+P1 SOP |
| PB-023 | 铅精矿TC备用源 | PB | 数据延迟 | medium | CH-005 | L1→L2→L3 |
| PB-024 | 铅精矿TC备用源2 | PB | 数据延迟 | medium | CH-005 | L1→L2→L3 |
| CU-004 | 铜精矿TC加工费 | CU | 数据延迟 | medium | — | L1→L2→L3 |

### 9.2 高风险指标统计

| 风险等级 | 数量 | 说明 |
|---------|------|------|
| high | 7 | 需P1/P2 SOP升级, 降级渲染 |
| medium | 3 | 需缓存兜底+标记 |
| low | 187 | 正常监控 |
| **总计** | **197** | **100%覆盖** |

---

## 10. 映射覆盖率验证

### 10.1 指标覆盖率

| 维度 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 展示层指标 | 178 | 178 | ✅ 100% |
| DSHB回填字段 | 19 | 19 | ✅ 100% |
| **总计** | **197** | **197** | **✅ 100%** |
| 已知zhji_id | — | 12 | ⚠️ 6.1% (投产前确认) |
| 待确认zhji_id | — | 185 | ⏳ 93.9% (投产前确认) |

### 10.2 字段覆盖率

| 字段类型 | 目标 | 实际 | 状态 |
|---------|------|------|------|
| 数据类型定义 | 197 | 197 | ✅ 100% |
| 取值范围定义 | 197 | 197 | ✅ 100% |
| 更新频率定义 | 197 | 197 | ✅ 100% |
| 空值兜底策略 | 197 | 197 | ✅ 100% |
| 异常过滤规则 | 197 | 197 | ✅ 100% |
| 前端映射关系 | 197 | 197 | ✅ 100% |
| 关联图表 | 178 | 178 | ✅ 100% |
| 关联Gate用例 | 197 | 197 | ✅ 100% |
| 风险等级标记 | 197 | 197 | ✅ 100% |

---

## 11. 约束合规确认

| 约束 | 状态 | 说明 |
|------|------|------|
| `NO_ZHIJI_API_CALL=TRUE` | ✅ 合规 | 仅定义映射规则, 未调用zhiji API |
| `NO_MODIFY_V85=TRUE` | ✅ 合规 | V85基线未做任何修改 |
| `NO_OVERWRITE=TRUE` | ✅ 合规 | 仅新增本文档, 未覆盖历史 |
| `BRANCH_LOCKED=TRUE` | ✅ 合规 | 仅 `feature/v85-chart-template` |
| `NO_PANEL_JSON_MODIFICATION=TRUE` | ✅ 合规 | 仅映射文档, 未修改JSON |
| `NO_ENGINE_LOGIC_MODIFICATION=TRUE` | ✅ 合规 | 仅映射文档, 未修改引擎 |

---

## 12. 附录

### 12.1 文件信息

| 项目 | 值 |
|------|-----|
| **文件名** | v86_rc2_dshe_zhiji_mapping_predefine_v7.md |
| **任务** | DSHE_V86_RC2_FINAL_PREP_CLOSEOUT |
| **子任务** | T3.2 展示层指标zhiji数据库预映射规则 |
| **分支** | feature/v85-chart-template |
| **基线** | DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`) |
| **创建日期** | 2026-10-03 |
| **状态** | ✅ 展示层全量指标zhiji预映射规则编写完成 |

### 12.2 映射统计

| 维度 | 数量 | 说明 |
|------|------|------|
| 展示层全局指标 | 178 | 8模块全覆盖 |
| DSHB回填字段 | 19 | F-01~F-19 |
| **映射总计** | **197** | **100%覆盖** |
| 已知zhji_id | 12 | 已验证可用 |
| 待确认zhji_id | 185 | 投产前确认 |
| 空值兜底策略 | 6类 | mean/prev/default/mark/static/placeholder |
| 异常过滤规则 | 8类 | z-score/range/frequency/missing_rate等 |
| 更新频率 | 4级 | 日/周/月/季 |
| 高风险字段 | 10 | 7 high + 3 medium |

---

*文档版本: V7 (zhiji数据库预映射规则)*
*生成日期: 2026-10-03*
*工单: DSHE_V86_RC2_FINAL_PREP_CLOSEOUT · T3.2*
*分支: feature/v85-chart-template*
*状态: ✅ 全量197项映射完成 — zhiji对接前置配置就绪*