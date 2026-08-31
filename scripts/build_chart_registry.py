#!/usr/bin/env python3
"""
build_chart_registry.py — 从 260 个 HTML 反提 CHART_REGISTRY
0 LLM token，纯正则 + 规则引擎

用法：
  python3 scripts/build_chart_registry.py              # 输出到 docs/CHART_REGISTRY.md
  python3 scripts/build_chart_registry.py --json       # 同时输出 JSON

输出：
  docs/CHART_REGISTRY.md   — 人类可读全表 + 异常报告
  data/chart_registry.json — 机器可读（后续脚本可消费）
"""

import re, json, glob, os, sys
from collections import defaultdict, Counter
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MD = os.path.join(BASE, "docs", "CHART_REGISTRY.md")
OUT_JSON = os.path.join(BASE, "data", "chart_registry.json")

# ── 品种中文名映射 ──
VARIETY_ZH = {
    'cu': '铜', 'al': '铝', 'pb': '铅', 'zn': '锌',
    'ni': '镍', 'sn': '锡', 'si': '硅', 'li': '锂'
}

# ── 板块编号→板块名 ──
CATEGORY_MAP = {
    '2': '价格', '3': '供给', '4': '库存',
    '5': '需求', '6': '进出口', '7': '成本利润', '8': '供需平衡'
}

# ── 关键词规则：指标名包含这些词 → 应归属某板块 ──
# (关键词, 应归属板块编号, 规则说明)
KEYWORD_RULES = [
    # 供给侧关键词
    (['矿产', '矿石产量', '矿：产量', '矿:产量', '精矿产量', '精矿：产量'], '3', '矿端产量'),
    (['TC', '加工费', 'treatment charge'], '3', 'TC加工费'),
    (['精炼产量', '精铅产量', '原生锌', '原生铅', '电解铜产量', '精铜产量',
      '精炼铜', '精炼镍', '精炼锡', '精炼锌', '电解铝', '原铝产量', '电解镍'], '3', '精炼产量'),
    (['产能利用率', '冶炼开工', '冶炼开工率', '开工率：冶炼', '检修'], '3', '开工率/检修'),
    (['再生铅', '再生锌', '再生铜', '废铜', '废铅', '废铝', '二次供应', '再生'], '3', '再生/二次'),
    # 库存侧关键词
    (['库存', '社会库存', '交易所库存', '仓单', '保税', '隐性库存', '在途',
      '注销', '注册仓单', 'LME库存', 'SHFE库存', '上期所库存', 'LME.*库存', 'SHFE.*库存'], '4', '库存'),
    # 需求侧关键词
    (['消费', '表观消费', '终端消费', '下游', '镀锌板', '镀锌开工',
      '不锈钢', '冷轧', '热轧', '压铸', '氧化锌', '硫酸镍', '多晶硅',
      '有机硅', '铝合金', '电池', '光伏', '新能源车', '开工率：下游',
      '排产', '产量：镀锌', '产量：不锈钢', '产量：压铸', '产量：氧化锌'], '5', '消费/下游'),
    # 进出口关键词
    (['进口量', '出口量', '进口', '出口', '发运', '贸易流', '净进口', 'HS'], '6', '进出口'),
    # 成本利润关键词
    (['利润', '成本', '盈利', '亏损', '能源', '电价', '焦炭', '煤炭',
      '石油焦', '硅煤'], '7', '成本/利润'),
    # 价格侧关键词（最低优先级，因为很多指标都含价格信息）
    (['升贴水', '基差', '价差', '月差', '期限结构', 'contango', 'backwardation',
      '进口盈亏', '沪伦比', '比价'], '2', '价差/升贴水'),
    (['持仓', '成交量', '多空', '前20', '席位', '资金'], '2', '持仓/资金'),
]

# ── 节点编号→板块编号 映射 ──
def node_to_category(node_code):
    """从节点编号提取板块号: 5.2→5, 3.1.1→3, 7.2→7"""
    return node_code.split('.')[0]

def parse_node_code(raw):
    """
    统一节点号格式：
      cu_2_1 → 2.1 ✓ (already handled by replace)
      pb_21 → 21 → 2.1 (need split)
      pb_32_3 → 32.3 → 3.2.3 (need split)
      pb_41_exchange_stock → 41.exchange.stock → 4.1 (strip name)
    """
    # 先替换 _ → .
    s = raw.replace('_', '.')
    # 去掉非数字后缀（如 exchange.stock → 只保留 41 → 4.1）
    # 找开头的数字部分
    m = re.match(r'^(\d+)', s)
    if not m:
        return s
    digits = m.group(1)
    rest = s[len(digits):]  # 可能是 .xxx 或空

    # 数字部分 >= 2位：首位=板块，其余=子节点
    if len(digits) >= 2:
        cat = digits[0]
        sub = '.'.join(digits[1:])
        node = cat + '.' + sub + rest
    else:
        node = digits + rest

    # 清理：去掉末尾的点，去掉连续点
    node = re.sub(r'\.+', '.', node).strip('.')
    return node


