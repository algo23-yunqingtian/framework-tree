# P49 因子文档补充 · 指标与参数释义

> **文档ID**: DSHA-P54-P49-FACTOR-DOC-SUPPLEMENT-001
> **生成时间**: 2026-10-16 GMT+8
> **Agent**: DSHA-P54
> **Branch**: feature/v88-g1
> **GATE**: CLOSED/HOLD
> **Wind API Calls**: 0
> **声明**: 纯离线文档补充，基于本地存量文件，无任何Wind访问。

---

## 1. 文档目的

本文档为 P49 因子体系补充完整的指标定义与参数释义，涵盖:
- 7 因子的完整参数说明
- 11 个参数的边界、敏感性与含义
- 数据字段与 Wind 字段映射关系
- 阈值与窗口参数释义
- 条件约束的验证方法说明

---

## 2. 因子总览

| Factor ID | 因子名称 | 准入状态 | 风险分类 | 条件约束 |
|---|---|---|---|---|
| FACTOR-001 | F19_hot_money_weight | HOLD | SYNTHETIC_DATA_ZERO_SIGNAL | Wind真实数据接入后重测 |
| FACTOR-002 | F20_attention_weight | HOLD | SYNTHETIC_DATA_ZERO_SIGNAL | Wind真实数据接入后重测 |
| FACTOR-003 | CF003_speculation_weight | HOLD | SYNTHETIC_DATA_ZERO_SIGNAL | Wind真实数据接入后重测 |
| FACTOR-004 | G1_IC_threshold | CONDITIONAL_PASS | THRESHOLD_STABILITY_DEFECT | IC稳定性+多窗口阈值验证 |
| FACTOR-005 | G3_ICIR_threshold | HOLD | ICIR_DEFINITION_REDESIGN_REQUIRED | ICIR指标重设计并验证 |
| FACTOR-006 | G7_leakage_ratio | CONDITIONAL_PASS | LEAKAGE_BOUNDARY_FALSE_ALARM | 真实数据下G7边界复核 |
| FACTOR-007 | SchemeD_frozen_weights | CONDITIONAL_PASS | MULTI_WINDOW_INSTABILITY | 35~100日窗口稳定性验证 |

---

## 3. 因子详细文档

### 3.1 FACTOR-001 · F19_hot_money_weight (热钱权重因子)

| 属性 | 值 |
|---|---|
| **Factor ID** | FACTOR-001 |
| **代码名** | F19_hot_money_weight |
| **中文名** | 热钱权重因子 |
| **数据源表** | Wind持仓量表 |
| **准入状态** | HOLD (WL-A001) |
| **风险分类** | SYNTHETIC_DATA_ZERO_SIGNAL |
| **泄露裁决** | N/A_SYNTHETIC_DATA |
| **当前IC** | 0.0 (合成数据零信号) |

**参数说明**:

| 参数名 | 类型 | 当前值 | 含义 |
|---|---|---|---|
| weight_alpha | float | N/A | 热钱资金权重系数，衡量短期投机资金对价格的冲击程度 |
| oi_change_ratio | float | N/A | 持仓量变化比率，(当前OI - 前日OI) / 前日OI |
| volume_weight | float | N/A | 成交量权重，标准化后的成交量因子 |

**数据字段**:

| 字段名 | 数据类型 | 来源 | 说明 |
|---|---|---|---|
| OI | numeric | Wind持仓量表 | 当日持仓量(手) |
| OI_change | numeric | Wind持仓量表 | 持仓量变化(手) |
| date | date | Wind持仓量表 | 交易日期 |
| variety | string | Wind持仓量表 | 品种代码 |

**Wind代码**: LI.SHF (锂), NI.SHF (镍), ZN.SHF (锌), CU.SHF (铜)

**日期范围**: 2023-01-01 ~ 2024-12-31

**阻断原因**: 因子基于合成数据计算，IC=0.0，无真实信号。需接入Wind真实数据后重新计算。

**解除条件**: Wind数据接入 + 重测通过 (IC != 0)

---

### 3.2 FACTOR-002 · F20_attention_weight (注意力权重因子)

| 属性 | 值 |
|---|---|
| **Factor ID** | FACTOR-002 |
| **代码名** | F20_attention_weight |
| **中文名** | 注意力权重因子 |
| **数据源表** | Wind新闻舆情表 |
| **准入状态** | HOLD (WL-A002) |
| **风险分类** | SYNTHETIC_DATA_ZERO_SIGNAL |
| **泄露裁决** | N/A_SYNTHETIC_DATA |

