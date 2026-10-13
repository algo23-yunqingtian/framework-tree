# V87-RC1 L2大盘 Phase03 — 灰度阶段观察手册

> **文档编号**: V87-RC1-E-L2-DASH-PHASE03-GRAY-OBSERVATION-HANDBOOK
> **版本**: v1.0.0
> **编制方**: DSHE (L2 展示层)
> **协作方**: DSHB (L1 业务层) + HERMES (L3 智能层)
> **分支**: `feature/v87-rc1-g1`
> **工单**: `DSHE_V87_RC1_L2_PHASE03_STAGEA_GRAY_PHASE_OBSERVATION`
> **编制日期**: 2027-03-15
> **密级**: 内部 — 项目组
> **上一阶段交付**: `v87_rc1_e_l2_dashboard_phase02_panel_alert_acceptance_report.md` (Commit `0d9a9d7`)
> **下游消费者**: Phase03 StageB 全量发布 / Phase04 稳定性验证
> **约束**: `BRANCH_LOCKED=TRUE` | `NO_MODIFY_V85=TRUE` | `NO_OVERWRITE=TRUE` | `NO_ZHIJI_API_CALL=TRUE` | `IE_AL_001_3LEVEL_PRESERVED=TRUE`

---

## 目录

1. [手册概述](#1-手册概述)
2. [灰度阶段时间线](#2-灰度阶段时间线)
3. [关键观察指标](#3-关键观察指标)
4. [告警响应 SOP](#4-告警响应-sop)
5. [监控面板](#5-监控面板)
6. [回滚程序](#6-回滚程序)
7. [升级矩阵](#7-升级矩阵)
8. [通信协议](#8-通信协议)
9. [观察检查清单](#9-观察检查清单)
10. [DSHB/HERMES 同步点](#10-dshbhermes-同步点)
11. [速查卡](#11-速查卡)
12. [状态标记](#12-状态标记)

---

## 1. 手册概述

### 1.1 手册目的

本手册是 V87-RC1 L2 大盘 Phase03 StageA **灰度发布观察** 的唯一权威操作指南。Phase02 已完成 8 个新面板开发、12 条告警规则迭代、5 个 HERMES 新审计字段集成，并通过全量验收（8/8 面板 PASS，12/12 告警规则 PASS，5/5 字段 PASS，误报 0，漏报 0）。Phase03 StageA 的任务是将这些成果从实验室环境安全地灰度到生产环境，通过系统化的观察、监控、决策机制确保：

1. **零中断上线**: 灰度期间 V86 基线业务不受任何影响
2. **数据完整性**: 5 个 HERMES 新字段灰度数据与 HERMES 源端 100% 一致
3. **性能达标**: 灰度流量下所有 P99 指标维持在 V200-1.0 预算内
4. **告警健康**: 12 条告警规则在灰度环境下维持零误报零漏报
5. **可回滚性**: 任意时刻可在 15 分钟内完成全量回滚

### 1.2 适用范围

| 范围 | 包含 | 不包含 |
|------|------|--------|
| **流量范围** | 50% 灰度流量 (从 V87 预估 560 QPS 的 50%) | V86 100% 基线流量 |
| **面板范围** | 全部 8 个 V87 新增面板 | 25 个 V86 继承面板（由 Phase01 监控基线模板覆盖） |
| **告警范围** | 全部 12 条 V87 告警规则 | — |
| **数据源范围** | HERMES L3 + DSHB Registry + ClickHouse + OTel Tracing | — |
| **环境范围** | 灰度集群 (`v87-gray-*` namespace) + V86 基线集群 | — |
| **时间范围** | T-2h 至 T+7d (含灰度前准备、灰度执行、灰度评估、灰度后观察) | — |

### 1.3 目标受众

| 角色 | 职责 | 使用章节 |
|------|------|----------|
| **SRE On-call** | 24×7 灰度值班，执行观察、告警响应、回滚决策 | §2, §3, §4, §6, §11 |
| **DSHE Ops** | L2 展示层运维，面板健康与性能调优 | §3, §5, §9 |
| **DSHB Ops** | L1 业务层运维，流量路由与 API 性能 | §2, §10 |
| **HERMES Ops** | L3 智能层运维，审计对账与数据完整性 | §3, §5, §10 |
| **Phase03 Lead** | 灰度决策者（GO/COND-GO/RED） | §2.4, §6, §9.4 |
| **VP Engineering** | 重大事件升级接收方 | §7 |

### 1.4 使用指南

1. **灰度前**：阅读 §1、§2、§9.1，完成灰度前检查清单（24 项）
2. **灰度启动时**：阅读 §2.2、§3、§4、§9.2，建立观察节奏
3. **灰度稳定期**：按 §9.3 每小时检查清单循环，每 30 分钟提交状态报告
4. **灰度评估时**：阅读 §2.4、§9.4，做出 GO/COND-GO/RED 决策
5. **异常时**：按 §4 告警响应 SOP 与 §6 回滚程序执行
6. **持续参考**：§11 速查卡可随时打开

### 1.5 前置文档

| 文档 | 用途 |
|------|------|
| `v87_rc1_e_l2_dashboard_phase01_requirement_spec_lock.md` | 需求规格锁定，12 项监控需求 |
| `v87_rc1_e_l2_dashboard_phase01_monitor_baseline_template.md` | V200-1.0 监控基线模板 |
| `v87_rc1_e_l2_dashboard_phase01_panel_backlog_list.md` | 8 面板开发清单 |
| `v87_rc1_e_l2_dashboard_phase02_alert_rule_iteration_spec.md` | 12 条告警规则规格 |
| `v87_rc1_e_l2_dashboard_phase02_panel_development_report.md` | 面板开发技术报告 |
| `v87_rc1_e_l2_dashboard_phase02_panel_alert_acceptance_report.md` | 面板+告警验收报告 |
| `v87_rc1_e_l2_dashboard_phase02_query_capacity_evaluation.md` | 查询容量评估 |
| `v87_rc1_e_l2_dashboard_phase02_new_field_data_integration_report.md` | 5 字段集成报告 |
| `v87_rc1_hermes_phase01_audit_rule_migration_spec.md` | HERMES 审计规则迁移 |
| `v87_rc1_hermes_phase02_audit_engine_performance_evaluation.md` | HERMES 审计引擎性能 |

### 1.6 关键约束与不变式

| 约束 | 值 | 说明 |
|------|-----|------|
| `BRANCH_LOCKED` | `TRUE` | 所有操作仅限 `feature/v87-rc1-g1` 分支 |
| `NO_MODIFY_V85` | `TRUE` | V85 继承面板严禁修改 |
| `NO_OVERWRITE` | `TRUE` | 严禁覆盖 V86 已有定义 |
| `NO_ZHIJI_API_CALL` | `TRUE` | 禁止直接调用机密 API |
| `IE_AL_001_3LEVEL_PRESERVED` | `TRUE` | IE-AL-001 三级阈值完整保留 |
| `BASELINE_V86_UNTOUCHED` | `TRUE` | V86 基线集群不受灰度影响 |
| `ROLLBACK_WINDOW` | `15min` | 全量回滚时间窗口 |
| `GRAY_PERCENT_START` | `50%` | 灰度起始比例 |
| `GRAY_PERCENT_MAX` | `100%` | 灰度最大比例（评估通过后） |
| `POST_GRAY_OBSERVE_DAYS` | `7` | 灰度后观察期天数 |

---

## 2. 灰度阶段时间线

### 2.1 时间线总览

```
T-2h ─── 灰度前(准备,24项清单) ─── T+0 ─── 灰度启动(密集观察,5min周期) ─── T+30min
    ─── 灰度稳定期(常规观察,1h×12项清单,30min报告) ─── T+4h ─── 灰度评估(GO/COND-GO/RED) ─── T+7d(灰度后,7d观察)
灰度流量: 0% → 50% → 50% → 75%/0%(回滚)
```

### 2.2 灰度前准备 (T-2h ~ T+0)

**目标**: 确保所有前置条件就绪，灰度启动无障碍。

| 时间 | 动作 | 负责人 | 验证方式 | 状态 |
|------|------|--------|----------|------|
| T-2h | 通知所有团队灰度即将启动 | Phase03 Lead | DingTalk `#v87-gray-announce` 发送预告 | ☐ |
| T-1.5h | 确认 DSHB 灰度路由配置就绪 | DSHB Ops | `curl http://dshb-router/v87-gray-status` 返回 `ready` | ☐ |
| T-1.5h | 确认 HERMES 审计对账管道就绪 | HERMES Ops | `curl http://hermes/v87-reconcile-status` 返回 `ready` | ☐ |
| T-1h | 灰度集群健康检查 | DSHE Ops | 全部 33 面板加载正常，P99 指标在预算内 | ☐ |
| T-1h | 告警规则 dry-run 验证 | DSHE Ops | 12 条规则 dry-run 全部 PASS | ☐ |
| T-1h | 回滚脚本准备与测试 | SRE | 本地模拟回滚测试通过 | ☐ |
| T-45min | 确认 5 字段数据管道畅通 | HERMES Ops | 5 字段最近 1h 数据完整率 100% | ☐ |
| T-30min | 最终预检会议 | 全体 | §9.1 检查清单 24/24 PASS | ☐ |
| T-15min | 冻结变更窗口 | Phase03 Lead | 通知所有团队暂停非灰度变更 | ☐ |
| T-5min | 灰度集群最后一轮检查 | DSHE Ops | 缓存预热完成，命中率 ≥95% | ☐ |
| T+0 | **灰度启动** — 流量切换到 50% | DSHB Ops | 灰度面板 QPS 开始爬升 | ☐ |

### 2.3 灰度启动期 (T+0 ~ T+30min) — 密集观察

**目标**: 灰度流量从 0% 攀升至 50%，此阶段指标波动最大，需最高频监控。

| 观察周期 | 频率 | 关键动作 | 升级条件 |
|---------|------|---------|---------|
| 0-5min | 每 30 秒 | 观察流量爬升曲线，确认无突刺 | QPS 跳变 >2× 预期 |
| 5-15min | 每 1 分钟 | 全部关键指标 §3.2 检查，首份状态报告 | 任一关键指标超阈值 |
| 15-25min | 每 1 分钟 | 同上，关注缓存预热曲线 | 缓存命中率 <90% |
| 25-30min | 每 1 分钟 | 稳定化确认，第二份状态报告 | 指标未收敛 |

**密集观察期特别关注**:

1. **流量爬升曲线**: 期望线性爬升至 50%（约 280 QPS 增量），实际偏差 >20% 需调查
2. **缓存预热**: 灰度面板缓存需从冷启动爬升至 ≥95% 命中率，低于 90% 持续 >5min 触发调查
3. **首次告警触发**: 任何首次触发的告警都需人工确认是否为真实异常
4. **V86 基线隔离**: 确认 V86 基线集群指标无异常波动

### 2.4 灰度稳定期 (T+30min ~ T+4h) — 常规观察

**目标**: 灰度流量稳定在 50%，系统进入稳态，按常规节奏观察。

| 观察周期 | 频率 | 关键动作 | 升级条件 |
|---------|------|---------|---------|
| 关键指标 | 每 1 分钟 | §3.2 自动检查，异常时人工介入 | 超阈值 |
| 高优指标 | 每 5 分钟 | §3.3 自动检查 | 超阈值 |
| 中优指标 | 每 15 分钟 | §3.4 自动检查 | 超阈值 |
| 低优指标 | 每 30 分钟 | §3.5 自动检查 | 超阈值 |
| 状态报告 | 每 30 分钟 | 在 `#v87-gray-announce` 提交 | — |
| 每小时清单 | 每 60 分钟 | §9.3 12 项检查 | 任一 FAIL |

**稳定期特别关注**:

1. **存储增长速率**: 预期 ~805GB/90d（灰度 50% 估算），实际增速超过 1.2× 预期需调查
2. **告警触发次数**: 预期每日 5-10 次（正常业务波动），>15 次需调查噪声抑制
3. **降噪率**: 预期 >80%（DBSCAN + 风暴抑制 + 重复抑制 + 维护窗口），<60% 需调查
4. **HERMES 对账**: 5 字段对账匹配率必须 100%，任何不匹配立即升级
5. **V86 vs V87 并行**: 两套集群并行运行，确认资源无争抢

### 2.5 灰度评估点 (T+4h) — 决策会议

**目标**: 基于 4 小时灰度观察数据，做出 GO/COND-GO/RED 三级决策。

#### 决策矩阵

| 决策 | 条件 | 后续动作 |
|------|------|---------|
| **GO** 🟢 | 全部关键指标达标 + 无 CRITICAL 告警 + 无回滚触发条件 + HERMES 对账 100% + V86 基线无异常 | 24h 后升至 75%，再 24h 升至 100% |
| **COND-GO** 🟡 | 1-2 项非关键指标轻微偏离（在安全范围内）+ 无 CRITICAL 告警 + 有明确缓解方案 | 维持 50% 再观察 4h，有条件达标后升 75% |
| **RED** 🔴 | 任一 RED 触发条件满足（见 §6.1） | 立即回滚，通知 VP Engineering |

#### GO 检查清单 (§9.4 摘要)

| # | 检查项 | 阈值 | 实际 | 状态 |
|---|--------|------|------|------|
| 1 | QPS 总量 | ≤560 QPS | — | ☐ |
| 2 | 渲染 P99 | ≤150ms | — | ☐ |
| 3 | 查询 P99 | ≤300ms | — | ☐ |
| 4 | 数据延迟 | ≤500ms | — | ☐ |
| 5 | 缓存命中率 | ≥95% | — | ☐ |
| 6 | 吞吐 | ≥900 ev/s | — | ☐ |
| 7 | WAL 延迟 P99 | <3ms | — | ☐ |
| 8 | 索引延迟 P99 | <7ms | — | ☐ |
| 9 | 丢包率 | <0.005% | — | ☐ |
| 10 | 告警触发次数 (4h) | <15 次 | — | ☐ |
| 11 | 误报数 | 0 | — | ☐ |
| 12 | 漏报数 | 0 | — | ☐ |
| 13 | HERMES 对账匹配率 | 100% | — | ☐ |
| 14 | V86 基线健康度 | 100/100 | — | ☐ |
| 15 | IE-AL-001 三级状态 | 全部 ≤CHECK | — | ☐ |

### 2.6 灰度后长期监控 (T+4h ~ T+7d)

**目标**: 灰度全量后持续监控 7 天，确认系统长期稳定性。

| 时间窗口 | 观察频率 | 关键指标 | 退出条件 |
|---------|---------|---------|---------|
| T+4h ~ T+24h | 同稳定期（1/5/15/30min） | 全部指标 | 24h 内无 CRITICAL 告警 |
| T+24h ~ T+7d | 每小时清单 + 每日回顾 | 全部指标 | 7d 内无 P0 事件 |
| T+7d | 阶段验收 | 全部指标 + 趋势分析 | 进入 Phase04 |

**长期监控特别关注**:

1. **存储增长趋势**: 确认 90d 存储趋势线在预期曲线上（~805GB 灰度 / ~890GB 全量）
2. **基线漂移**: P-008 基线漂移热力图持续观察，漂移率 >5% 需调查
3. **告警阈值漂移**: 运行 7d 后评估阈值是否需要微调
4. **容量预测准确性**: P-003 容量规划面板的预测精度跟踪
5. **HERMES 审计完整性**: 7d 内审计字段完整率必须维持 100%

---

## 3. 关键观察指标

### 3.1 指标分级总览

| 等级 | 检查频率 | 数量 | 覆盖范围 |
|------|---------|------|---------|
| **关键 (Critical)** | 1 分钟 | 5 | QPS、渲染 P99、查询 P99、数据延迟、缓存命中率 |
| **高优 (High)** | 5 分钟 | 4 | 吞吐、WAL 延迟、索引延迟、丢包率 |
| **中优 (Medium)** | 15 分钟 | 3 | 告警触发次数、告警健康度、降噪率 |
| **低优 (Low)** | 30 分钟 | 3 | 存储增长、字段完整率、基线漂移 |
| **总计** | — | **15** | — |

### 3.2 关键指标 (1 分钟检查)

| # | 指标名 | 指标 ID | 阈值 | 告警等级 | 灰度预期 | 违约动作 |
|---|--------|---------|------|---------|---------|---------|
| 1 | QPS 总量 | `hermes.query.qps.total` | ≤560 (保护: 800) | CRITICAL >560, WARNING >520 | ~280 (50%灰度) | WARNING: 5min 内调查; CRITICAL: 2min 确认 + 10min 缓解 |
| 2 | 渲染 P99 | `hermes.render.p99` | ≤150ms | CRITICAL >150ms, WARNING >120ms | ≤130ms | WARNING: 确认是否面板级; CRITICAL: 检查降级层级 |
| 3 | 查询 P99 | `hermes.query.p99` | ≤300ms | CRITICAL >300ms, WARNING >240ms | ≤250ms | WARNING: 检查查询缓存; CRITICAL: 触发查询优化 |
| 4 | 数据延迟 | `hermes.data.delay` | ≤500ms | CRITICAL >500ms, WARNING >400ms | ≤350ms | WARNING: 检查管道; CRITICAL: 检查 HERMES 源端 |
| 5 | 缓存命中率 | `hermes.cache.hit_rate` | ≥95% | CRITICAL <90%, WARNING <93% | ≥95% | WARNING: 检查缓存预热; CRITICAL: 触发缓存重建 |

> QPS 计算: V86=300 + 灰度面板~260 = 560 QPS (保护阈值 800)。渲染预算: P-001≤180ms, P-002≤200ms, P-003≤150ms, P-004≤180ms, P-006≤160ms, P-007≤150ms, P-008≤140ms。

### 3.3 高优指标 (5 分钟检查)

| # | 指标名 | 指标 ID | 阈值 | 告警等级 | 灰度预期 | 违约动作 |
|---|--------|---------|------|---------|---------|---------|
| 1 | 系统吞吐 | `hermes.throughput.evps` | ≥900 ev/s | CRITICAL <900, WARNING <945 | ≥900 ev/s | WARNING: 检查负载分布; CRITICAL: 扩容评估 |
| 2 | WAL 写入延迟 P99 | `hermes.wal.write.p99` | <3ms | CRITICAL >3ms, WARNING >2.4ms | <2ms | WARNING: 检查磁盘 IO; CRITICAL: 检查 WAL 段切换 |
| 3 | 索引写入延迟 P99 | `hermes.index.write.p99` | <7ms | CRITICAL >7ms, WARNING >5.6ms | <5ms | WARNING: 检查索引段合并; CRITICAL: 触发索引优化 |
| 4 | 丢包率 | `hermes.network.pkt_loss` | <0.005% | CRITICAL >0.005%, WARNING >0.004% | <0.002% | WARNING: 检查网络; CRITICAL: 检查网卡与交换机 |

> 吞吐基线: V200-1.0≥900 ev/s (Phase02 实测 932.4 ev/s)。灰度不减少总吞吐，仅改变路由。

### 3.4 中优指标 (15 分钟检查)

| # | 指标名 | 指标 ID | 阈值 | 告警等级 | 灰度预期 | 违约动作 |
|---|--------|---------|------|---------|---------|---------|
| 1 | 告警触发次数 | `hermes.alert.trigger.count` | <15/h | WARNING >15/h, CRITICAL >25/h | 5-10/h | WARNING: 检查噪声抑制; CRITICAL: 抑制规则调优 |
| 2 | 告警健康度 | `hermes.alert.health.score` | 100/100 | WARNING <100, CRITICAL <90 | 100/100 | WARNING: 调查降级原因; CRITICAL: 冻结告警评估 |
| 3 | 降噪率 | `hermes.alert.noise_reduction` | ≥80% | WARNING <70%, CRITICAL <60% | ≥80% | WARNING: 检查 DBSCAN 聚类; CRITICAL: 降噪参数调优 |

### 3.5 低优指标 (30 分钟检查)

| # | 指标名 | 指标 ID | 阈值 | 告警等级 | 灰度预期 | 违约动作 |
|---|--------|---------|------|---------|---------|---------|
| 1 | 存储增长 | `hermes.storage.growth.gb` | ~805GB/90d (灰度) | WARNING >1.2×预期, CRITICAL >1.5×预期 | ~805GB | WARNING: 检查 TTL; CRITICAL: 检查索引膨胀 |
| 2 | 字段完整率 | `hermes.field.completeness` | 100% | CRITICAL <100% | 100% | CRITICAL: 立即升级 HERMES |
| 3 | 基线漂移 | `hermes.baseline.drift.rate` | <5% | WARNING >5%, CRITICAL >10% | <3% | WARNING: 调查漂移源; CRITICAL: 冻结漂移面板 |

**5 个 HERMES 字段说明**:
| 字段 | 类型 | 完整率要求 | 灰度预期 |
|------|------|-----------|---------|
| `event_type` | VARCHAR(64) | 100% | 100% |
| `priority` | VARCHAR(8) | 100% | 100% |
| `trace_id` | VARCHAR(128) | 100% | 100% |
| `batch_id` | VARCHAR(64) | 100% | 100% |
| `retry_count` | INTEGER | 100% | 100% |

### 3.6 阈值对照总表 (V200-1.0 基线)

| 阈值 | V100-1.0 | V200-1.0 | V87 目标 | 灰度保护 |
|------|----------|----------|---------|---------|
| 系统吞吐 | ≥700 ev/s | ≥900 ev/s | ≥900 ev/s | — |
| WAL 写入延迟 P99 | ≤5ms | ≤3ms | <3ms | <3ms |
| 索引写入延迟 P99 | ≤10ms | ≤7ms | <7ms | <7ms |
| 丢包率 | ≤0.01% | ≤0.005% | <0.005% | <0.005% |
| 内存使用率 | ≤85% | ≤80% | ≤80% | ≤80% |
| 网络延迟 P99 | ≤5ms | ≤3ms | ≤3ms | ≤3ms |
| 查询 P99 (30d) | ≤500ms | ≤300ms | ≤300ms | ≤300ms |
| 渲染 P99 | ≤200ms | ≤150ms | ≤150ms | ≤150ms |
| 索引膨胀 | ≤10% | ≤8% | ≤8% | ≤8% |
| IE-AL-001 CHECK | — | 8.0% | 8.0% | 8.0% |
| IE-AL-001 WARNING | — | 8.05% | 8.05% | 8.05% |
| IE-AL-001 CRITICAL | — | 8.5% | 8.5% | 8.5% |

---

## 4. 告警响应 SOP

### 4.1 三级告警响应框架

```
┌─────────────────────────────────────────────────────────────────┐
│                    告警响应三级框架                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 1 (Warning) 🟡                                          │
│  ├── 确认: 5 分钟内                                            │
│  ├── 调查: 15 分钟内                                           │
│  ├── 动作: 观察为主，瞬时异常可忽略                              │
│  └── 升级: 15 分钟内未解决 → Level 2                            │
│                                                                 │
│  Level 2 (Critical) 🟠                                         │
│  ├── 确认: 2 分钟内                                            │
│  ├── 调查: 5 分钟内                                            │
│  ├── 动作: 10 分钟内采取纠正措施                                │
│  └── 升级: 10 分钟内未解决 → Level 3                            │
│                                                                 │
│  Level 3 (RED/Blocker) 🔴                                      │
│  ├── 确认: 1 分钟内                                            │
│  ├── 调查: 即时                                                │
│  ├── 动作: 触发回滚程序 (§6)                                   │
│  └── 升级: 即时通知 VP Engineering                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Level 1 (Warning) 响应流程

**触发条件**: 任一指标超过 WARNING 阈值但未达 CRITICAL。

**响应时间线**:
```
T+0min:  告警触发 → DingTalk @on-call + Email
T+1min:  确认告警 (ack) → 记录工单号
T+5min:  首次确认 (必须) → 如未确认，自动 @on-call-2
T+15min: 调查完成 → 判断为瞬时/持续/误报
T+15min+: 瞬时 → 关闭; 持续 → 升级 Level 2; 误报 → 抑制
```

**响应步骤**:
1. 确认告警（ack）: `curl -X POST http://hermes/alert/{id}/ack`
2. 记录工单: 在 `#v87-gray-dshe` 创建跟踪记录
3. 初步调查:
   - 检查指标当前值与趋势（是否回落）
   - 检查相关面板状态
   - 检查是否有其他关联告警
4. 决策:
   - 瞬时异常（<5min 回落）→ 关闭，记录到观察日志
   - 持续超阈值 → 升级 Level 2
   - 确认为误报 → 添加抑制规则，记录到误报库

### 4.3 Level 2 (Critical) 响应流程

**触发条件**: 任一指标超过 CRITICAL 阈值，或 Level 1 在 15min 内未解决。

**响应时间线**:
```
T+0min:  告警触发 → DingTalk @on-call + PagerDuty + Email
T+1min:  确认告警 (ack) → 通知 DSHB/HERMES
T+2min:  首次确认 (必须) → 如未确认，自动 @SRE-lead
T+5min:  调查完成 → 识别根因
T+10min: 纠正措施执行 → 验证效果
T+15min+: 如未解决 → 升级 Level 3 + 回滚评估
```

**响应步骤**:
1. 确认告警（ack）: 同步通知 DSHB Ops 和 HERMES Ops
2. 创建事件工单: `INC-V87-{date}-{seq}`
3. 根因调查:
   - 关联分析: 检查 12 条告警规则的关联面板
   - 时间线回溯: 最近 15min 的变更、部署、配置修改
   - 资源检查: CPU/内存/磁盘/网络四项
   - 面板级定位: 8 个面板逐个排查
4. 纠正措施:
   - 缓存重建: `curl -X POST http://hermes/cache/refresh`
   - 查询优化: 临时关闭高消耗面板
   - 限流: 触发 QPS 保护阈值限流
   - 降级: L0→L1→L2 逐层降级
5. 效果验证: 纠正后 5min 内指标必须回落

### 4.4 Level 3 (RED/Blocker) 响应流程

**触发条件**: 任一 RED 条件满足（见 §6.1）。

**响应时间线**:
```
T+0min:  告警触发 → 所有渠道通知 (DingTalk + PagerDuty + Email + SMS)
T+1min:  确认告警 (ack) → 触发回滚程序
T+1min:  通知 VP Engineering
T+2min:  灰度流量暂停 (DSHB 路由切换)
T+5min:  V86 基线恢复验证
T+15min: 全量回滚完成
T+30min: 根因初步分析
```

**响应步骤**:
1. 确认并通知: 全渠道通知，VP Engineering 必须收到
2. 触发回滚: 执行 §6.3 完整回滚步骤
3. 冻结: 暂停所有灰度相关操作
4. 根因分析: 回滚后启动 RCA
5. 恢复评估: RCA 完成后评估恢复条件

### 4.5 响应矩阵

| 告警类型 | L1 动作 | L2 动作 | L3 动作 | 升级 |
|---------|--------|--------|--------|------|
| QPS | 确认+调查 | 限流 | 回滚 | 15/10/5min |
| Render P99 | 检查面板 | 降级面板 | 回滚 | 15/10/5min |
| Query P99 | 检查缓存 | 查询优化 | 回滚 | 15/10/5min |
| Data Delay | 检查管道 | HERMES 调查 | 回滚 | 15/10/5min |
| Cache | 检查预热 | 缓存重建 | 回滚 | 15/10/5min |
| Throughput | 检查负载 | 扩容评估 | 回滚 | 15/10/5min |
| WAL/Index | 检查磁盘/段 | 优化 | 回滚 | 15/10/5min |
| Packet Loss | 检查网络 | 检查网卡 | 回滚 | 15/10/5min |
| Alert Noise | 检查抑制 | 降噪调优 | 冻结评估 | 15/10/5min |
| Field/Reconcile | 立即调查 | HERMES 升级 | 回滚 | 5/2/1min |
| IE-AL-001 | 检查膨胀 | 索引优化 | 三级升级 | 15/10/5min |

### 4.6 误报处理

| 步骤 | 动作 | 负责人 |
|------|------|--------|
| 1 | 标记为误报: `curl -X POST http://hermes/alert/{id}/dismiss -d '{"reason":"false_positive"}'` | On-call |
| 2 | 分析误报原因: 阈值过低/查询异常/测试数据 | DSHE Ops |
| 3 | 评估是否需要调整阈值 | DSHE Lead |
| 4 | 记录到误报库: `analysis/hermes_e2e_test/alert_false_positive_log.md` | On-call |
| 5 | 更新告警健康度评分 | DSHE Ops |
| 6 | 灰度评估时计入误报计数（必须为 0） | Phase03 Lead |

### 4.7 抑制与去重

**抑制规则**:
- **维护窗口抑制**: 每日 02:00-04:00 UTC，非 CRITICAL 告警自动抑制
- **关联告警抑制**: 同一根因的关联告警（DBSCAN 聚类距离 <0.3）仅保留主告警
- **重复告警抑制**: 同一指标同一级别 5min 内重复触发自动抑制
- **风暴抑制**: 1min 内 >5 条告警自动聚合为一条

**去重率目标**: ≥80%（即 80% 的原始告警被抑制或去重）

---

## 5. 监控面板

### 5.1 主面板: V87 灰度总览

**面板 ID**: `DSHE-DASH-V87-GRAY-OVERVIEW`

| 区域 | 内容 | 刷新 |
|------|------|------|
| 左上 | 灰度比例 + 灰度 QPS + V86 QPS | 30s |
| 右上 | 降级层级 (L0-L3) + 回滚倒计时 | 30s |
| 中部 | 关键 5 指标: QPS/Render/Query/Delay/Cache | 60s |
| 中下 | 高优 4 指标: Throughput/WAL/Index/Loss | 300s |
| 左下 | V86 vs V87 对比雷达图 | 300s |
| 右下 | 降级状态 + 触发条件 | 60s |
| 底部 | 最近 30min 告警时间线 | 60s |

### 5.2 面板级监控 (8 个 V87 面板)

| 面板 | 关键指标 | 异常指示 |
|------|---------|---------|
| P-001 AI 异常检测 | inference_latency, detection_accuracy | 延迟>200ms 或准确率<90% |
| P-002 跨服务依赖 | render_time, node_count, edge_count | 节点>500 或渲染>200ms |
| P-003 容量规划 | forecast_accuracy, compute_time | 精度<85% 或计算>3s |
| P-004 告警关联 | clustering_time, correlation_accuracy | 聚类>5s 或准确率<85% |
| P-006 全链路追踪 | trace_count, query_time, data_size | 追踪>100k/min 或查询>300ms |
| P-007 审计对账 | match_rate, reconcile_delay | 匹配率<100% 或延迟>500ms |
| P-008 基线漂移 | drift_sensitivity, heatmap_render_time | 检测延迟>10min |
| P-005 混沌工程 | (暂缓) | — |

### 5.3 告警关联面板

**面板 ID**: `DSHE-DASH-V87-ALERT-CORRELATION` — 活跃告警列表 / 告警时间线 / 降噪统计 / DBSCAN 聚类可视化 / 告警健康度仪表 / 误报漏报追踪 / IE-AL-001 三级状态

### 5.4 容量面板

**面板 ID**: `DSHE-DASH-V87-CAPACITY` — QPS 仪表 (保护:800) / 存储仪表 (~805GB) / 缓存仪表 (≥95%) / 降级仪表 (L0-L3) / 吞吐仪表 (≥900 ev/s)

### 5.5 审计对账面板

**面板 ID**: `DSHE-DASH-V87-AUDIT-RECONCILE`

| 区域 | 内容 | 阈值 |
|------|------|------|
| 5 字段完整率 | event_type / priority / trace_id / batch_id / retry_count | 100% |
| 对账匹配率 | 灰度数据 vs HERMES 源端 | 100% |
| 批次完整性 | batch_id 连续性检查 | 100% |
| 追踪关联 | trace_id 跨面板关联 | 100% |
| 对账延迟 | 对账处理延迟 | ≤500ms |
| 异常事件 | 审计异常率 | <1% |

---

## 6. 回滚程序

### 6.1 触发条件

**RED 触发条件** (任一满足即触发):
1. 任一 P0 blocker 事件
2. 任一 CRITICAL 告警在 10min 内未缓解
3. 2 次连续 CRITICAL 告警（同一指标或不同指标）
4. 任一关键指标（§3.2）超阈值持续 >5min
5. HERMES 对账匹配率 <100%
6. 字段完整率 <100%（任一字段）
7. V86 基线健康度 <100/100
8. 灰度集群 CPU >95% 或 内存 >85%
9. IE-AL-001 达到 CRITICAL 级别 (>8.5%)
10. 数据延迟 >1000ms 持续 >2min
11. 丢包率 >0.01% 持续 >1min
12. 人工判断需要回滚（Phase03 Lead 或 VP Engineering）

### 6.2 回滚分级

| 级别 | 名称 | 触发条件 | 回滚范围 | 时间线 |
|------|------|---------|---------|--------|
| RB-1 | 灰度暂停 | 任一 WARNING 持续 >15min | 暂停灰度流量，保留配置 | 1min |
| RB-2 | 灰度回退 | 任一 CRITICAL 或 2×CRITICAL | 灰度流量回到 0%，保留 V86 | 5min |
| RB-3 | 全量回滚 | RED 条件 | 全量回滚至 V86 基线 | 15min |

### 6.3 完整回滚步骤

#### RB-1: 灰度暂停

```
T+0min:  确认暂停条件 → 在 #v87-gray-announce 通知
T+1min:  DSHB Ops 暂停灰度路由
         $ dshb-router gray-pause --target v87-gray-cluster
T+2min:  验证灰度流量 = 0
         $ curl http://dshb-router/v87-gray-traffic | jq '.qps'
         # 预期: 0
T+3min:  DSHE Ops 确认灰度集群进入 standby
T+5min:  状态报告 → 评估是否继续
```

#### RB-2: 灰度回退

```
T+0: 确认条件→通知全体 | T+1: DSHB切回V86 ($ dshb-router gray-revert)
T+2: 验证灰度=0,V86=100% | T+3: DSHE停面板 | T+4: HERMES停管道
T+5: 验证V86健康度=100/100 | T+10: 根因分析 | T+15: 决策(恢复/调查/RB-3)
```

#### RB-3: 全量回滚

```
T+0: RED确认→全渠道通知→VP | T+1: DSHB全量回滚+禁用功能
T+3: DSHE停面板 | T+5: HERMES停管道 ($ hermes pipeline-stop)
T+7: 验证V86: 25面板正常,健康度100/100,QPS~300,无CRITICAL
T+10: 通知回滚完成 | T+15: 冻结灰度操作 | T+30: 启动RCA
```

### 6.4 回滚时间线总览

```
RB-1 (灰度暂停):  1min  ──── 暂停灰度流量
RB-2 (灰度回退):  5min  ──── 灰度流量回 0%，V86 恢复
RB-3 (全量回滚):  15min ──── 全量回滚至 V86 基线

总回滚窗口: 15min (从触发到全量回滚完成)
```

### 6.5 回滚公告模板

```
🚨 V87-RC1 L2 灰度回滚通知
事件编号: INC-V87-{YYYYMMDD}-{SEQ}
回滚级别: RB-{1|2|3} | 触发时间: {HH:MM:SS} UTC
触发原因: {条件描述} | 影响: V87 灰度 (V86 不受影响)
当前: 灰度 {n}QPS→0 | V86 正常 | 告警 {n} 条
动作: ☐ DSHB 切换 ☐ DSHE 停面板 ☐ HERMES 停管道 ☐ V86 验证
负责人: SRE@{name} DSHB@{name} DSHE@{name} HERMES@{name}
预计恢复: {待评估|已恢复} | 下次更新: 30min 内
联系: #v87-gray-announce
```

### 6.6 回滚后验证

| 验证项 | 方法 | 预期 | 状态 |
|--------|------|------|------|
| V86 QPS | `curl http://dshb-router/traffic` | ~300 QPS | ☐ |
| V86 面板 | 手动检查 25 面板 | 全部正常 | ☐ |
| V86 告警 | 检查告警列表 | 无 CRITICAL | ☐ |
| 健康度 | `curl http://hermes/health` | 100/100 | ☐ |
| 存储 | 检查存储增长 | 正常速率 | ☐ |
| 灰度流量 | `curl http://dshb-router/v87-gray-traffic` | 0 QPS | ☐ |
| HERMES 对账 | 检查对账状态 | 已停止 | ☐ |
| 缓存 | 检查缓存命中率 | ≥90% (V86 基线) | ☐ |

---

## 7. 升级矩阵

### 7.1 升级路径

```
Level 0: On-call Engineer (值班工程师)
    ↓ [15min 未解决 / Level 2]
Level 1: SRE Lead (SRE 负责人)
    ↓ [10min 未解决 / 需要资源调配]
Level 2: DSHE TL (L2 技术负责人)
    ↓ [需要跨团队协作]
Level 3: DSHB TL / HERMES TL (L1/L3 技术负责人)
    ↓ [重大事件 / 管理层决策]
Level 4: VP Engineering (工程副总裁)
```

### 7.2 各级升级时间线

| 级别 | 角色 | 升级触发 | 响应时间 | 联系方式 |
|------|------|---------|---------|---------|
| L0 | On-call Engineer | 任一告警 | 即时 | DingTalk @on-call |
| L1 | SRE Lead | L0 15min 未解决 | 5min | DingTalk @sre-lead + PagerDuty |
| L2 | DSHE TL | L1 10min 未解决 / 需技术决策 | 5min | DingTalk @dshe-tl + Phone |
| L3 | DSHB TL | 需 L1 团队协作 | 5min | DingTalk @dshb-tl + Phone |
| L3 | HERMES TL | 需 L3 团队协作 | 5min | DingTalk @hermes-tl + Phone |
| L4 | VP Engineering | Level 3 告警 / 回滚 / 重大事件 | 1min | Phone + Email + SMS |

### 7.3 联系人

| 角色 | 姓名 | 电话 | DingTalk | PagerDuty |
|------|------|------|---------|-----------|
| On-call Engineer | {rotating} | {rotation} | @v87-oncall | PD-V87-GRAY |
| SRE Lead | {name} | {phone} | @sre-lead | PD-SRE-LEAD |
| DSHE TL | {name} | {phone} | @dshe-tl | PD-DSHE-TL |
| DSHB TL | {name} | {phone} | @dshb-tl | PD-DSHB-TL |
| HERMES TL | {name} | {phone} | @hermes-tl | PD-HERMES-TL |
| VP Engineering | {name} | {phone} | @vp-eng | PD-VP-ENG |
| Phase03 Lead | {name} | {phone} | @phase03-lead | PD-PHASE03 |

### 7.4 升级触发条件

| 条件 | 目标级别 | 说明 |
|------|---------|------|
| 任一 CRITICAL 告警 | L0 → L1 (15min) | 值班未解决 |
| Level 2 告警未解决 | L1 → L2 (10min) | 需技术决策 |
| 回滚触发 | L2 → L3 | 需跨团队协作 |
| RED 条件 | L3 → L4 (1min) | 重大事件 |
| 字段完整率 <100% | L3 → L4 (1min) | HERMES 数据完整性 |
| 对账匹配率 <100% | L3 → L4 (1min) | 审计完整性 |
| V86 基线受影响 | L3 → L4 (1min) | 基线不可降级 |
| 人工判断 | 任意 → L4 | 任何人员可升级 |

---

## 8. 通信协议

### 8.1 钉钉频道

| 频道 | 用途 | 成员 | 消息频率 |
|------|------|------|---------|
| `#v87-gray-dshe` | DSHE L2 团队内部沟通 | DSHE Ops + SRE + Dev | 按需 |
| `#v87-gray-dshb` | DSHB L1 团队内部沟通 | DSHB Ops + Router + API | 按需 |
| `#v87-gray-hermes` | HERMES L3 团队内部沟通 | HERMES Ops + Audit + Pipeline | 按需 |
| `#v87-gray-announce` | 跨团队公告 + 状态报告 | 全体 | 30min 一次 |

### 8.2 报告频率

| 阶段 | 报告频率 | 报告人 | 频道 |
|------|---------|--------|------|
| 灰度启动期 (T+0~T+30min) | 15min 一次 | On-call | `#v87-gray-announce` |
| 灰度稳定期 (T+30min~T+4h) | 30min 一次 | On-call | `#v87-gray-announce` |
| 灰度评估期 (T+4h) | 评估报告 | Phase03 Lead | `#v87-gray-announce` + Meeting |
| 灰度后观察 (T+4h~T+7d) | 每日一次 | Phase03 Lead | `#v87-gray-announce` |

### 8.3 状态报告模板

```
📊 V87-RC1 L2 灰度状态报告 | {HH:MM} UTC | 灰度 {h:mm} | 50%

关键: QPS {v}/560 {✅⚠️🔴} Render {v}/≤150ms {✅⚠️🔴} Query {v}/≤300ms {✅⚠️🔴}
      Delay {v}/≤500ms {✅⚠️🔴} Cache {v}%/≥95% {✅⚠️🔴}
高优: Throughput {v}/≥900 {✅⚠️🔴} WAL {v}/<3ms {✅⚠️🔴} Index {v}/<7ms {✅⚠️🔴} Loss {v}%/<0.005% {✅⚠️🔴}
告警: 活跃{n} 新增{n} 已解{n} | 降噪{v}% 健康{v}/100
HERMES: 字段{v}% 匹配{v}% | 降级 L{0-3} | 回滚倒计时: N/A|15min
备注: {无异常|描述} | 负责人: @{on-call}
```

### 8.4 事件通信模板

```
🚨 V87-RC1 L2 灰度事件通知
事件: INC-V87-{SEQ} | 级别: L{1|2|3} {Warning|Critical|RED} | 时间: {HH:MM:SS}
规则: {rule-id} | 当前: {value} | 阈值: {threshold}
影响: 面板{panels} 用户{impact} 数据{integrity}
状态: ☐ack ☐调查 ☐纠正 ☐验证 | 当前: {investigating|mitigating|resolved}
负责人: @{on-call} | 下次更新: {15|5|1}min 内
```

### 8.5 决策通知模板

```
📢 V87-RC1 L2 灰度决策通知 | {HH:MM} UTC | 灰度 {h:mm}
决策: {🟢GO|🟡COND-GO|🔴RED}
依据: 指标{5/5|n/5} 告警{0|n}CRIT 对账{100%|n%} V86{正常|异常} 回滚{未触发|触发}
后续: 🟢→24h75%→48h100% | 🟡→维持50%再观4h | 🔴→立即回滚+RCA
决策: @{phase03-lead} | 参与: DSHE/DSHB/HERMES TL + SRE Lead
```

---

## 9. 观察检查清单

### 9.1 灰度前检查清单 (24 项)

| # | 检查项 | 类别 | 验证方法 | 负责人 | 状态 |
|---|--------|------|---------|--------|------|
| 1 | 灰度集群部署完成 | 基础设施 | `kubectl get pods -n v87-gray` 全部 Running | DSHE Ops | ☐ |
| 2 | V86 基线集群健康 | 基础设施 | 健康度 = 100/100 | DSHE Ops | ☐ |
| 3 | 网络连通性验证 | 基础设施 | `ping/nc` 灰度↔基线↔HERMES | DSHE Ops | ☐ |
| 4 | DNS 解析正确 | 基础设施 | `dig v87-gray.internal` 返回正确 IP | DSHE Ops | ☐ |
| 5 | TLS 证书有效 | 安全 | `openssl s_client` 检查过期 | DSHE Ops | ☐ |
| 6 | DSHB 灰度路由配置就绪 | 路由 | `curl http://dshb-router/v87-gray-status` = `ready` | DSHB Ops | ☐ |
| 7 | DSHB 流量权重配置正确 | 路由 | V86=50%, V87=50% | DSHB Ops | ☐ |
| 8 | DSHB 回滚脚本就绪 | 路由 | `dshb-router rollback --dry-run` PASS | DSHB Ops | ☐ |
| 9 | 8 面板全部加载正常 | 面板 | 手动检查 33 面板 (25+8) | DSHE Ops | ☐ |
| 10 | 12 告警规则 dry-run PASS | 告警 | 全部 12 条 dry-run 通过 | DSHE Ops | ☐ |
| 11 | IE-AL-001 三级阈值确认 | 告警 | CHECK=8.0% WARN=8.05% CRIT=8.5% | DSHE Ops | ☐ |
| 12 | 降噪策略启用 | 告警 | DBSCAN+风暴+重复+维护窗口 4 件套 | DSHE Ops | ☐ |
| 13 | HERMES 5 字段管道畅通 | 数据 | 最近 1h 完整率 100% | HERMES Ops | ☐ |
| 14 | HERMES 审计对账就绪 | 数据 | `curl http://hermes/v87-reconcile-status` = `ready` | HERMES Ops | ☐ |
| 15 | HERMES 回滚脚本就绪 | 数据 | `hermes pipeline-rollback --dry-run` PASS | HERMES Ops | ☐ |
| 16 | 缓存预热完成 | 性能 | 缓存命中率 ≥95% | DSHE Ops | ☐ |
| 17 | QPS 基线确认 | 性能 | V86 QPS ~300 | DSHE Ops | ☐ |
| 18 | 降级策略配置就绪 | 性能 | L0→L1→L2→L3 四级降级配置 | DSHE Ops | ☐ |
| 19 | 监控面板就绪 | 监控 | 全部 5 个监控面板加载正常 | DSHE Ops | ☐ |
| 20 | 告警通知通道就绪 | 通信 | DingTalk/PagerDuty/Email/SMS 全部可达 | SRE | ☐ |
| 21 | 联系人列表确认 | 通信 | 7 级联系人全部确认 | Phase03 Lead | ☐ |
| 22 | 回滚脚本测试通过 | 回滚 | 本地模拟回滚测试 PASS | SRE | ☐ |
| 23 | 变更窗口冻结 | 流程 | 通知全体暂停非灰度变更 | Phase03 Lead | ☐ |
| 24 | 灰度启动审批 | 流程 | Phase03 Lead + VP Engineering 签字 | Phase03 Lead | ☐ |

### 9.2 灰度启动检查清单 (18 项)

| # | 检查项 | 验证方法 | 预期 | 状态 |
|---|--------|---------|------|------|
| 1 | 灰度路由启动 | `curl http://dshb-router/v87-gray-status` | `active` | ☐ |
| 2 | 灰度流量开始爬升 | 观察 QPS 曲线 | 线性爬升至 50% | ☐ |
| 3 | 5 面板加载正常 (首批) | 手动检查 P-001~P-004,P-006 | 全部正常 | ☐ |
| 4 | 8 面板全部加载 (30min后) | 全部 8 面板检查 | 全部正常 | ☐ |
| 5 | QPS 在预期范围内 | QPS 仪表 | ≤560 | ☐ |
| 6 | 渲染 P99 达标 | 渲染面板 | ≤150ms | ☐ |
| 7 | 查询 P99 达标 | 查询面板 | ≤300ms | ☐ |
| 8 | 数据延迟达标 | 延迟面板 | ≤500ms | ☐ |
| 9 | 缓存命中率达标 | 缓存面板 | ≥95% | ☐ |
| 10 | 吞吐达标 | 吞吐面板 | ≥900 ev/s | ☐ |
| 11 | WAL 延迟达标 | WAL 面板 | <3ms | ☐ |
| 12 | 索引延迟达标 | 索引面板 | <7ms | ☐ |
| 13 | 丢包率达标 | 网络面板 | <0.005% | ☐ |
| 14 | 无 CRITICAL 告警 | 告警面板 | 0 CRITICAL | ☐ |
| 15 | HERMES 对账 100% | 对账面板 | 100% 匹配 | ☐ |
| 16 | 5 字段完整率 100% | 字段面板 | 100% | ☐ |
| 17 | V86 基线无影响 | 基线面板 | 100/100 | ☐ |
| 18 | 首份状态报告提交 | `#v87-gray-announce` | 已提交 | ☐ |

### 9.3 每小时观察检查清单 (12 项)

| # | 检查项 | 频率 | 阈值 | 状态 |
|---|--------|------|------|------|
| 1 | QPS 趋势 | 每 1min | ≤560 | ☐ |
| 2 | 渲染 P99 趋势 | 每 1min | ≤150ms | ☐ |
| 3 | 查询 P99 趋势 | 每 1min | ≤300ms | ☐ |
| 4 | 数据延迟趋势 | 每 1min | ≤500ms | ☐ |
| 5 | 缓存命中率 | 每 1min | ≥95% | ☐ |
| 6 | 吞吐 + WAL + 索引 + 丢包 | 每 5min | 见 §3.3 | ☐ |
| 7 | 告警触发次数 (1h) | 每 15min | <15/h | ☐ |
| 8 | 告警健康度 | 每 15min | 100/100 | ☐ |
| 9 | 降噪率 | 每 15min | ≥80% | ☐ |
| 10 | HERMES 对账 + 5 字段 | 每 30min | 100% | ☐ |
| 11 | 存储增长 + 基线漂移 | 每 30min | 见 §3.5 | ☐ |
| 12 | 降级层级 + V86 基线 | 每 30min | L0 / 100 | ☐ |

### 9.4 灰度评估检查清单 (15 项)

| # | 检查项 | 阈值 | 实际值 | 状态 |
|---|--------|------|--------|------|
| 1 | QPS 总量 | ≤560 | — | ☐ |
| 2 | 渲染 P99 | ≤150ms | — | ☐ |
| 3 | 查询 P99 | ≤300ms | — | ☐ |
| 4 | 数据延迟 | ≤500ms | — | ☐ |
| 5 | 缓存命中率 | ≥95% | — | ☐ |
| 6 | 系统吞吐 | ≥900 ev/s | — | ☐ |
| 7 | WAL 延迟 P99 | <3ms | — | ☐ |
| 8 | 索引延迟 P99 | <7ms | — | ☐ |
| 9 | 丢包率 | <0.005% | — | ☐ |
| 10 | 告警触发次数 (4h) | <15 次 | — | ☐ |
| 11 | 误报数 | 0 | — | ☐ |
| 12 | 漏报数 | 0 | — | ☐ |
| 13 | HERMES 对账匹配率 | 100% | — | ☐ |
| 14 | V86 基线健康度 | 100/100 | — | ☐ |
| 15 | IE-AL-001 三级状态 | 全部 ≤CHECK | — | ☐ |

### 9.5 灰度后检查清单 (10 项)

| # | 检查项 | 频率 | 验证方法 | 状态 |
|---|--------|------|---------|------|
| 1 | 每日状态回顾 | 每日 | 检查 7d 内告警趋势 | ☐ |
| 2 | 存储增长趋势 | 每日 | 确认 90d 预测曲线 | ☐ |
| 3 | 告警阈值评估 | 每 3d | 评估阈值是否需要微调 | ☐ |
| 4 | 降噪率趋势 | 每日 | 确认 ≥80% | ☐ |
| 5 | HERMES 对账 | 每日 | 100% 匹配 | ☐ |
| 6 | 基线漂移趋势 | 每日 | <5% | ☐ |
| 7 | 容量预测精度 | 每日 | P-003 面板精度 ≥85% | ☐ |
| 8 | 7d 趋势报告 | T+7d | 完整趋势分析 | ☐ |
| 9 | Phase04 准入 | T+7d | 7d 内无 P0 事件 | ☐ |
| 10 | 阶段验收签署 | T+7d | Phase03 Lead + VP Engineering | ☐ |

---

## 10. DSHB/HERMES 同步点

### 10.1 DSHB 同步

| 同步项 | DSHB 责任 | 验证方法 | 频率 | 状态 |
|--------|----------|---------|------|------|
| 灰度流量路由确认 | 路由配置 + 权重设置 | `curl http://dshb-router/v87-gray-status` | 灰度启动时 | ☐ |
| 功能开关同步 | `v87-gray-routing` feature flag | `curl http://dshb-router/feature-flags` | 灰度启动时 | ☐ |
| API 性能确认 | DSHB API P99 <50ms | API 监控面板 | 每 5min | ☐ |
| 流量分布验证 | V86=50%, V87=50% | `curl http://dshb-router/traffic-distribution` | 每 15min | ☐ |
| 回滚就绪确认 | 回滚脚本 + 切换时间 | `dshb-router rollback --dry-run` | 灰度前 | ☐ |
| 灰度比例调整 | 50% → 75% → 100% | 路由权重更新 | 按决策 | ☐ |

### 10.2 HERMES 同步

| 同步项 | HERMES 责任 | 验证方法 | 频率 | 状态 |
|--------|-----------|---------|------|------|
| 审计字段完整率 | 5 字段完整率 100% | `curl http://hermes/field-completeness` | 每 15min | ☐ |
| 追踪完整性 | trace_id 跨面板关联 | `curl http://hermes/trace-integrity` | 每 15min | ☐ |
| 对账结果 | 灰度 vs 源端 100% 匹配 | `curl http://hermes/reconcile-result` | 每 15min | ☐ |
| 批次完整性 | batch_id 连续性 | `curl http://hermes/batch-integrity` | 每 15min | ☐ |
| 审计引擎性能 | 审计引擎延迟 <500ms | `curl http://hermes/engine-latency` | 每 5min | ☐ |
| 审计管道状态 | 管道运行中 | `curl http://hermes/pipeline-status` | 每 15min | ☐ |
| 对账回滚就绪 | 回滚脚本 | `hermes pipeline-rollback --dry-run` | 灰度前 | ☐ |

### 10.3 联合观察窗口

| 窗口 | 时间 | 参与方 | 观察重点 | 输出 |
|------|------|--------|---------|------|
| W1 | T+30min | DSHE+DSHB+HERMES | 灰度启动稳定性 | 联合确认报告 |
| W2 | T+1h | DSHE+DSHB+HERMES | 1h 稳定性趋势 | 趋势分析报告 |
| W3 | T+4h | DSHE+DSHB+HERMES+VP | 灰度评估决策 | GO/COND-GO/RED |
| W4 | T+24h | DSHE+DSHB+HERMES | 24h 稳定性 | 稳定性确认报告 |

**联合观察会议模板**:
```
🤝 V87-RC1 L2 联合观察 | W{1|2|3|4} | {T+30min|1h|4h|24h} | {HH:MM} UTC
DSHE: 面板{33/33|n/33} 指标{5/5|n/5} 告警{0|n}CRIT 降级L{0-3}
DSHB: 路由{正常|异常} API{<50ms|超标} 分布{50/50|偏差}
HERMES: 字段{100%|n%} 对账{100%|n%} 延迟{<500ms|超标}
决策: {🟢继续|🟡加强|🔴暂停/回滚}
```

### 10.4 三方对账

| 对账维度 | DSHE 数据 | DSHB 数据 | HERMES 数据 | 一致率 | 状态 |
|---------|----------|----------|------------|--------|------|
| 流量 | 面板 QPS | 路由 QPS | 审计事件 QPS | 100% | ☐ |
| 告警 | DSHE 告警列表 | — | HERMES 告警列表 | 100% | ☐ |
| 审计字段 | 面板展示 | — | 源端数据 | 100% | ☐ |
| 对账 | 对账面板 | — | 对账结果 | 100% | ☐ |
| 追踪 | 追踪面板 | — | 追踪数据 | 100% | ☐ |

---

## 11. 速查卡

### 11.1 值班工程师一页纸

```
V87-RC1 L2 灰度值班速查卡
分支: feature/v87-rc1-g1 | 比例: 50% | 面板: 8+25=33 | 告警: 12 | 字段: 5

关键阈值 (1min): QPS≤560(保护800) Render≤150ms Query≤300ms Delay≤500ms Cache≥95%
高优阈值 (5min): Throughput≥900ev/s WAL<3ms Index<7ms Loss<0.005%

告警响应: L1(Warning) ack5min→15min调查 | L2(Critical) ack2min→10min纠正 | L3(RED) ack1min→回滚
回滚: RB-1暂停1min | RB-2回退5min | RB-3全量15min
升级: On-call→SRE Lead→DSHE TL→DSHB/HERMES TL→VP Eng
频道: #v87-gray-announce(30min) #v87-gray-dshe/-dshb/-hermes(内部)
决策: GO→24h75% | COND-GO→维持50%再观4h | RED→立即回滚
```

### 11.2 关键阈值速查

| 类别 | 指标 | 阈值 | 级别 | 频率 |
|------|------|------|------|------|
| Critical | QPS | ≤560 / 保护800 | C>560 W>520 | 1min |
| Critical | Render P99 | ≤150ms | C>150 W>120 | 1min |
| Critical | Query P99 | ≤300ms | C>300 W>240 | 1min |
| Critical | Data Delay | ≤500ms | C>500 W>400 | 1min |
| Critical | Cache Hit | ≥95% | C<90 W<93 | 1min |
| High | Throughput | ≥900 ev/s | C<900 W<945 | 5min |
| High | WAL P99 | <3ms | C>3 W>2.4 | 5min |
| High | Index P99 | <7ms | C>7 W>5.6 | 5min |
| High | Packet Loss | <0.005% | C>0.005 W>0.004 | 5min |
| Medium | Alert Count | <15/h | W>15 C>25 | 15min |
| Medium | Alert Health | 100/100 | W<100 C<90 | 15min |
| Medium | Noise Reduction | ≥80% | W<70 C<60 | 15min |
| Low | Storage Growth | ~805GB/90d | W>1.2× C>1.5× | 30min |
| Low | Field Completeness | 100% | C<100 | 30min |
| Low | Baseline Drift | <5% | W>5 C>10 | 30min |
| Special | IE-AL-001 | C>8.5 W>8.05 Ch>8.0 | 三级 | 1min |

### 11.3 关键命令速查

```bash
# 流量控制
dshb-router gray-pause --target v87-gray-cluster            # 暂停灰度
dshb-router gray-revert --target v87-gray-cluster --to v86  # 回退灰度
dshb-router full-rollback --from v87-gray --to v86          # 全量回滚
dshb-router rollback --dry-run                              # 回滚测试

# HERMES 管道
hermes pipeline-stop --pipeline v87-gray-audit              # 停止审计管道
hermes pipeline-rollback --dry-run                          # 回滚测试

# 告警 & 缓存
curl -X POST http://hermes/alert/{id}/ack                  # 确认告警
curl -X POST http://hermes/cache/refresh                    # 刷新缓存

# 系统状态
curl http://hermes/health                                   # 健康度
curl http://hermes/degradation-level                        # 降级层级
curl http://dshb-router/traffic                             # 流量分布

# 降级控制
curl -X POST http://hermes/degrade --data '{"level":N}'     # L0-L3
```

### 11.4 降级层级速查

| 层级 | 名称 | 触发条件 | 动作 | 恢复 |
|------|------|---------|------|------|
| L0 | 正常 | 默认 | 全功能运行 | — |
| L1 | 限流 | QPS >560 | 限制非关键查询 QPS | QPS <520 持续 5min |
| L2 | 降级 | QPS >700 或 渲染 P99 >150ms | 关闭 AI 面板 (P-001,P-004) + 拓扑面板 (P-002) | QPS <560 持续 10min |
| L3 | 只读 | QPS >800 或 数据延迟 >1000ms | 关闭全部 V87 面板，只保留 V86 | 手动恢复 |

### 11.5 决策流程图

```
灰度启动 T+0 → 观察 4h → ┌─ 🟢 GO ──→ 24h→75% → 48h→100% → 7d→Phase04
                         ├─ 🟡 COND-GO → 维持50% → 再观察4h → 评估
                         └─ 🔴 RED ──→ 15min 全量回滚 → RCA
```

---

## 12. 状态标记

### 12.1 文档状态

| 标记 | 值 |
|------|----|
| `DSHE_L2_PHASE03_GRAY_HANDBOOK_VERSION` | `v1.0.0` |
| `DSHE_L2_PHASE03_GRAY_HANDBOOK_STATUS` | `LOCKED` |
| `DSHE_L2_PHASE03_GRAY_HANDBOOK_BRANCH` | `feature/v87-rc1-g1` |
| `DSHE_L2_PHASE03_GRAY_HANDBOOK_PREV_COMMIT` | `0d9a9d7` |
| `DSHE_L2_PHASE03_GRAY_HANDBOOK_CREATED` | `2027-03-15` |
| `DSHE_L2_PHASE03_GRAY_HANDBOOK_REVIEWED_BY` | `DSHE Lead / DSHB Lead / HERMES Lead / SRE Lead` |

### 12.2 阶段状态

| 标记 | 值 |
|------|----|
| `DSHE_L2_PHASE03_STAGEA_GRAY_PERCENT_START` | `50` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_PERCENT_MAX` | `100` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_OBSERVE_DAYS` | `7` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_TOTAL_PANELS` | `33` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_NEW_PANELS` | `8` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_ALERT_RULES` | `12` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_HERMES_FIELDS` | `5` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_QPS_ESTIMATE` | `560` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_QPS_PROTECTION` | `800` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_STORAGE_ESTIMATE_GB` | `805` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_CACHE_HIT_MIN` | `95` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_RENDER_P99_MAX` | `150` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_QUERY_P99_MAX` | `300` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_DATA_DELAY_MAX` | `500` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_THROUGHPUT_MIN` | `900` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_WAL_P99_MAX` | `3` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_INDEX_P99_MAX` | `7` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_PACKET_LOSS_MAX` | `0.005` |
| `DSHE_L2_PHASE03_STAGEA_GRAY_ROLLBACK_WINDOW` | `15min` |

### 12.3 版本演进

| 版本 | 阶段 | 面板 | 告警规则 | 字段 | 关键事件 |
|------|------|------|---------|------|---------|
| V85 | GA | 17 | — | — | 基线建立 |
| V86 | GA | 25 | 9 | — | 长视图 + 预测 + 事件标记 |
| V87-RC1 P01 | 需求 | 25 (设计 8 新) | 9 (设计 12) | 0 (设计 5) | 需求锁定 + 基线模板 |
| V87-RC1 P02 | 开发+验收 | 33 (开发 8 新) | 12 (迭代) | 5 (集成) | 开发+验收通过 |
| **V87-RC1 P03 StageA** | **灰度观察** | **33 (灰度 50%)** | **12 (灰度)** | **5 (灰度)** | **本手册** |
| V87-RC1 P03 StageB | 全量发布 | 33 (100%) | 12 (全量) | 5 (全量) | 全量发布 |
| V87-RC1 P04 | 稳定性验证 | 33 | 12 | 5 | 7d 稳定性验证 |

### 12.4 下一里程碑

| 里程碑 | 时间 | 条件 | 负责人 |
|--------|------|------|--------|
| M1: 灰度前准备完成 | T-2h | §9.1 清单 24/24 PASS | Phase03 Lead |
| M2: 灰度启动 | T+0 | 灰度路由激活 | DSHB Ops |
| M3: 灰度稳定 (30min) | T+30min | §9.2 清单 18/18 PASS | On-call |
| M4: 灰度评估 | T+4h | §9.4 清单 15/15 → GO/COND-GO/RED | Phase03 Lead |
| M5: 灰度 75% | T+28h | M4 GO + 24h 稳定 | Phase03 Lead |
| M6: 灰度 100% | T+52h | M5 后 24h 稳定 | Phase03 Lead |
| M7: 灰度后观察 7d | T+7d | §9.5 清单 10/10 PASS | Phase03 Lead |
| M8: Phase04 准入 | T+7d | 7d 内无 P0 事件 | VP Engineering |

---

*文档结束*
