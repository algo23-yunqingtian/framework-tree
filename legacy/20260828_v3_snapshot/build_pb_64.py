#!/usr/bin/env python3
"""铅(PB) 6.4 海外对华发运子页 · v2 · 3 图全真数据（复用 build_pb_62_demo 模板）。

图1 LME 新加坡出发仓：i19 SG 注册 + i20 SG 注销（双轴联动）
图2 发运-到港节奏：i25 SG 出库量(日) + i17 海关铅锭进口(月)（双轴联动）
图3 海外 LME 分地区结构：i19 SG + i29 仁川 + i30 迪拜（三系列堆叠）

数据源：framework-tree/scripts/api_cache.db（i7/i17/i19/i20/i24/i25/i29/i30，全部 verified=true）
无新增 zhiji_id，无需再跑 refresh_cache。参见 analysis/iwencai/PB/64_diversify_20260828.md 自检报告。
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


def chart_dual(cid, title, sub, data_a, color_a, name_a, unit_a, data_b, color_b, name_b, unit_b, note):
    """双轴复合图：data_a 走左轴，data_b 走右轴。带图备注。"""
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
                 data_c, color_c, name_c, unit_c, note):
    """三系列堆叠面积图：三个指标共享左轴，用于展示分仓占比结构。带图备注。"""
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
footer{margin-top:20px;font-size:12px;color:#586069;text-align:center;border-top:1px solid #21262d;padding-top:16px}
.chart-note{font-size:12px;color:#a8c0d8;background:#10151c;border-left:3px solid #5b7a8c;padding:8px 10px;margin-top:8px;border-radius:0 4px 4px 0;line-height:1.6}
.note{font-size:12px;color:#8b949e;padding:12px;border-top:1px solid #21262d;margin-top:8px}
.note strong{color:#c9d1d9}"""

ANTI = """document.oncontextmenu=e=>{e.preventDefault();return false};
document.onkeydown=e=>{if(e.ctrlKey&&['c','s','p','u'].includes(e.key.toLowerCase())){e.preventDefault();return false}};
document.onselectstart=e=>{e.preventDefault();return false};"""

NOW = datetime.now().strftime("%Y-%m-%d")

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

# === 拼装页面 ===
page_html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 6.4 海外对华发运 · 有色金属研究框架</title>
<style>""" + CSS + """</style></head><body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK v2</small></div>
  <div class="hcrumbs">铅(PB) · 6 进出口 · 6.4 海外对华发运 · v3 3 图(带图备注)</div>
  <div class="hright">数据固化快照 · """ + NOW + """ · Zhiji/LME/海关</div>
</div>
<div class="panel">
""" + h1 + h2 + h3 + """
<div class="note">
<strong style="color:#c9d1d9">6.4 定义与数据源说明：</strong>6.4「海外对华发运」= 出发仓(LME 分地区)→发运动作(出库量)→到港(海关月度)链条。<br>
<strong style="color:#c9d1d9">指标组</strong>：i19 SG 注册仓单 / i20 SG 注销仓单 / i25 SG 出库量 / i29 仁川 / i30 迪拜 / i17 海关铅锭进口(月) / i7 LME 全球注销仓单。<br>
<strong style="color:#c9d1d9">数据源缺口</strong>：同花顺 6.4 推荐图中「在途量」「提单量」「提单库存」「升贴水」SMM/Mysteel 均无公开序列，已剔除（详见 analysis/iwencai/PB/64_diversify_20260828.md 自检报告）；「印度/哈萨克斯坦分国别月度矩阵」印度无 LME 授权仓，暂用 SG 总量作代理。<br>
<strong style="color:#c9d1d9">v2 变更</strong>：i40 海关铅精矿进口已从 6.4 调回 6.1 原料进口正主（indicators_v1.json v1.9）；本页面改用 LME 分地区+海关序列组合，无需新增 zhiji_id。
</div>
</div>
<footer>有色金属产业指标树 · 铅(PB) 6.4 海外对华发运 · v2（3 图全真数据 · LME 分地区代理）· indicators_v1.json v1.9</footer>
<script src="assets/echarts.min.js"></script>
<script>
""" + ANTI + """
""" + j1 + "\n" + j2 + "\n" + j3 + """
window.addEventListener('resize',function(){['echart_64_c1','echart_64_c2','echart_64_c3'].forEach(function(id){var el=document.getElementById(id);var inst=echarts.getInstanceByDom(el);if(inst)inst.resize();});});
</script></body></html>"""

out_path = os.path.join(os.path.dirname(BASE), "pb_64_overseas_shipping.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(page_html)
print("[OK] 已生成: %s (%d 字节)" % (out_path, len(page_html)))
print("[POINTS] i19=%d i20=%d i25=%d i17=%d i29=%d i30=%d" % (m19["n"], m20["n"], m25["n"], m17["n"], m29["n"], m30["n"]))
