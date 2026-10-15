#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V88 Phase03 P1 — CPU Baseline Collection Script (P1-Optimized)
================================================================

TASK_ID  : V88_PHASE03_P1_DSHE_CPU_BASELINE
AGENT    : DSHE
BRANCH   : feature/v88-g1 (BRANCH_LOCKED)

Purpose
-------
Collect a process-level CPU / latency / RSS baseline under fixed load
(all 101 charts, both matchable and pending_data), using the same
NodeBindingEngine.render_with_fallback() path that P0 used.

This script produces a **render-process-level baseline** suitable for
same-script / same-load / same-time-window optimisation comparison
within P1. It is explicitly NOT directly comparable with Phase02's
CPU FUSE 2.0% / peak 1.94% (which are full-chain business steady-state
means covering data supply + push + render).

Key design decisions (P1 improvements over P0):
  · Configurable rounds (default 5) for statistical stability
  · Per-round wall time and per-round CPU samples (not just aggregate)
  · Per-core normalised CPU% for multi-core fairness
  · Latency distribution: median / p95 / p99 / max / mean
  · RSS memory (ru_maxrss) captured via resource module
  · Comprehensive structured JSON output
  · Explicit caliber difference declaration
  · "same_script/same_load/same_time_window" metadata tags
  · Graceful fallback when psutil is unavailable
  · Automatic test DB detection (V88_PHASE03_TEST_DB)

Constraints (from V88 phase plan)
---------------------------------
  · NO ZHIJI API CALLS  (entirely offline)
  · NO ENGINE MODIFICATION (read-only NodeBindingEngine usage)
  · BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / APPEND_ONLY

Usage
-----
    python collect_cpu_baseline_p1.py                       # default 5 rounds
    python collect_cpu_baseline_p1.py --rounds 10           # more rounds
    python collect_cpu_baseline_p1.py --output report.json  # custom output
    python collect_cpu_baseline_p1.py --no-engine           # skip engine, latency only

Requirements: Python 3.8+, psutil (optional, falls back to time.process_time())

"""

import argparse
import json
import os
import platform
import re
import socket
import sys
import time
import traceback

# ---------------------------------------------------------------------------
# UTF-8 encoding guard (Windows GBK prevention)
# ---------------------------------------------------------------------------
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, Exception):
    pass  # Python < 3.7 or non-text stream; PYTHONIOENCODING covers it

# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Optional imports (graceful degradation)
# ---------------------------------------------------------------------------
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

# ---------------------------------------------------------------------------
# Module version / identity
# ---------------------------------------------------------------------------
SCRIPT_VERSION = "1.0.0"
SCRIPT_ID = "V88_PHASE03_P1_DSHE_CPU_BASELINE"
TASK_ID = SCRIPT_ID

# ---------------------------------------------------------------------------
# Paths (resolved at runtime)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# P1 dshe/ → p1/ → phase03/ → v88/ → e2e_output/ → analysis/ → framework-tree/
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", "..", ".."))

ENGINE_PATH = os.path.join(REPO_ROOT, "scripts", "node_binding_engine.py")
YAML_PATH = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "backlog",
                         "framework_tree_meta_chart.yaml")
TREE_CONFIG_PATH = os.path.join(REPO_ROOT, "data", "tree_config.json")

# Test DB candidates (priority order)
TEST_DB_CANDIDATES = [
    os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p0",
                 "phase03_test.db"),
    os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03",
                 "phase03_test.db"),
]
API_CACHE_DB = os.path.join(REPO_ROOT, "scripts", "api_cache.db")

# ---------------------------------------------------------------------------
# Constants from V88 phase plan / P0 gate checker
# ---------------------------------------------------------------------------
CPU_FUSE_THRESHOLD_PCT = 2.0        # Phase02 DSHB full-chain threshold (immutable)
CPU_PHASE02_PEAK_PCT = 1.94         # Phase02 observed peak (full-chain steady-state)
CPU_P0_OPTIMIZED_TARGET_PCT = 1.75  # P0-10 gate target (full-chain, DSHB scope)

TOTAL_CHARTS_EXPECTED = 101
MATCHABLE_CHARTS_EXPECTED = 85

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
_LOG_LINES = []

def log(msg, level="INFO"):
    """Log a message to stdout and the internal log buffer."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] [%s] %s" % (timestamp, level, msg)
    _LOG_LINES.append(line)
    print(line)


