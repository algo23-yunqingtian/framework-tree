#!/usr/bin/env python3
"""锡(SN) 2.3 价格子页 · wr数据 · v1 · 3 图真数据

图1 锡制品升贴水(正主)：wr169 锡制品升贴水(日)
图2 锡锭升水(辅)：wr173 锡锭升水(日)
图3 锡锭出厂价(辅)：wr174 锡锭出厂价(日)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_sn23wr_c1", "echart_sn23wr_c2", "echart_sn23wr_c3"]

m_premium = load_metric("wr169", code="SN")
m_ingot = load_metric("wr173", code="SN")
m_mill = load_metric("wr174", code="SN")

d_premium = pairs(m_premium)
d_ingot = pairs(m_ingot)
d_mill = pairs(m_mill)

print("[POINTS] 升贴水=%d 升水=%d 出厂价=%d" % (len(d_premium), len(d_ingot), len(d_mill)))

h1, j1 = chart_line_t(
    "echart_sn23wr_c1",
    "锡制品升贴水（2.3 正主）",
    "锡制品升贴水 · 日 · 元/吨 · %d 点 · 至 %s" % (
        len(d_premium), latest(m_premium)),
    "#8c6b9c", d_premium,
    "什么时候看：2.3 海外价格的正主图——判断锡制品价格结构。<br>"
    "怎么看：升贴水上行=锡制品需求旺盛或供应偏紧。升贴水下行=需求疲软或供应过剩。"
)

h2, j2 = chart_line_t(
    "echart_sn23wr_c2",
    "锡锭升水·季节图",
    "锡锭升水 · 日 · 百分比 · %d 点 · 至 %s" % (
        len(d_ingot), latest(m_ingot)),
    "#5b98c9", d_ingot,
    "什么时候看：锡锭升水反映锡锭现货与期货的价差。<br>"
    "怎么看：升水上行=现货偏紧。升水下行=现货充裕。"
)

h3, j3 = chart_line_t(
    "echart_sn23wr_c3",
    "锡锭出厂价·季节图",
    "锡锭出厂价 · 日 · 元/吨 · %d 点 · 至 %s" % (
        len(d_mill), latest(m_mill)),
    "#e06c75", d_mill,
    "什么时候看：锡锭出厂价是锡冶炼厂的出厂价格。<br>"
    "怎么看：出厂价上行=冶炼厂利润扩张。出厂价下行=冶炼厂利润收缩。"
)

NOTE = """<strong style="color:#c9d1d9">2.3 定义：</strong>海外价格 = 锡制品升贴水 + 锡锭升水 + 锡锭出厂价，判断锡价格基本面。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr169 锡制品升贴水(元/吨/日) —— 价格结构。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr173 锡锭升水(百分比/日) · wr174 锡锭出厂价(元/吨/日)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01668719 升贴水 + ID01895225 升水 + ID01590826 出厂价）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>升贴水1540点；升水1588点；出厂价1589点(日度)。<br>
<strong style="color:#c9d1d9">2.x 边界：</strong>2.1=盘面结构 · 2.2=现货升贴水 · 2.3=海外价格(正主=升贴水) · 2.4=价差体系 · 2.5=估值利润 · 2.6=持仓席位。"""

html = page_html(
    "锡(SN) 2.3 价格",
    make_crumb("锡", "SN", "2", "价格信号", "2.3", "海外价格", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 锡(SN) 2.3 价格 · v1（3 图真数据 · 升贴水 · 升水 · 出厂价）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("sn_23wr_price.html", html)
