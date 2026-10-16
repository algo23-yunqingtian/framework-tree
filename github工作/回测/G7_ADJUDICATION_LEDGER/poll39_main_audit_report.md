# Poll39 全量只读审计扫描 · 主报告

> **扫描 ID**: POLL39
> **扫描范围**: scope_lock V2 · 24 项 include_artifacts · 47 文件实际匹配
> **熔断器状态**: READY
> **扫描开始**: 2026-10-16T11:40:59+0800
> **扫描结束**: 2026-10-16T11:41:00+0800
> **耗时**: 0.668 s（hard timeout 600 / soft timeout 480）
> **裁决**: PASS
> **R-P61-001 应用**: 方案① hash_compare_exclude + C-1（APPROVED 2026-10-16T11:26:14+08:00）
> **READ_ONLY 断言**: 上游写入 0 / 覆盖 0 / 删除 0 / 重命名 0 / Wind 调用 0

## 1. 扫描范围

- **扫描根**: `D:\DSH_WORK\github工作\回测`
- **include_artifacts 条目**: 24（含 2 个 glob 展开）
- **实际匹配文件数**: 47
- **hash_compare_exclude**: 1 项（豁免双遍 sha256 比对）
  - `P49_decisions/audit/tracking_monitor_audit.jsonl`
- **未匹配条目**（声明但无实际文件）:
  - `P49_cross_agent_hash_check.json`
  - `P49_decision_tracking_monitor_latest.json`

## 2. 熔断器

| 属性 | 值 |
|---|---|
| enabled | True |
| alert_level | CRITICAL |
| continue_after_trip | False |
| state | READY |

## 3. 双遍 sha256 比对结果

- **参与哈希比对**: 46 文件
- **豁免（C-1 单独判定）**: 1 文件
- **哈希漂移**: 0


## 4. C-1 补偿控制（账本追加单调性）

| 属性 | 值 |
|---|---|
| pass | True |
| reason | OK_NO_APPEND |
| size1 (pass1) | 31663 |
| size2 (pass2) | 31663 |
| delta | 0 |

## 5. 账本重复 event_id 检查

| 属性 | 值 |
|---|---|
| pass | True |
| reason | OK_NO_REAL_DUPLICATE |
| rows | 42 |
| unique_ids | 11 |
| bad_lines | 0 |
| real_duplicates | {} |

## 6. 文件清单（全量）

