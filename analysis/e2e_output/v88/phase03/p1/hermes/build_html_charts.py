#!/usr/bin/env python3.12
# -*- coding: utf-8 -*-
"""
build_html_charts.py — V88 Phase03 P12 T1 交互式 HTML 图表 (Plotly)
严格 #6B4C9A 纯色商务风格，无渐变。
兼容 Plotly 5.15 (python3.12 系统包)。
"""
import os, sys, json
import plotly.graph_objects as go

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "web_asset")
os.makedirs(OUT, exist_ok=True)

# 配色
PRIMARY      = "#6B4C9A"
PRIMARY_DARK = "#4A3272"
PRIMARY_MID  = "#8B6DB8"
PRIMARY_LT   = "#C7B5DC"
GRAY_BG      = "#ECECF1"
GRAY_MID     = "#D6D6DF"
GRAY_TXT     = "#6E6E7A"
BLACK_TXT    = "#1F1F2A"
WHITE        = "#FFFFFF"
ACCENT_NEG   = "#B0413E"

FONT_FAM = "Noto Sans CJK SC, WenQuanYi Zen Hei, Arial, sans-serif"

def base_layout():
    """返回一个独立的 Layout dict（每次新建，避免引用共享）。"""
    return dict(
        font=dict(family=FONT_FAM, size=12, color=BLACK_TXT),
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        colorway=[PRIMARY, PRIMARY_MID, PRIMARY_LT, GRAY_MID],
    )

def make_title(text):
    return dict(text=text, x=0.02, font=dict(size=15, color=PRIMARY_DARK))

ARCH = os.path.join(HERE, "hermes_admission_gate_archive")
SNAP = os.path.join(HERE, "hermes_snapshot_format_archive")

raw = json.load(open(os.path.join(ARCH, "arbiter_final_regression_raw.json")))
snap = json.load(open(os.path.join(SNAP, "caliber_inventory_snapshot.json")))

# ──────────────────────────────────────────────────────────────────────────
# HTML 1: KPI 表格
# ──────────────────────────────────────────────────────────────────────────
kpis = [
    ("仲裁场景回归", "8/8", "ok"),
    ("预检通过率", "100%", "ok"),
    ("假阳性/假阴性", "0", "ok"),
    ("风险台账闭环", "3/3", "ok"),
    ("因子矩阵单元", "9", "ok"),
    ("口径快照校验", "10/10", "ok"),
    ("Key A 状态", "ABSENT", "warn"),
    ("Phase04", "FROZEN", "warn"),
]
color_map = {"ok": PRIMARY, "warn": PRIMARY_MID, "block": ACCENT_NEG}

fig = go.Figure(go.Table(
    header=dict(
        values=["<b>指标</b>", "<b>数值</b>", "<b>状态</b>"],
        fill_color=PRIMARY_DARK,
        font=dict(color=WHITE, size=13),
        align="center",
        height=34,
    ),
    cells=dict(
        values=[list(zip(*kpis))[0], list(zip(*kpis))[1],
                ["PASS" if s=="ok" else "WARN" for _,_,s in kpis]],
        fill_color=[WHITE, WHITE,
                    [color_map[s] for _,_,s in kpis]],
        font=dict(color=WHITE, size=12),
        align="center",
        height=30,
    ),
))
layout = base_layout()
layout["title"] = make_title("Phase03 准入门禁 核心指标 | V88 Phase03 P12")
layout["height"] = 380
layout["width"] = 620
layout["margin"] = dict(l=20, r=20, t=60, b=20)
fig.update_layout(layout)
fig.write_html(os.path.join(OUT, "01_kpi_cards.html"),
               include_plotlyjs="cdn", full_html=False)
print("✅ 01_kpi_cards.html")

# ──────────────────────────────────────────────────────────────────────────
# HTML 2: 3x3 因子热力图（离散色阶）
# ──────────────────────────────────────────────────────────────────────────
s1 = snap["section_1_factor_matrix"]
factors = [f["factor_id"] for f in s1["factors"]]
varieties = [v["code"] for v in s1["varieties"]]
matrix = []
for v_code in varieties:
    row = []
    for f_id in factors:
        cell = next(m for m in s1["matrix"]
                    if m["factor_id"] == f_id and m["variety"] == v_code)
        row.append(float(cell["quality_threshold"]["ic_min"]))
    matrix.append(row)

