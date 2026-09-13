#!/usr/bin/env python3
"""F1: R1 migration analysis - find over-migrated and missing charts"""
import json, os

base = r'D:\DSH_WORK\周报\framework-tree'
reg = json.load(open(os.path.join(base, 'data', 'chart_registry.json'), encoding='utf-8'))

# Current verdict distribution
from collections import Counter
pt_vc = Counter()
for c in reg['charts']:
    pt_vc[(c['page_type'], c['verdict'])] += 1

print("=== Current Verdict Distribution ===")
for (pt, v), n in sorted(pt_vc.items()):
    print(f"  {pt:20s} {v}: {n}")
total_green = sum(n for (pt, v), n in pt_vc.items() if v == '🟢')
print(f"\nTotal 🟢: {total_green}")
print(f"Target 🟢: 162")
print(f"Gap: {162 - total_green}")

# Find all 🟢 on regular pages with cross-sector main chart reason
r1_migrated = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='🟢' and '跨板块主图' in c.get('reason','')]
print(f"\nR1-migrated charts (regular+🟢+跨板块主图): {len(r1_migrated)}")

# Find 🟢 on regular pages WITHOUT cross-sector main chart (these were 🟢 before R1)
pre_r1_green = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='🟢' and '跨板块主图' not in c.get('reason','')]
print(f"Pre-R1 🟢 charts (regular+🟢 without 跨板块主图): {len(pre_r1_green)}")

# Check for charts that might be over-migrated
# Over-migrated = regular page, 🟢, but the cross-sector reference is actually legitimate design intent
# These would be charts where the indicator genuinely belongs to the other category
# and the chart is on a page that legitimately references it
print("\n=== Checking for over-migrated charts ===")
over_migrated = []
for c in r1_migrated:
    # Check if the chart's expected_cat matches the node_cat (shouldn't happen if cross-sector)
    if c['expected_cat'] and c['expected_cat'] == c['node_cat']:
        over_migrated.append(c)
        print(f"  SAME CAT (over-migrated?): {c['filename']} C{c['chart_seq']}: expected_cat={c['expected_cat']} node_cat={c['node_cat']}")

# Also check: charts on regular pages that reference the SAME category but are marked 🟢
# These might be over-migrated because same-category cross-reference is fine
same_cat_green = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='🟢' and c['expected_cat'] and c['expected_cat'] == c['node_cat']]
print(f"\nRegular+🟢+same cat (should be ✅?): {len(same_cat_green)}")
for c in same_cat_green[:5]:
    print(f"  {c['filename']} C{c['chart_seq']}: {c['reason'][:60]}")

# Check: charts on aggregate/home pages that should be ⚪ but are 🟢
agg_green = [c for c in reg['charts'] if c['page_type'] in ('sector_aggregate', 'home') and c['verdict']=='🟢']
print(f"\nAggregate/home 🟢 (should be ⚪): {len(agg_green)}")
for c in agg_green[:5]:
    print(f"  {c['filename']} C{c['chart_seq']}: {c['reason'][:60]}")

# Check: regular ⚪ charts (should be 0 after R1)
reg_white = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='⚪']
print(f"\nRegular ⚪ (should be 0): {len(reg_white)}")
for c in reg_white[:10]:
    print(f"  {c['filename']} C{c['chart_seq']}: {c['reason'][:60]}")

# Check: regular ✅ that reference cross-sector (should be 🟢?)
reg_cross_ok = [c for c in reg['charts'] if c['page_type']=='regular' and c['verdict']=='✅' and c['expected_cat'] and c['expected_cat'] != c['node_cat']]
print(f"\nRegular+✅+cross-sector (might need 🟢?): {len(reg_cross_ok)}")
for c in reg_cross_ok[:10]:
    print(f"  {c['filename']} C{c['chart_seq']}: node_cat={c['node_cat']} expected_cat={c['expected_cat']} role={c['role']}")

# Find charts with 主图 role on regular pages that reference cross-sector
# These should all be 🟢 after R1
main_cross = [c for c in reg['charts'] if c['page_type']=='regular' and c['role']=='主图' and c['expected_cat'] and c['expected_cat'] != c['node_cat']]
print(f"\nRegular+主图+cross-sector: {len(main_cross)}")
for c in main_cross:
    if c['verdict'] != '🟢':
        print(f"  NOT 🟢: {c['filename']} C{c['chart_seq']}: verdict={c['verdict']}")