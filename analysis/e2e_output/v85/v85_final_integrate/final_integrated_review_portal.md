# V85 图表模板人工评审总入口 · 最终整合版

> 工单: `HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE`  
> 生成时间: 2026-09-30 23:21:34  
> 分支: `feature/v85-chart-template`  
> ⛔ **状态: 测试环境评审材料，未上线**  
> 🆕 **最终整合**: 接入统一风险库 + PDF/THS 双源合并看板 + 全局总统计面板 + 分级渲染任务清单
>
> 上一版: `final_review_portal.md` (HERMES_SEMANTIC_BLACKLIST_UPDATE_AND_PORTAL_UPGRADE)

---

## 0. 全局总统计面板

### 0.1 模板总览

| 来源 | 模板总数 | 可直接渲染 | 人工复核 | 阻塞 | 无风险(CLEAN) |
|------|---------|-----------|---------|------|--------------|
| 📄 PDF | 333 | 89 | 1 | 243 | 89 |
| 📊 THS | 155 | 0 | 131 | 24 | 82 |
| **合计** | **488** | **89** | **132** | **267** | **171** |

### 0.2 风险分布

| 风险等级 | PDF 系列级 | THS 系列级 | 合计 | 处置策略 |
|---------|-----------|-----------|------|---------|
| 🔴 P0 (语义互斥对立) | 2 | 0 | 2 | 拦截渲染，禁止投产 |
| 🟠 P1 (近似口径不等价) | 1 | 0 | 1 | 人工复核后决定 |
| ℹ️ INFO (关键词命中/待匹配) | — | — | — | 观察项，不阻塞 |
| ✅ CLEAN (无风险) | 89 模板 | 82 模板 | 171 模板 | 可直接渲染 |

### 0.3 品种分布

| 品种 | 模板总数 | P0 | P1 | CLEAN |
|------|---------|----|----|-------|
| AL | 47 | 29 | 3 | 15 |
| AO | 63 | 51 | 0 | 12 |
| CU | 6 | 0 | 0 | 6 |
| LC | 100 | 72 | 0 | 28 |
| LI | 19 | 2 | 7 | 10 |
| NI | 79 | 33 | 9 | 37 |
| SI | 77 | 37 | 10 | 30 |
| SN | 67 | 38 | 11 | 18 |
| ZN | 30 | 5 | 10 | 15 |

### 0.4 渲染队列概览

| 分组 | 数量 | 占比 | 策略 |
|------|------|------|------|
| ✅ 可直接渲染 | 89 | 18% | 立即执行渲染 |
| ⚠️ 人工复核后渲染 | 132 | 27% | 人工复核确认后执行 |
| 🚫 阻塞不渲染 | 267 | 54% | 修复风险后重新评估 |

---

## 1. 模板来源标签说明

| 标签 | 含义 | 数量 | 说明 |
|------|------|------|------|
| 📄 PDF | 来自 DSHB PDF 解析的模板 | 333 张 | 已有 zhiji_id、verify_status、渲染 HTML，可预览 |
| 📊 THS | 来自同花顺原生 JSON 的模板 | 155 张 | 经 THS 适配层转换，**暂无 zhiji_id**，预览为适配后元数据 |

> ⚠️ **THS 模板限制**: 同花顺模板尚无 zhiji_id 匹配和渲染 HTML，预览入口指向适配层输出（元数据结构），非渲染图表。渲染需完成后续 `HERMES_THS_ZHIJI_MATCH` 工单。

---

## 2. 评审权限与状态标记规则

| 标记 | 含义 | 展示规则 | 投产结论 |
|------|------|----------|---------|
| 🟢 **FULL_OK** | 全部 series 校验通过 | 正常展示 | 可投产（评审通过后） |
| 🔴 **PART_OK** | 含 INVALID/MISSING series | 红色告警条 + 🚫标记 + 失败明细表 | **禁止投产** |
| 🟠 **口径待复核** | FILLED 匹配存在口径冲突(P0/P1) | 需在模板标题加注 | 复核通过前禁止投产 |
| ⏳ **pending** | THS 模板，待 zhiji_id 匹配 | 灰色标签 + 适配元数据 | 匹配完成前禁止投产 |

