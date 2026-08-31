#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_overview_all.py — 批量生成 31 个总览页（overview），消除全站 133 死链。

覆盖范围：
- cu_7_overview（铜成本，1 个）
- zn_2 ~ zn_7（锌，6 个）
- ni_2 ~ ni_7（镍，6 个）
- sn_2 ~ sn_7（锡，6 个）
- si_2 ~ si_7（硅，6 个）
- li_2 ~ li_7（锂，6 个）

红线：
- 不碰任何子页 HTML
- 不碰 indicators_v1.json
- 不碰 check_html.py / verify_render.js / reclaim.py 校验逻辑
- 已存在的子页做可点卡片（✅已上线），不存在的做静态 .card.off div（不做假链接）
- 总览页不进 check_html/verify_render 图表页计数（保持口径一致）
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TREE = json.load(open('data/tree_config.json', encoding='utf-8'))
COMM_COLOR = {c['code'].lower(): c.get('color', '#8fa3c4') for c in TREE['commodities']}
COMM_NAME = {c['code'].lower(): c['name'] for c in TREE['commodities']}
CATS = {c['id']: c for c in TREE['categories']}

# 已存在文件
EXISTING = set(os.listdir('.'))

# 板块 ID -> 板块序号
CATNUM = {'price': '2', 'supply': '3', 'inventory': '4', 'demand': '5', 'trade': '6', 'cost': '7'}

# 板块中文名
CAT_CN = {'price': '价格信号', 'supply': '供给', 'inventory': '库存', 'demand': '需求', 'trade': '进出口', 'cost': '成本·利润'}

# 品种 code 映射：文件名前缀 -> tree_config code（锂 LC 特殊）
FILE2TREE = {'li': 'lc'}
def tree_code(file_prefix):
    return FILE2TREE.get(file_prefix, file_prefix)

def cat_children(cat_id):
    return [(k['code'], k['name'], k.get('q', '')) for k in CATS[cat_id]['children']]

CSS = """*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f1419;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:32px;line-height:1.6}
.wrap{max-width:1180px;margin:0 auto}
.h1{font-size:26px;font-weight:700;color:%s;margin-bottom:6px}
.sub{color:#8b949e;font-size:13px;margin-bottom:24px}
.nav-back{margin-bottom:18px}
.nav-back a{color:%s;text-decoration:none;font-size:13px}
.nav-back a:hover{text-decoration:underline}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:28px}
.card{display:block;text-decoration:none;color:inherit;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px;transition:all .2s}
.card:hover{border-color:%s;transform:translateY(-2px);background:#1a2028}
.card.off{opacity:.55}
.card.off:hover{transform:none;background:#161b22;border-color:#30363d}
.card-head{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.card-num{display:inline-block;background:#30363d;color:#dfe6f0;font-weight:700;font-size:13px;padding:2px 8px;border-radius:4px}
.card-title{font-size:17px;font-weight:600;color:#e6edf3}
.card-charts{font-size:13px;color:#8b949e;margin-bottom:8px;font-style:italic}
.card-metrics{font-size:12px;color:#6e7681;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;margin-bottom:12px;word-break:break-all}
.card-foot{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px}
.badge{background:#21262d;color:#8b949e;padding:2px 8px;border-radius:10px;border:1px solid #30363d}
.badge.on{color:%s}
.note{background:#161b22;border:1px solid #30363d;border-left:3px solid %s;border-radius:6px;padding:14px 16px;font-size:13px;color:#8b949e;margin-bottom:20px}
.note b{color:#c9d1d9}
.note code{color:%s;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.footer{border-top:1px solid #21262d;padding-top:16px;font-size:12px;color:#6e7681;text-align:center}
.footer a{color:%s;text-decoration:none}
@media(max-width:820px){.grid{grid-template-columns:1fr}}"""

def pkey(node_code, comm):
    """3.1.1 -> cu_3_1_1; 3.2.3 -> cu_3_2_3; 4.1 -> cu_4_1; 5.1 -> cu_5_1; 6.1 -> cu_6_1; 7.1 -> cu_7_1"""
    s = node_code.replace('.', '_')
    return comm + '_' + s

