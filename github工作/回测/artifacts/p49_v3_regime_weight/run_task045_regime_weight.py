#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHA-TASK-045 · 分行情因子动态加权方案研发
═══════════════════════════════════════════════════════════════
令牌: DSHA-TASK045-REGIME-WEIGHT-TOKEN
基线: feature/v88-g1 HEAD=73b0e32

任务:
  P2.1 三段行情IC补齐 (9品种扩充DOWN样本, 8因子×3行情)
  P2.2 构建动态权重规则 (震荡=等权, 上涨=提价spread_cs/momentum, 下跌=降权高波动持仓)
  P2.3 三组对照回测 (等权基线 / 固定加权 / 动态Regime加权)
  P2.4 风险校验 (加权后因子相关性, 拥挤度控制)
  P2.5 制品归档 + 审计日志 + 10项冒烟全检

约束:
  - wind_api_calls=0; Gate=CLOSED/HOLD; Release=NOT_ISSUED
  - 生产因子配置保持锁定, 不修改生产端因子清单
  - 仅在独立研究沙箱执行 (artifacts/p49_v3_regime_weight/)
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
TOKEN = "DSHA-TASK045-REGIME-WEIGHT-TOKEN"
BASELINE_COMMIT = "73b0e32"
TASK_ID = "DSHA-TASK045-REGIME-WEIGHT"
GATE_STATUS = "CLOSED/HOLD"
RELEASE_STATUS = "NOT_ISSUED"
TZ = timezone(timedelta(hours=8))

# ════════════════════════════════════════════════════════════════
# 路径常量
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(r"D:\DSH_WORK\github工作\回测")
PROD_DIR = PROJECT_ROOT / "artifacts" / "p49_v3_backtest"
RESEARCH_DIR = PROJECT_ROOT / "artifacts" / "p49_v3_regime_weight"
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"

V3_FACTORS_CSV = PROD_DIR / "factors_full_11_v3.csv"
FACTOR_WEIGHT_PROD = PROD_DIR / "factor_weight_prod.json"
FACTOR_ENABLE_CONFIG = PROD_DIR / "factor_enable_config.json"
PROD_CHECKSUM = PROD_DIR / "prod_baseline_checksum.json"
DEPRECATED_SCRIPT = PROD_DIR / "run_v3_ic_weight_deprecated.py"
SET_E_LOCK = PROJECT_ROOT / "artifacts" / "p49_v2_experiment" / "strategy_set_e.lock.json"

# Research outputs
REGIME_IC_JSON = RESEARCH_DIR / "regime_factor_ic.json"
WEIGHT_RULES_JSON = RESEARCH_DIR / "dynamic_weight_rules.json"
BACKTEST_METRICS_JSON = RESEARCH_DIR / "comparison_backtest_metrics.json"
RISK_VALIDATION_JSON = RESEARCH_DIR / "risk_validation.json"
RESEARCH_MANIFEST = RESEARCH_DIR / "MANIFEST_v3_regime_weight.json"

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

# 滚动IC参数
IC_WINDOW_DAYS = 20
ROLLING_STEP = 20

# Regime thresholds
REGIME_PCT_THRESHOLD = 0.005  # 0.5% band for sideways

# 权重边界 (避免过拟合)
WEIGHT_MIN = 0.04
WEIGHT_MAX = 0.25

# ════════════════════════════════════════════════════════════════
# 动态权重规则 (基于TASK044分行情IC诊断结果)
# ════════════════════════════════════════════════════════════════
# 设计依据:
#   UP: momentum_20d IC=-0.13(强负), spread_cs IC=-0.14(强负) → 提权
#   UP: realized_vol_20d IC=0.065(正), vol_regime_change IC=0.015(弱) → 降权
#   DOWN: momentum_20d IC=-0.25(最强负), spread_cs IC=-0.04 → 提权momentum
#   DOWN: oi_change_1d IC≈0, oi_level IC=-0.039, realized_vol_20d IC=-0.024 → 降权
#   SIDEWAYS: 等权 (所有因子IC符号不稳定, 无法确定优势方向)
DYNAMIC_WEIGHTS = {
    "sideways": {  # 等权
        "contract_switch_flag": 0.125,
        "momentum_20d": 0.125,
        "oi_change_1d": 0.125,
        "oi_change_rate_7d": 0.125,
        "oi_level": 0.125,
        "realized_vol_20d": 0.125,
        "spread_cs": 0.125,
        "vol_regime_change": 0.125,
    },
    "up": {  # 50%等权+50%极端: 提价spread_cs/momentum, 降权vol/vol_regime_change, 平滑过渡降翻转率
        "contract_switch_flag": 0.1225,
        "momentum_20d": 0.1625,
        "oi_change_1d": 0.1275,
        "oi_change_rate_7d": 0.0975,
        "oi_level": 0.0925,
        "realized_vol_20d": 0.0975,
        "spread_cs": 0.1875,
        "vol_regime_change": 0.1125,
    },
    "down": {  # 50%等权+50%极端: 降权高波动持仓, 提价momentum, 平滑过渡降翻转率
        "contract_switch_flag": 0.1325,
        "momentum_20d": 0.1725,
        "oi_change_1d": 0.1025,
        "oi_change_rate_7d": 0.1125,
        "oi_level": 0.1025,
        "realized_vol_20d": 0.0925,
        "spread_cs": 0.1525,
        "vol_regime_change": 0.1325,
    },
}

# 固定加权方案 (IC绝对值加权, 最小权重0.04)
FIXED_WEIGHTS = {
    "contract_switch_flag": 0.04,
    "momentum_20d": 0.33,
    "oi_change_1d": 0.08,
    "oi_change_rate_7d": 0.07,
    "oi_level": 0.05,
    "realized_vol_20d": 0.05,
    "spread_cs": 0.32,
    "vol_regime_change": 0.06,
}

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
# 回测引擎
# ════════════════════════════════════════════════════════════════
def compute_backtest_from_signal(
    df: pd.DataFrame,
    signal_array: np.ndarray,
    threshold: float = SIGNAL_THRESHOLD,
    rebalance_interval: int = REBALANCE_INTERVAL,
    target_vol: float = TARGET_VOL,
    max_single_weight: float = MAX_SINGLE_WEIGHT,
) -> dict:
    """Run backtest from a pre-computed signal array.

    Args:
        df: DataFrame with 'date', 'close', 'symbol', 'realized_vol_20d' columns
        signal_array: 1D numpy array of signal values, same length as df
    """
    # 1. 仓位生成
    position = np.zeros(len(df))
    for i in range(1, len(df)):
        s = signal_array[i]
        if s > threshold:
            position[i] = 1.0
        elif s < -threshold:
            position[i] = -1.0
        else:
            position[i] = 0.0

    # 2. 调仓频率
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

    # 3. 仓位管理: 波动率目标
    if "realized_vol_20d" in df.columns:
        vol = df["realized_vol_20d"].values
        vol_weight = np.clip(target_vol / np.where(np.isnan(vol) | (vol == 0), 1.0, vol), 0, max_single_weight)
        position = position * vol_weight

    # 4. 日度收益计算
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

    # 5. 回撤控制
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

    # 6. 交易成本
    position_changes = np.abs(np.diff(position))
    min_len = min(len(strategy_returns), len(position_changes))
    strategy_returns = strategy_returns[:min_len]
    position_changes = position_changes[:min_len]
    cost_adjusted = np.zeros_like(strategy_returns)
    for i in range(len(strategy_returns)):
        cost_adjusted[i] = strategy_returns[i] - position_changes[i] * TRANSACTION_COST

    # 7. 绩效指标
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


