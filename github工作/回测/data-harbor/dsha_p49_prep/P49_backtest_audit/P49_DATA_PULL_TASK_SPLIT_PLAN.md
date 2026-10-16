# P49 数据拉取任务拆分计划 · Data Pull Task Split Plan

> **文档ID**: DSHA-P54-P49-DATA-PULL-TASK-SPLIT-001
> **生成时间**: 2026-10-16 GMT+8
> **Agent**: DSHA-P54
> **Branch**: feature/v88-g1
> **GATE**: CLOSED/HOLD
> **Wind API Calls**: 0
> **声明**: 本文档定义108次Wind调用的分片任务清单，锁定调用上限，防止越界批量拉取。

---

## 0. 计划概述

### 0.1 总览

| 维度 | 值 |
|---|---|
| 总调用数 | **108** |
| 涉及因子 | 3 (FACTOR-004, FACTOR-006, FACTOR-007) |
| 涉及数据表 | 3 (Wind因子IC计算表, Wind因子计算管线, Wind多因子合成表) |
| 涉及品种 | 4 (LI.SHF, NI.SHF, ZN.SHF, CU.SHF) |
| 日期范围 | 2023-01-01 ~ 2024-12-31 (731天) |
| 数据块数 | 3 |
| 块大小 | 365天/块 (最后一块1天) |
| 调用上限 | **108** (硬性上限，不可越界) |

### 0.2 调用数分配

```
FACTOR-004 (G1_IC_threshold):
  字段数: 3 (IC_score, forecast_return, realized_return)
  品种数: 4 (LI, NI, ZN, CU)
  块数: 3
  调用数: 3 × 4 × 3 = 36

FACTOR-006 (G7_leakage_ratio):
  字段数: 2 (leakage_score, info_score)
  品种数: 4 (LI, NI, ZN, CU)
  块数: 3
  调用数: 2 × 4 × 3 = 24

FACTOR-007 (SchemeD_frozen_weights):
  字段数: 4 (F19_score, F20_score, CF003_score, decay_score)
  品种数: 4 (LI, NI, ZN, CU)
  块数: 3
  调用数: 4 × 4 × 3 = 48

总计: 36 + 24 + 48 = 108 ✅
```

---

## 1. 数据块定义

### 1.1 块边界

| 块ID | 起始日期 | 结束日期 | 天数 | 覆盖说明 |
|---|---|---|---|---|
| CH01 | 2023-01-01 | 2023-12-31 | 365 | 完整年份 |
| CH02 | 2024-01-01 | 2024-12-30 | 365 | 完整年份(减1天) |
| CH03 | 2024-12-31 | 2024-12-31 | 1 | 余量天 |
| **总计** | — | — | **731** | 2023-01-01 ~ 2024-12-31 |

### 1.2 块计算验证

```
起始: 2023-01-01
+365天 → 2023-12-31 (CH01结束)
+1天 → 2024-01-01 (CH02起始)
+365天 → 2024-12-30 (CH02结束)
+1天 → 2024-12-31 (CH03起始+结束)
```

---

## 2. 分片任务清单

### 2.1 FACTOR-004 任务清单 (36次调用)

**数据表**: Wind因子IC计算表

