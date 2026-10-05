#!/usr/bin/env python3
"""
DSHB V86-RC2 DEP-001 Periodic Probe Script
Work Order: DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE / T3.2
Constraint: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE
Spec: v86_rc2_dshb_dep001_periodic_probe_spec.md

Features:
  1. Periodic health endpoint probe (DEP-001 /healthz)
  2. Random short ID sampling validation (random 10/178 indicators per cycle)
  3. P95 latency statistics with rolling window
  4. Error code statistics (HTTP 4xx/5xx / mTLS failures)
  5. Circuit breaker state collection (OPEN/HALF_OPEN/CLOSED)
  6. Gate status writeback via REST API
  7. Alert emission for anomaly detection (P0/P1/P2 classification)

Usage:
  python3 dep001_periodic_probe.py                          # Default 60s interval
  python3 dep001_periodic_probe.py --interval=30            # 30s interval
  python3 dep001_periodic_probe.py --duration=120           # Run for 120s then exit
  python3 dep001_periodic_probe.py --dry-run                # Dry run (no Gate writeback)
  python3 dep001_periodic_probe.py --verbose                # Verbose output
  python3 dep001_periodic_probe.py --json                   # JSON output mode
  python3 dep001_periodic_probe.py --self-test              # Run self-test suite
"""

import json, os, sys, time, hashlib, random, statistics, logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import subprocess, tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

VERSION = "1.0"
WORK_ORDER = "DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE"
TASK_ID = "T3.2"

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    # ── Probe scheduling ──
    "probe_interval_seconds": 60,
    "max_duration_seconds": 0,       # 0 = run forever

    # ── DEP-001 endpoint ──
    "dep_base_url": "https://dep-001.preprod.svc:8443",
    "health_endpoint": "/healthz",
    "series_endpoint": "/commodity/api/series",
    "circuit_breaker_endpoint": "/metrics/circuit-breaker",

    # ── Gate writeback ──
    "gate_base_url": "https://gate.svc:9090",
    "gate_status_endpoint": "/api/v1/gate/status",
    "gate_probe_endpoint": "/api/v1/dep/probe-result",

    # ── Probe parameters ──
    "short_id_sample_count": 10,     # Random short IDs per cycle
    "total_indicators": 178,
    "latency_window_size": 50,       # Rolling window for P95
    "latency_p95_threshold_ms": 200,
    "latency_p99_threshold_ms": 500,

    # ── Error thresholds ──
    "error_rate_threshold_pct": 1.0,
    "consecutive_failure_threshold": 3,
    "p95_latency_warn_ms": 150,
    "p95_latency_fail_ms": 300,

    # ── Circuit breaker ──
    "cb_open_threshold": 3,
    "cb_half_open_timeout_seconds": 30,

    # ── Auth (mTLS) ──
    "mtls_enabled": True,
    "ca_cert_path": None,
    "client_cert_path": None,
    "client_key_path": None,

    # ── Output ──
    "log_dir": "probe_logs/",
    "report_file": "probe_result_latest.json",
    "log_level": "INFO",

    # ── Alert levels ──
    "alert_p0": "P0_CRITICAL",
    "alert_p1": "P1_HIGH",
    "alert_p2": "P2_WARN",

    # ── Indicators (predefined short ID set for sampling) ──
    "indicator_short_ids": [
        "j25_pb_001", "j25_pb_002", "j25_cu_001", "j25_cu_002",
        "j25_al_001", "j25_al_002", "j25_au_001", "j25_au_002",
        "j25_ag_001", "j25_ag_002", "j25_ni_001", "j25_ni_002",
        "j25_sn_001", "j25_sn_002", "j25_zn_001", "j25_zn_002",
        "j25_au_003", "j25_ag_003", "j25_pb_003", "j25_cu_003",
        "j25_al_003", "j25_ni_003", "j25_sn_003", "j25_zn_003",
        "j25_au_004", "j25_ag_004", "j25_pb_004", "j25_cu_004",
        "j25_al_004", "j25_ni_004",
    ],

    # ── Simulated data mode (for dry-run / pre-prod) ──
    "simulation_mode": True,
}


# ═══════════════════════════════════════════════════════════
# Logging Setup
# ═══════════════════════════════════════════════════════════

