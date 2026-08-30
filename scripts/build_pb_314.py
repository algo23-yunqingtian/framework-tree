#!/usr/bin/env python3
"""铅(PB) 3.1.4 矿进口量与分国别子页 · v1 · 3 图全真数据（板块3·供给·第4子节点）。

图1 海关铅精矿进口量时序（chart_line_t）：i40 中国海关铅精矿进口量(月) —— 矿端进口正主
图2 SMM铅精矿净进口量（chart_line_t）：j314_net_imp SMM铅精矿净进口量(月) —— 精炼口径进口
图3 进口 vs 到港节奏（chart_dual）：i40 海关进口量 + i16 防城到港 —— 进口报关 vs 实际到港的时间差

数据源：中国海关铅精矿进口量(a10017055, 月) + SMM 铅精矿净进口量(a12871183, 月) + SMM 铅矿到港防城(a10127618, 月)。
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, write_html, make_crumb)

CIDS = ["echart_314_c1", "echart_314_c2", "echart_314_c3"]

m_imp = load_metric("i40")
m_net = load_metric("j314_net_imp")
m_port = load_metric("i16")

d_imp = pairs(m_imp)
d_net = pairs(m_net)
d_port = pairs(m_port)

print("[POINTS] 海关进口=%d 净进口=%d 到港防城=%d" % (
    len(d_imp), len(d_net), len(d_port)))

# === 图1：海关铅精矿进口量 ===
h1, j1 = chart_line_t(
    "echart_314_c1",
    "海关铅精矿进口量（3.1.4 正主）",
    "中国海关 铅精矿进口量 · 月 · 吨 · %d 点(2018起) · 至 %s" % (
        len(d_imp), latest(m_imp)),
    "#5b98c9", d_imp,
    "什么时候看：3.1.4 矿进口量的正主图——海关口径是矿端进口最权威的统计。<br>"
    "怎么看：海关进口量上行=矿端进口充裕=冶炼厂原料供应改善=冶炼端有动力维持开工。"
    "进口量下行=矿端进口收紧=冶炼厂原料供应偏紧=减产风险。"
    "海关数据滞后约20天,反映上月实际进口情况。"
)

# === 图2：SMM铅精矿净进口量 ===
h2, j2 = chart_line_t(
    "echart_314_c2",
    "SMM铅精矿净进口量·季节图",
    "SMM 铅精矿净进口量(实物吨) · 月 · 万实物吨 · %d 点(2024起) · 至 %s" % (
        len(d_net), latest(m_net)),
    "#7a8c5b", d_net,
    "什么时候看：判断SMM口径的铅精矿净进口量——净进口=进口-出口,反映实际净流入。<br>"
    "怎么看：净进口量上行=矿端净流入增加=冶炼端原料充裕。"
    "净进口量下行=矿端净流入减少=冶炼端原料偏紧。"
    "与海关数据对比：SMM口径通常略高于海关(含海关未统计的灰色通道)。"
)

# === 图3：进口 vs 到港节奏 ===
h3, j3 = chart_dual(
    "echart_314_c3",
    "海关进口 vs 防城到港（进口报关 vs 实际到港）",
    "中国海关 铅精矿进口量 · 月 · 吨 + SMM 铅矿到港-防城港 · 月 · 万吨 · %d/%d 点 · 至 %s" % (
        len(d_imp), len(d_port), latest(m_imp)),
    d_imp, "#5b98c9", "海关进口", "吨",
    d_port, "#e06c75", "防城到港", "万吨",
    "什么时候看：判断进口报关与实际到港的时间差——海关数据是报关口径,防城到港是实际货物抵达港口。<br>"
    "怎么看：海关进口上行=报关量增加=后续到港预期增加(滞后1-2月)。"
    "防城到港上行=实际货物抵达港口=冶炼厂可立即消耗。"
    "海关进口先行于到港1-2个月,是到港的领先指标。"
)

NOTE = """<strong style="color:#c9d1d9">3.1.4 定义：</strong>矿进口量与分国别 = 海关铅精矿进口量(正主) + SMM净进口量 + 进口vs到港节奏,判断矿端进口基本面与到货时间差。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>i40 中国海关铅精矿进口量(吨/月, 6.1原料进口正主) + j314_net_imp SMM铅精矿净进口量(万实物吨/月)。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>i16 铅矿到港防城(万吨/月, 294点)。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>海外矿财报产量 → 3.1.1正主 · 海外矿分国别 → 3.1.2正主 · 国内矿产量 → 3.1.3正主 · TC加工费 → 3.1.5正主。<br>
<strong style="color:#c9d1d9">数据源：</strong>中国海关铅精矿进口量(a10017055, 月度103点/2018起) + SMM 铅精矿净进口量(a12871183, 月度31点/2024起) + SMM 铅矿到港防城(a10127618, 月度294点/2019起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>海关进口103点；净进口31点；防城到港294点。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.1=海外矿财报产量 · 3.1.2=分国别总量 · 3.1.3=国内矿产量 · 3.1.4=矿进口量 · 3.1.5=TC加工费 · 3.2.1=精炼产量 · 3.2.2=开工率检修 · 3.2.3=再生供应(已上线) · 3.2.4=冶炼利润供应弹性。"""

html = page_html(
    "铅(PB) 3.1.4 矿进口量与分国别",
    make_crumb("铅", "PB", "3", "供给", "3.1.4", "矿进口量与分国别", "1", 3),
    "海关/SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 3.1.4 矿进口量与分国别 · v1（3 图全真数据 · 海关进口量 · 净进口季节图 · 进口vs到港）· indicators_v1.json v3.1",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_3_overview.html">← 回板块3总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_314_mine_import.html", html)
