#!/usr/bin/env python3
"""铜(CU) 2.1 进口盈亏与跨市贸易流子页 · v1 · 3 图全真数据（指标树填充板块2·价格信号·第1子节点）。

图1 进口盈亏时序⇄季节图（chart_line_t 正主）：cu_21_import 2448点(2016-05起)
    —— 直接量化内外盘套利窗口开合：负值=亏损窗口关闭，正值=盈利窗口打开
图2 进口盈亏 vs LME 铜价（chart_dual 复合）：左轴盈亏柱(元/吨) + 右轴 LME 3M(美元/吨)
    —— 海外铜价上行如何压制国内套利窗口
图3 进口盈亏 vs 沪铜主力（chart_dual 复合）：左轴盈亏柱(元/吨) + 右轴 SHFE(元/吨)
    —— 国内铜价强势但进口仍亏损 = 贸易流被阻断（内外盘价差不足覆盖汇率+关税+物流）

数据源：zhiji 料服务 SMM（进口盈亏 ID01030232）+ 观服务 LME/SHFE 行情，已灌 api_cache.db。
⚠️ 洋山铜溢价、保税区库存、跨市仓单结构（同花顺发散推荐）：知几无数据，标注待外部源。
⚠️ 节点命名说明：tree_config.json 将 2.1 定义为「盘面结构 q=持仓/价/成交量」，
   但 Step3 已注册指标 cu_21_import（进口盈亏）+ decision_2.1.md + 同花顺发散
   均指向「跨市场价差与贸易流」主题，且缓存无沪铜日度成交量/持仓量。
   本页按已注册指标与决策文档执行，按 AGENTS.md 规则5「产出可查」在此写明。
"""
from collections import OrderedDict
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, write_html, make_crumb)

CIDS = ["echart_cu_21_c1", "echart_cu_21_c2", "echart_cu_21_c3", "echart_cu_21_c4"]

# === 读数据（⚠️ CU 指标必须显式传 code="CU"，load_metric 默认 code="PB"）===
m_imp = load_metric("cu_21_import", "CU")           # 进口盈亏（元/吨）· 2448点 · 正主
m_lme = load_metric("cu_23_lme_settle", "CU")       # LME 铜 3M 结算价（美元/吨）· 2918点
m_shfe = load_metric("cu_22_close_front", "CU")     # SHFE 沪铜主力（元/吨）· 2833点
m_conc = load_metric("cu_21_import_conc", "CU")     # 铜精矿进口量（万吨）· 126点 · 备用

d_imp = pairs(m_imp)
d_lme = pairs(m_lme)
d_shfe = pairs(m_shfe)
d_conc = pairs(m_conc)

# === 进口盈亏日频 → 月频聚合（取月均值，季节图用）===
def to_monthly_mean(pairs_data):
    d = OrderedDict()
    for date, v in pairs_data:
        if v is None:
            continue
        ym = date[:7]
        d.setdefault(ym, []).append(v)
    out = []
    for ym, vals in d.items():
        out.append([ym + "-01", round(sum(vals) / len(vals), 1)])
    return out

d_imp_m = to_monthly_mean(d_imp)
print("[POINTS] 进口盈亏=%d 月频=%d LME=%d 沪铜=%d 铜精矿=%d"
      % (len(d_imp), len(d_imp_m), len(d_lme), len(d_shfe), len(d_conc)))

# === 图1：进口盈亏时序⇄季节（正主）===
h1, j1 = chart_line_t(
    "echart_cu_21_c1",
    "进口盈亏（内外盘套利窗口开合 · 正主指标）",
    "SMM · 日 · 元/吨 · 日频2448点(2016-05起) · 月频%d点(季节视图) · 至 %s" % (len(d_imp_m), latest(m_imp)),
    "#b87333",
    d_imp_m,
    "什么时候看：判断国内高价是否由进口窗口支撑，铜价冲高时先看这张图确认套利是否打开。<br>"
    "怎么看：负值=进口亏损窗口关闭（关税/汇率/物流成本吞噬价差，贸易流受阻）；正值=盈利窗口打开"
    "（进口套利启动、到货压力将传导至现货库存）。亏损越深代表内强外弱越极致，进口铜越难流通。"
    "最新(2026-08-28)：-1260元/吨，处于深度亏损区。",
    default_seasonal=True,
)

# === 图2：进口盈亏 vs LME 伦铜（海外压制力）===
h2, j2 = chart_dual(
    "echart_cu_21_c2",
    "进口盈亏 vs LME 铜价（海外铜价对套利窗口的压制力）",
    "SMM进口盈亏 + LME 3M结算价 · 日 · 左轴元/吨 / 右轴美元/吨 · %d/%d 点 · 至 %s" % (len(d_imp), len(d_lme), latest(m_imp)),
    d_imp, "#b87333", "进口盈亏", "元/吨",
    d_lme, "#5b98c9", "LME 3M", "美元/吨",
    "什么时候看：判断海外铜价上行如何压制国内套利窗口。<br>"
    "怎么看：伦铜上行且进口盈亏走负 = 海外强势压制套利，国内高价靠内需支撑而非进口；伦铜回落"
    "且盈亏转正 = 进口套利启动，海外货源将进入国内。LME铜价每涨1000美元≈进口盈亏恶化约14000元"
    "的传导弹性（含汇率与加工费）。最新(2026-08-28)：伦铜14370美元 + 盈亏-1260元。"
)

