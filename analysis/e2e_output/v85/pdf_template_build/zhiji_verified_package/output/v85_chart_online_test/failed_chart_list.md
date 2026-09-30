# 渲染失败图表清单

> 生成时间: 2026-09-30T13:30:01  
> 工单: HERMES_V85_CHART_TEMPLATE_INTEGRATION

## 1. 汇总

| 类别 | 数量 |
|------|------|
| 完全失败图表（无任何有效数据） | 5 |
| 部分失败图表（含失败series） | 6 |
| INVALID series（无效zhiji_id, HTTP 500） | 5 |
| MISSING series（缺失，重检索失败） | 2 |
| FETCH_FAIL series（时序拉取失败） | 0 |

## 2. 完全失败图表

### TPL-AO-042 — 海漂库存-全球主要国家-钢联
- 品种: AO | chart_type: 单折线 | 状态: PART_OK
  - 海漂库存-全球主要国家-钢联: INVALID — 无效zhiji_id: HTTP 500
- HTML: `rendered/TPL-AO-042.html`

### TPL-AO-058 — 发运量-路透-几内亚总和
- 品种: AO | chart_type: 单折线 | 状态: PART_OK
  - 发运量-路透-几内亚总和: MISSING — 缺失series: 无有效zhiji_id(重检索失败)
- HTML: `rendered/TPL-AO-058.html`

### TPL-SI-026 — DMC全国开工率
- 品种: SI | chart_type: 复合混合(折线+柱状) | 状态: PART_OK
  - DMC全国开工率: INVALID — 无效zhiji_id: HTTP 500
  - DMC:全国:开工率: INVALID — 无效zhiji_id: HTTP 500
- HTML: `rendered/TPL-SI-026.html`

### TPL-SI-028 — 再生铝合金龙头开工率
- 品种: SI | chart_type: 单折线 | 状态: PART_OK
  - 再生铝合金龙头开工率: INVALID — 无效zhiji_id: HTTP 500
- HTML: `rendered/TPL-SI-028.html`

### TPL-NI-033 — 镍铁理论利润（RKEF,山东）
- 品种: NI | chart_type: 单折线 | 状态: PART_OK
  - 镍铁理论利润（RKEF,山东）: MISSING — 缺失series: 无有效zhiji_id(重检索失败)
- HTML: `rendered/TPL-NI-033.html`

## 3. PART_OK 图表（不纳入正式投产看板）

| template_id | 品种 | 标题 | 失败series | 失败原因 |
|---|---|---|---|---|
| TPL-AO-042 | AO | 海漂库存-全球主要国家-钢联 | 1/1 | INVALID:无效zhiji_id: HTTP 500 |
| TPL-AO-058 | AO | 发运量-路透-几内亚总和 | 1/1 | MISSING:缺失series: 无有效zhiji_id(重检索失败) |
| TPL-SI-026 | SI | DMC全国开工率 | 2/2 | INVALID:无效zhiji_id: HTTP 500; INVALID:无效zhiji_id: HTTP 500 |
| TPL-SI-028 | SI | 再生铝合金龙头开工率 | 1/1 | INVALID:无效zhiji_id: HTTP 500 |
| TPL-SI-034 | SI | 多晶硅开工率 | 1/3 | INVALID:无效zhiji_id: HTTP 500 |
| TPL-NI-033 | NI | 镍铁理论利润（RKEF,山东） | 1/1 | MISSING:缺失series: 无有效zhiji_id(重检索失败) |

## 4. 失败 series 明细（T2.6 页面已标记）

| template_id | series | zhiji_id | 状态 | 原因 |
|---|---|---|---|---|
| TPL-AO-042 | 海漂库存-全球主要国家-钢联 | — | INVALID | 无效zhiji_id: HTTP 500 |
| TPL-AO-058 | 发运量-路透-几内亚总和 | — | MISSING | 缺失series: 无有效zhiji_id(重检索失败) |
| TPL-SI-026 | DMC全国开工率 | — | INVALID | 无效zhiji_id: HTTP 500 |
| TPL-SI-026 | DMC:全国:开工率 | — | INVALID | 无效zhiji_id: HTTP 500 |
| TPL-SI-028 | 再生铝合金龙头开工率 | — | INVALID | 无效zhiji_id: HTTP 500 |
| TPL-SI-034 | 中国多晶硅开工率 | — | INVALID | 无效zhiji_id: HTTP 500 |
| TPL-NI-033 | 镍铁理论利润（RKEF,山东） | — | MISSING | 缺失series: 无有效zhiji_id(重检索失败) |

## 5. 失败原因归类

- **INVALID** (5项): 无效zhiji_id: HTTP 500
- **MISSING** (2项): 缺失series: 无有效zhiji_id(重检索失败)
