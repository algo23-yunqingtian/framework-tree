#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_overview_cu_al.py — 主脑补建 7 个铜铝板块总览页，解 22 页死链。

背景：铜铝 agent 在 task/cu_price 建成 36 个铜铝页，但 22 个子页 nav_back 指向
不存在的板块总览页（cu_3_overview ×9 / cu_6_overview ×2 / al_3_overview ×1 /
al_4_overview ×5 / al_5_overview ×3 / al_6_overview ×1 / al_7_overview ×2）。
本脚本按已有 al_2_overview.html / cu_2_overview.html 的模板风格补齐这 7 个，
使 22 页 nav_back 全部可达。

红线：
- 数据内嵌零服务器依赖，零 fetch
- 主题色取 tree_config.json 品种色（铜 #b06a32 / 铝 #7a8a9c）
- 已上线节点卡片可点；未上线节点标注「待填充」为静态文本，不做假链接
- key 带品种前缀防撞名（见 AGENTS.md 红线）
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

# 子节点 code -> (label, nav_back 指向的 overview)
def cat_children(cat_id):
    return [(k['code'], k['name'], k.get('q', '')) for k in CATS[cat_id]['children']]

# 已存在子页
EXISTING = set(os.listdir('.'))

# ── 每页元数据：node_code -> (标题, 图表摘要, 指标, 徽标) ────────────────
# 从各页 HTML 的 title / card 摘取，保真反映实际内容
PAGES = {
 'cu_3_1_1': ('铜矿产量·澳', '铜矿产量时序⇄季节(正主) / 产出集中度', 'cu_311_output · cu_311_output_conc · cu_311_output_ratio_struct', '2图 · 主图45点'),
 'cu_3_1_2': ('铜矿产量·波兰', '海外矿分国别产量(正主)', 'cu_312_output · cu_312_output_conc', '1图 · 主图45点'),
 'cu_3_1_3': ('铜矿产量·中国', '国内铜矿产量时序⇄季节(正主) / 产量结构', 'cu_313_output · al_313_util(辅助) · cu_311_output_conc(辅助)', '2图 · 主图67点'),
 'cu_3_1_4': ('铜精矿进口', '海关铜精矿进口量(正主)', 'cu_314_import · cu_314_import_conc_arrival(辅助·空数据)', '1图 · 主图134点'),
 'cu_3_1_5': ('TC/RC 加工费', '国产TC vs 进口TC(正主) / TC分位自算 / 矿端紧松', 'cu_315_import_conc · al_315_tc_tc · al_315_tc_tc_percentile · cu_25_tc_conc(辅助)', '3图 · 主图134点'),
 'cu_3_2_1': ('电解铜产能产量', '电解铜产量时序⇄季节(正主) / 产能 / 进口', 'cu_321_output · cu_321_capacity · cu_321_import · al_313_util(辅助)', '3图 · 主图139点'),
 'cu_3_2_2': ('电解铜产量·开工率', '精炼产量时序⇄季节(正主) / 产能利用率辅助', 'cu_322_output · cu_321_capacity(辅助) · al_313_util(辅助)', '2图 · 主图138点'),
 'cu_3_2_4': ('冶炼利润·供应弹性', '冶炼利润(正主) / 成本曲线对照', 'cu_324_profit · al_324_cost · cu_25_tc_conc(辅助)', '2图 · 主图280点'),
 'cu_6_1': ('原料进口', '铜精矿进口时序⇄季节(正主) / 再生铜原料辅助', 'cu_321_import · al_323_import_scrap(辅助)', '2图 · 主图139点'),
 'cu_6_2': ('进出口', '精炼铜进出口(正主) / 净进口结构', 'al_62_import · cu_321_import(辅助)', '2图 · 主图139点'),
 'al_3_2_3': ('再生/二次供应', '进口废铝⇄库存(正主) / 二次供应结构', 'al_323_import_scrap · al_323_inv_scrap · cu_323_import_recycle(辅助)', '2图 · 主图59点'),
 'al_4_1': ('交易所库存', '上期所铝库存时序⇄季节(正主) / LME仓单 / 仓单占比', 'al_41_inv · al_41_warrant · al_41_lme_warrant · al_41_lme_warrant_ratio', '3图 · 主图56点'),
 'al_4_2': ('仓单', '上期所仓单⇄LME仓单(正主) / 仓单占比', 'al_41_warrant · al_41_warrant_ratio · al_41_lme_warrant · al_41_lme_warrant_ratio', '3图 · 主图140点'),
 'al_4_3': ('社会库存', '铝厂库存/社会库存(正主)', 'al_43_inv_plant', '1图 · 主图60点'),
 'al_4_4': ('工厂库存', '铝厂库存(正主)', 'al_43_inv_plant', '1图 · 主图60点'),
 'al_4_5': ('隐性·在途', '隐性库存分位自算(正主)', 'al_45_inv_implicit_percentile', '1图 · 主图56点'),
 'al_5_1': ('初级消费', '电解铝开工率时序⇄季节(正主·月) / 周度开工率辅助', 'al_51_util · al_51_util_week · al_51_cons', '2图 · 正主139点'),
 'al_5_2': ('终端消费', '终端细分消费时序⇄季节(正主) / 产量对照', 'al_52_cons · al_52_output · al_51_cons(辅助)', '2图 · 主图67点'),
 'al_5_3': ('消费价格', '铝价时序⇄季节(正主)', 'al_53_close_front', '1图 · 主图140点'),
 'al_6_3': ('制品出口', '铝材出口时序⇄季节(正主)', 'al_63_export', '1图 · 主图139点'),
 'al_7_1': ('电解铝成本', '电解铝成本曲线时序⇄季节(正主) / TC加工费辅助', 'al_71_cost · al_71_tc · cu_25_tc_conc(辅助)', '2图 · 主图104点'),
 'al_7_2': ('铝价与成本', '铝价时序⇄季节(正主) / 铝-氧化铝价差', 'al_53_close_front · al_71_tc', '2图 · 主图140点'),
}