def build_overview(comm, cat_id):
    """生成一个总览页 HTML"""
    tc = tree_code(comm)
    color = COMM_COLOR[tc]
    cname = COMM_NAME[tc]
    code_u = comm.upper()
    num = CATNUM[cat_id]
    cat_cn = CAT_CN[cat_id]
    children = cat_children(cat_id)
    
    cards = []
    n_on = 0
    for code, name, q in children:
        key = pkey(code, comm)
        fname = key + '.html'
        if fname in EXISTING:
            n_on += 1
            cards.append(''.join([
                '    <a class="card" href="%s">\n' % fname,
                '      <div class="card-head">\n',
                '        <span class="card-num">%s</span>\n' % code,
                '        <span class="card-title">%s</span>\n' % name,
                '      </div>\n',
                '      <div class="card-charts">%s</div>\n' % q,
                '      <div class="card-foot">\n',
                '        <span class="badge on">✅ 已上线</span>\n',
                '        <span class="badge">%s</span>\n' % q,
                '      </div>\n',
                '    </a>\n']))
        else:
            cards.append(''.join([
                '    <div class="card off">\n',
                '      <div class="card-head">\n',
                '        <span class="card-num">%s</span>\n' % code,
                '        <span class="card-title">%s</span>\n' % name,
                '      </div>\n',
                '      <div class="card-charts">%s</div>\n' % q,
                '      <div class="card-foot"><span class="badge">待填充 · 未建页</span></div>\n',
                '    </div>\n']))

    n_cards = len(children)
    # CSS 主题色
    css = CSS % ((color,) * 7)
    
    # 副标题
    sub = '%s · %d 个子节点中 %d 个已上线' % (cat_cn, n_cards, n_on)
    
    # Note 文案（简化版，说明板块边界）
    if cat_id == 'price':
        note = '价格信号的六个维度——盘面结构(2.1) → 现货升贴水(2.2) → 海外价格(2.3) → 价差体系(2.4) → 估值利润(2.5) → 持仓席位(2.6)。'
    elif cat_id == 'supply':
        note = '供给链路的九个节点——海外矿财报(3.1.1) → 分国别总量(3.1.2) → 国内矿(3.1.3) → 矿进口(3.1.4) → TC加工费(3.1.5) → 精炼产量(3.2.1) → 开工率(3.2.2) → 再生供应(3.2.3) → 冶炼利润(3.2.4)。'
    elif cat_id == 'inventory':
        note = '库存的五层递进——交易所库存(4.1) → 仓单(4.2) → 社会库存(4.3) → 工厂库存(4.4) → 隐性/在途(4.5)。'
    elif cat_id == 'demand':
        note = '需求的三级观察——初级消费/开工率(5.1) → 终端细分消费(5.2) → 需求先行指标(5.3)。'
    elif cat_id == 'trade':
        note = '贸易的四条线——原料进口(6.1) → 精炼金属进出口(6.2) → 制品出口(6.3) → 海外对华发运(6.4)。'
    elif cat_id == 'cost':
        note = '成本利润的三个面——成本曲线与分位(7.1) → 日度利润测算(7.2) → 能源/原料成本(7.3)。'
    else:
        note = ''
    
    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s(%s) 板块%s %s · 总览</title>
<style>%s</style></head>
<body>
<div class="wrap">
  <div class="nav-back"><a href="index.html">← 回主站</a></div>
  <div class="h1">%s(%s) · 板块%s【%s】总览</div>
  <div class="sub">%s · %d 个子节点中 %d 个已上线 · 2026-08-31</div>
  <div class="note">%s</div>
  <div class="grid">
%s  </div>
  <div class="footer">有色金属产业指标树 · %s(%s) · 板块%s %s总览 · 2026-08-31<br><a href="index.html">← 返回 framework-tree 根目录</a></div>
</div>
</body></html>
""" % (cname, code_u, num, cat_cn,
       css,
       cname, code_u, num, cat_cn,
       sub, n_cards, n_on, note,
       '\n'.join(cards),
       cname, code_u, num, cat_cn)
    return html, n_on, n_cards

# ── 生成 31 个总览页 ──
TARGETS = [
    ('cu', 'cost'),  # cu_7
    ('zn', 'price'), ('zn', 'supply'), ('zn', 'inventory'), ('zn', 'demand'), ('zn', 'trade'), ('zn', 'cost'),
    ('ni', 'price'), ('ni', 'supply'), ('ni', 'inventory'), ('ni', 'demand'), ('ni', 'trade'), ('ni', 'cost'),
    ('sn', 'price'), ('sn', 'supply'), ('sn', 'inventory'), ('sn', 'demand'), ('sn', 'trade'), ('sn', 'cost'),
    ('si', 'price'), ('si', 'supply'), ('si', 'inventory'), ('si', 'demand'), ('si', 'trade'), ('si', 'cost'),
    ('li', 'price'), ('li', 'supply'), ('li', 'inventory'), ('li', 'demand'), ('li', 'trade'), ('li', 'cost'),
]

total_on = 0
total_cards = 0
for comm, cat_id in TARGETS:
    num = CATNUM[cat_id]
    fname = '%s_%s_overview.html' % (comm, num)
    html, n_on, n_cards = build_overview(comm, cat_id)
    open(fname, 'w', encoding='utf-8').write(html)
    total_on += n_on
    total_cards += n_cards
    print('OK %-24s %d 字节  %d/%d 节点上线' % (fname, len(html.encode('utf-8')), n_on, n_cards))

print('\n=== 汇总 ===')
print('生成 %d 个总览页' % len(TARGETS))
print('可点卡片 %d / 总节点 %d' % (total_on, total_cards))
