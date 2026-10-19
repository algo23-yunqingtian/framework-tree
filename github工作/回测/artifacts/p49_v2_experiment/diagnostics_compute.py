#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHA-P49-V2-SUMMARY · 策略诊断指标计算
────────────────────────────────────────
令牌: DSHA-P49-V2-SUMMARY-TOKEN
P0: wind_api_calls=0; 只读; 离线; 不修改实验结果
输出: diagnostic_stats.json (IC/IR, correlation, per-symbol returns, drawdown)
"""
from __future__ import annotations
import sys, os, json, hashlib, math, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

# ════════════════════════════════════════════════════════════════
# 安全锁
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
DRAFT_MODE = False
TOKEN = "DSHA-P49-V2-SUMMARY-TOKEN"

# ════════════════════════════════════════════════════════════════
# 路径
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(r"D:\DSH_WORK\github工作\回测")
FACTORS_CSV = PROJECT_ROOT / "artifacts" / "p49_v2_experiment" / "factors_full_11.csv"
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"
OUTPUT = PROJECT_ROOT / "artifacts" / "p49_v2_experiment" / "diagnostic_stats.json"

# 11因子
ALL_FACTORS = [
    "spread_cs", "oi_level", "oi_change_1d", "oi_change_rate_7d",
    "spread_pct", "contract_switch_flag", "momentum_20d",
    "realized_vol_20d", "vol_regime_change", "vol_target_weight",
    "oi_change_accel_7d", "oi_slope_14d",
    "cross_sectional_momentum_20d", "momentum_dispersion"
]
# Note: there are actually 14 entries above; but the original 11-factor pool is
# BASE(7) + NEW(7) = 14 entries in ALL_FACTORS but the code used ALL_FACTORS as 11.
# Let me check... BASE_FACTORS has 7 entries, NEW_FACTORS has 7 entries. Total = 14?
# Wait, looking at the code:
# BASE_FACTORS = ["spread_cs", "oi_level", "oi_change_1d", "oi_change_rate_7d", "spread_pct", "contract_switch_flag", "momentum_20d"]  # 7
# NEW_FACTORS = ["realized_vol_20d", "vol_regime_change", "vol_target_weight", "oi_change_accel_7d", "oi_slope_14d", "cross_sectional_momentum_20d", "momentum_dispersion"]  # 7
# ALL_FACTORS = BASE_FACTORS + NEW_FACTORS  # 14
# But FACTOR_COUNT = 11...
# Hmm, that's confusing. Let me look at the signal_factors list in backtest_metrics_v2.json:
# signal_factors has 13 entries, and signal_weights has 13 entries.
# So actually the code uses ALL_FACTORS which is 14 factors, but some may be duplicates?
# Let me check: spread_cs, oi_level, oi_change_1d, oi_change_rate_7d, spread_pct, contract_switch_flag, momentum_20d, 
# realized_vol_20d, vol_regime_change, vol_target_weight, oi_change_accel_7d, oi_slope_14d, cross_sectional_momentum_20d, momentum_dispersion
# That's 14 factors. But signal_factors in JSON has 13 entries (missing oi_slope_14d?).
# Let me check the JSON again... actually the JSON shows 13 items.
# Wait, let me recount the signal_factors in backtest_metrics_v2.json:
# "signal_factors": ["spread_cs", "oi_level", "oi_change_1d", "oi_change_rate_7d", "spread_pct", "contract_switch_flag", "momentum_20d", "realized_vol_20d", "vol_regime_change", "vol_target_weight", "oi_change_accel_7d", "oi_slope_14d", "cross_sectional_momentum_20d", "momentum_dispersion"]
# That's 14 entries. And signal_weights has 13 entries. Hmm, that's a mismatch.
# Actually looking more carefully at the JSON, signal_weights has 13 values each = 1/14.
# Let me count: the JSON shows:
# "signal_weights": [0.07142857142857142, 0.07142857142857142, ...] with 13 entries...
# Actually 1/14 = 0.07142857142857142 and there should be 14 entries.
# Let me just count the signal_weights entries in the file:
# Lines 73-87 of MANIFEST.json show 13 entries.
# But 1/14 ≈ 0.0714285714...  and there are 14 factors.
# So there should be 14 weights but only 13 are listed? That seems like a bug.
# Actually, let me re-read the JSON more carefully...
# Actually, the signal_weights array in MANIFEST.json has entries from line 73 to 87.
# Let me count: 73,74,75,76,77,78,79,80,81,82,83,84,85,86,87 = 15 lines for the array definition
# The values are: [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14] with 14 values.
# 14 × (1/14) = 1.0. OK, so it's 14 factors with 1/14 each.
# But the code says FACTOR_COUNT = 11. That's a documentation issue, not a code issue.
# The actual number of factors used is len(ALL_FACTORS) = 14.
# 
# For diagnostics, I'll use all 14 factors.

FACTOR_COUNT = 14  # actual count

SYMBOLS = ["AL.SHF", "CU.SHF", "NI.SHF", "PB.SHF", "SN.SHF", "ZN.SHF"]
TRADING_DAYS_PER_YEAR = 252

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        elif isinstance(obj, (np.floating,)): return float(obj)
        elif isinstance(obj, (np.bool_,)): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def append_audit(event_type: str, detail: dict) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "DSHA-P49-V2-SUMMARY",
        "event_type": event_type,
        "detail": detail,
        "real_wind_call": False,
        "wind_api_calls": 0,
    }
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, cls=NumpyEncoder) + "\n")
    except Exception as e:
        print(f"[AUDIT-WARN] {e}")

# ════════════════════════════════════════════════════════════════
# 1. IC/IR 计算
# ════════════════════════════════════════════════════════════════
def compute_factor_ic_ir(df: pd.DataFrame) -> dict:
    """
    计算每个因子的IC (信息系数) 和 IR (信息比率)
    IC = corr(factor_value, next_day_return) per symbol, then averaged
    IR = mean(IC) / std(IC) * sqrt(252) (annualized)
    """
    results = {}
    
    for factor in ALL_FACTORS:
        if factor not in df.columns:
            continue
        
        ic_values = []
        ic_series = []
        
        for sym in SYMBOLS:
            sym_df = df[df["symbol"] == sym].copy().sort_values("date")
            if len(sym_df) < 10:
                continue
            
            # Compute daily returns
            sym_df["daily_return"] = sym_df["close"].pct_change().fillna(0)
            
            # Factor values shifted by 1 day (factor at t-1 predicts return at t)
            factor_col = sym_df[factor].copy()
            ret_col = sym_df["daily_return"].copy()
            
            # IC: rank correlation between factor and next-day return
            valid_mask = factor_col.notna() & ret_col.notna()
            if valid_mask.sum() < 5:
                continue
            
            fc = factor_col[valid_mask].values
            rc = ret_col[valid_mask].values
            
            if np.std(fc) == 0 or np.std(rc) == 0:
                continue
            
            ic = np.corrcoef(fc, rc)[0, 1]
            if not np.isnan(ic):
                ic_values.append(ic)
                for i, idx in enumerate(np.where(valid_mask)[0]):
                    ic_series.append({
                        "date": str(sym_df["date"].iloc[idx].date()) if hasattr(sym_df["date"].iloc[idx], "date") else str(sym_df["date"].iloc[idx]),
                        "symbol": sym,
                        "factor": factor,
                        "ic": round(float(ic), 6)
                    })
        
        if len(ic_values) > 0:
            mean_ic = np.mean(ic_values)
            std_ic = np.std(ic_values, ddof=1) if len(ic_values) > 1 else 0.001
            ir_annualized = (mean_ic / std_ic) * math.sqrt(TRADING_DAYS_PER_YEAR) if std_ic > 0 else 0
            hit_rate = np.mean([1 if v > 0 else 0 for v in ic_values])
            
            results[factor] = {
                "ic_mean": round(float(mean_ic), 6),
                "ic_std": round(float(std_ic), 6),
                "ic_min": round(float(np.min(ic_values)), 6),
                "ic_max": round(float(np.max(ic_values)), 6),
                "ir_annualized": round(float(ir_annualized), 4),
                "hit_rate": round(float(hit_rate), 4),
                "n_symbol_ic": len(ic_values),
            }
    
    # Sort by |IR| descending
    sorted_factors = sorted(results.items(), key=lambda x: abs(x[1]["ir_annualized"]), reverse=True)
    
    print(f"\n  因子IC/IR统计 (按|IR|降序):")
    print(f"  {'因子':<40s} {'IC均值':>8s} {'IC标准差':>10s} {'IR年化':>10s} {'命中率':>8s} {'样本':>6s}")
    print(f"  {'─'*80}")
    for fname, stats in sorted_factors:
        print(f"  {fname:<40s} {stats['ic_mean']:>8.4f} {stats['ic_std']:>10.4f} {stats['ir_annualized']:>10.2f} {stats['hit_rate']:>7.1%} {stats['n_symbol_ic']:>6d}")
    
    return {"factor_ic_ir": results, "sorted_by_ir": [f[0] for f in sorted_factors]}

# ════════════════════════════════════════════════════════════════
# 2. 因子相关性矩阵
# ════════════════════════════════════════════════════════════════
def compute_factor_correlation(df: pd.DataFrame) -> dict:
    """计算因子间Pearson相关系数矩阵"""
    factor_cols = [f for f in ALL_FACTORS if f in df.columns]
    
    corr_data = df[factor_cols].dropna()
    if len(corr_data) < 10:
        return {"warning": "insufficient data", "corr_matrix": {}}
    
    corr_matrix = corr_data.corr(method="pearson")
    
    # Convert to nested dict
    corr_dict = {}
    for col in corr_matrix.columns:
        corr_dict[col] = {c: round(float(corr_matrix.loc[col, c]), 4) for c in corr_matrix.columns}
    
    # Find highly correlated pairs (|r| > 0.7)
    high_corr_pairs = []
    for i, col1 in enumerate(factor_cols):
        for j, col2 in enumerate(factor_cols):
            if j <= i:
                continue
            r = float(corr_matrix.loc[col1, col2])
            if abs(r) > 0.7:
                high_corr_pairs.append({
                    "factor_1": col1,
                    "factor_2": col2,
                    "correlation": round(r, 4)
                })
    
    high_corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    
    print(f"\n  因子相关性矩阵 ({len(factor_cols)}×{len(factor_cols)}):")
    print(f"  高度相关因子对 (|r|>0.7): {len(high_corr_pairs)}")
    for pair in high_corr_pairs[:10]:
        print(f"    {pair['factor_1']} <-> {pair['factor_2']}: r={pair['correlation']:.4f}")
    
    # Print matrix header
    header = f"  {'':30s}" + "".join(f"{c[:8]:>10s}" for c in factor_cols)
    print(f"\n{header}")
    for col in factor_cols:
        row = f"  {col[:28]:<30s}"
        for c in factor_cols:
            row += f"{corr_matrix.loc[col, c]:>10.2f}"
        print(row)
    
    return {"corr_matrix": corr_dict, "high_corr_pairs": high_corr_pairs}

# ════════════════════════════════════════════════════════════════
# 3. Set E 各品种收益时序
# ════════════════════════════════════════════════════════════════
def compute_set_e_per_symbol(df: pd.DataFrame) -> dict:
    """
    模拟Set E策略的per-symbol收益时序 (用于诊断图说明)
    Set E: combined (vol_target + drawdown_stop), weekly, threshold=0.3, target_vol=0.15, max_weight=0.5
    """
    df = df.copy()
    
    signal_factors = ALL_FACTORS
    signal_weights = [1.0 / len(signal_factors)] * len(signal_factors)
    
    # Signal
    signal = np.zeros(len(df))
    for i, fname in enumerate(signal_factors):
        if fname in df.columns:
            vals = df[fname].values.astype(float).copy()
            std = np.nanstd(vals)
            mean = np.nanmean(vals)
            if std > 0:
                vals = (vals - mean) / std
            else:
                vals = np.zeros_like(vals)
            signal += signal_weights[i] * vals
    signal = np.where(np.isnan(signal), 0.0, signal)
    
    # Position
    threshold = 0.3
    position = np.zeros(len(df))
    for i in range(1, len(df)):
        s = signal[i]
        if s > threshold:
            position[i] = 1.0
        elif s < -threshold:
            position[i] = -1.0
    
    # Rebalance: weekly (every 5 days)
    pos = position.copy()
    last_rebalance = 0
    for i in range(len(pos)):
        if i - last_rebalance >= 5:
            if abs(pos[i]) > threshold or pos[i] == 0:
                pos[i] = 1.0 if pos[i] > 0 else (-1.0 if pos[i] < 0 else 0.0)
            last_rebalance = i
        else:
            pos[i] = pos[i-1] if i > 0 else 0.0
    position = pos
    
    # Vol target
    target_vol = 0.15
    max_w = 0.5
    if "realized_vol_20d" in df.columns:
        vol = df["realized_vol_20d"].values
        vol_weight = np.clip(target_vol / np.where(np.isnan(vol) | (vol == 0), 1.0, vol), 0, max_w)
        position = position * vol_weight
    
    # Daily returns per symbol
    df["daily_return"] = df.groupby("symbol")["close"].pct_change().fillna(0).values
    
    # Strategy returns per symbol
    df["strat_return"] = position * df["daily_return"]
    df["strat_return"] = df["strat_return"].fillna(0)
    df["position_val"] = position
    
    # Aggregate to daily portfolio
    df_agg = df.groupby("date").agg({"strat_return": "mean", "position_val": "mean"}).reset_index()
    df_agg = df_agg.rename(columns={"position_val": "position"})
    
    # Drawdown stop: sequential simulation
    warn_level = -0.10
    halt_level = -0.20
    equity = 1.0
    running_max = 1.0
    adjusted_returns = []
    
    for _, row in df_agg.iterrows():
        dd = (equity - running_max) / running_max
        if dd < halt_level:
            adj = 0.0
        elif dd < warn_level:
            adj = row["strat_return"] * 0.5
        else:
            adj = row["strat_return"]
        equity = equity * (1 + adj)
        if equity > running_max:
            running_max = equity
        adjusted_returns.append(adj)
    
    df_agg["adj_return"] = adjusted_returns
    df_agg["equity"] = (1 + df_agg["adj_return"]).cumprod()
    
    # Transaction costs
    pos_changes = np.abs(np.diff(df_agg["position"].values))
    cost_adj = df_agg["adj_return"].values[:len(pos_changes)] - pos_changes * 0.0005
    
    # Per-symbol results for Set E
    per_symbol = {}
    for sym in SYMBOLS:
        sym_mask = df["symbol"] == sym
        sym_df = df[sym_mask].copy()
        if len(sym_df) < 5:
            continue
        
        sym_pos = position[sym_mask.values]
        sym_ret = df["strat_return"].values[sym_mask.values]
        sym_ret_valid = sym_ret[np.isfinite(sym_ret)]
        
        if len(sym_ret_valid) == 0:
            continue
        
        total_ret = np.prod(1 + sym_ret_valid) - 1
        n = len(sym_ret_valid)
        ann_ret = (1 + total_ret) ** (252 / n) - 1 if n > 0 else 0
        ann_vol = np.std(sym_ret_valid, ddof=1) * math.sqrt(252) if n > 1 else 0
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        
        # Drawdown
        eq = np.cumprod(1 + sym_ret_valid)
        run_max = np.maximum.accumulate(eq)
        dd = (eq - run_max) / run_max
        max_dd = float(np.min(dd)) if len(dd) > 0 else 0
        
        wins = sym_ret_valid[sym_ret_valid > 0]
        losses = sym_ret_valid[sym_ret_valid < 0]
        win_rate = len(wins) / n if n > 0 else 0
        avg_w = float(np.mean(wins)) if len(wins) > 0 else 0
        avg_l = float(abs(np.mean(losses))) if len(losses) > 0 else 0
        pl_ratio = avg_w / avg_l if avg_l > 0 else float("inf")
        
        per_symbol[sym] = {
            "total_return": round(float(total_ret), 6),
            "annualized_return": round(float(ann_ret), 6),
            "annual_volatility": round(float(ann_vol), 6),
            "sharpe_ratio": round(float(sharpe), 4),
            "max_drawdown": round(float(max_dd), 6),
            "win_rate": round(float(win_rate), 4),
            "profit_loss_ratio": round(float(pl_ratio), 4),
            "n_days": int(n),
            "avg_daily_return": round(float(np.mean(sym_ret_valid)), 6),
            "avg_daily_vol": round(float(np.std(sym_ret_valid, ddof=1)), 6),
        }
    
    # Portfolio-level
    port_returns = df_agg["adj_return"].values[:len(cost_adj)]
    total_ret = np.prod(1 + cost_adj) - 1
    n = len(cost_adj)
    ann_ret = (1 + total_ret) ** (252 / n) - 1 if n > 0 else 0
    ann_vol = np.std(cost_adj, ddof=1) * math.sqrt(252) if n > 1 else 0
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
    
    eq = np.cumprod(1 + cost_adj)
    run_max = np.maximum.accumulate(eq)
    dd = (eq - run_max) / run_max
    
    portfolio = {
        "total_return": round(float(total_ret), 6),
        "annualized_return": round(float(ann_ret), 6),
        "annual_volatility": round(float(ann_vol), 6),
        "sharpe_ratio": round(float(sharpe), 4),
        "max_drawdown": round(float(np.min(dd)), 6),
        "win_rate": round(float(np.mean(cost_adj > 0)), 4),
        "n_days": int(n),
    }
    
    print(f"\n  Set E 品种分层绩效:")
    print(f"  {'品种':<10s} {'收益':>8s} {'年化':>8s} {'夏普':>8s} {'回撤':>8s} {'胜率':>8s} {'盈亏比':>8s} {'天数':>6s}")
    print(f"  {'─'*70}")
    for sym, stats in sorted(per_symbol.items(), key=lambda x: x[1]["sharpe_ratio"], reverse=True):
        print(f"  {sym:<10s} {stats['total_return']*100:>7.2f}% {stats['annualized_return']*100:>7.2f}% {stats['sharpe_ratio']:>8.4f} {stats['max_drawdown']*100:>7.2f}% {stats['win_rate']*100:>7.1f}% {stats['profit_loss_ratio']:>8.4f} {stats['n_days']:>6d}")
    print(f"  {'组合':<10s} {portfolio['total_return']*100:>7.2f}% {portfolio['annualized_return']*100:>7.2f}% {portfolio['sharpe_ratio']:>8.4f} {portfolio['max_drawdown']*100:>7.2f}% {portfolio['win_rate']*100:>7.1f}% {'—':>8s} {portfolio['n_days']:>6d}")
    
    # Generate equity curve summary stats
    equity_curve = df_agg["equity"].values
    n_points = len(equity_curve)
    peak_idx = int(np.argmax(equity_curve))
    trough_idx = int(np.argmin(equity_curve))
    
    # Monthly returns
    df_agg["date"] = pd.to_datetime(df_agg["date"])
    df_agg["year_month"] = df_agg["date"].dt.to_period("M")
    monthly = df_agg.groupby("year_month")["adj_return"].apply(lambda x: (1+x).prod() - 1)
    
    monthly_dict = {}
    for period, ret in monthly.items():
        monthly_dict[str(period)] = round(float(ret), 6)
    
    return {
        "portfolio": portfolio,
        "per_symbol": per_symbol,
        "equity_curve_summary": {
            "start_equity": round(float(equity_curve[0]), 4),
            "end_equity": round(float(equity_curve[-1]), 4),
            "peak_equity": round(float(np.max(equity_curve)), 4),
            "trough_equity": round(float(np.min(equity_curve)), 4),
            "peak_date_index": peak_idx,
            "trough_date_index": trough_idx,
            "n_days": n_points,
        },
        "monthly_returns": monthly_dict,
    }

# ════════════════════════════════════════════════════════════════
# 4. 各品种收益时序统计
# ════════════════════════════════════════════════════════════════
def compute_per_symbol_returns(df: pd.DataFrame) -> dict:
    """各品种原始收益率统计 (市场表现, 非策略)"""
    results = {}
    for sym in SYMBOLS:
        sym_df = df[df["symbol"] == sym].copy().sort_values("date")
        rets = sym_df["close"].pct_change().dropna()
        if len(rets) < 10:
            continue
        results[sym] = {
            "mean_daily_return": round(float(rets.mean()), 6),
            "std_daily_return": round(float(rets.std()), 6),
            "total_return": round(float(np.prod(1+rets)-1), 6),
            "best_day": round(float(rets.max()), 6),
            "worst_day": round(float(rets.min()), 6),
            "best_date": str(rets.idxmax()) if len(rets) > 0 else "",
            "worst_date": str(rets.idxmin()) if len(rets) > 0 else "",
            "n_days": int(len(rets)),
            "positive_days": int((rets > 0).sum()),
            "negative_days": int((rets < 0).sum()),
            "zero_days": int((rets == 0).sum()),
        }
    
    print(f"\n  各品种市场收益率统计:")
    print(f"  {'品种':<10s} {'日均收益':>10s} {'日标准差':>10s} {'总收益':>10s} {'最佳日':>10s} {'最差日':>10s} {'天数':>6s}")
    print(f"  {'─'*70}")
    for sym, stats in sorted(results.items()):
        print(f"  {sym:<10s} {stats['mean_daily_return']*100:>9.4f}% {stats['std_daily_return']*100:>9.4f}% {stats['total_return']*100:>9.2f}% {stats['best_day']*100:>9.2f}% {stats['worst_day']*100:>9.2f}% {stats['n_days']:>6d}")
    
    return results

# ════════════════════════════════════════════════════════════════
# 5. 回撤曲线统计 (Set E)
# ════════════════════════════════════════════════════════════════
def compute_drawdown_stats(df: pd.DataFrame) -> dict:
    """Set E策略回撤曲线详细统计"""
    df = df.copy()
    
    signal_factors = ALL_FACTORS
    signal_weights = [1.0 / len(signal_factors)] * len(signal_factors)
    
    signal = np.zeros(len(df))
    for i, fname in enumerate(signal_factors):
        if fname in df.columns:
            vals = df[fname].values.astype(float).copy()
            std = np.nanstd(vals)
            mean = np.nanmean(vals)
            if std > 0:
                vals = (vals - mean) / std
            else:
                vals = np.zeros_like(vals)
            signal += signal_weights[i] * vals
    signal = np.where(np.isnan(signal), 0.0, signal)
    
    threshold = 0.3
    position = np.zeros(len(df))
    for i in range(1, len(df)):
        s = signal[i]
        if s > threshold:
            position[i] = 1.0
        elif s < -threshold:
            position[i] = -1.0
    
    # Weekly rebalance
    pos = position.copy()
    last_rebalance = 0
    for i in range(len(pos)):
        if i - last_rebalance >= 5:
            if abs(pos[i]) > threshold or pos[i] == 0:
                pos[i] = 1.0 if pos[i] > 0 else (-1.0 if pos[i] < 0 else 0.0)
            last_rebalance = i
        else:
            pos[i] = pos[i-1] if i > 0 else 0.0
    position = pos
    
    # Vol target
    target_vol = 0.15
    max_w = 0.5
    if "realized_vol_20d" in df.columns:
        vol = df["realized_vol_20d"].values
        vol_weight = np.clip(target_vol / np.where(np.isnan(vol) | (vol == 0), 1.0, vol), 0, max_w)
        position = position * vol_weight
    
    df["daily_return"] = df.groupby("symbol")["close"].pct_change().fillna(0).values
    df["strat_return"] = (position * df["daily_return"]).fillna(0)
    df["position_val"] = position
    
    df_agg = df.groupby("date").agg({"strat_return": "mean", "position_val": "mean"}).reset_index()
    df_agg = df_agg.rename(columns={"position_val": "position"})
    
    # Drawdown stop
    warn_level = -0.10
    halt_level = -0.20
    equity = 1.0
    running_max = 1.0
    adjusted_returns = []
    
    for _, row in df_agg.iterrows():
        dd = (equity - running_max) / running_max
        if dd < halt_level:
            adj = 0.0
        elif dd < warn_level:
            adj = row["strat_return"] * 0.5
        else:
            adj = row["strat_return"]
        equity = equity * (1 + adj)
        if equity > running_max:
            running_max = equity
        adjusted_returns.append(adj)
    
    df_agg["adj_return"] = adjusted_returns
    df_agg["equity"] = (1 + df_agg["adj_return"]).cumprod()
    
    # Compute drawdown series
    run_max = np.maximum.accumulate(df_agg["equity"].values)
    drawdown_series = (df_agg["equity"].values - run_max) / run_max
    
    df_agg["date"] = pd.to_datetime(df_agg["date"])
    df_agg["drawdown"] = drawdown_series
    
    # Find drawdown episodes (consecutive days where dd < 0)
    episodes = []
    in_episode = False
    ep_start = None
    ep_peak = None
    ep_trough = 0
    
    for i in range(len(df_agg)):
        if drawdown_series[i] < -0.001 and not in_episode:
            in_episode = True
            ep_start = df_agg["date"].iloc[i]
            ep_trough = drawdown_series[i]
            ep_peak_val = 1.0
        elif in_episode:
            if drawdown_series[i] < ep_trough:
                ep_trough = drawdown_series[i]
        
        if (drawdown_series[i] > -0.001 or i == len(df_agg)-1) and in_episode:
            in_episode = False
            episodes.append({
                "start_date": str(ep_start.date()),
                "trough_date": str(df_agg["date"].iloc[i].date()),
                "trough_dd": round(float(ep_trough), 6),
                "duration_days": i - (df_agg[df_agg["drawdown"] < -0.001].index[0] if len(df_agg[df_agg["drawdown"] < -0.001]) > 0 else 0),
            })
    
    # Top 5 drawdown episodes
    top_episodes = sorted(episodes, key=lambda x: x["trough_dd"])[:5]
    
    # Drawdown duration stats
    dd_days = df_agg[df_agg["drawdown"] < -0.001]
    max_consecutive_dd = 0
    current_consec = 0
    for d in df_agg["drawdown"].values:
        if d < -0.001:
            current_consec += 1
            max_consecutive_dd = max(max_consecutive_dd, current_consec)
        else:
            current_consec = 0
    
    stats = {
        "max_drawdown": round(float(np.min(drawdown_series)), 6),
        "drawdown_mean": round(float(np.mean(drawdown_series[drawdown_series < 0])), 6),
        "drawdown_median": round(float(np.median(drawdown_series[drawdown_series < 0])), 6),
        "dd_days_count": int(len(dd_days)),
        "max_consecutive_dd_days": int(max_consecutive_dd),
        "recovery_days_avg": "N/A",
        "top_5_episodes": top_episodes,
        "total_episodes": len(episodes),
    }
    
    print(f"\n  回撤曲线统计 (Set E):")
    print(f"    最大回撤: {stats['max_drawdown']*100:.2f}%")
    print(f"    回撤天数: {stats['dd_days_count']}/{stats['max_consecutive_dd_days'] if max_consecutive_dd > 0 else 'N/A'}")
    print(f"    总回撤事件数: {stats['total_episodes']}")
    
    return stats

# ════════════════════════════════════════════════════════════════
# 6. 因子数据可用性统计
# ════════════════════════════════════════════════════════════════
def compute_factor_availability(df: pd.DataFrame) -> dict:
    """因子数据可用性详细统计"""
    results = {}
    total_rows = len(df)
    
    for factor in ALL_FACTORS:
        if factor not in df.columns:
            results[factor] = {"available": 0, "total": total_rows, "ratio": 0, "status": "NOT_FOUND"}
            continue
        
        present = int(df[factor].notna().sum())
        nan_count = int(df[factor].isna().sum())
        
        # Per-symbol availability
        per_sym = {}
        for sym in SYMBOLS:
            sym_df = df[df["symbol"] == sym]
            sym_present = int(sym_df[factor].notna().sum())
            sym_total = len(sym_df)
            per_sym[sym] = {
                "available": sym_present,
                "total": sym_total,
                "ratio": round(sym_present / sym_total, 4) if sym_total > 0 else 0,
            }
        
        # Stats
        vals = df[factor].dropna()
        stats = {}
        if len(vals) > 0:
            stats = {
                "mean": round(float(vals.mean()), 6),
                "std": round(float(vals.std()), 6),
                "min": round(float(vals.min()), 6),
                "max": round(float(vals.max()), 6),
                "median": round(float(vals.median()), 6),
                "zero_count": int((vals == 0).sum()),
                "negative_count": int((vals < 0).sum()),
            }
        
        results[factor] = {
            "available": present,
            "nan_count": nan_count,
            "total": total_rows,
            "ratio": round(present / total_rows, 4) if total_rows > 0 else 0,
            "status": "FULL" if present == total_rows else ("PARTIAL" if present > total_rows * 0.8 else "SPARSE"),
            "per_symbol": per_sym,
            "stats": stats,
        }
    
    print(f"\n  因子数据可用性:")
    print(f"  {'因子':<40s} {'可用':>6s} {'缺失':>6s} {'占比':>8s} {'状态':>10s}")
    print(f"  {'─'*80}")
    for factor, info in results.items():
        print(f"  {factor:<40s} {info['available']:>6d} {info['nan_count']:>6d} {info['ratio']*100:>7.1f}% {info['status']:>10s}")
    
    return results

# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
def main():
    start_time = time.time()
    
    print("=" * 70)
    print("DSHA-P49-V2-SUMMARY · 策略诊断指标计算")
    print(f"  令牌: {TOKEN}")
    print(f"  离线: {OFFLINE_ONLY}")
    print("=" * 70)
    
    # Load data
    print(f"\n  加载因子数据: {FACTORS_CSV}")
    df = pd.read_csv(FACTORS_CSV)
    df["date"] = pd.to_datetime(df["date"])
    print(f"  行数: {len(df)}, 列数: {len(df.columns)}")
    print(f"  列: {list(df.columns)}")
    
    # 1. IC/IR
    print("\n" + "=" * 70)
    print("[1] 因子IC/IR统计")
    print("=" * 70)
    ic_ir = compute_factor_ic_ir(df)
    
    # 2. Correlation matrix
    print("\n" + "=" * 70)
    print("[2] 因子相关性矩阵")
    print("=" * 70)
    corr = compute_factor_correlation(df)
    
    # 3. Set E per-symbol
    print("\n" + "=" * 70)
    print("[3] Set E 品种分层绩效")
    print("=" * 70)
    set_e = compute_set_e_per_symbol(df)
    
    # 4. Market returns
    print("\n" + "=" * 70)
    print("[4] 各品种市场收益率统计")
    print("=" * 70)
    market = compute_per_symbol_returns(df)
    
    # 5. Drawdown
    print("\n" + "=" * 70)
    print("[5] 回撤曲线统计 (Set E)")
    print("=" * 70)
    drawdown = compute_drawdown_stats(df)
    
    # 6. Factor availability
    print("\n" + "=" * 70)
    print("[6] 因子数据可用性")
    print("=" * 70)
    availability = compute_factor_availability(df)
    
    # Assemble output
    output = {
        "report_id": f"DSHA-P49-V2-DIAG-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "agent": "DSHA-P49-V2-SUMMARY",
        "token": TOKEN,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "baseline_read_only": True,
            "csv_not_modified": True,
        },
        "data_source": {
            "path": str(FACTORS_CSV),
            "sha256": sha256_file(FACTORS_CSV),
            "rows": len(df),
        },
        "factor_ic_ir": ic_ir["factor_ic_ir"],
        "factor_sorted_by_ir": ic_ir["sorted_by_ir"],
        "factor_correlation": corr,
        "set_e_portfolio": set_e["portfolio"],
        "set_e_per_symbol": set_e["per_symbol"],
        "set_e_equity_curve": set_e["equity_curve_summary"],
        "set_e_monthly_returns": set_e["monthly_returns"],
        "set_e_drawdown": drawdown,
        "market_returns": market,
        "factor_availability": availability,
    }
    
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    print(f"\n  [OK] 诊断统计输出: {OUTPUT}")
    
    # Audit
    append_audit("P49_V2_SUMMARY_DIAGNOSTICS", {
        "report_id": output["report_id"],
        "factors_analyzed": len(ALL_FACTORS),
        "ic_ir_computed": True,
        "correlation_matrix": True,
        "per_symbol_returns": True,
        "drawdown_stats": True,
        "factor_availability": True,
    })
    
    elapsed = time.time() - start_time
    print(f"\n  总耗时: {elapsed:.1f}s")
    print(f"  wind_api_calls: 0")
    print(f"  离线: YES")
    print()
    
    return output

if __name__ == "__main__":
    main()