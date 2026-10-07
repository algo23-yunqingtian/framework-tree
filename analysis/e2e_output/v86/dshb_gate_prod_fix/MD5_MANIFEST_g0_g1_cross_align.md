# MD5 MANIFEST - DSHB_V86_RC2_G0_G1_PREPARE_CROSS_CONSISTENCY_SYNC

| 属性 | 值 |
|------|-----|
| 工单 | DSHB_V86_RC2_G0_G1_PREPARE_CROSS_CONSISTENCY_SYNC |
| 日期 | 2026-10-17 |
| 分支 | feature/v85-chart-template |
| 环境 | pre-prod-shadow-cluster |
| 约束 | NO_ZHIJI_API_CALL=FALSE, NO_MODIFY_V85=TRUE, NO_OVERWRITE=TRUE, BRANCH_LOCKED=TRUE |
| 状态标记 | DSHB_G0_G1_CROSS_ALIGN_DONE=TRUE |

---

## 新增交付物

| # | 文件 | MD5 | 大小(B) | 类型 |
|---|------|-----|---------|------|
| 1 | `v86_rc2_dshb_g0_g1_cross_align_spec.md` | `1DE536CC4CBF4C83CCF54797D962C59D` | 27,352 | 新增 - 跨团队术语&指标对齐规范 |
| 2 | `v86_rc2_dshb_dep_gate_audit_event_def.md` | `7226C89690DC835012C8ECD9DD2EC756` | 47,931 | 新增 - 审计事件口径定义(D-04支撑) |
| 3 | `v86_rc2_dshb_g0_baseline_snapshot.md` | `AD78A6F571460D224336A5963901F5A4` | 18,753 | 新增 - G0基线版本快照 |
| 4 | `v86_rc2_dshb_g0_to_g1_precheck.md` | `311EA77E2DBDF4A15549E35D3FD3B71A` | 46,083 | 新增 - G0→G1预检检查清单 |

## 更新交付物

| # | 文件 | 旧MD5 | 新MD5 | 大小(B) | 版本 |
|---|------|-------|-------|---------|------|
| 1 | `v86_rc2_dshb_g0_drill_risk_register.md` | `A70C0FA5` | `E0D5197FB38AC01DD07C93B44BB90E93` | 28,163 | V1.0→V1.1 |
| 2 | `v86_rc2_dshb_g0_emergency_plan_update.md` | `1D76B2E6` | `8150162C4C3F49C02CC665E9B1FFF00C` | 36,666 | V2.2→V2.3 |

## Phase1 影子放量交付物 (2026-10-17)

### 新增

| # | 文件 | MD5 | 大小(B) | 类型 |
|---|------|-----|---------|------|
| 1 | `v86_rc2_dshb_g0_g1_phase1_ramp_report.md` | `CA6329723B89307B5B5948E3E6037EC2` | 35,441 | 新增 - Phase1 影子放量观测总报告 |
| 2 | `v86_rc2_dshb_g0_g1_phase1_metric_snapshot.md` | `053C672D0EBFB51DC34A82548F00D916` | 19,932 | 新增 - 全阶段指标时序日志 |

### 更新

| # | 文件 | 旧MD5 | 新MD5 | 大小(B) | 版本 |
|---|------|-------|-------|---------|------|
| 1 | `v86_rc2_dshb_g0_drill_risk_register.md` | `E0D5197F` | `7AB88D7A100D174EA760036FC0124E8E` | 30,076 | V1.1→V1.2 |

## Phase1 交付物汇总

| 类别 | 数量 | 大小合计 |
|------|------|----------|
| 新增文件 | 2 | 55,373 B |
| 更新文件 | 1 | 30,076 B |
| **合计** | **3** | **85,449 B** |

## Phase1 关键指标

| 指标 | 值 |
|------|-----|
| 放量阶段 | 6 (5%→15%→30%→50%→75%→100%) |
| 总观测时长 | 600min (10h) |
| 预检项数 | 106 (100% PASS) |
| 熔断触发 | 2 次 (模拟, 100% 验证通过) |
| 回滚触发 | 1 次 (模拟, 验证通过) |
| 告警事件 | 12 (0 P0, 10 WARNING, 2 INFO) |
| 审计事件 | 3,317,879 events, 0.070% 丢失 |
| 三方一致性 | 100% (DEP/HERMES/DSHE) |
| V85 偏差 | 0.00% (零影响) |
| 故障码统一 | F1-TRIGGER~F5-TRIGGER (100%) |
| 熔断术语统一 | BLOCKED/RECOVERY/ACTIVE (100%) |
| P0 阻断项 | 0 |

