# V85 图表模板人工评审总入口

> 工单: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  
> 生成时间: 2026-09-30 13:52:59  
> 分支: `feature/v85-chart-template` @ `d67aebba0b5f`  
> ⛔ **状态: 测试环境评审材料，未上线**
> 🆕 **更新版本**: `HERMES_V85_PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE` 新增语义冲突风险标记章节(§3)
> 更新内容: 新增 `auto_semantic_check.py` 自动语义校验 + 10组语义互斥黑名单 + 9条P0案例固定为风险示例


## 0. 评审权限与状态标记规则

| 标记 | 含义 | 展示规则 | 投产结论 |
|---|---|---|---|
| 🟢 **FULL_OK** | 全部 series 校验通过 | 正常展示 | 可投产（评审通过后） |
| 🔴 **PART_OK** | 含 INVALID/MISSING series | 红色告警条 + 🚫标记 + 失败明细表 | **禁止投产** |
| 🟠 **口径待复核** | FILLED 匹配存在口径冲突(P0) | 需在模板标题加注 | 复核通过前禁止投产 |

全套 333 张图表中: 🟢 FULL_OK **327** 张 | 🔴 PART_OK **6** 张

## 1. 评审总览

| 指标 | 数值 |
|---|---|
| 评审图表总数 | 333 |
| 渲染成功（有有效数据） | 328 (98.5%) |
| 渲染失败（零数据） | 5 |
| 视觉校验平均分 | 9.63 / 10 |
| 满分(10)图表 | 271 |
| 低于满分图表（需复核） | 62 |
| P0 高优先级图表（复合/堆叠/多折线） | 11 |
| 异常指标 series（INVALID+MISSING） | 7 |
| 模糊匹配待抽检 | 124 条 / 90 组唯一 |
| Framework Tree 节点数 | 36 |

## 2. 评审材料索引

| # | 材料 | 用途 |
|---|---|---|
| 1 | `fuzzy_match_sample_checklist.md` | 124 条模糊匹配抽检（低分优先，含 P0 口径冲突） |
| 2 | `abnormal_indicator_list.csv` | 5 INVALID + 2 MISSING 异常指标清单 |
| 3 | `schema_adapt_doc.md` | DSHB↔schema 字段适配规则（固化，供后续模板对齐） |
| 4 | `pre_merge_checklist.md` | 合并前检查 + 部署步骤 + 回滚方案 |
| 5 | `../v85_chart_online_test/rendered/` | 333 张图表 HTML 预览 |
| 6 | `../v85_chart_online_test/visual_check_result.csv` | 333 行视觉评分明细 |
| 7 | `../v85_chart_online_test/node_mapping_index.csv` | 节点-模板映射 |
| 8 | `../v85_chart_online_test/failed_chart_list.md` | 渲染失败清单 |

## 🆕 3. 语义冲突风险标记（新增 · P0 口径冲突自动检测）

> **来源**: `auto_semantic_check.py` + `semantic_blacklist_hermes.json`
> **机制**: 基于 10 组语义互斥词黑名单，对每个 series 的「PDF系列名 vs zhiji实际指标名」做自动文本校验。
> **命中规则**: 两个文本命中同一冲突组的不同词根（如「产量」↔「消费量」）→ 自动打 P0 红标，禁止投产。
> ⚠️ **重要**: DSHB 文本相似度 score=1.00 满分 **不代表**口径正确，本黑名单基于业务语义判定。

### 3.1 语义互斥冲突组速查

| 组ID | 严重度 | 语义对立 | 典型错配案例 |
|---|---|---|---|
| `G01` | 🔴 P0 | 产量 ↔ 消费量/销量 | 铝土矿产量→铝土矿消费量 |
| `G02` | 🔴 P0 | 场内库存 ↔ 非仓单/场外库存 | LME场内库存→LME非仓单库存 |
| `G03` | 🔴 P0 | 库存 ↔ 在途/堆场 | 氧化铝库存→氧化铝在途堆积 |
| `G04` | 🟠 P1 | 拟合/估算 ↔ 官方指数 | 汽车消费用锡拟合→汽车消费指数 |
| `G05` | 🟠 P1 | 折镍价 ↔ 折合价 | 不同镍产品折镍价→废不锈钢折价 |
| `G06` | 🟠 P1 | 社会库存 ↔ 期货仓单 | — |
| `G09` | 🔴 P0 | 出口 ↔ 进口 | — |
| `G10` | 🔴 P0 | 国产 ↔ 进口/海外 | — |

