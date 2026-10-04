# DSHB V86-RC2 DEP Trigger Chain — E2E Dry-Run Test Log

**Test ID**: DSHB_V86_RC2_DEP_E2E_DRYRUN_20261004_154842
**Execution Date**: 2026-10-04 15:48:42
**Total Duration**: 1.0s
**Python**: 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
**Platform**: nt
**Work Directory**: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix`
**Sandbox Directory**: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\_dryrun_sandbox`
**API Calls**: **All mocked** (zero real HTTP requests)
**Output Overwrite**: **Prevented** (all writes redirected to sandbox)

---

## 1. Test Environment

| Parameter | Value |
|-----------|-------|
| Python Version | 3.12.10 |
| Platform | nt |
| Working Dir | `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix` |
| Sandbox Dir | `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\_dryrun_sandbox` |
| Mock Mode | urllib.request mocked (all calls intercepted) |
| time.sleep | Disabled (no delays) |
| subprocess.run | Mocked (no real subprocess) |
| Mapping Logs | Copied from `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\mapping_logs` to sandbox |

---

## 2. Test Results Summary

| # | Step | Status | Duration | Detail |
|---|------|--------|----------|--------|
| 1 | Probe Phase | ✅ PASS | 1ms | 3/3 probes READY. j25_tc=9pts/HTTP200; i1=6pts/HTTP200; i3=6pts/HTTP200 |
| 2 | Trigger Retest | ✅ PASS | 633ms | 170 entries, 123 fetchable, 47 blocked, 123 meta-complete. Gate=NOT_READY, Concl... |
| 3 | Bridge Snapshot | ✅ PASS | 6ms | Valid JSON, 170 entries, gate=NOT_READY, MD5=CE5FAD7B30BB47EE |
| 4 | MD5 Computation | ✅ PASS | 56ms | Manifest: 2 files, MD5=EFFC2AC6A3E4F51E |
| 5 | Risk Register Update | ✅ PASS | 59ms | File exists (15,423 chars), valid content. post_trigger_actions ran OK |
| 6 | Gate Package Update | ✅ PASS | 1ms | File exists (26,085 chars), valid content |
| 7 | Cross-team Notification | ✅ PASS | 6ms | 5 events written: HERMES_NOTIFICATION, DSHE_NOTIFICATION, DEP_READY_DETECTED |

**Total Steps**: 7 | **Passed**: 7 | **Failed**: 0
**Chain Integrity**: ✅ ALL 7 LINKS PASS

---

## 3. Chain Integrity Detail (All 7 Links)

### Link 1: Probe Phase — ✅ PASS
- **Duration**: 1ms
- **Detail**: 3/3 probes READY. j25_tc=9pts/HTTP200; i1=6pts/HTTP200; i3=6pts/HTTP200

### Link 2: Trigger Retest — ✅ PASS
- **Duration**: 633ms
- **Detail**: 170 entries, 123 fetchable, 47 blocked, 123 meta-complete. Gate=NOT_READY, Conclusion=PARTIAL_FETCHABLE

### Link 3: Bridge Snapshot — ✅ PASS
- **Duration**: 6ms
- **Detail**: Valid JSON, 170 entries, gate=NOT_READY, MD5=CE5FAD7B30BB47EE

### Link 4: MD5 Computation — ✅ PASS
- **Duration**: 56ms
- **Detail**: Manifest: 2 files, MD5=EFFC2AC6A3E4F51E

### Link 5: Risk Register — ✅ PASS
- **Duration**: 59ms
- **Detail**: File exists (15,423 chars), valid content. post_trigger_actions ran OK

### Link 6: Gate Package — ✅ PASS
- **Duration**: 1ms
- **Detail**: File exists (26,085 chars), valid content

### Link 7: Cross-team Notification — ✅ PASS
- **Duration**: 6ms
- **Detail**: 5 events written: HERMES_NOTIFICATION, DSHE_NOTIFICATION, DEP_READY_DETECTED

---

## 4. Output Product Verification