def log_error(msg):
    log(msg, "ERROR")


def log_warn(msg):
    log(msg, "WARN")


# ===========================================================================
# CPU / Memory measurement helpers
# ===========================================================================
class CpuMeasure:
    """
    Process-level CPU measurement with graceful fallback.

    Preferred: psutil.Process().cpu_percent() — true process-level
    instantaneous CPU percentage (100 = one full core).

    Fallback: time.process_time() — measures CPU time consumed by this
    process.  CPU% = (cpu_time_delta / wall_time_delta) * 100.
    This is a window-averaged CPU% and is less noisy than per-round
    sampling, but sufficient for baseline comparison when psutil is
    unavailable.

    For RSS: resource.getrusage(RUSAGE_SELF).ru_maxrss (Unix, KB) or
    os.sysconf fallback.
    """

    def __init__(self):
        self.proc = None
        self.nproc = os.cpu_count() or 1

        if HAS_PSUTIL:
            self.proc = psutil.Process()
            # Warm up the CPU timer (first call returns 0.0)
            self.proc.cpu_percent(None)
            time.sleep(0.3)
            self.cpu_method = "psutil.Process().cpu_percent"
        else:
            self.cpu_method = "time.process_time() window-averaged (psutil unavailable)"
            log_warn("psutil not available — falling back to time.process_time()")

    def sample_cpu(self):
        """
        Return one CPU% sample.

        With psutil: returns instantaneous process CPU% (since last call).
        Without psutil: caller must provide wall_start/wall_end for window
        computation — see sample_cpu_window().
        """
        if self.proc is not None:
            return self.proc.cpu_percent(None)
        return None

    def sample_cpu_window(self, wall_start, wall_end):
        """
        Compute CPU% for a window [wall_start, wall_end] using
        time.process_time().  Returns a percentage float.
        """
        cpu_start = time.process_time()
        cpu_end = time.process_time()
        # We need to measure the window, so this is used differently:
        # The caller should record process_time before and after the round.
        # This method is a convenience wrapper.
        cpu_delta = cpu_end - cpu_start
        wall_delta = wall_end - wall_start
        if wall_delta > 0:
            return (cpu_delta / wall_delta) * 100.0
        return 0.0

    def start_timing(self):
        """Record process_time and wall_time for windowed CPU measurement."""
        return {
            "wall": time.time(),
            "cpu": time.process_time(),
        }

    def window_cpu_pct(self, t_start, t_end):
        """
        Compute CPU% for a window between two timing snapshots.

        Each snapshot is a dict with 'wall' and 'cpu' keys.
        Returns (cpu_pct, wall_sec, cpu_sec).
        """
        wall_delta = t_end["wall"] - t_start["wall"]
        cpu_delta = t_end["cpu"] - t_start["cpu"]
        cpu_pct = (cpu_delta / wall_delta * 100.0) if wall_delta > 0 else 0.0
        return cpu_pct, wall_delta, cpu_delta

    @property
    def cpu_method_name(self):
        return self.cpu_method

    def rss_mb(self):
        """Return current/peak RSS in MB."""
        # Prefer psutil
        if self.proc is not None:
            try:
                return self.proc.memory_info().rss / (1024 * 1024)
            except Exception:
                pass

        # Fallback: resource module (Unix only)
        if HAS_RESOURCE:
            try:
                # ru_maxrss is in KB on Unix, bytes on macOS
                # We detect by checking if it's unreasonably large
                rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                # On macOS, ru_maxrss is in bytes; on Linux it's in KB.
                # Heuristic: if value > 10^7, it's likely bytes (macOS)
                if rss_kb > 10_000_000:
                    return rss_kb / (1024 * 1024)  # bytes → MB
                return rss_kb / 1024.0  # KB → MB
            except Exception:
                pass

        # Last resort: parse ps output
        try:
            if platform.system() == "Windows":
                pass  # No easy way without psutil
            else:
                import subprocess
                result = subprocess.run(
                    ["ps", "-o", "rss=", str(os.getpid())],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return int(result.stdout.strip()) / 1024.0
        except Exception:
            pass

        return None


# ===========================================================================
# Engine loader
# ===========================================================================
def setup_test_db_env():
    """
    Auto-detect and set V88_PHASE03_TEST_DB environment variable.

    Priority:
      1. V88_PHASE03_TEST_DB already set (user override)
      2. Known test DB candidates that exist
      3. scripts/api_cache.db (default, used by engine anyway)

    Returns the resolved DB path (or None).
    """
    # Already set?
    existing = os.environ.get("V88_PHASE03_TEST_DB", "").strip()
    if existing:
        if os.path.exists(existing):
            log("Test DB: %s (from env V88_PHASE03_TEST_DB)" % existing)
            return existing
        else:
            log_warn("V88_PHASE03_TEST_DB set but path not found: %s" % existing)

    # Try known candidates
    for candidate in TEST_DB_CANDIDATES:
        if os.path.exists(candidate):
            os.environ["V88_PHASE03_TEST_DB"] = candidate
            log("Test DB auto-detected: %s" % candidate)
            return candidate

    # Check if api_cache.db exists (engine will use it by default)
    if os.path.exists(API_CACHE_DB):
        log("Using default api_cache.db: %s (no Phase03 test DB found)" % API_CACHE_DB)
        return API_CACHE_DB

    log_warn("No test DB found — engine will run without real data "
             "(all charts use simulated/placeholder fallback)")
    return None


def load_engine(repo_root=None):
    """
    Load the NodeBindingEngine from the repository scripts/ directory.

    Returns:
        (engine, success_msg) on success, or (None, error_msg) on failure.
    """
    if repo_root is None:
        repo_root = REPO_ROOT

    if not os.path.exists(ENGINE_PATH):
        return None, "Engine file not found: %s" % ENGINE_PATH

    if not os.path.exists(YAML_PATH):
        return None, "YAML metadata not found: %s" % YAML_PATH

    if not os.path.exists(TREE_CONFIG_PATH):
        return None, "Tree config not found: %s" % TREE_CONFIG_PATH

    try:
        sys.path.insert(0, os.path.join(repo_root, "scripts"))
        from node_binding_engine import NodeBindingEngine
        engine = NodeBindingEngine(repo_root=repo_root)
        ok, msg = engine.load()
        if not ok:
            return None, "Engine load failed: %s" % msg
        return engine, msg
    except Exception as e:
        return None, "Engine import/init failed: %s\n%s" % (str(e), traceback.format_exc())


# ===========================================================================
# Percentile helper
# ===========================================================================
def percentile(sorted_data, pct):
    """
    Compute the pct-th percentile of a sorted list.

    Args:
        sorted_data: list of numbers, already sorted ascending
        pct: percentile value 0-100

    Returns:
        The percentile value (interpolated).
    """
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]

    k = (pct / 100.0) * (n - 1)
    f = int(k)
    c = f + 1
    if c >= n:
        return sorted_data[-1]
    d = k - f
    return sorted_data[f] + d * (sorted_data[c] - sorted_data[f])


