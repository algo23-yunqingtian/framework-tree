#!/usr/bin/env python3
"""铅(PB) 4.2 仓单子页 · v1 · 3 图全真数据（板块4 拆分重构，对齐板块2/6 范式）。

图1 上期所铅仓单总量 + LME注销仓单 + 注销占比（chart_dual 主 + 自算占比）
图2 上期所仓单分地区（chart_line_t，上海仓单占比=上海仓单/上期所总仓单×100，自算）
图3 LME注册 + 注销仓单（chart_dual，交仓加速信号）

数据来源：api_cache.db（PB）。i2 SHFE仓单(485点) / i7 LME注销(2182点) /
i8 SHFE上海仓单(2088点) / i6 LME注册仓单(2182点)。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_42_c1", "echart_42_c2", "echart_42_c3"]

m2 = load_metric("i2")   # SHFE 铅仓单总量
m6 = load_metric("i6")   # LME 注册仓单
m7 = load_metric("i7")   # LME 注销仓单
m8 = load_metric("i8")   # SHFE 仓单分地区_上海

d2, d6, d7, d8 = pairs(m2), pairs(m6), pairs(m7), pairs(m8)

# 注销占比 = i7 / i6 × 100
m6_map = {dt: v for dt, v in d6}
rp_cancel = []
for dt, v7 in d7:
    if dt in m6_map and m6_map[dt]:
        rp_cancel.append([dt, round(v7 / m6_map[dt] * 100, 2)])

# 上海仓单占比 = i8 / i2 × 100
m2_map = {dt: v for dt, v in d2}
rp_sh = []
for dt, v8 in d8:
    if dt in m2_map and m2_map[dt]:
        rp_sh.append([dt, round(v8 / m2_map[dt] * 100, 2)])
print("[POINTS] SHFE仓单=%d LME注册=%d LME注销=%d 上海仓单=%d 注销占比=%d 上海占比=%d"
      % (len(d2), len(d6), len(d7), len(d8), len(rp_cancel), len(rp_sh)))

# === 图1：上期所仓单 + LME注销仓单 + 注销占比 ===
h1, j1 = chart_line_t(
    "echart_42_c1",
    "LME注销仓单 · 注销占比（交仓加速信号）",
    "LME注销仓单 + 注销占比(注销/注册×100，自算) · 日 · %% · 注册%d点 / 注销占比%d点 · 至 %s"
    % (len(d6), len(rp_cancel), latest(m7)),
    "#c87070",
    rp_cancel,
    "什么时候看：判断货源交仓速度。<br>"
    "怎么看：注销占比急升 = 仓单集中转入交仓流程（发运在途增加），后续到港将放量，"
    "压制进口利润、利空国内现货；占比回落 = 交仓放缓。注销占比是 4.5 在途的前瞻先行指标。"
    "最新：注销占比维持高位，说明全球货源处于交付转移窗口。",
    default_seasonal=True,
)

# === 图2：上期所仓单分地区（上海占比）===
h2, j2 = chart_line_t(
    "echart_42_c2",
    "上期所仓单 · 上海仓占比（国内交割仓分布）",
    "上期所铅仓单分地区占比(上海/总仓单×100，自算) · 日 · %% · 上海仓单%d点 / 上期所总仓单%d点 · 至 %s"
    % (len(d8), len(d2), latest(m2)),
    "#5fb3a1",
    rp_sh,
    "什么时候看：判断国内交割仓的空间分布是否集中。<br>"
    "怎么看：上海占比上升 = 仓单向华东交割库集中，华东现货承压；占比分散 = 多地均衡。"
    "国内仓单分地区仅上海口径在库（其余地区序列未入库），此图反映国内主要交割仓的变化。"
    "注意：上期所总仓单口径止2024-08。",
    default_seasonal=True,
)

# === 图3：LME注册 + 注销仓单 ===
h3, j3 = chart_dual(
    "echart_42_c3",
    "LME注册 + 注销仓单（货源状态）",
    "LME铅注册仓单 + 注销仓单 · 日 · 吨 · %d/%d 点 · 至 %s"
    % (len(d6), len(d7), latest(m6)),
    d6, "#5b98c9", "LME注册仓单", "吨",
    d7, "#c87070", "LME注销仓单", "吨",
    "什么时候看：判断 LME 库存的注册/注销结构。<br>"
    "怎么看：注册仓单 = 已入库可交割、沉淀的库存；注销仓单 = 正在转出交仓、即将离场的库存。"
    "注册占比高 = 库存沉淀未释放；注销占比高 = 货源正被消化发运。"
    "LME总库存/LME分地区在 4.1 展示，此页只看仓单状态拆分。",
)

NOTE = """<strong style="color:#c9d1d9">4.2 定义：</strong>仓单 = 注册仓单/注销仓单及其结构占比，衡量可交割资源的流转状态。注册=已沉淀，注销=正在交仓发运，是库存从静转动的分界。<br>
<strong style="color:#c9d1d9">指标组：</strong>i6 LME注册仓单 · i7 LME注销仓单 · i2 SHFE铅仓单 · i8 SHFE上海仓单。<br>
<strong style="color:#c9d1d9">数据质量：</strong>i6、i7 各2182点(2018-01起) / i8 2088点(2018-01起) / i2 485点(止2024-08-26)。<br>
<strong style="color:#c9d1d9">口径与边界：</strong>LME总库存与分地区库存属 4.1 交易所库存正主；上期所仓单背离(MA40)与 LME库存跨市在 4.1 图3。<strong>交割品牌/质押/贸易商库存/亚洲可交仓</strong>在知几无序列，按取舍规则3进备用库标「待外部源」。<br>
<strong style="color:#c9d1d9">拆分说明：</strong>本页由 pb_stock_v2.html 4.2 面板拆分而来，3图全部保留，仅重排图序（注销占比提为图1，因其为在途前瞻先行）。"""

html = page_html(
    "铅(PB) 4.2 仓单",
    make_crumb("铅", "PB", "4", "库存", "4.2", "仓单", "1", 3),
    "LME · SHFE · SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 4.2 仓单 · v1（3 图全真数据 · LME注销占比 · 上海仓占比 · 注册注销结构）· indicators_v1.json v2.5",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_4_overview.html">← 回板块4总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_42_warrant.html", html)