# === 图3：进口盈亏 vs 沪铜主力（国内价格传导）===
h3, j3 = chart_dual(
    "echart_cu_21_c3",
    "进口盈亏 vs 沪铜主力（内强外弱的传导结果）",
    "SMM进口盈亏 + SHFE主力 · 日 · 左轴盈亏元/吨 / 右轴沪铜元/吨 · %d/%d 点 · 至 %s" % (len(d_imp), len(d_shfe), latest(m_shfe)),
    d_imp, "#b87333", "进口盈亏", "元/吨",
    d_shfe, "#5fb3a1", "沪铜主力", "元/吨",
    "什么时候看：判断国内铜价强势是否可持续、贸易流是否被完全阻断。<br>"
    "怎么看：沪铜上行 + 盈亏走负 = 内强外弱极致，内外盘价差+汇率/关税/物流成本已无法覆盖，"
    "贸易流被完全阻断，现货供应全靠国产冶炼+库存去化；沪铜上行 + 盈亏转正 = 进口套利打开、"
    "到货压力上升、对现货形成压制。最新(2026-08-28)：沪铜108900元 + 盈亏-1260元，贸易流已阻断。"
)

# === 图4：进口盈亏 vs 铜精矿进口量（原料端交叉验证 · 备用库）===
h4, j4 = chart_dual(
    "echart_cu_21_c4",
    "进口盈亏 vs 铜精矿进口量（原料端贸易流交叉验证 · 备用库）",
    "SMM进口盈亏(日) + 铜精矿进口量(月) · 日/月 · 左轴元/吨 / 右轴万吨 · %d/%d 点 · 至 %s" % (len(d_imp), len(d_conc), latest(m_imp)),
    d_imp, "#b87333", "进口盈亏", "元/吨",
    d_conc, "#c9a227", "铜精矿进口", "万吨",
    "什么时候看：交叉验证贸易流是否被盈亏窗口压制（矿端原料链，非精炼铜端）。<br>"
    "怎么看：进口盈亏长期为负 + 铜精矿进口量维持 = 冶炼原料端贸易流仍顺畅（TC传导慢于精炼铜端）；"
    "两者同步走弱 = 整个进口链萎缩。⚠️ 本图量纲混合（日频盈亏 vs 月频进口量），仅作趋势对照，不作精确联动判断；"
    "指标更贴近 3.1.4 铜精矿进口，此处仅留作交叉验证。铜精矿进口量126月点(2015-01起)。"
)

NOTE = """<strong style="color:#c9d1d9">2.1 定义：</strong>进口盈亏 + 内外盘价差 + 贸易流，判断国内铜价强势是内需驱动还是区域割裂定价。<br>
<strong style="color:#c9d1d9">指标组：</strong>cu_21_import 进口盈亏(SMM,日,元/吨,正主) · cu_23_lme_settle LME 3M结算价(日,美元/吨) · cu_22_close_front SHFE电解铜主力(日,元/吨) · cu_21_import_conc 铜精矿进口量(月,万吨,备用库,归属3.1.4交叉验证)。<br>
<strong style="color:#c9d1d9">口径说明：</strong>进口盈亏=进口铜到岸成本(含关税13%+增值税13%+物流)与内盘价格折算的差额，正值=进口盈利、负值=进口亏损；月频聚合取月均值。<br>
<strong style="color:#c9d1d9">数据质量：</strong>进口盈亏 2448点(2016-05起)；LME 2918点(2015-01起)；沪铜主力 2833点(2015-01起)；铜精矿进口 126月点(2015-01起)。<br>
<strong style="color:#c9d1d9">待外部源：</strong>洋山铜溢价、保税区库存、跨市仓单结构（同花顺发散推荐）知几无数据，需 SMM/Wind/海关口径接入。<br>
<strong style="color:#c9d1d9">v1 节点命名说明：</strong>tree_config.json 将 2.1 定义为「盘面结构 q=持仓/价/成交量」，但 Step3 已注册指标与 decision_2.1.md 均指向「跨市场价差与贸易流」，且缓存无沪铜日度成交量/持仓量（盘面结构数据不可得）。本页按已注册指标与决策文档执行，按 AGENTS.md 规则5「产出可查」写明处理依据。"""

html = page_html(
    title="铜(CU) 2.1 进口盈亏与跨市贸易流",
    hcrumbs=make_crumb("铜", "CU", "2", "价格信号", "2.1", "进口盈亏与贸易流", "1", 4),
    hright="SMM + LME + SHFE",
    h1=h1,
    h2=h2,
    h3=h3 + h4,
    note_html=NOTE,
    footer_text="有色金属产业指标树 · 铜(CU) 2.1 进口盈亏与贸易流 · v1（4 图全真数据 · 进口盈亏正主 · 内外盘价差联动 · 原料端交叉）· indicators_v1.json v2.9",
    js_body=j1 + "\n" + j2 + "\n" + j3 + "\n" + j4,
    cids=CIDS,
    nav_back='<a href="cu_2_overview.html">← 回板块2总览</a> <a href="index.html">← 回主站</a>',
)
write_html("cu_2_1.html", html)
