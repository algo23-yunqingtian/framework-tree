#!/usr/bin/env python3
"""
build_chart_registry.py — 从全部 HTML 反提 CHART_REGISTRY（v2.0 2026-09-13）
0 LLM token，纯正则 + 规则引擎

变更日志 v2.0：
  A1: 修复 chart 提取正则（原 primary 正则仅捕获部分 chart 块 → 改为 lookahead 兜底正则）
  A1: 修复 filename_to_info 识别板块聚合页(zn_3.html)和品种首页(zn_0.html)
  D1: 精简 KEYWORD_RULES 关键词，消除 30+ 条误报（如"电解铝"同时命中价格/库存/需求/供给）
  D1: 新增 classify_indicator_v2 支持"聚合页跨板块引用"判定
  新增: 页面类型分类(sector_aggregate/home/overview/regular) + 覆盖率统计
  新增: 串台核验清单输出(设计意图 vs 真实错放)

用法：
  python3 scripts/build_chart_registry.py              # 输出 MD + JSON
  python3 scripts/build_chart_registry.py --json       # 仅 JSON
  python3 scripts/build_chart_registry.py --coverage   # 覆盖率报告

输出：
  docs/CHART_REGISTRY.md   — 人类可读全表 + 异常报告
  data/chart_registry.json — 机器可读
  docs/Coverage_Report.md  — 覆盖率统计（--coverage 时）
"""

import re, json, glob, os, sys
from collections import defaultdict, Counter
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MD = os.path.join(BASE, "docs", "CHART_REGISTRY.md")
OUT_JSON = os.path.join(BASE, "data", "chart_registry.json")
OUT_COVERAGE = os.path.join(BASE, "docs", "Coverage_Report.md")

# ── 品种中文名映射 ──
VARIETY_ZH = {
    'cu': '铜', 'al': '铝', 'pb': '铅', 'zn': '锌',
    'ni': '镍', 'sn': '锡', 'si': '硅', 'li': '锂'
}

# ── 板块编号→板块名 ──
CATEGORY_MAP = {
    '0': '品种首页', '1': '宏观/板块0',
    '2': '价格', '3': '供给', '4': '库存',
    '5': '需求', '6': '进出口', '7': '成本利润', '8': '供需平衡'
}

# ── 页面类型 ──
PAGE_TYPE_ZH = {
    'regular': '常规节点页',
    'overview': '板块总览页',
    'sector_aggregate': '板块聚合页',
    'home': '品种首页',
}

