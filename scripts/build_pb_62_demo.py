#!/usr/bin/env python3
"""铅(PB) 6.2 精炼金属进出口子页 · v2 · 3 图全真数据（复用 build_pb_61.py v2 模板）。

图1 海关铅锭月度进口（季节/时序切换）：i17（月，吨）
图2 中国进口 vs 全球发运背景：i17 精炼铅进口(月) + i7 LME 全球注销仓单(日)（双轴）
图3 LME 全球注销仓单（季节/时序切换）：i7（日，吨）

⚠️ 归属说明：i7 LME 全球注销仓单本身属 4.1，但作为 6.2 的"全球发运背景"辅轴是合理的对比参照，非归属错误。
⚠️ 数据源缺口：粗铅/铅合金独立口径、出口目的地分布、铅锭出口总量(a10017091 量级极小)——详见 62_diversify_20260828.md。
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


def chart_line_t(cid, title, sub, color, data, default_seasonal=False):
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
            '<button onclick="window.__tgl(\'%s\',this)">☀ 季节</button></div>'
            ) % (title, sub, cid, cid)
    return html, js


def chart_dual(cid, title, sub, data_a, color_a, name_a, unit_a, data_b, color_b, name_b, unit_b):
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
            '<div id="%s" style="width:100%%;height:320px"></div></div>'
            ) % (title, sub, cid)
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
footer{margin-top:20px;font-size:12px;color:#586069;text-align:center;border-top:1px solid #21262d;padding-top:16px}
.note{font-size:12px;color:#8b949e;padding:12px;border-top:1px solid #21262d;margin-top:8px}
.note strong{color:#c9d1d9}"""

ANTI = """document.oncontextmenu=e=>{e.preventDefault();return false};
document.onkeydown=e=>{if(e.ctrlKey&&['c','s','p','u'].includes(e.key.toLowerCase())){e.preventDefault();return false}};
document.onselectstart=e=>{e.preventDefault();return false};"""

NOW = datetime.now().strftime("%Y-%m-%d")

# === 读数据 ===
m17 = load_metric("i17")   # 海关铅锭进口量（月, 吨）
m7 = load_metric("i7")     # LME 全球注销仓单（日, 吨）

d17 = pairs(m17)
d7 = pairs(m7)

# === 图1：海关铅锭月度进口（季节/时序切换）===
h1, j1 = chart_line_t(
    "echart_62_c1",
    "海关铅锭月度进口量（6.2 精炼金属正主，季节/时序切换）",
    "海关 · 月 · 吨 · i17 %d 点 · 2018-01 至 %s" % (m17["n"], latest(m17)),
    "#b06a32",
    d17,
    default_seasonal=True
)

# === 图2：中国进口 vs 全球发运背景（双轴）===
h2, j2 = chart_dual(
    "echart_62_c2",
    "中国精炼铅进口(月) vs LME 全球注销仓单(日) —— 中国补库 vs 全球发运背景",
    "海关(月,吨) · LME(日,吨) · i17 %d 点 / i7 %d 点 · 至 %s / %s" % (m17["n"], m7["n"], latest(m17), latest(m7)),
    d17, "#b06a32", "中国精炼铅进口", "吨(海关,月,左)",
    d7, "#c96a5b", "LME 全球注销仓单", "吨(LME,日,右)"
)

# === 图3：LME 全球注销仓单（季节/时序切换）===
h3, j3 = chart_line_t(
    "echart_62_c3",
    "LME 全球注销仓单（发运背景分母，季节/时序切换）",
    "LME · 日 · 吨 · i7 %d 点 · 2018-01 至 %s" % (m7["n"], latest(m7)),
    "#c96a5b",
    d7,
    default_seasonal=True
)

# === 拼装页面 ===
page_html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 6.2 精炼金属进出口 · 有色金属研究框架</title>
<style>""" + CSS + """</style></head><body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK v2</small></div>
  <div class="hcrumbs">铅(PB) · 6 进出口 · 6.2 精炼金属进出口 · v2 3 图</div>
  <div class="hright">数据固化快照 · """ + NOW + """ · 海关/LME</div>
</div>
<div class="panel">
""" + h1 + h2 + h3 + """
<div class="note">
<strong style="color:#c9d1d9">6.2 定义与数据源说明：</strong>6.2「精炼金属进出口」= 进口未锻轧精炼铅(HS 7801) → 分国别来源 → 国内消费；同时铅锭出口 → 分目的地。这条"精炼金属双向贸易"链条。<br>
<strong style="color:#c9d1d9">指标组</strong>：i17 海关铅锭进口量(月,吨) · i7 LME 全球注销仓单(日,吨,作全球发运背景)。<br>
<strong style="color:#c9d1d9">归属说明</strong>：i7 LME 全球注销仓单本身属 4.1 库存，但作为 6.2 的"全球发运背景"辅轴是合理的对比参照（中国进口与全球发运量的对照），非归属错误。<br>
<strong style="color:#c9d1d9">数据源缺口</strong>：<br>
· 粗铅/铅合金独立口径：知几无独立序列 → 剔除；<br>
· 进口来源国月度矩阵：无原始数据 → 用 i17 总量代理 + 页脚备注印度 3626/澳洲 1613(2026.7)；<br>
· 出口目的地分布：SMM 有总量 a10017091 但非分目的地 → 剔除；<br>
· 铅锭出口总量 a10017091：SMM 有但量级极小（2026.7=2178 吨 vs 进口 9215 吨，<1/4）→ 不入库，标注为"出口数据缺口"。<br>
详见 analysis/iwencai/PB/62_diversify_20260828.md 自检报告。
</div>
</div>
<footer>有色金属产业指标树 · 铅(PB) 6.2 精炼金属进出口 · v2（3 图全真数据 · HS 7801 精炼金属正主）· indicators_v1.json v1.7</footer>
<script src="assets/echarts.min.js"></script>
<script>
""" + ANTI + """
""" + j1 + "\n" + j2 + "\n" + j3 + """
function __tgl(id,btn){var cur=window['__mode_'+id],nxt=cur==='ts'?'se':'ts';
window['__mode_'+id]=nxt;window['__inst_'+id].setOption(window['__opts_'+id][nxt],true);
btn.textContent=nxt==='ts'?'⏱ 时序':'☀ 季节';}
window.addEventListener('resize',function(){['echart_62_c1','echart_62_c2','echart_62_c3'].forEach(function(id){var el=document.getElementById(id);var inst=echarts.getInstanceByDom(el);if(inst)inst.resize();});});
</script></body></html>"""

out_path = os.path.join(os.path.dirname(BASE), "pb_62_import_export.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(page_html)
print("[OK] 已生成: %s (%d 字节)" % (out_path, len(page_html)))
print("[POINTS] i17=%d i7=%d" % (m17["n"], m7["n"]))
