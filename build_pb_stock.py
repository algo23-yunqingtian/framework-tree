import json

def load(fp):
    d = json.load(open(fp))
    return d.get("points", []), d

SERIES = {
    "i1": {"name": "LME铅库存", "unit": "吨", "src": "SMM · LME", "freq": "日",
           "file": "/tmp/pb_i1.json", "class": "4.1 交易所库存"},
    "i2": {"name": "SHFE铅仓单", "unit": "吨", "src": "SMM · 上期所", "freq": "日",
           "file": "/tmp/pb_i2.json", "class": "4.2 仓单"},
    "i3": {"name": "SMM铅锭五地社库", "unit": "万吨", "src": "SMM", "freq": "周",
           "file": "/tmp/pb_i3.json", "class": "4.3 社会库存"},
    "i4": {"name": "原生铅成品库存", "unit": "万吨", "src": "Mysteel", "freq": "周",
           "file": "/tmp/pb_i4.json", "class": "4.4 工厂库存"},
    "i5": {"name": "进口铅精矿港口库存", "unit": "万吨", "src": "Mysteel", "freq": "周",
           "file": "/tmp/pb_i5.json", "class": "4.5 隐性·在途库存"},
}

def to_nums(pts):
    out = []
    for p in pts:
        try:
            v = float(p["value"])
        except (TypeError, ValueError):
            continue
        out.append((p["date"], v))
    return out  # 已是倒序

def fmt(v):
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.2f}"

series_data = {}
meta = {}
for key, cfg in SERIES.items():
    pts, raw = load(cfg["file"])
    num = to_nums(pts)
    meta[key] = dict(cfg, latest=num[0] if num else None, count=len(num))
    series_data[key] = num

# === 构造 ECharts 选项（内联）===
echarts_opts = {}
for key, cfg in SERIES.items():
    num = series_data[key]
    # 最近250点展示
    show = num[-250:] if len(num) > 250 else num
    # 转为 ECharts 正序
    x = [d for d, v in show]
    y = [v for d, v in show]
    # 面积色
    color = {"i1": "#b06a32", "i2": "#7a8a9c", "i3": "#5b7a8c", "i4": "#7a8c5b", "i5": "#8c6b9c"}[key]
    echarts_opts[key] = json.dumps({
        "color": color,
        "grid": {"left": 55, "right": 25, "top": 30, "bottom": 35},
        "xAxis": {"type": "time", "axisLine": {"lineStyle": {"color": "#555"}},
                  "axisLabel": {"color": "#999", "fontSize": 10},
                  "splitLine": {"show": False}},
        "yAxis": {"type": "value", "name": cfg["unit"], "nameTextStyle": {"color": "#999"},
                  "axisLabel": {"color": "#999"},
                  "splitLine": {"lineStyle": {"color": "#333"}}},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "series": [{
            "type": "line", "showSymbol": False, "smooth": False,
            "data": [[x[i], y[i]] for i in range(len(x))],
            "lineStyle": {"width": 1.5, "color": color},
            "areaStyle": {"color": color, "opacity": 0.18},
            "emphasis": {"focus": "series"},
        }],
    })

# 元信息
meta_json = {}
for key, m in meta.items():
    latest = m["latest"]
    meta_json[key] = {"name": m["name"], "unit": m["unit"], "src": m["src"],
                      "freq": m["freq"], "cls": m["class"],
                      "latest_val": fmt(latest[1]) if latest else "-",
                      "latest_date": latest[0] if latest else "-",
                      "count": m["count"]}

