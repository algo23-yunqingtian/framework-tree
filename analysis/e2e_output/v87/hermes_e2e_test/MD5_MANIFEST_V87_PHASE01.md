# MD5_MANIFEST — V87-RC1 Phase01+Phase02

| 项目 | 值 |
|------|---|
| 分支 | feature/v87-rc1-g1 |
| 日期 | 2026-10-18 |
| 版本 | V87-RC1 |
| Phase | Phase01 + Phase02 |

---

## 1. V87 Phase01 产物

| # | 文件 | MD5 |
|---|------|-----|
| 1 | `v87_rc1_hermes_phase01_baseline_import_report.md` | `edfc42d58507893b2800c7c685fdd73f` |
| 2 | `v87_rc1_hermes_phase01_audit_rule_migration_spec.md` | `8f8c78d7c918885b5744a38c6b6094a1` |
| 3 | `v87_rc1_hermes_phase01_index_model_pre_calibration.md` | `93cd8f0ce5085e908d46caa36469dad1` |
| 4 | `v87_rc1_hermes_phase01_v87_gate_audit_criteria.md` | `5ea71c5eb1b083376b97b55062b7f039` |
| 5 | `v87_rc1_hermes_phase01_pre_reconcile_test_report.md` | `00f52dcb87e618e40ba6023f338c7cec` |
| 6 | `v87_rc1_hermes_phase01_risk_watchlist_v87_initial.md` | `8d9770fd5511f61a23c24d61cf827e52` |

## 2. V87 Phase02 产物

| # | 文件 | MD5 |
|---|------|-----|
| 1 | `v87_rc1_hermes_phase02_3party_requirement_final_align_minutes.md` | `ec1cf8ac58e9197b234e92483de64c78` |
| 2 | `v87_rc1_hermes_phase02_multi_scenario_reconcile_validation_report.md` | `9aaaf0303ca2ee5af6e668a63d775ed0` |
| 3 | `v87_rc1_hermes_phase02_fault_inject_reconcile_test_report.md` | `962cfc6477f7549008d24dc59e76cf3d` |
| 4 | `v87_rc1_hermes_phase02_index_model_tune_sensitivity_analysis.md` | `5bfce8e4c341bc756c24adf6e883a911` |
| 5 | `v87_rc1_hermes_phase02_v87_gate_risk_checklist.md` | `db33046c2610fce761d9d6a86058d3b9` |
| 6 | `v87_rc1_hermes_phase02_audit_engine_performance_evaluation.md` | `ad286190348b53d0745dfb6d988c9fec` |
| 7 | `risk_watchlist_v87_phase02.md` | `75be8cad8ed627291790d4d50b618605` |

## 3. V86 继承产物（只读引用）

| 文件 | MD5 | 来源 |
|------|-----|------|
| `phase4_gray_audit_wal_validator.py` | `de4d2cbe9a25e754f7b20ad628b6e50f` | V86 基础引擎 |
| `phase27_v86_full_version_audit_archive_closure.md` | `6311a41007e65407c3e2b56393f6be26` | V86 归档闭环 |

## 4. 不可篡改保证

- 所有产物已 commit 至 `feature/v87-rc1-g1`
- MD5 记录完整
- NO_OVERWRITE: Phase01产物MD5不变
- NO_MODIFY_V85: 不修改 `*.html`/`scripts/`/`data/`
