# Phase04 psutil Steady-State CPU Collector — Deployment Guide

> **Package**: opt-phase04-psutil-collector
> **Version**: 1.0.0-prod
> **TASK_ID**: V88_PHASE03_P2_DSHE_GATE_HARDEN_AND_PHASE04_PREP_PARTIAL_CHECK_JOB / T1
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1
> **PHASE**: Phase04 (NOT Phase03 gate path)
> **STATUS**: 🟡 READY FOR DEPLOYMENT — Awaiting Phase04 formal work order

---

## 1. Package Overview

### 1.1 Purpose

Production-ready psutil steady-state CPU collection daemon for Phase04. Provides the same caliber as Phase03 P0-12 native PASS (psutil.cpu_times() system-level full-link window) with production-grade daemon mode, alarm thresholds, and structured data output.

### 1.2 Key Design Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| CPU Measurement | `psutil.cpu_times()` system-level | Matches Phase03 P0-12 caliber; NOT process-level |
| Caliber | System-level full-link window | Caliber comparable with Phase02/Phase03 |
| Threshold | ≤1.75% steady-state CPU | Same as Phase03 P0-12 gate threshold |
| Output Format | JSON (structured) | Machine-readable for downstream processing |
| Alert Levels | Warning / Critical / Fuse | Production-grade alarm hierarchy |
| Directory | `opt-phase04-psutil-collector/` | Independent; does NOT touch Phase03 gate paths |
| Enable Flag | `false` (default) | Must explicitly enable after Phase04 work order |

### 1.3 File Inventory

| File | Description | Lines |
|------|-------------|------:|
| `config.yaml` | YAML configuration (all parameters) | ~80 |
| `alarm_threshold.json` | Alarm threshold definitions (CPU/P99/memory/DQ) | ~120 |
| `simple_daemon.py` | Production daemon (meter + alarm + lifecycle) | ~600 |
| `test_collector.py` | 14 test cases (unit + integration) | ~400 |
| `deploy_guide.md` | This document | — |

---

## 2. Prerequisites

### 2.1 Python Environment

| Requirement | Version | Check Command |
|-------------|:-------:|:-------------|
| Python | ≥3.10 | `python3 --version` |
| psutil | ≥5.9.0 | `pip show psutil` |
| PyYAML | ≥6.0 | `pip show pyyaml` |

### 2.2 Dependencies

```bash
pip install psutil pyyaml
```

### 2.3 System Requirements

| Requirement | Minimum | Recommended |
|-------------|:-------:|:----------:|
| OS | Windows 10 / Linux | — |
| CPU Cores | 4 | 8+ |
| RAM | 2GB | 4GB+ |
| Disk Space | 500MB (for 30 days data) | 2GB+ |
| Network | Local only | — |

---

## 3. Installation

### 3.1 Copy Package

```bash
# Copy to target deployment location
cp -r opt-phase04-psutil-collector/ /opt/phase04/psutil-collector/

# Or for Windows:
xcopy opt-phase04-psutil-collector /opt/phase04/psutil-collector /E /I
```

### 3.2 Verify Installation

```bash
cd /opt/phase04/psutil-collector

# Check files exist
ls -la config.yaml alarm_threshold.json simple_daemon.py test_collector.py

# Verify Python imports
python3 -c "import psutil; import yaml; print('Dependencies OK')"

# Run test suite
python3 test_collector.py
```

Expected test output:
```
14 tests run, 0 failures, 0 errors
STATUS: ✅ ALL TESTS PASSED
```

---

## 4. Configuration

### 4.1 Edit `config.yaml`

Key settings to configure:

