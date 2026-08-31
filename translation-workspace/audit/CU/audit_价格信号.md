# CU·价格信号 板块审计（Step1 同花顺回复）
# 抓取时间: 2026-09-01 03:26:39
# 覆盖子节点数: 6

---

问财 模型答案生成完成
已深度思考 · 思考 16秒 · 3 条资料

结论：建议将原24张“价格信号”图压缩为16张核心图，删除7类不合格/非价格信号指标，原2.1子节点拆分为3个独立模块。
本次调整严格遵循期货研报图表规范：仅保留可直接交易、可连续追踪、强解释价格的指标，所有统计派生类、临时不可追踪、弱相关凑数指标全部剔除；TC/RC、冶炼利润、矿端产量、废铜供给等指标移至「铜·矿冶利润与供给」板块，2.6持仓席位板块同步剔除所有环比/占比/集中度类派生指标，仅保留可连续拼接的原始持仓数据。

1. 结构调整总览

原方案2.1“沪铜—伦铜—进口盈亏三角图”实际混入了库存、升贴水、矿端、成本、汇率、全球库存、期限结构、持仓等多类指标，结构过于臃肿。建议拆分为三个独立模块：

2.1 全球铜价与跨市比价：仅保留沪铜、LME铜、COMEX铜、沪伦比、COMEX-LME溢价、跨市仓单；
2.2 国内现货与基差：仅保留SMM现货、基差、品级升贴水、区域价差、Mysteel现货成交；
2.3 海外价格与LME期限结构：仅保留LME现金/3M/15M、LME 0-3价差、LME库存、COMEX量价持仓、CFTC持仓。

被删除的原2.1内指标归属调整如下：

原指标	处理意见	建议归属
TC/RC、铜精矿港口库存、进口量、冶炼利润	非价格信号，属于矿端供给与冶炼利润	铜·矿冶利润与供给
社会库存季节性、库存天数、全球三大交易所库存总量	库存为独立价格验证维度	铜·库存与交割压力
汇率、关税、航运运费	属于进口盈亏与跨市套利测算输入	铜·跨市套利与进口盈亏
冶炼厂开工率、检修量、产量	属于供给端，且检修量属临时不可追踪	铜·供给与加工链
废铜供给、再生铜杆开工率	属于再生铜需求与替代弹性	铜·再生铜与废铜替代
2. 核心删除清单
2.1 统计派生类全部删除

以下类型不符合“原始信号”要求，禁止出现在价格信号主图中：近N年均值、标准差、分位数、环比、同比、增速、日增减、变化方向、持仓集中度、多空比、注销仓单占比、库存天数。若需展示统计信息，仅可作为右侧注释栏出现，不得作为主图指标。

2.2 临时不可追踪类全部删除

检修量、排产计划、停产通知、减产损失量、仓单交付量/注销量（非交易所标准字段）不得作为固定图表指标。其中“检修影响量”偶发且口径依赖调研，仅适合在事件研报中作为文本说明。

