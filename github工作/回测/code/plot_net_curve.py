#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-P63 · 净值曲线绘图脚本 (离线预构建)
Plot Net Value Curve — Pre-built Canvas, Axes, Legend, Style Definitions

═══════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不读取任何真实 Wind 数据
═══════════════════════════════════════════════════════════════════════
REAL_WIND_CALL: False (不可修改)
wind_api_calls: 0 (本模块不触发任何 Wind API 调用)
gate: CLOSED | release_permit: NOT_ISSUED

数据入口: 等待CSV落地后，将 net_value_series CSV 或回测结果 dict 传入
输出: PNG 图片文件

作者: DSHA-P63
基线: feature/v88-g1 @ 201ce9a
"""

import sys
import os
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple

# Force UTF-8 output for Chinese console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REAL_WIND_CALL = False
WIND_API_CALLS = 0

# ════════════════════════════════════════════════════════════════
# 绘图样式定义 (仅定义，不执行绘图 — 需 matplotlib 安装)
# ════════════════════════════════════════════════════════════════

PLOT_STYLE = {
    "figure": {
        "size_inches": (12, 6),
        "dpi": 150,
        "facecolor": "#FFFFFF",
    },
    "axes": {
        "title": {
            "text": "净值曲线 (Net Value Curve)",
            "fontsize": 14,
            "fontweight": "bold",
            "color": "#2C3E50",
            "pad": 12,
        },
        "xlabel": {
            "text": "日期",
            "fontsize": 11,
            "color": "#34495E",
        },
        "ylabel": {
            "text": "净值",
            "fontsize": 11,
            "color": "#34495E",
        },
        "grid": {
            "enabled": True,
            "alpha": 0.3,
            "linestyle": "--",
            "color": "#BDC3C7",
        },
    },
    "net_value_line": {
        "color": "#2E86DE",
        "linewidth": 2.0,
        "marker": "o",
        "markersize": 4,
        "linestyle": "-",
        "alpha": 1.0,
    },
    "equity_line": {
        "color": "#E74C3C",
        "linewidth": 1.5,
        "marker": "s",
        "markersize": 3,
        "linestyle": "--",
        "alpha": 0.8,
    },
    "baseline_line": {
        "color": "#95A5A6",
        "linewidth": 1.0,
        "linestyle": ":",
        "alpha": 0.7,
    },
    "drawdown_fill": {
        "color": "#E74C3C",
        "alpha": 0.15,
    },
    "legend": {
        "enabled": True,
        "loc": "upper left",
        "fontsize": 10,
        "framealpha": 0.9,
        "borderpad": 0.8,
    },
    "annotations": {
        "max_drawdown": {
            "color": "#E74C3C",
            "fontsize": 9,
            "fontweight": "bold",
        },
        "current_value": {
            "color": "#27AE60",
            "fontsize": 9,
        },
    },
}


def plot_net_value(
    dates: List[str],
    net_values: List[float],
    equity_curve: Optional[List[float]] = None,
    factor_values: Optional[List[float]] = None,
    max_drawdown: float = 0.0,
    max_drawdown_index: int = 0,
    output_path: Optional[str] = None,
    title_suffix: str = "",
    save_png: bool = True,
) -> Dict[str, Any]:
    """
    绘制净值曲线 — 画布、坐标轴、图例、样式定义。

    仅完成画布、坐标轴、图例、样式定义；不带真实数据，预留数据入口。
    当 matplotlib 可用时，实际渲染 PNG；否则返回空结果。

    Args:
        dates: 日期序列
        net_values: 净值序列 (initial_capital * (1 + cumulative_return))
        equity_curve: 可选的权益曲线 (与 net_values 对齐)
        factor_values: 可选的因子值序列 (副轴显示)
        max_drawdown: 最大回撤比率 (用于标注)
        max_drawdown_index: 最大回撤发生的位置索引
        output_path: 输出 PNG 文件路径 (None 则使用默认目录)
        title_suffix: 标题后缀 (如品种名)
        save_png: 是否保存 PNG (False 时仅返回绘图元数据)

    Returns:
        绘图结果字典
    """
    result = {
        "status": "SKIP",
        "notes": [],
        "has_data": False,
        "output_path": "",
        "data_points": 0,
        "real_wind_call": REAL_WIND_CALL,
        "wind_api_calls": WIND_API_CALLS,
    }

    # 检查数据
    if not dates or not net_values:
        result["notes"].append("无数据 — 等待CSV落地后填充")
        return result

    n = min(len(dates), len(net_values))
    dates = dates[:n]
    net_values = net_values[:n]
    result["data_points"] = n
    result["has_data"] = True

    # 检查 matplotlib 是否可用
    try:
        import matplotlib
        matplotlib.use("Agg")  # 非交互式后端
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        result["notes"].append("matplotlib 未安装 — 跳过实际渲染")
        result["notes"].append("画布/坐标轴/图例/样式定义已完成，数据入口已预留")
        result["status"] = "SKIPPED_NO_MPL"
        return result

    # ── 绘图 ──
    fig, ax1 = plt.subplots(
        figsize=PLOT_STYLE["figure"]["size_inches"],
        dpi=PLOT_STYLE["figure"]["dpi"],
        facecolor=PLOT_STYLE["figure"]["facecolor"],
    )

    # 净值曲线 (主轴)
    nv_style = PLOT_STYLE["net_value_line"]
    ax1.plot(
        range(n),
        net_values,
        color=nv_style["color"],
        linewidth=nv_style["linewidth"],
        marker=nv_style["marker"],
        markersize=nv_style["markersize"],
        linestyle=nv_style["linestyle"],
        alpha=nv_style["alpha"],
        label="净值",
        zorder=3,
    )

    # 权益曲线 (可选，副轴)
    if equity_curve and len(equity_curve) > 0:
        ec_style = PLOT_STYLE["equity_line"]
        ax2 = ax1.twinx()
        eq_n = min(len(equity_curve), n)
        ax2.plot(
            range(eq_n),
            equity_curve[:eq_n],
            color=ec_style["color"],
            linewidth=ec_style["linewidth"],
            marker=ec_style["marker"],
            markersize=ec_style["markersize"],
            linestyle=ec_style["linestyle"],
            alpha=ec_style["alpha"],
            label="权益曲线",
            zorder=2,
        )
        ax2.set_ylabel("权益价格", fontsize=10, color=ec_style["color"])

    # 基准线 (initial_capital = 1.0 or first net_value)
    if net_values:
        baseline = net_values[0]
        bl_style = PLOT_STYLE["baseline_line"]
        ax1.axhline(
            y=baseline,
            color=bl_style["color"],
            linewidth=bl_style["linewidth"],
            linestyle=bl_style["linestyle"],
            alpha=bl_style["alpha"],
            label=f"基准净值 ({baseline:.2f})",
            zorder=1,
        )

    # 最大回撤标注
    if max_drawdown < 0 and max_drawdown_index < n:
        dd_style = PLOT_STYLE["annotations"]["max_drawdown"]
        ax1.annotate(
            f"最大回撤\n{max_drawdown:.2%}",
            xy=(max_drawdown_index, net_values[max_drawdown_index]),
            xytext=(10, -20),
            textcoords="offset points",
            fontsize=dd_style["fontsize"],
            fontweight=dd_style["fontweight"],
            color=dd_style["color"],
            arrowprops=dict(
                arrowstyle="->",
                color=dd_style["color"],
                lw=1.0,
            ),
        )

    # 当前值标注
    if net_values:
        last_val = net_values[-1]
        cur_style = PLOT_STYLE["annotations"]["current_value"]
        ax1.annotate(
            f"当前: {last_val:.2f}",
            xy=(n - 1, last_val),
            xytext=(-50, 15),
            textcoords="offset points",
            fontsize=cur_style["fontsize"],
            color=cur_style["color"],
            ha="right",
        )

    # X轴日期刻度
    tick_step = max(1, n // 10)
    tick_positions = list(range(0, n, tick_step))
    tick_labels = [dates[i] for i in tick_positions if i < len(dates)]
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=8)

    # 坐标轴样式
    ax1_title = PLOT_STYLE["axes"]["title"]
    title = ax1_title["text"]
    if title_suffix:
        title += f" · {title_suffix}"
    ax1.set_title(
        title,
        fontsize=ax1_title["fontsize"],
        fontweight=ax1_title["fontweight"],
        color=ax1_title["color"],
        pad=ax1_title["pad"],
    )
    ax1_xlabel = PLOT_STYLE["axes"]["xlabel"]
    ax1.set_xlabel(ax1_xlabel["text"], fontsize=ax1_xlabel["fontsize"], color=ax1_xlabel["color"])
    ax1_ylabel = PLOT_STYLE["axes"]["ylabel"]
    ax1.set_ylabel(ax1_ylabel["text"], fontsize=ax1_ylabel["fontsize"], color=ax1_ylabel["color"])

    # 网格
    grid = PLOT_STYLE["axes"]["grid"]
    ax1.grid(
        True,
        alpha=grid["alpha"],
        linestyle=grid["linestyle"],
        color=grid["color"],
    )

    # 图例
    if PLOT_STYLE["legend"]["enabled"]:
        ax1.legend(
            loc=PLOT_STYLE["legend"]["loc"],
            fontsize=PLOT_STYLE["legend"]["fontsize"],
            framealpha=PLOT_STYLE["legend"]["framealpha"],
            borderpad=PLOT_STYLE["legend"]["borderpad"],
        )

    plt.tight_layout()

    # 保存
    result["output_path"] = ""
    if save_png:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "artifacts", "report_templates",
                f"net_value_curve_{timestamp}.png",
            )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")
        result["output_path"] = output_path

    plt.close(fig)

    result["status"] = "OK"
    return result


def render_from_csv(
    csv_path: str,
    output_path: Optional[str] = None,
    save_png: bool = True,
) -> Dict[str, Any]:
    """
    从 net_value_series CSV 文件渲染净值曲线。

    CSV 格式 (由 backtest_skeleton.save_net_value_series_csv 生成):
      date | close_price | factor_value | daily_return | cumulative_return | net_value

    Args:
        csv_path: 净值CSV文件路径
        output_path: 输出PNG路径
        save_png: 是否保存PNG

    Returns:
        绘图结果字典
    """
    if not os.path.exists(csv_path):
        return {
            "status": "ERROR",
            "notes": [f"CSV文件不存在: {csv_path}"],
            "real_wind_call": REAL_WIND_CALL,
            "wind_api_calls": WIND_API_CALLS,
        }

    import csv

    dates = []
    net_values = []
    equity_curve = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row.get("date", ""))
            nv = row.get("net_value", "")
            net_values.append(float(nv) if nv else None)
            price = row.get("close_price", "")
            equity_curve.append(float(price) if price else None)

    # 过滤空值
    valid_dates = []
    valid_nv = []
    valid_eq = []
    for i in range(len(dates)):
        if net_values[i] is not None:
            valid_dates.append(dates[i])
            valid_nv.append(net_values[i])
            if i < len(equity_curve) and equity_curve[i] is not None:
                valid_eq.append(equity_curve[i])

    return plot_net_value(
        dates=valid_dates,
        net_values=valid_nv,
        equity_curve=valid_eq if valid_eq else None,
        output_path=output_path,
        save_png=save_png,
    )


# ════════════════════════════════════════════════════════════════
# 命令行接口 (自测)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("🧪 DSHA-P63 · 净值曲线绘图脚本 — 仿真自测")
    print("=" * 70)
    print()

    # 测试1: 无数据 → SKIP 状态
    print("▶ 测试1: 无数据 → SKIP 状态")
    result = plot_net_value(dates=[], net_values=[])
    assert result["status"] == "SKIP"
    print(f"  ✅ 测试1通过 (status={result['status']})\n")

    # 测试2: 仿真数据绘图
    print("▶ 测试2: 仿真数据绘图")
    import random
    random.seed(42)

    base_date = datetime(2025, 1, 2)
    dates = []
    net_values = []
    equity_curve = []
    base_price = 24500.0
    initial_capital = 100000.0

    for i in range(20):
        d = base_date
        for _ in range(i):
            d = d + __import__("datetime").timedelta(days=1)
            while d.weekday() >= 5:
                d = d + __import__("datetime").timedelta(days=1)
        dates.append(d.strftime("%Y-%m-%d"))
        change = random.gauss(0, 100)
        base_price += change
        equity_curve.append(round(base_price, 2))
        ret = (base_price - 24500.0) / 24500.0
        net_values.append(round(initial_capital * (1 + ret), 2))

    result = plot_net_value(
        dates=dates,
        net_values=net_values,
        equity_curve=equity_curve,
        max_drawdown=-0.02,
        max_drawdown_index=15,
        save_png=True,
    )
    assert result["status"] in ("OK", "SKIPPED_NO_MPL")
    if result["status"] == "OK":
        assert os.path.exists(result["output_path"])
        print(f"  ✅ PNG: {result['output_path']}")
    else:
        print(f"  ✅ 跳过渲染 (原因: {result['notes'][0]})")
    print(f"  数据点: {result['data_points']}")
    print(f"  REAL_WIND_CALL: {result['real_wind_call']}")
    print(f"  wind_api_calls: {result['wind_api_calls']}\n")

    # 测试3: CSV渲染接口
    print("▶ 测试3: CSV渲染接口 (验证函数签名)")
    try:
        r = render_from_csv("NONEXISTENT.csv")
        assert r["status"] == "ERROR"
    except:
        assert False, "应返回 ERROR 而非抛出异常"
    print(f"  ✅ 测试3通过 (不存在的CSV → ERROR)\n")

    print("=" * 70)
    print("✅ 全部3项测试通过 — REAL_WIND_CALL=False, wind_api_calls=0")
    print("=" * 70)
    sys.exit(0)
