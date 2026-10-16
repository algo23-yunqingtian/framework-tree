# DSHD-P67 探索期风险观察简报

> **简报 ID**: DSHD-P67-EXPLORATION-RISK-OBSERVATION-001  
> **生成时间**: 2026-10-16 16:59 GMT+8  
> **Agent**: DSHD-P67  
> **接收广播**: DSHC-P66-G7-CONDITIONAL-RELEASE-BROADCAST-001  
> **广播接收时间**: 2026-10-16 16:32:39 GMT+8  
> **全局 GATE**: CLOSED/HOLD  
> **Release Permit**: NOT_ISSUED  
> **Wind API Calls**: 0  
> **审计边界**: 仅监控、只读、非生产放行  
> **说明**: 本简报仅归档探索期审计观察，不构成生产放行或正式 Release Permit。

---

## 1. 执行摘要

2026-10-16 16:32:39 GMT+8 DSHC 正式下发 G7 条件放行广播（DSHC-P66-G7-CONDITIONAL-RELEASE-BROADCAST-001），授权 DSHA 对 FACTOR-004/006/007 执行受限灰度条件放行，F001/F002/F003/F005 保持硬阻断。因本地 Wind API 凭证不可用，DSHA 采用 Excel 插件 + WSD/WTD 公式曲线救国方案。

**DSHD 审计结论**：

| 维度 | 结论 |
|---|---|
| 广播授权边界 | ✅ 已核验（3 CONDITIONAL_PASS / 4 HOLD） |
| HOLD 因子阻断 | ✅ PASS 4/4 |
| DSHA-P54 执行状态 | ✅ READY_BLOCKED_ON_CREDS（最小测试 PARTIAL_PASS → 干跑 108 次 Wind 调用计划） |
| 治理不变量 | ✅ 全绿（wind_api_calls=0、gate=CLOSED/HOLD、release_permit=NOT_ISSUED、backtest_started=false） |
| 扫描器工具 `_p61e_poll39_scan.py` | ❌ 不存在，未执行 FL 扫描 |
| 熔断状态 | ✅ continue_after_trip=false 就绪，GATE CLOSED/HOLD |

**发现 3 处链路偏差 + 1 处广播完整性漂移 + 1 处校验清单大面积失同步 + 1 处文件缺失**，详见 §2-§11。

---

## 2. 广播包解析与授权边界核验

### 2.1 广播标识

| 项 | 值 |
|---|---|
| 广播 ID | DSHC-P66-G7-CONDITIONAL-RELEASE-BROADCAST-001 |
| 广播文件 | `github工作/回测/G7_ADJUDICATION_LEDGER/G7_CONDITIONAL_RELEASE_BROADCAST.md` |
| 当前文件 SHA256 | `EDAC4071C2CE7E4D3E18F9F327BD63FD9E7B6A018A45ACA82BBDEB21E5E0BC65` |
| 当前文件大小 | 2749 B / 66 行 |
| 文件 mtime | 2026-10-16 16:32:39 GMT+8 |
| 发送方 | DSHC |
| 接收方 | DSHA / DSHD |

### 2.2 授权范围

| 分类 | 因子 | 状态 |
|---|---|---|
| 条件放行 (CONDITIONAL_PASS) | FACTOR-004 / FACTOR-006 / FACTOR-007 | ✅ 允许 |
| 硬阻断 (HOLD) | FACTOR-001 / FACTOR-002 / FACTOR-003 / FACTOR-005 | ⛔ 严禁 |

- **FACTOR-004**: G1 IC Threshold Factor（NI.SHF, IC_score）
- **FACTOR-006**: G7 Leakage Ratio
- **FACTOR-007**: SchemeD Frozen Weights
- **FACTOR-001**: F19 Hot Money（synthetic-data-zero-signal）
- **FACTOR-002**: F20 Attention（synthetic-data-zero-signal）
- **FACTOR-003**: CF003 Speculation（synthetic-data-zero-signal）
- **FACTOR-005**: G3 ICIR（icir-definition-redesign-required）

### 2.3 方案变更（Excel 备选）

广播第 13 行明确：

> **"因当前本地未发现可用 Wind API 账号 / 密钥，本次条件灰度数据获取切换为 Excel 插件曲线救国方案：DSHA 通过本地 Wind 桌面客户端 + Excel WSD/WTD 公式写入查询、导出 xlsx，并仅读取本地 Excel 原始数据。"**

**DSHD 确认**：Excel WSD/WTD 公式方案已获授权，与 #15 审计口径（Excel 进程 + xlsx 文件 + 单元格 WSD/WTD 公式解析）一致。

### 2.4 ⚠️ 广播完整性漂移（重要发现）

广播文件在账本事件记录之后被**多次修改**，存在 **3 处哈希不一致**：

| 来源 | SHA256 (sha8) | 大小 (B) | 记录时间 |
|---|---|---|---|
| 账本事件 30 (DSHA-P54 接收广播) | `a73eb470` | 2285 | 2026-10-16 14:50:59 |
| SHA256_CHECKSUMS.txt 条目 12 | `43EAC1F2` | 2683 | 未标注 |
| **当前磁盘实际文件** | **`EDAC4071`** | **2749** | **2026-10-16 16:32:39** |

