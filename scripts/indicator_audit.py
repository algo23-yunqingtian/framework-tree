#!/usr/bin/env python3
"""
indicator_audit.py — 全品种指标归属审计工具
用法: python3 scripts/indicator_audit.py [--variety NI] [--fix]

输出:
  data/audit_report.json     ← 机器可读
  docs/AUDIT_REPORT.md       ← 人类可读

审计维度:
  1. 万金油检测 — 同一指标被 ≥3 个节点使用
  2. 板块串用 — 指标的题材归属 vs 所在节点板块
  3. 正主缺失 — 节点应有正主指标但缺失
  4. 冗余膨胀 — 节点图数超标(>6)
  5. 空节点 — 子页面0图
"""

import re, os, sys, json, argparse
from collections import defaultdict, Counter
from datetime import datetime

# ============================================================
# 品种配置: 每个品种的板块定义 + 正主预期
# 新增品种只需在此添加, 不需要改主逻辑
# ============================================================
VARIETY_CONFIG = {
    'NI': {
        'zh': '镍',
        'boards': {
            '2': '价格信号',
            '3': '供给',
            '4': '库存',
            '5': '需求',
            '6': '进出口',
            '7': '成本利润',
        },
        # 每个节点期望的正主指标关键词(只要标题命中任一即算正主存在)
        'node_expectations': {
            '2.1': ['收盘价', '持仓', '成交量'],
            '2.2': ['升贴水', '基差', '现货'],
            '2.3': ['沪伦比', '比价', '进口盈亏'],
            '2.4': ['期限结构', '月差', '价差'],
            '2.5': ['加工费', 'TC'],
            '2.6': ['持仓', '资金'],
            '3.1.1': ['产量', '开工率', '印尼'],
            '3.1.2': ['产能', '投产'],
            '3.1.3': ['镍铁', 'NPI'],
            '3.1.4': ['矿', '进口', '红土'],
            '3.1.5': ['精炼', '电解镍'],
            '3.2.1': ['中国', '产量'],
            '3.2.2': ['开工率'],
            '3.2.3': ['冰镍', 'MHP'],
            '3.2.4': ['硫酸镍', '产量'],
            '4.1': ['LME', '库存'],
            '4.2': ['SHFE', '上期所', '库存'],
            '4.3': ['社会库存', '社库'],
            '4.4': ['镍豆', '库存'],
            '4.5': ['仓单', '注销'],
            '5.1': ['不锈钢', '排产'],
            '5.2': ['硫酸镍', '电池', '新能源'],
            '5.3': ['表观消费', '消费'],
            '6.1': ['进口', '矿'],
            '6.2': ['精炼', '进口'],
            '6.3': ['出口'],
            '6.4': ['LME', '地区', '库存'],
            '7.1': ['冶炼', '利润', '成本'],
            '7.2': ['RKEF', '镍铁', '成本'],
            '7.3': ['硫酸镍', '利润'],
        },
        # 指标标题关键词 → 应归属板块
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '沪伦比', '比价', '期限结构', '月差', '价差', '持仓量', '成交量', '持仓', '开盘价'],
            '3': ['产量', '产能', '开工率', '运行产能', '投产', '检修', '复产', '精炼镍：产量', '镍铁：产量', 'NPI', '冰镍：产量', 'MHP：产量', '硫酸镍：产量'],
            '4': ['库存', '仓单', '注销', '库存天数', '社库'],
            '5': ['消费', '需求', '排产', '表观消费', '不锈钢', '冷轧', '硫酸镍：产量'],  # 硫酸镍产量既算3也算5, 看节点
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量', '进口盈亏'],
            '7': ['利润', '成本', '加工费', 'TC', '冶炼利润', '现金成本', '完全成本'],
        },
        # 标准答案指标数上限(来自同花顺发散/独立看板)
        'max_charts': 25,
        'max_indicators': 55,
    },
    'ZN': {
        'zh': '锌',
        'boards': {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'},
        'node_expectations': {},  # 后续补充
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '沪伦比', '比价', '期限结构', '月差', '价差', '持仓量', '成交量'],
            '3': ['产量', '产能', '开工率', '冶炼', '精矿', 'TC', '加工费'],
            '4': ['库存', '仓单', '注销', '社库'],
            '5': ['消费', '需求', '镀锌', '压铸', '氧化锌', '表观消费'],
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量'],
            '7': ['利润', '成本', '冶炼利润'],
        },
        'max_charts': 25,
        'max_indicators': 55,
    },
    'CU': {
        'zh': '铜',
        'boards': {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'},
        'node_expectations': {},
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '沪伦比', '比价', '期限结构', '月差', '价差', '持仓量', '成交量'],
            '3': ['产量', '产能', '开工率', '精矿', 'TC', '加工费', '粗铜'],
            '4': ['库存', '仓单', '注销', '社库', '保税'],
            '5': ['消费', '需求', '电缆', '铜杆', '铜箔', '表观消费'],
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量', '进口盈亏'],
            '7': ['利润', '成本', '冶炼利润', 'TC'],
        },
        'max_charts': 25,
        'max_indicators': 55,
    },
    'AL': {
        'zh': '铝',
        'boards': {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'},
        'node_expectations': {},
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '沪伦比', '比价', '期限结构', '月差', '价差', '持仓量', '成交量'],
            '3': ['产量', '产能', '开工率', '电解铝', '氧化铝', '运行产能'],
            '4': ['库存', '仓单', '注销', '社库', '厂内库存'],
            '5': ['消费', '需求', '铝材', '铝板', '铝箔', '铝型材', '表观消费'],
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量'],
            '7': ['利润', '成本', '电力成本', '氧化铝成本'],
        },
        'max_charts': 25,
        'max_indicators': 55,
    },
    'PB': {
        'zh': '铅',
        'boards': {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'},
        'node_expectations': {},
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '沪伦比', '比价', '期限结构', '月差', '价差', '持仓量', '成交量'],
            '3': ['产量', '产能', '开工率', '精矿', '再生铅', '原生铅'],
            '4': ['库存', '仓单', '注销', '社库', '厂库'],
            '5': ['消费', '需求', '蓄电池', '电动车', '汽车', '表观消费'],
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量'],
            '7': ['利润', '成本', '再生铅成本', '冶炼利润'],
        },
        'max_charts': 25,
        'max_indicators': 55,
    },
    'SN': {
        'zh': '锡',
        'boards': {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'},
        'node_expectations': {},
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '沪伦比', '比价', '期限结构', '月差', '价差', '持仓量', '成交量'],
            '3': ['产量', '产能', '开工率', '精矿', '缅甸', '印尼'],
            '4': ['库存', '仓单', '注销', '社库'],
            '5': ['消费', '需求', '焊料', '光伏', '半导体', '表观消费'],
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量'],
            '7': ['利润', '成本', '冶炼利润'],
        },
        'max_charts': 25,
        'max_indicators': 55,
    },
    'SI': {
        'zh': '硅',
        'boards': {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'},
        'node_expectations': {},
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '比价', '价差', '持仓量', '成交量'],
            '3': ['产量', '产能', '开工率', '硅铁', '工业硅', '多晶硅'],
            '4': ['库存', '仓单', '注销', '社库', '厂库'],
            '5': ['消费', '需求', '多晶硅', '有机硅', '光伏', '表观消费'],
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量'],
            '7': ['利润', '成本', '电力成本'],
        },
        'max_charts': 25,
        'max_indicators': 55,
    },
    'LI': {
        'zh': '锂',
        'boards': {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'},
        'node_expectations': {},
        'keyword_board_map': {
            '2': ['收盘价', '升贴水', '基差', '价差', '持仓量', '成交量', '仓单'],
            '3': ['产量', '产能', '开工率', '锂辉石', '锂云母', '盐湖'],
            '4': ['库存', '仓单', '注销', '社库', '厂库'],
            '5': ['消费', '需求', '正极', '电池', '排产', '储能', '表观消费'],
            '6': ['进口量', '出口量', '海关', '进口数量', '出口数量'],
            '7': ['利润', '成本', '冶炼利润', '外购'],
        },
        'max_charts': 25,
        'max_indicators': 55,
    },
}


