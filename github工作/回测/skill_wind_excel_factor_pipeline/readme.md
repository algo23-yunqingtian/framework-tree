# Skill: Wind Excel Factor Pipeline — 完整流水线文档

> **DSHA-P61 · 流水线固化**
> 基线: `feature/v88-g1 @ cb56f1c`
> 状态: STATIC_STANDBY · gate=CLOSED/HOLD · release_permit=NOT_ISSUED
> 全流程: 采集 → 自动触发 → 因子计算 → 回测 → 结果归档
> 零Wind调用 · 零人工干预（人工仅创建marker + 开启REAL_WIND_CALL）

---

## 目录

1. [快速导入 (Quick Start)](#1-快速导入-quick-start)
2. [完整调用链路](#2-完整调用链路)
3. [P61 标准化输出格式](#3-p61-标准化输出格式)
4. [安全红线与保护机制](#4-安全红线与保护机制)
5. [文件清单与目录结构](#5-文件清单与目录结构)
6. [部署检查清单](#6-部署检查清单)
7. [故障排除](#7-故障排除)
8. [模块文档索引](#8-模块文档索引)

---

## 1. 快速导入 (Quick Start)

### 1.1 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | ≥3.8 | 标准库即可，无需第三方包 |
| Windows | ≥10 | Excel COM 接口依赖 |
| Excel | 已安装 | Wind WSS/WSD 公式引擎 |
| Git | ≥2.0 | 版本控制 |

### 1.2 一键导入

```bash
# 1. Clone 或拉取仓库
git clone <repo-url> && cd 回测

# 2. 确认代码完整性 (5个核心模块)
python -c "
import sys; sys.path.insert(0, 'code')
import factor_data_loader, factor_constructor, backtest_skeleton
import prototype_wss_assemble_sim, sample_data_trigger
print('✅ 5个核心模块全部就位')
print(f'REAL_WIND_CALL={factor_data_loader.REAL_WIND_CALL}')
print(f'wind_api_calls={factor_data_loader.WIND_API_CALLS}')
"

# 3. 运行仿真自测
python code/backtest_skeleton.py    # 12项测试
python code/factor_data_loader.py   # 6项测试
python code/factor_constructor.py   # 7项测试
python code/sample_data_trigger.py  # 触发器自测
```

### 1.3 首次运行 (仿真模式)

```bash
# 触发器自动扫描 artifacts/sample_output/ 下的CSV
python code/sample_data_trigger.py

# 如果有CSV → 自动执行:
#   数据加载 → 因子计算 → 回测 → 结果保存 → 自动归档
# 输出目录:
#   code/backtest_output/          — 实时输出
#   artifacts/backtest_archive/    — 自动归档
```

### 1.4 真实数据运行 (需人工许可)

```bash
# 步骤1: 创建许可文件 (必须由DSHC人工执行)
New-Item -ItemType File artifacts\sample_fetch_allow.marker

# 步骤2: 开启REAL_WIND_CALL (必须由DSHC人工编辑)
# 编辑 code/prototype_wss_assemble_sim.py
# 将 REAL_WIND_CALL = False 改为 REAL_WIND_CALL = True

# 步骤3: 执行WSS小样采集
python code/prototype_wss_assemble_sim.py

# 步骤4: 采集完成后CSV自动落地到 artifacts/sample_output/
# 步骤5: 触发器自动运行因子+回测
python code/sample_data_trigger.py
```

---

## 2. 完整调用链路

### 2.1 全景调用链

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      完整流水线调用链 (7阶段)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  阶段A: 人工许可                                                            │
│  ──────────────────────────────────────────────────────────────            │
│  ① 创建 marker → artifacts/sample_fetch_allow.marker                       │
│  ② 开启开关 → REAL_WIND_CALL = True                                        │
│  ③ 执行采集 → python code/prototype_wss_assemble_sim.py                    │
│                                                                             │
│  阶段B: WSS 小样采集 (P57/P58/P60 三重保护)                                  │
│  ──────────────────────────────────────────────────────────────            │
│  prototype_wss_assemble_sim.py                                              │
│    ├─ Final-Lock 4道断言 (marker + REAL_WIND_CALL + MAX_DAYS + MIN_INTERVAL)│
│    ├─ P57 三重COM防锁 (前置检查 + 强制回收 + 兜底自检)                        │
│    ├─ P60 Excel 多实例隔离 (USER_INSTANCE保护 + Agent PID管理)               │
│    └─ 输出: artifacts/sample_output/*.csv (双落地: code/sim_output/同步)     │
│                                                                             │
│  阶段C: 自动回调触发 (SHA256哈希锁)                                          │
│  ──────────────────────────────────────────────────────────────            │
│  sample_data_trigger.py                                                     │
│    ├─ check_new_csv_files() — SHA256对比检测新/修改CSV                       │
│    ├─ 无新文件 → 返回WAIT (不做任何计算, 防重复触发)                           │
│    └─ 有新文件 → run_pipeline_for_csv()                                     │
│                                                                             │
│  阶段D: 因子数据加载                                                         │
│  ──────────────────────────────────────────────────────────────            │
│  factor_data_loader.load_factor_data(data_path=csv_path)                   │
│    ├─ CSV读取 (utf-8-sig BOM兼容)                                           │
│    ├─ 数据校验 (空值/重复时间戳/异常值 z-score)                               │
│    └─ 标准化输出 {dates, values, symbol, indicator, metadata}               │
│                                                                             │
│  阶段E: 因子计算                                                            │
│  ──────────────────────────────────────────────────────────────            │
│  factor_constructor.compute_factor_from_data(data, factor_type)            │
│    ├─ 参数基线校验 (F007 window_days=60)                                    │
│    ├─ 因子选择: momentum / volatility / mean_reversion                       │
│    └─ 输出: factor_values[], factor_dates[], factor_stats                   │
│                                                                             │
│  阶段F: 回测计算                                                            │
│  ──────────────────────────────────────────────────────────────            │
│  backtest_skeleton.run_backtest(factor_data, price_data)                   │
│    ├─ 前置校验 (数据就绪检查 → WAIT/READY)                                   │
│    ├─ 指标计算: 累计收益/年化波动率/最大回撤/夏普比率/IC                        │
│    ├─ 因子统计: 均值/标准差/分位数/正负比例                                    │
│    └─ 输出: 回测结果字典 (status=OK/WAIT/ERROR)                              │
│                                                                             │
│  阶段G: P61 标准化输出 + 自动归档                                            │
│  ──────────────────────────────────────────────────────────────            │
│  backtest_skeleton.save_backtest_result(result)                             │
│    ├─ (1) Markdown 摘要 → code/backtest_output/*.md                        │
│    ├─ (2) JSON 结果 → code/backtest_output/*.json                          │
│    ├─ (3) 指标表格 CSV → backtest_metrics_*.csv                             │
│    ├─ (4) 时序净值 CSV → net_value_series_*.csv                             │
│    ├─ (5) 快照 JSON → backtest_snapshot_*.json                             │
│    └─ (6) 自动归档 → artifacts/backtest_archive/{timestamp}/                │
│          ├─ 所有5类文件复制归档                                              │
│          └─ MANIFEST.json 归档清单                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
artifacts/sample_output/*.csv
        │
        ▼
  ┌───────────────────┐
  │ factor_data_loader │ ← CSV读取 + 数据校验 + 标准化
  └────────┬──────────┘
           │
           ▼
  ┌───────────────────┐
  │ factor_constructor │ ← 参数基线校验 + 因子计算
  └────────┬──────────┘
           │
           ▼
  ┌───────────────────┐
  │ backtest_skeleton  │ ← 回测指标 + IC计算
  └────────┬──────────┘
           │
           ▼
  ┌──────────────────────────────────────────────────┐
  │ save_backtest_result() — P61 标准化输出           │
  │                                                  │
  │  ┌──────────┐  ┌──────────────┐  ┌──────────┐  │
  │  │ metrics  │  │  net_value   │  │ snapshot │  │
  │  │   .csv   │  │    .csv      │  │   .json  │  │
  │  └──────────┘  └──────────────┘  └──────────┘  │
  │        │              │               │         │
  │        └──────────────┼───────────────┘         │
  │                       ▼                         │
  │            ┌──────────────────┐                 │
  │            │ 自动归档 (zip)    │                 │
  │            │ artifacts/       │                 │
  │            │ backtest_archive │                 │
  │            │ /{timestamp}/    │                 │
  │            └──────────────────┘                 │
  └──────────────────────────────────────────────────┘
```

---

## 3. P61 标准化输出格式

### 3.1 指标表格 CSV (backtest_metrics_*.csv)

| 列名 | 说明 | 示例 |
|------|------|------|
| `metric_name` | 指标名称 | `total_return` |
| `value` | 指标值 (字符串) | `-0.006772` |
| `unit` | 单位 | `%`, `days`, `-`, `ISO8601` |
| `description` | 中文描述 | `总收益率` |

**核心指标清单**:

| 分类 | 指标 | 说明 |
|------|------|------|
| 基础 | `factor_type`, `factor_id`, `symbol`, `indicator`, `data_source` | 回测元数据 |
| 基础 | `trading_days`, `factor_points`, `start_date`, `end_date` | 数据范围 |
| 收益 | `total_return`, `annualized_return` | 总收益 + 年化收益 |
| 风险 | `annual_volatility`, `daily_volatility`, `max_drawdown` | 波动率 + 最大回撤 |
| 风险调整 | `sharpe_ratio` | 夏普比率 |
| 因子效率 | `information_coefficient`, `IC_IR`, `IC_sample_size` | 信息系数 + IC信息比率 |
| 因子统计 | `factor_mean`, `factor_std`, `factor_min`, `factor_max` | 分布统计 |
| 因子统计 | `factor_p25`, `factor_p50`, `factor_p75` | 分位数 |
| 因子统计 | `positive_ratio`, `negative_ratio` | 正负比例 |
| 安全 | `real_wind_call`, `wind_api_calls`, `timestamp` | 安全状态 + 时间戳 |

### 3.2 时序净值 CSV (net_value_series_*.csv)

| 列名 | 类型 | 说明 |
|------|------|------|
| `date` | YYYY-MM-DD | 交易日 |
| `close_price` | float | 收盘价 |
| `factor_value` | float / 空 | 因子值 (对齐后) |
| `daily_return` | float / 空 | 日收益率 |
| `cumulative_return` | float / 空 | 累计收益率 |
| `net_value` | float | 净值 (基于 initial_capital=100000) |

**示例**:
```csv
date,close_price,factor_value,daily_return,cumulative_return,net_value
2025-01-07,24451.21,0.004999,0.002633,0.002633,100263.30
2025-01-08,24839.20,0.007842,0.015868,0.018585,101858.50
...
```

### 3.3 快照 JSON (backtest_snapshot_*.json)

用于仪表盘直接读取，结构精简：

```json
{
  "snapshot_id": "BT-20261018132234-MOM",
  "created_at": "2026-10-18T13:22:34+00:00",
  "status": "OK",
  "metadata": {
    "factor_type": "momentum",
    "factor_id": "TEST-MOM",
    "symbol": "ZN.SHF",
    "indicator": "close",
    "data_source": "SIMULATED (NOT REAL)",
    "start_date": "2025-01-07",
    "end_date": "2025-01-15",
    "trading_days": 7,
    "factor_points": 7,
    "config": {"risk_free_rate": 0.0, "initial_capital": 100000.0}
  },
  "metrics": {
    "total_return": -0.006772,
    "annualized_return": -0.217011,
    "annual_volatility": 0.037796,
    "daily_volatility": 0.0023809,
    "max_drawdown": -0.007245,
    "sharpe_ratio": -7.5282,
    "information_coefficient": 0.123456,
    "IC_IR": 0.345678,
    "IC_sample_size": 5
  },
  "factor_stats": {
    "count": 7,
    "mean": 0.001234,
    "std": 0.005678,
    "min": -0.002345,
    "max": 0.005678,
    "p25": -0.001111,
    "p50": 0.001234,
    "p75": 0.003456,
    "positive_ratio": 0.5714,
    "negative_ratio": 0.4286
  },
  "equity_curve_summary": {
    "length": 7,
    "start_value": 24451.21,
    "end_value": 24542.72,
    "preview_first5": [24451.21, 24839.20, 24671.22, 24503.95, 24526.34]
  },
  "data_provenance": {
    "price_source": "SIMULATED (NOT REAL)",
    "price_status": "OK",
    "price_metadata": {},
    "factor_data_source": "SIMULATED (NOT REAL)"
  },
  "safety": {
    "real_wind_call": false,
    "wind_api_calls": 0
  },
  "archive_info": {
    "archive_dir": "artifacts/backtest_archive/20261018_132234_momentum_ZN.SHF",
    "archive_id": "20261018_132234_momentum_ZN.SHF"
  }
}
```

### 3.4 自动归档

每次回测完成后，所有5类文件自动归档到时间戳目录：

```
artifacts/backtest_archive/
└── 20261018_132234_momentum_ZN.SHF/
    ├── MANIFEST.json                          ← 归档清单
    ├── backtest_metrics_momentum_ZN.SHF_*.csv  ← 指标表格
    ├── net_value_series_momentum_ZN.SHF_*.csv  ← 时序净值
    ├── backtest_snapshot_momentum_ZN.SHF_*.json ← 快照
    ├── backtest_momentum_ZN.SHF_*.md           ← Markdown摘要
    └── backtest_momentum_ZN.SHF_*.json         ← 完整JSON
```

**MANIFEST.json** 包含归档ID、时间戳、文件清单、安全状态。

---

## 4. 安全红线与保护机制

### 4.1 不可修改常量

| 常量 | 值 | 文件 | 说明 |
|------|-----|------|------|
| `REAL_WIND_CALL` | `False` | 所有模块 | 禁止Agent修改为True |
| `MAX_DAYS_PER_ROUND` | `10` | `prototype_wss_assemble_sim.py` | 单次最大交易日 |
| `MIN_INTERVAL_SEC` | `12` | `prototype_wss_assemble_sim.py` | 最小请求间隔 |
| `SIM_DATA_POINTS` | `10` | `prototype_wss_assemble_sim.py` | 模拟数据点 |
| `COM_HANG_TIMEOUT_SEC` | `30` | `prototype_wss_assemble_sim.py` | COM卡死超时 |
| `COM_HANG_KILL_ONLY_AGENT` | `True` | `prototype_wss_assemble_sim.py` | 仅终止Agent实例 |

### 4.2 Final-Lock 4道断言 (P58)

| 断言 | 检查内容 | 失败行为 |
|------|----------|----------|
| FINAL-LOCK-1 | `artifacts/sample_fetch_allow.marker` 存在 | AssertionError → 拒绝执行 |
| FINAL-LOCK-2 | `REAL_WIND_CALL is True` | AssertionError → 拒绝执行 |
| FINAL-LOCK-3 | `MAX_DAYS_PER_ROUND == 10` | AssertionError → 拒绝执行 |
| FINAL-LOCK-4 | `MIN_INTERVAL_SEC == 12` | AssertionError → 拒绝执行 |

> ⚠️ **禁止注释、临时屏蔽或绕过这四道锁。** 真实调用需同时满足 marker存在 + REAL_WIND_CALL=True。

### 4.3 Excel 实例隔离 (P60)

| 实例类型 | 标识 | Agent行为 |
|----------|------|-----------|
| USER_INSTANCE | `USER_INSTANCE_EXCEL` | 不读取、不操作、不终止 |
| AGENT_INSTANCE | `DSHA_P60_AGENT_EXCEL` | 可释放、可终止 |

**隔离流程**: 识别用户实例 → 创建隔离Agent实例 → 正常WSS查询 → 正常路径:COM释放 / 异常路径:仅杀Agent

**安全机制**: `_kill_agent_excel_only()` 含安全检查 — 若 `agent_pid in user_pids` 则拒绝终止。

### 4.4 防重复触发 (SHA256哈希锁)

| 文件 | 用途 |
|------|------|
| `.trigger_state.json` | 记录已处理CSV的SHA256哈希 |
| `trigger_run_log.jsonl` | 触发器运行审计日志 |

**机制**: 每次扫描CSV文件时计算SHA256，与状态文件对比。已处理的文件不重复触发。

### 4.5 Agent 禁止操作

| 操作 | 原因 |
|------|------|
| ❌ 创建 `sample_fetch_allow.marker` | 必须由DSHC人工执行 |
| ❌ 修改 `REAL_WIND_CALL` 为True | 必须由DSHC人工编辑 |
| ❌ 注释/禁用Final-Lock断言 | 安全锁不可绕过 |
| ❌ 修改 MAX_DAYS / MIN_INTERVAL | 硬限制保护 |
| ❌ 读取用户Excel数据 | 实例隔离保护 |
| ❌ 终止用户Excel进程 | 实例隔离保护 |

---

## 5. 文件清单与目录结构

### 5.1 核心代码模块

| 文件 | 阶段 | 说明 |
|------|------|------|
| `code/prototype_wss_assemble_sim.py` | A/B | WSS采集原型 + P57 COM防锁 + P60实例隔离 |
| `code/sample_data_trigger.py` | C | 小样CSV落地自动回调触发器 |
| `code/factor_data_loader.py` | D | 离线因子数据加载 + 数据校验 |
| `code/factor_constructor.py` | E | 基础因子构造 (momentum/volatility/mean_reversion) |
| `code/backtest_skeleton.py` | F/G | 回测框架 + P61标准化输出 + 自动归档 |

### 5.2 输出目录

| 目录 | 说明 |
|------|------|
| `artifacts/sample_output/` | 小样CSV落地目录 (输入) |
| `code/sim_output/` | 仿真输出同步目录 |
| `code/backtest_output/` | 回测实时输出 (MD + JSON + CSV + 快照) |
| `code/factor_offline_result/` | 因子计算结果 |
| `artifacts/backtest_archive/` | 回测自动归档 (P61新增) |
| `artifacts/wss_sample_run.log` | WSS主运行日志 |
| `artifacts/wss_small_sample_alerts.jsonl` | COM告警日志 |
| `artifacts/sample_output/trigger_run_log.jsonl` | 触发器运行日志 |
| `artifacts/sample_output/.trigger_state.json` | 触发器状态文件 (SHA256哈希锁) |

### 5.3 审计日志

| 文件 | 说明 |
|------|------|
| `tracking_monitor_audit.jsonl` | 项目级审计事件 |
| `data-harbor/dsha_p49_prep/P49_backtest_audit/wind_excel_events.jsonl` | Wind Excel事件日志 |

---

## 6. 部署检查清单

### 6.1 环境检查

```bash
# 1. Python版本
python --version  # ≥3.8

# 2. 核心模块完整性
python -c "
import sys; sys.path.insert(0, 'code')
import factor_data_loader, factor_constructor, backtest_skeleton
import prototype_wss_assemble_sim, sample_data_trigger
print('✅ 5个核心模块全部就位')
"

# 3. 安全常量验证
python -c "
import sys; sys.path.insert(0, 'code')
import factor_data_loader, factor_constructor, backtest_skeleton
import prototype_wss_assemble_sim, sample_data_trigger
assert factor_data_loader.REAL_WIND_CALL is False
assert factor_data_loader.WIND_API_CALLS == 0
assert prototype_wss_assemble_sim.MAX_DAYS_PER_ROUND == 10
assert prototype_wss_assemble_sim.MIN_INTERVAL_SEC == 12
print('✅ 安全常量全部锁定')
"
```

### 6.2 自测验证

```bash
# 运行全部模块自测
python code/factor_data_loader.py   # 6项测试
python code/factor_constructor.py   # 7项测试
python code/backtest_skeleton.py    # 12项测试
python code/sample_data_trigger.py  # 触发器自测
```

### 6.3 全流程仿真测试

```bash
# 使用P59内置仿真CSV数据完整跑一遍全链路
# (需要 artifacts/sample_output/ZN.SHF_close_simulated.csv 存在)
python code/sample_data_trigger.py

# 验证输出:
# 1. Excel不干扰前台人工窗口 ✅
# 2. 新文件自动触发回测 ✅
# 3. 输出文件格式统一 (3类CSV/JSON) ✅
# 4. 无重复执行 (SHA256哈希锁) ✅
# 5. 自动归档到 artifacts/backtest_archive/ ✅
```

---

## 7. 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 触发器返回WAIT | 无新CSV文件或数据不足 | 确认CSV在 `artifacts/sample_output/` 且数据点 > window_days |
| 因子返回NO_DATA | window_days=60但数据点<61 | 使用 `params={"window_days": 5}` 覆盖或等待更多数据 |
| 回测返回WAIT | 因子或价格数据缺失 | 检查 `check_inputs()` 输出，确认数据对齐 |
| COM异常/卡死 | Excel COM不稳定 | P57三重防锁 + P60 Agent-only kill 自动处理 |
| Final-Lock AssertionError | marker不存在或REAL_WIND_CALL=False | 由DSHC人工创建marker + 开启REAL_WIND_CALL |
| 重复触发 | SHA256未更新 | 检查 `.trigger_state.json` 是否正确记录 |
| 归档目录缺失 | 归档失败 | 检查 `artifacts/backtest_archive/` 写权限 |
| CSV编码错误 | BOM不匹配 | 确保使用 `encoding="utf-8-sig"` 读取CSV |

---

## 8. 模块文档索引

| 文档 | 内容 |
|------|------|
| [collector/readme.md](collector/readme.md) | Excel多实例隔离 + 触发器 + COM异常处置 |
| [backtest/readme.md](backtest/readme.md) | 回测框架 + 标准化输出 + 归档 (P61) |
| 本文件 | 完整流水线 + 部署指南 + 故障排除 |

### 附录: 状态速查

```
REAL_WIND_CALL:         False (锁定)
wind_api_calls:         0
gate:                   CLOSED/HOLD
release_permit:         NOT_ISSUED
marker:                 NOT EXISTS
sample_fetch_allow:     NOT EXISTS
Final-Lock:             4/4 完整
P57 COM防锁:            三重加固
P60 实例隔离:           已就位
P61 标准化输出:         5类文件 + 自动归档
回调触发器:             SHA256哈希锁
P59 框架:               37项测试通过
状态:                   STATIC_STANDBY
```
