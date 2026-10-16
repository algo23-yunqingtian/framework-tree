#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wind Online Watcher — Safe Trigger for Factor Calculation

TASK_ID: V88_PHASE03_P4_DSHB_P014_READY_FOR_FACTOR_CALC
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)
GENERATED: 2026-10-22

⚠️  CRITICAL SAFETY NOTICE ⚠️
============================================================
1. This watcher is DETECTION-ONLY. It NEVER initiates any
   external API call or data pull on its own.

2. DEFAULT STATE: SLEEP. The watcher sleeps indefinitely
   until WIND_DATA_LINK_ONLINE.flag is detected at the
   repository root.

3. NO FLAG = NO ACTION. Without the flag, the watcher
   will NEVER start factor calculation, NEVER call any
   external interface, and NEVER bypass any gateway.

4. The watcher does NOT:
   - Import WindPy
   - Call any Wind API
   - Pull any external data
   - Execute any git push
   - Modify any file outside its designated output
   - Bypass any security gateway

5. When the flag IS detected, the watcher ONLY:
   - Logs the detection event
   - Writes a trigger status file
   - Can invoke the pre-approved factor calculation entry
     point (which itself is gated and inert)

6. The watcher NEVER bypasses HERMES release gate or
   the dual-lock baseline merge policy.

⚠️  END OF SAFETY NOTICE ⚠️
============================================================

