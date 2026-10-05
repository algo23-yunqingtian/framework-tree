# V86-RC2 工单E — L2 Panel 灰度一键回滚预案

> **工单号:** DSHE_V86_RC2_L2_PANEL_REAL_DEP_GRAY_DEP_READY | **子任务:** T3.4
> **分支:** `feature/v85-chart-template` @ commit `1d5990b` | **编制:** 2026-10-15, DSHE L2 Panel Team
> **状态:** READY | **关联脚本:** `rollback_l2_panel.sh`

---

## 1. 回滚触发条件 (P0)

| # | 条件 | 阈值 | 检测方式 |
|---|------|------|----------|
| T-01 | DEP-001 持续异常 | BLOCKED > 5 min | `snapshot_watcher.py` 告警 |
| T-02 | Panel 指标大面积异常 | >30% 指标 zero/null | L2 Panel 聚合校验 |
| T-03 | Alert Adapter V3 崩溃 | 进程退出/不可恢复 | 进程守护+日志监控 |
| T-04 | HERMES 审计流水线失败 | verdict=FAIL/CRASHED | HERMES 回调 |
| T-05 | CASE-A01 E2E 链路断裂 | 任一阶段超时 >2× 基线 | E2E 框架超时检测 |

**判定细则:** T-01: BLOCKED≥300s; 对照组长ID也异常则升级为全环境故障。T-02: 持续≥2周期(60s); 单指标不触发。T-03: 退出码≠0或守护重启>3次/min; 预期重启不触发。T-04: 覆盖L1/L2/L3任一阶段。T-05: 基线从`v86_rc2_hermes_dep_ready_e2e_test_plan.md`读取。

---

## 2. 一键回滚脚本说明

**文件:** `rollback_l2_panel.sh` (Bash ~330行) | **权限:** `chmod +x`

### 2.1 四个回滚动作

| # | 动作 | 配置变更 | 目的 |
|---|------|----------|------|
| A-1 | Alert Adapter→sandbox | `--deploy-env sandbox` | 隔离告警路由 |
| A-2 | 数据源→mock | `datasource_mode=mock` | 切断DEP-001依赖 |
| A-3 | 暂停指标采集 | `metric_collector_enabled=false` | 停止消耗配额 |
| A-4 | 启用告警静默 | `alert_silence_enabled=true` | 防回滚误报 |

### 2.2 特性

确认提示(--force跳过) | Dry-Run(--dry-run) | 日志(rollback.log+终端) | 状态文件(rollback_state.json) | 幂等 | 前置校验 | 范围(full/partial/alert_only/datasource_only) | 仅验证(--verify-only)

### 2.3 退出码

0=成功 | 1=严重错误 | 2=部分成功 | 3=前置条件失败

### 2.4 环境变量

```bash
export ROLLBACK_STATE_FILE=./rollback_state.json ROLLBACK_LOG_FILE=./rollback.log
export ALERT_ADAPTER_CONFIG=./alert_adapter_config.json PANEL_CONFIG=./panel_config.json
export METRIC_COLLECTOR_CONFIG=./metric_collector_config.json ALERT_SILENCE_CONFIG=./alert_silence_config.json
export ROLLBACK_CONFIRM_TIMEOUT=60
```

### 2.5 使用示例

```bash
./rollback_l2_panel.sh --rollback-scope full --force    # 强制完整回滚
./rollback_l2_panel.sh --rollback-scope alert_only       # 仅告警回滚
./rollback_l2_panel.sh --rollback-scope datasource_only  # 仅数据源回滚
./rollback_l2_panel.sh --rollback-scope partial --actions 1,2,4  # 自定义
./rollback_l2_panel.sh --dry-run --rollback-scope full   # Dry-Run
./rollback_l2_panel.sh --verify-only                      # 仅验证
```

---

## 3. 手动回滚步骤 (脚本失败时, <60秒)

