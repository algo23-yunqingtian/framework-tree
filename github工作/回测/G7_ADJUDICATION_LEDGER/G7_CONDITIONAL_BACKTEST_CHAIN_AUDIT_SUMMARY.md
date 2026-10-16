# G7 条件回测链路审计摘要草案

> **文档ID**: DSHC-P66-G7-CONDITIONAL-BACKTEST-CHAIN-AUDIT-001  
> **生成时间**: 2026-10-16 GMT+8  
> **关联广播**: `G7_CONDITIONAL_RELEASE_BROADCAST.md`  
> **关联临时凭证**: `G7_CONDITIONAL_RELEASE_PERMIT.md`  
> **关联台账**: `G7_ADJUDICATION_PACKAGE_MANIFEST.json`  
> **范围声明**: 仅记录本次受限灰度条件放行的审计边界、监控目标与紧急撤销预案，不构成生产放行、全局放行或完整 Release Permit。

---

## 1. 本次灰度放行范围

| 项目 | 值 |
|---|---|
| 条件放行范围 | FACTOR-004 / FACTOR-006 / FACTOR-007 |
| 冻结 HOLD 因子 | FACTOR-001 / FACTOR-002 / FACTOR-003 / FACTOR-005 |
| 链路类型 | 受限灰度链路 |
| 全局 GATE | CLOSED/HOLD |
| 全局 Release Permit | NOT_ISSUED |
| Wind API Calls | 0 |
| Git push | NOT_EXECUTED |
| P49/P53 基线 | LOCKED / 未修改 |
| 审计账本基线 | 仅允许条件放行归档与校验更新 |

---

## 2. 风险边界

1. 本次仅开放 3 个 `CONDITIONAL_PASS` 因子，不代表任何生产放行。
2. 4 个 `HOLD` 因子维持冻结，禁止任何计算、数据读取、回测触发或 Wind 拉取。
3. 条件通道仅限回测链路的验证性记录，不得扩展到生产环境。
4. 若条件因子出现越界访问、越权写入或异常泄漏命中，立即撤销临时许可。
5. 若 HOLD 因子被触发，立即关闭条件通道并进入紧急处置。
6. 若出现任何新的泄漏证据，立即升级至审计复核。

---

## 3. 预期监控指标

| 指标 | 目标/阈值 | 说明 |
|---|---|---|
| 条件放行因子进入链路数 | 3 | 仅 FACTOR-004 / 006 / 007 |
| HOLD 因子触发数 | 0 | 触发即撤销 |
| Wind API Calls | 0 | 禁止外部数据拉取 |
| 灰度链路越界访问 | 0 | 发现即中止 |
| 异常泄漏命中 | 0 | 发现即撤销并复核 |
| 审计告警 | 0 | 出现异常立即升级 |
| Release Permit 状态 | NOT_ISSUED | 维持不变 |
| Gate 状态 | CLOSED/HOLD | 维持不变 |

---

## 4. 紧急撤销触发条件

出现以下任一情况，立即撤销临时许可并关闭条件通道：

1. 任一 HOLD 因子被计算、读取或触发。
2. 任一条件因子越界访问或越权写入。
3. 灰度链路日志出现异常泄漏命中。
4. DSHD 审计发现未授权访问或异常事件。
5. 调度或下游反馈要求暂停。
6. 任何新的代码层泄漏证据出现。

---

## 5. 审计摘要结论

- 本次审计摘要仅记录条件灰度的范围、边界与撤销预案。
- 它不改变全局 GATE，不签发完整 Release Permit，不触发生产回测。
- 后续若 DSHA / DSHD 任一反馈异常，将立即按本摘要第 4 节执行撤销流程。

---

## 6. 临时 Wind 访问凭证记录

| 项目 | 当前状态 |
|---|---|
| 凭证 ID | DSHC-P66-G7-WIND-TEMP-CRED-001 |
| 有效期 | 2023-01-01 至 2024-12-31 |
| 访问边界 | 仅限 3 个条件放行因子所需 Wind 数据表；禁止跨表、跨时间范围查询 |
| 允许因子 | FACTOR-004 / FACTOR-006 / FACTOR-007 |
| 禁止因子 | FACTOR-001 / FACTOR-002 / FACTOR-003 / FACTOR-005 |
| 撤销触发条件 | 任一 HOLD 因子触发、越界访问、异常拉取、异常泄漏命中、DSHD 告警 |
| 凭证用途 | 仅限 DSHA Wind 连通性验证与受限灰度回测 |
| 数据获取方式 | 本地 Wind 桌面客户端 + Excel WSD/WTD 公式导出 xlsx |
| 凭证可用性 | 当前本地未发现可用 Wind API 账号 / 密钥 |
| 接入指南 | `G7_EXCEL_WIND_PLUGIN_ACCESS_GUIDE.md` |

## 7. 记录状态

| 项目 | 当前状态 |
|---|---|
| 摘要用途 | 条件灰度审计预案 |
| 是否允许修改 | 仅可归档更新 |
| 是否触发运行 | NO |
| 是否改变全局状态 | NO |
| DSHA/DSHD 执行反馈 | MONITORING_ROUND_002_RECORDED |
| DSHA 最小测试 | PARTIAL_PASS |
| DSHD 审计准备 | AUDIT_LINK_ENABLED_EXCEL_FALLBACK |
| 监控轮次归档 | `G7_DSHA_DSHD_MONITORING_ROUND_002.md` |
| DSHD 探索期简报 | `DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md` |
| DSHA 测试报告 | `data-harbor/dsha_p49_prep/P49_backtest_audit/excel_wind_test_report.md` |

> **最终声明**: 本文件为条件回测链路的审计摘要草案，不扩展条件范围，不解除冻结，不改变全局管控状态。