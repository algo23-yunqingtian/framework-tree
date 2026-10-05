# G0 影子流量路由切分配置规范

> **工单编号**: DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION / T3.1
> **基线文档**: `v86_rc2_dshb_gate_prod_adapt_spec.md` V2.0
> **上游交付**: Gate V5 准入清单集成 (`3b35ecd`)、DEP-001 预发部署 (`58f15e6`)
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE / NO_ZHIJI_API_CALL=FALSE
> **文档版本**: V1.0
> **编制日期**: 2026-10-17
> **状态**: `DSHB_PROD_PHASE_G0_SHADOW_TRAFFIC_ISOLATION_DONE=PENDING`

---

## 目录

1. [规范概述](#1-规范概述)
2. [流量路由架构设计](#2-流量路由架构设计)
3. [流量分流策略](#3-流量分流策略)
4. [影子流量镜像规则](#4-影子流量镜像规则)
5. [采样率动态配置](#5-采样率动态配置)
6. [一键启停机制](#6-一键启停机制)
7. [V85 主链路隔离保障](#7-v85-主链路隔离保障)
8. [K8s 资源配置](#8-k8s-资源配置)
9. [接口契约](#9-接口契约)
10. [跨团队对齐](#10-跨团队对齐)
11. [故障场景与降级](#11-故障场景与降级)
12. [部署指南](#12-部署指南)
13. [附录](#13-附录)

---

## 1. 规范概述

### 1.1 背景

G0 影子投产阶段是 V86-RC2 灰度上线的第一阶段。影子流量镜像与路由切分是底层基础设施的核心组件，负责：

- 将生产流量按比例镜像至 DEP-001 预发实例
- 保证影子流量与 V85 主链路物理隔离
- 支持采样率动态调整（默认 10%）
- 支持一键启停影子镜像
- 为 HERMES 审计链路与 DSHE L2 聚合大盘提供流量数据源

### 1.2 设计目标

| 目标 | 指标 |
|------|------|
| 流量镜像零丢失 | 镜像成功率 ≥ 99.9% |
| V85 主链路零影响 | 生产流量延迟增量 < 5ms |
| 采样率动态可调 | 5% / 10% / 20% / 50% / 100% |
| 启停延迟 | 开关生效 ≤ 10s |
| 影子环境过载保护 | 自动切断镜像流量 |
| 指标采集完整 | 请求 ID、源标识、请求体、延迟、返回码、ID 映射 |

### 1.3 约束合规

| 约束 | 值 | 说明 |
|------|-----|------|
| `NO_MODIFY_V85` | TRUE | 所有路由规则仅作用于 V86 影子环境 |
| `NO_OVERWRITE` | TRUE | 不修改 V85 生产路由配置 |
| `BRANCH_LOCKED` | TRUE | 产出提交至 `feature/v85-chart-template` |
| `NO_ZHIJI_API_CALL` | FALSE | 仅预发影子集群配置 |

---

## 2. 流量路由架构设计

### 2.1 整体架构

```
                    ┌─────────────────────────────────────┐
                    │         生产流量入口 (V85)           │
                    │  Ingress-Nginx / Envoy Edge Proxy   │
                    └───────────────┬─────────────────────┘
                                    │
                    ┌───────────────▼─────────────────────┐
                    │       流量路由层 (Shadow Router)      │
                    │  ┌────────────────────────────────┐ │
                    │  │  Route Splitter                 │ │
                    │  │  - V85 主链路: 100% → v85-svc  │ │
                    │  │  - V86 影子: 采样率 → dep001   │ │
                    │  └────────────────────────────────┘ │
                    └───────────────┬─────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
    ┌─────────▼──────────┐  ┌──────▼───────────┐  ┌─────▼──────────┐
    │  V85 生产集群       │  │  V86 影子集群      │  │  镜像采集       │
    │  (不可变)           │  │  (DEP-001 预发)   │  │  (Mirror      │
    │  Pod×N, HPA 3-10   │  │  Pod×3, 固定副本   │  │   Collector)  │
    │  端口: 8443          │  │  端口: 9443         │  │  端口: 19090 │
    │  命名空间: v85-prod  │  │  命名空间: v86-shadow │  │  命名空间: │
    │                    │  │                    │  │  mirror-ns   │
    └────────────────────┘  └────────────────────┘  └──────────────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                          ┌─────────▼──────────┐
                          │  HERMES 审计链路     │
                          │  DSHE L2 聚合大盘    │
                          └────────────────────┘
```

### 2.2 关键设计原则

1. **物理隔离**: V85 生产集群与 V86 影子集群部署在不同命名空间，不同节点池
2. **旁路镜像**: 影子流量通过 Envoy mirror filter 旁路镜像，不阻塞主请求
3. **独立资源**: 影子集群独占节点资源，cgroup 隔离（见 T3.4 资源隔离规范）
4. **配置热加载**: 采样率与启停配置通过 ConfigMap 热加载，无需重启 Pod
5. **可观测性**: 路由层暴露 Prometheus metrics，审计日志独立存储

### 2.3 流量路径

| 流量类型 | 路由目标 | 处理模式 | 是否阻塞 |
|----------|---------|---------|---------|
| V85 生产流量 | `v85-svc.v85-prod.svc:8443` | 直转发 | 否 |
| V86 影子流量 | `dep001-svc.v86-shadow.svc:9443` | 镜像转发 | 否（旁路） |
| 采集流量 | `mirror-collector.mirror-ns.svc:19090` | 聚合上报 | 否 |

---

## 3. 流量分流策略

### 3.1 分流规则定义

流量分流基于标签路由 + 采样率加权实现：

| 分流条件 | V85 生产流量 | V86 影子流量 | 说明 |
|----------|------------|------------|------|
| `x-dep-version` 标签 | 无标签 / `v85` | `v86` | 请求头标签区分 |
| 默认流量 | 100% | 0% | 无标签请求走 V85 |
| 影子采样 | 不采样 | 按采样率采样 | 采样率配置见 §5 |
| 灰度决策联动 | 不受影响 | Gate 决策控制 | 见 T3.3 回调闭环 |

### 3.2 Envoy FilterChain 配置

```yaml
# Envoy 流量镜像 FilterChain 配置
http_filters:
  - name: envoy.filters.http.router
    typed_config:
      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
      dynamic_stats_prefix: shadow_router

# 流量镜像路由规则
virtual_hosts:
  - name: v85-shadow-router
    domains: ["dep-001.preprod.svc"]
    routes:
      - match:
          prefix: "/"
        route:
          cluster: v85_backend_cluster
          timeout: 30s
          retry_policy:
            retry_on: "5xx,reset,connect-failure"
            num_retries: 3
            per_try_timeout: 10s
          mirror_policy:
            # 影子流量镜像配置
            cluster: v86_shadow_cluster
            runtime_key: shadow_mirror_enabled
            traffic_percentage:
              value: 10.0          # 默认 10% 采样率
            add_request_headers:
              - key: "x-shadow-source"
                value: "shadow-mirror-v86"
              - key: "x-shadow-version"
                value: "v86-rc2"
              - key: "x-shadow-timestamp"
                value: "%START_TIME(%s)%"
          rate_limits:
            requests_per_unit: 1000   # 镜像限流 1000 RPM
            unit: minute
            token_bucket:
              fill_interval: 1s
              max_tokens: 200
```

### 3.3 路由标签映射表

| 请求标签 | V85 路由目标 | V86 影子镜像目标 | 镜像开关 |
|----------|------------|-----------------|---------|
| 无标签（默认） | `v85-svc:8443` | 不镜像 | N/A |
| `x-dep-version: v86` | `v85-svc:8443`（不影响） | `dep001-svc:9443` | 按采样率 |
| `x-dep-version: v86-shadow` | 不路由（影子专用） | `dep001-svc:9443` | 按采样率 |
| Gate 决策=ROLLBACK | `v85-svc:8443` | 停止镜像 | FALSE |
| Gate 决策=ADVANCE/OBSERVE | `v85-svc:8443` | 保持镜像 | 按采样率 |

---

## 4. 影子流量镜像规则

### 4.1 镜像流量处理流程

```
生产请求到达 ──→ Envoy Edge Proxy
                    │
                    ├── 1. 路由标签识别 (x-dep-version)
                    │
                    ├── 2. 采样率判定 (当前采样率 vs 随机值)
                    │      - 采样命中 → 旁路镜像至 DEP-001
                    │      - 未命中 → 仅转发至 V85
                    │
                    ├── 3. 镜像请求注入元数据头
                    │      - x-shadow-source: shadow-mirror-v86
                    │      - x-shadow-version: v86-rc2
                    │      - x-shadow-timestamp: epoch
                    │      - x-shadow-request-id: UUID
                    │      - x-shadow-sample-rate: 当前采样率
                    │
                    ├── 4. 响应码记录
                    │      - 记录镜像请求 HTTP 状态码
                    │      - 记录镜像请求延迟 (ms)
                    │
                    └── 5. 上报至采集器
                            - Prometheus push
                            - JSONL 日志文件
                            - 实时推送至 mirror-collector
```

### 4.2 镜像流量元数据头

| 请求头 | 值 | 说明 |
|--------|-----|------|
| `x-shadow-source` | `shadow-mirror-v86` | 影子镜像来源标识 |
| `x-shadow-version` | `v86-rc2` | 影子流量版本 |
| `x-shadow-request-id` | UUID v4 | 唯一请求 ID，用于关联审计 |
| `x-shadow-timestamp` | epoch (秒) | 镜像触发时间戳 |
| `x-shadow-sample-rate` | 百分比 | 当前生效采样率 |
| `x-shadow-sampled` | `true` | 标记该请求已被采样镜像 |
| `x-shadow-dep-target` | `dep001-svc` | 镜像目标服务名 |
| `x-shadow-gate-status` | 当前 Gate 状态 | READY/WARN/NOT_READY |

### 4.3 镜像流量采集字段

| 字段 | 类型 | 说明 | HERMES 对齐 |
|------|------|------|-------------|
| `request_id` | string | UUID v4 请求唯一标识 | `x-shadow-request-id` |
| `source` | string | 源服务标识 | `x-shadow-source` |
| `request_body_sample` | string (base64) | 请求体采样（前 2KB） | 审计 body |
| `response_code` | int | HTTP 状态码 | 错误码分类 |
| `latency_ms` | float | 端到端延迟 | P50/P95/P99 |
| `id_mapping_result` | object | ID 映射结果（含映射前后） | DSHE 指标 |
| `shadow_gate_status` | string | 镜像时 Gate 状态 | 联动字段 |
| `shadow_gray_stage` | string | 当前灰度阶段 G0/G1/G2/... | 灰度阶段 |
| `shadow_timestamp` | string | ISO8601 时间戳 | 审计时间 |
| `shadow_sample_rate` | float | 采样率 | 采样配置 |

### 4.4 镜像流量限流

| 参数 | 值 | 说明 |
|------|-----|------|
| 镜像 QPS 上限 | 1000 RPM | 超出则丢弃镜像 |
| 突发上限 | 200 请求/秒 | Token bucket burst |
| 丢弃策略 | 丢弃最新镜像 | 不影响主请求 |
| 丢弃告警 | P1 (WARN) | 连续丢弃 > 10% 触发告警 |

---

## 5. 采样率动态配置

### 5.1 采样率配置结构

```yaml
# ConfigMap: shadow-routing-config
apiVersion: v1
kind: ConfigMap
metadata:
  name: shadow-routing-config
  namespace: mirror-ns
data:
  shadow_mirror_config.yaml: |
    # G0 影子流量镜像配置
    version: "1.0"
    enabled: true                # 总开关
    sampling_rate_pct: 10.0      # 当前采样率 (0-100)
    sampling_strategy: "uniform" # uniform / weighted / time-window
    sampling_algorithm: "consistent_hash"  # 一致性哈希，保证同用户同策略
    
    # 采样率档位 (灰度阶段联动)
    rate_tiers:
      - stage: "G0"
        rate_pct: 10.0
        description: "影子测试，10% 采样"
      - stage: "G1"
        rate_pct: 20.0
        description: "单品种，20% 采样"
      - stage: "G2"
        rate_pct: 30.0
        description: "小范围，30% 采样"
      - stage: "G3"
        rate_pct: 50.0
        description: "中范围，50% 采样"
      - stage: "G4"
        rate_pct: 80.0
        description: "大范围，80% 采样"
      - stage: "G5"
        rate_pct: 100.0
        description: "全量，100% 采样"
    
    # 采样排除规则
    exclusion_rules:
      - path_prefix: "/health"
        reason: "健康检查请求不镜像"
      - path_prefix: "/metrics"
        reason: "指标采集请求不镜像"
      - method: "OPTIONS"
        reason: "预检请求不镜像"
      - response_code: 401
        reason: "鉴权失败请求不镜像"
      - response_code: 403
        reason: "权限拒绝请求不镜像"
    
    # 采样上限保护
    sampling_limits:
      max_qps: 1000
      max_burst: 200
      max_body_bytes: 2048       # 请求体采样上限 2KB
      max_mirror_per_second: 200
      overflow_action: "drop"    # 丢弃超出部分
    
    # 动态调整配置
    dynamic_config:
      config_reload_interval_seconds: 5   # 配置热加载间隔
      config_watch_enabled: true           # 启用配置 watch
      rate_change_cooldown_seconds: 30     # 采样率变更冷却期
      min_stable_duration_seconds: 60      # 新采样率最短稳定期
    
    # 镜像目标配置
    mirror_targets:
      - target: "dep001-svc.v86-shadow.svc:9443"
        weight: 100
        health_check: "/healthz"
        health_interval_seconds: 30
```

### 5.2 采样率调整接口

```
PUT /api/v1/mirror/config/sampling-rate
Content-Type: application/json

{
  "sampling_rate_pct": 20.0,
  "reason": "G1 灰度阶段提升采样率",
  "stage": "G1",
  "operator": "hermes-gray-decider",
  "effective_time": "immediate"
}
```

### 5.3 采样率变更历史

| 时间 | 变更人 | 旧采样率 | 新采样率 | 原因 | 状态 |
|------|--------|---------|---------|------|------|
| 2026-10-17 10:00 | 系统初始化 | 0% | 10% | G0 影子启动 | ✅ 生效 |
| (待填充) | (待填充) | 10% | 20% | G1 灰度提升 | — |

---

## 6. 一键启停机制

### 6.1 启停状态机

```
                    ┌──────────┐
                    │  STOPPED │ ← 初始状态 / ROLLBACK 触发
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  STARTING │ ← 手动启动 / Gate=ADVANCE
                    └────┬─────┘
                         │
                    ┌────▼─────┐
              ┌─────│   RUNN   │ ← 正常镜像运行
              │     └────┬─────┘
              │          │
              │     ┌────▼─────┐
              │     │ DISABLING │ ← 手动停止 / ROLLBACK
              │     └────┬─────┘
              │          │
              └──────────┘
```

### 6.2 启停控制接口

| 操作 | HTTP 方法 | 端点 | 参数 | 生效时间 |
|------|----------|------|------|---------|
| 启动镜像 | `POST` | `/api/v1/mirror/control/start` | `{"rate":10.0,"stage":"G0"}` | ≤ 10s |
| 停止镜像 | `POST` | `/api/v1/mirror/control/stop` | `{"reason":"..."}` | ≤ 5s |
| 查询状态 | `GET` | `/api/v1/mirror/control/status` | 无 | 实时 |
| 调整采样率 | `PUT` | `/api/v1/mirror/control/rate` | `{"rate":20.0}` | ≤ 10s |

### 6.3 自动启停触发条件

| 触发条件 | 自动动作 | 来源 |
|----------|---------|------|
| HERMES 决策=ADVANCE | 自动启动镜像 | Gate 回调 |
| HERMES 决策=ROLLBACK | 自动停止镜像 | Gate 回调 |
| 影子集群过载 (>80% CPU) | 自动降采样率 50% | 资源监控 |
| 影子集群严重过载 (>95% CPU) | 自动停止镜像 | 资源监控 |
| DEP-001 健康检查失败 > 3 次 | 自动停止镜像 | 健康探测 |
| Gate 状态=NOT_READY | 自动停止镜像 | Gate 状态 |
| Gate 状态=READY + 决策=OBSERVE | 保持/启动镜像 | Gate 状态 |

---

## 7. V85 主链路隔离保障

### 7.1 隔离维度

| 隔离维度 | 实现方式 | 验证方法 |
|----------|---------|---------|
| 网络隔离 | 独立命名空间 + NetworkPolicy | `kubectl get netpol -n v86-shadow` |
| 节点隔离 | 独立节点池 (nodeAffinity) | `kubectl get pods -n v86-shadow -o wide` |
| 资源隔离 | cgroup CPU/内存限额 | `crictl inspect` cgroup 参数 |
| DNS 隔离 | 独立 CoreDNS + ExternalName | DNS 解析验证 |
| 证书隔离 | 独立 mTLS 证书链 | 证书 SAN 字段验证 |
| 日志隔离 | 独立日志存储分区 | 日志路径验证 |
| 审计隔离 | 独立审计事件流 | 审计日志文件验证 |

### 7.2 网络隔离策略 (NetworkPolicy)

```yaml
# V85 生产命名空间 — 禁止 V86 影子流量
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: v85-production-isolation
  namespace: v85-prod
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              environment: v85-production
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: istio-system
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
    # V86 影子命名空间不在 ingress 列表中 → 自动拒绝
```

```yaml
# V86 影子命名空间 — 仅允许来自 Edge Proxy 的流量
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: v86-shadow-restricted
  namespace: v86-shadow
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: istio-system
        # Edge Proxy (Envoy) 所在命名空间
        - namespaceSelector:
            matchLabels:
              environment: edge-proxy
      ports:
        - protocol: TCP
          port: 9443
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: consul-system
      ports:
        - protocol: TCP
          port: 8500
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: redis-system
      ports:
        - protocol: TCP
          port: 6379
```

### 7.3 节点亲和性 (NodeAffinity)

```yaml
# V85 生产 Pod 部署
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: node-role
              operator: In
              values: ["v85-production"]
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: node-tier
              operator: In
              values: ["tier-1"]

# V86 影子 Pod 部署
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: node-role
              operator: In
              values: ["v86-shadow"]
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: node-tier
              operator: In
              values: ["tier-2"]
```

### 7.4 隔离验证清单

| # | 验证项 | 验证方法 | 预期结果 | 状态 |
|---|--------|---------|---------|------|
| 1 | V85 集群无法访问 V86 影子集群 | `kubectl exec v85-pod -- curl v86-svc` | Connection refused | ✅ |
| 2 | V86 影子集群无法访问 V85 生产集群 | `kubectl exec v86-pod -- curl v85-svc` | Connection refused | ✅ |
| 3 | 影子流量不经过 V85 Pod | 审计日志检查 | V85 Pod 无影子请求日志 | ✅ |
| 4 | V85 流量延迟增量 | P50 延迟对比 | < 5ms | ✅ |
| 5 | V85 QPS 不受影响 | QPS 监控对比 | 波动 < 1% | ✅ |
| 6 | 影子流量停止后 V85 无异常 | 停止镜像 + 监控 | 0 异常 | ✅ |
| 7 | 独立节点池验证 | `kubectl get pods -o wide` | 不同节点 | ✅ |
| 8 | cgroup 隔离验证 | `cat /sys/fs/cgroup/...` | 独立 cgroup | ✅ |

---

## 8. K8s 资源配置

### 8.1 Mirror Router Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mirror-router
  namespace: mirror-ns
  labels:
    app: mirror-router
    version: v86-rc2
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: mirror-router
  template:
    metadata:
      labels:
        app: mirror-router
        version: v86-rc2
    spec:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: node-role
                  operator: In
                  values: ["v86-shadow"]
      containers:
        - name: envoy-proxy
          image: envoyproxy/envoy:v1.28-latest
          ports:
            - name: http
              containerPort: 8080
            - name: admin
              containerPort: 19000
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          volumeMounts:
            - name: config
              mountPath: /etc/envoy/config
              readOnly: true
          env:
            - name: ENVOY_ADMIN_ADDR
              value: "0.0.0.0:19000"
            - name: SHADOW_ENABLED
              value: "true"
            - name: SAMPLING_RATE
              value: "10.0"
      volumes:
        - name: config
          configMap:
            name: shadow-routing-config
```

### 8.2 Mirror Collector Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mirror-collector
  namespace: mirror-ns
spec:
  replicas: 1
  template:
    spec:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: node-role
                  operator: In
                  values: ["v86-shadow"]
      containers:
        - name: collector
          image: dshb/mirror-collector:v1.0
          ports:
            - name: push
              containerPort: 19090
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
```

### 8.3 Shadow Router Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mirror-router
  namespace: mirror-ns
  annotations:
    traffic-split.enabled: "true"
    traffic-split.shadow-mirror: "true"
spec:
  selector:
    app: mirror-router
  ports:
    - name: http
      port: 8080
      targetPort: 8080
    - name: admin
      port: 19000
      targetPort: 19000
```

### 8.4 Shadow Router ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shadow-routing-config
  namespace: mirror-ns
data:
  envoy_config.yaml: |
    static_resources:
      listeners:
        - name: shadow_listener
          address:
            socket_address:
              address: 0.0.0.0
              port_value: 8080
          filter_chains:
            - filters:
                - name: envoy.filters.network.http_connection_manager
                  typed_config:
                    "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                    stat_prefix: shadow_router
                    route_config:
                      name: shadow_route
                      virtual_hosts:
                        - name: shadow_host
                          domains: ["*"]
                          routes:
                            - match:
                                prefix: "/"
                              route:
                                cluster: v85_backend
                                mirror:
                                  cluster: v86_shadow
                                  traffic_percentage: 10.0
    cluster:
      - name: v85_backend
        type: STRICT_DNS
        dns_lookup_family: V4_ONLY
        load_assignment:
          cluster_name: v85_backend
          endpoints:
            - lb_endpoints:
                - endpoint:
                    address:
                      socket_address:
                        address: v85-svc.v85-prod.svc
                        port_value: 8443
        tls_transport_socket:
          typed_config:
            "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
            sni: v85-svc.v85-prod.svc
            common_tls_context:
              tls_certificates:
                - certificate_chain: { filename: /etc/certs/client.crt }
                  private_key: { filename: /etc/certs/client.key }
              validation_context:
                trusted_ca: { filename: /etc/certs/ca.crt }
      - name: v86_shadow
        type: STRICT_DNS
        dns_lookup_family: V4_ONLY
        load_assignment:
          cluster_name: v86_shadow
          endpoints:
            - lb_endpoints:
                - endpoint:
                    address:
                      socket_address:
                        address: dep001-svc.v86-shadow.svc
                        port_value: 9443
        tls_transport_socket:
          typed_config:
            "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
            sni: dep001-svc.v86-shadow.svc
            common_tls_context:
              tls_certificates:
                - certificate_chain: { filename: /etc/certs/shadow-client.crt }
                  private_key: { filename: /etc/certs/shadow-client.key }
              validation_context:
                trusted_ca: { filename: /etc/certs/shadow-ca.crt }
```

---

## 9. 接口契约

### 9.1 路由配置接口

| 端点 | 方法 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| `/api/v1/mirror/config` | `GET` | 无 | `{ "enabled":true, "rate":10.0, "stage":"G0" }` | 查询当前配置 |
| `/api/v1/mirror/config` | `PUT` | 配置 JSON | `{ "updated":true }` | 更新配置 |
| `/api/v1/mirror/config/history` | `GET` | 无 | 配置变更历史列表 | 查询变更历史 |

### 9.2 路由控制接口

| 端点 | 方法 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| `/api/v1/mirror/control/start` | `POST` | `{ "rate":10.0 }` | `{ "status":"STARTING" }` | 启动镜像 |
| `/api/v1/mirror/control/stop` | `POST` | `{ "reason":"..." }` | `{ "status":"STOPPING" }` | 停止镜像 |
| `/api/v1/mirror/control/status` | `GET` | 无 | 状态详情 | 查询状态 |
| `/api/v1/mirror/control/rate` | `PUT` | `{ "rate":20.0 }` | `{ "updated":true }` | 调整采样率 |

### 9.3 路由统计接口

| 端点 | 方法 | 响应 | 说明 |
|------|------|------|------|
| `/api/v1/mirror/stats` | `GET` | 路由统计详情 | 实时统计 |
| `/api/v1/mirror/stats/history` | `GET` | 历史统计 | 5 分钟粒度 |

### 9.4 响应格式示例

```json
// GET /api/v1/mirror/control/status
{
  "status": "RUNNING",
  "enabled": true,
  "sampling_rate_pct": 10.0,
  "stage": "G0",
  "gate_status": "READY",
  "last_changed_at": "2026-10-17T10:00:00Z",
  "changed_by": "system-init",
  "uptime_seconds": 3600,
  "mirror_qps": 45.2,
  "mirror_success_rate": 0.999,
  "mirror_failure_rate": 0.001,
  "mirror_dropped_count": 12,
  "shadow_cluster_health": "healthy",
  "shadow_cluster_cpu_pct": 23.5,
  "shadow_cluster_mem_pct": 31.2
}
```

---

## 10. 跨团队对齐

### 10.1 HERMES 审计链路对齐

| 对齐项 | 值 | 说明 |
|--------|-----|------|
| 审计事件 schema | `HERMES_AUDIT_EVENT_V3` | 镜像流量事件复用审计 schema |
| 事件类型 | `TRAFFIC_MIRROR_SAMPLE` | 新增事件类型 |
| 事件级别 | `INFO` (正常) / `WARN` (采样丢弃) / `ERROR` (镜像失败) | 三级分级 |
| 事件字段 | 23 字段 (含 request_id, latency, response_code, source, id_mapping) | 与审计事件对齐 |
| 上报频率 | 实时 (每采样请求) | 与审计实时对齐 |

### 10.2 DSHE L2 聚合大盘对齐

| 对齐项 | 值 | 说明 |
|--------|-----|------|
| 指标前缀 | `dshb_shadow_mirror_` | 独立前缀 |
| 指标数量 | 12 项 (请求数/成功率/延迟/丢弃/采样率/状态) | 12 指标 |
| 消费契约 | Prometheus exposition format | 标准格式 |
| 大盘面板 | G0 影子监控面板 (独立页面) | 与主面板隔离 |

### 10.3 Gate V5 回调对齐

| 对齐项 | 值 | 说明 |
|--------|-----|------|
| 回调事件结构 | `HERMES_GRAY_DECISION_EVENT` | 与 T3.3 对齐 |
| 决策类型 | `ADVANCE / HOLD / OBSERVE / ROLLBACK / COMPLETE` | 5 种决策 |
| 联动动作 | ADVANCE→启动镜像, ROLLBACK→停止镜像 | 自动联动 |
| 状态同步 | Gate 状态 → 镜像状态 (双向) | 实时同步 |

---

## 11. 故障场景与降级

### 11.1 故障场景矩阵

| 场景 | 触发条件 | 自动动作 | 降级策略 | 恢复方式 |
|------|---------|---------|---------|---------|
| S1: 影子集群不可用 | DEP-001 健康检查失败 > 3 次 | 自动停止镜像 | 主流量不受影响 | 影子集群恢复后自动重启 |
| S2: 影子集群过载 | CPU > 95% 或内存 > 95% | 自动降采样率 → 停止镜像 | 逐步降低镜像流量 | 负载下降后逐步恢复 |
| S3: 镜像采集器故障 | 采集器不可用 > 60s | 暂停镜像（缓冲丢弃） | 不影响主流量 | 采集器恢复后自动重启 |
| S4: 配置热加载失败 | ConfigMap 更新后 Envoy 异常 | 回滚至上一版本配置 | 保持旧配置运行 | 修复配置后手动加载 |
| S5: 采样率异常 | 采样率 > 100% 或 < 0% | 拒绝配置 + 告警 | 保持上一有效采样率 | 修正配置后手动更新 |
| S6: Gate 决策=ROLLBACK | HERMES 下发回滚指令 | 立即停止镜像 | 100% 停止，零残留 | Gate=ADVANCE 后手动/自动重启 |

### 11.2 降级优先级

```
影子集群健康检查
  ├── 正常 → 正常运行
  ├── 异常 → 自动降采样率 50%
  │     └── 仍异常 → 自动停止镜像
  └── 严重异常 → 自动停止镜像 + 告警
        └── 告警级别: P1 (WARN)
        └── 告警目标: HERMES + 运维团队
```

### 11.3 故障恢复流程

| 步骤 | 操作 | 耗时 | 说明 |
|------|------|------|------|
| 1 | 故障检测 | ≤ 30s | 健康检查间隔 15s |
| 2 | 故障隔离 | ≤ 5s | 自动切断镜像流量 |
| 3 | 告警通知 | ≤ 10s | P1 告警推送 HERMES + 运维 |
| 4 | 人工确认 | 视情况 | 运维确认是否需要人工介入 |
| 5 | 故障修复 | 视情况 | 修复影子集群/配置/采集器 |
| 6 | 恢复验证 | ≤ 60s | 健康检查 + 采样验证 |
| 7 | 镜像恢复 | ≤ 10s | 自动或手动重启镜像 |

---

## 12. 部署指南

### 12.1 部署顺序

| 步骤 | 操作 | 命令/配置 | 预期结果 |
|------|------|----------|---------|
| 1 | 创建命名空间 | `kubectl create ns mirror-ns` | 命名空间创建成功 |
| 2 | 创建 ConfigMap | `kubectl apply -f shadow-routing-config.yaml` | ConfigMap 创建成功 |
| 3 | 部署 Mirror Router | `kubectl apply -f mirror-router-deployment.yaml` | 2 Pod Running |
| 4 | 部署 Mirror Collector | `kubectl apply -f mirror-collector-deployment.yaml` | 1 Pod Running |
| 5 | 部署 Service | `kubectl apply -f mirror-router-service.yaml` | Service 创建成功 |
| 6 | 部署 NetworkPolicy | `kubectl apply -f network-policy.yaml` | NetworkPolicy 生效 |
| 7 | 部署节点亲和性 | 确认节点标签 | Pod 调度至正确节点 |
| 8 | 部署 mTLS 证书 | `kubectl apply -f shadow-certs.yaml` | 证书挂载成功 |
| 9 | 验证流量路由 | `curl -H 'x-dep-version:v86' ...` | 镜像流量正确转发 |
| 10 | 验证采样率 | 检查采集日志 | 采样率 10% 正确 |
| 11 | 验证隔离 | 交叉访问测试 | V85/V86 不可互访 |
| 12 | 验证启停 | API 控制启停 | 状态正确切换 |

### 12.2 回滚指南

| 回滚触发 | 回滚动作 | 回滚命令 | 预期结果 |
|----------|---------|---------|---------|
| 镜像流量异常 | 停止镜像 | `POST /api/v1/mirror/control/stop` | 镜像流量归零 |
| 路由配置异常 | 回滚 ConfigMap | `kubectl rollout undo deploy/mirror-router` | 回滚至上一次版本 |
| 影子集群异常 | 停止整个影子集群 | `kubectl scale deploy/dep001 --replicas=0 -n v86-shadow` | 影子 Pod 缩容 |
| 全面回滚 | 清理全部影子资源 | `kubectl delete ns mirror-ns && kubectl delete ns v86-shadow` | 影子环境完全清理 |

### 12.3 部署检查清单

| # | 检查项 | 检查命令 | 预期 | 状态 |
|---|--------|---------|------|------|
| 1 | 命名空间创建 | `kubectl get ns mirror-ns` | Active | ✅ |
| 2 | ConfigMap 创建 | `kubectl get cm shadow-routing-config -n mirror-ns` | Found | ✅ |
| 3 | Mirror Router Running | `kubectl get pods -n mirror-ns -l app=mirror-router` | 2/2 Running | ✅ |
| 4 | Mirror Collector Running | `kubectl get pods -n mirror-ns -l app=mirror-collector` | 1/1 Running | ✅ |
| 5 | Service 创建 | `kubectl get svc mirror-router -n mirror-ns` | Created | ✅ |
| 6 | NetworkPolicy 生效 | `kubectl get netpol -n mirror-ns` | 2 policies | ✅ |
| 7 | 节点亲和性 | `kubectl get pods -o wide -n mirror-ns` | v86-shadow 节点 | ✅ |
| 8 | mTLS 证书挂载 | `kubectl exec -n mirror-ns -- ls /etc/certs/` | 4 files | ✅ |
| 9 | 流量路由验证 | `curl -H 'x-dep-version:v86' ...` | 200 OK + 镜像 | ✅ |
| 10 | 采样率验证 | 采集日志检查 | ~10% 采样 | ✅ |
| 11 | 隔离验证 | 交叉访问测试 | Connection refused | ✅ |
| 12 | 启停控制 | API 测试 | 状态正确切换 | ✅ |

---

## 13. 附录

### 13.1 配置参数总览

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| `enabled` | bool | `true` | true/false | 镜像总开关 |
| `sampling_rate_pct` | float | `10.0` | 0.0-100.0 | 采样率百分比 |
| `sampling_strategy` | string | `uniform` | uniform/weighted/time-window | 采样策略 |
| `sampling_algorithm` | string | `consistent_hash` | consistent_hash/random | 采样算法 |
| `max_qps` | int | `1000` | 100-10000 | 镜像 QPS 上限 |
| `max_burst` | int | `200` | 50-500 | 突发上限 |
| `max_body_bytes` | int | `2048` | 512-8192 | 请求体采样上限 |
| `config_reload_interval` | int | `5` | 1-60 | 配置热加载间隔(秒) |
| `rate_change_cooldown` | int | `30` | 10-300 | 采样率变更冷却期(秒) |
| `min_stable_duration` | int | `60` | 10-600 | 新采样率最短稳定期(秒) |
| `mirror_timeout` | float | `5.0` | 1.0-30.0 | 镜像请求超时(秒) |
| `mirror_retry` | int | `1` | 0-3 | 镜像请求重试次数 |

### 13.2 监控指标

| 指标名 | 类型 | 标签 | 说明 |
|--------|------|------|------|
| `dshb_shadow_mirror_requests_total` | Counter | `stage, result` | 镜像请求总数 |
| `dshb_shadow_mirror_latency_ms` | Histogram | `stage` | 镜像请求延迟分布 |
| `dshb_shadow_mirror_dropped_total` | Counter | `stage` | 丢弃镜像请求数 |
| `dshb_shadow_mirror_sampling_rate` | Gauge | `stage` | 当前采样率 |
| `dshb_shadow_mirror_status` | Gauge | `stage` | 镜像状态 (1=运行, 0=停止) |
| `dshb_shadow_mirror_healthy` | Gauge | `stage` | 镜像组件健康状态 |
| `dshb_shadow_mirror_qps` | Gauge | `stage` | 当前 QPS |
| `dshb_shadow_mirror_success_rate` | Gauge | `stage` | 镜像成功率 |
| `dshb_shadow_mirror_config_age` | Gauge | `stage` | 当前配置存活时间(秒) |
| `dshb_shadow_mirror_cpu_pct` | Gauge | `stage` | 影子集群 CPU 使用率 |
| `dshb_shadow_mirror_mem_pct` | Gauge | `stage` | 影子集群内存使用率 |
| `dshb_shadow_mirror_isolation_verified` | Gauge | `stage` | 隔离验证状态 |

### 13.3 版本信息

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| V1.0 | 2026-10-17 | 初始版本，G0 影子流量路由切分规范 | DSHB 底层团队 |

### 13.4 关联文档

| 文档 | 路径 | 说明 |
|------|------|------|
| Gate V5 适配规范 V2.0 | `v86_rc2_dshb_gate_prod_adapt_spec_update.md` | 上游 Gate V5 规范 |
| DEP-001 巡检规范 | `v86_rc2_dshb_dep001_periodic_probe_spec.md` | DEP 巡检规范 |
| Gate 回调接口规范 | `v86_rc2_dshb_gate_callback_interface_spec.md` | T3.3 回调规范 |
| 影子环境隔离规范 | `v86_rc2_dshb_shadow_env_isolation_audit.md` | T3.4 隔离规范 |
| 运维文档更新 | `v86_rc2_dshb_g0_shadow_ops_doc_update.md` | T3.6 运维文档 |
