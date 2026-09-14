#!/usr/bin/env python3
"""Check PB indicators in step3_final and indicators_v1"""
import json

# Check indicators_v1
v1 = json.load(open('data/indicators_v1.json', encoding='utf-8'))
pb_v1 = [k for k in v1['indicators'] if k.startswith('j') or k.startswith('i')]
no_nodes_v1 = [k for k in pb_v1 if v1['indicators'][k].get('_nodes') is None or v1['indicators'][k].get('_nodes') == []]
print(f"indicators_v1.json: {len(pb_v1)} PB indicators, {len(no_nodes_v1)} with _nodes missing")

# Check step3_final
sf = json.load(open('analysis/iwencai/step3_final.json', encoding='utf-8'))
tiers = {}
for tier_key in ['A', 'B', 'C']:
    items = sf.get(tier_key, [])
    for x in items:
        code = x.get('code', '')
        if code.startswith('j') or code.startswith('i'):
            tiers.setdefault(code, x.get('tier', tier_key))
print(f"step3_final.json: {len(tiers)} PB indicators found in A/B/C tiers")
for t in ['A', 'B', 'C']:
    count = sum(1 for v in tiers.values() if v == t)
    print(f"  Tier {t}: {count}")