| 任务ID | 因子 | 品种 | 字段 | 块ID | 日期范围 | 调用序号 |
|---|---|---|---|---|---|---|
| T-F004-001 | FACTOR-004 | LI.SHF | IC_score | CH01 | 2023-01-01~2023-12-31 | 1 |
| T-F004-002 | FACTOR-004 | LI.SHF | forecast_return | CH01 | 2023-01-01~2023-12-31 | 2 |
| T-F004-003 | FACTOR-004 | LI.SHF | realized_return | CH01 | 2023-01-01~2023-12-31 | 3 |
| T-F004-004 | FACTOR-004 | NI.SHF | IC_score | CH01 | 2023-01-01~2023-12-31 | 4 |
| T-F004-005 | FACTOR-004 | NI.SHF | forecast_return | CH01 | 2023-01-01~2023-12-31 | 5 |
| T-F004-006 | FACTOR-004 | NI.SHF | realized_return | CH01 | 2023-01-01~2023-12-31 | 6 |
| T-F004-007 | FACTOR-004 | ZN.SHF | IC_score | CH01 | 2023-01-01~2023-12-31 | 7 |
| T-F004-008 | FACTOR-004 | ZN.SHF | forecast_return | CH01 | 2023-01-01~2023-12-31 | 8 |
| T-F004-009 | FACTOR-004 | ZN.SHF | realized_return | CH01 | 2023-01-01~2023-12-31 | 9 |
| T-F004-010 | FACTOR-004 | CU.SHF | IC_score | CH01 | 2023-01-01~2023-12-31 | 10 |
| T-F004-011 | FACTOR-004 | CU.SHF | forecast_return | CH01 | 2023-01-01~2023-12-31 | 11 |
| T-F004-012 | FACTOR-004 | CU.SHF | realized_return | CH01 | 2023-01-01~2023-12-31 | 12 |
| T-F004-013 | FACTOR-004 | LI.SHF | IC_score | CH02 | 2024-01-01~2024-12-30 | 13 |
| T-F004-014 | FACTOR-004 | LI.SHF | forecast_return | CH02 | 2024-01-01~2024-12-30 | 14 |
| T-F004-015 | FACTOR-004 | LI.SHF | realized_return | CH02 | 2024-01-01~2024-12-30 | 15 |
| T-F004-016 | FACTOR-004 | NI.SHF | IC_score | CH02 | 2024-01-01~2024-12-30 | 16 |
| T-F004-017 | FACTOR-004 | NI.SHF | forecast_return | CH02 | 2024-01-01~2024-12-30 | 17 |
| T-F004-018 | FACTOR-004 | NI.SHF | realized_return | CH02 | 2024-01-01~2024-12-30 | 18 |
| T-F004-019 | FACTOR-004 | ZN.SHF | IC_score | CH02 | 2024-01-01~2024-12-30 | 19 |
| T-F004-020 | FACTOR-004 | ZN.SHF | forecast_return | CH02 | 2024-01-01~2024-12-30 | 20 |
| T-F004-021 | FACTOR-004 | ZN.SHF | realized_return | CH02 | 2024-01-01~2024-12-30 | 21 |
| T-F004-022 | FACTOR-004 | CU.SHF | IC_score | CH02 | 2024-01-01~2024-12-30 | 22 |
| T-F004-023 | FACTOR-004 | CU.SHF | forecast_return | CH02 | 2024-01-01~2024-12-30 | 23 |
| T-F004-024 | FACTOR-004 | CU.SHF | realized_return | CH02 | 2024-01-01~2024-12-30 | 24 |
| T-F004-025 | FACTOR-004 | LI.SHF | IC_score | CH03 | 2024-12-31~2024-12-31 | 25 |
| T-F004-026 | FACTOR-004 | LI.SHF | forecast_return | CH03 | 2024-12-31~2024-12-31 | 26 |
| T-F004-027 | FACTOR-004 | LI.SHF | realized_return | CH03 | 2024-12-31~2024-12-31 | 27 |
| T-F004-028 | FACTOR-004 | NI.SHF | IC_score | CH03 | 2024-12-31~2024-12-31 | 28 |
| T-F004-029 | FACTOR-004 | NI.SHF | forecast_return | CH03 | 2024-12-31~2024-12-31 | 29 |
| T-F004-030 | FACTOR-004 | NI.SHF | realized_return | CH03 | 2024-12-31~2024-12-31 | 30 |
| T-F004-031 | FACTOR-004 | ZN.SHF | IC_score | CH03 | 2024-12-31~2024-12-31 | 31 |
| T-F004-032 | FACTOR-004 | ZN.SHF | forecast_return | CH03 | 2024-12-31~2024-12-31 | 32 |
| T-F004-033 | FACTOR-004 | ZN.SHF | realized_return | CH03 | 2024-12-31~2024-12-31 | 33 |
| T-F004-034 | FACTOR-004 | CU.SHF | IC_score | CH03 | 2024-12-31~2024-12-31 | 34 |
| T-F004-035 | FACTOR-004 | CU.SHF | forecast_return | CH03 | 2024-12-31~2024-12-31 | 35 |
| T-F004-036 | FACTOR-004 | CU.SHF | realized_return | CH03 | 2024-12-31~2024-12-31 | 36 |

