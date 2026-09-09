#!/usr/bin/env python3
"""氧化铝(AO) 3.2.1 精炼产量子页 · v1 · 2 图真数据

图1 氧化铝建成产能(正主)：wr28 氧化铝建成产能(月) —— 产能上限
图2 氧化铝产量-河南(辅)：wr32 氧化铝产量-河南(月) —— 主产区实际产量
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao321_c1", "echart_ao321_c2"]

m_cap = load_metric("wr28", code="AO")
m_prod = load_metric("wr32", code="AO")

d_cap = pairs(m_cap)
d_prod = pairs(m_prod)

print("[POINTS] 产能=%d 产量河南=%d" % (len(d_cap), len(d_prod)))

h1, j1 = chart_line_t(
    "echart_ao321_c1",
    "氧化铝建成产能（3.2.1 正主）",
    "氧化铝建成产能 · 月 · 万吨 · %d 点 · 至 %s" % (
        len(d_cap), latest(m_cap)),
    "#9a6b4f", d_cap,
    "什么时候看：3.2.1 精炼产量的正主图——判断氧化铝行业产能上限与扩张趋势。<br>"
    "怎么看：产能上行=新产能投放=供给扩张=价格承压。产能下行=产能退出=供给收缩。"
    "与产量结合看：产能-产量=闲置产能，闲置率高=行业供过于求。"
)

h2, j2 = chart_line_t(
    "echart_ao321_c2",
    "氧化铝产量-河南·季节图",
    "氧化铝产量-河南 · 月 · 万吨 · %d 点 · 至 %s" % (
        len(d_prod), latest(m_prod)),
    "#5b98c9", d_prod,
    "什么时候看：河南是中国氧化铝主产区之一，产量反映实际开工水平。<br>"
    "怎么看：产量上行=开工率提升=供给增加。产量下行=减产或检修=供给收缩。"
)

NOTE = """<strong style="color:#c9d1d9">3.2.1 定义：</strong>精炼产量 = 氧化铝建成产能 + 分地区实际产量，判断产能上限与实际开工水平。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr28 氧化铝建成产能(万吨/月) —— 产能上限。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr32 氧化铝产量-河南(万吨/月) · wr34/wr35 三网均价(价格端)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01001835 建成产能 + ID01001748 河南产量）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>产能80点；河南产量80点(月度)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.x=矿端 · 3.2.1=精炼产量(正主=建成产能) · 3.2.2=开工率 · 3.2.3=再生供应 · 3.2.4=冶炼利润弹性。"""

html = page_html(
    "氧化铝(AO) 3.2.1 精炼产量",
    make_crumb("氧化铝", "AO", "3", "供给", "3.2.1", "精炼产量", "1", 2),
    "知几",
    h1, h2, "", NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 3.2.1 精炼产量 · v1（2 图真数据 · 建成产能 · 河南产量）· indicators_v1.json v3.82",
    j1 + "\n" + j2,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_321_production.html", html)
