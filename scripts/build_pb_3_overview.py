#!/usr/bin/env python3
"""铅(PB) 板块3【供给】总览页 · v2 · 3.1.1-3.2.4 导航入口。

对称 pb_2_overview / pb_6_overview。3.2.3 先上线，后 3.1.1-3.1.5/3.2.1/3.2.2/3.2.4 八节点全上线。
主题色 #7a8c5b（板块3 供给·矿绿，区别于板块2金色/板块6紫色）。
"""
import os
from pathlib import Path

CARDS = [
    # (节点号, 名称, 链接, 图表摘要, 指标, 数据质量, 状态)
    ("3.1.1", "海外矿·财报产量", "pb_311_overseas_mine.html",
     "图1 全球铅矿产量(正主) / 图2 铅矿到港防城 / 图3 进口铅精矿港口库存",
     "j311_ilm 全球铅矿产量(月) · i16 铅矿到港防城(月) · i5 进口铅精矿港口库存(周)",
     "102月+294月+432周 3图全真", "✅ 已上线"),
    ("3.1.2", "海外矿·分国别总量", "pb_312_overseas_by_country.html",
     "图1 全球产量vs中国进口 / 图2 全球产量季节图 / 图3 分港口结构",
     "j311_ilm 全球铅矿产量(月) · i40 海关铅精矿进口(月) · i16 防城到港(月) · i5 港口库存(周)",
     "102月+103月+294月+432周 3图全真", "✅ 已上线"),
    ("3.1.3", "国内矿产量", "pb_313_domestic_mine.html",
     "图1 青海铅精矿产量(正主) / 图2 产量季节图 / 图3 国内原料库存",
     "j313_qh 青海铅精矿产量(月) · i10 铅精矿原料库存(月)",
     "65月+227月 3图全真", "✅ 已上线"),
    ("3.1.4", "矿进口量与分国别", "pb_314_mine_import.html",
     "图1 海关铅精矿进口量(正主) / 图2 SMM净进口季节图 / 图3 进口vs到港节奏",
     "i40 海关铅精矿进口(月) · j314_net_imp SMM净进口(月) · i16 防城到港(月)",
     "103月+31月+294月 3图全真", "✅ 已上线"),
    ("3.1.5", "TC 加工费", "pb_315_tc_fee.html",
     "图1 国产TC正主+进口辅助 / 图2 国产TC季节图 / 图3 TC分位带",
     "j25_tc 国产TC(日,正主) · j73_imp_tc 进口TC(日,辅助)",
     "1370日+2042日 3图全真", "✅ 已上线"),
    ("3.2.1", "精炼产量", "pb_321_refining_output.html",
     "图1 原生铅产量(正主) / 图2 原生vs再生对比 / 图3 原生产量季节图",
     "j323_native_output 原生铅产量(月) · j323_regen_output 再生精铅产量(月)",
     "101月+91月 3图全真", "✅ 已上线"),
    ("3.2.2", "开工率与检修", "pb_322_operating_rate.html",
     "图1 原生铅产能利用率周(正主) / 图2 原生vs再生开工率 / 图3 开工率季节图",
     "j322_native_util_w 原生产能利用率(周) · j323_smm_regen_rate 再生铅开工率(月)",
     "338周+103月 3图全真", "✅ 已上线"),
    ("3.2.3", "再生/二次供应", "pb_32_3_regen_supply.html",
     "图1 再生铅有效供应 / 图2 原生vs再生供应结构 / 图3 产能利用率双口径 / 图4 产量季节图",
     "j323_regen_output 再生精铅产量(月) · j323_regen_util 产能利用率(月) · j323_regen_util_w 30家样本(周) · j323_native_output 原生铅产量(月)",
     "91月+380周 4图全真", "✅ 已上线"),
    ("3.2.4", "冶炼利润→供应弹性", "pb_324_profit_elasticity.html",
     "图1 铅锭-再生精铅价差(正主) / 图2 再生铅炉型利润对比 / 图3 利润季节图",
     "j324_primary_spread 精废价差(日) · j324_regen_profit_refl 反射炉利润(日) · j324_regen_profit_bof 富氧炉利润(日)",
     "1478日+1870日 3图全真", "✅ 已上线"),
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
.h1{font-size:26px;font-weight:700;color:#7a8c5b;margin-bottom:6px}
.sub{color:#8b949e;font-size:13px;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:28px}
.card{display:block;text-decoration:none;color:inherit;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px;transition:all .2s}
.card:hover{border-color:#7a8c5b;transform:translateY(-2px);background:#1a2028}
.card-off{opacity:.5;cursor:default}
.card-off:hover{border-color:#30363d;transform:none;background:#161b22}
.card-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.card-num{display:inline-block;background:#7a8c5b;color:#0f1419;font-weight:700;font-size:13px;padding:2px 8px;border-radius:4px}
.card-off .card-num{background:#30363d;color:#8b949e}
.card-title{font-size:17px;font-weight:600;color:#e6edf3}
.card-charts{font-size:13px;color:#c9d1d9;margin-bottom:8px}
.card-metrics{font-size:12px;color:#8b949e;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;margin-bottom:12px}
.card-foot{display:flex;justify-content:space-between;align-items:center;font-size:12px}
.badge{background:#21262d;color:#8b949e;padding:2px 8px;border-radius:10px;border:1px solid #30363d}
.go{color:#7a8c5b;font-weight:600}
.go.off{color:#6e7681}
.nav-back{display:flex;gap:16px;align-items:center;font-size:12px;margin-bottom:16px;user-select:none}
.nav-back a{color:#5b7a8c;text-decoration:none;padding:4px 10px;background:#161b22;border:1px solid #21262d;border-radius:6px;transition:color .15s,background .15s}
.nav-back a:hover{color:#c9d1d9;background:#21262d;text-decoration:none}
.note{background:#161b22;border:1px solid #30363d;border-left:3px solid #7a8c5b;border-radius:6px;padding:14px 16px;font-size:13px;color:#8b949e;margin-bottom:20px}
.note b{color:#c9d1d9}
.footer{border-top:1px solid #21262d;padding-top:16px;font-size:12px;color:#6e7681;text-align:center}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
'''

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 板块3 供给 · 总览</title>
<style>{CSS}</style></head>
<body>
<div class="wrap">
  <div class="nav-back"><a href="index.html">← 回主站</a></div>
  <div class="h1">铅(PB) · 板块3【供给】总览</div>
  <div class="sub">10 个子节点 · 3.1.1-3.2.4 全部上线（3.2.3 先上线，后 8 节点全上线）· indicators_v1.json v3.1 · 2026-08-31</div>

  <div class="note">
    <b>板块3 覆盖：</b>矿端（3.1.1 海外矿财报 / 3.1.2 分国别 / 3.1.3 国内矿 / 3.1.4 矿进口 / 3.1.5 TC加工费）+ 冶炼端（3.2.1 精炼产量 / 3.2.2 开工率与检修 / 3.2.3 再生二次供应 / 3.2.4 冶炼利润供应弹性）。<br>
    <b>3.1.5 TC加工费正主：</b>国产TC(a10127385)为正主，题材对象完全一致（树config定义）；进口TC(a10021355)=7.3正主，3.1.5仅作辅助交叉。<br>
    <b>3.2.2 开工率：</b>原生铅产能利用率(周,ID01030007)为正主，338点至2026-08；再生铅开工率(月)作辅助对比。<br>
    <b>3.2.4 供应弹性：</b>铅锭-再生精铅价差(ID01501478)为正主，1478点至2026-08；反射炉/富氧侧吹炉利润作炉型对比。<br>
    <b>数据底座：</b>ILZSG全球铅矿产量 + NBS青海铅精矿产量 + 中国海关铅精矿进口 + SMM国产TC/进口TC + Mysteel原生铅产量/产能利用率/精废价差/再生铅炉型利润。
  </div>

  <div class="grid">{cards_html}
  </div>

  <div class="footer">
    有色金属产业指标树 · 铅(PB) · 板块3 供给总览 · v2 · 2026-08-31<br>
    <a href="index.html" style="color:#7a8c5b;text-decoration:none">← 返回 framework-tree 主站</a>
  </div>
</div>
</body></html>'''

out = str(Path(__file__).resolve().parent.parent / 'pb_3_overview.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print('[OK] 已生成 %s (%d 字节)' % (out, os.path.getsize(out)))
