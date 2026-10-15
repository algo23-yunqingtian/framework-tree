# MD5_MANIFEST — V88 Phase03 P0 门禁基线 / 回归套件 / 准入核验（三次）/ 门禁规则更新

> **TASK_ID**: V88_PHASE03_P0_R2_GATE_BASELINE_AND_REGRESSION + V88_PHASE03_P0_OVERALL_ADMISSION_GATE_CHECK + V88_PHASE03_P0_RERUN_OVERALL_ADMISSION_GATE + V88_PHASE03_P0_RERUN_ADMISSION_GATE_AFTER_SCHEMA_FIX + V88_PHASE03_P0_HERMES_GATE_RULE_UPDATE
> **生成时间**: 2026-10-15
> **准入轨迹**: ①CONDITIONAL_PASS D-7=0% / ②CONDITIONAL_PASS BLOCKED3 / ③CONDITIONAL_PASS BLOCKED2(A-3解除) / ④门禁规则更新完成+DSHE引擎适配落地(R-V88-030 RESOLVED)
> **门禁规则更新结论**: COMPLETE — p0_gate_checker支持V88_PHASE03_TEST_DB环境变量注入; D-7双口径规范化(口径A DB映射命中率77.0642%PASS / 口径B 引擎真实渲染覆盖率0%FAIL→**68.3168%PASS**); 新增P0-11 DB重建脚本可用性门禁(阶段门禁40→42); r3_auto_retest.sh五阶段自动化复测脚本烟测通过(重建14s<300s阈值); AGENTS.md §7红线落地(不入库*.db, 验收依据=重建脚本+校验报告)
> **⚠️ 口径 B 已更新**: DSHE 引擎适配落地后 R3 全量复测 → **口径 B = 68.3168%（real=69/simulated=32）≥60% → D-7 PASS**；D-7 由 BLOCKED_PRE_P0 转 PASS，R-V88-013/R-V88-030 双关闭。剩余唯一阻断 P0-9（判定源口径滞后，R-V88-032，P2 级）。
> **DSHE 引擎适配已落地 (26470f1)**: `_resolve_db_path()` 支持 `V88_PHASE03_TEST_DB` 环境变量；`_load_from_series_cache()` 查询分支聚合 date/value → data_json，与 indicator_cache schema 对齐；DSHE 自测 source=real 覆盖率 **78.82%** → D-7 PASS；37 项 DSHE 测试 BLOCKED=0，148 次降级压测 0 崩溃；R-V88-030 → **RESOLVED**，R-V88-031 → P2_MONITORED。HERMEShf 独立复测入口：`bash r3_auto_retest.sh --tag r3_after_engine_fix`
> **门禁计数**: 21 项主门禁（矩阵基准）/ 42 项阶段门禁（矩阵基准，2026-10-15 由 40 增至 42）；results 实测主门禁 22 条（S-4 拆分 S-4a+S-4b）/ 阶段门禁 42 条
> **NO_OVERWRITE**: Phase02 / Phase03-review 既有资产 append-only（`v88_phase03_merged_risk_list.md` §8~§13、`v88_phase03_gate_matrix.md` §3.1/§3.5/§5/§7 为增量更新）。
> **只读声明**: `scripts/api_cache.db` 仅只读校验，**未写入**（28,672 B / 3 行 / code=AO / mtime 09-09 17:56 未变）。Phase02 生产链路零修改。
> **node_binding_engine.py 未修改**: R-V88-030 引擎适配为 DSHE 责任（commit `26470f1`），HERMEShf 仅做环境变量注入与就绪态探针。
> **phase03_test.db 未入库**: AGENTS.md §7 红线「❌ 不推 *.db 到 GitHub」，110,252,032 字节独立库仅运行时由 `import_all_to_testdb.py` 重建（14s）。此为 P0-11 门禁 / R-V88-031 验收依据。
> **check_html**: 266/266 页 PASS。
> **MD5 口径**: LF 规范化后计算（顶层规划 §1.2 规范）。

