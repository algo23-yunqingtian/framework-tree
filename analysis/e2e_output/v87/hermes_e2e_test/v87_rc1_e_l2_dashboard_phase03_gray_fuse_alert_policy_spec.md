# DSHE V87 RC1 Phase03 StageA — Gray Fuse Alert Policy Specification

**Document**: 87_rc1_e_l2_dashboard_phase03_gray_fuse_alert_policy_spec.md  
**Version**: v1.0.0-spec  
**Date**: 2027-03-16  
**Branch**: feature/v87-rc1-g1  
**Phase**: Phase03 StageA — 50% Gray Fuse Alert Policy  
**Author**: DSHE (L2 Display Layer)  
**Reviewers**: DSHB (L1 Business Layer), HERMES (L3 Audit Layer)  
**Status**: SPEC_LOCKED  
**Constraints**: BRANCH_LOCKED=TRUE | NO_MODIFY_V85=TRUE | NO_OVERWRITE=TRUE | NO_ZHIJI_API_CALL=TRUE | IE_AL_001_3LEVEL_PRESERVED=TRUE

---

## 1. Executive Summary

### 1.1 Phase Positioning

Phase03 StageA establishes the fuse alert policy for the 50% gray ramp phase. The policy defines a three-level decision model (GO / COND-GO / RED) mapped to four degradation levels (L0–L3), governing all 12 V87 alert rules and 8 panels under gray traffic conditions.

### 1.2 Key Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Gray traffic ratio | 50% | Work order DSHE_V87_RC1_L2_PHASE03 |
| Baseline traffic | V86 preserved (V100-1.0) | Phase02 baseline |
| Alert rules | 12 (8 V86-inherited + 4 V87-new) | Phase02 alert rule iteration |
| Panels | 8 V87 panels (7 active + 1 deferred) | Phase02 panel development |
| QPS protection threshold | 800 | Phase02 capacity evaluation |
| Gray QPS estimate | 560 (30% headroom) | 50% gray + baseline |
| Storage estimate (90d) | ~805GB (9.8% headroom) | 50% gray + baseline |
| Degradation levels | L0 normal → L1 throttle → L2 degrade → L3 read-only | Phase02 |
| Decision levels | GO / COND-GO / RED | V200-1.0 baseline |

### 1.3 Three-Level Decision Model

| Decision | Criteria | Action |
|----------|----------|--------|
| **GO** | All metrics within thresholds for 30+ min | Proceed with ramp; normal observation |
| **COND-GO** | Any metric in conditional range (within 80-95% of threshold) | Enhanced monitoring; delayed ramp decision |
| **RED** | Any metric exceeds critical threshold (sustained 3+ min) | Auto-trigger degradation; halt ramp; rollback if needed |

---

## 2. L0-L3 Degradation Mechanism

### 2.1 Degradation Level Definitions

| Level | Name | Trigger Condition | Panel Behavior | Query Behavior | Recovery |
|-------|------|------------------|----------------|----------------|----------|
| **L0** | Normal | All metrics within thresholds | All 7 active panels full resolution | Full query pipeline | N/A |
| **L1** | Throttle | Any metric in warning range (80-95% threshold) | All panels refresh rate reduced 50% (30s→60s) | Cache-only for low-priority queries | Auto-revert after 5min recovery |
| **L2** | Degrade | RED alert on heavy panel metric | Heavy panels (P-001/P-004/P-006/P-007) disabled; show static snapshots | Cache-only mode; no new queries for heavy panels | Manual recovery after root cause resolved |
| **L3** | Read-only | System-wide RED (QPS>700 or >2 concurrent CRITICAL) | All panels frozen; last known good state displayed | No write operations; read-only cache | Emergency only; full rollback triggered |

### 2.2 Degradation State Machine

