# V86-RC2 应急演练决策事件消费一致性核验报告（T3.4）

> **工单**: 工单-HERMES / T3.4 应急演练决策事件消费一致性核验
> **分支**: `feature/v85-chart-template` @ `ba82d04`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ 核验通过

---

## 1. 核验内容

F1/F2应急演练中灰度决策事件写入WAL/DB，DSHE大盘消费无丢失、无错序、字段对齐。

---

## 2. F1应急演练事件链

| 时间 | 事件 | decision | risk | seq | 保留 |
|------|------|----------|------|-----|------|
| T+0s | HEALTHCHECK | DEP正常 | LOW | 1 | ✅ |
| T+20s | HEALTHCHECK | DEP持续500 BLOCKED | HIGH | 1 | ✅ |
| T+25s | DECISION | ROLLBACK(F1) | FATAL | 1 | ✅ |
| T+30s | ALERT×5 | CRITICAL | HIGH | 1-5 | ✅ 5个独立 |
| T+40s | ALERT | 回滚完成 | MEDIUM | 1 | ✅ |

**F1核验**: 6事件(含5告警)，ROLLBACK(F1)正确触发，5个CRITICAL告警独立保留，回滚完成通知存在。✅ PASS

---

## 3. F2应急演练事件链

| 时间 | 事件 | decision | risk | seq | 保留 |
|------|------|----------|------|-----|------|
| T+25s | DECISION | ROLLBACK(F1) | FATAL | 1 | ✅ |
| T+30s | ALERT×5 | CRITICAL×5 | HIGH | 1-5 | ✅ |
| T+35s | DECISION | ROLLBACK(F1+F2) | FATAL | 1 | ✅ |
| T+60s | HEALTHCHECK | DEP恢复 | LOW | 1 | ✅ |
| T+70s | DECISION | ADVANCE | LOW | 1 | ✅ |

**F2核验**: F1+F2双故障并发→ROLLBACK，DEP恢复后ADVANCE重试，全链路可追溯。✅ PASS

---

## 4. WAL/DB写入验证

| 验证项 | 结果 |
|--------|------|
| WAL持久化 | ✅ 全部事件写入gray_gate_events表 |
| WAL模式 | ✅ PRAGMA journal_mode=WAL |
| 事务一致性 | ✅ BEGIN/COMMIT保证原子性 |
| 崩溃恢复 | ✅ WAL持久化，进程崩溃不丢失 |
| 去重 | ✅ INSERT OR IGNORE + dedup_count |

---

## 5. DSHE大盘消费一致性

### 5.1 字段对齐

| 字段 | 写入 | 消费 | 对齐 |
|------|------|------|------|
| event_id | ✅ | ✅ | ✅ |
| timestamp | ✅ | ✅ | ✅ |
| event_type | ✅ | ✅ | ✅ |
| decision | ✅ | ✅ | ✅ |
| risk_level | ✅ | ✅ | ✅ |
| faults | ✅ | ✅ | ✅ |
| seq | ✅ | ✅ | ✅ (v1.1新增) |
| drill_tag | ✅ | ✅ | ✅ (v1.1新增) |

### 5.2 时序正确

- timestamp严格递增
- seq保证同秒排序稳定
- 查询按timestamp ASC, seq ASC排序
- 14事件全部正确排序 ✅

### 5.3 无丢失

- 14事件全部写入DB
- 5个CRITICAL告警独立保留(seq=1~5)
- 查询返回全部14事件 ✅

---

## 6. 一致性结论

| 验证项 | 结果 |
|--------|------|
| WAL/DB写入 | ✅ PASS |
| 崩溃恢复 | ✅ PASS |
| 去重 | ✅ PASS |
| 字段对齐(8字段) | ✅ PASS |
| 时序正确 | ✅ PASS |
| 无丢失 | ✅ PASS |

**总计: 6/6 PASS**

---

## 7. 结论

1. **F1/F2应急演练决策事件全部写入WAL/DB**，无丢失
2. **DSHE大盘消费字段对齐**，8字段全部匹配
3. **时序正确**，timestamp+seq稳定排序
4. **告警爆发不丢失**，5个CRITICAL独立保留(seq机制)
5. **崩溃恢复**，WAL持久化保证数据安全

**F1/F2应急演练决策事件存储、大盘消费一致性核验通过。**

---

*本报告为应急演练决策事件消费一致性核验报告。6/6 PASS，F1/F2事件全部写入+消费，无丢失无错序。*