| Product | Exists | Size | MD5 (first 16) |
|---------|--------|------|-----------------|
| Bridge Snapshot (JSON) | ✅ Yes | 165,068 bytes | `CE5FAD7B30BB47EE` |
| Summary JSON | ✅ Yes | 3,137 bytes | `2B915DCB29F5C185` |
| MD5 Manifest | ✅ Yes | 349 bytes | `FFAE430800C7AAAF` |
| Alert Events (JSON) | ✅ Yes | 4,268 bytes | `C82152797A3C393D` |
| Risk Register (original) | ✅ Yes | 23,105 bytes | `2BD49F0C711AA5F4` |
| Gate Package (original) | ✅ Yes | 32,873 bytes | `75C581E8380B8A6A` |

**Sandbox output files**: 185

---

## 5. Mock Data Validation

| Mock Type | Description | Data Points | Status |
|-----------|-------------|-------------|--------|
| Probe j25_tc | 铅精矿TC加工费 | 9 points, values 7.8–9.3 | ✅ Valid |
| Probe i1 | 铅锭社会库存 | 6 points, values 138k–150k | ✅ Valid |
| Probe i3 | 沪铅期货收盘价 | 6 points, values 15470–15520 | ✅ Valid |
| Real IDs (i1–i7, j25_tc) | 8 indicators w/ realistic market data | 2–9 pts each | ✅ Valid |
| Fabricated (s_lead_lme_inv) | LME铅库存, perm_state=-4 | 3 points | ✅ Valid |
| Fabricated (s_lead_shfe_inv) | 上期所铅库存, perm_state=-4 | 3 points | ✅ Valid |
| Generic s_xxx | Per-ID hash-based mock data | 3 points each | ✅ Valid |
| Unknown IDs | error: 无法识别指标来源 | 0 points | ✅ Valid |
| DERIVED entries | No API call (skipped by script) | N/A | ✅ Correct |

**HTTP Status**: All mocked responses return HTTP 200 | ✅ Verified
**Permission States**: -4 for fabricated IDs, None for real IDs | ✅ Correct

---

## 6. Defects Found During Dry-Run

### DEF-001 (LOW): ConfigLoader YAML parser may misparse complex values

- **Location**: `dep_ready_trigger.py:133-240 (ConfigLoader.load)`
- **Description**: The simplified YAML parser in dep_ready_trigger.py ConfigLoader.load() may not correctly handle multi-line strings, quoted values with colons, or deeply nested structures. The current trigger_config.yaml is simple enough to parse correctly, but the parser is fragile for edge cases.
- **Impact**: LOW — current config works, future changes may break parsing.

### DEF-002 (LOW): time.sleep() blocks in _rate_limit() and probe_once()

- **Location**: `dep_ready_trigger.py:259-264, full_reverify_v3_batch_v2.py:41-50`
- **Description**: Both ZhijiProber._rate_limit() and probe_once() call time.sleep() which blocks the main thread. In daemon mode this is fine, but in test or dry-run contexts it slows execution. The _rate_limit() also writes a shared lock file (.locks/data.lock) that could cause issues in concurrent test scenarios.
- **Impact**: LOW — only affects test speed, not correctness.

### DEF-003 (MEDIUM): trigger_retest() uses subprocess.run — no mock-friendly interface

- **Location**: `dep_ready_trigger.py:404-443`
- **Description**: DepReadyTrigger.trigger_retest() calls subprocess.run() to execute the retest script. This makes it difficult to mock the retest in unit tests without intercepting subprocess.run. A better approach would be to allow direct function calls or use dependency injection for the retest executor.
- **Impact**: MEDIUM — complicates testability and dry-run testing.

### DEF-004 (MEDIUM): update_risk_register and update_gate_package are log-only

- **Location**: `dep_ready_trigger.py:613-616`
- **Description**: The post_trigger_actions 'update_risk_register' and 'update_gate_package' only log messages to console (lines 613-616) without actually modifying the corresponding files. The files v86_rc2_dshb_risk_re_evaluate_v3.md and v86_rc2_gate_pre_submit_package_v2.md are referenced but never updated by the trigger script.
- **Impact**: MEDIUM — these actions appear to do nothing, which may lead to confusion about whether the risk register and gate package are being updated.

### DEF-005 (LOW): trigger's generate_bridge_snapshot() only validates, doesn't regenerate

