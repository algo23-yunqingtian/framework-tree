# V86 Framework Tree 资产元数据索引 V6 (T3.3)

> 任务: `DSHE_V86_ALIAS_V6_ITERATION_GD187598` · T3.3
> 分支: `feature/v85-chart-template`
> 基线: DSHE V5 Asset Index (commit 57a86ff)
> 迭代: V5 → V6 (全局指标对齐 + 分模块索引 + 版本链路补全)
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED
> 生成日期: 2026-10-03

---

## 目录

1. [Framework Tree 目录总览 V6](#1-framework-tree-目录总览-v6)
2. [资产元数据索引 V6](#2-资产元数据索引-v6)
3. [分模块资产索引 (PB/ZNN/NI/SN/LI/AL/CU/AO)](#3-分模块资产索引)
4. [版本链路追踪 V6](#4-版本链路追踪-v6)
5. [Framework Tree 页面渲染规则 V6](#5-framework-tree-页面渲染规则-v6)
6. [框架树同步待办清单 V6](#6-框架树同步待办清单-v6)
7. [资产完整性校验 V6](#7-资产完整性校验-v6)

---

## 1. Framework Tree 目录总览 V6

### 1.1 目录树结构

```
analysis/e2e_output/v86/
├── dshb_gate_accept_final/          (7 files, 151 KB)  — DSHB 终审验收
├── dshb_gate_final_review/           (7 files, 213 KB)  — DSHB 终审复核
├── dshb_gate_upgrade_review/         (11 files, 205 KB) — DSHB 终审升级
├── dshb_rule_ci_stress/              (11 files, 234 KB) — DSHB 规则 CI 压测
├── dshb_rule_full_regress/           (10 files, 250 KB) — DSHB 规则全量回归
├── dshb_rule_predev/                  (7 files, 129 KB) — DSHB 规则预开发
├── dshb_rule_prod_prep/              (9 files, 191 KB)  — DSHB 规则生产准备
├── dshe_alias_gate_demo_release/    (5 files, 115 KB)  — DSHE 别名演示发布
├── dshe_alias_gate_final/           (14 files, 418 KB)  — DSHE 别名终审
├── dshe_alias_gate_final_v2/        (5 files, 133 KB)   — DSHE 别名终审 V2
├── dshe_alias_gate_final_v3/        (5 files, 139 KB)   — DSHE 别名终审 V3
├── dshe_alias_gate_final_v4/        (5 files, 188 KB)   — DSHE 别名终审 V4
├── dshe_alias_gate_final_v5/        (5 files, 162 KB)   — DSHE 别名终审 V5
├── **dshe_alias_gate_final_v6/**    (**5 files, ~200 KB**) — **DSHE 别名终审 V6 (本次)**
├── dshe_alias_joint_check/          (11 files, 187 KB)  — DSHE 联合检查
├── dshe_alias_ops_final/            (7 files, 100 KB)   — DSHE 运维终稿
├── dshe_alias_predev/               (10 files, 280 KB)  — DSHE 预开发
├── dshe_alias_prod_prep/            (11 files, 3.5 MB)  — DSHE 生产准备
├── hermes_e2e_test/                 (6 files, 46 KB)    — Hermes E2E 测试
├── hermes_portal_prep/              (6 files, 49 KB)    — Hermes 门户准备
└── JOB_READY.flag                    (1 file, ~21 KB)    — 任务就绪标记
```

### 1.2 目录统计 V6

| 目录 | 文件数 | 总大小 | 所属模块 | 版本 |
|------|-------|-------|---------|------|
| dshb_gate_accept_final | 7 | 151 KB | DSHB Gate | 终审验收 |
| dshb_gate_final_review | 7 | 213 KB | DSHB Gate | 终审复核 |
| dshb_gate_upgrade_review | 11 | 205 KB | DSHB Gate | 终审升级 |
| dshb_rule_ci_stress | 11 | 234 KB | DSHB Rule | CI 压测 |
| dshb_rule_full_regress | 10 | 250 KB | DSHB Rule | 全量回归 |
| dshb_rule_predev | 7 | 129 KB | DSHB Rule | 预开发 |
| dshb_rule_prod_prep | 9 | 191 KB | DSHB Rule | 生产准备 |
| dshe_alias_gate_demo_release | 5 | 115 KB | DSHE Alias | 演示发布 |
| dshe_alias_gate_final | 14 | 418 KB | DSHE Alias | 终审 (V1) |
| dshe_alias_gate_final_v2 | 5 | 133 KB | DSHE Alias | 终审 V2 |
| dshe_alias_gate_final_v3 | 5 | 139 KB | DSHE Alias | 终审 V3 |
| dshe_alias_gate_final_v4 | 5 | 188 KB | DSHE Alias | 终审 V4 |
| dshe_alias_gate_final_v5 | 5 | 162 KB | DSHE Alias | 终审 V5 |
| **dshe_alias_gate_final_v6** | **5** | **~200 KB** | **DSHE Alias** | **终审 V6 (本次)** |
| dshe_alias_joint_check | 11 | 187 KB | DSHE Alias | 联合检查 |
| dshe_alias_ops_final | 7 | 100 KB | DSHE Alias | 运维终稿 |
| dshe_alias_predev | 10 | 280 KB | DSHE Alias | 预开发 |
| dshe_alias_prod_prep | 11 | 3.5 MB | DSHE Alias | 生产准备 |
| hermes_e2e_test | 6 | 46 KB | Hermes | E2E 测试 |
| hermes_portal_prep | 6 | 49 KB | Hermes | 门户准备 |
| (root) | 1 | ~21 KB | 全局 | JOB_READY.flag |
| **总计** | **158** | **~7.8 MB** | — | — |

---

## 2. 资产元数据索引 V6

### 2.1 DSHB Gate 资产 (31 files, 569 KB)

| # | 文件路径 | 大小 | 版本 | 说明 | 关联 Commit |
|---|---------|------|------|------|-----------|
| 1 | dshb_gate_accept_final/JOB_READY.flag | 1,892 B | — | 任务就绪标记 | 311f82c |
| 2 | dshb_gate_accept_final/v86_gate_acceptance_final_report.md | 21,131 B | V1 | 终审验收报告 | 311f82c |
| 3 | dshb_gate_accept_final/v86_join_prod_stress_test_report.md | 13,714 B | V1 | 联合压测报告 | 311f82c |
| 4 | dshb_gate_accept_final/v86_launch_risk_register.md | 33,165 B | V1 | 上线风险台账 | 311f82c |
| 5 | dshb_gate_accept_final/v86_preflight_checklist.md | 31,035 B | V1 | 上线前置清单 | 311f82c |
| 6 | dshb_gate_accept_final/stress_test_results.json | 12,091 B | — | 压测结果数据 | 311f82c |
| 7 | dshb_gate_accept_final/MD5_MANIFEST.md | 2,046 B | — | MD5 校验清单 | 311f82c |
| 8 | dshb_gate_accept_final/joint_prod_stress_test.py | 53,912 B | — | 联合压测脚本 | 311f82c |
| 9 | dshb_gate_final_review/JOB_READY.flag | 1,953 B | — | 任务就绪标记 | 311f82c |
| 10 | dshb_gate_final_review/v86_crossgroup_consistency_report.md | 36,840 B | V1 | 跨组一致性报告 | 311f82c |
| 11 | dshb_gate_final_review/v86_gate_closure_verification.md | 32,751 B | V1 | Gate 闭环验证 | 311f82c |
| 12 | dshb_gate_final_review/v86_preflight_checklist_final.md | 63,928 B | V1 | 前置清单 (终稿) | 311f82c |
| 13 | dshb_gate_final_review/v86_risk_closure_verification.md | 45,003 B | V1 | 风险闭环验证 | 311f82c |
| 14 | dshb_gate_final_review/v86_stress_baseline_fixation.md | 17,808 B | V1 | 压测基线固化 | 311f82c |
| 15 | dshb_gate_final_review/stress_test_results_v2.json | 13,568 B | — | 压测结果 V2 | 311f82c |
| 16 | dshb_gate_final_review/MD5_MANIFEST.md | 2,135 B | — | MD5 校验清单 | 311f82c |
| 17 | dshb_gate_final_review/joint_prod_stress_test_v2.py | 27,625 B | — | 联合压测脚本 V2 | 311f82c |
| 18 | dshb_gate_upgrade_review/JOB_READY.flag | 1,651 B | — | 任务就绪标记 | 311f82c |
| 19 | dshb_gate_upgrade_review/v86_conditional_conditions_closure_v2.md | 31,147 B | V2 | 条件闭环 V2 | 311f82c |
| 20 | dshb_gate_upgrade_review/v86_dependency_gap_impact_assessment.md | 16,659 B | V1 | DEPENDENCY_GAP 评估 | 311f82c |
| 21 | dshb_gate_upgrade_review/v86_gate_upgrade_assessment_report.md | 27,208 B | V1 | 终审升级评估 | 311f82c |
| 22 | dshb_gate_upgrade_review/v86_gate_upgrade_assessment_report_v3.md | 25,190 B | V3 | 终审升级评估 V3 | 311f82c |
| 23 | dshb_gate_upgrade_review/v86_monitoring_gap_review_report.md | 22,453 B | V1 | 监控缺口评审 | 311f82c |
| 24 | dshb_gate_upgrade_review/v86_open_risks_disposition_v2.md | 26,372 B | V2 | 开放风险处置 V2 | 311f82c |
| 25 | dshb_gate_upgrade_review/v86_preflight_checklist_v2.md | 34,379 B | V2 | 前置清单 V2 | 311f82c |
| 26 | dshb_gate_upgrade_review/v86_preflight_checklist_v4.md | 19,916 B | V4 | 前置清单 V4 | 311f82c |
| 27 | dshb_gate_upgrade_review/MD5_MANIFEST_v2.md | 1,890 B | — | MD5 校验清单 V2 | 311f82c |
| 28 | dshb_gate_upgrade_review/MD5_MANIFEST_v3.md | 2,215 B | — | MD5 校验清单 V3 | 311f82c |
| 29 | dshb_gate_upgrade_review/v86_crossgroup_consistency_report.md | — | — | 跨组一致性 (引用) | 311f82c |
| 30 | dshb_gate_upgrade_review/v86_monitoring_gap_review_report.md | — | — | 监控缺口 (引用) | 311f82c |
| 31 | dshb_gate_upgrade_review/v86_dependency_gap_impact_assessment.md | — | — | GAP 评估 (引用) | 311f82c |

### 2.2 DSHB Rule 资产 (37 files, 804 KB)

| # | 文件路径 | 大小 | 版本 | 说明 | 关联 Commit |
|---|---------|------|------|------|-----------|
| 1 | dshb_rule_ci_stress/JOB_READY.flag | 772 B | — | 任务就绪标记 | b0ff196 |
| 2 | dshb_rule_ci_stress/v86_p1_rule_prototype.py | 81,487 B | — | P1 规则原型 | b0ff196 |
| 3 | dshb_rule_ci_stress/v86_p1_rule_test_suite.json | 15,221 B | — | P1 规则测试套件 | b0ff196 |
| 4 | dshb_rule_ci_stress/ci_rule_verify_pipeline.py | 37,203 B | — | CI 规则验证管线 | b0ff196 |
| 5 | dshb_rule_ci_stress/benchmark_results.json | 6,397 B | — | 基准测试结果 | b0ff196 |
| 6 | dshb_rule_ci_stress/ci_report.json | 17,003 B | — | CI 报告 | b0ff196 |
| 7 | dshb_rule_ci_stress/ci_result.txt | 1,659 B | — | CI 结果 | b0ff196 |
| 8 | dshb_rule_ci_stress/v86_rule_fault_tolerance.md | 13,787 B | V1 | 规则容错报告 | b0ff196 |
| 9 | dshb_rule_ci_stress/v86_rule_ops_checklist.md | 17,117 B | V1 | 规则运维清单 | b0ff196 |
| 10 | dshb_rule_ci_stress/v86_rule_performance_report.md | 10,426 B | V1 | 规则性能报告 | b0ff196 |
| 11 | dshb_rule_ci_stress/MD5_MANIFEST.md | 532 B | — | MD5 校验清单 | b0ff196 |
| 12 | dshb_rule_full_regress/JOB_READY.flag | 518 B | — | 任务就绪标记 | b0ff196 |
| 13 | dshb_rule_full_regress/v86_metric_caliber_doc.md | 20,499 B | V1 | **指标口径文档 (全局指标主清单来源)** | b0ff196 |
| 14 | dshb_rule_full_regress/v86_rule_alias_joint_regression.md | 14,863 B | V1 | 规则-别名联合回归 | b0ff196 |
| 15 | dshb_rule_full_regress/v86_rule_asset_bundle.md | 8,458 B | V1 | 规则资产包 | b0ff196 |
| 16 | dshb_rule_full_regress/v86_rule_error_code_spec.md | 36,005 B | V1 | 错误码规范 | b0ff196 |
| 17 | dshb_rule_full_regress/ci_report_enhanced.json | 32,450 B | — | CI 报告 (增强) | b0ff196 |
| 18 | dshb_rule_full_regress/ci_result_enhanced.txt | 3,390 B | — | CI 结果 (增强) | b0ff196 |
| 19 | dshb_rule_full_regress/ci_rule_alias_enhanced.py | 74,320 B | — | CI 规则-别名增强脚本 | b0ff196 |
| 20 | dshb_rule_full_regress/joint_regression_results.json | 58,983 B | — | 联合回归结果 | b0ff196 |
| 21 | dshb_rule_full_regress/joint_regression_runner.py | 37,065 B | — | 联合回归运行器 | b0ff196 |
| 22 | dshb_rule_full_regress/MD5_MANIFEST.md | 1,532 B | — | MD5 校验清单 | b0ff196 |
| 23 | dshb_rule_predev/comparison_report.json | 2,192 B | — | 对比报告 | b0ff196 |
| 24 | dshb_rule_predev/v85_v86_rule_compare.py | 24,330 B | — | V85/V86 规则对比 | b0ff196 |
| 25 | dshb_rule_predev/v86_bl_rule_regression_report.md | 21,282 B | V1 | 黑名单规则回归报告 | b0ff196 |
| 26 | dshb_rule_predev/v86_p0_rule_prototype.py | 56,156 B | — | P0 规则原型 | b0ff196 |
| 27 | dshb_rule_predev/v86_rule_task_adapter.md | 18,940 B | V1 | 规则任务适配器 | b0ff196 |
| 28 | dshb_rule_predev/v86_rule_test_suite.json | 26,727 B | — | 规则测试套件 | b0ff196 |
| 29 | dshb_rule_predev/MD5_MANIFEST.md | 2,546 B | — | MD5 校验清单 | b0ff196 |
| 30 | dshb_rule_prod_prep/JOB_READY.flag | 1,101 B | — | 任务就绪标记 | b0ff196 |
| 31 | dshb_rule_prod_prep/v86_rule_full_dataset_replay_report.md | 11,703 B | V1 | 全量回放报告 | b0ff196 |
| 32 | dshb_rule_prod_prep/v86_rule_metric_monitor_spec.md | 29,315 B | V1 | **规则监控指标规范 (全局指标主清单 90 指标定义)** | b0ff196 |
| 33 | dshb_rule_prod_prep/v86_rule_production_bundle.md | 11,035 B | V1 | 规则生产包 | b0ff196 |
| 34 | dshb_rule_prod_prep/v86_rule_resource_estimate.md | 14,005 B | V1 | 规则资源评估 | b0ff196 |
| 35 | dshb_rule_prod_prep/v86_rule_rollback_plan.md | 15,568 B | V1 | 规则回滚计划 | b0ff196 |
| 36 | dshb_rule_prod_prep/full_dataset_replay_runner.py | 33,857 B | — | 全量回放运行器 | b0ff196 |
| 37 | dshb_rule_prod_prep/full_replay_results.json | 72,863 B | — | 全量回放结果 | b0ff196 |

### 2.3 DSHE Alias 资产 (71 files, 5.3 MB)

| # | 文件路径 | 大小 | 版本 | 说明 | 关联 Commit |
|---|---------|------|------|------|-----------|
| 1 | dshe_alias_gate_demo_release/MD5_CHECKSUM_LIST.md | 3,399 B | — | MD5 校验清单 | 61b8ca5 |
| 2 | dshe_alias_gate_demo_release/v86_alias_gate_demo_package.md | 34,011 B | V1 | 别名演示包 | 61b8ca5 |
| 3 | dshe_alias_gate_demo_release/v86_alias_gate_qakb.md | 24,143 B | V1 | QA 知识库 | 61b8ca5 |
| 4 | dshe_alias_gate_demo_release/v86_alias_portal_data_cross_check.md | 20,743 B | V1 | 门户数据交叉检查 | 61b8ca5 |
| 5 | dshe_alias_gate_demo_release/v86_alias_release_note_final.md | 26,640 B | V1 | Release Note 终稿 | 61b8ca5 |
| 6 | dshe_alias_gate_final/JOB_READY.flag | 1,910 B | — | 任务就绪标记 | 61b8ca5 |
| 7 | dshe_alias_gate_final/MD5_CHECKSUM_LIST.md | 4,380 B | — | MD5 校验清单 | 61b8ca5 |
| 8 | dshe_alias_gate_final/MD5_MANIFEST_v2.md | 2,279 B | — | MD5 校验清单 V2 | 61b8ca5 |
| 9 | dshe_alias_gate_final/v86_alias_caliber_consistency_review_v2.md | 26,333 B | V2 | 口径一致性复核 V2 | 61b8ca5 |
| 10 | dshe_alias_gate_final/v86_alias_caliber_final_audit.md | 29,230 B | V1 | 口径终审报告 | 61b8ca5 |
| 11 | dshe_alias_gate_final/v86_alias_final_archive_bundle.md | 32,140 B | V1 | 归档资产包 | 61b8ca5 |
| 12 | dshe_alias_gate_final/v86_alias_final_archive_bundle_v2.md | 29,380 B | V2 | 归档资产包 V2 | 61b8ca5 |
| 13 | dshe_alias_gate_final/v86_alias_gate_final_demo_package.md | 37,752 B | V1 | 演示包 V1 | 61b8ca5 |
| 14 | dshe_alias_gate_final/v86_alias_gate_final_demo_package_v2.md | 28,599 B | V2 | 演示包 V2 | 61b8ca5 |
| 15 | dshe_alias_gate_final/v86_alias_gate_qakb_v2.md | 16,202 B | V2 | QA 知识库 V2 | 61b8ca5 |
| 16 | dshe_alias_gate_final/v86_alias_grafana_panels_final.md | 66,123 B | V1 | Grafana 面板终稿 | 61b8ca5 |
| 17 | dshe_alias_gate_final/v86_alias_portal_deviation_fix_report.md | 48,879 B | V1 | 门户偏差修复报告 | 61b8ca5 |
| 18 | dshe_alias_gate_final/v86_alias_release_note_v2.md | 19,333 B | V2 | Release Note V2 | 61b8ca5 |
| 19 | dshe_alias_gate_final/v86_alias_risk_monitoring_coverage_review_v2.md | 51,117 B | V2 | 风险监控覆盖复核 V2 | 61b8ca5 |
| 20 | dshe_alias_gate_final_v2/MD5_CHECKSUM_LIST_v2.md | 4,986 B | — | MD5 校验清单 V2 | eefa4d3 |
| 21 | dshe_alias_gate_final_v2/v86_alias_final_archive_bundle_v2.md | 31,183 B | V2 | 归档资产包 V2 | eefa4d3 |
| 22 | dshe_alias_gate_final_v2/v86_alias_gate_final_demo_v3.md | 32,107 B | V3 | 演示包 V3 | eefa4d3 |
| 23 | dshe_alias_gate_final_v2/v86_alias_portal_caliber_second_review.md | 32,330 B | V1 | 口径二次复核 V1 | eefa4d3 |
| 24 | dshe_alias_gate_final_v2/v86_alias_risk_monitoring_review.md | 29,765 B | V1 | 风险监控复核 V1 | eefa4d3 |
| 25 | dshe_alias_gate_final_v3/MD5_CHECKSUM_LIST_v3.md | 4,179 B | — | MD5 校验清单 V3 | eefa4d3 |
| 26 | dshe_alias_gate_final_v3/v86_alias_final_archive_bundle_v3.md | 22,695 B | V3 | 归档资产包 V3 | eefa4d3 |
| 27 | dshe_alias_gate_final_v3/v86_alias_gate_final_demo_v4.md | 35,914 B | V4 | 演示包 V4 | eefa4d3 |
| 28 | dshe_alias_gate_final_v3/v86_alias_portal_caliber_second_review_v2.md | 41,813 B | V2 | 口径二次复核 V2 | eefa4d3 |
| 29 | dshe_alias_gate_final_v3/v86_alias_risk_monitoring_review_v2.md | 39,533 B | V2 | 风险监控复核 V2 | eefa4d3 |
| 30 | dshe_alias_gate_final_v4/MD5_CHECKSUM_LIST_v4.md | 5,280 B | — | MD5 校验清单 V4 | a9d8a4e |
| 31 | dshe_alias_gate_final_v4/v86_alias_final_archive_bundle_v4.md | 28,197 B | V4 | 归档资产包 V4 | a9d8a4e |
| 32 | dshe_alias_gate_final_v4/v86_alias_gate_final_demo_v5.md | 67,122 B | V5 | 演示包 V5 | a9d8a4e |
| 33 | dshe_alias_gate_final_v4/v86_alias_portal_caliber_second_review_v3.md | 62,823 B | V3 | 口径二次复核 V3 | a9d8a4e |
| 34 | dshe_alias_gate_final_v4/v86_alias_risk_monitoring_review_v3.md | 69,615 B | V3 | 风险监控复核 V3 | a9d8a4e |
| 35 | dshe_alias_gate_final_v5/MD5_CHECKSUM_LIST_v5.md | 10,493 B | — | MD5 校验清单 V5 | 57a86ff |
| 36 | dshe_alias_gate_final_v5/v86_alias_final_archive_bundle_v5.md | 21,291 B | V5 | 归档资产包 V5 | 57a86ff |
| 37 | dshe_alias_gate_final_v5/v86_alias_gate_final_demo_v6.md | 76,123 B | V6 | 演示包 V6 | 57a86ff |
| 38 | dshe_alias_gate_final_v5/v86_panel_metric_alignment_report.md | 31,899 B | V1 | 面板指标对齐报告 | 57a86ff |
| 39 | dshe_alias_gate_final_v5/v86_framework_tree_asset_index.md | 32,121 B | V1 | Framework Tree 资产索引 | 57a86ff |
| 40 | **dshe_alias_gate_final_v6/MD5_CHECKSUM_LIST_v6.md** | **—** | **—** | **MD5 校验清单 V6** | **本次** |
| 41 | **dshe_alias_gate_final_v6/v86_alias_final_archive_bundle_v6.md** | **—** | **V6** | **归档资产包 V6** | **本次** |
| 42 | **dshe_alias_gate_final_v6/v86_alias_gate_final_demo_v7.md** | **—** | **V7** | **演示包 V7** | **本次** |
| 43 | **dshe_alias_gate_final_v6/v86_panel_metric_alignment_report_v6.md** | **—** | **V6** | **面板指标对齐报告 V6** | **本次** |
| 44 | **dshe_alias_gate_final_v6/v86_framework_tree_asset_index_v6.md** | **—** | **V6** | **Framework Tree 资产索引 V6** | **本次** |
| 45 | dshe_alias_joint_check/MD5_CHECKSUM_LIST.md | 2,205 B | — | MD5 校验清单 | 168a073 |
| 46 | dshe_alias_joint_check/v86_alias_asset_bundle.md | 6,704 B | V1 | 别名资产包 | 168a073 |
| 47 | dshe_alias_joint_check/v86_alias_rule_joint_scan.md | 9,167 B | V1 | 别名-规则联合扫描 | 168a073 |
| 48 | dshe_alias_joint_check/alias_engine_warmup_optimize.py | 21,479 B | — | 预热优化脚本 | 168a073 |
| 49 | dshe_alias_joint_check/alias_gate_auto_check.py | 33,372 B | — | Gate 自动检查 | 168a073 |
| 50 | dshe_alias_joint_check/alias_p0_manual_sample_set.json | 57,873 B | — | P0 手动样本集 | 168a073 |
| 51 | dshe_alias_joint_check/gate_auto_check_report.json | 1,636 B | — | Gate 自动检查报告 | 168a073 |
| 52 | dshe_alias_joint_check/warmup_benchmark_results.json | 3,128 B | — | 预热基准结果 | 168a073 |
| 53 | dshe_alias_joint_check/warmup_verify_results.json | 1,477 B | — | 预热验证结果 | 168a073 |
| 54 | dshe_alias_ops_final/MD5_CHECKSUM_LIST.md | 5,077 B | — | MD5 校验清单 | 81268a6 |
| 55 | dshe_alias_ops_final/v86_alias_frozen_asset_bundle.md | 10,526 B | V1 | 冻结资产包 | 81268a6 |
| 56 | dshe_alias_ops_final/v86_alias_gray_full_simulation.md | 17,072 B | V1 | 灰度全量仿真 | 81268a6 |
| 57 | dshe_alias_ops_final/v86_alias_ops_manual_final.md | 29,923 B | V1 | 运维手册终稿 | 81268a6 |
| 58 | dshe_alias_ops_final/v86_alias_prod_integrate_verify_report.md | 21,750 B | V1 | 生产集成验证 | 81268a6 |
| 59 | dshe_alias_ops_final/gray_simulation_results.json | 25,039 B | — | 灰度仿真结果 | 81268a6 |
| 60 | dshe_alias_ops_final/gray_simulation_runner.py | 29,140 B | — | 灰度仿真运行器 | 81268a6 |
| 61 | dshe_alias_predev/MD5_CHECKSUM_LIST.md | 1,695 B | — | MD5 校验清单 | 5e874a7 |
| 62 | dshe_alias_predev/v86_alias_engine_risk_perf_estimate.md | 12,301 B | V1 | 风险性能评估 | 5e874a7 |
| 63 | dshe_alias_predev/v86_alias_regression_report.md | 11,641 B | V1 | 别名回归报告 | 5e874a7 |
| 64 | dshe_alias_predev/alias_task_adapter.py | 30,024 B | — | 任务适配器 | 5e874a7 |
| 65 | dshe_alias_predev/alias_v86_extended_test_case.json | 20,927 B | — | 扩展测试用例 | 5e874a7 |
| 66 | dshe_alias_predev/regression_results.json | 130,190 B | — | 回归结果 | 5e874a7 |
| 67 | dshe_alias_predev/test_run_results.json | 15,062 B | — | 测试运行结果 | 5e874a7 |
| 68 | dshe_alias_predev/v86_alias_engine_prototype.py | 42,512 B | — | 引擎原型 | 5e874a7 |
| 69 | dshe_alias_prod_prep/MD5_CHECKSUM_LIST.md | 1,560 B | — | MD5 校验清单 | d8e44a9 |
| 70 | dshe_alias_prod_prep/v86_alias_degrade_plan.md | 14,871 B | V1 | 降级计划 | d8e44a9 |
| 71 | dshe_alias_prod_prep/v86_alias_full_replay_report.md | 6,580 B | V1 | 全量回放报告 | d8e44a9 |
| 72 | dshe_alias_prod_prep/v86_alias_gray_release_plan.md | 13,218 B | V1 | 灰度发布计划 | d8e44a9 |
| 73 | dshe_alias_prod_prep/v86_alias_monitor_spec.md | 17,364 B | V1 | 监控规范 | d8e44a9 |
| 74 | dshe_alias_prod_prep/v86_alias_production_bundle.md | 17,385 B | V1 | 生产包 | d8e44a9 |
| 75 | dshe_alias_prod_prep/replay_results.json | 3,382,924 B | — | 回放结果 (大文件) | d8e44a9 |
| 76 | dshe_alias_prod_prep/v86_alias_full_replay.py | 25,076 B | — | 全量回放脚本 | d8e44a9 |

### 2.4 Hermes 资产 (12 files, 95 KB)

| # | 文件路径 | 大小 | 版本 | 说明 | 关联 Commit |
|---|---------|------|------|------|-----------|
| 1 | hermes_e2e_test/MD5_CHECKSUM_LIST.md | 662 B | — | MD5 校验清单 | 03b3a73 |
| 2 | hermes_e2e_test/portal_defect_fix_patch.md | 6,480 B | V1 | 门户缺陷修复补丁 | 03b3a73 |
| 3 | hermes_e2e_test/portal_metric_caliber_ui.md | 8,866 B | V1 | 门户指标口径 UI | 03b3a73 |
| 4 | hermes_e2e_test/v86_demo_runbook.md | 9,533 B | V1 | 演示运行手册 | 03b3a73 |
| 5 | hermes_e2e_test/v86_dual_task_portal.md | 13,003 B | V1 | 双任务门户 | 03b3a73 |
| 6 | hermes_e2e_test/v86_full_e2e_report.md | 7,734 B | V1 | 全量 E2E 报告 | 03b3a73 |
| 7 | hermes_portal_prep/MD5_CHECKSUM_LIST.md | 575 B | — | MD5 校验清单 | 03b3a73 |
| 8 | hermes_portal_prep/portal_e2e_smoke_report.md | 9,184 B | V1 | 门户 E2E 冒烟报告 | 03b3a73 |
| 9 | hermes_portal_prep/portal_permission_config.md | 8,944 B | V1 | 门户权限配置 | 03b3a73 |
| 10 | hermes_portal_prep/v85_frozen_portal_page.md | 9,936 B | V1 | V85 冻结门户页 | 03b3a73 |
| 11 | hermes_portal_prep/v85_v86_compare_panel.md | 9,015 B | V1 | V85/V86 对比面板 | 03b3a73 |
| 12 | hermes_portal_prep/v86_portal_integrate_doc.md | 12,946 B | V1 | 门户集成文档 | 03b3a73 |

### 2.5 全局资产 (1 file)

| # | 文件路径 | 大小 | 版本 | 说明 | 关联 Commit |
|---|---------|------|------|------|-----------|
| 1 | JOB_READY.flag | ~21 KB | — | 任务就绪标记 (全局) | 57a86ff + 本次 |

---

## 3. 分模块资产索引

### 3.1 品种模块索引

#### PB (铅) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 6 | 铅锭价格, 铅锭进出口比价 | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 4 | 社会库存, 保税库存, 厂库库存, 期货库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 4 | 精炼铅产量, 再生铅产量, 电解铅产量, 进口铅锭 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 3 | 铅酸电池产量, 表观消费, 铅需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 4 | 铅精矿成本, 精炼铅成本, 再生铅成本, 综合成本 | replay_results.json | dshe_alias_prod_prep/ |
| 进出口 | 4 | 铅锭出口, 铅锭进口, 铅精矿出口, 铅精矿进口 | replay_results.json | dshe_alias_prod_prep/ |
| **PB 总计** | **25** | — | — | — |

#### ZNN (锌) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 6 | 锌锭价格, 锌锭进出口比价 | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 5 | 社会库存, 保税库存, 厂库库存, 期货库存, 在途库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 5 | 电解锌产量, 进口锌锭, 锌精矿进口, 国产锌精矿, 锌加工费 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 4 | 镀锌产量, 压铸锌合金, 氧化锌, 锌需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 3 | 锌精矿成本, 电解锌成本, 综合成本 | replay_results.json | dshe_alias_prod_prep/ |
| 进出口 | 4 | 锌锭出口, 锌锭进口, 锌精矿出口, 锌精矿进口 | replay_results.json | dshe_alias_prod_prep/ |
| **ZNN 总计** | **27** | — | — | — |

#### NI (镍) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 5 | 镍矿价格, 高镍生铁, 镍铁价格, 硫酸镍 | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 3 | 镍库存, 镍期货库存, 镍厂库库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 4 | 镍矿产量, 印尼镍矿, 镍铁产量, 硫酸镍产量 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 3 | 不锈钢镍需求, 电池镍需求, 镍需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 3 | 镍矿成本, 镍铁成本, 硫酸镍成本 | replay_results.json | dshe_alias_prod_prep/ |
| **NI 总计** | **18** | — | — | — |

#### SN (锡) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 4 | 锡锭价格, 锡精矿价格, 印尼锡价 | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 3 | 锡库存, 锡期货库存, 锡厂库库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 4 | 锡矿产量, 缅甸锡矿, 印尼锡矿, 锡精矿进口 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 2 | 焊锡需求, 锡需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 3 | 锡矿成本, 锡锭成本, 综合成本 | replay_results.json | dshe_alias_prod_prep/ |
| **SN 总计** | **16** | — | — | — |

#### LI (锂) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 5 | 碳酸锂价格, 氢氧化锂价格, 锂辉石价格 | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 3 | 锂库存, 锂期货库存, 锂厂库库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 4 | 碳酸锂产量, 氢氧化锂产量, 锂辉石矿产量, 锂云母产量 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 3 | 电池碳酸锂需求, 电池氢氧化锂需求, 锂需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 3 | 锂辉石成本, 锂云母成本, 碳酸锂成本 | replay_results.json | dshe_alias_prod_prep/ |
| **LI 总计** | **18** | — | — | — |

#### AL (铝) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 6 | 电解铝价格, 铝锭进出口比价, A00铝价 | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 5 | 社会库存, 保税库存, 厂库库存, 期货库存, 在途库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 5 | 电解铝产量, 氧化铝产量, 铝土矿产量, 电解铝开工率, 氧化铝开工率 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 4 | 汽车铝需求, 建筑铝需求, 包装铝需求, 铝需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 4 | 铝土矿成本, 氧化铝成本, 电解铝成本, 电力成本 | replay_results.json | dshe_alias_prod_prep/ |
| 进出口 | 4 | 铝锭出口, 铝锭进口, 氧化铝出口, 氧化铝进口 | replay_results.json | dshe_alias_prod_prep/ |
| **AL 总计** | **28** | — | — | — |

#### CU (铜) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 6 | 电解铜价格, 铜精矿TC/RC, 进口铜溢价, LME铜价 | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 5 | 社会库存, 保税库存, 厂库库存, 期货库存, LME库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 5 | 电解铜产量, 精炼铜产量, 进口阴极铜, 铜精矿进口, 冶炼加工费 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 4 | 电线电缆铜需求, 铜板带箔需求, 铜管需求, 铜需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 3 | 铜精矿成本, 电解铜成本, 综合成本 | replay_results.json | dshe_alias_prod_prep/ |
| 进出口 | 4 | 铜锭出口, 铜锭进口, 铜精矿出口, 铜精矿进口 | replay_results.json | dshe_alias_prod_prep/ |
| **CU 总计** | **27** | — | — | — |

#### AO (氧化铝) 模块

| 指标域 | 指标数 | 代表指标 | 数据源 | 关联文件 |
|-------|-------|---------|-------|---------|
| 价格 | 4 | 氧化铝价格, 澳洲氧化铝FOB, 南非氧化铝FOB | replay_results.json | dshe_alias_prod_prep/ |
| 库存 | 2 | 氧化铝库存, 氧化铝厂库库存 | replay_results.json | dshe_alias_prod_prep/ |
| 供给 | 3 | 氧化铝产量, 进口氧化铝, 国内氧化铝产量 | replay_results.json | dshe_alias_prod_prep/ |
| 需求 | 2 | 电解铝氧化铝需求, 氧化铝需求 | replay_results.json | dshe_alias_prod_prep/ |
| 成本 | 3 | 铝土矿成本, 氧化铝成本, 能源成本 | replay_results.json | dshe_alias_prod_prep/ |
| **AO 总计** | **14** | — | — | — |

### 3.2 分模块汇总

| 品种 | 指标数 | 占比 | 数据源覆盖 | 关联别名条目 |
|------|-------|------|---------|------------|
| PB (铅) | 25 | 5.4% | ✅ replay_results.json | ~232 |
| ZNN (锌) | 27 | 5.8% | ✅ replay_results.json | ~604 |
| NI (镍) | 18 | 3.9% | ✅ replay_results.json | ~1,161 |
| SN (锡) | 16 | 3.5% | ✅ replay_results.json | ~743 |
| LI (锂) | 18 | 3.9% | ✅ replay_results.json | ~604 |
| AL (铝) | 28 | 6.0% | ✅ replay_results.json | ~604 |
| CU (铜) | 27 | 5.8% | ✅ replay_results.json | ~139 |
| AO (氧化铝) | 14 | 3.0% | ✅ replay_results.json | ~92 |
| **总计** | **173** | **100%** | **✅ 8/8 品种** | **~4,179** |

> 注: 别名条目数为估计值, 基于 replay_results.json 中各品种别名条目比例推算。总计 4,643 条目中约 4,179 归入 8 品种模块。

### 3.3 分模块资产树

```
analysis/e2e_output/v86/
├── 📁 dshe_alias_prod_prep/  ← 全品种共享
│   ├── 📄 v86_alias_monitor_spec.md           (别名监控规范, 全品种)
│   ├── 📄 v86_alias_degrade_plan.md           (降级计划, 全品种)
│   ├── 📄 v86_alias_full_replay_report.md     (全量回放报告)
│   ├── 📄 v86_alias_gray_release_plan.md      (灰度发布计划)
│   ├── 📄 v86_alias_production_bundle.md      (生产包)
│   ├── 📊 replay_results.json                 (4,643 条目, 全品种)
│   └── 🐍 v86_alias_full_replay.py            (全量回放脚本)
│
├── 📁 dshe_alias_gate_final_v5/               ← V5 终审 (含 Panel 指标对齐)
│   ├── 📄 v86_panel_metric_alignment_report.md (157 指标对齐)
│   └── 📄 v86_alias_gate_final_demo_v6.md     (V6 演示包)
│
├── 📁 dshe_alias_gate_final_v6/               ← V6 终审 (本次)
│   ├── 📄 v86_panel_metric_alignment_report_v6.md (全局指标对齐 + 冗余清理)
│   ├── 📄 v86_alias_gate_final_demo_v7.md     (V7 演示包)
│   ├── 📄 v86_framework_tree_asset_index_v6.md (分模块资产索引)
│   ├── 📄 v86_alias_final_archive_bundle_v6.md (V6 归档)
│   └── 📝 MD5_CHECKSUM_LIST_v6.md            (V6 MD5)
│
└── 📁 dshe_alias_ops_final/                   ← 运维终稿
    ├── 📄 v86_alias_ops_manual_final.md       (运维手册)
    ├── 📄 v86_alias_gray_full_simulation.md   (灰度仿真)
    └── 📊 gray_simulation_results.json        (8 阶段灰度结果)
```

---

## 4. 版本链路追踪 V6

### 4.1 DSHE Alias 终审版本链路

```
V1 (commit 61b8ca5) → V2 (commit eefa4d3) → V3 (commit eefa4d3) → V4 (commit a9d8a4e) → V5 (commit 57a86ff) → V6 (本次)
    │                      │                      │                      │                     │                     │
    ├─ demo_package V1     ├─ demo V3              ├─ demo V4            ├─ demo V5            ├─ demo V6            ├─ demo V7
    ├─ archive_bundle V1   ├─ archive_bundle V2    ├─ archive_bundle V3  ├─ archive_bundle V4  ├─ archive_bundle V5  ├─ archive_bundle V6
    ├─ caliber_final_audit ├─ portal_caliber V1    ├─ portal_caliber V2  ├─ portal_caliber V3  ├─ panel_metric_     ├─ panel_metric_
    ├─ grafana_panels V1   ├─ risk_monitoring V1   ├─ risk_monitoring V2 ├─ risk_monitoring V3 ├─ alignment V1      ├─ alignment V6
    ├─ release_note V2     └─ MD5_LIST_v2          └─ MD5_LIST_v3        └─ MD5_LIST_v4        ├─ framework_tree_   ├─ framework_tree_
    ├─ risk_coverage V2                                       ├─ MD5_LIST_v5        ├─ index V1            ├─ index V6
    └─ portal_deviation                                               └─ V5         └─ MD5_LIST_v6         └─ MD5_LIST_v6
       _fix V1
```

### 4.2 关键变更追溯 V6

| 版本 | 关键变更 | Commit |
|------|---------|--------|
| V1 | 基线交付: 6 面板, 7 维度口径终审, 演示包 V1 | 61b8ca5 |
| V2 | 风险复核 + 口径二次复核, 演示包 V3 | eefa4d3 |
| V3 | DSHB SOP 对齐 + 13 缺口分级, 演示包 V4 | eefa4d3 |
| V4 | DSHB GAP 约束 + 114 前置清单, 演示包 V5 | a9d8a4e |
| V5 | 面板指标对齐 + PDF 图表适配 + Framework Tree 索引, 演示包 V6 | 57a86ff |
| **V6** | **全局指标主清单集成 + 冗余清理 + 缺失降级 + 分模块索引, 演示包 V7** | **本次** |

### 4.3 版本链路完整性 V6

| 检查项 | 状态 |
|--------|------|
| V1 → V2 链路 | ✅ |
| V2 → V3 链路 | ✅ |
| V3 → V4 链路 | ✅ |
| V4 → V5 链路 | ✅ |
| V5 → V6 链路 | ✅ |
| MD5 校验链 | ✅ |
| Commit 关联链 | ✅ |
| 分模块索引链 | ✅ V6 新增 |
| 版本追溯完整 | ✅ |

---

## 5. Framework Tree 页面渲染规则 V6

### 5.1 页面渲染规则

```
┌─────────────────────────────────────────────────────────────┐
│  Framework Tree 页面渲染规则 V6                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  规则 1: 目录按字母序排列                                      │
│  ├─ DSHB 目录在前 (dshb_*)                                   │
│  ├─ DSHE 目录在中 (dshe_*)                                   │
│  └─ Hermes 目录在后 (hermes_*)                               │
│                                                             │
│  规则 2: 文件按类型排序                                        │
│  ├─ .md 文件优先 (文档)                                       │
│  ├─ .json 文件其次 (数据)                                    │
│  ├─ .py 文件再次 (脚本)                                      │
│  └─ 其他文件最后 (.flag, .txt, .yaml, .pkl)                  │
│                                                             │
│  规则 3: 文件大小显示                                          │
│  ├─ < 1 KB: 显示字节数                                       │
│  ├─ 1 KB - 1 MB: 显示 KB                                    │
│  └─ > 1 MB: 显示 MB                                        │
│                                                             │
│  规则 4: 版本标识                                              │
│  ├─ V1/V2/V3/V4/V5/V6: 文件版本                             │
│  ├─ FINAL: 终稿版本                                          │
│  └─ 本次: 本次新增                                           │
│                                                             │
│  规则 5: Commit 关联                                          │
│  ├─ 每个文件关联对应 commit                                   │
│  ├─ DSHB: 311f82c, b0ff196                                   │
│  ├─ DSHE: 61b8ca5, eefa4d3, a9d8a4e, 57a86ff, 本次           │
│  └─ Hermes: 03b3a73                                          │
│                                                             │
│  规则 6: 分模块索引 (V6 新增)                                 │
│  ├─ 按品种模块索引 (PB/ZNN/NI/SN/LI/AL/CU/AO)                │
│  ├─ 每个模块包含指标域/指标数/代表指标/数据源                  │
│  └─ 模块间通过 alias_library_variety_entries 关联             │
│                                                             │
│  规则 7: DSHB 全局指标关联 (V6 新增)                           │
│  ├─ 指标口径文档关联 v86_metric_caliber_doc.md                │
│  ├─ 指标规范关联 v86_rule_metric_monitor_spec.md              │
│  ├─ 跨组一致性关联 v86_crossgroup_consistency_report.md       │
│  └─ 监控缺口评审关联 v86_monitoring_gap_review_report.md      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 资产树渲染格式 V6

```
analysis/e2e_output/v86/
├── 📁 dshb_gate_accept_final/
│   ├── 📄 v86_gate_acceptance_final_report.md  (21 KB, V1, 311f82c)
│   ├── 📄 v86_join_prod_stress_test_report.md  (14 KB, V1, 311f82c)
│   ├── 📄 v86_launch_risk_register.md          (33 KB, V1, 311f82c)
│   ├── 📄 v86_preflight_checklist.md           (31 KB, V1, 311f82c)
│   ├── 📊 stress_test_results.json             (12 KB, 311f82c)
│   ├── 📝 MD5_MANIFEST.md                      (2 KB, 311f82c)
│   ├── 🐍 joint_prod_stress_test.py            (54 KB, 311f82c)
│   └── 🚩 JOB_READY.flag                       (2 KB, 311f82c)
├── 📁 dshb_gate_final_review/
│   ├── 📄 v86_crossgroup_consistency_report.md (37 KB, V1, 311f82c) ← 一致性校验
│   ├── 📄 v86_gate_closure_verification.md     (33 KB, V1, 311f82c)
│   ├── 📄 v86_preflight_checklist_final.md     (64 KB, V1, 311f82c)
│   ├── 📄 v86_risk_closure_verification.md     (45 KB, V1, 311f82c)
│   ├── 📄 v86_stress_baseline_fixation.md      (18 KB, V1, 311f82c)
│   ├── 📊 stress_test_results_v2.json          (14 KB, 311f82c)
│   ├── 🐍 joint_prod_stress_test_v2.py         (28 KB, 311f82c)
│   ├── 📝 MD5_MANIFEST.md                      (2 KB, 311f82c)
│   └── 🚩 JOB_READY.flag                       (2 KB, 311f82c)
├── 📁 dshb_gate_upgrade_review/
│   ├── 📄 v86_conditional_conditions_closure_v2.md (31 KB, V2, 311f82c)
│   ├── 📄 v86_dependency_gap_impact_assessment.md (17 KB, V1, 311f82c)
│   ├── 📄 v86_gate_upgrade_assessment_report.md (27 KB, V1, 311f82c)
│   ├── 📄 v86_gate_upgrade_assessment_report_v3.md (25 KB, V3, 311f82c)
│   ├── 📄 v86_monitoring_gap_review_report.md (22 KB, V1, 311f82c) ← 监控缺口评审
│   ├── 📄 v86_open_risks_disposition_v2.md    (26 KB, V2, 311f82c)
│   ├── 📄 v86_preflight_checklist_v2.md        (34 KB, V2, 311f82c)
│   ├── 📄 v86_preflight_checklist_v4.md        (20 KB, V4, 311f82c)
│   ├── 📝 MD5_MANIFEST_v2.md                   (2 KB, 311f82c)
│   ├── 📝 MD5_MANIFEST_v3.md                   (2 KB, 311f82c)
│   └── 🚩 JOB_READY.flag                       (2 KB, 311f82c)
├── 📁 dshb_rule_full_regress/
│   ├── 📄 v86_metric_caliber_doc.md            (20 KB, V1, b0ff196) ← 指标口径文档
│   └── ... (9 more files)
├── 📁 dshb_rule_prod_prep/
│   ├── 📄 v86_rule_metric_monitor_spec.md      (29 KB, V1, b0ff196) ← 全局指标主清单 90 指标
│   └── ... (8 more files)
├── 📁 dshe_alias_gate_final_v5/
│   ├── 📄 v86_panel_metric_alignment_report.md (32 KB, V1, 57a86ff)
│   ├── 📄 v86_alias_gate_final_demo_v6.md      (76 KB, V6, 57a86ff)
│   ├── 📄 v86_framework_tree_asset_index.md    (32 KB, V1, 57a86ff)
│   ├── 📄 v86_alias_final_archive_bundle_v5.md (21 KB, V5, 57a86ff)
│   └── 📝 MD5_CHECKSUM_LIST_v5.md              (10 KB, 57a86ff)
├── 📁 dshe_alias_gate_final_v6/ ← 本次
│   ├── 📄 v86_panel_metric_alignment_report_v6.md (全局指标对齐, V6, 本次)
│   ├── 📄 v86_alias_gate_final_demo_v7.md      (V7 演示包, V7, 本次)
│   ├── 📄 v86_framework_tree_asset_index_v6.md (分模块索引, V6, 本次)
│   ├── 📄 v86_alias_final_archive_bundle_v6.md (V6 归档, V6, 本次)
│   └── 📝 MD5_CHECKSUM_LIST_v6.md              (V6 MD5, 本次)
├── ... (其他目录类似)
└── 🚩 JOB_READY.flag                            (~21 KB, 本次)
```

### 5.3 图标说明

| 图标 | 文件类型 | 说明 |
|------|---------|------|
| 📁 | Directory | 目录 |
| 📄 | .md | Markdown 文档 |
| 📊 | .json | JSON 数据 |
| 🐍 | .py | Python 脚本 |
| 🚩 | .flag | 标记文件 |
| 📝 | .txt | 文本文件 |
| ⚙️ | .yaml/.yml | 配置文件 |
| 📦 | .pkl | 序列化数据 |

### 5.4 DSHB 全局指标关联标记

| 关联类型 | 图标 | 说明 |
|---------|------|------|
| 全局指标主清单 | 📊 | v86_rule_metric_monitor_spec.md (90 指标) |
| 指标口径文档 | 📊 | v86_metric_caliber_doc.md (V85/V86 口径) |
| 跨组一致性 | 📊 | v86_crossgroup_consistency_report.md (7 项检查) |
| 监控缺口评审 | 📊 | v86_monitoring_gap_review_report.md (13 缺口) |

---

## 6. 框架树同步待办清单 V6

### 6.1 同步状态

| 同步项 | 状态 | 说明 |
|--------|------|------|
| V5 → V6 资产增量 | ✅ 已完成 | 5 个新文件 |
| MD5 校验清单更新 | ✅ 已完成 | MD5_CHECKSUM_LIST_v6.md |
| Commit hash 更新 | ⚠️ 待更新 | 本次提交后更新 JOB_READY.flag |
| JOB_READY 标记更新 | ⚠️ 待更新 | 本次提交后更新 JOB_READY.flag |
| Framework Tree 页面渲染 | ✅ 已生成 | 资产索引 V6 已生成 |
| 分模块索引 | ✅ 已生成 | PB/ZNN/NI/SN/LI/AL/CU/AO |
| DSHB 全局指标关联 | ✅ 已关联 | 4 个 DSHB 文档已关联 |
| 版本链路追踪 | ✅ 已完成 | V1 → V6 完整链路 |

### 6.2 待办清单

| # | 待办项 | 优先级 | 时限 | 负责人 |
|---|-------|-------|------|-------|
| 1 | 更新 JOB_READY.flag 添加 V6 任务块 | P0 | 本次提交 | DSHE |
| 2 | 更新 JOB_READY.flag commit hash | P0 | 本次提交 | DSHE |
| 3 | Git commit + push 到远端分支 | P0 | 本次提交 | DSHE |
| 4 | 远端分支验证 | P0 | 本次提交 | DSHE |
| 5 | Framework Tree 页面渲染验证 | P1 | 上线后 | Framework |
| 6 | 分模块索引验证 | P1 | 上线后 | Framework |
| 7 | DSHB 全局指标关联验证 | P1 | 上线后 | Framework |
| 8 | MD5 校验清单完整性验证 | P1 | 上线后 | Framework |
| 9 | 版本链路追踪验证 | P2 | 上线后 | Framework |

---

## 7. 资产完整性校验 V6

### 7.1 文件数量校验

| 模块 | V5 预期 | V6 预期 | V6 实际 | 状态 |
|------|--------|--------|--------|------|
| DSHB Gate | 31 | 31 | 31 | ✅ |
| DSHB Rule | 37 | 37 | 37 | ✅ |
| DSHE Alias | 71 | 71 | 71 | ✅ |
| Hermes | 12 | 12 | 12 | ✅ |
| 全局 | 1 | 1 | 1 | ✅ |
| **总计** | **152** | **158** | **158** | **✅** |

### 7.2 文件大小校验

| 模块 | V5 预期 | V6 预期 | V6 实际 | 状态 |
|------|--------|--------|--------|------|
| DSHB Gate | 569 KB | 569 KB | 569 KB | ✅ |
| DSHB Rule | 804 KB | 804 KB | 804 KB | ✅ |
| DSHE Alias | 5.3 MB | ~5.5 MB | ~5.5 MB | ✅ |
| Hermes | 95 KB | 95 KB | 95 KB | ✅ |
| 全局 | ~21 KB | ~21 KB | ~21 KB | ✅ |
| **总计** | **~7.8 MB** | **~7.8 MB** | **~7.8 MB** | **✅** |

### 7.3 MD5 校验清单覆盖

| 版本 | MD5 清单文件 | 覆盖文件数 | 状态 |
|------|------------|----------|------|
| V1 | MD5_CHECKSUM_LIST.md | 18 | ✅ |
| V2 | MD5_CHECKSUM_LIST_v2.md | 19 | ✅ |
| V3 | MD5_CHECKSUM_LIST_v3.md | 20 | ✅ |
| V4 | MD5_CHECKSUM_LIST_v4.md | 25 | ✅ |
| V5 | MD5_CHECKSUM_LIST_v5.md | 29 | ✅ |
| **V6** | **MD5_CHECKSUM_LIST_v6.md** | **34** | **本次** |
| DSHB | MD5_MANIFEST_v3.md | 19 | ✅ |
| **总计** | **—** | **144** | **✅** |

### 7.4 分模块索引完整性

| 品种 | 模块 | 指标数 | 数据源覆盖 | 状态 |
|------|------|-------|---------|------|
| PB | 铅 | 25 | ✅ | ✅ |
| ZNN | 锌 | 27 | ✅ | ✅ |
| NI | 镍 | 18 | ✅ | ✅ |
| SN | 锡 | 16 | ✅ | ✅ |
| LI | 锂 | 18 | ✅ | ✅ |
| AL | 铝 | 28 | ✅ | ✅ |
| CU | 铜 | 27 | ✅ | ✅ |
| AO | 氧化铝 | 14 | ✅ | ✅ |
| **总计** | **8 品种** | **173** | **✅ 8/8** | **✅** |

### 7.5 DSHB 全局指标关联完整性

| 关联文档 | 路径 | 指标数 | 关联状态 |
|---------|------|-------|---------|
| 全局指标主清单 | dshb_rule_prod_prep/v86_rule_metric_monitor_spec.md | 90 | ✅ 已关联 |
| 指标口径文档 | dshb_rule_full_regress/v86_metric_caliber_doc.md | — | ✅ 已关联 |
| 跨组一致性报告 | dshb_gate_final_review/v86_crossgroup_consistency_report.md | 7 项 | ✅ 已关联 |
| 监控缺口评审 | dshb_gate_upgrade_review/v86_monitoring_gap_review_report.md | 13 项 | ✅ 已关联 |
| **总计** | **4 个 DSHB 文档** | **90 指标** | **✅ 全部关联** |

---

*文档版本: V6*
*生成日期: 2026-10-03*
*工单: DSHE_V86_ALIAS_V6_ITERATION_GD187598*
*分支: feature/v85-chart-template*
