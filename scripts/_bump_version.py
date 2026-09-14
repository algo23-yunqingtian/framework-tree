import json

with open('data/indicators_v1.json', encoding='utf-8') as f:
    d = json.load(f)

d['version'] = 'v3.50'
d['_meta']['version'] = 'v3.50'
d['updated'] = '2026-09-13 20:15'
d['change'] = 'PB correction merge + registration: remote 964(3.49) + 61 new = 1025 indicators'

# Add changelog entry
if 'version_changelog' not in d:
    d['version_changelog'] = []
d['version_changelog'].append({
    'version': '3.50',
    'date': '2026-09-13',
    'change': 'Merge remote 3.49 (964) + PB correction batch registration (61 new A-level indicators from 27 correction files)'
})

with open('data/indicators_v1.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'Updated: v3.50, {len(d["indicators"])} indicators')
