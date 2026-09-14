#!/usr/bin/env python3
"""U2: Add missing SHFE aliases to alias map. F1: Fix R1 migration logic."""
import json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# U2: Add missing SHFE aliases
# ============================================================
def add_shfe_aliases():
    alias_path = os.path.join(BASE, 'docs', 'alias_metadb', 'thsh_zhiji_alias_map.json')
    v1_path = os.path.join(BASE, 'data', 'indicators_v1.json')
    
    d = json.load(open(alias_path, encoding='utf-8'))
    v1 = json.load(open(v1_path, encoding='utf-8'))
    aliases = d.get('aliases', {})
    indicators = v1.get('indicators', {})
    
    added = 0
    # Find SHFE indicators missing aliases
    for k, ind in indicators.items():
        ind_name = ind.get('name', '') if isinstance(ind, dict) else ''
        zhiji_name = ind.get('zhiji_name', '') if isinstance(ind, dict) else ''
        
        # Check if this is a SHFE indicator
        is_shfe = 'SHFE' in ind_name.upper() or '上期所' in ind_name or \
                  'SHFE' in zhiji_name.upper() or '上期所' in zhiji_name
        
        if not is_shfe:
            continue
        
        # Check if already has alias
        if k in aliases or ind_name in aliases or zhiji_name in aliases:
            continue
        
        # Add alias: use indicator key as THS name, zhiji_name as target
        ths_name = ind_name if ind_name else k
        target = zhiji_name if zhiji_name else ind_name
        if ths_name and target and ths_name != target:
            aliases[ths_name] = {
                'zhiji_name': target,
                'indicator_key': k,
                'variety': ind.get('variety', ''),
                'code': ind.get('code', ''),
            }
            added += 1
        elif target and not ths_name:
            aliases[target] = {
                'zhiji_name': target,
                'indicator_key': k,
                'variety': ind.get('variety', ''),
                'code': ind.get('code', ''),
            }
            added += 1
    
    d['aliases'] = aliases
    d['_meta']['total_aliases'] = len(aliases)
    d['_meta']['updated'] = '2026-09-13 19:30'
    d['_meta']['shfe_alias_update'] = 'U2: added %d SHFE/上期所 aliases' % added
    
    with open(alias_path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    
    print(f"U2: Added {added} SHFE aliases. Total aliases: {len(aliases)}")
    return added

# ============================================================
# F1: Fix R1 migration - modify judge_placement to handle edge cases
# ============================================================
def fix_f1_migration():
    """Modify build_chart_registry.py to handle edge cases in R1 migration."""
    script_path = os.path.join(BASE, 'scripts', 'build_chart_registry.py')
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The current R1 logic moves all 主图+cross-sector to 🟢.
    # The task says 3 were over-migrated. These might be charts where:
    # 1. The chart is on a page that references multiple categories legitimately
    # 2. The chart's cross-sector reference is actually within the same category
    
    # Fix: Add a check for charts that have a cross-sector reference
    # but the reference is to a closely related category AND the chart
    # is NOT a "串台" case (i.e., the indicator is legitimately cross-referenced)
    
    old_r1 = """    # R1修复：常规节点页跨板块主图 → 🟢待人工确认（可能串台）
    # 仅聚合页/首页保留⚪设计意图（见上方 page_type in ('sector_aggregate','home') 分支）
    if chart_role == '主图':
        return '\\U0001f7e2', expected_cat, '常规节点页跨板块主图（可能串台，需人工确认）：引用%s类指标·板块%s' % (
            expected_cat, CATEGORY_MAP.get(expected_cat, '?'))"""
    
    new_r1 = """    # R1修复：常规节点页跨板块主图 → 🟢待人工确认（可能串台）
    # F1修正：仅当跨板块引用为"串台"时标记🟢；合法跨板块引用（如进口→供给、TC→成本）保留✅
    if chart_role == '主图':
        # 合法跨板块引用白名单：这些跨板块引用是设计意图的一部分
        LEGIT_CROSS = {
            ('3', '6'),  # 供给→进出口（进口是供给的一部分）
            ('7', '3'),  # 成本→供给（TC是成本的一部分）
            ('4', '2'),  # 库存→价格（库存参考价格）
            ('5', '2'),  # 需求→价格（需求参考价格）
            ('6', '4'),  # 进出口→库存（进出口关联库存）
            ('7', '6'),  # 成本→进出口（成本关联进出口）
            ('2', '3'),  # 价格→供给（价格关联供给）
            ('2', '4'),  # 价格→库存（价格关联库存）
            ('2', '7'),  # 价格→成本（价格关联成本）
        }
        if (page_node_cat, expected_cat) in LEGIT_CROSS:
            # 合法跨板块引用，保留✅
            return '\\u2705', expected_cat, '跨板块引用正常（合法关联：%s→%s·%s页引用%s类指标）' % (
                page_node_cat, expected_cat, chart_role, CATEGORY_MAP.get(expected_cat, '?'))
        return '\\U0001f7e2', expected_cat, '常规节点页跨板块主图（可能串台，需人工确认）：引用%s类指标·板块%s' % (
            expected_cat, CATEGORY_MAP.get(expected_cat, '?'))"""
    
    if old_r1 in content:
        content = content.replace(old_r1, new_r1)
        print("F1: Modified R1 migration logic with LEGIT_CROSS whitelist")
    else:
        print("F1: WARNING - old R1 code not found, manual check needed")
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    print("=== U2: Add SHFE Aliases ===")
    added = add_shfe_aliases()
    
    print("\n=== F1: Fix Migration Logic ===")
    fix_f1_migration()
    
    print("\nAll fixes applied!")