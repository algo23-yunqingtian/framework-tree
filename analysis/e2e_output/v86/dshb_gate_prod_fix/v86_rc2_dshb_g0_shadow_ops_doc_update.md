# G0 影子运维文档更新

> **工单编号**: DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION / T3.6
> **基线文档**: `v86_rc2_dshb_gate_prod_adapt_spec_update.md` V2.0 + `v86_rc2_b_dep001_ops_manual.md` V1.0
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE / NO_ZHIJI_API_CALL=FALSE
> **文档版本**: V2.0
> **编制日期**: 2026-10-17
> **状态**: `DSHB_PROD_PHASE_G0_SHADOW_TRAFFIC_ISOLATION_DONE=PENDING`

---

## 目录

1. [更新概述](#1-更新概述)
2. [DEP-001 运维手册更新](#2-dep-001-运维手册更新)
3. [Gate V5 适配规范更新](#3-gate-v5-适配规范更新)
4. [新增：流量镜像运维](#4-新增流量镜像运维)
5. [新增：路由规则运维](#5-新增路由规则运维)
6. [新增：回调接口运维](#6-新增回调接口运维)
7. [新增：影子资源隔离运维](#7-新增影子资源隔离运维)
8. [故障排查指南更新](#8-故障排查指南更新)
9. [监控告警更新](#9-监控告警更新)
10. [应急预案更新](#10-应急预案更新)
11. [附录](#11-附录)

---

## 1. 更新概述

### 1.1 更新背景

G0 影子投产阶段引入了以下新能力，需要同步更新运维文档：

- **T3.1**: G0 影子流量路由切分规则配置
- **T3.2**: DEP-001 流量镜像采集规则落地
- **T3.3**: Gate V5 动态状态回调闭环开发
- **T3.4**: G0 影子环境资源隔离加固
- **T3.5**: 底层 G0 影子全链路验证

### 1.2 更新目标

| 目标 | 文档 | 章节 | 状态 |
|------|------|------|------|
| DEP-001 运维手册更新 | `v86_rc2_b_dep001_ops_manual.md` | 新增 §17-§20 | ✅ |
| Gate V5 适配规范更新 | `v86_rc2_dshb_gate_prod_adapt_spec_update.md` | 新增 §10-§13 | ✅ |
| 新增：流量镜像运维 | 本文档 | §4 | ✅ |
| 新增：路由规则运维 | 本文档 | §5 | ✅ |
| 新增：回调接口运维 | 本文档 | §6 | ✅ |
| 新增：影子资源隔离运维 | 本文档 | §7 | ✅ |
| 故障排查指南更新 | 本文档 | §8 | ✅ |
| 监控告警更新 | 本文档 | §9 | ✅ |
| 应急预案更新 | 本文档 | §10 | ✅ |

### 1.3 变更摘要

| 变更类型 | 数量 | 说明 |
|----------|------|------|
| 新增章节 | 5 | 流量镜像、路由规则、回调接口、资源隔离、故障排查 |
| 更新章节 | 3 | 监控告警、应急预案、版本演进 |
| 新增配置项 | 15 | 镜像/路由/回调/隔离相关配置 |
| 新增接口 | 5 | 镜像控制、路由配置、回调、审计、状态查询 |
| 新增指标 | 12 | 影子镜像 12 项 Prometheus 指标 |
| 新增告警 | 6 | 影子镜像/路由/回调/隔离告警 |
| 新增应急预案 | 4 | 镜像异常/路由异常/回调故障/隔离故障 |

---

## 2. DEP-001 运维手册更新

### 2.1 新增 §17: G0 影子流量镜像

#### 2.1.1 影子镜像概述

DEP-001 在 G0 影子阶段承担以下职责：

| 职责 | 说明 |
|------|------|
| 接收影子镜像流量 | 从 mirror-router 接收 10% 采样镜像流量 |
| 影子数据处理 | 独立处理影子流量，不影响生产数据 |
| 影子指标上报 | 上报影子流量指标至 DSHE L2 面板 |
| 影子审计事件 | 生成影子审计事件至 HERMES |

#### 2.1.2 影子镜像端口

| 端口 | 协议 | 用途 | 来源 |
|------|------|------|------|
| 9443 | HTTPS (TLS 1.3) | 影子流量接收 | mirror-router |
| 19000 | HTTP | Admin (Envoy 管理) | 本地 |
| 19090 | HTTP | 采集器上报 | mirror-collector |

#### 2.1.3 影子镜像流量处理

```bash
# 查看影子镜像流量
kubectl exec -n v86-shadow dep001 -- \
  curl -sk https://localhost:9443/metrics | grep shadow_mirror

# 查看影子镜像统计
kubectl exec -n v86-shadow dep001 -- \
  curl -sk https://localhost:9443/metrics | grep dshb_shadow_mirror

# 验证影子流量接收
kubectl exec -n v86-shadow dep001 -- \
  curl -sk -H 'x-dep-version:v86-shadow' \
  -H 'x-shadow-request-id:test-uuid' \
  https://localhost:9443/commodity/api/series
```

#### 2.1.4 影子镜像配置

```yaml
# DEP-001 影子镜像配置 (ConfigMap 新增字段)
shadow_mirror:
  enabled: true
  port: 9443
  max_connections: 500
  rate_limit:
    requests_per_unit: 1000
    unit: minute
    burst: 200
  health_check:
    endpoint: /healthz
    interval_seconds: 30
    timeout_seconds: 5
    failure_threshold: 3
```

### 2.2 新增 §18: 影子环境运维命令

#### 2.2.1 状态检查命令

```bash
# DEP-001 影子实例状态
kubectl get pods -n v86-shadow -l app=dep001
kubectl describe pod -n v86-shadow dep001
kubectl logs -n v86-shadow dep001 --tail=50

# 影子镜像状态
kubectl get pods -n mirror-ns -l app=mirror-router
kubectl get pods -n mirror-ns -l app=mirror-collector
kubectl logs -n mirror-ns mirror-router --tail=50

# Gate 回调状态
kubectl get pods -n gate-ns -l app=gate-v5-gray-callback
kubectl logs -n gate-ns gate-v5-gray-callback --tail=50
```

#### 2.2.2 健康检查命令

```bash
# DEP-001 影子健康检查
kubectl exec -n v86-shadow dep001 -- \
  curl -sk https://localhost:9443/healthz

# Mirror Router 健康检查
kubectl exec -n mirror-ns mirror-router -- \
  curl -s http://localhost:8080/health

# Mirror Collector 健康检查
kubectl exec -n mirror-ns mirror-collector -- \
  curl -s http://localhost:19090/health

# Gate 回调健康检查
kubectl exec -n gate-ns gate-v5-gray-callback -- \
  curl -s http://localhost:9090/api/v1/gate/callback/health
```

#### 2.2.3 资源检查命令

```bash
# 影子集群资源使用率
kubectl top pods -n v86-shadow
kubectl top pods -n mirror-ns
kubectl top pods -n gate-ns

# 节点资源使用率
kubectl top nodes

# 磁盘使用率
kubectl exec -n v86-shadow dep001 -- df -h
```

### 2.3 新增 §19: 影子镜像启停操作

#### 2.3.1 启动影子镜像

```bash
# 方法 1: API 启动
curl -X POST http://mirror-router.mirror-ns.svc:8080/api/v1/mirror/control/start \
  -H 'Content-Type: application/json' \
  -d '{"rate": 10.0, "stage": "G0"}'

# 方法 2: kubectl 配置
kubectl patch cm shadow-routing-config -n mirror-ns \
  -p '{"data":{"shadow_mirror_config.yaml":"enabled: true\nsampling_rate_pct: 10.0"}}'
```

#### 2.3.2 停止影子镜像

```bash
# 方法 1: API 停止
curl -X POST http://mirror-router.mirror-ns.svc:8080/api/v1/mirror/control/stop \
  -H 'Content-Type: application/json' \
  -d '{"reason": "手动停止"}'

# 方法 2: ConfigMap 配置
kubectl patch cm shadow-routing-config -n mirror-ns \
  -p '{"data":{"shadow_mirror_config.yaml":"enabled: false"}}'
```

#### 2.3.3 调整采样率

```bash
# 调整采样率至 20%
curl -X PUT http://mirror-router.mirror-ns.svc:8080/api/v1/mirror/control/rate \
  -H 'Content-Type: application/json' \
  -d '{"rate": 20.0}'
```

---

## 3. Gate V5 适配规范更新

### 3.1 新增 §10: G0 影子阶段 Gate 行为

#### 3.1.1 G0 影子阶段 Gate 状态映射

| 灰度阶段 | Gate 状态 | DEP 巡检 | 影子镜像 | 采样率 | 说明 |
|----------|----------|---------|---------|--------|------|
| G0 (影子) | READY | 运行 | 运行 | 10% | 影子测试 |
| G0 (ROLLBACK) | NOT_READY | 停止 | 停止 | 0% | 回滚 |
| G1 (单品种) | READY | 运行 | 运行 | 20% | 单品种 |
| G2 (小范围) | READY | 运行 | 运行 | 30% | 小范围 |
| G3 (中范围) | READY | 运行 | 运行 | 50% | 中范围 |
| G4 (大范围) | READY | 运行 | 运行 | 80% | 大范围 |
| G5 (全量) | READY | 停止 | 停止 | 100% | 全量 |

#### 3.1.2 G0 影子阶段 Gate 联动规则

| HERMES 决策 | Gate 动作 | DEP 巡检 | 影子镜像 | 采样率 |
|------------|----------|---------|---------|--------|
| ADVANCE (G0→G1) | READY | START | START | 20% |
| HOLD | WARN | CONTINUE | CONTINUE | 不变 |
| OBSERVE | WARN | CONTINUE | CONTINUE | 不变 |
| ROLLBACK | NOT_READY | STOP | STOP | 不变 |
| COMPLETE | READY | STOP | STOP | 不变 |

### 3.2 新增 §11: Gate 回调接口运维

#### 3.2.1 回调接口检查

```bash
# 检查回调服务状态
kubectl get pods -n gate-ns -l app=gate-v5-gray-callback

# 查询 Gate 状态
curl http://gate-callback:9090/api/v1/gate/callback/status

# 查询审计统计
curl http://gate-callback:9090/api/v1/gate/callback/audit/stats

# 手动触发决策
curl -X POST http://gate-callback:9090/api/v1/gate/callback/decision \
  -H 'Content-Type: application/json' \
  -d '{
    "timestamp": "2026-10-17T10:00:00Z",
    "decision": "ADVANCE",
    "decision_reason": "G0 观测完成",
    "current_stage": "G0",
    "next_stage": "G1"
  }'
```

### 3.3 新增 §12: Gate 回调告警规则

| 告警名 | 条件 | 级别 | 说明 |
|--------|------|------|------|
| Gate Callback Down | `gate_callback_health == 0` | CRITICAL | 服务不可用 |
| Decision Fail Rate High | `failed / total > 10%` | HIGH | 决策失败率过高 |
| Gate Status NOT_READY | `gate_callback_gate_status == 2` | HIGH | Gate 处于 NOT_READY |
| DEP Probe Stopped | `gate_callback_dep_probe_running == 0` | WARN | DEP 巡检意外停止 |
| Shadow Mirror Stopped | `gate_callback_shadow_mirror_running == 0` | WARN | 影子镜像意外停止 |
| Request Latency High | `p95_request_duration > 1000ms` | WARN | 请求延迟过高 |

### 3.4 新增 §13: Gate 回调部署更新

#### 3.4.1 新增环境变量

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `SHADOW_MIRROR_API` | `http://mirror-router.mirror-ns.svc:8080` | 影子镜像 API |
| `DEDUP_WINDOW` | `60` | 事件去重窗口 (秒) |
| `RETRY_MAX` | `3` | 最大重试次数 |
| `GATE_BASE_URL` | `https://gate.svc:9090` | Gate API 地址 |

#### 3.4.2 新增探针

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/gate/callback/health
    port: 9090
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/v1/gate/callback/health
    port: 9090
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 2
```

---

## 4. 新增：流量镜像运维

### 4.1 流量镜像组件架构

| 组件 | 命名空间 | Pod 数 | 端口 | 用途 |
|------|---------|--------|------|------|
| mirror-router | mirror-ns | 2 | 8080 | 流量镜像路由 |
| mirror-collector | mirror-ns | 1 | 19090 | 镜像流量采集 |

### 4.2 流量镜像运维命令

```bash
# 查看镜像路由状态
kubectl get pods -n mirror-ns -l app=mirror-router
kubectl logs -n mirror-ns mirror-router --tail=100

# 查看镜像采集器状态
kubectl get pods -n mirror-ns -l app=mirror-collector
kubectl logs -n mirror-ns mirror-collector --tail=100

# 查看镜像配置
kubectl get cm shadow-routing-config -n mirror-ns -o yaml

# 查看镜像统计
curl http://mirror-router.mirror-ns.svc:8080/api/v1/mirror/stats

# 查看镜像采样率
curl http://mirror-router.mirror-ns.svc:8080/api/v1/mirror/control/status
```

### 4.3 流量镜像常见操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 查看镜像状态 | `curl /api/v1/mirror/control/status` | 查询镜像状态 |
| 启动镜像 | `POST /api/v1/mirror/control/start` | 启动镜像 |
| 停止镜像 | `POST /api/v1/mirror/control/stop` | 停止镜像 |
| 调整采样率 | `PUT /api/v1/mirror/control/rate` | 调整采样率 |
| 查看统计 | `GET /api/v1/mirror/stats` | 查看统计 |
| 查看配置 | `GET /api/v1/mirror/config` | 查看配置 |

### 4.4 流量镜像故障排查

| 故障现象 | 排查步骤 | 常见原因 | 解决方案 |
|----------|---------|---------|---------|
| 镜像流量为零 | 1. 检查镜像状态<br>2. 检查路由配置<br>3. 检查 DEP 健康 | 镜像已停止 | 启动镜像 |
| 镜像流量异常高 | 1. 检查采样率<br>2. 检查流量来源 | 采样率配置错误 | 调整采样率 |
| 镜像延迟过高 | 1. 检查 DEP 负载<br>2. 检查网络带宽 | DEP 过载 | 降采样率 |
| 镜像丢弃率高 | 1. 检查 QPS 限制<br>2. 检查网络 | 限流触发 | 调整 burst |

---

## 5. 新增：路由规则运维

### 5.1 路由规则架构

| 组件 | 配置方式 | 热加载 | 说明 |
|------|---------|--------|------|
| Envoy FilterChain | ConfigMap + 环境变量 | ✅ 热加载 | 流量镜像 FilterChain |
| K8s NetworkPolicy | YAML 文件 | ❌ 需重启 | 网络隔离策略 |
| ConfigMap | ConfigMap | ✅ 热加载 | 采样率/启停配置 |

### 5.2 路由规则运维命令

```bash
# 查看路由配置
kubectl get cm shadow-routing-config -n mirror-ns -o yaml

# 查看 NetworkPolicy
kubectl get netpol -A
kubectl describe netpol -n v86-shadow

# 验证路由规则
kubectl exec -n mirror-ns mirror-router -- \
  curl -H 'x-dep-version:v86-shadow' \
  http://localhost:8080/health

# 验证采样率
kubectl exec -n mirror-ns mirror-router -- \
  curl http://localhost:8080/api/v1/mirror/control/status
```

### 5.3 路由规则变更流程

| 步骤 | 操作 | 命令 | 验证 |
|------|------|------|------|
| 1 | 备份当前配置 | `kubectl get cm shadow-routing-config -o yaml > backup.yaml` | 确认备份 |
| 2 | 修改配置 | 编辑 ConfigMap | 检查语法 |
| 3 | 应用配置 | `kubectl apply -f shadow-routing-config.yaml` | 应用成功 |
| 4 | 验证配置 | `kubectl get cm shadow-routing-config` | 配置更新 |
| 5 | 验证效果 | 检查镜像流量/采样率 | 效果正确 |
| 6 | 回滚 (如需) | `kubectl apply -f backup.yaml` | 恢复 |

### 5.4 路由规则故障排查

| 故障现象 | 排查步骤 | 常见原因 | 解决方案 |
|----------|---------|---------|---------|
| 路由规则不生效 | 1. 检查 ConfigMap<br>2. 检查 Envoy 配置 | 配置语法错误 | 修复配置 |
| 路由规则生效异常 | 1. 检查采样率<br>2. 检查镜像目标 | 目标服务不可用 | 修复目标服务 |
| 路由规则热加载失败 | 1. 检查 Envoy 日志<br>2. 检查配置版本 | 配置版本冲突 | 回滚配置 |

---

## 6. 新增：回调接口运维

### 6.1 回调接口架构

| 组件 | 命名空间 | Pod 数 | 端口 | 用途 |
|------|---------|--------|------|------|
| gate-v5-gray-callback | gate-ns | 2 | 9090 | 灰度决策回调 |

### 6.2 回调接口运维命令

```bash
# 查看回调服务状态
kubectl get pods -n gate-ns -l app=gate-v5-gray-callback
kubectl describe pod -n gate-ns gate-v5-gray-callback

# 查看回调日志
kubectl logs -n gate-ns gate-v5-gray-callback --tail=100

# 查询 Gate 状态
curl http://gate-callback:9090/api/v1/gate/callback/status

# 查询审计统计
curl http://gate-callback:9090/api/v1/gate/callback/audit/stats

# 健康检查
curl http://gate-callback:9090/api/v1/gate/callback/health
```

### 6.3 回调接口常见操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 查询状态 | `GET /api/v1/gate/callback/status` | 查询 Gate 状态 |
| 查询审计统计 | `GET /api/v1/gate/callback/audit/stats` | 查询审计统计 |
| 健康检查 | `GET /api/v1/gate/callback/health` | 健康检查 |
| 接收决策 | `POST /api/v1/gate/callback/decision` | 接收灰度决策 |

### 6.4 回调接口故障排查

| 故障现象 | 排查步骤 | 常见原因 | 解决方案 |
|----------|---------|---------|---------|
| 回调服务不可用 | 1. 检查 Pod 状态<br>2. 检查健康检查 | Pod 异常 | 重启 Pod |
| 决策事件未处理 | 1. 检查日志<br>2. 检查 Gate API | Gate API 不可用 | 修复 Gate API |
| 决策事件重复 | 1. 检查去重配置<br>2. 检查事件 ID | 去重窗口配置 | 调整去重窗口 |
| 决策处理失败 | 1. 检查日志<br>2. 检查子服务 | 子服务不可用 | 修复子服务 |

---

## 7. 新增：影子资源隔离运维

### 7.1 资源隔离组件

| 组件 | 实现方式 | 配置位置 |
|------|---------|---------|
| cgroup 资源限额 | K8s ResourceQuota + Pod resources | `v86-shadow-quota.yaml` |
| 进程隔离 | cgroup + namespace | Pod SecurityContext |
| 网络 ACL | NetworkPolicy | `network-policy.yaml` |
| 日志隔离 | PVC + 独立路径 | `v86-shadow-logs-pvc.yaml` |
| 磁盘水位保护 | 监控 + 自动清理 | `disk-cleanup-config.yaml` |

### 7.2 资源隔离运维命令

```bash
# 检查 ResourceQuota
kubectl get quota -n v86-shadow
kubectl describe quota -n v86-shadow

# 检查 Pod 资源使用
kubectl top pods -n v86-shadow
kubectl top pods -n mirror-ns

# 检查 NetworkPolicy
kubectl get netpol -A
kubectl describe netpol -n v86-shadow

# 检查日志 PVC
kubectl get pvc -n v86-shadow
kubectl describe pvc -n v86-shadow v86-shadow-logs-pvc

# 检查磁盘使用率
kubectl exec -n v86-shadow dep001 -- df -h

# 检查 cgroup
kubectl exec -n v86-shadow dep001 -- cat /sys/fs/cgroup/cpu.max
kubectl exec -n v86-shadow dep001 -- cat /sys/fs/cgroup/memory.max
```

### 7.3 资源隔离常见操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 查看 ResourceQuota | `kubectl get quota -n v86-shadow` | 查看配额 |
| 更新 ResourceQuota | `kubectl apply -f v86-shadow-quota.yaml` | 更新配额 |
| 查看 NetworkPolicy | `kubectl get netpol -n v86-shadow` | 查看策略 |
| 查看 Pod 资源 | `kubectl top pods -n v86-shadow` | 查看使用率 |
| 查看磁盘 | `kubectl exec -n v86-shadow -- df -h` | 查看磁盘 |
| 查看 cgroup | `kubectl exec -- cat /sys/fs/cgroup/cpu.max` | 查看限额 |

### 7.4 资源隔离故障排查

| 故障现象 | 排查步骤 | 常见原因 | 解决方案 |
|----------|---------|---------|---------|
| 资源超限 | 1. 检查 ResourceQuota<br>2. 检查 Pod 使用率 | 配额不足 | 调整配额 |
| 网络隔离异常 | 1. 检查 NetworkPolicy<br>2. 检查连通性 | 策略配置错误 | 修复策略 |
| 磁盘超限 | 1. 检查磁盘使用率<br>2. 检查日志大小 | 日志过多 | 清理日志 |
| OOM 事件 | 1. 检查内存使用<br>2. 检查内存限额 | 内存不足 | 调整限额 |

---

## 8. 故障排查指南更新

### 8.1 G0 影子故障排查流程

```
G0 影子异常
    │
    ├── 1. 检查 DEP-001 影子实例
    │     ├── Pod 状态 → kubectl get pods -n v86-shadow
    │     ├── 健康检查 → curl /healthz
    │     └── 日志 → kubectl logs
    │
    ├── 2. 检查流量镜像
    │     ├── 镜像状态 → GET /api/v1/mirror/control/status
    │     ├── 采样率 → GET /api/v1/mirror/control/status
    │     ├── Mirror Router → kubectl logs -n mirror-ns
    │     └── Mirror Collector → kubectl logs -n mirror-ns
    │
    ├── 3. 检查 Gate 回调
    │     ├── 回调服务 → kubectl get pods -n gate-ns
    │     ├── Gate 状态 → GET /api/v1/gate/callback/status
    │     ├── 审计统计 → GET /api/v1/gate/callback/audit/stats
    │     └── 回调日志 → kubectl logs -n gate-ns
    │
    ├── 4. 检查资源隔离
    │     ├── ResourceQuota → kubectl get quota -n v86-shadow
    │     ├── Pod 资源 → kubectl top pods -n v86-shadow
    │     ├── NetworkPolicy → kubectl get netpol -n v86-shadow
    │     └── 磁盘使用 → kubectl exec -- df -h
    │
    └── 5. 检查跨环境污染
          ├── V85 QPS → 检查是否受影响
          ├── V85 P99 → 检查是否受影响
          └── V85 错误率 → 检查是否受影响
```

### 8.2 常见故障场景

| 故障场景 | 症状 | 排查步骤 | 解决方案 |
|----------|------|---------|---------|
| 镜像流量为零 | 无镜像请求 | 1. 检查镜像状态<br>2. 检查路由配置<br>3. 检查 DEP 健康 | 启动镜像/修复配置 |
| 镜像流量异常高 | 镜像请求过多 | 1. 检查采样率<br>2. 检查流量来源 | 降低采样率 |
| 镜像延迟过高 | P99 > 200ms | 1. 检查 DEP 负载<br>2. 检查网络 | 降采样率/扩容 |
| Gate 回调失败 | 决策未处理 | 1. 检查回调服务<br>2. 检查 Gate API | 重启服务/修复 API |
| 资源超限 | CPU/内存 > 80% | 1. 检查 ResourceQuota<br>2. 检查 Pod 使用 | 扩容/降采样 |
| 跨环境污染 | V85 受影响 | 1. 检查 NetworkPolicy<br>2. 检查 cgroup | 修复隔离配置 |

### 8.3 日志排查命令

```bash
# DEP-001 影子日志
kubectl logs -n v86-shadow dep001 --tail=200 | grep -i error
kubectl logs -n v86-shadow dep001 --tail=200 | grep -i shadow

# Mirror Router 日志
kubectl logs -n mirror-ns mirror-router --tail=200 | grep -i error
kubectl logs -n mirror-ns mirror-router --tail=200 | grep -i mirror

# Mirror Collector 日志
kubectl logs -n mirror-ns mirror-collector --tail=200 | grep -i error

# Gate 回调日志
kubectl logs -n gate-ns gate-v5-gray-callback --tail=200 | grep -i error
kubectl logs -n gate-ns gate-v5-gray-callback --tail=200 | grep -i decision

# 审计日志
kubectl exec -n gate-ns gate-v5-gray-callback -- \
  cat audit_logs/audit_$(date +%Y%m%d).jsonl | tail -50
```

---

## 9. 监控告警更新

### 9.1 新增 Prometheus 指标

| 指标名 | 类型 | 标签 | 说明 |
|--------|------|------|------|
| `dshb_shadow_mirror_requests_total` | Counter | `stage,result` | 镜像请求总数 |
| `dshb_shadow_mirror_latency_ms` | Histogram | `stage` | 镜像延迟分布 |
| `dshb_shadow_mirror_dropped_total` | Counter | `stage` | 丢弃镜像数 |
| `dshb_shadow_mirror_sampling_rate` | Gauge | `stage` | 当前采样率 |
| `dshb_shadow_mirror_status` | Gauge | `stage` | 镜像状态 |
| `dshb_shadow_mirror_healthy` | Gauge | `stage` | 镜像健康 |
| `dshb_shadow_mirror_qps` | Gauge | `stage` | 当前 QPS |
| `dshb_shadow_mirror_success_rate` | Gauge | `stage` | 镜像成功率 |
| `dshb_shadow_mirror_config_age` | Gauge | `stage` | 配置年龄 |
| `dshb_shadow_mirror_cpu_pct` | Gauge | `stage` | CPU 使用率 |
| `dshb_shadow_mirror_mem_pct` | Gauge | `stage` | 内存使用率 |
| `dshb_shadow_mirror_isolation_verified` | Gauge | `stage` | 隔离验证状态 |

### 9.2 新增告警规则

| 告警名 | 条件 | 级别 | 持续时长 | 说明 |
|--------|------|------|---------|------|
| Shadow Mirror Down | `dshb_shadow_mirror_healthy == 0` | CRITICAL | 1m | 镜像组件不可用 |
| Shadow Mirror Stopped | `dshb_shadow_mirror_status == 0` (非 ROLLBACK) | HIGH | 5m | 镜像意外停止 |
| Shadow Mirror Error Rate High | `error_rate > 1%` | HIGH | 5m | 错误率过高 |
| Shadow Mirror Latency High | `p95_latency > 100ms` | WARN | 10m | 延迟过高 |
| Shadow Mirror Drop Rate High | `drop_rate > 5%` | WARN | 10m | 丢弃率过高 |
| Shadow Resource Overload | `cpu > 80% OR mem > 80%` | HIGH | 5m | 资源过载 |
| Shadow Isolation Failed | `isolation_verified == 0` | CRITICAL | 1m | 隔离验证失败 |

### 9.3 告警通知矩阵

| 级别 | 通知方式 | 通知目标 | 响应时间 |
|------|---------|---------|---------|
| CRITICAL | 电话 + 短信 | DSHB + 运维 + HERMES | 5 分钟 |
| HIGH | 企业微信 + 邮件 | DSHB + 运维 | 15 分钟 |
| WARN | 邮件 | 运维 | 30 分钟 |

### 9.4 Grafana 面板更新

| 面板 | 子面板 | 数据源 | 说明 |
|------|--------|--------|------|
| G0 影子监控 | 4 | Prometheus | 镜像概览 |
| G0 影子延迟 | 3 | Prometheus | 延迟分布 |
| G0 影子错误 | 2 | Prometheus | 错误统计 |
| G0 影子资源 | 3 | Prometheus | 资源使用 |
| G0 影子审计 | 3 | Prometheus | 审计事件 |
| **合计** | **15** | **Prometheus** | **G0 影子监控** |

---

## 10. 应急预案更新

### 10.1 应急场景与预案

| # | 应急场景 | 触发条件 | 预案 | 回滚时间 |
|---|---------|---------|------|---------|
| E01 | 镜像流量异常 | 镜像流量 > 200% 基线 | 降采样率至 5% → 停止镜像 | < 5s |
| E02 | DEP 影子实例故障 | DEP-001 不可用 > 30s | 停止镜像 → 恢复后自动重启 | < 60s |
| E03 | Gate 回调故障 | 回调服务不可用 > 60s | 重启回调服务 → 手动更新 Gate 状态 | < 30s |
| E04 | 影子环境资源过载 | CPU/内存 > 95% | 停止镜像 → 扩容 → 恢复 | < 60s |

### 10.2 应急流程

#### E01: 镜像流量异常

```
1. 检测: 监控告警 Shadow Mirror Error Rate High
2. 确认: curl /api/v1/mirror/control/status
3. 执行:
   a. 降采样率: curl -X PUT .../rate -d '{"rate": 5.0}'
   b. 若仍异常: curl -X POST .../stop
4. 通知: 通知 HERMES + 运维
5. 恢复: 修复后 curl -X POST .../start -d '{"rate": 10.0}'
```

#### E02: DEP 影子实例故障

```
1. 检测: DEP-001 健康检查失败 > 3 次
2. 自动: 镜像自动停止 (22s)
3. 确认: kubectl get pods -n v86-shadow dep001
4. 执行:
   a. 检查日志: kubectl logs -n v86-shadow dep001
   b. 修复问题: kubectl delete pod dep001 (自动重启)
5. 恢复: 健康检查通过后镜像自动重启
```

#### E03: Gate 回调故障

```
1. 检测: 回调服务不可用 > 60s
2. 确认: kubectl get pods -n gate-ns gate-v5-gray-callback
3. 执行:
   a. 重启服务: kubectl rollout restart deploy/gate-v5-gray-callback
   b. 手动更新 Gate 状态 (如需)
4. 恢复: 健康检查通过后自动恢复
```

#### E04: 影子环境资源过载

```
1. 检测: CPU/内存 > 95%
2. 自动: 停止镜像
3. 确认: kubectl top pods -n v86-shadow
4. 执行:
   a. 扩容: kubectl scale deploy/dep001 --replicas=4 -n v86-shadow
   b. 等待负载下降
5. 恢复: CPU/内存 < 60% 后镜像自动重启
```

### 10.3 回滚流程

```
1. 确认回滚触发条件
2. 执行回滚命令:
   a. 停止镜像: curl -X POST .../stop
   b. 停止巡检: kill dep001_periodic_probe
   c. 更新 Gate 状态: Gate = NOT_READY
   d. 缩容影子集群: kubectl scale --replicas=0
3. 验证回滚:
   a. 镜像流量 = 0
   b. DEP 巡检已停止
   c. Gate 状态 = NOT_READY
   d. V85 零影响
4. 通知: HERMES + 运维
```

---

## 11. 附录

### 11.1 版本演进

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| V1.0 | 2026-10-17 | 初始版本，Gate V5 适配规范 | DSHB 底层团队 |
| V2.0 | 2026-10-17 | 新增巡检配置、指标字典、灰度脚本同步 | DSHB 底层团队 |
| V2.1 | 2026-10-17 | 新增 G0 影子运维章节 (镜像/路由/回调/隔离) | DSHB 底层团队 |

### 11.2 关联文档

| 文档 | 路径 |
|------|------|
| G0 影子路由配置规范 | `v86_rc2_dshb_g0_shadow_route_config_spec.md` |
| DEP-001 流量镜像验证报告 | `v86_rc2_dshb_dep001_traffic_mirror_verify_report.md` |
| Gate 回调接口规范 | `v86_rc2_dshb_gate_callback_interface_spec.md` |
| 影子环境隔离审计报告 | `v86_rc2_dshb_shadow_env_isolation_audit.md` |
| G0 影子底层验收报告 | `v86_rc2_dshb_g0_shadow_underlayer_acceptance_report.md` |
| DEP-001 运维手册 | `v86_rc2_b_dep001_ops_manual.md` |
| Gate V5 适配规范 | `v86_rc2_dshb_gate_prod_adapt_spec_update.md` |

### 11.3 约束合规

| 约束 | 值 | 说明 |
|------|-----|------|
| `NO_MODIFY_V85` | TRUE | 所有运维操作仅作用于 V86 影子环境 |
| `NO_OVERWRITE` | TRUE | 新增文档独立提交，不覆盖 V85 运维文档 |
| `BRANCH_LOCKED` | TRUE | 产出提交至 `feature/v85-chart-template` |
| `NO_ZHIJI_API_CALL` | FALSE | 仅预发影子集群运维 |

### 11.4 文档版本

| 版本 | 日期 | 变更 |
|------|------|------|
| V2.1 | 2026-10-17 | 初始版本，G0 影子运维文档更新 |
