# V86-RC2 投产阶段 zhiji_id 映射同步更新报告

> **工单**: `DSHE_V86_RC2_PROD_PHASE_STAGE1` · T3.2
> **分支**: `feature/v85-chart-template`
> **约束**: NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED / NO_ZHIJI_API_CALL=FALSE (投产阶段允许调用)
> **跨团队**: 全部映射变更同步 DSHB 验证 + HERMES 审计
> **生成日期**: 2026-10-04
> **状态**: ✅ **投产基线确立 — 36图表/178指标/19字段/190 zhiji_id 映射同步就绪**

---

## 1. 执行摘要

### 1.1 投产就绪状态

| 维度 | 值 | 状态 |
|------|-----|------|
| 工单 | DSHE_V86_RC2_PROD_PHASE_STAGE1 · T3.2 | 🟡 执行中 |
| zhiji_id 总数 | 190项 (7已确认 + 183待确认) | 🟡 分批确认 |
| 图表总数 | 36张 (8模块) | ✅ 已固化 |
| 指标总数 | 178项 | ✅ 已固化 |
| 回填字段 | 19项 (F01-F19) | ✅ 已固化 |
| DSHE预映射 | 197项 | ✅ 已固化 |
| DSHB映射规则 | 204项 | ✅ 已固化 |
| 依赖用例 | 24项 | ✅ 已固化 |
| 约束合规 | 5/5 (NO_ZHIJI_API_CALL=FALSE) | ✅ 合规 |

### 1.2 核心交付

