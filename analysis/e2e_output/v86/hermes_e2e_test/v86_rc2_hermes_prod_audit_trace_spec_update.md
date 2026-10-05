# V86-RC2 投产审计追溯规范 — 混沌故障场景更新（T3.5）

> **工单**: 工单-HERMES / T3.5 审计追溯文档更新
> **分支**: `feature/v85-chart-template` @ `ba82d04`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ 更新完成

---

## 1. 混沌故障场景检索示例

### 1.1 按演练标记查询

```bash
# 混沌演练全部事件
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, decision_reason, seq \
   FROM gray_gate_events WHERE drill_tag='chaos' \
   ORDER BY timestamp, seq;"

# 恢复演练事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE drill_tag='failover';"

# 正常生产事件(无演练标记)
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE drill_tag='normal';"
```

### 1.2 按事件来源查询

```bash
# HERMES审计事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE source='hermes';"

# DSHB来源事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE source='dshb';"

# DSHE来源事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE source='dshe';"
```

---

## 2. 故障回溯命令

### 2.1 F1链路故障回溯

```bash
# Step 1: 找到F1 ROLLBACK事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE decision='ROLLBACK' AND faults LIKE '%F1%' \
   ORDER BY timestamp DESC LIMIT 1;"

# Step 2: 找到触发前DEP状态(往前1小时)
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE event_type='HEALTHCHECK' \
   AND dep_001_status='BLOCKED' ORDER BY timestamp DESC LIMIT 10;"

# Step 3: 找到相关告警
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE event_type='ALERT' \
   AND risk_level='HIGH' ORDER BY timestamp DESC LIMIT 20;"

# Step 4: 串联事件链
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, seq, faults \
   FROM gray_gate_events WHERE run_id='CHAOS-DRILL-001' \
   ORDER BY timestamp, seq;"
```

### 2.2 F2告警爆发回溯

```bash
# 找到CRITICAL告警爆发
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE decision='CRITICAL' \
   AND risk_level='HIGH' ORDER BY timestamp, seq;"

# 找到F2 ROLLBACK事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE decision='ROLLBACK' \
   AND faults LIKE '%F2%' ORDER BY timestamp DESC LIMIT 5;"
```

---

## 3. 事件排查命令

### 3.1 告警统计

```bash
# 按风险等级统计
sqlite3 gray_gate_events.db \
  "SELECT risk_level, COUNT(*) FROM gray_gate_events \
   GROUP BY risk_level;"

# 按决策类型统计
sqlite3 gray_gate_events.db \
  "SELECT decision, COUNT(*) FROM gray_gate_events \
   GROUP BY decision;"

# 按事件类型统计
sqlite3 gray_gate_events.db \
  "SELECT event_type, COUNT(*) FROM gray_gate_events \
   GROUP BY event_type;"
```

### 3.2 重复投递检测

```bash
# 找到重复投递的事件(dedup_count > 1)
sqlite3 gray_gate_events.db \
  "SELECT event_id, timestamp, decision, dedup_count \
   FROM gray_gate_events WHERE dedup_count > 1;"
```

### 3.3 时序异常检测

```bash
# 检查timestamp是否递增(找乱序事件)
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, seq, \
   LAG(timestamp) OVER (ORDER BY timestamp) as prev_ts \
   FROM gray_gate_events \
   HAVING timestamp < prev_ts;"
```

### 3.4 完整性检查

```bash
# 数据库完整性
sqlite3 gray_gate_events.db "PRAGMA integrity_check;"

# 字段完整性(检查NULL)
sqlite3 gray_gate_events.db \
  "SELECT event_id, timestamp FROM gray_gate_events \
   WHERE timestamp IS NULL OR event_type IS NULL;"

# 事件类型完整性
sqlite3 gray_gate_events.db \
  "SELECT DISTINCT event_type FROM gray_gate_events;"
```

---

## 4. 混沌演练时间线模板

```
T+0s   HEALTHCHECK  DEP正常 RECOVERED  (LOW, seq=1)
T+5s   ALERT        Gate预检通过        (MEDIUM, seq=1)
T+10s  HEALTHCHECK  DEP抖动 flap=1      (LOW, seq=1)
T+20s  HEALTHCHECK  DEP持续500 BLOCKED  (HIGH, seq=1)
T+25s  DECISION     ROLLBACK(F1) FATAL (FATAL, seq=1)
T+30s  ALERT×5      CRITICAL告警爆发    (HIGH, seq=1-5)
T+35s  DECISION     ROLLBACK(F1+F2)    (FATAL, seq=1)
T+40s  ALERT        回滚完成            (MEDIUM, seq=1)
T+60s  HEALTHCHECK  DEP恢复 RECOVERED   (LOW, seq=1)
T+70s  DECISION     ADVANCE             (LOW, seq=1)
```

---

## 5. 运维操作补充

### 5.1 演练数据清理

```bash
# 清理混沌演练数据(保留生产数据)
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE drill_tag='chaos';"

# 清理恢复演练数据
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE drill_tag='failover';"

# 清理旧事件(保留30天)
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE timestamp < datetime('now', '-30 days');"
```

### 5.2 导出追溯日志

```bash
# 导出完整事件链(含演练标记)
sqlite3 -header -csv gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, \
   dep_001_status, faults, seq, source, drill_tag \
   FROM gray_gate_events ORDER BY timestamp, seq;" \
  > trace_export.csv
```

---

## 6. 版本更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-10-15 | 初始版本: 6维追溯 |
| v1.1 | 2026-10-15 | 追加混沌故障场景检索、事件排查命令、演练数据清理 |

---

*本规范为投产审计追溯规范更新版。追加混沌故障场景检索示例、故障回溯命令、事件排查命令、演练数据清理操作。*
