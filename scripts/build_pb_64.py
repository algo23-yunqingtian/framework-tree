#!/usr/bin/env python3
"""铅(PB) 6.4 海外对华发运子页 · v2 · 3 图全真数据（P1 重构：改用 chart_kits.py 公共模块）。

图1 LME 新加坡出发仓：i19 SG 注册 + i20 SG 注销（双轴联动）
图2 发运-到港节奏：i25 SG 出库量(日) + i17 海关铅锭进口(月)（双轴联动）
图3 海外 LME 分地区结构：i19 SG + i29 仁川 + i30 迪拜（三系列堆叠）

数据源：framework-tree/scripts/api_cache.db（i17/i19/i20/i25/i29/i30，全部 verified=true）
无新增 zhiji_id，无需再跑 refresh_cache。参见 analysis/iwencai/PB/64_diversify_20260828.md 自检报告。
⚠️ v2（P1）：补上 chart_kits 统一公共 JS（此前本页无 __seasonalize/__tgl/resize 公共封装，resize 为内联）；
   CSS 补回 button 样式，与其他 3 页结构一致。
"""
from chart_kits import (load_metric, pairs, latest,
                        chart_dual, chart_triple, page_html, write_html)

CIDS = ["echart_64_c1", "echart_64_c2", "echart_64_c3"]

# === 读数据 ===
m19 = load_metric("i19")   # SG 注册仓单（日, 吨）
m20 = load_metric("i20")   # SG 注销仓单（日, 吨）
m25 = load_metric("i25")   # SG 出库量（日, 吨）
m17 = load_metric("i17")   # 海关铅锭进口（月, 吨）
m29 = load_metric("i29")   # 仁川 LME 库（日, 吨）
m30 = load_metric("i30")   # 迪拜 LME 库（日, 吨）

d19 = pairs(m19)
d20 = pairs(m20)
d25 = pairs(m25)
d17 = pairs(m17)
d29 = pairs(m29)
d30 = pairs(m30)

# === 图1：LME 新加坡出发仓（SG 注册 + SG 注销） ===
h1, j1 = chart_dual(
    "echart_64_c1",
    "LME 新加坡出发仓：注册仓单 + 注销仓单（发运前置信号）",
    "LME(SG) · 日 · 吨 · i19 注册 %d 点 / i20 注销 %d 点 · 至 %s" % (m19["n"], m20["n"], max(latest(m19), latest(m20))),
    d19, "#5b98c9", "SG 注册仓单", "吨(左)",
    d20, "#c96a5b", "SG 注销仓单", "吨(右)",
    "什么时候看：LME 高库存是否即将转化为对华发运——这是 6.4 最前置的领先指标。<br>"
    "两个指标的关系：注册仓单=锁在仓库里待卖的水位；注销仓单=贸易商申请「提货出海」的开闸信号。"
    "注册高而注销不动 = 货趴在库不动（市场弱、无人接货）；"
    "注销仓单突然激增而总库存仍高位 = 这批货即将动身，1-3 周后到华，国内现货承压。"
)

# === 图2：发运-到港节奏（SG 出库量日度 + 海关月度进口） ===
h2, j2 = chart_dual(
    "echart_64_c2",
    "发运动作 → 到港结果：SG 出库量(日) + 海关铅锭月度进口",
    "LME(SG)出库(日,吨) · 海关(月,吨) · i25 %d 点 / i17 %d 点 · 至 %s / %s" % (m25["n"], m17["n"], latest(m25), latest(m17)),
    d25, "#7a8c5b", "SG 出库量", "吨(日,左)",
    d17, "#b06a32", "海关铅锭进口", "吨(月,右)",
    "什么时候看：海关数据发布前 2-4 周预判国内进口冲击节奏。<br>"
    "两个指标的关系：SG 出库量(左,日频)是「货已离仓」的动作，"
    "海关铅锭进口(右,月频)是「货已到港报关」的结果——中间隔着 1-3 周海运+报关。"
    "左轴连续放量 → 1-3 周后右轴月度数字必然抬升；"
    "左轴熄火 → 右轴下月转弱。这张图是海关数据的前瞻。"
)

# === 图3：LME 分地区结构（SG + 仁川 + 迪拜） ===
h3, j3 = chart_triple(
    "echart_64_c3",
    "LME 分地区结构：新加坡 + 仁川 + 迪拜（新加坡占比 >90% 印证）",
    "LME · 日 · 吨 · i19 SG %d 点 / i29 仁川 %d 点 / i30 迪拜 %d 点" % (m19["n"], m29["n"], m30["n"]),
    d19, "#5b98c9", "SG 新加坡", "吨(堆叠)",
    d29, "#b0a332", "仁川", "吨(堆叠)",
    d30, "#9b6bb5", "迪拜", "吨(堆叠)",
    "什么时候看：对华发运的货到底从哪个仓出发——决定运距、运费、到港节奏。<br>"
    "三个指标的关系：堆叠面积 = LME 亚太三大仓的库存分布（新加坡/仁川/迪拜）。"
    "新加坡面积几乎压满 = 亚太铅全部堆在新加坡（中国最近的出发仓，海运 2-4 天），"
    "意味着一旦开闸，冲击中国最快；仁川/迪拜面积抬升 = 货源向远端仓迁移，"
    "到华运距变长、节奏变慢。当前仁川/迪拜近乎 0，印证新加坡吸纳超 90%。"
)

# === 页面专属说明 ===
NOTE = """<strong style="color:#c9d1d9">6.4 定义与数据源说明：</strong>6.4「海外对华发运」= 出发仓(LME 分地区)→发运动作(出库量)→到港(海关月度)链条。<br>
<strong style="color:#c9d1d9">指标组</strong>：i19 SG 注册仓单 / i20 SG 注销仓单 / i25 SG 出库量 / i29 仁川 / i30 迪拜 / i17 海关铅锭进口(月) / i7 LME 全球注销仓单。<br>
<strong style="color:#c9d1d9">数据源缺口</strong>：同花顺 6.4 推荐图中「在途量」「提单量」「提单库存」「升贴水」SMM/Mysteel 均无公开序列，已剔除（详见 analysis/iwencai/PB/64_diversify_20260828.md 自检报告）；「印度/哈萨克斯坦分国别月度矩阵」印度无 LME 授权仓，暂用 SG 总量作代理。<br>
<strong style="color:#c9d1d9">v2 变更</strong>：i40 海关铅精矿进口已从 6.4 调回 6.1 原料进口正主（indicators_v1.json v1.9）；本页面改用 LME 分地区+海关序列组合，无需新增 zhiji_id。"""

html = page_html(
    "铅(PB) 6.4 海外对华发运",
    "铅(PB) · 6 进出口 · 6.4 海外对华发运 · v3 3 图(带图备注)",
    "Zhiji/LME/海关",
    h1, h2, h3, NOTE,
    "有色金属产业指标树 · 铅(PB) 6.4 海外对华发运 · v3（3 图全真数据 · LME 分地区代理 · 季节真数据）· indicators_v1.json v1.9",
    j1 + "\n" + j2 + "\n" + j3,
    CIDS,
)
write_html("pb_64_overseas_shipping.html", html)
print("[POINTS] i19=%d i20=%d i25=%d i17=%d i29=%d i30=%d" % (m19["n"], m20["n"], m25["n"], m17["n"], m29["n"], m30["n"]))