### 2.2 FACTOR-006 任务清单 (24次调用)

**数据表**: Wind因子计算管线

| 任务ID | 因子 | 品种 | 字段 | 块ID | 日期范围 | 调用序号 |
|---|---|---|---|---|---|---|
| T-F006-001 | FACTOR-006 | LI.SHF | leakage_score | CH01 | 2023-01-01~2023-12-31 | 37 |
| T-F006-002 | FACTOR-006 | LI.SHF | info_score | CH01 | 2023-01-01~2023-12-31 | 38 |
| T-F006-003 | FACTOR-006 | NI.SHF | leakage_score | CH01 | 2023-01-01~2023-12-31 | 39 |
| T-F006-004 | FACTOR-006 | NI.SHF | info_score | CH01 | 2023-01-01~2023-12-31 | 40 |
| T-F006-005 | FACTOR-006 | ZN.SHF | leakage_score | CH01 | 2023-01-01~2023-12-31 | 41 |
| T-F006-006 | FACTOR-006 | ZN.SHF | info_score | CH01 | 2023-01-01~2023-12-31 | 42 |
| T-F006-007 | FACTOR-006 | CU.SHF | leakage_score | CH01 | 2023-01-01~2023-12-31 | 43 |
| T-F006-008 | FACTOR-006 | CU.SHF | info_score | CH01 | 2023-01-01~2023-12-31 | 44 |
| T-F006-009 | FACTOR-006 | LI.SHF | leakage_score | CH02 | 2024-01-01~2024-12-30 | 45 |
| T-F006-010 | FACTOR-006 | LI.SHF | info_score | CH02 | 2024-01-01~2024-12-30 | 46 |
| T-F006-011 | FACTOR-006 | NI.SHF | leakage_score | CH02 | 2024-01-01~2024-12-30 | 47 |
| T-F006-012 | FACTOR-006 | NI.SHF | info_score | CH02 | 2024-01-01~2024-12-30 | 48 |
| T-F006-013 | FACTOR-006 | ZN.SHF | leakage_score | CH02 | 2024-01-01~2024-12-30 | 49 |
| T-F006-014 | FACTOR-006 | ZN.SHF | info_score | CH02 | 2024-01-01~2024-12-30 | 50 |
| T-F006-015 | FACTOR-006 | CU.SHF | leakage_score | CH02 | 2024-01-01~2024-12-30 | 51 |
| T-F006-016 | FACTOR-006 | CU.SHF | info_score | CH02 | 2024-01-01~2024-12-30 | 52 |
| T-F006-017 | FACTOR-006 | LI.SHF | leakage_score | CH03 | 2024-12-31~2024-12-31 | 53 |
| T-F006-018 | FACTOR-006 | LI.SHF | info_score | CH03 | 2024-12-31~2024-12-31 | 54 |
| T-F006-019 | FACTOR-006 | NI.SHF | leakage_score | CH03 | 2024-12-31~2024-12-31 | 55 |
| T-F006-020 | FACTOR-006 | NI.SHF | info_score | CH03 | 2024-12-31~2024-12-31 | 56 |
| T-F006-021 | FACTOR-006 | ZN.SHF | leakage_score | CH03 | 2024-12-31~2024-12-31 | 57 |
| T-F006-022 | FACTOR-006 | ZN.SHF | info_score | CH03 | 2024-12-31~2024-12-31 | 58 |
| T-F006-023 | FACTOR-006 | CU.SHF | leakage_score | CH03 | 2024-12-31~2024-12-31 | 59 |
| T-F006-024 | FACTOR-006 | CU.SHF | info_score | CH03 | 2024-12-31~2024-12-31 | 60 |

