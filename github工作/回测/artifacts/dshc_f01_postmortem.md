# DSHC-F01 Postmortem — GUI全量金属行情采集

> **Ticket**: DSHC-F01  
> **Status**: PARTIAL_FETCH  
> **Commit**: 593d688 (feature/v88-g1)  
> **Finalize commit**: (this commit)  
> **Date**: 2026-10-19

---

## 1. Executive Summary

GUI-simulated Wind data fetch for 7 symbols × 4 indicators = 28 combinations.  
24/28 combos succeeded, producing 7,362 rows of market data (threshold: 300 ✅).  
LC.SHF (Lithium Carbonate) returned no data for any indicator — confirmed Wind-empty symbol.  
Token A01-USER-REMOTE-F01 = EXHAUSTED (one-time, non-reusable).  
Gate remains CLOSED/HOLD. No release_permit issued.

---

## 2. Data Collected

| Symbol | CLOSE | VOL | OI | SETTLE |
|---|---|---|---|---|
| ZN.SHF | 400 rows | 27 rows | 400 rows | 400 rows |
| CU.SHF | 400 rows | 27 rows | 400 rows | 400 rows |
| PB.SHF | 400 rows | 27 rows | 400 rows | 400 rows |
| AL.SHF | 400 rows | 27 rows | 400 rows | 400 rows |
| SN.SHF | 400 rows | 27 rows | 400 rows | 400 rows |
| NI.SHF | 400 rows | 27 rows | 400 rows | 400 rows |
| **LC.SHF** | **NO DATA** | **NO DATA** | **NO DATA** | **NO DATA** |

- **CLOSE/OI/SETTLE**: 400 rows each (2025-01-02 → 2026-08-26, ~400 trading days)
- **VOL**: 27 rows each (2026-09-03 → 2026-10-19, sparse — Wind data availability)
- **LC.SHF**: All 4 indicators returned dates with empty values — no data in Wind for this symbol

---

## 3. Guard Results

| Guard | Rule | Result |
|---|---|---|
| GR1_SINGLE_WINDOW | Max 1 Excel COM instance | ✅ ENFORCED |
| GR2_SPAWN_CAP | Hard limit 1 spawn per execution | ✅ ENFORCED (1 spawned) |
| GR3_CLEANUP_ON_EXIT | Try/finally Excel lifecycle | ✅ ENFORCED (1 leak killed) |
| GR4_NULL_GUARD | Null check after COM access | ✅ ENFORCED |
| GR5_WALL_CLOCK | 600s hard timeout | ✅ ENFORCED (538.4s used) |

- PID 14644 (protected Excel): ALIVE throughout execution
- Temp Excel PID: 22160, cleaned up on exit

---

## 4. Key Technical Findings

### 4.1 Clipboard Format (CRITICAL)

WSD range copy via `Range.Copy()` + `Get-Clipboard` produces **space-separated date-value pairs on a single line**:
```
date1\tvalue1 date2\tvalue2 date3\tvalue3 ...
```
NOT newline-separated TSV. Parsing regex: `(\d{4}-\d{2}-\d{2})\t(\S+)`

### 4.2 LC.SHF — No Data

All 4 indicators (CLOSE/VOL/OI/SETTLE) returned dates but empty B-column values.  
Confirmed from T1FIX lessons.json (`lc_shf_status` field).  
**Action**: Marked as WIND_EMPTY_SYMBOL in lessons.json permanent blacklist.

### 4.3 VOL Data Sparse

All VOL indicators returned only 27 rows (2026-09-03 → 2026-10-19).  
Wind's `Fill=Previous` does not fill missing VOL data. This is a Wind data availability issue.

### 4.4 GC Cleanup Hang

`[GC]::WaitForPendingFinalizers()` hung indefinitely after collecting 24 combos.  
**Fix**: Removed `WaitForPendingFinalizers()`, replaced with immediate leaked-Excel kill after `GC.Collect()`.

### 4.5 Row-Based Formula Placement

Each combo uses different Excel rows (advancing by 405) to avoid the B1 ClearContents bug  
where `Range.ClearContents()` fails to clear spilled WSD array formula results.

---

## 5. Error Log

| Run | Error | Root Cause | Fix |
|---|---|---|---|
| 1 | Clipboard parsing returned 0 rows | Clipboard is single-line space-separated, not TSV | Regex `(\d{4}-\d{2}-\d{2})\t(\S+)` |
| 2 | PS 5.1 variable syntax error | `$sym/$ind:` parsed as drive-qualified | Changed to `${sym}/${ind}` |
| 3 | GC cleanup hang | `WaitForPendingFinalizers()` blocked | Removed, immediate leak-kill |
| 4 | SUCCESS | — | — |

---

## 6. Script Lock

`scripts/dshc_f01_gui_fetch.ps1` is **version-locked** at commit 593d688.  
No further modifications to F01 fetch logic.  
Changes require a new workorder ticket.

---

## 7. Artifacts Archived

| File | Description |
|---|---|
| `artifacts/dshc_f01_receipt.json` | Execution receipt (24/28 combos, 7362 rows) |
| `artifacts/dshc_f01_events.jsonl` | Full execution trace (157 events) |
| `artifacts/dshc_f01_postmortem.md` | This document |
| `output_sample/wdf_sample_metals_raw.csv` | Raw CSV (7362 data rows, long format) |
| `scripts/dshc_f01_gui_fetch.ps1` | Fetch script (version-locked) |
| `scripts/diag_clipboard.ps1` | Clipboard format diagnostic tool |
| `artifacts/dshc_t1_lessons.json` | Updated with LC.SHF blacklist + F01 script lock |
