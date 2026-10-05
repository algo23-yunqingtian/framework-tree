# V86-RC2 灰度多阶段面板降级策略规范

> **工单**: DSHE_V86_RC2_L2_PANEL_REAL_DEP_GRAY_DEP_READY / T3.3
> **分支**: `feature/v85-chart-template` @ `1d5990b`
> **编制方**: DSHE | **生效日期**: 2026-10-15 | **文档状态**: FINAL
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 1. 概述

**目的**: 定义 L2 面板层从影子观测 → 灰度分阶 → 全量生产的降级策略，确保 197 项指标在真实 DEP-001 环境下的渐进可用。

**范围**: 197 项指标 (SP-001~SP-197) | 6 主面板 SP1-SP6 / 72 子面板 | 15+6 告警 | DEP-001 | Alert Adapter V3

**三阶段灰度总览**:

```
G0 影子 (24-48h) ──→ G1(1%) → G2(10%) → G3(30%) → G4(60%) ──→ G5 全量(100%)
  观测模式         各阶段 ≥4h 渐进放大                              生产通道
  Mock回滚        可降阶回滚                                        持续监控
```

**阶段定义**:

| 阶段 | 流量 | 指标采样 | 告警级别 | 推送 | 数据源 | 窗口 | 回滚目标 |
|------|------|---------|---------|------|--------|------|---------|
| G0 | 100%旁路 | 100%(197) | P0-P2 | ❌观察 | Real | 24-48h | Mock |
| G1 | 1% | 50%低频 | P0 | ✅ | Real | ≥4h | G0 |
| G2 | 10% | 70% | P0+P1 | ✅ | Real | ≥4h | G1 |
| G3 | 30% | 85% | P0+P1+P2 | ✅ | Real | ≥4h | G2 |
| G4 | 60% | 100% | 全部 | ✅ | Real | ≥4h | G3 |
| G5 | 100% | 100%(197) | 全部 | ✅生产 | Real | 持续 | G4 |

---

## 2. G0 影子观测阶段

**定位**: 最终验证窗口，使用真实 DEP-001 但不影响生产流量。全部 197 指标旁路采集，告警仅观察不推送。

**配置**: `data_source=real` | `metrics=197(100%)` | `panels=SP1-SP6/72子面板` | `badge=🟡SHADOW_MODE` | `alert_env=sandbox` | `push=FALSE` | `fallback=historical_snapshot` | `grace=300s` | `rollback=mock(≤5min)`

**告警规则**: 12 条告警全部进入观察模式（触发不推送），持久化至 `.logs/alert_adapter_v3_sandbox.log` + `.checkpoint/alert_adapter_v3_sandbox.jsonl`

**退出条件**: 24h 内 P0=0 且 P1<5 且 P2<20 → 自动晋级 G1；或 DSHE 人工审批；或 DEP-001 恢复确认 + L2 CRITICAL=0

**回滚**: DEP不可达>5min 或 P0>3 → 自动切回 Mock；手动回滚随时可用；回滚时间≤5min

---

## 3. G1-G4 灰度分阶阶段

**策略**: 指数递增流量 + 渐进指标采样 + 分级告警启用。每阶段观察 ≥4h。

**各阶段配置**:

| 参数 | G1 | G2 | G3 | G4 |
|------|----|----|----|----|
| 流量比例 | 1% | 10% | 30% | 60% |
| P0采样 | 100% | 100% | 100% | 100% |
| P1采样 | — | 70% | 85% | 100% |
| P2采样 | 50% | 70% | 85% | 100% |
| 告警级别 | P0 | P0+P1 | P0-P2 | 全部 |
| 面板禁用 | SP4-12,SP5-08,SP6-06 | SP4-12 | 无 | 无 |
| 晋级条件 | 0P0+0回滚 | P0<2+P1<5 | P0<3+P1<8+P2<20 | P0<3+P1<8+P2<20+完整性≥195/197 |
| 回滚条件 | P0触发 | P0≥2或P1≥5 | 超阈值 | 超阈值 |
| 检查频率 | 15min | 5min | 5min | 5min |

**指标优先级分级**:

| 优先级 | 指标范围 | 数量 | 占比 | 策略 |
|--------|---------|------|------|------|
| P0 | SP-001~048+SP-181~183 | 51 | 25.9% | 强制100%不可降级 |
| P1 | SP-049~130 | 82 | 41.6% | 可配置(50-100%) |
| P2 | SP-131~160+SP-161~180+SP-184~197 | 64 | 32.5% | 可配置(0-100%) |

