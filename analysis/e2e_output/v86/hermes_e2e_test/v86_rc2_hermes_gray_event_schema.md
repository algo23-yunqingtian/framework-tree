# V86-RC2 灰度决策事件Schema规范（T3.2）

> **载体**: `gray_gate_event_persist.py`
> **分支**: `feature/v85-chart-template` @ `5ade5a2`
> **版本**: 1.0
> **日期**: 2026-10-15

---

## 1. Schema总览

```
gray_gate_events 表
├── event_id         TEXT PK    - 事件唯一ID (MD5: run_id|timestamp|decision)
├── timestamp        TEXT       - ISO8601 UTC (2026-10-15T16:00:00Z)
├── event_type       TEXT       - DECISION / HEALTHCHECK / ALERT
├── decision         TEXT       - ADVANCE / HOLD / OBSERVE / ROLLBACK / COMPLETE
├── decision_reason  TEXT       - 决策理由 (中文)
├── current_stage    TEXT       - 当前灰度阶段 (G0-G5)
├── next_stage       TEXT NULL  - 下一阶段 (仅ADVANCE非空)
├── dep_001_status   TEXT       - DEP状态 (BLOCKED/RECOVERED)
├── gate_status      TEXT       - Gate状态 (ACTIVE/GATE_REVIEW_PAUSED=TRUE)
├── risk_level       TEXT       - LOW / MEDIUM / HIGH / FATAL
├── faults           JSON       - 故障列表 ["F1","F2",...]
├── auto_rollback    TEXT       - "True"/"False"
├── need_confirm     TEXT       - "True"/"False"
├── rollback_timeout TEXT       - "0秒"/"30分钟"/"8小时"/...
├── rollback_scope   TEXT       - "全部品种"/"当前阶段"
├── flags_to_set     JSON       - ["GATE_REVIEW_PAUSED=TRUE",...]
├── all_faults       JSON       - 全部故障详情
├── gaps             JSON       - 准入缺口项 (仅HOLD)
├── remaining_hours  REAL NULL  - 剩余观测时间
├── input_state      JSON NULL  - 决策输入状态快照
├── schema_version   TEXT       - "1.0"
└── run_id           TEXT       - 运行批次ID
```

---

## 2. 决策类型与风险等级映射

| decision | risk_level | 触发条件 | 示例 |
|----------|-----------|----------|------|
| ADVANCE | LOW | 观测完成+准入通过 | G1→G2 |
| HOLD | MEDIUM | 准入未通过/DEP未就绪 | DEP BLOCKED |
| OBSERVE | LOW | 观测期未满 | 10/24h |
| ROLLBACK | FATAL/HIGH/MEDIUM | 故障触发 | F1=FATAL |
| COMPLETE | LOW | G5观测完成 | 全量完成 |

---

## 3. 故障风险映射

| 故障 | risk_level | 自动回滚 | 人工确认 | 超时 |
|------|-----------|----------|----------|------|
| F1 | FATAL | ✅ | ❌ | 0秒 |
| F2 | HIGH | ✅ | ✅ | 30分钟 |
| F3 | HIGH | ❌ | ✅ | 8小时 |
| F4 | MEDIUM | ❌ | ✅ | 2小时 |
| F5 | MEDIUM | ❌ | ✅ | 1小时 |

---

## 4. DSHE消费契约

DSHE聚合大盘按以下契约消费：

### 4.1 实时读取

```sql
-- 最新事件(倒序)
SELECT * FROM gray_gate_events ORDER BY timestamp DESC LIMIT 10;

-- 按决策类型过滤
SELECT * FROM gray_gate_events WHERE decision = 'ROLLBACK';

-- 按风险等级过滤
SELECT * FROM gray_gate_events WHERE risk_level IN ('HIGH', 'FATAL');

-- 按阶段过滤
SELECT * FROM gray_gate_events WHERE current_stage = 'G2';
```

### 4.2 字段对齐

| DSHE字段 | 本模块字段 | 对齐 |
|----------|-----------|------|
| event_id | event_id | ✅ |
| timestamp | timestamp | ✅ |
| decision | decision | ✅ |
| risk | risk_level | ✅ |
| stage | current_stage | ✅ |
| dep_status | dep_001_status | ✅ |
| faults | faults | ✅ |

### 4.3 时序保证

- `timestamp`严格递增（UTC）
- `event_id`唯一（MD5去重）
- WAL模式保证事务一致性
- 查询按`timestamp DESC`倒序

---

## 5. 事件类型

### DECISION事件
每次`gray_gate_decider.decide()`调用后产生。包含完整决策上下文。

### HEALTHCHECK事件
DEP健康状态变化时产生。用于追踪DEP状态历史。

### ALERT事件
CRITICAL/HIGH告警触发时产生。关联故障ID。

---

## 6. 集成示例

```python
from gray_gate_event_persist import GrayEventPersistor, persist_decision
from gray_gate_decider import decide

# 方式1: 直接持久化
p = GrayEventPersistor('/data/gray_events.db')
result = decide(state)
event_id = p.record_decision(result, state)
p.close()

# 方式2: 包装函数自动持久化
result, event_id = persist_decision(decide, state, '/data/gray_events.db')

# 方式3: 健康检查
p = GrayEventPersistor('/data/gray_events.db')
p.record_healthcheck(state, run_id='HC-001')
p.close()
```

---

## 7. 自检结果

10/10 PASS：ADVANCE/ROLLBACK/OBSERVE/HOLD四类决策持久化 + HEALTHCHECK/ALERT事件 + 查询/总数/schema验证。

---

*本规范为gray_gate_event_persist.py的事件Schema文档。Schema版本1.0，与DSHE聚合大盘消费契约对齐。*
