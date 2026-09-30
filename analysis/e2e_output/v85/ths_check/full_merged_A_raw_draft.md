# indicators_v1 待补指标录入草稿

> **任务**: DSH-B_REBUILD_AND_MERGE_B2_THS_TASK  
> **生成时间**: 自动重建  
> **约束**: 仅草稿，不写入指标库  

## 总览

| 指标 | 数量 |
|------|------|
| B2 重建有效待补 (仅PDF周报) | 45 |
| THS CAT_A_RAW_MISS (仅同花顺) | 667 |
| 两者均出现 | 0 |
| **合并去重总计** | **712** |

### 来源分布

| 来源标记 | 数量 | 占比 |
|----------|------|------|
| 仅同花顺 | 667 | 93.7% |
| 仅PDF周报 | 45 | 6.3% |

### B2 来源文件分布

| PDF周报文件 | 有效指标数 |
|-------------|-----------|
| 铝周报20260830.pdf | 33 |
| 镍与不锈钢周报20260906.pdf | 8 |
| 锡周报20260905.pdf | 2 |
| 氧化铝周报20260830.pdf | 1 |
| 硅产业链周报20260906.pdf | 1 |

### 品种分布

| 品种代码 | 指标数 |
|----------|--------|
| NI | 242 |
| SN | 140 |
| ZN | 115 |
| SI | 94 |
| LI | 49 |
| AL | 48 |
| CU | 13 |

### 引用次数分布 (THS)

| 引用次数 | 指标数 |
|----------|--------|
| 10+ | 2 |
| 5-9 | 5 |
| 2-4 | 100 |
| 1 | 560 |

---

## B2 重建详情

> 原始 B2 条目: 109 行
> 唯一 chart_title: 87
> 清洗后有效: 84
> 库内已存在: 21
> **有效待补 (v1 缺失): 45**

### 有效待补指标列表

| # | 指标名 | 来源PDF | 出现次数 | 同花顺交叉 | 
|---|--------|---------|----------|------------|
| 1 | 铝终端消费 | 铝周报20260830.pdf | 6 | 否 |
| 2 | 沪铝25Δ | 铝周报20260830.pdf | 3 | 否 |
| 3 | 沪铜25Δ | 铝周报20260830.pdf | 3 | 否 |
| 4 | 工业硅开炉情况 | 硅产业链周报20260906.pdf | 2 | 否 |
| 5 | 沪铝IV | 铝周报20260830.pdf | 2 | 否 |
| 6 | 白色家电消费 | 锡周报20260905.pdf | 2 | 否 |
| 7 | 镍板库存 | 镍与不锈钢周报20260906.pdf | 2 | 否 |
| 8 | MHP镍折扣系数 | 镍与不锈钢周报20260906.pdf | 2 | 否 |
| 9 | 河南进口矿现金流利润 | 氧化铝周报20260830.pdf | 1 | 否 |
| 10 | 电解铝：社库+厂库（农历） | 铝周报20260830.pdf | 1 | 否 |
| 11 | 铝棒-社库+厂库（农历） | 铝周报20260830.pdf | 1 | 否 |
| 12 | 铝板带箔-原料库存 | 铝周报20260830.pdf | 1 | 否 |
| 13 | 铝板带箔-原料库存天数 | 铝周报20260830.pdf | 1 | 否 |
| 14 | 未锻轧铝进口量 | 铝周报20260830.pdf | 1 | 否 |
| 15 | 废铝进口总量 | 铝周报20260830.pdf | 1 | 否 |
| 16 | 铝材进口量-板带 | 铝周报20260830.pdf | 1 | 否 |
| 17 | 铝材进口量-铝箔 | 铝周报20260830.pdf | 1 | 否 |
| 18 | 铝水比例 | 铝周报20260830.pdf | 1 | 否 |
| 19 | 出口-铝制品 | 铝周报20260830.pdf | 1 | 否 |
| 20 | 出口-铝材-型材条杆 | 铝周报20260830.pdf | 1 | 否 |
| 21 | 出口-铝材-板带箔 | 铝周报20260830.pdf | 1 | 否 |
| 22 | 铝材出口-中东 | 铝周报20260830.pdf | 1 | 否 |
| 23 | 铝材出口-EU-27 | 铝周报20260830.pdf | 1 | 否 |
| 24 | 铝制品出口-EU-27 | 铝周报20260830.pdf | 1 | 否 |
| 25 | 铝制品出口-北美 | 铝周报20260830.pdf | 1 | 否 |
| 26 | 铝制品出口-东南亚 | 铝周报20260830.pdf | 1 | 否 |
| 27 | 铝制品出口-中东 | 铝周报20260830.pdf | 1 | 否 |
| 28 | 乘用车批发销量（内外销）-当月值 | 铝周报20260830.pdf | 1 | 否 |
| 29 | 乘用车零售量（内销）-当月值 | 铝周报20260830.pdf | 1 | 否 |
| 30 | 乘用车零售量（内销）-累计值 | 铝周报20260830.pdf | 1 | 否 |
| 31 | 乘用车出口量-当月值 | 铝周报20260830.pdf | 1 | 否 |
| 32 | 乘用车出口量-累计值 | 铝周报20260830.pdf | 1 | 否 |
| 33 | 新能源乘用车出口量-当月值 | 铝周报20260830.pdf | 1 | 否 |
| 34 | 新能源乘用车出口量-累计值 | 铝周报20260830.pdf | 1 | 否 |
| 35 | 亏损企业比例 | 铝周报20260830.pdf | 1 | 否 |
| 36 | 汽车制造产成品周转天数 | 铝周报20260830.pdf | 1 | 否 |
| 37 | 光伏组件净出口 | 铝周报20260830.pdf | 1 | 否 |
| 38 | 电网建设累计同比 | 铝周报20260830.pdf | 1 | 否 |
| 39 | 同基准下有色库存相对比值对比 | 锡周报20260905.pdf | 1 | 否 |
| 40 | 不同镍产品折镍价 | 镍与不锈钢周报20260906.pdf | 1 | 否 |
| 41 | MHP钴折扣系数 | 镍与不锈钢周报20260906.pdf | 1 | 否 |
| 42 | 镍豆库存 | 镍与不锈钢周报20260906.pdf | 1 | 否 |
| 43 | 新能源车销量 | 镍与不锈钢周报20260906.pdf | 1 | 否 |
| 44 | 菲律宾镍矿价格（1.5%） | 镍与不锈钢周报20260906.pdf | 1 | 否 |
| 45 | 菲律宾镍矿价格：不同品味 | 镍与不锈钢周报20260906.pdf | 1 | 否 |