`
L0 (Normal) ──[Warning breach]──→ L1 (Throttle)
  │                                    │
  │                                    ├──[Recovery 5min]──→ L0
  │                                    │
  │                                    └──[Sustained breach 3min]──→ L2
  │                                                                     │
  │                                                                     ├──[Root cause resolved]──→ L0
  │                                                                     │
  │                                                                     └──[System-wide RED]──→ L3
  │                                                                                              │
  └──[System-wide RED]──────────────────────────────────────────────────────────────────→ L3
`

### 2.3 Recovery Conditions

| Transition | Recovery Condition | Auto/Manual | Timeline |
|------------|-------------------|-------------|----------|
| L1 → L0 | All metrics within thresholds for 5 consecutive min | Auto | 5 min |
| L2 → L0 | Root cause resolved + all metrics within thresholds for 10 min | Manual | 10 min |
| L3 → L0 | Full rollback or manual recovery + verification | Manual | 30 min |
| L2 → L1 | Metrics improve to warning range | Auto | 3 min |
| L1 → L2 | Metrics deteriorate to RED range | Auto | 3 min |

---

## 3. Gray-Specific Alert Rules

### 3.1 V86-Inherited Rules (8 rules, gray-adapted)

| Rule | Metric | V86 Threshold | Gray Threshold | Gray Rationale | GO Range | COND-GO Range | RED Range |
|------|--------|--------------|---------------|---------------|----------|---------------|-----------|
| G-AL-001 | CPU Usage | >85% | >80% | Gray adds computation overhead | <70% | 70-80% | >80% |
| G-AL-002 | Memory Usage | >85% | >80% | Gray panels increase memory | <72% | 72-80% | >80% |
| G-AL-003 | Disk Usage | >80% | >75% | Gray storage growth | <70% | 70-75% | >75% |
| G-AL-004 | Network Latency | >5ms | >3ms | Gray adds query traffic | <2ms | 2-3ms | >3ms |
| H-AL-001 | Query P99 | >500ms | >300ms | V200-1.0 target ≤300ms | <200ms | 200-300ms | >300ms |
| H-AL-002 | Render P99 | >200ms | >150ms | V200-1.0 target ≤150ms | <100ms | 100-150ms | >150ms |
| CP-AL-005 | Capacity Forecast | Forecast breach | Forecast breach | V87 capacity prediction | Within forecast | ±5% forecast | >5% forecast |
| IE-AL-001 | Index Size (3-level) | CHECK>8.0% WARN>8.05% CRIT>8.5% | Same (preserved) | IE-AL-001 3-level preserved | <8.0% | 8.0-8.5% | >8.5% |

### 3.2 V87-New Rules (4 rules, gray-specific)

| Rule | Metric | Gray Threshold | GO Range | COND-GO Range | RED Range | Notes |
|------|--------|---------------|----------|---------------|-----------|-------|
| V87-AL-009 | Throughput | <900 ev/s | ≥900 ev/s | 850-900 ev/s | <850 ev/s | V200-1.0 baseline |
| V87-AL-010 | Packet Loss | >0.005% | <0.003% | 0.003-0.005% | >0.005% | V200-1.0 baseline |
| AUD-AL-001 | Audit Anomaly Rate | >2% | <0.5% | 0.5-2% | >2% | HERMES audit layer |
| AUD-AL-002 | Audit Mismatch Count | >10/10min | <3/10min | 3-10/10min | >10/10min | HERMES reconciliation |

### 3.3 IE-AL-001 Three-Level Preservation

IE-AL-001 retains its V86 three-level structure with AI anomaly detection overlay:

| Level | Threshold | Alert Type | Gray Action |
|-------|-----------|------------|-------------|
| CHECK | >8.0% | Info (no page) | Log only; monitor |
| WARNING | >8.05% | Warning (DingTalk) | Enhanced monitoring; delayed ramp |
| CRITICAL | >8.5% | Critical (PagerDuty) | Auto-trigger L2 degradation |

---

