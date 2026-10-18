# DSHD-P70 Orphan Excel Cleanup Safe Guard Dashboard

**Generated**: 2026-10-18T10:17:12+08:00
**Poll Number**: #1760
**Session**: DSHD-P70
**Monitor Version**: v1.0
**Baseline**: feature/v88-g1 @ 01a022f
**Poll Interval**: 60s

---

## COM Health Assessment

[优秀] COM stability score: 100/100 | Excel=0 Orphan=0 Flash1min=0 WDFchg=0

**Overall**: [GREEN] OK: wmain(RUNNING,PID=824,visible=True) | InitWAPI(RUNNING,PID=14188) | Excel(NONE) | Ports=0 | Flash5min=2 | Flash1min=0 | Orphan=0 | WDFchg=0 | CB=READY | SkillSHA=OK | ComScore=100/100 | Rating=优秀 -- All invariants passing

---

## COM Jitter Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Excel Flash Events (1min) | 0 | CLEAR |
| Excel Flash Events (5min) | 2 | CLEAR |
| Orphan Excel Count | 0 | CLEAR |
| WDF Load Changes (5min) | 0 | CLEAR |
| WDF Load Stability Score | 100/100 | 优秀 |

---

## Excel Process Detail

*No EXCEL.EXE processes running.*

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
| COM_JITTER_WARNING (>4 flash/5min) | CLEAR | 2 flash events |
| SESSION_VISIBILITY (wmain invisible 3 polls) | CLEAR | Streak: 0 |
| WDF_INIT_MISSING (InitWAPI disappeared) | CLEAR | Present |

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

## Process Status (Inherited)

| Process | PID | State | Start Time | Window Title | Visible |
|---------|-----|-------|------------|--------------|---------|
| wmain.exe | 824 | RUNNING | 2026-10-18T10:11:59+08:00 | Wind金融终端..Alice | True |
| InitWAPI.exe | 14188 | RUNNING | 2026-10-17T16:33:32+08:00 | N/A | N/A |
| EXCEL.EXE | N/A | NOT_RUNNING | N/A | N/A | N/A |
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
| Wind TCP Ports (62000-64000) | 0 |
| .wind/users File Count | 0 |
| Credential Alert | NONE |
| Wind API Calls | 0 |
| Skill SHA Check | ALL_MATCH |
| Monitor Log Lines | 1149 |
| Tracking Ledger Lines | 149 |
| COM Lock Events Lines | 16 |

---

*Dashboard auto-generated every 10 polls. Read-only observation. No remediation actions taken.*