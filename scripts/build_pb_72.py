#!/usr/bin/env python3
"""铅(PB) 7.2 日度利润测算子页 · v1 · 3 图全真数据（板块7·成本利润·第2子节点）。

图1 原生铅冶炼利润 vs 白银收益（chart_dual）：j72_smelt_profit 冶炼利润 + j25_ag_revenue 白银收益
    —— 冶炼利润是7.2正主：日度盈亏直接反映冶炼端经营状况；白银收益是利润的核心补偿因子
图2 原生铅冶炼利润季节图（chart_line_t seasonal）：近5年历年线，观察利润季节性规律
图3 再生铅利润 vs 废蓄电池价（chart_dual）：j24_regen_profit 再生利润(辅助) + j25_battery 废蓄电池价
    —— 再生铅利润为2.4正主仅作辅助；废蓄电池价是再生铅成本的直接驱动

数据源：SMM 铅冶炼利润(a10127392, 日) + SMM 白银收益(a10127387, 日) + SMM 再生铅利润(a10016953, 日) + SMM 废蓄电池价(s22731628, 日)。
备用（未入正主）：完全成本曲线(知几无铅专用序列，需外部源)；日度利润分位(需计算衍生指标)。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_72_c1", "echart_72_c2", "echart_72_c3"]

m_profit = load_metric("j72_smelt_profit")
m_ag = load_metric("j25_ag_revenue")
m_regen = load_metric("j24_regen_profit")
m_battery = load_metric("j25_battery")

d_profit = pairs(m_profit)
d_ag = pairs(m_ag)
d_regen = pairs(m_regen)
d_battery = pairs(m_battery)

print("[POINTS] 冶炼利润=%d 白银收益=%d 再生利润=%d 废蓄电池=%d" % (
    len(d_profit), len(d_ag), len(d_regen), len(d_battery)))

# === 图1：原生铅冶炼利润 vs 白银收益 ===
h1, j1 = chart_dual(
    "echart_72_c1",
    "原生铅冶炼利润 vs 白银副产品收益（7.2 正主）",
    "SMM 铅冶炼利润(加工) · 日 · 元/吨 + SMM 白银收益 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (
        len(d_profit), len(d_ag), latest(m_profit)),
    d_profit, "#e06c75", "原生铅冶炼利润", "元/吨",
    d_ag, "#5fb3a1", "白银副产品收益", "元/吨",
    "什么时候看：7.2日度利润测算的正主图——判断原生铅冶炼厂当日盈亏与核心补偿因子。<br>"
    "怎么看：利润转负并加深=冶炼亏损、减产/停产预期强、成本支撑铅价底部；利润高企=开工动力足。"
    "白银收益上行=银价走强=冶炼利润补偿增强；白银收益下行=利润压缩。"
    "最新(2026-08-28)：冶炼利润约1134元(盈利)、白银收益约200元。"
)

# === 图2：原生铅冶炼利润季节图 ===
h2, j2 = chart_line_t(
    "echart_72_c2",
    "原生铅冶炼利润·季节图",
    "SMM 铅冶炼利润(加工) · 日 · 元/吨 · %d 点(2021起) · 至 %s" % (
        len(d_profit), latest(m_profit)),
    "#e06c75", d_profit,
    "什么时候看：判断冶炼利润的月度季节性规律。<br>"
    "怎么看：Q1(春节旺季)利润通常偏高(铅价+TC支撑)，Q2/Q3(淡季)利润压缩；"
    "Q4(备货季)利润回升。若某年全年利润线整体下移=结构性成本上升或需求走弱。"
)

# === 图3：再生铅利润 vs 废蓄电池价 ===
h3, j3 = chart_dual(
    "echart_72_c3",
    "再生铅利润 vs 废蓄电池价（再生端成本验证）",
    "SMM 再生铅利润 · 日 · 元/吨 + SMM 废蓄电池均价 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (
        len(d_regen), len(d_battery), latest(m_regen)),
    d_regen, "#b06a32", "再生铅利润", "元/吨",
    d_battery, "#5b98c9", "废蓄电池均价", "元/吨",
    "什么时候看：判断再生铅冶炼端的盈亏状况与成本驱动——废电瓶是再生铅的直接原料。<br>"
    "怎么看：废蓄电池价上行=再生铅成本抬升=利润压缩=减产风险；废蓄电池价下行=成本缓解=利润修复。"
    "利润持续为负=行业性亏损=中小炼厂减产/停产预期。"
    "最新(2026-08-28)：再生利润约-512元(亏损)、废蓄电池约9275元。注：再生利润=2.4正主仅作辅助。"
)

NOTE = """<strong style="color:#c9d1d9">7.2 定义：</strong>日度利润测算 = 原生铅冶炼利润(日度) + 白银补偿 + 再生铅利润验证，判断冶炼端当日盈亏与减产信号。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>j72_smelt_profit 铅冶炼利润(加工)(元/吨/日) · j25_ag_revenue 白银收益(元/吨/日)。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>j24_regen_profit 再生铅利润(元/吨/日, 2.4正主仅作辅助) · j25_battery 废蓄电池价(元/吨/日)。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>再生铅利润(j24_regen_profit) → 2.4价差体系正主 · 铅精矿TC(j25_tc) → 2.5估值与利润正主 · 完全成本曲线(知几无铅专用序列，入备用库标「待外部源」) · 日度利润分位(需计算衍生指标，不入正主)。<br>
<strong style="color:#c9d1d9">数据源：</strong>SMM 铅冶炼利润(a10127392, 日度1370点/2021起) + SMM 白银收益(a10127387, 日度1370点/2021起) + SMM 再生铅利润(a10016953, 日度1611点/2016起) + SMM 废蓄电池价(s22731628, 日度645点/2023-12起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>冶炼利润/白银1370点(2021-01起)；再生利润1611点(2016-07起)；废蓄电池645点(2023-12起)。<br>
<strong style="color:#c9d1d9">7.x 边界：</strong>7.1=成本曲线·季同步(正主=加工成本) · 7.2=日度利润测算·日同步(正主=冶炼利润) · 7.3=能源/原料成本·月先行(正主=硫酸价)。出口图已在6.3(HS8507)展示。"""

html = page_html(
    "铅(PB) 7.2 日度利润测算",
    make_crumb("铅", "PB", "7", "成本利润", "7.2", "日度利润测算", "1", 3),
    "SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 7.2 日度利润测算 · v1（3 图全真数据 · 冶炼利润vs白银 · 利润季节图 · 再生利润vs废电池）· indicators_v1.json v2.8",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_7_overview.html">← 回板块7总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_72_daily_profit.html", html)