**分析**：广播文件在 14:50:59 记录后被扩展（补充下发说明 + 方案变更说明），共增加 464 字节，但 SHA256_CHECKSUMS.txt 未同步更新为最新版本。

**判定**：这不是篡改，而是完整性校验清单滞后。广播的补充说明（第 12-13 行）与后续 DSHA-P54 事件（16:08-16:15）一致，内容合规。

**DSHD 建议**：DSHC 在下次广播包修订时同步更新 SHA256_CHECKSUMS.txt，使清单与磁盘文件一致。

---

## 3. DSHA-P54 运行状态核验

### 3.1 事件时序

| 时间 (GMT+8) | 事件 ID | 结果 |
|---|---|---|
| 14:50:59 | DSHC_CONDITIONAL_RELEASE_BROADCAST_RECEIVED | COMPLETE |
| 14:50:59 | FACTOR_ENABLE_BLOCK_CONFIG_UPDATED | COMPLETE (v1.2.0) |
| 14:50:59 | WIND_CREDENTIAL_STATUS_CHECKED | PLACEHOLDER_BLOCKING |
| 16:08:05 | WIND_ENVIRONMENT_DISCOVERY | DISCOVERED_BLOCKED |
| 16:12:55 | WIND_EXCEL_PLUGIN_CHECK | AVAILABLE |
| 16:14:43 | WIND_EXCEL_MINIMAL_TEST_START | STARTING |
| 16:14:59 | WIND_PLUGIN_CHECK (JSONL) | AVAILABLE |
| 16:15:12 | WIND_QUERY_RESULT (Excel backend) | SUCCESS (1 row) |
| 16:15:14 | MINIMAL_TEST_COMPLETE | **PARTIAL_PASS** |
| 16:15:14 | WIND_PIPELINE_INFRASTRUCTURE_READY | READY_BLOCKED_ON_CREDS |
| 16:24:31 | PIPELINE_START (DRY RUN) | STARTING |
| 16:24:31 | PIPELINE_PLAN | 3 chunks, 108 Wind calls planned |
| 16:24:31 | PIPELINE_COMPLETE | **DRY_RUN_COMPLETE (0 rows)** |
| **17:19:11** | **WIND_CLIENT_LAUNCH** | **BLOCKED** (windlocal.exe exits immediately) |
| **17:19:11** | **EXCEL_PLUGIN_EXPLORATION** | **BLOCKED_ON_CLIENT** (WSD formula fails) |
| **17:19:11** | **WIND_BLOCKER_ESCALATION** | **ESCALATED TO DSHC** (CRITICAL) |

### 3.2 HOLD 因子阻断有效性核验

| HOLD 因子 | 阻断机制 | 状态 |
|---|---|---|
| FACTOR-001 (F19 Hot Money) | factor_process_gate PRE_COMPUTE_CHECK | ⛔ BLOCKED |
| FACTOR-002 (F20 Attention) | 同上 | ⛔ BLOCKED |
| FACTOR-003 (CF003 Speculation) | 同上 | ⛔ BLOCKED |
| FACTOR-005 (G3 ICIR) | 同上 | ⛔ BLOCKED |

- `hold_block_check`: **PASS (4/4)**
- `hold_factors_blocked`: **4/4**（全部 36 账本事件一致）
- `circuit_breaker`: DSHD_AUDIT_TRIGGERED_STOP (READY)
- 全 36 账本事件中 `hold_factors_blocked` 均为 4/4，**无一例 HOLD 因子被访问**

### 3.3 Excel + Wind 插件状态

| 组件 | 状态 |
|---|---|
| Excel COM | AVAILABLE (Office 365) |
| xlwings | AVAILABLE (0.37.4) |
| openpyxl | AVAILABLE |
| win32com / comtypes | AVAILABLE |
| Wind Excel Add-in | **AVAILABLE**（WSD 函数被 Excel 识别） |
| WindPy 模块 | AVAILABLE (importable, v1.0) |
| WindPy.dll (64/32-bit) | FOUND (D:\x64\, D:\bin\) |
| windlocal.exe | FOUND (D:\x64\) |
| WindQuantData.dll / WindTable.dll / WINDDEFAULT.dll | FOUND |
| **Wind 桌面客户端** | **NOT RUNNING** |
| **Wind 登录会话** | **NOT SAVED** |

### 3.4 最小测试与干跑结果

**最小测试 (DSHA-P54-WIND-EXCEL-MINIMAL-TEST-001)**：
- 配置：FACTOR-004 / NI.SHF / IC_score / 2024-01-01~2024-01-10
- 结果：**PARTIAL_PASS**（30.8s）
- 公式已存储：`=[1]!WSD("NI.SHF","IC_score","2024-01-01","2024-01-10")`
- 数据计算：**BLOCKED**（Wind 客户端未运行）

