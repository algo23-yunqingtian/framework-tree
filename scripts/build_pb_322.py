#!/usr/bin/env python3
"""铅(PB) 3.2.2 开工率与检修子页 · v1 · 3 图全真数据（板块3·供给·第7子节点）。

图1 原生铅产能利用率(周)时序（chart_line_t）：j322_native_util_w Mysteel原生铅产能利用率(周) —— 开工率正主
图2 原生vs再生开工率对比（chart_dual）：j322_native_util_w 原生产能利用率(周) + j323_smm_regen_rate 再生铅开工率(月)
     —— 原生vs再生开工率对比,反映两大供给来源的开工状态
图3 原生铅产能利用率(周)季节图（chart_line_t seasonal）：近5年历年线,观察开工率季节性

数据源：Mysteel 原生铅产能利用率(ID01030007, 周) + SMM 再生铅开工率(a10017000, 月)。
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, write_html, make_crumb)

CIDS = ["echart_322_c1", "echart_322_c2", "echart_322_c3"]

m_native_w = load_metric("j322_native_util_w")
m_regen_rate = load_metric("j323_smm_regen_rate")

d_native_w = pairs(m_native_w)
d_regen_rate = pairs(m_regen_rate)

print("[POINTS] 原生开工率周=%d 再生开工率月=%d" % (
    len(d_native_w), len(d_regen_rate)))

# === 图1：原生铅产能利用率(周) ===
h1, j1 = chart_line_t(
    "echart_322_c1",
    "原生铅产能利用率(周)（3.2.2 正主）",
    "Mysteel 原生铅产能利用率(中国) · 周 · %% · %d 点(2023起) · 至 %s" % (
        len(d_native_w), latest(m_native_w)),
    "#5fb3a1", d_native_w,
    "什么时候看：3.2.2 开工率的正主图——原生铅产能利用率是冶炼端开工的最直接指标。<br>"
    "怎么看：开工率上行=冶炼端开工改善=原生供给增加=铅价供给压力增大。"
    "开工率下行=冶炼端减产=原生供给收紧=铅价供给支撑增强。"
    "开工率<70%%=冶炼亏损或检修期;开工率>80%%=冶炼盈利、开工饱满。"
    "周度数据比月度更灵敏,能更快捕捉开工变化。"
)

# === 图2：原生vs再生开工率对比 ===
h2, j2 = chart_dual(
    "echart_322_c2",
    "原生 vs 再生开工率（3.2 供给结构）",
    "Mysteel 原生铅产能利用率(周) · %% + SMM 再生铅开工率(月) · %% · %d/%d 点 · 至 %s" % (
        len(d_native_w), len(d_regen_rate), latest(m_native_w)),
    d_native_w, "#5fb3a1", "原生产能利用率(周)", "%",
    d_regen_rate, "#5b98c9", "再生铅开工率(月)", "%",
    "什么时候看：判断中国铅冶炼的开工结构——原生vs再生的开工率对比反映两大供给来源的开工状态。<br>"
    "怎么看：原生开工率上行=原生冶炼端开工改善=原生供给增加。"
    "再生开工率上行=再生冶炼端开工改善=再生供给增加(再生铅是边际供给,与废电瓶供应相关)。"
    "原生开工率高于再生=原生主导;再生开工率高于原生=再生主导。"
    "注：再生铅开工率=3.2.3正主,3.2.2仅作辅助对比。"
)

# === 图3：原生铅产能利用率(周)季节图 ===
h3, j3 = chart_line_t(
    "echart_322_c3",
    "原生铅产能利用率(周)·季节图",
    "Mysteel 原生铅产能利用率(中国) · 周 · %% · %d 点(2023起) · 至 %s" % (
        len(d_native_w), latest(m_native_w)),
    "#5fb3a1", d_native_w,
    "什么时候看：判断原生铅产能利用率的月度季节性规律——开工率季节性反映冶炼端供需周期。<br>"
    "怎么看：Q4(旺季)开工率高(冶炼利润好+需求旺)；Q1(春节)偏低(节前停产)。"
    "若某年开工率线整体抬升=原生冶炼端结构性改善;若下移=环保限产或成本压力。"
)

NOTE = """<strong style="color:#c9d1d9">3.2.2 定义：</strong>开工率与检修 = 原生铅产能利用率(周,正主) + 原生vs再生开工率对比,判断中国铅冶炼端的开工状态与季节性。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>j322_native_util_w Mysteel原生铅产能利用率(周,% ) —— 新注册指标,338点至2026-08。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>j323_smm_regen_rate SMM再生铅开工率(月,% , 3.2.3正主仅作辅助对比) · j322_native_util_m 原生铅产能利用率(月,79点,备用)。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>海外矿财报产量 → 3.1.1正主 · 海外矿分国别 → 3.1.2正主 · 国内矿产量 → 3.1.3正主 · 矿进口量 → 3.1.4正主 · TC加工费 → 3.1.5正主 · 再生铅开工率 → 3.2.3正主(辅助对比)。<br>
<strong style="color:#c9d1d9">数据源：</strong>Mysteel 原生铅产能利用率(ID01030007, 周度338点/2023起) + SMM 再生铅开工率(a10017000, 月度103点/2022起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>原生开工率(周)338点；再生开工率(月)103点。<br>
<strong style="color:#c9d1d9">3.x 边界：</strong>3.1.1=海外矿财报产量 · 3.1.2=分国别总量 · 3.1.3=国内矿产量 · 3.1.4=矿进口量 · 3.1.5=TC加工费 · 3.2.1=精炼产量 · 3.2.2=开工率检修 · 3.2.3=再生供应(已上线) · 3.2.4=冶炼利润供应弹性。"""

html = page_html(
    "铅(PB) 3.2.2 开工率与检修",
    make_crumb("铅", "PB", "3", "供给", "3.2.2", "开工率与检修", "1", 3),
    "Mysteel/SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 3.2.2 开工率与检修 · v1（3 图全真数据 · 原生开工率(周) · 原生vs再生 · 开工率季节图）· indicators_v1.json v3.1",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_3_overview.html">← 回板块3总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_322_operating_rate.html", html)