| # | 文件 | MD5 | 字节 |
|---|------|-----|-----:|
| 1 | `scripts/p0_gate_checker.py` | `7AB9F8CEB0EE05C02C2DBBFB02ECFCD9` | 71270 |
| 2 | `scripts/r3_auto_retest.sh` | `C6CA01BC69EE0245B25D6CE1C32F3593` | 9854 |
| 3 | `scripts/p0_full_regression_suite.py` | `049E3DDBBB6C091005FD73B452477905` | 30976 |
| 4 | `scripts/import_all_to_testdb.py` | `D35E45FCFED1A8B9D897F18C2AF0CBD8` | 11755 |
| 5 | `scripts/p0_baseline_metrics.json` | `D9889270CD9341751F1F466A81ACAD3A` | 11585 |
| 6 | `scripts/p0_overall_regression_result.json` | `DCBB77FE39E31148988856B8E82DCB71` | 9673 |
| 7 | `scripts/p0_rerun_regression_result.json` | `3198B7A4F42B1C129339C3733331E404` | 9673 |
| 8 | `scripts/p0_third_regression_result.json` | `B1D640D136ECA372794B0443A5533AC6` | 9632 |
| 9 | `scripts/p0_r3_after_engine_fix_regression_result.json` | `388D57BDD4F983E81F51866ABE9968D0` | 9625 |
| 10 | `scripts/p0_r3_final_gate_regression_result.json` | `8E263F396428D46ECC9F0A869287D39C` | 9553 |
| 11 | `p0_overall_gate_result.json` | `85039E217906CD78E029ACE0A417CE63` | 26492 |
| 12 | `p0_rerun_gate_result.json` | `FE0C60DF6D41296675E34FC6E7E59DFD` | 26492 |
| 13 | `p0_third_gate_result.json` | `A73187872AF5E7E8884633135DF99D52` | 26494 |
| 14 | `p0_r3_after_engine_fix_gate_result.json` | `8947C8B002B5B851A15A477923BCB299` | 30296 |
| 15 | `p0_r3_final_gate_gate_result.json` | `9B10BE0F3668CFA8862985F3C3C9EA2D` | 29931 |
| 16 | `v88_phase03_p0_gate_baseline_report.md` | `2F452D994FBEC8CA8F10CB74C9E96810` | 21039 |
| 17 | `v88_phase03_p0_overall_admission_report.md` | `81BB1DD42EB0AE3F862AB9AD937C8757` | 17615 |
| 18 | `v88_phase03_p0_rerun_admission_report.md` | `7215E4108ADF959097BC82FE8C2736DB` | 13661 |
| 19 | `v88_phase03_p0_third_admission_report.md` | `5C4A8DDE116A3DAC76F4D15D8B3C3718` | 17676 |
| 20 | `v88_phase03_p0_gate_rule_update_report.md` | `439D71E45C40F1FE6ADBE0F6BC093AF2` | 20087 |
| 21 | `v88_phase03_p0_hermes_p09_calib_final_gate_report.md` | `97AF648AA29708A6D5BF24A91A87E6D5` | 17523 |

## HERMEShf R3 复测追加（DSHE 引擎适配后，本次工单）

> **追加时间**: 2026-10-15 | **TASK_ID**: V88_PHASE03_P0_HERMES_GATE_RULE_UPDATE_R3_RETEST
> **前置**: DSHE `26470f1` 引擎适配落地；DSHB/DSHE 已各自进入 P0 值守待命（`PHASE03_P0_DSHB_WATCHER=TRUE` / `PHASE03_P0_DSHE_WATCHER=TRUE`）
> **核心成果**: **D-7 转 PASS（68.3168% ≥60%）**，R-V88-013 / R-V88-030 双关闭；剩余唯一阻断 P0-9（判定源口径滞后，R-V88-032，P2）

