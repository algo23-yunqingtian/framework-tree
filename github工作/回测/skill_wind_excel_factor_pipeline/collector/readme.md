# Skill: Wind Excel Factor Pipeline — Collector Module

> **DSHA-P60 · 采集模块文档**
> 基线: `feature/v88-g1 @ c214cdf`
> 状态: STATIC_STANDBY · gate=CLOSED/HOLD · release_permit=NOT_ISSUED
> 关联原型: `code/prototype_wss_assemble_sim.py`
> 回调触发器: `code/sample_data_trigger.py`

---

## 目录

1. [Excel 多实例隔离设计](#1-excel-多实例隔离设计)
2. [小样数据落地自动触发回测](#2-小样数据落地自动触发回测)
3. [COM 异常处置预案](#3-com-异常处置预案)
4. [调用链全景图](#4-调用链全景图)
5. [安全红线与保护机制](#5-安全红线与保护机制)
6. [文件清单](#6-文件清单)

---

## 1. Excel 多实例隔离设计

### 1.1 设计原则

Wind WSS/WSD 公式必须通过 Excel COM 接口调用。当用户前台同时运行 Excel 时，
Agent 脚本的 COM 操作**必须与用户 Excel 完全隔离**，避免：

- ❌ 操作或关闭用户 Excel 窗口
- ❌ 干扰用户正在编辑的工作表
- ❌ 读取用户 Excel 中的数据
- ❌ 终止用户的 Excel 进程

### 1.2 实例分类

| 实例类型 | 标识 | PID 来源 | Agent 行为 |
|----------|------|----------|------------|
| **USER_INSTANCE** | `USER_INSTANCE_EXCEL` | 创建 Agent 实例前枚举 | 不读取、不操作、不终止 |
| **AGENT_INSTANCE** | `DSHA_P60_AGENT_EXCEL` | 创建 COM 对象后对比 | 可释放、可终止 |

### 1.3 隔离流程

```
┌──────────────────────────────────────────────────────────────────┐
│                     P60 Excel 实例隔离流程                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 创建 Agent 实例之前                                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ _identify_user_excel_instances()                       │       │
│  │ → 枚举所有 EXCEL.EXE 进程                              │       │
│  │ → 记录 PID 列表为 USER_INSTANCE 排除集                  │       │
│  │ → 日志: "识别到 N 个用户前台Excel实例 — 不操作"         │       │
│  └──────────────────────────────────────────────────────┘       │
│                          ↓                                       │
│  Step 2: 创建 Agent 隔离实例                                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ win32com.client.Dispatch("Excel.Application")          │       │
│  │ → Visible = False (无窗口)                             │       │
│  │ → DisplayAlerts = False                                │       │
│  │ → _detect_agent_excel_pid(before_pids)                 │       │
│  │   对比创建前后的 PID 列表, 新 PID = Agent 实例          │       │
│  └──────────────────────────────────────────────────────┘       │
│                          ↓                                       │
│  Step 3: 正常 WSS 查询                                            │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ wb = xl.Workbooks.Add()                                │       │
│  │ ws.Cells(1,1).Value = '=WSS("ZN.SHF","close",...)'    │       │
│  │ ws.Calculate()                                         │       │
│  │ value = ws.Cells(1,1).Value                            │       │
│  └──────────────────────────────────────────────────────┘       │
│                          ↓                                       │
│  Step 4: 正常路径 — COM 释放                                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ assert_com_cleanup(xl)                                 │       │
│  │ → 逐层释放 Worksheet → Workbook → Application          │       │
│  │ → xl.Quit()                                            │       │
│  │ → GC.Collect() × 2                                    │       │
│  │ → agent_pid = None (Agent 实例已清理)                   │       │
│  └──────────────────────────────────────────────────────┘       │
│                          ↓                                       │
│  Step 4 (异常路径): COM 卡死                                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ except:                                                │       │
│  │ → _kill_agent_excel_only(agent_pid, user_instances)   │       │
│  │   ├─ 安全检查: agent_pid ∉ user_pids                   │       │
│  │   ├─ taskkill /F /PID <agent_pid>                     │       │
│  │   └─ 用户 Excel 不受影响                                │       │
│  │ → log_alert("COM_HANG_AGENT_ONLY_KILLED")             │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 核心函数

| 函数 | 位置 | 功能 |
|------|------|------|
| `_identify_user_excel_instances()` | `prototype_wss_assemble_sim.py` | 识别用户前台 Excel 实例 |
| `_detect_agent_excel_pid()` | `prototype_wss_assemble_sim.py` | 检测 Agent 新建 Excel PID |
| `_kill_agent_excel_only()` | `prototype_wss_assemble_sim.py` | 仅终止 Agent Excel 实例 |
| `assert_com_cleanup()` | `prototype_wss_assemble_sim.py` (P57) | 逐层释放 + GC 双重回收 |
| `check_excel_residue()` | `prototype_wss_assemble_sim.py` (P57) | 兜底进程自检 |

### 1.5 安全常量

```python
COM_HANG_TIMEOUT_SEC        = 30      # COM 卡死超时 (秒)
COM_HANG_KILL_ONLY_AGENT   = True     # COM 卡死时仅终止 Agent 实例
AGENT_INSTANCE_LABEL       = "DSHA_P60_AGENT_EXCEL"
USER_INSTANCE_LABEL        = "USER_INSTANCE_EXCEL"
```

---

## 2. 小样数据落地自动触发回测

### 2.1 触发机制

当 WSS 小样采集完成后，CSV 文件落地至 `artifacts/sample_output/`，
自动触发 `code/sample_data_trigger.py` 执行完整因子+回测管道。

```
artifacts/sample_output/*.csv (新文件落地)
    │
    ▼
check_new_csv_files()
    │ 对比 .trigger_state.json 中的 SHA256
    │
    ├─ 无新文件 → 返回 WAIT (不做任何计算)
    │
    └─ 有新文件 → run_pipeline_for_csv()
                        │
                        ▼
        ┌──────────────────────────────────────────┐
        │  Step 1: factor_data_loader               │
        │    load_factor_data(data_path=csv_path)   │
        │    → 数据校验 + 标准化输出                 │
        ├──────────────────────────────────────────┤
        │  Step 2: factor_constructor               │
        │    compute_factor_from_data(data)         │
        │    → momentum 因子计算                     │
        ├──────────────────────────────────────────┤
        │  Step 3: backtest_skeleton                │
        │    run_backtest(factor_data, price_data)  │
        │    → 累计收益/波动率/最大回撤/夏普          │
        ├──────────────────────────────────────────┤
        │  Step 4: backtest_skeleton                │
        │    save_backtest_result(result)            │
        │    → code/backtest_output/*.md + *.json   │
        └──────────────────────────────────────────┘
```

### 2.2 保护机制

| 保护项 | 实现 |
|--------|------|
| 无新文件不触发 | `check_new_csv_files()` 对比 SHA256，无变化返回 WAIT |
| 仅触发小样采集后 | 仅扫描 `artifacts/sample_output/` 目录 |
| 不修改 REAL_WIND_CALL | 常量锁定为 False |
| 不创建 marker | 无 `New-Item` / `os.makedirs` 对 marker 的操作 |
| 零 Wind API 调用 | 全流程离线，wind_api_calls = 0 |

### 2.3 状态追踪

状态文件: `artifacts/sample_output/.trigger_state.json`

```json
{
  "last_trigger_timestamp": "2026-10-18T12:04:21+00:00",
  "processed_files": {
    "ZN.SHF_close_simulated.csv": {
      "sha256": "abc123...",
      "processed_at": "2026-10-18T12:04:21+00:00",
      "status": "TRIGGERED"
    }
  }
}
```

### 2.4 调用接口

| 接口 | 用途 |
|------|------|
| `trigger_on_sample_landing()` | 主入口: 扫描 + 自动触发 |
| `trigger_callback(data_path)` | 轻量接口: 指定单文件触发 |
| `check_new_csv_files()` | 仅检测新文件 |
| `run_pipeline_for_csv(csv_path)` | 对单文件执行完整管道 |

### 2.5 命令行调用

```bash
# 自动扫描 + 触发
python code/sample_data_trigger.py

# 指定文件触发 (模块导入)
python -c "from sample_data_trigger import trigger_callback; trigger_callback('artifacts/sample_output/ZN.SHF_close.csv')"
```

---

## 3. COM 异常处置预案

### 3.1 异常场景与处置

| 异常场景 | 处置策略 | 用户 Excel 影响 |
|----------|----------|----------------|
| COM 对象创建成功但查询超时 | `_kill_agent_excel_only(agent_pid)` — 仅终止 Agent PID | ❌ 无影响 |
| COM 对象创建失败 (ImportError) | 直接返回错误，无 PID 可终止 | ❌ 无影响 |
| `assert_com_cleanup()` 抛出异常 | GC 双重释放 + 兜底进程自检 | ❌ 无影响 |
| 兜底自检发现孤儿进程 | 仅终止与 Agent PID 匹配的孤儿 | ❌ 无影响 |
| 用户 Excel 已存在孤儿进程 | P57 `assert_no_orphan_excel()` 拒绝启动 | ❌ 无影响 |

### 3.2 处置优先级

```
1. 优先保护用户前台 Excel 会话 (绝不终止 USER_INSTANCE)
2. 其次保护 Agent Excel 隔离实例 (COM 异常时终止 Agent PID)
3. 最后记录告警日志 (COM_HANG_AGENT_ONLY_KILLED)
```

### 3.3 告警事件

| 告警类型 | 严重级别 | 触发条件 |
|----------|----------|----------|
| `COM_HANG_AGENT_ONLY_KILLED` | CRITICAL | COM 异常时终止 Agent Excel |
| `COM_ORPHAN_AFTER_CALL` | CRITICAL | 调用后检测到孤儿进程 |
| `COM_ORPHAN_PRECALL` | CRITICAL | 调用前检测到孤儿进程 |
| `COM_ORPHAN_POSTCALL` | CRITICAL | 调用后检测到孤儿进程 |

告警日志: `artifacts/wss_small_sample_alerts.jsonl`

### 3.4 用户 Excel 保护承诺

> **Agent 保证: 脚本全程不读取、不操作、不终止用户前台 Excel 进程。**
>
> 当用户前台 Excel 正在运行时:
> - Agent 创建独立的无窗口 Excel 实例 (`Visible=False`)
> - 仅通过 COM 对象引用操作 Agent 实例
> - COM 异常时仅对 Agent PID 执行 `taskkill /F`
> - 用户 Excel 的 PID 在终止前被验证排除

---

## 4. 调用链全景图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        完整采集→回测调用链                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  阶段 A: WSS 小样采集 (需人工许可)                                  │   │
│  │  ─────────────────────────────────────────                        │   │
│  │  prototype_wss_assemble_sim.py                                     │   │
│  │    ├─ Final-Lock 4 道断言 (marker + REAL_WIND_CALL + 硬限制)      │   │
│  │    ├─ P57 三重COM防锁 (前置检查 + 强制回收 + 兜底自检)              │   │
│  │    ├─ P60 Excel 多实例隔离 (USER_INSTANCE 保护 + Agent PID 管理)   │   │
│  │    └─ 输出: artifacts/sample_output/*.csv (双落地)                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↓ CSV 落地                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  阶段 B: 自动回调触发                                             │   │
│  │  ─────────────────────────────────────────                        │   │
│  │  sample_data_trigger.py                                            │   │
│  │    ├─ check_new_csv_files() — SHA256 对比检测新文件                │   │
│  │    ├─ 无新文件 → 返回 WAIT                                         │   │
│  │    └─ 有新文件 → run_pipeline_for_csv()                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  阶段 C: P59 离线因子+回测管道                                     │   │
│  │  ─────────────────────────────────────────                        │   │
│  │  factor_data_loader.load_factor_data()                             │   │
│  │    → 数据校验 (空值/重复/异常值)                                    │   │
│  │    → 标准化输出                                                    │   │
│  │                          ↓                                         │   │
│  │  factor_constructor.compute_factor_from_data()                     │   │
│  │    → 参数基线校验 (F007 window_days=60)                            │   │
│  │    → momentum 因子计算                                             │   │
│  │                          ↓                                         │   │
│  │  backtest_skeleton.run_backtest()                                  │   │
│  │    → 累计收益/年化波动率/最大回撤/夏普比率                            │   │
│  │                          ↓                                         │   │
│  │  backtest_skeleton.save_backtest_result()                          │   │
│  │    → code/backtest_output/*.md + *.json                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 安全红线与保护机制

### 5.1 不可修改常量

| 常量 | 值 | 文件 |
|------|-----|------|
| `REAL_WIND_CALL` | `False` | 所有模块 |
| `MAX_DAYS_PER_ROUND` | `10` | `prototype_wss_assemble_sim.py` |
| `MIN_INTERVAL_SEC` | `12` | `prototype_wss_assemble_sim.py` |
| `SIM_DATA_POINTS` | `10` | `prototype_wss_assemble_sim.py` |

### 5.2 不可绕过的断言 (P58 Final-Lock)

| 断言 | 检查内容 | 文件位置 |
|------|----------|----------|
| FINAL-LOCK-1 | `artifacts/sample_fetch_allow.marker` 存在 | `__main__` 块 |
| FINAL-LOCK-2 | `REAL_WIND_CALL is True` | `__main__` 块 |
| FINAL-LOCK-3 | `MAX_DAYS_PER_ROUND == 10` | `__main__` 块 |
| FINAL-LOCK-4 | `MIN_INTERVAL_SEC == 12` | `__main__` 块 |

### 5.3 Agent 禁止操作

| 操作 | 原因 |
|------|------|
| ❌ 创建 `sample_fetch_allow.marker` | 必须由 DSHC 人工执行 |
| ❌ 修改 `REAL_WIND_CALL` 为 True | 必须由 DSHC 人工编辑 |
| ❌ 注释/禁用 Final-Lock 断言 | 安全锁不可绕过 |
| ❌ 修改 MAX_DAYS / MIN_INTERVAL | 硬限制保护 |
| ❌ 读取用户 Excel 数据 | 实例隔离保护 |
| ❌ 终止用户 Excel 进程 | 实例隔离保护 |

---

## 6. 文件清单

### P60 新增/修改文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `code/prototype_wss_assemble_sim.py` | 修改 | +P60 多实例隔离逻辑 |
| `code/sample_data_trigger.py` | 新增 | 小样数据落地自动回调触发器 |
| `skill_wind_excel_factor_pipeline/collector/readme.md` | 新增 | 本文件 — 采集模块文档 |

### P59 依赖文件

| 文件 | 说明 |
|------|------|
| `code/factor_data_loader.py` | 离线数据加载 |
| `code/factor_constructor.py` | 基础因子构造 |
| `code/backtest_skeleton.py` | 极简回测框架 |

### 输出目录

| 目录 | 说明 |
|------|------|
| `artifacts/sample_output/` | 小样 CSV 落地目录 (输入) |
| `code/factor_offline_result/` | 因子计算结果 |
| `code/backtest_output/` | 回测结果 (MD + JSON) |
| `artifacts/wss_sample_run.log` | WSS 主运行日志 |
| `artifacts/wss_small_sample_alerts.jsonl` | COM 告警日志 |
| `artifacts/sample_output/trigger_run_log.jsonl` | 触发器运行日志 |
| `artifacts/sample_output/.trigger_state.json` | 触发器状态文件 |

---

## 附录: 状态速查

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
回调触发器:             已就位
P59 框架:               19/19 测试通过
状态:                   STATIC_STANDBY
```