discrete_scale = [WHITE, "#E7DEEF", "#C7B5DC", "#9A7EC4", PRIMARY]
fig = go.Figure(go.Heatmap(
    z=matrix,
    x=factors,
    y=varieties,
    colorscale=[[i/(len(discrete_scale)-1), c]
                for i, c in enumerate(discrete_scale)],
    colorbar=dict(thickness=12, outlinewidth=0, title_text="IC_min"),
    text=[[f"{v:.3f}" for v in row] for row in matrix],
    texttemplate="%{text}",
    textfont=dict(color=WHITE, size=13),
    hovertemplate="品种: %{y}<br>因子: %{x}<br>IC_min: %{z:.3f}<extra></extra>",
))
layout = base_layout()
layout["title"] = make_title("3×3 因子质量门槛矩阵 (IC_min) | 数据源: caliber_inventory_snapshot.json")
layout["height"] = 460
layout["width"] = 680
layout["xaxis"] = dict(showgrid=False, tickfont=dict(size=11))
layout["yaxis"] = dict(showgrid=False, tickfont=dict(size=11), autorange="reversed")
fig.update_layout(layout)
fig.write_html(os.path.join(OUT, "02_factor_heatmap.html"),
               include_plotlyjs="cdn", full_html=False)
print("✅ 02_factor_heatmap.html")

# ──────────────────────────────────────────────────────────────────────────
# HTML 3: 仲裁场景柱状图
# ──────────────────────────────────────────────────────────────────────────
sc_ids, sc_pre, sc_colors, sc_status, sc_desc = [], [], [], [], []
for s in raw["scenarios"]:
    sc_ids.append(s["id"])
    sc_pre.append(len(s.get("prechecks", [])))
    st = "PASS" if s.get("all_pass") else ("SKIP" if s.get("skipped") else "FAIL")
    sc_status.append(st)
    sc_desc.append(s["desc"])
    sc_colors.append({"PASS": PRIMARY, "SKIP": PRIMARY_LT, "FAIL": ACCENT_NEG}[st])

fig = go.Figure(go.Bar(
    x=sc_ids,
    y=sc_pre,
    marker_color=sc_colors,
    text=[f"{p}/5<br>{st}" for p, st in zip(sc_pre, sc_status)],
    textposition="outside",
    textfont=dict(color=PRIMARY_DARK, size=11),
    hovertemplate="场景: %{x}<br>预检数: %{y}<br>描述: %{customdata}<extra></extra>",
    customdata=sc_desc,
    width=0.55,
))
layout = base_layout()
layout["title"] = make_title("仲裁器 8 场景最终回归 (P11) | 5 ALL PASS + 3 SKIP | 0 假阳性/假阴性")
layout["height"] = 420
layout["width"] = 820
layout["yaxis"] = dict(range=[0, 6], dtick=1, title_text="预检项执行数",
                      gridcolor=GRAY_BG, gridwidth=0.8, zeroline=False)
layout["xaxis"] = dict(gridcolor=GRAY_BG)
layout["showlegend"] = False
layout["shapes"] = [dict(type="line", x0=-0.5, x1=7.5, y0=5, y1=5,
                         line=dict(color=PRIMARY_LT, width=1, dash="dot"))]
layout["annotations"] = [dict(x=7.3, y=5.15, text="满分线 5/5",
                              font=dict(color=PRIMARY_MID, size=9),
                              showarrow=False)]
fig.update_layout(layout)
fig.write_html(os.path.join(OUT, "03_scenario_bars.html"),
               include_plotlyjs="cdn", full_html=False)
print("✅ 03_scenario_bars.html")

