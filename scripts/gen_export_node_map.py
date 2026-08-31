#!/usr/bin/env python3
"""
P0: 自动生成 data/export_node_map.json
从 tree_config.json + 磁盘实际 HTML 文件，生成 node→page 映射表。
"""
import json, os, re

BASE = "/home/ubuntu/framework-tree"
tree = json.load(open(f"{BASE}/data/tree_config.json"))
comms = {c['id']: c['code'] for c in tree['commodities']}  # cu→CU

node_map = {}  # { "CU:3.1.2": ["cu_3_1_2.html"], ... }

for f in sorted(os.listdir(BASE)):
    if not f.endswith('.html') or f == 'index.html': continue
    m = re.match(r'^(cu|al|pb|zn|ni|sn|si|li)_(.+)\.html$', f)
    if not m: continue
    v_id, page_part = m.group(1), m.group(2)
    code = comms.get(v_id, v_id.upper())
    
    # 提取板块号：去掉 overview 后缀，取前导数字段
    if page_part.endswith('_overview'):
        grp = page_part.replace('_overview','')
        node_map.setdefault(f"{code}:overview:{grp}", []).append(f)
    else:
        # 尝试匹配数字前缀
        m2 = re.match(r'^(\d+)', page_part)
        if m2:
            node_map.setdefault(f"{code}:{m2.group(1)}", []).append(f)

# 按 key 排序
node_map = dict(sorted(node_map.items()))

json.dump(node_map, open(f"{BASE}/data/export_node_map.json",'w'),
          ensure_ascii=False, indent=2)
print(f"✅ 生成 {len(node_map)} 个节点映射 → data/export_node_map.json")
