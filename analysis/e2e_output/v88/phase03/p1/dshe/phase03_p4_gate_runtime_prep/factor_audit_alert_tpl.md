# Factor Audit Alert Template — Pre-Event Template (v1.0.0)

> **TASK_ID**: V88_PHASE03_P4_DSHE_P015_GATE_MONITOR_READY / T6
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED: TRUE)
> **GENERATED**: 2026-10-17T00:59 UTC+8
> **STATUS**: ✅ TEMPLATE READY — No fake alerts generated

---

## 1. Purpose

Prepare a structured audit alert template for factor computation (IC/IR) runtime events. This is a **template only** — no actual alerts are generated. When a real factor computation event occurs, this template can be used to generate a 1-click audit note.

---

## 2. Template Structure

```
┌─────────────────────────────────────────────────────────────┐
│  FACTOR RUNTIME AUDIT ALERT                                  │
├─────────────────────────────────────────────────────────────┤
│  Alert ID:      FACTOR-{{YYYYMMDD}}-{{SEQ}}                 │
│  Timestamp:     {{ISO_TIMESTAMP}}                            │
│  Severity:      {{INFO | WARNING | CRITICAL}}                │
│  Rule ID:       {{FR-001 ~ FR-006}}                          │
│  Rule Name:     {{rule_name}}                                │
│  Agent:         DSHE                                         │
│  Branch:        feature/v88-g1                               │
│  Phase:         Phase04_IC_IR                                │
├─────────────────────────────────────────────────────────────┤
│  Event Details:                                              │
│    Matched Path:  {{matched_path}}                           │
│    Match Detail:  {{match_detail}}                           │
│    File Size:     {{file_size_bytes}}                        │
│    SHA256:        {{sha256_hash}}                            │
│    MD5:           {{md5_hash}}                               │
│    Extension:     {{file_extension}}                         │
├─────────────────────────────────────────────────────────────┤
│  Action Taken:                                               │
│    Auto-Kill:     FALSE (never enabled)                      │
│    Auto-Modify:   FALSE (never enabled)                      │
│    Auto-Git:      FALSE (never enabled)                      │
│    Action:        {{alert_only | alert_and_log}}              │
├─────────────────────────────────────────────────────────────┤
│  Escalation:                                                │
│    Auto-Escalate: FALSE                                     │
│    Manual Review Required: TRUE                              │
│    Contact:       DSHE_AGENT                                 │
├─────────────────────────────────────────────────────────────┤
│  Audit Trail:                                               │
│    Recorded In:  opt_hooks/factor_runtime_audit_log.jsonl    │
│    Alert Log:    opt_hooks/factor_runtime_alert_log.txt     │
│    JSON Alert:   opt_hooks/factor_runtime_alerts.json        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Severity Levels

| Level | Description | Action | Response Time |
|:-----:|-------------|--------|:-------------:|
| **INFO** | Informational — no action needed | Log only | None required |
| **WARNING** | Potential issue detected — manual review needed | Log + notify | <4h |
| **CRITICAL** | Immediate attention required | Log + escalate (manual) | <1h |

---

## 4. Alert Categories

### 4.1 File Extension Violation (FR-001)

```
Severity: WARNING
Template: FACTOR-{{YYYYMMDD}}-001
Example: Factor output file with non-whitelisted extension (.exe, .bat, .dll)
Action: alert_only
```

### 4.2 File Size Exceeded (FR-002)

```
Severity: WARNING (100MB) / CRITICAL (500MB)
Template: FACTOR-{{YYYYMMDD}}-002
Example: Factor output file exceeds 100MB threshold
Action: alert_only
```

### 4.3 Rapid Bulk File Creation (FR-003)

```
Severity: WARNING (>500 files/5min) / CRITICAL (>2000 files/5min)
Template: FACTOR-{{YYYYMMDD}}-003
Example: Suspicious rapid file creation in factor_workspace
Action: alert_only
```

### 4.4 Plaintext Credential Detected (FR-004)

```
Severity: CRITICAL
Template: FACTOR-{{YYYYMMDD}}-004
Example: API key, token, or secret found in factor output JSON
Action: alert_and_log
```

### 4.5 Cross-Directory Boundary Violation (FR-005)

```
Severity: WARNING
Template: FACTOR-{{YYYYMMDD}}-005
Example: Factor output references or writes outside factor_workspace
Action: alert_only
```

### 4.6 Factor Output Hash Mismatch (FR-006)

```
Severity: INFO
Template: FACTOR-{{YYYYMMDD}}-006
Example: Hash snapshot shows unexpected file change
Action: snapshot_only
```

---

## 5. Escalation Policy

```
┌─────────────────────────────────────────────────────────────┐
│  ESCALATION POLICY — FACTOR RUNTIME                          │
├─────────────────────────────────────────────────────────────┤
│  Auto-Escalate:       FALSE                                  │
│  Manual Review:       REQUIRED for all WARNING+ alerts       │
│  Escalation Contact:  DSHE_AGENT                             │
│  HERMES Escalation:   Manual only (no auto-trigger)          │
│  WIND Escalation:     N/A (Wind link not active)             │
├─────────────────────────────────────────────────────────────┤
│  Escalation Triggers:                                        │
│  1. CRITICAL severity alert                                  │
│  2. Multiple WARNING alerts within 1 hour                   │
│  3. Credential leak detected (FR-004)                        │
│  4. Boundary violation targeting protected directories       │
├─────────────────────────────────────────────────────────────┤
│  Manual Escalation Steps:                                    │
│  1. Review alert details in audit log                        │
│  2. Verify affected file(s)                                  │
│  3. If legitimate → update alert status to RESOLVED          │
│  4. If malicious → escalate to DSHE_AGENT for action         │
│  5. If uncertain → mark as PENDING_REVIEW                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Audit Record Format