# ── 板块配置：overview 文件名 -> (品种, cat_id, 板块中文名, 副标题要点, note 文案) ──
BOARDS = {
 'cu_3_overview.html': ('cu', 'supply', '供给', '铜供给链路：矿端5节点(3.1.x) + 冶炼3节点(3.2.1/3.2.2/3.2.4)已上线，3.2.3再生供应为铝页复用',
   '铜供给的六个切面——海外矿财报(3.1.1) → 分国别总量(3.1.2) → 国内矿(3.1.3) → 精矿进口(3.1.4) → TC加工费(3.1.5) → 精炼产量/开工率/利润(3.2.1·3.2.2·3.2.4)。'
   '<br><b>数据质量声明：</b>矿端 3.1.1/3.1.2 主图仅约 45 点（季度·分国别口径），季节性视图年跨度较短；'
   '<code>cu_314_import_conc_arrival</code> 实测空数据，仅作 3.1.4 辅助位不主图；'
   '<code>al_313_util</code> 系铝电解开工率，在铜 3.1.3/3.2.1/3.2.2 中作辅助对照，正主均为铜自身指标。'),
 'cu_6_overview.html': ('cu', 'trade', '进出口', '铜进出口：6.1 原料进口 + 6.2 精炼金属进出口已上线',
   '铜贸易的两条线——原料进口(6.1) → 精炼金属进出口(6.2)。<br>'
   '<b>边界说明：</b>铜 6.3 制品出口 / 6.4 海外对华发运未建页，知几无对应连续序列，待外部源。'
   '<code>al_62_import</code> 系铝进出口序列，在铜 6.2 中作辅助参照，正主为铜进口口径。'),
 'al_3_overview.html': ('al', 'supply', '供给', '铝供给：3.2.3 再生/二次供应已上线（铝原生矿端无独立序列，走再生主链）',
   '铝与铜的关键差异——铝几乎无原生矿独立供给序列（氧化铝一体化定价，知几无分国别铝矿产量），'
   '供给主线落在<b>再生/二次供应</b>。<br>'
   '<b>数据质量声明：</b><code>al_323_import_scrap</code> 主图 59 点，年跨度约 5 年；'
   '<code>cu_323_import_recycle</code> 系铜再生进口，仅作辅助对照。'),
 'al_4_overview.html': ('al', 'inventory', '库存', '铝库存 5 节点全上线：交易所→仓单→社会→工厂→隐性在途',
   '铝库存的五层递进——交易所库存(4.1) → 仓单(4.2) → 社会库存(4.3) → 工厂库存(4.4) → 隐性/在途(4.5)。<br>'
   '<b>口径注意：</b>4.3 社会库存与 4.4 工厂库存正主同为 <code>al_43_inv_plant</code>（知几无独立社会库存序列，铝社库以铝厂库存代理，此为已记录的口径妥协，两页图注均标注）；'
   '4.5 隐性库存为分位自算（<code>_derived</code>），非直接序列。'
   '4.1 主图 56 点为月度口径，季节性视图年跨度短于日度页。'),
 'al_5_overview.html': ('al', 'demand', '需求', '铝需求 3 节点全上线：初级消费→终端→消费价格',
   '铝需求的三级观察——初级消费/开工率(5.1) → 终端细分消费(5.2) → 消费价格(5.3)。<br>'
   '<b>正主归属：</b>5.1 正主为 <code>al_51_util</code>（SMM 电解铝开工率，月 139 点）贴合 tree_config q=「开工率·同步」；'
   '<code>al_51_util_week</code> 仅 86 点/1 完整年，作高频辅助不作季节主图。'
   '5.3 正主 <code>al_53_close_front</code> 与 2.x 的 <code>al_00_close_front</code> 为同一行情序列的不同挂点（价格信号 vs 需求端消费价格视角）。'),
 'al_6_overview.html': ('al', 'trade', '进出口', '铝进出口：6.3 制品出口已上线',
   '铝制品出口(6.3)为当前唯一上线节点。<br>'
   '<b>未建页：</b>6.1 原料进口 / 6.2 精炼铝进出口 / 6.4 海外对华发运未建，知几铝进出口序列覆盖不全，待外部源（海关总署口径）。'),
 'al_7_overview.html': ('al', 'cost', '成本·利润', '铝成本利润：7.1 成本曲线 + 7.2 铝价与成本已上线',
   '铝成本的两面——成本曲线与分位(7.1) → 铝价与成本对照(7.2)。<br>'
   '<b>未建页：</b>7.3 能源/原料成本未建，电铝对电力成本敏感但知几铝电价序列覆盖不足，待外部源。'
   '<code>cu_25_tc_conc</code> 系铜 TC 集中度，在 7.1 作辅助参照。'),
}

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

