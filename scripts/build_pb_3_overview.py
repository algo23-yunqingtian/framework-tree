#!/usr/bin/env python3
"""铅(PB) 板块3【供给】总览页 · v1 · 3.1.1-3.2.4 导航入口。

对称 pb_2_overview / pb_6_overview。当前仅 3.2.3 上线，其余 9 节点标注「待填充」。
主题色 #7a8c5b（板块3 供给·矿绿，区别于板块2金色/板块6紫色）。
"""
import os
from pathlib import Path

CARDS = [
    # (节点号, 名称, 链接或 None, 图表摘要, 指标, 数据质量, 状态)
    ("3.1.1", "海外矿·财报产量", None,
     "主要铅矿企业季度产量（ILZSG/USGS）",
     "待知几验证：USGS/ILZSG 海外矿产量序列",
     "待填充", "待填充"),
    ("3.1.2", "海外矿·分国别总量", None,
     "中国/秘鲁/澳/塔/巴 分国别矿产量",
     "ID00300294 系列 中国有色金属工业年鉴分国别(年)",
     "待填充", "待填充"),
    ("3.1.3", "国内矿产量", None,
     "国内铅矿矿产量 + 精矿产量",
     "Mysteel 国内铅矿产量(月)",
     "待填充", "待填充"),
    ("3.1.4", "矿进口量与分国别", None,
     "海关铅精矿月度进口 + 分国别",
     "i40 海关铅精矿进口(月) · 已在 6.1 展示",
     "跨板块复用", "待填充"),
    ("3.1.5", "TC 加工费", None,
     "国产TC + 进口TC + 矿端紧松",
     "j25_tc 国产TC · 已在 2.5 展示",
     "跨板块复用", "待填充"),
    ("3.2.1", "精炼产量", None,
     "精炼铅总产量 + 冶炼产量",
     "Mysteel 精炼铅产量(月)",
     "待填充", "待填充"),
    ("3.2.2", "开工率与检修", None,
     "原生铅开工率 + 检修停产损失量",
     "Mysteel 原生铅开工率/检修事件",
     "待填充", "待填充"),
    ("3.2.3", "再生/二次供应", "pb_32_3_regen_supply.html",
     "图1 再生铅有效供应(产量×利用率×原料库存) / 图2 原生vs再生供应结构(再生占比) / 图3 产能利用率双口径 / 图4 产量季节图",
     "j323_regen_output 再生精铅产量(月) · j323_regen_util 产能利用率(月) · j323_regen_util_w 30家样本(周) · j323_native_output 原生铅产量(月) · i12 再生原料库存(周)",
     "91月+380周 4图全真", "✅ 已上线"),
    ("3.2.4", "冶炼利润→供应弹性", None,
     "冶炼利润驱动的供应弹性",
     "j24_regen_profit 再生利润 · 已在 2.4 展示",
     "跨板块复用", "待填充"),
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
  <div class="sub">10 个子节点 · 3.2.3 再生/二次供应已上线（3 图全真数据）· 其余 9 节点待填充 · indicators_v1.json v2.5 · 2026-08-29</div>

  <div class="note">
    <b>板块3 覆盖：</b>矿端（3.1.1 海外矿财报 / 3.1.2 分国别 / 3.1.3 国内矿 / 3.1.4 矿进口 / 3.1.5 TC加工费）+ 冶炼端（3.2.1 精炼产量 / 3.2.2 开工率与检修 / 3.2.3 再生二次供应 / 3.2.4 冶炼利润供应弹性）。<br>
    <b>先行上线 3.2.3 的原因：</b>铅的核心定价锚是「再生铅定价」，再生铅 2025 年已占中国铅总产量约 51.6%（SMM 口径），是供给端的主导变量；而矿端节点（3.1.x）缓存数据陈旧（i16 防城到港止于 2020、i5 精矿港口库存止于 2023-09、i10 原料库存止于 2022-04），需换外部数据源后再建。<br>
    <b>跨板块复用提示：</b>3.1.4 矿进口（i40）已在 6.1 展示；3.1.5 TC加工费（j25_tc）与 3.2.4 冶炼利润（j24_regen_profit）已在 2.5 / 2.4 展示，建页时需换视角避免口径重复。<br>
    <b>数据底座：</b>SMM 再生精铅产量（月）+ Mysteel 再生铅产能利用率（月/30家周度）+ Mysteel 原生铅产量（月）+ SMM 再生铅原料库存（周）。
  </div>

  <div class="grid">{cards_html}
  </div>

  <div class="footer">
    有色金属产业指标树 · 铅(PB) · 板块3 供给总览 · v1 · 2026-08-29<br>
    <a href="index.html" style="color:#7a8c5b;text-decoration:none">← 返回 framework-tree 主站</a>
  </div>
</div>
</body></html>'''

out = str(Path(__file__).resolve().parent.parent / 'pb_3_overview.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print('[OK] 已生成 %s (%d 字节)' % (out, os.path.getsize(out)))
