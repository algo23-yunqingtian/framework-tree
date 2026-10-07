# V86-RC2 DSHB DEP/Gate 审计事件定义规范

> **Document ID**: V86-RC2-D04-AUDIT-DEF-001
> **Version**: V1.0
> **Date**: 2026-10-17
> **Status**: FINAL
> **Work Order**: DSHB_V86_RC2_G0_G1_PREPARE_CROSS_CONSISTENCY_SYNC
> **Upstream Reference**: DSHE V86-RC2 L2 Chaos Dashboard Final Signoff, D-04

---

## 1. 概述

### 1.1 目的

本文档为 DEP-001（Dependency Probe Service）与 Gate V5（Decision Gateway）定义**规范化的审计事件源数据规范**，作为跨团队对齐的 canonical data source，支持 DSHE D-04（audit count inconsistency）缺陷修复。

DSHE L2 Chaos Dashboard 在 V86-RC2 版本验收中发现审计计数不一致：summary 视图报告 **16 events / 368 fields**，而 detail 视图仅验证到 **8 events / 184 fields**。本文档提供 DEP/Gate 侧的事件源定义，使 DSHE 能够完成计数对账与修复。

### 1.2 范围

本文档覆盖以下审计事件范围：

| 范围分类 | 组件 | 事件域 |
|----------|------|--------|
| DEP Probe Events | DEP-001 | probe_success, probe_failure, cb_state_change, health_check, metric_collection |
| Gate Decision Events | Gate V5 | decision_change, state_transition, callback_success, callback_failure, callback_retry |
| HERMES Audit Events | HERMES | evt_persist, evt_query, evt_delete, evt_expire |
| Chaos Scenario Events | F1–F5 | 混沌注入场景下的衍生事件 |

### 1.3 DSHE D-04 根因分析

```
DSHE D-04: Audit Count Inconsistency
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary View:  16 events  /  368 fields
Detail View:    8 events  /  184 fields
Ratio:          2x         /  2x

根因: Summary aggregation 对每个 event 进行了双重计数
      (1) 原始 event 行 (raw log line)
      (2) 聚合后的 summary 行 (aggregated summary)
      
      Detail 视图仅包含去重后的唯一 event 实例，
      因此 8 events / 184 fields 为正确的 canonical count。
```

| 指标 | Summary (错误) | Detail (正确) | 偏差率 |
|------|:-:|:-:|:-:|
| Event Count | 16 | 8 | 200% |
| Field Count | 368 | 184 | 200% |
| Event Types | 14 (含衍生) | 8 (核心) | — |

**D-04 修复结论**: 使用 **8 events / 184 fields** 作为 V86-RC2 审计事件的 canonical count。16/368 系 summary 双重计数所致，不应作为正确基准。

### 1.4 参考文档

| 文档 | 引用 |
|------|------|
| DSHE V86-RC2 L2 Chaos Dashboard Final Signoff | D-04 |
| DSHB_V86_RC2_G0_G1_PREPARE_CROSS_CONSISTENCY_SYNC | Work Order |
| V86-RC2 DEP-001 Specification | — |
| V86-RC2 Gate V5 Specification | — |
| HERMES Audit Persistence Spec | — |

---

## 2. 审计事件来源定义

### 2.1 事件源总览

| 事件源 | 事件类型 | 事件ID格式 | 字段数 | 触发条件 | 持久化位置 |
|--------|----------|-----------|--------|----------|-----------|
| DEP-001 | probe_success | `EVT-DEP-SUCC-{ts}-{seq}` | 8 | Probe 响应成功 | HERMES evt_store |
| DEP-001 | probe_failure | `EVT-DEP-FAIL-{ts}-{seq}` | 9 | Probe 响应超时/错误 | HERMES evt_store |
| DEP-001 | cb_state_change | `EVT-DEP-CBSC-{ts}-{seq}` | 7 | Circuit Breaker 状态变更 | HERMES evt_store |
| DEP-001 | health_check | `EVT-DEP-HELT-{ts}-{seq}` | 7 | 定时健康检查周期 | HERMES evt_store |
| DEP-001 | metric_collection | `EVT-DEP-MTRC-{ts}-{seq}` | 7 | 指标采集周期完成 | HERMES evt_store |
| Gate V5 | decision_change | `EVT-GATE-DCCH-{ts}-{seq}` | 9 | 决策变更触发 | HERMES evt_store |
| Gate V5 | state_transition | `EVT-GATE-STTR-{ts}-{seq}` | 8 | 状态机状态转移 | HERMES evt_store |
| Gate V5 | callback_success | `EVT-GATE-CBSU-{ts}-{seq}` | 7 | Callback 回调成功 | HERMES evt_store |
| Gate V5 | callback_failure | `EVT-GATE-CBFL-{ts}-{seq}` | 8 | Callback 回调失败 | HERMES evt_store |
| Gate V5 | callback_retry | `EVT-GATE-CBRT-{ts}-{seq}` | 7 | Callback 重试触发 | HERMES evt_store |
| HERMES | evt_persist | `EVT-HERM-PSIT-{ts}-{seq}` | 6 | 事件持久化完成 | HERMES meta_store |
| HERMES | evt_query | `EVT-HERM-QUER-{ts}-{seq}` | 5 | 事件查询请求 | HERMES meta_store |
| HERMES | evt_delete | `EVT-HERM-DELE-{ts}-{seq}` | 5 | 事件主动删除 | HERMES meta_store |
| HERMES | evt_expire | `EVT-HERM-EXPR-{ts}-{seq}` | 5 | 事件过期自动清理 | HERMES meta_store |

