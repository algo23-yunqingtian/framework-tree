# ALL_MISS 高风险模板专项报告

- 报告时间: 自动生成
- ALL_MISS 模板数: **16**
- 涵盖品种: CU, LI, NI, SI, ZN
- 模板图型: 全部为时序图（HERMES 已支持）
- 缺失原因: 全部指标在 indicators_v1 中均未找到匹配

---

## 分类说明

| 分类 | 含义 | 处置方式 |
|------|------|----------|
| CAT_A_RAW_MISS | 原始业务指标，库内确实无 | 需新增数据源接入 |
| CAT_B_DERIVED | 衍生计算指标（统计量） | 需计算引擎，不直接入库 |
| CAT_C_ALIAS_EXIST | 实体存在，仅命名差异 | 扩充别名映射即可 |

---

## THS-CU-4.1 (CU)

- **图表标题**: 铜 · 4.1 · LME铜库存、上期所铜库存、COMEX铜库存 vs 各LME仓库/地点铜库存 · 时序图
- **指标总数**: 2

- **分类统计**:
  - CAT_C_ALIAS_EXIST: 2

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | LME铜库存、上期所铜库存、COMEX铜库存 | CAT_C_ALIAS_EXIST |
| 2 | 各LME仓库/地点铜库存 | CAT_C_ALIAS_EXIST |

---

## THS-CU-4.2 (CU)

- **图表标题**: 铜 · 4.2 · SHFE铜仓单、沪铜主力价格、现货升贴水 等4项 · 时序图
- **指标总数**: 4

- **分类统计**:
  - CAT_C_ALIAS_EXIST: 4

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | SHFE铜仓单、沪铜主力价格、现货升贴水 | CAT_C_ALIAS_EXIST |
| 2 | 电解铜仓单、国际铜仓单 | CAT_C_ALIAS_EXIST |
| 3 | 仓单注册量、仓单注销量、仓单总量 | CAT_C_ALIAS_EXIST |
| 4 | 上海、江苏、广东、浙江等仓单数量 | CAT_C_ALIAS_EXIST |

---

## THS-CU-4.4 (CU)

- **图表标题**: 铜 · 4.4 · LME-approved warehouses 等7项 · 时序图
- **指标总数**: 7

- **分类统计**:
  - CAT_A_RAW_MISS: 2
  - CAT_C_ALIAS_EXIST: 5

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | LME-approved warehouses | CAT_A_RAW_MISS |
| 2 | Cancelled warrants | CAT_A_RAW_MISS |
| 3 | 上海保税区铜库存、广东保税区铜库存 | CAT_C_ALIAS_EXIST |
| 4 | 保税区库存、沪伦进口盈亏或COMEX-LME价差 | CAT_C_ALIAS_EXIST |
| 5 | 上海、广东等保税区库存 | CAT_C_ALIAS_EXIST |
| 6 | 在途海运铜库存估算 | CAT_C_ALIAS_EXIST |
| 7 | 保税区库存、进口利润、精废价差 | CAT_C_ALIAS_EXIST |

---

## THS-LI-3.1.2 (LI)

- **图表标题**: 锂 · 3.1.2 · 澳大利亚锂矿产量（万吨LCE） 等10项 · 时序图
- **指标总数**: 10

- **分类统计**:
  - CAT_A_RAW_MISS: 7
  - CAT_B_DERIVED: 2
  - CAT_C_ALIAS_EXIST: 1

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 澳大利亚锂矿产量（万吨LCE） | CAT_A_RAW_MISS |
| 2 | 非洲锂矿产量（万吨LCE） | CAT_A_RAW_MISS |
| 3 | 南美锂矿产量（万吨LCE） | CAT_A_RAW_MISS |
| 4 | 亚洲锂矿产量（万吨LCE） | CAT_A_RAW_MISS |
| 5 | 海外锂矿进口量分国别（万吨LCE） | CAT_A_RAW_MISS |
| 6 | 海外锂矿出口量分国别（万吨LCE） | CAT_A_RAW_MISS |
| 7 | 海外锂矿库存分国别（万吨LCE） | CAT_C_ALIAS_EXIST |
| 8 | 海外锂矿产能分国别（万吨LCE） | CAT_A_RAW_MISS |
| 9 | 近3年同月均值（万吨LCE） | CAT_B_DERIVED |
| 10 | 近3年同月标准差（万吨LCE） | CAT_B_DERIVED |

