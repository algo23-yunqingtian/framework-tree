#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P81 Factor Pool Stability Pre-Check Hook
==========================================
Task: DSHD-P81-AUDIT-FACTOR-STABILITY
Token: DSHD-P81-AUDIT-FACTOR-TOKEN
Purpose: 因子池稳定性校验钩子 - 任何因子配置变更时自动触发稳定性预审告警

Usage:
  python p81_factor_stability_hook.py [--mode check|full] [--verbose]

Modes:
  check - 快速检查（30秒内）：读取现有制品，验证因子池稳定性状态
  full  - 完整检查（含IC重算）：复现3段时序IC，与基准值对比

Returns (JSON):
  {
    "hook_id": "P81-FACTOR-STABILITY-HOOK",
    "status": "PASS|WARN|FAIL",
    "timestamp": "...",
    "checks": [...],
    "alerts": [...]
  }

Red lines:
  - wind_api_calls = 0
  - Gate = CLOSED/HOLD
  - Release = NOT_ISSUED
  - Read-only: 不修改任何因子配置或回测结果
"""
import json, os, sys, hashlib, argparse
from datetime import datetime, timezone, timedelta

BASE = r'D:\DSH_WORK\github工作\回测'
P49 = os.path.join(BASE, 'artifacts', 'p49_v3_backtest')
ARTIFACTS = os.path.join(BASE, 'artifacts')
AUDIT_LEDGER = os.path.join(BASE, 'tracking_monitor_audit.jsonl')

HOOK_ID = 'P81-FACTOR-STABILITY-HOOK'
TASK_ID = 'DSHD-P81-AUDIT-FACTOR-STABILITY'
TOKEN = 'DSHD-P81-AUDIT-FACTOR-TOKEN'

# Known factor stability baseline (from audit)
FACTOR_STABILITY_BASELINE = {
    'oi_change_1d':       {'risk': 'HIGH', 'sign_stable': False, 'segment_ics': [0.013486, -0.032230, 0.021984]},
    'oi_change_rate_7d':  {'risk': 'HIGH', 'sign_stable': False, 'segment_ics': [0.001701, -0.017511, 0.000049]},
    'oi_level':           {'risk': 'HIGH', 'sign_stable': False, 'segment_ics': [0.016006, 0.104693, -0.105001]},
    'realized_vol_20d':   {'risk': 'MEDIUM', 'sign_stable': False, 'segment_ics': [0.023115, 0.050423, -0.062836]},
}

# Factor config files to monitor
MONITORED_FILES = [
    ('factor_enable_config.json', os.path.join(P49, 'factor_enable_config.json')),
    ('factor_weight.json', os.path.join(P49, 'factor_weight.json')),
    ('weighted_backtest_metrics.json', os.path.join(P49, 'weighted_backtest_metrics.json')),
    ('factor_stability_report.md', os.path.join(P49, 'factor_stability_report.md')),
    ('factors_full_11_v3.csv', os.path.join(P49, 'factors_full_11_v3.csv')),
    ('run_v3_factor_weight.py', os.path.join(P49, 'run_v3_factor_weight.py')),
]

# Known good SHAs (from audit snapshot + WEIGHT-FIX concurrent change)
KNOWN_SHAS = {
    'factor_weight.json': '14a99ffc6b5e3975',
    'factor_enable_config.json': 'b2e5464b4fed2109',
    'weighted_backtest_metrics.json': 'a7e5b042ca1dd296',
    'factor_stability_report.md': '5df308c8de635728',
    'factors_full_11_v3.csv': 'dd6674bb323ce6f5',
    'run_v3_factor_weight.py': 'a2e4ec2d24228c7b',
}

# Baseline SHA history (for change detection)
SHA_HISTORY = {
    'factor_weight.json': {'original': 'c39467b73321078d', 'weight_fix': '14a99ffc6b5e3975'},
    'factor_enable_config.json': {'original': '5151949a62115280', 'weight_fix': 'b2e5464b4fed2109'},
    'weighted_backtest_metrics.json': {'original': '6f20a9fd161ae076', 'weight_fix': 'a7e5b042ca1dd296'},
    'factor_stability_report.md': {'original': '5f24590dc726d0e7', 'weight_fix': '5df308c8de635728'},
}


def compute_sha256(filepath):
    """Compute SHA256 of a file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_file_integrity():
    """Check if monitored files have been modified since audit."""
    checks = []
    alerts = []
    
    for label, filepath in MONITORED_FILES:
        current_sha = compute_sha256(filepath)
        known_sha = KNOWN_SHAS.get(label)
        
        if current_sha is None:
            checks.append({
                'file': label,
                'status': 'MISSING',
                'current_sha': None,
                'known_sha': known_sha
            })
            alerts.append({
                'level': 'WARN',
                'message': f'{label} is missing'
            })
        elif known_sha and current_sha[:16] != known_sha:
            checks.append({
                'file': label,
                'status': 'MODIFIED',
                'current_sha': current_sha,
                'known_sha': known_sha,
                'size_bytes': os.path.getsize(filepath)
            })
            alerts.append({
                'level': 'WARN',
                'message': f'{label} has been modified since audit. '
                           f'Old: {known_sha}... -> New: {current_sha[:16]}...'
            })
        else:
            checks.append({
                'file': label,
                'status': 'UNCHANGED',
                'current_sha': current_sha,
                'known_sha': known_sha
            })
    
    return checks, alerts


