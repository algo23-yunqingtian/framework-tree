# DSHA-P59 · 离线因子与回测框架就绪文档
# Offline Factor & Backtest Framework Readiness

> **文档 ID**: DSHA-P59-OFFLINE-FRAMEWORK-READY-001
> **生成时间**: 2026-10-18 GMT+8
> **Agent**: DSHA-P59
> **Branch**: feature/v88-g1
> **基线**: feature/v88-g1 @ 48b7197 (P72 HEAD, P58 Final-Lock 已就位)
> **GATE**: CLOSED/HOLD | **Release Permit**: NOT_ISSUED
> **Wind API Calls**: 0
> **声明**: 纯离线代码框架, 未调用任何 Wind API, 未修改 P58 Final-Lock。

---

## 0. 目标

预先搭建离线因子与回测框架, 等待小样原始 WSS 数据落地即可直接加载运算。
不读取任何真实 Wind 数据, 不点火, 保持 STATIC_STANDBY。

---

## 1. 数据依赖

### 1.1 必需数据

| 依赖 | 路径 | 状态 | 说明 |
|------|------|------|------|
| 小样 CSV 输出 | `artifacts/sample_output/*.csv` | ✅ PRESENT (仿真) | 小样 WSS 采集输出, 含 date,value,symbol,indicator,source |
| 统计 JSON | `artifacts/sample_output/sim_run_stats.json` | ✅ PRESENT | 小样运行统计, 含数据源标记 |
| 许可文件 | `artifacts/sample_fetch_allow.marker` | 🔒 NOT EXISTS | 真实采集必须存在, 当前仅仿真 |

### 1.2 数据格式要求

小样 CSV 必须包含以下列:

```
date, value, symbol, indicator, source
```

| 列 | 类型 | 说明 | 示例 |
|----|------|------|------|
| date | str | 交易日 (YYYY-MM-DD) | 2025-01-02 |
| value | float | 数值 | 24400.18 |
| symbol | str | 品种代码 | ZN.SHF |
| indicator | str | 指标名称 | close |
| source | str | 数据源标记 | SIMULATED |

### 1.3 数据就绪条件

| 条件 | 当前状态 | 说明 |
|------|----------|------|
| CSV 文件存在 | ✅ 是 (仿真) | 仿真数据 10 行 |
| 文件可读 (UTF-8) | ✅ 是 | 标准编码 |
| 列名匹配 | ✅ 是 | 5 列完整 |
| 值域合理 | ✅ 是 | 24400~24840 元/吨 |

---

## 2. 模块调用顺序

```
factor_data_loader → factor_constructor → backtest_skeleton
        ↓                    ↓                    ↓
   数据加载            因子计算             回测引擎
   + 校验             + 参数校验           + 指标计算
```

### 2.1 模块接口

#### 2.1.1 factor_data_loader (code/factor_data_loader.py)

```python
# 主入口
result = load_factor_data(data_path=None, anomaly_threshold=3.0)

# 返回结构
{
    "status": "OK" | "WARNING",
    "symbol": "ZN.SHF",
    "indicator": "close",
    "source": "SIMULATED",
    "dates": ["2025-01-02", ...],
    "values": [24400.18, ...],
    "metadata": {
        "record_count": 10,
        "validation": {
            "overall_passed": True,
            "null_count": 0,
            "duplicate_count": 0,
            "anomalous_count": 0
        }
    }
}
```

#### 2.1.2 factor_constructor (code/factor_constructor.py)

```python
# 主入口
result = compute_factor_from_data(data, factor_type, params)

# 支持的因子类型
- "momentum": 动量因子 (N日收益率)
- "volatility": 波动率因子 (N日收益率标准差)
- "mean_reversion": 均值回归因子 (Z-score)

# 参数基线校验 (F007)
- window_days: 60 (基准) / 35~100 (验证范围)
- weights: frozen
- decay_factor: frozen
```