def build(overview, comm, cat_id, cat_cn, sub, note):
    color = COMM_COLOR[comm]
    cname = COMM_NAME[comm]
    code_u = comm.upper()
    num = catnum(cat_id)
    children = cat_children(cat_id)
    # 本页节点 key 映射：node_code -> PAGES key
    def pkey(node_code, comm, level):
        """3.1.1 -> cu_3_1_1; 3.2.3 -> cu_3_2_3; 4.1 -> cu_4_1; 5.1 -> cu_5_1; 6.1 -> cu_6_1; 7.1 -> cu_7_1"""
        s = node_code.replace('.', '_')
        return comm + '_' + s

    cards = []
    n_on = 0
    for code, name, q in children:
        key = pkey(code, comm, code.count('.'))
        fname = key + '.html'
        if fname in EXISTING and key in PAGES:
            n_on += 1
            title, charts, metrics, badge = PAGES[key]
            cards.append(''.join([
                '    <a class="card" href="%s">\n' % fname,
                '      <div class="card-head">\n',
                '        <span class="card-num">%s</span>\n' % code,
                '        <span class="card-title">%s</span>\n' % title,
                '      </div>\n',
                '      <div class="card-charts">%s</div>\n' % charts,
                '      <div class="card-metrics">%s</div>\n' % metrics,
                '      <div class="card-foot">\n',
                '        <span class="badge on">%s</span>\n' % badge,
                '        <span class="badge">%s</span>\n' % q,
                '      </div>\n',
                '    </a>\n']))
        elif fname in EXISTING:
            # 已建页但本脚本未登记元数据 → 仍给真链接，标注待补登记
            n_on += 1
            cards.append(''.join([
                '    <a class="card" href="%s">\n' % fname,
                '      <div class="card-head">\n',
                '        <span class="card-num">%s</span>\n' % code,
                '        <span class="card-title">已上线（元数据待补）</span>\n',
                '      </div>\n',
                '      <div class="card-metrics">file exists</div>\n',
                '      <div class="card-foot"><span class="badge">%s</span></div>\n' % q,
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
    # 两阶段格式化：先套 CSS 主题色（含 @media/%d，不能与下方 HTML 格式串混用）
    css = CSS % ((color,) * 7)
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

def catnum(cat_id):
    """price->2, supply->3, inventory->4, demand->5, trade->6, cost->7"""
    return {'price': '2', 'supply': '3', 'inventory': '4', 'demand': '5', 'trade': '6', 'cost': '7'}[cat_id]

for fname, (comm, cat_id, cat_cn, sub, note) in BOARDS.items():
    num = catnum(cat_id)
    html, n_on, n_cards = build(fname, comm, cat_id, cat_cn, sub, note)
    html = html.replace('板块%s ' % num, '板块%s ' % num)
    open(fname, 'w', encoding='utf-8').write(html)
    print('OK %-24s %d 字节  %d/%d 节点上线' % (fname, len(html.encode('utf-8')), n_on, n_cards))
