# G0 应急预案文档更新 V2.2

| 属性 | 值 |
|------|-----|
| 工单 | DSHB_V86_RC2_G0_JOINT_PRECHECK_CHAOS |
| 子任务 | T3.5 应急预案文档更新 |
| 版本 | V2.3 (基于 V2.2 更新 — 跨团队术语&指标对齐) |
| 日期 | 2026-10-17 |
| 环境 | 预发影子集群（pre-prod-shadow-cluster） |
| 文档类型 | DEP-001 运维手册 + Gate V5 运维手册 |
| 更新内容 | 混沌故障场景(F1-TRIGGER~F5-TRIGGER)、F1-TRIGGER/F2-TRIGGER 应急操作步骤、故障恢复流程、跨团队术语统一(BLOCKED/RECOVERY/ACTIVE)、P99分项阈值(告警500ms/决策1s/刷新5s) |
| 约束 | NO_ZHIJI_API_CALL=FALSE, NO_MODIFY_V85=TRUE, NO_OVERWRITE=TRUE |

---

## 1. 概述

### 1.1 背景

上一轮工单 `DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION` (commit `ba82d04`) 已完成 G0 影子运维文档更新 V2.1，新增 DEP-001 手册 §17-§20 和 Gate 适配 §10-§13。

本轮 T3.2 混沌注入测试 (5/5 PASS) 和 T3.3 F1/F2 应急熔断演练 (2/2 PASS) 已验证全部应急场景。本报告在 V2.1 基础上新增混沌故障场景操作指南、F1/F2 应急操作步骤、故障恢复流程，形成完整的 G0 影子应急预案 V2.2。

### 1.2 更新范围

| 手册 | 章节 | 更新内容 | 变更类型 |
|------|------|----------|----------|
| DEP-001 运维手册 | §21-§24 | 混沌故障场景操作、F1 应急步骤、恢复流程、演练记录 | 新增 |
| Gate V5 运维手册 | §14-§17 | 混沌故障场景操作、F1/F2 应急步骤、回调恢复、演练记录 | 新增 |
| 跨团队应急 | §25 | 三方联合应急流程 | 新增 |
| 附录 | A-D | 演练数据、命令速查、联系人、修订历史 | 新增 |

### 1.3 不变更项

| 手册 | 章节 | 说明 |
|------|------|------|
| DEP-001 运维手册 | §1-§20 (V2.1) | 保留不变 |
| Gate V5 运维手册 | §1-§13 (V2.1) | 保留不变 |

---

## 2. DEP-001 运维手册 V2.2 更新

### 2.1 §21 混沌故障场景操作指南

#### 2.1.1 混沌测试环境配置

| 参数 | 值 | 说明 |
|------|-----|------|
| 混沌工具 | Chaos Mesh V2.3 | 故障注入控制器 |
| 注入命名空间 | shadow-ns | 影子命名空间 |
| 允许注入目标 | dep001, gate-v5, envoy | 仅影子组件 |
| 禁止注入目标 | V85 生产环境组件 | NO_MODIFY_V85=TRUE |
| 默认注入时长 | 120s | 可配置 |
| 最大并发注入 | 1 场景/次 | 避免叠加影响 |

#### 2.1.2 混沌故障场景操作清单

| 故障码 | 命令 | 操作说明 | 预期结果 | 恢复操作 | 严重级别 |
|------|------|----------|----------|----------|----------|
| F1-TRIGGER: DEP 单实例 Kill | `kubectl create chaos pod-kill -n shadow-ns --selector=app=dep001 --pod-number=1 --signal=SIGKILL --duration=120s` | 杀死 DEP 第1个副本 | 熔断器BLOCKED，剩余实例承接 | 自动恢复 (livenessProbe→RECOVERY→ACTIVE) | P0 |
| F2-TRIGGER: 网络时延抖动 | `kubectl create chaos network-latency -n shadow-ns --selector=app=dep001 --latency=500ms --jitter=200ms --offset=10% --interface=eth0 --duration=180s` | 注入网络延迟 | P99 告警触发(阈值500ms) | 自动恢复 (注入过期) | P1 |
| F3-TRIGGER: 端口阻断 | `kubectl create chaos network-delay -n shadow-ns --selector=app=dep001 --interface=eth0 --drop-ratio=100 --port=9090 --duration=90s` | 阻断 DEP 指标端口 | 连接池保护，熔断器BLOCKED | 自动恢复 (注入过期) | P1 |
| F4-TRIGGER: mTLS 证书失效 | `kubectl create chaos cert-expiry -n shadow-ns --selector=app=dep001 --cert-type=client --expire-immediate=true --duration=120s` | 客户端证书过期 | 鉴权拒绝，安全隔离 | 自动恢复 (证书续期) | P2 |
| F5-TRIGGER: Gate 服务下线 | `kubectl create chaos pod-kill -n shadow-ns --selector=app=gate-v5 --pod-number=1 --signal=SIGKILL --duration=150s` | 杀死 Gate 服务 | 回调降级，本地缓冲 | 自动恢复 (K8s 重启) | P1 |

