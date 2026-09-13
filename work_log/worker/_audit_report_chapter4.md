# 章节4：指标匹配全链路样本 — 审计报告

> 导出时间：2026-09-02
> 工作目录：D:\DSH_WORK\周报

---

## 4.1 同花顺Agent返回原始响应脚本（原样，3组）

---

### 组1：成功案例（匹配成功）

**案例：CU·库存 4.1 三大交易所库存 — 三交易所均命中**

---

#### 1.1 同花顺返回原文（CU_库存_iwencai_round1.md）

```
# 同花顺回复 · 铜·库存 纠正(第一轮)
# 时间: 2026-09-02 06:42:31

---

你是CU基本面分析师，帮我纠正以下指标映射。

以下是CU·库存板块的旧指标名称和对应的 zhiji_id，其中部分 zhiji_id 是错误的（如 ID01659225 矿产粗铜产量 被错误分配给了多个不相关指标）。

请帮我：
1. 识别哪些 zhiji_id 是明显错误的（品种不对、指标类型不对）
2. 对每个正确的指标，给出 SMM 和 Mysteel 平台的精确指标全称（可用于知几搜索的关键词）
3. 对于没有 SMM/Mysteel 数据的指标，说明应该用哪个数据源

指标清单：
- 4.4|LME Copper Official Price / LME Copper Cash Settle
  旧ID: ID01659225 | 旧名: 矿产粗铜：产量：中国（月）
- 4.4|LME Copper Warehouse Stocks / Open Stock / Cancell
  旧ID: ID01659225 | 旧名: 矿产粗铜：产量：中国（月）
- 4.4|LME Warrants / Open Warrants / Cancelled Warrants
  旧ID: ID01659225 | 旧名: 矿产粗铜：产量：中国（月）
- 4.4|LME-approved warehouses
  旧ID: ID01659225 | 旧名: 矿产粗铜：产量：中国（月）
- 4.4|Cancelled warrants
  旧ID: ID01659225 | 旧名: 矿产粗铜：产量：中国（月）
- 4.4|Warehouse wait times / Queue data
  旧ID: ID01659225 | 旧名: 矿产粗铜：产量：中国（月）
- 4.1|LME铜库存、上期所铜库存、COMEX铜库存
  旧ID: ID01552124 | 旧名: USGS：精铜：库存：美国（年）
- 4.1|各LME仓库/地点铜库存
  旧ID: ID01552124 | 旧名: USGS：精铜：库存：美国（年）
- 4.2|SHFE铜仓单、沪铜主力价格、现货升贴水
  旧ID: ID00302616 | 旧名: 电解铜：平水铜：现货升贴水：山东（日）
- 4.2|电解铜仓单、国际铜仓单
  旧ID: ID00299393 | 旧名: ICSG：电解铜：产量：全球（月）
- 4.2|仓单注册量、仓单注销量、仓单总量
  旧ID: ID01535718 | 旧名: 计价铜：销量：BHP：Spence（季）
- 4.2|上海、江苏、广东、浙江等仓单数量
  旧ID: FU00048061 | 旧名: CZCE：硅锰：仓单数量：江苏奔牛库（日）
- 4.3|SMM中国主流地区电解铜社会库存
  旧ID: ID00183769 | 旧名: 螺纹钢：35个城市：社会库存：东北地区（周）
- 4.3|Mysteel国内市场电解铜现货库存
  旧ID: ID01528478 | 旧名: 精炼镍：现货库存：国内：全口径：27家样本仓库（周）
- 4.3|上海库存、广东库存、江苏库存
  旧ID: ID01030899 | 旧名: 棕榈油：库存：广东（周）
- 4.3|上海、广东、江苏、浙江、江西等区域库存
  旧ID: ID01552124 | 旧名: USGS：精铜：库存：美国（年）
- 4.3|社会库存、电解铜现货成交量
  旧ID: ID01168763 | 旧名: 电解铜：现货库存：中国（日）
- 4.3|社会库存、SHFE铜仓单
  旧ID: ID00183781 | 旧名: 螺纹钢：35个城市：社会库存：中国（周）
- 4.4|上海保税区铜库存、广东保税区铜库存
  旧ID: ID01030219 | 旧名: 锌锭：库存：上海保税区（周）
- 4.4|保税区库存、沪伦进口盈亏或COMEX-LME价差
  旧ID: ID01510878 | 旧名: 电解钴：库存：保税区（周）
- 4.4|SMM/机构统计的"铜社会总库存含保税区"
  旧ID: ID01200757 | 旧名: 电解铜：现货库存：中国：保税区（日）
- 4.4|上海、广东等保税区库存
  旧ID: ID01510878 | 旧名: 电解钴：库存：保税区（周）
- 4.4|在途海运铜库存估算
  旧ID: ID01552124 | 旧名: USGS：精铜：库存：美国（年）
- 4.4|保税区库存、进口利润、精废价差
  旧ID: ID01552124 | 旧名: USGS：精铜：库存：美国（年）
- 4.5|精铜杆企业原料库存
  旧ID: ID01225147 | 旧名: 甲醇：原料：下游厂家：库存：中国（周）
- 4.5|精铜杆企业成品库存
  旧ID: ID01723483 | 旧名: 铝板带箔：130家样本企业：成品库存：中国（周）
- 4.5|再生铜杆企业原料库存
  旧ID: ID01225147 | 旧名: 甲醇：原料：下游厂家：库存：中国（周）
- 4.5|黄铜棒企业原料库存
  旧ID: ID01225147 | 旧名: 甲醇：原料：下游厂家：库存：中国（周）
- 4.5|铜线缆企业原料库存、漆包线企业原料库存
  旧ID: RE00009883 | 旧名: 塑编：原料：库存：中国（周）
- 4.5|精铜杆、再生铜杆、线缆、铜管等成品库存
  旧ID: ID01167306 | 旧名: 锌：冶炼厂：成品库存：中国（周）
- 4.5|原因
  旧ID: ID01659225 | 旧名: 矿产粗铜：产量：中国（月）

请用表格格式回复，列为：图名称 | 指标是否正确 | SMM精确名 | Mysteel精确名 | 备注
  问财 正在思考
快速推理中 · 2 条资料
已联网搜索网页
SMM 电解铜 社会库存 指标名称
Mysteel 电解铜 现货库存 指标名称
LME铜 库存 仓单 指标名称 SMM Mysteel
上海保税区 铜库存 SMM Mysteel 指标
精铜杆 企业原料库存 成品库存 指标名称
SHFE铜 仓单 注册量 注销量 指标名称

现有信息已经足够判断大部分旧ID明显错配，但部分下游库存和LME仓单指标还需要再确认标准表述，尤其要区分SMM周度调研、Mysteel现货库存和交易所仓单数据，避免把"库存""仓单""注册量""注销量"混为一谈。

已联网搜索网页
SMM 精铜杆 原料库存 成品库存 指标名称
SMM LME铜 注册仓单 注销仓单 指标名称
Mysteel 电解铜 仓单 注册量 注销量 指标名称
SMM 再生铜杆 原料库存 黄铜棒 原料库存
SMM 铜线缆 漆包线 原料库存 指标名称

现在可以直接给表格了。我要把错误ID、正确指标名、SMM/Mysteel可搜索关键词和备注一次说清，同时明确哪些指标没有对应平台数据、应改用交易所或机构口径，方便用户后续直接修正映射。

以下是纠正后的指标映射表。所有旧ID为 ID01659225（矿产粗铜：产量：中国（月））的条目均为明显错误——该ID属于矿产粗铜产量指标，与LME铜价、LME库存、LME仓单等铜库存板块指标完全无关。

图名称	指标是否正确	SMM精确名	Mysteel精确名	备注
LME Copper Official Price / LME Copper Cash Settle	❌ 错误	LME铜官方价格 / LME铜现金结算价	同左	旧ID ID01659225 为矿产粗铜产量，品种完全不对。LME铜价属LME官方数据，SMM/Mysteel不直接生产该指标，应使用LME官网或同花顺期货通数据
LME铜库存 / Open Stock / Cancelled	❌ 错误	LME铜库存（注册仓单+注销仓单）	同左	旧ID ID01659225 错误。LME库存属LME官方数据，SMM每日转载LME铜库存变动，Mysteel亦转载。应使用LME官网或同花顺期货通
LME Warrants / Open Warrants / Cancelled Warrants	❌ 错误	LME铜注册仓单 / LME铜注销仓单	同左	旧ID ID01659225 错误。注册仓单=可交割货源，注销仓单=已提货但仍在系统内的铜。SMM每日报道LME铜仓单数据

LME-approved warehouses	❌ 错误	LME认证仓库铜库存（分仓库）	同左	旧ID ID01659225 错误。LME认证仓库分伦敦、阿姆斯特丹、纽约等，SMM/Mysteel不直接生产分仓库数据，应使用LME官网
Cancelled warrants	❌ 错误	LME铜注销仓单	同左	旧ID ID01659225 错误。注销仓单占比是LME挤仓风险核心指标，SMM每日报道

Warehouse wait times / Queue data	❌ 错误	LME铜仓库排队时间	同左	旧ID ID01659225 错误。LME排队时间属LME官方数据，SMM/Mysteel不直接生产，应使用LME官网
LME铜库存、上期所铜库存、COMEX铜库存	❌ 错误	LME铜库存 / SHFE铜库存 / COMEX铜库存	同左	旧ID ID01552124（USGS：精铜：库存：美国（年））错误，USGS为美国地质调查局，不统计铜库存。SHFE铜库存应使用上期所官网仓单数据，COMEX铜库存使用LME或CME官网

各LME仓库/地点铜库存	❌ 错误	LME铜库存（分仓库：伦敦/阿姆斯特丹/纽约等）	同左	旧ID ID01552124 错误。分仓库数据应使用LME官网，SMM每日转载LME总库存及分仓库变动

SHFE铜仓单、沪铜主力价格、现货升贴水	❌ 错误	SHFE铜期货		
大势研判
走势预测
买卖点研判
股票诊断
行业分析
选股票
智能图说
AI复盘
热点雷达
投资目标
账户管理
反馈

快速推理
```

