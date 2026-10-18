# DSHD-P69 COM Lock and Excel Jitter Dashboard

**Generated**: 2026-10-18T09:29:59+08:00
**Poll Number**: #1730
**Session**: DSHD-P69
**Monitor Version**: v1.0
**Baseline**: feature/v88-g1 @ 01a022f
**Poll Interval**: 60s

---

## COM Health Assessment

[COM稳定] COM stability score: 100/100 | Excel=0 Orphan=0 Flash1min=0 WDFchg=0

**Overall**: [YELLOW] WARNING: wmain(NOT_RUNNING) | InitWAPI(RUNNING,PID=14188) | Excel(NONE) | Ports=0 | Flash5min=0 | Flash1min=0 | Orphan=0 | WDFchg=0 | CB=READY | SkillSHA=OK | ComScore=100/100 | Rating=COM稳定 -- All invariants with alerts: SESSION_VISIBILITY.

---

## COM Jitter Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Excel Flash Events (1min) | 0 | CLEAR |
| Excel Flash Events (5min) | 0 | CLEAR |
| Orphan Excel Count | 0 | CLEAR |
| WDF Load Changes (5min) | 0 | CLEAR |
| WDF Load Stability Score | 100/100 | COM稳定 |

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
| COM_JITTER_WARNING (>4 flash/5min) | CLEAR | 0 flash events |
| SESSION_VISIBILITY (wmain invisible 3 polls) | TRIGGERED | Streak: 6 |
| WDF_INIT_MISSING (InitWAPI disappeared) | CLEAR | Present |

---

## Process Status (Inherited)

| Process | PID | State | Start Time | Window Title | Visible |
|---------|-----|-------|------------|--------------|---------|
| wmain.exe | N/A | NOT_RUNNING | N/A | N/A | False |
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
| Monitor Log Lines | 1079 |
| Tracking Ledger Lines | 118 |
| COM Lock Events Lines | 0 |

---

*Dashboard auto-generated every 10 polls. Read-only observation. No remediation actions taken.*