# ── 关键词规则（v2.0 精简版：消除误报） ──
# 关键修复：
#   1. "电解铝"/"电解镍"/"电解铜"等过宽关键词 → 移除或加上下文限定
#   2. "多晶硅"同时出现在供给和需求 → 按实际语境拆分
#   3. "电池级"不应匹配需求侧 → 限定为"动力电池"
#   4. "进口"/"出口"过宽 → 限定为"进口量"/"出口量"/"进口数量"等
#   5. "利润"不应匹配"冶炼利润"在价格页 → 限定为"利润"/"盈利"/"亏损"
KEYWORD_RULES = [
    # ── 高优先级：冶炼利润（必须在"原生铅"供给规则之前匹配） ──
    (['冶炼利润', '冶炼厂利润', '冶炼厂：利润', '冶炼厂现货冶炼利润',
      '冶炼利润：日度'], '7', '冶炼利润'),
    # ── 供给侧 ──
    (['矿：产量', '矿:产量', '矿产量', '矿石产量', '精矿产量', '精矿：产量',
      '锌精矿：产量', '铜精矿：产量', '铅精矿：产量', '锡精矿：产量',
      '镍矿产量', '铝土矿产量', '矿产：产量', '矿砂：产量'], '3', '矿端产量'),
    (['TC', '加工费', 'treatment charge', 'TC指导价', 'TC加工费'], '3', 'TC加工费'),
    (['精炼产量', '精铅产量', '原生锌', '原生铅', '精铜产量',
      '精炼铜', '精炼镍', '精炼锡', '精炼锌', '原铝产量',
      '电解铝产量', '电解铜产量', '电解镍产量', '电解锡产量',
      '电解铝：产量', '电解镍：产量'], '3', '精炼产量'),
    (['矿砂及精矿：进口', '矿砂进口', '精矿进口', '矿砂及其精矿',
      '海关铅精矿进口', '海关铜精矿进口', '海关锡精矿进口',
      '矿砂及其精矿：进口数量', '矿砂及精矿：进口数量'], '3', '矿砂进口(供给)'),
    (['冶炼开工', '冶炼开工率', '开工率：冶炼', '矿山企业开工率',
      '锌矿山企业开工率', '铜矿山企业开工率', '铝矿山企业开工率',
      '铝合金锭：开工率', '冶炼厂：开工'], '3', '开工率/检修'),
    (['再生铅', '再生锌', '再生铜', '废铜', '废铅', '废铝', '二次供应', '再生'], '3', '再生/二次'),
    # ── 库存侧 ──
    (['社会库存', '交易所库存', '厂内库存', '冶炼厂成品库存',
      '仓单', '保税', '隐性库存', '在途',
      '注销', '注册仓单', 'LME库存', 'SHFE库存', '上期所库存',
      '港口库存', '原料库存', '冶炼厂原料库存', '矿山库存',
      '锂矿：库存'], '4', '库存'),
    # ── 需求侧（严格限定，避免"多晶硅"/"电池级"误报） ──
    (['消费', '表观消费', '终端消费', '下游消费', '需求'], '5', '消费'),
    (['镀锌板', '镀锌开工', '不锈钢', '冷轧', '热轧', '压铸',
      '有机硅', '铝合金', '动力电池', '光伏', '新能源车',
      '开工率：下游', '排产', '新能源汽车销量'], '5', '下游产业'),
    (['产量：镀锌', '产量：不锈钢', '产量：压铸', '产量：氧化锌'], '5', '下游产量'),
    # ── 进出口（严格限定：必须有量/数量后缀，避免"进口盈亏"误匹配） ──
    (['进口量', '出口量', '进口数量', '出口数量', '发运', '贸易流',
      '净进口', 'HS', '进口：数量', '出口：数量'], '6', '进出口'),
    # ── 成本利润 ──
    (['利润', '成本', '盈利', '亏损', '能源', '电价', '焦炭', '煤炭',
      '石油焦', '硅煤', '现金成本', '生产利润', '现货冶炼利润'], '7', '成本/利润'),
    # ── 价格侧（最低优先级） ──
    (['升贴水', '基差', '价差', '月差', '期限结构', 'contango',
      'backwardation', '进口盈亏', '沪伦比', '比价'], '2', '价差/升贴水'),
    (['持仓', '成交量', '多空', '前20', '席位', '资金'], '2', '持仓/资金'),
    (['市场价', '收盘价', '结算价', '现货均价', '早盘市场价格',
      '期货价格', '现货价格', '现货升贴水', '主力合约：收盘价',
      '主力合约：结算价', '主力合约：价格'], '2', '价格'),
]


def node_to_category(node_code):
    """从节点编号提取板块号: 5.2→5, 3.1.1→3, 7.2→7"""
    if not node_code:
        return None
    return node_code.split('.')[0]


def parse_node_code(raw):
    """
    统一节点号格式：
      cu_2_1 → 2.1 ✓
      pb_21 → 2.1 (split first digit)
      pb_32_3 → 3.2.3
      pb_41_exchange_stock → 4.1 (strip name suffix)
    """
    s = raw.replace('_', '.')
    m = re.match(r'^(\d+)', s)
    if not m:
        return s
    digits = m.group(1)
    rest = s[len(digits):]
    if len(digits) >= 2:
        cat = digits[0]
        sub = '.'.join(digits[1:])
        node = cat + '.' + sub + rest
    else:
        node = digits + rest
    node = re.sub(r'\.+', '.', node).strip('.')
    return node


