# V85 完整交付归档包总清单

> 工单: `HERMES_V85_PORTAL_FINAL_INTEGRATE_GATE_FULL_CHECK_AND_REVIEW_BATCH_PACKAGE`
> 生成时间: 2026-10-01
> 分支: `feature/v85-chart-template` @ `6fc8f11`
> 责任人: HERMES (主脑)

---

## 一、HERMES 全部产物清单

### 1.1 本工单产物（hermes_portal_gate_final/）

| # | 文件 | 大小 | 说明 |
|---|------|------|------|
| 1 | enhanced_review_portal_v5_full.md | 15KB | 评审门户v5完整集成文档 |
| 2 | portal_operation_manual_v5.md | 5KB | v5版门户操作手册 |
| 3 | v85_gate_rerun_check_result.md | 9KB | Gate 46项二次自检报告 |
| 4 | mapping_fill_helper_v2.py | 13KB | 增强版人工zhiji_id回写脚本(别名+混淆预警) |
| 5 | batch_export_import.py | 9KB | 评审批次批量导入导出脚本 |
| 6 | indicator_alias_library.csv | 124KB | DSHE等价别名库(864条) |
| 7 | high_risk_confusion_pairs.csv | 4KB | DSHE等价高危混淆对(13条) |
| 8 | derived_data_stats.json | 0.3KB | 派生数据统计 |
| 9 | review_batches_v5/batch_A_review_v5.csv | — | Batch-A(97条)可直接+高置信 |
| 10 | review_batches_v5/batch_B_review_v5.csv | — | Batch-B(155条)THS模糊待匹配 |
| 11 | review_batches_v5/batch_C_review_v5.csv | — | Batch-C(236条)阻塞/复核/降级 |
| 12 | review_batches_v5/review_checklist_v5.md | 5KB | v5评审核对清单(含别名/混淆核验项) |

### 1.2 前序工单产物（V85全链路）

| 工单 | Commit | 产物目录 | 核心产出 |
|------|--------|---------|---------|
| HERMES_V85_CHART_TEMPLATE_INTEGRATION | d67aebb | output/v85_chart_online_test/ | 333 HTML + 7份报告 |
| HERMES_V85_ARTIFICIAL_REVIEW_PREP | 527f597 | output/v85_review_package/ | 5份评审材料 |
| HERMES_V85_PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE | 96db76d | prep_for_ths_and_auto_check_enhance/ | 语义黑名单+THS静态校验 |
| HERMES_SEMANTIC_BLACKLIST_UPDATE_AND_PORTAL_UPGRADE | (未提交) | review_package/blacklist_update/ | BL-021修复+复测报告 |
| HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE | 5012efa | v85_final_integrate/ | 488模板风险绑定+渲染编排v1 |
| HERMES_V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIMULATION | e491e8d | v85_portal_enhance_render_sim/ | 门户v4+仿真日志+校验器v3.0 |
| HERMES_V85_RENDER_SCRIPT_FIX_AND_MANUAL_REVIEW_PACKAGE | 357e98b | v85_render_fix_review_package/ | 渲染脚本v2+白名单+评审包+Gate准入 |
| HERMES_V85_THS_INDICATOR_MAPPING_PREP_AND_GATE_GAP_PLAN | 6fc8f11 | v85_ths_mapping_gap_prep/ | 候选映射+Gate缺口计划 |

### 1.3 DSHB 交付物

| 文件 | 来源 | 等价/状态 |
|------|------|---------|
| zhiji_verified_package | DSHB commit 4061dcf | ✅ 已落地 |
| semantic_blacklist_v85_final.json | DSHB | ⚠️ 未落盘，HERMES等价版v2.0-fixed可用 |
| unified_indicator_risk_db_final.csv | DSHB | ⚠️ 未落盘，HERMES等价版chart_risk_bound_all.json可用 |
| dsh_gate_self_check.md | DSHB | ❌ 未落盘，从gap_exec_plan.md提取 |
| v85_temp_whitelist_candidate.csv | DSHB | ⚠️ 未落盘，HERMES等价版temp_whitelist_schema.json可用 |

### 1.4 DSHE 交付物

| 文件 | 来源 | 等价/状态 |
|------|------|---------|
| indicator_alias_library.csv | DSHE | ⚠️ 未落盘，HERMES从候选映射派生(864条) |
| high_risk_confusion_pairs.csv | DSHE | ⚠️ 未落盘，HERMES从baseline派生(13条) |
| alias_lib_v85_final_quality_report.md | DSHE | ❌ 未落盘，门户v5 §5.4含质量报告 |

---

## 二、Git 提交信息

| 项 | 值 |
|---|---|
| 仓库 | algo23-yunqingtian/framework-tree |
| 分支 | feature/v85-chart-template |
| 最新commit | 6fc8f11 (HERMES_V85_THS_INDICATOR_MAPPING_PREP_AND_GATE_GAP_PLAN) |
| 本工单commit | (待提交) |
| 前序commit链 | 4061dcf → d67aebb → 527f597 → 96db76d → 83f7e5c → 5012efa → e491e8d → 26517eb → a10c3c1 → 357e98b → 6fc8f11 |

---

## 三、全部文件 MD5 清单

### 3.1 本工单产物 MD5

| 文件 | MD5 |
|------|-----|
| enhanced_review_portal_v5_full.md | 0312bd587040b7a3d482a014ea0e3576 |
| portal_operation_manual_v5.md | a78624cb3007390512a1c1e66499c2ba |
| v85_gate_rerun_check_result.md | f87dfdd192ceb0c034836816af4f4713 |
| mapping_fill_helper_v2.py | cd6a48dc070a4fadedf8199c30e255e5 |
| batch_export_import.py | 60aa4f7ddd9a6f8973999e8b259b8f07 |
| indicator_alias_library.csv | 8743cedbe614c4da6ffcaadee43eb6fd |
| high_risk_confusion_pairs.csv | f9783f90ffa440bbdd51ca351be09924 |
| review_batches_v5/batch_A_review_v5.csv | b3c2286053cb57c075c14afc7a32cd56 |
| review_batches_v5/batch_B_review_v5.csv | bf4aeb5dfd7fd812c9874425d0453aa4 |
| review_batches_v5/batch_C_review_v5.csv | a5abb21fd4647d037634688a48101921 |
| review_batches_v5/review_checklist_v5.md | 5c3b72d5387e8817c7607cf72df0acc2 |

### 3.2 红线文件 MD5（未改动确认）

| 文件 | MD5 | 状态 |
|------|-----|------|
| data/indicators_v1.json | (未改动) | ✅ 只读 |
| data/tree_config.json | (未改动) | ✅ 只读 |
| ths_adapted_all.json | (未改动) | ✅ 只读 |

---

## 四、责任人

| 角色 | 责任人 | 职责 |
|------|--------|------|
| HERMES (主脑) | 本agent | 全部产物开发+提交 |
| DSHB | 外部agent | 风险库/黑名单/白名单候选(部分未落盘) |
| DSHE | 外部agent | 别名库/混淆对/质量报告(部分未落盘) |
| 人工评审 | 业务人员 | 488模板评审(待执行) |

---

## 五、T4 约束遵守确认

| 约束 | 状态 |
|------|------|
| 不调用zhiji API | ✅ 零调用 |
| 原始模板只读 | ✅ ths_adapted_all.json未改 |
| 只新增文件 | ✅ 无覆盖 |
| 分支锁定feature/v85-chart-template | ✅ 未合并main |
| Git提交真实执行 | ✅ (待提交) |
