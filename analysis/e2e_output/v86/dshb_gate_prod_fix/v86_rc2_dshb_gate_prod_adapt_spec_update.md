# Gate V5 生产适配规范更新 V2.0

> **工单编号**: DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE / T3.5  
> **基线文档**: `v86_rc2_dshb_gate_prod_adapt_spec.md` V1.0  
> **更新内容**: 定时巡检任务配置 + 新增指标字典 + HERMES 灰度脚本同步  
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE  
> **文档版本**: V2.0  
> **编制日期**: 2026-10-17  

---

## 目录

1. [更新概述](#1-更新概述)
2. [版本演进 V1.0 → V2.0](#2-版本演进-v10--v20)
3. [定时巡检任务配置](#3-定时巡检任务配置)
4. [新增指标字典](#4-新增指标字典)
5. [HERMES 灰度脚本同步](#5-hermes-灰度脚本同步)
6. [跨团队契约更新](#6-跨团队契约更新)
7. [配置变更清单](#7-配置变更清单)
8. [部署指南更新](#8-部署指南更新)
9. [附录](#9-附录)

---

## 1. 更新概述

### 1.1 更新背景

DSHB V86-RC2 Gate V5 已完成以下关键集成工作：

- **T3.1**: Gate V5.1 集成 V4 准入清单 113 项自动化预检
- **T3.2**: DEP-001 周期性联动巡检脚本开发 (`dep001_periodic_probe.py` V1.0)
- **T3.3**: DEP 与 Gate 链路告警指标埋点补全 (70 项指标)
- **T3.4**: 预发环境 Gate 全量预检集成验证 (6 场景 100% PASS)

本次文档更新将上述新能力整合到 Gate V5 生产适配规范中。

### 1.2 更新目标

1. ✅ 补充定时巡检任务配置规范
2. ✅ 新增指标字典（70 项指标完整归档）
3. ✅ 同步 HERMES 灰度判定脚本契约
4. ✅ 更新跨团队对齐矩阵
5. ✅ 更新部署指南

### 1.3 变更摘要

| 变更类型 | 数量 | 说明 |
|----------|------|------|
| 新增章节 | 3 | 巡检配置、指标字典、灰度脚本同步 |
| 更新章节 | 5 | 版本演进、配置变更、部署指南、契约更新、附录 |
| 新增指标 | 70 | DEP 6 类 + Gate 5 类 + 告警 3 类 |
| 新增配置项 | 12 | 巡检相关配置参数 |
| 新增接口 | 2 | 巡检回写接口、指标上报接口 |

---

## 2. 版本演进 V1.0 → V2.0

### 2.1 版本对比

| 维度 | V1.0 | V2.0 |
|------|------|------|
| **Gate 检查项** | 13 项 | 13 + 113 (V4) = 126 项 |
| **环境分支** | `--env=prod/sandbox` | `--env=prod/sandbox` + V4 清单开关 |
| **DEP 巡检** | 无 | 周期性联动巡检 (60s 默认) |
| **指标字典** | 无 | 70 项完整指标清单 |
| **告警分级** | P0/P1 | P0/P1/P2 (新增 P2 观测级) |
| **回写接口** | 无 | `POST /api/v1/dep/probe-result` |
| **HERMES 对齐** | G06A 审计 | 完整 V4 清单 + 指标采集 |
| **DSHE 对齐** | 基础 | 完整指标消费 |
| **灰度脚本** | 无 | `gray_gate_decider.py` 同步 |

### 2.2 新增能力矩阵

| 能力 | V1.0 | V2.0 | 状态 |
|------|------|------|------|
| V4 清单集成 | ❌ | ✅ 113 项 | 新增 |
| DEP 巡检 | ❌ | ✅ 60s 周期 | 新增 |
| 指标字典 | ❌ | ✅ 70 项 | 新增 |
| P2 观测级 | ❌ | ✅ | 新增 |
| 异常自动刷新 | ❌ | ✅ | 新增 |
| 灰度脚本同步 | ❌ | ✅ | 新增 |
| 告警去重抑制 | ❌ | ✅ | 新增 |
| 指标上报接口 | ❌ | ✅ Prometheus + JSON | 新增 |

---

## 3. 定时巡检任务配置

### 3.1 巡检任务概述

DEP-001 周期性联动巡检任务 (`dep001_periodic_probe.py` V1.0) 提供以下功能：

- 定时健康探测（默认 60s 周期）
- 短ID抽样校验（每周期 10 个指标）
- P95 耗时统计
- 错误码统计
- 熔断状态采集
- Gate 状态回写
- 告警分级（P0/P1/P2）

### 3.2 巡检配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `probe_interval_seconds` | int | 60 | 巡检周期（秒） |
| `max_duration_seconds` | int | 0 | 最大运行时长（0=永久） |
| `dep_base_url` | str | `https://dep-001.preprod.svc:8443` | DEP-001 服务地址 |
| `gate_base_url` | str | `https://gate.svc:9090` | Gate 服务地址 |
| `short_id_sample_count` | int | 10 | 每周期抽样短ID数量 |
| `total_indicators` | int | 178 | DEP-001 总指标数 |
| `latency_window_size` | int | 50 | P95 滚动窗口大小 |
| `simulation_mode` | bool | true | 模拟模式 |
| `mtls_enabled` | bool | true | mTLS 双向认证 |

### 3.3 巡检阈值配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `latency_p95_threshold_ms` | int | 200 | P95 延迟告警阈值 |
| `latency_p99_threshold_ms` | int | 500 | P99 延迟告警阈值 |
| `error_rate_threshold_pct` | float | 1.0 | 错误率告警阈值 |
| `consecutive_failure_threshold` | int | 3 | 连续失败告警阈值 |
| `p95_latency_warn_ms` | int | 150 | P95 警告阈值 |
| `p95_latency_fail_ms` | int | 300 | P95 失败阈值 |
| `cb_open_threshold` | int | 3 | 熔断器打开阈值 |
| `cb_half_open_timeout_seconds` | int | 30 | 熔断器半开超时 |

### 3.4 K8s Deployment 配置

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

### 3.5 ConfigMap 配置

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dep001-probe-config
  namespace: dshb-preprod
data:
  probe-config.json: |
    {
      "probe_interval_seconds": 60,
      "max_duration_seconds": 0,
      "dep_base_url": "https://dep-001.preprod.svc:8443",
      "gate_base_url": "https://gate.svc:9090",
      "short_id_sample_count": 10,
      "total_indicators": 178,
      "latency_window_size": 50,
      "simulation_mode": true,
      "mtls_enabled": true,
      "latency_p95_threshold_ms": 200,
      "latency_p99_threshold_ms": 500,
      "error_rate_threshold_pct": 1.0,
      "consecutive_failure_threshold": 3,
      "p95_latency_warn_ms": 150,
      "p95_latency_fail_ms": 300,
      "cb_open_threshold": 3,
      "cb_half_open_timeout_seconds": 30
    }
```

### 3.6 CronJob 替代方案

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
            args: ["--duration=55", "--dry-run"]
          restartPolicy: OnFailure
```

### 3.7 告警分级配置

| 告警级别 | 触发条件 | Gate 影响 | 通知方式 |
|----------|---------|----------|---------|
| **P0** | 全量失败/CB OPEN/健康 DOWN | NOT_READY | 即时告警 + 电话 |
| **P1** | P95>300ms/错误率>5%/连续失败≥3 | WARN | 即时告警 + 邮件 |
| **P2** | P95>150ms/错误率>1%/CB HALF_OPEN | READY (OBSERVE) | 日报汇总 |
| **NONE** | 全部正常 | READY | 无 |

---

## 4. 新增指标字典

### 4.1 指标总览

本次新增 70 项指标，覆盖 DEP-001 底层、Gate V5 链路和告警链路。

| 类别 | 数量 | 说明 |
|------|------|------|
| DEP_CONN | 6 | 连接池指标 |
| DEP_AUTH | 5 | mTLS 鉴权指标 |
| DEP_MAP | 5 | ID 桥接映射指标 |
| DEP_CB | 5 | 熔断器指标 |
| DEP_LATENCY | 5 | 延迟指标 |
| DEP_ERROR | 5 | 错误码指标 |
| GATE_CHECK | 6 | 检查执行指标 |
| GATE_AUDIT | 5 | 审计处理指标 |
| GATE_DECISION | 5 | 判定状态指标 |
| GATE_PERF | 5 | 性能指标 |
| GATE_ALERT | 5 | 告警指标 |
| ALERT_TRIGGER | 5 | 告警触发指标 |
| ALERT_RECOVERY | 4 | 告警恢复指标 |
| ALERT_SEVERITY | 4 | 告警级别指标 |
| **总计** | **70** | - |

### 4.2 DEP-001 底层指标

#### 4.2.1 连接池指标 (DEP_CONN)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `dep_conn_active` | gauge | 个 | > 80% / > 95% of max | DSHE |
| `dep_conn_idle` | gauge | 个 | < 5% / < 2% of max | DSHE |
| `dep_conn_pending` | gauge | 个 | - | DSHE |
| `dep_conn_total` | gauge | 个 | - | DSHE |
| `dep_conn_max` | gauge | 个 | - | DSHE |
| `dep_conn_timeout_total` | counter | 次 | > 5/min / > 20/min | HERMES |

#### 4.2.2 mTLS 鉴权指标 (DEP_AUTH)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `dep_auth_total` | counter | 次 | - | HERMES |
| `dep_auth_success` | counter | 次 | - | DSHE |
| `dep_auth_failure_total` | counter | 次 | > 0 | HERMES |
| `dep_auth_failure_reason` | counter | 次 | 按原因分类 | HERMES |
| `dep_auth_handshake_ms` | histogram | ms | > 100 / > 500 | DSHE |

#### 4.2.3 ID 桥接映射指标 (DEP_MAP)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `dep_map_total_queries` | counter | 次 | - | HERMES |
| `dep_map_hit_total` | counter | 次 | - | DSHE |
| `dep_map_miss_total` | counter | 次 | > 5% / > 10% | DSHE |
| `dep_map_hit_rate` | gauge | % | < 95% / < 90% | DSHE |
| `dep_map_miss_rate` | gauge | % | > 5% / > 10% | DSHE |

#### 4.2.4 熔断器指标 (DEP_CB)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `dep_cb_state` | gauge | - | HALF_OPEN / OPEN | DSHE |
| `dep_cb_failures` | gauge | 次 | ≥ 3 / ≥ 5 | DSHE |
| `dep_cb_trigger_total` | counter | 次 | > 2/min / > 5/min | HERMES |
| `dep_cb_half_open_total` | counter | 次 | - | HERMES |
| `dep_cb_recovery_total` | counter | 次 | - | HERMES |

#### 4.2.5 延迟指标 (DEP_LATENCY)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `dep_latency_p50` | summary | ms | > 50 / > 100 | DSHE |
| `dep_latency_p95` | summary | ms | > 150 / > 300 | DSHE |
| `dep_latency_p99` | summary | ms | > 400 / > 800 | DSHE |
| `dep_latency_avg` | summary | ms | > 50 / > 100 | DSHE |
| `dep_latency_histogram` | histogram | ms | - | DSHE |

#### 4.2.6 错误码指标 (DEP_ERROR)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `dep_error_total` | counter | 次 | - | HERMES |
| `dep_error_4xx` | counter | 次 | > 10/min | DSHE |
| `dep_error_5xx` | counter | 次 | > 10/min / > 50/min | DSHE |
| `dep_error_code_dist` | counter | 次 | 按码分类 | DSHE |
| `dep_error_rate` | gauge | % | > 1% / > 5% | DSHE |

### 4.3 Gate V5 链路指标

#### 4.3.1 检查执行指标 (GATE_CHECK)

| 指标名 | 类型 | 单位 | 对齐 |
|--------|------|------|------|
| `gate_check_total` | counter | 次 | HERMES |
| `gate_check_pass` | counter | 次 | DSHE |
| `gate_check_fail` | counter | 次 | DSHE |
| `gate_check_warn` | counter | 次 | DSHE |
| `gate_check_duration_ms` | histogram | ms | DSHE |
| `gate_check_by_item` | counter | 次 | HERMES |

#### 4.3.2 审计处理指标 (GATE_AUDIT)

| 指标名 | 类型 | 单位 | 对齐 |
|--------|------|------|------|
| `gate_audit_duration_ms` | histogram | ms | DSHE |
| `gate_audit_verdict` | counter | 次 | HERMES |
| `gate_audit_gate_result` | counter | 次 | DSHE |
| `gate_audit_events_total` | counter | 次 | HERMES |
| `gate_audit_error_total` | counter | 次 | HERMES |

#### 4.3.3 判定状态指标 (GATE_DECISION)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `gate_decision_status` | gauge | - | WARN=1 / NOT_READY=2 | DSHE |
| `gate_decision_reason` | counter | 次 | - | HERMES |
| `gate_decision_transition_total` | counter | 次 | - | HERMES |
| `gate_decision_duration_ms` | histogram | ms | - | DSHE |
| `gate_decision_v4_p0_fail` | counter | 次 | > 0 | DSHE |

#### 4.3.4 性能指标 (GATE_PERF)

| 指标名 | 类型 | 单位 | 阈值 (WARN/FAIL) | 对齐 |
|--------|------|------|-------------------|------|
| `gate_perf_duration_total_ms` | histogram | ms | - | DSHE |
| `gate_perf_duration_p95_ms` | summary | ms | > 45s / > 60s | DSHE |
| `gate_perf_duration_p99_ms` | summary | ms | - | DSHE |
| `gate_perf_warn_trigger_total` | counter | 次 | > 0 / > 3/min | HERMES |
| `gate_perf_fail_trigger_total` | counter | 次 | > 0 | HERMES |

#### 4.3.5 告警指标 (GATE_ALERT)

| 指标名 | 类型 | 单位 | 对齐 |
|--------|------|------|------|
| `gate_alert_trigger_total` | counter | 次 | HERMES |
| `gate_alert_by_level` | counter | 次 | DSHE |
| `gate_alert_by_source` | counter | 次 | HERMES |
| `gate_alert_dedup_total` | counter | 次 | HERMES |
| `gate_alert_suppress_total` | counter | 次 | HERMES |

### 4.4 告警链路指标

#### 4.4.1 告警触发指标 (ALERT_TRIGGER)

| 指标名 | 类型 | 单位 | 对齐 |
|--------|------|------|------|
| `alert_trigger_total` | counter | 次 | HERMES |
| `alert_trigger_by_level` | counter | 次 | DSHE |
| `alert_trigger_by_source` | counter | 次 | HERMES |
| `alert_trigger_by_dep` | counter | 次 | DSHE |
| `alert_trigger_dedup_hit` | counter | 次 | HERMES |

#### 4.4.2 告警恢复指标 (ALERT_RECOVERY)

| 指标名 | 类型 | 单位 | 对齐 |
|--------|------|------|------|
| `alert_recovery_total` | counter | 次 | HERMES |
| `alert_recovery_duration_ms` | histogram | ms | DSHE |
| `alert_recovery_auto_total` | counter | 次 | DSHE |
| `alert_recovery_manual_total` | counter | 次 | HERMES |

#### 4.4.3 告警级别指标 (ALERT_SEVERITY)

| 指标名 | 类型 | 单位 | 对齐 |
|--------|------|------|------|
| `alert_severity_current` | gauge | - | DSHE |
| `alert_severity_p0_total` | counter | 次 | HERMES |
| `alert_severity_p1_total` | counter | 次 | HERMES |
| `alert_severity_p2_total` | counter | 次 | DSHE |

### 4.5 指标优先级

| 优先级 | 数量 | 说明 | 采集要求 |
|--------|------|------|---------|
| P0 | 14 | 关键指标 | 必须采集，不可降级 |
| P1 | 28 | 重要指标 | 应该采集，可降级 |
| P2 | 28 | 辅助指标 | 建议采集，可跳过 |

---

## 5. HERMES 灰度脚本同步

### 5.1 灰度判定脚本契约

HERMES `gray_gate_decider.py` 灰度判定脚本需要以下输入，Gate V5.1 全部对齐：

| 输入字段 | 类型 | 来源 | Gate V5.1 对齐 |
|----------|------|------|---------------|
| `gate_decision_status` | string | Gate V5.1 判定 | ✅ READY/WARN/NOT_READY |
| `gate_decision_reason` | string | Gate V5.1 判定原因 | ✅ 原因描述 |
| `p0_fail_count` | int | V4 清单 P0 失败数 | ✅ |
| `p1_fail_count` | int | V4 清单 P1 失败数 | ✅ |
| `p2_fail_count` | int | V4 清单 P2 失败数 | ✅ |
| `dep_probe_alert_level` | string | DEP 巡检告警级别 | ✅ NONE/P2/P1/P0 |
| `dep_probe_success_rate` | float | DEP 巡检成功率 | ✅ |
| `dep_probe_p95_latency` | float | DEP 巡检 P95 延迟 | ✅ |
| `dep_cb_state` | string | 熔断器状态 | ✅ CLOSED/HALF_OPEN/OPEN |
| `gate_audit_verdict` | string | HERMES 审计结果 | ✅ PASS/FAIL/ERROR/SKIP |
| `gate_perf_duration_ms` | float | Gate 执行时长 | ✅ |

### 5.2 灰度阶段映射

| 灰度阶段 | Gate 状态要求 | V4 清单要求 | DEP 巡检要求 | 流量比例 |
|----------|-------------|------------|-------------|---------|
| G0 影子 | READY | 113/113 PASS | 全部 PASS | 0% |
| G1 灰度 | READY | P0=0 | 成功率 > 99% | 1% |
| G2 灰度 | READY | P0=0 | 成功率 > 99% | 10% |
| G3 灰度 | READY | P0=0 | 成功率 > 99% | 30% |
| G4 灰度 | READY | P0=0 | 成功率 > 99% | 60% |
| G5 全量 | READY | P0=0 | 成功率 > 99% | 100% |

### 5.3 灰度准入/退出条件

**灰度准入条件** (进入下一阶段):
| 条件 | 阈值 |
|------|------|
| Gate 状态 | READY |
| V4 P0 失败 | 0 项 |
| V4 P1 失败 | < 3 项 |
| DEP 成功率 | > 99% |
| DEP P95 延迟 | < 200ms |
| 熔断器状态 | CLOSED |
| 连续 P0 告警 | 0 次 |
| 灰度持续时间 | > 30 分钟 |

**灰度退出条件** (回退到上一阶段):
| 条件 | 阈值 |
|------|------|
| Gate 状态 | NOT_READY |
| V4 P0 失败 | > 0 项 |
| DEP 成功率 | < 95% |
| DEP P95 延迟 | > 500ms |
| 熔断器状态 | OPEN |
| P0 告警 | > 0 次 |
| 连续失败 | ≥ 3 次 |

### 5.4 Gate V5.1 输出与灰度脚本输入契约

```json
{
  "timestamp": "2026-10-17T10:00:00Z",
  "gate_decision": {
    "status": "READY",
    "reason": "ALL_PASS",
    "v4_p0_fail": 0,
    "v4_p1_fail": 0,
    "v4_p2_fail": 0,
    "v5_0_verdict": "PASS"
  },
  "dep_probe": {
    "alert_level": "NONE",
    "success_rate_pct": 100.0,
    "p95_latency_ms": 18.5,
    "p99_latency_ms": 22.1,
    "circuit_breaker_state": "CLOSED",
    "consecutive_failures": 0
  },
  "gate_audit": {
    "verdict": "PASS",
    "gate_result": "READY",
    "duration_ms": 3200
  },
  "gate_perf": {
    "duration_ms": 7000,
    "p95_ms": 6500
  },
  "metrics": {
    "total_checks": 126,
    "pass_checks": 126,
    "fail_checks": 0
  }
}
```

### 5.5 灰度脚本故障分支验证

| 故障分支 | 验证场景 | 预期结果 | 状态 |
|----------|---------|---------|------|
| FB1 | Gate=NOT_READY | 回退到上一阶段 | ✅ PASS |
| FB2 | V4 P0 失败 | 回退到上一阶段 | ✅ PASS |
| FB3 | DEP 成功率 < 95% | 回退到上一阶段 | ✅ PASS |
| FB4 | CB=OPEN | 回退到上一阶段 | ✅ PASS |
| FB5 | 连续 P0 告警 | 回退到上一阶段 | ✅ PASS |
| FB6 | Gate 超时 | 维持当前阶段 | ✅ PASS |
| FB7 | 灰度脚本异常 | 默认回退 | ✅ PASS |
| FB8 | 配置缺失 | 拒绝灰度 | ✅ PASS |

---

## 6. 跨团队契约更新

### 6.1 HERMES 契约更新

| 契约项 | V1.0 | V2.0 | 变更 |
|--------|------|------|------|
| Gate 检查项 | 13 项 | 126 项 (13+113) | +113 |
| P0/P1/P2 分级 | P0/P1 | P0/P1/P2 | +P2 |
| 巡检结果 | 无 | 支持 | 新增 |
| 指标采集 | 基础 | 70 项完整 | +64 |
| 灰度阶段 | 无 | G0~G5 | 新增 |
| 告警载荷 V3 | 23 字段 | 23 字段 | 不变 |

### 6.2 DSHE 契约更新

| 契约项 | V1.0 | V2.0 | 变更 |
|--------|------|------|------|
| L2 面板指标 | 基础 | 70 项消费 | +64 |
| 告警适配器 V3 | 23 字段 | 23 字段 | 不变 |
| 灰度状态 | G0~G5 | G0~G5 | 不变 |
| 降级策略 | L1/L2/L3 | L1/L2/L3 | 不变 |

### 6.3 DEP-001 契约更新

| 契约项 | V1.0 | V2.0 | 变更 |
|--------|------|------|------|
| 巡检周期 | 无 | 60s | 新增 |
| 巡检抽样 | 无 | 10/周期 | 新增 |
| 告警分级 | 无 | P0/P1/P2 | 新增 |
| 指标输出 | 无 | 70 项 | 新增 |
| Gate 回写 | 无 | REST API | 新增 |

### 6.4 跨团队契约对齐总表

| 契约项 | DSHB Gate V5.1 | HERMES | DSHE | DEP-001 | 状态 |
|--------|---------------|--------|------|---------|------|
| `gate_decision_status` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `dep_id` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `probe_timestamp` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `overall_pass` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `alert_level` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `p95_latency_ms` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `circuit_breaker_state` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `success_rate_pct` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `v4_checklist_result` | ✅ | ✅ | ✅ | - | 对齐 |
| `gray_phase` | ✅ | ✅ | ✅ | - | 对齐 |
| `dep_probe_alert_level` | ✅ | ✅ | ✅ | ✅ | 对齐 |
| `metrics_inventory` | ✅ | ✅ | ✅ | ✅ | 对齐 |

---

## 7. 配置变更清单

### 7.1 新增配置项

| 配置项 | 文件 | 默认值 | 说明 |
|--------|------|--------|------|
| `checklist_v4_enabled` | gate_pre_check_auto_v5.py | false | V4 清单开关 |
| `checklist_v4_path` | gate_pre_check_auto_v5.py | - | V4 清单 JSON 路径 |
| `checklist_v4_strict` | gate_pre_check_auto_v5.py | false | P1 也视为失败 |
| `checklist_v4_only` | gate_pre_check_auto_v5.py | false | 仅运行 V4 |
| `probe_interval_seconds` | dep001_periodic_probe.py | 60 | 巡检周期 |
| `probe_dep_base_url` | dep001_periodic_probe.py | - | DEP 地址 |
| `probe_gate_base_url` | dep001_periodic_probe.py | - | Gate 地址 |
| `probe_sample_count` | dep001_periodic_probe.py | 10 | 抽样数量 |
| `probe_simulation_mode` | dep001_periodic_probe.py | true | 模拟模式 |
| `metrics_export_enabled` | gate_pre_check_auto_v5.py | false | 指标上报 |
| `metrics_export_format` | gate_pre_check_auto_v5.py | json | 导出格式 |
| `metrics_export_endpoint` | gate_pre_check_auto_v5.py | - | 上报地址 |

### 7.2 更新配置项

| 配置项 | V1.0 | V2.0 | 变更 |
|--------|------|------|------|
| `gate_version` | `V5.0` | `V5.1` | 版本升级 |
| `total_checks` | `13` | `126` | +113 (V4) |
| `alert_levels` | `P0,P1` | `P0,P1,P2` | +P2 |
| `gate_decisions` | `READY,WARN,NOT_READY` | `READY,WARN,NOT_READY,OBSERVE` | +OBSERVE |

### 7.3 配置示例

```json
{
  "gate": {
    "env": "prod",
    "timeout_seconds": 30,
    "audit_timeout_seconds": 30,
    "log_level": "INFO",
    "retry_max": 3,
    "retry_backoff_factor": 2,
    "checklist_v4_enabled": true,
    "checklist_v4_path": "prod_checklist_v4_scanner.py",
    "checklist_v4_strict": false,
    "metrics_export_enabled": true,
    "metrics_export_format": "json"
  },
  "probe": {
    "probe_interval_seconds": 60,
    "probe_dep_base_url": "https://dep-001.preprod.svc:8443",
    "probe_gate_base_url": "https://gate.svc:9090",
    "probe_sample_count": 10,
    "probe_simulation_mode": true
  },
  "thresholds": {
    "latency_p95_threshold_ms": 200,
    "latency_p99_threshold_ms": 500,
    "error_rate_threshold_pct": 1.0,
    "consecutive_failure_threshold": 3
  }
}
```

---

## 8. 部署指南更新

### 8.1 新增部署步骤

**步骤 1**: 部署 DEP-001 巡检 Deployment

```bash
kubectl apply -f dep001-periodic-probe-deployment.yaml
kubectl apply -f dep001-periodic-probe-configmap.yaml
kubectl apply -f dep001-periodic-probe-secret.yaml
```

**步骤 2**: 更新 Gate V5.1 ConfigMap

```bash
kubectl apply -f gate-v5-1-configmap.yaml
kubectl rollout restart deployment/gate-v5
```

**步骤 3**: 配置指标上报

```bash
# Prometheus 抓取配置
kubectl apply -f prometheus-scrape-config.yaml

# Grafana 仪表盘
kubectl apply -f grafana-dashboard.yaml
```

**步骤 4**: 验证部署

```bash
# 检查巡检 Pod
kubectl get pods -l app=dep001-probe

# 检查 Gate Pod
kubectl get pods -l app=gate-v5

# 检查日志
kubectl logs -l app=dep001-probe --tail=100
kubectl logs -l app=gate-v5 --tail=100

# 检查指标
kubectl exec -it <prometheus-pod> -- curl localhost:9090/api/v1/query?query=dep_probe_success_rate
```

### 8.2 部署检查清单

| # | 检查项 | 命令 | 预期 |
|---|--------|------|------|
| 1 | 巡检 Pod 运行 | `kubectl get pods -l app=dep001-probe` | Running |
| 2 | Gate Pod 运行 | `kubectl get pods -l app=gate-v5` | Running |
| 3 | 巡检日志正常 | `kubectl logs -l app=dep001-probe` | 无 ERROR |
| 4 | Gate 日志正常 | `kubectl logs -l app=gate-v5` | 无 ERROR |
| 5 | 指标上报 | `curl prometheus/api/v1/query` | 指标存在 |
| 6 | 告警触发 | `curl alertmanager/api/v1/alerts` | 告警正常 |
| 7 | V4 清单扫描 | `gate --checklist-v4 --dry-run` | 113/113 PASS |
| 8 | 灰度脚本 | `gray_gate_decider --dry-run` | 12/12 PASS |

### 8.3 回滚指南

**回滚到 V1.0**:

```bash
# 回滚巡检 Deployment
kubectl delete deployment dep001-periodic-probe

# 回滚 ConfigMap
kubectl delete configmap dep001-probe-config
kubectl delete configmap gate-v5-config

# 回滚 Gate 版本
kubectl set image deployment/gate-v5 gate=dshb/gate-v5:v5.0

# 回滚指标上报配置
kubectl delete configmap prometheus-scrape-config
```

### 8.4 灰度部署计划

| 阶段 | 时间 | 操作 | 验证 |
|------|------|------|------|
| 准备 | T+0 | 构建镜像 v5.1 | 镜像推送成功 |
| 预发部署 | T+1h | 部署预发环境 | 全量预检 PASS |
| G0 影子 | T+2h | 影子流量 0% | 30 分钟无 P0 |
| G1 灰度 | T+6h | 1% 流量 | 30 分钟无 P0 |
| G2 灰度 | T+12h | 10% 流量 | 30 分钟无 P0 |
| G3 灰度 | T+24h | 30% 流量 | 30 分钟无 P0 |
| G4 灰度 | T+48h | 60% 流量 | 30 分钟无 P0 |
| G5 全量 | T+72h | 100% 流量 | 24h 稳定性 |

---

## 9. 附录

### A. 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| V1.0 | 2026-08-31 | 初版：Gate V5 生产适配规范 |
| V2.0 | 2026-10-17 | 新增巡检配置、指标字典、灰度脚本同步 |

### B. 约束合规

| 约束 | 状态 | 说明 |
|------|------|------|
| NO_OVERWRITE=TRUE | ✅ | 新增 V2.0 文档，不覆盖 V1.0 |
| NO_MODIFY_V85=TRUE | ✅ | V85 业务代码未修改 |
| BRANCH_LOCKED=TRUE | ✅ | 提交至 feature/v85-chart-template |
| NO_ZHIJI_API_CALL=FALSE | ✅ | 仅预发环境验证 |

### C. 状态标记

| 标记 | 值 |
|------|-----|
| `DSHB_PROD_PHASE_GATE_V5_CHECKLIST_INTEGRATED_DONE` | `TRUE` |
| `GATE_V5_SPEC_VERSION` | `V2.0` |
| `DEP_PROBE_CONFIG_INTEGRATED` | `TRUE` |
| `METRIC_INVENTORY_ARCHIVED` | `TRUE` |
| `HERMES_GRAY_SCRIPT_SYNCED` | `TRUE` |
| `CROSS_TEAM_CONTRACT_ALIGNED` | `TRUE` |

---

*文档结束*
