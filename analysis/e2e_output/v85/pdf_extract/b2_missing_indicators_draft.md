# B2 缺失指标录入草稿

> 自动生成，人工复核后复制粘贴到 `indicators_v1.json`
> 生成时间: 2026-09-29 18:24
> 条目总数: 109 (有效指标: 23, 噪声: 86)

## 🔴 P0 — 周报高频图表（优先录入） (8 条)

| # | 指标名 | 品种 | 地域 | 频率 | 单位 | 相似候选 | 来源 |
|---|--------|------|------|------|------|----------|------|
| 1 | `Cash` | — | 中国 | unknown | — | LME：铝：CASH-3M合约：结算价差（日）(al_2_lme_settle) | LME：铅：CASH-3M合约：结算价差（日）(pb_23_aux_2) | 铝周报 chart_29 |
| 2 | `连三` | — | 中国 | unknown | — | — | 铝周报 chart_29 |
| 3 | `连四` | — | 中国 | unknown | — | — | 铝周报 chart_29 |
| 4 | `连五` | — | 中国 | unknown | — | — | 铝周报 chart_29 |
| 5 | `交通运输` | AL | 中国 | unknown | — | — | 铝周报 chart_104 |
| 6 | `房屋建筑` | AL | 中国 | unknown | — | — | 铝周报 chart_104 |
| 7 | `家电` | AL | 中国 | unknown | — | — | 铝周报 chart_104 |
| 8 | `电力` | AL | 中国 | unknown | — | 电力成本分项(si_72_cost) | 电力成本分项(si_72_cost_power) | 铝周报 chart_104 |

<details><summary>🔴 JSON 录入片段（前 8 条）</summary>

### 1. Cash

```json
{
  "b2_001_futures": {
    "name": "Cash",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_futures",
    "ids": {
      "al": "(待查:ID01244864)"
    },
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_29",
      "chart_title": "AL盘面结构",
      "priority": "P0",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "期货",
      "similar_in_db": "LME：铝：CASH-3M合约：结算价差（日）(al_2_lme_settle) | LME：铅：CASH-3M合约：结算价差（日）(pb_23_aux_2) | SHFE铅仓单(i2)",
      "raw_text": "Cash",
      "note": "人工复核后录入"
    }
  }
}
```

### 2. 连三

```json
{
  "b2_002_futures": {
    "name": "连三",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_futures",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_29",
      "chart_title": "AL盘面结构",
      "priority": "P0",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "期货",
      "similar_in_db": "无",
      "raw_text": "连三",
      "note": "人工复核后录入"
    }
  }
}
```

### 3. 连四

```json
{
  "b2_003_futures": {
    "name": "连四",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_futures",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_29",
      "chart_title": "AL盘面结构",
      "priority": "P0",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "期货",
      "similar_in_db": "无",
      "raw_text": "连四",
      "note": "人工复核后录入"
    }
  }
}
```

### 4. 连五

```json
{
  "b2_004_futures": {
    "name": "连五",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_futures",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_29",
      "chart_title": "AL盘面结构",
      "priority": "P0",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "期货",
      "similar_in_db": "无",
      "raw_text": "连五",
      "note": "人工复核后录入"
    }
  }
}
```

### 5. 交通运输

```json
{
  "b2_005_consumption": {
    "name": "交通运输",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_consumption",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_104",
      "chart_title": "铝终端消费",
      "priority": "P0",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "消费",
      "similar_in_db": "无",
      "raw_text": "交通运输",
      "note": "人工复核后录入"
    }
  }
}
```

### 6. 房屋建筑

```json
{
  "b2_006_consumption": {
    "name": "房屋建筑",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_consumption",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_104",
      "chart_title": "铝终端消费",
      "priority": "P0",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "消费",
      "similar_in_db": "无",
      "raw_text": "房屋建筑",
      "note": "人工复核后录入"
    }
  }
}
```

### 7. 家电

