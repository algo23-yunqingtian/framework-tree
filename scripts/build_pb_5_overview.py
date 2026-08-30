#!/usr/bin/env python3
"""铅(PB) 板块5【需求】总览页 · v1 · 5.1-5.3 导航入口。

对称 pb_3_overview / pb_6_overview。5.1/5.2/5.3 全部上线。
主题色 #4f8a7a（板块5 需求·青绿，区别于板块3矿绿/板块2金色/板块6紫色）。
"""
import os
from pathlib import Path

CARDS = [
    # (节点号, 名称, 链接或 None, 图表摘要, 指标, 数据质量, 状态)
    ("5.1", "初级消费", "pb_51_primary_consumption.html",
     "图1 表观消费 vs 实际消费 / 图2 表观消费量季节图 / 图3 铅酸电池开工率 vs 消费验证",
     "j51_apparent 表观消费(月) · j51_cons 实际消费(月) · j51_util 蓄电池开工率(周) · i18 铅锭社库(4.3正主) · j51_h2so4 硫酸价(7.x正主)",
     "102月+周度 3图全真", "✅ 已上线"),
    ("5.2", "终端细分消费", "pb_52_terminal_consumption.html",
     "图1 汽车销量 vs 铅蓄电池成品库存 / 图2 汽车销量季节图 / 图3 基站设备产量 vs 成品库存",
     "j52_car_sales 汽车销量(月) · j52_base_station 基站设备产量(月) · j52_battery_inv 蓄电池成品库存(月)",
     "102月+85月+31月 3图全真", "✅ 已上线"),
    ("5.3", "需求先行指标", "pb_53_demand_leading.html",
     "图1 下月预计开工率 vs 成品库存 / 图2 下月预计开工率季节图 / 图3 再生铅库存天数 vs 废电瓶动态",
     "j53_next_rate 下月预计开工率(月) · j53_waste_inv 废电瓶库存动态(月) · j53_regen_days 再生铅原料库存天数(月)",
     "3图全真", "✅ 已上线"),
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
.h1{font-size:26px;font-weight:700;color:#4f8a7a;margin-bottom:6px}
.sub{color:#8b949e;font-size:13px;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:28px}
.card{display:block;text-decoration:none;color:inherit;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px;transition:all .2s}
.card:hover{border-color:#4f8a7a;transform:translateY(-2px);background:#1a2028}
.card-off{opacity:.5;cursor:default}
.card-off:hover{border-color:#30363d;transform:none;background:#161b22}
.card-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.card-num{display:inline-block;background:#4f8a7a;color:#0f1419;font-weight:700;font-size:13px;padding:2px 8px;border-radius:4px}
.card-off .card-num{background:#30363d;color:#8b949e}
.card-title{font-size:17px;font-weight:600;color:#e6edf3}
.card-charts{font-size:13px;color:#c9d1d9;margin-bottom:8px}
.card-metrics{font-size:12px;color:#8b949e;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;margin-bottom:12px}
.card-foot{display:flex;justify-content:space-between;align-items:center;font-size:12px}
.badge{background:#21262d;color:#8b949e;padding:2px 8px;border-radius:10px;border:1px solid #30363d}
.go{color:#4f8a7a;font-weight:600}
.go.off{color:#6e7681}
.nav-back{display:flex;gap:16px;align-items:center;font-size:12px;margin-bottom:16px;user-select:none}
.nav-back a{color:#5b7a8c;text-decoration:none;padding:4px 10px;background:#161b22;border:1px solid #21262d;border-radius:6px;transition:color .15s,background .15s}
.nav-back a:hover{color:#c9d1d9;background:#21262d;text-decoration:none}
.note{background:#161b22;border:1px solid #30363d;border-left:3px solid #4f8a7a;border-radius:6px;padding:14px 16px;font-size:13px;color:#8b949e;margin-bottom:20px}
.note b{color:#c9d1d9}
.footer{border-top:1px solid #21262d;padding-top:16px;font-size:12px;color:#6e7681;text-align:center}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
'''

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 板块5 需求 · 总览</title>
<style>{CSS}</style></head>
<body>
<div class="wrap">
  <div class="nav-back"><a href="index.html">← 回主站</a></div>
  <div class="h1">铅(PB) · 板块5【需求】总览</div>
  <div class="sub">需求 = 初级消费(开工率·同步) / 终端细分消费(滞后) / 需求先行指标(先行1-2月)</div>
  <div class="note"><b>板块范围公告：</b>图表看板覆盖板块 2/3/4/5/6/7。板块8（供需平衡）不做图表。
  铅 80%+ 终端为铅酸蓄电池（启动/动力/储能三类），5.x 只做国内消费，出口图已在 6.3（HS8507）展示不重复。</div>
  <div class="grid">
{cards_html}
  </div>
  <div class="footer">有色金属产业指标树 · 铅(PB) · 板块5 需求总览 v1 · indicators_v1.json v2.7 · 反拷贝保护开启</div>
</div>
</body></html>
'''

out = Path(os.path.dirname(os.path.abspath(__file__))).parent / "pb_5_overview.html"
out.write_text(HTML, encoding="utf-8")
print("已生成", out, out.stat().st_size, "bytes")