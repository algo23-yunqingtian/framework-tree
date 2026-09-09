#!/usr/bin/env python3
"""镍(NI) 6.1 进出口子页 · wr数据 · v1 · 3 图真数据

图1 镍铁进口量(正主)：wr271 镍铁进口量(月)
图2 镍铁进口-印尼(辅)：wr272 镍铁进口-印尼(月)
图3 镍铁进口总量(辅)：wr275 镍铁进口总量(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ni61wr_c1", "echart_ni61wr_c2", "echart_ni61wr_c3"]

m_total = load_metric("wr271", code="NI")
m_id = load_metric("wr272", code="NI")
m_all = load_metric("wr275", code="NI")

d_total = pairs(m_total)
d_id = pairs(m_id)
d_all = pairs(m_all)

print("[POINTS] 进口=%d 印尼=%d 总量=%d" % (len(d_total), len(d_id), len(d_all)))

h1, j1 = chart_line_t(
    "echart_ni61wr_c1",
    "镍铁进口量（6.1 正主）",
    "镍铁进口量 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_total), latest(m_total)),
    "#7a8c5b", d_total,
    "什么时候看：6.1 进出口的正主图——判断中国镍铁进口依赖度。<br>"
    "怎么看：进口上行=国内镍铁供给不足=进口依赖增加。进口下行=国内供给充裕=进口依赖减少。"
)

h2, j2 = chart_line_t(
    "echart_ni61wr_c2",
    "镍铁进口-印尼·季节图",
    "镍铁进口-印尼 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_id), latest(m_id)),
    "#5b98c9", d_id,
    "什么时候看：印尼是中国镍铁最大进口来源国。<br>"
    "怎么看：印尼进口上行=印尼镍铁供应充裕。印尼进口下行=印尼供应收缩。"
)

h3, j3 = chart_line_t(
    "echart_ni61wr_c3",
    "镍铁进口总量·季节图",
    "镍铁进口总量 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_all), latest(m_all)),
    "#e06c75", d_all,
    "什么时候看：总量反映镍铁整体进口规模。<br>"
    "怎么看：总量与分国别结合看，判断进口来源结构变化。"
)

NOTE = """<strong style="color:#c9d1d9">6.1 定义：</strong>进出口 = 镍铁进口量 + 印尼进口 + 总量，判断镍铁进口依赖度与来源结构。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr271 镍铁进口量(吨/月) —— 进口依赖度。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr272 印尼进口 · wr275 总量。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01002128 进口 + ID01002129 印尼 + ID01002130 总量）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>进口79点；印尼54点；总量79点(月度)。<br>
<strong style="color:#c9d1d9">6.x 边界：</strong>6.1=进出口(正主=进口量) · 6.2=精炼进出口 · 6.3=制品出口 · 6.4=全球化布局。"""

html = page_html(
    "镍(NI) 6.1 进出口",
    make_crumb("镍", "NI", "6", "进出口", "6.1", "进出口", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 镍(NI) 6.1 进出口 · v1（3 图真数据 · 进口量 · 印尼 · 总量）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ni_61wr_trade.html", html)