#### 1.2 Prompt全文（CU_库存_prompt.txt）

```
你是铜基本面分析师，帮我纠正以下指标映射。
以下是CU·库存(4.1-4.5)板块的旧指标名称和对应的 zhiji_id，其中部分 zhiji_id 是错误的。
请帮我：
1. 识别哪些 zhiji_id 是明显错误的（品种不对、指标类型不对）
2. 对每个正确的指标，给出 SMM 和 Mysteel 平台的精确指标全称（可用于知几搜索的关键词）
3. 对于没有 SMM/Mysteel 数据的指标，说明应该用哪个数据源
请用表格格式回复，列为：图名称 | 指标是否正确 | SMM精确名 | Mysteel精确名 | 备注
```

#### 1.3 zhiji_search.json（CU_库存_zhiji_search.json 关键片段）

```json
{
  "4.1|LME铜库存、上期所铜库存、COMEX铜库存": {
    "sub": "4.1",
    "grade": "A",
    "hit_ids": ["ID00188286", "FU00015497", "FU00015498", "FU00057200"],
    "hit_names": ["COMEX：铜：期货库存（日）", "LME：铜：注册仓单（日）", "LME：铜：注销仓单（日）", "SHFE：铜(BC)：期货库存（周）"],
    "note": "三交易所均命中"
  },
  "4.1|各LME仓库/地点铜库存": {
    "sub": "4.1",
    "grade": "B",
    "hit_ids": ["FU00094570", "FU00103253", "FU00103367"],
    "hit_names": ["LME：铜：期货库存：香港（日）", "LME：铜：非仓单库存：欧洲（日）", "LME：铜：非仓单库存：北美（日）"],
    "note": "有LME按地点数据但不完整"
  },
  "4.2|SHFE铜仓单、沪铜主力价格、现货升贴水": {
    "sub": "4.2",
    "grade": "A",
    "hit_ids": ["FU00057200", "FU00015764", "ID00302616"],
    "hit_names": ["SHFE：铜(BC)：期货库存（周）", "SHFE：电解铜：主力合约：收盘价（日）", "电解铜：平水铜：现货升贴水：山东（日）"],
    "note": "三要素全命中"
  },
  "4.2|SMM 1#电解铜升贴水": {
    "sub": "4.2",
    "grade": "A",
    "hit_ids": ["ID01677008"],
    "hit_names": ["电解铜：1#：升贴水：上海（日）"],
    "note": "精确命中"
  },
  "4.3|SMM中国主流地区电解铜社会库存": {
    "sub": "4.3",
    "grade": "A",
    "hit_ids": ["ID01168763", "a10015034"],
    "hit_names": ["电解铜：现货库存：中国（日）", "SMM：电解铜社会库存：上海（周度）"],
    "note": "Mysteel中国总计 + SMM上海"
  },
  "4.3|上海库存、广东库存、江苏库存": {
    "sub": "4.3",
    "grade": "A",
    "hit_ids": ["ID00188319", "ID00188316", "ID00188321", "ID00188317"],
    "hit_names": ["电解铜：现货库存：上海（日）", "广东（日）", "江苏（日）", "浙江（日）"],
    "note": "分地区全命中"
  },
  "4.4|保税区库存、沪伦进口盈亏或COMEX-LME价差": {
    "sub": "4.4",
    "grade": "A",
    "hit_ids": ["ID01030232", "ID01030231", "ID01038030"],
    "hit_names": ["铜进口盈亏（日）", "铜进口盈亏（月）", "铜进口利润均值（日）"],
    "note": "铜进口盈亏数据完整"
  },
  "4.4|在途海运铜库存估算": {
    "sub": "4.4",
    "grade": "C",
    "hit_ids": [],
    "hit_names": [],
    "note": "知几无铜海运在途库存数据"
  }
}
```

#### 1.4 Correction文件（CU_库存_correct_20260902.md 关键节选）

```
命中率: 14/23 = 60.9%

### 4.1 三大交易所库存（2 个指标）

| 1 | LME铜库存、上期所铜库存、COMEX铜库存 | LME铜库存 / SHFE铜库存 / COMEX铜库存 | ID00188286 / FU00015497 / FU00015498 / FU00057200 | COMEX铜期货库存(日) / LME铜注册仓单(日) / LME铜注销仓单(日) / SHFE铜(BC)期货库存(周) | ✅A | 三交易所均命中 |
| 2 | 各LME仓库/地点铜库存 | LME各仓库铜库存 | FU00094570 / FU00103253 / FU00103367 | LME铜期货库存：香港(日) / LME铜非仓单库存：欧洲(日) / LME铜非仓单库存：北美(日) | ⚠️B | 有LME按地点数据但不完整 |

### 4.3 社会库存（5 个指标）

| 8 | SMM中国主流地区电解铜社会库存 | SMM中国主流地区电解铜社会库存 | ID01168763 / a10015034 | 电解铜现货库存：中国(日) / SMM：电解铜社会库存：上海(周度) | ✅A | 精确命中 |
| 9 | Mysteel国内市场电解铜现货库存 | Mysteel国内市场电解铜现货库存 | ID01168763 | 电解铜：现货库存：中国（日） | ✅A | 精确命中 |
| 10 | 上海库存、广东库存、江苏库存 | SMM电解铜社会库存 上海/广东/江苏 | ID00188319 / ID00188316 / ID00188321 / ID00188317 | 上海(日) / 广东(日) / 江苏(日) / 浙江(日) | ✅A | 分地区全命中 |

### 4.4 保税区库存与国际（5 个指标）

| 14 | 保税区库存、沪伦进口盈亏或COMEX-LME价差 | 铜进口盈亏 / COMEX-LME铜价差 | ID01030232 / ID01030231 / ID01038030 | 铜进口盈亏(日) / 铜进口盈亏(月) / 铜进口利润均值(日) | ✅A | 精确命中 |
| 17 | 保税区库存、进口利润、精废价差 | 保税区铜库存 + 进口利润 + 精废价差 | ID01200757 / ID01030232 / ID01001703 | 电解铜保税区库存(日) + 铜进口盈亏(日) + 精废铜价差广东(日) | ✅A | 三要素全命中 |
```

**案例判定依据**：
- 同花顺正确识别了旧ID ID01659225（矿产粗铜产量）和 ID01552124（USGS精铜库存）为明显错配
- 同花顺给出了正确的指标全称和搜索关键词
- 知几验证后，4.1 三交易所均命中A级，4.3分地区全命中A级
- 最终 CU_库存 23个指标中14个A级、3个B级、6个C级，命中率60.9%

---

### 组2：匹配错误案例

**案例：AL·库存 上期所沪铝期货仓单 — 知几无数据（C级）**

---

#### 2.1 同花顺返回原文（AL_库存_iwencai_r1.md）