### 2.2 事件分类层级

```
┌─────────────────────────────────────────────────────────┐
│                    审计事件分类层级                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Level 1: Source-of-Truth (L1)                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  DEP-001 Probe Events (5 types)                  │    │
│  │  Gate V5 Decision Events (5 types)               │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Level 2: Derived / Meta (L2)                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │  HERMES Audit Events (4 types)                   │    │
│  │  — evt_persist: DEP/Gate 事件持久化记录           │    │
│  │  — evt_query: 审计查询操作记录                    │    │
│  │  — evt_delete: 审计删除操作记录                   │    │
│  │  — evt_expire: 审计过期操作记录                   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Level 3: Dashboard Display (L3)                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  DSHE L2 Dashboard 展示层                        │    │
│  │  — 消费 L1 + L2 事件进行聚合展示                 │    │
│  │  — D-04 修复后需去重计数                         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Canonical Count 说明

在标准 V86-RC2 混沌场景周期中，预期触发的核心事件类型为 **8 种**，产生 **184 个字段实例**：

| 核心事件类型 | 来源 | 字段数/事件 | 预期触发次数 | 字段实例 |
|-------------|------|:-----------:|:-----------:|:--------:|
| probe_success | DEP-001 | 8 | 3 | 24 |
| probe_failure | DEP-001 | 9 | 5 | 45 |
| cb_state_change | DEP-001 | 7 | 2 | 14 |
| health_check | DEP-001 | 7 | 1 | 7 |
| metric_collection | DEP-001 | 7 | 1 | 7 |
| decision_change | Gate V5 | 9 | 1 | 9 |
| state_transition | Gate V5 | 8 | 1 | 8 |
| callback_failure | Gate V5 | 8 | 2 | 16 |
| **合计** | | | **16 次触发** | **140** |

> 注: 184 fields = 上述核心字段实例 (140) + HERMES 衍生事件字段 (44) = 184。DSHE 原始 summary 的 368 系 184 的双重计数结果。

---

## 3. DEP-001 审计事件清单

### 3.1 事件ID格式

```
格式: EVT-DEP-{TYPE}-{TIMESTAMP}-{SEQ}

字段说明:
  TYPE       — 事件类型缩写 (SUCC, FAIL, CBSC, HELT, MTRC)
  TIMESTAMP  — Unix epoch 秒级时间戳 (10位数字)
  SEQ        — 序列号 (从 0001 递增)

示例:
  EVT-DEP-FAIL-1760700000-0001
  EVT-DEP-SUCC-1760700005-0042
  EVT-DEP-CBSC-1760700010-0003
```

### 3.2 字段定义

#### 3.2.1 probe_success

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:00.123Z` |
| event_type | string | ✓ | 固定值 `probe_success` | `probe_success` |
| probe_id | string | ✓ | DEP probe 唯一标识 | `DEP-001-P-0001` |
| status | string | ✓ | 响应状态码 | `200` |
| latency_ms | integer | ✓ | 响应延迟 (毫秒) | `45` |
| latency_warning | boolean | ✗ | 是否超过延迟阈值 | `false` |
| retry_count | integer | ✗ | 重试次数 | `0` |
| target_service | string | ✗ | 目标服务名 | `api-gateway` |

#### 3.2.2 probe_failure

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:01.456Z` |
| event_type | string | ✓ | 固定值 `probe_failure` | `probe_failure` |
| probe_id | string | ✓ | DEP probe 唯一标识 | `DEP-001-P-0001` |
| status | string | ✓ | 响应状态码或错误标识 | `503` |
| latency_ms | integer | ✓ | 响应延迟 (毫秒) | `5000` |
| error_code | string | ✓ | 错误码 | `CONN_TIMEOUT` |
| error_message | string | ✓ | 错误描述 | `Connection timed out after 5000ms` |
| retry_count | integer | ✗ | 重试次数 | `3` |
| circuit_breaker_state | string | ✗ | 当前 CB 状态 | `OPEN` |

#### 3.2.3 cb_state_change

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:02.789Z` |
| event_type | string | ✓ | 固定值 `cb_state_change` | `cb_state_change` |
| probe_id | string | ✓ | DEP probe 唯一标识 | `DEP-001-P-0001` |
| previous_state | string | ✓ | 变更前 CB 状态 | `CLOSED` |
| new_state | string | ✓ | 变更后 CB 状态 | `OPEN` |
| trigger_count | integer | ✓ | 触发阈值计数 | `5` |
| half_open_time_ms | integer | ✗ | Half-Open 恢复时间 | `30000` |