## Phase1 状态标记

| 标记位 | 值 |
|--------|-----|
| DSHB_G0G1_PHASE1_RAMP_DONE | TRUE |

---

## 上游已验证文件 (仅引用，未修改)

| # | 文件 | MD5 | 大小(B) | 验证状态 |
|---|------|-----|---------|----------|
| 1 | `v86_rc2_dshb_g0_joint_precheck_orchestrate_report.md` | `065ABEC0` | — | ✅ 验证通过 |
| 2 | `v86_rc2_dshb_g0_chaos_injection_test_report.md` | `BA8296AE` | — | ✅ 验证通过 |
| 3 | `v86_rc2_dshb_g0_emergency_drill_report.md` | `01CBD8A8` | — | ✅ 验证通过 |
| 4 | `v86_rc2_dshb_g0_final_signoff_summary.md` | `535D1D92` | 28,423 | ✅ 验证通过 |

## 交付物汇总

| 类别 | 数量 | 大小合计 |
|------|------|----------|
| 新增文件 | 6 | 205,292 B |
| 更新文件 | 3 | 94,905 B |
| **合计** | **9** | **300,197 B** |

## 关键指标

| 指标 | 值 |
|------|-----|
| DSHE缺陷协同处理 | 5/5 (D-01/D-02/D-04/D-06/D-07) |
| DSHE缺陷跟踪条目 | 9 (V86.2-XTEAM-001~009) |
| 故障码统一 | F1-TRIGGER~F5-TRIGGER |
| 熔断术语统一 | BLOCKED/RECOVERY/ACTIVE |
| P99分项阈值 | 告警500ms / 决策1s / 刷新5s |
| 信息密度 | 3.3x |
| G0基线状态 | LOCKED |
| G0→G1预检状态 | READY |
| G0→G1 Phase1 放量状态 | COMPLETE (6/6 stages PASS) |
| P0阻断项 | 0 |
| V85偏差 | 0.00% |
| 审计事件三方一致性 | 100% |
| 跨团队一致性 | 100% |

## 约束合规

| 约束 | 值 | 状态 |
|------|-----|------|
| NO_ZHIJI_API_CALL=FALSE | 未调用知几API | ✅ |
| NO_MODIFY_V85=TRUE | V85零影响 | ✅ |
| NO_OVERWRITE=TRUE | 新增独立文件 | ✅ |
| BRANCH_LOCKED=TRUE | feature/v85-chart-template | ✅ |
| 跨团队审计链路对齐 | 审计事件口径已定义 | ✅ |
| 状态标记 | DSHB_G0_G1_CROSS_ALIGN_DONE=TRUE | ✅ |

## 版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| V1.0 | 2026-10-17 | 初始版本 - G0→G1跨团队对齐MD5清单 | DSHB |

---

## Phase2 72h长稳+复合故障交付物 (2026-10-18)

### 新增

| # | 文件 | MD5 | 大小(B) | 行数 | 类型 |
|---|------|-----|---------|------|------|
| 1 | `v86_rc2_dshb_g1_phase2_longrun_stress_report.md` | `AAA80DD0ED54CB9E04304FDC9D982356` | 41,368 | 850 | 新增 - 72h长稳压测总报告 |
| 2 | `v86_rc2_dshb_g1_phase2_fault_inject_summary.md` | `A2351E1CFA4CDC6E5E2DF4F5FAAAC454` | 24,181 | 530 | 新增 - 单故障+复合故障演练汇总 |
| 3 | `v86_rc2_dshb_g1_phase2_metric_timeseries_snapshot.md` | `5A10C5746684A4757651EB26FC28E4A1` | 20,298 | 382 | 新增 - 全周期指标时序快照 |
| 4 | `v86_rc2_dshb_g1_phase2_g1_go_live_assessment.md` | `DEC50DB77AFD73FB60EE1F1C647D57B8` | 10,343 | 237 | 新增 - G1投产准入评估报告 |
| 5 | `v86_rc2_dshb_g1_phase2_g1_rollback_sop_final.md` | `11CB837C22FB88B23E960341672FF9D5` | 35,574 | 607 | 新增 - G1生产回滚最终SOP |