---

## THS-LI-4.1 (LI)

- **图表标题**: 锂 · 4.1 · 碳酸锂交易所库存（万吨LCE） 等10项 · 时序图
- **指标总数**: 10

- **分类统计**:
  - CAT_B_DERIVED: 2
  - CAT_C_ALIAS_EXIST: 8

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 碳酸锂交易所库存（万吨LCE） | CAT_C_ALIAS_EXIST |
| 2 | 氢氧化锂交易所库存（万吨LCE） | CAT_C_ALIAS_EXIST |
| 3 | 电池级碳酸锂交易所库存（万吨LCE） | CAT_C_ALIAS_EXIST |
| 4 | 工业级碳酸锂交易所库存（万吨LCE） | CAT_C_ALIAS_EXIST |
| 5 | 仓单数量（万吨LCE） | CAT_C_ALIAS_EXIST |
| 6 | 注销仓单数量（万吨LCE） | CAT_C_ALIAS_EXIST |
| 7 | 在途库存（万吨LCE） | CAT_C_ALIAS_EXIST |
| 8 | 隐性库存（万吨LCE） | CAT_C_ALIAS_EXIST |
| 9 | 近3年同月均值（万吨LCE） | CAT_B_DERIVED |
| 10 | 近3年同月标准差（万吨LCE） | CAT_B_DERIVED |

---

## THS-NI-3.1.4 (NI)

- **图表标题**: 镍 · 3.1.4 · 镍精矿进口总量（万吨） 等20项 · 时序图
- **指标总数**: 20

- **分类统计**:
  - CAT_A_RAW_MISS: 15
  - CAT_B_DERIVED: 5

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 镍精矿进口总量（万吨） | CAT_A_RAW_MISS |
| 2 | 镍精矿进口量（吨） | CAT_A_RAW_MISS |
| 3 | 中国从印尼进口镍精矿量（万吨） | CAT_A_RAW_MISS |
| 4 | 印尼进口占比（%） | CAT_B_DERIVED |
| 5 | 中国从菲律宾进口镍精矿量（万吨） | CAT_A_RAW_MISS |
| 6 | 菲律宾进口占比（%） | CAT_B_DERIVED |
| 7 | 中国从新喀里多尼亚进口镍精矿量（万吨） | CAT_A_RAW_MISS |
| 8 | 新喀里多尼亚进口占比（%） | CAT_B_DERIVED |
| 9 | 印尼进口量（万吨） | CAT_A_RAW_MISS |
| 10 | 菲律宾进口量（万吨） | CAT_A_RAW_MISS |
| 11 | 新喀里多尼亚进口量（万吨） | CAT_A_RAW_MISS |
| 12 | 澳大利亚进口量（万吨） | CAT_A_RAW_MISS |
| 13 | 国内镍精炼产量（万吨） | CAT_A_RAW_MISS |
| 14 | 镍精矿进口量（万吨） | CAT_A_RAW_MISS |
| 15 | 进口依赖度（%） | CAT_A_RAW_MISS |
| 16 | 近3年同月进口总量均值（万吨） | CAT_B_DERIVED |
| 17 | 近3年同月进口总量标准差（万吨） | CAT_B_DERIVED |
| 18 | 印尼镍精矿进口量（万吨） | CAT_A_RAW_MISS |
| 19 | 菲律宾镍精矿进口量（万吨） | CAT_A_RAW_MISS |
| 20 | 印尼-菲律宾进口量比（倍） | CAT_A_RAW_MISS |

---

## THS-SI-3.1.1 (SI)

- **图表标题**: 硅 · 3.1.1 · 海外硅矿季度产量（万吨） 等10项 · 时序图
- **指标总数**: 10