#### 2.1.3 混沌测试操作 SOP

```
步骤 1: 确认预检状态
  └─ 确认 GATE_DECISION=READY
  └─ 确认 DEP_001_STATUS=READY
  └─ 确认 SHADOW_ENV_STATUS=READY

步骤 2: 记录基线指标
  └─ QPS, P50/P95/P99 延迟
  └─ 错误率, mTLS 握手率
  └─ 指标采集率, 告警数量

步骤 3: 执行混沌注入
  └─ 选择场景 (F1-TRIGGER~F5-TRIGGER)
  └─ 执行注入命令
  └─ 记录注入时间

步骤 4: 观测指标
  └─ 监控熔断器状态
  └─ 监控延迟/错误率/QPS
  └─ 监控 HERMES 审计事件
  └─ 监控 DSHE 大盘状态
  └─ 确认 V85 零影响

步骤 5: 验证恢复
  └─ 确认故障恢复 (自动/手动)
  └─ 确认指标回归基线
  └─ 确认状态同步 (Gate/HERMES/DSHE)

步骤 6: 记录结果
  └─ 记录场景结果 (PASS/FAIL)
  └─ 记录发现项
  └─ 更新演练记录 (§24)
```

#### 2.1.4 混沌测试安全检查清单

| # | 检查项 | 状态 | 说明 |
|---|--------|------|------|
| 1 | 注入目标确认为影子环境 | □ | 确认 selector 正确 |
| 2 | V85 生产环境未受影响 | □ | 确认 V85 QPS偏差<0.01% / P99偏差<0.01ms(告警阈值500ms/决策阈值1s/刷新阈值5s) |
| 4 | 基线指标已记录 | □ | QPS/延迟/错误率 |
| 5 | HERMES 审计已确认正常 | □ | 确认 WAL 写入正常 |
| 6 | DSHE 大盘已确认正常 | □ | 确认面板刷新正常 |
| 7 | On-call 通知渠道已确认 | □ | 确认电话/SMS/邮件可达 |
| 8 | 注入时长已设置 (≤180s) | □ | 避免过长影响 |
| 9 | 注入场景唯一 (未叠加) | □ | 确认仅 1 场景运行中 |
| 10 | 恢复机制已确认 | □ | 确认自动恢复条件 |

### 2.2 §22 F1-TRIGGER 应急操作步骤

#### 2.2.1 F1 故障定义

| 属性 | 值 |
|------|-----|
| 故障代号 | F1-TRIGGER |
| 故障描述 | DEP-001 服务完全不可用 (全部副本不可达) |
| 优先级 | F1 (最高) |
| 影响范围 | G0 影子全部流量 |
| 响应时间要求 | <5min |
| 恢复时间目标 | <30min |

#### 2.2.2 F1 应急操作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    F1 应急操作流程                            │
└─────────────────────────────────────────────────────────────┘

Phase 1: 故障检测 (T+0s ~ T+5s)
┌─────────────────────────────────────────────────────────────┐
│ 步骤 1.1: 确认故障                                            │
│   ├─ 检查 DEP 健康状态: kubectl get pods -n shadow-ns        │
│   ├─ 检查 livenessProbe: kubectl describe pod                │
│   ├─ 检查 DEP 指标: kubectl port-forward dep001 9090         │
│   └─ 确认故障类型: 进程挂/端口阻断/网络不可达                  │
│                                                              │
│ 步骤 1.2: 确认 V85 影响                                       │
│   ├─ 检查 V85 QPS: 确认偏差 <0.01%                            │
│   ├─ 检查 V85 P99: 确认偏差 <0.01ms                          │
│   ├─ 检查 V85 错误率: 确认偏差 <0.001%                        │
│   └─ 确认 V85 零影响 ✓                                       │
│                                                              │
│ 步骤 1.3: 通知相关人员                                        │
│   ├─ HERMES 自动通知 On-call                                 │
│   ├─ 确认 HERMES 审计事件: EVT-F1-001                        │
│   └─ 确认 DSHE 大盘状态: NOT_READY                           │
└─────────────────────────────────────────────────────────────┘

Phase 2: 应急动作 (T+10s ~ T+30s)
┌─────────────────────────────────────────────────────────────┐
│ 步骤 2.1: 切断镜像流量                                        │
│   ├─ 命令: kubectl edit configmap dep001-config -n shadow-ns │
│   ├─ 设置: sampling_rate=0                                   │
│   ├─ 验证: kubectl get configmap -o yaml                     │
│   └─ 确认: Envoy FilterChain 热加载 ✓                       │
│                                                              │
│ 步骤 2.2: DEP 巡检停止                                        │
│   ├─ 命令: curl -X POST http://dep001:9090/admin/stop       │
│   ├─ 或: kubectl exec dep001 -- systemctl stop dep001-probe │
│   ├─ 验证: curl http://dep001:9090/healthz → 503            │
│   └─ 确认: 巡检状态 STOPPED ✓                                │
│                                                              │
│ 步骤 2.3: Gate 状态切换                                       │
│   ├─ 自动: Gate 检测到 DEP 不可用 → NOT_READY                │
│   ├─ 验证: curl http://gate-v5:8443/status                   │
│   ├─ 确认: NOT_READY ✓                                       │
│   └─ 确认: 决策引擎降级 (HOLD) ✓                             │
│                                                              │
│ 步骤 2.4: HERMES ROLLBACK                                    │
│   ├─ 自动: HERMES 决策器收到 NOT_READY → ROLLBACK            │
│   ├─ 验证: HERMES 审计事件 EVT-F1-ROLLBACK-001              │
│   ├─ 确认: 采样率 0% ✓                                       │
│   └─ 确认: DSHE 大盘 NOT_READY ✓                             │
└─────────────────────────────────────────────────────────────┘

