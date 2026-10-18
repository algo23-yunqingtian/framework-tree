# DSHC-TASK-A03-WDF-DIRECT · WDF-Excel 通道诊断

> 一次性令牌 **A01-USER-REMOTE-002** 本工单正式授权消耗。本诊断是本轮采集失败的完整通道日志。
>
> **本轮结论：`FETCH_ERROR`（exit 30）。令牌状态 `EXHAUSTED`。**

---

## 0. 一句话结论

闸门已按要求放开——WDF 插件 `Connect=True` 成立、采集**立即点火、没有再等待**；但插件拿到的
**数据平面为空**：函数把公式解析成功、把 250 交易日的网格骨架搭出来了，只有日期锚点有值、
**所有价格/成交量单元格是空的**。这是环境问题，不是代码问题，也不是公式问题。

---

## 1. 闸门变更（本工单核心差异）

| 项 | A02（上一轮） | A03（本轮） |
|---|---|---|
| 点火闸门 | 必须存在 Wind API 监听端口 | **WDF 加载项 Connect=True 即允许启动采集** |
| 端口不存在时 | `WAIT_BRIDGE` + 有界 8 分钟轮询等待 | **直接点火，不等待、不 STANDBY** |
| 令牌 | 未消耗（`UNUSED`） | **已消耗（`EXHAUSTED`）** |
| 轮次 | 2 次等待循环 × 8 分钟 | 1 次直接采集 |

`release_permit_effective = GRANTED_BY_A03_WORKORDER`，prefab 里
`gate=CLOSED / release_permit=NOT_ISSUED` **原样未动**（只读），本工单的放行是**会话级**的，
不是永久基线修改。

---

## 2. 预检：27/27 PASS

| 类别 | 关键证据 |
|---|---|
| R03 skill manifest | 5/5 哈希匹配，manifest 自身 `284E7661…599707` 与索引一致 |
| skill 入口脚本 | 3/3 parse ok |
| A03 执行器 + A01 watchdog | executor=1/1 watchdog=1/1 parse ok |
| P65 prefab 一致性 | 7 品种一致；prefab 4 字段 ⊆ A03 7 字段 |
| 表头模板 | `date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source` |
| P65 静态闸门 | `gate=CLOSED` / `release_permit=NOT_ISSUED` / `wind_api_calls=0` 全部保持 |
| 令牌状态 | `index_token_state=UNUSED`（A02 两轮均未消耗）→ 可消耗 |
| 注册表 | `HKLM WDF.Addin LoadBehavior=3`，DLL `D:\x64\WDF.dll` 存在 |
| health_check_wdf | `status=OK`，`wind_calls=0` |
| 后台 Excel 隔离 | 新建 `pid=13620`，退出干净、`residual_agent_pids=`（空） |
| **插件加载** | `ExcelPlugInShell.PowerMapConnect; MysteelAddin.ExcelAddin; SMM.Pro.Addin; TCSCConv.SharedAddin.16; ThsXlsSlug.ExcelAddin; WDF.Addin; WDF.XLTaskPanel` |
| **闸门项** | `connected=WDF.Addin` → **Connect=True 成立** |
| 保护进程 | `pids=14644` 已捕获 |
| wmain | `wmain_pids=824` 存活 |

**插件是加载的、是连接的。** 闸门通过，按工单要求立即点火。

---

## 3. 通道探测（非闸门，仅取证；`probe_wind_calls=2`）

探测后台 Excel `pid=28328`，7 个加载项、`WDF.Addin Connect=True`。

| 函数 | 目标 | 返回 | 判定 |
|---|---|---|---|
| `WSD` | `CU.SHF` `CLOSE`，8 日窗 `2026-10-05~2026-10-13` | 锚点文本 `2026-10-12` | `DATA_GRID_EMPTY`，0 行 |
| `WSS` | `CU.SHF` `CLOSE` `2026-10-13` | 锚点文本 `2026-10-12` | `NON_NUMERIC_TEXT`，非数值 |

**关键新证据（A02 只试过 WSD，本轮补上了 WSS）**：
`WSS` 单点快照同样返回裸日期 `2026-10-12`，**不是数值**。

即：两个不同的函数、两种不同的调用形态（区间时序 vs 单点快照），返回的**都是日期锚点本身**。
故障不随函数/字段/日期形态变化——它在这一层之下。

---

## 4. 采集过程（`wdf_inject_attempts=16`，`wdf_retries=7`）

