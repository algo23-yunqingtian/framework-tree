#!/usr/bin/env python3
"""氧化铝(AO) 4.2 仓单子页 · v1 · 1 图真数据

图1 期货库存-氧化铝-广西(正主)：wr50 期货库存-氧化铝-广西(日) —— 交易所库存
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao42_c1"]

m_inv = load_metric("wr50", code="AO")
d_inv = pairs(m_inv)

print("[POINTS] 期货库存=%d" % len(d_inv))

h1, j1 = chart_line_t(
    "echart_ao42_c1",
    "期货库存-氧化铝-广西（4.2 正主）",
    "期货库存-氧化铝-广西 · 日 · 吨 · %d 点 · 至 %s" % (
        len(d_inv), latest(m_inv)),
    "#9a6b4f", d_inv,
    "什么时候看：4.2 仓单的正主图——判断交易所库存水平与交割压力。<br>"
    "怎么看：库存上行=交割压力大=近月贴水扩大。库存下行=交割压力小=近月升水扩大。"
    "与仓单结合看：库存-仓单=未注册库存，反映交割潜力。"
)

NOTE = """<strong style="color:#c9d1d9">4.2 定义：</strong>仓单 = 期货库存-氧化铝-广西，判断交易所库存水平与交割压力。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr50 期货库存-氧化铝-广西(吨/日) —— 交易所库存。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr52 厂内库存(4.4) · wr56 社会库存(4.4)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（FU00086790 期货库存-广西）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>94点(日度)。<br>
<strong style="color:#c9d1d9">4.x 边界：</strong>4.1=交易所库存 · 4.2=仓单(正主=期货库存-广西) · 4.3=社会库存 · 4.4=工厂库存 · 4.5=隐性在途。"""

html = page_html(
    "氧化铝(AO) 4.2 仓单",
    make_crumb("氧化铝", "AO", "4", "库存", "4.2", "仓单", "1", 1),
    "知几",
    h1, "", "", NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 4.2 仓单 · v1（1 图真数据 · 期货库存-广西）· indicators_v1.json v3.82",
    j1,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_42_warehouse_receipts.html", html)