Phase 3: 故障修复 (T+600s)
┌─────────────────────────────────────────────────────────────┐
│ 步骤 3.1: 诊断 DEP 不可用原因                                 │
│   ├─ 检查 POD 状态: kubectl get pods -n shadow-ns            │
│   ├─ 检查日志: kubectl logs -l app=dep001                    │
│   ├─ 检查事件: kubectl get events -n shadow-ns               │
│   ├─ 检查资源: kubectl top pods -n shadow-ns                 │
│   └─ 确认根因: 资源不足/OOM/代码错误/依赖故障                 │
│                                                              │
│ 步骤 3.2: 修复 DEP                                           │
│   ├─ 资源不足: kubectl scale deployment dep001 --replicas=3 │
│   ├─ OOM: 调整 memory limit                                  │
│   ├─ 代码错误: 回滚至上一版本                                  │
│   └─ 依赖故障: 等待依赖恢复                                  │
│                                                              │
│ 步骤 3.3: 确认 DEP 恢复                                       │
│   ├─ kubectl get pods -n shadow-ns → 3/3 Running            │
│   ├─ curl http://dep001:9090/healthz → 200 OK               │
│   └─ 确认: DEP 完全恢复 ✓                                    │
└─────────────────────────────────────────────────────────────┘

Phase 4: 逐步恢复 (T+630s ~ T+725s)
┌─────────────────────────────────────────────────────────────┐
│ 步骤 4.1: 恢复检查                                            │
│   ├─ DEP 健康检查: 3 次连续 200 OK                            │
│   ├─ DEP 指标恢复: 12 项指标全部上报                          │
│   └─ 确认: 恢复检查通过 ✓                                    │
│                                                              │
│ 步骤 4.2: Gate 状态: NOT_READY → OBSERVE                     │
│   ├─ 自动切换 (T+610s)                                       │
│   ├─ 验证: curl http://gate-v5:8443/status → OBSERVE        │
│   └─ 确认: 观察期启动 ✓                                      │
│                                                              │
│ 步骤 4.3: HERMES 决策: ROLLBACK → ADVANCE                    │
│   ├─ 自动切换 (T+615s)                                       │
│   ├─ 采样率: 0% → 1%                                         │
│   └─ 确认: HERMES 审计事件 EVT-F1-ADVANCE-001 ✓             │
│                                                              │
│ 步骤 4.4: 采样率逐步增加                                      │
│   ├─ T+630s: 1% → 5% (Envoy FilterChain 更新)               │
│   ├─ T+660s: 5% → 10% (Envoy FilterChain 更新)              │
│   ├─ 验证: kubectl get configmap dep001-config -o yaml      │
│   └─ 确认: sampling_rate=10 ✓                                │
│                                                              │
│ 步骤 4.5: DEP 巡检: STOPPED → RUNNING                        │
│   ├─ 命令: curl -X POST http://dep001:9090/admin/start      │
│   ├─ 或: kubectl exec dep001 -- systemctl start dep001-probe │
│   └─ 确认: 巡检状态 RUNNING ✓                                │
│                                                              │
│ 步骤 4.6: Gate 状态: OBSERVE → READY                          │
│   ├─ 自动切换 (T+700s, 观察期 30s)                           │
│   └─ 确认: Gate 状态 READY ✓                                 │
│                                                              │
│ 步骤 4.7: HERMES 决策: ADVANCE → COMPLETE                    │
│   ├─ 自动切换 (T+720s)                                       │
│   └─ 确认: HERMES 审计事件 EVT-F1-COMPLETE-001 ✓            │
│                                                              │
│ 步骤 4.8: DSHE 大盘: WARN → READY                            │
│   ├─ 自动切换 (T+725s)                                       │
│   └─ 确认: 大盘状态 READY ✓                                  │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2.3 F1 应急命令速查

