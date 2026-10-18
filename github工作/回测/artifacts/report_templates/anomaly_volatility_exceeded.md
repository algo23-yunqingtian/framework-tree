# 🚨 异常报告: 回测波动率超限 · Backtest Volatility Exceeded

<!-- TEMPLATE_ID: DSHA-P63-ANOMALY-VOLATILITY-EXCEEDED-001 -->
<!-- TRIGGER: annual_volatility > 0.60 (60%) 或 daily_volatility > 0.0378 (3.78%) -->

---

## 告警级别

| 字段 | 值 |
|------|-----|
| **告警级别** | 🔴 CRITICAL |
| **异常类型** | VOLATILITY_EXCEEDED |
| **触发条件** | annual_volatility > 60% 或 daily_volatility > 3.78% |
| **生成时间** | {{generated_at}} |

---

## 问题描述

回测组合的波动率超出合理范围，表明因子在极端市场条件下可能产生
过大的仓位偏移或收益预测不稳定。

### 波动率统计

| 指标 | 实际值 | 上限阈值 | 状态 |
|------|--------|----------|------|
| 年化波动率 | {{annual_volatility}} | 60% | {{annual_vol_status}} |
| 日均波动率 | {{daily_volatility}} | 3.78% | {{daily_vol_status}} |
| 最大回撤 | {{max_drawdown}} | -20% | {{max_dd_status}} |
| 夏普比率 | {{sharpe_ratio}} | - | {{sharpe_status}} |

### 波动率分布

| 指标 | 值 |
|------|-----|
| 日均波动率 (前25%分位) | {{daily_vol_p25}} |
| 日均波动率 (50%分位) | {{daily_vol_p50}} |
| 日均波动率 (75%分位) | {{daily_vol_p75}} |
| 波动率最大值 | {{daily_vol_max}} |
| 波动率最小值 | {{daily_vol_min}} |
| 连续高波动天数 | {{consecutive_high_vol_days}} |

---

## 影响分析

| 影响项 | 影响程度 | 说明 |
|--------|----------|------|
| 风险控制 | ❌ 失效 | 波动率超限 = 仓位管理失控 |
| 收益稳定性 | ❌ 不稳定 | 高波动 = 收益波动剧烈 |
| 夏普比率 | ❌ 低下 | 高波动压低夏普比率 |
| 最大回撤 | ⚠️ 恶化 | 高波动通常伴随深回撤 |
| 条件通过 | ❌ 失败 | WL-A跟踪项条件验证不满足 |

---

## 可能原因分析

| # | 可能原因 | 概率 | 验证方法 |
|---|----------|------|----------|
| 1 | 因子值异常 (极端因子值) | 高 | 检查因子值分布 z-score |
| 2 | 价格数据异常 (价格跳变) | 中 | 检查价格序列日变化率 |
| 3 | 窗口参数不当 | 中 | 检查 window_days 设置 |
| 4 | 因子权重失衡 | 低 | 检查 SchemeD 权重分配 |
| 5 | 市场极端行情 | 低 | 检查日期范围市场环境 |

---

## 建议操作

### 立即操作

1. ✅ 检查因子值分布: 是否存在 z-score > 3 的极端值
2. ✅ 检查价格数据: 是否存在日变化率 > 5% 的异常跳变
3. ✅ 检查窗口参数: window_days 是否在验证范围内 (35~100)
4. ✅ 检查清洗规则: 是否已应用 z-score 归一化

### 异常值处理

根据 P49_FACTOR_CLEANING_SPEC.json 中的清洗规则:

| 规则ID | 方法 | 阈值 | 动作 |
|--------|------|------|------|
| F001-CLN-003 | z_score | z=3.0 | cap_at_3sigma |
| F001-CLN-004 | iqr | 1.5×IQR | cap_at_iqr_bound |
| F004-CLN-004 | z_score | z=3.0 | exclude_row |
| F004-CLN-006 | absolute | >0.05 | exclude_row |

> 建议: 对所有因子值执行 z-score 截尾 (cap_at_3sigma)，
> 对价格日变化率 > 5% 的异常行执行 exclude_row。

### 升级操作

1. 如果清洗率 > 95% → 触发 F003-ANOM-001 (100%坏样本清洗率预警, CRITICAL)
2. 如果最大回撤 > 40% → 触发方向不一致性检查 (F007-ANOM-002, CRITICAL)
3. 如果连续高波动 → 检查是否为市场结构性变化
4. 如果所有因子均超限 → 升级 DSHC 审核，暂停因子回测

---

## 波动率对比

| 品种 | 年化波动率 | 日均波动率 | 夏普比率 | 状态 |
|------|------------|------------|----------|------|
| {{symbol}} | {{annual_volatility}} | {{daily_volatility}} | {{sharpe_ratio}} | ⚠️ 超限 |
| LI.SHF (参考) | ~20% | ~1.25% | ~0.5 | 正常 |
| NI.SHF (参考) | ~25% | ~1.56% | ~0.4 | 正常 |
| CU.SHF (参考) | ~15% | ~0.94% | ~0.6 | 正常 |
| ZN.SHF (参考) | ~20% | ~1.25% | ~0.5 | 正常 |

---

## 波动率控制建议

### 短期

```
1. 降低因子仓位: 使用波动率目标化 (volatility targeting)
2. 增加清洗规则: 对所有因子值执行 z-score 截尾
3. 延长窗口: 从 window_days=60 增加到 80 或 100
```

### 中期

```
1. 引入波动率因子作为对冲信号
2. 实现动态仓位管理 (基于实时波动率)
3. 设定最大回撤止损线 (如 -15%)
```

### 长期

```
1. 优化 SchemeD 权重分配 (需 DSHC 审核)
2. 引入多品种分散化 (LI/NI/ZN/CU)
3. 增加风险预算管理
```

---

## 安全声明

> REAL_WIND_CALL={{real_wind_call}} | WIND_API_CALLS={{wind_api_calls}}
> 本报告为离线分析产物，未调用任何 Wind API。
> GATE={{gate}} | RELEASE_PERMIT={{release_permit}}
> MAX_DAYS_PER_ROUND=10 | MIN_INTERVAL_SEC=12 | G7_THRESHOLD=0.005

---

> **DSHA-P63 异常模板**: 本模板为离线预构建产物，等真实回测触发对应条件时直接套用。
> CRITICAL级异常需升级DSHC审核，不可自行绕过。
> 波动率控制建议仅供参考，实际执行需 DSHC 批准。

_生成时间: {{generated_at}} | Agent: {{agent}} | Branch: feature/v88-g1_
