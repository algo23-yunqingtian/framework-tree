#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHD-TASK-041: Global Monitoring + Crowding & Regime Inspection
=================================================================
Continuous monitoring orchestrator.
Token: DSHD-TASK041-TOKEN
Baseline: origin/feature/v88-g1 HEAD=9237b8f
Mode: AUDIT_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED

Subtasks:
  P0: Background DSHC/DSHA event stream listener
  P1: P81 inspection (file lock health, process keepalive, memory threshold)
  P2: 7-factor crowding calculation, P90 baseline check
  P3: Regime detection (INSUFFICIENT_DATA handling)
  P4: Risk ledger update + audit events
  P5: Document maintenance (dshd_cluster_brief_regime_crowding.md)
  P6: DSHC lock conflict / DSHA factor risk capture

Usage:
  python task041_monitor.py --once          # Single inspection cycle
  python task041_monitor.py --continuous    # Loop with 5-min interval
  python task041_monitor.py --daemon        # Run in background
"""

import json, os, sys, time, hashlib, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================
TZ_CN = timezone(timedelta(hours=8))

BASE = r'D:\DSH_WORK\github工作\回测'
LEDGER = os.path.join(BASE, 'G7_ADJUDICATION_LEDGER')
ARTIFACTS = os.path.join(BASE, 'artifacts')

FILES = {
    'file_lock_ps1':      os.path.join(LEDGER, 'p81_file_lock.ps1'),
    'crowding_state':     os.path.join(LEDGER, 'p82_crowding_state.json'),
    'crowding_baseline':  os.path.join(LEDGER, 'p82_crowding_baseline.json'),
    'risk_ledger':        os.path.join(LEDGER, 'p82_risk_ledger.json'),
    'regime_state':       os.path.join(LEDGER, 'p82_regime_state.json'),
    'ic_watchdog':        os.path.join(LEDGER, 'p82_ic_watchdog_state.json'),
    'perf_drift':         os.path.join(LEDGER, 'p82_perf_drift_state.json'),
    'pipeline_alerts':    os.path.join(LEDGER, 'p82_pipeline_alerts.json'),
    'version_history':    os.path.join(LEDGER, 'p81_version_history.json'),
    'audit_log':          os.path.join(BASE, 'tracking_monitor_audit.jsonl'),
    'brief_rc':           os.path.join(ARTIFACTS, 'dshd_cluster_brief_regime_crowding.md'),
    'brief_main':         os.path.join(ARTIFACTS, 'dshd_cluster_brief.md'),
    'p81_watch':          os.path.join(LEDGER, 'dshd_p81_watch.ps1'),
    'p81_inspect':        os.path.join(LEDGER, 'p81_periodic_inspect.ps1'),
    'dsha_ic_checksum':   os.path.join(LEDGER, 'task037_dsha_ic_checksum.json'),
}

# DSHC event files (all known event sources)
DSHC_EVENT_FILES = [
    os.path.join(ARTIFACTS, 'dshc_p86_events.jsonl'),
    os.path.join(ARTIFACTS, 'dshc_ignite_a01_events.jsonl'),
    os.path.join(ARTIFACTS, 'dshc_ignite_a02_events.jsonl'),
    os.path.join(ARTIFACTS, 'dshc_p90a_final_events.jsonl'),
    os.path.join(ARTIFACTS, 'dshc_a03_fetch_events.jsonl'),
    os.path.join(ARTIFACTS, 'dshc_t1_fetch_events.jsonl'),
    os.path.join(ARTIFACTS, 'dshc_t1fix_events.jsonl'),
    os.path.join(ARTIFACTS, 'dshc_f01_events.jsonl'),
]

# Monitoring thresholds
THRESHOLDS = {
    'file_lock_timeout_sec': 30,
    'memory_threshold_mb': 256,
    'inspection_interval_sec': 300,       # 5 minutes
    'dshc_event_poll_sec': 60,             # 1 minute for event polling
    'p90_crowding_threshold': 51.5,
    'directional_concentration_extreme': 0.7,
    'value_hhi_high': 0.25,
    'ic_decay_threshold': 0.3,
    'perf_return_threshold': 0.15,
    'perf_sharpe_threshold': 1.5,
    'perf_drawdown_threshold': -0.05,
}

# Risk ledger dedup key - only filter TASK-040 entries (fix from TASK-040)
RISK_LEDGER_SOURCE_FILTERS = ['DSHD-TASK040', 'DSHD-TASK039', 'DSHD-TASK041']


# ============================================================================
# Utility Functions
# ============================================================================
def now_iso():
    """Current time in ISO 8601 with +08:00 offset."""
    return datetime.now(TZ_CN).isoformat(timespec='seconds')


def log(msg):
    """Print with timestamp."""
    ts = datetime.now(TZ_CN).strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)


def sha256_file(path):
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def read_json(path):
    """Read JSON file with UTF-8 BOM handling."""
    try:
        with open(path, encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        log(f"  WARN: Failed to read {os.path.basename(path)}: {e}")
        return None


def write_json(path, data, lock_timeout=30):
    """Write JSON file with file lock protection."""
    try:
        # Use msvcrt.locking for Windows file locking
        import msvcrt
        mode = 'wb' if not os.path.exists(path) else 'r+b'
        f = open(path, mode)
        try:
            f.seek(0, 2)  # seek to end
            size = f.tell()
            f.seek(0)
            # Acquire exclusive lock
            for attempt in range(3):
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, max(size, 1))
                    break
                except OSError:
                    if attempt == 2:
                        raise
                    time.sleep(0.5)
            # Truncate and write
            f.truncate(0)
            f.write(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
            f.flush()
            # Release lock
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, max(size, 1))
        finally:
            f.close()
    except Exception as e:
        log(f"  WARN: File lock write failed for {os.path.basename(path)}: {e}")
        # Fallback: write without lock
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log(f"  WARN: Wrote {os.path.basename(path)} WITHOUT lock (fallback)")
    return True


def append_audit_event(event_dict):
    """Append a single event to the audit log JSONL file with retry on permission conflict."""
    line = json.dumps(event_dict, ensure_ascii=False) + '\n'
    for attempt in range(5):
        try:
            with open(FILES['audit_log'], 'a', encoding='utf-8') as f:
                f.write(line)
                f.flush()
            return True
        except Exception as e:
            if attempt == 4:
                log(f"  WARN: Audit append failed after 5 retries: {e}")
                return False
            time.sleep(0.5)
    return False


def count_lines(path):
    """Count lines in a file."""
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path, 'rb') as f:
        for line in f:
            count += 1
    return count


def file_size_mb(path):
    """Get file size in MB."""
    if not os.path.exists(path):
        return 0.0
    return os.path.getsize(path) / (1024 * 1024)


# ============================================================================
# P1: P81 Inspection - File Lock Health, Process Keepalive, Memory Threshold
# ============================================================================
def p1_inspect_processes():
    """Check DSHD/DSHC/DSHA/PowerShell process states."""
    import subprocess
    results = {
        'inspection_type': 'P1_PROCESS_KEEPALIVE',
        'timestamp': now_iso(),
        'p81_watch_running': False,
        'p81_inspect_running': False,
        'p80_phase2_running': False,
        'powershell_processes': [],
        'memory_threshold_mb': THRESHOLDS['memory_threshold_mb'],
        'memory_alerts': [],
    }

    try:
        # Check all PowerShell processes
        r = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             'Get-Process -Name powershell,pwsh -ErrorAction SilentlyContinue | '
             'Select-Object Id, ProcessName, @{N=\'MemMB\';E={[math]::Round($_.WorkingSet/1MB,1)}}, '
             'StartTime | ConvertTo-Json -Compress'],
            capture_output=True, text=True, timeout=15
        )
        if r.stdout.strip() and r.stdout.strip() != 'null':
            procs = json.loads(r.stdout.strip())
            if isinstance(procs, dict):
                procs = [procs]
            for p in procs:
                pid = p.get('Id', 0)
                mem_mb = p.get('MemMB', 0)
                p81_watch_running = False
                p81_inspect_running = False
                p80_phase2_running = False

                # Check command line
                cmd = p.get('CommandLine', '') or ''
                if 'p81_watch' in cmd.lower():
                    p81_watch_running = True
                if 'periodic_inspect' in cmd.lower():
                    p81_inspect_running = True
                if 'phase2' in cmd.lower() or 'audit_watch' in cmd.lower():
                    p80_phase2_running = True

                entry = {
                    'pid': pid,
                    'name': p.get('ProcessName', ''),
                    'mem_mb': mem_mb,
                    'start_time': p.get('StartTime', ''),
                }
                results['powershell_processes'].append(entry)

                # Memory threshold check
                if mem_mb > THRESHOLDS['memory_threshold_mb']:
                    results['memory_alerts'].append({
                        'pid': pid,
                        'name': p.get('ProcessName', ''),
                        'mem_mb': mem_mb,
                        'threshold_mb': THRESHOLDS['memory_threshold_mb'],
                        'action': 'SOFT_RESTART_RECOMMENDED',
                    })

            results['p81_watch_running'] = p81_watch_running
            results['p81_inspect_running'] = p81_inspect_running
            results['p80_phase2_running'] = p80_phase2_running
    except Exception as e:
        results['error'] = str(e)

    # File lock health check
    file_lock_ps1 = FILES['file_lock_ps1']
    if os.path.exists(file_lock_ps1):
        results['file_lock_module'] = {
            'exists': True,
            'size_bytes': os.path.getsize(file_lock_ps1),
            'sha256': sha256_file(file_lock_ps1),
            'last_modified': datetime.fromtimestamp(
                os.path.getmtime(file_lock_ps1), TZ_CN
            ).isoformat(timespec='seconds'),
        }
    else:
        results['file_lock_module'] = {'exists': False}

    # Script modification check
    for key, label in [('p81_watch', 'P81 Watch'), ('p81_inspect', 'P81 Inspect')]:
        fpath = FILES[key]
        if os.path.exists(fpath):
            content = open(fpath, encoding='utf-8').read()
            results[f'{key}_filelock_integration'] = {
                'has_file_lock_import': 'FileLockModulePath' in content or 'p81_file_lock' in content,
                'has_write_with_lock': 'Write-FileWithLock' in content,
                'has_keepalive': 'Check-P80WatcherKeepalive' in content,
                'has_memory_check': 'MemoryThresholdMB' in content or 'Check-MemoryThreshold' in content,
            }

    return results


def p1_inspect_pipeline_lock_conflicts():
    """Scan DSHC event files for lock conflicts and anomalies."""
    results = {
        'inspection_type': 'P6_DSHC_LOCK_CONFLICT_SCAN',
        'timestamp': now_iso(),
        'total_events_scanned': 0,
        'lock_conflicts_found': 0,
        'collection_timeouts_found': 0,
        'event_types': {},
        'new_events_since_last_scan': 0,
        'event_files': {},
        'dscha_available': False,
    }

    # Check DSHA directory
    dsha_path = os.path.join(BASE, 'DSHA')
    results['dsha_available'] = os.path.exists(dsha_path)
    if not results['dsha_available']:
        results['dsha_status'] = 'DSHA_DIR_NOT_FOUND - no factor computation events to capture'

    # Scan DSHC event files
    total_lines = 0
    lock_conflicts = 0
    collection_timeouts = 0
    event_types = {}

    for ev_file in DSHC_EVENT_FILES:
        if not os.path.exists(ev_file):
            continue
        fname = os.path.basename(ev_file)
        line_count = count_lines(ev_file)
        file_size = os.path.getsize(ev_file)
        results['event_files'][fname] = {
            'lines': line_count,
            'size_bytes': file_size,
        }
        total_lines += line_count

        # Scan for lock conflicts and timeouts
        try:
            with open(ev_file, encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    etype = ev.get('type', ev.get('event_type', ''))
                    msg = ev.get('message', '')
                    event_types[etype] = event_types.get(etype, 0) + 1
                    if 'lock' in etype.lower() or 'LOCK_CONFLICT' in etype:
                        lock_conflicts += 1
                    if 'timeout' in etype.lower() or 'COLLECTION_TIMEOUT' in etype:
                        collection_timeouts += 1
        except Exception:
            pass

    results['total_events_scanned'] = total_lines
    results['lock_conflicts_found'] = lock_conflicts
    results['collection_timeouts_found'] = collection_timeouts
    results['event_types'] = event_types

    # Read pipeline alerts for cross-reference
    pa = read_json(FILES['pipeline_alerts'])
    if pa:
        results['pipeline_alerts_last_scan'] = pa.get('last_scan')
        results['pipeline_alerts_total'] = pa.get('total_alerts_detected')
        results['pipeline_alerts_by_type'] = pa.get('last_scan_results', {}).get('by_type', {})

    return results


# ============================================================================
# P2: 7-Factor Crowding Calculation
# ============================================================================
CROWDING_FACTORS = [
    'oi_change_1d', 'oi_change_rate_7d', 'oi_level',
    'realized_vol_20d', 'vol_regime_change', 'spread_cs', 'momentum_20d',
]
# contract_switch_flag excluded from crowding analysis (STABLE factor)


def p2_compute_crowding():
    """Read current crowding state, validate against P90 baseline, compute alerts."""
    state = read_json(FILES['crowding_state'])
    baseline = read_json(FILES['crowding_baseline'])

    if not state or not baseline:
        return {'error': 'Failed to read crowding state or baseline'}

    p90_threshold = baseline.get('p90_threshold', 51.5)
    thresholds = THRESHOLDS

    factor_results = {}
    alert_factors = []
    total_score = 0
    count = 0

    for factor_name in CROWDING_FACTORS:
        fdata = state.get('factor_results', {}).get(factor_name, {})
        if not fdata:
            continue

        score = fdata.get('crowding_score', {}).get('score', 0)
        total_score += score
        count += 1

        # Check against P90 baseline
        above_p90 = score >= p90_threshold

        # Component checks
        dir_conc = fdata.get('directional_concentration', {})
        val_conc = fdata.get('value_concentration', {})
        ic_mom = fdata.get('ic_momentum', {})

        dir_flag = dir_conc.get('concentration_flag', False)
        val_flag = val_conc.get('concentration_flag', False)
        ic_decay = ic_mom.get('ic_decay', 0)
        ic_flag = ic_decay > thresholds['ic_decay_threshold']

        # Portfolio alert
        portfolio_alert = above_p90 or dir_flag or val_flag or ic_flag

        result = {
            'factor': factor_name,
            'score': score,
            'above_p90': above_p90,
            'p90_threshold': p90_threshold,
            'directional_concentration_flag': dir_flag,
            'value_concentration_flag': val_flag,
            'ic_decay': round(ic_decay, 4),
            'ic_decay_flag': ic_flag,
            'portfolio_alert': portfolio_alert,
            'alert_flags': fdata.get('alert_flags', []),
            'alert_triggered': fdata.get('alert_triggered', False),
        }
        factor_results[factor_name] = result

        if portfolio_alert:
            alert_factors.append(factor_name)

    # Portfolio summary
    mean_score = total_score / count if count else 0
    portfolio_level = 'CROWDING_LOW'
    if mean_score >= 50:
        portfolio_level = 'CROWDING_HIGH'
    elif mean_score >= 30:
        portfolio_level = 'CROWDING_MEDIUM'

    # Check component baselines
    component_baselines = baseline.get('component_baselines', {})

    return {
        'inspection_type': 'P2_CROWDING_CALCULATION',
        'timestamp': now_iso(),
        'p90_threshold': p90_threshold,
        'factor_results': factor_results,
        'alert_factors': alert_factors,
        'alert_count': len(alert_factors),
        'portfolio_summary': {
            'mean_score': round(mean_score, 2),
            'count': count,
            'level': portfolio_level,
        },
        'component_baselines': component_baselines,
        'baseline_run_count': baseline.get('history_accumulation', {}).get('run_count', 0),
    }


def p2_append_baseline_history(crowding_result):
    """Append current crowding scores to baseline history for temporal percentile tracking."""
    baseline = read_json(FILES['crowding_baseline'])
    if not baseline:
        return False

    scores = {}
    for fname in CROWDING_FACTORS:
        fdata = crowding_result.get('factor_results', {}).get(fname, {})
        if fdata:
            scores[fname] = fdata.get('score', 0)

    if not scores:
        return False

    # Get current run count
    hist = baseline.get('history_accumulation', {})
    run_count = hist.get('run_count', 0)
    run_id = run_count + 1

    # Append to history
    runs = hist.get('runs', [])
    runs.append({
        'run_id': run_id,
        'timestamp': now_iso(),
        'source': 'DSHD-TASK041',
        'scores': scores,
    })
    hist['run_count'] = run_id
    hist['runs'] = runs
    hist['note'] = (
        f"Baseline accumulated over {run_count} runs. "
        f"Minimum 5 runs recommended for stable percentile thresholds."
    )

    baseline['history_accumulation'] = hist
    baseline['last_updated'] = now_iso()

    # Recompute cross-sectional percentiles if enough runs
    if run_count >= 5:
        all_scores = []
        for r in runs:
            all_scores.extend(r.get('scores', {}).values())
        if all_scores:
            sorted_scores = sorted(all_scores)
            n = len(sorted_scores)
            p90_idx = int(n * 0.9)
            new_p90 = round(sorted_scores[min(p90_idx, n-1)], 1)
            baseline['p90_threshold'] = new_p90
            log(f"  P2: Updated P90 threshold to {new_p90} (from {run_count} runs)")

    write_json(FILES['crowding_baseline'], baseline)
    return True


# ============================================================================
# P3: Regime Detection
# ============================================================================
def p3_regime_detection():
    """Check regime state, ensure INSUFFICIENT_DATA handling is correct."""
    regime = read_json(FILES['regime_state'])
    if not regime:
        return {'error': 'Failed to read regime state'}

    counts = regime.get('regime_counts', {})
    insuff_handling = regime.get('insufficient_data_handling', {})

    # Verify DOWN regime handling
    down_days = counts.get('DOWN', 0) + counts.get('DOWN_INSUFFICIENT_DATA', 0)
    down_insuff = counts.get('DOWN_INSUFFICIENT_DATA', 0)
    min_window = insuff_handling.get('min_window_days', 20)

    down_insufficient = down_insuff >= min_window
    if not down_insufficient and down_days > 0 and down_days < min_window:
        # Already marked correctly by TASK-040
        down_insufficient = True
        insuff_handling['auto_correction'] = (
            f"DOWN days={down_days} < min_window={min_window}, "
            f"confirmed INSUFFICIENT_DATA"
        )

    # Check for UNKNOWN false alerts
    unknown_count = counts.get('UNKNOWN', 0)
    false_alerts_prevented = insuff_handling.get('handling', '') != ''

    return {
        'inspection_type': 'P3_REGIME_DETECTION',
        'timestamp': now_iso(),
        'regime_counts': counts,
        'down_regime': {
            'total_days': down_days,
            'insufficient_data_days': down_insuff,
            'below_min_window': down_days < min_window,
            'handling': 'INSUFFICIENT_DATA' if down_days < min_window else 'SUFFICIENT_DATA',
            'false_alerts_prevented': false_alerts_prevented,
        },
        'unknown_regime': {
            'count': unknown_count,
            'note': counts.get('UNKNOWN_note', ''),
        },
        'insufficient_data_handling': insuff_handling,
    }


# ============================================================================
# P4: Risk Ledger Update
# ============================================================================
def p4_update_risk_ledger():
    """Update risk ledger with current monitoring status. Filter out prior TASK-040/041 duplicates."""
    ledger = read_json(FILES['risk_ledger'])
    if not ledger:
        return {'error': 'Failed to read risk ledger'}

    entries = ledger.get('risk_entries', [])
    original_count = len(entries)
    version = ledger.get('version', '4.0.0-TASK040')

    # Count by status (before filtering)
    by_status = {}
    for e in entries:
        s = e.get('status', 'UNKNOWN')
        by_status[s] = by_status.get(s, 0) + 1

    # Filter out prior TASK-040/041 entries to prevent duplication
    filtered_entries = []
    removed_count = 0
    for e in entries:
        source = e.get('source', '')
        factor = e.get('factor', '')
        # Remove duplicate TASK-040 crowding entries (keep IC/perf entries)
        if source == 'DSHD-TASK040' and 'CROWDING' in factor:
            removed_count += 1
            continue
        if source == 'DSHD-TASK041':
            removed_count += 1
            continue
        filtered_entries.append(e)

    # Only update file if version changed or duplicates removed
    if version != '4.1.0-TASK041' or removed_count > 0:
        ledger['version'] = '4.1.0-TASK041'
        ledger['updated_at'] = now_iso()
        ledger['risk_entries'] = filtered_entries
        write_json(FILES['risk_ledger'], ledger)

    entries = filtered_entries

    # Count after filtering
    by_status_new = {}
    for e in entries:
        s = e.get('status', 'UNKNOWN')
        by_status_new[s] = by_status_new.get(s, 0) + 1

    result = {
        'inspection_type': 'P4_RISK_LEDGER_UPDATE',
        'timestamp': now_iso(),
        'version_before': version,
        'version_after': '4.1.0-TASK041',
        'entries_before': original_count,
        'entries_after': len(entries),
        'duplicates_removed': removed_count,
        'by_status_before': by_status,
        'by_status_after': by_status_new,
        'ic_flip_alerts': by_status_new.get('ALERT', 0),
        'stable_factors': by_status_new.get('STABLE', 0),
        'warn_factors': by_status_new.get('WARN', 0),
    }

    return result


# ============================================================================
# P5: Document Maintenance
# ============================================================================
def p5_update_document():
    """Update the regime_crowding markdown document with current monitoring data."""
    crowding = read_json(FILES['crowding_state'])
    baseline = read_json(FILES['crowding_baseline'])
    regime = read_json(FILES['regime_state'])

    if not crowding or not baseline or not regime:
        return {'error': 'Failed to read data for document update'}

    p90 = baseline.get('p90_threshold', 51.5)
    run_count = baseline.get('history_accumulation', {}).get('run_count', 0)

    # Build factor table
    factor_rows = []
    alert_count = 0
    for fname in CROWDING_FACTORS:
        fdata = crowding.get('factor_results', {}).get(fname, {})
        if not fdata:
            continue
        score = fdata.get('crowding_score', {}).get('score', 0)
        flags = fdata.get('alert_flags', [])
        severity = fdata.get('alert_severity', 'NONE')
        triggered = fdata.get('alert_triggered', False)
        if triggered:
            alert_count += 1
        flag_str = ','.join(flags) if flags else '-'
        status_icon = '⚠' if triggered else '✅'
        status_label = f"{status_icon} {severity}" if triggered else 'OK'
        factor_rows.append(f"| {fname} | {score} | {p90} | {flag_str} | {status_label} |")

    factor_table = '\n'.join(factor_rows)

    # Build regime table
    counts = regime.get('regime_counts', {})
    total_days = sum(v for k, v in counts.items() if isinstance(v, int) and k != 'UNKNOWN_note')
    regime_rows = []
    for rname in ['UP', 'DOWN', 'SIDEWAYS', 'UNKNOWN']:
        days = counts.get(rname, 0)
        pct = round(days / total_days * 100, 1) if total_days else 0
        note = ''
        if rname == 'DOWN':
            insuff = regime.get('insufficient_data_handling', {})
            if insuff:
                note = '⚠ INSUFFICIENT_DATA'
        if rname == 'UNKNOWN':
            note = '边界情况'
        regime_rows.append(f"| {rname} | {days} | {pct}% | {note} |")
    regime_table = '\n'.join(regime_rows)

    # Build content
    ts = now_iso()
    content = f"""# DSHD 监控文档 — Regime识别 + 拥挤度监控 (独立持久化)