---

## 3. 语义冲突风险标记（统一风险库 v2.0-fixed）

> **风险库版本**: `semantic_blacklist_hermes_fixed.json v2.0-fixed`
> **校验器版本**: `updated_auto_semantic_check.py v2.0` (UnifiedSemanticChecker)
> **冲突组数**: 10 组 (G01-G10)
> **BL-021 修复**: G08 移除"均价"/"现货价"，消除 3 条 P1 误报
> **机制**: 对每个 series 的「PDF系列名 vs zhiji实际指标名」做自动文本校验
> ⚠️ **重要**: DSHB 文本相似度 score=1.00 满分 **不代表**口径正确，本黑名单基于业务语义判定

### 3.1 语义互斥冲突组速查（10 组）

| 组ID | 严重度 | 语义对立 | 典型错配案例 |
|------|--------|---------|------------|
| `G01` | 🔴 P0 | 产量 ↔ 消费量/销量 | 铝土矿产量→铝土矿消费量 |
| `G02` | 🔴 P0 | 场内库存 ↔ 非仓单/场外库存 | LME场内库存→LME非仓单库存 |
| `G03` | 🔴 P0 | 库存 ↔ 在途/堆场 | 氧化铝库存→氧化铝在途&站台堆积 |
| `G04` | 🟠 P1 | 拟合/估算 ↔ 官方指数 | 汽车端消费用锡拟合→汽车消费指数 |
| `G05` | 🟠 P1 | 折镍价 ↔ 折合价 | 不同镍产品折镍价→304废不锈钢折合镍铁 |
| `G06` | 🟠 P1 | 社会库存 ↔ 期货仓单 | — |
| `G07` | 🟠 P1 | 开工率 ↔ 产量 | DMC全国开工率 (INVALID) |
| `G08` | 🟠 P1 | 价格 ↔ 成本 | (BL-021修复后移除"均价"误报) |
| `G09` | 🔴 P0 | 出口 ↔ 进口 | — |
| `G10` | 🔴 P0 | 国产 ↔ 进口/海外 | — |

### 3.2 已知 P0 冲突实例（8 条，来自 comparison_v1.0_vs_v2.0.json）

| 模板ID | 系列名 | zhiji实际指标名 | 冲突组 | 分数 |
|--------|--------|----------------|--------|------|
| TPL-AO-020/026 | 氧化铝库存-阿拉丁-堆场站台 | SMM:中国氧化铝在途&站台堆积:库存量:周度 | G03 | 0.57 |
| TPL-LC-084/086/099 | 其他电池(磷酸铁锂) 销量 | SMM: 境内其他电池产量: 月度 | G01 | 0.86 |
| TPL-LC-091/092 | 新能源乘用车 产量 | SMM: 国产乘用车销量-新能源汽车: 周度 | G01 | 1.00 |
| TPL-AL-013 | LME主要仓库场内库存 | LME：非仓单库存：欧洲（日） | G02 | 0.55 |

### 3.3 已知 P1 冲突实例（2 条）

| 模板ID | 系列名 | zhiji实际指标名 | 冲突组 | 分数 |
|--------|--------|----------------|--------|------|
| TPL-SN-034 | 汽车端消费用锡拟合 | 汽车：消费指数：中国（月） | G04 | 0.44 |
| TPL-NI-004 | 不同镍产品折镍价 | SMM: 304废不锈钢折合镍铁价格: 日度 | G05 | 0.50 |

---

## 4. 分级渲染任务清单

### 4.1 可直接渲染（89 个）

> 风险等级: CLEAN — 无语义冲突，无 INVALID/MISSING zhiji_id

| 来源 | 模板ID | 品种 | 风险等级 | 策略 |
|------|--------|------|---------|------|
| PDF | `TPL-AO-001` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-010` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-011` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-012` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-013` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-016` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-017` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-022` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-024` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-032` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-036` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-AO-060` | AO | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-003` | SI | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-005` | SI | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-008` | SI | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-009` | SI | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-010` | SI | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-014` | SI | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-015` | SI | CLEAN | 可直接渲染 |
| PDF | `TPL-SI-017` | SI | CLEAN | 可直接渲染 |