Author: DSHB Agent
Version: 1.0.0
Status: DORMANT (default sleep, no flag = no action)
"""

import json
import logging
import os
import sys
import time
from datetime import datetime

# =============================================================================
# CONFIGURATION — DO NOT MODIFY WITHOUT REVIEW
# =============================================================================

# Path to the trigger flag (at repository root)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FLAG_PATH = os.path.join(REPO_ROOT, 'WIND_DATA_LINK_ONLINE.flag')

# Paths for watcher output
WATCHER_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(WATCHER_DIR, 'wind_watcher_status.json')
LOG_FILE = os.path.join(WATCHER_DIR, 'wind_watcher.log')

# Path to the factor calculation skeleton
FACTOR_CALC_PATH = os.path.join(REPO_ROOT, 'factor_workspace', 'pb_zn_recyclepb_v1', 'ic_ir_calc_skeleton.py')

# Polling interval (seconds)
POLL_INTERVAL_SECONDS = 300  # 5 minutes
POLL_TIMEOUT_SECONDS = 0     # 0 = poll indefinitely (default sleep)

# Maximum number of polls before giving up (0 = unlimited)
MAX_POLLS = 0

# Safety limits
MAX_FLAG_SIZE_BYTES = 1024 * 1024  # 1 MB max flag file size
MIN_FLAG_AGE_SECONDS = 0           # 0 = accept immediately


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger('wind_online_watcher')


# =============================================================================
# FLAG DETECTION
# =============================================================================

def check_flag_exists():
    """
    Check if WIND_DATA_LINK_ONLINE.flag exists and is valid.

    The flag must:
    - Exist as a file at the repository root
    - Be non-empty (at least 1 byte)
    - Not exceed 1 MB
    - Be older than MIN_FLAG_AGE_SECONDS (0 = immediate)

    Returns:
        tuple: (flag_exists: bool, flag_info: dict)
    """
    if not os.path.exists(FLAG_PATH):
        return False, {
            'status': 'NOT_FOUND',
            'flag_path': FLAG_PATH,
            'message': 'WIND_DATA_LINK_ONLINE.flag not found at repository root',
            'next_action': 'SLEEP_AND_RETRY',
        }

    # Validate flag file
    try:
        stat = os.stat(FLAG_PATH)
        size_bytes = stat.st_size
        age_seconds = time.time() - stat.st_mtime

        # Check size
        if size_bytes == 0:
            return False, {
                'status': 'EMPTY',
                'flag_path': FLAG_PATH,
                'size_bytes': 0,
                'message': 'Flag file is empty (0 bytes) — invalid trigger',
                'next_action': 'SLEEP_AND_RETRY',
            }

        if size_bytes > MAX_FLAG_SIZE_BYTES:
            return False, {
                'status': 'TOO_LARGE',
                'flag_path': FLAG_PATH,
                'size_bytes': size_bytes,
                'message': f'Flag file exceeds max size ({size_bytes} > {MAX_FLAG_SIZE_BYTES} bytes)',
                'next_action': 'SLEEP_AND_RETRY',
            }

        # Check age
        if age_seconds < MIN_FLAG_AGE_SECONDS:
            return False, {
                'status': 'TOO_NEW',
                'flag_path': FLAG_PATH,
                'age_seconds': age_seconds,
                'message': f'Flag file is too new ({age_seconds:.1f}s < {MIN_FLAG_AGE_SECONDS}s)',
                'next_action': 'SLEEP_AND_RETRY',
            }

        # Read flag content for logging (first 500 chars)
        with open(FLAG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            flag_content = f.read(500)

        return True, {
            'status': 'FOUND_VALID',
            'flag_path': FLAG_PATH,
            'size_bytes': size_bytes,
            'age_seconds': round(age_seconds, 1),
            'content_preview': flag_content[:200],
            'message': 'WIND_DATA_LINK_ONLINE.flag detected and validated',
            'next_action': 'PROCEED_TO_PRECHECK',
        }

    except Exception as e:
        return False, {
            'status': 'ERROR',
            'flag_path': FLAG_PATH,
            'error': str(e),
            'message': f'Error checking flag: {e}',
            'next_action': 'SLEEP_AND_RETRY',
        }


# =============================================================================
# STATUS TRACKING
# =============================================================================

def write_status(status_data):
    """Write watcher status to status file."""
    status_data['last_check_timestamp'] = datetime.now().isoformat()
    status_data['script_version'] = '1.0.0'
    status_data['repo_root'] = REPO_ROOT
    status_data['flag_path'] = FLAG_PATH
    status_data['poll_interval_seconds'] = POLL_INTERVAL_SECONDS

    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2, ensure_ascii=False)


def append_log(message):
    """Append a log entry to the audit log."""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'message': message,
    }
    log_dir = os.path.join(REPO_ROOT, 'factor_workspace', 'pb_zn_recyclepb_v1', 'audit')
    log_path = os.path.join(log_dir, 'trigger_events.jsonl')
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


# =============================================================================
# PRE-CHECK (Before invoking calculation)
# =============================================================================

def precheck():
    """
    Run pre-checks before allowing factor calculation.
    
    These checks ensure:
    1. The factor calculation skeleton exists
    2. The workspace directories exist
    3. The skeleton script does NOT contain hardcoded WindPy calls
    4. No auto-push commands exist in the skeleton
    """
    checks = {}

    # Check 1: Factor skeleton exists
    checks['skeleton_exists'] = os.path.exists(FACTOR_CALC_PATH)
    if not checks['skeleton_exists']:
        return False, {'error': f'Factor skeleton not found: {FACTOR_CALC_PATH}'}

    # Check 2: Workspace directories exist
    workspace = os.path.join(REPO_ROOT, 'factor_workspace', 'pb_zn_recyclepb_v1')
    for subdir in ['input', 'output', 'audit', 'checksum']:
        checks[f'workspace_{subdir}'] = os.path.isdir(os.path.join(workspace, subdir))

    if not all(checks[f'workspace_{s}'] for s in ['input', 'output', 'audit', 'checksum']):
        missing = [s for s in ['input', 'output', 'audit', 'checksum'] if not checks[f'workspace_{s}']]
        return False, {'error': f'Missing workspace directories: {missing}'}

    # Check 3: Skeleton does NOT contain hardcoded WindPy calls
    wind_patterns = ['import WindPy', 'from WindPy', 'import wind', 'from wind',
                     'w.wss(', 'w.wset(', 'w.wsi(', 'w.wts(', 'WindPy.w.']
    with open(FACTOR_CALC_PATH, 'r', encoding='utf-8', errors='replace') as f:
        skeleton_content = f.read()

    for pattern in wind_patterns:
        if pattern in skeleton_content:
            return False, {'error': f'WARNING: Pattern "{pattern}" found in skeleton — possible hardcoded Wind call'}
    
    checks['no_hardcoded_wind_calls'] = True

    # Check 4: No git push commands in skeleton
    git_patterns = ['git push', 'git commit', 'git add', 'subprocess.run.*git', 'os.system.*git']
    import re
    for pattern in git_patterns:
        if re.search(pattern, skeleton_content):
            return False, {'error': f'WARNING: Git pattern "{pattern}" found in skeleton — possible auto-push'}
    
    checks['no_auto_push'] = True

    return True, checks


# =============================================================================
# MAIN WATCHER LOOP
# =============================================================================

def watch(flag_check_only=False):
    """
    Main watcher loop.
    
    Default behavior: SLEEP until flag detected.
    - If flag NOT found: log status, sleep POLL_INTERVAL_SECONDS, retry
    - If flag FOUND: run precheck, invoke factor calculation if precheck passes
    
    Args:
        flag_check_only: If True, check flag once and exit (no loop)
    
    Returns:
        dict: Final status
    """
    logger = setup_logging()
    logger.info("=" * 70)
    logger.info("Wind Online Watcher — STARTING")
    logger.info(f"Flag path: {FLAG_PATH}")
    logger.info(f"Poll interval: {POLL_INTERVAL_SECONDS}s")
    logger.info(f"Max polls: {MAX_POLLS if MAX_POLLS > 0 else 'unlimited'}")
    logger.info("=" * 70)

    poll_count = 0
    final_status = {
        'status': 'NOT_STARTED',
        'watch_start_time': datetime.now().isoformat(),
        'poll_count': 0,
        'final_state': 'IDLE',
    }

    while True:
        poll_count += 1

        # Write periodic status
        status_data = {
            'status': 'WATCHING',
            'poll_count': poll_count,
            'poll_interval_seconds': POLL_INTERVAL_SECONDS,
            'flag_detected': False,
            'final_state': 'IDLE_SLEEPING',
        }
        write_status(status_data)

        # Check flag
        flag_exists, flag_info = check_flag_exists()
        logger.info(f"Poll #{poll_count}: flag_exists={flag_exists}, status={flag_info.get('status', 'UNKNOWN')}")

        if not flag_exists:
            # No flag — default sleep behavior
            logger.info(f"Flag not found ({flag_info.get('status', 'UNKNOWN')}). Sleeping {POLL_INTERVAL_SECONDS}s...")
            logger.info("  ⚠️  No action taken. Default SLEEP mode. No API calls made.")

            if MAX_POLLS > 0 and poll_count >= MAX_POLLS:
                logger.info(f"Max polls ({MAX_POLLS}) reached. Exiting.")
                final_status['status'] = 'TIMEOUT'
                final_status['final_state'] = 'TIMEOUT_NO_FLAG'
                break

            if flag_check_only:
                logger.info("One-shot check mode. Exiting.")
                final_status['status'] = 'NO_FLAG'
                final_status['final_state'] = 'NO_FLAG_ONESHOT'
                break

            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        # ---- FLAG DETECTED ----
        logger.info("=" * 70)
        logger.info("🚀 WIND_DATA_LINK_ONLINE.flag DETECTED!")
        logger.info(f"Flag info: {json.dumps(flag_info, indent=2, ensure_ascii=False)}")
        logger.info("=" * 70)

        final_status['status'] = 'FLAG_DETECTED'
        final_status['flag_info'] = flag_info
        append_log('WIND_DATA_LINK_ONLINE.flag detected — proceeding to precheck')

        if flag_check_only:
            logger.info("One-shot check mode — flag found. Exiting without calculation.")
            final_status['final_state'] = 'FLAG_DETECTED_ONESHOT'
            break

        # Run pre-checks
        logger.info("Running pre-checks...")
        precheck_ok, precheck_result = precheck()
        
        if not precheck_ok:
            logger.warning(f"Pre-check FAILED: {precheck_result}")
            final_status['status'] = 'PRECHECK_FAILED'
            final_status['final_state'] = 'PRECHECK_FAILED'
            final_status['precheck_result'] = precheck_result
            append_log(f'Pre-check failed: {precheck_result}')
            # Sleep and retry (the flag might be stale)
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        logger.info(f"Pre-check PASSED: {json.dumps(precheck_result, indent=2)}")
        append_log('Pre-check passed — proceeding to calculation')

        # ---- INVOKED CALCULATION (GATED AND INERT) ----
        # The calculation skeleton itself checks the flag again (defense in depth)
        # and is inert unless real data is available
        try:
            logger.info("Invoking factor calculation entry point (gated)...")
            logger.info(f"  Entry point: {FACTOR_CALC_PATH}")
            logger.info("  Note: This entry point is ITSELF gated and will not produce")
            logger.info("        results without real data ingestion through the approved gateway.")

            # The calculation will execute but will likely return STUB_INERT
            # because real data ingestion hasn't been set up yet
            import subprocess
            calc_result = subprocess.run(
                [sys.executable, FACTOR_CALC_PATH, '--factor-id', 'momentum_20d', '--variety', 'PB'],
                capture_output=True,
                text=True,
                timeout=300,
            )
            logger.info(f"Calculation exit code: {calc_result.returncode}")
            logger.info(f"Calculation stdout: {calc_result.stdout[:500]}")
            if calc_result.stderr:
                logger.warning(f"Calculation stderr: {calc_result.stderr[:500]}")

            append_log(f'Calculation completed with exit code {calc_result.returncode}')
            final_status['status'] = 'CALCULATION_INVOKED'
            final_status['final_state'] = 'CALCULATION_COMPLETED'
            final_status['calc_exit_code'] = calc_result.returncode

        except subprocess.TimeoutExpired:
            logger.error("Calculation timed out (300s)")
            append_log('Calculation timed out')
            final_status['status'] = 'CALCULATION_TIMEOUT'
            final_status['final_state'] = 'CALCULATION_TIMEOUT'
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            append_log(f'Calculation error: {e}')
            final_status['status'] = 'CALCULATION_ERROR'
            final_status['final_state'] = 'CALCULATION_ERROR'
            final_status['error'] = str(e)

        break  # Exit watcher loop after processing flag

    # Write final status
    final_status['watch_end_time'] = datetime.now().isoformat()
    final_status['poll_count'] = poll_count
    write_status(final_status)
    logger.info(f"Final status: {json.dumps(final_status, indent=2, ensure_ascii=False)}")
    logger.info("Wind Online Watcher — STOPPED")
    
    return final_status


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Wind Online Watcher — Safe trigger for factor calculation (dormant by default)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '⚠️  SAFETY NOTICE:\n'
            '  This watcher is DETECTION-ONLY. It NEVER initiates any\n'
            '  external API call or data pull on its own.\n\n'
            '  DEFAULT STATE: SLEEP. The watcher sleeps indefinitely\n'
            '  until WIND_DATA_LINK_ONLINE.flag is detected.\n\n'
            '  NO FLAG = NO ACTION. Without the flag, the watcher\n'
            '  will NEVER start factor calculation, NEVER call any\n'
            '  external interface, and NEVER bypass any gateway.\n\n'
            '  Usage examples:\n'
            '    # Check flag once and exit (no loop)\n'
            '    python wind_online_watcher.py --check-only\n\n'
            '    # Start watching (default: sleep until flag detected)\n'
            '    python wind_online_watcher.py\n\n'
            '    # Watch with 60s poll interval\n'
            '    python wind_online_watcher.py --interval 60\n\n'
            '    # Watch for max 10 polls then exit\n'
            '    python wind_online_watcher.py --max-polls 10\n'
        )
    )

    parser.add_argument('--check-only', action='store_true',
                        help='Check flag once and exit (no loop, no calculation)')
    parser.add_argument('--interval', type=int, default=POLL_INTERVAL_SECONDS,
                        help=f'Poll interval in seconds (default: {POLL_INTERVAL_SECONDS})')
    parser.add_argument('--max-polls', type=int, default=MAX_POLLS,
                        help=f'Maximum polls before exit (default: {MAX_POLLS}, 0=unlimited)')
    parser.add_argument('--flag-path', default=None,
                        help='Custom flag path (default: WIND_DATA_LINK_ONLINE.flag at repo root)')

    args = parser.parse_args()

    # Override defaults if specified
    global POLL_INTERVAL_SECONDS, MAX_POLLS
    POLL_INTERVAL_SECONDS = args.interval
    MAX_POLLS = args.max_polls

    if args.flag_path:
        global FLAG_PATH
        FLAG_PATH = args.flag_path

    watch(flag_check_only=args.check_only)


if __name__ == '__main__':
    main()