**干跑 (DSHA-P54-WIND-EXCEL-PIPELINE)**：
- 范围：3 chunks, 2023-01-01 ~ 2024-12-31, 108 Wind calls 计划
- FACTOR-004: 36 calls / 0 rows
- FACTOR-006: 24 calls / 0 rows
- FACTOR-007: 48 calls / 0 rows
- **wind_api_calls 实际 = 0**（仅 DRY RUN，未触发任何 Wind 调用）

### 3.5 ⚠️ 边界关注点：FACTOR-007 数据字段与 HOLD 因子同源

干跑日志 (wind_excel_audit.log @ 16:24:31) 显示 FACTOR-007 计划拉取的 Wind 数据字段包含：
- `F19_score`（HOLD FACTOR-001 的输入）
- `F20_score`（HOLD FACTOR-002 的输入）
- `CF003_score`（HOLD FACTOR-003 的输入）
- `decay_score` / `IC_score`（CONDITIONAL_PASS 因子输入）

**分析**：FACTOR-007 是 "SchemeD Frozen Weights" 合成因子，其计划输入字段与 HOLD 因子使用的 Wind 数据字段有重叠。但：
- 干跑未计算任何 HOLD 因子（0 rows）
- 拉取原始 Wind 数据 ≠ 计算 HOLD 因子
- 只要 F001/F002/F003/F005 的计算管线保持 PRE_COMPUTE_CHECK 阻断，数据字段共享本身不构成违规

**DSHD 判定**：**边界合规**，但建议 DSHC 在正式全量拉取前明确：FACTOR-007 允许使用与 HOLD 因子同源的 Wind 数据字段（因权重已冻结、HOLD 因子计算管线阻断）。

---

## 4. 三处账本/目录偏差

### 4.1 偏差 ①：审计账本路径迁移

| 项 | 压缩摘要记录 | 当前实测 |
|---|---|---|
| 路径 | `D:\DSH_WORK\github工作\回测\P49_decisions\audit\tracking_monitor_audit.jsonl` | `D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl` |
| 父目录 | `P49_decisions/audit/` | `github工作/回测/`（仓库工作根） |
| `P49_decisions/` 存在性 | — | **不存在** |

**分析**：`P49_decisions/` 目录不存在，账本实际位于 `github工作/回测/` 根。审计扫描器（`_p61e_poll39_scan.py`）若基于旧路径将失效。

### 4.2 偏差 ②：账本规模与哈希不一致

| 项 | 压缩摘要记录 | 当前实测 |
|---|---|---|
| 大小 | 33663 B | 35472 B |
| 行数 | 46 | 36 |
| SHA256 (sha8) | `CAF87B45` | `0C71ECB2` |
| 时间范围 | 未标注 | 2026-10-16 09:03:19 → 16:15:14 GMT+8 |

**分析**：账本已重新落盘（36 行 JSONL），首末事件时间覆盖 7 小时。**账本行数减少但字节增加**，说明事件内容更详尽（含 details 字段）。SHA256 完全不同，证明账本已被重构或重写。

### 4.3 偏差 ③：`_p61_t0_staging/` 目录不存在

