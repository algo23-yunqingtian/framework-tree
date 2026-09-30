#!/usr/bin/env python3
"""
DSH-B_REBUILD_AND_MERGE_B2_THS_TASK
=====================================
Rebuild B2 missing indicators from PDF weekly report source,
merge with THS CAT_A_RAW_MISS, deduplicate, tag sources,
and output 3 deliverables.

Inputs:
  1. pdf_extract/missing_classify.csv    (B2 source from prior task)
  2. ths_check/ths_missing_classify.csv  (THS classification)
  3. indicators_v1.json                  (master indicator library)

Outputs (to ths_check/):
  1. b2_missing_preview_rebuild.csv      (rebuilt PDF weekly missing list)
  2. full_merged_A_raw_missing.csv       (merged dedup total)
  3. full_merged_A_raw_draft.md          (indicators_v1 entry draft)

Constraints: read-only on inputs, no zhiji API, no v1 modification.
"""
import json
import csv
import re
import os
from collections import Counter, defaultdict

# ── Paths ──────────────────────────────────────────────────────────────
BASE = r'D:\DSH_WORK\github工作\analysis\e2e_output\v85\ths_check'
FW_DSH     = r'D:\DSH_WORK\github工作'
FW_FT      = r'D:\DSH_WORK\framework-tree'
PDF_EXTRACT = os.path.join(FW_FT, 'analysis', 'e2e_output', 'v85', 'pdf_extract')
B2_SRC      = os.path.join(PDF_EXTRACT, 'missing_classify.csv')
V1_PATH     = os.path.join(FW_FT, 'data', 'indicators_v1.json')
THS_CLASSIFY = os.path.join(BASE, 'ths_missing_classify.csv')

OUT_DIR = BASE