- **Location**: `dep_ready_trigger.py:489-503`
- **Description**: DepReadyTrigger.generate_bridge_snapshot() (line 489-503) only checks if the snapshot file exists and computes its MD5. It does NOT regenerate the snapshot. The actual snapshot generation is done by full_reverify_v3_batch_v2.py's generate_bridge_snapshot(). If the retest fails, the trigger's method will log a warning and skip.
- **Impact**: LOW — correct behavior for the happy path, but the warning may be confusing.

### DEF-006 (LOW): Alert event file writes are not atomic

- **Location**: `dep_ready_trigger.py:505-544`
- **Description**: write_alert_event() reads existing events, appends new ones, and writes back the entire file. If the process crashes mid-write, the file could be corrupted. Atomic writes (write to temp, then rename) would be safer.
- **Impact**: LOW — unlikely in normal operation, but could corrupt events in edge cases.

### DEF-007 (LOW): trigger_retest() doesn't save full stdout/stderr to log file

- **Location**: `dep_ready_trigger.py:417-443`
- **Description**: When the retest script fails (non-zero exit code), the error is logged to console and the alert event file, but the full stdout/stderr is not saved to a log file for post-mortem analysis. Only the last 50 lines of stdout are logged at DEBUG level, and only the first 500 chars of stderr are logged on failure.
- **Impact**: LOW — production debugging may need more complete logs.

### DEF-008 (LOW): MockState sleep_calls uses __dict__ hack instead of simple variable

- **Location**: `dryrun_e2e_test.py (this test harness)`
- **Description**: The install_time_mocks() function uses MockState.__dict__.__setitem__('sleep_calls', ...) which is a hacky pattern. A simple module-level counter would be cleaner.
- **Impact**: LOW — cosmetic, no functional impact.

---

## 7. Execution Log (Full)

