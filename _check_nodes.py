"""Check tree_config nodes vs existing pages for each variety"""
import json, os

with open('data/tree_config.json', encoding='utf-8') as f:
    tc = json.load(f)

# Get all nodes per variety
variety_nodes = {}
for cat in tc['categories']:
    for child in cat.get('children', []):
        comms = child.get('comms', [])
        for comm in comms:
            variety_nodes.setdefault(comm, []).append((child['id'], child['code'], child['name']))
        for sub in child.get('children', []):
            for comm in sub.get('comms', []):
                variety_nodes.setdefault(comm, []).append((sub['id'], sub['code'], sub['name']))

# Existing pages
pages = {}
for f in os.listdir('.'):
    if f.endswith('.html') and f[0].isalpha():
        prefix = f.split('_')[0]
        pages.setdefault(prefix, []).append(f)

# Check coverage
print("=== Node coverage by variety ===")
for var in ['li', 'si', 'ni', 'sn', 'al', 'cu', 'zn', 'pb', 'ao']:
    nodes = variety_nodes.get(var, [])
    node_pages = pages.get(var, [])
    print(f"\n{var}: {len(nodes)} nodes, {len(node_pages)} pages")
    
    # Check which nodes have pages
    node_ids = set()
    for nid, code, name in nodes:
        # Match node code to page filename
        has_page = any(code.replace('.', '') in p.replace('.', '') for p in node_pages)
        if not has_page:
            print(f"  MISSING: {code} {name} ({nid})")
    
    if len(node_pages) > 0:
        print(f"  Pages: {sorted(node_pages)[:5]}...")