| # | 文件 | size (pass1) | sha256 (pass1) | 哈希比对 |
|---|---|---|---|---|
| 1 | `github_release_manifest.json` | 53.0 KB | `fb8dd7c795f5fc42` | ✓ |
| 2 | `publish_gate_rule.json` | 8.0 KB | `b0f477911faed89d` | ✓ |
| 3 | `github_pages_index_meta.md` | 2.9 KB | `7c38415b79d161e2` | ✓ |
| 4 | `updated_github_release_manifest.json` | 75.2 KB | `5712f73c54abd602` | ✓ |
| 5 | `updated_pages_index_meta.md` | 6.8 KB | `02894f62f22455cc` | ✓ |
| 6 | `final_project_manifest.json` | 17.5 KB | `21d37c55e1912023` | ✓ |
| 7 | `phase58_audit_log.jsonl` | 27.2 KB | `181107280794f33b` | ✓ |
| 8 | `P47_deliverable_manifest.json` | 2.9 KB | `ec4db580cd22a75f` | ✓ |
| 9 | `P47_audit_manifest.json` | 16.2 KB | `f31e65b864b5a70b` | ✓ |
| 10 | `P49_decisions/audit/tracking_monitor_audit.jsonl` | 30.9 KB | `c3976fe3ce712d4a` | 豁免 |
| 11 | `P49_decisions/flags/G7_THRESHOLD_v1_DECISION_DONE.flag` | 2.3 KB | `fc92cb2957340293` | ✓ |
| 12 | `P49_decisions/flags/G7_THRESHOLD_v1_DECISION_DONE_flag_sha256.txt` | 66 | `0ccda6aeea184c47` | ✓ |
| 13 | `P49_decisions/flags/METADATA_VERSIONING_v1_DECISION_DONE.flag` | 2.4 KB | `accffd6f65e315ee` | ✓ |
| 14 | `P49_decisions/flags/METADATA_VERSIONING_v1_DECISION_DONE_flag_sha256.txt` | 66 | `1fba148255d705a6` | ✓ |
| 15 | `P49_decisions/flags/WINDPY_EXCEL_FALLBACK_v1_DECISION_DONE.flag` | 2.4 KB | `42028be90422dc04` | ✓ |
| 16 | `P49_decisions/flags/WINDPY_EXCEL_FALLBACK_v1_DECISION_DONE_flag_sha256.txt` | 66 | `e2e16158e286c0ec` | ✓ |
| 17 | `P49_decisions/flags/WIND_BATCH_STRATEGY_v1_DECISION_DONE.flag` | 2.4 KB | `ee87c76f683aaec0` | ✓ |
| 18 | `P49_decisions/flags/WIND_BATCH_STRATEGY_v1_DECISION_DONE_flag_sha256.txt` | 66 | `9b2ec305dd409fa0` | ✓ |
| 19 | `P49_decisions/production/EXCEL_ALTERNATIVE_PATH_V1_official_alias_decision_manifest.json` | 2.2 KB | `8f03972179dd53b4` | ✓ |
| 20 | `P49_decisions/production/G7_THRESHOLD_V1_decision_manifest.json` | 2.1 KB | `57fd60e22d92e9d9` | ✓ |
| 21 | `P49_decisions/production/ISSUE_FLAGS_RESULT.json` | 7.0 KB | `4dbf4b9d35df2394` | ✓ |
| 22 | `P49_decisions/production/METADATA_VERSIONING_V1_decision_manifest.json` | 2.1 KB | `8e64d5f0072951b1` | ✓ |
| 23 | `P49_decisions/production/WINDPY_EXCEL_FALLBACK_V1_decision_manifest.json` | 2.1 KB | `da2b649d17d413f1` | ✓ |
| 24 | `P49_decisions/production/WIND_BATCH_STRATEGY_V1_decision_manifest.json` | 2.1 KB | `dd6dd0a046062e3c` | ✓ |
| 25 | `P49_decisions/production/audit/decision_flag_audit.jsonl` | 2.3 KB | `7325bd1bbcff896b` | ✓ |
| 26 | `P49_decisions/production/flags/G7_THRESHOLD_v1_DECISION_DONE.flag` | 2.2 KB | `f076580353f820d8` | ✓ |
| 27 | `P49_decisions/production/flags/G7_THRESHOLD_v1_DECISION_DONE_flag_sha256.txt` | 66 | `d0ecedd2126cda63` | ✓ |
| 28 | `P49_decisions/production/flags/METADATA_VERSIONING_v1_DECISION_DONE.flag` | 2.2 KB | `f9a77eab311f756d` | ✓ |
| 29 | `P49_decisions/production/flags/METADATA_VERSIONING_v1_DECISION_DONE_flag_sha256.txt` | 66 | `cc9e5bfa65527359` | ✓ |
| 30 | `P49_decisions/production/flags/WINDPY_EXCEL_FALLBACK_v1_DECISION_DONE.flag` | 2.2 KB | `8c6eb4b0faceb3d2` | ✓ |
| 31 | `P49_decisions/production/flags/WINDPY_EXCEL_FALLBACK_v1_DECISION_DONE_flag_sha256.txt` | 66 | `7c21e44a70ab25ce` | ✓ |
| 32 | `P49_decisions/production/flags/WIND_BATCH_STRATEGY_v1_DECISION_DONE.flag` | 2.2 KB | `4e72ec30fd20db0f` | ✓ |
| 33 | `P49_decisions/production/flags/WIND_BATCH_STRATEGY_v1_DECISION_DONE_flag_sha256.txt` | 66 | `8dfc630d82f7260d` | ✓ |
| 34 | `P49_decisions/production/tracking_records/G7_THRESHOLD_V1.json` | 627 | `7ce0bdffb21c5055` | ✓ |
| 35 | `P49_decisions/production/tracking_records/METADATA_VERSIONING_V1.json` | 646 | `db05c391372d4d93` | ✓ |
| 36 | `P49_decisions/production/tracking_records/WINDPY_EXCEL_FALLBACK_V1.json` | 650 | `4ec1f274415ff93a` | ✓ |
| 37 | `P49_decisions/production/tracking_records/WIND_BATCH_STRATEGY_V1.json` | 644 | `9c99c66e5e3f8b6c` | ✓ |
| 38 | `data-harbor/dsha_p49_prep/P49_experiment_monitor/P49_meta_summary.md` | 9.9 KB | `55fa11b21b7f8d79` | ✓ |
| 39 | `fault_audit_shturl` | 1.3 KB | `6a11eb390b0ed4e0` | ✓ |
| 40 | `fault_audit_log.md` | 1.3 KB | `a993b7d56575b919` | ✓ |
| 41 | `repo_write_lock.py` | 2.1 KB | `7ea4cf588f2c84c4` | ✓ |
| 42 | `release_generation_counter.py` | 1.8 KB | `5bb9b6cba9ee262b` | ✓ |
| 43 | `audit_ledger_dedupe_hook.py` | 9.4 KB | `8da705e24e270761` | ✓ |
| 44 | `ledger_dedupe_exec.py` | 11.3 KB | `254a139d8d9850f7` | ✓ |
| 45 | `ledger_dedupe_dryrun_report.md` | 2.5 KB | `bfcc99213d509344` | ✓ |
| 46 | `git_push_manifest.json` | 10.4 KB | `2234d5c702daa3a6` | ✓ |
| 47 | `P49_decision_tracking_monitor_report.md` | 7.1 KB | `c58d2e02b9652f9f` | ✓ |

