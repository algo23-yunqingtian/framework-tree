# indicators_v1 录入草稿

- 草稿时间: 自动生成
- 合并来源: 同花顺 CAT_A 原始缺失指标 + PDF周报 B2 待补指标
- 合并后去重总数: **693**

> B2_MISSING_FILE_NOT_FOUND: b2_missing_preview.csv not found in repository. Prior task DSH-B_B2_MISSING_INDICATOR_PREP_TASK outputs missing. Merge contains only THS CAT_A raw missing indicators.

---

## 来源统计

| 来源 | 数量 | 占比 |
|------|------|------|
| 同花顺模板 | 693 | 100.0% |

## 按品种统计

| 品种 | 指标数 |
|------|--------|
| NI | 344 |
| SN | 171 |
| ZN | 135 |
| SI | 103 |
| LI | 51 |
| AL | 28 |
| CU | 12 |

---

## 录入草稿清单

> 以下指标建议作为 indicators_v1 新增条目。
> 字段说明:
> - `name`: 指标中文名（取自同花顺原始名称）
> - `unit`: 单位（从指标名中提取）
> - `freq`: 建议频率（需根据数据源确认）
> - `source`: 来源标注
> - `ref_count`: 同花顺引用次数

```json
{
  "indicators": [
{
    "name": "镍精矿TC（美元/吨干矿）",
    "unit": "美元/吨干矿",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 18,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.5;THS-NI-3.2.1;THS-NI-3.2.2;THS-NI-3.2.3"
},
{
    "name": "沪伦比（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 12,
    "sample_templates": "THS-LI-2.3;THS-ZN-2.1;THS-ZN-2.2;THS-ZN-2.3;THS-ZN-2.4"
},
{
    "name": "国内锌精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 7,
    "sample_templates": "THS-ZN-3.2.1;THS-ZN-3.2.2;THS-ZN-3.2.3;THS-ZN-5.1;THS-ZN-5.3"
},
{
    "name": "加工费（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 6,
    "sample_templates": "THS-NI-7.1;THS-NI-7.2;THS-NI-7.3;THS-SN-7.1;THS-SN-7.2"
},
{
    "name": "多空持仓比（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 6,
    "sample_templates": "THS-LI-2.1;THS-LI-2.6;THS-SN-2.1;THS-SN-2.6;THS-ZN-2.1"
},
{
    "name": "汇率（USD/CNY）",
    "unit": "USD/CNY",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 5,
    "sample_templates": "THS-NI-2.1;THS-NI-2.2;THS-NI-2.3;THS-NI-2.4;THS-NI-2.6"
},
{
    "name": "电价（元/度）",
    "unit": "元/度",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 5,
    "sample_templates": "THS-NI-7.1;THS-NI-7.3;THS-SN-7.1;THS-SN-7.2;THS-SN-7.3"
},
{
    "name": "电解镍产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 4,
    "sample_templates": "THS-NI-3.1.3;THS-NI-3.2;THS-NI-3.2.1;THS-NI-3.2.3"
},
{
    "name": "LME锡期货收盘价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-SN-2.3;THS-SN-2.4;THS-SN-2.5"
},
{
    "name": "LME镍现货价格（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-2.1;THS-NI-2.2;THS-NI-2.3"
},
{
    "name": "TC（美元/吨干矿）",
    "unit": "美元/吨干矿",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-7.1;THS-NI-7.2;THS-NI-7.3"
},
{
    "name": "关税税率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-SN-6.2;THS-SN-6.3;THS-SN-6.4"
},
{
    "name": "动力电池排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-5.1;THS-NI-5.2;THS-NI-5.3"
},
{
    "name": "印尼镍精矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.4;THS-NI-3.1.5"
},
{
    "name": "原料成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-SN-7.1;THS-SN-7.2;THS-SN-7.3"
},
{
    "name": "国内镍精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.3;THS-NI-3.1.4"
},
{
    "name": "沪镍主力合约价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-2.1;THS-NI-2.2;THS-NI-2.3"
},
{
    "name": "电解镍现货价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-2.2;THS-NI-2.4;THS-NI-2.5"
},
{
    "name": "电解镍现金成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-7.1;THS-NI-7.2;THS-NI-7.3"
},
{
    "name": "能源成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-SN-7.1;THS-SN-7.2;THS-SN-7.3"
},
{
    "name": "菲律宾镍矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.1;THS-NI-3.1.2"
},
{
    "name": "菲律宾镍精矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.4;THS-NI-3.1.5"
},
{
    "name": "进出口金额（亿元）",
    "unit": "亿元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-SN-6.2;THS-SN-6.3;THS-SN-6.4"
},
{
    "name": "镍合金排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-5.1;THS-NI-5.2;THS-NI-5.3"
},
{
    "name": "镍生铁NPI现货价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-2.2;THS-NI-2.4;THS-NI-2.5"
},
{
    "name": "镍矿成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-7.1;THS-NI-7.2;THS-NI-7.3"
},
{
    "name": "镍铁产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-3.1.3;THS-NI-3.2;THS-NI-3.2.1"
},
{
    "name": "高冰镍现货价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 3,
    "sample_templates": "THS-NI-2.2;THS-NI-2.4;THS-NI-2.5"
},
{
    "name": "LME Cash-3M spread",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.2;THS-NI-2.3"
},
{
    "name": "LME Nickel Stock",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-4.2;THS-NI-4.3"
},
{
    "name": "LME工业硅收盘价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-2.3;THS-SI-3.1.4"
},
{
    "name": "LME锌收盘价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-2.3;THS-ZN-5.3"
},
{
    "name": "LME镍近月合约价格（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.3;THS-NI-2.4"
},
{
    "name": "LME镍远月合约价格（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.3;THS-NI-2.4"
},
{
    "name": "SMM1#电解镍价格、SMM8-12%高镍生铁价格、SMM高冰镍价格",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.2;THS-NI-2.4"
},
{
    "name": "SMM1#电解镍升贴水",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.1;THS-NI-2.2"
},
{
    "name": "不锈钢废料再生镍量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.2;THS-NI-3.2.3"
},
{
    "name": "不锈钢排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-5.1;THS-NI-5.3"
},
{
    "name": "中国从印尼进口镍精矿量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.4"
},
{
    "name": "中国从新喀里多尼亚进口镍精矿量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.4"
},
{
    "name": "中国从菲律宾进口镍精矿量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.4"
},
{
    "name": "元/吨）",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.2;THS-NI-2.4"
},
{
    "name": "再生锡价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-2.5;THS-SN-7.3"
},
{
    "name": "再生锡进口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-3.2.3;THS-SN-6.1"
},
{
    "name": "再生锡进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-3.2.3;THS-SN-6.1"
},
{
    "name": "再生镍产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.2;THS-NI-3.2.3"
},
{
    "name": "冶炼成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-7.1;THS-SN-7.2"
},
{
    "name": "南非锌矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-3.1.2;THS-ZN-3.1.4"
},
{
    "name": "印尼镍矿HPM基准价（美元/湿吨）",
    "unit": "美元/湿吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1;THS-NI-7.3"
},
{
    "name": "印尼镍矿开工天数（天/季度）",
    "unit": "天/季度",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.2"
},
{
    "name": "印尼镍精矿TC（美元/吨干矿）",
    "unit": "美元/吨干矿",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.5"
},
{
    "name": "印度锌矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-3.1.2;THS-ZN-3.1.4"
},
{
    "name": "发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-6.1;THS-SN-6.4"
},
{
    "name": "国内压铸合金产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-5.2;THS-ZN-6.3"
},
{
    "name": "国内氧化锌产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-5.2;THS-ZN-6.3"
},
{
    "name": "国内电池级锌产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-5.2;THS-ZN-5.3"
},
{
    "name": "国内电锌进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-6.2;THS-ZN-6.4"
},
{
    "name": "国内硅矿月产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-3.1.3;THS-SI-3.1.4"
},
{
    "name": "国内硅矿月加工费TC（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-3.1.3;THS-SI-3.1.4"
},
{
    "name": "国内精炼锡检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-3.2.1;THS-SN-3.2.2"
},
{
    "name": "国内锂盐检修量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-LI-3.2.1;THS-LI-3.2.2"
},
{
    "name": "国内锌精炼产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-3.2.1;THS-ZN-3.2.2"
},
{
    "name": "国内锌精炼检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-3.2.1;THS-ZN-3.2.2"
},
{
    "name": "国内锌精炼进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-3.2.1;THS-ZN-3.2.2"
},
{
    "name": "国内镀锌板产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-5.2;THS-ZN-6.3"
},
{
    "name": "多晶硅下游订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-5.2;THS-SI-5.3"
},
{
    "name": "多晶硅冶炼成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-2.5;THS-SI-7.1"
},
{
    "name": "工业硅下游订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-5.2;THS-SI-5.3"
},
{
    "name": "工业硅冶炼厂检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-3.1.5;THS-SI-3.2.4"
},
{
    "name": "工业硅能源成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-7.1;THS-SI-7.2"
},
{
    "name": "工业硅进口盈亏（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-2.2;THS-SI-2.3"
},
{
    "name": "排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-5.1;THS-SN-5.3"
},
{
    "name": "新喀里多尼亚镍矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.2"
},
{
    "name": "新喀里多尼亚镍矿开工天数（天/季度）",
    "unit": "天/季度",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.2"
},
{
    "name": "新喀里多尼亚镍精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.2"
},
{
    "name": "月差（近月-远月",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.3;THS-NI-2.4"
},
{
    "name": "沪铝主力价格",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-AL-4.1;THS-AL-4.2"
},
{
    "name": "海外发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-6.1;THS-SN-6.4"
},
{
    "name": "海外精炼锡产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-3.1.1;THS-SN-3.2.1"
},
{
    "name": "海外精炼锡产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-3.1.1;THS-SN-3.2.1"
},
{
    "name": "澳大利亚锌矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-3.1.2;THS-ZN-3.1.4"
},
{
    "name": "澳大利亚镍矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.2"
},
{
    "name": "现金成本时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-7.1;THS-SN-7.2"
},
{
    "name": "现金成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-7.1;THS-SN-7.2"
},
{
    "name": "电池级镍回收量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.2;THS-NI-3.2.3"
},
{
    "name": "电解镍出口盈亏（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-6.2;THS-NI-7.2"
},
{
    "name": "电解镍现货价格、镍生铁NPI现货价格、高冰镍现货价格",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.2;THS-NI-2.4"
},
{
    "name": "电解镍现货价格（元/吨）、镍生铁NPI现货价格（元/吨）、高冰镍现货价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.2;THS-NI-2.4"
},
{
    "name": "电解镍进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-6.1;THS-NI-6.2"
},
{
    "name": "电镀镍排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-5.1;THS-NI-5.2"
},
{
    "name": "秘鲁锌矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-ZN-3.1.2;THS-ZN-3.1.4"
},
{
    "name": "终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-5.1;THS-SN-5.2"
},
{
    "name": "缅甸锡矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-3.1.1;THS-SN-3.1.2"
},
{
    "name": "缅甸锡矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-3.1.4;THS-SN-3.1.5"
},
{
    "name": "美元/吨）",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.3;THS-NI-2.4"
},
{
    "name": "菲律宾镍矿开工天数（天/季度）",
    "unit": "天/季度",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.2"
},
{
    "name": "菲律宾镍精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.1;THS-NI-3.1.2"
},
{
    "name": "菲律宾镍精矿TC（美元/吨干矿）",
    "unit": "美元/吨干矿",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.5"
},
{
    "name": "进口依赖度（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.3;THS-NI-3.1.4"
},
{
    "name": "进口费用（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-2.2;THS-NI-2.3"
},
{
    "name": "金属硅进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SI-6.1;THS-SI-6.4"
},
{
    "name": "锡精矿价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-2.5;THS-SN-7.3"
},
{
    "name": "锡锭现货价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-SN-2.2;THS-SN-2.5"
},
{
    "name": "镍价（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-7.1;THS-NI-7.2"
},
{
    "name": "镍精矿进口总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1;THS-NI-3.1.4"
},
{
    "name": "镍精矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.1.3;THS-NI-3.1.4"
},
{
    "name": "高冰镍再生量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-3.2;THS-NI-3.2.3"
},
{
    "name": "高冰镍成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 2,
    "sample_templates": "THS-NI-7.1;THS-NI-7.3"
},
{
    "name": "2",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "4",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "6",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "8",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "9",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "A00现货价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.3"
},
{
    "name": "A00铝现货均价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.1"
},
{
    "name": "COME",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "COMEX Copper活跃合约",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "COMEX工业硅收盘价（美元/磅）",
    "unit": "美元/磅",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.3"
},
{
    "name": "COMEX工业硅现货升贴水（美元/磅）",
    "unit": "美元/磅",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.3"
},
{
    "name": "COMEX活跃价折算美元/吨相对LME 3M溢价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "COMEX锂价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.3"
},
{
    "name": "COMEX锌收盘价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-2.3"
},
{
    "name": "COMEX锡期货收盘价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.3"
},
{
    "name": "COMEX镍期货收盘价（美元/磅）",
    "unit": "美元/磅",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "Cancelled warrants",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-4.4"
},
{
    "name": "Electrolytic nickel production",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "LME Copper Cash/3M",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "LME Nickel Stock（吨）",
    "unit": "吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.1"
},
{
    "name": "LME warranted stocks",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "LME-approved warehouses",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-4.4"
},
{
    "name": "LME工业硅3个月期货收盘价（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.3"
},
{
    "name": "LME工业硅现货升贴水（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.3"
},
{
    "name": "LME工业硅现金价格（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.3"
},
{
    "name": "LME锂价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.3"
},
{
    "name": "LME锡期货收盘价时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.3"
},
{
    "name": "LME锡期限结构时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.4"
},
{
    "name": "LME锡期限结构（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.4"
},
{
    "name": "LME锡现货现金价时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.3"
},
{
    "name": "LME锡近远月价差（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.4"
},
{
    "name": "LME镍3个月期货价格（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "LME镍升贴水0-3（LME Nickel Premium/Discount 0-3）",
    "unit": "LME Nickel Premium/Discount 0-3",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.1"
},
{
    "name": "LME镍月差（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "LME镍现货价格（美元/吨）、LME镍3个月期货价格（美元/吨）、升贴水（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.2"
},
{
    "name": "LME镍现金-3个月月差",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "LME镍现金价格（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "LME镍现金价格（美元/吨）、LME镍3个月期货价格（美元/吨）、现金-3个月月差（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "LME镍近月-远月价差（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "Matte nickel production",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "Mysteel进口镍在途量:分国别",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "Nickel concentrate TC",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "Nickel sulfate production",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "Recycled nickel production",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "Refined nickel production",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "SHFE/LME比价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "SMM 1#电解铜升贴水",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "SMM EQ-A铜升贴水",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "SMM国内铝水比例",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-4.3"
},
{
    "name": "SMM进口镍在途量:分国别",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "三元电池排产",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "三元电池排产、沪镍主力合约收盘价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "不锈钢废料再生镍量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "不锈钢终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "不锈钢表观消费量、三元电池排产",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "不锈钢表观消费量、沪镍主力合约收盘价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "中位成本",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.1"
},
{
    "name": "中国未锻轧铝及铝材月度出口量",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-6.2"
},
{
    "name": "中国未锻轧铝及铝材月度进口量",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-6.2"
},
{
    "name": "中国氧化铝进口/出口/净进口",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-6.1"
},
{
    "name": "中国硅矿月产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "中国硅矿月再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "中国硅矿月加工费TC（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "中国硅矿月进口总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.4"
},
{
    "name": "中国硅矿月进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "中国铝制品月度出口量",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-6.3"
},
{
    "name": "中国镍矿到港量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "云南镍矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "云南镍矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "云南镍矿开工天数（天/月）",
    "unit": "天/月",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "云南镍矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "亚洲锂矿产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.2"
},
{
    "name": "价差（电解镍-NPI",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.2"
},
{
    "name": "估算辅料成本",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.2"
},
{
    "name": "俄罗斯发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.4"
},
{
    "name": "俄罗斯锡矿进口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "俄罗斯锡矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "俄罗斯锡精矿产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.2"
},
{
    "name": "俄罗斯锡精矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.2"
},
{
    "name": "俄罗斯锡精矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "俄罗斯锡锭出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.2"
},
{
    "name": "俄罗斯锡锭进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.2"
},
{
    "name": "具体执行",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "再生氢氧化锂产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.3"
},
{
    "name": "再生碳酸锂产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.3"
},
{
    "name": "再生锌产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.2.3"
},
{
    "name": "再生锌检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.2.3"
},
{
    "name": "再生锌进口量分国别（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.2.3"
},
{
    "name": "再生锌进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.2.3"
},
{
    "name": "再生锡产能利用率时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "再生锡价格时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "再生锡开工天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "再生锡检修量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "再生锡检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "再生锡进口量分国别时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "再生镍-电解镍产量比（倍）",
    "unit": "倍",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.3"
},
{
    "name": "冰晶石现货价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.2"
},
{
    "name": "冶炼产能（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.4"
},
{
    "name": "冶炼检修量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.4"
},
{
    "name": "几内亚铝土矿CIF/FOB",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.3"
},
{
    "name": "出口金额、出口均价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-6.3"
},
{
    "name": "分原料硫酸镍利润（元/镍吨）",
    "unit": "元/镍吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "分原料硫酸镍利润（元/镍吨）（MHP/高冰镍/镍豆）",
    "unit": "元/镍吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "分原料硫酸镍完全成本（元/镍吨）",
    "unit": "元/镍吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "删除图数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "前20名席位轮动方向（多头增加/空头增加/双增/双减）",
    "unit": "多头增加/空头增加/双增/双减",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.6"
},
{
    "name": "前20名持仓集中度（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.6"
},
{
    "name": "前20多头净持仓（手）",
    "unit": "手",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.6"
},
{
    "name": "前20席位总持仓（手）",
    "unit": "手",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.6"
},
{
    "name": "前20空头净持仓（手）",
    "unit": "手",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.6"
},
{
    "name": "动力煤价格指数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.3"
},
{
    "name": "动力电池废料进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.3"
},
{
    "name": "动力电池终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "升水铜升贴水",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "升贴水（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "单吨氧化铝成本",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.2"
},
{
    "name": "单吨阳极成本",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.2"
},
{
    "name": "南美进口量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.4"
},
{
    "name": "南美锂矿产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.2"
},
{
    "name": "南非锌矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "南非锌矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "南非锌矿再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "南非锌矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "南非锌精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "印尼-菲律宾进口量比（倍）",
    "unit": "倍",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.4"
},
{
    "name": "印尼再生锡产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "印尼再生锡产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "印尼再生锡进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "印尼发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.4"
},
{
    "name": "印尼电子级锡出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "印尼电解镍进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.2"
},
{
    "name": "印尼进口在途量、菲律宾进口在途量、新喀里多尼亚进口在途量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "印尼进口在途量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "印尼进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.4"
},
{
    "name": "印尼锡矿进口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "印尼锡矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "印尼锡精矿产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.2"
},
{
    "name": "印尼锡精矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "印尼锡锭进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.2"
},
{
    "name": "印尼镍生铁/NPI发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "印尼镍生铁/NPI对华发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "印尼镍矿HPM基准价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "印尼镍矿RKAB配额",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "印尼镍矿RKAB配额（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "印尼镍矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "印尼镍矿产能（万吨/年）",
    "unit": "万吨/年",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.2"
},
{
    "name": "印尼镍矿发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "印尼镍矿对华发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "印尼镍矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "印尼镍矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.1"
},
{
    "name": "印尼镍矿配额利用率",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "印尼镍矿配额利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "印尼镍精炼产能（万吨/年）",
    "unit": "万吨/年",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "印尼镍精矿TC",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "印尼镍铁冶炼项目样本投产条数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "印尼需求增速（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "印尼高冰镍完全成本、印尼高冰镍现金成本、印尼高冰镍利润",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.5"
},
{
    "name": "印尼高冰镍完全成本（元/吨）、印尼高冰镍现金成本（元/吨）、印尼高冰镍利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.5"
},
{
    "name": "印尼高冰镍完全成本（周度）、印尼高冰镍现金成本（周度）、印尼高冰镍利润（周度）",
    "unit": "周度",
    "freq": "weekly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.5"
},
{
    "name": "印尼高冰镍完全成本（美元/镍吨）、印尼高冰镍现金成本（美元/镍吨）",
    "unit": "美元/镍吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "印尼高冰镍完全成本：利润（周度）",
    "unit": "周度",
    "freq": "weekly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "印度锌矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "印度锌矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "印度锌矿再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "印度锌矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "印度锌精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "原图数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "原料成本时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "发运天数时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.4"
},
{
    "name": "四川镍矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "四川镍矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "四川镍矿开工天数（天/月）",
    "unit": "天/月",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "四川镍矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "回收企业产能（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.3"
},
{
    "name": "回收企业产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.3"
},
{
    "name": "回收企业开工天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.3"
},
{
    "name": "回收企业检修量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.3"
},
{
    "name": "国产铝土矿价格",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.3"
},
{
    "name": "国内再生锌进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.1"
},
{
    "name": "国内压铸合金出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内氧化锌出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内电池级锌订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.3"
},
{
    "name": "国内电锌关税税率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.2"
},
{
    "name": "国内电锌净进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.2"
},
{
    "name": "国内电锌出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.2"
},
{
    "name": "国内电锌进出口金额（亿美元）",
    "unit": "亿美元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.2"
},
{
    "name": "国内电锌进口量分国别（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.2"
},
{
    "name": "国内电锌进口量总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.2"
},
{
    "name": "国内硅矿月产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.3"
},
{
    "name": "国内硅矿月检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.3"
},
{
    "name": "国内硅矿月沪伦比（倍）",
    "unit": "倍",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.4"
},
{
    "name": "国内硅矿月进口盈亏（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.4"
},
{
    "name": "国内精炼锡产能利用率时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.1"
},
{
    "name": "国内精炼锡产能时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.2"
},
{
    "name": "国内精炼锡产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.2"
},
{
    "name": "国内精炼锡产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.1"
},
{
    "name": "国内精炼锡开工天数时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.2"
},
{
    "name": "国内精炼锡开工天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.2"
},
{
    "name": "国内精炼锡检修量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.2"
},
{
    "name": "国内锂盐产能（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.2"
},
{
    "name": "国内锂盐精炼产能（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.1"
},
{
    "name": "国内锂矿产能（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.3"
},
{
    "name": "国内锂矿产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.3"
},
{
    "name": "国内锂矿检修量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.3"
},
{
    "name": "国内锌冶炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.1"
},
{
    "name": "国内锌冶炼成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.1"
},
{
    "name": "国内锌冶炼排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.1"
},
{
    "name": "国内锌冶炼日度利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.2"
},
{
    "name": "国内锌冶炼日度原料成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.2"
},
{
    "name": "国内锌冶炼日度现金成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.2"
},
{
    "name": "国内锌冶炼日度电价（元/度）",
    "unit": "元/度",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.2"
},
{
    "name": "国内锌冶炼月天然气成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼月成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼月柴油成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼月煤炭成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼月电价（元/度）",
    "unit": "元/度",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼月硫酸成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼月能源成本分结构（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼月能源成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌冶炼订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.1"
},
{
    "name": "国内锌冶炼需求增速（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.1"
},
{
    "name": "国内锌出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.3"
},
{
    "name": "国内锌制品出口量分国别（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内锌制品出口量总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内锌制品出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内锌制品出口金额（亿美元）",
    "unit": "亿美元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内锌原料成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.1"
},
{
    "name": "国内锌合金出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内锌现金成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.1"
},
{
    "name": "国内锌电价（元/度）",
    "unit": "元/度",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.1"
},
{
    "name": "国内锌电解成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.1"
},
{
    "name": "国内锌电解日度利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.2"
},
{
    "name": "国内锌电解月成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.3"
},
{
    "name": "国内锌矿产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.3"
},
{
    "name": "国内锌矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.3"
},
{
    "name": "国内锌矿进口量分国别（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.3"
},
{
    "name": "国内锌精炼开工天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.2.2"
},
{
    "name": "国内锌精炼日度产量（吨）",
    "unit": "吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.2"
},
{
    "name": "国内锌精炼进口量分国别（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.2.1"
},
{
    "name": "国内锌精矿关税税率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.1"
},
{
    "name": "国内锌精矿发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.1"
},
{
    "name": "国内锌精矿月成本（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-7.3"
},
{
    "name": "国内锌精矿进口量总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.1"
},
{
    "name": "国内锌锭消费量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.2"
},
{
    "name": "国内锡矿产能利用率时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.3"
},
{
    "name": "国内锡矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.3"
},
{
    "name": "国内锡矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.3"
},
{
    "name": "国内镀锌板/热镀锌消费量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.2"
},
{
    "name": "国内镀锌板出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.3"
},
{
    "name": "国内镀锌板排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.3"
},
{
    "name": "国内镀锌板订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-5.3"
},
{
    "name": "国内镍矿-精炼产量比（倍）",
    "unit": "倍",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "国内镍矿进口依赖度（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "国内需求增速（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "多晶硅下游排产计划量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.3"
},
{
    "name": "多晶硅下游终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.2"
},
{
    "name": "多晶硅下游采购量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.3"
},
{
    "name": "多晶硅下游预付款（亿元）",
    "unit": "亿元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.3"
},
{
    "name": "多晶硅再生月产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.2.3"
},
{
    "name": "多晶硅净出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.2"
},
{
    "name": "多晶硅制品净出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.3"
},
{
    "name": "多晶硅制品出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.3"
},
{
    "name": "多晶硅海外发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.4"
},
{
    "name": "多晶硅现金利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-7.2"
},
{
    "name": "多晶硅精炼月检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.2.2"
},
{
    "name": "多空持仓比（多头/空头）",
    "unit": "多头/空头",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.6"
},
{
    "name": "工业硅TC加工费（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.2.4"
},
{
    "name": "工业硅下游排产计划量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.3"
},
{
    "name": "工业硅下游消费增速（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.2"
},
{
    "name": "工业硅下游终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.2"
},
{
    "name": "工业硅下游采购量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.3"
},
{
    "name": "工业硅下游预付款（亿元）",
    "unit": "亿元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.3"
},
{
    "name": "工业硅出口关税税率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.2"
},
{
    "name": "工业硅出口发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.2"
},
{
    "name": "工业硅制品出口关税税率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.3"
},
{
    "name": "工业硅制品出口发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.3"
},
{
    "name": "工业硅加工费（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-7.2"
},
{
    "name": "工业硅原料成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-7.1"
},
{
    "name": "工业硅排产计划量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.1"
},
{
    "name": "工业硅期货多空持仓比（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.6"
},
{
    "name": "工业硅期货日度多空持仓比（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.1"
},
{
    "name": "工业硅期货近月合约收盘价（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.4"
},
{
    "name": "工业硅期货远月合约收盘价（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.4"
},
{
    "name": "工业硅沪伦比（倍）",
    "unit": "倍",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.2"
},
{
    "name": "工业硅海外发运分国别量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.4"
},
{
    "name": "工业硅海外发运发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.4"
},
{
    "name": "工业硅海外发运发运金额（亿元）",
    "unit": "亿元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.4"
},
{
    "name": "工业硅海外发运总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.4"
},
{
    "name": "工业硅海外发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.4"
},
{
    "name": "工业硅现货价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.2"
},
{
    "name": "工业硅现货升贴水（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-2.2"
},
{
    "name": "工业硅现金利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-7.2"
},
{
    "name": "工业硅矿端TC加工费（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.5"
},
{
    "name": "工业硅精炼月开工天数（天）",
    "unit": "天",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.2.2"
},
{
    "name": "工业硅进口关税税率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.1"
},
{
    "name": "工业硅进口发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.1"
},
{
    "name": "工业级碳酸锂利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.5"
},
{
    "name": "巴西硅矿月产能利用率（%）",
    "unit": "%",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "巴西硅矿月产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "巴西硅矿月产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "巴西硅矿月再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "巴西硅矿月加工费TC（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "巴西硅矿月进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "平水铜升贴水",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "总进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "排产计划时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "新喀里多尼亚电解镍进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.2"
},
{
    "name": "新喀里多尼亚进口在途量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "新喀里多尼亚进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.4"
},
{
    "name": "新喀里多尼亚镍矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "新喀里多尼亚镍矿产能（万吨/年）",
    "unit": "万吨/年",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.2"
},
{
    "name": "新喀里多尼亚镍矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "新喀里多尼亚镍矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.1"
},
{
    "name": "新喀里多尼亚镍精炼产能（万吨/年）",
    "unit": "万吨/年",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "新喀里多尼亚镍精矿TC（美元/吨干矿）",
    "unit": "美元/吨干矿",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.5"
},
{
    "name": "新增图数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "日度分原料硫酸镍完全成本（元/镍吨）",
    "unit": "元/镍吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "日度分原料硫酸镍完全成本（元/镍吨）（MHP/高冰镍/镍豆）",
    "unit": "元/镍吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "最终图数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "月差（近月-远月）",
    "unit": "近月-远月",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.1"
},
{
    "name": "氟化铝现货价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.2"
},
{
    "name": "氧化铝现货均价/指数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.2"
},
{
    "name": "沪锡前20净持仓时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.6"
},
{
    "name": "沪锡多空持仓比时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.6"
},
{
    "name": "沪锡期限结构时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.4"
},
{
    "name": "沪锡期限结构（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.4"
},
{
    "name": "沪锡近远月价差时序图",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.4"
},
{
    "name": "沪锡近远月价差（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.4"
},
{
    "name": "沪镍3个月期货价格（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍主力合约价格（元/吨）、LME镍现货价格（美元/吨）、汇率（USD/CNY）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "沪镍主力合约价格（元/吨）、LME镍现货价格（美元/吨）、汇率（USD/CNY）、进口费用（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.2"
},
{
    "name": "沪镍主力合约前20名持仓总量（手）",
    "unit": "手",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.6"
},
{
    "name": "沪镍前20名多空持仓比",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.6"
},
{
    "name": "沪镍前20名席位轮动方向",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.6"
},
{
    "name": "沪镍前20名持仓集中度",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.6"
},
{
    "name": "沪镍月差",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍月差（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍现金-3个月月差",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍现金价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍现金价格（元/吨）、沪镍3个月期货价格（元/吨）、现金-3个月月差（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍近月-远月价差（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍近月-远月价差（元/吨）、LME镍近月-远月价差（美元/吨）、汇率（USD/CNY）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍近月合约价格、沪镍远月合约价格、月差",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.1"
},
{
    "name": "沪镍近月合约价格、沪镍远月合约价格、月差（近月-远月）",
    "unit": "近月-远月",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.1"
},
{
    "name": "沪镍近月合约价格（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "沪镍远月合约价格",
    "unit": "",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.1"
},
{
    "name": "沪镍远月合约价格（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "海外发运量与发运天数时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.4"
},
{
    "name": "海外发运量分国别时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.4"
},
{
    "name": "海外发运量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.4"
},
{
    "name": "海外对华发运总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "海外对华电锌发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.4"
},
{
    "name": "海外对华锌发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.4"
},
{
    "name": "海外对华锌发运盈亏（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.4"
},
{
    "name": "海外对华锌发运量分国别（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.4"
},
{
    "name": "海外对华锌发运量总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.4"
},
{
    "name": "海外对华锌发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.4"
},
{
    "name": "海外对华锌精矿发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-6.4"
},
{
    "name": "海外检修量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.1"
},
{
    "name": "海外硅矿季度产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.1"
},
{
    "name": "海外硅矿季度产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.1"
},
{
    "name": "海外硅矿季度产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.1"
},
{
    "name": "海外硅矿季度再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.1"
},
{
    "name": "海外硅矿季度加工费TC（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.1"
},
{
    "name": "海外硅矿季度检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.1"
},
{
    "name": "海外硅矿季度进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.1"
},
{
    "name": "海外精炼产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.1"
},
{
    "name": "海外精炼锡检修量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.2"
},
{
    "name": "海外精炼锡检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.2"
},
{
    "name": "海外进口量分国别（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.1"
},
{
    "name": "海外进口量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.1"
},
{
    "name": "海外锂矿产能分国别（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.2"
},
{
    "name": "海外锂矿产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.1"
},
{
    "name": "海外锂矿出口量分国别（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.2"
},
{
    "name": "海外锂矿进口量分国别（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.2"
},
{
    "name": "海外锌矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锌矿产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锌矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锌矿再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锌矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锌矿进口量分国别（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锌矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锌精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.1"
},
{
    "name": "海外锡矿产能利用率时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.1"
},
{
    "name": "海外锡矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.1"
},
{
    "name": "海外锡矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.1"
},
{
    "name": "海外锡矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.1"
},
{
    "name": "海外锡精矿产量总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.2"
},
{
    "name": "海外锡精矿产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.1"
},
{
    "name": "湿法铜升贴水",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-CU-2.3"
},
{
    "name": "澳大利亚进口量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.4"
},
{
    "name": "澳大利亚进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.4"
},
{
    "name": "澳大利亚锂矿产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.2"
},
{
    "name": "澳大利亚锌矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "澳大利亚锌矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "澳大利亚锌矿再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "澳大利亚锌矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "澳大利亚锌精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "澳大利亚锡矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "澳大利亚锡精矿产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.2"
},
{
    "name": "澳大利亚锡精矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.2"
},
{
    "name": "澳大利亚镍矿产能（万吨/年）",
    "unit": "万吨/年",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.2"
},
{
    "name": "澳大利亚镍矿产量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "澳大利亚镍矿开工天数（天/季度）",
    "unit": "天/季度",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.2"
},
{
    "name": "澳大利亚镍精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.2"
},
{
    "name": "焊锡/锡化工终端产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "焊锡/锡焊料排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "焊锡/锡焊料终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "焊锡/锡焊料终端订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "焊锡/锡焊料订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "焊锡价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.5"
},
{
    "name": "焊锡终端产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "焊锡订单量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "煤价（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "煤沥青价格",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.3"
},
{
    "name": "现金-3个月月差（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.4"
},
{
    "name": "现金-3个月月差（美元/吨）",
    "unit": "美元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.3"
},
{
    "name": "现金价（美元/吨）",
    "unit": "美元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.3"
},
{
    "name": "甘肃镍矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "甘肃镍矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "甘肃镍矿开工天数（天/月）",
    "unit": "天/月",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "甘肃镍矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "电价时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "电子级锡出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "电子级锡终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "电子级锡订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "电池级碳酸锂利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.5"
},
{
    "name": "电池级镍制品出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.3"
},
{
    "name": "电池级镍制品出口金额（亿美元）",
    "unit": "亿美元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.3"
},
{
    "name": "电池级镍回收量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "电解铝行业加权平均完全成本",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.1"
},
{
    "name": "电解锌现金成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-2.5"
},
{
    "name": "电解镍产量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "电解镍冶炼完全成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.5"
},
{
    "name": "电解镍出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.2"
},
{
    "name": "电解镍发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "电解镍完全成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.4"
},
{
    "name": "电解镍对华发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "电解镍日度利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "电解镍日度利润（元/吨）、沪镍主力合约收盘价（元/吨）、电解镍现金成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "电解镍检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.2"
},
{
    "name": "电镀镍制品出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.3"
},
{
    "name": "电镀镍制品出口金额（亿美元）",
    "unit": "亿美元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.3"
},
{
    "name": "电镀镍终端消费量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "电镀镍订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.3"
},
{
    "name": "盐湖提锂利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.5"
},
{
    "name": "盐湖提锂精炼产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.1"
},
{
    "name": "矿-精炼产量比（倍）",
    "unit": "倍",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.3"
},
{
    "name": "秘鲁锌矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "秘鲁锌矿产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "秘鲁锌矿再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "秘鲁锌矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "秘鲁锌精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.2"
},
{
    "name": "精炼锡净进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.2"
},
{
    "name": "精炼镍日度利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "精炼镍检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.2"
},
{
    "name": "精炼镍进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.2"
},
{
    "name": "终端排产计划（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "终端消费增速（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "缅甸再生锡产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "缅甸再生锡产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.2.3"
},
{
    "name": "缅甸再生锡进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "缅甸发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.4"
},
{
    "name": "缅甸电子级锡出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "缅甸锡矿产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.1"
},
{
    "name": "缅甸锡矿价格时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "缅甸锡矿价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "缅甸锡矿进口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "缅甸锡精矿产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.2"
},
{
    "name": "缅甸锡精矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "缅甸锡锭出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.2"
},
{
    "name": "缅甸锡锭进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.2"
},
{
    "name": "缅甸需求增速（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "美国硅矿月产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "美国硅矿月产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "美国硅矿月再生产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "美国硅矿月加工费TC（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "美国硅矿月进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.1.2"
},
{
    "name": "能源/原料成本总量（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "能源成本时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "船货在途量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "菲律宾电解镍进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.2"
},
{
    "name": "菲律宾矿-精炼产量比（倍）",
    "unit": "倍",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.2"
},
{
    "name": "菲律宾至中国海运费（美元/湿吨）",
    "unit": "美元/湿吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "菲律宾进口在途量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "菲律宾进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.4"
},
{
    "name": "菲律宾镍矿CIF价格（美元/湿吨）",
    "unit": "美元/湿吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "菲律宾镍矿CIF价格（美元/湿吨）、菲律宾镍矿FOB价格（美元/湿吨）",
    "unit": "美元/湿吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "菲律宾镍矿产能利用率（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "菲律宾镍矿产能（万吨/年）",
    "unit": "万吨/年",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.2"
},
{
    "name": "菲律宾镍矿产量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "菲律宾镍矿发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "菲律宾镍矿对华发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "菲律宾镍矿检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "菲律宾镍矿离港量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "菲律宾镍矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.1"
},
{
    "name": "菲律宾镍精炼产能（万吨/年）",
    "unit": "万吨/年",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.1"
},
{
    "name": "菲律宾镍精矿TC",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "菲律宾镍精矿进口量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "行业理论盈利",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.1"
},
{
    "name": "进口在途量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-4.5"
},
{
    "name": "金属硅下游终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-5.2"
},
{
    "name": "金属硅再生月产能（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.2.3"
},
{
    "name": "金属硅冶炼成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-7.1"
},
{
    "name": "金属硅净出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.2"
},
{
    "name": "金属硅净进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.1"
},
{
    "name": "金属硅出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.2"
},
{
    "name": "金属硅制品净出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.3"
},
{
    "name": "金属硅制品出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.3"
},
{
    "name": "金属硅海外发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-6.4"
},
{
    "name": "金属硅精炼月检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SI-3.2.2"
},
{
    "name": "铝价指数",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.1"
},
{
    "name": "铝制结构件/容器/车轮/绞线出口量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-6.3"
},
{
    "name": "铝板带/铝箔/铝挤压材出口量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-6.3"
},
{
    "name": "锂云母/锂辉石利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-2.5"
},
{
    "name": "锂云母精炼产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.1"
},
{
    "name": "锂云母进口量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.4"
},
{
    "name": "锂矿进口总量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.4"
},
{
    "name": "锂矿进口量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.4"
},
{
    "name": "锂辉石产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.3"
},
{
    "name": "锂辉石精炼产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.2.1"
},
{
    "name": "锂辉石进口量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.4"
},
{
    "name": "锌月差（元/吨）",
    "unit": "元/吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-2.4"
},
{
    "name": "锌矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-3.1.4"
},
{
    "name": "锌精矿成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-ZN-2.5"
},
{
    "name": "锡制品出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "锡化工出口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "锡化工出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "锡化工终端产量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "锡化工终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.2"
},
{
    "name": "锡化工订单量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "锡焊料/焊锡与锡化工出口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "锡焊料/焊锡出口量分国别时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "锡焊料/焊锡出口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "锡焊料/焊锡出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.3"
},
{
    "name": "锡矿总进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-3.1.4"
},
{
    "name": "锡精矿与再生锡进口量时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "锡精矿价格时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-7.3"
},
{
    "name": "锡精矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "锡锭净进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "锡锭现货价格时序图",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-2.2"
},
{
    "name": "锡锭进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-6.1"
},
{
    "name": "镍冶炼成本总量（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "镍冶炼成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "镍冶炼日度利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "镍制品出口总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.3"
},
{
    "name": "镍原料进口总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.1"
},
{
    "name": "镍合金出口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.3"
},
{
    "name": "镍合金出口金额（亿美元）",
    "unit": "亿美元",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.3"
},
{
    "name": "镍合金终端产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "镍现货价格（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.2"
},
{
    "name": "镍生铁/NPI成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.3"
},
{
    "name": "镍生铁/NPI进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.1"
},
{
    "name": "镍矿CIF价格（美元/湿吨）、镍矿FOB价格（美元/湿吨）",
    "unit": "美元/湿吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "镍矿进口量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.1"
},
{
    "name": "镍精炼产量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.1"
},
{
    "name": "镍精炼金属进口总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.2"
},
{
    "name": "镍精矿TC",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "镍精矿进口到港量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1"
},
{
    "name": "镍精矿进口量（吨）",
    "unit": "吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.1.4"
},
{
    "name": "镍终端消费总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.2"
},
{
    "name": "镍铁RKEF成本（元/镍点）",
    "unit": "元/镍点",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "镍铁一体化利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-2.5"
},
{
    "name": "镍铁一体化成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "镍铁一体化成本（元/吨）、镍精矿TC（美元/吨干矿）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "镍铁一体化日度利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "镍铁一体化日度利润（元/吨）、镍矿成本（元/吨）、TC（美元/吨干矿）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "镍铁完全成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.4"
},
{
    "name": "镍铁检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.2"
},
{
    "name": "镍需求先行指标总量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-5.3"
},
{
    "name": "需求增速（%）",
    "unit": "%",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-SN-5.3"
},
{
    "name": "非洲进口量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.4"
},
{
    "name": "非洲锂矿产量（万吨LCE）",
    "unit": "万吨LCE",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-LI-3.1.2"
},
{
    "name": "预焙阳极价格",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.3"
},
{
    "name": "预焙阳极均价",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-AL-3.2"
},
{
    "name": "高冰镍产量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "高冰镍再生量",
    "unit": "",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2"
},
{
    "name": "高冰镍发运天数（天）",
    "unit": "天",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "高冰镍完全成本（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.4"
},
{
    "name": "高冰镍对华发运量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-6.4"
},
{
    "name": "高冰镍成本（元/吨）、镍矿成本（元/吨）、加工费（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.1"
},
{
    "name": "高冰镍日度利润（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "高冰镍日度利润（元/吨）、镍矿成本（元/吨）、加工费（元/吨）",
    "unit": "元/吨",
    "freq": "daily",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-7.2"
},
{
    "name": "高冰镍检修量（万吨）",
    "unit": "万吨",
    "freq": "monthly",
    "source": "同花顺模板",
    "ref_count": 1,
    "sample_templates": "THS-NI-3.2.2"
}
  ]
}
```

