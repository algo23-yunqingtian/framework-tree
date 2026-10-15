# V88 Phase03 P1 — Engine-Side Threshold Monitor Design Spec
# 引擎侧阈值监控模块设计文档

> **TASK_ID**: V88_PHASE03_P1_ENGINE_THRESHOLD_MONITOR
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **DATE**: 2026-10-15
> **SCHEMA**: v88-p1.0.1
> **PURPOSE**: Engine-side threshold monitoring with 3-tier fuse thresholds.
>             Engine reads DSHB threshold config (JSON), monitors live metrics,
>             triggers fuse/warning logic.
> **STATUS**: V88_PHASE03_P1_ENGINE_THRESHOLD_MONITOR=READY

---

## 0. One-Line Summary

**EngineThresholdMonitor** is a standalone Python module that implements 3-tier
(4-level) threshold monitoring for the Phase03 rendering engine. It reads
DSHB-produced threshold JSON configs, checks 6 categories of engine metrics
(CPU, latency, error rate, noise rate, memory, indicator coverage), triggers
fuse/warning logic at the appropriate severity level, and returns comprehensive
evaluations with structured alerts. It does NOT modify the engine — it is a
plug-in monitoring layer that can be instantiated alongside any engine instance.

---

## 1. Architecture Overview

### 1.1 System Positioning