## 4. Alert Fusion Logic

### 4.1 Multi-Rule Correlation for Decision

| Scenario | Rules Involved | Decision | Action |
|----------|---------------|----------|--------|
| Single non-critical rule breach | Any 1 rule (COND-GO range) | COND-GO | Enhanced monitoring |
| Single critical rule breach | Any 1 rule (RED range) | RED | Auto-degrade |
| 2+ rules COND-GO breach | 2+ rules in COND-GO range | COND-GO | Enhanced monitoring; 15min observation |
| 2+ rules breach (mixed) | 1 RED + any COND-GO | RED | Immediate degrade |
| 2+ rules RED breach | 2+ rules in RED range | RED | L2→L3 escalation |
| System-wide breach | QPS>700 OR 3+ RED concurrent | RED | L3 read-only; rollback |

### 4.2 Time Window Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Evaluation window | 5 min rolling | Sliding window for metric aggregation |
| RED grace period | 3 min sustained | Metric must exceed RED threshold for 3 consecutive min |
| Recovery grace period | 5 min sustained | Metric must stay within GO range for 5 consecutive min |
| Storm detection window | 10 min | Alert storm threshold window |
| Repeat suppression window | 30 min | Duplicate alert suppression window |

### 4.3 Alert Storm Suppression

| Parameter | V86 | Gray (50%) | Rationale |
|-----------|-----|-----------|-----------|
| Max alerts per 10min | 20 | 5 | Lower volume in gray traffic |
| DBSCAN ε (time) | 60s | 30s | Tighter clustering for gray |
| DBSCAN min_samples | 3 | 2 | Lower minimum for gray volume |
| Maintenance window suppression | Active | Active | Scheduled maintenance excluded |
| Repeat suppression | 30min | 30min | Unchanged |

---

## 5. Automatic Panel Degradation Actions

### 5.1 RED → L1 (Throttle)

| Action | Timeline | Detail |
|--------|----------|--------|
| Reduce refresh rate | T+0 | All panels: 30s → 60s |
| Enable cache-only mode | T+15s | Low-priority queries served from cache |
| Notify on-call | T+30s | DingTalk notification |
| Log event | T+0 | Degradation event logged |

### 5.2 RED → L2 (Degrade)

| Action | Timeline | Detail |
|--------|----------|--------|
| Disable heavy panels | T+0 | P-001 (AI anomaly), P-004 (alert correlation), P-006 (full trace), P-007 (audit reconciliation) |
| Show static snapshots | T+15s | Last known good data displayed with "DEGRADED" banner |
| Pause heavy queries | T+30s | No new queries for disabled panels |
| Notify SRE lead | T+60s | PagerDuty escalation |
| Log event | T+0 | Degradation event logged with root cause hint |

### 5.3 RED → L3 (Read-only)

| Action | Timeline | Detail |
|--------|----------|--------|
| Freeze all panels | T+0 | All panels frozen at last known state |
| Disable write operations | T+0 | No metric ingestion; read-only cache |
| Trigger rollback procedure | T+30s | Pause gray traffic; verify baseline recovery |
| Notify TL + management | T+60s | Full escalation chain |
| Log event | T+0 | Critical event logged with full context |

### 5.4 Recovery Actions

| Level | Recovery Trigger | Action | Timeline |
|-------|-----------------|--------|----------|
| L1 → L0 | All metrics GO for 5min | Auto-revert refresh rate; re-enable queries | T+5min |
| L2 → L0 | Root cause resolved + 10min stable | Re-enable panels progressively; warm cache | T+10min |
| L3 → L0 | Rollback verified + manual approval | Full recovery; warm all caches; validate data | T+30min |

---

## 6. Notification and Escalation Matrix

### 6.1 Notification Channels

