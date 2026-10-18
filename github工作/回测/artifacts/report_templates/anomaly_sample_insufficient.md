# ⚠️ 异常报告: 样本量不足 · Sample Size Insufficient

<!-- TEMPLATE_ID: DSHA-P63-ANOMALY-SAMPLE-INSUFFICIENT-001 -->
<!-- TRIGGER: 回测数据量 < min_trading_days (61) 或 factor_points < 30 -->

---

## 告警级别

| 字段 | 值 |
|------|-----|
| **告警级别** | 🟡 WARNING |
| **异常类型** | SAMPLE_INSUFFICIENT |
| **触发条件** | trading_days < 61 或 factor_points < 30 |
| **生成时间** | {{generated_at}} |

---

## 问题描述

回测数据量不足以产生统计意义上的因子分析结果。

### 数据量统计

| 指标 | 实际值 | 最低要求 | 状态 |
|------|--------|----------|------|
| 交易日数 | {{trading_days}} | 61 | {{trading_days_status}} |
| 因子点数 | {{factor_points}} | 30 | {{factor_points_status}} |
| 起始日期 | {{start_date}} | - | - |
| 结束日期 | {{end_date}} | - | - |
| 数据源 | {{data_source}} | - | - |

> ⚠️ **注意**: 动量因子 (window_days=60) 最少需要 61 个交易日才能计算 1 个因子点。
> 均值回归因子 (window_days=60) 最少需要 60 个交易日。
> 波动率因子 (window_days=20) 最少需要 21 个交易日。

---

## 影响分析

| 影响项 | 影响程度 | 说明 |
|--------|----------|------|
| 因子计算 | ❌ 不可用 | 窗口不足，返回 NO_DATA 状态 |
| IC计算 | ❌ 不可用 | 最少需要 3 个因子点，30 个为统计意义门槛 |
| 夏普比率 | ⚠️ 不精确 | 数据点少，年化计算误差大 |
| 最大回撤 | ⚠️ 不精确 | 短窗口可能遗漏真实回撤 |
| 报告结论 | ❌ 无效 | 不可作为因子有效性判断依据 |

---

## 建议操作

### 立即操作

1. ✅ 检查 artifacts/sample_output/ 目录中CSV文件是否完整
2. ✅ 确认 MAX_DAYS_PER_ROUND=10 未修改 (P62触发器参数)
3. ✅ 确认 MIN_INTERVAL_SEC=12 未修改 (P62触发器参数)
4. ✅ 等待更多交易日数据积累 (10交易日/轮 × N轮)

### 后续操作

1. 确认数据完整性: 运行 `python code/p62_listener_health_check.py`
2. 数据量达标后重新运行回测:
   ```python
   import factor_data_loader, factor_constructor, backtest_skeleton
   data = factor_data_loader.load_factor_data()
   factor = factor_constructor.compute_factor_from_data(data, factor_type="momentum")
   result = backtest_skeleton.run_backtest(factor_data=factor, price_data=data)
   ```
3. 渲染报告: 使用 `backtest_report_template.md` 模板

---

## 数据积累进度

| 轮次 | 交易日 | 累计交易日 | 状态 |
|------|--------|------------|------|
| 当前 | {{trading_days}} | {{trading_days}} | ❌ 不足 |
| 目标 | ≥ 61 | ≥ 61 | ✅ 达标 |

> 按 MAX_DAYS_PER_ROUND=10 计算，需要约 {{required_rounds}} 轮采集。

---

## 安全声明

> REAL_WIND_CALL={{real_wind_call}} | WIND_API_CALLS={{wind_api_calls}}
> 本报告为离线分析产物，未调用任何 Wind API。
> GATE={{gate}} | RELEASE_PERMIT={{release_permit}}

---

> **DSHA-P63 异常模板**: 本模板为离线预构建产物，等真实回测触发对应条件时直接套用。
> 当数据量达标后，回测将自动返回 OK 状态，使用主报告模板 (backtest_report_template.md)。

_生成时间: {{generated_at}} | Agent: {{agent}} | Branch: feature/v88-g1_
