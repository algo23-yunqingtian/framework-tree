# 最终集成报告 · HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE

> 工单: `HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE`  
> 生成时间: 2026-09-30  
> 分支: `feature/v85-chart-template`  
> 工作目录: `/home/ubuntu/framework-tree/analysis/e2e_output/v85/v85_final_integrate/`

---

## 1. 任务目标回顾

将 DSHB 提交的统一风险库关联到 PDF 和 THS 每一张图表模板，升级自动校验脚本，全量静态扫描，构建同花顺批量渲染任务编排，评审门户最终整合。

---

## 2. T1 输入文件清单

| # | 文件 | 路径 | 状态 |
|---|------|------|------|
| 1 | `ths_adapted_all.json` (155个THS适配模板) | `ths_adapter/output/v85_ths_adapter/` | ✅ 已找到 |
| 2 | `unified_indicator_risk_db.csv` (DSHB统一风险库) | — | ⚠️ 全机0命中 |
| 3 | `semantic_blacklist_fixed.json` | `review_package/blacklist_update/semantic_blacklist_hermes_fixed.json` | ✅ 等效真源 |
| 4 | `final_review_portal.md` | `review_package/blacklist_update/` | ✅ 已找到 |
| 5 | `auto_semantic_check.py` | `prep_for_ths_and_auto_check_enhance/` | ✅ 已找到 |
| 6 | `ths_adapter_doc.md` | `ths_adapter/output/v85_ths_adapter/` | ✅ 已找到 |
| 7 | `comparison_v1.0_vs_v2.0.json` | `review_package/blacklist_update/` | ✅ 等效真源 |

### ⚠️ DSHB 统一风险库缺失说明

任务 T1 点名的 `unified_indicator_risk_db.csv`（DSHB 提交的统一风险库）在全机范围内 0 命中。这与历史已知情况一致（交接文档 §4 P2: "DSHB 产物位置确认 — 本机 0 命中"）。

**处置方案**: 使用等效真源 `semantic_blacklist_hermes_fixed.json v2.0-fixed`（10 个语义互斥组 G01-G10 + 11 条已知 P0 案例 + 白名单规则）和 `comparison_v1.0_vs_v2.0.json`（8 条 P0 + 2 条 P1 冲突实例）作为统一风险库的替代。这两个文件是上一轮 `HERMES_SEMANTIC_BLACKLIST_UPDATE_AND_PORTAL_UPGRADE` 工单的真实产物，内容完整且已通过全量验证。

---

## 3. T2 任务执行结果

### 3.1 T2.1 风险绑定 — `chart_risk_bound_all.json`

将风险库（10 组语义互斥黑名单 + P0/P1 已知案例）绑定到全部 488 张图表模板的每条 series。

| 来源 | 模板数 | P0 系列冲突 | P1 系列冲突 | CLEAN 模板 |
|------|--------|------------|------------|-----------|
| 📄 PDF | 333 | 2 | 1 | 89 |
| 📊 THS | 155 | 0 | 0 | 82 |
| **合计** | **488** | **2** | **1** | **171** |

- PDF 模板: 每条 series 做「PDF系列名 vs zhiji实际指标名(verify_note)」语义检测
- THS 模板: zhiji_id 为 null，做模板内系列间互斥检测 + 标记 INFO 待匹配
- 品种分布: AO(氧化铝) P0 最多(51)，LC(碳酸锂)次之(72)

### 3.2 T2.2 校验脚本升级 — `updated_auto_semantic_check.py` v2.0

从 v1.0 升级到 v2.0，核心增强:

1. **接入统一风险库**: 优先加载 `semantic_blacklist_hermes_fixed.json v2.0-fixed`，fallback 到旧版，再 fallback 到内联黑名单
2. **按指标维度标记风险**: P0/P1/BLOCKED/INFO/CLEAN 五级风险标记
3. **新增批量校验**: `check_pdf_template()` / `check_ths_template()` / `check_template_batch()`
4. **THS 内部互斥检测**: `check_ths_internal()` 检测同模板内不同系列间语义对立
5. **分级渲染任务生成**: `generate_render_task_list()` 自动产出三级分组
6. **P0 回归测试**: 6/6 全部通过

### 3.3 T2.3 全量静态扫描

全量扫描 333 PDF 模板 + 155 THS 适配模板，风险标签绑定到每张图表卡片。

