#!/usr/bin/env python3
"""
Phase04 psutil Steady-State CPU Collector — Production Daemon
================================================================

TASK_ID: V88_PHASE03_P2_DSHE_GATE_HARDEN_AND_PHASE04_PREP_PARTIAL_CHECK_JOB / T1
AGENT: DSHE | BRANCH: feature/v88-g1 (BRANCH_LOCKED)
PHASE: Phase04 (NOT Phase03 gate path)

This daemon provides production-ready steady-state CPU collection using
psutil system-level measurement (same caliber as Phase03 P0-12).

CONSTRAINTS:
- Does NOT modify Phase03 gate paths
- Does NOT modify engine code
- Does NOT call ZHIJI API
- Stays in opt-phase04-psutil-collector/ independent directory
- Enabled only after Phase04 formal work order

USAGE:
  python3 simple_daemon.py --config config.yaml
  python3 simple_daemon.py --config config.yaml --daemon
  python3 simple_daemon.py --config config.yaml --test

C-3 Constraint Compliance:
- Phase03 P0-12 native PASS: steady-state CPU = 0.0654% (threshold 1.75%)
- Phase04 inherits same psutil.cpu_times() system-level caliber
- No prototype→production caliber switch
"""

import argparse
import datetime
import hashlib
import json
import logging
import os
import signal
import sys
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Imports (graceful degradation) ────────────────────────────────
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# ─── Version ───────────────────────────────────────────────────────
VERSION = "1.0.0-prod"
TASK_ID = "V88_PHASE03_P2_DSHE_GATE_HARDEN_AND_PHASE04_PREP_PARTIAL_CHECK_JOB"

# ─── Logging ───────────────────────────────────────────────────────
logger = logging.getLogger("phase04_psutil_collector")


# ═══════════════════════════════════════════════════════════════════
# CONFIG LOADER
# ═══════════════════════════════════════════════════════════════════