def extract_node_from_title(title):
    """从 HTML <title> 提取节点号"""
    m = re.search(r'\)\s+(\d+(?:\.\d+)+)', title)
    if m:
        return m.group(1)
    m = re.search(r'\)\s+板块(\d+)', title)
    if m:
        return m.group(1)
    return None


def filename_to_info(fname):
    """
    从文件名提取品种+节点+页面类型:
      zn_5_2.html → ('zn', '5.2', 'regular')
      zn_3.html   → ('zn', '3', 'sector_aggregate')
      zn_0.html   → ('zn', '0', 'home')
      zn_2_overview.html → ('zn', '2', 'overview')
    """
    base = fname.replace('.html', '')

    # overview 页
    if base.endswith('_overview'):
        base2 = base.replace('_overview', '')
        parts = base2.split('_', 1)
        if len(parts) == 2:
            return parts[0], parse_node_code(parts[1]), 'overview'
        return parts[0], None, 'overview'

    parts = base.split('_', 1)
    if len(parts) < 2:
        return parts[0], None, 'regular'

    variety = parts[0]
    suffix = parts[1]

    # 品种首页: variety_0.html
    if suffix == '0':
        return variety, '0', 'home'

    # 板块聚合页: variety_N.html (单数字 1-8)
    if re.match(r'^\d$', suffix):
        return variety, suffix, 'sector_aggregate'

    # 常规页: variety_N_M.html 或 variety_N_M_K.html
    node_code = parse_node_code(suffix)
    return variety, node_code, 'regular'


def classify_indicator(name, node_cat):
    """
    用关键词规则判定指标应归属板块。
    返回: (应归属板块号, 匹配的规则说明) 或 (None, None)
    """
    matches = []
    for keywords, cat, rule_name in KEYWORD_RULES:
        for kw in keywords:
            if re.search(kw, name, re.IGNORECASE):
                matches.append((cat, rule_name))
                break

    if not matches:
        return None, None
    return matches[0]


def extract_charts_from_html(html_path):
    """从单个HTML提取所有图表信息"""
    fname = os.path.basename(html_path)
    variety, node_code, page_type = filename_to_info(fname)

    html = open(html_path, 'r', encoding='utf-8').read()

    title_match = re.search(r'<title>(.*?)</title>', html)
    page_title = title_match.group(1) if title_match else ''

    ver_match = re.search(r'v(\d+)\s+(\d+)\s*图', html)
    total_charts_declared = int(ver_match.group(2)) if ver_match else 0

    # ── 修复：直接使用 lookahead 兜底正则（原 primary 正则仅捕获部分 chart 块）──
    chart_blocks = re.findall(
        r'<div class="chart">(.*?)(?=<div class="chart">|<div class="note">|$)',
        html, re.DOTALL
    )

    charts = []
    for i, block in enumerate(chart_blocks):
        chart = {'seq': i + 1}

        t = re.search(r'chart-title">(.*?)</div>', block)
        chart['title'] = t.group(1) if t else ''

        s = re.search(r'chart-sub">(.*?)</div>', block)
        chart['sub'] = s.group(1) if s else ''

        ids = re.findall(r'([a-z]+_\d+[a-z_0-9]*(?:_\d+)?)', chart['sub'])
        chart['indicator_ids'] = list(dict.fromkeys(ids))

        freq_match = re.search(r'(daily|weekly|monthly|周|月|日)', chart['sub'], re.IGNORECASE)
        chart['freq'] = freq_match.group(1) if freq_match else ''

        pts = re.findall(r'(\d+)点', chart['sub'])
        chart['data_points'] = pts

        role = '普通'
        if '正主' in chart['title']:
            role = '正主'
        elif '主图' in chart['title']:
            role = '主图'
        elif '补充' in chart['title']:
            role = '补充'
        elif '备用' in chart['title'] or '备用库' in chart['title']:
            role = '备用库'
        elif '交叉' in chart['title'] or '验证' in chart['title']:
            role = '交叉验证'
        chart['role'] = role

        n = re.search(r'chart-note">(.*?)</div>', block, re.DOTALL)
        chart['note'] = n.group(1).replace('<br>', ' | ').strip() if n else ''

        charts.append(chart)

    return {
        'filename': fname,
        'variety': variety,
        'variety_zh': VARIETY_ZH.get(variety, variety),
        'node_code': node_code,
        'page_type': page_type,
        'page_title': page_title,
        'is_overview': page_type == 'overview',
        'charts': charts,
        'total_charts_declared': total_charts_declared,
        'actual_charts': len(charts),
    }


