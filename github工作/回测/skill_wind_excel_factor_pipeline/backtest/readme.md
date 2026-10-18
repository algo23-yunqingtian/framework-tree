# Skill: Wind Excel Factor Pipeline — Backtest Module (P61)

> **DSHA-P61 · 回测输出标准化**
> 基线: `feature/v88-g1 @ cb56f1c`
> 关联模块: `code/backtest_skeleton.py`
> 上游: factor_data_loader → factor_constructor
> 下游: artifacts/backtest_archive/

---

## 1. 标准化输出规格

每次回测自动生成 **5类文件 + 自动归档**:

| # | 文件类型 | 格式 | 用途 |
|---|----------|------|------|
| 1 | Markdown摘要 | `.md` | 人工可读的回测报告 |
| 2 | JSON结果 | `.json` | 完整结构化数据 |
| 3 | 指标表格 | `.csv` | 仪表盘/Excel读取 |
| 4 | 时序净值 | `.csv` | 净值曲线可视化 |
| 5 | 快照 | `.json` | 仪表盘直接读取 |
| 6 | 归档 | 目录 | 历史结果防覆盖 |

## 2. 指标表格 CSV 规格

### 2.1 核心指标定义

| 指标名 | 计算公式 | 单位 | 说明 |
|--------|----------|------|------|
| `total_return` | (P_end - P_start) / P_start | % | 总收益率 |
| `annualized_return` | (1 + total_return)^(252/n) - 1 | % | 年化收益率 |
| `annual_volatility` | std(daily_returns) × √252 | % | 年化波动率 |
| `daily_volatility` | std(daily_returns) | % | 日均波动率 |
| `max_drawdown` | min(P_t / max(P_0..P_t) - 1) | % | 最大回撤 |
| `sharpe_ratio` | (mean_r - rf/252) / std_r × √252 | - | 夏普比率 |
| `information_coefficient` | corr(factor_t, forward_return_{t+1}) | - | 信息系数(IC) |
| `IC_IR` | IC × √n | - | IC信息比率 |

### 2.2 IC计算说明

IC (Information Coefficient) 衡量因子值与未来收益率的相关性:

```
IC = Pearson_Corr(factor_values, forward_returns)

forward_returns[i] = equity[i+1] / equity[i] - 1
```

- `IC > 0`: 因子值越高，未来收益越高（正向因子）
- `IC < 0`: 因子值越高，未来收益越低（反向因子）
- `IC ≈ 0`: 因子无预测能力

## 3. 时序净值 CSV 规格

每行对应一个交易日，包含完整的净值跟踪数据:

| 列 | 类型 | 说明 |
|----|------|------|
| `date` | YYYY-MM-DD | 交易日 |
| `close_price` | float | 当日收盘价 |
| `factor_value` | float / 空 | 因子值（对齐后，前N行为空） |
| `daily_return` | float / 空 | 日收益率 = (P_t - P_{t-1}) / P_{t-1} |
| `cumulative_return` | float / 空 | 累计收益率（从首日开始复合） |
| `net_value` | float | 净值 = initial_capital × (1 + cumulative_return) |

## 4. 快照 JSON 规格

快照专为仪表盘设计，包含精简的指标摘要:

```json
{
  "snapshot_id": "BT-{YYYYMMDDHHMMSS}-{FACTOR_TYPE_ABBR}",
  "created_at": "ISO8601时间戳",
  "status": "OK | WAIT | ERROR",
  "metadata": { /* 回测参数 */ },
  "metrics": { /* 核心指标 */ },
  "factor_stats": { /* 因子分布 */ },
  "equity_curve_summary": { /* 净值摘要 */ },
  "data_provenance": { /* 数据来源 */ },
  "safety": { "real_wind_call": false, "wind_api_calls": 0 },
  "archive_info": { /* 归档路径 */ }
}
```

## 5. 自动归档机制

### 5.1 归档目录结构

```
artifacts/backtest_archive/
└── {YYYYMMDD_HHMMSS}_{factor_type}_{symbol}/
    ├── MANIFEST.json
    ├── backtest_metrics_*.csv
    ├── net_value_series_*.csv
    ├── backtest_snapshot_*.json
    ├── backtest_*.md
    └── backtest_*.json
```

### 5.2 防覆盖保证

- 每次回测使用独立时间戳目录，不会覆盖历史结果
- MANIFEST.json 记录完整归档清单，便于追溯
- 归档为文件复制（非移动），原始输出保留在 `code/backtest_output/`

## 6. 接口说明

### 6.1 核心函数

| 函数 | 用途 | 返回值 |
|------|------|--------|
| `run_backtest(factor_data, price_data)` | 执行回测计算 | 结果字典 |
| `save_backtest_result(result)` | 完整保存 (5文件+归档) | 文件路径字典 |
| `save_backtest_metrics_csv(result)` | 单独保存指标CSV | 文件路径 |
| `save_net_value_series_csv(result)` | 单独保存净值CSV | 文件路径 |
| `save_backtest_snapshot_json(result)` | 单独保存快照JSON | 文件路径 |
| `archive_backtest_result(files, result)` | 单独执行归档 | 归档目录路径 |
| `compute_IC(factor_values, forward_returns)` | 计算信息系数 | (IC, IC_IR, n) |
| `_compute_ic_from_result(result)` | 从结果提取IC | (IC, IC_IR, n) |
| `_annualized_return(result)` | 计算年化收益率 | float |

### 6.2 返回值结构

`save_backtest_result()` 返回:

```python
{
    "md": "path/to/backtest_*.md",
    "json": "path/to/backtest_*.json",
    "metrics_csv": "path/to/backtest_metrics_*.csv",
    "net_value_csv": "path/to/net_value_series_*.csv",
    "snapshot_json": "path/to/backtest_snapshot_*.json",
    "archive_dir": "path/to/backtest_archive/{timestamp}/"
}
```

## 7. 安全约束

| 约束 | 值 | 说明 |
|------|-----|------|
| `REAL_WIND_CALL` | `False` | 不触发任何Wind API |
| `WIND_API_CALLS` | `0` | 零Wind调用 |
| 数据源 | 离线CSV | 仅使用本地数据 |
| 输出编码 | UTF-8 / UTF-8-SIG | CSV使用BOM兼容Excel |

## 8. 测试覆盖

| 测试项 | 数量 | 说明 |
|--------|------|------|
| WAIT状态 | 2 | 无输入 + 只有价格 |
| OK状态 | 1 | 完整回测 |
| MD/JSON保存 | 1 | 基础输出 |
| 波动率因子 | 1 | 第二种因子类型 |
| WAIT Markdown | 1 | WAIT状态输出 |
| **P61 指标CSV** | 1 | 34行指标表格 |
| **P61 净值CSV** | 1 | 时序净值 |
| **P61 快照JSON** | 1 | 仪表盘快照 |
| **P61 完整保存** | 1 | 5文件+归档+清单 |
| **IC计算** | 1 | 信息系数验证 |
| **年化收益率** | 1 | 年化计算验证 |
| **合计** | **12** | **全部通过** |
