#!/usr/bin/env python3
"""铅(PB) 2.1 盘面结构子页 · v1 · 3 图全真数据（指标树填充板块1·价格信号·第1子节点）。

图1 沪铅主力量价仓三联动（chart_pv 复合图）：j21_close 收盘价左轴 + j21_volume 成交量 + j21_oi 持仓量 右轴
图2 沪铅主力月度收盘价季节图（chart_line_t 时序⇄季节）：j21_close 日频聚合月频
图3 成交持仓比（chart_line_t）：j21_volume / j21_oi 计算

数据源：zhiji 观服务 kline PB D（3751 交易日，2011-03 至 2026-08-28），已灌 api_cache.db。
⚠️ 前20会员多空持仓/集中度（同花顺图3/4）：知几料服务无数据，标注待外部源（上期所会员持仓排名）。
"""
from chart_kits import (load_metric, pairs, latest, chart_pv, chart_line_t,
                        page_html, write_html)
from collections import OrderedDict

CIDS = ["echart_21_c1", "echart_21_c2", "echart_21_c3"]

# === 读数据 ===
m_close = load_metric("j21_close")   # 沪铅主力连续收盘价（日, 元/吨）
m_vol = load_metric("j21_volume")    # 成交量（日, 手）
m_oi = load_metric("j21_oi")         # 持仓量（日, 手）

d_close = pairs(m_close)
d_vol = pairs(m_vol)
d_oi = pairs(m_oi)

# === 日频 → 月频聚合（收盘价取月末值，量/仓取月内均值）===
def to_monthly(pairs_data, agg="last"):
    d = OrderedDict()
    for date, v in pairs_data:
        if v is None:
            continue
        ym = date[:7]  # YYYY-MM
        if ym not in d:
            d[ym] = []
        d[ym].append(v)
    out = []
    for ym, vals in d.items():
        if agg == "last":
            out.append([ym + "-01", vals[-1]])
        elif agg == "mean":
            out.append([ym + "-01", sum(vals) / len(vals)])
    return out

m_close_m = to_monthly(d_close, "last")   # 月末收盘价
m_vol_m = to_monthly(d_vol, "mean")       # 月均成交量
m_oi_m = to_monthly(d_oi, "last")         # 月末持仓量

# === 成交持仓比（日频 volume/oi，按日期对齐）===
vol_map = {d: v for d, v in d_vol}
oi_map = {d: v for d, v in d_oi}
ratio_pts = []
for d, v in d_close:
    if d in vol_map and d in oi_map and oi_map[d] and oi_map[d] != 0:
        ratio_pts.append([d, round(vol_map[d] / oi_map[d], 3)])
print("[POINTS] close=%d vol=%d oi=%d 月close=%d 成交持仓比=%d"
      % (len(d_close), len(d_vol), len(d_oi), len(m_close_m), len(ratio_pts)))

# === 图1：量价仓三联动 ===
h1, j1 = chart_pv(
    "echart_21_c1",
    "沪铅主力量价仓三联动（价格方向 + 资金参与度）",
    "上期所·主力连续 · 日 · 价格元/吨 / 量仓手 · j21_close %d 点 · 2011-03 至 %s" % (m_close["n"], latest(m_close)),
    d_close, "#b06a32", "收盘价", "元/吨",
    d_vol, "#5b98c9", "成交量", "手",
    d_oi, "#c9a227", "持仓量", "手",
    "什么时候看：判断铅价涨跌是否有资金参与、是趋势行情还是情绪反弹。<br>"
    "怎么看：价涨量增仓增 = 趋势确认（多头主动进场）；价涨量缩仓降 = 空头回补/情绪修复（不追）；"
    "价跌量增仓增 = 空头主导；持仓异常放大而价滞涨 = 高位分歧、警惕变盘。"
)

# === 图2：收盘价季节图（月末收盘价）===
h2, j2 = chart_line_t(
    "echart_21_c2",
    "沪铅主力月末收盘价季节图（近5年各一条线 + 图例标年份）",
    "上期所·主力连续 · 月 · 元/吨 · 日频聚月末 · 2011-03 至 %s" % latest(m_close),
    "#9b6bb5",
    m_close_m,
    "什么时候看：判断当前价格在历史季节性中的位置。<br>"
    "怎么看：切到季节视图后把近5年每月收盘价叠一起，今年这条线明显高于历史同期 = 基本面驱动偏强；"
    "贴着历史均值 = 季节性波动为主，突破/跌破需额外逻辑确认。",
    default_seasonal=True
)

# === 图3：成交持仓比 ===
h3, j3 = chart_line_t(
    "echart_21_c3",
    "沪铅主力成交持仓比（单位持仓对应的交易活跃度）",
    "上期所·主力连续 · 日 · 比值 · 成交量/持仓量 计算 · %d 点 · 至 %s" % (len(ratio_pts), latest(m_close)),
    "#5fb3a1",
    ratio_pts,
    "什么时候看：识别高位放量换手、筹码松动或趋势加速前的资金拥挤。<br>"
    "怎么看：比值持续高位 = 换手剧烈、短线资金主导，趋势不稳；比值低位放大伴随价格突破 = "
    "新资金进场、趋势可信度高。比值与价格同升 = 趋势加速信号。"
)

# === 页面专属说明 ===
NOTE = """<strong style="color:#c9d1d9">2.1 定义：</strong>盘面结构 = 期货价格方向 + 成交确认 + 持仓确认 + 多空结构确认四件事。<br>
<strong style="color:#c9d1d9">指标组：</strong>j21_close 沪铅主力连续收盘价(日,元/吨) · j21_volume 成交量(日,手) · j21_oi 持仓量(日,手)，数据源=zhiji 观服务 kline PB D（2011-03 至 2026-08-28，3751 交易日全量）。<br>
<strong style="color:#c9d1d9">口径说明：</strong>成交持仓比 = 成交量/持仓量（日频计算）；月末收盘价 = 日频聚合月频（取月末值）。<br>
<strong style="color:#c9d1d9">待外部源：</strong>前20会员多空持仓/持仓集中度（同花顺图3/4）知几料服务无数据，需上期所会员持仓排名接入。"""

html = page_html(
    "铅(PB) 2.1 盘面结构",
    "铅(PB) · 2 价格信号 · 2.1 盘面结构 · v1 3 图",
    "上期所",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 2.1 盘面结构 · v1（3 图全真数据 · 量价仓三联动 · 收盘价季节图）· indicators_v1.json v2.0",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
)
write_html("pb_21_price_structure.html", html)
