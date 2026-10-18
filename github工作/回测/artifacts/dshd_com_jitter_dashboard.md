# DSHD-P71 Sample Run Audit Relay Dashboard

**Generated**: 2026-10-18T13:03:56+08:00
**Poll Number**: #1910
**Session**: DSHD-P71
**Monitor Version**: v1.0
**Baseline**: feature/v88-g1 @ 01a022f
**Poll Interval**: 60s (current: 60)s

---

## COM Health Assessment

[优秀] COM stability score: 100/100 | Excel=1 Orphan=0 Flash1min=0 WDFchg=0

**Overall**: [YELLOW] WARNING: wmain(RUNNING,PID=824,visible=True) | InitWAPI(RUNNING,PID=14188) | Excel(count=1) | Ports=1 | Flash5min=0 | Flash1min=0 | Orphan=0 | WDFchg=0 | CB=READY | SkillSHA=FAIL(skill_readme.md,bootstrap_wdf.ps1,skill_manifest.json,reset_wdf_safe.ps1) | ComScore=100/100 | Rating=优秀 | SampleMarker=ABSENT | SampleActive=NO | P86Ready=READY-WAITING -- All invariants with alerts: SKILL_HASH_MISMATCH.

---

## COM Jitter Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Excel Flash Events (1min) | 0 | CLEAR |
| Excel Flash Events (5min) | 0 | CLEAR |
| Orphan Excel Count | 0 | CLEAR |
| WDF Load Changes (5min) | 0 | CLEAR |
| WDF Load Stability Score | 100/100 | 优秀 |

---

## Excel Process Detail

| PID | Window | Visible | Orphan | Start Time | Working Set (MB) | WDF Modules |
|-----|--------|---------|--------|------------|------------------|-------------|
| 28272 | 铅周报240127 - Excel | True | NO | 2026-10-18T11:56:33+08:00 | 484.3 | WDF.dll |

---

## WDF Addin Load Behavior

| HIVE | LoadBehavior | State |
|------|-------------|-------|
| HKCU | 3 | ALWAYS_LOAD |
| HKLM | 3 | ALWAYS_LOAD |
| XL Task Panel | 2 | LOAD_ON_DEMAND |

---

## Recent WDF LoadBehavior Changes (Last 10)

*No WDF LoadBehavior changes recorded.*

---

## Alert Status

| Alert | Status | Detail |
|-------|--------|--------|
| COM_JITTER_ALERT (>3 start/stop/1min) | CLEAR | 0 events in 1min |
| COM_ORPHAN_PROCESS_WARNING | CLEAR | None |
| WDF_LOAD_FLAP_WARNING (>2 changes/5min) | CLEAR | 0 changes in 5min |
| COM_JITTER_WARNING (>4 flash/5min) | CLEAR | 0 flash events |
| SESSION_VISIBILITY (wmain invisible 3 polls) | CLEAR | Streak: 0 |
| WDF_INIT_MISSING (InitWAPI disappeared) | CLEAR | Present |
| SESSION_FLICKER (P71: visible/invisible flicker 3 polls) | CLEAR | History: VVV |
| SAMPLE_ACTIVE_OBSERVING (P71: marker+python running) | CLEAR | Not active |
| TRACKING_JSON_NEW_ERRORS (P73: new JSON parse errors) | CRITICAL | TRACKING_JSON_NEW_ERRORS_CRITICAL: 2 new JSON parse errors (lines: 2,5) |

---

## P70 Cleanup Guard Status

| Item | Value |
|------|-------|
| Guard Status | STATIC_STANDBY |
| Cleanup Marker | NOT_FOUND |
| Marker Path | D:\DSH_WORK\github工作\回测\artifacts\com_clean_allow.marker |
| Guard Action Taken | NO |
| Target Orphan PIDs | 22660, 25976 |
| Cleanup Actions Total | 0 |
| COM Graceful Exits | 0 |
| Taskkill Fallbacks | 0 |
| Skipped (Windowed) | 0 |

*No guard actions this poll (no marker or no orphans).*

> **Red Line**: No cleanup without marker. Never kills windowed Excel, wmain, or InitWAPI.

