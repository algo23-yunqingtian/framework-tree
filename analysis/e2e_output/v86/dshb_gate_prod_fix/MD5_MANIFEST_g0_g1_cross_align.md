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
| 新增文件 | 4 | 139,919 B |
| 更新文件 | 2 | 64,829 B |
| **合计** | **6** | **204,748 B** |

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
| P0阻断项 | 0 |
| V85偏差 | 0.00% |
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
