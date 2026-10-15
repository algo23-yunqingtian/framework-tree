# MD5_MANIFEST — V88 Phase03 P0 门禁基线 / 回归套件 / 准入核验（三次）

> **TASK_ID**: V88_PHASE03_P0_R2_GATE_BASELINE_AND_REGRESSION + V88_PHASE03_P0_OVERALL_ADMISSION_GATE_CHECK + V88_PHASE03_P0_RERUN_OVERALL_ADMISSION_GATE + V88_PHASE03_P0_RERUN_ADMISSION_GATE_AFTER_SCHEMA_FIX
> **生成时间**: 2026-10-15
> **三次准入结论轨迹**: ①CONDITIONAL_PASS D-7=0% / ②CONDITIONAL_PASS D-7=0% BLOCKED3 / ③CONDITIONAL_PASS D-7=0% BLOCKED2 A-3解除
> **第三次准入核心**: phase03_test.db 已重建（110MB/475593行/615指标/0错误）, 双键映射命中84/109=77.06%≥60% ✅, R-09隔离达标 ✅, A-3解除 ✅；但引擎数据源路径硬编码scripts/api_cache.db+schema不兼容(R-V88-030) → D-7仍0%, B-3/C-3未解除
> **门禁计数**: 21 项主门禁（矩阵基准）/ 40 项阶段门禁（矩阵基准）；results 实测主门禁 22 条（S-4 拆分 S-4a+S-4b）/ 阶段门禁 41 条

| # | 文件 | MD5 | 字节 |
|---|------|-----|-----:|
| 1 | `scripts/p0_gate_checker.py` | `F8ADA7681B2FB9A84752F5D694F8F57A` | 47133 |
| 2 | `scripts/p0_full_regression_suite.py` | `C8B492364A04EF2587615D7BCA7F183C` | 29458 |
| 3 | `scripts/p0_baseline_metrics.json` | `F0479C029B76B131328B1550DE2C75F7` | 9359 |
| 4 | `scripts/p0_overall_regression_result.json` | `DCBB77FE39E31148988856B8E82DCB71` | 9673 |
| 5 | `scripts/p0_rerun_regression_result.json` | `3198B7A4F42B1C129339C3733331E404` | 9673 |
| 6 | `scripts/p0_third_regression_result.json` | `B1D640D136ECA372794B0443A5533AC6` | 9632 |
| 7 | `p0_overall_gate_result.json` | `85039E217906CD78E029ACE0A417CE63` | 26492 |
| 8 | `p0_rerun_gate_result.json` | `FE0C60DF6D41296675E34FC6E7E59DFD` | 26492 |
| 9 | `p0_third_gate_result.json` | `A73187872AF5E7E8884633135DF99D52` | 26494 |
| 10 | `v88_phase03_p0_gate_baseline_report.md` | `2F452D994FBEC8CA8F10CB74C9E96810` | 21039 |
| 11 | `v88_phase03_p0_overall_admission_report.md` | `81BB1DD42EB0AE3F862AB9AD937C8757` | 17615 |
| 12 | `v88_phase03_p0_rerun_admission_report.md` | `7215E4108ADF959097BC82FE8C2736DB` | 13661 |
| 13 | `v88_phase03_p0_third_admission_report.md` | `5C4A8DDE116A3DAC76F4D15D8B3C3718` | 17676 |

> **MD5 口径**: LF 规范化后计算（顶层规划 §1.2 规范）。
> **NO_OVERWRITE**: Phase02 / Phase03-review 既有资产 MD5 零修改（`v88_phase03_merged_risk_list.md` §8/§9/§10/§11 为 append-only 追加）。
> **只读声明**: `scripts/api_cache.db` 仅只读校验（A-2 用例），**未写入**（28,672 B / 3 行 / code=AO / 时间戳 9/9 三轮未变）。Phase02 生产链路零修改。
> **phase03_test.db 未入库**: AGENTS.md §7 红线「❌ 不推 *.db 到 GitHub」，110,252,032 字节的独立库仅存在于运行时环境。HERMEShf 以 DSHB 的 `import_all_to_testdb.py` 脚本重建方式验证（14.0 秒 / 0 错误 / 0 主键冲突）。此为 R-V88-031 流程风险。
> **check_html**: 266/266 页 PASS。
> **协作说明**: DSHB 交付 `import_all_to_testdb.py` / `verify_testdb.py` / `phase03_testdb_coverage_report.json` / `v88_phase03_p0_independent_testdb_ingest_report.md`（commit 21f4820）；DSHE 交付 `v88_phase03_p0_real_render_verify.py` / `v88_phase03_p0_real_render_metrics.json`（commit 3e2cd66）；均不计入本工单 MD5 清单。
