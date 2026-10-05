# DSHB V86-RC2 DEP-001 短ID解析服务运维手册

> **文档编号**: DSHB-V86-RC2-DEP001-OPS-V1.0
> **文档版本**: V1.0
> **编制日期**: 2026-10-17
> **适用版本**: DEP-001 v1.0.0-rc2
> **分支**: `feature/v85-chart-template`
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE
> **目标读者**: 运维工程师、SRE、DSHB/DSHE/HERMES团队成员
> **文档状态**: 🟢 FINAL — 16章节完整交付

---

## 目录

1. [概述](#1-概述)
2. [服务架构](#2-服务架构)
3. [部署架构](#3-部署架构)
4. [启动与停止](#4-启动与停止)
5. [扩容与缩容](#5-扩容与缩容)
6. [降级策略](#6-降级策略)
7. [故障定位](#7-故障定位)
8. [日志检索](#8-日志检索)
9. [监控告警](#9-监控告警)
10. [灾备切换](#10-灾备切换)
11. [证书管理](#11-证书管理)
12. [Token管理](#12-token管理)
13. [配置管理](#13-配置管理)
14. [维护操作](#14-维护操作)
15. [应急预案](#15-应急预案)
16. [附录](#16-附录)

---

## 1. 概述

### 1.1 文档目的

本运维手册为DEP-001短ID解析服务的标准运维操作指南，涵盖服务架构、部署架构、启停操作、扩缩容、降级策略、故障定位、日志检索、监控告警、灾备切换、证书/Token管理、配置管理、维护操作及应急预案等16个章节。

### 1.2 适用范围

| 环境 | 适用 | 说明 |
|------|------|------|
| **预发环境** | ✅ | 本手册主要适用环境 |
| **生产环境** | ✅ | 操作相同，需额外审批 |
| **沙箱环境** | ❌ | 沙箱为测试环境，不适用 |

### 1.3 文档关联

| 关联文档 | 路径 | 说明 |
|----------|------|------|
| DEP-001联调清单 | `v86_rc2_dshb_dep001_integration_prep_checklist.md` | 联调前置条件 |
| Gate V5适配规范 | `v86_rc2_dshb_gate_prod_adapt_spec.md` | Gate预检查适配 |
| 风险台账V4 | `v86_rc2_b_risk_review_dep001_real_env.md` | 风险评审 |
| 部署自检报告 | `v86_rc2_b_dep001_deploy_selfcheck_report.md` | T3.1部署验证 |
| 压力测试报告 | `v86_rc2_b_dep001_stress_jitter_test_report.md` | T3.2压力验证 |
| Gate集成报告 | `v86_rc2_b_dep001_gate_real_integration_report.md` | T3.3 E2E验证 |
| 72h观测报告 | `v86_rc2_b_dep001_longrun_obs_report.md` | T3.4稳定性验证 |

### 1.4 版本信息

| 项目 | 值 |
|------|-----|
| 服务名称 | DEP-001 短ID解析服务 |
| 服务版本 | v1.0.0-rc2 |
| 镜像标签 | `registry.dep001.internal/dep001/api:v1.0.0-rc2-preprod` |
| 分支 | `feature/v85-chart-template` |
| 基线commit | `1366698` |

---

## 2. 服务架构

### 2.1 架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                    DEP-001 服务架构                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  客户端层                                                   │   │
│  │  ├── DSHB Gate Server (Gate V5)                           │   │
│  │  ├── DSHE Alert Server                                    │   │
│  │  └── HERMES Audit Server                                  │   │
│  └───────────────────────────┬──────────────────────────────┘   │
│                              │ HTTP (mTLS + Token)                │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  接入层                                                    │   │
│  │  ├── API Gateway (NGINX Ingress)                          │   │
│  │  │   ├── TLS 1.3, mTLS enabled                            │   │
│  │  │   ├── Rate limit: 1000 RPM, burst=200                  │   │
│  │  │   └── Timeout: connect=30s, read=15s                   │   │
│  │  └── DNS: dep001-api.preprod.internal                     │   │
│  └───────────────────────────┬──────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  应用层 (3 replicas)                                       │   │
│  │  ├── dep001-api-001 (10.86.32.10)                         │   │
│  │  ├── dep001-api-002 (10.86.32.11)                         │   │
│  │  └── dep001-api-003 (10.86.32.12)                         │   │
│  │                                                            │   │
│  │  核心组件:                                                  │   │
│  │  ├── REST API Server (Python 3.11, FastAPI)                │   │
│  │  ├── Short ID Resolver (解析short_id→long_id)               │   │
│  │  ├── Circuit Breaker (熔断器: threshold=5, timeout=30s)     │   │
│  │  ├── Rate Limiter (限流器: 1000 RPM, burst=200)             │   │
│  │  ├── Health Check (存活/就绪/启动探针)                        │   │
│  │  ├── Audit Logger (审计日志: JSON格式)                        │   │
│  │  └── Config Manager (配置管理: ConfigMap + Secrets)          │   │
│  └───────────────────────────┬──────────────────────────────┘   │
│                              │                                    │
│              ┌───────────────┼───────────────┐                    │
│              ▼               ▼               ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ MySQL 8.0    │  │ Redis 7.2    │  │ Consul 1.16  │           │
│  │ :3306        │  │ :6379        │  │ :8500        │           │
│  │ 主数据库      │  │ 缓存层        │  │ 服务发现      │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  监控层                                                    │   │
│  │  ├── Prometheus 2.47.1 (:9090)                           │   │
│  │  ├── Grafana 10.2.2 (:3000)                              │   │
│  │  └── ELK 8.11.1 (:5601/:9200)                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明

| 组件 | 技术栈 | 职责 | 关键参数 |
|------|--------|------|----------|
| **API Server** | Python 3.11, FastAPI | REST API服务 | :8080 |
| **Short ID Resolver** | Python 3.11 | short_id→long_id解析 | 缓存TTL=300s |
| **Circuit Breaker** | 自研 (状态机) | 熔断保护 | threshold=5, timeout=30s |
| **Rate Limiter** | 令牌桶 | 限流保护 | 1000 RPM, burst=200 |
| **Health Check** | FastAPI端点 | 存活/就绪探测 | :9090/live,ready,startup |
| **Audit Logger** | JSON Lines | 审计日志 | /var/log/dep001/audit/ |
| **Config Manager** | ConfigMap+Secrets | 配置管理 | 热加载 |
| **DB Connector** | PyMySQL | MySQL连接 | pool=20 |
| **Redis Client** | redis-py | Redis缓存 | pool=10, TTL=300s |
| **Consul Agent** | Consul 1.16 | 服务发现 | :8500 |

### 2.3 数据流

```
请求数据流:
  ┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 客户端 │───▶│ API Gateway│───▶│ API Server│───▶│ DB/Cache│
  │      │    │ (路由/TLS) │    │ (解析)    │    │ (数据)   │
  └──────┘    └──────────┘    └──────────┘    └──────────┘
       │                                │
       │         ┌──────────┐           │
       │         │ Audit    │◀──────────┘
       │         │ Logger   │ (审计)
       │         └──────────┘
       │
       ▼
  ┌──────┐    ┌──────────┐
  │ 响应  │◀───│ 客户端    │
  │      │    │          │
  └──────┘    └──────────┘

熔断/限流数据流:
  ┌──────┐    ┌──────────────┐    ┌──────────────┐
  │ 客户端 │───▶│ Rate Limiter │───▶│ Circuit      │
  │      │    │ (限流检查)    │    │ Breaker      │
  └──────┘    └──────┬───────┘    │ (熔断检查)     │
                      │            └──────┬───────┘
                      │                    │
                      ▼                    ▼
                 ┌──────────┐         ┌──────────┐
                 │ 429限流   │         │ 503熔断   │
                 │ 返回      │         │ 返回      │
                 └──────────┘         └──────────┘
```

---

## 3. 部署架构

### 3.1 环境拓扑

| 环境 | 集群 | 命名空间 | Pod数 | 数据库 | 缓存 |
|------|------|----------|-------|--------|------|
| **预发** | dep001-preprod | dep001-preprod | 3 | preprod-db | preprod-redis |
| **生产** | dep001-prod | dep001-prod | 6 | prod-db | prod-redis |

### 3.2 K8s资源清单

```yaml
# Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dep001-api
  namespace: dep001-preprod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dep001-api
  template:
    spec:
      containers:
        - name: dep001-api
          image: registry.dep001.internal/dep001/api:v1.0.0-rc2-preprod
          ports:
            - containerPort: 8080
            - containerPort: 9090
            - containerPort: 8081
          resources:
            requests: {cpu: 2000m, memory: 512Mi}
            limits: {cpu: 4000m, memory: 1Gi}

# Service
apiVersion: v1
kind: Service
metadata:
  name: dep001-api-svc
spec:
  selector:
    app: dep001-api
  ports:
    - port: 8080
    - port: 9090
  type: ClusterIP

# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dep001-api-ingress
spec:
  rules:
    - host: dep001-api.preprod.internal
      http:
        paths:
          - path: /commodity/api
            backend:
              service: {name: dep001-api-svc, port: {number: 8080}}
          - path: /healthz
            backend:
              service: {name: dep001-api-svc, port: {number: 9090}}
```

---

## 4. 启动与停止

### 4.1 正常启动

```bash
# 1. 确认ConfigMap和Secrets已创建
kubectl get configmap dep001-api-config -n dep001-preprod
kubectl get secret dep001-api-secret -n dep001-preprod
kubectl get secret dep001-mtls-certs -n dep001-preprod

# 2. 创建Deployment
kubectl apply -f dep001-api-deployment.yaml -n dep001-preprod

# 3. 确认Pod启动
kubectl get pods -n dep001-preprod -l app=dep001-api -w

# 4. 确认Pod就绪 (所有Pod READY)
kubectl wait --for=condition=ready pod -l app=dep001-api -n dep001-preprod --timeout=120s

# 5. 确认健康探测
curl https://dep001-api.preprod.internal/healthz/ready

# 6. 确认Consul注册
curl http://consul-preprod:8500/v1/health/service/dep001-api

# 7. 确认审计日志
tail -f /var/log/dep001/audit/audit_$(date +%Y%m%d_*.log)

# 8. 确认监控指标
curl http://prometheus:9090/api/v1/query?query=dep001_api_requests_total
```

### 4.2 启动流程检查清单

| 步骤 | 检查项 | 命令 | 预期结果 |
|------|--------|------|----------|
| 1 | ConfigMap存在 | `kubectl get configmap` | 存在 |
| 2 | Secrets存在 | `kubectl get secret` | 存在 |
| 3 | Deployment创建 | `kubectl apply -f` | created/unchanged |
| 4 | Pod运行中 | `kubectl get pods` | Running |
| 5 | Pod就绪 | `kubectl wait --for=condition=ready` | condition met |
| 6 | 存活探针 | `curl /healthz/live` | HTTP 200 |
| 7 | 就绪探针 | `curl /healthz/ready` | HTTP 200 |
| 8 | Consul注册 | `curl consul/health/service` | 3 healthy |
| 9 | 审计日志 | `tail -f audit_*.log` | 日志输出 |
| 10 | 监控指标 | `curl prometheus/query` | 有指标 |

### 4.3 正常停止

```bash
# 1. 确认无活跃请求
kubectl exec -n dep001-preprod dep001-api-001 -- \
  curl -s http://localhost:8080/status | jq '.active_requests'

# 2. 减少副本数 (优雅停止)
kubectl scale deployment dep001-api --replicas=0 -n dep001-preprod

# 3. 等待Pod终止
kubectl wait --for=delete pod -l app=dep001-api -n dep001-preprod --timeout=60s

# 4. 确认Pod已删除
kubectl get pods -n dep001-preprod -l app=dep001-api

# 5. 确认Consul注销
curl http://consul-preprod:8500/v1/health/service/dep001-api

# 6. 确认审计日志 (shutdown日志)
tail -10 /var/log/dep001/audit/audit_$(date +%Y%m%d_*.log)
```

### 4.4 紧急停止

```bash
# 紧急停止 (不优雅)
kubectl delete deployment dep001-api -n dep001-preprod

# 确认全部Pod已删除
kubectl get pods -n dep001-preprod -l app=dep001-api

# 记录紧急停止事件
echo "$(date) EMERGENCY_STOP reason=<原因> by=<操作人>" >> /var/log/dep001/emergency.log
```

---

## 5. 扩容与缩容

### 5.1 水平扩容

```bash
# 手动扩容
kubectl scale deployment dep001-api --replicas=6 -n dep001-preprod

# 确认Pod就绪
kubectl wait --for=condition=ready pod -l app=dep001-api -n dep001-preprod --timeout=120s

# 确认Consul注册
curl http://consul-preprod:8500/v1/health/service/dep001-api

# 确认负载均衡 (请求分布均匀)
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -s https://dep001-api.preprod.internal/commodity/api/series?id=j25_tc
done
```

### 5.2 自动扩缩容 (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dep001-api-hpa
  namespace: dep001-preprod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dep001-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### 5.3 扩容策略

| 触发条件 | 动作 | 目标副本数 |
|----------|------|-----------|
| CPU > 75% | 扩容 | +2 |
| CPU > 85% | 紧急扩容 | +4 |
| 内存 > 80% | 扩容 | +2 |
| QPS > 3000 | 扩容 | +2 |
| 错误率 > 1% | 检查后扩容 | +2 |
| 熔断器OPEN | 不扩容 (检查根因) | — |

### 5.4 缩容策略

| 触发条件 | 动作 | 目标副本数 |
|----------|------|-----------|
| CPU < 30% 持续30min | 缩容 | -1 |
| QPS < 100 持续30min | 缩容 | -1 |
| 最少副本数 | — | 3 |

### 5.5 扩容检查清单

| 步骤 | 检查项 | 预期结果 |
|------|--------|----------|
| 1 | 当前副本数 | 3 |
| 2 | 目标副本数 | 6 |
| 3 | 资源充足 | CPU/内存配额充足 |
| 4 | Pod就绪 | 全部READY |
| 5 | Consul注册 | 6 healthy |
| 6 | 负载均衡 | 请求均匀分布 |
| 7 | 监控正常 | QPS/P95正常 |

---

## 6. 降级策略

### 6.1 降级级别

| 级别 | 触发条件 | 降级动作 | 恢复条件 |
|------|----------|----------|----------|
| L0 | 正常 | 无降级 | — |
| L1 | 错误率>1% | 缓存优先, DB只读 | 错误率<0.5% |
| L2 | 错误率>5% | 只返回缓存, 跳过DB | 错误率<1% |
| L3 | 熔断器OPEN | 返回503+降级标志 | 熔断器CLOSED |

### 6.2 降级流程

```
正常状态 (L0)
  │
  │ 错误率>1%
  ▼
降级L1: 缓存优先
  │ ├── DB查询超时 (30s) → 从缓存返回
  │ ├── 缓存未命中 → 降级响应 (包含cache_miss=true)
  │ └── 错误率<0.5% → 恢复L0
  │
  │ 错误率>5%
  ▼
降级L2: 只返回缓存
  │ ├── 跳过所有DB查询
  │ ├── 仅从Redis缓存返回
  │ └── 错误率<1% → 恢复L1
  │
  │ 熔断器OPEN
  ▼
降级L3: 熔断拦截
  │ ├── 所有请求返回503
  │ ├── 包含降级标志 (degraded=true)
  │ └── 熔断器CLOSED → 恢复L2
```

### 6.3 降级响应格式

```json
{
  "error": {
    "code": "SERVICE_DEGRADED",
    "message": "服务降级中",
    "status": 503,
    "degraded": true,
    "degrade_level": "L2",
    "cache_miss": true,
    "retry_after": 30
  },
  "meta": {
    "timestamp": "2026-10-17T10:00:00Z",
    "request_id": "req-20261017-0001",
    "trace_id": "trace-abc123"
  }
}
```

---

## 7. 故障定位

### 7.1 故障分类

| 故障类型 | 现象 | 可能原因 | 排查步骤 |
|----------|------|----------|----------|
| 服务不可用 | Pod CrashLoopBackOff | OOM/panic/配置错误 | §7.2 |
| 请求超时 | P99>500ms | DB/Cache慢查询 | §7.3 |
| 错误率高 | HTTP 500>5% | 代码bug/依赖故障 | §7.4 |
| 熔断器OPEN | 全部返回503 | 连续失败 | §7.5 |
| 限流触发 | HTTP 429 | 流量超限 | §7.6 |
| 缓存异常 | 命中率<50% | 缓存雪崩/Redis故障 | §7.7 |
| 配置错误 | 启动失败/行为异常 | ConfigMap/Secrets错误 | §7.8 |
| 网络故障 | 连接超时 | DNS/防火墙/网络 | §7.9 |

### 7.2 Pod CrashLoopBackOff排查

```bash
# 1. 查看Pod事件
kubectl describe pod <pod-name> -n dep001-preprod

# 2. 查看容器日志 (当前+上次)
kubectl logs <pod-name> -n dep001-preprod
kubectl logs <pod-name> -n dep001-preprod --previous

# 3. 查看OOM情况
kubectl describe pod <pod-name> -n dep001-preprod | grep -i oom

# 4. 检查资源限制
kubectl get pod <pod-name> -n dep001-preprod -o jsonpath='{.spec.containers[0].resources}'

# 5. 检查配置
kubectl exec <pod-name> -n dep001-preprod -- cat /etc/dep001/config/app.yaml

# 6. 重启Pod (如非配置问题)
kubectl delete pod <pod-name> -n dep001-preprod
```

### 7.3 请求超时排查

```bash
# 1. 查看延迟指标
curl http://prometheus:9090/api/v1/query?query=histogram_quantile(0.99,rate(dep001_api_latency_ms_bucket[5m]))

# 2. 检查DB延迟
kubectl exec dep001-api-001 -n dep001-preprod -- \
  mysql -h mysql-preprod -e "SHOW STATUS LIKE 'Innodb_rows_read'"

# 3. 检查Redis延迟
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod --latency

# 4. 检查连接池
curl http://prometheus:9090/api/v1/query?query=dep001_connection_pool_active/dep001_connection_pool_max

# 5. 检查网络延迟
kubectl exec dep001-api-001 -n dep001-preprod -- \
  ping -c 10 mysql-preprod
```

### 7.4 错误率高排查

```bash
# 1. 查看错误码分布
curl http://prometheus:9090/api/v1/query?query=sum by (code)(rate(dep001_api_errors_total[5m]))

# 2. 查看错误日志
kubectl logs -l app=dep001-api -n dep001-preprod --tail=100 | grep -i error

# 3. 检查DB连接
kubectl exec dep001-api-001 -n dep001-preprod -- \
  mysql -h mysql-preprod -e "SHOW PROCESSLIST"

# 4. 检查最近部署
kubectl rollout history deployment dep001-api -n dep001-preprod
```

### 7.5 熔断器排查

```bash
# 1. 查看熔断器状态
curl http://prometheus:9090/api/v1/query?query=dep001_circuit_breaker_state

# 2. 查看熔断器指标
curl http://prometheus:9090/api/v1/query?query=dep001_circuit_breaker_failure_count

# 3. 检查后端健康
kubectl exec dep001-api-001 -n dep001-preprod -- \
  curl -s http://mysql-preprod:3306

# 4. 检查缓存健康
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod ping

# 5. 手动重置熔断器 (谨慎)
kubectl exec dep001-api-001 -n dep001-preprod -- \
  curl -X POST http://localhost:8080/admin/circuit-breaker/reset
```

### 7.6 限流排查

```bash
# 1. 查看当前RPM
curl http://prometheus:9090/api/v1/query?query=dep001_rate_limiter_current_rpm

# 2. 查看限流配置
kubectl exec dep001-api-001 -n dep001-preprod -- \
  cat /etc/dep001/config/rate_limit.yaml

# 3. 查看429响应数
curl http://prometheus:9090/api/v1/query?query=rate(dep001_api_errors_total{code="429"}[5m])

# 4. 调整限流阈值 (如需要)
kubectl patch configmap dep001-api-config -n dep001-preprod \
  -p '{"data":{"rate_limit.requests_per_minute":"2000"}}'
```

### 7.7 缓存排查

```bash
# 1. 查看缓存命中率
curl http://prometheus:9090/api/v1/query?query=rate(dep001_cache_hits_total[5m])/rate(dep001_cache_requests_total[5m])

# 2. 检查Redis健康
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod INFO stats

# 3. 检查缓存驱逐
curl http://prometheus:9090/api/v1/query?query=rate(dep001_cache_evictions_total[5m])

# 4. 检查缓存大小
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod DBSIZE
```

---

## 8. 日志检索

### 8.1 日志位置

| 日志类型 | 路径 | 格式 | 轮转 |
|----------|------|------|------|
| 应用日志 | `/var/log/dep001/app/` | JSON Lines | 按天, 90天 |
| 审计日志 | `/var/log/dep001/audit/` | JSON Lines | 按天, 90天 |
| 错误日志 | `/var/log/dep001/error/` | JSON Lines | 按天, 30天 |
| 容器日志 | K8s (kubectl logs) | 文本 | 自动 |
| 访问日志 | NGINX Ingress | JSON | 按天, 30天 |

### 8.2 日志格式

```json
{
  "timestamp": "2026-10-17T10:00:01.123Z",
  "level": "INFO",
  "service": "dep001-api",
  "version": "v1.0.0-rc2",
  "pod": "dep001-api-7f8b9c6d4-x2k9m",
  "event_type": "API_REQUEST",
  "event_id": "evt-20261017-0001",
  "request_id": "req-20261017-0001",
  "method": "GET",
  "path": "/commodity/api/series",
  "query": {"id": "j25_tc"},
  "status_code": 200,
  "latency_ms": 12.3,
  "client_ip": "10.86.32.50",
  "trace_id": "trace-abc123def456"
}
```

### 8.3 常用检索命令

```bash
# 查看最近100条日志
kubectl logs -l app=dep001-api -n dep001-preprod --tail=100

# 查看特定Pod日志
kubectl logs dep001-api-001 -n dep001-preprod --tail=100

# 查看上一次崩溃日志
kubectl logs dep001-api-001 -n dep001-preprod --previous

# 实时查看日志
kubectl logs -f -l app=dep001-api -n dep001-preprod

# 按关键字搜索
kubectl logs -l app=dep001-api -n dep001-preprod --since=1h | grep -i error

# 按时间范围
kubectl logs -l app=dep001-api -n dep001-preprod --since=30m
```

### 8.4 ELK检索

| 查询场景 | Kibana查询 |
|----------|-----------|
| 最近1小时错误 | `event_type: ERROR AND @timestamp: *>now-1h` |
| 熔断器事件 | `event_type: CIRCUIT_BREAKER AND @timestamp: *>now-1h` |
| 限流事件 | `event_type: RATE_LIMIT AND @timestamp: *>now-1h` |
| 慢查询 | `latency_ms > 100 AND @timestamp: *>now-1h` |
| 特定请求 | `request_id: "req-20261017-0001"` |
| 特定trace | `trace_id: "trace-abc123"` |

---

## 9. 监控告警

### 9.1 监控仪表盘

| 仪表盘 | URL | 关键面板 |
|--------|-----|----------|
| DEP-001 Overview | http://grafana:3000/d/dep001-overview | QPS/P95/错误率/CPU/内存 |
| DEP-001 Performance | http://grafana:3000/d/dep001-perf | P50/P95/P99/连接池/缓存 |
| DEP-001 Reliability | http://grafana:3000/d/dep001-reliability | 熔断器/限流器/降级/错误码 |
| DEP-001 72h Obs | http://grafana:3000/d/dep001-longrun | 全部指标72h趋势 |

### 9.2 告警规则清单

| 规则ID | 名称 | 阈值 | 严重度 | 通知 |
|--------|------|------|--------|------|
| ALERT-01 | CPU高 | >80% 5min | WARN | 企微 |
| ALERT-02 | CPU严重 | >90% 5min | HIGH | 短信+企微 |
| ALERT-03 | 内存高 | >85% 5min | HIGH | 短信+企微 |
| ALERT-04 | 错误率高 | >1% 3min | WARN | 企微 |
| ALERT-05 | 错误率严重 | >5% 1min | CRITICAL | 短信+邮件+企微 |
| ALERT-06 | P95延迟高 | >200ms 3min | WARN | 企微 |
| ALERT-07 | P95延迟严重 | >500ms 1min | HIGH | 短信+企微 |
| ALERT-08 | 熔断器OPEN | =1 1min | CRITICAL | 短信+邮件+企微 |
| ALERT-09 | 连接池高 | >90% 5min | WARN | 企微 |
| ALERT-10 | 服务发现失败 | >3连续 1min | CRITICAL | 短信+邮件+企微 |
| ALERT-11 | 内存泄漏 | >50MB/hour 30min | WARN | 企微 |
| ALERT-12 | 磁盘高 | >85% 5min | WARN | 企微 |

### 9.3 告警响应流程

```
告警触发
  │
  ▼
确认告警 (查看仪表盘)
  │
  ├── 误报 → 调整告警阈值
  │
  ▼
定位根因 (查看日志/指标)
  │
  ├── 已知问题 → 执行已知修复流程
  │
  ▼
评估影响 (用户影响范围)
  │
  ├── CRITICAL → 立即执行应急预案 (§15)
  │
  ▼
执行修复
  │
  ├── 扩容 → kubectl scale
  │ ├── 重启 → kubectl delete pod
  │ ├── 回滚 → kubectl rollout undo
  │ └── 降级 → 执行降级策略 (§6)
  │
  ▼
验证恢复
  │
  ├── 告警恢复 → 记录事件
  │
  ▼
记录事件 (更新事件日志)
```

---

## 10. 灾备切换

### 10.1 灾备架构

```
主集群 (dep001-preprod)
  │
  │ 数据同步 (异步)
  ▼
灾备集群 (dep001-dr)
  │
  │ DNS切换 (30秒TTL)
  ▼
客户端 (DSHB/DSHE/HERMES)
```

### 10.2 RTO/RPO目标

| 指标 | 目标 | 说明 |
|------|------|------|
| **RTO** | <30分钟 | 从故障发生到服务恢复 |
| **RPO** | <5分钟 | 数据丢失时间窗口 |

### 10.3 灾备切换流程

```bash
# 1. 确认主集群故障
kubectl get pods -n dep001-preprod -l app=dep001-api

# 2. 评估影响
echo "时间: $(date)"
echo "主集群状态: $(kubectl get pods -n dep001-preprod -l app=dep001-api --no-headers | wc -l) ready"

# 3. 检查灾备集群就绪
kubectl get pods -n dep001-dr -l app=dep001-api

# 4. 确认灾备集群健康
curl http://consul-dr:8500/v1/health/service/dep001-api

# 5. DNS切换 (30秒TTL)
dig dep001-api.preprod.internal
echo "新IP: <灾备集群IP>"

# 6. 确认切换成功
for i in 1 2 3; do
  curl -s https://dep001-api.preprod.internal/healthz/ready
  sleep 30  # 等待DNS TTL
done

# 7. 确认监控切换
curl http://prometheus-dr:9090/api/v1/query?query=dep001_api_requests_total

# 8. 通知团队
echo "灾备切换完成: $(date)" | 通知 DSHB+DSHE+HERMES
```

### 10.4 回切流程

```bash
# 1. 确认主集群恢复
kubectl get pods -n dep001-preprod -l app=dep001-api
kubectl wait --for=condition=ready pod -l app=dep001-api -n dep001-preprod --timeout=120s

# 2. 确认数据同步 (无数据丢失)
echo "检查数据同步状态: $(date)"

# 3. DNS回切
echo "回切DNS: $(date)"

# 4. 确认回切成功
for i in 1 2 3; do
  curl -s https://dep001-api.preprod.internal/healthz/ready
  sleep 30
done

# 5. 关闭灾备集群
kubectl scale deployment dep001-api --replicas=0 -n dep001-dr

# 6. 通知团队
echo "回切完成: $(date)" | 通知 DSHB+DSHE+HERMES
```

---

## 11. 证书管理

### 11.1 证书清单

| 证书 | 用途 | 有效期 | 轮换周期 | 位置 |
|------|------|--------|----------|------|
| Root CA | CA签发 | 2年 | 2年 | `ca-bundle.pem` |
| Server Cert | API服务器 | 1年 | 1年 | `server.pem` |
| Client Cert (DSHB) | DSHB客户端 | 1年 | 1年 | `client-dshb.pem` |
| Client Cert (DSHE) | DSHE客户端 | 1年 | 1年 | `client-dshe.pem` |
| Client Cert (HERMES) | HERMES客户端 | 1年 | 1年 | `client-hermes.pem` |

### 11.2 证书轮换流程

```bash
# 1. 生成新证书
openssl req -new -key client-key.pem -out client.csr -subj "/CN=dshb-gate-client"
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out client-new.pem -days 365

# 2. 更新K8s Secret
kubectl create secret tls dep001-client-certs \
  --cert=client-new.pem \
  --key=client-key.pem \
  --dry-run=client -o yaml | kubectl apply -f - -n dep001-preprod

# 3. 滚动重启Pod (加载新证书)
kubectl rollout restart deployment dep001-api -n dep001-preprod

# 4. 确认新证书生效
kubectl exec dep001-api-001 -n dep001-preprod -- \
  openssl x509 -in /etc/ssl/dep001/client.pem -noout -dates

# 5. 确认mTLS连接正常
curl -s https://dep001-api.preprod.internal/healthz/ready
```

### 11.3 证书过期监控

```yaml
# Prometheus告警规则
- alert: Dep001CertExpiringSoon
  expr: dep001_tls_cert_expiry_days < 30
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "DEP-001 TLS证书将在{{ $value }}天内过期"

- alert: Dep001CertExpiringCritical
  expr: dep001_tls_cert_expiry_days < 7
  for: 1h
  labels:
    severity: critical
  annotations:
    summary: "DEP-001 TLS证书将在{{ $value }}天内过期 — 紧急"
```

---

## 12. Token管理

### 12.1 Token信息

| 项目 | 值 |
|------|-----|
| Token格式 | Bearer Token (JWT) |
| 有效期 | 90天 |
| 轮换周期 | 90天 (提前7天提醒) |
| 存储位置 | K8s Secret `dep001-api-secret` |
| 吊销方式 | 服务器端吊销列表 + K8s Secret更新 |

### 12.2 Token轮换流程

```bash
# 1. 生成新Token
export NEW_TOKEN=$(python3 -c "
import jwt, datetime
token = jwt.encode({
    'sub': 'dshb-gate-client',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=90),
    'iat': datetime.datetime.utcnow()
}, 'secret-key', algorithm='HS256')
print(token)
")

# 2. 更新K8s Secret
kubectl create secret generic dep001-api-secret \
  --from-literal=api_token=$NEW_TOKEN \
  --from-literal=token_expiry=$(date -d '+90 days' +%Y-%m-%d) \
  --dry-run=client -o yaml | kubectl apply -f - -n dep001-preprod

# 3. 滚动重启Pod (加载新Token)
kubectl rollout restart deployment dep001-api -n dep001-preprod

# 4. 确认新Token生效
curl -s -H "Authorization: Bearer $NEW_TOKEN" \
  https://dep001-api.preprod.internal/healthz/ready

# 5. 确认旧Token已失效
curl -s -H "Authorization: Bearer $OLD_TOKEN" \
  https://dep001-api.preprod.internal/healthz/ready
```

### 12.3 Token过期监控

```yaml
# Prometheus告警规则
- alert: Dep001TokenExpiringSoon
  expr: dep001_token_expiry_days < 14
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "DEP-001 API Token将在{{ $value }}天后过期"

- alert: Dep001TokenExpired
  expr: dep001_token_expiry_days < 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "DEP-001 API Token已过期 — 紧急轮换"
```

---

## 13. 配置管理

### 13.1 配置文件位置

| 配置类型 | 路径 | 管理方式 | 热加载 |
|----------|------|----------|--------|
| 应用配置 | `/etc/dep001/config/app.yaml` | ConfigMap | ✅ |
| 限流配置 | `/etc/dep001/config/rate_limit.yaml` | ConfigMap | ✅ |
| 熔断配置 | `/etc/dep001/config/circuit_breaker.yaml` | ConfigMap | ✅ |
| 数据库配置 | K8s Secret | Secret | ❌ (需重启) |
| 缓存配置 | `/etc/dep001/config/cache.yaml` | ConfigMap | ✅ |
| 日志配置 | `/etc/dep001/config/logging.yaml` | ConfigMap | ✅ |

### 13.2 配置更新流程

```bash
# 1. 更新ConfigMap
kubectl edit configmap dep001-api-config -n dep001-preprod

# 或
kubectl patch configmap dep001-api-config -n dep001-preprod \
  -p '{"data":{"api.max_concurrency":"200"}}'

# 2. 热加载 (支持热加载的配置)
# 无需重启Pod, ConfigMap自动同步

# 3. 滚动重启 (不支持热加载的配置)
kubectl rollout restart deployment dep001-api -n dep001-preprod

# 4. 确认配置生效
kubectl exec dep001-api-001 -n dep001-preprod -- \
  cat /etc/dep001/config/app.yaml | grep -A5 "max_concurrency"
```

### 13.3 配置回滚

```bash
# 1. 查看配置历史
kubectl rollout history configmap dep001-api-config -n dep001-preprod

# 2. 回滚到上一个版本
kubectl rollout undo configmap dep001-api-config -n dep001-preprod

# 3. 回滚到指定版本
kubectl rollout undo configmap dep001-api-config -n dep001-preprod --to-revision=2

# 4. 确认回滚
kubectl exec dep001-api-001 -n dep001-preprod -- \
  cat /etc/dep001/config/app.yaml
```

---

## 14. 维护操作

### 14.1 版本升级

```bash
# 1. 确认新版本镜像
docker pull registry.dep001.internal/dep001/api:v1.0.1-rc2

# 2. 更新Deployment镜像
kubectl set image deployment/dep001-api \
  dep001-api=registry.dep001.internal/dep001/api:v1.0.1-rc2 \
  -n dep001-preprod

# 3. 确认滚动更新
kubectl rollout status deployment dep001-api -n dep001-preprod --timeout=300s

# 4. 确认新版本健康
kubectl get pods -n dep001-preprod -l app=dep001-api
kubectl wait --for=condition=ready pod -l app=dep001-api -n dep001-preprod --timeout=120s

# 5. 确认监控正常
curl https://dep001-api.preprod.internal/healthz/ready

# 6. 确认审计日志
tail -10 /var/log/dep001/audit/audit_$(date +%Y%m%d_*.log)
```

### 14.2 版本回滚

```bash
# 1. 查看部署历史
kubectl rollout history deployment dep001-api -n dep001-preprod

# 2. 回滚到上一个版本
kubectl rollout undo deployment dep001-api -n dep001-preprod

# 3. 回滚到指定版本
kubectl rollout undo deployment dep001-api -n dep001-preprod --to-revision=3

# 4. 确认回滚完成
kubectl rollout status deployment dep001-api -n dep001-preprod

# 5. 确认健康
curl https://dep001-api.preprod.internal/healthz/ready
```

### 14.3 数据库维护

```bash
# 1. 检查DB连接
kubectl exec dep001-api-001 -n dep001-preprod -- \
  mysql -h mysql-preprod -e "SHOW STATUS LIKE 'Threads_connected'"

# 2. 检查DB慢查询
kubectl exec dep001-api-001 -n dep001-preprod -- \
  mysql -h mysql-preprod -e "SHOW FULL PROCESSLIST"

# 3. 数据库备份
kubectl exec dep001-api-001 -n dep001-preprod -- \
  mysqldump -h mysql-preprod dep001_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 4. 数据库索引优化
kubectl exec dep001-api-001 -n dep001-preprod -- \
  mysql -h mysql-preprod dep001_db -e "ANALYZE TABLE short_id_mapping"
```

### 14.4 Redis维护

```bash
# 1. 检查Redis状态
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod INFO

# 2. 检查Redis内存
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod INFO memory

# 3. 清理过期Key
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod --scan --pattern "dep001:*" | wc -l

# 4. Redis持久化检查
kubectl exec dep001-api-001 -n dep001-preprod -- \
  redis-cli -h redis-preprod INFO persistence
```

---

## 15. 应急预案

### 15.1 应急预案清单

| 预案ID | 场景 | 严重度 | 响应时间 | 负责团队 |
|--------|------|--------|----------|----------|
| ER-01 | 服务完全不可用 | P0 | <5min | SRE |
| ER-02 | 数据丢失 | P0 | <5min | DBA |
| ER-03 | 安全事件 | P0 | <5min | 安全团队 |
| ER-04 | 大规模错误率>5% | P1 | <15min | SRE |
| ER-05 | 熔断器持续OPEN | P1 | <15min | SRE |
| ER-06 | 缓存雪崩 | P1 | <15min | SRE |
| ER-07 | 证书过期 | P2 | <30min | SRE |
| ER-08 | Token过期 | P2 | <30min | SRE |

### 15.2 应急预案ER-01: 服务完全不可用

```
┌──────────────────────────────────────────────────────────────────┐
│  应急预案ER-01: 服务完全不可用                                       │
│  严重度: P0 / 响应时间: <5min                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  触发条件:                                                        │
│  ├── 所有Pod CrashLoopBackOff                                    │
│  ├── 服务不可达 (DNS解析失败或连接超时)                              │
│  └── HTTP 503 (全部请求被拒绝)                                    │
│                                                                  │
│  响应流程:                                                        │
│  │                                                              │
│  ├── 1. 确认故障 (5分钟)                                         │
│  │   ├── kubectl get pods -n dep001-preprod                    │
│  │   ├── kubectl describe pod dep001-api-001 -n dep001-preprod │
│  │   └── kubectl logs dep001-api-001 --previous                │
│  │                                                              │
│  ├── 2. 评估根因 (5分钟)                                         │
│  │   ├── OOM → 调整资源限制, 扩容                                │
│  │   ├── 配置错误 → 回滚配置                                     │
│  │   ├── 镜像问题 → 回滚镜像                                     │
│  │   └── 依赖故障 → 降级/灾备切换                                │
│  │                                                              │
│  ├── 3. 执行修复 (10分钟)                                        │
│  │   ├── 回滚: kubectl rollout undo deployment dep001-api       │
│  │   ├── 扩容: kubectl scale deployment dep001-api --replicas=6 │
│  │   └── 灾备: 执行灾备切换流程 (§10.3)                          │
│  │                                                              │
│  ├── 4. 验证恢复 (5分钟)                                         │
│  │   ├── curl https://dep001-api.preprod.internal/healthz/ready │
│  │   └── 确认监控指标恢复正常                                     │
│  │                                                              │
│  └── 5. 记录事件                                                 │
│     └── 更新事件日志, 通知DSHB/DSHE/HERMES                        │
│                                                                  │
│  总响应时间: <25min                                              │
└──────────────────────────────────────────────────────────────────┘
```

### 15.3 应急预案ER-04: 大规模错误率>5%

```
┌──────────────────────────────────────────────────────────────────┐
│  应急预案ER-04: 大规模错误率>5%                                    │
│  严重度: P1 / 响应时间: <15min                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  触发条件:                                                        │
│  └── 错误率>5% 持续1分钟                                         │
│                                                                  │
│  响应流程:                                                        │
│  │                                                              │
│  ├── 1. 确认故障 (5分钟)                                         │
│  │   ├── 查看错误码分布                                          │
│  │   └── 查看最近部署                                            │
│  │                                                              │
│  ├── 2. 定位根因 (5分钟)                                         │
│  │   ├── 500错误 → 检查代码/DB/Cache                             │
│  │   ├── 503错误 → 检查熔断器                                    │
│  │   ├── 504错误 → 检查超时/网络                                 │
│  │   └── 429错误 → 检查限流器                                    │
│  │                                                              │
│  ├── 3. 执行修复 (5分钟)                                         │
│  │   ├── 回滚 → kubectl rollout undo                            │
│  │   ├── 降级 → 执行降级策略 (§6)                                │
│  │   └── 扩容 → kubectl scale                                   │
│  │                                                              │
│  └── 4. 验证恢复 + 记录事件                                      │
│                                                                  │
│  总响应时间: <15min                                              │
└──────────────────────────────────────────────────────────────────┘
```

### 15.4 事件记录模板

```yaml
# 事件记录模板
event_id: EVT-20261017-001
event_type: SERVICE_UNAVAILABLE
severity: P0
timestamp: 2026-10-17T10:00:00Z
detect_time: 2026-10-17T10:01:00Z
resolve_time: 2026-10-17T10:20:00Z
duration_min: 19
root_cause: 镜像v1.0.1-rc2存在配置错误
impact: "全部请求失败, data_fetchable_rate=0%"
action_taken: "kubectl rollout undo deployment dep001-api"
resolved_by: "kubectl rollout undo"
affected_services: [DSHB, DSHE, HERMES]
affected_clients: [dshb-gate, dshe-alert, hermes-audit]
notifications_sent:
  - channel: 企微
    timestamp: 2026-10-17T10:02:00Z
  - channel: 短信
    timestamp: 2026-10-17T10:02:00Z
postmortem: "需审查镜像发布流程"
```

---

## 16. 附录

### 16.1 常用命令速查表

| 操作 | 命令 |
|------|------|
| 查看Pod | `kubectl get pods -n dep001-preprod -l app=dep001-api` |
| 查看日志 | `kubectl logs -l app=dep001-api -n dep001-preprod --tail=100` |
| 实时日志 | `kubectl logs -f -l app=dep001-api -n dep001-preprod` |
| 扩缩容 | `kubectl scale deployment dep001-api --replicas=<N> -n dep001-preprod` |
| 滚动重启 | `kubectl rollout restart deployment dep001-api -n dep001-preprod` |
| 回滚 | `kubectl rollout undo deployment dep001-api -n dep001-preprod` |
| 查看状态 | `kubectl rollout status deployment dep001-api -n dep001-preprod` |
| 描述Pod | `kubectl describe pod <name> -n dep001-preprod` |
| 执行命令 | `kubectl exec <name> -n dep001-preprod -- <cmd>` |
| 健康检查 | `curl https://dep001-api.preprod.internal/healthz/ready` |
| 服务状态 | `curl https://dep001-api.preprod.internal/status` |

### 16.2 联系信息

| 团队 | 角色 | 联系方式 | 响应时间 |
|------|------|----------|----------|
| DSHB SRE | 主联系人 | sre-dshb@company.com | <5min (P0) |
| DSHB SRE | 备份联系人 | sre-dshb-backup@company.com | <15min (P0) |
| 数据库DBA | 主联系人 | dba@company.com | <15min (P0) |
| 安全团队 | 主联系人 | security@company.com | <15min (P0) |
| 网络运维 | 主联系人 | network@company.com | <30min (P1) |
| Consul运维 | 主联系人 | consul-ops@company.com | <30min (P1) |

### 16.3 FAQ

**Q1: 如何快速确认服务是否正常？**

```bash
curl -s https://dep001-api.preprod.internal/healthz/ready | jq '.status'
# 预期输出: "ready"
```

**Q2: 如何快速扩容？**

```bash
kubectl scale deployment dep001-api --replicas=6 -n dep001-preprod
kubectl wait --for=condition=ready pod -l app=dep001-api -n dep001-preprod --timeout=120s
```

**Q3: 如何快速回滚？**

```bash
kubectl rollout undo deployment dep001-api -n dep001-preprod
kubectl rollout status deployment dep001-api -n dep001-preprod
```

**Q4: 如何查看熔断器状态？**

```bash
curl http://prometheus:9090/api/v1/query?query=dep001_circuit_breaker_state
# 0=CLOSED, 1=OPEN, 2=HALF_OPEN
```

**Q5: 如何查看缓存命中率？**

```bash
curl http://prometheus:9090/api/v1/query?query=rate(dep001_cache_hits_total[5m])/rate(dep001_cache_requests_total[5m])
```

**Q6: 证书过期了怎么办？**

```bash
# 紧急轮换 (见§11.2)
kubectl create secret tls dep001-client-certs \
  --cert=client-new.pem --key=client-key.pem \
  --dry-run=client -o yaml | kubectl apply -f - -n dep001-preprod
kubectl rollout restart deployment dep001-api -n dep001-preprod
```

**Q7: 如何查看最近1小时的错误日志？**

```bash
kubectl logs -l app=dep001-api -n dep001-preprod --since=1h | grep -i error
```

### 16.4 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-10-17 | 初始版本，16章节完整交付 | DSHB Team |

---

> **文档结束**
> **DEP-001运维手册: 🟢 16章节完整交付**
> **适用版本: v1.0.0-rc2 | 分支: feature/v85-chart-template**
