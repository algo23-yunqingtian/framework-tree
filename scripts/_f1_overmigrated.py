#!/usr/bin/env python3
"""F1: Find over-migrated charts. Check which R1-migrated charts are actually legitimate cross-references."""
import json, os

base = r'D:\DSH_WORK\周报\framework-tree'
reg = json.load(open(os.path.join(base, 'data', 'chart_registry.json'), encoding='utf-8'))

# Logical cross-reference pairs (source_cat -> target_cat is legitimate)
LOGICAL_CROSS = {
    ('3', '6'): '进口是供给的一部分',
    ('3', '5'): '产量是需求的一部分',
    ('4', '2'): '库存参考价格',
    ('5', '2'): '需求参考价格',
    ('6', '3'): '进出口关联供给',
    ('6', '4'): '进出口关联库存',
    ('7', '3'): '成本关联供给/TC',
    ('7', '2'): '成本参考价格',
    ('7', '6'): '成本关联进出口',
    ('2', '3'): '价格关联供给',
    ('2', '4'): '价格关联库存',
    ('2', '7'): '价格关联成本',
}

r1_migrated = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='🟢' and '跨板块主图' in c.get('reason','')]
print(f"R1-migrated charts: {len(r1_migrated)}")

over_migrated = []
for c in r1_migrated:
    nc = c['node_cat']
    ec = c['expected_cat']
    if (nc, ec) in LOGICAL_CROSS:
        over_migrated.append(c)
        print(f"  OVER-MIGRATED?: {c['filename']} C{c['chart_seq']} node_cat={nc} expected_cat={ec} reason: {LOGICAL_CROSS[(nc,ec)]}")
        print(f"    Title: {c['chart_title'][:60]}")

print(f"\nTotal potential over-migrated: {len(over_migrated)}")

# Also check: which 🟢 charts are NOT R1-migrated (pre-existing)
pre_r1 = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='🟢' and '跨板块主图' not in c.get('reason','')]
print(f"Pre-R1 🟢 charts: {len(pre_r1)}")
# Check if any of these should be ⚪
for c in pre_r1[:5]:
    print(f"  {c['filename']} C{c['chart_seq']}: {c['reason'][:60]}")

# Check: regular ✅ cross-sector that might need 🟢
cross_ok = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='✅' and c['expected_cat'] and c['expected_cat'] != c['node_cat']]
print(f"\nRegular+✅+cross-sector: {len(cross_ok)}")
# Show role distribution
from collections import Counter
role_dist = Counter(c['role'] for c in cross_ok)
print(f"Role distribution: {dict(role_dist)}")

# Check: which regular pages have NO 🟢 charts (might be under-migrated)
regular_pages = set()
green_pages = set()
for c in reg['charts']:
    if c['page_type'] == 'regular':
        regular_pages.add(c['filename'])
        if c['verdict'] == '🟢':
            green_pages.add(c['filename'])
no_green = regular_pages - green_pages
print(f"\nRegular pages with no 🟢: {len(no_green)} / {len(regular_pages)}")
# Check if any of these pages have cross-sector main charts
for pg in sorted(no_green)[:10]:
    page_charts = [c for c in reg['charts'] if c['filename']==pg and c['page_type']=='regular']
    cross_mains = [c for c in page_charts if c['role']=='主图' and c['expected_cat'] and c['expected_cat'] != c['node_cat']]
    if cross_mains:
        print(f"  {pg}: has cross-sector main charts but no 🟢!")
        for c in cross_mains:
            print(f"    C{c['chart_seq']}: {c['chart_title'][:50]} verdict={c['verdict']}")