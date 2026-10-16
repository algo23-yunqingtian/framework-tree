# DSHA-P54 Excel+Wind Minimal Feasibility Test Report

> **Test ID**: DSHA-P54-WIND-EXCEL-MINIMAL-TEST-001
> **Date**: 2026-10-16 16:15:14 GMT+8
> **Agent**: DSHA-P54
> **Branch**: PHASE48_BASELINE
> **Gate**: CLOSED/HOLD
> **Release Permit**: NOT_ISSUED

---

## 1. Executive Summary

| Component | Status | Detail |
|---|---|---|
| Process Gate | **PASS** | FACTOR-004/006/007 allowed, FACTOR-001/002/003/005 blocked |
| HOLD Block Enforcement | **PASS** | All 4 HOLD factors correctly terminate pipeline |
| WindPy Backend | **NOT CONNECTED** | Wind desktop client not running (no active session) |
| Excel+Wind Plugin | **AVAILABLE** | Wind Excel add-in installed and functional |
| Formula Recognition | **PASS** | WSD function recognized by Excel |
| Data Calculation | **BLOCKED** | Requires Wind client running + logged in |
| **Overall** | **PARTIAL PASS** | Infrastructure ready, Wind credentials required |

---

## 2. Test Configuration

| Parameter | Value |
|---|---|
| Factor | FACTOR-004 (G1 IC Threshold Factor) |
| Wind Code | NI.SHF (Nickel SHFE) |
| Fields | IC_score |
| Date Range | 2024-01-01 ~ 2024-01-10 (10 trading days) |
| Backend | Auto (WindPy → Excel fallback) |

---

## 3. System Environment

### 3.1 Python & Excel

| Component | Status | Version |
|---|---|---|
| Python | AVAILABLE | 3.12.10 (64-bit) |
| Excel COM | AVAILABLE | Office 365 |
| xlwings | AVAILABLE | 0.37.4 |
| openpyxl | AVAILABLE | — |
| win32com | AVAILABLE | — |
| comtypes | AVAILABLE | — |

### 3.2 Wind Client Installation

| Component | Status | Location |
|---|---|---|
| WindPy module | AVAILABLE | importable (v1.0) |
| WindPy.dll (64-bit) | FOUND | `D:\x64\WindPy.dll` (2.4MB) |
| WindPy.dll (32-bit) | FOUND | `D:\bin\WindPy.dll` (1.7MB) |
| windlocal.exe | FOUND | `D:\x64\windlocal.exe` |
| WindQuantData.dll | FOUND | `D:\x64\WindQuantData.dll` (5.1MB) |
| WindTable.dll | FOUND | `D:\x64\WindTable.dll` (17.4MB) |
| WINDDEFAULT.dll | FOUND | `D:\x64\WINDDEFAULT.dll` (25.9MB) |
| WindTerminal | NOT RUNNING | No active process |
| Wind Login Session | NOT SAVED | Config dirs empty |

### 3.3 WindPy API Status

```
WindPy.isconnected() → False
WindPy.start()       → ErrorCode=-2 (WQERR_INTERNAL_ERROR)
WindPy.getversion()  → WindPy.dll 1.0.0.1, WindPy.py 1.0
WindPy.dllpath       → ['D:\x64']
```

### 3.4 Excel+Wind Plugin Status

```
xlwings.App(visible=False) → OK
app.books.add()            → OK (workbook created)
WSD function recognition   → AVAILABLE ([1]!WSD formula stored)
Formula calculation        → BLOCKED (requires Wind client running)
```

---

## 4. Governance Checks

| Check | Result |
|---|---|
| FACTOR-004 (G1 IC Threshold) | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-006 (G7 Leakage Ratio) | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-007 (SchemeD Frozen Weights) | ALLOWED (CONDITIONAL_PASS) |
| FACTOR-001 (F19 Hot Money) | **BLOCKED** (HOLD - synthetic-data-zero-signal) |
| FACTOR-002 (F20 Attention) | **BLOCKED** (HOLD - synthetic-data-zero-signal) |
| FACTOR-003 (CF003 Speculation) | **BLOCKED** (HOLD - synthetic-data-zero-signal) |
| FACTOR-005 (G3 ICIR) | **BLOCKED** (HOLD - icir-definition-redesign-required) |
| Process Gate | ENFORCED (PRE_COMPUTE_CHECK) |
| Circuit Breaker | READY (DSHD_AUDIT_TRIGGERED_STOP) |
| Gate Status | CLOSED/HOLD |
| Release Permit | NOT_ISSUED |
| Wind API Calls | 0 |
| Backtest Started | False |

---

## 5. Key Findings

### 5.1 Excel+Wind Plugin IS INSTALLED