def extract_node_from_title(title):
    """
    从 HTML <title> 提取节点号：
      "铅(PB) 4.1 交易所库存 · 有色金属研究框架" → "4.1"
      "锌(ZN) 5.2 终端消费 · ..." → "5.2"
      "铜(CU) 2.1 进口盈亏与跨市贸易流 · ..." → "2.1"
    """
    m = re.search(r'\)\s+(\d+(?:\.\d+)+)', title)
    if m:
        return m.group(1)
    # fallback: 单级节点 "板块1 宏观"
    m = re.search(r'\)\s+板块(\d+)', title)
    if m:
        return m.group(1)
    return None


def filename_to_info(fname):
    """从文件名提取品种+节点: zn_5_2.html → (zn, 5.2)"""
    base = fname.replace('.html', '')
    # overview 页
    if base.endswith('_overview'):
        base2 = base.replace('_overview', '')
        parts = base2.split('_', 1)
        if len(parts) == 2:
            return parts[0], parse_node_code(parts[1]), True
        return parts[0], None, True

    parts = base.split('_', 1)
    if len(parts) < 2:
        return parts[0], None, False

    variety = parts[0]
    node_code = parse_node_code(parts[1])
    return variety, node_code, False


def classify_indicator(name, node_cat):
    """
    用关键词规则判定指标应归属板块。
    返回: (应归属板块号, 匹配的规则说明) 或 (None, None) 如果无匹配
    """
    matches = []
    for keywords, cat, rule_name in KEYWORD_RULES:
        for kw in keywords:
            if re.search(kw, name, re.IGNORECASE):
                matches.append((cat, rule_name))
                break

    if not matches:
        return None, None

    # 取第一个匹配的规则
    return matches[0]


def extract_charts_from_html(html_path):
    """从单个HTML提取所有图表信息"""
    fname = os.path.basename(html_path)
    variety, node_code, is_overview = filename_to_info(fname)

    html = open(html_path, 'r', encoding='utf-8').read()

    # 标题
    title_match = re.search(r'<title>(.*?)</title>', html)
    page_title = title_match.group(1) if title_match else ''

    # 版本号信息
    ver_match = re.search(r'v(\d+)\s+(\d+)\s*图', html)
    total_charts_declared = int(ver_match.group(2)) if ver_match else 0

    # 提取所有 chart 块
    chart_blocks = re.findall(
        r'<div class="chart">(.*?)</div>\s*</div>\s*</div>',
        html, re.DOTALL
    )
    if not chart_blocks:
        # fallback: 用更宽松的匹配
        chart_blocks = re.findall(
            r'<div class="chart">(.*?)(?=<div class="chart">|<div class="note">)',
            html, re.DOTALL
        )

    charts = []
    for i, block in enumerate(chart_blocks):
        chart = {'seq': i + 1}

        # 图标题
        t = re.search(r'chart-title">(.*?)</div>', block)
        chart['title'] = t.group(1) if t else ''

        # 副标题（含指标ID、频率、单位、数据点）
        s = re.search(r'chart-sub">(.*?)</div>', block)
        chart['sub'] = s.group(1) if s else ''

        # 提取指标ID（如 zn_52_output, cu_21_profit）
        ids = re.findall(r'([a-z]+_\d+[a-z_0-9]*(?:_\d+)?)', chart['sub'])
        chart['indicator_ids'] = list(dict.fromkeys(ids))  # 去重保序

        # 提取频率
        freq_match = re.search(r'(daily|weekly|monthly|周|月|日)', chart['sub'], re.IGNORECASE)
        chart['freq'] = freq_match.group(1) if freq_match else ''

        # 提取数据点
        pts = re.findall(r'(\d+)点', chart['sub'])
        chart['data_points'] = pts

        # 提取角色标注
        role = '普通'
        title_lower = chart['title'].lower()
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

        # 提取 note
        n = re.search(r'chart-note">(.*?)</div>', block, re.DOTALL)
        chart['note'] = n.group(1).replace('<br>', ' | ').strip() if n else ''

        charts.append(chart)

    return {
        'filename': fname,
        'variety': variety,
        'variety_zh': VARIETY_ZH.get(variety, variety),
        'node_code': node_code,
        'page_title': page_title,
        'is_overview': is_overview,
        'charts': charts,
        'total_charts_declared': total_charts_declared,
        'actual_charts': len(charts),
    }


