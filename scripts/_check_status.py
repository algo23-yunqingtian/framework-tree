#!/usr/bin/env python3
"""Check alias map structure and PB div-ids"""
import json, os, glob, re

base = r'D:\DSH_WORK\周报\framework-tree'

# Check alias map
print("=== Alias Map Structure ===")
d = json.load(open(os.path.join(base, 'docs', 'alias_metadb', 'thsh_zhiji_alias_map.json'), encoding='utf-8'))
print(f"Top keys: {list(d.keys())}")
print(f"Meta: {d.get('_meta', {})}")
aliases = d.get('aliases', {})
print(f"Aliases count: {len(aliases)}")
# Count SHFE entries
shfe_count = 0
shfe_keys = []
for k, v in aliases.items():
    zhiji_name = v.get('zhiji_name', '') if isinstance(v, dict) else ''
    if 'SHFE' in zhiji_name.upper() or '上期所' in zhiji_name:
        shfe_count += 1
        shfe_keys.append(k)
    if 'SHFE' in k.upper() or '上期所' in k:
        shfe_count += 1
        shfe_keys.append(k)
# Deduplicate
shfe_keys = list(set(shfe_keys))
print(f"SHFE/上期所 entries (in aliases): {len(shfe_keys)}")
if shfe_keys:
    print(f"Sample: {shfe_keys[:5]}")

# Check by_code
by_code = d.get('by_code', {})
print(f"\nBy-code keys: {list(by_code.keys())}")
for code, items in by_code.items():
    if isinstance(items, list):
        print(f"  {code}: {len(items)} entries")
        if items:
            print(f"    Sample: {items[0] if isinstance(items[0], str) else list(items[0].keys()) if isinstance(items[0], dict) else '?'}")
    elif isinstance(items, dict):
        print(f"  {code}: dict with {len(items)} keys")

# Check by_tier
by_tier = d.get('by_tier', {})
print(f"\nBy-tier keys: {list(by_tier.keys())}")

# Check PB div-ids
print("\n=== PB Div-IDs ===")
html_files = sorted(glob.glob(os.path.join(base, 'pb_*.html')))
non_standard = []
standard_pat = re.compile(r'^echart_pb_[0-9]+(?:_[0-9]+)*_c\d+$')
for hf in html_files:
    fname = os.path.basename(hf)
    html = open(hf, encoding='utf-8').read()
    divs = re.findall(r'<div id="(echart_[^"]+)"', html)
    for dv in divs:
        if not standard_pat.match(dv):
            non_standard.append((fname, dv))
print(f"PB HTML files: {len(html_files)}")
print(f"Non-standard div-ids: {len(non_standard)}")
for f, dv in non_standard[:20]:
    print(f"  {f}: {dv}")
if len(non_standard) > 20:
    print(f"  ... and {len(non_standard)-20} more")