# MD5_MANIFEST — V87-RC1 Phase01

| 项目 | 值 |
|------|---|
| 分支 | feature/v87-rc1-g1 |
| 日期 | 2026-10-18 |
| 版本 | V87-RC1 |
| Phase | Phase01 |

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

## 2. V86 继承产物（只读引用）

| 文件 | MD5 | 来源 |
|------|-----|------|
| `phase4_gray_audit_wal_validator.py` | `de4d2cbe9a25e754f7b20ad628b6e50f` | V86 基础引擎 |
| `phase27_v86_full_version_audit_archive_closure.md` | `6311a41007e65407c3e2b56393f6be26` | V86 归档闭环 |
| `phase27_risk_watchlist_v7_longterm_final.md` | `ab2997c7e0541fffd56dc1aeac223fbf` | V86 风险清单v7.0 |

## 3. 不可篡改保证

- 所有产物已 commit 至 `feature/v87-rc1-g1`
- MD5 记录完整
- NO_OVERWRITE: V87 不修改 V86 产物
- NO_MODIFY_V85: 不修改 `*.html`/`scripts/`/`data/`
