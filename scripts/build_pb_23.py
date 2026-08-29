#!/usr/bin/env python3
"""铅(PB) 2.3 海外价格子页 · v1 · 3 图全真数据（指标树填充板块1·价格信号·第3子节点）。

图1 LME铅期限结构（chart_dual）：j23_lme_cash 现货结算 + j23_lme_3m 官方3M（现货升水=Back/Contango）
图2 LME铅现货价季节图（chart_line_t 时序⇄季节）：j23_lme_cash 现货结算
图3 海外升贴水与进口盈亏（chart_dual）：j23_lme_sp3 现货/3M升贴水 + j23_imp_profit 进口盈亏

数据源：zhiji 料服务 LME/SMM。现货2945点(2015-01起)，3M 1056点(2022-06起)，升贴水2942点，进口盈亏1896点(2018-10起)。
⚠️ COMEX铅价知几无 → 图3同花顺(COMEX联动)放弃；沪伦比(2.2已入库)并入进口盈亏NOTE。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html,
                        make_crumb)

CIDS = ["echart_23_c1", "echart_23_c2", "echart_23_c3"]

m_cash = load_metric("j23_lme_cash")
m_3m = load_metric("j23_lme_3m")
m_sp3 = load_metric("j23_lme_sp3")
m_imp = load_metric("j23_imp_profit")

d_cash = pairs(m_cash)
d_3m = pairs(m_3m)
d_sp3 = pairs(m_sp3)
d_imp = pairs(m_imp)
print("[POINTS] cash=%d 3m=%d sp3=%d imp=%d" % (len(d_cash), len(d_3m), len(d_sp3), len(d_imp)))

# === 图1：LME铅期限结构（现货 vs 3个月）===
h1, j1 = chart_dual(
    "echart_23_c1",
    "LME铅现货 vs 官方3个月（期限结构）",
    "LME 现货结算价 vs 官方3M卖价 · 日 · 美元/吨 · 现货%d点(2015起) / 3M %d点(2022-06起) · 至 %s" % (len(d_cash), len(d_3m), latest(m_cash)),
    d_cash, "#b06a32", "LME现货结算", "美元/吨",
    d_3m, "#5b98c9", "LME官方3M", "美元/吨",
    "什么时候看：判断海外铅现货紧不紧。<br>"
    "怎么看：现货在3个月上方（现货升水/Backwardation）= 现货抢货、近端紧张、可能逼仓；"
    "现货在下方（Contango）= 库存宽松、远期更贵。最新(2026-08-28)：现货1880 vs 3M 1911 = 现货贴水约31美元。"
)

# === 图2：LME铅现货结算价季节图 ===
h2, j2 = chart_line_t(
    "echart_23_c2",
    "LME铅现货结算价季节图（近5年各一条线 + 图例标年份）",
    "LME · 日 · 美元/吨 · %d 点 · 2015-01 至 %s" % (len(d_cash), latest(m_cash)),
    "#9b6bb5",
    d_cash,
    "什么时候看：判断当前LME铅价在历史季节性中的位置。<br>"
    "怎么看：切季节视图把近5年叠一起，今年明显高于历史同期 = 海外价格强势（去库/逼仓）；"
    "明显低于 = 海外价格弱势（累库/需求差）。结合LME库存判断。",
    default_seasonal=True
)

# === 图3：海外升贴水 + 进口盈亏 ===
h3, j3 = chart_dual(
    "echart_23_c3",
    "LME升贴水 vs 铅进口盈亏（内外传导）",
    "LME(现货/3个月)升贴水 + SMM进口盈亏(现货) · 日 · 升贴水美元/吨 · 进口盈亏元/吨 · %d 点 · 至 %s" % (len(d_imp), latest(m_imp)),
    d_sp3, "#5fb3a1", "LME现货/3M升贴水", "美元/吨",
    d_imp, "#e5c07b", "铅进口盈亏", "元/吨",
    "什么时候看：海外现货松紧 + 进口窗口是否打开。<br>"
    "怎么看：升贴水转正并扩大 = 海外现货紧张（利多外盘）；进口盈亏转正 = 进口窗口打开、海外偏贵将引流入、压制国内升水。"
    "最新(2026-08-28)：LME升贴水-35美元(Contango) + 进口盈亏16200元(大幅转正=进口有利)。沪伦比值(j22_shfe_ratio 8.5)并入2.2页。"
)

NOTE = """<strong style="color:#c9d1d9">2.3 定义：</strong>海外价格（LME/COMEX），判断海外现货松紧、期限结构与内外价差传导。<br>
<strong style="color:#c9d1d9">指标组：</strong>j23_lme_cash LME现货结算(美元/吨) · j23_lme_3m 官方3M卖价 · j23_lme_0to3/02...0to3 0-3月升贴水 · j23_imp_profit 进口盈亏(元/吨) · j22_shfe_ratio 沪伦比(2.2入库)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>现货结算 2945点(2015-01至2026-08-28) 全量；官方3M 1056点(2022-06起,因LME数据源启始晚)；升贴水 2942点；进口盈亏 1896点(2018-10起)。<br>
<strong style="color:#c9d1d9">未覆盖：</strong>COMEX铅价(知几无,仅库存/出入库 g0286...)、LME 15个月远期价(未取)、美元兑人民币(汇率环节)。"""

html = page_html(
    "铅(PB) 2.3 海外价格",
    make_crumb("铅", "PB", "2", "价格信号", "2.3", "海外价格", "1", 3),
    "LME / SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 2.3 海外价格 · v1（3 图全真数据 · LME期限结构 · 现货季节 · 升贴水与进口盈亏）· indicators_v1.json v2.2",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,

    nav_back='<a href="pb_2_overview.html">← 回板块2总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_23_overseas_price.html", html)
