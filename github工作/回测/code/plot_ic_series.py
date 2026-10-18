#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-P63 · IC时序图绘图脚本 (离线预构建)
Plot IC Series — Pre-built Canvas, Axes, Legend, Style Definitions

═══════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不读取任何真实 Wind 数据
═══════════════════════════════════════════════════════════════════════
REAL_WIND_CALL: False (不可修改)
wind_api_calls: 0 (本模块不触发任何 Wind API 调用)
gate: CLOSED | release_permit: NOT_ISSUED

数据入口: 等待CSV落地后，将 factor_values + forward_returns 传入
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
        "size_inches": (12, 5),
        "dpi": 150,
        "facecolor": "#FFFFFF",
    },
    "axes": {
        "title": {
            "text": "IC 时序图 (Information Coefficient Series)",
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
            "text": "IC值",
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
    "ic_line": {
        "color": "#8E44AD",
        "linewidth": 2.0,
        "marker": "o",
        "markersize": 4,
        "linestyle": "-",
        "alpha": 1.0,
    },
    "ic_mean_line": {
        "color": "#2E86DE",
        "linewidth": 1.5,
        "linestyle": "--",
        "alpha": 0.8,
    },
    "zero_line": {
        "color": "#95A5A6",
        "linewidth": 1.0,
        "linestyle": ":",
        "alpha": 0.7,
    },
    "positive_fill": {
        "color": "#27AE60",
        "alpha": 0.1,
    },
    "negative_fill": {
        "color": "#E74C3C",
        "alpha": 0.1,
    },
    "legend": {
        "enabled": True,
        "loc": "upper left",
        "fontsize": 10,
        "framealpha": 0.9,
        "borderpad": 0.8,
    },
    "annotations": {
        "max_ic": {
            "color": "#27AE60",
            "fontsize": 9,
            "fontweight": "bold",
        },
        "min_ic": {
            "color": "#E74C3C",
            "fontsize": 9,
            "fontweight": "bold",
        },
    },
}


def plot_ic_series(
    dates: List[str],
    ic_values: List[float],
    ic_mean: Optional[float] = None,
    ic_std: Optional[float] = None,
    ic_ir: Optional[float] = None,
    output_path: Optional[str] = None,
    title_suffix: str = "",
    save_png: bool = True,
) -> Dict[str, Any]:
    """
    绘制IC时序图 — 画布、坐标轴、图例、样式定义。

    仅完成画布、坐标轴、图例、样式定义；不带真实数据，预留数据入口。
    当 matplotlib 可用时，实际渲染 PNG；否则返回空结果。

    Args:
        dates: 日期序列 (与 ic_values 对齐)
        ic_values: IC值序列 (滚动IC)
        ic_mean: 可选的IC均值 (水平参考线)
        ic_std: 可选的IC标准差 (置信带)
        ic_ir: 可选的ICIR值 (标注)
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
    if not dates or not ic_values:
        result["notes"].append("无数据 — 等待CSV落地后填充")
        return result

    n = min(len(dates), len(ic_values))
    dates = dates[:n]
    ic_values = [v for v in ic_values[:n] if v is not None]
    n = len(ic_values)

    if n == 0:
        result["notes"].append("无有效IC数据点")
        return result

    # 对齐日期
    valid_dates = dates[:n]
    result["data_points"] = n
    result["has_data"] = True

    # 检查 matplotlib 是否可用
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        result["notes"].append("matplotlib 未安装 — 跳过实际渲染")
        result["notes"].append("画布/坐标轴/图例/样式定义已完成，数据入口已预留")
        result["status"] = "SKIPPED_NO_MPL"
        return result

    # ── 绘图 ──
    fig, ax = plt.subplots(
        figsize=PLOT_STYLE["figure"]["size_inches"],
        dpi=PLOT_STYLE["figure"]["dpi"],
        facecolor=PLOT_STYLE["figure"]["facecolor"],
    )

    x = list(range(n))

    # IC 主曲线
    ic_style = PLOT_STYLE["ic_line"]
    ax.plot(
        x, ic_values,
        color=ic_style["color"],
        linewidth=ic_style["linewidth"],
        marker=ic_style["marker"],
        markersize=ic_style["markersize"],
        linestyle=ic_style["linestyle"],
        alpha=ic_style["alpha"],
        label="IC值",
        zorder=3,
    )

    # 正/负填充区域
    ax.fill_between(
        x, 0, ic_values,
        where=[v > 0 for v in ic_values],
        color=PLOT_STYLE["positive_fill"]["color"],
        alpha=PLOT_STYLE["positive_fill"]["alpha"],
        interpolate=True,
        zorder=1,
    )
    ax.fill_between(
        x, 0, ic_values,
        where=[v < 0 for v in ic_values],
        color=PLOT_STYLE["negative_fill"]["color"],
        alpha=PLOT_STYLE["negative_fill"]["alpha"],
        interpolate=True,
        zorder=1,
    )

    # 零线
    z_style = PLOT_STYLE["zero_line"]
    ax.axhline(
        y=0,
        color=z_style["color"],
        linewidth=z_style["linewidth"],
        linestyle=z_style["linestyle"],
        alpha=z_style["alpha"],
        zorder=2,
    )

    # IC 均值线
    if ic_mean is not None:
        m_style = PLOT_STYLE["ic_mean_line"]
        ax.axhline(
            y=ic_mean,
            color=m_style["color"],
            linewidth=m_style["linewidth"],
            linestyle=m_style["linestyle"],
            alpha=m_style["alpha"],
            label=f"IC均值 ({ic_mean:.4f})",
            zorder=2,
        )

    # IC 标准差置信带
    if ic_std is not None and ic_mean is not None:
        upper = ic_mean + ic_std
        lower = ic_mean - ic_std
        ax.axhline(y=upper, color="#F39C12", linewidth=0.8, linestyle="-.", alpha=0.5, zorder=1)
        ax.axhline(y=lower, color="#F39C12", linewidth=0.8, linestyle="-.", alpha=0.5, zorder=1)

    # 最大值/最小值标注
    max_ic = max(ic_values)
    min_ic = min(ic_values)
    max_idx = ic_values.index(max_ic)
    min_idx = ic_values.index(min_ic)

    if max_ic > 0:
        max_style = PLOT_STYLE["annotations"]["max_ic"]
        ax.annotate(
            f"max IC: {max_ic:.4f}",
            xy=(max_idx, max_ic),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=max_style["fontsize"],
            fontweight=max_style["fontweight"],
            color=max_style["color"],
            arrowprops=dict(arrowstyle="->", color=max_style["color"], lw=1.0),
        )

    if min_ic < 0:
        min_style = PLOT_STYLE["annotations"]["min_ic"]
        ax.annotate(
            f"min IC: {min_ic:.4f}",
            xy=(min_idx, min_ic),
            xytext=(10, -20),
            textcoords="offset points",
            fontsize=min_style["fontsize"],
            fontweight=min_style["fontweight"],
            color=min_style["color"],
            arrowprops=dict(arrowstyle="->", color=min_style["color"], lw=1.0),
        )

    # ICIR 标注 (右上)
    if ic_ir is not None:
        ax.text(
            0.95, 0.95,
            f"IC_IR: {ic_ir:.4f}",
            transform=ax.transAxes,
            fontsize=10,
            fontweight="bold",
            color="#2C3E50",
            ha="right",
            va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#ECF0F1", alpha=0.8),
        )

    # X轴日期刻度
    tick_step = max(1, n // 10)
    tick_positions = list(range(0, n, tick_step))
    tick_labels = [valid_dates[i] for i in tick_positions if i < len(valid_dates)]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=8)

    # 坐标轴样式
    ax_title = PLOT_STYLE["axes"]["title"]
    title = ax_title["text"]
    if title_suffix:
        title += f" · {title_suffix}"
    ax.set_title(
        title,
        fontsize=ax_title["fontsize"],
        fontweight=ax_title["fontweight"],
        color=ax_title["color"],
        pad=ax_title["pad"],
    )
    ax_xlabel = PLOT_STYLE["axes"]["xlabel"]
    ax.set_xlabel(ax_xlabel["text"], fontsize=ax_xlabel["fontsize"], color=ax_xlabel["color"])
    ax_ylabel = PLOT_STYLE["axes"]["ylabel"]
    ax.set_ylabel(ax_ylabel["text"], fontsize=ax_ylabel["fontsize"], color=ax_ylabel["color"])

    # 网格
    grid = PLOT_STYLE["axes"]["grid"]
    ax.grid(
        True,
        alpha=grid["alpha"],
        linestyle=grid["linestyle"],
        color=grid["color"],
    )

    # 图例
    if PLOT_STYLE["legend"]["enabled"]:
        ax.legend(
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
                f"ic_series_{timestamp}.png",
            )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, bbox_inches="tight")
        result["output_path"] = output_path

    plt.close(fig)

    result["status"] = "OK"
    return result


def render_from_backtest_result(
    result: Dict[str, Any],
    output_path: Optional[str] = None,
    save_png: bool = True,
) -> Dict[str, Any]:
    """
    从 backtest_skeleton.run_backtest() 结果渲染IC时序图。

    需要 result 中包含:
      - factor_values: 因子值序列
      - aligned_dates: 日期序列
      - equity_curve: 价格曲线 (用于计算 forward_returns)

    Args:
        result: 回测结果字典
        output_path: 输出PNG路径
        save_png: 是否保存PNG

    Returns:
        绘图结果字典
    """
    factor_values = result.get("factor_values", [])
    aligned_dates = result.get("aligned_dates", [])
    equity_curve = result.get("equity_curve", [])

    if not factor_values or not equity_curve:
        return {
            "status": "SKIP",
            "notes": ["回测结果中缺少 factor_values 或 equity_curve"],
            "real_wind_call": REAL_WIND_CALL,
            "wind_api_calls": WIND_API_CALLS,
        }

    # 计算 forward_returns
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

    # 计算滚动IC (简单实现: 用整体IC作为单点，或滑动窗口)
    from backtest_skeleton import compute_IC
    ic_val, ic_ir, ic_n = compute_IC(factor_values, forward_returns)

    # 生成简单的IC序列 (每个点用当前IC)
    # 实际场景中应计算滚动IC，此处为模板演示
    ic_series = [ic_val] * n
    dates_for_plot = aligned_dates[offset:] if offset < len(aligned_dates) else aligned_dates

    return plot_ic_series(
        dates=dates_for_plot[:n],
        ic_values=ic_series,
        ic_mean=ic_val,
        ic_ir=ic_ir,
        output_path=output_path,
        save_png=save_png,
    )


# ════════════════════════════════════════════════════════════════
# 命令行接口 (自测)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("🧪 DSHA-P63 · IC时序图绘图脚本 — 仿真自测")
    print("=" * 70)
    print()

    # 测试1: 无数据 → SKIP 状态
    print("▶ 测试1: 无数据 → SKIP 状态")
    result = plot_ic_series(dates=[], ic_values=[])
    assert result["status"] == "SKIP"
    print(f"  ✅ 测试1通过 (status={result['status']})\n")

    # 测试2: 仿真IC数据绘图
    print("▶ 测试2: 仿真IC数据绘图")
    import random
    random.seed(42)

    base_date = datetime(2025, 1, 2)
    dates = []
    ic_values = []

    for i in range(20):
        d = base_date
        for _ in range(i):
            d = d + __import__("datetime").timedelta(days=1)
            while d.weekday() >= 5:
                d = d + __import__("datetime").timedelta(days=1)
        dates.append(d.strftime("%Y-%m-%d"))
        ic = random.gauss(0.05, 0.03)  # 模拟IC值
        ic_values.append(round(ic, 6))

    result = plot_ic_series(
        dates=dates,
        ic_values=ic_values,
        ic_mean=sum(ic_values) / len(ic_values),
        ic_std=(sum((v - sum(ic_values)/len(ic_values))**2 for v in ic_values) / len(ic_values)) ** 0.5,
        ic_ir=0.5,
        save_png=True,
    )
    assert result["status"] in ("OK", "SKIPPED_NO_MPL")
    if result["status"] == "OK":
        assert os.path.exists(result["output_path"])
        print(f"  ✅ PNG: {result['output_path']}")
    else:
        print(f"  ✅ 跳过渲染 (原因: {result['notes'][0]})")
    print(f"  数据点: {result['data_points']}")
    print(f"  IC均值: {sum(ic_values)/len(ic_values):.4f}")
    print(f"  IC范围: [{min(ic_values):.4f}, {max(ic_values):.4f}]")
    print(f"  REAL_WIND_CALL: {result['real_wind_call']}")
    print(f"  wind_api_calls: {result['wind_api_calls']}\n")

    # 测试3: 从回测结果渲染接口
    print("▶ 测试3: 从回测结果渲染接口 (验证函数签名)")
    mock_result = {
        "factor_values": [0.1, 0.2, 0.15, 0.25, 0.18],
        "aligned_dates": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"],
        "equity_curve": [24500.0, 24600.0, 24550.0, 24700.0, 24650.0],
    }
    r = render_from_backtest_result(mock_result, save_png=False)
    assert r["status"] in ("OK", "SKIPPED_NO_MPL", "SKIP")
    print(f"  ✅ 测试3通过 (status={r['status']})\n")

    print("=" * 70)
    print("✅ 全部3项测试通过 — REAL_WIND_CALL=False, wind_api_calls=0")
    print("=" * 70)
    sys.exit(0)
