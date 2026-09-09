#!/usr/bin/env python3
"""镍(NI) 2.3 价格子页 · wr数据 · v1 · 3 图真数据

图1 镍价-日(正主)：wr256 镍价(日)
图2 镍价-周(辅)：wr257 镍价(周)
图3 镍只涨(辅)：wr252 镍只涨(日)
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ni23wr_c1", "echart_ni23wr_c2", "echart_ni23wr_c3"]

m_daily = load_metric("wr256", code="NI")
m_weekly = load_metric("wr257", code="NI")
m_only_up = load_metric("wr252", code="NI")

d_daily = pairs(m_daily)
d_weekly = pairs(m_weekly)
d_only_up = pairs(m_only_up)

print("[POINTS] 日=%d 周=%d 只涨=%d" % (len(d_daily), len(d_weekly), len(d_only_up)))

h1, j1 = chart_line_t(
    "echart_ni23wr_c1",
    "镍价（2.3 正主）",
    "镍价(日) · 元/吨 · %d 点 · 至 %s" % (
        len(d_daily), latest(m_daily)),
    "#7a8c5b", d_daily,
    "什么时候看：2.3 海外价格的正主图——判断镍价格基本面。<br>"
    "怎么看：价格上行=镍供应偏紧或需求旺盛。价格下行=供应过剩或需求疲软。"
)

h2, j2 = chart_line_t(
    "echart_ni23wr_c2",
    "镍价-周·季节图",
    "镍价(周) · 元/吨 · %d 点 · 至 %s" % (
        len(d_weekly), latest(m_weekly)),
    "#5b98c9", d_weekly,
    "什么时候看：周度价格反映中期趋势。<br>"
    "怎么看：周度价格与日度价格结合看，判断趋势持续性。"
)

h3, j3 = chart_line_t(
    "echart_ni23wr_c3",
    "镍只涨·季节图",
    "镍只涨(日) · 手 · %d 点 · 至 %s" % (
        len(d_only_up), latest(m_only_up)),
    "#e06c75", d_only_up,
    "什么时候看：镍只涨是镍期货的投机指标，反映多头情绪。<br>"
    "怎么看：只涨上行=多头情绪升温=价格上涨动力增强。"
)

NOTE = """<strong style="color:#c9d1d9">2.3 定义：</strong>海外价格 = 镍价 + 镍只涨，判断镍价格基本面与投机情绪。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr256 镍价(元/吨/日) —— 现货价格基准。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr257 镍价(周) · wr252 镍只涨(手/日)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID00185681 日 + ID00185682 周 + FU00024325 只涨）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>日1661点；周1661点；只涨1616点(日度)。<br>
<strong style="color:#c9d1d9">2.x 边界：</strong>2.1=盘面结构 · 2.2=现货升贴水 · 2.3=海外价格(正主=镍价) · 2.4=价差体系 · 2.5=估值利润 · 2.6=持仓席位。"""

html = page_html(
    "镍(NI) 2.3 价格",
    make_crumb("镍", "NI", "2", "价格信号", "2.3", "海外价格", "1", 3),
    "知几",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 镍(NI) 2.3 价格 · v1（3 图真数据 · 镍价 · 镍价周 · 镍只涨）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ni_23wr_price.html", html)