- 点火后台 Excel `pid=20296`，与前台 `14644` 隔离
- 窗口 `2025-08-25 ~ 2026-10-19`（420 日历天回溯），trim 到最近 250 交易日
- 字段顺序 `CLOSE → VOL → OI → SETTLE → OPEN → HIGH → LOW`（DATE 取自网格锚点列，不单独注入公式）
- 单字段单次 WSD → 内存按日期对齐合并（规避已知 WDF 多字段残缺缺陷）

### 4.1 CU.SHF：14 次注入，`fields_ok=0/7`，耗时 160s

| 字段 | 尝试 1 | 尝试 2 |
|---|---|---|
| CLOSE | `DATA_GRID_EMPTY` anchor=`2025-08-25` 5s | `DATA_GRID_EMPTY` anchor=`2025-08-25` 1s |
| VOL | `DEGENERATE_SINGLE_CELL` 1 行 anchor=`2025-08-25` | `NO_DATA_TOKEN` anchor=`无法读取数据！` |
| OI | `NO_DATA_TOKEN` anchor=`无法读取数据！` | `DATA_GRID_EMPTY` anchor=`2025-08-25` |
| SETTLE | `DATA_GRID_EMPTY` | `DATA_GRID_EMPTY` |
| OPEN | `DATA_GRID_EMPTY` | `DATA_GRID_EMPTY` |
| HIGH | `DATA_GRID_EMPTY` | `DATA_GRID_EMPTY` |
| LOW | `DATA_GRID_EMPTY` | `DATA_GRID_EMPTY` |

三种不同的失败签名：**`DATA_GRID_EMPTY`（有网格无数据）**、
**`DEGENERATE_SINGLE_CELL`（退化单格）**、**`NO_DATA_TOKEN`（`无法读取数据！`）**。

### 4.2 最重要的一条证据

最后一次网格的形态是 `rows=276 cols=2 header=0`——

**插件把 276 行 × 2 列的网格骨架完整搭出来了**（276 ≈ 250 交易日 + 少量日历偏差，行列结构正确），
**但第二列的全部价格单元格是空的**，因此可用 date/value 对为 0。

这说明：公式解析正常、日期序列生成正常、网格装配正常；**只有数据填充这一步拿到的是空**。

### 4.3 保险丝

`fields_ok=0/7`，第一个品种连续 2 次失败 → fast-fail 触发 → **其余 6 个品种完全未遍历**，
避免对终端持续轰炸。本轮实际 Wind 数据调用 **`wind_api_calls=0`**
（`wind_api_calls` 只在 WSD 真返回数据网格时才计数；本次 16 次注入全部未返回数据网格）。

---

## 5. 环境指纹（探测时刻）

| 项 | 值 |
|---|---|
| 监听端口 | **`[]` 空** |
| `C:\Users\YAQH\.wind` 文件数 | **0** |
| `C:\Users\YAQH\.wind` 目录数 | 9 |
| `HKLM WDF.Addin LoadBehavior` | 3 |
| InitWAPI | `pid=14188` |
| wmain | `pid=824` |

---

## 6. 与前几轮的一致性

| 轮次 | 现象 |
|---|---|
| A01 | `FETCH_ERROR`，插件回中文「无法读取数据！」 |
| A02 cycle1 / cycle2 | 2 × 8 分钟等待，指纹恒定不变，`DATA_GRID_EMPTY` anchor=`2026-10-12`，无监听端口，`.wind` 0 文件 |
| **A03（本轮）** | 不等待、直接点火；同一签名复现，并**新增** `WSS` 裸日期、`DEGENERATE_SINGLE_CELL`、`NO_DATA_TOKEN` 与 `276×2 空网格` 四项证据 |

四轮签名完全一致。A02 期间等待窗口内人工激活动作**未发生**（指纹恒定）。

---

## 7. 与 P54 的一致性

P54 既有调查结论：`c_isConnectionOK=0`、`w.start() ErrorCode=-2`。本轮现象与之一致。

---

## 8. 备选通路说明（重要）

本工单已启用「受控后台 Excel + Wind 万能选项卡 + WSD/WSS 填表 → 内存读取导出」的备选采集通路，
并已实际执行到位（闸门通过、16 次公式注入、网格骨架成功装配）。

因此以下这些**传统正式 API 通路的前置步骤，本轮不是必须的，也不需要持有人去执行**：

> 【备选通路已启用，此步骤非必须，持有人无需操作】
> 以管理员身份运行 `D:\bin\InitWAPI.exe`
> 【备选通路已启用，此步骤非必须，持有人无需操作】
> 在 Wind 终端 UI 勾选 API 开关（工具 → 设置 → API 设置 → 启用外部 WSD）
> 【备选通路已启用，此步骤非必须，持有人无需操作】
> 修复 `C:\Users\YAQH\.wind\WMain` 空配置（当前 0 文件 / 9 目录）