---

## 注意事项

1. **所有指标均需人工审核**: 以上为自动生成的草稿，录入前需人工确认指标名称、单位、频率的准确性。
2. **不修改 indicators_v1**: 本草稿仅供参考，未对 indicators_v1.json 做任何修改。
3. **CAT_B 衍生指标不入库**: 均值、标准差、分位等统计指标应通过计算引擎生成，不建议直接作为 indicators_v1 条目。
4. **CAT_C 别名扩充**: 实体已存在的指标（如「沪伦比」可能已有对应的 SHFE/LME 比价条目），只需在别名映射中扩充，无需新增时序数据。
5. **数据源对接**: 新增指标需确认数据源（知几 API / 海关 / 交易所 / 第三方），并编写对应的 fetch 脚本。
6. **去重原则**: 合并时已对指标名称做精确去重，但语义重复（如同一指标的不同表述）需人工识别。

---

## 产出文件索引

| 文件 | 说明 |
|------|------|
| `ths_missing_classify.csv` | THS 缺失指标分类明细（1396 条） |
| `high_risk_all_miss_template.md` | 16 个 ALL_MISS 模板专项报告 |
| `merged_total_missing_preview.csv` | PDF周报+同花顺合并去重待补清单（693 条） |
| `merged_total_missing_draft.md` | 本文件：录入草稿 |
