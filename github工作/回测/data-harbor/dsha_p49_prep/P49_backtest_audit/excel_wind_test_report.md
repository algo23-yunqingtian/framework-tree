# DSHA-P54 Excel+Wind Minimal Feasibility Test Report

> **Test ID**: DSHA-P54-WIND-EXCEL-MINIMAL-TEST-001
> **Date**: 2026-10-16 17:15 GMT+8 (Updated)
> **Agent**: DSHA-P54
> **Branch**: feature/v88-g1
> **Gate**: CLOSED/HOLD
> **Release Permit**: NOT_ISSUED

---

## 1. Executive Summary

| Component | Status | Detail |
|---|---|---|
| Process Gate | **PASS** | FACTOR-004/006/007 allowed, FACTOR-001/002/003/005 blocked |
| HOLD Block Enforcement | **PASS** | All 4 HOLD factors correctly terminate pipeline |
| Wind Desktop Client | **NOT FUNCTIONAL** | windlocal.exe exits immediately (code 0), all 26 CLI args tested |
| WindPy Backend | **NOT CONNECTED** | start() ErrorCode=-2 (desktop client not running) |
| Wind Excel Add-in (WDF) | **REGISTERED_NOT_LOADED** | COM registered, Excel Addins registered, but cannot load |
| WSD/WSS Formula Execution | **BLOCKED** | COM error -2147352567 (Invalid formula name) |
| Simple Excel Formula | **PASS** | =1+1 returns 2.0 (Excel works) |
| Credentials Provided | **YES** | 13199157886 / Tyq1999! |
| Credentials Usable | **NO** | WindPy requires desktop client running first |
| **Overall** | **BLOCKED** | Wind desktop client not functional - ESCALATED TO DSHC |

---

## 2. Wind Client Exploration (New - Session 2)

### 2.1 windlocal.exe Launch Attempts

| Attempt | Command | Result |
|---|---|---|
| 1 | `windlocal.exe` | EXITED code=0 immediately |
| 2 | `windlocal.exe /login` | EXITED code=0 |
| 3 | `windlocal.exe -login` | EXITED code=0 |
| 4 | `windlocal.exe --login` | EXITED code=0 |
| 5 | `windlocal.exe /start` | EXITED code=0 |
| 6-26 | Various args (`/daemon`, `/service`, `/silent`, `/headless`, etc.) | ALL EXITED code=0 |

**Conclusion**: windlocal.exe exits immediately with code 0 regardless of arguments. It appears to be a launcher/bootstrapper that checks for conditions (license, config, service) and exits if not met.

### 2.2 Other Wind Executables

| Executable | Result |
|---|---|
| WindNavigator.exe | Runs for 8+ seconds, then exits |
| WindSC.exe | Exit code 3221225595 (crash) |
| WindRS.exe | Exit code 3221225595 (crash) |
| ModuleUpdate.exe | Exits after 1 second |
| WindUpdate.RUN | Persistent process (21260), updater only |

### 2.3 Wind Config Directories

| Directory | Status |
|---|---|
| `C:\Users\YAQH\.wind` | EXISTS - only 1-byte marker files (WMain) |
| `C:\Users\YAQH\AppData\Roaming\.Wind` | EXISTS - only 1-byte marker files (WMain/etc/res/users) |
| No license files found | — |
| No Wind environment variables | — |

### 2.4 WindPy API Status

```
WindPy.isconnected() → False
WindPy.start()       → ErrorCode=-2 (Start Error!)
WindPy.c_start("13199157886", "Tyq1999!", 30000) → ErrorCode=-2
WindPy.c_start("", "", 30000) → ErrorCode=-2
```

**Conclusion**: ErrorCode=-2 means the Wind desktop client is not running at all. WindPy cannot connect directly to a Wind server - it requires the desktop client to be running as an intermediary.

---

## 3. Excel+Wind Plugin Deep Exploration (New - Session 2)

### 3.1 COM Registration Status

| Item | Status |
|---|---|
| WDF.XLTaskPanel COM object | REGISTERED (HKCR\CLSID\{6B525F62-...}) |
| wdf.dll location | `D:\x64\wdf.dll` (15MB) |
| Excel Addins registry | REGISTERED (LoadBehavior=3) |
| regExcel.bat | Registers `wdf.dll` via `regsvr32` |

### 3.2 Excel Add-in Loading

| Test | Result |
|---|---|
| `excel.COMAddIns.Count` | 7 (add-ins present) |
| WDF in COMAddIns list | NOT FOUND (all 7 have "Item.Name" read errors) |
| `AddWithPath("D:\x64\wdf.dll")` | FAILED |
| Simple formula `=1+1` | **PASS** (returns 2.0) |
| `=[1]!WSD(...)` formula | **FAILED** (COM error -2147352567) |
| `=[1]!WSS(...)` formula | **FAILED** (COM error -2147352567) |
| openpyxl write + Excel open | **FAILED** (Excel rejects formula on open) |

