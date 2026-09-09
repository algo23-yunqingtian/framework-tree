#!/usr/bin/env python3
"""碳酸锂(LC) 7.1 成本子页 · wr数据 · v1 · 3 图真数据

图1 锂辉石加工费-四川(正主)：wr158 锂辉石加工费-四川(月)
图2 锂辉石加工费-山东(辅)：wr159 锂辉石加工费-山东(月)
图3 锂辉石加工费-江西(辅)：wr160 锂辉石加工费-江西(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_lc71wr_c1", "echart_lc71wr_c2", "echart_lc71wr_c3"]

m_sc = load_metric("wr158", code="LC")
m_sd = load_metric("wr159", code="LC")
m_jx = load_metric("wr160", code="LC")

d_sc = pairs(m_sc)
d_sd = pairs(m_sd)
d_jx = pairs(m_jx)

print("[POINTS] 四川=%d 山东=%d 江西=%d" % (len(d_sc), len(d_sd), len(d_jx)))

h1, j1 = chart_line_t(
    "echart_lc71wr_c1",
    "锂辉石加工费-四川（7.1 正主）",
    "锂辉石加工费-四川 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_sc), latest(m_sc)),
    "#4f8a7a", d_sc,
    "什么时候看：7.1 成本曲线的正主图——判断锂辉石加工成本。<br>"
    "怎么看：加工费上行=加工利润扩张。加工费下行=加工利润收缩。"
)

h2, j2 = chart_line_t(
    "echart_lc71wr_c2",
    "锂辉石加工费-山东·季节图",
    "锂辉石加工费-山东 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_sd), latest(m_sd)),
    "#5b98c9", d_sd,
    "什么时候看：山东是另一主要加工费地区。<br>"
    "怎么看：山东加工费与四川价差反映地区供需差异。"
)

h3, j3 = chart_line_t(
    "echart_lc71wr_c3",
    "锂辉石加工费-江西·季节图",
    "锂辉石加工费-江西 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_jx), latest(m_jx)),
    "#e06c75", d_jx,
    "什么时候看：江西是新兴加工费地区。<br>"
    "怎么看：江西加工费低于四川=新产能价格竞争激烈。"
)

NOTE = """<strong style="color:#c9d1d9">7.1 定义：</strong>成本曲线 = 锂辉石加工费分地区，判断加工成本水平与地区价差。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr158 锂辉石加工费-四川(元/吨/月) —— 主产区。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr159 山东 · wr160 江西 · wr161 广西 · wr162 云南 · wr163 河北 · wr164 青海。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01380157 四川 + ID01380158 山东 + ID01380159 江西）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>四川56点；山东56点；江西56点(月度)。<br>
<strong style="color:#c9d1d9">7.x 边界：</strong>7.1=成本曲线(正主=四川加工费) · 7.2=日度利润 · 7.3=能源/原料成本。"""

html = page_html(
    "碳酸锂(LC) 7.1 成本曲线",
    make_crumb("碳酸锂", "LC", "7", "成本利润", "7.1", "成本曲线", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 碳酸锂(LC) 7.1 成本曲线 · v1（3 图真数据 · 四川 · 山东 · 江西加工费）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("li_71wr_cost_curve.html", html)