Each alert generates a JSONL record:

```json
{
  "timestamp": "2026-10-17T00:59:00+08:00",
  "alert_id": "FACTOR-20261017-001",
  "severity": "WARNING",
  "rule_id": "FR-001",
  "rule_name": "output_file_extension_whitelist",
  "matched_path": "factor_workspace/xxx.suspicious",
  "match_detail": "Extension .suspicious not in whitelist",
  "file_size_bytes": 1024,
  "sha256": "abc123...",
  "md5": "def456...",
  "extension": ".suspicious",
  "action_taken": "alert_only",
  "auto_kill": false,
  "auto_modify": false,
  "auto_git": false,
  "manual_review_required": true,
  "escalation_contact": "DSHE_AGENT",
  "branch": "feature/v88-g1",
  "phase": "Phase04_IC_IR",
  "hook_version": "2.0.0-preview"
}
```

---

## 7. Template Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `{{YYYYMMDD}}` | Date in YYYYMMDD format | `20261017` |
| `{{SEQ}}` | Sequential alert number | `001`, `002`, ... |
| `{{ISO_TIMESTAMP}}` | ISO 8601 timestamp | `2026-10-17T00:59:00+08:00` |
| `{{INFO\|WARNING\|CRITICAL}}` | Severity level | `WARNING` |
| `{{FR-001 ~ FR-006}}` | Rule ID | `FR-001` |
| `{{rule_name}}` | Rule name from YAML | `output_file_extension_whitelist` |
| `{{matched_path}}` | Full path of matched file | `factor_workspace/xxx.json` |
| `{{match_detail}}` | Description of match | `File extension not whitelisted` |
| `{{file_size_bytes}}` | File size in bytes | `1024` |
| `{{sha256_hash}}` | SHA256 hash of file | `abc123...` |
| `{{md5_hash}}` | MD5 hash of file | `def456...` |
| `{{file_extension}}` | File extension | `.json` |
| `{{alert_only\|alert_and_log}}` | Action type | `alert_and_log` |

---

## 8. Usage Instructions

### 8.1 Auto-Generation (Future)

When factor_runtime_rules_v1.yaml is integrated into the monitoring pipeline:
1. Rules are evaluated on each scan cycle
2. Matched rules generate alerts using this template
3. Alerts are written to JSONL audit log
4. Summary written to alert log and JSON alert file
5. Manual review required for all WARNING+ alerts

### 8.2 Manual 1-Click Generation

For manual audit notes:
1. Copy the template structure from Section 2
2. Fill in the placeholder variables
3. Write to audit log or include in report
4. Mark review status

---

## 9. Constraints Compliance

| Constraint | Status |
|------------|:------:|
| No fake alerts generated | ✅ |
| Template only — no live events | ✅ |
| All severity levels documented | ✅ |
| Escalation policy defined | ✅ |
| Manual review required | ✅ |
| No auto-escalation to HERMES | ✅ |
| Branch locked | ✅ |
| No git operations | ✅ |

---

## 10. Declaration

> ✅ **FACTOR AUDIT ALERT TEMPLATE READY**
>
> - Template structure defined for 6 rule categories (FR-001 ~ FR-006)
> - 3 severity levels documented (INFO, WARNING, CRITICAL)
> - Escalation policy defined (manual only, no auto-escalation)
> - Audit record format specified (JSONL)
> - Template variables documented
> - Usage instructions provided
> - **NO fake alerts generated** — this is a template only
> - Ready for 1-click audit note generation when factor events occur

---

> **标记**: T6=COMPLETE | Factor Audit Alert Template Prepared
> *Generated: 2026-10-17T00:59 UTC+8 | DSHE | V88_PHASE03_P4_DSHE_P015_GATE_MONITOR_READY*