def judge_placement(page_node_cat, indicator_name, indicator_ids, chart_role):
    """
    判定指标放在当前节点是否合理。
    返回: (判定, 应归属板块, 说明)
      判定: ✅ / 🟡 / 🔴
    
    核心规则：
    - 正主/主图：必须归属正确板块，跨板块=🔴
    - 补充/交叉验证：允许跨板块引用
    """
    expected_cat, rule_name = classify_indicator(indicator_name, page_node_cat)

    if expected_cat is None:
        return '🟢', None, '无关键词命中（可能正确，需人工确认）'

    if expected_cat == page_node_cat:
        return '✅', expected_cat, f'匹配规则「{rule_name}」→ 板块{expected_cat}({CATEGORY_MAP.get(expected_cat,"?")}) ✓'

    # 正主/主图不允许跨板块
    if chart_role in ['正主', '主图']:
        return '🔴', expected_cat, f'⚠️ {chart_role}指标「{rule_name}」→ 应归属板块{expected_cat}({CATEGORY_MAP.get(expected_cat,"?")})，但放在板块{page_node_cat}({CATEGORY_MAP.get(page_node_cat,"?")})'

    # 补充/交叉验证/备用库/普通 允许跨板块
    return '✅', expected_cat, f'跨板块引用正常（{chart_role}·{page_node_cat}页引用{expected_cat}类指标）'