2.3 弱相关/重复类删除
2.1中“沪铜—伦铜—进口盈亏三角图”仅保留沪伦比价，进口盈亏为衍生结果，不得与价格并列；
2.4中LME/CME/SHFE期限结构重复，合并为全球铜期限结构曲线对比图，LME与COMEX曲线分左、右双轴展示；
2.5中“铜价本身”不属于估值利润图指标，从2.5剔除，保留TC/RC、硫酸、冶炼利润等利润链指标。
3. 重组后每个子节点保留图表（共16张）
子节点	保留图名称	核心指标	处理意见
2.1 全球铜价与跨市比价	沪铜、LME铜、COMEX铜联动图	沪铜主力/连续收盘价；LME Copper Cash/3M；COMEX Copper活跃合约	保留，作为价格主坐标系
2.1	沪伦比与COMEX-LME溢价图	SHFE/LME比价；COMEX活跃价折算美元/吨相对LME 3M溢价	保留，删除“进口盈亏”主图地位
2.1	三大交易所仓单与可交割库存图	SHFE铜仓单；LME Copper Warranted/Cancelled Stocks；COMEX Registered/Eligible Stocks	保留，库存归仓单交割压力模块
2.2 国内现货与基差	SMM 1#电解铜现货与沪铜基差图	SMM 1#电解铜现货均价；沪铜主力收盘价；SMM 1#电解铜升贴水	保留为核心图
2.2	品级升贴水结构图	平水铜升贴水；升水铜升贴水；湿法铜升贴水；SMM EQ-A铜升贴水	保留，删除“升水铜/平水铜/湿法铜价格联动图”避免重复
2.2	上海—广东区域升贴水价差图	上海电解铜现货升贴水；广东电解铜现货升贴水；上海—广东升贴水价差	保留，删除“季节性”命名
2.3 海外价格与LME期限结构	LME现金—3个月—15个月曲线图	LME Copper Cash；LME 3 Months；LME 15 Months	保留为核心图
2.3	LME 0-3升贴水与库存联动图	LME Cash-3M spread；LME Copper Warehouse Stocks；LME Cancelled Warrants	保留，库存和注销仓单作为物理紧张信号
2.3	COMEX铜价—成交量—持仓量图	COMEX Copper活跃合约收盘价；Volume；Open Interest	保留
2.3	CFTC铜持仓结构图	Non-Commercial Net Long；Commercial Net Position；Non-Reportable；COMEX价格	保留，作为外盘情绪验证
2.4 价差体系	全球铜期限结构曲线对比图	LME Cash/3M/15M；COMEX连续近月/远月；SHFE近月/远月	合并原2.4多张期限图
2.4	SHFE近远月Back强度图	SHFE近月合约收盘价；SHFE远月合约收盘价；近远月月差；近月持仓量	保留，删除“季节性”命名
2.5 估值与利润	TC/RC与硫酸副产品收益图	铜精矿现货TC；铜精矿现货RC；硫酸出厂价；单吨铜硫酸副产品收益	移至矿冶利润板块更合适，若保留仅作为“铜价利润传导”附录
2.6 持仓席位观察	沪铜前20多空头持仓与价格图	沪铜主力/指数收盘价；前20多单持仓量；前20空单持仓量；净持仓	保留，删除集中度/比率类指标

重组后每个子节点均控制在5-6张核心图，无重复、无凑数，完全贴合期货研报“价格信号”的监控需求。

4. 最终指标清单：名称、口径、频率与可得性

说明：以下“平台可搜索名”按国内主流行情/研报常用字段给出；SMM名称以SMM官网报价页和公告页为准，Mysteel名称以钢联周报标题为准；LME和CFTC英文字段按官方报告/主流终端习惯给出。若终端字段不完全一致，最终录入时以平台下拉框命中结果为准。

| 子节点 | 图名称 | 指标名 | SMM官方全称（精确） | Mysteel官方全称（精确） | LME/CME英文变量名 | 频率 | 可得性 | 单位 |
|---|---|---|---|---|---|---|
| 2.1 | 沪铜/LME/COMEX价格联动 | 沪铜主力收盘价 | 无统一口径，终端常用：沪铜主力合约收盘价 | 无统一口径 | SHFE Copper main contract close；LME Copper Cash/3M official settlement；COMEX Copper HG active close | 日度 | 公开/行情终端 | 元/吨；美元/吨；美分/磅 |
| 2.1 | 沪伦比与跨市溢价 | 沪伦比 | 无统一口径，计算项：沪铜主力/（LME铜3M×汇率×单位换算） | 无统一口径 | SHFE-LME ratio；COMEX-LME premium | 日度 | 公开但跨市口径需统一换算 | 无量纲；美元/吨 |
| 2.1 | 三大交易所仓单库存 | SHFE铜仓单 | 上期所铜期货仓单 | 上期所铜期货仓单日报 | SHFE copper warehouse warrants | 日度 | 公开 | 吨 |
| 2.1 | 三大交易所仓单库存 | LME铜注册仓单 | LME铜注册仓单，常称 on-warrant/warranted stock | LME铜注册仓单 | LME Copper warrants / warranted stock | 日度 | 官方公开/部分终端付费 | 吨 |
| 2.1 | 三大交易所仓单库存 | LME铜注销仓单 | LME铜注销仓单 | LME铜注销仓单 | Cancelled warrants | 日度 | 官方公开 | 吨 |
| 2.2 | SMM现货与基差 | SMM 1#电解铜现货均价 | SMM 1#电解铜现货均价 / SMM上海1#电解铜价格
+2
 | 无统一口径 | 无LME对应 | 日度，交易日11点左右 | 付费/部分摘要公开 | 元/吨，含税上海主流仓库自提 |