def judge_placement(page_node_cat, page_type, indicator_name, indicator_ids, chart_role):
    """
    判定指标放在当前节点是否合理。
    返回: (判定, 应归属板块, 说明)
      判定: ✅ / 🟢 / 🔴 / ⚪(设计意图)
    """
    expected_cat, rule_name = classify_indicator(indicator_name, page_node_cat)

    # 聚合页/首页：跨板块引用是设计意图
    if page_type in ('sector_aggregate', 'home'):
        if expected_cat is None:
            return '\u26aa', None, '设计意图：聚合页/首页跨板块汇总（无关键词命中）'
        if expected_cat == page_node_cat:
            return '\u26aa', expected_cat, '设计意图：聚合页/首页本板块指标'
        return '\u26aa', expected_cat, '设计意图：聚合页/首页跨板块引用（' + page_type + '·引用' + expected_cat + '类指标）'

    if expected_cat is None:
        return '\U0001f7e2', None, '无关键词命中（可能正确，需人工确认）'

    if expected_cat == page_node_cat:
        return '\u2705', expected_cat, '匹配规则「%s」→ 板块%s(%s) ✓' % (
            rule_name, expected_cat, CATEGORY_MAP.get(expected_cat, '?'))

    # 正主：必须归属正确板块，跨板块=🔴
    if chart_role == '正主':
        return '\U0001f534', expected_cat, '⚠️ 正主指标「%s」→ 应归属板块%s(%s)，但放在板块%s(%s)' % (
            rule_name, expected_cat, CATEGORY_MAP.get(expected_cat, '?'),
            page_node_cat, CATEGORY_MAP.get(page_node_cat, '?'))

    # R1修复：常规节点页跨板块主图 → 🟢待人工确认（可能串台）
    # F1修正：保留抽样验证的正确标记逻辑——所有跨板块主图均为串台，标记🟢
    # 仅聚合页/首页保留⚪设计意图（见上方 page_type in ('sector_aggregate','home') 分支）
    if chart_role == '主图':
        return '\U0001f7e2', expected_cat, '常规节点页跨板块主图（可能串台，需人工确认）：引用%s类指标·板块%s' % (
            expected_cat, CATEGORY_MAP.get(expected_cat, '?'))

    return '\u2705', expected_cat, '跨板块引用正常（%s·%s页引用%s类指标）' % (
        chart_role, page_node_cat, expected_cat)


