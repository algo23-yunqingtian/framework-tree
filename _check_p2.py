"""Check verified non-AO wr indicators by variety"""
import json
from collections import Counter

with open('data/indicators_v1.json', encoding='utf-8') as f:
    d = json.load(f)

# Count verified by variety
varieties = Counter()
details = {}
for k, v in d.items():
    if k.startswith('wr') and v.get('verified'):
        meta = v.get('weekly_report_import', {})
        var = meta.get('variety', '?')
        varieties[var] += 1
        details.setdefault(var, []).append((k, v.get('name','')[:30], v.get('unit',''), list(v.get('ids',{}).values())[0]))

print("=== Verified wr indicators by variety ===")
for var, cnt in sorted(varieties.items()):
    print(f"\n{var}: {cnt} verified")
    for k, name, unit, zid in details[var][:10]:
        print(f"  {k}: {name} | {unit} | {zid}")

# Check tree_config for existing nodes
with open('data/tree_config.json', encoding='utf-8') as f:
    tc = json.load(f)

print("\n=== Existing HTML pages ===")
import os
pages = [f for f in os.listdir('.') if f.endswith('.html') and f[0].isalpha()]
print(f"Total HTML pages: {len(pages)}")
# Group by variety prefix
prefixes = Counter()
for p in pages:
    pre = p.split('_')[0]
    prefixes[pre] += 1
for pre, cnt in sorted(prefixes.items()):
    print(f"  {pre}: {cnt} pages")
