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
> *Generated: 2026-10-16T22:45 UTC+8 | DSHE | V88 Phase03 P1*