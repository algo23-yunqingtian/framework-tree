#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
noise_indicator_monitor.py
==========================
V88 Phase03 P1 - Noise Indicator Rendering Monitor

Purpose:
    Detect and monitor noise indicators that may cause rendering anomalies
    in chart outputs. Noise indicators are data series with high variability,
    structural gaps, outliers, or temporal anomalies that degrade chart quality.

Noise Categories:
    STATISTICAL  - High coefficient of variation, extreme variance
    STRUCTURAL   - Data gaps, zero clusters, discontinuities
    TEMPORAL     - Sudden spikes, time-based anomalies

Detection Algorithms:
    1. Coefficient of Variation (CV = |std/mean|): CV > 0.5 => HIGH noise
    2. Sudden Spike Detection: |change| > 3x rolling standard deviation
    3. Gap Detection: Missing/None data points in the series
    4. Outlier Detection: Values beyond 3x IQR (Tukey fences)
    5. Zero-Value Clustering: Consecutive zero runs >= threshold
    6. Discontinuity Detection: |change| > 5x median absolute difference

Compatibility:
    - indicator_cache schema: (metric, code, data_json)
    - series_cache schema: (id, indicator_id, indicator_id_mapped, commodity,
      date, value, source, imported_at)
    - Engine-agnostic: does not modify node_binding_engine.py
      (MD5: CD73DEAEEC54A7F1F8BDE92C1300A9DC)

Constraints:
    - Pure Python standard library + sqlite3
    - UTF-8 encoding
    - ASCII-safe output (no emoji that breaks GBK)
    - Testable independently

Usage:
    from noise_indicator_monitor import NoiseIndicatorMonitor
    monitor = NoiseIndicatorMonitor(noise_threshold=0.5)
    report = monitor.monitor_all_charts(engine)
    print(report.to_json())

Author: DSHE Agent
Version: 1.0.0
Date: 2026-10-15
Task: V88 Phase03 P1 DSHE Noise Indicator Rendering Monitor
"""

import json
import math
import os
import platform
import sqlite3
import statistics
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# =============================================================================
# Platform Setup (Windows GBK compatibility)
# =============================================================================

def _setup_platform():
    # type: () -> None
    """Configure platform-specific environment for encoding compatibility."""
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


_setup_platform()


# =============================================================================
# Noise Level and Category Enums
# =============================================================================

class NoiseLevel(Enum):
    """Enumeration of noise severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NoiseCategory(Enum):
    """Enumeration of noise categories."""
    STATISTICAL = "STATISTICAL"
    STRUCTURAL = "STRUCTURAL"
    TEMPORAL = "TEMPORAL"


# =============================================================================
# Data Containers
# =============================================================================

@dataclass
class NoiseMetrics:
    """
    Container for computed noise metrics on a data series.

    Attributes:
        cv: Coefficient of variation (|std/mean|)
        spike_count: Number of detected sudden spikes
        gap_count: Number of missing/None data points
        outlier_count: Number of IQR-based outliers
        zero_run_max: Maximum consecutive zeros run length
        zero_run_count: Number of zero runs (runs >= ZERO_RUN_THRESHOLD)
        discontinuity_count: Number of detected discontinuities
        mean: Mean value of the series
        std: Population standard deviation
        min: Minimum value
        max: Maximum value
        count: Total number of data points (including gaps)
        gap_ratio: Proportion of gaps (gap_count / count)
        noise_score: Composite noise score (0.0-100.0)
    """
    cv: float = 0.0
    spike_count: int = 0
    gap_count: int = 0
    outlier_count: int = 0
    zero_run_max: int = 0
    zero_run_count: int = 0
    discontinuity_count: int = 0
    mean: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0
    count: int = 0
    gap_ratio: float = 0.0
    noise_score: float = 0.0

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class NoiseReport:
    """
    Comprehensive noise report.

    Attributes:
        generated_at: Timestamp of report generation
        total_indicators: Total indicators monitored
        total_charts: Total charts monitored
        per_indicator: Dict of indicator_id -> noise analysis
        per_chart: Dict of chart_id -> noise analysis
        statistics: Overall noise statistics
        problematic_indicators: List of indicator IDs with HIGH or MEDIUM noise
        recommendations: List of actionable recommendations
    """
    generated_at: str = ""
    total_indicators: int = 0
    total_charts: int = 0
    per_indicator: Dict[str, Any] = field(default_factory=dict)
    per_chart: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    problematic_indicators: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """Convert to dictionary for JSON serialization."""
        return {
            "generated_at": self.generated_at,
            "total_indicators": self.total_indicators,
            "total_charts": self.total_charts,
            "per_indicator": self.per_indicator,
            "per_chart": self.per_chart,
            "statistics": self.statistics,
            "problematic_indicators": self.problematic_indicators,
            "recommendations": self.recommendations,
        }

    def to_json(self):
        # type: () -> str
        """Serialize to JSON string (ASCII-safe)."""
        return json.dumps(self.to_dict(), ensure_ascii=True, indent=2)


# =============================================================================
# Main Monitor Class
# =============================================================================