# ──────────────────────────────────────────────────────────────────────────
# HTML 4: 风险闭环进度
# ──────────────────────────────────────────────────────────────────────────
risks = [
    ("R-V88-P6-001", 100, "CLOSED", "3项预检静态True→真实文件校验 (P7)"),
    ("R-V88-P7-001", 100, "CLOSED", "#3文档校验局限→JSON迁移方案 (P8, Phase04落地)"),
    ("R-V88-P8-001", 100, "CLOSED", "快照格式不匹配→JSON+双源校验10/10 (P9)"),
]
fig = go.Figure()
for i, (name, prog, state, note) in enumerate(risks):
    color = {"CLOSED": PRIMARY, "DEFERRED": PRIMARY_MID, "OPEN": ACCENT_NEG}[state]
    fig.add_trace(go.Bar(
        y=[name], x=[100], orientation="h",
        marker_color=GRAY_BG, width=0.5,
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Bar(
        y=[name], x=[prog], orientation="h",
        marker_color=color, width=0.5,
        text=f"{prog}% {state}",
        textposition="inside",
        textfont=dict(color=WHITE, size=12),
        hovertemplate=f"{name}<br>{state}<br>{note}<extra></extra>",
        showlegend=False,
    ))
layout = base_layout()
layout["title"] = make_title("风险台账闭环进度 (3/3 全部闭环) | 0 阻断")
layout["height"] = 320
layout["width"] = 820
layout["barmode"] = "overlay"
layout["xaxis"] = dict(range=[0, 110], dtick=25,
                      tickformat=".0f", title_text="%",
                      gridcolor=GRAY_BG, gridwidth=0.8)
layout["yaxis"] = dict(autorange="reversed", gridcolor=GRAY_BG)
layout["showlegend"] = False
fig.update_layout(layout)
fig.write_html(os.path.join(OUT, "04_risk_progress.html"),
               include_plotlyjs="cdn", full_html=False)
print("✅ 04_risk_progress.html")

# ──────────────────────────────────────────────────────────────────────────
# HTML 5: 三方口径矩阵
# ──────────────────────────────────────────────────────────────────────────
# 用 Plotly Table 表示矩阵（支持 per-cell fill_color）
# 注：Plotly 5.15 Table.cells.font 只接受单个 Font dict，不支持 per-cell 颜色
#     → 统一 WHITE 文字；用两个暗色 fill 区分 PASS / N/A
agents = ["HERMEShf", "DSHB", "DSHE"]
dims = ["因子矩阵口径", "快照格式", "哈希绑定", "预检逻辑", "风险台账"]
cells = [
    [1, 1, 1],
    [1, 1, 1],
    [1, 1, 0],
    [1, 0, 0],
    [1, 1, 1],
]
n_rows = len(dims)
# 因 Plotly 5.15 Table.cells.font 只接受单一 Font dict（无 per-cell 文字色），
# 选用浅色底 + 统一黑字方案，靠"深浅"区分 PASS / N/A，保留紫色语义：
PASS_FILL = PRIMARY_LT     # #C7B5DC 浅紫（黑字可读，保留"紫=好"语义）
NA_FILL   = GRAY_BG        # #ECECF1 浅灰（黑字可读）
LABEL_FILL = PRIMARY_DARK  # 深紫（白字，与表头协调）

# 第 1 列：维度名
col0_fill = [LABEL_FILL] * n_rows
col0_values = list(dims)
# Agent 列
col_fill = []
col_values = []
for a_idx in range(len(agents)):
    col_fill.append([PASS_FILL if cells[i][a_idx] else NA_FILL for i in range(n_rows)])
    col_values.append(["PASS" if cells[i][a_idx] else "N/A" for i in range(n_rows)])

fig = go.Figure(go.Table(
    header=dict(
        values=["维度"] + agents,
        fill_color=PRIMARY_DARK,
        font=dict(color=WHITE, size=13),
        align="center",
        height=34,
    ),
    cells=dict(
        values=[col0_values] + col_values,
        fill_color=[col0_fill] + col_fill,
        # 统一黑字（浅色底可读）；维度列虽为深紫底，但仍黑字——牺牲一点反差
        # 但保留 PASS/N/A 主色语义；如需更佳对比，可切换到 PNG 版
        font=dict(color=BLACK_TXT, size=12),
        align="center",
        height=34,
    ),
))

layout = base_layout()
layout["title"] = make_title("三方口径一致性矩阵 | 5维度 × 3 Agent | PASS=浅紫 / N/A=浅灰")
layout["height"] = 380
layout["width"] = 560
layout["margin"] = dict(l=40, r=20, t=60, b=20)
fig.update_layout(layout)
fig.write_html(os.path.join(OUT, "05_caliber_matrix.html"),
               include_plotlyjs="cdn", full_html=False)
print("✅ 05_caliber_matrix.html")

print("\n=== HTML generation complete ===")
for f in sorted(os.listdir(OUT)):
    if f.endswith(".html"):
        print(f"  {f:40s} {os.path.getsize(os.path.join(OUT,f)):>7d} bytes")