```json
{
  "b2_007_consumption": {
    "name": "家电",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_consumption",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_104",
      "chart_title": "铝终端消费",
      "priority": "P0",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "消费",
      "similar_in_db": "无",
      "raw_text": "家电",
      "note": "人工复核后录入"
    }
  }
}
```

### 8. 电力

```json
{
  "b2_008_consumption": {
    "name": "电力",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_consumption",
    "ids": {
      "SI": "(待查:ID02313973)"
    },
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_104",
      "chart_title": "铝终端消费",
      "priority": "P0",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "消费",
      "similar_in_db": "电力成本分项(si_72_cost) | 电力成本分项(si_72_cost_power) | 电力成本分项(si_72_cost_power_2)",
      "raw_text": "电力",
      "note": "人工复核后录入"
    }
  }
}
```

</details>

## 🟡 P1 — 中频出现指标 (14 条)

| # | 指标名 | 品种 | 地域 | 频率 | 单位 | 相似候选 | 来源 |
|---|--------|------|------|------|------|----------|------|
| 1 | `沪铝25Δ` | AL | 中国 | unknown | — | — | 铝周报 chart_22 |
| 2 | `Risk` | AL | 中国 | unknown | — | — | 铝周报 chart_22 |
| 3 | `Reversal` | AL | 中国 | unknown | — | — | 铝周报 chart_22 |
| 4 | `沪铜25Δ` | CU | 中国 | unknown | — | — | 铝周报 chart_23 |
| 5 | `Risk` | CU | 中国 | unknown | — | — | 铝周报 chart_23 |
| 6 | `Reversal` | CU | 中国 | unknown | — | — | 铝周报 chart_23 |
| 7 | `沪铝IV` | AL | 中国 | unknown | — | — | 铝周报 chart_24 |
| 8 | `India` | — | LME | unknown | — | — | 铝周报 chart_31 |
| 9 | `亏损企业比例` | — | 中国 | unknown | — | — | 铝周报 chart_119 |
| 10 | `电网基本建设投资完成额` | — | 中国 | monthly | — | 中国：电网工程：投资完成额累计值（月）(cu_52_grid_inv) | 铝周报 chart_126 |
| 11 | `新增220千伏及以上线路长度` | — | 中国 | monthly | — | — | 铝周报 chart_127 |
| 12 | `电网建设累计同比` | — | 中国 | unknown | — | — | 铝周报 chart_128 |
| 13 | `销量:动力电池` | — | 中国 | monthly | — | 动力电池装车量(li_52_idx) | 中国动力电池产量：三元(wr239) | 铝周报 chart_130 |
| 14 | `同基准下有色库存相对比值对比` | — | 中国 | daily | — | — | 锡周报 chart_06 |

<details><summary>🟡 JSON 录入片段（前 14 条）</summary>

### 1. 沪铝25Δ

```json
{
  "b2_001_misc": {
    "name": "沪铝25Δ",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_22",
      "chart_title": "沪铝25Δ",
      "priority": "P1",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "沪铝25Δ",
      "note": "人工复核后录入"
    }
  }
}
```

### 2. Risk

```json
{
  "b2_002_misc": {
    "name": "Risk",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_22",
      "chart_title": "沪铝25Δ",
      "priority": "P1",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "Risk",
      "note": "人工复核后录入"
    }
  }
}
```

### 3. Reversal

```json
{
  "b2_003_misc": {
    "name": "Reversal",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_22",
      "chart_title": "沪铝25Δ",
      "priority": "P1",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "Reversal",
      "note": "人工复核后录入"
    }
  }
}
```

### 4. 沪铜25Δ

```json
{
  "b2_004_misc": {
    "name": "沪铜25Δ",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_23",
      "chart_title": "沪铜25Δ",
      "priority": "P1",
      "variety_hint": "CU",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "沪铜25Δ",
      "note": "人工复核后录入"
    }
  }
}
```