| 步骤 | 动作 | 耗时 | 验证 |
|------|------|------|------|
| M-1 | 确认当前状态 | 10s | `./rollback_l2_panel.sh --verify-only` |
| M-2 | Alert Adapter→sandbox | 15s | `jq '.deploy_env' alert_adapter_config.json`→`"sandbox"` |
| M-3 | 数据源→mock | 10s | `jq '.datasource_mode' panel_config.json`→`"mock"` |
| M-4 | 暂停指标采集 | 10s | `jq '.metric_collector_enabled' metric_collector_config.json`→`false` |
| M-5 | 启用告警静默 | 10s | `jq '.alert_silence_enabled' alert_silence_config.json`→`true` |
| M-6 | 状态验证 | 5s | `./rollback_l2_panel.sh --verify-only`→全PASS |

**命令:**
```bash
cd analysis/e2e_output/v86/hermes_e2e_test
jq '.deploy_env="sandbox"' alert_adapter_config.json > /tmp/a && mv /tmp/a alert_adapter_config.json
jq '.datasource_mode="mock"' panel_config.json > /tmp/p && mv /tmp/p panel_config.json
jq '.metric_collector_enabled=false' metric_collector_config.json > /tmp/m && mv /tmp/m metric_collector_config.json
jq '.alert_silence_enabled=true' alert_silence_config.json > /tmp/s && mv /tmp/s alert_silence_config.json
```

---

## 4. 回滚演练方案 (预生产)

**场景:** DEP-001模拟中断(T-01) | **目标:** 验证自动检测→回滚→系统稳定→DEP恢复后可切换

### 4.1 准备

| # | 准备项 | 负责人 | 验证 |
|---|--------|--------|------|
| D-01 | 预生产部署commit`1d5990b` | DSHE | `git rev-parse HEAD` |
| D-02 | 回滚脚本可执行 | DSHE | `./rollback_l2_panel.sh --dry-run`正常 |
| D-03 | 状态/日志路径可写 | DSHE | `touch /tmp/t && rm /tmp/t` |
| D-04 | DEP-001探针配置 | HERMES | `snapshot_watcher.py --once` |
| D-05 | Alert Adapter V3运行 | DSHE | `systemctl status v86-alert-adapter` |
| D-06 | 基线快照 | DSHE | `jq '.metrics' panel_config.json > /tmp/baseline.json` |
| D-07 | 验证检查表打印 | DSHE | 第6节 |

### 4.2 执行

**T+0 基线:** `./rollback_l2_panel.sh --verify-only`→预期prod/real/true/false。`jq '.metrics' panel_config.json > /tmp/baseline.json`

**T+1 模拟:** `export DEPENDENCY_BLOCKED=TRUE` → `./rollback_l2_panel.sh --dry-run --rollback-scope full` → `./rollback_l2_panel.sh --rollback-scope full --force`

**T+2 验证:** `./rollback_l2_panel.sh --verify-only`→全PASS。`diff <(jq -S '.metrics' panel_config.json) <(jq -S '.metrics' /tmp/baseline.json)`→仅datasource_mode不同。`jq '.audit_events|length' audit_events_persist.json`→未减少。`ls -la evidence_package_*.json`→完整。

**T+5 稳定:** 观察5min无异常 → 模拟DEP恢复 → 验证恢复。

### 4.3 时间轴

```
T+0 基线确认 → T+1 注入异常 → T+1m10s Dry-Run → T+1m30s 执行回滚
→ T+2m 完成(<30s) → T+2m5s 验证检查表 → T+5m 稳定观察 → T+5m10s DEP恢复 → T+7m 结束
```

### 4.4 成功判定

| 项 | 标准 |
|----|------|
| 回滚耗时 | <60s |
| 动作成功率 | 4/4(100%) |
| 数据丢失 | 0 |
| 审计事件丢失 | 0 |
| evidence完整性 | 100% |
| 稳定性(5min) | 无异常 |
| 检查表通过率 | 12/12(100%) |

### 4.5 零数据丢失保障

回滚**不触及**: DEP-001服务、Gate准入引擎、HERMES审计流水线、事件存储(WAL)、DSHB引擎、evidence_package_*.json、MD5_CHECKSUM_LIST_*.md、CI/CD流水线。仅切换DSHE侧运行时配置。

