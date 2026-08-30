#!/usr/bin/env python3
"""铅(PB) 3.2.4 冶炼利润→供应弹性子页 · v1 · 3 图全真数据（板块3·供给·第9子节点）。

图1 铅锭-再生精铅价差（chart_line_t）：j324_primary_spread Mysteel铅锭-再生精铅价差(日) —— 供应弹性正主
图2 再生铅炉型利润对比（chart_dual）：j324_regen_profit_refl 反射炉利润 + j324_regen_profit_bof 富氧侧吹炉利润
     —— 再生铅两大炉型的利润对比,反映再生冶炼端的供给弹性
图3 再生铅反射炉利润季节图（chart_line_t seasonal）：近5年历年线,观察再生利润季节性

数据源：Mysteel 铅锭-再生精铅价差(ID01501478, 日) + Mysteel 再生铅反射炉利润(ID01167269, 日) + Mysteel 再生铅富氧侧吹炉利润(ID01167270, 日)。
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, write_html, make_crumb)

CIDS = ["echart_324_c1", "echart_324_c2", "echart_324_c3"]

m_spread = load_metric("j324_primary_spread")
m_refl = load_metric("j324_regen_profit_refl")
m_bof = load_metric("j324_regen_profit_bof")

d_spread = pairs(m_spread)
d_refl = pairs(m_refl)
d_bof = pairs(m_bof)

print("[POINTS] 精废价差=%d 反射炉利润=%d 富氧炉利润=%d" % (
    len(d_spread), len(d_refl), len(d_bof)))

# === 图1：铅锭-再生精铅价差 ===
h1, j1 = chart_line_t(
    "echart_324_c1",
    "铅锭-再生精铅价差（3.2.4 正主）",
    "Mysteel 铅锭-再生精铅价差 · 日 · 元/吨 · %d 点(2019起) · 至 %s" % (
        len(d_spread), latest(m_spread)),
    "#e06c75", d_spread,
    "什么时候看：3.2.4 冶炼利润→供应弹性的正主图——铅锭与再生精铅的价差是再生铅供给弹性的核心驱动。<br>"
    "怎么看：价差为正(铅锭>再生精铅)=再生铅利润好=再生冶炼端开工改善=再生供给增加=供应弹性正向。"
    "价差为负(再生精铅>铅锭)=再生铅亏损=再生冶炼端减产=再生供给收紧=供应弹性负向。"
    "价差为正且扩大=再生供给扩张预期强;价差为负且加深=再生供给收缩预期强。"
    "注：j24_refine_spread(2.4正主,精废价差)与j324_primary_spread口径不同——前者为现货价差,后者为铅锭vs再生精铅价差。"
)

# === 图2：再生铅炉型利润对比 ===
h2, j2 = chart_dual(
    "echart_324_c2",
    "再生铅炉型利润对比（反射炉 vs 富氧侧吹炉）",
    "Mysteel 再生铅反射炉利润 · 日 · 元/吨 + Mysteel 再生铅富氧侧吹炉利润 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (
        len(d_refl), len(d_bof), latest(m_refl)),
    d_refl, "#b06a32", "反射炉利润", "元/吨",
    d_bof, "#5b98c9", "富氧侧吹炉利润", "元/吨",
    "什么时候看：判断再生铅两大炉型的利润分化——反射炉和富氧侧吹炉是再生铅的主要冶炼工艺,利润差异反映技术路线的竞争力。<br>"
    "怎么看：反射炉利润>富氧炉=传统工艺利润更高=反射炉产能开工更有动力。"
    "富氧炉利润>反射炉=新工艺利润更高=富氧侧吹炉产能开工更有动力。"
    "两条线均为负=再生铅全线亏损=再生供给全面收缩=铅价供给支撑增强。"
    "两条线均为正=再生铅全线盈利=再生供给全面扩张=铅价供给压力增大。"
)

# === 图3：再生铅反射炉利润季节图 ===
h3, j3 = chart_line_t(
    "echart_324_c3",
    "再生铅反射炉利润·季节图",
    "Mysteel 再生铅反射炉利润 · 日 · 元/吨 · %d 点(2019起) · 至 %s" % (
        len(d_refl), latest(m_refl)),
    "#b06a32", d_refl,
    "什么时候看：判断再生铅反射炉利润的月度季节性规律——再生利润季节性反映再生冶炼端的供需周期。<br>"
    "怎么看：Q4(旺季)利润偏高(需求旺+开工率高)；Q1(春节)偏低(节前停产)。"
    "若某年利润线整体抬升=再生铅成本结构改善;若下移=废电瓶成本上升或再生精铅价格下跌。"
)

NOTE = """<strong style="color:#c9d1d9">3.2.4 定义：</strong>冶炼利润→供应弹性 = 铅锭-再生精铅价差(正主) + 再生铅炉型利润对比,判断再生铅供给弹性的核心驱动与技术路线分化。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>j324_primary_spread 铅锭-再生精铅价差(元/吨/日, 新注册,1478点至2026-08)。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>j324_regen_profit_refl 再生铅反射炉利润(元/吨/日, 新注册,1870点) · j324_regen_profit_bof 再生铅富氧侧吹炉利润(元/吨/日, 新注册,1870点) · j72_smelt_profit 铅冶炼利润(7.2正主,辅助) · j24_refine_spread 精废价差(2.4正主,辅助,口径不同)。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>海外矿财报产量 → 3.1.1正主 · 海外矿分国别 → 3.1.2正主 · 国内矿产量 → 3.1.3正主 · 矿进口量 → 3.1.4正主 · TC加工费 → 3.1.5正主 · 再生精铅产量 → 3.2.3正主 · 铅冶炼利润 → 7.2正主(辅助)。<br>
<strong style="color:#c9d1d9">数据源：</strong>Mysteel 铅锭-再生精铅价差(ID01501478, 日度1478点/2019起) + Mysteel 再生铅反射炉利润(ID01167269, 日度1870点/2019起) + Mysteel 再生铅富氧侧吹炉利润(ID01167270, 日度1870点/2019起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>精废价差1478点(2019-01起)；反射炉利润1870点(2019-01起)；富氧炉利润1870点(2019-01起)。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.1=海外矿财报产量 · 3.1.2=分国别总量 · 3.1.3=国内矿产量 · 3.1.4=矿进口量 · 3.1.5=TC加工费 · 3.2.1=精炼产量 · 3.2.2=开工率检修 · 3.2.3=再生供应(已上线) · 3.2.4=冶炼利润供应弹性。"""

html = page_html(
    "铅(PB) 3.2.4 冶炼利润→供应弹性",
    make_crumb("铅", "PB", "3", "供给", "3.2.4", "冶炼利润→供应弹性", "1", 3),
    "Mysteel",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 3.2.4 冶炼利润→供应弹性 · v1（3 图全真数据 · 精废价差 · 炉型利润对比 · 利润季节图）· indicators_v1.json v3.1",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_3_overview.html">← 回板块3总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_324_profit_elasticity.html", html)