### 5. Risk

```json
{
  "b2_005_misc": {
    "name": "Risk",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_23",
      "chart_title": "沪铜25Δ",
      "priority": "P1",
      "variety_hint": "CU",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "Risk",
      "note": "人工复核后录入"
    }
  }
}
```

### 6. Reversal

```json
{
  "b2_006_misc": {
    "name": "Reversal",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_23",
      "chart_title": "沪铜25Δ",
      "priority": "P1",
      "variety_hint": "CU",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "Reversal",
      "note": "人工复核后录入"
    }
  }
}
```

### 7. 沪铝IV

```json
{
  "b2_007_misc": {
    "name": "沪铝IV",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_24",
      "chart_title": "沪铝IV",
      "priority": "P1",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "沪铝IV",
      "note": "人工复核后录入"
    }
  }
}
```

### 8. India

```json
{
  "b2_008_stock": {
    "name": "India",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_31",
      "chart_title": "LME仓单原产地",
      "priority": "P1",
      "variety_hint": "(待确认)",
      "region_hint": "LME",
      "dimension": "库存",
      "similar_in_db": "无",
      "raw_text": "India",
      "note": "人工复核后录入"
    }
  }
}
```

### 9. 亏损企业比例

```json
{
  "b2_009_profit": {
    "name": "亏损企业比例",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_profit",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_119",
      "chart_title": "亏损企业比例",
      "priority": "P1",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "利润",
      "similar_in_db": "无",
      "raw_text": "亏损企业比例",
      "note": "人工复核后录入"
    }
  }
}
```

### 10. 电网基本建设投资完成额

```json
{
  "b2_010_invest": {
    "name": "电网基本建设投资完成额",
    "unit": "(待确认)",
    "freq": "monthly",
    "verified": false,
    "category": "b2_missing_invest",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_126",
      "chart_title": "中国:电网基本建设投资完成额:当月值",
      "priority": "P1",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "投资",
      "similar_in_db": "中国：电网工程：投资完成额累计值（月）(cu_52_grid_inv)",
      "raw_text": "中国:电网基本建设投资完成额:当月值",
      "note": "人工复核后录入"
    }
  }
}
```

### 11. 新增220千伏及以上线路长度

```json
{
  "b2_011_misc": {
    "name": "新增220千伏及以上线路长度",
    "unit": "(待确认)",
    "freq": "monthly",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_127",
      "chart_title": "中国:新增220千伏及以上线路长度:当月值",
      "priority": "P1",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "中国:新增220千伏及以上线路长度:当月值",
      "note": "人工复核后录入"
    }
  }
}
```

### 12. 电网建设累计同比

```json
{
  "b2_012_stat": {
    "name": "电网建设累计同比",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_stat",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_128",
      "chart_title": "电网建设累计同比",
      "priority": "P1",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "统计",
      "similar_in_db": "无",
      "raw_text": "电网建设累计同比",
      "note": "人工复核后录入"
    }
  }
}
```

### 13. 销量:动力电池

```json
{
  "b2_013_sales": {
    "name": "销量:动力电池",
    "unit": "(待确认)",
    "freq": "monthly",
    "verified": false,
    "category": "b2_missing_sales",
    "ids": {
      "LI": "(待查:ID01660879)"
    },
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_130",
      "chart_title": "中国:销量:动力电池:当月值",
      "priority": "P1",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "销量",
      "similar_in_db": "动力电池装车量(li_52_idx) | 中国动力电池产量：三元(wr239) | 动力电池 出口:三元材料(wr140)",
      "raw_text": "中国:销量:动力电池:当月值",
      "note": "人工复核后录入"
    }
  }
}
```

### 14. 同基准下有色库存相对比值对比

