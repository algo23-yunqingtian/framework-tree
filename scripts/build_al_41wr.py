#!/usr/bin/env python3
"""铝(AL) 4.1 交易所库存子页 · wr数据 · v1 · 3 图真数据

图1 电解铝库存-中国(正主)：wr8 电解铝库存-中国(月)
图2 铝棒库存-中国(辅)：wr9 铝棒库存-中国(月)
图3 铝合金进口量(辅)：wr27 铝合金进口量(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_al41wr_c1", "echart_al41wr_c2", "echart_al41wr_c3"]

m_al = load_metric("wr8", code="AL")
m_rod = load_metric("wr9", code="AL")
m_import = load_metric("wr27", code="AL")

d_al = pairs(m_al)
d_rod = pairs(m_rod)
d_import = pairs(m_import)

print("[POINTS] 电解铝=%d 铝棒=%d 进口=%d" % (len(d_al), len(d_rod), len(d_import)))

h1, j1 = chart_line_t(
    "echart_al41wr_c1",
    "电解铝库存-中国（4.1 正主）",
    "电解铝库存-中国 · 月 · 万吨 · %d 点 · 至 %s" % (
        len(d_al), latest(m_al)),
    "#7a8a9c", d_al,
    "什么时候看：4.1 交易所库存的正主图——判断电解铝整体库存水平。<br>"
    "怎么看：库存上行=供给过剩或需求疲软。库存下行=需求旺盛或供给收缩。"
)

h2, j2 = chart_line_t(
    "echart_al41wr_c2",
    "铝棒库存-中国·季节图",
    "铝棒库存-中国 · 月 · 万吨 · %d 点 · 至 %s" % (
        len(d_rod), latest(m_rod)),
    "#5b98c9", d_rod,
    "什么时候看：铝棒是电解铝主要加工品之一。<br>"
    "怎么看：铝棒库存变化反映下游加工需求与供给平衡。"
)

h3, j3 = chart_line_t(
    "echart_al41wr_c3",
    "铝合金进口量·季节图",
    "铝合金进口量 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_import), latest(m_import)),
    "#e06c75", d_import,
    "什么时候看：铝合金进口反映国内铝合金供给缺口。<br>"
    "怎么看：进口上行=国内供给不足。进口下行=国内供给充裕。"
)

NOTE = """<strong style="color:#c9d1d9">4.1 定义：</strong>交易所库存 = 电解铝库存 + 铝棒库存 + 铝合金进口，判断库存水平与进口依赖度。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr8 电解铝库存-中国(万吨/月) —— 总库存。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr9 铝棒库存 · wr27 铝合金进口量 · wr5 未锻轧铝合金出口。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01001760 电解铝 + ID01029971 铝棒 + ID01114281 进口）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>电解铝336点；铝棒343点；进口79点(月度)。<br>
<strong style="color:#c9d1d9">4.x 边界：</strong>4.1=交易所库存(正主=电解铝) · 4.2=仓单 · 4.3=社会库存 · 4.4=工厂库存 · 4.5=隐性在途。"""

html = page_html(
    "铝(AL) 4.1 交易所库存",
    make_crumb("铝", "AL", "4", "库存", "4.1", "交易所库存", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铝(AL) 4.1 交易所库存 · v1（3 图真数据 · 电解铝 · 铝棒 · 进口）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("al_41wr_exchange_inventory.html", html)