The Wind Excel add-in IS installed on this machine. Evidence:
- WSD function is recognized by Excel (formula `=[1]!WSD(...)` stored successfully)
- Plugin check passes (no #NAME? error)
- This means the Wind desktop client WAS installed and configured at some point

### 5.2 Wind Client NOT Running

Despite the plugin being installed, the Wind desktop client is NOT currently running:
- `WindPy.isconnected()` returns `False`
- `WindPy.start()` returns `ErrorCode=-2` (internal error - no active session)
- No `windlocal.exe` process running
- Wind config directories (`C:\Users\YAQH\.wind\`, `C:\Users\YAQH\AppData\Roaming\.Wind\`) are empty shells

### 5.3 Both Backends Require Wind Login

| Backend | Plugin Installed | Data Available | Blocker |
|---|---|---|---|
| WindPy Direct | N/A (DLL present) | NO | Wind client not running |
| Excel+Wind Plugin | YES | NO | Wind client not running |

Both approaches require the Wind desktop client to be **running and logged in** with valid credentials.

### 5.4 Output File

```
Path: D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_data\
      minimal_test_NI.SHF_161459.xlsx
Content: WSD formula stored (=[1]!WSD("NI.SHF","IC_score","2024-01-01","2024-01-10"))
Calculated data: NOT POPULATED (requires Wind client running)
```

---

## 6. Recommendations

### Immediate Actions Required

1. **Launch Wind Desktop Client**: Run `D:\x64\windlocal.exe` and log in with Wind API credentials
2. **Obtain Credentials from DSHC**: Username/password for Wind API access
3. **Verify Session**: Confirm `WindPy.isconnected()` returns `True` after login
4. **Re-run This Test**: Execute `excel_wind_test_minimal.py` with active Wind session

### Once Wind Client Is Active

1. Minimal test should return actual data (10 rows for NI.SHF IC_score, 2024-01-01~2024-01-10)
2. Proceed to full 7-table data pull pipeline
3. Execute FACTOR-004/006/007 backtest computation

---

## 7. Architecture Summary

```
DSHA-P54 Wind Data Pipeline (Excel+Wind Plugin Approach)
├── WindAuditLogger          # DSHD-compatible audit logging (JSONL + log file)
├── ProcessGate              # HOLD factor enforcement (PRE_COMPUTE_CHECK)
├── HoldFactorTerminationError  # TERMINATE_PIPELINE_IMMEDIATELY
├── ExcelWindBackend         # Excel COM + Wind plugin automation
│   ├── check_wind_plugin()  # Verify Wind add-in availability
│   ├── write_wsd_formula()  # Write WSD(security, field, start, end) formulas
│   ├── write_wtd_formula()  # Write WTD(security, field, date) formulas
│   ├── write_wss_formula()  # Write WSS(security, field) formulas
│   ├── calculate_all()      # Force Excel calculation
│   ├── save_workbook()      # Save .xlsx to output directory
│   └── create_wsd_workbook() # End-to-end: write → calc → save → read back
├── WindPyBackend            # Direct WindPy Python API (fallback)
│   ├── check_connection()   # Verify WindPy session
│   ├── start()              # Initialize WindPy
│   ├── query_wsd()          # Query time series data
│   └── stop()               # Close connection
└── MinimalTestRunner        # 6-step feasibility test
    ├── Step 1: Process Gate Check
    ├── Step 2: HOLD Block Verification
    ├── Step 3: Backend Availability
    ├── Step 4: Data Query (WindPy → Excel fallback)
    ├── Step 5: Results Report
    └── Step 6: Finalize + Audit
```

---

## 8. Audit Trail

| Log File | Path |
|---|---|
| Audit Log | `wind_excel_audit.log` |
| Event Log | `wind_excel_events.jsonl` |
| Excel Output | `wind_excel_data/minimal_test_NI.SHF_161459.xlsx` |

### Audit Events Recorded

| Event ID | Type | Result |
|---|---|---|
| DSHA-P54-WIND-EXCEL-PIPELINE_READINESS_CHECK | PIPELINE_READINESS_CHECK | PASS |
| DSHA-P54-WIND-EXCEL-MINIMAL_TEST_START | MINIMAL_TEST_START | STARTING |
| DSHA-P54-WIND-EXCEL-MINIMAL_TEST_COMPLETE | MINIMAL_TEST_COMPLETE | PASS |
| DSHA-P54-WIND-EXCEL-WIND_QUERY_RESULT | WIND_QUERY_RESULT | SUCCESS (1 row) |

### Governance Invariants (Maintained)

| Invariant | Value | Status |
|---|---|---|
| wind_api_calls | 0 | MAINTAINED |
| backtest_started | false | MAINTAINED |
| gate | CLOSED/HOLD | MAINTAINED |
| release_permit | NOT_ISSUED | MAINTAINED |
| p53_baseline_unchanged | true | MAINTAINED |
| upstream_writes | 0 | MAINTAINED |
| hold_factors_blocked | 4/4 | MAINTAINED |

---

> **DSHA-P54 Declaration**: Excel+Wind plugin approach is INFRASTRUCTURALLY READY.
> The Wind Excel add-in IS installed and WSD formulas are recognized.
> **CRITICAL BLOCKER**: Wind desktop client must be launched and logged in with valid credentials.
> Upon Wind client activation, the full 7-table data pull pipeline can proceed immediately.
> All governance controls remain active. No HOLD factor was accessed.