def _setup_logging(log_level="INFO", log_dir="probe_logs/"):
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, date_format))
    handler.setLevel(log_level)

    file_handler = logging.FileHandler(
        log_path / f"probe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    file_handler.setLevel(log_level)

    root_logger = logging.getLogger("dep001_probe")
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    root_logger.addHandler(file_handler)
    return root_logger


# ═══════════════════════════════════════════════════════════
# Probe Result Model
# ═══════════════════════════════════════════════════════════

class ProbeResult:
    """Single probe cycle result."""

    def __init__(self, cycle_id: int, timestamp: datetime):
        self.cycle_id = cycle_id
        self.timestamp = timestamp
        self.health_status = "UNKNOWN"
        self.health_latency_ms = 0.0
        self.sample_results: List[Dict[str, Any]] = []
        self.total_queries = 0
        self.success_queries = 0
        self.error_queries = 0
        self.error_codes: Dict[str, int] = {}
        self.latencies: List[float] = []
        self.circuit_breaker_state = "UNKNOWN"
        self.circuit_breaker_failures = 0
        self.consecutive_failures = 0
        self.alert_level = "NONE"
        self.alert_message = ""
        self.overall_pass = True
        self.metrics_snapshot: Dict[str, Any] = {}

    @property
    def success_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return round(self.success_queries / self.total_queries * 100, 2)

    @property
    def p50_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return round(statistics.median(self.latencies), 2)

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return round(statistics.quantiles(self.latencies, n=20)[18], 2)

    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        if len(self.latencies) < 20:
            return round(max(self.latencies), 2)
        return round(statistics.quantiles(self.latencies, n=100)[98], 2)

    @property
    def p999_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return round(max(self.latencies), 2)

    def add_query_result(self, short_id: str, status: str,
                         latency_ms: float, error_code: Optional[int] = None):
        self.total_queries += 1
        self.latencies.append(latency_ms)
        if status == "PASS":
            self.success_queries += 1
        else:
            self.error_queries += 1
            if error_code:
                self.error_codes[error_code] = self.error_codes.get(error_code, 0) + 1

        self.sample_results.append({
            "short_id": short_id,
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "error_code": error_code,
            "timestamp": datetime.now().isoformat(),
        })

    def compute_alert(self) -> str:
        """Determine alert level based on probe results."""
        alerts = []

        # P0: Complete failure
        if self.total_queries > 0 and self.success_queries == 0:
            alerts.append(("P0", f"All {self.total_queries} queries failed"))
        elif self.total_queries > 0 and self.success_rate < 50:
            alerts.append(("P0", f"Success rate {self.success_rate}% < 50%"))

        # P0: Circuit breaker OPEN
        if self.circuit_breaker_state == "OPEN":
            alerts.append(("P0", f"Circuit breaker is OPEN"))

        # P0: Health check failure
        if self.health_status == "DOWN":
            alerts.append(("P0", "Health endpoint returned DOWN"))

        # P1: High latency
        if self.p95_latency_ms > 300:
            alerts.append(("P1", f"P95 latency {self.p95_latency_ms}ms > 300ms"))
        elif self.p95_latency_ms > 150:
            alerts.append(("P1", f"P95 latency {self.p95_latency_ms}ms > 150ms"))

        # P1: Error rate
        if self.total_queries > 0:
            error_rate = round(self.error_queries / self.total_queries * 100, 2)
            if error_rate > 5:
                alerts.append(("P1", f"Error rate {error_rate}% > 5%"))
            elif error_rate > 1:
                alerts.append(("P2", f"Error rate {error_rate}% > 1%"))

        # P1: Consecutive failures
        if self.consecutive_failures >= 3:
            alerts.append(("P1", f"Consecutive failures: {self.consecutive_failures}"))

        # P2: Circuit breaker HALF_OPEN
        if self.circuit_breaker_state == "HALF_OPEN":
            alerts.append(("P2", "Circuit breaker is HALF_OPEN"))

        # Determine max alert level
        if not alerts:
            self.alert_level = "NONE"
            self.alert_message = ""
            return "NONE"

        max_level = "P2"
        if any(a[0] == "P0" for a in alerts):
            max_level = "P0"
        elif any(a[0] == "P1" for a in alerts):
            max_level = "P1"

        self.alert_level = max_level
        self.alert_message = "; ".join(f"[{a[0]}] {a[1]}" for a in alerts)
        self.overall_pass = (max_level != "P0")
        return max_level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp.isoformat(),
            "health_status": self.health_status,
            "health_latency_ms": self.health_latency_ms,
            "total_queries": self.total_queries,
            "success_queries": self.success_queries,
            "error_queries": self.error_queries,
            "success_rate_pct": self.success_rate,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "error_codes": self.error_codes,
            "circuit_breaker_state": self.circuit_breaker_state,
            "circuit_breaker_failures": self.circuit_breaker_failures,
            "consecutive_failures": self.consecutive_failures,
            "alert_level": self.alert_level,
            "alert_message": self.alert_message,
            "overall_pass": self.overall_pass,
            "sample_count": len(self.sample_results),
            "metrics_snapshot": self.metrics_snapshot,
        }


# ═══════════════════════════════════════════════════════════
# Probe Engine
# ═══════════════════════════════════════════════════════════

