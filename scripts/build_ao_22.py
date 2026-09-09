#!/usr/bin/env python3
"""氧化铝(AO) 2.2 现货与升贴水子页 · v1 · 2 图真数据。

AO 是第 9 个独立品种节点（v3.80），对应 tree_config.json p2 子节点。
数据源：zhiji 料服务 SMM/中国铝网。
- 图1 三网长单均价 内蒙古 vs 山东（chart_dual）：wr34 内蒙(月) + wr35 山东(月)
- 图2 中国氧化铝一级平均价季节图（chart_line_t 时序⇄季节）：wr40(日)
- wr38 贵州长单均价 / wr28 建成产能 等并入 NOTE

数据量：wr34/35 各 68 点(2021-01~2026-08 月) · wr40 2121 点(2018-01~2026-09 日)
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao22_c1", "echart_ao22_c2"]

m_nm = load_metric("wr34", code="AO")
m_sd = load_metric("wr35", code="AO")
m_cn = load_metric("wr40", code="AO")

d_nm = pairs(m_nm)
d_sd = pairs(m_sd)
d_cn = pairs(m_cn)
print("[POINTS] 内蒙=%d 山东=%d 中国一级=%d" % (len(d_nm), len(d_sd), len(d_cn)))

# === 图1：三网长单均价 内蒙古 vs 山东 ===
h1, j1 = chart_dual(
    "echart_ao22_c1",
    "氧化铝三网长单均价：内蒙古 vs 山东",
    "SMM 三网长单均价 · 月 · 元/吨 · 内蒙%d点 / 山东%d点 · 2021-01 至 %s" % (len(d_nm), len(d_sd), latest(m_nm)),
    d_nm, "#b06a32", "内蒙古长单均价", "元/吨",
    d_sd, "#5b98c9", "山东长单均价", "元/吨",
    "什么时候看：氧化铝两大主产区（西北内蒙 vs 华东山东）长单定价走势。<br>"
    "怎么看：内蒙通常高于山东（运费+电力成本，内蒙火电+新疆进口矿成本传导）；"
    "两线价差扩大 = 区域供需分化（内蒙矿端紧张 vs 山东消费偏弱）；"
    "贵州长单均价(wr38) 同口径可叠加。长单均价是氧化铝行业定价基准，反映冶炼厂与电解铝厂的月度议定价格。"
)

# === 图2：中国氧化铝一级平均价季节图 ===
h2, j2 = chart_line_t(
    "echart_ao22_c2",
    "中国氧化铝一级平均价季节图（近5年各一条线 + 图例标年份）",
    "中国平均价-氧化铝一级 · 日 · 元/吨 · %d 点 · 2018-01 至 %s" % (len(d_cn), latest(m_cn)),
    "#9b6bb5",
    d_cn,
    "什么时候看：判断当前国内氧化铝现货价在历史季节性中的位置。<br>"
    "怎么看：切季节视图把近5年叠一起，今年明显高于历史同期 = 矿端紧张、氧化铝走强（利多）；"
    "明显低于 = 供给宽松（累库/进口矿充裕）。结合矿端发运量(wr60-71)与开工率(wr57)判断驱动。"
    "2022-2023 年氧化铝因铝土矿供给冲击曾大幅冲高。",
    default_seasonal=True
)

NOTE = """<strong style="color:#c9d1d9">2.2 定义：</strong>氧化铝现货价格与长单定价，判断矿端成本传导与冶炼溢价。<br>
<strong style="color:#c9d1d9">指标组：</strong>wr34 内蒙长单均价(月) · wr35 山东长单均价(月) · wr38 贵州长单均价(月) · wr40 中国一级平均价(日) · wr39 东澳FOB / wr41 印尼FOB / wr44 澳洲FOB（海外FOB，SMM源，待凭据） · wr43 现货vs长协价差（衍生，需两序列做差）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>wr34/35/38 各 68 点(2021-01~2026-08 月) 全量 verified；wr40 2121 点(2018-01~2026-09 日) 全量 verified。海外FOB(wr39/41/44) 与 spot-vs-长协(wr43) 为 SMM 源待凭据修复后补。<br>
<strong style="color:#c9d1d9">未覆盖：</strong>长单vs现货价差衍生(wr43，需两序列做差)、海外FOB三区域(SMM源 a1 前缀，凭据 code=10017 超限待修)、氧化铝开工率(wr57 单条未 verified)。<br>
<strong style="color:#c9d1d9">产业链位置：</strong>铝土矿(wr60-71) → 氧化铝(wr28-59,本页) → 电解铝(AL板块)。氧化铝是电解铝前驱，价格受矿端供给与电力成本双重驱动。"""

html = page_html(
    "氧化铝(AO) 2.2 现货与升贴水",
    make_crumb("氧化铝", "AO", "2", "价格", "2.2", "现货与升贴水", "1", 2),
    "SMM / 中国铝网",
    h1, h2, "", NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 2.2 现货与升贴水 · v1（2 图真数据 · 三网长单均价对比 · 中国一级价季节）· indicators_v1.json v3.81",
    j1 + "\n" + j2,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_22_spot.html", html)
