# DSHC-TASK-A01-PHASE2 · WDF 通道诊断报告（A02）

> **工单**: DSHC-TASK-A01-PHASE2 · `auth_ref=A01-USER-REMOTE-002`（一次性点火令牌，本阶段**未消耗**，保持 UNUSED）
> **人工许可**: `PERM-A01-REMOTE-WIND-BRIDGE-001`（持有人远程桌面人工激活 Wind 桥接；Agent 仅观测，不执行任何管理员操作）
> **分支**: feature/v88-g1
> **运行状态**: `WAIT_BRIDGE` → **STANDBY**（两轮各 8 分钟等待，桥接仍未激活，未点火）
> **日期**: 2026-10-19 00:17–00:48 GMT+8（两轮完整等待窗口）

---

## 1. 结论（一句话）

**Wind 终端 API 桥接层仍未激活**：WDF 加载项正常加载、Connect=True、WSD 公式有响应（锚点返回裸日期 `2026-10-12` 而非数据网格），但没有任何数据网格返回（`DATA_GRID_EMPTY`）、无 Wind API 监听端口、`.wind` 配置目录 0 文件。两轮各 8 分钟等待窗口内环境指纹恒定不变，**人工尚未执行 PERM-A01-REMOTE-WIND-BRIDGE-001 的激活动作**。按工单 P1 契约：输出 `IGNITE_STATUS=WAIT_BRIDGE`，不点火，令牌不消耗，退回 STANDBY。

---

## 2. 执行事实（两轮）

| 项 | 第一轮（cycle 1） | 第二轮（cycle 2，权威回执） |
|---|---|---|
| 预检 | **26/26 PASS** | **26/26 PASS**（`artifacts/wdf_preflight_check.json`） |
| 桥接探测① | pid=8476 → `NOT_ACTIVATED` | pid=28656 → `NOT_ACTIVATED` |
| 探测结果 | `DATA_GRID_EMPTY`，rows=0，anchor=`2026-10-12` | 同左 |
| 等待窗口 | 8 分钟，15 轮轮询，1 信号变化，1 次重探（pid=22804） | 8 分钟，14 轮轮询，1 信号变化，1 次重探（pid=17124） |
| 重探结果 | `NOT_ACTIVATED` | `NOT_ACTIVATED` |
| 收尾 | STANDBY，令牌 UNUSED | STANDBY，令牌 UNUSED（回执 → `dshc_ignite_run_receipt.json`） |
| `probe_wind_calls` | 2（探测均为单字段小窗口） | 2 |
| `wind_api_calls` | **0**（仅当 WSD 返回数据网格才计数；从未有网格返回） | **0** |
| CSV | 保持表头（50B，SHA256 `BEF26114…0895`），0 数据行 | 同左（防覆盖护栏生效） |
| 后台 Excel 回收 | 仅 14644 存活；marker 已清 | `SAFETY_NET_RESET` 定向终止 17124，`marker_cleared=true`；仅 14644 存活 |
| 回执归档 | `dshc_ignite_run_receipt_A02_wait_cycle1.json` | 权威回执（本轮） |

**两轮合计**：4 次就绪探测（每次 1 条单字段 WSD 小窗口调用）、0 数据网格、0 数据行、令牌 0 消耗、0 次轰炸。

---

## 3. 桥接就绪探测证据

### 3.1 环境信号（廉价探测，无 Wind 调用）

| 信号 | 值（两轮全程恒定） |
|---|---|
| InitWAPI 进程 | pid=**14188**（启动于 10-17 16:33，两轮等待中从未重启） |
| wmain 进程 | pid=**824**（启动于 10-18 10:11） |
| Wind 监听端口 | **[]**（InitWAPI/wmain/WindUpdate 无任何 LISTEN 端口） |
| `.wind` 配置 | `C:\Users\YAQH\.wind` 存在但 **0 文件 / 9 空目录**（`etc\wings\jsmodule`、`res\wings\setting\formulas`、`users` 全空） |
| WDF 加载项 | `HKLM LoadBehavior=3`，`Connect=True`（代理 Excel 内 7 个 ProgId 可见） |

指纹比对在 14–15 轮轮询中**恒定不变**，证明人工激活动作在等待窗口内**未发生**。第 1 轮轮询出现 1 次「信号变化」为保守比对器的假阳性（重探后确认环境未变，结果仍 `NOT_ACTIVATED`），符合「仅在信号变化时重探」的防轰炸设计。

### 3.2 真实 WSD 单字段探测（每次 1 条，计入 `probe_wind_calls`）

```
=WSD("CU.SHF","CLOSE","2026-10-08","2026-10-16")     ← 8 个自然日小窗口
结果: 锚点 A1.Text = '2026-10-12'（裸日期）
分类: DATA_GRID_EMPTY（UsedRange ≥2x2 但无任何可用 date/value 对，rows=0）
```