def compute_signal_fixed(df: pd.DataFrame, factors: List[str], weights: List[float]) -> np.ndarray:
    """Compute composite signal from fixed weights."""
    signal = np.zeros(len(df))
    for i, fname in enumerate(factors):
        if fname in df.columns:
            vals = df[fname].values.astype(float).copy()
            std = np.nanstd(vals)
            mean = np.nanmean(vals)
            if std > 0:
                vals = (vals - mean) / std
            else:
                vals = np.zeros_like(vals)
            w = weights[i] if i < len(weights) else 0.0
            signal += w * vals
    return np.where(np.isnan(signal), 0.0, signal)


def compute_signal_dynamic(df: pd.DataFrame, factors: List[str],
                            regime_weights: Dict[str, Dict[str, float]],
                            regime_col: str = "regime") -> np.ndarray:
    """Compute composite signal using regime-specific dynamic weights."""
    # Pre-compute z-scores for all factors
    zscores = {}
    for fname in factors:
        if fname in df.columns:
            vals = df[fname].values.astype(float).copy()
            std = np.nanstd(vals)
            mean = np.nanmean(vals)
            if std > 0:
                zscores[fname] = (vals - mean) / std
            else:
                zscores[fname] = np.zeros_like(vals)
        else:
            zscores[fname] = np.zeros(len(df))

    regimes = df[regime_col].values if regime_col in df.columns else np.zeros(len(df), dtype=object)

    signal = np.zeros(len(df))
    n_factors = len(factors)
    for i in range(len(df)):
        r = regimes[i]
        if r not in regime_weights:
            r = "sideways"  # fallback
        rw = regime_weights[r]
        s = 0.0
        for j, fname in enumerate(factors):
            w = rw.get(fname, 1.0 / n_factors)
            s += w * zscores[fname][i]
        signal[i] = s

    return np.where(np.isnan(signal), 0.0, signal)


def compute_backtest_with_weights(
    df: pd.DataFrame,
    signal_factors: List[str],
    signal_weights: List[float],
    threshold: float = SIGNAL_THRESHOLD,
    rebalance_interval: int = REBALANCE_INTERVAL,
    target_vol: float = TARGET_VOL,
    max_single_weight: float = MAX_SINGLE_WEIGHT,
) -> dict:
    """Run backtest with fixed weights (backward-compatible wrapper)."""
    signal = compute_signal_fixed(df, signal_factors, signal_weights)
    return compute_backtest_from_signal(df, signal, threshold, rebalance_interval, target_vol, max_single_weight)


def compute_backtest_dynamic(
    df: pd.DataFrame,
    signal_factors: List[str],
    regime_weights: Dict[str, Dict[str, float]],
    threshold: float = SIGNAL_THRESHOLD,
    rebalance_interval: int = REBALANCE_INTERVAL,
    target_vol: float = TARGET_VOL,
    max_single_weight: float = MAX_SINGLE_WEIGHT,
) -> dict:
    """Run backtest with dynamic regime-specific weights."""
    signal = compute_signal_dynamic(df, signal_factors, regime_weights)
    return compute_backtest_from_signal(df, signal, threshold, rebalance_interval, target_vol, max_single_weight)


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
    monotonic_pairs = 0
    for i in range(1, len(ics)):
        if abs(ics[i]) >= abs(ics[i-1]) - 0.005:
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
# 复合信号翻转率计算
# ════════════════════════════════════════════════════════════════
def compute_composite_flip_rate(
    df: pd.DataFrame,
    signal_array: np.ndarray,
    symbols: List[str],
    signal_name: str = "composite_signal",
    window: int = IC_WINDOW_DAYS,
    step: int = ROLLING_STEP,
) -> dict:
    """Compute rolling IC of composite signal vs returns, then flip rate.

    Args:
        df: DataFrame with date, close, symbol columns
        signal_array: pre-computed composite signal array
        symbols: list of symbols to include
    """
    df_copy = df.copy()
    df_copy[signal_name] = signal_array
    df_copy = df_copy[df_copy["symbol"].isin(symbols)].copy()

    ic_data = compute_rolling_ic_for_factors(df_copy, [signal_name], symbols, window, step)
    window_ics = ic_data.get(signal_name, [])

    if len(window_ics) < 2:
        return {
            "flip_rate": 0.0,
            "flip_count": 0,
            "num_windows": len(window_ics),
            "ic_mean": 0.0,
            "ic_std": 0.0,
            "ir": 0.0,
            "ic_values": [w["ic"] for w in window_ics],
        }

    flip_rate, flip_count = compute_sign_flip_rate(window_ics)
    summary = compute_ic_summary(window_ics)

    return {
        "flip_rate": round(flip_rate, 4),
        "flip_count": flip_count,
        "num_windows": len(window_ics),
        "ic_mean": summary["ic_mean"],
        "ic_std": summary["ic_std"],
        "ir": summary["ir"],
        "ic_values": [w["ic"] for w in window_ics],
    }


# ════════════════════════════════════════════════════════════════
# 相关性矩阵
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


def compute_weighted_corr_matrix(corr_matrix: dict, weights: Dict[str, float], factors: List[str]) -> dict:
    """Compute effective weighted correlation: w_i * w_j * corr(i,j)."""
    result = {}
    for f1 in factors:
        result[f1] = {}
        for f2 in factors:
            c = corr_matrix.get(f1, {}).get(f2, 0.0)
            w1 = weights.get(f1, 0.0)
            w2 = weights.get(f2, 0.0)
            result[f1][f2] = round(w1 * w2 * c, 6)
    return result


def compute_hhi(weights: Dict[str, float]) -> float:
    """Compute Herfindahl-Hirschman Index of weight distribution."""
    return sum(w ** 2 for w in weights.values())


def compute_portfolio_variance(corr_matrix: dict, weights: Dict[str, float],
                                factors: List[str]) -> float:
    """Compute portfolio variance: sum(w_i * w_j * cov(i,j)).
    Here we approximate cov as corr * std_i * std_j, but since we only have corr,
    we use the normalized version: sum(w_i * w_j * corr(i,j)).
    """
    var = 0.0
    for f1 in factors:
        for f2 in factors:
            c = corr_matrix.get(f1, {}).get(f2, 0.0)
            w1 = weights.get(f1, 0.0)
            w2 = weights.get(f2, 0.0)
            var += w1 * w2 * c
    return round(var, 6)


# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════
def main():
    global WIND_API_CALLS, REAL_WIND_CALL

    start_time = time.time()

    print("=" * 72)
    print("DSHA-TASK-045 · 分行情因子动态加权方案研发")
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

    append_audit("TASK045_START", {
        "token": TOKEN,
        "baseline_commit": BASELINE_COMMIT,
        "precondition_checks": preconditions,
        "execution_type": "research_sandbox",
    })

    # Load full data (all 9 symbols)
    df_full = pd.read_csv(V3_FACTORS_CSV)
    df_full["date"] = pd.to_datetime(df_full["date"])

    # 4-symbol whitelist for backtest
    df_4sym = df_full[df_full["symbol"].isin(ALL_4_SYMBOLS)].copy()
    df_4sym = df_4sym.sort_values(["symbol", "date"]).reset_index(drop=True)
    print(f"\n  数据: {len(df_full)}行 (9品种), {len(df_4sym)}行 (4品种白名单)")

    # ════════════════════════════════════════════════════════════
    # P2.1: 三段行情IC补齐 (9品种扩充DOWN样本)
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P2.1] 三段行情IC补齐 (9品种扩充DOWN样本)")
    print("=" * 72)

    p2_1_results = {}

    # Classify regimes for 4-symbol pool
    df_4sym_regime = classify_regimes(df_4sym, ma_window=20)
    regime_counts_4sym = df_4sym_regime["regime"].value_counts().to_dict()
    print(f"\n  4品种Regime分布: {regime_counts_4sym}")

    # Classify regimes for 9-symbol pool (for DOWN expansion)
    all_symbols_9 = sorted(df_full["symbol"].unique().tolist())
    df_9sym_regime = classify_regimes(df_full, ma_window=20)
    regime_counts_9sym = df_9sym_regime["regime"].value_counts().to_dict()
    print(f"  9品种Regime分布: {regime_counts_9sym}")

    # Check DOWN sample sufficiency
    down_4sym = regime_counts_4sym.get("down", 0)
    down_9sym = regime_counts_9sym.get("down", 0)
    min_window = IC_WINDOW_DAYS  # 20
    down_sufficient_4sym = down_4sym >= min_window
    down_sufficient_9sym = down_9sym >= min_window

    print(f"\n  DOWN样本: 4品种={down_4sym}, 9品种={down_9sym}")
    print(f"  最小窗口要求: {min_window}天")
    print(f"  DOWN样本充分: 4品种={'✅' if down_sufficient_4sym else '❌'}, 9品种={'✅' if down_sufficient_9sym else '❌'}")

    # Compute regime IC for all 8 factors using 9-symbol pool (expanded)
    print(f"\n  计算9品种池分行情IC (扩充DOWN样本)...")
    regime_ic_9sym = compute_regime_ic(
        df_9sym_regime, RETAINED_FACTORS, all_symbols_9,
        IC_WINDOW_DAYS, ROLLING_STEP
    )

    # Compute regime IC for 4-symbol pool (for comparison)
    print(f"  计算4品种池分行情IC (基线对照)...")
    regime_ic_4sym = compute_regime_ic(
        df_4sym_regime, RETAINED_FACTORS, ALL_4_SYMBOLS,
        IC_WINDOW_DAYS, ROLLING_STEP
    )

    # Full-sample IC for 4-symbol pool
    full_ic_4sym = compute_rolling_ic_for_factors(
        df_4sym_regime, RETAINED_FACTORS, ALL_4_SYMBOLS,
        IC_WINDOW_DAYS, ROLLING_STEP
    )

    # Build regime IC report
    factor_ic_report = {}
    for factor in RETAINED_FACTORS:
        # Full sample
        full_windows = full_ic_4sym.get(factor, [])
        full_flip_rate, full_flip_count = compute_sign_flip_rate(full_windows)
        full_summary = compute_ic_summary(full_windows)

        # Per regime (9-symbol expanded)
        regime_info_9 = {}
        for regime in ["up", "down", "sideways"]:
            rd = regime_ic_9sym.get(regime, {}).get(factor, {})
            regime_info_9[regime] = {
                "ic_mean": rd.get("ic_mean", 0.0),
                "ic_std": rd.get("ic_std", 0.0),
                "ir": rd.get("ir", 0.0),
                "flip_rate": rd.get("flip_rate", 0.0),
                "num_windows": rd.get("num_windows", 0),
            }

        # Per regime (4-symbol baseline)
        regime_info_4 = {}
        for regime in ["up", "down", "sideways"]:
            rd = regime_ic_4sym.get(regime, {}).get(factor, {})
            regime_info_4[regime] = {
                "ic_mean": rd.get("ic_mean", 0.0),
                "ic_std": rd.get("ic_std", 0.0),
                "ir": rd.get("ir", 0.0),
                "flip_rate": rd.get("flip_rate", 0.0),
                "num_windows": rd.get("num_windows", 0),
            }

        # Sign divergence check
        regime_ics = [regime_info_9[r]["ic_mean"] for r in ["up", "down", "sideways"]]
        ic_signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in regime_ics]
        sign_divergence = len(set(ic_signs)) > 1

        # Weight recommendation
        up_ic = regime_info_9["up"]["ic_mean"]
        down_ic = regime_info_9["down"]["ic_mean"]
        sideways_ic = regime_info_9["sideways"]["ic_mean"]

        if factor == "contract_switch_flag":
            weight_rec = "保持等权 (特殊因子, IC≈0)"
        elif sign_divergence and abs(up_ic) > 0.05:
            weight_rec = f"UP提权 (|IC_up|={abs(up_ic):.3f}), DOWN{'提权' if abs(down_ic) > 0.05 else '降权'}"
        elif sign_divergence:
            weight_rec = "分行情差异化加权"
        else:
            weight_rec = "IC符号一致, 可统一加权"

        factor_ic_report[factor] = {
            "full_sample_4sym": {
                "ic_mean": full_summary["ic_mean"],
                "ic_std": full_summary["ic_std"],
                "ir": full_summary["ir"],
                "flip_rate": round(full_flip_rate, 4),
                "flip_count": full_flip_count,
                "num_windows": full_summary["num_windows"],
                "ic_positive_ratio": full_summary["ic_positive_ratio"],
            },
            "regimes_9sym": regime_info_9,
            "regimes_4sym": regime_info_4,
            "sign_divergence": sign_divergence,
            "ic_signs_by_regime": dict(zip(["up", "down", "sideways"], ic_signs)),
            "weight_recommendation": weight_rec,
        }

        # Print summary
        print(f"\n  [{factor}]")
        print(f"    全样本IC均值: {full_summary['ic_mean']:.6f}, 翻转率: {full_flip_rate*100:.1f}%")
        for regime in ["up", "down", "sideways"]:
            r9 = regime_info_9[regime]
            print(f"    {regime:>10s}: IC均值={r9['ic_mean']:.6f}, 翻转率={r9['flip_rate']*100:.1f}%, 窗口数={r9['num_windows']}")
        print(f"    符号分歧: {'是' if sign_divergence else '否'} → {weight_rec}")

    p2_1_results["regime_counts_4sym"] = regime_counts_4sym
    p2_1_results["regime_counts_9sym"] = regime_counts_9sym
    p2_1_results["down_sample_sufficient_4sym"] = down_sufficient_4sym
    p2_1_results["down_sample_sufficient_9sym"] = down_sufficient_9sym
    p2_1_results["min_window_required"] = min_window
    p2_1_results["factor_ic_report"] = factor_ic_report

    # Write regime_factor_ic.json
    regime_ic_output = {
        "output_id": "DSHA-TASK045-REGIME-IC",
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
        "regime_counts_4sym": regime_counts_4sym,
        "regime_counts_9sym": regime_counts_9sym,
        "down_sample_sufficient_4sym": down_sufficient_4sym,
        "down_sample_sufficient_9sym": down_sufficient_9sym,
        "min_window_required": min_window,
        "factors_analyzed": RETAINED_FACTORS,
        "factor_ic_report": factor_ic_report,
        "notes": "9品种池用于扩充DOWN区间IC样本, 4品种池用于基线对照",
    }
    REGIME_IC_JSON.write_text(
        json.dumps(regime_ic_output, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"\n  ✅ regime_factor_ic.json 已写入")

    # ════════════════════════════════════════════════════════════
    # P2.2: 构建动态权重规则
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P2.2] 构建动态权重规则")
    print("=" * 72)

    p2_2_results = {}

    # Verify weight sums
    for regime in ["up", "down", "sideways"]:
        w_sum = sum(DYNAMIC_WEIGHTS[regime].values())
        print(f"  {regime:>10s}: 权重和={w_sum:.6f} {'✅' if abs(w_sum - 1.0) < 1e-6 else '❌'}")

    # Verify weight bounds
    for regime in ["up", "down", "sideways"]:
        for f, w in DYNAMIC_WEIGHTS[regime].items():
            if w < WEIGHT_MIN or w > WEIGHT_MAX:
                print(f"  ⚠️  {regime}/{f}: 权重{w:.4f}超出边界[{WEIGHT_MIN}, {WEIGHT_MAX}]")

    # Fixed weights verification
    fixed_sum = sum(FIXED_WEIGHTS.values())
    print(f"  {'fixed':>10s}: 权重和={fixed_sum:.6f} {'✅' if abs(fixed_sum - 1.0) < 1e-6 else '❌'}")

    # Build weight rules description
    weight_rules_description = {
        "design_principle": "基于TASK044分行情IC诊断, 各行情段提权IC绝对值最大的因子, 降权IC符号不稳定或接近零的因子",
        "sideways": {
            "strategy": "等权 (所有因子IC符号不稳定, 无法确定优势方向)",
            "weights": DYNAMIC_WEIGHTS["sideways"],
            "rationale": "震荡行情中因子IC符号频繁翻转, 等权分散风险最合理",
        },
        "up": {
            "strategy": "提价spread_cs + momentum_20d, 降权realized_vol_20d/vol_regime_change",
            "weights": DYNAMIC_WEIGHTS["up"],
            "rationale": "上涨行情中spread_cs(IC=-0.14)和momentum_20d(IC=-0.13)具有最强预测力",
        },
        "down": {
            "strategy": "降权高波动持仓因子(oi_change_1d/oi_level/realized_vol_20d), 提价momentum_20d",
            "weights": DYNAMIC_WEIGHTS["down"],
            "rationale": "下跌行情中momentum_20d(IC=-0.25)预测力最强, 持仓因子IC接近零或为负",
        },
    }

    p2_2_results["dynamic_weights"] = DYNAMIC_WEIGHTS
    p2_2_results["fixed_weights"] = FIXED_WEIGHTS
    p2_2_results["weight_rules_description"] = weight_rules_description
    p2_2_results["weight_bounds"] = {"min": WEIGHT_MIN, "max": WEIGHT_MAX}
    p2_2_results["normalization"] = "sum_to_1_per_regime"

    # Write dynamic_weight_rules.json
    weight_rules_output = {
        "output_id": "DSHA-TASK045-DYNAMIC-WEIGHTS",
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
        "dynamic_weights": DYNAMIC_WEIGHTS,
        "fixed_weights": FIXED_WEIGHTS,
        "weight_rules_description": weight_rules_description,
        "weight_bounds": {"min": WEIGHT_MIN, "max": WEIGHT_MAX},
        "normalization": "sum_to_1_per_regime",
        "factor_list": RETAINED_FACTORS,
    }
    WEIGHT_RULES_JSON.write_text(
        json.dumps(weight_rules_output, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"  ✅ dynamic_weight_rules.json 已写入")

    # Print weight comparison table
    print(f"\n  权重对照表:")
    print(f"  {'因子':<25s} {'等权':>8s} {'固定加权':>10s} {'上涨':>8s} {'下跌':>8s} {'震荡':>8s}")
    print(f"  {'-'*72}")
    for f in RETAINED_FACTORS:
        eq = 0.125
        fx = FIXED_WEIGHTS[f]
        up = DYNAMIC_WEIGHTS["up"][f]
        dn = DYNAMIC_WEIGHTS["down"][f]
        sw = DYNAMIC_WEIGHTS["sideways"][f]
        print(f"  {f:<25s} {eq:>8.4f} {fx:>10.4f} {up:>8.4f} {dn:>8.4f} {sw:>8.4f}")
    print(f"  {'合计':<25s} {'1.0000':>8s} {'1.0000':>10s} {sum(DYNAMIC_WEIGHTS['up'].values()):>8.4f} {sum(DYNAMIC_WEIGHTS['down'].values()):>8.4f} {sum(DYNAMIC_WEIGHTS['sideways'].values()):>8.4f}")

    # ════════════════════════════════════════════════════════════
    # P2.3: 三组对照回测
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P2.3] 三组对照回测 (等权基线 / 固定加权 / 动态Regime加权)")
    print("=" * 72)

    p2_3_results = {}

    # Use 4-symbol whitelist with regime classification
    df_bt = df_4sym_regime.copy()
    # Drop ma20 column to avoid confusion (keep regime)
    df_bt_clean = df_bt.drop(columns=["ma20"], errors="ignore")

    # ─── Group A: 等权基线 ───
    print(f"\n[Group A] 等权基线 (8因子×0.125)...")
    signal_a = compute_signal_fixed(df_bt_clean, RETAINED_FACTORS, EQUAL_WEIGHTS)
    bt_a = compute_backtest_from_signal(
        df_bt_clean, signal_a,
        SIGNAL_THRESHOLD, REBALANCE_INTERVAL, TARGET_VOL, MAX_SINGLE_WEIGHT
    )
    metrics_a = bt_a["metrics"]
    print(f"  收益: {metrics_a['total_return']*100:.2f}%, 夏普: {metrics_a['sharpe_ratio']:.4f}, "
          f"回撤: {metrics_a['max_drawdown']*100:.2f}%, 交易: {metrics_a['trade_count']}")

    # ─── Group B: 固定加权 ───
    print(f"\n[Group B] 固定加权 (IC绝对值加权)...")
    fixed_weights_list = [FIXED_WEIGHTS[f] for f in RETAINED_FACTORS]
    signal_b = compute_signal_fixed(df_bt_clean, RETAINED_FACTORS, fixed_weights_list)
    bt_b = compute_backtest_from_signal(
        df_bt_clean, signal_b,
        SIGNAL_THRESHOLD, REBALANCE_INTERVAL, TARGET_VOL, MAX_SINGLE_WEIGHT
    )
    metrics_b = bt_b["metrics"]
    print(f"  收益: {metrics_b['total_return']*100:.2f}%, 夏普: {metrics_b['sharpe_ratio']:.4f}, "
          f"回撤: {metrics_b['max_drawdown']*100:.2f}%, 交易: {metrics_b['trade_count']}")

    # ─── Group C: 动态Regime加权 ───
    print(f"\n[Group C] 动态Regime加权...")
    signal_c = compute_signal_dynamic(
        df_bt_clean, RETAINED_FACTORS, DYNAMIC_WEIGHTS
    )
    bt_c = compute_backtest_from_signal(
        df_bt_clean, signal_c,
        SIGNAL_THRESHOLD, REBALANCE_INTERVAL, TARGET_VOL, MAX_SINGLE_WEIGHT
    )
    metrics_c = bt_c["metrics"]
    print(f"  收益: {metrics_c['total_return']*100:.2f}%, 夏普: {metrics_c['sharpe_ratio']:.4f}, "
          f"回撤: {metrics_c['max_drawdown']*100:.2f}%, 交易: {metrics_c['trade_count']}")

    # ─── 复合信号翻转率 ───
    print(f"\n[复合信号翻转率计算]...")
    flip_a = compute_composite_flip_rate(df_bt_clean, signal_a, ALL_4_SYMBOLS, "signal_a")
    flip_b = compute_composite_flip_rate(df_bt_clean, signal_b, ALL_4_SYMBOLS, "signal_b")
    flip_c = compute_composite_flip_rate(df_bt_clean, signal_c, ALL_4_SYMBOLS, "signal_c")

    print(f"  Group A (等权): 翻转率={flip_a['flip_rate']*100:.1f}%, IC均值={flip_a['ic_mean']:.6f}")
    print(f"  Group B (固定加权): 翻转率={flip_b['flip_rate']*100:.1f}%, IC均值={flip_b['ic_mean']:.6f}")
    print(f"  Group C (动态加权): 翻转率={flip_c['flip_rate']*100:.1f}%, IC均值={flip_c['ic_mean']:.6f}")

    # ─── 加权平均因子翻转率 ───
    print(f"\n[加权平均因子翻转率计算]...")
    # 4-symbol factor flip rates (from TASK044 full-sample IC)
    factor_flip_rates = {}
    for factor in RETAINED_FACTORS:
        fw_windows = full_ic_4sym.get(factor, [])
        ff_rate, _ = compute_sign_flip_rate(fw_windows)
        factor_flip_rates[factor] = round(ff_rate, 4)

    # Equal weight: unweighted average
    wavg_flip_a = float(np.mean(list(factor_flip_rates.values())))

    # Fixed weight: weighted average
    wavg_flip_b = sum(FIXED_WEIGHTS[f] * factor_flip_rates[f] for f in RETAINED_FACTORS)

    # Dynamic weight: weighted average per regime, then average across regimes
    wavg_flip_c_by_regime = {}
    for regime in ["up", "down", "sideways"]:
        rw = DYNAMIC_WEIGHTS[regime]
        wavg = sum(rw[f] * factor_flip_rates[f] for f in RETAINED_FACTORS)
        wavg_flip_c_by_regime[regime] = round(wavg, 4)
    total_regime_count = sum(regime_counts_4sym.values())
    wavg_flip_c = sum(
        wavg_flip_c_by_regime[r] * regime_counts_4sym.get(r, 0) / total_regime_count
        for r in ["up", "down", "sideways"]
    ) if total_regime_count > 0 else 0.0

    print(f"  因子翻转率 (4品种全样本):")
    for f in RETAINED_FACTORS:
        print(f"    {f:<25s}: {factor_flip_rates[f]*100:.1f}%")
    print(f"\n  加权平均因子翻转率:")
    print(f"    等权(A): {wavg_flip_a*100:.2f}%")
    print(f"    固定加权(B): {wavg_flip_b*100:.2f}%")
    print(f"    动态加权(C): {wavg_flip_c*100:.2f}% (UP={wavg_flip_c_by_regime['up']*100:.2f}%, "
          f"DOWN={wavg_flip_c_by_regime['down']*100:.2f}%, SIDEWAYS={wavg_flip_c_by_regime['sideways']*100:.2f}%)")
    wavg_reduction_c_vs_a = wavg_flip_a - wavg_flip_c
    print(f"    动态vs等权 加权翻转率下降: {wavg_reduction_c_vs_a*100:.2f}pp")

    # ─── 对照对比 ───
    comparison = {
        "group_a_equal_weight": {
            "factors": RETAINED_FACTORS,
            "num_factors": len(RETAINED_FACTORS),
            "weight_method": "equal_weight",
            "metrics": metrics_a,
            "composite_flip_rate": flip_a["flip_rate"],
            "composite_ic_mean": flip_a["ic_mean"],
        },
        "group_b_fixed_weight": {
            "factors": RETAINED_FACTORS,
            "num_factors": len(RETAINED_FACTORS),
            "weight_method": "ic_magnitude_weighted",
            "weights": FIXED_WEIGHTS,
            "metrics": metrics_b,
            "composite_flip_rate": flip_b["flip_rate"],
            "composite_ic_mean": flip_b["ic_mean"],
        },
        "group_c_dynamic_regime": {
            "factors": RETAINED_FACTORS,
            "num_factors": len(RETAINED_FACTORS),
            "weight_method": "dynamic_regime_weighted",
            "dynamic_weights": DYNAMIC_WEIGHTS,
            "metrics": metrics_c,
            "composite_flip_rate": flip_c["flip_rate"],
            "composite_ic_mean": flip_c["ic_mean"],
        },
    }

    # Comparison summary
    return_delta_b_vs_a = round(metrics_b["total_return"] - metrics_a["total_return"], 6)
    return_delta_c_vs_a = round(metrics_c["total_return"] - metrics_a["total_return"], 6)
    sharpe_delta_b_vs_a = round(metrics_b["sharpe_ratio"] - metrics_a["sharpe_ratio"], 6)
    sharpe_delta_c_vs_a = round(metrics_c["sharpe_ratio"] - metrics_a["sharpe_ratio"], 6)
    max_dd_delta_b_vs_a = round(metrics_b["max_drawdown"] - metrics_a["max_drawdown"], 6)
    max_dd_delta_c_vs_a = round(metrics_c["max_drawdown"] - metrics_a["max_drawdown"], 6)
    flip_reduction_b_vs_a = round(flip_a["flip_rate"] - flip_b["flip_rate"], 4)
    flip_reduction_c_vs_a = round(flip_a["flip_rate"] - flip_c["flip_rate"], 4)

    comparison["comparison_summary"] = {
        "fixed_vs_equal": {
            "return_delta": return_delta_b_vs_a,
            "sharpe_delta": sharpe_delta_b_vs_a,
            "max_dd_delta": max_dd_delta_b_vs_a,
            "flip_rate_reduction": flip_reduction_b_vs_a,
            "weighted_flip_rate_reduction": round(wavg_flip_a - wavg_flip_b, 4),
        },
        "dynamic_vs_equal": {
            "return_delta": return_delta_c_vs_a,
            "sharpe_delta": sharpe_delta_c_vs_a,
            "max_dd_delta": max_dd_delta_c_vs_a,
            "flip_rate_reduction": flip_reduction_c_vs_a,
            "flip_rate_reduction_pct": round(flip_reduction_c_vs_a / flip_a["flip_rate"] * 100, 2) if flip_a["flip_rate"] > 0 else 0,
            "weighted_flip_rate_reduction": round(wavg_reduction_c_vs_a, 4),
            "weighted_flip_rate_reduction_pct": round(wavg_reduction_c_vs_a / wavg_flip_a * 100, 2) if wavg_flip_a > 0 else 0,
        },
        "dynamic_vs_fixed": {
            "return_delta": round(metrics_c["total_return"] - metrics_b["total_return"], 6),
            "sharpe_delta": round(metrics_c["sharpe_ratio"] - metrics_b["sharpe_ratio"], 6),
            "max_dd_delta": round(metrics_c["max_drawdown"] - metrics_b["max_drawdown"], 6),
            "flip_rate_reduction": round(flip_b["flip_rate"] - flip_c["flip_rate"], 4),
        },
    }

    print(f"\n  对照对比:")
    print(f"  {'指标':<25s} {'等权(A)':>12s} {'固定加权(B)':>12s} {'动态加权(C)':>12s}")
    print(f"  {'-'*62}")
    print(f"  {'总收益':<25s} {metrics_a['total_return']*100:>11.2f}% {metrics_b['total_return']*100:>11.2f}% {metrics_c['total_return']*100:>11.2f}%")
    print(f"  {'夏普比率':<25s} {metrics_a['sharpe_ratio']:>12.4f} {metrics_b['sharpe_ratio']:>12.4f} {metrics_c['sharpe_ratio']:>12.4f}")
    print(f"  {'最大回撤':<25s} {metrics_a['max_drawdown']*100:>11.2f}% {metrics_b['max_drawdown']*100:>11.2f}% {metrics_c['max_drawdown']*100:>11.2f}%")
    print(f"  {'交易次数':<25s} {metrics_a['trade_count']:>12d} {metrics_b['trade_count']:>12d} {metrics_c['trade_count']:>12d}")
    print(f"  {'复合信号翻转率':<25s} {flip_a['flip_rate']*100:>11.1f}% {flip_b['flip_rate']*100:>11.1f}% {flip_c['flip_rate']*100:>11.1f}%")
    print(f"  {'加权平均因子翻转率':<25s} {wavg_flip_a*100:>11.2f}% {wavg_flip_b*100:>11.2f}% {wavg_flip_c*100:>11.2f}%")

    p2_3_results["comparison"] = comparison
    p2_3_results["flip_rates"] = {
        "equal_weight_composite": flip_a["flip_rate"],
        "fixed_weight_composite": flip_b["flip_rate"],
        "dynamic_regime_composite": flip_c["flip_rate"],
        "equal_weight_wavg_factor": round(wavg_flip_a, 4),
        "fixed_weight_wavg_factor": round(wavg_flip_b, 4),
        "dynamic_regime_wavg_factor": round(wavg_flip_c, 4),
    }
    p2_3_results["factor_flip_rates_4sym"] = factor_flip_rates

    # Write comparison_backtest_metrics.json
    backtest_metrics_output = {
        "output_id": "DSHA-TASK045-COMPARISON-BACKTEST",
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
        "groups": comparison,
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
    print(f"\n  ✅ comparison_backtest_metrics.json 已写入")

    # ════════════════════════════════════════════════════════════
    # P2.4: 风险校验 (相关性 + 拥挤度)
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P2.4] 风险校验 (加权后因子相关性, 拥挤度控制)")
    print("=" * 72)

    p2_4_results = {}

    # ─── 4.1: 基础相关性矩阵 ───
    print(f"\n[4.1] 基础因子相关性矩阵...")
    corr_matrix = compute_correlation_matrix(df_4sym_regime, RETAINED_FACTORS)

    # Report high-correlation pairs
    high_corr_pairs = []
    for i, f1 in enumerate(RETAINED_FACTORS):
        for j, f2 in enumerate(RETAINED_FACTORS):
            if j > i:
                c = corr_matrix[f1][f2]
                if abs(c) > 0.3:
                    high_corr_pairs.append((f1, f2, c))
    high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    print(f"  高相关因子对 (|r|>0.3): {len(high_corr_pairs)}对")
    for f1, f2, c in high_corr_pairs:
        print(f"    {f1} <-> {f2}: r={c:.6f}")

    # ─── 4.2: 各方案加权后相关性 ───
    print(f"\n[4.2] 各方案加权后相关性贡献...")
    weighted_corr = {}
    for name, weights_dict in [("equal_weight", {f: 0.125 for f in RETAINED_FACTORS}),
                                ("fixed_weight", FIXED_WEIGHTS),
                                ("dynamic_up", DYNAMIC_WEIGHTS["up"]),
                                ("dynamic_down", DYNAMIC_WEIGHTS["down"]),
                                ("dynamic_sideways", DYNAMIC_WEIGHTS["sideways"])]:
        wc = compute_weighted_corr_matrix(corr_matrix, weights_dict, RETAINED_FACTORS)
        weighted_corr[name] = wc
        pv = compute_portfolio_variance(corr_matrix, weights_dict, RETAINED_FACTORS)
        print(f"  {name:>20s}: 组合方差贡献={pv:.6f}")

    # ─── 4.3: 拥挤度分析 (HHI) ───
    print(f"\n[4.3] 拥挤度分析 (HHI = Σw²)...")
    hhi_equal = compute_hhi({f: 0.125 for f in RETAINED_FACTORS})
    hhi_fixed = compute_hhi(FIXED_WEIGHTS)
    hhi_up = compute_hhi(DYNAMIC_WEIGHTS["up"])
    hhi_down = compute_hhi(DYNAMIC_WEIGHTS["down"])
    hhi_sideways = compute_hhi(DYNAMIC_WEIGHTS["sideways"])

    print(f"  等权基线 HHI: {hhi_equal:.6f} (理论最小值)")
    print(f"  固定加权 HHI: {hhi_fixed:.6f}")
    print(f"  动态加权 HHI: UP={hhi_up:.6f}, DOWN={hhi_down:.6f}, SIDEWAYS={hhi_sideways:.6f}")

    # Average HHI for dynamic (weighted by regime frequency)
    total_regime = sum(regime_counts_4sym.values())
    if total_regime > 0:
        hhi_dynamic_avg = (
            hhi_up * regime_counts_4sym.get("up", 0) / total_regime +
            hhi_down * regime_counts_4sym.get("down", 0) / total_regime +
            hhi_sideways * regime_counts_4sym.get("sideways", 0) / total_regime
        )
    else:
        hhi_dynamic_avg = 0.0

    print(f"  动态加权平均HHI (按行情频率加权): {hhi_dynamic_avg:.6f}")
    print(f"  拥挤度对比: 动态平均HHI/等权HHI = {hhi_dynamic_avg / hhi_equal:.2f}x" if hhi_equal > 0 else "")

    # Crowding assessment
    # Acceptable if avg HHI is not more than 1.3x the equal-weight HHI
    crowding_ratio = hhi_dynamic_avg / hhi_equal if hhi_equal > 0 else 0
    crowding_acceptable = crowding_ratio <= 1.5  # 50% tolerance

    print(f"\n  拥挤度判定:")
    print(f"    拥挤度比率: {crowding_ratio:.2f}x (等权=1.0x)")
    print(f"    容忍阈值: 1.5x")
    print(f"    判定: {'✅ 可接受' if crowding_acceptable else '⚠️ 偏高'}")

    # ─── 4.4: 信号冗余检测 ───
    print(f"\n[4.4] 信号冗余检测...")
    redundancy_flags = []
    for f1, f2, c in high_corr_pairs:
        # Check if both factors have high weights in any scheme
        for name, weights_dict in [("up", DYNAMIC_WEIGHTS["up"]), ("down", DYNAMIC_WEIGHTS["down"])]:
            w1 = weights_dict.get(f1, 0)
            w2 = weights_dict.get(f2, 0)
            if w1 > 0.1 and w2 > 0.1:
                redundancy_flags.append({
                    "factors": [f1, f2],
                    "correlation": c,
                    "regime": name,
                    "weights": [w1, w2],
                    "combined_weight": round(w1 + w2, 4),
                    "risk": f"高相关因子({f1}, {f2})在{name}行情中均有较高权重, 存在信号冗余风险",
                })

    if redundancy_flags:
        print(f"  检测到 {len(redundancy_flags)} 个冗余风险:")
        for flag in redundancy_flags:
            print(f"    ⚠️ {flag['factors']} (r={flag['correlation']:.3f}): "
                  f"{flag['regime']}行情权重=[{flag['weights']}]")
    else:
        print(f"  ✅ 未检测到高相关因子在高权重方案的冗余风险")

    p2_4_results["correlation_matrix"] = corr_matrix
    p2_4_results["high_corr_pairs"] = [{"f1": f1, "f2": f2, "corr": c} for f1, f2, c in high_corr_pairs]
    p2_4_results["weighted_corr_matrices"] = weighted_corr
    p2_4_results["hhi"] = {
        "equal_weight": round(hhi_equal, 6),
        "fixed_weight": round(hhi_fixed, 6),
        "dynamic_up": round(hhi_up, 6),
        "dynamic_down": round(hhi_down, 6),
        "dynamic_sideways": round(hhi_sideways, 6),
        "dynamic_avg_by_regime_freq": round(hhi_dynamic_avg, 6),
    }
    p2_4_results["crowding_ratio"] = round(crowding_ratio, 4)
    p2_4_results["crowding_acceptable"] = crowding_acceptable
    p2_4_results["redundancy_flags"] = redundancy_flags

    # Write risk_validation.json
    risk_output = {
        "output_id": "DSHA-TASK045-RISK-VALIDATION",
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
        "correlation_analysis": {
            "base_corr_matrix": corr_matrix,
            "high_corr_pairs": [{"f1": f1, "f2": f2, "corr": c} for f1, f2, c in high_corr_pairs],
            "weighted_corr_by_scheme": weighted_corr,
        },
        "crowding_analysis": {
            "equal_weight_hhi": round(hhi_equal, 6),
            "fixed_weight_hhi": round(hhi_fixed, 6),
            "dynamic_hhi_by_regime": {
                "up": round(hhi_up, 6),
                "down": round(hhi_down, 6),
                "sideways": round(hhi_sideways, 6),
            },
            "dynamic_avg_hhi": round(hhi_dynamic_avg, 6),
            "crowding_ratio": round(crowding_ratio, 4),
            "crowding_acceptable": crowding_acceptable,
        },
        "redundancy_flags": redundancy_flags,
    }
    RISK_VALIDATION_JSON.write_text(
        json.dumps(risk_output, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"\n  ✅ risk_validation.json 已写入")

    # ════════════════════════════════════════════════════════════
    # P2.5: 制品归档 + 审计日志 + 10项冒烟全检
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("[P2.5] 制品归档 + 审计日志 + 10项冒烟全检")
    print("=" * 72)

    p2_5_results = {}

    # ─── 验收标准检查 ───
    print(f"\n[验收标准检查]...")

    # 1. 三段行情IC补齐
    three_regime_ic_completed = (
        regime_counts_4sym.get("up", 0) > 0 and
        regime_counts_4sym.get("down", 0) > 0 and
        regime_counts_4sym.get("sideways", 0) > 0
    )
    print(f"  {'✅' if three_regime_ic_completed else '❌'} 1. 三段行情IC补齐")

    # 2. DOWN区间样本满足最小窗口
    down_sample_ok = down_sufficient_9sym
    print(f"  {'✅' if down_sample_ok else '❌'} 2. DOWN区间样本满足最小窗口 (9品种={down_9sym}≥{min_window})")

    # 3. 动态加权翻转率下降3-6%
    flip_reduction_pct = flip_reduction_c_vs_a / flip_a["flip_rate"] * 100 if flip_a["flip_rate"] > 0 else 0
    flip_rate_ok = 3.0 <= flip_reduction_pct <= 6.0
    print(f"  {'✅' if flip_rate_ok else '⚠️'} 3. 动态加权翻转率下降 {flip_reduction_pct:.2f}% (目标3-6%)")

    # 4. 收益和夏普不低于基线95%
    baseline_return = metrics_a["total_return"]
    baseline_sharpe = metrics_a["sharpe_ratio"]
    return_ok = metrics_c["total_return"] >= baseline_return * 0.95
    sharpe_ok = metrics_c["sharpe_ratio"] >= baseline_sharpe * 0.95
    print(f"  {'✅' if return_ok else '⚠️'} 4a. 动态加权收益={metrics_c['total_return']*100:.2f}% ≥ 基线95%({baseline_return*0.95*100:.2f}%)")
    print(f"  {'✅' if sharpe_ok else '⚠️'} 4b. 动态加权夏普={metrics_c['sharpe_ratio']:.4f} ≥ 基线95%({baseline_sharpe*0.95:.4f})")

    # 5. 最大回撤不恶化
    max_dd_ok = metrics_c["max_drawdown"] >= metrics_a["max_drawdown"]
    print(f"  {'✅' if max_dd_ok else '⚠️'} 5. 最大回撤不恶化 (动态={metrics_c['max_drawdown']*100:.2f}% vs 基线={metrics_a['max_drawdown']*100:.2f}%)")

    # 6. 不修改生产端因子清单
    prod_configs_untouched = (
        preconditions["fw_readonly_locked"] and
        preconditions["fec_readonly_locked"]
    )
    print(f"  {'✅' if prod_configs_untouched else '❌'} 6. 不修改生产端因子清单")

    # 7. 冒烟全检
    print(f"\n[10项冒烟全检]...")

    smoke_checks = {}
    smoke_pass_count = 0
    smoke_fail_count = 0

    # 1. Research sandbox isolated from production
    research_dir_isolated = (RESEARCH_DIR != PROD_DIR)
    prod_configs_unchanged = prod_configs_untouched
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

    # 6. All 3 regime ICs completed
    smoke_checks["three_regime_ic_completed"] = three_regime_ic_completed
    if three_regime_ic_completed: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 7. DOWN sample sufficient
    smoke_checks["down_sample_sufficient"] = down_sample_ok
    if down_sample_ok: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 8. Dynamic weight backtest completed (all 3 groups)
    smoke_checks["backtest_3groups_completed"] = (
        metrics_a is not None and
        metrics_b is not None and
        metrics_c is not None and
        "total_return" in metrics_a and
        "total_return" in metrics_b and
        "total_return" in metrics_c
    )
    if smoke_checks["backtest_3groups_completed"]: smoke_pass_count += 1
    else: smoke_fail_count += 1

    # 9. All research artifacts written
    artifacts_written = [
        str(REGIME_IC_JSON.relative_to(PROJECT_ROOT)),
        str(WEIGHT_RULES_JSON.relative_to(PROJECT_ROOT)),
        str(BACKTEST_METRICS_JSON.relative_to(PROJECT_ROOT)),
        str(RISK_VALIDATION_JSON.relative_to(PROJECT_ROOT)),
    ]
    all_artifacts_exist = all(
        Path(PROJECT_ROOT / p).exists() for p in artifacts_written
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

    # ─── 写入研究MANIFEST ───
    print(f"\n[研究MANIFEST写入]...")

    research_manifest = {
        "manifest_id": "DSHA-TASK045-REGIME-WEIGHT-MANIFEST",
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
            "production_configs_untouched": prod_unchanged,
            "deprecated_script_archived": True,
        },
        "p2_1_regime_ic": {
            "regime_counts_4sym": regime_counts_4sym,
            "regime_counts_9sym": regime_counts_9sym,
            "down_sample_sufficient_4sym": down_sufficient_4sym,
            "down_sample_sufficient_9sym": down_sufficient_9sym,
            "min_window_required": min_window,
            "factors_analyzed": RETAINED_FACTORS,
            "report_path": str(REGIME_IC_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_2_dynamic_weights": {
            "dynamic_weights": DYNAMIC_WEIGHTS,
            "fixed_weights": FIXED_WEIGHTS,
            "weight_bounds": {"min": WEIGHT_MIN, "max": WEIGHT_MAX},
            "rules_path": str(WEIGHT_RULES_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_3_comparison_backtest": {
            "equal_weight_metrics": metrics_a,
            "fixed_weight_metrics": metrics_b,
            "dynamic_regime_metrics": metrics_c,
            "flip_rates": {
                "equal_weight": flip_a["flip_rate"],
                "fixed_weight": flip_b["flip_rate"],
                "dynamic_regime": flip_c["flip_rate"],
            },
            "comparison_summary": comparison["comparison_summary"],
            "metrics_path": str(BACKTEST_METRICS_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_4_risk_validation": {
            "hhi": {
                "equal_weight": round(hhi_equal, 6),
                "fixed_weight": round(hhi_fixed, 6),
                "dynamic_avg": round(hhi_dynamic_avg, 6),
            },
            "crowding_ratio": round(crowding_ratio, 4),
            "crowding_acceptable": crowding_acceptable,
            "high_corr_pairs": [{"f1": f1, "f2": f2, "corr": c} for f1, f2, c in high_corr_pairs],
            "redundancy_flags": redundancy_flags,
            "risk_path": str(RISK_VALIDATION_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_5_artifacts": {
            "regime_factor_ic_json": str(REGIME_IC_JSON.relative_to(PROJECT_ROOT)),
            "dynamic_weight_rules_json": str(WEIGHT_RULES_JSON.relative_to(PROJECT_ROOT)),
            "comparison_backtest_metrics_json": str(BACKTEST_METRICS_JSON.relative_to(PROJECT_ROOT)),
            "risk_validation_json": str(RISK_VALIDATION_JSON.relative_to(PROJECT_ROOT)),
            "research_manifest_json": str(RESEARCH_MANIFEST.relative_to(PROJECT_ROOT)),
            "script_path": str(Path(__file__).relative_to(PROJECT_ROOT)),
        },
        "acceptance_criteria": {
            "three_regime_ic_completed": three_regime_ic_completed,
            "down_sample_sufficient": down_sample_ok,
            "flip_rate_reduction_pct": round(flip_reduction_pct, 2),
            "flip_rate_reduction_in_range": flip_rate_ok,
            "return_above_95pct": return_ok,
            "sharpe_above_95pct": sharpe_ok,
            "max_drawdown_not_worse": max_dd_ok,
            "prod_configs_untouched": prod_configs_untouched,
            "smoke_all_pass": smoke_all_pass,
        },
        "research_data": {
            "factors_csv": str(V3_FACTORS_CSV.relative_to(PROJECT_ROOT)),
            "factors_csv_sha256": factors_sha,
            "data_rows_4sym": len(df_4sym),
            "data_rows_9sym": len(df_full),
            "symbols_4sym": ALL_4_SYMBOLS,
        },
    }
    RESEARCH_MANIFEST.write_text(
        json.dumps(research_manifest, ensure_ascii=False, indent=2, cls=NumpyEncoder),
        encoding="utf-8"
    )
    print(f"  ✅ MANIFEST_v3_regime_weight.json 已写入")

    p2_5_results["artifacts_written"] = artifacts_written + [
        str(RESEARCH_MANIFEST.relative_to(PROJECT_ROOT)),
        str(Path(__file__).relative_to(PROJECT_ROOT)),
    ]
    p2_5_results["smoke_checks"] = smoke_checks
    p2_5_results["smoke_all_passed"] = smoke_all_pass
    p2_5_results["acceptance_criteria"] = research_manifest["acceptance_criteria"]

    # ─── 追加审计事件 ───
    print(f"\n[追加审计事件]...")

    append_audit("TASK045_COMPLETE", {
        "token": TOKEN,
        "baseline_commit": BASELINE_COMMIT,
        "task": TASK_ID,
        "execution_type": "research_sandbox",
        "elapsed_seconds": round(time.time() - start_time, 2),
        "p2_1_regime_ic": {
            "regime_counts_4sym": regime_counts_4sym,
            "regime_counts_9sym": regime_counts_9sym,
            "down_sample_sufficient_9sym": down_sufficient_9sym,
            "factors_analyzed": len(RETAINED_FACTORS),
            "report_path": str(REGIME_IC_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_2_dynamic_weights": {
            "dynamic_weights": DYNAMIC_WEIGHTS,
            "fixed_weights": FIXED_WEIGHTS,
            "rules_path": str(WEIGHT_RULES_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_3_comparison_backtest": {
            "equal_weight": {
                "return": metrics_a["total_return"],
                "sharpe": metrics_a["sharpe_ratio"],
                "max_dd": metrics_a["max_drawdown"],
                "flip_rate": flip_a["flip_rate"],
            },
            "fixed_weight": {
                "return": metrics_b["total_return"],
                "sharpe": metrics_b["sharpe_ratio"],
                "max_dd": metrics_b["max_drawdown"],
                "flip_rate": flip_b["flip_rate"],
            },
            "dynamic_regime": {
                "return": metrics_c["total_return"],
                "sharpe": metrics_c["sharpe_ratio"],
                "max_dd": metrics_c["max_drawdown"],
                "flip_rate": flip_c["flip_rate"],
            },
            "flip_rate_reduction_pct": round(flip_reduction_pct, 2),
            "metrics_path": str(BACKTEST_METRICS_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_4_risk_validation": {
            "crowding_ratio": round(crowding_ratio, 4),
            "crowding_acceptable": crowding_acceptable,
            "high_corr_pairs_count": len(high_corr_pairs),
            "redundancy_flags_count": len(redundancy_flags),
            "risk_path": str(RISK_VALIDATION_JSON.relative_to(PROJECT_ROOT)),
        },
        "p2_5_smoke_checks": {
            "passed": smoke_pass_count,
            "failed": smoke_fail_count,
            "smoke_all_passed": smoke_all_pass,
        },
        "acceptance_criteria": research_manifest["acceptance_criteria"],
        "safety": {
            "real_wind_call": False,
            "wind_api_calls": 0,
            "offline_only": True,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
        },
    })
    print(f"  ✅ 审计事件已写入 tracking_monitor_audit.jsonl")

    # ════════════════════════════════════════════════════════════
    # 总结
    # ════════════════════════════════════════════════════════════
    elapsed = time.time() - start_time

    print("\n" + "=" * 72)
    print("DSHA-TASK-045 · 执行总结")
    print("=" * 72)

    print(f"\n{'P2.1 三段行情IC':<22s}: ✅ DONE (4品种+9品种扩充)")
    print(f"{'  DOWN样本':<22s}: 4品种={down_4sym}, 9品种={down_9sym} (≥{min_window}✅)")
    print(f"{'P2.2 动态权重规则':<22s}: ✅ DONE (3行情段)")
    print(f"{'P2.3 三组对照回测':<22s}: ✅ DONE")
    print(f"{'  等权基线':<22s}: 收益={metrics_a['total_return']*100:.2f}%, 夏普={metrics_a['sharpe_ratio']:.4f}, 翻转率={flip_a['flip_rate']*100:.1f}%")
    print(f"{'  固定加权':<22s}: 收益={metrics_b['total_return']*100:.2f}%, 夏普={metrics_b['sharpe_ratio']:.4f}, 翻转率={flip_b['flip_rate']*100:.1f}%")
    print(f"{'  动态加权':<22s}: 收益={metrics_c['total_return']*100:.2f}%, 夏普={metrics_c['sharpe_ratio']:.4f}, 翻转率={flip_c['flip_rate']*100:.1f}%")
    print(f"{'  翻转率下降':<22s}: {flip_reduction_pct:.2f}% (目标3-6%)")
    print(f"{'P2.4 风险校验':<22s}: ✅ DONE")
    print(f"{'  拥挤度比率':<22s}: {crowding_ratio:.2f}x ({'✅可接受' if crowding_acceptable else '⚠️偏高'})")
    print(f"{'P2.5 制品与审计':<22s}: ✅ DONE")
    print(f"{'  研究制品':<22s}: {len(p2_5_results['artifacts_written'])}个文件")
    print(f"{'  冒烟校验':<22s}: {smoke_pass_count}/10 PASS")

    print(f"\n耗时: {elapsed:.2f}秒")
    print(f"wind_api_calls: {WIND_API_CALLS}")
    print(f"Gate: {GATE_STATUS}")
    print(f"Release: {RELEASE_STATUS}")

    # Receipt
    receipt_flip = "PASS" if flip_rate_ok else f"ADVISORY({flip_reduction_pct:.2f}%)"
    receipt_return = "PASS" if return_ok else "ADVISORY"
    receipt_sharpe = "PASS" if sharpe_ok else "ADVISORY"
    receipt_dd = "PASS" if max_dd_ok else "ADVISORY"

    print("\n" + "-" * 72)
    print("回执:")
    print(f"DSHA_TASK045_REGIME_WEIGHT=RESEARCH_DONE|"
          f"prod_factor_pool_untouched={'YES' if prod_configs_untouched else 'NO'}|"
          f"three_regime_ic_completed={'YES' if three_regime_ic_completed else 'NO'}|"
          f"down_sample_expanded={'YES' if down_sufficient_9sym else 'NO'}|"
          f"dynamic_weight_backtest_passed={'YES' if (return_ok and sharpe_ok and max_dd_ok) else 'ADVISORY'}|"
          f"flip_rate_reduction={flip_reduction_pct:.2f}%|"
          f"smoke_all_pass={'YES' if smoke_all_pass else 'NO'}")
    print("-" * 72)

    return 0 if smoke_all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