```json
{
  "b2_014_stock": {
    "name": "同基准下有色库存相对比值对比",
    "unit": "(待确认)",
    "freq": "daily",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "锡周报",
      "chart_local_id": "chart_06",
      "chart_title": "同基准下有色库存相对比值对比",
      "priority": "P1",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "库存",
      "similar_in_db": "无",
      "raw_text": "同基准下有色库存相对比值对比",
      "note": "人工复核后录入"
    }
  }
}
```

</details>

## 🟢 P2 — 低频偶现有效指标 (1 条)

| # | 指标名 | 品种 | 地域 | 频率 | 单位 | 相似候选 | 来源 |
|---|--------|------|------|------|------|----------|------|
| 1 | `四金属` | — | 中国 | unknown | — | 周产量-金属硅-云南(wr202) | 周产量-金属硅-四川(wr203) | 锡周报 chart_07 |

<details><summary>🟢 JSON 录入片段（前 1 条）</summary>

### 1. 四金属

```json
{
  "b2_001_misc": {
    "name": "四金属",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "锡周报",
      "chart_local_id": "chart_07",
      "chart_title": "四金属",
      "priority": "P2",
      "variety_hint": "(待确认)",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "周产量-金属硅-云南(wr202) | 周产量-金属硅-四川(wr203) | 周产量-金属硅-新疆(wr204)",
      "raw_text": "四金属",
      "note": "人工复核后录入"
    }
  }
}
```

</details>

## ⚪ P2 — 噪声文本（非真实指标，供参考） (86 条)

