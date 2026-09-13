#!/usr/bin/env python3
"""PB indicator _nodes check"""
import json

data = json.load(open('data/indicators_v1.json', encoding='utf-8'))
pb_indicators = [i for i in data['indicators'] if i['mid'].startswith('j') or i['mid'].startswith('i')]
print(f"Total PB indicators: {len(pb_indicators)}")

no_nodes = [i for i in pb_indicators if i.get('_nodes', None) == [] or i.get('_nodes') is None]
has_nodes = [i for i in pb_indicators if i.get('_nodes') and len(i['_nodes']) > 0]
print(f"With _nodes populated: {len(has_nodes)}")
print(f"With _nodes=[] or missing: {len(no_nodes)}")

if no_nodes:
    print(f"\nSample _nodes=[] entries:")
    for i in no_nodes[:10]:
        print(f"  {i['mid']}: _nodes={i.get('_nodes')}")
    if len(no_nodes) > 10:
        print(f"  ... and {len(no_nodes)-10} more")