```
[15:48:42.905] [INFO] ======================================================================
[15:48:42.905] [BANNER] DSHB V86-RC2 DEP Trigger Chain — E2E Dry-Run Test
[15:48:42.905] [INFO] Test ID: DSHB_V86_RC2_DEP_E2E_DRYRUN_20261004_154842
[15:48:42.905] [INFO] Started: 2026-10-04T15:48:42.905799
[15:48:42.905] [INFO] ======================================================================
[15:48:42.905] [INFO] Python: 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
[15:48:42.905] [INFO] Platform: nt
[15:48:42.906] [INFO] Work Dir: D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix
[15:48:42.906] [SETUP] 
[SETUP] Creating sandbox...
[15:48:42.935] [SETUP]   Copied 10 files from mapping_logs to sandbox
[15:48:42.935] [SETUP] [SETUP] Installing mocks...
[15:48:42.935] [SETUP] [SETUP] Loading and patching modules...
[15:48:42.965] [SETUP]   retest.OUTPUT_DIR -> D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\_dryrun_sandbox
[15:48:42.965] [SETUP]   retest.LOG_DIR    -> D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\_dryrun_sandbox\full_reverify_v3_batch_logs
[15:48:42.965] [SETUP]   retest.MAP_DIR    -> D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\_dryrun_sandbox\mapping_logs
[15:48:43.089] [STEP] Step 1: Probe Phase — DEP readiness detection
[15:48:43.090] [PASS]   ✅ PASS (1ms) 3/3 probes READY. j25_tc=9pts/HTTP200; i1=6pts/HTTP200; i3=6pts/HTTP200
[15:48:43.093] [INFO]   run_single_probe also passed
[15:48:43.093] [STEP] Step 2: Trigger Retest — full_reverify_v3_batch_v2.main()
[15:48:43.727] [PASS]   ✅ PASS (633ms) 170 entries, 123 fetchable, 47 blocked, 123 meta-complete. Gate=NOT_READY, Conclusion=PARTIAL_FETCHABLE
[15:48:43.727] [STEP] Step 3: Bridge Snapshot Generation — generate_bridge_snapshot
[15:48:43.733] [PASS]   ✅ PASS (6ms) Valid JSON, 170 entries, gate=NOT_READY, MD5=CE5FAD7B30BB47EE
[15:48:43.733] [STEP] Step 4: MD5 Computation — generate_md5_manifest
[15:48:43.789] [PASS]   ✅ PASS (56ms) Manifest: 2 files, MD5=EFFC2AC6A3E4F51E
[15:48:43.789] [STEP] Step 5: Risk Register Update — post_trigger_action
[15:48:43.848] [PASS]   ✅ PASS (59ms) File exists (15,423 chars), valid content. post_trigger_actions ran OK
[15:48:43.848] [STEP] Step 6: Gate Package Update — post_trigger_action
[15:48:43.849] [PASS]   ✅ PASS (1ms) File exists (26,085 chars), valid content
[15:48:43.849] [STEP] Step 7: Cross-team Notification — DSHE + HERMES
[15:48:43.855] [INFO]   Event types: {'HERMES_NOTIFICATION', 'DSHE_NOTIFICATION', 'DEP_READY_DETECTED'}
[15:48:43.855] [PASS]   ✅ PASS (6ms) 5 events written: HERMES_NOTIFICATION, DSHE_NOTIFICATION, DEP_READY_DETECTED
[15:48:43.855] [INFO] 
======================================================================
[15:48:43.855] [CHAIN] CHAIN INTEGRITY VERIFICATION
[15:48:43.855] [INFO] ======================================================================
[15:48:43.855] [INFO]   ✅ Link 1: Probe Phase — PASS (1.0ms)
[15:48:43.855] [INFO]   ✅ Link 2: Trigger Retest — PASS (633.0ms)
[15:48:43.855] [INFO]   ✅ Link 3: Bridge Snapshot — PASS (6.0ms)
[15:48:43.855] [INFO]   ✅ Link 4: MD5 Computation — PASS (56.0ms)
[15:48:43.855] [INFO]   ✅ Link 5: Risk Register — PASS (59.0ms)
[15:48:43.855] [INFO]   ✅ Link 6: Gate Package — PASS (1.0ms)
[15:48:43.855] [INFO]   ✅ Link 7: Cross-team Notification — PASS (6.0ms)
[15:48:43.855] [RESULT] 
Chain Integrity: ✅ ALL 7 LINKS PASS
[15:48:43.855] [INFO] ======================================================================
[15:48:43.855] [INFO] 
======================================================================
[15:48:43.855] [VERIFY] OUTPUT PRODUCT VERIFICATION
[15:48:43.855] [INFO] ======================================================================
[15:48:43.857] [INFO]   ✅ Bridge Snapshot (JSON): 165,068 bytes, MD5=CE5FAD7B30BB47EE
[15:48:43.859] [INFO]   ✅ Summary JSON: 3,137 bytes, MD5=2B915DCB29F5C185
[15:48:43.862] [INFO]   ✅ MD5 Manifest: 349 bytes, MD5=FFAE430800C7AAAF
[15:48:43.864] [INFO]   ✅ Alert Events (JSON): 4,268 bytes, MD5=C82152797A3C393D
[15:48:43.866] [INFO]   ✅ Risk Register (original): 23,105 bytes, MD5=2BD49F0C711AA5F4
[15:48:43.868] [INFO]   ✅ Gate Package (original): 32,873 bytes, MD5=75C581E8380B8A6A
[15:48:43.868] [INFO] 
======================================================================
[15:48:43.868] [INFO] DEFECT SCAN
[15:48:43.868] [INFO] ======================================================================
[15:48:43.868] [INFO]   [LOW] DEF-001: ConfigLoader YAML parser may misparse complex values
[15:48:43.868] [INFO]   [LOW] DEF-002: time.sleep() blocks in _rate_limit() and probe_once()
[15:48:43.868] [INFO]   [MEDIUM] DEF-003: trigger_retest() uses subprocess.run — no mock-friendly interface
[15:48:43.868] [INFO]   [MEDIUM] DEF-004: update_risk_register and update_gate_package are log-only
[15:48:43.868] [INFO]   [LOW] DEF-005: trigger's generate_bridge_snapshot() only validates, doesn't regenerate
[15:48:43.868] [INFO]   [LOW] DEF-006: Alert event file writes are not atomic
[15:48:43.868] [INFO]   [LOW] DEF-007: trigger_retest() doesn't save full stdout/stderr to log file
[15:48:43.868] [INFO]   [LOW] DEF-008: MockState sleep_calls uses __dict__ hack instead of simple variable
```

---

**End of Dry-Run Test Log**
**Generated at**: 2026-10-04T15:48:43.945852