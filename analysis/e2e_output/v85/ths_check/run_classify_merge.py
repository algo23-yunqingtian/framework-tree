#!/usr/bin/env python3
"""
DSH-B_THS_MISS_CLASSIFY_AND_MERGE_TASK
Classify THS missing indicators into CAT_A/CAT_B/CAT_C,
merge with B2 missing indicators, and output draft for indicators_v1 entry.
"""
import json
import csv
import re
import os
from collections import defaultdict, Counter

# ── Paths ──
BASE = r'D:\DSH_WORK\github工作\analysis\e2e_output\v85\ths_check'
FW   = r'D:\DSH_WORK\github工作\framework-tree'
OUT  = BASE

# ── 1. Read THS missing indicator list ──
ths_missing = []  # list of {indicator_name, reference_count, sample_template_ids}
with open(os.path.join(BASE, 'ths_missing_indicator_list.csv'), 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ths_missing.append({
            'indicator_name': row['indicator_name'].strip(),
            'reference_count': int(row['reference_count']),
            'sample_template_ids': row['sample_template_ids'].split(';')
        })
print(f"[1] THS missing indicators loaded: {len(ths_missing)}")

# ── 2. Read indicators_v1.json ──
with open(os.path.join(FW, 'data', 'indicators_v1.json'), 'r', encoding='utf-8') as f:
    v1 = json.load(f)

# Build name index from indicators_v1
v1_names = set()
v1_id_to_name = {}
for key, val in v1.items():
    if isinstance(val, dict):
        name = val.get('name')
        if name:
            v1_names.add(name.strip())
            v1_id_to_name[key] = name.strip()
        # _cn_* cross-product entries
        entry = val.get('entry', {})
        if entry and isinstance(entry, dict):
            name = entry.get('name')
            if name:
                v1_names.add(name.strip())
                v1_id_to_name[key] = name.strip()

print(f"[2] indicators_v1 names loaded: {len(v1_names)}")

# ── 3. Read chart check result for ALL_MISS templates ──
all_miss_templates = []
with open(os.path.join(BASE, 'ths_chart_check_result.csv'), 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'].strip() == 'ALL_MISS':
            all_miss_templates.append(row)
print(f"[3] ALL_MISS templates loaded: {len(all_miss_templates)}")

# ── 4. Classification logic ──

# CAT_B patterns: statistical derivations
cat_b_patterns = [
    r'均值', r'标准差', r'分位', r'同比增速', r'环比增速',
    r'斜率', r'占比', r'占比（%', r'占比\(', r'分位（%',
    r'均值（', r'标准差（', r'分位（', r'分位\(',
    r'近\d+年同月', r'近\d+年同季', r'近\d+年同周', r'近\d+年同日',
    r'近\d+年同期', r'近\d+年同', r'近\d+年',
]

def is_cat_b(name):
    """Check if indicator is a derived/statistical indicator."""
    for pat in cat_b_patterns:
        if re.search(pat, name):
            return True
    return False

# CAT_C: check if entity exists in v1 under different name
# We build a set of core keywords and check if v1 has a name with matching core concepts
def extract_core_keywords(ths_name):
    """Extract core semantic keywords from THS indicator name."""
    # Remove unit suffixes
    core = re.sub(r'[（(][^）)]*[）)]', '', ths_name).strip()
    # Remove trailing chart suffix
    core = re.sub(r'时序图$', '', core).strip()
    return core

def find_v1_alias(ths_name, product=None):
    """Check if THS missing indicator has a product-matched alias in v1.
    
    Only returns alias if v1 name contains both the keyword AND the product name,
    OR if it's a cross-product concept confirmed to exist for that product.
    """
    core = extract_core_keywords(ths_name)
    
    # Direct exact match
    if core and core in v1_names:
        return core
    
    # Product-aware alias matching
    # Map THS keywords to what they should match in v1
    alias_checks = {
        '沪伦比': ['沪伦比', '沪伦比值'],
        '基差': ['基差'],
        '月差': ['月差'],
        '期限结构': ['期限结构'],
        '仓单注册量': ['仓单注册量'],
        '仓单量': ['仓单'],
        '仓单': ['仓单'],
        '库存天数': ['库存天数'],
        '持仓量': ['持仓量'],
        '成交量': ['成交量'],
        '多空持仓比': ['多空持仓比', '持仓比'],
        '现货升贴水': ['现货升贴水', '升贴水'],
        '冶炼利润': ['冶炼利润', '利润'],
        '加工费': ['加工费'],
        '电价': ['电价', '用电价格'],
        '汇率': ['汇率', 'USD/CNY'],
        '进口盈亏': ['进口盈亏'],
        '开工率': ['开工率'],
        '精炼产量': ['精炼产量', '精炼...产量'],
        '表观消费': ['表观消费'],
        '社会库存': ['社会库存'],
        '库存': ['库存'],
        'TC': ['TC', '加工费'],
    }
    
    # Product name mapping for cross-product checking
    product_names = {
        'NI': ['镍'], 'ZN': ['锌'], 'SN': ['锡'], 'SI': ['硅'],
        'LI': ['锂'], 'CU': ['铜'], 'AL': ['铝'],
        'PB': ['铅'], 'LC': ['碳酸锂', '锂'],
    }
    
    prod_keywords = product_names.get(product, [])
    
    for k, v1_keywords in alias_checks.items():
        if k in ths_name:
            # Check if v1 has a matching name for the same product
            for v1n in v1_names:
                if any(vk in v1n for vk in v1_keywords):
                    # Check product match
                    if prod_keywords:
                        # Must match same product
                        if any(pk in v1n for pk in prod_keywords):
                            return v1n
                    else:
                        # Cross-product concept, any product match is OK
                        return v1n
    
    return None

# Classify each indicator
classified = []
for ind in ths_missing:
    name = ind['indicator_name']
    ref_count = ind['reference_count']
    template_ids = ind['sample_template_ids']
    
    # Extract product from first template_id
    product = None
    if template_ids:
        parts = template_ids[0].split('-')
        if len(parts) >= 2:
            product = parts[1]
    
    if is_cat_b(name):
        cat = 'CAT_B_DERIVED'
        alias_in_v1 = None
        note = '衍生计算指标（统计量），需计算引擎'
    else:
        alias = find_v1_alias(name, product)
        if alias:
            cat = 'CAT_C_ALIAS_EXIST'
            alias_in_v1 = alias
            note = f'实体存在于v1: {alias}'
        else:
            cat = 'CAT_A_RAW_MISS'
            alias_in_v1 = None
            note = '原始业务指标，库内确实无，需新增接入'
    
    classified.append({
        'indicator_name': name,
        'reference_count': ref_count,
        'sample_template_ids': ';'.join(template_ids),
        'category': cat,
        'alias_in_v1': alias_in_v1 or '',
        'note': note
    })

# Stats
cat_counts = Counter(c['category'] for c in classified)
print(f"[4] Classification done: {dict(cat_counts)}")

# ── 5. Output ths_missing_classify.csv ──
classify_path = os.path.join(OUT, 'ths_missing_classify.csv')
with open(classify_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['indicator_name', 'reference_count', 'sample_template_ids',
                     'category', 'alias_in_v1', 'note'])
    # Sort by reference_count descending
    classified.sort(key=lambda x: -x['reference_count'])
    for c in classified:
        writer.writerow([c['indicator_name'], c['reference_count'],
                        c['sample_template_ids'], c['category'],
                        c['alias_in_v1'], c['note']])
print(f"[5] Written: {classify_path}")

# ── 6. Output high_risk_all_miss_template.md ──
md_path = os.path.join(OUT, 'high_risk_all_miss_template.md')
with open(md_path, 'w', encoding='utf-8') as f:
    f.write('# ALL_MISS 高风险模板专项报告\n\n')
    f.write(f'- 报告时间: 自动生成\n')
    f.write(f'- ALL_MISS 模板数: **{len(all_miss_templates)}**\n')
    f.write(f'- 涵盖品种: CU, LI, NI, SI, ZN\n')
    f.write(f'- 模板图型: 全部为时序图（HERMES 已支持）\n')
    f.write(f'- 缺失原因: 全部指标在 indicators_v1 中均未找到匹配\n\n')
    f.write('---\n\n')
    f.write('## 分类说明\n\n')
    f.write('| 分类 | 含义 | 处置方式 |\n')
    f.write('|------|------|----------|\n')
    f.write('| CAT_A_RAW_MISS | 原始业务指标，库内确实无 | 需新增数据源接入 |\n')
    f.write('| CAT_B_DERIVED | 衍生计算指标（统计量） | 需计算引擎，不直接入库 |\n')
    f.write('| CAT_C_ALIAS_EXIST | 实体存在，仅命名差异 | 扩充别名映射即可 |\n\n')
    f.write('---\n\n')
    
    # Classify indicators for ALL_MISS templates
    all_miss_indicators = {}  # template_id -> list of classified indicators
    for tpl in all_miss_templates:
        tid = tpl['template_id'].strip()
        variety = tpl['variety'].strip()
        chart_title = tpl['chart_title'].strip()
        indicators_str = tpl['all_ths_indicators'].strip()
        indicators = [i.strip() for i in indicators_str.split(';') if i.strip()]
        
        # Classify each indicator
        ind_classified = []
        for ind_name in indicators:
            if is_cat_b(ind_name):
                ind_classified.append((ind_name, 'CAT_B_DERIVED'))
            else:
                alias = find_v1_alias(ind_name, variety)
                if alias:
                    ind_classified.append((ind_name, 'CAT_C_ALIAS_EXIST'))
                else:
                    ind_classified.append((ind_name, 'CAT_A_RAW_MISS'))
        
        all_miss_indicators[tid] = {
            'variety': variety,
            'chart_title': chart_title,
            'indicators': ind_classified
        }
    
    # Sort by variety
    sorted_tids = sorted(all_miss_indicators.keys(), key=lambda x: (all_miss_indicators[x]['variety'], x))
    
    for tid in sorted_tids:
        info = all_miss_indicators[tid]
        f.write(f'## {tid} ({info["variety"]})\n\n')
        f.write(f'- **图表标题**: {info["chart_title"]}\n')
        f.write(f'- **指标总数**: {len(info["indicators"])}\n\n')
        
        # Category breakdown
        cat_breakdown = Counter(c for _, c in info['indicators'])
        f.write('- **分类统计**:\n')
        for cat in ['CAT_A_RAW_MISS', 'CAT_B_DERIVED', 'CAT_C_ALIAS_EXIST']:
            cnt = cat_breakdown.get(cat, 0)
            if cnt > 0:
                f.write(f'  - {cat}: {cnt}\n')
        f.write('\n')
        
        # Indicator list
        f.write('| # | 指标名称 | 分类 |\n')
        f.write('|---|----------|------|\n')
        for i, (ind_name, cat) in enumerate(info['indicators'], 1):
            f.write(f'| {i} | {ind_name} | {cat} |\n')
        f.write('\n---\n\n')
    
    # Summary
    f.write('## 汇总\n\n')
    total_inds = sum(len(info['indicators']) for info in all_miss_indicators.values())
    total_a = sum(1 for info in all_miss_indicators.values() for _, c in info['indicators'] if c == 'CAT_A_RAW_MISS')
    total_b = sum(1 for info in all_miss_indicators.values() for _, c in info['indicators'] if c == 'CAT_B_DERIVED')
    total_c = sum(1 for info in all_miss_indicators.values() for _, c in info['indicators'] if c == 'CAT_C_ALIAS_EXIST')
    f.write(f'- 16 个 ALL_MISS 模板共含 **{total_inds}** 条指标\n')
    f.write(f'- CAT_A_RAW_MISS: {total_a} ({total_a/total_inds*100:.1f}%)\n')
    f.write(f'- CAT_B_DERIVED: {total_b} ({total_b/total_inds*100:.1f}%)\n')
    f.write(f'- CAT_C_ALIAS_EXIST: {total_c} ({total_c/total_inds*100:.1f}%)\n\n')
    f.write('### 按品种分布\n\n')
    f.write('| 品种 | 模板数 | 指标总数 |\n')
    f.write('|------|--------|----------|\n')
    var_count = defaultdict(list)
    for tid, info in all_miss_indicators.items():
        var_count[info['variety']].append(len(info['indicators']))
    for v in sorted(var_count.keys()):
        f.write(f'| {v} | {len(var_count[v])} | {sum(var_count[v])} |\n')
    
    f.write('\n### 缺失指标集中度分析\n\n')
    f.write('> 16 个 ALL_MISS 模板集中在以下板块:\n')
    f.write('> - **供给(3.x)**: NI-3.1.4, SI-3.1.1, ZN-3.1.1, ZN-3.1.2\n')
    f.write('> - **库存(4.x)**: CU-4.1, CU-4.2, CU-4.4, LI-4.1, ZN-4.4, ZN-4.5\n')
    f.write('> - **需求(5.x)**: SI-5.2, SI-5.3\n')
    f.write('> - **进出口(6.x)**: ZN-6.2\n')
    f.write('> - **成本利润(7.x)**: ZN-7.1, ZN-7.2\n')
    f.write('>\n')
    f.write('> **共性特征**: 这些板块的指标多为细分地区/细分工艺的原始业务数据（如「秘鲁锌矿产量」、「印尼镍矿产量」），\n')
    f.write('> indicators_v1 中尚无对应的分国别/分区域细粒度指标。\n')

print(f"[6] Written: {md_path}")

# ── 7. CAT_A indicators for merge ──
cat_a_indicators = [c for c in classified if c['category'] == 'CAT_A_RAW_MISS']
cat_a_names = set(c['indicator_name'] for c in cat_a_indicators)
print(f"[7] CAT_A indicators: {len(cat_a_indicators)}")

# ── 8. B2 missing preview (not available, reconstruct from known B2 indicators) ──
# The prior task DSH-B_B2_MISSING_INDICATOR_PREP_TASK outputs were not found.
# We reconstruct the 23 B2 indicators from known context.
# B2 indicators are typically related to PDF weekly report analysis.
# Since we can't find the file, we'll note this gap and proceed.

b2_missing_file = None
# Try multiple possible paths
for candidate in [
    os.path.join(BASE, 'b2_missing_preview.csv'),
    os.path.join(r'D:\DSH_WORK\github工作\analysis\e2e_output\v85\pdf_extract', 'b2_missing_preview.csv'),
    os.path.join(FW, 'analysis', 'pdf_extract', 'b2_missing_preview.csv'),
]:
    if os.path.exists(candidate):
        b2_missing_file = candidate
        break

b2_indicators = []
b2_note = ''

if b2_missing_file:
    with open(b2_missing_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            b2_indicators.append(row)
    b2_note = f'B2 file found at: {b2_missing_file}, {len(b2_indicators)} indicators'
else:
    b2_note = 'B2_MISSING_FILE_NOT_FOUND: b2_missing_preview.csv not found in repository. Prior task DSH-B_B2_MISSING_INDICATOR_PREP_TASK outputs missing. Merge contains only THS CAT_A raw missing indicators.'
    print(f"[8] B2 file NOT FOUND. Gap noted.")

# ── 9. Merge CAT_A with B2, deduplicate ──
merged = []
seen = set()

for c in cat_a_indicators:
    name = c['indicator_name']
    if name not in seen:
        seen.add(name)
        merged.append({
            'indicator_name': name,
            'reference_count': c['reference_count'],
            'sample_template_ids': c['sample_template_ids'],
            'source': '同花顺模板',
            'category': 'CAT_A_RAW_MISS'
        })

for b2 in b2_indicators:
    name = b2.get('indicator_name', '').strip()
    if name and name not in seen:
        seen.add(name)
        merged.append({
            'indicator_name': name,
            'reference_count': int(b2.get('reference_count', 0) or 0),
            'sample_template_ids': b2.get('sample_template_ids', b2.get('node_id', '')),
            'source': 'PDF周报',
            'category': 'CAT_A_RAW_MISS'
        })
    elif name in seen:
        # Update source to mark as both
        for m in merged:
            if m['indicator_name'] == name:
                if '同花顺模板' in m['source'] and 'PDF周报' not in m['source']:
                    m['source'] = '两者均出现'
                break

print(f"[9] Merged total (deduplicated): {len(merged)}")

# ── 10. Output merged_total_missing_preview.csv ──
merged_csv = os.path.join(OUT, 'merged_total_missing_preview.csv')
with open(merged_csv, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['indicator_name', 'reference_count', 'sample_template_ids',
                     'source', 'category'])
    merged.sort(key=lambda x: (-x['reference_count'], x['indicator_name']))
    for m in merged:
        writer.writerow([m['indicator_name'], m['reference_count'],
                        m['sample_template_ids'], m['source'], m['category']])
print(f"[10] Written: {merged_csv}")

# ── 11. Output merged_total_missing_draft.md ──
draft_md = os.path.join(OUT, 'merged_total_missing_draft.md')
with open(draft_md, 'w', encoding='utf-8') as f:
    f.write('# indicators_v1 录入草稿\n\n')
    f.write(f'- 草稿时间: 自动生成\n')
    f.write(f'- 合并来源: 同花顺 CAT_A 原始缺失指标 + PDF周报 B2 待补指标\n')
    f.write(f'- 合并后去重总数: **{len(merged)}**\n\n')
    
    if b2_note.startswith('B2_MISSING'):
        f.write(f'> {b2_note}\n\n')
    
    f.write('---\n\n')
    
    # Stats by source
    source_counts = Counter(m['source'] for m in merged)
    f.write('## 来源统计\n\n')
    f.write('| 来源 | 数量 | 占比 |\n')
    f.write('|------|------|------|\n')
    for src, cnt in source_counts.most_common():
        f.write(f'| {src} | {cnt} | {cnt/len(merged)*100:.1f}% |\n')
    f.write('\n')
    
    # Stats by variety
    f.write('## 按品种统计\n\n')
    var_counter = Counter()
    for m in merged:
        for tid in m['sample_template_ids'].split(';'):
            parts = tid.split('-')
            if len(parts) >= 2:
                var_counter[parts[1]] += 1
    f.write('| 品种 | 指标数 |\n')
    f.write('|------|--------|\n')
    for v, cnt in var_counter.most_common():
        f.write(f'| {v} | {cnt} |\n')
    f.write('\n')
    
    f.write('---\n\n')
    f.write('## 录入草稿清单\n\n')
    f.write('> 以下指标建议作为 indicators_v1 新增条目。\n')
    f.write('> 字段说明:\n')
    f.write('> - `name`: 指标中文名（取自同花顺原始名称）\n')
    f.write('> - `unit`: 单位（从指标名中提取）\n')
    f.write('> - `freq`: 建议频率（需根据数据源确认）\n')
    f.write('> - `source`: 来源标注\n')
    f.write('> - `ref_count`: 同花顺引用次数\n\n')
    
    f.write('```json\n')
    f.write('{\n')
    f.write('  "indicators": [\n')
    for i, m in enumerate(merged):
        # Extract unit from name
        unit = ''
        unit_match = re.search(r'[（(]([^）)]+)[）)]', m['indicator_name'])
        if unit_match:
            unit = unit_match.group(1)
        
        # Guess frequency
        freq = 'daily'  # default
        if '月' in m['indicator_name'] or '万吨' in m['indicator_name']:
            freq = 'monthly'
        if '周' in m['indicator_name']:
            freq = 'weekly'
        
        entry = {
            'name': m['indicator_name'],
            'unit': unit,
            'freq': freq,
            'source': m['source'],
            'ref_count': m['reference_count'],
            'sample_templates': m['sample_template_ids']
        }
        comma = ',' if i < len(merged) - 1 else ''
        f.write(json.dumps(entry, ensure_ascii=False, indent=4))
        f.write(comma)
        f.write('\n')
    f.write('  ]\n')
    f.write('}\n')
    f.write('```\n\n')
    
    f.write('---\n\n')
    f.write('## 注意事项\n\n')
    f.write('1. **所有指标均需人工审核**: 以上为自动生成的草稿，录入前需人工确认指标名称、单位、频率的准确性。\n')
    f.write('2. **不修改 indicators_v1**: 本草稿仅供参考，未对 indicators_v1.json 做任何修改。\n')
    f.write('3. **CAT_B 衍生指标不入库**: 均值、标准差、分位等统计指标应通过计算引擎生成，不建议直接作为 indicators_v1 条目。\n')
    f.write('4. **CAT_C 别名扩充**: 实体已存在的指标（如「沪伦比」可能已有对应的 SHFE/LME 比价条目），只需在别名映射中扩充，无需新增时序数据。\n')
    f.write('5. **数据源对接**: 新增指标需确认数据源（知几 API / 海关 / 交易所 / 第三方），并编写对应的 fetch 脚本。\n')
    f.write('6. **去重原则**: 合并时已对指标名称做精确去重，但语义重复（如同一指标的不同表述）需人工识别。\n\n')
    
    f.write('---\n\n')
    f.write('## 产出文件索引\n\n')
    f.write('| 文件 | 说明 |\n')
    f.write('|------|------|\n')
    f.write(f'| `ths_missing_classify.csv` | THS 缺失指标分类明细（{len(classified)} 条） |\n')
    f.write(f'| `high_risk_all_miss_template.md` | 16 个 ALL_MISS 模板专项报告 |\n')
    f.write(f'| `merged_total_missing_preview.csv` | PDF周报+同花顺合并去重待补清单（{len(merged)} 条） |\n')
    f.write(f'| `merged_total_missing_draft.md` | 本文件：录入草稿 |\n')

print(f"[11] Written: {draft_md}")

# ── 12. Final summary ──
print(f"\n{'='*60}")
print(f"DSH-B_THS_MISS_CLASSIFY_AND_MERGE_TASK 完成")
print(f"{'='*60}")
print(f"THS 缺失指标分类:")
print(f"  CAT_A_RAW_MISS: {cat_counts.get('CAT_A_RAW_MISS', 0)}")
print(f"  CAT_B_DERIVED:  {cat_counts.get('CAT_B_DERIVED', 0)}")
print(f"  CAT_C_ALIAS_EXIST: {cat_counts.get('CAT_C_ALIAS_EXIST', 0)}")
print(f"合并后待补清单: {len(merged)}")
if b2_note.startswith('⚠️'):
    print(f"B2 文件状态: {b2_note}")
print(f"输出目录: {OUT}")
print(f"  - ths_missing_classify.csv")
print(f"  - high_risk_all_miss_template.md")
print(f"  - merged_total_missing_preview.csv")
print(f"  - merged_total_missing_draft.md")