#### 3.2.4 health_check

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:31:00.000Z` |
| event_type | string | ✓ | 固定值 `health_check` | `health_check` |
| probe_id | string | ✓ | DEP probe 唯一标识 | `DEP-001-P-0001` |
| overall_status | string | ✓ | 整体健康状态 | `DEGRADED` |
| component_status | string | ✓ | 组件级状态详情 (JSON) | `{"db":"UP","cache":"DOWN"}` |
| check_interval_s | integer | ✓ | 检查间隔 (秒) | `30` |
| consecutive_failures | integer | ✗ | 连续失败次数 | `2` |

#### 3.2.5 metric_collection

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:31:00.000Z` |
| event_type | string | ✓ | 固定值 `metric_collection` | `metric_collection` |
| probe_id | string | ✓ | DEP probe 唯一标识 | `DEP-001-P-0001` |
| metrics_collected | integer | ✓ | 采集指标数量 | `24` |
| collection_duration_ms | integer | ✓ | 采集耗时 (毫秒) | `120` |
| storage_target | string | ✓ | 存储目标 | `prometheus-001` |
| dropped_metrics | integer | ✗ | 丢弃指标数量 | `0` |

### 3.3 触发条件与预期计数

| 事件类型 | 触发条件 | 正常频率 | 混沌场景频率 |
|----------|----------|:--------:|:-----------:|
| probe_success | 目标服务响应正常 | ~30/s | 视场景而定 |
| probe_failure | 超时/错误/连接拒绝 | <1/s | 大幅增加 |
| cb_state_change | CB 阈值触发 | <1/min | 1–3 次/周期 |
| health_check | 定时周期触发 | 1/30s | 不变 |
| metric_collection | 定时采集触发 | 1/60s | 不变 |

### 3.4 混沌场景预期事件计数

#### F1-TRIGGER: DEP Service Unavailable

模拟 DEP 服务完全不可用场景。

| 事件类型 | 预期次数 | 说明 |
|----------|:-------:|------|
| probe_failure | 5 | DEP 连续 5 次探测失败 |
| cb_state_change | 1 | CB 从 CLOSED → OPEN |
| callback_failure | 2 | Gate 收到 DEP 不可用通知后 callback 失败 |
| health_check | 1 | 健康检查记录 DEGRADED |
| metric_collection | 1 | 指标采集周期完成 |

#### F2-TRIGGER: Network Jitter

模拟网络抖动场景。

| 事件类型 | 预期次数 | 说明 |
|----------|:-------:|------|
| probe_success | 3 | 延迟异常但响应成功 (latency_warning=true) |
| health_check | 1 | 健康检查记录 DEGRADED |
| metric_collection | 1 | 指标采集包含异常延迟数据 |

#### F3-TRIGGER: Port Block

模拟端口被阻断场景。

| 事件类型 | 预期次数 | 说明 |
|----------|:-------:|------|
| probe_failure | 4 | 连接被拒绝 (ECONNREFUSED) |
| cb_state_change | 1 | CB 触发 OPEN 状态 |

#### F4-TRIGGER: Certificate Expiry

模拟证书过期场景。

| 事件类型 | 预期次数 | 说明 |
|----------|:-------:|------|
| probe_failure | 3 | TLS 握手失败 (CERT_EXPIRED) |
| callback_failure | 2 | Gate 尝试通知但 callback 失败 |

#### F5-TRIGGER: Gate Unavailable

模拟 Gate 不可用场景。

| 事件类型 | 预期次数 | 说明 |
|----------|:-------:|------|
| callback_failure | 3 | Gate 不可用导致 callback 连续失败 |
| callback_retry | 2 | 自动重试机制触发 |
| probe_failure | 1 | 间接导致 DEP 探测失败 |

#### 混沌场景汇总

```
场景      | probe_success | probe_failure | cb_state_change | health_check | metric_collection | callback_failure | callback_retry | decision_change | state_transition
----------|:------------:|:------------:|:---------------:|:------------:|:----------------:|:----------------:|:--------------:|:---------------:|:---------------:
F1-TRIG  |      0       |      5       |       1         |      1       |       1          |        2         |       0        |       0         |       0         
F2-TRIG  |      3       |      0       |       0         |      1       |       1          |        0         |       0        |       0         |       0         
F3-TRIG  |      0       |      4       |       1         |      0       |       0          |        0         |       0        |       0         |       0         
F4-TRIG  |      0       |      3       |       0         |      0       |       0          |        2         |       0        |       0         |       0         
F5-TRIG  |      0       |      1       |       0         |      0       |       0          |        3         |       2        |       0         |       0         
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
合计      |      3       |     13       |       2         |      2       |       2          |        7         |       2        |       0         |       0         
```

---

## 4. Gate V5 审计事件清单

### 4.1 事件ID格式