| # | 操作 | 命令 | 说明 |
|---|------|------|------|
| 1 | 检查 DEP 状态 | `kubectl get pods -n shadow-ns -l app=dep001` | 确认 POD 状态 |
| 2 | 检查 DEP 健康 | `curl http://dep001:9090/healthz` | 健康检查 |
| 3 | 切断镜像流量 | `kubectl edit configmap dep001-config -n shadow-ns` | 设置 sampling_rate=0 |
| 4 | DEP 巡检停止 | `curl -X POST http://dep001:9090/admin/stop` | 停止巡检 |
| 5 | 检查 Gate 状态 | `curl http://gate-v5:8443/status` | 确认 NOT_READY |
| 6 | 检查 HERMES 审计 | `curl http://hermes:8888/audit/events?tag=F1` | 查看事件 |
| 7 | 检查 DSHE 状态 | `curl http://dshe:3000/api/status` | 确认 NOT_READY |
| 8 | DEP 恢复 | `kubectl scale deployment dep001 --replicas=3` | 扩缩容 |
| 9 | 恢复检查 | `kubectl logs -l app=dep001 --tail=50` | 查看日志 |
| 10 | 采样率恢复 | `kubectl edit configmap dep001-config -n shadow-ns` | 逐步恢复采样率 |
| 11 | DEP 巡检恢复 | `curl -X POST http://dep001:9090/admin/start` | 恢复巡检 |
| 12 | 确认恢复 | `curl http://gate-v5:8443/status` | 确认 READY |

### 2.3 §23 故障恢复流程

#### 2.3.1 恢复流程总览

| 恢复阶段 | 时间 | 关键动作 | 验证 |
|----------|------|----------|------|
| 故障检测 | T+0~5s | livenessProbe 失败检测 | 故障确认 |
| 应急动作 | T+10~30s | 切断镜像+巡检停止+Gate切换+HERMES ROLLBACK | 应急链路闭环 |
| 故障修复 | T+600s | DEP 修复 (手动/自动) | DEP 恢复 |
| 逐步恢复 | T+630~725s | 采样率 0→10%+巡检恢复+Gate READY | 全部恢复 |
| 恢复确认 | T+725s | 状态同步确认 | 三方一致 |

#### 2.3.2 恢复检查清单

| # | 检查项 | 命令/方法 | 通过标准 | 状态 |
|---|--------|-----------|----------|------|
| 1 | DEP 健康 | `curl http://dep001:9090/healthz` | 200 OK | □ |
| 2 | DEP 指标恢复 | `curl http://dep001:9090/metrics` | 12 项指标 | □ |
| 3 | 采样率恢复 | `kubectl get configmap dep001-config -o yaml` | sampling_rate=10 | □ |
| 4 | Envoy 热加载 | `curl http://envoy:8080/config_dump` | 配置生效 | □ |
| 5 | DEP 巡检恢复 | `curl http://dep001:9090/status` | RUNNING | □ |
| 6 | Gate 状态 | `curl http://gate-v5:8443/status` | READY | □ |
| 7 | HERMES 审计 | `curl http://hermes:8888/audit/events?tag=F1` | 事件完整 | □ |
| 8 | DSHE 大盘 | `curl http://dshe:3000/api/status` | READY | □ |
| 9 | V85 零影响 | 检查 V85 QPS/P99 | 偏差 <0.01% | □ |
| 10 | 跨团队一致性 | 四方状态对比 | 一致 | □ |

### 2.4 §24 演练记录

#### 2.4.1 混沌注入测试记录

| 日期 | 故障码 | 执行时间 | 执行者 | 结果 | 发现项 |
|------|--------|----------|--------|------|--------|
| 2026-10-17 | F1-TRIGGER DEP 单实例 Kill | 15:00 | DSHB | PASS | — |
| 2026-10-17 | F2-TRIGGER 网络时延抖动 | 15:10 | DSHB | PASS | P1-001: 指标丢弃 |
| 2026-10-17 | F3-TRIGGER 端口阻断 | 15:20 | DSHB | PASS | P2-005: 指标停止 |
| 2026-10-17 | F4-TRIGGER mTLS 证书失效 | 15:30 | DSHB | PASS | — |
| 2026-10-17 | F5-TRIGGER Gate 服务下线 | 15:40 | DSHB | PASS | P2-001: flush 延迟 |

#### 2.4.2 F1-TRIGGER/F2-TRIGGER 应急演练记录

| 日期 | 故障码 | 执行时间 | 执行者 | 结果 | 发现项 |
|------|--------|----------|--------|------|--------|
| 2026-10-17 | F1-TRIGGER DEP 不可用 | 16:00 | DSHB | PASS | P1-002: 恢复时间长, P1-004: 告警延迟 |
| 2026-10-17 | F2-TRIGGER CRITICAL 爆发 | 16:20 | DSHB | PASS | P1-003: 动作延迟, P2-003: 去重延迟 |

#### 2.4.3 演练统计

| 指标 | 值 |
|------|-----|
| 混沌测试场景数 | 5 |
| 混沌测试通过 | 5 (100%) |
| 应急演练场景数 | 2 |
| 应急演练通过 | 2 (100%) |
| 发现 P0 | 0 |
| 发现 P1 | 4 |
| 发现 P2 | 5 |
| 发现待确认 | 3 |
| V85 影响 | 0% |

---

## 3. Gate V5 运维手册 V2.2 更新

### 3.1 §14 混沌故障场景操作指南

#### 3.1.1 Gate 混沌场景操作清单

