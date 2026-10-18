# DSHC-IGNITE-A01 · WDF 通道诊断报告

> **工单**: DSHC-IGNITE-A01-AUTH · `auth_ref=A01-USER-REMOTE-001`
> **授权**: USER_EXPLICIT_ONE_SHOT_REMOTE_AUTHORISATION（一次性，已在本轮耗尽并失效）
> **分支**: feature/v88-g1
> **运行状态**: `FETCH_ERROR`（通道失败，0 条数据）
> **日期**: 2026-10-18 20:45–20:47 GMT+8

---

## 1. 结论（一句话）

**Excel-WDF 插件链路已加载且可响应公式，但 Wind 终端 API 桥接层未激活，WSD 从不返回数据网格。** 本次授权运行按契约完整执行、完整留痕、完整回收，未触碰任何红线。P62-LOOP 无数据可消费。

---

## 2. 执行事实

| 项 | 值 |
|---|---|
| 预检 | **16/16 PASS**（`artifacts/wdf_preflight_check.json`） |
| 代理后台 Excel | pid=**24736**，生命周期 **67s**（硬上限 12min，远未触达） |
| 前台用户 Excel | pid=**14644**《永安期货研究中心 锌数据库-锭篇》——**全程存活、未受影响** |
| WDF 加载项 | 在代理实例中 **已加载且 Connect=True**（7 个 ProgId，含 WDF.Addin / WDF.XLTaskPanel） |
| 品种尝试 | CU.SHF 3 次尝试全部返回 `无法读取数据！`；**首个品种即 fail-fast 中止**，其余 6 个未尝试（不轰炸 Wind） |
| CSV | `output_sample/wdf_sample_metals_raw.csv`，**0 数据行**，50 字节，SHA256 `BEF26114…0895` |
| `wind_api_calls` | **0**（语义：仅当 WSD 实际返回数据网格才计数；本次无一网格返回） |
| `wdf_retries` / `wdf_inject_attempts` | 2 / 3 |
| 回收 | `reset_wdf_safe.ps1` 定向终止 24736；marker 已清；再次核验 24736 已不存在 |
| 看门狗 | 执行器自回收完成后被终止（若放任，会在 20:58 误报 HARD_TIMEOUT） |

---

## 3. 通道诊断证据（5 次独立探测）

### 3.1 `Application.Evaluate` 永久停在占位符

```
WSD("CU.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous")
poll1  t+2s   call_ms=1513   String [Fetching...]     ← 首次调用即发出 Wind 请求
poll2  t+5s   call_ms=19     String [Fetching...]     ← 之后全是缓存读回
...
poll40 t+119s call_ms=3      String [Fetching...]     ← 122 秒 40 次轮询，永不变
```

### 3.2 数组公式在此绑定下无效

```
={1,2,3;4,5,6}  → stored 正常，但 IsInArray=False，CurrentArray 恒为 1x1，Text=[1]
```
PowerShell 5.1 COM 绑定不把单单元格 `FormulaArray` 当成 CSE 数组公式；`Application.Eval` 在此 interop 中不存在，`ExecuteExcel4Macro "{=...}"` 被 zh-CN locale 拒绝。多单元格溢出对自动化**完全不可见**。

### 3.3 唯一可用路径：单元格公式 + `Calculate()` + 轮询

```
poll1 t+0s  A1=[Fetching...]          ← 占位符
poll2 t+5s  A1=[2025-01-02]           ← 5 秒内被替换
```
**这是本次授权运行实际使用的路径。**

### 3.4 参数形式枚举：字段参数不被尊重

| 公式 | 结果 |
|---|---|
| `WSD("CU.SHF","CLOSE","2025-01-02","2025-01-03")` | `2025-01-02`（日期串） |
| `WSD("CU.SHF","Close",...)` | `2025-01-02`（大小写不敏感，同为日期串） |
| `WSD("CU.SHF","CLOSE;OPEN",...)` | `73280`（裸数值，无溢出） |
| `WSD("CU.SHF",1,...)` | `73280` |
| `WSD("CU.SHF","","...",...)` | `73280` |
| `WSD("CU.SHF","HIGHEST",...)` | `无法读取数据！` |
| `WS("CU.SHF",1)` | `#NAME?`（函数不存在） |
| `WSS("CU.SHF")` | `#VALUE!`（函数不存在） |
| 完整 payload 公式 | **`无法读取数据！`** |