**选择性面板禁用**: G1 禁用 SP4-sub-12(重复检测), SP5-sub-08(告警未处理), SP6-sub-06(趋势异常)；G2 仅 SP4-sub-12；G3+ 全部启用

**晋级状态机**: G0→G1→G2→G3→G4→G5，任一级 FAIL 降阶至上一级；强制回滚: 任意阶段→Mock(手动)

---

## 4. G5 全量生产阶段

**定位**: 最终生产阶段。197 指标 100% 采集，全部告警推送至生产通道，影子模式废弃但回滚开关保留。

**配置**: `traffic=100%` | `metrics=197/100%` | `badge=🟢FULLY_AVAILABLE` | `alert_env=prod` | `push=TRUE` | `channels=6通道` | `monitor_interval=1min` | `rollback_switch=TRUE` | `rollback_target=G4`

**影子模式废弃**: Mock数据源→LEGACY保留 | shadow标签清除 | 徽章→🟢 | sandbox→prod | 回滚开关保留 | SP-124影子/生产偏差指标保留

**持续监控**: 完整性/延迟/面板/API/缓存/告警/DEP 共 7 维度，1min~30s 间隔，P0→飞书+邮件+电话

---

## 5. 降级策略

### 5.1 流量降级 (Token Bucket)

| 级别 | 阈值 | 动作 | 触发 | 恢复 |
|------|------|------|------|------|
| 软限流 | 500 rps | 队列缓冲 | >500s | <500s 60s |
| 硬限流 | 300 rps | 拒绝(429) | >300s 30s | <300s 120s |
| 熔断 | 100 rps | 仅P0通过 | >100s 60s | <100s 300s+人工 |

优先级: P0永不限流 > P1软限以上 > P2硬限以上 > 数据查询全限

### 5.2 指标采样降级

P0=100%强制(不可降级) | P1=可配置(最低50%) | P2=可配置(最低0%)。系统CPU>80%时P1自动降为50%，CPU>70%时P2自动降为50%。

### 5.3 告警静默

| 类型 | 触发 | 范围 | 时长 | 恢复 |
|------|------|------|------|------|
| 维护窗口 | 自动 | 全部 | 窗口内 | 窗口结束 |
| 晋级过渡 | 自动 | P1/P2 | 15min | 晋级确认 |
| 数据源切换 | 自动 | 全部 | 5min | 切换完成 |
| DEP降级 | 自动 | P2 | 降级期 | DEP恢复 |
| 告警风暴 | 自动 | P2 | 10min | 速率回落 |
| 人工 | DSHE+HERMES双审批 | 精确规则 | ≤4h | 超时重新审批 |

### 5.4 阈值动态调整

7日滑动窗口基线，漂移>20%触发调整(上限±50%)，>20%调整需HERMES审核，连续3天调整需人工审核。

### 5.5 降级适用矩阵

| 策略 | G0 | G1 | G2 | G3 | G4 | G5 |
|------|----|----|----|----|----|----|
| 流量-软限 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 流量-硬限 | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| 流量-熔断 | — | — | ✅ | ✅ | ✅ | ✅ |
| 采样降级 | — | ✅ | ✅ | ✅ | ✅ | — |
| 自动静默 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 阈值调整 | — | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 6. DEP 故障自动回退

**架构**: DEP-001不可达 → 5min宽限期 → 切换历史快照(🟡DEPENDENCY_BLOCKED) → 3次连续成功轮询 → 自动回退(🟢FULLY_AVAILABLE)

**时间线**:

| 时间 | 动作 | 状态 |
|------|------|------|
| T+0s | DEP不可达检测 | ACTIVE→BLOCKED |
| T+300s | 宽限超时，切换快照 | BLOCKED→FALLBACK |
| 3次成功(30s间隔) | 恢复验证 | BLOCKED→RECOVERY→RECOVERED |
| RECOVERED | 切换实时数据 | RECOVERED→ACTIVE |

**参数**: grace=300s | poll_interval=30s | poll_timeout=5s | recovery_polls=3 | snapshot_retention=30d | snapshot_max_age=24h

**DS-06 抖动规则**:

> "RECOVERED后再次发生BLOCKED≥2次判定为DEP抖动"

```
BLOCKED(不计) → RECOVERY(不计) → RECOVERED(窗口打开) → BLOCKED count≥2 → ⚠️FLAPPING
RECOVERY→BLOCKED(未经过RECOVERED) = 恢复验证失败(不计为抖动)
```

抖动处置: CRITICAL告警 + 冻结晋级 + HERMES人工介入 + 暂停自动回退

**DEP状态转换**:

