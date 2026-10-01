# V86 Rule Engine Operations Monitoring Metric Specification

**Task:** DSHB_V86_RULE_ENGINE_FULL_DATASET_REPLAY_AND_PROD_BUNDLE_BUILD  
**Deliverable:** T2.5 — Monitoring Metrics  
**Branch:** feature/v85-chart-template  
**Base Commit:** 68517fb  
**Aligned With:** V86 E Backend Task API (commit bcd64dd), DSHE Alias Engine (commit d8e44a9)  

---

## 1. Metric Overview

This specification defines the complete set of metrics exposed by the V86 rule engine for production monitoring. Metrics are aligned with the V86 backend monitoring conventions and the DSHE alias engine's metric patterns.

### 1.1 Metric Categories

| Category | Prefix | Count | Description |
|----------|--------|-------|-------------|
| System Health | `v86_system_` | 6 | Engine status, version, uptime |
| Throughput | `v86_throughput_` | 8 | Request rates, batch sizes |
| Latency | `v86_latency_` | 12 | p50/p95/p99/max per endpoint |
| Rule Hits | `v86_rule_` | 24 | Per-rule hit counts and FP rates |
| Errors | `v86_error_` | 10 | Error code counts by type |
| Queue | `v86_queue_` | 4 | Queue depth, wait time, rejections |
| Data Quality | `v86_data_` | 4 | DATA_MISSING, validation failures |
| Memory | `v86_memory_` | 4 | Memory usage per component |

### 1.2 Naming Convention

```
{namespace}_{domain}_{metric}_{unit}

Examples:
  v86_throughput_evaluate_total      (counter)
  v86_latency_p95_evaluate_ms        (gauge)
  v86_rule_hit_BL020_total           (counter)
  v86_error_BAD_PAYLOAD_total        (counter)
  v86_queue_depth                    (gauge)
```

---

## 2. System Health Metrics

### 2.1 Health Status

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_system_health` | gauge | - | 1.0 = healthy, 0.0 = unhealthy |
| `v86_system_ready` | gauge | - | 1.0 = accepting requests, 0.0 = draining |
| `v86_system_uptime_seconds` | counter | - | Total uptime in seconds |
| `v86_system_version` | gauge | version | Version number (constant 1.0) |
| `v86_system_engine_loaded` | gauge | engine_type | 1.0 if engine loaded (rule=18, alias=31) |
| `v86_system_engine_rules_total` | gauge | - | Total rules loaded (18) |

### 2.2 Health Endpoint

```
GET /health
Response:
{
  "status": "healthy",
  "version": "v86.1-prod",
  "rules": 18,
  "p0_rules": 6,
  "p1_rules": 12,
  "alias_engine": "f3+f4",
  "uptime_sec": 3600,
  "memory_mb": 72.5,
  "queue_depth": 0
}
```

---

## 3. Throughput Metrics

### 3.1 Evaluation Throughput

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_throughput_evaluate_total` | counter | - | Total evaluations processed |
| `v86_throughput_evaluate_blocked_total` | counter | - | Total BLOCKED results |
| `v86_throughput_evaluate_passed_total` | counter | - | Total PASSED results |
| `v86_throughput_evaluate_data_missing_total` | counter | - | Total DATA_MISSING results |
| `v86_throughput_evaluate_not_applicable_total` | counter | - | Total NOT_APPLICABLE results |
| `v86_throughput_evaluate_error_total` | counter | error_code | Total errors by error code |
| `v86_throughput_evaluate_rate_per_sec` | gauge | - | Current evaluations/sec |
| `v86_throughput_evaluate_batch_size_avg` | gauge | - | Average batch size (batch endpoint) |

### 3.2 Batch Throughput

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_throughput_batch_total` | counter | - | Total batch requests |
| `v86_throughput_batch_items_total` | counter | - | Total items in batches |
| `v86_throughput_batch_blocked_total` | counter | - | Total blocked items in batches |
| `v86_throughput_batch_passed_total` | counter | - | Total passed items in batches |

### 3.3 Prometheus Export (throughput)

```prometheus
# HELP v86_throughput_evaluate_total Total evaluations processed
# TYPE v86_throughput_evaluate_total counter
v86_throughput_evaluate_total 5442.0

