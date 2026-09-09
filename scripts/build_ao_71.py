#!/usr/bin/env python3
"""氧化铝(AO) 7.1 成本曲线子页 · v1 · 1 图真数据

图1 氧化铝冶炼成本(正主)：wr47 冶炼成本(月) —— 成本曲线核心
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao71_c1"]

m_cost = load_metric("wr47", code="AO")
d_cost = pairs(m_cost)

print("[POINTS] 冶炼成本=%d" % len(d_cost))

h1, j1 = chart_line_t(
    "echart_ao71_c1",
    "氧化铝冶炼成本（7.1 正主）",
    "冶炼成本 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_cost), latest(m_cost)),
    "#9a6b4f", d_cost,
    "什么时候看：7.1 成本曲线的正主图——判断氧化铝行业成本水平与利润空间。<br>"
    "怎么看：成本上行=原料或能源涨价=利润承压。成本下行=原料或能源降价=利润扩张。"
    "与价格结合看：价格-成本=毛利，毛利为正=行业盈利，毛利为负=亏损减产。"
)

NOTE = """<strong style="color:#c9d1d9">7.1 定义：</strong>成本曲线 = 氧化铝冶炼成本，判断行业成本水平与利润空间。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr47 氧化铝冶炼成本(元/吨/月) —— 成本曲线核心。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr40 中国平均价(价格端) · wr34/wr35 三网均价(分地区)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01721669 冶炼成本）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>47点(月度)。<br>
<strong style="color:#c9d1d9">7.x 边界：</strong>7.1=成本曲线(正主=冶炼成本) · 7.2=日度利润 · 7.3=能源/原料成本。"""

html = page_html(
    "氧化铝(AO) 7.1 成本曲线",
    make_crumb("氧化铝", "AO", "7", "成本利润", "7.1", "成本曲线", "1", 1),
    "知几",
    h1, "", "", NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 7.1 成本曲线 · v1（1 图真数据 · 冶炼成本）· indicators_v1.json v3.82",
    j1,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_71_cost_curve.html", html)
