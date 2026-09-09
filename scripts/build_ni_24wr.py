#!/usr/bin/env python3
"""镍(NI) 2.4 价差子页 · wr数据 · v1 · 2 图真数据

图1 硫酸镍价格(正主)：wr254 硫酸镍价格(月)
图2 镍价(辅)：wr256 镍价(日)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ni24wr_c1", "echart_ni24wr_c2"]

m_sulfate = load_metric("wr254", code="NI")
m_nickel = load_metric("wr256", code="NI")

d_sulfate = pairs(m_sulfate)
d_nickel = pairs(m_nickel)

print("[POINTS] 硫酸镍=%d 镍价=%d" % (len(d_sulfate), len(d_nickel)))

h1, j1 = chart_line_t(
    "echart_ni24wr_c1",
    "硫酸镍价格（2.4 正主）",
    "硫酸镍价格 · 月 · 万元/吨 · %d 点 · 至 %s" % (
        len(d_sulfate), latest(m_sulfate)),
    "#7a8c5b", d_sulfate,
    "什么时候看：2.4 价差的正主图——硫酸镍是镍的主要化工品种。<br>"
    "怎么看：硫酸镍价格上行=下游需求旺盛。硫酸镍价格下行=需求疲软。"
)

h2, j2 = chart_line_t(
    "echart_ni24wr_c2",
    "镍价·季节图",
    "镍价(日) · 元/吨 · %d 点 · 至 %s" % (
        len(d_nickel), latest(m_nickel)),
    "#5b98c9", d_nickel,
    "什么时候看：镍价是硫酸镍定价的基础。<br>"
    "怎么看：镍价上行=硫酸镍成本上升=利润承压。镍价下行=成本下降=利润扩张。"
)

NOTE = """<strong style="color:#c9d1d9">2.4 定义：</strong>价差 = 硫酸镍价格 + 镍价，判断镍化工品种价格结构。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr254 硫酸镍价格(万元/吨/月) —— 化工品种。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr256 镍价(元/吨/日) · wr257 镍价(周) · wr252 镍只涨。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01722282 硫酸镍 + ID00185681 镍价）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>硫酸镍36点；镍价1661点。<br>
<strong style="color:#c9d1d9">2.x 边界：</strong>2.1=盘面结构 · 2.2=现货升贴水 · 2.3=海外价格 · 2.4=价差体系(正主=硫酸镍) · 2.5=估值利润 · 2.6=持仓席位。"""

html = page_html(
    "镍(NI) 2.4 价差",
    make_crumb("镍", "NI", "2", "价格信号", "2.4", "价差体系", "1", 2),
    "知几",
    h1, h2, "", NOTE,
    "有色金属产业指标树 · 镍(NI) 2.4 价差 · v1（2 图真数据 · 硫酸镍 · 镍价）· indicators_v1.json v3.82",
    j1 + "\n" + j2,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ni_24wr_spread.html", html)