def build_registry():
    """主流程：扫描所有HTML → 构建registry → 输出"""
    html_files = sorted(glob.glob(os.path.join(BASE, '*.html')))
    # 排除 index.html 和 assets
    html_files = [f for f in html_files if 'index.html' not in f]

    print(f"扫描 {len(html_files)} 个 HTML 文件...")

    all_pages = []
    all_charts = []  # flat list of (page_info, chart_info)
    anomalies = []

    for hf in html_files:
        page = extract_charts_from_html(hf)
        all_pages.append(page)

        if page['is_overview'] or not page['node_code']:
            continue

        node_cat = node_to_category(page['node_code'])

        for chart in page['charts']:
            # 用图标题做判定（标题包含完整指标名）
            title_text = chart['title']
            # 也用副标题里的指标ID
            ids_text = ' '.join(chart['indicator_ids'])

            verdict, expected_cat, reason = judge_placement(
                node_cat, title_text, chart['indicator_ids'], chart['role']
            )

            record = {
                'variety': page['variety'],
                'variety_zh': page['variety_zh'],
                'node': page['node_code'],
                'node_cat': node_cat,
                'node_cat_name': CATEGORY_MAP.get(node_cat, '?'),
                'filename': page['filename'],
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

            if verdict == '🔴':
                anomalies.append(record)

    print(f"  提取 {len(all_charts)} 张图 / {len(all_pages)} 个页面")
    print(f"  异常: {len(anomalies)} 张图归属可疑")

    # ── 统计 ──
    verdict_counts = Counter(r['verdict'] for r in all_charts)
    variety_counts = Counter(r['variety'] for r in all_charts)
    cat_counts = Counter(r['node_cat'] for r in all_charts)

    # ── 输出 Markdown ──
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write(f"# CHART_REGISTRY — 全品种图×指标映射表\n\n")
        f.write(f"> 自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')} · 扫描 {len(all_pages)} 页 / {len(all_charts)} 图\n\n")

        # ── 概要统计 ──
        f.write("## 概要\n\n")
        f.write("| 维度 | 数值 |\n|---|---|\n")
        f.write(f"| 总页面 | {len(all_pages)} |\n")
        f.write(f"| 总图数 | {len(all_charts)} |\n")
        f.write(f"| ✅ 归属正确 | {verdict_counts.get('✅', 0)} |\n")
        f.write(f"| 🟢 无关键词命中(待人工) | {verdict_counts.get('🟢', 0)} |\n")
        f.write(f"| 🔴 归属可疑 | {verdict_counts.get('🔴', 0)} |\n")
        f.write("\n")

        f.write("### 按品种\n\n")
        f.write("| 品种 | 页面数 | 图数 | 异常 |\n|---|---|---|---|\n")
        for v in ['cu', 'al', 'pb', 'zn', 'ni', 'sn', 'si', 'li']:
            v_pages = sum(1 for p in all_pages if p['variety'] == v and not p['is_overview'])
            v_charts = sum(1 for r in all_charts if r['variety'] == v)
            v_anom = sum(1 for r in all_charts if r['variety'] == v and r['verdict'] == '🔴')
            f.write(f"| {VARIETY_ZH.get(v, v)}({v.upper()}) | {v_pages} | {v_charts} | {v_anom} |\n")
        f.write("\n")

        f.write("### 按板块\n\n")
        f.write("| 板块 | 图数 | 异常 |\n|---|---|---|\n")
        for cat_id in ['2', '3', '4', '5', '6', '7', '8']:
            c_charts = sum(1 for r in all_charts if r['node_cat'] == cat_id)
            c_anom = sum(1 for r in all_charts if r['node_cat'] == cat_id and r['verdict'] == '🔴')
            f.write(f"| {cat_id} {CATEGORY_MAP.get(cat_id, '?')} | {c_charts} | {c_anom} |\n")
        f.write("\n")

        # ── 异常报告（优先展示） ──
        f.write("---\n\n## 🔴 异常报告（归属可疑）\n\n")
        if anomalies:
            f.write(f"共 {len(anomalies)} 张图指标归属与所在板块不匹配：\n\n")
            f.write("| 品种 | 节点 | 图# | 图标题 | 指标ID | 应归属 | 判定理由 |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for a in sorted(anomalies, key=lambda x: (x['variety'], x['node'])):
                title_short = a['chart_title'][:40] + ('...' if len(a['chart_title']) > 40 else '')
                ids = ', '.join(a['indicator_ids'][:3])
                expected = f"{a['expected_cat']}.{a['expected_cat_name']}" if a['expected_cat'] else '?'
                f.write(f"| {a['variety_zh']} | {a['node']} | C{a['chart_seq']} | {title_short} | {ids} | {expected} | {a['reason']} |\n")
        else:
            f.write("✅ 无异常。\n")
        f.write("\n")

        # ── 全量明细表（按品种→节点→图） ──
        f.write("---\n\n## 全量明细\n\n")

        current_variety = None
        current_node = None

        for r in sorted(all_charts, key=lambda x: (x['variety'], x['node'], x['chart_seq'])):
            if r['variety'] != current_variety:
                current_variety = r['variety']
                current_node = None
                f.write(f"### {r['variety_zh']}({r['variety'].upper()})\n\n")
                f.write("| 节点 | 板块 | 图# | 角色 | 图标题 | 指标ID | 频率 | 数据点 | 判定 |\n")
                f.write("|---|---|---|---|---|---|---|---|---|\n")

            if r['node'] != current_node:
                current_node = r['node']

            title_short = r['chart_title'][:50] + ('...' if len(r['chart_title']) > 50 else '')
            ids = ', '.join(r['indicator_ids'][:3])
            pts = '/'.join(r['data_points'][:2]) if r['data_points'] else '-'
            f.write(f"| {r['node']} | {r['node_cat']}.{r['node_cat_name']} | C{r['chart_seq']} | {r['role']} | {title_short} | {ids} | {r['freq']} | {pts} | {r['verdict']} |\n")

        f.write("\n")

        # ── Overview 页清单 ──
        f.write("---\n\n## Overview 页（总览）\n\n")
        f.write("| 品种 | 文件名 | 标题 | 声明图数 |\n|---|---|---|---|\n")
        for p in all_pages:
            if p['is_overview']:
                f.write(f"| {p['variety_zh']} | {p['filename']} | {p['page_title'][:40]} | {p['total_charts_declared'] or '-'} |\n")
        f.write("\n")

        # ── 无图的节点页 ──
        empty_pages = [p for p in all_pages if not p['is_overview'] and p['actual_charts'] == 0]
        if empty_pages:
            f.write("---\n\n## ⚠️ 无图页面\n\n")
            f.write("| 品种 | 节点 | 文件名 |\n|---|---|---|\n")
            for p in empty_pages:
                f.write(f"| {p['variety_zh']} | {p['node_code']} | {p['filename']} |\n")
            f.write("\n")

    print(f"  ✅ Markdown → {OUT_MD}")

    # ── 输出 JSON ──
    if '--json' in sys.argv or True:  # 默认也输出JSON
        registry_data = {
            '_meta': {
                'version': '1.0',
                'generated': datetime.now().isoformat(),
                'total_pages': len(all_pages),
                'total_charts': len(all_charts),
                'anomalies': len(anomalies),
            },
            'charts': all_charts,
            'pages': [
                {
                    'filename': p['filename'],
                    'variety': p['variety'],
                    'node_code': p['node_code'],
                    'is_overview': p['is_overview'],
                    'actual_charts': p['actual_charts'],
                }
                for p in all_pages
            ],
        }
        with open(OUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ JSON → {OUT_JSON}")

    # ── 终端摘要 ──
    print(f"\n{'='*60}")
    print(f"  判定分布: ✅={verdict_counts.get('✅',0)}  🟢={verdict_counts.get('🟢',0)}  🔴={verdict_counts.get('🔴',0)}")
    print(f"  异常品种分布:")
    anom_by_variety = Counter(a['variety'] for a in anomalies)
    for v, n in anom_by_variety.most_common():
        print(f"    {VARIETY_ZH.get(v,v)}({v.upper()}): {n} 张图")
    print(f"{'='*60}")


if __name__ == '__main__':
    build_registry()
