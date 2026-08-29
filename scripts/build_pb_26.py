#!/usr/bin/env python3
"""铅(PB) 2.6 持仓席位观察子页 · v1 · 3 图全真数据（指标树填充板块1·价格信号·第6子节点）。

图1 沪铅持仓量+成交量（量仓结构，chart_dual）：j21_oi + j21_volume（观 kline PB D 全量）
图2 沪铅持仓量季节图（chart_line_t 时序⇄季节）：j21_oi 近5年历年线
图3 持仓-价格背离（chart_dual）：j21_oi 持仓量 + j21_close 收盘价

数据源：zhiji 观服务 kline PB D，3751 交易日（2011-03 至 2026-08-28）。
⚠️ 前20会员多空/集中度/多空比：上期所会员持仓排名，知几无数据 → 标注待外部源（上期所官网/商业终端）。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html)

CIDS = ["echart_26_c1", "echart_26_c2", "echart_26_c3"]

m_oi = load_metric("j21_oi")       # 沪铅主力持仓量
m_vol = load_metric("j21_volume")  # 沪铅主力成交量
m_close = load_metric("j21_close") # 沪铅主力收盘价

d_oi = pairs(m_oi)
d_vol = pairs(m_vol)
d_close = pairs(m_close)
print("[POINTS] 持仓=%d 成交=%d 收盘=%d" % (len(d_oi), len(d_vol), len(d_close)))

# === 图1：量仓结构（持仓量 + 成交量）===
h1, j1 = chart_dual(
    "echart_26_c1",
    "沪铅主力持仓量 vs 成交量（量仓结构）",
    "观 kline PB D 主连 · 日 · 手 · %d 点 · 2011-03 至 %s" % (len(d_oi), latest(m_oi)),
    d_oi, "#b06a32", "持仓量", "手",
    d_vol, "#5b98c9", "成交量", "手",
    "什么时候看：判断资金参与度与换手强度。<br>"
    "怎么看：量增仓增 = 新资金入场、趋势延续；量增仓减 = 资金对倒/获利了结；"
    "量缩仓增 = 持仓集中、波动蓄势；量仓同缩 = 观望。最新(2026-08-28)：持仓约9.5万手。"
)

# === 图2：持仓量季节图 ===
h2, j2 = chart_line_t(
    "echart_26_c2",
    "沪铅主力持仓量季节图（近5年各一条线 + 图例标年份）",
    "观 kline PB D · 日 · 手 · %d 点 · 2011-03 至 %s" % (len(d_oi), latest(m_oi)),
    "#9b6bb5",
    d_oi,
    "什么时候看：判断当前持仓量在历史季节性中的位置。<br>"
    "怎么看：切季节视图把近5年叠一起，今年持仓明显高于历史同期 = 资金聚集度高、行情波动潜力大；"
    "明显低于 = 资金撤离。持仓高位通常对应变盘窗口。",
    default_seasonal=True
)

# === 图3：持仓-价格背离 ===
h3, j3 = chart_dual(
    "echart_26_c3",
    "沪铅持仓量 vs 收盘价（量价背离）",
    "观 kline PB D 主连 · 日 · 手/元每吨 · %d 点 · 至 %s" % (len(d_close), latest(m_close)),
    d_oi, "#b06a32", "持仓量", "手",
    d_close, "#5b98c9", "收盘价", "元/吨",
    "什么时候看：判断上涨/下跌是否由资金推动，识别顶背离。<br>"
    "怎么看：价涨仓增 = 多头资金推动、健康；价涨仓减 = 空头回补/情绪反弹、不可持续；"
    "价跌仓增 = 空头主动打压、弱势；价跌仓减 = 多头止损离场、接近底部。"
    "最新(2026-08-28)：收盘16245元。注：前20会员多空/集中度待上期所会员持仓排名外部源。"
)

NOTE = """<strong style="color:#c9d1d9">2.6 定义：</strong>持仓席位观察 = 主力持仓量/成交量/前20会员多空/集中度/多空比，判断资金方向与筹码集中度。<br>
<strong style="color:#c9d1d9">指标组：</strong>j21_oi 沪铅主力持仓量(手) · j21_volume 成交量(手) · j21_close 收盘价(元/吨)，均来自观服务 kline PB D，3751 交易日全量。<br>
<strong style="color:#c9d1d9">未覆盖（待外部源）：</strong>前20会员多单/空单/净持仓/多空比/集中度 —— 上期所会员持仓排名，知几无数据，需上期所官网/商业终端/akshare(未装)。<br>
<strong style="color:#c9d1d9">同花顺参考：</strong>2026-08-28 沪铅前20期商全月合约多单8.72万手/空单8.40万手/多空比1.04/净多3259手（公开摘要）。"""

html = page_html(
    "铅(PB) 2.6 持仓席位观察",
    "铅(PB) · 2 价格信号 · 2.6 持仓席位观察 · v1 3 图",
    "SHFE 观服务",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 2.6 持仓席位观察 · v1（3 图全真数据 · 量仓结构 · 持仓季节 · 量价背离）· indicators_v1.json v2.4",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
)
write_html("pb_26_position_holder.html", html)