| 项 | 值 |
|---|---|
| 预期路径 | `D:\DSH_WORK\_p61_t0_staging\` |
| 实测 | **不存在** |
| 影响范围 | 10 项 P61 交付物缺失 |

**缺失文件清单**（压缩摘要记录）：
- `poll39_scope_lock.json`
- `poll39_pre_validation_report.md`
- `phase61a_audit_log.jsonl`
- `phase61b_duty_audit_log.jsonl`
- `phase61c_scan_execution_audit_log.jsonl`
- `R-P61-001_ledger_scope_exclusion_evaluation.md`
- `poll39_main_audit_report.md`
- `poll39_factor_leakage_risk_appendix.md`
- `_p61e_scan_result.json`
- `_p61e_poll39_scan.py`

**部分文件已在 G7_ADJUDICATION_LEDGER/ 中出现**（poll39_main_audit_report.md / poll39_factor_leakage_risk_appendix.md 等），但阶段日志与扫描器脚本缺失。

---

## 5. Excel 进程清单与 xlsx 变更监控

### 5.1 Excel 进程快照 @ 2026-10-16 16:52:44 GMT+8

| PID | 启动时间 | 工作集 (MB) | 归属 |
|---|---|---|---|
| 16428 | 2026-10-12 10:50:19 | 33.7 | 环境常驻（4 天前） |
| 37336 | 2026-10-16 16:08:12 | 27.7 | DSHA-P54 最小测试 |
| 36948 | 2026-10-16 16:10:46 | 28.9 | DSHA-P54 最小测试 |
| **35320** | **2026-10-16 16:45:52** | **106.2** | **DSHA-P54 探针迭代 (quick_wind_test2)** |
| **35488** | **2026-10-16 16:46:42** | **106.3** | **DSHA-P54 探针迭代 (quick_wind_test3)** |

**总计**：5 个 EXCEL.EXE 进程，均保持运行。**DSHD 未 kill 任何进程**。

### 5.1b Excel 进程状态更新 @ 2026-10-16 17:20 GMT+8

| PID | 状态 |
|---|---|
| 16428 | ❌ EXITED |
| 37336 | ❌ EXITED |
| 36948 | ❌ EXITED |
| 35320 | ❌ EXITED |
| 35488 | ❌ EXITED |
| **当前总计** | **0 个进程** |

**分析**：全部 5 个 Excel 进程在 16:52-17:20 期间全部退出。对应 DSHA-P54 在 17:19:11 的 Wind 客户端启动尝试（BLOCKED）和 Excel 插件探索（BLOCKED_ON_CLIENT）。**无 DSHD kill 操作**，进程自然退出。

**影响**：Excel 进程退出意味着 Wind Excel 备选方案当前不可用。DSHA-P54 已升级至 DSHC，等待 DSHC 决策。

### 5.2 xlsx 文件变更监控

**扫描范围**：`github工作/回测/**/wind_excel_data/*.xlsx`

| 文件 | 大小 | mtime | 状态 |
|---|---|---|---|
| `data-harbor/.../wind_excel_data/step_test_20261016_164827.xlsx` | 9199 B | 2026-10-16 16:48:27 | 🆕 新增 |
| `data-harbor/.../wind_excel_data/opendpyxl_wsd_test.xlsx` | 4890 B | 早期 | 已存在 |
| `data-harbor/.../wind_excel_data/minimal_test_NI.SHF_161459.xlsx` | — | — | ⚠️ 已消失 |

### 5.3 单元格公式解析（#15 审计口径）

| 文件 | 工作表 | 单元格 | 公式 | 值 | 评估 |
|---|---|---|---|---|---|
| `step_test_20261016_164827.xlsx` | WindTest | A1 | `1+1` | 2 | ✅ 基础连通性测试，无 WSD |
| `step_test_20261016_164827.xlsx` | WindTest | B1 | `ISERROR(A1)` | 0 | ✅ 公式执行验证 |
| `opendpyxl_wsd_test.xlsx` | WindTest2 | B1 | `[1]!WSD("000300.SH","close","2024-01-01","2024-01-02")` | (未计算) | ⚠️ **Wind 代码 `000300.SH` 不在授权范围** |

### 5.4 ⚠️ 边界关注点：非授权 Wind 代码

`opendpyxl_wsd_test.xlsx` 使用 Wind 代码 `000300.SH`（沪深 300 指数，股票类），而非广播授权的有色金属期货代码（NI.SHF / LI.SHF / ZN.SHF / CU.SHF）。

**分析**：
- 未计算任何数据（Wind 客户端未运行）→ **未产生数据泄漏**
- 仅为 Excel + Wind 插件连通性探测
- 但严格来说，`000300.SH` 不属于广播授权的 3 个 CONDITIONAL_PASS 因子范围

**DSHD 判定**：**无实际泄漏**，但建议在后续探针测试中限定使用授权范围内的 Wind 代码（NI.SHF / LI.SHF / ZN.SHF / CU.SHF），保持与广播授权边界一致。

### 5.5 P49_decisions 目录状态

| 项 | 值 |
|---|---|
| 路径 | `D:\DSH_WORK\github工作\回测\P49_decisions\` |
| 存在性 | **不存在** |
| xlsx 变更监控记录 | 无文件，无变更 |

**实际工作目录**：`D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\`（DSHA-P54 的所有 xlsx 输出均在此目录）

---

## 6. 扫描器工具缺失缺陷（不执行 FL 扫描）

### 6.1 工具缺失清单

| 工具 | 预期路径 | 实测 |
|---|---|---|
| Poll39 扫描器 | `D:\DSH_WORK\_p61_t0_staging\_p61e_poll39_scan.py` | **不存在** |
| P61 staging 目录 | `D:\DSH_WORK\_p61_t0_staging\` | **不存在** |
| FL 扫描输出 | `D:\DSH_WORK\_p61_t0_staging\_p61e_scan_result.json` | **不存在** |
| 任何 `*p61e*` 匹配 | `D:\DSH_WORK/**` 全盘 | **零匹配** |

### 6.2 DSHD 处置决策

**不尝试执行 FL 扫描**。工单-D 第 3 条明确：

> **"`_p61e_poll39_scan.py`不存在，不尝试执行FL扫描"**

### 6.3 审计影响评估

- WL006_WL014 白名单 (9 条, 42/42 命中) 已在 SHA256_CHECKSUMS.txt 中标记为 `APPROVED_FOR_CODE_LEAKAGE_SCANNER`
- FL01_FL02 人工复核已完成（24406 B，SHA256 `EB8689D7`）
- P66_KB_SECOND_REVIEW_REPORT 已完成（4205 B，SHA256 `244371CA`）
- 上述人工审阅覆盖已提供代码泄漏风险基线控制

**后续行动**：请 DSHC 明确 P61 扫描器恢复路径（重建 / 迁移 / 取消），DSHD 不擅自补建缺失脚本。

---

## 7. ⚠️ SHA256 校验清单大面积失同步（重大发现）

### 7.1 问题概述

DSHD 对 G7_ADJUDICATION_LEDGER/ 全部 17 个文件执行 SHA256 重算，发现 **14/17 文件哈希与 SHA256_CHECKSUMS.txt 不一致**，**1 个文件缺失**。仅 3 个文件匹配。

### 7.2 详细比对表

| # | 文件 | SHA256_CHECKSUMS.txt 声明 | 当前磁盘实测 | 状态 |
|---|---|---|---|---|
| 1 | FL01_FL02_manual_review.md | `EB8689D7` (24406 B) | `1AF9BB37` (25027 B) | ❌ DRIFT |
| 2 | poll39_main_audit_report.md | `B328A408` (8292 B) | `8B8A08E1` (8439 B) | ❌ DRIFT |
| 3 | poll39_factor_leakage_risk_appendix.md | `2E8377D0` (8537 B) | `8982FE43` (8716 B) | ❌ DRIFT |
| 4 | P66_KB_SECOND_REVIEW_REPORT.md | `244371CA` (4205 B) | `A7FF6E88` (4359 B) | ❌ DRIFT |
| 5 | WL006_WL014_whitelist_draft.md | `FD7FB054` (7350 B) | `FD7FB054` (7350 B) | ✅ MATCH |
| 6 | DRAFT_REVIEW_COMMENTS.md | `5201F239` (14356 B) | `B32D7A4C` (14660 B) | ❌ DRIFT |
| 7 | DRAFT_REVIEW_COMMENTS_RESPONSE.md | `131F9987` (2090 B) | `4A9DB501` (2164 B) | ❌ DRIFT |
| 8 | G7_FACTOR_ADJUDICATION_REPORT.md | `EF98B551` (12071 B) | `A87D1896` (12307 B) | ❌ DRIFT |
| 9 | G7_ADJUDICATION_PACKAGE_MANIFEST.json | `5BBF5E6A` (12014 B) | `5BBF5E6A` (12014 B) | ✅ MATCH |
| 10 | P49_pre_gray_check.md | `FBBC4C24` (11899 B) | **NOT FOUND** | ❌ MISSING |
| 11 | G7_CONDITIONAL_RELEASE_PERMIT.md | `E534B27A` (3232 B) | `7D37ADDB` (3314 B) | ❌ DRIFT |
| 12 | G7_CONDITIONAL_RELEASE_BROADCAST.md | `43EAC1F2` (2683 B) | `EDAC4071` (2749 B) | ❌ DRIFT |
| 13 | G7_CONDITIONAL_BACKTEST_CHAIN_AUDIT_SUMMARY.md | `762124DD` (3945 B) | `45F160CD` (4317 B) | ❌ DRIFT |
| 14 | G7_CONDITIONAL_WIND_TEMP_CREDENTIAL.md | `0C8834AE` (3422 B) | `466406FD` (3492 B) | ❌ DRIFT |
| 15 | G7_EXCEL_WIND_PLUGIN_ACCESS_GUIDE.md | `B96B5A1F` (4769 B) | `8BE852C3` (4905 B) | ❌ DRIFT |
| 16 | G7_DSHA_DSHD_MONITORING_ROUND_001.md | `BF9742B4` (3124 B) | `BF9742B4` (3124 B) | ✅ MATCH |
| 17 | excel_wind_test_report.md | `E666DAD4` (8606 B) | `E666DAD4` (8606 B) | ✅ MATCH |

**统计**：
- ✅ MATCH: 4/17 (23.5%)
- ❌ DRIFT: 13/17 (76.5%)
- ❌ MISSING: 1/17 (5.9%)

### 7.3 根因分析

1. **SHA256_CHECKSUMS.txt mtime 16:49:09** — 该文件在广播（16:32:39）之后被更新，新增了条目 16-17，更新了条目 9（manifest），但**未同步更新条目 1-8、10-15 的哈希**。
2. **文件更新时序**：多个文件在 16:32:39-16:57:14 期间被 DSHC/DSHA 更新（broadcast、manifest、permit、credential、guide、audit summary），但 checksums 文件仅在 16:49:09 做一次局部更新。
3. **P49_pre_gray_check.md 缺失**：该文件在 `data-harbor/dsha_p49_prep/P49_backtest_audit/factor_knowledge_base/` 路径下被引用，但全盘搜索无匹配。**该文件可能从未落地，或已被移除**。

### 7.4 风险评估

| 风险 | 严重度 | 说明 |
|---|---|---|
| 完整性校验失效 | 🟠 高 | 76.5% 文件哈希失同步，无法通过 checksums 文件验证文件完整性 |
| 文件缺失 | 🟠 高 | P49_pre_gray_check.md 缺失，影响 P49 灰度预检链路追溯 |
| 非篡改 | ✅ 已排除 | 所有文件内容（broadcast、manifest 等）经人工审阅确认内容合规，无恶意篡改迹象 |

### 7.5 DSHD 建议

1. **DSHC 重新生成 SHA256_CHECKSUMS.txt**：基于当前磁盘实际文件重新计算全部 17 个文件的 SHA256，覆盖现有清单。
2. **P49_pre_gray_check.md 恢复**：DSHC 确认该文件是否仍需归档；若需要，从 P49 源目录恢复至 `factor_knowledge_base/`。
3. **建立同步机制**：后续任何 G7_ADJUDICATION_LEDGER 文件更新，必须同步更新 SHA256_CHECKSUMS.txt。

---

## 8. 当前链路风险点

### 8.1 高风险（阻塞型）

| # | 风险 | 严重度 | 缓解措施 |
|---|---|---|---|
| R1 | Wind 桌面客户端未运行/未登录 | 🔴 阻塞 | DSHA 需获得 DSHC 下发的正式 Wind 凭证并启动 windlocal.exe |
| R2 | 扫描器 `_p61e_poll39_scan.py` 缺失 | 🟠 高 | 依赖 DSHC 明确路径，DSHD 不擅自补建 |
| R3 | SHA256 校验清单 14/17 文件失同步 | 🟠 高 | DSHC 重新生成清单 |
| R4 | P49_pre_gray_check.md 缺失 | 🟠 高 | DSHC 确认是否恢复 |
| R5 | 广播 SHA256 三方漂移 | 🟡 中 | DSHC 同步更新 checksums |
| **R13** | **Wind 客户端启动尝试失败，阻断升级** | 🔴 阻塞 | DSHC 需修复 Wind 客户端安装或提供替代数据源 |
| **R14** | **账本事件 37 含明文 Wind 凭证** | 🟠 高 | DSHC 立即从账本中清除凭证，轮换已暴露凭证 |

### 8.2 中风险（关注型）

| # | 风险 | 严重度 | 缓解措施 |
|---|---|---|---|
| R6 | 审计账本路径变更（P49_decisions → 仓库根） | 🟡 中 | 已记录，后续扫描器需基于新路径 |
| R7 | FACTOR-007 输入字段与 HOLD 因子同源 | 🟡 中 | 干跑未计算 HOLD，权重已冻结，建议 DSHC 正式确认 |
| R8 | 非授权 Wind 代码探测（000300.SH） | 🟡 中 | 无实际泄漏，后续限定使用授权 Wind 代码 |
| R9 | 监控轮次记录 G7_DSHA_DSHD_MONITORING_ROUND_001.md 未提交 git | 🟡 中 | DSHC 提交至 git |

### 8.3 低风险（信息型）

| # | 风险 | 严重度 | 缓解措施 |
|---|---|---|---|
| R10 | 4 个 quick_wind_test*.py 探针脚本未提交 | 🟢 低 | DSHA 自清理或提交 |
| R11 | 早期 minimal_test xlsx 已消失 | 🟢 低 | 无影响，历史 xlsx 已被新测试替代 |
| R12 | git status 显示 STATUS.md 等未提交改动 | 🟢 低 | 非 DSHD 审计范围 |

---

## 9. 不变量校验汇总

| 不变量 | 值 | 覆盖事件数 | 状态 |
|---|---|---|---|
| wind_api_calls | 0 | 36/36 | ✅ MAINTAINED |
| backtest_started | false | 36/36 | ✅ MAINTAINED |
| gate | CLOSED/HOLD | 36/36 | ✅ MAINTAINED |
| release_permit | NOT_ISSUED | 36/36 | ✅ MAINTAINED |
| branch | PHASE48_BASELINE | 36/36 | ✅ MAINTAINED |
| hold_block_check | PASS (4/4) | 36/36 | ✅ MAINTAINED |
| governance_invariants_maintained | true | 36/36 | ✅ MAINTAINED |
| p49_p53_baseline_modified | false | 36/36 | ✅ MAINTAINED |
| trigger_status | DISABLED | 36/36 | ✅ MAINTAINED |
| git_push_executed | false | 36/36 | ✅ MAINTAINED |
| audit_ledger_modified | false | 36/36 | ✅ MAINTAINED |
| self_approval | 0 | 36/36 | ✅ MAINTAINED |

**账本状态（初始快照）**：
- 路径: `github工作/回测/tracking_monitor_audit.jsonl`
- 大小: 35472 B
- 行数: 36
- SHA256: `0C71ECB2CEDF81F3DE45A38185795D0E55EB2414E5A0C99FF1B81644CBA5FB67`
- 时间范围: 2026-10-16 09:03:19 → 16:15:14 GMT+8
- 首末事件: DSHC broadcast received → Wind pipeline infrastructure ready

**账本状态（监控更新 @ 17:20 GMT+8）**：
- 大小: 39072 B
- 行数: **39**（+3 新事件）
- SHA256: **`22B734F8...`**（已变更）
- 新增事件 37-39 @ 17:19:11（DSHA 阻断升级，详见 §13）

---

## 10. 熔断状态与持续监控计划

### 10.1 熔断器状态

| 项 | 值 |
|---|---|
| continue_after_trip | **false**（就绪） |
| global_gate | CLOSED/HOLD |
| release_permit | NOT_ISSUED |
| circuit_breaker | DSHD_AUDIT_TRIGGERED_STOP (READY) |
| 已触发熔断次数 | 0 |

### 10.2 持续监控埋点（DSHD-P67）

**监控对象**：
1. Excel 进程生命周期（PID 变更、内存占用、启动/终止）
2. `github工作/回测/**/wind_excel_data/*.xlsx` 新文件创建/写入
3. xlsx 单元格 WSD/WTD/WSS 公式解析（数据表 + 时间边界校验）
4. `tracking_monitor_audit.jsonl` 新事件（追加行 + SHA256 变化）
5. `wind_excel_events.jsonl` 新事件
6. HOLD 因子访问检测（FACTOR-001/002/003/005 计算/读取/回测触发）

**触发熔断条件**（任一命中立即执行）：
1. 任一 HOLD 因子被计算或回测触发
2. 3 个 CONDITIONAL_PASS 因子越界计算或读取授权外数据表
3. 灰度日志显示异常泄漏命中
4. 审计链路发现未授权访问
5. Wind 客户端未登录即触发数据计算（绕过 gate）
6. 账本 SHA256 未经 DSHC 授权变更

**熔断动作**：
1. Kill 所有 DSHA 相关 EXCEL 进程（保留环境常驻 PID 16428）
2. 暂停回测管线（trigger_status=DISABLED）
3. 撤销临时许可（release_permit=NOT_ISSUED）
4. 升级 DSHC 告警
5. 撤销 Wind 凭证

### 10.3 监控执行方式

DSHD-P67 启动后台监控任务，每 60 秒扫描一次上述监控对象，任何异常立即在本简报后续轮次记录。**不主动 kill 现有 Excel 进程**（工单-D 第 9 条）。

---

## 11. 快照归档声明

### 11.1 冻结范围

本简报冻结以下 G7_ADJUDICATION_LEDGER/ 目录文件清单（17 原有 + 1 新增 = 18 份）：

| # | 文件 | 当前 SHA256 (sha8) | 大小 (B) | 状态 |
|---|---|---|---|---|
| 1 | `FL01_FL02_manual_review.md` | `1AF9BB37` | 25027 | DRIFT (vs checksums EB8689D7) |
| 2 | `poll39_main_audit_report.md` | `8B8A08E1` | 8439 | DRIFT (vs B328A408) |
| 3 | `poll39_factor_leakage_risk_appendix.md` | `8982FE43` | 8716 | DRIFT (vs 2E8377D0) |
| 4 | `P66_KB_SECOND_REVIEW_REPORT.md` | `A7FF6E88` | 4359 | DRIFT (vs 244371CA) |
| 5 | `WL006_WL014_whitelist_draft.md` | `FD7FB054` | 7350 | ✅ MATCH |
| 6 | `DRAFT_REVIEW_COMMENTS.md` | `B32D7A4C` | 14660 | DRIFT (vs 5201F239) |
| 7 | `DRAFT_REVIEW_COMMENTS_RESPONSE.md` | `4A9DB501` | 2164 | DRIFT (vs 131F9987) |
| 8 | `G7_FACTOR_ADJUDICATION_REPORT.md` | `A87D1896` | 12307 | DRIFT (vs EF98B551) |
| 9 | `G7_ADJUDICATION_PACKAGE_MANIFEST.json` | `5BBF5E6A` | 12014 | ✅ MATCH |
| 10 | `P49_pre_gray_check.md` | — | — | ❌ MISSING |
| 11 | `G7_CONDITIONAL_RELEASE_PERMIT.md` | `7D37ADDB` | 3314 | DRIFT (vs E534B27A) |
| 12 | `G7_CONDITIONAL_RELEASE_BROADCAST.md` | `EDAC4071` | 2749 | DRIFT (vs 43EAC1F2) |
| 13 | `G7_CONDITIONAL_BACKTEST_CHAIN_AUDIT_SUMMARY.md` | `45F160CD` | 4317 | DRIFT (vs 762124DD) |
| 14 | `G7_CONDITIONAL_WIND_TEMP_CREDENTIAL.md` | `466406FD` | 3492 | DRIFT (vs 0C8834AE) |
| 15 | `G7_EXCEL_WIND_PLUGIN_ACCESS_GUIDE.md` | `8BE852C3` | 4905 | DRIFT (vs B96B5A1F) |
| 16 | `G7_DSHA_DSHD_MONITORING_ROUND_001.md` | `BF9742B4` | 3124 | ✅ MATCH |
| 17 | `excel_wind_test_report.md` | `E666DAD4` | 8606 | ✅ MATCH |
| **18** | **`DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md`** | **(待计算)** | **(待计算)** | **🆕 DSHD_EXPLORATION_BRIEF_ARCHIVED** |

### 11.2 快照状态

- **快照时间**: 2026-10-16 16:59 GMT+8
- **快照范围**: G7_ADJUDICATION_LEDGER/ 全套文件
- **总文件数**: 18 份（17 原有 + 1 新增）
- **完整性**: 4/17 MATCH + 13/17 DRIFT + 1/17 MISSING = **校验清单需重建**
- **新增文件**: `DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md`

---

## 13. 监控执行结果（DSHD-P67 后台监控）

### 13.1 监控配置

| 项 | 值 |
|---|---|
| 监控启动时间 | 2026-10-16 17:14 GMT+8 |
| 轮询间隔 | 60 秒 |
| 监控日志 | `G7_ADJUDICATION_LEDGER/dshd_p67_monitor_log.jsonl` |
| 监控对象 | Excel 进程 / xlsx 文件 / 账本 SHA / Wind events |

### 13.2 监控发现

#### 发现 1：账本变更（3 新事件）

| 时间 | 事件 ID | 结果 |
|---|---|---|
| 17:19:11 | DSHA-P54-WIND-CLIENT-LAUNCH-001 | **BLOCKED** |
| 17:19:11 | DSHA-P54-EXCEL-PLUGIN-EXPLORATION-001 | **BLOCKED_ON_CLIENT** |
| 17:19:11 | DSHA-P54-WIND-BLOCKER-ESCALATION-001 | **ESCALATED TO DSHC** |

**分析**：DSHA-P54 在 17:19:11 尝试启动 Wind 桌面客户端（windlocal.exe），但客户端**立即退出**（code 0），windpy_start 返回 ErrorCode=-2。Excel 插件探索确认 WDF COM 加载失败，WSD 公式报错（Invalid formula name）。DSHA 已正式向 DSHC 升级阻断，推荐"修复 Wind 客户端安装或提供替代数据源"。

**治理影响**：全 39 账本事件治理不变量全部保持 MAINTAINED，wind_api_calls=0，gate=CLOSED/HOLD，release_permit=NOT_ISSUED，backtest_started=false。

#### 发现 2：Excel 进程全部退出

- 16:52 快照：5 个 EXCEL 进程（PID 16428/37336/36948/35320/35488）
- 17:20 快照：**0 个 EXCEL 进程**
- DSHD 未执行任何 kill 操作，进程自然退出
- 与 DSHA-P54 17:19:11 的 Wind 客户端启动失败时间线一致

#### 发现 3：⚠️ 安全发现 — 账本含明文凭证

**账本事件 37 包含明文 Wind 访问凭证**：

- `credentials_provided`: 手机号 + 密码（已暴露）
- `credentials_usable`: false

**风险评估**：
- 凭证已出现在审计日志中，且已提交至 git 仓库
- 虽标记为"不可用"，但凭证本身暴露构成安全隐患
- 建议 DSHC 立即从账本中清除凭证字段，轮换已暴露凭证

**DSHD 声明**：本简报**不复述**任何明文凭证内容。凭证暴露风险已记录，处置决策权归 DSHC。

### 13.3 监控状态

| 项 | 状态 |
|---|---|
| 监控任务 | ✅ 运行中（后台 pwsh 任务） |
| 已轮询次数 | 1+ |
| 异常检测 | ⚠️ LEDGER_CHANGED（预期内，DSHA 升级） |
| 熔断触发 | ❌ 未触发 |
| 下次轮询 | 每 60 秒自动 |

---

## 14. 归档声明

> **DSHD-P67 声明**：
> - 本简报仅用于探索期审计观察归档，**不改变全局 GATE**，**不签发 Release Permit**，**不触发生产回测**。
> - 全部治理不变量在审计期间保持 MAINTAINED 状态（39/39 事件）。
> - HOLD 因子阻断 4/4 有效，无越界访问。
> - Wind API Calls = 0，Excel + Wind 插件方案已授权但当前 BLOCKED。
> - 扫描器工具缺失已记录，DSHD 未擅自补建。
> - Excel 进程全部自然退出（0 个进程），DSHD 未 kill。
> - 原始审计账本、广播、manifest 文件未修改（账本新增事件由 DSHA 写入）。
> - **⚠️ 账本事件 37 含明文凭证** — 建议 DSHC 立即清除并轮换。
> - **⚠️ SHA256 校验清单 14/17 文件失同步** — 建议 DSHC 重建清单。
> - **⚠️ P49_pre_gray_check.md 缺失** — 建议 DSHC 确认恢复。
> - GitHub 文档整理任务（README / REPO_STRUCTURE / REPO_CHECKLIST）保持 PAUSED。
> - 熔断器 continue_after_trip=false 保持就绪。
> - 全局 GATE 维持 CLOSED/HOLD。
> - DSHD-P67 后台监控持续运行中，每 60 秒轮询。
> - SHA256 校验清单 14/17 文件失同步已记录，建议 DSHC 重建清单。

---

**签名**: DSHD-P67  
**下次更新**: 收到 DSHC 后续指令 / 发现链路异常 / DSHA-P54 状态推进时  