# ============================================================
# Step 1: 解析 HTML
# ============================================================
def parse_variety_html(variety_code):
    """解析某品种所有HTML, 返回结构化数据"""
    prefix = variety_code.lower() + '_'
    files = sorted([f for f in os.listdir('.')
                    if f.startswith(prefix) and f.endswith('.html') and 'overview' not in f])

    pages = {}
    all_indicators = {}  # id → {title, nodes, roles}

    for fname in files:
        node_raw = fname.replace(prefix, '').replace('.html', '')
        node = node_raw.replace('_', '.')

        with open(fname) as f:
            html = f.read()

        titles = re.findall(r'chart-title[">](.*?)</div>', html)
        subs = re.findall(r'chart-sub[">](.*?)</div>', html)

        charts = []
        for t, s in zip(titles, subs):
            t = t.strip().lstrip('>')
            s = s.strip().lstrip('>')
            ids = [x.strip() for x in re.findall(r'[a-z]{2}_\w+', s)]
            role = '主图' if '主图' in t else ('补充' if '补充' in t else '普通')
            title_clean = re.sub(r'（(主图|补充)[^）]*）', '', t).strip()

            chart_info = {
                'title': title_clean,
                'full_title': t,
                'ids': ids,
                'role': role,
            }
            charts.append(chart_info)

            for ind_id in ids:
                if ind_id not in all_indicators:
                    all_indicators[ind_id] = {
                        'title': title_clean[:80],
                        'nodes': set(),
                        'roles': set(),
                    }
                all_indicators[ind_id]['nodes'].add(node)
                all_indicators[ind_id]['roles'].add(role)

        pages[node] = {
            'file': fname,
            'charts': charts,
            'chart_count': len(charts),
        }

    # set → list for JSON serialization
    for ind_id, info in all_indicators.items():
        info['nodes'] = sorted(info['nodes'])
        info['roles'] = sorted(info['roles'])

    return pages, all_indicators


