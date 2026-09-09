#!/usr/bin/env python3
"""碳酸锂(LC) 4.1 交易所库存子页 · wr数据 · v1 · 2 图真数据

图1 碳酸锂仓单(正主)：wr124 碳酸锂仓单(日)
图2 碳酸锂总库存(辅)：wr130 碳酸锂总库存(周)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_lc41wr_c1", "echart_lc41wr_c2"]

m_receipt = load_metric("wr124", code="LC")
m_total = load_metric("wr130", code="LC")

d_receipt = pairs(m_receipt)
d_total = pairs(m_total)

print("[POINTS] 仓单=%d 总库存=%d" % (len(d_receipt), len(d_total)))

h1, j1 = chart_line_t(
    "echart_lc41wr_c1",
    "碳酸锂仓单（4.1 正主）",
    "碳酸锂仓单 · 日 · 吨 · %d 点 · 至 %s" % (
        len(d_receipt), latest(m_receipt)),
    "#4f8a7a", d_receipt,
    "什么时候看：4.1 交易所库存的正主图——判断碳酸锂交割压力。<br>"
    "怎么看：仓单上行=交割压力大=近月贴水扩大。仓单下行=交割压力小=近月升水扩大。"
)

h2, j2 = chart_line_t(
    "echart_lc41wr_c2",
    "碳酸锂总库存·季节图",
    "碳酸锂总库存 · 周 · 吨 · %d 点 · 至 %s" % (
        len(d_total), latest(m_total)),
    "#5b98c9", d_total,
    "什么时候看：总库存是仓单+社会库存的总量。<br>"
    "怎么看：总库存上行=全行业累库=供应过剩。总库存下行=去库=供需偏紧。"
)

NOTE = """<strong style="color:#c9d1d9">4.1 定义：</strong>交易所库存 = 碳酸锂仓单 + 总库存，判断库存水平与交割压力。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr124 碳酸锂仓单(吨/日) —— 交割压力。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr126 总库存-上期所 · wr130 总库存-广期所。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID00188314 仓单 + ID00188315 总库存）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>仓单663点(日度)；总库存35点(周度)。<br>
<strong style="color:#c9d1d9">4.x 边界：</strong>4.1=交易所库存(正主=仓单) · 4.2=仓单 · 4.3=社会库存 · 4.4=工厂库存 · 4.5=隐性在途。"""

html = page_html(
    "碳酸锂(LC) 4.1 交易所库存",
    make_crumb("碳酸锂", "LC", "4", "库存", "4.1", "交易所库存", "1", 2),
    "知几",
    h1, h2, "", NOTE,
    "有色金属产业指标树 · 碳酸锂(LC) 4.1 交易所库存 · v1（2 图真数据 · 仓单 · 总库存）· indicators_v1.json v3.82",
    j1 + "\n" + j2,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("li_41wr_exchange_inventory.html", html)
