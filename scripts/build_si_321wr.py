#!/usr/bin/env python3
"""硅(SI) 3.2.1 多晶硅产量子页 · wr数据 · v1 · 3 图真数据

图1 多晶硅产量(正主)：wr212 多晶硅产量(月)
图2 多晶硅产量-青海(辅)：wr218 多晶硅产量-青海(月)
图3 多晶硅产量-云南(辅)：wr221 多晶硅产量-云南(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_si321wr_c1", "echart_si321wr_c2", "echart_si321wr_c3"]

m_total = load_metric("wr212", code="SI")
m_qh = load_metric("wr218", code="SI")
m_yn = load_metric("wr221", code="SI")

d_total = pairs(m_total)
d_qh = pairs(m_qh)
d_yn = pairs(m_yn)

print("[POINTS] 总量=%d 青海=%d 云南=%d" % (len(d_total), len(d_qh), len(d_yn)))

h1, j1 = chart_line_t(
    "echart_si321wr_c1",
    "多晶硅产量（3.2.1 正主）",
    "多晶硅产量 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_total), latest(m_total)),
    "#c08a3e", d_total,
    "什么时候看：3.2.1 精炼产量的正主图——判断多晶硅行业产出水平。<br>"
    "怎么看：产量上行=开工率提升=供给增加。产量下行=减产或检修=供给收缩。"
)

h2, j2 = chart_line_t(
    "echart_si321wr_c2",
    "多晶硅产量-青海·季节图",
    "多晶硅产量-青海 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_qh), latest(m_qh)),
    "#5b98c9", d_qh,
    "什么时候看：青海是多晶硅主产区之一。<br>"
    "怎么看：青海产量变化反映主产区供需平衡。"
)

h3, j3 = chart_line_t(
    "echart_si321wr_c3",
    "多晶硅产量-云南·季节图",
    "多晶硅产量-云南 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_yn), latest(m_yn)),
    "#e06c75", d_yn,
    "什么时候看：云南是新兴多晶硅产区。<br>"
    "怎么看：云南产量上行=新产能投放=供给扩张。"
)

NOTE = """<strong style="color:#c9d1d9">3.2.1 定义：</strong>精炼产量 = 多晶硅产量 + 分地区产量，判断实际开工水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr212 多晶硅产量(吨/月) —— 总产量。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr218 青海产量 · wr221 云南产量 · wr219 N型182mm价格 · wr220 N型210mm价格。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID02036182 总量 + ID02036185 青海 + ID02032074 云南）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>总量32点；青海32点；云南133点(月度)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.x=矿端 · 3.2.1=精炼产量(正主=总量) · 3.2.2=开工率 · 3.2.3=再生供应 · 3.2.4=冶炼利润弹性。"""

html = page_html(
    "硅(SI) 3.2.1 多晶硅产量",
    make_crumb("硅", "SI", "3", "供给", "3.2.1", "多晶硅产量", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 硅(SI) 3.2.1 多晶硅产量 · v1（3 图真数据 · 总量 · 青海 · 云南）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("si_321wr_polysilicon.html", html)
