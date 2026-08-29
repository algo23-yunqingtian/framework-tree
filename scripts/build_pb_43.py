#!/usr/bin/env python3
"""铅(PB) 4.3 社会库存子页 · v1 · 3 图全真数据（板块4 拆分重构，对齐板块2/6 范式）。

图1 全国社库 + 五地社库（chart_dual，Mysteel日频全国 vs SMM周频五地总计，双口径一致性）
图2 SMM五地社会库存拆分（chart_dual 主 + 图3 分地区明细，此处放广东/江苏代表两轴对比）
图3 Mysteel 全国铅锭现货库存（chart_line_t，日频高精度，含季节切换）

数据来源：api_cache.db（PB）。i31 Mysteel全国(768点) / i18 SMM五地总计(716点) /
i32广东 / i33江苏 / i34浙江 / i35天津 / i36上海（各616点,周度,2020-01起）。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        chart_triple, page_html, write_html, make_crumb)

CIDS = ["echart_43_c1", "echart_43_c2", "echart_43_c3"]

m31 = load_metric("i31")  # Mysteel 全国社库
m18 = load_metric("i18")  # SMM 五地社库总计
m32 = load_metric("i32")  # 广东
m33 = load_metric("i33")  # 江苏
m34 = load_metric("i34")  # 浙江
m35 = load_metric("i35")  # 天津
m36 = load_metric("i36")  # 上海

d31, d18 = pairs(m31), pairs(m18)
d32, d33, d34 = pairs(m32), pairs(m33), pairs(m34)
print("[POINTS] Mysteel全国=%d SMM五地=%d 广东=%d 江苏=%d 浙江=%d"
      % (len(d31), len(d18), len(d32), len(d33), len(d34)))

# === 图1：全国社库 + 五地社库（双口径） ===
h1, j1 = chart_dual(
    "echart_43_c1",
    "全国社库 vs 五地社库（双口径去库一致性）",
    "Mysteel全国(日) + SMM五地总计(周) · 万吨 · %d/%d 点 · 至 %s / %s"
    % (len(d31), len(d18), latest(m31), latest(m18)),
    d31, "#b06a32", "Mysteel全国", "万吨",
    d18, "#5b98c9", "SMM五地总计", "万吨",
    "什么时候看：判断国内社会库存的去化是否与全国同步。<br>"
    "怎么看：Mysteel全国(六市+全国口径)与SMM五地总计同向下行 = 去库信号一致、可信度高；"
    "全国去库而五地堆积 = 库存正从核心销区外溢到边缘地区，实际压力比五地口径更大。"
    "社库与交易所库存(4.1)叠加才是国内总库存。",
)

# === 图2：SMM五地分地区（三轴主要销区） ===
h2, j2 = chart_triple(
    "echart_43_c2",
    "SMM五地社库 · 主要销区结构",
    "广东 + 江苏 + 浙江（再生铅主销区） · 周 · 万吨 · 各%d点(2020-01起) · 至 %s"
    % (len(d32), latest(m32)),
    d32, "#c87070", "广东", "万吨",
    d33, "#5b98c9", "江苏", "万吨",
    d34, "#7a8c5b", "浙江", "万吨",
    "什么时候看：判断库存压力集中在哪个销区。<br>"
    "怎么看：广东+浙江是铅蓄电池主销区，库存占比上升 = 电池厂收货意愿弱、需求端偏冷；"
    "江苏是再生铅产业带，库存堆积 = 再生冶炼开工或出货受阻。"
    "天津、上海两地序列在库(i35/i36)，按取舍规则2未上图（信息量低于前三地），已入备用库。",
)

# === 图3：Mysteel 全国铅锭现货库存 ===
h3, j3 = chart_line_t(
    "echart_43_c3",
    "Mysteel全国铅锭现货库存（日频高精度）",
    "Mysteel铅锭现货库存 · 日 · 万吨 · %d 点 · 至 %s" % (len(d31), latest(m31)),
    "#b06a32",
    d31,
    "什么时候看：判断社会库存的短期变化节奏与季节性。<br>"
    "怎么看：日频序列对去库速度最敏感，配合季节视图看历年规律。铅社库通常Q1春节前去库、"
    "Q2累库、Q3-Q4去库（汽车产销旺季）。日度序列止2026-08，为最新可用数据。",
    default_seasonal=True,
)

NOTE = """<strong style="color:#c9d1d9">4.3 定义：</strong>社会库存 = 交易所之外的渠道库存（贸易商/加工厂/仓库），周度或日频，同步偏滞后，反映国内现货链路的真实压力。<br>
<strong style="color:#c9d1d9">指标组：</strong>i31 Mysteel全国社库(日) · i18 SMM五地总计(周) · i32广东 · i33江苏 · i34浙江 · i35天津 · i36上海(周)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>i31 768点(2018-01起) / i18 716点 / i32~i36 各616点(2020-01起)。<br>
<strong style="color:#c9d1d9">口径与边界：</strong>交易所显性库存属 4.1；工厂/原料端库存属 4.4；隐性在途属 4.5。<strong>Mysteel六市分城市</strong>(江西等)在知几无序列，按取舍规则3以全国日频替代并标「待外部源」。<br>
<strong style="color:#c9d1d9">拆分说明：</strong>本页由 pb_stock_v2.html 4.3 面板拆分而来，3图全部保留；新增图2 五地分地区（原v2仅在4.3面板内嵌，此次提为独立图）。"""

html = page_html(
    "铅(PB) 4.3 社会库存",
    make_crumb("铅", "PB", "4", "库存", "4.3", "社会库存", "1", 3),
    "Mysteel · SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 4.3 社会库存 · v1（3 图全真数据 · 双口径 · 五地销区结构 · 全国日频季节）· indicators_v1.json v2.5",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="pb_4_overview.html">← 回板块4总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_43_social_stock.html", html)
