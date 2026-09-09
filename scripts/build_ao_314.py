#!/usr/bin/env python3
"""氧化铝(AO) 3.1.4 矿进口发运到港口页 · v1 · 1 图真数据

图1 港口库存-中国(正主)：wr74 港口库存-中国(月) —— 矿端到港消化节奏
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao314_c1"]

m_port = load_metric("wr74", code="AO")
d_port = pairs(m_port)

print("[POINTS] 港口库存=%d" % len(d_port))

h1, j1 = chart_line_t(
    "echart_ao314_c1",
    "港口库存-中国（3.1.4 正主）",
    "港口库存-中国 · 月 · 万吨 · %d 点 · 至 %s" % (
        len(d_port), latest(m_port)),
    "#9a6b4f", d_port,
    "什么时候看：3.1.4 矿进口发运到港的正主图——判断矿端到港消化节奏。<br>"
    "怎么看：港口库存上行=到港充裕或消耗放缓=短期原料供应宽松。"
    "港口库存下行=消耗加快=供应偏紧。与几内亚出口结合看：库存上行+出口上行=供应充裕。"
)

NOTE = """<strong style="color:#c9d1d9">3.1.4 定义：</strong>矿进口发运到港 = 港口库存-中国，判断矿端到港消化节奏。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr74 港口库存-中国(万吨/月) —— 矿端到港消化节奏。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr73 几内亚出口(3.1.3) · wr66 铝土矿库存(待SMM)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID00188314 港口库存-中国）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>346点(月度)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.1=海外矿财报产量 · 3.1.2=分国别总量 · 3.1.3=国内矿产量 · 3.1.4=矿进口发运到港(正主=港口库存) · 3.1.5=TC加工费 · 3.2.x=精炼。"""

html = page_html(
    "氧化铝(AO) 3.1.4 矿进口发运到港",
    make_crumb("氧化铝", "AO", "3", "供给", "3.1.4", "矿进口发运到港", "1", 1),
    "知几",
    h1, "", "", NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 3.1.4 矿进口发运到港 · v1（1 图真数据 · 港口库存-中国）· indicators_v1.json v3.82",
    j1,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_314_import_arrival.html", html)
