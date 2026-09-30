# THS Chart Template → HERMES 指标匹配检查报告

- 检查时间: 2026-09-29 22:31:45
- THS 模板总数: **155**
- 品种 (variety): AL, CU, LI, NI, SI, SN, ZN
- HERMES 支持 plot type: 季节图, 时序图

## 1. 分类统计

| 状态 | 数量 | 占比 |
|---|---:|---:|
| FULL_MATCH | 0 | 0.0% |
| PARTIAL_MISS | 139 | 89.7% |
| ALL_MISS | 16 | 10.3% |
| PLOT_TYPE_NOT_SUPPORT | 0 | 0.0% |
| EMPTY_TEMPLATE | 0 | 0.0% |

- 完全匹配 (all indicators in indicators_v1 + plot 支持): **0**
- 部分缺失 (some indicators missing): **139**
- 全部缺失 (all indicators missing): **16**
- 图型不支持 (all matched, plot 不在 HERMES 支持集): **0**

- 指标精确匹配次数: 2
- 指标模糊匹配次数: 497
- 唯一缺失指标数: 1396

> **⚠️ 方法说明**: 模糊匹配使用 `difflib.get_close_matches(cutoff=0.6)`，对中文文本会产生**假阳性**（如「沪铝」误配到「沪铅」），因此 FULL_MATCH 数偏乐观、缺失指标数偏保守。请结合 `matched_ids` 列人工复核关键字段的实际匹配对象。

## 2. 按品种统计 (missing templates)

| 品种 | 模板总数 | 非 FULL_MATCH | 缺失率 |
|---|---:|---:|---:|
| AL | 9 | 9 | 100.0% |
| CU | 6 | 6 | 100.0% |
| LI | 19 | 19 | 100.0% |
| NI | 32 | 32 | 100.0% |
| SI | 29 | 29 | 100.0% |
| SN | 30 | 30 | 100.0% |
| ZN | 30 | 30 | 100.0% |

## 3. THS plot type 分布 (与 HERMES 支持情况)

| plot_type | 模板数 | HERMES 支持 |
|---|---:|:---:|
| 排名图 | 2 | ❌ |
| 时序图 | 153 | ✅ |

**HERMES 不支持的 plot type 明细:**
- 排名图: 2 个模板

## 4. 高风险模板清单 (ALL_MISS + PLOT_TYPE_NOT_SUPPORT)

共 **16** 个高风险模板。

| template_id | 品种 | plot_type | status | 缺失指标数 | 示例缺失指标 |
|---|---|---|---|---:|---|
| THS-CU-4.1 | CU | 时序图 | ALL_MISS | 2 | LME铜库存、上期所铜库存、COMEX铜库存, 各LME仓库/地点铜库存 |
| THS-CU-4.2 | CU | 时序图 | ALL_MISS | 4 | SHFE铜仓单、沪铜主力价格、现货升贴水, 电解铜仓单、国际铜仓单 |
| THS-CU-4.4 | CU | 时序图 | ALL_MISS | 7 | LME-approved warehouses, Cancelled warrants |
| THS-LI-3.1.2 | LI | 时序图 | ALL_MISS | 10 | 澳大利亚锂矿产量（万吨LCE）, 非洲锂矿产量（万吨LCE） |
| THS-LI-4.1 | LI | 时序图 | ALL_MISS | 10 | 碳酸锂交易所库存（万吨LCE）, 氢氧化锂交易所库存（万吨LCE） |
| THS-NI-3.1.4 | NI | 时序图 | ALL_MISS | 20 | 镍精矿进口总量（万吨）, 镍精矿进口量（吨） |
| THS-SI-3.1.1 | SI | 时序图 | ALL_MISS | 10 | 海外硅矿季度产量（万吨）, 海外硅矿季度产能（万吨） |
| THS-SI-5.2 | SI | 时序图 | ALL_MISS | 11 | 工业硅下游终端产量（万吨）, 工业硅下游消费占比（%） |
| THS-SI-5.3 | SI | 时序图 | ALL_MISS | 10 | 工业硅下游排产计划量（万吨）, 工业硅下游订单量（万吨） |
| THS-ZN-3.1.1 | ZN | 时序图 | ALL_MISS | 12 | 海外锌矿产量（万吨）, 海外锌矿加工费TC（美元/吨干矿） |
| THS-ZN-3.1.2 | ZN | 时序图 | ALL_MISS | 30 | 秘鲁锌矿产量（万吨）, 澳大利亚锌矿产量（万吨） |
| THS-ZN-4.4 | ZN | 时序图 | ALL_MISS | 10 | 国内锌厂内锌锭库存（万吨）, 国内锌社会库存总量（万吨） |
| THS-ZN-4.5 | ZN | 时序图 | ALL_MISS | 8 | 国内锌隐性库存总量（万吨）, 国内锌社会库存总量（万吨） |
| THS-ZN-6.2 | ZN | 时序图 | ALL_MISS | 11 | 国内电锌进口量（万吨）, 国内电锌出口量（万吨） |
| THS-ZN-7.1 | ZN | 时序图 | ALL_MISS | 11 | 国内锌冶炼成本（元/吨）, 国内锌冶炼成本分位（%） |
| THS-ZN-7.2 | ZN | 时序图 | ALL_MISS | 10 | 国内锌冶炼日度利润（元/吨）, 国内锌精炼日度产量（吨） |