| 当前 | 事件 | 目标 | 计数 | 告警 |
|------|------|------|------|------|
| ACTIVE | DEP_FAILURE | BLOCKED | — | P1 |
| BLOCKED | GRACE_TIMEOUT | FALLBACK | — | P0 |
| FALLBACK | POLL_SUCCESS | RECOVERY | — | — |
| RECOVERY | VERIFY_PASS×3 | RECOVERED | 0 | — |
| RECOVERED | DEP_FAILURE×2 | FLAPPING | 2 | CRITICAL |

---

## 7. 切换控制逻辑

**配置驱动**: JSON配置文件，支持热重载(5s间隔检测，无需重启)。语法校验失败→回退至上一有效配置。

**配置结构**: phase | data_source | metrics(priority_sampling/panel_selective_disable) | alerts(silence/channels) | rate_limiting(token_bucket) | dep_fallback(grace/polls/flap_rule) | threshold_adjustment | audit(trail/event_types)

**审计轨迹**: 每次事件记录 event_id/timestamp/type/phase_change/trigger/operator/dep_registry_id/data_source_change/metrics_change/alert_change/audit_fingerprint/rollback_available

**环境守卫**: Alert Adapter V3 `EnvironmentGuard` 防止 sandbox/prod 交叉写入。规则: PROD_AUTH_MISSING/PROD_CROSS_WRITE/SANDBOX_CROSS_WRITE 全部拒绝

**阶段配置对比**:

| 字段 | G0 | G1 | G2 | G3 | G4 | G5 |
|------|----|----|----|----|----|----|
| deploy_env | sandbox | sandbox | sandbox | sandbox | sandbox | prod |
| push | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| P0/P1/P2采样 | 1.0/-/- | 1.0/-/0.5 | 1.0/0.7/0.7 | 1.0/0.85/0.85 | 1.0/1.0/1.0 | 1.0/1.0/1.0 |
| badge | SHADOW | GRAY-G1 | GRAY-G2 | GRAY-G3 | GRAY-G4 | FULLY |
| rollback_target | mock | G0 | G1 | G2 | G3 | G4 |

---

## 8. 跨团队同步

**同步节奏**: G0进入(一次性通知) → G0运行(每日报告) → 每次晋级(配置快照+决策) → G5(全量通知+影子废弃) → 任何回滚(即时P0告警) → DEP故障(状态通知) → DS-06抖动(CRITICAL+电话)

**责任矩阵**: DSHE执行切换(≤5min响应) | DSHB确认数据源(1日) | HERMES审计审批(1日) | B-Team业务通知(4h)

---

## 9. 约束合规

| 约束 | 值 | 状态 |
|------|-----|------|
| JOB_READY | FALSE | ✅ |
| NO_MODIFY_V85 | TRUE | ✅ |
| NO_OVERWRITE | TRUE | ✅ |
| BRANCH_LOCKED | TRUE | ✅ |
| L2_INDEPENDENT_CALL_CHAIN | TRUE | ✅ |
| AUDIT_TRACEABILITY | TRUE | ✅ |
| ENV_GUARD_ENFORCED | TRUE | ✅ |
| P0_FORCED_100 | TRUE | ✅ |
| DS_06_ENFORCED | TRUE | ✅ |
| DEP_GRACE_PERIOD | 300s | ✅ |
| ROLLBACK_WINDOW | 15min | ✅ |
| HOT_RELOAD | TRUE | ✅ |
| ALERT_ADAPTER_V3 | TRUE | ✅ |

---

## 10. 状态标记

```
DSHE_V86_RC2_L2_PANEL_GRAY_DEGRADE_READY=TRUE
T3.3_GRAY_DEGRADE_SPEC_COMPLETE=TRUE
GRAY_PHASES=6(G0+G1+G2+G3+G4+G5)
DEGRADATION_STRATEGIES=4(Traffic/Metric/Alert/Threshold)
DEP_FAULT_FALLBACK_ENABLED=TRUE
DS_06_RULE_ENFORCED=TRUE
HOT_RELOAD_ENABLED=TRUE
AUDIT_TRAIL_ENABLED=TRUE
ENV_GUARD_ENABLED=TRUE
ALERT_ADAPTER_V3_DEPLOY_ENV_SANDBOX=TRUE
CROSS_TEAM_SYNC_CONFIGURED=TRUE
```

---

*Generated: 2026-10-15 | Task: DSHE_V86_RC2_L2_PANEL_REAL_DEP_GRAY_DEP_READY / T3.3*
*Branch: feature/v85-chart-template @ 1d5990b (L2_SHARD_BUGFIX_PROD_ADAPT_DONE)*
*Status: T3.3 COMPLETE — 6阶段降级/回滚/晋级策略全部定义*
