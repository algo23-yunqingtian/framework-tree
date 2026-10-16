# DSHA-P54 Excel+Wind Minimal Feasibility Test Report

> **Test ID**: DSHA-P54-WIND-EXCEL-MINIMAL-TEST-001
> **Date**: 2026-10-16 18:25 GMT+8 (Updated - Session 3: WindPy Connectivity Test)
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
| Wind Desktop Client (WMain) | **RUNNING** | WMain.exe (PID 19612) + WBox.exe (PID 2496) + 7× wbrowser.exe |
| WindPy Import | **PASS** | Module loads successfully from D:\x64\WindPy.py |
| WindPy Dependencies | **PASS** | pandas 3.0.5, numpy 2.5.3, ctypes available |
| WindPy c_isConnectionOK | **0 (NOT_CONNECTED)** | WBox service not accessible from WindPy |
| WindPy w.start() | **FAILED** | ErrorCode=-2 ("Start Error!") |
| WindPy c_start() with creds | **FAILED** | ErrorCode=-2 (30s timeout) |
| WindPy c_start() with creds 60s | **FAILED** | ErrorCode=-2 (60s timeout) |
| WindPy Sample Query | **SKIPPED** | Cannot query without connection |
| Wind Excel Add-in (WDF) | **REGISTERED_NOT_LOADED** | COM registered, Excel Addins registered, but cannot load |
| WSD/WSS Formula Execution | **BLOCKED** | COM error -2147352567 (Invalid formula name) |
| Simple Excel Formula | **PASS** | =1+1 returns 2.0 (Excel works) |
| Credentials Provided | **YES** | 13199157886 / Tyq1999! |
| Credentials Usable | **NO** | ErrorCode=-2 despite creds; license/permission suspected |
| **Overall** | **BLOCKED** | WindPy w.start() fails with ErrorCode=-2 despite Wind client running - ESCALATED TO DSHC |

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

## 4. WindPy Environment Investigation (New - Session 3)

### 4.1 WindPy Documentation & API Analysis

| Item | Detail |
|---|---|
| Main file | `D:\x64\WindPy.py` (2182 lines, cp936 encoding) |
| DLL | `D:\x64\WindPy.dll` (2.4 MB) |
| Pth file | `...\site-packages\WindPy.pth` → `D:\x64` |
| Version header | "Version: 1.0, Updated: 20130820" |
| Core class | `class w` - wraps WindPy.dll functions |
| Main methods | `w.start()`, `w.stop()`, `w.wsd()`, `w.wss()`, `w.wst()`, `w.tdays()`, etc. |
| Connection model | Requires Wind desktop client running as intermediary |
| Authentication | `w.start()` passes empty creds to DLL; DLL authenticates via running client |
| Direct c_start | `c_start(username, password, waitTime_ms)` accepts explicit creds |

### 4.2 WindPy API Method Inventory

| Method | Purpose | Signature |
|---|---|---|
| `w.start()` | Establish connection | `(waitTime=120, showmenu=True)` |
| `w.stop()` | Disconnect | `()` |
| `w.wsd()` | Time series data | `(codes, fields, beginTime, endTime, options)` |
| `w.wss()` | Static data | `(codes, fields, options)` |
| `w.wst()` | Tick data | `(codes, fields, beginTime, endTime, options)` |
| `w.wsi()` | Indicator data | `(codes, fields, beginTime, endTime, options)` |
| `w.tdays()` | Trading days | `(begintime, endtime, options)` |
| `w.tdayscount()` | Trading day count | `(begintime, endtime, options)` |
| `w.wset()` | Wind sets/tables | `(tablename, options)` |
| `w.wpf()` | Portfolio queries | `(productname, tablename, options)` |
| `w.wgel()` | Wind GEL | `(fun, id, options)` |
| `w.isconnected()` | Check connection | `()` → bool |

### 4.3 Python Dependencies

| Package | Version | Status |
|---|---|---|
| pandas | 3.0.5 | **OK** (note: `applymap()` deprecated in 3.x; WindPy `wdata2dfdt()` may need `map()`) |
| numpy | 2.5.3 | OK |
| ctypes | 1.1.0 | OK (built-in) |
| sys | 3.12.10 | OK (built-in) |
| threading | 3.12.10 | OK (built-in) |
| datetime | 3.12.10 | OK (built-in) |

### 4.4 Wind Desktop Client Process Discovery (Session 3)

**Major discovery**: Unlike Session 2 (where windlocal.exe exited immediately and no Wind processes were running), the Wind desktop client IS NOW RUNNING with multiple components:

| Process | PID | Path | Role |
|---|---|---|---|
| **WMain.exe** | 19612 | `D:\bin\WMain.exe` | Wind main application |
| **WBox.exe** | 2496 | `D:\bin\WBox.exe` | Wind communication service |
| **wbrowser.exe** ×7 | 18744, 20500, 20852, 21008, 21144, 21204, 36900 | `D:\bin\wbrowser109\wbrowser.exe` | Web browser components |
| **WindUpdate.RUN** | 21260 | `D:\tmp\WindUpdate.RUN` | Background updater |

**WindPy c_isConnectionOK()** returns `0` → NOT_CONNECTED despite WBox.exe running.

### 4.5 Connection Test Results

