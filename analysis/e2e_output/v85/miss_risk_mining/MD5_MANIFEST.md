# V85 Miss Risk Mining — MD5清单

**生成时间**: 2026-10-01 12:34:25
**任务**: DSH-B_V85_MISS_RISK_ROOTCAUSE_MINING_AND_BLACKLIST_BOUNDARY_EXPAND
**输出路径**: analysis/e2e_output/v85/miss_risk_mining/

---

## 输出文件清单

| # | 文件名 | 大小(bytes) | MD5 |
|---|--------|-------------|-----|
| 1 | p0_miss_4_case_analysis.md | 10,929 | `586bac3921b0a190c10e0c5c66489ba2` |
| 2 | p0_unhit_5_items_report.md | 10,037 | `36c7b213816d5e4f064e32374f16046e` |
| 3 | blacklist_boundary_testset.json | 11,489 | `bba79ab946b4d0d584406216e6d81455` |
| 4 | blacklist_extend_candidate_v2.json | 7,037 | `1489cda7f7d6fc8c78cb5611653832cd` |
| 5 | unified_indicator_risk_db_v2.csv | 47,296 | `fbde5245b225876445fc0af72e926ef7` |
| 6 | dsh_gate_self_check_v2.md | 6,916 | `149107ecea95ef17874e4045b6a15272` |
| 7 | rule_defect_summary.md | 7,748 | `1d445da6ccec7c0a834518810338c420` |
| 8 | build_miss_risk_mining.py | 75,442 | `ec462598cdd9768ba0ebb5c893cc4374` |

## 约束声明

| 约束 | 状态 |
|------|------|
| NO_PRODUCTION_MODIFICATION | ✅ semantic_blacklist_v85_final.json未被修改 |
| NO_SOURCE_MODIFICATION | ✅ GT/原始模板/indicators_v1.json未修改 |
| NO_GT_MODIFICATION | ✅ GT未修改 |
| NO_ZHIJI_API_CALL | ✅ 未调用任何时序数据API |
| APPEND_ONLY | ✅ 仅新增文件，未覆盖历史产物 |
| 输出为候选文件 | ✅ 仅输出候选规则，未修改生产黑名单 |

---

**约束声明**: NO_PRODUCTION_MODIFICATION=true, NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true, NO_ZHIJI_API_CALL=true