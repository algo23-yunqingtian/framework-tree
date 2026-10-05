# DEP-001 周期性联动巡检任务规范 V1.0

> **工单编号**: DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE / T3.2  
> **脚本文件**: `dep001_periodic_probe.py`  
> **脚本版本**: V1.0  
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE  
> **文档版本**: V1.0  
> **编制日期**: 2026-10-17  

---

## 目录

1. [概述](#1-概述)
2. [架构设计](#2-架构设计)
3. [配置规范](#3-配置规范)
4. [巡检类型详解](#4-巡检类型详解)
5. [告警分级机制](#5-告警分级机制)
6. [Gate 状态回写](#6-gate-状态回写)
7. [指标埋点对齐](#7-指标埋点对齐)
8. [部署与调度](#8-部署与调度)
9. [接口契约](#9-接口契约)
10. [跨团队集成](#10-跨团队集成)
11. [自检与测试](#11-自检与测试)
12. [运行参数参考](#12-运行参数参考)

---

## 1. 概述

### 1.1 背景

DEP-001（zhiji 数据平台短ID前缀解析服务）在预发环境已完成部署、压力测试、Gate V5 真实集成 E2E 和 72h 长时观测，R-DEP-07 风险已闭环（`WAIT_REAL_ENV_VERIFY` → `DRYRUN_VERIFIED`）。当前 DEP-001 预发服务已就绪（`B_PROD_PHASE_DEP001_SERVICE_READY=TRUE`），具备启动 G0 影子投产条件。

然而，DEP-001 当前缺少周期性自动巡检任务，无法实现：
- 实时健康状态监控
- 短ID数据质量持续校验
- 异常自动感知与 Gate 状态刷新
- 熔断器/限流器状态自动采集

### 1.2 目标

开发 `dep001_periodic_probe.py` 周期性联动巡检脚本，实现：

1. ✅ **定时健康探测**: 默认 60s 周期调用 DEP-001 `/healthz` 端点
2. ✅ **短ID抽样校验**: 每周期随机抽取 10 个指标短ID进行查询验证
3. ✅ **P95 耗时统计**: 滚动窗口计算 P50/P95/P99 延迟百分位
4. ✅ **错误码统计**: 分类统计 HTTP 4xx/5xx 及 mTLS 失败
5. ✅ **熔断状态采集**: 采集 DEP-001 熔断器状态（CLOSED/HALF_OPEN/OPEN）
6. ✅ **Gate 状态回写**: 巡检结果通过 REST API 回写至 Gate 服务
7. ✅ **告警分级**: P0（阻断）/ P1（警告）/ P2（观测）三级告警
8. ✅ **自检功能**: `--self-test` 内置 37 项自检测试

### 1.3 设计原则

| 原则 | 说明 |
|------|------|
| **非侵入式** | 巡检脚本独立运行，不修改 DEP-001 服务代码 |
| **可配置** | 调度周期、抽样数量、阈值均可配置 |
| **双模式** | 支持 simulation_mode（模拟）和 real_mode（真实） |
| **幂等性** | 重复执行不会产生副作用 |
| **优雅降级** | 网络异常不导致进程崩溃 |
| **指标对齐** | 输出指标格式对齐 HERMES 审计和 DSHE L2 面板 |

---

## 2. 架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    DSHB V86-RC2 Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────────┐     ┌─────────────┐ │
│  │              │     │                  │     │             │ │
│  │  DEP-001     │◄────│  dep001_probe.py │────►│  Gate V5    │ │
│  │  Service     │     │  (巡检引擎)        │     │  Service    │ │
│  │  (Pre-prod)  │     │                  │     │  (Pre-prod) │ │
│  │              │     │  - Health Probe  │     │             │ │
│  │  /healthz    │     │  - Short ID Probe│     │  - Status   │ │
│  │  /series     │     │  - P95 Stats     │     │  - Alert    │ │
│  │  /cb-state   │     │  - Error Stats   │     │  - Decision │ │
│  └──────────────┘     │  - CB Collection │     └─────────────┘ │
│                        └────────┬─────────┘                      │
│                                 │                                │
│                                 ▼                                │
│                        ┌──────────────────┐                      │
│                        │  probe_logs/      │                      │
│                        │  probe_result_    │                      │
│                        │  latest.json      │                      │
│                        └──────────────────┘                      │
│                                                                  │
│  ┌──────────────┐     ┌──────────────────┐                      │
│  │  HERMES       │     │  DSHE L2 Panel    │                      │
│  │  Auditor      │◄────│  (Metrics消费)     │                      │
│  └──────────────┘     └──────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 巡检流程

```
┌──────────────────────────────────────────────────────────────────┐
│                    Probe Cycle Flow                              │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌────────────────┐   │
│  │  1. 健康探测   │───►│  2. 短ID抽样   │───►│  3. 熔断状态    │   │
│  │  /healthz     │    │  /series?id   │    │  /cb-state     │   │
│  │  (5s timeout) │    │  (10 IDs)     │    │                │   │
│  └───────────────┘    └───────────────┘    └────────┬───────┘   │
│                                                      │          │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  4. 统计计算                                          │        │
│  │  - P50/P95/P99 延迟                                 │        │
│  │  - 成功率/错误率                                     │        │
│  │  - 错误码分类                                        │        │
│  │  - 连续失败计数                                      │        │
│  └─────────────────────┬───────────────────────────────┘        │
│                        │                                          │
│  ┌─────────────────────▼───────────────────────────────┐        │
│  │  5. 告警判定                                          │        │
│  │  P0: 全失败/CB_OPEN/健康DOWN                          │        │
│  │  P1: P95>300ms/错误率>5%/连续失败≥3                   │        │
│  │  P2: P95>150ms/错误率>1%/CB_HALF_OPEN                │        │
│  └─────────────────────┬───────────────────────────────┘        │
│                        │                                          │
│  ┌─────────────────────▼───────────────────────────────┐        │
│  │  6. Gate 回写                                          │        │
│  │  POST /api/v1/dep/probe-result                        │        │
│  │  - status: READY / NOT_READY                          │        │
│  │  - alert_level: P0/P1/P2/NONE                        │        │
│  └──────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  7. 日志与存储                                             │   │
│  │  - probe_logs/probe_YYYYMMDD_HHMMSS.log                  │   │
│  │  - probe_result_latest.json                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 核心组件

| 组件 | 类/函数 | 职责 |
|------|---------|------|
| 配置管理 | `DEFAULT_CONFIG` | 集中配置调度、端点、阈值、指标 |
| 结果模型 | `ProbeResult` | 封装单周期巡检结果，计算告警 |
| 巡检引擎 | `DepProbeEngine` | 执行巡检循环、调用 DEP、回写 Gate |
| 自检套件 | `run_self_test()` | 37 项自动化测试覆盖全部组件 |
| CLI 入口 | `main()` | 参数解析、配置加载、引擎启动 |

---

## 3. 配置规范

### 3.1 核心配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `probe_interval_seconds` | int | 60 | 巡检周期（秒） |
| `max_duration_seconds` | int | 0 | 最大运行时长（0=永久） |
| `dep_base_url` | str | `https://dep-001.preprod.svc:8443` | DEP-001 服务地址 |
| `gate_base_url` | str | `https://gate.svc:9090` | Gate 服务地址 |
| `short_id_sample_count` | int | 10 | 每周期抽样短ID数量 |
| `total_indicators` | int | 178 | DEP-001 总指标数 |
| `latency_window_size` | int | 50 | P95 滚动窗口大小 |
| `simulation_mode` | bool | True | 模拟模式（预发环境） |

### 3.2 阈值配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `latency_p95_threshold_ms` | int | 200 | P95 延迟阈值（告警） |
| `latency_p99_threshold_ms` | int | 500 | P99 延迟阈值（严重） |
| `error_rate_threshold_pct` | float | 1.0 | 错误率阈值（告警） |
| `consecutive_failure_threshold` | int | 3 | 连续失败阈值（告警） |
| `p95_latency_warn_ms` | int | 150 | P95 警告阈值 |
| `p95_latency_fail_ms` | int | 300 | P95 失败阈值 |
| `cb_open_threshold` | int | 3 | 熔断器打开阈值 |
| `cb_half_open_timeout_seconds` | int | 30 | 熔断器半开超时 |

### 3.3 告警配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `alert_p0` | str | `P0_CRITICAL` | P0 告警级别标签 |
| `alert_p1` | str | `P1_HIGH` | P1 告警级别标签 |
| `alert_p2` | str | `P2_WARN` | P2 告警级别标签 |

### 3.4 安全配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `mtls_enabled` | bool | True | mTLS 双向认证 |
| `ca_cert_path` | str | None | CA 证书路径 |
| `client_cert_path` | str | None | 客户端证书路径 |
| `client_key_path` | str | None | 客户端私钥路径 |

---

## 4. 巡检类型详解

### 4.1 健康探测 (Health Probe)

**端点**: `GET /healthz`  
**超时**: 10s  
**预期响应**: HTTP 200, `{"status": "UP", "version": "x.x.x"}`

| 响应状态 | 判定 | 说明 |
|----------|------|------|
| 200 UP | HEALTHY | 服务正常 |
| 200 DEGRADED | DEGRADED | 服务降级（部分功能不可用） |
| 503 / 超时 | DOWN | 服务不可用 |

### 4.2 短ID抽样校验 (Short ID Sampling)

**端点**: `GET /commodity/api/series?id={short_id}`  
**抽样策略**: 每周期从 30 个预定义短ID中随机抽取 10 个

**短ID覆盖范围**（8品种）：

| 品种 | 短ID前缀 | 覆盖数 |
|------|---------|--------|
| 铅(PB) | `j25_pb_*` | 4 |
| 铜(CU) | `j25_cu_*` | 4 |
| 铝(AL) | `j25_al_*` | 4 |
| 金(AU) | `j25_au_*` | 4 |
| 银(AG) | `j25_ag_*` | 4 |
| 镍(NI) | `j25_ni_*` | 4 |
| 锡(SN) | `j25_sn_*` | 4 |
| 锌(ZN) | `j25_zn_*` | 4 |

**预期响应**:
```json
{
  "id": "j25_pb_001",
  "name": "铅锭社会库存",
  "data": [...],
  "metadata": {"commodity": "pb", "indicator_type": "inventory"}
}
```

### 4.3 P95 延迟统计

**计算方法**:
- **P50**（中位数）: `statistics.median(latencies)`
- **P95**: `statistics.quantiles(latencies, n=20)[18]`（滚动窗口）
- **P99**: `statistics.quantiles(latencies, n=100)[98]`（至少 20 个样本）

**阈值**：

| 百分位 | 警告阈值 | 失败阈值 |
|--------|---------|---------|
| P50 | 50ms | 100ms |
| P95 | 150ms | 300ms |
| P99 | 400ms | 800ms |

### 4.4 错误码统计

| 错误码 | 分类 | 含义 |
|--------|------|------|
| 401 | 鉴权失败 | mTLS 证书无效/过期 |
| 403 | 权限拒绝 | Token 权限不足 |
| 404 | 资源不存在 | 短ID 无效 |
| 429 | 限流 | 触发令牌桶限流 |
| 500 | 内部错误 | DEP 服务内部异常 |
| 502 | 网关错误 | 上游服务异常 |
| 503 | 服务不可用 | DEP 熔断/维护 |
| 504 | 网关超时 | 上游响应超时 |

### 4.5 熔断状态采集

**端点**: `GET /metrics/circuit-breaker`  
**预期响应**:
```json
{
  "state": "CLOSED",
  "failures": 0,
  "half_open_attempts": 0,
  "last_state_change": "2026-10-17T10:00:00Z"
}
```

| 状态 | 含义 | Gate 影响 |
|------|------|----------|
| CLOSED | 正常 | 无影响 |
| HALF_OPEN | 恢复中 | P2 告警 |
| OPEN | 熔断 | P0 阻断 |

---

## 5. 告警分级机制

### 5.1 告警级别定义

| 级别 | 标签 | 含义 | Gate 影响 |
|------|------|------|----------|
| **P0** | `P0_CRITICAL` | 严重故障 | Gate=NOT_READY |
| **P1** | `P1_HIGH` | 高度警告 | Gate=WARN |
| **P2** | `P2_WARN` | 低度告警 | Gate=OBSERVE |
| NONE | - | 正常 | Gate=READY |

### 5.2 告警触发条件

**P0（阻断级）**：
| 条件 | 阈值 | 说明 |
|------|------|------|
| 全量失败 | 100% 查询失败 | DEP 完全不可用 |
| 成功率极低 | < 50% | 服务严重降级 |
| 熔断器 OPEN | state=OPEN | DEP 已熔断 |
| 健康探测 DOWN | /healthz 非 200 | 服务宕机 |

**P1（警告级）**：
| 条件 | 阈值 | 说明 |
|------|------|------|
| P95 延迟高 | > 300ms | 服务响应缓慢 |
| 错误率高 | > 5% | 服务不稳定 |
| 连续失败 | ≥ 3 次 | 可能为持续性故障 |

**P2（观测级）**：
| 条件 | 阈值 | 说明 |
|------|------|------|
| P95 延迟偏高 | > 150ms | 服务略有延迟 |
| 错误率偏高 | > 1% | 偶发异常 |
| 熔断器 HALF_OPEN | state=HALF_OPEN | 服务恢复中 |

### 5.3 告警去重与抑制

- **去重窗口**: 同一告警在 5 分钟内不重复发送
- **抑制规则**: P0 告警触发后，P1/P2 告警被抑制
- **恢复通知**: 告警消除后发送恢复通知

---

## 6. Gate 状态回写

### 6.1 回写接口

**端点**: `POST /api/v1/dep/probe-result`  
**方法**: HTTP POST  
**Content-Type**: `application/json`  
**认证**: mTLS 双向认证

**请求体**:
```json
{
  "dep_id": "DEP-001",
  "probe_result": {
    "cycle_id": 1,
    "timestamp": "2026-10-17T10:00:00",
    "health_status": "UP",
    "total_queries": 10,
    "success_queries": 10,
    "success_rate_pct": 100.0,
    "p50_latency_ms": 15.2,
    "p95_latency_ms": 18.5,
    "circuit_breaker_state": "CLOSED",
    "alert_level": "NONE",
    "overall_pass": true
  },
  "gate_update": {
    "status": "READY",
    "reason": "All probes passed",
    "alert_level": "NONE",
    "consecutive_failures": 0
  }
}
```

### 6.2 Gate 状态映射

| 巡检结果 | Gate 状态 | 说明 |
|----------|----------|------|
| 全 PASS + NONE alert | `READY` | 服务正常 |
| P2 告警 | `READY` | 低度告警，不阻断 |
| P1 告警 | `WARN` | 高度警告，观察 |
| P0 告警 | `NOT_READY` | 严重故障，阻断 |
| 连续失败 ≥ 3 | `NOT_READY` | 持续性故障 |
| 熔断器 OPEN | `NOT_READY` | DEP 熔断 |

### 6.3 回写失败处理

| 场景 | 处理方式 |
|------|---------|
| Gate 不可达 | 重试 3 次，指数退避（1s→2s→4s） |
| Gate 返回错误 | 记录错误日志，标记回写失败 |
| 回写超时 | 10s 超时，跳过等待下一周期 |
| 回写失败 > 5 次 | 发送 P1 告警通知运维 |

---

## 7. 指标埋点对齐

### 7.1 输出指标清单

| 指标名称 | 类型 | 单位 | 对齐目标 |
|----------|------|------|---------|
| `dep_probe_cycle_id` | counter | - | HERMES 审计 |
| `dep_probe_total_queries` | counter | 次 | HERMES 审计 |
| `dep_probe_success_queries` | counter | 次 | DSHE L2 面板 |
| `dep_probe_error_queries` | counter | 次 | DSHE L2 面板 |
| `dep_probe_success_rate` | gauge | % | DSHE L2 面板 |
| `dep_probe_p50_latency` | gauge | ms | DSHE L2 面板 |
| `dep_probe_p95_latency` | gauge | ms | DSHE L2 面板 |
| `dep_probe_p99_latency` | gauge | ms | DSHE L2 面板 |
| `dep_probe_health_status` | gauge | - | DSHE L2 面板 |
| `dep_probe_cb_state` | gauge | - | DSHE L2 面板 |
| `dep_probe_consecutive_failures` | gauge | 次 | HERMES 审计 |
| `dep_probe_alert_level` | gauge | - | HERMES 审计 |
| `dep_gate_writeback_status` | gauge | - | HERMES 审计 |

### 7.2 HERMES 审计对齐

HERMES evidence_auditor_v2_plus 需要以下字段：

| 字段 | 类型 | 示例 |
|------|------|------|
| `dep_id` | string | `"DEP-001"` |
| `probe_timestamp` | string (ISO) | `"2026-10-17T10:00:00Z"` |
| `probe_cycle_id` | int | `1` |
| `overall_pass` | bool | `true` |
| `alert_level` | string | `"NONE"` |
| `p0_count` | int | `0` |
| `p1_count` | int | `0` |
| `p2_count` | int | `0` |

### 7.3 DSHE L2 面板对齐

DSHE L2 面板需要以下指标展示：

| 面板 | 指标 | 数据源 |
|------|------|--------|
| 健康状态 | `dep_probe_health_status` | ProbeResult.health_status |
| 成功率 | `dep_probe_success_rate` | ProbeResult.success_rate |
| P95 延迟 | `dep_probe_p95_latency` | ProbeResult.p95_latency_ms |
| 熔断状态 | `dep_probe_cb_state` | ProbeResult.circuit_breaker_state |
| 告警级别 | `dep_probe_alert_level` | ProbeResult.alert_level |
| 连续失败 | `dep_probe_consecutive_failures` | ProbeResult.consecutive_failures |

---

## 8. 部署与调度

### 8.1 K8s Deployment 配置

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dep001-periodic-probe
  namespace: dshb-preprod
  labels:
    app: dep001-probe
    version: v1.0
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dep001-probe
  template:
    metadata:
      labels:
        app: dep001-probe
    spec:
      containers:
      - name: probe
        image: dshb/dep001-probe:v1.0
        command: ["python3", "dep001_periodic_probe.py"]
        args:
          - "--interval=60"
          - "--dep-url=https://dep-001.preprod.svc:8443"
          - "--gate-url=https://gate.svc:9090"
          - "--sample-count=10"
          - "--dry-run"
        env:
        - name: DEPENDENCY_ID
          value: "DEP-001"
        - name: SIMULATION_MODE
          value: "true"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        volumeMounts:
        - name: probe-logs
          mountPath: /app/probe_logs
        - name: probe-config
          mountPath: /app/config
      volumes:
      - name: probe-logs
        emptyDir: {}
      - name: probe-config
        configMap:
          name: dep001-probe-config
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        readOnlyRootFilesystem: true
```

### 8.2 CronJob 配置（替代方案）

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dep001-periodic-probe
  namespace: dshb-preprod
spec:
  schedule: "*/1 * * * *"  # 每 1 分钟
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: probe
            image: dshb/dep001-probe:v1.0
            args: ["--duration=60", "--dry-run"]
          restartPolicy: OnFailure
```

### 8.3 systemd Timer 配置（裸金属）

```ini
# /etc/systemd/system/dep001-probe.service
[Unit]
Description=DEP-001 Periodic Probe
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/dshb/dep001_periodic_probe.py --duration=55 --dry-run
User=probe
WorkingDirectory=/opt/dshb
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/dep001-probe.timer
[Unit]
Description=Run DEP-001 Probe Every Minute

[Timer]
OnCalendar=*:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 8.4 部署检查清单

| # | 检查项 | 预期 |
|---|--------|------|
| 1 | 镜像构建成功 | `dshb/dep001-probe:v1.0` |
| 2 | ConfigMap 配置正确 | probe-interval=60 |
| 3 | Secret 挂载正确 | mTLS 证书/密钥 |
| 4 | Service 发现配置 | dep-001.preprod.svc:8443 |
| 5 | Gate 端点可达 | gate.svc:9090 |
| 6 | 日志卷挂载 | probe_logs/ 可写 |
| 7 | 资源限制合理 | 100m CPU / 128Mi Mem |
| 8 | 安全上下文 | non-root, read-only FS |
| 9 | CronJob 调度正确 | 每 1 分钟触发 |
| 10 | 自检通过 | `--self-test` 37/37 PASS |

---

## 9. 接口契约

### 9.1 巡检结果 JSON Schema

```json
{
  "probe_version": "1.0",
  "work_order": "DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE",
  "task_id": "T3.2",
  "timestamp": "2026-10-17T10:00:00",
  "summary": {
    "total_cycles": 10,
    "total_queries": 100,
    "total_success": 99,
    "total_errors": 1,
    "avg_success_rate_pct": 99.0
  },
  "cycles": [
    {
      "cycle_id": 1,
      "timestamp": "2026-10-17T10:00:00",
      "health_status": "UP",
      "health_latency_ms": 4.5,
      "total_queries": 10,
      "success_queries": 10,
      "error_queries": 0,
      "success_rate_pct": 100.0,
      "p50_latency_ms": 15.2,
      "p95_latency_ms": 18.5,
      "p99_latency_ms": 22.1,
      "error_codes": {},
      "circuit_breaker_state": "CLOSED",
      "circuit_breaker_failures": 0,
      "consecutive_failures": 0,
      "alert_level": "NONE",
      "alert_message": "",
      "overall_pass": true,
      "sample_count": 10,
      "metrics_snapshot": {}
    }
  ]
}
```

### 9.2 CLI 参数契约

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--interval` | int | 60 | 巡检周期（秒） |
| `--duration` | int | 0 | 最大运行时长（0=永久） |
| `--dep-url` | str | `https://dep-001.preprod.svc:8443` | DEP-001 URL |
| `--gate-url` | str | `https://gate.svc:9090` | Gate URL |
| `--sample-count` | int | 10 | 每周期抽样数 |
| `--dry-run` | bool | false | 不回写 Gate |
| `--verbose` | bool | false | 详细日志 |
| `--json` | bool | false | JSON 输出 |
| `--self-test` | bool | false | 运行自检 |
| `--config` | str | None | 配置文件路径 |

### 9.3 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 正常退出（含 self-test 全 PASS） |
| 1 | self-test 存在 FAIL |
| 2 | 配置错误 |
| 3 | 运行时异常 |

---

## 10. 跨团队集成

### 10.1 HERMES 集成

| 集成点 | 说明 |
|--------|------|
| evidence_auditor_v2_plus | 巡检结果作为 L1 证据包输入 |
| audit_file 格式 | `probe_result_latest.json` 兼容审计器 |
| 告警载荷 | V3 载荷契约 23 字段对齐 |

### 10.2 DSHE 集成

| 集成点 | 说明 |
|--------|------|
| L2 面板 | `dep_probe_*` 指标直接消费 |
| 告警适配器 V3 | 巡检告警通过适配器 V3 转发 |
| 灰度降级 | 巡检异常触发面板降级 |

### 10.3 Gate V5 集成

| 集成点 | 说明 |
|--------|------|
| gate_pre_check_auto_v5.py | 巡检结果注入 Gate 检查流程 |
| 状态回写 | `POST /api/v1/dep/probe-result` |
| 告警联动 | 巡检 P0 → Gate NOT_READY |

### 10.4 契约对齐验证矩阵

| 契约项 | HERMES | DSHE | Gate V5 | 状态 |
|--------|--------|------|---------|------|
| `dep_id` | ✅ | ✅ | ✅ | 对齐 |
| `probe_timestamp` | ✅ | ✅ | ✅ | 对齐 |
| `overall_pass` | ✅ | ✅ | ✅ | 对齐 |
| `alert_level` | ✅ | ✅ | ✅ | 对齐 |
| `p95_latency_ms` | ✅ | ✅ | ✅ | 对齐 |
| `circuit_breaker_state` | ✅ | ✅ | ✅ | 对齐 |
| `success_rate_pct` | ✅ | ✅ | ✅ | 对齐 |

---

## 11. 自检与测试

### 11.1 自检套件

`--self-test` 模式运行 37 项测试，覆盖：

| 测试组 | 数量 | 覆盖范围 |
|--------|------|---------|
| T1: 配置完整性 | 10 | 配置默认值、必填项 |
| T2: ProbeResult 模型 | 12 | 查询统计、延迟百分位、告警判定 |
| T3: ProbeEngine | 7 | 引擎初始化、单周期、回写 |
| T4: 告警分级 | 9 | P0/P1/P2/NONE 全部场景 |
| T5: 边界情况 | 5 | 空结果、单查询、序列化 |
| T6: 版本元数据 | 3 | VERSION、WORK_ORDER、TASK_ID |
| T7: 配置边界 | 3 | 阈值边界值 |

### 11.2 预期自检结果

```
Self-Test Results: 37 PASS, 0 FAIL, 37 total
```

### 11.3 预发环境测试计划

| 测试项 | 方法 | 预期 |
|--------|------|------|
| 单周期运行 | `--duration=0` 运行 1 周期 | 10 查询全部 PASS |
| 多周期运行 | `--duration=300` 运行 5 分钟 | 5 周期全部 PASS |
| 长时运行 | `--duration=3600` 运行 1 小时 | 60 周期，成功率 > 99% |
| 异常场景 | 配置错误 DEP URL | 优雅降级，不崩溃 |
| 熔断模拟 | CB 状态为 OPEN | P0 告警触发 |
| 回写验证 | `--dry-run=false` | Gate 收到回写请求 |

---

## 12. 运行参数参考

### 12.1 预发环境推荐配置

```bash
python3 dep001_periodic_probe.py \
  --interval=60 \
  --dep-url="https://dep-001.preprod.svc:8443" \
  --gate-url="https://gate.svc:9090" \
  --sample-count=10 \
  --dry-run \
  --verbose
```

### 12.2 生产环境推荐配置

```bash
python3 dep001_periodic_probe.py \
  --interval=30 \
  --dep-url="https://dep-001.prod.svc:8443" \
  --gate-url="https://gate.svc:9090" \
  --sample-count=20 \
  --config=/etc/dshb/probe-prod-config.json
```

### 12.3 快速验证

```bash
# 自检
python3 dep001_periodic_probe.py --self-test

# 单周期 dry-run
python3 dep001_periodic_probe.py --dry-run --verbose

# 5 分钟短跑
python3 dep001_periodic_probe.py --duration=300 --interval=30 --dry-run
```

---

## 附录

### A. 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| V1.0 | 2026-10-17 | 初版发布，DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE / T3.2 |

### B. 约束合规

| 约束 | 状态 |
|------|------|
| NO_OVERWRITE=TRUE | ✅ 仅新增 dep001_periodic_probe.py |
| NO_MODIFY_V85=TRUE | ✅ V85 业务代码未修改 |
| BRANCH_LOCKED=TRUE | ✅ 提交至 feature/v85-chart-template |
| NO_ZHIJI_API_CALL=FALSE | ✅ 仅预发环境验证 |

---

*文档结束*
