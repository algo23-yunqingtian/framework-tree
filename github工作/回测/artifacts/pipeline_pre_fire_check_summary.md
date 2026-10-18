# P83–P86 环境治理与 P87 终验收摘要

## 基线
- 基线：feature/v88-g1 @ 01a022fdffb36e603abd623842cef65f80f24c92
- Gate：CLOSED/HOLD
- Release permit：NOT_ISSUED
- Wind API calls：0
- DEFECT-012：CLOSED
- Matlab：ignored

## P83–P86 过程回顾
- P83：建立 Wind 本地能力图与手动触发备份脚本，确认 WSS 可用、WSD/WST 受限。
- P84：准备小样取数环境，生成模板与预检脚本，确认模板 10 日窗口。
- P85：完成 wmain 前台恢复、COM 预检通过、模板有效性确认。
- P86：生成小样控制器、后检清单、就绪 JSON 与事件链，保持 READY-WAITING。

## 双 marker + 四层断言安全体系
- 双 marker：
  - `artifacts/sample_fetch_allow.marker`：样本点火开关，当前缺失。
  - `artifacts/sample_approve_expand.marker`：扩展放行开关，当前缺失。
- 四层断言：
  1. `sample_fetch_allow.marker` 必须存在。
  2. `REAL_WIND_CALL` 必须为 True。
  3. `MAX_DAYS_PER_ROUND = 10`。
  4. `MIN_INTERVAL_SEC = 12`。
- 当前状态：四层断言均未满足点火条件，保持静态待命。

## COM 锁修复过程
- 已确认 `EXCEL` 残留为 0。
- 已确认 `wmain` PID 824 前台可见。
- 已确认 `InitWAPI` PID 14188 运行中。
- DSHD 面板显示 COM 稳定性评分 `100/100`。
- 未产生新的 `WDF_ENV_READY.token`。

## 当前进程快照
- `wmain`：PID 824，标题 `Wind金融终端..Alice`
- `InitWAPI`：PID 14188
- `EXCEL`：0
- `WDF_ENV_READY.token`：不存在
- `sample_fetch_allow.marker`：不存在
- `sample_approve_expand.marker`：不存在

## 全部 7 项不变量快照
- gate = CLOSED/HOLD
- release_permit = NOT_ISSUED
- wind_api_calls = 0
- credential_alert = NONE
- circuit_breaker = READY
- hold_block_check = PASS
- ledger_append_only = TRUE

## DSHA-P58 / DSHD-P71 交叉核对
- DSHA-P58 证据：`docs/prototype_wss_shard_fetch_design.md` 中的 FINAL-LOCK 说明与点火授权路径一致。
- DSHD-P71 证据：`artifacts/dshd_wind_observation_dashboard.md` 与 `artifacts/dshd_com_jitter_dashboard.md` 均显示 `ComScore=100/100`、`P86Ready=READY-WAITING`。
- 交叉结论：P58 安全门、P71 观测门、P86 控制器门三者一致，均处于静态就绪状态。

## 人类点火 / 回滚操作手册
### 点火（仅人工）
1. 确认 COM 健康评分 >= 90。
2. 创建 `artifacts/sample_fetch_allow.marker`。
3. 手动将 `REAL_WIND_CALL` 改为 `True`。
4. 运行 P86 控制器。
5. 检查输出、告警与 Excel 残留。

### 回滚（仅人工）
1. 删除 `artifacts/sample_fetch_allow.marker`。
2. 将 `REAL_WIND_CALL` 改回 `False`。
3. 复核事件链与告警日志。
4. 确认 `wmain` / `InitWAPI` 保留，`EXCEL` 归零。

## 结论
- P87 只做静态自检、链路闭环、事件补全和最终就绪盖章。
- 未点火、未创建任何 marker、未生成 token、未修改安全锁常量。
- 当前最终状态：FINAL_READY，但仍必须 MANUAL_ONLY。
