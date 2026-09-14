#!/usr/bin/env python3
"""R1 classification list: charts moved from ⚪ to 🟢"""
import json

reg = json.load(open('data/chart_registry.json', encoding='utf-8'))
moved = [c for c in reg['charts'] if c['page_type'] == 'regular' and c['verdict'] == '🟢' and '跨板块主图' in c['reason']]

print(f"R1修复: {len(moved)} charts moved from ⚪(设计意图) → 🟢(待人工确认)")
print()

by_variety = {}
for c in moved:
    by_variety.setdefault(c['variety_zh'], []).append(c)

for v in ['铜', '铝', '铅', '锌', '镍', '锡', '硅', '锂']:
    if v in by_variety:
        charts = by_variety[v]
        print(f"--- {v} ({len(charts)} charts) ---")
        for c in sorted(charts, key=lambda x: (x['filename'], x['chart_seq'])):
            print(f"  {c['filename']} C{c['chart_seq']}: {c['chart_title'][:55]}")
        print()

# Summary
print("=" * 60)
print(f"Total: {len(moved)} charts")
print(f"By variety: {', '.join(f'{v}={len(charts)}' for v, charts in by_variety.items())}")