#!/usr/bin/env python3
"""碳酸锂(LC) 6.1 进出口子页 · wr数据 · v1 · 3 图真数据

图1 碳酸锂进口-中国(正主)：wr141 碳酸锂进口-中国(月)
图2 碳酸锂出口-全球(辅)：wr142 碳酸锂出口-全球(月)
图3 碳酸锂产量-全球(辅)：wr143 碳酸锂产量-全球(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_lc61wr_c1", "echart_lc61wr_c2", "echart_lc61wr_c3"]

m_import = load_metric("wr141", code="LC")
m_export = load_metric("wr142", code="LC")
m_global = load_metric("wr143", code="LC")

d_import = pairs(m_import)
d_export = pairs(m_export)
d_global = pairs(m_global)

print("[POINTS] 进口=%d 出口=%d 全球=%d" % (len(d_import), len(d_export), len(d_global)))

h1, j1 = chart_line_t(
    "echart_lc61wr_c1",
    "碳酸锂进口-中国（6.1 正主）",
    "碳酸锂进口-中国 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_import), latest(m_import)),
    "#4f8a7a", d_import,
    "什么时候看：6.1 进出口的正主图——判断中国碳酸锂进口依赖度。<br>"
    "怎么看：进口上行=国内供给不足=进口依赖增加。进口下行=国内供给充裕=进口依赖减少。"
)

h2, j2 = chart_line_t(
    "echart_lc61wr_c2",
    "碳酸锂出口-全球·季节图",
    "碳酸锂出口-全球 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_export), latest(m_export)),
    "#5b98c9", d_export,
    "什么时候看：全球出口反映碳酸锂国际贸易格局。<br>"
    "怎么看：出口上行=全球需求旺盛。出口下行=全球需求疲软。"
)

h3, j3 = chart_line_t(
    "echart_lc61wr_c3",
    "碳酸锂产量-全球·季节图",
    "碳酸锂产量-全球 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_global), latest(m_global)),
    "#e06c75", d_global,
    "什么时候看：全球产量反映碳酸锂整体供给水平。<br>"
    "怎么看：全球产量上行=供给增加。全球产量下行=供给收缩。"
)

NOTE = """<strong style="color:#c9d1d9">6.1 定义：</strong>进出口 = 碳酸锂进口-中国 + 全球出口 + 全球产量，判断国际贸易格局。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr141 碳酸锂进口-中国(吨/月) —— 进口依赖度。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr142 全球出口 · wr143 全球产量。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01380154 进口 + ID01380155 出口 + ID01380156 全球产量）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>进口43点；出口31点；全球产量43点(月度)。<br>
<strong style="color:#c9d1d9">6.x 边界：</strong>6.1=进出口(正主=中国进口) · 6.2=精炼进出口 · 6.3=制品出口 · 6.4=全球化布局。"""

html = page_html(
    "碳酸锂(LC) 6.1 进出口",
    make_crumb("碳酸锂", "LC", "6", "进出口", "6.1", "进出口", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 碳酸锂(LC) 6.1 进出口 · v1（3 图真数据 · 中国进口 · 全球出口 · 全球产量）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("li_61wr_trade.html", html)