### 已存在于 indicators_v1 的 B2 条目

| 指标名 | 备注 |
|--------|------|
| LME仓单原产地 | 库内已存在 |
| 上期所不锈钢月间结构 | 库内已存在 |
| 中国冰镍进口量 | 库内已存在 |
| 中国冰镍进口量：自印尼 | 库内已存在 |
| 中国动力电池产量：三元 | 库内已存在 |
| 中国动力电池产量：磷酸铁锂 | 库内已存在 |
| 中国硫酸镍产量 | 库内已存在 |
| 中国精炼镍产量 | 库内已存在 |
| 中国镍铁产量 | 库内已存在 |
| 中国高碳铬铁产量 | 库内已存在 |
| 印尼冰镍产量（分品味） | 库内已存在 |
| 印尼冰镍产量（高冰镍+低冰镍） | 库内已存在 |
| 印尼精炼镍产量 | 库内已存在 |
| 工业级碳酸锂 现货价格 | 库内已存在 |
| 沪锡价格走势 | 库内已存在 |
| 电池级氢氧化锂(微粉) 价格 | 库内已存在 |
| 铝合金进口量 | 库内已存在 |
| 铝土矿进口-几内亚 | 库内已存在 |
| 铬矿价格（块矿，36-38%Cr，南非产） | 库内已存在 |
| 镍铁进口量 | 库内已存在 |
| 高碳铬铁价格（内蒙古） | 库内已存在 |

### 清洗排除的 B2 条目 (噪声)

| 指标名 | 排除原因 | 出现次数 |
|--------|----------|----------|
| AL盘面结构 | noise_term | 4 |
| 四金属 | noise_term | 4 |
| SMM: | english_label | 2 |

---

## 合并去重总清单

共 712 条指标 (PDF-B2 + THS-CAT_A 去重合并)

### 按引用次数排序 (Top 50)