**参数说明**:

| 参数名 | 类型 | 当前值 | 含义 |
|---|---|---|---|
| attention_weight | float | N/A | 市场注意力权重，基于搜索量和舆情热度计算 |
| sentiment_beta | float | N/A | 情绪因子，衡量市场情绪对价格的影响系数 |
| search_decay | float | N/A | 搜索量衰减因子，指数衰减权重 |

**数据字段**:

| 字段名 | 数据类型 | 来源 | 说明 |
|---|---|---|---|
| sentiment_score | numeric | Wind新闻舆情表 | 舆情情绪得分 (-1~1) |
| search_volume | numeric | Wind新闻舆情表 | 搜索引擎搜索量 |
| date | date | Wind新闻舆情表 | 交易日期 |
| variety | string | Wind新闻舆情表 | 品种代码 |

**阻断原因**: 同FACTOR-001，合成数据零信号。

---

### 3.3 FACTOR-003 · CF003_speculation_weight (投机持仓权重因子)

| 属性 | 值 |
|---|---|
| **Factor ID** | FACTOR-003 |
| **代码名** | CF003_speculation_weight |
| **中文名** | 投机持仓权重因子 |
| **数据源表** | Wind交易所持仓明细表 |
| **准入状态** | HOLD (WL-A003) |
| **风险分类** | SYNTHETIC_DATA_ZERO_SIGNAL |

**参数说明**:

| 参数名 | 类型 | 当前值 | 含义 |
|---|---|---|---|
| spec_oi_ratio | float | N/A | 投机持仓占比，投机持仓/总持仓 |
| long_short_ratio | float | N/A | 多空持仓比，多头持仓/空头持仓 |
| exchange_concentration | float | N/A | 交易所集中度，前N大会员持仓占比 |

**数据字段**:

| 字段名 | 数据类型 | 来源 | 说明 |
|---|---|---|---|
| exchange_oi | numeric | Wind交易所持仓明细表 | 交易所持仓量 |
| long_oi | numeric | Wind交易所持仓明细表 | 多头持仓量 |
| short_oi | numeric | Wind交易所持仓明细表 | 空头持仓量 |
| date | date | Wind交易所持仓明细表 | 交易日期 |
| variety | string | Wind交易所持仓明细表 | 品种代码 |

**特殊标注**: 100% 坏样本清洗率需关注 (来自poll39_factor_leakage_risk_appendix.md)

---

### 3.4 FACTOR-004 · G1_IC_threshold (G1 IC入场阈值因子) ⭐ CONDITIONAL_PASS

| 属性 | 值 |
|---|---|
| **Factor ID** | FACTOR-004 |
| **代码名** | G1_IC_threshold |
| **中文名** | G1 IC入场阈值因子 |
| **数据源表** | Wind因子IC计算表 |
| **准入状态** | CONDITIONAL_PASS (WL-A004) |
| **风险分类** | THRESHOLD_STABILITY_DEFECT |
| **泄露裁决** | NO_LEAKAGE_EVIDENCE |
| **Process Block** | False (已允许进入管线) |

**参数说明**:

| 参数名 | 类型 | 当前值 | 敏感性 | 含义 |
|---|---|---|---|---|
| ic_threshold | float | 待验证 | HIGH | IC入场阈值，因子值超过此阈值时触发交易信号 |
| ic_window | int | 60 | MEDIUM | IC计算窗口(日)，滚动IC的计算窗口长度 |
| ic_significance | float | 0.05 | MEDIUM | IC显著性水平，p值阈值 |

**数据字段与Wind映射**:

| 字段名 | Wind字段 | 数据类型 | 说明 |
|---|---|---|---|
| IC_score | IC | numeric | Information Coefficient，因子值与未来收益的相关系数 |
| forecast_return | FCR | numeric | 预测收益率，基于因子值计算的预期收益 |
| realized_return | RR | numeric | 实际收益率，实际实现的未来收益 |

**条件约束详解**:

| 约束项 | 要求 | 验证方法 | 当前状态 |
|---|---|---|---|
| IC稳定性 | IC符号在多个时间窗口内保持一致 | 35d/60d/100d窗口IC符号检验 | 待验证 |
| 多窗口阈值 | 阈值在不同窗口下保持稳定 | 网格搜索阈值敏感性分析 | 待验证 |

**异常过滤规则 (G1-ANOM-001~004)**:

