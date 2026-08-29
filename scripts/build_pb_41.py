#!/usr/bin/env python3
"""铅(PB) 4.1 交易所库存子页 · v1 · 3 图全真数据（板块4 拆分重构，对齐板块2/6 范式）。

图1  LME铅总库存 + 注销占比（chart_line_t，注销占比=注销仓单/总库存×100，自算）
图2  LME铅库存分地区（chart_dual，新加坡注册 vs 新加坡注销；迪拜/仁川无连续同期故不入）
图3  上期所铅库存 + LME铅库存（chart_dual，海内外跨市对比）

数据来源：api_cache.db（PB）。i1 LME总库存(501点,止2024-08-27) / i2 SHFE仓单(485点) /
i7 LME注销仓单(2182点) / i19 SG注册(2194点) / i20 SG注销(2194点)。
⚠️ 数据新鲜度：i1/i2 缓存止 2024-08，为历史口径快照；i7/i19/i20 至 2026。NOTE 标注。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_41_c1", "echart_41_c2", "echart_41_c3"]

m1 = load_metric("i1")    # LME 铅总库存
m2 = load_metric("i2")    # SHFE 铅仓单
m7 = load_metric("i7")    # LME 注销仓单
m19 = load_metric("i19")  # LME 新加坡注册仓单
m20 = load_metric("i20")  # LME 新加坡注销仓单

d1, d2, d7, d19, d20 = pairs(m1), pairs(m2), pairs(m7), pairs(m19), pairs(m20)

# 注销占比 = i7 / i1 × 100（按共有日期）
m1_map = {dt: v for dt, v in d1}
rp = []
for dt, v7 in d7:
    if dt in m1_map and m1_map[dt]:
        rp.append([dt, round(v7 / m1_map[dt] * 100, 2)])
print("[POINTS] LME总=%d SHFE仓单=%d LME注销=%d SG注册=%d SG注销=%d 注销占比=%d"
      % (len(d1), len(d2), len(d7), len(d19), len(d20), len(rp)))

# === 图1：LME 铅总库存 + 注销占比 ===
h1, j1 = chart_line_t(
    "echart_41_c1",
    "LME铅库存 · 注销占比（显性化节奏）",
    "LME铅总库存 + 注销占比(注销/总×100，自算) · 日 · %% · 总库存%d点(止%s) / 注销占比%d点 · 至 %s"
    % (len(d1), latest(m1), len(rp), latest(m7)),
    "#b06a32",
    rp,
    "什么时候看：判断全球显性库存的显性化/隐性化节奏。<br>"
    "怎么看：注销占比上升 = 货源正在从注册库转出（发往中国/交付中），隐性库存转化为可见压力；"
    "占比下降 = 货源在沉淀为注册库。注销占比是进口到港的前瞻信号，比总量更有信息量。"
    "注意：注销仓单口径至2026，总库存口径止2024，两条线时间窗不同。",
    default_seasonal=True,
)

# === 图2：LME 新加坡注册 vs 注销仓单 ===
h2, j2 = chart_dual(
    "echart_41_c2",
    "LME新加坡仓单结构（注册 vs 注销）",
    "LME铅新加坡分仓 · 日 · 吨 · SG注册%d点 / SG注销%d点 · 至 %s"
    % (len(d19), len(d20), latest(m20)),
    d19, "#5b98c9", "SG注册仓单", "吨",
    d20, "#c87070", "SG注销仓单", "吨",
    "什么时候看：判断新加坡 LME 库的显性化进度。<br>"
    "怎么看：新加坡是 LME 铅的亚洲枢纽仓，占 LME 总库存九成以上。"
    "SG注销仓单堆积 = 货源集中在此待发货（进口到港的前瞻信号）；注册仓单堆积 = 库存沉淀、压力未释放。"
    "最新：SG注销占SG总仓单比例高企，说明货源正处于交付转移窗口。",
)

# === 图3：上期所铅库存 + LME铅库存 ===
h3, j3 = chart_dual(
    "echart_41_c3",
    "上期所铅仓单 + LME铅库存（海内外跨市）",
    "SHFE铅仓单 + LME铅总库存 · 日 · 左:吨(SHFE) / 右:吨(LME) · %d/%d 点 · 至 %s"
    % (len(d2), len(d1), latest(m1)),
    d2, "#5fb3a1", "SHFE铅仓单", "吨",
    d1, "#b06a32", "LME铅库存", "吨",
    "什么时候看：判断海内外库存是否同步去化，以及跨市套利空间。<br>"
    "怎么看：SHFE与LME同向去化 = 全球同步紧平衡，价格上涨有支撑；"
    "SHFE去化而LME堆积 = 进口利润窗口可能打开，海外库存将流向中国。"
    "沪伦比值(价格端)在2.3展示，此处只看库存实物量。",
)

NOTE = """<strong style="color:#c9d1d9">4.1 定义：</strong>交易所库存 = LME总库存/分地区仓单/注销仓单/上期所仓单，是显性库存的正主指标，日频、滞后小，直接反映全球可交割资源的沉淀与释放节奏。<br>
<strong style="color:#c9d1d9">指标组：</strong>i1 LME铅总库存 · i2 SHFE铅仓单 · i7 LME注销仓单 · i19 SG注册仓单 · i20 SG注销仓单。<br>
<strong style="color:#c9d1d9">数据质量：</strong>i1 501点(止2024-08-27) / i2 485点(止2024-08-26) / i7 2182点(2018-01起) / i19、i20 各2194点(2018-01起)。<br>
<strong style="color:#c9d1d9">口径与边界：</strong>注册/注销仓单拆分属 4.2 仓单正主；国内社会库存(4.3)、工厂/原料库存(4.4)、隐性在途(4.5) 不在此页。<strong>i1/i2 缓存为历史快照，止2024-08</strong>，如需最新值请跑 refresh_cache.py 更新。<br>
<strong style="color:#c9d1d9">拆分说明：</strong>本页由 pb_stock_v2.html 4.1 面板拆分而来，原4图减为3图（C02分地区系列中仁川i29止2021-08、迪拜i30止2025-03，连续性与主序列不一致，按取舍规则3剔除进备用库）。"""

html = page_html(
    "铅(PB) 4.1 交易所库存",
    make_crumb("铅", "PB", "4", "库存", "4.1", "交易所库存", "1", 3),
    "LME · SHFE · SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 4.1 交易所库存 · v1（3 图全真数据 · LME注销占比 · SG仓单结构 · SHFE+LME跨市）· indicators_v1.json v2.5",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_4_overview.html">← 回板块4总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_41_exchange_stock.html", html)