| 故障码 | 命令 | 操作说明 | 预期结果 | 恢复操作 |
|------|------|----------|----------|----------|
| F5-TRIGGER: Gate 服务下线 | `kubectl create chaos pod-kill -n shadow-ns --selector=app=gate-v5 --pod-number=1 --signal=SIGKILL --duration=150s` | 杀死 Gate 服务 | 回调降级，本地缓冲 | 自动恢复 (K8s 重启) |
| Gate 网络隔离 | `kubectl create chaos network-delay -n shadow-ns --selector=app=gate-v5 --interface=eth0 --drop-ratio=100 --port=8443 --duration=120s` | 阻断 Gate 回调端口 | 回调超时，本地缓冲 | 自动恢复 (注入过期) |
| Gate 证书失效 | `kubectl create chaos cert-expiry -n shadow-ns --selector=app=gate-v5 --cert-type=server --expire-immediate=true --duration=120s` | Gate 服务端证书过期 | 回调 401 拒绝 | 自动恢复 (证书续期) |
| Gate 配置错误 | `kubectl create chaos config-mutation -n shadow-ns --selector=app=gate-v5 --key=decision_threshold --value=999 --duration=60s` | 修改决策阈值 | 决策不触发 | 自动恢复 (注入过期) |

#### 3.1.2 Gate 混沌测试 SOP

```
步骤 1: 确认 Gate 状态
  └─ curl http://gate-v5:8443/status → READY
  └─ curl http://gate-v5:8443/healthz → 200 OK
  └─ 确认 Gate 状态 READY ✓

步骤 2: 记录基线指标
  └─ gate_decision_count
  └─ gate_callback_latency (P50/P95/P99)
  └─ gate_state_transitions
  └─ gate_error_rate

步骤 3: 执行混沌注入
  └─ 选择场景 (F5-TRIGGER/Gate 网络隔离/Gate 证书失效/Gate 配置错误)
  └─ 执行注入命令
  └─ 记录注入时间

步骤 4: 观测指标
  └─ 监控 /healthz → 503
  └─ 监控 /readyz → 503
  └─ 监控回调端点 → 503 + 本地缓冲
  └─ 监控状态切换 → READY → NOT_READY
  └─ 确认事件缓冲数量
  └─ 确认 HERMES 审计延迟上报

步骤 5: 验证恢复
  └─ 确认 Gate 服务恢复 (K8s 自动重启)
  └─ 确认状态切换 → NOT_READY → READY
  └─ 确认事件 flush (50 事件全部上报 HERMES)
  └─ 确认指标回归基线

步骤 6: 记录结果
  └─ 记录场景结果 (PASS/FAIL)
  └─ 记录发现项
```

#### 3.1.3 Gate 混沌测试安全检查清单

| # | 检查项 | 状态 | 说明 |
|---|--------|------|------|
| 1 | 注入目标确认为 Gate 服务 | □ | 确认 selector=app=gate-v5 |
| 2 | V85 生产环境未受影响 | □ | 确认 V85 QPS偏差<0.01% / P99偏差<0.01ms(告警阈值500ms/决策阈值1s/刷新阈值5s) |
| 3 | Gate 状态已记录 (READY) | □ | 确认基线 |
| 4 | 本地缓冲机制已确认 | □ | 确认事件缓冲上限 (50) |
| 5 | HERMES 审计已确认正常 | □ | 确认 WAL 写入正常 |
| 6 | 注入时长已设置 (≤180s) | □ | 避免过长影响 |
| 7 | 恢复机制已确认 (K8s 自动重启) | □ | 确认 livenessProbe 配置 |

### 3.2 §15 F1-TRIGGER/F2-TRIGGER 应急操作步骤

#### 3.2.1 F1-TRIGGER 应急操作 (Gate 视角)

| 步骤 | 操作 | 命令/方法 | 说明 |
|------|------|-----------|------|
| 1 | 确认故障 | `curl http://gate-v5:8443/status` | 确认 NOT_READY |
| 2 | 确认决策 | 检查决策引擎状态 | 确认 HOLD 模式 |
| 3 | 确认回调 | 检查回调端点状态 | 确认降级模式 |
| 4 | 确认事件缓冲 | 检查本地缓冲数量 | 确认事件无丢失 |
| 5 | 确认 HERMES 通知 | 检查 HERMES 审计 | 确认 ROLLBACK 事件 |
| 6 | 确认 DSHE 通知 | 检查 DSHE 大盘状态 | 确认 NOT_READY |
| 7 | 等待恢复 | 等待 DEP 恢复 | 自动切换 |
| 8 | 确认恢复 | `curl http://gate-v5:8443/status` | 确认 READY |

#### 3.2.2 F2-TRIGGER 应急操作 (Gate 视角)

| 步骤 | 操作 | 命令/方法 | 说明 |
|------|------|-----------|------|
| 1 | 确认告警 | 检查 CRITICAL 告警数量 | 确认告警爆发 |
| 2 | 确认熔断 | 检查熔断器状态 | 确认BLOCKED |
| 3 | 确认状态 | `curl http://gate-v5:8443/status` | 确认 WARN |
| 4 | 确认决策 | 检查决策引擎状态 | 确认 OBSERVE |
| 5 | 确认 HERMES 通知 | 检查 HERMES 审计 | 确认 OBSERVE 事件 |
| 6 | 确认 DSHE 通知 | 检查 DSHE 大盘状态 | 确认 WARN |
| 7 | 等待告警恢复 | 等待告警恢复 | 自动切换 |
| 8 | 确认恢复 | `curl http://gate-v5:8443/status` | 确认 READY |

