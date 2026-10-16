# DSHB Phase04 DQA 缺陷对渲染引擎影响评估 (刷新版)

> **TASK_ID**: V88_PHASE03_P1_DSHE_P012_NATIVE_PASS_CONSOLIDATE_AND_SYNC_JOB / T3
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **评估时间**: 2026-10-16T20:48 UTC+8
> **基线来源**: v1.4.0-cpu-triple-fix (原生 PASS)
> **刷新说明**: 基线已从 v3.0.0 (豁免版) 刷新为 v1.4.0-cpu-triple-fix (原生 PASS)
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL

---

## 0. 基线刷新声明

| 项 | 刷新前 (v3.0.0) | 刷新后 (v1.4.0-cpu-triple-fix) |
|:--|:---------------:|:-------------------------------:|
| 基线版本 | v3.0.0 | **v1.4.0-cpu-triple-fix** |
| CPU 口径 | process_time 进程级 | **psutil 系统级稳态** |
| cpu_peak_pct | 99.4871% | **0.0654%** |
| Schema | v1.x | **v2.0-steady-state** |
| 门禁路径 | `p012_cpu_benchmark/` | **`dshe/cpu_peak_pct.json`** |
| 豁免状态 | EXEMPTION_REQUESTED | **TERMINATED (native PASS)** |
| frozen commit | b1987a4 | **55458b6** |
| merge_status | ready | **ready-refresh** |

**影响范围**: DQA 缺陷清单 14 项全部基于数据采集/校验层面，与 CPU 基线口径变更无关。渲染引擎适配工作量 **2.5 人天不变**，不受影响。

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

---

## 3. 渲染引擎适配清单

### 3.1 Phase04 M1 前（P1 优先级）

| # | 适配项 | 修改文件 | 工时 | 说明 |
|:-:|--------|----------|:----:|------|
| 1 | 频率标签 | `chart_kits.py` meta 块 | 0.5d | 增加 `frequency: daily|weekly|monthly` 字段 |
| 2 | 置信度标记 | `chart_kits.py` meta 块 | 0.5d | 增加 `confidence: {level, ci_width}` 字段 |
| 3 | 覆盖率标记 | `chart_kits.py` meta 块 | 0.5d | 增加 `coverage_ratio` 字段 |
| 4 | 节假日豁免标记 | `chart_kits.py` meta 块 | 0.5d | 增加 `calendar_exempt: true|false` |
| 5 | 品种验证标记 | `node_binding_engine.py` | 0.5d | 增加品种-指标交叉验证 meta |

**合计**：2.5 人天，全部为元数据字段追加，不涉及渲染逻辑。

### 3.2 Phase04 M2 前（P2 优先级）

| # | 适配项 | 修改文件 | 工时 |
|:-:|--------|----------|:----:|
| 6 | 派生指标专用阈值标签 | `chart_kits.py` | 0.5d |
| 7 | 数据源时滞展示 | `chart_kits.py` meta 块 | 0.5d |

---

## 4. 36 指标渲染就绪度评估

| 状态 | 数量 | 占比 | 渲染影响 |
|:----:|:----:|:----:|----------|
| ✅ PASS (可直接渲染) | 16 | 44.4% | 无 |
| ⚠️ WARN (需补源后渲染) | 12 | 33.3% | 低 |
| 🔴 BLOCKED (需新建爬虫) | 8 | 22.2% | 中 |

---

## 5. 结论与建议

1. **基线已刷新**：DQA 影响评估基于 v1.4.0-cpu-triple-fix 基线（原生 PASS），非豁免版
2. **渲染引擎无需修改核心逻辑**：DSHB DQA 缺陷 14 项全部属于数据采集/校验层面
3. **渲染侧适配工作量**：2.5 人天（M1 前）+ 1.0 人天（M2 前）= 3.5 人天
4. **Phase04 M5 对接前置条件**：36 项指标 DQA 全 PASS 后对接渲染——当前 16/36 已 PASS
5. **建议**：DSHE 在 Phase04 M1 启动时同步实施 5 项元数据适配，不阻断 Phase03 收尾

---

*Generated: 2026-10-16 UTC+8 | DSHE | DQA影响评估刷新版 (基线: v1.4.0-cpu-triple-fix)*