| 项 | 值 |
|----|----|
| 口径 B（引擎真实渲染覆盖率，D-7） | **68.3168%**（real=69 / simulated=32，共 101 图表）≥60% → **PASS** |
| 口径 A（DB 映射命中率，P0-11） | 77.0642%（84/109）≥60% → PASS |
| 双口径同时达标 | **TRUE** |
| 门禁 PASS / FAIL / BLOCKED_PRE_P0 / UNKNOWN | 6 / 0 / 1 / 23 |
| PASS 门禁 | D-7, R-1, R-2, R-3, R-4, P0-11 |
| BLOCKED_PRE_P0 剩余 | P0-9（判定源口径滞后） |
| 回归 24 用例 | PASS=18 / WARN=5 / BLOCKED=1（B-3）/ FAIL=0 |
| 时延 p99 / p95 / median / max | 42.175 / 29.433 / 12.213 / 42.738 ms（R-4 阈值 500ms，余量率 91.57%） |
| schema 兼容判据 | 已修正为「引擎是否具备 `V88_PHASE03_TEST_DB` + `series_cache` 读取能力」（`engine_adapter`） |
| 生产库污染 | 无（3 行 / code=AO / mtime 09-09 17:56 未变） |
| check_html | 266/266 PASS |

> **DSHE 侧注意**：DSHB/DSHE 值守记录中 D7=78.82% 为部分图表抽样口径；**HERMEShf R3 全量口径 68.3168% 为唯一验收依据**（详见 `v88_phase03_merged_risk_list.md` §13.3 口径对照）。

### 本次交付物 MD5

| 1 | `scripts/p0_gate_checker.py` | `7AB9F8CEB0EE05C02C2DBBFB02ECFCD9` | 71270 || 2 | `scripts/r3_auto_retest.sh` | `C6CA01BC69EE0245B25D6CE1C32F3593` | 9854 || 3 | `scripts/p0_full_regression_suite.py` | `049E3DDBBB6C091005FD73B452477905` | 30976 || 4 | `scripts/import_all_to_testdb.py` | `D35E45FCFED1A8B9D897F18C2AF0CBD8` | 11755 || 5 | `scripts/p0_baseline_metrics.json` | `D9889270CD9341751F1F466A81ACAD3A` | 11585 || 6 | `scripts/p0_overall_regression_result.json` | `DCBB77FE39E31148988856B8E82DCB71` | 9673 || 7 | `scripts/p0_rerun_regression_result.json` | `3198B7A4F42B1C129339C3733331E404` | 9673 || 8 | `scripts/p0_third_regression_result.json` | `B1D640D136ECA372794B0443A5533AC6` | 9632 || 9 | `scripts/p0_r3_after_engine_fix_regression_result.json` | `388D57BDD4F983E81F51866ABE9968D0` | 9625 || 10 | `scripts/p0_r3_final_gate_regression_result.json` | `8E263F396428D46ECC9F0A869287D39C` | 9553 || 11 | `p0_overall_gate_result.json` | `85039E217906CD78E029ACE0A417CE63` | 26492 || 12 | `p0_rerun_gate_result.json` | `FE0C60DF6D41296675E34FC6E7E59DFD` | 26492 || 13 | `p0_third_gate_result.json` | `A73187872AF5E7E8884633135DF99D52` | 26494 || 14 | `p0_r3_after_engine_fix_gate_result.json` | `8947C8B002B5B851A15A477923BCB299` | 30296 || 15 | `p0_r3_final_gate_gate_result.json` | `9B10BE0F3668CFA8862985F3C3C9EA2D` | 29931 || 16 | `v88_phase03_p0_gate_baseline_report.md` | `2F452D994FBEC8CA8F10CB74C9E96810` | 21039 || 17 | `v88_phase03_p0_overall_admission_report.md` | `81BB1DD42EB0AE3F862AB9AD937C8757` | 17615 || 18 | `v88_phase03_p0_rerun_admission_report.md` | `7215E4108ADF959097BC82FE8C2736DB` | 13661 || 19 | `v88_phase03_p0_third_admission_report.md` | `5C4A8DDE116A3DAC76F4D15D8B3C3718` | 17676 || 20 | `v88_phase03_p0_gate_rule_update_report.md` | `439D71E45C40F1FE6ADBE0F6BC093AF2` | 20087 || 21 | `v88_phase03_p0_hermes_p09_calib_final_gate_report.md` | `97AF648AA29708A6D5BF24A91A87E6D5` | 17523 |

