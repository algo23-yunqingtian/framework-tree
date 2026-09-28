#!/usr/bin/env python3
"""Extract TP samples from V8.5 P0 full regression."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\DSH_WORK\framework-tree\analysis_temp\dshb_v8_reg_out\t1_p0_full_regression.json', encoding='utf-8') as f:
    data = json.load(f)

results = data['main_test_set']['all_results']
tp_samples = [r for r in results if r.get('evaluation') == 'TP']

print(f'Total TP: {len(tp_samples)}')
print(f'Total samples: {len(results)}')
print(f'Total FN: {len([r for r in results if r.get("evaluation") == "FN"])}')
print()

# Group by category
from collections import Counter
cat_counts = Counter(s.get('category', '') for s in tp_samples)
print('TP by category:')
for cat, cnt in cat_counts.most_common():
    print(f'  {cat}: {cnt}')
print()

# Group by match level
level_counts = Counter(s.get('match_level', '') for s in tp_samples)
print('TP by match level:')
for lv, cnt in level_counts.most_common():
    print(f'  {lv}: {cnt}')
print()

# Show all TP samples
print(f'{"Sample ID":12s} {"Matched ID":16s} {"Level":4s} {"Confidence":10s} {"Variety":8s} {"Category":20s} {"Indicator Name"}')
print('-' * 130)
for s in tp_samples:
    print(f"{s['sample_id']:12s} {s.get('matched_id',''):16s} {s.get('match_level',''):4s} {s.get('match_confidence',''):10s} {s.get('variety',''):8s} {s.get('category',''):20s} {s.get('indicator_name','')[:40]}")

# Also list FN
print('\n=== FN samples ===')
fn_samples = [r for r in results if r.get('evaluation') == 'FN']
for s in fn_samples:
    print(f"{s['sample_id']:12s} {s.get('matched_id',''):16s} {s.get('match_level',''):4s} {s.get('match_confidence',''):10s} {s.get('variety',''):8s} {s.get('indicator_name','')}")