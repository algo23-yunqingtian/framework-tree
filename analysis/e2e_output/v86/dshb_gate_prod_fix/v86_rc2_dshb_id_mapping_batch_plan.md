# DSHB V86-RC2 投产阶段 — ID桥接全量映射9批次执行计划

> **工单**: DSHB_V86_RC2_ID_MAPPING_FULL_T3.1
> **分支**: `feature/v85-chart-template` (BRANCH_LOCKED=TRUE)
> **执行日期**: 2026-10-13
> **前置基线**: DSHB_PROD_PHASE_FIX_DONE=TRUE, V86_RC2_PREP_CLOSED=TRUE
> **当前状态**: 桥接表V2真实有效桥接率=4.49% (8/178), 170项PENDING条目待映射
> **目标**: 全量映射170项PENDING条目, 真实有效桥接率≥80% (≥143/178)
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **跨团队同步**: DSHE (抽样验证), HERMES (二次审计)

---

## 目录

1. [映射目标与现状](#1-映射目标与现状)
2. [9批次拆分总览](#2-9批次拆分总览)
3. [Batch-1: P0核心指标 (9项)](#3-batch-1-p0核心指标-9项)
4. [Batch-2: P1-PB扩展 (28项)](#4-batch-2-p1-pb扩展-28项)
5. [Batch-3: P1-CU扩展 (23项)](#5-batch-3-p1-cu扩展-23项)
6. [Batch-4: P1-ZN扩展 (22项)](#6-batch-4-p1-zn扩展-22项)
7. [Batch-5: P1-AL全模块 (25项)](#7-batch-5-p1-al全模块-25项)
8. [Batch-6: P2-NI全模块 (18项)](#8-batch-6-p2-ni全模块-18项)
9. [Batch-7: P2-SN全模块 (14项)](#9-batch-7-p2-sn全模块-14项)
10. [Batch-8: P2-SI全模块 (16项)](#10-batch-8-p2-si全模块-16项)
11. [Batch-9: P2-LI全模块 (15项)](#11-batch-9-p2-li全模块-15项)
12. [映射方法与策略](#12-映射方法与策略)
13. [验收标准](#13-验收标准)
14. [约束合规声明](#14-约束合规声明)

---

## 1. 映射目标与现状

### 1.1 当前桥接状态

| 维度 | 数量 | 占比 |
|------|------|------|
| 总指标条目 | 178 | 100% |
| COMPLETED (已映射) | 8 | 4.49% |
| PENDING (待映射) | 170 | 95.51% |
| 回填字段 (已MAPPED) | 19 | 不计入桥接率 |

### 1.2 映射目标

```
映射目标:
  目标有效桥接率: ≥80%
  目标COMPLETED数: ≥143/178
  当前COMPLETED数: 8/178
  需要新增映射: ≥135项
  预计执行批次: 9批次
  预计完成时间: 2026-10-16前
```

### 1.3 9批次进度目标

| 批次 | 完成后COMPLETED | 有效桥接率 | 目标 |
|------|----------------|-----------|------|
| Batch-1 | 8+9=17 | 9.55% | P0核心指标全部映射 |
| Batch-2 | 17+28=45 | 25.28% | PB系列全部映射 |
| Batch-3 | 45+23=68 | 38.20% | CU系列全部映射 |
| Batch-4 | 68+22=90 | 50.56% | ZN系列全部映射 |
| Batch-5 | 90+25=115 | 64.61% | AL系列全部映射 |
| Batch-6 | 115+18=133 | 74.72% | NI系列全部映射 |
| Batch-7 | 133+14=147 | 82.58% | ≥80%目标达成 ✅ |
| Batch-8 | 147+16=163 | 91.57% | SI系列全部映射 |
| Batch-9 | 163+15=178 | 100% | LI系列全部映射 |

---

## 2. 9批次拆分总览

| 批次 | 优先级 | 品种 | 条目数 | 映射方法 | 预计完成 | 责任人 |
|------|--------|------|--------|---------|---------|--------|
| Batch-1 | P0 | PB/CU/ZN | 9 | 计算推导+API搜索 | 2026-10-13 | DSHB团队 |
| Batch-2 | P1/P2 | PB | 28 | API搜索+计算推导 | 2026-10-13 | DSHB团队 |
| Batch-3 | P1 | CU | 23 | API搜索+计算推导 | 2026-10-13 | DSHB团队 |
| Batch-4 | P1 | ZN | 22 | API搜索+计算推导 | 2026-10-13 | DSHB团队 |
| Batch-5 | P1 | AL | 25 | API搜索+计算推导 | 2026-10-13 | DSHB团队 |
| Batch-6 | P2 | NI | 18 | API搜索+人工确认 | 2026-10-14 | DSHB+DSHE |
| Batch-7 | P2 | SN | 14 | API搜索+人工确认 | 2026-10-14 | DSHB+DSHE |
| Batch-8 | P2 | SI | 16 | API搜索+人工确认 | 2026-10-15 | DSHB+DSHE |
| Batch-9 | P2 | LI | 15 | API搜索+人工确认 | 2026-10-16 | DSHB+DSHE |
| **合计** | — | **8品种** | **170** | — | **2026-10-16** | — |

### 2.1 品种分布

| 品种 | COMPLETED | PENDING | 批次覆盖 | 映射后完成 |
|------|-----------|---------|---------|-----------|
| PB (铅) | 6 | 31 | Batch-1(3)+Batch-2(28) | 37/37 ✅ |
| CU (铜) | 1 | 27 | Batch-1(4)+Batch-3(23) | 28/28 ✅ |
| ZN (锌) | 1 | 24 | Batch-1(2)+Batch-4(22) | 25/25 ✅ |
| AL (铝) | 0 | 25 | Batch-5(25) | 25/25 ✅ |
| NI (镍) | 0 | 18 | Batch-6(18) | 18/18 ✅ |
| SN (锡) | 0 | 14 | Batch-7(14) | 14/14 ✅ |
| SI (硅) | 0 | 16 | Batch-8(16) | 16/16 ✅ |
| LI (锂) | 0 | 15 | Batch-9(15) | 15/15 ✅ |
| **合计** | **8** | **170** | **170** | **178/178 ✅** |

---

## 3. Batch-1: P0核心指标 (9项)

### 3.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-1 |
| 优先级 | P0 (最高) |
| 条目数 | 9 |
| 品种覆盖 | PB(3), CU(4), ZN(2) |
| 映射方法 | 计算推导(1项) + API搜索(8项) |
| 负责人 | DSHB团队 |
| 截止时间 | 2026-10-13 |

### 3.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 | 映射详情 |
|---|-----------|--------|---------|------|---------|---------|
| 1 | PB-011 | lead_total_inv | 铅锭总库存 | ton | 计算推导 | = lead_social_inv + lead_exchange_inv |
| 2 | PB-012 | lead_lme_inv | 铅锭LME库存 | ton | API搜索 | "LME 铅 库存" |
| 3 | PB-013 | lead_shfe_inv | 铅锭上期所库存 | ton | API搜索 | "上期所 铅 库存 仓单" |
| 4 | CU-004 | cu_tc | 铜精矿TC加工费 | USD/dmt | API搜索 | "铜精矿 TC 加工费" |
| 5 | CU-005 | cu_social_inv | 电解铜社会库存 | ton | API搜索 | "电解铜 社会库存" |
| 6 | CU-006 | cu_exchange_inv | 电解铜交易所库存 | ton | API搜索 | "电解铜 交易所库存 上期所" |
| 7 | CU-007 | cu_rod_rate | 铜杆开工率 | % | API搜索 | "铜杆 开工率" |
| 8 | ZN-002 | zn_social_inv | 锌锭社会库存 | ton | API搜索 | "锌锭 社会库存" |
| 9 | ZN-003 | zn_tc | 锌精矿TC加工费 | USD/dmt | API搜索 | "锌精矿 TC 加工费" |

### 3.3 验收标准

```
Batch-1验收标准:
  ✅ 9/9项映射完成 (COMPLETED)
  ✅ API搜索命中率 ≥8/9 (计算推导1项豁免)
  ✅ 所有API搜索结果数据非空
  ✅ 底层口径校验通过 (单位/公式/统计口径)
  ✅ DSHE抽样验证通过 (30%=3项抽样)
  ✅ 桥接表V2更新 (新增9项COMPLETED)
  ✅ 批次日志生成
```

---

## 4. Batch-2: P1/P2 PB扩展 (28项)

### 4.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-2 |
| 优先级 | P1(12项) + P2(16项) |
| 条目数 | 28 |
| 品种覆盖 | PB(28) |
| 映射方法 | API搜索(22项) + 计算推导(6项) |
| 负责人 | DSHB团队 |
| 截止时间 | 2026-10-13 |

### 4.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | PB-002 | lead_open_interest | 沪铅期货持仓量 | lot | API搜索 |
| 2 | PB-003 | lead_volume | 沪铅期货成交量 | lot | API搜索 |
| 3 | PB-004 | lead_settlement | 沪铅期货结算价 | CNY/ton | API搜索 |
| 4 | PB-005 | lead_bid_ask_spread | 沪铅买卖价差 | CNY/ton | API搜索 |
| 5 | PB-006 | lead_monthly_spread | 沪铅月价差 | CNY/ton | API搜索 |
| 6 | PB-007 | lead_basis | 沪铅期现价差 | CNY/ton | API搜索 |
| 7 | PB-014 | lead_inv_change | 铅锭库存变动 | ton | 计算推导 |
| 8 | PB-016 | lead_consume | 铅锭消费量 | ton | API搜索 |
| 9 | PB-018 | lead_export | 铅锭出口量 | ton | API搜索 |
| 10 | PB-019 | lead_import | 铅锭进口量 | ton | API搜索 |
| 11 | PB-020 | lead_net_export | 铅锭净出口 | ton | 计算推导 |
| 12 | PB-021 | lead_stock_cover_days | 铅锭库存覆盖天数 | day | 计算推导 |
| 13 | PB-022 | lead_ore_price | 铅精矿价格 | CNY/ton | API搜索 |
| 14 | PB-023 | lead_conc_price_silver | 铅精矿价格(含银) | CNY/ton | API搜索 |
| 15 | PB-024 | lead_smelt_cost | 电解铅冶炼成本 | CNY/ton | API搜索 |
| 16 | PB-025 | lead_metal_cost | 铅金属成本 | CNY/ton | 计算推导 |
| 17 | PB-026 | lead_battery_cost | 铅酸电池成本 | CNY/kWh | API搜索 |
| 18 | PB-027 | lead_battery_price | 铅酸电池价格 | CNY/kWh | API搜索 |
| 19 | PB-028 | lead_battery_profit | 铅酸电池利润 | CNY/kWh | 计算推导 |
| 20 | PB-029 | lead_battery_util | 铅酸电池开工率 | % | API搜索 |
| 21 | PB-030 | lead_battery_output | 铅酸电池产量 | ton | API搜索 |
| 22 | PB-031 | lead_plate_price | 铅板价格 | CNY/ton | API搜索 |
| 23 | PB-032 | lead_pipe_price | 铅管价格 | CNY/ton | API搜索 |
| 24 | PB-033 | lead_sheet_price | 铅板卷价格 | CNY/ton | API搜索 |
| 25 | PB-034 | lead_cable_price | 铅电缆价格 | CNY/ton | API搜索 |
| 26 | PB-035 | lead_balance | 铅供需平衡 | ton | 计算推导 |
| 27 | PB-036 | lead_apparent_consume | 铅表观消费 | ton | 计算推导 |
| 28 | PB-037 | lead_balance_table | 铅供需平衡表 | ton/JSON | 计算推导 |

### 4.3 验收标准

```
Batch-2验收标准:
  ✅ 28/28项映射完成
  ✅ API搜索命中率 ≥22/28 (计算推导6项豁免)
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=9项抽样)
  ✅ PB系列全品种映射完成
```

---

## 5. Batch-3: P1 CU扩展 (23项)

### 5.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-3 |
| 优先级 | P1 |
| 条目数 | 23 |
| 品种覆盖 | CU(23) |
| 映射方法 | API搜索(14项) + 计算推导(9项) |
| 负责人 | DSHB团队 |
| 截止时间 | 2026-10-13 |

### 5.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | CU-002 | cu_open_interest | 沪铜期货持仓量 | lot | API搜索 |
| 2 | CU-003 | cu_volume | 沪铜期货成交量 | lot | API搜索 |
| 3 | CU-008 | cu_wire_rate | 铜线开工率 | % | API搜索 |
| 4 | CU-009 | cu_sheet_rate | 铜板开工率 | % | API搜索 |
| 5 | CU-010 | cu_pipe_rate | 铜管开工率 | % | API搜索 |
| 6 | CU-011 | cu_wire_profit | 铜线利润 | CNY/ton | API搜索 |
| 7 | CU-012 | cu_sheet_profit | 铜板利润 | CNY/ton | API搜索 |
| 8 | CU-013 | cu_pipe_profit | 铜管利润 | CNY/ton | API搜索 |
| 9 | CU-014 | cu_ore_price | 铜精矿价格 | USD/lb | API搜索 |
| 10 | CU-015 | cu_import_cost | 铜进口成本 | CNY/ton | 计算推导 |
| 11 | CU-016 | cu_consume | 铜消费量 | ton | API搜索 |
| 12 | CU-017 | cu_export | 铜出口量 | ton | API搜索 |
| 13 | CU-018 | cu_import | 铜进口量 | ton | API搜索 |
| 14 | CU-019 | cu_net_export | 铜净出口 | ton | 计算推导 |
| 15 | CU-020 | cu_balance | 铜供需平衡 | ton | 计算推导 |
| 16 | CU-021 | cu_apparent_consume | 铜表观消费 | ton | 计算推导 |
| 17 | CU-022 | cu_tc_change | 铜TC变动 | USD/dmt | 计算推导 |
| 18 | CU-023 | cu_inventory_ratio | 铜库存比率 | % | 计算推导 |
| 19 | CU-024 | cu_monthly_spread | 沪铜月差 | CNY/ton | API搜索 |
| 20 | CU-025 | cu_basis | 沪铜期现价差 | CNY/ton | API搜索 |
| 21 | CU-026 | cu_smelt_profit | 电解铜冶炼利润 | CNY/ton | 计算推导 |
| 22 | CU-027 | cu_balance_table | 铜供需平衡表 | ton/JSON | 计算推导 |
| 23 | CU-028 | cu_price_spread_lme_shfe | 铜LME-SHFE价差 | CNY/ton | API搜索 |

### 5.3 验收标准

```
Batch-3验收标准:
  ✅ 23/23项映射完成
  ✅ API搜索命中率 ≥14/23
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=7项抽样)
  ✅ CU系列全品种映射完成
```

---

## 6. Batch-4: P1 ZN扩展 (22项)

### 6.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-4 |
| 优先级 | P1 |
| 条目数 | 22 |
| 品种覆盖 | ZN(22) |
| 映射方法 | API搜索(12项) + 计算推导(10项) |
| 负责人 | DSHB团队 |
| 截止时间 | 2026-10-13 |

### 6.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | ZN-004 | zn_open_interest | 沪锌期货持仓量 | lot | API搜索 |
| 2 | ZN-005 | zn_volume | 沪锌期货成交量 | lot | API搜索 |
| 3 | ZN-006 | zn_wire_rate | 锌线开工率 | % | API搜索 |
| 4 | ZN-007 | zn_plate_rate | 锌板开工率 | % | API搜索 |
| 5 | ZN-008 | zn_pipe_rate | 锌管开工率 | % | API搜索 |
| 6 | ZN-009 | zn_export | 锌出口量 | ton | API搜索 |
| 7 | ZN-010 | zn_import | 锌进口量 | ton | API搜索 |
| 8 | ZN-011 | zn_net_export | 锌净出口 | ton | 计算推导 |
| 9 | ZN-012 | zn_consume | 锌消费量 | ton | API搜索 |
| 10 | ZN-013 | zn_balance | 锌供需平衡 | ton | 计算推导 |
| 11 | ZN-014 | zn_apparent_consume | 锌表观消费 | ton | 计算推导 |
| 12 | ZN-015 | zn_exchange_inv | 锌锭交易所库存 | ton | API搜索 |
| 13 | ZN-016 | zn_ore_price | 锌精矿价格 | CNY/ton | API搜索 |
| 14 | ZN-017 | zn_smelt_cost | 电解锌冶炼成本 | CNY/ton | API搜索 |
| 15 | ZN-018 | zn_smelt_profit | 电解锌冶炼利润 | CNY/ton | 计算推导 |
| 16 | ZN-019 | zn_tc_change | 锌TC变动 | USD/dmt | 计算推导 |
| 17 | ZN-020 | zn_inventory_ratio | 锌库存比率 | % | 计算推导 |
| 18 | ZN-021 | zn_monthly_spread | 沪锌月差 | CNY/ton | API搜索 |
| 19 | ZN-022 | zn_basis | 沪锌期现价差 | CNY/ton | API搜索 |
| 20 | ZN-023 | zn_balance_table | 锌供需平衡表 | ton/JSON | 计算推导 |
| 21 | ZN-024 | zn_lme_inv | 锌锭LME库存 | ton | API搜索 |
| 22 | ZN-025 | zn_warehouse_inv | 锌锭仓单库存 | ton | API搜索 |

### 6.3 验收标准

```
Batch-4验收标准:
  ✅ 22/22项映射完成
  ✅ API搜索命中率 ≥12/22
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=7项抽样)
  ✅ ZN系列全品种映射完成
```

---

## 7. Batch-5: P1 AL全模块 (25项)

### 7.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-5 |
| 优先级 | P1 |
| 条目数 | 25 |
| 品种覆盖 | AL(25) |
| 映射方法 | API搜索(20项) + 计算推导(5项) |
| 负责人 | DSHB团队 |
| 截止时间 | 2026-10-13 |

### 7.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | AL-001 | al_close | 沪铝期货收盘价 | CNY/ton | API搜索 |
| 2 | AL-002 | al_open_interest | 沪铝期货持仓量 | lot | API搜索 |
| 3 | AL-003 | al_volume | 沪铝期货成交量 | lot | API搜索 |
| 4 | AL-004 | al_social_inv | 电解铝社会库存 | ton | API搜索 |
| 5 | AL-005 | al_exchange_inv | 电解铝交易所库存 | ton | API搜索 |
| 6 | AL-006 | al_electrolysis | 电解铝产量 | ton | API搜索 |
| 7 | AL-007 | al_ore_price | 铝土矿价格 | USD/ton | API搜索 |
| 8 | AL-008 | al_smelt_cost | 电解铝冶炼成本 | CNY/ton | API搜索 |
| 9 | AL-009 | al_smelt_profit | 电解铝冶炼利润 | CNY/ton | 计算推导 |
| 10 | AL-010 | al_consume | 铝消费量 | ton | API搜索 |
| 11 | AL-011 | al_export | 铝出口量 | ton | API搜索 |
| 12 | AL-012 | al_import | 铝进口量 | ton | API搜索 |
| 13 | AL-013 | al_net_export | 铝净出口 | ton | 计算推导 |
| 14 | AL-014 | al_balance | 铝供需平衡 | ton | 计算推导 |
| 15 | AL-015 | al_apparent_consume | 铝表观消费 | ton | 计算推导 |
| 16 | AL-016 | al_lme_inv | 铝LME库存 | ton | API搜索 |
| 17 | AL-017 | al_monthly_spread | 沪铝月差 | CNY/ton | API搜索 |
| 18 | AL-018 | al_basis | 沪铝期现价差 | CNY/ton | API搜索 |
| 19 | AL-019 | al_inventory_ratio | 铝库存比率 | % | 计算推导 |
| 20 | AL-020 | al_balance_table | 铝供需平衡表 | ton/JSON | 计算推导 |
| 21 | AL-021 | al_power_consume | 铝电力消费 | kWh/ton | API搜索 |
| 22 | AL-022 | al_ore_grade | 铝土矿品位 | % | API搜索 |
| 23 | AL-023 | al_ingot_price | 铝锭价格 | CNY/ton | API搜索 |
| 24 | AL-024 | al_profile_price | 铝型材价格 | CNY/ton | API搜索 |
| 25 | AL-025 | al_util_rate | 电解铝开工率 | % | API搜索 |

### 7.3 验收标准

```
Batch-5验收标准:
  ✅ 25/25项映射完成
  ✅ API搜索命中率 ≥20/25
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=8项抽样)
  ✅ AL系列全品种映射完成
```

---

## 8. Batch-6: P2 NI全模块 (18项)

### 8.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-6 |
| 优先级 | P2 |
| 条目数 | 18 |
| 品种覆盖 | NI(18) |
| 映射方法 | API搜索(12项) + 计算推导(6项) |
| 负责人 | DSHB+DSHE联合 |
| 截止时间 | 2026-10-14 |

### 8.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | NI-001 | ni_close | 沪镍期货收盘价 | CNY/ton | API搜索 |
| 2 | NI-002 | ni_open_interest | 沪镍期货持仓量 | lot | API搜索 |
| 3 | NI-003 | ni_volume | 沪镍期货成交量 | lot | API搜索 |
| 4 | NI-004 | ni_social_inv | 镍社会库存 | ton | API搜索 |
| 5 | NI-005 | ni_exchange_inv | 镍交易所库存 | ton | API搜索 |
| 6 | NI-006 | ni_production | 镍产量 | ton | API搜索 |
| 7 | NI-007 | ni_consume | 镍消费量 | ton | API搜索 |
| 8 | NI-008 | ni_export | 镍出口量 | ton | API搜索 |
| 9 | NI-009 | ni_import | 镍进口量 | ton | API搜索 |
| 10 | NI-010 | ni_net_export | 镍净出口 | ton | 计算推导 |
| 11 | NI-011 | ni_balance | 镍供需平衡 | ton | 计算推导 |
| 12 | NI-012 | ni_apparent_consume | 镍表观消费 | ton | 计算推导 |
| 13 | NI-013 | ni_lme_inv | 镍LME库存 | ton | API搜索 |
| 14 | NI-014 | ni_smelt_cost | 镍冶炼成本 | CNY/ton | API搜索 |
| 15 | NI-015 | ni_smelt_profit | 镍冶炼利润 | CNY/ton | 计算推导 |
| 16 | NI-016 | ni_monthly_spread | 沪镍月差 | CNY/ton | API搜索 |
| 17 | NI-017 | ni_basis | 沪镍期现价差 | CNY/ton | API搜索 |
| 18 | NI-018 | ni_balance_table | 镍供需平衡表 | ton/JSON | 计算推导 |

### 8.3 验收标准

```
Batch-6验收标准:
  ✅ 18/18项映射完成
  ✅ API搜索命中率 ≥12/18
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=6项抽样)
  ✅ NI系列全品种映射完成
```

---

## 9. Batch-7: P2 SN全模块 (14项)

### 9.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-7 |
| 优先级 | P2 |
| 条目数 | 14 |
| 品种覆盖 | SN(14) |
| 映射方法 | API搜索(9项) + 计算推导(5项) |
| 负责人 | DSHB+DSHE联合 |
| 截止时间 | 2026-10-14 |

### 9.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | SN-001 | sn_close | 沪锡期货收盘价 | CNY/ton | API搜索 |
| 2 | SN-002 | sn_open_interest | 沪锡期货持仓量 | lot | API搜索 |
| 3 | SN-003 | sn_volume | 沪锡期货成交量 | lot | API搜索 |
| 4 | SN-004 | sn_social_inv | 锡社会库存 | ton | API搜索 |
| 5 | SN-005 | sn_production | 锡产量 | ton | API搜索 |
| 6 | SN-006 | sn_consume | 锡消费量 | ton | API搜索 |
| 7 | SN-007 | sn_export | 锡出口量 | ton | API搜索 |
| 8 | SN-008 | sn_import | 锡进口量 | ton | API搜索 |
| 9 | SN-009 | sn_net_export | 锡净出口 | ton | 计算推导 |
| 10 | SN-010 | sn_balance | 锡供需平衡 | ton | 计算推导 |
| 11 | SN-011 | sn_apparent_consume | 锡表观消费 | ton | 计算推导 |
| 12 | SN-012 | sn_lme_inv | 锡LME库存 | ton | API搜索 |
| 13 | SN-013 | sn_smelt_cost | 锡冶炼成本 | CNY/ton | API搜索 |
| 14 | SN-014 | sn_smelt_profit | 锡冶炼利润 | CNY/ton | 计算推导 |

### 9.3 验收标准

```
Batch-7验收标准:
  ✅ 14/14项映射完成
  ✅ API搜索命中率 ≥9/14
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=5项抽样)
  ✅ SN系列全品种映射完成
  ✅ 有效桥接率首次突破80%目标!
```

---

## 10. Batch-8: P2 SI全模块 (16项)

### 10.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-8 |
| 优先级 | P2 |
| 条目数 | 16 |
| 品种覆盖 | SI(16) |
| 映射方法 | API搜索(11项) + 计算推导(5项) |
| 负责人 | DSHB+DSHE联合 |
| 截止时间 | 2026-10-15 |

### 10.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | SI-001 | si_close | 工业硅期货收盘价 | CNY/ton | API搜索 |
| 2 | SI-002 | si_open_interest | 工业硅期货持仓量 | lot | API搜索 |
| 3 | SI-003 | si_volume | 工业硅期货成交量 | lot | API搜索 |
| 4 | SI-004 | si_inventory | 工业硅库存 | ton | API搜索 |
| 5 | SI-005 | si_production | 工业硅产量 | ton | API搜索 |
| 6 | SI-006 | si_consume | 工业硅消费量 | ton | API搜索 |
| 7 | SI-007 | si_export | 工业硅出口量 | ton | API搜索 |
| 8 | SI-008 | si_import | 工业硅进口量 | ton | API搜索 |
| 9 | SI-009 | si_net_export | 工业硅净出口 | ton | 计算推导 |
| 10 | SI-010 | si_balance | 工业硅供需平衡 | ton | 计算推导 |
| 11 | SI-011 | si_apparent_consume | 工业硅表观消费 | ton | 计算推导 |
| 12 | SI-012 | si_ore_price | 硅石价格 | CNY/ton | API搜索 |
| 13 | SI-013 | si_power_consume | 工业硅电力消费 | kWh/ton | API搜索 |
| 14 | SI-014 | si_monthly_spread | 工业硅月差 | CNY/ton | API搜索 |
| 15 | SI-015 | si_basis | 工业硅期现价差 | CNY/ton | API搜索 |
| 16 | SI-016 | si_balance_table | 工业硅供需平衡表 | ton/JSON | 计算推导 |

### 10.3 验收标准

```
Batch-8验收标准:
  ✅ 16/16项映射完成
  ✅ API搜索命中率 ≥11/16
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=5项抽样)
  ✅ SI系列全品种映射完成
```

---

## 11. Batch-9: P2 LI全模块 (15项)

### 11.1 批次定义

| 维度 | 值 |
|------|-----|
| 批次号 | Batch-9 |
| 优先级 | P2 |
| 条目数 | 15 |
| 品种覆盖 | LI(15) |
| 映射方法 | API搜索(10项) + 计算推导(5项) |
| 负责人 | DSHB+DSHE联合 |
| 截止时间 | 2026-10-16 |

### 11.2 指标清单

| # | DSHE指标ID | 语义ID | 指标名称 | 单位 | 映射方法 |
|---|-----------|--------|---------|------|---------|
| 1 | LI-001 | li_close | 碳酸锂期货收盘价 | CNY/ton | API搜索 |
| 2 | LI-002 | li_open_interest | 碳酸锂期货持仓量 | lot | API搜索 |
| 3 | LI-003 | li_volume | 碳酸锂期货成交量 | lot | API搜索 |
| 4 | LI-004 | li_social_inv | 碳酸锂社会库存 | ton | API搜索 |
| 5 | LI-005 | li_production | 碳酸锂产量 | ton | API搜索 |
| 6 | LI-006 | li_consume | 碳酸锂消费量 | ton | API搜索 |
| 7 | LI-007 | li_export | 碳酸锂出口量 | ton | API搜索 |
| 8 | LI-008 | li_import | 碳酸锂进口量 | ton | API搜索 |
| 9 | LI-009 | li_net_export | 碳酸锂净出口 | ton | 计算推导 |
| 10 | LI-010 | li_balance | 碳酸锂供需平衡 | ton | 计算推导 |
| 11 | LI-011 | li_apparent_consume | 碳酸锂表观消费 | ton | 计算推导 |
| 12 | LI-012 | li_ore_price | 锂矿石价格 | USD/ton | API搜索 |
| 13 | LI-013 | li_monthly_spread | 碳酸锂月差 | CNY/ton | API搜索 |
| 14 | LI-014 | li_basis | 碳酸锂期现价差 | CNY/ton | API搜索 |
| 15 | LI-015 | li_balance_table | 碳酸锂供需平衡表 | ton/JSON | 计算推导 |

### 11.3 验收标准

```
Batch-9验收标准:
  ✅ 15/15项映射完成
  ✅ API搜索命中率 ≥10/15
  ✅ 底层口径校验通过
  ✅ DSHE抽样验证通过 (30%=5项抽样)
  ✅ LI系列全品种映射完成
  ✅ 全量170项PENDING条目处理完毕!
```

---

## 12. 映射方法与策略

### 12.1 四种映射策略

| 策略 | 适用场景 | 数量 | 说明 |
|------|---------|------|------|
| 计算推导 | 可从已确认指标计算的派生指标 | 47项 | 净出口、供需平衡、表观消费、库存变动等 |
| API搜索 | zhiji数据源有直接对应数据的指标 | 112项 | 通过search API匹配语义ID关键词 |
| 批量搜索 | 按品种批量匹配的指标 | — | 作为API搜索的补充策略 |
| 人工确认 | 需DSHE/DSHB联合确认的歧义项 | 11项 | LI/SI/NI特殊数据源 |

### 12.2 映射自动化脚本

```
映射脚本: id_mapping_full_script.py
路径: analysis/e2e_output/v86/dshb_gate_prod_fix/
功能:
  1. 170项PENDING条目定义 (含搜索关键词)
  2. zhiji search API调用 (限频1s)
  3. zhiji series API验证
  4. 计算推导指标自动生成
  5. 批次日志生成
  6. 汇总JSON生成
```

### 12.3 映射质量保障

```
映射质量保障:
  1. API搜索匹配阈值: score≥6 (A级)
  2. 低分项: score<6 标记为PENDING_MANUAL
  3. 无结果项: 标记为PENDING_NO_MATCH
  4. 计算推导项: 公式验证+边界检查
  5. 每批次DSHE抽样验证 (30%)
```

---

## 13. 验收标准

### 13.1 单批次验收

| 验收项 | 标准 |
|--------|------|
| 映射完成率 | 100% (COMPLETED) |
| API搜索命中率 | ≥批次条目数 (计算推导豁免) |
| 底层口径校验 | 公式/单位/统计口径一致 |
| DSHE抽样验证 | 30%抽样全部PASS |
| 桥接表更新 | V2版本同步更新 |
| 批次日志 | JSON日志+统计汇总 |

### 13.2 全量验收

| 验收项 | 标准 | 目标 |
|--------|------|------|
| 有效桥接率 | ≥80% | 178/178=100% |
| COMPLETED总数 | ≥143 | 178 |
| DSHE抽样验证 | 全部PASS | 全部 |
| 风险台账 | 全部更新 | 22项 |
| 产物入库 | 全部提交远端 | 全部 |
| 约束合规 | 4/4合规 | 全部 |

---

## 14. 约束合规声明

| 约束 | 要求 | 实际 | 状态 |
|------|------|------|------|
| NO_ZHIJI_API_CALL | FALSE (允许调用) | 允许调用 | ✅ 合规 |
| NO_MODIFY_V85 | TRUE (禁止修改) | 未修改V85 | ✅ 合规 |
| NO_OVERWRITE | TRUE (禁止覆盖) | 新增文件+迭代更新V2 | ✅ 合规 |
| BRANCH_LOCKED | TRUE (锁定分支) | feature/v85-chart-template | ✅ 合规 |

---

> **文档生成**: 2026-10-13
> **任务**: DSHB_V86_RC2_ID_MAPPING_FULL_T3.1
> **分支**: `feature/v85-chart-template`
> **状态**: ✅ **FINAL — 9批次映射执行计划, 170项PENDING条目全量覆盖, 目标有效桥接率≥80%**