| 2.2 | SMM现货与基差 | SMM 1#电解铜升贴水 | SMM 1#电解铜升贴水
+1
 | 钢联/研报常称：SMM 1#铜升贴水 | 无LME对应 | 日度 | 付费/研报摘要公开 | 元/吨 |
| 2.2 | 基差衍生图 | 沪铜主力基差 | 无统一官方标准，市场常用：SMM 1#电解铜均价 - 沪铜主力收盘价 | 无统一口径 | SHFE copper main basis vs spot | 日度 | 公开但属自算指标 | 元/吨 |
| 2.2 | 品级升贴水 | 平水铜升贴水 | 平水铜升贴水
+3
 | Mysteel午评常用：平水铜升贴水 | 无LME对应 | 日度 | 付费/研报摘要公开 | 元/吨 |
| 2.2 | 品级升贴水 | 升水铜升贴水 | 升水铜升贴水
+2
 | Mysteel午评常用：好铜升水/升水铜升贴水 | 无LME对应 | 日度 | 付费/研报摘要公开 | 元/吨 |
| 2.2 | 品级升贴水 | 湿法铜升贴水 | 湿法铜升贴水
+3
 | Mysteel午评常用：湿法铜升贴水 | 无LME对应 | 日度 | 付费/研报摘要公开 | 元/吨 |
| 2.2 | 品级升贴水 | SMM EQ-A铜升贴水 | SMM EQ-A铜升贴水；SMM EQ-A铜现货价
 | 无统一口径 | 无LME对应 | 日度 | 付费/SMM自2026-09-01正式发布 | 元/吨 |
| 2.2 | 区域价差 | 上海电解铜升贴水 | SMM上海电解铜升贴水/上海1#电解铜升贴水
+1
 | Mysteel：上海电解铜现货升水 | 无LME对应 | 日度 | 付费/研报摘要公开 | 元/吨 |
| 2.2 | 区域价差 | 广东电解铜升贴水 | SMM广东电解铜升贴水
+1
 | Mysteel：广东电解铜现货升水 | 无LME对应 | 日度 | 付费/研报摘要公开 | 元/吨 |
| 2.2 | 现货成交验证 | 电解铜现货成交量 | 无SMM统一公开标准名，研报常称：SMM电解铜现货成交量 | Mysteel国内电解铜现货成交量
 | 无LME对应 | 日度/周度汇总 | Mysteel公开周报；SMM需数据库 | 吨 |
| 2.3 | LME期限结构 | LME铜现金结算价 | 无SMM对应，属LME官方价格 | 无Mysteel对应 | Copper Cash；LME official cash settlement | 日度 | 官方公开/商业授权 | USD/tonne |
| 2.3 | LME期限结构 | LME铜3个月官方价 | 无SMM对应 | 无Mysteel对应 | Copper 3 Months；LME official 3M settlement | 日度 | 官方公开/商业授权 | USD/tonne |
| 2.3 | LME期限结构 | LME铜15个月官方价 | 无SMM对应 | 无Mysteel对应 | Copper 15 Months | 日度 | 官方公开/商业授权 | USD/tonne |
| 2.3 | LME 0-3升贴水 | LME铜0-3升贴水 | 市场常用：LME铜现金价-3个月期货价 | 研报常用：LME 0-3升贴水 | LME Copper Cash-3M spread；部分终端：LME Copper Cash - 3 month spread
 | 日度 | 商业终端可直接取；LME官方以分项价格发布 | USD/tonne |
