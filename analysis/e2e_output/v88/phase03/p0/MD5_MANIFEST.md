# MD5_MANIFEST — V88 Phase03 P0 门禁基线与回归套件

> **TASK_ID**: V88_PHASE03_P0_R2_GATE_BASELINE_AND_REGRESSION
> **BASELINE HEAD**: e3673f2 | **生成时间**: 2026-10-15
> **重跑**: P0-R1 并行工单 db_import_jsonl.py / db_load.py 就位后重跑，A-6 由 BLOCKED 转 PASS（BLOCKED 4→3）

| # | 文件 | MD5 | 字节 |
|---|------|-----|-----:|
| 1 | `scripts/p0_gate_checker.py` | `3726664ED2096BDDD07DF42F9FF1896A` | 45432 |
| 2 | `scripts/p0_full_regression_suite.py` | `C8B492364A04EF2587615D7BCA7F183C` | 29458 |
| 3 | `scripts/p0_baseline_metrics.json` | `673BEC95CF59F5ADEB789BEA4D3FA241` | 9361 |
| 4 | `scripts/p0_regression_results.json` | `66A6765CBE5B79364F21433C44E1A704` | 9673 |
| 5 | `v88_phase03_p0_gate_baseline_report.md` | `2F452D994FBEC8CA8F10CB74C9E96810` | 21039 |

> **MD5 口径**: LF 规范化后计算（顶层规划 §1.2 规范）。
> **NO_OVERWRITE**: Phase02 / Phase03-review 既有资产 MD5 零修改（`v88_phase03_merged_risk_list.md` §8 为 append-only 追加）。
> **只读声明**: `scripts/api_cache.db` 仅只读校验（A-2 用例），未写入。Phase02 生产链路零修改。
> **check_html**: 266/266 页 PASS。
> **P0-R1 协作说明**: `scripts/db_import_jsonl.py` / `scripts/db_load.py` / `scripts/test_db_setup.py` 为 P0-R1 并行工单（DSHE）交付，不计入本工单 MD5 清单。
