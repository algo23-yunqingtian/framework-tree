# DSHB V86-RC2 投产阶段 — 双向ID桥接映射对照表 V2 (修正版)

> **工单**: DSHB_V86_RC2_PROD_FIX_T3.3
> **分支**: `feature/v85-chart-template` (BRANCH_LOCKED=TRUE)
> **执行日期**: 2026-10-12
> **修正基线**: V86_RC2_PREP_CLOSED=TRUE, DSHB_PROD_PHASE_STAGE3_DONE=TRUE, DSHB_PROD_PHASE_STAGE4_DONE=TRUE
> **HERMES审计编号**: R-AUDIT-02 (桥接表统计口径误导)
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **跨团队同步**: DSHE, HERMES
> **文档状态**: FINAL — 修正Stage3桥接表统计口径, COMPLETED/PENDING分离, 真实有效桥接率=4.5% (8/178), PENDING条目映射计划已制定

---

## 目录

1. [修正说明](#1-修正说明)
2. [V2核心统计](#2-v2核心统计)
3. [COMPLETED条目清单](#3-completed条目清单)
4. [PENDING条目清单](#4-pending条目清单)
5. [回填字段映射](#5-回填字段映射)
6. [真实有效桥接率计算](#6-真实有效桥接率计算)
7. [Stage3统计口径修正对照](#7-stage3统计口径修正对照)
8. [PENDING条目映射计划](#8-pending条目映射计划)
9. [DSHE语义ID对齐说明](#9-dshe语义id对齐说明)
10. [约束合规声明](#10-约束合规声明)

---

## 1. 修正说明

### 1.1 修正原因

| 审计编号 | 问题描述 | Stage3原状态 | V2修正 |
|---------|---------|-------------|--------|
| R-AUDIT-02 | 将PENDING待映射条目计入100%覆盖率 | 197/197 (100%) 名义覆盖 | **8/178 (4.5%) 真实有效** |
| — | PENDING条目计入有效映射 | TO_BE_CONFIRMED计入100% | **PENDING不计入有效映射** |
| — | 无COMPLETED/PENDING分离 | 单一状态字段 | **新增status字段: COMPLETED/PENDING** |
| — | 语义ID定义不一致 | lead_social_inv vs gmv_daily_avg | **统一语义ID定义规范** |

### 1.2 修正原则

```
修正原则:
  ✅ COMPLETED = 已完成映射 = 有明确的zhiji短ID + zhiji长ID + DSHE语义ID
  ✅ PENDING   = 待映射 = zhiji短ID或长ID为TO_BE_CONFIRMED
  ✅ 有效桥接率 = COMPLETED数 / 总指标数 (不含回填字段)
  ✅ PENDING条目不计入有效桥接率
  ✅ 回填字段不计入指标映射率统计 (独立统计)
```

---

## 2. V2核心统计

### 2.1 总体统计

| 维度 | 数量 | 占比 | 说明 |
|------|------|------|------|
| **总映射条目** | **197** | 100% | 178指标 + 19回填字段 |
| **CONFIRMED (COMPLETED)** | **8** | 4.06% | 已完成全部映射 |
| **PENDING** | **170** | 86.30% | 待映射 |
| **MAPPED (回填)** | **19** | 9.64% | 回填字段映射完成 |
| **真实有效桥接率** | **4.49%** | — | 8/178 (仅指标) |
| **含回填总映射率** | **15.23%** | — | 27/178 |

### 2.2 品种分布

| 品种 | 指标总数 | COMPLETED | PENDING | 完成率 | 状态 |
|------|---------|-----------|---------|--------|------|
| PB (铅) | 37 | 6 | 31 | 16.2% | 🟡 部分完成 |
| CU (铜) | 28 | 1 | 27 | 3.6% | 🟡 部分完成 |
| AL (铝) | 25 | 0 | 25 | 0% | 🔴 未完成 |
| ZN (锌) | 25 | 1 | 24 | 4.0% | 🟡 部分完成 |
| NI (镍) | 18 | 0 | 18 | 0% | 🔴 未完成 |
| SN (锡) | 14 | 0 | 14 | 0% | 🔴 未完成 |
| SI (工业硅) | 16 | 0 | 16 | 0% | 🔴 未完成 |
| LI (锂) | 15 | 0 | 15 | 0% | 🔴 未完成 |
| 回填字段 | 19 | 19 | 0 | 100% | ✅ 已完成 |
| **合计** | **197** | **27** | **170** | **13.7%** | 🟡 |

### 2.3 已知ID汇总

| ID类型 | 数量 | 状态 |
|--------|------|------|
| 已确认短ID (zhiji short) | 7 | i3, i4, i1, i2, j25_tc, i5, i6, i7 |
| 已确认长ID (zhiji long) | 8 | ID02226332~ID02226339 |
| DSHE语义ID (已确认) | 8 | 8项CONFIRMED对应 |
| DSHE指标ID (已确认) | 8 | 8项CONFIRMED对应 |

---

## 3. COMPLETED条目清单

### 3.1 COMPLETED映射详情 (8项)

| # | DSHE指标ID | zhiji短ID | zhiji长ID | DSHE语义ID | 指标名称 | 单位 | API系列ID | 状态 |
|---|-----------|----------|----------|-----------|---------|------|----------|------|
| 1 | PB-001 | i3 | ID02226332 | shfe_lead_close | 沪铅期货收盘价 | CNY/ton | a10022001 | ✅ COMPLETED |
| 2 | PB-008 | i4 | ID02226333 | lead_ore_spot | 铅锭现货价格 | CNY/ton | a10022002 | ✅ COMPLETED |
| 3 | PB-009 | i1 | ID02226334 | lead_social_inv | 铅锭社会库存 | ton | a10022003 | ✅ COMPLETED |
| 4 | PB-010 | i2 | ID02226335 | lead_exchange_inv | 铅锭交易所库存 | ton | a10022004 | ✅ COMPLETED |
| 5 | PB-015 | j25_tc | ID02226336 | lead_tc | 铅精矿TC加工费 | USD/dmt | a10021355 | ✅ COMPLETED |
| 6 | PB-017 | i5 | ID02226337 | lead_production | 电解铅产量 | ton | a10022005 | ✅ COMPLETED |
| 7 | CU-001 | i6 | ID02226338 | shfe_cu_close | 沪铜期货收盘价 | CNY/ton | a10022006 | ✅ COMPLETED |
| 8 | ZN-001 | i7 | ID02226339 | shfe_zn_close | 沪锌期货收盘价 | CNY/ton | a10022007 | ✅ COMPLETED |

### 3.2 COMPLETED条目特征

```
COMPLETED条目特征:
  ✅ 全部有明确的zhiji短ID (非TO_BE_CONFIRMED)
  ✅ 全部有明确的zhiji长ID (非TO_BE_CONFIRMED)
  ✅ 全部有DSHE语义ID
  ✅ 全部有DSHE指标ID
  ✅ 全部已通过API调用验证 (或历史确认)
  ✅ 全部有对应API系列ID (可调用)
```

---

## 4. PENDING条目清单

### 4.1 PENDING条目统计

| 维度 | 数量 | 说明 |
|------|------|------|
| 总PENDING条目 | 170 | 占全部指标178的95.5% |
| 缺少短ID | 170 | 全部为TO_BE_CONFIRMED |
| 缺少长ID | 170 | 全部为TO_BE_CONFIRMED |
| 有语义ID | 170 | 语义ID已预定义 |
| 有指标ID | 170 | 指标ID已预定义 |
| 可搜索映射 | 170 | 可通过zhiji API搜索匹配 |

### 4.2 PENDING条目按品种分布

| 品种 | PENDING数 | 占比 | 映射难度 |
|------|----------|------|---------|
| PB (铅) | 31 | 18.2% | 🟡 中等 (有3个已知短ID可参考) |
| CU (铜) | 27 | 15.9% | 🟡 中等 (有1个已知短ID可参考) |
| AL (铝) | 25 | 14.7% | 🟠 较高 (无已知短ID参考) |
| ZN (锌) | 24 | 14.1% | 🟡 中等 (有1个已知短ID可参考) |
| NI (镍) | 18 | 10.6% | 🟠 较高 |
| SN (锡) | 14 | 8.2% | 🟠 较高 |
| SI (工业硅) | 16 | 9.4% | 🟠 较高 |
| LI (锂) | 15 | 8.8% | 🔴 高 (数据源有限) |
| **合计** | **170** | **100%** | — |

### 4.3 PENDING条目优先级排序

| 优先级 | 条目 | 理由 | 数量 |
|--------|------|------|------|
| P0 | PB-011~PB-013 (铅库存系列) | 核心指标, 与已确认i1/i2强关联 | 3 |
| P0 | CU-004~CU-007 (铜核心指标) | TC/库存/开工率, 关键指标 | 4 |
| P0 | ZN-002~ZN-003 (锌库存/TC) | 关键指标, 与已知i7强关联 | 2 |
| P1 | PB-016~PB-020, PB-023~PB-030 | PB系列扩展 | 15 |
| P1 | CU-005~CU-028 (除已确认) | CU系列扩展 | 23 |
| P1 | ZN-004~ZN-025 (除已确认) | ZN系列扩展 | 22 |
| P1 | AL-001~AL-025 | AL全模块 | 25 |
| P2 | NI-001~NI-018 | NI全模块 | 18 |
| P2 | SN-001~SN-014 | SN全模块 | 14 |
| P2 | SI-001~SI-016 | SI全模块 | 16 |
| P2 | LI-001~LI-015 | LI全模块 | 15 |
| **合计** | **P0: 9, P1: 85, P2: 76** | **170** | — |

### 4.4 PENDING条目明细 (节选 — P0优先级)

| # | DSHE指标ID | DSHE语义ID | 指标名称 | 数据类型 | 单位 | 映射计划 |
|---|-----------|-----------|---------|---------|------|---------|
| 1 | PB-011 | lead_total_inv | 铅锭总库存 | INTEGER | ton | 计算值: lead_social_inv + lead_exchange_inv |
| 2 | PB-012 | lead_lme_inv | 铅锭LME库存 | INTEGER | ton | API搜索: "LME铅库存" |
| 3 | PB-013 | lead_shfe_inv | 铅锭上期所库存 | INTEGER | ton | API搜索: "上期所铅库存" |
| 4 | CU-004 | cu_tc | 铜精矿TC加工费 | FLOAT | USD/dmt | API搜索: "铜精矿 TC 加工费" |
| 5 | CU-005 | cu_social_inv | 电解铜社会库存 | INTEGER | ton | API搜索: "电解铜 社会库存" |
| 6 | CU-006 | cu_exchange_inv | 电解铜交易所库存 | INTEGER | ton | API搜索: "电解铜 交易所库存" |
| 7 | CU-007 | cu_rod_rate | 铜杆开工率 | FLOAT | % | API搜索: "铜杆 开工率" |
| 8 | ZN-002 | zn_social_inv | 锌锭社会库存 | INTEGER | ton | API搜索: "锌锭 社会库存" |
| 9 | ZN-003 | zn_tc | 锌精矿TC加工费 | FLOAT | USD/dmt | API搜索: "锌精矿 TC 加工费" |

### 4.5 PENDING条目映射方法

```
PENDING条目映射方法 (优先级排序):
  1. 计算值: 可从已确认指标推导 (如lead_total_inv = lead_social_inv + lead_exchange_inv)
  2. API搜索: 通过zhiji search API搜索关键词, 匹配语义ID
  3. 同花顺发散: 通过指标名称反向搜索知几数据源
  4. 人工确认: 需DSHE/DSHB人工确认的歧义项
```

---

## 5. 回填字段映射

### 5.1 回填字段清单 (19项 — 全部MAPPED)

| # | 字段ID | DSHE语义ID | 字段名称 | 数据类型 | 关联zhiji表 | 状态 |
|---|--------|-----------|---------|---------|-----------|------|
| 1 | F-01 | api_batch_support | API批量支持 | BOOLEAN | metric_config | ✅ MAPPED |
| 2 | F-02 | api_subpage_support | API子页面支持 | BOOLEAN | metric_config | ✅ MAPPED |
| 3 | F-03 | api_subpage_data | API子页面数据 | JSON | metric_value | ✅ MAPPED |
| 4 | F-04 | api_batch_timing | API批量时序 | JSON | metric_config | ✅ MAPPED |
| 5 | F-05 | chart_data_source | 图表数据源 | STRING | metric_value | ✅ MAPPED |
| 6 | F-06 | chart_data_consistency | 图表数据一致性 | FLOAT | metric_value | ✅ MAPPED |
| 7 | F-07 | chart_degrade_status | 图表降级状态 | JSON | metric_status | ✅ MAPPED |
| 8 | F-08 | subpanel_data_source | 子面板数据源 | STRING | metric_config | ✅ MAPPED |
| 9 | F-09 | subpanel_data_consistency | 子面板数据一致性 | FLOAT | metric_value | ✅ MAPPED |
| 10 | F-10 | batch_chart_data | 分批图表数据 | JSON | metric_value | ✅ MAPPED |
| 11 | F-11 | chart_data_points | 图表数据点数量 | INTEGER | metric_value | ✅ MAPPED |
| 12 | F-12 | chart_time_range | 图表时间范围 | STRING | metric_value | ✅ MAPPED |
| 13 | F-13 | alias_resolve_rate | 别名解析率 | FLOAT | metric_alias | ✅ MAPPED |
| 14 | F-14 | data_source_status | 数据源状态 | JSON | metric_status | ✅ MAPPED |
| 15 | F-15 | probe_success_rate | 探测成功率 | FLOAT | metric_status | ✅ MAPPED |
| 16 | F-16 | degrade_chart_status | 降级图表状态 | JSON | metric_status | ✅ MAPPED |
| 17 | F-17 | recover_data_consistency | 恢复数据一致性 | FLOAT | metric_value | ✅ MAPPED |
| 18 | F-18 | scenario_replay_data | 场景回放数据 | JSON | metric_value | ✅ MAPPED |
| 19 | F-19 | qa_replay_data | Q&A回放数据 | JSON | metric_value | ✅ MAPPED |

### 5.2 回填字段说明

```
回填字段特点:
  ✅ 全部19项已完成语义ID映射
  ✅ 无需zhiji短ID/长ID (非数据指标)
  ✅ 属于DSHB→DSHE数据回填契约
  ✅ 与指标桥接率统计独立
```

---

## 6. 真实有效桥接率计算

### 6.1 计算方法

```
真实有效桥接率 = COMPLETED数 / 总指标数
             = 8 / 178
             = 4.49%

含回填总映射率 = (COMPLETED + MAPPED回填) / 总条目数
             = (8 + 19) / 197
             = 13.71%
```

### 6.2 与Stage3对照

| 指标 | Stage3报告 | V2修正 | 差异 |
|------|-----------|--------|------|
| 名义覆盖率 | 197/197 (100%) | 27/197 (13.7%) | -86.3% |
| 真实有效桥接率 | 未区分 | 8/178 (4.5%) | +4.5% (首次真实计算) |
| COMPLETED数 | 未标注 | 8 | — |
| PENDING数 | 计入100% | 170 (排除) | -170 |
| 统计口径 | PENDING计入覆盖 | 仅COMPLETED计入 | ✅ 修正 |

### 6.3 目标覆盖率路径

| 阶段 | 目标有效桥接率 | COMPLETED数 | 需要新增映射 | 预计时间 |
|------|-------------|------------|------------|---------|
| 当前 | 4.5% | 8 | — | — |
| P0映射 | 9.5% | 17 | +9 (P0优先级) | 2026-10-13 |
| P1映射 | 53.4% | 95 | +78 (P1优先级) | 2026-10-15 |
| P2映射 | 80.3% | 143 | +48 (P2优先级) | 2026-10-18 |
| 目标 | **≥80%** | **≥143** | **+135** | **2026-10-18** |

---

## 7. Stage3统计口径修正对照

### 7.1 修正前后对比

| 维度 | Stage3 (修正前) | V2 (修正后) | 变化 |
|------|---------------|------------|------|
| 总映射条目 | 197/197 (100%) | 197 (不变) | — |
| 已确认映射 | 未明确标注 | 8 (4.5%) | 新增标注 |
| PENDING条目 | 计入100%覆盖 | 170 (排除) | 排除PENDING |
| 有效桥接率 | 100% (名义) | 4.5% (真实) | -95.5% |
| 回填字段 | 19/19 (100%) | 19/19 (100%) | 不变 |
| 统计口径 | PENDING=COMPLETED | COMPLETED≠PENDING | ✅ 修正 |
| 风险标记 | 无 | R-AUDIT-02 | 新增 |

### 7.2 R-AUDIT-02风险处置

```
R-AUDIT-02: 桥接表统计口径误导
  问题: 将PENDING待映射条目计入100%覆盖率
  影响: 虚假声称197/197 (100%)覆盖, 实际有效仅8/178 (4.5%)
  修正: COMPLETED/PENDING分离, 仅COMPLETED计入有效桥接率
  状态: ✅ 已修正
```

---

## 8. PENDING条目映射计划

### 8.1 映射执行策略

```
映射执行策略:
  策略1: 计算值推导 (3项)
    - PB-011: lead_total_inv = lead_social_inv + lead_exchange_inv
    - PB-014: lead_inv_change = 时间序列差分
    - PB-037: lead_balance = 供给 - 需求

  策略2: API搜索匹配 (约85项)
    - 通过zhiji search API搜索语义ID关键词
    - 匹配返回的series_id
    - 验证数据有效性

  策略3: 批量搜索 (约50项)
    - 按品种批量搜索
    - 按语义ID前缀匹配
    - 人工确认歧义项

  策略4: 跨团队人工确认 (约32项)
    - LI/SI/NI等特殊数据源
    - 需DSHE/DSHB联合确认
```

### 8.2 映射优先级执行表

| 执行批次 | 优先级 | 条目数 | 预计完成 | 方法 |
|---------|--------|--------|---------|------|
| Batch-1 | P0 | 9 | 2026-10-13 | 计算推导+API搜索 |
| Batch-2 | P1 (PB扩展) | 15 | 2026-10-13 | API搜索 |
| Batch-3 | P1 (CU扩展) | 23 | 2026-10-14 | API搜索 |
| Batch-4 | P1 (ZN扩展) | 22 | 2026-10-14 | API搜索 |
| Batch-5 | P1 (AL全模块) | 25 | 2026-10-14 | API搜索 |
| Batch-6 | P2 (NI全模块) | 18 | 2026-10-15 | API搜索+人工 |
| Batch-7 | P2 (SN全模块) | 14 | 2026-10-15 | API搜索+人工 |
| Batch-8 | P2 (SI全模块) | 16 | 2026-10-16 | API搜索+人工 |
| Batch-9 | P2 (LI全模块) | 15 | 2026-10-16 | API搜索+人工 |
| **合计** | — | **157** | **2026-10-16** | — |

### 8.3 ≥80%覆盖率达成条件

```
≥80%覆盖率达成条件:
  ✅ COMPLETED数 ≥ 143/178 (80.3%)
  ✅ 当前: 8 → 需要新增: 135
  ✅ Batch-1~9完成: 8 + 157 = 165/178 (92.7%)
  ✅ 时间: 2026-10-16前完成
  ✅ 验证: 每项映射需API调用验证+DSHE确认
```

---

## 9. DSHE语义ID对齐说明

### 9.1 语义ID统一规范

| 语义ID格式 | 示例 | 说明 |
|-----------|------|------|
| `{metal}_{category}_{name}` | `lead_tc`, `lead_social_inv` | 标准格式 |
| `{metal}_{category}` | `lead_inv`, `cu_tc` | 简化格式 |
| `{category}_{detail}` | `alias_resolve_rate` | 回填字段格式 |

### 9.2 语义ID冲突修正

| 冲突项 | Stage3定义 | V2修正定义 | 说明 |
|--------|-----------|-----------|------|
| lead_social_inv | PB-009 i1 | ✅ 一致 | 铅锭社会库存 |
| lead_exchange_inv | PB-010 i2 | ✅ 一致 | 铅锭交易所库存 |
| lead_tc | PB-015 j25_tc | ✅ 一致 | 铅精矿TC加工费 |
| gmv_daily_avg | (DSHE文档中使用) | 不在桥接表内 | ⚠️ DSHE侧需确认来源 |
| lead_social_inv vs gmv_daily_avg | DSHE面板引用错误 | 统一为lead_social_inv | 跨文档引用需修正 |

### 9.3 双向交叉引用验证

```
双向交叉引用验证 (COMPLETED条目):
  1. PB-009 → i1 → lead_social_inv → 铅锭社会库存 → ID02226334 → a10022003 ✅
  2. PB-010 → i2 → lead_exchange_inv → 铅锭交易所库存 → ID02226335 → a10022004 ✅
  3. PB-015 → j25_tc → lead_tc → 铅精矿TC加工费 → ID02226336 → a10021355 ✅
  4. PB-001 → i3 → shfe_lead_close → 沪铅期货收盘价 → ID02226332 → a10022001 ✅
  5. PB-008 → i4 → lead_ore_spot → 铅锭现货价格 → ID02226333 → a10022002 ✅
  6. PB-017 → i5 → lead_production → 电解铅产量 → ID02226337 → a10022005 ✅
  7. CU-001 → i6 → shfe_cu_close → 沪铜期货收盘价 → ID02226338 → a10022006 ✅
  8. ZN-001 → i7 → shfe_zn_close → 沪锌期货收盘价 → ID02226339 → a10022007 ✅
```

---

## 10. 约束合规声明

| 约束 | 要求 | 实际 | 状态 |
|------|------|------|------|
| NO_ZHIJI_API_CALL | FALSE (允许调用) | 允许调用 | ✅ 合规 |
| NO_MODIFY_V85 | TRUE (禁止修改) | 未修改V85 | ✅ 合规 |
| NO_OVERWRITE | TRUE (禁止覆盖) | 新增V2版本 | ✅ 合规 |
| BRANCH_LOCKED | TRUE (锁定分支) | feature/v85-chart-template | ✅ 合规 |

---

> **文档生成**: 2026-10-12
> **任务**: DSHB_V86_RC2_PROD_FIX_T3.3
> **分支**: `feature/v85-chart-template`
> **状态**: ✅ **FINAL — 桥接表V2修正版, COMPLETED/PENDING分离, 真实有效桥接率=4.5% (8/178), PENDING映射计划已制定**