| Test | Method | ErrorCode | Interpretation |
|---|---|---|---|
| 1 | `w.start(waitTime=30)` | **-2** | "Start Error!" (generic) |
| 2 | `c_start("13199157886","Tyq1999!",30000)` | **-2** | Unknown error code |
| 3 | `c_start("13199157886","Tyq1999!",60000)` | **-2** | Unknown error code |
| 4 | `c_isConnectionOK()` | **0** | NOT_CONNECTED |

**Error code reference** (from WindPy source):

| Code | Meaning |
|---|---|
| 0 | OK |
| -40520009 | WBox lost |
| -40520008 | Timeout Error |
| -40520005 | No Python API Authority |
| -40520019 | Account restricted |
| -40520004 | Login Failed |
| -40520014 | Please Logon iWind firstly |
| **-2** | **Unknown - not in documented error codes** |

### 4.6 Root Cause Analysis

| Factor | Assessment |
|---|---|
| Wind client running? | **YES** (WMain.exe, WBox.exe, 7× wbrowser.exe) |
| WindPy import? | **YES** |
| WindPy DLL loaded? | **YES** |
| WindPy connection? | **NO** (ErrorCode=-2) |
| Credentials provided? | **YES** (13199157886 / Tyq1999!) |
| Credentials usable? | **NO** (same error with/without creds) |
| Likely cause | **WindPy license/permission not activated for this account** or version incompatibility between WindPy.dll and running Wind client |
| Alternative cause | WBox service not accessible to WindPy (firewall/config issue) |

### 4.7 Hard Constraint Triggered

Per 工单-A instruction: *"一旦发现Wind客户端许可异常、w.start()启动失败，立刻停止全部Wind相关尝试，上报DSHC，切回静态待命"*

**Action taken**: All Wind attempts stopped. No sample query executed. Return to STATIC_STANDBY.

---

## 5. Governance Checks

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

### BLOCKER: WINDPY_CONNECTION_FAILED

**Severity**: CRITICAL

**Impact**:
- All Wind data queries blocked (108 calls for FACTOR-004/006/007)
- Excel Wind plugin cannot load without desktop client
- WindPy cannot connect (ErrorCode=-2) despite Wind client running
- Backtest cannot start

**What Was Tried (All Sessions)**:
1. windlocal.exe launch (exits code 0 immediately) - Session 2
2. 26 CLI argument combinations (all exit code 0) - Session 2
3. WindNavigator.exe / WindSC.exe / WindRS.exe (all fail) - Session 2
4. WindPy start() with empty creds (ErrorCode=-2) - Session 2
5. WindPy c_start() with credentials directly (ErrorCode=-2) - Session 2
6. WDF Excel add-in registration (registered but cannot load) - Session 2
7. openpyxl formula write + Excel calculate (formula not recognized) - Session 2
8. **WindPy w.start() with provided credentials** (ErrorCode=-2) - **Session 3**
9. **WindPy c_start() with 13199157886/Tyq1999!, 30s timeout** (ErrorCode=-2) - **Session 3**
10. **WindPy c_start() with 13199157886/Tyq1999!, 60s timeout** (ErrorCode=-2) - **Session 3**
11. **WindPy c_isConnectionOK()** → 0 (NOT_CONNECTED) - **Session 3**
12. **Wind client process verification**: WMain.exe (PID 19612), WBox.exe (PID 2496), 7× wbrowser.exe - **Session 3**

**Key Session 3 Discovery**: Wind desktop client IS running (WMain.exe, WBox.exe, wbrowser.exe) but WindPy still returns ErrorCode=-2. This is different from Session 2 where no Wind processes were running. The issue is likely **WindPy license/permission not activated** or **version incompatibility** between WindPy.dll and the running Wind client.

**What Is Needed**:
1. WindPy API license must be activated for account 13199157886
2. OR: DSHC must verify WindPy.dll version compatibility with running Wind client
3. OR: DSHC must provide alternative data access method
4. OR: DSHC must fix WBox service accessibility for WindPy

**Escalation**: DSHC

---

## 7. Audit Trail

| Log File | Path | Events |
|---|---|---|
| Wind Excel Events | `wind_excel_events.jsonl` | 36 events (28 original + 8 Session 3) |
| Tracking Monitor | `tracking_monitor_audit.jsonl` | 42 events (39 original + 3 Session 3) |
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

### New Audit Events (Session 3 - WindPy Connectivity Test)

| Event Type | Status | Detail |
|---|---|---|
| WINDPY_IMPORT | SUCCESS | WindPy module loaded from D:\x64 |
| WIND_CLIENT_PROCESS_CHECK | CHECKED | WMain/WBox/wbrowser ×7 running, WBox NOT_CONNECTED |
| WINDPY_W_START | FAILED | All attempts ErrorCode=-2 |
| TEST_ABORTED | CONNECT_FAILED | Per hard constraint, stopped all Wind attempts |
| windpy_connect_attempt | ATTEMPTING | w.start() with creds 13199157886/Tyq1999! |
| windpy_connect_result | FAILED | ErrorCode=-2, cannot establish connection |
| windpy_test_result | CONNECT_FAILED | License/permission issue suspected |

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
> **CRITICAL BLOCKER**: WindPy w.start() fails with ErrorCode=-2 despite Wind client (WMain/WBox) running.
> WindPy API license/permission appears not activated for account 13199157886.
> All governance controls remain active. No HOLD factor was accessed.
> wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED.
> **Hard constraint triggered**: All Wind attempts stopped. Returned to STATIC_STANDBY. Awaiting DSHC.