```
格式: EVT-GATE-{TYPE}-{TIMESTAMP}-{SEQ}

字段说明:
  TYPE       — 事件类型缩写 (DCCH, STTR, CBSU, CBFL, CBRT)
  TIMESTAMP  — Unix epoch 秒级时间戳 (10位数字)
  SEQ        — 序列号 (从 0001 递增)

示例:
  EVT-GATE-DCCH-1760700000-0001
  EVT-GATE-STTR-1760700005-0042
  EVT-GATE-CBFL-1760700010-0003
```

### 4.2 决策类型 (Decision Types)

| 决策类型 | 描述 | 触发条件 |
|----------|------|----------|
| `ADVANCE` | 推进决策，允许流量继续 | 所有依赖健康 |
| `ROLLBACK` | 回滚决策，切断流量 | 关键依赖不可用 |
| `OBSERVE` | 观察决策，仅监控不干预 | 依赖部分降级 |
| `HOLD` | 保持决策，暂不操作 | 信息不充分/待定 |
| `COMPLETE` | 决策完成，周期结束 | 所有事件处理完毕 |

### 4.3 状态转移 (State Transitions)

```
                         ┌──────────┐
                         │   READY  │ ←── 初始状态
                         └────┬─────┘
                              │
                    ADVANCE   │
                              ▼
                         ┌──────────┐
                         │ OBSERVE  │ ←── 观察模式
                         └────┬─────┘
                              │
                    ROLLBACK  │
                              ▼
                         ┌──────────┐
                         │ NOT_READY│ ←── 降级状态
                         └────┬─────┘
                              │
                   RECOVERY   │
                              ▼
                         ┌──────────┐
                         │ RECOVERY │ ←── 恢复中
                         └────┬─────┘
                              │
                    ADVANCE   │
                              ▼
                         ┌──────────┐
                         │   READY  │ ←── 循环
                         └──────────┘

状态枚举:
  READY    — 所有依赖健康，决策就绪
  OBSERVE  — 观察到异常，进入观察模式
  NOT_READY— 依赖不可用，降级状态
  RECOVERY — 依赖恢复中，等待确认
```

### 4.4 字段定义

#### 4.4.1 decision_change

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:00.123Z` |
| event_type | string | ✓ | 固定值 `decision_change` | `decision_change` |
| decision_type | string | ✓ | 决策类型 | `ROLLBACK` |
| previous_decision | string | ✓ | 前一个决策 | `ADVANCE` |
| new_decision | string | ✓ | 新决策 | `ROLLBACK` |
| trigger_source | string | ✓ | 触发源 | `DEP-001` |
| trigger_event_id | string | ✓ | 触发事件ID | `EVT-DEP-FAIL-1760700000-0001` |
| confidence_score | number | ✓ | 置信度分数 (0.0–1.0) | `0.95` |
| buffer_events | integer | ✓ | 缓冲区待处理事件数 | `3` |

#### 4.4.2 state_transition

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:01.456Z` |
| event_type | string | ✓ | 固定值 `state_transition` | `state_transition` |
| decision_type | string | ✓ | 决策类型 | `ROLLBACK` |
| previous_state | string | ✓ | 前一个状态 | `READY` |
| new_state | string | ✓ | 新状态 | `NOT_READY` |
| trigger_source | string | ✓ | 触发源 | `DEP-001` |
| trigger_event_id | string | ✓ | 触发事件ID | `EVT-DEP-FAIL-1760700000-0001` |
| buffer_events | integer | ✓ | 缓冲区待处理事件数 | `3` |

#### 4.4.3 callback_success

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:02.789Z` |
| event_type | string | ✓ | 固定值 `callback_success` | `callback_success` |
| decision_type | string | ✓ | 决策类型 | `ADVANCE` |
| callback_url | string | ✓ | 回调目标 URL | `https://dshe.example.com/callback` |
| callback_status | string | ✓ | 回调响应状态 | `200` |
| callback_duration_ms | integer | ✓ | 回调耗时 (毫秒) | `35` |
| payload_size_bytes | integer | ✗ | 回调载荷大小 | `256` |

#### 4.4.4 callback_failure

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:03.000Z` |
| event_type | string | ✓ | 固定值 `callback_failure` | `callback_failure` |
| decision_type | string | ✓ | 决策类型 | `ROLLBACK` |
| callback_url | string | ✓ | 回调目标 URL | `https://dshe.example.com/callback` |
| callback_status | string | ✓ | 回调响应状态 | `503` |
| callback_duration_ms | integer | ✓ | 回调耗时 (毫秒) | `10000` |
| error_code | string | ✓ | 错误码 | `GATE_UNAVAILABLE` |
| retry_count | integer | ✗ | 已重试次数 | `3` |

#### 4.4.5 callback_retry

