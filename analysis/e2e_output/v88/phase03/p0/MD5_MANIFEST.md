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

---

## DSHB 数据侧归档（V88_PHASE03_P0_DSHB_ARTIFACT_ARCHIVE）

> **追加时间**: 2026-10-15
> **追加内容**: DSHB P0 阶段收尾，固化重建脚本/校验脚本/映射清单/口径文档/风险台账

| # | 文件 | MD5 | 字节 |
|---|------|-----|-----:|
| 14 | `scripts/rebuild_phase03_testdb.py` | `717A0B9BEEDD421F368E9A6D9AE88A1F` | 7464 |
| 15 | `scripts/verify_testdb.py` | `FE6B5470C6480D220B6A8427D2145467` | 13374 |
| 16 | `scripts/export_mapping_list.py` | `B6A7E0F5AAAF11CB144C512E2582EE39` | 11479 |
| 17 | `v88_phase03_p0_metric_caliber_definition.md` | `7415BA6D72D99AE57F5AF6B66A0ABDF2` | 6880 |
| 18 | `v88_phase03_p0_metric_indicator_code_mapping.md` | `BDF859EDC090C98FF021717DC417A911` | 57561 |
| 19 | `v88_phase03_p0_metric_indicator_code_mapping.json` | `F91C6FA0AEC2C2C90AC49E0F900BB1A5` | 157757 |
| 20 | `v88_phase03_data_risk_list.md` | `0F2D27BF437DF9EBADCD2658BFCA8D73` | 6749 |
| 21 | `v88_phase03_p0_dshb_archive_report.md` | `8C360F1623A1BAF76C53EFC75EC369AF` | 6557 |

> **DSHB 归档核心**: rebuild_phase03_testdb.py 一键重建 + verify_testdb.py 9项校验全通过 + 映射清单615条完整导出 + 口径说明文档清晰区分DB映射命中率(77.06%) vs 引擎D7覆盖率(0%) + 数据侧风险9项全部闭环
> **R-V88-031 缓解**: phase03_test.db 无需推送，rebuild_phase03_testdb.py 可在任意节点一键复现
> **数据侧风险闭环**: R-V88-025 CLOSED / R-V88-028 CLOSED / R-V88-029 CLOSED / R-V88-031 MITIGATED


### V88_PHASE03_P0_R1_ENGINE_ADAPT_FIX (DSHE)
| 文件 | MD5 | 大小(B) |
|------|:---:|:------:|
| scripts/node_binding_engine.py | `cd73deaeec54a7f1f8bde92c1300a9dc` | 45,411 |
| analysis/e2e_output/v88/phase03/p0/v88_phase03_p0_engine_adapt_fix_report.md | `480b486c872c7cef09c11eb937d7ab20` | 11,748 |
| analysis/e2e_output/v88/phase03/p0/v88_phase03_visual_risk_list.md | `d394ddee9e749ffde6e2606502e9f7f1` | 14,507 |
| STATUS.md | `ed6f4c71bf7b26ef49655673693d5b37` | 1,047,997 |
| analysis/e2e_output/v88/JOB_READY.flag | `762adde951011c7a56714e402ea0d4d9` | 52,467 |

### V88_PHASE03_P0_DSHB_WATCHER_TASK (DSHB)
| 文件 | MD5 | 大小(B) |
|------|:---:|:------:|
| analysis/e2e_output/v88/phase03/p1/dshb/v88_phase03_p1_dshb_prematerials.md | `B832C604AE3EAD20B5A03CEE3D2824F7` | 7,215 |
| STATUS.md | `UPDATED` | — |
| analysis/e2e_output/v88/JOB_READY.flag | `UPDATED` | — |

> **DSHB 值守核心**: 归档脚本7个文件MD5全匹配锁定 / DSHE引擎修复确认(D7=78.82% PASS) / P1前置资料就绪(指标基线615/映射基线608/风险11项全闭环) / PHASE03_P0_DSHB_WATCHER=TRUE 待命等待P1工单