| # | 指标名 | 品种 | 地域 | 频率 | 单位 | 相似候选 | 来源 |
|---|--------|------|------|------|------|----------|------|
| 1 | `度相比前期进一步加` | — | 河南 | unknown | — | — | 氧化铝周报 chart_28 |
| 2 | `单小幅增加` | AL | 山东 | unknown | — | — | 氧化铝周报 chart_41 |
| 3 | `万吨仓单过期` | AL | 山东 | unknown | 万吨 | 不锈钢仓单(wr263) | SHFE铅仓单(i2) | 氧化铝周报 chart_41 |
| 4 | `万吨（17.2%` | AL | 几内亚 | unknown | 万吨 | 印尼镍矿价格（HPM 1.6%）(wr253) | 氧化铝周报 chart_80 |
| 5 | `铁合金在线口径` | SI | 中国 | unknown | — | 铝合金进口量(wr27) | 镍铁进口量(wr275) | 硅产业链周报 chart_22 |
| 6 | `铁合金在线口径` | SI | 中国 | unknown | — | 铝合金进口量(wr27) | 镍铁进口量(wr275) | 硅产业链周报 chart_23 |
| 7 | `SMM锂盐价格走势图` | LC | SMM | daily | — | 沪锡价格走势(wr170) | SMM 铅精废价差(j24_refine_spread) | 碳酸锂周报 chart_02 |
| 8 | `SMM锂盐价格走势图` | LC | SMM | daily | — | 沪锡价格走势(wr170) | SMM 铅精废价差(j24_refine_spread) | 碳酸锂周报 chart_04 |
| 9 | `Curve` | AL | 中国 | unknown | — | — | 铝周报 chart_24 |
| 10 | `春节` | AL | 中国 | unknown | — | — | 铝周报 chart_39 |
| 11 | `春节` | AL | 中国 | unknown | — | — | 铝周报 chart_41 |
| 12 | `` | AL | 中国 | daily | — | — | 铝周报 chart_46 |
| 13 | `` | AL | 中国 | daily | 天 | — | 铝周报 chart_47 |
| 14 | `` | AL | 中国 | unknown | — | — | 铝周报 chart_56 |
| 15 | `` | AL | 中国 | unknown | — | — | 铝周报 chart_57 |
| 16 | `` | AL | 中国 | unknown | — | — | 铝周报 chart_58 |
| 17 | `万吨万吨` | AL | 中国 | unknown | 万吨 | — | 铝周报 chart_60 |
| 18 | `万吨万吨` | AL | 中国 | unknown | 万吨 | — | 铝周报 chart_61 |
| 19 | `万吨%` | AL | 中国 | unknown | 万吨 | — | 铝周报 chart_66 |
| 20 | `万吨%` | AL | 中国 | monthly | 万吨 | — | 铝周报 chart_67 |
| 21 | `` | — | SMM | unknown | — | — | 铝周报 chart_84 |
| 22 | `` | — | SMM | unknown | — | — | 铝周报 chart_85 |
| 23 | `万吨万吨` | AL | 中国 | unknown | 万吨 | — | 铝周报 chart_91 |
| 24 | `万吨万吨` | AL | 中国 | unknown | 万吨 | — | 铝周报 chart_92 |
| 25 | `万吨万吨` | AL | 中国 | unknown | 万吨 | — | 铝周报 chart_93 |
| 26 | `万吨9` | AL | 中东 | unknown | 万吨 | — | 铝周报 chart_98 |
| 27 | `万吨9` | AL | EU | unknown | 万吨 | — | 铝周报 chart_99 |
| 28 | `万吨9` | AL | EU | unknown | 万吨 | — | 铝周报 chart_100 |
| 29 | `万吨9` | AL | 北美 | unknown | 万吨 | — | 铝周报 chart_101 |
| 30 | `万吨9` | AL | 东南亚 | unknown | 万吨 | — | 铝周报 chart_102 |
| 31 | `万吨9` | AL | 中东 | unknown | 万吨 | — | 铝周报 chart_103 |
| 32 | `累计同比（截至6月` | AL | 中国 | monthly | — | — | 铝周报 chart_104 |
| 33 | `当月值` | AL | 中国 | monthly | — | — | 铝周报 chart_104 |
| 34 | `万辆` | — | 中国 | unknown | 万辆 | — | 铝周报 chart_107 |
| 35 | `万辆` | — | 中国 | unknown | 万辆 | — | 铝周报 chart_108 |
| 36 | `万辆` | — | 中国 | unknown | 万辆 | — | 铝周报 chart_109 |
| 37 | `万辆` | — | 中国 | monthly | 万辆 | — | 铝周报 chart_110 |
| 38 | `万辆` | — | 中国 | monthly | 万辆 | — | 铝周报 chart_111 |
| 39 | `万辆` | — | 中国 | monthly | 万辆 | — | 铝周报 chart_112 |
| 40 | `万辆` | — | 中国 | unknown | 万辆 | — | 铝周报 chart_113 |
| 41 | `万辆` | — | 中国 | monthly | 万辆 | — | 铝周报 chart_114 |
| 42 | `万辆` | — | 中国 | unknown | 万辆 | — | 铝周报 chart_115 |
| 43 | `万辆` | — | 中国 | monthly | 万辆 | — | 铝周报 chart_116 |
| 44 | `万辆` | — | 中国 | unknown | 万辆 | — | 铝周报 chart_117 |
| 45 | `万辆` | — | 中国 | weekly | 万辆 | — | 铝周报 chart_120 |
| 46 | `` | SI | SMM | monthly | — | — | 铝周报 chart_124 |
| 47 | `` | SI | 中国 | unknown | — | — | 铝周报 chart_125 |
| 48 | `存提供基本面支撑` | SN | 中国 | unknown | — | — | 锡周报 chart_02 |
| 49 | `vs` | — | 中国 | unknown | — | 氧化铝现货vs长协价格(wr43) | 锡周报 chart_07 |
| 50 | `SPX` | — | 中国 | unknown | — | — | 锡周报 chart_07 |
| 51 | `60日滚动相关图：锡` | SN | 中国 | daily | — | — | 锡周报 chart_07 |
| 52 | `` | — | LME | daily | — | — | 锡周报 chart_39 |
| 53 | `样本白电总用锡Yoy` | SN | 中国 | unknown | — | — | 锡周报 chart_49 |
| 54 | `Yoy` | — | 中国 | unknown | — | — | 锡周报 chart_49 |
| 55 | `短期观望策略` | NI | 中国 | unknown | — | — | 镍与不锈钢周报 chart_01 |
| 56 | `` | NI | SHFE | monthly | — | — | 镍与不锈钢周报 chart_02 |
| 57 | `` | NI | SHFE | monthly | — | — | 镍与不锈钢周报 chart_03 |
| 58 | `元/金属吨` | NI | 中国 | unknown | 元/金属吨 | — | 镍与不锈钢周报 chart_05 |
| 59 | `%/金属吨100` | NI | 印尼 | unknown | 吨 | — | 镍与不锈钢周报 chart_11 |
| 60 | `%%%/金属吨` | NI | 印尼 | unknown | 吨 | — | 镍与不锈钢周报 chart_11 |
| 61 | `%/金属吨100` | — | 印尼 | unknown | 吨 | — | 镍与不锈钢周报 chart_12 |
| 62 | `` | NI | 中国 | weekly | — | — | 镍与不锈钢周报 chart_17 |
| 63 | `` | NI | 印尼 | weekly | — | — | 镍与不锈钢周报 chart_18 |
| 64 | `` | NI | 中国 | unknown | — | — | 镍与不锈钢周报 chart_19 |
| 65 | `` | NI | 中国 | daily | — | — | 镍与不锈钢周报 chart_20 |
| 66 | `` | NI | 中国 | daily | — | — | 镍与不锈钢周报 chart_21 |
| 67 | `` | NI | 中国 | daily | — | — | 镍与不锈钢周报 chart_22 |
| 68 | `金属吨` | NI | 中国 | unknown | 吨 | 周产量-金属硅-云南(wr202) | 周产量-金属硅-四川(wr203) | 镍与不锈钢周报 chart_29 |
| 69 | `` | NI | 中国 | unknown | — | — | 镍与不锈钢周报 chart_33 |
| 70 | `` | NI | 中国 | unknown | — | — | 镍与不锈钢周报 chart_34 |
| 71 | `金属吨` | NI | 印尼 | unknown | 吨 | 周产量-金属硅-云南(wr202) | 周产量-金属硅-四川(wr203) | 镍与不锈钢周报 chart_35 |
| 72 | `` | NI | 印尼 | weekly | — | — | 镍与不锈钢周报 chart_36 |
| 73 | `` | — | 中国 | weekly | 元 | — | 镍与不锈钢周报 chart_37 |
| 74 | `` | LC | 中国 | weekly | — | — | 镍与不锈钢周报 chart_38 |
| 75 | `万辆` | — | 中国 | unknown | 万辆 | — | 镍与不锈钢周报 chart_41 |
| 76 | `万辆` | — | 中国 | unknown | 万辆 | — | 镍与不锈钢周报 chart_42 |
| 77 | `美元/湿吨` | NI | 菲律宾 | unknown | 美元/湿吨 | — | 镍与不锈钢周报 chart_47 |
| 78 | `美元/湿吨` | NI | 印尼 | unknown | 美元/湿吨 | — | 镍与不锈钢周报 chart_48 |
| 79 | `美元/湿吨` | NI | 菲律宾 | unknown | 美元/湿吨 | — | 镍与不锈钢周报 chart_49 |
| 80 | `元/度吨` | NI | 南非 | unknown | 元/度吨 | 三元材料 周度产量(wr133) | 三元材料 月度产量(wr136) | 镍与不锈钢周报 chart_52 |
| 81 | `元/50基吨` | NI | 内蒙古 | unknown | 元/50基吨 | — | 镍与不锈钢周报 chart_53 |
| 82 | `元/50基吨` | NI | 中国 | unknown | 元/50基吨 | — | 镍与不锈钢周报 chart_54 |
| 83 | `元/50基吨` | NI | 中国 | unknown | 元/50基吨 | — | 镍与不锈钢周报 chart_55 |
| 84 | `` | NI | 中国 | weekly | — | — | 镍与不锈钢周报 chart_57 |
| 85 | `` | NI | 中国 | unknown | — | — | 镍与不锈钢周报 chart_58 |
| 86 | `万金属吨万金属吨` | NI | 印尼 | unknown | 吨 | — | 镍与不锈钢周报 chart_59 |