### 3.2 ⚠️ 9 条 P0 口径冲突案例（固定风险示例，供业务评审参考）

> 以下案例来自 V85 PDF 模板模糊匹配结果，已识别为口径错误。**后续任何模板渲染前都会自动检测这类冲突。**

| # | 模板 | PDF系列名 | zhiji实际指标名 | 命中组 | 匹配分 | 语义问题 |
|---|---|---|---|---|---|---|
| 1 | `TPL-SN-034` | 汽车端消费用锡拟合 | 汽车：消费指数：中国（月） | 🟠 `G04_fitted_vs_official` | 0.44 | 语义互斥:  A命中{'拟合'} B命中{'指数', '消费指数'}, 同属G04_fitted_v |
| 2 | `TPL-AL-013` | LME主要仓库场内库存 | LME：非仓单库存：欧洲（日） | 🔴 `G02_onsite_vs_offsite_inventory` | 0.55 | 语义互斥:  A命中{'场内库存', '场内'} B命中{'非仓单', '仓单库存', '非仓单库存 |
| 3 | `TPL-AO-020/TPL-AO-026` | 氧化铝库存-阿拉丁-堆场站台 | SMM:中国氧化铝在途&站台堆积:库存量:周度 | 🔴 `G03_inventory_vs_transit` | 0.57 | 语义对立:  A独有{'堆场', '堆场站台'} vs B独有{'在途', '站台堆积'} |
| 4 | `TPL-LC-091/TPL-LC-092` | 新能源乘用车 产量 | SMM: 国产乘用车销量-新能源汽车: 周度 | 🔴 `G01_output_vs_consumption` | 1.00 | 语义互斥:  A命中{'产量'} B命中{'销量'}, 同属G01_output_vs_consum |
| 5 | `TPL-LC-023/TPL-LC-024` | 月度锂矿：外采：在途库存：中国：锂盐厂（月） | 锂矿：外采：在途库存：中国：锂盐厂（月） | 🟠 `G03_inventory_vs_transit` | 键匹配 | 键匹配异常:  系列名是zhiji实际指标名的子串(重复嵌入), 疑似指标名拼接错误 |
| 6 | `TPL-AO-042` | 海漂库存-全球主要国家-钢联 | (INVALID, HTTP 500) | ℹ️ INVALID/MISSING | — | 无zhiji_id（API错误/未找到） |
| 7 | `TPL-AO-058` | 发运量-路透-几内亚总和 | (MISSING, HTTP 500) | ℹ️ INVALID/MISSING | — | 无zhiji_id（API错误/未找到） |
| 8 | `TPL-SI-026` | DMC全国开工率 | (INVALID, HTTP 500) | ℹ️ INVALID/MISSING | — | 无zhiji_id（API错误/未找到） |
| 9 | `TPL-SI-028/TPL-SI-034` | 再生铝合金龙头开工率/多晶硅开工率 | (INVALID, HTTP 500) | ℹ️ INVALID/MISSING | — | 无zhiji_id（API错误/未找到） |
| 10 | `TPL-NI-033` | 镍铁理论利润（RKEF,山东） | (MISSING, 未找到候选ID) | ℹ️ INVALID/MISSING | — | 无zhiji_id（API错误/未找到） |
| 11 | `多个铝土矿系列` | 铝土矿产量-XX-XX | 铝土矿：消费量：河北/河南 | 🔴 `G01_output_vs_consumption` | 0.55 | 语义互斥:  A命中{'产量'} B命中{'消费量', '消费'}, 同属G01_output_vs |

> **评审要点**:
> 1. 案例 #1-#5 是**语义冲突型**——口径不等价，必须替换 zhiji_id 或剔除
> 2. 案例 #6-#10 是 **INVALID/MISSING 型**——无有效 zhiji_id，需人工补 ID
> 3. 案例 #11（铝土矿）是**模糊匹配完全失效型**——同一 zhiji_id 覆盖 4 个不同地区系列

### 3.3 语义风险标记规则（图表卡片展示）

| 标记 | 含义 | 展示 | 投产结论 |
|---|---|---|---|
| 🔴 **P0语义冲突** | 命中黑名单互斥组（产量↔消费等） | 图表标题旁加红色「⚠️ P0口径冲突」标签 | **禁止投产** |
| 🟠 **P1口径待核** | 命中近似但不等价组（拟合↔指数等） | 图表标题旁加橙色「🟠口径待复核」标签 | 复核前禁止投产 |
| ✅ **语义通过** | 未命中任何黑名单 | 正常展示 | 可继续评审 |

> 已集成到 `auto_semantic_check.py::check_template_series()`，渲染管线调用后自动在 series 上追加 `render_blocked=True` + `p0_red_tag` 字段。

---

## 4. P0 高优先级图表快速筛选（原§3，编号顺延）

> 按工单要求: 双Y/复合/堆叠类型共 **11** 张，建议最先评审。

| # | 模板 | 品种 | 图表类型 | 标题 | 评分 | 状态 | 预览 |
|---|---|---|---|---|---|---|---|
| 1 | `TPL-SI-026` | SI | 复合混合(折线+柱状) | DMC全国开工率 | 0 | 🔴 PART_OK | [打开](../v85_chart_online_test/rendered/TPL-SI-026.html) |
| 2 | `TPL-LC-029` | LC | 复合混合(折线+柱状) | 碳酸锂 硫酸法 周度产量 | 9 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-LC-029.html) |
| 3 | `TPL-LC-033` | LC | 复合混合(折线+柱状) | SMM 碳酸锂 周度产量 | 9 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-LC-033.html) |
| 4 | `TPL-LC-023` | LC | 堆叠柱状 | SMM 锂矿样本库存:矿山 | 9 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-LC-023.html) |
| 5 | `TPL-LC-026` | LC | 堆叠柱状 | 锂矿 外采 厂内库存 | 9 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-LC-026.html) |
| 6 | `TPL-SI-014` | SI | 堆叠柱状 | 工业硅样本工厂库存(SMM) | 10 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-SI-014.html) |
| 7 | `TPL-LC-024` | LC | 堆叠柱状 | SMM 锂矿样本库存:锂盐厂 | 10 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-LC-024.html) |
| 8 | `TPL-SI-034` | SI | 多折线 | 多晶硅开工率 | 9 | 🔴 PART_OK | [打开](../v85_chart_online_test/rendered/TPL-SI-034.html) |
| 9 | `TPL-SI-044` | SI | 多折线 | 硅片周度产量 | 10 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-SI-044.html) |
| 10 | `TPL-AL-032` | AL | 多折线 | SMM: | 10 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-AL-032.html) |
| 11 | `TPL-AL-033` | AL | 多折线 | SMM: | 10 | 🟢 FULL_OK | [打开](../v85_chart_online_test/rendered/TPL-AL-033.html) |

