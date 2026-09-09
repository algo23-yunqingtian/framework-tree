#!/usr/bin/env python3
"""氧化铝(AO) 4.4 工厂库存子页 · v1 · 2 图真数据

图1 氧化铝厂内库存(正主)：wr52 厂内库存(周) —— 冶炼厂原料库存
图2 氧化铝库存-钢联(辅)：wr56 钢联库存(周) —— 社会库存
"""
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_ao44_c1", "echart_ao44_c2"]

m_mill = load_metric("wr52", code="AO")
m_society = load_metric("wr56", code="AO")

d_mill = pairs(m_mill)
d_society = pairs(m_society)

print("[POINTS] 厂内库存=%d 社会库存=%d" % (len(d_mill), len(d_society)))

h1, j1 = chart_line_t(
    "echart_ao44_c1",
    "氧化铝厂内库存（4.4 正主）",
    "厂内库存 · 周 · 万吨 · %d 点 · 至 %s" % (
        len(d_mill), latest(m_mill)),
    "#9a6b4f", d_mill,
    "什么时候看：4.4 工厂库存的正主图——判断冶炼厂原料库存水平。<br>"
    "怎么看：库存上行=原料充裕或消耗放缓=短期供应宽松。库存下行=消耗加快=供应偏紧。"
)

h2, j2 = chart_line_t(
    "echart_ao44_c2",
    "氧化铝社会库存·季节图",
    "钢联氧化铝库存 · 周 · 万吨 · %d 点 · 至 %s" % (
        len(d_society), latest(m_society)),
    "#5b98c9", d_society,
    "什么时候看：社会库存是厂内库存+流通环节的总量，反映整体库存水平。<br>"
    "怎么看：社会库存上行=全行业累库=供应过剩。社会库存下行=去库=供需偏紧。"
)

NOTE = """<strong style="color:#c9d1d9">4.4 定义：</strong>工厂库存 = 氧化铝厂内库存 + 社会库存，判断原料库存水平与供需平衡。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>wr52 厂内库存(万吨/周) —— 冶炼厂原料库存。<br>
<strong style="color:#c9d1d9">辅助指标：</strong>wr56 钢联氧化铝库存(万吨/周) · wr50 期货库存(仓单端)。<br>
<strong style="color:#c9d1d9">数据源：</strong>知几 API（ID01721655 厂内库存 + ID01721691 钢联库存）。<br>
<strong style="color:#c9d1d9">数据质量：</strong>厂内库存242点；社会库存242点(周度)。<br>
<strong style="color:#c9d1d9">4.x 边界：</strong>4.1=交易所库存 · 4.2=仓单 · 4.3=社会库存 · 4.4=工厂库存(正主=厂内库存) · 4.5=隐性在途。"""

html = page_html(
    "氧化铝(AO) 4.4 工厂库存",
    make_crumb("氧化铝", "AO", "4", "库存", "4.4", "工厂库存", "1", 2),
    "知几/钢联",
    h1, h2, "", NOTE,
    "有色金属产业指标树 · 氧化铝(AO) 4.4 工厂库存 · v1（2 图真数据 · 厂内库存 · 社会库存）· indicators_v1.json v3.82",
    j1 + "\n" + j2,
    CIDS,
    nav_back='<a href="index.html">← 回主站</a>',
)
write_html("ao_44_mill_inventory.html", html)
