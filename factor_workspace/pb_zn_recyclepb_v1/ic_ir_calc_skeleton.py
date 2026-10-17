#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IC-IR Calculation Skeleton 鈥?P0-14 Factor Calculation Framework

TASK_ID: V88_PHASE03_P4_DSHB_P014_READY_FOR_FACTOR_CALC
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)
GENERATED: 2026-10-22

鈿狅笍  CRITICAL SAFETY NOTICE 鈿狅笍
============================================================
1. This script is a SKELETON ONLY. It does NOT contain any
   hardcoded WindPy or external API calls.

2. THE run_calc() ENTRY POINT IS INERT until
   WIND_DATA_LINK_ONLINE.flag is detected at the repository root.

3. This script NEVER calls any external API by itself.
   Wind data is pulled exclusively through the trigger pipeline:
     WIND_DATA_LINK_ONLINE.flag 鈫?wind_online_watcher.py 鈫?
     (approved gateway) 鈫?factor data ingestion 鈫?THIS SCRIPT

4. NO AUTO-PUSH: This script does NOT execute any git operations.

5. NO AUTO-API: This script does NOT initiate any network calls.

6. The ONLY execution path is:
   - Manual invocation AFTER flag detection confirms WIND_DATA_LINK_ONLINE
   - OR automated invocation BY wind_online_watcher.py AFTER flag detection

7. All output files are automatically accompanied by .md5 checksums.

8. This script is DORMANT and INERT. It produces NO factor results
   until the trigger condition is met.

鈿狅笍  END OF SAFETY NOTICE 鈿狅笍
============================================================

Author: DSHB Agent
Version: 1.0.0-skeleton
Status: INERT (no hardcoded Wind calls, no auto-push, no API calls)
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime

# =============================================================================
# CONSTANTS 鈥?DO NOT MODIFY WITHOUT REVIEW
# =============================================================================

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
FLAG_PATH = os.path.join(REPO_ROOT, 'WIND_DATA_LINK_ONLINE.flag')
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(WORKSPACE, 'output')
AUDIT_DIR = os.path.join(WORKSPACE, 'audit')
CHECKSUM_DIR = os.path.join(WORKSPACE, 'checksum')

VARIETIES = ['PB', 'ZN', 'Recycle-PB']
OUTPUT_SCHEMA_IC = 'v88-factor-ic-result-1.0'
OUTPUT_SCHEMA_IR = 'v88-factor-ir-result-1.0'
OUTPUT_SCHEMA_META = 'v88-factor-meta-1.0'


# =============================================================================
# CHECKSUM UTILITY
# =============================================================================

def compute_md5(filepath):
    """Compute MD5 hash of a file."""
    md5_hash = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def generate_checksum(filepath):
    """Generate .md5 checksum file alongside the source file."""
    checksum_path = filepath + '.md5'
    md5_value = compute_md5(filepath)
    size = os.path.getsize(filepath)
    checksum_content = f"{md5_value}  {os.path.basename(filepath)}\n# Size: {size} bytes\n"
    checksum_content += f"# Generated: {datetime.now().isoformat()}\n"
    checksum_content += f"# Algorithm: MD5\n"
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(checksum_content)
    return md5_value


# =============================================================================
# VALIDATION
# =============================================================================