# ══════════════════════════════════════════════════════════════════════
# STEP 1: Read B2 source — missing_classify.csv
# ══════════════════════════════════════════════════════════════════════
print("[1] Reading B2 source: missing_classify.csv ...")
b2_entries = []
with open(B2_SRC, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        b2_entries.append(row)
print(f"    Total rows: {len(b2_entries)}")

# Filter B2_指标名无库元数据 (库缺失 — real missing indicators)
# Note: classification is in root_cause column, not branch_label
b2_missing_rows = [r for r in b2_entries
                   if 'B2_指标名无库元数据' in r.get('root_cause', '')]
b1_noise_rows   = [r for r in b2_entries
                   if 'B1_噪声文本' in r.get('root_cause', '')]
print(f"    B2 (库缺失) rows: {len(b2_missing_rows)}")
print(f"    B1 (噪声文本) rows: {len(b1_noise_rows)}")

# Extract unique chart_titles from B2 entries (chart_title = indicator name)
b2_title_info = {}
for r in b2_missing_rows:
    title = r['chart_title'].strip()
    if not title:
        continue
    if title not in b2_title_info:
        b2_title_info[title] = {
            'source_files': set(),
            'pages': set(),
            'chart_ids': set(),
            'missing_texts': [],
            'occurrence_count': 0
        }
    b2_title_info[title]['source_files'].add(r['source_file'].strip())
    b2_title_info[title]['pages'].add(r['page_num'].strip())
    b2_title_info[title]['chart_ids'].add(r['chart_local_id'].strip())
    mt = r['missing_text'].strip()
    if mt and mt not in b2_title_info[title]['missing_texts']:
        b2_title_info[title]['missing_texts'].append(mt)
    b2_title_info[title]['occurrence_count'] += 1

print(f"    Unique B2 chart_titles: {len(b2_title_info)}")

# ══════════════════════════════════════════════════════════════════════
# STEP 2: Clean B2 titles — filter noise, keep valid indicators
# ══════════════════════════════════════════════════════════════════════
print("[2] Cleaning B2 titles ...")

def is_valid_b2_title(title):
    """
    Heuristic filter for valid business indicator names from B2 chart_titles.
    Returns (is_valid, reason) tuple.
    """
    t = title.strip()
    
    # Rule 1: Too short to be a meaningful indicator name
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', t))
    total_len = len(t)
    if chinese_chars < 2 and total_len < 4:
        return False, "too_short"
    
    # Rule 2: Pure English labels (SMM:, SPX, Risk, Curve, Cash, etc.)
    if re.match(r'^[A-Za-z\s:]+$', t):
        return False, "english_label"
    
    # Rule 3: Known noise chart descriptions
    noise_terms = {
        'SMM:', 'SMM', 'LME', 'SPX', '四金属', 'Curve', 'Cash', 'Risk',
        'Reversal', 'India', 'vs', '连续合约', '连一', '连二', '连三',
        '连四', '连五', '汇总1', '吨吨', 'GWh', 'Gwh', 'GW', '万辆',
        '万吨', '元/吨', '%', '天万吨', 'MWH', 'MWHMWH',
        '平均价:', '日度', '周度', '月差（近月-远月',
        '删除图数', '具体执行', '2', '4', '6', '8', '9',
        'AL盘面结构', '盘面结构', '价格走势',
    }
    if t in noise_terms:
        return False, "noise_term"
    
    # Rule 4: Chart type descriptions (not specific indicators)
    chart_desc_patterns = [
        r'^AL盘面结构$',
        r'^四金属$',
        r'^.*盘面结构$',
        r'^.*价格走势$',
        r'^.*月间结构$',
        r'^.*走势图$',
        r'^.*滚动相关图$',
        r'^.*比值对比$',
        r'^.*累计同比$',
        r'^.*变化$',
        r'^.*消费$',   # too generic if alone
    ]
    # But only reject if it's ONLY a description, not a specific indicator
    # (e.g. "铝终端消费" is valid, "四金属" is not)
    
    # Rule 5: Pure punctuation / symbols
    if re.match(r'^[\W_]+$', t):
        return False, "punctuation_only"
    
    # Rule 6: Looks like a data source label (SMM:xxx, 中国:xxx is actually valid)
    # Only reject if it's JUST the label prefix
    if t in ('SMM:', 'SMM:', 'LME:', 'SHFE:'):
        return False, "label_prefix"
    
    # Rule 7: Pure unit labels that appear as chart_titles
    unit_patterns = [
        r'^元/吨元/吨$', r'^美元/湿吨$', r'^美元/磅$',
        r'^%/\s*金属吨100$', r'^元/度吨$', r'^元/50基吨$',
        r'^万吨%$', r'^万金属吨$', r'^万万吨吨万吨$',
        r'^万元吨$', r'^万吨万吨$', r'^吨吨$',
        r'^万万吨吨$', r'^万吨9$',
    ]
    for pat in unit_patterns:
        if re.match(pat, t):
            return False, "unit_label"
    
    # Rule 8: Chart series labels (not indicator names)
    series_labels = {
        '总消费', '净出口', '房屋建筑', '家电', '电力',
        '交通运输', '当月值', '累计同比（截至6月）',
        '样本白电总用锡Yoy', 'Yoy', '空调用锡量累计',
        '60日滚动相关图：锡', '锡=AI的实物，', 'SPX',
    }
    if t in series_labels:
        return False, "series_label"
    
    # Rule 9: Too generic / ambiguous (single concept without qualifier)
    generic_alone = {
        '铝终端消费',   # valid actually - it's an indicator
        '亏损企业比例', # valid
        '铝水比例',     # valid
    }
    # Don't reject these - they are valid
    
    return True, "valid"

# Apply cleaning
b2_clean = {}
b2_rejected = {}
for title, info in b2_title_info.items():
    is_valid, reason = is_valid_b2_title(title)
    if is_valid:
        b2_clean[title] = info
    else:
        b2_rejected[title] = {'reason': reason, **info}

print(f"    Valid B2 titles: {len(b2_clean)}")
print(f"    Rejected B2 titles: {len(b2_rejected)}")

# Show rejected titles for transparency
if b2_rejected:
    print(f"    Rejected (first 20):")
    for t, info in list(b2_rejected.items())[:20]:
        print(f"      '{t}' -> {info['reason']}")

# ══════════════════════════════════════════════════════════════════════
# STEP 3: Read indicators_v1.json — build name index
# ══════════════════════════════════════════════════════════════════════
print("[3] Reading indicators_v1.json ...")
with open(V1_PATH, 'r', encoding='utf-8') as f:
    v1 = json.load(f)

v1_names = set()
for key, val in v1.items():
    if isinstance(val, dict):
        name = val.get('name')
        if name:
            v1_names.add(name.strip())
        entry = val.get('entry', {})
        if entry and isinstance(entry, dict):
            name = entry.get('name')
            if name:
                v1_names.add(name.strip())

print(f"    V1 indicator names: {len(v1_names)}")

# ══════════════════════════════════════════════════════════════════════
# STEP 4: Filter B2 titles against v1 — keep only missing ones
# ══════════════════════════════════════════════════════════════════════
print("[4] Filtering B2 titles against v1 ...")

def normalize_for_match(name):
    """Normalize an indicator name for cross-source matching."""
    n = name.strip()
    # Remove unit suffixes: （xxx）or (xxx)
    n = re.sub(r'[（(][^）)]*[）)]', '', n)
    # Remove whitespace variations
    n = re.sub(r'\s+', '', n)
    # Remove trailing punctuation
    n = n.rstrip('：:,，;；。.')
    return n

# Check each cleaned B2 title against v1
b2_valid_missing = {}
b2_in_v1 = {}
for title, info in b2_clean.items():
    norm_title = normalize_for_match(title)
    # Exact match check
    if norm_title in v1_names or title in v1_names:
        b2_in_v1[title] = info
    else:
        # Check if any v1 name contains this as substring (fuzzy)
        # Only check for longer names (>= 5 chars) to avoid false positives
        fuzzy_match = False
        if len(norm_title) >= 5:
            for v1n in v1_names:
                v1_norm = normalize_for_match(v1n)
                if norm_title in v1_norm or v1_norm in norm_title:
                    fuzzy_match = True
                    break
        if not fuzzy_match:
            b2_valid_missing[title] = info

print(f"    B2 titles already in v1: {len(b2_in_v1)}")
print(f"    B2 valid missing (NOT in v1): {len(b2_valid_missing)}")

if b2_in_v1:
    print(f"    In-v1 B2 titles (first 10):")
    for t in list(b2_in_v1.keys())[:10]:
        print(f"      '{t}'")

# ══════════════════════════════════════════════════════════════════════
# STEP 5: Read THS CAT_A_RAW_MISS
# ══════════════════════════════════════════════════════════════════════
print("[5] Reading THS CAT_A_RAW_MISS ...")
ths_cat_a = {}
with open(THS_CLASSIFY, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('category', '').strip() == 'CAT_A_RAW_MISS':
            name = row['indicator_name'].strip()
            if name:
                ths_cat_a[name] = {
                    'reference_count': int(row['reference_count']),
                    'sample_template_ids': row['sample_template_ids'],
                }

print(f"    THS CAT_A_RAW_MISS indicators: {len(ths_cat_a)}")

# ══════════════════════════════════════════════════════════════════════
# STEP 6: Merge B2 + THS, deduplicate, tag sources
# ══════════════════════════════════════════════════════════════════════
print("[6] Merging B2 + THS, deduplicating, tagging sources ...")

# Build lookup: normalized_name -> {source, original_name, ref_count, templates}
merged = {}

# First, add THS CAT_A indicators
for name, info in ths_cat_a.items():
    norm = normalize_for_match(name)
    if norm not in merged:
        merged[norm] = {
            'display_name': name,
            'sources': set(),
            'reference_count': info['reference_count'],
            'sample_template_ids': info['sample_template_ids'],
            'category': 'CAT_A_RAW_MISS',
        }
    merged[norm]['sources'].add('THS')

# Then, add B2 valid missing indicators
for name, info in b2_valid_missing.items():
    norm = normalize_for_match(name)
    if norm in merged:
        # Already exists from THS — add B2 source
        merged[norm]['sources'].add('B2')
    else:
        merged[norm] = {
            'display_name': name,
            'sources': {'B2'},
            'reference_count': 0,
            'sample_template_ids': '',
            'category': 'CAT_A_RAW_MISS',
        }

# Tag sources
source_counts = Counter()
merged_list = []
for norm, info in sorted(merged.items(), key=lambda x: -x[1]['reference_count']):
    src = info['sources']
    if src == {'B2'}:
        tag = '仅PDF周报'
    elif src == {'THS'}:
        tag = '仅同花顺'
    else:
        tag = '两者均出现'
    source_counts[tag] += 1
    
    entry = {
        'indicator_name': info['display_name'],
        'reference_count': info['reference_count'],
        'sample_template_ids': info['sample_template_ids'],
        'source_tag': tag,
        'category': info['category'],
    }
    merged_list.append(entry)

print(f"    Total merged: {len(merged_list)}")
for tag, cnt in source_counts.most_common():
    print(f"      {tag}: {cnt}")

# ══════════════════════════════════════════════════════════════════════
# STEP 7: Output b2_missing_preview_rebuild.csv
# ══════════════════════════════════════════════════════════════════════
print("[7] Writing b2_missing_preview_rebuild.csv ...")

b2_csv_path = os.path.join(OUT_DIR, 'b2_missing_preview_rebuild.csv')
with open(b2_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'indicator_name', 'source_file', 'page_num', 'chart_local_id',
        'missing_texts', 'occurrence_count', 'exists_in_v1'
    ])
    
    # Valid missing (not in v1)
    for title, info in sorted(b2_valid_missing.items(),
                               key=lambda x: -x[1]['occurrence_count']):
        writer.writerow([
            title,
            ';'.join(sorted(info['source_files'])),
            ';'.join(sorted(info['pages'])),
            ';'.join(sorted(info['chart_ids'])),
            ' | '.join(info['missing_texts'][:3]),
            info['occurrence_count'],
            'NO'
        ])
    
    # Already in v1 (for completeness)
    for title, info in sorted(b2_in_v1.items()):
        writer.writerow([
            title,
            ';'.join(sorted(info['source_files'])),
            ';'.join(sorted(info['pages'])),
            ';'.join(sorted(info['chart_ids'])),
            ' | '.join(info['missing_texts'][:3]),
            info['occurrence_count'],
            'YES'
        ])
    
    # Rejected noise (for transparency)
    for title, info in sorted(b2_rejected.items()):
        writer.writerow([
            title,
            ';'.join(sorted(info['source_files'])),
            ';'.join(sorted(info['pages'])),
            ';'.join(sorted(info['chart_ids'])),
            ' | '.join(info.get('missing_texts', [])[:3]),
            info['occurrence_count'],
            f'REJECTED:{info["reason"]}'
        ])

print(f"    Written: {b2_csv_path}")
print(f"    Rows: valid_missing={len(b2_valid_missing)}, in_v1={len(b2_in_v1)}, rejected={len(b2_rejected)}")

# ══════════════════════════════════════════════════════════════════════
# STEP 8: Output full_merged_A_raw_missing.csv
# ══════════════════════════════════════════════════════════════════════
print("[8] Writing full_merged_A_raw_missing.csv ...")

merged_csv_path = os.path.join(OUT_DIR, 'full_merged_A_raw_missing.csv')
with open(merged_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'indicator_name', 'reference_count', 'sample_template_ids',
        'source_tag', 'category'
    ])
    for entry in merged_list:
        writer.writerow([
            entry['indicator_name'],
            entry['reference_count'],
            entry['sample_template_ids'],
            entry['source_tag'],
            entry['category']
        ])