#### 3.2.3 Gate 应急命令速查

| # | 操作 | 命令 | 说明 |
|---|------|------|------|
| 1 | 检查 Gate 状态 | `curl http://gate-v5:8443/status` | READY/WARN/NOT_READY |
| 2 | 检查健康 | `curl http://gate-v5:8443/healthz` | 200/503 |
| 3 | 检查就绪 | `curl http://gate-v5:8443/readyz` | 200/503 |
| 4 | 检查回调 | `curl http://gate-v5:8443/callback/decision` | 决策回调 |
| 5 | 检查事件缓冲 | `curl http://gate-v5:8443/admin/buffer` | 本地缓冲数量 |
| 6 | 检查审计 | `curl http://hermes:8888/audit/events?tag=gate` | Gate 相关审计 |
| 7 | 检查决策历史 | `curl http://gate-v5:8443/admin/decisions` | 决策历史 |
| 8 | 强制状态切换 | `curl -X POST http://gate-v5:8443/admin/state?state=READY` | 手动切换 |
| 9 | 强制 flush 缓冲 | `curl -X POST http://gate-v5:8443/admin/flush` | 手动 flush |

### 3.3 §16 回调恢复流程

#### 3.3.1 回调恢复流程 (F5-TRIGGER 场景)

```
Phase 1: Gate 故障检测 (T+0~5s)
┌─────────────────────────────────────────────────────────────┐
│ 步骤 1.1: 健康检查失败                                        │
│   ├─ /healthz → 503                                          │
│   ├─ /readyz → 503                                           │
│   └─ 状态切换: READY → NOT_READY (T+5s)                      │
│                                                              │
│ 步骤 1.2: 回调降级                                            │
│   ├─ 回调端点 → 503 + 本地缓冲                               │
│   ├─ 事件写入本地缓冲 (50 事件上限)                           │
│   └─ 决策引擎降级: HOLD 模式                                  │
└─────────────────────────────────────────────────────────────┘

Phase 2: Gate 自动恢复 (T+45s)
┌─────────────────────────────────────────────────────────────┐
│ 步骤 2.1: K8s 自动重启                                        │
│   ├─ livenessProbe 失败 → K8s 重启 POD                       │
│   ├─ 重启时间: 45s (默认)                                     │
│   └─ 确认: POD Running ✓                                     │
│                                                              │
│ 步骤 2.2: 健康检查恢复                                        │
│   ├─ /healthz → 200 OK (T+50s)                               │
│   ├─ /readyz → 200 OK (T+55s)                                │
│   └─ 状态切换: NOT_READY → OBSERVE (T+60s)                   │
└─────────────────────────────────────────────────────────────┘

Phase 3: 事件 Flush (T+60~65s)
┌─────────────────────────────────────────────────────────────┐
│ 步骤 3.1: 缓冲事件 flush                                     │
│   ├─ 50 事件 → HERMES (T+65s)                                │
│   ├─ flush 时间: 5s                                           │
│   └─ 确认: HERMES 审计事件 EVT-F5-TRIGGER-FLUSH-001~050 ✓           │
│                                                              │
│ 步骤 3.2: 状态恢复                                            │
│   ├─ Gate 状态: OBSERVE → READY (T+90s)                      │
│   ├─ 决策引擎: HOLD → NORMAL                                  │
│   └─ 确认: 回调恢复 ✓                                         │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.2 回调恢复检查清单

| # | 检查项 | 命令/方法 | 通过标准 | 状态 |
|---|--------|-----------|----------|------|
| 1 | Gate POD 恢复 | `kubectl get pods -l app=gate-v5` | Running | □ |
| 2 | 健康检查恢复 | `curl http://gate-v5:8443/healthz` | 200 OK | □ |
| 3 | 就绪检查恢复 | `curl http://gate-v5:8443/readyz` | 200 OK | □ |
| 4 | 状态切换 | `curl http://gate-v5:8443/status` | READY | □ |
| 5 | 事件 flush | `curl http://gate-v5:8443/admin/buffer` | 0 缓冲 | □ |
| 6 | HERMES 审计 | `curl http://hermes:8888/audit/events?tag=F5-TRIGGER` | 50 事件 | □ |
| 7 | 决策引擎恢复 | 检查决策历史 | NORMAL 模式 | □ |
| 8 | DSHE 同步 | `curl http://dshe:3000/api/status` | READY | □ |

### 3.4 §17 演练记录

#### 3.4.1 Gate 混沌注入测试记录

| 日期 | 故障码 | 执行时间 | 执行者 | 结果 | 发现项 |
|------|--------|----------|--------|------|--------|
| 2026-10-17 | F5-TRIGGER Gate 服务下线 | 15:40 | DSHB | PASS | P2-001: flush 延迟 |