| # | 指标名 | 引用次数 | 来源 | 
|---|--------|----------|------|
| 1 | 镍精矿TC（美元/吨干矿） | 18 | 仅同花顺 |
| 2 | 沪伦比（元/吨） | 12 | 仅同花顺 |
| 3 | 国内锌精炼产量（万吨） | 7 | 仅同花顺 |
| 4 | 加工费（元/吨） | 6 | 仅同花顺 |
| 5 | 多空持仓比（%） | 6 | 仅同花顺 |
| 6 | 汇率（USD/CNY） | 5 | 仅同花顺 |
| 7 | 电价（元/度） | 5 | 仅同花顺 |
| 8 | 电解镍产量（万吨） | 4 | 仅同花顺 |
| 9 | LME锡期货收盘价（美元/吨） | 3 | 仅同花顺 |
| 10 | LME镍现货价格（美元/吨） | 3 | 仅同花顺 |
| 11 | TC（美元/吨干矿） | 3 | 仅同花顺 |
| 12 | 关税税率（%） | 3 | 仅同花顺 |
| 13 | 动力电池排产计划（万吨） | 3 | 仅同花顺 |
| 14 | 印尼镍精矿进口量（万吨） | 3 | 仅同花顺 |
| 15 | 原料成本（元/吨） | 3 | 仅同花顺 |
| 16 | 国内镍精炼产量（万吨） | 3 | 仅同花顺 |
| 17 | 沪镍主力合约价格（元/吨） | 3 | 仅同花顺 |
| 18 | 电解镍现货价格（元/吨） | 3 | 仅同花顺 |
| 19 | 电解镍现金成本（元/吨） | 3 | 仅同花顺 |
| 20 | 能源成本（元/吨） | 3 | 仅同花顺 |
| 21 | 菲律宾镍矿产量（万吨） | 3 | 仅同花顺 |
| 22 | 菲律宾镍精矿进口量（万吨） | 3 | 仅同花顺 |
| 23 | 进出口金额（亿元） | 3 | 仅同花顺 |
| 24 | 镍合金排产计划（万吨） | 3 | 仅同花顺 |
| 25 | 镍生铁NPI现货价格（元/吨） | 3 | 仅同花顺 |
| 26 | 镍矿成本（元/吨） | 3 | 仅同花顺 |
| 27 | 镍铁产量（万吨） | 3 | 仅同花顺 |
| 28 | 高冰镍现货价格（元/吨） | 3 | 仅同花顺 |
| 29 | LME Cash-3M spread | 2 | 仅同花顺 |
| 30 | LME Nickel Stock | 2 | 仅同花顺 |
| 31 | LME工业硅收盘价（美元/吨） | 2 | 仅同花顺 |
| 32 | LME锌收盘价（美元/吨） | 2 | 仅同花顺 |
| 33 | LME镍近月合约价格（美元/吨） | 2 | 仅同花顺 |
| 34 | LME镍远月合约价格（美元/吨） | 2 | 仅同花顺 |
| 35 | SMM1#电解镍价格、SMM8-12%高镍生铁价格、SMM高冰镍价格 | 2 | 仅同花顺 |
| 36 | SMM1#电解镍升贴水 | 2 | 仅同花顺 |
| 37 | 不锈钢废料再生镍量（万吨） | 2 | 仅同花顺 |
| 38 | 不锈钢排产计划（万吨） | 2 | 仅同花顺 |
| 39 | 中国从印尼进口镍精矿量（万吨） | 2 | 仅同花顺 |
| 40 | 中国从新喀里多尼亚进口镍精矿量（万吨） | 2 | 仅同花顺 |
| 41 | 中国从菲律宾进口镍精矿量（万吨） | 2 | 仅同花顺 |
| 42 | 元/吨） | 2 | 仅同花顺 |
| 43 | 再生锡价格（元/吨） | 2 | 仅同花顺 |
| 44 | 再生锡进口量时序图 | 2 | 仅同花顺 |
| 45 | 再生锡进口量（万吨） | 2 | 仅同花顺 |
| 46 | 再生镍产量（万吨） | 2 | 仅同花顺 |
| 47 | 冶炼成本（元/吨） | 2 | 仅同花顺 |
| 48 | 南非锌矿进口量（万吨） | 2 | 仅同花顺 |
| 49 | 印尼镍矿HPM基准价（美元/湿吨） | 2 | 仅同花顺 |
| 50 | 印尼镍矿开工天数（天/季度） | 2 | 仅同花顺 |

---

## indicators_v1 录入草稿

> **注意**: 以下为草稿格式，未写入指标库。需人工审核后正式录入。