**该加载项只暴露 WSD，且不尊重所请求的字段列表（`CLOSE;VOL;OI;SETTLE`），因此无法产出工单要求的宽表 schema。**

### 3.5 与既有 P54 调查一致

`data-harbor/dsha_p49_prep/P49_backtest_audit/` 下的既有结论完全吻合：

- `wind_excel_harvest_guide.md`：`WSD/WSS = #NAME?`，根因 **Wind 终端 API 桥接层未激活**（`.wind\WMain\` 存在但为空、无本地 API 监听端口、`windlocal.exe` 立即退出、`regsvr32` 静默失败）
- `excel_wind_test_report.md`：`WindPy c_isConnectionOK=0`、`w.start() ErrorCode=-2`、凭据可用但 `ErrorCode=-2`

本次环境相比 2026-07-13 **有改善**（WDF.Addin 现在能加载并 Connect、WSD 有响应而非 `#NAME?`），但**数据面仍然不可用**——桥接层仍是共同瓶颈。

---

## 4. 红线自检（全绿）

| 红线 | 状态 |
|---|---|
| 一次性授权，本轮耗尽即失效 | ✅ `auth_expired_after_this_run=true` |
| 从不终止前台 Excel 14644 | ✅ 存活，未被触碰 |
| 仅 Excel-WDF 链路，未用 WindPy | ✅ `windpy_used=false` |
| 12 分钟硬超时 | ✅ 代理 Excel 实际 67s；未触达 |
| 最多 2 次 WDF 重试 | ✅ `wdf_retries=2` |
| 不轰炸 Wind | ✅ 首个品种失败即中止，未遍历 7 品种 |
| 事件全量入 G7 裁决账本 | ✅ `tracking_monitor_audit.jsonl` 169+ 条、`dshc_p90a_final_events.jsonl`、`dshc_ignite_a01_events.jsonl` |
| 产物提交至 `feature/v88-g1` | ✅ |
| 不产生永久配置修改 | ✅ `permanent_config_modified=false` |
| 不产生永久 marker | ✅ `sample_fetch_allow_marker_created=false` |
| DSHD-P79 红线基线字段未动 | ✅ `wind_api_calls=0` / `real_wind_call=false` / `marker_created=false` |

---

## 5. 需要的后续动作（非本工单范围）

要让 Excel-WDF 链路真正出数，需要**人工在 Wind 终端侧**完成以下任一操作（均无法通过远程/自动化完成，且不在本工单授权范围内）：

1. 以管理员身份运行 `D:\bin\InitWAPI.exe` 激活 API 桥接层
2. Wind 终端 → 工具 → 设置 → API 设置 → 启用相关 API
3. 确保 `.wind\WMain\` 配置目录非空（当前为空）
4. 或远程桌面人工登录 Wind 终端确认会话可用

**本次不修改任何配置、不创建 marker、不持久化 `REAL_WIND_CALL`。**

---

## 6. 产物清单

| 文件 | 说明 |
|---|---|
| `scripts/dshc_ignite_a01_wdf_fetch.ps1` | 执行器（预检 + 隔离 Excel + WSD 抓取 + 重试 + 安全回收 + 回执） |
| `scripts/dshc_ignite_a01_hardtimeout_watchdog.ps1` | 12 分钟硬超时看门狗（定向 PID，拒杀受保护进程） |
| `artifacts/wdf_preflight_check.json` | 预检 16/16 |
| `artifacts/dshc_ignite_run_receipt.json` | 运行回执（`FETCH_ERROR`） |
| `artifacts/dshc_ignite_a01_events.jsonl` | A01 本地事件流 |
| `artifacts/dshc_ignite_a01_channel_diagnosis.md` | 本文件 |
| `output_sample/wdf_sample_metals_raw.csv` | 宽表 CSV（仅表头，0 数据行） |
| `artifacts/cross_agent_artifact_index.json` | 索引（A01 章节为**纯增量**追加） |
| `scripts/_a01_*.ps1` | 通道诊断探测脚本（可复跑验证本报告结论） |