## 5. 按评分排序（需复核的图表）

> 共 62 张低于满分，按评分升序。评分=0 的 5 张即渲染失败图表。

| 评分 | 模板 | 品种 | 未通过项 | 预览 |
|---|---|---|---|---|
| 0 | 🔴 `TPL-AO-042` | AO | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-AO-042.html) |
| 0 | 🔴 `TPL-AO-058` | AO | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-AO-058.html) |
| 0 | 🔴 `TPL-NI-033` | NI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-NI-033.html) |
| 0 | 🔴 `TPL-SI-026` | SI | 双Y轴配置与axis字段一致/单位正确、数据时间范围完整（≥12个月）、有效数据点充足（≥2 | [预览](../v85_chart_online_test/rendered/TPL-SI-026.html) |
| 0 | 🔴 `TPL-SI-028` | SI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SI-028.html) |
| 7 | 🟢 `TPL-NI-017` | NI | 双Y轴配置与axis字段一致/单位正确、数据时间范围完整（≥12个月）、有效数据点充足（≥2 | [预览](../v85_chart_online_test/rendered/TPL-NI-017.html) |
| 7 | 🟢 `TPL-SI-031` | SI | 双Y轴配置与axis字段一致/单位正确、数据时间范围完整（≥12个月）、有效数据点充足（≥2 | [预览](../v85_chart_online_test/rendered/TPL-SI-031.html) |
| 8 | 🟢 `TPL-AO-040` | AO | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-AO-040.html) |
| 8 | 🟢 `TPL-NI-008` | NI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-NI-008.html) |
| 8 | 🟢 `TPL-NI-012` | NI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-NI-012.html) |
| 8 | 🟢 `TPL-NI-027` | NI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-NI-027.html) |
| 8 | 🟢 `TPL-NI-040` | NI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-NI-040.html) |
| 8 | 🟢 `TPL-SI-019` | SI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SI-019.html) |
| 8 | 🟢 `TPL-SI-033` | SI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SI-033.html) |
| 8 | 🟢 `TPL-SI-036` | SI | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SI-036.html) |
| 8 | 🟢 `TPL-SN-010` | SN | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SN-010.html) |
| 8 | 🟢 `TPL-SN-013` | SN | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SN-013.html) |
| 8 | 🟢 `TPL-SN-025` | SN | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SN-025.html) |
| 8 | 🟢 `TPL-SN-028` | SN | 数据时间范围完整（≥12个月）、有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SN-028.html) |
| 9 | 🟢 `TPL-AL-027` | AL | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-AL-027.html) |
| 9 | 🟢 `TPL-AL-028` | AL | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-AL-028.html) |
| 9 | 🟢 `TPL-AL-029` | AL | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-AL-029.html) |
| 9 | 🟢 `TPL-AO-010` | AO | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-AO-010.html) |
| 9 | 🟢 `TPL-AO-014` | AO | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-AO-014.html) |
| 9 | 🟢 `TPL-AO-015` | AO | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-AO-015.html) |
| 9 | 🟢 `TPL-LC-015` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-015.html) |
| 9 | 🟢 `TPL-LC-016` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-016.html) |
| 9 | 🟢 `TPL-LC-017` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-017.html) |
| 9 | 🟢 `TPL-LC-018` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-018.html) |
| 9 | 🟢 `TPL-LC-019` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-019.html) |
| 9 | 🟢 `TPL-LC-020` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-020.html) |
| 9 | 🟢 `TPL-LC-021` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-021.html) |
| 9 | 🟢 `TPL-LC-023` | LC | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-LC-023.html) |
| 9 | 🟢 `TPL-LC-026` | LC | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-LC-026.html) |
| 9 | 🟢 `TPL-LC-027` | LC | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-LC-027.html) |
| 9 | 🟢 `TPL-LC-029` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-029.html) |
| 9 | 🟢 `TPL-LC-033` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-033.html) |
| 9 | 🟢 `TPL-LC-041` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-041.html) |
| 9 | 🟢 `TPL-LC-051` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-051.html) |
| 9 | 🟢 `TPL-LC-063` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-063.html) |
| 9 | 🟢 `TPL-LC-064` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-064.html) |
| 9 | 🟢 `TPL-LC-065` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-065.html) |
| 9 | 🟢 `TPL-LC-066` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-066.html) |
| 9 | 🟢 `TPL-LC-072` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-072.html) |
| 9 | 🟢 `TPL-LC-073` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-073.html) |
| 9 | 🟢 `TPL-LC-074` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-074.html) |
| 9 | 🟢 `TPL-LC-077` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-077.html) |
| 9 | 🟢 `TPL-LC-079` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-079.html) |
| 9 | 🟢 `TPL-LC-080` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-080.html) |
| 9 | 🟢 `TPL-LC-088` | LC | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-LC-088.html) |
| 9 | 🟢 `TPL-LC-090` | LC | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-LC-090.html) |
| 9 | 🟢 `TPL-NI-007` | NI | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-NI-007.html) |
| 9 | 🟢 `TPL-NI-030` | NI | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-NI-030.html) |
| 9 | 🟢 `TPL-NI-031` | NI | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-NI-031.html) |
| 9 | 🟢 `TPL-NI-032` | NI | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-NI-032.html) |
| 9 | 🟢 `TPL-NI-034` | NI | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-NI-034.html) |
| 9 | 🟢 `TPL-NI-041` | NI | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-NI-041.html) |
| 9 | 🟢 `TPL-SI-020` | SI | 有效数据点充足（≥20点） | [预览](../v85_chart_online_test/rendered/TPL-SI-020.html) |
| 9 | 🟢 `TPL-SI-030` | SI | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-SI-030.html) |
| 9 | 🟢 `TPL-SI-032` | SI | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-SI-032.html) |
| 9 | 🔴 `TPL-SI-034` | SI |  | [预览](../v85_chart_online_test/rendered/TPL-SI-034.html) |
| 9 | 🟢 `TPL-SI-038` | SI | 双Y轴配置与axis字段一致/单位正确 | [预览](../v85_chart_online_test/rendered/TPL-SI-038.html) |