# HELP v86_throughput_evaluate_blocked_total Total BLOCKED results
# TYPE v86_throughput_evaluate_blocked_total counter
v86_throughput_evaluate_blocked_total 7.0

# HELP v86_throughput_evaluate_passed_total Total PASSED results
# TYPE v86_throughput_evaluate_passed_total counter
v86_throughput_evaluate_passed_total 5280.0

# HELP v86_throughput_evaluate_data_missing_total Total DATA_MISSING results
# TYPE v86_throughput_evaluate_data_missing_total counter
v86_throughput_evaluate_data_missing_total 155.0

# HELP v86_throughput_evaluate_rate_per_sec Current evaluations per second
# TYPE v86_throughput_evaluate_rate_per_sec gauge
v86_throughput_evaluate_rate_per_sec 4173.0
```

---

## 4. Latency Metrics

### 4.1 Single Evaluation Latency

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_latency_evaluate_p50_ms` | gauge | - | P50 latency in ms |
| `v86_latency_evaluate_p95_ms` | gauge | - | P95 latency in ms |
| `v86_latency_evaluate_p99_ms` | gauge | - | P99 latency in ms |
| `v86_latency_evaluate_max_ms` | gauge | - | Max latency in ms |
| `v86_latency_evaluate_avg_ms` | gauge | - | Average latency in ms |
| `v86_latency_evaluate_total_seconds` | histogram | - | Histogram of evaluation latencies |
| `v86_latency_evaluate_sum_seconds` | counter | - | Sum of evaluation latencies |
| `v86_latency_evaluate_count` | counter | - | Count of evaluations for latency |

### 4.2 Alias Resolution Latency

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_latency_alias_resolve_p50_ms` | gauge | - | P50 alias resolution latency |
| `v86_latency_alias_resolve_p95_ms` | gauge | - | P95 alias resolution latency |
| `v86_latency_alias_resolve_p99_ms` | gauge | - | P99 alias resolution latency |
| `v86_latency_alias_resolve_total_seconds` | histogram | - | Alias resolution latency histogram |

### 4.3 Batch Latency

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_latency_batch_p50_ms` | gauge | - | P50 batch latency |
| `v86_latency_batch_p95_ms` | gauge | - | P95 batch latency |
| `v86_latency_batch_avg_ms` | gauge | - | Average batch latency |

### 4.4 Latency Histogram (Prometheus)

```prometheus
# HELP v86_latency_evaluate_total_seconds Distribution of evaluation latencies
# TYPE v86_latency_evaluate_total_seconds histogram
v86_latency_evaluate_total_seconds_bucket{le="0.01"} 4200.0
v86_latency_evaluate_total_seconds_bucket{le="0.05"} 5200.0
v86_latency_evaluate_total_seconds_bucket{le="0.1"} 5400.0
v86_latency_evaluate_total_seconds_bucket{le="0.5"} 5442.0
v86_latency_evaluate_total_seconds_bucket{le="1.0"} 5442.0
v86_latency_evaluate_total_seconds_bucket{le="5.0"} 5442.0
v86_latency_evaluate_total_seconds_bucket{le="+Inf"} 5442.0
v86_latency_evaluate_total_seconds_sum 1246.2
v86_latency_evaluate_total_seconds_count 5442.0
```

---

## 5. Rule Hit Metrics

### 5.1 Per-Rule Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_rule_hit_total` | counter | rule_id, severity | Total hits per rule |
| `v86_rule_hit_blocked_total` | counter | rule_id | Total BLOCKED per rule |
| `v86_rule_fp_total` | counter | rule_id | Total false positives per rule |
| `v86_rule_fp_rate` | gauge | rule_id | FP rate per rule (0.0-1.0) |
| `v86_rule_avg_latency_ms` | gauge | rule_id | Average latency per rule |
| `v86_rule_last_hit_timestamp` | gauge | rule_id | Unix timestamp of last hit |
| `v86_rule_status` | gauge | rule_id | 1.0 = active, 0.0 = paused |

### 5.2 Per-Rule Metric Examples