## 7. FL-01/02/03 因子泄露专项检测（摘要）

完整明细见附表 `poll39_factor_leakage_risk_appendix.md`。

| FL | 名称 | 严重级 | 扫描脚本数 | 命中次数 | 裁决 |
|---|---|---|---|---|---|
| FL-01 | 未来数据引入检测 (look-ahead leakage) | HIGH | 39 | 19 | REVIEW |
| FL-02 | 样本截断时间边界校验 (sample cutoff boundary) | HIGH | 39 | 23 | REVIEW |
| FL-03 | 训练/测试时间切片隔离校验 (train-test temporal isolation) | HIGH | 39 | 0 | PASS |

## 8. 7 因子泄露风险结论

| # | Factor ID | 因子代码 | 分类 | 风险级 | 准入 | FL 关联命中 | 泄露裁决 |
|---|---|---|---|---|---|---|---|
| 1 | P0-1 | `F19_hot_money_weight` | SYNTHETIC_DATA_ZERO_SIGNAL | HIGH | HOLD | 0 | N/A_SYNTHETIC_DATA |
| 2 | P0-2 | `F20_attention_weight` | SYNTHETIC_DATA_ZERO_SIGNAL | HIGH | HOLD | 0 | N/A_SYNTHETIC_DATA |
| 3 | P0-3 | `CF003_speculation_weight` | SYNTHETIC_DATA_ZERO_SIGNAL | HIGH | HOLD | 0 | N/A_SYNTHETIC_DATA |
| 4 | P0-4 | `G1_IC_threshold` | THRESHOLD_STABILITY_DEFECT | HIGH | CONDITIONAL_PASS | 0 | NO_LEAKAGE_EVIDENCE |
| 5 | P0-5 | `G3_ICIR_threshold` | THRESHOLD_STABILITY_DEFECT | HIGH | HOLD | 0 | NO_LEAKAGE_EVIDENCE |
| 6 | P0-6 | `G7_leakage_ratio` | LEAKAGE_BOUNDARY_FALSE_ALARM_ISSUE | WARN | CONDITIONAL_PASS | 0 | FALSE_ALARM_MITIGATED |
| 7 | P0-7 | `SchemeD_frozen_weights` | MULTI_WINDOW_INSTABILITY | MEDIUM | CONDITIONAL_PASS | 0 | NO_LEAKAGE_EVIDENCE |

## 9. 扫描裁决

**裁决：PASS（无熔断触发）**

- 46 项哈希比对全部一致（0 漂移）
- C-1 账本单调性校验通过
- 账本重复 event_id = 0
- 扫描全程 READ_ONLY，上游写入 0
- 熔断器保持 READY

**GATE 状态**：维持 `CLOSED/HOLD`；`release_permit` 维持 `NOT_ISSUED`；`self_approval = 0`。本扫描不构成任何发布许可。

_生成时间：_2026-10-16T11:41:00+0800