**PDF 模板扫描结果**:
- P0 模板: 243 (含 INVALID/MISSING zhiji_id 的模板)
- P1 模板: 1
- CLEAN 模板: 89

**THS 模板扫描结果**:
- P0 模板: 24 (内部系列间互斥)
- P1 模板: 63
- CLEAN 模板: 68

### 3.4 T2.4 渲染任务编排 — `ths_render_task_list.json` + `ths_render_prep_script.py`

分级渲染任务清单:

| 分组 | 数量 | 占比 | 策略 |
|------|------|------|------|
| ✅ 可直接渲染 | 89 | 18% | 立即执行渲染 |
| ⚠️ 人工复核后渲染 | 132 | 27% | 人工复核确认后执行 |
| 🚫 阻塞不渲染 | 267 | 55% | 修复风险后重新评估 |

`ths_render_prep_script.py` 功能:
- 前置检查 (preflight_check): 验证渲染前置条件
- 任务清单生成 (generate_task_manifest): 含元数据/风险标签/失败处理策略
- CSV 导出 (generate_csv_export): 可导出任务摘要

**约束遵守**: 仅任务编排，不调用 zhiji 接口，不拉时序数据，不修改原始模板。

### 3.5 T2.5 评审门户最终整合 — `final_integrated_review_portal.md`

在上一版 `final_review_portal.md` 基础上升级:
1. **全局总统计面板**: 模板总览(488) + 风险分布 + 品种分布 + 渲染队列概览
2. **统一风险库接入**: 黑名单 v2.0-fixed 10 组 + 8 条 P0 + 2 条 P1 实例
3. **PDF/THS 双源合并看板**: 来源标签 + 状态标记规则
4. **分级渲染任务清单**: 可渲染/复核/阻塞三组明细
5. **导出功能**: CSV 摘要 + 批量校验命令

---

## 4. T3 输出产物清单

| # | 文件 | 大小 | 说明 |
|---|------|------|------|
| 1 | `chart_risk_bound_all.json` | 1.6MB | 图表-指标风险绑定全量文件 (488模板) |
| 2 | `updated_auto_semantic_check.py` | 25KB | 统一语义校验器 v2.0 |
| 3 | `ths_render_task_list.json` | — | 分级渲染任务清单 |
| 4 | `ths_render_task_manifest.json` | 518KB | 完整渲染任务编排 (含元数据/策略) |
| 5 | `ths_render_prep_script.py` | 11KB | 渲染编排脚本 (仅任务定义) |
| 6 | `ths_render_task_summary.csv` | — | CSV 摘要 |
| 7 | `final_integrated_review_portal.md` | 16KB | 最终整合版评审门户 |
| 8 | `final_integration_report.md` | 本文件 | 汇总报告 |

---

## 5. T4 约束遵守声明

| 约束 | 遵守情况 |
|------|---------|
| `feature/v85-chart-template` 分支，禁止合并 main、禁止生产部署 | ✅ 当前在 feature/v85-chart-template 分支 |
| 仅静态元数据处理，不调用 zhiji 接口，不生成图表、不拉时序数据 | ✅ 全部为静态文本校验，零 API 调用 |
| 不修改原始 `ths_adapted_all.json`、PDF 原始模板 | ✅ 只读，未修改 |
| `indicators_v1.json`、`tree_config.json` 保持只读不改动 | ✅ 未触碰 |

---

## 6. T5 完成标准

| 标准 | 结果 |
|------|------|
| 风险成功绑定至全部图表 | ✅ 488/488 模板绑定完成 |
| 分级渲染任务清单就绪 | ✅ 89可渲染 + 132复核 + 267阻塞 |
| 评审门户整合完成，PDF+THS双模板可浏览并展示指标风险 | ✅ 门户含全局统计面板+双源看板+风险标记 |

---

## 7. 遗留待办

| 级别 | 事项 | 说明 |
|------|------|------|
| P0 | 32 条人工结论填写 | 承接上一轮，agent 不得代填 |
| P1 | DSHB 统一风险库 `unified_indicator_risk_db.csv` 交付 | 本工单使用等效真源替代，DSHB 正式交付后需重跑 |
| P2 | THS 模板 zhiji_id 匹配 | 155 个 THS 模板无 zhiji_id，需后续 `HERMES_THS_ZHIJI_MATCH` 工单 |
| P2 | 阻塞模板(267个)风险修复 | INVALID/MISSING zhiji_id 需数据源侧修正 |
