# MD5_MANIFEST — V88 Phase03 P0 门禁基线 / 回归套件 / 整体准入核验

> **TASK_ID**: V88_PHASE03_P0_R2_GATE_BASELINE_AND_REGRESSION + V88_PHASE03_P0_OVERALL_ADMISSION_GATE_CHECK
> **生成时间**: 2026-10-15
> **准入结论**: CONDITIONAL_PASS（D-7 覆盖率 0.0000% 未达 60%，P0 准入不通过，P1 工单不可下发）
> **门禁计数**: 21 项主门禁（矩阵基准）/ 40 项阶段门禁（矩阵基准）；results 实测主门禁 22 条（S-4 拆分 S-4a+S-4b）/ 阶段门禁 41 条

| # | 文件 | MD5 | 字节 |
|---|------|-----|-----:|
| 1 | `scripts/p0_gate_checker.py` | `F8ADA7681B2FB9A84752F5D694F8F57A` | 47133 |
| 2 | `scripts/p0_full_regression_suite.py` | `C8B492364A04EF2587615D7BCA7F183C` | 29458 |
| 3 | `scripts/p0_baseline_metrics.json` | `019B4481720E8025089CC0BA4594CCE0` | 9357 |
| 4 | `scripts/p0_overall_regression_result.json` | `DCBB77FE39E31148988856B8E82DCB71` | 9673 |
| 5 | `p0_overall_gate_result.json` | `85039E217906CD78E029ACE0A417CE63` | 26492 |
| 6 | `v88_phase03_p0_gate_baseline_report.md` | `2F452D994FBEC8CA8F10CB74C9E96810` | 21039 |
| 7 | `v88_phase03_p0_overall_admission_report.md` | `81BB1DD42EB0AE3F862AB9AD937C8757` | 17615 |

> **MD5 口径**: LF 规范化后计算（顶层规划 §1.2 规范）。
> **NO_OVERWRITE**: Phase02 / Phase03-review 既有资产 MD5 零修改（`v88_phase03_merged_risk_list.md` §8/§9 为 append-only 追加）。
> **只读声明**: `scripts/api_cache.db` 仅只读校验（A-2 用例），未写入。Phase02 生产链路零修改。
> **check_html**: 266/266 页 PASS。
> **协作说明**: `db_import_jsonl.py` / `db_load.py` / `test_db_setup.py` / `validate_report.py` / `cache_coverage_calc.py` 为 P0-R0/P0-R1 并行工单（DSHB/DSHE）交付，不计入本工单 MD5 清单。