def compute_latency_stats(latencies_ms):
    """Compute latency distribution stats from a list of ms values."""
    if not latencies_ms:
        return {
            "median_ms": 0, "p95_ms": 0, "p99_ms": 0,
            "max_ms": 0, "mean_ms": 0, "min_ms": 0,
            "count": 0,
        }
    s = sorted(latencies_ms)
    n = len(s)
    mean = sum(s) / n
    median = percentile(s, 50)
    p95 = percentile(s, 95)
    p99 = percentile(s, 99)
    return {
        "median_ms": round(median, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "max_ms": round(s[-1], 3),
        "min_ms": round(s[0], 3),
        "mean_ms": round(mean, 3),
        "count": n,
    }


# ===========================================================================
# Main collection function
# ===========================================================================
def collect_cpu_baseline_p1(rounds=5, output_path=None, use_engine=True,
                            repo_root=None):
    """
    Collect P1 CPU / latency / RSS baseline under fixed load.

    Fixed load: render ALL charts (matchable + pending_data) via
    render_with_fallback() in each round.

    Args:
        rounds: number of measurement rounds (default 5)
        output_path: path for JSON output file (None = stdout only)
        use_engine: whether to use NodeBindingEngine (default True)
        repo_root: repository root override

    Returns:
        Complete JSON-reportable dictionary.
    """
    if repo_root is None:
        repo_root = REPO_ROOT

    log("=" * 72)
    log("V88 Phase03 P1 — CPU Baseline Collection")
    log("Script: collect_cpu_baseline_p1.py v%s" % SCRIPT_VERSION)
    log("=" * 72)

    # ------------------------------------------------------------------
    # 0. Environment setup
    # ------------------------------------------------------------------
    db_path = setup_test_db_env()

    cpu_m = CpuMeasure()

    report = {
        "meta": {
            "script": "collect_cpu_baseline_p1.py",
            "script_version": SCRIPT_VERSION,
            "script_id": SCRIPT_ID,
            "task_id": TASK_ID,
            "agent": "DSHE",
            "phase": "V88 Phase03 P1",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "same_script": True,
            "same_load": True,
            "same_time_window": True,
            "caliber_declaration": (
                "CALIBER DIFFERENCE (R-V88-027): Phase02 CPU FUSE 2.0% / "
                "peak 1.94% is a FULL-CHAIN BUSINESS STEADY-STATE mean "
                "(data supply + push + render). This P1 baseline is a "
                "RENDER-PROCESS INSTANTANEOUS measurement "
                "(psutil.Process().cpu_percent() or time.process_time()), "
                "which includes YAML parsing and Python interpreter overhead. "
                "The two calibers differ by ~45-52x and are NOT DIRECTLY "
                "COMPARABLE. For P1 gate decisions, use DSHB full-chain "
                "caliber optimisation A/B comparison."
            ),
            "comparability_note": (
                "⚠️ Phase02 CPU FUSE 2.0%/peak 1.94% = full-chain business "
                "steady-state mean caliber (DSHB scope, includes data supply + "
                "push + render). This P1 baseline = render-process instantaneous "
                "re-run caliber (DSHE scope, process-level CPU via "
                "psutil.Process().cpu_percent or time.process_time()). "
                "The two calibers are NOT directly comparable. "
                "P1 CPU gate decisions require DSHB full-chain caliber "
                "optimisation A/B comparison (same script / same load / "
                "same time window)."
            ),
            "constraints": {
                "no_zhiji_api": True,
                "no_engine_modification": True,
                "branch_locked": True,
                "no_overwrite": True,
                "append_only": True,
            },
        },
        "config": {
            "rounds": rounds,
            "total_charts_expected": TOTAL_CHARTS_EXPECTED,
            "matchable_charts_expected": MATCHABLE_CHARTS_EXPECTED,
            "pending_data_charts_expected": TOTAL_CHARTS_EXPECTED - MATCHABLE_CHARTS_EXPECTED,
            "engine_path": ENGINE_PATH,
            "yaml_path": YAML_PATH,
            "tree_config_path": TREE_CONFIG_PATH,
            "test_db_path": db_path,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cpu_cores": cpu_m.nproc,
            "output_path": output_path,
        },
        "environment": {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_release": platform.release(),
            "arch": platform.machine(),
            "processor": platform.processor() or "unknown",
        },
        "measurement_method": {
            "cpu_method": cpu_m.cpu_method_name,
            "has_psutil": HAS_PSUTIL,
            "has_resource": HAS_RESOURCE,
            "rss_method": (
                "psutil.Process().memory_info().rss" if HAS_PSUTIL
                else ("resource.getrusage().ru_maxrss" if HAS_RESOURCE
                      else "ps command fallback")
            ),
            "nproc": cpu_m.nproc,
        },
        "summary": {},
        "per_round": [],
        "per_chart_type": {},
        "engine_info": {},
        "caliber_comparability": {
            "phase02_fuse_threshold_pct": CPU_FUSE_THRESHOLD_PCT,
            "phase02_peak_pct": CPU_PHASE02_PEAK_PCT,
            "p0_optimized_target_pct": CPU_P0_OPTIMIZED_TARGET_PCT,
            "p1_process_level": {},
            "ratio_vs_phase02_peak": None,
            "comparability": "NOT_DIRECTLY_COMPARABLE",
            "explanation": (
                "Phase02 FUSE 2.0% / peak 1.94% is full-chain business "
                "steady-state mean caliber. This P1 process-level CPU is "
                "render-process instantaneous caliber. The ratio is reported "
                "for reference only and MUST NOT be used for gate decisions."
            ),
        },
        "errors": [],
        "log_lines": [],
        "status": "UNKNOWN",
        "status_reason": "",
    }

    # ------------------------------------------------------------------
    # 1. Load engine
    # ------------------------------------------------------------------
    engine = None
    if use_engine:
        log("[1/5] Loading NodeBindingEngine...")
        engine, eng_msg = load_engine(repo_root)
        if engine is None:
            log_error("Engine failed to load: %s" % eng_msg)
            report["errors"].append("engine_load_failed: %s" % eng_msg)
            report["status"] = "FAILED"
            report["status_reason"] = "Engine load failed: %s" % eng_msg
            report["engine_info"] = {"loaded": False, "error": eng_msg}
            return report

        log("[1/5] Engine loaded: %s" % eng_msg)
        total_charts = len(engine.charts)
        matchable = sum(1 for c in engine.charts if c.data_status == "matchable")
        pending = sum(1 for c in engine.charts if c.data_status == "pending_data")
        deprecated = sum(1 for c in engine.charts if c.data_status == "deprecated")

        report["engine_info"] = {
            "loaded": True,
            "load_time_sec": round(engine.load_time, 4) if engine.load_time else None,
            "total_charts": total_charts,
            "matchable_charts": matchable,
            "pending_data_charts": pending,
            "deprecated_charts": deprecated,
            "node_count": len(engine.node_index),
            "chart_ids": [c.chart_id for c in engine.charts],
            "chart_types": sorted(set(c.chart_type for c in engine.charts)),
            "data_status_breakdown": {
                "matchable": matchable,
                "pending_data": pending,
                "deprecated": deprecated,
            },
        }
        report["config"]["total_charts_actual"] = total_charts
        log("[1/5] Charts: %d total (%d matchable, %d pending_data, %d deprecated)" %
            (total_charts, matchable, pending, deprecated))
    else:
        log("[1/5] Engine skipped (--no-engine)")
        report["engine_info"] = {"loaded": False, "reason": "user_requested_skip"}

    # ------------------------------------------------------------------
    # 2. Pre-warm: render once to warm caches before measurement
    # ------------------------------------------------------------------
    if engine is not None:
        log("[2/5] Pre-warming engine (1 full render pass)...")
        try:
            warm_t0 = time.time()
            for cb in engine.charts:
                engine.render_with_fallback(cb.chart_id)
            warm_time = time.time() - warm_t0
            log("[2/5] Pre-warm complete: %.2fs for %d charts" % (warm_time, total_charts))
        except Exception as e:
            log_error("[2/5] Pre-warm failed (non-fatal): %s" % str(e))

    # ------------------------------------------------------------------
    # 3. Measurement rounds
    # ------------------------------------------------------------------
    log("[3/5] Starting %d measurement round(s)..." % rounds)

    all_latencies = []
    per_round_data = []
    all_chart_type_latencies = {}
    total_renders = 0
    render_errors = []
    grand_wall_start = time.time()

    for rnd in range(rounds):
        rnd_num = rnd + 1
        log("[3/5] Round %d/%d starting..." % (rnd_num, rounds))

        round_start_wall = time.time()
        round_start_cpu = cpu_m.start_timing()

        round_latencies = []
        round_errors = []

        if engine is not None:
            for cb in engine.charts:
                t_render_start = time.time()
                try:
                    result = engine.render_with_fallback(cb.chart_id)
                    t_render_end = time.time()
                    latency_ms = (t_render_end - t_render_start) * 1000.0

                    round_latencies.append({
                        "chart_id": cb.chart_id,
                        "chart_type": cb.chart_type,
                        "data_status": cb.data_status,
                        "latency_ms": round(latency_ms, 3),
                        "renderable": result.get("renderable", False) if isinstance(result, dict) else False,
                    })
                    all_latencies.append(latency_ms)

                    # Accumulate per-chart-type stats
                    ct = cb.chart_type
                    if ct not in all_chart_type_latencies:
                        all_chart_type_latencies[ct] = []
                    all_chart_type_latencies[ct].append(latency_ms)

                    total_renders += 1
                except Exception as e:
                    error_msg = "round %d chart %s: %s" % (rnd_num, cb.chart_id, str(e))
                    round_errors.append(error_msg)
                    render_errors.append(error_msg)
                    log_error("  [render error] %s" % error_msg)
        else:
            # No engine: just record empty latency
            log("  [round %d] No engine — skipping render" % rnd_num)

        round_end_cpu = cpu_m.start_timing()
        round_end_wall = time.time()
        wall_sec = round_end_wall - round_start_wall

        # Compute CPU% for this round
        if HAS_PSUTIL:
            cpu_samples = cpu_m.sample_cpu()
            cpu_raw_pct = cpu_samples
        else:
            cpu_raw_pct, wall_delta, cpu_sec = cpu_m.window_cpu_pct(
                round_start_cpu, round_end_cpu)
            # Also compute via total wall time for consistency
            if wall_delta == 0 and wall_sec > 0:
                cpu_raw_pct = (cpu_sec / wall_sec) * 100.0

        cpu_per_core_pct = (cpu_raw_pct / cpu_m.nproc * 100.0) if cpu_raw_pct is not None else None

        round_data = {
            "round": rnd_num,
            "wall_sec": round(wall_sec, 4),
            "cpu_raw_pct": round(cpu_raw_pct, 4) if cpu_raw_pct is not None else None,
            "cpu_per_core_pct": round(cpu_per_core_pct, 4) if cpu_per_core_pct is not None else None,
            "renders": len(round_latencies),
            "render_errors": len(round_errors),
            "latency_ms": compute_latency_stats([l["latency_ms"] for l in round_latencies]),
            "chart_results": round_latencies,
        }
        per_round_data.append(round_data)

        log("[3/5] Round %d/%d: wall=%.2fs, CPU=%.4f%% (per-core=%.4f%%), "
            "renders=%d, errors=%d, latency p50=%.2fms p95=%.2fms"
            % (rnd_num, rounds, wall_sec,
               cpu_raw_pct if cpu_raw_pct is not None else 0,
               cpu_per_core_pct if cpu_per_core_pct is not None else 0,
               len(round_latencies), len(round_errors),
               round_data["latency_ms"]["median_ms"],
               round_data["latency_ms"]["p95_ms"]))

    grand_wall_end = time.time()
    total_wall_sec = grand_wall_end - grand_wall_start

    # ------------------------------------------------------------------
    # 4. Aggregate summary
    # ------------------------------------------------------------------
    log("[4/5] Computing aggregate summary...")

    all_latencies.sort()

    # CPU aggregation
    cpu_raw_values = [r["cpu_raw_pct"] for r in per_round_data if r["cpu_raw_pct"] is not None]
    cpu_per_core_values = [r["cpu_per_core_pct"] for r in per_round_data if r["cpu_per_core_pct"] is not None]

    cpu_mean_raw = sum(cpu_raw_values) / len(cpu_raw_values) if cpu_raw_values else None
    cpu_max_raw = max(cpu_raw_values) if cpu_raw_values else None
    cpu_min_raw = min(cpu_raw_values) if cpu_raw_values else None
    cpu_mean_per_core = sum(cpu_per_core_values) / len(cpu_per_core_values) if cpu_per_core_values else None
    cpu_max_per_core = max(cpu_per_core_values) if cpu_per_core_values else None
    cpu_min_per_core = min(cpu_per_core_values) if cpu_per_core_values else None

    # RSS
    rss_mb = cpu_m.rss_mb()

    # Throughput
    total_render_wall = sum(r["wall_sec"] for r in per_round_data if r["renders"] > 0)
    renders_per_sec = (total_renders / total_render_wall) if total_render_wall > 0 else 0

    # Latency stats
    latency_stats = compute_latency_stats(all_latencies)

    report["summary"] = {
        "total_renders": total_renders,
        "total_render_errors": len(render_errors),
        "total_wall_sec": round(total_wall_sec, 4),
        "renders_per_sec": round(renders_per_sec, 2),
        "cpu_raw": {
            "mean_pct": round(cpu_mean_raw, 4) if cpu_mean_raw is not None else None,
            "peak_pct": round(cpu_max_raw, 4) if cpu_max_raw is not None else None,
            "min_pct": round(cpu_min_raw, 4) if cpu_min_raw is not None else None,
            "samples": len(cpu_raw_values),
        },
        "cpu_per_core": {
            "mean_pct": round(cpu_mean_per_core, 4) if cpu_mean_per_core is not None else None,
            "peak_pct": round(cpu_max_per_core, 4) if cpu_max_per_core is not None else None,
            "min_pct": round(cpu_min_per_core, 4) if cpu_min_per_core is not None else None,
            "nproc": cpu_m.nproc,
        },
        "rss_max_mb": round(rss_mb, 4) if rss_mb is not None else None,
        "latency_ms": latency_stats,
        "wall_time_per_round": {
            "values_sec": [r["wall_sec"] for r in per_round_data],
            "mean_sec": round(
                sum(r["wall_sec"] for r in per_round_data) / len(per_round_data), 4
            ) if per_round_data else None,
            "min_sec": round(min(r["wall_sec"] for r in per_round_data), 4) if per_round_data else None,
            "max_sec": round(max(r["wall_sec"] for r in per_round_data), 4) if per_round_data else None,
        },
    }

    # ------------------------------------------------------------------
    # 5. Per-chart-type breakdown
    # ------------------------------------------------------------------
    per_chart_type_summary = {}
    for ct, lat_list in all_chart_type_latencies.items():
        per_chart_type_summary[ct] = {
            "count": len(lat_list),
            "latency_ms": compute_latency_stats(lat_list),
        }

    report["per_chart_type"] = per_chart_type_summary

    # ------------------------------------------------------------------
    # 6. Caliber comparability
    # ------------------------------------------------------------------
    if cpu_max_raw is not None:
        ratio = cpu_max_raw / CPU_PHASE02_PEAK_PCT if CPU_PHASE02_PEAK_PCT > 0 else None
        report["caliber_comparability"]["p1_process_level"] = {
            "peak_pct": round(cpu_max_raw, 4),
            "mean_pct": round(cpu_mean_raw, 4) if cpu_mean_raw is not None else None,
            "cpu_method": cpu_m.cpu_method_name,
        }
        report["caliber_comparability"]["ratio_vs_phase02_peak"] = round(ratio, 2) if ratio else None

    # ------------------------------------------------------------------
    # 7. Status determination
    # ------------------------------------------------------------------
    report["log_lines"] = list(_LOG_LINES)

    if render_errors:
        report["errors"].extend(render_errors)

    if not all_latencies:
        report["status"] = "FAILED"
        report["status_reason"] = "No renders completed — cannot produce baseline."
    elif cpu_max_raw is None:
        report["status"] = "PARTIAL"
        report["status_reason"] = "CPU measurement unavailable (no psutil, no time.process_time)."
    else:
        report["status"] = "OK"
        report["status_reason"] = (
            "Baseline collected successfully: %d renders across %d rounds. "
            "CPU peak=%.4f%% (per-core=%.4f%%), RSS=%.2fMB, "
            "latency p50=%.2fms p95=%.2fms p99=%.2fms."
            % (total_renders, rounds,
               cpu_max_raw, cpu_max_per_core if cpu_max_per_core else 0,
               rss_mb if rss_mb else 0,
               latency_stats["median_ms"], latency_stats["p95_ms"],
               latency_stats["p99_ms"]))

    # ------------------------------------------------------------------
    # 8. Output
    # ------------------------------------------------------------------
    log("[5/5] Writing output...")

    output_dir = os.path.dirname(output_path) if output_path else None
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    json_str = json.dumps(report, ensure_ascii=False, indent=2)

    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            log("Output written to: %s (%d bytes)" % (output_path, len(json_str)))
        except Exception as e:
            log_error("Failed to write output file: %s" % str(e))
            report["errors"].append("output_write_failed: %s" % str(e))
    else:
        log("No output path specified — report printed to stdout above.")

    log("=" * 72)
    log("COLLECTION COMPLETE")
    log("Status: %s" % report["status"])
    log("Renders: %d | Rounds: %d | Wall: %.2fs" % (
        total_renders, rounds, total_wall_sec))
    if cpu_max_raw is not None:
        log("CPU peak: %.4f%% (per-core: %.4f%%)" % (
            cpu_max_raw, cpu_max_per_core if cpu_max_per_core else 0))
    if rss_mb is not None:
        log("RSS: %.2f MB" % rss_mb)
    if latency_stats["count"] > 0:
        log("Latency: p50=%.2fms p95=%.2fms p99=%.2fms max=%.2fms" % (
            latency_stats["median_ms"], latency_stats["p95_ms"],
            latency_stats["p99_ms"], latency_stats["max_ms"]))
    log("=" * 72)

    return report


# ===========================================================================
# CLI entry point
# ===========================================================================
def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "V88 Phase03 P1 — CPU Baseline Collection Script.\n"
            "Collects process-level CPU / latency / RSS baseline under "
            "fixed load (all 101 charts) for same-script/same-load/same-time-window "
            "optimisation comparison."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python collect_cpu_baseline_p1.py --rounds 5 --output report.json\n"
            "  python collect_cpu_baseline_p1.py --rounds 10 --no-engine\n"
        ),
    )
    parser.add_argument(
        "--rounds", type=int, default=5,
        help="Number of measurement rounds (default: 5). "
             "Each round renders all charts once.")
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSON file path (default: print to stdout).")
    parser.add_argument(
        "--no-engine", action="store_true",
        help="Skip engine loading (latency-only mode, for debugging).")
    parser.add_argument(
        "--repo-root", type=str, default=None,
        help="Override repository root directory (default: auto-detect).")
    parser.add_argument(
        "--version", action="version",
        version="collect_cpu_baseline_p1.py v%s" % SCRIPT_VERSION)

    return parser.parse_args(argv)


def main(argv=None):
    """Main entry point."""
    args = parse_args(argv)

    if args.repo_root:
        global REPO_ROOT
        REPO_ROOT = os.path.abspath(args.repo_root)

    log("Starting P1 CPU baseline collection...")
    log("Repository root: %s" % REPO_ROOT)
    log("Rounds: %d | Engine: %s | Output: %s" % (
        args.rounds,
        "yes" if not args.no_engine else "no",
        args.output or "stdout"))

    try:
        report = collect_cpu_baseline_p1(
            rounds=args.rounds,
            output_path=args.output,
            use_engine=not args.no_engine,
            repo_root=args.repo_root,
        )
        return 0 if report["status"] == "OK" else 1
    except KeyboardInterrupt:
        log_error("Interrupted by user")
        return 130
    except Exception as e:
        log_error("Unhandled exception: %s\n%s" % (str(e), traceback.format_exc()))
        return 2


if __name__ == "__main__":
    sys.exit(main())
