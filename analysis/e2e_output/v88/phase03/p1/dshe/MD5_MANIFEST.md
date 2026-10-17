# MD5 Manifest — V88 Phase03 P1 DSHE

> **Generated**: 2026-10-16T22:45 UTC+8
> **Agent**: DSHE | **Branch**: feature/v88-g1 (BRANCH_LOCKED)
> **Purpose**: MD5 checksum registry for all DSHE Phase03 P1 deliverables

---

## 1. P0-12 Native PASS Consolidation (Frozen)

**Directory**: `p012_nativepass_consolidate/`
**Commit**: `09bf0be` | **Status**: FROZEN

| File | Size (B) | MD5 |
|------|--------:|-----|
| `ARCHIVED_DIRECTORIES_NOTE.md` | 1,911 | `dcbdd014b8958be14cc8d41894eeada9` |
| `baseline_export.json` | 1,953 | `dbd875049df77043e74c5127a8c0f849` |
| `baseline_export.py` | 7,421 | `e332a4fc84d0ee9a709e80341121d15c` |
| `cross_agent_post_nativepass_sop.md` | 8,584 | `2cca93e4da9332b419791b032edd871f` |
| `dqa_render_impact_analysis.md` | 5,986 | `ad82d57b22daebc580dabf61d87511e6` |
| `dshb_risklist_patch.md` | 3,224 | `a169421d9c4ff989dac3e6e02bd3fcbf` |
| `frozen_artifact_lock_confirm.md` | 4,577 | `afdd6badba43e2e0d923000eb4fb20f8` |
| `native_pass_self_verify_bench_results.json` | 24,647 | `52de19670cada2a70949402268814bc3` |
| `native_pass_self_verify_report.md` | 6,182 | `8e5c2b70d6d4a91c5fe8400014249a39` |
| `v88_p012_native_pass_self_verify_bench.py` | 21,563 | `ba902962d276ee5b825176c850c3b8dd` |
| `v88_phase03_p012_reversal_nativepass_note.md` | 9,218 | `6aa649c03cd3b3e12c7b0f6cf5b3f5ee` |
| `v88_phase03_p1_dshe_risklist.md` | 6,921 | `dfbc8b38f298ea46944eadf3cdf7e517` |

**Total**: 12 files | 102,194 bytes

---

## 2. Phase03 P2 Harden & Phase04 Prep

**Directory**: `phase03_p2_harden/`
**Status**: ACTIVE

| File | Size (B) | MD5 |
|------|--------:|-----|
| `dshe_phase04_rendering_bootstrap_checklist.md` | 9,967 | `dec5f0e8addc4382e68519928a413219` |
| `extract_non_rendered.py` | 2,637 | `7671d8312772d8cedb650d9a48a4c829` |
| `gate_freeze_seal.md` | 7,993 | `7dd0e45091cb0b43f6ccf85943a86c9d` |
| `partial_render_precheck_report.md` | 7,973 | `b77d6d1fbed010820eafa34f83d90ee0` |
| `quick_r3_sample_verify.md` | 4,281 | `52c0424c6dabdbd2dc9efbfa09ea68a8` |
| `partial_render_evidence/non_rendered_indicators_evidence.json` | 6,245 | `0342115b72895ff4a35d7b58a7d80d9b` |
| `opt-phase04-psutil-collector/config.yaml` | 3,353 | `a2ca81ab3a215930aadacc222f8db5e4` |
| `opt-phase04-psutil-collector/simple_daemon.py` | 29,633 | `deae3dd626bb9b78bcbdf7bb25ae2ed8` |
| `opt-phase04-psutil-collector/alarm_threshold.json` | 2,964 | `fa9cf79e554e5b18e6503421b3ef3128` |
| `opt-phase04-psutil-collector/test_collector.py` | 17,022 | `e19d2a0618358b1742fdad1beafcf903` |
| `opt-phase04-psutil-collector/deploy_guide.md` | 10,286 | `ed0029ef2fd42668066f5171067b56ce` |

**Total**: 11 files | 103,354 bytes

---

## 3. Metadata Files

| File | Size (B) | MD5 |
|------|--------:|-----|
| `STATUS.md` | — | `9b7e2cffb7e3608470c9b4cbe392f5d6` |
| `JOB_READY.flag` | — | `2db8a4302b40d04da89def6b0f0b5b4f` |

---

## 4. Archived Directories (Read-Only, Preserved)

