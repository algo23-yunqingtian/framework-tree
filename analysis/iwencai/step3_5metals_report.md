# 5 金属 Step3 知几 search 初筛报告

## 汇总

- 唯一候选指标查询：1345
- 有 zhiji 命中：1345 (100.0%)
- 分层：Tier A 782 / Tier B 233 / Tier C 330

## 分品种

| 品种 | 节点 | 唯一查询 | 有命中 | 命中率 | A | B | C |
|---|---:|---:|---:|---:|---:|---:|---:|
| ZN 锌 | 30 | 268 | 268 | 100.0% | 111 | 43 | 114 |
| NI 镍 | 30 | 327 | 327 | 100.0% | 233 | 56 | 38 |
| SI 工业硅 | 30 | 278 | 278 | 100.0% | 163 | 46 | 69 |
| SN 锡 | 30 | 298 | 298 | 100.0% | 172 | 61 | 65 |
| LI 锂 | 30 | 174 | 174 | 100.0% | 103 | 27 | 44 |

## 说明

- Tier A：search 命中的最佳项达到强匹配阈值（品种词 + 关键词/SMM 源），可进入后续候选精修。
- Tier B：有可查候选但需抽查口径/频率/单位。
- Tier C：无命中、弱命中、疑似误配或查询本身为衍生指标，暂入备用库/需改关键词。

## 输出文件

- `analysis/iwencai/step3_5metals_candidates.json`
- `analysis/iwencai/step3_5metals_search_results.json`
- `analysis/iwencai/step3_5metals_summary.json`