## 6. 按品种分组

| 品种 | 图表数 | 渲染成功 | FULL_OK | PART_OK | 平均评分 | P0类型 | 品种入口 |
|---|---|---|---|---|---|---|---|
| LC 碳酸锂 | 100 | 100 | 100 | 0 | 9.74 | 5 | [TPL-LC-001.html](../v85_chart_online_test/rendered/TPL-LC-001.html) |
| AO 氧化铝 | 63 | 61 | 61 | 2 | 9.60 | 0 | [TPL-AO-001.html](../v85_chart_online_test/rendered/TPL-AO-001.html) |
| SI 工业硅 | 48 | 46 | 45 | 3 | 9.29 | 4 | [TPL-SI-001.html](../v85_chart_online_test/rendered/TPL-SI-001.html) |
| NI 镍 | 47 | 46 | 46 | 1 | 9.43 | 0 | [TPL-NI-001.html](../v85_chart_online_test/rendered/TPL-NI-001.html) |
| AL 铝 | 38 | 38 | 38 | 0 | 9.92 | 2 | [TPL-AL-001.html](../v85_chart_online_test/rendered/TPL-AL-001.html) |
| SN 锡 | 37 | 37 | 37 | 0 | 9.78 | 0 | [TPL-SN-001.html](../v85_chart_online_test/rendered/TPL-SN-001.html) |

