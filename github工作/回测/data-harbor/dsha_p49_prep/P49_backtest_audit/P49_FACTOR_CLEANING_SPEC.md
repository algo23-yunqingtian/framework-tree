# P49 因子数据清洗规范说明文档 · Factor Cleaning Specification Companion

> **文档ID**: DSHA-P54-P49-FACTOR-CLEANING-SPEC-001-COMPANION
> **生成时间**: 2026-10-16 GMT+8
> **Agent**: DSHA-P54
> **Branch**: feature/v88-g1
> **GATE**: CLOSED/HOLD
> **Wind API Calls**: 0
> **配套文件**: `P49_FACTOR_CLEANING_SPEC.json`

---

## 0. 文档目的

本文档为 `P49_FACTOR_CLEANING_SPEC.json` 的配套说明文档，解释清洗规则的设计逻辑、执行顺序、异常处理策略。

---

## 1. 清洗规范总览

### 1.1 统计概览

| 维度 | 数值 |
|---|---|
| 总因子数 | 7 |
| 总参数数 | 11 |
| 总数据字段 | 18 (去重) |
| 因子级清洗规则 | 58 |
| 全局清洗规则 | 7 |
| 异常过滤规则 | 10 |
| **总规则数** | **66** |

### 1.2 规则分类分布

| 类别 | 因子级 | 全局 | 合计 |
|---|---|---|---|
| 缺失值处理 (missing_value_handling) | 14 | 1 (NaN/Inf) | 15 |
| 异常值检测 (outlier_detection) | 7 | 0 | 7 |
| 异常过滤 (anomaly_filtering) | 7 | 1 (零值密集) | 8 |
| 边界检查 (boundary_checking) | 10 | 0 | 10 |
| 一致性验证 (consistency_validation) | 14 | 2 (重复行+行计数) | 16 |
| 数据类型强制 (data_type_enforcement) | 7 | 2 (日期+品种) | 9 |
| **合计** | **58** | **8** | **66** |

### 1.3 按因子分布

| Factor | 准入状态 | 清洗规则数 | 异常规则数 | 总计 |
|---|---|---|---|---|
| FACTOR-001 | HOLD | 7 | 0 | 7 |
| FACTOR-002 | HOLD | 7 | 0 | 7 |
| FACTOR-003 | HOLD | 7 | 1 | 8 |
| FACTOR-004 | CONDITIONAL_PASS | 10 | 4 | 14 |
| FACTOR-005 | HOLD | 7 | 1 | 8 |
| FACTOR-006 | CONDITIONAL_PASS | 9 | 2 | 11 |
| FACTOR-007 | CONDITIONAL_PASS | 10 | 3 | 13 |
| **全局** | — | 7 | 0 | 7 |
| **总计** | — | **57** | **10** | **67** |

---

## 2. 清洗执行顺序

### 2.1 执行流水线

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: 全局预处理 (Global Pre-processing)                  │
│  ─────────────────────────────────────────                    │
│  GLB-CLN-001: 日期格式标准化 → %Y-%m-%d                      │
│  GLB-CLN-002: 品种代码校验 → LI/NI/ZN/CU.SHF                │
│  GLB-CLN-003: NaN/Inf替换 → 排除行                           │
│  GLB-CLN-004: 重复行检测 → key=date+variety, keep_last       │
│  GLB-CLN-005: 日期范围校验 → 2023-01-01 ~ 2024-12-31        │
├─────────────────────────────────────────────────────────────┤
│  STAGE 2: 因子级清洗 (Factor-level Cleaning)                  │
│  ─────────────────────────────────────────                    │
│  按因子ID顺序执行各因子的 CLN-001 ~ CLN-nnn 规则              │
│  因子内部按 rule_id 字母序执行                                │
├─────────────────────────────────────────────────────────────┤
│  STAGE 3: 全局后处理 (Global Post-processing)                  │
│  ─────────────────────────────────────────                    │
│  GLB-CLN-006: 行计数校验 → 每块250~400行                     │
│  GLB-CLN-007: 零值密集检测 → 零值比例<80%                     │
├─────────────────────────────────────────────────────────────┤
│  STAGE 4: 异常规则 (Anomaly Rules)                            │
│  ─────────────────────────────────────────                    │
│  按因子ID顺序执行各因子的 ANOM-001 ~ ANOM-nnn 规则             │
│  标记但不阻断（除非severity=CRITICAL）                         │
├─────────────────────────────────────────────────────────────┤
│  STAGE 5: 条件约束验证 (Conditional Constraint Validation)     │
│  ─────────────────────────────────────────                    │
│  验证WL-A001~WL-A007跟踪项条件是否满足                        │
│  HOLD因子: 确认仍被阻断                                       │
│  CONDITIONAL因子: 检查条件进展                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 执行顺序规则