```
+------------------------------------------------------------------+
|                        DSHB (Data Layer)                         |
|  - Produces threshold configuration JSON                         |
|  - Outputs: threshold_config.json (GREEN/YELLOW/RED/BLUE tiers) |
+-----------------------------+------------------------------------+
                              | JSON config
                              v
+------------------------------------------------------------------+
|                   EngineThresholdMonitor                         |
|  - Loads thresholds from JSON config                             |
|  - check_cpu_baseline()       <- CPU metrics                     |
|  - check_latency()            <- Latency percentiles              |
|  - check_render_error_rate()  <- Error count / total             |
|  - check_noise_rate()         <- False positive count / total    |
|  - check_memory()             <- RSS in MB                       |
|  - check_indicator_coverage() <- Real charts / total charts      |
|  - evaluate()                 <- Comprehensive all-metrics check |
|  - trigger_fuse(level)        <- RED/BLUE fuse trigger           |
+-----------------------------+------------------------------------+
                              |
                    +---------+---------+
                    |                   |
                    v                   v
           +-------+-------+   +-------+-------+
           |  NodeBinding  |   | Alert/Log     |
           |  Engine       |   | System        |
           |  (unchanged)  |   |               |
           +---------------+   +---------------+
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Non-invasive** | Engine is NOT modified. Monitor is instantiated separately. |
| **Configurable** | All thresholds loaded from DSHB JSON config; no hardcoded values. |
| **Testable** | No external dependencies beyond Python stdlib; mock engine supported. |
| **ASCII-safe** | Uses [OK]/[!!]/[??]/[CRIT]/[FATAL] instead of emoji. |
| **UTF-8** | All files UTF-8 encoded. |
| **Fail-safe** | Missing thresholds default to GREEN (no false alerts). |

### 1.3 Module Structure

```
engine_threshold_monitor.py
|-- Constants (LEVEL_*, STATUS_*, FUSE_*, DEFAULT_THRESHOLDS)
|-- EngineThresholdMonitor class
|   |-- __init__()                    - Initialize with config path
|   |-- load_thresholds()             - Parse DSHB threshold JSON
|   |-- check_cpu_baseline()          - CPU metric check
|   |-- check_latency()               - Latency percentile check
|   |-- check_render_error_rate()     - Error rate check
|   |-- check_noise_rate()            - Noise rate check
|   |-- check_memory()                - Memory (RSS) check
|   |-- check_indicator_coverage()    - Coverage rate check
|   |-- evaluate()                    - Comprehensive evaluation
|   |-- get_alerts()                  - Return active alerts
|   |-- trigger_fuse()                - Trigger fuse at level
|   |-- reset_fuse()                  - Manual fuse reset
|   |-- get_fuse_state()              - Query fuse state
|   |-- get_statistics()              - Monitor statistics
|   |-- _determine_level()            - Value-to-level mapping
|   |-- _determine_inverted_level()   - Inverted metric mapping
|   |-- _create_alert()               - Alert dict factory
|   |-- _execute_fuse_action()        - Engine callback
|   |-- _generate_summary()           - Human-readable summary
|-- _demo_usage()                     - Demo/test function
```

---

## 2. 3-Tier Threshold Definition Table

### 2.1 Level Definitions

| Level | Color | Priority | Action | HERMEShf Mapping |
|:-----:|:-----:|:--------:|--------|:----------------:|
| **GREEN** | Normal | 0 | No action | N/A |
| **YELLOW** | Warning | 1 | Log + notify (email/daily report) | WARN |
| **RED** | Critical | 2 | Trigger fuse, stop rendering | CRIT |
| **BLUE** | Fatal | 3 | Emergency shutdown, escalate | CRIT+ESCALATED |

### 2.2 CPU Thresholds

| Metric | GREEN | YELLOW | RED | BLUE | Unit |
|--------|:-----:|:------:|:---:|:----:|:----:|
| process_level_pct | < 5.0 | 5.0 - 15.0 | 15.0 - 30.0 | > 30.0 | % |
| business_chain_pct | < 2.0 | 2.0 - 5.0 | 5.0 - 10.0 | > 10.0 | % |
| per_core_max_pct | < 80.0 | 80.0 - 90.0 | 90.0 - 95.0 | > 95.0 | % |

**Baseline**: P0 measured peak process CPU = 30.6% (psutil.Process().cpu_percent()).
**FUSE constraint**: Full-chain business CPU FUSE threshold = 2.0% (P0, unchanged).

### 2.3 Latency Thresholds

| Metric | GREEN | YELLOW | RED | BLUE | Unit |
|--------|:-----:|:------:|:---:|:----:|:----:|
| p99_ms | < 200.0 | 200.0 - 500.0 | 500.0 - 1000.0 | > 1000.0 | ms |
| p95_ms | < 100.0 | 100.0 - 300.0 | 300.0 - 500.0 | > 500.0 | ms |
| median_ms | < 50.0 | 50.0 - 100.0 | 100.0 - 200.0 | > 200.0 | ms |
| max_ms | < 500.0 | 500.0 - 1000.0 | 1000.0 - 2000.0 | > 2000.0 | ms |
| avg_ms | < 50.0 | 50.0 - 100.0 | 100.0 - 200.0 | > 200.0 | ms |

**Baseline**: P0 engine stats: avg=31.58ms, p50=20.99ms, p95=89.00ms, p99=246.01ms,
max=342.00ms. P99 hard threshold = 500ms (G4 gate), target = 200ms.

### 2.4 Render Error Rate

| Level | Threshold | Unit |
|:-----:|:---------:|:----:|
| GREEN | = 0.0% | % |
| YELLOW | > 0.01% | % |
| RED | > 0.05% | % |
| BLUE | > 1.0% | % |

**Baseline**: P0 render errors = 0.00% (0/250 renders).

### 2.5 Noise Rate

| Level | Threshold | Unit |
|:-----:|:---------:|:----:|
| GREEN | < 10.0% | % |
| YELLOW | 10.0 - 15.0% | % |
| RED | 15.0 - 25.0% | % |
| BLUE | > 25.0% | % |

**Baseline**: P0 alert noise target < 10%. 7-day silent period mechanism.

### 2.6 Memory (RSS)

| Level | Threshold | Unit |
|:-----:|:---------:|:----:|
| GREEN | < 200 MB | MB |
| YELLOW | 200 - 500 MB | MB |
| RED | 500 MB - 1 GB | MB |
| BLUE | > 1 GB | MB |

**Baseline**: Phase02 engine RSS typically < 150 MB.

### 2.7 Indicator Coverage Rate

| Level | Threshold | Unit |
|:-----:|:---------:|:----:|
| GREEN | >= 60.0% | % |
| YELLOW | 40.0 - 60.0% | % |
| RED | 20.0 - 40.0% | % |
| BLUE | < 20.0% | % |

**Baseline**: P0 D7 coverage = 78.82% (67/85 matchable charts).
**Gate**: P1 requires >= 60% (G4 gate).

> **Note**: Indicator coverage is an **inverted** metric — higher values are
> better. The `check_indicator_coverage()` method uses `_determine_inverted_level()`
> to correctly map higher-is-better semantics.

---

## 3. Monitoring Metrics Catalog

### 3.1 CPU Metrics

| Metric ID | Source | Description |
|-----------|--------|-------------|
| `process_cpu_pct` | `psutil.Process().cpu_percent()` | Process-level CPU usage |
| `business_cpu_pct` | Full-chain business CPU calculation | CPU FUSE threshold metric |
| `per_core_max_pct` | `psutil.cpu_percent(percpu=True)` max | Highest core utilization |
| `per_core_avg_pct` | `psutil.cpu_percent(percpu=True)` avg | Average core utilization |

### 3.2 Latency Metrics

| Metric ID | Source | Description |
|-----------|--------|-------------|
| `p99_ms` | Engine render time array percentile | 99th percentile latency |
| `p95_ms` | Engine render time array percentile | 95th percentile latency |
| `median_ms` | Engine render time array P50 | Median latency |
| `max_ms` | Engine render time array max | Maximum latency |
| `avg_ms` | Engine render time array mean | Average latency |

### 3.3 Rate Metrics

| Metric ID | Formula | Description |
|-----------|---------|-------------|
| `render_error_rate` | errors / total * 100 | Render failure rate |
| `noise_rate` | false_positives / total_alerts * 100 | Alert noise rate |
| `coverage_rate` | real_charts / total_charts * 100 | Indicator coverage rate |

### 3.4 Memory Metrics

| Metric ID | Source | Description |
|-----------|--------|-------------|
| `rss_mb` | `psutil.Process().memory_info().rss / 1024 / 1024` | RSS memory usage |

### 3.5 Metric Collection Pattern

```python
# The monitor accepts metrics in a flat or nested dict:
metrics = {
    "cpu": {
        "process_cpu_pct": 15.3,
        "business_cpu_pct": 2.5,
        "per_core_max_pct": 85.0,
    },
    "latency": {
        "p99_ms": 350.0,
        "p95_ms": 200.0,
        "median_ms": 15.0,
    },
    "render_errors": 0,
    "render_total": 250,
    "noise_count": 2,
    "alert_total": 11,
    "rss_mb": 180.0,
    "real_charts": 67,
    "total_charts": 85,
}
evaluation = monitor.evaluate(metrics)
```

---

## 4. Fuse Trigger Logic

### 4.1 Fuse States

| State | Description | Recovery |
|:-----:|-------------|----------|
| **CLOSED** | Fuse intact, rendering active | Initial state |
| **OPEN** | Fuse tripped, rendering stopped | Manual `reset_fuse()` |
| **HALF_OPEN** | Testing recovery (future) | Not yet implemented |

### 4.2 Auto-Trigger Conditions

The monitor auto-triggers fuse when any metric reaches RED or BLUE level:

| Condition | Fuse Level | Action |
|-----------|:----------:|--------|
| CPU any metric >= RED | RED | Stop rendering |
| Latency P99 >= RED (500ms) | RED | Stop rendering |
| Render error rate >= RED (0.05%) | RED | Stop rendering |
| Any metric >= BLUE | BLUE | Emergency shutdown |
| Multiple YELLOW metrics | YELLOW | Log + notify (no fuse) |

### 4.3 Fuse Action Execution

```
trigger_fuse("RED"):
  1. Set fuse_state = OPEN
  2. Record fuse alert in alert history
  3. If engine instance provided:
     - Call engine.stop() OR engine.pause() OR engine.set_render_enabled(False)
  4. Log CRITICAL message