print(f"    Written: {merged_csv_path}")
print(f"    Rows: {len(merged_list)}")

# ══════════════════════════════════════════════════════════════════════
# STEP 9: Output full_merged_A_raw_draft.md
# ══════════════════════════════════════════════════════════════════════
print("[9] Writing full_merged_A_raw_draft.md ...")

draft_md_path = os.path.join(OUT_DIR, 'full_merged_A_raw_draft.md')

# Count by source
b2_only = sum(1 for e in merged_list if e['source_tag'] == '仅PDF周报')
ths_only = sum(1 for e in merged_list if e['source_tag'] == '仅同花顺')
both = sum(1 for e in merged_list if e['source_tag'] == '两者均出现')

# Count by product (from template IDs or name)
product_counter = Counter()
for entry in merged_list:
    name = entry['indicator_name']
    templates = entry['sample_template_ids']
    # Try to extract product from template IDs
    if templates:
        products = set()
        for tid in templates.split(';'):
            m = re.match(r'THS-([A-Z]+)', tid.strip())
            if m:
                products.add(m.group(1))
        for p in products:
            product_counter[p] += 1
    # If no template IDs, try to infer from name
    if not templates or not products:
        if '镍' in name:
            product_counter['NI'] += 1
        elif '锌' in name:
            product_counter['ZN'] += 1
        elif '锡' in name:
            product_counter['SN'] += 1
        elif '铝' in name:
            product_counter['AL'] += 1
        elif '锂' in name:
            product_counter['LI'] += 1
        elif '铜' in name:
            product_counter['CU'] += 1
        elif '硅' in name:
            product_counter['SI'] += 1