class NoiseIndicatorMonitor:
    """
    Noise Indicator Rendering Monitor for V88 Phase03 P1.

    Detects and classifies noise in indicator data series that may cause
    rendering anomalies in charts. Monitors per-indicator and per-chart
    noise levels to identify problematic indicators for remediation.

    Noise Categories:
        - STATISTICAL: High CV, extreme variance
        - STRUCTURAL: Gaps, zeros, discontinuities
        - TEMPORAL: Time-based anomalies (sudden changes, spikes)

    Compatibility:
        - Works with indicator_cache schema (metric, code, data_json)
        - Works with series_cache schema (indicator_id, date, value, ...)
        - Engine-agnostic: does not modify node_binding_engine.py
        - Testable independently

    Attributes:
        engine: Optional engine instance for accessing all indicators/charts
        noise_threshold: CV threshold for high noise classification
        detected_noise: Cache of detected noise metrics per indicator
        chart_results: Cache of per-chart noise results
        _noise_report: Cached noise report (lazily generated)

    Example:
        >>> monitor = NoiseIndicatorMonitor(noise_threshold=0.5)
        >>> report = monitor.monitor_all_charts(engine)
        >>> print(report.to_json())
    """

    # Classification thresholds
    CV_THRESHOLD_HIGH = 0.5        # CV > 0.5 => HIGH noise
    CV_THRESHOLD_MEDIUM = 0.25     # CV > 0.25 => MEDIUM noise
    SPIKE_STD_FACTOR = 3.0         # Spike = change > 3x rolling std
    OUTLIER_IQR_FACTOR = 3.0       # Outlier = beyond 3x IQR
    ZERO_RUN_THRESHOLD = 5         # Min consecutive zeros for zero cluster
    GAP_RATIO_HIGH = 0.3           # Gap ratio > 0.3 => structural noise
    DISCONTINUITY_FACTOR = 5.0     # Discontinuity = change > 5x median diff
    ROLLING_WINDOW = 5             # Window size for rolling std

    def __init__(self, engine=None, noise_threshold=0.5):
        # type: (Any, float) -> None
        """
        Initialize the noise monitor.

        Args:
            engine: Optional engine instance (e.g. NodeBindingEngine)
                    for accessing all indicators/charts. If None, the monitor
                    operates in standalone mode using provided data.
            noise_threshold: CV threshold for high noise classification.
                           Default 0.5 (CV > 0.5 => HIGH noise).
        """
        self.engine = engine
        self.noise_threshold = noise_threshold
        self.detected_noise = {}      # type: Dict[str, NoiseMetrics]
        self.chart_results = {}       # type: Dict[str, Dict[str, Any]]
        self._noise_report = None     # type: Optional[NoiseReport]

    # =========================================================================
    # Public API - Core Methods
    # =========================================================================

    def detect_noise_in_data(self, points):
        # type: (List[Any]) -> NoiseMetrics
        """
        Detect noise in a data series.

        Computes coefficient of variation, sudden spikes, gaps, outliers,
        and zero-value clustering for the given data points.

        Args:
            points: Data series. Can be:
                - List of numbers: [10.0, 10.5, ...]
                - List of dicts: [{"date": "...", "value": 10.0}, ...]
                - List of tuples: [("2015-01-05", 10.0), ...]
                - List with None for gaps: [10.0, None, 10.2, ...]
                - Mix of the above

        Returns:
            NoiseMetrics: Container with all computed noise metrics.

        Raises:
            ValueError: If points is None.
        """
        if points is None:
            raise ValueError("points cannot be None")

        metrics = NoiseMetrics()
        all_values = list(points)
        metrics.count = len(all_values)

        # Extract numeric values and identify gaps
        valid_values = []      # type: List[float]
        gap_count = 0

        for v in all_values:
            val = self._extract_value(v)
            if val is None:
                gap_count += 1
            else:
                valid_values.append(val)

        metrics.gap_count = gap_count
        metrics.gap_ratio = gap_count / metrics.count if metrics.count > 0 else 0.0

        if not valid_values:
            # All gaps or empty - return with zero metrics
            return metrics

        # Basic statistics
        metrics.min = min(valid_values)
        metrics.max = max(valid_values)
        metrics.mean = statistics.mean(valid_values)
        metrics.std = (
            statistics.pstdev(valid_values) if len(valid_values) > 1 else 0.0
        )

        # Coefficient of Variation
        epsilon = 1e-10
        if abs(metrics.mean) > epsilon:
            metrics.cv = abs(metrics.std / metrics.mean)
        else:
            # Mean near zero: all-zero => no noise, otherwise high relative variation
            metrics.cv = 0.0 if metrics.std < epsilon else 1.0

        # Spike detection
        metrics.spike_count = self._detect_spikes(all_values)

        # Outlier detection (IQR-based)
        metrics.outlier_count = self._detect_outliers(valid_values)

        # Zero clustering
        metrics.zero_run_max, metrics.zero_run_count = self._detect_zero_runs(
            all_values
        )

        # Discontinuity detection
        metrics.discontinuity_count = self._detect_discontinuities(all_values)

        # Composite noise score (0-100)
        metrics.noise_score = self._compute_noise_score(metrics)

        return metrics

    def classify_noise_level(self, points):
        # type: (List[Any]) -> NoiseLevel
        """
        Classify a data series as LOW, MEDIUM, or HIGH noise.

        Uses coefficient of variation and gap ratio as primary signals.

        Args:
            points: Data series (see detect_noise_in_data for accepted formats).

        Returns:
            NoiseLevel: LOW, MEDIUM, or HIGH.

        Raises:
            ValueError: If points is None.
        """
        if points is None:
            raise ValueError("points cannot be None")
        metrics = self.detect_noise_in_data(points)
        return self._classify_from_metrics(metrics)

    def monitor_chart_render(self, chart_id, render_result):
        # type: (str, Any) -> Dict[str, Any]
        """
        Monitor a single chart's render result for noise issues.

        Inspects the render result for noise indicators. The render_result
        can be a dict with keys like 'points', 'series', 'data', or 'values',
        or it can be a list of points.

        Args:
            chart_id: Unique identifier for the chart.
            render_result: Render result data. Supported formats:
                - Dict with 'points': single series
                - Dict with 'series': list of series dicts
                - List of points (treated as single series)
                - Any object with .points attribute

        Returns:
            Dict with chart noise analysis including:
                - chart_id: str
                - noise_level: str (LOW/MEDIUM/HIGH)
                - noise_category: List[str]
                - metrics: Aggregated metrics
                - issues: List[str]
                - recommendations: List[str]
                - series_analyses: List[Dict] per-series analysis

        Raises:
            ValueError: If render_result is None.
        """
        if render_result is None:
            raise ValueError("render_result cannot be None")

        result = {
            "chart_id": chart_id,
            "noise_level": NoiseLevel.LOW.value,
            "noise_category": [],
            "metrics": {},
            "issues": [],
            "recommendations": [],
            "series_analyses": [],
        }  # type: Dict[str, Any]

        # Extract series from render result
        series_data = self._extract_series_from_render_result(render_result)

        if not series_data:
            # No data - HIGH noise (structural issue)
            result["noise_level"] = NoiseLevel.HIGH.value
            result["noise_category"] = [NoiseCategory.STRUCTURAL.value]
            result["issues"] = ["No data points in render result"]
            result["recommendations"] = ["Verify data source availability"]
            self.chart_results[chart_id] = result
            return result

        # Analyze each series
        all_metrics = []  # type: List[NoiseMetrics]

        for series_id, pts in series_data:
            m = self.detect_noise_in_data(pts)
            level = self._classify_from_metrics(m)
            category = self._categorize_noise(m)
            issues = self._extract_issues(m)

            all_metrics.append(m)

            result["series_analyses"].append({
                "series_id": series_id,
                "noise_level": level.value,
                "noise_category": [c.value for c in category],
                "metrics": m.to_dict(),
                "issues": issues,
            })

        # Aggregate: worst level wins
        worst_metrics = max(
            all_metrics,
            key=lambda m: self._severity_rank(self._classify_from_metrics(m))
        )
        result["noise_level"] = self._classify_from_metrics(worst_metrics).value
        result["noise_category"] = sorted({
            c.value for m in all_metrics for c in self._categorize_noise(m)
        })
        result["metrics"] = {
            "avg_cv": sum(m.cv for m in all_metrics) / len(all_metrics),
            "max_cv": max(m.cv for m in all_metrics),
            "total_spikes": sum(m.spike_count for m in all_metrics),
            "total_gaps": sum(m.gap_count for m in all_metrics),
            "total_outliers": sum(m.outlier_count for m in all_metrics),
            "total_points": sum(m.count for m in all_metrics),
        }
        result["issues"] = [
            issue for m in all_metrics for issue in self._extract_issues(m)
        ]
        result["recommendations"] = self._recommendations_from_metrics(all_metrics)

        self.chart_results[chart_id] = result
        return result

    def monitor_all_charts(self, engine=None):
        # type: (Any) -> NoiseReport
        """
        Monitor all charts from the engine and generate a comprehensive noise report.

        If engine is provided, it overrides the engine set in __init__.
        The engine can be:
            - A NodeBindingEngine instance with .indicators/.charts or
              .get_indicators()/.get_charts() methods
            - A dict-like with indicators and/or charts
            - A string path to a SQLite database (auto-detects schema)
            - None: generates report from previously monitored charts only

        Args:
            engine: Optional engine instance, dict, or DB path string.
                   If None, uses self.engine.

        Returns:
            NoiseReport: Comprehensive noise report.
        """
        use_engine = engine if engine is not None else self.engine

        report = NoiseReport()
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if use_engine is None:
            # No engine - generate from cached chart results
            report.total_charts = len(self.chart_results)
            report.per_chart = dict(self.chart_results)
            report.statistics = self._compute_overall_stats(report.per_chart, {})
            report.problematic_indicators = self._find_problematic(report.per_chart)
            report.recommendations = self._generate_recommendations(report)
            self._noise_report = report
            return report

        # If engine is a string, treat as DB path
        if isinstance(use_engine, str):
            db_path = use_engine
            schema = self.detect_db_schema(db_path)
            if schema:
                indicators = self._load_all_from_db(db_path, schema)
                report.total_indicators = len(indicators)
                for ind_id, pts in indicators.items():
                    try:
                        m = self.detect_noise_in_data(pts)
                        level = self._classify_from_metrics(m)
                        category = self._categorize_noise(m)
                        self.detected_noise[ind_id] = m
                        report.per_indicator[ind_id] = {
                            "indicator_id": ind_id,
                            "noise_level": level.value,
                            "noise_category": [c.value for c in category],
                            "metrics": m.to_dict(),
                            "issues": self._extract_issues(m),
                        }
                    except Exception as e:
                        report.per_indicator[ind_id] = {
                            "indicator_id": ind_id,
                            "noise_level": NoiseLevel.HIGH.value,
                            "noise_category": [NoiseCategory.STRUCTURAL.value],
                            "metrics": {},
                            "issues": ["Monitoring error: %s" % str(e)],
                        }
            report.total_charts = len(self.chart_results)
            report.per_chart = dict(self.chart_results)
            report.statistics = self._compute_overall_stats(
                report.per_chart, report.per_indicator
            )
            report.problematic_indicators = self._find_problematic(
                report.per_indicator
            )
            report.recommendations = self._generate_recommendations(report)
            self._noise_report = report
            return report

        # Get indicators from engine
        indicators = self._get_engine_indicators(use_engine)

        # Get charts from engine
        charts = self._get_engine_charts(use_engine)

        # If no direct indicators/charts found, try engine's DB path
        if not indicators and not charts:
            db_path = self._get_engine_db_path(use_engine)
            if db_path:
                schema = self.detect_db_schema(db_path)
                if schema:
                    indicators = self._load_all_from_db(db_path, schema)

        # Monitor each chart
        for chart_id, render_data in charts.items():
            try:
                result = self.monitor_chart_render(chart_id, render_data)
                report.per_chart[chart_id] = result
            except Exception as e:
                report.per_chart[chart_id] = {
                    "chart_id": chart_id,
                    "noise_level": NoiseLevel.HIGH.value,
                    "noise_category": [NoiseCategory.STRUCTURAL.value],
                    "metrics": {},
                    "issues": ["Monitoring error: %s" % str(e)],
                    "recommendations": ["Investigate monitoring exception"],
                }

        # Monitor each indicator
        for indicator_id, indicator_data in indicators.items():
            try:
                pts = self._extract_indicator_points(indicator_data)
                m = self.detect_noise_in_data(pts)
                level = self._classify_from_metrics(m)
                category = self._categorize_noise(m)
                self.detected_noise[indicator_id] = m
                report.per_indicator[indicator_id] = {
                    "indicator_id": indicator_id,
                    "noise_level": level.value,
                    "noise_category": [c.value for c in category],
                    "metrics": m.to_dict(),
                    "issues": self._extract_issues(m),
                }
            except Exception as e:
                report.per_indicator[indicator_id] = {
                    "indicator_id": indicator_id,
                    "noise_level": NoiseLevel.HIGH.value,
                    "noise_category": [NoiseCategory.STRUCTURAL.value],
                    "metrics": {},
                    "issues": ["Monitoring error: %s" % str(e)],
                }

        report.total_indicators = len(report.per_indicator)
        report.total_charts = len(report.per_chart)
        report.statistics = self._compute_overall_stats(
            report.per_chart, report.per_indicator
        )
        report.problematic_indicators = self._find_problematic(
            report.per_indicator
        )
        report.recommendations = self._generate_recommendations(report)

        self._noise_report = report
        return report

    def get_noise_report(self):
        # type: () -> NoiseReport
        """
        Generate (or return cached) comprehensive noise report.

        If monitor_all_charts has been called, returns the cached report.
        Otherwise, calls monitor_all_charts with current engine state.

        Returns:
            NoiseReport: Comprehensive noise report.
        """
        if self._noise_report is not None:
            return self._noise_report
        return self.monitor_all_charts()

    def is_noisy_indicator(self, indicator_id, points):
        # type: (str, List[Any]) -> bool
        """
        Check if an indicator is noisy based on its data points.

        Args:
            indicator_id: Identifier for the indicator.
            points: Data points of the indicator.

        Returns:
            bool: True if the indicator is classified as MEDIUM or HIGH noise.

        Raises:
            ValueError: If points is None.
        """
        if points is None:
            raise ValueError("points cannot be None")

        m = self.detect_noise_in_data(points)
        self.detected_noise[indicator_id] = m
        level = self._classify_from_metrics(m)
        return level in (NoiseLevel.MEDIUM, NoiseLevel.HIGH)

    def calculate_noise_metrics(self, points):
        # type: (List[Any]) -> Dict[str, Any]
        """
        Calculate noise metrics for a data series.

        Args:
            points: Data points to analyze.

        Returns:
            Dict with: cv, spike_count, gap_count, outlier_count,
                     zero_run_max, zero_run_count, discontinuity_count,
                     mean, std, min, max, count, gap_ratio, noise_score.

        Raises:
            ValueError: If points is None.
        """
        if points is None:
            raise ValueError("points cannot be None")

        m = self.detect_noise_in_data(points)
        return m.to_dict()

    # =========================================================================
    # Public API - Database Compatibility Methods
    # =========================================================================

    @staticmethod
    def detect_db_schema(db_path):
        # type: (str) -> Optional[str]
        """
        Detect which schema the database uses.

        Args:
            db_path: Path to SQLite database file.

        Returns:
            'indicator_cache', 'series_cache', or None.
        """
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cur.fetchall()}
            conn.close()

            if "indicator_cache" in tables:
                return "indicator_cache"
            elif "series_cache" in tables:
                return "series_cache"
            return None
        except sqlite3.Error:
            return None

    @staticmethod
    def load_from_indicator_cache(db_path, indicator_id):
        # type: (str, str) -> List[Dict[str, Any]]
        """
        Load indicator data from indicator_cache schema.

        Schema: (metric, code, data_json)
        data_json format:
            {"name": "...", "unit": "...", "points": [{"date": "...", "value": ...}]}

        Args:
            db_path: Path to SQLite database file.
            indicator_id: Indicator ID to query (matched against metric or code).

        Returns:
            List of point dicts: [{"date": "...", "value": ...}, ...]
        """
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                "SELECT data_json FROM indicator_cache "
                "WHERE metric=? OR code=?",
                (indicator_id, indicator_id)
            )
            row = cur.fetchone()
            conn.close()

            if row:
                d = json.loads(row[0])
                return d.get("points", [])
            return []
        except (sqlite3.Error, json.JSONDecodeError):
            return []

    @staticmethod
    def load_from_series_cache(db_path, indicator_id, commodity=None,
                               use_mapped=False):
        # type: (str, str, Optional[str], bool) -> List[Dict[str, Any]]
        """
        Load indicator data from series_cache schema.

        Schema: (id, indicator_id, indicator_id_mapped, commodity, date,
                 value, source, imported_at)

        Args:
            db_path: Path to SQLite database file.
            indicator_id: Indicator ID to query.
            commodity: Optional commodity filter.
            use_mapped: If True, query by indicator_id_mapped instead.

        Returns:
            List of point dicts: [{"date": "...", "value": ...}, ...]
        """
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()

            col = "indicator_id_mapped" if use_mapped else "indicator_id"
            if commodity:
                cur.execute(
                    "SELECT date, value FROM series_cache "
                    "WHERE %s=? AND commodity=? ORDER BY date" % col,
                    (indicator_id, commodity)
                )
            else:
                cur.execute(
                    "SELECT date, value FROM series_cache "
                    "WHERE %s=? ORDER BY date" % col,
                    (indicator_id,)
                )
            rows = cur.fetchall()
            conn.close()

            return [
                {"date": r[0], "value": r[1]}
                for r in rows
                if r[1] is not None
            ]
        except sqlite3.Error:
            return []

    def load_from_db(self, db_path, indicator_id, schema=None, commodity=None):
        # type: (str, str, Optional[str], Optional[str]) -> List[Dict[str, Any]]
        """
        Load indicator data from database with automatic schema detection.

        Args:
            db_path: Path to SQLite database file.
            indicator_id: Indicator ID to query.
            schema: Schema type ('indicator_cache' or 'series_cache').
                   Auto-detected if None.
            commodity: Optional commodity filter (for series_cache).

        Returns:
            List of point dicts: [{"date": "...", "value": ...}, ...]
        """
        if schema is None:
            schema = self.detect_db_schema(db_path)

        if schema == "indicator_cache":
            return self.load_from_indicator_cache(db_path, indicator_id)
        elif schema == "series_cache":
            return self.load_from_series_cache(db_path, indicator_id, commodity)
        return []

    def monitor_indicator_from_db(self, db_path, indicator_id, schema=None,
                                  commodity=None):
        # type: (str, str, Optional[str], Optional[str]) -> Dict[str, Any]
        """
        Load and monitor a single indicator from database.

        Args:
            db_path: Path to SQLite database file.
            indicator_id: Indicator ID to monitor.
            schema: Schema type. Auto-detected if None.
            commodity: Optional commodity filter.

        Returns:
            Dict with indicator noise analysis.
        """
        pts = self.load_from_db(db_path, indicator_id, schema=schema,
                                commodity=commodity)
        m = self.detect_noise_in_data(pts)
        level = self._classify_from_metrics(m)
        category = self._categorize_noise(m)
        self.detected_noise[indicator_id] = m
        return {
            "indicator_id": indicator_id,
            "noise_level": level.value,
            "noise_category": [c.value for c in category],
            "metrics": m.to_dict(),
            "issues": self._extract_issues(m),
        }

    def monitor_all_from_database(self, db_path, schema=None):
        # type: (str, Optional[str]) -> NoiseReport
        """
        Monitor all indicators from a database.

        Args:
            db_path: Path to SQLite database file.
            schema: Schema type. Auto-detected if None.

        Returns:
            NoiseReport: Comprehensive noise report.
        """
        if schema is None:
            schema = self.detect_db_schema(db_path)

        if not schema:
            report = NoiseReport()
            report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report.recommendations = ["Cannot detect DB schema"]
            self._noise_report = report
            return report

        indicators = self._load_all_from_db(db_path, schema)

        report = NoiseReport()
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.total_indicators = len(indicators)
        report.total_charts = 0

        for ind_id, pts in indicators.items():
            try:
                m = self.detect_noise_in_data(pts)
                level = self._classify_from_metrics(m)
                category = self._categorize_noise(m)
                self.detected_noise[ind_id] = m
                report.per_indicator[ind_id] = {
                    "indicator_id": ind_id,
                    "noise_level": level.value,
                    "noise_category": [c.value for c in category],
                    "metrics": m.to_dict(),
                    "issues": self._extract_issues(m),
                }
            except Exception as e:
                report.per_indicator[ind_id] = {
                    "indicator_id": ind_id,
                    "noise_level": NoiseLevel.HIGH.value,
                    "noise_category": [NoiseCategory.STRUCTURAL.value],
                    "metrics": {},
                    "issues": ["Monitoring error: %s" % str(e)],
                }

        report.statistics = self._compute_overall_stats({}, report.per_indicator)
        report.problematic_indicators = self._find_problematic(report.per_indicator)
        report.recommendations = self._generate_recommendations(report)
        self._noise_report = report
        return report

    # =========================================================================
    # Public API - Persistence Methods
    # =========================================================================

    def save_report_to_db(self, db_path, table_name="noise_reports"):
        # type: (str, str) -> str
        """
        Save noise report to SQLite database.

        Args:
            db_path: Path to SQLite database file.
            table_name: Name of the table to create/use.

        Returns:
            str: The db path where the report was saved.
        """
        if self._noise_report is None:
            self._noise_report = self.monitor_all_charts()

        report_json = json.dumps(self._noise_report.to_dict(), ensure_ascii=True)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS %s (" % table_name +
            "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
            "generated_at TEXT NOT NULL, " +
            "total_indicators INTEGER, " +
            "total_charts INTEGER, " +
            "report_json TEXT NOT NULL, " +
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        cursor.execute(
            "INSERT INTO %s (generated_at, total_indicators, total_charts, "
            "report_json) VALUES (?, ?, ?, ?)" % table_name,
            (
                self._noise_report.generated_at,
                self._noise_report.total_indicators,
                self._noise_report.total_charts,
                report_json,
            )
        )
        conn.commit()
        conn.close()

        return str(db_path)

    def load_report_from_db(self, db_path, table_name="noise_reports",
                            latest_only=True):
        # type: (str, str, bool) -> List[Dict[str, Any]]
        """
        Load noise report(s) from SQLite database.

        Args:
            db_path: Path to SQLite database file.
            table_name: Name of the table.
            latest_only: If True, return only the most recent report.

        Returns:
            List of dicts with report data.
        """
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if latest_only:
                cursor.execute(
                    "SELECT * FROM %s ORDER BY id DESC LIMIT 1" % table_name
                )
                row = cursor.fetchone()
                if row is None:
                    return []
                return [{
                    "row": dict(row),
                    "report": json.loads(row["report_json"]),
                }]
            else:
                cursor.execute(
                    "SELECT * FROM %s ORDER BY id ASC" % table_name
                )
                rows = cursor.fetchall()
                return [
                    {
                        "row": dict(r),
                        "report": json.loads(r["report_json"]),
                    }
                    for r in rows
                ]
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    # =========================================================================
    # Internal Helpers - Noise Detection Algorithms
    # =========================================================================

    def _classify_from_metrics(self, metrics):
        # type: (NoiseMetrics) -> NoiseLevel
        """Classify noise level from computed metrics."""
        # If no data points at all, it's HIGH noise (structural issue)
        if metrics.count == 0:
            return NoiseLevel.HIGH

        # HIGH noise criteria (any one is sufficient)
        if metrics.cv > self.noise_threshold:
            return NoiseLevel.HIGH
        if metrics.gap_ratio > self.GAP_RATIO_HIGH:
            return NoiseLevel.HIGH
        if metrics.spike_count > 5:
            return NoiseLevel.HIGH
        if metrics.outlier_count > 5:
            return NoiseLevel.HIGH
        if metrics.zero_run_max >= 10:
            return NoiseLevel.HIGH

        # MEDIUM noise criteria
        if metrics.cv > self.CV_THRESHOLD_MEDIUM:
            return NoiseLevel.MEDIUM
        if metrics.gap_ratio > 0.1:
            return NoiseLevel.MEDIUM
        if metrics.spike_count >= 2:
            return NoiseLevel.MEDIUM
        if metrics.outlier_count >= 2:
            return NoiseLevel.MEDIUM
        if metrics.zero_run_max >= self.ZERO_RUN_THRESHOLD:
            return NoiseLevel.MEDIUM

        return NoiseLevel.LOW

    def _categorize_noise(self, metrics):
        # type: (NoiseMetrics) -> List[NoiseCategory]
        """Categorize noise into STATISTICAL/STRUCTURAL/TEMPORAL."""
        categories = []  # type: List[NoiseCategory]

        # STATISTICAL: High CV, extreme variance
        if metrics.cv > self.CV_THRESHOLD_MEDIUM:
            categories.append(NoiseCategory.STATISTICAL)

        # STRUCTURAL: Gaps, zeros, discontinuities
        if (metrics.gap_count > 0 or
            metrics.zero_run_count > 0 or
            metrics.discontinuity_count > 0):
            categories.append(NoiseCategory.STRUCTURAL)

        # TEMPORAL: Sudden changes, spikes
        if metrics.spike_count > 0:
            categories.append(NoiseCategory.TEMPORAL)

        return categories

    def _extract_issues(self, metrics):
        # type: (NoiseMetrics) -> List[str]
        """Extract human-readable issues from metrics."""
        issues = []  # type: List[str]

        if metrics.cv > self.noise_threshold:
            issues.append(
                "High CV: %.4f (threshold: %.2f)"
                % (metrics.cv, self.noise_threshold)
            )
        elif metrics.cv > self.CV_THRESHOLD_MEDIUM:
            issues.append("Elevated CV: %.4f" % metrics.cv)

        if metrics.gap_ratio > 0.3:
            issues.append(
                "High gap ratio: %.1f%% (%d/%d)"
                % (metrics.gap_ratio * 100, metrics.gap_count, metrics.count)
            )
        elif metrics.gap_count > 0:
            issues.append(
                "Gaps detected: %d/%d" % (metrics.gap_count, metrics.count)
            )

        if metrics.spike_count > 0:
            issues.append("Sudden spikes detected: %d" % metrics.spike_count)

        if metrics.outlier_count > 0:
            issues.append("Outliers detected: %d" % metrics.outlier_count)

        if metrics.zero_run_max >= self.ZERO_RUN_THRESHOLD:
            issues.append(
                "Zero clustering: max run of %d consecutive zeros"
                % metrics.zero_run_max
            )

        if metrics.discontinuity_count > 0:
            issues.append(
                "Discontinuities detected: %d" % metrics.discontinuity_count
            )

        return issues

    def _compute_noise_score(self, metrics):
        # type: (NoiseMetrics) -> float
        """
        Compute composite noise score (0.0-100.0).

        Weighted combination of all noise signals:
            CV:          0-30 points
            Gap ratio:   0-20 points
            Spikes:      0-15 points
            Outliers:    0-15 points
            Zeros:       0-10 points
            Discont.:    0-10 points
        """
        score = 0.0

        # CV contribution (up to 30 points)
        if metrics.count > 0:
            cv_ratio = min(
                metrics.cv / max(self.noise_threshold, 1e-10), 2.0
            )
            score += cv_ratio * 15.0

        # Gap ratio contribution (up to 20 points)
        gap_ratio = min(
            metrics.gap_ratio / max(self.GAP_RATIO_HIGH, 1e-10), 2.0
        )
        score += gap_ratio * 10.0

        # Spike contribution (up to 15 points)
        spike_ratio = min(metrics.spike_count / 5.0, 2.0)
        score += spike_ratio * 7.5

        # Outlier contribution (up to 15 points)
        outlier_ratio = min(metrics.outlier_count / 5.0, 2.0)
        score += outlier_ratio * 7.5

        # Zero clustering contribution (up to 10 points)
        if metrics.zero_run_max >= 10:
            score += 10.0
        elif metrics.zero_run_max >= self.ZERO_RUN_THRESHOLD:
            score += 5.0

        # Discontinuity contribution (up to 10 points)
        disc_ratio = min(metrics.discontinuity_count / 3.0, 1.0)
        score += disc_ratio * 10.0

        return min(score, 100.0)

    @staticmethod
    def _extract_value(item):
        # type: (Any) -> Optional[float]
        """
        Extract numeric value from a single data point item.

        Handles: None, int, float, dict, tuple/list, objects with .value.

        Args:
            item: A single data point (any supported format).

        Returns:
            float value or None if the item represents a gap.
        """
        if item is None:
            return None
        if isinstance(item, bool):
            return float(item)
        if isinstance(item, (int, float)):
            if isinstance(item, float) and math.isnan(item):
                return None
            return float(item)
        if isinstance(item, dict):
            val = item.get("value") or item.get("v") or item.get("data")
            if val is None:
                return None
            try:
                return float(val)
            except (TypeError, ValueError):
                return None
        if isinstance(item, (list, tuple)):
            if len(item) >= 2 and item[1] is not None:
                try:
                    return float(item[1])
                except (TypeError, ValueError):
                    return None
            return None
        # Object with .value attribute
        val = getattr(item, 'value', None)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                return None
        return None

    def _detect_spikes(self, points):
        # type: (List[Any]) -> int
        """
        Detect sudden spikes: value change > SPIKE_STD_FACTOR * rolling std.

        Uses a rolling window of ROLLING_WINDOW points before the current
        position (excluding the current value) to compute local std.
        This prevents the spike itself from inflating the detection threshold.

        Args:
            points: Data series (any format accepted by detect_noise_in_data).

        Returns:
            int: Number of detected spikes.
        """
        if len(points) < 3:
            return 0

        values = [self._extract_value(p) for p in points]
        window = self.ROLLING_WINDOW
        spike_count = 0

        for i in range(1, len(values)):
            if values[i] is None or values[i - 1] is None:
                continue

            # Compute rolling std of previous window (not including current)
            start = max(0, i - window)
            window_vals = [
                values[j] for j in range(start, i)
                if values[j] is not None
            ]

            if len(window_vals) < 2:
                continue

            local_std = statistics.pstdev(window_vals)
            change = abs(values[i] - values[i - 1])

            if local_std > 1e-10 and change > self.SPIKE_STD_FACTOR * local_std:
                spike_count += 1

        return spike_count

    def _detect_outliers(self, values):
        # type: (List[float]) -> int
        """
        Detect outliers using IQR method: values beyond 3x IQR.

        Uses Tukey's fences with a factor of 3 (extreme outliers).
        Quartiles computed via linear interpolation.

        Args:
            values: List of numeric values (gaps already filtered out).

        Returns:
            int: Number of detected outliers.
        """
        if len(values) < 4:
            return 0

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        def _quantile(q):
            # type: (float) -> float
            """Calculate quantile using linear interpolation."""
            idx = q * (n - 1)
            lo = int(math.floor(idx))
            hi = int(math.ceil(idx))
            if lo == hi:
                return sorted_vals[lo]
            frac = idx - lo
            return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac

        q1 = _quantile(0.25)
        q3 = _quantile(0.75)
        iqr = q3 - q1

        if iqr <= 0:
            return 0

        lower_bound = q1 - self.OUTLIER_IQR_FACTOR * iqr
        upper_bound = q3 + self.OUTLIER_IQR_FACTOR * iqr

        outlier_count = 0
        for v in values:
            if v < lower_bound or v > upper_bound:
                outlier_count += 1

        return outlier_count

    def _detect_zero_runs(self, points):
        # type: (List[Any]) -> Tuple[int, int]
        """
        Detect zero-value clustering.

        A "run" is a consecutive sequence of zeros of length >= ZERO_RUN_THRESHOLD.
        None values (gaps) break a run.

        Args:
            points: Data series (any format).

        Returns:
            Tuple of (max_run_length, count_of_runs).
        """
        max_run = 0
        run_count = 0
        current_run = 0

        for p in points:
            val = self._extract_value(p)

            if val is None:
                # Gap - finalize current run
                if current_run >= self.ZERO_RUN_THRESHOLD:
                    run_count += 1
                    max_run = max(max_run, current_run)
                current_run = 0
            elif val == 0.0:
                current_run += 1
            else:
                if current_run >= self.ZERO_RUN_THRESHOLD:
                    run_count += 1
                    max_run = max(max_run, current_run)
                current_run = 0

        # Finalize last run
        if current_run >= self.ZERO_RUN_THRESHOLD:
            run_count += 1
            max_run = max(max_run, current_run)

        return max_run, run_count

    def _detect_discontinuities(self, points):
        # type: (List[Any]) -> int
        """
        Detect discontinuities: sudden large jumps in value.

        A discontinuity is when |v[i] - v[i-1]| > DISCONTINUITY_FACTOR *
        median of absolute differences.

        Args:
            points: Data series (any format).

        Returns:
            int: Number of detected discontinuities.
        """
        if len(points) < 3:
            return 0

        values = [self._extract_value(p) for p in points]

        # Compute absolute differences between consecutive non-None values
        differences = []  # type: List[float]
        for i in range(1, len(values)):
            if values[i] is not None and values[i - 1] is not None:
                differences.append(abs(values[i] - values[i - 1]))

        if len(differences) < 3:
            return 0

        median_diff = statistics.median(differences)
        if median_diff <= 1e-10:
            # All differences near zero - no discontinuities
            return 0

        threshold = self.DISCONTINUITY_FACTOR * median_diff
        count = 0
        for i in range(1, len(values)):
            if values[i] is not None and values[i - 1] is not None:
                if abs(values[i] - values[i - 1]) > threshold:
                    count += 1

        return count

    # =========================================================================
    # Internal Helpers - Data Extraction
    # =========================================================================

    def _extract_series_from_render_result(self, render_result):
        # type: (Any) -> List[Tuple[str, List[Any]]]
        """
        Extract series data from various render_result formats.

        Supported formats:
            - List: treated as single series with id "series_0"
            - Dict with 'series': list of series, each with 'points' or 'data'
            - Dict with 'points': single series
            - Dict with 'data': single series (if data is a list)
            - Dict with 'values': single series
            - Nested: {"data": {"series": [...]}}
            - Any object with .points attribute

        Args:
            render_result: The render result to extract series from.

        Returns:
            List of (series_id, points) tuples.
        """
        series_list = []  # type: List[Tuple[str, List[Any]]]

        if render_result is None:
            return series_list

        if isinstance(render_result, list):
            # Single series
            series_list.append(("series_0", render_result))
        elif isinstance(render_result, dict):
            # Check for 'series' key (multi-series)
            series_val = render_result.get('series')
            if series_val is not None and isinstance(series_val, (list, tuple)):
                for i, s in enumerate(series_val):
                    sid = (
                        s.get('id', "series_%d" % i)
                        if isinstance(s, dict) else "series_%d" % i
                    )
                    if isinstance(s, dict):
                        pts = (
                            s.get('points') or
                            s.get('data') or
                            s.get('values') or
                            s.get('series_data')
                        )
                    else:
                        pts = s
                    series_list.append((sid, pts if pts is not None else []))
            else:
                # Single series - check common keys
                pts = None
                for key in ('points', 'data', 'values', 'series_data',
                            'rendered_points'):
                    if key in render_result:
                        pts = render_result[key]
                        break

                # If 'data' is a dict with 'points', use that
                if pts is None and 'data' in render_result:
                    d = render_result['data']
                    if isinstance(d, dict) and 'points' in d:
                        pts = d['points']
                    elif isinstance(d, list):
                        pts = d

                # If still None, try 'series' as a single series object
                if pts is None and 'series' in render_result:
                    s = render_result['series']
                    if isinstance(s, dict):
                        pts = (
                            s.get('points') or
                            s.get('data') or
                            s.get('values')
                        )
                    elif isinstance(s, list):
                        pts = s

                series_list.append(("series_0", pts if pts is not None else []))
        elif hasattr(render_result, 'points'):
            try:
                series_list.append(("series_0", list(render_result.points)))
            except (TypeError, AttributeError):
                series_list.append(("series_0", []))
        else:
            # Try to convert to list
            try:
                series_list.append(("series_0", list(render_result)))
            except TypeError:
                series_list.append(("series_0", []))

        return series_list

    def _extract_indicator_points(self, indicator_data):
        # type: (Any) -> List[Any]
        """
        Extract points from indicator data.

        Supports indicator_cache and series_cache schemas, plus direct formats.

        Args:
            indicator_data: Indicator data in various formats.

        Returns:
            List of data points.
        """
        if indicator_data is None:
            return []

        # Direct list
        if isinstance(indicator_data, (list, tuple)):
            return list(indicator_data)

        # Dict formats
        if isinstance(indicator_data, dict):
            for key in ('points', 'values', 'data', 'series', 'series_data',
                        'rendered_points'):
                if key in indicator_data:
                    v = indicator_data[key]
                    if isinstance(v, (list, tuple)):
                        return list(v)
                    elif isinstance(v, dict):
                        for sub_key in ('points', 'values', 'data'):
                            if sub_key in v and isinstance(v[sub_key],
                                                           (list, tuple)):
                                return list(v[sub_key])
            return []

        # Object with .points or .values
        for attr in ('points', 'values', 'data'):
            if hasattr(indicator_data, attr):
                val = getattr(indicator_data, attr)
                if isinstance(val, (list, tuple)):
                    return list(val)

        return []

    def _get_engine_indicators(self, engine):
        # type: (Any) -> Dict[str, Any]
        """
        Get indicators from engine.

        Supports various engine interfaces:
            - engine.indicators: dict of indicator_id -> data
            - engine.get_indicators(): dict
            - engine.indicator_cache: dict
            - engine.series_cache: dict

        Args:
            engine: Engine object.

        Returns:
            Dict of indicator_id -> indicator data.
        """
        if engine is None:
            return {}

        # Try direct attributes
        for attr in ('indicators', 'indicator_cache', 'series_cache',
                     'indicator_data', 'all_indicators'):
            val = getattr(engine, attr, None)
            if val is not None and hasattr(val, 'items'):
                return dict(val)

        # Try method calls
        for method in ('get_indicators', 'list_indicators',
                       'get_all_indicators', 'get_indicator_data'):
            fn = getattr(engine, method, None)
            if callable(fn):
                try:
                    result = fn()
                    if isinstance(result, dict):
                        return result
                except Exception:
                    continue

        # Try .items() iteration
        if hasattr(engine, 'items'):
            try:
                return {k: v for k, v in engine.items()}
            except Exception:
                pass

        return {}

    def _get_engine_charts(self, engine):
        # type: (Any) -> Dict[str, Any]
        """
        Get charts from engine.

        Supports various engine interfaces:
            - engine.charts: dict of chart_id -> render data
            - engine.get_charts(): dict
            - engine.render_results: dict
            - engine.get_render_results(): dict

        Args:
            engine: Engine object.

        Returns:
            Dict of chart_id -> chart render data.
        """
        if engine is None:
            return {}

        # Try direct attributes
        for attr in ('charts', 'render_results', 'render_cache',
                     'chart_data', 'chart_results'):
            val = getattr(engine, attr, None)
            if val is not None and hasattr(val, 'items'):
                return dict(val)

        # Try method calls
        for method in ('get_charts', 'list_charts', 'get_render_results',
                       'get_all_charts', 'get_render_data'):
            fn = getattr(engine, method, None)
            if callable(fn):
                try:
                    result = fn()
                    if isinstance(result, dict):
                        return result
                except Exception:
                    continue

        # Try .items() iteration
        if hasattr(engine, 'items'):
            try:
                return {k: v for k, v in engine.items()}
            except Exception:
                pass

        return {}

    def _get_engine_db_path(self, engine):
        # type: (Any) -> Optional[str]
        """
        Try to get the database path from an engine object.

        Args:
            engine: Engine object.

        Returns:
            str: DB path if found, None otherwise.
        """
        if engine is None:
            return None

        # Try _resolve_db_path method (NodeBindingEngine)
        fn = getattr(engine, '_resolve_db_path', None)
        if callable(fn):
            try:
                path = fn()
                if path and os.path.exists(str(path)):
                    return str(path)
            except Exception:
                pass

        # Try direct attributes
        for attr in ('db_path', '_db_path', 'database_path', 'db_file'):
            val = getattr(engine, attr, None)
            if val and os.path.exists(str(val)):
                return str(val)

        return None

    def _load_all_from_db(self, db_path, schema):
        # type: (str, str) -> Dict[str, List[Dict[str, Any]]]
        """
        Load all indicators from database.

        Args:
            db_path: Path to SQLite database file.
            schema: Schema type ('indicator_cache' or 'series_cache').

        Returns:
            Dict of indicator_id -> list of point dicts.
        """
        indicators = {}  # type: Dict[str, List[Dict[str, Any]]]

        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()

            if schema == "series_cache":
                # Load all distinct indicator IDs
                cur.execute(
                    "SELECT DISTINCT indicator_id FROM series_cache "
                    "ORDER BY indicator_id"
                )
                ids = [r[0] for r in cur.fetchall()]

                # Batch load: get all rows and group by indicator_id
                cur.execute(
                    "SELECT indicator_id, date, value FROM series_cache "
                    "WHERE value IS NOT NULL ORDER BY indicator_id, date"
                )
                for row in cur.fetchall():
                    ind_id = row[0]
                    if ind_id not in indicators:
                        indicators[ind_id] = []
                    indicators[ind_id].append({
                        "date": row[1],
                        "value": row[2],
                    })

            elif schema == "indicator_cache":
                cur.execute(
                    "SELECT metric, data_json FROM indicator_cache"
                )
                for row in cur.fetchall():
                    ind_id = row[0]
                    try:
                        d = json.loads(row[1])
                        pts = d.get("points", [])
                        if pts:
                            indicators[ind_id] = pts
                    except (json.JSONDecodeError, TypeError):
                        pass

            conn.close()
        except sqlite3.Error:
            pass

        return indicators

    # =========================================================================
    # Internal Helpers - Report Generation
    # =========================================================================

    def _compute_overall_stats(self, per_chart, per_indicator):
        # type: (Dict[str, Any], Dict[str, Any]) -> Dict[str, Any]
        """
        Compute overall statistics from per-chart and per-indicator results.

        Args:
            per_chart: Dict of chart_id -> chart analysis result.
            per_indicator: Dict of indicator_id -> indicator analysis result.

        Returns:
            Dict with aggregated statistics.
        """
        stats = {
            "noise_level_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
            "category_distribution": {
                "STATISTICAL": 0,
                "STRUCTURAL": 0,
                "TEMPORAL": 0,
            },
            "total_spikes": 0,
            "total_gaps": 0,
            "total_outliers": 0,
            "total_discontinuities": 0,
            "avg_cv": 0.0,
            "max_cv": 0.0,
            "avg_noise_score": 0.0,
        }  # type: Dict[str, Any]

        total_items = 0
        cv_sum = 0.0
        score_sum = 0.0

        # Aggregate chart-level stats
        for chart_id, result in per_chart.items():
            level = result.get("noise_level", "LOW")
            if level in stats["noise_level_distribution"]:
                stats["noise_level_distribution"][level] += 1

            for cat in result.get("noise_category", []):
                if cat in stats["category_distribution"]:
                    stats["category_distribution"][cat] += 1

            metrics = result.get("metrics", {})
            if "total_spikes" in metrics:
                stats["total_spikes"] += metrics["total_spikes"]
            if "total_gaps" in metrics:
                stats["total_gaps"] += metrics["total_gaps"]
            if "total_outliers" in metrics:
                stats["total_outliers"] += metrics["total_outliers"]
            if "avg_cv" in metrics:
                stats["max_cv"] = max(stats["max_cv"], metrics["avg_cv"])
                cv_sum += metrics["avg_cv"]
            if "max_cv" in metrics:
                stats["max_cv"] = max(stats["max_cv"], metrics["max_cv"])
            total_items += 1

        # Aggregate indicator-level stats
        for indicator_id, result in per_indicator.items():
            level = result.get("noise_level", "LOW")
            if level in stats["noise_level_distribution"]:
                stats["noise_level_distribution"][level] += 1

            for cat in result.get("noise_category", []):
                if cat in stats["category_distribution"]:
                    stats["category_distribution"][cat] += 1

            metrics = result.get("metrics", {})
            if "spike_count" in metrics:
                stats["total_spikes"] += metrics["spike_count"]
            if "gap_count" in metrics:
                stats["total_gaps"] += metrics["gap_count"]
            if "outlier_count" in metrics:
                stats["total_outliers"] += metrics["outlier_count"]
            if "discontinuity_count" in metrics:
                stats["total_discontinuities"] += metrics["discontinuity_count"]
            if "cv" in metrics:
                stats["max_cv"] = max(stats["max_cv"], metrics["cv"])
                cv_sum += metrics["cv"]
            if "noise_score" in metrics:
                score_sum += metrics["noise_score"]
            total_items += 1

        # Compute averages
        stats["avg_cv"] = (
            round(cv_sum / total_items, 4) if total_items > 0 else 0.0
        )
        stats["avg_noise_score"] = (
            round(score_sum / total_items, 2) if total_items > 0 else 0.0
        )

        return stats

    @staticmethod
    def _find_problematic(results):
        # type: (Dict[str, Any]) -> List[str]
        """
        Find problematic indicator/chart IDs from results.

        Args:
            results: Dict of id -> analysis result.

        Returns:
            Sorted list of IDs with MEDIUM or HIGH noise.
        """
        problematic = []  # type: List[str]
        for id_, result in results.items():
            level = result.get("noise_level", "LOW")
            if level in ("HIGH", "MEDIUM"):
                problematic.append(id_)
        return sorted(problematic)

    def _recommendations_from_metrics(self, metrics_list):
        # type: (List[NoiseMetrics]) -> List[str]
        """
        Generate recommendations from list of metrics.

        Args:
            metrics_list: List of NoiseMetrics from chart series.

        Returns:
            List of actionable recommendations.
        """
        recs = []  # type: List[str]

        if not metrics_list:
            return ["No data available"]

        total_gaps = sum(m.gap_count for m in metrics_list)
        total_spikes = sum(m.spike_count for m in metrics_list)
        total_outliers = sum(m.outlier_count for m in metrics_list)
        avg_cv = sum(m.cv for m in metrics_list) / len(metrics_list)
        max_zero_run = max(m.zero_run_max for m in metrics_list)
        total_disc = sum(m.discontinuity_count for m in metrics_list)

        if total_gaps > 0:
            recs.append(
                "Impute or filter %d gap(s) to reduce structural noise"
                % total_gaps
            )
        if total_spikes > 0:
            recs.append(
                "Investigate %d spike(s); consider rolling median filter "
                "or anomaly flagging" % total_spikes
            )
        if total_outliers > 0:
            recs.append(
                "Review %d outlier(s); apply IQR-based capping or "
                "winsorization" % total_outliers
            )
        if total_disc > 0:
            recs.append(
                "Detect %d discontinuity(ies); validate data continuity "
                "and source" % total_disc
            )
        if avg_cv > self.noise_threshold:
            recs.append(
                "High variability (avg CV=%.3f); consider normalization "
                "or trend decomposition" % avg_cv
            )
        if max_zero_run >= self.ZERO_RUN_THRESHOLD:
            recs.append(
                "Detect zero clustering (max run=%d); consider data "
                "source validation" % max_zero_run
            )

        if not recs:
            recs.append("Data quality is acceptable for rendering")

        return recs

    def _generate_recommendations(self, report):
        # type: (NoiseReport) -> List[str]
        """
        Generate overall recommendations for the noise report.

        Args:
            report: The NoiseReport to generate recommendations for.

        Returns:
            List of actionable recommendations.
        """
        recs = []  # type: List[str]

        stats = report.statistics
        dist = stats.get("noise_level_distribution", {})
        high_count = dist.get("HIGH", 0)
        medium_count = dist.get("MEDIUM", 0)

        if high_count > 0:
            recs.append(
                "URGENT: %d chart(s)/indicator(s) classified as HIGH noise; "
                "prioritize remediation before rendering" % high_count
            )
        if medium_count > 0:
            recs.append(
                "Review %d MEDIUM noise item(s); consider smoothing or "
                "filtering" % medium_count
            )

        if stats.get("total_gaps", 0) > 0:
            recs.append(
                "Total %d gap(s) detected across all series; "
                "consider imputation or gap-filling strategy"
                % stats["total_gaps"]
            )
        if stats.get("total_spikes", 0) > 0:
            recs.append(
                "Total %d spike(s) detected; consider rolling median "
                "filter or anomaly flagging" % stats["total_spikes"]
            )
        if stats.get("total_outliers", 0) > 0:
            recs.append(
                "Total %d outlier(s) detected; consider IQR-based capping"
                % stats["total_outliers"]
            )
        if stats.get("total_discontinuities", 0) > 0:
            recs.append(
                "Total %d discontinuity(ies) detected; validate data "
                "source continuity" % stats["total_discontinuities"]
            )

        if report.problematic_indicators:
            preview = ", ".join(report.problematic_indicators[:10])
            suffix = "..." if len(report.problematic_indicators) > 10 else ""
            recs.append(
                "Problematic indicators: %s%s" % (preview, suffix)
            )

        if not recs:
            recs.append(
                "All charts and indicators meet noise quality standards"
            )

        return recs

    @staticmethod
    def _severity_rank(level):
        # type: (NoiseLevel) -> int
        """
        Rank noise severity numerically for comparison.

        Args:
            level: NoiseLevel to rank.

        Returns:
            int: 0=LOW, 1=MEDIUM, 2=HIGH.
        """
        return {
            NoiseLevel.LOW: 0,
            NoiseLevel.MEDIUM: 1,
            NoiseLevel.HIGH: 2,
        }.get(level, 0)


# =============================================================================
# Standalone Testing
# =============================================================================

def _run_self_test():
    # type: () -> None
    """
    Run a comprehensive self-test of the NoiseIndicatorMonitor.

    Tests all major algorithms and edge cases without requiring an engine.
    """
    print("=" * 72)
    print("  NoiseIndicatorMonitor Self-Test")
    print("=" * 72)
    print()

    monitor = NoiseIndicatorMonitor(noise_threshold=0.5)
    pass_count = 0
    fail_count = 0

    def check(name, condition, detail=""):
        nonlocal pass_count, fail_count
        if condition:
            print("  [PASS] %s" % name)
            pass_count += 1
        else:
            print("  [FAIL] %s %s" % (name, detail))
            fail_count += 1

    # --- Test 1: Clean data -> LOW noise ---
    clean_points = [10.0, 10.5, 10.2, 10.3, 10.1, 10.4, 10.6, 10.2, 10.3, 10.5]
    level = monitor.classify_noise_level(clean_points)
    m = monitor.calculate_noise_metrics(clean_points)
    check("Clean data -> LOW", level == NoiseLevel.LOW,
          "(got %s)" % level.value)
    check("Clean CV < 0.5", m["cv"] < 0.5, "(cv=%.4f)" % m["cv"])
    check("Clean no spikes", m["spike_count"] == 0)
    check("Clean no gaps", m["gap_count"] == 0)
    check("Clean no outliers", m["outlier_count"] == 0)
    print("        CV=%.4f, spikes=%d, gaps=%d, outliers=%d, score=%.1f"
          % (m["cv"], m["spike_count"], m["gap_count"],
             m["outlier_count"], m["noise_score"]))
    print()

    # --- Test 2: Noisy data (high CV) -> HIGH noise ---
    noisy_points = [10.0, 100.0, 10.5, 500.0, 10.2, -500.0, 10.3, 1000.0, 10.1, 10.4]
    level = monitor.classify_noise_level(noisy_points)
    m = monitor.calculate_noise_metrics(noisy_points)
    check("Noisy data -> HIGH", level == NoiseLevel.HIGH,
          "(got %s)" % level.value)
    check("Noisy CV > 0.5", m["cv"] > 0.5, "(cv=%.4f)" % m["cv"])
    print("        CV=%.4f, spikes=%d, gaps=%d, outliers=%d, score=%.1f"
          % (m["cv"], m["spike_count"], m["gap_count"],
             m["outlier_count"], m["noise_score"]))
    print()

    # --- Test 3: Gapped data -> structural noise ---
    gapped_points = [10.0, None, 10.2, None, None, 10.5, None, 10.3, 10.1, None]
    level = monitor.classify_noise_level(gapped_points)
    m = monitor.calculate_noise_metrics(gapped_points)
    check("Gapped data -> HIGH", level == NoiseLevel.HIGH,
          "(got %s)" % level.value)
    check("Gaps detected", m["gap_count"] == 5, "(gaps=%d)" % m["gap_count"])
    check("Gap ratio > 0.3", m["gap_ratio"] > 0.3,
          "(ratio=%.2f)" % m["gap_ratio"])
    print("        CV=%.4f, gaps=%d, ratio=%.2f, score=%.1f"
          % (m["cv"], m["gap_count"], m["gap_ratio"], m["noise_score"]))
    print()

    # --- Test 4: Zero clustering -> structural noise ---
    zero_points = [0.0] * 10 + [10.0, 10.0]
    level = monitor.classify_noise_level(zero_points)
    m = monitor.calculate_noise_metrics(zero_points)
    check("Zero clustering detected", m["zero_run_max"] >= 10,
          "(max_run=%d)" % m["zero_run_max"])
    check("Zero runs counted", m["zero_run_count"] >= 1)
    print("        CV=%.4f, zero_max=%d, zero_count=%d, score=%.1f"
          % (m["cv"], m["zero_run_max"], m["zero_run_count"],
             m["noise_score"]))
    print()

    # --- Test 5: Spike detection ---
    spike_points = [10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 1000.0, 10.6, 10.7]
    m = monitor.calculate_noise_metrics(spike_points)
    check("Spike detected", m["spike_count"] >= 1,
          "(spikes=%d)" % m["spike_count"])
    print("        CV=%.4f, spikes=%d, outliers=%d"
          % (m["cv"], m["spike_count"], m["outlier_count"]))
    print()

    # --- Test 6: Outlier detection ---
    outlier_points = ([10.0, 10.1, 10.2, 10.3, 10.4, 10.5,
                       10.6, 10.7, 10.8, 10.9, 5000.0])
    m = monitor.calculate_noise_metrics(outlier_points)
    check("Outlier detected", m["outlier_count"] >= 1,
          "(outliers=%d)" % m["outlier_count"])
    print("        CV=%.4f, outliers=%d" % (m["cv"], m["outlier_count"]))
    print()

    # --- Test 7: Dict-format points ---
    dict_points = [
        {"date": "2024-01-01", "value": 10.0},
        {"date": "2024-01-02", "value": 10.5},
        {"date": "2024-01-03", "value": 10.2},
        {"date": "2024-01-04", "value": None},
        {"date": "2024-01-05", "value": 10.3},
    ]
    m = monitor.calculate_noise_metrics(dict_points)
    check("Dict points count=5", m["count"] == 5, "(count=%d)" % m["count"])
    check("Dict gap detected", m["gap_count"] == 1,
          "(gaps=%d)" % m["gap_count"])
    print("        CV=%.4f, count=%d, gaps=%d"
          % (m["cv"], m["count"], m["gap_count"]))
    print()

    # --- Test 8: Monitor chart render (single series) ---
    chart_result = monitor.monitor_chart_render("chart_1", {
        "points": clean_points,
        "indicator_id": "ind_1",
    })
    check("Chart render level LOW", chart_result["noise_level"] == "LOW",
          "(level=%s)" % chart_result["noise_level"])
    check("Chart render issues=0", len(chart_result["issues"]) == 0,
          "(issues=%d)" % len(chart_result["issues"]))
    print("        level=%s, issues=%d, series=%d"
          % (chart_result["noise_level"], len(chart_result["issues"]),
             len(chart_result["series_analyses"])))
    print()

    # --- Test 9: Monitor chart render (multi-series) ---
    multi_result = monitor.monitor_chart_render("chart_2", {
        "chart_id": "chart_2",
        "series": [
            {"id": "clean_series", "points": clean_points},
            {"id": "noisy_series", "points": noisy_points},
        ],
    })
    check("Multi-series -> HIGH", multi_result["noise_level"] == "HIGH",
          "(level=%s)" % multi_result["noise_level"])
    check("Multi-series 2 series",
          len(multi_result["series_analyses"]) == 2)
    print("        level=%s, series=%d, spikes=%d"
          % (multi_result["noise_level"], len(multi_result["series_analyses"]),
             multi_result["metrics"].get("total_spikes", 0)))
    print()

    # --- Test 10: Monitor chart render (list format) ---
    list_result = monitor.monitor_chart_render("chart_3", clean_points)
    check("List format works", list_result["noise_level"] == "LOW")
    print("        level=%s" % list_result["noise_level"])
    print()

    # --- Test 11: Monitor chart render (no data) ---
    empty_result = monitor.monitor_chart_render("chart_4", {"points": []})
    check("Empty chart -> HIGH", empty_result["noise_level"] == "HIGH")
    print("        level=%s, issues=%d"
          % (empty_result["noise_level"], len(empty_result["issues"])))
    print()

    # --- Test 12: is_noisy_indicator ---
    is_noisy = monitor.is_noisy_indicator("test_noisy", noisy_points)
    check("Noisy indicator -> True", is_noisy is True)

    is_clean = monitor.is_noisy_indicator("test_clean", clean_points)
    check("Clean indicator -> False", is_clean is False)
    print()

    # --- Test 13: Full report (no engine, cached data) ---
    report = monitor.monitor_all_charts()
    check("Report generated", report is not None)
    check("Report has charts", report.total_charts >= 4,
          "(charts=%d)" % report.total_charts)
    check("Report has recommendations", len(report.recommendations) > 0)
    check("Report has problematic", len(report.problematic_indicators) > 0)
    print("        charts=%d, problematic=%d, recs=%d"
          % (report.total_charts, len(report.problematic_indicators),
             len(report.recommendations)))
    print()

    # --- Test 14: Report JSON serialization ---
    json_str = report.to_json()
    parsed = json.loads(json_str)
    check("JSON round-trip", parsed["total_charts"] == report.total_charts)
    check("JSON is ASCII-safe",
          all(ord(c) < 128 for c in json_str[:500]))
    print("        JSON length=%d chars" % len(json_str))
    print()

    # --- Test 15: NoiseMetrics to_dict ---
    nm = monitor.detect_noise_in_data(dict_points)
    md = nm.to_dict()
    check("Metrics to_dict has cv", "cv" in md)
    check("Metrics to_dict has noise_score", "noise_score" in md)
    check("Metrics to_dict has spike_count", "spike_count" in md)
    check("Metrics to_dict has outlier_count", "outlier_count" in md)
    check("Metrics to_dict has zero_run_max", "zero_run_max" in md)
    print()

    # --- Test 16: DB save/load ---
    db_path = os.path.join(tempfile.gettempdir(), "noise_monitor_test.db")
    try:
        monitor.save_report_to_db(db_path)
        loaded = monitor.load_report_from_db(db_path, latest_only=True)
        check("DB save/load works", len(loaded) == 1)
        check("DB loaded report matches",
              loaded[0]["report"]["total_charts"] == report.total_charts)
        print("        DB path=%s" % db_path)
    except Exception as e:
        check("DB save/load works", False, "(error: %s)" % str(e))
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
    print()

    # --- Test 17: DB schema detection and loading ---
    schema_db = os.path.join(tempfile.gettempdir(), "noise_schema_test.db")
    try:
        conn = sqlite3.connect(schema_db)
        # Create indicator_cache
        conn.execute(
            "CREATE TABLE indicator_cache (metric TEXT, code TEXT, data_json TEXT)"
        )
        conn.execute(
            "INSERT INTO indicator_cache VALUES (?, ?, ?)",
            (
                "test_ind", "TEST_IND",
                json.dumps({
                    "name": "Test", "unit": "USD",
                    "points": [
                        {"date": "2024-01-01", "value": 10.0},
                        {"date": "2024-01-02", "value": 10.5},
                        {"date": "2024-01-03", "value": 10.2},
                    ]
                })
            )
        )
        # Create series_cache
        conn.execute(
            "CREATE TABLE series_cache (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "indicator_id TEXT, indicator_id_mapped TEXT, commodity TEXT, "
            "date TEXT, value REAL, source TEXT, imported_at TEXT)"
        )
        for d, v in [("2024-01-01", 10.0), ("2024-01-02", 10.5),
                     ("2024-01-03", 10.2)]:
            conn.execute(
                "INSERT INTO series_cache (indicator_id, indicator_id_mapped, "
                "commodity, date, value, source) VALUES (?, ?, ?, ?, ?, ?)",
                ("test_ind", "TEST_IND", "cu", d, v, "derived")
            )
        conn.commit()
        conn.close()

        # Schema detection
        schema = NoiseIndicatorMonitor.detect_db_schema(schema_db)
        check("Schema detection",
              schema in ("indicator_cache", "series_cache"),
              "(got %s)" % schema)

        # Indicator cache loading
        pts = NoiseIndicatorMonitor.load_from_indicator_cache(schema_db, "test_ind")
        check("Indicator cache load", len(pts) == 3, "(got %d)" % len(pts))

        # Series cache loading
        pts = NoiseIndicatorMonitor.load_from_series_cache(
            schema_db, "test_ind", commodity="cu"
        )
        check("Series cache load", len(pts) == 3, "(got %d)" % len(pts))

        # Unified loading
        pts = monitor.load_from_db(schema_db, "test_ind")
        check("Unified DB load", len(pts) == 3, "(got %d)" % len(pts))

        # Monitor from DB
        result = monitor.monitor_indicator_from_db(schema_db, "test_ind")
        check("Monitor from DB", result["noise_level"] == "LOW",
              "(level=%s)" % result["noise_level"])

        # Monitor all from DB
        report2 = monitor.monitor_all_from_database(schema_db)
        check("Monitor all from DB", report2.total_indicators >= 1,
              "(indicators=%d)" % report2.total_indicators)

    except Exception as e:
        check("DB schema test", False, "(error: %s)" % str(e))
    finally:
        if os.path.exists(schema_db):
            os.remove(schema_db)
    print()

    # --- Test 18: Edge cases ---
    # Empty list
    m = monitor.calculate_noise_metrics([])
    check("Empty list -> LOW",
          monitor.classify_noise_level([]) == NoiseLevel.LOW)
    check("Empty list count=0", m["count"] == 0)

    # Single value
    m = monitor.calculate_noise_metrics([42.0])
    check("Single value -> LOW",
          monitor.classify_noise_level([42.0]) == NoiseLevel.LOW)
    check("Single value cv=0", m["cv"] == 0.0)

    # All zeros
    m = monitor.calculate_noise_metrics([0.0] * 20)
    check("All zeros -> LOW",
          monitor.classify_noise_level([0.0] * 20) == NoiseLevel.LOW)
    check("All zeros cv=0", m["cv"] == 0.0)
    check("All zeros clustering", m["zero_run_max"] >= 20)

    # All None (all gaps)
    level = monitor.classify_noise_level([None] * 10)
    m = monitor.calculate_noise_metrics([None] * 10)
    check("All gaps -> HIGH", level == NoiseLevel.HIGH)
    check("All gaps ratio=1.0", m["gap_ratio"] == 1.0)

    # None input
    try:
        monitor.detect_noise_in_data(None)
        check("None input raises ValueError", False)
    except ValueError:
        check("None input raises ValueError", True)

    # All same value
    m = monitor.calculate_noise_metrics([5.0] * 10)
    check("All same -> LOW",
          monitor.classify_noise_level([5.0] * 10) == NoiseLevel.LOW)
    check("All same cv=0", m["cv"] == 0.0)

    # NaN values
    m = monitor.calculate_noise_metrics([1.0, float("nan"), 2.0, float("nan")])
    check("NaN treated as gap", m["gap_count"] == 2,
          "(gaps=%d)" % m["gap_count"])

    # Tuple-format points
    tuple_pts = [("2024-01-01", 10.0), ("2024-01-02", 10.5),
                 ("2024-01-03", None)]
    m = monitor.calculate_noise_metrics(tuple_pts)
    check("Tuple points count=3", m["count"] == 3)
    check("Tuple gap detected", m["gap_count"] == 1)

    print()
    print("-" * 72)
    print("  Results: %d passed, %d failed" % (pass_count, fail_count))
    print("-" * 72)

    if fail_count > 0:
        print("  [WARNING] Some tests failed!")
        sys.exit(1)
    else:
        print("  All tests passed!")
        sys.exit(0)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    _run_self_test()