trigger_fuse("BLUE"):
  1. Set fuse_state = OPEN
  2. Record fuse alert in alert history
  3. If engine instance provided:
     - Call engine.shutdown() OR engine.stop() + engine.cleanup()
  4. Log FATAL message
  5. Trigger phone escalation (via notification system)
```

### 4.4 Fuse Recovery

```python
# Manual reset
result = monitor.reset_fuse()
# Returns: {"success": True, "fuse_state": "CLOSED", ...}

# After reset, metrics must return to GREEN for sustained period
# (7-day silent period recommended per P0 alert mapping spec)
```

### 4.5 Alert Escalation Path

```
GREEN (Normal)
  |  threshold crossed
  v
YELLOW (Warning) -- Log + notify -- 3 days sustained --> escalate
  |  threshold crossed
  v
RED (Critical) -- Stop rendering -- 1 hour sustained --> escalate
  |  threshold crossed
  v
BLUE (Fatal) -- Emergency shutdown -- 24h sustained --> manual intervention
```

---

## 5. Alert Format Specification

### 5.1 Standard Alert Format

Every alert conforms to this JSON structure:

```json
{
    "level": "RED",
    "category": "latency",
    "metric": "p99_ms",
    "value": 600.0,
    "threshold": 500.0,
    "timestamp": "2026-10-15T12:00:00Z",
    "message": "latency.p99_ms: 600.0 exceeded threshold 500.0 (level=RED)"
}
```

### 5.2 Field Definitions

| Field | Type | Description | Required |
|-------|:----:|-------------|:--------:|
| `level` | string | Alert level: GREEN/YELLOW/RED/BLUE | YES |
| `category` | string | Metric category: cpu/latency/error_rate/etc. | YES |
| `metric` | string | Specific metric name within category | YES |
| `value` | float/int | Current measured value | YES |
| `threshold` | float | Threshold that was crossed (null if GREEN) | YES |
| `timestamp` | string | ISO 8601 UTC timestamp | YES |
| `message` | string | Human-readable alert description | YES |

### 5.3 Alert Query

```python
# All alerts (sorted by severity, highest first)
alerts = monitor.get_alerts()

