#!/usr/bin/env python3
"""镍(NI) 4.1 交易所库存子页 · wr数据 · v1 · 3 图真数据

图1 镍库存-中国(正主)：wr241 中国镍库存(月)
图2 镍库存-精炼镍(辅)：wr242 中国精炼镍库存(月)
图3 镍库存-电镀镍(辅)：wr243 中国电镀镍库存(月)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ni41wr_c1", "echart_ni41wr_c2", "echart_ni41wr_c3"]

m_total = load_metric("wr241", code="NI")
m_refined = load_metric("wr242", code="NI")
m_plating = load_metric("wr243", code="NI")

d_total = pairs(m_total)
d_refined = pairs(m_refined)
d_plating = pairs(m_plating)

print("[POINTS] 总库存=%d 精炼镍=%d 电镀镍=%d" % (len(d_total), len(d_refined), len(d_plating)))

h1, j1 = chart_line_t(
    "echart_ni41wr_c1",
    "中国镍库存（4.1 正主）",
    "中国镍库存 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_total), latest(m_total)),
    "#7a8c5b", d_total,
    "什么时候看：4.1 交易所库存的正主图——判断镍整体库存水平。<br>"
    "怎么看：库存上行=供给过剩或需求疲软。库存下行=需求旺盛或供给收缩。"
)

h2, j2 = chart_line_t(
    "echart_ni41wr_c2",
    "精炼镍库存·季节图",
    "中国精炼镍库存 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_refined), latest(m_refined)),
    "#5b98c9", d_refined,
    "什么时候看：精炼镍是主要工业镍品种。<br>"
    "怎么看：精炼镍库存变化反映工业需求与供给平衡。"
)

h3, j3 = chart_line_t(
    "echart_ni41wr_c3",
    "电镀镍库存·季节图",
    "中国电镀镍库存 · 月 · 吨 · %d 点 · 至 %s" % (
        len(d_plating), latest(m_plating)),
    "#e06c75", d_plating,
    "什么时候看：电镀镍用于电镀加工，需求相对稳定。<br>"
    "怎么看：电镀镍库存变化反映电镀行业景气度。"
)

NOTE = """<strong style="color:#c9d1d9">4.1 定义：</strong>交易所库存 = 中国镍库存 + 分品种库存，判断镍整体库存水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr241 中国镍库存(吨/月) —— 总库存。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr242 精炼镍库存 · wr243 电镀镍库存 · wr244 不锈钢镍库存 · wr245 镍铁库存。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01002132 总库存 + ID01002085 精炼镍 + ID01002124 电镀镍）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>总库存80点；精炼镍80点；电镀镍79点(月度)。<br>
<strong style="color:#c9d1d9">4.x 边界：</strong>4.1=交易所库存(正主=总库存) · 4.2=仓单 · 4.3=社会库存 · 4.4=工厂库存 · 4.5=隐性在途。"""

html = page_html(
    "镍(NI) 4.1 交易所库存",
    make_crumb("镍", "NI", "4", "库存", "4.1", "交易所库存", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 镍(NI) 4.1 交易所库存 · v1（3 图真数据 · 总库存 · 精炼镍 · 电镀镍）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ni_41wr_exchange_inventory.html", html)