## 5. Top 缺失指标 (按被引用次数)

| # | 指标名 | 引用次数 | 示例 template_id |
|---:|---|---:|---|
| 1 | 镍精矿TC（美元/吨干矿） | 18 | THS-NI-3.1, THS-NI-3.1.5, THS-NI-3.2.1 |
| 2 | 沪伦比（元/吨） | 12 | THS-LI-2.3, THS-ZN-2.1, THS-ZN-2.2 |
| 3 | 近3年同月产量均值（万吨） | 12 | THS-SI-3.1.2, THS-SI-3.1.3, THS-SI-3.2.1 |
| 4 | 近3年同月产量标准差（万吨） | 12 | THS-SI-3.1.2, THS-SI-3.1.3, THS-SI-3.2.1 |
| 5 | 近3年同月均值（万吨LCE） | 10 | THS-LI-3.1.2, THS-LI-3.1.3, THS-LI-3.1.4 |
| 6 | 近3年同月标准差（万吨LCE） | 10 | THS-LI-3.1.2, THS-LI-3.1.3, THS-LI-3.1.4 |
| 7 | 近3年同月进口量均值（万吨） | 10 | THS-NI-6.1, THS-NI-6.2, THS-SI-3.1.4 |
| 8 | 近3年同月进口量标准差（万吨） | 10 | THS-NI-6.1, THS-NI-6.2, THS-SI-3.1.4 |
| 9 | 近3年同月开工率均值（%） | 8 | THS-NI-3.2.2, THS-NI-5.1, THS-SI-3.2.2 |
| 10 | 近3年同月开工率标准差（%） | 8 | THS-NI-3.2.2, THS-NI-5.1, THS-SI-3.2.2 |
| 11 | 国内锌精炼产量（万吨） | 7 | THS-ZN-3.2.1, THS-ZN-3.2.2, THS-ZN-3.2.3 |
| 12 | 月差（元/吨） | 7 | THS-LI-2.1, THS-LI-2.2, THS-LI-2.4 |
| 13 | 近3年同月出口量均值（万吨） | 7 | THS-NI-6.3, THS-SI-6.2, THS-SI-6.3 |
| 14 | 近3年同月出口量标准差（万吨） | 7 | THS-NI-6.3, THS-SI-6.2, THS-SI-6.3 |
| 15 | 上期所锌仓单注册量（手） | 6 | THS-ZN-3.1.4, THS-ZN-3.1.5, THS-ZN-3.2.4 |
| 16 | 加工费（元/吨） | 6 | THS-NI-7.1, THS-NI-7.2, THS-NI-7.3 |
| 17 | 多空持仓比（%） | 6 | THS-LI-2.1, THS-LI-2.6, THS-SN-2.1 |
| 18 | 上期所镍仓单量（手） | 5 | THS-NI-4.1, THS-NI-4.2, THS-NI-4.3 |
| 19 | 冶炼利润（元/吨） | 5 | THS-LI-2.5, THS-LI-3.2.4, THS-SN-7.1 |
| 20 | 成交量（手） | 5 | THS-LI-2.1, THS-LI-2.6, THS-SN-2.1 |
| 21 | 持仓量（手） | 5 | THS-LI-2.1, THS-LI-2.4, THS-LI-2.6 |
| 22 | 汇率（USD/CNY） | 5 | THS-NI-2.1, THS-NI-2.2, THS-NI-2.3 |
| 23 | 电价（元/度） | 5 | THS-NI-7.1, THS-NI-7.3, THS-SN-7.1 |
| 24 | 电解锌冶炼利润（元/吨） | 5 | THS-ZN-2.5, THS-ZN-3.1.5, THS-ZN-3.2.1 |
| 25 | 锌精矿TC（美元/吨干矿） | 5 | THS-ZN-2.5, THS-ZN-3.1.5, THS-ZN-3.2.1 |
| 26 | 保税区仓单（手） | 4 | THS-SN-6.1, THS-SN-6.2, THS-SN-6.3 |
| 27 | 国内锌社会库存总量（万吨） | 4 | THS-ZN-4.3, THS-ZN-4.4, THS-ZN-4.5 |
| 28 | 现货升贴水（元/吨） | 4 | THS-LI-2.1, THS-SN-2.1, THS-ZN-2.1 |
| 29 | 电解镍产量（万吨） | 4 | THS-NI-3.1.3, THS-NI-3.2, THS-NI-3.2.1 |
| 30 | 电解镍冶炼利润（元/吨） | 4 | THS-NI-2.5, THS-NI-3.1.5, THS-NI-3.2 |

## 6. 输出文件

- `analysis\e2e_output\v85\ths_check\ths_chart_template_list.json` (154206 B)
- `analysis\e2e_output\v85\ths_check\ths_chart_check_result.csv` (194475 B)
- `analysis\e2e_output\v85\ths_check\ths_missing_indicator_list.csv` (77607 B)
- `analysis\e2e_output\v85\ths_check\ths_chart_check_summary.md` (6894 B)
