import json

with open('scripts/correction_extract_report.json', encoding='utf-8') as f:
    d = json.load(f)

entries = d['new_entries']
print(f'Total new entries: {len(entries)}')
print()

# Group by source file
from collections import defaultdict
by_source = defaultdict(list)
for e in entries:
    by_source[e['source']].append(e)

for src, items in sorted(by_source.items()):
    print(f'--- {src} ({len(items)} new) ---')
    for i, e in enumerate(items):
        name = e['name'][:40]
        print(f'  {i+1}. {e["zhiji_id"]} | {name} | node={e["node"]}')
    print()
