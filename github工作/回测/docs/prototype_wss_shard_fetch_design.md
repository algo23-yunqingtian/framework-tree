# DSHA-P55 · WSS 分片拼装简易时序 — 离线原型设计文档

> **状态**: 纸上设计 + 模拟原型 · **不执行真实 Wind 调用**  
> **分支基线**: `feature/v88-g1 @ 01a022f`  
> **红线约束**: gate=CLOSED/HOLD, release_permit=NOT_ISSUED, wind_api_calls=0  
> **版本**: v1.0 · 2026-10-17

---

## 1. 路线定位：备选 B 方案

```
┌─────────────────────────────────────────────────────────────┐
│  主通路 (Plan A)          备选通路 (Plan B)                  │
│  Excel WDF WSD 函数       WSS 单点循环拼装                    │
│  (API 桥接待激活)         (仅 WSS 快照，逐日推进)             │
│  ─────────────────       ─────────────────                  │
│  一次调用取完整序列        逐日调用拼装序列                    │
│  需要 WDF API 桥接        不需要 API 桥接                    │
│  请求量: 1× 品种×指标     请求量: N× 品种×指标               │
│  状态: BLOCKED (API)     状态: PLAN_B_ON_PAPER               │
└─────────────────────────────────────────────────────────────┘
```

**Plan B 启用条件**（缺一不可）：
1. ✅ 主通路已修复 **OR** 收到 `release_permit` 许可
2. ✅ `REAL_WIND_CALL` 常量切换为 `True`
3. ✅ 全部 P3 前置检查项通过
4. ✅ 风控制熔断标记文件不存在

**当前状态**: Plan B 仅在纸上设计 + 离线模拟，**不得对真实 Wind 发起任何循环请求**。

---

## 2. 原理：WSS 单点快照 → 逐日分片 → 拼装时序

### 2.1 WSS 能力边界

| 能力 | WSD | WSS | WSS 分片拼装 (Plan B) |
|------|-----|-----|----------------------|
| 返回类型 | 时序序列 | 单个快照值 | 多日快照拼接成序列 |
| 日期参数 | 起止区间 | 单个交易日 | 需逐日循环调用 |
| API 桥接依赖 | 是 | 否 | 否 |
| 原始请求量 | 1 | 1 | N (N=交易日数) |
| 返回字段 | 多字段 | 单字段 | 逐字段调用 |

### 2.2 拼装流程

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 交易日列表 │────▶│ WSS 逐日调用  │────▶│ 单次快照落盘  │────▶│ 序列拼装+对齐 │
│ (T1..TN) │     │ (12-15s间隔) │     │ (JSON/CSV)   │     │ (去重+排序)  │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                        │                                      │
                    ┌───▼──────────┐                       ┌───▼──────────┐
                    │ 限流/休眠控制  │                       │ 最终时序 CSV  │
                    │ 紧急停止检查   │                       │ (factor.csv) │
                    └──────────────┘                       └──────────────┘
```

### 2.3 伪代码骨架

```python
# 伪代码 — 不执行，仅说明结构
trading_days = get_trading_calendar("2025-01-01", "2025-12-31")  # ~245 日
series = {}

for day in trading_days:
    # 限流：每次 WSS 调用间隔 12-15 秒
    time.sleep(random.uniform(12, 15))
    
    # 紧急停止检查
    if emergency_stop_marker_exists():
        log("EMERGENCY_STOP triggered")
        break
    
    # WSS 单点查询（模拟或真实）
    snapshot = wind_wss_query(
        code="ZN.SHF",
        indicator="close",
        date=day
    )
    
    if snapshot is not None:
        series[day] = snapshot

# 拼装对齐
assembled = align_series(trading_days, series)
write_csv(assembled)
```

### 2.4 数学模型

```
设 N = 交易日总数，F = 指标字段数
请求总数 = N × F
最小时间预算 = N × F × 12s  (以最小间隔 12s 计)
最大时间预算 = N × F × 15s  (以最大间隔 15s 计)

以 6 品种 × 8 指标 × 245 日 为例：
  请求总数 = 6 × 8 × 245 = 11,760
  最小耗时 = 11,760 × 12 = 141,120s ≈ 39.2 小时
  最大耗时 = 11,760 × 15 = 176,400s ≈ 49 小时

结论: 全量采集不可行，仅适合：
  (a) 小样验证 (≤12 日 × 1 品种 × 1 指标 = 12 请求)
  (b) 增量补充 (缺失日补齐)
  (c) 单点验证 (WSS 功能可用性确认)