---

## P71 Sample Readiness Status (NEW)

| Item | Value |
|------|-------|
| SAMPLE_CONTROLLER_READY | READY-WAITING |
| SAMPLE_MARKER_STATUS | ABSENT |
| Sample Marker Path | D:\DSH_WORK\github工作\回测\artifacts\sample_fetch_allow.marker |
| RECENT_ALERT_COUNT (10min) | 0 |
| Total WSS Alert Lines | 0 |
| Alerts Indexed Total | 0 |
| New Alerts This Poll | 0 |
| Python Prototype Running | NO |
| SAMPLE_ACTIVE_OBSERVING | NO |
| CURRENT_COM_HEALTH | 100/100 (优秀) |
| 风险评级 | 环境就绪，适合点火 |

> **Red Line**: DSHD never creates/deletes sample_fetch_allow.marker. DSHD never calls controller or Python scripts. DSHD only observes.

---

## Offline Factor Framework Readiness (P73 NEW)

| Item | Value |
|------|-------|
| DSHA-P59 Artifact Status | NOT_FOUND |
| Offline Factor Framework Readiness | ARTIFACT_FOUND |
| Artifact Path | D:\DSH_WORK\github工作\回测\artifacts\cross_agent_artifact_index.json |
| P89 Cross-Index Status | CROSS_INDEX_IN_PROGRESS |
| Note | DSHA-P59 offline factor framework artifact not yet published. P89 cross-agent artifact index in progress. |

> **Status**: Offline factor framework (DSHA-P59) pending. DSHC-P89 artifact cross-indexing underway. DSHD observes only.

---

## Tracking Log JSON Integrity (P73 NEW)

| Metric | Value |
|--------|-------|
| Total Parse Errors | 15 |
| Historical DSHA-P54 Artifacts | 13 |
| New JSON Parse Errors | 2 |
| Historical Error Lines | 2, 5, 8, 11, 12 |
| Alert Status | CRITICAL - New errors detected |
| Threshold Rule | Historical DSHA-P54 encoding artifacts → INFO log only; new JSON parse errors → CRITICAL alert |

> **P73 Threshold**: Historical tracking_monitor_audit.jsonl encoding artifacts (13 lines from DSHA-P54 with Chinese characters) do NOT trigger CRITICAL. New parse errors WILL trigger CRITICAL.

---

## Process Status (Inherited)

| Process | PID | State | Start Time | Window Title | Visible |
|---------|-----|-------|------------|--------------|---------|
| wmain.exe | 824 | RUNNING | 2026-10-18T10:11:59+08:00 | Wind金融终端..Alice | True |
| InitWAPI.exe | 14188 | RUNNING | 2026-10-17T16:33:32+08:00 | N/A | N/A |
| EXCEL.EXE | 28272 | RUNNING | N/A | N/A | N/A |
| windlocal.exe | N/A | NOT_RUNNING | N/A | N/A | N/A |
| python.exe/pythonw.exe | N/A | NOT_RUNNING | N/A | N/A | N/A |

---

## Invariants Status (Inherited)

| Invariant | Expected | Actual | Status |
|-----------|----------|--------|--------|
| gate | CLOSED/HOLD | CLOSED/HOLD | PASS |
| release_permit | NOT_ISSUED | NOT_ISSUED | PASS |
| wind_api_calls | 0 | 0 | PASS |
| credential_alert | NONE | NONE | PASS |
| circuit_breaker | READY | READY | PASS |
| hold_block_check | PASS | PASS | PASS |
| ledger_append_only | TRUE | TRUE | PASS |

---

## System Details (Inherited)

| Item | Value |
|------|-------|
| Wind TCP Ports (62000-64000) | 1 |
| .wind/users File Count | 0 |
| Credential Alert | NONE |
| Wind API Calls | 0 |
| Skill SHA Check | MISMATCH: $($skillHashFailed -join  ) |
| Monitor Log Lines | 1327 |
| Tracking Ledger Lines | 305 |
| COM Lock Events Lines | 24 |

---

*Dashboard auto-generated every 10 polls. Read-only observation. No remediation actions taken.*