| Decision | Channel | Recipients | Timeline |
|----------|---------|------------|----------|
| GO | None | N/A | N/A |
| COND-GO | DingTalk #v87-gray-dshe | On-call SRE, DSHE ops | Within 1min |
| RED (L1) | DingTalk #v87-gray-dshe | On-call SRE, DSHE ops | Within 30s |
| RED (L2) | PagerDuty + DingTalk | SRE lead, DSHE TL | Within 60s |
| RED (L3) | PagerDuty + DingTalk + Email | TL, VP Eng, Release Manager | Within 60s |

### 6.2 Escalation Timeline

| Escalation | Trigger | Timeline | Recipients |
|------------|---------|----------|------------|
| E0 → E1 | RED detected | T+0 | On-call SRE |
| E1 → E2 | No ack within 5min | T+5min | SRE lead |
| E2 → E3 | L2 active >15min | T+15min | DSHE TL |
| E3 → E4 | L3 active or L2 >30min | T+30min | VP Engineering |
| E4 → E5 | Rollback triggered | T+30min | Release Manager |

---

## 7. Full Alert Rule Configuration (YAML)

`yaml
gray_fuse_alert_policy:
  version: "v87-rc1-phase03-stagea"
  gray_traffic_ratio: 50
  decision_model:
    levels: [GO, COND-GO, RED]
    evaluation_window: 5m
    red_grace_period: 3m
    recovery_grace_period: 5m
  degradation:
    levels: [L0, L1, L2, L3]
    auto_recovery:
      L1_to_L0: true
      L2_to_L0: false
      L3_to_L0: false
  alert_rules:
    G-AL-001:
      metric: cpu_usage_percent
      gray_threshold: 80
      go_range: { min: 0, max: 70 }
      cond_go_range: { min: 70, max: 80 }
      red_range: { min: 80, max: 100 }
      action: RED_L2
    G-AL-002:
      metric: memory_usage_percent
      gray_threshold: 80
      go_range: { min: 0, max: 72 }
      cond_go_range: { min: 72, max: 80 }
      red_range: { min: 80, max: 100 }
      action: RED_L2
    G-AL-003:
      metric: disk_usage_percent
      gray_threshold: 75
      go_range: { min: 0, max: 70 }
      cond_go_range: { min: 70, max: 75 }
      red_range: { min: 75, max: 100 }
      action: RED_L2
    G-AL-004:
      metric: network_latency_ms
      gray_threshold: 3
      go_range: { min: 0, max: 2 }
      cond_go_range: { min: 2, max: 3 }
      red_range: { min: 3, max: 100 }
      action: RED_L1
    H-AL-001:
      metric: query_p99_ms
      gray_threshold: 300
      go_range: { min: 0, max: 200 }
      cond_go_range: { min: 200, max: 300 }
      red_range: { min: 300, max: 1000 }
      action: RED_L1
    H-AL-002:
      metric: render_p99_ms
      gray_threshold: 150
      go_range: { min: 0, max: 100 }
      cond_go_range: { min: 100, max: 150 }
      red_range: { min: 150, max: 500 }
      action: RED_L1
    CP-AL-005:
      metric: capacity_forecast_breach
      gray_threshold: true
      go_range: { forecast: within }
      cond_go_range: { forecast: ±5% }
      red_range: { forecast: >5% }
      action: RED_L2
    IE-AL-001:
      metric: index_size_percent
      preserved_from_v86: true
      check_threshold: 8.0
      warning_threshold: 8.05
      critical_threshold: 8.5
      action: RED_L2
    V87-AL-009:
      metric: throughput_ev_per_s
      gray_threshold: 900
      go_range: { min: 900, max: 2000 }
      cond_go_range: { min: 850, max: 900 }
      red_range: { min: 0, max: 850 }
      action: RED_L1
    V87-AL-010:
      metric: packet_loss_percent
      gray_threshold: 0.005
      go_range: { min: 0, max: 0.003 }
      cond_go_range: { min: 0.003, max: 0.005 }
      red_range: { min: 0.005, max: 1.0 }
      action: RED_L2
    AUD-AL-001:
      metric: audit_anomaly_rate_percent
      gray_threshold: 2
      go_range: { min: 0, max: 0.5 }
      cond_go_range: { min: 0.5, max: 2 }
      red_range: { min: 2, max: 100 }
      action: RED_L2
    AUD-AL-002:
      metric: audit_mismatch_per_10min
      gray_threshold: 10
      go_range: { min: 0, max: 3 }
      cond_go_range: { min: 3, max: 10 }
      red_range: { min: 10, max: 1000 }
      action: RED_L2
  noise_suppression:
    dbscan:
      epsilon: 30
      min_samples: 2
    storm_suppression:
      max_alerts_per_10min: 5
    repeat_suppression:
      window: 30m
    maintenance_window:
      enabled: true
  system_wide_triggers:
    qps_threshold: 700
    concurrent_red_critical: 3
    action: L3
`