def load_config(config_path: str) -> Dict[str, Any]:
    """Load and validate YAML configuration file."""
    if not YAML_AVAILABLE:
        logger.warning("PyYAML not available, using defaults")
        return DEFAULT_CONFIG
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Merge with defaults
    merged = {**DEFAULT_CONFIG, **config}
    
    # Validate critical fields
    validate_config(merged)
    
    return merged


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration for critical fields."""
    errors = []
    
    if not config.get("collector", {}).get("enabled", False):
        logger.info("Collector is DISABLED (wait for Phase04 work order)")
    
    # Check thresholds are valid
    alarm = config.get("alarm", {})
    if alarm.get("enabled", False):
        cpu_thresh = alarm.get("cpu_thresholds", {}).get("steady_state_pct", {})
        if cpu_thresh.get("fuse", 1.75) < cpu_thresh.get("warning", 0.50):
            errors.append("CPU fuse threshold must be >= warning threshold")
    
    if errors:
        raise ValueError(f"Config validation failed: {'; '.join(errors)}")


# ═══════════════════════════════════════════════════════════════════
# CPU METER (Production-Grade)
# ═══════════════════════════════════════════════════════════════════

class SystemCpuMeter:
    """
    Production-grade system-level CPU meter using psutil.
    
    Caliber: psutil.cpu_times() system-level full-link window
    (NOT process-level psutil.Process().cpu_percent())
    
    This matches Phase03 P0-12 steady-state measurement caliber exactly.
    """
    
    def __init__(self, nproc: Optional[int] = None):
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil is required for CPU measurement")
        
        self.nproc = nproc or psutil.cpu_count() or 1
        self._last_times = None
        self._last_wall = None
        self._initialized = False
        
        logger.info(f"SystemCpuMeter initialized (nproc={self.nproc}, psutil={psutil.__version__})")
    
    def pre_warm(self):
        """Pre-warm psutil for consistent readings."""
        # First call to cpu_times() initializes internal state
        self._last_times = psutil.cpu_times()
        self._last_wall = time.time()
        time.sleep(0.1)
        self._last_times = psutil.cpu_times()
        self._last_wall = time.time()
        self._initialized = True
        logger.info("SystemCpuMeter pre-warmed")
    
    def measure_interval(self, interval_sec: float) -> Dict[str, Any]:
        """
        Measure system CPU utilization over a given interval.
        
        Returns dict with wall_sec, total_cpu_sec, cpu_pct.
        """
        # Get baseline
        t0 = time.time()
        cpu_t0 = psutil.cpu_times()
        idle_t0 = cpu_t0.idle + cpu_t0.iowait
        
        # Wait
        time.sleep(interval_sec)
        
        # Get endpoint
        t1 = time.time()
        cpu_t1 = psutil.cpu_times()
        idle_t1 = cpu_t1.idle + cpu_t1.iowait
        
        # Calculate
        wall_sec = t1 - t0
        total_cpu_sec = self.nproc * wall_sec
        busy_cpu_sec = total_cpu_sec - (idle_t1 - idle_t0)
        cpu_pct = (busy_cpu_sec / total_cpu_sec) * 100.0
        
        return {
            "wall_sec": round(wall_sec, 4),
            "total_cpu_sec": round(total_cpu_sec, 2),
            "busy_cpu_sec": round(busy_cpu_sec, 2),
            "idle_cpu_sec": round(idle_t1 - idle_t0, 2),
            "cpu_pct": round(cpu_pct, 4)
        }
    
    def measure_steady_state(
        self, 
        rounds: int = 3, 
        rounds_idle_gap_sec: float = 300.0,
        baseline_sec: float = 15.0
    ) -> Dict[str, Any]:
        """
        Measure steady-state CPU across multiple rounds with idle gaps.
        
        This is the production-grade measurement matching Phase03 P0-12 methodology.
        """
        logger.info(f"Starting steady-state measurement: rounds={rounds}, "
                    f"baseline={baseline_sec}s, idle_gap={rounds_idle_gap_sec}s")
        
        # Phase 1: Baseline measurement
        baseline = self.measure_interval(baseline_sec)
        logger.info(f"Baseline: wall={baseline['wall_sec']}s, "
                    f"cpu_pct={baseline['cpu_pct']}%")
        
        # Phase 2: Multiple rounds with idle gaps
        rounds_data = []
        total_wall = 0
        total_busy = 0
        
        for r in range(1, rounds + 1):
            logger.info(f"Round {r}/{rounds} starting...")
            
            # Measure one round
            round_result = self.measure_interval(
                min(30.0, baseline_sec)  # Cap at 30s per round
            )
            
            rounds_data.append({
                "round": r,
                "wall_sec": round_result["wall_sec"],
                "busy_cpu_sec": round_result["busy_cpu_sec"],
                "cpu_pct": round_result["cpu_pct"]
            })
            
            total_wall += round_result["wall_sec"]
            total_busy += round_result["busy_cpu_sec"]
            
            # Idle gap (skip after last round)
            if r < rounds:
                logger.info(f"Idle gap: {rounds_idle_gap_sec}s...")
                time.sleep(rounds_idle_gap_sec)
        
        # Calculate steady-state CPU
        steady_cpu_pct = (total_busy / (total_wall * self.nproc)) * 100.0 if total_wall > 0 else 0.0
        
        return {
            "baseline": baseline,
            "rounds": rounds,
            "idle_gap_sec": rounds_idle_gap_sec,
            "steady_state_cpu_pct": round(steady_cpu_pct, 4),
            "total_wall_sec": round(total_wall, 4),
            "total_busy_cpu_sec": round(total_busy, 2),
            "per_round": rounds_data
        }


# ═══════════════════════════════════════════════════════════════════
# ALARM SYSTEM (Production-Grade)
# ═══════════════════════════════════════════════════════════════════

class AlarmSystem:
    """
    Production alarm system with threshold evaluation and alert deduplication.
    
    Alert levels:
    - WARNING: Log and continue collection
    - CRITICAL: Log and alert (notification channel)
    - FUSE: Halt collection, require manual reset
    """
    
    def __init__(self, alarm_config: Dict[str, Any]):
        self.config = alarm_config
        self._alert_log: List[Dict] = []
        self._last_alert_time: Dict[str, float] = {}
        self._active_alerts: Dict[str, Dict] = {}
        self._dedup_window = alarm_config.get("notification_config", {}).get("dedup_window_sec", 600)
        self._fuse_halted = False
        
        logger.info(f"AlarmSystem initialized with {len(alarm_config.get('cpu_thresholds', {}))} threshold groups")
    
    def check_cpu_threshold(self, steady_cpu_pct: float) -> Tuple[str, str]:
        """
        Check steady-state CPU against thresholds.
        
        Returns (severity, message).
        """
        thresholds = self.config.get("cpu_thresholds", {}).get("steady_state_pct", {})
        
        if steady_cpu_pct >= thresholds.get("fuse", 1.75):
            self._fuse_halted = True
            return "fuse", f"CPU steady-state {steady_cpu_pct:.4f}% >= fuse {thresholds.get('fuse'):.2f}%"
        elif steady_cpu_pct >= thresholds.get("critical", 1.00):
            return "critical", f"CPU steady-state {steady_cpu_pct:.4f}% >= critical {thresholds.get('critical'):.2f}%"
        elif steady_cpu_pct >= thresholds.get("warning", 0.50):
            return "warning", f"CPU steady-state {steady_cpu_pct:.4f}% >= warning {thresholds.get('warning'):.2f}%"
        
        return "ok", f"CPU steady-state {steady_cpu_pct:.4f}% within normal range"
    
    def check_p99_latency(self, p99_ms: float) -> Tuple[str, str]:
        """Check P99 latency against thresholds."""
        thresholds = self.config.get("cpu_thresholds", {}).get("p99_latency_ms", {})
        
        if p99_ms >= thresholds.get("fuse", 500):
            return "fuse", f"P99 latency {p99_ms:.1f}ms >= fuse {thresholds.get('fuse')}ms"
        elif p99_ms >= thresholds.get("critical", 450):
            return "critical", f"P99 latency {p99_ms:.1f}ms >= critical {thresholds.get('critical')}ms"
        elif p99_ms >= thresholds.get("warning", 400):
            return "warning", f"P99 latency {p99_ms:.1f}ms >= warning {thresholds.get('warning')}ms"
        
        return "ok", f"P99 latency {p99_ms:.1f}ms within normal range"
    
    def evaluate(self, measurement: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all thresholds against measurement data.
        Returns list of alert dicts.
        """
        alerts = []
        
        # Check CPU
        steady_cpu = measurement.get("steady_state_cpu_pct", 0)
        cpu_sev, cpu_msg = self.check_cpu_threshold(steady_cpu)
        alerts.append({"metric": "steady_state_cpu", "severity": cpu_sev, "message": cpu_msg})
        
        # Check P99 if available
        p99_ms = measurement.get("p99_latency_ms")
        if p99_ms is not None:
            p99_sev, p99_msg = self.check_p99_latency(p99_ms)
            alerts.append({"metric": "p99_latency", "severity": p99_sev, "message": p99_msg})
        
        # Deduplicate alerts
        now = time.time()
        deduped_alerts = []
        for alert in alerts:
            key = f"{alert['metric']}_{alert['severity']}"
            if key not in self._last_alert_time or (now - self._last_alert_time[key]) > self._dedup_window:
                self._last_alert_time[key] = now
                deduped_alerts.append(alert)
        
        # Update active alerts
        for alert in alerts:
            key = alert['metric']
            if alert['severity'] != 'ok':
                self._active_alerts[key] = {
                    "severity": alert['severity'],
                    "message": alert['message'],
                    "timestamp": now
                }
            else:
                self._active_alerts.pop(key, None)
        
        return deduped_alerts
    
    def is_halted(self) -> bool:
        """Check if collection should be halted (fuse triggered)."""
        return self._fuse_halted
    
    def get_active_alerts(self) -> Dict[str, Dict]:
        """Return current active alerts."""
        return dict(self._active_alerts)
    
    def log_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Log alerts to configured channels."""
        for alert in alerts:
            severity = alert.get("severity", "info")
            message = alert.get("message", "")
            
            if severity == "fuse":
                logger.critical(f"[FUSE] {alert.get('metric')}: {message}")
            elif severity == "critical":
                logger.error(f"[CRITICAL] {alert.get('metric')}: {message}")
            elif severity == "warning":
                logger.warning(f"[WARNING] {alert.get('metric')}: {message}")
            else:
                logger.info(f"[OK] {alert.get('metric')}: {message}")


# ═══════════════════════════════════════════════════════════════════
# ENGINE INTEGRITY CHECK
# ═══════════════════════════════════════════════════════════════════

def verify_engine_integrity(config: Dict[str, Any]) -> Dict[str, Any]:
    """Verify engine MD5 integrity."""
    engine_config = config.get("engine", {})
    expected_md5 = engine_config.get("expected_md5", "")
    engine_path = engine_config.get("path", "")
    
    if not engine_path:
        return {"verified": False, "error": "Engine path not configured"}
    
    engine_full = Path(engine_path)
    if not engine_full.is_absolute():
        engine_full = Path(os.getcwd()) / engine_full
    
    if not engine_full.exists():
        return {"verified": False, "error": f"Engine file not found: {engine_full}"}
    
    actual_md5 = hashlib.md5(engine_full.read_bytes()).hexdigest().lower()
    expected_lower = expected_md5.lower() if expected_md5 else ""
    
    return {
        "verified": actual_md5 == expected_lower,
        "expected_md5": expected_md5,
        "actual_md5": actual_md5,
        "engine_path": str(engine_full),
        "error": None if actual_md5 == expected_lower else f"MD5 mismatch: expected {expected_md5}, got {actual_md5}"
    }


# ═══════════════════════════════════════════════════════════════════
# DATA OUTPUT
# ═══════════════════════════════════════════════════════════════════

def write_measurement_output(
    measurement: Dict[str, Any],
    output_dir: str,
    filename_pattern: str = "psutil_steady_{timestamp}.json"
) -> str:
    """Write measurement data to JSON output file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = filename_pattern.replace("{timestamp}", timestamp)
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(measurement, f, indent=2, default=str)
    
    logger.info(f"Measurement written: {filepath} ({filepath.stat().st_size} bytes)")
    return str(filepath)


