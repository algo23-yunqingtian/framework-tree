# V85 交付包完整性自检报告

> 生成时间: 2026-10-01T13:13:04.449554
> 校验工具: delivery_package_check.py
> 基线目录: /home/ubuntu/framework-tree/analysis/e2e_output/v85/hermes_v85_final_delivery/..

---

## 一、自检总览

| 校验项 | 通过 | 未通过 | 状态 |
|--------|------|--------|------|
| 文件存在性 | 28 | 0 | ✅ PASS |
| 约束合规 | 3 | 1 | ❌ FAIL |
| 红线文件 | 2 | 0 | ✅ PASS |
| 分支检查 | — | — | ✅ feature/v85-chart-template |

**总判定: ❌ FAIL — 存在不完整项**

---

## 二、文件清单校验

| # | 文件 | 存在 | MD5 | 状态 |
|---|------|------|-----|------|
| 1 | hermes_v85_final_delivery/enhanced_review_portal_v6_final.md | ✅ | `4cd72715` | ✅ |
| 2 | hermes_v85_final_delivery/portal_operation_manual_v7.md | ✅ | `0f43ac4c` | ✅ |
| 3 | hermes_v85_final_delivery/v85_full_delivery_manifest_v2.md | ✅ | `b993222b` | ✅ |
| 4 | hermes_v85_final_delivery/v85_delivery_readme.md | ✅ | `83904cfe` | ✅ |
| 5 | hermes_v85_final_delivery/delivery_package_check.py | ✅ | `d7853485` | ✅ |
| 6 | hermes_v85_final_delivery/v85_gate_final_acceptance_report.md | ✅ | `65b55b15` | ✅ |
| 7 | hermes_v85_final_delivery/v85_archive_folder_tree.md | ✅ | `f178269a` | ✅ |
| 8 | hermes_v85_final_delivery/v85_demo_overview.md | ✅ | `cbc66f07` | ✅ |
| 9 | hermes_human_review_tool/enhanced_review_portal_v5_review_workbench.md | ✅ | `5f0f9e3d` | ✅ |
| 10 | hermes_human_review_tool/portal_operation_manual_v6.md | ✅ | `e5cd96c1` | ✅ |
| 11 | hermes_human_review_tool/batch_export_import_v2.py | ✅ | `af41c3a9` | ✅ |
| 12 | hermes_human_review_tool/batch_tool_manual.md | ✅ | `53b32962` | ✅ |
| 13 | hermes_human_review_tool/gate_dashboard_spec.md | ✅ | `7cc518e7` | ✅ |
| 14 | hermes_human_review_tool/human_review_archive_spec.md | ✅ | `6f32b12c` | ✅ |
| 15 | hermes_human_review_tool/gate_pre_check.py | ✅ | `36759393` | ✅ |
| 16 | hermes_human_review_tool/v85_p0_risk_human_workbook.csv | ✅ | `b7479d78` | ✅ |
| 17 | hermes_human_review_tool/gate_block_tracker.csv | ✅ | `e6a73572` | ✅ |
| 18 | hermes_human_review_tool/review_batches_v6/batch_A_review_v6.csv | ✅ | `ddee3151` | ✅ |
| 19 | hermes_human_review_tool/review_batches_v6/batch_B_review_v6.csv | ✅ | `f6b422ab` | ✅ |
| 20 | hermes_human_review_tool/review_batches_v6/batch_C_review_v6.csv | ✅ | `675f4c8a` | ✅ |
| 21 | hermes_human_review_tool/review_batches_v6/review_checklist_v6.md | ✅ | `6143f4ea` | ✅ |
| 22 | hermes_portal_gate_final/enhanced_review_portal_v5_full.md | ✅ | `0312bd58` | ✅ |
| 23 | hermes_portal_gate_final/portal_operation_manual_v5.md | ✅ | `a78624cb` | ✅ |
| 24 | hermes_portal_gate_final/v85_gate_rerun_check_result.md | ✅ | `f87dfdd1` | ✅ |
| 25 | hermes_portal_gate_final/mapping_fill_helper_v2.py | ✅ | `cd6a48dc` | ✅ |
| 26 | hermes_portal_gate_final/batch_export_import.py | ✅ | `60aa4f7d` | ✅ |
| 27 | hermes_portal_gate_final/indicator_alias_library.csv | ✅ | `8743cedb` | ✅ |
| 28 | hermes_portal_gate_final/high_risk_confusion_pairs.csv | ✅ | `f9783f90` | ✅ |

---

## 三、约束合规校验

| # | 约束 | 结果 | 详情 |
|---|------|------|------|
| 1 | NO_ZHIJI_API_CALL | ⚠ | 发现3个文件引用zhiji_api |
| 2 | NO_MODIFY_SOURCE_TEMPLATE | ✅ | 红线文件MD5匹配 |
| 3 | ONLY_NEW_FILES | ✅ | 本轮仅新增文件 |
| 4 | BRANCH_LOCKED | ✅ | feature/v85-chart-template |

---

## 四、红线文件校验

| 文件 | MD5 | 状态 |
|------|-----|------|
| data/indicators_v1.json | `7a864e10` | ✅ 未修改 |
| data/tree_config.json | `9b98c8af` | ✅ 未修改 |

---

## 五、自检结论

❌ 交付包不完整，请检查未通过项。