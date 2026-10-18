# DSHD-P71 Sample Run Audit Relay Dashboard

**Generated**: 2026-10-18T21:31:27+08:00
**Poll Number**: #2380
**Session**: DSHD-P71
**Monitor Version**: v1.0
**Baseline**: feature/v88-g1 @ 01a022f
**Poll Interval**: 60s (current: 60)s

---

## COM Health Assessment

[优秀] COM stability score: 100/100 | Excel=1 Orphan=0 Flash1min=0 WDFchg=0

**Overall**: [YELLOW] WARNING: wmain(RUNNING,PID=824,visible=True) | InitWAPI(RUNNING,PID=14188) | Excel(count=1) | Ports=0 | Flash5min=0 | Flash1min=0 | Orphan=0 | WDFchg=0 | CB=TRIPPED | SkillSHA=FAIL(skill_readme.md,bootstrap_wdf.ps1,skill_manifest.json,health_check_wdf.ps1,reset_wdf_safe.ps1) | ComScore=100/100 | Rating=优秀 | SampleMarker=ABSENT | SampleActive=NO | P86Ready=READY-WAITING -- All invariants with alerts: WIND_API_CALLS_GT0, SKILL_HASH_MISMATCH.

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
| 14644 | 【永安期货研究中心】锌数据库-锭篇 - Excel | True | NO | 2026-10-18T15:50:01+08:00 | 143.6 | WDF.dll |

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
| TRACKING_JSON_NEW_ERRORS (P73: new JSON parse errors) | CRITICAL | TRACKING_JSON_NEW_ERRORS_CRITICAL: 93 new JSON parse errors (lines: 243,303,737,791,837,841,845,853,857,864,868,875,880,887,892,899,901,902,904,905,907,908,910,911,913,914,915,917,918,920,921,923,924,926,927,928,930,931,933,934,936,938,939,941,942,944,945,946,948,949,951,952,954,955,957,958,960,961,964,965,967,968,970,971,973,974,976,977,978,980,981,983,984,986,987,989,990,991,993,994,996,997,999,1000,1002,1003,1005,1006,1008,1009,1272,1274,1275) |

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
| Total Parse Errors | 93 |
| Historical DSHA-P54 Artifacts | 0 |
| New JSON Parse Errors | 93 |
| Historical Error Lines | 243, 303, 737, 791, 837 |
| Alert Status | CRITICAL - New errors detected |
| Threshold Rule | Historical DSHA-P54 encoding artifacts → INFO log only; new JSON parse errors → CRITICAL alert |

> **P73 Threshold**: Historical tracking_monitor_audit.jsonl encoding artifacts (13 lines from DSHA-P54 with Chinese characters) do NOT trigger CRITICAL. New parse errors WILL trigger CRITICAL.

---

## Process Status (Inherited)

| Process | PID | State | Start Time | Window Title | Visible |
|---------|-----|-------|------------|--------------|---------|
| wmain.exe | 824 | RUNNING | 2026-10-18T10:11:59+08:00 | Wind金融终端..Alice | True |
| InitWAPI.exe | 14188 | RUNNING | 2026-10-17T16:33:32+08:00 | N/A | N/A |
| EXCEL.EXE | 14644 | RUNNING | N/A | N/A | N/A |
| windlocal.exe | N/A | NOT_RUNNING | N/A | N/A | N/A |
| python.exe/pythonw.exe | N/A | NOT_RUNNING | N/A | N/A | N/A |

---

## Invariants Status (Inherited)

| Invariant | Expected | Actual | Status |
|-----------|----------|--------|--------|
| gate | CLOSED/HOLD | CLOSED/HOLD | PASS |
| release_permit | NOT_ISSUED | NOT_ISSUED | PASS |
| wind_api_calls | 0 | 2212495360 | FAIL |
| credential_alert | NONE | NONE | PASS |
| circuit_breaker | READY | TRIPPED | FAIL |
| hold_block_check | PASS | FAIL | FAIL |
| ledger_append_only | TRUE | TRUE | PASS |

---

## System Details (Inherited)

| Item | Value |
|------|-------|
| Wind TCP Ports (62000-64000) | 0 |
| .wind/users File Count | 0 |
| Credential Alert | NONE |
| Wind API Calls | 2212495360 |
| Skill SHA Check | MISMATCH: skill_readme.md, bootstrap_wdf.ps1, skill_manifest.json, health_check_wdf.ps1, reset_wdf_safe.ps1 |
| Monitor Log Lines | 1436 |
| Tracking Ledger Lines | 1275 |
| COM Lock Events Lines | 29 |

---

*Dashboard auto-generated every 10 polls. Read-only observation. No remediation actions taken.*