```
# 同花顺回复 · AL·库存
# 2026-09-02 06:50:58

---

你是AL基本面分析师，纠正以下指标映射。

以下是AL·库存板块的旧指标名称和对应的 zhiji_id，其中部分 zhiji_id 是错误的。

请帮我：
1. 识别哪些 zhiji_id 是明显错误的（品种不对、指标类型不对）
2. 对每个正确的指标，给出 SMM 和 Mysteel 平台的精确指标全称（用于知几搜索的关键词）
3. 对于没有 SMM/Mysteel 数据的指标，说明应该用哪个数据源

指标清单：
- 4.1|上期所沪铝期货仓单
  旧ID: FU00016906 | 旧名: CZCE：硅锰：仓单数量（日）
- 4.1|LME Aluminium Total Inventories / Open Stocks
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.1|Registered Warrants / Cancelled Warrants
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.1|上期所沪铝期货仓单；LME铝总库存
  旧ID: ID00185743 | 旧名: 镍生铁：库存合计：中国：实物量（月）
- 4.1|上期所沪铝期货仓单；沪铝主力价格
  旧ID: ID00188139 | 旧名: 氧化铝：汇总价格：中国（日）
- 4.2|中国主要地区/市场电解铝社会库存
  旧ID: ID00188307 | 旧名: 电解铝：现货库存：中国（日）
- 4.2|SMM周度铝锭库存 / 国内主流消费地电解铝锭库存
  旧ID: ID01528478 | 旧名: 精炼镍：现货库存：国内：全口径：27家样本仓库（周）
- 4.2|无锡、佛山、巩义、上海、重庆、天津等区域库存
  旧ID: ID01030927 | 旧名: 棕榈油：库存：天津（周）
- 4.2|Mysteel/SMM社会库存；沪铝主力价格
  旧ID: ID01001944 | 旧名: 废铝：社会库存：中国（月）
- 4.2|Mysteel社会库存；上期所沪铝期货仓单
  旧ID: ID00184048 | 旧名: 热轧板卷：33个城市：社会库存：中国（周）
- 4.2|电解铝社会库存；铝棒社会库存
  旧ID: ID00184048 | 旧名: 热轧板卷：33个城市：社会库存：中国（周）
- 4.3|中国电解铝企业厂内铝锭库存
  旧ID: ID01179784 | 旧名: 焦炭：247家钢铁企业：库存：东北地区（周）
- 4.3|中国主要地区电解铝社会库存；电解铝企业厂内铝锭库存
  旧ID: ID00184048 | 旧名: 热轧板卷：33个城市：社会库存：中国（周）
- 4.3|电解铝社会库存、电解铝厂内库存、电解铝出库量
  旧ID: ID01002072 | 旧名: 电解铝：厂内库存：中国（日）
- 4.3|国内铝棒社会库存 / 主要市场铝棒库存
  旧ID: ID01528478 | 旧名: 精炼镍：现货库存：国内：全口径：27家样本仓库（周）
- 4.3|SMM国内铝水比例；铝锭社会库存
  旧ID: ID01528478 | 旧名: 精炼镍：现货库存：国内：全口径：27家样本仓库（周）
- 4.3|铝棒社会库存；铝棒加工费
  旧ID: ID00259465 | 旧名: 铝棒：6063：Φ120：加工费：佛山（日）
- 4.3|建议图数量
  旧ID: ID00402646 | 旧名: 压榨厂：豆粕：111家样本企业：未执行合同：数量：中国（周）
- 4.3|5张
  旧ID: ID02400942 | 旧名: 08铝压块：尺寸≤350mm*350mm*600mm：市场最低价：张家口（日）
- 4.3|6张
  旧ID: ID02400942 | 旧名: 08铝压块：尺寸≤350mm*350mm*600mm：市场最低价：张家口（日）
- 4.3|强化当前库存偏紧判断
  旧ID: ID01721697 | 旧名: 氧化铝：库存：中国（周）
- 4.3|连续去库且绝对值回落至80万吨下方
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.3|仓单持续下降，价格同步走强
  旧ID: ID00188139 | 旧名: 氧化铝：汇总价格：中国（日）
- 4.3|总库存维持25万吨以下，注销仓单上升
  旧ID: FU00014316 | 旧名: LME：铝：注销仓单（日）
- 4.3|厂内库存低位，出库量上升
  旧ID: ID01001760 | 旧名: 电解铝：出库量：中国（日）
- 4.3|铝棒库存低位且加工费坚挺
  旧ID: ID00259465 | 旧名: 铝棒：6063：Φ120：加工费：佛山（日）
- 4.3|明确披露"货权不清库存"规模下降
  旧ID: ID01721697 | 旧名: 氧化铝：库存：中国（周）
- 4.1|最终保留图
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.2|最终保留图
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）

请用表格格式回复，列为：图名称 | 是否正确 | SMM精确名 | Mysteel精确名 | 备注
  问财 正在思考
快速推理中 · 1 条资料

用户是在做指标映射纠错，不是要行情判断。我先按"品种是否对应、指标类型是否合理、平台口径是否匹配"三条线筛查，再补足SMM和Mysteel的精确名称；对明显错配的条目，需要同时确认原旧ID实际对应什么，避免把错误ID直接当成正确映射。

已联网搜索网页
SMM 电解铝社会库存 周度铝锭库存 指标名称
Mysteel 电解铝社会库存 厂内库存 出库量 指标名称
上期所 沪铝期货仓单 指标名称 SMM Mysteel
LME 铝 总库存 注销仓单 注册仓单 指标名称
SMM 铝棒社会库存 铝棒加工费 指标名称
Mysteel 铝棒库存 加工费 指标名称
SMM 电解铝企业厂内铝锭库存 指标名称
Mysteel 电解铝厂内库存 出库量 指标名称

根据搜索结果，我已对全部指标进行了逐一核查。以下是纠正结果：

图名称	是否正确	SMM精确名	Mysteel精确名	备注
上期所沪铝期货仓单	❌ 错误	上期所沪铝期货仓单	上期所铝期货仓单	旧ID对应硅锰仓单，品种完全不对
+1

LME Aluminium Total Inventories / Open Stocks	❌ 错误	LME铝总库存	LME铝总库存	旧ID对应USGS粗铝进口，品种和平台均不对
+1

Registered Warrants / Cancelled Warrants	❌ 错误	LME铝注册仓单 / LME铝注销仓单	LME铝注册仓单 / LME铝注销仓单	旧ID同上行，品种和平台均不对
+1

上期所沪铝期货仓单；LME铝总库存	❌ 错误	上期所沪铝期货仓单 / LME铝总库存	上期所铝期货仓单 / LME铝总库存	旧ID对应镍生铁库存，品种完全不对

上期所沪铝期货仓单；沪铝主力价格	❌ 错误	上期所沪铝期货仓单 / 沪铝主力合约价格	上期所铝期货仓单 / 沪铝主力价格	旧ID对应氧化铝汇总价格，品种不对

中国主要地区/市场电解铝社会库存	✅ 正确	国内主流消费地电解铝锭库存（周）	中国主要地区电解铝社会库存（日）	旧ID已正确，SMM为周度、Mysteel为日度
+1

SMM周度铝锭库存 / 国内主流消费地电解铝锭库存	❌ 错误	国内主流消费地电解铝锭库存（周）	—	旧ID对应精炼镍现货库存，品种完全不对
+1

无锡、佛山、巩义、上海、重庆、天津等区域库存	❌ 错误	国内主流消费地电解铝锭库存（分区域）	中国主要地区电解铝社会库存（分区域）	旧ID对应棕榈油库存，品种完全不对

Mysteel/SMM社会库存；沪铝主力价格	❌ 错误	国内主流消费地电解铝锭库存 / 沪铝主力合约价格	中国主要地区电解铝社会库存 / 沪铝主力价格	旧ID对应废铝社会库存，品种不对

Mysteel社会库存；上期所沪铝期货仓单	❌ 错误	国内主流消费地电解铝锭库存 / 上期所沪铝期货仓单	中国主要地区电解铝社会库存 / 上期所铝期货仓单	旧ID对应热轧板卷社会库存，品种完全不对
+1

电解铝社会库存；铝棒社会库存	❌ 错误	国内主流消费地电解铝锭库存 / 国内铝棒社会库存	中国主要地区电解铝社会库存 / 铝棒社会库存	旧ID对应热轧板卷社会库存，品种不对
+1

中国电解铝企业厂内铝锭库存	❌ 错误	电解铝企业厂内铝锭库存（周）	中国电解铝企业厂内铝锭库存（周）	旧ID对应焦炭库存，品种完全不对
+1

中国主要地区电解铝社会库存；电解铝企业厂内铝锭库存	❌ 错误	国内主流消费地电解铝锭库存 / 电解铝企业厂内铝锭库存（周）	中国主要地区电解铝社会库存 / 中国电解铝企业厂内铝锭库存（周）	旧ID对应热轧板卷社会库存，品种不对
+1

电解铝社会库存、电解铝厂内库存、电解铝出库量	❌ 错误	国内主流消费地电解铝锭库存 / 电解铝企业厂内铝锭库存 / 电解铝出库量	中国主要地区电解铝社会库存 / 中国电解铝企业厂内铝锭库存 / 电解铝出库量	旧ID对应电解铝厂内库存（日），缺少社会库存和出库量
+1

国内铝棒社会库存 / 主要市场铝棒库存	❌ 错误	国内铝棒社会库存（周）	铝棒社会库存（周）	旧ID对应精炼镍现货库存，品种完全不对
+1

SMM国内铝水比例；铝锭社会库存	❌ 错误	国内铝水比例 / 国内主流消费地电解铝锭库存（周）	铝水直供比例 / 中国主要地区电解铝社会库存	旧ID对应精炼镍现货库存，品种完全不对
+1

铝棒社会库存；铝棒加工费	❌ 错误	国内铝棒社会库存（周） / 铝棒加工费（佛山）	铝棒社会库存（周） / 铝棒加工费（佛山）	旧ID对应铝棒加工费（日），缺少社会库存
+1

建议图数量	❌ 错误	—	—	旧ID对应豆粕未执行合同数量，与铝无关，无对应指标

5张	❌ 错误	—	—	旧ID对应08铝压块最低价，与库存无关，无对应指标

6张	❌ 错误	—	—	同上，旧ID对应08铝压块最低价，与库存无关

强化当前库存偏紧判断	❌ 错误	—	—	旧ID对应氧化铝库存，品种不对，此为判断结论非指标

连续去库且绝对值回落至80万吨下方	❌ 错误	国内主流消费地电解铝锭库存（周）	中国主要地区电解铝社会库存（日）	旧ID对应USGS粗铝进口，品种和平台均不对
+1

仓单持续下降，价格同步走强	❌ 错误	上期所沪铝期货仓单 / 沪铝主力合约价格	上期所铝期货仓单 / 沪铝主力价格	旧ID对应氧化铝汇总价格，品种不对

总库存维持25万吨以下，注销仓单上升	❌ 错误	LME铝总库存 / LME铝注销仓单	LME铝总库存 / LME铝注销仓单	旧ID对应LME铝注销仓单（日），缺少总库存
+1

厂内库存低位，出库量上升	❌ 错误	电解铝企业厂内铝锭库存（周） / 电解铝出库量	中国电解铝企业厂内铝锭库存（周） / 电解铝出库量	旧ID对应电解铝出库量（日），缺少厂内库存
+1

铝棒库存低位且加工费坚挺	❌ 错误	国内铝棒社会库存（周） / 铝棒加工费（佛山）	铝棒社会库存（周） / 铝棒加工费（佛山）	旧ID对应铝棒加工费（日），缺少社会库存
+1

明确披露"货权不清库存"规模下降	❌ 错误	—	中国主要地区电解铝社会库存（含货权不清库存）	旧ID对应氧化铝库存，品种不对；Mysteel社库数据中包含约10.7万吨货权不清晰库存
+1

最终保留图	❌ 错误	—	—	旧ID对应USGS粗铝进口，品种和平台均不对，无对应指标

最终保留图	❌ 错误	—	—	同上
核心纠正总结

错误类型分布：

错误类型	数量	说明
品种完全不对	18项	旧ID指向硅锰、镍、棕榈油、焦炭、热轧板卷、豆粕、08铝压块、USGS粗铝进口、氧化铝等，与铝库存无关
品种部分不对	4项	旧ID指向氧化铝、废铝、电解铝出库量等，与铝库存相关但品种或口径不匹配
指标类型不对	3项	"建议图数量""5张""6张"为图示数量而非指标，旧ID对应无关数据
平台/口径不匹配	3项	旧ID为日度而目标为周度，或缺少部分指标

正确指标（旧ID已正确）： 仅"中国主要地区/市场电解铝社会库存"一项旧ID正确
+1

无SMM/Mysteel数据的指标： "建议图数量""5张""6张"为图示数量说明，非可查询指标；"最终保留图"为决策结论，非指标。"货权不清库存"为Mysteel社库数据中的子项（约10.7万吨），无独立指标，需用Mysteel中国主要地区电解铝社会库存数据
+1

建议替换方案： 对于品种完全错误的18项，应重新分配至对应铝库存指标的zhiji_id；对于"建议图数量""5张""6张"等图示说明，建议删除或替换为实际指标。

需要我进一步查询这些铝库存指标在知几平台上的正确zhiji_id吗？

37个溯源
大势研判
走势预测
买卖点研判
股票诊断
行业分析
选股票
智能图说
AI复盘
热点雷达
投资目标
账户管理
反馈

快速推理
```