<details>
<summary>📋 查看全部 89 条可渲染模板</summary>

完整清单见 `ths_render_task_manifest.json` → `render_groups.can_render.tasks`

</details>

### 4.2 人工复核后渲染（132 个）

> 风险等级: P1 / INFO — 存在近似口径不等价或 THS 待匹配

| 来源 | 模板ID | 品种 | 风险等级 | 风险数 | 策略 |
|------|--------|------|---------|--------|------|
| PDF | `TPL-SN-034` | SN | P1 | P0:0 P1:1 | 人工复核: 存在P1近似口径不等价, 复核后决定是否渲染 |
| THS | `THS-AL-3.1` | AL | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-AL-3.2` | AL | P1 | P0:0 P1:0 | 人工复核: 存在P1近似口径不等价或内部对立 |
| THS | `THS-AL-3.3` | AL | P1 | P0:0 P1:0 | 人工复核: 存在P1近似口径不等价或内部对立 |
| THS | `THS-AL-4.1` | AL | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-AL-4.2` | AL | P1 | P0:0 P1:0 | 人工复核: 存在P1近似口径不等价或内部对立 |
| THS | `THS-AL-4.3` | AL | P1 | P0:0 P1:0 | 人工复核: 存在P1近似口径不等价或内部对立 |
| THS | `THS-AL-6.3` | AL | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-CU-2.3` | CU | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-CU-4.1` | CU | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-CU-4.2` | CU | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-CU-4.3` | CU | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-CU-4.4` | CU | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-CU-4.5` | CU | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-LI-2.1` | LI | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-LI-2.2` | LI | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-LI-2.4` | LI | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-LI-2.5` | LI | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-LI-2.6` | LI | CLEAN | P0:0 P1:0 | 待匹配zhiji_id后渲染 (THS模板无zhiji_id) |
| THS | `THS-LI-3.1.1` | LI | P1 | P0:0 P1:0 | 人工复核: 存在P1近似口径不等价或内部对立 |

<details>
<summary>📋 查看全部 132 条复核模板</summary>

完整清单见 `ths_render_task_manifest.json` → `render_groups.review_first.tasks`

</details>

### 4.3 🚫 阻塞不渲染（267 个）

> 风险等级: P0 / BLOCKED — 存在语义互斥对立或 INVALID zhiji_id

| 来源 | 模板ID | 品种 | 风险等级 | 风险数 | 策略 |
|------|--------|------|---------|--------|------|
| PDF | `TPL-AO-002` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-003` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-004` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-005` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-006` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-007` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-008` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-009` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-014` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-015` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-018` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-019` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-020` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-021` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-023` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-025` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-026` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-027` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-028` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |
| PDF | `TPL-AO-029` | AO | P0 | P0:0 P1:0 Blk:1 | 阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染 |

<details>
<summary>📋 查看全部 267 条阻塞模板</summary>

完整清单见 `ths_render_task_manifest.json` → `render_groups.blocked.tasks`

</details>

---

## 5. 评审材料索引

| # | 材料 | 来源 | 路径 | 用途 |
|---|------|------|------|------|
| 1 | `chart_risk_bound_all.json` | PDF+THS | `v85_final_integrate/chart_risk_bound_all.json` | **图表-指标风险绑定全量文件** (488模板) |
| 2 | `updated_auto_semantic_check.py` | 通用 | `v85_final_integrate/updated_auto_semantic_check.py` | **统一语义校验器 v2.0** |
| 3 | `ths_render_task_list.json` | PDF+THS | `v85_final_integrate/ths_render_task_list.json` | **分级渲染任务清单** |
| 4 | `ths_render_task_manifest.json` | PDF+THS | `v85_final_integrate/ths_render_task_manifest.json` | **完整渲染任务编排** (含元数据/策略) |
| 5 | `ths_render_prep_script.py` | 通用 | `v85_final_integrate/ths_render_prep_script.py` | **渲染编排脚本** (仅任务定义) |
| 6 | `ths_render_task_summary.csv` | PDF+THS | `v85_final_integrate/ths_render_task_summary.csv` | **CSV摘要** (可导出) |
| 7 | `semantic_blacklist_hermes_fixed.json` | 通用 | `review_package/blacklist_update/semantic_blacklist_hermes_fixed.json` | **统一风险库 v2.0-fixed** (10组) |
| 8 | `comparison_v1.0_vs_v2.0.json` | 通用 | `review_package/blacklist_update/comparison_v1.0_vs_v2.0.json` | **新旧对比** (8 P0 + 2 P1) |
| 9 | `ths_adapted_all.json` | THS | `ths_adapter/output/v85_ths_adapter/ths_adapted_all.json` | 155 个适配后模板 |
| 10 | `pdf_web_chart_template_hermes_ready.json` | PDF | `pdf_template_build/zhiji_verified_package/` | 333 个 PDF 模板 |
| 11 | `blacklist_rerun_report.md` | 通用 | `review_package/blacklist_update/blacklist_rerun_report.md` | 黑名单复测报告 |

---

## 6. 导出功能

### 6.1 单模板风险明细 CSV

渲染任务摘要已导出为 CSV: `ths_render_task_summary.csv`

字段: `task_id, source, template_id, variety, risk_level, p0, p1, blocked, strategy, status`

### 6.2 批量导出命令

```bash
# 全量校验 + 生成渲染任务清单
python3 v85_final_integrate/updated_auto_semantic_check.py --full \
  --blacklist review_package/blacklist_update/semantic_blacklist_hermes_fixed.json \
  --pdf pdf_template_build/zhiji_verified_package/pdf_web_chart_template_hermes_ready.json \
  --ths ths_adapter/output/v85_ths_adapter/ths_adapted_all.json \
  --out v85_final_integrate/