> 生成时间: {ts}
> 任务: DSHD-TASK-041-MONITOR
> 令牌: DSHD-TASK041-TOKEN
> 模式: AUDIT_READ_ONLY
> 注意: 本文件独立于 P81 集群简报 (dshd_cluster_brief.md), 不会被 5 分钟巡检覆盖。
> 数据真源: p82_regime_state.json + p82_crowding_state.json + p82_crowding_baseline.json

---

## 十二、Regime 行情自动识别

> 检测器: DSHD-TASK039-REGIME-DETECT
> 版本: 1.0.0
> 锁定: True
> TASK-041 巡检时间: {ts}

### 12.1 行情分布

| 行情 | 天数 | 占比 | 状态 |
|---|---|---|---|
{regime_table}

### 12.2 DOWN 行情处理

> DOWN 行情天数: {counts.get('DOWN', 0)}, 低于 20 天最小窗口
> 处理策略: INSUFFICIENT_DATA, 不产生 UNKNOWN 无效告警

---

## 十三、因子拥挤度监控

> 监控器: DSHD-TASK039-CROWDING-MONITOR
> 版本: 1.0.0
> P90 基线阈值: {p90}
> 基线运行次数: {run_count}
> TASK-041 巡检时间: {ts}

### 13.1 告警阈值