- **分类统计**:
  - CAT_A_RAW_MISS: 7
  - CAT_B_DERIVED: 2
  - CAT_C_ALIAS_EXIST: 1

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 海外硅矿季度产量（万吨） | CAT_A_RAW_MISS |
| 2 | 海外硅矿季度产能（万吨） | CAT_A_RAW_MISS |
| 3 | 海外硅矿季度开工率（%） | CAT_C_ALIAS_EXIST |
| 4 | 海外硅矿季度产能利用率（%） | CAT_A_RAW_MISS |
| 5 | 海外硅矿季度检修量（万吨） | CAT_A_RAW_MISS |
| 6 | 海外硅矿季度进口量（万吨） | CAT_A_RAW_MISS |
| 7 | 海外硅矿季度再生产量（万吨） | CAT_A_RAW_MISS |
| 8 | 海外硅矿季度加工费TC（元/吨） | CAT_A_RAW_MISS |
| 9 | 近3年同季产量均值（万吨） | CAT_B_DERIVED |
| 10 | 近3年同季产量标准差（万吨） | CAT_B_DERIVED |

---

## THS-SI-5.2 (SI)

- **图表标题**: 硅 · 5.2 · 工业硅下游终端产量（万吨） 等11项 · 时序图
- **指标总数**: 11

- **分类统计**:
  - CAT_A_RAW_MISS: 6
  - CAT_B_DERIVED: 5

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 工业硅下游终端产量（万吨） | CAT_A_RAW_MISS |
| 2 | 工业硅下游消费占比（%） | CAT_B_DERIVED |
| 3 | 多晶硅下游终端产量（万吨） | CAT_A_RAW_MISS |
| 4 | 多晶硅下游消费占比（%） | CAT_B_DERIVED |
| 5 | 金属硅下游终端产量（万吨） | CAT_A_RAW_MISS |
| 6 | 金属硅下游消费占比（%） | CAT_B_DERIVED |
| 7 | 工业硅下游订单量（万吨） | CAT_A_RAW_MISS |
| 8 | 多晶硅下游订单量（万吨） | CAT_A_RAW_MISS |
| 9 | 近3年同月消费占比均值（%） | CAT_B_DERIVED |
| 10 | 近3年同月消费占比标准差（%） | CAT_B_DERIVED |
| 11 | 工业硅下游消费增速（%） | CAT_A_RAW_MISS |

---

## THS-SI-5.3 (SI)

- **图表标题**: 硅 · 5.3 · 工业硅下游排产计划量（万吨） 等10项 · 时序图
- **指标总数**: 10

- **分类统计**:
  - CAT_A_RAW_MISS: 8
  - CAT_B_DERIVED: 2

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 工业硅下游排产计划量（万吨） | CAT_A_RAW_MISS |
| 2 | 工业硅下游订单量（万吨） | CAT_A_RAW_MISS |
| 3 | 多晶硅下游排产计划量（万吨） | CAT_A_RAW_MISS |
| 4 | 多晶硅下游订单量（万吨） | CAT_A_RAW_MISS |
| 5 | 工业硅下游采购量（万吨） | CAT_A_RAW_MISS |
| 6 | 工业硅下游预付款（亿元） | CAT_A_RAW_MISS |
| 7 | 近3年同月排产计划量均值（万吨） | CAT_B_DERIVED |
| 8 | 近3年同月排产计划量标准差（万吨） | CAT_B_DERIVED |
| 9 | 多晶硅下游预付款（亿元） | CAT_A_RAW_MISS |
| 10 | 多晶硅下游采购量（万吨） | CAT_A_RAW_MISS |

---

## THS-ZN-3.1.1 (ZN)

- **图表标题**: 锌 · 3.1.1 · 海外锌矿产量（万吨） 等12项 · 时序图
- **指标总数**: 12