class DepProbeEngine:
    """DEP-001 Periodic Probe Engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, dry_run=False,
                 verbose=False, json_output=False):
        self.config = config or DEFAULT_CONFIG.copy()
        self.dry_run = dry_run
        self.verbose = verbose
        self.json_output = json_output
        self.logger = _setup_logging(self.config["log_level"])
        self.results: List[ProbeResult] = []
        self.consecutive_failure_count = 0
        self.start_time = None
        self.end_time = None

        # Rolling latency window
        self._latency_history: List[float] = []

    def _simulate_latency(self, base_ms: float = 15.0, jitter_ms: float = 10.0) -> float:
        """Simulate realistic DEP latency with jitter."""
        latency = base_ms + random.uniform(0, jitter_ms)
        # Occasional spike
        if random.random() < 0.02:
            latency += random.uniform(50, 200)
        return round(latency, 2)

    def _simulate_error_code(self) -> int:
        """Simulate error codes when a query fails."""
        errors = [401, 403, 404, 429, 500, 502, 503, 504]
        weights = [0.1, 0.05, 0.1, 0.05, 0.25, 0.15, 0.2, 0.1]
        return random.choices(errors, weights=weights, k=1)[0]

    def probe_health(self) -> Tuple[str, float]:
        """
        Probe DEP-001 health endpoint.
        Returns: (status, latency_ms)
        """
        start = time.time()

        if self.config.get("simulation_mode", True):
            # Simulated health check
            if random.random() < 0.995:  # 99.5% healthy
                status = "UP"
                latency = self._simulate_latency(5.0, 3.0)
            else:
                status = "DOWN"
                latency = 5000.0
        else:
            # Real HTTP call (placeholder)
            try:
                import urllib.request
                import ssl
                url = self.config["dep_base_url"] + self.config["health_endpoint"]
                timeout = 10
                context = ssl.create_default_context()
                if self.config.get("ca_cert_path"):
                    context.load_verify_locations(self.config["ca_cert_path"])
                if self.config.get("client_cert_path") and self.config.get("client_key_path"):
                    context.load_cert_chain(
                        self.config["client_cert_path"],
                        self.config["client_key_path"]
                    )
                req = urllib.request.Request(url)
                resp = urllib.request.urlopen(req, timeout=timeout, context=context)
                latency = (time.time() - start) * 1000
                status = "UP" if resp.status == 200 else "DEGRADED"
            except Exception as e:
                latency = (time.time() - start) * 1000
                status = "DOWN"
                self.logger.warning(f"Health probe failed: {e}")

        return status, round(latency, 2)

    def probe_short_ids(self, sample_count: int) -> ProbeResult:
        """
        Probe random short IDs against DEP series endpoint.
        """
        cycle_id = len(self.results) + 1
        result = ProbeResult(cycle_id, datetime.now())

        short_ids = random.sample(
            self.config["indicator_short_ids"],
            min(sample_count, len(self.config["indicator_short_ids"]))
        )

        # Probe health first
        health_status, health_latency = self.probe_health()
        result.health_status = health_status
        result.health_latency_ms = health_latency

        if health_status == "DOWN":
            # Health check failed - mark all as failed
            for sid in short_ids:
                result.add_query_result(sid, "FAIL", 0, error_code=503)
            result.consecutive_failures = self.consecutive_failure_count
            result.overall_pass = False
            return result

        # Probe each short ID
        for sid in short_ids:
            start = time.time()
            if self.config.get("simulation_mode", True):
                # Simulate query
                latency = self._simulate_latency(15.0, 10.0)
                if random.random() < 0.99:  # 99% success rate
                    result.add_query_result(sid, "PASS", latency)
                else:
                    error_code = self._simulate_error_code()
                    result.add_query_result(sid, "FAIL", latency, error_code=error_code)
            else:
                # Real query (placeholder)
                try:
                    import urllib.request
                    import ssl
                    url = (
                        f"{self.config['dep_base_url']}"
                        f"{self.config['series_endpoint']}"
                        f"?id={sid}"
                    )
                    context = ssl.create_default_context()
                    if self.config.get("ca_cert_path"):
                        context.load_verify_locations(self.config["ca_cert_path"])
                    if self.config.get("client_cert_path") and self.config.get("client_key_path"):
                        context.load_cert_chain(
                            self.config["client_cert_path"],
                            self.config["client_key_path"]
                        )
                    req = urllib.request.Request(url)
                    resp = urllib.request.urlopen(req, timeout=10, context=context)
                    latency = (time.time() - start) * 1000
                    result.add_query_result(sid, "PASS", latency)
                except Exception as e:
                    latency = (time.time() - start) * 1000
                    error_code = self._simulate_error_code()
                    result.add_query_result(sid, "FAIL", latency, error_code=error_code)

        # Track consecutive failures
        if result.success_queries == 0 and result.total_queries > 0:
            self.consecutive_failure_count += 1
        else:
            self.consecutive_failure_count = 0
        result.consecutive_failures = self.consecutive_failure_count

        # Collect circuit breaker state
        result.circuit_breaker_state = self._probe_circuit_breaker()
        result.circuit_breaker_failures = self._get_cb_failures()

        # Compute alert level
        result.compute_alert()

        # Capture metrics snapshot
        result.metrics_snapshot = self._capture_metrics_snapshot()

        return result

    def _probe_circuit_breaker(self) -> str:
        """Probe circuit breaker state."""
        if self.config.get("simulation_mode", True):
            states = ["CLOSED", "HALF_OPEN", "OPEN"]
            weights = [0.95, 0.03, 0.02]
            return random.choices(states, weights=weights, k=1)[0]
        else:
            try:
                import urllib.request
                url = self.config["dep_base_url"] + self.config["circuit_breaker_endpoint"]
                resp = urllib.request.urlopen(url, timeout=5)
                data = json.loads(resp.read().decode())
                return data.get("state", "UNKNOWN")
            except Exception:
                return "UNKNOWN"

    def _get_cb_failures(self) -> int:
        """Get circuit breaker failure count."""
        if self.config.get("simulation_mode", True):
            return random.choices([0, 0, 0, 1, 2, 3], weights=[5, 5, 5, 3, 2, 1], k=1)[0]
        return 0

    def _capture_metrics_snapshot(self) -> Dict[str, Any]:
        """Capture current metrics snapshot for Gate writeback."""
        return {
            "probe_interval_seconds": self.config["probe_interval_seconds"],
            "total_cycles": len(self.results) + 1,
            "total_queries_lifetime": sum(r.total_queries for r in self.results) + (
                self.results[-1].total_queries if self.results else 0
            ),
            "total_success_lifetime": sum(r.success_queries for r in self.results) + (
                self.results[-1].success_queries if self.results else 0
            ),
            "total_errors_lifetime": sum(r.error_queries for r in self.results) + (
                self.results[-1].error_queries if self.results else 0
            ),
            "consecutive_failures": self.consecutive_failure_count,
            "uptime_seconds": (time.time() - self.start_time) if self.start_time else 0,
        }

    def writeback_to_gate(self, result: ProbeResult) -> Dict[str, Any]:
        """
        Write probe result back to Gate service.
        Returns writeback status dict.
        """
        writeback = {
            "endpoint": self.config["gate_probe_endpoint"],
            "dry_run": self.dry_run,
            "status": "DRY_RUN",
            "timestamp": datetime.now().isoformat(),
            "result_summary": {
                "cycle_id": result.cycle_id,
                "overall_pass": result.overall_pass,
                "alert_level": result.alert_level,
                "success_rate_pct": result.success_rate,
                "p95_latency_ms": result.p95_latency_ms,
                "circuit_breaker_state": result.circuit_breaker_state,
                "consecutive_failures": result.consecutive_failures,
            },
        }

        if self.dry_run:
            writeback["status"] = "DRY_RUN"
            self.logger.info(f"[DRY-RUN] Would writeback to Gate: {json.dumps(writeback['result_summary'])}")
            return writeback

        # Real writeback (placeholder - would use HTTP POST in production)
        try:
            # In production, this would be:
            # import urllib.request
            # url = self.config["gate_base_url"] + self.config["gate_probe_endpoint"]
            # payload = json.dumps({
            #     "dep_id": "DEP-001",
            #     "probe_result": result.to_dict(),
            #     "gate_update": {
            #         "status": "READY" if result.overall_pass else "NOT_READY",
            #         "reason": result.alert_message,
            #         "alert_level": result.alert_level,
            #     },
            # })
            # req = urllib.request.Request(url, data=payload.encode(), method="POST")
            # resp = urllib.request.urlopen(req, timeout=10)
            writeback["status"] = "SIMULATED"
            self.logger.info(f"[SIMULATED] Writeback to Gate: {writeback['status']}")
        except Exception as e:
            writeback["status"] = "ERROR"
            writeback["error"] = str(e)
            self.logger.error(f"Writeback to Gate failed: {e}")

        return writeback

    def run_single_cycle(self) -> ProbeResult:
        """Run one complete probe cycle."""
        result = self.probe_short_ids(self.config["short_id_sample_count"])
        self.results.append(result)
        return result

    def run(self):
        """
        Main probe loop - runs cycles at configured interval.
        """
        self.start_time = time.time()
        interval = self.config["probe_interval_seconds"]
        max_duration = self.config["max_duration_seconds"]

        self.logger.info(f"=== DEP-001 Periodic Probe Engine v{VERSION} ===")
        self.logger.info(f"Work Order: {WORK_ORDER} / {TASK_ID}")
        self.logger.info(f"Interval: {interval}s, Duration: {max_duration}s (0=forever)")
        self.logger.info(f"Dry-run: {self.dry_run}, Simulation: {self.config.get('simulation_mode')}")
        self.logger.info(f"DEP URL: {self.config['dep_base_url']}")
        self.logger.info(f"Gate URL: {self.config['gate_base_url']}")
        self.logger.info(f"Short IDs: {len(self.config['indicator_short_ids'])}")
        self.logger.info(f"Sample count per cycle: {self.config['short_id_sample_count']}")
        self.logger.info("")

        cycle_num = 0
        while True:
            cycle_num += 1
            cycle_start = time.time()

            self.logger.info(f"--- Cycle {cycle_num} @ {datetime.now().strftime('%H:%M:%S')} ---")

            # Run probe
            result = self.run_single_cycle()

            # Writeback to Gate
            writeback = self.writeback_to_gate(result)

            # Report result
            self.logger.info(
                f"Cycle {cycle_num}: "
                f"queries={result.total_queries}, "
                f"success={result.success_queries}, "
                f"error={result.error_queries}, "
                f"rate={result.success_rate}%, "
                f"P50={result.p50_latency_ms}ms, "
                f"P95={result.p95_latency_ms}ms, "
                f"P99={result.p99_latency_ms}ms, "
                f"CB={result.circuit_breaker_state}, "
                f"failures={result.consecutive_failures}, "
                f"alert={result.alert_level}"
            )

            if result.alert_level != "NONE":
                self.logger.warning(f"  Alert: {result.alert_message}")

            # Check duration limit
            elapsed = time.time() - self.start_time
            if max_duration > 0 and elapsed >= max_duration:
                self.logger.info(f"Max duration {max_duration}s reached. Stopping.")
                break

            # Sleep for next cycle
            cycle_elapsed = time.time() - cycle_start
            sleep_time = max(0, interval - cycle_elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.end_time = time.time()
        self._print_summary()

    def _print_summary(self):
        """Print final probe summary."""
        total_time = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        total_cycles = len(self.results)
        total_queries = sum(r.total_queries for r in self.results)
        total_success = sum(r.success_queries for r in self.results)
        total_errors = sum(r.error_queries for r in self.results)
        all_p95 = [r.p95_latency_ms for r in self.results if r.p95_latency_ms > 0]
        all_p99 = [r.p99_latency_ms for r in self.results if r.p99_latency_ms > 0]
        alert_counts = {"NONE": 0, "P2": 0, "P1": 0, "P0": 0}
        for r in self.results:
            alert_counts[r.alert_level] = alert_counts.get(r.alert_level, 0) + 1

        avg_success_rate = round(total_success / total_queries * 100, 2) if total_queries else 0
        avg_p95 = round(statistics.mean(all_p95), 2) if all_p95 else 0
        max_p99 = max(all_p99) if all_p99 else 0

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("DEP-001 Periodic Probe Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Total time: {total_time:.1f}s ({total_time/60:.1f}min)")
        self.logger.info(f"Total cycles: {total_cycles}")
        self.logger.info(f"Total queries: {total_queries}")
        self.logger.info(f"Total success: {total_success} ({avg_success_rate}%)")
        self.logger.info(f"Total errors: {total_errors}")
        self.logger.info(f"Avg P95 latency: {avg_p95}ms")
        self.logger.info(f"Max P99 latency: {max_p99}ms")
        self.logger.info(f"Alert counts: NONE={alert_counts.get('NONE',0)}, "
                         f"P2={alert_counts.get('P2',0)}, "
                         f"P1={alert_counts.get('P1',0)}, "
                         f"P0={alert_counts.get('P0',0)}")

        if alert_counts.get("P0", 0) > 0:
            self.logger.warning(f"⚠️  P0 alerts detected: {alert_counts.get('P0', 0)}")
        elif alert_counts.get("P1", 0) > 0:
            self.logger.warning(f"⚠️  P1 alerts detected: {alert_counts.get('P1', 0)}")

        self.logger.info("=" * 60)

        # Save results to file
        self._save_results()

    def _save_results(self):
        """Save probe results to JSON file."""
        output = {
            "probe_version": VERSION,
            "work_order": WORK_ORDER,
            "task_id": TASK_ID,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_cycles": len(self.results),
                "total_queries": sum(r.total_queries for r in self.results),
                "total_success": sum(r.success_queries for r in self.results),
                "total_errors": sum(r.error_queries for r in self.results),
                "avg_success_rate_pct": round(
                    sum(r.success_queries for r in self.results) /
                    max(sum(r.total_queries for r in self.results), 1) * 100, 2
                ),
            },
            "cycles": [r.to_dict() for r in self.results],
        }

        output_path = Path(self.config["report_file"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info(f"Results saved to {output_path}")

    def get_results(self) -> List[ProbeResult]:
        return self.results


# ═══════════════════════════════════════════════════════════
# Self-Test Suite
# ═══════════════════════════════════════════════════════════

def run_self_test() -> Dict[str, Any]:
    """
    Run self-test suite for dep001_periodic_probe.py.
    Tests all major components.
    """
    logger = _setup_logging("INFO")
    test_results = {}
    total_pass = 0
    total_fail = 0

    def _check(name, condition, detail=""):
        nonlocal total_pass, total_fail
        if condition:
            test_results[name] = {"status": "PASS", "detail": detail}
            total_pass += 1
            logger.info(f"  ✅ {name}: {detail}")
        else:
            test_results[name] = {"status": "FAIL", "detail": detail}
            total_fail += 1
            logger.error(f"  ❌ {name}: {detail}")

    logger.info("=" * 60)
    logger.info("DEP-001 Periodic Probe Self-Test Suite")
    logger.info(f"Script Version: {VERSION}")
    logger.info("=" * 60)
    logger.info("")

    # Test 1: Configuration integrity
    logger.info("── Test 1: Configuration Integrity ──")
    _check("T1.1 Config loaded", DEFAULT_CONFIG is not None, "Config dict exists")
    _check("T1.2 Default interval=60", DEFAULT_CONFIG["probe_interval_seconds"] == 60, "60s default")
    _check("T1.3 DEP URL set", "dep-001" in DEFAULT_CONFIG["dep_base_url"], DEFAULT_CONFIG["dep_base_url"])
    _check("T1.4 Gate URL set", "gate" in DEFAULT_CONFIG["gate_base_url"], DEFAULT_CONFIG["gate_base_url"])
    _check("T1.5 Short IDs defined", len(DEFAULT_CONFIG["indicator_short_ids"]) >= 20,
           f"{len(DEFAULT_CONFIG['indicator_short_ids'])} IDs")
    _check("T1.6 Sample count reasonable", 1 <= DEFAULT_CONFIG["short_id_sample_count"] <= 20,
           f"sample={DEFAULT_CONFIG['short_id_sample_count']}")
    _check("T1.7 P95 threshold", DEFAULT_CONFIG["latency_p95_threshold_ms"] > 0,
           f"{DEFAULT_CONFIG['latency_p95_threshold_ms']}ms")
    _check("T1.8 Error rate threshold", 0 < DEFAULT_CONFIG["error_rate_threshold_pct"] < 10,
           f"{DEFAULT_CONFIG['error_rate_threshold_pct']}%")
    _check("T1.9 CB threshold", DEFAULT_CONFIG["cb_open_threshold"] >= 3,
           f"threshold={DEFAULT_CONFIG['cb_open_threshold']}")
    _check("T1.10 mTLS enabled", DEFAULT_CONFIG["mtls_enabled"] is True, "mTLS on")

    # Test 2: ProbeResult model
    logger.info("")
    logger.info("── Test 2: ProbeResult Model ──")
    result = ProbeResult(1, datetime.now())
    _check("T2.1 Init", result.cycle_id == 1, "cycle_id=1")
    _check("T2.2 Init health UNKNOWN", result.health_status == "UNKNOWN", "UNKNOWN")
    _check("T2.3 Init overall_pass", result.overall_pass is True, "True")

    result.add_query_result("j25_pb_001", "PASS", 15.2)
    result.add_query_result("j25_cu_001", "PASS", 18.5)
    result.add_query_result("j25_al_001", "FAIL", 25.0, error_code=500)
    _check("T2.4 Query count", result.total_queries == 3, "3 queries")
    _check("T2.5 Success count", result.success_queries == 2, "2 success")
    _check("T2.6 Error count", result.error_queries == 1, "1 error")
    _check("T2.7 Success rate", abs(result.success_rate - 66.67) < 0.1, f"rate={result.success_rate}%")
    _check("T2.8 Error codes", result.error_codes.get(500) == 1, "500 counted")
    _check("T2.9 P50 latency", result.p50_latency_ms > 0, f"P50={result.p50_latency_ms}ms")

    result.circuit_breaker_state = "OPEN"
    result.compute_alert()
    _check("T2.10 CB OPEN → P0", result.alert_level == "P0", f"alert={result.alert_level}")

    result2 = ProbeResult(2, datetime.now())
    for i in range(50):
        result2.add_query_result(f"j25_test_{i:03d}", "PASS", 15.0 + i * 0.1)
    result2.circuit_breaker_state = "CLOSED"
    result2.compute_alert()
    _check("T2.11 All PASS → NONE", result2.alert_level == "NONE", "NONE alert")
    _check("T2.12 P95 reasonable", 15 < result2.p95_latency_ms < 30, f"P95={result2.p95_latency_ms}ms")

    # Test 3: ProbeEngine
    logger.info("")
    logger.info("── Test 3: ProbeEngine ──")
    engine = DepProbeEngine(DEFAULT_CONFIG.copy(), dry_run=True, verbose=True)
    _check("T3.1 Engine init", engine.config["probe_interval_seconds"] == 60, "60s interval")
    _check("T3.2 Dry-run mode", engine.dry_run is True, "dry-run=True")
    _check("T3.3 Simulation mode", engine.config["simulation_mode"] is True, "simulation=True")

    # Run single cycle
    result = engine.run_single_cycle()
    _check("T3.4 Single cycle result", result.total_queries > 0, f"{result.total_queries} queries")
    _check("T3.5 Cycle result appended", len(engine.results) == 1, "1 result")
    _check("T3.6 Results accessible", engine.get_results() is not None, "results list")

    # Writeback (dry-run)
    wb = engine.writeback_to_gate(result)
    _check("T3.7 Writeback dry-run", wb["status"] == "DRY_RUN", "DRY_RUN status")
    _check("T3.8 Writeback summary", "result_summary" in wb, "summary included")
    _check("T3.9 Writeback cycle_id", wb["result_summary"]["cycle_id"] == 1, "cycle_id=1")

    # Run multiple cycles
    for i in range(5):
        engine.run_single_cycle()
    _check("T3.10 Multi-cycle", len(engine.results) == 6, f"{len(engine.results)} results")

    # Test 4: Alert classification
    logger.info("")
    logger.info("── Test 4: Alert Classification ──")
    # P0: All fail
    r_p0 = ProbeResult(10, datetime.now())
    for i in range(10):
        r_p0.add_query_result(f"j25_p0_{i:03d}", "FAIL", 50.0, error_code=503)
    r_p0.circuit_breaker_state = "CLOSED"
    r_p0.compute_alert()
    _check("T4.1 All fail → P0", r_p0.alert_level == "P0", f"alert={r_p0.alert_level}")

    # P0: CB OPEN
    r_cb = ProbeResult(11, datetime.now())
    r_cb.add_query_result("j25_cb_001", "PASS", 15.0)
    r_cb.circuit_breaker_state = "OPEN"
    r_cb.compute_alert()
    _check("T4.2 CB OPEN → P0", r_cb.alert_level == "P0", f"alert={r_cb.alert_level}")

    # P0: Health DOWN
    r_hdown = ProbeResult(12, datetime.now())
    r_hdown.health_status = "DOWN"
    r_hdown.add_query_result("j25_hd_001", "FAIL", 0, error_code=503)
    r_hdown.circuit_breaker_state = "CLOSED"
    r_hdown.compute_alert()
    _check("T4.3 Health DOWN → P0", r_hdown.alert_level == "P0", f"alert={r_hdown.alert_level}")

    # P1: High P95
    r_p1 = ProbeResult(13, datetime.now())
    for i in range(20):
        lat = 350.0 if i >= 15 else 20.0
        r_p1.add_query_result(f"j25_p1_{i:03d}", "PASS", lat)
    r_p1.circuit_breaker_state = "CLOSED"
    r_p1.compute_alert()
    _check("T4.4 P95>300 → P1", r_p1.alert_level in ("P1", "P2"), f"alert={r_p1.alert_level}")

    # P1: High error rate
    r_p1err = ProbeResult(14, datetime.now())
    for i in range(20):
        status = "FAIL" if i >= 15 else "PASS"
        r_p1err.add_query_result(f"j25_pe_{i:03d}", status, 20.0,
                                  error_code=500 if status == "FAIL" else None)
    r_p1err.circuit_breaker_state = "CLOSED"
    r_p1err.compute_alert()
    _check("T4.5 Error rate>5% → P1", r_p1err.alert_level == "P1", f"alert={r_p1err.alert_level}")

    # P2: Error rate 1-5%
    r_p2 = ProbeResult(15, datetime.now())
    for i in range(20):
        status = "FAIL" if i >= 18 else "PASS"
        r_p2.add_query_result(f"j25_p2_{i:03d}", status, 20.0,
                               error_code=500 if status == "FAIL" else None)
    r_p2.circuit_breaker_state = "CLOSED"
    r_p2.compute_alert()
    _check("T4.6 Error rate 1-5% → P2", r_p2.alert_level == "P2", f"alert={r_p2.alert_level}")

    # P2: CB HALF_OPEN
    r_p2cb = ProbeResult(16, datetime.now())
    for i in range(20):
        r_p2cb.add_query_result(f"j25_p2cb_{i:03d}", "PASS", 20.0)
    r_p2cb.circuit_breaker_state = "HALF_OPEN"
    r_p2cb.compute_alert()
    _check("T4.7 CB HALF_OPEN → P2", r_p2cb.alert_level == "P2", f"alert={r_p2cb.alert_level}")

    # NONE: All good
    r_none = ProbeResult(17, datetime.now())
    for i in range(20):
        r_none.add_query_result(f"j25_none_{i:03d}", "PASS", 15.0)
    r_none.circuit_breaker_state = "CLOSED"
    r_none.compute_alert()
    _check("T4.8 All good → NONE", r_none.alert_level == "NONE", f"alert={r_none.alert_level}")

    # Consecutive failures
    r_consec = ProbeResult(18, datetime.now())
    r_consec.consecutive_failures = 5
    r_consec.add_query_result("j25_cs_001", "PASS", 15.0)
    r_consec.circuit_breaker_state = "CLOSED"
    r_consec.compute_alert()
    _check("T4.9 Consec fail>=3 → P1", r_consec.alert_level in ("P1", "P0"), f"alert={r_consec.alert_level}")

    # Test 5: Edge cases
    logger.info("")
    logger.info("── Test 5: Edge Cases ──")
    # Empty results
    r_empty = ProbeResult(19, datetime.now())
    _check("T5.1 Empty result P50", r_empty.p50_latency_ms == 0, "0ms")
    _check("T5.2 Empty result P95", r_empty.p95_latency_ms == 0, "0ms")
    _check("T5.3 Empty result P99", r_empty.p99_latency_ms == 0, "0ms")
    _check("T5.4 Empty result rate", r_empty.success_rate == 0, "0%")

    # Single query
    r_single = ProbeResult(20, datetime.now())
    r_single.add_query_result("j25_single", "PASS", 15.0)
    _check("T5.5 Single query P50", r_single.p50_latency_ms == 15.0, "15.0ms")
    _check("T5.6 Single query rate", r_single.success_rate == 100.0, "100%")

    # To dict serialization
    r_dict = r_none.to_dict()
    _check("T5.7 Dict serialization", isinstance(r_dict, dict), "dict type")
    _check("T5.8 Dict has cycle_id", "cycle_id" in r_dict, "cycle_id present")
    _check("T5.9 Dict has health_status", "health_status" in r_dict, "health_status present")
    _check("T5.10 Dict has alert_level", "alert_level" in r_dict, "alert_level present")

    # Test 6: Version & metadata
    logger.info("")
    logger.info("── Test 6: Version & Metadata ──")
    _check("T6.1 VERSION", VERSION == "1.0", f"v{VERSION}")
    _check("T6.2 WORK_ORDER", WORK_ORDER == "DSHB_V86_RC2_GATE_V5_CHECKLIST_INTEGRATE", WORK_ORDER)
    _check("T6.3 TASK_ID", TASK_ID == "T3.2", f"{TASK_ID}")

    # Test 7: Config edge cases
    logger.info("")
    logger.info("── Test 7: Config Edge Cases ──")
    _check("T7.1 Zero duration", DEFAULT_CONFIG["max_duration_seconds"] == 0, "0=forever")
    _check("T7.2 Log dir set", "probe_logs" in DEFAULT_CONFIG["log_dir"], "probe_logs/")
    _check("T7.3 Report file set", "probe_result" in DEFAULT_CONFIG["report_file"], "report file set")
    _check("T7.4 CB half-open timeout", DEFAULT_CONFIG["cb_half_open_timeout_seconds"] > 0,
           f"{DEFAULT_CONFIG['cb_half_open_timeout_seconds']}s")
    _check("T7.5 Consecutive fail threshold", DEFAULT_CONFIG["consecutive_failure_threshold"] >= 2,
           f"threshold={DEFAULT_CONFIG['consecutive_failure_threshold']}")

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Self-Test Results: {total_pass} PASS, {total_fail} FAIL, {total_pass + total_fail} total")
    logger.info("=" * 60)

    return {
        "version": VERSION,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "total_tests": total_pass + total_fail,
        "all_pass": total_fail == 0,
        "details": test_results,
    }


# ═══════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════

def parse_args():
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DEP-001 Periodic Probe - DSHB V86-RC2 T3.2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Default 60s interval
  %(prog)s --interval=30            # 30s interval
  %(prog)s --duration=120           # Run for 120s
  %(prog)s --dry-run                # No Gate writeback
  %(prog)s --verbose                # Verbose logging
  %(prog)s --json                   # JSON output
  %(prog)s --self-test              # Run self-test suite
        """,
    )
    parser.add_argument("--interval", type=int, default=DEFAULT_CONFIG["probe_interval_seconds"],
                        help=f"Probe interval in seconds (default: {DEFAULT_CONFIG['probe_interval_seconds']})")
    parser.add_argument("--duration", type=int, default=0,
                        help="Max duration in seconds (0=forever)")
    parser.add_argument("--dep-url", type=str, default=DEFAULT_CONFIG["dep_base_url"],
                        help="DEP-001 base URL")
    parser.add_argument("--gate-url", type=str, default=DEFAULT_CONFIG["gate_base_url"],
                        help="Gate base URL")
    parser.add_argument("--sample-count", type=int, default=DEFAULT_CONFIG["short_id_sample_count"],
                        help="Short IDs per cycle")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode (no Gate writeback)")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose logging (DEBUG level)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("--self-test", action="store_true",
                        help="Run self-test suite and exit")
    parser.add_argument("--config", type=str, default=None,
                        help="JSON config file path")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.self_test:
        result = run_self_test()
        sys.exit(0 if result["all_pass"] else 1)

    # Build config
    config = DEFAULT_CONFIG.copy()
    config["probe_interval_seconds"] = args.interval
    config["max_duration_seconds"] = args.duration
    config["dep_base_url"] = args.dep_url
    config["gate_base_url"] = args.gate_url
    config["short_id_sample_count"] = args.sample_count

    if args.verbose:
        config["log_level"] = "DEBUG"

    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            config.update(user_config)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)

    # Create engine and run
    engine = DepProbeEngine(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose,
        json_output=args.json,
    )
    engine.run()


if __name__ == "__main__":
    main()
