#!/usr/bin/env python3
"""碳酸锂(LC) 3.2.1 精炼产量子页 · wr数据 · v1 · 3 图真数据

图1 碳酸锂产量-四川(正主)：wr94 碳酸锂产量-四川(月)
图2 碳酸锂产量-山东(辅)：wr95 碳酸锂产量-山东(月)
图3 碳酸锂产量-青海(辅)：wr101 碳酸锂产量-青海(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_lc321_c1", "echart_lc321_c2", "echart_lc321_c3"]

m_sc = load_metric("wr94", code="LC")
m_sd = load_metric("wr95", code="LC")
m_qh = load_metric("wr101", code="LC")

d_sc = pairs(m_sc)
d_sd = pairs(m_sd)
d_qh = pairs(m_qh)

print("[POINTS] 四川=%d 山东=%d 青海=%d" % (len(d_sc), len(d_sd), len(d_qh)))

h1, j1 = chart_line_t(
    "echart_lc321_c1",
    "碳酸锂产量-四川（3.2.1 正主）",
    "碳酸锂产量-四川 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_sc), latest(m_sc)),
    "#4f8a7a", d_sc,
    "什么时候看：3.2.1 精炼产量的正主图——四川是中国碳酸锂主产区。<br>"
    "怎么看：产量上行=开工率提升=供给增加。产量下行=减产或检修=供给收缩。"
)

h2, j2 = chart_line_t(
    "echart_lc321_c2",
    "碳酸锂产量-山东·季节图",
    "碳酸锂产量-山东 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_sd), latest(m_sd)),
    "#5b98c9", d_sd,
    "什么时候看：山东是另一主要碳酸锂产区。<br>"
    "怎么看：山东产量变化反映主产区供需平衡。"
)

h3, j3 = chart_line_t(
    "echart_lc321_c3",
    "碳酸锂产量-青海·季节图",
    "碳酸锂产量-青海 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_qh), latest(m_qh)),
    "#e06c75", d_qh,
    "什么时候看：青海以盐湖提锂为主，产量受季节影响较大。<br>"
    "怎么看：青海产量下行=盐湖提锂淡季=供给收缩。"
)

NOTE = """<strong style="color:#c9d1d9">3.2.1 定义：</strong>精炼产量 = 碳酸锂分地区产量，判断实际开工水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr94 碳酸锂产量-四川(吨/月) —— 主产区。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr95 山东 · wr96 内蒙 · wr97 广西 · wr98 江西 · wr99 河北 · wr100 云南 · wr101 青海。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01865198 四川 + ID01380152 山东 + ID01865195 青海）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>四川56点；山东44点；青海56点(月度)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.x=矿端 · 3.2.1=精炼产量(正主=四川) · 3.2.2=开工率 · 3.2.3=再生供应 · 3.2.4=冶炼利润弹性。"""

html = page_html(
    "碳酸锂(LC) 3.2.1 精炼产量",
    make_crumb("碳酸锂", "LC", "3", "供给", "3.2.1", "精炼产量", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 碳酸锂(LC) 3.2.1 精炼产量 · v1（3 图真数据 · 四川 · 山东 · 青海）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("li_321_wr_production.html", html)
