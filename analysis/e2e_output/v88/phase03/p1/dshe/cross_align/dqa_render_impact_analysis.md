# DSHB Phase04 DQA 缺陷对渲染引擎影响评估

> **TASK_ID**: V88_PHASE03_P1_DSHE_P012_EXEMPTION_PREPARE_AND_CROSS_AGENT_ALIGN_JOB / T1
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **评估时间**: 2026-10-16 UTC+8
> **数据来源**: DSHB `background_followup/phase04_36metric_prototype_precheck.md` + `background_continue/v88_phase04_36metric_data_source_plan.md`
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL

---

## 1. 评估摘要

| 项 | 结果 |
|:---|:-----|
| DSHB DQA 缺陷清单总量 | **14 项**（3 覆盖缺口 + 7 假阳性 + 8 假阴性） |
| 新增 DQA 规则 | DQA-09/10/11（已设计）+ DQA-12/13/14/15（建议新增） |
| 渲染引擎需适配项 | **5 项**（DQA-03 频率自适应 / DQA-04 MAD / DQA-05 跨品种 / DQA-07 节假日 / DQA-08 换算） |
| 渲染引擎不需适配项 | **6 项**（DQA-01 BOM / DQA-02 时区 / DQA-06 分级 / DQA-09~15） |
| 渲染引擎阻断项 | **0 项**（全部为数据侧/采集侧改进，不阻断渲染链路） |

**核心结论**：DSHB Phase04 DQA 缺陷清单的 14 项问题全部属于数据采集与数据质量校验层面，不影响 DSHE `NodeBindingEngine.render_with_fallback()` 渲染链路。渲染引擎需适配的 5 项为 DQA 规则改进后渲染侧元数据展示需要同步更新（如频率标签、节假日标记），但非渲染逻辑变更。

---

## 2. DQA 缺陷清单逐项影响分析

### 2.1 覆盖缺口（3 类 → 14 项指标）

| # | 缺口类型 | 影响指标数 | 渲染引擎影响 | DSHE 适配项 |
|:-:|----------|:----------:|:------------:|:-----------:|
| CG-1 | 月度频率无 DQA | 6 | 无 | 渲染侧需增加频率标签（日/月/周） |
| CG-2 | 代理模型无置信度 | 6 | 无 | 渲染侧需展示置信度标记 |
| CG-3 | 依赖链无端到端校验 | 2 | 无 | 无 |

**渲染侧适配**：`chart_kits.py` 或 `node_binding_engine.py` 的图表元数据 `meta` 块需增加 `frequency` 和 `confidence` 字段，用于前端展示频率标签和置信度标记。**不涉及渲染逻辑变更**。

### 2.2 假阳性场景（7 处 → 14 项指标受影响）

| # | DQA 规则 | 触发指标 | 渲染引擎影响 | DSHE 适配项 |
|:-:|:--------:|----------|:------------:|:-----------:|
| FP-01 | DQA-04 | cu_spot_premium | 无 | 无 |
| FP-02 | DQA-04 | sn_spot_premium | 无 | 无 |
| FP-03 | DQA-04 | al_premium_change (派生) | 无 | 派生指标阈值标签 |
| FP-04 | DQA-07 | pb_price_percentile | 无 | 节假日标记 |
| FP-05 | DQA-07 | pb_long_short_ratio | 无 | 节假日标记 |
| FP-06 | DQA-01 | SPOT_IS (外部 CSV) | 无 | 无 |
| FP-07 | DQA-04 | cu_premium_change | 无 | 无 |

**渲染侧适配**：FP-03/04/05 需要在渲染结果中标注「派生指标专用阈值」和「节假日豁免」标记，便于前端展示。这些标记存储在 `meta` 块中，不影响 `render_with_fallback()` 的数据读取与绑定逻辑。

### 2.3 假阴性场景（8 处）

| # | DQA 规则 | 触发指标 | 渲染引擎影响 | DSHE 适配项 |
|:-:|:--------:|----------|:------------:|:-----------:|
| FN-01 | DQA-06 | sn_top20_net | 无 | 无（数据侧修复） |
| FN-02 | DQA-03 | cu_smelter_production | 无 | 频率标签 |
| FN-03 | DQA-08 | 所有单位指标 | 无 | 无 |
| FN-04 | DQA-04 | li_term_structure | 无 | 覆盖率标记 |
| FN-05 | DQA-02 | 所有指标 | 无 | 无 |
| FN-06 | DQA-05 | 跨品种映射 | 无 | 品种验证标记 |
| FN-07 | DQA-04 | cu_smelter_profit | 无 | 无 |
| FN-08 | DQA-03 | sn_spot_premium | 无 | 覆盖率标记 |

