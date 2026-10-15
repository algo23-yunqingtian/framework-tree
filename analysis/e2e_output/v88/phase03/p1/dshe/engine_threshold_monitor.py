#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
engine_threshold_monitor.py — V88 Phase03-P1 Engine-Side Threshold Monitor
==========================================================================
TASK_ID: V88_PHASE03_P1_ENGINE_THRESHOLD_MONITOR
AGENT: DSHE
BRANCH: feature/v88-g1 (BRANCH_LOCKED)
DATE: 2026-10-15
PURPOSE: Engine-side 3-tier (4-level) threshold monitoring with fuse trigger logic.

Architecture:
    DSHB outputs threshold configuration (JSON format)
    -> EngineThresholdMonitor loads thresholds from JSON config
    -> Checks against live engine metrics (CPU, latency, error rate, etc.)
    -> Triggers fuse/warning logic at appropriate tier
    -> Returns comprehensive evaluation with alerts

Threshold Levels:
    GREEN  (Normal)    : No action
    YELLOW (Warning)   : Log + notify
    RED    (Critical)  : Trigger fuse, stop rendering
    BLUE   (Fatal)     : Emergency shutdown

Design Constraints:
    - Does NOT modify the engine
    - ASCII-safe output (no emoji, uses [OK]/[!!]/[??] for status indicators)
    - UTF-8 encoding
    - Fully testable independently (no external dependencies beyond stdlib)
    - All thresholds configurable via DSHB JSON config

Baseline References:
    - CPU FUSE threshold (full-chain): 2.0% (P0, unchanged)
    - Process-level CPU peak: ~30.6% (P0 baseline via psutil)
    - Latency P99 hard threshold: < 500ms (G4 gate)
    - Latency P99 target: < 200ms
    - Noise rate target: < 10%
    - Indicator coverage gate: >= 60%
    - Concurrent P99 at 50: 342ms (P0 stress test)
    - Render error rate: 0.00% (P0 baseline)

Change Log:
    V88-P1.0.1 (2026-10-15): Phase03-P1 initial version
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

# =============================================================================
# Constants
# =============================================================================
SCHEMA_VERSION = "v88-p1.0.1"
TASK_ID = "V88_PHASE03_P1_ENGINE_THRESHOLD_MONITOR"
AGENT = "DSHE"
BRANCH = "feature/v88-g1"

# Threshold level constants
LEVEL_GREEN = "GREEN"
LEVEL_YELLOW = "YELLOW"
LEVEL_RED = "RED"
LEVEL_BLUE = "BLUE"

# Level priority (higher = more severe)
LEVEL_PRIORITY = {
    LEVEL_GREEN: 0,
    LEVEL_YELLOW: 1,
    LEVEL_RED: 2,
    LEVEL_BLUE: 3,
}

# Status indicator strings (ASCII-safe, no emoji)
STATUS_OK = "[OK]"
STATUS_WARN = "[!!]"
STATUS_UNKNOWN = "[??]"
STATUS_CRITICAL = "[CRIT]"
STATUS_FATAL = "[FATAL]"

# Fuse states
FUSE_OPEN = "OPEN"        # Fuse tripped, rendering stopped
FUSE_CLOSED = "CLOSED"    # Fuse intact, rendering active
FUSE_HALF_OPEN = "HALF_OPEN"  # Testing recovery

# Default thresholds (overridable via JSON config)
DEFAULT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "cpu": {
        "process_level_pct": {
            "green": 5.0,
            "yellow": 15.0,
            "red": 30.0,
            "blue": 50.0,
            "unit": "percent",
            "description": "Process-level CPU utilization (psutil.Process.cpu_percent)"
        },
        "business_chain_pct": {
            "green": 2.0,
            "yellow": 5.0,
            "red": 10.0,
            "blue": 20.0,
            "unit": "percent",
            "description": "Full-chain business CPU (P0 FUSE threshold is 2.0%)"
        },
        "per_core_max_pct": {
            "green": 80.0,
            "yellow": 90.0,
            "red": 95.0,
            "blue": 98.0,
            "unit": "percent",
            "description": "Per-core normalized CPU utilization"
        }
    },
    "latency": {
        "p99_ms": {
            "green": 200.0,
            "yellow": 500.0,
            "red": 1000.0,
            "blue": 2000.0,
            "unit": "milliseconds",
            "description": "P99 latency (target < 200ms, hard threshold < 500ms)"
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
            "description": "Median (P50) latency"
        },
        "max_ms": {
            "green": 500.0,
            "yellow": 1000.0,
            "red": 2000.0,
            "blue": 5000.0,
            "unit": "milliseconds",
            "description": "Maximum observed latency"
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
            "description": "Render error rate (errors / total_renders * 100)"
        }
    },
    "noise_rate": {
        "rate_pct": {
            "green": 10.0,
            "yellow": 15.0,
            "red": 25.0,
            "blue": 40.0,
            "unit": "percent",
            "description": "Alert noise rate (false_positives / total_alerts * 100)"
        }
    },
    "memory": {
        "rss_mb": {
            "green": 200.0,
            "yellow": 500.0,
            "red": 1000.0,
            "blue": 2048.0,
            "unit": "megabytes",
            "description": "Resident Set Size (RSS) memory usage"
        }
    },
    "indicator_coverage": {
        "rate_pct": {
            "green": 60.0,
            "yellow": 40.0,
            "red": 20.0,
            "blue": 5.0,
            "unit": "percent",
            "description": "Indicator coverage rate (source=real / total_charts * 100)"
        }
    }
}