#### 2.2 Prompt全文（AL_库存_prompt.txt）

```
你是铝基本面分析师，帮我纠正以下指标映射。
以下是AL·库存(4.1-4.5)板块的旧指标名称和对应的 zhiji_id，其中部分 zhiji_id 是错误的。
请帮我：
1. 识别哪些 zhiji_id 是明显错误的（品种不对、指标类型不对）
2. 对每个正确的指标，给出 SMM 和 Mysteel 平台的精确指标全称（用于知几搜索的关键词）
3. 对于没有 SMM/Mysteel 数据的指标，说明应该用哪个数据源
请用表格格式回复，列为：图名称 | 是否正确 | SMM精确名 | Mysteel精确名 | 备注
```

#### 2.3 zhiji_search.json（AL_库存_zhiji_search.json 关键片段）

```json
{
  "4.|上期所沪铝期货仓单时序": {
    "subnode": "4.",
    "chart": "上期所沪铝期货仓单时序",
    "names": ["上期所沪铝期货仓单", "上海期货交易所铝期货仓单；同花顺iFinD常见名：期货仓单", "上期所铝仓单；上海期货交易所铝仓单", "SHFE Aluminium Warehouse Receipts / OHALW", "公开/资讯免费；历史序列通常需数据终端", "吨，研报常换算万吨"],
    "grade": "C",
    "hit_id": null,
    "hit_name": "知几无数据",
    "hit_path": "",
    "hit_source": null,
    "searched_terms": ["上期所沪铝期货仓单", "上海期货交易所铝期货仓单；同花顺iFinD常见名：期货仓单", "上期所铝仓单；上海期货交易所铝仓单", "铝 SHFE Aluminium Warehouse Receipts / OHALW"],
    "_fix_note": "hit_name不含AL品种词"
  },
  "4.|LME铝总库存时序": {
    "subnode": "4.",
    "chart": "LME铝总库存时序",
    "names": ["LME铝总库存", "LME铝库存；LME铝总库存", "LME铝库存；伦铝库存", "LME Aluminium Total Inventories；Stock Summary中 Aluminium opening/closing stocks", "日频，部分历史月报/季报", "LME官方仓储库存报告；完整明细通常付费/授权", "吨，常用万吨展示"],
    "grade": "A",
    "hit_id": "ID01721697",
    "hit_name": "氧化铝：库存：中国（周）",
    "hit_path": "行业数据 有色金属 有色金属数据库 库存 社会库存 铝金属",
    "hit_source": "mysteel",
    "searched_terms": ["LME铝总库存", "LME铝库存；LME铝总库存", "LME铝库存；伦铝库存", "LME Aluminium Total Inventories；Stock Summary中 Aluminium opening/closing stocks"]
  }
}
```

#### 2.4 Correction文件（AL_库存_correct_20260902.md）

```
# AL·库存 指标纠正对照表（同花顺审计+知几验证）

> 日期: 2026-09-02 | 品种: AL | 板块: 库存
> 指标数: 11 | ✅A=8 | ⚠️B=0 | ❌C=3 | 命中率=72.7%

| # | 子节点 | 图名称 | 原始指标名 | 知几ID | 知几名称 | 来源 | 级别 | 备注 |
|---|--------|--------|-----------|--------|---------|------|------|------|
| 1 | 4. | LME注册仓单与注销仓单 | LME注册仓单；LME注销仓单; LME铝注册仓单；LME铝注销仓单 | FU00014316 | LME：铝：注销仓单（日） | mysteel | ✅A |  |
| 2 | 4. | LME铝总库存时序 | LME铝总库存; LME铝库存；LME铝总库存 | ID01721697 | 氧化铝：库存：中国（周） | mysteel | ✅A |  |
| 3 | 4. | Mysteel中国主要地区电解铝社会 | 中国主要地区电解铝社会库存; 国内主流消费地电解铝锭库存；SMM周度铝锭库存 | — | 无数据 | — | ❌C | 知几无数据 |
| 4 | 4. | Mysteel中国电解铝企业厂内铝锭 | 中国电解铝企业厂内铝锭库存; 电解铝企业厂内铝锭库存；厂内库存 | ID01002072 | 电解铝：厂内库存：中国（日） | mysteel | ✅A |  |
| 5 | 4. | Mysteel铝产品库存及出库表 | 电解铝社会库存；电解铝厂内库存；电解铝出库量; 多用于研报月报转载，非SMM固定 | ID01002072 | 电解铝：厂内库存：中国（日） | mysteel | ✅A |  |
| 6 | 4. | SMM国内主流消费地电解铝锭库存 | SMM国内主流消费地电解铝锭库存; SMM周度铝锭库存；国内主流消费地电解铝锭库 | — | 无数据 | — | ❌C | 知几无数据 |
| 7 | 4. | 上期所沪铝期货仓单时序 | 上期所沪铝期货仓单; 上海期货交易所铝期货仓单；同花顺iFinD常见名：期货仓单 | ID01552110 | USGS：粗铝：进口数量：美国（年） | mysteel | ✅A |  |
| 8 | 4. | 国内铝水比例与铝锭库存 | 国内铝水比例；铝锭社会库存; SMM国内铝水比例；国内电解铝铝水比例 | ID01001759 | 电解铝：铝水比例：中国（月） | mysteel | ✅A |  |
| 9 | 4. | 社会库存分地区结构 | 无锡/佛山/巩义/上海/重庆/天津等地电解铝社会库存; SMM/Mysteel社 | ID00188303 | 电解铝：现货库存：天津（日） | mysteel | ✅A |  |
| 10 | 4. | 铝棒加工费与铝棒库存 | 铝棒加工费；铝棒社会库存; 6063铝棒加工费；佛山/无锡铝棒加工费；国内铝棒社 | ID00259465 | 铝棒：6063：Φ120：加工费：佛山（日） | mysteel | ✅A |  |
| 11 | 4. | 铝棒社会库存 | 国内铝棒社会库存; 国内铝棒社会库存 | — | 无数据 | — | ❌C | 知几无数据 |
```

**案例判定依据**：
- 上期所沪铝期货仓单：同花顺正确识别旧ID FU00016906（CZCE硅锰仓单）为错配，给出正确名称"上期所沪铝期货仓单"，但知几搜索后结果为C级（知几无数据）
- LME铝总库存：旧ID ID01552110（USGS粗铝进口数量）为品种+指标类型双重错误，同花顺纠正为"LME铝总库存"，知几命中ID01721697（氧化铝库存）——命中氧化铝而非LME铝，属于弱匹配
- 铝棒社会库存：SMM/Mysteel无独立指标，知几搜索无结果，C级

---

### 组3：跨品种串指标案例

**案例：ID01552110（USGS：粗铝：进口数量：美国（年））被多次错误分配给不同品种不同指标**

---

#### 3.1 同花顺返回原文（引用AL_库存_iwencai_r1.md 中ID01552110相关部分）

```
- 4.1|LME Aluminium Total Inventories / Open Stocks
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.1|Registered Warrants / Cancelled Warrants
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.3|连续去库且绝对值回落至80万吨下方
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.1|最终保留图
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
- 4.2|最终保留图
  旧ID: ID01552110 | 旧名: USGS：粗铝：进口数量：美国（年）
```

同花顺在回复中对每一条都标注了"❌ 错误"，说明旧ID对应USGS粗铝进口，品种和平台均不对。

#### 3.2 Prompt全文（AL_库存_prompt.txt）

```
你是铝基本面分析师，帮我纠正以下指标映射。
以下是AL·库存(4.1-4.5)板块的旧指标名称和对应的 zhiji_id，其中部分 zhiji_id 是错误的。
请帮我：
1. 识别哪些 zhiji_id 是明显错误的（品种不对、指标类型不对）
2. 对每个正确的指标，给出 SMM 和 Mysteel 平台的精确指标全称（用于知几搜索的关键词）
3. 对于没有 SMM/Mysteel 数据的指标，说明应该用哪个数据源
请用表格格式回复，列为：图名称 | 是否正确 | SMM精确名 | Mysteel精确名 | 备注
```

#### 3.3 zhiji_search.json（AL_供给_zhiji_search.json 中ID01552110跨品种案例）

```json
{
  "2.|中国原铝产量": {
    "subnode": "2.",
    "chart": "中国原铝产量",
    "names": ["IAI中国原生铝产量; 中国原生铝产量"],
    "grade": "A",
    "hit_id": "ID01001542",
    "hit_name": "再生铝合金锭：158家样本企业：产量：中国（月）",
    "hit_path": "行业数据 有色金属 有色金属数据库 供给 产量 铝金属",
    "hit_source": "mysteel",
    "searched_terms": ["中国原铝产量"]
  },
  "2.|再生铝开工率": {
    "subnode": "2.",
    "chart": "再生铝开工率",
    "names": ["再生铝合金开工率; 再生铝行业开工率；再生铝合金开工率"],
    "grade": "A",
    "hit_id": "ID01552110",
    "hit_name": "USGS：粗铝：进口数量：美国（年）",
    "hit_path": "USGS 铝土矿 进口 美国 年",
    "hit_source": "mysteel",
    "searched_terms": ["再生铝开工率"]
  },
  "2.|氧化铝开工率": {
    "subnode": "2.",
    "chart": "氧化铝开工率",
    "names": ["全国冶金级氧化铝周度开工率; 全国冶金级氧化铝周度开工率"],
    "grade": "A",
    "hit_id": "ID01552110",
    "hit_name": "USGS：粗铝：进口数量：美国（年）",
    "hit_path": "USGS 铝土矿 进口 美国 年",
    "hit_source": "mysteel",
    "searched_terms": ["氧化铝开工率"]
  },
  "2.|澳大利亚/印尼等来源国": {
    "subnode": "2.",
    "chart": "澳大利亚/印尼等来源国",
    "names": ["中国自澳大利亚/印尼进口铝土矿量; 无统一SMM名"],
    "grade": "A",
    "hit_id": "ID01552110",
    "hit_name": "USGS：粗铝：进口数量：美国（年）",
    "hit_path": "USGS 铝土矿 进口 美国 年",
    "hit_source": "mysteel",
    "searched_terms": ["澳大利亚/印尼等来源国"]
  }
}
```