# Reference count distribution
ref_counts = [e['reference_count'] for e in merged_list if e['reference_count'] > 0]
ref_count_dist = Counter()
for rc in ref_counts:
    if rc >= 10:
        ref_count_dist['10+'] += 1
    elif rc >= 5:
        ref_count_dist['5-9'] += 1
    elif rc >= 2:
        ref_count_dist['2-4'] += 1
    else:
        ref_count_dist['1'] += 1

# B2 source file distribution
b2_src_files = Counter()
for info in b2_valid_missing.values():
    for sf in info['source_files']:
        b2_src_files[sf] += 1

# Generate draft entries
draft_entries = []
for entry in merged_list:
    name = entry['indicator_name']
    # Infer unit from name
    unit = ''
    if '万吨' in name:
        unit = '万吨'
    elif '元/吨' in name:
        unit = '元/吨'
    elif '美元/吨' in name:
        unit = '美元/吨'
    elif '美元/湿吨' in name:
        unit = '美元/湿吨'
    elif '美元/磅' in name:
        unit = '美元/磅'
    elif '%' in name or '百分比' in name:
        unit = '%'
    elif '天' in name:
        unit = '天'
    elif '万元' in name:
        unit = '万元'
    elif '亿元' in name:
        unit = '亿元'
    elif '万辆' in name:
        unit = '万辆'
    elif '手' in name:
        unit = '手'
    elif 'LCE' in name:
        unit = '万吨LCE'
    elif '吨' in name:
        unit = '吨'
    
    # Infer frequency
    if '日' in name or '日度' in name:
        freq = '日度'
    elif '周' in name:
        freq = '周度'
    elif '月' in name:
        freq = '月度'
    elif '季' in name:
        freq = '季度'
    elif '年' in name:
        freq = '年度'
    else:
        freq = '待确认'
    
    # Source
    if entry['source_tag'] == '两者均出现':
        source = '同花顺问财+PDF周报'
    elif entry['source_tag'] == '仅PDF周报':
        source = 'PDF周报'
    else:
        source = '同花顺问财'
    
    draft_entry = {
        'name': name,
        'unit': unit if unit else '待确认',
        'freq': freq,
        'source': source,
        'ref_count': entry['reference_count'],
        'note': ''
    }
    draft_entries.append(draft_entry)