#### 3.4.2 Gate 应急参与记录

| 日期 | 场景 | Gate 状态变化 | 决策 | 结果 |
|------|------|--------------|------|------|
| 2026-10-17 | F1 DEP 不可用 | READY→NOT_READY→OBSERVE→READY | ROLLBACK→ADVANCE→COMPLETE | PASS |
| 2026-10-17 | F2 CRITICAL 爆发 | READY→WARN→OBSERVE→READY | OBSERVE→ADVANCE→COMPLETE | PASS |

---

## 4. §25 跨团队联合应急流程

### 4.1 联合应急角色分工

| 角色 | 团队 | 职责 | 工具 |
|------|------|------|------|
| 应急指挥 | DSHB | 统筹协调，确认故障级别，通知相关人员 | — |
| DEP 负责人 | DEP | DEP 故障诊断与修复 | kubectl, dep001 CLI |
| Gate 负责人 | Gate | Gate 状态确认与恢复 | curl, gate CLI |
| HERMES 负责人 | HERMES | 审计事件确认与决策验证 | HERMES CLI |
| DSHE 负责人 | DSHE | 大盘状态确认与通知 | DSHE CLI |
| On-call | 值班 | 接警与初步响应 | Alertmanager |

### 4.2 联合应急流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    联合应急流程                               │
└─────────────────────────────────────────────────────────────┘

步骤 1: 故障检测 (自动)
  ├─ Alertmanager 检测告警
  ├─ livenessProbe 检测故障
  └─ 指标异常检测

步骤 2: 故障通知 (自动)
  ├─ Alertmanager → HERMES (事件上报)
  ├─ HERMES → DSHE (状态同步)
  ├─ HERMES → On-call (通知)
  └─ DSHE → 应急指挥 (通知)

步骤 3: 故障确认 (手动)
  ├─ On-call: 确认故障级别 (F1-TRIGGER/F2-TRIGGER/F3-TRIGGER)
  ├─ 应急指挥: 确认应急级别
  └─ 通知: 相关团队负责人

步骤 4: 应急动作 (自动+手动)
  ├─ 自动: 切断镜像流量 (Envoy)
  ├─ 自动: DEP 巡检停止 (probe)
  ├─ 自动: Gate 状态切换 (Gate)
  ├─ 自动: HERMES 决策 (HERMES)
  ├─ 手动: DEP 修复 (DEP 负责人)
  └─ 手动: 确认恢复 (应急指挥)

步骤 5: 故障修复 (手动)
  ├─ DEP 负责人: 诊断+修复
  ├─ 应急指挥: 确认修复
  └─ 通知: 开始恢复流程

步骤 6: 逐步恢复 (自动)
  ├─ 自动: Gate NOT_READY → OBSERVE
  ├─ 自动: HERMES ROLLBACK → ADVANCE
  ├─ 自动: 采样率 0% → 10%
  ├─ 自动: DEP 巡检 STOPPED → RUNNING
  ├─ 自动: Gate OBSERVE → READY
  └─ 自动: DSHE NOT_READY → READY

步骤 7: 恢复确认 (手动)
  ├─ 应急指挥: 确认全部恢复
  ├─ 各团队: 确认各自组件恢复
  └─ 记录: 演练记录更新

步骤 8: 事后复盘 (手动)
  ├─ 应急指挥: 组织复盘
  ├─ 各团队: 提交发现项
  └─ 更新: 风险清单 + 应急预案