#### 2.1.3 backtest_skeleton (code/backtest_skeleton.py)

```python
# 主入口
result = run_backtest(factor_data, price_data, config)

# 计算指标
- 累计收益率 (Cumulative Return)
- 年化波动率 (Annual Volatility)
- 日均波动率 (Daily Volatility)
- 最大回撤 (Max Drawdown)
- 夏普比率 (Sharpe Ratio)

# 输出
- backtest_{type}_{symbol}_{timestamp}.md
- backtest_{type}_{symbol}_{timestamp}.json
```

### 2.2 完整调用示例

```python
import factor_data_loader
import factor_constructor
import backtest_skeleton

# Step 1: 加载数据
data = factor_data_loader.load_factor_data()

# Step 2: 计算因子
factor = factor_constructor.compute_factor_from_data(
    data, factor_type="momentum"
)

# Step 3: 运行回测
bt = backtest_skeleton.run_backtest(
    factor_data=factor,
    price_data=data
)

# Step 4: 保存结果
paths = backtest_skeleton.save_backtest_result(bt)
```

---

## 3. 异常处理说明

### 3.1 数据加载异常 (factor_data_loader)

| 异常类型 | 触发条件 | 处理方式 |
|----------|----------|----------|
| MissingDataFileError | CSV 文件不存在 | 抛出异常, 调用方可捕获 |
| EmptyDataFrameError | CSV 文件无数据行 | 抛出异常 |
| DataIntegrityError | 空值/重复/异常值 | 返回 WARNING 状态, 不中断流程 |
| 数据文件缺失 | 目录不存在或为空 | 自动回退到内置仿真数据 (10行) |

### 3.2 因子构造异常 (factor_constructor)

| 异常类型 | 触发条件 | 处理方式 |
|----------|----------|----------|
| 数据量不足 | prices 长度 < window+1 | 返回 NO_DATA 状态, 因子序列为空 |
| 参数超出范围 | window_days 超出验证范围 | 返回校验错误, 不中断计算 |
| 权重未冻结 | 权重参数非 frozen | 返回警告, 继续计算 |

### 3.3 回测引擎异常 (backtest_skeleton)

| 异常类型 | 触发条件 | 处理方式 |
|----------|----------|----------|
| 无输入数据 | factor_data 或 price_data 为 None | 返回 WAIT 状态, 不报错 |
| 因子序列为空 | factor_values 为空列表 | 返回 WAIT 状态 |
| 长度不匹配 | 因子序列 > 价格序列 | 返回 WAIT 状态 |

### 3.4 安全红线异常 (所有模块)

| 条件 | 处理方式 |
|------|----------|
| REAL_WIND_CALL 修改 | 🔒 硬锁死, 禁止修改 |
| wind_api_calls > 0 | 🔒 本框架不触发 Wind API |
| marker 文件创建 | 🔒 Agent 禁止自行创建 |
| Final-Lock 绕过 | 🔒 禁止注释/屏蔽 |

---

## 4. 模块状态

### 4.1 代码文件

| 模块 | 路径 | 状态 | 行数 | 测试数 |
|------|------|------|------|--------|
| 数据加载 | `code/factor_data_loader.py` | ✅ 已编写 | ~450 | 6 |
| 因子构造 | `code/factor_constructor.py` | ✅ 已编写 | ~420 | 7 |
| 回测引擎 | `code/backtest_skeleton.py` | ✅ 已编写 | ~470 | 6 |

### 4.2 输出目录

| 目录 | 路径 | 状态 |
|------|------|------|
| 因子离线结果 | `code/factor_offline_result/` | 待生成 (仿真测试时创建) |
| 回测输出 | `code/backtest_output/` | 待生成 (仿真测试时创建) |

### 4.3 安全锁确认