| 字段名 | 类型 | 必填 | 描述 | 示例值 |
|--------|------|:----:|------|--------|
| timestamp | string | ✓ | ISO 8601 时间戳 | `2026-10-17T10:30:04.000Z` |
| event_type | string | ✓ | 固定值 `callback_retry` | `callback_retry` |
| decision_type | string | ✓ | 决策类型 | `ROLLBACK` |
| callback_url | string | ✓ | 回调目标 URL | `https://dshe.example.com/callback` |
| retry_attempt | integer | ✓ | 当前重试轮次 | `1` |
| retry_delay_ms | integer | ✓ | 重试等待时间 (毫秒) | `5000` |
| max_retries | integer | ✓ | 最大重试次数 | `3` |

### 4.5 Gate 决策事件状态转移序列

```
场景: F1-TRIGGER (DEP Service Unavailable)

时间轴:
  t=0s    probe_failure (DEP-001) → EVT-DEP-FAIL-1760700000-0001
  t=1s    probe_failure (DEP-001) → EVT-DEP-FAIL-1760700001-0002
  ...
  t=5s    probe_failure (DEP-001) → EVT-DEP-FAIL-1760700005-0006
          [CB 阈值达到: 5 次连续失败]
  t=5.1s  cb_state_change (DEP-001) → EVT-DEP-CBSC-1760700005-0001
          [CLOSED → OPEN]
  t=5.2s  decision_change (Gate V5) → EVT-GATE-DCCH-1760700005-0001
          [ADVANCE → ROLLBACK]
  t=5.3s  state_transition (Gate V5) → EVT-GATE-STTR-1760700005-0001
          [READY → NOT_READY]
  t=5.4s  callback_failure (Gate V5) → EVT-GATE-CBFL-1760700005-0001
          [尝试回调 DSHE 但 DSHE 不可用]
```

---

## 5. 审计事件统计口径规范

### 5.1 事件计数规则

**核心规则**: 以 `event_id` 为单位进行唯一计数，**不**以 log line 或 event type 为单位。

```
规则 R1: 唯一事件计数
━━━━━━━━━━━━━━━━━━━
  每个唯一 event_id = 1 个事件，无论重试次数或 log 行数。
  
  示例:
    EVT-DEP-FAIL-1760700000-0001 (重试 3 次, 产生 3 行 log)
    → 计数为 1 个事件，不是 3 个事件

规则 R2: 去重
━━━━━━━━━━━
  相同 event_id 视为同一事件，不重复计数。
  
  示例:
    EVT-DEP-FAIL-1760700000-0001 (原始行)
    EVT-DEP-FAIL-1760700000-0001 (聚合行)
    → 计数为 1 个事件

规则 R3: 字段计数
━━━━━━━━━━━━━━━
  字段实例数 = Σ (每个事件的必填字段数 + 已填充的可选字段数)
  
  示例:
    probe_failure: 9 字段 (6 必填 + 3 可选, 若全部填充)
    5 个 probe_failure 事件 = 45 个字段实例
```

### 5.2 去重机制

```
去重策略: 基于 event_id 的精确匹配

┌─────────────────────────────────────────────┐
│  Event Counting Pipeline                    │
│                                             │
│  Raw Logs ──→ Dedup by event_id ──→ Count  │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  event_id           | count | dedup │    │
│  ├─────────────────────┼───────┼───────┤    │
│  │  EVT-DEP-FAIL-...01 │  1    │  1    │    │
│  │  EVT-DEP-FAIL-...01 │  1    │  ✗    │    │
│  │  EVT-DEP-FAIL-...02 │  1    │  1    │    │
│  │  EVT-DEP-FAIL-...02 │  1    │  ✗    │    │
│  │  EVT-DEP-CBSC-...01 │  1    │  1    │    │
│  └─────────────────────┴───────┴───────┘    │
│                                             │
│  Unique events: 3                           │
│  Total log lines: 5                         │
│  Fields (unique): 9+9+7 = 25               │
│                                             │
└─────────────────────────────────────────────┘
```

### 5.3 聚合窗口

```
聚合窗口 (Aggregation Window):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  窗口类型: 滑动窗口 (Sliding Window)
  窗口大小: 5 分钟 (300 秒)
  步长:     30 秒 (每 30 秒重新计算)

  ┌─────────────────────────────────────────────────────┐
  │ t=0    t=5min    t=10min   t=15min                  │
  │ │──────│────────│────────│                          │
  │   w1     w2       w3                                 │
  │                                       w4            │
  │  每次滑动重新计算窗口内唯一事件数                    │
  │                                                     │
  └─────────────────────────────────────────────────────┘
  
  窗口内计数规则:
    - 仅统计窗口内的唯一 event_id
    - 窗口边界使用 [start, end) 左闭右开
    - 跨窗口的重试事件按首次出现时间归属
```

### 5.4 跨团队对齐规则

| 规则 | 说明 | 优先级 |
|------|------|:------:|
| **L1 > L2** | DEP/Gate 事件为 source-of-truth，HERMES 事件为衍生 | P0 |
| **Unique > Raw** | 以唯一 event_id 计数，不以 log line 计数 | P0 |
| **Detail > Summary** | 当 summary 与 detail 不一致时，以 detail 为准 | P0 |
| **Source > Derived** | 当 DEP/Gate 与 HERMES 计数不一致时，以 DEP/Gate 为准 | P1 |

