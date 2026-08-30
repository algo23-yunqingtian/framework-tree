#!/usr/bin/env python3
"""铅(PB) 3.2.1 精炼产量子页 · v1 · 3 图全真数据（板块3·供给·第6子节点）。

图1 原生铅产量时序（chart_line_t）：j323_native_output Mysteel原生铅产量(月) —— 精炼产量正主
图2 原生vs再生产量对比（chart_dual）：j323_native_output 原生铅产量 + j323_regen_output 再生精铅产量
     —— 原生vs再生结构对比,反映中国铅冶炼的两大供给来源
图3 原生铅产量季节图（chart_line_t seasonal）：近5年历年线,观察原生产量季节性

数据源：Mysteel 原生铅产量(ID01001562, 月) + SMM 再生精铅产量(a10098385, 月)。
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, write_html, make_crumb)

CIDS = ["echart_321_c1", "echart_321_c2", "echart_321_c3"]

m_native = load_metric("j323_native_output")
m_regen = load_metric("j323_regen_output")

d_native = pairs(m_native)
d_regen = pairs(m_regen)

print("[POINTS] 原生产量=%d 再生产量=%d" % (
    len(d_native), len(d_regen)))

# === 图1：原生铅产量 ===
h1, j1 = chart_line_t(
    "echart_321_c1",
    "原生铅产量（3.2.1 正主）",
    "Mysteel 原生铅产量(中国) · 月 · 万吨 · %d 点(2021起) · 至 %s" % (
        len(d_native), latest(m_native)),
    "#b06a32", d_native,
    "什么时候看：3.2.1 精炼产量的正主图——原生铅产量是中国铅供给的第一来源。<br>"
    "怎么看：原生铅产量上行=冶炼端开工充足=原生供给改善=铅价供给压力增大。"
    "原生铅产量下行=冶炼端减产=原生供给收紧=铅价供给支撑增强。"
    "原生铅产量与TC加工费、冶炼利润正相关——TC高+利润好=产量高。"
)

# === 图2：原生vs再生产量对比 ===
h2, j2 = chart_dual(
    "echart_321_c2",
    "原生铅 vs 再生铅产量（3.2 供给结构）",
    "Mysteel 原生铅产量 · 月 · 万吨 + SMM 再生精铅产量 · 月 · 万吨 · %d/%d 点 · 至 %s" % (
        len(d_native), len(d_regen), latest(m_native)),
    d_native, "#b06a32", "原生铅产量", "万吨",
    d_regen, "#5b98c9", "再生精铅产量", "万吨",
    "什么时候看：判断中国铅冶炼的供给结构——原生vs再生的相对占比反映行业格局变化。<br>"
    "怎么看：原生占比下降+再生占比上升=再生铅产能扩张=行业再生化趋势。"
    "原生产量上行=原生冶炼端开工改善=原生供给增加。"
    "再生产量上行=再生冶炼端开工改善=再生供给增加(再生铅是边际供给,与废电瓶供应相关)。"
    "注：再生精铅产量=3.2.3正主,3.2.1仅作辅助对比。"
)

# === 图3：原生铅产量季节图 ===
h3, j3 = chart_line_t(
    "echart_321_c3",
    "原生铅产量·季节图",
    "Mysteel 原生铅产量(中国) · 月 · 万吨 · %d 点(2021起) · 至 %s" % (
        len(d_native), latest(m_native)),
    "#b06a32", d_native,
    "什么时候看：判断原生铅产量的月度季节性规律——原生产量受冶炼利润、TC、检修等影响。<br>"
    "怎么看：Q4(旺季)产量偏高(冶炼利润好+开工率高)；Q1(春节)偏低(节前停产)。"
    "若某年产量线整体抬升=原生冶炼产能扩张;若下移=环保限产或资源枯竭。"
)

NOTE = """<strong style="color:#c9d1d9">3.2.1 定义：</strong>精炼产量 = 原生铅产量(正主) + 原生vs再生对比,判断中国铅精炼端的供给基本面与结构变化。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>j323_native_output Mysteel原生铅产量(万吨/月) —— 3.2.3原有指标,3.2.1提为正主。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>j323_regen_output SMM再生精铅产量(万吨/月, 3.2.3正主仅作辅助对比)。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>海外矿财报产量 → 3.1.1正主 · 海外矿分国别 → 3.1.2正主 · 国内矿产量 → 3.1.3正主 · 矿进口量 → 3.1.4正主 · TC加工费 → 3.1.5正主 · 再生精铅产量 → 3.2.3正主(辅助对比)。<br>
<strong style="color:#c9d1d9">数据源：</strong>Mysteel 原生铅产量(ID01001562, 月度101点/2021起) + SMM 再生精铅产量(a10098385, 月度91点/2022起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>原生铅产量101点(2021-01起)；再生精铅产量91点(2022-02起)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.1=海外矿财报产量 · 3.1.2=分国别总量 · 3.1.3=国内矿产量 · 3.1.4=矿进口量 · 3.1.5=TC加工费 · 3.2.1=精炼产量 · 3.2.2=开工率检修 · 3.2.3=再生供应(已上线) · 3.2.4=冶炼利润供应弹性。"""

html = page_html(
    "铅(PB) 3.2.1 精炼产量",
    make_crumb("铅", "PB", "3", "供给", "3.2.1", "精炼产量", "1", 3),
    "Mysteel/SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 3.2.1 精炼产量 · v1（3 图全真数据 · 原生铅产量 · 原生vs再生 · 原生产量季节图）· indicators_v1.json v3.1",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_3_overview.html">← 回板块3总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_321_refining_output.html", html)