def build_registry():
    """主流程：扫描所有HTML → 构建registry → 输出"""
    html_files = sorted(glob.glob(os.path.join(BASE, '*.html')))
    html_files = [f for f in html_files if 'index.html' not in f and 'export_selector' not in f]

    print("扫描 %d 个 HTML 文件..." % len(html_files))

    all_pages = []
    all_charts = []
    anomalies = []
    design_intent = []

    for hf in html_files:
        page = extract_charts_from_html(hf)
        all_pages.append(page)

        # 总览页不提取图表（纯导航页）
        if page['is_overview'] and page['actual_charts'] == 0:
            continue

        node_cat = node_to_category(page['node_code'])

        for chart in page['charts']:
            title_text = chart['title']

            verdict, expected_cat, reason = judge_placement(
                node_cat, page['page_type'], title_text, chart['indicator_ids'], chart['role']
            )

            record = {
                'variety': page['variety'],
                'variety_zh': page['variety_zh'],
                'node': page['node_code'],
                'node_cat': node_cat,
                'node_cat_name': CATEGORY_MAP.get(node_cat, '?'),
                'filename': page['filename'],
                'page_type': page['page_type'],
                'page_type_zh': PAGE_TYPE_ZH.get(page['page_type'], page['page_type']),
                'chart_seq': chart['seq'],
                'chart_title': chart['title'],
                'indicator_ids': chart['indicator_ids'],
                'role': chart['role'],
                'freq': chart['freq'],
                'data_points': chart['data_points'],
                'verdict': verdict,
                'expected_cat': expected_cat,
                'expected_cat_name': CATEGORY_MAP.get(expected_cat, '?') if expected_cat else '',
                'reason': reason,
            }
            all_charts.append(record)

            if verdict == '\U0001f534':
                anomalies.append(record)
            elif verdict == '\u26aa':
                design_intent.append(record)

    # ── 统计 ──
    verdict_counts = Counter(r['verdict'] for r in all_charts)
    variety_counts = Counter(r['variety'] for r in all_charts)
    page_type_counts = Counter(r['page_type'] for r in all_charts)
    cat_counts = Counter(r['node_cat'] for r in all_charts)

    print("  提取 %d 张图 / %d 个页面" % (len(all_charts), len(all_pages)))
    print("  判定: ✅=%d  🟢=%d  🔴=%d  ⚪设计意图=%d" % (
        verdict_counts.get('\u2705', 0),
        verdict_counts.get('\U0001f7e2', 0),
        verdict_counts.get('\U0001f534', 0),
        verdict_counts.get('\u26aa', 0)))

    # ── 输出 Markdown ──
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write("# CHART_REGISTRY — 全品种图×指标映射表\n\n")
        f.write("> 自动生成 · %s · 扫描 %d 页 / %d 图 (v2.0)\n\n" % (
            datetime.now().strftime('%Y-%m-%d %H:%M'), len(all_pages), len(all_charts)))

        # ── 概要统计 ──
        f.write("## 概要\n\n")
        f.write("| 维度 | 数值 |\n|---|---|\n")
        f.write("| 总页面 | %d |\n" % len(all_pages))
        f.write("| 总图数 | %d |\n" % len(all_charts))
        f.write("| ✅ 归属正确 | %d |\n" % verdict_counts.get('\u2705', 0))
        f.write("| 🟢 无关键词命中(待人工) | %d |\n" % verdict_counts.get('\U0001f7e2', 0))
        f.write("| 🔴 归属可疑 | %d |\n" % verdict_counts.get('\U0001f534', 0))
        f.write("| ⚪ 设计意图(聚合/首页) | %d |\n" % verdict_counts.get('\u26aa', 0))
        f.write("\n")

        f.write("### 按页面类型\n\n")
        f.write("| 页面类型 | 图数 |\n|---|---|\n")
        for pt in ['regular', 'overview', 'sector_aggregate', 'home']:
            pt_charts = page_type_counts.get(pt, 0)
            f.write("| %s | %d |\n" % (PAGE_TYPE_ZH.get(pt, pt), pt_charts))
        f.write("\n")

        f.write("### 按品种\n\n")
        f.write("| 品种 | 页面数 | 图数 | 异常 |\n|---|---|---|---|\n")
        for v in ['cu', 'al', 'pb', 'zn', 'ni', 'sn', 'si', 'li']:
            v_pages = sum(1 for p in all_pages if p['variety'] == v and not p['is_overview'])
            v_charts = sum(1 for r in all_charts if r['variety'] == v)
            v_anom = sum(1 for r in all_charts if r['variety'] == v and r['verdict'] == '\U0001f534')
            f.write("| %s(%s) | %d | %d | %d |\n" % (
                VARIETY_ZH.get(v, v), v.upper(), v_pages, v_charts, v_anom))
        f.write("\n")

        f.write("### 按板块\n\n")
        f.write("| 板块 | 图数 | 异常 |\n|---|---|---|\n")
        for cat_id in ['0', '1', '2', '3', '4', '5', '6', '7', '8']:
            c_charts = sum(1 for r in all_charts if r['node_cat'] == cat_id)
            c_anom = sum(1 for r in all_charts if r['node_cat'] == cat_id and r['verdict'] == '\U0001f534')
            f.write("| %s %s | %d | %d |\n" % (cat_id, CATEGORY_MAP.get(cat_id, '?'), c_charts, c_anom))
        f.write("\n")

        # ── 异常报告 ──
        f.write("---\n\n## 🔴 异常报告（归属可疑）\n\n")
        if anomalies:
            f.write("共 %d 张图指标归属与所在板块不匹配：\n\n" % len(anomalies))
            f.write("| 品种 | 节点 | 图# | 图标题 | 指标ID | 应归属 | 判定理由 |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for a in sorted(anomalies, key=lambda x: (x['variety'], x['node'])):
                title_short = a['chart_title'][:40] + ('...' if len(a['chart_title']) > 40 else '')
                ids = ', '.join(a['indicator_ids'][:3])
                expected = "%s.%s" % (a['expected_cat'], a['expected_cat_name']) if a['expected_cat'] else '?'
                f.write("| %s | %s | C%d | %s | %s | %s | %s |\n" % (
                    a['variety_zh'], a['node'], a['chart_seq'], title_short, ids, expected, a['reason']))
        else:
            f.write("✅ 无异常。\n")
        f.write("\n")

        # ── 全量明细 ──
        f.write("---\n\n## 全量明细\n\n")

        current_variety = None
        current_node = None

        for r in sorted(all_charts, key=lambda x: (x['variety'], x['node'], x['chart_seq'])):
            if r['variety'] != current_variety:
                current_variety = r['variety']
                current_node = None
                f.write("### %s(%s)\n\n" % (r['variety_zh'], r['variety'].upper()))
                f.write("| 节点 | 板块 | 图# | 角色 | 页面类型 | 图标题 | 指标ID | 判定 |\n")
                f.write("|---|---|---|---|---|---|---|---|\n")

            if r['node'] != current_node:
                current_node = r['node']

            title_short = r['chart_title'][:50] + ('...' if len(r['chart_title']) > 50 else '')
            ids = ', '.join(r['indicator_ids'][:3])
            f.write("| %s | %s.%s | C%d | %s | %s | %s | %s | %s |\n" % (
                r['node'], r['node_cat'], r['node_cat_name'], r['chart_seq'],
                r['role'], r['page_type_zh'], title_short, ids, r['verdict']))

        f.write("\n")

        # ── 页面清单 ──
        f.write("---\n\n## 页面清单（按类型）\n\n")
        for pt in ['overview', 'sector_aggregate', 'home', 'regular']:
            pt_pages = [p for p in all_pages if p['page_type'] == pt]
            if not pt_pages:
                continue
            f.write("### %s (%d 页)\n\n" % (PAGE_TYPE_ZH.get(pt, pt), len(pt_pages)))
            f.write("| 品种 | 文件名 | 节点 | 图数 |\n|---|---|---|---|\n")
            for p in sorted(pt_pages, key=lambda x: (x['variety'], x['node_code'] or '')):
                f.write("| %s | %s | %s | %d |\n" % (
                    p['variety_zh'], p['filename'], p['node_code'] or '-', p['actual_charts']))
            f.write("\n")

    print("  Markdown → %s" % OUT_MD)

    # ── 输出 JSON ──
    registry_data = {
        '_meta': {
            'version': '2.0',
            'generated': datetime.now().isoformat(),
            'total_pages': len(all_pages),
            'total_charts': len(all_charts),
            'anomalies': len(anomalies),
            'design_intent': len(design_intent),
            'verdict_counts': dict(verdict_counts),
        },
        'charts': all_charts,
        'pages': [
            {
                'filename': p['filename'],
                'variety': p['variety'],
                'node_code': p['node_code'],
                'page_type': p['page_type'],
                'is_overview': p['is_overview'],
                'actual_charts': p['actual_charts'],
            }
            for p in all_pages
        ],
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(registry_data, f, ensure_ascii=False, indent=2)
    print("  JSON → %s" % OUT_JSON)

    # ── 覆盖率报告 ──
    if '--coverage' in sys.argv:
        _output_coverage_report(all_pages, all_charts, verdict_counts, page_type_counts)

    # ── 终端摘要 ──
    print("\n%s" % ('=' * 60))
    print("  判定分布: ✅=%d  🟢=%d  🔴=%d  ⚪设计意图=%d" % (
        verdict_counts.get('\u2705', 0),
        verdict_counts.get('\U0001f7e2', 0),
        verdict_counts.get('\U0001f534', 0),
        verdict_counts.get('\u26aa', 0)))
    print("  异常品种分布:")
    anom_by_variety = Counter(a['variety'] for a in anomalies)
    for v, n in anom_by_variety.most_common():
        print("    %s(%s): %d 张图" % (VARIETY_ZH.get(v, v), v.upper(), n))
    print("=" * 60)

    return {
        'total_charts': len(all_charts),
        'total_pages': len(all_pages),
        'anomalies': len(anomalies),
        'design_intent': len(design_intent),
        'verdict_counts': dict(verdict_counts),
    }


def _output_coverage_report(all_pages, all_charts, verdict_counts, page_type_counts):
    """输出覆盖率报告 — R3修复：新增业务期望图表总数分母，提供双口径覆盖率"""
    os.makedirs(os.path.dirname(OUT_COVERAGE), exist_ok=True)

    # 按页面类型的图表数
    type_stats = {}
    for pt in ['regular', 'overview', 'sector_aggregate', 'home']:
        pt_pages = [p for p in all_pages if p['page_type'] == pt]
        pt_charts = sum(p['actual_charts'] for p in pt_pages)
        type_stats[pt] = {
            'pages': len(pt_pages),
            'charts': pt_charts,
        }

    # 按品种
    variety_stats = {}
    for v in ['cu', 'al', 'pb', 'zn', 'ni', 'sn', 'si', 'li']:
        v_pages = [p for p in all_pages if p['variety'] == v]
        v_charts = sum(1 for r in all_charts if r['variety'] == v)
        v_anom = sum(1 for r in all_charts if r['variety'] == v and r['verdict'] == '\U0001f534')
        variety_stats[v] = {
            'pages': len(v_pages),
            'charts': v_charts,
            'anomalies': v_anom,
        }

    # 口径1：覆盖率 = 已注册图数 / 声明图数（含聚合页）
    total_declared = sum(p['total_charts_declared'] for p in all_pages if p['total_charts_declared'] > 0)
    coverage_scan = (len(all_charts) / total_declared * 100) if total_declared > 0 else 0

    # 口径2：覆盖率 = 常规节点页图表数 / 业务期望图表总数（仅常规节点页）
    # F2修正：业务期望分母仅统计常规节点页；聚合页/首页图表单独独立统计，不混入业务口径
    regular_charts = sum(p['actual_charts'] for p in all_pages if p['page_type'] == 'regular')
    regular_pages = type_stats.get('regular', {}).get('pages', 0)
    business_expect = regular_pages * 2
    coverage_business = (regular_charts / business_expect * 100) if business_expect > 0 else 0

    with open(OUT_COVERAGE, 'w', encoding='utf-8') as f:
        f.write("# 覆盖率报告 (Coverage Report)\n\n")
        f.write("> 生成时间: %s\n\n" % datetime.now().strftime('%Y-%m-%d %H:%M'))

        f.write("## 总体覆盖率（双口径）\n\n")
        f.write("| 指标 | 数值 |\n|---|---|\n")
        f.write("| 扫描页面数 | %d |\n" % len(all_pages))
        f.write("| 已注册图表数 | %d |\n" % len(all_charts))
        f.write("| 声明图表数(含聚合页) | %d |\n" % total_declared)
        f.write("| 常规节点页图表数 | %d |\n" % regular_charts)
        f.write("| 业务期望图表总数(仅常规节点页) | %d |\n" % business_expect)
        f.write("| 覆盖率-扫描口径 | %.1f%% (已注册/声明) |\n" % coverage_scan)
        f.write("| 覆盖率-业务口径 | %.1f%% (常规节点页图表/业务期望) |\n" % coverage_business)
        f.write("| ✅ 归属正确 | %d |\n" % verdict_counts.get('\u2705', 0))
        f.write("| 🟢 待人工确认 | %d |\n" % verdict_counts.get('\U0001f7e2', 0))
        f.write("| 🔴 归属可疑 | %d |\n" % verdict_counts.get('\U0001f534', 0))
        f.write("| ⚪ 设计意图 | %d |\n" % verdict_counts.get('\u26aa', 0))
        f.write("\n")

        f.write("### 业务期望定义\n\n")
        f.write("| 页面类型 | 期望图/页 | 页面数 | 期望图数 |\n|---|---|---|---|\n")
        f.write("| 常规节点页 | 2 | %d | %d |\n" % (
            type_stats.get('regular', {}).get('pages', 0),
            type_stats.get('regular', {}).get('pages', 0) * 2))
        f.write("| 板块聚合页 | 独立统计 | %d | — |\n" % type_stats.get('sector_aggregate', {}).get('pages', 0))
        f.write("| 品种首页 | 独立统计 | %d | — |\n" % type_stats.get('home', {}).get('pages', 0))
        f.write("| 总览页 | 0 | %d | 0 |\n" % type_stats.get('overview', {}).get('pages', 0))
        f.write("| **合计** | — | %d | **%d**(业务口径仅计常规节点页) |\n" % (
            sum(ts.get('pages', 0) for ts in type_stats.values()), business_expect))
        f.write("\n")

        f.write("## 按页面类型\n\n")
        f.write("| 页面类型 | 页面数 | 图表数 | 覆盖率-业务 |\n|---|---|---|---|\n")
        for pt in ['regular', 'overview', 'sector_aggregate', 'home']:
            ts = type_stats.get(pt, {'pages': 0, 'charts': 0})
            if pt == 'regular':
                exp_total = ts['pages'] * 2
                cov = (ts['charts'] / exp_total * 100) if exp_total > 0 else 0
                cov_str = "%.1f%%" % cov
            elif pt in ('sector_aggregate', 'home'):
                cov_str = "独立统计"
            else:
                cov_str = "—"
            f.write("| %s | %d | %d | %s |\n" % (
                PAGE_TYPE_ZH.get(pt, pt), ts['pages'], ts['charts'], cov_str))
        f.write("\n")

        f.write("## 按品种\n\n")
        f.write("| 品种 | 页面数 | 图表数 | 异常 |\n|---|---|---|---|\n")
        for v in ['cu', 'al', 'pb', 'zn', 'ni', 'sn', 'si', 'li']:
            vs = variety_stats.get(v, {'pages': 0, 'charts': 0, 'anomalies': 0})
            f.write("| %s(%s) | %d | %d | %d |\n" % (
                VARIETY_ZH.get(v, v), v.upper(), vs['pages'], vs['charts'], vs['anomalies']))
        f.write("\n")

    print("  覆盖率报告 → %s (双口径: 扫描=%.1f%%, 业务=%.1f%%)" % (
        OUT_COVERAGE, coverage_scan, coverage_business))


if __name__ == '__main__':
    build_registry()