### 2.3 FACTOR-007 任务清单 (48次调用)

**数据表**: Wind多因子合成表

| 任务ID | 因子 | 品种 | 字段 | 块ID | 日期范围 | 调用序号 |
|---|---|---|---|---|---|---|
| T-F007-001 | FACTOR-007 | LI.SHF | F19_score | CH01 | 2023-01-01~2023-12-31 | 61 |
| T-F007-002 | FACTOR-007 | LI.SHF | F20_score | CH01 | 2023-01-01~2023-12-31 | 62 |
| T-F007-003 | FACTOR-007 | LI.SHF | CF003_score | CH01 | 2023-01-01~2023-12-31 | 63 |
| T-F007-004 | FACTOR-007 | LI.SHF | decay_score | CH01 | 2023-01-01~2023-12-31 | 64 |
| T-F007-005 | FACTOR-007 | NI.SHF | F19_score | CH01 | 2023-01-01~2023-12-31 | 65 |
| T-F007-006 | FACTOR-007 | NI.SHF | F20_score | CH01 | 2023-01-01~2023-12-31 | 66 |
| T-F007-007 | FACTOR-007 | NI.SHF | CF003_score | CH01 | 2023-01-01~2023-12-31 | 67 |
| T-F007-008 | FACTOR-007 | NI.SHF | decay_score | CH01 | 2023-01-01~2023-12-31 | 68 |
| T-F007-009 | FACTOR-007 | ZN.SHF | F19_score | CH01 | 2023-01-01~2023-12-31 | 69 |
| T-F007-010 | FACTOR-007 | ZN.SHF | F20_score | CH01 | 2023-01-01~2023-12-31 | 70 |
| T-F007-011 | FACTOR-007 | ZN.SHF | CF003_score | CH01 | 2023-01-01~2023-12-31 | 71 |
| T-F007-012 | FACTOR-007 | ZN.SHF | decay_score | CH01 | 2023-01-01~2023-12-31 | 72 |
| T-F007-013 | FACTOR-007 | CU.SHF | F19_score | CH01 | 2023-01-01~2023-12-31 | 73 |
| T-F007-014 | FACTOR-007 | CU.SHF | F20_score | CH01 | 2023-01-01~2023-12-31 | 74 |
| T-F007-015 | FACTOR-007 | CU.SHF | CF003_score | CH01 | 2023-01-01~2023-12-31 | 75 |
| T-F007-016 | FACTOR-007 | CU.SHF | decay_score | CH01 | 2023-01-01~2023-12-31 | 76 |
| T-F007-017 | FACTOR-007 | LI.SHF | F19_score | CH02 | 2024-01-01~2024-12-30 | 77 |
| T-F007-018 | FACTOR-007 | LI.SHF | F20_score | CH02 | 2024-01-01~2024-12-30 | 78 |
| T-F007-019 | FACTOR-007 | LI.SHF | CF003_score | CH02 | 2024-01-01~2024-12-30 | 79 |
| T-F007-020 | FACTOR-007 | LI.SHF | decay_score | CH02 | 2024-01-01~2024-12-30 | 80 |
| T-F007-021 | FACTOR-007 | NI.SHF | F19_score | CH02 | 2024-01-01~2024-12-30 | 81 |
| T-F007-022 | FACTOR-007 | NI.SHF | F20_score | CH02 | 2024-01-01~2024-12-30 | 82 |
| T-F007-023 | FACTOR-007 | NI.SHF | CF003_score | CH02 | 2024-01-01~2024-12-30 | 83 |
| T-F007-024 | FACTOR-007 | NI.SHF | decay_score | CH02 | 2024-01-01~2024-12-30 | 84 |
| T-F007-025 | FACTOR-007 | ZN.SHF | F19_score | CH02 | 2024-01-01~2024-12-30 | 85 |
| T-F007-026 | FACTOR-007 | ZN.SHF | F20_score | CH02 | 2024-01-01~2024-12-30 | 86 |
| T-F007-027 | FACTOR-007 | ZN.SHF | CF003_score | CH02 | 2024-01-01~2024-12-30 | 87 |
| T-F007-028 | FACTOR-007 | ZN.SHF | decay_score | CH02 | 2024-01-01~2024-12-30 | 88 |
| T-F007-029 | FACTOR-007 | CU.SHF | F19_score | CH02 | 2024-01-01~2024-12-30 | 89 |
| T-F007-030 | FACTOR-007 | CU.SHF | F20_score | CH02 | 2024-01-01~2024-12-30 | 90 |
| T-F007-031 | FACTOR-007 | CU.SHF | CF003_score | CH02 | 2024-01-01~2024-12-30 | 91 |
| T-F007-032 | FACTOR-007 | CU.SHF | decay_score | CH02 | 2024-01-01~2024-12-30 | 92 |
| T-F007-033 | FACTOR-007 | LI.SHF | F19_score | CH03 | 2024-12-31~2024-12-31 | 93 |
| T-F007-034 | FACTOR-007 | LI.SHF | F20_score | CH03 | 2024-12-31~2024-12-31 | 94 |
| T-F007-035 | FACTOR-007 | LI.SHF | CF003_score | CH03 | 2024-12-31~2024-12-31 | 95 |
| T-F007-036 | FACTOR-007 | LI.SHF | decay_score | CH03 | 2024-12-31~2024-12-31 | 96 |
| T-F007-037 | FACTOR-007 | NI.SHF | F19_score | CH03 | 2024-12-31~2024-12-31 | 97 |
| T-F007-038 | FACTOR-007 | NI.SHF | F20_score | CH03 | 2024-12-31~2024-12-31 | 98 |
| T-F007-039 | FACTOR-007 | NI.SHF | CF003_score | CH03 | 2024-12-31~2024-12-31 | 99 |
| T-F007-040 | FACTOR-007 | NI.SHF | decay_score | CH03 | 2024-12-31~2024-12-31 | 100 |
| T-F007-041 | FACTOR-007 | ZN.SHF | F19_score | CH03 | 2024-12-31~2024-12-31 | 101 |
| T-F007-042 | FACTOR-007 | ZN.SHF | F20_score | CH03 | 2024-12-31~2024-12-31 | 102 |
| T-F007-043 | FACTOR-007 | ZN.SHF | CF003_score | CH03 | 2024-12-31~2024-12-31 | 103 |
| T-F007-044 | FACTOR-007 | ZN.SHF | decay_score | CH03 | 2024-12-31~2024-12-31 | 104 |
| T-F007-045 | FACTOR-007 | CU.SHF | F19_score | CH03 | 2024-12-31~2024-12-31 | 105 |
| T-F007-046 | FACTOR-007 | CU.SHF | F20_score | CH03 | 2024-12-31~2024-12-31 | 106 |
| T-F007-047 | FACTOR-007 | CU.SHF | CF003_score | CH03 | 2024-12-31~2024-12-31 | 107 |
| T-F007-048 | FACTOR-007 | CU.SHF | decay_score | CH03 | 2024-12-31~2024-12-31 | 108 |

