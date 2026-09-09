#!/usr/bin/env python3
"""硅(SI) 2.3 价格子页 · wr数据 · v1 · 3 图真数据

图1 工业硅价格-441#(正主)：wr207 工业硅价格-441#(日)
图2 工业硅价格-553#(辅)：wr232 工业硅价格(月)
图3 多晶硅价格-N型182mm(辅)：wr219 多晶硅价格-N型182mm(日)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_si23wr_c1", "echart_si23wr_c2", "echart_si23wr_c3"]

m_441 = load_metric("wr207", code="SI")
m_553 = load_metric("wr232", code="SI")
m_poly = load_metric("wr219", code="SI")

d_441 = pairs(m_441)
d_553 = pairs(m_553)
d_poly = pairs(m_poly)

print("[POINTS] 441#=%d 553#=%d 多晶硅N182=%d" % (len(d_441), len(d_553), len(d_poly)))

h1, j1 = chart_line_t(
    "echart_si23wr_c1",
    "工业硅价格-441#（2.3 正主）",
    "工业硅价格-441#(天津) · 日 · 元/吨 · %d 点 · 至 %s" % (
        len(d_441), latest(m_441)),
    "#c08a3e", d_441,
    "什么时候看：2.3 海外价格的正主图——工业硅441#是主力合约。<br>"
    "怎么看：价格上行=硅供应偏紧或需求旺盛。价格下行=供应过剩或需求疲软。"
)

h2, j2 = chart_line_t(
    "echart_si23wr_c2",
    "工业硅价格-553#·季节图",
    "工业硅价格 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_553), latest(m_553)),
    "#5b98c9", d_553,
    "什么时候看：553#是另一个主要工业硅牌号。<br>"
    "怎么看：553#与441#价差反映供需结构变化。"
)

h3, j3 = chart_line_t(
    "echart_si23wr_c3",
    "多晶硅价格-N型182mm·季节图",
    "多晶硅价格-N型182mm · 日 · 元/片 · %d 点 · 至 %s" % (
        len(d_poly), latest(m_poly)),
    "#e06c75", d_poly,
    "什么时候看：多晶硅是光伏产业链上游核心环节。<br>"
    "怎么看：多晶硅价格下行=光伏成本下降=装机量上升。"
)

NOTE = """<strong style="color:#c9d1d9">2.3 定义：</strong>海外价格 = 工业硅价格 + 多晶硅价格，判断硅产业链价格基本面。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr207 工业硅价格-441#(元/吨/日) —— 主力合约。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr232 工业硅价格(553#) · wr219 多晶硅价格-N型182mm · wr220 N型210mm · wr209 光伏级工业硅。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID00258568 441# + ID01523500 553# + ID01994882 多晶硅N182）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>441# 1660点(日度)；553# 187点(月度)；多晶硅N182 79点(日度)。<br>
<strong style="color:#c9d1d9">2.x 边界：</strong>2.1=盘面结构 · 2.2=现货升贴水 · 2.3=海外价格(正主=441#) · 2.4=价差体系 · 2.5=估值利润 · 2.6=持仓席位。"""

html = page_html(
    "硅(SI) 2.3 价格",
    make_crumb("硅", "SI", "2", "价格信号", "2.3", "海外价格", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 硅(SI) 2.3 价格 · v1（3 图真数据 · 441# · 553# · 多晶硅N182）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("si_23wr_price.html", html)