#### 3.4 Correction文件（AL_供给_correct_20260902.md 中ID01552110多条）

```
| 9 | 2. | 再生铝开工率 | 再生铝合金开工率; 再生铝行业开工率；再生铝合金开工率 | ID01552110 | USGS：粗铝：进口数量：美国（年） | mysteel | ✅A |  |
| 20 | 2. | 氧化铝开工率 | 全国冶金级氧化铝周度开工率; 全国冶金级氧化铝周度开工率 | ID01552110 | USGS：粗铝：进口数量：美国（年） | mysteel | ✅A |  |
| 25 | 2. | 澳大利亚/印尼等来源国 | 中国自澳大利亚/印尼进口铝土矿量; 无统一SMM名 | ID01552110 | USGS：粗铝：进口数量：美国（年） | mysteel | ✅A |  |
```

**案例判定依据**：
- ID01552110（USGS：粗铝：进口数量：美国（年））在旧映射中被反复错误分配到：
  - AL·库存 4.1 LME铝总库存（品种+指标类型双错：USGS vs LME，粗铝进口 vs 库存）
  - AL·库存 4.1 注册仓单/注销仓单（同上）
  - AL·库存 4.3 连续去库判断（指标类型错误：进口量 vs 库存变化）
  - AL·库存 4.1/4.2 最终保留图（非指标）
  - AL·供给 再生铝开工率（品种错：USGS粗铝进口 vs 再生铝开工率）
  - AL·供给 氧化铝开工率（品种错：USGS粗铝进口 vs 氧化铝开工率）
  - AL·供给 澳大利亚/印尼来源国（品种错：USGS美国 vs 澳大利亚/印尼）
- 知几搜索"再生铝开工率"、"氧化铝开工率"等关键词均返回ID01552110作为最佳命中，标记为A级——但实际上这是跨品种污染
- 审计报告_A级命中复核_20260902.md 中确认：AL板块27条问题中有3条A级假命中，ID01552110即为其中主要代表

---

## 4.2 指标匹配映射表（40+行）

以下从 step2_match_*.json、correction_*.md、iwencai_r1.md 中提取覆盖 ZN/PB/CU/AL/NI/SN/SI/LI 的映射记录：

| # | 同花顺指标名称 | zhiji数据库字段名 | 指标所属品种 | 匹配结果 | 失败原因 |
|---|---------------|------------------|------------|---------|---------|
| 1 | LME铜库存、上期所铜库存、COMEX铜库存 | COMEX：铜：期货库存（日）/ LME：铜：注册仓单（日）/ LME：铜：注销仓单（日）/ SHFE：铜(BC)：期货库存（周） | CU | ✅A | — |
| 2 | 各LME仓库/地点铜库存 | LME：铜：期货库存：香港（日）/ LME：铜：非仓单库存：欧洲（日） | CU | ⚠️B | 有分地点但不完整 |
| 3 | SHFE铜仓单、沪铜主力价格、现货升贴水 | SHFE：铜(BC)：期货库存（周）/ SHFE：电解铜：主力合约：收盘价（日）/ 电解铜：平水铜：现货升贴水：山东（日） | CU | ✅A | — |
| 4 | SMM 1#电解铜升贴水 | 电解铜：1#：升贴水：上海（日） | CU | ✅A | — |
| 5 | 在途海运铜库存估算 | — | CU | ❌C | 知几无数据 |
| 6 | 精铜杆企业原料库存 | — | CU | ❌C | 知几无中国精铜杆原料库存 |
| 7 | 精铜杆企业成品库存 | 铜杆：社会库存：中国（日） | CU | ✅A | — |
| 8 | 上期所沪铝期货仓单 | — | AL | ❌C | 知几无数据 |
| 9 | LME铝总库存 | 氧化铝：库存：中国（周） | AL | ✅A(弱) | 命中氧化铝非LME铝 |
| 10 | 中国主要地区电解铝社会库存 | — | AL | ❌C | 知几无数据 |
| 11 | 中国电解铝企业厂内铝锭库存 | 电解铝：厂内库存：中国（日） | AL | ✅A | — |
| 12 | 电解铝社会库存、厂内库存、出库量 | 电解铝：厂内库存：中国（日） | AL | ✅A | — |
| 13 | 铝棒社会库存 | — | AL | ❌C | 知几无数据 |
| 14 | 再生铝开工率 | USGS：粗铝：进口数量：美国（年） | AL | ✅A(假) | 跨品种污染：USGS粗铝进口≠再生铝开工率 |
| 15 | 氧化铝开工率 | USGS：粗铝：进口数量：美国（年） | AL | ✅A(假) | 跨品种污染：USGS粗铝进口≠氧化铝开工率 |
| 16 | 中国原铝产量 | 再生铝合金锭：158家样本企业：产量：中国（月） | AL | ✅A | — |
| 17 | 铝土矿：三水型：几内亚产CIF价 | 铝土矿：三水型：45%Al，3%Si：几内亚产：CIF价：山东主要港口 | AL | ✅A | — |
| 18 | 精炼镍开工率+镍价 | 精炼镍：开工率：中国（月） | NI | ✅A | — |
| 19 | 三元电池排产+镍价 | 冷轧不锈钢：300：排产：中国（月） | NI | ✅A | — |
| 20 | LME镍库存+镍价 | 精炼镍：库存：中国：27家样本仓库（周） | NI | ✅A | — |
| 21 | 不锈钢表观消费量 | 不锈钢：表观消费量：中国（月） | NI | ✅A | — |
| 22 | 三元电池排产 | 冷轧不锈钢：300：排产：中国（月） | NI | ✅A | 实际应为三元正极材料产量 |
| 23 | 镍进口量 | 镍湿法中间品：进口量：印尼→中国（月） | NI | ✅A | 口径不同：SMM=湿法中间品 vs Mysteel=精炼镍 |
| 24 | 镍矿CIF价格 | 红土镍矿：1.6%Ni，0.05%Co，20%Fe，1%Cr，35%含水：CIF价：印尼（日） | NI | ✅A | — |
| 25 | 电解镍日度利润 | 电解镍：Ni≥99.96%：俄罗斯产：现货到岸升贴水：中国（日） | NI | ✅A | — |
| 26 | 镍矿港口库存 | 菲律宾镍矿：港口库存：12个港口（周） | NI | ✅A | — |
| 27 | 精炼锡产量 | 精炼锡：产量：印尼：天马（季） | SN | ✅A | — |
| 28 | 焊锡终端产量 | 精炼锡：产量：印尼：天马（季） | SN | ✅A | 匹配到印尼天马而非国内焊锡 |
| 29 | 焊锡开工率 | — | SN | ❌C | 知几无数据 |
| 30 | 锡化工开工率 | — | SN | ❌C | 知几无数据 |
| 31 | 焊锡表观消费量 | — | SN | ❌C | 知几无数据 |
| 32 | 焊锡终端库存 | — | SN | ❌C | 知几无数据 |
| 33 | 排产计划 | — | SN | ❌C | 知几无数据 |
| 34 | 锡化工订单量同比增速 | 精炼锡：出口数量：马来西亚（月） | SN | ✅A(假) | 出口量≠订单量 |
| 35 | 锡矿进口实物量（万吨） | CM0000451711（澳大利亚）+ CM0000451719（俄罗斯） | ZN | ✅A | — |
| 36 | 国内锌矿产量 | — | ZN | ❌C | 知几无国内锌矿产量 |
| 37 | 锌矿进口盈亏 | 铜进口盈亏（日）（近似） | ZN | ✅A | 知几无锌矿进口盈亏 |
| 38 | 国内精炼锌产量 | ID01510883（月）+ ID01593781（周） | ZN | ✅A | — |
| 39 | 锌精矿港口库存 | ID00188330 | ZN | ✅A | — |
| 40 | 锌矿企业利润 | — | ZN | ❌C | 知几无锌矿企业利润 |
| 41 | 锌锭库存（SMM三地） | ID00188329（锌锭现货库存中国） | ZN | ✅A | — |
| 42 | 锌出口利润 | ID02424836（先进生物燃料D5价格） | ZN | ❌C | 知几无锌出口利润，命中完全无关 |
| 43 | 沪市锌锭升贴水 | ID01167397（锌锭升贴水广东）+ ID01167389（上海） | ZN | ✅A | — |
| 44 | 沪市基差 | FU00024317（SHFE锌基差） | ZN | ✅A | — |
| 45 | 制造业PMI | ID00002349（螺纹钢HRB400E汇总价格上海） | ZN | ❌C | 知几无PMI，命中螺纹钢价格 |
| 46 | 碳酸锂期货主力合约收盘价 | GFEX: 碳酸锂: 主力合约: 收盘价: 日度 | LI | ✅A | — |
| 47 | 氢氧化锂现货升贴水 | SMM: 精炼锡进出口盈亏: premium: 日度 | LI | ❌C | 跨品种污染：锡≠锂 |
| 48 | 碳酸锂社会库存 | SMM: 四地样本碳酸锂社会库存（上海，江苏，江西，四川）: 周度 | LI | ✅A | — |
| 49 | 沪伦比（碳酸锂） | SMM: 电解铝: 沪伦铝比值: 日度 | LI | ❌C | 跨品种污染：铝≠锂 |
| 50 | 工业硅主力合约收盘价 | GFEX: 工业硅: 主力合约: 收盘价: 日度 | SI | ✅A | — |
| 51 | 工业硅现货升贴水 | SMM铜产业链季度平衡:SMM1#电解铜现货升贴水均价: 预测值 | SI | ❌C | 跨品种污染：铜≠硅 |
| 52 | 工业硅冶炼利润 | 工业硅：421#：利润：新疆（周） | SI | ✅A | — |
| 53 | 工业硅冶炼成本 | 工业硅：421#：成本：新疆（周） | SI | ✅A | — |
| 54 | 国内硅矿月产量 | 日本水泥协会：矿渣硅酸盐水泥：销量占比：国内（年） | SI | ❌C | 完全无关命中 |

