# DSHA-P49 · 对照回测框架规格 (Baseline vs Experiment)

> **文档ID**: DSHA-P49-PREP-COMPARISON  
> **生成时间**: 2026-10-19  
> **基线**: `feature/v88-g1` HEAD=`19e80cb`  
> **令牌**: DSHA-P49-PREP-TOKEN  
> **状态**: PREPARED  
> **关联**: pipeline_v2_draft.py, factor_candidate_list.md

---

## 1. 框架目标

建立**可复现、可对照、可比较**的两组回测体系:

| 组别 | 数据源 | 因子 | 策略 | 状态 |
|------|--------|------|------|------|
| **基线组** | P49原版CSV (当前) | P49原版3因子 | 等权复合 + 全仓 + 日频 | 🔒 锁定 |
| **实验组** | DSHC新数据 (待修复) | FACTOR_EXTRACT_V1 Skill | 可配置 | ⏳ 待激活 |

---

## 2. 基线组规格 (Immutable Baseline)

### 2.1 数据

| 项 | 值 | 说明 |
|---|---|---|
| CSV路径 | `output_sample/wdf_sample_metals_long.csv` | 当前7362行 |
| SHA256 | `3c14f50f063c4734950064b1072585626588e93568191d6a85767ba1699b5ed1` | 不可修改 |
| 行数 | 7362 | |
| 品种 | 6 (CU/ZN/PB/AL/SN/NI) | |
| 指标 | 4 (CLOSE/OI/SETTLE/VOL) | |
| 日期 | 2025-01-02 ~ 2026-10-19 | |
| VOL状态 | 162行, 与CLOSE零重叠 | 已知缺陷 |

### 2.2 因子

| 因子ID | 使用 | 说明 |
|--------|------|------|
| `momentum_20d` | ✅ | 20日动量 |
| `spread_cs` | ✅ | 收盘-结算价差 |
| `oi_change_rate_7d` | ✅ | OI 7日变化率 |
| 其他4因子 | ❌ | 未参与信号 |

### 2.3 信号生成

```
signal = (momentum_norm + spread_norm + oi_momentum_norm) / 3
```

- 等权复合
- z-score归一化
- 无阈值

### 2.4 执行规则

| 项 | 值 |
|---|---|
| 信号→仓位 | signal>0→Long(1), signal<0→Short(-1), signal=0→Flat(0) |
| 仓位管理 | 全仓(100%) |
| 调仓频率 | 每日 |
| 交易成本 | 0.05% per position change |
| 初始资本 | 1,000,000 |

### 2.5 锁定结果

| 指标 | 基线值 | 锁定状态 |
|------|--------|----------|
| 总收益率 (均值) | **-37.69%** | 🔒 不可修改 |
| 总收益率 (中位数) | -25.08% | 🔒 |
| 夏普比率 (均值) | -1.2980 | 🔒 |
| 夏普比率 (中位数) | -1.3227 | 🔒 |
| 最大回撤 (均值) | -42.10% | 🔒 |
| 最大回撤 (最差) | -82.81% (SN) | 🔒 |
| 胜率 (均值) | 44.68% | 🔒 |
| 盈亏比 (均值) | 0.9193 | 🔒 |

### 2.6 品种分层锁定结果

| 品种 | 收益率 | 夏普 | 回撤 | 胜率 | P/L | 交易数 |
|------|--------|------|------|------|-----|--------|
| CU | -15.96% | -0.5431 | -22.85% | 46.2% | 1.05 | 92 |
| ZN | -18.74% | -0.8159 | -27.85% | 45.5% | 1.03 | 114 |
| AL | -18.95% | -0.7761 | -24.69% | 47.2% | 0.94 | 78 |
| PB | -31.21% | -1.9484 | -32.04% | 40.5% | 0.97 | 142 |
| NI | -59.99% | -1.8294 | -62.34% | 45.2% | 0.78 | 107 |
| SN | -81.26% | -1.8748 | -82.81% | 43.5% | 0.74 | 109 |

### 2.7 基线完整性校验

每次实验组回测前, 必须验证基线完整性:

```python
# 校验清单
baseline_checks = {
    "csv_sha256": "3c14f50f063c4734950064b1072585626588e93568191d6a85767ba1699b5ed1",
    "csv_rows": 7362,
    "symbols_count": 6,
    "trading_days": 400,
    "factors_used": ["momentum_20d", "spread_cs", "oi_change_rate_7d"],
    "transaction_cost": 0.0005,
    "initial_capital": 1000000,
    "baseline_total_return_avg": -0.376868,
    "baseline_sharpe_avg": -1.297965,
}
```

---

## 3. 实验组规格 (Pending Activation)

### 3.1 前置条件 (Activation Gates)