| 项目 | 值 | 状态 |
|------|-----|------|
| REAL_WIND_CALL | False | ✅ 锁定 |
| wind_api_calls | 0 | ✅ 零调用 |
| MAX_DAYS_PER_ROUND | 10 (P58 不变) | ✅ 未修改 |
| MIN_INTERVAL_SEC | 12 (P58 不变) | ✅ 未修改 |
| P58 Final-Lock 断言 | 4道 | ✅ 未修改 |
| marker 文件 | NOT EXISTS | ✅ Agent 未创建 |

---

## 5. 仿真测试结果

### 5.1 factor_data_loader

| 测试 | 内容 | 结果 |
|------|------|------|
| T1 | 内置仿真数据 (10行) | ✅ PASS |
| T2 | 空值校验 (3个空值) | ✅ PASS |
| T3 | 重复时间戳校验 (1个重复) | ✅ PASS |
| T4 | 异常值检测 (z>3) | ✅ PASS |
| T5 | 综合校验 | ✅ PASS |
| T6 | 文件不存在异常 | ✅ PASS |

### 5.2 factor_constructor

| 测试 | 内容 | 结果 |
|------|------|------|
| T1 | F007 参数基线校验 | ✅ PASS |
| T2 | 动量因子计算 | ✅ PASS |
| T3 | 波动率因子计算 | ✅ PASS |
| T4 | 均值回归因子计算 | ✅ PASS |
| T5 | 数据不足 → NO_DATA | ✅ PASS |
| T6 | 参数超出范围 → 警告 | ✅ PASS |
| T7 | 保存因子结果 | ✅ PASS |

### 5.3 backtest_skeleton

| 测试 | 内容 | 结果 |
|------|------|------|
| T1 | 无输入 → WAIT | ✅ PASS |
| T2 | 只有价格无因子 → WAIT | ✅ PASS |
| T3 | 完整数据 → OK + 指标 | ✅ PASS |
| T4 | 保存回测结果 (MD+JSON) | ✅ PASS |
| T5 | 波动率因子回测 | ✅ PASS |
| T6 | WAIT 状态 Markdown 输出 | ✅ PASS |

---

## 6. 版本记录

| 版本 | 时间 | 变更 |
|------|------|------|
| v1.0 | 2026-10-18 | 初始创建: 3 模块 + 文档 + 仿真测试 |

---

## 7. 与 P58 的关系

| P58 项目 | P59 兼容性 | 说明 |
|----------|------------|------|
| REAL_WIND_CALL=False | ✅ 兼容 | P59 不修改此常量 |
| MAX_DAYS_PER_ROUND=10 | ✅ 兼容 | P59 不修改此常量 |
| MIN_INTERVAL_SEC=12 | ✅ 兼容 | P59 不修改此常量 |
| Final-Lock 4 断言 | ✅ 兼容 | P59 不修改 P58 代码 |
| 日志路由 | ✅ 兼容 | P59 不修改日志路由 |
| 双输出 | ✅ 兼容 | P59 不修改输出逻辑 |
| marker 文件 | ✅ 兼容 | P59 不创建 marker |

---

## 8. 下一步

### 8.1 等待条件

1. **DSHC 人工创建** `artifacts/sample_fetch_allow.marker`
2. **DSHC 人工修改** `REAL_WIND_CALL = True`
3. **DSHC 人工执行** WSS 小样采集 (10交易日, 12s间隔)
4. **小样输出 CSV** 落入 `artifacts/sample_output/`
5. 上述 3 个模块即可加载真实数据进行运算

### 8.2 预期流程

```
[人工授权] → [WSS采集] → [CSV输出] → [数据加载] → [因子计算] → [回测分析]
   marker         REAL_WIND         10日数据     factor_data    factor_      backtest_
   创建           _CALL=True                        _loader      _constructor  _skeleton
```

### 8.3 当前状态

**STATIC_STANDBY** — 框架已就绪, 等待小样数据落地。

---

> **DSHA-P59 声明**: 本文档为纯离线分析产物, 未调用任何 Wind API。
> REAL_WIND_CALL=False | wind_api_calls=0 | gate=CLOSED/HOLD