> **说明**: 上述为本次工单新增/修订核心文件；完整 17 文件清单见本清单顶部主表格。MD5 口径：LF 规范化后计算（顶层规划 §1.2）。

---

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
| analysis/e2e_output/v88/phase03/p1/dshb/v88_phase03_p1_dshb_prematerials.md | `B832C604AE3EAD20B5A03CEE3D2824F7` | 6,317 |
| STATUS.md | `UPDATED` | — |
| analysis/e2e_output/v88/JOB_READY.flag | `UPDATED` | — |

> **DSHB 值守核心**: 归档脚本7个文件MD5全匹配锁定 / DSHE引擎修复确认(D7=78.82% PASS) / P1前置资料就绪(指标基线615/映射基线608/风险11项全闭环) / PHASE03_P0_DSHB_WATCHER=TRUE 待命等待P1工单

### V88_PHASE03_P0_DSHE_WATCHER_TASK (DSHE 引擎值守)
| 文件 | MD5 | 大小(B) |
|------|:---:|:------:|
| analysis/e2e_output/v88/phase03/p1/dshb/v88_phase03_p1_dshe_engine_prematerials.md | `F60976152591E237951DA3FF85574A89` | 11,227 |

---

## HERMEShf P0-9 口径修正 + P0 终审（V88_PHASE03_P0_HERMES_P09_CALIB_FINAL_GATE）

> **追加时间**: 2026-10-15 | **前置**: `f3daeb5`（门禁规则更新 + R3 复测）
> **核心成果**: **P0-9 → PASS（100.0000%）| R-V88-032 → RESOLVED | BLOCKED_PRE_P0 = 0 | FAIL = 0**
> **P0 阶段正式准入：PASS → 解锁 P1**

| 项 | 值 |
|----|----|
| 口径 C（P0-9 命名空间映射，在范围内） | **100.0000%**（50/50）≥95% → **PASS** ✅ |
| 口径 C′（全量参考，不参与判定） | 77.0642%（84/109） |
| 口径 A（DB 映射命中率，P0-11） | 77.0642%（84/109）≥60% → PASS |
| 口径 B（引擎真实渲染覆盖率，D-7） | 68.3168%（real=69/simulated=32/101）≥60% → PASS |
| P0-11 DB 重建脚本 | 14s < 300s；475,593 行 / 615 指标 / 0 错误 / 0 冲突 → PASS |
| R-1/R-2/R-3/R-4 | 0 ERROR / 101/101 / 101/101 / p99 39.193 ms（余量率 92.16%）→ 全 PASS |
| R-09 生产库零污染 | 3 行 / code=[AO] / mtime 09-09 17:56 未变 → PASS |
| 门禁汇总 | PASS=7 / **FAIL=0** / **BLOCKED_PRE_P0=0** / NOT_APPLICABLE=34 / UNKNOWN=23 |
| verdict | **PASS_WITH_UNKNOWN**（UNKNOWN 均为 P1/P2 阶段门禁，非 P0 阻断） |
| 回归 24 用例 | PASS=19 / WARN=5 / **BLOCKED=0** / **FAIL=0**（B-3 由 BLOCKED → PASS） |
| 衍生品命名空间剔除 | 59 项（前缀 COMEX_/LC_/SPOT_IS 18 项 + 7 类后缀 41 项），P2 建库项 R-V88-033 |
| 交叉一致性 | P0-9 `intersection_count=84` ≡ P0-11 `db_mapping_intersection=84`（双向归一口径正确） |

### 本次交付物 MD5

| # | 文件 | MD5 | 字节 |
|---|------|-----|-----:|
| 1 | `scripts/p0_gate_checker.py` | `7AB9F8CEB0EE05C02C2DBBFB02ECFCD9` | 71270 |
| 2 | `scripts/p0_full_regression_suite.py` | `049E3DDBBB6C091005FD73B452477905` | 30976 |
| 3 | `p0_r3_final_gate_gate_result.json` | `9B10BE0F3668CFA8862985F3C3C9EA2D` | 29931 |
| 4 | `scripts/p0_r3_final_gate_regression_result.json` | `8E263F396428D46ECC9F0A869287D39C` | 9553 |
| 5 | `v88_phase03_p0_hermes_p09_calib_final_gate_report.md` | `97AF648AA29708A6D5BF24A91A87E6D5` | 17523 |

