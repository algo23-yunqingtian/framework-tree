#!/usr/bin/env python3
"""铅(PB) 2.5 估值与利润子页 · v1 · 3 图全真数据（指标树填充板块1·价格信号·第5子节点）。

图1 原生 vs 再生冶炼利润（chart_dual）：j25_smelt_cost 原生加工成本 + j25_ag_revenue 白银收益(抵扣) + j24_regen_profit 再生利润
    —— 原生净利润 ≈ 白银收益 - 加工成本（副产品抵扣后），与再生利润对比
图2 再生铅成本线（chart_dual）：j25_battery 废蓄电池均价 + j22_regen 再生精铅 + 精废价差(计算)
图3 铅精矿TC vs 沪铅价（chart_dual）：j25_tc 国产TC + j21_close 沪铅主力

数据源：zhiji 料服务 SMM。加工成本/白银收益/TC 1370点(2021起)；废蓄电池 645点(2023-12起)；再生利润 2586点(2016起)。
⚠️ 原生铅综合利润 = 白银收益 - 加工成本 + 铅价-精矿成本，SMM未直接给利润值，用加工成本+白银收益展示成本结构。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html)

CIDS = ["echart_25_c1", "echart_25_c2", "echart_25_c3"]

m_cost = load_metric("j25_smelt_cost")
m_ag = load_metric("j25_ag_revenue")
m_rp = load_metric("j24_regen_profit")
m_bat = load_metric("j25_battery")
m_regen = load_metric("j22_regen")
m_tc = load_metric("j25_tc")
m_pb = load_metric("j21_close")

d_cost = pairs(m_cost)
d_ag = pairs(m_ag)
d_rp = pairs(m_rp)
d_bat = pairs(m_bat)
d_regen = pairs(m_regen)
d_tc = pairs(m_tc)
d_pb = pairs(m_pb)

# 原生净利（白银收益 - 加工成本，副产品抵扣后近似）+ 再生利润对齐
ag_map = {d: v for d, v in d_ag}
cost_map = {d: v for d, v in d_cost}
d_native = []
for d, v in d_cost:
    if d in ag_map:
        d_native.append([d, round(ag_map[d] - v, 2)])
print("[POINTS] 原生净利=%d 再生利润=%d 废电池=%d 再生精铅=%d TC=%d 沪铅=%d" % (len(d_native), len(d_rp), len(d_bat), len(d_regen), len(d_tc), len(d_pb)))

# === 图1：原生 vs 再生冶炼利润 ===
h1, j1 = chart_dual(
    "echart_25_c1",
    "原生铅 vs 再生铅冶炼利润",
    "原生净利≈白银收益-加工成本 + SMM再生铅利润 · 日 · 元/吨 · 原生%d点(2021起) / 再生%d点(2016起) · 至 %s" % (len(d_native), len(d_rp), latest(m_rp)),
    d_native, "#e06c75", "原生铅净利(估)", "元/吨",
    d_rp, "#5b98c9", "再生铅利润", "元/吨",
    "什么时候看：判断冶炼端盈亏，利润是供给收缩/扩张的直接驱动。<br>"
    "怎么看：利润转负并加深 = 冶炼亏损、减产/停产预期强、支撑铅价底部（成本支撑）；"
    "利润高企 = 开工动力足、供给压力大。原生净利为估算(白银收益-加工成本)。最新(2026-08-28)：再生利润-512元(亏损)、原生净利约-238元。"
)

# === 图2：再生铅成本线 ===
h2, j2 = chart_dual(
    "echart_25_c2",
    "废蓄电池 vs 再生精铅（再生成本线）",
    "SMM 废蓄电池均价 + 再生精铅均价 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (len(d_bat), len(d_regen), latest(m_regen)),
    d_bat, "#b06a32", "废蓄电池均价", "元/吨",
    d_regen, "#5b98c9", "再生精铅均价", "元/吨",
    "什么时候看：判断再生铅的成本支撑。<br>"
    "怎么看：废电池(原料)与再生精铅(成品)价差=精废价差，决定再生利润弹性。"
    "废电池涨得快 = 再生成本抬升、利润被吞噬、减产风险；价差收窄 = 再生厂亏损。"
    "最新(2026-08-28)：废蓄电池9275 vs 再生精铅15975 = 价差6700元。注：废电池数据仅2.7年(2023-12起)。"
)

# === 图3：铅精矿TC vs 沪铅价 ===
h3, j3 = chart_dual(
    "echart_25_c3",
    "铅精矿TC vs 沪铅价（矿端紧松）",
    "SMM 国产铅精矿加工费TC + 沪铅主力 · 日 · TC元/金属吨 · %d/%d 点 · 至 %s" % (len(d_tc), len(d_pb), d_pb[-1][0]),
    d_tc, "#5fb3a1", "国产TC", "元/金属吨",
    d_pb, "#b06a32", "沪铅主力", "元/吨",
    "什么时候看：判断矿端紧松与原生冶炼利润的挤压关系。<br>"
    "怎么看：TC下行 = 矿端偏紧、原生冶炼原料成本上升、利润承压；TC上行 = 矿端宽松。"
    "最新(2026-08-28)：国产TC 150元(低位,矿端偏紧) + 沪铅16245元。"
)

NOTE = """<strong style="color:#c9d1d9">2.5 定义：</strong>估值与利润 = 原生/再生冶炼利润 + 废电瓶成本 + 价格分位 + TC加工费，判断成本支撑与利润驱动。<br>
<strong style="color:#c9d1d9">指标组：</strong>j25_smelt_cost 原生加工成本(元/吨) · j25_ag_revenue 白银收益 · j25_tc 国产TC(元/金属吨) · j25_battery 废蓄电池价 · j24_regen_profit 再生利润 · j22_regen 再生精铅。<br>
<strong style="color:#c9d1d9">数据质量：</strong>加工成本/白银/TC 1370点(2021-01起)；废蓄电池 645点(2023-12起)；再生利润 2586点(2016起)。<br>
<strong style="color:#c9d1d9">口径：</strong>SMM无原生铅综合利润直接字段，图1用「白银收益-加工成本」估算；精废价差 j00146945 已在2.4展示。"""

html = page_html(
    "铅(PB) 2.5 估值与利润",
    "铅(PB) · 2 价格信号 · 2.5 估值与利润 · v1 3 图",
    "SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 2.5 估值与利润 · v1（3 图全真数据 · 原生再生利润 · 再生成本线 · TC矿端）· indicators_v1.json v2.4",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
)
write_html("pb_25_valuation_profit.html", html)