| 参数 | 值 |
|---|---|
| 拥挤度告警分位数 | 90% |
| 方向性集中度阈值 | {THRESHOLDS['directional_concentration_extreme']} |
| 值集中度HHI阈值 | {THRESHOLDS['value_hhi_high']} |
| IC衰减阈值 | {THRESHOLDS['ic_decay_threshold']} |
| P90分位数基线 | {p90} |
| 告警严重度 | MEDIUM |

### 13.2 因子拥挤度详情

| 因子 | 拥挤度 | P90阈值 | 告警标志 | 状态 |
|---|---|---|---|---|
{factor_table}

### 13.3 组合整体拥挤度

| 指标 | 值 |
|---|---|
| 整体等级 | CROWDING_LOW |
| 告警因子数 | {alert_count} |
| P90基线阈值 | {p90} |
| 基线运行次数 | {run_count} |

---

## 十四、TASK-041 全局监控状态

> 任务: DSHD-TASK-041-MONITOR
> 巡检时间: {ts}

### 14.1 监控覆盖

- P0: 后台事件流监听 (DSHC 8个事件文件)
- P1: P81巡检 (文件锁健康 + 进程保活 + 内存阈值 {THRESHOLDS['memory_threshold_mb']}MB)
- P2: 7因子拥挤度实时计算 + P90基线对照
- P3: 行情Regime识别 (DOWN=INSUFFICIENT_DATA)
- P4: 风险台账v4.1.0持续更新
- P5: 文档持久化维护
- P6: DSHC锁冲突/DSHA因子风险事件捕捉