def check_factor_enable_config():
    """Check factor enable config for stability-related changes."""
    filepath = os.path.join(P49, 'factor_enable_config.json')
    if not os.path.exists(filepath):
        return {'status': 'MISSING', 'detail': 'factor_enable_config.json not found'}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    checks = []
    alerts = []
    
    # Check if OI factors are still in conditional_pool_switch
    conditional = config.get('factor_layers', {}).get('conditional_pool_switch', {})
    conditional_factors = set(conditional.get('factors', []))
    expected_oi = {'oi_change_1d', 'oi_change_rate_7d', 'oi_level'}
    
    if conditional_factors == expected_oi:
        checks.append({'check': 'oi_factors_conditional', 'status': 'OK'})
    else:
        checks.append({'check': 'oi_factors_conditional', 'status': 'CHANGED',
                       'expected': list(expected_oi), 'actual': list(conditional_factors)})
        alerts.append({'level': 'WARN', 'message': f'OI factor pool changed: {conditional_factors}'})
    
    # Check if always_enabled factors are correct
    always = config.get('factor_layers', {}).get('always_enabled', {})
    always_factors = set(always.get('factors', []))
    if always_factors == {'realized_vol_20d'}:
        checks.append({'check': 'vol_factor_always_enabled', 'status': 'OK'})
    else:
        checks.append({'check': 'vol_factor_always_enabled', 'status': 'CHANGED',
                       'expected': ['realized_vol_20d'], 'actual': list(always_factors)})
        alerts.append({'level': 'WARN', 'message': f'Always-enabled factors changed: {always_factors}'})
    
    return {
        'status': 'PASS' if not alerts else 'WARN',
        'checks': checks,
        'alerts': alerts,
        'total_factors_4_symbol': config.get('total_factors_4_symbol', 0),
        'total_factors_9_symbol': config.get('total_factors_9_symbol', 0),
    }