| Gate | 条件 | 当前状态 | 阻塞项 |
|------|------|----------|--------|
| G1 | DSHC修复VOL时序对齐 | ⏳ OPEN | TODO-01 |
| G2 | FACTOR_EXTRACT_V1 Skill就绪 | ⏳ OPEN | 因子提取模块 |
| G3 | 新数据SHA256记录 | ⏳ OPEN | DSHC输出新CSV |
| G4 | comparison_config.json就绪 | ⏳ OPEN | 实验组参数 |
| G5 | DRAFT_MODE设为False | ⏳ OPEN | pipeline_v2_draft.py |

### 3.2 预期数据

| 项 | 当前 (基线) | 预期 (实验) | 变化 |
|---|---|---|---|
| CSV行数 | 7,362 | ≥7,362 | +VOL修复 |
| VOL有效行 | 0 (对齐后) | ≥380 (预期) | +380行 |
| 对齐交易日 | 400 | ≥400 | 可能增加 |
| 因子数 | 3 (信号) | 9 (信号) | +6因子 |
| 数据SHA256 | `3c14f50f...` | 新哈希 (待DSHC输出) | 变更 |

### 3.3 预期因子组合

| 实验方案 | 因子 | 权重策略 | 预期效果 |
|----------|------|----------|----------|
| Exp-A | 原3因子 + 波动率 (4因子) | 等权 | 过滤波动噪声 |
| Exp-B | 原3因子 + OI加速 (5因子) | 等权 | 增强资金流信号 |
| Exp-C | 原3因子 + 波动率 + OI加速 (6因子) | 等权 | 多维度增强 |
| Exp-D | 横截面相对强弱 (市场中性) | 排名信号 | 方向中性 |
| Exp-E | 全因子组合 + 最优权重 | 回归优化 | 最优信号 |

### 3.4 对照实验配置模板

```json
{
  "comparison_id": "DSHA-P49-CMP-001",
  "created_at": "2026-10-19",
  "status": "PENDING_ACTIVATION",
  
  "baseline_group": {
    "label": "P49原版 (锁定基线)",
    "csv_path": "output_sample/wdf_sample_metals_long.csv",
    "csv_sha256": "3c14f50f063c4734950064b1072585626588e93568191d6a85767ba1699b5ed1",
    "factors": ["momentum_20d", "spread_cs", "oi_change_rate_7d"],
    "signal_weights": [1/3, 1/3, 1/3],
    "normalization": "zscore",
    "position_strategy": "full",
    "rebalance_frequency": "daily",
    "threshold": 0.0
  },
  
  "experiment_groups": [
    {
      "id": "exp_a_volatility",
      "label": "Exp-A: 原3因子+波动率",
      "activation_gate": ["G1", "G2"],
      "csv_path": "output_sample/wdf_sample_metals_long_v2.csv",
      "extractors": [
        {"type": "builtin", "enabled": true},
        {"type": "volatility", "enabled": true, "target_vol": 0.15}
      ],
      "factors": ["momentum_20d", "spread_cs", "oi_change_rate_7d", "realized_vol_20d"],
      "signal_weights": [1/4, 1/4, 1/4, 1/4],
      "normalization": "zscore",
      "position_strategy": "full",
      "rebalance_frequency": "daily",
      "threshold": 0.0
    },
    {
      "id": "exp_b_oi_accel",
      "label": "Exp-B: 原3因子+OI加速",
      "activation_gate": ["G1", "G2"],
      "extractors": [
        {"type": "builtin", "enabled": true},
        {"type": "oi_acceleration", "enabled": true}
      ],
      "factors": ["momentum_20d", "spread_cs", "oi_change_rate_7d", "oi_change_accel_7d", "oi_slope_14d"],
      "signal_weights": [1/5, 1/5, 1/5, 1/5, 1/5],
      "normalization": "zscore",
      "position_strategy": "full",
      "rebalance_frequency": "daily",
      "threshold": 0.0
    },
    {
      "id": "exp_c_full_enhance",
      "label": "Exp-C: 原3因子+波动率+OI加速",
      "activation_gate": ["G1", "G2"],
      "extractors": [
        {"type": "builtin", "enabled": true},
        {"type": "volatility", "enabled": true, "target_vol": 0.15},
        {"type": "oi_acceleration", "enabled": true}
      ],
      "factors": [
        "momentum_20d", "spread_cs", "oi_change_rate_7d",
        "realized_vol_20d", "vol_regime_change", "oi_change_accel_7d", "oi_slope_14d"
      ],
      "signal_weights": [1/7, 1/7, 1/7, 1/7, 1/7, 1/7, 1/7],
      "normalization": "zscore",
      "position_strategy": "vol_target",
      "target_vol": 0.15,
      "rebalance_frequency": "weekly",
      "threshold": 0.3
    }
  ]
}
```