# Only RED and above
critical_alerts = monitor.get_alerts(min_level="RED")

# Only YELLOW and above
warning_alerts = monitor.get_alerts(min_level="YELLOW")
```

---

## 6. DSHB Threshold Config Integration

### 6.1 JSON Config Format

DSHB produces a threshold configuration file in the following format:

```json
{
    "schema_version": "v88-p1.0.1",
    "generated_by": "DSHB",
    "generated_at": "2026-10-15T12:00:00Z",
    "thresholds": {
        "cpu": {
            "process_level_pct": {
                "green": 5.0,
                "yellow": 15.0,
                "red": 30.0,
                "blue": 50.0,
                "unit": "percent",
                "description": "Process-level CPU utilization"
            },
            "business_chain_pct": {
                "green": 2.0,
                "yellow": 5.0,
                "red": 10.0,
                "blue": 20.0,
                "unit": "percent",
                "description": "Full-chain business CPU"
            },
            "per_core_max_pct": {
                "green": 80.0,
                "yellow": 90.0,
                "red": 95.0,
                "blue": 98.0,
                "unit": "percent",
                "description": "Per-core max CPU utilization"
            }
        },
        "latency": {
            "p99_ms": {
                "green": 200.0,
                "yellow": 500.0,
                "red": 1000.0,
                "blue": 2000.0,
                "unit": "milliseconds",
                "description": "P99 latency"
            },
            "p95_ms": {
                "green": 100.0,
                "yellow": 300.0,
                "red": 500.0,
                "blue": 1000.0,
                "unit": "milliseconds",
                "description": "P95 latency"
            },
            "median_ms": {
                "green": 50.0,
                "yellow": 100.0,
                "red": 200.0,
                "blue": 500.0,
                "unit": "milliseconds",
                "description": "Median latency"
            },
            "max_ms": {
                "green": 500.0,
                "yellow": 1000.0,
                "red": 2000.0,
                "blue": 5000.0,
                "unit": "milliseconds",
                "description": "Max latency"
            },
            "avg_ms": {
                "green": 50.0,
                "yellow": 100.0,
                "red": 200.0,
                "blue": 500.0,
                "unit": "milliseconds",
                "description": "Average latency"
            }
        },
        "render_error_rate": {
            "rate_pct": {
                "green": 0.0,
                "yellow": 0.01,
                "red": 0.05,
                "blue": 1.0,
                "unit": "percent",
                "description": "Render error rate"
            }
        },
        "noise_rate": {
            "rate_pct": {
                "green": 10.0,
                "yellow": 15.0,
                "red": 25.0,
                "blue": 40.0,
                "unit": "percent",
                "description": "Alert noise rate"
            }
        },
        "memory": {
            "rss_mb": {
                "green": 200.0,
                "yellow": 500.0,
                "red": 1000.0,
                "blue": 2048.0,
                "unit": "megabytes",
                "description": "RSS memory"
            }
        },
        "indicator_coverage": {
            "rate_pct": {
                "green": 60.0,
                "yellow": 40.0,
                "red": 20.0,
                "blue": 5.0,
                "unit": "percent",
                "description": "Indicator coverage rate (inverted)"
            }
        }
    }
}
```

### 6.2 Loading Config

```python
# From file path
monitor = EngineThresholdMonitor(
    threshold_config_path="path/to/threshold_config.json"
)

