#!/usr/bin/env python3
import json

with open('framework-tree/analysis/e2e_output/v88/phase03/p1/dshb/v88_phase03_p1_metric_indicator_code_mapping.json','r',encoding='utf-8') as f:
    d = json.load(f)

p09 = d.get('p0_9', {})
print(f'P0-9 denominator: {p09.get("denominator")}')
print(f'P0-9 numerator: {p09.get("numerator")}')
print(f'P0-9 coverage: {p09.get("coverage_pct")}%')
print(f'Method: {p09.get("method")}')
missing = p09.get('missing_ids', [])
print(f'Missing ({len(missing)}): {missing}')
orphan = p09.get('orphan_ids', [])
print(f'Orphan count: {len(orphan)}')
intersection = p09.get('intersection_ids', [])
print(f'Intersection count: {len(intersection)}')
print()
print('Summary:')
print(json.dumps(d['summary'], indent=2))