```

### 4.3 联合应急沟通矩阵

| 事件 | 发送方 | 接收方 | 渠道 | 延迟 |
|------|--------|--------|------|------|
| 故障检测 | Alertmanager | HERMES | HTTP | <1s |
| 故障通知 | HERMES | On-call | 电话+SMS+邮件 | <30s |
| 状态同步 | HERMES | DSHE | HTTP | <5s |
| 应急指令 | 应急指挥 | 各团队 | 电话+IM | <60s |
| 修复确认 | DEP 负责人 | 应急指挥 | IM | <60s |
| 恢复通知 | DSHE | 各团队 | HTTP | <5s |
| 复盘通知 | 应急指挥 | 各团队 | IM | <30min |

### 4.4 联合应急演练流程

| 阶段 | 操作 | 时间 | 参与方 |
|------|------|------|--------|
| 桌面推演 | 讨论流程+确认角色 | 30min | 全部 |
| 故障模拟 | 注入 F1-TRIGGER/F2-TRIGGER 故障 | 10min | DSHB |
| 检测确认 | 确认故障检测 | 5min | DEP+Gate+HERMES+DSHE |
| 应急动作 | 执行应急流程 | 30min | 全部 |
| 故障修复 | 修复 DEP/Gate | 30min | DEP+Gate |
| 逐步恢复 | 逐步恢复流程 | 30min | 全部 |
| 恢复确认 | 确认全部恢复 | 10min | 全部 |
| 事后复盘 | 讨论+记录 | 30min | 全部 |
| **合计** | — | **185min** | — |

---

## 5. 附录

### 5.1 A. 演练数据汇总

| 故障码 | 注入时间 | 检测时间 | 应急启动 | 全链路闭环 | 恢复时间 | 结果 |
|--------|----------|----------|----------|------------|----------|------|
| F1-TRIGGER DEP Kill | 15:00 | 5s | 10s | 18s | 45s | PASS |
| F2-TRIGGER 网络抖动 | 15:10 | 8s | 10s | 18s | 22s | PASS |
| F3-TRIGGER 端口阻断 | 15:20 | 0s | 2s | 5s | 92s | PASS |
| F4-TRIGGER mTLS 失效 | 15:30 | 0s | 5s | 10s | 123s | PASS |
| F5-TRIGGER Gate 下线 | 15:40 | 3s | 5s | 10s | 60s | PASS |
| F1-TRIGGER DEP 不可用 | 16:00 | 5s | 10s | 18s | 725s | PASS |
| F2-TRIGGER CRITICAL 爆发 | 16:20 | 8s | 10s | 18s | 375s | PASS |

### 5.2 B. 命令速查表

| # | 命令 | 用途 | 环境 |
|---|------|------|------|
| 1 | `kubectl get pods -n shadow-ns` | 查看影子 POD | shadow-ns |
| 2 | `kubectl get pods -n shadow-ns -l app=dep001` | 查看 DEP POD | shadow-ns |
| 3 | `kubectl get pods -n shadow-ns -l app=gate-v5` | 查看 Gate POD | shadow-ns |
| 4 | `curl http://dep001:9090/healthz` | DEP 健康检查 | shadow-ns |
| 5 | `curl http://gate-v5:8443/status` | Gate 状态 | shadow-ns |
| 6 | `curl http://gate-v5:8443/healthz` | Gate 健康 | shadow-ns |
| 7 | `curl http://hermes:8888/audit/events` | HERMES 审计 | shadow-ns |
| 8 | `curl http://dshe:3000/api/status` | DSHE 状态 | shadow-ns |
| 9 | `kubectl edit configmap dep001-config -n shadow-ns` | 修改采样率 | shadow-ns |
| 10 | `kubectl scale deployment dep001 --replicas=3` | DEP 扩缩容 | shadow-ns |
| 11 | `kubectl logs -l app=dep001 --tail=50` | DEP 日志 | shadow-ns |
| 12 | `kubectl logs -l app=gate-v5 --tail=50` | Gate 日志 | shadow-ns |
| 13 | `kubectl get events -n shadow-ns --sort-by='.lastTimestamp'` | 影子事件 | shadow-ns |
| 14 | `kubectl create chaos pod-kill ...` | 混沌注入 | shadow-ns |
| 15 | `kubectl delete chaos <name> -n shadow-ns` | 删除混沌 | shadow-ns |

### 5.3 C. 联系人

| 角色 | 联系人 | 电话 | IM | 备注 |
|------|--------|------|-----|------|
| DSHB 负责人 | — | — | — | 应急指挥 |
| DEP 负责人 | — | — | — | DEP 故障诊断 |
| Gate 负责人 | — | — | — | Gate 状态确认 |
| HERMES 负责人 | — | — | — | 审计事件确认 |
| DSHE 负责人 | — | — | — | 大盘状态确认 |
| On-call | — | — | — | 值班 |

### 5.4 D. 修订历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| V2.3 | 2026-10-17 | 跨团队术语&指标对齐: 故障码C1-C5→F1-TRIGGER~F5-TRIGGER, 熔断术语CLOSED→ACTIVE/OPEN→BLOCKED/HALF_OPEN→RECOVERY, P99分项阈值(告警500ms/决策1s/刷新5s), 审计事件ID更新, DSHE D-01/D-02/D-04/D-06/D-07对齐 | DSHB |
| V2.2 | 2026-10-17 | 新增混沌故障场景§21-§17, F1/F2应急步骤§22-§16, 恢复流程§23-§16, 演练记录§24-§17, 跨团队应急§25, 附录A-D | DSHB |
| V2.1 | 2026-10-17 | DEP-001手册§17-§20, Gate适配§10-§13, 新增5章节, 12指标6告警4应急预案 | DSHB |
| V2.0 | 2026-10-15 | 初始版本 | DSHB |

### 5.5 约束合规清单

| 约束 | 值 | 状态 | 验证 |
|------|-----|------|------|
| NO_ZHIJI_API_CALL=FALSE | 未调用知几 API | ✅ | 演练日志确认 |
| NO_MODIFY_V85=TRUE | V85 零影响 | ✅ | QPS/P99 偏差 0.00% |
| NO_OVERWRITE=TRUE | V2.1 保留, V2.2 新增章节 | ✅ | 文件列表确认 |
| BRANCH_LOCKED=TRUE | 提交至 origin/feature/v85-chart-template | ✅ | git log 确认 |

### 5.6 应急预案文档 MD5

| 报告 | MD5 | 大小 |
|------|-----|------|
| v86_rc2_dshb_g0_emergency_plan_update.md | `(待计算)` | ~32,000 B |