```prometheus
# P0 Rules
v86_rule_hit_total{rule_id="BL-009a",severity="P0"} 1.0
v86_rule_hit_total{rule_id="BL-026",severity="P0"} 0.0
v86_rule_hit_total{rule_id="BL-012",severity="P0"} 0.0
v86_rule_hit_total{rule_id="BL-001",severity="P0"} 0.0
v86_rule_hit_total{rule_id="BL-002",severity="P0"} 0.0
v86_rule_hit_total{rule_id="BL-003",severity="P0"} 0.0

# P1 Rules
v86_rule_hit_total{rule_id="BL-020",severity="P1"} 2.0
v86_rule_hit_total{rule_id="BL-021",severity="P1"} 1.0
v86_rule_hit_total{rule_id="BL-022",severity="P1"} 1.0
v86_rule_hit_total{rule_id="BL-027",severity="P1"} 1.0
v86_rule_hit_total{rule_id="BL-028",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-029",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-030",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-031",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-032",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-033",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-034",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-035",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-036",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-037",severity="P1"} 0.0
v86_rule_hit_total{rule_id="BL-038",severity="P1"} 1.0

# Rule Status
v86_rule_status{rule_id="BL-009a"} 1.0
v86_rule_status{rule_id="BL-020"} 1.0
v86_rule_status{rule_id="BL-022"} 1.0
```

### 5.3 Rule FP Rate Calculation

```
v86_rule_fp_rate = v86_rule_fp_total / max(1, v86_rule_hit_total)

Example: BL-020 hit 2 times, 0 FP → rate = 0.0/2.0 = 0.0
Example: BL-022 hit 1 time, 0 FP → rate = 0.0/1.0 = 0.0
```

---

## 6. Error Metrics

### 6.1 Error Code Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_error_total` | counter | error_code | Total errors by error code |
| `v86_error_rate_per_sec` | gauge | - | Current error rate |
| `v86_error_last_timestamp` | gauge | - | Last error timestamp |

### 6.2 Error Code Enumeration

| Error Code | HTTP Status | Retryable | Metric Name |
|------------|------------|-----------|-------------|
| OK | 200 | - | (no error) |
| RULE_ENGINE_LOAD_FAILED | 500 | Yes | `v86_error_RULE_ENGINE_LOAD_FAILED_total` |
| RULE_NOT_FOUND | 404 | No | `v86_error_RULE_NOT_FOUND_total` |
| RULE_CONFLICT | 409 | No | `v86_error_RULE_CONFLICT_total` |
| PATTERN_EMPTY | 400 | No | `v86_error_PATTERN_EMPTY_total` |
| VARIETY_DETECT_FAILED | 500 | Yes | `v86_error_VARIETY_DETECT_FAILED_total` |
| BIDIRECTIONAL_CHECK_ERROR | 500 | Yes | `v86_error_BIDIRECTIONAL_CHECK_ERROR_total` |
| EMPTY_INDICATOR | 400 | No | `v86_error_EMPTY_INDICATOR_total` |
| EMPTY_MATCHED | 400 | No | `v86_error_EMPTY_MATCHED_total` |
| INDICATOR_TOO_LONG | 400 | No | `v86_error_INDICATOR_TOO_LONG_total` |
| MATCHED_TOO_LONG | 400 | No | `v86_error_MATCHED_TOO_LONG_total` |
| INVALID_ALIAS_FORMAT | 400 | No | `v86_error_INVALID_ALIAS_FORMAT_total` |
| ALIAS_MAP_NOT_FOUND | 404 | No | `v86_error_ALIAS_MAP_NOT_FOUND_total` |
| ALIAS_MAP_CORRUPT | 500 | Yes | `v86_error_ALIAS_MAP_CORRUPT_total` |
| CSV_PARSE_ERROR | 400 | No | `v86_error_CSV_PARSE_ERROR_total` |
| JSON_PARSE_ERROR | 400 | No | `v86_error_JSON_PARSE_ERROR_total` |
| TIMEOUT | 504 | Yes | `v86_error_TIMEOUT_total` |
| INTERNAL_ERROR | 500 | Yes | `v86_error_INTERNAL_ERROR_total` |
| DATA_MISSING | 200 | No | `v86_error_DATA_MISSING_total` (special status) |

### 6.3 Error Metric Examples

```prometheus
# No errors during full replay
v86_error_total{error_code="EMPTY_INDICATOR"} 0.0
v86_error_total{error_code="EMPTY_MATCHED"} 0.0
v86_error_total{error_code="RULE_ENGINE_LOAD_FAILED"} 0.0
v86_error_total{error_code="INTERNAL_ERROR"} 0.0
v86_error_total{error_code="TIMEOUT"} 0.0
v86_error_total{error_code="DATA_MISSING"} 155.0
v86_error_rate_per_sec 0.0
```