```json
{"name": "镍精矿TC（美元/吨干矿）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 18, "note": ""},
{"name": "沪伦比（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 12, "note": ""},
{"name": "国内锌精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 7, "note": ""},
{"name": "加工费（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 6, "note": ""},
{"name": "多空持仓比（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 6, "note": ""},
{"name": "汇率（USD/CNY）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 5, "note": ""},
{"name": "电价（元/度）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 5, "note": ""},
{"name": "电解镍产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 4, "note": ""},
{"name": "LME锡期货收盘价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "LME镍现货价格（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "TC（美元/吨干矿）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "关税税率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "动力电池排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "印尼镍精矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "原料成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "国内镍精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "沪镍主力合约价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "电解镍现货价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "电解镍现金成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "能源成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "菲律宾镍矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "菲律宾镍精矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "进出口金额（亿元）", "unit": "亿元", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "镍合金排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "镍生铁NPI现货价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "镍矿成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "镍铁产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "高冰镍现货价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 3, "note": ""},
{"name": "LME Cash-3M spread", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "LME Nickel Stock", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "LME工业硅收盘价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "LME锌收盘价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "LME镍近月合约价格（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "LME镍远月合约价格（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "SMM1#电解镍价格、SMM8-12%高镍生铁价格、SMM高冰镍价格", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "SMM1#电解镍升贴水", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "不锈钢废料再生镍量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "不锈钢排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "中国从印尼进口镍精矿量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "中国从新喀里多尼亚进口镍精矿量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "中国从菲律宾进口镍精矿量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "再生锡价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "再生锡进口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "再生锡进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "再生镍产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "冶炼成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "南非锌矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "印尼镍矿HPM基准价（美元/湿吨）", "unit": "美元/湿吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "印尼镍矿开工天数（天/季度）", "unit": "天", "freq": "季度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "印尼镍精矿TC（美元/吨干矿）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "印度锌矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内压铸合金产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内氧化锌产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内电池级锌产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内电锌进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内硅矿月产量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内硅矿月加工费TC（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内精炼锡检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内锂盐检修量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内锌精炼产能（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内锌精炼检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内锌精炼进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "国内镀锌板产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "多晶硅下游订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "多晶硅冶炼成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "工业硅下游订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "工业硅冶炼厂检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "工业硅能源成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "工业硅进口盈亏（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "新喀里多尼亚镍矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "新喀里多尼亚镍矿开工天数（天/季度）", "unit": "天", "freq": "季度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "新喀里多尼亚镍精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "月差（近月-远月", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "沪铝主力价格", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "海外发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "海外精炼锡产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "海外精炼锡产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "澳大利亚锌矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "澳大利亚镍矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "现金成本时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "现金成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "电池级镍回收量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "电解镍出口盈亏（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "电解镍现货价格、镍生铁NPI现货价格、高冰镍现货价格", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "电解镍进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "电镀镍排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "秘鲁锌矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "缅甸锡矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "缅甸锡矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "菲律宾镍矿开工天数（天/季度）", "unit": "天", "freq": "季度", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "菲律宾镍精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "菲律宾镍精矿TC（美元/吨干矿）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "进口依赖度（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "进口费用（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "金属硅进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "锡精矿价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "锡锭现货价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "镍价（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "镍精矿进口总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "镍精矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "高冰镍再生量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "高冰镍成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 2, "note": ""},
{"name": "2", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "4", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "6", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "8", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "9", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "A00现货价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "A00铝现货均价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COME", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX Copper活跃合约", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX工业硅收盘价（美元/磅）", "unit": "美元/磅", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX工业硅现货升贴水（美元/磅）", "unit": "美元/磅", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX活跃价折算美元/吨相对LME 3M溢价", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX锂价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX锌收盘价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX锡期货收盘价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "COMEX镍期货收盘价（美元/磅）", "unit": "美元/磅", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Cancelled warrants", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Electrolytic nickel production", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME Copper Cash/3M", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME warranted stocks", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME-approved warehouses", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME工业硅3个月期货收盘价（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME工业硅现货升贴水（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME工业硅现金价格（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME锂价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME锡期货收盘价时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME锡期限结构时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME锡期限结构（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME锡现货现金价时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME锡近远月价差（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍3个月期货价格（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍升贴水0-3（LME Nickel Premium/Discount 0-3）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍月差（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍现货价格（美元/吨）、LME镍3个月期货价格（美元/吨）、升贴水（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍现金-3个月月差", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍现金价格（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍现金价格（美元/吨）、LME镍3个月期货价格（美元/吨）、现金-3个月月差（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "LME镍近月-远月价差（美元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Matte nickel production", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Mysteel进口镍在途量:分国别", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Nickel concentrate TC", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Nickel sulfate production", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Recycled nickel production", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "Refined nickel production", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "SHFE/LME比价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "SMM 1#电解铜升贴水", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "SMM EQ-A铜升贴水", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "SMM国内铝水比例", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "SMM进口镍在途量:分国别", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "三元电池排产", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "三元电池排产、沪镍主力合约收盘价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "不锈钢终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "不锈钢表观消费量、三元电池排产", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "不锈钢表观消费量、沪镍主力合约收盘价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中位成本", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国未锻轧铝及铝材月度出口量", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国未锻轧铝及铝材月度进口量", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国氧化铝进口/出口/净进口", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国硅矿月产能（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国硅矿月再生产量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国硅矿月加工费TC（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国硅矿月进口总量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国硅矿月进口量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国铝制品月度出口量", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "中国镍矿到港量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "云南镍矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "云南镍矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "云南镍矿开工天数（天/月）", "unit": "天", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "云南镍矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "亚洲锂矿产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "价差（电解镍-NPI", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "估算辅料成本", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯锡矿进口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯锡矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯锡精矿产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯锡精矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯锡精矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯锡锭出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "俄罗斯锡锭进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "具体执行", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生氢氧化锂产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生碳酸锂产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锌产能（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锌检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锌进口量分国别（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锌进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锡产能利用率时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锡价格时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锡开工天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锡检修量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锡检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生锡进口量分国别时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "再生镍-电解镍产量比（倍）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "冰晶石现货价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "冶炼产能（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "冶炼检修量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "几内亚铝土矿CIF/FOB", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "出口金额、出口均价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "分原料硫酸镍利润（元/镍吨）", "unit": "吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "分原料硫酸镍完全成本（元/镍吨）", "unit": "吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "删除图数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "前20名席位轮动方向（多头增加/空头增加/双增/双减）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "前20名持仓集中度（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "前20多头净持仓（手）", "unit": "手", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "前20席位总持仓（手）", "unit": "手", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "前20空头净持仓（手）", "unit": "手", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "动力煤价格指数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "动力电池废料进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "动力电池终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "升水铜升贴水", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "升贴水（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "单吨氧化铝成本", "unit": "吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "单吨阳极成本", "unit": "吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "南美进口量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "南美锂矿产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "南非锌矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "南非锌矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "南非锌矿再生产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "南非锌矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "南非锌精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼-菲律宾进口量比（倍）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼再生锡产能（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼再生锡产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼再生锡进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼电子级锡出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼电解镍进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼进口在途量、菲律宾进口在途量、新喀里多尼亚进口在途量", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼进口在途量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼锡矿进口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼锡矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼锡精矿产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼锡精矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼锡锭进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍生铁/NPI发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍生铁/NPI对华发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿RKAB配额", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿产能（万吨/年）", "unit": "万吨", "freq": "年度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿对华发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍矿配额利用率", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍精炼产能（万吨/年）", "unit": "万吨", "freq": "年度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼镍铁冶炼项目样本投产条数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼需求增速（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼高冰镍完全成本、印尼高冰镍现金成本、印尼高冰镍利润", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼高冰镍完全成本（美元/镍吨）、印尼高冰镍现金成本（美元/镍吨）", "unit": "吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印尼高冰镍完全成本：利润（周度）", "unit": "待确认", "freq": "周度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印度锌矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印度锌矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印度锌矿再生产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印度锌矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "印度锌精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "原图数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "原料成本时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "发运天数时序图", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "四川镍矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "四川镍矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "四川镍矿开工天数（天/月）", "unit": "天", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "四川镍矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "回收企业产能（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "回收企业产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "回收企业开工天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "回收企业检修量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国产铝土矿价格", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内再生锌进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内压铸合金出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内氧化锌出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内电池级锌订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内电锌关税税率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内电锌净进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内电锌出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内电锌进出口金额（亿美元）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内电锌进口量分国别（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内电锌进口量总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内硅矿月产能（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内硅矿月检修量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内硅矿月沪伦比（倍）", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内硅矿月进口盈亏（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内精炼锡产能利用率时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内精炼锡产能时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内精炼锡产能（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内精炼锡产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内精炼锡开工天数时序图", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内精炼锡开工天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内精炼锡检修量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锂盐产能（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锂盐精炼产能（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锂矿产能（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锂矿产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锂矿检修量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼日度利润（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼日度原料成本（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼日度现金成本（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼日度电价（元/度）", "unit": "待确认", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月天然气成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月柴油成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月煤炭成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月电价（元/度）", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月硫酸成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月能源成本分结构（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼月能源成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌冶炼需求增速（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌制品出口量分国别（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌制品出口量总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌制品出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌制品出口金额（亿美元）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌原料成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌合金出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌现金成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌电价（元/度）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌电解成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌电解日度利润（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌电解月成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌矿产能（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌矿进口量分国别（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌精炼开工天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌精炼日度产量（吨）", "unit": "吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌精炼进口量分国别（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌精矿关税税率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌精矿发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌精矿月成本（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌精矿进口量总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锌锭消费量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锡矿产能利用率时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锡矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内锡矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内镀锌板/热镀锌消费量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内镀锌板出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内镀锌板排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内镀锌板订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内镍矿-精炼产量比（倍）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内镍矿进口依赖度（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "国内需求增速（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅下游排产计划量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅下游终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅下游采购量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅下游预付款（亿元）", "unit": "亿元", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅再生月产能（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅净出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅制品净出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅制品出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅海外发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅现金利润（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "多晶硅精炼月检修量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅TC加工费（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅下游排产计划量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅下游消费增速（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅下游终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅下游采购量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅下游预付款（亿元）", "unit": "亿元", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅出口关税税率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅出口发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅制品出口关税税率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅制品出口发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅加工费（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅原料成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅排产计划量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅期货多空持仓比（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅期货日度多空持仓比（%）", "unit": "%", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅期货近月合约收盘价（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅期货远月合约收盘价（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅沪伦比（倍）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅海外发运分国别量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅海外发运发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅海外发运发运金额（亿元）", "unit": "亿元", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅海外发运总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅海外发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅现货价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅现货升贴水（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅现金利润（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅矿端TC加工费（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅精炼月开工天数（天）", "unit": "天", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅进口关税税率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业硅进口发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "工业级碳酸锂利润（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "巴西硅矿月产能利用率（%）", "unit": "%", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "巴西硅矿月产能（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "巴西硅矿月产量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "巴西硅矿月再生产量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "巴西硅矿月加工费TC（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "巴西硅矿月进口量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "平水铜升贴水", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "总进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "排产计划时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚电解镍进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚进口在途量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚镍矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚镍矿产能（万吨/年）", "unit": "万吨", "freq": "年度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚镍矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚镍矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚镍精炼产能（万吨/年）", "unit": "万吨", "freq": "年度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新喀里多尼亚镍精矿TC（美元/吨干矿）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "新增图数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "日度分原料硫酸镍完全成本（元/镍吨）", "unit": "吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "最终图数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "月差（近月-远月）", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "氟化铝现货价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "氧化铝现货均价/指数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪锡前20净持仓时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪锡多空持仓比时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪锡期限结构时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪锡期限结构（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪锡近远月价差时序图", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪锡近远月价差（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍3个月期货价格（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍主力合约价格（元/吨）、LME镍现货价格（美元/吨）、汇率（USD/CNY）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍主力合约价格（元/吨）、LME镍现货价格（美元/吨）、汇率（USD/CNY）、进口费用（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍主力合约前20名持仓总量（手）", "unit": "手", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍前20名多空持仓比", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍前20名席位轮动方向", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍前20名持仓集中度", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍月差", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍现金-3个月月差", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍现金价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍现金价格（元/吨）、沪镍3个月期货价格（元/吨）、现金-3个月月差（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍近月-远月价差（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍近月-远月价差（元/吨）、LME镍近月-远月价差（美元/吨）、汇率（USD/CNY）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍近月合约价格、沪镍远月合约价格、月差", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍近月合约价格（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "沪镍远月合约价格", "unit": "待确认", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外发运量与发运天数时序图", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外发运量分国别时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外发运量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华发运总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华电锌发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华锌发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华锌发运盈亏（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华锌发运量分国别（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华锌发运量总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华锌发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外对华锌精矿发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外检修量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外硅矿季度产能利用率（%）", "unit": "%", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外硅矿季度产能（万吨）", "unit": "万吨", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外硅矿季度产量（万吨）", "unit": "万吨", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外硅矿季度再生产量（万吨）", "unit": "万吨", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外硅矿季度加工费TC（元/吨）", "unit": "元/吨", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外硅矿季度检修量（万吨）", "unit": "万吨", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外硅矿季度进口量（万吨）", "unit": "万吨", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外精炼产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外精炼锡检修量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外精炼锡检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外进口量分国别（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外进口量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锂矿产能分国别（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锂矿产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锂矿出口量分国别（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锂矿进口量分国别（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌矿产能（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌矿再生产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌矿进口量分国别（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锌精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锡矿产能利用率时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锡矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锡矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锡矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锡精矿产量总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "海外锡精矿产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "湿法铜升贴水", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚进口量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锂矿产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锌矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锌矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锌矿再生产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锌矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锌精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锡矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锡精矿产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚锡精矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚镍矿产能（万吨/年）", "unit": "万吨", "freq": "年度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚镍矿开工天数（天/季度）", "unit": "天", "freq": "季度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "澳大利亚镍精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡/锡化工终端产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡/锡焊料排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡/锡焊料终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡/锡焊料终端订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡/锡焊料订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡终端产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "焊锡订单量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "煤价（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "煤沥青价格", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "现金-3个月月差（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "现金价（美元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "甘肃镍矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "甘肃镍矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "甘肃镍矿开工天数（天/月）", "unit": "天", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "甘肃镍矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电价时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电子级锡出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电子级锡终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电子级锡订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电池级碳酸锂利润（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电池级镍制品出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电池级镍制品出口金额（亿美元）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解铝行业加权平均完全成本", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解锌现金成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍冶炼完全成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍完全成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍对华发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍日度利润（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍日度利润（元/吨）、沪镍主力合约收盘价（元/吨）、电解镍现金成本（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电解镍检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电镀镍制品出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电镀镍制品出口金额（亿美元）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电镀镍终端消费量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "电镀镍订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "盐湖提锂利润（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "盐湖提锂精炼产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "矿-精炼产量比（倍）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "秘鲁锌矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "秘鲁锌矿产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "秘鲁锌矿再生产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "秘鲁锌矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "秘鲁锌精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "精炼锡净进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "精炼镍日度利润（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "精炼镍检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "精炼镍进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "终端排产计划（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "终端消费增速（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸再生锡产能（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸再生锡产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸再生锡进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸电子级锡出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡矿产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡矿价格时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡矿价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡矿进口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡精矿产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡精矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡锭出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸锡锭进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "缅甸需求增速（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "美国硅矿月产能（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "美国硅矿月产量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "美国硅矿月再生产量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "美国硅矿月加工费TC（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "美国硅矿月进口量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "能源/原料成本总量（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "能源成本时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "船货在途量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾电解镍进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾矿-精炼产量比（倍）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾至中国海运费（美元/湿吨）", "unit": "美元/湿吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾进口在途量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿CIF价格（美元/湿吨）", "unit": "美元/湿吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿CIF价格（美元/湿吨）、菲律宾镍矿FOB价格（美元/湿吨）", "unit": "美元/湿吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿产能利用率（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿产能（万吨/年）", "unit": "万吨", "freq": "年度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿对华发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿离港量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "菲律宾镍精炼产能（万吨/年）", "unit": "万吨", "freq": "年度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "行业理论盈利", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "进口在途量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅下游终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅再生月产能（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅冶炼成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅净出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅净进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅制品净出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅制品出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅海外发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "金属硅精炼月检修量（万吨）", "unit": "万吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "铝价指数", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "铝制结构件/容器/车轮/绞线出口量", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "铝板带/铝箔/铝挤压材出口量", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂云母/锂辉石利润（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂云母精炼产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂云母进口量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂矿进口总量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂矿进口量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂辉石产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂辉石精炼产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锂辉石进口量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锌月差（元/吨）", "unit": "元/吨", "freq": "月度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锌矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锌精矿成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡制品出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡化工出口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡化工出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡化工终端产量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡化工终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡化工订单量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡焊料/焊锡与锡化工出口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡焊料/焊锡出口量分国别时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡焊料/焊锡出口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡焊料/焊锡出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡矿总进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡精矿与再生锡进口量时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡精矿价格时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡精矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡锭净进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡锭现货价格时序图", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "锡锭进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍冶炼成本总量（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍冶炼成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍冶炼日度利润（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍制品出口总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍原料进口总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍合金出口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍合金出口金额（亿美元）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍合金终端产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍现货价格（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍生铁/NPI成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍生铁/NPI进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍矿CIF价格（美元/湿吨）、镍矿FOB价格（美元/湿吨）", "unit": "美元/湿吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍矿进口量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍精炼产量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍精炼金属进口总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍精矿进口到港量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍终端消费总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁RKEF成本（元/镍点）", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁一体化利润（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁一体化成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁一体化成本（元/吨）、镍精矿TC（美元/吨干矿）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁一体化日度利润（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁一体化日度利润（元/吨）、镍矿成本（元/吨）、TC（美元/吨干矿）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁完全成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍铁检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "镍需求先行指标总量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "需求增速（%）", "unit": "%", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "非洲进口量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "非洲锂矿产量（万吨LCE）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "预焙阳极价格", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "预焙阳极均价", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍产量", "unit": "待确认", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍发运天数（天）", "unit": "天", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍完全成本（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍对华发运量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍成本（元/吨）、镍矿成本（元/吨）、加工费（元/吨）", "unit": "元/吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍日度利润（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍日度利润（元/吨）、镍矿成本（元/吨）、加工费（元/吨）", "unit": "元/吨", "freq": "日度", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "高冰镍检修量（万吨）", "unit": "万吨", "freq": "待确认", "source": "同花顺问财", "ref_count": 1, "note": ""},
{"name": "河南进口矿现金流利润", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "工业硅开炉情况", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "沪铝25Δ", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "沪铜25Δ", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "沪铝IV", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "电解铝：社库+厂库（农历）", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝棒-社库+厂库（农历）", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝板带箔-原料库存", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝板带箔-原料库存天数", "unit": "天", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "未锻轧铝进口量", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "废铝进口总量", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝材进口量-板带", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝材进口量-铝箔", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝水比例", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "出口-铝制品", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "出口-铝材-型材条杆", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "出口-铝材-板带箔", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝材出口-中东", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝材出口-EU-27", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝制品出口-EU-27", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝制品出口-北美", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝制品出口-东南亚", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝制品出口-中东", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "铝终端消费", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "乘用车批发销量（内外销）-当月值", "unit": "待确认", "freq": "月度", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "乘用车零售量（内销）-当月值", "unit": "待确认", "freq": "月度", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "乘用车零售量（内销）-累计值", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "乘用车出口量-当月值", "unit": "待确认", "freq": "月度", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "乘用车出口量-累计值", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "新能源乘用车出口量-当月值", "unit": "待确认", "freq": "月度", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "新能源乘用车出口量-累计值", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "亏损企业比例", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "汽车制造产成品周转天数", "unit": "天", "freq": "周度", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "光伏组件净出口", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "电网建设累计同比", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "同基准下有色库存相对比值对比", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "白色家电消费", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "镍板库存", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "不同镍产品折镍价", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "MHP镍折扣系数", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "MHP钴折扣系数", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "镍豆库存", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "新能源车销量", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "菲律宾镍矿价格（1.5%）", "unit": "%", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
{"name": "菲律宾镍矿价格：不同品味", "unit": "待确认", "freq": "待确认", "source": "PDF周报", "ref_count": 0, "note": ""},
]
```