- **分类统计**:
  - CAT_A_RAW_MISS: 8
  - CAT_B_DERIVED: 2
  - CAT_C_ALIAS_EXIST: 2

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 海外锌矿产量（万吨） | CAT_A_RAW_MISS |
| 2 | 海外锌矿加工费TC（美元/吨干矿） | CAT_C_ALIAS_EXIST |
| 3 | 海外锌精炼产量（万吨） | CAT_A_RAW_MISS |
| 4 | 海外锌矿开工率（%） | CAT_C_ALIAS_EXIST |
| 5 | 海外锌矿产能利用率（%） | CAT_A_RAW_MISS |
| 6 | 海外锌矿产能（万吨） | CAT_A_RAW_MISS |
| 7 | 海外锌矿检修量（万吨） | CAT_A_RAW_MISS |
| 8 | 海外锌矿进口量（万吨） | CAT_A_RAW_MISS |
| 9 | 海外锌矿进口量分国别（万吨） | CAT_A_RAW_MISS |
| 10 | 海外锌矿再生产量（万吨） | CAT_A_RAW_MISS |
| 11 | 近3年同季产量均值（万吨） | CAT_B_DERIVED |
| 12 | 近3年同季产量标准差（万吨） | CAT_B_DERIVED |

---

## THS-ZN-3.1.2 (ZN)

- **图表标题**: 锌 · 3.1.2 · 秘鲁锌矿产量（万吨） 等30项 · 时序图
- **指标总数**: 30

- **分类统计**:
  - CAT_A_RAW_MISS: 24
  - CAT_B_DERIVED: 2
  - CAT_C_ALIAS_EXIST: 4

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 秘鲁锌矿产量（万吨） | CAT_A_RAW_MISS |
| 2 | 澳大利亚锌矿产量（万吨） | CAT_A_RAW_MISS |
| 3 | 印度锌矿产量（万吨） | CAT_A_RAW_MISS |
| 4 | 南非锌矿产量（万吨） | CAT_A_RAW_MISS |
| 5 | 秘鲁锌精炼产量（万吨） | CAT_A_RAW_MISS |
| 6 | 澳大利亚锌精炼产量（万吨） | CAT_A_RAW_MISS |
| 7 | 印度锌精炼产量（万吨） | CAT_A_RAW_MISS |
| 8 | 南非锌精炼产量（万吨） | CAT_A_RAW_MISS |
| 9 | 秘鲁锌矿开工率（%） | CAT_C_ALIAS_EXIST |
| 10 | 澳大利亚锌矿开工率（%） | CAT_C_ALIAS_EXIST |
| 11 | 印度锌矿开工率（%） | CAT_C_ALIAS_EXIST |
| 12 | 南非锌矿开工率（%） | CAT_C_ALIAS_EXIST |
| 13 | 秘鲁锌矿产能利用率（%） | CAT_A_RAW_MISS |
| 14 | 澳大利亚锌矿产能利用率（%） | CAT_A_RAW_MISS |
| 15 | 印度锌矿产能利用率（%） | CAT_A_RAW_MISS |
| 16 | 南非锌矿产能利用率（%） | CAT_A_RAW_MISS |
| 17 | 秘鲁锌矿检修量（万吨） | CAT_A_RAW_MISS |
| 18 | 澳大利亚锌矿检修量（万吨） | CAT_A_RAW_MISS |
| 19 | 印度锌矿检修量（万吨） | CAT_A_RAW_MISS |
| 20 | 南非锌矿检修量（万吨） | CAT_A_RAW_MISS |
| 21 | 秘鲁锌矿进口量（万吨） | CAT_A_RAW_MISS |
| 22 | 澳大利亚锌矿进口量（万吨） | CAT_A_RAW_MISS |
| 23 | 印度锌矿进口量（万吨） | CAT_A_RAW_MISS |
| 24 | 南非锌矿进口量（万吨） | CAT_A_RAW_MISS |
| 25 | 秘鲁锌矿再生产量（万吨） | CAT_A_RAW_MISS |
| 26 | 澳大利亚锌矿再生产量（万吨） | CAT_A_RAW_MISS |
| 27 | 印度锌矿再生产量（万吨） | CAT_A_RAW_MISS |
| 28 | 南非锌矿再生产量（万吨） | CAT_A_RAW_MISS |
| 29 | 近3年同月秘鲁产量均值（万吨） | CAT_B_DERIVED |
| 30 | 近3年同月秘鲁产量标准差（万吨） | CAT_B_DERIVED |

