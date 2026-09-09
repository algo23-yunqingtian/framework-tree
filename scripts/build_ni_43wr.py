#!/usr/bin/env python3
"""镍(NI) 4.3 社会库存子页 · wr数据 · v1 · 2 图真数据

图1 不锈钢库存-300系热轧(正主)：wr264 不锈钢库存-300系热轧(周)
图2 不锈钢库存-300系冷轧(辅)：wr266 不锈钢库存-300系冷轧(周)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ni43wr_c1", "echart_ni43wr_c2"]

m_hot = load_metric("wr264", code="NI")
m_cold = load_metric("wr266", code="NI")

d_hot = pairs(m_hot)
d_cold = pairs(m_cold)

print("[POINTS] 热轧=%d 冷轧=%d" % (len(d_hot), len(d_cold)))

h1, j1 = chart_line_t(
    "echart_ni43wr_c1",
    "不锈钢库存-300系热轧（4.3 正主）",
    "不锈钢库存-300系热轧 · 周 · 吨 · %d 点 · 至 %s" % (
        len(d_hot), latest(m_hot)),
    "#7a8c5b", d_hot,
    "什么时候看：4.3 社会库存的正主图——判断不锈钢热轧库存水平。<br>"
    "怎么看：库存上行=下游需求疲软或供应过剩。库存下行=需求旺盛或供应收缩。"
)

h2, j2 = chart_line_t(
    "echart_ni43wr_c2",
    "不锈钢库存-300系冷轧·季节图",
    "不锈钢库存-300系冷轧 · 周 · 吨 · %d 点 · 至 %s" % (
        len(d_cold), latest(m_cold)),
    "#5b98c9", d_cold,
    "什么时候看：冷轧库存反映精加工环节库存水平。<br>"
    "怎么看：冷轧库存与热轧库存结合看，判断产业链库存分布。"
)

NOTE = """<strong style="color:#c9d1d9">4.3 定义：</strong>社会库存 = 不锈钢300系热轧/冷轧库存，判断下游库存水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr264 不锈钢库存-300系热轧(吨/周) —— 热轧库存。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr266 不锈钢库存-300系冷轧(吨/周)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01002126 热轧 + ID01002127 冷轧）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>热轧291点；冷轧291点(周度)。<br>
<strong style="color:#c9d1d9">4.x 边界：</strong>4.1=交易所库存 · 4.2=仓单 · 4.3=社会库存(正主=热轧) · 4.4=工厂库存 · 4.5=隐性在途。"""

html = page_html(
    "镍(NI) 4.3 社会库存",
    make_crumb("镍", "NI", "4", "库存", "4.3", "社会库存", "1", 2),
    "知几",
    h1, h2, "", NOTE,
    "有色金属产业指标树 · 镍(NI) 4.3 社会库存 · v1（2 图真数据 · 热轧 · 冷轧）· indicators_v1.json v3.82",
    j1 + "\n" + j2,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ni_43wr_social_inventory.html", html)
