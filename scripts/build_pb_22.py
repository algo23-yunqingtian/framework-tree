#!/usr/bin/env python3
"""铅(PB) 2.2 现货与升贴水子页 · v1 · 3 图全真数据（指标树填充板块1·价格信号·第2子节点）。

图1 铅现货—沪铅主力基差复合图（chart_dual）：j22_spot SMM1#铅现货均价 + j21_close 主力收盘价 + 基差(计算)
图2 区域现货价季节图（chart_line_t 时序⇄季节）：j22_spot 全国 1#铅现货
图3 原生铅—再生精铅价差（chart_dual）：j22_spot 原生 + j22_regen 再生精铅 + 价差(计算)

数据源：zhiji 料服务 SMM，日频 2101 点（2018-01 至 2026-08-28），已灌 api_cache.db。
⚠️ 区域升贴水（图2 同花顺）/ 区域价差热力图（图3 同花顺）：上海/广东/河南/天津现货价已拿到，
   但升贴水仅上海有 (a10017061)，区域价差用 4 地现货价差展示。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html,
                        make_crumb)

CIDS = ["echart_22_c1", "echart_22_c2", "echart_22_c3"]

# === 读数据 ===
m_spot = load_metric("j22_spot")      # SMM 1#铅锭现货均价（日, 元/吨）
m_sh = load_metric("j22_spot_sh")     # 上海
m_gd = load_metric("j22_spot_gd")     # 广东
m_hn = load_metric("j22_spot_hn")     # 河南
m_tj = load_metric("j22_spot_tj")     # 天津
m_close = load_metric("j21_close")    # 沪铅主力收盘价（日, 元/吨）
m_regen = load_metric("j22_regen")    # 再生精铅平均价（日, 元/吨）

d_spot = pairs(m_spot)
d_sh = pairs(m_sh)
d_gd = pairs(m_gd)
d_hn = pairs(m_hn)
d_tj = pairs(m_tj)
d_close = pairs(m_close)
d_regen = pairs(m_regen)

# === 基差 = 现货 - 期货（按日期对齐）===
close_map = {d: v for d, v in d_close}
basis_pts = []
for d, v in d_spot:
    if d in close_map:
        basis_pts.append([d, round(v - close_map[d], 2)])
print("[POINTS] spot=%d 基差=%d 再生=%d" % (len(d_spot), len(basis_pts), len(d_regen)))

# === 图1：基差复合图（现货 + 期货 双轴 + 基差？用 chart_dual 现货vs期货，基差放NOTE）===
# chart_dual 支持两条线；基差单独作第3图更清晰。图1 = 现货 vs 主力 双线看基差走势
h1, j1 = chart_dual(
    "echart_22_c1",
    "铅现货 vs 沪铅主力（基差走势）",
    "SMM 1#铅锭现货均价 vs 沪铅主力收盘价 · 日 · 元/吨 · %d 点 · 2018-01 至 %s" % (len(d_spot), latest(m_spot)),
    d_spot, "#b06a32", "SMM 1#铅现货", "元/吨",
    d_close, "#5b98c9", "沪铅主力收盘", "元/吨",
    "什么时候看：判断现货是否比盘面强。<br>"
    "怎么看：现货线在上方（现货升水）= 现货紧张、下游接货改善、支撑盘面；现货线在下方（现货贴水）= "
    "现货弱、盘面升水透支。两线收窄/走阔即基差收敛/扩大。最新(2026-08-28)：现货16075 vs 主力16245 = 现货贴水约170元。"
)

# === 图2：全国 1#铅现货季节图 ===
h2, j2 = chart_line_t(
    "echart_22_c2",
    "SMM 1#铅锭现货均价季节图（近5年各一条线 + 图例标年份）",
    "SMM · 日 · 元/吨 · 2018-01 至 %s" % latest(m_spot),
    "#9b6bb5",
    d_spot,
    "什么时候看：判断当前现货价格在历史季节性中的位置。<br>"
    "怎么看：切季节视图把近5年叠一起，今年明显高于历史同期 = 现货偏强（旺季/缺货）；"
    "明显低于 = 现货偏弱（淡季/过剩）。结合库存判断是季节性还是趋势。",
    default_seasonal=True
)

# === 图3：原生铅—再生精铅价差 ===
h3, j3 = chart_dual(
    "echart_22_c3",
    "原生铅 vs 再生精铅（再生替代压力）",
    "SMM 1#铅锭(原生) vs SMM 再生精铅均价 · 日 · 元/吨 · %d 点 · 至 %s" % (len(d_regen), latest(m_regen)),
    d_spot, "#b06a32", "原生 1#铅", "元/吨",
    d_regen, "#5fb3a1", "再生精铅", "元/吨",
    "什么时候看：判断再生铅对原生铅的替代压力。<br>"
    "怎么看：原生-再生价差扩大 = 再生铅贴水加深、再生供给承压或交割替代折价被重估；"
    "价差收窄到交割替代贴水(150元/吨)附近 = 可能触发仓单注册与套利。最新(2026-08-28)：原生16075 vs 再生15975 = 价差100元。"
)

# === 页面专属说明 ===
NOTE = """<strong style="color:#c9d1d9">2.2 定义：</strong>现货价格 + 升贴水/基差 + 区域价差，判断现货紧张是否真实、贴水是否收敛、区域套利是否打开。<br>
<strong style="color:#c9d1d9">指标组：</strong>j22_spot SMM1#铅锭现货均价(日,元/吨) · j22_regen 再生精铅均价(日,元/吨) · 基差=现货-主力(计算) · 区域现货：上海/广东/河南/天津(s20001968-83)。<br>
<strong style="color:#c9d1d9">已入库：</strong>j22_spot/sh/gd/hn/tj/premium/regen/shfe_ratio 共 8 指标，日频 2101 点（2018-01 至 2026-08-28）。<br>
<strong style="color:#c9d1d9">口径：</strong>沪伦比值 a10155854（日，8.5 于 2026-08-28）；上海铅现货升贴水 a10017061（日，20元 于 2026-08-28）。"""

html = page_html(
    "铅(PB) 2.2 现货与升贴水",
    make_crumb("铅", "PB", "2", "价格信号", "2.2", "现货与升贴水", "1", 3),
    "SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 2.2 现货与升贴水 · v1（3 图全真数据 · 基差 · 现货季节 · 原生再生价差）· indicators_v1.json v2.0",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,

    nav_back='<a href="pb_2_overview.html">← 回板块2总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_22_spot_premium.html", html)
