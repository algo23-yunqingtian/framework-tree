#!/usr/bin/env python3
"""铅(PB) 2.4 价差体系子页 · v1 · 3 图全真数据（指标树填充板块1·价格信号·第4子节点）。

图1 沪铅期现月差（chart_dual）：j24_spread_m 当月 + j24_spread_s 次月（期现价差，月差=次月-当月）
图2 再生铅利润 + 精废价差（chart_dual）：j24_regen_profit + j24_refine_spread
图3 铅锌比价（chart_dual）：j21_close 沪铅主连 vs ZN 主连 close（kline 落盘）→ 比价=铅/锌

数据源：zhiji 料服务 SMM（期现价差251点2025-08起 / 再生利润2586点2016起 / 精废价差2831点2015起）+ 观服务 kline ZN(4731根2007起)。
⚠️ 期限结构多合约曲线、跨期逼仓图：需要 SHFE 各月合约收盘价，本次用 SMM 期现价差当月/次月近似月差。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html,
                        make_crumb)
import json

CIDS = ["echart_24_c1", "echart_24_c2", "echart_24_c3"]

m_m = load_metric("j24_spread_m")   # 期现价差当月
m_s = load_metric("j24_spread_s")   # 期现价差次月
m_rp = load_metric("j24_regen_profit")
m_rs = load_metric("j24_refine_spread")
m_pb = load_metric("j21_close")

d_m = pairs(m_m)
d_s = pairs(m_s)
d_rp = pairs(m_rp)
d_rs = pairs(m_rs)
d_pb = pairs(m_pb)

# 沪锌主连（从落盘 json 读取）
zn = json.load(open('/home/ubuntu/analysis/iwencai/PB/pb_zn_main_daily.json'))
d_zn = [[b["time"], b["close"]] for b in zn["bars"]]
print("[POINTS] 月差m=%d s=%d 再生利润=%d 精废=%d 沪铅=%d 沪锌=%d" % (len(d_m), len(d_s), len(d_rp), len(d_rs), len(d_pb), len(d_zn)))

# === 图1：沪铅期现月差（当月 vs 次月）===
h1, j1 = chart_dual(
    "echart_24_c1",
    "沪铅期现价差：当月 vs 次月（月差结构）",
    "SMM 沪铅期现价差(收盘) · 日 · 元/吨 · %d 点 · 2025-08 至 %s" % (len(d_m), latest(m_m)),
    d_m, "#b06a32", "当月合约价差", "元/吨",
    d_s, "#5b98c9", "次月合约价差", "元/吨",
    "什么时候看：判断近月是否紧张（逼仓/挤仓结构）。<br>"
    "怎么看：当月价差明显高于次月 = 近月贴水收窄/升水扩大、现货抢货、可能逼仓；"
    "两线同步走强 = 整体期现回归。最新(2026-08-28)：当月125 vs 次月170 = 月差约45元。"
    "注：数据仅1年(2025-08起)，趋势判断需更长历史。"
)

# === 图2：再生铅利润 + 精废价差 ===
h2, j2 = chart_dual(
    "echart_24_c2",
    "再生铅利润 vs 精废价差（再生供给压力）",
    "SMM 再生铅利润 + 铅精废价差 · 日 · 元/吨 · %d/%d 点 · 至 %s" % (len(d_rp), len(d_rs), latest(m_rp)),
    d_rp, "#e06c75", "再生铅利润", "元/吨",
    d_rs, "#5fb3a1", "铅精废价差", "元/吨",
    "什么时候看：判断再生铅开工意愿，再生是铅供给的主力。<br>"
    "怎么看：再生铅利润转负并加深（当前-512元）= 再生厂亏损、减产意愿强、支撑铅价底部；"
    "精废价差收窄 = 废电瓶贵、再生利润被压缩。利润修复后供应回升对远月价差形成压制。"
)

# === 图3：铅锌比价 ===
h3, j3 = chart_dual(
    "echart_24_c3",
    "沪铅 vs 沪锌（跨品种比价）",
    "沪铅主连(close) vs 沪锌主连(close) · 日 · 元/吨 · %d/%d 点 · 至 %s" % (len(d_pb), len(d_zn), d_pb[-1][0]),
    d_pb, "#b06a32", "沪铅主力", "元/吨",
    d_zn, "#5b98c9", "沪锌主力", "元/吨",
    "什么时候看：判断铅相对锌的估值位置。<br>"
    "怎么看：两线背离/收窄反映铅锌估值修复。参考：2026-06 锌铅比价1.51、价差8500元，突破2022以来90%分位 = 铅相对锌历史低位；"
    "铅价补涨修复比价。同花顺案例：2024-07 沪铅 08-09 月差扩至725元/吨的软挤仓行情。"
)

NOTE = """<strong style="color:#c9d1d9">2.4 定义：</strong>价差体系 = 月差/跨期/期限结构/沪伦比/跨品种比价，判断近月逼仓、进口压力、跨品种估值。<br>
<strong style="color:#c9d1d9">指标组：</strong>j24_spread_m/s 期现价差当月/次月(元/吨) · j24_regen_profit 再生铅利润 · j24_refine_spread 精废价差 · 沪铅主连 j21_close · 沪锌主连 ZN kline。<br>
<strong style="color:#c9d1d9">数据质量：</strong>期现价差 251点(2025-08起,1年)；再生利润 2586点(2016起)；精废价差 2831点(2015起)；沪锌主连 4731根(2007起)。<br>
<strong style="color:#c9d1d9">未覆盖：</strong>SHFE 各月合约完整期限结构曲线（本次用期现价差当月/次月近似）、沪伦比值(2.2已入库 a10155854)、进口盈亏(2.3已入库 a12759796)。"""

html = page_html(
    "铅(PB) 2.4 价差体系",
    make_crumb("铅", "PB", "2", "价格信号", "2.4", "价差体系", "1", 3),
    "SMM / SHFE",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 2.4 价差体系 · v1（3 图全真数据 · 期现月差 · 再生利润精废价差 · 铅锌比价）· indicators_v1.json v2.3",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,

    nav_back='<a href="pb_2_overview.html">← 回板块2总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_24_spread_system.html", html)