---

## 注意事项

1. **B2 重建基于 heuristic 清洗**: 清洗规则基于启发式过滤，可能存在漏判或误判。建议人工审核被排除的条目。
2. **B2 与 THS 匹配使用归一化名称**: 去除单位后缀后比较，可能遗漏语义相同但命名差异较大的指标。
3. **fuzzy match 已应用**: 对长度 >=5 的 B2 标题，检查 v1 中是否有包含关系。仅保留无模糊匹配的条目。
4. **参考引用次数仅 THS 有效**: B2 独有指标的 reference_count=0 (PDF 无模板引用计数概念)。
5. **未调用 zhiji API**: 本脚本仅做文本分类与合并，不涉及任何 API 调用。
6. **未修改 indicators_v1**: 所有输入文件只读，输出仅为草稿。
7. **indicators_v1 版本**: 基于当前 indicators_v1.json (v3.50-p3fix) 的指标名集合。

## 数据血缘

| 输入 | 路径 | 状态 |
|------|------|------|
| B2 原始文件 | `D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\pdf_extract\missing_classify.csv` | 已读取 (148 行) |
| THS 分类文件 | `D:\DSH_WORK\github工作\analysis\e2e_output\v85\ths_check\ths_missing_classify.csv` | 已读取 (CAT_A=693) |
| indicators_v1 | `D:\DSH_WORK\framework-tree\data\indicators_v1.json` | 已读取 (1239 指标名) |

## 输出产物

| 文件 | 说明 |
|------|------|
| `b2_missing_preview_rebuild.csv` | B2 重建待补清单 (含有效/已存在/排除) |
| `full_merged_A_raw_missing.csv` | PDF+同花顺合并去重总清单 |
| `full_merged_A_raw_draft.md` | 本文件 — indicators_v1 录入草稿 |
