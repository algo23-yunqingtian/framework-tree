#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
# Force UTF-8 output for Chinese console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
"""
DSHA-P59/P61 · 极简回测框架骨架 — 输出标准化版
(Backtest Skeleton — OFFLINE ONLY, NO REAL WIND DATA)

═══════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不读取任何真实 Wind 数据
═══════════════════════════════════════════════════════════════════════
REAL_WIND_CALL: False (不可修改)
wind_api_calls: 0 (本模块不触发任何 Wind API 调用)
gate: CLOSED/HOLD | release_permit: NOT_ISSUED

P61 标准化输出:
  每次回测自动生成 3 类文件 + 自动归档:
  (1) backtest_metrics.csv      — 结构化指标表格 (年化收益/波动率/回撤/夏普/IC)
  (2) net_value_series.csv       — 时序净值 (日期/价格/因子值/日收益/累计收益/净值)
  (3) backtest_snapshot.json     — 快照文件 (仪表盘读取用)
  (4) 自动归档 → artifacts/backtest_archive/{timestamp}/

数据流:
  factor_data_loader → factor_constructor → 本模块

前置校验:
  无输入原始数据时直接返回 WAIT 状态, 不报错崩溃。

输入:
  - 因子序列 (来自 factor_constructor)
  - 价格序列 (来自 factor_data_loader)

输出目录:
  - code/backtest_output/       (实时输出)
  - artifacts/backtest_archive/ (自动归档)

作者: DSHA-P59 / DSHA-P61
基线: feature/v88-g1
"""

import csv
import json
import os
import shutil
import sys
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 — 不可切换 (本轮工作)
# ════════════════════════════════════════════════════════════════

REAL_WIND_CALL = False
WIND_API_CALLS = 0

# ════════════════════════════════════════════════════════════════
# 项目路径
# ════════════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKTEST_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "backtest_output"
)
BACKTEST_ARCHIVE_DIR = os.path.join(PROJECT_ROOT, "artifacts", "backtest_archive")


# ════════════════════════════════════════════════════════════════
# 回测状态枚举
# ════════════════════════════════════════════════════════════════

BACKTEST_STATUS_WAIT = "WAIT"          # 等待输入数据
BACKTEST_STATUS_READY = "READY"         # 数据就绪, 可计算
BACKTEST_STATUS_OK = "OK"               # 回测完成
BACKTEST_STATUS_ERROR = "ERROR"         # 回测错误


# ════════════════════════════════════════════════════════════════
# 前置校验
# ════════════════════════════════════════════════════════════════

def check_inputs(factor_data: Optional[Dict[str, Any]],
                 price_data: Optional[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """
    前置校验: 检查输入数据是否就绪。

    Args:
        factor_data: factor_constructor 输出 (可 None)
        price_data: factor_data_loader 输出 (可 None)

    Returns:
        (status, notes) 元组
    """
    notes = []
    has_factor = factor_data is not None and factor_data.get("factor_values") is not None
    has_price = price_data is not None and price_data.get("values") is not None

    if not has_factor:
        notes.append("缺少因子序列 (factor_data)")
    if not has_price:
        notes.append("缺少价格序列 (price_data)")

    if not has_factor and not has_price:
        return BACKTEST_STATUS_WAIT, ["无输入数据 — 等待小样数据落地"]
    if not has_factor:
        return BACKTEST_STATUS_WAIT, notes
    if not has_price:
        return BACKTEST_STATUS_WAIT, notes

    # 检查长度匹配
    factor_vals = factor_data.get("factor_values", [])
    price_vals = price_data.get("values", [])

    if len(factor_vals) == 0:
        return BACKTEST_STATUS_WAIT, ["因子序列为空"]

    # 对齐: 因子序列长度 ≤ 价格序列长度
    if len(factor_vals) > len(price_vals):
        return BACKTEST_STATUS_WAIT, [
            f"因子序列({len(factor_vals)}) > 价格序列({len(price_vals)}), 长度不匹配"
        ]

    return BACKTEST_STATUS_READY, []


# ════════════════════════════════════════════════════════════════
# 基础指标计算
# ════════════════════════════════════════════════════════════════

def compute_cumulative_return(
    prices: List[float],
) -> Tuple[List[float], float]:
    """
    计算累计收益率序列。

    Args:
        prices: 价格序列

    Returns:
        (累计收益率列表, 总累计收益率)
    """
    if len(prices) < 2:
        return [], 0.0

    returns = []
    cum_ret = 1.0
    for i in range(1, len(prices)):
        daily_ret = (prices[i] - prices[i - 1]) / prices[i - 1]
        cum_ret *= (1 + daily_ret)
        returns.append(round(cum_ret - 1.0, 8))

    return returns, round(cum_ret - 1.0, 8)


def compute_volatility(
    prices: List[float],
) -> Tuple[float, float]:
    """
    计算年化波动率和日均波动率。

    Args:
        prices: 价格序列

    Returns:
        (年化波动率, 日均波动率)
    """
    if len(prices) < 3:
        return 0.0, 0.0

    daily_returns = []
    for i in range(1, len(prices)):
        r = (prices[i] - prices[i - 1]) / prices[i - 1]
        daily_returns.append(r)

    mean_r = sum(daily_returns) / len(daily_returns)
    var = sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
    daily_vol = math.sqrt(var)
    annual_vol = daily_vol * math.sqrt(252)  # 年化

    return round(annual_vol, 8), round(daily_vol, 8)


def compute_max_drawdown(
    prices: List[float],
) -> Tuple[float, float]:
    """
    计算最大回撤。

    Args:
        prices: 价格序列

    Returns:
        (最大回撤比率, 最大回撤时的价格)
    """
    if len(prices) < 2:
        return 0.0, prices[0] if prices else 0.0

    max_price = prices[0]
    max_dd = 0.0
    max_dd_price = prices[0]

    for p in prices:
        if p > max_price:
            max_price = p
        dd = (p - max_price) / max_price
        if dd < max_dd:
            max_dd = dd
            max_dd_price = p

    return round(max_dd, 8), max_dd_price


def compute_sharpe_ratio(
    prices: List[float],
    risk_free_rate: float = 0.0,
) -> float:
    """
    计算年化夏普比率。

    Args:
        prices: 价格序列
        risk_free_rate: 年化无风险利率 (默认0)

    Returns:
        夏普比率
    """
    if len(prices) < 3:
        return 0.0

    daily_returns = []
    for i in range(1, len(prices)):
        r = (prices[i] - prices[i - 1]) / prices[i - 1]
        daily_returns.append(r)

    mean_r = sum(daily_returns) / len(daily_returns)
    var = sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
    std = math.sqrt(var)

    if std == 0:
        return 0.0

    daily_rf = risk_free_rate / 252
    daily_sharpe = (mean_r - daily_rf) / std
    annual_sharpe = daily_sharpe * math.sqrt(252)

    return round(annual_sharpe, 8)


# ════════════════════════════════════════════════════════════════
# 回测主函数
# ════════════════════════════════════════════════════════════════

def run_backtest(
    factor_data: Optional[Dict[str, Any]] = None,
    price_data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    回测主入口 — 计算基础回测指标。

    Args:
        factor_data: factor_constructor 输出 (因子序列)
        price_data: factor_data_loader 输出 (价格序列)
        config: 回测配置参数

    Returns:
        回测结果字典, 包含 status 字段:
          - WAIT: 等待输入数据
          - OK: 回测完成
          - ERROR: 回测错误
    """
    if config is None:
        config = {
            "risk_free_rate": 0.0,
            "initial_capital": 100000.0,
        }

    # ── 前置校验 ──
    pre_status, pre_notes = check_inputs(factor_data, price_data)

    if pre_status == BACKTEST_STATUS_WAIT:
        return {
            "status": BACKTEST_STATUS_WAIT,
            "notes": pre_notes,
            "factor_data_available": factor_data is not None,
            "price_data_available": price_data is not None,
            "real_wind_call": REAL_WIND_CALL,
            "wind_api_calls": WIND_API_CALLS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── 提取数据 ──
    prices = price_data["values"]
    dates = price_data["dates"]
    factor_values = factor_data["factor_values"]
    factor_dates = factor_data["factor_dates"]
    factor_type = factor_data.get("factor_type", "unknown")
    factor_id = factor_data.get("factor_id", "unknown")

    # 对齐: 从第一个因子值开始的价格序列
    # factor_values 对应 prices 的最后 len(factor_values) 个
    offset = len(prices) - len(factor_values)
    aligned_prices = prices[offset:]
    aligned_dates = dates[offset:]

    # ── 计算基础指标 ──
    cum_returns, total_return = compute_cumulative_return(aligned_prices)
    annual_vol, daily_vol = compute_volatility(aligned_prices)
    max_dd, max_dd_price = compute_max_drawdown(aligned_prices)
    sharpe = compute_sharpe_ratio(aligned_prices,
                                    risk_free_rate=config.get("risk_free_rate", 0.0))

    # ── 因子统计 ──
    factor_stats = _compute_factor_stats(factor_values)

    # ── 构建结果 ──
    result = {
        "status": BACKTEST_STATUS_OK,
        "summary": {
            "factor_type": factor_type,
            "factor_id": factor_id,
            "symbol": price_data.get("symbol", "UNKNOWN"),
            "indicator": price_data.get("indicator", "UNKNOWN"),
            "data_source": price_data.get("source", "UNKNOWN"),
            "total_return": total_return,
            "annual_volatility": annual_vol,
            "daily_volatility": daily_vol,
            "max_drawdown": max_dd,
            "sharpe_ratio": sharpe,
            "trading_days": len(aligned_prices),
            "factor_points": len(factor_values),
            "start_date": aligned_dates[0] if aligned_dates else "N/A",
            "end_date": aligned_dates[-1] if aligned_dates else "N/A",
            "config": config,
        },
        "factor_stats": factor_stats,
        "equity_curve": [round(aligned_prices[i], 2) for i in range(len(aligned_prices))],
        "return_curve": cum_returns,
        "factor_values": factor_values,
        "aligned_dates": aligned_dates,
        "notes": [],
        "real_wind_call": REAL_WIND_CALL,
        "wind_api_calls": WIND_API_CALLS,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 添加数据源信息
    result["data_provenance"] = {
        "price_source": price_data.get("source", "UNKNOWN"),
        "price_status": price_data.get("status", "UNKNOWN"),
        "price_metadata": price_data.get("metadata", {}),
        "factor_data_source": factor_data.get("data_source", "UNKNOWN"),
    }

    return result


def _compute_factor_stats(factors: List[float]) -> Dict[str, Any]:
    """计算因子统计量"""
    if not factors:
        return {}

    mean = sum(factors) / len(factors)
    var = sum((f - mean) ** 2 for f in factors) / len(factors)
    std = math.sqrt(var)
    min_f = min(factors)
    max_f = max(factors)

    # 分位数
    sorted_f = sorted(factors)
    n = len(sorted_f)
    p25 = sorted_f[int(n * 0.25)]
    p50 = sorted_f[int(n * 0.50)]
    p75 = sorted_f[int(n * 0.75)]

    # 正负因子比例
    positive = sum(1 for f in factors if f > 0)
    negative = sum(1 for f in factors if f < 0)
    zero = sum(1 for f in factors if f == 0)

    return {
        "count": len(factors),
        "mean": round(mean, 8),
        "std": round(std, 8),
        "min": round(min_f, 8),
        "max": round(max_f, 8),
        "p25": round(p25, 8),
        "p50": round(p50, 8),
        "p75": round(p75, 8),
        "positive_count": positive,
        "negative_count": negative,
        "zero_count": zero,
        "positive_ratio": round(positive / len(factors), 4),
        "negative_ratio": round(negative / len(factors), 4),
    }


def compute_IC(
    factor_values: List[float],
    forward_returns: List[float],
) -> Tuple[float, float, int]:
    """
    计算信息系数 (Information Coefficient) — Pearson 相关系数。

    IC = corr(factor_t, forward_return_{t+1})

    Args:
        factor_values: 因子值序列
        forward_returns: 向前收益率序列 (与因子值一一对应)

    Returns:
        (IC值, IC_IR值, 有效样本数)
        IC_IR = mean(IC_series) / std(IC_series)  — 此处用整体IC的标准差近似
    """
    n = min(len(factor_values), len(forward_returns))
    if n < 3:
        return 0.0, 0.0, n

    fv = factor_values[:n]
    fr = forward_returns[:n]

    mean_f = sum(fv) / n
    mean_r = sum(fr) / n

    var_f = sum((f - mean_f) ** 2 for f in fv) / n
    var_r = sum((r - mean_r) ** 2 for r in fr) / n

    cov_fr = sum((fv[i] - mean_f) * (fr[i] - mean_r) for i in range(n)) / n

    std_f = math.sqrt(var_f)
    std_r = math.sqrt(var_r)

    if std_f == 0 or std_r == 0:
        return 0.0, 0.0, n

    ic = cov_fr / (std_f * std_r)
    ic_ir = round(ic * math.sqrt(n), 8) if n > 0 else 0.0

    return round(ic, 8), ic_ir, n


# ════════════════════════════════════════════════════════════════
# P61: 标准化输出 — CSV 指标表格 + 时序净值 + 快照 JSON
# ════════════════════════════════════════════════════════════════

def save_backtest_metrics_csv(
    result: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """
    生成结构化回测指标 CSV 文件。

    输出列:
      metric_name | value | unit | description

    Args:
        result: run_backtest() 返回的结果字典
        output_path: 可选的输出路径 (默认在 output_dir 下)

    Returns:
        生成的 CSV 文件路径
    """
    if result.get("status") == BACKTEST_STATUS_WAIT:
        return ""

    s = result["summary"]
    fs = result.get("factor_stats", {})
    ic_value, ic_ir, ic_n = _compute_ic_from_result(result)

    # 指标定义: (name, value, unit, description)
    metrics = [
        ("factor_type",          str(s["factor_type"]),          "-",    "因子类型"),
        ("factor_id",            str(s["factor_id"]),            "-",    "因子ID"),
        ("symbol",               str(s["symbol"]),               "-",    "品种"),
        ("indicator",            str(s["indicator"]),            "-",    "指标"),
        ("data_source",          str(s["data_source"]),          "-",    "数据源"),
        ("trading_days",         str(s["trading_days"]),         "days", "交易日数"),
        ("factor_points",        str(s["factor_points"]),        "-",    "因子点数"),
        ("start_date",           str(s["start_date"]),           "date", "起始日期"),
        ("end_date",             str(s["end_date"]),             "date", "结束日期"),
        ("",                     "",                             "",     ""),
        ("total_return",         f"{s['total_return']:.6f}",     "%",    "总收益率"),
        ("annualized_return",    f"{_annualized_return(s):.6f}",  "%",   "年化收益率"),
        ("annual_volatility",    f"{s['annual_volatility']:.6f}", "%",   "年化波动率"),
        ("daily_volatility",     f"{s['daily_volatility']:.6f}", "%",    "日均波动率"),
        ("max_drawdown",         f"{s['max_drawdown']:.6f}",     "%",    "最大回撤"),
        ("sharpe_ratio",         f"{s['sharpe_ratio']:.6f}",     "-",    "夏普比率"),
        ("information_coefficient", f"{ic_value:.6f}",           "-",    "信息系数(IC)"),
        ("IC_IR",                f"{ic_ir:.6f}",                 "-",    "IC信息比率"),
        ("IC_sample_size",       str(ic_n),                      "-",    "IC有效样本数"),
        ("",                     "",                             "",     ""),
        ("factor_mean",          str(fs.get("mean", "N/A")),     "-",    "因子均值"),
        ("factor_std",           str(fs.get("std", "N/A")),      "-",    "因子标准差"),
        ("factor_min",           str(fs.get("min", "N/A")),      "-",    "因子最小值"),
        ("factor_max",           str(fs.get("max", "N/A")),      "-",    "因子最大值"),
        ("factor_p25",           str(fs.get("p25", "N/A")),      "-",    "因子25%分位"),
        ("factor_p50",           str(fs.get("p50", "N/A")),      "-",    "因子50%分位"),
        ("factor_p75",           str(fs.get("p75", "N/A")),      "-",    "因子75%分位"),
        ("positive_ratio",       str(fs.get("positive_ratio", "N/A")), "%", "正值比例"),
        ("negative_ratio",       str(fs.get("negative_ratio", "N/A")), "%", "负值比例"),
        ("",                     "",                             "",     ""),
        ("real_wind_call",       str(REAL_WIND_CALL),            "bool", "是否调用Wind"),
        ("wind_api_calls",       str(WIND_API_CALLS),            "int",  "Wind API调用次数"),
        ("timestamp",            str(result["timestamp"]),       "ISO8601", "生成时间"),
    ]

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"backtest_metrics_{s['factor_type']}_{s['symbol']}_{timestamp}.csv"
        output_path = os.path.join(BACKTEST_OUTPUT_DIR, fname)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric_name", "value", "unit", "description"])
        for row in metrics:
            writer.writerow(row)

    return output_path


def save_net_value_series_csv(
    result: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """
    生成时序净值 CSV 文件。

    输出列:
      date | close_price | factor_value | daily_return | cumulative_return | net_value

    Args:
        result: run_backtest() 返回的结果字典
        output_path: 可选的输出路径

    Returns:
        生成的 CSV 文件路径
    """
    if result.get("status") == BACKTEST_STATUS_WAIT:
        return ""

    s = result["summary"]
    dates = result.get("aligned_dates", [])
    equity = result.get("equity_curve", [])
    cum_returns = result.get("return_curve", [])
    factor_values = result.get("factor_values", [])
    initial_capital = s.get("config", {}).get("initial_capital", 100000.0)

    # 对齐: 因子值从 offset 位置开始
    n_dates = len(dates)
    n_equity = len(equity)
    n_factor = len(factor_values)
    factor_offset = n_dates - n_factor

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"net_value_series_{s['factor_type']}_{s['symbol']}_{timestamp}.csv"
        output_path = os.path.join(BACKTEST_OUTPUT_DIR, fname)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "close_price", "factor_value",
            "daily_return", "cumulative_return", "net_value"
        ])

        for i in range(n_dates):
            d = dates[i] if i < len(dates) else ""
            price = equity[i] if i < n_equity else ""
            fv_idx = i - factor_offset
            fv = factor_values[fv_idx] if 0 <= fv_idx < n_factor else ""
            # 日收益率: 从日价格差计算
            if i > 0 and i - 1 < n_equity and equity[i - 1] > 0:
                daily_ret = (equity[i] - equity[i - 1]) / equity[i - 1]
            else:
                daily_ret = ""
            # 累计收益率: 从 return_curve 取
            cr_idx = i - 1  # return_curve[0] 对应第2天
            cr = cum_returns[cr_idx] if 0 <= cr_idx < len(cum_returns) else (
                0.0 if i == 0 else ""
            )
            # 净值: initial_capital * (1 + cumulative_return)
            if cr != "" and isinstance(cr, (int, float)):
                nv = round(initial_capital * (1 + cr), 2)
            elif i == 0:
                nv = round(initial_capital, 2)
            else:
                nv = ""

            writer.writerow([
                d, price,
                round(fv, 8) if isinstance(fv, (int, float)) else fv,
                round(daily_ret, 8) if isinstance(daily_ret, (int, float)) else daily_ret,
                round(cr, 8) if isinstance(cr, (int, float)) else cr,
                nv,
            ])

    return output_path


def save_backtest_snapshot_json(
    result: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """
    生成回测快照 JSON 文件 (用于仪表盘读取)。

    快照内容:
      - 回测元数据 (factor_type, symbol, 时间戳)
      - 结构化指标摘要
      - 因子统计
      - 数据溯源
      - 归档路径引用

    Args:
        result: run_backtest() 返回的结果字典
        output_path: 可选的输出路径

    Returns:
        生成的 JSON 文件路径
    """
    if result.get("status") == BACKTEST_STATUS_WAIT:
        return ""

    s = result["summary"]
    fs = result.get("factor_stats", {})
    ic_value, ic_ir, ic_n = _compute_ic_from_result(result)

    snapshot = {
        "snapshot_id": f"BT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{s['factor_type'][:3].upper()}",
        "created_at": result["timestamp"],
        "status": result["status"],
        "metadata": {
            "factor_type": s["factor_type"],
            "factor_id": s["factor_id"],
            "symbol": s["symbol"],
            "indicator": s["indicator"],
            "data_source": s["data_source"],
            "start_date": s["start_date"],
            "end_date": s["end_date"],
            "trading_days": s["trading_days"],
            "factor_points": s["factor_points"],
            "config": s.get("config", {}),
        },
        "metrics": {
            "total_return": s["total_return"],
            "annualized_return": round(_annualized_return(s), 8),
            "annual_volatility": s["annual_volatility"],
            "daily_volatility": s["daily_volatility"],
            "max_drawdown": s["max_drawdown"],
            "sharpe_ratio": s["sharpe_ratio"],
            "information_coefficient": ic_value,
            "IC_IR": ic_ir,
            "IC_sample_size": ic_n,
        },
        "factor_stats": {
            "count": fs.get("count", 0),
            "mean": fs.get("mean", 0.0),
            "std": fs.get("std", 0.0),
            "min": fs.get("min", 0.0),
            "max": fs.get("max", 0.0),
            "p25": fs.get("p25", 0.0),
            "p50": fs.get("p50", 0.0),
            "p75": fs.get("p75", 0.0),
            "positive_ratio": fs.get("positive_ratio", 0.0),
            "negative_ratio": fs.get("negative_ratio", 0.0),
        },
        "equity_curve_summary": {
            "length": len(result.get("equity_curve", [])),
            "start_value": result.get("equity_curve", [0])[0] if result.get("equity_curve") else 0,
            "end_value": result.get("equity_curve", [0])[-1] if result.get("equity_curve") else 0,
            "preview_first5": result.get("equity_curve", [])[:5],
        },
        "data_provenance": result.get("data_provenance", {}),
        "safety": {
            "real_wind_call": result["real_wind_call"],
            "wind_api_calls": result["wind_api_calls"],
        },
        "archive_info": {},  # 填充后回填
    }

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"backtest_snapshot_{s['factor_type']}_{s['symbol']}_{timestamp}.json"
        output_path = os.path.join(BACKTEST_OUTPUT_DIR, fname)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    return output_path


def archive_backtest_result(
    files: Dict[str, str],
    result: Dict[str, Any],
) -> str:
    """
    将回测结果文件自动归档到 artifacts/backtest_archive/{timestamp}/。

    归档目录结构:
      artifacts/backtest_archive/
        20261018_130000_momentum_ZN.SHF/
          backtest_metrics_xxx.csv
          net_value_series_xxx.csv
          backtest_snapshot_xxx.json
          backtest_xxx.md           (原有 MD 摘要)
          backtest_xxx.json        (原有 JSON)
          MANIFEST.json            (归档清单)

    Args:
        files: 文件路径字典 {"md": ..., "json": ..., "metrics_csv": ..., ...}
        result: run_backtest() 返回的结果字典

    Returns:
        归档目录路径
    """
    s = result.get("summary", {})
    factor_type = s.get("factor_type", "unknown")
    symbol = s.get("symbol", "UNKNOWN")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{timestamp}_{factor_type}_{symbol}"
    archive_dir = os.path.join(BACKTEST_ARCHIVE_DIR, archive_name)

    os.makedirs(archive_dir, exist_ok=True)

    # 复制所有文件到归档目录
    manifest = {
        "archive_id": archive_name,
        "created_at": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "factor_type": factor_type,
        "symbol": symbol,
        "files": [],
        "real_wind_call": result.get("real_wind_call", REAL_WIND_CALL),
        "wind_api_calls": result.get("wind_api_calls", WIND_API_CALLS),
    }

    for key, filepath in files.items():
        if filepath and os.path.exists(filepath):
            basename = os.path.basename(filepath)
            dest = os.path.join(archive_dir, basename)
            shutil.copy2(filepath, dest)
            manifest["files"].append({
                "type": key,
                "basename": basename,
                "source": filepath,
                "archived": dest,
            })

    # 写入归档清单
    manifest_path = os.path.join(archive_dir, "MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return archive_dir


def _compute_ic_from_result(result: Dict[str, Any]) -> Tuple[float, float, int]:
    """从回测结果中提取因子值和收益率, 计算 IC。"""
    factor_values = result.get("factor_values", [])
    aligned_dates = result.get("aligned_dates", [])
    equity_curve = result.get("equity_curve", [])

    if not factor_values or not equity_curve:
        return 0.0, 0.0, 0

    # forward_returns: equity[i+1] / equity[i] - 1
    # factor_values 与 equity_curve 的最后 len(factor_values) 个对齐
    n = len(factor_values)
    total = len(equity_curve)
    offset = total - n

    forward_returns = []
    for i in range(n):
        idx = offset + i
        if idx < total - 1:
            fr = (equity_curve[idx + 1] - equity_curve[idx]) / equity_curve[idx]
            forward_returns.append(fr)
        else:
            forward_returns.append(0.0)

    return compute_IC(factor_values, forward_returns)


def _annualized_return(result: Dict[str, Any]) -> float:
    """从总收益率计算年化收益率。支持传入完整result或summary字典。"""
    # 支持两种输入: 完整result (含summary键) 或 summary字典本身
    s = result.get("summary", result)
    total_return = s.get("total_return", 0.0)
    trading_days = s.get("trading_days", 1)

    if trading_days <= 0:
        return 0.0

    # 年化: (1 + total_return)^(252/trading_days) - 1
    try:
        return round((1 + total_return) ** (252.0 / trading_days) - 1, 8)
    except (OverflowError, ZeroDivisionError):
        return 0.0


# ════════════════════════════════════════════════════════════════
# 结果输出: Markdown + JSON + CSV + 快照 + 归档
# ════════════════════════════════════════════════════════════════

def generate_summary_md(result: Dict[str, Any]) -> str:
    """生成回测摘要 Markdown 文本"""
    if result["status"] == BACKTEST_STATUS_WAIT:
        return (
            "# 回测摘要\n\n"
            "**状态**: ⏳ WAIT — 等待输入数据\n\n"
            + "\n".join(f"- {n}" for n in result.get("notes", []))
            + "\n\n"
            "> REAL_WIND_CALL=False | wind_api_calls=0\n"
        )

    s = result["summary"]
    fs = result.get("factor_stats", {})

    md = f"""# 回测摘要 · {s['factor_type']} · {s['symbol']}

**状态**: ✅ OK | **生成时间**: {result['timestamp']}

---

## 基本参数

| 项目 | 值 |
|------|----|
| 因子类型 | {s['factor_type']} |
| 因子ID | {s['factor_id']} |
| 品种 | {s['symbol']} |
| 指标 | {s['indicator']} |
| 数据源 | {s['data_source']} |
| 交易日数 | {s['trading_days']} |
| 因子点数 | {s['factor_points']} |
| 起始日期 | {s['start_date']} |
| 结束日期 | {s['end_date']} |

## 回测指标

| 指标 | 值 |
|------|-----|
| 累计收益率 | {s['total_return']:.4%} |
| 年化波动率 | {s['annual_volatility']:.4%} |
| 日均波动率 | {s['daily_volatility']:.6%} |
| 最大回撤 | {s['max_drawdown']:.4%} |
| 夏普比率 | {s['sharpe_ratio']:.4f} |

## 因子统计

| 统计量 | 值 |
|--------|-----|
| 计数 | {fs.get('count', 'N/A')} |
| 均值 | {fs.get('mean', 'N/A')} |
| 标准差 | {fs.get('std', 'N/A')} |
| 最小值 | {fs.get('min', 'N/A')} |
| 最大值 | {fs.get('max', 'N/A')} |
| 25%分位 | {fs.get('p25', 'N/A')} |
| 50%分位 | {fs.get('p50', 'N/A')} |
| 75%分位 | {fs.get('p75', 'N/A')} |
| 正值比例 | {fs.get('positive_ratio', 'N/A')} |
| 负值比例 | {fs.get('negative_ratio', 'N/A')} |

## 数据溯源

- 价格数据源: {result['data_provenance']['price_source']}
- 价格状态: {result['data_provenance']['price_status']}
- 因子数据源: {result['data_provenance']['factor_data_source']}

---

> REAL_WIND_CALL={result['real_wind_call']} | wind_api_calls={result['wind_api_calls']}
>
> ⚠️ 本回测使用仿真数据, 非真实行情。
"""
    return md


def save_backtest_result(result: Dict[str, Any],
                          output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    保存回测结果 — P61 标准化输出。

    生成 5 类文件 + 自动归档:
      1. Markdown 摘要 (.md)
      2. JSON 结果 (.json)
      3. 指标表格 CSV (backtest_metrics_*.csv)
      4. 时序净值 CSV (net_value_series_*.csv)
      5. 快照 JSON (backtest_snapshot_*.json)
      6. 自动归档 → artifacts/backtest_archive/{timestamp}/

    Returns:
        {
            "md": path,
            "json": path,
            "metrics_csv": path,
            "net_value_csv": path,
            "snapshot_json": path,
            "archive_dir": path
        }
    """
    if output_dir is None:
        output_dir = BACKTEST_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    factor_type = result.get("summary", {}).get("factor_type", "unknown")
    symbol = result.get("summary", {}).get("symbol", "UNKNOWN")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── 1. Markdown 摘要 ──
    md_content = generate_summary_md(result)
    md_path = os.path.join(output_dir, f"backtest_{factor_type}_{symbol}_{timestamp}.md")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # ── 2. JSON 结果 ──
    json_path = os.path.join(output_dir, f"backtest_{factor_type}_{symbol}_{timestamp}.json")

    # 写入 JSON (移除过长的 equity_curve 以减小文件)
    json_out = dict(result)
    if "equity_curve" in json_out:
        json_out["equity_curve_preview"] = json_out["equity_curve"][:5]
        json_out["equity_curve_length"] = len(json_out["equity_curve"])
        del json_out["equity_curve"]
    if "return_curve" in json_out:
        json_out["return_curve_preview"] = json_out["return_curve"][:5]
        json_out["return_curve_length"] = len(json_out["return_curve"])
        del json_out["return_curve"]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_out, f, ensure_ascii=False, indent=2)

    # ── 3. 指标表格 CSV ──
    metrics_csv_path = ""
    if result.get("status") == BACKTEST_STATUS_OK:
        metrics_csv_path = save_backtest_metrics_csv(result)

    # ── 4. 时序净值 CSV ──
    net_value_csv_path = ""
    if result.get("status") == BACKTEST_STATUS_OK:
        net_value_csv_path = save_net_value_series_csv(result)

    # ── 5. 快照 JSON ──
    snapshot_json_path = ""
    if result.get("status") == BACKTEST_STATUS_OK:
        snapshot_json_path = save_backtest_snapshot_json(result)

    # ── 6. 自动归档 ──
    archive_dir = ""
    if result.get("status") == BACKTEST_STATUS_OK:
        all_files = {
            "md": md_path,
            "json": json_path,
            "metrics_csv": metrics_csv_path,
            "net_value_csv": net_value_csv_path,
            "snapshot_json": snapshot_json_path,
        }
        archive_dir = archive_backtest_result(all_files, result)

        # 回填快照中的归档路径
        if snapshot_json_path and os.path.exists(snapshot_json_path):
            with open(snapshot_json_path, "r", encoding="utf-8") as f:
                snap = json.load(f)
            snap["archive_info"]["archive_dir"] = archive_dir
            snap["archive_info"]["archive_id"] = os.path.basename(archive_dir)
            with open(snapshot_json_path, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)

    return {
        "md": md_path,
        "json": json_path,
        "metrics_csv": metrics_csv_path,
        "net_value_csv": net_value_csv_path,
        "snapshot_json": snapshot_json_path,
        "archive_dir": archive_dir,
    }


# ════════════════════════════════════════════════════════════════
# 日志输出
# ════════════════════════════════════════════════════════════════

def _print_backtest_summary(result: Dict[str, Any]):
    """打印回测结果摘要"""
    print()
    print("─" * 60)
    print("📈 [P59] 回测结果摘要")
    print("─" * 60)
    print(f"  状态:         {result['status']}")

    if result["status"] == BACKTEST_STATUS_WAIT:
        print("  ⏳ WAIT — 等待输入数据")
        for n in result.get("notes", []):
            print(f"    • {n}")
    elif result["status"] == BACKTEST_STATUS_OK:
        s = result["summary"]
        print(f"  因子类型:     {s['factor_type']} ({s['factor_id']})")
        print(f"  品种:         {s['symbol']}")
        print(f"  数据源:       {s['data_source']}")
        print(f"  交易日数:     {s['trading_days']}")
        print(f"  因子点数:     {s['factor_points']}")
        print(f"  日期范围:     {s['start_date']} ~ {s['end_date']}")
        print()
        print(f"  累计收益率:   {s['total_return']:.4%}")
        print(f"  年化波动率:   {s['annual_volatility']:.4%}")
        print(f"  日均波动率:   {s['daily_volatility']:.6%}")
        print(f"  最大回撤:     {s['max_drawdown']:.4%}")
        print(f"  夏普比率:     {s['sharpe_ratio']:.4f}")
    else:
        print(f"  ⚠️ 状态: {result['status']}")

    print(f"  REAL_WIND_CALL: {result['real_wind_call']}")
    print(f"  wind_api_calls:  {result['wind_api_calls']}")
    print("─" * 60)


# ════════════════════════════════════════════════════════════════
# 命令行接口 (自测)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("🧪 DSHA-P59 · 极简回测框架骨架 — 仿真自测")
    print("=" * 70)
    print()

    # 引入数据加载和因子构造模块
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import factor_data_loader
    import factor_constructor

    # ── 测试1: 无输入 → WAIT 状态 ──
    print("▶ 测试1: 无输入 → WAIT 状态")
    wait_result = run_backtest()
    assert wait_result["status"] == BACKTEST_STATUS_WAIT, \
        f"预期 WAIT, 实际 {wait_result['status']}"
    print(f"  ✅ 测试1通过 (status={wait_result['status']})\n")

    # ── 测试2: 只有价格无因子 → WAIT 状态 ──
    print("▶ 测试2: 只有价格无因子 → WAIT 状态")
    test_data = factor_data_loader._generate_builtin_test_data()
    price_data = {
        "dates": test_data["dates"],
        "values": test_data["values"],
        "symbol": "ZN.SHF",
        "indicator": "close",
        "source": "SIMULATED (NOT REAL)",
        "status": "OK",
        "metadata": {"record_count": 10},
    }
    wait_result2 = run_backtest(factor_data=None, price_data=price_data)
    assert wait_result2["status"] == BACKTEST_STATUS_WAIT
    print(f"  ✅ 测试2通过 (status={wait_result2['status']})\n")

    # ── 测试3: 完整数据 → OK 状态 ──
    print("▶ 测试3: 完整数据 → OK 状态")

    # 先生成因子
    factor_result = factor_constructor.compute_factor_from_data(
        data={
            "dates": test_data["dates"],
            "values": test_data["values"],
            "symbol": "ZN.SHF",
            "indicator": "close",
            "source": "SIMULATED (NOT REAL)",
            "status": "OK",
        },
        factor_type="momentum",
        params={"window_days": 3, "factor_id": "TEST-MOM", "factor_name": "测试动量"},
    )
    assert factor_result["factor_count"] > 0, "因子应为非空"

    bt_result = run_backtest(
        factor_data=factor_result,
        price_data=price_data,
    )
    assert bt_result["status"] == BACKTEST_STATUS_OK, \
        f"预期 OK, 实际 {bt_result['status']}"
    _print_backtest_summary(bt_result)

    # 验证关键指标存在
    summary = bt_result["summary"]
    assert "total_return" in summary
    assert "annual_volatility" in summary
    assert "max_drawdown" in summary
    assert "sharpe_ratio" in summary
    print(f"  ✅ 测试3通过 (total_return={summary['total_return']:.4%})\n")

    # ── 测试4: 保存回测结果 ──
    print("▶ 测试4: 保存回测结果 (MD + JSON)")
    saved = save_backtest_result(bt_result)
    assert os.path.exists(saved["md"]), f"MD不存在: {saved['md']}"
    assert os.path.exists(saved["json"]), f"JSON不存在: {saved['json']}"
    print(f"  ✅ MD: {saved['md']}")
    print(f"  ✅ JSON: {saved['json']}\n")

    # ── 测试5: 波动率因子回测 ──
    print("▶ 测试5: 波动率因子回测")
    vol_factor = factor_constructor.compute_factor_from_data(
        data={
            "dates": test_data["dates"],
            "values": test_data["values"],
            "symbol": "ZN.SHF",
            "indicator": "close",
            "source": "SIMULATED (NOT REAL)",
            "status": "OK",
        },
        factor_type="volatility",
        params={"window_days": 5, "factor_id": "TEST-VOL", "factor_name": "测试波动率"},
    )
    bt_vol = run_backtest(factor_data=vol_factor, price_data=price_data)
    assert bt_vol["status"] == BACKTEST_STATUS_OK
    _print_backtest_summary(bt_vol)
    print(f"  ✅ 测试5通过\n")

    # ── 测试6: WAIT 状态 Markdown 输出 ──
    print("▶ 测试6: WAIT 状态 Markdown 输出")
    wait_md = generate_summary_md(wait_result)
    assert "WAIT" in wait_md
    assert "等待输入数据" in wait_md
    print(f"  ✅ 测试6通过 (MD 包含 WAIT 标识)\n")

    # ── 测试7: P61 标准化指标 CSV ──
    print("▶ 测试7: P61 标准化指标 CSV")
    metrics_csv = save_backtest_metrics_csv(bt_result)
    assert os.path.exists(metrics_csv), f"指标CSV不存在: {metrics_csv}"
    with open(metrics_csv, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
    assert len(lines) >= 5, f"指标CSV行数不足: {len(lines)}"
    assert "metric_name" in lines[0], "CSV表头缺失"
    assert "total_return" in "".join(lines), "缺少 total_return 指标"
    assert "annual_volatility" in "".join(lines), "缺少 annual_volatility 指标"
    assert "max_drawdown" in "".join(lines), "缺少 max_drawdown 指标"
    assert "sharpe_ratio" in "".join(lines), "缺少 sharpe_ratio 指标"
    assert "information_coefficient" in "".join(lines), "缺少 IC 指标"
    print(f"  ✅ 指标CSV: {os.path.basename(metrics_csv)} ({len(lines)} 行)\n")

    # ── 测试8: P61 时序净值 CSV ──
    print("▶ 测试8: P61 时序净值 CSV")
    nv_csv = save_net_value_series_csv(bt_result)
    assert os.path.exists(nv_csv), f"净值CSV不存在: {nv_csv}"
    with open(nv_csv, "r", encoding="utf-8-sig") as f:
        nv_lines = f.readlines()
    assert len(nv_lines) >= 2, f"净值CSV行数不足"
    assert "date" in nv_lines[0], "CSV表头缺失 date"
    assert "net_value" in nv_lines[0], "CSV表头缺失 net_value"
    print(f"  ✅ 净值CSV: {os.path.basename(nv_csv)} ({len(nv_lines)} 行)\n")

    # ── 测试9: P61 快照 JSON ──
    print("▶ 测试9: P61 快照 JSON")
    snap_json = save_backtest_snapshot_json(bt_result)
    assert os.path.exists(snap_json), f"快照JSON不存在: {snap_json}"
    with open(snap_json, "r", encoding="utf-8") as f:
        snap_data = json.load(f)
    assert "snapshot_id" in snap_data, "缺少 snapshot_id"
    assert "metrics" in snap_data, "缺少 metrics"
    assert "factor_stats" in snap_data, "缺少 factor_stats"
    assert "safety" in snap_data, "缺少 safety"
    assert snap_data["safety"]["real_wind_call"] is False, "REAL_WIND_CALL 必须为 False"
    print(f"  ✅ 快照JSON: {os.path.basename(snap_json)} (snapshot_id={snap_data['snapshot_id']})\n")

    # ── 测试10: P61 完整保存 (含归档) ──
    print("▶ 测试10: P61 完整保存 (5类文件 + 自动归档)")
    saved = save_backtest_result(bt_result)
    assert os.path.exists(saved["md"]), "MD不存在"
    assert os.path.exists(saved["json"]), "JSON不存在"
    assert os.path.exists(saved["metrics_csv"]), "指标CSV不存在"
    assert os.path.exists(saved["net_value_csv"]), "净值CSV不存在"
    assert os.path.exists(saved["snapshot_json"]), "快照JSON不存在"
    assert saved["archive_dir"], "归档目录缺失"
    assert os.path.isdir(saved["archive_dir"]), f"归档目录不存在: {saved['archive_dir']}"
    manifest_path = os.path.join(saved["archive_dir"], "MANIFEST.json")
    assert os.path.exists(manifest_path), "归档清单不存在"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert len(manifest["files"]) >= 5, f"归档文件数不足: {len(manifest['files'])}"
    print(f"  ✅ 5类文件全部生成")
    print(f"  ✅ 归档目录: {saved['archive_dir']}")
    print(f"  ✅ 归档清单: {len(manifest['files'])} 个文件\n")

    # ── 测试11: IC 计算验证 ──
    print("▶ 测试11: IC 计算验证")
    # 使用波动率因子结果验证 IC
    ic_val, ic_ir, ic_n = _compute_ic_from_result(bt_vol)
    print(f"  波动率因子 IC={ic_val}, IC_IR={ic_ir}, n={ic_n}")
    # 验证 IC 在 [-1, 1] 范围
    assert -1.0 <= ic_val <= 1.0, f"IC 值超范围: {ic_val}"
    assert ic_n >= 0, "IC 样本数不应为负"
    print(f"  ✅ IC计算通过\n")

    # ── 测试12: 年化收益率验证 ──
    print("▶ 测试12: 年化收益率验证")
    ann_ret = _annualized_return(bt_result)
    assert isinstance(ann_ret, float), "年化收益率应为浮点数"
    print(f"  年化收益率: {ann_ret:.6f}")
    print(f"  ✅ 年化收益率计算通过\n")

    print("=" * 70)
    print("✅ 全部12项测试通过 — REAL_WIND_CALL=False, wind_api_calls=0")
    print("✅ P61 标准化输出: 指标CSV + 净值CSV + 快照JSON + 自动归档")
    print("=" * 70)
    sys.exit(0)