| Directory | Files | Status |
|-----------|:-----:|:------:|
| `cross_align_ARCHIVED/` | 10 | ✅ ARCHIVE (read-only) |
| `p012_cpu_exception_ARCHIVED/` | 8 | ✅ ARCHIVE (read-only) |

---

## 5. Engine Integrity

| Item | Value |
|:-----|:------|
| Engine MD5 | `cd73deaeec54a7f1f8bde92c1300a9dc` |
| Frozen | TRUE |
| Cross-commit consistent | ✅ |

---

> **Verification Command**:
> ```bash
> Get-FileHash -Path '<file_path>' -Algorithm MD5
> ```
>
## 6. Phase03 P3 Gate Triple Lock & Metrics DB Seed

**Directory**: `phase03_p3_gate_triple_lock/`
**Status**: COMPLETE

| File | Size (B) | MD5 |
|------|--------:|-----|
| `gate_triple_seal_final.md` | 11,176 | `74eaea204cb437dc13ed72b2468e7ca1` |
| `psutil_package_locked_confirmation.md` | 3,029 | `fd598094973b572f215dcdf00439622b` |
| `dshe_dshb_quick_reconcile.md` | 5,719 | `3e5eab08ab7f46d8f6fb79bfe8a685e2` |
| `quick_r3_recheck.md` | 1,865 | `e20322e3f9ecd2f82f5c97c80b8a4aa7` |

### 6.1 Framework-tree Additions

| File | Size (B) | MD5 |
|------|--------:|-----|
| `framework-tree/metrics-db/weekly/dshe_v88_gate_harden.json` | 480 | `90B5A1AB57DAB5FEE43284CDC4FE5039` |
| `framework-tree/metrics-db/weekly/dshe_v88_gate_harden.json.md5` | — | — |
| `framework-tree/node-mapping/dshe_gate_variety_bind.yaml` | 8,374 | `f8d2472d38f30ebadd714b7a8194f625` |
| `chart-tpl/dshe_weekly_report_fixed_tpl.js` | 14,856 | `6ae73aec5b4869fc206b3df506c34f2a` |
| `opt_hooks/blocker_monitor_hook_snippet.py` | 13,846 | `185cf443f5b475cef4f225ed520dda49` |

> *Generated: 2026-10-16T22:45 UTC+8 | DSHE | V88 Phase03 P1*

---

## 7. Phase03 P4 Gate Runtime Prep

**Directory**: `phase03_p4_gate_runtime_prep/`
**Status**: COMPLETE — GATE_WATCH_PREPARED_AWAIT_DATA_TRIGGER

| File | Size (B) | MD5 |
|------|--------:|-----|
| `triple_seal_reverify_v2.md` | 12,617 | `3860A5E3535305637C57DD47DE71EDED` |
| `psutil_ultra_lock_confirmation.md` | 6,519 | `6562ACF77C920FFAD77A8128632DD729` |
| `gate_rule_install_note.md` | 4,621 | `8CC052F215DB59B0646CBB4DE93F9CF5` |
| `variety_render_caliber_recheck.md` | 8,554 | `C7062385E2A8A84F4406D9D7B5F0522E` |
| `hook_upgrade_log.md` | 5,750 | `C99D170EB70AB33F310051D9F39E4AD8` |
| `render_health_check.md` | 4,095 | `E2BDAF92B75589FCB8CDCBB92E5C9E41` |
| `factor_audit_alert_tpl.md` | 11,027 | `DC541683EAE7B81004D05A3F1D34C1AB` |

### 7.1 Gate Rules & Hook Upgrade

| File | Size (B) | MD5 |
|------|--------:|-----|
| `gate_rules/factor_runtime_rules_v1.yaml` | 6,407 | `FB610E02DC1881FEDF29BFC0F36C0E95` |
| `opt_hooks/blocker_monitor_hook_snippet.py` | 17,087 | `5EC795C516BEC98EF0594648A3D2BA03` |

### 7.2 P4 Metrics Summary

| Metric | Value | Status |
|--------|:-----:|:------:|
| Triple seal reverify | 12/12 SHA256+MD5 match | ✅ |
| Engine frozen | `cd73deae...` | ✅ |
| psutil enabled | false | ✅ |
| psutil daemon | false | ✅ |
| Factor rules deployed | 6 rules | ✅ |
| Hook version | v2.0.0-preview | ✅ |
| Hook AUTO_COMMIT_MODE | false | ✅ |
| R3 E2E | 8/8 PASS | ✅ |
| Constraints | 11/11 | ✅ |
| Gate contamination | 0 | ✅ |