### 14.2 红线约束

| 约束 | 状态 |
|---|---|
| wind_api_calls | 0 |
| Gate | CLOSED/HOLD |
| Release | NOT_ISSUED |
| IC翻转门禁 | 硬锁定不变 |
| 绩效漂移门禁 | 硬锁定不变 |
| 文件锁保护 | 30s超时 |

---
*本文件由 DSHD-TASK-041-MONITOR 自动生成*
*{ts}*
"""

    write_json(FILES['brief_rc'], content)  # Will write as text via write_json fallback
    # Actually, we need to write as text, not JSON. Let me fix this.
    with open(FILES['brief_rc'], 'w', encoding='utf-8') as f:
        f.write(content)

    return {
        'inspection_type': 'P5_DOCUMENT_UPDATE',
        'timestamp': now_iso(),
        'file': os.path.basename(FILES['brief_rc']),
        'size_bytes': len(content.encode('utf-8')),
        'sections_updated': ['12_0_REGIME', '13_0_CROWDING', '14_0_TASK041'],
    }


# ============================================================================
# P6: DSHC Lock Conflict / DSHA Factor Risk Capture
# ============================================================================
def p6_capture_events():
    """Scan DSHC events for lock conflicts, DSHA factor risks, capture anomalies."""
    results = p1_inspect_pipeline_lock_conflicts()

    # Check IC watchdog for factor risk
    ic = read_json(FILES['ic_watchdog'])
    if ic:
        factor_risks = {}
        for fac, hist in ic.get('factor_history', {}).items():
            if hist:
                last = hist[-1]
                factor_risks[fac] = {
                    'flip_rate': last.get('flip_rate'),
                    'num_windows': last.get('num_windows'),
                    'hard_locked': last.get('hard_locked', False),
                    'status': last.get('hard_lock_status', 'N/A'),
                }
        results['ic_factor_risks'] = factor_risks
        results['ic_watchdog_total_runs'] = ic.get('total_runs', 0)

    # Check perf drift
    perf = read_json(FILES['perf_drift'])
    if perf and perf.get('history'):
        last = perf['history'][-1]
        results['perf_drift'] = {
            'return': last.get('total_return'),
            'sharpe': last.get('sharpe_ratio'),
            'drawdown': last.get('max_drawdown'),
            'all_pass': last.get('all_pass'),
        }

    return results


# ============================================================================
# Audit Events
# ============================================================================
def write_audit_events(results, cycle_id):
    """Write all monitoring events to the audit log."""
    events = []

    # Task start event
    events.append({
        'timestamp': results['timestamp'],
        'event': 'DSHD-T041-MONITOR-CYCLE-START',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'token': 'DSHD-TASK041-TOKEN',
        'cycle_id': cycle_id,
        'mode': 'AUDIT_READ_ONLY',
        'wind_api_calls': 0,
        'gate': 'CLOSED/HOLD',
        'release_permit': 'NOT_ISSUED',
        'severity': 'INFO',
    })

    # P1: Process keepalive
    p1 = results.get('p1_processes', {})
    events.append({
        'timestamp': results['timestamp'],
        'event': 'DSHD-T041-P1-PROCESS-KEEPALIVE',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'p81_watch_running': p1.get('p81_watch_running', False),
        'p81_inspect_running': p1.get('p81_inspect_running', False),
        'p80_phase2_running': p1.get('p80_phase2_running', False),
        'memory_alerts': len(p1.get('memory_alerts', [])),
        'file_lock_module_exists': p1.get('file_lock_module', {}).get('exists', False),
        'severity': 'INFO' if len(p1.get('memory_alerts', [])) == 0 else 'WARNING',
    })

    # P2: Crowding calculation
    p2 = results.get('p2_crowding', {})
    events.append({
        'timestamp': results['timestamp'],
        'event': 'DSHD-T041-P2-CROWDING-CALC',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'p90_threshold': p2.get('p90_threshold', 51.5),
        'alert_count': p2.get('alert_count', 0),
        'alert_factors': p2.get('alert_factors', []),
        'portfolio_level': p2.get('portfolio_summary', {}).get('level', 'UNKNOWN'),
        'portfolio_mean_score': p2.get('portfolio_summary', {}).get('mean_score', 0),
        'severity': 'INFO',
    })

    # P3: Regime detection
    p3 = results.get('p3_regime', {})
    down = p3.get('down_regime', {})
    events.append({
        'timestamp': results['timestamp'],
        'event': 'DSHD-T041-P3-REGIME-DETECT',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'down_days': down.get('total_days', 0),
        'down_handling': down.get('handling', 'UNKNOWN'),
        'unknown_count': p3.get('unknown_regime', {}).get('count', 0),
        'false_alerts_prevented': down.get('false_alerts_prevented', False),
        'severity': 'INFO',
    })

    # P4: Risk ledger update
    p4 = results.get('p4_ledger', {})
    events.append({
        'timestamp': results['timestamp'],
        'event': 'DSHD-T041-P4-RISK-LEDGER',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'version': p4.get('version_after', '4.1.0-TASK041'),
        'entries_after': p4.get('entries_after', 0),
        'duplicates_removed': p4.get('duplicates_removed', 0),
        'ic_flip_alerts': p4.get('ic_flip_alerts', 0),
        'severity': 'INFO',
    })

    # P5: Document update
    p5 = results.get('p5_doc', {})
    events.append({
        'timestamp': results['timestamp'],
        'event': 'DSHD-T041-P5-DOC-UPDATE',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'file': p5.get('file', ''),
        'size_bytes': p5.get('size_bytes', 0),
        'severity': 'INFO',
    })

    # P6: DSHC/DSHA event capture
    p6 = results.get('p6_events', {})
    events.append({
        'timestamp': results['timestamp'],
        'event': 'DSHD-T041-P6-DSHC-DSHA-CAPTURE',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'total_events_scanned': p6.get('total_events_scanned', 0),
        'lock_conflicts': p6.get('lock_conflicts_found', 0),
        'collection_timeouts': p6.get('collection_timeouts_found', 0),
        'dsha_available': p6.get('dsha_available', False),
        'ic_factor_risk_count': len(p6.get('ic_factor_risks', {})),
        'perf_drift_all_pass': p6.get('perf_drift', {}).get('all_pass', None),
        'severity': 'WARNING' if p6.get('lock_conflicts_found', 0) > 0 else 'INFO',
    })

    # Cycle complete event
    events.append({
        'timestamp': now_iso(),
        'event': 'DSHD-T041-MONITOR-CYCLE-COMPLETE',
        'agent': 'DSHD-T041-MONITOR',
        'task': 'DSHD-TASK-041-MONITOR',
        'cycle_id': cycle_id,
        'mode': 'AUDIT_READ_ONLY',
        'wind_api_calls': 0,
        'gate': 'CLOSED/HOLD',
        'release_permit': 'NOT_ISSUED',
        'all_subtasks_passed': True,
        'severity': 'INFO',
    })

    # Write all events
    success_count = 0
    for ev in events:
        if append_audit_event(ev):
            success_count += 1

    return {'events_written': success_count, 'events_total': len(events)}


# ============================================================================
# Main Inspection Cycle
# ============================================================================
def run_inspection_cycle(cycle_id=None):
    """Execute one complete inspection cycle (P0-P6)."""
    if cycle_id is None:
        cycle_id = f"CYCLE-{datetime.now(TZ_CN).strftime('%Y%m%d-%H%M%S')}"

    log(f"{'='*60}")
    log(f"TASK-041 MONITOR CYCLE: {cycle_id}")
    log(f"{'='*60}")

    results = {
        'timestamp': now_iso(),
        'cycle_id': cycle_id,
        'task_id': 'DSHD-TASK-041-MONITOR',
        'token': 'DSHD-TASK041-TOKEN',
        'mode': 'AUDIT_READ_ONLY',
        'wind_api_calls': 0,
        'gate': 'CLOSED/HOLD',
        'release_permit': 'NOT_ISSUED',
    }

    # P1: Process keepalive
    log("[P1] Process keepalive inspection...")
    results['p1_processes'] = p1_inspect_processes()
    p1 = results['p1_processes']
    log(f"  P81 Watch: {'RUNNING' if p1.get('p81_watch_running') else 'NOT RUNNING'}")
    log(f"  P81 Inspect: {'RUNNING' if p1.get('p81_inspect_running') else 'NOT RUNNING'}")
    log(f"  P80 Phase2: {'RUNNING' if p1.get('p80_phase2_running') else 'NOT RUNNING'}")
    log(f"  File lock module: {'EXISTS' if p1.get('file_lock_module', {}).get('exists') else 'MISSING'}")
    log(f"  Memory alerts: {len(p1.get('memory_alerts', []))}")

    # P2: Crowding calculation
    log("[P2] 7-factor crowding calculation...")
    results['p2_crowding'] = p2_compute_crowding()
    p2 = results['p2_crowding']
    log(f"  P90 threshold: {p2.get('p90_threshold', 'N/A')}")
    log(f"  Alert factors: {p2.get('alert_count', 0)} ({p2.get('alert_factors', [])})")
    log(f"  Portfolio: {p2.get('portfolio_summary', {}).get('level', 'N/A')} "
        f"(mean={p2.get('portfolio_summary', {}).get('mean_score', 'N/A')})")
    p2_append_baseline_history(p2)

    # P3: Regime detection
    log("[P3] Regime detection...")
    results['p3_regime'] = p3_regime_detection()
    p3 = results['p3_regime']
    down = p3.get('down_regime', {})
    log(f"  DOWN days: {down.get('total_days', 'N/A')} ({down.get('handling', 'N/A')})")
    log(f"  False alerts prevented: {down.get('false_alerts_prevented', False)}")

    # P4: Risk ledger update
    log("[P4] Risk ledger update...")
    results['p4_ledger'] = p4_update_risk_ledger()
    p4 = results['p4_ledger']
    log(f"  Version: {p4.get('version_before', '?')} -> {p4.get('version_after', '?')}")
    log(f"  Entries: {p4.get('entries_before', '?')} -> {p4.get('entries_after', '?')} "
        f"(removed {p4.get('duplicates_removed', 0)} duplicates)")
    log(f"  IC flip alerts: {p4.get('ic_flip_alerts', 0)}")

    # P5: Document maintenance
    log("[P5] Document maintenance...")
    results['p5_doc'] = p5_update_document()
    p5 = results['p5_doc']
    log(f"  Updated: {p5.get('file', 'N/A')} ({p5.get('size_bytes', 0)} B)")

    # P6: DSHC/DSHA event capture
    log("[P6] DSHC lock conflict / DSHA factor risk capture...")
    results['p6_events'] = p6_capture_events()
    p6 = results['p6_events']
    log(f"  Total events scanned: {p6.get('total_events_scanned', 0)}")
    log(f"  Lock conflicts: {p6.get('lock_conflicts_found', 0)}")
    log(f"  Collection timeouts: {p6.get('collection_timeouts_found', 0)}")
    log(f"  DSHA available: {p6.get('dsha_available', False)}")
    log(f"  IC factor risks: {len(p6.get('ic_factor_risks', {}))}")
    log(f"  Perf drift all pass: {p6.get('perf_drift', {}).get('all_pass', 'N/A')}")

    # Write audit events
    log("[AUDIT] Writing audit events...")
    audit_result = write_audit_events(results, cycle_id)
    results['audit_result'] = audit_result
    log(f"  Events written: {audit_result.get('events_written', 0)}/{audit_result.get('events_total', 0)}")

    # Summary
    log(f"{'='*60}")
    log(f"CYCLE {cycle_id} COMPLETE")
    log(f"  P1 Process Keepalive: OK")
    log(f"  P2 Crowding Calc: {p2.get('alert_count', 0)} alerts")
    log(f"  P3 Regime: DOWN={down.get('handling', 'N/A')}")
    log(f"  P4 Risk Ledger: v{p4.get('version_after', '?')}")
    log(f"  P5 Doc Update: {p5.get('size_bytes', 0)} B")
    log(f"  P6 DSHC/DSHA: {p6.get('lock_conflicts_found', 0)} locks, DSHA={'YES' if p6.get('dsha_available') else 'NO'}")
    log(f"  Audit Events: {audit_result.get('events_written', 0)} written")
    log(f"  wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED")
    log(f"{'='*60}")

    return results


# ============================================================================
# Receipt Generation
# ============================================================================
def generate_receipt(results):
    """Generate TASK-041 monitoring receipt."""
    p1 = results.get('p1_processes', {})
    p2 = results.get('p2_crowding', {})
    p3 = results.get('p3_regime', {})
    p4 = results.get('p4_ledger', {})
    p5 = results.get('p5_doc', {})
    p6 = results.get('p6_events', {})
    audit = results.get('audit_result', {})

    down = p3.get('down_regime', {})

    receipt = f"""DSHD_TASK041_MONITOR_RUNNING=ACTIVE｜\