---

## THS-ZN-4.4 (ZN)

- **图表标题**: 锌 · 4.4 · 国内锌厂内锌锭库存（万吨） 等10项 · 时序图
- **指标总数**: 10

- **分类统计**:
  - CAT_B_DERIVED: 3
  - CAT_C_ALIAS_EXIST: 7

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 国内锌厂内锌锭库存（万吨） | CAT_C_ALIAS_EXIST |
| 2 | 国内锌社会库存总量（万吨） | CAT_C_ALIAS_EXIST |
| 3 | 国内锌厂内锌合金库存（万吨） | CAT_C_ALIAS_EXIST |
| 4 | 国内锌厂内库存占比（%） | CAT_B_DERIVED |
| 5 | 国内锌厂内库存天数（天） | CAT_C_ALIAS_EXIST |
| 6 | 近3年同月/同周库存均值（万吨） | CAT_B_DERIVED |
| 7 | 近3年同月/同周库存标准差（万吨） | CAT_B_DERIVED |
| 8 | 上期所锌仓单注册量（手） | CAT_C_ALIAS_EXIST |
| 9 | 国内锌厂内锌锭库存分地区（万吨） | CAT_C_ALIAS_EXIST |
| 10 | 锌锭现货升贴水（元/吨） | CAT_C_ALIAS_EXIST |

---

## THS-ZN-4.5 (ZN)

- **图表标题**: 锌 · 4.5 · 国内锌隐性库存总量（万吨） 等8项 · 时序图
- **指标总数**: 8

- **分类统计**:
  - CAT_B_DERIVED: 3
  - CAT_C_ALIAS_EXIST: 5

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 国内锌隐性库存总量（万吨） | CAT_C_ALIAS_EXIST |
| 2 | 国内锌社会库存总量（万吨） | CAT_C_ALIAS_EXIST |
| 3 | 国内锌在途库存总量（万吨） | CAT_C_ALIAS_EXIST |
| 4 | 国内锌隐性库存占比（%） | CAT_B_DERIVED |
| 5 | 国内锌在途库存占比（%） | CAT_B_DERIVED |
| 6 | 近3年同月/同周均值（万吨） | CAT_B_DERIVED |
| 7 | 国内锌隐性库存分地区（万吨） | CAT_C_ALIAS_EXIST |
| 8 | 锌锭现货升贴水（元/吨） | CAT_C_ALIAS_EXIST |

---

## THS-ZN-6.2 (ZN)

- **图表标题**: 锌 · 6.2 · 国内电锌进口量（万吨） 等11项 · 时序图
- **指标总数**: 11

- **分类统计**:
  - CAT_A_RAW_MISS: 7
  - CAT_B_DERIVED: 2
  - CAT_C_ALIAS_EXIST: 2

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 国内电锌进口量（万吨） | CAT_A_RAW_MISS |
| 2 | 国内电锌出口量（万吨） | CAT_A_RAW_MISS |
| 3 | 国内电锌净进口量（万吨） | CAT_A_RAW_MISS |
| 4 | 国内电锌进口量分国别（万吨） | CAT_A_RAW_MISS |
| 5 | 国内电锌进口量总量（万吨） | CAT_A_RAW_MISS |
| 6 | 国内电锌保税区库存（万吨） | CAT_C_ALIAS_EXIST |
| 7 | 国内电锌保税区仓单（手） | CAT_C_ALIAS_EXIST |
| 8 | 近3年同月出口量均值（万吨） | CAT_B_DERIVED |
| 9 | 近3年同月出口量标准差（万吨） | CAT_B_DERIVED |
| 10 | 国内电锌进出口金额（亿美元） | CAT_A_RAW_MISS |
| 11 | 国内电锌关税税率（%） | CAT_A_RAW_MISS |

---

## THS-ZN-7.1 (ZN)