---

## 7. Queue Metrics

### 7.1 Queue Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_queue_depth` | gauge | - | Current queue depth |
| `v86_queue_max_depth` | gauge | - | Maximum queue depth ever reached |
| `v86_queue_wait_time_avg_ms` | gauge | - | Average queue wait time |
| `v86_queue_wait_time_max_ms` | gauge | - | Maximum queue wait time |
| `v86_queue_rejected_total` | counter | - | Total requests rejected due to queue full |
| `v86_queue_accepted_total` | counter | - | Total requests accepted |

### 7.2 Queue Thresholds (Aligned with Resource Estimate)

| Queue Depth | Status | Action |
|-------------|--------|--------|
| 0-100 | GREEN | Normal |
| 101-500 | YELLOW | Monitor |
| 501-2000 | ORANGE | Scale up |
| 2001-5000 | RED | Emergency |
| 5000+ | CRITICAL | Reject requests |

### 7.3 Queue Metric Examples

```prometheus
# Normal operation
v86_queue_depth 0.0
v86_queue_max_depth 12.0
v86_queue_wait_time_avg_ms 0.5
v86_queue_wait_time_max_ms 2.1
v86_queue_rejected_total 0.0
v86_queue_accepted_total 5442.0
```

---

## 8. Data Quality Metrics

### 8.1 Data Quality

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_data_missing_total` | counter | - | Total DATA_MISSING responses |
| `v86_data_validation_failures_total` | counter | field | Validation failures by field |
| `v86_data_nfkc_applied_total` | counter | - | NFKC normalizations applied |
| `v86_data_avg_indicator_length` | gauge | - | Average indicator_name length |
| `v86_data_avg_matched_length` | gauge | - | Average matched_name length |

### 8.2 Data Quality Examples

```prometheus
v86_data_missing_total 155.0
v86_data_validation_failures_total{field="indicator_name"} 0.0
v86_data_validation_failures_total{field="matched_name"} 0.0
v86_data_nfkc_applied_total 5442.0
v86_data_avg_indicator_length 18.5
v86_data_avg_matched_length 22.3
```

---

## 9. Memory Metrics

### 9.1 Memory Usage

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `v86_memory_rule_engine_mb` | gauge | - | Rule engine memory (MB) |
| `v86_memory_alias_engine_mb` | gauge | - | Alias engine memory (MB) |
| `v86_memory_total_mb` | gauge | - | Total process memory (MB) |
| `v86_memory_gc_cycles_total` | counter | - | GC cycles completed |
| `v86_memory_gc_time_total_ms` | counter | - | Total GC time (ms) |

### 9.2 Memory Examples

```prometheus
v86_memory_rule_engine_mb 5.2
v86_memory_alias_engine_mb 35.8
v86_memory_total_mb 72.5
v86_memory_gc_cycles_total 48.0
v86_memory_gc_time_total_ms 1245.0
```

---

## 10. Prometheus Export Configuration

### 10.1 Full /metrics Endpoint

```python
#!/usr/bin/env python3
"""
Prometheus metrics endpoint for V86 rule engine.
Usage: from metrics_exporter import MetricsExporter; exporter = MetricsExporter()
"""

class MetricsExporter:
    """Prometheus metrics exporter for V86 rule engine."""
    
    def __init__(self):
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
    
    def inc_counter(self, name, labels=None, value=1.0):
        """Increment a counter metric."""
        key = f"{name}{labels or ''}"
        self.counters[key] = self.counters.get(key, 0) + value
    
    def set_gauge(self, name, value, labels=None):
        """Set a gauge metric."""
        key = f"{name}{labels or ''}"
        self.gauges[key] = value
    
    def add_histogram(self, name, value, labels=None):
        """Add a value to a histogram."""
        key = f"{name}{labels or ''}"
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
    
    def render(self) -> str:
        """Render all metrics in Prometheus text format."""
        lines = []
        
        # Counters
        for key, value in sorted(self.counters.items()):
            name = key.split('{')[0]
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in sorted(self.gauges.items()):
            name = key.split('{')[0]
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms
        for key, values in sorted(self.histograms.items()):
            name = key.split('{')[0]
            lines.append(f"# TYPE {name} histogram")
            if values:
                lines.append(f"{key}_sum {sum(values)}")
                lines.append(f"{key}_count {len(values)}")
        
        return "\n".join(lines) + "\n"


