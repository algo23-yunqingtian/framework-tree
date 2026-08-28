#!/usr/bin/env python3
"""铅(PB) 6.1 原料进口子页 · v2 · 3 图全真数据（复用 build_pb_64 v2 模板）。

图1 海关铅精矿月度进口（季节/时序切换）：i40（月，吨）
图2 到港→消化：i9 冶炼厂精矿库存(月) + i5 港口库存(周)（双轴）
图3 防城到港量（历史周频，过滤非零）：i16（周，万吨）

⚠️ 修正：v1 页面 6.1 图2 误用了 i17（海关铅锭进口，属 6.2 精炼金属）。本次 v2 剔除 i17，
   6.1 正主 = i40 海关铅精矿进口（原料端）。参见 analysis/iwencai/PB/61_diversify_20260828.md。
"""
import sqlite3, json, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "api_cache.db")
CONNECTION = sqlite3.connect(DB)
CURSOR = CONNECTION.cursor()


def load_metric(mid):
    r = CURSOR.execute("SELECT data_json FROM indicator_cache WHERE metric=? AND code='PB'", (mid,)).fetchone()
    if not r:
        return None
    d = json.loads(r[0])
    pts = [{"date": p["date"], "value": float(p["value"])} for p in d.get("points", [])
           if isinstance(p, dict) and p.get("date") and p.get("value") is not None]
    pts.sort(key=lambda p: p["date"])
    return {"name": d.get("name", ""), "unit": d.get("unit", ""), "freq": d.get("freq", ""),
            "n": len(pts), "points": pts,
            "dates": [p["date"] for p in pts], "values": [p["value"] for p in pts]}


def pairs(m):
    return [[d, v] for d, v in zip(m["dates"], m["values"]) if v is not None]


def latest(m):
    return max(m["dates"]) if m["dates"] else "-"


def chart_line_t(cid, title, sub, color, data, note='', default_seasonal=False):
    """单变量双模式图（时序⇄季节切换）。default_seasonal=False 时默认时序。"""
    json_pts = json.dumps(data, ensure_ascii=False)
    color30 = color + "30"
    color00 = color + "00"
    color20 = color + "20"
    mode = "se" if default_seasonal else "ts"
    js = ("window['__data_%s'] = %s;\n"
          "var __d = window['__data_%s'];\n"
          "window['__opts_%s'] = {\n"
          "  ts: {\n"
          "    tooltip:{trigger:'axis'},grid:{left:55,right:60,top:30,bottom:40},\n"
          "    xAxis:{type:'time',axisLabel:{color:'#aaa',interval:0},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}},axisTick:{lineStyle:{color:'#444'}}},\n"
          "    yAxis:{type:'value',axisLabel:{color:'#aaa'},splitLine:{lineStyle:{color:'#333',type:'dashed'}},axisLine:{lineStyle:{color:'#444'}}},\n"
          "    series:[{name:'%s',type:'line',smooth:true,symbol:'circle',symbolSize:4,\n"
          "      lineStyle:{color:'%s',width:2},\n"
          "      areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'%s'},{offset:1,color:'%s'}]}},\n"
          "      data:__d,markPoint:{symbol:'circle',symbolSize:6,data:[{coord:[__d[__d.length-1][0],__d[__d.length-1][1]],\n"
          "        itemStyle:{color:'%s'},label:{show:false}}]}}]\n"
          "  },\n"
          "  se: {\n"
          "    tooltip:{trigger:'axis'},grid:{left:55,right:60,top:30,bottom:40},\n"
          "    xAxis:{type:'category',data:['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
          "    yAxis:{type:'value',axisLabel:{color:'#aaa'},splitLine:{lineStyle:{color:'#333',type:'dashed'}},axisLine:{lineStyle:{color:'#444'}}},\n"
          "    series:[{name:'%s',type:'line',smooth:true,symbol:'circle',symbolSize:4,lineStyle:{color:'%s',width:2},areaStyle:{color:'%s'},data:[null,null,null,null,null,null,null,null,null,null,null,null]}]\n"
          "  }\n"
          "};\n"
          "window['__inst_%s'] = echarts.init(document.getElementById('%s'),'dark');\n"
          "window['__mode_%s'] = '%s';\n"
          "window['__inst_%s'].setOption(window['__opts_%s']['%s'], true);\n"
          ) % (cid, json_pts, cid, cid, title, color, color30, color00, color,
               title, color, color20,
               cid, cid, cid, mode, cid, cid, mode)
    html = ('<div class="chart"><div class="chart-title">%s</div>'
            '<div class="chart-sub">%s</div>'
            '<div id="%s" style="width:100%%;height:280px"></div>'
            '<button onclick="window.__tgl(\'%s\',this)">☀ 季节</button>'
            '<div class="chart-note">📌 %s</div></div>'
            ) % (title, sub, cid, cid, note)
    return html, js


