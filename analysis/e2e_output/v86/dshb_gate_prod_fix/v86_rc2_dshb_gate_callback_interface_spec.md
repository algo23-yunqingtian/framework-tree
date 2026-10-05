# Gate V5 灰度决策回调接口规范

> **工单编号**: DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION / T3.3
> **关联脚本**: `gate_v5_gray_callback.py` V1.0
> **上游事件源**: HERMES `gray_gate_decider.py` (5 决策: ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE)
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE / NO_ZHIJI_API_CALL=FALSE
> **文档版本**: V1.0
> **编制日期**: 2026-10-17
> **状态**: `DSHB_PROD_PHASE_G0_SHADOW_TRAFFIC_ISOLATION_DONE=PENDING`

---

## 目录

1. [接口概述](#1-接口概述)
2. [接口架构](#2-接口架构)
3. [事件结构定义](#3-事件结构定义)
4. [回调接口规范](#4-回调接口规范)
5. [状态查询接口](#5-状态查询接口)
6. [健康检查接口](#6-健康检查接口)
7. [审计统计接口](#7-审计统计接口)
8. [状态机定义](#8-状态机定义)
9. [决策-动作联动矩阵](#9-决策-动作联动矩阵)
10. [错误处理与重试](#10-错误处理与重试)
11. [事件去重与幂等](#11-事件去重与幂等)
12. [HERMES 对齐规范](#12-hermes-对齐规范)
13. [安全与鉴权](#13-安全与鉴权)
14. [监控与告警](#14-监控与告警)
15. [部署配置](#15-部署配置)
16. [附录](#16-附录)

---

## 1. 接口概述

### 1.1 功能描述

Gate V5 灰度决策回调接口是 DSHB V86-RC2 G0 影子投产阶段的核心闭环组件，负责：

1. **接收 HERMES 灰度决策事件**: 订阅 `gray_gate_decider.py` 输出的 5 种决策 (ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE)
2. **自动更新 Gate 状态**: 根据决策结果更新 Gate V5 状态 (READY/WARN/NOT_READY)
3. **联动 DEP 巡检**: 决策驱动 DEP-001 周期性巡检启停
4. **联动影子镜像**: 决策驱动流量镜像启停与采样率调整
5. **审计事件持久化**: 全量决策事件审计记录与上报

### 1.2 接口基本信息

| 属性 | 值 |
|------|-----|
| 协议 | HTTP/HTTPS (TLS 1.3) |
| 端口 | 9090 (默认) |
| 路径前缀 | `/api/v1/gate/callback/` |
| 认证 | Token + mTLS (生产) / 无认证 (预发) |
| 超时 | 30s (请求) / 5s (健康检查) |
| 编码 | UTF-8 / JSON |
| 版本 | V1.0 |

### 1.3 接口列表

| 端点 | 方法 | 描述 | 调用方 |
|------|------|------|--------|
| `/api/v1/gate/callback/decision` | POST | 接收灰度决策事件 | HERMES `gray_gate_decider` |
| `/api/v1/gate/callback/status` | GET | 查询 Gate 状态 | DSHE / 运维 |
| `/api/v1/gate/callback/health` | GET | 健康检查 | K8s / LB |
| `/api/v1/gate/callback/audit/stats` | GET | 审计统计 | DSHE / 运维 |

---

## 2. 接口架构

### 2.1 架构图

```
HERMES gray_gate_decider.py
        │
        │  HTTP POST /api/v1/gate/callback/decision
        │  (JSON body: decision event)
        ▼
┌──────────────────────────────────────────────┐
│  Gate V5 Gray Callback Handler               │
│  (gate_v5_gray_callback.py)                   │
│                                                │
│  ┌─────────────────────────────────────────┐  │
│  │ 1. 事件去重检查                          │  │
│  │    └── MD5(content) 60s 窗口去重         │  │
│  └─────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │ 2. 事件结构验证                          │  │
│  │    └── 必填字段 + 枚举值校验              │  │
│  └─────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │ 3. 决策动作执行                          │  │
│  │    ├── Gate 状态更新                      │  │
│  │    ├── DEP 巡检启停                      │  │
│  │    ├── 影子镜像启停                      │  │
│  │    └── 采样率调整                         │  │
│  └─────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │ 4. 审计事件持久化                        │  │
│  │    └── JSONL + 外部推送 (可选)           │  │
│  └─────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────┐  │
│  │ 5. 状态更新 (线程安全)                   │  │
│  │    └── gate_status / dep_probe / mirror │  │
│  └─────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
Gate API   DEP Probe   Shadow Mirror
(:9090)   (CLI)       (Envoy API)
```

### 2.2 数据流

```
HERMES → Callback → Gate Status API → Gate DB
                  → DEP Probe CLI → DEP Process
                  → Shadow Mirror API → Envoy Router
                  → Audit Logger → JSONL + External Push
```

---

## 3. 事件结构定义

### 3.1 决策事件结构 (HERMES_GRAY_DECISION_EVENT)

```json
{
  "event_id": "uuid-v4",
  "timestamp": "2026-10-17T10:00:00Z",
  "decision": "ADVANCE",
  "decision_reason": "G0 观测完成，准入 G1",
  "current_stage": "G0",
  "next_stage": "G1",
  "dep_001_status": "RECOVERED",
  "observe_hours_elapsed": 24.0,
  "observe_hours_required": 24.0,
  "faults_detected": [],
  "all_faults": [],
  "rollback_info": null,
  "gaps": null,
  "remaining_hours": null,
  "next_traffic": null,
  "next_varieties": null,
  "metrics_snapshot": {
    "p95_ms": 18.2,
    "p99_ms": 45.6,
    "error_rate": 0.0045,
    "dep_flap_count": 0,
    "critical_alerts": 0,
    "non_zero_rate": 0.998,
    "throughput_drop_pct": 0.0
  }
}
```

### 3.2 字段定义

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `event_id` | string (UUID) | ❌ | 事件唯一 ID (缺省自动生成) | `a1b2c3d4-...` |
| `timestamp` | ISO8601 | ✅ | 事件产生时间 | `2026-10-17T10:00:00Z` |
| `decision` | enum | ✅ | 决策类型 | `ADVANCE` |
| `decision_reason` | string | ✅ | 决策原因 | `G0 观测完成，准入 G1` |
| `current_stage` | enum | ✅ | 当前灰度阶段 | `G0` |
| `next_stage` | enum | ❌ | 下一阶段 (仅 ADVANCE) | `G1` |
| `dep_001_status` | string | ❌ | DEP-001 状态 | `RECOVERED` |
| `observe_hours_elapsed` | float | ❌ | 已观测时长 | `24.0` |
| `observe_hours_required` | float | ❌ | 所需观测时长 | `24.0` |
| `faults_detected` | array | ❌ | 已检测故障 | `["F1"]` |
| `all_faults` | array | ❌ | 全部故障详情 | `[{"id":"F1",...}]` |
| `rollback_info` | object | ❌ | 回滚信息 (仅 ROLLBACK) | `{...}` |
| `gaps` | array | ❌ | 准入缺口 (仅 HOLD) | `["..."]` |
| `remaining_hours` | float | ❌ | 剩余观测时长 (仅 OBSERVE) | `12.0` |
| `next_traffic` | string | ❌ | 下一阶段流量 (仅 ADVANCE) | `1%` |
| `next_varieties` | int | ❌ | 下一阶段品种数 (仅 ADVANCE) | `1` |
| `metrics_snapshot` | object | ❌ | 指标快照 | `{...}` |

### 3.3 决策类型定义

| 决策 | 值 | 说明 | 触发条件 | 优先级 |
|------|-----|------|---------|--------|
| ADVANCE | `"ADVANCE"` | 灰度推进 | 观测完成 + 准入通过 | 1 |
| HOLD | `"HOLD"` | 灰度暂停 | 准入未通过 | 2 |
| OBSERVE | `"OBSERVE"` | 灰度观测中 | 观测期未满 | 3 |
| ROLLBACK | `"ROLLBACK"` | 灰度回滚 | 故障触发 | 4 |
| COMPLETE | `"COMPLETE"` | 灰度完成 | G5 观测完成 | 0 |

### 3.4 灰度阶段定义

| 阶段 | 值 | 流量 | 品种数 | 观测时长 | 说明 |
|------|-----|------|--------|---------|------|
| G0 | `"G0"` | 0% | 0 | 24h | 影子测试 |
| G1 | `"G1"` | 1% | 1 | 24h | 单品种 |
| G2 | `"G2"` | 5% | 7 | 24h | 小范围 |
| G3 | `"G3"` | 20% | 28 | 48h | 中范围 |
| G4 | `"G4"` | 50% | 42 | 48h | 大范围 |
| G5 | `"G5"` | 100% | 56 | 168h | 全量 |

---

## 4. 回调接口规范

### 4.1 POST /api/v1/gate/callback/decision

**描述**: 接收 HERMES 灰度决策事件，执行决策动作闭环

**请求**:

```http
POST /api/v1/gate/callback/decision HTTP/1.1
Host: gate-callback:9090
Content-Type: application/json
Authorization: Bearer <token>

{
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-10-17T10:00:00Z",
  "decision": "ADVANCE",
  "decision_reason": "G0 观测完成，准入 G1",
  "current_stage": "G0",
  "next_stage": "G1",
  "dep_001_status": "RECOVERED",
  "observe_hours_elapsed": 24.0,
  "observe_hours_required": 24.0,
  "faults_detected": [],
  "all_faults": [],
  "metrics_snapshot": {
    "p95_ms": 18.2,
    "p99_ms": 45.6,
    "error_rate": 0.0045
  }
}
```

**响应 (成功)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-Id: c9d8e7f6-...

{
  "status": "PROCESSED",
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "decision": "ADVANCE",
  "current_stage": "G0",
  "timestamp": "2026-10-17T10:00:01Z",
  "actions": {
    "gate_status": {
      "status": "OK",
      "old_status": "WARN",
      "new_status": "READY",
      "message": "Gate 状态已更新: WARN → READY"
    },
    "dep_probe": {
      "status": "OK",
      "action": "START",
      "message": "DEP 周期性巡检已启动"
    },
    "shadow_mirror": {
      "status": "OK",
      "action": "START",
      "message": "影子流量镜像已启动"
    },
    "sampling_rate": {
      "status": "OK",
      "old_rate": 10.0,
      "new_rate": 20.0,
      "message": "采样率已更新: 10.0% → 20.0%"
    }
  },
  "message": "灰度推进：启动巡检+镜像"
}
```

**响应 (重复事件)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "DUPLICATE",
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "decision": "ADVANCE",
  "action": "ignored",
  "message": "事件已忽略 (重复)"
}
```

**响应 (验证失败)**:

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": "INVALID",
  "event_id": "invalid-evt",
  "decision": "UNKNOWN",
  "action": "rejected",
  "message": "事件验证失败: 无效决策值: UNKNOWN",
  "errors": ["无效决策值: UNKNOWN (有效值: ADVANCE, HOLD, OBSERVE, ROLLBACK, COMPLETE)"]
}
```

**响应 (内部错误)**:

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "status": "ERROR",
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "decision": "ADVANCE",
  "action": "failed",
  "message": "内部错误: Gate 状态更新失败",
  "error": "connection refused: gate.svc:9090"
}
```

### 4.2 决策响应矩阵

| 决策 | Gate 动作 | DEP 巡检动作 | 影子镜像动作 | 采样率动作 | 响应 status |
|------|----------|------------|------------|----------|------------|
| ADVANCE | READY | START | START | 按下一阶段调整 | `PROCESSED` |
| HOLD | WARN | CONTINUE | CONTINUE | 不变 | `PROCESSED` |
| OBSERVE | WARN | CONTINUE | CONTINUE | 不变 | `PROCESSED` |
| ROLLBACK | NOT_READY | STOP | STOP | 不变 | `PROCESSED` |
| COMPLETE | READY | STOP | STOP | 不变 | `PROCESSED` |

---

## 5. 状态查询接口

### 5.1 GET /api/v1/gate/callback/status

**描述**: 查询 Gate V5 回调处理器当前状态

**请求**:

```http
GET /api/v1/gate/callback/status HTTP/1.1
Host: gate-callback:9090
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "gate_status": "READY",
  "dep_probe_running": true,
  "shadow_mirror_running": true,
  "shadow_sampling_rate": 20.0,
  "current_stage": "G1",
  "last_decision": "ADVANCE",
  "last_decision_time": "2026-10-17T10:00:00Z",
  "decision_count": 5,
  "error_count": 0,
  "version": "1.0",
  "work_order": "DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION",
  "timestamp": "2026-10-17T10:05:00Z"
}
```

**状态字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `gate_status` | string | Gate 状态 (READY/WARN/NOT_READY) |
| `dep_probe_running` | bool | DEP 巡检是否运行 |
| `shadow_mirror_running` | bool | 影子镜像是否运行 |
| `shadow_sampling_rate` | float | 当前采样率 (%) |
| `current_stage` | string | 当前灰度阶段 (G0-G5) |
| `last_decision` | string | 最近决策 |
| `last_decision_time` | ISO8601 | 最近决策时间 |
| `decision_count` | int | 累计决策数 |
| `error_count` | int | 累计错误数 |
| `version` | string | 脚本版本 |
| `work_order` | string | 工单编号 |
| `timestamp` | ISO8601 | 查询时间 |

---

## 6. 健康检查接口

### 6.1 GET /api/v1/gate/callback/health

**描述**: 健康检查端点，供 K8s livenessProbe 与 readinessProbe 使用

**请求**:

```http
GET /api/v1/gate/callback/health HTTP/1.1
Host: gate-callback:9090
```

**响应 (健康)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "HEALTHY",
  "version": "1.0",
  "timestamp": "2026-10-17T10:05:00Z",
  "work_order": "DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION"
}
```

**响应 (不健康)**:

```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "status": "UNHEALTHY",
  "version": "1.0",
  "timestamp": "2026-10-17T10:05:00Z",
  "work_order": "DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION",
  "reason": "Gate 状态更新失败，连续失败次数: 3"
}
```

### 6.2 K8s 探针配置

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

## 7. 审计统计接口

### 7.1 GET /api/v1/gate/callback/audit/stats

**描述**: 查询审计事件统计信息

**请求**:

```http
GET /api/v1/gate/callback/audit/stats HTTP/1.1
Host: gate-callback:9090
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "total_events": 42,
  "recent_events": 42,
  "event_types": {
    "DECISION_RECEIVED": 10,
    "DECISION_PROCESSED": 10,
    "DECISION_FAILED": 2,
    "GATE_STATUS_UPDATED": 8,
    "DEP_PROBE_STARTED": 2,
    "DEP_PROBE_STOPPED": 1,
    "SHADOW_MIRROR_STARTED": 3,
    "SHADOW_MIRROR_STOPPED": 1,
    "SHADOW_RATE_CHANGED": 2,
    "HEALTH_CHECK": 2,
    "CONFIG_CHANGED": 0,
    "ERROR": 1
  },
  "severities": {
    "INFO": 35,
    "WARN": 5,
    "ERROR": 1,
    "CRITICAL": 0
  }
}
```

### 7.2 审计事件类型

| 事件类型 | 说明 | 级别 |
|----------|------|------|
| `DECISION_RECEIVED` | 决策事件已接收 | INFO |
| `DECISION_PROCESSED` | 决策事件已处理 | INFO |
| `DECISION_FAILED` | 决策事件处理失败 | WARN/ERROR |
| `GATE_STATUS_UPDATED` | Gate 状态已更新 | INFO |
| `DEP_PROBE_STARTED` | DEP 巡检已启动 | INFO |
| `DEP_PROBE_STOPPED` | DEP 巡检已停止 | INFO |
| `SHADOW_MIRROR_STARTED` | 影子镜像已启动 | INFO |
| `SHADOW_MIRROR_STOPPED` | 影子镜像已停止 | INFO |
| `SHADOW_RATE_CHANGED` | 采样率已变更 | INFO |
| `HEALTH_CHECK` | 健康检查 | INFO |
| `CONFIG_CHANGED` | 配置已变更 | INFO |
| `ERROR` | 错误事件 | ERROR |

### 7.3 审计事件级别

| 级别 | 说明 | 处理 |
|------|------|------|
| `INFO` | 正常信息 | 记录 |
| `WARN` | 警告 (重复事件、状态跳过) | 记录 + 监控 |
| `ERROR` | 错误 (验证失败、执行失败) | 记录 + 告警 |
| `CRITICAL` | 严重错误 (连续失败) | 记录 + 告警 + 人工介入 |

---

## 8. 状态机定义

### 8.1 Gate 状态机

```
                          ┌──────────────────────────────────┐
                          │                                    │
                          ▼                                    │
                    ┌──────────┐                                │
                    │  READY   │◄──── ADVANCE / COMPLETE ──────┤
                    └────┬─────┘                                │
                         │                                      │
                    HOLD / OBSERVE                              │
                         │                                      │
                    ┌────▼─────┐                                │
                    │   WARN   │                                │
                    └────┬─────┘                                │
                         │                                      │
                    ROLLBACK                                  │
                         │                                      │
                    ┌────▼──────────┐                          │
                    │  NOT_READY    │────────── ADVANCE ───────┘
                    └───────────────┘
```

### 8.2 Gate 状态定义

| 状态 | 值 | 说明 | 联动动作 |
|------|-----|------|---------|
| READY | `"READY"` | 灰度可推进 | 巡检启动、镜像启动 |
| WARN | `"WARN"` | 灰度暂停/观测中 | 巡检继续、镜像继续 |
| NOT_READY | `"NOT_READY"` | 灰度回滚 | 巡检停止、镜像停止 |

### 8.3 状态转换规则

| 当前状态 | 决策 | 目标状态 | 动作 |
|----------|------|---------|------|
| READY | ADVANCE | READY | 保持状态 (已在 READY) |
| READY | HOLD | WARN | 降级 |
| READY | OBSERVE | WARN | 降级 |
| READY | ROLLBACK | NOT_READY | 降级 |
| READY | COMPLETE | READY | 保持状态 |
| WARN | ADVANCE | READY | 升级 |
| WARN | HOLD | WARN | 保持状态 |
| WARN | OBSERVE | WARN | 保持状态 |
| WARN | ROLLBACK | NOT_READY | 降级 |
| WARN | COMPLETE | READY | 升级 |
| NOT_READY | ADVANCE | READY | 升级 |
| NOT_READY | HOLD | WARN | 升级 |
| NOT_READY | OBSERVE | WARN | 升级 |
| NOT_READY | ROLLBACK | NOT_READY | 保持状态 (已在 NOT_READY) |
| NOT_READY | COMPLETE | READY | 升级 |

---

## 9. 决策-动作联动矩阵

### 9.1 完整联动矩阵

| 决策 | Gate 状态 | DEP 巡检 | 影子镜像 | 采样率 | 审计事件 | 说明 |
|------|----------|---------|---------|--------|---------|------|
| ADVANCE | → READY | START | START | 按下一阶段 | `GATE_STATUS_UPDATED` + `DEP_PROBE_STARTED` + `SHADOW_MIRROR_STARTED` + `SHADOW_RATE_CHANGED` | 灰度推进 |
| HOLD | → WARN | CONTINUE | CONTINUE | 不变 | `GATE_STATUS_UPDATED` | 灰度暂停 |
| OBSERVE | → WARN | CONTINUE | CONTINUE | 不变 | `GATE_STATUS_UPDATED` | 灰度观测 |
| ROLLBACK | → NOT_READY | STOP | STOP | 不变 | `GATE_STATUS_UPDATED` + `DEP_PROBE_STOPPED` + `SHADOW_MIRROR_STOPPED` | 灰度回滚 |
| COMPLETE | → READY | STOP | STOP | 不变 | `GATE_STATUS_UPDATED` + `DEP_PROBE_STOPPED` + `SHADOW_MIRROR_STOPPED` | 灰度完成 |

### 9.2 动作详细映射

| 动作 | 目标 | 操作 | 实现方式 | 超时 |
|------|------|------|---------|------|
| Gate 状态更新 | Gate API | `POST /api/v1/gate/status` | HTTP REST | 5s |
| DEP 巡检启动 | DEP Probe CLI | `python3 dep001_periodic_probe.py` | 子进程 | 30s |
| DEP 巡检停止 | DEP Probe CLI | `kill <pid>` | 子进程 | 5s |
| 影子镜像启动 | Envoy Router | `POST /api/v1/mirror/control/start` | HTTP REST | 5s |
| 影子镜像停止 | Envoy Router | `POST /api/v1/mirror/control/stop` | HTTP REST | 5s |
| 采样率调整 | Envoy Router | `PUT /api/v1/mirror/control/rate` | HTTP REST | 5s |

### 9.3 幂等性保证

| 动作 | 幂等性 | 说明 |
|------|--------|------|
| Gate 状态更新 | ✅ 幂等 | 状态相同时跳过更新 |
| DEP 巡检启动 | ✅ 幂等 | 已运行时跳过启动 |
| DEP 巡检停止 | ✅ 幂等 | 已停止时跳过停止 |
| 影子镜像启动 | ✅ 幂等 | 已运行时跳过启动 |
| 影子镜像停止 | ✅ 幂等 | 已停止时跳过停止 |
| 采样率调整 | ✅ 幂等 | 采样率相同时跳过更新 |

---

## 10. 错误处理与重试

### 10.1 错误处理矩阵

| 错误类型 | 错误码 | HTTP 状态码 | 重试 | 说明 |
|----------|--------|------------|------|------|
| JSON 解析失败 | `INVALID_JSON` | 400 | 否 | 请求体格式错误 |
| 缺少必填字段 | `MISSING_FIELD` | 400 | 否 | 缺少 decision/timestamp/current_stage |
| 无效决策值 | `INVALID_DECISION` | 400 | 否 | decision 不在 ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE |
| 无效阶段值 | `INVALID_STAGE` | 400 | 否 | current_stage 不在 G0-G5 |
| 重复事件 | `DUPLICATE_EVENT` | 200 | 否 | 事件去重窗口内重复 |
| Gate 更新失败 | `GATE_UPDATE_FAIL` | 500 | 是 (3 次) | Gate API 不可用 |
| DEP 操作失败 | `DEP_OPERATE_FAIL` | 500 | 是 (3 次) | DEP CLI 执行失败 |
| 镜像操作失败 | `MIRROR_OPERATE_FAIL` | 500 | 是 (3 次) | Envoy API 不可用 |
| 内部错误 | `INTERNAL_ERROR` | 500 | 是 (3 次) | 未知错误 |

### 10.2 重试策略

| 参数 | 值 | 说明 |
|------|-----|------|
| 最大重试次数 | 3 | 单次决策最多重试 3 次 |
| 重试退避间隔 | 2s | 指数退避: 2s, 4s, 8s |
| 重试超时 | 30s | 单次重试总超时 |
| 重试范围 | 仅网络/服务错误 | 验证错误不重试 |
| 重试后失败 | 记录审计 + 告警 | CRITICAL 级别 |

### 10.3 错误恢复流程

| 步骤 | 操作 | 耗时 | 说明 |
|------|------|------|------|
| 1 | 错误检测 | ≤ 5s | 子操作超时 |
| 2 | 重试 (1st) | 2s | 指数退避 |
| 3 | 重试 (2nd) | 4s | 指数退避 |
| 4 | 重试 (3rd) | 8s | 指数退避 |
| 5 | 审计记录 | ≤ 1s | 记录失败事件 |
| 6 | 告警推送 | ≤ 5s | CRITICAL 告警 |
| 7 | 人工介入 | 视情况 | 运维确认 |

---

## 11. 事件去重与幂等

### 11.1 事件去重机制

| 参数 | 值 | 说明 |
|------|-----|------|
| 去重窗口 | 60s | 60 秒内相同内容事件视为重复 |
| 去重键算法 | MD5(content) | `decision + current_stage + next_stage + dep_001_status` |
| 去重缓存 | 内存 dict | 过期自动清理 |
| 重复事件处理 | 忽略 + 审计记录 | 返回 `status=DUPLICATE` |

### 11.2 去重键计算

```python
def compute_dedup_key(event):
    content = json.dumps({
        "decision": event["decision"],
        "current_stage": event["current_stage"],
        "next_stage": event.get("next_stage"),
        "dep_001_status": event.get("dep_001_status"),
    }, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()
```

### 11.3 幂等性保证

| 场景 | 处理方式 | 保证 |
|------|---------|------|
| 相同事件重复发送 | 去重窗口内忽略 | 不重复执行动作 |
| 事件已处理后再次发送 | 去重窗口内忽略 | 不重复执行动作 |
| 不同决策但相同状态 | 正常处理 | 状态相同时跳过更新 |
| 动作已执行 (如巡检已启动) | 跳过启动 | 不重复启动 |

---

## 12. HERMES 对齐规范

### 12.1 事件结构对齐

| 对齐项 | HERMES `gray_gate_decider` | Gate Callback | 对齐 |
|--------|--------------------------|---------------|------|
| 事件结构 | `HERMES_GRAY_DECISION_EVENT` | `HERMES_GRAY_DECISION_EVENT` | ✅ 一致 |
| 决策类型 | `ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE` | `ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE` | ✅ 一致 |
| 灰度阶段 | `G0/G1/G2/G3/G4/G5` | `G0/G1/G2/G3/G4/G5` | ✅ 一致 |
| 时间戳格式 | ISO8601 UTC | ISO8601 UTC | ✅ 一致 |
| 故障矩阵 | F1-F5 | F1-F5 | ✅ 一致 |
| 字段数量 | 23 | 23 | ✅ 一致 |

### 12.2 事件传输协议

| 维度 | 值 | 说明 |
|------|-----|------|
| 传输方式 | HTTP POST | 实时推送 |
| 传输频率 | 每次决策触发 | 非周期 |
| 传输超时 | 30s | 单次请求超时 |
| 重试次数 | 3 | 传输失败重试 |
| 认证方式 | Token + mTLS (生产) | 预发无认证 |
| 数据格式 | JSON (UTF-8) | 标准 JSON |

### 12.3 事件生命周期

```
HERMES gray_gate_decider
    │
    │ 1. 决策产生 (decision + metrics)
    ▼
    │ 2. HTTP POST → Gate Callback
    ▼
Gate Callback Handler
    │ 3. 事件接收 (DECISION_RECEIVED)
    │ 4. 去重检查 (DUPLICATE?)
    │ 5. 结构验证 (INVALID?)
    │ 6. 动作执行 (GATE_STATUS_UPDATED + DEP_PROBE_* + SHADOW_MIRROR_*)
    │ 7. 处理完成 (DECISION_PROCESSED)
    ▼
    │ 8. 审计持久化 (JSONL + External)
    ▼
DSHE L2 面板 / HERMES 审计
```

---

## 13. 安全与鉴权

### 13.1 认证机制

| 环境 | 认证方式 | 说明 |
|------|---------|------|
| 预发 (sandbox) | 无认证 | 预发环境不强制认证 |
| 生产 (prod) | Token + mTLS | 双向认证 |

### 13.2 Token 认证

| 参数 | 值 | 说明 |
|------|-----|------|
| Token 位置 | `Authorization: Bearer <token>` | HTTP Header |
| Token 格式 | JWT (HS256) | JSON Web Token |
| Token 有效期 | 24 小时 | 到期需刷新 |
| Token 签发 | HERMES 服务 | 由 HERMES 签发 |
| Token 验证 | Gate Callback | 验证签名 + 有效期 |

### 13.3 mTLS 配置

| 参数 | 值 | 说明 |
|------|-----|------|
| TLS 版本 | TLS 1.3 | 最高版本 |
| 证书算法 | RSA 4096 | 强加密 |
| 客户端证书 | HERMES 服务证书 | HERMES → Callback |
| 服务端证书 | Callback 服务证书 | Callback → HERMES |
| CA 证书 | 共享 CA | 双向验证 |
| 证书有效期 | 90 天 | 到期前 15 天告警 |

### 13.4 安全加固

| 措施 | 配置 | 说明 |
|------|------|------|
| 请求速率限制 | 100 req/s | 防止洪泛 |
| 请求大小限制 | 64 KB | 防止大请求 |
| IP 白名单 | HERMES 服务 IP | 仅允许 HERMES |
| CORS | 禁用 | 禁止跨域 |
| 审计日志 | 全量记录 | 所有请求审计 |

---

## 14. 监控与告警

### 14.1 监控指标

| 指标名 | 类型 | 标签 | 说明 |
|--------|------|------|------|
| `gate_callback_decisions_total` | Counter | `decision` | 决策事件总数 |
| `gate_callback_decisions_processed` | Counter | `decision` | 已处理决策数 |
| `gate_callback_decisions_failed` | Counter | `decision` | 处理失败决策数 |
| `gate_callback_decisions_duplicate` | Counter | `decision` | 重复决策数 |
| `gate_callback_gate_status` | Gauge | `status` | 当前 Gate 状态 (0/1/2) |
| `gate_callback_dep_probe_running` | Gauge | - | DEP 巡检运行状态 |
| `gate_callback_shadow_mirror_running` | Gauge | - | 影子镜像运行状态 |
| `gate_callback_shadow_sampling_rate` | Gauge | - | 当前采样率 |
| `gate_callback_request_duration_ms` | Histogram | - | 请求处理延迟 |
| `gate_callback_health` | Gauge | - | 健康状态 (1=健康, 0=不健康) |
| `gate_callback_error_total` | Counter | `type` | 错误总数 |

### 14.2 告警规则

| 告警名 | 条件 | 级别 | 说明 |
|--------|------|------|------|
| Gate Callback Down | `gate_callback_health == 0` | CRITICAL | 服务不可用 |
| Decision Fail Rate High | `failed / total > 10%` | HIGH | 决策失败率过高 |
| Gate Status NOT_READY | `gate_callback_gate_status == 2` | HIGH | Gate 处于 NOT_READY |
| DEP Probe Stopped | `gate_callback_dep_probe_running == 0` (非 ROLLBACK) | WARN | DEP 巡检意外停止 |
| Shadow Mirror Stopped | `gate_callback_shadow_mirror_running == 0` (非 ROLLBACK) | WARN | 影子镜像意外停止 |
| High Duplicate Rate | `duplicate / total > 50%` | WARN | 事件重复率过高 |
| Request Latency High | `p95_request_duration > 1000ms` | WARN | 请求延迟过高 |

### 14.3 告警通知

| 级别 | 通知方式 | 通知目标 | 响应时间 |
|------|---------|---------|---------|
| CRITICAL | 电话 + 短信 | HERMES + 运维 | 5 分钟 |
| HIGH | 企业微信 + 邮件 | HERMES + 运维 | 15 分钟 |
| WARN | 邮件 | 运维 | 30 分钟 |

---

## 15. 部署配置

### 15.1 K8s Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gate-v5-gray-callback
  namespace: gate-ns
  labels:
    app: gate-v5-gray-callback
    version: v1.0
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: gate-v5-gray-callback
  template:
    metadata:
      labels:
        app: gate-v5-gray-callback
        version: v1.0
    spec:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: node-role
                  operator: In
                  values: ["gate-service"]
      containers:
        - name: callback
          image: dshb/gate-v5-gray-callback:v1.0
          ports:
            - name: http
              containerPort: 9090
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
          env:
            - name: SERVER_PORT
              value: "9090"
            - name: SERVER_HOST
              value: "0.0.0.0"
            - name: GATE_BASE_URL
              value: "https://gate.svc:9090"
            - name: SHADOW_MIRROR_API
              value: "http://mirror-router.mirror-ns.svc:8080"
            - name: DRY_RUN
              value: "false"
            - name: LOG_LEVEL
              value: "INFO"
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
          volumeMounts:
            - name: audit-logs
              mountPath: /app/audit_logs
      volumes:
        - name: audit-logs
          persistentVolumeClaim:
            claimName: gate-audit-logs-pvc
```

### 15.2 Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gate-v5-gray-callback
  namespace: gate-ns
spec:
  selector:
    app: gate-v5-gray-callback
  ports:
    - name: http
      port: 9090
      targetPort: 9090
  type: ClusterIP
```

### 15.3 配置参数

| 参数 | 默认值 | 环境变量 | 说明 |
|------|--------|---------|------|
| `server_port` | 9090 | `SERVER_PORT` | HTTP 服务端口 |
| `server_host` | `0.0.0.0` | `SERVER_HOST` | HTTP 服务地址 |
| `gate_base_url` | `https://gate.svc:9090` | `GATE_BASE_URL` | Gate API 地址 |
| `shadow_mirror_api` | `http://mirror-router.mirror-ns.svc:8080` | `SHADOW_MIRROR_API` | 影子镜像 API |
| `dry_run` | `false` | `DRY_RUN` | 干运行模式 |
| `log_level` | `INFO` | `LOG_LEVEL` | 日志级别 |
| `audit_log_dir` | `audit_logs/` | `AUDIT_LOG_DIR` | 审计日志目录 |
| `event_dedup_window` | 60s | `DEDUP_WINDOW` | 事件去重窗口 |
| `event_retry_max` | 3 | `RETRY_MAX` | 最大重试次数 |

---

## 16. 附录

### 16.1 完整示例: ADVANCE 决策

```json
// 请求
{
  "event_id": "evt-001",
  "timestamp": "2026-10-17T10:00:00Z",
  "decision": "ADVANCE",
  "decision_reason": "G0 观测完成，准入 G1",
  "current_stage": "G0",
  "next_stage": "G1",
  "dep_001_status": "RECOVERED",
  "observe_hours_elapsed": 24.0,
  "observe_hours_required": 24.0,
  "faults_detected": [],
  "metrics_snapshot": {
    "p95_ms": 18.2,
    "p99_ms": 45.6,
    "error_rate": 0.0045
  }
}

// 响应
{
  "status": "PROCESSED",
  "event_id": "evt-001",
  "decision": "ADVANCE",
  "current_stage": "G0",
  "timestamp": "2026-10-17T10:00:01Z",
  "actions": {
    "gate_status": {
      "status": "OK",
      "old_status": "WARN",
      "new_status": "READY",
      "message": "Gate 状态已更新: WARN → READY"
    },
    "dep_probe": {
      "status": "OK",
      "action": "START",
      "message": "DEP 周期性巡检已启动"
    },
    "shadow_mirror": {
      "status": "OK",
      "action": "START",
      "message": "影子流量镜像已启动"
    },
    "sampling_rate": {
      "status": "OK",
      "old_rate": 10.0,
      "new_rate": 20.0,
      "message": "采样率已更新: 10.0% → 20.0%"
    }
  },
  "message": "灰度推进：启动巡检+镜像"
}
```

### 16.2 完整示例: ROLLBACK 决策

```json
// 请求
{
  "event_id": "evt-002",
  "timestamp": "2026-10-17T12:00:00Z",
  "decision": "ROLLBACK",
  "decision_reason": "触发 F1 (链路级)",
  "current_stage": "G1",
  "faults_detected": ["F1"],
  "all_faults": [
    {
      "id": "F1",
      "name": "链路级",
      "severity": "FATAL",
      "auto_rollback": true
    }
  ],
  "metrics_snapshot": {
    "http_500_count": 5,
    "error_rate": 0.05
  }
}

// 响应
{
  "status": "PROCESSED",
  "event_id": "evt-002",
  "decision": "ROLLBACK",
  "current_stage": "G1",
  "timestamp": "2026-10-17T12:00:01Z",
  "actions": {
    "gate_status": {
      "status": "OK",
      "old_status": "READY",
      "new_status": "NOT_READY",
      "message": "Gate 状态已更新: READY → NOT_READY"
    },
    "dep_probe": {
      "status": "OK",
      "action": "STOP",
      "message": "DEP 周期性巡检已停止"
    },
    "shadow_mirror": {
      "status": "OK",
      "action": "STOP",
      "message": "影子流量镜像已停止"
    }
  },
  "message": "灰度回滚：停止巡检+镜像"
}
```

### 16.3 版本信息

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| V1.0 | 2026-10-17 | 初始版本，Gate V5 灰度决策回调接口规范 | DSHB 底层团队 |

### 16.4 关联文档

| 文档 | 路径 |
|------|------|
| G0 影子路由配置规范 | `v86_rc2_dshb_g0_shadow_route_config_spec.md` |
| DEP-001 流量镜像验证报告 | `v86_rc2_dshb_dep001_traffic_mirror_verify_report.md` |
| 影子环境隔离审计报告 | `v86_rc2_dshb_shadow_env_isolation_audit.md` |
| Gate V5 适配规范 V2.0 | `v86_rc2_dshb_gate_prod_adapt_spec_update.md` |
| HERMES 灰度判定脚本 | `gray_gate_decider.py` |
