# DSHE V87-RC1 L2 Dashboard Phase02 Panel Development Report

**Document ID**: DSHE-V87-RC1-L2-P02-DEV-RPT-001  
**Revision**: 1.0  
**Classification**: Internal / Engineering  
**Date**: 2025-01-15  
**Work Order**: `DSHE_V87_RC1_L2_PHASE02_V87_DASHBOARD_DEVELOP_AND_ALERT_RULE_ITERATE`  
**Phase**: Phase02 — Panel Development & Alert Rule Iteration  
**Program**: DSHE V87-RC1 L2 Dashboard Enhancement  

---

## Document Status Markers

```
DSHE_L2_PHASE02_V87_PANEL_DEV_START=TRUE
DSHE_L2_PHASE02_V87_PANEL_TOTAL=8
DSHE_L2_PHASE02_V87_PANEL_P1=6
DSHE_L2_PHASE02_V87_PANEL_P2=2
DSHE_L2_PHASE02_V87_PANEL_DEFERRED=1
DSHE_L2_PHASE02_V87_PANEL_BASELINE_V200_1_0=TRUE
DSHE_L2_PHASE02_V87_PANEL_5HERMES_FIELDS_INTEGRATED=TRUE
```

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Panel Development Overview](#2-panel-development-overview)
3. [V87-P-001: AI Anomaly Detection Panel](#3-v87-p-001-ai-anomaly-detection-panel)
4. [V87-P-002: Cross-Service Dependency Topology Panel](#4-v87-p-002-cross-service-dependency-topology-panel)
5. [V87-P-003: Automated Capacity Planning Panel](#5-v87-p-003-automated-capacity-planning-panel)
6. [V87-P-004: Alert Correlation Analysis Panel](#6-v87-p-004-alert-correlation-analysis-panel)
7. [V87-P-005: Chaos Engineering Automation Panel (Design Only)](#7-v87-p-005-chaos-engineering-automation-panel-design-only)
8. [V87-P-006: Full Trace Panel](#8-v87-p-006-full-trace-panel)
9. [V87-P-007: Audit Reconciliation Panel](#9-v87-p-007-audit-reconciliation-panel)
10. [V87-P-008: Baseline Drift Heatmap Panel](#10-v87-p-008-baseline-drift-heatmap-panel)
11. [Cross-Panel Integration & Data Flow Architecture](#11-cross-panel-integration--data-flow-architecture)
12. [Technical Implementation Details](#12-technical-implementation-details)
13. [Performance Budget & Optimization Plan](#13-performance-budget--optimization-plan)
14. [Quality Assurance Plan](#14-quality-assurance-plan)
15. [Risk Assessment & Mitigation](#15-risk-assessment--mitigation)
16. [Development Timeline & Milestones](#16-development-timeline--milestones)
17. [Appendix](#17-appendix)

---

## 1. Executive Summary

### 1.1 Phase02 Scope

Phase02 of the DSHE V87-RC1 L2 Dashboard program transitions from the Phase01 requirements lock (which defined 8 new V87 panels) to active development and alert rule iteration. This report documents the complete technical specification, architecture, and implementation plan for the 8 new panels that will be developed in this phase, alongside the iteration of alert rules to support the expanded V87 monitoring surface.

### 1.2 Objectives

| Objective | Description | Measurement |
|-----------|-------------|-------------|
| O1 — Panel Delivery | Develop and deploy 8 new V87 panels (6×P1, 2×P2, 1 deferred) | All panels pass integration + performance gates |
| O2 — Metric Expansion | Expand V200-1.0 baseline metrics from 24 to 32 | All 8 new metrics instrumented and queryable |
| O3 — Alert Rule Iteration | Iterate from 9 to 12 alert rules (8 frozen + IE-AL-001 three-level + 3 new) | All rules validated against P99 thresholds |
| O4 — Performance Compliance | All panels meet V200-1.0 performance budgets | Render P99 ≤150ms, Load P99 ≤2s (or per-panel budget) |
| O5 — HERMES V87 Integration | Integrate 5 new audit fields into relevant panels | event_type, priority, trace_id, batch_id, retry_count |
| O6 — Cross-Panel Data Flow | Establish unified data plane across all 33 panels | Event bus integration, shared cache layer |

### 1.3 Key Metrics

| Metric | V86 (Previous) | V87 Target | Delta |
|--------|---------------|------------|-------|
| Panel Count | 25 | 33 | +8 (+32%) |
| Metric Count | 24 (V100-1.0) | 32 (V200-1.0) | +8 (+33%) |
| Alert Rules | 9 (8 frozen + 1 IE-AL-001) | 12 (iterated) | +3 (+33%) |
| Baseline Version | V100-1.0 | V200-1.0 | Major upgrade |
| AI Models | 1 (Prophet) | 3 (Prophet + Isolation Forest + LSTM) | +2 |
| Data Sources | 2 (HERMES L3, DSHB Registry) | 5 (+ClickHouse, OTel Tracing, DSHB V87 SDK) | +3 |

### 1.4 V200-1.0 Baseline Thresholds (Key Changes from V100-1.0)

| Threshold | V100-1.0 | V200-1.0 | Change |
|-----------|----------|----------|--------|
| System Throughput | ≥700 ev/s | ≥900 ev/s | +28.6% |
| WAL Write Delay P99 | ≤5ms | ≤3ms | Tightened 40% |
| Index Write Delay P99 | ≤10ms | ≤7ms | Tightened 30% |
| Packet Loss Rate | ≤0.01% | ≤0.005% | Tightened 50% |
| Memory Usage | ≤85% | ≤80% | Tightened 5pp |
| Network Latency P99 | ≤5ms | ≤3ms | Tightened 40% |
| Query P99 (30d) | ≤500ms | ≤300ms | Tightened 40% |
| Render P99 | ≤200ms | ≤150ms | Tightened 25% |
| Index Bloat | ≤10% | ≤8% | Tightened 20% |

### 1.5 HERMES V87 New Audit Fields

| Field | Type | Description | Panels Consuming |
|-------|------|-------------|-----------------|
| `event_type` | VARCHAR(64) | Categorical event classification (e.g., `ALERT`, `ANOMALY`, `CAPACITY`, `TRACE`) | P-001, P-004, P-007 |
| `priority` | VARCHAR(8) | Severity level: `P1`, `P2`, `P3`, `P4`, `P5` | P-001, P-004, P-007 |
| `trace_id` | VARCHAR(128) | Distributed trace correlation ID (OpenTelemetry format) | P-006, P-007 |
| `batch_id` | VARCHAR(64) | Batch processing identifier for bulk operations | P-003, P-007 |
| `retry_count` | INTEGER | Number of retry attempts for failed operations (default: 0) | P-001, P-004, P-007 |

### 1.6 Success Criteria

Phase02 is considered successful when:

1. All 7 active panels (P-001 through P-004, P-006, P-007, P-008) pass integration testing and are deployed to the staging L2 dashboard.
2. All 8 new metrics are instrumented, queryable via the V200-1.0 API, and included in the baseline dashboard.
3. All 12 alert rules pass rule validation and are deployed to the alert engine.
4. All panels meet their individual performance budgets under 10× concurrent user load.
5. Cross-panel data flow is operational: an anomaly detected in P-001 can be correlated with traces in P-006 and alerts in P-004 within ≤5 seconds.
6. P-005 design document is reviewed and approved for Phase03 implementation.
---

## 2. Panel Development Overview

### 2.1 Panel Summary Table

| Panel ID | Panel Name | Priority | Status | Baseline Extension | Data Source | Est. Effort |
|----------|-----------|----------|--------|-------------------|-------------|-------------|
| V87-P-001 | AI 异常检测面板 (AI Anomaly Detection) | P1 | ACTIVE | New | HERMES L3 Anomaly Detection Service | 35 person-days |
| V87-P-002 | 跨服务依赖拓扑 (Cross-Service Dependency Topology) | P1 | ACTIVE | New | DSHB Service Registry + Call Chain Tracing | 30 person-days |
| V87-P-003 | 自动化容量规划 (Automated Capacity Planning) | P1 | ACTIVE | V86-P-022 Extended | HERMES Capacity Service + DSHB Metrics | 28 person-days |
| V87-P-004 | 告警关联分析 (Alert Correlation Analysis) | P1 | ACTIVE | New | HERMES Alert Service + Correlation Engine | 32 person-days |
| V87-P-005 | 混沌工程自动化 (Chaos Engineering Automation) | P2 | DEFERRED (Phase03) | New | N/A (Design Only) | 12 person-days (design) |
| V87-P-006 | 全链路追踪面板 (Full Trace Panel) | P1 | ACTIVE | New | DSHB V87 Tracing SDK (OpenTelemetry) | 33 person-days |
| V87-P-007 | 审计对账面板 (Audit Reconciliation) | P1 | ACTIVE | New | HERMES L3 Audit + DSHB Events + ClickHouse | 27 person-days |
| V87-P-008 | 基线漂移热力图 (Baseline Drift Heatmap) | P2 | ACTIVE | V86-P-016 Extended | HERMES Baseline Service + Metric Store | 18 person-days |

### 2.2 Priority Classification

```
┌─────────────────────────────────────────────────────────────────┐
│                     V87 PANEL PRIORITY MATRIX                     │
├──────────────┬──────────────────┬────────────────────────────────┤
│   P1 (P0)    │  Mission-Critical  │  P-001, P-002, P-003, P-004,  │
│              │  Blocks release     │  P-006, P-007                  │
│              │  6 panels            │  Must ship with V87-RC1        │
├──────────────┼──────────────────┼────────────────────────────────┤
│   P2 (P1)    │  Important         │  P-008 (ACTIVE)                 │
│              │  High value         │  P-005 (DEFERRED to Phase03)    │
│              │  2 panels            │                                 │
└──────────────┴──────────────────┴────────────────────────────────┘
```

### 2.3 Development Status Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  V87-RC1 PHASE02 DEVELOPMENT STATUS (as of report date)         │
├──────────────────────┬──────────┬──────────┬────────────────────┤
│  Panel               │  Spec    │  Impl    │  Integration        │
│                      │  Status  │  Status  │  Status             │
├──────────────────────┼──────────┼──────────┼────────────────────┤
│  V87-P-001 AI Anomaly│  ✅ Lock │  🔄 Actv │  ⏳ Pending         │
│  V87-P-002 Topology  │  ✅ Lock │  🔄 Actv │  ⏳ Pending         │
│  V87-P-003 Capacity  │  ✅ Lock │  🔄 Actv │  ⏳ Pending         │
│  V87-P-004 Correlat. │  ✅ Lock │  🔄 Actv │  ⏳ Pending         │
│  V87-P-005 Chaos     │  ✅ Lock │  N/A     │  N/A (Phase03)      │
│  V87-P-006 Trace     │  ✅ Lock │  🔄 Actv │  ⏳ Pending         │
│  V87-P-007 Audit     │  ✅ Lock │  🔄 Actv │  ⏳ Pending         │
│  V87-P-008 Drift     │  ✅ Lock │  🔄 Actv │  ⏳ Pending         │
├──────────────────────┼──────────┼──────────┼────────────────────┤
│  TOTAL (7 active)    │  7/7 ✅  │  7/7 🔄  │  0/7 ⏳            │
│  DEFERRED (1)        │  1/1 ✅  │  0/1 —   │  0/1 —             │
└──────────────────────┴──────────┴──────────┴────────────────────┘
Legend: ✅ Complete  🔄 Active  ⏳ Pending  — Not applicable
```

### 2.4 Cross-Panel Dependency Map

```
                        ┌──────────────┐
                        │  HERMES L3   │
                        │  Core Engine │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼───────┐ ┌─────▼──────┐ ┌──────▼──────┐
     │ P-001 Anomaly  │ │ P-004 Alert│ │ P-007 Audit │
     │ Detection      │ │ Correlation│ │ Reconciliation│
     └────────┬───────┘ └─────┬──────┘ └──────┬──────┘
              │                │                │
              └────────┬───────┘                │
                       │                        │
                  ┌────▼─────┐            ┌─────▼─────┐
                  │ ClickHouse│◄──────────│ DSHB V87  │
                  │ (Logs)   │            │ Tracing   │
                  └──────────┘            └─────┬─────┘
                                                │
                                         ┌─────▼─────┐
                                         │ P-006 Full│
                                         │ Trace     │
                                         └───────────┘

     ┌──────────────┐         ┌──────────────┐
     │ P-002 Topology│◄───────►│ P-006 Trace  │
     │ (Registry)   │  calls  │ (Spans)      │
     └──────┬───────┘         └──────────────┘
            │
     ┌──────▼───────┐
     │ P-003 Capacity│
     │ Planning     │
     └──────────────┘

     ┌──────────────┐
     │ P-008 Drift  │
     │ Heatmap      │─── V86-P-016 extension
     └──────────────┘

     ┌──────────────┐
     │ P-005 Chaos  │
     │ (Design Only)│─── Deferred to Phase03
     └──────────────┘
```

### 2.5 Shared Infrastructure Components

| Component | Consumers | Description |
|-----------|----------|-------------|
| `@dshb/event-bus` | All 7 active panels | WebSocket + MQTT hybrid event bus for real-time data streaming |
| `@dshb/panel-core` | All 7 active panels | Shared panel framework: lifecycle, data fetching, caching, rendering |
| `@dshb/viz-kit` | P-001, P-002, P-003, P-006, P-008 | Chart library (ECharts 5.x, D3 v7, Cytoscape.js) |
| `@dshb/alert-engine` | P-001, P-004, P-007 | Alert rule evaluation + suppression + notification |
| `@dshb/model-api` | P-001, P-003 | ML model inference client (Prophet, LSTM, Isolation Forest) |
| `@dshb/otel-client` | P-006, P-002 | OpenTelemetry trace span consumer + aggregation |
| `@dshb/audit-client` | P-007, P-001, P-004 | HERMES audit log reader with 5 new V87 fields |
| `@dshb/topology-api` | P-002, P-006 | Service registry + call graph API client |

---

## 3. V87-P-001: AI Anomaly Detection Panel

### 3.1 Panel Metadata

| Attribute | Value |
|-----------|-------|
| **Panel ID** | V87-P-001 |
| **Panel Name** | AI 异常检测面板 / AI Anomaly Detection Panel |
| **Priority** | P1 (Mission-Critical) |
| **Work Order** | DSHE_V87_RC1_L2_PHASE02_V87_DASHBOARD_DEVELOP_AND_ALERT_RULE_ITERATE |
| **Estimated Effort** | 35 person-days |
| **Owner** | ML Platform Team |
| **Data Source** | HERMES L3 Anomaly Detection Service (gRPC + REST) |
| **ML Models** | Prophet (time series baseline), Isolation Forest (unsupervised anomaly), LSTM (sequential anomaly) |
| **Integration Status** | Phase02 ACTIVE |

### 3.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        V87-P-001 ARCHITECTURE                            │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        BROWSER (Frontend)                        │    │
│  │                                                                   │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │    │
│  │  │ Anomaly    │  │ Anomaly    │  │ Model      │  │ Cold     │  │    │
│  │  │ Overview   │  │ Timeline   │  │ Performance│  │ Start    │  │    │
│  │  │ Region     │  │ Region     │  │ Region     │  │ Status   │  │    │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └─────┬────┘  │    │
│  │         │               │               │               │        │    │
│  │  ┌──────▼───────────────▼───────────────▼───────────────▼────┐   │    │
│  │  │              Panel React Component Layer                    │   │    │
│  │  │  (React 18 + Grafana Panel SDK + TypeScript)               │   │    │
│  │  └──────────────────────────────┬────────────────────────────┘   │    │
│  └─────────────────────────────────┬─────────────────────────────────┘    │
│                                    │                                      │
│                          ┌─────────▼──────────┐                           │
│                          │   Panel Core API    │                           │
│                          │   (@dshb/panel-core)│                           │
│                          └─────────┬──────────┘                           │
│                                    │                                      │
│  ┌─────────────────────────────────┼─────────────────────────────────┐   │
│  │                     API Gateway (Kong / NGINX)                      │   │
│  └─────────────────────────────────┬─────────────────────────────────┘   │
│                                    │                                      │
│  ┌─────────────────────────────────┼─────────────────────────────────┐   │
│  │                      HERMES L3 Services                             │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Anomaly      │  │ Anomaly      │  │ Feedback     │              │   │
│  │  │ Detection    │  │ Event Store  │  │ Service      │              │   │
│  │  │ (gRPC)       │  │ (InfluxDB)   │  │ (REST)       │              │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │   │
│  │         │                  │                  │                      │   │
│  │  ┌──────▼──────────────────▼──────────────────▼──────────────┐     │   │
│  │  │              ML Model Inference Layer                       │     │   │
│  │  │  ┌─────────┐  ┌──────────────┐  ┌─────────┐               │     │   │
│  │  │  │ Prophet │  │ Isolation    │  │  LSTM   │               │     │   │
│  │  │  │ Engine  │  │ Forest       │  │ Network │               │     │   │
│  │  │  │ (Time   │  │ (Unsupervised│  │ (Sequen-│               │     │   │
│  │  │  │ Series) │  │  Anomaly)    │  │  tial)  │               │     │   │
│  │  │  └─────────┘  └──────────────┘  └─────────┘               │     │   │
│  │  └────────────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Data Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Metric  │────►│  Metric  │────►│   ML     │────►│ Anomaly  │
│  Ingress │     │  Buffer  │     │  Pipeline│     │  Store   │
│ (WAL)    │     │ (Influx) │     │ (gRPC)   │     │ (Influx) │
└──────────┘     └──────────┘     └────┬─────┘     └────┬─────┘
                                       │                  │
                          ┌────────────▼──────────────────▼────┐
                          │         Event Bus (WebSocket)       │
                          └────────────────┬───────────────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │   P-001 Frontend       │
                              │   (React + Grafana)    │
                              └────────────────────────┘
```

### 3.4 AI Model Integration

#### 3.4.1 Hybrid Model Architecture

The panel uses a three-model ensemble approach for comprehensive anomaly detection:

| Model | Role | Algorithm | Input | Output |
|-------|------|-----------|-------|--------|
| **Prophet** | Baseline learning | Seasonal decomposition + trend estimation | 30-day historical metric series | Expected value + confidence interval |
| **Isolation Forest** | Point anomaly detection | Unsupervised ensemble of random isolation trees | Multi-metric feature vectors (CPU, mem, QPS, error rate) | Anomaly score [0, 1] |
| **LSTM** | Sequential anomaly detection | Long Short-Term Memory neural network | 10-minute sliding window metric sequences | Anomaly probability + direction (rising/falling) |

#### 3.4.2 Model Ensemble Scoring

```python
# Pseudocode: Hybrid Anomaly Scoring Algorithm
def hybrid_anomaly_score(
    metrics: Dict[str, List[float]],
    prophet_baseline: Dict[str, Any],
    isolation_forest: IsolationForest,
    lstm_model: LSTM,
    weights: Dict[str, float] = {"prophet": 0.30, "iforest": 0.35, "lstm": 0.35}
) -> AnomalyResult:
    
    scores = {}
    
    # 1. Prophet: Compare observed vs. expected with confidence interval
    for metric_name, series in metrics.items():
        expected = prophet_baseline[metric_name]
        deviation = (series[-1] - expected["value"]) / expected["std"]
        scores[f"prophet_{metric_name}"] = min(1.0, abs(deviation) / 3.0)
    
    # 2. Isolation Forest: Multi-metric point anomaly
    feature_vector = [
        metrics["cpu_usage"][-1],
        metrics["memory_usage"][-1],
        metrics["qps"][-1],
        metrics["error_rate"][-1],
        metrics["network_latency_p99"][-1]
    ]
    iforest_score = 1.0 - isolation_forest.score_samples([feature_vector])[0]
    scores["isolation_forest"] = max(0.0, min(1.0, iforest_score))
    
    # 3. LSTM: Sequential anomaly with direction
    sequence = build_sliding_window(metrics, window_size=10)
    lstm_pred = lstm_model.predict([sequence])
    scores["lstm_anomaly_prob"] = float(lstm_pred[0][0])
    scores["lstm_direction"] = "rising" if lstm_pred[0][1] > 0 else "falling"
    
    # Weighted ensemble score
    ensemble_score = (
        weights["prophet"] * np.mean([s for k, s in scores.items() if k.startswith("prophet_")])
        + weights["iforest"] * scores["isolation_forest"]
        + weights["lstm"] * scores["lstm_anomaly_prob"]
    )
    
    # Anomaly classification
    if ensemble_score >= 0.85:
        severity = "P1_CRITICAL"
    elif ensemble_score >= 0.70:
        severity = "P2_HIGH"
    elif ensemble_score >= 0.55:
        severity = "P3_MEDIUM"
    else:
        severity = "NORMAL"
    
    return AnomalyResult(
        score=ensemble_score,
        severity=severity,
        component_scores=scores,
        direction=scores.get("lstm_direction"),
        detected_at=datetime.now()
    )
```

#### 3.4.3 Model Training Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Historical │───►│  Feature    │───►│  Model      │───►│  Model      │
│  Data (30d) │    │  Engineer-  │    │  Training   │    │  Registry   │
│  (InfluxDB) │    │  ing        │    │  (GPU Pool) │    │  (S3 + DB)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                   │                   │
     │              ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
     │              │ Imputa- │        │ Pro-    │        │ Model   │
     │              │ tion    │        │ phet    │        │ Version │
     │              │ Normal- │        │ LSTM    │        │ Tracking│
     │              │ ization │        │ IForest │        │ (DB)    │
     │              │ Scaling │        │ Train   │        │         │
     │              └─────────┘        └─────────┘        └─────────┘
     │
     ▼
  ┌─────────┐
  │ Auto-   │  Retraining triggered every 24h or when
  │ Retrigger│  drift exceeds 15% (MMD test)
  └─────────┘
```

### 3.5 UI Component Specification

#### 3.5.1 Region Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    V87-P-001 LAYOUT (12-column grid)                     │
│                                                                          │
│  ┌─────────────────────────────────────┐  ┌──────────────────────────┐  │
│  │  REGION 1: Anomaly Overview          │  │  REGION 4: Model Perf.  │  │
│  │  (8 cols × 2 rows)                   │  │  (4 cols × 2 rows)      │  │
│  │                                     │  │                          │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐        │  │  ┌────────────────────┐  │  │
│  │  │Total │ │Active│ │Avg   │        │  │  │ Prophet: F1=0.92   │  │  │
│  │  │ 47   │ │ 12   │ │Score │        │  │  │ IForest: AUC=0.89  │  │  │
│  │  │Today │ │Now   │ │0.68  │        │  │  │ LSTM: Acc=0.87    │  │  │
│  │  └──────┘ └──────┘ └──────┘        │  │  │ Ensemble: F1=0.94  │  │  │
│  │                                     │  │  └────────────────────┘  │  │
│  │  ┌──────────────────────────────┐  │  │                          │  │
│  │  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐  │  │  │  ┌────────────────────┐  │  │
│  │  │  │P1 │ │P2 │ │P3 │ │NR │  │  │  │  │ Model Versions:    │  │  │
│  │  │  │ 3 │ │ 7 │ │ 8 │ │29 │  │  │  │  │ v200.1.0 (active)  │  │  │
│  │  │  └───┘ └───┘ └───┘ └───┘  │  │  │  │ v200.0.9 (prev)    │  │  │
│  │  │   Sev. Dist. by Priority    │  │  │  └────────────────────┘  │  │
│  │  └──────────────────────────────┘  │  │                          │  │
│  └─────────────────────────────────────┘  └──────────────────────────┘  │
│                                                                          │
│  ┌─────────────────────────────────────┐  ┌──────────────────────────┐  │
│  │  REGION 2: Anomaly Time Series       │  │  REGION 5: Cold Start    │  │
│  │  (8 cols × 3 rows)                   │  │  Status (4 cols × 2)    │  │
│  │                                     │  │                          │  │
│  │  ┌─────────────────────────────────┐│  │  ┌────────────────────┐  │  │
│  │  │  📈 24h Anomaly Score Timeline  ││  │  │ Prophet: READY     │  │  │
│  │  │  ╱╲    ╱╲  ╱╲                 ││  │  │ IForest: READY     │  │  │
│  │  │ ╱  ╲  ╱  ╲╱  ╲    ╱╲          ││  │  │ LSTM: WARMING UP   │  │  │
│  │  │    ╲╱  ╲      ╲  ╱  ╲╱         ││  │  │ Cold start: 0/7    │  │  │
│  │  │  ────[Threshold=0.70]────────   ││  │  │ days remaining     │  │  │
│  │  │  Anomaly zones highlighted red   ││  │  └────────────────────┘  │  │
│  │  └─────────────────────────────────┘│  │                          │  │
│  │                                     │  │  ┌────────────────────┐  │  │
│  │  ┌─────────────────────────────────┐│  │  │ Data sufficiency:  │  │  │
│  │  │  📊 Per-Metric Anomaly Heatmap  ││  │  │ CPU:  ✓ (18d)     │  │  │
│  │  │  CPU  [░░░░░░░░░░] 0.02        ││  │  │ Mem:  ✓ (18d)     │  │  │
│  │  │  MEM  [████░░░░░░] 0.41        ││  │  │ QPS:  △ (12d)     │  │  │
│  │  │  QPS  [██████░░░░] 0.67  ◄──   ││  │  │ Err:  ✗ (3d)      │  │  │
│  │  │  ERR  [████████░░] 0.89  ◄──   ││  │  └────────────────────┘  │  │
│  │  └─────────────────────────────────┘│  └──────────────────────────┘  │
│  └─────────────────────────────────────┘                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  REGION 3: Anomaly Event List (12 cols × 3 rows)                    │ │
│  │                                                                     │ │
│  │  ┌─────┬──────────┬──────────┬─────┬──────────┬──────┬──────────┐ │ │
│  │  │ Time│ Metric   │ Score    │ Sev │ Direction│ Status│ Actions  │ │ │
│  │  ├─────┼──────────┼──────────┼─────┼──────────┼──────┼──────────┤ │ │
│  │  │14:32│ err_rate │ 0.92     │ P1  │ Rising   │OPEN  │[Ack][Det]│ │ │
│  │  │14:28│ mem_usage│ 0.85     │ P2  │ Rising   │ACK   │[Ack][Det]│ │ │
│  │  │14:15│ cpu_usage│ 0.78     │ P2  │ Rising   │RESOLV│[Ack][Det]│ │ │
│  │  │14:01│ qps      │ 0.71     │ P3  │ Falling  │RESOLV│[Ack][Det]│ │ │
│  │  │13:45│ net_lat  │ 0.58     │ P3  │ Rising   │CLOSED│[Ack][Det]│ │ │
│  │  └─────┴──────────┴──────────┴─────┴──────────┴──────┴──────────┘ │ │
│  │  [Filter: All Services ▼] [Time Range: 1h ▼] [Sort: Score ▼]     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.5.2 Interactive Features

| Feature | Description | Trigger |
|---------|-------------|---------|
| Anomaly Zoom | Click on anomaly zone in timeline → drill into per-second granularity | Mouse click on timeline anomaly marker |
| Cross-Metric Correlation | Hover on anomaly point → tooltip shows correlated metric spikes | Mouse hover on timeline |
| Event Detail | Click on event row → expand with full context, model scores, suggested actions | Row click |
| Acknowledge | Mark anomaly as acknowledged, suppress repeat alerts for 30 min | [Ack] button |
| Drill-down | Navigate to P-006 trace view via trace_id in anomaly event | [Det] button |
| Feedback Loop | Rate anomaly as True Positive / False Positive → feeds into model retraining | Feedback dialog |
| Filter by Service | Filter all regions by service name | Dropdown filter |
| Time Range | Adjust time window: 1h, 6h, 24h, 7d, 30d | Time range selector |

### 3.6 API Contract

#### 3.6.1 Anomaly Detection API

```json
// GET /api/v87/anomaly/detect
// Headers: X-Panel-ID: V87-P-001, X-Baseline-Version: V200-1.0
{
  "request": {
    "service_id": "string",        // Service identifier (e.g., "dshb-gateway")
    "time_range": {
      "from": "2025-01-15T14:00:00Z",
      "to": "2025-01-15T15:00:00Z"
    },
    "metrics": ["cpu_usage", "memory_usage", "qps", "error_rate", "network_latency_p99"],
    "model_config": {
      "ensemble_weights": {"prophet": 0.30, "iforest": 0.35, "lstm": 0.35},
      "thresholds": {
        "critical": 0.85,
        "high": 0.70,
        "medium": 0.55
      }
    }
  },
  "response": {
    "status": "OK",
    "anomalies": [
      {
        "anomaly_id": "anom-20250115-143200-001",
        "detected_at": "2025-01-15T14:32:00.000Z",
        "score": 0.92,
        "severity": "P1_CRITICAL",
        "direction": "rising",
        "metrics_affected": ["error_rate", "network_latency_p99"],
        "component_scores": {
          "prophet_error_rate": 0.88,
          "prophet_network_latency_p99": 0.91,
          "isolation_forest": 0.87,
          "lstm_anomaly_prob": 0.94
        },
        "cause_attribution": {
          "primary_cause": "dshb-gateway:connection_pool_exhaustion",
          "confidence": 0.82,
          "correlated_events": ["alert-20250115-143100-001", "alert-20250115-143130-001"]
        },
        "suggested_actions": [
          "Increase connection pool size for dshb-gateway",
          "Check upstream service dshb-auth response times"
        ],
        "feedback": {
          "is_true_positive": null,
          "reported_by": null,
          "reported_at": null
        }
      }
    ],
    "summary": {
      "total_anomalies": 3,
      "p1_count": 1,
      "p2_count": 1,
      "p3_count": 1,
      "avg_score": 0.85,
      "model_version": "v200.1.0"
    }
  }
}
```

#### 3.6.2 Anomaly Event API

```json
// GET /api/v87/anomaly/events
// Query params: service_id, severity, status, time_from, time_to, page, page_size

// Response
{
  "status": "OK",
  "events": [
    {
      "event_id": "anom-20250115-143200-001",
      "event_type": "ANOMALY",         // HERMES V87 field
      "priority": "P1",                 // HERMES V87 field
      "trace_id": "tr-abc123def456",   // HERMES V87 field
      "batch_id": "batch-001",         // HERMES V87 field
      "retry_count": 0,                // HERMES V87 field
      "timestamp": "2025-01-15T14:32:00.000Z",
      "service_id": "dshb-gateway",
      "metric": "error_rate",
      "score": 0.92,
      "severity": "P1_CRITICAL",
      "status": "OPEN",
      "direction": "rising",
      "current_value": 0.035,
      "baseline_value": 0.002,
      "deviation_pct": 1650.0
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 47,
    "total_pages": 3
  }
}
```

#### 3.6.3 Model Performance API

```json
// GET /api/v87/anomaly/model-performance
{
  "status": "OK",
  "models": [
    {
      "model_name": "prophet_baseline",
      "version": "v200.1.0",
      "metrics": {
        "precision": 0.91,
        "recall": 0.89,
        "f1_score": 0.90,
        "auc_roc": 0.93
      },
      "last_trained_at": "2025-01-15T06:00:00Z",
      "training_data_days": 30,
      "status": "READY"
    },
    {
      "model_name": "isolation_forest",
      "version": "v200.1.0",
      "metrics": {
        "precision": 0.87,
        "recall": 0.85,
        "f1_score": 0.86,
        "auc_roc": 0.89
      },
      "last_trained_at": "2025-01-15T06:00:00Z",
      "training_data_days": 30,
      "status": "READY"
    },
    {
      "model_name": "lstm_sequential",
      "version": "v200.1.0",
      "metrics": {
        "precision": 0.86,
        "recall": 0.84,
        "f1_score": 0.85,
        "accuracy": 0.87
      },
      "last_trained_at": "2025-01-15T06:00:00Z",
      "training_data_days": 30,
      "status": "READY"
    },
    {
      "model_name": "ensemble",
      "version": "v200.1.0",
      "metrics": {
        "precision": 0.93,
        "recall": 0.91,
        "f1_score": 0.92,
        "auc_roc": 0.95
      },
      "last_trained_at": "2025-01-15T06:00:00Z",
      "training_data_days": 30,
      "status": "READY"
    }
  ],
  "cold_start_status": {
    "metrics_ready": 7,
    "metrics_total": 7,
    "cold_start_complete": true,
    "days_remaining": 0
  }
}
```

#### 3.6.4 Feedback API

```json
// POST /api/v87/anomaly/feedback
{
  "request": {
    "anomaly_id": "anom-20250115-143200-001",
    "feedback_type": "TRUE_POSITIVE",  // TRUE_POSITIVE | FALSE_POSITIVE | UNCERTAIN
    "comment": "Confirmed: connection pool exhaustion caused cascade failure",
    "reported_by": "oncall-engineer@company.com"
  },
  "response": {
    "status": "OK",
    "message": "Feedback recorded. Model will incorporate this data in next retraining cycle.",
    "next_retraining_eta": "2025-01-16T06:00:00Z"
  }
}
```

### 3.7 Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Panel load time (P99) | ≤2s | Lighthouse + custom instrumentation |
| Anomaly marking latency (P99) | ≤3s | End-to-end from metric ingest to UI marker |
| API response time (P99) | ≤500ms | API gateway metrics |
| Model inference latency (P99) | ≤200ms | ML inference service metrics |
| Concurrent user support | 50 users | Load test with k6 |
| Data freshness | ≤10s | Polling interval for anomaly updates |

### 3.8 Test Plan

| Test Category | Test Cases | Coverage Target |
|--------------|------------|-----------------|
| Unit Tests | Model scoring, ensemble weighting, threshold classification | ≥90% lines |
| Integration Tests | API contracts, data flow, model service connectivity | 20+ scenarios |
| Performance Tests | Load (50 users), stress (200 users), spike (100 users/sec) | 3 test runs |
| Visual Regression | All 5 regions at 4 breakpoints (mobile, tablet, laptop, desktop) | Chromatic/ Percy |
| Model Accuracy | Ensemble F1 ≥0.90, AUC ≥0.93 on validation set | CI gate |
---

## 4. V87-P-002: Cross-Service Dependency Topology Panel

### 4.1 Panel Metadata

| Attribute | Value |
|-----------|-------|
| **Panel ID** | V87-P-002 |
| **Panel Name** | 跨服务依赖拓扑 / Cross-Service Dependency Topology |
| **Priority** | P1 (Mission-Critical) |
| **Estimated Effort** | 30 person-days |
| **Owner** | Observability Platform Team |
| **Data Source** | DSHB Service Registry + Call Chain Tracing (DSHB V87 Tracing SDK) |
| **Rendering Engine** | Cytoscape.js (graph) + D3.js (visualization layers) |
| **Integration Status** | Phase02 ACTIVE |

### 4.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      V87-P-002 ARCHITECTURE                                  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     BROWSER (Frontend)                                 │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │              Topology Canvas (SVG + WebGL fallback)              │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │                                                          │  │  │  │
│  │  │  │         ┌───┐      ┌───┐      ┌───┐                     │  │  │  │
│  │  │  │         │API│─────►│AUTH│─────►│DB │                     │  │  │  │
│  │  │  │         │ GW │      │ Svc │     │   │                     │  │  │  │
│  │  │  │         └───┘      └───┘      └───┘                     │  │  │  │
│  │  │  │          │              │              │                 │  │  │  │
│  │  │  │          ▼              ▼              ▼                 │  │  │  │
│  │  │  │         ┌───┐      ┌───┐       ┌─────┐                 │  │  │  │
│  │  │  │         │QPS│      │P99 │      │Err% │                 │  │  │  │
│  │  │  │         │10k│      │45ms│      │0.02%│                 │  │  │  │
│  │  │  │         └───┘      └───┘      └─────┘                 │  │  │  │
│  │  │  │                                                          │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │
│  │  │                                                                   │  │
│  │  │  Layouts: Circular | Force-directed | Hierarchical | Grid       │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ Trace        │  │ Service      │  │ Fault        │                │  │
│  │  │ Waterfall    │  │ Health       │  │ Propagation  │                │  │
│  │  │ Drawer       │  │ Panel        │  │ Overlay      │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│                          ┌─────────────┐                                    │
│                          │ Event Bus   │◄── WebSocket (60s incremental)     │
│                          └──────┬──────┘                                    │
│                                 │                                            │
│  ┌──────────────────────────────┼────────────────────────────────────────┐  │
│  │                  API Layer                                      │  │
│  │                                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Registry API │  │ Tracing API  │  │ Health API   │          │  │
│  │  │ (DSHB)       │  │ (OTel)       │  │ (DSHB)       │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Topology Rendering Engine

#### 4.3.1 Rendering Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Registry│───►│  Topology│───►│  Layout  │───►│  Render  │───►│   UI     │
│  Data    │    │  Builder │    │  Engine  │    │  Canvas  │    │  Layer   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     │              ┌─▼─┐          ┌─▼──┐         ┌──▼───┐       ┌──▼────┐
     │              │ N │          │ Cy │         │SVG   │       │Zoom   │
     │              │ Ed│          │ Fo │         │WebGL │       │Filter │
     │              │ Ge│          │ Hi │         │      │       │Drill  │
     │              └───┘          └───┘         └──────┘       └───────┘
     │
     ▼
  ┌─────────┐
  │ DSHB    │  Service registry with health status, QPS, P99, error rate
  │ Registry│
  └─────────┘
```

#### 4.3.2 Layout Algorithms

| Layout | Algorithm | Best For | Complexity | Max Nodes |
|--------|-----------|----------|------------|-----------|
| **Circular** | Circle packing | Small topologies, overview | O(n) | ≤50 |
| **Force-Directed** | Fruchterman-Reingold + Barnes-Hut | General purpose, discovering clusters | O(n log n) | ≤500 |
| **Hierarchical** | Sugiyama layering | Call hierarchy, request flow | O(n + e) | ≤300 |
| **Grid** | Regular grid packing | Static overview, comparison | O(n) | ≤500 |
| **Radial** | Radial force layout | Hub-and-spoke patterns | O(n log n) | ≤200 |

#### 4.3.3 Performance Optimization Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│  500 NODES ≤2s RENDER — PERFORMANCE STRATEGY                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Progressive Rendering                                        │
│     ├── Phase 1: Node skeleton (circles) — 200ms                │
│     ├── Phase 2: Edge rendering — 400ms                          │
│     ├── Phase 3: Labels + metrics — 600ms                       │
│     └── Phase 4: Health colors + animations — 800ms             │
│                                                                   │
│  2. WebGL Fallback (Cytoscape.js ext-canvas)                     │
│     ├── Triggered when nodes > 100                                │
│     ├── Canvas2D for ≤100 nodes                                  │
│     └── WebGL for >100 nodes (2x-5x speed improvement)          │
│                                                                   │
│  3. Viewport Culling                                              │
│     ├── Only render nodes within visible viewport + 20% margin   │
│     ├── Off-screen nodes rendered as simplified shapes           │
│     └── Zoom level adaptive detail (LOD)                         │
│                                                                   │
│  4. Incremental Update (60s cycle)                               │
│     ├── Diff-based update: only changed nodes/edges re-rendered  │
│     ├── WebSocket push for real-time changes                     │
│     └── Background refresh: 60s poll as fallback                 │
│                                                                   │
│  5. Pre-computed Layout                                           │
│     ├── Server-side layout computation for initial render        │
│     ├── Client-side only for interactive re-layout               │
│     └── Layout cache key: topology_hash + layout_algo            │
│                                                                   │
│  6. Batched Updates                                               │
│     ├── requestAnimationFrame throttling                         │
│     ├── Coalesce multiple property changes into single frame     │
│     └── Defer non-critical updates (labels, tooltips)            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Node/Edge Data Model

#### 4.4.1 Node Schema

```typescript
// @dshb/topology-api/src/nodes.d.ts
interface ServiceNode {
  // Identity
  id: string;                    // Service ID (e.g., "dshb-gateway-001")
  name: string;                  // Display name
  namespace: string;             // Kubernetes namespace
  
  // Health
  health: 'healthy' | 'degraded' | 'critical' | 'unknown';
  health_color: string;          // CSS color value
  uptime_pct: number;            // Uptime percentage (last 24h)
  
  // Metrics (real-time)
  qps: number;                   // Queries per second
  p99_latency_ms: number;        // P99 latency in milliseconds
  error_rate_pct: number;        // Error rate percentage
  cpu_usage_pct: number;         // CPU utilization
  memory_usage_pct: number;      // Memory utilization
  
  // Dependencies
  incoming_edges: string[];      // IDs of services that call this
  outgoing_edges: string[];      // IDs of services this calls
  
  // Tracing
  trace_count_24h: number;       // Total traces in last 24h
  error_trace_pct: number;       // Percentage of traces with errors
  
  // Metadata
  version: string;               // Service version
  deploy_time: string;           // ISO timestamp of last deploy
  pod_count: number;             // Number of running pods
  region: string;                // Deployment region
  
  // HERMES V87 audit fields (when available)
  event_type?: string;
  priority?: string;
  batch_id?: string;
  retry_count?: number;
}

// Node visual properties
interface NodeVisualProps {
  size: number;                  // Radius (scaled by QPS: min 12px, max 48px)
  color: string;                 // Health-based fill color
  border_color: string;          // Border color
  border_width: number;          // Border width (health-based)
  shape: 'circle' | 'diamond' | 'hexagon'; // Shape by service type
  label_position: 'outside' | 'inside' | 'below';
  show_metrics: boolean;         // Show QPS/P99/Err% labels
  animation: 'pulse' | 'none';   // Pulse animation for critical services
}
```

#### 4.4.2 Edge Schema

```typescript
// @dshb/topology-api/src/edges.d.ts
interface CallEdge {
  // Identity
  id: string;                    // Edge ID (source → target hash)
  source: string;                // Source service node ID
  target: string;                // Target service node ID
  
  // Protocol
  protocol: 'HTTP' | 'gRPC' | 'Redis' | 'PostgreSQL' | 'Kafka' | 'Custom';
  endpoint: string;              // Target endpoint (e.g., "/api/v87/services")
  
  // Metrics
  qps: number;                   // Call rate
  p99_latency_ms: number;        // P99 latency
  p50_latency_ms: number;        // P50 latency
  error_rate_pct: number;        // Error rate
  success_rate_pct: number;      // Success rate
  
  // Health
  health: 'healthy' | 'degraded' | 'critical';
  
  // Visualization
  color: string;                 // Color by error rate threshold
  width: number;                 // Width by QPS (1px to 8px)
  dashed: boolean;               // Dashed for async calls (Kafka)
  arrow_type: 'triangle' | 'circle' | 'none';
  
  // Fault propagation
  is_fault_path: boolean;        // True if on active fault propagation path
  fault_impact_score: number;    // 0-1 score of fault impact
}
```

### 4.5 Service Registry Integration

#### 4.5.1 DSHB Registry API

```json
// GET /api/v87/registry/services
{
  "status": "OK",
  "services": [
    {
      "id": "dshb-gateway-001",
      "name": "DSHB API Gateway",
      "namespace": "production",
      "health": "healthy",
      "uptime_pct": 99.97,
      "qps": 12450,
      "p99_latency_ms": 42,
      "error_rate_pct": 0.008,
      "cpu_usage_pct": 34.2,
      "memory_usage_pct": 62.1,
      "version": "v87.0.1",
      "deploy_time": "2025-01-14T10:00:00Z",
      "pod_count": 6,
      "region": "cn-north-1",
      "dependencies": [
        "dshb-auth-001",
        "dshb-user-001",
        "dshb-order-001",
        "dshb-inventory-001"
      ]
    }
  ],
  "topology": {
    "node_count": 47,
    "edge_count": 128,
    "generated_at": "2025-01-15T14:00:00Z",
    "topology_hash": "a3f2b1c9d8e7f6"
  }
}
```

#### 4.5.2 Topology Discovery Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Service      │───►│ Registry     │───►│ Topology     │───►│ Event Bus    │
│ Auto-Reg.    │    │ Polling      │    │ Builder      │    │ (WebSocket)  │
│ (DSHB SDK)   │    │ (30s cycle)  │    │ (Diff + Merge)│    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │                   │
       │  ┌───────────────▼──────────────┐    │                   │
       │  │  Call Chain Tracing         │    │                   │
       │  │  (DSHB V87 SDK → OTel)      │    │                   │
       │  └───────────────┬──────────────┘    │                   │
       │                  │                   │                   │
       │  ┌───────────────▼──────────────┐    │                   │
       │  │  Edge Metrics Aggregation    │    │                   │
       │  │  (10s window, P99 calc)      │    │                   │
       │  └───────────────┬──────────────┘    │                   │
       │                  │                   │                   │
       │                  └───────────────────┘                   │
       │                                     │                   │
       │  ┌──────────────────────────────────▼────────────────┐   │
       │  │           Topology Change Detection               │   │
       │  │  ┌─────────────────────────────────────────────┐  │   │
       │  │  │ if topology_hash changed:                    │  │   │
       │  │  │   1. Compute diff (new/removed nodes/edges) │  │   │
       │  │  │   2. Push delta to WebSocket clients         │  │   │
       │  │  │   3. Full topology refresh if delta > 30%   │  │   │
       │  │  └─────────────────────────────────────────────┘  │   │
       │  └────────────────────────────────────────────────────┘   │
       └────────────────────────────────────────────────────────────┘
```

### 4.6 Fault Propagation Analysis

#### 4.6.1 Fault Propagation Algorithm

```python
# Pseudocode: Fault propagation scoring
def compute_fault_propagation(topology: Topology, root_cause: str) -> Dict[str, float]:
    """
    BFS from root cause node, computing impact score for each dependent service.
    Score decays with each hop based on call volume and error rate.
    """
    impact_scores = {}
    queue = deque([(root_cause, 1.0)])  # (node_id, current_score)
    visited = set()
    
    while queue:
        node_id, score = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        impact_scores[node_id] = score
        
        for edge in topology.get_outgoing_edges(node_id):
            target = edge.target
            if target not in visited:
                # Decay factor: QPS weight (higher QPS = more impact)
                qps_weight = min(1.0, edge.qps / 10000.0)
                # Error amplification: if edge already has errors, fault propagates faster
                error_factor = 1.0 + (edge.error_rate_pct / 100.0) * 2.0
                # Hop decay: reduce impact per hop (exponential decay)
                hop_decay = 0.85
                new_score = score * qps_weight * error_factor * hop_decay
                
                if new_score >= 0.10:  # Minimum threshold for reporting
                    queue.append((target, new_score))
    
    return impact_scores
```

#### 4.6.2 Fault Propagation Visualization

```
Example fault propagation scenario:

     ┌─────────────────────────────────────────────────────┐
     │                                                     │
     │    ┌───┐                                           │
     │    │DB │  ● Critical (root cause)                   │
     │    └─┬─┘  Impact Score: 1.00                       │
     │      │ (QPS=5000, Err=5.0%)                        │
     │      ▼                                              │
     │    ┌───┐  Impact Score: 0.85                       │
     │    │SVC│  ● Critical                               │
     │    │B   │  Error rate: 3.2%                        │
     │    └─┬─┘                                           │
     │      │ (QPS=3000, Err=2.1%)                        │
     │      ▼                                              │
     │    ┌───┐  Impact Score: 0.42                       │
     │    │SVC│  ● Degraded                               │
     │    │A   │  Error rate: 0.8%                        │
     │    └─┬─┘                                           │
     │      │ (QPS=1000, Err=0.3%)                        │
     │      ▼                                              │
     │    ┌───┐  Impact Score: 0.15                       │
     │    │SVC│  ● Minor                                   │
     │    │C   │  Error rate: 0.05%                       │
     │    └───┘                                           │
     │                                                     │
     │  Legend: Red=Critical(>0.5) Orange=Degraded        │
     │         Yellow=Minor(>0.1) Gray=Normal             │
     └─────────────────────────────────────────────────────┘
```

### 4.7 UI Component Specification

#### 4.7.1 Topology View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  V87-P-002: Cross-Service Dependency Topology                       │   │
│  │  [Layout: Force-Directed ▼] [Refresh: Auto(60s) ▼] [Export: PNG/SVG]│   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │                          ┌───┐                                      │   │
│  │                    ┌────►│DB │◄────┐                                │   │
│  │                    │     └───┘     │                                │   │
│  │                    │               │                                │   │
│  │  ┌───┐       ┌────▼──┐       ┌────▼──┐                            │   │
│  │  │API│──────►│ Auth  │──────►│ User  │                            │   │
│  │  │ GW │  10k│  Svc  │  3k   │  Svc  │                            │   │
│  │  │    │  45ms│       │  12ms│       │                            │   │
│  │  └─┬──┘  0.1%│  0.05%│  0.02%│ 0.01%│                            │   │
│  │    │         └───┬───┘       └───────┘                            │   │
│  │    │             │                                                  │   │
│  │    │             ▼                                                  │   │
│  │    │         ┌──────────┐                                           │   │
│  │    │         │Order Svc │                                           │   │
│  │    │         │  2k QPS  │                                           │   │
│  │    │         │  28ms P99│                                           │   │
│  │    │         │  0.03% Err│                                          │   │
│  │    │         └──────────┘                                           │   │
│  │    │                                                                 │   │
│  │    ▼                                                                 │   │
│  │  ┌───┐                                                              │   │
│  │  │MQ │◄─────────────────────────────────────────────────────────── │   │
│  │  └───┘                                                              │   │
│  │                                                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Trace        │  │ Service Info │  │ Fault        │  │ Metrics      │   │
│  │ Waterfall    │  │ (selected)   │  │ Propagation  │  │ Inspector    │   │
│  │ [Click node] │  │              │  │ [Enable]     │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│  Legend: ● Healthy ● Degraded ● Critical ● Unknown                        │
│  Edge: ── Sync call  - - - Async (MQ)  ████ High QPS                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.7.2 Trace Waterfall Drawer

```
┌─────────────────────────────────────────────────────────────┐
│  Trace Waterfall: tr-abc123def456                            │
│  Service: dshb-gateway → dshb-auth → dshb-user              │
│  Total: 42ms  │  Status: ✓ Success                           │
├─────────────────────────────────────────────────────────────┤
│  Span                    Time     Duration  Status           │
│  ─────────────────────────────────────────────────────────   │
│  [====] GET /api/v87/orders       42ms    ✓                 │
│      ├─ [==] POST /auth/token       8ms    ✓                │
│      │     └─ [ ] Redis GET           2ms    ✓              │
│      ├─ [==] GET /users/{id}         12ms   ✓               │
│      │     └─ [ ] DB Query            10ms   ✓              │
│      ├─ [==] GET /inventory/{sku}    14ms   ✓               │
│      │     └─ [ ] DB Query            12ms   ✓              │
│      └─ [ ] Log event                2ms    ✓               │
└─────────────────────────────────────────────────────────────┘
```

### 4.8 API Contract

#### 4.8.1 Topology Query API

```json
// GET /api/v87/topology/query
// Headers: X-Panel-ID: V87-P-002, X-Baseline-Version: V200-1.0
{
  "request": {
    "namespace": "production",
    "depth": 3,                    // Max depth from any node
    "layout": "force-directed",
    "include_metrics": true,
    "include_fault_propagation": false,
    "time_range": {
      "from": "2025-01-15T14:00:00Z",
      "to": "2025-01-15T15:00:00Z"
    }
  },
  "response": {
    "status": "OK",
    "topology": {
      "nodes": [
        {
          "id": "dshb-gateway-001",
          "name": "DSHB API Gateway",
          "health": "healthy",
          "qps": 12450,
          "p99_latency_ms": 42,
          "error_rate_pct": 0.008,
          "cpu_usage_pct": 34.2,
          "memory_usage_pct": 62.1,
          "pod_count": 6,
          "version": "v87.0.1"
        }
      ],
      "edges": [
        {
          "id": "dshb-gateway-001->dshb-auth-001",
          "source": "dshb-gateway-001",
          "target": "dshb-auth-001",
          "protocol": "HTTP",
          "endpoint": "/auth/token",
          "qps": 10200,
          "p99_latency_ms": 12,
          "error_rate_pct": 0.005,
          "health": "healthy"
        }
      ],
      "layout": {
        "algorithm": "force-directed",
        "positions": {
          "dshb-gateway-001": {"x": 400, "y": 300},
          "dshb-auth-001": {"x": 550, "y": 200},
          "dshb-user-001": {"x": 700, "y": 300}
        },
        "computed_at": "2025-01-15T14:00:00Z"
      },
      "topology_hash": "a3f2b1c9d8e7f6"
    }
  }
}
```

#### 4.8.2 Incremental Update API

```json
// WebSocket message: topology.update
{
  "type": "topology.update",
  "timestamp": "2025-01-15T15:01:00Z",
  "delta": {
    "added_nodes": [
      {"id": "dshb-new-svc-001", "name": "New Service", "health": "unknown"}
    ],
    "removed_nodes": [],
    "updated_nodes": [
      {
        "id": "dshb-gateway-001",
        "changes": {
          "qps": 13100,
          "p99_latency_ms": 45,
          "error_rate_pct": 0.012
        }
      }
    ],
    "added_edges": [
      {
        "id": "dshb-gateway-001->dshb-new-svc-001",
        "source": "dshb-gateway-001",
        "target": "dshb-new-svc-001",
        "qps": 500,
        "p99_latency_ms": 25
      }
    ],
    "removed_edges": [],
    "updated_edges": []
  },
  "topology_hash": "b4c3a2d8e9f0a1"
}
```

#### 4.8.3 Trace Query API

```json
// GET /api/v87/topology/trace/waterfall
// Query params: trace_id, service_id, time_range
{
  "response": {
    "trace_id": "tr-abc123def456",
    "total_duration_ms": 42,
    "status": "SUCCESS",
    "spans": [
      {
        "span_id": "sp-001",
        "parent_span_id": null,
        "service": "dshb-gateway-001",
        "operation": "GET /api/v87/orders",
        "start_time": "2025-01-15T14:30:00.000Z",
        "duration_ms": 42,
        "status": "OK",
        "children": [
          {
            "span_id": "sp-002",
            "parent_span_id": "sp-001",
            "service": "dshb-auth-001",
            "operation": "POST /auth/token",
            "start_time": "2025-01-15T14:30:00.010Z",
            "duration_ms": 8,
            "status": "OK",
            "children": [
              {
                "span_id": "sp-003",
                "parent_span_id": "sp-002",
                "service": "redis-cache-001",
                "operation": "GET session:abc123",
                "start_time": "2025-01-15T14:30:00.012Z",
                "duration_ms": 2,
                "status": "OK",
                "children": []
              }
            ]
          }
        ]
      }
    ],
    "hermes_fields": {
      "event_type": "TRACE",
      "trace_id": "tr-abc123def456",
      "batch_id": "batch-traces-20250115-143000"
    }
  }
}
```

### 4.9 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| 500-node topology render | ≤2s | Performance.now() measurement |
| 100-node topology render | ≤500ms | Performance.now() measurement |
| Incremental refresh latency | ≤1s | WebSocket push to render |
| Full refresh cycle | 60s | Configured polling interval |
| API response time (P99) | ≤300ms | API gateway metrics |
| Memory usage | ≤100MB per user session | Browser DevTools measurement |

### 4.10 Test Plan

| Test Category | Test Cases | Tools |
|--------------|------------|-------|
| Unit Tests | Node/edge model, layout algorithms, diff computation | Jest |
| Integration Tests | Registry API, WebSocket updates, trace queries | Supertest + ws |
| Performance Tests | 100/250/500 node rendering, incremental updates | Lighthouse + custom |
| Visual Regression | Layout stability across updates | Chromatic |
| Cross-browser | Chrome, Firefox, Safari, Edge | Playwright |
| Stress Test | 200 concurrent users viewing topology | k6 |

---

## 5. V87-P-003: Automated Capacity Planning Panel

### 5.1 Panel Metadata

| Attribute | Value |
|-----------|-------|
| **Panel ID** | V87-P-003 |
| **Panel Name** | 自动化容量规划 / Automated Capacity Planning |
| **Priority** | P1 (Mission-Critical) |
| **Estimated Effort** | 28 person-days |
| **Owner** | Platform Engineering Team |
| **Data Source** | HERMES Capacity Service + DSHB Metrics + V86-P-022 (extended) |
| **ML Models** | Prophet + LSTM hybrid prediction |
| **Integration Status** | Phase02 ACTIVE |

### 5.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      V87-P-003 ARCHITECTURE                                  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     BROWSER (Frontend)                                 │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │              Capacity Dashboard Grid                             │  │  │
│  │  │                                                                   │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  REGION 1: Capacity Overview (KPIs)                        │  │  │  │
│  │  │  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                     │  │  │  │
│  │  │  │  │CPU │ │Mem │ │Disk│ │QPS │ │Net │                     │  │  │  │
│  │  │  │  │72% │ │65% │ │58% │ │12k │ │3ms │                     │  │  │  │
│  │  │  │  └────┘ └────┘ └────┘ └────┘ └────┘                     │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │  │
│  │  │                                                                   │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  REGION 2: Load Trend Forecast                            │  │  │  │
│  │  │  │  Multi-resource prediction with confidence intervals       │  │  │  │
│  │  │  │  Prophet (trend + seasonality) + LSTM (non-linear patterns) │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │  │
│  │  │                                                                   │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  REGION 3: Capacity Recommendations                        │  │  │  │
│  │  │  │  Elastic scaling suggestions with cost estimates           │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │  │
│  │  │                                                                   │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  REGION 4: Forecast Accuracy Tracking                      │  │  │  │
│  │  │  │  MAPE ≤15% — rolling accuracy metrics                      │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │  │
│  │  │                                                                   │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  REGION 5: Scaling Window Calendar                         │  │  │  │
│  │  │  │  Gantt-style view of planned/active scaling windows        │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │  │
│  │  │                                                                   │  │  │
│  │  │  ┌───────────────────────────────────────────────────────────┐  │  │  │
│  │  │  │  REGION 6: Capacity Alerts                                 │  │  │  │
│  │  │  │  Active capacity-related alerts and warnings               │  │  │  │
│  │  │  └───────────────────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                  API Layer                                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │ Prediction   │  │ Recommendation│  │ History API  │               │  │
│  │  │ API          │  │ API           │  │              │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              Backend Services                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │ ML Inference │  │ Business     │  │ Capacity     │               │  │
│  │  │ (Prophet+LSTM│  │ Driver Model│  │ Decision     │               │  │
│  │  │              │  │              │  │ Engine       │               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Prediction Model Integration

#### 5.3.1 Multi-Resource Prediction Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Metric     │───►│  Pre-       │───►│  Ensemble   │───►│  Output     │
│  Collection │    │  Processing │    │  Prediction │    │  Generation │
│  (30d hist) │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                  │                   │                   │
     │              ┌───▼──────────────┐    │                   │
     │              │ • Missing value   │    │                   │
     │              │   imputation      │    │                   │
     │              │ • Feature scaling  │    │                   │
     │              │ • Holiday markers  │    │                   │
     │              │ • Business driver  │    │                   │
     │              │   correlation      │    │                   │
     │              │ • Lags & rolling   │    │                   │
     │              │   statistics       │    │                   │
     │              └───────────────────┘    │                   │
     │                                       │                   │
     │              ┌─────────────────────────┤                   │
     │              │                         │                   │
     │         ┌────▼──────────┐    ┌─────────▼────┐              │
     │         │  Prophet      │    │  LSTM        │              │
     │         │  (Trend +     │    │  (Non-linear │              │
     │         │   Seasonal)   │    │   Patterns)  │              │
     │         │               │    │              │              │
     │         │  Weight: 0.4  │    │  Weight: 0.6 │              │
     │         └───────┬───────┘    └────────┬─────┘              │
     │                 │                     │                    │
     │                 └──────────┬──────────┘                    │
     │                            │                                │
     │                 ┌──────────▼──────────┐                    │
     │                 │  Weighted Average   │                    │
     │                 │  + Confidence       │                    │
     │                 │  Interval (95%)     │                    │
     │                 └──────────┬──────────┘                    │
     │                            │                                │
     │                            └──────────────────────────────►│
     │                                                             │
     ▼                                                             ▼
  ┌─────────┐                                              ┌─────────────┐
  │Business │                                              │ Prediction  │
  │Drivers  │                                              │ Time Series │
  │(Event   │◄───── used for feature engineering ─────────►│ (1h steps) │
  │Calendar)│                                              │ + CI bounds │
  └─────────┘                                              └─────────────┘
```

#### 5.3.2 Prediction Configuration

```typescript
// @dshb/model-api/src/capacity-prediction.ts
interface CapacityPredictionConfig {
  resources: ResourcePrediction[];
  business_drivers: BusinessDriverConfig[];
  model_params: {
    prophet: {
      changepoint_prior_scale: number;    // Default: 0.01
      seasonality_prior_scale: number;    // Default: 10.0
      holidays_prior_scale: number;       // Default: 10.0
      weekly_seasonality: boolean;        // Default: true
      yearly_seasonality: boolean;        // Default: false
    };
    lstm: {
      hidden_size: number;                // Default: 128
      num_layers: number;                 // Default: 2
      dropout: number;                    // Default: 0.2
      sequence_length: number;            // Default: 168 (1 week of hourly)
      output_horizon: number;             // Default: 168 (1 week ahead)
    };
    ensemble: {
      prophet_weight: number;             // Default: 0.4
      lstm_weight: number;                // Default: 0.6
    };
  };
  accuracy_targets: {
    mape: number;                         // Target: ≤15%
    rmse: number;                         // Target: ≤0.15 (normalized)
  };
}

interface ResourcePrediction {
  resource_name: 'cpu' | 'memory' | 'disk' | 'qps' | 'network_latency';
  unit: string;                           // '%', 'MB', 'GB', 'req/s', 'ms'
  baseline_threshold: number;             // V200-1.0 threshold
  warning_threshold: number;              // 80% of max
  critical_threshold: number;             // 95% of max
  prediction_horizon_hours: number;       // Default: 168 (7 days)
}
```

### 5.4 Capacity Recommendation Engine

#### 5.4.1 Recommendation Logic

```python
# Pseudocode: Capacity recommendation engine
def generate_capacity_recommendations(
    predictions: Dict[str, Prediction],
    current_config: ServiceConfig,
    business_drivers: List[BusinessEvent],
    cost_model: CostModel
) -> List[CapacityRecommendation]:
    
    recommendations = []
    
    for resource, pred in predictions.items():
        current_usage = current_config.resources[resource].usage
        projected_peak = pred.predicted_max  # 7-day ahead
        threshold = current_config.resources[resource].warning_threshold
        
        # Check if projected usage exceeds threshold
        days_to_threshold = pred.days_to_threshold()
        
        if days_to_threshold is not None and days_to_threshold <= 7:
            # Calculate recommended scaling
            required_increase = (projected_peak - threshold) / current_usage
            recommended_scale_factor = 1.0 + required_increase + 0.2  # 20% headroom
            
            # Consider business drivers
            upcoming_events = [e for e in business_drivers if e.start < pred.end_time]
            event_impact = sum(e.capacity_impact for e in upcoming_events)
            recommended_scale_factor *= (1.0 + event_impact)
            
            # Calculate cost
            cost_estimate = cost_model.estimate(
                service=current_config,
                resource=resource,
                scale_factor=recommended_scale_factor,
                duration_days=days_to_threshold + 7
            )
            
            # Determine urgency
            if days_to_threshold <= 1:
                urgency = "IMMEDIATE"
            elif days_to_threshold <= 3:
                urgency = "URGENT"
            elif days_to_threshold <= 7:
                urgency = "PLANNED"
            else:
                urgency = "SCHEDULED"
            
            recommendations.append(CapacityRecommendation(
                resource=resource,
                current_usage=current_usage,
                projected_peak=projected_peak,
                days_to_threshold=days_to_threshold,
                recommended_scale_factor=recommended_scale_factor,
                cost_estimate_usd=cost_estimate.monthly_cost,
                urgency=urgency,
                rationale=generate_rationale(pred, business_drivers, cost_estimate)
            ))
    
    # Sort by urgency
    urgency_order = {"IMMEDIATE": 0, "URGENT": 1, "PLANNED": 2, "SCHEDULED": 3}
    recommendations.sort(key=lambda r: urgency_order[r.urgency])
    
    return recommendations
```

### 5.5 UI Component Specification

#### 5.5.1 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  V87-P-003: Automated Capacity Planning                                    │
│  [Service: dshb-gateway ▼] [Timeframe: 7d ▼] [Refresh: Auto(60s) ▼]       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ REGION 1: Capacity Overview ──────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ CPU      │  │ Memory   │  │ Disk     │  │ QPS      │          │   │
│  │  │ ███████░░│  │ ██████░░░│  │ █████░░░░│  │ █████████│          │   │
│  │  │ 72%      │  │ 65%      │  │ 58%      │  │ 12,450   │          │   │
│  │  │ ▲ +3%   │  │ ▲ +2%   │  │ ▲ +1%   │  │ ▲ +5%   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  │                                                                     │   │
│  │  Health: ● All Resources Within Thresholds                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ REGION 2: Load Trend Forecast (7-day ahead) ─────────────────────┐   │
│  │                                                                     │   │
│  │  CPU% 100┤                                                       │   │
│  │          │          ╱╲                                           │   │
│  │          │         ╱  ╲          ╱╲  ← Predicted Peak (82%)      │   │
│  │          │        ╱    ╲        ╱  ╲                             │   │
│  │          │       ╱      ╲      ╱    ╲                            │   │
│  │     50  ┤──────╱────────╲────╱──────╲────────────────            │   │
│  │          │      ╱        ╲   ╱                                          │   │
│  │          │     ╱          ╲ ╱                                           │   │
│  │          │    ╱            ╳                                            │   │
│  │          │   ╱              ╲╱                                         │   │
│  │     0   ┤──╱────────────────────────────────────                      │   │
│  │          │Mon Tue Wed Thu Fri Sat Sun                                   │   │
│  │          │─── Actual ─ ─ ─ Predicted   ▒ Confidence Interval (95%)  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ REGION 3: Capacity Recommendations ──────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐         │   │
│  │  │ Resource │  Current │ Projected│  Days To │ Cost     │         │   │
│  │  │          │  Usage   │   Peak   │Threshold │Estimate  │         │   │
│  │  ├──────────┼──────────┼──────────┼──────────┼──────────┤         │   │
│  │  │ CPU      │   72%    │   82%    │   2 days │ $1,200/mo│         │   │
│  │  │ Memory   │   65%    │   78%    │   5 days │   $800/mo│         │   │
│  │  │ QPS      │  12,450  │  18,000  │   1 day  │  $2,500/mo│         │   │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘         │   │
│  │                                                                     │   │
│  │  [Scale Up: CPU +50%] [Scale Up: Mem +30%] [Schedule QPS Scaling]  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ REGION 4: Forecast Accuracy ────┐  ┌─ REGION 5: Scaling Calendar ──┐  │
│  │                                   │  │                                 │  │
│  │  MAPE: 8.3% (target ≤15%) ✓     │  │  Jan 15  │██ QPS Scaling ██   │  │
│  │  RMSE: 0.09 (target ≤0.15) ✓    │  │  Jan 16  │██ CPU Scaling ██    │  │
│  │                                   │  │  Jan 17  │                     │  │
│  │  ┌──────────────────────────┐   │  │  Jan 18  │██ Black Friday Prep  │  │
│  │  │  📊 Rolling MAPE (7d)   │   │  │  Jan 19  │██ Black Friday Prep  │  │
│  │  │  10%──┐                  │   │  │  Jan 20  │██ Black Friday Prep  │  │
│  │  │      │   ╲              │   │  │  Jan 21  │                     │  │
│  │  │   8% │     ╲__          │   │  │  Jan 22  │██ Mem Scaling ██    │  │
│  │  │      │         ╲__      │   │  │  Jan 23  │                     │  │
│  │  │   6% └──────────────    │   │  │                                 │  │
│  │  └──────────────────────────┘   │  └─────────────────────────────────┘  │
│  └───────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                             │
│  ┌─ REGION 6: Capacity Alerts ────────────────────────────────────────┐   │
│  │  🟡 [PLANNED] QPS projected to exceed 15,000 within 48h — consider  │   │
│  │       pre-scaling to 18,000 capacity (cost: $2,500/mo)               │   │
│  │  🟢 [OK] CPU within thresholds — next check in 24h                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.6 API Contract

#### 5.6.1 Prediction API

```json
// GET /api/v87/capacity/predict
{
  "request": {
    "service_id": "dshb-gateway-001",
    "resources": ["cpu", "memory", "qps"],
    "horizon_hours": 168,
    "include_confidence_interval": true,
    "model_version": "v200.1.0"
  },
  "response": {
    "status": "OK",
    "predictions": [
      {
        "resource": "cpu",
        "unit": "percent",
        "current_value": 72.3,
        "forecast": [
          {
            "timestamp": "2025-01-15T15:00:00Z",
            "predicted": 74.1,
            "confidence_lower_95": 70.5,
            "confidence_upper_95": 77.8,
            "component_predictions": {
              "prophet": 73.8,
              "lstm": 74.4
            }
          }
        ],
        "peak": {
          "value": 82.0,
          "timestamp": "2025-01-17T14:00:00Z",
          "confidence_lower_95": 78.5,
          "confidence_upper_95": 85.2
        },
        "days_to_warning_threshold": 2,
        "days_to_critical_threshold": 1,
        "trend": "increasing",
        "accuracy": {
          "mape": 8.3,
          "rmse": 0.09,
          "last_evaluated_at": "2025-01-15T06:00:00Z"
        }
      }
    ],
    "business_drivers": [
      {
        "event_name": "Black Friday Sale",
        "start": "2025-01-18T00:00:00Z",
        "end": "2025-01-20T23:59:59Z",
        "expected_capacity_impact": 0.45,
        "affected_resources": ["cpu", "memory", "qps"]
      }
    ],
    "model_version": "v200.1.0"
  }
}
```

#### 5.6.2 Recommendation API

```json
// GET /api/v87/capacity/recommendations
{
  "response": {
    "recommendations": [
      {
        "recommendation_id": "rec-20250115-001",
        "service_id": "dshb-gateway-001",
        "resource": "qps",
        "urgency": "URGENT",
        "current_usage": 12450,
        "projected_peak": 18000,
        "projected_peak_timestamp": "2025-01-17T14:00:00Z",
        "days_to_threshold": 1,
        "recommended_scale_factor": 1.5,
        "recommended_capacity": 18675,
        "cost_estimate": {
          "monthly_cost_usd": 2500,
          "daily_cost_usd": 83.33,
          "currency": "USD"
        },
        "rationale": "QPS is projected to reach 18,000 by Jan 17 due to Black Friday sale. Current capacity of 15,000 will be exceeded. Recommend scaling to 18,675 (1.5x) with 20% headroom. Monthly cost increase: $2,500.",
        "actions": [
          {
            "action": "scale_up",
            "resource": "qps",
            "target": 18675,
            "estimated_completion": "2025-01-15T16:00:00Z"
          }
        ],
        "created_at": "2025-01-15T14:00:00Z"
      }
    ]
  }
}
```

#### 5.6.3 Scaling Window Calendar API

```json
// GET /api/v87/capacity/scaling-calendar
{
  "response": {
    "windows": [
      {
        "window_id": "sw-20250115-001",
        "service_id": "dshb-gateway-001",
        "resource": "qps",
        "status": "PLANNED",
        "scheduled_start": "2025-01-15T16:00:00Z",
        "scheduled_end": "2025-01-15T18:00:00Z",
        "action": "scale_up",
        "from_value": 15000,
        "to_value": 18675,
        "reason": "Capacity recommendation rec-20250115-001",
        "approval_status": "PENDING",
        "approved_by": null,
        "created_by": "capacity-engine",
        "created_at": "2025-01-15T14:00:00Z"
      }
    ]
  }
}
```

### 5.7 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Panel load time (P99) | ≤2s | Lighthouse |
| Prediction API (P99) | ≤1s | API gateway metrics |
| Forecast accuracy (MAPE) | ≤15% | Backtesting on holdout data |
| Recommendation latency | ≤500ms | Engine metrics |
| Scaling window execution | ≤10 min from approval | Infrastructure metrics |

### 5.8 Test Plan

| Test Category | Test Cases | Tools |
|--------------|------------|-------|
| Unit Tests | Prediction models, recommendation engine, cost calculator | Jest |
| Integration Tests | API contracts, model service, scaling workflow | Supertest |
| Performance Tests | 1h/24h/7d prediction latency | Custom load tests |
| Accuracy Tests | MAPE/RMSE validation on 30d holdout | Backtesting framework |
| Business Driver Tests | Event calendar impact calculation | Integration tests |
---

## 6. V87-P-004: Alert Correlation Analysis Panel

### 6.1 Panel Metadata

| Attribute | Value |
|-----------|-------|
| **Panel ID** | V87-P-004 |
| **Panel Name** | 告警关联分析 / Alert Correlation Analysis |
| **Priority** | P1 (Mission-Critical) |
| **Estimated Effort** | 32 person-days |
| **Owner** | Alerting Platform Team |
| **Data Source** | HERMES Alert Service + Correlation Engine + Alert Store |
| **Clustering Algorithm** | DBSCAN (density-based spatial clustering) |
| **Integration Status** | Phase02 ACTIVE |

### 6.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      V87-P-004 ARCHITECTURE                                  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     BROWSER (Frontend)                                 │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  REGION 1: Correlation Event Overview (KPIs + Timeline)         │  │  │
│  │  │  REGION 2: Alert Timeline (Chronological view with clusters)    │  │  │
│  │  │  REGION 3: Root Cause Recommendations                           │  │  │
│  │  │  REGION 4: Suppression Status                                   │  │  │
│  │  │  REGION 5: Correlation Matrix                                   │  │  │
│  │  │  REGION 6: Event Details                                        │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              Correlation Engine (Backend)                                │  │
│  │                                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ Alert        │  │ Clustering   │  │ Root Cause   │                │  │
│  │  │ Ingestor     │──►│ (DBSCAN)    │──►│ Inference    │                │  │
│  │  │              │  │              │  │ Engine       │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  │         │                  │                   │                        │  │
│  │         ▼                  ▼                   ▼                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ Suppression  │  │ Correlation  │  │ Notification │                │  │
│  │  │ Engine       │  │ Score Calc   │  │ Service      │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Clustering Algorithm (DBSCAN)

#### 6.3.1 Alert Feature Vector Construction

```python
# Pseudocode: Alert feature vector for clustering
def build_alert_feature_vector(alert: Alert) -> np.ndarray:
    """
    Build a feature vector for an alert to be used in DBSCAN clustering.
    Features are normalized to [0, 1] range.
    """
    features = {
        # Temporal features
        'time_since_last_alert': normalize(alert.time_since_last, 0, 600),
        'time_of_day': alert.timestamp.hour / 24.0,
        'day_of_week': alert.timestamp.dayofweek / 7.0,
        
        # Metric features
        'value_deviation': normalize(alert.value_deviation, -5, 5),
        'trend_direction': {
            'rising': 1.0, 'falling': -1.0, 'stable': 0.0
        }.get(alert.trend_direction, 0.0),
        
        # Service features
        'service_type': hash_service_type(alert.service_type),  # One-hot encoded
        'resource_type': hash_resource_type(alert.resource_type),  # One-hot encoded
        'region': hash_region(alert.region),  # One-hot encoded
        
        # Context features
        'correlation_score': alert.correlation_score,  # Pre-computed
        'dependency_depth': normalize(alert.dependency_depth, 0, 10),
        'alert_density': normalize(alert.alert_density_per_min, 0, 100),
    }
    
    return np.array(list(features.values()))
```

#### 6.3.2 DBSCAN Configuration

```python
# Pseudocode: DBSCAN clustering with adaptive parameters
from sklearn.cluster import DBSCAN

def cluster_alerts(alerts: List[Alert], config: DBSCANConfig = None) -> List[Cluster]:
    if config is None:
        config = DBSCANConfig()
    
    # Build feature matrix
    features = np.array([build_alert_feature_vector(a) for a in alerts])
    
    # Adaptive epsilon based on data density
    # Compute pairwise distances for a sample
    sample_size = min(1000, len(features))
    sample_indices = np.random.choice(len(features), sample_size, replace=False)
    sample_features = features[sample_indices]
    distances = compute_pairwise_distances(sample_features)
    
    # Epsilon = 95th percentile of distances (adjustable)
    epsilon = np.percentile(distances, 95)
    epsilon = max(config.min_epsilon, min(config.max_epsilon, epsilon))
    
    # DBSCAN clustering
    db = DBSCAN(
        eps=epsilon,
        min_samples=config.min_samples,       # Default: 3
        metric=config.metric,                  # 'cosine' for normalized features
        algorithm=config.algorithm,            # 'auto'
        n_jobs=-1
    )
    labels = db.fit_predict(features)
    
    # Extract clusters
    clusters = []
    for cluster_id in set(labels):
        if cluster_id == -1:
            continue  # Skip noise
        cluster_alerts = [alerts[i] for i, l in enumerate(labels) if l == cluster_id]
        clusters.append(Cluster(
            id=f"cluster-{cluster_id}",
            alerts=cluster_alerts,
            centroid=compute_cluster_centroid(cluster_alerts),
            noise_points=sum(1 for l in labels if l == -1 and cluster_id != -1),
            density=compute_cluster_density(cluster_alerts),
            created_at=datetime.now()
        ))
    
    return clusters

class DBSCANConfig:
    min_samples: int = 3
    min_epsilon: float = 0.3
    max_epsilon: float = 0.8
    metric: str = 'cosine'
    algorithm: str = 'auto'
```

### 6.4 Correlation Engine

#### 6.4.1 Correlation Scoring Algorithm

```python
# Pseudocode: Multi-dimensional correlation scoring
def compute_correlation_score(alert_a: Alert, alert_b: Alert) -> float:
    """
    Compute correlation score between two alerts.
    Score >= 0.8 indicates high correlation.
    """
    scores = {}
    
    # 1. Temporal correlation (weight: 0.30)
    time_diff_min = abs(alert_a.timestamp - alert_b.timestamp).total_seconds() / 60.0
    scores['temporal'] = max(0.0, 1.0 - time_diff_min / 30.0)  # Decay over 30 min
    
    # 2. Service dependency correlation (weight: 0.35)
    if alert_a.service_id in alert_b.dependent_services or \
       alert_b.service_id in alert_a.dependent_services:
        scores['dependency'] = 1.0
    elif alert_a.service_id == alert_b.service_id:
        scores['dependency'] = 0.5
    else:
        scores['dependency'] = 0.0
    
    # 3. Metric similarity (weight: 0.20)
    if alert_a.metric == alert_b.metric:
        scores['metric'] = 1.0
    elif alert_a.resource_type == alert_b.resource_type:
        scores['metric'] = 0.6
    else:
        scores['metric'] = 0.0
    
    # 4. Trend similarity (weight: 0.15)
    if alert_a.trend_direction == alert_b.trend_direction:
        scores['trend'] = 1.0
    elif alert_a.trend_direction == 'stable' or alert_b.trend_direction == 'stable':
        scores['trend'] = 0.5
    else:
        scores['trend'] = 0.0
    
    # Weighted sum
    weights = {'temporal': 0.30, 'dependency': 0.35, 'metric': 0.20, 'trend': 0.15}
    total_score = sum(scores[k] * weights[k] for k in scores)
    
    return min(1.0, total_score)

# Correlation threshold
CORRELATION_THRESHOLD = 0.8
```

#### 6.4.2 Root Cause Inference

```python
# Pseudocode: Root cause inference using Bayesian network + dependency graph
def infer_root_cause(cluster: Cluster, topology: Topology) -> List[RootCauseCandidate]:
    """
    Infer potential root causes for a cluster of correlated alerts.
    Uses Bayesian probability + dependency depth analysis.
    """
    candidates = []
    
    # Score each alert in the cluster as a potential root cause
    for alert in cluster.alerts:
        score = 0.0
        
        # 1. Earliest alert in cluster (causal priority)
        time_rank = cluster.alerts.index(alert)
        temporal_score = 1.0 - (time_rank / len(cluster.alerts))
        score += temporal_score * 0.30
        
        # 2. Dependency depth (root cause = service with most dependents)
        dependents_count = topology.count_dependents(alert.service_id)
        max_dependents = max(t.count_dependents(a.service_id) for a in cluster.alerts)
        dependency_score = dependents_count / max(max_dependents, 1)
        score += dependency_score * 0.35
        
        # 3. Alert severity (higher severity = more likely root cause)
        severity_weights = {'P1': 1.0, 'P2': 0.8, 'P3': 0.6, 'P4': 0.4, 'P5': 0.2}
        severity_score = severity_weights.get(alert.priority, 0.0)
        score += severity_score * 0.20
        
        # 4. Anomaly score (higher = more likely root cause)
        anomaly_score = alert.anomaly_score if hasattr(alert, 'anomaly_score') else 0.5
        score += anomaly_score * 0.15
        
        # Normalize
        candidates.append(RootCauseCandidate(
            alert=alert,
            score=min(1.0, score),
            confidence='HIGH' if score >= 0.75 else 'MEDIUM' if score >= 0.50 else 'LOW',
            rationale=generate_rationale(alert, cluster, topology, score)
        ))
    
    # Sort by score
    candidates.sort(key=lambda c: c.score, reverse=True)
    
    # Root cause accuracy target: >=80% (measured by human validation feedback)
    return candidates[:3]  # Top 3 candidates
```

### 6.5 Suppression Engine

#### 6.5.1 Suppression Rules

```python
# Pseudocode: Alert storm auto-suppression
class SuppressionEngine:
    def __init__(self, config: SuppressionConfig):
        self.config = config
        self.suppression_window = {}  # alert_key -> last_suppressed_at
    
    def should_suppress(self, alert: Alert) -> SuppressionDecision:
        """
        Determine if an alert should be suppressed.
        Suppression delay target: <=5s P99
        """
        # 1. Check for active suppression rules
        for rule in self.config.suppression_rules:
            if rule.matches(alert):
                # Calculate suppression delay
                now = datetime.now()
                last_suppressed = self.suppression_window.get(alert.key)
                delay = (now - last_suppressed).total_seconds() if last_suppressed else 0
                
                if delay < rule.silence_period:
                    return SuppressionDecision(
                        suppress=True,
                        rule_id=rule.id,
                        reason=f"Silenced by rule {rule.id}: {rule.description}",
                        next_check=now + timedelta(seconds=rule.silence_period - delay)
                    )
        
        # 2. Check for alert storm detection
        storm_score = self._detect_storm(alert)
        if storm_score >= self.config.storm_threshold:
            return SuppressionDecision(
                suppress=True,
                rule_id="auto-storm",
                reason=f"Alert storm detected (score: {storm_score:.2f})",
                next_check=datetime.now() + timedelta(seconds=self.config.storm_silence)
            )
        
        return SuppressionDecision(suppress=False)
    
    def _detect_storm(self, alert: Alert) -> float:
        """Detect alert storm: burst of alerts in short window."""
        recent_alerts = self._get_recent_alerts(alert.service_id, window_seconds=60)
        if len(recent_alerts) < self.config.storm_min_alerts:
            return 0.0
        
        # Storm score: alert density + correlation
        density = len(recent_alerts) / 60.0  # alerts per minute
        avg_correlation = self._avg_correlation(recent_alerts)
        storm_score = min(1.0, (density / 10.0) * 0.6 + avg_correlation * 0.4)
        
        return storm_score

class SuppressionConfig:
    storm_threshold: float = 0.7
    storm_min_alerts: int = 5
    storm_silence: int = 300  # 5 minutes
    suppression_delay_target_ms: int = 5000  # P99 target
```

### 6.6 UI Component Specification

#### 6.6.1 Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  V87-P-004: Alert Correlation Analysis                                     │
│  [Cluster: All ▼] [Time Range: 1h ▼] [Threshold: 0.80] [Refresh: Auto]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ REGION 1: Correlation Event Overview ────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │   │
│  │  │Total │ │Active│ │Suppr.│ │Storm │ │Avg   │                   │   │
│  │  │Alerts│ │Clusters│ │Count│ │Detected│ │Score│                   │   │
│  │  │  142 │ │   18  │ │  37  │ │   3   │ │0.82  │                   │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                   │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  📊 Correlation Timeline (last 1h)                          │  │   │
│  │  │  142 ┤  ▁▁▂▂▃▃▃▄▄▄▅▅▅▆▆▆▇▇▇█▇▇▆▆▅▅▄▄▃▃▂▂▁▁▁            │  │   │
│  │  │   70 ┤                                                        │  │   │
│  │  │    0 ┤                                                        │  │   │
│  │  │      └──────────────────────────────────────                 │  │   │
│  │  │  13:00    13:15    13:30    13:45    14:00                   │  │   │
│  │  │  ── Total Alerts  -- Correlated  -- Suppressed                │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ REGION 2: Alert Timeline ────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Time       │ Alert ID     │ Metric    │ Service    │ Cluster │   │   │
│  │  ─────────────────────────────────────────────────────────────    │   │
│  │  14:32:00   │ alert-001    │ err_rate  │ dshb-gw    │ C-012   │   │   │
│  │  14:32:05   │ alert-002    │ cpu_usage │ dshb-auth  │ C-012   │   │   │
│  │  14:32:10   │ alert-003    │ mem_usage │ dshb-user  │ C-012   │   │   │
│  │  14:32:15   │ alert-004    │ qps       │ dshb-order │ C-012   │   │   │
│  │  14:32:20   │ alert-005    │ err_rate  │ dshb-inv   │ C-012   │   │   │
│  │  ────── ─────────────────────────────────────────────────────     │   │   │
│  │  │ Cluster C-012: 5 alerts, correlation score: 0.91              │   │   │
│  │  │ Root cause: dshb-gateway (confidence: HIGH)                    │   │   │
│  │  │ Suppressed: 3 of 5 alerts (60% noise reduction)                │   │   │
│  │  ────── ─────────────────────────────────────────────────────     │   │   │
│  │  14:28:00   │ alert-010    │ disk_io   │ db-primary │ C-011   │   │   │
│  │  14:28:03   │ alert-011    │ conn_pool │ db-replica │ C-011   │   │   │
│  │  ...                                                       │   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ REGION 3: Root Cause Recommendations ────────────────────────────┐   │
│  │  Cluster C-012 (14:32)                                             │   │
│  │  ┌──────────────┬──────────┬──────────┬──────────────────────┐   │   │
│  │  │ Candidate    │ Score    │Confidence│ Rationale              │   │   │
│  │  ├──────────────┼──────────┼──────────┼──────────────────────┤   │   │
│  │  │ dshb-gateway │   0.92   │   HIGH   │ Earliest alert, most │   │   │
│  │  │              │          │          │ dependent services   │   │   │
│  │  ├──────────────┼──────────┼──────────┼──────────────────────┤   │   │
│  │  │ dshb-auth    │   0.74   │   MEDIUM │ High severity, deep  │   │   │
│  │  │              │          │          │ in call chain        │   │   │
│  │  ├──────────────┼──────────┼──────────┼──────────────────────┤   │   │
│  │  │ dshb-user    │   0.51   │   LOW    │ Downstream from      │   │   │
│  │  │              │          │          │ gateway, later alert │   │   │
│  │  └──────────────┴──────────┴──────────┴──────────────────────┘   │   │
│  │                                                                     │   │
│  │  [View Trace] [View Topology] [Acknowledge] [Dismiss]               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ REGION 4: Suppression Status ────────┐  ┌─ REGION 5: Correlation     │  │
│  │                                        │  │    Matrix                   │  │
│  │  Active Suppressions: 37               │  │                            │  │
│  │  Storm Suppressions: 3                 │  │  Service    │ dshb-gw│auth│ │  │
│  │                                        │  │ ──────────┼───────┼──────┤  │  │
│  │  ┌──────────────────────────────────┐ │  │ dshb-gw    │ 1.00  │ 0.92│  │  │
│  │  │ Rule           │ Count │ Expiry  │ │  │ dshb-auth  │ 0.92  │ 1.00│  │  │
│  │  ├────────────────┼───────┼────────┤ │  │ dshb-user  │ 0.85  │ 0.78│  │  │
│  │  │ storm-001      │  12   │ 14:37  │ │  │ dshb-order │ 0.72  │ 0.65│  │  │
│  │  │ silence-err    │   8   │ 14:45  │ │  │ dshb-inv   │ 0.88  │ 0.71│  │  │
│  │  │ dedup-db       │   5   │ 14:50  │ │  │            │       │      │  │  │
│  │  │ auto-suppress  │  12   │ 14:32  │ │  └─────────────────────────────┘  │
│  │  └────────────────┴───────┴────────┘ │  │ Color: Red(>0.8) Orange(0.5-0.8)│  │
│  │                                        │  │       Green(<0.5)               │  │
│  └────────────────────────────────────────┘  └──────────────────────────────┘  │
│                                                                             │
│  ┌─ REGION 6: Event Details ───────────────────────────────────────────┐  │
│  │  [Selected: Cluster C-012]                                           │  │
│  │  Timeline: 14:32:00 → 14:32:20 (20 seconds)                         │  │
│  │  Correlation Score: 0.91  │  Noise Reduction: 60%                    │  │
│  │  Root Cause: dshb-gateway  │  Confidence: HIGH                       │  │
│  │  Alerts: 5 (2 suppressed)  │  Services: 5                            │  │
│  │  [View All Alerts] [Create Incident] [Close Cluster]                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.7 Alert Rule Iteration (V87)

#### 6.7.1 Alert Rules Overview

| Rule ID | Name | Type | Status | Priority | Threshold |
|---------|------|------|--------|----------|-----------|
| AL-001 | High CPU Usage | Metric threshold | FROZEN (V86) | P2 | >80% for 5min |
| AL-002 | High Memory Usage | Metric threshold | FROZEN (V86) | P2 | >85% for 5min |
| AL-003 | High Error Rate | Metric threshold | FROZEN (V86) | P1 | >1% for 3min |
| AL-004 | Service Unhealthy | Health check | FROZEN (V86) | P1 | <50% healthy pods |
| AL-005 | High Latency P99 | Metric threshold | FROZEN (V86) | P2 | >500ms for 5min |
| AL-006 | Disk Space Low | Metric threshold | FROZEN (V86) | P2 | >80% for 10min |
| AL-007 | Database Connection Pool | Metric threshold | FROZEN (V86) | P1 | >90% for 3min |
| AL-008 | Network Packet Loss | Metric threshold | FROZEN (V86) | P1 | >0.01% for 1min |
| IE-AL-001 | Three-Level Incident Alert | Composite | FROZEN (V86) | P1 | 3-level cascade |
| **AL-V87-001** | **Correlated Alert Storm** | **Correlation** | **NEW (V87)** | **P1** | **≥5 correlated alerts in 60s** |
| **AL-V87-002** | **Anomaly-Driven Alert** | **AI-driven** | **NEW (V87)** | **P2** | **Anomaly score ≥0.70** |
| **AL-V87-003** | **Capacity Exceeded** | **Prediction** | **NEW (V87)** | **P2** | **Projected breach ≤24h** |

#### 6.7.2 New Alert Rule Definitions

```json
// AL-V87-001: Correlated Alert Storm
{
  "rule_id": "AL-V87-001",
  "name": "Correlated Alert Storm",
  "description": "Detects bursts of correlated alerts indicating cascading failures",
  "type": "correlation",
  "priority": "P1",
  "enabled": true,
  "correlation": {
    "min_alerts": 5,
    "time_window_seconds": 60,
    "min_correlation_score": 0.80,
    "require_same_cluster": false
  },
  "suppression": {
    "silence_period_seconds": 300,
    "group_by": ["cluster_id", "service_id"],
    "auto_suppress": true
  },
  "notification": {
    "channels": ["pagerduty", "slack", "email"],
    "escalation": {
      "after_minutes": 5,
      "escalate_to": "oncall-lead"
    }
  },
  "root_cause_inference": {
    "enabled": true,
    "min_confidence": "HIGH"
  }
}

// AL-V87-002: Anomaly-Driven Alert
{
  "rule_id": "AL-V87-002",
  "name": "Anomaly-Driven Alert",
  "description": "Alerts based on AI anomaly detection scores from P-001",
  "type": "ai_anomaly",
  "priority": "P2",
  "enabled": true,
  "anomaly": {
    "min_score": 0.70,
    "min_severity": "P2_HIGH",
    "require_direction": false,
    "model": "ensemble"
  },
  "suppression": {
    "silence_period_seconds": 1800,
    "group_by": ["service_id", "metric"],
    "feedback_required": false
  }
}

// AL-V87-003: Capacity Exceeded Prediction
{
  "rule_id": "AL-V87-003",
  "name": "Capacity Exceeded Prediction",
  "description": "Alerts when capacity projection exceeds threshold within 24h",
  "type": "prediction",
  "priority": "P2",
  "enabled": true,
  "prediction": {
    "horizon_hours": 24,
    "min_confidence": 0.80,
    "resources": ["cpu", "memory", "qps"],
    "threshold_pct": 85
  },
  "notification": {
    "channels": ["slack", "email"],
    "include_recommendation": true
  }
}
```

### 6.8 API Contract

#### 6.8.1 Cluster Query API

```json
// GET /api/v87/correlation/clusters
{
  "request": {
    "time_range": {
      "from": "2025-01-15T13:00:00Z",
      "to": "2025-01-15T14:00:00Z"
    },
    "min_correlation_score": 0.80,
    "status": "active",
    "page": 1,
    "page_size": 20
  },
  "response": {
    "status": "OK",
    "clusters": [
      {
        "cluster_id": "C-012",
        "created_at": "2025-01-15T14:32:00Z",
        "status": "active",
        "alert_count": 5,
        "correlation_score": 0.91,
        "noise_reduction_pct": 60.0,
        "root_cause": {
          "service_id": "dshb-gateway-001",
          "confidence": "HIGH",
          "score": 0.92,
          "rationale": "Earliest alert in cluster with highest dependency fan-out"
        },
        "alerts": [
          {
            "alert_id": "alert-001",
            "event_type": "ALERT",         // HERMES V87
            "priority": "P1",                // HERMES V87
            "trace_id": "tr-abc123",         // HERMES V87
            "batch_id": "batch-20250115-012", // HERMES V87
            "retry_count": 0,                // HERMES V87
            "timestamp": "2025-01-15T14:32:00Z",
            "service_id": "dshb-gateway-001",
            "metric": "error_rate",
            "value": 0.035,
            "threshold": 0.01,
            "suppressed": false
          }
        ]
      }
    ],
    "summary": {
      "total_clusters": 18,
      "active_clusters": 3,
      "total_alerts": 142,
      "suppressed_alerts": 37,
      "storm_count": 3,
      "avg_correlation_score": 0.82,
      "root_cause_accuracy_pct": 83.5
    }
  }
}
```

#### 6.8.2 Suppression Rules API

```json
// GET /api/v87/correlation/suppression-rules
{
  "response": {
    "rules": [
      {
        "rule_id": "suppression-001",
        "name": "Error rate silence for dshb-gateway",
        "type": "silence",
        "enabled": true,
        "match": {
          "service_id": "dshb-gateway-001",
          "metric": "error_rate",
          "priority": ["P1", "P2"]
        },
        "silence_period_seconds": 1800,
        "created_at": "2025-01-15T14:32:00Z",
        "expires_at": "2025-01-15T15:02:00Z",
        "suppressed_count": 8,
        "created_by": "auto-storm"
      }
    ]
  }
}

// POST /api/v87/correlation/suppression-rules (create/edit)
{
  "request": {
    "rule_id": "suppression-001",
    "enabled": true,
    "silence_period_seconds": 1800
  }
}
```

#### 6.8.3 Correlation Matrix API

```json
// GET /api/v87/correlation/matrix
{
  "response": {
    "services": ["dshb-gateway", "dshb-auth", "dshb-user", "dshb-order", "dshb-inventory"],
    "matrix": [
      [1.00, 0.92, 0.85, 0.72, 0.88],
      [0.92, 1.00, 0.78, 0.65, 0.71],
      [0.85, 0.78, 1.00, 0.82, 0.79],
      [0.72, 0.65, 0.82, 1.00, 0.88],
      [0.88, 0.71, 0.79, 0.88, 1.00]
    ],
    "threshold": 0.80,
    "computed_at": "2025-01-15T14:35:00Z"
  }
}
```

### 6.9 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Correlation threshold | ≥0.80 | Configured parameter |
| Suppression delay (P99) | ≤5s | End-to-end from alert to suppression |
| Root cause accuracy | ≥80% | Human validation feedback |
| Clustering latency | ≤2s | DBSCAN on 1000 alerts |
| Panel load time (P99) | ≤2s | Lighthouse |
| API response (P99) | ≤500ms | API gateway metrics |

### 6.10 Test Plan

| Test Category | Test Cases | Tools |
|--------------|------------|-------|
| Unit Tests | DBSCAN clustering, correlation scoring, suppression engine | Jest |
| Integration Tests | API contracts, alert ingestion, suppression workflow | Supertest |
| Performance Tests | 1000 alert clustering, storm detection latency | Custom |
| Accuracy Tests | Root cause accuracy ≥80% on labeled dataset | Backtesting |
| Suppression Tests | Suppression delay ≤5s P99, storm detection | Load tests |

---

## 7. V87-P-005: Chaos Engineering Automation Panel (Design Only)

> **⚠️ DEFERRED TO PHASE03**: This panel is in design-only status for Phase02. No implementation work is performed in Phase02. The design document below serves as the blueprint for Phase03 development.

### 7.1 Panel Metadata

| Attribute | Value |
|-----------|-------|
| **Panel ID** | V87-P-005 |
| **Panel Name** | 混沌工程自动化 / Chaos Engineering Automation |
| **Priority** | P2 (Important) |
| **Status** | DEFERRED to Phase03 |
| **Estimated Effort (Phase03)** | 30 person-days (implementation) |
| **Design Owner** | SRE Platform Team |
| **Integration Status** | Design Only — No Phase02 Implementation |

### 7.2 Design Document

#### 7.2.1 Experiment Orchestration (YAML DSL)

```yaml
# chaos_experiment.yaml
# V87-P-005: Chaos Engineering Experiment Definition
apiVersion: chaos.v87
kind: Experiment
metadata:
  name: gateway-latency-stress
  namespace: production
  owner: sre-platform-team
  description: "Test gateway latency under simulated database slowdown"
  priority: P1
  approval_required: true

spec:
  # Target services
  targets:
    - service: dshb-gateway-001
      namespace: production
      strategy: all_instances
    - service: dshb-auth-001
      namespace: production
      strategy: 50_percent

  # Experiment phases
  phases:
    - name: baseline
      duration: 300s  # 5 minutes
      actions:
        - type: observe
          metrics:
            - service: dshb-gateway-001
              metric: latency_p99
              threshold_warning: 100ms
              threshold_critical: 200ms
            - service: dshb-auth-001
              metric: latency_p99
              threshold_warning: 50ms
              threshold_critical: 100ms

    - name: injection
      duration: 600s  # 10 minutes
      actions:
        - type: latency_injection
          target: dshb-auth-001
          endpoint: /auth/token
          latency_ms: 500
          probability: 0.3  # 30% of requests
          gradual_ramp: true
          ramp_duration: 60s

    - name: recovery
      duration: 300s  # 5 minutes
      actions:
        - type: observe
          metrics:
            - service: dshb-gateway-001
              metric: latency_p99
              expect_recovery_within: 120s

  # Smart injection timing
  smart_timing:
    enabled: true
    constraints:
      - avoid_business_hours: true
      - avoid_deploy_window: true
      - avoid_peak_traffic: true
      - max_concurrent_experiments: 2
      - minimum_cool_down: 3600s  # 1 hour between experiments
    preferred_windows:
      - day_of_week: [Mon, Tue, Wed, Thu]
        hours: [22, 23, 0, 1, 2, 3]  # Off-peak hours

  # SLO impact evaluation
  slo_evaluation:
    enabled: true
    slo_targets:
      - metric: latency_p99
        service: dshb-gateway-001
        target: 200ms
        window: 30d
      - metric: availability
        service: dshb-gateway-001
        target: 99.95%
        window: 30d
      - metric: error_rate
        service: dshb-gateway-001
        target: 0.1%
        window: 30d
    evaluation_criteria:
      - error_budget_remaining: 0.10  # 10% budget remaining
      - max_breach_duration: 300s
      - max_breach_count: 2

  # Auto report generation
  reporting:
    enabled: true
    format: [pdf, json]
    include:
      - experiment_timeline
      - metric_anomalies
      - slo_impact_summary
      - fault_propagation_map
      - recommendations
    send_to:
      - email: sre-team@company.com
      - slack: "#sre-chaos-reports"
      - dashboard: V87-P-005

  # Safety controls
  safety:
    max_experiment_duration: 3600s  # 1 hour max
    auto_abort:
      - condition: "error_rate > 5%"
        action: abort
      - condition: "latency_p99 > 1000ms"
        action: abort
      - condition: "availability < 99%"
        action: abort
    manual_abort: true
    require_dual_approval: true  # 2 approvers required
```

#### 7.2.2 System Architecture (Design)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              V87-P-005 DESIGN ARCHITECTURE (Phase03 Implementation)          │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    CONTROL PLANE                                        │  │
│  │                                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ Experiment   │  │ Smart Timing │  │ SLO          │                │  │
│  │  │ Orchestrator │  │ Scheduler    │  │ Evaluator    │                │  │
│  │  │              │  │              │  │              │                │  │
│  │  │ YAML DSL     │  │ Business     │  │ Budget       │                │  │
│  │  │ Parser       │  │ Cal. Aware   │  │ Tracking     │                │  │
│  │  │              │  │              │  │              │                │  │
│  │  │ Approval     │  │ Peak         │  │ Breach       │                │  │
│  │  │ Workflow     │  │ Detection    │  │ Detection    │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    DATA PLANE                                           │  │
│  │                                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ Injection    │  │ Metric       │  │ Report       │                │  │
│  │  │ Engine       │  │ Collector    │  │ Generator    │                │  │
│  │  │              │  │              │  │              │                │  │
│  │  │ Network      │  │ Real-time    │  │ PDF          │                │  │
│  │  │ CPU/Mem      │  │ Streaming    │  │ JSON         │                │  │
│  │  │ Disk I/O     │  │              │  │ Dashboard    │                │  │
│  │  │ Load Gen.    │  │              │  │              │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    SAFETY PLANE                                         │  │
│  │                                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ Abort        │  │ Blast Radius │  │ Audit Trail  │                │  │
│  │  │ Controller   │  │ Limiter      │  │              │                │  │
│  │  │              │  │              │  │              │                │  │
│  │  │ Auto-abort   │  │ Scope Limit  │  │ Full Log     │                │  │
│  │  │ Manual Abort │  │ Time Limit   │  │ Approval     │                │  │
│  │  │ Dual Approv. │  │ Resource     │  │ History      │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.2.3 Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Production outage during experiment** | Medium | Critical | Dual approval, blast radius limiter, auto-abort on SLO breach, off-peak scheduling |
| **Insufficient monitoring during experiment** | Low | High | Pre-experiment validation checklist, minimum 5-min baseline observation |
| **Excessive blast radius** | Medium | High | Scope limiter: max 50% of instances per experiment, namespace isolation |
| **User-visible degradation** | Medium | High | Peak traffic avoidance, gradual ramp injection, error budget check |
| **Incomplete rollback** | Low | Critical | Pre-configured rollback procedures, automated recovery phase |
| **False positive experiment results** | Medium | Medium | 30-day SLO window, statistical significance testing (p<0.05) |

#### 7.2.4 Future Integration Plan (Phase03)

| Phase03 Milestone | Deliverable | Dependencies |
|-------------------|-------------|-------------|
| Phase03-M1: Engine Core | Experiment orchestrator, YAML DSL parser | V87-P-001, V87-P-004 (completed) |
| Phase03-M2: Injection Engine | Network, CPU, memory, disk injection | Chaos Mesh / Litmus integration |
| Phase03-M3: Smart Timing | Business calendar integration, peak detection | DSHB scheduling API |
| Phase03-M4: SLO Evaluation | Budget tracking, breach detection | V87-P-003 (capacity planning) |
| Phase03-M5: Reporting | Auto report generation, dashboard integration | V87-P-001, V87-P-004 |
| Phase03-M6: Safety | Abort controller, audit trail | HERMES audit service |
| Phase03-M7: UI | Experiment dashboard, visualization | All Phase03-M1 through M6 |
<!-- APPEND_HERE -->