---

## 4.3 绘图脚本样例

### 4.3.1 成功绘图代码样例（_pipeline/_draw_charts.py 核心节选）

```python
# -*- coding: utf-8 -*-
"""
第3段：画图层 (v3 修复版)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
功能：
  读 _chart_config.json + mid_data/raw_data → 出 PNG 到 charts/

图型规则（SPEC）：
  ┌────────────┬────────────────────────────────────────────────────────────┐
  │ 类型        │ 规则                                                        │
  ├────────────┼────────────────────────────────────────────────────────────┤
  │ seasonal   │ X轴=1月~12月; 按年叠色; 浅粉底#FFF0F5;                     │
  │            │ 2023浅蓝/2024蓝/2025橙/2026深红加粗; 无marker/标题/来源;    │
  │            │ 微软雅黑; 浅灰网格#cccccc; 图例右上; 图上方标注数据来源      │
  ├────────────┼────────────────────────────────────────────────────────────┤
  │ line       │ X轴=时间轴自适应; 单轴单系列细线 / 双轴双色;                 │
  │            │ 样式同季节性(浅粉底/无标题/微软雅黑)                         │
  ├────────────┼────────────────────────────────────────────────────────────┤
  │ gap        │ 不画空白图, 显示"数据暂缺: XXX"占位文字                       │
  └────────────┴────────────────────────────────────────────────────────────┘

v3 修复内容：
  1. TC line 图竖线问题：date 字段为纯整数(行号)时，识别为周度连续序列，
     映射到近似日期(从2021-01-01起每周+7天)，而非全部映射到2026-01-01
  2. 季节性图12月缺失：month_frac 改用 days_in_month 精确计算，
     xlim 调整为 (0.5, 13.0) 以容纳12月尾日数据
  3. 背景色改为浅粉底 #FFF0F5
  4. 每张图上方标注数据来源(Excel/zhiji + 变量标识)
"""

import json, sys, os, calendar
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
PIPE = BASE / '_pipeline'
RAW = BASE / 'raw_data'
MID = BASE / 'mid_data'
CHARTS = BASE / 'charts'
CHARTS.mkdir(exist_ok=True)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import font_manager
    import numpy as np
    import calendar
except ImportError:
    print("需要 matplotlib / numpy / calendar")
    sys.exit(1)

# ─── 中文字体 ────────────────────────────────────────────────────────
def setup_font():
    candidates = [
        "Microsoft YaHei", "微软雅黑",
        "SimHei", "黑体",
        "WenQuanYi Micro Hei",
        "Noto Sans CJK SC",
    ]
    for name in candidates:
        try:
            fp = font_manager.findfont(name, fallback_to_default=False)
            if fp and os.path.exists(fp):
                plt.rcParams['font.family'] = name
                return name
        except Exception:
            continue
    plt.rcParams['font.family'] = 'sans-serif'
```

### 4.3.2 绘图配置（_chart_config.json 节选）

```json
{
  "_说明": "61张图配置（锌版）。从 _精确Excel映射表.json 转换，添加图型分类。数据源=zhiji_id 或 excel_only 或 needs_fix。chart_type: seasonal(图例=年份) / line(图例=指标名)。",
  "charts": [
    {
      "chart_id": "chart1",
      "name": "Zn50 TC周度均值",
      "slide": 5,
      "source_type": "excel_only",
      "zhiji_id": null,
      "excel_fallback": ["锌SMM补充数据", "TC", "B", "D"],
      "chart_type": "line",
      "series": ["国产TC", "进口TC"],
      "output": "chart01_tc_line.png",
      "dual_axis": true,
      "ylabel": "元/干吨"
    },
    {
      "chart_id": "chart3",
      "name": "沪锌结算价",
      "slide": 19,
      "source_type": "confirmed",
      "zhiji_id": "FU00016353",
      "excel_fallback": ["锭篇", "沪锌价格", "H"],
      "chart_type": "seasonal",
      "series": ["2021", "2022", "2023", "2024", "2025", "2026"],
      "output": "chart03_shfe_settle_seasonal.png"
    },
    {
      "chart_id": "chart4",
      "name": "锌出口利润",
      "slide": 19,
      "source_type": "excel_only",
      "zhiji_id": null,
      "excel_fallback": ["锭篇", "源点补充", ...],
      "chart_type": "seasonal"
    }
  ]
}
```

### 4.3.3 失败绘图案例及原因

**案例1：chart25 国产矿冶炼利润 — Excel公式返回#N/A**

```
原因：Excel 公式因缺输入返回 #N/A，只能读 PPT 缓存
配置：source_type: "needs_fix", zhiji_id: null
```

**案例2：chart7 锌主连月差 — zhiji ID01167312 符号反了**

```
原因：zhiji ID01167312 符号反了（正负号错误），改用 Excel 源
配置：source_type: "needs_fix"
```

**案例3：chart4 锌出口利润 — 知几搜索命中完全无关**

```
原因：搜索"锌出口利润"命中 ID02424836（先进生物燃料D5价格），match_score=-1, match_status="NO_DATA"
实际使用：改用 zhiji ID01030236（锌锭进口盈亏含税，日度）近似替代
```

---

## 4.4 匹配逻辑代码/规则

### 4.4.1 指标关键词匹配逻辑

**文件：`step2_zhiji_verify.py`（完整代码已由subagent返回）**

关键逻辑摘录：

```python
# 搜索词构造（第XXX行）
def build_search_query(indicator_name, variety):
    """从指标名中提取搜索关键词"""
    # 1. 去掉机构前缀: SMM / Mysteel / 我的钢铁 / LME
    name = re.sub(r'(SMM|Mysteel|我的钢铁|LME)\s*[:：]?\s*', '', indicator_name)
    # 2. 去掉频率后缀: 周度 / 月度 / 日度
    name = re.sub(r'(周度|月度|日度|季度)', '', name)
    # 3. 去掉单位后缀: 元/吨 / 美元/干吨 / 万吨
    name = re.sub(r'(元/吨|美元/干吨|万吨|万金属吨)', '', name)
    # 4. 添加品种词
    variety_cn = {"CU": "铜", "AL": "铝", "NI": "镍", "SN": "锡", "ZN": "锌", "PB": "铅", "SI": "硅", "LI": "锂"}
    query = f"{variety_cn.get(variety, '')} {name}"
    return query
```

```python
# 分级规则（第XXX行）
def grade_match(search_results, indicator_name):
    """根据搜索结果判定A/B/C级别"""
    if not search_results:
        return "C", None, None  # 无结果 → C级
    
    top = search_results[0]
    name = top.get("name", "")
    
    # A级判定：命中名包含品种词 + 指标类型词
    if contains_variety_word(name) and contains_indicator_type(name):
        return "A", top["id"], name
    
    # B级判定：部分匹配
    if contains_variety_word(name) or contains_indicator_type(name):
        return "B", top["id"], name
    
    # C级判定：命中但完全无关
    return "C", top["id"], name
```

### 4.4.2 去重规则

**文件：`step0_extract.py`（完整代码已由subagent返回）**

```python
# 跨节点去重（第XXX行）
def dedup_cross_node(indicators, node_map):
    """同一指标出现在多个节点时，保留首次出现的节点"""
    seen = set()
    unique = []
    for ind in indicators:
        key = (ind["name"], ind["variety"])
        if key not in seen:
            seen.add(key)
            unique.append(ind)
        else:
            # 记录重复，但不删除
            duplicate_log.append(ind)
    return unique, duplicate_log
```

### 4.4.3 归属校验规则

**文件：`calibration_mechanism.md` + `METHODOLOGY_INDICATOR_CORRECTION.md`**

```
归属校验规则（5条）：

1. 品种校验：命中名必须包含本品种关键词（铜→铜/铜精矿/电解铜；铝→铝/电解铝/氧化铝）
   反例：搜"铝库存"命中"USGS：粗铝：进口数量：美国" → 品种词有"铝"但指标类型不对 → B级
   
2. 板块校验：指标必须落在本子节点边界内（以tree_config.json该节点q字段+板块定义为准）
   跨类指标→剔除放备用库
   
3. 频率校验：同频指标才能同图（日频+日频=OK；日频+月频=需双轴展示并标注频率差异）
   
4. 正主校验：每子节点1个正主指标，其余作辅助/交叉验证
   正主必须贴合本节点tree_config的q字段定义
   
5. 防串用规则：已在别页做正主的指标禁止在本页重复当正主
   grep 已有build脚本/已发布HTML的指标ID
```

### 4.4.4 正主防串用规则

**文件：`AGENTS.md`（框架级规范）**

```
正主防串用（强制）：做任何节点前，先查这个指标是否已经是其他页面的正主
（grep 已有 build 脚本 / 已发布 HTML 的指标 ID）。
已在别页做正主的指标（如 i18 铅锭社库=4.3 正主、j25_tc=2.5 正主）
禁止在本页重复当正主，只能作辅助交叉或进备用库。
正主必须贴合本节点 tree_config 的 q 字段定义。
```

### 4.4.5 分数阈值规则

**文件：`step2_match_*.json` + `_step2_state.json`**

```
分级标准：
  A级（精确命中）：命中名含品种词 + 指标类型词 + 频率匹配
  B级（弱匹配）：命中名含部分关键词，但品种或类型不完全匹配
  C级（无数据）：知几无数据或命中完全无关指标

从_step2_state.json观察：
  - grade字段值为"A"/"B"/"C"
  - hit_score字段始终为0（未启用数值评分，仅用布尔判定）
  - hit_source字段为"mysteel"或"smm"或null
```

### 4.4.6 同花顺纠错5条规则

**文件：`METHODOLOGY_INDICATOR_CORRECTION.md`**

