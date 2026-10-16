# DSHD-P67 Wind 测试过程审计备注

**工单**: DSHD-P67 工单-D 继续执行 | **审计日期**: 2026-10-16  
**监控范围**: POLL-221+ → POLL-284+ (23:05) | **分支**: `feature/v88-g1`  
**治理不变量**: 7/7 全绿 (gate=CLOSED/HOLD, wind_api_calls=0)  
**凭证告警**: CRITICAL_CREDENTIAL_DETECTED (POLL-283, 22:50:52)

---

## 一、CRITICAL 告警：明文凭证泄露 (DEFECT-012)

| 项 | 详情 |
|---|---|
| **时间** | 2026-10-16 22:48:57 |
| **触发轮次** | POLL-283 (22:50:52), POLL-284 (22:51:52) |
| **告警类型** | CRITICAL_CREDENTIAL_DETECTED |
| **涉及文件** | `wind_excel_events.jsonl` 第52行, `tracking_monitor_audit.jsonl` 第54行 |
| **凭证模式** | 明文账号/密码组合 (已脱敏) |
| **根因** | DSHA-P49 测试脚本写入日志时未执行凭证脱敏 |
| **wind_fix_log.md 自报** | "明文密码写入日志: 0次" — 对 V3 脚本正确，但未涵盖 DSHA-P49 条目 |
| **处置** | 已自动升级至 DSHC。DEFECT-012 登记入册。DEFERRED_TO_LAUNCH 策略适用。 |

**注意**: DSHC-P68 已将 DEFECT-005 更新为 DEFERRED_TO_LAUNCH，但未涵盖 DEFECT-012 新实例。DSHD 未修改任何文件（仅观察/记录/升级）。

---

## 二、DSHA-P54 V3 Wind/Excel 测试审计 (wind_fix_log.md)

### 2.1 测试时间线

| 时间 | 事件 | 结果 |
|---|---|---|
| 22:48:53 | Python 3.12.10 启动, WindPy 模块导入 | ✅ 成功 |
| 22:48:56 | Wind 终端进程检查 | ✅ 1进程 (WindUpdate.RUN), WBox NOT_CONNECTED |
| 22:48:57 | w.start() 尝试 | ❌ ErrorCode=-2 |
| 22:48:57 | TEST_ABORTED | ✅ 按硬约束停止 |
| 22:48:57 | WINDPY_STOP | ⏭️ 跳过 (未连接) |

### 2.2 环境基线 (wind_fix_log.md)

| 项 | 值 | 状态 |
|---|---|---|
| Python | 3.12.10 (64-bit AMD64) | ✅ |
| WindPy.dll (D:\x64) | v1.10.1.4, 2,411,328B | ✅ 存在 |
| WindPy.dll (D:\bin) | v1.10.1.4, 1,753,920B | ✅ 存在 |
| WindPy.py | ~2182行, cp936, 88,086B | ✅ 存在 |
| WindPy.pth | 指向 D:\x64 | ✅ 正确 |
| Wind 终端 (wmain.exe) | v26.6.1.19, PID 19612 | ✅ 运行中 |
| WBox.exe | PID 2496 | ✅ 运行中 |
| windlocal.exe | v1.0.28.53436 | ⚠️ 启动后立即退出 (exit=0) |
| .wind 目录 | C:\Users\YAQH\.wind\WMain\ | ⚠️ **目录为空** (0 文件) |
| InitWAPI.exe | v1.11.30.1124 | ⚠️ **需管理员权限** (本环境无) |

### 2.3 根因链 (确认)

```
终端未登录 → .wind 配置为空 → InitWAPI.exe 未运行(需管理员)
→ 无本地 API 端点(0 监听端口) → windlocal.exe 立即退出
→ WindPy c_start() ErrorCode=-2 → 所有数据路径阻断
```

### 2.4 关键发现

1. **终端进程运行但无本地 API 端点** — 终端有外网连接 (Wind 服务器)，但本地 0 监听端口
2. **`.wind\WMain\users` 完全为空** — 无配置文件、无许可证、无用户数据
3. **ErrorCode=-2** — DLL 层面失败，未到认证阶段
4. **InitWAPI.exe 需管理员权限** — 沙箱环境无法执行
5. **WDF COM 未注册** — regsvr32 执行但 COM 组件未出现在注册表
6. **Wind Excel add-in 未加载** — Excel 已打开但 Wind 插件未加载

### 2.5 治理约束遵守

| 约束 | 状态 |
|---|---|
| wind_api_calls=0 | ✅ DSHD-P67 未执行任何 Wind 调用 |
| gate=CLOSED/HOLD | ✅ |
| backtest_started=false | ✅ |
| release_permit=NOT_ISSUED | ✅ |
| HOLD 因子 4/4 拦截 | ✅ |
| 审计日志仅追加 | ✅ |

