#!/usr/bin/env python3
"""铅(PB) 4.5 隐性·在途库存子页 · v1 · 2 图全真数据（板块4 拆分重构，对齐板块2/6 范式）。

图1 LME 新加坡非仓单库存（chart_line_t，隐性库存的直接观测代理）
图2 铅锭进口量（海关）+ LME 新加坡入库量（chart_dual，到港节奏）

数据来源：api_cache.db（PB）。i23 LME新加坡非仓单库存(353点,止2025-04) /
i17 海关铅锭进口量(103点,月度) / i24 LME新加坡入库量(2194点,日度)。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_45_c1", "echart_45_c2"]

m23 = load_metric("i23")  # LME 新加坡非仓单库存
m17 = load_metric("i17")  # 海关铅锭进口量
m24 = load_metric("i24")  # LME 新加坡入库量

d23, d17, d24 = pairs(m23), pairs(m17), pairs(m24)
print("[POINTS] SG非仓单=%d 海关进口=%d SG入库=%d" % (len(d23), len(d17), len(d24)))

# === 图1：LME 新加坡非仓单库存 ===
h1, j1 = chart_line_t(
    "echart_45_c1",
    "LME新加坡非仓单库存（隐性库存直接观测）",
    "LME铅新加坡非仓单库存 · 日 · 吨 · %d 点 · 至 %s" % (len(d23), latest(m23)),
    "#c87070",
    d23,
    "什么时候看：直接观测隐性库存的沉淀量。<br>"
    "怎么看：非仓单库存 = 已入库但尚未转为可交割仓单的库存，是最接近「隐性库存」的公开代理指标。"
    "非仓单库存上升 = 库存正从显性转隐性（货源隐藏），后续释放会突然冲击市场；"
    "非仓单库存下降 = 隐性库存转为仓单，货源显性化、供给压力可见。"
    "⚠️ 此指标缓存仅覆盖 2025-04 至 2026-08（1.4 年），年度不足无法做季节对齐，"
    "故本页图为时序视图；需更长历史请跑 refresh_cache.py 补拉。",
    default_seasonal=False,
)

# === 图2：铅锭进口量 + SG入库量 ===
h2, j2 = chart_dual(
    "echart_45_c2",
    "海关铅锭进口 + LME新加坡入库（在途到港节奏）",
    "海关铅锭进口(月) + LME新加坡入库量(日) · 吨 · %d/%d 点 · 至 %s / %s"
    % (len(d17), len(d24), latest(m17), latest(m24)),
    d17, "#5fb3a1", "海关铅锭进口", "吨",
    d24, "#5b98c9", "SG入库量", "吨",
    "什么时候看：判断在途货源的到港节奏。<br>"
    "怎么看：海关进口为最终落地口径（滞后15-20天），SG入库量是到港前的高频代理。"
    "SG入库放量而海关进口未跟上 = 货源在途未清关；两者同步上行 = 进口窗口完全打开、国内供给压力上升。"
    "6.4 海外对华发运展示更细的发运结构，此处只看总量节奏。",
)

NOTE = """<strong style="color:#c9d1d9">4.5 定义：</strong>隐性/在途库存 = 非仓单库存 + 在途货源（已到港未清关、在海上、在仓库但未转仓单），周/月频，是显性库存之外的「未释放」库存。<br>
<strong style="color:#c9d1d9">指标组：</strong>i23 LME新加坡非仓单库存(日) · i17 海关铅锭进口量(月) · i24 LME新加坡入库量(日)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>i23 353点(止2025-04-01) / i17 103点(月度,2018-01起) / i24 2194点(日度,2018-01起)。<br>
<strong style="color:#c9d1d9">口径与边界：</strong>海关铅锭进口总量同时是 6.1/6.2 的到港结果，此页只作在途节奏代理，避免与进出口板块口径重复。<strong>提单量/提单库存/在途量</strong>(6.4发散推荐)在知几无序列，按取舍规则3入备用库标「待外部源」。<br>
<strong style="color:#c9d1d9">拆分说明：</strong>本页由 pb_stock_v2.html 4.5 面板拆分而来，2图全部保留；隐性库存推算(自算)因依赖陈旧序列未上图，逻辑保留在 NOTE。"""

html = page_html(
    "铅(PB) 4.5 隐性·在途库存",
    make_crumb("铅", "PB", "4", "库存", "4.5", "隐性·在途", "1", 2),
    "LME · 海关",
    h1, h2, "", NOTE,
    "有色金属产业指标树 · 铅(PB) 4.5 隐性·在途库存 · v1（2 图全真数据 · SG非仓单 · 进口与入库节奏）· indicators_v1.json v2.5",
    j1 + "\n" + j2,
    CIDS,
    nav_back='<a href="pb_4_overview.html">← 回板块4总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_45_hidden_stock.html", html)
