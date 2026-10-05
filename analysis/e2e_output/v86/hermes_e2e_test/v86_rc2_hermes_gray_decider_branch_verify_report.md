# V86-RC2 gray_gate_decider 全故障分支专项验证报告（T3.1）

> **工单**: 工单-HERMES / T3.1 gray_gate_decider全故障分支专项验证
> **分支**: `feature/v85-chart-template` @ `629ccb7`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ 10/10 PASS

---

## 1. 验证场景与结果

| # | 场景 | 输入特征 | 期望 | 实测 | 故障 | 结果 |
|---|------|----------|------|------|------|------|
| S01 | DEP健康 | G1观测完成,非零率98%,p95=15ms | ADVANCE | ADVANCE | — | ✅ PASS |
| S02 | DEP持续500 | HTTP500×8+对照组失败 | ROLLBACK | ROLLBACK | F1 | ✅ PASS |
| S03 | DEP间歇抖动 | flap×4+断连×6 | ROLLBACK | ROLLBACK | F5 | ✅ PASS |
| S04 | DEP恢复 | G3观测完成,非零率99.5% | ADVANCE | ADVANCE | — | ✅ PASS |
| S05 | 审计性能超限 | p95=250ms+吞吐降60% | ROLLBACK | ROLLBACK | F4 | ✅ PASS |
| S06 | CRITICAL爆发 | critical_alerts=5 | ROLLBACK | ROLLBACK | F2 | ✅ PASS |
| S07 | 多故障并发 | F2+F4+F5并发 | ROLLBACK(F2) | ROLLBACK(F2) | F2 | ✅ PASS |
| S08 | G0影子期500 | G0+HTTP500×6+对照组失败 | ROLLBACK | ROLLBACK | F1 | ✅ PASS |
| S09 | Gate未通过 | gate_g06_pass=False | ROLLBACK | ROLLBACK | F3 | ✅ PASS |
| S10 | 观测期未满 | G2,12/24h | OBSERVE | OBSERVE | — | ✅ PASS |

**总计: 10/10 PASS**

---

## 2. F1-F5回滚矩阵匹配验证

| 故障 | 触发条件 | 期望行为 | 实测行为 | 匹配 |
|------|----------|----------|----------|------|
| F1 | HTTP500×5+对照组失败 | 自动0秒回滚,全部品种 | S02/S08: auto_rollback=True,timeout=0秒 | ✅ |
| F2 | CRITICAL>0 | 自动30分钟确认回滚 | S06: auto=True,confirm=True,30分钟 | ✅ |
| F3 | G-06未通过 | 人工确认8小时 | S09: auto=False,confirm=True,8小时 | ✅ |
| F4 | 吞吐降>50%/p95>200ms | 人工确认2小时 | S05: auto=False,confirm=True,2小时 | ✅ |
| F5 | DEP抖动≥3/断连>5 | 人工确认1小时 | S03: auto=False,confirm=True,1小时 | ✅ |

---

## 3. 多故障优先级验证

S07测试F2+F4+F5并发：
- 期望: 取最严重故障F2（优先级F1>F2>F3>F4>F5）
- 实测: `fault=F2`
- ✅ **PASS**

---

## 4. G0影子期特殊验证

S08: G0影子期DEP持续500
- 期望: G0不豁免F1链路级故障，仍应ROLLBACK
- 实测: ROLLBACK(F1)
- ✅ **PASS** — G0影子期不影响F1链路级判定

---

## 5. 结论

1. **10/10 PASS**: 全部故障分支验证通过
2. **F1-F5回滚矩阵匹配**: 5类故障触发条件、回滚行为、超时、范围全部对齐
3. **多故障优先级正确**: 取最严重故障
4. **G0不豁免F1**: 影子期链路故障仍ROLLBACK
5. **无逻辑偏差**: 脚本输出与回滚矩阵完全一致

---

*本报告为gray_gate_decider.py全故障分支专项验证报告。10/10 PASS，脚本输出与F1-F5回滚矩阵完全匹配。*