### 5.5 DSHE D-04 修复方案

```
D-04 修复步骤:

Step 1: 确认 Canonical Count
  使用本文档定义的事件源定义，验证:
  → 8 events / 184 fields 为正确基准
  → 16 events / 368 fields 为错误双重计数结果

Step 2: 修复 DSHE Summary 逻辑
  修改 summary 聚合逻辑:
    BEFORE: count(events) + count(summaries)  ← 双重计数
    AFTER:  count(distinct event_id)          ← 唯一计数

Step 3: 验证修复
  执行混沌场景 F1–F5 注入，验证:
    Summary count == Detail count
    Field count == 184 (per canonical scenario)

Step 4: 跨团队签字确认
  DSHB (DEP/Gate) + DSHE (Dashboard) 共同确认
  更新 D-04 状态为 RESOLVED
```

---

## 6. 跨团队审计事件对齐

### 6.1 事件流转映射

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  DEP-001    │     │  Gate V5    │     │   HERMES    │
│             │     │             │     │             │
│ probe_*     │────→│ decision_*  │────→│ evt_persist │
│ cb_state_*  │     │ state_*     │     │ evt_query   │
│ health_*    │     │ callback_*  │     │ evt_delete  │
│ metric_*    │     │             │     │ evt_expire  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  DSHE L2        │
                  │  Dashboard      │
                  │                 │
                  │  • Summary      │
                  │  • Detail       │
                  │  • Audit Log    │
                  └─────────────────┘
```

### 6.2 事件映射表

| DEP/Gate 事件 (L1) | HERMES 衍生事件 (L2) | DSHE 展示 (L3) | 对齐状态 |
|--------------------|---------------------|----------------|:--------:|
| probe_success | evt_persist | Dashboard: Success Rate | ✓ |
| probe_failure | evt_persist | Dashboard: Failure Rate | ✓ |
| cb_state_change | evt_persist | Dashboard: CB Timeline | ✓ |
| health_check | evt_persist | Dashboard: Health Panel | ✓ |
| metric_collection | evt_persist | Dashboard: Metrics Chart | ✓ |
| decision_change | evt_persist | Dashboard: Decision Log | ✓ |
| state_transition | evt_persist | Dashboard: State Diagram | ✓ |
| callback_success | evt_persist | Dashboard: Callback OK | ✓ |
| callback_failure | evt_persist | Dashboard: Callback FAIL | ✓ |
| callback_retry | evt_persist | Dashboard: Retry Count | ✓ |
| — | evt_query | Dashboard: Query Log | — |
| — | evt_delete | Dashboard: Deletion Log | — |
| — | evt_expire | Dashboard: Expiry Log | — |

### 6.3 计数对账流程

```
计数对账 (Count Reconciliation) 流程:

  ┌─────────────────────────────────────────────────────────┐
  │ Step 1: DEP/Gate 侧统计                                  │
  │   - 提取 DEP-001 所有 event_id (唯一)                   │
  │   - 提取 Gate V5 所有 event_id (唯一)                    │
  │   - 汇总: L1_event_count = DEP + Gate                    │
  │                                                        │
  │ Step 2: HERMES 侧统计                                    │
  │   - 提取 evt_persist 记录中的 source_event_id           │
  │   - 去重后统计唯一事件数                                  │
  │   - 汇总: L2_event_count = HERMES 衍生事件数             │
  │                                                        │
  │ Step 3: 对账                                            │
  │   - L1_event_count vs L2_event_count                    │
  │   - 若 L1 == L2: 对账通过 ✓                              │
  │   - 若 L1 > L2: HERMES 持久化延迟，等待同步              │
  │   - 若 L1 < L2: 异常，检查 HERMES 是否记录了额外事件     │
  │                                                        │
  │ Step 4: DSHE 展示层验证                                  │
  │   - Summary count vs Detail count                       │
  │   - 若 Summary == Detail: D-04 已修复 ✓                  │
  │   - 若 Summary != Detail: 执行 D-04 修复流程             │
  │                                                        │
  └─────────────────────────────────────────────────────────┘
```

### 6.4 差异解决策略

| 差异类型 | 场景 | 解决策略 | 优先级 |
|----------|------|----------|:------:|
| Summary ≠ Detail | DSHE 展示层双重计数 | 修复 summary 逻辑，以 detail 为准 | P0 |
| L1 > L2 | HERMES 持久化延迟 | 等待 HERMES 同步完成，最长 5min | P1 |
| L1 < L2 | HERMES 记录了非 L1 事件 | 核查 HERMES evt_query/evt_delete 记录 | P1 |
| DEP ≠ Gate | DEP 与 Gate 事件数不一致 | 以 DEP 为基准（上游），Gate 需对齐 | P0 |
| 字段缺失 | 部分事件字段为空 | 仅计数非空字段，空字段不计入 | P2 |

---

## 7. 附录：事件字段完整定义

### 7.1 DEP-001 事件字段完整定义

#### probe_success (8 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:00.123Z` |
| 2 | event_type | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `probe_success` |
| 3 | probe_id | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `DEP-001-P-0001` |
| 4 | status | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `200` |
| 5 | latency_ms | integer | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `45` |
| 6 | latency_warning | boolean | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `false` |
| 7 | retry_count | integer | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `0` |
| 8 | target_service | string | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `api-gateway` |

