# V86 别名引擎 Gate 终审 v2 (CONDITIONAL_PASS 迭代版) — MD5 校验清单

> 任务: `DSHE_V86_ALIAS_GATE_RISK_MONITORING_ALIGNMENT_AND_FINAL_ARCHIVE` · T3.4
> 分支: `feature/v85-chart-template`
> 基线 Commit: `bcbb0e7`
> 资产版本: `v86.0.0-frozen`
> 生成时间: 2026-10-02

---

## V86 别名引擎 — Gate 终审 v2 产出 (dshe_alias_gate_final_v2)

| MD5 | 大小 (B) | 文件 |
|-----|----------|------|
| D9D88D7D2E16839C98BB7A993E69AF24 | 29,134 | `dshe_alias_gate_final_v2/v86_alias_risk_monitoring_review.md` |
| F866032755A4C96CA3AD238B6DF6CA74 | 31,715 | `dshe_alias_gate_final_v2/v86_alias_portal_caliber_second_review.md` |
| 47C2013534CA421262A4DA6D6B3F748D | 31,515 | `dshe_alias_gate_final_v2/v86_alias_gate_final_demo_v3.md` |
| 4FE8EBD6B9215A3F5020D43019B5D143 | 30,622 | `dshe_alias_gate_final_v2/v86_alias_final_archive_bundle_v2.md` |
| — | — | `dshe_alias_gate_final_v2/MD5_CHECKSUM_LIST_v2.md` (本文件) |

## 全局

| MD5 | 大小 (B) | 文件 |
|-----|----------|------|
| DEC8E371DFC53FD6869CEDD961086D7B | 11,222 | `JOB_READY.flag` |

---

## 校验命令

```bash
# 从 dshe_alias_gate_final_v2 目录验证
cd analysis/e2e_output/v86/dshe_alias_gate_final_v2
# 使用 MD5_CHECKSUM_LIST_v2.md 中的 MD5 列表
```

---

## 汇总

| 类别 | 文件数 | 总大小 |
|------|--------|--------|
| 风险监控覆盖度复核 | 1 | 29,134B |
| 门户口径二次复核 | 1 | 31,715B |
| CONDITIONAL_PASS 演示包 | 1 | 31,515B |
| 归档资产包 v2 | 1 | 30,622B |
| MD5 清单 | 1 | — |
| JOB_READY.flag | 1 | 11,222B |
| **总计** | **6** | **~134,208B** |

---

## 前置交付资产索引 (MD5)

| 资产 | MD5 | 文件 |
|------|-----|------|
| 门户偏差修复 | E29D7B1F3DDA4FFC83C0531C4BCC3A08 | `v86_alias_portal_deviation_fix_report.md` |
| Grafana 面板 | 0706108693FAC5DADAE4F047CC78B20B | `v86_alias_grafana_panels_final.md` |
| 口径终审 | 022CDDAC5F54F36674C44FE40D339716 | `v86_alias_caliber_final_audit.md` |
| 终审演示包 | 29242B40022C2D1F607C73F4952F20C1 | `v86_alias_gate_final_demo_package.md` |
| 归档资产包 v1 | 3D87DFE2AF99FF60A56E1D369B9A9DB3 | `v86_alias_final_archive_bundle.md` |
| MD5 清单 v1 | — | `MD5_CHECKSUM_LIST.md` |
| Gate 演示包 | F144F7E66017340C17F7E0C53838F12D | `v86_alias_gate_demo_package.md` |
| Release Note | 56771CA9E1D1680C4438818DF2F95E48 | `v86_alias_release_note_final.md` |
| Gate 问答知识库 | BD79A43B9B331E7DC357BE58634D1A4D | `v86_alias_gate_qakb.md` |
| 门户交叉核验 | E20C84994378121B35F78A58E90B6413 | `v86_alias_portal_data_cross_check.md` |
| 运维手册 | E1EFAA2C8A26FA08233784759C1614F2 | `v86_alias_ops_manual_final.md` |
| 灰度仿真 | 75487A8F1448C7DAE7A1C9E6936074E8 | `v86_alias_gray_full_simulation.md` |
| 集成校验 | C6273225803A593469122E90068B81EF | `v86_alias_prod_integrate_verify_report.md` |
| 仿真脚本 | 139C3A4C01ADD90536078759370F6324 | `gray_simulation_runner.py` |
| 仿真结果 | C584460D50C1D6D0AE16D8C7EC7C9AC9 | `gray_simulation_results.json` |
| 全量回放 | 421B93B765967E533496F7FFF53A18A6 | `v86_alias_full_replay.py` |
| 回放报告 | 016A79BE90D8D08A9ED4218E5A84C935 | `v86_alias_full_replay_report.md` |
| 生产部署包 | 054EAC866B350727BAFC15BBF36D4A46 | `v86_alias_production_bundle.md` |
| 灰度方案 | C2F029CC434DFF473D2542584517D5F3 | `v86_alias_gray_release_plan.md` |
| 降级预案 | A8473607D2BFFC31D5C11D8352EC550D | `v86_alias_degrade_plan.md` |
| 监控规范 | 510A4CFC196B4D301EE3E23301A9DFE0 | `v86_alias_monitor_spec.md` |
| 门禁自动化 | C8A0F439AE6D9318D4DDAAF0730ACC06 | `alias_gate_auto_check.py` |
| 预热优化 | 48EB5AC0ADE4ACBB1FD1FA8C9DE29609 | `alias_engine_warmup_optimize.py` |
| P0 样本集 | 49FADBB8CA098DFEA0935974C622A49A | `alias_p0_manual_sample_set.json` |
| 联合扫描 | F82FB68A0534C5BE506F5AE1790573DC | `v86_alias_rule_joint_scan.md` |
| 引擎原型 | E77C8E3692235F1CCE83076920F118C9 | `v86_alias_engine_prototype.py` |
| 任务适配层 | DC88D82E1F6BDF2802EBF4B5091647E3 | `alias_task_adapter.py` |
| 风险评估 | 2A92953FFF7AEEA45D6EA0B3E8210820 | `v86_alias_engine_risk_perf_estimate.md` |
| DSHB 生产部署 | BD71B14140CA7C2ABFF423DE7E29425A | `v86_rule_production_bundle.md` |
| DSHB 回退方案 | 43CAEC3D168EA0D36510D3A26C132893 | `v86_rule_rollback_plan.md` |
| DSHB 资源评估 | 8C899316BF7EE67D15F23869AA81C5DA | `v86_rule_resource_estimate.md` |
| DSHB 监控规范 | 6A7526B91601D650384A1CB840342DF6 | `v86_rule_metric_monitor_spec.md` |
| DSHB 全量回放 | F6B8242F89C9F60D60E203DF138DBBBB | `v86_rule_full_dataset_replay_report.md` |
| V85 MD5 | 79EA4CDBB6D6527A75E6BB98D9606980 | `v85_final_archive/MD5_MANIFEST.md` |

---

*MD5 清单 v2 由 DSHE_V86_ALIAS_GATE_RISK_MONITORING_ALIGNMENT_AND_FINAL_ARCHIVE T3.4 生成*
*分支: feature/v85-chart-template · Commit: bcbb0e7 · 资产版本: v86.0.0-frozen*
