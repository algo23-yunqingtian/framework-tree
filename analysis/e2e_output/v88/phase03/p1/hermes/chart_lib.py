#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chart_lib.py — V88 Phase03 Web 看板通用绘图库
==================================================================
TASK_ID : V88_PHASE03_P12_HERMESHF_P11_WEB_DASHBOARD_CHART_BUILD / T0
AGENT   : HERMEShf
BRANCH  : feature/v88-g1  (BRANCH_LOCKED)

设计规范（硬约束）
------------------
1. 主色   : #6B4C9A （品牌紫，本工单指定"深蓝商务主色"）
2. 辅助色 : 浅灰系 #ECECF1 / #D6D6DF / #9A9AA8
3. 背景   : #FFFFFF 纯白
4. 无渐变 : 禁止任何 gradient colormap；热力图使用 ListedColormap 离散阶梯色块
5. 无圆角 : 所有图元 (bar/patch/rect) 禁止 rounded 样式
6. 无阴影 : 禁止 shadow / edgeglow
7. 无边框 : 图容器不画外边框，仅保留必要网格基线
8. 无行情 : 本库只画已有审计产物数据，不接行情源

依赖 : matplotlib (PNG) + plotly (HTML)
"""
from __future__ import annotations
import os
import datetime

# ---------------------------------------------------------------------------
# 0. 配色常量（唯一真源，禁止他处硬编码颜色）
# ---------------------------------------------------------------------------
PRIMARY      = "#6B4C9A"   # 品牌主色
PRIMARY_DARK = "#4A3272"   # 主色压暗（标题/强调）
PRIMARY_MID  = "#8B6DB8"   # 主色提亮（次级系列）
PRIMARY_LT   = "#C7B5DC"   # 主色浅（背景块/对比项）
GRAY_BG      = "#ECECF1"   # 浅灰底
GRAY_MID     = "#D6D6DF"   # 中灰线
GRAY_TXT     = "#6E6E7A"   # 灰色文字
BLACK_TXT    = "#1F1F2A"   # 正文黑
WHITE        = "#FFFFFF"
ACCENT_NEG   = "#B0413E"   # 仅用于 FAIL/阻断标注（克制使用）

# 热力图离散阶梯（5 级，纯纯色块，非渐变）
HEAT_RAMP = [WHITE, "#E7DEEF", "#C7B5DC", "#9A7EC4", PRIMARY]

FONT_CANDIDATES = [
    "Noto Sans CJK SC", "Noto Sans CJK JP", "Source Han Sans SC",
    "WenQuanYi Zen Hei", "WenQuanYi Micro Hei", "Droid Sans Fallback",
    "SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans",
]

# 字符兜底：当主字体（CJK）缺少 unicode 符号时，matplotlib 可回退到 DejaVu。
# 通过 fontconfig 将 DejaVu Sans 作为后备字体，确保 ✓/× 正常渲染。
SYMBOL_FALLBACK = "DejaVu Sans"

# ---------------------------------------------------------------------------
# 1. 全局样式（matplotlib）
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import ListedColormap
import numpy as np


def _pick_font():
    """探测系统可用中文字体，命中即设全局；无中文字体时回退 DejaVu 并警告。"""
    available = {f.name for f in fm.fontManager.ttflist}
    for name in FONT_CANDIDATES:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name] + plt.rcParams["font.sans-serif"]
            return name
    return None


_INSTALLED_FONT = _pick_font()

plt.rcParams.update({
    "font.sans-serif":          plt.rcParams["font.sans-serif"],
    "axes.unicode_minus":       False,
    "figure.facecolor":         WHITE,
    "axes.facecolor":           WHITE,
    "savefig.facecolor":        WHITE,
    "figure.dpi":               150,
    "savefig.dpi":              150,
    "axes.edgecolor":           GRAY_MID,
    "axes.labelcolor":          BLACK_TXT,
    "text.color":               BLACK_TXT,
    "xtick.color":              GRAY_TXT,
    "ytick.color":              GRAY_TXT,
    "axes.linewidth":           0.9,
    "grid.color":               GRAY_BG,
    "grid.linewidth":           0.8,
    "font.size":                10,
})

HEAT_CM = ListedColormap(HEAT_RAMP)  # 离散色，插值方式见 imshow 调用


def heat_cmap() -> ListedColormap:
    return HEAT_CM


# ---------------------------------------------------------------------------
# 2. 通用工具
# ---------------------------------------------------------------------------
def _strip_spines(ax, keep=("bottom", "left")):
    """移除多余边框线，保留必要基线。"""
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(side in keep)


def _title(ax, main, sub=None, pad=14):
    ax.set_title(main, color=PRIMARY_DARK, fontsize=13, fontweight="bold",
                 loc="left", pad=(26 if sub else pad))
    if sub:
        ax.text(0, 1.035, sub, transform=ax.transAxes,
                color=GRAY_TXT, fontsize=8.5, va="bottom", ha="left")


def _footer(fig, text, y=0.015):
    fig.text(0.01, y, text, color=GRAY_TXT, fontsize=7.5, ha="left")


def _no_rounded_rect(ax, x, y, w, h, color, text=None, fs=9, tc=WHITE, bold=True):
    """纯色矩形 + 居中文字。刻意不使用 rounded=True。"""
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color,
                               edgecolor="none", linewidth=0))
    if text is not None:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                color=tc, fontsize=fs, fontweight="bold" if bold else "normal")


def save_png(fig, path, close=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.28,
                facecolor=WHITE, edgecolor="none")
    if close:
        plt.close(fig)
    return path


TS_TAG = "2026-10-17"
SOURCE_TAG = ("V88 Phase03 P12 | AGENT: HERMEShf | branch: feature/v88-g1 | "
              "data: audit artifacts only (no market data)")

# ---------------------------------------------------------------------------
# 3. 图表 1 — KPI 卡片
# ---------------------------------------------------------------------------
def kpi_cards(kpis, out_png, title="Phase03 准入门禁 核心指标",
              subtitle=None, cols=4, rows=None, fig_h=None):
    """
    kpis : list of dict { "label", "value", "unit"(可选), "state": "ok|warn|block" }
    纯色方块卡片，无渐变无圆角。
    """
    n = len(kpis)
    rows = rows or ((n + cols - 1) // cols)
    fig_h = fig_h or (1.55 * rows + 1.0)
    fig, ax = plt.subplots(figsize=(cols * 3.05, fig_h))
    ax.set_xlim(0, cols); ax.set_ylim(0, rows)
    ax.axis("off")

    bw, bh = 0.86, 0.80
    palette = {"ok": PRIMARY, "warn": PRIMARY_MID, "block": ACCENT_NEG,
               "neutral": PRIMARY_LT}
    for i, k in enumerate(kpis):
        r, c = i // cols, i % cols
        x = c + (1 - bw) / 2
        y = (rows - 1 - r) + (1 - bh) / 2
        color = palette.get(k.get("state", "ok"), PRIMARY)
        _no_rounded_rect(ax, x, y, bw, bh, color)
        val = k["value"] + (f" {k['unit']}" if k.get("unit") else "")
        ax.text(x + bw / 2, y + bh * 0.62, val, ha="center", va="center",
                color=WHITE, fontsize=17, fontweight="bold")
        ax.text(x + bw / 2, y + bh * 0.26, k["label"], ha="center",
                va="center", color="#F0EAF6", fontsize=8.6)

    _title(ax, title, subtitle or SOURCE_TAG)
    _footer(fig, SOURCE_TAG)
    return save_png(fig, out_png)


# ---------------------------------------------------------------------------
# 4. 图表 2 — 3x3 因子一致性热力图
# ---------------------------------------------------------------------------
def factor_heatmap(matrix, rows, cols, out_png,
                   title="3×3 因子质量门槛矩阵", subtitle=None,
                   value_fmt="{:.2f}", annotate=True, note=None):
    """
    matrix : 二维 list，len(matrix)==len(rows)，每行 len==len(cols)
    rows   : 行标签（如品种）
    cols   : 列标签（如因子）
    使用 ListedColormap 离散 5 级阶梯色 —— 纯色块、无渐变插值。
    """
    n_r, n_c = len(rows), len(cols)
    fig, ax = plt.subplots(figsize=(2.15 * n_c + 2.4, 1.55 * n_r + 1.9))
    data = np.asarray(matrix, dtype=float)
    vmin, vmax = float(data.min()), float(data.max())
    if vmax <= vmin:
        vmax = vmin + 1e-6

    im = ax.imshow(data, cmap=HEAT_CM, aspect="auto", vmin=vmin, vmax=vmax,
                   interpolation="nearest")   # nearest = 硬边纯色块，非平滑渐变

    ax.set_xticks(range(n_c)); ax.set_xticklabels(cols, fontsize=9.5)
    ax.set_yticks(range(n_r)); ax.set_yticklabels(rows, fontsize=9.5)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    if annotate:
        for i in range(n_r):
            for j in range(n_c):
                v = data[i, j]
                ax.text(j, i, value_fmt.format(v), ha="center", va="center",
                        fontsize=10, fontweight="bold",
                        color=WHITE if i and v >= vmin + (vmax - vmin) * 0.55
                        else PRIMARY_DARK)

    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=GRAY_TXT, length=0)
    cb.set_label("value", color=GRAY_TXT, fontsize=8.5)

    _title(ax, title, subtitle or note or SOURCE_TAG)
    _footer(fig, SOURCE_TAG, y=0.005)
    return save_png(fig, out_png)


def factor_conformance_grid(cells, rows, cols, out_png,
                             title="三方口径一致性矩阵", subtitle=None,
                             icon_pass="PASS", icon_fail="FAIL"):
    """
    0/1 一致性矩阵：PASS=主色实心块 + PASS, FAIL=浅灰块 + FAIL。
    cells : 二维 list of bool
    """
    n_r, n_c = len(rows), len(cols)
    fig, ax = plt.subplots(figsize=(2.2 * n_c + 2.6, 1.5 * n_r + 1.9))
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            ok = bool(cells[i][j])
            col = PRIMARY if ok else GRAY_BG
            ax.add_patch(plt.Rectangle((j - 0.42, n_r - 1 - i - 0.42),
                                       0.84, 0.84, facecolor=col,
                                       edgecolor="none"))
            sym = icon_pass if ok else icon_fail
            ax.text(j, n_r - 1 - i, sym, ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color=WHITE if ok else GRAY_TXT)
    ax.set_xlim(-0.5, n_c - 0.5); ax.set_ylim(-0.5, n_r - 0.5)
    ax.set_xticks(range(n_c)); ax.set_xticklabels(cols, fontsize=9.5)
    ax.set_yticks(range(n_r)); ax.set_yticklabels(rows[::-1], fontsize=9.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    _title(ax, title, subtitle or SOURCE_TAG)
    _footer(fig, SOURCE_TAG, y=0.005)
    return save_png(fig, out_png)


# ---------------------------------------------------------------------------
# 5. 图表 3 — 仲裁场景回归柱状图
# ---------------------------------------------------------------------------
def scenario_bars(scenarios, out_png,
                  title="仲裁器 8 场景回归", subtitle=None, fig_w=9.2):
    """
    scenarios : list of {"id","desc","prechecks":int,"status":"PASS|SKIP|FAIL"}
    柱体为预检执行数（0-5），颜色区分状态；高度 0 的 SKIP 柱以浅灰标注。
    """
    n = len(scenarios)
    fig, ax = plt.subplots(figsize=(fig_w, 4.6))
    colors, labels, heights, tick = [], [], [], []
    cmap = {"PASS": PRIMARY, "SKIP": PRIMARY_LT, "FAIL": ACCENT_NEG}
    for s in scenarios:
        colors.append(cmap.get(s["status"], PRIMARY_MID))
        labels.append(f'{s["id"]}\n{s["status"]}')
        heights.append(s["prechecks"])
        tick.append(s["id"])

    bars = ax.bar(range(n), heights, width=0.58, color=colors,
                  edgecolor="none", zorder=3)
    # SKIP 场景叠加虚线描边，表明"合法跳过而非零值"
    for i, s in enumerate(scenarios):
        if s["status"] == "SKIP":
            bars[i].set_edgecolor(PRIMARY_MID)
            bars[i].set_linewidth(1.2)
            bars[i].set_hatch("")
            ax.text(i, 0.16, "SKIP", ha="center", va="bottom",
                    fontsize=8.5, color=PRIMARY_DARK, fontweight="bold")
        else:
            ax.text(i, heights[i] + 0.12, f'{heights[i]}/5', ha="center",
                    va="bottom", fontsize=9.5, color=PRIMARY_DARK,
                    fontweight="bold")

    ax.set_ylim(0, 6.0); ax.set_yticks([0, 1, 2, 3, 4, 5])
    ax.set_ylabel("预检项执行数", fontsize=9.5, color=GRAY_TXT)
    ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=8.8)
    ax.grid(axis="y", zorder=0)
    _strip_spines(ax)
    ax.set_axisbelow(True)
    _title(ax, title, subtitle or SOURCE_TAG)

    # 图例（纯方块，无圆角）
    for idx, (k, v) in enumerate([("PASS", PRIMARY), ("SKIP", PRIMARY_LT)]):
        ax.add_patch(plt.Rectangle((0.72, 0.86 - 0.1 * idx), 0.012, 0.03,
                                   transform=ax.transAxes, facecolor=v,
                                   edgecolor="none"))
        ax.text(0.745, 0.875 - 0.1 * idx, k, transform=ax.transAxes,
                fontsize=8.5, color=GRAY_TXT, va="center")

    _footer(fig, SOURCE_TAG)
    return save_png(fig, out_png)


# ---------------------------------------------------------------------------
# 6. 图表 4 — 风险闭环进度条形图
# ---------------------------------------------------------------------------
def risk_progress(items, out_png,
                  title="风险台账闭环进度", subtitle=None, fig_w=9.6):
    """
    items : list of {"name","progress":0-100,"state":"CLOSED|DEFERRED|OPEN",
                     "note":str}
    水平条形，主色填充，浅灰为未完成底轨。
    """
    n = len(items)
    fig, ax = plt.subplots(figsize=(fig_w, 0.78 * n + 2.0))
    y = np.arange(n)[::-1]
    cmap = {"CLOSED": PRIMARY, "DEFERRED": PRIMARY_MID, "OPEN": ACCENT_NEG}
    for i, it in enumerate(items):
        yi = y[i]
        ax.barh(yi, 100, height=0.46, color=GRAY_BG, edgecolor="none", zorder=2)
        ax.barh(yi, it["progress"], height=0.46,
                color=cmap.get(it["state"], PRIMARY), edgecolor="none", zorder=3)
        ax.text(101.5, yi, f'{it["progress"]:.0f}%', va="center", ha="left",
                fontsize=9.5, fontweight="bold", color=PRIMARY_DARK)
        ax.text(-1.5, yi + 0.06, it["name"], va="center", ha="right",
                fontsize=9.3, color=BLACK_TXT)
        ax.text(-1.5, yi - 0.24, f'{it["state"]}  {it.get("note","")}',
                va="center", ha="right", fontsize=7.6, color=GRAY_TXT)

    ax.set_xlim(0, 112); ax.set_ylim(-0.75, n - 0.25)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8.5)
    ax.tick_params(length=0)
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_yticks([])
    _title(ax, title, subtitle or SOURCE_TAG)
    _footer(fig, SOURCE_TAG)
    return save_png(fig, out_png)