| 规则 | 说明 |
|---|---|
| 先全局后因子 | 全局预处理在任何因子清洗之前执行 |
| 先清洗后异常 | 清洗规则先于异常规则执行 |
| 先数值后校验 | 缺失值处理先于边界检查 |
| 先标记后阻断 | 异常规则仅标记，仅CRITICAL级阻断 |

---

## 3. 关键清洗规则详解

### 3.1 FACTOR-004 · G1_IC_threshold (CONDITIONAL_PASS)

**数据字段**: IC_score, forecast_return, realized_return, date, variety

**关键规则**:

| 规则ID | 描述 | 方法 | 阈值 | 动作 |
|---|---|---|---|---|
| F004-CLN-004 | IC极端值过滤 | z_score | |z| > 3.0 | exclude_row |
| F004-CLN-005 | 预测收益异常 | 95% CI | 超出区间 | exclude_row |
| F004-CLN-006 | 收益跳变 | 绝对阈值 | |Δr| > 5% | exclude_row |
| F004-CLN-008 | 窗口边缘检测 | 最小观测 | < 5观测 | flag_edge |

**特殊处理**: IC_score字段必须完整，不允许填充——缺失即排除行。这是因为IC值是因子核心指标，填充值会污染后续计算。

### 3.2 FACTOR-006 · G7_leakage_ratio (CONDITIONAL_PASS)

**数据字段**: leakage_score, info_score, date, variety, factor_id

**关键规则**:

| 规则ID | 描述 | 方法 | 阈值 | 动作 |
|---|---|---|---|---|
| F006-CLN-005 | 泄漏标记 | 阈值检查 | > 0.005 | flag_as_leakage |
| F006-CLN-006 | 极端值检测 | z_score | |z| > 3.0 | flag_for_review |
| F006-ANOM-001 | G7边界复核 | 阈值检查 | > 0.005 | flag_as_potential_leakage (CRITICAL) |
| F006-ANOM-002 | 白名单覆盖 | 白名单匹配 | WL-001范围 | suppress_false_alarm |

**特殊处理**: G7_THRESHOLD=0.005 由DSHC锁定，不可修改。异常规则会检查是否在WL-001白名单覆盖范围内——若在范围内则压制为假警报。

### 3.3 FACTOR-007 · SchemeD_frozen_weights (CONDITIONAL_PASS)

**数据字段**: F19_score, F20_score, CF003_score, decay_score, date, variety

**关键规则**:

| 规则ID | 描述 | 方法 | 阈值 | 动作 |
|---|---|---|---|---|
| F007-CLN-005 | 子因子极端值 | z_score | |z| > 3.0 | cap_at_3sigma |
| F007-CLN-006 | 子因子范围 | 范围检查 | [-1, 1] | clip_to_range |
| F007-CLN-007 | 加权求和一致性 | 求和校验 | tolerance=0.001 | recalculate |
| F007-CLN-008 | 窗口参数边界 | 范围检查 | [35, 100] | reject |

**特殊处理**: 4个子因子得分均不填充，缺失即排除行。加权求和一致性校验确保合成因子计算正确。窗口参数边界校验确保不在35~100日范围外执行。

---

## 4. 异常处理策略

### 4.1 动作分级