---

## 8. Phase03 P6 Gate Runtime Standby (P0-17)

**Directory**: `dshb_p017_gate_watch_archive/`
**Status**: COMPLETE — GATE_ON_WATCH_AWAIT_DUAL_KEYS

| File | Size (B) | MD5 |
|------|--------:|-----|
| `triple_seal_v3_reverify.md` | 13,717 | `8BC3FDD6F66B6D727D1725BD79263ACE` |
| `gate_rule_upgrade_shturl` | 6,805 | `665735A07EBFA0B4C7B1600BC117AB25` |
| `hook_scan_scope_upgrade.md` | 6,288 | `4AEA39C16D052B168E70AB12BCEB1A16` |
| `dshb_workspace_monitor_config.md` | 6,045 | `741A633B8841F88D937F5B4B4125063F` |
| `psutil_ultra_lock_v2.md` | 4,449 | `3F7FC55E880839430622EB303B6998FB` |
| `render_health_v2.md` | 4,872 | `E3148F2BEC39A296591C1E305541E973` |

### 8.1 Updated Files

| File | Size (B) | MD5 |
|------|--------:|-----|
| `gate_rules/factor_runtime_rules_v1.yaml` | 13,936 | `1CEB1245C5012839698110299160F7F9` |
| `opt_hooks/blocker_monitor_hook_snippet.py` | 22,438 | `CDA86B397177EBCAF8546F1BE6FE6636` |

### 8.2 P0-17 Metrics Summary

| Metric | Value | Status |
|--------|:-----:|:------:|
| Triple seal v3 reverify | 12/12 MD5+SHA256 match | ✅ |
| Engine frozen | `cd73deae...` (MD5) | ✅ |
| Engine SHA256 | `604958f2...` | ✅ |
| Archive dirs | 18 files read-only | ✅ |
| Factor rules | 9 rules (v1.1.0-preview) | ✅ |
| Hook version | v2.1.0-preview | ✅ |
| Hook AUTO_COMMIT_MODE | false | ✅ |
| psutil enabled | false | ✅ |
| psutil daemon | false | ✅ |
| R3 E2E | 8/8 PASS | ✅ |
| Render queue | idle, 0 zombies | ✅ |
| Dual keys status | INACTIVE | ⏳ |
| Constraints | 11/11 | ✅ |
| Gate contamination | 0 | ✅ |

---

## 9. Phase03 P7 Gate Pending Issue Cleanup

**Directory**: `analysis/e2e_output/v88/phase03/p7/dshe/phase03_p7_gate_cleanup/`
**Task**: V88_PHASE03_P7_DSHE_P018_GATE_PENDING_ISSUE_CLEANUP
**Status**: COMPLETE — GATE_ON_WATCH_AWAIT_DUAL_KEYS

| File | Size (B) | MD5 |
|------|--------:|-----|
| `rv88_035_fix_report.md` | 8,338 | `22E2DFE8C8E49FD0DFA025946F975D97` |
| `await_caliber_indicator_list.md` | 9,127 | `42A3BF8CEF8F9BBC0A9A075936B44793` |
| `enhanced_gate_trigger_verify.md` | 12,021 | `A5F0E3D6795C67D9F24F4F1B309CFD23` |
| `triple_seal_v4_check.md` | 9,841 | `63DCCA39D26C8DED177A65912C2FDFB6` |
| `psutil_lock_recheck_v3.md` | 4,542 | `D4B56FAF84D45B7BFD78E5FCBF1BD7C0` |

**Total**: 5 files | 43,869 bytes

### 9.1 Verification Summary

| Item | Value | Status |
|:-----|:------|:------:|
| R-V88-035 | CLOSED (boundary verified, R3 8/8 PASS) | ✅ |
| Calibration indicators | 9 slots reserved, awaiting HERMEShf snapshot | ⏳ |
| Enhanced gate trigger | Dual-key INACTIVE, FR-007~009 sealed, 20 constraints verified | ✅ |
| Triple-seal v4 | 12/12 MD5+SHA256 match, 6-layer chain unbroken | ✅ |
| psutil lock v3 | enabled:false, daemon:false, 0 processes, 0 output | ✅ |
| Engine MD5 | `cd73deae...` (frozen) | ✅ |
| Engine SHA256 | `604958f2...` (frozen) | ✅ |
| Constraints | 11/11 compliant | ✅ |
| Gate contamination | 0 | ✅ |