def check_ic_weight_config():
    """Check IC weight config for stability concerns."""
    filepath = os.path.join(P49, 'factor_weight.json')
    if not os.path.exists(filepath):
        return {'status': 'MISSING', 'detail': 'factor_weight.json not found'}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    alerts = []
    ic_values = config.get('ic_values', {})
    effective_weights = config.get('effective_weights', {})
    
    # Check for IC method: is it using TS IC or CSV IC?
    method = config.get('weighting_method', 'unknown')
    ic_source = 'unknown'
    
    # Known CSV IC values for comparison
    csv_ic_4symbol = {
        'spread_cs': -0.064899,
        'realized_vol_20d': 0.053897,
        'oi_change_rate_7d': 0.044248,
        'oi_level': 0.038378,
        'momentum_20d': 0.03706,
        'vol_regime_change': 0.011865,
        'oi_change_1d': 0.00616,
        'contract_switch_flag': 0.0,
    }
    
    # Detect if using TS IC or CSV IC
    for fname, csv_val in csv_ic_4symbol.items():
        ts_val = ic_values.get(fname, None)
        if ts_val is not None and abs(ts_val - csv_val) > 0.001:
            ic_source = 'TS_IC'  # Using compute_per_symbol_ts_ic
            break
    
    if ic_source == 'TS_IC':
        alerts.append({
            'level': 'WARN',
            'message': 'IC weight config uses TS_IC (compute_per_symbol_ts_ic) instead of CSV_IC. '
                       'This causes spread_cs to dominate with negative weight.',
            'method': method,
            'ic_source': ic_source
        })
    
    # Check for dominant negative weight
    if effective_weights:
        max_abs_weight = max(abs(w) for w in effective_weights.values())
        max_weight_factor = max(effective_weights, key=lambda k: abs(effective_weights[k]))
        if effective_weights[max_weight_factor] < -0.15:
            alerts.append({
                'level': 'WARN',
                'message': f'Dominant negative weight: {max_weight_factor} = {effective_weights[max_weight_factor]:+.4f}',
                'factor': max_weight_factor,
                'weight': effective_weights[max_weight_factor]
            })
    
    return {
        'status': 'PASS' if not alerts else 'WARN',
        'method': method,
        'ic_source': ic_source,
        'ic_values': ic_values,
        'alerts': alerts
    }


def run_full_ic_recompute():
    """Full IC recomputation for all monitored factors (read-only)."""
    try:
        import pandas as pd
        import numpy as np
        from scipy.stats import pearsonr
    except ImportError:
        return {'status': 'SKIP', 'detail': 'pandas/numpy/scipy not available'}
    
    csv_path = os.path.join(P49, 'factors_full_11_v3.csv')
    if not os.path.exists(csv_path):
        return {'status': 'MISSING', 'detail': 'factors_full_11_v3.csv not found'}
    
    df = pd.read_csv(csv_path)
    SYMBOLS = ['LC.GFE', 'NI.SHF', 'ZN.SHF', 'CU.SHF']
    
    df_sub = df[df['symbol'].isin(SYMBOLS)].copy()
    df_sub = df_sub.sort_values(['symbol', 'date']).copy()
    df_sub['date'] = pd.to_datetime(df_sub['date'])
    df_sub['next_return'] = df_sub.groupby('symbol')['close'].pct_change().shift(-1)
    
    all_dates = sorted(df_sub['date'].unique())
    n_dates = len(all_dates)
    segment_size = n_dates // 3
    
    results = {}
    for factor_name, baseline in FACTOR_STABILITY_BASELINE.items():
        segment_ics = []
        for i in range(3):
            start = i * segment_size
            end = start + segment_size if i < 2 else n_dates
            seg_dates = all_dates[start:end]
            seg_start = pd.Timestamp(seg_dates[0]).date()
            seg_end = pd.Timestamp(seg_dates[-1]).date()
            
            mask = (df_sub['date'] >= pd.Timestamp(seg_start)) & (df_sub['date'] <= pd.Timestamp(seg_end))
            seg_df = df_sub[mask]
            valid = seg_df[[factor_name, 'next_return']].dropna()
            
            if len(valid) < 10:
                segment_ics.append(0.0)
            else:
                try:
                    ic_val, _ = pearsonr(valid[factor_name].values, valid['next_return'].values)
                    segment_ics.append(round(float(ic_val), 6))
                except Exception:
                    segment_ics.append(0.0)
        
        # Check sign stability
        signs = [np.sign(ic) for ic in segment_ics if abs(ic) > 1e-6]
        sign_stable = len(set(signs)) == 1 if signs else None
        
        # Compare with baseline
        baseline_match = all(
            abs(segment_ics[i] - baseline['segment_ics'][i]) < 0.0001
            for i in range(min(len(segment_ics), 3))
        )
        
        results[factor_name] = {
            'segment_ics': segment_ics,
            'sign_stable': sign_stable,
            'baseline_segment_ics': baseline['segment_ics'],
            'baseline_match': baseline_match,
            'risk': baseline['risk'],
        }
    
    return {
        'status': 'PASS' if all(r['baseline_match'] for r in results.values()) else 'WARN',
        'method': '3-segment Pearson IC recomputation',
        'factors': results,
    }