<details><summary>⚪ JSON 录入片段（前 15 条）</summary>

### 1. 度相比前期进一步加

```json
{
  "b2_001_price": {
    "name": "度相比前期进一步加",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_price",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "氧化铝周报",
      "chart_local_id": "chart_28",
      "chart_title": "河南进口矿现金流利润",
      "priority": "P2",
      "variety_hint": "(待确认)",
      "region_hint": "河南",
      "dimension": "价格",
      "similar_in_db": "无",
      "raw_text": "度相比前期进一步加",
      "note": "人工复核后录入"
    }
  }
}
```

### 2. 单小幅增加

```json
{
  "b2_002_stock": {
    "name": "单小幅增加",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "氧化铝周报",
      "chart_local_id": "chart_41",
      "chart_title": "期货库存:氧化铝-山东",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "山东",
      "dimension": "库存",
      "similar_in_db": "无",
      "raw_text": "单小幅增加",
      "note": "人工复核后录入"
    }
  }
}
```

### 3. 万吨仓单过期

```json
{
  "b2_003_stock": {
    "name": "万吨仓单过期",
    "unit": "万吨",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "氧化铝周报",
      "chart_local_id": "chart_41",
      "chart_title": "期货库存:氧化铝-山东",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "山东",
      "dimension": "库存",
      "similar_in_db": "不锈钢仓单(wr263) | SHFE铅仓单(i2) | 碳酸锂 仓单量(wr124)",
      "raw_text": "万吨仓单过期",
      "note": "人工复核后录入"
    }
  }
}
```

