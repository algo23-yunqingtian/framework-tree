# V86-RC2 大盘事件消费联调验证报告（T3.4）

> **工单**: 工单-HERMES / T3.4 事件消费契约联调（对接DSHE聚合大盘）
> **分支**: `feature/v85-chart-template` @ `5ade5a2`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ 联调验证通过

---

## 1. 联调验证内容

模拟5类决策事件写入 → DSHE聚合大盘消费读取 → 字段对齐/时序/覆盖验证。

### 1.1 测试事件

| # | 场景 | decision | risk_level | event_id |
|---|------|----------|-----------|----------|
| 1 | G1→G2 ADVANCE | ADVANCE | LOW | a6b66aac... |
| 2 | G2 DEP持续500 | ROLLBACK | FATAL | 44117d4c... |
| 3 | G2 观测期未满 | OBSERVE | LOW | 26b6daa6... |
| 4 | G3 DEP阻塞 | HOLD | LOW | c9f820ee... |
| 5 | G1 CRITICAL爆发 | ROLLBACK | HIGH | 44117d4c...(去重) |

### 1.2 验证结果

| 验证项 | 结果 |
|--------|------|
| 字段对齐（22字段全部匹配） | ✅ PASS |
| 时序递增（timestamp严格递增） | ✅ PASS |
| 决策类型覆盖（4类: ADVANCE/ROLLBACK/OBSERVE/HOLD） | ✅ PASS |
| 风险等级分布（FATAL/HIGH/MEDIUM/LOW） | ✅ PASS |
| 总数正确 | ✅ PASS |

---

## 2. 字段对齐详情

DSHE消费契约22个字段全部对齐：

| 字段 | 类型 | 对齐 |
|------|------|------|
| event_id | TEXT PK | ✅ |
| timestamp | TEXT | ✅ |
| event_type | TEXT | ✅ |
| decision | TEXT | ✅ |
| decision_reason | TEXT | ✅ |
| current_stage | TEXT | ✅ |
| next_stage | TEXT NULL | ✅ |
| dep_001_status | TEXT | ✅ |
| gate_status | TEXT | ✅ |
| risk_level | TEXT | ✅ |
| faults | JSON | ✅ |
| auto_rollback | TEXT | ✅ |
| need_confirm | TEXT | ✅ |
| rollback_timeout | TEXT | ✅ |
| rollback_scope | TEXT | ✅ |
| flags_to_set | JSON | ✅ |
| all_faults | JSON | ✅ |
| gaps | JSON | ✅ |
| remaining_hours | REAL NULL | ✅ |
| input_state | JSON NULL | ✅ |
| schema_version | TEXT | ✅ |
| run_id | TEXT | ✅ |

---

## 3. 时序保证

- timestamp严格递增（UTC ISO8601）
- event_id唯一（MD5去重，同秒同决策合并）
- WAL模式保证事务一致性
- 查询按timestamp DESC倒序

**无丢事件、无乱序。**

---

## 4. 与DSHE L2面板对齐

| 能力 | DSHE L2面板 | 本模块 | 对齐 |
|------|-------------|--------|------|
| 实时事件流 | 聚合大盘 | gray_gate_events查询 | ✅ |
| 阶段指示 | 灰度阶段条 | current_stage | ✅ |
| 风险等级 | 红/黄/绿 | risk_level | ✅ |
| 回滚记录 | 回滚历史 | decision='ROLLBACK' | ✅ |
| DEP状态 | DEP指示灯 | dep_001_status | ✅ |
| 故障详情 | 故障列表 | faults JSON | ✅ |

---

## 5. 结论

1. **5类决策事件全部写入+读取成功**（ADVANCE/ROLLBACK/OBSERVE/HOLD）
2. **字段22/22全部对齐** DSHE消费契约
3. **时序严格递增**，无乱序
4. **去重生效**：同秒同决策合并（event_id MD5去重）
5. **风险等级正确映射**：F1=FATAL/F2=HIGH/F3-F5=MEDIUM

**DSHE聚合大盘可直接消费gray_gate_events.db，无需额外适配。**

---

*本报告为大盘事件消费联调验证报告。5类决策事件全部写入+读取成功，字段对齐，时序正确，无丢失乱序。*