def write_audit_event(status, alerts):
    """Write audit event to tracking_monitor_audit.jsonl."""
    event = {
        'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'agent': 'DSHD-P81-AUDIT-FACTOR',
        'event': HOOK_ID,
        'task_id': TASK_ID,
        'token': TOKEN,
        'mode': 'AUDIT_READ_ONLY',
        'wind_api_calls': 0,
        'gate': 'CLOSED/HOLD',
        'release': 'NOT_ISSUED',
        'status': status,
        'alerts': alerts,
        'intervention': 'NONE',
        'data': {
            'hook_id': HOOK_ID,
            'monitoring_factors': list(FACTOR_STABILITY_BASELINE.keys()),
            'known_sha_checked': len(KNOWN_SHAS),
            'total_monitored_files': len(MONITORED_FILES),
        }
    }
    
    try:
        with open(AUDIT_LEDGER, 'a', encoding='utf-8-sig') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        print(f'Failed to write audit event: {e}', file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description='P81 Factor Pool Stability Pre-Check Hook')
    parser.add_argument('--mode', choices=['check', 'full'], default='check',
                        help='check=quick integrity check, full=include IC recomputation')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--no-audit', action='store_true',
                        help='Skip writing audit event')
    args = parser.parse_args()
    
    all_alerts = []
    
    # 1. File integrity check
    integrity_checks, integrity_alerts = check_file_integrity()
    all_alerts.extend(integrity_alerts)
    
    # 2. Factor config check
    config_check = check_factor_enable_config()
    if isinstance(config_check, dict) and 'alerts' in config_check:
        all_alerts.extend(config_check['alerts'])
    
    # 3. IC weight config check
    ic_check = check_ic_weight_config()
    if isinstance(ic_check, dict) and 'alerts' in ic_check:
        all_alerts.extend(ic_check['alerts'])
    
    # 4. Full IC recompute (optional)
    ic_recompute = None
    if args.mode == 'full':
        ic_recompute = run_full_ic_recompute()
    
    # Determine overall status
    has_warn = any(a['level'] == 'WARN' for a in all_alerts)
    has_fail = any(a['level'] == 'FAIL' for a in all_alerts)
    
    if has_fail:
        overall_status = 'FAIL'
    elif has_warn:
        overall_status = 'WARN'
    else:
        overall_status = 'PASS'
    
    result = {
        'hook_id': HOOK_ID,
        'task_id': TASK_ID,
        'token': TOKEN,
        'status': overall_status,
        'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'mode': 'AUDIT_READ_ONLY',
        'wind_api_calls': 0,
        'gate': 'CLOSED/HOLD',
        'release': 'NOT_ISSUED',
        'intervention': 'NONE',
        'checks': {
            'file_integrity': integrity_checks,
            'factor_enable_config': config_check,
            'ic_weight_config': ic_check,
            'ic_recompute': ic_recompute,
        },
        'alerts': all_alerts,
    }
    
    # Write audit event
    if not args.no_audit:
        write_audit_event(overall_status, all_alerts)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if overall_status == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
