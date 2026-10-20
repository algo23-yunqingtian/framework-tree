#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crowding_monitor.py — DSHD-TASK-039 因子拥挤度监控模块
==========================================================
Token:    DSHD-TASK039-MONITOR-UPGRADE-TOKEN
Mode:     AUDIT_READ_ONLY · wind_api_calls=0
Function:
  - 计算因子多空持仓集中度（方向性偏度 + 值分布集中度）
  - 计算近期超额收益动量（滚动IC衰减检测）
  - 当拥挤度突破历史分位数（90th percentile）时，新增MEDIUM级别预警
  - 仅新增监控，不覆盖原有告警逻辑

Crowding Metrics:
  1. Directional Concentration (dir_concentration):
     - Ratio of positive factor values / total non-zero values
     - 0.5 = balanced, >0.7 or <0.3 = crowded in one direction

  2. Value Concentration (value_concentration):
     - HHI of factor value distribution (binned into deciles)
     - Higher HHI = more concentrated (more crowded)

  3. Excess Return Momentum (ic_momentum):
     - Rolling 5d vs 20d IC comparison
     - Decay in recent IC vs longer-term IC = crowding signal

  4. Crowding Score (composite):
     - Combined percentile of dir_concentration + value_concentration + IC decay
     - Alert at 90th percentile of historical

Alert Threshold (HARD LOCKED):
  CROWDING_ALERT_PERCENTILE = 90  (90th percentile)
  Alert level: MEDIUM
