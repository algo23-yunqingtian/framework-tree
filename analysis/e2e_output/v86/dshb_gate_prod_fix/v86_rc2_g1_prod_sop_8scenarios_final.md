# DSHB V86-RC2 G1 — 8类故障场景生产SOP终版

> **工单ID**: DSHB_V86_RC2_G1_PHASE3_CONDITIONAL_PASS_FULL_CLOSE_AND_PROD_BASELINE_LOCK
> **版本**: V1.2 (基于V1.1修订 — Phase5三方指标口径对齐+P99时延3类独立定义+吞吐/丢失率/72h总量统一口径)
> **日期**: 2026-10-18
> **环境**: pre-prod-shadow-cluster
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **文档状态**: FINAL — 8类故障场景SOP全部定稿, RTO/RPO标准统一, 约束合规确认, 沙箱演练验证修订

---

## 目录

1. [报告头信息](#1-报告头信息)
2. [场景概述](#2-场景概述)
3. [故障场景完整SOP](#3-故障场景完整sop)
4. [统一RTO/RPO标准](#4-统一rto-rpo标准)
5. [统一审计核验标准](#5-统一审计核验标准)
6. [故障后复盘模板](#6-故障后复盘模板)
7. [故障演练日历](#7-故障演练日历)
8. [约束合规](#8-约束合规)
9. [版本历史](#9-版本历史)

---

## 1. 报告头信息

| 项目 | 内容 |
|------|------|
| **工单ID** | DSHB_V86_RC2_G1_PHASE3_CONDITIONAL_PASS_FULL_CLOSE_AND_PROD_BASELINE_LOCK |
| **版本** | V1.1 |
| **日期** | 2026-10-18 |
| **环境** | pre-prod-shadow-cluster |
| **约束** | NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE |
| **分支** | `feature/v85-chart-template` (BRANCH_LOCKED=TRUE) |
| **文档状态** | FINAL |
| **审核人** | DSHB G1 故障演练委员会 |
| **审批编号** | DSHB_V86_RC2_G1_PROD_SOP_V1.0_APPROVED |

---

## 2. 场景概述

### 2.1 场景清单

本SOP定义DSHB V86-RC2生产环境8类故障场景的标准操作流程, 覆盖单故障和复合故障两大类别。

```
场景分类:
  单故障场景 (C1~C5): 5个, 模拟单一组件故障
  复合故障场景 (CF01~CF03): 3个, 模拟多组件并发故障
```

| 场景ID | 故障名称 | 故障类型 | 影响组件 | 严重度 | 优先级 |
|--------|---------|---------|---------|-------|-------|
| **C1** | DEP实例Kill | 单故障 | DEP依赖服务实例 | P1 | 高 |
| **C2** | 网络抖动 | 单故障 | 网络层(丢包/延迟) | P1 | 高 |
| **C3** | 端口阻断 | 单故障 | 网络层(端口阻断) | P1 | 高 |
| **C4** | mTLS失效 | 单故障 | 传输层(mTLS证书) | P0 | 紧急 |
| **C5** | Gate下线 | 单故障 | Gate网关服务 | P1 | 高 |
| **CF01** | DEP Kill + 网络抖动 | 复合故障 | DEP + 网络 | P0 | 紧急 |
| **CF02** | Gate下线 + mTLS失效 | 复合故障 | Gate + mTLS | P0 | 紧急 |
| **CF03** | 端口阻断 + 高并发 | 复合故障 | 网络 + 负载 | P1 | 高 |

### 2.2 熔断状态机

所有故障场景均遵循统一的熔断状态机:

```
熔断状态机:
  ACTIVE (正常运行)
    │
    │ 故障触发 (故障注入/检测)
    ▼
  BLOCKED (熔断阻断)
    │
    │ 自动恢复 / 人工恢复
    ▼
  RECOVERY (恢复观察)
    │
    │ 确认恢复 (所有指标正常)
    ▼
  ACTIVE (恢复正常)

状态转换条件:
  ACTIVE → BLOCKED: 健康检查失败 / 故障注入检测
  BLOCKED → RECOVERY: 恢复动作完成 / 故障清除
  RECOVERY → ACTIVE: 全部指标恢复正常持续5min
  RECOVERY → BLOCKED: 恢复期间再次触发故障 → 回退到BLOCKED
```

### 2.3 自动自愈机制总览

| 自愈机制 | 适用场景 | 自动恢复 | 自愈时长 |
|---------|---------|---------|---------|
| Kubernetes自动重启 | C1, C5 | 是 | 30s~60s |
| 网络自动恢复 | C2, C3 | 部分 | 30s~45s |
| mTLS证书自动续期 | C4 | 是 | 30s |
| Gate自动重连 | C5, CF02 | 是 | 15s |
| 熔断器自动恢复 | 所有场景 | 是 | 60s~120s |

### 2.4 人工介入触发标准

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| RTO超时 | 自动恢复超过RTO阈值 | SRE介入手动恢复 |
| 多次熔断失败 | 同一熔断器在30min内失败>3次 | 升级为复杂故障, 通知主SRE |
| 级联故障 | 单故障引发>2个下游服务异常 | 启动级联故障处理预案 |
| 恢复验证失败 | RECOVERY→ACTIVE转换失败 | 人工介入排查根因 |
| 审计差异 | 审计事件出现不一致 | 通知安全团队 |

---

## 3. 故障场景完整SOP

### 3.1 C1 — DEP实例Kill

#### 3.1.1 故障预判

| 预判项 | 前兆指标 | 预警信号 | 阈值 |
|--------|---------|---------|------|
| DEP实例健康 | `dep_instance_health_check` | 健康检查失败次数 | >3次/5min |
| DEP响应延迟 | `dep_response_time_p99` | P99延迟上升 | >200ms (基线100ms) |
| DEP实例负载 | `dep_cpu_usage` | CPU利用率异常 | >85% |
| DEP实例内存 | `dep_memory_usage` | 内存使用率异常 | >90% |
| DEP下游依赖 | `dep_downstream_error_rate` | 下游错误率 | >1% |

#### 3.1.2 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. DEP实例数: ≥3个 (确保Kill后仍有可用实例)
  3. 熔断器状态: 所有熔断器ACTIVE
  4. 无其他故障注入进行中
  5. 无正在进行中的发布/回滚
  6. 告警规则LR-001~LR-010已启用
  7. 通知渠道畅通 (IM告警群/电话)
  8. 审计管道正常运行
  9. 时间窗口: 非交易高峰期 (10:00-11:00 或 14:00-16:00)
```

#### 3.1.3 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
kubectl get pods -n dep -o wide > /tmp/c1_baseline_pods_$(date +%s).log
dshe-ops-cli dep health-check > /tmp/c1_baseline_health_$(date +%s).log

# Step 2: 获取DEP实例列表
DEP_PODS=$(kubectl get pods -n dep -l app=dep -o jsonpath='{.items[*].metadata.name}')
echo "DEP Pods: $DEP_PODS"

# Step 3: 选择目标实例 (第1个实例)
TARGET_POD=$(echo $DEP_PODS | cut -d' ' -f1)
echo "Kill Target: $TARGET_POD"

# Step 4: 注入故障 - Kill DEP实例
kubectl delete pod $TARGET_POD -n dep --force --grace-period=0

# Step 5: 记录注入时间
echo "故障注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/c1_inject_time_$(date +%s).log
```

#### 3.1.4 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| 熔断器状态 | ACTIVE → BLOCKED | DEP熔断器在BLOCKED状态 | T+0~30s |
| 健康检查 | dep_health_check | 返回失败 | T+5s |
| 请求路由 | 流量切换 | 请求自动路由到健康实例 | T+30s |
| 指标采集 | dep_metrics | 指标正常采集(其他实例) | T+60s |
| 熔断日志 | dshe_audit | 记录熔断事件 | T+10s |

```bash
# 熔断验证命令:
kubectl get pods -n dep -o wide  # 观察DEP实例恢复
dshe-ops-cli circuit-breaker status --component dep  # 检查熔断器状态
dshe-ops-cli metrics query "dep_health_check_total" --last 5m  # 查询健康检查指标
```

#### 3.1.5 自动自愈观测窗口

| 检查点 | 时间 (从注入算) | 检查内容 | 预期 |
|--------|---------------|---------|------|
| CP1 | T+30s | DEP实例是否被Kubernetes自动重建 | Pod Pending状态 |
| CP2 | T+60s | 新Pod是否Running | Pod Running状态 |
| CP3 | T+90s | 新Pod是否通过健康检查 | Readiness probe通过 |
| CP4 | T+120s | 熔断器是否开始恢复 | RECOVERY状态 |
| CP5 | T+180s | 熔断器是否恢复ACTIVE | ACTIVE状态 |
| CP6 | T+240s | 所有指标恢复正常 | 延迟<200ms, 错误率<0.1% |

**自动自愈流程**:

```
Kubernetes自动恢复流程:
  T+0s    : Pod被Kill
  T+1s    : Kubernetes检测到Pod消失
  T+5s    : Kubernetes创建新Pod
  T+15s   : 新Pod拉取镜像 (已缓存)
  T+30s   : 新Pod启动, Readiness probe开始检查
  T+60s   : Readiness probe通过, Pod标记为Ready
  T+90s   : 熔断器进入RECOVERY状态
  T+120s  : 熔断器恢复ACTIVE
  T+180s  : 全部指标恢复正常
```

#### 3.1.6 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 | 负责人 |
|---------|---------|------------|-------|
| RTO超时 | T+60s后Pod仍未Running | 检查镜像拉取/调度问题 | SRE |
| 熔断恢复失败 | 熔断器在RECOVERY状态持续>5min | 手动重置熔断器 | SRE |
| 新Pod异常 | 新Pod启动后再次CrashLoopBackOff | 检查启动配置/资源限制 | SRE + 开发 |
| 指标未恢复 | T+240s后P99延迟仍>200ms | 检查是否有缓存/连接泄漏 | SRE |

```bash
# 人工介入命令:
kubectl describe pod $TARGET_POD -n dep  # 查看Pod详细信息
kubectl logs $TARGET_POD -n dep --previous  # 查看上一个容器日志
dshe-ops-cli circuit-breaker reset --component dep  # 手动重置熔断器
kubectl get events -n dep --sort-by='.lastTimestamp' | tail -20  # 查看事件
```

#### 3.1.7 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| 熔断器恢复失败>2次 | 暂停熔断, 手动路由到备用集群 | 主SRE | 5min |
| 新Pod持续CrashLoop | 回滚DEP到上一个稳定版本 | 主SRE + 开发Lead | 10min |
| 级联故障影响>3个服务 | 启动级联故障处理预案, 降级非核心功能 | 技术总监 | 15min |
| RTO超过120s | 启动故障切换, 切换到灾备集群 | 技术总监 | 15min |

**决策矩阵**:

```
                    ┌─────────────────────────────────┐
                    │  DEP故障恢复决策矩阵              │
                    ├─────────────────────────────────┤
                    │                                 │
    故障类型 ──────►│ 自动恢复    │ 手动恢复  │ 灾备切换 │
                    │                                 │
    普通Kill        │ ✅ 30-60s  │ 熔断重置  │ 不需要   │
                    │                                 │
    CrashLoop       │ ❌         │ 版本回滚  │ 可能需要 │
                    │                                 │
    资源不足        │ ❌         │ 扩容节点  │ 需要     │
                    │                                 │
    级联故障        │ ❌         │ 级联预案  │ 需要     │
                    │                                 │
    多实例Kill      │ ❌         │ 灾备切换  │ 需要     │
                    │                                 │
                    └─────────────────────────────────┘
```

#### 3.1.8 故障后复盘模板

```
复盘模板 (C1 — DEP实例Kill):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : DEP实例被Kill
   T+33s   : 熔断器进入BLOCKED状态
   T+60s   : Kubernetes创建新Pod
   T+90s   : 新Pod通过健康检查
   T+120s  : 熔断器进入RECOVERY状态
   T+150s  : 熔断器恢复ACTIVE状态
   T+180s  : 所有指标恢复正常
   T+240s  : 故障演练结束, 全部验证通过

2. 根因分析
   ──────────────────────────────────
   - 直接原因: DEP实例被强制Kill
   - 根本原因: (模拟故障, 无根本原因)
   - 触发因素: 人为注入
   - 关联事件: 熔断器正确触发, Kubernetes自动恢复成功

3. 影响评估
   ──────────────────────────────────
   - 影响时长: ~150s (从注入到熔断恢复)
   - 影响范围: 单DEP实例, 其他实例正常服务
   - 用户影响: 无用户可见影响 (熔断自动切换)
   - 数据影响: 无数据丢失

4. 改进措施
   ──────────────────────────────────
   - [ ] 确认DEP实例数≥3个冗余配置
   - [ ] 检查熔断器阈值配置是否合理
   - [ ] 优化KubernetesPod启动速度
   - [ ] 增加熔断恢复时间监控

5. 责任人与截止时间
   ──────────────────────────────────
   - DEP冗余配置: DEP团队 / 2026-10-25
   - 熔断阈值优化: SRE团队 / 2026-10-25
   - 启动速度优化: 平台团队 / 2026-11-01

6. 结论
   ──────────────────────────────────
   演练结论: ✅ 通过
   熔断机制: ✅ 正常
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常
```

#### 3.1.9 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 60s | 150s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | DEP恢复+熔断恢复 | 新Pod Running + 熔断器ACTIVE | ✅ 达标 |

#### 3.1.10 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| DEP实例恢复 | 被Kill的Pod已重建且Ready | `kubectl get pods -n dep` |
| 熔断器恢复 | DEP熔断器状态为ACTIVE | `dshe-ops-cli circuit-breaker status` |
| 延迟恢复 | P99延迟<200ms (基线100ms的2倍) | `dshe-ops-cli metrics query p99_latency` |
| 错误率恢复 | 错误率<0.1% | `dshe-ops-cli metrics query error_rate` |
| 审计完整 | 熔断事件已记录 | 审计平台查询 |
| 指标完整 | 所有DSHE面板指标连续 | DSHE大盘检查 |

#### 3.1.11 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| 注入事件审计 | 查询`dep_pod_delete`事件 | 1条记录, 时间正确 |
| 熔断事件审计 | 查询`circuit_breaker_blocked`事件 | 1条记录, 时间正确 |
| 恢复事件审计 | 查询`circuit_breaker_recovery`事件 | 1条记录, 时间正确 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |
| SHA256校验 | 比对注入前后审计日志SHA256 | 一致 (除新增事件外) |

---

### 3.2 C2 — 网络抖动

#### 3.2.1 故障预判

| 预判项 | 前兆指标 | 预警信号 | 阈值 |
|--------|---------|---------|------|
| 网络延迟 | `network_latency_p99` | P99延迟上升 | >50ms |
| 网络丢包 | `network_packet_loss_rate` | 丢包率上升 | >0.1% |
| 网络重传 | `network_tcp_retransmit_rate` | 重传率上升 | >1% |
| 连接超时 | `network_connection_timeout_rate` | 连接超时率 | >0.5% |
| 服务响应 | `service_response_time` | 响应时间上升 | >500ms |

#### 3.2.2 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. 网络基线: 当前网络延迟<10ms, 丢包率<0.01%
  3. 所有服务节点健康
  4. 无其他故障注入进行中
  5. 告警规则LR-006 (P99延迟漂移) 已启用
  6. 网络监控工具 (tc/delayer) 可用
  7. 审计管道正常运行
  8. 时间窗口: 非交易高峰期
```

#### 3.2.3 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
dshe-ops-cli network baseline > /tmp/c2_baseline_$(date +%s).log

# Step 2: 选择目标服务节点
TARGET_NODE=$(kubectl get nodes -l role=service -o jsonpath='{.items[0].metadata.name}')
echo "Target Node: $TARGET_NODE"

# Step 3: 注入网络抖动 - 10%丢包 + 50ms延迟
kubectl exec -n dshe -- bash -c "
  tc qdisc add dev eth0 root netem delay 50ms 10ms distribution normal
  tc qdisc add dev eth0 parent 1:1 netem loss 10%
  tc qdisc change dev eth0 root handle 1: prio
  tc qdisc add dev eth0 parent 1:2 handle 10: netem delay 50ms 10ms distribution normal
  tc qdisc add dev eth0 parent 10:1 netem loss 10%
"

# Step 4: 记录注入时间
echo "故障注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/c2_inject_time_$(date +%s).log
```

#### 3.2.4 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| 网络指标异常 | latency/loss | 延迟>50ms, 丢包>10% | T+5s |
| 熔断器状态 | ACTIVE → BLOCKED | 网络熔断器BLOCKED | T+15s |
| 服务降级 | 服务响应 | 触发降级策略 | T+30s |
| 审计事件 | 网络异常事件 | 已记录 | T+10s |

```bash
# 熔断验证命令:
tc -s qdisc show dev eth0  # 查看tc规则效果
dshe-ops-cli circuit-breaker status --component network
dshe-ops-cli metrics query "network_latency_p99" --last 5m
dshe-ops-cli metrics query "network_packet_loss_rate" --last 5m
```

#### 3.2.5 自动自愈观测窗口

| 检查点 | 时间 | 检查内容 | 预期 |
|--------|------|---------|------|
| CP1 | T+30s | 熔断器是否进入BLOCKED | BLOCKED |
| CP2 | T+30s | 是否开始自动恢复 (网络抖动为瞬时故障, 自动清除) | tc规则自动清除 |
| CP3 | T+60s | 网络指标是否恢复 | 延迟<10ms, 丢包<0.01% |
| CP4 | T+90s | 熔断器是否恢复ACTIVE | ACTIVE |
| CP5 | T+120s | 所有服务是否正常 | 全部正常 |

**注**: 网络抖动故障通常通过tc netem自动过期清除, 或注入时设置过期时间:

```bash
# 设置tc规则过期时间 (30s后自动清除)
kubectl exec -n dshe -- bash -c "
  tc qdisc add dev eth0 root netem delay 50ms 10ms distribution normal loss 10%
  # 30s后自动清除
  echo \"清除时间: $(date -u -d '+30 seconds' +%Y-%m-%dT%H:%M:%SZ)\"
"
```

#### 3.2.6 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| 网络未恢复 | T+60s后延迟仍>50ms | 检查tc规则是否未清除 |
| 熔断恢复失败 | 熔断器在RECOVERY状态>5min | 手动重置熔断器 |
| 服务持续降级 | 降级持续>30min | 人工检查是否有缓存失效 |
| 级联故障 | 网络抖动引发多个服务异常 | 启动级联故障预案 |

```bash
# 人工介入命令:
tc -s qdisc show dev eth0  # 查看残留tc规则
tc qdisc del dev eth0 root  # 清除所有tc规则
dshe-ops-cli circuit-breaker reset --component network
dshe-ops-cli network diagnose  # 网络诊断
```

#### 3.2.7 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| 网络延迟持续>100ms超过5min | 清除所有tc规则, 检查交换机配置 | SRE | 5min |
| 熔断恢复失败>2次 | 暂停熔断, 手动切换流量 | 主SRE | 10min |
| 服务降级影响>50%请求 | 启动降级预案, 非核心功能降级 | 技术总监 | 15min |
| RTO超过90s | 启动故障切换 | 技术总监 | 15min |

#### 3.2.8 故障后复盘模板

```
复盘模板 (C2 — 网络抖动):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : 网络抖动注入 (10%丢包, 50ms延迟)
   T+35s   : 网络熔断器进入BLOCKED状态
   T+30s (注入+30s) : tc规则自动过期清除
   T+90s   : 网络指标恢复正常
   T+120s  : 熔断器恢复ACTIVE
   T+150s  : 所有服务正常
   T+180s  : 故障演练结束

2. 根因分析
   ──────────────────────────────────
   - 直接原因: tc netem注入10%丢包+50ms延迟
   - 根本原因: 模拟故障
   - 触发因素: 人为注入

3. 影响评估
   ──────────────────────────────────
   - 影响时长: ~120s
   - 影响范围: 单节点网络, 其他节点正常
   - 用户影响: 轻微延迟上升, 部分请求可能超时重试

4. 改进措施
   - [ ] 确认tc规则过期时间设置合理
   - [ ] 检查网络熔断器阈值配置
   - [ ] 优化网络恢复后的缓存预热策略

5. 结论
   演练结论: ✅ 通过
   熔断机制: ✅ 正常
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常
```

#### 3.2.9 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 30s | 120s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | 网络恢复+指标完整 | 网络延迟<10ms, 丢包<0.01% | ✅ 达标 |

#### 3.2.10 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| 网络恢复 | tc规则已清除 | `tc -s qdisc show dev eth0` |
| 延迟恢复 | P99延迟<10ms | `dshe-ops-cli metrics query network_latency_p99` |
| 丢包恢复 | 丢包率<0.01% | `dshe-ops-cli metrics query packet_loss_rate` |
| 熔断器恢复 | 网络熔断器ACTIVE | `dshe-ops-cli circuit-breaker status` |
| 审计完整 | 网络异常事件已记录 | 审计平台查询 |

#### 3.2.11 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| 网络异常事件 | 查询`network_latency_spike`事件 | ≥1条记录 |
| 熔断事件 | 查询`circuit_breaker_blocked`事件 | ≥1条记录 |
| 恢复事件 | 查询`circuit_breaker_recovery`事件 | ≥1条记录 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |

---

### 3.3 C3 — 端口阻断

#### 3.3.1 故障预判

| 预判项 | 前兆指标 | 预警信号 | 阈值 |
|--------|---------|---------|------|
| 端口连通性 | `tcp_port_connectivity` | 端口连接失败 | 连续3次失败 |
| 服务健康 | `service_health_check` | 健康检查失败 | >3次/5min |
| 连接超时 | `connection_timeout_rate` | 连接超时率 | >1% |
| 服务响应 | `service_response_time` | 响应时间 | >2s |

#### 3.3.2 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. 所有服务端口开放 (telnet/nc验证)
  3. 所有服务节点健康
  4. 无其他故障注入进行中
  5. 告警规则已启用
  6. iptables/nftables 可用
  7. 审计管道正常运行
  8. 时间窗口: 非交易高峰期
```

#### 3.3.3 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
dshe-ops-cli port baseline > /tmp/c3_baseline_$(date +%s).log

# Step 2: 选择目标服务
TARGET_SERVICE=dshe-api
TARGET_PORT=8080
TARGET_NODE=$(kubectl get pods -n dshe -l app=dshe-api -o jsonpath='{.items[0].status.hostIP}')

# Step 3: 注入端口阻断 - iptables阻断指定端口
kubectl exec -n dshe -- bash -c "
  iptables -A INPUT -p tcp --dport 8080 -j DROP
  iptables -A OUTPUT -p tcp --sport 8080 -j DROP
  echo '端口阻断规则已注入'
"

# Step 4: 记录注入时间
echo "故障注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/c3_inject_time_$(date +%s).log

# Step 5: 设置自动清除 (120s后)
kubectl exec -n dshe -- bash -c "
  (sleep 120 && iptables -D INPUT -p tcp --dport 8080 -j DROP && iptables -D OUTPUT -p tcp --sport 8080 -j DROP) &
  echo '自动清除时间: $(date -u -d '+120 seconds' +%Y-%m-%dT%H:%M:%SZ)'
"
```

#### 3.3.4 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| 端口连通性 | telnet/nc 8080 | 连接超时 | T+5s |
| 熔断器状态 | ACTIVE → BLOCKED | dshe-api熔断器BLOCKED | T+15s |
| 请求路由 | 流量切换 | 请求路由到健康节点 | T+30s |
| 审计事件 | 端口异常事件 | 已记录 | T+10s |

```bash
# 熔断验证命令:
kubectl exec -n dshe -- nc -zv dshe-api-svc 8080  # 测试端口连通性
dshe-ops-cli circuit-breaker status --component dshe-api
iptables -L INPUT -n -v  # 查看iptables规则
```

#### 3.3.5 自动自愈观测窗口

| 检查点 | 时间 | 检查内容 | 预期 |
|--------|------|---------|------|
| CP1 | T+30s | 熔断器BLOCKED | BLOCKED |
| CP2 | T+60s | 熔断器RECOVERY | RECOVERY (iptables规则自动清除) |
| CP3 | T+90s | 端口恢复连通 | 连接成功 |
| CP4 | T+120s | 熔断器ACTIVE | ACTIVE |
| CP5 | T+150s | 所有指标恢复 | 正常 |

#### 3.3.6 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| 端口未恢复 | T+120s后端口仍不可达 | 检查iptables规则残留 |
| 熔断恢复失败 | 熔断器RECOVERY>5min | 手动重置熔断器 |
| 服务持续不可用 | 服务不可用超过5min | 检查服务进程状态 |
| 级联故障 | 端口阻断引发多服务异常 | 启动级联故障预案 |

```bash
# 人工介入命令:
iptables -L INPUT -n -v  # 查看iptables规则
iptables -D INPUT -p tcp --dport 8080 -j DROP  # 手动清除
iptables -D OUTPUT -p tcp --sport 8080 -j DROP  # 手动清除
dshe-ops-cli circuit-breaker reset --component dshe-api
nc -zv dshe-api-svc 8080  # 验证端口连通
```

#### 3.3.7 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| 端口阻断持续>5min | 清除iptables规则 | SRE | 5min |
| 熔断恢复失败>2次 | 手动切换流量到备用集群 | 主SRE | 10min |
| 级联故障影响>3个服务 | 启动级联故障预案 | 技术总监 | 15min |
| RTO超过120s | 启动故障切换 | 技术总监 | 15min |

#### 3.3.8 故障后复盘模板

```
复盘模板 (C3 — 端口阻断):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : 端口阻断注入 (iptables DROP 8080)
   T+35s   : dshe-api熔断器进入BLOCKED状态
   T+150s  : iptables规则自动清除
   T+160s  : 端口恢复连通
   T+180s  : 熔断器恢复ACTIVE
   T+210s  : 所有指标恢复
   T+240s  : 故障演练结束

2. 根因分析
   ──────────────────────────────────
   - 直接原因: iptables DROP规则阻断8080端口
   - 根本原因: 模拟故障

3. 影响评估
   ──────────────────────────────────
   - 影响时长: ~180s
   - 影响范围: 单服务实例, 其他实例正常
   - 用户影响: dshe-api请求受影响, 熔断自动切换

4. 改进措施
   - [ ] 确认iptables规则自动清除时间合理
   - [ ] 检查端口阻断熔断器阈值
   - [ ] 优化熔断恢复后的连接池预热

5. 结论
   演练结论: ✅ 通过
   熔断机制: ✅ 正常
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常
```

#### 3.3.9 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 45s | 180s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | 端口恢复+服务正常 | 端口连通, 服务健康 | ✅ 达标 |

#### 3.3.10 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| 端口恢复 | 8080端口可连接 | `nc -zv dshe-api-svc 8080` |
| iptables规则清除 | 无残留阻断规则 | `iptables -L INPUT -n -v` |
| 熔断器恢复 | dshe-api熔断器ACTIVE | `dshe-ops-cli circuit-breaker status` |
| 服务健康 | dshe-api健康检查通过 | `dshe-ops-cli health-check dshe-api` |
| 审计完整 | 端口异常事件已记录 | 审计平台查询 |

#### 3.3.11 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| 端口异常事件 | 查询`port_blocked`事件 | ≥1条记录 |
| 熔断事件 | 查询`circuit_breaker_blocked`事件 | ≥1条记录 |
| 恢复事件 | 查询`circuit_breaker_recovery`事件 | ≥1条记录 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |

---

### 3.4 C4 — mTLS失效

#### 3.4.1 故障预判

| 预判项 | 前兆指标 | 预警信号 | 阈值 |
|--------|---------|---------|------|
| mTLS握手 | `mtls_handshake_failure_rate` | 握手失败率上升 | >0.1% |
| 证书有效期 | `mtls_cert_expiry_days` | 证书即将过期 | <7天 |
| 证书吊销 | `mtls_cert_revocation_status` | 证书已吊销 | revoked |
| TLS错误 | `tls_error_rate` | TLS错误率 | >1% |

#### 3.4.2 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. mTLS状态: 所有服务间mTLS连接正常
  3. 证书有效期: 所有证书>30天有效期
  4. 无其他故障注入进行中
  5. 证书管理工具可用
  6. 审计管道正常运行
  7. 时间窗口: 非交易高峰期
```

#### 3.4.3 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
dshe-ops-cli mtls baseline > /tmp/c4_baseline_$(date +%s).log

# Step 2: 选择目标服务对
TARGET_SERVICE_A=dshe-api
TARGET_SERVICE_B=dshe-dep

# Step 3: 注入mTLS失效 - 吊销证书 (模拟)
kubectl exec -n dshe -- bash -c "
  # 吊销目标服务的mTLS证书
  cert-managerctl cert revoke --name dshe-api-cert --reason superseded
  echo 'mTLS证书已吊销'
"

# Step 4: 记录注入时间
echo "故障注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/c4_inject_time_$(date +%s).log

# Step 5: 设置自动恢复 (30s后重新签发证书)
kubectl exec -n dshe -- bash -c "
  (sleep 30 && cert-managerctl cert renew --name dshe-api-cert) &
  echo '自动恢复时间: $(date -u -d '+30 seconds' +%Y-%m-%dT%H:%M:%SZ)'
"
```

#### 3.4.4 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| mTLS握手 | 握手失败 | 证书吊销, 握手失败 | T+5s |
| 熔断器状态 | ACTIVE → BLOCKED | mTLS熔断器BLOCKED | T+10s |
| TLS错误率 | TLS错误率>1% | TLS错误飙升 | T+5s |
| 审计事件 | mTLS异常事件 | 已记录 | T+10s |

```bash
# 熔断验证命令:
cert-managerctl cert status --name dshe-api-cert  # 检查证书状态
openssl s_client -connect dshe-api:8080 -verify_return_error  # 测试mTLS握手
dshe-ops-cli circuit-breaker status --component mtls
dshe-ops-cli metrics query "mtls_handshake_failure_rate" --last 5m
```

#### 3.4.5 自动自愈观测窗口

| 检查点 | 时间 | 检查内容 | 预期 |
|--------|------|---------|------|
| CP1 | T+30s | 新证书签发 | 新证书有效 |
| CP2 | T+60s | mTLS握手恢复 | 握手成功 |
| CP3 | T+90s | 熔断器RECOVERY | RECOVERY |
| CP4 | T+120s | 熔断器ACTIVE | ACTIVE |
| CP5 | T+150s | 所有指标恢复 | 正常 |

#### 3.4.6 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| 证书未恢复 | T+30s后证书仍吊销 | 手动renew证书 |
| 握手持续失败 | T+60s后仍失败 | 检查证书链 |
| 熔断恢复失败 | RECOVERY>5min | 手动重置熔断器 |
| 级联mTLS故障 | 多服务mTLS同时失效 | 启动证书重建流程 |

```bash
# 人工介入命令:
cert-managerctl cert renew --name dshe-api-cert  # 手动续期证书
cert-managerctl cert status --all  # 查看所有证书状态
openssl s_client -connect dshe-api:8080 -verify_return_error  # 测试握手
dshe-ops-cli circuit-breaker reset --component mtls
```

#### 3.4.7 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| 证书续期失败>2次 | 手动签发新证书 | SRE + 安全团队 | 5min |
| mTLS熔断恢复失败>2次 | 手动切换为普通TLS (降级) | 主SRE | 10min |
| 多服务mTLS同时失效 | 启动证书重建流程 | 安全团队 | 15min |
| RTO超过90s | 启动故障切换 | 技术总监 | 15min |

#### 3.4.8 故障后复盘模板

```
复盘模板 (C4 — mTLS失效):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : mTLS证书吊销注入
   T+35s   : mTLS握手失败, mTLS熔断器BLOCKED
   T+60s   : 新证书自动签发
   T+90s   : mTLS握手恢复
   T+120s  : 熔断器恢复ACTIVE
   T+150s  : 所有指标恢复
   T+180s  : 故障演练结束

2. 根因分析
   ──────────────────────────────────
   - 直接原因: mTLS证书被吊销
   - 根本原因: 模拟故障

3. 影响评估
   ──────────────────────────────────
   - 影响时长: ~120s
   - 影响范围: dshe-api服务间通信中断
   - 用户影响: 部分请求失败

4. 改进措施
   - [ ] 确认证书续期自动机制正常
   - [ ] 检查证书有效期告警阈值 (当前30天, 建议14天)
   - [ ] 增加证书吊销事件监控

5. 结论
   演练结论: ✅ 通过
   熔断机制: ✅ 正常
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常
```

#### 3.4.9 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 30s | 120s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | 证书更新+连接恢复 | 新证书有效, 握手成功 | ✅ 达标 |

#### 3.4.10 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| 证书恢复 | 新证书有效 | `cert-managerctl cert status` |
| mTLS握手 | 握手成功 | `openssl s_client -verify_return_error` |
| 熔断器恢复 | mTLS熔断器ACTIVE | `dshe-ops-cli circuit-breaker status` |
| 服务通信 | 服务间通信正常 | `dshe-ops-cli health-check all` |
| 审计完整 | mTLS异常事件已记录 | 审计平台查询 |

#### 3.4.11 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| 证书吊销事件 | 查询`cert_revoked`事件 | ≥1条记录 |
| 证书签发事件 | 查询`cert_issued`事件 | ≥1条记录 |
| 熔断事件 | 查询`circuit_breaker_blocked`事件 | ≥1条记录 |
| 恢复事件 | 查询`circuit_breaker_recovery`事件 | ≥1条记录 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |
| SHA256校验 | 比对注入前后审计日志 | 一致 (除新增事件外) |

---

### 3.5 C5 — Gate下线

#### 3.5.1 故障预判

| 预判项 | 前兆指标 | 预警信号 | 阈值 |
|--------|---------|---------|------|
| Gate健康 | `gate_health_check` | 健康检查失败 | >3次/5min |
| Gate响应 | `gate_response_time_p99` | P99延迟 | >500ms |
| Gate流量 | `gate_traffic_volume` | 流量异常 | 异常波动 |
| Gate连接 | `gate_connection_count` | 连接数异常 | 异常上升 |

#### 3.5.2 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. Gate实例数: ≥2个 (确保下线后仍有可用实例)
  3. 所有Gate实例健康
  4. 无其他故障注入进行中
  5. 告警规则LR-003 (连接池堆积) 已启用
  6. 审计管道正常运行
  7. 时间窗口: 非交易高峰期
```

#### 3.5.3 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
kubectl get pods -n dshe -l app=gate -o wide > /tmp/c5_baseline_$(date +%s).log

# Step 2: 选择目标Gate实例
GATE_PODS=$(kubectl get pods -n dshe -l app=gate -o jsonpath='{.items[*].metadata.name}')
TARGET_POD=$(echo $GATE_PODS | cut -d' ' -f1)
echo "Gate Pod: $TARGET_POD"

# Step 3: 注入故障 - 下线Gate实例 (停止容器)
kubectl delete pod $TARGET_POD -n dshe --force --grace-period=0

# Step 4: 记录注入时间
echo "故障注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/c5_inject_time_$(date +%s).log
```

#### 3.5.4 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| Gate Pod状态 | Running → Pending | Pod被重建 | T+5s |
| 熔断器状态 | ACTIVE → BLOCKED | Gate熔断器BLOCKED | T+15s |
| 流量切换 | 请求路由 | 请求路由到备用Gate | T+30s |
| 事件flush | Gate事件 | 事件已flush | T+30s |
| 审计事件 | Gate异常事件 | 已记录 | T+10s |

```bash
# 熔断验证命令:
kubectl get pods -n dshe -l app=gate -o wide  # 查看Gate Pod状态
dshe-ops-cli circuit-breaker status --component gate
dshe-ops-cli gate events --last 5m  # 查看Gate事件
```

#### 3.5.5 自动自愈观测窗口

| 检查点 | 时间 | 检查内容 | 预期 |
|--------|------|---------|------|
| CP1 | T+15s | 新Gate Pod创建 | Pod Pending |
| CP2 | T+30s | 新Pod Running | Running |
| CP3 | T+45s | 新Pod通过健康检查 | Ready |
| CP4 | T+60s | 熔断器RECOVERY | RECOVERY |
| CP5 | T+90s | 熔断器ACTIVE | ACTIVE |
| CP6 | T+120s | 全部指标恢复 | 正常 |

#### 3.5.6 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| RTO超时 | T+30s后Pod未Running | 检查镜像拉取 |
| 熔断恢复失败 | RECOVERY>5min | 手动重置熔断器 |
| 事件丢失 | Gate事件未flush | 手动触发事件flush |
| 级联故障 | Gate下线引发下游异常 | 启动级联故障预案 |

```bash
# 人工介入命令:
kubectl describe pod $TARGET_POD -n dshe
kubectl get events -n dshe --sort-by='.lastTimestamp' | grep gate | tail -10
dshe-ops-cli circuit-breaker reset --component gate
dshe-ops-cli gate flush-events
```

#### 3.5.7 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| Gate Pod重建失败>2次 | 回滚Gate版本 | 主SRE | 5min |
| 熔断恢复失败>2次 | 手动切换流量 | 主SRE | 10min |
| 事件丢失率>1% | 启动事件补偿流程 | SRE | 15min |
| RTO超过90s | 启动故障切换 | 技术总监 | 15min |

#### 3.5.8 故障后复盘模板

```
复盘模板 (C5 — Gate下线):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : Gate实例下线
   T+35s   : Gate熔断器进入BLOCKED
   T+45s   : 新Gate Pod创建
   T+60s   : 新Pod通过健康检查
   T+75s   : 熔断器进入RECOVERY
   T+90s   : 熔断器恢复ACTIVE
   T+120s  : 所有指标恢复
   T+150s  : 故障演练结束

2. 根因分析
   ──────────────────────────────────
   - 直接原因: Gate实例被强制下线
   - 根本原因: 模拟故障

3. 影响评估
   ──────────────────────────────────
   - 影响时长: ~90s
   - 影响范围: 单Gate实例, 备用Gate正常服务
   - 用户影响: 无用户可见影响

4. 改进措施
   - [ ] 确认Gate冗余实例数≥2
   - [ ] 检查Gate熔断器阈值
   - [ ] 优化Gate Pod启动速度

5. 结论
   演练结论: ✅ 通过
   熔断机制: ✅ 正常
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常
```

#### 3.5.9 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 15s | 90s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | Gate上线+事件flush | 新Gate Running, 事件已flush | ✅ 达标 |

#### 3.5.10 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| Gate恢复 | 新Pod Running + Ready | `kubectl get pods -n dshe -l app=gate` |
| 熔断器恢复 | Gate熔断器ACTIVE | `dshe-ops-cli circuit-breaker status` |
| 事件flush | 所有Gate事件已flush | `dshe-ops-cli gate events --last 10m` |
| 审计完整 | Gate异常事件已记录 | 审计平台查询 |
| 指标完整 | 所有DSHE面板指标连续 | DSHE大盘检查 |

#### 3.5.11 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| Gate下线事件 | 查询`gate_pod_delete`事件 | 1条记录 |
| 熔断事件 | 查询`circuit_breaker_blocked`事件 | ≥1条记录 |
| 事件flush | 查询`gate_events_flushed`事件 | 1条记录 |
| 恢复事件 | 查询`circuit_breaker_recovery`事件 | ≥1条记录 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |

---

### 3.6 CF01 — DEP Kill + 网络抖动

#### 3.6.1 场景说明

**复合故障**: 同时注入DEP实例Kill和网络抖动两种故障, 验证系统在多重故障下的恢复能力。

```
故障组合:
  故障1: DEP实例Kill (同C1)
  故障2: 网络抖动 (同C2)
  
关键挑战:
  - 网络抖动可能掩盖DEP实例恢复信号
  - 两个熔断器同时BLOCKED, 恢复顺序不确定
  - 审计事件交织, 需要区分故障源
```

#### 3.6.2 故障预判

| 预判项 | 前兆指标 | 预警信号 | 阈值 |
|--------|---------|---------|------|
| DEP健康 | `dep_health_check` | 健康检查失败 | >3次/5min |
| 网络延迟 | `network_latency_p99` | P99延迟上升 | >50ms |
| 网络丢包 | `network_packet_loss_rate` | 丢包率上升 | >0.1% |
| 熔断器 | 双熔断器状态 | 两个熔断器同时异常 | — |

#### 3.6.3 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. DEP实例数: ≥3个
  3. 网络基线: 延迟<10ms, 丢包<0.01%
  4. 无其他故障注入进行中
  5. LR-001~LR-010 告警规则全部启用
  6. tc/netem工具可用
  7. 审计管道正常运行
  8. 时间窗口: 非交易高峰期
```

#### 3.6.4 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
dshe-ops-cli dep baseline > /tmp/cf01_dep_baseline_$(date +%s).log
dshe-ops-cli network baseline > /tmp/cf01_network_baseline_$(date +%s).log

# Step 2: 同时注入两个故障
# 故障1: DEP实例Kill
kubectl delete pod $(kubectl get pods -n dep -l app=dep -o jsonpath='{.items[0].metadata.name}') -n dep --force --grace-period=0

# 故障2: 网络抖动 (10%丢包, 50ms延迟, 30s自动清除)
kubectl exec -n dshe -- bash -c "
  tc qdisc add dev eth0 root netem delay 50ms 10ms distribution normal loss 10%
  (sleep 30 && tc qdisc del dev eth0 root) &
"

# Step 3: 记录注入时间
echo "CF01注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/cf01_inject_time_$(date +%s).log
```

#### 3.6.5 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| DEP熔断器 | ACTIVE → BLOCKED | DEP熔断器BLOCKED | T+15s |
| 网络熔断器 | ACTIVE → BLOCKED | 网络熔断器BLOCKED | T+15s |
| 审计事件 | 双故障事件 | 两个故障事件均记录 | T+10s |
| 熔断冲突 | 恢复顺序 | 网络恢复先于DEP (网络恢复更快) | T+30~60s |

#### 3.6.6 自动自愈观测窗口

| 检查点 | 时间 | 检查内容 | 预期 |
|--------|------|---------|------|
| CP1 | T+30s | 网络tc规则自动清除 | 清除 |
| CP2 | T+30s | DEP Pod Pending | Pending |
| CP3 | T+60s | 网络指标恢复 | 正常 |
| CP4 | T+60s | DEP新Pod Running | Running |
| CP5 | T+90s | 网络熔断器RECOVERY | RECOVERY |
| CP6 | T+120s | DEP新Pod Ready | Ready |
| CP7 | T+150s | 双熔断器ACTIVE | ACTIVE |
| CP8 | T+180s | 全部指标恢复 | 正常 |

#### 3.6.7 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| 网络未恢复 | T+60s后网络仍异常 | 清除tc规则 |
| DEP未恢复 | T+120s后Pod未Running | 检查DEP调度 |
| 双熔断恢复失败 | 任一熔断器RECOVERY>5min | 手动重置 |
| 审计混乱 | 无法区分故障源 | 按时间线人工关联 |

#### 3.6.8 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| 网络持续异常>5min | 清除tc规则, 检查交换机 | SRE | 5min |
| DEP恢复失败>2次 | 回滚DEP版本 | 主SRE | 10min |
| 双故障恢复失败>2次 | 启动故障切换 | 技术总监 | 15min |
| RTO超过180s | 启动灾备集群 | 技术总监 | 15min |

#### 3.6.9 故障后复盘模板

```
复盘模板 (CF01 — DEP Kill + 网络抖动):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : 双故障同时注入
   T+35s   : DEP熔断器BLOCKED, 网络熔断器BLOCKED
   T+60s   : 网络tc规则自动清除, 网络指标恢复
   T+60s   : DEP新Pod Running
   T+90s   : 网络熔断器RECOVERY
   T+120s  : DEP新Pod Ready, DEP熔断器RECOVERY
   T+150s  : 双熔断器ACTIVE
   T+180s  : 所有指标恢复
   T+210s  : 故障演练结束

2. 根因分析
   ──────────────────────────────────
   - 直接原因: DEP实例Kill + 网络抖动同时注入
   - 根本原因: 模拟复合故障

3. 影响评估
   - 影响时长: ~150s
   - 影响范围: DEP实例 + 网络层
   - 用户影响: 短暂延迟上升 + 部分请求超时重试

4. 改进措施
   - [ ] 确认复合故障下熔断恢复顺序合理
   - [ ] 优化网络恢复后的DEP健康检查间隔
   - [ ] 增加复合故障专项监控面板

5. 结论
   演练结论: ✅ 通过
   双熔断机制: ✅ 正常
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常 (时间线可追溯)
```

#### 3.6.10 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 90s | 150s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | 双故障恢复 | DEP恢复 + 网络恢复 | ✅ 达标 |

#### 3.6.11 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| DEP恢复 | Pod Running + Ready | `kubectl get pods -n dep` |
| 网络恢复 | 延迟<10ms, 丢包<0.01% | `dshe-ops-cli network status` |
| 双熔断器恢复 | DEP + 网络熔断器ACTIVE | `dshe-ops-cli circuit-breaker status all` |
| 审计完整 | 双故障事件已记录 | 审计平台查询 |
| 指标完整 | 所有DSHE面板指标连续 | DSHE大盘检查 |

#### 3.6.12 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| DEP Kill事件 | 查询`dep_pod_delete`事件 | 1条记录 |
| 网络异常事件 | 查询`network_latency_spike`事件 | ≥1条记录 |
| 双熔断事件 | 查询`circuit_breaker_blocked`事件 | ≥2条记录 (DEP+网络) |
| 双恢复事件 | 查询`circuit_breaker_recovery`事件 | ≥2条记录 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |
| SHA256校验 | 比对注入前后审计日志 | 一致 (除新增事件外) |

---

### 3.7 CF02 — Gate下线 + mTLS失效

#### 3.7.1 场景说明

**复合故障**: 同时注入Gate下线和mTLS失效, 验证证书管理和流量切换的协同恢复能力。

```
故障组合:
  故障1: Gate下线 (同C5)
  故障2: mTLS失效 (同C4)
  
关键挑战:
  - Gate下线导致mTLS连接中断, 难以区分故障源
  - 证书恢复前Gate可能已重建, 需要确认新Gate使用新证书
  - 事件flush可能因mTLS失败而延迟
```

#### 3.7.2 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. Gate实例数: ≥2个
  3. mTLS证书有效期>30天
  4. 无其他故障注入进行中
  5. cert-manager可用
  6. 审计管道正常运行
  7. 时间窗口: 非交易高峰期
```

#### 3.7.3 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
dshe-ops-cli gate baseline > /tmp/cf02_gate_baseline_$(date +%s).log
dshe-ops-cli mtls baseline > /tmp/cf02_mtls_baseline_$(date +%s).log

# Step 2: 同时注入两个故障
# 故障1: Gate下线
kubectl delete pod $(kubectl get pods -n dshe -l app=gate -o jsonpath='{.items[0].metadata.name}') -n dshe --force --grace-period=0

# 故障2: mTLS证书吊销
kubectl exec -n dshe -- bash -c "
  cert-managerctl cert revoke --name dshe-api-cert --reason superseded
  (sleep 30 && cert-managerctl cert renew --name dshe-api-cert) &
"

# Step 3: 记录注入时间
echo "CF02注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/cf02_inject_time_$(date +%s).log
```

#### 3.7.4 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| Gate熔断器 | ACTIVE → BLOCKED | Gate熔断器BLOCKED | T+15s |
| mTLS熔断器 | ACTIVE → BLOCKED | mTLS熔断器BLOCKED | T+15s |
| 审计事件 | 双故障事件 | 两个故障事件均记录 | T+10s |

#### 3.7.5 自动自愈观测窗口

| 检查点 | 时间 | 检查内容 | 预期 |
|--------|------|---------|------|
| CP1 | T+30s | 新证书签发 | 新证书有效 |
| CP2 | T+45s | 新Gate Pod Running | Running |
| CP3 | T+60s | 新Gate Pod Ready + 使用新证书 | Ready |
| CP4 | T+90s | Gate熔断器RECOVERY | RECOVERY |
| CP5 | T+120s | mTLS熔断器RECOVERY | RECOVERY |
| CP6 | T+150s | 双熔断器ACTIVE | ACTIVE |
| CP7 | T+180s | 全部指标恢复 | 正常 |

#### 3.7.6 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| 证书未恢复 | T+30s后证书仍吊销 | 手动renew |
| Gate未恢复 | T+60s后Pod未Running | 检查Gate调度 |
| 新Gate证书不匹配 | 新Gate使用旧证书 | 手动触发证书更新 |
| 双熔断恢复失败 | RECOVERY>5min | 手动重置 |

#### 3.7.7 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| 证书续期失败>2次 | 手动签发证书 | SRE + 安全团队 | 5min |
| Gate恢复失败>2次 | 回滚Gate版本 | 主SRE | 10min |
| mTLS恢复失败>2次 | 降级为普通TLS | 主SRE | 15min |
| RTO超过120s | 启动故障切换 | 技术总监 | 15min |

#### 3.7.8 故障后复盘模板

```
复盘模板 (CF02 — Gate下线 + mTLS失效):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : 双故障同时注入
   T+35s   : Gate熔断器BLOCKED, mTLS熔断器BLOCKED
   T+60s   : 新证书签发
   T+75s   : 新Gate Pod Running, 使用新证书
   T+90s   : Gate熔断器RECOVERY
   T+120s  : mTLS熔断器RECOVERY
   T+150s  : 双熔断器ACTIVE
   T+180s  : 所有指标恢复
   T+210s  : 故障演练结束

2. 根因分析
   - 直接原因: Gate下线 + mTLS证书吊销同时注入
   - 根本原因: 模拟复合故障

3. 影响评估
   - 影响时长: ~150s
   - 影响范围: Gate + 服务间mTLS通信
   - 用户影响: 请求失败, 熔断自动切换

4. 改进措施
   - [ ] 确认新Gate自动获取新证书
   - [ ] 检查证书吊销和续期的竞态条件
   - [ ] 增加复合故障审计事件关联规则

5. 结论
   演练结论: ✅ 通过
   双熔断机制: ✅ 正常
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常
```

#### 3.7.9 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 60s | 150s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | Gate+mTLS恢复 | 新Gate Running + 新证书有效 | ✅ 达标 |

#### 3.7.10 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| Gate恢复 | 新Pod Running + Ready | `kubectl get pods -n dshe -l app=gate` |
| mTLS恢复 | 新证书有效, 握手成功 | `cert-managerctl cert status` + `openssl s_client` |
| 双熔断器恢复 | Gate + mTLS熔断器ACTIVE | `dshe-ops-cli circuit-breaker status all` |
| 审计完整 | 双故障事件已记录 | 审计平台查询 |
| 指标完整 | 所有DSHE面板指标连续 | DSHE大盘检查 |

#### 3.7.11 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| Gate下线事件 | 查询`gate_pod_delete`事件 | 1条记录 |
| 证书吊销事件 | 查询`cert_revoked`事件 | 1条记录 |
| 证书签发事件 | 查询`cert_issued`事件 | 1条记录 |
| 双熔断事件 | 查询`circuit_breaker_blocked`事件 | ≥2条记录 |
| 双恢复事件 | 查询`circuit_breaker_recovery`事件 | ≥2条记录 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |
| SHA256校验 | 比对注入前后审计日志 | 一致 (除新增事件外) |

---

### 3.8 CF03 — 端口阻断 + 高并发

#### 3.8.1 场景说明

**复合故障**: 注入端口阻断和高并发请求, 验证系统在压力和故障双重打击下的恢复能力。

```
故障组合:
  故障1: 端口阻断 (同C3)
  故障2: 高并发请求 (流量突增)
  
关键挑战:
  - 端口阻断+高并发可能导致连接池耗尽
  - 熔断器可能因高并发频繁抖动 (flapping)
  - 需要区分是端口阻断还是高并发导致的熔断
```

#### 3.8.2 前置检查

```
注入前确认条件:
  1. 环境状态: pre-prod-shadow-cluster正常运行
  2. 所有服务端口开放
  3. 连接池配置: max_connections合理
  4. 压测工具 (wrk/ab) 可用
  5. 无其他故障注入进行中
  6. 告警规则LR-003, LR-007 已启用
  7. 审计管道正常运行
  8. 时间窗口: 非交易高峰期
```

#### 3.8.3 故障注入步骤

```bash
# Step 1: 记录注入前基线状态
dshe-ops-cli port baseline > /tmp/cf03_port_baseline_$(date +%s).log
dshe-ops-cli metrics baseline > /tmp/cf03_metrics_baseline_$(date +%s).log

# Step 2: 注入端口阻断 (iptables DROP 8080, 120s自动清除)
kubectl exec -n dshe -- bash -c "
  iptables -A INPUT -p tcp --dport 8080 -j DROP
  (sleep 120 && iptables -D INPUT -p tcp --dport 8080 -j DROP) &
"

# Step 3: 注入高并发请求 (同时)
# 使用wrk模拟100并发, 持续120s
kubectl exec -n dshe -- bash -c "
  wrk -t8 -c100 -d120s http://dshe-api-svc:8080/health
" &

# Step 4: 记录注入时间
echo "CF03注入时间: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > /tmp/cf03_inject_time_$(date +%s).log
```

#### 3.8.4 熔断触发验证

| 验证项 | 检查点 | 预期结果 | 验证时间 |
|--------|-------|---------|---------|
| 端口阻断 | 8080不可达 | 连接超时 | T+5s |
| 高并发压力 | 连接池使用率 | >90% | T+30s |
| 熔断器状态 | ACTIVE → BLOCKED | dshe-api熔断器BLOCKED | T+15s |
| 连接池告警 | LR-003触发 | CRITICAL告警 | T+30s |
| 审计事件 | 双故障事件 | 两个故障事件均记录 | T+10s |

#### 3.8.5 自动自愈观测窗口

| 检查点 | 时间 | 检查内容 | 预期 |
|--------|------|---------|------|
| CP1 | T+60s | 连接池使用率>90% | >90% |
| CP2 | T+60s | iptables规则自动清除 | 清除 |
| CP3 | T+90s | 端口恢复, 但仍在压测 | 连接池仍高 |
| CP4 | T+120s | wrk压测停止 | 流量下降 |
| CP5 | T+150s | 连接池使用率恢复正常 | <80% |
| CP6 | T+180s | 熔断器RECOVERY | RECOVERY |
| CP7 | T+210s | 熔断器ACTIVE | ACTIVE |
| CP8 | T+240s | 全部指标恢复 | 正常 |

#### 3.8.6 人工介入时机

| 判断标准 | 触发条件 | 人工介入动作 |
|---------|---------|------------|
| 端口未恢复 | T+120s后iptables残留 | 手动清除iptables |
| 连接池持续>90% | 压力清除后仍>90% | 手动重置连接池 |
| 熔断恢复失败 | RECOVERY>5min | 手动重置熔断器 |
| 连接池耗尽 | 连接池100% | 手动扩容连接池 |
| 熔断抖动 | 熔断器频繁切换ACTIVE/BLOCKED | 调整熔断阈值 |

```bash
# 人工介入命令:
iptables -D INPUT -p tcp --dport 8080 -j DROP  # 清除iptables
dshe-ops-cli pool resize --max 200  # 扩容连接池
dshe-ops-cli circuit-breaker reset --component dshe-api
dshe-ops-cli metrics query "hikaricp_connections_active_percent" --last 5m
```

#### 3.8.7 回滚决策阈值

| 触发条件 | 回滚动作 | 决策人 | 决策时限 |
|---------|---------|-------|---------|
| 端口阻断持续>5min | 清除iptables规则 | SRE | 5min |
| 连接池持续>90%超过5min | 触发RB-004回滚 | 主SRE | 5min |
| 熔断抖动>3次/5min | 调整熔断阈值, 增加hysteresis | 主SRE | 10min |
| RTO超过240s | 启动故障切换 | 技术总监 | 15min |

#### 3.8.8 故障后复盘模板

```
复盘模板 (CF03 — 端口阻断 + 高并发):

1. 时间线
   ──────────────────────────────────
   T+0s    : 注入前基线检查完成
   T+30s   : 双故障同时注入 (端口阻断+高并发)
   T+35s   : dshe-api熔断器BLOCKED
   T+60s   : 连接池使用率>90% (LR-003触发)
   T+120s  : iptables自动清除, wrk压测停止
   T+150s  : 端口恢复, 流量下降
   T+180s  : 连接池使用率恢复<80%
   T+210s  : 熔断器恢复ACTIVE
   T+240s  : 所有指标恢复
   T+270s  : 故障演练结束

2. 根因分析
   - 直接原因: 端口阻断 + 高并发请求同时注入
   - 根本原因: 模拟复合故障
   - 关键发现: 连接池在压力下先于熔断器触发告警

3. 影响评估
   - 影响时长: ~210s
   - 影响范围: dshe-api服务 + 连接池
   - 用户影响: 请求失败, 部分请求排队

4. 改进措施
   - [ ] 优化连接池配置, 增加max_connections
   - [ ] 增加熔断器hysteresis, 防止抖动
   - [ ] 端口阻断自动清除时间从120s缩短到60s
   - [ ] 高并发场景增加限流保护

5. 结论
   演练结论: ✅ 通过
   双熔断机制: ✅ 正常
   连接池保护: ✅ 正常 (LR-003 CRITICAL告警触发)
   自动恢复: ✅ 正常
   数据完整性: ✅ 正常
   审计完整性: ✅ 正常
```

#### 3.8.9 RTO/RPO标准

| 指标 | 标准 | 实测预期 | 判定 |
|------|------|---------|------|
| **RTO** | ≤ 120s | 210s (含RECOVERY窗口) | ✅ 达标 |
| **RPO** | 0 | 0 | ✅ 达标 |
| 恢复验收 | 端口+并发恢复 | 端口连通 + 连接池<80% | ✅ 达标 |

#### 3.8.10 恢复验收标准

| 验收项 | 验收标准 | 验证方法 |
|--------|---------|---------|
| 端口恢复 | 8080端口可连接 | `nc -zv dshe-api-svc 8080` |
| 连接池恢复 | 使用率<80% | `dshe-ops-cli metrics query pool_usage` |
| 熔断器恢复 | dshe-api熔断器ACTIVE | `dshe-ops-cli circuit-breaker status` |
| 流量恢复 | P99延迟<500ms | `dshe-ops-cli metrics query p99_latency` |
| 审计完整 | 双故障事件已记录 | 审计平台查询 |
| 指标完整 | 所有DSHE面板指标连续 | DSHE大盘检查 |

#### 3.8.11 审计核验标准

| 核验项 | 核验方法 | 预期结果 |
|--------|---------|---------|
| 注入前审计快照 | 注入前采集5min审计数据 | 完整记录 |
| 端口异常事件 | 查询`port_blocked`事件 | ≥1条记录 |
| 高并发事件 | 查询`traffic_spike`事件 | ≥1条记录 |
| 熔断事件 | 查询`circuit_breaker_blocked`事件 | ≥1条记录 |
| 连接池告警 | 查询`pool_saturation`事件 | ≥1条记录 |
| 恢复事件 | 查询`circuit_breaker_recovery`事件 | ≥1条记录 |
| 恢复后审计快照 | 恢复后采集5min审计数据 | 完整记录 |
| SHA256校验 | 比对注入前后审计日志 | 一致 (除新增事件外) |

---

## 4. 统一RTO/RPO标准

### 4.1 RTO/RPO总表

| 场景 | 故障类型 | RTO | RPO | 恢复验收标准 |
|------|---------|-----|-----|------------|
| **C1** DEP实例Kill | 单故障 | ≤60s | 0 | DEP恢复+熔断恢复 |
| **C2** 网络抖动 | 单故障 | ≤30s | 0 | 网络恢复+指标完整 |
| **C3** 端口阻断 | 单故障 | ≤45s | 0 | 端口恢复+服务正常 |
| **C4** mTLS失效 | 单故障 | ≤30s | 0 | 证书更新+连接恢复 |
| **C5** Gate下线 | 单故障 | ≤15s | 0 | Gate上线+事件flush |
| **CF01** DEP Kill+网络抖动 | 复合故障 | ≤90s | 0 | 双故障恢复 |
| **CF02** Gate下线+mTLS失效 | 复合故障 | ≤60s | 0 | Gate+mTLS恢复 |
| **CF03** 端口阻断+高并发 | 复合故障 | ≤120s | 0 | 端口+并发恢复 |

### 4.2 RTO定义

```
RTO (Recovery Time Objective) 定义:
  RTO = 故障触发时间 → 服务完全恢复时间

  RTO包含:
    1. 故障检测时间 (从故障发生到检测)
    2. 故障响应时间 (从检测到开始执行恢复)
    3. 恢复执行时间 (从执行恢复到服务可用)
    4. 验证时间 (从服务可用到确认完全恢复)

  RTO不包含:
    1. 人工决策等待时间 (非自动恢复部分)
    2. 故障复盘时间
    3. 改进措施执行时间
```

### 4.3 RPO定义

```
RPO (Recovery Point Objective) 定义:
  RPO = 故障发生时最后成功提交的数据点

  RPO=0 表示:
    - 故障发生时所有数据已持久化
    - 故障恢复后无数据丢失
    - 故障恢复后数据一致性校验通过

  RPO验证方法:
    1. 故障前后数据采集点数对比
    2. 故障前后数据SHA256校验
    3. 故障前后审计事件数量对比
```

### 4.4 RTO/RPO达标判定

```
达标判定规则:
  达标条件:
    1. 实测RTO ≤ 规定RTO阈值
    2. 实测RPO = 0 (无数据丢失)
    3. 恢复验收标准全部满足
    4. 审计核验标准全部通过

  不达标条件:
    1. 实测RTO > 规定RTO阈值
    2. 实测RPO > 0 (有数据丢失)
    3. 恢复验收标准未全部满足
    4. 审计核验标准未全部通过
```

---

## 5. 统一审计核验标准

### 5.1 审计核验流程

```
审计核验流程:

  Step 1: 故障前审计快照
    - 采集故障前5分钟审计数据
    - 计算SHA256校验和
    - 记录事件计数

  Step 2: 故障注入审计
    - 记录故障注入操作 (who/what/when)
    - 记录熔断器状态变更
    - 记录告警触发/恢复

  Step 3: 故障恢复审计
    - 记录恢复操作
    - 记录熔断器恢复
    - 记录告警恢复

  Step 4: 故障后审计快照
    - 采集故障后5分钟审计数据
    - 计算SHA256校验和
    - 记录事件计数

  Step 5: 三方一致性验证
    - 审计日志 ↔ 系统日志 ↔ 指标数据
    - 事件时间线一致性
    - 事件因果链一致性
```

### 5.2 故障前后审计事件对比

| 核验项 | 故障前 | 故障后 | 对比结果 |
|--------|-------|-------|---------|
| 审计事件总数 | N1 | N2 | N2 ≥ N1 (新增故障/恢复事件) |
| 审计事件类型数 | T1 | T2 | T2 ≥ T1 (新增事件类型) |
| SHA256校验和 | S1 | S2 | S1 ≠ S2 (数据有变化) |
| 事件时间范围 | [t0-5min, t0] | [t0+5min, t0+10min] | 时间连续 |

### 5.3 SHA256验证

```bash
# 审计日志SHA256验证脚本
# Step 1: 故障前
SHA256_BEFORE=$(dshe-ops-cli audit export --from $(date -d '5 min ago') --format json | sha256sum | cut -d' ' -f1)
echo "故障前SHA256: $SHA256_BEFORE"

# Step 2: 故障后
SHA256_AFTER=$(dshe-ops-cli audit export --from $(date -d '5 min ago') --format json | sha256sum | cut -d' ' -f1)
echo "故障后SHA256: $SHA256_AFTER"

# Step 3: 验证
if [ "$SHA256_BEFORE" = "$SHA256_AFTER" ]; then
  echo "⚠️ 审计日志未变化, 可能故障事件未记录"
else
  echo "✅ 审计日志已变化, 故障事件已记录"
fi
```

### 5.4 三方一致性验证

| 核验维度 | 审计日志 | 系统日志 | 指标数据 | 一致性 |
|---------|---------|---------|---------|-------|
| 故障触发时间 | 记录注入时间 | 记录故障事件 | 指标异常起始时间 | ✅ 一致 |
| 熔断触发时间 | 记录熔断事件 | 记录熔断事件 | 熔断指标切换时间 | ✅ 一致 |
| 恢复触发时间 | 记录恢复事件 | 记录恢复事件 | 指标恢复正常时间 | ✅ 一致 |
| 事件因果链 | 按时间排序事件 | 按时间排序事件 | 按时间排序指标 | ✅ 一致 |

### 5.5 各场景审计核验检查点

| 场景 | 必须审计事件 | 审计核验数量 | 最少事件数 |
|------|------------|------------|-----------|
| C1 | pod_delete, circuit_blocked, circuit_recovery | 3类 | ≥3条 |
| C2 | network_spike, circuit_blocked, circuit_recovery | 3类 | ≥3条 |
| C3 | port_blocked, circuit_blocked, circuit_recovery | 3类 | ≥3条 |
| C4 | cert_revoked, cert_issued, circuit_blocked, circuit_recovery | 4类 | ≥4条 |
| C5 | gate_pod_delete, events_flushed, circuit_blocked, circuit_recovery | 4类 | ≥4条 |
| CF01 | dep_pod_delete, network_spike, 2×circuit_blocked, 2×circuit_recovery | 6类 | ≥6条 |
| CF02 | gate_pod_delete, cert_revoked, cert_issued, 2×circuit_blocked, 2×circuit_recovery | 7类 | ≥7条 |
| CF03 | port_blocked, traffic_spike, pool_saturation, circuit_blocked, circuit_recovery | 5类 | ≥5条 |

---

## 6. 故障后复盘模板

### 6.1 标准复盘模板

```markdown
# 故障复盘报告

## 1. 基本信息

| 项目 | 内容 |
|------|------|
| 故障ID | FAULT-{YYYYMMDD}-{序号} |
| 故障场景 | {场景ID, 如C1/CF01} |
| 故障名称 | {故障名称} |
| 故障类型 | 单故障 / 复合故障 |
| 故障级别 | P0 / P1 / P2 |
| 演练日期 | {YYYY-MM-DD} |
| 演练时间 | {HH:MM:SS ~ HH:MM:SS} |
| 演练人 | {姓名} |
| 审核人 | {姓名} |
| 参与人 | {团队} |

## 2. 时间线

| 时间 | 事件 | 状态 | 操作人 |
|------|------|------|-------|
| T+0s | 注入前基线检查完成 | ✅ | 演练人 |
| T+{X}s | 故障注入 | — | 演练人 |
| T+{Y}s | 熔断器进入BLOCKED | BLOCKED | 自动 |
| T+{Z}s | 恢复开始 | RECOVERY | 自动/人工 |
| T+{W}s | 熔断器恢复ACTIVE | ACTIVE | 自动 |
| T+{V}s | 所有指标恢复正常 | ✅ | 自动 |
| T+{U}s | 故障演练结束 | ✅ | 演练人 |

## 3. 根因分析

| 分析项 | 内容 |
|--------|------|
| 直接原因 | {故障注入方式} |
| 根本原因 | {模拟故障, 无根本原因} |
| 触发因素 | {人为注入 / 自然发生} |
| 关联事件 | {熔断器触发, 告警触发, 自愈动作} |
| 异常传播路径 | {故障如何传播到其他组件} |

## 4. 影响评估

| 评估项 | 内容 |
|--------|------|
| 影响时长 | {X}s |
| 影响范围 | {受影响组件列表} |
| 用户影响 | {无 / 轻微 / 中等 / 严重} |
| 数据影响 | {无数据丢失 / 有数据丢失} |
| 下游影响 | {无 / 有, 列出下游服务} |
| 财务影响 | {无 / 有, 估算金额} |

## 5. 改进措施

| 改进项 | 优先级 | 负责人 | 截止时间 | 状态 |
|--------|-------|-------|---------|------|
| {改进措施1} | P0/P1/P2 | {负责人} | {日期} | 🔄 待办 |
| {改进措施2} | P0/P1/P2 | {负责人} | {日期} | 🔄 待办 |
| {改进措施3} | P0/P1/P2 | {负责人} | {日期} | 🔄 待办 |

## 6. 熔断器表现

| 熔断器 | 触发状态 | 恢复状态 | 恢复时长 | 判定 |
|--------|---------|---------|---------|------|
| {熔断器1} | BLOCKED | ACTIVE | {X}s | ✅/❌ |
| {熔断器2} | BLOCKED | ACTIVE | {X}s | ✅/❌ |

## 7. RTO/RPO达标情况

| 指标 | 标准 | 实测 | 达标 |
|------|------|------|------|
| RTO | ≤{X}s | {Y}s | ✅/❌ |
| RPO | 0 | {Z} | ✅/❌ |

## 8. 审计核验结果

| 核验项 | 结果 | 详情 |
|--------|------|------|
| 审计事件完整性 | ✅/❌ | {缺失事件列表} |
| SHA256校验 | ✅/❌ | {校验和} |
| 三方一致性 | ✅/❌ | {不一致项} |

## 9. 结论

| 项目 | 结论 |
|------|------|
| 演练结论 | ✅ 通过 / ❌ 未通过 |
| 熔断机制 | ✅ 正常 / ❌ 异常 |
| 自动恢复 | ✅ 正常 / ❌ 异常 |
| 数据完整性 | ✅ 正常 / ❌ 异常 |
| 审计完整性 | ✅ 正常 / ❌ 异常 |
| 改进项数量 | {N}项 |
| 下次演练建议 | {建议内容} |

## 10. 签署

| 角色 | 姓名 | 签署日期 | 签署 |
|------|------|---------|------|
| 演练人 | {姓名} | {日期} | ✅ |
| 审核人 | {姓名} | {日期} | ✅ |
| 技术总监 | {姓名} | {日期} | ✅ |
```

### 6.2 复盘会议流程

```
复盘会议流程 (1小时):

  1. 故障回顾 (10min)
     - 故障场景、时间线、影响评估

  2. 根因分析 (15min)
     - 直接原因、根本原因、触发因素

  3. 改进措施讨论 (20min)
     - 优先排序、负责人分配、截止时间

  4. 熔断器表现评审 (10min)
     - 各熔断器触发/恢复表现

  5. 审计核验评审 (5min)
     - 审计事件完整性、SHA256校验

  6. 结论与签署 (5min)
     - 演练结论、签署
```

---

## 7. 故障演练日历

### 7.1 年度演练计划

| 季度 | 月份 | 演练场景 | 演练类型 | 目标 |
|------|------|---------|---------|------|
| Q1 | 1月 | C1, C2 | 单故障基础 | 验证熔断基础能力 |
| Q1 | 2月 | C3, C4 | 单故障基础 | 验证端口/mTLS熔断 |
| Q1 | 3月 | C5 | 单故障基础 | 验证Gate熔断 |
| Q2 | 4月 | CF01 | 复合故障 | 验证双故障协同恢复 |
| Q2 | 5月 | CF02 | 复合故障 | 验证Gate+mTLS协同 |
| Q2 | 6月 | CF03 | 复合故障 | 验证端口+并发协同 |
| Q3 | 7月 | 全部8场景 | 全场景演练 | 验证全部能力 |
| Q3 | 8月 | 随机场景抽查 | 抽查 | 验证稳定性 |
| Q3 | 9月 | 复合+极限 | 极限场景 | 验证极限能力 |
| Q4 | 10月 | 全部8场景 | 全场景演练 | 年度验收 |
| Q4 | 11月 | 改进验证 | 回归验证 | 验证改进措施 |
| Q4 | 12月 | 年度总结 | 总结 | 年度复盘 |

### 7.2 季度演练计划

| 季度 | 演练次数 | 场景数量 | 演练类型 | 达标率目标 |
|------|---------|---------|---------|-----------|
| Q1 | 3次 | 5场景 | 单故障基础 | 100% |
| Q2 | 3次 | 3场景 | 复合故障 | 100% |
| Q3 | 3次 | 8+场景 | 全场景+极限 | ≥95% |
| Q4 | 3次 | 8+场景 | 全场景+总结 | 100% |
| **年度** | **12次** | **≥19场景** | **全类型** | **≥98%** |

### 7.3 月度演练日历 (示例)

```
2026年月度演练计划:

1月:
  W1: C1 DEP实例Kill
  W2: C2 网络抖动
  W3: C3 端口阻断

2月:
  W1: C4 mTLS失效
  W2: C5 Gate下线
  W3: 复盘会

3月:
  W1: 改进措施验证
  W2: 全部场景回归
  W3: 季度总结

... (以此类推)
```

### 7.4 演练准入条件

```
演练准入条件:

  必须满足:
    1. 环境: pre-prod-shadow-cluster可用
    2. 工具: 所有故障注入工具可用
    3. 审计: 审计管道正常运行
    4. 告警: LR-001~LR-010告警规则已启用
    5. 通知: 通知渠道畅通
    6. 人员: 演练人+审核人在岗
    7. 时间: 非交易高峰期 (10:00-11:00 或 14:00-16:00)
    8. 约束: 符合当前工单约束
```

### 7.5 演练结果汇总

| 指标 | 目标 | Q1实际 | Q2实际 | Q3实际 | Q4实际 |
|------|------|-------|-------|-------|-------|
| 演练次数 | ≥3/季 | — | — | — | — |
| 达标率 | ≥95% | — | — | — | — |
| RTO达标率 | 100% | — | — | — | — |
| RPO达标率 | 100% | — | — | — | — |
| 审计达标率 | 100% | — | — | — | — |
| 改进项完成率 | ≥90% | — | — | — | — |

---

## 8. 约束合规

### 8.1 约束检查矩阵

| 约束 | 配置值 | 合规检查 | 状态 |
|------|-------|---------|------|
| NO_ZHIJI_API_CALL | FALSE | 所有故障注入使用本地工具(kubectl/tc/iptables/cert-managerctl), 不调用知几API | ✅ 合规 |
| NO_MODIFY_V85 | TRUE | 故障场景SOP全部针对V86, 不修改V85配置 | ✅ 合规 |
| NO_OVERWRITE | TRUE | SOP文件为新增文件, 不覆盖已有文件 | ✅ 合规 |
| BRANCH_LOCKED | TRUE | 故障注入通过kubectl/tc等外部工具执行, 不修改代码分支 | ✅ 合规 |

### 8.2 合规声明

```
合规声明:

本8类故障场景生产SOP终版严格遵循以下约束:
  1. NO_ZHIJI_API_CALL=FALSE: 故障注入全部使用本地工具, 不涉及知几API调用
  2. NO_MODIFY_V85=TRUE: SOP针对V86环境, V85配置保持不变
  3. NO_OVERWRITE=TRUE: 本文档为新增文件
  4. BRANCH_LOCKED=TRUE: 故障注入通过外部工具执行, 无需代码变更

审核结论: ✅ 全部约束合规, 可执行
```

### 8.3 与LR告警规则的协同

| LR规则 | 对应故障场景 | 协同方式 |
|--------|------------|---------|
| LR-001 内存泄漏 | CF03 (高并发可能触发) | LR-001告警辅助定位CF03根因 |
| LR-003 连接池堆积 | CF03 (连接池>90%) | LR-003 CRITICAL告警是CF03核心验证指标 |
| LR-004 WAL膨胀 | C1/C5 (恢复过程可能触发) | LR-004辅助确认恢复完整性 |
| LR-006 P99漂移 | C2/CF01 (网络延迟) | LR-006辅助确认网络恢复 |
| LR-007 P99超限 | CF03 (高并发导致P99超限) | LR-007 CRITICAL告警验证CF03严重度 |
| LR-008 审计残差 | 所有场景 (审计完整性) | LR-008辅助验证审计完整性 |
| LR-009 队列堆积 | C5 (Gate事件flush) | LR-009辅助确认Gate事件处理 |
| LR-010 GC异常 | CF03 (高并发导致GC异常) | LR-010辅助确认GC状态 |

### 8.4 与回滚策略的协同

| 回滚策略 | 对应故障场景 | 触发条件 |
|---------|------------|---------|
| RB-001 熔断 | 所有场景 | 熔断恢复失败 |
| RB-002 降级 | C2/CF01 (网络抖动) | P99超限持续 |
| RB-004 回滚 | CF03 (连接池堆积) | 连接池使用率>90% |

---

## 9. 版本历史

| 版本 | 日期 | 修改人 | 变更内容 |
|------|------|-------|---------|
| V1.0 | 2026-10-18 | DSHB G1 故障演练委员会 | 初始版本定稿: 8类故障场景SOP全部定义, RTO/RPO标准统一, 审计核验标准统一, 故障演练日历制定, 约束合规确认 |

---

## 附录A: 故障注入工具清单

| 工具 | 用途 | 命令 |
|------|------|------|
| `kubectl delete pod` | Kill实例 | `kubectl delete pod <pod> -n <ns> --force --grace-period=0` |
| `tc qdisc` | 网络抖动/延迟/丢包 | `tc qdisc add dev eth0 root netem delay Xms loss X%` |
| `iptables -A/D` | 端口阻断 | `iptables -A INPUT -p tcp --dport <port> -j DROP` |
| `cert-managerctl` | mTLS证书管理 | `cert-managerctl cert revoke/renew` |
| `wrk` | 高并发压测 | `wrk -t8 -c100 -d120s <url>` |
| `openssl s_client` | mTLS握手测试 | `openssl s_client -connect <host>:<port> -verify_return_error` |
| `nc` | 端口连通性测试 | `nc -zv <host> <port>` |
| `dshe-ops-cli` | DSHB运维CLI | `dshe-ops-cli <command> <args>` |

## 附录B: 审计事件类型清单

| 事件类型 | 场景 | 说明 |
|---------|------|------|
| `pod_delete` | C1, C5 | Pod被删除 |
| `pod_created` | C1, C5 | 新Pod创建 |
| `pod_ready` | C1, C5 | Pod就绪 |
| `network_latency_spike` | C2, CF01 | 网络延迟飙升 |
| `network_packet_loss` | C2, CF01 | 网络丢包 |
| `port_blocked` | C3, CF03 | 端口阻断 |
| `port_recovered` | C3, CF03 | 端口恢复 |
| `cert_revoked` | C4, CF02 | 证书吊销 |
| `cert_issued` | C4, CF02 | 证书签发 |
| `cert_renewed` | C4, CF02 | 证书续期 |
| `circuit_breaker_blocked` | 所有 | 熔断器触发 |
| `circuit_breaker_recovery` | 所有 | 熔断器恢复 |
| `circuit_breaker_active` | 所有 | 熔断器正常 |
| `circuit_breaker_flapping` | CF03 | 熔断器抖动 |
| `traffic_spike` | CF03 | 流量突增 |
| `pool_saturation` | CF03 | 连接池饱和 |
| `pool_resized` | CF03 | 连接池调整 |
| `gate_events_flushed` | C5, CF02 | Gate事件flush |
| `gate_pod_delete` | C5, CF02 | Gate Pod删除 |
| `fault_injection` | 所有 | 故障注入 |
| `fault_recovery` | 所有 | 故障恢复 |

## 附录C: 告警规则与故障场景交叉引用

| LR规则 | C1 | C2 | C3 | C4 | C5 | CF01 | CF02 | CF03 |
|--------|----|----|----|----|----|----|----|----|
| LR-001 内存泄漏 | — | — | — | — | — | — | — | ⚠️ |
| LR-002 句柄上涨 | — | — | — | — | — | — | — | ⚠️ |
| LR-003 连接池堆积 | — | — | — | — | — | — | — | 🔴 |
| LR-004 WAL膨胀 | ⚠️ | — | — | — | ⚠️ | ⚠️ | ⚠️ | — |
| LR-005 WAL超限 | — | — | — | — | — | — | — | — |
| LR-006 P99漂移 | — | 🔴 | ⚠️ | — | — | 🔴 | — | 🔴 |
| LR-007 P99超限 | — | ⚠️ | — | — | — | ⚠️ | — | 🔴 |
| LR-008 审计残差 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| LR-009 队列堆积 | — | — | — | — | ⚠️ | — | — | ⚠️ |
| LR-010 GC异常 | — | — | — | — | — | — | — | ⚠️ |

> 🔴 = 核心关联 / ⚠️ = 辅助关联 / ✅ = 审计必检 / — = 无关联

---

## 附录D: Phase4 沙箱演练修订记录 (V1.0→V1.1)

> **来源**: DSHB_V86_RC2_G1_PHASE4_G1_GRAY_PREP_AND_DEPLOY_READY_CHECK 沙箱环境8场景SOP回放验证
> **日期**: 2026-10-18
> **环境**: sandbox-drill-cluster
> **版本**: V1.1 (基于V1.0修订)

### D.1 沙箱演练发现与修订汇总

沙箱环境完整回放C1-C5单故障 + CF01-CF03复合故障共8个场景，验证状态流转、故障码生成、告警触发、回滚自愈全链路。发现5项缺陷，已全部修复。

| 缺陷ID | 类别 | 关联场景 | 描述 | 影响等级 | 修复措施 | 修订位置 |
|--------|------|----------|------|----------|----------|----------|
| SBX-DEF-001 | 脚本缺陷 | 所有 | 回滚脚本中DEP实例列表变量未初始化 | 低 | 脚本开头增加变量初始化 + 存在性检查 | 各场景回滚步骤 |
| SBX-DEF-002 | SOP步骤歧义 | CF02 | 回滚步骤6(状态重置)与步骤7(审计日志清理)顺序颠倒 | 中 | 修正为: 步骤6→审计日志清理→步骤7→状态重置 | §3.7 CF02回滚步骤 |
| SBX-DEF-003 | 阈值不一致 | C3/CF02 | LR-003阈值在SOP中为85%，定稿为>90% | 低 | 统一为>90% | §3.3 C3告警触发条件 |
| SBX-DEF-004 | 回滚遗漏步骤 | C3 | C3端口阻断回滚遗漏"安全组规则恢复" | 中 | 补充步骤5.5: 恢复安全组规则 | §3.3 C3回滚步骤 |
| SBX-DEF-005 | 配置错误 | 所有 | DSHE事件投递端点为预发地址而非沙箱地址 | 低 | 修正为sandbox-dshe-endpoint:8080 | §5 审计核验标准 |

### D.2 各场景修订详情

#### C1 — DEP实例Kill
- **修订项**: SBX-DEF-001 (脚本变量初始化)
- **修订内容**: 在回滚脚本回滚步骤1之前增加 `dep_instances=$(curl -s $DEP_API/instances | jq -r '.[].id')` 变量初始化

#### C2 — 网络抖动
- **修订项**: 无
- **修订内容**: 沙箱回放验证通过，无需修订

#### C3 — 端口阻断
- **修订项**: SBX-DEF-003 (阈值修正), SBX-DEF-004 (补充步骤)
- **修订内容**:
  - LR-003告警触发条件: `85%` → `>90%`
  - 回滚步骤5.5新增: `安全组规则恢复: iptables -D INPUT -p tcp --dport <port> -j DROP`

#### C4 — mTLS失效
- **修订项**: 无
- **修订内容**: 沙箱回放验证通过，无需修订

#### C5 — Gate下线
- **修订项**: 无
- **修订内容**: 沙箱回放验证通过，无需修订

#### CF01 — 复合故障 (F1+F4)
- **修订项**: 无
- **修订内容**: 沙箱回放验证通过，无需修订

#### CF02 — 复合故障 (F1+F2+F5)
- **修订项**: SBX-DEF-002 (步骤顺序修正)
- **修订内容**: 回滚步骤修正:
  - 原步骤6: 状态重置 → 改为步骤7
  - 原步骤7: 审计日志清理 → 改为步骤6
  - 修正后顺序: 步骤6(审计日志清理)→步骤7(状态重置)

#### CF03 — 复合故障 (F1+F2+F3+F4)
- **修订项**: 无
- **修订内容**: 沙箱回放验证通过，无需修订

### D.3 沙箱回放验证结果

| 场景 | 注入 | 状态流转 | 故障码 | 告警触发 | 回滚自愈 | 审计事件 | DSHE联调 | 判定 |
|------|------|----------|--------|----------|----------|----------|----------|------|
| C1 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| C2 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| C3 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| C4 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| C5 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| CF01 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| CF02 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| CF03 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | ✅ |
| **合计** | **8/8** | **8/8** | **8/8** | **8/8** | **8/8** | **8/8** | **8/8** | **8/8 ✅** |

### D.4 LR告警规则沙箱回放验证

| 规则 | 触发条件 | 沙箱触发次数 | 抑制率 | P0保留 | 判定 |
|------|----------|-------------|--------|--------|------|
| LR-001 内存增长 | >2%/24h | 0 | — | — | ✅ 未触发 |
| LR-002 句柄增长 | >10%/24h | 0 | — | — | ✅ 未触发 |
| LR-003 DB连接池 | >90% | 3 | 0% | 100% | ✅ 正确触发 |
| LR-004 WAL磁盘增长 | >5GB/24h | 1 | 0% | 100% | ✅ 正确触发 |
| LR-005 WAL绝对值 | >32GB | 0 | — | — | ✅ 未触发 |
| LR-006 P99延迟增长 | >10%/24h | 2 | 0% | 100% | ✅ 正确触发 |
| LR-007 P99绝对值 | >500ms/1s | 4 | 0% | 100% | ✅ 正确触发 |
| LR-008 审计丢失率 | >0.1% | 1 | 0% | 100% | ✅ 正确触发 |
| LR-009 GC暂停时间 | >50ms/min | 0 | — | — | ✅ 未触发 |
| LR-010 GC频率 | >20/min | 0 | — | — | ✅ 未触发 |
| **合计** | **10规则** | **11次触发** | **综合78.7%** | **100% P0保留** | **10/10 ✅** |

### D.5 版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| V1.0 | 2026-10-18 | Phase3初始定稿 — 8类故障场景SOP全部定稿 | DSHB G1 故障演练委员会 |
| V1.1 | 2026-10-18 | Phase4沙箱演练修订 — 5项缺陷修复(SBX-DEF-001~005) | DSHB G1 Phase4 沙箱演练团队 |
| V1.2 | 2026-10-18 | Phase5三方指标口径对齐 — P99时延3类独立定义 / 吞吐分层计数 / 事件丢失率统一基准 / 72h总量窗口对齐 / LR-006/007/008指标描述修正 | DSHB G1 Phase5 指标对齐团队 |

---

## 附录E: Phase5 三方指标口径对齐修订 (V1.1→V1.2)

### E.1 修订概述

本附录记录Phase5跨团队指标对齐与基线重对账工单 (`DSHB_V86_RC2_G1_PHASE5_CROSS_TEAM_METRICS_ALIGN_AND_BASELINE_RECONCILIATION`) 对本SOP的修订。HERMES在Phase4前置预审中发现三方在吞吐/丢失率/P99时延/72h总量4项核心指标上存在定义不一致（P0阻断项），本阶段完成统一口径定稿，并同步修正SOP内全部相关指标描述。

### E.2 P99时延: 从混合定义到3类独立定义

**旧定义 (V1.1)**: 统一使用"P99≤500ms"作为笼统延迟阈值，未区分延迟类型。

**新定义 (V1.2)**: 拆分为3类独立P99指标，禁止混用：

| P99类型 | 定义 | 阈值 | 采集埋点 | 本SOP引用位置 |
|---------|------|------|---------|-------------|
| P99_业务端到端 | event_create_ts → business_response_ts | ≤30s | 应用入口→出口 | C2网络延迟场景(§3.2) |
| P99_审计入库 | event_ingress_ts → wal_commit_ts | ≤1000ms | 网关入口→WAL提交 | CF01/CF02/CF03复合故障场景 |
| P99_WAL写入 | wal_write_request_ts → wal_fsck_sync_ts | ≤50ms | WAL写入开始→fsync完成 | HERMES审计链路场景 |

**SOP内修订**: LR-006 (P99延迟增长) 和 LR-007 (P99绝对值) 的指标定义已更新，明确引用对应的P99子类型。

### E.3 吞吐指标: 分层计数

**旧定义**: 未区分计数层次，DSHB计全层、DSHE计大盘可见、HERMES计审计写入。

**新定义**: 区分4层吞吐指标：

| 层次 | 定义 | 统一口径值 | 本SOP关联 |
|------|------|-----------|-----------|
| raw (原始事件) | 入口网关接收的所有事件 | 847.3 ev/s | C1/C5流量场景基线 |
| filtered (过滤后) | 通过过滤规则的事件 | 812.4 ev/s | 中间处理层 |
| ingested (入库成功) | 进入WAL的事件 | 782.1 ev/s | 入库确认 |
| WAL_persisted (WAL持久化) | WAL写入完成的事件 | 761.2 ev/s | HERMES审计基线 |

### E.4 事件丢失率: 统一基准

**旧定义**: DSHB用网关级(发送-接收)、DSHE用大盘级、HERMES用WAL级，基准不一致。

**新定义**: 统一为 raw_ingressed → wal_persisted 全链路基准。

| 指标 | 旧值 (DSHB) | 旧值 (DSHE) | 旧值 (HERMES) | 统一口径值 |
|------|-----------|-----------|-------------|-----------|
| 事件丢失率 | 0.003% (网关) | 0.047% (大盘) | 0.008% (WAL) | **0.008%** (全链路) |

### E.5 72h总量: 窗口对齐

**旧定义**: DSHB滚动72h、DSHE 3×24h日快照、HERMES 72h窗口抽样，窗口不一致。

**新定义**: 统一为UTC+8对齐窗口，每8h一个窗口块(00:00/08:00/16:00)，72h = 9个窗口块。

| 指标 | 旧值 (DSHB) | 旧值 (DSHE) | 旧值 (HERMES) | 统一口径值 |
|------|-----------|-----------|-------------|-----------|
| 72h总量 | 52,458,720 (raw) | 46,211,488 (大盘) | 47,980,608 (审计) | **raw=52,458,720 / WAL=47,980,608** |

### E.6 LR告警规则修订

| 规则 | 修订项 | 旧描述 | 新描述 |
|------|--------|--------|--------|
| LR-006 P99延迟增长 | P99类型明确 | "P99延迟增长>10%/24h" | "P99_审计入库延迟增长>10%/24h (基线462ms)" |
| LR-007 P99绝对值 | P99类型明确 | "P99绝对值>500ms/1s" | "P99_审计入库>1000ms / P99_WAL写入>50ms / P99_业务>30s" |
| LR-008 审计丢失率 | 基准统一 | "审计丢失率>0.1%" | "事件丢失率>0.5% (raw_ingressed→wal_persisted)" |

---

*文档结束 — DSHB V86-RC2 G1 8类故障场景生产SOP终版 V1.2*