# ═══════════════════════════════════════════════════════════════════
# DAEMON PROCESS
# ═══════════════════════════════════════════════════════════════════

class Phase04CollectorDaemon:
    """
    Production daemon process for Phase04 psutil steady-state collection.
    
    Lifecycle:
    1. Load config → validate → verify engine
    2. Initialize CPU meter → pre-warm
    3. Initialize alarm system
    4. Enter collection loop (with daemon mode support)
    5. Handle graceful shutdown
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._running = False
        self._meter: Optional[SystemCpuMeter] = None
        self._alarm: Optional[AlarmSystem] = None
        self._collection_count = 0
        self._last_error: Optional[str] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def initialize(self) -> bool:
        """Initialize collector components."""
        try:
            # Verify engine integrity
            engine_check = verify_engine_integrity(self.config)
            if not engine_check["verified"]:
                logger.error(f"Engine integrity check FAILED: {engine_check.get('error')}")
                return False
            
            logger.info(f"Engine integrity verified: {engine_check['actual_md5']}")
            
            # Initialize CPU meter
            self._meter = SystemCpuMeter(nproc=self.config.get("measurement", {}).get("nproc"))
            self._meter.pre_warm()
            
            # Initialize alarm system
            alarm_config = self.config.get("alarm", {})
            self._alarm = AlarmSystem(alarm_config)
            
            logger.info("Collector initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def collect_once(self) -> Dict[str, Any]:
        """Perform a single collection cycle."""
        self._collection_count += 1
        
        collection_config = self.config.get("collection", {})
        rounds = collection_config.get("rounds_per_cycle", 3)
        idle_gap = collection_config.get("idle_gap_sec", 300)
        baseline_sec = collection_config.get("baseline_duration_sec", 15)
        
        # Perform measurement
        steady_state = self._meter.measure_steady_state(
            rounds=rounds,
            rounds_idle_gap_sec=idle_gap,
            baseline_sec=baseline_sec
        )
        
        # Build measurement record
        measurement = {
            "timestamp": datetime.datetime.now().isoformat(),
            "collector_version": VERSION,
            "task_id": TASK_ID,
            "phase": "Phase04",
            "collection_number": self._collection_count,
            "measurement": {
                "method": "psutil.cpu_times() system-level full-link window",
                "caliber": "system-level",
                "steady_state_cpu_pct": steady_state["steady_state_cpu_pct"],
                "baseline_cpu_pct": steady_state["baseline"]["cpu_pct"],
                "rounds": steady_state["rounds"],
                "idle_gap_sec": steady_state["idle_gap_sec"],
                "total_wall_sec": steady_state["total_wall_sec"],
                "per_round": steady_state["per_round"]
            },
            "engine_info": {
                "expected_md5": self.config.get("engine", {}).get("expected_md5"),
                "total_charts": self.config.get("engine", {}).get("total_charts", 101)
            },
            "constraints": {
                "phase03_gate_path_untouched": True,
                "engine_md5_frozen": True,
                "branch_locked": "feature/v88-g1"
            }
        }
        
        # Evaluate alarms
        alerts = self._alarm.evaluate(measurement["measurement"])
        self._alarm.log_alerts(alerts)
        measurement["alerts"] = alerts
        
        # Check if collection should be halted
        if self._alarm.is_halted():
            logger.critical("FUSE triggered — halting collection")
            self._running = False
        
        # Write output
        output_config = self.config.get("output", {})
        output_dir = output_config.get("directory", "phase04_psutil_data")
        filename_pattern = output_config.get("filename_pattern", "psutil_steady_{timestamp}.json")
        write_measurement_output(measurement, output_dir, filename_pattern)
        
        logger.info(f"Collection #{self._collection_count} complete: "
                    f"steady_cpu={steady_state['steady_state_cpu_pct']:.4f}% "
                    f"baseline={steady_state['baseline']['cpu_pct']:.4f}%")
        
        return measurement
    
    def run(self, daemon_mode: bool = False) -> None:
        """Main collection loop."""
        if not self.initialize():
            logger.error("Initialization failed — exiting")
            return
        
        self._running = True
        interval_sec = self.config.get("collection", {}).get("interval_sec", 60)
        
        if daemon_mode:
            self._write_pid_file()
        
        logger.info(f"Starting collection loop (interval={interval_sec}s, daemon={daemon_mode})")
        
        while self._running:
            try:
                if not self.config.get("collector", {}).get("enabled", False):
                    logger.warning("Collector is DISABLED — waiting for Phase04 work order")
                    time.sleep(300)  # Check every 5 minutes
                    continue
                
                self.collect_once()
                
                # Wait for next interval (check for shutdown)
                wait_interval = interval_sec
                while wait_interval > 0 and self._running:
                    time.sleep(min(1, wait_interval))
                    wait_interval -= 1
                    
            except Exception as e:
                self._last_error = str(e)
                logger.error(f"Collection error: {e}")
                # Backoff before retry
                time.sleep(60)
        
        if daemon_mode:
            self._remove_pid_file()
        
        logger.info("Collection loop terminated")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum} — shutting down gracefully...")
        self._running = False
    
    def _write_pid_file(self) -> None:
        """Write PID file for daemon mode."""
        daemon_config = self.config.get("daemon", {})
        pid_file = daemon_config.get("pid_file", "/tmp/phase04_psutil_collector.pid")
        
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"PID file written: {pid_file}")
    
    def _remove_pid_file(self) -> None:
        """Remove PID file on shutdown."""
        daemon_config = self.config.get("daemon", {})
        pid_file = daemon_config.get("pid_file", "/tmp/phase04_psutil_collector.pid")
        
        try:
            os.unlink(pid_file)
            logger.info(f"PID file removed: {pid_file}")
        except FileNotFoundError:
            pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current daemon status."""
        return {
            "version": VERSION,
            "running": self._running,
            "collection_count": self._collection_count,
            "fuse_halted": self._alarm.is_halted() if self._alarm else False,
            "active_alerts": self._alarm.get_active_alerts() if self._alarm else {},
            "last_error": self._last_error
        }