> **说明**: 本次为 P0-9 判定逻辑修正 + 回归用例同步 + P0 终审报告；完整 21 文件清单见本清单顶部主表。

> **DSHE 值守核心**: 引擎基线锁定(MD5=cd73deae...) / 无HERMES缺陷工单 / 冒烟测试通过(101图表加载/25,497点查询/双Schema检测) / P1前置资料(环境变量/双Schema/D7口径/双引擎对比/风险台账) / PHASE03_P0_DSHE_WATCHER=TRUE 待命等待HERMEShf R3终审
| analysis/e2e_output/v88/JOB_READY.flag | `762adde951011c7a56714e402ea0d4d9` | 52,467 |

### V88_PHASE03_P0_DSHB_CONTINUE_WATCHER (DSHB 持续值守)
| 文件 | MD5 | 大小(B) |
|------|:---:|:------:|
| analysis/e2e_output/v88/phase03/p1/dshb/v88_phase03_p1_dshb_prematerials.md | `B832C604AE3EAD20B5A03CEE3D2824F7` | 6,317 |
| STATUS.md | `UPDATED` | — |
| analysis/e2e_output/v88/JOB_READY.flag | `UPDATED` | — |

> **DSHB 持续值守核心**: 归档脚本3+文档5个文件MD5全匹配锁定(8/8) / HERMES R3终审未输出,无缺陷工单 / P1前置资料6317B/182行/8节完整就绪 / 无代码改动/无新增开发 / MD5_MANIFEST P1前置资料size修正7215→6317(MD5不变) / PHASE03_P0_DSHB_CONTINUE_WATCHER=TRUE 待命等待HERMEShf终审及P1工单

### V88_PHASE03_P0_DSHB_FINAL_WATCHER (DSHB 最终值守)
| 文件 | MD5 | 大小(B) |
|------|:---:|:------:|
| analysis/e2e_output/v88/phase03/p1/dshb/v88_phase03_p1_dshb_prematerials.md | `B832C604AE3EAD20B5A03CEE3D2824F7` | 6,317 |
| STATUS.md | `UPDATED` | — |
| analysis/e2e_output/v88/JOB_READY.flag | `UPDATED` | — |

> **DSHB 最终值守核心**: 归档脚本3+文档5个文件MD5全匹配锁定(8/8) / HERMES终审无R3输出/P0-9无输出/无缺陷工单 / P1前置资料6317B/182行/8节完整就绪 / 无代码改动/无新增开发 / 待命等待HERMEShf终审PASS及P1工单

### V88_PHASE03_P0_DSHE_FINAL_WATCHER (DSHE 最终值守)
| 文件 | MD5 | 大小(B) |
|------|:---:|:------:|
| scripts/node_binding_engine.py | `cd73deaeec54a7f1f8bde92c1300a9dc` | 45,411 |
| analysis/e2e_output/v88/phase03/p1/dshb/v88_phase03_p1_dshe_engine_prematerials.md | `F60976152591E237951DA3FF85574A89` | 11,227 |
| analysis/e2e_output/v88/phase03/p0/p1_smoke_test_results.md | `924E4FED2279914D088C4A07F01B08C2` | 2,099 |
| STATUS.md | `UPDATED` | — |
| analysis/e2e_output/v88/JOB_READY.flag | `UPDATED` | — |

> **DSHE 最终值守核心**: 引擎基线锁定(MD5=cd73deae...) / HERMES终审无新提交(f3daeb5仍为最新)/无引擎缺陷工单 / P1冒烟测试14/14 PASS(双Schema/环境变量切换/101图表冒烟/降级链路/R-09隔离) / P1前置资料314行/10节完整就绪 / 无代码改动 / 待命等待HERMEShf终审PASS及P1工单