# ============================================================
# Step 2: 五维审计
# ============================================================
def classify_board(title, keyword_board_map):
    """根据标题关键词判断指标应归属板块"""
    for board, keywords in keyword_board_map.items():
        for kw in keywords:
            if kw in title:
                return board
    return None


def audit_variety(variety_code, pages, all_indicators):
    """执行五维审计"""
    config = VARIETY_CONFIG[variety_code]
    zh = config['zh']
    kw_map = config.get('keyword_board_map', {})
    max_charts = config.get('max_charts', 25)
    max_ind = config.get('max_indicators', 55)
    board_names = config.get('boards', {})

    issues = {
        'overuse': [],       # 1. 万金油
        'cross_board': [],   # 2. 板块串用
        'missing_anchor': [], # 3. 正主缺失
        'bloat': [],         # 4. 冗余膨胀
        'empty': [],         # 5. 空节点
    }

    # --- 审计1: 万金油检测 ---
    for ind_id, info in all_indicators.items():
        n = len(info['nodes'])
        if n >= 3:
            severity = '🔴' if n >= 5 else '🟡'
            issues['overuse'].append({
                'indicator_id': ind_id,
                'title': info['title'],
                'used_in_n_nodes': n,
                'nodes': info['nodes'],
                'severity': severity,
                'recommendation': f'此指标被{n}个节点使用，建议只保留在最核心的1-2个节点作为主图/辅轴，其余节点移除',
            })

    # --- 审计2: 板块串用 ---
    for node, page in pages.items():
        node_board = node.split('.')[0]
        for chart in page['charts']:
            expected_board = classify_board(chart['title'], kw_map)
            if expected_board and expected_board != node_board:
                # 正主/主图跨板块 = 严重; 补充/普通跨板块 = 轻微
                if chart['role'] in ('正主', '主图'):
                    severity = '🔴'
                else:
                    severity = '🟡'

                issues['cross_board'].append({
                    'node': node,
                    'file': page['file'],
                    'chart_title': chart['full_title'][:60],
                    'chart_role': chart['role'],
                    'actual_board': node_board,
                    'actual_board_name': board_names.get(node_board, '?'),
                    'expected_board': expected_board,
                    'expected_board_name': board_names.get(expected_board, '?'),
                    'severity': severity,
                    'recommendation': f'{chart["role"]}指标应归属{expected_board}.{board_names.get(expected_board, "?")}，当前在{node_board}.{board_names.get(node_board, "?")}',
                })

    # --- 审计3: 正主缺失 ---
    node_expectations = config.get('node_expectations', {})
    for node, expected_kws in node_expectations.items():
        if node not in pages:
            issues['missing_anchor'].append({
                'node': node,
                'severity': '🟡',
                'recommendation': f'节点{node}页面缺失(预期关键词: {"/".join(expected_kws)})',
            })
            continue

        page = pages[node]
        found = False
        found_in = None
        # Check ALL charts (not just 主图) for keyword match
        for chart in page['charts']:
            for kw in expected_kws:
                if kw in chart['title'] or kw in chart.get('full_title', ''):
                    found = True
                    found_in = chart['role']
                    break
            if found:
                break

        if not found:
            issues['missing_anchor'].append({
                'node': node,
                'file': page['file'],
                'chart_count': page['chart_count'],
                'expected_keywords': expected_kws,
                'actual_titles': [c['title'][:50] for c in page['charts']],
                'severity': '🔴',
                'recommendation': f'节点{node}所有图表均未命中预期关键词({"/".join(expected_kws)})，正主指标确实缺失',
            })
        elif found_in and found_in != '主图':
            issues['missing_anchor'].append({
                'node': node,
                'file': page['file'],
                'chart_count': page['chart_count'],
                'expected_keywords': expected_kws,
                'found_in_role': found_in,
                'actual_titles': [c['title'][:50] for c in page['charts']],
                'severity': '🟡',
                'recommendation': f'节点{node}的正主指标以{found_in}形式存在，建议提升为主图',
            })

    # --- 审计4: 冗余膨胀 ---
    total_charts = sum(p['chart_count'] for p in pages.values())
    if total_charts > max_charts:
        issues['bloat'].append({
            'total_charts': total_charts,
            'max_expected': max_charts,
            'ratio': f'{total_charts/max_charts:.1f}x',
            'severity': '🔴' if total_charts > max_charts * 2 else '🟡',
            'recommendation': f'全品种{total_charts}张图远超标准{max_charts}张，需精简。优先删除万金油指标的重复引用',
        })

    total_indicators = len(all_indicators)
    if total_indicators > max_ind:
        issues['bloat'].append({
            'total_indicators': total_indicators,
            'max_expected': max_ind,
            'ratio': f'{total_indicators/max_ind:.1f}x',
            'severity': '🔴' if total_indicators > max_ind * 1.5 else '🟡',
            'recommendation': f'共{total_indicators}个独立指标超过标准{max_ind}个，需检查是否有同义指标(不同ID但相同含义)',
        })

    # 单节点膨胀
    for node, page in pages.items():
        if page['chart_count'] > 6:
            issues['bloat'].append({
                'node': node,
                'file': page['file'],
                'chart_count': page['chart_count'],
                'severity': '🟡',
                'recommendation': f'节点{node}有{page["chart_count"]}张图(上限6)，建议精简到核心3-4张',
            })

    # --- 审计5: 空节点 ---
    for node, page in pages.items():
        if page['chart_count'] == 0:
            issues['empty'].append({
                'node': node,
                'file': page['file'],
                'severity': '🔴',
                'recommendation': f'节点{node}无图表，需补充数据或合并到相邻节点',
            })

    # --- 汇总 ---
    severity_counts = Counter()
    for cat, items in issues.items():
        for item in items:
            severity_counts[item['severity']] += 1

    return {
        'variety': variety_code,
        'variety_zh': zh,
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_pages': len(pages),
            'total_charts': sum(p['chart_count'] for p in pages.values()),
            'total_indicators': len(all_indicators),
            'max_charts_expected': max_charts,
            'max_indicators_expected': max_ind,
            'severity_counts': dict(severity_counts),
            'issue_counts': {cat: len(items) for cat, items in issues.items()},
        },
        'issues': issues,
    }


