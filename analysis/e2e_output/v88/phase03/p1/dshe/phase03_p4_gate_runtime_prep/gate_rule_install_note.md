# Factor Runtime Gate Rule Install Note

> **TASK_ID**: V88_PHASE03_P4_DSHE_P015_GATE_MONITOR_READY / T2
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED: TRUE)
> **GENERATED**: 2026-10-17T00:59 UTC+8
> **STATUS**: ✅ DEPLOYED — OBSERVE-ALERT-ONLY MODE

---

## 1. Overview

The factor runtime gate rule package (`factor_runtime_rules_v1.yaml`) has been deployed to `gate_rules/` for future factor computation (IC/IR) runtime monitoring.

---

## 2. Rule Package Summary

| Item | Value |
|------|-------|
| **Package name** | `factor_runtime_rules_v1` |
| **Version** | `1.0.0` |
| **Phase** | `Phase04_IC_IR` |
| **Role** | `factor_computation_runtime_monitor` |
| **Mode** | `observe_alert_only` |
| **Branch** | `feature/v88-g1` |
| **Location** | `gate_rules/factor_runtime_rules_v1.yaml` |

---

## 3. Rules Deployed (6 total)

| Rule ID | Name | Severity | Action | Description |
|---------|------|:--------:|:------:|-------------|
| `FR-001` | `output_file_extension_whitelist` | WARNING | alert | Approved file extensions only; blacklist for executables/scripts |
| `FR-002` | `single_file_size_threshold` | WARNING | alert | Alert at 100MB, critical at 500MB |
| `FR-003` | `rapid_bulk_file_creation` | WARNING | alert | >500 files in 5min = warning; >2000 = critical |
| `FR-004` | `plaintext_credential_scan` | CRITICAL | alert_and_log | Scan JSON outputs for leaked API keys/tokens |
| `FR-005` | `cross_directory_boundary_violation` | WARNING | alert | Monitor writes outside `factor_workspace/`; protect archived dirs |
| `FR-006` | `factor_output_triple_hash` | INFO | snapshot | SHA256 + MD5 snapshot of factor outputs for audit trail |

---

## 4. Safety Locks (Hard Constraints)

| Lock | Value | Description |
|------|:-----:|-------------|
| `auto_kill_process` | `false` | Will NEVER kill any process |
| `auto_modify_output` | `false` | Will NEVER modify any output file |
| `auto_delete_file` | `false` | Will NEVER delete any file |
| `auto_git_operation` | `false` | Will NEVER execute git add/commit/push |
| `auto_push` | `false` | Will NEVER push to remote |
| `intervention_level` | `observe_only` | Observe and alert, never intervene |
| `escalation_policy` | `notify_and_log` | Log and notify only; no auto-escalation |

---

## 5. WIND Data Link Status

| Item | Value |
|------|-------|
| Current status | `AWAITING_EXTERNAL_FLAG` |
| Flag file | `WIND_DATA_LINK_ONLINE.flag` |
| Active | `false` |
| Upgrade trigger | WIND_DATA_LINK_ONLINE.flag detected |

> The rule package will remain at current monitoring intensity until `WIND_DATA_LINK_ONLINE.flag` is placed in the repo root. No proactive data pull or Wind activation is performed.

---

## 6. Alert Configuration

| Parameter | Value |
|-----------|-------|
| Alerting enabled | `true` |
| Log target | `opt_hooks/factor_runtime_alert_log.txt` |
| JSON alert target | `opt_hooks/factor_runtime_alerts.json` |
| Deduplication window | 300 seconds |
| Max alerts per hour | 100 |
| Audit log | `opt_hooks/factor_runtime_audit_log.jsonl` |
| Audit retention | 90 days |

---

## 7. Escalation Policy

| Parameter | Value |
|-----------|-------|
| Auto-escalate | `false` |
| Manual escalation required | `true` |
| Escalation contact | `DSHE_AGENT` |

> All alerts require manual review. No automatic escalation to HERMES or other agents.

---

## 8. Boundary Protection

The rule package explicitly protects the following directories from cross-directory writes:

| Protected Directory | Protection |
|---------------------|:----------:|
| `scripts/` | ❌ FORBIDDEN |
| `github工作/framework-tree/scripts/` | ❌ FORBIDDEN |
| `analysis/.../p012_nativepass_consolidate/` | ❌ FORBIDDEN |
| `analysis/.../cross_align_ARCHIVED/` | ❌ FORBIDDEN |
| `analysis/.../p012_cpu_exception_ARCHIVED/` | ❌ FORBIDDEN |
| `analysis/.../opt-phase04-psutil-collector/` | ❌ FORBIDDEN |

---

## 9. Deployment Mode

```
DEPLOYED: factor_runtime_rules_v1.yaml
  Mode: OBSERVE-ALERT-ONLY
  Active: TRUE (loaded into monitoring logic)
  WIND active: FALSE
  Auto-kill: FALSE
  Auto-modify: FALSE
  Auto-git: FALSE
```

---

## 10. Future Activation Path

1. **WIND_DATA_LINK_ONLINE.flag** detected → monitoring intensity upgrade
2. **Phase04 formal work order** → collector activation
3. **IC/IR factor computation** → runtime monitoring rules become active
4. **All rules remain observe-alert** — no automatic intervention at any phase

---

> **标记**: T2=COMPLETE | Factor Runtime Gate Rules Deployed (observe-alert-only)
> *Generated: 2026-10-17T00:59 UTC+8 | DSHE | V88_PHASE03_P4_DSHE_P015_GATE_MONITOR_READY*