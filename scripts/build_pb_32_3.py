#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""铅(PB) 3.2.3 再生/二次供应子页 · v1 · 3 图全真数据（板块3·供给·第1子节点）。

图1 再生铅有效供应：产量 × 产能利用率 × 原料库存（自写柱+线+线）
    j323_regen_output 再生精铅产量(月柱) + j323_regen_util 产能利用率(月线右轴)
    + i12 再生铅原料库存(周压月线右轴) —— 废电瓶可回收量→有效产能的约束传导
图2 原生铅 vs 再生铅供应结构（自写双柱+占比线）
    j323_native_output 原生铅产量 + j323_regen_output 再生精铅产量 + 再生占比(计算)
图3 再生铅产能利用率：全行业 vs 30家样本（chart_dual）
    j323_regen_util 月度全行业 + j323_regen_util_w 周度30家样本
图4 再生铅产量季节图（chart_line_t，12月类目，近5年历年线）
    j323_regen_output —— 区分淡季自然回落与亏损导致的异常减产

数据源：SMM / Mysteel。产量与利用率 91 月(2019-01~2026-07)；周度利用率 380 点(2019-05~2026-08-28)；
再生原料库存 378 点(2019-05~2026-08-21)。
⚠️ 同花顺发散 8 图中，合规产能出清/进口粗铅/废料结构占比因无连续序列，NOTE 标注待外部源。
"""
import json
from chart_kits import (load_metric, pairs, latest, chart_dual, chart_line_t,
                        page_html, write_html, make_crumb)

CIDS = ["echart_32_3_c1", "echart_32_3_c2", "echart_32_3_c3", "echart_32_3_c4"]


def weekly_to_monthly(pairs_w, target_dates):
    """周度序列压月：取每月最后一个周度观测值。"""
    idx = {}
    for d, v in pairs_w:
        ym = d[:7]
        if ym not in idx or d > idx[ym][0]:
            idx[ym] = (d, v)
    out = []
    for d in target_dates:
        ym = d[:7]
        if ym in idx:
            out.append([idx[ym][0], idx[ym][1]])
    return out


m_out = load_metric("j323_regen_output")
m_util = load_metric("j323_regen_util")
m_mat = load_metric("i12")
m_nat = load_metric("j323_native_output")
m_utilw = load_metric("j323_regen_util_w")

d_out = pairs(m_out)
d_util = pairs(m_util)
d_mat = pairs(m_mat)
d_nat = pairs(m_nat)
d_utilw = pairs(m_utilw)

# 图1：原料库存周压月（对齐产量月份）
out_dates = [d for d, v in d_out]
d_mat_m = weekly_to_monthly(d_mat, out_dates)

# 图2：原生+再生 共有月份 → 再生占比
nm = {d: v for d, v in d_nat}
rg = {d: v for d, v in d_out}
common = sorted(set(nm) & set(rg))
d_nat_c = [[d, round(nm[d], 2)] for d in common]
d_regen_c = [[d, round(rg[d], 2)] for d in common]
d_ratio = [[d, round(rg[d] / (nm[d] + rg[d]) * 100, 1)] for d in common]

print("[POINTS] 再生产量=%d 产能利用率=%d 原料库存周=%d 压月=%d 原生=%d 共有=%d 周度利用率=%d"
      % (len(d_out), len(d_util), len(d_mat), len(d_mat_m), len(d_nat), len(common), len(d_utilw)))

# 最新值（用于 chart-note）
last_out = d_out[-1]
last_util = dict(d_util).get(last_out[0])
last_ratio = d_ratio[-1]
last_mat = d_mat_m[-1] if d_mat_m else ("-", None)
last_utilw = d_utilw[-1]

# === 图1：再生铅有效供应（柱+双折线）===
jo = json.dumps(d_out, ensure_ascii=False)
ju = json.dumps(d_util, ensure_ascii=False)
jm = json.dumps(d_mat_m, ensure_ascii=False)
cid1 = "echart_32_3_c1"
js1 = ("window['__data_%s'] = [%s, %s, %s];\n"
       "window['__opts_%s'] = {\n"
       "  tooltip:{trigger:'axis'},\n"
       "  legend:{data:['再生精铅产量','产能利用率','再生原料库存'],textStyle:{color:'#ccc'},top:0},\n"
       "  grid:{left:55,right:60,top:45,bottom:40},\n"
       "  xAxis:{type:'time',axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
       "  yAxis:[\n"
       "    {type:'value',name:'万吨',nameTextStyle:{color:'#aaa'},axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
       "    {type:'value',name:'%% / 万吨',nameTextStyle:{color:'#aaa'},axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}}\n"
       "  ],\n"
       "  series:[\n"
       "    {name:'再生精铅产量',type:'bar',barMaxWidth:6,itemStyle:{color:'#5b98c9'},data:%s},\n"
       "    {name:'产能利用率',type:'line',smooth:true,symbol:'circle',symbolSize:3,lineStyle:{color:'#e06c75',width:2},yAxisIndex:1,data:%s},\n"
       "    {name:'再生原料库存',type:'line',smooth:true,symbol:'circle',symbolSize:3,lineStyle:{color:'#5fb3a1',width:2},yAxisIndex:1,data:%s}\n"
       "  ]\n"
       "};\n"
       "window['__inst_%s'] = echarts.init(document.getElementById('%s'),'dark');\n"
       "window['__inst_%s'].setOption(window['__opts_%s'], true);\n"
       ) % (cid1, jo, ju, jm, cid1, jo, ju, jm, cid1, cid1, cid1, cid1)
h1 = ('<div class="chart"><div class="chart-title">再生铅有效供应：产量 × 产能利用率 × 原料库存</div>'
      '<div class="chart-sub">SMM 再生精铅产量 + Mysteel 再生铅产能利用率 + 再生铅原料库存 · 月(库存周压月) · %d/%d/%d 点 · 至 %s</div>'
      '<div id="%s" style="width:100%%;height:320px"></div>'
      '<div class="chart-note">📌 %s</div></div>') % (
    len(d_out), len(d_util), len(d_mat_m), latest(m_out), cid1,
    "什么时候看：判断再生铅（中国铅供给的主导变量）当前实际能产出多少，以及是产能过剩开不出还是真实放量。<br>"
    "怎么看：柱=实际产量（左轴万吨），红=产能利用率、绿=废电瓶原料库存（右轴）。三者同向下滑=废电瓶紧+亏损共振压制供应；"
    "利用率长期低于50%%说明名义产能被原料可得性约束。最新(2026-07)：产量%.2f万吨、产能利用率%.2f%%（低位）、原料库存%.2f万吨。"
    % (last_out[1], last_util, last_mat[1]))

# === 图2：原生 vs 再生供应结构 ===
jn = json.dumps(d_nat_c, ensure_ascii=False)
jr = json.dumps(d_regen_c, ensure_ascii=False)
jp = json.dumps(d_ratio, ensure_ascii=False)
cid2 = "echart_32_3_c2"
js2 = ("window['__data_%s'] = [%s, %s, %s];\n"
       "window['__opts_%s'] = {\n"
       "  tooltip:{trigger:'axis'},\n"
       "  legend:{data:['原生铅产量','再生铅产量','再生占比'],textStyle:{color:'#ccc'},top:0},\n"
       "  grid:{left:55,right:60,top:45,bottom:40},\n"
       "  xAxis:{type:'time',axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
       "  yAxis:[\n"
       "    {type:'value',name:'万吨',nameTextStyle:{color:'#aaa'},axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
       "    {type:'value',name:'%%',min:0,max:100,nameTextStyle:{color:'#aaa'},axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}}\n"
       "  ],\n"
       "  series:[\n"
       "    {name:'原生铅产量',type:'bar',stack:'supply',barMaxWidth:6,itemStyle:{color:'#7a8a9c'},data:%s},\n"
       "    {name:'再生铅产量',type:'bar',stack:'supply',barMaxWidth:6,itemStyle:{color:'#5b98c9'},data:%s},\n"
       "    {name:'再生占比',type:'line',smooth:true,symbol:'circle',symbolSize:3,lineStyle:{color:'#e06c75',width:2},yAxisIndex:1,data:%s}\n"
       "  ]\n"
       "};\n"
       "window['__inst_%s'] = echarts.init(document.getElementById('%s'),'dark');\n"
       "window['__inst_%s'].setOption(window['__opts_%s'], true);\n"
       ) % (cid2, jn, jr, jp, cid2, jn, jr, jp, cid2, cid2, cid2, cid2)
h2 = ('<div class="chart"><div class="chart-title">原生铅 vs 再生铅供应结构（再生占比）</div>'
      '<div class="chart-sub">Mysteel 原生铅产量 + SMM 再生精铅产量 + 再生占比(计算) · 月 · %d 月(共有区间) · 至 %s</div>'
      '<div id="%s" style="width:100%%;height:320px"></div>'
      '<div class="chart-note">📌 %s</div></div>') % (
    len(common), common[-1], cid2,
    "什么时候看：判断再生铅在中国铅总供给中的定价权重，矿端扰动与废电瓶扰动的相对影响力。<br>"
    "怎么看：堆叠柱=总精炼铅供给（灰=原生/蓝=再生），红线=再生占比。占比中枢上移=供应主导权从矿山转移到废电瓶回收体系，"
    "矿端(3.1)对价格的影响被削弱。区间:%s-%s，最新(2026-07)：原生%.2f + 再生%.2f 万吨、再生占比%.1f%%。"
    % (d_ratio[0][1], max(x[1] for x in d_ratio), d_nat_c[-1][1], d_regen_c[-1][1], d_ratio[-1][1]))

# === 图3：产能利用率 全行业 vs 30家样本 ===
h3, j3 = chart_dual(
    "echart_32_3_c3",
    "再生铅产能利用率：全行业月度 vs 30家样本周度",
    "Mysteel 再生铅产能利用率(全行业·月) + 30家样本(周) · %d/%d 点 · 至 %s" % (len(d_util), len(d_utilw), latest(m_utilw)),
    d_util, "#e06c75", "全行业(月度)", "%",
    d_utilw, "#5fb3a1", "30家样本(周度)", "%",
    "什么时候看：判断再生端开工是季节性回落还是异常冲击，验证旺季前供应弹性能否真实释放。<br>"
    "怎么看：两条线均为产能利用率，周度样本对亏损更敏感、振幅更大；两线背离走阔=样本龙头挺价减产、行业整体被动收缩。"
    "最新：全行业月度%.2f%%、样本周度%.2f%%。" % (last_util, last_utilw[1])
)

# === 图4：再生铅产量季节图（月度12月类目，近5年历年线）===
h4, j4 = chart_line_t(
    "echart_32_3_c4",
    "再生铅产量季节图",
    "SMM 再生精铅产量 · 月 · 万吨 · %d 点(2019-01起) · 至 %s · 季节视图近5年历年线" % (len(d_out), latest(m_out)),
    "#5b98c9",
    d_out,
    "什么时候看：判断当前再生铅产量处在历史季节性什么位置，区分淡季自然回落与亏损导致的异常减产。<br>"
    "怎么看：时序⇄季节切换（按钮切换）。季节视图横轴1-12月、每线一年。产量在历史同月分位带下沿=非季节性减产（原料紧或亏损）；"
    "旺季前产量回升但利用率仍低=名义产能释放，供应压力真实增加。最新(2026-07)：%.2f万吨。" % last_out[1],
    default_seasonal=True,
)

NOTE = """<strong style="color:#c9d1d9">3.2.3 定义：</strong>再生/二次供应 = 再生铅产量与开工 + 再生原料(废电瓶)供应 + 原生vs再生供应结构。铅的核心矛盾是「再生铅定价」，再生铅已成为中国铅供给的主导变量（2025年占铅总产量约51.6%，SMM口径），本节点聚焦「废电瓶可回收量 → 再生开工 → 实际产量」传导链。<br>
<strong style="color:#c9d1d9">指标组：</strong>j323_regen_output 再生精铅产量(万吨,月,a10098385) · j323_regen_util 再生铅产能利用率(%,月,ID01167229) · j323_regen_util_w 30家样本周度利用率(%,ID01030006) · j323_native_output 原生铅产量(万吨,月,ID01001562) · i12 再生铅原料库存(万吨,周,ID01167591) · j323_smm_regen_rate SMM再生铅开工率(%,月,a10017000,备用)。<br>
<strong style="color:#c9d1d9">数据质量：</strong>产量/利用率/原生产量 91月(2019-01起)；周度样本利用率 380点(2019-05~2026-08-28)；再生原料库存 378点(2019-05~2026-08-21)。<br>
<strong style="color:#c9d1d9">口径：</strong>再生铅产量分「废电瓶投入口径」与「成品再生精铅口径」，本节点用 SMM 成品口径；再生占比 = 再生精铅/(原生+再生)，分母非海关精炼铅总产量，与协会总产量口径存在差异。<br>
<strong style="color:#c9d1d9">v1 关键说明：</strong>同花顺发散 8 图中 3 项因无连续序列未上图——合规产能与低效产能出清(工信部《再生铅行业规范条件》：预处理≥10万吨/年、再生铅≥6万吨/年，事件型)、含铅废料来源结构占比(废铅酸蓄电池占再生原料85%+，截面值)、海外粗铅/铅合金进口(HS 7606，需海关口径)。<br>
<strong style="color:#c9d1d9">待外部源：</strong>再生铅企业原料库存天数、停产/减产企业数、环保关停产能事件表。<br>
<strong style="color:#c9d1d9">归属说明：</strong>精废价差/再生利润已在 2.4/2.5 从利润视角展示；本节点仅用利用率与产量呈现「利润→供应弹性」的结果端，避免口径重复。"""

html = page_html(
    "铅(PB) 3.2.3 再生/二次供应",
    make_crumb("铅", "PB", "3", "供给", "3.2.3", "再生/二次供应", "1", 4),
    "SMM + Mysteel",
    h1, h2, h3 + h4, NOTE,
    "有色金属产业指标树 · 铅(PB) 3.2.3 再生/二次供应 · v1（4 图全真数据 · 有效供应传导 · 原再生结构 · 利用率双口径 · 产量季节性）· indicators_v1.json v2.5",
    js1 + "\n" + js2 + "\n" + j3 + "\n" + j4,
    CIDS,
    nav_back='<a href="pb_3_overview.html">← 回板块3总览</a> <a href="index.html">← 回主站</a>',
)
write_html("pb_32_3_regen_supply.html", html)
