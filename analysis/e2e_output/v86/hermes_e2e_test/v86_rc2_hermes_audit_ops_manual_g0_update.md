# V86-RC2 HERMES审计运维手册 — G0影子投产章节（T3.5）

> **工单**: 工单-HERMES / T3.5 审计运维文档更新
> **分支**: `feature/v85-chart-template` @ `5ade5a2`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ G0章节更新完成

---

## 1. G0影子压测指标阈值

### 1.1 审计器吞吐阈值

| 指标 | 实测 | 阈值 | 评价 |
|------|------|------|------|
| 审计吞吐 | 105.1 ev/s (256call/包) | ≥50 ev/s | ✅ 2.1x |
| 审计P50 | 8.985ms | ≤15ms | ✅ |
| 审计P99 | 25.429ms | ≤50ms | ✅ |
| 审计MAX | 26.238ms | ≤100ms | ✅ |
| 审计总时间 | 9.51s/1000包 | ≤30s/1000包 | ✅ |

### 1.2 WAL写入阈值

| 指标 | 实测 | 阈值 | 评价 |
|------|------|------|------|
| WAL写入吞吐 | 78,015 ev/s | ≥50,000 ev/s | ✅ 1.56x |
| 批均耗时 | 12.82ms/1000条 | ≤1000ms/1000条 | ✅ |
| P50批次 | 14.81ms | ≤50ms | ✅ |
| P99批次 | 19.64ms | ≤100ms | ✅ |
| 丢包率 | 0.0000% | 0% | ✅ |
| 去重 | 生效 | 生效 | ✅ |

### 1.3 存储阈值

| 指标 | 实测 | 阈值 | 评价 |
|------|------|------|------|
| DB大小 | 3.27MB | ≤50MB | ✅ |
| WAL大小 | 0.72MB | ≤10MB | ✅ |
| 总存储 | 3.99MB | ≤60MB | ✅ |

---

## 2. 事件持久化存储规范

### 2.1 存储配置

```python
PRAGMA journal_mode=WAL
PRAGMA synchronous=NORMAL
PRAGMA cache_size=-4000  # 4MB
PRAGMA busy_timeout=5000
```

### 2.2 事件Schema (v1.0)

- **表**: `gray_gate_events`
- **字段**: 22个（见 `v86_rc2_hermes_gray_event_schema.md`）
- **索引**: 5个（decision/timestamp/risk/run_id/type）
- **存储**: SQLite WAL模式

### 2.3 事件类型

| 类型 | 说明 | 触发 |
|------|------|------|
| DECISION | 灰度决策 | 每次decide() |
| HEALTHCHECK | DEP健康 | 状态变化 |
| ALERT | 告警 | CRITICAL/HIGH |

---

## 3. 事件追溯查询指南

### 3.1 快速查询

```bash
# 最近10条事件
sqlite3 gray_gate_events.db \
  "SELECT timestamp, decision, risk_level, current_stage, decision_reason FROM gray_gate_events ORDER BY timestamp DESC LIMIT 10;"

# 最近24小时全部事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE timestamp > datetime('now', '-24 hours') ORDER BY timestamp;"

# 所有ROLLBACK事件
sqlite3 gray_gate_events.db \
  "SELECT timestamp, decision_reason, faults, risk_level FROM gray_gate_events WHERE decision='ROLLBACK';"

# 风险等级分布
sqlite3 gray_gate_events.db \
  "SELECT risk_level, COUNT(*) FROM gray_gate_events GROUP BY risk_level;"
```

### 3.2 故障回溯步骤

```
Step 1: 找到ROLLBACK事件 → SELECT * WHERE decision='ROLLBACK' ORDER BY timestamp DESC
Step 2: 找到触发前DEP状态 → SELECT * WHERE timestamp < ROLLBACK时间 AND event_type='HEALTHCHECK'
Step 3: 找到相关告警 → SELECT * WHERE timestamp > ROLLBACK前1h AND risk_level IN ('HIGH','FATAL')
Step 4: 串联事件链 → 按timestamp ASC排序输出
```

### 3.3 运维操作

```bash
# 导出追溯日志
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, decision_reason FROM gray_gate_events ORDER BY timestamp DESC LIMIT 1000;" \
  > trace_export.json

# 清理旧事件(保留30天)
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE timestamp < datetime('now', '-30 days');"

# 数据库完整性检查
sqlite3 gray_gate_events.db "PRAGMA integrity_check;"

# checkpoint
sqlite3 gray_gate_events.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

---

## 4. G0影子投产流程

```
1. DEP-001 RECOVERED确认
   ├─ zhiji_api.py series j25_tc → HTTP 200
   ├─ zhiji_api.py series i1 → HTTP 200
   └─ zhiji_api.py series i2 → HTTP 200

2. V4准入扫描
   ├─ python3 prod_checklist_v4_scanner.py
   └─ Gate判定: READY(61/66 P0通过+5DEP预期FAIL→DEP恢复后全PASS)

3. 灰度判定
   ├─ gray_gate_decider.decide(state)
   ├─ 决策: ADVANCE(G0→G1)
   └─ 持久化: gray_gate_event_persist.record_decision()

4. DSHE消费
   ├─ gray_gate_events.db实时读取
   ├─ 字段对齐(22字段)
   └─ 时序正确

5. 观测期
   ├─ G0: 24小时观测
   ├─ 非零率≥95%
   └─ p95≤50ms
```

---

## 5. 关键文件索引

| 文件 | 用途 |
|------|------|
| `evidence_auditor_v3.py` | 审计器(54/54 self-test) |
| `gray_gate_decider.py` | 灰度判定(12/12 self-test) |
| `gray_gate_event_persist.py` | 事件持久化(10/10 self-test) |
| `event_store_wal_v2.py` | WAL事件存储 |
| `prod_checklist_v4_scanner.py` | V4准入扫描(7/7 self-test) |
| `v86_rc2_hermes_gray_event_schema.md` | 事件Schema规范 |
| `v86_rc2_hermes_prod_audit_trace_spec.md` | 追溯查询规范 |

---

## 6. 自检命令

```bash
# 审计器
python3 evidence_auditor_v3.py --self-test        # 期望54/54

# 灰度判定
python3 gray_gate_decider.py --self-test           # 期望12/12

# 事件持久化
python3 gray_gate_event_persist.py --self-test     # 期望10/10

# V4扫描器
python3 prod_checklist_v4_scanner.py --self-test   # 期望7/7

# 一键全量
for f in evidence_auditor_v3.py gray_gate_decider.py gray_gate_event_persist.py prod_checklist_v4_scanner.py; do
  echo "=== $f ==="
  python3 $f --self-test 2>&1 | tail -3
done
```

---

*本手册为HERMES审计运维手册G0章节。包含G0影子压测阈值、事件持久化规范、追溯查询指南、G0投产流程、自检命令。*
