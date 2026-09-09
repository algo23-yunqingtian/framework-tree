#!/usr/bin/env python3
"""铝(AL) 2.3 价格子页 · wr数据 · v1 · 3 图真数据

图1 LME铝远月月差3-15(正主)：wr20 LME铝远月月差3-15(日)
图2 LME主要仓库注销仓单(辅)：wr16 LME主要仓库注销仓单(日)
图3 LME仓单原产地(辅)：wr17 LME仓单原产地(日)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_al23wr_c1", "echart_al23wr_c2", "echart_al23wr_c3"]

m_spread = load_metric("wr20", code="AL")
m_cancel = load_metric("wr16", code="AL")
m_origin = load_metric("wr17", code="AL")

d_spread = pairs(m_spread)
d_cancel = pairs(m_cancel)
d_origin = pairs(m_origin)

print("[POINTS] 月差=%d 注销仓单=%d 原产地=%d" % (len(d_spread), len(d_cancel), len(d_origin)))

h1, j1 = chart_line_t(
    "echart_al23wr_c1",
    "LME铝远月月差3-15（2.3 正主）",
    "LME铝远月月差3-15 · 日 · 美元/吨 · %d 点 · 至 %s" % (
        len(d_spread), latest(m_spread)),
    "#7a8a9c", d_spread,
    "什么时候看：2.3 海外价格的正主图——月差反映LME铝期限结构。<br>"
    "怎么看：月差上行=远月升水扩大=需求预期向好。月差下行=远月贴水=需求预期走弱。"
)

h2, j2 = chart_line_t(
    "echart_al23wr_c2",
    "LME主要仓库注销仓单·季节图",
    "LME主要仓库注销仓单 · 日 · 吨 · %d 点 · 至 %s" % (
        len(d_cancel), latest(m_cancel)),
    "#5b98c9", d_cancel,
    "什么时候看：注销仓单反映LME铝库存的注销情况。<br>"
    "怎么看：注销仓单上行=库存从仓库转移到注销状态=交割压力增加。"
)

h3, j3 = chart_line_t(
    "echart_al23wr_c3",
    "LME仓单原产地·季节图",
    "LME仓单原产地 · 日 · 吨 · %d 点 · 至 %s" % (
        len(d_origin), latest(m_origin)),
    "#e06c75", d_origin,
    "什么时候看：仓单原产地反映LME铝库存的地区分布。<br>"
    "怎么看：俄铝仓单占比=俄罗斯铝在LME的库存比例，影响供应格局。"
)

NOTE = """<strong style="color:#c9d1d9">2.3 定义：</strong>海外价格 = LME铝月差 + 注销仓单 + 仓单原产地，判断LME铝期限结构与库存分布。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr20 LME铝远月月差3-15(美元/吨/日) —— 期限结构。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr16 LME主要仓库注销仓单 · wr17 LME仓单原产地。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（FU00014801 月差 + FU00014808 注销仓单 + FU00014807 原产地）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>月差1683点；注销仓单1727点；原产地1728点(日度)。<br>
<strong style="color:#c9d1d9">2.x 边界：</strong>2.1=盘面结构 · 2.2=现货升贴水 · 2.3=海外价格(正主=LME月差) · 2.4=月差结构 · 2.5=库存 · 2.6=加工费。"""

html = page_html(
    "铝(AL) 2.3 价格",
    make_crumb("铝", "AL", "2", "价格信号", "2.3", "海外价格", "1", 3),
    "LME",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铝(AL) 2.3 价格 · v1（3 图真数据 · LME月差 · 注销仓单 · 原产地）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("al_23wr_price.html", html)