def chart_dual(cid, title, sub, data_a, color_a, name_a, unit_a, data_b, color_b, name_b, unit_b, note=''):
    """双轴复合图。"""
    ja = json.dumps(data_a, ensure_ascii=False)
    jb = json.dumps(data_b, ensure_ascii=False)
    color_a20 = color_a + "20"
    color_b20 = color_b + "20"
    js = ("window['__data_%s'] = [%s, %s];\n"
          "window['__opts_%s'] = {\n"
          "  tooltip:{trigger:'axis'},\n"
          "  legend:{data:['%s','%s'],textStyle:{color:'#ccc'},top:0},\n"
          "  grid:{left:55,right:55,top:45,bottom:40},\n"
          "  xAxis:{type:'time',axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
          "  yAxis:[\n"
          "    {type:'value',name:'%s',nameTextStyle:{color:'#aaa'},axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
          "    {type:'value',name:'%s',nameTextStyle:{color:'#aaa'},axisLabel:{color:'#aaa'},splitLine:{lineStyle:{color:'#333',type:'dashed'}},axisLine:{lineStyle:{color:'#444'}}}\n"
          "  ],\n"
          "  series:[\n"
          "    {name:'%s',type:'line',smooth:true,symbol:'circle',symbolSize:3,lineStyle:{color:'%s',width:2},areaStyle:{color:'%s'},data:%s},\n"
          "    {name:'%s',type:'line',smooth:true,symbol:'circle',symbolSize:3,lineStyle:{color:'%s',width:2},yAxisIndex:1,areaStyle:{color:'%s'},data:%s}\n"
          "  ]\n"
          "};\n"
          "window['__inst_%s'] = echarts.init(document.getElementById('%s'),'dark');\n"
          "window['__inst_%s'].setOption(window['__opts_%s'], true);\n"
          ) % (cid, ja, jb, cid, name_a, name_b, unit_a, unit_b, name_a, color_a, color_a20, ja,
               name_b, color_b, color_b20, jb, cid, cid, cid, cid)
    html = ('<div class="chart"><div class="chart-title">%s</div>'
            '<div class="chart-sub">%s</div>'
            '<div id="%s" style="width:100%%;height:320px"></div>'
            '<div class="chart-note">📌 %s</div></div>'
            ) % (title, sub, cid, note)
    return html, js


CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px;
     user-select:none;-webkit-user-select:none;-moz-user-select:none}
