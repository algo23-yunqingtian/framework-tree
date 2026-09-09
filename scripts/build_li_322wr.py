#!/usr/bin/env python3
"""碳酸锂(LC) 3.2.2 开工率子页 · wr数据 · v1 · 3 图真数据

图1 碳酸锂开工率(正主)：wr105 碳酸锂开工率(月)
图2 碳酸锂总能耗(辅)：wr106 碳酸锂总能耗(月)
图3 碳酸锂月度产量(辅)：wr138 碳酸锂月度产量(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_lc322wr_c1", "echart_lc322wr_c2", "echart_lc322wr_c3"]

m_rate = load_metric("wr105", code="LC")
m_energy = load_metric("wr106", code="LC")
m_prod = load_metric("wr138", code="LC")

d_rate = pairs(m_rate)
d_energy = pairs(m_energy)
d_prod = pairs(m_prod)

print("[POINTS] 开工率=%d 总能耗=%d 月产量=%d" % (len(d_rate), len(d_energy), len(d_prod)))

h1, j1 = chart_line_t(
    "echart_lc322wr_c1",
    "碳酸锂开工率（3.2.2 正主）",
    "碳酸锂开工率 · 月 · 百分比 · %d 点 · 至 %s" % (
        len(d_rate), latest(m_rate)),
    "#4f8a7a", d_rate,
    "什么时候看：3.2.2 开工率的正主图——判断碳酸锂行业开工水平。<br>"
    "怎么看：开工率上行=行业景气度提升=供给增加。开工率下行=行业低迷=供给收缩。"
)

h2, j2 = chart_line_t(
    "echart_lc322wr_c2",
    "碳酸锂总能耗·季节图",
    "碳酸锂总能耗 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_energy), latest(m_energy)),
    "#5b98c9", d_energy,
    "什么时候看：总能耗反映碳酸锂生产的能源消耗。<br>"
    "怎么看：能耗上行=产量增加或工艺变化。能耗下行=产量减少或工艺改进。"
)

h3, j3 = chart_line_t(
    "echart_lc322wr_c3",
    "碳酸锂月度产量·季节图",
    "碳酸锂月度产量 · 月 · 百分比 · %d 点 · 至 %s" % (
        len(d_prod), latest(m_prod)),
    "#e06c75", d_prod,
    "什么时候看：月度产量反映碳酸锂整体产出水平。<br>"
    "怎么看：产量上行=供给增加。产量下行=供给收缩。"
)

NOTE = """<strong style="color:#c9d1d9">3.2.2 定义：</strong>开工率 = 碳酸锂开工率 + 总能耗 + 月度产量，判断行业开工水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr105 碳酸锂开工率(百分比/月) —— 开工水平。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr106 总能耗(吨/月) · wr138 月度产量(百分比/月)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01707137 开工率 + ID01349541 总能耗 + ID01380153 月产量）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>开工率32点；总能耗56点；月产量68点(月度)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.x=矿端 · 3.2.1=精炼产量 · 3.2.2=开工率(正主=开工率) · 3.2.3=再生供应 · 3.2.4=冶炼利润弹性。"""

html = page_html(
    "碳酸锂(LC) 3.2.2 开工率",
    make_crumb("碳酸锂", "LC", "3", "供给", "3.2.2", "开工率", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 碳酸锂(LC) 3.2.2 开工率 · v1（3 图真数据 · 开工率 · 总能耗 · 月产量）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("li_322wr_utilization.html", html)