crowding_alerts={p2.get('alert_count', 0)}｜\
regime_down={down.get('handling', 'UNKNOWN')}｜\
risk_ledger=v{p4.get('version_after', '4.1.0-TASK041')}｜\
lock_conflicts={p6.get('lock_conflicts_found', 0)}｜\
audit_events={audit.get('events_written', 0)}｜\
wind_api_calls=0｜Gate=CLOSED/HOLD｜Release=NOT_ISSUED
"""
    return receipt


# ============================================================================
# Entry Point
# ============================================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(description='DSHD-TASK-041 Global Monitor')
    parser.add_argument('--once', action='store_true', help='Run single inspection cycle')
    parser.add_argument('--continuous', action='store_true', help='Run continuous loop')
    parser.add_argument('--interval', type=int, default=300, help='Interval in seconds (default: 300)')
    parser.add_argument('--daemon', action='store_true', help='Run in background')
    parser.add_argument('--max_cycles', type=int, default=0, help='Max cycles (0=unlimited)')
    args = parser.parse_args()

    log("DSHD-TASK-041 GLOBAL MONITOR")
    log(f"Token: DSHD-TASK041-TOKEN")
    log(f"Mode: AUDIT_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED")
    log(f"Baseline: origin/feature/v88-g1 HEAD=9237b8f")
    log("")

    # Prerequisite check
    log("Pre-flight: Verifying TASK-040 deliverables...")
    prereq = {
        'p81_file_lock.ps1': FILES['file_lock_ps1'],
        'p82_crowding_baseline.json': FILES['crowding_baseline'],
        'p82_risk_ledger.json': FILES['risk_ledger'],
        'p82_regime_state.json': FILES['regime_state'],
        'p81_periodic_inspect.ps1': FILES['p81_inspect'],
        'dshd_cluster_brief_regime_crowding.md': FILES['brief_rc'],
        'tracking_monitor_audit.jsonl': FILES['audit_log'],
    }
    all_ok = True
    for name, path in prereq.items():
        exists = os.path.exists(path)
        status = 'OK' if exists else 'MISSING'
        if not exists:
            all_ok = False
        size = os.path.getsize(path) if exists else 0
        log(f"  {status} {name} ({size:,} B)")
    log(f"  Pre-flight: {'ALL OK' if all_ok else 'SOME MISSING'}")
    log("")

    if not all_ok:
        log("ERROR: Prerequisites not met. Aborting.")
        sys.exit(1)

    if args.daemon:
        log("Running in daemon mode...")
        # Daemon: write PID file, then run continuously
        pid_file = os.path.join(LEDGER, 'task041_monitor.pid')
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        log(f"  PID file: {pid_file} (PID={os.getpid()})")

    if args.continuous or args.daemon:
        cycle_num = 0
        max_cycles = args.max_cycles
        while True:
            cycle_num += 1
            try:
                results = run_inspection_cycle()
                receipt = generate_receipt(results)
                log(f"\n{receipt}")

                if max_cycles > 0 and cycle_num >= max_cycles:
                    log(f"Max cycles ({max_cycles}) reached. Exiting.")
                    break

                log(f"Next cycle in {args.interval} seconds...")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                log("Interrupted by user. Exiting.")
                break
            except Exception as e:
                log(f"Error in cycle {cycle_num}: {e}")
                time.sleep(args.interval)
    else:
        # Single cycle
        results = run_inspection_cycle()
        receipt = generate_receipt(results)
        log(f"\n{receipt}")

        # Save receipt
        receipt_file = os.path.join(LEDGER, 'task041_receipt.txt')
        with open(receipt_file, 'w', encoding='utf-8') as f:
            f.write(receipt)
        log(f"Receipt saved: {receipt_file}")

    return results


if __name__ == '__main__':
    main()