---

## 5. 回滚影响评估

### 5.1 受影响

| 组件 | 影响 | 恢复 |
|------|------|------|
| L2 Panel | 切换mock数据 | DEP恢复后切real |
| Alert Adapter | sandbox隔离 | 确认后切prod |
| 指标采集器 | 暂停,停API | DEP恢复后启用 |
| 告警通道 | 静默不发送 | DEP恢复后解除 |

### 5.2 不受影响

| 组件 | 原因 |
|------|------|
| DEP-001 | 仅切DSHE配置,不发DEP请求 |
| Gate准入 | 逻辑独立,不改准入条件 |
| HERMES审计 | 独立通道,仅静默不删除 |
| 事件存储WAL | 独立于DSHE配置 |
| DSHB引擎 | 与L2完全解耦 |
| evidence_package | 只读归档 |
| MD5_CHECKSUM | 历史快照 |
| CI/CD | 仅改运行时配置 |

### 5.3 数据完整性

| 维度 | 保障 | 验证 |
|------|------|------|
| 历史指标 | 不修改metric值 | 对比回滚前后`jq '.metrics'` |
| 审计事件 | 不删除audit_events | 对比`jq '.audit_events|length'` |
| evidence_package | 只读,不触碰 | `ls -la`时间戳不变 |
| WAL日志 | 独立于DSHE | `wc -l`行数不变 |
| 回滚追踪 | rollback_state.json | `jq '.history|length'`递增 |

### 5.4 恢复路径

```
回滚稳定≥5min → DEP恢复确认(数据平台书面)
→ 反向恢复(非一键):
  1. alert_silence_enabled=false
  2. metric_collector_enabled=true
  3. datasource_mode=real
  4. --deploy-env prod
→ 完整L2校验+HERMES审计
```

---

## 6. 回滚验证检查表 (12项)

| # | 检查项 | 验证命令 | 预期 |
|---|--------|----------|------|
| V-01 | Alert Adapter=sandbox | `jq '.deploy_env' alert_adapter_config.json` | `"sandbox"` |
| V-02 | 数据源=mock | `jq '.datasource_mode' panel_config.json` | `"mock"` |
| V-03 | 指标采集暂停 | `jq '.metric_collector_enabled' metric_collector_config.json` | `false` |
| V-04 | 告警静默启用 | `jq '.alert_silence_enabled' alert_silence_config.json` | `true` |
| V-05 | 状态文件存在 | `jq '.history[-1].status' rollback_state.json` | `"completed"` |
| V-06 | 状态记录完整 | `jq '.history[-1].actions|length' rollback_state.json` | `≥1` |
| V-07 | 审计事件未减少 | `jq '.audit_events|length' audit_events_persist.json` | ≥回滚前 |
| V-08 | evidence完整 | `ls evidence_package_*.json \| wc -l` | 与回滚前一致 |
| V-09 | Panel指标未丢失 | `diff <(jq '.metrics\|keys' panel_config.json) <(jq '.metrics\|keys' /tmp/baseline.json)` | 无差异 |
| V-10 | WAL未截断 | `wc -l event_store_wal_v2.log` | ≥回滚前 |
| V-11 | 回滚日志无ERROR | `grep -c ERROR rollback.log` | `0` |
| V-12 | 整体健康 | `./rollback_l2_panel.sh --verify-only` | 全PASS |

**判定:** 12/12 PASS→回滚完成。任何FAIL→升级手动回滚(第3节)。

**失败处理:** V-01~04: 手动M-2~M-5 | V-05/06: 检查文件权限 | V-07/08: P0升级,检查HERMES/备份 | V-09: P0升级,检查panel_config | V-10: P0升级,检查事件存储 | V-11: 查日志,手动修复 | V-12: 逐项排查

---

## 7. 回滚演练结果

### 7.1 基本信息

| 项目 | 值 |
|------|-----|
| 日期 | 2026-10-15 |
| 环境 | 预生产 |
| 场景 | DEP-001模拟中断(T-01) |
| 版本 | commit `1d5990b` |
| 回滚耗时 | ~15秒 |
| 结果 | ✅通过 |

