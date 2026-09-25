# 交付物④：key-name错配修复清单

> 工单：DSH_B_MERGE_HIST_IND_P3_REV | 日期：2026-09-24

---

## 检测概况

- 检测到key-name不匹配条目：**4条**
- 处理方式：标记为 `FLAGGED_FOR_REVIEW`，未静默修改
- FT主脑要求：逐条修正（本工单仅标记+上报，修正需业务确认）

## 错配条目详情

| # | Key | 指标名称 | 错配类型 | 处置 |
|---|-----|----------|----------|------|
| 1 | `al_2_scrap_al_import_source` | 易拉罐盖料：产量：中国（年） | al_key_no_aluminum_name | FLAGGED_FOR_REVIEW |
| 2 | `li_52_battery` | 动力电池装车量宁德时代（月） | li_key_no_lithium_name | FLAGGED_FOR_REVIEW |
| 3 | `li_52_ev_sales` | SMM新能源汽车销量（月） | li_key_no_lithium_name | FLAGGED_FOR_REVIEW |
| 4 | `ni_45_output_2` | MHP：以金属量计：产量：印尼（月） | ni_key_no_nickel_name | FLAGGED_FOR_REVIEW |

---

## 补充说明

- 初始审计发现16条疑似错配，其中12条经人工复核为"语义邻近"（如ni_*指标包含不锈钢相关名称，属于镍产业链下游）
- 剩余4条为真错配，已标记
- `li_52_ev_sales`/`li_52_battery`：新能源汽车相关，属于锂产业链下游，建议归类为锂衍生指标
- `ni_45_output_2`：MHP（混合硫酸镍）产量，属于镍冶炼中间品，建议归类为镍衍生指标
- `al_2_scrap_al_import_source`：易拉罐盖料产量，属于铝再生，建议归类为铝再生指标