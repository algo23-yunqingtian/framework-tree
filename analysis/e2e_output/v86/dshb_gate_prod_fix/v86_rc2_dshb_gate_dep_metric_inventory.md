# DEP 与 Gate 链路告警指标埋点清单 V1.0

> **工单编号**: DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE / T3.3  
> **对齐目标**: HERMES 审计采集 + DSHE L2 面板消费  
> **覆盖范围**: DEP-001 底层 + Gate V5 链路  
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE  
> **文档版本**: V1.0  
> **编制日期**: 2026-10-17  

---

## 目录

1. [概述](#1-概述)
2. [指标分类体系](#2-指标分类体系)
3. [DEP-001 底层指标](#3-dep-001-底层指标)
4. [Gate V5 链路指标](#4-gate-v5-链路指标)
5. [告警指标](#5-告警指标)
6. [HERMES 审计对齐](#6-hermes-审计对齐)
7. [DSHE L2 面板对齐](#7-dshe-l2-面板对齐)
8. [指标输出格式](#8-指标输出格式)
9. [埋点实现](#9-埋点实现)
10. [指标清单总表](#10-指标清单总表)
11. [采集与消费矩阵](#11-采集与消费矩阵)
12. [附录](#12-附录)

---

## 1. 概述

### 1.1 背景

DSHB V86-RC2 进入 Gate V5 阶段。当前 DEP-001 底层服务和 Gate 链路存在以下指标缺失：

- **DEP-001 底层**: 连接池活跃/空闲连接数、mTLS 鉴权失败计数、ID 桥接映射命中率、熔断器触发次数未标准化输出
- **Gate 链路**: 判定状态指标、审计处理时长分布、检查项执行耗时分布未统一采集
- **告警链路**: 告警触发次数、告警级别分布、告警恢复时间未对齐 HERMES/DSHE 消费格式

### 1.2 目标

1. ✅ 补齐 DEP 底层缺失埋点：连接池、mTLS 鉴权、ID 映射命中率、熔断器
2. ✅ 补齐 Gate 链路缺失埋点：判定状态、检查执行耗时、审计处理时长
3. ✅ 指标输出格式对齐 HERMES 审计采集
4. ✅ 指标输出格式对齐 DSHE L2 面板消费
5. ✅ 完整指标清单归档，可追溯

### 1.3 设计原则

| 原则 | 说明 |
|------|------|
| **标准化命名** | 指标命名遵循 `{domain}_{component}_{metric}` 格式 |
| **类型明确** | 每个指标明确标注类型 (counter/gauge/histogram) |
| **单位统一** | 时间类统一毫秒，计数类无单位，比率类百分比 |
| **对齐消费** | 指标可直接被 HERMES 审计和 DSHE L2 面板消费 |
| **可追溯** | 每个指标关联数据源和采集方式 |

---

## 2. 指标分类体系

### 2.1 分类总览

```
DEP-001 + Gate 链路指标体系
│
├── DEP-001 底层指标 (6 类)
│   ├── DEP_CONN: 连接池指标 (6 项)
│   ├── DEP_AUTH: mTLS 鉴权指标 (5 项)
│   ├── DEP_MAP: ID 桥接映射指标 (5 项)
│   ├── DEP_CB: 熔断器指标 (5 项)
│   ├── DEP_LATENCY: 延迟指标 (5 项)
│   └── DEP_ERROR: 错误码指标 (5 项)
│
├── Gate V5 链路指标 (5 类)
│   ├── GATE_CHECK: 检查执行指标 (6 项)
│   ├── GATE_AUDIT: 审计处理指标 (5 项)
│   ├── GATE_DECISION: 判定状态指标 (5 项)
│   ├── GATE_PERF: 性能指标 (5 项)
│   └── GATE_ALERT: 告警指标 (5 项)
│
└── 告警链路指标 (3 类)
    ├── ALERT_TRIGGER: 告警触发指标 (5 项)
    ├── ALERT_RECOVERY: 告警恢复指标 (4 项)
    └── ALERT_SEVERITY: 告警级别指标 (4 项)
```

### 2.2 指标类型说明

| 类型 | 说明 | 示例 | 用途 |
|------|------|------|------|
| `counter` | 单调递增计数器 | `dep_auth_failure_total` | 事件计数 |
| `gauge` | 当前值 | `dep_conn_active` | 当前状态 |
| `histogram` | 分布统计 | `dep_latency_histogram` | 延迟分布 |
| `summary` | 预聚合统计 | `dep_latency_summary` | 百分位延迟 |

---

## 3. DEP-001 底层指标

### 3.1 连接池指标 (DEP_CONN)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `dep_conn_active` | gauge | 个 | DEP 连接池 | 实时采样 | DSHE L2 面板 |
| `dep_conn_idle` | gauge | 个 | DEP 连接池 | 实时采样 | DSHE L2 面板 |
| `dep_conn_pending` | gauge | 个 | DEP 连接池 | 实时采样 | DSHE L2 面板 |
| `dep_conn_total` | gauge | 个 | DEP 连接池 | 实时采样 | DSHE L2 面板 |
| `dep_conn_max` | gauge | 个 | DEP 连接池配置 | 配置读取 | DSHE L2 面板 |
| `dep_conn_timeout_total` | counter | 次 | DEP 连接池 | 事件计数 | HERMES 审计 |

**采集代码示例**:
```python
# DEP-001 连接池指标采集
def collect_dep_conn_metrics(pool):
    return {
        "dep_conn_active": pool.get_active_count(),
        "dep_conn_idle": pool.get_idle_count(),
        "dep_conn_pending": pool.get_pending_count(),
        "dep_conn_total": pool.get_total_count(),
        "dep_conn_max": pool.get_max_size(),
        "dep_conn_timeout_total": pool.get_timeout_count(),
    }
```

**阈值**:
| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| `dep_conn_active` | > 80% of max | > 95% of max |
| `dep_conn_idle` | < 5% of max | < 2% of max |
| `dep_conn_timeout_total` | > 5/min | > 20/min |

### 3.2 mTLS 鉴权指标 (DEP_AUTH)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `dep_auth_total` | counter | 次 | mTLS 握手 | 事件计数 | HERMES 审计 |
| `dep_auth_success` | counter | 次 | mTLS 握手 | 事件计数 | DSHE L2 面板 |
| `dep_auth_failure_total` | counter | 次 | mTLS 握手 | 事件计数 | HERMES 审计 |
| `dep_auth_failure_reason` | counter | 次 | mTLS 错误 | 标签分类 | HERMES 审计 |
| `dep_auth_handshake_ms` | histogram | ms | mTLS 握手 | 延迟统计 | DSHE L2 面板 |

**采集代码示例**:
```python
# DEP-001 mTLS 鉴权指标采集
def collect_dep_auth_metrics():
    return {
        "dep_auth_total": auth_handler.get_total_count(),
        "dep_auth_success": auth_handler.get_success_count(),
        "dep_auth_failure_total": auth_handler.get_failure_count(),
        "dep_auth_failure_reason": {
            "cert_expired": auth_handler.get_failure_by_reason("cert_expired"),
            "cert_invalid": auth_handler.get_failure_by_reason("cert_invalid"),
            "token_expired": auth_handler.get_failure_by_reason("token_expired"),
            "token_invalid": auth_handler.get_failure_by_reason("token_invalid"),
            "timeout": auth_handler.get_failure_by_reason("timeout"),
        },
    }
```

**失败原因标签**:
| 标签 | 含义 | 告警级别 |
|------|------|---------|
| `cert_expired` | 证书过期 | P0 |
| `cert_invalid` | 证书无效 | P0 |
| `token_expired` | Token 过期 | P1 |
| `token_invalid` | Token 无效 | P1 |
| `timeout` | 握手超时 | P2 |

### 3.3 ID 桥接映射指标 (DEP_MAP)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `dep_map_total_queries` | counter | 次 | ID 桥接层 | 事件计数 | HERMES 审计 |
| `dep_map_hit_total` | counter | 次 | ID 桥接层 | 事件计数 | DSHE L2 面板 |
| `dep_map_miss_total` | counter | 次 | ID 桥接层 | 事件计数 | DSHE L2 面板 |
| `dep_map_hit_rate` | gauge | % | 计算 | 实时计算 | DSHE L2 面板 |
| `dep_map_miss_rate` | gauge | % | 计算 | 实时计算 | DSHE L2 面板 |

**采集代码示例**:
```python
# DEP-001 ID 桥接映射指标采集
def collect_dep_map_metrics():
    total = map_cache.get_total_queries()
    hit = map_cache.get_hit_count()
    miss = map_cache.get_miss_count()
    hit_rate = round(hit / total * 100, 2) if total > 0 else 0
    miss_rate = round(miss / total * 100, 2) if total > 0 else 0
    return {
        "dep_map_total_queries": total,
        "dep_map_hit_total": hit,
        "dep_map_miss_total": miss,
        "dep_map_hit_rate": hit_rate,
        "dep_map_miss_rate": miss_rate,
    }
```

**阈值**:
| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| `dep_map_hit_rate` | < 95% | < 90% |
| `dep_map_miss_rate` | > 5% | > 10% |

### 3.4 熔断器指标 (DEP_CB)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `dep_cb_state` | gauge | - | 熔断器 | 实时采样 | DSHE L2 面板 |
| `dep_cb_failures` | gauge | 次 | 熔断器 | 实时采样 | DSHE L2 面板 |
| `dep_cb_trigger_total` | counter | 次 | 熔断器 | 事件计数 | HERMES 审计 |
| `dep_cb_half_open_total` | counter | 次 | 熔断器 | 事件计数 | HERMES 审计 |
| `dep_cb_recovery_total` | counter | 次 | 熔断器 | 事件计数 | HERMES 审计 |

**状态枚举**:
| 状态值 | 含义 | 映射 |
|--------|------|------|
| `CLOSED` | 正常 | 0 |
| `HALF_OPEN` | 恢复中 | 1 |
| `OPEN` | 熔断 | 2 |

**采集代码示例**:
```python
# DEP-001 熔断器指标采集
def collect_dep_cb_metrics(cb):
    return {
        "dep_cb_state": {"CLOSED": 0, "HALF_OPEN": 1, "OPEN": 2}.get(cb.state, -1),
        "dep_cb_failures": cb.current_failures,
        "dep_cb_trigger_total": cb.get_trigger_count(),
        "dep_cb_half_open_total": cb.get_half_open_count(),
        "dep_cb_recovery_total": cb.get_recovery_count(),
    }
```

**阈值**:
| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| `dep_cb_state` | HALF_OPEN | OPEN |
| `dep_cb_failures` | ≥ 3 | ≥ 5 |
| `dep_cb_trigger_total` | > 2/min | > 5/min |

### 3.5 延迟指标 (DEP_LATENCY)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `dep_latency_p50` | summary | ms | 请求处理 | 百分位计算 | DSHE L2 面板 |
| `dep_latency_p95` | summary | ms | 请求处理 | 百分位计算 | DSHE L2 面板 |
| `dep_latency_p99` | summary | ms | 请求处理 | 百分位计算 | DSHE L2 面板 |
| `dep_latency_avg` | summary | ms | 请求处理 | 平均计算 | DSHE L2 面板 |
| `dep_latency_histogram` | histogram | ms | 请求处理 | 分布统计 | DSHE L2 面板 |

**阈值**:
| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| `dep_latency_p95` | > 150ms | > 300ms |
| `dep_latency_p99` | > 400ms | > 800ms |
| `dep_latency_avg` | > 50ms | > 100ms |

### 3.6 错误码指标 (DEP_ERROR)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `dep_error_total` | counter | 次 | 请求处理 | 事件计数 | HERMES 审计 |
| `dep_error_4xx` | counter | 次 | 请求处理 | 事件计数 | DSHE L2 面板 |
| `dep_error_5xx` | counter | 次 | 请求处理 | 事件计数 | DSHE L2 面板 |
| `dep_error_code_dist` | counter | 次 | 请求处理 | 标签分类 | DSHE L2 面板 |
| `dep_error_rate` | gauge | % | 计算 | 实时计算 | DSHE L2 面板 |

**错误码分类**:
| 错误码 | 分类 | 标签 |
|--------|------|------|
| 401 | 鉴权失败 | `4xx` |
| 403 | 权限拒绝 | `4xx` |
| 404 | 资源不存在 | `4xx` |
| 429 | 限流 | `4xx` |
| 500 | 内部错误 | `5xx` |
| 502 | 网关错误 | `5xx` |
| 503 | 服务不可用 | `5xx` |
| 504 | 网关超时 | `5xx` |

**阈值**:
| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| `dep_error_rate` | > 1% | > 5% |
| `dep_error_5xx` | > 10/min | > 50/min |

---

## 4. Gate V5 链路指标

### 4.1 检查执行指标 (GATE_CHECK)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `gate_check_total` | counter | 次 | Gate 引擎 | 事件计数 | HERMES 审计 |
| `gate_check_pass` | counter | 次 | Gate 引擎 | 事件计数 | DSHE L2 面板 |
| `gate_check_fail` | counter | 次 | Gate 引擎 | 事件计数 | DSHE L2 面板 |
| `gate_check_warn` | counter | 次 | Gate 引擎 | 事件计数 | DSHE L2 面板 |
| `gate_check_duration_ms` | histogram | ms | Gate 引擎 | 延迟统计 | DSHE L2 面板 |
| `gate_check_by_item` | counter | 次 | Gate 引擎 | 标签分类 | HERMES 审计 |

**检查项标签**:
| 标签 | 含义 |
|------|------|
| `G01` | 交付物完整性 |
| `G02` | 约束合规 |
| `G03` | 文档口径 |
| `G04` | API 日志 |
| `G05` | 桥接表准确性 |
| `G06` | 风险台账 |
| `G06A` | HERMES 审计 |
| `G07` | 跨团队通知 |
| `G08` | 审计链路 |
| `G09` | 脚本审计 |
| `G10` | 真实取数 |
| `PERF-GUARD` | 性能守护 |
| `DS-06` | DEP 抖动检测 |
| `V4-B001`~`V4-T018` | V4 清单检查项 |

### 4.2 审计处理指标 (GATE_AUDIT)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `gate_audit_duration_ms` | histogram | ms | 审计器 | 延迟统计 | DSHE L2 面板 |
| `gate_audit_verdict` | counter | 次 | 审计器 | 标签分类 | HERMES 审计 |
| `gate_audit_gate_result` | counter | 次 | 审计器 | 标签分类 | DSHE L2 面板 |
| `gate_audit_events_total` | counter | 次 | 审计器 | 事件计数 | HERMES 审计 |
| `gate_audit_error_total` | counter | 次 | 审计器 | 事件计数 | HERMES 审计 |

**审计结果标签**:
| 标签 | 含义 |
|------|------|
| `PASS` | 审计通过 |
| `FAIL` | 审计失败 |
| `ERROR` | 审计异常 |
| `SKIP` | 审计跳过 |
| `BYPASS` | 紧急旁路 |

### 4.3 判定状态指标 (GATE_DECISION)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `gate_decision_status` | gauge | - | Gate 引擎 | 实时采样 | DSHE L2 面板 |
| `gate_decision_reason` | counter | 次 | Gate 引擎 | 标签分类 | HERMES 审计 |
| `gate_decision_transition_total` | counter | 次 | Gate 引擎 | 事件计数 | HERMES 审计 |
| `gate_decision_duration_ms` | histogram | ms | Gate 引擎 | 延迟统计 | DSHE L2 面板 |
| `gate_decision_v4_p0_fail` | counter | 次 | Gate 引擎 | 事件计数 | DSHE L2 面板 |

**判定状态映射**:
| 状态 | 数值 | 含义 |
|------|------|------|
| `READY` | 0 | 就绪 |
| `WARN` | 1 | 警告 |
| `NOT_READY` | 2 | 不可用 |
| `OBSERVE` | 3 | 观测中 |

### 4.4 性能指标 (GATE_PERF)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `gate_perf_duration_total_ms` | histogram | ms | Gate 引擎 | 延迟统计 | DSHE L2 面板 |
| `gate_perf_duration_p95_ms` | summary | ms | Gate 引擎 | 百分位计算 | DSHE L2 面板 |
| `gate_perf_duration_p99_ms` | summary | ms | Gate 引擎 | 百分位计算 | DSHE L2 面板 |
| `gate_perf_warn_trigger_total` | counter | 次 | PERF-GUARD | 事件计数 | HERMES 审计 |
| `gate_perf_fail_trigger_total` | counter | 次 | PERF-GUARD | 事件计数 | HERMES 审计 |

**阈值**:
| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| `gate_perf_duration_p95_ms` | > 45s | > 60s |
| `gate_perf_warn_trigger_total` | > 0 | > 3/min |
| `gate_perf_fail_trigger_total` | > 0 | > 0 |

### 4.5 告警指标 (GATE_ALERT)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `gate_alert_trigger_total` | counter | 次 | Gate 引擎 | 事件计数 | HERMES 审计 |
| `gate_alert_by_level` | counter | 次 | Gate 引擎 | 标签分类 | DSHE L2 面板 |
| `gate_alert_by_source` | counter | 次 | Gate 引擎 | 标签分类 | HERMES 审计 |
| `gate_alert_dedup_total` | counter | 次 | Gate 引擎 | 事件计数 | HERMES 审计 |
| `gate_alert_suppress_total` | counter | 次 | Gate 引擎 | 事件计数 | HERMES 审计 |

**告警级别标签**:
| 标签 | 含义 |
|------|------|
| `P0` | 严重 |
| `P1` | 高 |
| `P2` | 中 |
| `NONE` | 无告警 |

---

## 5. 告警指标

### 5.1 告警触发指标 (ALERT_TRIGGER)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `alert_trigger_total` | counter | 次 | 告警引擎 | 事件计数 | HERMES 审计 |
| `alert_trigger_by_level` | counter | 次 | 告警引擎 | 标签分类 | DSHE L2 面板 |
| `alert_trigger_by_source` | counter | 次 | 告警引擎 | 标签分类 | HERMES 审计 |
| `alert_trigger_by_dep` | counter | 次 | 告警引擎 | 标签分类 | DSHE L2 面板 |
| `alert_trigger_dedup_hit` | counter | 次 | 告警引擎 | 事件计数 | HERMES 审计 |

### 5.2 告警恢复指标 (ALERT_RECOVERY)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `alert_recovery_total` | counter | 次 | 告警引擎 | 事件计数 | HERMES 审计 |
| `alert_recovery_duration_ms` | histogram | ms | 告警引擎 | 延迟统计 | DSHE L2 面板 |
| `alert_recovery_auto_total` | counter | 次 | 告警引擎 | 事件计数 | DSHE L2 面板 |
| `alert_recovery_manual_total` | counter | 次 | 告警引擎 | 事件计数 | HERMES 审计 |

### 5.3 告警级别指标 (ALERT_SEVERITY)

| 指标名 | 类型 | 单位 | 数据源 | 采集方式 | 对齐目标 |
|--------|------|------|--------|---------|---------|
| `alert_severity_current` | gauge | - | 告警引擎 | 实时采样 | DSHE L2 面板 |
| `alert_severity_p0_total` | counter | 次 | 告警引擎 | 事件计数 | HERMES 审计 |
| `alert_severity_p1_total` | counter | 次 | 告警引擎 | 事件计数 | HERMES 审计 |
| `alert_severity_p2_total` | counter | 次 | 告警引擎 | 事件计数 | DSHE L2 面板 |

**告警级别映射**:
| 级别 | 数值 | 含义 |
|------|------|------|
| `NONE` | 0 | 无告警 |
| `P2` | 1 | 低度告警 |
| `P1` | 2 | 高度告警 |
| `P0` | 3 | 严重告警 |

---

## 6. HERMES 审计对齐

### 6.1 HERMES 审计字段映射

HERMES evidence_auditor_v2_plus 需要以下字段，本指标清单全部对齐：

| HERMES 字段 | 对应指标 | 数据源 | 状态 |
|-------------|---------|--------|------|
| `dep_id` | `dep_conn_*` 等 DEP 指标 | DEP-001 | ✅ 对齐 |
| `probe_timestamp` | 指标时间戳 | 采集时间 | ✅ 对齐 |
| `dep_probe_total_queries` | `dep_map_total_queries` | DEP 桥接层 | ✅ 对齐 |
| `dep_probe_success_queries` | `dep_auth_success` | DEP 鉴权层 | ✅ 对齐 |
| `dep_probe_success_rate` | `dep_map_hit_rate` | 计算 | ✅ 对齐 |
| `dep_probe_p95_latency` | `dep_latency_p95` | DEP 延迟 | ✅ 对齐 |
| `dep_probe_health_status` | `gate_decision_status` | Gate 判定 | ✅ 对齐 |
| `dep_probe_cb_state` | `dep_cb_state` | DEP 熔断器 | ✅ 对齐 |
| `dep_probe_consecutive_failures` | `dep_cb_failures` | DEP 熔断器 | ✅ 对齐 |
| `gate_decision_status` | `gate_decision_status` | Gate 判定 | ✅ 对齐 |
| `gate_audit_verdict` | `gate_audit_verdict` | Gate 审计 | ✅ 对齐 |
| `alert_trigger_total` | `alert_trigger_total` | 告警引擎 | ✅ 对齐 |

### 6.2 HERMES 审计输出格式

HERMES 审计器需要的 JSON 格式：
```json
{
  "dep_id": "DEP-001",
  "audit_timestamp": "2026-10-17T10:00:00Z",
  "metrics": {
    "dep_conn_active": 42,
    "dep_conn_idle": 18,
    "dep_auth_failure_total": 0,
    "dep_map_hit_rate": 98.5,
    "dep_cb_state": 0,
    "dep_latency_p95": 18.5,
    "gate_decision_status": 0,
    "gate_audit_verdict": "PASS",
    "alert_trigger_total": 0
  },
  "verdict": "PASS",
  "gate_result": "READY"
}
```

---

## 7. DSHE L2 面板对齐

### 7.1 DSHE L2 面板指标映射

DSHE L2 面板需要以下指标展示，本指标清单全部对齐：

| DSHE 面板 | 对应指标 | 数据源 | 展示形式 | 状态 |
|-----------|---------|--------|---------|------|
| DEP 健康状态 | `gate_decision_status` | Gate 判定 | 状态灯 | ✅ 对齐 |
| DEP 成功率 | `dep_map_hit_rate` | DEP 桥接层 | 折线图 | ✅ 对齐 |
| DEP P95 延迟 | `dep_latency_p95` | DEP 延迟 | 折线图 | ✅ 对齐 |
| DEP 熔断状态 | `dep_cb_state` | DEP 熔断器 | 状态灯 | ✅ 对齐 |
| DEP 连接池 | `dep_conn_active`/`dep_conn_idle` | DEP 连接池 | 堆叠图 | ✅ 对齐 |
| Gate 检查通过 | `gate_check_pass`/`gate_check_fail` | Gate 引擎 | 堆叠柱状图 | ✅ 对齐 |
| Gate 审计结果 | `gate_audit_verdict` | Gate 审计 | 饼图 | ✅ 对齐 |
| 告警级别 | `alert_severity_current` | 告警引擎 | 状态灯 | ✅ 对齐 |
| 告警触发数 | `alert_trigger_by_level` | 告警引擎 | 柱状图 | ✅ 对齐 |
| V4 清单结果 | `gate_decision_v4_p0_fail` | Gate V4 | 仪表盘 | ✅ 对齐 |

### 7.2 DSHE 告警适配器 V3 对齐

DSHE 告警适配器 V3 需要以下字段，本指标清单全部对齐：

| V3 字段 | 对应指标 | 状态 |
|---------|---------|------|
| `dep_id` | `dep_conn_active` 等 | ✅ 对齐 |
| `alert_id` | 指标 ID | ✅ 对齐 |
| `alert_level` | `alert_severity_current` | ✅ 对齐 |
| `alert_source` | 数据源 | ✅ 对齐 |
| `alert_timestamp` | 采集时间 | ✅ 对齐 |
| `dep_health_status` | `gate_decision_status` | ✅ 对齐 |
| `dep_latency_p95` | `dep_latency_p95` | ✅ 对齐 |
| `dep_error_rate` | `dep_error_rate` | ✅ 对齐 |
| `dep_cb_state` | `dep_cb_state` | ✅ 对齐 |

---

## 8. 指标输出格式

### 8.1 Prometheus 格式

```prometheus
# HELP dep_conn_active Active connections in DEP connection pool
# TYPE dep_conn_active gauge
dep_conn_active 42

# HELP dep_auth_failure_total Total mTLS authentication failures
# TYPE dep_auth_failure_total counter
dep_auth_failure_total{reason="cert_expired"} 0
dep_auth_failure_total{reason="token_expired"} 0

# HELP dep_map_hit_rate ID bridge mapping hit rate percentage
# TYPE dep_map_hit_rate gauge
dep_map_hit_rate 98.5

# HELP dep_cb_state Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)
# TYPE dep_cb_state gauge
dep_cb_state 0

# HELP dep_latency_p95 95th percentile latency in milliseconds
# TYPE dep_latency_p95 summary
dep_latency_p95{quantile="0.95"} 18.5

# HELP gate_decision_status Gate decision status (0=READY, 1=WARN, 2=NOT_READY)
# TYPE gate_decision_status gauge
gate_decision_status 0

# HELP gate_check_duration_ms Gate check execution duration histogram
# TYPE gate_check_duration_ms histogram
gate_check_duration_ms_bucket{le="1.0"} 5
gate_check_duration_ms_bucket{le="5.0"} 10
gate_check_duration_ms_bucket{le="30.0"} 12

# HELP alert_trigger_total Total alert triggers
# TYPE alert_trigger_total counter
alert_trigger_total{level="P0"} 0
alert_trigger_total{level="P1"} 0
alert_trigger_total{level="P2"} 0
```

### 8.2 JSON 输出格式

```json
{
  "timestamp": "2026-10-17T10:00:00Z",
  "dep_id": "DEP-001",
  "metrics": {
    "DEP_CONN": {
      "dep_conn_active": 42,
      "dep_conn_idle": 18,
      "dep_conn_pending": 0,
      "dep_conn_total": 60,
      "dep_conn_max": 100,
      "dep_conn_timeout_total": 0
    },
    "DEP_AUTH": {
      "dep_auth_total": 15000,
      "dep_auth_success": 14998,
      "dep_auth_failure_total": 2,
      "dep_auth_failure_reason": {
        "cert_expired": 0,
        "cert_invalid": 0,
        "token_expired": 1,
        "token_invalid": 0,
        "timeout": 1
      }
    },
    "DEP_MAP": {
      "dep_map_total_queries": 10000,
      "dep_map_hit_total": 9850,
      "dep_map_miss_total": 150,
      "dep_map_hit_rate": 98.5,
      "dep_map_miss_rate": 1.5
    },
    "DEP_CB": {
      "dep_cb_state": 0,
      "dep_cb_failures": 0,
      "dep_cb_trigger_total": 0,
      "dep_cb_half_open_total": 0,
      "dep_cb_recovery_total": 0
    },
    "DEP_LATENCY": {
      "dep_latency_p50": 12.3,
      "dep_latency_p95": 18.5,
      "dep_latency_p99": 32.1,
      "dep_latency_avg": 14.2
    },
    "DEP_ERROR": {
      "dep_error_total": 15,
      "dep_error_4xx": 5,
      "dep_error_5xx": 10,
      "dep_error_rate": 0.15
    },
    "GATE_CHECK": {
      "gate_check_total": 13,
      "gate_check_pass": 13,
      "gate_check_fail": 0,
      "gate_check_warn": 0
    },
    "GATE_AUDIT": {
      "gate_audit_duration_ms": 3.2,
      "gate_audit_verdict": "PASS",
      "gate_audit_gate_result": "READY"
    },
    "GATE_DECISION": {
      "gate_decision_status": 0,
      "gate_decision_reason": "ALL_PASS",
      "gate_decision_duration_ms": 7.0
    },
    "ALERT_TRIGGER": {
      "alert_trigger_total": 0
    }
  }
}
```

---

## 9. 埋点实现

### 9.1 指标采集器

```python
class DepMetricCollector:
    """DEP-001 指标采集器"""
    
    def __init__(self, dep_client, gate_engine):
        self.dep_client = dep_client
        self.gate_engine = gate_engine
        self.start_time = time.time()
        self.counters = {
            "dep_auth_total": 0,
            "dep_auth_success": 0,
            "dep_auth_failure_total": 0,
            "dep_map_total_queries": 0,
            "dep_map_hit_total": 0,
            "dep_map_miss_total": 0,
            "dep_error_total": 0,
            "dep_error_4xx": 0,
            "dep_error_5xx": 0,
            "dep_cb_trigger_total": 0,
            "dep_cb_half_open_total": 0,
            "dep_cb_recovery_total": 0,
            "gate_check_total": 0,
            "gate_check_pass": 0,
            "gate_check_fail": 0,
            "gate_check_warn": 0,
            "alert_trigger_total": 0,
        }
        self.latencies = []
    
    def collect_dep_metrics(self):
        """采集 DEP-001 底层指标"""
        return {
            "DEP_CONN": self._collect_conn_metrics(),
            "DEP_AUTH": self._collect_auth_metrics(),
            "DEP_MAP": self._collect_map_metrics(),
            "DEP_CB": self._collect_cb_metrics(),
            "DEP_LATENCY": self._collect_latency_metrics(),
            "DEP_ERROR": self._collect_error_metrics(),
        }
    
    def collect_gate_metrics(self):
        """采集 Gate V5 链路指标"""
        return {
            "GATE_CHECK": self._collect_check_metrics(),
            "GATE_AUDIT": self._collect_audit_metrics(),
            "GATE_DECISION": self._collect_decision_metrics(),
            "GATE_PERF": self._collect_perf_metrics(),
            "GATE_ALERT": self._collect_alert_metrics(),
        }
    
    def collect_all(self):
        """采集全部指标"""
        return {
            "timestamp": datetime.now().isoformat(),
            "dep_id": "DEP-001",
            "metrics": {
                **self.collect_dep_metrics(),
                **self.collect_gate_metrics(),
                "ALERT_TRIGGER": self._collect_alert_trigger_metrics(),
                "ALERT_RECOVERY": self._collect_alert_recovery_metrics(),
                "ALERT_SEVERITY": self._collect_alert_severity_metrics(),
            }
        }
```

### 9.2 指标上报接口

```python
class MetricExporter:
    """指标上报接口 — 对齐 HERMES 审计和 DSHE L2 面板"""
    
    def __init__(self, hermes_endpoint=None, dshe_endpoint=None):
        self.hermes_endpoint = hermes_endpoint
        self.dshe_endpoint = dshe_endpoint
    
    def export_to_hermes(self, metrics):
        """上报到 HERMES 审计"""
        payload = {
            "dep_id": metrics["dep_id"],
            "audit_timestamp": metrics["timestamp"],
            "metrics": metrics["metrics"],
        }
        # POST to HERMES evidence_auditor endpoint
        return self._post(self.hermes_endpoint, payload)
    
    def export_to_dshe(self, metrics):
        """上报到 DSHE L2 面板"""
        payload = {
            "dep_id": metrics["dep_id"],
            "metrics": metrics["metrics"],
        }
        # POST to DSHE panel ingestion endpoint
        return self._post(self.dshe_endpoint, payload)
    
    def export_to_prometheus(self, metrics):
        """输出 Prometheus 格式"""
        return self._format_prometheus(metrics["metrics"])
```

---

## 10. 指标清单总表

### 10.1 完整指标清单

| 序号 | 指标名 | 类型 | 单位 | 数据源 | 对齐目标 | 优先级 |
|------|--------|------|------|--------|---------|--------|
| 1 | `dep_conn_active` | gauge | 个 | DEP 连接池 | DSHE | P1 |
| 2 | `dep_conn_idle` | gauge | 个 | DEP 连接池 | DSHE | P1 |
| 3 | `dep_conn_pending` | gauge | 个 | DEP 连接池 | DSHE | P2 |
| 4 | `dep_conn_total` | gauge | 个 | DEP 连接池 | DSHE | P2 |
| 5 | `dep_conn_max` | gauge | 个 | DEP 配置 | DSHE | P2 |
| 6 | `dep_conn_timeout_total` | counter | 次 | DEP 连接池 | HERMES | P1 |
| 7 | `dep_auth_total` | counter | 次 | mTLS 握手 | HERMES | P1 |
| 8 | `dep_auth_success` | counter | 次 | mTLS 握手 | DSHE | P1 |
| 9 | `dep_auth_failure_total` | counter | 次 | mTLS 握手 | HERMES | P0 |
| 10 | `dep_auth_failure_reason` | counter | 次 | mTLS 错误 | HERMES | P0 |
| 11 | `dep_auth_handshake_ms` | histogram | ms | mTLS 握手 | DSHE | P2 |
| 12 | `dep_map_total_queries` | counter | 次 | ID 桥接层 | HERMES | P1 |
| 13 | `dep_map_hit_total` | counter | 次 | ID 桥接层 | DSHE | P1 |
| 14 | `dep_map_miss_total` | counter | 次 | ID 桥接层 | DSHE | P1 |
| 15 | `dep_map_hit_rate` | gauge | % | 计算 | DSHE | P0 |
| 16 | `dep_map_miss_rate` | gauge | % | 计算 | DSHE | P1 |
| 17 | `dep_cb_state` | gauge | - | 熔断器 | DSHE | P0 |
| 18 | `dep_cb_failures` | gauge | 次 | 熔断器 | DSHE | P1 |
| 19 | `dep_cb_trigger_total` | counter | 次 | 熔断器 | HERMES | P0 |
| 20 | `dep_cb_half_open_total` | counter | 次 | 熔断器 | HERMES | P1 |
| 21 | `dep_cb_recovery_total` | counter | 次 | 熔断器 | HERMES | P1 |
| 22 | `dep_latency_p50` | summary | ms | 请求处理 | DSHE | P1 |
| 23 | `dep_latency_p95` | summary | ms | 请求处理 | DSHE | P0 |
| 24 | `dep_latency_p99` | summary | ms | 请求处理 | DSHE | P0 |
| 25 | `dep_latency_avg` | summary | ms | 请求处理 | DSHE | P2 |
| 26 | `dep_latency_histogram` | histogram | ms | 请求处理 | DSHE | P2 |
| 27 | `dep_error_total` | counter | 次 | 请求处理 | HERMES | P1 |
| 28 | `dep_error_4xx` | counter | 次 | 请求处理 | DSHE | P1 |
| 29 | `dep_error_5xx` | counter | 次 | 请求处理 | DSHE | P0 |
| 30 | `dep_error_code_dist` | counter | 次 | 请求处理 | DSHE | P2 |
| 31 | `dep_error_rate` | gauge | % | 计算 | DSHE | P0 |
| 32 | `gate_check_total` | counter | 次 | Gate 引擎 | HERMES | P1 |
| 33 | `gate_check_pass` | counter | 次 | Gate 引擎 | DSHE | P1 |
| 34 | `gate_check_fail` | counter | 次 | Gate 引擎 | DSHE | P0 |
| 35 | `gate_check_warn` | counter | 次 | Gate 引擎 | DSHE | P1 |
| 36 | `gate_check_duration_ms` | histogram | ms | Gate 引擎 | DSHE | P2 |
| 37 | `gate_check_by_item` | counter | 次 | Gate 引擎 | HERMES | P2 |
| 38 | `gate_audit_duration_ms` | histogram | ms | 审计器 | DSHE | P1 |
| 39 | `gate_audit_verdict` | counter | 次 | 审计器 | HERMES | P1 |
| 40 | `gate_audit_gate_result` | counter | 次 | 审计器 | DSHE | P1 |
| 41 | `gate_audit_events_total` | counter | 次 | 审计器 | HERMES | P2 |
| 42 | `gate_audit_error_total` | counter | 次 | 审计器 | HERMES | P0 |
| 43 | `gate_decision_status` | gauge | - | Gate 引擎 | DSHE | P0 |
| 44 | `gate_decision_reason` | counter | 次 | Gate 引擎 | HERMES | P1 |
| 45 | `gate_decision_transition_total` | counter | 次 | Gate 引擎 | HERMES | P1 |
| 46 | `gate_decision_duration_ms` | histogram | ms | Gate 引擎 | DSHE | P2 |
| 47 | `gate_decision_v4_p0_fail` | counter | 次 | Gate V4 | DSHE | P0 |
| 48 | `gate_perf_duration_total_ms` | histogram | ms | Gate 引擎 | DSHE | P1 |
| 49 | `gate_perf_duration_p95_ms` | summary | ms | Gate 引擎 | DSHE | P0 |
| 50 | `gate_perf_duration_p99_ms` | summary | ms | Gate 引擎 | DSHE | P0 |
| 51 | `gate_perf_warn_trigger_total` | counter | 次 | PERF-GUARD | HERMES | P1 |
| 52 | `gate_perf_fail_trigger_total` | counter | 次 | PERF-GUARD | HERMES | P0 |
| 53 | `gate_alert_trigger_total` | counter | 次 | Gate 引擎 | HERMES | P1 |
| 54 | `gate_alert_by_level` | counter | 次 | Gate 引擎 | DSHE | P1 |
| 55 | `gate_alert_by_source` | counter | 次 | Gate 引擎 | HERMES | P2 |
| 56 | `gate_alert_dedup_total` | counter | 次 | Gate 引擎 | HERMES | P2 |
| 57 | `gate_alert_suppress_total` | counter | 次 | Gate 引擎 | HERMES | P2 |
| 58 | `alert_trigger_total` | counter | 次 | 告警引擎 | HERMES | P1 |
| 59 | `alert_trigger_by_level` | counter | 次 | 告警引擎 | DSHE | P1 |
| 60 | `alert_trigger_by_source` | counter | 次 | 告警引擎 | HERMES | P2 |
| 61 | `alert_trigger_by_dep` | counter | 次 | 告警引擎 | DSHE | P2 |
| 62 | `alert_trigger_dedup_hit` | counter | 次 | 告警引擎 | HERMES | P2 |
| 63 | `alert_recovery_total` | counter | 次 | 告警引擎 | HERMES | P1 |
| 64 | `alert_recovery_duration_ms` | histogram | ms | 告警引擎 | DSHE | P2 |
| 65 | `alert_recovery_auto_total` | counter | 次 | 告警引擎 | DSHE | P2 |
| 66 | `alert_recovery_manual_total` | counter | 次 | 告警引擎 | HERMES | P2 |
| 67 | `alert_severity_current` | gauge | - | 告警引擎 | DSHE | P0 |
| 68 | `alert_severity_p0_total` | counter | 次 | 告警引擎 | HERMES | P0 |
| 69 | `alert_severity_p1_total` | counter | 次 | 告警引擎 | HERMES | P1 |
| 70 | `alert_severity_p2_total` | counter | 次 | 告警引擎 | DSHE | P2 |

### 10.2 按优先级分类

| 优先级 | 数量 | 说明 |
|--------|------|------|
| P0 | 14 | 关键指标，必须采集 |
| P1 | 28 | 重要指标，应该采集 |
| P2 | 28 | 辅助指标，建议采集 |
| **总计** | **70** | - |

### 10.3 按对齐目标分类

| 对齐目标 | 数量 | 说明 |
|----------|------|------|
| HERMES 审计 | 33 | 证据审计需要 |
| DSHE L2 面板 | 42 | 面板展示需要 |
| 双目标 | 40 | 两者都需要 |
| **总计** | **70** | - |

---

## 11. 采集与消费矩阵

### 11.1 采集频率

| 指标类别 | 采集频率 | 延迟要求 | 说明 |
|----------|---------|---------|------|
| DEP_CONN | 实时 | < 1s | 连接池变化快 |
| DEP_AUTH | 实时 | < 1s | 每次握手 |
| DEP_MAP | 每 10s | < 5s | 映射查询统计 |
| DEP_CB | 实时 | < 1s | 状态变化快 |
| DEP_LATENCY | 每 10s | < 5s | 延迟统计 |
| DEP_ERROR | 实时 | < 1s | 错误计数 |
| GATE_CHECK | 每次检查 | < 2s | 检查完成后 |
| GATE_AUDIT | 每次审计 | < 2s | 审计完成后 |
| GATE_DECISION | 每次判定 | < 2s | 判定完成后 |
| GATE_PERF | 每次检查 | < 2s | 性能统计 |
| GATE_ALERT | 实时 | < 1s | 告警触发 |
| ALERT_* | 实时 | < 1s | 告警事件 |

### 11.2 消费路径

```
┌─────────────────────────────────────────────────────────────────┐
│                    指标消费路径                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐   │
│  │  指标采集器   │────►│  Prometheus  │────►│  Grafana/DSHE  │   │
│  │  Collector    │     │  Exporter    │     │  L2 Panel      │   │
│  └──────────────┘     └──────────────┘     └────────────────┘   │
│        │                                                          │
│        ▼                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐   │
│  │  指标采集器   │────►│  HERMES 审计  │────►│  L1 证据包     │   │
│  │  Collector    │     │  Auditor     │     │  Evidence      │   │
│  └──────────────┘     └──────────────┘     └────────────────┘   │
│        │                                                          │
│        ▼                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐   │
│  │  指标采集器   │────►│  JSON 输出   │────►│  Gate V5 引擎   │   │
│  │  Collector    │     │  文件        │     │  (回写判定)      │   │
│  └──────────────┘     └──────────────┘     └────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. 附录

### A. 指标命名规范

```
{domain}_{component}_{metric}_{suffix}

domain:     dep | gate | alert
component:  conn | auth | map | cb | latency | error | check | audit | decision | perf
metric:     active | idle | total | success | failure | hit | miss | rate | duration | state | trigger | recovery | severity
suffix:     (optional) — _total, _ms, _p50, _p95, _p99, _avg, _histogram, _current, _by_level, _by_source, _by_dep, _dedup, _suppress, _auto, _manual
```

### B. 约束合规

| 约束 | 状态 | 说明 |
|------|------|------|
| NO_OVERWRITE=TRUE | ✅ | 新增指标清单文档 |
| NO_MODIFY_V85=TRUE | ✅ | V85 业务代码未修改 |
| BRANCH_LOCKED=TRUE | ✅ | 提交至 feature/v85-chart-template |
| NO_ZHIJI_API_CALL=FALSE | ✅ | 仅预发环境验证 |

### C. 状态标记

| 标记 | 值 |
|------|-----|
| `DEP_GATE_METRIC_INVENTORY_VERSION` | `V1.0` |
| `TOTAL_METRICS` | `70` |
| `P0_METRICS` | `14` |
| `P1_METRICS` | `28` |
| `P2_METRICS` | `28` |
| `HERMES_ALIGNED` | `TRUE` |
| `DSHE_ALIGNED` | `TRUE` |

---

*文档结束*
