# V85 完整交付包全清单 v2

> 工单: `HERMES_V85_FINAL_DELIVERY_PACKAGE_BUILD_AND_ACCEPTANCE_PORTAL`
> 生成时间: 2026-10-01
> 分支: `feature/v85-chart-template`
> 基于commit: 53c0466 (HERMES) / 1abfa33 (DSHB) / 6fded66 (DSHB)

---

## 一、全部 V85 产物清单

### 1.1 HERMES 产物（5个工单）

#### 工单1: HERMES_V85_PORTAL_FINAL_INTEGRATE_GATE_FULL_CHECK_AND_REVIEW_BATCH_PACKAGE
- **Commit**: d324c76 → rebase后 d324c76
- **目录**: `hermes_portal_gate_final/`
- **产物**:

| # | 文件 | MD5 | 说明 |
|---|------|-----|------|
| 1 | enhanced_review_portal_v5_full.md | 0312bd58 | 门户v5 |
| 2 | portal_operation_manual_v5.md | a78624cb | v5手册 |
| 3 | v85_gate_rerun_check_result.md | f87dfdd1 | Gate46项自检 |
| 4 | mapping_fill_helper_v2.py | cd6a48dc | 回写脚本v2 |
| 5 | batch_export_import.py | 60aa4f7d | 批量工具v1 |
| 6 | indicator_alias_library.csv | 8743cedb | 别名库864条 |
| 7 | high_risk_confusion_pairs.csv | f9783f90 | 混淆对13条 |
| 8 | review_batches_v5/batch_A_review_v5.csv | b3c22860 | Batch-A 97条 |
| 9 | review_batches_v5/batch_B_review_v5.csv | bf4aeb5d | Batch-B 155条 |
| 10 | review_batches_v5/batch_C_review_v5.csv | a5abb21f | Batch-C 236条 |
| 11 | review_batches_v5/review_checklist_v5.md | 5c3b72d5 | v5核对清单 |
| 12 | v85_full_delivery_manifest.md | 441e08db | 交付清单v1 |
| 13 | v85_final_acceptance_summary.md | f8713213 | 验收总结v1 |

#### 工单2: HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP
- **Commit**: 53c0466
- **目录**: `hermes_human_review_tool/`
- **产物**:

| # | 文件 | MD5 | 说明 |
|---|------|-----|------|
| 1 | enhanced_review_portal_v5_review_workbench.md | 5f0f9e3d | 工作台门户 |
| 2 | portal_operation_manual_v6.md | e5cd96c1 | v6手册 |
| 3 | batch_export_import_v2.py | af41c3a9 | 批量工具v2 |
| 4 | batch_tool_manual.md | 53b32962 | 工具手册 |
| 5 | gate_dashboard_spec.md | 7cc518e7 | Gate看板设计 |
| 6 | human_review_archive_spec.md | 6f32b12c | 归档规范 |
| 7 | gate_pre_check.py | 36759393 | Gate预校验 |
| 8 | v85_p0_risk_human_workbook.csv | b7479d78 | P0风险工作表34条 |
| 9 | gate_block_tracker.csv | e6a73572 | Gate跟踪10项 |
| 10 | review_batches_v6/batch_A_review_v6.csv | ddee3151 | Batch-A v6 |
| 11 | review_batches_v6/batch_B_review_v6.csv | f6b422ab | Batch-B v6 |
| 12 | review_batches_v6/batch_C_review_v6.csv | 675f4c8a | Batch-C v6 |
| 13 | review_batches_v6/review_checklist_v6.md | 6143f4ea | v6核对清单 |

#### 工单3: HERMES_V85_FINAL_DELIVERY_PACKAGE_BUILD_AND_ACCEPTANCE_PORTAL（本轮）
- **Commit**: (待提交)
- **目录**: `hermes_v85_final_delivery/`
- **产物**:

| # | 文件 | MD5 | 说明 |
|---|------|-----|------|
| 1 | enhanced_review_portal_v6_final.md | (待计算) | V6验收门户 |
| 2 | portal_operation_manual_v7.md | (待计算) | v7手册 |
| 3 | v85_full_delivery_manifest_v2.md | (本文档) | 全交付清单v2 |
| 4 | v85_delivery_readme.md | (待计算) | 顶层README |
| 5 | delivery_package_check.py | (待计算) | 自检脚本 |
| 6 | delivery_check_result.md | (待计算) | 自检报告 |
| 7 | v85_gate_final_acceptance_report.md | (待计算) | Gate最终报告 |
| 8 | v85_archive_folder_tree.md | (待计算) | 归档目录树 |
| 9 | v85_demo_overview.md | (待计算) | 演示文档 |

### 1.2 DSHB 产物