# Write markdown draft
with open(draft_md_path, 'w', encoding='utf-8') as f:
    f.write('# indicators_v1 待补指标录入草稿\n\n')
    f.write(f'> **任务**: DSH-B_REBUILD_AND_MERGE_B2_THS_TASK  \n')
    f.write(f'> **生成时间**: 自动重建  \n')
    f.write(f'> **约束**: 仅草稿，不写入指标库  \n\n')
    
    # ── Executive Summary ──
    f.write('## 总览\n\n')
    f.write(f'| 指标 | 数量 |\n')
    f.write(f'|------|------|\n')
    f.write(f'| B2 重建有效待补 (仅PDF周报) | {b2_only} |\n')
    f.write(f'| THS CAT_A_RAW_MISS (仅同花顺) | {ths_only} |\n')
    f.write(f'| 两者均出现 | {both} |\n')
    f.write(f'| **合并去重总计** | **{len(merged_list)}** |\n\n')
    
    # Source breakdown
    f.write('### 来源分布\n\n')
    f.write('| 来源标记 | 数量 | 占比 |\n')
    f.write('|----------|------|------|\n')
    for tag, cnt in source_counts.most_common():
        pct = cnt / len(merged_list) * 100
        f.write(f'| {tag} | {cnt} | {pct:.1f}% |\n')
    f.write('\n')
    
    # B2 source file distribution
    f.write('### B2 来源文件分布\n\n')
    f.write('| PDF周报文件 | 有效指标数 |\n')
    f.write('|-------------|-----------|\n')
    for sf, cnt in b2_src_files.most_common():
        f.write(f'| {sf} | {cnt} |\n')
    f.write('\n')
    
    # Product distribution
    f.write('### 品种分布\n\n')
    f.write('| 品种代码 | 指标数 |\n')
    f.write('|----------|--------|\n')
    for prod, cnt in product_counter.most_common():
        f.write(f'| {prod} | {cnt} |\n')
    f.write('\n')
    
    # Reference count distribution
    f.write('### 引用次数分布 (THS)\n\n')
    f.write('| 引用次数 | 指标数 |\n')
    f.write('|----------|--------|\n')
    for range_label in ['10+', '5-9', '2-4', '1']:
        cnt = ref_count_dist.get(range_label, 0)
        f.write(f'| {range_label} | {cnt} |\n')
    f.write('\n')
    
    # ── B2 Rebuild Details ──
    f.write('---\n\n')
    f.write('## B2 重建详情\n\n')
    f.write(f'> 原始 B2 条目: {len(b2_missing_rows)} 行\n')
    f.write(f'> 唯一 chart_title: {len(b2_title_info)}\n')
    f.write(f'> 清洗后有效: {len(b2_clean)}\n')
    f.write(f'> 库内已存在: {len(b2_in_v1)}\n')
    f.write(f'> **有效待补 (v1 缺失): {len(b2_valid_missing)}**\n\n')
    
    f.write('### 有效待补指标列表\n\n')
    f.write('| # | 指标名 | 来源PDF | 出现次数 | 同花顺交叉 | \n')
    f.write('|---|--------|---------|----------|------------|\n')
    ths_norm_set = set()
    for name in ths_cat_a:
        ths_norm_set.add(normalize_for_match(name))
    
    for i, (title, info) in enumerate(sorted(b2_valid_missing.items(),
                                               key=lambda x: -x[1]['occurrence_count']), 1):
        norm = normalize_for_match(title)
        in_ths = '是' if norm in ths_norm_set else '否'
        src_files = ';'.join(sorted(info['source_files']))
        f.write(f'| {i} | {title} | {src_files} | {info["occurrence_count"]} | {in_ths} |\n')
    f.write('\n')
    
    f.write('### 已存在于 indicators_v1 的 B2 条目\n\n')
    if b2_in_v1:
        f.write('| 指标名 | 备注 |\n')
        f.write('|--------|------|\n')
        for title in sorted(b2_in_v1.keys()):
            f.write(f'| {title} | 库内已存在 |\n')
        f.write('\n')
    else:
        f.write('_无 — 所有清洗后的 B2 指标均不在 indicators_v1 中_\n\n')
    
    f.write('### 清洗排除的 B2 条目 (噪声)\n\n')
    if b2_rejected:
        f.write('| 指标名 | 排除原因 | 出现次数 |\n')
        f.write('|--------|----------|----------|\n')
        for title, info in sorted(b2_rejected.items(),
                                    key=lambda x: -x[1]['occurrence_count']):
            f.write(f'| {title} | {info["reason"]} | {info["occurrence_count"]} |\n')
        f.write('\n')
    
    # ── Full Merge Detail ──
    f.write('---\n\n')
    f.write('## 合并去重总清单\n\n')
    f.write(f'共 {len(merged_list)} 条指标 (PDF-B2 + THS-CAT_A 去重合并)\n\n')
    
    # Top 50 by reference count
    f.write('### 按引用次数排序 (Top 50)\n\n')
    f.write('| # | 指标名 | 引用次数 | 来源 | \n')
    f.write('|---|--------|----------|------|\n')
    for i, entry in enumerate(merged_list[:50], 1):
        f.write(f'| {i} | {entry["indicator_name"]} | {entry["reference_count"]} | {entry["source_tag"]} |\n')
    f.write('\n')
    
    # ── indicators_v1 Entry Draft ──
    f.write('---\n\n')
    f.write('## indicators_v1 录入草稿\n\n')
    f.write('> **注意**: 以下为草稿格式，未写入指标库。需人工审核后正式录入。\n\n')
    f.write('```json\n')
    
    for entry in draft_entries:
        f.write(json.dumps(entry, ensure_ascii=False))
        f.write(',\n')
    
    f.write(']\n')
    f.write('```\n\n')
    
    # ── Caveats ──
    f.write('---\n\n')
    f.write('## 注意事项\n\n')
    f.write('1. **B2 重建基于 heuristic 清洗**: 清洗规则基于启发式过滤，可能存在漏判或误判。建议人工审核被排除的条目。\n')
    f.write('2. **B2 与 THS 匹配使用归一化名称**: 去除单位后缀后比较，可能遗漏语义相同但命名差异较大的指标。\n')
    f.write('3. **fuzzy match 已应用**: 对长度 >=5 的 B2 标题，检查 v1 中是否有包含关系。仅保留无模糊匹配的条目。\n')
    f.write('4. **参考引用次数仅 THS 有效**: B2 独有指标的 reference_count=0 (PDF 无模板引用计数概念)。\n')
    f.write('5. **未调用 zhiji API**: 本脚本仅做文本分类与合并，不涉及任何 API 调用。\n')
    f.write('6. **未修改 indicators_v1**: 所有输入文件只读，输出仅为草稿。\n')
    f.write('7. **indicators_v1 版本**: 基于当前 indicators_v1.json (v3.50-p3fix) 的指标名集合。\n')
    
    # Data lineage
    f.write('\n## 数据血缘\n\n')
    f.write('| 输入 | 路径 | 状态 |\n')
    f.write('|------|------|------|\n')
    f.write(f'| B2 原始文件 | `{B2_SRC}` | 已读取 ({len(b2_entries)} 行) |\n')
    f.write(f'| THS 分类文件 | `{THS_CLASSIFY}` | 已读取 (CAT_A={len(ths_cat_a)}) |\n')
    f.write(f'| indicators_v1 | `{V1_PATH}` | 已读取 ({len(v1_names)} 指标名) |\n')
    
    # Output files
    f.write('\n## 输出产物\n\n')
    f.write('| 文件 | 说明 |\n')
    f.write('|------|------|\n')
    f.write(f'| `b2_missing_preview_rebuild.csv` | B2 重建待补清单 (含有效/已存在/排除) |\n')
    f.write(f'| `full_merged_A_raw_missing.csv` | PDF+同花顺合并去重总清单 |\n')
    f.write(f'| `full_merged_A_raw_draft.md` | 本文件 — indicators_v1 录入草稿 |\n')

print(f"    Written: {draft_md_path}")
print(f"    Draft entries: {len(draft_entries)}")

# ══════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DSH-B_REBUILD_AND_MERGE_B2_THS_TASK — COMPLETE")
print("=" * 70)
print(f"\nB2 Rebuild Summary:")
print(f"  Total B2 rows:        {len(b2_missing_rows)}")
print(f"  Unique chart_titles:  {len(b2_title_info)}")
print(f"  After cleaning:       {len(b2_clean)}")
print(f"  Already in v1:        {len(b2_in_v1)}")
print(f"  **Valid missing:      {len(b2_valid_missing)}**")
print(f"\nMerge Summary:")
print(f"  THS CAT_A_RAW_MISS:   {len(ths_cat_a)}")
print(f"  Merged total:         {len(merged_list)}")
for tag, cnt in source_counts.most_common():
    print(f"    {tag}: {cnt}")
print(f"\nOutput Files:")
print(f"  1. {b2_csv_path}")
print(f"  2. {merged_csv_path}")
print(f"  3. {draft_md_path}")