---

## 3. 调用上限锁定机制

### 3.1 硬性上限

| 层级 | 上限 | 验证方式 |
|---|---|---|
| 总调用上限 | **108** | pre_wind_call_guard_check.py 自动校验 |
| 单因子上限 | F004:36 / F006:24 / F007:48 | 管道执行前校验 |
| 单块上限 | 36 (F004) / 24 (F006) / 48 (F007) | 管道执行前校验 |
| 单品种上限 | 9 (F004) / 6 (F006) / 12 (F007) | 管道执行前校验 |
| 单日调用上限 | — | 由块边界隐式控制 |

### 3.2 越界防护

```
GUARD-001: 总调用数 ≤ 108
  └─ 超过108次调用时: 拒绝执行，抛出 CallLimitExceededError

GUARD-002: 因子调用数 ≤ 单因子上限
  └─ 超过因子上限时: 拒绝执行该因子剩余任务

GUARD-003: 禁止访问HOLD因子
  └─ 尝试访问FACTOR-001/002/003/005时: 抛出HoldFactorTerminationError

GUARD-004: 禁止跨日期范围
  └─ 调用日期超出2023-01-01~2024-12-31时: 拒绝执行

GUARD-005: 禁止跨品种
  └─ 调用品种不在LI/NI/ZN/CU.SHF时: 拒绝执行

GUARD-006: 禁止跨字段
  └─ 调用字段不在因子定义字段列表中时: 拒绝执行
```