| 规则ID | 描述 | 过滤条件 |
|---|---|---|
| G1-ANOM-001 | IC极端值过滤 | |IC| > 3 * IC_std |
| G1-ANOM-002 | 预测收益异常 | forecast_return 超出95%置信区间 |
| G1-ANOM-003 | 收益跳变 | |realized_return| > 5% |
| G1-ANOM-004 | 窗口边界伪影 | 窗口边缘数据不足5个观测 |

**预计调用数**: 36次 (3字段 × 4代码 × 3块)

---

### 3.5 FACTOR-005 · G3_ICIR_threshold (G3 ICIR稳定性阈值因子)

| 属性 | 值 |
|---|---|
| **Factor ID** | FACTOR-005 |
| **代码名** | G3_ICIR_threshold |
| **中文名** | G3 ICIR稳定性阈值因子 |
| **数据源表** | Wind因子ICIR计算表 |
| **准入状态** | HOLD (WL-A005) |
| **风险分类** | ICIR_DEFINITION_REDESIGN_REQUIRED |

**参数说明**:

| 参数名 | 类型 | 当前值 | 敏感性 | 含义 |
|---|---|---|---|---|
| icir_threshold | float | N/A | HIGH | ICIR入场阈值，信息比率的信息系数版本 |
| icir_window | int | 60 | MEDIUM | ICIR计算窗口 |
| icir_min_periods | int | 30 | LOW | ICIR最小观测期数 |

**阻断原因**: ICIR指标定义存在跨窗口符号翻转问题，需重新设计ICIR计算方式。

**ICIR定义问题**:
- 当前定义: ICIR = mean(IC) / std(IC)
- 问题: 在不同窗口(35d/60d/100d)下ICIR符号发生翻转，表明计算方式不稳定
- 建议: 引入滚动ICIR (rolling_ICIR) 作为辅助指标

**数据字段**:

| 字段名 | 数据类型 | 说明 |
|---|---|---|
| rolling_ICIR | numeric | 滚动ICIR值 |
| IC_std | numeric | IC标准差 |
| date | date | 交易日期 |

---

### 3.6 FACTOR-006 · G7_leakage_ratio (G7泄漏率因子) ⭐ CONDITIONAL_PASS

| 属性 | 值 |
|---|---|
| **Factor ID** | FACTOR-006 |
| **代码名** | G7_leakage_ratio |
| **中文名** | G7泄漏率因子 |
| **数据源表** | Wind因子计算管线 |
| **准入状态** | CONDITIONAL_PASS (WL-A006) |
| **风险分类** | LEAKAGE_BOUNDARY_FALSE_ALARM |
| **泄露裁决** | FALSE_ALARM_MITIGATED |
| **Process Block** | False (已允许进入管线) |
| **G7_THRESHOLD** | 0.005 (DSHC锁定) |

**参数说明**:

| 参数名 | 类型 | 当前值 | 敏感性 | 含义 |
|---|---|---|---|---|
| leakage_threshold | float | 0.005 | HIGH | 泄漏率阈值，超过此值判定为潜在泄露 |
| info_score_weight | float | 1.0 | MEDIUM | 信息分数权重，衡量因子信息含量 |
| leakage_window | int | 35 | LOW | 泄漏检测窗口 |

**数据字段与Wind映射**:

| 字段名 | Wind字段 | 数据类型 | 说明 |
|---|---|---|---|
| leakage_score | LKS | numeric | 泄漏分数，衡量因子值与未来数据的相关性 |
| info_score | IFS | numeric | 信息分数，衡量因子信息含量 |

**G7阈值锁定说明**:
- G7_THRESHOLD = 0.005 由DSHC在G7裁决中锁定
- 此阈值用于判定因子计算过程中是否存在未来数据泄露
- 31次误报已被白名单WL-001覆盖
- 当前为噪声级IC触发的边界告警，非真实泄露

**条件约束**: 真实数据下G7边界复核 — 接入Wind真实数据后重新验证G7阈值是否仍然适用。

**预计调用数**: 24次 (2字段 × 4代码 × 3块)

---

### 3.7 FACTOR-007 · SchemeD_frozen_weights (SchemeD冻结权重合成因子) ⭐ CONDITIONAL_PASS

| 属性 | 值 |
|---|---|
| **Factor ID** | FACTOR-007 |
| **代码名** | SchemeD_frozen_weights |
| **中文名** | SchemeD冻结权重合成因子 |
| **数据源表** | Wind多因子合成表 |
| **准入状态** | CONDITIONAL_PASS (WL-A007) |
| **风险分类** | MULTI_WINDOW_INSTABILITY |
| **泄露裁决** | NO_LEAKAGE_EVIDENCE |
| **Process Block** | False (已允许进入管线) |
| **窗口参数** | 60日 (基准) / 35~100日 (验证范围) |