.header{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;background:#161b22;border-radius:8px;margin-bottom:16px;border:1px solid #21262d}
.brand{font-size:20px;font-weight:600}.brand small{font-size:12px;color:#8b949e;margin-left:8px}
.hcrumbs{color:#8b949e}.hright{color:#5b7a8c;font-size:13px}
.panel{background:#161b22;border-radius:8px;padding:20px;border:1px solid #21262d}
.chart{background:#0d1117;border-radius:6px;padding:12px;margin:12px 0;border:1px solid #21262d}
.chart-title{font-size:15px;font-weight:600;margin-bottom:6px;color:#e6edf3}
.chart-sub{font-size:12px;color:#8b949e;margin-bottom:8px}
.chart button{background:#21262d;border:1px solid #30363d;color:#8b949e;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px;margin-top:4px;user-select:none}
.chart button:hover{background:#30363d;color:#c9d1d9}
.chart-note{font-size:12px;color:#a8c0d8;background:#10151c;border-left:3px solid #5b7a8c;padding:8px 10px;margin-top:8px;border-radius:0 4px 4px 0;line-height:1.6}
footer{margin-top:20px;font-size:12px;color:#586069;text-align:center;border-top:1px solid #21262d;padding-top:16px}
.note{font-size:12px;color:#8b949e;padding:12px;border-top:1px solid #21262d;margin-top:8px}
.note strong{color:#c9d1d9}"""

ANTI = """document.oncontextmenu=e=>{e.preventDefault();return false};
document.onkeydown=e=>{if(e.ctrlKey&&['c','s','p','u'].includes(e.key.toLowerCase())){e.preventDefault();return false}};
document.onselectstart=e=>{e.preventDefault();return false};"""

NOW = datetime.now().strftime("%Y-%m-%d")

# === 读数据 ===
m40 = load_metric("i40")   # 海关铅精矿进口量（月, 吨）
m9 = load_metric("i9")     # 冶炼厂铅精矿库存（月, 金属吨）
m5 = load_metric("i5")     # 精矿港口库存（周, 万吨）
m16 = load_metric("i16")   # 防城到港（周, 万吨）

d40 = pairs(m40)
d9 = pairs(m9)
d5 = pairs(m5)
# i16 防城到港近期数据源停更（连续 0），过滤非零
d16_filtered = [[d, v] for d, v in pairs(m16) if v is not None and float(v) != 0]

# === 图1：海关铅精矿月度进口（季节/时序切换）===
h1, j1 = chart_line_t(
    "echart_61_c1",
    "海关铅精矿月度进口量（原料端补库节奏，季节/时序切换）",
    "海关 · 月 · 吨 · i40 %d 点 · 2018-01 至 %s" % (m40["n"], latest(m40)),
    "#9b6bb5",
    d40,
    "什么时候看：原料端补库节奏、是否偏离季节性、冶炼厂原料库存能否撑住。<br>"
    "怎么看：单指标图，核心看同比偏离。切到季节视图后把 8 年每月叠一起，"
    "今年这条线明显低于历史同期 = 原料补给不及、冶炼厂面临缺矿减产风险；"
    "明显高于 = 抢原料囤矿（对下游成本是利多）。"
)

# === 图2：到港→消化（冶炼厂精矿库存 vs 港口库存）===
h2, j2 = chart_dual(
    "echart_61_c2",
    "到港→消化：冶炼厂精矿库存(月) + 港口库存(周)",
    "SMM 冶炼厂(月,金属吨) · 精矿港口(周,万吨) · i9 %d 点 / i5 %d 点 · 至 %s / %s" % (m9["n"], m5["n"], latest(m9), latest(m5)),
    d9, "#b06a32", "冶炼厂精矿库存", "金属吨(月,左)",
    d5, "#7a8c5b", "精矿港口库存", "万吨(周,右)",
    "什么时候看：到港的矿有没有真的进冶炼厂、原料消化效率高不高。<br>"
    "两个指标的关系：这是「存量-流量」配对——精矿先到港堆在港口(港口库存=滞留环节)，"
    "被冶炼厂拉走后变成厂内原料库存(冶炼厂库存=可冶炼环节)。<br>"
    "港口库存升 + 厂内库存降 = 货滞留港口(冶炼厂不愿拉货/原料价格高/开工不足)，"
    "原料端宽松；港口库存降 + 厂内库存升 = 冶炼厂积极备料，开工率预期上升。"
)

# === 图3：防城到港量（历史周频，过滤非零）===
h3, j3 = chart_line_t(
    "echart_61_c3",
    "铅矿防城到港量（历史周频，非零数据）",
    "沸腾环贸 · 周 · 万吨 · i16 %d 点(非零) · 2020-01 至 %s · 近期数据源停更" % (len(d16_filtered), max([d for d,_ in d16_filtered]) if d16_filtered else "-"),
    "#7a8c5b",
    d16_filtered,
    "什么时候看：到港节奏（比海关月度报关数据领先 2-4 周）。<br>"
    "怎么看：单指标周频图，到港峰谷 = 集中卸船冲击。到港高峰 + 港口库存积压 = "
    "冶炼厂接货意愿弱；到港高峰 + 库存快速下降 = 货一进港就被拉走。<br>"
    "⚠️ 数据源近期停更（2026.08 起连续 0），仅保留历史周频序列。"
)

# === 拼装页面 ===
page_html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 6.1 原料进口 · 有色金属研究框架</title>
<style>""" + CSS + """</style></head><body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK v2</small></div>
  <div class="hcrumbs">铅(PB) · 6 进出口 · 6.1 原料进口 · v3 3 图(带图备注)</div>
  <div class="hright">数据固化快照 · """ + NOW + """ · 海关/SMM/沸腾环贸</div>
</div>
<div class="panel">
""" + h1 + h2 + h3 + """
<div class="note">
<strong style="color:#c9d1d9">6.1 定义与数据源说明：</strong>6.1「原料进口」= 进口铅精矿(原料) → 港口到港 → 港口库存 → 冶炼厂原料库存 这条"原料端补库"链条。<br>
<strong style="color:#c9d1d9">指标组</strong>：i40 海关铅精矿进口量(月,吨) · i5 精矿港口库存(周,万吨) · i9 冶炼厂铅精矿库存(月,金属吨) · i16 防城铅矿到港(周,万吨)。<br>
<strong style="color:#c9d1d9">v2 关键修正</strong>：v1 页面 6.1 图2 误用了 i17（海关铅锭进口，属 6.2 精炼金属范畴），本次 v2 剔除 i17。6.1 正主 = i40 海关铅精矿进口（原料端）。<br>
<strong style="color:#c9d1d9">数据源缺口</strong>：同花顺 6.1 推荐图中「进口来源国集中度」「年度累计来源国热力图」「银精矿伴生含铅量」知几无原始月度分国别矩阵或独立口径，已剔除（详见 analysis/iwencai/PB/61_diversify_20260828.md 自检报告）。同花顺确认前十大进口来源国 = 俄罗斯/秘鲁/澳大利亚/塔吉克斯坦/巴西（仅作定性参考）。<br>
<strong style="color:#c9d1d9">数据源停更备注</strong>：i16 防城到港近期（2026.08）连续 0，数据源停更；图3 用过滤后 293 点（大部分 2020-2025 有值）。
</div>
</div>
<footer>有色金属产业指标树 · 铅(PB) 6.1 原料进口 · v2（3 图全真数据 · 原料端补库）· indicators_v1.json v1.9</footer>
<script src="assets/echarts.min.js"></script>
<script>
""" + ANTI + """
""" + j1 + "\n" + j2 + "\n" + j3 + """
function __tgl(id,btn){var cur=window['__mode_'+id],nxt=cur==='ts'?'se':'ts';
window['__mode_'+id]=nxt;window['__inst_'+id].setOption(window['__opts_'+id][nxt],true);
btn.textContent=nxt==='ts'?'⏱ 时序':'☀ 季节';}
window.addEventListener('resize',function(){['echart_61_c1','echart_61_c2','echart_61_c3'].forEach(function(id){var el=document.getElementById(id);var inst=echarts.getInstanceByDom(el);if(inst)inst.resize();});});
</script></body></html>"""

out_path = os.path.join(os.path.dirname(BASE), "pb_61_raw_material_import.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(page_html)
print("[OK] 已生成: %s (%d 字节)" % (out_path, len(page_html)))
print("[POINTS] i40=%d i9=%d i5=%d i16_filtered=%d" % (m40["n"], m9["n"], m5["n"], len(d16_filtered)))