### 3.3 调用计数器机制

```json
{
  "call_counter": {
    "total_limit": 108,
    "total_calls_made": 0,
    "total_calls_remaining": 108,
    "by_factor": {
      "FACTOR-004": {"limit": 36, "made": 0, "remaining": 36},
      "FACTOR-006": {"limit": 24, "made": 0, "remaining": 24},
      "FACTOR-007": {"limit": 48, "made": 0, "remaining": 48}
    },
    "by_chunk": {
      "CH01": {"limit": 64, "made": 0, "remaining": 64},
      "CH02": {"limit": 32, "made": 0, "remaining": 32},
      "CH03": {"limit": 12, "made": 0, "remaining": 12}
    }
  }
}
```

---

## 4. 执行策略

### 4.1 推荐执行顺序

| 顺序 | 因子 | 调用数 | 理由 |
|---|---|---|---|
| 1 | FACTOR-004 | 36 | 条件约束最少(仅IC稳定性)，最先验证 |
| 2 | FACTOR-006 | 24 | 调用数最少，验证G7边界 |
| 3 | FACTOR-007 | 48 | 调用数最多，多窗口稳定性验证 |

### 4.2 块内执行顺序

```
每个块内按品种顺序执行: LI → NI → ZN → CU
每个品种内按字段顺序执行: fields[0] → fields[1] → ... → fields[n-1]
```

### 4.3 错误处理

| 错误类型 | 处理方式 | 重试策略 |
|---|---|---|
| WindPy连接失败 | 切换到Excel后端 | 最多3次重试 |
| 单次调用失败 | 标记FAIL，继续下一个任务 | 最多1次重试 |
| 连续5次失败 | 停止执行，升级DSHC | 不自动重试 |
| 数据为空 | 标记EMPTY，继续 | 不重试 |
| 调用超限 | 拒绝执行，抛出异常 | 不重试 |

---

## 5. 任务完成追踪模板

```json
{
  "task_status": {
    "timestamp": "<ISO-8601>",
    "total_tasks": 108,
    "completed": 0,
    "failed": 0,
    "skipped": 0,
    "remaining": 108,
    "by_factor": {
      "FACTOR-004": {"total": 36, "completed": 0, "failed": 0, "skipped": 0},
      "FACTOR-006": {"total": 24, "completed": 0, "failed": 0, "skipped": 0},
      "FACTOR-007": {"total": 48, "completed": 0, "failed": 0, "skipped": 0}
    },
    "by_chunk": {
      "CH01": {"total": 64, "completed": 0, "failed": 0, "skipped": 0},
      "CH02": {"total": 32, "completed": 0, "failed": 0, "skipped": 0},
      "CH03": {"total": 12, "completed": 0, "failed": 0, "skipped": 0}
    },
    "total_wind_calls_actual": 0,
    "governance_invariants_maintained": true
  }
}
```

---

## 6. 治理不变量

| 不变量 | 要求 | 当前值 |
|---|---|---|
| wind_api_calls | 0 (拉取前) | 0 |
| backtest_started | false | false |
| gate | CLOSED/HOLD | CLOSED/HOLD |
| release_permit | NOT_ISSUED | NOT_ISSUED |
| HOLD因子访问 | 0 次 | 0 |
| 调用上限 | 108 | 108 (锁定) |

> **DSHA-P54 声明**: 本文档为纯离线分析产物，未调用任何 Wind API。
> 所有治理不变量保持：wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED。

---

_生成时间: 2026-10-16 GMT+8 | Agent: DSHA-P54 | Branch: feature/v88-g1_