# 渲染前置检查
python3 v85_final_integrate/ths_render_prep_script.py \
  --bound v85_final_integrate/chart_risk_bound_all.json \
  --tasks v85_final_integrate/ths_render_task_list.json \
  --out v85_final_integrate/

# 单对指标语义校验
python3 v85_final_integrate/updated_auto_semantic_check.py \
  --pair "新能源乘用车 产量" "SMM: 国产乘用车销量-新能源汽车: 周度"

# P0 回归测试
python3 v85_final_integrate/updated_auto_semantic_check.py --verify-cases \
  --blacklist review_package/blacklist_update/semantic_blacklist_hermes_fixed.json
```

---

## 7. 约束声明

- ⛔ **分支**: `feature/v85-chart-template`，禁止合并 main、禁止生产部署
- ⛔ **不调用 zhiji 接口**: 全部校验为静态文本比对，不拉时序数据
- ⛔ **不修改原始模板**: `ths_adapted_all.json`、`pdf_web_chart_template_hermes_ready.json` 只读
- ⛔ **不修改配置**: `indicators_v1.json`、`tree_config.json` 保持只读
- ⚠️ **DSHB 统一风险库**: 任务 T1 点名的 `unified_indicator_risk_db.csv` 全机 0 命中（DSHB 产物从未落地本机），本工单使用等效真源 `semantic_blacklist_hermes_fixed.json v2.0-fixed` + `comparison_v1.0_vs_v2.0.json` 作为统一风险库

---

## 8. 版本历史

| 版本 | 工单 | 日期 | 变更 |
|------|------|------|------|
| v1.0 | HERMES_V85_ARTIFICIAL_REVIEW_PREP | 2026-09-29 | 初始评审门户 |
| v2.0 | HERMES_SEMANTIC_BLACKLIST_UPDATE_AND_PORTAL_UPGRADE | 2026-09-30 | PDF/THS 双来源 + 黑名单 v2.0-fixed |
| **v3.0** | **HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE** | **2026-09-30** | **统一风险库接入 + 全局统计面板 + 分级渲染任务清单 + 导出功能** |