### 4. 万吨（17.2%

```json
{
  "b2_004_trade": {
    "name": "万吨（17.2%",
    "unit": "万吨",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_trade",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "氧化铝周报",
      "chart_local_id": "chart_80",
      "chart_title": "铝土矿进口-几内亚",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "几内亚",
      "dimension": "进出口",
      "similar_in_db": "印尼镍矿价格（HPM 1.6%）(wr253)",
      "raw_text": "万吨（17.2%",
      "note": "人工复核后录入"
    }
  }
}
```

### 5. 铁合金在线口径

```json
{
  "b2_005_misc": {
    "name": "铁合金在线口径",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "硅产业链周报",
      "chart_local_id": "chart_22",
      "chart_title": "工业硅开炉情况",
      "priority": "P2",
      "variety_hint": "SI",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "铝合金进口量(wr27) | 镍铁进口量(wr275)",
      "raw_text": "（铁合金在线口径）",
      "note": "人工复核后录入"
    }
  }
}
```

### 6. 铁合金在线口径

```json
{
  "b2_006_misc": {
    "name": "铁合金在线口径",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "硅产业链周报",
      "chart_local_id": "chart_23",
      "chart_title": "工业硅开炉情况",
      "priority": "P2",
      "variety_hint": "SI",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "铝合金进口量(wr27) | 镍铁进口量(wr275)",
      "raw_text": "（铁合金在线口径）",
      "note": "人工复核后录入"
    }
  }
}
```

### 7. SMM锂盐价格走势图

```json
{
  "b2_007_price": {
    "name": "SMM锂盐价格走势图",
    "unit": "(待确认)",
    "freq": "daily",
    "verified": false,
    "category": "b2_missing_price",
    "ids": {
      "SN": "(待查:a12841487)"
    },
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "碳酸锂周报",
      "chart_local_id": "chart_02",
      "chart_title": "工业级碳酸锂 现货价格",
      "priority": "P2",
      "variety_hint": "LC",
      "region_hint": "SMM",
      "dimension": "价格",
      "similar_in_db": "沪锡价格走势(wr170) | SMM 铅精废价差(j24_refine_spread) | SMM 锂矿样本库存:锂盐厂(wr148)",
      "raw_text": "SMM锂盐价格走势图（元/吨）",
      "note": "人工复核后录入"
    }
  }
}
```

