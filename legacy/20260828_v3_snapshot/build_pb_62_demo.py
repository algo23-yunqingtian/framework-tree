#!/usr/bin/env python3
"""铅(PB) 6.2 精炼金属进出口子页 · v3 · 3 图全真数据（用户反馈重构版）。

图1 海关铅锭月度进口（季节/时序切换）：i17（月，吨）—— 同花顺图1"进出口总量季节"进口侧的落地
图2 未锻轧铅进出口双向：i17 进口 + i41 出口 双轴 —— 同花顺图5"HS 7801 进出口双向月度时序"
图3 精炼铅净进口（计算）：i17 - i41 —— 同花顺图1"净进口补充还是净出口外流"

⚠️ 每张图下方带"图备注"= 观测用途(什么时候看) + 指标关系(图里各指标怎么配合)。
i7 LME 全球注销仓单移出 6.2（用户反馈与进出口关联牵强）——它属 4.1/6.4 发运背景。
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


def chart_line_t(cid, title, sub, color, data, note, default_seasonal=False):
    """单变量双模式图（时序⇄季节切换）+ 图备注。"""
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


def chart_dual(cid, title, sub, data_a, color_a, name_a, unit_a, data_b, color_b, name_b, unit_b, note):
    """双轴复合图 + 图备注。"""
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
m17 = load_metric("i17")   # 海关铅锭进口量（月, 吨）
m41 = load_metric("i41")   # 海关铅锭出口量（月, 吨）

d17 = pairs(m17)
d41 = pairs(m41)

# 净进口 = i17 - i41（计算指标）
d17d = {d: v for d, v in d17}
d41d = {d: v for d, v in d41}
common = sorted(set(d17d.keys()) & set(d41d.keys()))
d_net = [[d, d17d[d] - d41d.get(d, 0)] for d in common]

# === 图1：海关铅锭月度进口（季节/时序切换）===
h1, j1 = chart_line_t(
    "echart_62_c1",
    "中国海关铅锭进口量（月度）—— 6.2 精炼金属正主",
    "海关 · 月 · 吨 · i17 %d 点 · 2018-01 至 %s" % (m17["n"], latest(m17)),
    "#b06a32",
    d17,
    "什么时候看：进口窗口是否打开、国内缺口靠进口补多少。<br>"
    "怎么看：进口量高于历史同期 = 进口窗口打开/LME-沪铅价差有利抄底；连续下降 = 窗口关闭或海外无货可发。",
    default_seasonal=True
)

# === 图2：进出口双向（同花顺图5）===
h2, j2 = chart_dual(
    "echart_62_c2",
    "未锻轧铅进出口双向（HS 7801）—— 中国是净买方还是净卖方",
    "海关 · 月 · 吨 · i17 进口 %d 点 / i41 出口 %d 点 · 至 %s" % (m17["n"], m41["n"], latest(m17)),
    d17, "#b06a32", "精炼铅进口", "吨(月,左)",
    d41, "#5b98c9", "精炼铅出口", "吨(月,右)",
    "什么时候看：判断中国在全球铅贸易中的角色切换、出口窗口是否打开。<br>"
    "两个指标的关系：进口(左轴)是把海外货拉回国内，出口(右轴)是把国内货送往海外；<br>"
    "两者都是 HS 7801 精炼铅的月度物理流向。进口主线放大而出口无起色 = 净进口扩大 = 国内缺口靠进口补；<br>"
    "出口跳升（如2024-2025铅价内外倒挂时） = 出口利润打开、货往外流。进口 vs 出口差距收窄 = 贸易流向反转信号。"
)

# === 图3：净进口（同花顺图1 净进口侧）===
h3, j3 = chart_line_t(
    "echart_62_c3",
    "精炼铅净进口量（月度）—— 进口补库 vs 出口外流对冲后的净结果",
    "海关 · 月 · 吨 · 计算 i17-i41 · %d 点 · 至 %s" % (len(d_net), latest(m17)),
    "#9b6bb5",
    d_net,
    "什么时候看：只看一条线就知道国内净缺口方向。<br>"
    "怎么看：净进口 >0 且放大 = 国内真缺货靠进口补（利多转弱信号，因供给在补）；<br>"
    "净进口接近 0 或转负 = 国内不缺甚至外流（本地供给过剩，累库压力）。",
    default_seasonal=True
)

# === 拼装页面 ===
page_html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 6.2 精炼金属进出口 · 有色金属研究框架</title>
<style>""" + CSS + """</style></head><body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK v2</small></div>
  <div class="hcrumbs">铅(PB) · 6 进出口 · 6.2 精炼金属进出口 · v3 3 图(带图备注+双向)</div>
  <div class="hright">数据固化快照 · """ + NOW + """ · 海关</div>
</div>
<div class="panel">
""" + h1 + h2 + h3 + """
<div class="note">
<strong style="color:#c9d1d9">6.2 定义：</strong>进口未锻轧精炼铅(HS 7801) → 出口 → 净进口，这条"精炼金属双向贸易"链条。<br>
<strong style="color:#c9d1d9">指标组：</strong>i17 海关铅锭进口量(月,吨) · i41 海关铅锭出口量(月,吨,v1.9 新增) · 净进口=i17-i41(计算)。<br>
<strong style="color:#c9d1d9">v3 变更（用户反馈）：</strong>图2 由"进口+全球注销仓单"(关联牵强)改为"进口+出口"双向(对应同花顺图5)；i7 LME 全球注销仓单移出 6.2（属 4.1/6.4 发运背景）；新增 i41 出口指标；所有图表补"图备注"(📌 什么时候看+指标关系)。<br>
<strong style="color:#c9d1d9">数据源缺口：</strong>粗铅/铅合金独立口径、出口目的地分布（知几无分矩阵）、进口来源国月度矩阵（用总量代理，2026.7 印度 3626/澳洲 1613）。<br>
详见 analysis/iwencai/PB/62_diversify_20260828.md。
</div>
</div>
<footer>有色金属产业指标树 · 铅(PB) 6.2 精炼金属进出口 · v3（3 图全真数据 · HS 7801 双向）· indicators_v1.json v1.9</footer>
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
print("[POINTS] i17=%d i41=%d 净进口计算=%d" % (m17["n"], m41["n"], len(d_net)))
print("[SAMPLE 2026.07] 进口=%s 出口=%s 净进口=%s" % (d17d.get('2026-07-31'), d41d.get('2026-07-31'), (d17d.get('2026-07-31',0)-d41d.get('2026-07-31',0))))