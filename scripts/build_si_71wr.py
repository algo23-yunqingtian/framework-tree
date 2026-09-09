#!/usr/bin/env python3
"""硅(SI) 7.1 成本子页 · wr数据 · v1 · 3 图真数据

图1 工业硅成本-441#(正主)：wr231 工业硅成本-441#(月)
图2 工业硅成本-553#(辅)：wr232 工业硅成本-553#(月)
图3 光伏级工业硅成本(辅)：wr233 光伏级工业硅成本(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_si71wr_c1", "echart_si71wr_c2", "echart_si71wr_c3"]

m_441 = load_metric("wr231", code="SI")
m_553 = load_metric("wr232", code="SI")
m_pv = load_metric("wr233", code="SI")

d_441 = pairs(m_441)
d_553 = pairs(m_553)
d_pv = pairs(m_pv)

print("[POINTS] 441#=%d 553#=%d 光伏级=%d" % (len(d_441), len(d_553), len(d_pv)))

h1, j1 = chart_line_t(
    "echart_si71wr_c1",
    "工业硅成本-441#（7.1 正主）",
    "工业硅成本-441# · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_441), latest(m_441)),
    "#c08a3e", d_441,
    "什么时候看：7.1 成本曲线的正主图——判断工业硅成本水平。<br>"
    "怎么看：成本上行=原料或能源涨价=利润承压。成本下行=原料或能源降价=利润扩张。"
)

h2, j2 = chart_line_t(
    "echart_si71wr_c2",
    "工业硅成本-553#·季节图",
    "工业硅成本-553# · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_553), latest(m_553)),
    "#5b98c9", d_553,
    "什么时候看：553#是另一个主要工业硅牌号。<br>"
    "怎么看：553#成本与441#成本结合看，判断不同牌号成本差异。"
)

h3, j3 = chart_line_t(
    "echart_si71wr_c3",
    "光伏级工业硅成本·季节图",
    "光伏级工业硅成本 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_pv), latest(m_pv)),
    "#e06c75", d_pv,
    "什么时候看：光伏级工业硅是光伏产业链上游核心材料。<br>"
    "怎么看：光伏级成本上行=光伏成本上升=装机量可能下降。"
)

NOTE = """<strong style="color:#c9d1d9">7.1 定义：</strong>成本曲线 = 工业硅成本 + 光伏级成本，判断硅产业链成本水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr231 工业硅成本-441#(元/吨/月) —— 主力牌号。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr232 工业硅成本-553# · wr233 光伏级工业硅成本。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID02036183 441# + ID01523500 553# + ID02036184 光伏级）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>441# 41点；553# 187点；光伏级187点(月度)。<br>
<strong style="color:#c9d1d9">7.x 边界：</strong>7.1=成本曲线(正主=441#) · 7.2=日度利润 · 7.3=能源/原料成本。"""

html = page_html(
    "硅(SI) 7.1 成本曲线",
    make_crumb("硅", "SI", "7", "成本利润", "7.1", "成本曲线", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 硅(SI) 7.1 成本曲线 · v1（3 图真数据 · 441# · 553# · 光伏级）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("si_71wr_cost_curve.html", html)