| 2.3 | LME库存 | LME铜总库存 | LME铜库存 | Mysteel常引：LME铜库存 | LME Copper Warehouse Stocks
+2
 | 日度 | 官方公开 | 吨/metric tonnes |
| 2.3 | LME库存结构 | LME注册仓单 | LME warrants / on-warrant stock | 无Mysteel统一字段，研报称注册仓单 | Warranted stock / on-warrant inventory
+1
 | 日度 | 官方LME仓库报告 | 吨 |
| 2.3 | LME库存结构 | LME注销仓单 | LME cancelled warrants | 研报称注销仓单 | Cancelled warrants
+3
 | 日度 | 官方LME仓库报告 | 吨 |
| 2.3 | LME注销仓单比 | 注销仓单占比 | 计算项：注销仓单/总库存 | 计算项 | Cancellation ratio / share of cancelled warrants | 日度 | 公开但属自算指标 | % |
| 2.3 | COMEX量价持仓 | COMEX铜活跃合约收盘价 | 无SMM对应 | 无Mysteel对应 | COMEX Copper HG active contract close | 日度 | 公开/行情终端 | USD/lb |
| 2.3 | COMEX量价持仓 | COMEX铜成交量 | 无SMM对应 | 无Mysteel对应 | Volume
+1
 | 日度 | CME官方/行情终端 | 手/合约 |
| 2.3 | COMEX量价持仓 | COMEX铜持仓量 | 无SMM对应 | 无Mysteel对应 | Open Interest
+1
 | 日度 | CME官方/行情终端 | 手 |
| 2.3 | CFTC持仓 | 非商业净多头持仓 | 研报常用：CFTC投机基金净多 | 无Mysteel对应 | Non-Commercial Net Long；Legacy COT fields: Long Positions / Short Positions / Net Position
 | 周度 | 官方公开，滞后约一周 | 手 |
| 2.3 | CFTC持仓 | 商业净持仓 | 研报常用：商业会员净持仓 | 无Mysteel对应 | Commercial Net Position；Commercials Long/Short
 | 周度 | 官方公开，滞后约一周 | 手 |
| 2.4 | 全球期限结构 | SHFE近月合约收盘价 | 上期所铜近月合约收盘价 | 无Mysteel对应 | SHFE Copper near-month contract close | 日度 | 公开 | 元/吨 |
| 2.4 | 全球期限结构 | SHFE远月合约收盘价 | 上期所铜远月合约收盘价 | 无Mysteel对应 | SHFE Copper far-month contract close | 日度 | 公开 | 元/吨 |
| 2.4 | 全球期限结构 | SHFE近远月月差 | 沪铜近远月月差，常用：主力近月-主力远月 | 研报常用：沪铜近远月月差 | SHFE near-far spread | 日度 | 公开但属自算指标 | 元/吨 |
| 2.4 | 全球期限结构 | COMEX近远月月差 | 无统一官方名，常用：COMEX铜近远月月差 | 无Mysteel统一名 | COMEX Copper near-far spread | 日度 | 商业终端/行情软件 | USD/lb |
| 2.4 | 全球期限结构 | LME 3个月-15个月月差 | 无SMM/Mysteel对应 | 无Mysteel对应 | LME Copper 3M-15M spread
+1
 | 日度 | 商业终端可直接取 | USD/tonne |