---

## 4. 对照回测执行流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    对照回测执行流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 0: 前置检查                                                │
│  ├── 验证基线CSV SHA256 一致                                     │
│  ├── 验证基线锁定指标一致                                         │
│  └── 验证实验组前置Gate状态                                       │
│                                                                 │
│  Step 1: 数据加载                                                │
│  ├── 基线组: 加载当前CSV (wdf_sample_metals_long.csv)            │
│  └── 实验组: 加载新CSV (wdf_sample_metals_long_v2.csv)           │
│                                                                 │
│  Step 2: 数据对齐                                                │
│  ├── 基线组: 400交易日, VOL=0有效                                 │
│  └── 实验组: ≥400交易日, VOL≥380有效                             │
│                                                                 │
│  Step 3: 因子提取                                                │
│  ├── 基线组: BuiltInFactorExtractor (7因子, 3用于信号)            │
│  └── 实验组: 多提取器组合 (最多11因子)                            │
│                                                                 │
│  Step 4: 信号生成                                                │
│  ├── 基线组: 等权3因子 z-score复合                                │
│  └── 实验组: 可配置因子组合 + 归一化 + 阈值                        │
│                                                                 │
│  Step 5: 仓位管理                                                │
│  ├── 基线组: 全仓 (100%)                                         │
│  └── 实验组: 波动率目标 / Kelly / 回撤控制 / 权重上限              │
│                                                                 │
│  Step 6: 调仓频率                                                │
│  ├── 基线组: 每日                                                 │
│  └── 实验组: 周度 / 双周 / 自定义间隔                              │
│                                                                 │
│  Step 7: 回测执行                                                │
│  ├── 基线组: 固定P49原始结果 (不可重算)                            │
│  └── 实验组: 重新计算, 输出JSON                                   │
│                                                                 │
│  Step 8: 对比分析                                                │
│  ├── 组合层面对比: 收益率, 夏普, 回撤, 胜率, P/L                   │
│  ├── 品种层面对比: 6品种分品种对比                                 │
│  ├── 成本对比: 交易次数, 总成本                                   │
│  └── 输出 comparison_report.md + comparison_metrics.json         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 对比分析模板

### 5.1 组合层面对比表

| 指标 | 基线组 | 实验组A | 实验组B | 实验组C | 改善度 |
|------|--------|---------|---------|---------|--------|
| 收益率 (均值) | -37.69% | TBD | TBD | TBD | — |
| 夏普 (均值) | -1.298 | TBD | TBD | TBD | — |
| 回撤 (均值) | -42.10% | TBD | TBD | TBD | — |
| 胜率 (均值) | 44.68% | TBD | TBD | TBD | — |
| 盈亏比 (均值) | 0.919 | TBD | TBD | TBD | — |
| 交易次数 (均值) | 107 | TBD | TBD | TBD | — |
| 交易成本 (估算) | 5.35% | TBD | TBD | TBD | — |

### 5.2 品种层面对比表

| 品种 | 基线收益率 | 实验组A | 实验组B | 实验组C | 最优实验组 |
|------|-----------|---------|---------|---------|-----------|
| CU | -15.96% | TBD | TBD | TBD | — |
| ZN | -18.74% | TBD | TBD | TBD | — |
| AL | -18.95% | TBD | TBD | TBD | — |
| PB | -31.21% | TBD | TBD | TBD | — |
| NI | -59.99% | TBD | TBD | TBD | — |
| SN | -81.26% | TBD | TBD | TBD | — |

### 5.3 统计分析

