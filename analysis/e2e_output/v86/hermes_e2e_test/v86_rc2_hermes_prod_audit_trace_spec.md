# V86-RC2 投产全链路事件审计追溯规范（T3.3）

> **工单**: 工单-HERMES / T3.3 投产全链路事件审计追溯日志构建
> **分支**: `feature/v85-chart-template` @ `5ade5a2`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15

---

## 1. 全链路事件模型

```
DEP健康事件 → Gate预检事件 → 灰度决策事件 → 告警事件
     │            │               │             │
     ▼            ▼               ▼             ▼
 DEP状态变化    Gate检查结果     ADVANCE/       CRITICAL/
 BLOCKED/       PASS/FAIL       ROLLBACK/      HIGH告警
 RECOVERED                   OBSERVE/HOLD
```

### 1.1 事件类型定义

| 事件类型 | 来源 | 触发条件 | 关键字段 |
|----------|------|----------|----------|
| DEP_HEALTH | DEP服务 | 状态变化(BLOCKED↔RECOVERED) | dep_id, status, timestamp |
| GATE_CHECK | Gate预检 | Gate V5执行 | gate_result, checks, timestamp |
| GRAY_DECISION | 灰度判定 | 每次decide() | decision, stage, risk |
| ALERT | 审计器/告警 | CRITICAL/HIGH触发 | level, rule, message |

### 1.2 事件关联链

```
事件链: DEP_HEALTH(BLOCKED) → GATE_CHECK(FAIL) → GRAY_DECISION(ROLLBACK) → ALERT(CRITICAL)
```

通过以下键关联：
- `timestamp`: 时间戳严格递增
- `run_id`: 同批次共享
- `dep_id`: DEP-001标识
- `stage`: 灰度阶段

---

## 2. 追溯查询示例

### 2.1 按时间线追溯

```sql
-- 最近24小时全部事件
SELECT timestamp, event_type, decision, risk_level, current_stage,
       dep_001_status, decision_reason
FROM gray_gate_events
WHERE timestamp > datetime('now', '-24 hours')
ORDER BY timestamp ASC;
```

### 2.2 故障回溯

```sql
-- 回溯某次ROLLBACK的全链路
-- Step 1: 找到ROLLBACK事件
SELECT * FROM gray_gate_events WHERE decision = 'ROLLBACK' ORDER BY timestamp DESC LIMIT 1;

-- Step 2: 找到触发前的DEP状态
SELECT * FROM gray_gate_events
WHERE timestamp < 'ROLLBACK时间'
AND event_type = 'HEALTHCHECK'
ORDER BY timestamp DESC LIMIT 5;

-- Step 3: 找到相关告警
SELECT * FROM gray_gate_events
WHERE timestamp > 'ROLLBACK前1小时'
AND event_type = 'ALERT'
AND risk_level IN ('HIGH', 'FATAL')
ORDER BY timestamp ASC;
```

### 2.3 按阶段统计

```sql
-- 各阶段决策分布
SELECT current_stage, decision, COUNT(*) as cnt
FROM gray_gate_events
GROUP BY current_stage, decision;

-- 各阶段风险等级分布
SELECT current_stage, risk_level, COUNT(*) as cnt
FROM gray_gate_events
GROUP BY current_stage, risk_level;
```

---

## 3. 事件存储架构

```
gray_gate_events.db (SQLite WAL)
├── gray_gate_events 表
│   ├── DECISION事件 (4类: ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE)
│   ├── HEALTHCHECK事件 (DEP状态)
│   └── ALERT事件 (告警)
├── 索引
│   ├── idx_decision (按决策类型)
│   ├── idx_timestamp (按时间)
│   ├── idx_risk (按风险等级)
│   ├── idx_run_id (按批次)
│   └── idx_type (按事件类型)
└── 存储模式: WAL (持久化)
```

---

## 4. 追溯能力

| 能力 | 支持 | 查询方式 |
|------|------|----------|
| 按时间线 | ✅ | timestamp ASC/DESC |
| 按决策类型 | ✅ | decision = 'ROLLBACK' |
| 按风险等级 | ✅ | risk_level IN ('HIGH','FATAL') |
| 按阶段 | ✅ | current_stage = 'G2' |
| 按批次 | ✅ | run_id = 'RUN-xxx' |
| 按事件类型 | ✅ | event_type = 'HEALTHCHECK' |
| 故障回溯 | ✅ | 按时间线串联多事件 |
| DEP状态历史 | ✅ | event_type = 'HEALTHCHECK' |

---

## 5. 与DSHE L2面板对齐

| 追溯能力 | DSHE L2面板 | 本模块 |
|----------|-------------|--------|
| 实时事件流 | 聚合大盘 | gray_gate_events查询 |
| 阶段指示 | 灰度阶段条 | current_stage |
| 风险等级 | 红/黄/绿 | risk_level |
| 回滚记录 | 回滚历史 | decision='ROLLBACK' |
| DEP状态 | DEP指示灯 | dep_001_status |

---

## 6. 运维操作

### 6.1 导出追溯日志

```bash
# 导出最近1000条事件
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, decision_reason FROM gray_gate_events ORDER BY timestamp DESC LIMIT 1000;" \
  > trace_export.json
```

### 6.2 清理旧事件

```bash
# 保留最近30天
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE timestamp < datetime('now', '-30 days');"
```

---

*本规范为投产全链路事件审计追溯规范。支持按时间/决策类型/风险等级/阶段/批次/事件类型六维追溯，覆盖DEP→Gate→灰度决策→告警完整事件链。*