| 2.5 | TC/RC与硫酸收益 | 铜精矿现货TC | 铜精矿现货TC；SMM中国铜精矿现货TC | 钢联常用：中国铜精矿现货TC | 无LME对应 | 周度 | 付费/研报摘要公开 | USD/dmt |
| 2.5 | TC/RC与硫酸收益 | 铜精矿现货RC | 铜精矿现货RC | 钢联常用：中国铜精矿现货RC | 无LME对应 | 周度 | 付费/研报摘要公开 | USD/lb dry |
| 2.5 | TC/RC与硫酸收益 | 硫酸出厂价 | 常称：硫酸出厂价/硫酸价格 | Mysteel/生意社常用：硫酸出厂价 | 无LME对应 | 日度/周度 | 公开/付费数据库 | 元/吨 |
| 2.5 | TC/RC与硫酸收益 | 单吨铜硫酸副产品收益 | 研报测算项，无统一官方名 | 研报测算项，无统一官方名 | 无LME对应 | 周度/月度 | 机构测算 | 元/吨 |
| 2.6 | 持仓席位 | 沪铜前20多单持仓量 | 上期所铜主力合约前20名会员多头持仓量 | 研报常用：沪铜前20多单持仓量 | SHFE copper top 20 long positions | 日度 | 公开，收盘后 | 手 |
| 2.6 | 持仓席位 | 沪铜前20空单持仓量 | 上期所铜主力合约前20名会员空头持仓量 | 研报常用：沪铜前20空单持仓量 | SHFE copper top 20 short positions | 日度 | 公开，收盘后 | 手 |
| 2.6 | 持仓席位 | 沪铜前20净持仓 | 前20多单持仓量-前20空单持仓量 | 研报常用：沪铜前20净持仓/净空持仓
+2
 | SHFE copper top 20 net position | 日度 | 公开但属自算指标 | 手 |
| 2.6 | 持仓席位 | 沪铜持仓量 | 沪铜活跃合约持仓量 | 研报常称：SHFE铜活跃合约持仓量 | SHFE copper open interest
 | 日度 | 公开 | 手 |
| 2.6 | 持仓席位 | 沪铜成交量 | 沪铜活跃合约成交量 | 研报常称：SHFE铜活跃合约成交量
 | SHFE copper volume | 日度 | 公开 | 手 |

5. LME英文变量名特别确认

当前可确认的LME标准化字段如下：

中文	建议英文字段	说明
LME铜现金价	Copper Cash / LME Copper Cash settlement	LME官方发布Cash与3 Months官方结算价，终端也显示为“Settlement Cash / Settlement 3M”

LME铜3个月价	Copper 3 Months	LME标准3个月基准，全球铜贸易常用定价锚
+1

LME铜15个月价	Copper 15 Months	用于观察远期曲线斜率

LME 0-3升贴水	Cash-3M spread / Copper Cash - 3 month spread	部分数据商直接提供该spread，官方通常以Cash和3M两个价格发布，终端可计算

LME总库存	LME Copper Warehouse Stocks	LME官方发布仓库库存报告，常用字段为Warehouse Stocks
+2

LME注册仓单	Warranted stock / On-warrant inventory	指可用于合约交割的注册仓单
+1

LME注销仓单	Cancelled warrants	注销仓单，物理提库行为的重要观察项
+2

注销仓单占比	Cancellation ratio 或 Share of cancelled warrants	非官方统一字段名，终端常见为自定义字段
LME铜库存变化	Change in LME warehouse stocks	日报常用字段，非官方单一变量名

LME官方通常发布Cash、3M、15M、Warehouse Stocks等基础字段，0-3价差、注销仓单占比、COT净多等属于二次加工指标，建议在图表脚注标注“平台计算口径”。

6. SMM与Mysteel命名确认

SMM核心指标命名已全部核实，可直接用于图表标注：

SMM 1#电解铜现货均价：SMM官方定义为“SMM上海1#电解铜现货价格”，是可用于贸易结算参考的指示性价格，规格对应GB/T 467-2010 A级铜/Cu-CATH-1
+2
SMM 1#电解铜升贴水：SMM日报直接发布该字段，与1#电解铜现货价同日更新
+1
平水铜/升水铜/湿法铜升贴水：SMM报价页已结构化发布上述品级升贴水，是品级结构图的核心依据
+1
SMM EQ-A铜升贴水及现货价：SMM公告明确其计算公式为“1#电解铜盘面基准价 + EQ-A铜升贴水均价”，自2026年9月1日起正式发布