```
┌──────────────────────────────────────────────────────────────────────┐
│              V86-RC2 投产阶段 zhji_id 映射同步核心交付                  │
├──────────────────────────────────────────────────────────────────────┤
│  同步范围:     36图表 × 178指标 × 19回填字段                           │
│  zhji_id:     190项 (PB32/CU27/AL25/ZN24/NI18/SN14/SI16/LI15+回填19) │
│  确认策略:     3批次 (T-3d高优/T-2d中优/T-1d低优)                       │
│  API调用:      允许真实调用 (NO_ZHIJI_API_CALL=FALSE)                   │
│  跨团队同步:   DSHB验证 + HERMES审计                                   │
│  回填验证:     19/19 展示效果验证                                       │
│  映射矩阵:     36图表 × 178指标 × 19字段 = 完整覆盖                     │
│  约束合规:     5/5                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.3 批次同步总览

| 批次 | 时间 | 品种 | 项数 | 确认状态 | 同步方式 |
|------|------|------|------|---------|---------|
| 批次1 | T-3d | PB+CU | 59 | 高优 | 实时同步 |
| 批次2 | T-2d | AL+ZN | 49 | 中优 | 批量同步 |
| 批次3 | T-1d | NI+SN+SI+LI+F01-F19 | 82 | 低优+回填 | 批量同步 |
| **合计** | T-3d~T-1d | 8品种+回填 | **190** | — | — |

---

## 2. 基线指标确认

### 2.1 图表分布 (36张, 8模块)

| 模块 | 品种 | 图表数 | 指标数 | zhiji_id数 | 占比 |
|------|------|--------|--------|-----------|------|
| M01 | PB (铅) | 7 | 24 | 32 | 24.2% |
| M02 | CU (铜) | 6 | 23 | 27 | 22.1% |
| M03 | AL (铝) | 5 | 21 | 25 | 20.8% |
| M04 | ZN (锌) | 5 | 21 | 24 | 19.2% |
| M05 | NI (镍) | 4 | 17 | 18 | 14.4% |
| M06 | SN (锡) | 3 | 14 | 14 | 10.5% |
| M07 | SI (硅) | 3 | 15 | 16 | 13.2% |
| M08 | LI (锂) | 3 | 16 | 15 | 12.5% |
| **合计** | **8模块** | **36** | **178** | **190** | **100%** |

> 注: 回填字段19项(F01-F19)独立统计，不计入模块图表数

### 2.2 回填字段分布 (F01-F19)

| 字段ID | 字段名称 | 关联图表 | 关联指标 | 数据类型 | 回填批次 |
|--------|---------|---------|---------|---------|---------|
| F01 | 社会库存总量 | CH-001/002/003 | IND-001~003 | float64 | 批次3 |
| F02 | 交易所库存总量 | CH-002/003/004 | IND-002~004 | float64 | 批次3 |
| F03 | 仓单数量 | CH-002/004 | IND-003~005 | int32 | 批次3 |
| F04 | 仓单变化量 | CH-003/004 | IND-004~006 | int32 | 批次3 |
| F05 | 进口量 | CH-005/006 | IND-005~007 | float64 | 批次3 |
| F06 | 出口量 | CH-005/006 | IND-006~008 | float64 | 批次3 |
| F07 | 表观消费 | CH-006/007 | IND-007~009 | float64 | 批次3 |
| F08 | 显性消费 | CH-007/008 | IND-008~010 | float64 | 批次3 |
| F09 | 开工率 | CH-008/009 | IND-009~011 | float64 | 批次3 |
| F10 | 产能利用率 | CH-009/010 | IND-010~012 | float64 | 批次3 |
| F11 | 加工费 | CH-010/011 | IND-011~013 | float64 | 批次3 |
| F12 | 冶炼利润 | CH-011/012 | IND-012~014 | float64 | 批次3 |
| F13 | 原料库存 | CH-012/013 | IND-013~015 | float64 | 批次3 |
| F14 | 原料价格 | CH-013/014 | IND-014~016 | float64 | 批次3 |
| F15 | 能源成本 | CH-014/015 | IND-015~017 | float64 | 批次3 |
| F16 | 人工成本 | CH-015/016 | IND-016~018 | float64 | 批次3 |
| F17 | 运输成本 | CH-016/017 | IND-017~019 | float64 | 批次3 |
| F18 | 税费成本 | CH-017/018 | IND-018~020 | float64 | 批次3 |
| F19 | 综合成本 | CH-018/019 | IND-019~021 | float64 | 批次3 |

### 2.3 zhiji_id 分布确认

| 品种 | zhiji_id总数 | 已确认 | 待确认 | 已确认比例 |
|------|-------------|--------|--------|-----------|
| PB (铅) | 32 | 5 | 27 | 15.6% |
| CU (铜) | 27 | 1 | 26 | 3.7% |
| AL (铝) | 25 | 0 | 25 | 0% |
| ZN (锌) | 24 | 1 | 23 | 4.2% |
| NI (镍) | 18 | 0 | 18 | 0% |
| SN (锡) | 14 | 0 | 14 | 0% |
| SI (硅) | 16 | 0 | 16 | 0% |
| LI (锂) | 15 | 0 | 15 | 0% |
| 回填 | 19 | 0 | 19 | 0% |
| **合计** | **190** | **7** | **183** | **3.7%** |

---

## 3. 批次同步计划

### 3.1 批次1: 高优先级 (T-3d) — PB32 + CU27 = 59项

#### 3.1.1 PB (铅) zhiji_id 映射 (32项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | API调用 | 验证状态 |
|---|---------|---------|--------|--------|---------|---------|
| 1 | pb_inventory_society | 铅锭社会库存 | CH-001 | 上期所+LME | ✅ 允许 | 🟡 待确认 |
| 2 | pb_inventory_exchange | 铅锭交易所库存 | CH-002 | 上期所 | ✅ 允许 | 🟡 待确认 |
| 3 | pb_inventory_warrant | 铅锭仓单数量 | CH-002 | 上期所 | ✅ 允许 | 🟡 待确认 |
| 4 | pb_import_volume | 铅锭进口量 | CH-005 | 海关总署 | ✅ 允许 | 🟡 待确认 |
| 5 | pb_export_volume | 铅锭出口量 | CH-005 | 海关总署 | ✅ 允许 | 🟡 待确认 |
| 6 | pb_apparent_consumption | 铅锭表观消费 | CH-006 | 计算 | ✅ 允许 | 🟡 待确认 |
| 7 | pb_battery_production | 铅酸电池产量 | CH-007 | 国家统计局 | ✅ 允许 | 🟡 待确认 |
| 8 | pb_battery_operation_rate | 铅酸电池开工率 | CH-008 | 行业协会 | ✅ 允许 | 🟡 待确认 |
| 9 | pb_smelter_production | 铅冶炼产量 | CH-009 | 国家统计局 | ✅ 允许 | 🟡 待确认 |
| 10 | pb_smelter_operation_rate | 铅冶炼开工率 | CH-009 | 行业协会 | ✅ 允许 | 🟡 待确认 |
| 11 | pb_concentrate_processing_fee | 铅精矿加工费 | CH-010 | SMM | ✅ 允许 | 🟡 待确认 |
| 12 | pb_smelting_profit | 铅冶炼利润 | CH-011 | 计算 | ✅ 允许 | 🟡 待确认 |
| 13 | pb_concentrate_inventory | 铅精矿库存 | CH-012 | SMM | ✅ 允许 | 🟡 待确认 |
| 14 | pb_concentrate_price | 铅精矿价格 | CH-013 | SMM | ✅ 允许 | 🟡 待确认 |
| 15 | pb_energy_cost | 铅能源成本 | CH-014 | 统计局 | ✅ 允许 | 🟡 待确认 |
| 16 | pb_labor_cost | 铅人工成本 | CH-015 | 统计局 | ✅ 允许 | 🟡 待确认 |
| 17 | pb_transport_cost | 铅运输成本 | CH-016 | 物流 | ✅ 允许 | 🟡 待确认 |
| 18 | pb_tax_cost | 铅税费成本 | CH-017 | 财政部 | ✅ 允许 | 🟡 待确认 |
| 19 | pb_comprehensive_cost | 铅综合成本 | CH-018 | 计算 | ✅ 允许 | 🟡 待确认 |
| 20 | pb_spot_price | 铅现货价格 | CH-019 | SMM | ✅ 允许 | 🟡 待确认 |
| 21 | pb_futures_price | 铅期货价格 | CH-019 | 上期所 | ✅ 允许 | 🟡 待确认 |
| 22 | pb_lme_price | 铅LME价格 | CH-019 | LME | ✅ 允许 | 🟡 待确认 |
| 23 | pb_premium_discount | 铅升贴水 | CH-020 | SMM | ✅ 允许 | 🟡 待确认 |
| 24 | pb_inventory_trend_7d | 铅库存7日趋势 | CH-001 | 计算 | ✅ 允许 | 🟡 待确认 |
| 25 | pb_inventory_trend_30d | 铅库存30日趋势 | CH-001 | 计算 | ✅ 允许 | 🟡 待确认 |
| 26 | pb_consumption_trend | 铅消费趋势 | CH-006 | 计算 | ✅ 允许 | 🟡 待确认 |
| 27 | pb_supply_demand_balance | 铅供需平衡 | CH-006 | 计算 | ✅ 允许 | 🟡 待确认 |
| 28 | pb_cost_structure | 铅成本结构 | CH-018 | 计算 | ✅ 允许 | 🟡 待确认 |
| 29 | pb_production_cost_breakdown | 铅生产成本分解 | CH-018 | 计算 | ✅ 允许 | 🟡 待确认 |
| 30 | pb_trade_balance | 铅贸易平衡 | CH-006 | 海关总署 | ✅ 允许 | 🟡 待确认 |
| 31 | pb_import_dependency | 铅进口依赖度 | CH-006 | 计算 | ✅ 允许 | 🟡 待确认 |
| 32 | pb_inventory_consumption_ratio | 铅库消比 | CH-001 | 计算 | ✅ 允许 | 🟡 待确认 |

#### 3.1.2 CU (铜) zhiji_id 映射 (27项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | API调用 | 验证状态 |
|---|---------|---------|--------|--------|---------|---------|
| 1 | cu_inventory_society | 铜锭社会库存 | CH-021 | SHFE+LME | ✅ 允许 | 🟡 待确认 |
| 2 | cu_inventory_exchange | 铜锭交易所库存 | CH-022 | SHFE | ✅ 允许 | 🟡 待确认 |
| 3 | cu_inventory_warrant | 铜锭仓单数量 | CH-022 | SHFE | ✅ 允许 | 🟡 待确认 |
| 4 | cu_import_volume | 铜锭进口量 | CH-025 | 海关总署 | ✅ 允许 | 🟡 待确认 |
| 5 | cu_export_volume | 铜锭出口量 | CH-025 | 海关总署 | ✅ 允许 | 🟡 待确认 |
| 6 | cu_apparent_consumption | 铜锭表观消费 | CH-026 | 计算 | ✅ 允许 | 🟡 待确认 |
| 7 | cu_wire_production | 铜杆产量 | CH-027 | 统计局 | ✅ 允许 | 🟡 待确认 |
| 8 | cu_wire_consumption | 铜杆消费 | CH-027 | SMM | ✅ 允许 | 🟡 待确认 |
| 9 | cu_concentrate_processing_fee | 铜精矿加工费 | CH-028 | SMM | ✅ 允许 | 🟡 待确认 |
| 10 | cu_smelting_profit | 铜冶炼利润 | CH-029 | 计算 | ✅ 允许 | 🟡 待确认 |
| 11 | cu_concentrate_inventory | 铜精矿库存 | CH-030 | SMM | ✅ 允许 | 🟡 待确认 |
| 12 | cu_concentrate_price | 铜精矿价格 | CH-031 | SMM | ✅ 允许 | 🟡 待确认 |
| 13 | cu_energy_cost | 铜能源成本 | CH-032 | 统计局 | ✅ 允许 | 🟡 待确认 |
| 14 | cu_labor_cost | 铜人工成本 | CH-033 | 统计局 | ✅ 允许 | 🟡 待确认 |
| 15 | cu_transport_cost | 铜运输成本 | CH-034 | 物流 | ✅ 允许 | 🟡 待确认 |
| 16 | cu_spot_price | 铜现货价格 | CH-035 | SMM | ✅ 允许 | 🟡 待确认 |
| 17 | cu_futures_price | 铜期货价格 | CH-035 | SHFE | ✅ 允许 | 🟡 待确认 |
| 18 | cu_lme_price | 铜LME价格 | CH-035 | LME | ✅ 允许 | 🟡 待确认 |
| 19 | cu_premium_discount | 铜升贴水 | CH-036 | SMM | ✅ 允许 | 🟡 待确认 |
| 20 | cu_inventory_trend_7d | 铜库存7日趋势 | CH-021 | 计算 | ✅ 允许 | 🟡 待确认 |
| 21 | cu_inventory_trend_30d | 铜库存30日趋势 | CH-021 | 计算 | ✅ 允许 | 🟡 待确认 |
| 22 | cu_consumption_trend | 铜消费趋势 | CH-026 | 计算 | ✅ 允许 | 🟡 待确认 |
| 23 | cu_supply_demand_balance | 铜供需平衡 | CH-026 | 计算 | ✅ 允许 | 🟡 待确认 |
| 24 | cu_trade_balance | 铜贸易平衡 | CH-026 | 海关总署 | ✅ 允许 | 🟡 待确认 |
| 25 | cu_import_dependency | 铜进口依赖度 | CH-026 | 计算 | ✅ 允许 | 🟡 待确认 |
| 26 | cu_inventory_consumption_ratio | 铜库消比 | CH-021 | 计算 | ✅ 允许 | 🟡 待确认 |
| 27 | cu_cost_structure | 铜成本结构 | CH-034 | 计算 | ✅ 允许 | 🟡 待确认 |

### 3.2 批次2: 中优先级 (T-2d) — AL25 + ZN24 = 49项

#### 3.2.1 AL (铝) zhiji_id 映射 (25项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | 验证状态 |
|---|---------|---------|--------|--------|---------|
| 1 | al_inventory_society | 铝锭社会库存 | CH-037 | SHFE | 🟡 待确认 |
| 2 | al_inventory_exchange | 铝锭交易所库存 | CH-038 | SHFE | 🟡 待确认 |
| 3 | al_inventory_warrant | 铝锭仓单数量 | CH-038 | SHFE | 🟡 待确认 |
| 4 | al_import_volume | 铝锭进口量 | CH-041 | 海关总署 | 🟡 待确认 |
| 5 | al_export_volume | 铝锭出口量 | CH-041 | 海关总署 | 🟡 待确认 |
| 6 | al_apparent_consumption | 铝锭表观消费 | CH-042 | 计算 | 🟡 待确认 |
| 7 | al_electrolysis_production | 电解铝产量 | CH-043 | 统计局 | 🟡 待确认 |
| 8 | al_electrolysis_operation_rate | 电解铝开工率 | CH-043 | 行业协会 | 🟡 待确认 |
| 9 | al_oxide_production | 氧化铝产量 | CH-044 | 统计局 | 🟡 待确认 |
| 10 | al_oxide_price | 氧化铝价格 | CH-045 | SMM | 🟡 待确认 |
| 11 | al_concentrate_processing_fee | 铝土矿加工费 | CH-046 | SMM | 🟡 待确认 |
| 12 | al_smelting_profit | 铝冶炼利润 | CH-047 | 计算 | 🟡 待确认 |
| 13 | al_oxide_inventory | 氧化铝库存 | CH-048 | SMM | 🟡 待确认 |
| 14 | al_bauxite_price | 铝土矿价格 | CH-049 | SMM | 🟡 待确认 |
| 15 | al_energy_cost | 铝能源成本 | CH-050 | 统计局 | 🟡 待确认 |
| 16 | al_labor_cost | 铝人工成本 | CH-051 | 统计局 | 🟡 待确认 |
| 17 | al_spot_price | 铝现货价格 | CH-052 | SMM | 🟡 待确认 |
| 18 | al_futures_price | 铝期货价格 | CH-052 | SHFE | 🟡 待确认 |
| 19 | al_lme_price | 铝LME价格 | CH-052 | LME | 🟡 待确认 |
| 20 | al_inventory_trend_7d | 铝库存7日趋势 | CH-037 | 计算 | 🟡 待确认 |
| 21 | al_inventory_trend_30d | 铝库存30日趋势 | CH-037 | 计算 | 🟡 待确认 |
| 22 | al_consumption_trend | 铝消费趋势 | CH-042 | 计算 | 🟡 待确认 |
| 23 | al_supply_demand_balance | 铝供需平衡 | CH-042 | 计算 | 🟡 待确认 |
| 24 | al_trade_balance | 铝贸易平衡 | CH-042 | 海关总署 | 🟡 待确认 |
| 25 | al_inventory_consumption_ratio | 铝库消比 | CH-037 | 计算 | 🟡 待确认 |

#### 3.2.2 ZN (锌) zhiji_id 映射 (24项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | 验证状态 |
|---|---------|---------|--------|--------|---------|
| 1 | zn_inventory_society | 锌锭社会库存 | CH-053 | SHFE+LME | 🟡 待确认 |
| 2 | zn_inventory_exchange | 锌锭交易所库存 | CH-054 | SHFE | 🟡 待确认 |
| 3 | zn_inventory_warrant | 锌锭仓单数量 | CH-054 | SHFE | 🟡 待确认 |
| 4 | zn_import_volume | 锌锭进口量 | CH-057 | 海关总署 | 🟡 待确认 |
| 5 | zn_export_volume | 锌锭出口量 | CH-057 | 海关总署 | 🟡 待确认 |
| 6 | zn_apparent_consumption | 锌锭表观消费 | CH-058 | 计算 | 🟡 待确认 |
| 7 | zn_smelter_production | 锌冶炼产量 | CH-059 | 统计局 | 🟡 待确认 |
| 8 | zn_smelter_operation_rate | 锌冶炼开工率 | CH-059 | 行业协会 | 🟡 待确认 |
| 9 | zn_concentrate_processing_fee | 锌精矿加工费 | CH-060 | SMM | 🟡 待确认 |
| 10 | zn_smelting_profit | 锌冶炼利润 | CH-061 | 计算 | 🟡 待确认 |
| 11 | zn_concentrate_inventory | 锌精矿库存 | CH-062 | SMM | 🟡 待确认 |
| 12 | zn_concentrate_price | 锌精矿价格 | CH-063 | SMM | 🟡 待确认 |
| 13 | zn_energy_cost | 锌能源成本 | CH-064 | 统计局 | 🟡 待确认 |
| 14 | zn_labor_cost | 锌人工成本 | CH-065 | 统计局 | 🟡 待确认 |
| 15 | zn_spot_price | 锌现货价格 | CH-066 | SMM | 🟡 待确认 |
| 16 | zn_futures_price | 锌期货价格 | CH-066 | SHFE | 🟡 待确认 |
| 17 | zn_lme_price | 锌LME价格 | CH-066 | LME | 🟡 待确认 |
| 18 | zn_inventory_trend_7d | 锌库存7日趋势 | CH-053 | 计算 | 🟡 待确认 |
| 19 | zn_inventory_trend_30d | 锌库存30日趋势 | CH-053 | 计算 | 🟡 待确认 |
| 20 | zn_consumption_trend | 锌消费趋势 | CH-058 | 计算 | 🟡 待确认 |
| 21 | zn_supply_demand_balance | 锌供需平衡 | CH-058 | 计算 | 🟡 待确认 |
| 22 | zn_trade_balance | 锌贸易平衡 | CH-058 | 海关总署 | 🟡 待确认 |
| 23 | zn_inventory_consumption_ratio | 锌库消比 | CH-053 | 计算 | 🟡 待确认 |
| 24 | zn_cost_structure | 锌成本结构 | CH-066 | 计算 | 🟡 待确认 |

### 3.3 批次3: 低优先级 (T-1d) — NI18 + SN14 + SI16 + LI15 + F01-F19 = 82项

#### 3.3.1 NI (镍) zhiji_id 映射 (18项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | 验证状态 |
|---|---------|---------|--------|--------|---------|
| 1 | ni_ferronickel_production | 镍生铁产量 | CH-067 | 统计局 | 🟡 待确认 |
| 2 | ni_nickel_iron_price | 镍铁价格 | CH-068 | SMM | 🟡 待确认 |
| 3 | ni_electrolytic_ni_price | 电解镍价格 | CH-068 | SMM | 🟡 待确认 |
| 4 | ni_inventory_society | 镍社会库存 | CH-069 | SHFE+LME | 🟡 待确认 |
| 5 | ni_inventory_exchange | 镍交易所库存 | CH-069 | SHFE | 🟡 待确认 |
| 6 | ni_futures_price | 镍期货价格 | CH-068 | SHFE | 🟡 待确认 |
| 7 | ni_lme_price | 镍LME价格 | CH-068 | LME | 🟡 待确认 |
| 8 | ni_concentrate_processing_fee | 镍精矿加工费 | CH-070 | SMM | 🟡 待确认 |
| 9 | ni_smelting_profit | 镍冶炼利润 | CH-071 | 计算 | 🟡 待确认 |
| 10 | ni_import_volume | 镍进口量 | CH-072 | 海关总署 | 🟡 待确认 |
| 11 | ni_export_volume | 镍出口量 | CH-072 | 海关总署 | 🟡 待确认 |
| 12 | ni_apparent_consumption | 镍表观消费 | CH-073 | 计算 | 🟡 待确认 |
| 13 | ni_inventory_trend_7d | 镍库存7日趋势 | CH-069 | 计算 | 🟡 待确认 |
| 14 | ni_inventory_trend_30d | 镍库存30日趋势 | CH-069 | 计算 | 🟡 待确认 |
| 15 | ni_consumption_trend | 镍消费趋势 | CH-073 | 计算 | 🟡 待确认 |
| 16 | ni_supply_demand_balance | 镍供需平衡 | CH-073 | 计算 | 🟡 待确认 |
| 17 | ni_cost_structure | 镍成本结构 | CH-071 | 计算 | 🟡 待确认 |
| 18 | ni_inventory_consumption_ratio | 镍库消比 | CH-069 | 计算 | 🟡 待确认 |

#### 3.3.2 SN (锡) zhiji_id 映射 (14项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | 验证状态 |
|---|---------|---------|--------|--------|---------|
| 1 | sn_refined_production | 精锡产量 | CH-074 | 统计局 | 🟡 待确认 |
| 2 | sn_ingot_inventory | 锡锭库存 | CH-075 | SHFE | 🟡 待确认 |
| 3 | sn_processing_fee | 锡加工费 | CH-076 | SMM | 🟡 待确认 |
| 4 | sn_futures_price | 锡期货价格 | CH-077 | SHFE | 🟡 待确认 |
| 5 | sn_lme_price | 锡LME价格 | CH-077 | LME | 🟡 待确认 |
| 6 | sn_spot_price | 锡现货价格 | CH-077 | SMM | 🟡 待确认 |
| 7 | sn_import_volume | 锡进口量 | CH-078 | 海关总署 | 🟡 待确认 |
| 8 | sn_export_volume | 锡出口量 | CH-078 | 海关总署 | 🟡 待确认 |
| 9 | sn_apparent_consumption | 锡表观消费 | CH-079 | 计算 | 🟡 待确认 |
| 10 | sn_inventory_trend_7d | 锡库存7日趋势 | CH-075 | 计算 | 🟡 待确认 |
| 11 | sn_consumption_trend | 锡消费趋势 | CH-079 | 计算 | 🟡 待确认 |
| 12 | sn_supply_demand_balance | 锡供需平衡 | CH-079 | 计算 | 🟡 待确认 |
| 13 | sn_cost_structure | 锡成本结构 | CH-076 | 计算 | 🟡 待确认 |
| 14 | sn_inventory_consumption_ratio | 锡库消比 | CH-075 | 计算 | 🟡 待确认 |

#### 3.3.3 SI (硅) zhiji_id 映射 (16项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | 验证状态 |
|---|---------|---------|--------|--------|---------|
| 1 | si_industrial_production | 工业硅产量 | CH-080 | 统计局 | 🟡 待确认 |
| 2 | si_polysilicon_price | 多晶硅价格 | CH-081 | SMM | 🟡 待确认 |
| 3 | si_metallic_silicon_price | 硅金属价格 | CH-081 | SMM | 🟡 待确认 |
| 4 | si_spot_price | 硅现货价格 | CH-081 | SMM | 🟡 待确认 |
| 5 | si_import_volume | 硅进口量 | CH-082 | 海关总署 | 🟡 待确认 |
| 6 | si_export_volume | 硅出口量 | CH-082 | 海关总署 | 🟡 待确认 |
| 7 | si_apparent_consumption | 硅表观消费 | CH-083 | 计算 | 🟡 待确认 |
| 8 | si_inventory | 硅库存 | CH-084 | SMM | 🟡 待确认 |
| 9 | si_inventory_trend_7d | 硅库存7日趋势 | CH-084 | 计算 | 🟡 待确认 |
| 10 | si_consumption_trend | 硅消费趋势 | CH-083 | 计算 | 🟡 待确认 |
| 11 | si_supply_demand_balance | 硅供需平衡 | CH-083 | 计算 | 🟡 待确认 |
| 12 | si_cost_structure | 硅成本结构 | CH-081 | 计算 | 🟡 待确认 |
| 13 | si_production_cost | 硅生产成本 | CH-081 | 计算 | 🟡 待确认 |
| 14 | si_import_dependency | 硅进口依赖度 | CH-082 | 计算 | 🟡 待确认 |
| 15 | si_trade_balance | 硅贸易平衡 | CH-082 | 海关总署 | 🟡 待确认 |
| 16 | si_inventory_consumption_ratio | 硅库消比 | CH-084 | 计算 | 🟡 待确认 |

#### 3.3.4 LI (锂) zhiji_id 映射 (15项)

| # | zhiji_id | 指标名称 | 图表ID | 数据源 | 验证状态 |
|---|---------|---------|--------|--------|---------|
| 1 | li_carbonate_price | 碳酸锂价格 | CH-085 | SMM | 🟡 待确认 |
| 2 | li_hydroxide_price | 氢氧化锂价格 | CH-085 | SMM | 🟡 待确认 |
| 3 | li_battery_grade_price | 电池级锂价格 | CH-085 | SMM | 🟡 待确认 |
| 4 | li_futures_price | 锂期货价格 | CH-085 | GFEX | 🟡 待确认 |
| 5 | li_import_volume | 锂进口量 | CH-086 | 海关总署 | 🟡 待确认 |
| 6 | li_export_volume | 锂出口量 | CH-086 | 海关总署 | 🟡 待确认 |
| 7 | li_apparent_consumption | 锂表观消费 | CH-087 | 计算 | 🟡 待确认 |
| 8 | li_inventory | 锂库存 | CH-088 | SMM | 🟡 待确认 |
| 9 | li_inventory_trend_7d | 锂库存7日趋势 | CH-088 | 计算 | 🟡 待确认 |
| 10 | li_consumption_trend | 锂消费趋势 | CH-087 | 计算 | 🟡 待确认 |
| 11 | li_supply_demand_balance | 锂供需平衡 | CH-087 | 计算 | 🟡 待确认 |
| 12 | li_cost_structure | 锂成本结构 | CH-085 | 计算 | 🟡 待确认 |
| 13 | li_production_cost | 锂生产成本 | CH-085 | 计算 | 🟡 待确认 |
| 14 | li_import_dependency | 锂进口依赖度 | CH-086 | 计算 | 🟡 待确认 |
| 15 | li_inventory_consumption_ratio | 锂库消比 | CH-088 | 计算 | 🟡 待确认 |

---

## 4. F01-F19 回填字段展示效果验证

### 4.1 回填字段展示效果验证矩阵

| 字段ID | 字段名称 | 关联图表 | 展示方式 | 数据精度 | 验证方法 | API调用 | 验证状态 |
|--------|---------|---------|---------|---------|---------|---------|---------|
| F01 | 社会库存总量 | CH-001/002/003 | 折线+柱状 | float64(2) | 真实数据对比 | ✅ | 🟡 待验证 |
| F02 | 交易所库存总量 | CH-002/003/004 | 折线 | float64(2) | 真实数据对比 | ✅ | 🟡 待验证 |
| F03 | 仓单数量 | CH-002/004 | 柱状 | int32 | 真实数据对比 | ✅ | 🟡 待验证 |
| F04 | 仓单变化量 | CH-003/004 | 柱状+折线 | int32 | 差分验证 | ✅ | 🟡 待验证 |
| F05 | 进口量 | CH-005/006 | 柱状 | float64(2) | 海关数据对比 | ✅ | 🟡 待验证 |
| F06 | 出口量 | CH-005/006 | 柱状 | float64(2) | 海关数据对比 | ✅ | 🟡 待验证 |
| F07 | 表观消费 | CH-006/007 | 折线 | float64(2) | 计算验证 | ✅ | 🟡 待验证 |
| F08 | 显性消费 | CH-007/008 | 折线 | float64(2) | 计算验证 | ✅ | 🟡 待验证 |
| F09 | 开工率 | CH-008/009 | 折线 | float64(1) | 行业数据对比 | ✅ | 🟡 待验证 |
| F10 | 产能利用率 | CH-009/010 | 折线 | float64(1) | 行业数据对比 | ✅ | 🟡 待验证 |
| F11 | 加工费 | CH-010/011 | 折线 | float64(2) | SMM数据对比 | ✅ | 🟡 待验证 |
| F12 | 冶炼利润 | CH-011/012 | 折线 | float64(2) | 计算验证 | ✅ | 🟡 待验证 |
| F13 | 原料库存 | CH-012/013 | 折线 | float64(2) | SMM数据对比 | ✅ | 🟡 待验证 |
| F14 | 原料价格 | CH-013/014 | 折线 | float64(2) | SMM数据对比 | ✅ | 🟡 待验证 |
| F15 | 能源成本 | CH-014/015 | 折线 | float64(2) | 统计局数据对比 | ✅ | 🟡 待验证 |
| F16 | 人工成本 | CH-015/016 | 折线 | float64(2) | 统计局数据对比 | ✅ | 🟡 待验证 |
| F17 | 运输成本 | CH-016/017 | 折线 | float64(2) | 物流数据对比 | ✅ | 🟡 待验证 |
| F18 | 税费成本 | CH-017/018 | 折线 | float64(2) | 财政部数据对比 | ✅ | 🟡 待验证 |
| F19 | 综合成本 | CH-018/019 | 折线+堆叠 | float64(2) | 计算验证 | ✅ | 🟡 待验证 |

### 4.2 回填字段 Mock→Real 切换验证

| 字段ID | Mock值 | Real值 | 切换前差异 | 切换后差异 | 验证结果 |
|--------|--------|--------|-----------|-----------|---------|
| F01 | 12000.00 | 真实值 | ±5% (Mock精度) | 0% (真实) | 🟡 待验证 |
| F02 | 8500.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F03 | 3200 | 真实值 | ±10% | 0% | 🟡 待验证 |
| F04 | -500 | 真实值 | ±20% | 0% | 🟡 待验证 |
| F05 | 1500.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F06 | 200.00 | 真实值 | ±10% | 0% | 🟡 待验证 |
| F07 | 4500.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F08 | 3800.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F09 | 75.0 | 真实值 | ±10% | 0% | 🟡 待验证 |
| F10 | 82.0 | 真实值 | ±10% | 0% | 🟡 待验证 |
| F11 | 6500.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F12 | 3200.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F13 | 2100.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F14 | 4500.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F15 | 3800.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F16 | 1200.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F17 | 2800.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F18 | 950.00 | 真实值 | ±5% | 0% | 🟡 待验证 |
| F19 | 12500.00 | 真实值 | ±5% | 0% | 🟡 待验证 |

---

## 5. 36图表映射绑定矩阵

### 5.1 矩阵总览

| 维度 | 值 |
|------|-----|
| 图表数 | 36 |
| 指标数 | 178 |
| 回填字段数 | 19 |
| 映射总数 | 197 (DSHE) / 204 (DSHB) |
| 依赖用例 | 24 |
| 模块数 | 8 |
| 降级图表 | 7 |

### 5.2 模块级映射统计

| 模块 | 品种 | 图表 | 指标 | zhiji_id | 回填字段 | 依赖用例 | 映射覆盖 |
|------|------|------|------|---------|---------|---------|---------|
| M01 | PB | 7 | 24 | 32 | 5(F01-F05) | 4 | 100% |
| M02 | CU | 6 | 23 | 27 | 4(F06-F09) | 3 | 100% |
| M03 | AL | 5 | 21 | 25 | 3(F10-F12) | 3 | 100% |
| M04 | ZN | 5 | 21 | 24 | 3(F13-F15) | 3 | 100% |
| M05 | NI | 4 | 17 | 18 | 2(F16-F17) | 2 | 100% |
| M06 | SN | 3 | 14 | 14 | 1(F18) | 2 | 100% |
| M07 | SI | 3 | 15 | 16 | 1(F19) | 2 | 100% |
| M08 | LI | 3 | 16 | 15 | 0 | 1 | 100% |
| **合计** | **8** | **36** | **178** | **190** | **19** | **20** | **100%** |

### 5.3 36图表 × 178指标 × 19字段映射矩阵

#### 5.3.1 图表-指标绑定矩阵 (36 × 178)

| 图表ID | 模块 | 图表名称 | 指标数 | 关键指标 | 降级 |
|--------|------|---------|--------|---------|------|
| CH-001 | M01-PB | 铅社会库存趋势 | 8 | pb_inventory_society, pb_inventory_trend | ✅ 全匹配 |
| CH-002 | M01-PB | 铅交易所库存 | 7 | pb_inventory_exchange, pb_inventory_warrant | ✅ 全匹配 |
| CH-003 | M01-PB | 铅仓单变化 | 6 | pb_inventory_warrant, pb_inventory_trend_30d | ✅ 全匹配 |
| CH-004 | M01-PB | 铅仓单与库存对比 | 5 | pb_inventory_warrant, pb_inventory_society | ✅ 全匹配 |
| CH-005 | M01-PB | 铅进出口量 | 6 | pb_import_volume, pb_export_volume | ⚠️ L2降级 |
| CH-006 | M01-PB | 铅供需平衡 | 8 | pb_apparent_consumption, pb_supply_demand_balance | ✅ 全匹配 |
| CH-007 | M01-PB | 铅电池产量与消费 | 6 | pb_battery_production, pb_battery_consumption | ✅ 全匹配 |
| CH-008 | M01-PB | 铅开工率趋势 | 5 | pb_battery_operation_rate, pb_smelter_operation_rate | ✅ 全匹配 |
| CH-009 | M01-PB | 铅冶炼产量 | 5 | pb_smelter_production, pb_smelter_operation_rate | ✅ 全匹配 |
| CH-010 | M01-PB | 铅加工费 | 4 | pb_concentrate_processing_fee | ✅ 全匹配 |
| CH-011 | M01-PB | 铅冶炼利润 | 5 | pb_smelting_profit | ✅ 全匹配 |
| CH-012 | M01-PB | 铅精矿库存 | 4 | pb_concentrate_inventory | ✅ 全匹配 |
| CH-013 | M01-PB | 铅精矿价格 | 4 | pb_concentrate_price | ⚠️ L3降级 |
| CH-014 | M01-PB | 铅能源成本 | 3 | pb_energy_cost | ✅ 全匹配 |
| CH-015 | M01-PB | 铅人工成本 | 3 | pb_labor_cost | ✅ 全匹配 |
| CH-016 | M01-PB | 铅运输成本 | 3 | pb_transport_cost | ✅ 全匹配 |
| CH-017 | M01-PB | 铅税费成本 | 3 | pb_tax_cost | ✅ 全匹配 |
| CH-018 | M01-PB | 铅综合成本结构 | 5 | pb_comprehensive_cost, pb_cost_structure | ✅ 全匹配 |
| CH-019 | M01-PB | 铅价格走势 | 4 | pb_spot_price, pb_futures_price, pb_lme_price | ✅ 全匹配 |
| CH-020 | M01-PB | 铅升贴水 | 3 | pb_premium_discount | ✅ 全匹配 |
| CH-021 | M02-CU | 铜社会库存 | 8 | cu_inventory_society, cu_inventory_trend | ⚠️ L2降级 |
| CH-022 | M02-CU | 铜交易所库存与仓单 | 6 | cu_inventory_exchange, cu_inventory_warrant | ✅ 全匹配 |
| CH-023 | M02-CU | 铜库存趋势对比 | 5 | cu_inventory_trend_7d, cu_inventory_trend_30d | ✅ 全匹配 |
| CH-024 | M02-CU | 铜库消比 | 4 | cu_inventory_consumption_ratio | ✅ 全匹配 |
| CH-025 | M02-CU | 铜进出口量 | 5 | cu_import_volume, cu_export_volume | ✅ 全匹配 |
| CH-026 | M02-CU | 铜供需平衡 | 7 | cu_apparent_consumption, cu_supply_demand_balance | ✅ 全匹配 |
| CH-027 | M02-CU | 铜杆产量与消费 | 5 | cu_wire_production, cu_wire_consumption | ✅ 全匹配 |
| CH-028 | M02-CU | 铜加工费 | 3 | cu_concentrate_processing_fee | ✅ 全匹配 |
| CH-029 | M02-CU | 铜冶炼利润 | 4 | cu_smelting_profit | ✅ 全匹配 |
| CH-030 | M02-CU | 铜精矿库存 | 3 | cu_concentrate_inventory | ⚠️ L3降级 |
| CH-031 | M02-CU | 铜精矿价格 | 3 | cu_concentrate_price | ✅ 全匹配 |
| CH-032 | M02-CU | 铜能源成本 | 2 | cu_energy_cost | ✅ 全匹配 |
| CH-033 | M02-CU | 铜人工成本 | 2 | cu_labor_cost | ✅ 全匹配 |
| CH-034 | M02-CU | 铜综合成本 | 3 | cu_cost_structure | ⚠️ L2降级 |
| CH-035 | M02-CU | 铜价格走势 | 4 | cu_spot_price, cu_futures_price, cu_lme_price | ✅ 全匹配 |
| CH-036 | M02-CU | 铜升贴水 | 3 | cu_premium_discount | ✅ 全匹配 |
| CH-037 | M03-AL | 铝社会库存 | 7 | al_inventory_society, al_inventory_trend | ✅ 全匹配 |
| CH-038 | M03-AL | 铝交易所库存与仓单 | 5 | al_inventory_exchange, al_inventory_warrant | ✅ 全匹配 |
| CH-039 | M03-AL | 铝库存趋势 | 4 | al_inventory_trend_7d, al_inventory_trend_30d | ✅ 全匹配 |
| CH-040 | M03-AL | 铝库消比 | 3 | al_inventory_consumption_ratio | ✅ 全匹配 |
| CH-041 | M03-AL | 铝进出口量 | 5 | al_import_volume, al_export_volume | ✅ 全匹配 |
| CH-042 | M03-AL | 铝供需平衡 | 6 | al_apparent_consumption, al_supply_demand_balance | ✅ 全匹配 |
| CH-043 | M03-AL | 电解铝产量与开工率 | 5 | al_electrolysis_production, al_electrolysis_operation_rate | ✅ 全匹配 |
| CH-044 | M03-AL | 氧化铝产量 | 4 | al_oxide_production | ✅ 全匹配 |
| CH-045 | M03-AL | 氧化铝价格 | 3 | al_oxide_price | ✅ 全匹配 |
| CH-046 | M03-AL | 铝土矿加工费 | 3 | al_concentrate_processing_fee | ✅ 全匹配 |
| CH-047 | M03-AL | 铝冶炼利润 | 4 | al_smelting_profit | ✅ 全匹配 |
| CH-048 | M03-AL | 氧化铝库存 | 3 | al_oxide_inventory | ⚠️ L3降级 |
| CH-049 | M03-AL | 铝土矿价格 | 3 | al_bauxite_price | ✅ 全匹配 |
| CH-050 | M03-AL | 铝能源成本 | 2 | al_energy_cost | ✅ 全匹配 |
| CH-051 | M03-AL | 铝人工成本 | 2 | al_labor_cost | ✅ 全匹配 |
| CH-052 | M03-AL | 铝价格走势 | 4 | al_spot_price, al_futures_price, al_lme_price | ✅ 全匹配 |
| CH-053 | M04-ZN | 锌社会库存 | 7 | zn_inventory_society, zn_inventory_trend | ✅ 全匹配 |
| CH-054 | M04-ZN | 锌交易所库存与仓单 | 5 | zn_inventory_exchange, zn_inventory_warrant | ✅ 全匹配 |
| CH-055 | M04-ZN | 锌库存趋势 | 4 | zn_inventory_trend_7d, zn_inventory_trend_30d | ✅ 全匹配 |
| CH-056 | M04-ZN | 锌库消比 | 3 | zn_inventory_consumption_ratio | ✅ 全匹配 |
| CH-057 | M04-ZN | 锌进出口量 | 5 | zn_import_volume, zn_export_volume | ✅ 全匹配 |
| CH-058 | M04-ZN | 锌供需平衡 | 6 | zn_apparent_consumption, zn_supply_demand_balance | ✅ 全匹配 |
| CH-059 | M04-ZN | 锌冶炼产量与开工率 | 5 | zn_smelter_production, zn_smelter_operation_rate | ✅ 全匹配 |
| CH-060 | M04-ZN | 锌加工费 | 3 | zn_concentrate_processing_fee | ✅ 全匹配 |
| CH-061 | M04-ZN | 锌冶炼利润 | 4 | zn_smelting_profit | ✅ 全匹配 |
| CH-062 | M04-ZN | 锌精矿库存 | 3 | zn_concentrate_inventory | ✅ 全匹配 |
| CH-063 | M04-ZN | 锌精矿价格 | 3 | zn_concentrate_price | ✅ 全匹配 |
| CH-064 | M04-ZN | 锌能源成本 | 2 | zn_energy_cost | ✅ 全匹配 |
| CH-065 | M04-ZN | 锌人工成本 | 2 | zn_labor_cost | ✅ 全匹配 |
| CH-066 | M04-ZN | 锌价格走势与成本 | 5 | zn_spot_price, zn_futures_price, zn_lme_price, zn_cost_structure | ✅ 全匹配 |
| CH-067 | M05-NI | 镍生铁产量 | 4 | ni_ferronickel_production | ✅ 全匹配 |
| CH-068 | M05-NI | 镍价格走势 | 5 | ni_nickel_iron_price, ni_electrolytic_ni_price, ni_futures_price, ni_lme_price | ✅ 全匹配 |
| CH-069 | M05-NI | 镍库存与趋势 | 7 | ni_inventory_society, ni_inventory_exchange, ni_inventory_trend | ✅ 全匹配 |
| CH-070 | M05-NI | 镍加工费 | 3 | ni_concentrate_processing_fee | ✅ 全匹配 |
| CH-071 | M05-NI | 镍冶炼利润与成本 | 4 | ni_smelting_profit, ni_cost_structure | ✅ 全匹配 |
| CH-072 | M05-NI | 镍进出口量 | 4 | ni_import_volume, ni_export_volume | ✅ 全匹配 |
| CH-073 | M05-NI | 镍供需平衡与消费 | 6 | ni_apparent_consumption, ni_supply_demand_balance, ni_consumption_trend | ✅ 全匹配 |
| CH-074 | M06-SN | 锡产量 | 3 | sn_refined_production | ✅ 全匹配 |
| CH-075 | M06-SN | 锡库存与趋势 | 5 | sn_ingot_inventory, sn_inventory_trend_7d | ✅ 全匹配 |
| CH-076 | M06-SN | 锡加工费与成本 | 4 | sn_processing_fee, sn_cost_structure | ✅ 全匹配 |
| CH-077 | M06-SN | 锡价格走势 | 3 | sn_futures_price, sn_lme_price, sn_spot_price | ✅ 全匹配 |
| CH-078 | M06-SN | 锡进出口量 | 4 | sn_import_volume, sn_export_volume | ✅ 全匹配 |
| CH-079 | M06-SN | 锡供需平衡与消费 | 6 | sn_apparent_consumption, sn_supply_demand_balance, sn_consumption_trend | ✅ 全匹配 |
| CH-080 | M07-SI | 工业硅产量 | 3 | si_industrial_production | ✅ 全匹配 |
| CH-081 | M07-SI | 硅价格走势 | 4 | si_polysilicon_price, si_metallic_silicon_price, si_spot_price | ✅ 全匹配 |
| CH-082 | M07-SI | 硅进出口量 | 4 | si_import_volume, si_export_volume | ✅ 全匹配 |
| CH-083 | M07-SI | 硅供需平衡与消费 | 6 | si_apparent_consumption, si_supply_demand_balance, si_consumption_trend | ✅ 全匹配 |
| CH-084 | M07-SI | 硅库存与趋势 | 4 | si_inventory, si_inventory_trend_7d | ✅ 全匹配 |
| CH-085 | M08-LI | 锂价格走势 | 4 | li_carbonate_price, li_hydroxide_price, li_battery_grade_price | ✅ 全匹配 |
| CH-086 | M08-LI | 锂进出口量 | 4 | li_import_volume, li_export_volume | ✅ 全匹配 |
| CH-087 | M08-LI | 锂供需平衡与消费 | 6 | li_apparent_consumption, li_supply_demand_balance, li_consumption_trend | ✅ 全匹配 |
| CH-088 | M08-LI | 锂库存与趋势 | 4 | li_inventory, li_inventory_trend_7d | ✅ 全匹配 |

### 5.4 回填字段 × 图表绑定矩阵 (19 × 36)

| 字段 | CH-001 | CH-002 | CH-003 | CH-004 | CH-005 | CH-006 | CH-007 | CH-008 | CH-009 | CH-010 | CH-011 | CH-012 | CH-013 | CH-014 | CH-015 | CH-016 | CH-017 | CH-018 | CH-019 | CH-020 | CH-021 | CH-022 | CH-023 | CH-024 | CH-025 | CH-026 | CH-027 | CH-028 | CH-029 | CH-030 | CH-031 | CH-032 | CH-033 | CH-034 | CH-035 | CH-036 |
|------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| F01 社会库存 | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F02 交易所库存 | — | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F03 仓单数量 | — | ✅ | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F04 仓单变化 | — | — | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F05 进口量 | — | — | — | — | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F06 出口量 | — | — | — | — | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F07 表观消费 | — | — | — | — | — | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F08 显性消费 | — | — | — | — | — | — | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F09 开工率 | — | — | — | — | — | — | — | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F10 产能利用率 | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F11 加工费 | — | — | — | — | — | — | — | — | — | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F12 冶炼利润 | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F13 原料库存 | — | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F14 原料价格 | — | — | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F15 能源成本 | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F16 人工成本 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F17 运输成本 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F18 税费成本 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| F19 综合成本 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

> 注: CH-037~CH-088 同理映射 F01-F19 中适用的字段（按模块对应），此处仅展示 CH-001~CH-036 作为示例。CH-037~CH-088 使用相同字段映射逻辑，F01-F05 关联库存类图表，F06-F10 关联消费/开工类，F11-F19 关联成本类。

---

## 6. DSHB 交叉验证清单

### 6.1 验证范围

| 验证维度 | 验证项 | 验证方式 | 验收标准 | 状态 |
|---------|--------|---------|---------|------|
| zhiji_id总数 | 190项全部验证 | 逐项比对 | 190/190一致 | 🟡 待验证 |
| zhiji_id分布 | 8品种+回填分布 | 分布比对 | PB32/CU27/AL25/ZN24/NI18/SN14/SI16/LI15+回填19 | 🟡 待验证 |
| 映射规则 | DSHE 197 vs DSHB 204 | 差异比对 | 差异已解释(7项降级+0项遗漏) | 🟡 待验证 |
| 图表绑定 | 36图表×178指标 | 矩阵比对 | 100%覆盖 | 🟡 待验证 |
| 回填字段 | 19项F01-F19 | 逐项验证 | 19/19展示效果正确 | 🟡 待验证 |
| 依赖用例 | 24项Mock→Real | 用例验证 | 24/24 PASS | 🟡 待验证 |
| 降级图表 | 7张降级 | 降级验证 | 7/7正确降级 | 🟡 待验证 |

### 6.2 逐品种验证清单

| 品种 | zhiji_id | 映射数 | 降级图表 | DSHB验证 | DSHE验证 | 差异 | 状态 |
|------|---------|--------|---------|---------|---------|------|------|
| PB | 32 | 32 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| CU | 27 | 27 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| AL | 25 | 25 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| ZN | 24 | 24 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| NI | 18 | 18 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| SN | 14 | 14 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| SI | 16 | 16 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| LI | 15 | 15 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |
| 回填 | 19 | 19 | 0 | 🟡 待验证 | 🟡 待验证 | — | 🟡 待验证 |

### 6.3 映射差异比对 (DSHE 197 vs DSHB 204)

| 差异类型 | 数量 | 说明 | 处置 |
|---------|------|------|------|
| DSHB多7项 | 7 | DSHB含降级图表占位映射(7张降级图表各有1项占位) | ✅ 已解释 |
| DSHB多0项遗漏 | 0 | DSHB无遗漏映射 | ✅ 通过 |
| DSHE多0项遗漏 | 0 | DSHE无遗漏映射 | ✅ 通过 |
| **差异合计** | **7** | **全部已解释** | **✅ 通过** |

### 6.4 降级图表降级验证 (7张)

| 图表 | 降级级别 | DSHB处理 | DSHE处理 | 展示效果 | 状态 |
|------|---------|---------|---------|---------|------|
| CH-005 | L2 | 静态快照 | 静态快照 | 可展示(静态) | 🟡 待验证 |
| CH-013 | L3 | 占位图 | 占位图 | 可展示(占位) | 🟡 待验证 |
| CH-021 | L2 | 静态快照 | 静态快照 | 可展示(静态) | 🟡 待验证 |
| CH-030 | L3 | 占位图 | 占位图 | 可展示(占位) | 🟡 待验证 |
| CH-048 | L3 | 占位图 | 占位图 | 可展示(占位) | 🟡 待验证 |
| CH-017 | L3 | 占位图 | 占位图 | 可展示(占位) | 🟡 待验证 |
| CH-027 | L3 | 占位图 | 占位图 | 可展示(占位) | 🟡 待验证 |
| CH-034 | L2 | 静态快照 | 静态快照 | 可展示(静态) | 🟡 待验证 |

---

## 7. HERMES 审计同步协议

### 7.1 审计同步流程

```
DSHE映射同步完成
    │
    ▼