```

---

## 3. 风险清单

### 3.1 请求频率管控

| 风险 | 等级 | 说明 | 缓解措施 |
|------|------|------|----------|
| 请求过频触发 WSS 限流 | 🔴 高 | Wind WSS 有未公开频控阈值，密集请求可能被临时封禁 | 强制间隔≥12s；每轮≤12日 |
| 连续失败导致会话失效 | 🔴 高 | 失败累计超过阈值 → 会话被终止 | 失败计数≥3 自动停止 |
| 风控熔断误触 | 🟡 中 | 短时间大量请求可能被 Wind 风控拦截 | 熔断检查 + 紧急停止 |
| 单点失败浪费配额 | 🟢 低 | 单点请求失败 → 重新请求浪费资源 | 重试上限 2 次，间隔 30s |

### 3.2 防锁与稳定性

| 风险 | 等级 | 说明 | 缓解措施 |
|------|------|------|----------|
| Excel COM 占用锁 | 🔴 高 | WSS 调用期间 Excel 被锁，无法操作 | 调用期间禁止写入 Excel |
| 会话抖动 | 🟡 中 | WSS 返回"Fetching..."而非数值 | 检测并退避重试 |
| 终端崩溃/重启 | 🟡 中 | wmain.exe 意外退出 → 全部调用失败 | 进程存活检查 |
| 磁盘空间不足 | 🟢 低 | 大量 CSV 写入占满磁盘 | 预估磁盘预算 |

### 3.3 数据质量

| 风险 | 等级 | 说明 | 缓解措施 |
|------|------|------|----------|
| 数据不一致 | 🟡 中 | 多次快照之间数据可能不一致 | 以最终落盘值为准 |
| 缺失交易日 | 🟡 中 | 非交易日返回空值 | 交易日日历校准 |
| 时区偏移 | 🟢 低 | Wind 返回时间戳有时区偏移 | 统一 UTC+8 转换 |
| 缓存污染 | 🟢 低 | WSS 可能返回缓存值 | 带时间戳参数确保新鲜度 |

### 3.4 风控熔断

| 风险 | 等级 | 说明 | 缓解措施 |
|------|------|------|----------|
| 无紧急停止机制 | 🔴 高 | 无法中止正在执行的批量循环 | 紧急停止标记文件 |
| 无限循环 | 🔴 高 | 代码异常导致无限重试 | 硬编码最大轮次上限 |
| 静默失败 | 🟡 中 | 错误未抛出，结果空但不报错 | 返回值类型检查 |
| 凭据泄露 | 🟡 中 | WSS 调用日志包含 session 信息 | 日志脱敏 |

---

## 4. 强制限流规则（写死设计常量）

```python
# ──── 限流常量 (不可修改，仅由 DSHC 许可后启用) ────

MIN_INTERVAL_SEC      = 12      # 最小间隔 (秒)
MAX_INTERVAL_SEC      = 15      # 最大间隔 (秒)

MAX_DAYS_PER_ROUND    = 12      # 最大单轮交易日数量

MAX_RETRY_PER_POINT   = 2       # 单点最大重试次数
RETRY_BACKOFF_SEC     = 30      # 重试间隔 (秒)

MAX_CONSECUTIVE_FAIL  = 3       # 连续失败阈值 → 自动停止

# 紧急停止标记文件
EMERGENCY_STOP_FILE   = ".emergency_stop"   # 工作目录下

# ──── 限流算法 ────
def apply_rate_limit(request_count: int) -> float:
    """每次 WSS 调用后的休眠时间 (秒)"""
    interval = random.uniform(MIN_INTERVAL_SEC, MAX_INTERVAL_SEC)
    return interval