def create_default_exporter() -> MetricsExporter:
    """Create a metrics exporter with default V86 metrics."""
    exporter = MetricsExporter()
    
    # System health
    exporter.set_gauge("v86_system_health", 1.0)
    exporter.set_gauge("v86_system_ready", 1.0)
    exporter.set_gauge("v86_system_engine_rules_total", 18)
    
    # Default zero values for all error codes
    for code in ["RULE_ENGINE_LOAD_FAILED", "RULE_NOT_FOUND", "RULE_CONFLICT",
                 "PATTERN_EMPTY", "VARIETY_DETECT_FAILED", "BIDIRECTIONAL_CHECK_ERROR",
                 "EMPTY_INDICATOR", "EMPTY_MATCHED", "INDICATOR_TOO_LONG",
                 "MATCHED_TOO_LONG", "INVALID_ALIAS_FORMAT", "ALIAS_MAP_NOT_FOUND",
                 "ALIAS_MAP_CORRUPT", "CSV_PARSE_ERROR", "JSON_PARSE_ERROR",
                 "TIMEOUT", "INTERNAL_ERROR", "DATA_MISSING"]:
        exporter.inc_counter(f"v86_error_total{{error_code=\"{code}\"}}", value=0)
    
    # Default rule hit metrics (18 rules)
    for rule_id in ["BL-009a", "BL-026", "BL-012", "BL-001", "BL-002", "BL-003",
                    "BL-020", "BL-021", "BL-022", "BL-027", "BL-028", "BL-029",
                    "BL-030", "BL-031", "BL-032", "BL-033", "BL-034", "BL-035",
                    "BL-036", "BL-037", "BL-038"]:
        exporter.inc_counter(f"v86_rule_hit_total{{rule_id=\"{rule_id}\"}}", value=0)
        exporter.set_gauge(f"v86_rule_status{{rule_id=\"{rule_id}\"}}", 1.0)
    
    return exporter
```

### 10.2 Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "V86 Rule Engine Production Monitoring",
    "uid": "v86-rule-engine-prod",
    "tags": ["v86", "rule-engine", "production"],
    "timezone": "Asia/Shanghai",
    "panels": [
      {
        "title": "Throughput (requests/sec)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(v86_throughput_evaluate_total[5m])",
            "legendFormat": "evaluations/sec"
          }
        ]
      },
      {
        "title": "Latency (p50/p95/p99)",
        "type": "timeseries",
        "targets": [
          {"expr": "v86_latency_evaluate_p50_ms", "legendFormat": "p50"},
          {"expr": "v86_latency_evaluate_p95_ms", "legendFormat": "p95"},
          {"expr": "v86_latency_evaluate_p99_ms", "legendFormat": "p99"}
        ]
      },
      {
        "title": "Rule Hits by Rule ID",
        "type": "table",
        "targets": [
          {
            "expr": "v86_rule_hit_total",
            "legendFormat": "{{rule_id}}"
          }
        ]
      },
      {
        "title": "Error Rate by Code",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(v86_error_total[5m])",
            "legendFormat": "{{error_code}}"
          }
        ]
      },
      {
        "title": "Queue Depth",
        "type": "timeseries",
        "targets": [
          {"expr": "v86_queue_depth", "legendFormat": "queue_depth"}
        ]
      },
      {
        "title": "FP Rate by Rule",
        "type": "table",
        "targets": [
          {
            "expr": "v86_rule_fp_total / max(1, v86_rule_hit_total)",
            "legendFormat": "{{rule_id}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "timeseries",
        "targets": [
          {"expr": "v86_memory_total_mb", "legendFormat": "total_mb"},
          {"expr": "v86_memory_rule_engine_mb", "legendFormat": "rule_engine"},
          {"expr": "v86_memory_alias_engine_mb", "legendFormat": "alias_engine"}
        ]
      },
      {
        "title": "DATA_MISSING Count",
        "type": "stat",
        "targets": [
          {"expr": "v86_data_missing_total", "legendFormat": "data_missing"}
        ]
      }
    ]
  }
}
```

---

## 11. Alert Rules Configuration

### 11.1 Critical Alerts