---

## 三、有色金属小样因子采集状态

| 项 | 状态 |
|---|---|
| CSV 文件扫描 | 0 个 CSV 文件发现 |
| 数据收集 | 尚未开始 (依赖 DEFECT-004 修复) |
| 产出完整性 | 不适用 (无数据产出) |
| 阻断原因 | Wind 客户端不可用 → 无数据源 |

---

## 四、SHA256_CHECKSUMS.txt 独立复核 (DSHC-P68 修复后)

| Entry | 文件 | 期望 SHA8 | 实际 SHA8 | 状态 |
|---|---|---|---|---|
| #1 | FL01_FL02_manual_review.md | `1AF9BB37` | `1AF9BB37` | ✅ MATCH |
| #10 | P49_pre_gray_check.md | `E8E2A1E2` | `E8E2A1E2` | ✅ MATCH (PRESENT) |
| #20 | tracking_monitor_audit.jsonl | `06830FB1` | `FD14783C` | ❌ STALE (账本再次增长) |
| #22 | DSHD_DEFECT_OBSERVATION_REGISTRY.md | `2FE30A5C` | `2FE30A5C` | ✅ MATCH |

**Entry #20 说明**: DSHC-P68 于 22:50 刷新的 SHA256 (`06830FB1`) 对应账本 53 行版本。账本在 22:48:57 增长了 4 行 (53→57)，导致 SHA8 变为 `FD14783C`。**DSHD 未修改该文件** (DSHC 权限)。

---

## 五、缺陷登记簿更新摘要

| 缺陷 | 更新前 | 更新后 | 说明 |
|---|---|---|---|
| DEFECT-001 | OPEN | OPEN | 无变化 (P61 扫描器，等待 DSHC) |
| DEFECT-002 | OPEN | OPEN | DSHC-P68 刷新了 SHA256_CHECKSUMS，但 Entry #20 再次过期 |
| DEFECT-003 | RESOLVED | ✅ **确认 RESOLVED** | P49_pre_gray_check.md 存在 (13,892B, commit 28f0c9d) |
| DEFECT-004 | OPEN | **IN_PROGRESS** | DSHA-P54 V3 测试完成，两条路径均失败 |
| DEFECT-005 | OPEN | ✅ **确认 DEFERRED_TO_LAUNCH** | DSHC-P68 已更新 |
| DEFECT-012 | — | **NEW (OPEN)** | 明文凭证泄露新实例 (22:48:57) |

**当前缺陷统计**: 12 个总缺陷 (5 OPEN, 1 IN_PROGRESS, 4 RESOLVED, 2 INFORMATIONAL)

---

## 六、P61/SHA 漂移/git 历史 — 观察记录 (只登记不修复)

| 项 | 状态 | 观察记录 |
|---|---|---|
| P61 扫描器 | 缺失 | 无变化。DSHC 需决定恢复路径 (重建/迁移/取消) |
| SHA 漂移 | 持续 | DSHC-P68 于 22:50 刷新 (22 条目)，但 Entry #20 再次过期 (账本增长) |
| git 历史清理 | 待执行 | DEFECT-005/012 凭证仍在 git 历史中。DEFERRED_TO_LAUNCH 策略适用 |

---

## 七、DSHC 待办汇总

1. **修复 Wind 客户端** — DEFECT-004 (IN_PROGRESS)。需要管理员权限运行 `D:\bin\InitWAPI.exe` 或以管理员身份重新配置终端
2. **清理凭证** — DEFECT-012 (新)。`tracking_monitor_audit.jsonl` 第54行 + `wind_excel_events.jsonl` 第26行含明文凭证
3. **更新 SHA256_CHECKSUMS.txt** — Entry #20 过期 (账本 SHA8 从 `06830FB1` 变为 `FD14783C`)
4. **P61 扫描器决策** — DEFECT-001，恢复路径待定
5. **上线前轮换凭证** — DEFECT-005/012，DEFERRED_TO_LAUNCH 策略

---

## 八、监控状态

| 项 | 值 |
|---|---|
| 监控版本 | pwsh-7 v3 |
| 轮询间隔 | 60 秒 |
| 当前轮次 | POLL-284+ (22:51:52) |
| 日志行数 | 654 行 (336,785B) |
| 凭证告警 | CRITICAL_CREDENTIAL_DETECTED (POLL-283/284) |
| wind_api_calls | 0 |
| 账本行数 | 57 行 (47,221B, SHA8=`FD14783C`) |
| Wind 事件行数 | 56 行 |

---

*本备注由 DSHD-P67 监控代理生成。审计侧独立观察记录。*
*治理红线: wind_api_calls=0 ✅ | gate=CLOSED/HOLD ✅ | 审计仅追加 ✅*
*不包含任何明文凭证 (所有凭证已脱敏为 [REDACTED-CREDENTIAL])。*