```
| # | 规则 | 触发条件 | 同花顺如何识别 |
|---|-----|---------|------------|
| 1 | 品种错 | 命中名含其他品种词 | 看命中名的品种词（白银≠锌） |
| 2 | 地域错 | 海外概念命中国内 | 理解国家归属（秘鲁≠中国） |
| 3 | 产业链错位 | 矿山概念命中冶炼端 | 理解"矿山→冶炼→加工"上下游 |
| 4 | 个股 vs 行业 | 命中含公司名 | 识别公司主体，判定非行业口径 |
| 5 | 单一 vs 整体 | 命中含具体仓库/工厂 | 判断样本代表性不足 |
```

### 4.4.7 LLM匹配prompt

**文件：`METHODOLOGY_INDICATOR_CORRECTION.md` Step1/Step1b 模板**

```
Step1 纠正prompt模板：
"不是不是，你帮我看看这里是关于金属{品种}{板块}的指标，你看看哪些是不相关的？
 | 概念指标 | 旧映射 | 旧命中 |
 | {指标名1} | {旧zhiji_id} | {旧命中名} |
 ...
"

Step1b 推荐指标prompt模板：
"好，继续。再帮我看看这里是关于金属{品种}{板块}的指标，你帮我给出每个指标对应的SMM有色网和Mysteel钢联的官方全称、数据频率和单位。
 | 我需要的指标 | 说明 |
 | {指标名1} | {用途说明} |
 ...
 请按表格输出：
 | 指标 | SMM有色网官方全称 | Mysteel钢联官方全称 | 数据源 | 频率 | 单位 | 备注 |
"
```

---

## 4.5 节点A-F 输入/输出格式说明

### 节点A：读取 GitHub framework-tree 各商品主题节点

**输入**：
- `framework-tree/data/tree_config.json` — 品种定义（8个品种：CU/AL/PB/ZN/NI/SN/LC/SI）+ 6大板块 + 33个子节点 + q字段（板块定义说明）
- `framework-tree/data/indicators_v1.json` — 指标元数据唯一真源（v3.48，786个指标）
- `framework-tree/data/export_node_map.json` — 页面导出节点映射（494行，7个品种×6-8个板块的子页HTML文件清单）
- `framework-tree/data/chart_registry.json` — 图表注册表（259页面/596图表/49异常）

**输出**：
- 品种列表、板块列表、子节点列表
- 每个节点的预期指标数量和类型

**存储路径**：`framework-tree/data/`

### 节点B：调用同花顺Agent（问财）

**输入**：
- `prompt.txt` — 发送给同花顺的纠正prompt（包含旧指标名+旧zhiji_id+旧命中名）
- 浏览器CDP连接 — 通过WebSocket注入prompt到同花顺编辑器

**输出**：
- `*_iwencai_r1.md` / `*_iwencai_round1.md` — 同花顺返回原文（md格式，含纠正表+溯源+搜索记录）
- `*_iwencai_reply.md` — 同花顺回复副本（与r1内容相同，路径不同）

**存储路径**：
- `framework-tree/translation-workspace/correction/cu-al-ni-sn/{CU,AL,NI,SN}/`
- `framework-tree/translation-workspace/correction/{CU,AL,NI,SN}/`
- `framework-tree/analysis/iwencai/{CU,AL,NI,SN,ZN}/divergence_*.md`（发散文件）

**关键参数**：
- 两次发送间隔 ≥ 90秒（同花顺限流）
- prompt长度 ≤ 10000字（编辑器硬上限）
- 等至少20秒生成完成（判据：body出现"内容由AI生成，不构成投资建议"）
- 用 `[contenteditable]` 注入 + 完整鼠标事件序列点击 `.send-button`

### 节点C：将同花顺推荐指标匹配 zhiji 本地数据库字段

**输入**：
- `*_iwencai_r1.md` — 同花顺返回的精确指标全称（SMM + Mysteel）
- `*_zhiji_search.json` — 知几搜索中间结果（关键词→zhiji_id→命中名→path）
- `_zhiji_cache.py` — 本地缓存管理（首次全量拉取→保存→增量更新→纯本地模式）
- `_zhiji_match_results.json` — 匹配结果汇总（chart_id→desc→series_results→best_match→match_score）

**输出**：
- `step2_match_{品种}.json` — 每个品种的全量映射表（subnode|chart|name→grade→hit_id→hit_name→hit_source）
- `_step2_state.json` — 断点续跑状态（key=subnode|name[:50]）
- `_zhiji_verify_results.json` — 验证结果（keyword→zhiji_id→zhiji_name→ppt_orig_last3→match_status）
- `_zhiji_research_results.json` — 研究结果（chart→all_results→diff→status）
- `_zhiji_search_needs_fix.json` — 需修复的搜索结果

**存储路径**：
- `framework-tree/translation-workspace/mapping/{AL,CU,LI,NI,SI,SN,ZN}/step2_match_*.json`
- `framework-tree/translation-workspace/mapping/raw/B_*.csv`
- 工作区根目录 `_zhiji_*.json` / `_zhiji_*.py`

**关键规则**：
- 搜索词压缩：去掉SMM/Mysteel前缀、频率、单位、口径注释、调研样本数、括号注释
- 保留：品种词 + 产品形态 + 指标类型 + 地域
- 知几API限流：1次/秒
- 纯英文名(LME官方名)优先带品种前缀

### 节点D：校验指标归属品种，排除跨品种污染

**输入**：
- `step2_match_{品种}.json` — 节点C的输出
- `*_correct_*.md` — 纠正对照表（同花顺审计+知几验证）
- `*_correct_*.json` — 纠正结果JSON（含false_positives列表）
- `METHODOLOGY_INDICATOR_CORRECTION.md` — 纠正方法论（5条纠错规则）
- `calibration_mechanism.md` — 校准机制（四步闭环）
- `NI_FULL_MATRIX.md` — 全节点标准答案 vs 实际对照矩阵
- `AUDIT_NI_REPORT.md` — 指标归属审计报告（万金油/板块串用/正主缺失/冗余膨胀）
- `审计报告_A级命中复核_20260902.md` — A级假命中复核（489指标/401A/25B/62C/99问题）

**输出**：
- 标记跨品种污染的指标（如ID01552110被标记为AL假命中）
- 标记板块串用的指标（如冰镍进口量被放在3.供给而非6.进出口）
- 标记正主缺失的节点（如NI 2.4缺少期限结构/月差/价差关键词命中）
- 标记万金油指标（被≥3个节点复用的指标）

**存储路径**：
- `framework-tree/docs/AUDIT_NI_REPORT.md`
- `framework-tree/docs/NI_FULL_MATRIX.md`
- `framework-tree/docs/METHODOLOGY_INDICATOR_CORRECTION.md`
- `framework-tree/docs/calibration_mechanism.md`
- `framework-tree/translation-workspace/correction/cu-al-ni-sn/审计报告_A级命中复核_20260902.md`
- `framework-tree/translation-workspace/correction/cu-al-ni-sn/HANDOVER.md`

**关键规则**：
- 品种词匹配：命中名必须含本品种关键词
- 板块校验：指标必须落在tree_config.json该节点q字段定义范围内
- 正主防串用：grep已有build脚本/已发布HTML的指标ID
- 跨品种污染标记：ID01659225（矿产粗铜产量）被反复误用到价格/库存/持仓

### 节点E：生成绘图代码，生成图表

**输入**：
- `_chart_config.json` — 61张图的配置（chart_id→name→slide→source_type→zhiji_id→chart_type→series→output）
- `raw_data/` + `mid_data/` — 原始数据
- `_zhiji_cache/` — zhiji本地缓存
- `step2_match_*.json` — 映射表（确定哪些指标有数据可用）

**输出**：
- `charts/*.png` — 最终图表PNG
- `_pipeline/_overlay_charts.py` — PPTX图表到PNG替换（用lxml处理）
- `_pipeline/_composite_formulas.py` — 6个复合公式（冶炼利润/加工费/TC/进口盈亏等）
- `_pipeline/_data_summary.py` — 最新数据摘要提取
- `_pipeline/_fetch_raw.py` — 数据获取层（zhiji API + Excel多列）
- `_pipeline/_refresh_all_zhiji.py` — 刷新全部锌+铅zhiji ID

**存储路径**：
- `_pipeline/`
- `charts/`

**关键规则**：
- seasonal类型：X轴=1月~12月，按年叠色（2023浅蓝/2024蓝/2025橙/2026深红加粗）
- line类型：X轴=时间轴自适应，单轴单系列细线/双轴双色
- gap类型：不画空白图，显示"数据暂缺: XXX"占位文字
- 背景色：浅粉底 #FFF0F5
- 字体：微软雅黑
- 网格：浅灰 #cccccc

### 节点F：图表+文案回填 GitHub 看板对应标签页

**输入**：
- `charts/*.png` — 已生成的图表
- `api_server.py` — 数据API服务器（实时调用+3天滑动缓存）
- `PAGE_SPEC.md` — 页面统一规范（页头三段式/导航回链/图表卡片/底部note/Footer/反拷贝保护/季节图规则/数据内嵌/目录命名规范/三道门禁）
- `SOP_pipeline.md` — 7步标准流水线（同花顺提问→指标筛选→知几命中→入库→拉数据→画图→推送）
- `CHART_REGISTRY.md` — 图表注册表（259页面/596图表/420正确归属/127无关键词匹配/49可疑归属）
- `export_node_map.json` — 页面导出节点映射
- `build_overview_all.py` + `build_overview_cu_al.py` — 总览页批量生成
- `_embed_log.txt` — 图表嵌入日志（61张图跨20个slide）
- `_嵌入状态_锌_20260821.md` — 嵌入状态表
- `list_tabs.py` — 浏览器标签页列表（CDP WebSocket）

**输出**：
- `index.html` — 主看板页面（PAGE_MAP含80条映射，覆盖cu/al/pb全部子页+zn/ni/sn/si/li动态跳转）
- `*.html` — 各品种子页（按PAGE_SPEC规范：页头三段式/导航回链/图表卡片/底部note/Footer）
- `overview.html` — 总览页（静态卡片页面）
- `api_server.py` 运行在端口8786 — 提供 `/api/indicator?code=CU&metric=社库` 接口
- `api_cache.db` — SQLite缓存（3天滑动窗口）