# From dict (programmatic)
monitor = EngineThresholdMonitor()
monitor.load_thresholds(thresholds={
    "thresholds": {
        "cpu": {...},
        "latency": {...},
        ...
    }
})

# Custom thresholds (partial override)
monitor.load_thresholds(thresholds={
    "latency": {
        "p99_ms": {
            "green": 100.0,
            "yellow": 300.0,
            "red": 500.0,
            "blue": 1000.0,
            "unit": "milliseconds"
        }
    }
})
```

### 6.3 Config Validation

On load, the monitor validates:
1. Required categories exist (cpu, latency, render_error_rate, noise_rate,
   memory, indicator_coverage)
2. Each metric has all 4 levels (green, yellow, red, blue)
3. Threshold values are numeric (int/float)
4. Threshold ordering: green <= yellow <= red <= blue

Validation errors are logged as warnings but do not prevent operation.
Missing thresholds default to GREEN (no false alerts).

---

## 7. Integration Points with Engine

### 7.1 Non-Invasive Integration

The monitor does NOT require any changes to the engine. Integration is achieved
through instantiation and method calls:

```python
# Standalone usage (no engine modification)
from engine_threshold_monitor import EngineThresholdMonitor

# Initialize monitor with DSHB config
monitor = EngineThresholdMonitor(
    threshold_config_path="dshb/threshold_config.json"
)

# Feed metrics from engine runtime (collected externally)
metrics = {
    "cpu": {
        "process_cpu_pct": 15.3,
        "business_cpu_pct": 2.5,
    },
    "latency": {
        "p99_ms": 350.0,
        "p95_ms": 200.0,
    },
    "render_errors": 0,
    "render_total": 250,
    "real_charts": 67,
    "total_charts": 85,
}

evaluation = monitor.evaluate(metrics)
print(evaluation["summary"])

# Check fuse state
if monitor.get_fuse_state()["fuse_state"] != "CLOSED":
    print("Fuse is OPEN — rendering should be stopped")
```

### 7.2 Engine Callback (Optional)

If an engine instance is provided, `trigger_fuse()` will call engine methods:

```python
# With engine (optional)
engine = NodeBindingEngine(...)  # Or Phase03P0RenderEngine(...)
monitor = EngineThresholdMonitor(
    threshold_config_path="dshb/threshold_config.json",
    engine=engine  # Engine methods will be called on fuse trigger
)
```

**Expected engine methods** (all optional, gracefully handled if absent):

| Fuse Level | Method Called | Effect |
|:----------:|---------------|--------|
| RED | `engine.stop()` | Stop rendering, preserve cache |
| RED | `engine.pause()` | Alternative: pause rendering |
| RED | `engine.set_render_enabled(False)` | Alternative: disable render flag |
| BLUE | `engine.shutdown()` | Emergency shutdown |
| BLUE | `engine.stop()` + `engine.cleanup()` | Fallback: stop + cleanup |

### 7.3 Integration with P0 Render Engine

```python
# P0 render engine integration example
from v88_phase03_p0_render_engine import Phase03P0RenderEngine
from engine_threshold_monitor import EngineThresholdMonitor

