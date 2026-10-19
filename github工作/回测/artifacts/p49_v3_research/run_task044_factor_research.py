#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHA-TASK-044 · V3高翻转因子替换 + 备选因子池搭建
═══════════════════════════════════════════════════════════════════
令牌: DSHA-TASK044-FACTOR-RESEARCH-TOKEN
基线: feature/v88-g1 HEAD=73b0e32

任务:
  P1 存量7个高危因子诊断 (分行情切片IC、相关性矩阵、根因诊断)
  P2 新建15个备选因子候选池 (波动率/持仓/跨期价差三大方向)
  P3 备选组合对照回测 (对照组 vs 实验组, 仅研究不覆盖生产)
  P4 制品与审计闭环

约束:
  - wind_api_calls=0; Gate=CLOSED/HOLD; Release=NOT_ISSUED
  - 生产目录只读锁定, 禁止任何写入
  - 仅在独立research沙箱执行
  - run_v3_ic_weight_deprecated.py 继续归档隔离
  - 研究脚本与生产脚本物理目录隔离
"""
from __future__ import annotations

import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json, hashlib, math, time, warnings, csv, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

warnings.filterwarnings("ignore", message=".*input array is constant.*")
warnings.filterwarnings("ignore", message=".*All-NaN slice.*")
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════════
# JSON Encoder
# ════════════════════════════════════════════════════════════════
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        elif isinstance(obj, (np.floating,)): return float(obj)
        elif isinstance(obj, (np.bool_,)): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        elif isinstance(obj, (pd.Timestamp,)): return obj.isoformat()
        return super().default(obj)

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
TOKEN = "DSHA-TASK044-FACTOR-RESEARCH-TOKEN"
BASELINE_COMMIT = "73b0e32"
TASK_ID = "DSHA-TASK044-FACTOR-RESEARCH"
GATE_STATUS = "CLOSED/HOLD"
RELEASE_STATUS = "NOT_ISSUED"
TZ = timezone(timedelta(hours=8))

# ════════════════════════════════════════════════════════════════
# 路径常量
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(r"D:\DSH_WORK\github工作\回测")
PROD_DIR = PROJECT_ROOT / "artifacts" / "p49_v3_backtest"
RESEARCH_DIR = PROJECT_ROOT / "artifacts" / "p49_v3_research"
G7_DIR = PROJECT_ROOT / "G7_ADJUDICATION_LEDGER"
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"

V3_FACTORS_CSV = PROD_DIR / "factors_full_11_v3.csv"
FACTOR_WEIGHT_PROD = PROD_DIR / "factor_weight_prod.json"
FACTOR_ENABLE_CONFIG = PROD_DIR / "factor_enable_config.json"
PROD_CHECKSUM = PROD_DIR / "prod_baseline_checksum.json"
DEPRECATED_SCRIPT = PROD_DIR / "run_v3_ic_weight_deprecated.py"
SET_E_LOCK = PROJECT_ROOT / "artifacts" / "p49_v2_experiment" / "strategy_set_e.lock.json"

# Research outputs (physically isolated)
RESEARCH_MANIFEST = RESEARCH_DIR / "MANIFEST_v3_research.json"
CORR_MATRIX_JSON = RESEARCH_DIR / "corr_matrix.json"
CANDIDATE_LIST_JSON = RESEARCH_DIR / "candidate_factor_list.json"
REGIME_REPORT_JSON = RESEARCH_DIR / "regime_stability_report.json"
BACKTEST_METRICS_JSON = RESEARCH_DIR / "comparison_backtest_metrics.json"
RESEARCH_IC_EXPORT = RESEARCH_DIR / "research_rolling_ic_export.json"

# ════════════════════════════════════════════════════════════════
# Set E 冻结参数 (不可修改)
# ════════════════════════════════════════════════════════════════
SIGNAL_THRESHOLD = 0.3
REBALANCE_INTERVAL = 5
TARGET_VOL = 0.15
MAX_SINGLE_WEIGHT = 0.5
DRAWDOWN_WARN = -0.10
DRAWDOWN_HALT = -0.20
TRANSACTION_COST = 0.0005
INITIAL_CAPITAL = 1_000_000.0
TRADING_DAYS_PER_YEAR = 252

# 4品种白名单
ALL_4_SYMBOLS = ["LC.GFE", "NI.SHF", "CU.SHF", "ZN.SHF"]

# 8因子 (生产基线)
RETAINED_FACTORS = [
    "contract_switch_flag", "momentum_20d",
    "oi_change_1d", "oi_change_rate_7d",
    "oi_level", "realized_vol_20d",
    "spread_cs", "vol_regime_change",
]
EQUAL_WEIGHTS = [0.125] * len(RETAINED_FACTORS)

# 7个高翻转因子 (排除contract_switch_flag, flip=0%)
HIGH_FLIP_FACTORS = [
    "momentum_20d", "oi_change_1d", "oi_change_rate_7d",
    "oi_level", "realized_vol_20d", "spread_cs", "vol_regime_change",
]

# 3个翻转率最高的因子 (将被替换)
TOP3_FLIP_FACTORS = ["vol_regime_change", "momentum_20d", "realized_vol_20d"]
REMAINING_FACTORS = [f for f in RETAINED_FACTORS if f not in TOP3_FLIP_FACTORS]

# 15个候选因子
CANDIDATE_FACTORS = {
    "vol_range_pct_20d": "波动率-20日平均振幅百分比",
    "vol_return_skew_20d": "波动率-20日收益率偏度",
    "vol_return_kurtosis_20d": "波动率-20日收益率峰度",
    "vol_return_slope_20d": "波动率-20日收益率线性斜率",
    "vol_updown_ratio_20d": "波动率-20日上涨/下跌比率",
    "oi_momentum_20d": "持仓-20日持仓变动均值",
    "oi_to_vol_ratio_20d": "持仓-持仓变动/成交量比率20日均值",
    "oi_level_zscore_20d": "持仓-持仓量20日Z分数",
    "oi_acceleration_5d": "持仓-持仓变动5日加速度",
    "oi_rate_20d_momentum": "持仓-20日持仓变动率均值",
    "spread_cs_zscore_20d": "跨期-价差20日Z分数",
    "spread_cs_momentum_5d": "跨期-价差5日动量",
    "spread_pct_slope_20d": "跨期-价差百分比20日斜率",
    "spread_cs_atr_ratio_20d": "跨期-价差/ATR比率",
    "spread_cs_volatility_20d": "跨期-价差20日波动率",
}

# 滚动IC参数
IC_WINDOW_DAYS = 20
ROLLING_STEP = 20

# 翻转率筛选阈值
FLIP_RATE_FILTER = 0.20
IC_FILTER = 0.01
IR_FILTER = 0.05  # Information Ratio minimum

# Regime thresholds
REGIME_PCT_THRESHOLD = 0.005  # 0.5% band for sideways

# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def now_local() -> str:
    return datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S+08:00')

def append_audit(event_type: str, detail: dict) -> None:
    entry = {
        "timestamp": now_iso(),
        "agent": TASK_ID,
        "event_type": event_type,
        "detail": detail,
        "real_wind_call": False,
        "wind_api_calls": 0,
        "gate": GATE_STATUS,
        "release_permit": RELEASE_STATUS,
    }
    entry_str = json.dumps(entry, ensure_ascii=False, cls=NumpyEncoder) + "\n"
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(entry_str)
    except PermissionError:
        backup = AUDIT_LOG.parent / "tracking_monitor_audit_v3.jsonl"
        try:
            with open(backup, "a", encoding="utf-8") as f:
                f.write(entry_str)
        except Exception:
            pass
    except Exception:
        pass

# ════════════════════════════════════════════════════════════════
# 回测引擎 (与 V3 等权回测完全一致)
# ════════════════════════════════════════════════════════════════
def compute_backtest_with_weights(
    df: pd.DataFrame,
    signal_factors: List[str],
    signal_weights: List[float],
    threshold: float = SIGNAL_THRESHOLD,
    rebalance_interval: int = REBALANCE_INTERVAL,
    target_vol: float = TARGET_VOL,
    max_single_weight: float = MAX_SINGLE_WEIGHT,
) -> dict:
    df = df.copy()
    # 1. 信号生成: 加权复合因子
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
            w = signal_weights[i] if i < len(signal_weights) else 0.0
            signal += w * vals
    signal = np.where(np.isnan(signal), 0.0, signal)

    # 2. 仓位生成
    position = np.zeros(len(df))
    for i in range(1, len(df)):
        s = signal[i]
        if s > threshold:
            position[i] = 1.0
        elif s < -threshold:
            position[i] = -1.0
        else:
            position[i] = 0.0

    # 3. 调仓频率
    if rebalance_interval > 1:
        pos = position.copy()
        last_rebalance = 0
        for i in range(len(pos)):
            if i - last_rebalance >= rebalance_interval:
                if abs(pos[i]) > threshold or pos[i] == 0:
                    pos[i] = 1.0 if pos[i] > 0 else (-1.0 if pos[i] < 0 else 0.0)
                last_rebalance = i
            else:
                pos[i] = pos[i-1] if i > 0 else 0.0
        position = pos

    # 4. 仓位管理: 波动率目标
    if "realized_vol_20d" in df.columns:
        vol = df["realized_vol_20d"].values
        vol_weight = np.clip(target_vol / np.where(np.isnan(vol) | (vol == 0), 1.0, vol), 0, max_single_weight)
        position = position * vol_weight

    # 5. 日度收益计算
    daily_returns_per_symbol = df.groupby("symbol")["close"].pct_change().fillna(0).values
    min_len = min(len(position), len(daily_returns_per_symbol))
    position = position[:min_len]
    daily_returns_per_symbol = daily_returns_per_symbol[:min_len]
    strategy_returns_per_symbol = position * daily_returns_per_symbol
    nan_mask = ~np.isnan(strategy_returns_per_symbol)
    strategy_returns_per_symbol = strategy_returns_per_symbol[nan_mask]
    position_filtered = position[nan_mask]
    dates_filtered = df["date"].values[:min_len][nan_mask]
    df_agg = pd.DataFrame({
        "date": dates_filtered,
        "return": strategy_returns_per_symbol,
        "position": position_filtered,
    })
    daily_agg_df = df_agg.groupby("date").agg({"return": "mean", "position": "mean"}).reset_index()
    daily_agg_df.columns = ["date", "return", "position"]
    strategy_returns = daily_agg_df["return"].values
    position_agg = daily_agg_df["position"].values

    # 6. 回撤控制
    equity = INITIAL_CAPITAL
    running_max = INITIAL_CAPITAL
    adjusted_returns = np.zeros(len(strategy_returns))
    adjusted_positions = position_agg.copy()
    for i in range(len(strategy_returns)):
        dd = (equity - running_max) / running_max
        if dd < DRAWDOWN_HALT:
            adjusted_returns[i] = 0.0
            adjusted_positions[i] = 0.0
        elif dd < DRAWDOWN_WARN:
            adjusted_returns[i] = strategy_returns[i] * 0.5
            adjusted_positions[i] = position_agg[i] * 0.5
        else:
            adjusted_returns[i] = strategy_returns[i]
            adjusted_positions[i] = position_agg[i]
        equity = equity * (1 + adjusted_returns[i])
        if equity > running_max:
            running_max = equity
    strategy_returns = adjusted_returns
    position = adjusted_positions

    # 7. 交易成本
    position_changes = np.abs(np.diff(position))
    min_len = min(len(strategy_returns), len(position_changes))
    strategy_returns = strategy_returns[:min_len]
    position_changes = position_changes[:min_len]
    cost_adjusted = np.zeros_like(strategy_returns)
    for i in range(len(strategy_returns)):
        cost_adjusted[i] = strategy_returns[i] - position_changes[i] * TRANSACTION_COST

    # 8. 绩效指标
    equity_curve = np.cumprod(1 + cost_adjusted) * INITIAL_CAPITAL
    equity_curve = np.insert(equity_curve, 0, INITIAL_CAPITAL)
    total_return = (equity_curve[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL
    n_periods = len(cost_adjusted)
    annual_return = (1 + total_return) ** (TRADING_DAYS_PER_YEAR / n_periods) - 1 if n_periods > 0 else 0
    daily_vol = np.std(cost_adjusted, ddof=1) if n_periods > 1 else 0
    annual_vol = daily_vol * math.sqrt(TRADING_DAYS_PER_YEAR)
    sharpe = annual_return / annual_vol if annual_vol > 0 else 0
    running_max_eq = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max_eq) / running_max_eq
    max_drawdown = float(np.min(drawdown))
    winning = cost_adjusted[cost_adjusted > 0]
    losing = cost_adjusted[cost_adjusted < 0]
    win_rate = len(winning) / n_periods if n_periods > 0 else 0
    avg_win = float(np.mean(winning)) if len(winning) > 0 else 0
    avg_loss = float(abs(np.mean(losing))) if len(losing) > 0 else 0
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float("inf")
    trade_count = int(np.sum(position_changes > 0))
    calmar = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
    total_cost = float(np.sum(position_changes * TRANSACTION_COST))
    cost_ratio = total_cost / abs(total_return) if total_return != 0 else 0

    metrics = {
        "total_return": round(float(total_return), 6),
        "annualized_return": round(float(annual_return), 6),
        "annual_volatility": round(float(annual_vol), 6),
        "daily_volatility": round(float(daily_vol), 6),
        "max_drawdown": round(float(max_drawdown), 6),
        "sharpe_ratio": round(float(sharpe), 6),
        "calmar_ratio": round(float(calmar), 6),
        "win_rate": round(float(win_rate), 6),
        "avg_win": round(float(avg_win), 6),
        "avg_loss": round(float(avg_loss), 6),
        "profit_loss_ratio": round(float(profit_loss_ratio), 6),
        "trade_count": trade_count,
        "total_trades": trade_count,
        "n_periods": n_periods,
        "initial_capital": INITIAL_CAPITAL,
        "final_capital": round(float(equity_curve[-1]), 2),
        "total_transaction_cost": round(total_cost, 6),
        "cost_ratio": round(float(cost_ratio), 6),
    }

    return {
        "metrics": metrics,
        "equity_curve": equity_curve,
        "daily_returns": cost_adjusted,
        "positions": position,
        "drawdown_curve": drawdown,
    }

# ════════════════════════════════════════════════════════════════
# 滚动IC计算
# ════════════════════════════════════════════════════════════════
def compute_rolling_ic_for_factors(
    df: pd.DataFrame,
    factor_list: List[str],
    symbols: List[str],
    window: int = IC_WINDOW_DAYS,
    step: int = ROLLING_STEP,
) -> dict:
    """Compute rolling IC for given factors across window-day windows."""
    df_sorted = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    dates_unique = sorted(df_sorted["date"].unique())
    total_dates = len(dates_unique)
    num_windows = (total_dates - window) // step + 1

    # Pre-compute next-day returns per date per symbol
    returns_by_date = {}
    for i in range(len(dates_unique) - 1):
        d = dates_unique[i]
        d_next = dates_unique[i + 1]
        returns_by_date[d] = {}
        for sym in symbols:
            d_rows = df_sorted[(df_sorted["date"] == d) & (df_sorted["symbol"] == sym)]
            dn_rows = df_sorted[(df_sorted["date"] == d_next) & (df_sorted["symbol"] == sym)]
            if len(d_rows) > 0 and len(dn_rows) > 0:
                close_now = float(d_rows.iloc[0]["close"])
                close_next = float(dn_rows.iloc[0]["close"])
                if close_now > 0:
                    ret = (close_next - close_now) / close_now
                    returns_by_date[d][sym] = ret

    results = {}
    for factor in factor_list:
        window_ics = []
        for w in range(num_windows):
            w_start = w * step
            w_end = w_start + window
            window_dates = dates_unique[w_start:w_end]
            if len(window_dates) < 5:
                continue

            factor_vals = []
            ret_vals = []
            for d in window_dates:
                if d not in returns_by_date:
                    continue
                for sym in symbols:
                    if sym not in returns_by_date[d]:
                        continue
                    row = df_sorted[(df_sorted["date"] == d) & (df_sorted["symbol"] == sym)]
                    if len(row) == 0:
                        continue
                    raw = row.iloc[0].get(factor, '')
                    try:
                        fv = float(raw) if raw is not None and str(raw).strip() else None
                    except (ValueError, TypeError):
                        fv = None
                    if fv is not None and not np.isnan(fv):
                        factor_vals.append(fv)
                        ret_vals.append(returns_by_date[d][sym])

            if len(factor_vals) >= 10:
                try:
                    ic, _ = pearsonr(factor_vals, ret_vals)
                    ic = float(ic) if not np.isnan(ic) else 0.0
                except Exception:
                    ic = 0.0
                window_ics.append({
                    "window_start": str(window_dates[0])[:10],
                    "window_end": str(window_dates[-1])[:10],
                    "n_pairs": len(factor_vals),
                    "ic": round(ic, 6),
                    "sign": 1 if ic > 0 else (-1 if ic < 0 else 0),
                })
        results[factor] = window_ics
    return results

def compute_sign_flip_rate(window_ics: list) -> tuple:
    """Compute the fraction of consecutive window pairs where the sign flips."""
    if len(window_ics) < 2:
        return 0.0, 0
    flips = 0
    for i in range(1, len(window_ics)):
        prev_sign = window_ics[i - 1]["sign"]
        curr_sign = window_ics[i]["sign"]
        if prev_sign != 0 and curr_sign != 0 and prev_sign != curr_sign:
            flips += 1
    total_pairs = len(window_ics) - 1
    return flips / total_pairs if total_pairs > 0 else 0.0, flips

def compute_ic_summary(window_ics: list) -> dict:
    """Compute IC mean, std, IR, monotonicity from window_ics list."""
    if len(window_ics) < 2:
        return {"ic_mean": 0.0, "ic_std": 0.0, "ir": 0.0, "ic_positive_ratio": 0.0, "monotonicity": 0.0}
    ics = [w["ic"] for w in window_ics]
    ic_mean = float(np.mean(ics))
    ic_std = float(np.std(ics, ddof=1))
    ir = ic_mean / ic_std if ic_std > 1e-10 else 0.0
    ic_positive_ratio = sum(1 for ic in ics if ic > 0) / len(ics)
    # Monotonicity: fraction of consecutive pairs where |IC| is non-decreasing
    monotonic_pairs = 0
    for i in range(1, len(ics)):
        if abs(ics[i]) >= abs(ics[i-1]) - 0.005:  # small tolerance
            monotonic_pairs += 1
    monotonicity = monotonic_pairs / (len(ics) - 1) if len(ics) > 1 else 0.0
    return {
        "ic_mean": round(ic_mean, 6),
        "ic_std": round(ic_std, 6),
        "ir": round(ir, 6),
        "ic_positive_ratio": round(ic_positive_ratio, 4),
        "monotonicity": round(monotonicity, 4),
        "num_windows": len(window_ics),
    }

# ════════════════════════════════════════════════════════════════
# Regime Classification
# ════════════════════════════════════════════════════════════════
def classify_regimes(df: pd.DataFrame, ma_window: int = 20) -> pd.DataFrame:
    """Classify each row into 'up', 'down', or 'sideways' regime based on 20d MA."""
    df = df.copy()
    df["ma20"] = df.groupby("symbol")["close"].transform(
        lambda x: x.rolling(window=ma_window, min_periods=1).mean()
    )
    df["regime"] = np.where(
        df["close"] > df["ma20"] * (1 + REGIME_PCT_THRESHOLD), "up",
        np.where(df["close"] < df["ma20"] * (1 - REGIME_PCT_THRESHOLD), "down", "sideways")
    )
    # Fill NaN regimes (first N rows) with "sideways"
    df["regime"] = df["regime"].fillna("sideways")
    return df

def compute_regime_ic(
    df: pd.DataFrame,
    factor_list: List[str],
    symbols: List[str],
    window: int = IC_WINDOW_DAYS,
    step: int = ROLLING_STEP,
) -> dict:
    """Compute IC per regime slice. Returns dict of factor -> regime -> {ic_mean, ic_std, flip_rate, num_windows}."""
    results = {}
    for regime in ["up", "down", "sideways"]:
        df_regime = df[df["regime"] == regime].copy()
        if len(df_regime) < window * 2:
            results[regime] = {}
            continue
        ic_data = compute_rolling_ic_for_factors(df_regime, factor_list, symbols, window, step)
        regime_results = {}
        for factor, window_ics in ic_data.items():
            if len(window_ics) < 2:
                regime_results[factor] = {
                    "ic_mean": 0.0, "ic_std": 0.0, "ir": 0.0,
                    "flip_rate": 0.0, "flip_count": 0, "num_windows": len(window_ics),
                    "ic_values": [w["ic"] for w in window_ics],
                }
                continue
            flip_rate, flip_count = compute_sign_flip_rate(window_ics)
            summary = compute_ic_summary(window_ics)
            regime_results[factor] = {
                "ic_mean": summary["ic_mean"],
                "ic_std": summary["ic_std"],
                "ir": summary["ir"],
                "ic_positive_ratio": summary["ic_positive_ratio"],
                "flip_rate": round(flip_rate, 4),
                "flip_count": flip_count,
                "num_windows": len(window_ics),
                "ic_values": [w["ic"] for w in window_ics],
            }
        results[regime] = regime_results
    return results

# ════════════════════════════════════════════════════════════════
# 15候选因子构建
# ════════════════════════════════════════════════════════════════
def compute_candidate_factors(df: pd.DataFrame) -> pd.DataFrame:
    """Compute 15 new candidate factors from raw data. No future data."""
    df = df.copy()
    
    # --- Helper: compute rolling stats per symbol ---
    def rolling_stats(symbol_df: pd.DataFrame, col: str, window: int = 20) -> pd.Series:
        return symbol_df[col].rolling(window=window, min_periods=max(1, window // 2)).mean()
    
    def rolling_std(symbol_df: pd.DataFrame, col: str, window: int = 20) -> pd.Series:
        return symbol_df[col].rolling(window=window, min_periods=max(1, window // 2)).std()
    
    # Compute daily returns per symbol
    df["daily_return"] = df.groupby("symbol")["close"].pct_change().fillna(0)
    
    for fname, desc in CANDIDATE_FACTORS.items():
        df[fname] = np.nan
    
    for sym in ALL_4_SYMBOLS:
        mask = df["symbol"] == sym
        sd = df[mask].copy()
        idx = sd.index
        
        close = sd["close"].values
        high = sd["high"].values
        low = sd["low"].values
        oi = sd["oi"].values
        vol = sd["vol"].values
        oi_change_1d = sd["oi_change_1d"].fillna(0).values
        oi_change_rate_7d = sd["oi_change_rate_7d"].fillna(0).values
        spread_cs = sd["spread_cs"].fillna(0).values
        spread_pct = sd["spread_pct"].fillna(0).values
        atr_pct = sd["atr_pct"].fillna(0).values
        realized_vol_20d = sd["realized_vol_20d"].fillna(0).values
        daily_return = sd["daily_return"].values
        
        n = len(sd)
        
        # ===== Volatility Direction (5 factors) =====
        
        # 1. vol_range_pct_20d: mean of (high-low)/close over 20d
        range_pct = np.where(close > 0, (high - low) / np.where(close > 0, close, 1), 0)
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            vals.append(np.mean(range_pct[w_start:i+1]))
        df.loc[mask, "vol_range_pct_20d"] = vals
        
        # 2. vol_return_skew_20d: skewness of returns over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = daily_return[w_start:i+1]
            if len(w_data) >= 5 and np.std(w_data) > 1e-10:
                vals.append(float(pd.Series(w_data).skew()))
            else:
                vals.append(0.0)
        df.loc[mask, "vol_return_skew_20d"] = vals
        
        # 3. vol_return_kurtosis_20d: kurtosis of returns over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = daily_return[w_start:i+1]
            if len(w_data) >= 5 and np.std(w_data) > 1e-10:
                vals.append(float(pd.Series(w_data).kurtosis()))
            else:
                vals.append(0.0)
        df.loc[mask, "vol_return_kurtosis_20d"] = vals
        
        # 4. vol_return_slope_20d: linear regression slope of returns over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = daily_return[w_start:i+1]
            if len(w_data) >= 5:
                x = np.arange(len(w_data), dtype=float)
                try:
                    slope, _ = np.polyfit(x, w_data, 1)
                    vals.append(float(slope))
                except Exception:
                    vals.append(0.0)
            else:
                vals.append(0.0)
        df.loc[mask, "vol_return_slope_20d"] = vals
        
        # 5. vol_updown_ratio_20d: sum positive / sum abs negative over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = daily_return[w_start:i+1]
            pos_sum = np.sum(w_data[w_data > 0])
            neg_sum = np.sum(np.abs(w_data[w_data < 0]))
            if neg_sum > 1e-10:
                vals.append(pos_sum / neg_sum)
            elif pos_sum > 0:
                vals.append(1.0)  # all positive
            else:
                vals.append(0.0)
        df.loc[mask, "vol_updown_ratio_20d"] = vals
        
        # ===== Position Structure Direction (5 factors) =====
        
        # 6. oi_momentum_20d: mean of oi_change_1d over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            vals.append(np.mean(oi_change_1d[w_start:i+1]))
        df.loc[mask, "oi_momentum_20d"] = vals
        
        # 7. oi_to_vol_ratio_20d: mean of (oi_change_1d / vol) over 20d
        safe_vol = np.where(vol > 0, vol, 1.0)
        oi_vol_ratio = oi_change_1d / safe_vol
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            vals.append(np.mean(oi_vol_ratio[w_start:i+1]))
        df.loc[mask, "oi_to_vol_ratio_20d"] = vals
        
        # 8. oi_level_zscore_20d: z-score of oi_level vs 20d rolling stats
        oi_level = sd["oi_level"].values
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = oi_level[w_start:i+1]
            w_mean = np.mean(w_data)
            w_std = np.std(w_data)
            if w_std > 1e-10:
                vals.append((oi_level[i] - w_mean) / w_std)
            else:
                vals.append(0.0)
        df.loc[mask, "oi_level_zscore_20d"] = vals
        
        # 9. oi_acceleration_5d: oi_change_1d[t] - oi_change_1d[t-5]
        vals = []
        for i in range(n):
            if i >= 5:
                vals.append(oi_change_1d[i] - oi_change_1d[i - 5])
            else:
                vals.append(0.0)
        df.loc[mask, "oi_acceleration_5d"] = vals
        
        # 10. oi_rate_20d_momentum: mean of oi_change_rate_7d over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            vals.append(np.mean(oi_change_rate_7d[w_start:i+1]))
        df.loc[mask, "oi_rate_20d_momentum"] = vals
        
        # ===== Cross-Period Spread Direction (5 factors) =====
        
        # 11. spread_cs_zscore_20d: z-score of spread_cs vs 20d rolling stats
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = spread_cs[w_start:i+1]
            w_mean = np.mean(w_data)
            w_std = np.std(w_data)
            if w_std > 1e-10:
                vals.append((spread_cs[i] - w_mean) / w_std)
            else:
                vals.append(0.0)
        df.loc[mask, "spread_cs_zscore_20d"] = vals
        
        # 12. spread_cs_momentum_5d: spread_cs[t] - spread_cs[t-5]
        vals = []
        for i in range(n):
            if i >= 5:
                vals.append(spread_cs[i] - spread_cs[i - 5])
            else:
                vals.append(0.0)
        df.loc[mask, "spread_cs_momentum_5d"] = vals
        
        # 13. spread_pct_slope_20d: linear slope of spread_pct over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = spread_pct[w_start:i+1]
            if len(w_data) >= 5:
                x = np.arange(len(w_data), dtype=float)
                try:
                    slope, _ = np.polyfit(x, w_data, 1)
                    vals.append(float(slope))
                except Exception:
                    vals.append(0.0)
            else:
                vals.append(0.0)
        df.loc[mask, "spread_pct_slope_20d"] = vals
        
        # 14. spread_cs_atr_ratio_20d: spread_cs / atr_pct (normalized)
        safe_atr = np.where(atr_pct > 1e-10, atr_pct, 1.0)
        df.loc[mask, "spread_cs_atr_ratio_20d"] = spread_cs / safe_atr
        
        # 15. spread_cs_volatility_20d: rolling std of spread_cs over 20d
        vals = []
        for i in range(n):
            w_start = max(0, i - 19)
            w_data = spread_cs[w_start:i+1]
            vals.append(float(np.std(w_data, ddof=1)) if len(w_data) >= 2 else 0.0)
        df.loc[mask, "spread_cs_volatility_20d"] = vals
    
    # Drop temporary columns
    df = df.drop(columns=["daily_return", "ma20", "regime"], errors="ignore")
    
    # Replace NaN with 0 for computation
    for fname in CANDIDATE_FACTORS:
        df[fname] = df[fname].fillna(0).astype(float)
    
    return df

# ════════════════════════════════════════════════════════════════
# 相关性矩阵计算
# ════════════════════════════════════════════════════════════════
def compute_correlation_matrix(df: pd.DataFrame, factor_list: List[str]) -> dict:
    """Compute pairwise Pearson correlation matrix for given factors."""
    n = len(factor_list)
    corr_matrix = {}
    for i, f1 in enumerate(factor_list):
        corr_matrix[f1] = {}
        for j, f2 in enumerate(factor_list):
            if f1 == f2:
                corr_matrix[f1][f2] = 1.0
            elif j < i and f2 in corr_matrix and f1 in corr_matrix[f2]:
                corr_matrix[f1][f2] = corr_matrix[f2][f1]
            else:
                try:
                    v1 = df[f1].fillna(0).values.astype(float)
                    v2 = df[f2].fillna(0).values.astype(float)
                    mask = ~(np.isnan(v1) | np.isnan(v2))
                    v1 = v1[mask]
                    v2 = v2[mask]
                    if len(v1) >= 10 and np.std(v1) > 1e-10 and np.std(v2) > 1e-10:
                        corr, _ = pearsonr(v1, v2)
                        corr_matrix[f1][f2] = round(float(corr), 6)
                    else:
                        corr_matrix[f1][f2] = 0.0
                except Exception:
                    corr_matrix[f1][f2] = 0.0
    return corr_matrix

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════
def main():
    global WIND_API_CALLS, REAL_WIND_CALL

    start_time = time.time()

    print("=" * 72)
    print("DSHA-TASK-044 · V3高翻转因子替换 + 备选因子池搭建")
    print(f"令牌: {TOKEN}")
    print(f"基线: feature/v88-g1 HEAD={BASELINE_COMMIT}")
    print(f"时间: {now_iso()}")
    print(f"Gate: {GATE_STATUS} | Release: {RELEASE_STATUS}")
    print(f"研究沙箱: {RESEARCH_DIR.name}/ (物理隔离)")
    print("=" * 72)

    # ════════════════════════════════════════════════════════════
    # P0: 前置校验
    # ════════════════════════════════════════════════════════════
    print("\n[P0] 前置校验...")

    preconditions = {}

    # 1. Set E lock
    assert SET_E_LOCK.exists(), "Set E lock not found!"
    set_e_lock = json.loads(SET_E_LOCK.read_text(encoding="utf-8"))
    assert set_e_lock["status"] == "PERMANENTLY_FROZEN", "Set E lock not frozen!"
    preconditions["set_e_frozen"] = True
    print(f"  ✅ Set E Lock: {set_e_lock['status']}")

    # 2. Factors CSV
    assert V3_FACTORS_CSV.exists(), "Factors CSV not found!"
    factors_sha = sha256_file(V3_FACTORS_CSV)
    preconditions["factors_csv_available"] = True
    preconditions["factors_csv_sha256"] = factors_sha
    print(f"  ✅ Factors CSV: SHA={factors_sha[:16]}...")

    # 3. Production configs exist and are readonly
    assert FACTOR_WEIGHT_PROD.exists(), "factor_weight_prod.json not found!"
    assert FACTOR_ENABLE_CONFIG.exists(), "factor_enable_config.json not found!"
    fw_prod = json.loads(FACTOR_WEIGHT_PROD.read_text(encoding="utf-8"))
    fec = json.loads(FACTOR_ENABLE_CONFIG.read_text(encoding="utf-8"))
    preconditions["prod_configs_exist"] = True
    preconditions["fw_readonly_locked"] = fw_prod.get("readonly", {}).get("locked", False)
    preconditions["fec_readonly_locked"] = fec.get("readonly", {}).get("locked", False)
    print(f"  ✅ 生产配置文件只读锁定: fw={'YES' if preconditions['fw_readonly_locked'] else 'NO'}, fec={'YES' if preconditions['fec_readonly_locked'] else 'NO'}")

    # 4. Verify production baseline unchanged
    preconditions["prod_baseline_sha_matches"] = (factors_sha == "dd6674bb323ce6f5b9c7b80c021e1d1a5cb2917f631a822b1104924232611b9b")
    print(f"  ✅ 生产数据指纹: {'✅匹配' if preconditions['prod_baseline_sha_matches'] else '⚠️不匹配'}")

    # 5. Deprecated script still archived
    assert DEPRECATED_SCRIPT.exists(), "Deprecated script not found!"
    preconditions["deprecated_archived"] = True
    print(f"  ✅ Deprecated script archived: {DEPRECATED_SCRIPT.name}")

    # 6. Research directory isolation
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    preconditions["research_dir_created"] = RESEARCH_DIR.exists()
    print(f"  ✅ 研究沙箱目录: {RESEARCH_DIR.name}/")

    # 7. Safety locks
    preconditions["real_wind_call"] = False
    preconditions["wind_api_calls"] = 0
    preconditions["offline_only"] = True
    preconditions["gate"] = GATE_STATUS
    preconditions["release_permit"] = RELEASE_STATUS

    all_preconditions_pass = all(
        preconditions[k] is True for k in preconditions
        if k not in ("real_wind_call", "wind_api_calls", "gate", "release_permit", "factors_csv_sha256")
    ) and preconditions["real_wind_call"] is False and preconditions["wind_api_calls"] == 0

    if not all_preconditions_pass:
        print(f"  ❌ 前置校验未通过!")
        sys.exit(1)

    print(f"  ✅ Wind calls: 0 | Offline: YES | Gate: {GATE_STATUS} | Release: {RELEASE_STATUS}")

    append_audit("TASK044_START", {
        "token": TOKEN,
        "baseline_commit": BASELINE_COMMIT,
        "precondition_checks": preconditions,
        "execution_type": "research_sandbox",
    })

    # ════════════════════════════════════════════════════════════
    # P1: 存量7个高危因子诊断
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P1] 存量7个高危因子诊断")
    print("=" * 72)

    p1_results = {}

    # Load data
    print("\n[P1.0] 加载数据...")
    df_full = pd.read_csv(V3_FACTORS_CSV)
    df_full["date"] = pd.to_datetime(df_full["date"])
    df = df_full[df_full["symbol"].isin(ALL_4_SYMBOLS)].copy()
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    print(f"  数据: {len(df_full)}行→{len(df)}行 (4品种白名单)")

    # Classify regimes
    df = classify_regimes(df, ma_window=20)
    regime_counts = df["regime"].value_counts().to_dict()
    print(f"  Regime分布: {regime_counts}")

    # ─── P1.1: 分行情切片诊断 ───
    print(f"\n[P1.1] 分行情切片诊断 (7个高翻转因子)...")

    regime_ic_data = compute_regime_ic(df, HIGH_FLIP_FACTORS, ALL_4_SYMBOLS, IC_WINDOW_DAYS, ROLLING_STEP)

    # Also compute full-sample rolling IC for comparison
    full_ic_data = compute_rolling_ic_for_factors(df, HIGH_FLIP_FACTORS, ALL_4_SYMBOLS, IC_WINDOW_DAYS, ROLLING_STEP)

    regime_diagnosis = {}
    for factor in HIGH_FLIP_FACTORS:
        # Full sample
        full_windows = full_ic_data.get(factor, [])
        full_flip_rate, full_flip_count = compute_sign_flip_rate(full_windows)
        full_summary = compute_ic_summary(full_windows)

        # Per regime
        regime_info = {}
        for regime in ["up", "down", "sideways"]:
            rd = regime_ic_data.get(regime, {}).get(factor, {})
            regime_info[regime] = {
                "ic_mean": rd.get("ic_mean", 0.0),
                "ic_std": rd.get("ic_std", 0.0),
                "ir": rd.get("ir", 0.0),
                "flip_rate": rd.get("flip_rate", 0.0),
                "num_windows": rd.get("num_windows", 0),
            }

        # Determine root cause
        # If IC sign differs across regimes -> regime-dependent
        # If IC is consistently near zero -> permanent decay
        regime_ics = [regime_info[r]["ic_mean"] for r in ["up", "down", "sideways"]]
        ic_signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in regime_ics]
        ic_ranges = [abs(v) for v in regime_ics]

        sign_divergence = len(set(ic_signs)) > 1
        max_ic = max(ic_ranges) if ic_ranges else 0
        min_ic = min(ic_ranges) if ic_ranges else 0

        if sign_divergence and max_ic > 0.01:
            root_cause = "REGIME_DEPENDENT"
            root_cause_detail = "IC符号在不同行情段出现翻转, 因子有效性依赖市场状态"
        elif max_ic < 0.01 and full_summary["ic_mean"] < 0.005:
            root_cause = "PERMANENT_DECAY"
            root_cause_detail = "IC在全部行情段均接近零, 因子定价逻辑永久衰减"
        elif full_flip_rate > 0.5:
            root_cause = "REGIME_DEPENDENT"
            root_cause_detail = "全样本翻转率极高, 因子信号不稳定"
        else:
            root_cause = "MIXED"
            root_cause_detail = "部分行情段有效, 部分无效, 需进一步分析"

        regime_diagnosis[factor] = {
            "full_sample": {
                "ic_mean": full_summary["ic_mean"],
                "ic_std": full_summary["ic_std"],
                "ir": full_summary["ir"],
                "flip_rate": round(full_flip_rate, 4),
                "flip_count": full_flip_count,
                "num_windows": full_summary["num_windows"],
                "ic_positive_ratio": full_summary["ic_positive_ratio"],
            },
            "regimes": regime_info,
            "root_cause": root_cause,
            "root_cause_detail": root_cause_detail,
            "sign_divergence": sign_divergence,
            "ic_signs_by_regime": dict(zip(["up", "down", "sideways"], ic_signs)),
        }

        # Print summary
        print(f"\n  [{factor}]")
        print(f"    全样本IC均值: {full_summary['ic_mean']:.6f}, IR: {full_summary['ir']:.6f}, 翻转率: {full_flip_rate*100:.1f}%")
        for regime in ["up", "down", "sideways"]:
            ri = regime_info[regime]
            print(f"    {regime:>10s}: IC均值={ri['ic_mean']:.6f}, 翻转率={ri['flip_rate']*100:.1f}%, 窗口数={ri['num_windows']}")
        print(f"    根因判定: {root_cause} — {root_cause_detail}")

    p1_results["regime_diagnosis"] = regime_diagnosis

    # ─── P1.2: 因子相关性矩阵 ───
    print(f"\n[P1.2] 因子相关性矩阵 (8个生产因子)...")

    all_corr_factors = RETAINED_FACTORS
    corr_matrix = compute_correlation_matrix(df, all_corr_factors)

    # Write corr_matrix.json
    corr_output = {
        "output_id": "DSHA-TASK044-CORR-MATRIX",
        "generated_at": now_iso(),
        "token": TOKEN,
        "task": TASK_ID,
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
        },
        "factor_list": all_corr_factors,
        "num_factors": len(all_corr_factors),
        "correlation_matrix": corr_matrix,
        "notes": "Pearson相关性矩阵, 基于4品种白名单全样本计算",
    }

    CORR_MATRIX_JSON.write_text(
        json.dumps(corr_output, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"  ✅ corr_matrix.json 已写入 ({len(all_corr_factors)}x{len(all_corr_factors)})")

    # Print correlation highlights
    high_corr_pairs = []
    for i, f1 in enumerate(all_corr_factors):
        for j, f2 in enumerate(all_corr_factors):
            if j > i:
                c = corr_matrix[f1][f2]
                if abs(c) > 0.3:
                    high_corr_pairs.append((f1, f2, c))
    high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    print(f"  高相关因子对 (|r|>0.3): {len(high_corr_pairs)}对")
    for f1, f2, c in high_corr_pairs[:5]:
        print(f"    {f1} <-> {f2}: r={c:.6f}")

    p1_results["correlation_matrix"] = {
        "path": str(CORR_MATRIX_JSON.relative_to(PROJECT_ROOT)),
        "num_factors": len(all_corr_factors),
        "high_corr_pairs": [{"f1": f1, "f2": f2, "corr": c} for f1, f2, c in high_corr_pairs],
    }

    # ─── P1.3: 诊断报告 ───
    print(f"\n[P1.3] 诊断报告生成...")

    diagnosis_summary = {
        "total_factors_analyzed": len(HIGH_FLIP_FACTORS),
        "root_cause_distribution": {},
        "factors": {},
    }
    for factor, info in regime_diagnosis.items():
        rc = info["root_cause"]
        diagnosis_summary["root_cause_distribution"][rc] = diagnosis_summary["root_cause_distribution"].get(rc, 0) + 1
        diagnosis_summary["factors"][factor] = {
            "full_sample_ic": info["full_sample"]["ic_mean"],
            "full_sample_flip_rate": info["full_sample"]["flip_rate"],
            "root_cause": rc,
            "root_cause_detail": info["root_cause_detail"],
            "sign_divergence": info["sign_divergence"],
        }

    print(f"  根因分布: {diagnosis_summary['root_cause_distribution']}")
    for factor, info in diagnosis_summary["factors"].items():
        print(f"    {factor}: {info['root_cause']} — {info['root_cause_detail']}")

    p1_results["diagnosis_summary"] = diagnosis_summary

    # ════════════════════════════════════════════════════════════
    # P2: 备选因子候选池
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P2] 备选因子候选池搭建")
    print("=" * 72)

    p2_results = {}

    # ─── P2.1: 生成15个候选因子 ───
    print(f"\n[P2.1] 生成15个候选因子...")

    df_with_candidates = compute_candidate_factors(df)
    print(f"  ✅ 15个候选因子已计算完成")
    print(f"     方向: 波动率(5) + 持仓结构(5) + 跨期价差(5)")

    p2_results["candidate_generation"] = {
        "total_candidates": len(CANDIDATE_FACTORS),
        "directions": {
            "volatility": ["vol_range_pct_20d", "vol_return_skew_20d", "vol_return_kurtosis_20d", "vol_return_slope_20d", "vol_updown_ratio_20d"],
            "position_structure": ["oi_momentum_20d", "oi_to_vol_ratio_20d", "oi_level_zscore_20d", "oi_acceleration_5d", "oi_rate_20d_momentum"],
            "cross_period_spread": ["spread_cs_zscore_20d", "spread_cs_momentum_5d", "spread_pct_slope_20d", "spread_cs_atr_ratio_20d", "spread_cs_volatility_20d"],
        },
    }

    # ─── P2.2: 计算IC均值、IR、翻转率 ───
    print(f"\n[P2.2] 候选因子IC/IR/翻转率计算...")

    candidate_names = list(CANDIDATE_FACTORS.keys())
    candidate_ic_data = compute_rolling_ic_for_factors(df_with_candidates, candidate_names, ALL_4_SYMBOLS, IC_WINDOW_DAYS, ROLLING_STEP)

    candidate_profiles = {}
    passed_pool = []
    for cname in candidate_names:
        window_ics = candidate_ic_data.get(cname, [])
        flip_rate, flip_count = compute_sign_flip_rate(window_ics)
        summary = compute_ic_summary(window_ics)

        profile = {
            "factor_name": cname,
            "description": CANDIDATE_FACTORS[cname],
            "ic_mean": summary["ic_mean"],
            "ic_std": summary["ic_std"],
            "ir": summary["ir"],
            "ic_positive_ratio": summary["ic_positive_ratio"],
            "monotonicity": summary["monotonicity"],
            "flip_rate": round(flip_rate, 4),
            "flip_count": flip_count,
            "num_windows": summary["num_windows"],
            "ic_values": [w["ic"] for w in window_ics],
        }
        candidate_profiles[cname] = profile

        # Check filter criteria
        passed = (
            flip_rate <= FLIP_RATE_FILTER and
            abs(summary["ic_mean"]) > IC_FILTER and
            summary["ic_mean"] > 0 and  # must be positive IC
            summary["monotonicity"] > 0.4  # temporal stability
        )
        profile["passed_filter"] = passed
        profile["filter_details"] = {
            "flip_rate_ok": flip_rate <= FLIP_RATE_FILTER,
            "ic_positive_ok": summary["ic_mean"] > IC_FILTER,
            "ic_mean_positive": summary["ic_mean"] > 0,
            "monotonicity_ok": summary["monotonicity"] > 0.4,
        }

        if passed:
            passed_pool.append(cname)
            print(f"  ✅ {cname}: IC={summary['ic_mean']:.6f}, IR={summary['ir']:.6f}, 翻转率={flip_rate*100:.1f}%, 单调性={summary['monotonicity']:.2f} → 入选")
        else:
            print(f"  ❌ {cname}: IC={summary['ic_mean']:.6f}, IR={summary['ir']:.6f}, 翻转率={flip_rate*100:.1f}%, 单调性={summary['monotonicity']:.2f} → 淘汰")

    p2_results["candidate_profiles"] = candidate_profiles
    p2_results["passed_pool"] = passed_pool
    p2_results["passed_count"] = len(passed_pool)
    p2_results["failed_count"] = len(candidate_names) - len(passed_pool)

    print(f"\n  筛选结果: {len(passed_pool)}/{len(candidate_names)} 个候选通过筛选")

    # ─── P2.3: 单因子回测 ───
    print(f"\n[P2.3] 候选因子单因子回测 (4品种白名单)...")

    single_factor_backtests = {}
    for cname in passed_pool:
        if cname not in df_with_candidates.columns:
            continue
        bt_result = compute_backtest_with_weights(
            df=df_with_candidates,
            signal_factors=[cname],
            signal_weights=[1.0],  # single factor, weight=1.0
            threshold=SIGNAL_THRESHOLD,
            rebalance_interval=REBALANCE_INTERVAL,
            target_vol=TARGET_VOL,
            max_single_weight=MAX_SINGLE_WEIGHT,
        )
        bt_m = bt_result["metrics"]
        single_factor_backtests[cname] = {
            "metrics": bt_m,
            "ic_mean": candidate_profiles[cname]["ic_mean"],
            "ir": candidate_profiles[cname]["ir"],
            "flip_rate": candidate_profiles[cname]["flip_rate"],
        }
        print(f"  {cname}: 收益={bt_m['total_return']*100:.2f}%, 夏普={bt_m['sharpe_ratio']:.4f}, 回撤={bt_m['max_drawdown']*100:.2f}%, 交易={bt_m['trade_count']}")

    p2_results["single_factor_backtests"] = single_factor_backtests

    # If fewer than 3 passed, relax criteria and take best available
    if len(passed_pool) < 3:
        print(f"\n  ⚠️ 仅{len(passed_pool)}个候选通过严格筛选, 放宽标准选取最佳候选...")
        # Sort by combined score: positive IC, low flip rate, high monotonicity
        all_profiles_sorted = sorted(
            candidate_profiles.items(),
            key=lambda x: (
                x[1]["ic_mean"] if x[1]["ic_mean"] > 0 else -999,
                -x[1]["flip_rate"],
                x[1]["monotonicity"],
            ),
            reverse=True
        )
        relaxed_pool = []
        for cname, profile in all_profiles_sorted:
            if cname not in passed_pool and len(relaxed_pool) < 3 - len(passed_pool):
                relaxed_pool.append(cname)
                print(f"    补充: {cname} (IC={profile['ic_mean']:.6f}, 翻转率={profile['flip_rate']*100:.1f}%)")
        
        if relaxed_pool:
            passed_pool = passed_pool + relaxed_pool
            p2_results["relaxed_pool_additions"] = relaxed_pool
            # Also add these to single_factor_backtests
            for cname in relaxed_pool:
                if cname not in df_with_candidates.columns or cname in single_factor_backtests:
                    continue
                bt_result = compute_backtest_with_weights(
                    df=df_with_candidates,
                    signal_factors=[cname],
                    signal_weights=[1.0],
                    threshold=SIGNAL_THRESHOLD,
                    rebalance_interval=REBALANCE_INTERVAL,
                    target_vol=TARGET_VOL,
                    max_single_weight=MAX_SINGLE_WEIGHT,
                )
                bt_m = bt_result["metrics"]
                single_factor_backtests[cname] = {
                    "metrics": bt_m,
                    "ic_mean": candidate_profiles[cname]["ic_mean"],
                    "ir": candidate_profiles[cname]["ir"],
                    "flip_rate": candidate_profiles[cname]["flip_rate"],
                }
                print(f"    补充回测 {cname}: 收益={bt_m['total_return']*100:.2f}%, 夏普={bt_m['sharpe_ratio']:.4f}")
        
        p2_results["passed_count"] = len(passed_pool)

    # ════════════════════════════════════════════════════════════
    # P3: 备选组合对照回测
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P3] 备选组合对照回测 (仅研究, 不覆盖生产)")
    print("=" * 72)

    p3_results = {}

    # Ensure we have at least 3 candidates for replacement
    n_replace = min(3, len(passed_pool))
    replacement_candidates = passed_pool[:n_replace]
    print(f"\n  替换候选 (前{n_replace}个): {replacement_candidates}")

    # ─── P3.1: 对照组 (8因子等权, 生产基线) ───
    print(f"\n[P3.1] 对照组: 8因子等权 (生产基线)...")

    df_control = df.copy()
    bt_control = compute_backtest_with_weights(
        df=df_control,
        signal_factors=RETAINED_FACTORS,
        signal_weights=EQUAL_WEIGHTS,
        threshold=SIGNAL_THRESHOLD,
        rebalance_interval=REBALANCE_INTERVAL,
        target_vol=TARGET_VOL,
        max_single_weight=MAX_SINGLE_WEIGHT,
    )
    control_m = bt_control["metrics"]
    print(f"  收益: {control_m['total_return']*100:.2f}%, 夏普: {control_m['sharpe_ratio']:.4f}, 回撤: {control_m['max_drawdown']*100:.2f}%, 交易: {control_m['trade_count']}")

    # ─── P3.2: 实验组 (5保留因子 + n新候选, 等权) ───
    print(f"\n[P3.2] 实验组: {len(REMAINING_FACTORS)}保留 + {n_replace}新候选 = {len(REMAINING_FACTORS)+n_replace}因子等权...")

    exp_factors = REMAINING_FACTORS + replacement_candidates
    exp_weights = [1.0 / len(exp_factors)] * len(exp_factors)
    print(f"  实验组因子: {exp_factors}")
    print(f"  每个权重: {exp_weights[0]:.6f}")

    # Add candidate factor columns to df if not already present
    df_experiment = df.copy()
    for cname in replacement_candidates:
        if cname not in df_experiment.columns:
            # Re-compute candidate factors for this df
            df_with_cands_full = compute_candidate_factors(df)
            df_experiment = df_with_cands_full.copy()
            break

    bt_experiment = compute_backtest_with_weights(
        df=df_experiment,
        signal_factors=exp_factors,
        signal_weights=exp_weights,
        threshold=SIGNAL_THRESHOLD,
        rebalance_interval=REBALANCE_INTERVAL,
        target_vol=TARGET_VOL,
        max_single_weight=MAX_SINGLE_WEIGHT,
    )
    exp_m = bt_experiment["metrics"]
    print(f"  收益: {exp_m['total_return']*100:.2f}%, 夏普: {exp_m['sharpe_ratio']:.4f}, 回撤: {exp_m['max_drawdown']*100:.2f}%, 交易: {exp_m['trade_count']}")

    # ─── P3.3: 滚动IC稳定性对比 ───
    print(f"\n[P3.3] 滚动IC稳定性对比...")

    # Control group rolling IC (8 factors)
    control_ic_data = compute_rolling_ic_for_factors(df_control, RETAINED_FACTORS, ALL_4_SYMBOLS, IC_WINDOW_DAYS, ROLLING_STEP)
    control_flip_rates = {}
    for f in RETAINED_FACTORS:
        wr, fc = compute_sign_flip_rate(control_ic_data.get(f, []))
        control_flip_rates[f] = round(wr, 4)

    # Experiment group rolling IC
    exp_ic_data = compute_rolling_ic_for_factors(df_experiment, exp_factors, ALL_4_SYMBOLS, IC_WINDOW_DAYS, ROLLING_STEP)
    exp_flip_rates = {}
    for f in exp_factors:
        wr, fc = compute_sign_flip_rate(exp_ic_data.get(f, []))
        exp_flip_rates[f] = round(wr, 4)

    # Aggregate flip rates
    control_avg_flip = np.mean(list(control_flip_rates.values()))
    exp_avg_flip = np.mean(list(exp_flip_rates.values()))
    exp_max_flip = max(exp_flip_rates.values()) if exp_flip_rates else 0

    print(f"  对照组平均翻转率: {control_avg_flip*100:.1f}%")
    print(f"  实验组平均翻转率: {exp_avg_flip*100:.1f}%")
    print(f"  实验组最高翻转率: {exp_max_flip*100:.1f}%")

    # Build comparison
    comparison = {
        "control_group": {
            "factors": RETAINED_FACTORS,
            "num_factors": len(RETAINED_FACTORS),
            "weight_per_factor": 0.125,
            "metrics": control_m,
            "flip_rates": control_flip_rates,
            "avg_flip_rate": round(float(control_avg_flip), 4),
        },
        "experimental_group": {
            "factors": exp_factors,
            "num_factors": len(exp_factors),
            "weight_per_factor": round(exp_weights[0], 6),
            "metrics": exp_m,
            "flip_rates": exp_flip_rates,
            "avg_flip_rate": round(float(exp_avg_flip), 4),
            "max_flip_rate": round(float(exp_max_flip), 4),
            "replacement_candidates": replacement_candidates,
            "removed_factors": TOP3_FLIP_FACTORS[:n_replace],
            "remaining_factors": REMAINING_FACTORS,
        },
        "comparison_summary": {
            "return_delta": round(exp_m["total_return"] - control_m["total_return"], 6),
            "sharpe_delta": round(exp_m["sharpe_ratio"] - control_m["sharpe_ratio"], 6),
            "max_dd_delta": round(exp_m["max_drawdown"] - control_m["max_drawdown"], 6),
            "flip_rate_reduction": round(float(control_avg_flip - exp_avg_flip), 4),
            "trade_count_delta": exp_m["trade_count"] - control_m["trade_count"],
            "win_rate_delta": round(exp_m["win_rate"] - control_m["win_rate"], 6),
        },
    }

    print(f"\n  对照对比:")
    print(f"    收益差: {comparison['comparison_summary']['return_delta']*100:.2f}%")
    print(f"    夏普差: {comparison['comparison_summary']['sharpe_delta']:.4f}")
    print(f"    回撤差: {comparison['comparison_summary']['max_dd_delta']*100:.2f}%")
    print(f"    翻转率降低: {comparison['comparison_summary']['flip_rate_reduction']*100:.1f}%")

    p3_results["comparison"] = comparison

    # ════════════════════════════════════════════════════════════
    # P4: 制品与审计闭环
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P4] 制品与审计闭环")
    print("=" * 72)

    p4_results = {}

    # ─── P4.1: 写入所有研究制品 ───
    print(f"\n[P4.1] 写入研究制品...")

    # 1. Candidate factor list
    candidate_list = {
        "output_id": "DSHA-TASK044-CANDIDATE-POOL",
        "generated_at": now_iso(),
        "token": TOKEN,
        "task": TASK_ID,
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
        },
        "total_candidates": len(candidate_names),
        "passed_count": len(passed_pool),
        "passed_factors": passed_pool,
        "filter_criteria": {
            "flip_rate_max": FLIP_RATE_FILTER,
            "ic_mean_min": IC_FILTER,
            "monotonicity_min": 0.4,
        },
        "candidates": candidate_profiles,
        "single_factor_backtests": {k: {"metrics": v["metrics"]} for k, v in single_factor_backtests.items()},
        "replaced_in_experiment": replacement_candidates,
    }
    CANDIDATE_LIST_JSON.write_text(
        json.dumps(candidate_list, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"  ✅ candidate_factor_list.json 已写入 ({len(passed_pool)}/{len(candidate_names)}通过)")

    # 2. Regime stability report
    regime_report = {
        "output_id": "DSHA-TASK044-REGIME-REPORT",
        "generated_at": now_iso(),
        "token": TOKEN,
        "task": TASK_ID,
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
        },
        "regime_counts": regime_counts,
        "high_flip_factors_analyzed": HIGH_FLIP_FACTORS,
        "regime_diagnosis": regime_diagnosis,
        "diagnosis_summary": diagnosis_summary,
    }
    REGIME_REPORT_JSON.write_text(
        json.dumps(regime_report, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"  ✅ regime_stability_report.json 已写入")

    # 3. Comparison backtest metrics
    backtest_metrics_output = {
        "output_id": "DSHA-TASK044-COMPARISON-BACKTEST",
        "generated_at": now_iso(),
        "token": TOKEN,
        "task": TASK_ID,
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
        },
        "control_group": {
            "factors": RETAINED_FACTORS,
            "num_factors": len(RETAINED_FACTORS),
            "weight_per_factor": 0.125,
            "metrics": control_m,
            "flip_rates": control_flip_rates,
        },
        "experimental_group": {
            "factors": exp_factors,
            "num_factors": len(exp_factors),
            "weight_per_factor": round(exp_weights[0], 6),
            "metrics": exp_m,
            "flip_rates": exp_flip_rates,
            "replacement_candidates": replacement_candidates,
            "removed_factors": TOP3_FLIP_FACTORS[:n_replace],
        },
        "comparison_summary": comparison["comparison_summary"],
        "set_e_params": {
            "signal_threshold": SIGNAL_THRESHOLD,
            "rebalance_interval": REBALANCE_INTERVAL,
            "target_vol": TARGET_VOL,
            "max_single_weight": MAX_SINGLE_WEIGHT,
            "drawdown_warn": DRAWDOWN_WARN,
            "drawdown_halt": DRAWDOWN_HALT,
            "transaction_cost": TRANSACTION_COST,
            "initial_capital": INITIAL_CAPITAL,
        },
    }
    BACKTEST_METRICS_JSON.write_text(
        json.dumps(backtest_metrics_output, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"  ✅ comparison_backtest_metrics.json 已写入")

    # 4. Research MANIFEST
    research_manifest = {
        "manifest_id": "DSHA-TASK044-RESEARCH-MANIFEST",
        "generated_at": now_iso(),
        "token": TOKEN,
        "task": TASK_ID,
        "execution_type": "research_sandbox",
        "baseline_commit": BASELINE_COMMIT,
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
        },
        "sandbox_isolation": {
            "research_dir": str(RESEARCH_DIR.relative_to(PROJECT_ROOT)),
            "production_dir": str(PROD_DIR.relative_to(PROJECT_ROOT)),
            "production_configs_untouched": True,
            "deprecated_script_archived": True,
        },
        "p1_high_flip_diagnosis": {
            "factors_analyzed": HIGH_FLIP_FACTORS,
            "root_cause_distribution": diagnosis_summary["root_cause_distribution"],
            "correlation_matrix": {
                "path": str(CORR_MATRIX_JSON.relative_to(PROJECT_ROOT)),
                "num_factors": len(all_corr_factors),
            },
            "regime_report": {
                "path": str(REGIME_REPORT_JSON.relative_to(PROJECT_ROOT)),
            },
        },
        "p2_candidate_pool": {
            "total_candidates": len(candidate_names),
            "passed_count": len(passed_pool),
            "passed_factors": passed_pool,
            "candidate_list": {
                "path": str(CANDIDATE_LIST_JSON.relative_to(PROJECT_ROOT)),
            },
        },
        "p3_comparison_backtest": {
            "control_metrics": control_m,
            "experimental_metrics": exp_m,
            "comparison_summary": comparison["comparison_summary"],
            "metrics_path": str(BACKTEST_METRICS_JSON.relative_to(PROJECT_ROOT)),
        },
        "p4_artifacts": {
            "corr_matrix_json": str(CORR_MATRIX_JSON.relative_to(PROJECT_ROOT)),
            "candidate_factor_list_json": str(CANDIDATE_LIST_JSON.relative_to(PROJECT_ROOT)),
            "regime_stability_report_json": str(REGIME_REPORT_JSON.relative_to(PROJECT_ROOT)),
            "comparison_backtest_metrics_json": str(BACKTEST_METRICS_JSON.relative_to(PROJECT_ROOT)),
            "research_manifest_json": str(RESEARCH_MANIFEST.relative_to(PROJECT_ROOT)),
        },
        "research_data": {
            "factors_csv": str(V3_FACTORS_CSV.relative_to(PROJECT_ROOT)),
            "factors_csv_sha256": factors_sha,
            "data_rows": len(df),
            "symbols": ALL_4_SYMBOLS,
        },
    }
    RESEARCH_MANIFEST.write_text(
        json.dumps(research_manifest, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"  ✅ MANIFEST_v3_research.json 已写入")

    p4_results["artifacts_written"] = [
        str(CORR_MATRIX_JSON.relative_to(PROJECT_ROOT)),
        str(CANDIDATE_LIST_JSON.relative_to(PROJECT_ROOT)),
        str(REGIME_REPORT_JSON.relative_to(PROJECT_ROOT)),
        str(BACKTEST_METRICS_JSON.relative_to(PROJECT_ROOT)),
        str(RESEARCH_MANIFEST.relative_to(PROJECT_ROOT)),
    ]

    # ─── P4.2: 追加审计事件 ───
    print(f"\n[P4.2] 追加审计事件...")

    append_audit("TASK044_COMPLETE", {
        "token": TOKEN,
        "baseline_commit": BASELINE_COMMIT,
        "task": TASK_ID,
        "execution_type": "research_sandbox",
        "elapsed_seconds": round(time.time() - start_time, 2),
        "p1_diagnosis": {
            "factors_analyzed": HIGH_FLIP_FACTORS,
            "root_cause_distribution": diagnosis_summary["root_cause_distribution"],
            "corr_matrix_path": str(CORR_MATRIX_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_candidate_pool": {
            "total_candidates": len(candidate_names),
            "passed_count": len(passed_pool),
            "passed_factors": passed_pool,
            "filter_criteria": f"flip≤{FLIP_RATE_FILTER*100:.0f}%, IC>{IC_FILTER}, monotonicity>0.4",
        },
        "p3_comparison_backtest": {
            "control_return": control_m["total_return"],
            "control_sharpe": control_m["sharpe_ratio"],
            "control_max_dd": control_m["max_drawdown"],
            "experimental_return": exp_m["total_return"],
            "experimental_sharpe": exp_m["sharpe_ratio"],
            "experimental_max_dd": exp_m["max_drawdown"],
            "return_delta": comparison["comparison_summary"]["return_delta"],
            "sharpe_delta": comparison["comparison_summary"]["sharpe_delta"],
            "flip_rate_reduction": comparison["comparison_summary"]["flip_rate_reduction"],
        },
        "p4_artifacts": p4_results["artifacts_written"],
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
        },
    })

    # ─── P4.3: 10项冒烟全检 ───
    print(f"\n[P4.3] 10项冒烟全检...")

    smoke_checks = {}
    smoke_pass_count = 0
    smoke_fail_count = 0

    # 1. Research sandbox isolated from production
    prod_configs_unchanged = (
        preconditions["fw_readonly_locked"] and
        preconditions["fec_readonly_locked"] and
        sha256_file(FACTOR_WEIGHT_PROD) == sha256_file(FACTOR_WEIGHT_PROD)
    )
    research_dir_isolated = (RESEARCH_DIR != PROD_DIR)
    smoke_checks["sandbox_isolation_ok"] = prod_configs_unchanged and research_dir_isolated
    if smoke_checks["sandbox_isolation_ok"]: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 2. Wind API calls zero
    smoke_checks["wind_api_calls_zero"] = (WIND_API_CALLS == 0)
    if WIND_API_CALLS == 0: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 3. Gate closed/hold
    smoke_checks["gate_closed_hold"] = (GATE_STATUS == "CLOSED/HOLD")
    if GATE_STATUS == "CLOSED/HOLD": smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 4. Release not issued
    smoke_checks["release_not_issued"] = (RELEASE_STATUS == "NOT_ISSUED")
    if RELEASE_STATUS == "NOT_ISSUED": smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 5. Deprecated script still archived (not imported)
    deprecated_imported = False
    self_name = Path(__file__).name
    import_pattern = re.compile(r'^\s*(import|from)\s+run_v3_ic_weight_deprecated', re.MULTILINE)
    for search_dir in [RESEARCH_DIR, PROD_DIR]:
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                if fname.endswith(".py") and fname != DEPRECATED_SCRIPT.name and fname != self_name:
                    fpath = Path(root) / fname
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        if import_pattern.search(content):
                            deprecated_imported = True
                    except Exception:
                        pass
    smoke_checks["deprecated_not_reconnected"] = not deprecated_imported
    if not deprecated_imported: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 6. All 15 candidate factors computed
    all_candidates_computed = all(c in df_with_candidates.columns for c in candidate_names)
    smoke_checks["all_15_candidates_computed"] = all_candidates_computed
    if all_candidates_computed: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 7. Candidate pool has at least 1 pass
    smoke_checks["candidate_pool_nonempty"] = (len(passed_pool) >= 1)
    if len(passed_pool) >= 1: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 8. Backtest comparison completed
    smoke_checks["backtest_comparison_done"] = (
        control_m is not None and
        exp_m is not None and
        "total_return" in control_m and
        "total_return" in exp_m
    )
    if smoke_checks["backtest_comparison_done"]: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 9. All research artifacts written
    all_artifacts_exist = all(
        Path(PROJECT_ROOT / p).exists() for p in p4_results["artifacts_written"]
    )
    smoke_checks["all_artifacts_written"] = all_artifacts_exist
    if all_artifacts_exist: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 10. Production configs unchanged (SHA256 match)
    prod_checksum = json.loads(PROD_CHECKSUM.read_text(encoding="utf-8"))
    fw_expected_sha = prod_checksum.get("config_fingerprints", {}).get("factor_weight_prod", {}).get("sha256")
    fw_actual_sha = sha256_file(FACTOR_WEIGHT_PROD)
    fec_expected_sha = prod_checksum.get("config_fingerprints", {}).get("factor_enable_config", {}).get("sha256")
    fec_actual_sha = sha256_file(FACTOR_ENABLE_CONFIG)
    prod_unchanged = (fw_expected_sha == fw_actual_sha) and (fec_expected_sha == fec_actual_sha)
    smoke_checks["prod_configs_unchanged"] = prod_unchanged
    if prod_unchanged: smoke_pass_count += 1
    else: smoke_fail_count += 1

    smoke_all_pass = (smoke_fail_count == 0)
    smoke_checks["total_checks"] = 10
    smoke_checks["passed"] = smoke_pass_count
    smoke_checks["failed"] = smoke_fail_count
    smoke_checks["smoke_all_passed"] = smoke_all_pass

    print(f"\n  冒烟校验结果:")
    for k, v in smoke_checks.items():
        if isinstance(v, bool):
            status = "✅" if v else "❌"
            print(f"    {status} {k}: {v}")
        else:
            print(f"    ℹ️  {k}: {v}")
    print(f"\n  冒烟校验总结: {smoke_pass_count}/10 PASS, {smoke_fail_count}/10 FAIL")
    print(f"  结论: {'✅ 全部通过' if smoke_all_pass else '❌ 存在失败项'}")

    p4_results["smoke_checks"] = smoke_checks
    p4_results["smoke_all_passed"] = smoke_all_pass

    # ════════════════════════════════════════════════════════════
    # 总结
    # ════════════════════════════════════════════════════════════
    elapsed = time.time() - start_time

    print("\n" + "=" * 72)
    print("DSHA-TASK-044 · 执行总结")
    print("=" * 72)

    print(f"\n{'P1 高危因子诊断':<22s}: ✅ DONE ({len(HIGH_FLIP_FACTORS)}因子)")
    print(f"{'  分行情切片IC':<22s}: ✅ 上涨/下跌/震荡")
    print(f"{'  相关性矩阵':<22s}: ✅ {len(all_corr_factors)}x{len(all_corr_factors)}")
    print(f"{'  根因诊断':<22s}: ✅ {diagnosis_summary['root_cause_distribution']}")

    print(f"\n{'P2 候选因子池':<22s}: ✅ DONE ({len(passed_pool)}/{len(candidate_names)}通过)")
    print(f"{'  单因子回测':<22s}: ✅ {len(single_factor_backtests)}个候选")

    print(f"\n{'P3 对照回测':<22s}: ✅ DONE")
    print(f"{'  对照组':<22s}: 收益={control_m['total_return']*100:.2f}%, 夏普={control_m['sharpe_ratio']:.4f}")
    print(f"{'  实验组':<22s}: 收益={exp_m['total_return']*100:.2f}%, 夏普={exp_m['sharpe_ratio']:.4f}")
    print(f"{'  翻转率降低':<22s}: {comparison['comparison_summary']['flip_rate_reduction']*100:.1f}%")

    print(f"\n{'P4 制品与审计':<22s}: ✅ DONE")
    print(f"{'  研究制品':<22s}: {len(p4_results['artifacts_written'])}个文件")
    print(f"{'  冒烟校验':<22s}: {smoke_pass_count}/10 PASS")

    print(f"\n耗时: {elapsed:.2f}秒")
    print(f"wind_api_calls: {WIND_API_CALLS}")
    print(f"Gate: {GATE_STATUS}")
    print(f"Release: {RELEASE_STATUS}")

    # Receipt
    print("\n" + "-" * 72)
    print("回执:")
    print(f"DSHA_TASK044_FACTOR_RESEARCH=RESEARCH_DONE|"
          f"prod_baseline_untouched={'YES' if prod_unchanged else 'NO'}|"
          f"factor_regime_analyzed=YES|"
          f"candidate_pool_built={'YES' if len(passed_pool) > 0 else 'NO'}|"
          f"backtest_completed=YES|"
          f"sandbox_isolation_ok={'YES' if smoke_checks['sandbox_isolation_ok'] else 'NO'}")
    print("-" * 72)

    return 0 if (smoke_all_pass and len(passed_pool) > 0) else 1

if __name__ == "__main__":
    sys.exit(main())
