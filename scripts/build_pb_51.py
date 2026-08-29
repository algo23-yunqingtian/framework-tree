#!/usr/bin/env python3
"""铅(PB) 5.1 初级消费子页 · v2 · 3 图全真数据（指标树填充板块5·需求·第1子节点）。

v2 修正（主脑验收 T11）：
  · 图3 由「社库 vs 硫酸价格」改为「铅酸电池开工率 + 铅锭消费验证」
  · 归属规则1（正主优先）：i18 铅锭社库=4.3 库存正主、硫酸价=7.x 成本利润正主，5.1 不入正主
  · j51_util（SMM 铅蓄电池开工率: 总 a10151378 周度）作 5.1 正主

图1 铅锭表观消费 vs 实际消费（chart_dual）：j51_apparent 表观消费量 + j51_cons 实际消费量
    —— 表观=产量+进口-出口，实际扣除库存变动。差值反映库存变动方向。
图2 铅锭表观消费量季节图（chart_line_t seasonal）：近5年历年线，观察消费季节性规律。
图3 铅酸电池开工率 vs 铅锭消费验证（chart_dual）：j51_util 开工率(周) + j51_cons 消费量(月)
    —— 开工率=5.1 正主（同步反映电池厂对铅锭的实际消耗强度）；消费量=月度验证。

数据源：SMM 铅锭平衡(a10017183/a10017180 月) + SMM 铅蓄电池开工率(a10151378 周)。
备用（未入正主）：i18 铅锭社库(归属4.3)、j51_h2so4 硫酸价(归属7.x成本利润)。
"""
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html,
                        make_crumb)

CIDS = ["echart_51_c1", "echart_51_c2", "echart_51_c3"]

m_apparent = load_metric("j51_apparent")
m_cons = load_metric("j51_cons")
m_util = load_metric("j51_util")

d_apparent = pairs(m_apparent)
d_cons = pairs(m_cons)
d_util = pairs(m_util)

print("[POINTS] 表观消费=%d 实际消费=%d 开工率=%d" % (
    len(d_apparent), len(d_cons), len(d_util)))

# === 图1：铅锭表观消费 vs 实际消费 ===
h1, j1 = chart_dual(
    "echart_51_c1",
    "铅锭表观消费 vs 实际消费",
    "SMM 铅锭平衡 · 表观消费量 vs 消费量 · 月 · 万吨 · %d/%d 点(2015起) · 至 %s" % (
        len(d_apparent), len(d_cons), latest(m_apparent)),
    d_apparent, "#5b98c9", "表观消费量", "万吨",
    d_cons, "#e06c75", "实际消费量", "万吨",
    "什么时候看：判断铅锭需求的真实强弱。<br>"
    "怎么看：表观=产量+进口-出口，实际=表观-库存变动。两条线差距=库存变动方向：差距扩大=累库(消费弱)、收窄=去库(消费强)。"
    "最新(2026-06)：表观54.15 vs 实际52.15，差值+2.0=累库。"
    "春节月(2月)表观/实际均大幅回落，属季节性正常波动。"
)

# === 图2：铅锭表观消费量季节图 ===
h2, j2 = chart_line_t(
    "echart_51_c2",
    "铅锭表观消费量·季节图",
    "SMM 铅锭表观消费量 · 月 · 万吨 · %d 点(2015起) · 至 %s" % (
        len(d_apparent), latest(m_apparent)),
    "#5b98c9", d_apparent,
    "什么时候看：判断消费的月度季节性规律。<br>"
    "怎么看：春节月(2月)消费低谷，3-4月快速恢复；9-10月旺季，Q4为全年高位。"
    "2020年2月受疫情冲击创历史极低值。"
)

# === 图3：铅酸电池开工率 vs 铅锭消费验证 ===
h3, j3 = chart_dual(
    "echart_51_c3",
    "铅酸电池开工率 vs 铅锭消费验证（5.1 正主）",
    "SMM 铅蓄电池开工率(总) · 周 · %% / SMM 铅锭消费量 · 月 · 万吨 · %d/%d 点 · 至 %s" % (
        len(d_util), len(d_cons), latest(m_util)),
    d_util, "#5fb3a1", "铅酸电池开工率", "%",
    d_cons, "#b06a32", "铅锭消费量", "万吨",
    "什么时候看：5.1 初级消费的正主图——同步判断电池制造端对铅锭的实际消耗强度。<br>"
    "怎么看：开工率上行=电池厂排产意愿强=初级消费偏强；开工率下行=初级消费走弱。"
    "开工率与铅锭消费量同向=消费真实改善，背离=库存调节(累库/去库)掩盖真实趋势。"
    "开工率数据为周度、消费量为月度，两条线频率不同属正常（时间轴独立），关注趋势方向而非逐点重合。"
    "最新(2026-08)：开工率约50-55%（中位偏低）、铅锭消费约54万吨(月)。"
)

NOTE = """<strong style="color:#c9d1d9">5.1 定义：</strong>初级消费 = 铅酸蓄电池制造端对铅锭的同步消耗强度。铅酸电池是铅最核心下游（占消费90%+），开工率是 5.1 正主指标。<br>
<strong style="color:#c9d1d9">指标组（正主）：</strong>j51_util 铅酸电池开工率(总, %, 周) · j51_apparent 铅锭表观消费量(万吨/月) · j51_cons 铅锭消费量(万吨/月)。<br>
<strong style="color:#c9d1d9">备用指标（不入正主）：</strong>i18 铅锭五地社库(万吨/周，归属 4.3 库存正主) · j51_h2so4 硫酸价格(元/吨/日，归属 7.x 成本利润正主)。两者保留在 indicators_v1.json 供跨页引用，5.1 图不引用。<br>
<strong style="color:#c9d1d9">数据源：</strong>SMM 铅蓄电池开工率(a10151378, 周度404点) + SMM 铅锭平衡(a10017183/a10017180, 月度102点/2015起)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>表观消费/实际消费 102点(2015-01起)；开工率 404点(周频全量)。<br>
<strong style="color:#c9d1d9">5.1/5.2/5.3 边界：</strong>5.1 = 开工率·同步（正主）+ 表观/实际消费验证；5.2 = 终端细分·滞后（汽车/电动两轮/储能/通信基站）；5.3 = 需求先行1-2月（排产/订单/经销商库存）。出口图已在 6.3(HS8507) 做过，5.x 只做国内消费。<br>
<strong style="color:#c9d1d9">缺口：</strong>蓄电池产量(万kVAh)在知几无直接字段——开工率(a10151378)是最佳替代。</strong>"""

html = page_html(
    "铅(PB) 5.1 初级消费",
    make_crumb("铅", "PB", "5", "需求", "5.1", "初级消费", "1", 3),
    "SMM",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 5.1 初级消费 · v2（3 图全真数据 · 表观vs实际消费 · 季节规律 · 开工率+消费验证）· indicators_v1.json v2.7",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,

    nav_back='<a href="pb_5_overview.html">← 回板块5总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_51_primary_consumption.html", html)