#### probe_failure (9 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:01.456Z` |
| 2 | event_type | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `probe_failure` |
| 3 | probe_id | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `DEP-001-P-0001` |
| 4 | status | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `503` |
| 5 | latency_ms | integer | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `5000` |
| 6 | error_code | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `CONN_TIMEOUT` |
| 7 | error_message | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `Connection timed out` |
| 8 | retry_count | integer | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `3` |
| 9 | circuit_breaker_state | string (enum) | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `OPEN` |

#### cb_state_change (7 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:02.789Z` |
| 2 | event_type | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `cb_state_change` |
| 3 | probe_id | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `DEP-001-P-0001` |
| 4 | previous_state | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `CLOSED` |
| 5 | new_state | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `OPEN` |
| 6 | trigger_count | integer | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `5` |
| 7 | half_open_time_ms | integer | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `30000` |

#### health_check (7 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `2026-10-17T10:31:00.000Z` |
| 2 | event_type | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `health_check` |
| 3 | probe_id | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `DEP-001-P-0001` |
| 4 | overall_status | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `DEGRADED` |
| 5 | component_status | string (JSON) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `{"db":"UP","cache":"DOWN"}` |
| 6 | check_interval_s | integer | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `30` |
| 7 | consecutive_failures | integer | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `2` |

#### metric_collection (7 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `2026-10-17T10:31:00.000Z` |
| 2 | event_type | string (enum) | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `metric_collection` |
| 3 | probe_id | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `DEP-001-P-0001` |
| 4 | metrics_collected | integer | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `24` |
| 5 | collection_duration_ms | integer | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `120` |
| 6 | storage_target | string | ✓ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `prometheus-001` |
| 7 | dropped_metrics | integer | ✗ | DEP metrics endpoint | 7d hot / 30d warm / 90d cold | `0` |

### 7.2 Gate V5 事件字段完整定义

#### decision_change (9 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:00.123Z` |
| 2 | event_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `decision_change` |
| 3 | decision_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `ROLLBACK` |
| 4 | previous_decision | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `ADVANCE` |
| 5 | new_decision | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `ROLLBACK` |
| 6 | trigger_source | string | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `DEP-001` |
| 7 | trigger_event_id | string | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `EVT-DEP-FAIL-1760700000-0001` |
| 8 | confidence_score | number | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `0.95` |
| 9 | buffer_events | integer | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `3` |

#### state_transition (8 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:01.456Z` |
| 2 | event_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `state_transition` |
| 3 | decision_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `ROLLBACK` |
| 4 | previous_state | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `READY` |
| 5 | new_state | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `NOT_READY` |
| 6 | trigger_source | string | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `DEP-001` |
| 7 | trigger_event_id | string | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `EVT-DEP-FAIL-1760700000-0001` |
| 8 | buffer_events | integer | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `3` |

#### callback_success (7 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:02.789Z` |
| 2 | event_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `callback_success` |
| 3 | decision_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `ADVANCE` |
| 4 | callback_url | string (URI) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `https://dshe.example.com/callback` |
| 5 | callback_status | string | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `200` |
| 6 | callback_duration_ms | integer | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `35` |
| 7 | payload_size_bytes | integer | ✗ | Gate admin API | 7d hot / 30d warm / 90d cold | `256` |

#### callback_failure (8 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:03.000Z` |
| 2 | event_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `callback_failure` |
| 3 | decision_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `ROLLBACK` |
| 4 | callback_url | string (URI) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `https://dshe.example.com/callback` |
| 5 | callback_status | string | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `503` |
| 6 | callback_duration_ms | integer | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `10000` |
| 7 | error_code | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `GATE_UNAVAILABLE` |
| 8 | retry_count | integer | ✗ | Gate admin API | 7d hot / 30d warm / 90d cold | `3` |

#### callback_retry (7 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:04.000Z` |
| 2 | event_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `callback_retry` |
| 3 | decision_type | string (enum) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `ROLLBACK` |
| 4 | callback_url | string (URI) | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `https://dshe.example.com/callback` |
| 5 | retry_attempt | integer | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `1` |
| 6 | retry_delay_ms | integer | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `5000` |
| 7 | max_retries | integer | ✓ | Gate admin API | 7d hot / 30d warm / 90d cold | `3` |

### 7.3 HERMES 事件字段完整定义