**存储路径**：
- `framework-tree/`（前端页面+脚本+文档）
- `framework-tree/scripts/`（API服务器+构建脚本）
- `framework-tree/docs/`（规范文档）

**关键规则**：
- 数据内嵌：页面数据必须硬编码进HTML，不许fetch/XMLHttpRequest/axios
- 反拷贝保护：禁止右键/Ctrl+C/S/P/U/选中
- 三道门禁：check_html.py（静态校验）+ verify_render.js（jsdom渲染校验）+ reclaim.py（格式契约+产物完整性）
- PAGE_MAP：index.html第288-408行的手写字典，从16条→80条，覆盖cu/al/pb全部子页
- 品种前缀：cu/al/pb/zn/ni/sn/li/si（小写，硅用si不用sg，锂用li）

---

## 已读取文件清单

### 节点A（6个文件）
1. `framework-tree/data/tree_config.json` — 品种+板块+子节点定义
2. `framework-tree/data/export_node_map.json` — 页面导出映射（494行）
3. `framework-tree/data/chart_registry.json` — 图表注册表（1791+行）
4. `framework-tree/data/indicators_v1.json` — 指标元数据（13132行，仅读前120行+统计）
5. `framework-tree/translation-workspace/mapping/STEP3_REVIEW_LIST.md` — Step3复核清单（424行，A318+B285）
6. `framework-tree/translation-workspace/mapping/_step2_state.json` — Step2状态（1421行）

### 节点B（13个文件）
7. `framework-tree/translation-workspace/correction/cu-al-ni-sn/HANDOVER.md` — 交接文档（133行）
8. `framework-tree/translation-workspace/correction/cu-al-ni-sn/CU/CU_库存_iwencai_r1.md` — 同花顺回复（162行）
9. `framework-tree/translation-workspace/correction/cu-al-ni-sn/CU/CU_库存_iwencai_round1.md` — 同花顺回复副本（133行）
10. `framework-tree/translation-workspace/correction/cu-al-ni-sn/CU/CU_价格信号_iwencai_round1.md` — 同花顺回复（148行）
11. `framework-tree/translation-workspace/correction/cu-al-ni-sn/AL/AL_库存_iwencai_r1.md` — 同花顺回复（206行）
12. `framework-tree/translation-workspace/correction/cu-al-ni-sn/AL/AL_进出口_iwencai_r1.md` — 同花顺回复（64行）
13. `framework-tree/translation-workspace/correction/cu-al-ni-sn/NI/NI_需求_iwencai_r1.md` — 同花顺回复（161行）
14. `framework-tree/translation-workspace/correction/cu-al-ni-sn/NI/NI_成本利润_iwencai_r1.md` — 同花顺回复（130行）
15. `framework-tree/translation-workspace/correction/cu-al-ni-sn/SN/SN_需求_iwencai_r1.md` — 同花顺回复（149行）
16. `framework-tree/translation-workspace/correction/cu-al-ni-sn/审计报告_A级命中复核_20260902.md` — A级复核报告（175行）
17. `framework-tree/translation-workspace/correction/cu-al-ni-sn/{CU,AL,NI,SN}/_prompt.txt` — 24个prompt文件
18. `framework-tree/translation-workspace/correction/{CU,AL,NI,SN}/_zhiji_search.json` — 26个搜索文件
19. `framework-tree/analysis/iwencai/ZN/divergence_4.1.md` — ZN发散文件（43行）

### 节点C（16个文件）
20. `framework-tree/translation-workspace/scripts/step0_extract.py` — 概念提取脚本
21. `framework-tree/translation-workspace/scripts/step2_zhiji_verify.py` — 知几验证脚本
22. `framework-tree/translation-workspace/scripts/iwencai_audit_driver.py` — 同花顺审计驱动
23. `framework-tree/translation-workspace/mapping/AL/step2_match_AL.json` — AL映射（783行）
24. `framework-tree/translation-workspace/mapping/CU/step2_match_CU.json` — CU映射（849行）
25. `framework-tree/translation-workspace/mapping/ZN/step2_match_ZN.json` — ZN映射（3467行）
26. `framework-tree/translation-workspace/mapping/NI/step2_match_NI.json` — NI映射（4072行）
27. `framework-tree/translation-workspace/mapping/LI/step2_match_LI.json` — LI映射（646行）
28. `framework-tree/translation-workspace/mapping/SI/step2_match_SI.json` — SI映射（968行）
29. `framework-tree/translation-workspace/mapping/SN/step2_match_SN.json` — SN映射（989行）
30. `framework-tree/translation-workspace/mapping/raw/B_LI.csv` — 锂CSV（96行）
31. `framework-tree/translation-workspace/mapping/raw/B_SI.csv` — 硅CSV（146行）
32. `framework-tree/translation-workspace/mapping/raw/B_SN.csv` — 锡CSV（153行）
33. `_zhiji_match_results.json` — 匹配结果（1203行）
34. `_zhiji_verify_results.json` — 验证结果（3554行）
35. `_zhiji_search_needs_fix.json` — 需修复搜索（408行）
36. `_zhiji_research_results.json` — 研究结果（1576行）
37. `_zhiji_cache.py` — 缓存管理脚本（339行）
38. `_search_needs_fix.py` — 搜索修复脚本（43行）

### 节点D（12个文件）
39. `framework-tree/docs/METHODOLOGY_INDICATOR_CORRECTION.md` — 纠正方法论（159行）
40. `framework-tree/docs/AUDIT_NI_REPORT.md` — NI审计报告（由subagent读取）
41. `framework-tree/docs/calibration_mechanism.md` — 校准机制（109行）
42. `framework-tree/docs/NI_FULL_MATRIX.md` — NI全矩阵（由subagent读取）
43. `framework-tree/translation-workspace/correction/cu-al-ni-sn/SN/SN_需求_correct_20260902.md` — SN需求纠正表
44. `framework-tree/translation-workspace/correction/cu-al-ni-sn/NI/NI_需求_correct_20260902.md` — NI需求纠正表
45. `framework-tree/translation-workspace/correction/cu-al-ni-sn/CU/4_库存/CU_库存_correct_20260902.md` — CU库存纠正表
46. `framework-tree/translation-workspace/correction/cu-al-ni-sn/AL/AL_供给_correct_20260902.md` — AL供给纠正表
47. `framework-tree/translation-workspace/correction/cu-al-ni-sn/AL/AL_库存_correct_20260902.md` — AL库存纠正表
48. `framework-tree/translation-workspace/correction/cu-al-ni-sn/CU/2_价格信号/CU_价格信号_correct_v2_20260902.md` — CU价格信号v2
49. `framework-tree/translation-workspace/correction/cu-al-ni-sn/{CU,NI,SN}/_correct_*.json` — 3个纠正JSON
50. `_映射目录树_锌.md` — 锌映射目录树（353行）
51. `_锌zhiji映射目录.md` / `_铅zhiji映射目录.md` — 映射目录（subagent读取）
52. `_图表目录库_锌版.json` / `_数据对照_锌版.json` / `_精确Excel映射表.json` — 映射JSON（subagent读取）

### 节点E（28个文件）
53. `_pipeline/_draw_charts.py` — 绘图主脚本（762行）
54. `_pipeline/_draw_charts_v2.py` — 绘图v2（895行）
55. `_pipeline/_draw_charts_whitebg.py` — 白底绘图（799行）
56. `_pipeline/_chart_config.json` — 图表配置（1470行，61张图）
57. `_pipeline/_overlay_charts.py` — PPTX图表替换（341行）
58. `_pipeline/_composite_formulas.py` — 复合公式（320行）
59. `_pipeline/_data_summary.py` — 数据摘要（116行）
60. `_pipeline/_fetch_raw.py` — 数据获取（445行）
61. `_pipeline/_refresh_all_zhiji.py` — 刷新缓存（107行）
62. `al_demand_v3.py` — 铝需求验证（119行）
63. `cu_demand_v3.py` — 铜需求验证（122行）
64. `ni_demand_verify.py` — 镍需求验证（118行）
65. `ni_price_signal_v3.py` — 镍价格信号（130行）
66. `cu_price_signal_v3.py` — 铜价格信号（181行）
67. `sn_cost_profit_v3.py` — 锡成本利润（115行）
68. `cu_cost_profit_v3.py` — 铜成本利润（118行）
69. `batch_verify.py` — 批量验证（400行）
70. `full_audit.py` — 完整审计（221行）
71. `verify_generic.py` — 通用验证（176行）
72. `restructure.py` — 重构脚本（124行）
73. `fix_all_grades.py` — 修复级别（108行）
74. `final_audit.py` — 最终审计（23行）
75. `batch_audit.py` — 批量审计（67行）
76. `batch_fix.py` — 批量修复（121行）
77. `batch_audit2.py` — 批量审计2（40行）
78. `framework-tree/scripts/audit_chart_quality.py` — 图表质量审计（43行）
79. `framework-tree/scripts/audit_chart_quality_precise.py` — 精确审计（120行）
80. `framework-tree/scripts/build_chart_registry.py` — 构建注册表（457行）

### 节点F（9个文件）
81. `framework-tree/scripts/api_server.py` — API服务器（174行）
82. `framework-tree/docs/PAGE_SPEC.md` — 页面规范（165行）
83. `framework-tree/docs/SOP_pipeline.md` — 流水线SOP（427行）
84. `framework-tree/docs/CHART_REGISTRY.md` — 图表注册表（793行）
85. `framework-tree/scripts/build_overview_all.py` — 总览页构建（193行）
86. `framework-tree/scripts/build_overview_cu_al.py` — 铜铝总览页（243行）
87. `_embed_log.txt` — 嵌入日志（30行）
88. `_嵌入状态_锌_20260821.md` — 嵌入状态（161行）
89. `list_tabs.py` — 标签页列表（9行）

### 附加文件
90. `_all_files_combined.txt` — 685,719 bytes，全部16个映射文件的合并输出（670KB）

---

**总计读取：89+ 个文件**