与 A01 诊断结论**完全一致**：该 WDF 加载项已加载、已连接、WSD 有响应（返回裸日期而非 `#NAME?`），但 **Wind 终端 API 桥接层未激活**——WSD 从不产出数据网格。环境相比 2026-07-13（P54 调查）有改善（插件链路可用），但数据面仍是同一瓶颈：`.wind\WMain\` 空、无本地 API 端口。

### 3.3 与 P54 既有调查的一致性

`data-harbor/dsha_p49_prep/P49_backtest_audit/` 结论仍适用：`WindPy c_isConnectionOK=0`、`w.start() ErrorCode=-2`、`.wind\WMain\` 空、无 API 监听端口、`regsvr32` 静默失败。**桥接层激活是纯人工操作，无法远程/自动化完成。**

---

## 4. 红线自检（全绿）

| 红线 | 状态 |
|---|---|
| 一次性令牌 A01-USER-REMOTE-002 未误用 | ✅ `token_state=UNUSED`（未点火，未消耗，可等待人工激活后点火） |
| 绝不触碰前台 Excel PID 14644《永安期货研究中心 锌数据库-锭篇》 | ✅ 全程存活，保护锁生效 |
| 仅 Excel-WDF 链路，未用 WindPy / InitWAPI | ✅ `windpy_used=false` / `initwapi_used=false` |
| Agent 不执行管理员操作 | ✅ `admin_operation_performed=false`（人工许可 PERM-A01-REMOTE-WIND-BRIDGE-001 专属） |
| 12 分钟硬超时 | ✅ 后台 Excel 实际生命周期 ≤8s，远未触达 |
| 不轰炸 Wind | ✅ 每次仅 1 条小窗口单字段探测；等待窗口仅在信号变化时重探 |
| 事件全量入 G7 裁决账本 | ✅ `tracking_monitor_audit.jsonl`、`dshc_p90a_final_events.jsonl`、`dshc_ignite_a02_events.jsonl`（`a01_tag=A01-USER-REMOTE-002`） |
| 不产生永久 marker | ✅ `sample_fetch_allow_marker_created=false`；transient PID marker 已清除 |
| 不产生永久配置修改 | ✅ `permanent_config_modified=false` |
| 不改动 DSHA-P68 | ✅ 3 个资产哈希与预检锁定完全一致（`dsha_p68_deltas=[]`） |
| 不改动 DSHD-P80 | ✅ **执行器从未写入任何 P80 路径**（写范围仅为自有产物）；守护基线捕获到 4 个 P80 文件的哈希变化，经 mtime 证据（00:48:37–00:51:03，晚于本轮结束）确认是 **DSHD-P80 审计进程自身**在轮询中重写自己的快照/目录/简报（其快照已显示 `a01_tag=A01-USER-REMOTE-002`、`poll_count=21`、`windApiCallsMax=0`） |
| 不抢夺回测职责 | ✅ `backtest_run=false`、`no_backtest_stolen=true`、`no_p62_mirror=true`（CSV 留在 `output_sample/`，正式 sanity+9 步管线归 DSHA-P68） |
| 跨 agent 索引红线基线字段未动 | ✅ 顶层 `wind_api_calls=0` / `real_wind_call=false` / `marker_created=false` 保持不变（更新前断言） |

---

## 5. 需要的后续动作（非 Agent 能力范围，持有人执行）

1. **以管理员身份运行 `D:\bin\InitWAPI.exe`** 激活 API 桥接层（Agent 不可执行管理员操作）
2. **Wind 终端 → 工具 → 设置 → API 设置 → 启用外部 WSD**（需在终端 UI 内操作）
3. **修复 `C:\Users\YAQH\.wind\WMain` 空配置**（当前 0 文件；激活后应生成用户配置）
4. 或远程桌面登录 Wind 终端确认会话可用

完成后：桥接指纹将发生变化（新监听端口 / `.wind` 出现文件 / InitWAPI 重启），持有者只需再次下达点火指令（令牌仍为 UNUSED），执行器 `-Mode full` 即会自动探测 → 点火 → 出数。

**本次未修改任何配置、未创建 marker、未持久化 `REAL_WIND_CALL`、未消耗令牌。**

---

## 6. 产物清单

| 文件 | 说明 |
|---|---|
| `scripts/dshc_ignite_a02_wdf_fetch.ps1` | A02 执行器（预检 26 项 + 桥接探测 + 8 分钟等待循环 + 分批单字段 WSD + 内存对齐合并 + 安全回收 + 回执） |
| `artifacts/wdf_preflight_check.json` | 预检 26/26 PASS |
| `artifacts/wdf_bridge_readiness.json` | 桥接等待循环汇总（14 轮指纹信号日志，verdict=NOT_ACTIVATED） |
| `artifacts/dshc_ignite_run_receipt.json` | **权威回执**（WAIT_BRIDGE / STANDBY，令牌 UNUSED） |
| `artifacts/dshc_ignite_run_receipt_A02_wait_cycle1.json` | 第一轮回执归档（证据保留） |
| `artifacts/dshc_ignite_run_receipt_A01_USER_REMOTE_001.json` | A01 回执归档（证据保留） |
| `artifacts/dshc_raw_preview_check.json` | 原始 CSV 预览（0 行 / 表头 / 非空统计；**仅预览不跑回测**） |
| `artifacts/dshc_ignite_a02_events.jsonl` | A02 事件流（`a01_tag=A01-USER-REMOTE-002`） |
| `output_sample/wdf_sample_metals_raw.csv` | 宽表原始 CSV（保持表头，0 数据行，SHA256 `BEF26114…0895`） |
| `artifacts/cross_agent_artifact_index.json` | 索引（A02 章节纯增量追加；红线基线字段未动） |