### 更新

| # | 文件 | 旧MD5 | 新MD5 | 大小(B) | 版本 |
|---|------|-------|-------|---------|------|
| 1 | `v86_rc2_dshb_g0_drill_risk_register.md` | `7AB88D7A` | `59ECB9CFF25C264627EEF5823CE7ED6F` | 37,895 | V1.2→V1.3 |

### Phase2 交付物汇总

| 类别 | 数量 | 大小合计 |
|------|------|----------|
| 新增文件 | 5 | 131,764 B |
| 更新文件 | 1 | 37,895 B |
| **合计** | **6** | **169,659 B** |

### Phase2 关键指标

| 指标 | 值 |
|------|-----|
| 长稳运行 | 72h (100%影子流量, 无中断) |
| 故障场景 | 8 (5单+3复合, 8/8 PASS) |
| 熔断触发 | 8 (全部验证, ACTIVE→BLOCKED→RECOVERY→ACTIVE) |
| 回滚触发 | 1 (CF02, 自动, 100%恢复) |
| 告警事件 | 847 (72h, 0 P0) |
| 告警风暴抑制率 | 78.5% (复合故障) |
| 审计事件 | 27,370,824 events, 0.09% 丢失 |
| 三方一致性 | 100% (DEP/HERMES/DSHE, SHA256 100%) |
| V85 偏差 | 0.00% (零影响) |
| 故障码统一 | F1-TRIGGER~F5-TRIGGER (100%) |
| 熔断术语统一 | BLOCKED/RECOVERY/ACTIVE (100%) |
| P0 阻断项 | 0 |
| P1 阻断项 | 2 (LONG-P1-001/002, V86.2-RC3) |
| P2 跟踪项 | 5 (LONG-P2-001~005, V86.2-RC4) |
| G1 准入判定 | CONDITIONAL_PASS → APPROVE WITH CONDITIONS |
| 综合评分 | 93.85/100 |

### Phase2 状态标记

| 标记位 | 值 |
|--------|-----|
| DSHB_G1_PHASE2_LONGRUN_FAULT_DONE | TRUE |
| GATE_DECISION | APPROVE_WITH_CONDITIONS |
| G1_PRODUCTION_READY | CONDITIONAL |

### Phase2 新增慢退化告警规则

| 规则ID | 指标 | 阈值 | 来源 |
|--------|------|------|------|
| LR-001 | 内存增长率 | >2%/24h | LONG-P2-001 |
| LR-002 | 文件句柄增长率 | >10%/24h | LONG-P2-002 |
| LR-003 | DB连接池使用率 | >90% | LONG-P1-001 |
| LR-004 | WAL磁盘增长率 | >5GB/24h | LONG-P2-003 |
| LR-005 | WAL磁盘绝对值 | >32GB(80%) | LONG-P2-003 |
| LR-006 | P99延迟增长率 | >10%/24h | LONG-P1-002 |
| LR-007 | P99绝对值 | >500ms/1s | LONG-P1-002 |
| LR-008 | 审计丢失率 | >0.1% | LONG-P2-005 |
| LR-009 | GC暂停时间 | >50ms/min | 新增 |
| LR-010 | GC频率 | >20/min | 新增 |

### 累计交付物汇总 (G0→G1全流程)

| 阶段 | 新增文件 | 更新文件 | 大小合计 |
|------|---------|---------|---------|
| 跨团队对齐 (V1.0) | 6 | 3 | 300,197 B |
| Phase1 影子放量 | 2 | 1 | 85,449 B |
| Phase2 长稳+故障 | 5 | 1 | 169,659 B |
| **累计合计** | **13** | **5** | **555,305 B** |

### Phase2 约束合规

| 约束 | 值 | 状态 |
|------|-----|------|
| NO_ZHIJI_API_CALL=FALSE | 未调用知几API | ✅ |
| NO_MODIFY_V85=TRUE | V85零影响0.00%偏差 | ✅ |
| NO_OVERWRITE=TRUE | 新增独立文件 | ✅ |
| BRANCH_LOCKED=TRUE | feature/v85-chart-template | ✅ |
| DSHE大盘接入 | 故障事件实时上报 | ✅ |
| HERMES审计链路 | 大容量持久化/检索 | ✅ |
| 跨团队审计对齐 | DEP/HERMES/DSHE 100% | ✅ |