```python
# 对比分析代码框架 (待实验组数据就绪后执行)
def compare_results(baseline_metrics, experiment_metrics):
    """对比基线和实验组回测结果"""
    
    comparison = {}
    
    # 收益率对比
    comparison["total_return"] = {
        "baseline_avg": baseline_metrics["total_return_avg"],
        "experiment_avg": experiment_metrics["total_return_avg"],
        "delta": experiment_metrics["total_return_avg"] - baseline_metrics["total_return_avg"],
        "improvement_pct": (
            (experiment_metrics["total_return_avg"] - baseline_metrics["total_return_avg"])
            / abs(baseline_metrics["total_return_avg"]) * 100
            if baseline_metrics["total_return_avg"] != 0 else 0
        ),
    }
    
    # 夏普对比
    comparison["sharpe"] = {
        "baseline_avg": baseline_metrics["sharpe_avg"],
        "experiment_avg": experiment_metrics["sharpe_avg"],
        "delta": experiment_metrics["sharpe_avg"] - baseline_metrics["sharpe_avg"],
        "improvement": "positive" if experiment_metrics["sharpe_avg"] > baseline_metrics["sharpe_avg"] else "negative",
    }
    
    # 回撤对比
    comparison["max_drawdown"] = {
        "baseline_avg": baseline_metrics["max_drawdown_avg"],
        "experiment_avg": experiment_metrics["max_drawdown_avg"],
        "delta": experiment_metrics["max_drawdown_avg"] - baseline_metrics["max_drawdown_avg"],
        "improvement": "reduced" if experiment_metrics["max_drawdown_avg"] > baseline_metrics["max_drawdown_avg"] else "worsened",
    }
    
    # 胜率对比
    comparison["win_rate"] = {
        "baseline_avg": baseline_metrics["win_rate_avg"],
        "experiment_avg": experiment_metrics["win_rate_avg"],
        "delta": experiment_metrics["win_rate_avg"] - baseline_metrics["win_rate_avg"],
    }
    
    # 盈亏对比
    comparison["profit_loss_ratio"] = {
        "baseline_avg": baseline_metrics["profit_loss_ratio_avg"],
        "experiment_avg": experiment_metrics["profit_loss_ratio_avg"],
        "delta": experiment_metrics["profit_loss_ratio_avg"] - baseline_metrics["profit_loss_ratio_avg"],
    }
    
    # 综合评分 (自定义)
    # 归一化到0-100分
    comparison["composite_score"] = calculate_composite_score(comparison)
    
    return comparison
```

---

## 6. 输出规范

### 6.1 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 对照结果JSON | `artifacts/p49_backtest/comparison_metrics.json` | 结构化对比指标 |
| 对照报告MD | `artifacts/p49_backtest/comparison_report.md` | 人类可读对比报告 |
| 对照配置JSON | `artifacts/p49_backtest/comparison_config.json` | 实验组配置 (激活后) |
| 实验组指标 | `artifacts/p49_backtest/experiment_{id}_metrics.json` | 每组实验结果 |
| 审计日志 | `tracking_monitor_audit.jsonl` | P49-CMP审计事件 |

### 6.2 审计事件

```json
{
  "event_type": "P49_COMPARISON_RUN",
  "detail": {
    "comparison_id": "DSHA-P49-CMP-001",
    "baseline_group": "P49原版",
    "experiment_groups": ["exp_a", "exp_b", "exp_c"],
    "data_version_baseline": "SHA256=3c14f50f...",
    "data_version_experiment": "SHA256=TBD",
    "factors_baseline": ["momentum_20d", "spread_cs", "oi_change_rate_7d"],
    "factors_experiment": ["...", "..."],
    "result_status": "PENDING_ACTIVATION"
  }
}
```

---

## 7. 激活检查清单

实验组回测激活前, 逐项确认:

- [ ] **G1**: DSHC修复VOL时序对齐 (TODO-01关闭)
- [ ] **G2**: FACTOR_EXTRACT_V1 Skill就绪并部署
- [ ] **G3**: 新CSV已生成, SHA256已记录
- [ ] **G4**: comparison_config.json 实验组配置已填充
- [ ] **G5**: pipeline_v2_draft.py 中 DRAFT_MODE 设为 False
- [ ] **G6**: 基线锁定指标已验证一致 (SHA256 + 回测结果)
- [ ] **G7**: 新数据行数/品种数/日期范围已校验
- [ ] **G8**: 新因子提取结果已验证 (因子数量, 有效行数)
- [ ] **G9**: 交易成本参数已确认 (维持0.05%)
- [ ] **G10**: 初始资本已确认 (维持1,000,000)

---

## 8. 与P49原版的关系

```
P49原版 (feature/v88-g1, commit 4b4360b)
  │
  ├── P49-SUMMARY 复盘 (commit 19e80cb)
  │     └── factor_candidate_list.md (因子备选库)
  │     └── pipeline_v2_draft.py (流水线改造草案)
  │     └── comparison_framework.md (对照框架 ← 本文档)
  │     └── optimization_params.json (备选参数)
  │     └── MANIFEST.json (资产清单, 已更新)
  │
  └── P49-PREP 准备 (本阶段)
        └── comparison_framework.md (对照框架)
        └── comparison_config.json (实验配置, 待填充)
        └── pipeline_v2_draft.py (草稿, DRAFT_MODE=True)
```

**关键原则**: 
- 基线组结果 **不可重算、不可修改** (P49原版锁定)
- 实验组完全独立, 可独立配置
- 所有对照组共享同一套回测引擎 (run_backtest_v2)
- 对比分析自动化, 人工审核结论

---

> **下一步**: 等待DSHC输出VOL对齐新数据 + FACTOR_EXTRACT_V1 Skill就绪, 填充comparison_config.json实验组配置后激活