| 工单 | Commit | 目录 | 核心产出 |
|------|--------|------|---------|
| DSH-B_V85_FULL_CHAIN_INTEGRATE | 6fded66 | dshb_full_integrate/ | 黑名单31规则+488回放+34 P0验证+风险库v1+Gate v1 |
| DSH-B_V85_MISS_RISK_ROOTCAUSE_MINING | 1abfa33 | miss_risk_mining/ | 4条漏拦截根因+5条未命中报告+边界测试集+风险库v2+Gate v2+BL-009a候选 |

### 1.3 DSHB/DSHE 本轮新交付物落盘情况

| 文件 | 来源 | 状态 | 等价替代 |
|------|------|------|---------|
| post_review_playback_summary.md | DSHB | ❌ 未落盘 | full_488_template_playback_result.csv (2721行) |
| v85_risk_db_final_archived.csv | DSHB | ❌ 未落盘 | unified_indicator_risk_db_v2.csv (50条, 50字段) |
| dsh_final_gate_acceptance.md | DSHB | ❌ 未落盘 | dsh_gate_self_check_v2.md (6项Gate v2) |
| alias_sampling_audit_report.md | DSHE | ❌ 未落盘 | indicator_alias_library.csv (864条) |
| v86_alias_engine_full_design.md | DSHE | ❌ 未落盘 | 待V86 |
| alias_test_case_set.json | DSHE | ❌ 未落盘 | blacklist_boundary_testset.json (302条) |

### 1.4 前序工单产物

| 工单 | Commit | 目录 | 核心产出 |
|------|--------|------|---------|
| V85_CHART_TEMPLATE_INTEGRATION | d67aebb | output/v85_chart_online_test/ | 333 HTML + 7份报告 |
| V85_ARTIFICIAL_REVIEW_PREP | 527f597 | output/v85_review_package/ | 5份评审材料 |
| PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE | 96db76d | prep_for_ths_and_auto_check_enhance/ | 语义黑名单+THS静态校验 |
| SEMANTIC_BLACKLIST_UPDATE_AND_PORTAL_UPGRADE | (未提交) | review_package/blacklist_update/ | BL-021修复 |
| THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE | 5012efa | v85_final_integrate/ | 488模板风险绑定+渲染编排v1 |
| V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIMULATION | e491e8d | v85_portal_enhance_render_sim/ | 门户v4+仿真+校验器v3 |
| V85_RENDER_SCRIPT_FIX_AND_MANUAL_REVIEW_PACKAGE | 357e98b | v85_render_fix_review_package/ | 渲染脚本v2+白名单+评审包+Gate |
| V85_THS_INDICATOR_MAPPING_PREP_AND_GATE_GAP_PLAN | 6fc8f11 | v85_ths_mapping_gap_prep/ | 候选映射+Gate缺口计划 |

---

## 二、Git 提交历史

| Commit | 作者 | 说明 |
|--------|------|------|
| 53c0466 | HERMES | V85人工评审工作台+批次v6+Gate预校验 |
| 9670e3b | DSHB | update JOB_READY.flag |
| 1abfa33 | DSHB | 漏检风险根因挖掘+黑名单边界扩展 |
| d324c76 | HERMES | V85门户v5最终集成+Gate46项自检+评审批次v5 |
| 8688b6d | DSHB | DSHB全链路集成+最终Gate准备 |
| 6fded66 | DSHB | DSHB全链路集成+最终Gate准备 |
| 6fc8f11 | HERMES | THS候选映射+Gate缺口计划 |
| 357e98b | HERMES | 渲染脚本v2+白名单+评审包 |
| e491e8d | HERMES | 门户v4+渲染仿真 |
| 5012efa | HERMES | 488模板风险绑定+渲染编排 |
| 96db76d | HERMES | 语义黑名单+THS静态校验 |
| 527f597 | HERMES | 5份评审材料 |
| d67aebb | HERMES | 333 HTML + 7份报告 |

---

## 三、红线文件 MD5

| 文件 | MD5 | 状态 |
|------|-----|------|
| data/indicators_v1.json | 7a864e10e4dd4b54fa2b65aa7df3cf88 | ✅ 只读 |
| data/tree_config.json | 9b98c8afc85578880c3dac1705b70861 | ✅ 只读 |
| ths_adapted_all.json | 5f249a156e357285103060636380fea8 | ✅ 只读 |

---

## 四、责任人

| 角色 | 责任人 | 职责 |
|------|--------|------|
| HERMES | 本agent | 全部产物开发+提交 |
| DSHB | 外部agent | 风险库/黑名单/回放/根因挖掘 |
| DSHE | 外部agent | 别名库/混淆对/质量报告(部分未落盘) |
| 人工评审 | 业务人员 | 488模板评审(待执行) |

---

## 五、T4 约束遵守确认

| 约束 | 状态 |
|------|------|
| 不调用zhiji API | ✅ 零调用 |
| 原始模板只读 | ✅ 红线文件未改 |
| 仅新增文件 | ✅ 无覆盖 |
| 分支锁定 | ✅ feature/v85-chart-template |
| Git提交真实执行 | ✅ (本轮待提交) |