### 8. SMM锂盐价格走势图

```json
{
  "b2_008_price": {
    "name": "SMM锂盐价格走势图",
    "unit": "(待确认)",
    "freq": "daily",
    "verified": false,
    "category": "b2_missing_price",
    "ids": {
      "SN": "(待查:a12841487)"
    },
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "碳酸锂周报",
      "chart_local_id": "chart_04",
      "chart_title": "电池级氢氧化锂(微粉) 价格",
      "priority": "P2",
      "variety_hint": "LC",
      "region_hint": "SMM",
      "dimension": "价格",
      "similar_in_db": "沪锡价格走势(wr170) | SMM 铅精废价差(j24_refine_spread) | SMM 锂矿样本库存:锂盐厂(wr148)",
      "raw_text": "SMM锂盐价格走势图（元/吨）",
      "note": "人工复核后录入"
    }
  }
}
```

### 9. Curve

```json
{
  "b2_009_misc": {
    "name": "Curve",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_misc",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_24",
      "chart_title": "沪铝IV",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "其他",
      "similar_in_db": "无",
      "raw_text": "Curve",
      "note": "人工复核后录入"
    }
  }
}
```

### 10. 春节

```json
{
  "b2_010_stock": {
    "name": "春节",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_39",
      "chart_title": "电解铝：社库+厂库（农历）",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "库存",
      "similar_in_db": "无",
      "raw_text": "春节",
      "note": "人工复核后录入"
    }
  }
}
```

### 11. 春节

```json
{
  "b2_011_stock": {
    "name": "春节",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_41",
      "chart_title": "铝棒-社库+厂库（农历）",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "库存",
      "similar_in_db": "无",
      "raw_text": "春节",
      "note": "人工复核后录入"
    }
  }
}
```

### 12. 

```json
{
  "b2_012_stock": {
    "name": "(空)",
    "unit": "(待确认)",
    "freq": "daily",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_46",
      "chart_title": "铝板带箔-原料库存",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "库存",
      "similar_in_db": "无",
      "raw_text": "天万吨",
      "note": "人工复核后录入"
    }
  }
}
```

### 13. 

```json
{
  "b2_013_stock": {
    "name": "(空)",
    "unit": "天",
    "freq": "daily",
    "verified": false,
    "category": "b2_missing_stock",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_47",
      "chart_title": "铝板带箔-原料库存天数",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "库存",
      "similar_in_db": "无",
      "raw_text": "天万吨",
      "note": "人工复核后录入"
    }
  }
}
```

### 14. 

```json
{
  "b2_014_trade": {
    "name": "(空)",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_trade",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_56",
      "chart_title": "未锻轧铝进口量",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "进出口",
      "similar_in_db": "无",
      "raw_text": "万万吨吨万吨",
      "note": "人工复核后录入"
    }
  }
}
```

### 15. 

```json
{
  "b2_015_trade": {
    "name": "(空)",
    "unit": "(待确认)",
    "freq": "(待确认)",
    "verified": false,
    "category": "b2_missing_trade",
    "ids": {},
    "_origin": "b2_missing_prep",
    "_meta": {
      "source_pdf": "铝周报",
      "chart_local_id": "chart_57",
      "chart_title": "铝合金进口量",
      "priority": "P2",
      "variety_hint": "AL",
      "region_hint": "中国",
      "dimension": "进出口",
      "similar_in_db": "无",
      "raw_text": "万万吨吨万吨",
      "note": "人工复核后录入"
    }
  }
}
```

</details>