# ============================================================
# Step 3: 生成修复建议
# ============================================================
def generate_fix_plan(audit_result, all_indicators):
    """根据审计结果生成修复计划"""
    plan = {
        'variety': audit_result['variety'],
        'remove_indicators': [],   # 从哪些节点移除哪些指标
        'keep_indicators': [],     # 保留的指标+节点
        'add_indicators': [],      # 需要补充的指标
        'merge_candidates': [],    # 可能合并的同义指标
    }

    # 从万金油问题生成修复建议
    for item in audit_result['issues']['overuse']:
        ind_id = item['indicator_id']
        nodes = item['nodes']
        # 保留在前2个节点(按节点号排序), 移除其余
        keep = nodes[:2]
        remove = nodes[2:]
        plan['remove_indicators'].append({
            'indicator_id': ind_id,
            'title': item['title'],
            'keep_in': keep,
            'remove_from': remove,
            'reason': f'万金油: 被{len(nodes)}个节点使用, 保留{keep}',
        })

    # 从板块串用生成修复建议
    for item in audit_result['issues']['cross_board']:
        if item['severity'] == '🔴':
            plan['remove_indicators'].append({
                'indicator_id': '见HTML',
                'title': item['chart_title'],
                'node': item['node'],
                'reason': f'板块串用: {item["actual_board_name"]}页的{item["chart_role"]}应归属{item["expected_board_name"]}',
            })

    # 检测可能合并的同义指标
    title_groups = defaultdict(list)
    for ind_id, info in all_indicators.items():
        # 归一化标题(去后缀)
        base = re.sub(r'[：:（(].*$', '', info['title']).strip()
        if len(base) > 5:
            title_groups[base].append(ind_id)

    for base, ids in title_groups.items():
        if len(ids) > 1:
            plan['merge_candidates'].append({
                'base_title': base,
                'indicator_ids': ids,
                'count': len(ids),
                'reason': f'{len(ids)}个指标标题相似, 可能可合并',
            })

    return plan


