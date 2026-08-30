#!/usr/bin/env python3
"""铅(PB) 7.3 能源/原料成本子页 · v1 · 3 图全真数据（板块7·成本利润·第3子节点）。

图1 硫酸价 vs 铅冶炼利润（chart_dual）：j51_h2so4 硫酸价(正主) + j72_smelt_profit 冶炼利润(辅助)
    —— 硫酸是铅冶炼的核心副产品(伴生)，价格波动直接影响冶炼利润补偿
图2 硫酸价季节图（chart_line_t seasonal）：近5年历年线，观察硫酸季节性规律
图3 进口TC vs 国产TC（chart_dual）：j73_imp_tc 进口TC + j25_tc 国产TC
    —— 进口TC vs 国产TC的价差反映国际矿端与国内矿端的供需分化

数据源：SMM 硫酸价(a10127388, 日) + SMM 铅冶炼利润(a10127392, 日) + SMM 进口TC(a10021355, 日) + SMM 国产TC(a10127385, 日)。
备用（未入正主）：广西电解铝电价(a12762872, 月)——铅冶炼电力成本代理指标，但非铅专用数据。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_73_c1", "echart_73_c2", "echart_73_c3"]

m_h2so4 = load_metric("j51_h2so4")
m_profit = load_metric("j72_smelt_profit")
m_imp_tc = load_metric("j73_imp_tc")
m_tc = load_metric("j25_tc")

d_h2so4 = pairs(m_h2so4)
d_profit = pairs(m_profit)
d_imp_tc = pairs(m_imp_tc)
d_tc = pairs(m_tc)

print("[POINTS] 硫酸价=%d 冶炼利润=%d 进口TC=%d 国产TC=%d" % (
    len(d_h2so4), len(d_profit), len(d_imp_tc), len(d_tc)))

# === 图1：硫酸价 vs 铅冶炼利润 ===
h1, j1 = chart_dual(
    "echart_73_c1",
    "硫酸价 vs 铅冶炼利润（7.3 正主）",
    "SMM 硫酸价格 · 日 · 元/吨 + SMM 铅冶炼利润 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (
        len(d_h2so4), len(d_profit), latest(m_h2so4)),
    d_h2so4, "#b06a32", "硫酸价", "元/吨",
    d_profit, "#e06c75", "冶炼利润", "元/吨",
    "什么时候看：7.3能源/原料成本的正主图——判断副产品(硫酸)对冶炼利润的补偿力度。<br>"
    "怎么看：硫酸价上行=副产品收益增强=冶炼利润补偿增加=冶炼端有动力维持开工。"
    "硫酸价下行=副产品收益减弱=冶炼利润压缩=减产风险。"
    "两条线正相关=硫酸对冶炼利润的补偿效应显著。"
    "最新(2026-08-28)：硫酸价约1475元(高位)、冶炼利润约1134元(盈利)。注：硫酸价=5.1备用库，7.3提为正主。"
)

# === 图2：硫酸价季节图 ===
h2, j2 = chart_line_t(
    "echart_73_c2",
    "硫酸价·季节图",
    "SMM 硫酸价格 · 日 · 元/吨 · %d 点(2021起) · 至 %s" % (
        len(d_h2so4), latest(m_h2so4)),
    "#b06a32", d_h2so4,
    "什么时候看：判断硫酸价的月度季节性规律——硫酸是铅冶炼的伴生副产品，价格季节性影响冶炼成本结构。<br>"
    "怎么看：Q2(春耕化肥季)硫酸需求旺=价格偏高；Q4(冬季)需求回落=价格偏弱。"
    "若某年硫酸价线整体抬升=磷化工/化肥需求结构性增长=副产品收益长期改善。"
)

# === 图3：进口TC vs 国产TC ===
h3, j3 = chart_dual(
    "echart_73_c3",
    "进口TC vs 国产TC（矿端供需分化）",
    "SMM 进口铅精矿加工费 · 日 · 美元/吨 + SMM 国产TC · 日 · 元/金属吨 · %d/%d 点 · 至 %s" % (
        len(d_imp_tc), len(d_tc), latest(m_imp_tc)),
    d_imp_tc, "#5b98c9", "进口TC", "美元/吨",
    d_tc, "#5fb3a1", "国产TC", "元/金属吨",
    "什么时候看：判断国际矿端与国内矿端的供需分化——进口TC反映全球铅精矿供应，国产TC反映国内矿端。<br>"
    "怎么看：进口TC为负=全球铅精矿极度短缺=进口窗口关闭=国内原料供应收紧。"
    "国产TC下行=国内矿端偏紧=原生冶炼原料成本上升。"
    "两条线同向下行=全球性矿端短缺；背离=国内矿端供应相对宽松。"
    "最新(2026-08-27)：进口TC约-170美元(极度短缺)、国产TC约150元(低位)。"
)

NOTE = """<strong style="color:#c9d1d9">7.3 定义：</strong>能源/原料成本 = 硫酸副产品收益(月先行) + 进口vs国产TC矿端分化，判断成本端先行信号与原料供应趋势。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>j51_h2so4 硫酸价(元/吨/日, 5.1备用库→7.3正主) · j73_imp_tc 进口TC(美元/吨/日)。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>j72_smelt_profit 铅冶炼利润(元/吨/日, 7.2正主仅作辅助) · j25_tc 国产TC(元/金属吨/日, 2.5正主仅作辅助) · j73_elec_price 广西电解铝电价(元/kWh/月, 电力成本代理指标, 未入正主)。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>铅精矿TC(j25_tc) → 2.5估值与利润正主 · 铅锭社库(i18) → 4.3社会库存正主，不入7.x · 环保投入成本(知几无序列，入备用库标「待外部源」) · 铅精矿含金银计价系数(2026-08上线，需持续观察)。<br>
<strong style="color:#c9d1d9">数据源：</strong>SMM 硫酸价格(a10127388, 日度1370点/2021起) + SMM 铅冶炼利润(a10127392, 日度1370点/2021起) + SMM 进口TC(a10021355, 日度1570点/2008起) + SMM 国产TC(a10127385, 日度1370点/2021起) + SMM 广西电解铝电价(a12762872, 月度43点/2023起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>硫酸/冶炼利润/国产TC各1370点(2021-01起)；进口TC 1570点(2008-01起)；广西电解铝电价43点(2023-01起)。<br>
<strong style="color:#c9d1d9">7.x 边界：</strong>7.1=成本曲线·季同步(正主=加工成本) · 7.2=日度利润测算·日同步(正主=冶炼利润) · 7.3=能源/原料成本·月先行(正主=硫酸价+进口TC)。出口图已在6.3(HS8507)展示，7.x只做国内冶炼成本。"""

html = page_html(
    "铅(PB) 7.3 能源/原料成本",
    make_crumb("铅", "PB", "7", "成本利润", "7.3", "能源/原料成本", "1", 3),
    "SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 7.3 能源/原料成本 · v1（3 图全真数据 · 硫酸vs利润 · 硫酸季节图 · 进口vs国产TC）· indicators_v1.json v2.8",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_7_overview.html">← 回板块7总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_73_energy_cost.html", html)
