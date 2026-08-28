#!/usr/bin/env python3
"""铅(PB) 6.3 制品出口子页 · v2 · 3 图全真数据（复用 build_pb_62_demo.py v2 模板）。

图1 铅蓄电池出口总量（季节/时序切换）：i37（月，个）
图2 启动型铅蓄电池出口（季节/时序切换）：i38（月，个）
图3 启动型 vs 其他类型结构（双轴）：i38 起动型 + (i37-i38) 其他类型

⚠️ 数据源缺口：铅蓄电池进口（HS 8507 含锂电池需剔除）、出口目的地分布（知几无矩阵）——详见 63_diversify_20260828.md。
⚠️ 政策变量：海合会反倾销税率 25.8-74%，2026.1.13 生效。
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
    """单变量双模式图（时序⇄季节切换）。"""
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
m37 = load_metric("i37")   # 铅蓄电池出口总量（月, 个）
m38 = load_metric("i38")   # 起动型铅蓄电池出口（月, 个）
m39 = load_metric("i39")   # 铅蓄电池出口累计（月, 个）— 备用

d37 = pairs(m37)
d38 = pairs(m38)

# 计算"其他类型"= i37 - i38
m37_dict = {d: v for d, v in d37}
m38_dict = {d: v for d, v in d38}
common_dates = sorted(set(m37_dict.keys()) & set(m38_dict.keys()))
d_other = [[d, m37_dict[d] - m38_dict[d]] for d in common_dates]

# === 图1：铅蓄电池出口总量（季节/时序切换）===
h1, j1 = chart_line_t(
    "echart_63_c1",
    "铅蓄电池出口总量（6.3 制品出口正主，季节/时序切换）",
    "海关 · 月 · 个 · i37 %d 点 · 2018-01 至 %s" % (m37["n"], latest(m37)),
    "#9b6bb5",
    d37,
    "什么时候看：出口旺季成色、海合会反倾销生效后出口是否受冲击。<br>"
    "怎么看：单指标月度图，季节性强（Q4/Q1 旺）。切季节视图对比历史同期，"
    "今年旺季线明显低于历史 = 旺季成色差、需求外流受抑；"
    "反倾销 2026.1.13 生效后 1-6 月线持续走弱 = 政策直接杀伤可见。",
    default_seasonal=True
)

# === 图2：启动型铅蓄电池出口（季节/时序切换）===
h2, j2 = chart_line_t(
    "echart_63_c2",
    "启动型铅蓄电池出口量（HS 85071000，季节/时序切换）",
    "海关 · 月 · 个 · i38 %d 点 · 2018-01 至 %s" % (m38["n"], latest(m38)),
    "#b06a32",
    d38,
    "什么时候看：汽车启动用电池这条主力线的景气度。<br>"
    "怎么看：单指标月度图。启动型是铅蓄电池出口的绝对主力（约 30%），"
    "它的斜率 = 汽车产业链的海外需求；若整体出口(i37)走弱但启动型坚挺 = "
    "结构在切向储能/两轮（非启动型），铅需求拉动逻辑会变。",
    default_seasonal=True
)

# === 图3：启动型 vs 其他类型结构（双轴）===
h3, j3 = chart_dual(
    "echart_63_c3",
    "铅蓄电池出口结构：启动型 vs 其他类型（HS 85071000 vs 85072000）",
    "海关 · 月 · 个 · i38 启动型 %d 点 / (i37-i38) 其他类型 %d 点 · 至 %s" % (m38["n"], len(d_other), latest(m38)),
    d38, "#b06a32", "启动型铅蓄电池", "个(月,左)",
    d_other, "#5b98c9", "其他类型铅蓄电池", "个(月,右)",
    "什么时候看：出口结构是否切换、铅需求拉动逻辑是否改变。<br>"
    "两个指标的关系：左轴启动型(85071000)是汽车链，右轴其他(85072000)是储能/UPS/两轮链，"
    "两者相加 = 铅蓄电池出口总量(i37)。<br>"
    "启动型上升 = 汽车链强势；其他类型上升 = 储能/两轮崛起。两条线走势分化 = "
    "产品结构切换；若启动型塌而总量稳 = 出口全靠储能撑（铅单耗不同，需求折算要重估）。"
)

# === 拼装页面 ===
page_html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 6.3 制品出口 · 有色金属研究框架</title>
<style>""" + CSS + """</style></head><body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK v2</small></div>
  <div class="hcrumbs">铅(PB) · 6 进出口 · 6.3 制品出口 · v3 3 图(带图备注)</div>
  <div class="hright">数据固化快照 · """ + NOW + """ · 海关</div>
</div>
<div class="panel">
""" + h1 + h2 + h3 + """
<div class="note">
<strong style="color:#c9d1d9">6.3 定义与数据源说明：</strong>6.3「制品出口」= 铅蓄电池出口(HS 8507) → 分启动型(85071000)/其他(85072000)结构 → 分目的地 → 海合会反倾销政策。这条"下游制品出口"链条。<br>
<strong style="color:#c9d1d9">指标组</strong>：i37 铅蓄电池出口总量(月,个) · i38 起动型铅蓄电池出口(月,个) · 计算"其他类型"=(i37-i38)。<br>
<strong style="color:#c9d1d9">数据源缺口</strong>：<br>
· 铅蓄电池进口：HS 8507 含锂电池需剔除，知几无独立"铅蓄电池进口"序列 → 用 i37 总量代理"净出口"概念；<br>
· 出口目的地分布：知几无分目的地矩阵 → 剔除；<br>
· HS 7806 铅材制品（铅条/铅板/铅焊料）：口径不清 → 剔除。<br>
<strong style="color:#c9d1d9">政策变量</strong>：海合会反倾销税率 25.8-74%，2026.1.13 生效；2026.7 出口 1904.58 万只，累计同比-6.57%。<br>
详见 analysis/iwencai/PB/63_diversify_20260828.md 自检报告。
</div>
</div>
<footer>有色金属产业指标树 · 铅(PB) 6.3 制品出口 · v2（3 图全真数据 · HS 8507 制品出口）· indicators_v1.json v1.9</footer>
<script src="assets/echarts.min.js"></script>
<script>
""" + ANTI + """
""" + j1 + "\n" + j2 + "\n" + j3 + """
function __tgl(id,btn){var cur=window['__mode_'+id],nxt=cur==='ts'?'se':'ts';
window['__mode_'+id]=nxt;window['__inst_'+id].setOption(window['__opts_'+id][nxt],true);
btn.textContent=nxt==='ts'?'⏱ 时序':'☀ 季节';}
window.addEventListener('resize',function(){['echart_63_c1','echart_63_c2','echart_63_c3'].forEach(function(id){var el=document.getElementById(id);var inst=echarts.getInstanceByDom(el);if(inst)inst.resize();});});
</script></body></html>"""

out_path = os.path.join(os.path.dirname(BASE), "pb_63_product_export.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(page_html)
print("[OK] 已生成: %s (%d 字节)" % (out_path, len(page_html)))
print("[POINTS] i37=%d i38=%d 其他类型计算=%d" % (m37["n"], m38["n"], len(d_other)))
print("[SAMPLE] 2026.07 i37=%d i38=%d 其他=%d" % (m37_dict.get('2026-07-31', 0), m38_dict.get('2026-07-31', 0), m37_dict.get('2026-07-31', 0) - m38_dict.get('2026-07-31', 0)))