**参数说明**:

| 参数名 | 类型 | 当前值 | 敏感性 | 含义 |
|---|---|---|---|---|
| f19_weight | float | frozen | HIGH | F19热钱因子权重 (冻结值) |
| f20_weight | float | frozen | HIGH | F20注意力因子权重 (冻结值) |
| cf003_weight | float | frozen | HIGH | CF003投机因子权重 (冻结值) |
| decay_factor | float | frozen | MEDIUM | 衰减因子，多窗口合成时的时间衰减 |
| window_days | int | 60 | MEDIUM | 合成窗口天数 (基准值) |

**数据字段与Wind映射**:

| 字段名 | Wind字段 | 数据类型 | 说明 |
|---|---|---|---|
| F19_score | F19 | numeric | F19热钱权重因子得分 |
| F20_score | F20 | numeric | F20注意力权重因子得分 |
| CF003_score | CF003 | numeric | CF003投机持仓权重因子得分 |
| decay_score | DEC | numeric | 时间衰减后合成得分 |

**SchemeD合成逻辑**:
```
SchemeD = f19_weight * F19_score 
        + f20_weight * F20_score 
        + cf003_weight * CF003_score 
        * decay_factor(t)
```

**多窗口不稳定性说明**:
- 当前在合成数据下: 16/20 窗口不稳定
- 不稳定定义: 合成因子在不同窗口下的排名相关性 < 0.6
- 约束窗口: 35~100日
- 当前代码使用60日基准值，多窗口验证需在数据拉取后执行

**条件约束**: 35~100日窗口稳定性验证 — 需在真实数据下验证合成因子在多个窗口下的稳定性。

**预计调用数**: 48次 (4字段 × 4代码 × 3块)

---

## 4. 参数边界汇总表

| # | 参数名 | 所属因子 | 类型 | 范围/边界 | 敏感性 | 当前值 | 冻结 |
|---|---|---|---|---|---|---|---|
| 1 | ic_threshold | FACTOR-004 | float | [0.02, 0.15] | HIGH | 待验证 | 否 |
| 2 | ic_window | FACTOR-004 | int | [20, 120] | MEDIUM | 60 | 否 |
| 3 | icir_threshold | FACTOR-005 | float | [0.5, 2.0] | HIGH | N/A | 是 |
| 4 | icir_window | FACTOR-005 | int | [20, 120] | MEDIUM | 60 | 否 |
| 5 | leakage_threshold | FACTOR-006 | float | [0.001, 0.01] | HIGH | 0.005 | 是 (DSHC锁定) |
| 6 | info_score_weight | FACTOR-006 | float | [0.5, 2.0] | MEDIUM | 1.0 | 否 |
| 7 | f19_weight | FACTOR-007 | float | [0.0, 1.0] | HIGH | frozen | 是 |
| 8 | f20_weight | FACTOR-007 | float | [0.0, 1.0] | HIGH | frozen | 是 |
| 9 | cf003_weight | FACTOR-007 | float | [0.0, 1.0] | HIGH | frozen | 是 |
| 10 | decay_factor | FACTOR-007 | float | [0.01, 0.99] | MEDIUM | frozen | 是 |
| 11 | window_days | FACTOR-007 | int | [35, 100] | MEDIUM | 60 | 否 |

**敏感性分布**: HIGH: 4 / MEDIUM: 7 / LOW: 0

**冻结参数**: 6个 (icir_threshold, leakage_threshold, f19_weight, f20_weight, cf003_weight, decay_factor)
**可调节参数**: 5个 (ic_threshold, ic_window, icir_window, info_score_weight, window_days)

---

## 5. 数据字段汇总