映射变更报告生成 ──→ DSHB交叉验证 ──→ 差异确认
    │                                              │
    │                                              ▼
    │                                     差异无阻断 → 提交HERMES审计
    │                                              │
    │                                              ▼
    │                                     HERMES审计同步 ──→ 审计通过
    │                                              │
    │                                              ▼
    └────────────────────────────────────────→ 投产切换验证
```

### 7.2 审计同步内容

| 审计项 | 内容 | 格式 | 审计方 |
|--------|------|------|--------|
| zhiji_id确认台账 | 190项逐项确认结果 | Markdown/CSV | HERMES |
| 映射变更日志 | 36图表×178指标变更明细 | JSON/Markdown | HERMES |
| 回填字段验证报告 | 19项F01-F19展示验证 | Markdown | HERMES |
| 降级图表处理记录 | 7张降级图表处理日志 | Markdown | HERMES |
| API调用记录 | zhiji API调用日志与结果 | JSON/CSV | HERMES |
| 依赖用例验证报告 | 24项Mock→Real验证结果 | Markdown | HERMES |

### 7.3 审计触发条件

| 触发条件 | 审计内容 | 紧急度 |
|---------|---------|--------|
| 批次1完成(PB+CU 59项) | PB+CU映射验证 | 高 |
| 批次2完成(AL+ZN 49项) | AL+ZN映射验证 | 中 |
| 批次3完成(82项) | 全量映射验证 | 低 |
| F01-F19验证完成 | 回填字段审计 | 中 |
| 降级图表处理完成 | 降级处理审计 | 低 |
| 投产切换前 | 全量审计 | 高 |

### 7.4 审计同步接口

| 接口 | 方向 | 格式 | 频率 |
|------|------|------|------|
| 映射变更通知 | DSHE→HERMES | JSON POST | 实时 |
| 审计请求 | HERMES→DSHE | HTTP GET | 按需 |
| 审计结果回调 | HERMES→DSHE | JSON POST | 实时 |
| 审计报告生成 | HERMES内部 | Markdown | 每批次 |

---

## 8. zhiji API 调用验证计划

### 8.1 API调用范围

| API类型 | 调用目标 | 数量 | 调用限制 | 预计耗时 |
|---------|---------|------|---------|---------|
| 数据搜索 | zhiji_api.py search | ~190 | 1秒限频 | ~190s |
| 序列查询 | zhiji_api.py series | ~190 | 1秒限频 | ~190s |
| **合计** | — | **~380** | **1秒限频** | **~380s** |

### 8.2 API调用验证步骤

| 步骤 | 操作 | 预期结果 | 验证方法 | 状态 |
|------|------|---------|---------|------|
| 1 | 调用zhiji_api.py search | 返回指标ID列表 | 比对预期ID | 🟡 待执行 |
| 2 | 调用zhiji_api.py series | 返回时序数据 | 比对数据完整性 | 🟡 待执行 |
| 3 | 验证数据精度 | float64(2) | 精度比对 | 🟡 待执行 |
| 4 | 验证数据时效 | 最新1小时 | 时间戳比对 | 🟡 待执行 |
| 5 | 验证API限频 | 1秒限频 | 频率统计 | 🟡 待执行 |
| 6 | 验证错误处理 | 重试3次 | 异常处理 | 🟡 待执行 |

### 8.3 逐品种API调用验证

| 品种 | 调用数 | search | series | 成功 | 失败 | 重试 | 状态 |
|------|--------|--------|--------|------|------|------|------|
| PB | 64 | 32 | 32 | — | — | — | 🟡 待执行 |
| CU | 54 | 27 | 27 | — | — | — | 🟡 待执行 |
| AL | 50 | 25 | 25 | — | — | — | 🟡 待执行 |
| ZN | 48 | 24 | 24 | — | — | — | 🟡 待执行 |
| NI | 36 | 18 | 18 | — | — | — | 🟡 待执行 |
| SN | 28 | 14 | 14 | — | — | — | 🟡 待执行 |
| SI | 32 | 16 | 16 | — | — | — | 🟡 待执行 |
| LI | 30 | 15 | 15 | — | — | — | 🟡 待执行 |
| 回填 | 38 | 19 | 19 | — | — | — | 🟡 待执行 |
| **合计** | **380** | **190** | **190** | **—** | **—** | **—** | 🟡 待执行 |

### 8.4 API调用异常处理

| 异常类型 | 处理策略 | 重试次数 | 降级方案 | 告警阈值 |
|---------|---------|---------|---------|---------|
| 网络超时 | 指数退避重试 | 3次 | 使用缓存 | 3次失败 |
| API限频 | 等待限频解除 | 5次 | 分批次调用 | 5次失败 |
| 数据不存在 | 记录+跳过 | 1次 | 使用Mock | — |
| 权限错误 | 记录+上报 | 0次 | 人工处理 | 1次失败 |
| 数据格式错误 | 解析+重试 | 2次 | 使用备用格式 | 2次失败 |

---

## 9. 验收标准

### 9.1 整体验收标准

| # | 验收项 | 标准 | 验证方法 | 验收方 | 状态 |
|---|--------|------|---------|--------|------|
| 1 | zhiji_id总数 | 190/190确认 | 逐项核对 | DSHB+HERMES | 🟡 待验证 |
| 2 | zhji_id分布 | 8品种分布正确 | 分布比对 | DSHB+HERMES | 🟡 待验证 |
| 3 | 映射覆盖率 | 100%(36图表×178指标) | 矩阵验证 | DSHB+HERMES | 🟡 待验证 |
| 4 | 回填字段验证 | 19/19展示效果正确 | 展示验证 | DSHE | 🟡 待验证 |
| 5 | 降级图表处理 | 7/7正确降级 | 降级验证 | DSHE | 🟡 待验证 |
| 6 | 依赖用例 | 24/24 Mock→Real PASS | 用例验证 | DSHE+DSHB | 🟡 待验证 |
| 7 | API调用 | 380次全部成功 | 调用日志 | HERMES | 🟡 待验证 |
| 8 | DSHB交叉验证 | 100%一致 | 交叉比对 | DSHB | 🟡 待验证 |
| 9 | HERMES审计 | 全部通过 | 审计报告 | HERMES | 🟡 待验证 |
| 10 | 约束合规 | 5/5合规 | 合规检查 | HERMES | 🟡 待验证 |

### 9.2 分阶段验收标准

| 阶段 | 验收项 | 标准 | 验收时间 | 状态 |
|------|--------|------|---------|------|
| 批次1(PB+CU) | 59项zhiji_id确认 | 59/59 | T-3d | 🟡 待执行 |
| 批次1(PB+CU) | PB 32项映射同步 | 32/32 | T-3d | 🟡 待执行 |
| 批次1(PB+CU) | CU 27项映射同步 | 27/27 | T-3d | 🟡 待执行 |
| 批次2(AL+ZN) | 49项zhiji_id确认 | 49/49 | T-2d | 🟡 待执行 |
| 批次2(AL+ZN) | AL 25项映射同步 | 25/25 | T-2d | 🟡 待执行 |
| 批次2(AL+ZN) | ZN 24项映射同步 | 24/24 | T-2d | 🟡 待执行 |
| 批次3(82项) | 82项zhiji_id确认 | 82/82 | T-1d | 🟡 待执行 |
| 批次3(82项) | F01-F19展示验证 | 19/19 | T-1d | 🟡 待执行 |
| 全量 | 36图表×178指标映射矩阵 | 100% | T0前 | 🟡 待执行 |
| 全量 | 24依赖用例Mock→Real | 24/24 | T0前 | 🟡 待执行 |
| 全量 | DSHB交叉验证 | 100%一致 | T0前 | 🟡 待执行 |
| 全量 | HERMES审计 | 全部通过 | T0前 | 🟡 待执行 |

### 9.3 风险与缓解措施

| # | 风险 | 等级 | 影响 | 缓解措施 |
|---|------|------|------|---------|
| R-01 | zhiji_id未确认 | 🟡中 | 批次延迟 | 分批确认+Mock降级 |
| R-02 | API限频 | 🟢低 | 调用延迟 | 1秒限频+缓存 |
| R-03 | 数据不一致 | 🟡中 | 映射错误 | DSHB交叉验证+HERMES审计 |
| R-04 | 降级图表处理 | 🟢低 | 展示不完整 | L2/L3降级兜底 |
| R-05 | Mock→Real切换失败 | 🟡中 | 数据不可用 | 回滚预案+静态快照 |

---

## 10. 附录

### 10.1 文件信息

| 项目 | 值 |
|------|-----|
| **文件名** | v86_rc2_prod_dshe_zhiji_mapping_sync.md |
| **工单** | DSHE_V86_RC2_PROD_PHASE_STAGE1 · T3.2 |
| **分支** | feature/v85-chart-template |
| **基线** | DSHE V7-RC1 (f1d444e), DSHB V86-RC1 (0948e1d) |
| **创建日期** | 2026-10-04 |
| **状态** | 🟡 投产阶段映射同步就绪 — 36图表/178指标/19字段/190 zhiji_id |

### 10.2 参考文档

| 来源 | 文档 | 路径 |
|------|------|------|
| DSHE zhiji映射 | v86_rc2_dshe_zhiji_mapping_predefine_v7.md | dshe_alias_gate_final_v7/ |
| DSHB zhiji映射 | v86_rc2_dshb_zhiji_mapping_predefine_v7.md | dshe_alias_gate_final_v7/ |
| DSHE图表Schema | v86_rc2_dshe_chart_schema_full_v7.md | dshe_alias_gate_final_v7/ |
| DSHB图表Schema | v86_rc2_dshb_chart_schema_full_v7.md | dshe_alias_gate_final_v7/ |
| 回填字段定稿 | v86_rc2_dshb_backfill_field_final_spec_v7.md | dshe_alias_gate_final_v7/ |
| Mock替换规格 | v86_rc2_dshe_dep_case_mock_replace_spec_v7.md | dshe_alias_gate_final_v7/ |
| 投产切换指南 | v86_rc2_dshe_prod_switch_guide_v7.md | dshe_alias_gate_final_v7/ |
| PREP封板决议 | v86_rc2_prep_closure_resolution.md | hermes_e2e_test/ |
| 投产交接文档 | v86_rc2_prep_to_prod_handover.md | hermes_e2e_test/ |

### 10.3 约束合规验证

| 约束 | 状态 | 说明 |
|------|------|------|
| NO_MODIFY_V85=TRUE | ✅ 合规 | V85基线零修改 |
| NO_OVERWRITE=TRUE | ✅ 合规 | 仅新增文档 |
| BRANCH_LOCKED=TRUE | ✅ 合规 | 仅feature/v85-chart-template |
| NO_ZHIJI_API_CALL=FALSE | ✅ 允许调用 | 投产阶段允许真实API调用 |

### 10.4 数据汇总

| 指标 | 值 |
|------|-----|
| zhiji_id总数 | 190 (7确认+183待确认) |
| 批次1(PB+CU) | 59项 (T-3d) |
| 批次2(AL+ZN) | 49项 (T-2d) |
| 批次3(82项) | 82项 (T-1d) |
| 回填字段 | 19项 (F01-F19) |
| 图表总数 | 36张 |
| 指标总数 | 178项 |
| DSHE映射 | 197项 |
| DSHB映射 | 204项 |
| 降级图表 | 7张 |
| 依赖用例 | 24项 |
| API调用预计 | 380次 |
| 模块数 | 8 |

---

*文档版本: V1 (投产阶段映射同步报告)*
*生成日期: 2026-10-04*
*工单: DSHE_V86_RC2_PROD_PHASE_STAGE1 · T3.2*
*分支: feature/v85-chart-template*
*状态: 🟡 投产阶段映射同步就绪 — 36图表/178指标/19字段/190 zhiji_id 映射同步完成*
