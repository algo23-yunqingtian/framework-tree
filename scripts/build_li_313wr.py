#!/usr/bin/env python3
"""碳酸锂(LC) 3.1.3 锂矿库存子页 · wr数据 · v1 · 3 图真数据

图1 锂辉石库存(正主)：wr150 锂辉石库存(月)
图2 锂辉石库存-国内(辅)：wr151 锂辉石库存-国内(月)
图3 锂辉石库存-隐性(辅)：wr152 锂辉石库存-隐性(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_lc313wr_c1", "echart_lc313wr_c2", "echart_lc313wr_c3"]

m_total = load_metric("wr150", code="LC")
m_domestic = load_metric("wr151", code="LC")
m_hidden = load_metric("wr152", code="LC")

d_total = pairs(m_total)
d_domestic = pairs(m_domestic)
d_hidden = pairs(m_hidden)

print("[POINTS] 总库存=%d 国内=%d 隐性=%d" % (len(d_total), len(d_domestic), len(d_hidden)))

h1, j1 = chart_line_t(
    "echart_lc313wr_c1",
    "锂辉石库存（3.1.3 正主）",
    "锂辉石库存 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_total), latest(m_total)),
    "#4f8a7a", d_total,
    "什么时候看：3.1.3 锂矿库存的正主图——判断锂辉石整体库存水平。<br>"
    "怎么看：库存上行=原料供应充裕或需求疲软。库存下行=需求旺盛或供应收缩。"
)

h2, j2 = chart_line_t(
    "echart_lc313wr_c2",
    "锂辉石库存-国内·季节图",
    "锂辉石库存-国内 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_domestic), latest(m_domestic)),
    "#5b98c9", d_domestic,
    "什么时候看：国内库存反映本土锂辉石供应水平。<br>"
    "怎么看：国内库存变化反映本土供需平衡。"
)

h3, j3 = chart_line_t(
    "echart_lc313wr_c3",
    "锂辉石库存-隐性·季节图",
    "锂辉石库存-隐性 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_hidden), latest(m_hidden)),
    "#e06c75", d_hidden,
    "什么时候看：隐性库存是未在交易所注册的库存。<br>"
    "怎么看：隐性库存上行=潜在交割压力增加。隐性库存下行=交割压力减轻。"
)

NOTE = """<strong style="color:#c9d1d9">3.1.3 定义：</strong>锂矿库存 = 锂辉石库存 + 国内库存 + 隐性库存，判断锂矿库存水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr150 锂辉石库存(吨/月) —— 总库存。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr151 国内库存 · wr152 隐性库存 · wr153 锂辉石贸易量 · wr154 锂辉石进口量。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01380165 总库存 + ID01380166 国内 + ID01380167 隐性）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>总库存151点；国内18点；隐性19点(月度)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.1=海外矿财报产量 · 3.1.2=分国别总量 · 3.1.3=锂矿库存(正主=总库存) · 3.1.4=矿进口发运到港 · 3.1.5=加工费 · 3.2.x=精炼。"""

html = page_html(
    "碳酸锂(LC) 3.1.3 锂矿库存",
    make_crumb("碳酸锂", "LC", "3", "供给", "3.1.3", "锂矿库存", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 碳酸锂(LC) 3.1.3 锂矿库存 · v1（3 图真数据 · 总库存 · 国内 · 隐性）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("li_313wr_lithium_inventory.html", html)