engine = Phase03P0RenderEngine(
    yaml_path="framework_tree_meta_chart.yaml",
    mapping_table_path="dshe_naming_mapping.json"
)
engine.load()

monitor = EngineThresholdMonitor(
    threshold_config_path="dshb/threshold_config.json",
    engine=engine
)

# After rendering, check metrics
result = engine.render_chart_p0('cu_p1_ts_01')
latency_ms = result.get("latency_ms", 0)

monitor.check_latency({"p99_ms": latency_ms})

# Comprehensive check after batch render
metrics = {
    "cpu": {
        "process_cpu_pct": 15.3,
        "business_cpu_pct": 2.5,
    },
    "latency": {
        "p99_ms": 246.0,
        "p95_ms": 89.0,
        "median_ms": 21.0,
    },
    "render_errors": 0,
    "render_total": 250,
    "real_charts": 67,
    "total_charts": 85,
}
eval_result = monitor.evaluate(metrics)
```

### 7.4 Integration with P1 Concurrency Tests

```python
# 500-concurrent load test integration
from concurrent.futures import ThreadPoolExecutor
from engine_threshold_monitor import EngineThresholdMonitor

monitor = EngineThresholdMonitor()

# During load test, periodically check thresholds
with ThreadPoolExecutor(max_workers=500) as executor:
    for i in range(500):
        future = executor.submit(render_task, i)
        # Periodic check
        if i % 50 == 0:
            check_metrics = {
                "cpu": {"process_cpu_pct": get_cpu_usage()},
                "latency": {"p99_ms": get_p99_latency()},
                "render_errors": 0,
                "render_total": i,
            }
            evaluation = monitor.evaluate(check_metrics)
            if evaluation["fuse_state"] != "CLOSED":
                # Fuse triggered — abort load test
                executor.shutdown(wait=True)
                break
```

---

## 8. Test Strategy

### 8.1 Unit Tests

The module is fully testable independently. Key test cases:

| Test ID | Description | Method |
|---------|-------------|--------|
| UT-01 | Default threshold loading | `__init__()` without path |
| UT-02 | JSON config loading | `load_thresholds(path=...)` |
| UT-03 | Config validation (missing category) | `load_thresholds(thresholds={})` |
| UT-04 | Config validation (out-of-order) | `load_thresholds(thresholds={...})` |
| UT-05 | CPU check - all GREEN | `check_cpu_baseline({"process_cpu_pct": 1.0})` |
| UT-06 | CPU check - YELLOW | `check_cpu_baseline({"process_cpu_pct": 10.0})` |
| UT-07 | CPU check - RED (triggers fuse) | `check_cpu_baseline({"process_cpu_pct": 20.0})` |
| UT-08 | Latency check - all GREEN | `check_latency({"p99_ms": 100.0})` |
| UT-09 | Latency check - YELLOW | `check_latency({"p99_ms": 300.0})` |
| UT-10 | Latency check - RED | `check_latency({"p99_ms": 600.0})` |
| UT-11 | Render error rate - GREEN (0 errors) | `check_render_error_rate(0, 100)` |
| UT-12 | Render error rate - RED | `check_render_error_rate(10, 100)` |
| UT-13 | Noise rate - GREEN | `check_noise_rate(5, 100)` |
| UT-14 | Noise rate - RED | `check_noise_rate(20, 100)` |
| UT-15 | Memory - GREEN | `check_memory(100.0)` |
| UT-16 | Coverage - GREEN (inverted) | `check_indicator_coverage(85, 100)` |
| UT-17 | Coverage - RED (inverted) | `check_indicator_coverage(20, 100)` |
| UT-18 | Comprehensive evaluate | `evaluate(metrics)` |
| UT-19 | Alert filtering | `get_alerts(min_level="RED")` |
| UT-20 | Fuse trigger RED | `trigger_fuse("RED")` |
| UT-21 | Fuse trigger BLUE | `trigger_fuse("BLUE")` |
| UT-22 | Fuse reset | `reset_fuse()` |
| UT-23 | Invalid fuse level | `trigger_fuse("GREEN")` |
| UT-24 | Zero total_count handling | `check_render_error_rate(0, 0)` |

### 8.2 Independent Test Script

The module includes a `_demo_usage()` function that can be run directly:

```bash
python engine_threshold_monitor.py
```

This exercises all methods and prints comprehensive output for manual verification.

### 8.3 Integration Tests

| Test ID | Description | Prerequisite |
|---------|-------------|-------------|
| IT-01 | Monitor + Phase03P0RenderEngine | P0 render engine available |
| IT-02 | Monitor + 500-concurrent load test | Load test infrastructure |
| IT-03 | DSHB config integration | DSHB threshold config JSON |
| IT-04 | Fuse trigger stops rendering | Engine with stop() method |

### 8.4 Test Execution

```python
# Minimal test
from engine_threshold_monitor import EngineThresholdMonitor