```yaml
# prometheus/rules/v86-critical-alerts.yaml
groups:
  - name: v86-critical-alerts
    rules:
      # P0: Engine down
      - alert: V86EngineDown
        expr: v86_system_health == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "V86 Rule Engine is DOWN"
          description: "Engine health check failed for 30 seconds"

      # P0: P95 latency critical
      - alert: V86LatencyCritical
        expr: v86_latency_evaluate_p95_ms > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "V86 Rule Engine P95 latency critical"
          description: "P95 latency {{ $value }}ms exceeds 10ms for 2 minutes"

      # P0: High error rate
      - alert: V86ErrorRateCritical
        expr: rate(v86_error_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "V86 Rule Engine error rate critical"
          description: "Error rate {{ $value }}/sec exceeds 5% for 5 minutes"

      # P0: Queue critical
      - alert: V86QueueCritical
        expr: v86_queue_depth > 2000
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "V86 Rule Engine queue critical"
          description: "Queue depth {{ $value }} exceeds 2000"
```

### 11.2 Warning Alerts

```yaml
# prometheus/rules/v86-warning-alerts.yaml
groups:
  - name: v86-warning-alerts
    rules:
      # P1: P95 latency high
      - alert: V86LatencyHigh
        expr: v86_latency_evaluate_p95_ms > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine P95 latency high"
          description: "P95 latency {{ $value }}ms exceeds 5ms for 5 minutes"

      # P1: FP rate high
      - alert: V86FPHigh
        expr: (sum(v86_rule_fp_total) / max(1, sum(v86_rule_hit_total))) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine FP rate high"
          description: "FP rate {{ $value * 100 | printf \"%.2f\" }}% exceeds 5%"

      # P1: Memory high
      - alert: V86MemoryHigh
        expr: v86_memory_total_mb > 600
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine memory high"
          description: "Memory usage {{ $value }}MB exceeds 600MB"

      # P1: Queue high
      - alert: V86QueueHigh
        expr: v86_queue_depth > 500
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine queue high"
          description: "Queue depth {{ $value }} exceeds 500 for 2 minutes"
```

---

## 12. Backend API Alignment

### 12.1 Alignment with V86 E Backend Task API

| V86 Metric | Backend API Field | Alignment |
|------------|------------------|-----------|
| `v86_throughput_evaluate_total` | `task.total` | Total evaluations = task total |
| `v86_throughput_evaluate_blocked_total` | `result.blocked` | Blocked count aligned |
| `v86_latency_evaluate_p95_ms` | `metrics.latency.p95` | Latency aligned |
| `v86_error_total` | `error.code` | Error codes mapped |
| `v86_data_missing_total` | `result.data_missing` | DATA_MISSING aligned |
| `v86_rule_hit_total` | `metrics.rules.{id}.hits` | Per-rule hit count |

### 12.2 Alignment with DSHE Alias Engine

| V86 Metric | DSHE Metric | Alignment |
|------------|------------|-----------|
| `v86_latency_alias_resolve_p95_ms` | `alias_resolve_p95_ms` | Alias latency aligned |
| `v86_throughput_evaluate_total` | `total_tasks_processed` | Throughput aligned |
| `v86_error_TOTAL` | `error_count` | Error count aligned |
| `v86_memory_total_mb` | `process_resident_memory_bytes` | Memory aligned |

### 12.3 Backend Monitoring Integration

```python
# Example: Submit metrics to backend monitoring API
import json
import requests

def submit_metrics(metrics_dict, backend_url="http://localhost:8080"):
    """Submit V86 metrics to backend monitoring API."""
    payload = {
        "task_type": "v86_rule_engine_metrics",
        "version": "v86.1-prod",
        "metrics": metrics_dict,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    response = requests.post(
        f"{backend_url}/api/v1/monitoring/report",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json()
```

---

## 13. Metric Export API

### 13.1 Endpoints

| Endpoint | Method | Content-Type | Description |
|----------|--------|-------------|-------------|
| `/metrics` | GET | text/plain | Prometheus text format |
| `/metrics/json` | GET | application/json | JSON format |
| `/metrics/summary` | GET | application/json | Summary metrics |
| `/metrics/rules` | GET | application/json | Rule-specific metrics |
| `/metrics/latency` | GET | application/json | Latency distribution |
| `/metrics/errors` | GET | application/json | Error breakdown |