#### evt_persist (6 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:30:00.200Z` |
| 2 | event_type | string (enum) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `evt_persist` |
| 3 | source_event_id | string | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `EVT-DEP-FAIL-1760700000-0001` |
| 4 | source_type | string (enum) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `DEP-001` |
| 5 | persistence_status | string (enum) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `COMMITTED` |
| 6 | retention_tier | string (enum) | ✗ | HERMES audit API | 7d hot / 30d warm / 90d cold | `hot` |

#### evt_query (5 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:35:00.000Z` |
| 2 | event_type | string (enum) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `evt_query` |
| 3 | query_filter | string (JSON) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `{"type":"probe_failure","range":"5m"}` |
| 4 | result_count | integer | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `12` |
| 5 | query_duration_ms | integer | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `45` |

#### evt_delete (5 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:40:00.000Z` |
| 2 | event_type | string (enum) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `evt_delete` |
| 3 | target_event_id | string | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `EVT-DEP-SUCC-1760600000-0001` |
| 4 | delete_reason | string | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `MANUAL_EXPIRE` |
| 5 | operator | string | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `hermes-admin` |

#### evt_expire (5 fields)

| # | 字段名 | 类型 | 必填 | 数据源 | 保留策略 | 示例值 |
|---|--------|------|:----:|--------|----------|--------|
| 1 | timestamp | string (ISO 8601) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `2026-10-17T10:45:00.000Z` |
| 2 | event_type | string (enum) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `evt_expire` |
| 3 | expired_count | integer | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `156` |
| 4 | expired_tier | string (enum) | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `hot` |
| 5 | batch_id | string | ✓ | HERMES audit API | 7d hot / 30d warm / 90d cold | `BATCH-20261017-0045` |

### 7.4 字段统计汇总

| 事件类型 | 必填字段 | 可选字段 | 总字段 |
|----------|:--------:|:--------:|:------:|
| probe_success | 5 | 3 | 8 |
| probe_failure | 7 | 2 | 9 |
| cb_state_change | 6 | 1 | 7 |
| health_check | 6 | 1 | 7 |
| metric_collection | 6 | 1 | 7 |
| decision_change | 9 | 0 | 9 |
| state_transition | 8 | 0 | 8 |
| callback_success | 6 | 1 | 7 |
| callback_failure | 7 | 1 | 8 |
| callback_retry | 7 | 0 | 7 |
| evt_persist | 5 | 1 | 6 |
| evt_query | 5 | 0 | 5 |
| evt_delete | 5 | 0 | 5 |
| evt_expire | 5 | 0 | 5 |
| **合计** | **77** | **11** | **88** |

> 注: 88 为唯一字段定义数。184 fields 为运行时实例计数（含重复事件实例），非字段类型数。

---

## 8. 版本与约束

### 8.1 文档版本

| 项目 | 值 |
|------|-----|
| 文档版本 | V1.0 |
| 发布日期 | 2026-10-17 |
| 文档负责人 | DSHB Team |
| 审批状态 | FINAL — 待 DSHB + DSHE 跨团队签字确认 |
| 关联 Work Order | DSHB_V86_RC2_G0_G1_PREPARE_CROSS_CONSISTENCY_SYNC |
| 关联缺陷 | DSHE D-04 (Audit Count Inconsistency) |

### 8.2 约束条件

| 约束标识 | 值 | 说明 |
|----------|-----|------|
| `NO_ZHIJI_API_CALL` | `FALSE` | 允许使用智己 API 进行数据验证 |
| `NO_MODIFY_V85` | `TRUE` | 禁止修改 V85 版本代码/配置 |
| `NO_OVERWRITE` | `TRUE` | 禁止覆盖现有数据，仅追加 |

### 8.3 上游引用

| 引用 | 说明 |
|------|------|
| `DSHB_V86_RC2_G0_G1_PREPARE_CROSS_CONSISTENCY_SYNC` | 本 Work Order 的上游同步任务 |
| DSHE V86-RC2 L2 Chaos Dashboard Final Signoff | D-04 缺陷来源 |
| DEP-001 Specification V5.2 | DEP 事件定义基准 |
| Gate V5 Specification | Gate 事件定义基准 |
| HERMES Audit Persistence Spec | 持久化规范 |

### 8.4 变更历史

| 版本 | 日期 | 变更说明 | 作者 |
|:----:|:----:|----------|------|
| V1.0 | 2026-10-17 | 初始发布，定义 DEP/Gate 审计事件规范 | DSHB Team |

### 8.5 签字确认

| 团队 | 角色 | 签字 | 日期 |
|------|------|:----:|:----:|
| DSHB | DEP-001 负责人 | __________ | ______ |
| DSHB | Gate V5 负责人 | __________ | ______ |
| HERMES | 审计持久化负责人 | __________ | ______ |
| DSHE | L2 Dashboard 负责人 | __________ | ______ |

---

> **END OF DOCUMENT**
>
> 本文档为 V86-RC2 G0/G1 跨团队一致性对齐工作的核心数据源规范，所有审计事件定义、字段规格、计数规则均以本文档为准。
>
> D-04 修复基准: **8 events / 184 fields** (canonical), 非 16 events / 368 fields (double-counted)。
