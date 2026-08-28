#!/usr/bin/env python3
"""chart_kits.py — framework-tree 静态页 Build 公共模块（P1 抽取，v1.0 2026-08-28）。

所有品种子页 build 脚本只做三件事：
  1. load_metric 读指标
  2. 调用 chart_line_t / chart_dual / chart_triple 定义图表（含图备注）
  3. 拼装页面（标题/页脚/note 专属文案）

公共能力：
  · load_metric / pairs / latest    — 读 api_cache.db 时序
  · chart_line_t                    — 单指标 时序⇄季节 双模式（季节=按月份历年均值，真数据）
  · chart_dual                      — 双轴复合图（左轴/右轴）
  · chart_triple                    — 三系列堆叠面积图
  · CSS / ANTI / JS_COMMON(cids)    — 样式 + 反拷贝 + __seasonalize/__tgl/resize

⚠️ 坑（从 build_pb_6X 实测沉淀，勿回退）：
  · 图备注/标题内嵌 ASCII 双引号会炸 Python 字符串 → 统一用中文引号「」
  · JS 模板用 % 格式化而非 f-string（f-string 内反斜杠 SyntaxError）
  · 季节按钮必须有真数据：se 分支 data=window.__seasonalize(__d)，不能硬编码 [null×12]
  · build 输出 HTML 到仓库根目录，用 out("pb_63_product_export.html") 定位
"""
import sqlite3, json, os
from datetime import datetime

# ============================================================
# 数据层
# ============================================================

def _connect():
    BASE = os.path.dirname(os.path.abspath(__file__))
    return BASE

BASE = _connect()
DB = os.path.join(BASE, "api_cache.db")
_CONN = sqlite3.connect(DB)
_CURSOR = _CONN.cursor()


def load_metric(mid, code="PB"):
    """从 api_cache.db 读取指标时序。返回 {name,unit,freq,n,points,dates,values} 或 None。"""
    r = _CURSOR.execute("SELECT data_json FROM indicator_cache WHERE metric=? AND code=?",
                        (mid, code)).fetchone()
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


def sub_series(m_a, m_b, name_a, name_b):
    """计算两条序列的差值（按共有日期），返回 [[date, diff], ...]。"""
    da = {d: v for d, v in pairs(m_a)}
    db = {d: v for d, v in pairs(m_b)}
    common = sorted(set(da.keys()) & set(db.keys()))
    return [[d, da[d] - db.get(d, 0)] for d in common], da, db

# ============================================================
# 图表 JS/HTML 模板（% 格式化，勿改 f-string）
# ============================================================