```

---

## 5. 离线模拟器说明

### 5.1 设计原则

模拟器位于 `code/prototype_wss_assemble_sim.py`：

1. **零真实 Wind 调用** — `REAL_WIND_CALL = False` 硬锁死
2. **模拟数据** — 使用 `random.gauss` 生成模拟价格序列
3. **演示完整流程** — 逐日拼装、去重、对齐、限流休眠、紧急停止
4. **输出样例 CSV** — 模拟数据结果，**非真实行情**

### 5.2 模拟器常量

```python
REAL_WIND_CALL = False           # ← 硬锁死，不允许本轮切换为 True
SIM_DATA_POINTS = 10             # 模拟交易日数量 (演示用)
SIM_SYMBOL = "ZN.SHF"            # 模拟品种
SIM_INDICATOR = "close"          # 模拟指标
SIM_PRICE_BASE = 24500.0         # 模拟基准价 (元/吨)
```

### 5.3 运行方式

```bash
python code/prototype_wss_assemble_sim.py
```

输出:
- 控制台: 执行日志 (逐日请求、限流等待、拼装进度)
- 文件: `code/sim_output/ZN.SHF_close_simulated.csv` (模拟样例)
- 文件: `code/sim_output/sim_run_stats.json` (运行统计)

---

## 6. 未来真正执行的前置检查清单

> ⚠️ **以下清单全部通过后，`REAL_WIND_CALL` 方可切换为 `True`**

### 6.1 信号/令牌 (必须全部就位)

| # | 检查项 | 预期值 | 验证方式 |
|---|--------|--------|----------|
| 1 | `WDF_ENV_READY.token` 存在 | ✅ 文件存在 | `Test-Path artifacts/WDF_ENV_READY.token` |
| 2 | `DSHC 许可信号` 已收到 | ✅ 许可文件 | `factor_exp_workspace/dshc_permit.json` 中 `status=GRANTED` |
| 3 | `release_permit` 状态 | ✅ `ISSUED` | 检查 `tracking_monitor_audit.jsonl` 最新许可事件 |
| 4 | `gate` 状态 | ✅ `OPEN` | 检查 `STATUS.md` gate 字段 |
| 5 | `wind_api_calls` 额度 | ✅ >0 | 检查 `pre_wind_call_guard_check.py` 计数 |
| 6 | `DEFECT-012` 状态 | ✅ `CLOSED` | 检查 `STATUS.md` |
| 7 | `WDF.Addin` LoadBehavior | ✅ ≠3 或 API 桥接已激活 | 注册表检查 |
| 8 | Wind 终端进程存活 | ✅ `wmain.exe` + `WBox.exe` | 进程检查 |

### 6.2 环境就绪 (必须全部通过)

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 9 | WSS 单点探测成功 | `wsd_pretest.py` 返回数值而非 `"Fetching..."` |
| 10 | 无紧急停止标记 | `.emergency_stop` 文件不存在 |
| 11 | 磁盘剩余空间 | ≥100MB |
| 12 | Python 进程数 | ≤3 (无多余 pipeline 进程) |
| 13 | 风控制熔断检查 | 无熔断标记 |

### 6.3 代码就绪 (必须全部完成)

| # | 检查项 | 完成标准 |
|---|--------|----------|
| 14 | 交易日日历数据源 | 已定义 `get_trading_calendar()` 函数 |
| 15 | 异常处理框架 | 所有 WSS 调用包裹在 try-except 中 |
| 16 | 紧急停止响应 | 每轮循环检查 `.emergency_stop` 文件 |
| 17 | 数据校验 | 返回值类型检查 (必须为 float) |
| 18 | 日志脱敏 | 无凭据信息写入日志 |

### 6.4 审批流程 (必须全部完成)

| # | 步骤 | 责任人 |
|---|------|--------|
| 19 | 提交 `REAL_WIND_CALL=True` 代码变更 | DSHC |
| 20 | 代码审查 (guard 全 PASS) | DSHC + 架构线 |
| 21 | 小样验证 (1 品种 × 1 指标 × 3 日) | DSHC |
| 22 | 逐步放量 (12日 → 全部) | DSHC |
| 23 | 全量采集监控 | DSHC + 看门狗 |

### 6.5 告警停机条件

以下任一条件触发，**立即停止所有 WSS 调用**：

| # | 告警 | 严重级别 | 动作 |
|---|------|----------|------|
| A1 | 连续 3 次 WSS 返回非数值 (`Fetching...`) | 🔴 紧急 | 停止 + 上报 |
| A2 | `wind_api_calls` 超过配额 80% | 🟡 警告 | 减速 + 上报 |
| A3 | Wind 终端进程消失 | 🔴 紧急 | 停止 + 上报 |
| A4 | `.emergency_stop` 标记文件出现 | 🔴 紧急 | 停止 + 清理现场 |
| A5 | WSS 返回错误代码 | 🔴 紧急 | 停止 + 记录错误 |
| A6 | 单次调用超时 >30s | 🟡 警告 | 重试 1 次，仍超时则停止 |
| A7 | 磁盘空间 <50MB | 🔴 紧急 | 停止 + 清理临时文件 |
| A8 | 风控熔断触发 | 🔴 紧急 | 停止 + 等待 DSHC 介入 |
| A9 | 代码异常 (未捕获异常) | 🔴 紧急 | 停止 + 记录堆栈 |
| A10 | 连续 2 轮 (24 请求) 数据缺失率 >20% | 🟡 警告 | 减速 + 上报 |

---

## 7. 附录

### 7.1 相关文档

- `factor_exp_workspace/harvest_to_csv.py` — 主通路 CSV 导出脚本
- `factor_exp_workspace/wsd_pretest.py` — WSD/WSS 探测脚本
- `data-harbor/.../pre_wind_call_guard_check.py` — 守卫自检脚本
- `G7_ADJUDICATION_LEDGER/` — G7 仲裁账本

### 7.2 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-10-17 | 初始设计 · 纸上方案 + 模拟原型 |

---

> **⚠️ 红线重申**: 本文档为离线设计，不包含任何真实 Wind 调用代码。`REAL_WIND_CALL` 在本轮工作中强制锁定为 `False`。未收到 `release_permit` 前，不得对真实 Wind 发起任何循环请求。
