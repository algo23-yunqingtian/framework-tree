#!/usr/bin/env python3
"""Analyze TP samples for deduplication."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\DSH_WORK\framework-tree\analysis_temp\dshb_v8_reg_out\t1_p0_full_regression.json', encoding='utf-8') as f:
    data = json.load(f)

results = data['main_test_set']['all_results']
tp_samples = [r for r in results if r.get('evaluation') == 'TP']

# Unique matched IDs
matched_ids = set()
id_to_samples = {}
for s in tp_samples:
    mid = s.get('matched_id', '')
    matched_ids.add(mid)
    if mid not in id_to_samples:
        id_to_samples[mid] = []
    id_to_samples[mid].append(s['sample_id'])

print(f'Total TP samples: {len(tp_samples)}')
print(f'Unique matched IDs: {len(matched_ids)}')
print(f'Samples sharing IDs: {sum(1 for ids, samples in id_to_samples.items() if len(samples) > 1)}')
print()

# Show duplicates
print('=== Duplicate matched IDs ===')
for mid, samples in sorted(id_to_samples.items()):
    if len(samples) > 1:
        print(f'  {mid}: {", ".join(samples)}')

print()
print('=== Unique matched IDs (sorted) ===')
for mid in sorted(matched_ids):
    samples = id_to_samples[mid]
    s = tp_samples[tp_samples.index(next(x for x in tp_samples if x.get('matched_id') == mid))]
    print(f'  {mid:16s} | {s.get("variety",""):5s} | {s.get("indicator_name","")[:50]}')