def chart_line_t(cid, title, sub, color, data, note='', default_seasonal=False,
                 seasonal_max_years=5, seasonal_min_year=None, seasonal_max_year=None):
    """单变量双模式图（时序⇄季节切换）+ 图备注。

    季节视图 = 历年各一条线，图例标年份，横轴 1-12 月（按年份分组的月度原始值，不做均值）。
    参数：
      seasonal_max_years: 最多显示最近 N 年（默认 5，含当年）
      seasonal_min_year / seasonal_max_year: 显式覆盖年份范围（传了就不自动算）
    """
    json_pts = json.dumps(data, ensure_ascii=False)
    color30 = color + "30"
    color00 = color + "00"
    # 年份范围：自动取最近 N 年
    years_str = "[]"
    if data:
        years = sorted({int(p[0][:4]) for p in data if p[1] is not None})
        if seasonal_min_year is not None:
            years = [y for y in years if y >= seasonal_min_year]
        if seasonal_max_year is not None:
            years = [y for y in years if y <= seasonal_max_year]
        if seasonal_max_years and len(years) > seasonal_max_years:
            years = years[-seasonal_max_years:]
        years_str = json.dumps(years, ensure_ascii=False)
    mode = "se" if default_seasonal else "ts"
    # 按钮初始文字 = 点击后会切到的视图（与 __tgl 翻转语义对齐）
    #   当前 ts(时序) → 按钮显示「☀ 季节」（点了切到季节）
    #   当前 se(季节) → 按钮显示「⏱ 时序」（点了切回时序）
    btn_txt = "⏱ 时序" if mode == "se" else "☀ 季节"
    js = ("var __yrs_%s=%s;\n"
          "var __pal_%s=['#b06a32','#5b98c9','#7a8c5b','#9b6bb5','#c87070','#c9a227','#5fb3a1','#8c6fb0','#a67d5a','#6a8caf'];\n"
          "window['__data_%s'] = %s;\n"
          "window['__opts_%s'] = {\n"
          "  ts: {\n"
          "    tooltip:{trigger:'axis'},grid:{left:55,right:60,top:30,bottom:40},\n"
          "    xAxis:{type:'time',axisLabel:{color:'#aaa',interval:0},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}},axisTick:{lineStyle:{color:'#444'}}},\n"
          "    yAxis:{type:'value',axisLabel:{color:'#aaa'},splitLine:{lineStyle:{color:'#333',type:'dashed'}},axisLine:{lineStyle:{color:'#444'}}},\n"
          "    series:[{name:'%s',type:'line',smooth:true,symbol:'circle',symbolSize:4,\n"
          "      lineStyle:{color:'%s',width:2},\n"
          "      areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'%s'},{offset:1,color:'%s'}]}},\n"
          "      data:window['__data_%s'],markPoint:{symbol:'circle',symbolSize:6,data:[{coord:[window['__data_%s'][window['__data_%s'].length-1][0],window['__data_%s'][window['__data_%s'].length-1][1]],\n"
          "        itemStyle:{color:'%s'},label:{show:false}}]}}]\n"
          "  },\n"
          "  se: {\n"
          "    tooltip:{trigger:'axis',confine:true},\n"
          "    legend:{data:__yrs_%s.map(function(y){return y+'年';}),textStyle:{color:'#ccc',fontSize:11},top:0,type:'scroll'},\n"
          "    grid:{left:55,right:60,top:35,bottom:40},\n"
          "    xAxis:{type:'category',data:['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
          "    yAxis:{type:'value',axisLabel:{color:'#aaa'},splitLine:{lineStyle:{color:'#333',type:'dashed'}},axisLine:{lineStyle:{color:'#444'}}},\n"
          "    series:window.__seasonalizeByYear(window['__data_%s'], __yrs_%s, __pal_%s)\n"
          "  }\n"
          "};\n"
          "window['__inst_%s'] = echarts.init(document.getElementById('%s'),'dark');\n"
          "window['__mode_%s'] = '%s';\n"
          "window['__inst_%s'].setOption(window['__opts_%s']['%s'], true);\n"
          ) % (cid, years_str, cid, cid, json_pts, cid, title, color, color30, color00,
               cid, cid, cid, cid, cid, color,
               cid, cid, cid,
               cid, cid, cid, cid, mode, cid, cid, mode)
    html = ('<div class="chart"><div class="chart-title">%s</div>'
            '<div class="chart-sub">%s</div>'
            '<div id="%s" style="width:100%%;height:320px"></div>'
            '<button onclick="window.__tgl(\'%s\',this)">__BTNTXT__</button>'
            '<div class="chart-note">📌 %s</div></div>'
            ) % (title, sub, cid, cid, note)
    html = html.replace("__BTNTXT__", btn_txt)
    return html, js


def chart_dual(cid, title, sub, data_a, color_a, name_a, unit_a, data_b, color_b, name_b, unit_b, note=''):
    """双轴复合图：data_a 左轴，data_b 右轴。带图备注。"""
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


def chart_triple(cid, title, sub, data_a, color_a, name_a, unit_a,
                 data_b, color_b, name_b, unit_b,
                 data_c, color_c, name_c, unit_c, note=''):
    """三系列堆叠面积图：共享左轴，分仓占比结构。带图备注。"""
    ja = json.dumps(data_a, ensure_ascii=False)
    jb = json.dumps(data_b, ensure_ascii=False)
    jc = json.dumps(data_c, ensure_ascii=False)
    color_a20 = color_a + "20"
    color_b20 = color_b + "20"
    color_c20 = color_c + "20"
    js = ("window['__data_%s'] = [%s, %s, %s];\n"
          "window['__opts_%s'] = {\n"
          "  tooltip:{trigger:'axis'},\n"
          "  legend:{data:['%s','%s','%s'],textStyle:{color:'#ccc'},top:0},\n"
          "  grid:{left:55,right:55,top:45,bottom:40},\n"
          "  xAxis:{type:'time',axisLabel:{color:'#aaa'},splitLine:{show:false},axisLine:{lineStyle:{color:'#444'}}},\n"
          "  yAxis:{type:'value',name:'%s',nameTextStyle:{color:'#aaa'},axisLabel:{color:'#aaa'},splitLine:{lineStyle:{color:'#333',type:'dashed'}},axisLine:{lineStyle:{color:'#444'}}},\n"
          "  series:[\n"
          "    {name:'%s',type:'line',stack:'all',smooth:true,symbol:'none',lineStyle:{color:'%s',width:1},areaStyle:{color:'%s'},data:%s},\n"
          "    {name:'%s',type:'line',stack:'all',smooth:true,symbol:'none',lineStyle:{color:'%s',width:1},areaStyle:{color:'%s'},data:%s},\n"
          "    {name:'%s',type:'line',stack:'all',smooth:true,symbol:'none',lineStyle:{color:'%s',width:1},areaStyle:{color:'%s'},data:%s}\n"
          "  ]\n"
          "};\n"
          "window['__inst_%s'] = echarts.init(document.getElementById('%s'),'dark');\n"
          "window['__inst_%s'].setOption(window['__opts_%s'], true);\n"
          ) % (cid, ja, jb, jc, cid, name_a, name_b, name_c, unit_a,
               name_a, color_a, color_a20, ja,
               name_b, color_b, color_b20, jb,
               name_c, color_c, color_c20, jc,
               cid, cid, cid, cid)
    html = ('<div class="chart"><div class="chart-title">%s</div>'
            '<div class="chart-sub">%s</div>'
            '<div id="%s" style="width:100%%;height:320px"></div>'
            '<div class="chart-note">📌 %s</div></div>'
            ) % (title, sub, cid, note)
    return html, js

