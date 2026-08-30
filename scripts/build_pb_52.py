#!/usr/bin/env python3
"""铅(PB) 5.2 终端细分消费子页 · v1 · 3 图全真数据（指标树填充板块5·需求·第2子节点）。

图1 汽车销量 vs 铅蓄电池成品库存（chart_dual）：j52_car_sales 汽车销量 + j52_battery_inv 成品库存
    —— 汽车是铅蓄电池最大终端下游（占消费50%+），销量=终端需求正主；成品库存=终端备货验证。
图2 汽车销量季节图（chart_line_t seasonal）：近5年历年线，观察汽车销量季节性规律。
图3 基站设备产量 vs 铅蓄电池成品库存（chart_dual）：j52_base_station 基站设备产量 + j52_battery_inv 成品库存
    —— 通信基站(UPS备电)是铅蓄电池重要下游，设备产量反映通信基建需求。

数据源：SMM 中国汽车产销量(a10128004 月) + Mysteel 移动通信基站设备(CM0000017742 月) + SMM 铅蓄电池成品库存(a12813406 月)。
备用（未入正主）：电动两轮车/储能装机（知几无月度数据）；铅蓄电池出口量（归 6.3 制品出口，5.x 只做国内消费）。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html,
                        make_crumb)

CIDS = ["echart_52_c1", "echart_52_c2", "echart_52_c3"]

m_car = load_metric("j52_car_sales")
m_bs = load_metric("j52_base_station")
m_inv = load_metric("j52_battery_inv")

d_car = pairs(m_car)
d_bs = pairs(m_bs)
d_inv = pairs(m_inv)

print("[POINTS] 汽车销量=%d 基站设备=%d 成品库存=%d" % (
    len(d_car), len(d_bs), len(d_inv)))

# === 图1：汽车销量 vs 铅蓄电池成品库存 ===
h1, j1 = chart_dual(
    "echart_52_c1",
    "汽车销量 vs 铅蓄电池成品库存（5.2 正主）",
    "SMM 中国汽车销量 · 月 · 万辆 / SMM 铅蓄电池成品库存 · 月 · KVAh · %d/%d 点 · 至 %s" % (
        len(d_car), len(d_inv), latest(m_car)),
    d_car, "#5b98c9", "汽车销量", "万辆",
    d_inv, "#e06c75", "铅蓄电池成品库存", "KVAh",
    "什么时候看：5.2 终端细分的正主图——判断汽车终端对铅蓄电池的真实需求。<br>"
    "怎么看：汽车销量上行=汽车后市场铅需求走强=终端消费偏强；成品库存下行=终端去库=消费强于供给。"
    "两条线同向(销量升+库存降)=终端消费真实改善；背离(销量升+库存升)=终端备货观望，需求质量存疑。"
    "最新(2026-06)：汽车销量约200万辆、成品库存约1200 KVAh。"
)

# === 图2：汽车销量季节图 ===
h2, j2 = chart_line_t(
    "echart_52_c2",
    "汽车销量·季节图",
    "SMM 中国汽车销量 · 月 · 万辆 · %d 点(2020起) · 至 %s" % (
        len(d_car), latest(m_car)),
    "#5b98c9", d_car,
    "什么时候看：判断汽车销量的月度季节性规律。<br>"
    "怎么看：春节月(2月)销量低谷，3-4月快速恢复；6-7月淡季，9-10月旺季(金九银十)，Q4为全年高位。"
    "2020年2月受疫情冲击创历史极低值，新能源车渗透率快速提升拉高2024年后基线。"
)

# === 图3：基站设备产量 vs 铅蓄电池成品库存 ===
h3, j3 = chart_dual(
    "echart_52_c3",
    "基站设备产量 vs 铅蓄电池成品库存（通信终端）",
    "Mysteel 移动通信基站设备产量 · 月 · 万信道 / SMM 铅蓄电池成品库存 · 月 · KVAh · %d/%d 点 · 至 %s" % (
        len(d_bs), len(d_inv), latest(m_bs)),
    d_bs, "#5fb3a1", "基站设备产量", "万信道",
    d_inv, "#b06a32", "铅蓄电池成品库存", "KVAh",
    "什么时候看：判断通信基建对铅蓄电池(UPS备电)的需求传导。<br>"
    "怎么看：基站设备产量上行=通信基建投入增加=UPS备电需求走强=终端消费增量。"
    "成品库存下行=终端去库加速=通信备电需求真实。"
    "基站设备产量与成品库存背离=通信备电需求分化(新建vs替换)。"
    "最新(2026-07)：基站设备产量约35万信道、成品库存约1200 KVAh。"
)

NOTE = """<strong style="color:#c9d1d9">5.2 定义：</strong>终端细分消费 = 铅蓄电池在终端行业的滞后消耗。汽车(50%+)/通信基站(15%)/储能(10%)是三大终端，汽车是最大下游。
<strong style="color:#c9d1d9">指标组（正主）：</strong>j52_car_sales 汽车销量(万辆/月) · j52_base_station 基站设备产量(万信道/月) · j52_battery_inv 铅蓄电池成品库存(KVAh/月)。<br>
<strong style="color:#c9d1d9">备用指标（不入正主）：</strong>电动两轮车产量（知几无月度数据，需外部源：中商情报网/中国自行车协会） · 储能装机量（知几仅有省份级年度数据，无全国月度）。两者保留在发散记录排除项供后续启用。<br>
<strong style="color:#c9d1d9">排除项（归属其他节点）：</strong>铅蓄电池出口量(a10017078/i37) → 6.3 制品出口 · 铅蓄电池进口量(a10017043) → 6.x 进出口 · 铅锭消费量(j51_cons) → 5.1 初级消费。5.x 只做国内消费，不做进出口。<br>
<strong style="color:#c9d1d9">数据源：</strong>SMM 中国汽车产销量(a10128004, 月度102点/2020起) + Mysteel 移动通信基站设备(CM0000017742, 月度85点/2020起) + SMM 铅蓄电池成品库存(a12813406, 月度31点/2023起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>汽车销量 102点(2020-01起)；基站设备 85点(2020-03起)；成品库存 31点(2023-01起，较短)。<br>
<strong style="color:#c9d1d9">5.1/5.2/5.3 边界：</strong>5.1 = 开工率·同步（正主）+ 表观/实际消费验证；5.2 = 终端细分·滞后（汽车/通信基站/成品库存）；5.3 = 需求先行1-2月（排产/订单/经销商库存）。出口图已在 6.3(HS8507) 做过，5.x 只做国内消费。<br>
<strong style="color:#c9d1d9">缺口：</strong>电动两轮车/储能装机在知几无月度数据，需外部源（中商情报网/高工储能/工信部）补充。</strong>"""

html = page_html(
    "铅(PB) 5.2 终端细分消费",
    make_crumb("铅", "PB", "5", "需求", "5.2", "终端细分消费", "2", 3),
    "SMM/Mysteel",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 5.2 终端细分消费 · v1（3 图全真数据 · 汽车销量+成品库存 · 季节规律 · 基站设备+成品库存）· indicators_v1.json v2.8",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,

    nav_back='<a href="pb_5_overview.html">← 回板块5总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_52_terminal_consumption.html", html)