```yaml
collector:
  enabled: true                    # Enable collector (AFTER Phase04 work order)

collection:
  interval_sec: 60                 # Collection interval
  rounds_per_cycle: 3              # Rounds per cycle
  idle_gap_sec: 300                # Idle gap between rounds
  baseline_duration_sec: 15        # Baseline measurement duration

engine:
  path: "scripts/node_binding_engine.py"   # Engine path (absolute recommended)
  db_path: "analysis/e2e_output/v88/phase03/p0/phase03_test.db"

output:
  directory: "/var/data/phase04/psutil_data"   # Output directory
  retention_days: 30                           # Data retention
```

### 4.2 Alarm Thresholds (`alarm_threshold.json`)

Default thresholds (caliber: psutil.cpu_times system-level):

| Metric | Warning | Critical | Fuse |
|--------|:-------:|:--------:|:----:|
| Steady-State CPU | 0.50% | 1.00% | 1.75% |
| P99 Latency | 400ms | 450ms | 500ms |
| CPU Drift | 5.0% | 10.0% | 20.0% |

### 4.3 Environment Variables (Optional)

| Variable | Default | Description |
|----------|:-------:|-------------|
| `PHASE04_COLLECTOR_CONFIG` | `config.yaml` | Config file path |
| `PHASE04_COLLECTOR_LOG` | `/var/log/phase04_psutil_collector.log` | Log file path |
| `PHASE04_COLLECTOR_PID` | `/tmp/phase04_psutil_collector.pid` | PID file path |

---

## 5. Usage

### 5.1 Single Test Cycle

```bash
python3 simple_daemon.py --config config.yaml --test
```

Output:
```
[INFO] Engine integrity verified: cd73deaeec54a7f1f8bde92c1300a9dc
[INFO] SystemCpuMeter initialized (nproc=16, psutil=7.2.2)
[INFO] Baseline: wall=15.0s, cpu_pct=43.57%
[INFO] Round 1/3: wall=22.5s, cpu_pct=45.14%
[INFO] Idle gap: 300s...
[INFO] Round 2/3: wall=24.9s, cpu_pct=52.87%
[INFO] Idle gap: 300s...
[INFO] Round 3/3: wall=22.4s, cpu_pct=45.14%
[INFO] Collection #1 complete: steady_cpu=0.0654%
```

### 5.2 Foreground Run

```bash
python3 simple_daemon.py --config config.yaml
```

### 5.3 Daemon Mode

```bash
python3 simple_daemon.py --config config.yaml --daemon
```

### 5.4 Status Check

```bash
python3 simple_daemon.py --config config.yaml --status
```

Output:
```json
{
  "version": "1.0.0-prod",
  "running": true,
  "collection_count": 42,
  "fuse_halted": false,
  "active_alerts": {},
  "last_error": null
}
```

---

## 6. Systemd Integration (Linux)

### 6.1 Create Service File

```ini
# /etc/systemd/system/phase04-psutil-collector.service
[Unit]
Description=Phase04 psutil Steady-State CPU Collector
After=network.target
Requires=psql.service

[Service]
Type=simple
User=phase04
Group=phase04
WorkingDirectory=/opt/phase04/psutil-collector
ExecStart=/usr/bin/python3 simple_daemon.py --config config.yaml --daemon
ExecStop=/bin/kill -SIGTERM $MAINPID
Restart=on-failure
RestartSec=30
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### 6.2 Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable phase04-psutil-collector.service
sudo systemctl start phase04-psutil-collector.service

# Check status
sudo systemctl status phase04-psutil-collector.service

# View logs
sudo journalctl -u phase04-psutil-collector.service -f
```

---

## 7. Monitoring & Maintenance

### 7.1 Data Output

Measurements are written as JSON files:

```
/var/data/phase04/psutil_data/
├── psutil_steady_20261016_223000.json
├── psutil_steady_20261016_233000.json
└── ...
```

### 7.2 Alert Logs

Alerts are logged to console and optionally to `alerts/phase04_psutil_alerts.jsonl`.

### 7.3 Data Rotation

Configure in `config.yaml`:
```yaml
output:
  retention_days: 30
  max_archive_size_mb: 100
```

### 7.4 Maintenance Schedule