Mysteel核心指标命名已核实：

中国16港进口铜精矿当周库存：Mysteel周报标准标题，与“中国7个主流港口进口铜精矿当周库存”为原口径/新口径并列披露
+1
国内市场电解铜现货库存：Mysteel标准标题，包含上海、广东、江苏等分区域库存
+1
国内电解铜现货成交量：Mysteel可披露样本企业电解铜现货成交量，适合替代“需求强弱”的弱口径代理指标
7. 图表设计审稿意见

建议所有图统一采用“单核心信号+最多1个验证指标”的组合，避免信息过载：

图类型	推荐组合	禁止组合
LME期限结构	Cash、3M、15M三线；右侧标注0-3价差	不要叠加库存、汇率、TC
国内基差	SMM 1#电解铜均价 + 沪铜主力 + 1#升贴水	不要叠加平水铜、升水铜、湿法铜全部品级价格
品级升贴水	平水铜、升水铜、湿法铜、EQ-A四条升贴水线	不要叠加1#电解铜均价，避免量纲混杂
库存仓单	SHFE仓单 + LME库存；可小倍数叠加注销仓单	不要叠加社会库存和保税区库存，口径冲突
CFTC	Non-Commercial Net Long + Commercial Net Position + COMEX价格	不要叠加“净多占比”“分位数”等统计派生
持仓席位	前20多单、前20空单、净持仓、价格四图联动	不要叠加集中度、多空比、换月迁移季节线

单图信息密度建议：

价格/升贴水类：最多4条线，超过则拆分为子图；
库存类：总量+结构，避免同时放SHFE、LME、COMEX、SMM、保税区、社会库存6类库存；
期限结构：LME用官方Cash/3M/15M，SHFE用连续近月/远月，COMEX用连续近月/远月，三者分面展示比强行叠加更专业。
8. 风险与口径边界
LME官方变量边界：LME官方核心字段为Cash、3M、15M、Warehouse Stocks、Warranted/Cancelled Split，0-3价差、注销仓单占比为二次加工指标，需在图注中说明计算口径
+2
SMM/Mysteel商业数据边界：SMM现货价、升贴水、EQ-A升贴水，以及Mysteel现货库存、铜精矿港口库存为商业数据库口径，公开研报常引用摘要值，历史长序列通常需要付费权限
+4
COMEX/CFTC边界：COMEX价格和量仓为交易所行情；CFTC持仓为周度报告，字段为Legacy COT中的Commercials、Non-Commercials、Non-Reportables的Long/Short/Net Position，滞后披露且不构成交易信号
+1
跨市换算边界：沪伦比和进口盈亏依赖汇率、税率、运费、保税区和港口交割地假设，建议仅展示“沪伦比”，进口盈亏作为附录，不作为主信号。
9. 最终执行建议

建议图表数据库按三层结构维护，避免后续重复增图导致混乱：

价格层：沪铜、LME Cash/3M/15M、COMEX HG、沪伦比、0-3、3-15；
现货层：SMM 1#均价、SMM升贴水、平水/升水/湿法/EQ-A升贴水、上海/广东升贴水、Mysteel现货成交量；
交割与资金层：SHFE仓单、LME warrants/cancelled warrants、LME stocks、COMEX registered/eligible、CFTC Non-Commercial Net Long、SHFE前20净持仓。

TC/RC、硫酸、冶炼利润、铜精矿港口库存、电解铜产量、再生铜杆开工率、废铜供给等指标应整体迁移至「铜·矿冶利润与供给」板块，不要在“价格信号”中重复出现。

要不要我继续把这套重组后的16张图整理成可直接落图的“图表目录+字段映射+Excel字段命名规范”，包含中文图名、英文变量、频率、更新时点、口径责任人？

77个溯源
大势研判
走势预测
买卖点研判
股票诊断
行业分析
选股票
智能图说
AI复盘