# Test 1: Basic init
m = EngineThresholdMonitor()
assert m.thresholds["latency"]["p99_ms"]["green"] == 200.0

# Test 2: GREEN result
result = m.check_latency({"p99_ms": 100.0})
assert result["overall_level"] == "GREEN"

# Test 3: RED result triggers fuse
m.clear_alerts()
result = m.check_latency({"p99_ms": 600.0})
assert result["overall_level"] == "RED"
assert m.get_fuse_state()["fuse_state"] == "OPEN"

# Test 4: Reset fuse
m.reset_fuse()
assert m.get_fuse_state()["fuse_state"] == "CLOSED"
```

---

## 9. Performance Overhead Analysis

### 9.1 CPU Overhead

| Operation | Estimated Cost | Notes |
|-----------|:-------------:|-------|
| `load_thresholds()` | < 1ms | JSON parse, one-time |
| `check_cpu_baseline()` | < 0.01ms | Dict lookup + comparison |
| `check_latency()` | < 0.01ms | 5 metric checks |
| `check_render_error_rate()` | < 0.001ms | Single division |
| `check_noise_rate()` | < 0.001ms | Single division |
| `check_memory()` | < 0.001ms | Single comparison |
| `check_indicator_coverage()` | < 0.001ms | Single division |
| `evaluate()` (all) | < 0.05ms | All checks combined |
| `get_alerts()` | < 0.001ms | List sort |
| `trigger_fuse()` | < 1ms | State update + logging |

**Total per evaluation cycle**: < 0.05ms (negligible).

### 9.2 Memory Overhead

| Component | Estimated Size | Notes |
|-----------|:-------------:|-------|
| DEFAULT_THRESHOLDS dict | ~2 KB | 6 categories, 15 metrics |
| EngineThresholdMonitor instance | ~1 KB | Small state dict |
| Alert list (per 100 alerts) | ~10 KB | ~100 bytes per alert dict |
| Evaluation result dict | ~5 KB | Per evaluate() call |

**Total memory overhead**: < 20 KB even under load.

### 9.3 I/O Overhead

- **Zero I/O during checks**: All metrics are passed as in-memory dicts.
- **File I/O**: Only during `load_thresholds()` (one-time).
- **No database access**: All computation is in-memory.

### 9.4 Thread Safety

| Component | Thread Safety | Notes |
|-----------|:------------:|-------|
| `load_thresholds()` | Not thread-safe | Call once during init |
| `check_*()` methods | Thread-safe | Read-only on `self.thresholds` |
| `evaluate()` | Thread-safe | Uses local state + cached metrics |
| `trigger_fuse()` | Not thread-safe | Should be called from single thread |
| `get_alerts()` | Thread-safe | Read-only on `self._alerts` |

**Recommendation**: Use a single monitoring thread that calls `evaluate()`
periodically and checks `get_alerts()`.

---

## 10. Rollout Plan

### 10.1 Phase03 P1 Rollout

| Step | Action | Owner | Deliverable |
|:----:|--------|:-----:|-------------|
| 1 | DSHB produces threshold_config.json | DSHB | `dshb/threshold_config.json` |
| 2 | DSHE integrates monitor into render pipeline | DSHE | Engine call sites updated |
| 3 | P1 unit tests pass (UT-01 to UT-24) | DSHE | Test report |
| 4 | P1 integration tests pass (IT-01 to IT-04) | DSHE | Integration report |
| 5 | 7-day silent period (log-only, no fuse) | DSHE | Noise rate report |
| 6 | Fuse activation (enable RED/BLUE triggers) | DSHE | Fuse enabled |
| 7 | P2 long-stability observation (7 days) | HERMEShf | Stability report |

### 10.2 DSHB Threshold Config Integration Timeline

| Phase | Week | DSHB Action | DSHE Action |
|:-----:|:----:|-------------|-------------|
| P0 D2 | W1 | Threshold config JSON v0.1 | Review config format |
| P1 D1 | W2 | Threshold config JSON v1.0 | Integrate + unit test |
| P1 D4 | W3 | Config calibration (if needed) | 7-day silent period |
| P2 D1 | W4 | Monitor threshold effectiveness | Fuse activation |
| P2 D8 | W5 | Final threshold tuning | P2 stability complete |

### 10.3 Rollback Plan

| Scenario | Detection | Action | Recovery |
|----------|:---------:|--------|----------|
| False positive fuse (noise rate > 10%) | Monitor `noise_rate` check | Reset fuse, widen thresholds | Re-observe 7 days |
| Fuse prevents legitimate rendering | Alert + human review | Reset fuse, increase threshold | Re-deploy config |
| Monitor crash (module error) | Exception in evaluate() | Fallback to GREEN | Fix and restart |

### 10.4 Success Criteria

| # | Criterion | Threshold | Verification |
|:-:|-----------|:---------:|-------------|
| 1 | Module loads without error | 0 errors | `python -c "import engine_threshold_monitor"` |
| 2 | All unit tests pass | 24/24 PASS | Test execution report |
| 3 | Threshold config loads from DSHB JSON | Config parsed | Integration test |
| 4 | RED trigger stops rendering | Fuse state = OPEN | IT-04 verification |
| 5 | BLUE trigger stops rendering | Fuse state = OPEN | IT-04 verification |
| 6 | Noise rate < 10% after silent period | < 10% | P2 observation |
| 7 | Zero engine modification required | MD5 unchanged | `md5sum` comparison |

---

## 11. Constraint Compliance

| # | Constraint | Status |
|:-:|------------|:------:|
| 1 | Does NOT modify engine | YES — standalone module |
| 2 | UTF-8 encoding | YES — all files UTF-8 |
| 3 | ASCII-safe output (no emoji) | YES — uses [OK]/[!!]/[??]/[CRIT]/[FATAL] |
| 4 | Supports DSHB JSON threshold config | YES — `load_thresholds(path=...)` |
| 5 | Testable independently | YES — no external dependencies, demo function |
| 6 | CPU FUSE 2.0% unchanged | YES — default threshold, config-overridable |
| 7 | BRANCH_LOCKED | YES — feature/v88-g1 |
| 8 | NO_OVERWRITE | YES — new files only |
| 9 | NO_MODIFY_V87 | YES — no V87 asset changes |
| 10 | NO_ZHIJI_API_CALL | YES — no API calls |

---

## 12. Change Log

| Version | Date | Description | Author |
|:-------:|:----:|-------------|:------:|
| v1.0 | 2026-10-15 | P1 initial design spec | DSHE |

---

*Document Generated: 2026-10-15 UTC+8*
*Generated by: DSHE Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED)*
*Schema: v88-p1.0.1*
*Status: V88_PHASE03_P1_ENGINE_THRESHOLD_MONITOR=READY*
*Reference: P0 Alert Level Mapping / Gate Matrix R-5/R-6 / G4 Goal*
