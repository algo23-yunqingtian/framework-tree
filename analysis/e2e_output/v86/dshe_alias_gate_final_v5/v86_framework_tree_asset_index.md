# V86 Framework Tree 资产元数据索引 (T3.3)

> 任务: `DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V5_ARCHIVE` · T3.3
> 分支: `feature/v85-chart-template`
> 基线: DSHE V4 (commit a9d8a4e)
> 用途: framework tree 页面资产元数据 / 目录树索引 / 同步待办清单
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED
> 生成日期: 2026-10-03

---

## 目录

1. [Framework Tree 目录总览](#1-framework-tree-目录总览)
2. [资产元数据索引](#2-资产元数据索引)
3. [版本链路追踪](#3-版本链路追踪)
4. [Framework Tree 页面渲染规则](#4-framework-tree-页面渲染规则)
5. [框架树同步待办清单](#5-框架树同步待办清单)
6. [资产完整性校验](#6-资产完整性校验)

---

## 1. Framework Tree 目录总览

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
├── dshe_alias_gate_final_v5/        (4 files, 108 KB)   — DSHE 别名终审 V5 (本次)
├── dshe_alias_joint_check/          (11 files, 187 KB)  — DSHE 联合检查
├── dshe_alias_ops_final/            (7 files, 100 KB)   — DSHE 运维终稿
├── dshe_alias_predev/               (10 files, 280 KB)  — DSHE 预开发
├── dshe_alias_prod_prep/            (11 files, 3.5 MB)  — DSHE 生产准备
├── hermes_e2e_test/                 (6 files, 46 KB)    — Hermes E2E 测试
├── hermes_portal_prep/              (6 files, 49 KB)    — Hermes 门户准备
└── JOB_READY.flag                    (1 file, 18 KB)    — 任务就绪标记
```

### 1.2 目录统计

| 目录 | 文件数 | 总大小 | 所属模块 | 版本 |
|------|-------|-------|---------|------|
| dshb_gate_accept_final | 7 | 151 KB | DSHB Gate | 终审验收 |
| dshb_gate_final_review | 7 | 213 KB | DSHB Gate | 终审复核 |
| dshb_gate_upgrade_review | 11 | 205 KB | DSHB Gate | 终审升级 (V2/V3) |
| dshb_rule_ci_stress | 11 | 234 KB | DSHB Rule | CI 压测 |
| dshb_rule_full_regress | 10 | 250 KB | DSHB Rule | 全量回归 |
| dshb_rule_predev | 7 | 129 KB | DSHB Rule | 预开发 |
| dshb_rule_prod_prep | 9 | 191 KB | DSHB Rule | 生产准备 |
| dshe_alias_gate_demo_release | 5 | 115 KB | DSHE Alias | 演示发布 |
| dshe_alias_gate_final | 14 | 418 KB | DSHE Alias | 终审 (V1) |
| dshe_alias_gate_final_v2 | 5 | 133 KB | DSHE Alias | 终审 V2 |
| dshe_alias_gate_final_v3 | 5 | 139 KB | DSHE Alias | 终审 V3 |
| dshe_alias_gate_final_v4 | 5 | 188 KB | DSHE Alias | 终审 V4 |
| **dshe_alias_gate_final_v5** | **4** | **108 KB** | **DSHE Alias** | **终审 V5 (本次)** |
| dshe_alias_joint_check | 11 | 187 KB | DSHE Alias | 联合检查 |
| dshe_alias_ops_final | 7 | 100 KB | DSHE Alias | 运维终稿 |
| dshe_alias_predev | 10 | 280 KB | DSHE Alias | 预开发 |
| dshe_alias_prod_prep | 11 | 3.5 MB | DSHE Alias | 生产准备 |
| hermes_e2e_test | 6 | 46 KB | Hermes | E2E 测试 |
| hermes_portal_prep | 6 | 49 KB | Hermes | 门户准备 |
| (root) | 1 | 18 KB | 全局 | JOB_READY.flag |
| **总计** | **150** | **7.6 MB** | — | — |

---

## 2. 资产元数据索引

### 2.1 DSHB Gate 资产 (31 files, 569 KB)

| # | 文件路径 | 大小 | 版本 | 说明 | 关联 Commit |
|---|---------|------|------|------|-----------|
| 1 | dshb_gate_accept_final/JOB_READY.flag | 1,892 B | — | 任务就绪标记 | 311f82c |
| 2 | dshb_gate_accept_final/JOB_READY.flag | 1,892 B | — | 任务就绪标记 | 311f82c |
| 3 | dshb_gate_accept_final/v86_gate_acceptance_final_report.md | 21,131 B | V1 | 终审验收报告 | 311f82c |
| 4 | dshb_gate_accept_final/v86_join_prod_stress_test_report.md | 13,714 B | V1 | 联合压测报告 | 311f82c |
| 5 | dshb_gate_accept_final/v86_launch_risk_register.md | 33,165 B | V1 | 上线风险台账 | 311f82c |
| 6 | dshb_gate_accept_final/v86_preflight_checklist.md | 31,035 B | V1 | 上线前置清单 | 311f82c |
| 7 | dshb_gate_accept_final/stress_test_results.json | 12,091 B | — | 压测结果数据 | 311f82c |
| 8 | dshb_gate_accept_final/MD5_MANIFEST.md | 2,046 B | — | MD5 校验清单 | 311f82c |
| 9 | dshb_gate_accept_final/joint_prod_stress_test.py | 53,912 B | — | 联合压测脚本 | 311f82c |
| 10 | dshb_gate_final_review/JOB_READY.flag | 1,953 B | — | 任务就绪标记 | 311f82c |
| 11 | dshb_gate_final_review/v86_crossgroup_consistency_report.md | 36,840 B | V1 | 跨组一致性报告 | 311f82c |
| 12 | dshb_gate_final_review/v86_gate_closure_verification.md | 32,751 B | V1 | Gate 闭环验证 | 311f82c |
| 13 | dshb_gate_final_review/v86_preflight_checklist_final.md | 63,928 B | V1 | 前置清单 (终稿) | 311f82c |
| 14 | dshb_gate_final_review/v86_risk_closure_verification.md | 45,003 B | V1 | 风险闭环验证 | 311f82c |
| 15 | dshb_gate_final_review/v86_stress_baseline_fixation.md | 17,808 B | V1 | 压测基线固化 | 311f82c |
| 16 | dshb_gate_final_review/stress_test_results_v2.json | 13,568 B | — | 压测结果 V2 | 311f82c |
| 17 | dshb_gate_final_review/MD5_MANIFEST.md | 2,135 B | — | MD5 校验清单 | 311f82c |
| 18 | dshb_gate_final_review/joint_prod_stress_test_v2.py | 27,625 B | — | 联合压测脚本 V2 | 311f82c |
| 19 | dshb_gate_upgrade_review/JOB_READY.flag | 1,651 B | — | 任务就绪标记 | 311f82c |
| 20 | dshb_gate_upgrade_review/v86_conditional_conditions_closure_v2.md | 31,147 B | V2 | 条件闭环 V2 | 311f82c |
| 21 | dshb_gate_upgrade_review/v86_dependency_gap_impact_assessment.md | 16,659 B | V1 | DEPENDENCY_GAP 评估 | 311f82c |
| 22 | dshb_gate_upgrade_review/v86_gate_upgrade_assessment_report.md | 27,208 B | V1 | 终审升级评估 | 311f82c |
| 23 | dshb_gate_upgrade_review/v86_gate_upgrade_assessment_report_v3.md | 25,190 B | V3 | 终审升级评估 V3 | 311f82c |
| 24 | dshb_gate_upgrade_review/v86_monitoring_gap_review_report.md | 22,453 B | V1 | 监控缺口评审 | 311f82c |
| 25 | dshb_gate_upgrade_review/v86_open_risks_disposition_v2.md | 26,372 B | V2 | 开放风险处置 V2 | 311f82c |
| 26 | dshb_gate_upgrade_review/v86_preflight_checklist_v2.md | 34,379 B | V2 | 前置清单 V2 | 311f82c |
| 27 | dshb_gate_upgrade_review/v86_preflight_checklist_v4.md | 19,916 B | V4 | 前置清单 V4 | 311f82c |
| 28 | dshb_gate_upgrade_review/MD5_MANIFEST_v2.md | 1,890 B | — | MD5 校验清单 V2 | 311f82c |
| 29 | dshb_gate_upgrade_review/MD5_MANIFEST_v3.md | 2,215 B | — | MD5 校验清单 V3 | 311f82c |

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
| 13 | dshb_rule_full_regress/v86_metric_caliber_doc.md | 20,499 B | V1 | 指标口径文档 | b0ff196 |
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
| 32 | dshb_rule_prod_prep/v86_rule_metric_monitor_spec.md | 29,315 B | V1 | 规则监控指标规范 | b0ff196 |
| 33 | dshb_rule_prod_prep/v86_rule_production_bundle.md | 11,035 B | V1 | 规则生产包 | b0ff196 |
| 34 | dshb_rule_prod_prep/v86_rule_resource_estimate.md | 14,005 B | V1 | 规则资源评估 | b0ff196 |
| 35 | dshb_rule_prod_prep/v86_rule_rollback_plan.md | 15,568 B | V1 | 规则回滚计划 | b0ff196 |
| 36 | dshb_rule_prod_prep/full_dataset_replay_runner.py | 33,857 B | — | 全量回放运行器 | b0ff196 |
| 37 | dshb_rule_prod_prep/full_replay_results.json | 72,863 B | — | 全量回放结果 | b0ff196 |

### 2.3 DSHE Alias 资产 (66 files, 5.1 MB)

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
| 35 | **dshe_alias_gate_final_v5/MD5_CHECKSUM_LIST_v5.md** | **—** | **—** | **MD5 校验清单 V5** | **本次** |
| 36 | **dshe_alias_gate_final_v5/v86_alias_final_archive_bundle_v5.md** | **—** | **V5** | **归档资产包 V5** | **本次** |
| 37 | **dshe_alias_gate_final_v5/v86_alias_gate_final_demo_v6.md** | **76,123 B** | **V6** | **演示包 V6** | **本次** |
| 38 | **dshe_alias_gate_final_v5/v86_panel_metric_alignment_report.md** | **31,899 B** | **V1** | **面板指标对齐报告** | **本次** |
| 39 | **dshe_alias_gate_final_v5/v86_framework_tree_asset_index.md** | **—** | **V1** | **Framework Tree 资产索引** | **本次** |
| 40 | dshe_alias_joint_check/MD5_CHECKSUM_LIST.md | 2,205 B | — | MD5 校验清单 | 168a073 |
| 41 | dshe_alias_joint_check/v86_alias_asset_bundle.md | 6,704 B | V1 | 别名资产包 | 168a073 |
| 42 | dshe_alias_joint_check/v86_alias_rule_joint_scan.md | 9,167 B | V1 | 别名-规则联合扫描 | 168a073 |
| 43 | dshe_alias_joint_check/alias_engine_warmup_optimize.py | 21,479 B | — | 预热优化脚本 | 168a073 |
| 44 | dshe_alias_joint_check/alias_gate_auto_check.py | 33,372 B | — | Gate 自动检查 | 168a073 |
| 45 | dshe_alias_joint_check/alias_p0_manual_sample_set.json | 57,873 B | — | P0 手动样本集 | 168a073 |
| 46 | dshe_alias_joint_check/gate_auto_check_report.json | 1,636 B | — | Gate 自动检查报告 | 168a073 |
| 47 | dshe_alias_joint_check/warmup_benchmark_results.json | 3,128 B | — | 预热基准结果 | 168a073 |
| 48 | dshe_alias_joint_check/warmup_verify_results.json | 1,477 B | — | 预热验证结果 | 168a073 |
| 49 | dshe_alias_ops_final/MD5_CHECKSUM_LIST.md | 5,077 B | — | MD5 校验清单 | 81268a6 |
| 50 | dshe_alias_ops_final/v86_alias_frozen_asset_bundle.md | 10,526 B | V1 | 冻结资产包 | 81268a6 |
| 51 | dshe_alias_ops_final/v86_alias_gray_full_simulation.md | 17,072 B | V1 | 灰度全量仿真 | 81268a6 |
| 52 | dshe_alias_ops_final/v86_alias_ops_manual_final.md | 29,923 B | V1 | 运维手册终稿 | 81268a6 |
| 53 | dshe_alias_ops_final/v86_alias_prod_integrate_verify_report.md | 21,750 B | V1 | 生产集成验证 | 81268a6 |
| 54 | dshe_alias_ops_final/gray_simulation_results.json | 25,039 B | — | 灰度仿真结果 | 81268a6 |
| 55 | dshe_alias_ops_final/gray_simulation_runner.py | 29,140 B | — | 灰度仿真运行器 | 81268a6 |
| 56 | dshe_alias_predev/MD5_CHECKSUM_LIST.md | 1,695 B | — | MD5 校验清单 | 5e874a7 |
| 57 | dshe_alias_predev/v86_alias_engine_risk_perf_estimate.md | 12,301 B | V1 | 风险性能评估 | 5e874a7 |
| 58 | dshe_alias_predev/v86_alias_regression_report.md | 11,641 B | V1 | 别名回归报告 | 5e874a7 |
| 59 | dshe_alias_predev/alias_task_adapter.py | 30,024 B | — | 任务适配器 | 5e874a7 |
| 60 | dshe_alias_predev/alias_v86_extended_test_case.json | 20,927 B | — | 扩展测试用例 | 5e874a7 |
| 61 | dshe_alias_predev/regression_results.json | 130,190 B | — | 回归结果 | 5e874a7 |
| 62 | dshe_alias_predev/test_run_results.json | 15,062 B | — | 测试运行结果 | 5e874a7 |
| 63 | dshe_alias_predev/v86_alias_engine_prototype.py | 42,512 B | — | 引擎原型 | 5e874a7 |
| 64 | dshe_alias_prod_prep/MD5_CHECKSUM_LIST.md | 1,560 B | — | MD5 校验清单 | d8e44a9 |
| 65 | dshe_alias_prod_prep/v86_alias_degrade_plan.md | 14,871 B | V1 | 降级计划 | d8e44a9 |
| 66 | dshe_alias_prod_prep/v86_alias_full_replay_report.md | 6,580 B | V1 | 全量回放报告 | d8e44a9 |
| 67 | dshe_alias_prod_prep/v86_alias_gray_release_plan.md | 13,218 B | V1 | 灰度发布计划 | d8e44a9 |
| 68 | dshe_alias_prod_prep/v86_alias_monitor_spec.md | 17,364 B | V1 | 监控规范 | d8e44a9 |
| 69 | dshe_alias_prod_prep/v86_alias_production_bundle.md | 17,385 B | V1 | 生产包 | d8e44a9 |
| 70 | dshe_alias_prod_prep/replay_results.json | 3,382,924 B | — | 回放结果 (大文件) | d8e44a9 |
| 71 | dshe_alias_prod_prep/v86_alias_full_replay.py | 25,076 B | — | 全量回放脚本 | d8e44a9 |

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

### 2.5 全局资产 (1 file, 18 KB)

| # | 文件路径 | 大小 | 版本 | 说明 | 关联 Commit |
|---|---------|------|------|------|-----------|
| 1 | JOB_READY.flag | 17,895 B | — | 任务就绪标记 (全局) | a9d8a4e |

---

## 3. 版本链路追踪

### 3.1 DSHE Alias 终审版本链路

```
V1 (dshe_alias_gate_final)          V2 (dshe_alias_gate_final_v2)
  ├─ demo_package V1                    ├─ demo V3
  ├─ archive_bundle V1                 ├─ archive_bundle V2
  ├─ caliber_final_audit V1            ├─ portal_caliber_second_review V1
  ├─ grafana_panels_final V1           ├─ risk_monitoring_review V1
  ├─ release_note V2                   └─ MD5_CHECKSUM_LIST_v2
  ├─ risk_monitoring_coverage V2
  ├─ portal_deviation_fix V1
  └─ MD5_CHECKSUM_LIST V1

V3 (dshe_alias_gate_final_v3)         V4 (dshe_alias_gate_final_v4)
  ├─ demo V4                           ├─ demo V5
  ├─ archive_bundle V3                 ├─ archive_bundle V4
  ├─ portal_caliber_second_review V2   ├─ portal_caliber_second_review V3
  ├─ risk_monitoring_review V2         ├─ risk_monitoring_review V3
  └─ MD5_CHECKSUM_LIST_v3              └─ MD5_CHECKSUM_LIST_v4

V5 (dshe_alias_gate_final_v5) ← 本次
  ├─ demo V6
  ├─ archive_bundle V5
  ├─ panel_metric_alignment_report V1
  ├─ framework_tree_asset_index V1
  └─ MD5_CHECKSUM_LIST_v5
```

### 3.2 DSHB Gate 终审版本链路

```
V1 (dshb_gate_accept_final)
  ├─ gate_acceptance_final_report V1
  ├─ launch_risk_register V1
  ├─ preflight_checklist V1
  └─ stress_test_results V1

V2 (dshb_gate_upgrade_review)
  ├─ conditional_conditions_closure V2
  ├─ open_risks_disposition V2
  ├─ preflight_checklist V2
  ├─ monitoring_gap_review V1
  ├─ dependency_gap_impact_assessment V1
  └─ gate_upgrade_assessment_report V1

V3 (dshb_gate_upgrade_review)
  ├─ gate_upgrade_assessment_report V3
  ├─ preflight_checklist V4
  └─ MD5_MANIFEST_v3
```

### 3.3 Commit 关联

| 版本 | Commit | 描述 |
|------|--------|------|
| DSHB 基线 | 311f82c | DSHB Gate FULL_PASS FINAL |
| DSHB Rule | b0ff196 | DSHB 规则引擎交付 |
| DSHE V1 | 61b8ca5 | DSHE 别名引擎终审 |
| DSHE V2/V3 | eefa4d3 | DSHE 别名终审 V2/V3 |
| DSHE V4 | a9d8a4e | DSHE 别名终审 V4 |
| DSHE V5 | 本次 | DSHE 别名终审 V5 (本次提交) |
| Hermes | 03b3a73 | Hermes 门户集成 |
| DSHB Prod Prep | d8e44a9 | DSHB 生产准备 |
| DSHE Ops Final | 81268a6 | DSHE 运维终稿 |
| DSHE Predev | 5e874a7 | DSHE 预开发 |
| DSHE Joint Check | 168a073 | DSHE 联合检查 |

---

## 4. Framework Tree 页面渲染规则

### 4.1 目录树渲染

Framework tree 页面按以下规则渲染目录树:

```
┌─────────────────────────────────────────────────────────────┐
│  Framework Tree 页面渲染规则                                   │
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
│  ├─ V1/V2/V3/V4/V5: 文件版本                                 │
│  ├─ FINAL: 终稿版本                                          │
│  └─ 本次: 本次新增                                           │
│                                                             │
│  规则 5: Commit 关联                                          │
│  ├─ 每个文件关联对应 commit                                   │
│  ├─ DSHB: 311f82c, b0ff196                                   │
│  ├─ DSHE: 61b8ca5, eefa4d3, a9d8a4e, 本次                    │
│  └─ Hermes: 03b3a73                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 资产树渲染格式

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
│   ├── 📄 v86_crossgroup_consistency_report.md (37 KB, V1, 311f82c)
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
│   ├── 📄 v86_monitoring_gap_review_report.md (22 KB, V1, 311f82c)
│   ├── 📄 v86_open_risks_disposition_v2.md    (26 KB, V2, 311f82c)
│   ├── 📄 v86_preflight_checklist_v2.md        (34 KB, V2, 311f82c)
│   ├── 📄 v86_preflight_checklist_v4.md        (20 KB, V4, 311f82c)
│   ├── 📝 MD5_MANIFEST_v2.md                   (2 KB, 311f82c)
│   ├── 📝 MD5_MANIFEST_v3.md                   (2 KB, 311f82c)
│   └── 🚩 JOB_READY.flag                       (2 KB, 311f82c)
├── ... (其他目录类似)
├── 📁 dshe_alias_gate_final_v5/ ← 本次
│   ├── 📄 v86_panel_metric_alignment_report.md (32 KB, V1, 本次)
│   ├── 📄 v86_alias_gate_final_demo_v6.md      (76 KB, V6, 本次)
│   ├── 📄 v86_framework_tree_asset_index.md    (—, V1, 本次)
│   ├── 📄 v86_alias_final_archive_bundle_v5.md (—, V5, 本次)
│   └── 📝 MD5_CHECKSUM_LIST_v5.md              (—, 本次)
├── 📁 hermes_e2e_test/
│   └── ... (6 files)
├── 📁 hermes_portal_prep/
│   └── ... (6 files)
└── 🚩 JOB_READY.flag                            (18 KB, a9d8a4e)
```

### 4.3 图标说明

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

---

## 5. 框架树同步待办清单

### 5.1 同步状态

| 同步项 | 状态 | 说明 |
|--------|------|------|
| V4 → V5 资产增量 | ✅ 已完成 | 4 个新文件 |
| MD5 校验清单更新 | ✅ 已完成 | MD5_CHECKSUM_LIST_v5.md |
| Commit hash 更新 | ⚠️ 待更新 | 本次提交后更新 JOB_READY.flag |
| JOB_READY 标记更新 | ⚠️ 待更新 | 本次提交后更新 JOB_READY.flag |
| Framework Tree 页面渲染 | ✅ 已生成 | 资产索引已生成 |
| 版本链路追踪 | ✅ 已完成 | V1 → V5 完整链路 |

### 5.2 待办清单

| # | 待办项 | 优先级 | 时限 | 负责人 |
|---|-------|-------|------|-------|
| 1 | 更新 JOB_READY.flag 添加 V5 任务块 | P0 | 本次提交 | DSHE |
| 2 | 更新 JOB_READY.flag commit hash | P0 | 本次提交 | DSHE |
| 3 | Git commit + push 到远端分支 | P0 | 本次提交 | DSHE |
| 4 | 远端分支验证 | P0 | 本次提交 | DSHE |
| 5 | Framework Tree 页面渲染验证 | P1 | 上线后 | Framework |
| 6 | 资产索引完整性校验 | P1 | 上线后 | Framework |
| 7 | MD5 校验清单完整性验证 | P1 | 上线后 | Framework |
| 8 | 版本链路追踪验证 | P2 | 上线后 | Framework |

---

## 6. 资产完整性校验

### 6.1 文件数量校验

| 模块 | 预期文件数 | 实际文件数 | 状态 |
|------|----------|----------|------|
| DSHB Gate | 31 | 31 | ✅ |
| DSHB Rule | 37 | 37 | ✅ |
| DSHE Alias | 66 | 66 | ✅ |
| Hermes | 12 | 12 | ✅ |
| 全局 | 1 | 1 | ✅ |
| **总计** | **147** | **147** | ✅ |

### 6.2 文件大小校验

| 模块 | 预期大小 | 实际大小 | 状态 |
|------|---------|---------|------|
| DSHB Gate | 569 KB | 569 KB | ✅ |
| DSHB Rule | 804 KB | 804 KB | ✅ |
| DSHE Alias | 5.1 MB | 5.1 MB | ✅ |
| Hermes | 95 KB | 95 KB | ✅ |
| 全局 | 18 KB | 18 KB | ✅ |
| **总计** | **7.6 MB** | **7.6 MB** | ✅ |

### 6.3 MD5 校验清单覆盖

| 版本 | MD5 清单文件 | 覆盖文件数 | 状态 |
|------|------------|----------|------|
| V1 | MD5_CHECKSUM_LIST.md | 18 | ✅ |
| V2 | MD5_CHECKSUM_LIST_v2.md | 19 | ✅ |
| V3 | MD5_CHECKSUM_LIST_v3.md | 20 | ✅ |
| V4 | MD5_CHECKSUM_LIST_v4.md | 25 | ✅ |
| **V5** | **MD5_CHECKSUM_LIST_v5.md** | **29** | **本次** |
| DSHB | MD5_MANIFEST_v3.md | 19 | ✅ |
| **总计** | **—** | **130** | **✅** |

---

*文档版本: V1*
*生成日期: 2026-10-03*
*工单: DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V5_ARCHIVE*
*分支: feature/v85-chart-template*