# ============================================================
# Step 4: 输出报告
# ============================================================
def write_report(audit_result, fix_plan):
    """生成 Markdown + JSON 报告"""
    r = audit_result
    s = r['summary']
    zh = r['variety_zh']
    code = r['variety']

    # --- JSON ---
    os.makedirs('data', exist_ok=True)
    json_path = f'data/audit_{code.lower()}.json'
    with open(json_path, 'w') as f:
        json.dump({
            'audit': audit_result,
            'fix_plan': fix_plan,
        }, f, ensure_ascii=False, indent=2)

    # --- Markdown ---
    os.makedirs('docs', exist_ok=True)
    md_path = f'docs/AUDIT_{code}_REPORT.md'

    lines = []
    lines.append(f'# {zh}({code}) 指标归属审计报告')
    lines.append(f'> 自动生成 · {r["timestamp"][:19]} · indicator_audit.py')
    lines.append('')
    lines.append('## 概要')
    lines.append('')
    lines.append('| 维度 | 实际 | 标准上限 | 状态 |')
    lines.append('|---|---|---|---|')
    chart_status = '🔴' if s['total_charts'] > s['max_charts_expected'] * 2 else ('🟡' if s['total_charts'] > s['max_charts_expected'] else '✅')
    ind_status = '🔴' if s['total_indicators'] > s['max_indicators_expected'] * 1.5 else ('🟡' if s['total_indicators'] > s['max_indicators_expected'] else '✅')
    lines.append(f'| 页面数 | {s["total_pages"]} | — | — |')
    lines.append(f'| 图数 | {s["total_charts"]} | {s["max_charts_expected"]} | {chart_status} |')
    lines.append(f'| 独立指标 | {s["total_indicators"]} | {s["max_indicators_expected"]} | {ind_status} |')
    lines.append('')

    sev = s.get('severity_counts', {})
    lines.append(f'**问题严重度**: 🔴{sev.get("🔴", 0)} / 🟡{sev.get("🟡", 0)}')
    lines.append('')

    ic = s.get('issue_counts', {})
    lines.append('| 审计维度 | 问题数 |')
    lines.append('|---|---|')
    dim_names = {
        'overuse': '万金油(≥3节点复用)',
        'cross_board': '板块串用',
        'missing_anchor': '正主缺失',
        'bloat': '冗余膨胀',
        'empty': '空节点',
    }
    for dim, name in dim_names.items():
        cnt = ic.get(dim, 0)
        icon = '🔴' if cnt >= 3 else ('🟡' if cnt >= 1 else '✅')
        lines.append(f'| {name} | {cnt} {icon} |')
    lines.append('')

    # --- 详细问题列表 ---
    lines.append('---')
    lines.append('')
    lines.append('## 🔴 严重问题')
    lines.append('')

    for cat, items in r['issues'].items():
        severe = [i for i in items if i.get('severity') == '🔴']
        if not severe:
            continue
        lines.append(f'### {dim_names.get(cat, cat)} ({len(severe)}条)')
        lines.append('')
        for item in severe[:15]:
            if cat == 'overuse':
                lines.append(f'- **{item["indicator_id"]}**: {item["title"][:50]} → 被{item["used_in_n_nodes"]}个节点使用')
                lines.append(f'  - 节点: {", ".join(item["nodes"][:8])}{"..." if len(item["nodes"]) > 8 else ""}')
                lines.append(f'  - 💡 {item["recommendation"]}')
            elif cat == 'cross_board':
                lines.append(f'- **{item["node"]}**: {item["chart_title"][:50]}')
                lines.append(f'  - 当前: {item["actual_board"]}.{item["actual_board_name"]} | 应属: {item["expected_board"]}.{item["expected_board_name"]}')
                lines.append(f'  - 💡 {item["recommendation"]}')
            elif cat == 'missing_anchor':
                lines.append(f'- **{item["node"]}**: 预期关键词 {item.get("expected_keywords", "N/A")}')
                if 'actual_titles' in item:
                    lines.append(f'  - 实际标题: {", ".join(item["actual_titles"][:3])}')
                lines.append(f'  - 💡 {item["recommendation"]}')
            elif cat == 'bloat':
                lines.append(f'- {item.get("node", "全局")}: {item["recommendation"]}')
            elif cat == 'empty':
                lines.append(f'- **{item["node"]}**: {item["recommendation"]}')
            lines.append('')
        if len(severe) > 15:
            lines.append(f'  ... 还有{len(severe)-15}条，详见JSON')
            lines.append('')

    # --- 黄色问题 ---
    lines.append('## 🟡 待确认问题')
    lines.append('')
    yellow_count = sum(1 for cat, items in r['issues'].items() for i in items if i.get('severity') == '🟡')
    lines.append(f'共 {yellow_count} 条，详见 `{json_path}`')
    lines.append('')

    # --- 修复计划 ---
    lines.append('---')
    lines.append('')
    lines.append('## 修复计划')
    lines.append('')

    if fix_plan['remove_indicators']:
        lines.append(f'### 需移除 ({len(fix_plan["remove_indicators"])}项)')
        lines.append('')
        lines.append('| # | 指标/图 | 节点 | 原因 |')
        lines.append('|---|---|---|---|')
        for i, item in enumerate(fix_plan['remove_indicators'][:20]):
            title = item.get('title', '')[:40]
            node = item.get('node', item.get('remove_from', '?'))
            if isinstance(node, list):
                node = ','.join(node[:3])
            lines.append(f'| {i+1} | {title} | {node} | {item["reason"][:50]} |')
        lines.append('')

    if fix_plan['merge_candidates']:
        lines.append(f'### 可合并候选 ({len(fix_plan["merge_candidates"])}组)')
        lines.append('')
        for mc in fix_plan['merge_candidates'][:10]:
            lines.append(f'- **{mc["base_title"][:50]}** ({mc["count"]}个): {", ".join(mc["indicator_ids"][:5])}')
        lines.append('')

    lines.append('---')
    lines.append('')
    lines.append('## 使用方法')
    lines.append('')
    lines.append('1. 审读上方🔴问题，确认每个是否确实需要修')
    lines.append('2. 对确认要修的项，定位到对应的build脚本和HTML')
    lines.append('3. 修改build脚本后重新生成HTML')
    lines.append('4. 重跑 `python3 scripts/indicator_audit.py --variety ' + code + '` 验证')
    lines.append('')

    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))

    return md_path, json_path


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='全品种指标归属审计')
    parser.add_argument('--variety', '-v', help='品种代码(NI/ZN/CU/AL/PB/SN/SI/LI), 不指定则审计全部')
    parser.add_argument('--fix', action='store_true', help='生成修复建议')
    args = parser.parse_args()

    varieties = [args.variety.upper()] if args.variety else list(VARIETY_CONFIG.keys())

    all_results = []
    for vcode in varieties:
        if vcode not in VARIETY_CONFIG:
            print(f'⚠️ 品种 {vcode} 未配置, 跳过')
            continue

        config = VARIETY_CONFIG[vcode]
        prefix = vcode.lower() + '_'

        # 检查是否有HTML
        files = [f for f in os.listdir('.') if f.startswith(prefix) and f.endswith('.html')]
        if not files:
            print(f'⚠️ {config["zh"]}({vcode}): 无HTML文件, 跳过')
            continue

        pages, all_indicators = parse_variety_html(vcode)
        result = audit_variety(vcode, pages, all_indicators)
        fix_plan = generate_fix_plan(result, all_indicators)
        md_path, json_path = write_report(result, fix_plan)

        s = result['summary']
        sev = s['severity_counts']
        print(f'\n{"="*60}')
        print(f'  {config["zh"]}({vcode}): {s["total_pages"]}页 / {s["total_charts"]}图 / {s["total_indicators"]}指标')
        print(f'  🔴 {sev.get("🔴", 0)} / 🟡 {sev.get("🟡", 0)}')
        print(f'  📄 {md_path}')
        print(f'  📦 {json_path}')
        print(f'{"="*60}')

        all_results.append((vcode, result, fix_plan))

    # 全品种汇总
    if len(all_results) > 1:
        print(f'\n{"="*60}')
        print(f'  全品种汇总: {len(all_results)}个品种')
        total_red = sum(r[1]['summary']['severity_counts'].get('🔴', 0) for r in all_results)
        total_yellow = sum(r[1]['summary']['severity_counts'].get('🟡', 0) for r in all_results)
        print(f'  🔴 总严重: {total_red} / 🟡 总待确认: {total_yellow}')
        print(f'{"="*60}')


if __name__ == '__main__':
    main()