# ═══════════════════════════════════════════════════════════════════
# DEFAULT CONFIG
# ═══════════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "collector": {
        "version": VERSION,
        "phase": "Phase04",
        "enabled": False,
        "log_level": "info"
    },
    "collection": {
        "interval_sec": 60,
        "rounds_per_cycle": 3,
        "idle_gap_sec": 300,
        "baseline_duration_sec": 15
    },
    "measurement": {
        "method": "psutil.cpu_times",
        "caliber": "system-level",
        "cpu_threshold_pct": 1.75,
        "p99_latency_ms": 500
    },
    "engine": {
        "path": "scripts/node_binding_engine.py",
        "expected_md5": "cd73deaeec54a7f1f8bde92c1300a9dc",
        "total_charts": 101
    },
    "output": {
        "directory": "phase04_psutil_data",
        "filename_pattern": "psutil_steady_{timestamp}.json"
    },
    "alarm": {
        "enabled": True,
        "config_file": "alarm_threshold.json"
    },
    "daemon": {
        "enabled": False,
        "pid_file": "/tmp/phase04_psutil_collector.pid"
    }
}


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description=f"Phase04 psutil Steady-State CPU Collector v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 simple_daemon.py --config config.yaml --test       # Run single test cycle
  python3 simple_daemon.py --config config.yaml              # Run foreground
  python3 simple_daemon.py --config config.yaml --daemon     # Run as daemon
  python3 simple_daemon.py --config config.yaml --status     # Show status
        """
    )
    
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("--test", action="store_true", help="Run single test cycle (no daemon)")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--log-level", default=None, help="Override log level (debug/info/warning/error)")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = args.log_level or "info"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Override log level from config
    if config.get("collector", {}).get("log_level"):
        logging.getLogger().setLevel(
            getattr(logging, config["collector"]["log_level"].upper(), logging.INFO)
        )
    
    # Status mode
    if args.status:
        daemon = Phase04CollectorDaemon(config)
        status = daemon.get_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    # Create daemon
    daemon = Phase04CollectorDaemon(config)
    
    # Test mode: single collection cycle
    if args.test:
        logger.info("=" * 60)
        logger.info("TEST MODE: Single collection cycle")
        logger.info("=" * 60)
        
        if not daemon.initialize():
            sys.exit(1)
        
        # Temporarily enable collector for testing
        config["collector"]["enabled"] = True
        
        try:
            result = daemon.collect_once()
            logger.info(f"TEST COMPLETE: steady_cpu={result['measurement']['steady_state_cpu_pct']:.4f}%")
            logger.info(f"TEST RESULT: {'PASS' if result['alerts'][0]['severity'] == 'ok' else 'ALERT'}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"TEST FAILED: {e}")
            sys.exit(1)
    
    # Run daemon
    daemon.run(daemon_mode=args.daemon)


if __name__ == "__main__":
    main()