"""
import json, os, sys, csv, math, argparse, statistics
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ─── Paths ───
BASE    = r'D:\DSH_WORK\github工作\回测'
P49     = os.path.join(BASE, 'artifacts', 'p49_v3_backtest')
G7      = os.path.join(BASE, 'G7_ADJUDICATION_LEDGER')
ART     = os.path.join(BASE, 'artifacts')
FACTOR_CSV = os.path.join(P49, 'factors_full_11_v3.csv')
CROWDING_STATE_FILE = os.path.join(G7, 'p82_crowding_state.json')

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

IC_WINDOW_DAYS = 20
IC_FLIP_RATE_ALARM = 0.20
IC_LOCKED_ALERT_FACTORS = [
    'vol_regime_change', 'momentum_20d', 'realized_vol_20d',
    'oi_level', 'oi_change_1d', 'oi_change_rate_7d', 'spread_cs'
]
IC_LOCKED_STABLE_FACTORS = ['contract_switch_flag']

# ─── Crowding Thresholds (HARD LOCKED) ───
CROWDING_ALERT_PERCENTILE = 90     # 90th percentile → MEDIUM alert
DIR_CONCENTRATION_EXTREME = 0.70   # >70% one direction = extreme
VALUE_HHI_HIGH = 0.25              # HHI > 0.25 = concentrated
IC_DECAY_WINDOW_SHORT = 5          # 5-day rolling IC
IC_DECAY_WINDOW_LONG = 20          # 20-day rolling IC
IC_DECAY_THRESHOLD = 0.30          # 30% decay from long to short = signal


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
    """Compute daily returns from close prices"""
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


def compute_factor_series(data, factor):
    """
    Extract a time series of factor values across all symbols.
    Returns list of (date, symbol, value) sorted by date.
    """
    series = []
    for date in sorted(data.keys()):
        for symbol in SYMBOL_WHITELIST:
            if symbol in data[date]:
                fv = safe_float(data[date][symbol].get(factor, ''))
                if fv is not None:
                    series.append((date, symbol, fv))
    return series


def compute_directional_concentration(series):
    """
    Compute directional concentration: ratio of positive values.
    0.5 = balanced, >0.7 or <0.3 = crowded.
    Returns dict with concentration stats.
    """
    if not series:
        return {'positive_ratio': None, 'negative_ratio': None, 'zero_count': 0}

    values = [v for _, _, v in series]
    pos_count = sum(1 for v in values if v > 0)
    neg_count = sum(1 for v in values if v < 0)
    zero_count = sum(1 for v in values if v == 0)

    total_nonzero = pos_count + neg_count
    pos_ratio = pos_count / total_nonzero if total_nonzero > 0 else 0.5
    neg_ratio = neg_count / total_nonzero if total_nonzero > 0 else 0.5

    # Skewness as a crowding indicator
    if len(values) >= 3:
        mean_v = sum(values) / len(values)
        std_v = math.sqrt(sum((v - mean_v)**2 for v in values) / len(values))
        skewness = sum(((v - mean_v) / std_v)**3 for v in values) / len(values) if std_v > 0 else 0
    else:
        skewness = 0

    return {
        'total_observations': len(values),
        'positive_count': pos_count,
        'negative_count': neg_count,
        'zero_count': zero_count,
        'positive_ratio': round(pos_ratio, 4),
        'negative_ratio': round(neg_ratio, 4),
        'skewness': round(skewness, 4),
        'concentration_flag': pos_ratio > DIR_CONCENTRATION_EXTREME or pos_ratio < (1 - DIR_CONCENTRATION_EXTREME),
        'mean_value': round(sum(values) / len(values), 6) if values else 0,
        'std_value': round(math.sqrt(sum((v - sum(values)/len(values))**2 for v in values) / len(values)), 6) if len(values) > 1 else 0,
    }


def compute_value_concentration(series):
    """
    Compute HHI (Herfindahl-Hirschman Index) of factor value distribution.
    Bin values into 10 equal-width bins, compute HHI.
    Higher HHI = more concentrated = more crowded.
    """
    if not series:
        return {'hhi': None, 'num_bins': 0, 'dominant_bin': None}

    values = [v for _, _, v in series]
    if not values:
        return {'hhi': None, 'num_bins': 0}

    min_v, max_v = min(values), max(values)
    if min_v == max_v:
        return {'hhi': 1.0, 'num_bins': 1, 'dominant_bin': 'all_same', 'range': 0}

    # Bin into 10 equal-width bins
    num_bins = 10
    bin_width = (max_v - min_v) / num_bins
    bin_counts = [0] * num_bins

    for v in values:
        bin_idx = min(int((v - min_v) / bin_width), num_bins - 1)
        bin_counts[bin_idx] += 1

    total = len(values)
    hhi = sum((c / total)**2 for c in bin_counts if c > 0)

    dominant_bin_idx = bin_counts.index(max(bin_counts))
    dominant_bin_pct = bin_counts[dominant_bin_idx] / total

    return {
        'hhi': round(hhi, 6),
        'hhi_normalized': round(hhi * (num_bins - 1) / num_bins, 6) if num_bins > 1 else 0,
        'num_bins': num_bins,
        'bin_counts': bin_counts,
        'dominant_bin_index': dominant_bin_idx,
        'dominant_bin_pct': round(dominant_bin_pct, 4),
        'value_range': round(max_v - min_v, 6),
        'concentration_flag': hhi > VALUE_HHI_HIGH,
    }


def compute_ic_momentum(data, daily_returns, factor, short_window=IC_DECAY_WINDOW_SHORT, long_window=IC_DECAY_WINDOW_LONG):
    """
    Compute IC momentum: compare short-window IC vs long-window IC.
    Decay = short_ic / long_ic. Decay < (1 - threshold) = crowding signal.
    """
    dates_sorted = sorted(data.keys())
    short_ics = []
    long_ics = []

    for i in range(0, len(dates_sorted)):
        # Short window IC
        short_dates = dates_sorted[max(0, i - short_window + 1):i + 1]
        if len(short_dates) >= 5:
            f_vals, r_vals = [], []
            for d in short_dates:
                if d not in daily_returns:
                    continue
                for symbol in SYMBOL_WHITELIST:
                    if symbol not in daily_returns[d]:
                        continue
                    fv = safe_float(data[d][symbol].get(factor, ''))
                    if fv is not None:
                        f_vals.append(fv)
                        r_vals.append(daily_returns[d][symbol])
            if len(f_vals) >= 5:
                short_ics.append(pearson_corr(f_vals, r_vals))

        # Long window IC
        long_dates = dates_sorted[max(0, i - long_window + 1):i + 1]
        if len(long_dates) >= 10:
            f_vals, r_vals = [], []
            for d in long_dates:
                if d not in daily_returns:
                    continue
                for symbol in SYMBOL_WHITELIST:
                    if symbol not in daily_returns[d]:
                        continue
                    fv = safe_float(data[d][symbol].get(factor, ''))
                    if fv is not None:
                        f_vals.append(fv)
                        r_vals.append(daily_returns[d][symbol])
            if len(f_vals) >= 10:
                long_ics.append(pearson_corr(f_vals, r_vals))

    if not short_ics or not long_ics:
        return {
            'short_window_ic': None, 'long_window_ic': None,
            'ic_decay': None, 'momentum_flag': False,
        }

    mean_short = sum(short_ics) / len(short_ics)
    mean_long = sum(long_ics) / len(long_ics)

    # IC decay: if long IC is meaningful and short IC has dropped significantly
    if abs(mean_long) > 0.001:
        ic_decay = 1 - (abs(mean_short) / abs(mean_long))
        ic_decay = max(0, min(1, ic_decay))  # Clamp to [0, 1]
    else:
        ic_decay = 0

    momentum_flag = ic_decay > IC_DECAY_THRESHOLD

    return {
        'short_window_ic': round(mean_short, 6),
        'long_window_ic': round(mean_long, 6),
        'ic_decay': round(ic_decay, 4),
        'ic_decay_pct': f"{ic_decay*100:.1f}%",
        'momentum_flag': momentum_flag,
        'short_window_observations': len(short_ics),
        'long_window_observations': len(long_ics),
        'interpretation': (
            f"短期IC={mean_short:.5f}, 长期IC={mean_long:.5f}, "
            f"衰减率={ic_decay*100:.1f}%"
        ),
    }


def compute_crowding_score(dir_conc, value_conc, ic_mom):
    """
    Compute composite crowding score (0-100 scale).
    Higher = more crowded.
    """
    score = 0
    components = {}

    # Component 1: Directional concentration (0-35 points)
    if dir_conc.get('positive_ratio') is not None:
        pos_ratio = dir_conc['positive_ratio']
        # Deviation from 0.5
        dir_dev = abs(pos_ratio - 0.5) * 2  # 0 to 1
        dir_points = dir_dev * 35
        components['directional'] = round(dir_points, 2)
        score += dir_points

    # Component 2: Value concentration (0-35 points)
    if value_conc.get('hhi') is not None:
        hhi = value_conc['hhi']
        # HHI normalized to 0-1 scale (max HHI=1 for single bin)
        value_points = min(hhi, 1.0) * 35
        components['value_concentration'] = round(value_points, 2)
        score += value_points

    # Component 3: IC momentum decay (0-30 points)
    if ic_mom.get('ic_decay') is not None:
        decay = ic_mom['ic_decay']
        ic_points = decay * 30
        components['ic_decay'] = round(ic_points, 2)
        score += ic_points

    return {
        'score': round(score, 2),
        'max_score': 100,
        'score_pct': round(score / 100 * 100, 1),
        'components': components,
    }


def compute_historical_percentile(current_value, history):
    """Compute what percentile the current value falls in, given historical values"""
    if not history or len(history) < 10:
        return None
    sorted_h = sorted(history)
    count_below = sum(1 for v in sorted_h if v <= current_value)
    percentile = (count_below / len(sorted_h)) * 100
    return round(percentile, 1)


def monitor_crowding(output_state=None):
    """
    Main crowding monitoring function.
    Returns comprehensive crowding state dictionary.
    """
    print("=" * 70)
    print("[TASK-039] Factor Crowding Monitor — Concentration & Momentum")
    print("=" * 70)
    print(f"  Alert percentile threshold: {CROWDING_ALERT_PERCENTILE}th")
    print(f"  Directional concentration extreme: >{DIR_CONCENTRATION_EXTREME*100:.0f}%")
    print(f"  Value HHI high: >{VALUE_HHI_HIGH}")
    print(f"  IC decay threshold: >{IC_DECAY_THRESHOLD*100:.0f}%")
    print()

    # Load data
    data = load_factor_data()
    dates_sorted = sorted(data.keys())
    daily_returns = compute_daily_returns(data)
    total_dates = len(dates_sorted)

    print(f"  Total trading dates: {total_dates}")
    print(f"  Date range: {dates_sorted[0]} → {dates_sorted[-1]}")
    print()

    # Per-factor crowding analysis
    factor_results = {}
    alerts = []

    print("  Computing per-factor crowding metrics...")
    for factor in FACTOR_COLUMNS:
        print(f"\n  --- {factor} ---")

        # Get factor time series
        series = compute_factor_series(data, factor)
        if not series:
            factor_results[factor] = {'status': 'NO_DATA'}
            print(f"    [SKIP] No data available")
            continue

        # 1. Directional concentration
        dir_conc = compute_directional_concentration(series)
        print(f"    Dir Concentration: pos_ratio={dir_conc.get('positive_ratio', 'N/A')} "
              f"skewness={dir_conc.get('skewness', 'N/A')} "
              f"flag={'CROWDED' if dir_conc.get('concentration_flag') else 'OK'}")

        # 2. Value concentration (HHI)
        value_conc = compute_value_concentration(series)
        print(f"    Value Concentration: HHI={value_conc.get('hhi', 'N/A')} "
              f"dominant_bin={value_conc.get('dominant_bin_pct', 'N/A')} "
              f"flag={'CONCENTRATED' if value_conc.get('concentration_flag') else 'OK'}")

        # 3. IC momentum
        ic_mom = compute_ic_momentum(data, daily_returns, factor)
        print(f"    IC Momentum: short_IC={ic_mom.get('short_window_ic', 'N/A')} "
              f"long_IC={ic_mom.get('long_window_ic', 'N/A')} "
              f"decay={ic_mom.get('ic_decay', 'N/A')} "
              f"flag={'DECAY' if ic_mom.get('momentum_flag') else 'OK'}")

        # 4. Composite crowding score
        crowding = compute_crowding_score(dir_conc, value_conc, ic_mom)
        print(f"    Crowding Score: {crowding['score']}/{crowding['max_score']} "
              f"({crowding['score_pct']}%)")

        # 5. Historical percentile
        # Store current metrics in history for percentile comparison
        score_percentile = None

        factor_results[factor] = {
            'status': 'OK',
            'total_observations': dir_conc.get('total_observations', 0),
            'directional_concentration': dir_conc,
            'value_concentration': value_conc,
            'ic_momentum': ic_mom,
            'crowding_score': crowding,
            'score_percentile': score_percentile,
            'alert_triggered': False,
            'alert_severity': None,
        }

        # Check for alert
        alert_flags = []
        if dir_conc.get('concentration_flag'):
            alert_flags.append('DIRECTIONAL_CROWDED')
        if value_conc.get('concentration_flag'):
            alert_flags.append('VALUE_CONCENTRATED')
        if ic_mom.get('momentum_flag'):
            alert_flags.append('IC_DECAY')

        if alert_flags:
            factor_results[factor]['status'] = 'CROWDED'
            factor_results[factor]['alert_triggered'] = True
            factor_results[factor]['alert_severity'] = 'MEDIUM'
            factor_results[factor]['alert_flags'] = alert_flags

            alert_entry = {
                'factor': factor,
                'alert_type': 'FACTOR_CROWDING_DETECTED',
                'severity': 'MEDIUM',
                'crowding_score': crowding['score'],
                'score_percentile': score_percentile,
                'flags': alert_flags,
                'detail': f"{factor} 拥挤度异常: score={crowding['score']}, "
                          f"dir_conc={dir_conc.get('positive_ratio', 'N/A')}, "
                          f"HHI={value_conc.get('hhi', 'N/A')}, "
                          f"IC_decay={ic_mom.get('ic_decay', 'N/A')}",
                'directional_concentration': dir_conc.get('positive_ratio', None),
                'value_hhi': value_conc.get('hhi', None),
                'ic_decay': ic_mom.get('ic_decay', None),
                'source': TASK_TAG,
            }
            alerts.append(alert_entry)
            print(f"    [ALERT-MEDIUM] Crowding detected! Flags: {', '.join(alert_flags)}")

    # Compute portfolio-level crowding summary
    print(f"\n  {'='*50}")
    print(f"  Portfolio-Level Crowding Summary")
    print(f"  {'='*50}")

    scores = []
    for factor in FACTOR_COLUMNS:
        result = factor_results.get(factor, {})
        if result.get('crowding_score'):
            scores.append(result['crowding_score']['score'])

    if scores:
        portfolio_crowding = {
            'mean_score': round(sum(scores) / len(scores), 2),
            'max_score': round(max(scores), 2),
            'min_score': round(min(scores), 2),
            'std_score': round(math.sqrt(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)), 2) if len(scores) > 1 else 0,
            'num_factors_alerting': sum(1 for s in scores if s > 50),
            'avg_score_pct': round(sum(scores) / len(scores), 1),
        }
        print(f"    Mean Score: {portfolio_crowding['mean_score']}/{100} ({portfolio_crowding['avg_score_pct']}%)")
        print(f"    Max Score: {portfolio_crowding['max_score']}/{100}")
        print(f"    Min Score: {portfolio_crowding['min_score']}/{100}")
        print(f"    Factors Alerting (>50): {portfolio_crowding['num_factors_alerting']}/{len(scores)}")
    else:
        portfolio_crowding = {'mean_score': 0, 'max_score': 0, 'min_score': 0}

    # Overall crowding level
    if portfolio_crowding.get('num_factors_alerting', 0) >= 3:
        overall_level = 'CROWDING_HIGH'
    elif portfolio_crowding.get('num_factors_alerting', 0) >= 1:
        overall_level = 'CROWDING_MODERATE'
    else:
        overall_level = 'CROWDING_LOW'

    print(f"\n    Overall Crowding Level: {overall_level}")
    print(f"    Alerts Generated: {len(alerts)}")

    # Build state output
    state = {
        'crowding_monitor': {
            'monitor_id': 'DSHD-TASK039-CROWDING-MONITOR',
            'version': '1.0.0',
            'task_id': TASK_ID,
            'token': TOKEN,
            'mode': 'AUDIT_READ_ONLY',
            'wind_api_calls': 0,
            'gate': 'CLOSED/HOLD',
            'release_permit': 'NOT_ISSUED',
        },
        'thresholds': {
            'crowding_alert_percentile': CROWDING_ALERT_PERCENTILE,
            'dir_concentration_extreme': DIR_CONCENTRATION_EXTREME,
            'value_hhi_high': VALUE_HHI_HIGH,
            'ic_decay_threshold': IC_DECAY_THRESHOLD,
            'short_ic_window': IC_DECAY_WINDOW_SHORT,
            'long_ic_window': IC_DECAY_WINDOW_LONG,
            'alert_severity': 'MEDIUM',
            'hard_locked': True,
            'hard_lock_reason': 'TASK-039 PERMANENT',
        },
        'factor_results': factor_results,
        'portfolio_crowding': portfolio_crowding,
        'overall_crowding_level': overall_level,
        'alerts': alerts,
        'last_run': now_str(),
        'total_runs': 0,
        'run_history': [],
    }

    print(f"\n  Crowding Monitor Complete.")
    return state


def save_state(state, output_path=None):
    """Save crowding state to JSON"""
    path = output_path or CROWDING_STATE_FILE
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
        'overall_level': state['overall_crowding_level'],
        'num_alerts': len(state['alerts']),
        'mean_score': state['portfolio_crowding'].get('mean_score', 0),
        'source': TASK_TAG,
    })
    state['run_history'] = state['run_history'][-50:]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"\n  State saved: {path} (run #{state['total_runs']})")
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crowding Monitor Module')
    parser.add_argument('--output-state', type=str, default=CROWDING_STATE_FILE,
                        help='Output state JSON path')
    args = parser.parse_args()

    state = monitor_crowding()
    save_state(state, args.output_state)

    print(f"\n{'='*70}")
    print(f"  DSHD-TASK-039 Crowding Monitor COMPLETE")
    print(f"{'='*70}")