# === 写 HTML ===
cards_html = ""
charts_html = ""
for key in ["i1", "i2", "i3", "i4", "i5"]:
    m = meta_json[key]
    cards_html += f'''
    <div class="kcard">
      <div class="kcls">{m["cls"]}</div>
      <div class="kname">{m["name"]}</div>
      <div class="kmain"><span class="kval">{m["latest_val"]}</span><span class="kunit">{m["unit"]}</span></div>
      <div class="kmeta">{m["src"]} · {m["freq"]}频 · 共{m["count"]}点</div>
      <div class="kdate">最新 {m["latest_date"]}</div>
    </div>'''
    charts_html += f'''
    <div class="chart-row">
      <div class="chart-head">
        <span class="ch-code">{key.upper()}</span>
        <span class="ch-name">{m["name"]}</span>
        <span class="ch-src">{m["src"]} · {m["freq"]} · {m["unit"]}</span>
      </div>
      <div id="echart_{key}" class="chart-box"></div>
    </div>'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB)库存 · 有色金属研究框架</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;background:#10141b;color:#d8dce5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;font-size:13px}}
.header{{background:#161b23;border-bottom:1px solid #252b36;padding:14px 28px;display:flex;align-items:center;gap:18px}}
.brand{{font-weight:700;font-size:16px;color:#e0c9a2;display:flex;align-items:center;gap:8px}}
.brand small{{font-weight:400;font-size:11px;color:#7a7468;margin-left:6px;letter-spacing:1px}}
.hcrumbs{{color:#8b8171;font-size:12px;margin-left:14px;padding-left:14px;border-left:1px solid #252b36}}
.hright{{margin-left:auto;font-size:11px;color:#7a7468;letter-spacing:1px}}
.kpi{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding:18px 28px;background:#10141b;border-bottom:1px solid #252b36}}
.kcard{{background:#161b23;border:1px solid #252b36;border-radius:6px;padding:14px 14px 12px;display:flex;flex-direction:column;gap:4px}}
.kcls{{font-size:10px;color:#7a8c5b;letter-spacing:1px;font-weight:600}}
.kname{{font-size:12.5px;color:#cfc8b8;font-weight:500}}
.kmain{{display:flex;align-items:baseline;gap:6px;margin-top:4px}}
.kval{{font-size:22px;font-weight:700;color:#e0c9a2}}
.kunit{{font-size:11px;color:#7a7468}}
.kmeta{{font-size:10px;color:#6f6a5d}}
.kdate{{font-size:10px;color:#8b8171;margin-top:2px}}
.charts{{padding:14px 28px 28px}}
.chart-row{{margin-bottom:14px;background:#161b23;border:1px solid #252b36;border-radius:6px;padding:12px 16px 6px}}
.chart-head{{display:flex;align-items:center;gap:12px;margin-bottom:6px}}
.ch-code{{font:700 11px Consolas,monospace;color:#b06a32}}
.ch-name{{font-size:12.5px;color:#cfc8b8;font-weight:500}}
.ch-src{{font-size:10px;color:#6f6a5d;margin-left:auto}}
.chart-box{{height:230px;width:100%}}
footer{{padding:12px 28px;color:#6f6a5d;font-size:11px;border-top:1px solid #252b36;text-align:center}}
@media(max-width:1100px){{.kpi{{grid-template-columns:repeat(2,1fr)}}}}
</style></head>
<body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK</small></div>
  <div class="hcrumbs">铅(PB) · 4 库存 · 5 子类</div>
  <div class="hright">数据固化快照 · 2026-08-26 · 来源:Zhiji SMM/Mysteel</div>
</div>
<div class="kpi">{cards_html}</div>
<div class="charts">{charts_html}</div>
<footer>有色金属产业指标树 · 铅(PB)库存 · 静态快照版(线上可直接访问)</footer>
<script src="assets/echarts.min.js"></script>
<script>
'''
for key in ["i1", "i2", "i3", "i4", "i5"]:
    html += f'\n  var c_{key} = echarts.init(document.getElementById("echart_{key}"), "dark");\n'
    html += f'  c_{key}.setOption({echarts_opts[key]});\n'
html += """
  window.addEventListener('resize', function(){
    ['i1','i2','i3','i4','i5'].forEach(k=>window['c_'+k]&&window['c_'+k].resize());
  });
</script>
<script>
document.oncontextmenu=function(){{return false}};
document.onkeydown=function(e){{if(e.key==='F12'||(e.ctrlKey&&['c','C','s','S','p','P'].includes(e.key))){{e.preventDefault();return false}}}};
document.onselectstart=function(){{return false}};
document.ondragstart=function(){{return false}};
</script>
</body></html>
"""

out = "/home/ubuntu/framework-tree/pb_stock.html"
open(out, "w", encoding="utf-8").write(html)
print(f"✅ 落地页生成 {out}")
print("各子类点数:", {k: meta_json[k]["count"] for k in meta_json})
