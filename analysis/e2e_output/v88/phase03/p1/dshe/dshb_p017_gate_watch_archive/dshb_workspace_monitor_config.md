# DSHB Workspace Monitor Configuration — P0-17 T3

> **TASK_ID**: V88_PHASE03_P6_DSHE_P017_GATE_RUNTIME_STANDBY / T3
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1
> **GENERATED**: 2026-10-17T02:30 UTC+8
> **PURPOSE**: Polling scan configuration for DSHB factor_workspace computation directory
> **MODE**: READ-ONLY — hash-only read, no file modification
> **STATUS**: CONFIGURED

---

## 1. Monitor Purpose

Configure a polling scan task to monitor DSHB's `factor_workspace/` computation directory. The monitor:
1. Reads file hashes only — does NOT modify any file
2. Detects anomalies (new files, modified files, unexpected changes)
3. Writes anomalies to audit log immediately
4. Does NOT auto-commit, does NOT intervene in business processes
5. Does NOT kill processes, does NOT modify outputs

---

## 2. Workspace Inventory

**DSHB Factor Workspace Path**: `github工作/framework-tree/factor_workspace/pb_zn_recyclepb_v1/`

### 2.1 Current Files

| # | File | Size (B) | Type | Status |
|---|------|--------:|------|:------:|
| 1 | `ic_ir_calc_skeleton.py` | 15,010 | Python script | ✅ SCANNED |
| 2 | `ic_ir_calc_skeleton.py.md5` | 150 | MD5 checksum | ✅ SCANNED |

### 2.2 Subdirectory Structure

| Directory | Purpose | Files | Status |
|-----------|---------|:-----:|:------:|
| `input/` | Factor computation inputs | 0 | ✅ EMPTY |
| `output/` | Factor computation outputs | 0 | ✅ EMPTY |
| `audit/` | Audit trail | 0 | ✅ EMPTY |
| `checksum/` | Checksums | 0 | ✅ EMPTY |

---

## 3. Monitor Configuration

### 3.1 Polling Parameters

| Parameter | Value | Unit |
|-----------|:-----:|:----:|
| Polling interval | 300 | seconds (5 min) |
| Scan depth | 10 | levels |
| Max files per scan | 5,000 | files |
| Hash algorithms | SHA256, MD5 | — |
| File read mode | READ-ONLY | — |
| File modification | NONE | — |
| File deletion | NONE | — |
| Process modification | NONE | — |

### 3.2 Anomaly Detection Rules

| Rule ID | Name | Trigger | Severity |
|---------|------|---------|:--------:|
| WM-001 | New file detection | Any new file in factor_workspace/ | WARNING |
| WM-002 | File hash change | Existing file hash differs from baseline | WARNING |
| WM-003 | File deletion detection | Existing file disappeared | CRITICAL |
| WM-004 | Large file alert | File > 100 MB | WARNING |
| WM-005 | Batch creation alert | >100 files in 5 min | CRITICAL |
| WM-006 | Unauthorized extension | File with .exe, .bat, .cmd, .ps1, .sh, .dll, .so, .dylib | CRITICAL |
| WM-007 | Boundary violation | Write outside factor_workspace/ | WARNING |
| WM-008 | Credential leak | Pattern match on plaintext credentials | CRITICAL |
| WM-009 | Hash chain break | File checksum mismatch vs .md5 file | WARNING |

### 3.3 Anomaly Response

| Action | Enabled | Note |
|--------|:-------:|------|
| Write to audit log | ✅ YES | Immediate append to `opt_hooks/factor_runtime_audit_log.jsonl` |
| Write to alert log | ✅ YES | Append to `opt_hooks/factor_runtime_alert_log.txt` |
| Write to alert JSON | ✅ YES | Append to `opt_hooks/factor_runtime_alerts.json` |
| Auto-escalate | ❌ NO | Manual escalation only |
| Kill process | ❌ NO | Never |
| Modify output | ❌ NO | Never |
| Delete file | ❌ NO | Never |
| Git operation | ❌ NO | Never |

---

## 4. Audit Log Format

```jsonl
{"timestamp":"2026-10-17T02:30:00Z","rule_id":"WM-001","severity":"WARNING","matched_path":"factor_workspace/pb_zn_recyclepb_v1/output/new_factor.json","match_detail":"New file detected, size=10240 bytes, sha256=...","action_taken":"logged_only"}
```

**Log path**: `opt_hooks/factor_runtime_audit_log.jsonl`
**Retention**: 90 days
**Format**: JSONL (one JSON object per line)

---

## 5. Monitor Integration

| Component | Integration |
|-----------|:-----------:|
| `blocker_monitor_hook_snippet.py` v2.1.0-preview | ✅ Primary scan engine |
| `factor_runtime_rules_v1.yaml` v1.1.0-preview | ✅ Rule definitions |
| `factor_workspace_hash_snapshot.json` | ✅ Baseline hash store |
| `factor_runtime_audit_log.jsonl` | ✅ Anomaly log |
| `factor_runtime_alert_log.txt` | ✅ Text alert log |
| `factor_runtime_alerts.json` | ✅ JSON alert store |

---

## 6. Safety Guarantees

| Guarantee | Status |
|-----------|:------:|
| Read-only file access | ✅ All operations are reads only |
| No file modification | ✅ Confirmed — no write to factor_workspace/ |
| No process modification | ✅ Confirmed — no kill, no start, no stop |
| No auto git commit | ✅ Confirmed — AUTO_COMMIT_MODE=False |
| No external API call | ✅ Confirmed — NO_ZHIJI_API_CALL=True |
| No business process intervention | ✅ Confirmed — observe-alert only |
| Anomaly detection only | ✅ Confirmed — all rules are detect-and-log |
| Manual escalation only | ✅ Confirmed — no auto-escalation |

---

## 7. Dual-Key Protocol Status

| Key | Status | Impact |
|:---:|:------:|--------|
| `WIND_DATA_LINK_ONLINE.flag` | ❌ NOT DETECTED | No monitoring intensity upgrade |
| `DUAL_KEYS_ACTIVE.flag` | ❌ NOT DETECTED | No enhanced scanning |
| Combined | ❌ INACTIVE | Basic watch level only |

**When both keys active**: Monitoring intensity will upgrade to enhanced watch, FR-007~009 rules activated, polling interval reduced to 60s.

---

## 8. Declaration

> ✅ **DSHB WORKSPACE MONITOR CONFIGURED — T3 COMPLETE**
>
> - Workspace: `factor_workspace/pb_zn_recyclepb_v1/` — full coverage
> - Files scanned: 2 (SHA256+MD5 baseline established)
> - Anomaly rules: 9 (WM-001 through WM-009)
> - Polling interval: 300s (basic watch)
> - Read-only: ✅ Confirmed
> - No modification: ✅ Confirmed
> - No auto-commit: ✅ Confirmed
> - Anomaly → audit log: ✅ Immediate
> - Dual keys: ❌ Inactive — basic watch only
>
> **Monitor is ready. Awaiting dual-key activation for intensity upgrade.**

---

> **标记**: T3=COMPLETE | DSHB workspace monitor configured
> **Polling scan, hash-only read, anomaly→audit log, no intervention**
> *Generated: 2026-10-17T02:30 UTC+8 | DSHE | V88_PHASE03_P6_DSHE_P017_GATE_RUNTIME_STANDBY*