| # | 字段名 | Wind字段 | 所属因子 | 数据类型 | 数据表 |
|---|---|---|---|---|---|
| 1 | OI | — | FACTOR-001 | numeric | Wind持仓量表 |
| 2 | OI_change | — | FACTOR-001 | numeric | Wind持仓量表 |
| 3 | sentiment_score | — | FACTOR-002 | numeric | Wind新闻舆情表 |
| 4 | search_volume | — | FACTOR-002 | numeric | Wind新闻舆情表 |
| 5 | exchange_oi | — | FACTOR-003 | numeric | Wind交易所持仓明细表 |
| 6 | long_oi | — | FACTOR-003 | numeric | Wind交易所持仓明细表 |
| 7 | short_oi | — | FACTOR-003 | numeric | Wind交易所持仓明细表 |
| 8 | IC_score | IC | FACTOR-004 | numeric | Wind因子IC计算表 |
| 9 | forecast_return | FCR | FACTOR-004 | numeric | Wind因子IC计算表 |
| 10 | realized_return | RR | FACTOR-004 | numeric | Wind因子IC计算表 |
| 11 | rolling_ICIR | — | FACTOR-005 | numeric | Wind因子ICIR计算表 |
| 12 | IC_std | — | FACTOR-005 | numeric | Wind因子ICIR计算表 |
| 13 | leakage_score | LKS | FACTOR-006 | numeric | Wind因子计算管线 |
| 14 | info_score | IFS | FACTOR-006 | numeric | Wind因子计算管线 |
| 15 | F19_score | F19 | FACTOR-007 | numeric | Wind多因子合成表 |
| 16 | F20_score | F20 | FACTOR-007 | numeric | Wind多因子合成表 |
| 17 | CF003_score | CF003 | FACTOR-007 | numeric | Wind多因子合成表 |
| 18 | decay_score | DEC | FACTOR-007 | numeric | Wind多因子合成表 |

**唯一字段数**: 18 (含日期和品种共21列)
**跨因子依赖**: 7 项 (F19/F20/CF003 三个HOLD因子为FACTOR-007的输入)

---

## 6. 指标计算公式参考

### 6.1 IC (Information Coefficient)

```
IC(t) = corr(factor_values[t-w:t], returns[t:t+1])
```

- `w`: 窗口长度 (ic_window = 60)
- 计算方法: Spearman秩相关系数
- 阈值: ic_threshold (待验证)

### 6.2 ICIR (Information Coefficient to Information Ratio)

```
ICIR(t) = mean(IC[t-w:t]) / std(IC[t-w:t])
```

- 问题: 跨窗口符号翻转 (FACTOR-005 HOLD原因)
- 建议: 使用 rolling_ICIR 辅助指标

### 6.3 G7 Leakage Score

```
G7_leakage(t) = |corr(factor_values[t], future_data[t+1:t+w])|
```

- 阈值: leakage_threshold = 0.005 (DSHC锁定)
- 超过阈值判定为潜在泄露

### 6.4 SchemeD Synthesis

```
SchemeD(t) = sum(weight_i * factor_i(t) * decay_factor^(t-t0))
```

- 权重: f19_weight, f20_weight, cf003_weight (冻结)
- 衰减: decay_factor (冻结)
- 窗口: window_days = 60 (基准)

---

## 7. 治理不变量

| 不变量 | 当前值 | 状态 |
|---|---|---|
| wind_api_calls | 0 | ✅ MAINTAINED |
| backtest_started | false | ✅ MAINTAINED |
| gate | CLOSED/HOLD | ✅ MAINTAINED |
| release_permit | NOT_ISSUED | ✅ MAINTAINED |
| F001/002/003/005 HOLD | 4/4 blocked | ✅ MAINTAINED |
| F004/006/007 CONDITIONAL | 3/3 ready (blocked on data) | ✅ MAINTAINED |

---

## 8. 文档引用关系

```
G7_FACTOR_ADJUDICATION_REPORT.md (裁决报告)
    ├── poll39_factor_leakage_risk_appendix.md (泄露风险附表)
    ├── WL006_WL014_whitelist_draft.md (白名单草案)
    ├── FL01_FL02_manual_review.md (人工复核)
    ├── P49_factor_version_diff_report.md (版本差异对比)
    ├── P49_backtest_pipeline_offline_validation.py (管道校验脚本)
    └── P49_factor_doc_supplement.md (本文档)
```

---

## 9. 附录 · 文件清单

| 文件 | 类型 | 状态 |
|---|---|---|
| `P49_factor_doc_supplement.md` | 本文档 | NEW |
| `P49_factor_version_diff_report.md` | 版本差异对比 | NEW |
| `P49_backtest_pipeline_offline_validation.py` | 管道校验脚本 | NEW |
| `P49_pipeline_validation_results.json` | 校验结果 | NEW |

---

_生成时间: 2026-10-16 GMT+8 | Agent: DSHA-P54 | Branch: feature/v88-g1_
_声明: 本文档为纯离线产物，未调用任何Wind API，未访问任何HOLD因子数据。_