# =============================================================================
# EngineThresholdMonitor
# =============================================================================
class EngineThresholdMonitor:
    """
    Engine-side threshold monitor with 3-tier fuse thresholds.

    Monitors engine health metrics against configurable thresholds and triggers
    fuse/warning logic at appropriate severity levels.

    Threshold Levels:
        GREEN  (Normal)    : No action, metrics within safe range
        YELLOW (Warning)   : Log warning + notify, no fuse action
        RED    (Critical)  : Trigger fuse, stop rendering
        BLUE   (Fatal)     : Emergency shutdown, escalate immediately

    Usage:
        # From DSHB JSON config
        monitor = EngineThresholdMonitor(
            threshold_config_path="path/to/threshold_config.json"
        )

        # Or with defaults and inline thresholds
        monitor = EngineThresholdMonitor()
        monitor.load_thresholds({"cpu": {...}, "latency": {...}})

        # Check individual metrics
        cpu_status = monitor.check_cpu_baseline({"process_cpu_pct": 15.3})
        latency_status = monitor.check_latency({
            "p99_ms": 350.0, "p95_ms": 200.0, "median_ms": 15.0
        })

        # Run comprehensive evaluation
        evaluation = monitor.evaluate()
        print(evaluation.get_summary())

        # Check alerts
        alerts = monitor.get_alerts()
        print(f"Active alerts: {len(alerts)}")

        # Trigger fuse at specific level
        monitor.trigger_fuse("RED")
    """

    def __init__(self, threshold_config_path: Optional[str] = None,
                 engine: Any = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize EngineThresholdMonitor.

        Args:
            threshold_config_path: Path to DSHB threshold config JSON file.
                If None, uses DEFAULT_THRESHOLDS.
            engine: Optional engine instance for fuse trigger callback.
                If provided, trigger_fuse() will attempt to call engine.stop()
                or engine.shutdown() depending on fuse level.
            logger: Optional logger instance. If None, creates a default logger.
        """
        self.engine = engine
        self.logger = logger or logging.getLogger(__name__)

        # Load thresholds
        self.thresholds: Dict[str, Dict[str, Any]] = {}
        if threshold_config_path:
            self.load_thresholds(path=threshold_config_path)
        else:
            self.load_thresholds(thresholds=DEFAULT_THRESHOLDS)

        # State tracking
        self._alerts: List[Dict[str, Any]] = []
        self._fuse_state: str = FUSE_CLOSED
        self._fuse_level: Optional[str] = None
        self._fuse_triggered_at: Optional[float] = None
        self._alert_history: List[Dict[str, Any]] = []
        self._last_evaluation: Optional[Dict[str, Any]] = None

        # Metrics cache for evaluate()
        self._last_metrics: Dict[str, Any] = {}

        self.logger.info(
            "%s EngineThresholdMonitor initialized (schema=%s, config=%s)",
            STATUS_OK, SCHEMA_VERSION,
            threshold_config_path or "defaults"
        )

    # =========================================================================
    # Threshold Loading
    # =========================================================================
    def load_thresholds(self, path: Optional[str] = None,
                        thresholds: Optional[Dict] = None) -> bool:
        """
        Load threshold configuration from JSON config file or dict.

        Args:
            path: Path to JSON file containing threshold configuration.
            thresholds: Optional dict of thresholds (takes precedence if both
                provided).

        Returns:
            True if thresholds loaded successfully, False otherwise.

        JSON Config Format:
            {
                "schema_version": "v88-p1.0.1",
                "thresholds": {
                    "cpu": {
                        "process_level_pct": {
                            "green": 5.0, "yellow": 15.0,
                            "red": 30.0, "blue": 50.0,
                            "unit": "percent"
                        },
                        ...
                    },
                    "latency": {
                        "p99_ms": {
                            "green": 200.0, "yellow": 500.0,
                            "red": 1000.0, "blue": 2000.0,
                            "unit": "milliseconds"
                        },
                        ...
                    },
                    ...
                }
            }
        """
        config = None

        if thresholds is not None:
            config = thresholds
        elif path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(
                    "%s Loaded thresholds from %s (%d categories)",
                    STATUS_OK, path,
                    len(config.get("thresholds", {}))
                )
            except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
                self.logger.warning(
                    "%s Failed to load threshold config from %s: %s. Using defaults.",
                    STATUS_WARN, path, e
                )
                config = None

        if config is None:
            config = DEFAULT_THRESHOLDS

        # Extract thresholds dict from config
        if "thresholds" in config:
            self.thresholds = config["thresholds"]
        else:
            self.thresholds = config

        # Validate threshold structure
        self._validate_thresholds()

        return True

    def _validate_thresholds(self) -> List[str]:
        """
        Validate threshold structure.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        required_categories = ["cpu", "latency", "render_error_rate",
                                "noise_rate", "memory", "indicator_coverage"]
        required_levels = ["green", "yellow", "red", "blue"]

        # Categories where higher values are better (inverted thresholds)
        inverted_categories = {"indicator_coverage"}

        for category in required_categories:
            if category not in self.thresholds:
                errors.append(f"Missing category: {category}")
                continue
            for metric, spec in self.thresholds[category].items():
                if not isinstance(spec, dict):
                    errors.append(
                        f"{category}.{metric}: must be a dict, got {type(spec).__name__}"
                    )
                    continue
                for level in required_levels:
                    if level not in spec:
                        errors.append(
                            f"{category}.{metric}: missing '{level}' threshold"
                        )
                    elif not isinstance(spec[level], (int, float)):
                        errors.append(
                            f"{category}.{metric}.{level}: must be numeric, "
                            f"got {type(spec[level]).__name__}"
                        )
                # Check threshold ordering
                values = [spec.get(l, 0) for l in required_levels]
                if category in inverted_categories:
                    # Inverted: green >= yellow >= red >= blue (higher is better)
                    if values != sorted(values, reverse=True):
                        errors.append(
                            f"{category}.{metric}: inverted thresholds out of order "
                            f"(expected green >= yellow >= red >= blue, "
                            f"got {values})"
                        )
                else:
                    # Normal: green <= yellow <= red <= blue (higher is worse)
                    if values != sorted(values):
                        errors.append(
                            f"{category}.{metric}: thresholds out of order "
                            f"(expected green <= yellow <= red <= blue, "
                            f"got {values})"
                        )

        if errors:
            self.logger.warning(
                "%s Threshold validation found %d issue(s): %s",
                STATUS_UNKNOWN, len(errors), "; ".join(errors[:5])
            )

        return errors

    def get_threshold(self, category: str, metric: str,
                      level: str) -> Optional[float]:
        """
        Get a specific threshold value.

        Args:
            category: Threshold category (e.g., "cpu", "latency").
            metric: Metric name within category (e.g., "p99_ms").
            level: Threshold level (e.g., "green", "yellow").

        Returns:
            Threshold value or None if not found.
        """
        try:
            return self.thresholds[category][metric][level]
        except (KeyError, TypeError):
            return None

    # =========================================================================
    # Metric Checks
    # =========================================================================
    def check_cpu_baseline(self, baseline_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check CPU utilization against 3-tier thresholds.

        Args:
            baseline_report: Dict containing CPU metrics. Expected keys:
                - process_cpu_pct: Process-level CPU usage (psutil)
                - business_cpu_pct: Full-chain business CPU usage
                - per_core_max_pct: Maximum per-core CPU usage
                - per_core_avg_pct: Average per-core CPU usage

        Returns:
            Dict with status per CPU metric:
            {
                "process_cpu_pct": {"level": "YELLOW", "value": 15.3, "threshold": 15.0, ...},
                ...
                "overall_level": "YELLOW",
                "alerts": [...]
            }
        """
        results = {}
        category_thresholds = self.thresholds.get("cpu", {})

        cpu_metrics = {
            "process_cpu_pct": baseline_report.get("process_cpu_pct",
                                                    baseline_report.get("process_cpu", 0)),
            "business_cpu_pct": baseline_report.get("business_cpu_pct",
                                                      baseline_report.get("business_cpu", 0)),
            "per_core_max_pct": baseline_report.get("per_core_max_pct",
                                                      baseline_report.get("per_core_max", 0)),
            "per_core_avg_pct": baseline_report.get("per_core_avg_pct",
                                                      baseline_report.get("per_core_avg", 0)),
        }

        overall_level = LEVEL_GREEN

        for metric_name, value in cpu_metrics.items():
            if value is None:
                value = 0.0
            metric_key = f"{metric_name}"
            threshold_spec = category_thresholds.get(metric_key, {})

            if not threshold_spec:
                # Try partial match (e.g., process_cpu -> process_level_pct)
                short_key = metric_name.replace("_cpu_pct", "").replace("_pct", "")
                for k in category_thresholds:
                    if k.startswith(short_key):
                        metric_key = k
                        threshold_spec = category_thresholds[k]
                        break

            if not threshold_spec:
                # Cannot check this metric
                results[metric_name] = {
                    "level": LEVEL_GREEN,
                    "value": value,
                    "status": STATUS_UNKNOWN,
                    "message": f"No threshold defined for {metric_name}"
                }
                continue

            level = self._determine_level(value, threshold_spec)
            results[metric_name] = {
                "level": level,
                "value": value,
                "thresholds": {
                    "green": threshold_spec.get("green"),
                    "yellow": threshold_spec.get("yellow"),
                    "red": threshold_spec.get("red"),
                    "blue": threshold_spec.get("blue"),
                },
                "status": self._level_to_status(level),
                "message": f"CPU {metric_name}: {value:.2f} (threshold: "
                           f"Y={threshold_spec.get('yellow')}, "
                           f"R={threshold_spec.get('red')}, "
                           f"B={threshold_spec.get('blue')})"
            }

            # Track worst level
            if LEVEL_PRIORITY.get(level, 0) > LEVEL_PRIORITY.get(overall_level, 0):
                overall_level = level

            # Create alert if above GREEN
            if level != LEVEL_GREEN:
                alert = self._create_alert(
                    level=level,
                    category="cpu",
                    metric=metric_name,
                    value=value,
                    threshold=self._get_trigger_threshold(value, threshold_spec)
                )
                self._alerts.append(alert)

        result = {
            "metrics": results,
            "overall_level": overall_level,
            "overall_status": self._level_to_status(overall_level),
        }

        # Auto-trigger fuse if RED or above
        if LEVEL_PRIORITY.get(overall_level, 0) >= LEVEL_PRIORITY.get(LEVEL_RED, 0):
            self._auto_trigger_fuse(overall_level)

        return result

    def check_latency(self, latency_ms_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Check latency metrics against thresholds.

        Args:
            latency_ms_dict: Dict containing latency percentiles in ms.
                Expected keys: p99_ms, p95_ms, median_ms (or p50_ms),
                max_ms, avg_ms. Also accepts p99, p95, p50, max, avg
                (without _ms suffix).

        Returns:
            Dict with status per latency metric and overall level.
        """
        results = {}
        category_thresholds = self.thresholds.get("latency", {})

        # Normalize latency dict keys
        normalized = {}
        for key, value in latency_ms_dict.items():
            if key.endswith("_ms"):
                normalized[key] = value
            elif key in ("p99", "p95", "p50", "median", "max", "avg"):
                suffix_map = {"median": "median", "max": "max", "avg": "avg"}
                new_key = suffix_map.get(key, key)
                normalized[f"{new_key}_ms"] = value
            else:
                normalized[key] = value

        overall_level = LEVEL_GREEN

        for metric_name, value in normalized.items():
            if value is None:
                value = 0.0

            threshold_spec = category_thresholds.get(metric_name, {})

            if not threshold_spec:
                results[metric_name] = {
                    "level": LEVEL_GREEN,
                    "value": value,
                    "status": STATUS_UNKNOWN,
                    "message": f"No threshold defined for latency.{metric_name}"
                }
                continue

            level = self._determine_level(value, threshold_spec)
            results[metric_name] = {
                "level": level,
                "value": round(value, 4),
                "thresholds": {
                    "green": threshold_spec.get("green"),
                    "yellow": threshold_spec.get("yellow"),
                    "red": threshold_spec.get("red"),
                    "blue": threshold_spec.get("blue"),
                },
                "status": self._level_to_status(level),
                "message": f"Latency {metric_name}: {value:.2f}ms "
                           f"(Y={threshold_spec.get('yellow')}, "
                           f"R={threshold_spec.get('red')})"
            }

            if LEVEL_PRIORITY.get(level, 0) > LEVEL_PRIORITY.get(overall_level, 0):
                overall_level = level

            if level != LEVEL_GREEN:
                alert = self._create_alert(
                    level=level,
                    category="latency",
                    metric=metric_name,
                    value=round(value, 4),
                    threshold=self._get_trigger_threshold(value, threshold_spec)
                )
                self._alerts.append(alert)

        return {
            "metrics": results,
            "overall_level": overall_level,
            "overall_status": self._level_to_status(overall_level),
        }

    def check_render_error_rate(self, error_count: int,
                                total_count: int) -> Dict[str, Any]:
        """
        Check render error rate against thresholds.

        Args:
            error_count: Number of render errors.
            total_count: Total number of render attempts.

        Returns:
            Dict with error rate, level, and alert info.
        """
        category_thresholds = self.thresholds.get("render_error_rate", {})
        threshold_spec = category_thresholds.get("rate_pct", {})

        if total_count <= 0:
            return {
                "level": LEVEL_GREEN,
                "value": 0.0,
                "error_count": error_count,
                "total_count": total_count,
                "status": STATUS_UNKNOWN,
                "message": f"Cannot compute error rate: total_count={total_count}"
            }

        rate_pct = (error_count / total_count) * 100.0

        if not threshold_spec:
            return {
                "level": LEVEL_GREEN,
                "value": round(rate_pct, 6),
                "error_count": error_count,
                "total_count": total_count,
                "status": STATUS_UNKNOWN,
                "message": "No threshold defined for render_error_rate.rate_pct"
            }

        level = self._determine_level(rate_pct, threshold_spec)

        result = {
            "level": level,
            "value": round(rate_pct, 6),
            "error_count": error_count,
            "total_count": total_count,
            "thresholds": {
                "green": threshold_spec.get("green"),
                "yellow": threshold_spec.get("yellow"),
                "red": threshold_spec.get("red"),
                "blue": threshold_spec.get("blue"),
            },
            "status": self._level_to_status(level),
            "message": f"Render error rate: {rate_pct:.4f}% "
                       f"({error_count}/{total_count})"
        }

        if level != LEVEL_GREEN:
            alert = self._create_alert(
                level=level,
                category="render_error_rate",
                metric="rate_pct",
                value=round(rate_pct, 6),
                threshold=self._get_trigger_threshold(rate_pct, threshold_spec)
            )
            self._alerts.append(alert)

        # Auto-trigger fuse if RED or above
        if LEVEL_PRIORITY.get(level, 0) >= LEVEL_PRIORITY.get(LEVEL_RED, 0):
            self._auto_trigger_fuse(level)

        return result

    def check_noise_rate(self, noise_count: int,
                         total_count: int) -> Dict[str, Any]:
        """
        Check alert noise rate against thresholds.

        Args:
            noise_count: Number of false positive alerts (noise).
            total_count: Total number of alerts generated.

        Returns:
            Dict with noise rate, level, and alert info.
        """
        category_thresholds = self.thresholds.get("noise_rate", {})
        threshold_spec = category_thresholds.get("rate_pct", {})

        if total_count <= 0:
            return {
                "level": LEVEL_GREEN,
                "value": 0.0,
                "noise_count": noise_count,
                "total_count": total_count,
                "status": STATUS_UNKNOWN,
                "message": f"Cannot compute noise rate: total_count={total_count}"
            }

        rate_pct = (noise_count / total_count) * 100.0

        if not threshold_spec:
            return {
                "level": LEVEL_GREEN,
                "value": round(rate_pct, 6),
                "noise_count": noise_count,
                "total_count": total_count,
                "status": STATUS_UNKNOWN,
                "message": "No threshold defined for noise_rate.rate_pct"
            }

        level = self._determine_level(rate_pct, threshold_spec)

        result = {
            "level": level,
            "value": round(rate_pct, 6),
            "noise_count": noise_count,
            "total_count": total_count,
            "thresholds": {
                "green": threshold_spec.get("green"),
                "yellow": threshold_spec.get("yellow"),
                "red": threshold_spec.get("red"),
                "blue": threshold_spec.get("blue"),
            },
            "status": self._level_to_status(level),
            "message": f"Noise rate: {rate_pct:.4f}% "
                       f"({noise_count}/{total_count})"
        }

        if level != LEVEL_GREEN:
            alert = self._create_alert(
                level=level,
                category="noise_rate",
                metric="rate_pct",
                value=round(rate_pct, 6),
                threshold=self._get_trigger_threshold(rate_pct, threshold_spec)
            )
            self._alerts.append(alert)

        return result

    def check_memory(self, rss_mb: float) -> Dict[str, Any]:
        """
        Check memory (RSS) usage against thresholds.

        Args:
            rss_mb: Resident Set Size in megabytes.

        Returns:
            Dict with RSS level and threshold comparison.
        """
        category_thresholds = self.thresholds.get("memory", {})
        threshold_spec = category_thresholds.get("rss_mb", {})

        if not threshold_spec:
            return {
                "level": LEVEL_GREEN,
                "value": rss_mb,
                "status": STATUS_UNKNOWN,
                "message": "No threshold defined for memory.rss_mb"
            }

        level = self._determine_level(rss_mb, threshold_spec)

        result = {
            "level": level,
            "value": round(rss_mb, 2),
            "unit": "MB",
            "thresholds": {
                "green": threshold_spec.get("green"),
                "yellow": threshold_spec.get("yellow"),
                "red": threshold_spec.get("red"),
                "blue": threshold_spec.get("blue"),
            },
            "status": self._level_to_status(level),
            "message": f"RSS memory: {rss_mb:.1f}MB "
                       f"(Y={threshold_spec.get('yellow')}, "
                       f"R={threshold_spec.get('red')})"
        }

        if level != LEVEL_GREEN:
            alert = self._create_alert(
                level=level,
                category="memory",
                metric="rss_mb",
                value=round(rss_mb, 2),
                threshold=self._get_trigger_threshold(rss_mb, threshold_spec)
            )
            self._alerts.append(alert)

        return result

    def check_indicator_coverage(self, real_count: int,
                                 total_count: int) -> Dict[str, Any]:
        """
        Check indicator coverage rate against thresholds.

        Args:
            real_count: Number of charts with source=real data.
            total_count: Total number of charts.

        Returns:
            Dict with coverage rate, level, and alert info.
        """
        category_thresholds = self.thresholds.get("indicator_coverage", {})
        threshold_spec = category_thresholds.get("rate_pct", {})

        if total_count <= 0:
            return {
                "level": LEVEL_GREEN,
                "value": 0.0,
                "real_count": real_count,
                "total_count": total_count,
                "status": STATUS_UNKNOWN,
                "message": f"Cannot compute coverage: total_count={total_count}"
            }

        rate_pct = (real_count / total_count) * 100.0

        if not threshold_spec:
            return {
                "level": LEVEL_GREEN,
                "value": round(rate_pct, 4),
                "real_count": real_count,
                "total_count": total_count,
                "status": STATUS_UNKNOWN,
                "message": "No threshold defined for indicator_coverage.rate_pct"
            }

        # Coverage rate is INVERTED: higher is better, so green is ABOVE green threshold
        # This is special handling: green >= green_threshold, blue < blue_threshold
        level = self._determine_inverted_level(rate_pct, threshold_spec)

        result = {
            "level": level,
            "value": round(rate_pct, 4),
            "real_count": real_count,
            "total_count": total_count,
            "thresholds": {
                "green_min": threshold_spec.get("green"),
                "yellow_min": threshold_spec.get("yellow"),
                "red_min": threshold_spec.get("red"),
                "blue_min": threshold_spec.get("blue"),
            },
            "status": self._level_to_status(level),
            "message": f"Indicator coverage: {rate_pct:.2f}% "
                       f"({real_count}/{total_count}) "
                       f"(target >= {threshold_spec.get('green')}%)"
        }

        if level != LEVEL_GREEN:
            # For inverted, the threshold is the minimum we fell below
            alert = self._create_alert(
                level=level,
                category="indicator_coverage",
                metric="rate_pct",
                value=round(rate_pct, 4),
                threshold=self._get_trigger_threshold_inverted(rate_pct, threshold_spec)
            )
            self._alerts.append(alert)

        return result

    # =========================================================================
    # Comprehensive Evaluation
    # =========================================================================
    def evaluate(self, metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run all checks and return comprehensive evaluation.

        Args:
            metrics: Dict of all metrics to check. Expected structure:
                {
                    "cpu": {
                        "process_cpu_pct": 15.3,
                        "business_cpu_pct": 2.5,
                        "per_core_max_pct": 85.0
                    },
                    "latency": {
                        "p99_ms": 350.0,
                        "p95_ms": 200.0,
                        "median_ms": 15.0,
                        "max_ms": 500.0,
                        "avg_ms": 31.5
                    },
                    "render_errors": 0,
                    "render_total": 250,
                    "noise_count": 2,
                    "alert_total": 11,
                    "rss_mb": 180.0,
                    "real_charts": 67,
                    "total_charts": 85
                }
                If None, uses last cached metrics (from previous check calls).

        Returns:
            Dict with comprehensive evaluation:
            {
                "timestamp": "2026-10-15T12:00:00Z",
                "overall_level": "YELLOW",
                "fuse_state": "CLOSED",
                "categories": {
                    "cpu": {...},
                    "latency": {...},
                    ...
                },
                "alerts": [...],
                "summary": "..."
            }
        """
        # Cache metrics for later use
        if metrics:
            self._last_metrics = metrics

        evaluation = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "schema_version": SCHEMA_VERSION,
            "overall_level": LEVEL_GREEN,
            "fuse_state": self._fuse_state,
            "categories": {},
            "alerts": list(self._alerts),
            "summary": "",
        }

        # Determine worst overall level
        worst_priority = 0
        worst_level = LEVEL_GREEN

        # --- CPU ---
        cpu_data = self._get_metric(metrics, "cpu", {})
        if cpu_data:
            cpu_result = self.check_cpu_baseline(cpu_data)
            evaluation["categories"]["cpu"] = cpu_result
            level = cpu_result.get("overall_level", LEVEL_GREEN)
            if LEVEL_PRIORITY.get(level, 0) > worst_priority:
                worst_priority = LEVEL_PRIORITY[level]
                worst_level = level

        # --- Latency ---
        latency_data = self._get_metric(metrics, "latency", {})
        if latency_data:
            latency_result = self.check_latency(latency_data)
            evaluation["categories"]["latency"] = latency_result
            level = latency_result.get("overall_level", LEVEL_GREEN)
            if LEVEL_PRIORITY.get(level, 0) > worst_priority:
                worst_priority = LEVEL_PRIORITY[level]
                worst_level = level

        # --- Render Error Rate ---
        render_errors = self._get_metric(metrics, "render_errors", 0)
        render_total = self._get_metric(metrics, "render_total", 0)
        if render_total > 0:
            error_result = self.check_render_error_rate(render_errors, render_total)
            evaluation["categories"]["render_error_rate"] = error_result
            level = error_result.get("level", LEVEL_GREEN)
            if LEVEL_PRIORITY.get(level, 0) > worst_priority:
                worst_priority = LEVEL_PRIORITY[level]
                worst_level = level

        # --- Noise Rate ---
        noise_count = self._get_metric(metrics, "noise_count", 0)
        alert_total = self._get_metric(metrics, "alert_total", 0)
        if alert_total > 0:
            noise_result = self.check_noise_rate(noise_count, alert_total)
            evaluation["categories"]["noise_rate"] = noise_result
            level = noise_result.get("level", LEVEL_GREEN)
            if LEVEL_PRIORITY.get(level, 0) > worst_priority:
                worst_priority = LEVEL_PRIORITY[level]
                worst_level = level

        # --- Memory ---
        rss_mb = self._get_metric(metrics, "rss_mb", None)
        if rss_mb is not None:
            mem_result = self.check_memory(rss_mb)
            evaluation["categories"]["memory"] = mem_result
            level = mem_result.get("level", LEVEL_GREEN)
            if LEVEL_PRIORITY.get(level, 0) > worst_priority:
                worst_priority = LEVEL_PRIORITY[level]
                worst_level = level

        # --- Indicator Coverage ---
        real_charts = self._get_metric(metrics, "real_charts", 0)
        total_charts = self._get_metric(metrics, "total_charts", 0)
        if total_charts > 0:
            cov_result = self.check_indicator_coverage(real_charts, total_charts)
            evaluation["categories"]["indicator_coverage"] = cov_result
            level = cov_result.get("level", LEVEL_GREEN)
            if LEVEL_PRIORITY.get(level, 0) > worst_priority:
                worst_priority = LEVEL_PRIORITY[level]
                worst_level = level

        evaluation["overall_level"] = worst_level

        # Generate summary
        evaluation["summary"] = self._generate_summary(evaluation)

        # Update fuse state if needed
        if worst_priority >= LEVEL_PRIORITY.get(LEVEL_RED, 0):
            self._auto_trigger_fuse(worst_level)
            evaluation["fuse_state"] = self._fuse_state
            evaluation["fuse_level"] = self._fuse_level
            evaluation["fuse_triggered_at"] = self._fuse_triggered_at

        # Cache this evaluation
        self._last_evaluation = evaluation

        return evaluation

    def get_alerts(self, min_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return list of active alerts.

        Args:
            min_level: Minimum alert level to include. If None, returns all.
                Valid values: "GREEN", "YELLOW", "RED", "BLUE".

        Returns:
            List of alert dicts sorted by severity (highest first).
        """
        if not min_level:
            return sorted(
                self._alerts,
                key=lambda a: LEVEL_PRIORITY.get(a.get("level", LEVEL_GREEN), 0),
                reverse=True
            )

        min_priority = LEVEL_PRIORITY.get(min_level, 0)
        filtered = [
            a for a in self._alerts
            if LEVEL_PRIORITY.get(a.get("level", LEVEL_GREEN), 0) >= min_priority
        ]
        return sorted(
            filtered,
            key=lambda a: LEVEL_PRIORITY.get(a.get("level", LEVEL_GREEN), 0),
            reverse=True
        )

    # =========================================================================
    # Fuse Control
    # =========================================================================
    def trigger_fuse(self, level: str) -> Dict[str, Any]:
        """
        Trigger fuse at the given level.

        Fuse levels:
            RED   : Critical fuse - stop rendering, maintain cache
            BLUE  : Fatal fuse - emergency shutdown

        Args:
            level: Fuse level to trigger ("RED" or "BLUE").

        Returns:
            Dict with fuse action result.
        """
        if level not in (LEVEL_RED, LEVEL_BLUE):
            return {
                "success": False,
                "error": f"Invalid fuse level: {level}. "
                         f"Only RED and BLUE trigger fuse.",
                "fuse_state": self._fuse_state
            }

        result = {
            "success": True,
            "level": level,
            "fuse_state": FUSE_OPEN,
            "action_taken": "",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": ""
        }

        # Update fuse state
        previous_state = self._fuse_state
        self._fuse_state = FUSE_OPEN
        self._fuse_level = level
        self._fuse_triggered_at = time.time()

        # Record fuse alert
        fuse_alert = {
            "level": level,
            "category": "fuse",
            "metric": "fuse_trigger",
            "value": level,
            "threshold": level,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": f"FUSE TRIGGERED at level {level}",
            "previous_state": previous_state,
        }
        self._alerts.append(fuse_alert)
        self._alert_history.append(fuse_alert)

        # Execute fuse action
        if level == LEVEL_RED:
            result["action_taken"] = "STOP_RENDERING"
            result["message"] = (
                "RED fuse triggered: rendering stopped, "
                "cache preserved, escalation to DSHB+DSHE initiated"
            )
            self._execute_fuse_action("stop_rendering")
        elif level == LEVEL_BLUE:
            result["action_taken"] = "EMERGENCY_SHUTDOWN"
            result["message"] = (
                "BLUE fuse triggered: emergency shutdown initiated, "
                "all processes stopped, P2 alert + phone escalation"
            )
            self._execute_fuse_action("emergency_shutdown")

        self.logger.critical(
            "%s FUSE TRIGGERED: level=%s, state=%s, action=%s",
            STATUS_FATAL if level == LEVEL_BLUE else STATUS_CRITICAL,
            level, FUSE_OPEN, result["action_taken"]
        )

        return result

    def reset_fuse(self) -> Dict[str, Any]:
        """
        Reset fuse to CLOSED state (manual recovery).

        Returns:
            Dict with reset result.
        """
        previous_state = self._fuse_state
        result = {
            "success": True,
            "previous_state": previous_state,
            "fuse_state": FUSE_CLOSED,
            "message": "Fuse manually reset to CLOSED",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        self._fuse_state = FUSE_CLOSED
        self._fuse_level = None
        self._fuse_triggered_at = None

        self.logger.info(
            "%s Fuse reset: %s -> %s",
            STATUS_OK, previous_state, FUSE_CLOSED
        )

        return result

    def get_fuse_state(self) -> Dict[str, Any]:
        """
        Get current fuse state.

        Returns:
            Dict with fuse state, level, and timing info.
        """
        return {
            "fuse_state": self._fuse_state,
            "fuse_level": self._fuse_level,
            "fuse_triggered_at": (
                datetime.fromtimestamp(self._fuse_triggered_at).isoformat() + "Z"
                if self._fuse_triggered_at else None
            ),
            "fuse_open_duration_s": (
                round(time.time() - self._fuse_triggered_at, 2)
                if self._fuse_triggered_at else 0.0
            ),
        }

    # =========================================================================
    # Utility / Helper Methods
    # =========================================================================
    def clear_alerts(self):
        """Clear all active alerts (does not affect history)."""
        self._alerts = []

    def clear_alert_history(self):
        """Clear alert history."""
        self._alert_history = []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get monitor statistics.

        Returns:
            Dict with monitor stats.
        """
        return {
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "agent": AGENT,
            "total_alerts": len(self._alerts),
            "alert_count_by_level": {
                LEVEL_GREEN: sum(1 for a in self._alerts if a.get("level") == LEVEL_GREEN),
                LEVEL_YELLOW: sum(1 for a in self._alerts if a.get("level") == LEVEL_YELLOW),
                LEVEL_RED: sum(1 for a in self._alerts if a.get("level") == LEVEL_RED),
                LEVEL_BLUE: sum(1 for a in self._alerts if a.get("level") == LEVEL_BLUE),
            },
            "total_alert_history": len(self._alert_history),
            "fuse_state": self._fuse_state,
            "categories_monitored": list(self.thresholds.keys()),
        }

    def _get_metric(self, metrics: Optional[Dict], key: str,
                    default: Any = None) -> Any:
        """Get metric value from dict with case-insensitive fallback."""
        if metrics is None:
            return default
        if not isinstance(metrics, dict):
            return default
        if key in metrics:
            return metrics[key]
        # Try case-insensitive lookup
        lower_key = key.lower()
        for k, v in metrics.items():
            if k.lower() == lower_key:
                return v
        return default

    def _determine_level(self, value: float,
                         spec: Dict[str, Any]) -> str:
        """
        Determine threshold level for a value (higher = worse).

        Args:
            value: Current metric value.
            spec: Threshold spec dict with green/yellow/red/blue keys.

        Returns:
            Level string: "GREEN", "YELLOW", "RED", or "BLUE".
        """
        if value <= spec.get("green", float('inf')):
            return LEVEL_GREEN
        elif value <= spec.get("yellow", float('inf')):
            return LEVEL_YELLOW
        elif value <= spec.get("red", float('inf')):
            return LEVEL_RED
        else:
            return LEVEL_BLUE

    def _determine_inverted_level(self, value: float,
                                   spec: Dict[str, Any]) -> str:
        """
        Determine threshold level for inverted metrics (higher = better).

        For metrics like coverage rate where higher values are better:
            GREEN: value >= green_threshold
            YELLOW: value >= yellow_threshold (but < green)
            RED: value >= red_threshold (but < yellow)
            BLUE: value < red_threshold

        Args:
            value: Current metric value (higher is better).
            spec: Threshold spec dict.

        Returns:
            Level string.
        """
        if value >= spec.get("green", 0):
            return LEVEL_GREEN
        elif value >= spec.get("yellow", 0):
            return LEVEL_YELLOW
        elif value >= spec.get("red", 0):
            return LEVEL_RED
        else:
            return LEVEL_BLUE

    def _get_trigger_threshold(self, value: float,
                                spec: Dict[str, Any]) -> Optional[float]:
        """Get the threshold value that was just crossed (higher = worse)."""
        if value > spec.get("blue", float('inf')):
            return spec.get("blue")
        elif value > spec.get("red", float('inf')):
            return spec.get("red")
        elif value > spec.get("yellow", float('inf')):
            return spec.get("yellow")
        return spec.get("green")

    def _get_trigger_threshold_inverted(self, value: float,
                                         spec: Dict[str, Any]) -> Optional[float]:
        """Get the threshold value that was just crossed (inverted)."""
        if value < spec.get("red", 0):
            return spec.get("red")
        elif value < spec.get("yellow", 0):
            return spec.get("yellow")
        elif value < spec.get("green", 0):
            return spec.get("green")
        return None

    def _create_alert(self, level: str, category: str, metric: str,
                      value: Any, threshold: Optional[float]) -> Dict[str, Any]:
        """Create a standard alert dict."""
        return {
            "level": level,
            "category": category,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": f"{category}.{metric}: {value} exceeded threshold "
                       f"{threshold} (level={level})",
        }

    def _level_to_status(self, level: str) -> str:
        """Convert level to ASCII-safe status indicator."""
        mapping = {
            LEVEL_GREEN: STATUS_OK,
            LEVEL_YELLOW: STATUS_WARN,
            LEVEL_RED: STATUS_CRITICAL,
            LEVEL_BLUE: STATUS_FATAL,
        }
        return mapping.get(level, STATUS_UNKNOWN)

    def _auto_trigger_fuse(self, level: str):
        """
        Auto-trigger fuse if threshold reaches RED or BLUE level.

        Args:
            level: The current overall level.
        """
        if LEVEL_PRIORITY.get(level, 0) >= LEVEL_PRIORITY.get(LEVEL_RED, 0):
            if self._fuse_state == FUSE_CLOSED:
                self.trigger_fuse(level)

    def _execute_fuse_action(self, action: str):
        """
        Execute fuse action on engine if available.

        Args:
            action: Action type ("stop_rendering" or "emergency_shutdown").
        """
        if self.engine is None:
            return

        try:
            if action == "stop_rendering":
                # Try common engine methods
                if hasattr(self.engine, 'stop'):
                    self.engine.stop()
                elif hasattr(self.engine, 'pause'):
                    self.engine.pause()
                elif hasattr(self.engine, 'set_render_enabled'):
                    self.engine.set_render_enabled(False)
            elif action == "emergency_shutdown":
                if hasattr(self.engine, 'shutdown'):
                    self.engine.shutdown()
                elif hasattr(self.engine, 'stop'):
                    self.engine.stop()
                    if hasattr(self.engine, 'cleanup'):
                        self.engine.cleanup()
        except Exception as e:
            self.logger.error(
                "%s Failed to execute fuse action '%s' on engine: %s",
                STATUS_UNKNOWN, action, e
            )

    def _generate_summary(self, evaluation: Dict[str, Any]) -> str:
        """
        Generate human-readable summary string.

        Args:
            evaluation: Current evaluation dict.

        Returns:
            Summary string.
        """
        lines = []
        overall = evaluation.get("overall_level", LEVEL_GREEN)
        fuse_state = evaluation.get("fuse_state", FUSE_CLOSED)

        lines.append(f"OVERALL: {overall} ({self._level_to_status(overall)})")

        for category, result in evaluation.get("categories", {}).items():
            level = result.get("overall_level", result.get("level", LEVEL_GREEN))
            status = self._level_to_status(level)
            lines.append(f"  {category}: {level} {status}")

            # Add top metrics
            if "metrics" in result:
                for metric_name, metric_data in result["metrics"].items():
                    m_level = metric_data.get("level", LEVEL_GREEN)
                    if m_level != LEVEL_GREEN:
                        lines.append(
                            f"    {metric_name}: {m_level} "
                            f"(value={metric_data.get('value')})"
                        )
            elif "value" in result and result.get("level") != LEVEL_GREEN:
                lines.append(
                    f"    value={result.get('value')} "
                    f"({result.get('message', '')})"
                )

        if evaluation.get("alerts"):
            alert_levels = {}
            for alert in evaluation["alerts"]:
                lvl = alert.get("level", LEVEL_GREEN)
                alert_levels[lvl] = alert_levels.get(lvl, 0) + 1
            alert_summary = ", ".join(
                f"{lvl}={count}" for lvl, count in
                sorted(alert_levels.items(),
                       key=lambda x: LEVEL_PRIORITY.get(x[0], 0),
                       reverse=True)
                if lvl != LEVEL_GREEN
            )
            lines.append(f"  ALERTS: {alert_summary}")

        if fuse_state != FUSE_CLOSED:
            lines.append(f"  FUSE: {fuse_state} (level={self._fuse_level})")

        return " | ".join(lines)


# =============================================================================
# Sample / Demo Usage
# =============================================================================
def _demo_usage():
    """
    Demonstrate usage of EngineThresholdMonitor.

    This function is for testing and demonstration purposes only.
    Run with: python engine_threshold_monitor.py
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    print("=" * 70)
    print("EngineThresholdMonitor Demo")
    print(f"Schema: {SCHEMA_VERSION}")
    print("=" * 70)

    # 1. Create monitor with defaults
    monitor = EngineThresholdMonitor()
    print(f"\n{STATUS_OK} Monitor initialized with default thresholds")
    print(f"   Categories: {list(monitor.thresholds.keys())}")

    # 2. Check CPU
    print(f"\n--- CPU Check ---")
    cpu_report = {
        "process_cpu_pct": 15.3,
        "business_cpu_pct": 3.2,
        "per_core_max_pct": 85.0,
    }
    cpu_result = monitor.clear_alerts()
    cpu_result = monitor.check_cpu_baseline(cpu_report)
    print(f"   Overall: {cpu_result['overall_level']} "
          f"({cpu_result['overall_status']})")
    for name, data in cpu_result['metrics'].items():
        print(f"   {name}: {data['level']} "
              f"(value={data['value']}, Y={data.get('thresholds', {}).get('yellow')})")

    # 3. Check latency
    print(f"\n--- Latency Check ---")
    latency_data = {
        "p99_ms": 350.0,
        "p95_ms": 200.0,
        "median_ms": 15.0,
        "max_ms": 500.0,
        "avg_ms": 31.5,
    }
    latency_result = monitor.check_latency(latency_data)
    print(f"   Overall: {latency_result['overall_level']} "
          f"({latency_result['overall_status']})")
    for name, data in latency_result['metrics'].items():
        print(f"   {name}: {data['level']} (value={data['value']}ms)")

    # 4. Check render error rate
    print(f"\n--- Render Error Rate Check ---")
    error_result = monitor.check_render_error_rate(0, 250)
    print(f"   Level: {error_result['level']} "
          f"(rate={error_result['value']}%)")

    # 5. Check noise rate
    print(f"\n--- Noise Rate Check ---")
    noise_result = monitor.check_noise_rate(2, 11)
    print(f"   Level: {noise_result['level']} "
          f"(rate={noise_result['value']}%)")

    # 6. Check memory
    print(f"\n--- Memory Check ---")
    mem_result = monitor.check_memory(180.0)
    print(f"   Level: {mem_result['level']} "
          f"(RSS={mem_result['value']}MB)")

    # 7. Check indicator coverage
    print(f"\n--- Indicator Coverage Check ---")
    cov_result = monitor.check_indicator_coverage(67, 85)
    print(f"   Level: {cov_result['level']} "
          f"(coverage={cov_result['value']}%)")

    # 8. Comprehensive evaluation
    print(f"\n--- Comprehensive Evaluation ---")
    all_metrics = {
        "cpu": cpu_report,
        "latency": latency_data,
        "render_errors": 0,
        "render_total": 250,
        "noise_count": 2,
        "alert_total": 11,
        "rss_mb": 180.0,
        "real_charts": 67,
        "total_charts": 85,
    }
    evaluation = monitor.evaluate(all_metrics)
    print(f"\n{evaluation['summary']}")
    print(f"\n   Timestamp: {evaluation['timestamp']}")
    print(f"   Fuse State: {evaluation['fuse_state']}")
    print(f"   Active Alerts: {len(evaluation['alerts'])}")

    # 9. Get alerts
    print(f"\n--- Active Alerts ---")
    alerts = monitor.get_alerts()
    for alert in alerts:
        print(f"   [{alert['level']}] {alert['category']}.{alert['metric']}: "
              f"{alert['message']}")

    # 10. Fuse state
    print(f"\n--- Fuse State ---")
    fuse_state = monitor.get_fuse_state()
    print(f"   State: {fuse_state['fuse_state']}")
    print(f"   Level: {fuse_state['fuse_level']}")

    # 11. Monitor statistics
    print(f"\n--- Statistics ---")
    stats = monitor.get_statistics()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    # 12. Test fuse trigger
    print(f"\n--- Fuse Trigger Test ---")
    print(f"   Current fuse state: {monitor.get_fuse_state()['fuse_state']}")

    # Simulate critical condition
    print(f"\n   Simulating RED trigger (P99 > 500ms)...")
    critical_latency = {"p99_ms": 600.0, "p95_ms": 350.0, "median_ms": 50.0}
    monitor.clear_alerts()
    monitor.check_latency(critical_latency)
    print(f"   Fuse state after critical latency: "
          f"{monitor.get_fuse_state()['fuse_state']}")

    # Test manual fuse trigger
    print(f"\n   Manual trigger at RED...")
    fuse_result = monitor.trigger_fuse("RED")
    print(f"   Result: {fuse_result}")

    # Test fuse reset
    print(f"\n   Resetting fuse...")
    reset_result = monitor.reset_fuse()
    print(f"   Result: {reset_result}")

    # 13. Test with custom thresholds
    print(f"\n--- Custom Thresholds ---")
    custom_thresholds = {
        "thresholds": {
            "latency": {
                "p99_ms": {
                    "green": 100.0,
                    "yellow": 300.0,
                    "red": 500.0,
                    "blue": 1000.0,
                    "unit": "milliseconds"
                }
            }
        }
    }
    monitor2 = EngineThresholdMonitor()
    monitor2.load_thresholds(thresholds=custom_thresholds)
    print(f"   Custom p99 thresholds: {monitor2.thresholds['latency']['p99_ms']}")
    result = monitor2.check_latency({"p99_ms": 250.0})
    print(f"   p99=250ms: {result['metrics']['p99_ms']['level']}")

    print(f"\n{STATUS_OK} Demo complete.")


if __name__ == "__main__":
    _demo_usage()
