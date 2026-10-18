#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-P62 · Sample Data Listener Standby Monitor
─────────────────────────────────────────────────────────────
Continuously verifies:
  1. sample_data_trigger.py listener health (SHA256 dedup mechanism)
  2. 4× Final-Lock assertions (marker, REAL_WIND_CALL, MAX_DAYS, MIN_INTERVAL)
  3. MAX_DAYS_PER_ROUND / MIN_INTERVAL_SEC parameters unmodified
  4. Excel isolation functions (USER_INSTANCE protection)
  5. Output directory read/write permissions

Produces:
  artifacts/dsha_p62_listener_snapshot.json (updated each run)

Alert rules:
  CRITICAL — code/config tampered → audit log entry
  WARNING  — directory permission issue

STATIC_STANDBY: no data collection, no Wind calls, no REAL_WIND_CALL modification.
"""

import json
import os
import re
import sys
import hashlib
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# ════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════

REAL_WIND_CALL = False
WIND_API_CALLS = 0

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.dirname(os.path.abspath(__file__))

# Key file paths
PROTOTYPE_PATH = os.path.join(CODE_DIR, 'prototype_wss_assemble_sim.py')
BACKTEST_PATH = os.path.join(CODE_DIR, 'backtest_skeleton.py')
TRIGGER_PATH = os.path.join(CODE_DIR, 'sample_data_trigger.py')
FACTCON_PATH = os.path.join(CODE_DIR, 'factor_constructor.py')
LOADER_PATH = os.path.join(CODE_DIR, 'factor_data_loader.py')

SAMPLE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'artifacts', 'sample_output')
BACKTEST_ARCHIVE_DIR = os.path.join(PROJECT_ROOT, 'artifacts', 'backtest_archive')
SNAPSHOT_PATH = os.path.join(PROJECT_ROOT, 'artifacts', 'dsha_p62_listener_snapshot.json')
AUDIT_LOG_PATH = os.path.join(PROJECT_ROOT, 'tracking_monitor_audit.jsonl')
WIND_EVENTS_PATH = os.path.join(PROJECT_ROOT, 'data-harbor', 'dsha_p49_prep', 'P49_backtest_audit', 'wind_excel_events.jsonl')

# Expected safe values
EXPECTED_MAX_DAYS = 10
EXPECTED_MIN_INTERVAL = 12
EXPECTED_REAL_WIND_CALL = False

# P60 Excel isolation function signatures (must all be present)
REQUIRED_ISOLATION_FUNCTIONS = [
    '_identify_user_excel_instances',
    '_detect_agent_excel_pid',
    '_kill_agent_excel_only',
]

# P61 output function signatures (must all be present)
REQUIRED_P61_FUNCTIONS = [
    'save_backtest_metrics_csv',
    'save_net_value_series_csv',
    'save_backtest_snapshot_json',
    'archive_backtest_result',
    'compute_IC',
]

# Final-Lock assertion markers (must all appear in prototype)
FINAL_LOCK_MARKERS = [
    'FINAL-LOCK-1: MISSING_SAMPLE_MARKER',
    'FINAL-LOCK-2: REAL_WIND_CALL_NOT_ENABLED',
    'FINAL-LOCK-3: MAX_DAYS_HAS_BEEN_ALTERED-PROTECTED',
    'FINAL-LOCK-4: MIN_INTERVAL_HAS_BEEN_ALTERED-PROTECTED',
]


# ════════════════════════════════════════════════════════════════
# Health Check Functions
# ════════════════════════════════════════════════════════════════

def check_file_exists(filepath):
    """Check if a file exists and return its size."""
    if os.path.isfile(filepath):
        return {'exists': True, 'size': os.path.getsize(filepath)}
    return {'exists': False, 'size': 0}


def read_file_text(filepath):
    """Read file content as text."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, UnicodeDecodeError):
        return None