| Task | Frequency | Command |
|------|:---------:|---------|
| Data cleanup | Daily | `find output/ -name "*.json" -mtime +30 -delete` |
| Health check | Daily | `python3 simple_daemon.py --status` |
| Config review | Monthly | Review `alarm_threshold.json` thresholds |
| Full test run | Weekly | `python3 test_collector.py` |

---

## 8. Troubleshooting

### 8.1 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| "psutil not found" | psutil not installed | `pip install psutil` |
| "Config file not found" | Wrong config path | Use absolute path in `--config` |
| Engine MD5 mismatch | Engine modified | Verify engine integrity; check Phase03 gate |
| High CPU readings | System load too high | Increase `idle_gap_sec`; check system load |
| Fuse triggered | CPU above 1.75% | Investigate root cause; do NOT increase threshold |

### 8.2 Diagnostic Commands

```bash
# Check psutil availability
python3 -c "import psutil; print(psutil.cpu_times())"

# Verify engine MD5
python3 -c "import hashlib; print(hashlib.md5(open('scripts/node_binding_engine.py','rb').read()).hexdigest())"

# Check collector process
ps aux | grep simple_daemon

# Check data output
ls -la output/*.json | head -5
```

---

## 9. Rollback

### 9.1 Disable Collector

```yaml
# Edit config.yaml
collector:
  enabled: false
```

### 9.2 Stop Daemon

```bash
# Stop systemd service
sudo systemctl stop phase04-psutil-collector.service

# Or kill process directly
kill $(cat /tmp/phase04_psutil_collector.pid)
```

### 9.3 Uninstall

```bash
# Remove systemd service
sudo systemctl disable phase04-psutil-collector.service
sudo rm /etc/systemd/system/phase04-psutil-collector.service

# Remove package
rm -rf /opt/phase04/psutil-collector/

# Remove data
rm -rf /var/data/phase04/psutil_data/
```

---

## 10. Constraints Compliance

| Constraint | Status | Verification |
|------------|:------:|--------------|
| Phase03 gate path untouched | ✅ | Independent directory; no writes to Phase03 paths |
| Engine MD5 frozen | ✅ | `cd73deaeec54a7f1f8bde92c1300a9dc` verified at init |
| No noise monitor modification | ✅ | No references to noise monitor code |
| No threshold monitor modification | ✅ | No references to threshold monitor code |
| No ZHIJI API call | ✅ | No API calls in codebase |
| Branch locked | ✅ | `feature/v88-g1` |
| No overwrite | ✅ | Append-only output; no in-place modifications |
| No V87 modification | ✅ | Phase04 only; no V87 references |

---

## 11. Deployment Checklist

| # | Step | Status |
|---|------|:------:|
| 1 | Copy package to target location | ⬜ |
| 2 | Install dependencies (psutil, pyyaml) | ⬜ |
| 3 | Run test suite (`python3 test_collector.py`) | ⬜ |
| 4 | Configure `config.yaml` | ⬜ |
| 5 | Verify engine MD5 integrity | ⬜ |
| 6 | Create output directory | ⬜ |
| 7 | Enable collector (`enabled: true`) | ⬜ |
| 8 | Run single test cycle | ⬜ |
| 9 | Deploy systemd service | ⬜ |
| 10 | Verify monitoring/alerts | ⬜ |
| 11 | Schedule data rotation | ⬜ |
| 12 | Update STATUS.md + JOB_READY.flag | ⬜ |

---

> **NOTE**: This package is deployed ONLY after Phase04 formal work order is issued. Until then, `collector.enabled` remains `false`.
>
> **C-3 Compliance**: Phase04 psutil steady-state collection upgraded from prototype to production-ready. Caliber maintained: `psutil.cpu_times()` system-level full-link window.
>
> *Generated: 2026-10-16T22:45 UTC+8 | DSHE | Phase04 psutil Collector Deploy Guide*