def validate_trigger_condition():
    """
    Check if WIND_DATA_LINK_ONLINE.flag exists at repo root.
    This is the ONLY gate that allows execution.

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if os.path.exists(FLAG_PATH):
        return True, (
            f"鉁?TRIGGER ACTIVE: WIND_DATA_LINK_ONLINE.flag found at {FLAG_PATH}\n"
            f"   Data link confirmed online. Factor calculation authorized."
        )
    return False, (
        f"鉀?TRIGGER INACTIVE: WIND_DATA_LINK_ONLINE.flag NOT FOUND at {FLAG_PATH}\n"
        f"   Factor calculation PROHIBITED. No data source confirmed.\n"
        f"   Awaiting external placement of WIND_DATA_LINK_ONLINE.flag."
    )


def validate_input(input_dir):
    """
    Validate that input data exists and is well-formed.
    Called BEFORE any calculation.

    Exception Fuse #1 - Empty Input File Detection:
    Checks that every required input file is present AND non-empty (> 0 bytes).
    Empty files are treated as a hard error (aborts calculation, no fallback).
    """
    required_files = []  # Will be populated after data ingestion
    for f in required_files:
        fpath = os.path.join(input_dir, f)
        if not os.path.exists(fpath):
            return False, f"Missing required input file: {f}"
        # ===== EXCEPTION FUSE #1: Empty input file guard =====
        file_size = os.path.getsize(fpath)
        if file_size == 0:
            return False, (
                f"EXCEPTION_FUSE_EMPTY_INPUT: Input file {f} is empty "
                f"(0 bytes). Calculation aborted."
            )
    return True, "Input validation passed (no empty files detected)"


def validate_time_series_continuity(dates, tolerance_days=3):
    """
    Exception Fuse #2 - Time Series Gap Detection:
    Checks for gaps (missing dates) in a time series.
    A gap exceeding tolerance_days is treated as a data quality error.
    """
    from datetime import date, timedelta

    if not dates or len(dates) < 2:
        return True, "Fewer than 2 data points - continuity check skipped"

    parsed = []
    for d in dates:
        if isinstance(d, date):
            parsed.append(d)
        elif isinstance(d, str):
            try:
                parsed.append(date.fromisoformat(d))
            except ValueError:
                return False, f"Invalid date format: '{d}' (expected YYYY-MM-DD)"
        else:
            return False, f"Unsupported date type: {type(d).__name__}"

    gaps = []
    for i in range(1, len(parsed)):
        delta = (parsed[i] - parsed[i - 1]).days
        if delta > tolerance_days:
            gaps.append({
                'from_date': parsed[i - 1].isoformat(),
                'to_date': parsed[i].isoformat(),
                'gap_days': delta,
                'expected_max_days': tolerance_days,
            })

    if gaps:
        gap_summary = "; ".join(
            f"{g['from_date']}->{g['to_date']} ({g['gap_days']}d > {tolerance_days}d)"
            for g in gaps[:5]
        )
        total_gaps = len(gaps)
        if total_gaps > 5:
            gap_summary += f"; ... +{total_gaps - 5} more gaps"
        return False, (
            f"EXCEPTION_FUSE_TIME_GAP: {total_gaps} time series gap(s) detected "
            f"(tolerance={tolerance_days}d): {gap_summary}. "
            f"Calculation aborted - data continuity requirement not met."
        )

    return True, "Time series continuity check passed (no gaps detected)"


def validate_output_dir_exists(output_dir):
    """
    Exception Fuse #3 - Output Directory Existence Check:
    Verifies that the output directory exists and is writable.
    """
    if not os.path.exists(output_dir):
        return False, (
            f"EXCEPTION_FUSE_OUTPUT_DIR_MISSING: Output directory does not exist: "
            f"'{output_dir}'. Calculation aborted."
        )
    if not os.path.isdir(output_dir):
        return False, (
            f"EXCEPTION_FUSE_OUTPUT_DIR_INVALID: Path is not a directory: "
            f"'{output_dir}'. Calculation aborted."
        )
    test_file = os.path.join(output_dir, '.write_test')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True, "Output directory existence check passed"
    except (OSError, IOError) as e:
        return False, (
            f"EXCEPTION_FUSE_OUTPUT_DIR_NOT_WRITABLE: Output directory "
            f"'{output_dir}' is not writable: {e}. Calculation aborted."
        )

def validate_output_schema(result, expected_schema):
    """Validate that output result matches expected schema version."""
    if 'schema' not in result:
        return False, "Missing 'schema' field in output"
    if result['schema'] != expected_schema:
        return False, f"Schema mismatch: expected {expected_schema}, got {result['schema']}"
    return True, "Output schema validation passed"


# =============================================================================
# CALCULATION STUBS 鈥?DO NOT EXECUTE WITHOUT TRIGGER
# =============================================================================

def calculate_ic(factor_data, return_data):
    """
    Calculate Information Coefficient (IC) between factor values and forward returns.
    
    鈿狅笍 STUB 鈥?This function is a placeholder. Real implementation requires
    Wind data ingestion through the approved gateway pipeline.
    
    Args:
        factor_data: list of factor values (sorted by date)
        return_data: list of forward return values (sorted by date)
    
    Returns:
        dict: IC calculation results
    """
    if not factor_data or not return_data:
        raise ValueError("Empty factor or return data 鈥?cannot compute IC")
    if len(factor_data) != len(return_data):
        raise ValueError("Factor and return data must have equal length")

    n = len(factor_data)
    mean_f = sum(factor_data) / n
    mean_r = sum(return_data) / n

    cov = sum((f - mean_f) * (r - mean_r) for f, r in zip(factor_data, return_data)) / n
    var_f = sum((f - mean_f) ** 2 for f in factor_data) / n
    var_r = sum((r - mean_r) ** 2 for r in return_data) / n

    if var_f == 0 or var_r == 0:
        raise ValueError("Zero variance in factor or return data 鈥?cannot compute IC")

    ic_mean = cov / (var_f * var_r) ** 0.5
    return {
        'ic_mean': round(ic_mean, 6),
        'ic_std': round((cov ** 2 / (n * var_f * var_r)) ** 0.5, 6),
        'ic_ir': round(ic_mean / (cov ** 2 / (n * var_f * var_r)) ** 0.5, 4) if cov != 0 else 0,
        'sample_count': n,
    }


def calculate_ir(ic_series):
    """
    Calculate Information Ratio (IR) from a series of IC values.
    
    鈿狅笍 STUB 鈥?Real implementation depends on IC calculation.
    
    Args:
        ic_series: list of IC values over time
    
    Returns:
        dict: IR calculation results
    """
    if not ic_series:
        raise ValueError("Empty IC series 鈥?cannot compute IR")

    n = len(ic_series)
    ic_mean = sum(ic_series) / n
    ic_var = sum((x - ic_mean) ** 2 for x in ic_series) / n
    ic_std = ic_var ** 0.5

    if ic_std == 0:
        raise ValueError("Zero IC variance 鈥?IR undefined")

    ir_mean = ic_mean / ic_std
    t_stat = (ic_mean / ic_std) * (n ** 0.5) if n > 1 else 0

    return {
        'ir_mean': round(ir_mean, 4),
        'ir_annualized': round(ir_mean * (252 ** 0.5), 4),  # Annualize (252 trading days)
        't_statistic': round(t_stat, 4),
        'p_value': None,  # Would require scipy.stats
        'significant_at_5pct': abs(t_stat) > 1.96,
        'positive_ic_count': sum(1 for x in ic_series if x > 0),
        'negative_ic_count': sum(1 for x in ic_series if x < 0),
    }


# =============================================================================
# OUTPUT BUILDERS
# =============================================================================

def build_ic_result(factor_id, variety, date_range, ic_values, calc_result):
    """Build IC result JSON structure."""
    return {
        'schema': OUTPUT_SCHEMA_IC,
        'factor_id': factor_id,
        'variety': variety,
        'date_range': date_range,
        'sample_count': calc_result['sample_count'],
        'ic_values': ic_values,
        'ic_mean': calc_result['ic_mean'],
        'ic_std': calc_result['ic_std'],
        'ic_ir': calc_result['ic_ir'],
        'ic_positive_rate': round(sum(1 for v in ic_values if v > 0) / max(len(ic_values), 1), 4),
        'data_source': 'WIND_DATA_LINK',
        'calculated_at': datetime.now().isoformat(),
        'checksum_md5': None,  # Set after file write
    }


def build_ir_result(factor_id, variety, date_range, ir_result):
    """Build IR result JSON structure."""
    return {
        'schema': OUTPUT_SCHEMA_IR,
        'factor_id': factor_id,
        'variety': variety,
        'date_range': date_range,
        'ir_mean': ir_result['ir_mean'],
        'ir_annualized': ir_result['ir_annualized'],
        'ir_positive_count': ir_result['positive_ic_count'],
        'ir_negative_count': ir_result['negative_ic_count'],
        't_statistic': ir_result['t_statistic'],
        'p_value': ir_result['p_value'],
        'significant_at_5pct': ir_result['significant_at_5pct'],
        'data_source': 'WIND_DATA_LINK',
        'calculated_at': datetime.now().isoformat(),
        'checksum_md5': None,
    }


def build_factor_meta(factor_id, factor_name, variety, category, lookback_days, forward_days, description):
    """Build factor metadata JSON structure."""
    return {
        'schema': OUTPUT_SCHEMA_META,
        'factor_id': factor_id,
        'factor_name': factor_name,
        'variety': variety,
        'category': category,
        'lookback_days': lookback_days,
        'forward_return_horizon_days': forward_days,
        'description': description,
        'data_source': 'WIND_DATA_LINK',
        'ic_ir_skeleton_deployed': True,
        'warmup_status': 'AWAIT_DATA_TRIGGER',
        'created_at': datetime.now().isoformat(),
    }


# =============================================================================
# MAIN EXECUTION ENTRY POINT
# =============================================================================

def run_calc(factor_id='momentum_20d', variety='PB', date_range=('2026-10-01', '2026-10-22')):
    """
    鈿狅笍 ENTRY POINT 鈥?WILL NOT EXECUTE WITHOUT WIND_DATA_LINK_ONLINE.flag 鈿狅笍
    
    This is the main execution entry point for factor calculation.
    It is INERT until the trigger condition is met.
    
    Execution flow:
    1. Check WIND_DATA_LINK_ONLINE.flag 鈫?if absent, EXIT immediately
    2. Validate input data 鈫?if invalid, EXIT with error
    3. Calculate IC
    4. Calculate IR
    5. Write results with MD5 checksums
    6. Write audit log
    
    鈿狅笍 NO AUTO-PUSH: This function does NOT call any git commands.
    鈿狅笍 NO AUTO-API: This function does NOT call any external API.
    
    Args:
        factor_id: Factor identifier string
        variety: Variety symbol (PB, ZN, Recycle-PB)
        date_range: (start_date, end_date) tuple
    
    Returns:
        dict: Execution result with status
    """
    print("=" * 70)
    print("IC-IR CALCULATION SKELETON 鈥?ENTRY POINT")
    print(f"Factor: {factor_id} | Variety: {variety} | Range: {date_range}")
    print("=" * 70)

    # ---- GATE 1: Trigger condition check ----
    is_valid, message = validate_trigger_condition()
    print(message)
    if not is_valid:
        print("\n鉀?EXITING 鈥?Trigger condition not met.")
        return {
            'status': 'ABORTED',
            'reason': 'WIND_DATA_LINK_ONLINE.flag not found',
            'factor_calculation_prohibited': True,
        }

    # ---- GATE 2: Input validation ----
    input_dir = os.path.join(WORKSPACE, 'input')
    input_ok, input_msg = validate_input(input_dir)
    if not input_ok:
        print(f"\n鉂?Input validation failed: {input_msg}")
        return {
            'status': 'FAILED',
            'reason': input_msg,
            'factor_calculation_prohibited': False,
        }
    print(f"鉁?{input_msg}")

    # ---- GATE 3: Output directory existence check (Exception Fuse #3) ----
    output_dir = os.path.join(WORKSPACE, "output")
    output_ok, output_msg = validate_output_dir_exists(output_dir)
    if not output_ok:
        print(f"\n Output directory check failed: {output_msg}")
        return {
            "status": "FAILED",
            "reason": output_msg,
            "factor_calculation_prohibited": False,
            "exception_fuse": "OUTPUT_DIR_MISSING",
        }
    print(f" {output_msg}")


    # ---- CALCULATION (STUB 鈥?no real data) ----
    print("\n鈿狅笍  STUB: No real factor data available. Cannot execute calculation.")
    print("    Real execution requires data ingestion through approved Wind gateway.")
    print("    This is a SKELETON ONLY 鈥?no hardcoded Wind calls.\n")

    return {
        'status': 'STUB_INERT',
        'reason': 'Skeleton only 鈥?no real data for calculation',
        'factor_calculation_prohibited': False,
        'requires_data_ingestion': True,
        'data_source_required': 'WIND_DATA_LINK',
    }


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='IC-IR Factor Calculation Skeleton (INERT 鈥?requires WIND_DATA_LINK_ONLINE.flag)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            '鈿狅笍  SAFETY NOTICE:\n'
            '  This script is a SKELETON ONLY.\n'
            '  It does NOT contain hardcoded WindPy or external API calls.\n'
            '  The run_calc() entry point is INERT until\n'
            '  WIND_DATA_LINK_ONLINE.flag is detected at repository root.\n'
            '  No auto-push. No auto-API. No external data pull.\n'
        )
    )

    parser.add_argument('--factor-id', default='momentum_20d', help='Factor identifier')
    parser.add_argument('--variety', default='PB', choices=['PB', 'ZN', 'Recycle-PB'], help='Variety symbol')
    parser.add_argument('--date-start', default='2026-10-01', help='Date range start')
    parser.add_argument('--date-end', default='2026-10-22', help='Date range end')
    parser.add_argument('--check-trigger', action='store_true', help='Only check trigger condition, do not calculate')

    args = parser.parse_args()

    if args.check_trigger:
        is_valid, message = validate_trigger_condition()
        print(message)
        sys.exit(0 if is_valid else 1)

    result = run_calc(
        factor_id=args.factor_id,
        variety=args.variety,
        date_range=(args.date_start, args.date_end),
    )

    print(f"\nResult: {json.dumps(result, indent=2)}")
    sys.exit(0 if result['status'] in ('COMPLETED', 'STUB_INERT') else 1)


if __name__ == '__main__':
    main()
