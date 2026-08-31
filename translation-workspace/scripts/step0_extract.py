#!/usr/bin/env python3
"""
Step 0: 从 divergence_*.md 提取概念指标 + 跨节点去重 + 按板块分组
用法: python step0_extract.py ZN  (或其他品种代号)
输出: analysis/iwencai/{品种}/concept_indicators.json
"""
import re, json, os, glob, sys

# 6大板块分组
DIM_MAP = {
    '2': '价格信号',
    '3': '供给',
    '4': '库存',
    '5': '需求',
    '6': '进出口',
    '7': '成本利润'
}

def extract_concepts(variety_dir):
    """从divergence文件提取概念指标"""
    results = {}  # {node_id: [{name, chart_name, chart_type}]}
    
    for f in sorted(glob.glob(f"{variety_dir}/divergence_*.md")):
        node_id = re.search(r'divergence_(.+)\.md', f).group(1)
        with open(f, encoding='utf-8') as fh:
            content = fh.read()
        
        indicators = []
        # 匹配表格行: | 序号 | 图名称 | 包含指标(...) | 题材归属度 | ...
        for m in re.finditer(r'\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(?:直接相关|归属)', content):
            seq = m.group(1).strip()
            chart_name = m.group(2).strip()
            raw_indicators = m.group(3).strip()
            # 拆分指标名
            for ind in re.split(r'[、,，]', raw_indicators):
                ind = ind.strip()
                # 去除单位后缀
                ind = re.sub(r'[（(][^)）]*[)）]', '', ind).strip()
                # 去除频率后缀
                ind = re.sub(r'[（(](?:季|月|周|日)[)）]$', '', ind).strip()
                if ind and len(ind) >= 2:
                    indicators.append({
                        'name': ind,
                        'chart_name': chart_name,
                        'node_id': node_id
                    })
        
        if indicators:
            results[node_id] = indicators
    
    return results

def deduplicate(all_concepts):
    """跨节点去重：同一指标名只保留最贴切的节点"""
    seen = {}  # {normalized_name: [occurrences]}
    
    for node_id, indicators in all_concepts.items():
        for ind in indicators:
            # 归一化key
            key = ind['name'].replace(' ', '').replace('国内', '').replace('海外', '')
            key = re.sub(r'[（(][^)）]*[)）]', '', key)
            if key not in seen:
                seen[key] = []
            seen[key].append({
                'name': ind['name'],
                'chart_name': ind['chart_name'],
                'node_id': node_id
            })
    
    # 统计每个指标出现在多少个节点
    deduped = {}
    for key, occurrences in seen.items():
        if len(occurrences) == 1:
            # 只出现一次，直接保留
            o = occurrences[0]
            if o['node_id'] not in deduped:
                deduped[o['node_id']] = []
            deduped[o['node_id']].append(o['name'])
        else:
            # 出现在多个节点，记录重复信息
            # 保留第一个出现的节点
            primary = occurrences[0]
            if primary['node_id'] not in deduped:
                deduped[primary['node_id']] = []
            deduped[primary['node_id']].append(primary['name'])
    
    return deduped, seen

def group_by_dim(all_concepts):
    """按板块分组"""
    groups = {}
    for node_id, indicators in all_concepts.items():
        dim = node_id.split('.')[0]
        dim_name = DIM_MAP.get(dim, dim)
        if dim_name not in groups:
            groups[dim_name] = {'nodes': {}, 'unique_indicators': set()}
        
        # 去重该节点内的指标
        names = list(set(ind['name'] for ind in indicators))
        groups[dim_name]['nodes'][node_id] = names
        groups[dim_name]['unique_indicators'].update(names)
    
    # set转list
    for dim in groups:
        groups[dim]['unique_indicators'] = sorted(groups[dim]['unique_indicators'])
        groups[dim]['node_count'] = len(groups[dim]['nodes'])
        groups[dim]['unique_count'] = len(groups[dim]['unique_indicators'])
    
    return groups

def main():
    if len(sys.argv) < 2:
        print("用法: python step0_extract.py <品种代号>")
        print("示例: python step0_extract.py ZN")
        sys.exit(1)
    
    variety = sys.argv[1].upper()
    
    # 尝试多个路径
    search_paths = [
        f"/home/ubuntu/framework-tree/analysis/iwencai/{variety}",
        f"/home/ubuntu/analysis/iwencai/{variety}",
    ]
    
    variety_dir = None
    for p in search_paths:
        if os.path.exists(p):
            variety_dir = p
            break
    
    if not variety_dir:
        print(f"❌ 找不到 {variety} 的 divergence 目录")
        print(f"搜索路径: {search_paths}")
        sys.exit(1)
    
    print(f"📂 品种: {variety}")
    print(f"📁 路径: {variety_dir}")
    
    # Step 1: 提取
    concepts = extract_concepts(variety_dir)
    print(f"✅ 提取完成: {len(concepts)} 个节点")
    
    # Step 2: 去重
    deduped, seen = deduplicate(concepts)
    multi_node = {k: v for k, v in seen.items() if len(v) > 1}
    print(f"✅ 去重完成: {len(multi_node)} 个指标跨节点重复")
    
    # Step 3: 分组
    grouped = group_by_dim(concepts)
    print(f"✅ 分组完成: {len(grouped)} 个板块")
    for dim, info in sorted(grouped.items()):
        print(f"   {dim}: {info['node_count']}个节点, {info['unique_count']}个独立指标")
    
    # Step 4: 输出
    output = {
        'variety': variety,
        'total_nodes': len(concepts),
        'total_raw_indicators': sum(len(v) for v in concepts.values()),
        'cross_node_duplicates': {k: [{'node': o['node_id'], 'name': o['name']} for o in v] for k, v in multi_node.items()},
        'groups': grouped
    }
    
    out_path = f"{variety_dir}/concept_indicators.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📄 输出: {out_path}")
    
    # 打印每个板块的指标清单
    print(f"\n{'='*60}")
    print(f"📊 {variety} 概念指标清单（按板块）")
    print(f"{'='*60}")
    for dim, info in sorted(grouped.items()):
        print(f"\n### {dim} ({info['node_count']}个节点, {info['unique_count']}个指标)")
        for i, name in enumerate(info['unique_indicators'], 1):
            dup_mark = " [跨节点重复]" if any(name.replace('国内','').replace('海外','').replace(' ','') == k for k in multi_node) else ""
            print(f"  {i:2d}. {name}{dup_mark}")

if __name__ == '__main__':
    main()
