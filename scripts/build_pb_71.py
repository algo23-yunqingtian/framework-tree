#!/usr/bin/env python3
"""铅(PB) 7.1 成本曲线与分位子页 · v1 · 3 图全真数据（板块7·成本利润·第1子节点）。

图1 铅冶炼加工成本 vs 白银副产品收益（chart_dual）：j25_smelt_cost 加工成本 + j25_ag_revenue 白银收益
    —— 成本曲线的两大组件：加工成本=冶炼端直接支出，白银收益=副产品抵扣，净成本≈加工成本-白银收益
图2 铅冶炼加工成本季节图（chart_line_t seasonal）：近5年历年线，观察成本季节性规律
图3 铅精矿TC vs 冶炼利润（chart_dual）：j25_tc 国产TC(辅助) + j72_smelt_profit 冶炼利润(辅助)
    —— TC为矿端原料成本驱动，冶炼利润反映成本-价格综合关系

数据源：SMM 铅冶炼加工成本(a10127391) + SMM 白银收益(a10127387) + SMM 国产TC(a10127385) + SMM 铅冶炼利润(a10127392)。
备用（未入正主）：完全成本/C1现金成本（知几无铅专用序列，需安泰科/长江有色外部源）。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_71_c1", "echart_71_c2", "echart_71_c3"]

m_cost = load_metric("j25_smelt_cost")
m_ag = load_metric("j25_ag_revenue")
m_tc = load_metric("j25_tc")
m_profit = load_metric("j72_smelt_profit")

d_cost = pairs(m_cost)
d_ag = pairs(m_ag)
d_tc = pairs(m_tc)
d_profit = pairs(m_profit)

print("[POINTS] 加工成本=%d 白银收益=%d TC=%d 冶炼利润=%d" % (
    len(d_cost), len(d_ag), len(d_tc), len(d_profit)))

# === 图1：铅冶炼加工成本 vs 白银副产品收益 ===
h1, j1 = chart_dual(
    "echart_71_c1",
    "铅冶炼加工成本 vs 白银副产品收益（7.1 正主）",
    "SMM 铅冶炼加工成本 · 日 · 元/吨 + SMM 白银收益 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (
        len(d_cost), len(d_ag), latest(m_cost)),
    d_cost, "#b06a32", "铅冶炼加工成本", "元/吨",
    d_ag, "#5fb3a1", "白银副产品收益", "元/吨",
    "什么时候看：判断原生铅冶炼成本曲线的两个核心组件——加工成本(支出)与白银收益(抵扣)。<br>"
    "怎么看：净冶炼成本≈加工成本-白银收益。加工成本上行+白银收益下行=成本曲线整体上移=成本支撑增强。"
    "白银收益下行=银价走弱=冶炼利润压缩。最新(2026-08-28)：加工成本约1000元、白银收益约200元。"
)

# === 图2：铅冶炼加工成本季节图 ===
h2, j2 = chart_line_t(
    "echart_71_c2",
    "铅冶炼加工成本·季节图",
    "SMM 铅冶炼加工成本 · 日 · 元/吨 · %d 点(2021起) · 至 %s" % (
        len(d_cost), latest(m_cost)),
    "#b06a32", d_cost,
    "什么时候看：判断加工成本的月度季节性规律。<br>"
    "怎么看：加工成本与铅价、银价联动，Q1(春节后补库)+Q4(旺季备货)通常偏高，Q2/Q3(淡季)偏低。"
    "若某年成本线整体抬升=上游原料成本结构性上涨=成本支撑位上移。"
)

# === 图3：铅精矿TC vs 冶炼利润 ===
h3, j3 = chart_dual(
    "echart_71_c3",
    "铅精矿TC vs 冶炼利润（矿端紧松+成本传导）",
    "SMM 国产TC · 日 · 元/金属吨 + SMM 铅冶炼利润 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (
        len(d_tc), len(d_profit), latest(m_tc)),
    d_tc, "#5b98c9", "国产TC", "元/金属吨",
    d_profit, "#e06c75", "冶炼利润", "元/吨",
    "什么时候看：判断矿端原料成本压力与冶炼利润的传导关系。<br>"
    "怎么看：TC下行=矿端偏紧=原生冶炼原料成本上升=利润承压。TC与利润正相关=矿端成本向下游传导顺畅；"
    "背离(TC降但利润不降)=副产品收益(白银/硫酸)补偿了成本上升。"
    "最新(2026-08-28)：国产TC约150元(低位)、冶炼利润约1134元。注：TC=2.5正主仅作辅助。"
)

NOTE = """<strong style="color:#c9d1d9">7.1 定义：</strong>成本曲线与分位 = 原生铅冶炼成本的核心组件(加工成本+白银收益)及其季节性规律，判断成本支撑位与利润传导。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>j25_smelt_cost 铅冶炼加工成本(元/吨/日) · j25_ag_revenue 白银收益(元/吨/日)。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>j25_tc 国产TC(元/金属吨/日, 2.5正主仅作辅助) · j72_smelt_profit 铅冶炼利润(元/吨/日, 7.2正主仅作辅助交叉)。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>铅精矿TC(j25_tc) → 2.5估值与利润正主 · 再生铅利润(j24_regen_profit) → 2.4价差体系正主 · 铅锭社库(i18) → 4.3社会库存正主，不入7.x · 完全成本/C1现金成本(知几无铅专用序列，入备用库标「待外部源」)。<br>
<strong style="color:#c9d1d9">数据源：</strong>SMM 铅冶炼加工成本(a10127391, 日度1370点/2021起) + SMM 白银收益(a10127387, 日度1370点/2021起) + SMM 国产TC(a10127385, 日度1370点/2021起) + SMM 铅冶炼利润(a10127392, 日度1370点/2021起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>加工成本/白银/TC/冶炼利润各1370点(2021-01起)。知几无铅C1现金成本/完全成本直接序列——需安泰科/长江有色外部源补充。<br>
<strong style="color:#c9d1d9">7.x 边界：</strong>7.1=成本曲线·季同步(正主=加工成本) · 7.2=日度利润测算·日同步(正主=冶炼利润) · 7.3=能源/原料成本·月先行(正主=硫酸价)。出口图已在6.3(HS8507)展示，7.x只做国内冶炼成本。"""

html = page_html(
    "铅(PB) 7.1 成本曲线与分位",
    make_crumb("铅", "PB", "7", "成本利润", "7.1", "成本曲线与分位", "1", 3),
    "SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 7.1 成本曲线与分位 · v1（3 图全真数据 · 加工成本vs白银收益 · 成本季节图 · TCvs利润）· indicators_v1.json v2.8",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_7_overview.html">← 回板块7总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_71_cost_curve.html", html)
