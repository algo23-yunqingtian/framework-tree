# V88 Phase03 P1 — P0-12 + P0-13 Baseline Merge Operations Playbook

> **Version**: 1.0.0  
> **Owner**: DSHB Phase03 P1  
> **Status**: 🟡 DRY-RUN Only — awaiting P0-13 168h window completion + HERMES marker  
> **Branch**: `feature/v88-g1` (BRANCH_LOCKED)  
> **Script**: `p012_p013_baseline_merge.py`  
> **Schema**: `v88-long-stable-baseline-1.0`

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Prerequisites](#2-prerequisites)
3. [Safety Lock Conditions](#3-safety-lock-conditions)
4. [File Structure & Naming](#4-file-structure--naming)
5. [Execution Procedures](#5-execution-procedures)
6. [Rollback Plan](#6-rollback-plan)
7. [Verification Checklist](#7-verification-checklist)
8. [Timeline & Current Status](#8-timeline--current-status)
9. [Constraint Compliance](#9-constraint-compliance)
10. [Emergency Stop Procedure](#10-emergency-stop-procedure)
11. [Troubleshooting](#11-troubleshooting)
12. [Appendix: Schema Reference](#12-appendix-schema-reference)

---

## 1. Purpose & Scope

### 1.1 Purpose

This playbook governs the **C-4 baseline merge preparation** operation: combining two independent observation baselines into a single unified long-stable baseline artifact that serves as the ground-truth reference for Phase04 threshold evaluation.

### 1.2 Baselines Being Merged

| Baseline | ID | Source | Key Metric |
|---|---|---|---|
| **P0-12 Render CPU** | `V88-P012-RENDER-CPU-BASELINE` | DSHE `baseline_export.json` (v2.0-steady-state schema) | `cpu_peak_pct` = 0.0654% |
| **P0-13 Noise Rate** | `V88-P013-NOISE-RATE-BASELINE` | DSHB noise observation (post-168h window) | `noise_rate_pct` (TBD) |

### 1.3 Output

- **File**: `v88-long-stable-baseline.json`
- **Schema**: `v88-long-stable-baseline-1.0`
- **Merged ID**: `V88-LONG-STABLE-BASELINE`

### 1.4 Scope Boundaries

- This operation **does not** modify V87 artifacts (`NO_MODIFY_V87`).
- This operation **does not** edit release tags (`NO_EDIT_RELEASE_TAG`).
- This operation **does not** call any external API (`NO_ZHIJI_API_CALL`).
- This operation **does not** overwrite existing output (`NO_OVERWRITE`).
- All work is confined to `analysis/e2e_output/v88/phase03/p1/dshb/prep_p013_close/`.

---

## 2. Prerequisites

### 2.1 P0-12 Baseline (Already Available)

| Requirement | Status | Detail |
|---|---|---|
| DSHE `baseline_export.json` | ✅ Available | Located at `../` relative to this directory |
| Schema version | ✅ v2.0-steady-state | Confirmed |
| CPU peak | ✅ 0.0654% | Full-link business steady-state calibration |
| Frozen version | ✅ 1.4.0-cpu-triple-fix | |

### 2.2 P0-13 Snapshot (Pending)

| Requirement | Status | Detail |
|---|---|---|
| 168-hour observation window | ⏳ Pending | Must complete before snapshot is generated |
| `p013_noise_baseline_snapshot.json` | ⏳ Not yet created | Will be generated after observation completes |
| `noise_rate_pct` value | ⏳ TBD | Derived from 168h observation |
| `data_completeness` | ⏳ Expected 1.0 | Must be full completeness for merge |

### 2.3 HERMES Release Marker (Pending)

| Requirement | Status | Detail |
|---|---|---|
| `hermes_release_marker.flag` | ⏳ Not yet created | Must be placed by HERMES release pipeline |
| Content | — | Marker file; content is informational only |

---

## 3. Safety Lock Conditions

Both locks must be satisfied simultaneously for a real write to occur.

### Lock 1: P0-13 168h MD5 Snapshot

- **File**: `p013_noise_baseline_snapshot.json`
- **Check**: File exists (`p013_snapshot_path.is_file()`)
- **Purpose**: Confirms the 168-hour observation window has completed and the noise rate baseline is finalized with a computable MD5 hash.

### Lock 2: HERMES Release Marker

- **File**: `hermes_release_marker.flag`
- **Check**: File exists (`hermes_marker_path.is_file()`)
- **Purpose**: Confirms the HERMES release pipeline has been triggered and the environment is ready for baseline freezing.

### Lock Logic Truth Table

| Lock 1 (P0-13) | Lock 2 (HERMES) | `both_ready` | Engine Action |
|:---:|:---:|:---:|---|
| ❌ | ❌ | ❌ | DRY-RUN only; print status |
| ❌ | ✅ | ❌ | DRY-RUN only; P0-13 missing |
| ✅ | ❌ | ❌ | DRY-RUN only; HERMES marker missing |
| ✅ | ✅ | ✅ | DRY-RUN preview OR `execute_merge()` with `--execute` |

### Behaviour on Unmet Locks

- **`--dry-run` mode** (default): Prints lock status and what would be merged. Never writes.
- **`--execute` mode**: Raises `SafetyLockError` with a descriptive message listing which locks are missing. Exit code 1.
- **`--self-test` mode**: Creates mock files in a temp directory. Independent of real locks.

---

## 4. File Structure & Naming

### 4.1 Directory Layout

```
analysis/e2e_output/v88/phase03/p1/dshb/prep_p013_close/
├── p012_p013_baseline_merge.py     # ← Merge engine script
├── merge_operation_playbook.md      # ← This playbook
│
│  ── Referenced at execution time (created externally) ──
│
├── p013_noise_baseline_snapshot.json  # Lock 1: P0-13 168h snapshot
├── hermes_release_marker.flag         # Lock 2: HERMES marker
│
│  ── Output (only written when both locks are met) ──
│
└── v88-long-stable-baseline.json      # Unified merged baseline
```

### 4.2 Naming Conventions

| Pattern | Description | Example |
|---|---|---|
| `p0{NN}_{purpose}.json` | Task-specific JSON artifact | `p013_noise_baseline_snapshot.json` |
| `{service}_release_marker.flag` | Service release marker flag | `hermes_release_marker.flag` |
| `v{version}-{description}-baseline.json` | Versioned baseline output | `v88-long-stable-baseline.json` |

---

## 5. Execution Procedures

### 5.1 Dry Run (Default — Safe)

```bash
cd analysis/e2e_output/v88/phase03/p1/dshb/prep_p013_close/
python p012_p013_baseline_merge.py --dry-run
```

**Expected output** (when locks are not met):
```
  [Lock 1] P0-13 168h snapshot: NOT FOUND
           Path: .../p013_noise_baseline_snapshot.json

  [Lock 2] HERMES release marker: NOT FOUND
           Path: .../hermes_release_marker.flag

  Both locks ready: False

  [INFO] Safety locks NOT satisfied — DRY RUN only.
         No output file will be created.
```

**When to run**: Any time — safe by design. Run before every real execution to verify state.

### 5.2 Self-Test (Mock Validation)

```bash
python p012_p013_baseline_merge.py --self-test
```

Runs 4 tests against mock data in a temporary directory:

| # | Test | Verifies |
|---|---|---|
| 1 | Safety locks NOT met | `dry_run()` does not write; `execute_merge()` raises `SafetyLockError` |
| 2 | Both locks met | `execute_merge()` creates valid output; NO_OVERWRITE guard blocks second write |
| 3 | Merge validation | Valid data passes; corrupted data is caught |
| 4 | Schema round-trip | Full write → read → re-validate cycle |

**Expected output**: `SELF-TEST RESULTS: 4 passed, 0 failed`

### 5.3 Real Execution (When Locks Are Met)

```bash
# Step 1: Verify lock state
python p012_p013_baseline_merge.py --dry-run

# Step 2: Confirm both locks show "FOUND" and both_ready = True

# Step 3: Execute
python p012_p013_baseline_merge.py --execute
```

**Expected output**:
```
  [Lock 1] P0-13 168h snapshot: FOUND
  [Lock 2] HERMES release marker: FOUND
  Both locks ready: True
  ...
  [OK] Merged baseline written: .../v88-long-stable-baseline.json
  [DONE] Merge executed successfully.
```

### 5.4 Programmatic Import (Unit Testing)

```python
from p012_p013_baseline_merge import (
    BaselineMergeEngine,
    MockBaselineGenerator,
    SafetyLockError,
)

gen = MockBaselineGenerator(temp_dir="/tmp/test")
gen.setup_full()

engine = BaselineMergeEngine(
    p012_baseline_path=str(gen.p012_path),
    p013_snapshot_path=str(gen.p013_path),
    hermes_marker_path=str(gen.hermes_marker_path),
    output_path=str(gen.output_path),
)

result = engine.execute_merge()
gen.cleanup()
```

---

## 6. Rollback Plan

### 6.1 Scenario: Output File Created but Incorrect

| Step | Action | Detail |
|---|---|---|
| 1 | Delete the output file | `del v88-long-stable-baseline.json` |
| 2 | Remove safety lock files | `del p013_noise_baseline_snapshot.json` and `del hermes_release_marker.flag` |
| 3 | Restore environment | The engine is stateless; no database writes were made |
| 4 | Re-run self-test | `python p012_p013_baseline_merge.py --self-test` to verify engine integrity |

### 6.2 Scenario: Partial Write (Corrupt Output)

The engine writes atomically via temp file + `os.replace()`. A partial write should not leave a corrupt file. However, if it does:

```bash
# Check if output is valid JSON
python -c "import json; json.load(open('v88-long-stable-baseline.json'))"

# If invalid, delete and re-run
del v88-long-stable-baseline.json
python p012_p013_baseline_merge.py --execute
```

### 6.3 Scenario: Lock Files Placed but Merge Failed

```bash
# Lock files are safe to remove — they can be re-created
del hermes_release_marker.flag
del p013_noise_baseline_snapshot.json

# Investigate the failure log, fix the issue, re-create locks, and retry
```

### 6.4 Rollback Guarantees

- ✅ The merge engine never modifies input files.
- ✅ The output is written atomically (temp file → rename).
- ✅ No database writes, no API calls, no network operations.
- ✅ All inputs remain available for re-merge after any failure.

---

## 7. Verification Checklist

Complete all items after a successful `--execute` run:

| # | Check | Command / Method | Expected |
|---|---|---|---|
| 1 | Output file exists | `python -c "import os; print(os.path.exists('v88-long-stable-baseline.json'))"` | `True` |
| 2 | Valid JSON | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); print('OK')" 2>&1` | `OK` |
| 3 | Schema version correct | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert d['schema_version']=='v88-long-stable-baseline-1.0'; print('OK')"` | `OK` |
| 4 | Baseline ID correct | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert d['baseline_id']=='V88-LONG-STABLE-BASELINE'; print('OK')"` | `OK` |
| 5 | P0-12 CPU peak present | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert d['p012_render_cpu']['cpu_peak_pct']==0.0654; print('OK')"` | `OK` |
| 6 | P0-13 observation hours = 168 | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert d['p013_noise_rate']['observation_hours']==168; print('OK')"` | `OK` |
| 7 | MD5 checksum present (32 chars) | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert len(d['merge_metadata']['p013_snapshot_md5'])==32; print('OK')"` | `OK` |
| 8 | Safety locks recorded as verified | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert d['merge_metadata']['safety_locks_verified'] is True; print('OK')"` | `OK` |
| 9 | Hermes marker recorded as present | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert d['merge_metadata']['hermes_marker_present'] is True; print('OK')"` | `OK` |
| 10 | Merge status = COMPLETE | `python -c "import json; d=json.load(open('v88-long-stable-baseline.json')); assert d['merge_metadata']['merge_status']=='COMPLETE'; print('OK')"` | `OK` |
| 11 | Self-test still passes | `python p012_p013_baseline_merge.py --self-test` | `4 passed, 0 failed` |
| 12 | No temp files left | `dir /b v88_baseline_* 2>&1` | `File Not Found` (or no match) |

---

## 8. Timeline & Current Status

### 8.1 Current State (as of playbook creation)

```
Phase 1: Preparation           ✅ COMPLETE
  ├── Script written           ✅ p012_p013_baseline_merge.py
  ├── Playbook written         ✅ merge_operation_playbook.md
  └── Self-test passing        ✅ 4/4 tests pass

Phase 2: Prerequisites         ⏳ PENDING
  ├── P0-12 baseline           ✅ Available (DSHE v2.0-steady-state)
  ├── P0-13 168h observation   ⏳ Window in progress
  └── HERMES release marker    ⏳ Not yet placed

Phase 3: Merge Execution       ⏳ PENDING
  ├── Dry-run verification     ⏳ Run after locks are met
  └── Real execution           ⏳ Run with --execute flag

Phase 4: Verification          ⏳ PENDING
  └── All 12 checklist items   ⏳ Run post-execute
```

### 8.2 Gate Criteria to Proceed to Phase 3

All three conditions must be TRUE:
1. `p013_noise_baseline_snapshot.json` exists in `prep_p013_close/`
2. `hermes_release_marker.flag` exists in `prep_p013_close/`
3. `python p012_p013_baseline_merge.py --self-test` returns `4 passed, 0 failed`

### 8.3 Approval Gate

Before executing Phase 3, confirm with the DSHB Phase03 P1 owner that:
- [ ] P0-13 observation data has been reviewed and accepted
- [ ] HERMES release pipeline has completed its pre-freeze checks
- [ ] The P0-13 `noise_rate_pct` value is within the expected range (0.0 – 0.1%)
- [ ] The merge operation will not conflict with any concurrent activity on `feature/v88-g1`

---

## 9. Constraint Compliance

| Constraint | Enforcement | Mechanism |
|---|---|---|
| **NO_OVERWRITE** | Output file existence check before write | `engine.output_path.exists()` guard; raises `OSError` |
| **NO_MODIFY_V87** | No reference to V87 artifacts in code or paths | Path resolution is scoped to `prep_p013_close/` only |
| **NO_EDIT_RELEASE_TAG** | No tag manipulation in code or CLI | Script never invokes `git tag` or modifies tag refs |
| **NO_ZHIJI_API_CALL** | Zero network imports; no HTTP calls | Script uses only `json`, `os`, `sys`, `hashlib`, `tempfile`, `datetime`, `pathlib` |
| **BRANCH_LOCKED** | Work confined to `feature/v88-g1` branch | File writes are to the pre-existing `prep_p013_close/` directory |
| **Python 3.8+** | `from __future__ import annotations`; `typing.Optional`, `Dict`, `List`, `Tuple` | No walrus operators, no `match` statements, no `X | Y` type syntax |

---

## 10. Emergency Stop Procedure

If something goes wrong during execution:

### 10.1 During Dry Run (No Risk)

```
Press Ctrl+C at any time. No files are written.
```

### 10.2 During Execute (Before Write)

```
Press Ctrl+C. The engine checks locks, loads data, and validates
BEFORE writing. If interrupted during this phase, no output file
exists and the environment is unchanged.
```

### 10.3 During Execute (After Write Begins)

The atomic write means the file is either fully written or not written at all. If interrupted mid-write:

```bash
# Check for leftover temp files
dir /b v88_baseline_*.json

# Delete any temp files found
del v88_baseline_*.json 2>nul

# Check if the output file was created
python -c "import os; print(os.path.exists('v88-long-stable-baseline.json'))"
```

### 10.4 Complete Abort

```bash
# Remove all merge artifacts (inputs are safe — they're read-only)
del v88-long-stable-baseline.json 2>nul
del v88_baseline_*.json 2>nul

# Lock files can be preserved or removed as appropriate
# del p013_noise_baseline_snapshot.json
# del hermes_release_marker.flag

# Verify engine integrity
python p012_p013_baseline_merge.py --self-test
```

---

## 11. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `SafetyLockError` on `--execute` | One or both lock files missing | Create the missing lock file(s), or use `--dry-run` |
| `OSError: NO_OVERWRITE violation` | Output file already exists | Delete existing output: `del v88-long-stable-baseline.json` |
| `SchemaValidationError` | Source data malformed | Check input JSON structure; run self-test to verify engine |
| `[WARN] Could not load P0-12 baseline` | DSHE export path incorrect | Verify `dshe_baseline_export.json` is in the parent directory |
| `[WARN] Could not load P0-13 snapshot` | Snapshot file missing or invalid JSON | Ensure `p013_noise_baseline_snapshot.json` exists with valid JSON |
| `FileNotFoundError` on import | Running from wrong directory | `cd analysis/e2e_output/v88/phase03/p1/dshb/prep_p013_close/` |
| Self-test failure | Corrupted mock data or environment issue | Re-run `--self-test`; temp dirs are cleaned automatically |

---

## 12. Appendix: Schema Reference

### 12.1 Merged Baseline Schema (`v88-long-stable-baseline-1.0`)

```json
{
  "baseline_id": "V88-LONG-STABLE-BASELINE",
  "schema_version": "v88-long-stable-baseline-1.0",
  "merged_at": "<ISO 8601 UTC timestamp>",
  "p012_render_cpu": {
    "baseline_id": "V88-P012-RENDER-CPU-BASELINE",
    "cpu_peak_pct": 0.0654,
    "cpu_threshold_phase04": 2.0,
    "cpu_caliber": "full_link_business_steady_state",
    "frozen_version": "1.4.0-cpu-triple-fix",
    "schema_version": "v2.0-steady-state"
  },
  "p013_noise_rate": {
    "baseline_id": "V88-P013-NOISE-RATE-BASELINE",
    "noise_rate_pct": "<from P0-13 snapshot>",
    "observation_hours": 168,
    "data_completeness": 1.0,
    "target_threshold": 0.1
  },
  "merge_metadata": {
    "merge_type": "P0-12 + P0-13",
    "safety_locks_verified": true,
    "hermes_marker_present": true,
    "p013_snapshot_md5": "<32-char MD5 hex of snapshot file>",
    "merge_status": "COMPLETE",
    "merge_engine_version": "1.0.0"
  }
}
```

### 12.2 P0-12 Section Field Definitions

| Field | Type | Description |
|---|---|---|
| `baseline_id` | string | Source baseline identifier |
| `cpu_peak_pct` | float | Peak CPU utilization percentage during steady-state window |
| `cpu_threshold_phase04` | float | Phase04 alert threshold percentage |
| `cpu_caliber` | string | Calibration methodology description |
| `frozen_version` | string | Frozen engine version tag |
| `schema_version` | string | Source schema version identifier |

### 12.3 P0-13 Section Field Definitions

| Field | Type | Description |
|---|---|---|
| `baseline_id` | string | Source baseline identifier |
| `noise_rate_pct` | float | Percentage of data points flagged as noise |
| `observation_hours` | integer | Total observation window duration (expected: 168) |
| `data_completeness` | float | Fraction of expected data points received (1.0 = complete) |
| `target_threshold` | float | Maximum acceptable noise rate for Phase04 |

### 12.4 Merge Metadata Field Definitions

| Field | Type | Description |
|---|---|---|
| `merge_type` | string | Description of the merge operation |
| `safety_locks_verified` | boolean | Whether both safety locks were verified as present |
| `hermes_marker_present` | boolean | Whether the HERMES marker was confirmed |
| `p013_snapshot_md5` | string | MD5 hash of the P0-13 snapshot file (32 hex chars) |
| `merge_status` | string | Final merge status (`"COMPLETE"`) |
| `merge_engine_version` | string | Version of the merge engine script |

### 12.5 Validation Rules

| Rule | Detail |
|---|---|
| `baseline_id` must equal `"V88-LONG-STABLE-BASELINE"` | Hardcoded constant |
| `schema_version` must equal `"v88-long-stable-baseline-1.0"` | Hardcoded constant |
| `merged_at` must be a non-empty ISO 8601 string | UTC timestamp with `Z` suffix |
| `cpu_peak_pct` must be in range [0.0, 100.0] | Numeric bounds check |
| `noise_rate_pct` must be in range [0.0, 100.0] | Numeric bounds check |
| `observation_hours` must equal `168` | Exact match required |
| `merge_status` must equal `"COMPLETE"` | No partial or failed merges allowed |
| `p013_snapshot_md5` must be exactly 32 characters | Hex MD5 length check |
| All required top-level keys must be present | `baseline_id`, `schema_version`, `merged_at`, `p012_render_cpu`, `p013_noise_rate`, `merge_metadata` |
| All P0-12 expected fields must be present | `baseline_id`, `cpu_peak_pct`, `cpu_threshold_phase04`, `cpu_caliber`, `frozen_version`, `schema_version` |
| All P0-13 expected fields must be present | `baseline_id`, `noise_rate_pct`, `observation_hours`, `data_completeness`, `target_threshold` |

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | (creation) | T2 — p012_p013_baseline_merge | Initial playbook; covers all 12 sections |

---

*End of playbook. All 12 verification checks must pass before this baseline is considered frozen and available for Phase04 consumption.*