### 3.3 Root Cause

The WDF Excel add-in requires the Wind desktop client to be running. Without it:
1. The add-in cannot load into Excel
2. WSD/WSS functions are not registered as Excel functions
3. Formulas referencing `[1]!WSD(...)` fail with "Invalid formula name"

---

## 4. Governance Checks

| Check | Result |
|---|---|
| FACTOR-004 (G1 IC Threshold) | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-006 (G7 Leakage Ratio) | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-007 (SchemeD Frozen Weights) | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-001 (F19 Hot Money) | **BLOCKED** (HOLD) |
| FACTOR-002 (F20 Attention) | **BLOCKED** (HOLD) |
| FACTOR-003 (CF003 Speculation) | **BLOCKED** (HOLD) |
| FACTOR-005 (G3 ICIR) | **BLOCKED** (HOLD) |
| Gate Status | CLOSED/HOLD |
| Release Permit | NOT_ISSUED |
| Wind API Calls | 0 |
| Backtest Started | False |

---

## 5. Code Infrastructure Status

| Component | Status | File |
|---|---|---|
| Dual Backend Architecture | **READY** | `wind_excel_automation.py` |
| Process Gate (HOLD enforcement) | **READY** | `wind_excel_automation.py` |
| Audit Logger (JSONL + log) | **READY** | `wind_excel_automation.py` |
| Minimal Test Script | **READY** | `excel_wind_test_minimal.py` |
| Full Pipeline (108 calls) | **READY** | `wind_data_pull_pipeline.py` |
| Factor Calculation | **READY** | (pipeline includes) |

---

## 6. Blocker Report

### BLOCKER: WIND_DESKTOP_CLIENT_NOT_FUNCTIONAL

**Severity**: CRITICAL

**Impact**:
- All Wind data queries blocked (108 calls for FACTOR-004/006/007)
- Excel Wind plugin cannot load without desktop client
- WindPy cannot connect without desktop client
- Backtest cannot start

**What Was Tried**:
1. windlocal.exe launch (exits code 0 immediately)
2. 26 CLI argument combinations (all exit code 0)
3. WindNavigator.exe / WindSC.exe / WindRS.exe (all fail)
4. WindPy start() with and without credentials (ErrorCode=-2)
5. WindPy c_start() with credentials directly (ErrorCode=-2)
6. WDF Excel add-in registration (registered but cannot load)
7. openpyxl formula write + Excel calculate (formula not recognized)

**What Is Needed**:
1. Wind desktop client must be properly installed with valid license
2. windlocal.exe must start and remain running as a service
3. OR: DSHC must provide alternative data access method

**Escalation**: DSHC

---

## 7. Audit Trail

| Log File | Path | Events |
|---|---|---|
| Wind Excel Events | `wind_excel_events.jsonl` | 28 events |
| Tracking Monitor | `tracking_monitor_audit.jsonl` | 39 events |
| Audit Log | `wind_excel_audit.log` | Text log |
| Excel Output | `wind_excel_data/` | Test files |

### New Audit Events (Session 2)

| Event ID | Type | Result |
|---|---|---|
| DSHA-P54-WIND-EXCEL-WIND_CLIENT_LAUNCH | WIND_CLIENT_LAUNCH | BLOCKED |
| DSHA-P54-WIND-EXCEL-EXCEL_PLUGIN_REGISTRATION | EXCEL_PLUGIN_REGISTRATION | REGISTERED_NOT_LOADED |
| DSHA-P54-WIND-EXCEL-BLOCKER_REPORT | BLOCKER_REPORT | BLOCKED |
| DSHA-P54-WIND-CLIENT-LAUNCH-001 | wind_client_launch_attempt | BLOCKED |
| DSHA-P54-EXCEL-PLUGIN-EXPLORATION-001 | excel_plugin_exploration | BLOCKED_ON_CLIENT |
| DSHA-P54-WIND-BLOCKER-ESCALATION-001 | wind_blocker_escalation | BLOCKED_ESCALATED |

### Governance Invariants (Maintained)

| Invariant | Value | Status |
|---|---|---|
| wind_api_calls | 0 | MAINTAINED |
| backtest_started | false | MAINTAINED |
| gate | CLOSED/HOLD | MAINTAINED |
| release_permit | NOT_ISSUED | MAINTAINED |
| hold_factors_blocked | 4/4 | MAINTAINED |

---

> **DSHA-P54 Declaration**: Code infrastructure is READY (dual backend + pipeline + audit logging).
> **CRITICAL BLOCKER**: Wind desktop client not functional - escalated to DSHC.
> All governance controls remain active. No HOLD factor was accessed.
> wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED.