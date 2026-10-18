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
DSHA-P59 · 极简回测框架骨架
(Backtest Skeleton — OFFLINE ONLY, NO REAL WIND DATA)

═══════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不读取任何真实 Wind 数据
═══════════════════════════════════════════════════════════════════════
REAL_WIND_CALL: False (不可修改)
wind_api_calls: 0 (本模块不触发任何 Wind API 调用)
gate: CLOSED/HOLD | release_permit: NOT_ISSUED

数据流:
  factor_data_loader → factor_constructor → 本模块

前置校验:
  无输入原始数据时直接返回 WAIT 状态, 不报错崩溃。

输入:
  - 因子序列 (来自 factor_constructor)
  - 价格序列 (来自 factor_data_loader)

输出:
  - 回测摘要 Markdown + JSON
  - 目录: code/backtest_output/

作者: DSHA-P59
基线: feature/v88-g1
"""

import json
import os
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


# ════════════════════════════════════════════════════════════════
# 结果输出: Markdown + JSON
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
    保存回测结果 (Markdown + JSON) 到输出目录。

    Returns:
        {"md": path, "json": path}
    """
    if output_dir is None:
        output_dir = BACKTEST_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    factor_type = result.get("summary", {}).get("factor_type", "unknown")
    symbol = result.get("summary", {}).get("symbol", "UNKNOWN")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    md_content = generate_summary_md(result)
    md_path = os.path.join(output_dir, f"backtest_{factor_type}_{symbol}_{timestamp}.md")

    json_path = os.path.join(output_dir, f"backtest_{factor_type}_{symbol}_{timestamp}.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

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

    return {"md": md_path, "json": json_path}


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

    print("=" * 70)
    print("✅ 全部6项测试通过 — REAL_WIND_CALL=False, wind_api_calls=0")
    print("=" * 70)
    sys.exit(0)
