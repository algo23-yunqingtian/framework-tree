# T2 交付物 MD5 清单

> 任务：`DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN`  
> 分支：`feature/v85-chart-template`  
> 目录：`analysis/e2e_output/v85/dshe_alias_audit_design/`  
> 约束：未修改 `indicator_alias_library.csv` / `indicators_v1.json` / GT / 黑名单；0 次 zhiji API 调用

## 1. 七份指定交付物

| # | 文件 | 字节 | MD5 |
|---|---|---|---|
| 1 | `alias_sampling_audit_report.md` | 12,129 | `11301D1AE74871BD8D04608E95DC2DFE` |
| 2 | `alias_audit_sample.csv` | 64,827 | `819CB85ACEEF9D859B7792302DE7B890` |
| 3 | `canonical_resolve_fix_design.md` | 14,236 | `C5699EBB613E44E11D5B2E704882C71D` |
| 4 | `high_prio_ambig_analysis.md` | 13,401 | `EB2D55C6992786E4BCCD6AA77C7DED34` |
| 5 | `multi_canonical_conflict_solution.md` | 18,002 | `4E193881C40D30F22C010BF784F9D6AC` |
| 6 | `v86_alias_engine_full_design.md` | 17,593 | `DC8F943DE4E10E7DAA7FEFBEAA9963CD` |
| 7 | `alias_test_case_set.json` | 768,363 | `271C374BED5C59FAAC34F47B4C7376B0` |

## 2. 配套产物（脚本 / 中间结果 / 测试产物）

| # | 文件 | 字节 | MD5 |
|---|---|---|---|
| 1 | `T2_summary_report.md` | 9,467 | `71C16999D82B576CC41AD9B96DF42F27` |
| 2 | `audit_kit.py` | 17,676 | `80415E415F0FBCDB2CE441542D53BFE6` |
| 3 | `build_sampling_audit.py` | 27,838 | `E18820672D32F6F598EEC45EEFDB0DF8` |
| 4 | `build_test_case_set.py` | 15,954 | `60D749C3BC55964C100D08AC1A32A258` |
| 5 | `canonical_resolve_fix.py` | 37,066 | `CAD1F0420BE1ABA0FABB76E86212B779` |
| 6 | `canonical_resolve_fix_result.json` | 14,007 | `978E2832B56167B7AF50ED9D077C8A5D` |
| 7 | `blacklist_coverage_analysis.py` | 6,894 | `C96C142A88FC57394B67B399A8AD6E44` |
| 8 | `blacklist_rule_coverage_matrix.csv` | 10,191 | `810FE8A11ACE2683584D86A2A64E29A3` |
| 9 | `blacklist_testset_verdicts.py` | 5,514 | `B0D1FB553E8447F4BF0F90A1103DC445` |
| 10 | `blacklist_testset_verdicts.csv` | 5,538 | `8E214936FDDC3DDAA197B02FBAC032B5` |
| 11 | `blacklist_rule_testing_design.md` | 19,916 | `E84EBF23A4A5BD3C68F865BAF5B829BB` |
| 12 | `blacklist_rule_effectiveness_test.py` | 46,868 | `97404AB126EA15DB4E489DA2AB4C3E98` |
| 13 | `blacklist_rule_test_result.json` | 171,493 | `09340481D52866445977E0FE143D3BBB` |
| 14 | `blacklist_rule_test_result.md` | 16,724 | `1376043EAF70CFC32CEDA74CD64F7B43` |
| 15 | `regression_gate_config.json` | 5,250 | `AA0F1EC4685ED8B8C59DA946A5CE26DA` |
| 16 | `generate_conflict_classification.py` | 5,183 | `70CFDAF8AF43AD88B622D9D17A19D05F` |
| 17 | `multi_canonical_conflicts_165.csv` | 85,121 | `4EC7B2236B33C9BF9E43EA99A63F89CC` |
| 18 | `multi_canonical_conflict_classification.csv` | 63,411 | `8DC5826939BF152017D071C2A21C1FE8` |
| 19 | `sampling_audit_result.json` | 38,898 | `92931A61C2E7FCCA1F904497333C51B3` |
| 20 | `v86_gate_fusion_framework.md` | 20,094 | `26FFD097215779AE304C043B0A8B3783` |

## 3. 汇总

- 指定交付物：7 / 7 全部存在
- 配套产物：20
- 合计文件：27
- 合计字节：1,531,654

---

```
NO_SOURCE_MODIFICATION=TRUE
NO_GT_MODIFICATION=TRUE
NO_RULE_MODIFICATION=TRUE
NO_ZHIJI_API_CALL=TRUE
READ_ONLY=TRUE
APPEND_ONLY=TRUE
HISTORICAL_ARTIFACTS_PRESERVED=TRUE
```
