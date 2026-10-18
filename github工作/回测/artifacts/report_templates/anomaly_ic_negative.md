# 🚨 异常报告: IC显著为负 · IC Significantly Negative

<!-- TEMPLATE_ID: DSHA-P63-ANOMALY-IC-NEGATIVE-001 -->
<!-- TRIGGER: IC < 0 且 |IC| > 2 * IC_std, 或 IC_IR < 0 -->

---

## 告警级别

| 字段 | 值 |
|------|-----|
| **告警级别** | 🔴 CRITICAL |
| **异常类型** | IC_SIGNIFICANTLY_NEGATIVE |
| **触发条件** | IC < 0 且 \|IC\| > 2×IC_std，或 IC_IR < 0 |
| **生成时间** | {{generated_at}} |

---

## 问题描述

因子信息系数 (IC) 显著为负，表明因子值与未来收益率呈负相关关系。
这意味着当前因子设计可能存在方向性错误或数据泄露问题。

### IC统计

| 指标 | 值 | 参考范围 | 状态 |
|------|-----|----------|------|
| IC (信息系数) | {{ic_value}} | [-1.0, 1.0] | {{ic_status}} |
| IC_IR (信息比率) | {{icir_value}} | [-∞, +∞] | {{icir_status}} |
| IC样本数 | {{ic_sample_size}} | ≥ 30 | {{sample_status}} |
| IC标准差 | {{ic_std}} | - | - |
| 2×IC_std阈值 | {{ic_threshold_2sigma}} | - | {{threshold_status}} |

### IC时序摘要

| 指标 | 值 |
|------|-----|
| IC均值 | {{ic_mean}} |
| IC最大值 | {{ic_max}} |
| IC最小值 | {{ic_min}} |
| IC正值比例 | {{ic_positive_ratio}} |
| IC负值比例 | {{ic_negative_ratio}} |
| 连续负IC天数 | {{consecutive_negative_days}} |

---

## 影响分析

| 影响项 | 影响程度 | 说明 |
|--------|----------|------|
| 因子有效性 | ❌ 否定 | IC显著为负 = 因子方向错误 |
| 收益预测 | ❌ 失效 | 负IC = 因子值越大，未来收益越低 |
| 策略信号 | ❌ 反转 | 需反转因子方向才能产生正收益 |
| 条件通过 | ❌ 失败 | WL-A跟踪项条件验证不满足 |
| 多窗口验证 | ⚠️ 待定 | 需验证多窗口下IC一致性 |

---

## 可能原因分析

| # | 可能原因 | 概率 | 验证方法 |
|---|----------|------|----------|
| 1 | 因子方向定义错误 | 高 | 检查因子计算公式方向 |
| 2 | 数据泄露 (leakage) | 中 | 检查 G7_THRESHOLD=0.005 检测 |
| 3 | 样本选择偏差 | 中 | 检查日期范围和品种覆盖 |
| 4 | 因子衰减过快 | 低 | 检查 decay_factor 设置 |
| 5 | 市场结构变化 | 低 | 检查市场环境和行业变化 |

---

## 建议操作

### 立即操作

1. ✅ 检查 G7 信息泄漏检测: `leakage_score` 是否超过 0.005
2. ✅ 检查因子计算公式方向是否正确
3. ✅ 检查 IC 窗口设置 (ic_window=60) 是否合理
4. ✅ 运行多窗口验证 (35/60/80/100日) 确认IC一致性

### 升级操作

1. 如果 G7 检测到泄漏 → 升级 DSHC 审核，暂停因子
2. 如果方向定义错误 → 修改因子计算方向，重新回测
3. 如果多窗口不一致 → 触发 F007-ANOM-001 (排名相关性不稳定性, CRITICAL)
4. 如果连续负IC → 触发 ESCALATION，暂停F007条件验证

---

## IC方向反转建议

如果确认因子方向错误，建议反转因子方向:

```python
# 原始因子
ic_original = {{ic_value}}

# 反转后
ic_reversed = -ic_original  # 预期变为正值

# 反转因子序列
reversed_factor_values = [-v for v in factor_values]
```

> ⚠️ **注意**: 因子方向反转需经 DSHC 审核批准后方可执行。

---

## 多窗口验证要求

| 窗口 | IC值 | IC方向 | 与基准一致性 |
|------|------|--------|--------------|
| 35日 | {{ic_35d}} | {{ic_35d_direction}} | {{ic_35d_consistency}} |
| 60日 (基准) | {{ic_value}} | {{ic_direction}} | - |
| 80日 | {{ic_80d}} | {{ic_80d_direction}} | {{ic_80d_consistency}} |
| 100日 | {{ic_100d}} | {{ic_100d_direction}} | {{ic_100d_consistency}} |

> 通过标准: ≥ 3/4 窗口 IC 方向一致且 Spearman ρ ≥ 0.80

---

## 安全声明

> REAL_WIND_CALL={{real_wind_call}} | WIND_API_CALLS={{wind_api_calls}}
> 本报告为离线分析产物，未调用任何 Wind API。
> GATE={{gate}} | RELEASE_PERMIT={{release_permit}}
> G7_THRESHOLD=0.005 (DSHC冻结) | F007 window_days=60 (基准锚点)

---

> **DSHA-P63 异常模板**: 本模板为离线预构建产物，等真实回测触发对应条件时直接套用。
> CRITICAL级异常需升级DSHC审核，不可自行绕过。

_生成时间: {{generated_at}} | Agent: {{agent}} | Branch: feature/v88-g1_