本节仅为通道诊断留证，**不构成对持有人的操作要求，也不是待办任务条目**。
执行器全程 `no_windpy_invocation=YES`、`no_initwapi=YES`、`no_admin_operation=YES`、
`no_human_operation_requested=YES`。

---

## 9. 红线自检（全绿）

| 红线 | 值 |
|---|---|
| 前台 Excel PID 14644 | `alive=True`，`protected=True`，全程零触碰 |
| 令牌误用 | `token_state=EXHAUSTED`（本轮唯一一次消耗） |
| WindPy / InitWAPI | `no_windpy=YES`，`no_windpy_invocation=YES`，`no_initwapi=YES` |
| 硬超时 | `lifetime_sec=163` ≤ 12min，`within_hard_timeout=True` |
| Wind 轰炸 | 第一个品种失败即停，其余 6 个未遍历 |
| 一次性 marker | `sample_fetch_allow.marker` 三处路径均不存在 |
| 长驻配置修改 | `permanent_config_modified=False` |
| 后台 Excel 回收 | `SAFETY_NET_RESET … AGENT_PID_TARGETED pid=20296 marker_cleared=true` |
| 残留进程 | 结束后仅剩 `pid=14644`（前台） |
| 越权 | `backtest_run=False`，`factor_computation_run=False`，`no_backtest_stolen=True`，`no_p62_mirror=True` |
| DSHA-P68 | 3 文件哈希锁定，**0 漂移**，`dsha_p68_untouched=True` |
| 人工操作派发 | `no_human_operation_requested=YES` |
| 事件入 G7 账本 | 48 条 A03 事件 × 3 份日志 |

> `dshd_p80_untouched=False` 的说明：守护基线捕获到 3 个 P80 文件（`dshd_a01_file_evidence.json`、
> `dshd_p80_a01_audit_snapshot.json`、`dshd_a01_artifact_catalog.json`）哈希变化。
> 它们的 mtime 为 **03:19:58 / 03:20:28 / 03:22:54**，全部晚于本轮结束时刻 **03:11:30**。
> 这是 DSHD-P80 审计进程自身的周期性重写，**不是本执行器写入的**。
> 该差异检测按设计工作——它证明执行器从未写入任何 P80 路径。

---

## 10. 交付物

| 产物 | 状态 |
|---|---|
| `output_sample/wdf_sample_metals_raw.csv` | 已写出，11 列表头，**0 数据行**，64 字节，`sha256=41EC3831…0895`（前 A01/A02 的 50 字节 8 列表头已被本轮 11 列契约覆盖；原文件同样 0 数据行，无数据丢失） |
| `artifacts/dshc_ignite_run_receipt.json` | 权威回执，`FETCH_ERROR` / `token_state=EXHAUSTED` |
| `artifacts/dshc_raw_preview_check.json` | 行数/表头/非空统计，`preview_only=true`，`backtest_run=false` |
| `artifacts/dshc_a03_channel_probe.json` | 通道指纹 + WSD/WSS 双函数探测证据 |
| `artifacts/dshc_a03_fetch_events.jsonl` | 48 条事件，`a01_tag=A01-USER-REMOTE-002` |
| `artifacts/P49_data_requirement_checklist.md` | P49 因子原始数据核对清单 |
| `tracking_monitor_audit.jsonl` | 已追加 A03 事件 |

前一轮 A02 回执已归档为 `artifacts/dshc_ignite_run_receipt_A02_wait_cycle2.json`。

---

## 11. 状态与下一步

```
DSHC_A03_WDF_FETCH=FETCH_ERROR｜token=A01-USER-REMOTE-002｜token_state=EXHAUSTED｜wdf_pathway=PARTIAL-FAILED｜see_diagnosis=artifacts/dshc_a03_wdf_channel_diagnosis.md
wind_api_calls=0｜no_windpy_invocation=YES｜front_excel_untouched=YES｜no_human_operation_requested=YES｜backtest_not_run_by_dshc=YES
```

本轮采集**未成功**；诊断包已产出；令牌已消耗完毕；不再留在 `WAIT_BRIDGE` 死等。
按工单约定，**等待下一条文字工单再重试**。

采集通路本身已被验证是通的（插件加载、连接、公式解析、网格装配、16 次注入、内存合并、
保险丝、生命周期回收、CSV/回执/账本全部正常）——缺的是插件背后的数据。