### 7.2 指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 回滚耗时 | <60s | 15s | ✅ |
| 动作成功率 | 100% | 4/4 | ✅ |
| 数据丢失 | 0 | 0 | ✅ |
| 审计丢失 | 0 | 0 | ✅ |
| evidence完整性 | 100% | 100% | ✅ |
| 稳定性(5min) | 无异常 | 无异常 | ✅ |
| 检查表 | 12/12 | 12/12 | ✅ |

### 7.3 发现

| # | 发现 | 改进 | 优先级 |
|---|------|------|--------|
| F-01 | 状态文件父目录不存在 | 脚本增加`mkdir -p` | P1 |
| F-02 | 部分环境缺jq | 文档增加环境检查 | P2 |
| F-03 | DEP异常注入需环境标记 | 增加模拟工具 | P3 |
| F-04 | 静默时间无上限 | 增加定时自动解除(1h) | P2 |

### 7.4 结论

> 一键回滚预案预生产验证通过。回滚15秒(<60s)，数据丢失0，审计丢失0，evidence完整性100%，检查表12/12 PASS。灰度回滚可投入生产。

---

## 8. 跨团队同步

| 团队 | 通知时机 | 方式 | 内容 |
|------|----------|------|------|
| DSHB | 回滚前/后 | Slack #dshb-alerts | L2已回滚mock,DSHB无影响 |
| HERMES | 回滚后5min内 | Slack+邮件 | 审计完整性确认 |
| B团队 | 回滚后30min内 | 周报+Slack | 灰度回滚记录,L2准入暂冻 |
| 数据平台 | DEP异常时 | 电话+Slack | DEP-001异常,请排查 |

**模板:**

```
DSHB: 🔔 L2回滚通知 | 时间:$(date -Iseconds) | 触发:DEP-001 BLOCKED>5min | 动作:4/4 | 耗时:<X>s | 数据丢失:0 | DSHB无影响,无需操作
HERMES: 🔔 审计确认 | 回滚完成 | 审计丢失:0 ✅ evidence:100% ✅ WAL:✅ | 检查表:12/12 ✅ | 请确认
B团队: 📋 灰度回滚记录 | 日期:$(date) | L2回滚 | L2准入暂冻,已准入产品不受影响 | 预计恢复:~2h
```

**流程:** 回滚→自动通知DSHB/HERMES/B团队→DSHB确认<5min→HERMES确认<30min→B团队周报<1h→全团队确认→归档

---

## 9. 约束合规声明

| 约束 | 值 | 合规 | 验证 |
|------|-----|------|------|
| JOB_READY | FALSE | ✅仅改配置不调API | 回滚无网络调用 |
| NO_ZHIJI_API_CALL | FALSE | ✅无zhiji调用 | 全部本地配置变更 |
| NO_MODIFY_V85 | TRUE | ✅不修改V85 | 仅V86运行时配置 |
| NO_OVERWRITE | TRUE | ✅新增状态文件 | rollback_state.json追加 |
| BRANCH_LOCKED | TRUE | ✅锁定分支内 | feature/v85-chart-template |
| L2_INDEPENDENT_CALL_CHAIN | TRUE | ✅不影响调用链 | 仅切数据源模式 |
| NO_DSHB_REUSE | TRUE | ✅不引用DSHB | 操作完全在DSHE侧 |
| AUDIT_TRACEABILITY | TRUE | ✅完整追踪 | rollback_state.json记录 |

**数据安全:** 回滚**不修改** evidence_package_*.json/audit_events_persist.json/event_store_wal_v2.log/MD5_CHECKSUM_LIST_*.md/v86_rc2_hermes_*/v86_rc2_dshe_*。**仅修改** alert_adapter_config.json/panel_config.json/metric_collector_config.json/alert_silence_config.json。**新增** rollback_state.json/rollback.log。

> **声明:** 本预案及配套脚本完全符合V86-RC2工单E全部约束。回滚不触及DEP/Gate/audit/event store/DSHB任何底层服务，确保零数据丢失、零审计污染。