- **图表标题**: 锌 · 7.1 · 国内锌冶炼成本（元/吨） 等11项 · 时序图
- **指标总数**: 11

- **分类统计**:
  - CAT_A_RAW_MISS: 6
  - CAT_B_DERIVED: 3
  - CAT_C_ALIAS_EXIST: 2

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 国内锌冶炼成本（元/吨） | CAT_A_RAW_MISS |
| 2 | 国内锌冶炼成本分位（%） | CAT_B_DERIVED |
| 3 | 国内锌精炼产量（万吨） | CAT_A_RAW_MISS |
| 4 | 国内锌冶炼加工费（元/吨） | CAT_C_ALIAS_EXIST |
| 5 | 国内锌电解成本（元/吨） | CAT_A_RAW_MISS |
| 6 | 国内锌现金成本（元/吨） | CAT_A_RAW_MISS |
| 7 | 国内锌冶炼利润（元/吨） | CAT_C_ALIAS_EXIST |
| 8 | 国内锌电价（元/度） | CAT_A_RAW_MISS |
| 9 | 国内锌原料成本（元/吨） | CAT_A_RAW_MISS |
| 10 | 近3年同季成本均值（元/吨） | CAT_B_DERIVED |
| 11 | 近3年同季成本标准差（元/吨） | CAT_B_DERIVED |

---

## THS-ZN-7.2 (ZN)

- **图表标题**: 锌 · 7.2 · 国内锌冶炼日度利润（元/吨） 等10项 · 时序图
- **指标总数**: 10

- **分类统计**:
  - CAT_A_RAW_MISS: 6
  - CAT_B_DERIVED: 3
  - CAT_C_ALIAS_EXIST: 1

| # | 指标名称 | 分类 |
|---|----------|------|
| 1 | 国内锌冶炼日度利润（元/吨） | CAT_A_RAW_MISS |
| 2 | 国内锌精炼日度产量（吨） | CAT_A_RAW_MISS |
| 3 | 国内锌电解日度利润（元/吨） | CAT_A_RAW_MISS |
| 4 | 国内锌冶炼日度加工费（元/吨） | CAT_C_ALIAS_EXIST |
| 5 | 国内锌冶炼日度原料成本（元/吨） | CAT_A_RAW_MISS |
| 6 | 国内锌冶炼日度电价（元/度） | CAT_A_RAW_MISS |
| 7 | 国内锌冶炼日度现金成本（元/吨） | CAT_A_RAW_MISS |
| 8 | 国内锌冶炼日度分位成本（%） | CAT_B_DERIVED |
| 9 | 近3年同日产量均值（吨） | CAT_B_DERIVED |
| 10 | 近3年同日产量标准差（吨） | CAT_B_DERIVED |

---

## 汇总

- 16 个 ALL_MISS 模板共含 **176** 条指标
- CAT_A_RAW_MISS: 96 (54.5%)
- CAT_B_DERIVED: 36 (20.5%)
- CAT_C_ALIAS_EXIST: 44 (25.0%)

### 按品种分布

| 品种 | 模板数 | 指标总数 |
|------|--------|----------|
| CU | 3 | 13 |
| LI | 2 | 20 |
| NI | 1 | 20 |
| SI | 3 | 31 |
| ZN | 7 | 92 |

### 缺失指标集中度分析

> 16 个 ALL_MISS 模板集中在以下板块:
> - **供给(3.x)**: NI-3.1.4, SI-3.1.1, ZN-3.1.1, ZN-3.1.2
> - **库存(4.x)**: CU-4.1, CU-4.2, CU-4.4, LI-4.1, ZN-4.4, ZN-4.5
> - **需求(5.x)**: SI-5.2, SI-5.3
> - **进出口(6.x)**: ZN-6.2
> - **成本利润(7.x)**: ZN-7.1, ZN-7.2
>
> **共性特征**: 这些板块的指标多为细分地区/细分工艺的原始业务数据（如「秘鲁锌矿产量」、「印尼镍矿产量」），
> indicators_v1 中尚无对应的分国别/分区域细粒度指标。
