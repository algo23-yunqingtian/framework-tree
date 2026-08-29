#!/usr/bin/env python3
"""铅(PB) 板块1【价格信号】总览页 · v1 · 2.1-2.6 导航入口。

静态导航页：不依赖数据接口，纯 HTML+CSS，列出 6 个子节点页面卡片 + 每页 3 图摘要 + 指标覆盖情况。
供用户快速浏览板块1成果，也是后续板块总览页的模板。
"""
import json, os
from pathlib import Path

CARDS = [
    ("2.1", "盘面结构", "pb_21_price_structure.html",
     "图1 量价仓三联动 / 图2 收盘价季节 / 图3 成交持仓比",
     "j21_close · j21_volume · j21_oi（观kline PB D 3751日 2011起）", "3751 点全量"),
    ("2.2", "现货与升贴水", "pb_22_spot_premium.html",
     "图1 现货vs主力基差 / 图2 现货季节 / 图3 原生vs再生价差",
     "j22_spot 等8指标（SMM 1#铅现货全国+沪粤豫津 + 再生精铅 + 沪伦比）", "2101 点"),
    ("2.3", "海外价格", "pb_23_overseas_price.html",
     "图1 LME期限结构 / 图2 LME现货季节 / 图3 升贴水vs进口盈亏",
     "j23_lme_cash/3m/0to3/sp3 + j23_imp_profit（LME + SMM）", "2945 点"),
    ("2.4", "价差体系", "pb_24_spread_system.html",
     "图1 期现月差 / 图2 再生利润vs精废价差 / 图3 铅锌比价",
     "j24_spread_m/s + regen_profit + refine_spread（SMM + 沪锌kline）", "4731 点"),
    ("2.5", "估值与利润", "pb_25_valuation_profit.html",
     "图1 原生vs再生利润 / 图2 废电池vs再生精铅 / 图3 TC矿端",
     "j25_smelt_cost/ag_revenue/tc/battery（SMM 精炼铅成本及利润）", "2586 点"),
    ("2.6", "持仓席位观察", "pb_26_position_holder.html",
     "图1 量仓结构 / 图2 持仓季节 / 图3 量价背离",
     "j21_oi · j21_volume · j21_close（观kline PB D）", "3751 点全量"),
]

# 卡片 HTML
cards_html = ""
for num, title, href, charts, metrics, quality in CARDS:
    cards_html += f'''
    <a class="card" href="{href}">
      <div class="card-head">
        <span class="card-num">{num}</span>
        <span class="card-title">{title}</span>
      </div>
      <div class="card-charts">{charts}</div>
      <div class="card-metrics">{metrics}</div>
      <div class="card-foot">
        <span class="badge">数据 {quality}</span>
        <span class="go">查看 →</span>
      </div>
    </a>'''

CSS = '''
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f1419;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:32px;line-height:1.6}
.wrap{max-width:1180px;margin:0 auto}
.h1{font-size:26px;font-weight:700;color:#e5c07b;margin-bottom:6px}
.sub{color:#8b949e;font-size:13px;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:28px}
.card{display:block;text-decoration:none;color:inherit;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px;transition:all .2s}
.card:hover{border-color:#e5c07b;transform:translateY(-2px);background:#1a2028}
.card-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.card-num{display:inline-block;background:#e5c07b;color:#0f1419;font-weight:700;font-size:13px;padding:2px 8px;border-radius:4px}
.card-title{font-size:17px;font-weight:600;color:#e6edf3}
.card-charts{font-size:13px;color:#c9d1d9;margin-bottom:8px}
.card-metrics{font-size:12px;color:#8b949e;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;margin-bottom:12px}
.card-foot{display:flex;justify-content:space-between;align-items:center;font-size:12px}
.badge{background:#21262d;color:#8b949e;padding:2px 8px;border-radius:10px;border:1px solid #30363d}
.go{color:#e5c07b;font-weight:600}
.note{background:#161b22;border:1px solid #30363d;border-left:3px solid #e5c07b;border-radius:6px;padding:14px 16px;font-size:13px;color:#8b949e;margin-bottom:20px}
.note b{color:#c9d1d9}
.footer{border-top:1px solid #21262d;padding-top:16px;font-size:12px;color:#6e7681;text-align:center}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
'''

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 板块1 价格信号 · 总览</title>
<style>{CSS}</style></head>
<body>
<div class="wrap">
  <div class="h1">铅(PB) · 板块1【价格信号】总览</div>
  <div class="sub">6 个子节点全部上线 · 共 18 张图全真数据 · indicators_v1.json v2.4（73 指标）· 2026-08-29</div>

  <div class="note">
    <b>板块1 覆盖：</b>盘面结构 · 现货与升贴水 · 海外价格 · 价差体系 · 估值与利润 · 持仓席位观察。<br>
    <b>数据底座：</b>zhiji 观服务（kline 全品种日K）+ 料服务（SMM/LME 日频指标），全部落盘 api_cache.db 日频全量。<br>
    <b>待外部源：</b>2.6 前20会员多空/集中度（上期所会员持仓排名，知几无数据）；2.3 COMEX铅价（知几仅库存）。
  </div>

  <div class="grid">{cards_html}
  </div>

  <div class="footer">
    有色金属产业指标树 · 铅(PB) · 板块1 价格信号总览 · v1 · 2026-08-29<br>
    <a href="/" style="color:#e5c07b;text-decoration:none">← 返回 framework-tree 根目录</a>
  </div>
</div>
</body></html>'''

out = str(Path(__file__).resolve().parent.parent / 'pb_2_overview.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print('[OK] 已生成 %s (%d 字节)' % (out, os.path.getsize(out)))