| 动作 | 含义 | 阻断性 | 可逆性 |
|---|---|---|---|
| exclude_row | 排除该行数据 | 阻断 | 可恢复（保留原始数据） |
| clip_to_range | 裁剪至范围内 | 修改值 | 可逆 |
| cap_at_3sigma | 封顶至3σ | 修改值 | 可逆 |
| set_to_zero | 设为零 | 修改值 | 可逆 |
| flag_for_review | 标记待审 | 不阻断 | 可清除 |
| flag_as_leakage | 标记为泄露 | 不阻断 | 可清除 |
| flag_instability | 标记为不稳定 | 不阻断 | 可清除 |
| flag_definition_issue | 标记定义问题 | 不阻断 | 可清除 |
| recalculate | 重新计算 | 修改值 | 可逆 |
| reject_out_of_range | 拒绝越界值 | 阻断 | 可恢复 |
| escalate_to_dshc | 升级DSHC | 阻断 | 需DSHC审批 |
| suppress_false_alarm | 压制假警报 | 不阻断 | 可恢复 |

### 4.2 严重级别

| 级别 | 说明 | 动作 |
|---|---|---|
| INFO | 信息级，仅记录 | 继续执行 |
| WARNING | 预警级，需关注 | 标记后继续 |
| CRITICAL | 严重级，需处理 | 标记后升级DSHC |

---

## 5. 数据字段标准化

### 5.1 字段命名规范

| 规范 | 说明 | 示例 |
|---|---|---|
| 蛇形命名 | Python字段名统一snake_case | IC_score, forecast_return |
| Wind字段缩写 | Wind端使用标准缩写 | IC, FCR, RR |
| 日期格式 | 统一YYYY-MM-DD | 2023-01-15 |
| 品种代码 | 统一品种.交易所.SHF格式 | LI.SHF |
| 数值精度 | 统一保留10位小数 | 0.1234567890 |

### 5.2 字段映射完整性

| 因子 | 本地字段 | Wind字段 | 映射状态 |
|---|---|---|---|
| FACTOR-004 | IC_score | IC | ✅ |
| FACTOR-004 | forecast_return | FCR | ✅ |
| FACTOR-004 | realized_return | RR | ✅ |
| FACTOR-006 | leakage_score | LKS | ✅ |
| FACTOR-006 | info_score | IFS | ✅ |
| FACTOR-007 | F19_score | F19 | ✅ |
| FACTOR-007 | F20_score | F20 | ✅ |
| FACTOR-007 | CF003_score | CF003 | ✅ |
| FACTOR-007 | decay_score | DEC | ✅ |

---

## 6. 执行阶段控制

### 6.1 当前阶段

| 因子 | 阶段 | 清洗状态 |
|---|---|---|
| FACTOR-001 | 定义阶段 | ❌ 不执行 (HOLD) |
| FACTOR-002 | 定义阶段 | ❌ 不执行 (HOLD) |
| FACTOR-003 | 定义阶段 | ❌ 不执行 (HOLD) |
| FACTOR-004 | 定义阶段 | ❌ 不执行 (等待数据拉取) |
| FACTOR-005 | 定义阶段 | ❌ 不执行 (HOLD) |
| FACTOR-006 | 定义阶段 | ❌ 不执行 (等待数据拉取) |
| FACTOR-007 | 定义阶段 | ❌ 不执行 (等待数据拉取) |

### 6.2 执行触发条件

清洗规则的执行需满足以下条件：
1. Wind 真实数据拉取完成
2. 数据落盘至本地
3. DSHC 授权执行
4. HOLD 因子仍保持阻断

---

## 7. 总结

| 项目 | 结果 |
|---|---|
| 总规则数 | 66 (58 因子级 + 7 全局 + 10 异常) |
| 清洗执行阶段 | 定义阶段完成，等待数据拉取后执行 |
| HOLD因子规则 | 已定义但未执行，保持阻断 |
| CONDITIONAL因子规则 | 已定义，等待数据拉取后执行 |
| 全局预处理规则 | 7条，覆盖日期/品种/NaN/重复/范围/计数/零值 |
| 异常规则 | 10条，覆盖极端值/边界/稳定性/泄露 |

> **DSHA-P54 声明**: 本文档为纯离线分析产物，未调用任何 Wind API。
> 所有治理不变量保持：wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED。

---

_生成时间: 2026-10-16 GMT+8 | Agent: DSHA-P54 | Branch: feature/v88-g1_