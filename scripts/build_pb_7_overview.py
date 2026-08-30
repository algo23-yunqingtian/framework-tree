#!/usr/bin/env python3
"""铅(PB) 板块7【成本利润】总览页 · v1 · 7.1-7.3 导航入口。

对称 pb_5_overview。当前 7.1/7.2/7.3 均已上线。
主题色 #b06a32（板块7 成本利润·橙红，区别于板块5青绿/板块3矿绿/板块2金色）。
"""
import os
from pathlib import Path

CARDS = [
    # (节点号, 名称, 链接, 图表摘要, 指标, 数据质量, 状态)
    ("7.1", "成本曲线与分位", "pb_71_cost_curve.html",
     "图1 铅冶炼加工成本 vs 白银收益 / 图2 加工成本季节图 / 图3 铅精矿TC vs 冶炼利润",
     "j25_smelt_cost 加工成本(日) · j25_ag_revenue 白银收益(日) · j25_tc 国产TC(日,2.5正主辅助) · j72_smelt_profit 冶炼利润(日,7.2正主辅助)",
     "1370点×4 3图全真", "✅ 已上线"),
    ("7.2", "日度利润测算", "pb_72_daily_profit.html",
     "图1 原生铅冶炼利润 vs 白银收益 / 图2 冶炼利润季节图 / 图3 再生铅利润 vs 废蓄电池价",
     "j72_smelt_profit 冶炼利润(日) · j25_ag_revenue 白银收益(日) · j24_regen_profit 再生利润(日,2.4正主辅助) · j25_battery 废蓄电池价(日)",
     "1370点+645点 3图全真", "✅ 已上线"),
    ("7.3", "能源/原料成本", "pb_73_energy_cost.html",
     "图1 硫酸价 vs 冶炼利润 / 图2 硫酸价季节图 / 图3 进口TC vs 国产TC",
     "j51_h2so4 硫酸价(日) · j72_smelt_profit 冶炼利润(日) · j73_imp_tc 进口TC(日) · j25_tc 国产TC(日,2.5正主辅助) · j73_elec_price 广西电解铝电价(月,备用)",
     "1370点+1570点 3图全真", "✅ 已上线"),
]

cards_html = ""
for num, title, href, charts, metrics, quality, status in CARDS:
    cls = "card" if href else "card card-off"
    go = '<span class="go">查看 →</span>' if href else '<span class="go off">待填充</span>'
    inner = ('''
      <div class="card-head">
        <span class="card-num">%s</span>
        <span class="card-title">%s</span>
      </div>
      <div class="card-charts">%s</div>
      <div class="card-metrics">%s</div>
      <div class="card-foot">
        <span class="badge">%s</span>
        %s
      </div>''' % (num, title, charts, metrics, quality, go))
    if href:
        cards_html += '<a class="%s" href="%s">%s</a>' % (cls, href, inner)
    else:
        cards_html += '<div class="%s">%s</div>' % (cls, inner)

CSS = '''
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f1419;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:32px;line-height:1.6;
     user-select:none;-webkit-user-select:none;-moz-user-select:none}
.wrap{max-width:1180px;margin:0 auto}
.h1{font-size:26px;font-weight:700;color:#b06a32;margin-bottom:6px}
.sub{color:#8b949e;font-size:13px;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:28px}
.card{display:block;text-decoration:none;color:inherit;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px;transition:all .2s}
.card:hover{border-color:#b06a32;transform:translateY(-2px);background:#1a2028}
.card-off{opacity:.5;cursor:default}
.card-off:hover{border-color:#30363d;transform:none;background:#161b22}
.card-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.card-num{display:inline-block;background:#b06a32;color:#0f1419;font-weight:700;font-size:13px;padding:2px 8px;border-radius:4px}
.card-off .card-num{background:#30363d;color:#8b949e}
.card-title{font-size:17px;font-weight:600;color:#e6edf3}
.card-charts{font-size:13px;color:#c9d1d9;margin-bottom:8px}
.card-metrics{font-size:12px;color:#8b949e;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;margin-bottom:12px}
.card-foot{display:flex;justify-content:space-between;align-items:center;font-size:12px}
.badge{background:#21262d;color:#8b949e;padding:2px 8px;border-radius:10px;border:1px solid #30363d}
.go{color:#b06a32;font-weight:600}
.go.off{color:#6e7681}
.nav-back{display:flex;gap:16px;align-items:center;font-size:12px;margin-bottom:16px;user-select:none}
.nav-back a{color:#5b7a8c;text-decoration:none;padding:4px 10px;background:#161b22;border:1px solid #21262d;border-radius:6px;transition:color .15s,background .15s}
.nav-back a:hover{color:#c9d1d9;background:#21262d;text-decoration:none}
.note{background:#161b22;border:1px solid #30363d;border-left:3px solid #b06a32;border-radius:6px;padding:14px 16px;font-size:13px;color:#8b949e;margin-bottom:20px}
.note b{color:#c9d1d9}
.footer{border-top:1px solid #21262d;padding-top:16px;font-size:12px;color:#6e7681;text-align:center}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
'''

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 板块7 成本利润 · 总览</title>
<style>{CSS}</style></head>
<body>
<div class="wrap">
  <div class="nav-back"><a href="index.html">← 回主站</a></div>
  <div class="h1">铅(PB) · 板块7【成本利润】总览</div>
  <div class="sub">成本利润 = 成本曲线与分位(季·同步) / 日度利润测算(日·同步) / 能源原料成本(月·先行)</div>
  <div class="note"><b>板块范围公告：</b>图表看板覆盖板块 2/3/4/5/6/7。板块8（供需平衡）不做图表。
  7.x 只做国内冶炼成本端——出口图已在 6.3(HS8507) 展示不重复。知几无铅C1现金成本/完全成本直接序列，需外部源(安泰科/长江有色)补充。</div>
  <div class="grid">
{cards_html}
  </div>
  <div class="footer">有色金属产业指标树 · 铅(PB) · 板块7 成本利润总览 v1 · indicators_v1.json v2.8 · 反拷贝保护开启</div>
</div>
</body></html>
'''

out = Path(os.path.dirname(os.path.abspath(__file__))).parent / "pb_7_overview.html"
out.write_text(HTML, encoding="utf-8")
print("已生成", out, out.stat().st_size, "bytes")
