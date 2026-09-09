#!/usr/bin/env python3
"""氧化铝(AO) 2.3 价格子页 · v1 · 3 图真数据（板块2·价格信号·海外价格）

图1 中国氧化铝平均价(正主)：wr40 中国平均价-氧化铝一级(日) —— 国内现货价格基准
图2 三网均价-山东(辅)：wr35 三网均价-山东(月) —— 主产区山东价格
图3 三网均价-内蒙古(辅)：wr34 三网均价-内蒙古(月) —— 新兴产区内蒙古价格
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao23_c1", "echart_ao23_c2", "echart_ao23_c3"]

m_avg = load_metric("wr40", code="AO")
m_sd = load_metric("wr35", code="AO")
m_nm = load_metric("wr34", code="AO")

d_avg = pairs(m_avg)
d_sd = pairs(m_sd)
d_nm = pairs(m_nm)

print("[POINTS] 平均价=%d 山东=%d 内蒙古=%d" % (
    len(d_avg), len(d_sd), len(d_nm)))

# === 图1：中国氧化铝平均价 ===
h1, j1 = chart_line_t(
    "echart_ao23_c1",
    "中国氧化铝平均价（2.3 正主）",
    "中国平均价-氧化铝一级 · 日 · 元/吨 · %d 点(2023起) · 至 %s" % (
        len(d_avg), latest(m_avg)),
    "#9a6b4f", d_avg,
    "什么时候看：2.3 海外价格的正主图——判断国内氧化铝现货价格基本面。<br>"
    "怎么看：价格上行=氧化铝供应偏紧或需求旺盛=冶炼利润扩张。"
    "价格下行=氧化铝供应过剩或需求疲软=冶炼利润收缩。"
    "与电解铝成本联动：氧化铝占电解铝成本60-70%，氧化铝价格直接影响电解铝利润。"
)

# === 图2：三网均价-山东 ===
h2, j2 = chart_line_t(
    "echart_ao23_c2",
    "三网均价-山东·季节图",
    "三网均价-山东 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_sd), latest(m_sd)),
    "#5b98c9", d_sd,
    "什么时候看：山东是中国氧化铝最大主产区，山东价格是行业定价基准。<br>"
    "怎么看：山东价格上行=主产区供应偏紧。价格下行=主产区供应过剩。"
)

# === 图3：三网均价-内蒙古 ===
h3, j3 = chart_line_t(
    "echart_ao23_c3",
    "三网均价-内蒙古·季节图",
    "三网均价-内蒙古 · 月 · 元/吨 · %d 点 · 至 %s" % (
        len(d_nm), latest(m_nm)),
    "#e06c75", d_nm,
    "什么时候看：内蒙古是新兴氧化铝产区，价格反映新产能投放对市场的冲击。<br>"
    "怎么看：内蒙古价格低于山东=新产能价格竞争激烈=行业利润承压。"
)

NOTE = """<strong style="color:#c9d1d9">2.3 定义：</strong>海外价格 = 中国氧化铝平均价 + 分地区三网均价，判断国内现货价格基本面与地区价差。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr40 中国平均价-氧化铝一级(元/吨/日) —— 国内现货价格基准。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr35 三网均价-山东(元/吨/月) · wr34 三网均价-内蒙古(元/吨/月) · wr38 三网均价-贵州(元/吨/月)。<br>
<strong style="color:#c9d1d9">排除项：</strong>海外FOB价格 → 2.3正主(wr88) · 电解铝价格 → AL板块 · 铝土矿价格 → AO 3.1.x。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID00188139 中国平均价 + ID01721687 山东 + ID01721686 内蒙古 + ID01721683 贵州）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>平均价1623点(2023-08起)；山东/内蒙古/贵州各68-20点(月度)。<br>
<strong style="color:#c9d1d9">2.x 边界：</strong>2.1=盘面结构(持仓/价/成交量) · 2.2=现货升贴水 · 2.3=海外价格(正主=中国平均价) · 2.4=月差结构 · 2.5=库存 · 2.6=加工费。"""

html = page_html(
    "氧化铝(AO) 2.3 价格",
    make_crumb("氧化铝", "AO", "2", "价格信号", "2.3", "海外价格", "1", 3),
    "知几/Mysteel",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 2.3 价格 · v1（3 图真数据 · 中国平均价 · 山东 · 内蒙古）· indicators_v1.json v3.82",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_23_price.html", html)