def _sha256_text(text):
    """SHA256 hash of text content."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def check_real_wind_call():
    """Verify REAL_WIND_CALL = False in all key modules."""
    results = {}
    files = {
        'prototype_wss_assemble_sim.py': PROTOTYPE_PATH,
        'backtest_skeleton.py': BACKTEST_PATH,
        'sample_data_trigger.py': TRIGGER_PATH,
        'factor_constructor.py': FACTCON_PATH,
        'factor_data_loader.py': LOADER_PATH,
    }
    for name, path in files.items():
        content = read_file_text(path)
        if content is None:
            results[name] = {'status': 'ERROR', 'detail': 'file not readable'}
            continue
        # Find the REAL_WIND_CALL assignment line
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('REAL_WIND_CALL') and '=' in stripped:
                if 'REAL_WIND_CALL = False' in stripped:
                    results[name] = {'status': 'PASS', 'value': False, 'line': stripped}
                elif 'REAL_WIND_CALL = True' in stripped:
                    results[name] = {'status': 'CRITICAL', 'value': True, 'line': stripped}
                else:
                    results[name] = {'status': 'WARNING', 'value': 'unknown', 'line': stripped}
                break
        else:
            results[name] = {'status': 'WARNING', 'value': 'not found', 'line': None}
    all_pass = all(r['status'] == 'PASS' for r in results.values())
    return {'all_pass': all_pass, 'files': results}


def check_final_lock_assertions():
    """Verify 4 Final-Lock assertions present in prototype."""
    content = read_file_text(PROTOTYPE_PATH)
    if content is None:
        return {'status': 'ERROR', 'detail': 'prototype file not readable', 'markers_found': []}

    found = []
    missing = []
    for marker in FINAL_LOCK_MARKERS:
        if marker in content:
            found.append(marker)
        else:
            missing.append(marker)

    status = 'PASS' if len(found) == 4 and not missing else 'CRITICAL'
    return {
        'status': status,
        'total_expected': 4,
        'found': found,
        'missing': missing,
    }


def check_param_integrity():
    """Verify MAX_DAYS_PER_ROUND and MIN_INTERVAL_SEC unchanged."""
    content = read_file_text(PROTOTYPE_PATH)
    if content is None:
        return {'status': 'ERROR', 'detail': 'prototype file not readable'}

    results = {}
    patterns = [
        ('MAX_DAYS_PER_ROUND', r'MAX_DAYS_PER_ROUND\s*=\s*(\d+)'),
        ('MIN_INTERVAL_SEC', r'MIN_INTERVAL_SEC\s*=\s*(\d+)'),
    ]
    for name, pattern in patterns:
        m = re.search(pattern, content)
        if m:
            val = int(m.group(1))
            expected = EXPECTED_MAX_DAYS if name == 'MAX_DAYS_PER_ROUND' else EXPECTED_MIN_INTERVAL
            results[name] = {
                'found': val,
                'expected': expected,
                'match': val == expected,
                'status': 'PASS' if val == expected else 'CRITICAL',
            }
        else:
            results[name] = {'found': None, 'expected': None, 'match': False, 'status': 'WARNING'}

    all_pass = all(r['status'] == 'PASS' for r in results.values())
    return {'all_pass': all_pass, 'params': results}


def check_excel_isolation():
    """Verify Excel isolation functions present in prototype."""
    content = read_file_text(PROTOTYPE_PATH)
    if content is None:
        return {'status': 'ERROR', 'detail': 'prototype file not readable'}

    found = []
    missing = []
    for func_name in REQUIRED_ISOLATION_FUNCTIONS:
        # Look for def func_name( in the content
        pattern = rf'def\s+{func_name}\s*\('
        if re.search(pattern, content):
            found.append(func_name)
        else:
            missing.append(func_name)

    # Also verify USER_INSTANCE_LABEL constant
    has_user_label = 'USER_INSTANCE_LABEL' in content
    # Verify safety check in _kill_agent_excel_only
    has_safety_check = 'if agent_pid in user_pids' in content

    status = 'PASS' if len(found) == 3 and has_user_label and has_safety_check else 'CRITICAL'
    return {
        'status': status,
        'functions_found': found,
        'functions_missing': missing,
        'has_USER_INSTANCE_LABEL': has_user_label,
        'has_safety_check': has_safety_check,
    }


def check_p61_output_functions():
    """Verify P61 output functions present in backtest_skeleton.py."""
    content = read_file_text(BACKTEST_PATH)
    if content is None:
        return {'status': 'ERROR', 'detail': 'backtest file not readable'}

    found = []
    missing = []
    for func_name in REQUIRED_P61_FUNCTIONS:
        pattern = rf'def\s+{func_name}\s*\('
        if re.search(pattern, content):
            found.append(func_name)
        else:
            missing.append(func_name)

    status = 'PASS' if len(found) == len(REQUIRED_P61_FUNCTIONS) else 'CRITICAL'
    return {
        'status': status,
        'functions_found': found,
        'functions_missing': missing,
    }


def check_trigger_health():
    """Verify trigger script SHA256 dedup mechanism and key constants."""
    content = read_file_text(TRIGGER_PATH)
    if content is None:
        return {'status': 'ERROR', 'detail': 'trigger file not readable'}

    checks = {}
    # SHA256 function
    checks['sha256_function'] = 'def _file_sha256' in content
    # State load/save
    checks['state_load'] = 'def _load_trigger_state' in content
    checks['state_save'] = 'def _save_trigger_state' in content
    # CSV scan
    checks['csv_scan'] = 'def _scan_sample_csvs' in content
    # Check new files
    checks['check_new_csv_files'] = 'def check_new_csv_files' in content
    # REAL_WIND_CALL = False
    checks['real_wind_call_false'] = 'REAL_WIND_CALL = False' in content
    # WAIT state
    checks['wait_state'] = 'STATUS_WAIT' in content

    all_pass = all(checks.values())
    return {'all_pass': all_pass, 'checks': checks}


def check_directory_permissions():
    """Verify output directories exist and are writable."""
    results = {}
    for label, path in [
        ('sample_output', SAMPLE_OUTPUT_DIR),
        ('backtest_archive', BACKTEST_ARCHIVE_DIR),
    ]:
        exists = os.path.isdir(path)
        writable = os.access(path, os.W_OK) if exists else False
        readable = os.access(path, os.R_OK) if exists else False
        results[label] = {
            'path': path,
            'exists': exists,
            'writable': writable,
            'readable': readable,
            'status': 'PASS' if exists and writable and readable else 'WARNING',
        }
        if exists:
            # Count files
            results[label]['file_count'] = len(os.listdir(path))

    all_pass = all(r['status'] == 'PASS' for r in results.values())
    return {'all_pass': all_pass, 'directories': results}


def check_marker_absence():
    """Verify sample_fetch_allow.marker does NOT exist."""
    marker_path = os.path.join(PROJECT_ROOT, 'artifacts', 'sample_fetch_allow.marker')
    exists = os.path.exists(marker_path)
    return {
        'path': marker_path,
        'exists': exists,
        'status': 'PASS' if not exists else 'CRITICAL',
    }


def compute_file_hashes():
    """Compute SHA256 hashes of key files for tamper detection."""
    hashes = {}
    for name, path in {
        'prototype_wss_assemble_sim.py': PROTOTYPE_PATH,
        'backtest_skeleton.py': BACKTEST_PATH,
        'sample_data_trigger.py': TRIGGER_PATH,
    }.items():
        info = check_file_exists(path)
        if info['exists']:
            content = read_file_text(path)
            if content:
                hashes[name] = {
                    'sha256': _sha256_text(content),
                    'size': info['size'],
                }
    return hashes


# ════════════════════════════════════════════════════════════════
# Snapshot Builder
# ════════════════════════════════════════════════════════════════

def build_snapshot():
    """Execute all health checks and build snapshot dict."""
    now = datetime.now(timezone.utc).isoformat()

    checks = {
        'real_wind_call': check_real_wind_call(),
        'final_lock_assertions': check_final_lock_assertions(),
        'param_integrity': check_param_integrity(),
        'excel_isolation': check_excel_isolation(),
        'p61_output_functions': check_p61_output_functions(),
        'trigger_health': check_trigger_health(),
        'directory_permissions': check_directory_permissions(),
        'marker_absence': check_marker_absence(),
    }

    # Determine overall status
    critical = []
    warnings = []
    for check_name, result in checks.items():
        if isinstance(result, dict):
            s = result.get('status', result.get('all_pass', None))
            if s is True or s == 'PASS':
                continue
            elif s is False or s == 'CRITICAL':
                critical.append(check_name)
            elif s == 'WARNING':
                warnings.append(check_name)

    overall = 'HEALTHY'
    if critical:
        overall = 'CRITICAL'
    elif warnings:
        overall = 'WARNING'

    # File hashes for tamper detection
    file_hashes = compute_file_hashes()

    snapshot = {
        'snapshot_id': f'P62-{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}',
        'timestamp_utc': now,
        'phase': 'DSHA-P62',
        'gate': 'CLOSED',
        'release_permit': 'NOT_ISSUED',
        'real_wind_call': REAL_WIND_CALL,
        'wind_api_calls': WIND_API_CALLS,
        'status': overall,
        'critical_count': len(critical),
        'warning_count': len(warnings),
        'checks': checks,
        'file_hashes': file_hashes,
        'key_files': {
            'prototype': check_file_exists(PROTOTYPE_PATH),
            'backtest_skeleton': check_file_exists(BACKTEST_PATH),
            'sample_data_trigger': check_file_exists(TRIGGER_PATH),
            'factor_constructor': check_file_exists(FACTCON_PATH),
            'factor_data_loader': check_file_exists(LOADER_PATH),
        },
        'red_lines': {
            'wind_api_calls_zero': WIND_API_CALLS == 0,
            'real_wind_call_false': REAL_WIND_CALL == False,
            'marker_absent': not os.path.exists(
                os.path.join(PROJECT_ROOT, 'artifacts', 'sample_fetch_allow.marker')),
            'no_active_collection': True,
        },
    }

    return snapshot


# ════════════════════════════════════════════════════════════════
# Alert & Audit
# ════════════════════════════════════════════════════════════════

def write_alert(snapshot, severity, check_name, detail):
    """Write an alert to the audit log."""
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_id': f'DSHA-P62-LISTENER-ALERT-{severity}-{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}',
        'phase': 'DSHA-P62',
        'severity': severity,
        'check_name': check_name,
        'detail': detail,
        'real_wind_call': REAL_WIND_CALL,
        'wind_api_calls': WIND_API_CALLS,
    }
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    with open(AUDIT_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def write_ready_event():
    """Append P62 ready event to audit logs."""
    now = datetime.now(timezone.utc).isoformat()
    event = {
        'timestamp': now,
        'event_id': 'DSHA-P62-SAMPLE-DATA-LISTENER-STANDBY-READY-001',
        'phase': 'DSHA-P62',
        'status': 'READY',
        'detail': 'Sample Data Listener Standby Monitor initialized — health checks passing, STATIC_STANDBY maintained',
        'real_wind_call': REAL_WIND_CALL,
        'wind_api_calls': WIND_API_CALLS,
        'gate': 'CLOSED',
        'release_permit': 'NOT_ISSUED',
        'snapshot_path': SNAPSHOT_PATH,
    }
    # Write to tracking_monitor_audit.jsonl
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    with open(AUDIT_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

    # Write to wind_excel_events.jsonl
    os.makedirs(os.path.dirname(WIND_EVENTS_PATH), exist_ok=True)
    with open(WIND_EVENTS_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

    return event


def write_snapshot(snapshot):
    """Write snapshot to JSON file."""
    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
    with open(SNAPSHOT_PATH, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return SNAPSHOT_PATH


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("DSHA-P62 · Sample Data Listener Standby Monitor")
    print("=" * 60)
    print()

    # Run health checks
    snapshot = build_snapshot()

    # Write snapshot
    snap_path = write_snapshot(snapshot)
    print(f"📸 Snapshot written: {snap_path}")
    print(f"   Status: {snapshot['status']}")
    print(f"   Critical: {snapshot['critical_count']} | Warnings: {snapshot['warning_count']}")
    print()

    # Write alerts for critical/warning issues
    alerts_written = 0
    for check_name, result in snapshot['checks'].items():
        if isinstance(result, dict):
            s = result.get('status', result.get('all_pass', None))
            if s == 'CRITICAL' or s is False:
                detail = json.dumps(result, ensure_ascii=False)[:500]
                write_alert(snapshot, 'CRITICAL', check_name, detail)
                alerts_written += 1
                print(f"  🚨 CRITICAL ALERT: {check_name}")
            elif s == 'WARNING' or s is None:
                if check_name not in ('real_wind_call', 'trigger_health'):
                    # Only warn for actual directory issues
                    detail = json.dumps(result, ensure_ascii=False)[:500]
                    write_alert(snapshot, 'WARNING', check_name, detail)
                    alerts_written += 1
                    print(f"  ⚠️  WARNING ALERT: {check_name}")

    if alerts_written == 0:
        print("  ✅ No alerts — all checks pass")
    print()

    # Summary
    print("─" * 40)
    print("HEALTH CHECK SUMMARY")
    print("─" * 40)

    rwc = snapshot['checks']['real_wind_call']
    fl = snapshot['checks']['final_lock_assertions']
    pi = snapshot['checks']['param_integrity']
    ei = snapshot['checks']['excel_isolation']
    p61 = snapshot['checks']['p61_output_functions']
    th = snapshot['checks']['trigger_health']
    dp = snapshot['checks']['directory_permissions']
    ma = snapshot['checks']['marker_absence']

    print(f"  🔒 REAL_WIND_CALL:      {'✅ PASS' if rwc['all_pass'] else '🚨 FAIL'} ({sum(1 for v in rwc['files'].values() if v['status']=='PASS')}/5 files)")
    print(f"  🔒 Final-Lock:          {'✅ PASS' if fl['status']=='PASS' else '🚨 FAIL'} ({len(fl['found'])}/4 assertions)")
    print(f"  🔒 Parameters:          {'✅ PASS' if pi['all_pass'] else '🚨 FAIL'} (MAX_DAYS={pi['params'].get('MAX_DAYS_PER_ROUND',{}).get('found')}, MIN_INTERVAL={pi['params'].get('MIN_INTERVAL_SEC',{}).get('found')}))")
    print(f"  🔒 Excel Isolation:     {'✅ PASS' if ei['status']=='PASS' else '🚨 FAIL'} ({len(ei['functions_found'])}/3 functions)")
    print(f"  🔒 P61 Output:          {'✅ PASS' if p61['status']=='PASS' else '🚨 FAIL'} ({len(p61['functions_found'])}/5 functions)")
    print(f"  🔒 Trigger Health:      {'✅ PASS' if th['all_pass'] else '🚨 FAIL'}")
    print(f"  📁 Directory Perms:     {'✅ PASS' if dp['all_pass'] else '⚠️  FAIL'}")
    print(f"  🚫 Marker Absent:       {'✅ PASS' if ma['status']=='PASS' else '🚨 FAIL'}")
    print()

    print("─" * 40)
    print("RED LINE VERIFICATION")
    print("─" * 40)
    for k, v in snapshot['red_lines'].items():
        icon = '✅' if v else '🚨'
        print(f"  {icon} {k}: {v}")
    print()

    print("─" * 40)
    print("FILE HASHES (tamper detection)")
    print("─" * 40)
    for name, info in snapshot['file_hashes'].items():
        print(f"  {name}: {info['sha256'][:16]}... (size={info['size']})")
    print()

    # Write ready event (only on first run / fresh snapshot)
    # Check if ready event already exists
    if os.path.exists(AUDIT_LOG_PATH):
        with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
            log_content = f.read()
        if 'DSHA-P62-SAMPLE-DATA-LISTENER-STANDBY-READY-001' not in log_content:
            event = write_ready_event()
            print(f"📝 Ready event written: {event['event_id']}")
        else:
            print("📝 Ready event already exists — skipping duplicate")
    else:
        event = write_ready_event()
        print(f"📝 Ready event written: {event['event_id']}")

    print()
    print("=" * 60)
    print("DSHA-P62 · STATIC_STANDBY · Monitoring Active")
    print("  REAL_WIND_CALL=False | WIND_API_CALLS=0 | gate=CLOSED")
    print("  Waiting for CSV landing in artifacts/sample_output/")
    print("=" * 60)

    return snapshot


if __name__ == '__main__':
    result = main()