---

## 8. Status Markers

`
DSHE_L2_PHASE03_GRAY_FUSE_ALERT_POLICY=TRUE
DSHE_L2_PHASE03_GRAY_FUSE_DECISION_MODEL=GO_COND_GO_RED
DSHE_L2_PHASE03_GRAY_FUSE_DEGRADATION_LEVELS=4
DSHE_L2_PHASE03_GRAY_FUSE_DEGRADATION_L0=L1_L2_L3
DSHE_L2_PHASE03_GRAY_FUSE_RULES_TOTAL=12
DSHE_L2_PHASE03_GRAY_FUSE_RULES_V86_INHERITED=8
DSHE_L2_PHASE03_GRAY_FUSE_RULES_V87_NEW=4
DSHE_L2_PHASE03_GRAY_FUSE_IE_AL_001_3LEVEL_PRESERVED=TRUE
DSHE_L2_PHASE03_GRAY_FUSE_NOISE_SUPPRESSION_ENABLED=TRUE
DSHE_L2_PHASE03_GRAY_FUSE_AUTO_DEGRADATION_ENABLED=TRUE
DSHE_L2_PHASE03_GRAY_FUSE_L0_L1_AUTO_RECOVERY=TRUE
DSHE_L2_PHASE03_GRAY_FUSE_L2_L3_MANUAL_RECOVERY=TRUE
DSHE_L2_PHASE03_GRAY_FUSE_NOTIFICATION_CHANNELS=3
DSHE_L2_PHASE03_GRAY_FUSE_ESCALATION_LEVELS=5
DSHE_L2_PHASE03_GRAY_FUSE_EVALUATION_WINDOW=5min
DSHE_L2_PHASE03_GRAY_FUSE_RED_GRACE_PERIOD=3min
DSHE_L2_PHASE03_GRAY_FUSE_RECOVERY_GRACE_PERIOD=5min
DSHE_L2_PHASE03_GRAY_FUSE_STORM_SUPPRESSION_THRESHOLD=5_per_10min
DSHE_L2_PHASE03_GRAY_FUSE_SYSTEM_WIDE_QPS_TRIGGER=700
DSHE_L2_PHASE03_GRAY_FUSE_SYSTEM_WIDE_RED_TRIGGER=3_concurrent
DSHE_L2_PHASE03_GRAY_FUSE_ALERT_POLICY_LOCKED=TRUE
DSHE_L2_PHASE03_GRAY_FUSE_CROSS_REVIEW_DSHB=CONFIRMED
DSHE_L2_PHASE03_GRAY_FUSE_CROSS_REVIEW_HERMES=CONFIRMED
DSHE_L2_PHASE03_GRAY_FUSE_DONE=TRUE
DSHE_L2_PHASE03_DONE=TRUE
JOB_READY=TRUE
`

---

## 9. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| v1.0.0 | 2027-03-16 | DSHE | Initial spec for Phase03 StageA 50% gray fuse alert policy |