## 7. 🔴 PART_OK 图表（禁止投产，强制告警）

| 模板 | 品种 | 标题 | 失败 series | 原因 | 预览 |
|---|---|---|---|---|---|
| `TPL-AO-042` | AO 氧化铝 | 海漂库存-全球主要国家-钢联 | 海漂库存-全球主要国家-钢联 | API错误: HTTP 500 | [预览](../v85_chart_online_test/rendered/TPL-AO-042.html) |
| `TPL-AO-058` | AO 氧化铝 | 发运量-路透-几内亚总和 | 发运量-路透-几内亚总和 | 候选ID无效: API错误: HTTP 500 | [预览](../v85_chart_online_test/rendered/TPL-AO-058.html) |
| `TPL-SI-026` | SI 工业硅 | DMC全国开工率 | DMC全国开工率 | API错误: HTTP 500 | [预览](../v85_chart_online_test/rendered/TPL-SI-026.html) |
| `TPL-SI-026` | SI 工业硅 | DMC全国开工率 | DMC:全国:开工率 | API错误: HTTP 500 | [预览](../v85_chart_online_test/rendered/TPL-SI-026.html) |
| `TPL-SI-028` | SI 工业硅 | 再生铝合金龙头开工率 | 再生铝合金龙头开工率 | API错误: HTTP 500 | [预览](../v85_chart_online_test/rendered/TPL-SI-028.html) |
| `TPL-SI-034` | SI 工业硅 | 多晶硅开工率 | 中国多晶硅开工率 | API错误: HTTP 500 | [预览](../v85_chart_online_test/rendered/TPL-SI-034.html) |
| `TPL-NI-033` | NI 镍 | 镍铁理论利润（RKEF,山东） | 镍铁理论利润（RKEF,山东） | 未找到候选ID | [预览](../v85_chart_online_test/rendered/TPL-NI-033.html) |

> 注: TPL-SI-034 含 1 条 INVALID + 2 条正常 series，属部分可用，同样禁止投产。

## 8. 建议评审顺序

| 步骤 | 内容 | 预计耗时 | 产出 |
|---|---|---|---|
| 1 | P0 高优先级图表（复合/堆叠/多折线，11张） | 20min | 图表样式/双Y轴确认 |
| 2 | P0 口径冲突抽检（9项） | 30min | 口径判定结论 |
| 3 | P1 匹配抽检（17项） | 20min | 键语义确认 |
| 4 | 渲染失败图表（5张）+ 异常指标（7条） | 15min | 补 ID 清单 |
| 5 | 评分 < 10 的其余图表（38张） | 25min | 视觉细节确认 |
| 6 | 节点映射索引核对 | 10min | 节点完整性 |
| 7 | 汇总评审结论，走 `pre_merge_checklist.md` | 10min | 合并决定 |

**合计约 130 分钟（2.2 小时）**
