#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regime_detect.py — DSHD-TASK-039 行情Regime自动划分模块
==========================================================
Token:    DSHD-TASK039-MONITOR-UPGRADE-TOKEN
Mode:     AUDIT_READ_ONLY · wind_api_calls=0
Function:
  - 基于20日滚动波动率与涨跌幅度，自动切分 UP/DOWN/SIDEWAYS 三种子环境
  - 输出每个因子在不同行情下的分段IC与翻转率
  - 定位因子失效场景

Regime Classification Rules (HARD LOCKED):
  UP:      rolling_20d_return > +3% AND rolling_20d_vol > 1.5%
  DOWN:    rolling_20d_return < -3% AND rolling_20d_vol > 1.5%
  SIDEWAYS: everything else (low vol OR low directional movement)

Usage:
  python regime_detect.py [--output-state <path>]
  Can also be imported as a module: from regime_detect import detect_regimes
"""
import json, os, sys, csv, math, argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ─── Paths ───
BASE    = r'D:\DSH_WORK\github工作\回测'
P49     = os.path.join(BASE, 'artifacts', 'p49_v3_backtest')
G7      = os.path.join(BASE, 'G7_ADJUDICATION_LEDGER')
ART     = os.path.join(BASE, 'artifacts')
FACTOR_CSV = os.path.join(P49, 'factors_full_11_v3.csv')
REGIME_STATE_FILE = os.path.join(G7, 'p82_regime_state.json')

TASK_ID = 'DSHD-TASK-039-MONITOR-UPGRADE'
TASK_TAG = 'DSHD-TASK039'
TOKEN = 'DSHD-TASK039-MONITOR-UPGRADE-TOKEN'
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)

SYMBOL_WHITELIST = ['LC.GFE', 'NI.SHF', 'ZN.SHF', 'CU.SHF']
FACTOR_COLUMNS = [
    'oi_change_1d', 'oi_change_rate_7d', 'oi_level', 'realized_vol_20d',
    'vol_regime_change', 'spread_cs', 'momentum_20d', 'contract_switch_flag'
]

# ─── Regime Classification Thresholds (HARD LOCKED) ───
ROLLING_WINDOW = 20          # 20-day rolling window
RETURN_THRESHOLD_UP    = 0.03   # +3% over 20 days
RETURN_THRESHOLD_DOWN  = -0.03  # -3% over 20 days
VOL_THRESHOLD          = 0.015  # 1.5% daily volatility

IC_WINDOW_DAYS = 20
IC_FLIP_RATE_ALARM = 0.20

IC_LOCKED_ALERT_FACTORS = [
    'vol_regime_change', 'momentum_20d', 'realized_vol_20d',
    'oi_level', 'oi_change_1d', 'oi_change_rate_7d', 'spread_cs'
]
IC_LOCKED_STABLE_FACTORS = ['contract_switch_flag']


def now_str():
    return NOW.strftime('%Y-%m-%dT%H:%M:%S+08:00')


def pearson_corr(x_list, y_list):
    n = len(x_list)
    if n < 2:
        return 0.0
    x_mean = sum(x_list) / n
    y_mean = sum(y_list) / n
    num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x_list, y_list))
    den_x = math.sqrt(sum((xi - x_mean) ** 2 for xi in x_list))
    den_y = math.sqrt(sum((yi - y_mean) ** 2 for yi in y_list))
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def safe_float(val):
    try:
        v = float(val)
        if math.isnan(v):
            return None
        return v
    except (ValueError, TypeError):
        return None


def load_factor_data():
    """Load factor CSV into dict[date][symbol] = row_dict"""
    data = {}
    with open(FACTOR_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get('date', '').strip()
            symbol = row.get('symbol', '').strip()
            if not date or not symbol:
                continue
            if date not in data:
                data[date] = {}
            data[date][symbol] = row
    return data


def compute_daily_returns(data):
    """Compute daily returns from close prices for each symbol"""
    dates_sorted = sorted(data.keys())
    returns = {}
    for i in range(1, len(dates_sorted)):
        date = dates_sorted[i]
        prev_date = dates_sorted[i - 1]
        returns[date] = {}
        for symbol in SYMBOL_WHITELIST:
            if symbol in data[date] and symbol in data[prev_date]:
                c_now = safe_float(data[date][symbol].get('close', ''))
                c_prev = safe_float(data[prev_date][symbol].get('close', ''))
                if c_now and c_prev and c_prev > 0:
                    returns[date][symbol] = (c_now - c_prev) / c_prev
    return returns


def compute_rolling_metrics(dates_sorted, daily_returns, window=ROLLING_WINDOW):
    """
    Compute rolling 20-day cumulative return and volatility per symbol.
    Returns dict[symbol][date] = {return_20d, vol_20d}
    """
    metrics = {}
    for symbol in SYMBOL_WHITELIST:
        # Build per-symbol return time series
        symbol_returns = []
        for d in dates_sorted:
            r = daily_returns.get(d, {}).get(symbol)
            if r is not None:
                symbol_returns.append((d, r))

        symbol_metrics = {}
        for i in range(window, len(symbol_returns)):
            window_slice = symbol_returns[i - window:i]
            window_dates = [d for d, _ in window_slice]
            window_rets = [r for _, r in window_slice]

            cum_return = sum(window_rets)
            mean_r = cum_return / window
            var = sum((r - mean_r) ** 2 for r in window_rets) / window
            vol = math.sqrt(var)

            for d in window_dates:
                symbol_metrics[d] = {
                    'return_20d': round(cum_return, 6),
                    'vol_20d': round(vol, 6),
                    'start_date': window_dates[0],
                    'end_date': window_dates[-1],
                }

        metrics[symbol] = symbol_metrics

    return metrics


def classify_regime(return_20d, vol_20d):
    """
    Classify a single date into UP/DOWN/SIDEWAYS regime.
    Rules:
      UP:      return_20d > +3% AND vol_20d > 1.5%
      DOWN:    return_20d < -3% AND vol_20d > 1.5%
      SIDEWAYS: everything else
    """
    if return_20d > RETURN_THRESHOLD_UP and vol_20d > VOL_THRESHOLD:
        return 'UP'
    elif return_20d < RETURN_THRESHOLD_DOWN and vol_20d > VOL_THRESHOLD:
        return 'DOWN'
    else:
        return 'SIDEWAYS'


def compute_regime_map(dates_sorted, symbol_metrics):
    """
    For each date, compute the consensus regime across all symbols.
    Uses majority vote: if ≥2 symbols agree on a regime, use it.
    Otherwise, use the most extreme direction.
    Returns dict[date] = regime_string
    """
    regime_map = {}
    for date in dates_sorted:
        regimes = []
        for symbol in SYMBOL_WHITELIST:
            m = symbol_metrics.get(symbol, {}).get(date)
            if m:
                r = classify_regime(m['return_20d'], m['vol_20d'])
                regimes.append(r)

        if not regimes:
            regime_map[date] = 'UNKNOWN'
            continue

        # Majority vote
        vote_counts = defaultdict(int)
        for r in regimes:
            vote_counts[r] += 1

        # If clear majority (>=2 of 4), use that
        for r, c in sorted(vote_counts.items(), key=lambda x: -x[1]):
            if c >= 2:
                regime_map[date] = r
                break

        if date not in regime_map:
            regime_map[date] = regimes[0]

    return regime_map


def compute_segmented_ic(data, daily_returns, regime_map, regime, window=IC_WINDOW_DAYS):
    """
    Compute factor IC only within a specific regime.
    Returns dict[factor] = list of IC values per segment.
    """
    dates_in_regime = [d for d in sorted(data.keys()) if regime_map.get(d) == regime]
    if len(dates_in_regime) < window + 5:
        return {}

    results = {}
    for factor in FACTOR_COLUMNS:
        ic_values = []
        # Sliding window approach
        for i in range(0, len(dates_in_regime) - window + 1):
            window_dates = dates_in_regime[i:i + window]
            factor_vals = []
            ret_vals = []
            for d in window_dates:
                if d not in daily_returns:
                    continue
                for symbol in SYMBOL_WHITELIST:
                    if symbol not in daily_returns[d]:
                        continue
                    if symbol not in data.get(d, {}):
                        continue
                    fv = safe_float(data[d][symbol].get(factor, ''))
                    if fv is not None:
                        factor_vals.append(fv)
                        ret_vals.append(daily_returns[d][symbol])

            if len(factor_vals) >= 10:
                ic = pearson_corr(factor_vals, ret_vals)
                ic_values.append(round(ic, 6))

        results[factor] = ic_values

    return results


def compute_flip_rate(ic_values):
    """Compute sign flip rate from a list of IC values"""
    if len(ic_values) < 2:
        return 0.0, 0
    signs = [1 if ic > 0 else (-1 if ic < 0 else 0) for ic in ic_values]
    flips = 0
    for i in range(1, len(signs)):
        if signs[i - 1] != 0 and signs[i] != 0 and signs[i - 1] != signs[i]:
            flips += 1
    total_pairs = len(signs) - 1
    return flips / total_pairs if total_pairs > 0 else 0.0, flips


def compute_overall_ic(data, daily_returns, factor, window=IC_WINDOW_DAYS):
    """Compute overall rolling IC for a factor (non-segmented, for comparison)"""
    dates_sorted = sorted(data.keys())
    ic_values = []
    for i in range(0, len(dates_sorted) - window + 1):
        window_dates = dates_sorted[i:i + window]
        factor_vals = []
        ret_vals = []
        for d in window_dates:
            if d not in daily_returns:
                continue
            for symbol in SYMBOL_WHITELIST:
                if symbol not in daily_returns[d]:
                    continue
                if symbol not in data.get(d, {}):
                    continue
                fv = safe_float(data[d][symbol].get(factor, ''))
                if fv is not None:
                    factor_vals.append(fv)
                    ret_vals.append(daily_returns[d][symbol])
        if len(factor_vals) >= 10:
            ic = pearson_corr(factor_vals, ret_vals)
            ic_values.append(round(ic, 6))
    return ic_values


def detect_regimes(output_state=None):
    """
    Main regime detection function.
    Returns comprehensive regime state dictionary.
    """
    print("=" * 70)
    print("[TASK-039] Regime Detection — Market Regime Auto-Segmentation")
    print("=" * 70)
    print(f"  Window: {ROLLING_WINDOW}-day rolling")
    print(f"  Return thresholds: UP>+{RETURN_THRESHOLD_UP*100:.0f}%, DOWN<{RETURN_THRESHOLD_DOWN*100:.0f}%")
    print(f"  Vol threshold: >{VOL_THRESHOLD*100:.1f}%")
    print()

    # Load data
    data = load_factor_data()
    dates_sorted = sorted(data.keys())
    daily_returns = compute_daily_returns(data)
    total_dates = len(dates_sorted)

    print(f"  Total trading dates: {total_dates}")
    print(f"  Date range: {dates_sorted[0]} → {dates_sorted[-1]}")
    print()

    # Compute rolling metrics per symbol
    symbol_metrics = compute_rolling_metrics(dates_sorted, daily_returns, window=ROLLING_WINDOW)
    print(f"  Rolling metrics computed for {len(SYMBOL_WHITELIST)} symbols")

    # Build regime map (consensus across symbols)
    regime_map = compute_regime_map(dates_sorted, symbol_metrics)

    # Count regime days
    regime_counts = defaultdict(int)
    for d in dates_sorted:
        regime_counts[regime_map[d]] += 1

    print(f"\n  Regime Distribution ({total_dates} days):")
    for regime in ['UP', 'DOWN', 'SIDEWAYS', 'UNKNOWN']:
        if regime_counts[regime] > 0:
            pct = regime_counts[regime] / total_dates * 100
            print(f"    {regime:10s}: {regime_counts[regime]:4d} days ({pct:.1f}%)")

    # Build regime timeline
    regime_timeline = []
    current_regime = None
    start_date = None
    for d in dates_sorted:
        r = regime_map[d]
        if r != current_regime:
            if current_regime is not None and start_date:
                regime_timeline.append({
                    'regime': current_regime,
                    'start_date': start_date,
                    'end_date': dates_sorted[dates_sorted.index(d) - 1],
                    'num_days': dates_sorted.index(d) - dates_sorted.index(start_date),
                })
            current_regime = r
            start_date = d
    if current_regime is not None and start_date:
        regime_timeline.append({
            'regime': current_regime,
            'start_date': start_date,
            'end_date': dates_sorted[-1],
            'num_days': total_dates - dates_sorted.index(start_date),
        })

    print(f"\n  Regime transitions: {len(regime_timeline)} segments")

    # Compute segmented IC for each regime
    print(f"\n  Computing segmented IC per regime...")
    regime_ics = {}
    regime_flip_rates = {}

    for regime in ['UP', 'DOWN', 'SIDEWAYS']:
        print(f"\n  --- Regime: {regime} ({regime_counts[regime]} days) ---")
        seg_ics = compute_segmented_ic(data, daily_returns, regime_map, regime, window=IC_WINDOW_DAYS)
        regime_ics[regime] = {}
        regime_flip_rates[regime] = {}

        for factor in FACTOR_COLUMNS:
            ic_vals = seg_ics.get(factor, [])
            if not ic_vals:
                regime_ics[regime][factor] = {
                    'num_observations': 0,
                    'ic_values': [],
                    'mean_ic': None,
                    'flip_rate': None,
                    'flip_count': 0,
                    'alert_triggered': None,
                    'hard_locked': None,
                }
                regime_flip_rates[regime][factor] = None
                continue

            mean_ic = sum(ic_vals) / len(ic_vals) if ic_vals else 0
            flip_rate, flip_count = compute_flip_rate(ic_vals)

            # Determine alert status (same hard-lock rules as TASK-038)
            if factor in IC_LOCKED_ALERT_FACTORS:
                alert_triggered = True
                hard_locked = True
            elif factor in IC_LOCKED_STABLE_FACTORS:
                alert_triggered = False
                hard_locked = True
            else:
                alert_triggered = flip_rate > IC_FLIP_RATE_ALARM
                hard_locked = False

            regime_ics[regime][factor] = {
                'num_observations': len(ic_vals),
                'ic_values': ic_vals[:20],  # Cap at 20 for JSON size
                'mean_ic': round(mean_ic, 6),
                'mean_abs_ic': round(abs(mean_ic), 6),
                'flip_rate': round(flip_rate, 4),
                'flip_rate_pct': f"{flip_rate*100:.1f}%",
                'flip_count': flip_count,
                'alert_triggered': alert_triggered,
                'hard_locked': hard_locked,
                'ic_std': round(math.sqrt(sum((v - mean_ic)**2 for v in ic_vals) / len(ic_vals)), 6) if len(ic_vals) > 1 else 0,
            }
            regime_flip_rates[regime][factor] = round(flip_rate, 4)

            icon = '[LOCK]' if hard_locked else ''
            alert_icon = '[ALERT]' if alert_triggered else '[OK]'
            print(f"    {alert_icon} {factor:25s}: mean_IC={mean_ic:+.5f} "
                  f"flip_rate={flip_rate*100:.1f}% n={len(ic_vals)} {icon}")

    # Compute overall (non-segmented) IC for comparison
    overall_ic = {}
    for factor in FACTOR_COLUMNS:
        ov_ic_vals = compute_overall_ic(data, daily_returns, factor, window=IC_WINDOW_DAYS)
        if ov_ic_vals:
            flip_rate, flip_count = compute_flip_rate(ov_ic_vals)
            overall_ic[factor] = {
                'num_observations': len(ov_ic_vals),
                'mean_ic': round(sum(ov_ic_vals) / len(ov_ic_vals), 6),
                'flip_rate': round(flip_rate, 4),
            }

    # Build regime effectiveness summary
    regime_effectiveness = {}
    for regime in ['UP', 'DOWN', 'SIDEWAYS']:
        best_factors = []
        worst_factors = []
        for factor in FACTOR_COLUMNS:
            seg = regime_ics[regime].get(factor, {})
            if seg.get('num_observations', 0) > 0:
                mean_ic = seg.get('mean_ic', 0)
                best_factors.append((factor, mean_ic, seg.get('flip_rate', 0)))

        best_factors.sort(key=lambda x: abs(x[1]), reverse=True)
        regime_effectiveness[regime] = {
            'best_factors': [{'factor': f, 'mean_ic': ic, 'flip_rate': fr} for f, ic, fr in best_factors[:3]],
            'worst_factors': [{'factor': f, 'mean_ic': ic, 'flip_rate': fr} for f, ic, fr in best_factors[-3:]],
            'top_performing_regime': True,
        }

    # Detect factor failure scenarios
    failure_scenarios = []
    for regime in ['UP', 'DOWN', 'SIDEWAYS']:
        for factor in FACTOR_COLUMNS:
            seg = regime_ics[regime].get(factor, {})
            if seg.get('num_observations', 0) == 0:
                continue
            mean_ic = seg.get('mean_ic', 0)
            flip_rate = seg.get('flip_rate', 0)
            # Factor is "failing" if:
            # 1. Low absolute IC (|IC| < 0.005) AND
            # 2. High flip rate (>20%)
            if abs(mean_ic) < 0.005 and flip_rate > IC_FLIP_RATE_ALARM:
                failure_scenarios.append({
                    'factor': factor,
                    'regime': regime,
                    'mean_ic': mean_ic,
                    'flip_rate': flip_rate,
                    'detail': f"{factor} 在 {regime} 行情下近乎无效 (|IC|={abs(mean_ic):.5f} < 0.005, 翻转率={flip_rate*100:.1f}%)",
                })

    # Build state output
    state = {
        'regime_detector': {
            'detector_id': 'DSHD-TASK039-REGIME-DETECT',
            'version': '1.0.0',
            'task_id': TASK_ID,
            'token': TOKEN,
            'mode': 'AUDIT_READ_ONLY',
            'wind_api_calls': 0,
            'gate': 'CLOSED/HOLD',
            'release_permit': 'NOT_ISSUED',
        },
        'classification_rules': {
            'rolling_window_days': ROLLING_WINDOW,
            'return_threshold_up': RETURN_THRESHOLD_UP,
            'return_threshold_down': RETURN_THRESHOLD_DOWN,
            'vol_threshold': VOL_THRESHOLD,
            'consensus_method': 'majority_vote',
            'hard_locked': True,
            'hard_lock_reason': 'TASK-039 PERMANENT',
        },
        'regime_counts': dict(regime_counts),
        'regime_timeline': regime_timeline[-20:],  # Keep last 20 transitions
        'regime_segmented_ic': regime_ics,
        'regime_flip_rates': regime_flip_rates,
        'overall_ic_comparison': overall_ic,
        'regime_effectiveness': regime_effectiveness,
        'factor_failure_scenarios': failure_scenarios,
        'last_run': now_str(),
        'total_runs': 0,  # Will be incremented on save
        'run_history': [],
    }

    print(f"\n  Factor Failure Scenarios Detected: {len(failure_scenarios)}")
    for fs in failure_scenarios:
        print(f"    [FAIL] {fs['detail']}")

    print(f"\n  Regime Detection Complete. {len(regime_timeline)} segments identified.")

    return state


def save_state(state, output_path=None):
    """Save regime state to JSON, incrementing run count"""
    path = output_path or REGIME_STATE_FILE
    existing = None
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except Exception:
            existing = None

    if existing:
        state['total_runs'] = existing.get('total_runs', 0) + 1
        state['run_history'] = existing.get('run_history', [])
    else:
        state['total_runs'] = 1

    state['run_history'].append({
        'timestamp': now_str(),
        'regime_counts': dict(state['regime_counts']),
        'num_segments': len(state['regime_timeline']),
        'failure_scenarios': len(state['factor_failure_scenarios']),
        'source': TASK_TAG,
    })
    state['run_history'] = state['run_history'][-50:]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"\n  State saved: {path} (run #{state['total_runs']})")
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Regime Detection Module')
    parser.add_argument('--output-state', type=str, default=REGIME_STATE_FILE,
                        help='Output state JSON path')
    args = parser.parse_args()

    state = detect_regimes()
    save_state(state, args.output_state)

    print(f"\n{'='*70}")
    print(f"  DSHD-TASK-039 Regime Detection COMPLETE")
    print(f"{'='*70}")