### 13.2 Metrics Summary Endpoint

```
GET /metrics/summary
Response:
{
  "total_evaluate": 5442,
  "blocked": 7,
  "passed": 5280,
  "data_missing": 155,
  "errors": 0,
  "throughput_per_sec": 4173.0,
  "p50_ms": 0.0,
  "p95_ms": 1.001,
  "p99_ms": 1.004,
  "fp_rate": 0.0,
  "queue_depth": 0,
  "memory_mb": 72.5,
  "uptime_sec": 3600,
  "timestamp": "2026-10-02T01:30:00Z"
}
```

---

## 14. Metric Collection Cadence

| Metric Type | Cadence | Description |
|-------------|---------|-------------|
| Counters | Incrementing | Count up only, never reset |
| Gauges | Real-time | Current value at query time |
| Histograms | Binned | Pre-defined bucket boundaries |
| Snapshots | Every 60s | Periodic metrics summary |

### 14.1 Recommended Scrape Interval

| Environment | Interval | Description |
|-------------|----------|-------------|
| Dev/Staging | 60s | Low frequency |
| Production | 15s | Standard monitoring |
| High-frequency | 5s | Real-time monitoring |

---

## 15. SLA / SLO Definitions

### 15.1 Service Level Objectives

| SLO | Target | Measurement |
|-----|--------|-------------|
| Availability | 99.9% | `(total_time - downtime) / total_time` |
| P95 Latency | < 5ms | `v86_latency_evaluate_p95_ms` |
| FP Rate | < 5% | `sum(v86_rule_fp_total) / sum(v86_rule_hit_total)` |
| Error Rate | < 1% | `rate(v86_error_total[5m]) / rate(v86_throughput_evaluate_total[5m])` |
| Queue Rejection | < 0.1% | `rate(v86_queue_rejected_total[5m]) / rate(v86_throughput_evaluate_total[5m])` |

### 15.2 SLI (Service Level Indicators)

| SLI | Metric | Unit |
|-----|--------|------|
| Availability | `v86_system_health` | 0.0-1.0 |
| Latency | `v86_latency_evaluate_p95_ms` | ms |
| FP Rate | `v86_rule_fp_rate` | 0.0-1.0 |
| Error Rate | `v86_error_rate_per_sec` | errors/sec |
| Throughput | `v86_throughput_evaluate_rate_per_sec` | requests/sec |

---

## 16. Dashboard Layout

### 16.1 Top Row (Status Overview)

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Engine Health   │ │ Throughput/sec  │ │ P95 Latency     │ │ Error Rate      │
│ (Gauge 1.0)     │ │ (Gauge 4173)    │ │ (Gauge 1.0ms)   │ │ (Gauge 0%)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 16.2 Middle Row (Detail)

```
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│ Throughput Over Time              │ │ Latency Distribution (p50/p95/p99)│
│ (Time series)                     │ │ (Time series)                     │
└───────────────────────────────────┘ └───────────────────────────────────┘
```

### 16.3 Bottom Row (Metrics)

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Rule Hits    │ │ FP Rate      │ │ Queue Depth  │ │ Memory Usage │
│ (Table)      │ │ (Table)      │ │ (Time series)│ │ (Time series)│
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 17. Summary

### 17.1 Metric Count by Category

| Category | Count | Type |
|----------|-------|------|
| System Health | 6 | Gauge, Counter |
| Throughput | 12 | Counter, Gauge |
| Latency | 14 | Gauge, Histogram, Counter |
| Rule Hits | 24 | Counter, Gauge |
| Errors | 18 | Counter, Gauge |
| Queue | 6 | Gauge, Counter |
| Data Quality | 5 | Counter, Gauge |
| Memory | 5 | Gauge, Counter |
| **Total** | **90** | **~90 unique metrics** |

### 17.2 Integration Checklist

| Item | Status | Notes |
|------|--------|-------|
| Prometheus export | Defined | `/metrics` endpoint |
| Grafana dashboard | Defined | 8 panels |
| Alert rules | Defined | 4 critical + 4 warning |
| Backend alignment | Defined | V86 E API + DSHE alias |
| SLO/SLA | Defined | 5 SLOs, 5 SLIs |
| Metric documentation | Complete | This document |

---

*Generated by DSHB Agent — v86.1-prod*