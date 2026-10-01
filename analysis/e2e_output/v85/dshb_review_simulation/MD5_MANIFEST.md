# MD5 清单 — DSH-B_V85_HUMAN_REVIEW_SIMULATION_AND_PRECHECK

> 生成时间: 2026-10-01 15:38:08
> 分支: `feature/v85-chart-template`
> 输出目录: `analysis/e2e_output/v85/dshb_review_simulation/`

## 交付产物

| # | 文件 | 大小 | MD5 |
|---|------|------|-----|
| 1 | `sim_sceneA_result.csv` | 11,953 B | `f981388a614692bc146924ac0bc6c4de` |
| 2 | `sim_sceneB_result.csv` | 12,972 B | `148bca5f0562fa7f644c718131f21e3b` |
| 3 | `simulation_compare_report.md` | 7,023 B | `4873fa368ad3c90618b98aefaef81fa2` |
| 4 | `review_consistency_check.py` | 15,777 B | `25cde96e56aea9c19b5025d685ce22e9` |
| 5 | `review_consistency_guide.md` | 6,114 B | `22bf3c9dc757dd3035283428c8fc26c3` |
| 6 | `bl009a_multi_scenario_verify.md` | 5,190 B | `579e5d12b855ee05aac05d0c3652efad` |
| 7 | `gate_block_impact_analysis.md` | 9,719 B | `a4377f9eeb9b337cd6397403a5e0f5ca` |
| 8 | `human_review_faq.md` | 9,915 B | `4de133375906327366ffd49d9a6b8b09` |
| 9 | `build_review_simulation.py` | 102,117 B | `126201e887e1921a0ce51460bec09d1e` |

## 输入文件（未修改）

| 文件 | MD5 |
|------|-----|
| `v85_p0_risk_human_workbook.csv` | `cafdbe53c6fdfe88bfdf0261e0381042` |
| `gate_block_tracker.csv` | `351743dbe9cba275f36a0c3a21feb746` |
| `blacklist_boundary_testset.json` | `bba79ab946b4d0d584406216e6d81455` |
| `semantic_blacklist_v85_final.json` | `1e1bdf48a7734bce50df263ce4c3ef1a` |
| `cross_variety_p0_validation.csv` | `d550bfb8de713dd9d137d66a05c4279c` |
| `blacklist_extend_candidate_v2.json` | `1489cda7f7d6fc8c78cb5611653832cd` |

## 校验约束

| 约束 | 状态 |
|------|------|
| 不修改原始风险库 | ✅ 确认 |
| 不修改黑名单 | ✅ 确认 |
| 不修改人工工作表源文件 | ✅ 确认 |
| GT/indicators_v1.json只读 | ✅ 确认 |
| 禁止调用zhiji API | ✅ 确认 |
| 历史交付产物全部保留 | ✅ 确认 |
| 仅新增文件，不覆盖 | ✅ 确认 |