# ============================================================
# 页面公共件
# ============================================================

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


def JS_COMMON(cids):
    """生成公共 JS：__seasonalize(历月均值,兼容保留) + __seasonalizeByYear(历年各一条线) + __tgl + resize。"""
    ids_js = ",".join("'%s'" % c for c in cids)
    return ("function __seasonalize(arr){var g={};for(var i=0;i<arr.length;i++){"
            "var m=parseInt(arr[i][0].split('-')[1],10)-1;"
            "if(m<0||m>11||arr[i][1]==null)continue;g[m]=g[m]||[];g[m].push(arr[i][1]);}"
            "var out=[];for(var k=0;k<12;k++){var v=g[k];"
            "out.push(v?Math.round(v.reduce(function(a,b){return a+b},0)/v.length):null);}"
            "return out;}\n"
            "function __seasonalizeByYear(arr,years,palette){var ys=(years||[]).slice().sort();var pal=palette||['#b06a32','#5b98c9','#7a8c5b','#9b6bb5','#c87070','#c9a227','#5fb3a1','#8c6fb0','#a67d5a','#6a8caf'];var by={};for(var y=0;y<ys.length;y++)by[ys[y]]=null;for(var i=0;i<arr.length;i++){var d=arr[i][0];var v=arr[i][1];if(v==null)continue;var yr=parseInt(d.substring(0,4),10);var mm=parseInt(d.substring(5,7),10)-1;if(mm<0||mm>11)continue;if(by[yr]===undefined)continue;if(by[yr]===null)by[yr]=new Array(12);by[yr][mm]=v;}var series=[];for(var yi=0;yi<ys.length;yi++){var yv=ys[yi];var dat=by[yv];if(!dat)continue;var color=pal[yi %% pal.length];var nonNull=0;for(var k=0;k<12;k++)if(dat[k]!==null)nonNull++;if(nonNull<3)continue;var rounded=[];for(var k=0;k<12;k++)rounded.push(dat[k]===null?null:Math.round(dat[k]));series.push({name:yv+'年',type:'line',smooth:true,symbol:'circle',symbolSize:5,connectNulls:true,lineStyle:{color:color,width:2},itemStyle:{color:color},data:rounded});}return series;}\n"
            "function __tgl(id,btn){var cur=window['__mode_'+id],nxt=cur==='ts'?'se':'ts';\n"
            "window['__mode_'+id]=nxt;window['__inst_'+id].setOption(window['__opts_'+id][nxt],true);\n"
            "btn.textContent=nxt==='ts'?'☀ 季节':'⏱ 时序';}\n"
            "window.addEventListener('resize',function(){[" + ids_js + "].forEach(function(id){"
            "var el=document.getElementById(id);var inst=echarts.getInstanceByDom(el);if(inst)inst.resize();});});\n")


def page_html(title, hcrumbs, hright, h1, h2, h3, note_html, footer_text, js_body, cids):
    """拼装完整页面骨架。js_body=各图 js 拼接，cids=本页全部图表id（resize用）。"""
    return ("""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · 有色金属研究框架</title>
<style>""" + CSS + """</style></head><body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK v2</small></div>
  <div class="hcrumbs">%s</div>
  <div class="hright">数据固化快照 · """ + NOW + """ · %s</div>
</div>
<div class="panel">
%s
<div class="note">
%s
</div>
</div>
<footer>%s</footer>
<script src="assets/echarts.min.js"></script>
<script>
""" + ANTI + """
%s
""" + JS_COMMON(cids) + """
</script></body></html>""") % (title, hcrumbs, hright, h1 + h2 + h3, note_html, footer_text, js_body)


def out(fname):
    """输出 HTML 到仓库根目录，返回完整路径。"""
    path = os.path.join(os.path.dirname(BASE), fname)
    return path


def write_html(fname, content):
    path = out(fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] 已生成: %s (%d 字节)" % (path, len(content)))
    return path