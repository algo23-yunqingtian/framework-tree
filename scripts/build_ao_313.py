#!/usr/bin/env python3
"""氧化铝(AO) 3.1.3 国内矿产量子页 · v1 · 1 图真数据

图1 几内亚铝土矿出口(正主)：wr73 几内亚出口-全球主要港口(月) —— 海外矿供应
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao313_c1"]

m_export = load_metric("wr73", code="AO")
d_export = pairs(m_export)

print("[POINTS] 几内亚出口=%d" % len(d_export))

h1, j1 = chart_line_t(
    "echart_ao313_c1",
    "几内亚铝土矿出口（3.1.3 正主）",
    "几内亚出口-全球主要港口 · 月 · 万吨 · %d 点 · 至 %s" % (
        len(d_export), latest(m_export)),
    "#9a6b4f", d_export,
    "什么时候看：3.1.3 国内矿产量的正主图——判断海外矿供应基本面。<br>"
    "怎么看：几内亚出口上行=海外矿供应充裕=进口窗口打开。出口下行=供应收紧=进口窗口关闭。"
    "几内亚是全球最大铝土矿出口国，其出口量直接影响中国氧化铝原料供应。"
)

NOTE = """<strong style="color:#c9d1d9">3.1.3 定义：</strong>国内矿产量 = 几内亚铝土矿出口(海外矿代理)，判断海外矿供应基本面。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr73 几内亚出口-全球主要港口(万吨/月) —— 海外矿供应代理。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr74 港口库存(到港消化节奏)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01201231 几内亚出口）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>263点(月度)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.1=海外矿财报产量 · 3.1.2=分国别总量 · 3.1.3=国内矿产量(正主=几内亚出口) · 3.1.4=矿进口量 · 3.1.5=TC加工费 · 3.2.x=精炼。"""

html = page_html(
    "氧化铝(AO) 3.1.3 国内矿产量",
    make_crumb("氧化铝", "AO", "3", "供给", "3.1.3", "国内矿产量", "1", 1),
    "知几",
    h1, "", "", NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 3.1.3 国内矿产量 · v1（1 图真数据 · 几内亚出口）· indicators_v1.json v3.82",
    j1,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_313_domestic_mine.html", html)