**渲染侧适配**：全部为数据侧修复，渲染引擎不需要逻辑变更。部分指标需增加「覆盖率」和「品种验证」元数据标记，但通过 `meta` 块追加即可。

---

## 3. 新增 DQA 规则对渲染引擎影响

### 3.1 DQA-09~11（已设计）

| 规则 | 名称 | 渲染影响 | DSHE 动作 |
|------|------|:--------:|-----------|
| DQA-09 | 数据源交叉验证 | 无 | 无——数据侧多源校验，不经过渲染引擎 |
| DQA-10 | 代理估算置信度 | 低 | 渲染 `meta` 块增加 `confidence_interval` 字段 |
| DQA-11 | 月度/日度频率一致性 | 低 | 渲染 `meta` 块增加 `frequency_match` 标记 |

### 3.2 DQA-12~15（建议新增）

| 规则 | 名称 | 渲染影响 | DSHE 动作 |
|------|------|:--------:|-----------|
| DQA-12 | 数据源时滞检测 | 无 | 无——时滞在采集侧检测 |
| DQA-13 | 历史覆盖率 | 低 | 渲染 `meta` 块增加 `coverage_ratio` 字段 |
| DQA-14 | 依赖链一致性 | 无 | 无——依赖链在 DSHB 校验 |
| DQA-15 | 节假日/业务日历豁免 | 低 | 渲染 `meta` 块增加 `calendar_exempt` 标记 |

---

## 4. 渲染引擎适配清单

### 4.1 Phase04 M1 前（P1 优先级）

| # | 适配项 | 修改文件 | 工时 | 说明 |
|:-:|--------|----------|:----:|------|
| 1 | 频率标签 | `chart_kits.py` meta 块 | 0.5d | 增加 `frequency: daily|weekly|monthly` 字段 |
| 2 | 置信度标记 | `chart_kits.py` meta 块 | 0.5d | 增加 `confidence: {level, ci_width}` 字段 |
| 3 | 覆盖率标记 | `chart_kits.py` meta 块 | 0.5d | 增加 `coverage_ratio` 字段 |
| 4 | 节假日豁免标记 | `chart_kits.py` meta 块 | 0.5d | 增加 `calendar_exempt: true\|false` |
| 5 | 品种验证标记 | `node_binding_engine.py` | 0.5d | 增加品种-指标交叉验证 meta |

**合计**：2.5 人天，全部为元数据字段追加，不涉及渲染逻辑。

### 4.2 Phase04 M2 前（P2 优先级）

| # | 适配项 | 修改文件 | 工时 |
|:-:|--------|----------|:----:|
| 6 | 派生指标专用阈值标签 | `chart_kits.py` | 0.5d |
| 7 | 数据源时滞展示 | `chart_kits.py` meta 块 | 0.5d |

### 4.3 不需适配项（6 项）

DQA-01 BOM 检测、DQA-02 时区检查、DQA-06 分级阈值、DQA-09 多源校验、DQA-12 时滞检测、DQA-14 依赖链——全部在 DSHB 采集/校验侧完成，不经过渲染引擎。

---

## 5. 36 指标渲染就绪度评估

| 状态 | 数量 | 占比 | 渲染影响 |
|:----:|:----:|:----:|----------|
| ✅ PASS (可直接渲染) | 16 | 44.4% | 无——已有数据+DQA全通过 |
| ⚠️ WARN (需补源后渲染) | 12 | 33.3% | 低——数据补全后即可渲染 |
| 🔴 BLOCKED (需新建爬虫) | 8 | 22.2% | 中——需新建指标绑定+渲染模板 |

**渲染引擎 BLOCKED 项影响**：8 项 BLOCKED 指标（cu/al 供给+成本）需要新建图表模板，但已有 16 项 PASS 指标可立即进入 Phase04 渲染流水线。渲染引擎当前架构（`NodeBindingEngine` + `chart_kits.py`）已支持动态指标绑定，新增指标只需配置 `meta_chart` 映射，无需修改引擎核心逻辑。

---

## 6. 结论与建议

1. **渲染引擎无需修改核心逻辑**：DSHB DQA 缺陷 14 项全部属于数据采集/校验层面，渲染链路不受影响
2. **渲染侧适配工作量**：2.5 人天（M1 前）+ 1.0 人天（M2 前）= 3.5 人天，全部为元数据字段追加
3. **Phase04 M5 对接前置条件**：36 项指标 DQA 全 PASS 后对接渲染——当前 16/36 已 PASS，渲染引擎已就绪
4. **建议**：DSHE 在 Phase04 M1 启动时同步实施 5 项元数据适配，不阻断 Phase03 收尾

---

*Generated: 2026-10-16 UTC+8 | DSHE | DQA影响评估基于 DSHB phase04_36metric_prototype_precheck.md*
