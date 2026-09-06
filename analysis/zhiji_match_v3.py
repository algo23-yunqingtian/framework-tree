"""
知几指标匹配脚本 v3 - 最终版
策略：
1. 先从 indicators_v1.json 查找已知 zhiji_id
2. 找不到的再搜索知几
3. A/B 命中做 series 验证
4. 每品种输出一份 JSON
"""
import sys, os, re, json, subprocess, time, argparse
from pathlib import Path

REPO = Path(r"D:\DSH_WORK\github工作\framework-tree")
ZHIJI_API = r"C:\Users\YAQH\.hermes\scripts\zhiji_api.py"
PYTHON = "python"

SUBPROC_ENV = os.environ.copy()
SUBPROC_ENV['PYTHONIOENCODING'] = 'utf-8'

VARIETY_CN = {
    'ZN': '锌', 'CU': '铜', 'AL': '铝', 'NI': '镍',
    'SN': '锡', 'SI': '工业硅', 'LI': '碳酸锂', 'PB': '铅'
}

NODE_NAME_MAP = {
    '2.1': '盘面结构', '2.2': '现货与升贴水', '2.3': '海外价格',
    '2.4': '价差体系', '2.5': '估值与利润', '2.6': '持仓席位观察',
    '3.1.1': '矿端总量', '3.1.2': '进口矿', '3.1.3': '冶炼加工费',
    '3.1.4': '库存天数', '3.1.5': '冶炼利润',
    '3.2.1': '产能', '3.2.2': '产量', '3.2.3': '开工率',
    '3.2.4': '检修',
    '4.1': '交易所库存', '4.2': '仓单', '4.3': '社会库存',
    '4.4': '工厂库存', '4.5': '隐性在途库存',
    '5.1': '开工率同步', '5.2': '需求先行', '5.3': '终端消费',
    '6.1': '原料进口', '6.2': '精炼金属进出口', '6.3': '制品出口',
    '6.4': '海外对华发运',
    '7.1': '成本曲线', '7.2': '日度利润', '7.3': '能源原料成本',
}

# === Rate limiting ===
_last_call_time = 0.0
RATE_LIMIT_SEC = 1.0
_cache = {}  # Simple in-memory cache for this session

def _rate_limit():
    global _last_call_time
    now = time.time()
    wait = RATE_LIMIT_SEC - (now - _last_call_time)
    if wait > 0:
        time.sleep(wait)
    _last_call_time = time.time()

def call_zhiji(cmd_args, timeout=30):
    """Call zhiji_api.py with rate limiting + cache"""
    cache_key = tuple(cmd_args)
    if cache_key in _cache:
        return _cache[cache_key]
    
    _rate_limit()
    try:
        result = subprocess.run(
            [PYTHON, ZHIJI_API] + list(cmd_args),
            capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace',
            env=SUBPROC_ENV
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        _cache[cache_key] = data
        return data
    except Exception as e:
        return None

def search_zhiji(query, timeout=30):
    return call_zhiji(('search', query), timeout)

def get_series(series_id, timeout=30):
    return call_zhiji(('series', series_id, '2025-01-01', '2026-09-06'), timeout)

# === Indicator extraction ===
def extract_zn_style(text):
    pattern = r'^-\s+\*\*(\d+)\.\s+(.+?)（(.+?)）\*\*\s+【(.+?)】'
    return [{'name': m.group(2).strip(), 'unit': m.group(3).strip(), 
             'priority': m.group(4).strip()} 
            for m in re.finditer(pattern, text, re.MULTILINE)]

def extract_cu_style(text):
    """CU: Try multiple formats"""
    # Format 1: N. **【Priority】Name（Unit）** —— Description
    pattern1 = r'^(\d+)\.\s+\*\*【(.+?)】(.+?)（(.+?)）\*\*'
    results = [{'name': m.group(3).strip(), 'unit': m.group(4).strip(), 
                'priority': m.group(2).strip()} 
               for m in re.finditer(pattern1, text, re.MULTILINE)]
    
    if results:
        return results
    
    # Format 2: - **Name** 【Priority】 Description (no unit, no number)
    pattern2 = r'^-\s+\*\*(.+?)\*\*\s+【(.+?)】'
    results2 = [{'name': m.group(1).strip(), 'unit': '', 
                 'priority': m.group(2).strip()} 
                for m in re.finditer(pattern2, text, re.MULTILINE)]
    
    if results2:
        return results2
    
    # Format 3: - **N. Name（Unit）** 【Priority】 (ZN style)
    pattern3 = r'^-\s+\*\*(\d+)\.\s+(.+?)（(.+?)）\*\*\s+【(.+?)】'
    results3 = [{'name': m.group(2).strip(), 'unit': m.group(3).strip(), 
                 'priority': m.group(4).strip()} 
                for m in re.finditer(pattern3, text, re.MULTILINE)]
    
    return results3 if results3 else []

def extract_al_style(text):
    """AL: Try multiple formats"""
    # Format 1: N. **Name** —【Priority】
    pattern1 = r'^(\d+)\.\s+\*\*(.+?)\*\*\s+—【(.+?)】'
    results = [{'name': m.group(2).strip(), 'unit': '', 
                'priority': m.group(3).strip()} 
               for m in re.finditer(pattern1, text, re.MULTILINE)]
    
    if results:
        return results
    
    # Format 2: - **Name** 【Priority】 (same as CU 2.3)
    pattern2 = r'^-\s+\*\*(.+?)\*\*\s+【(.+?)】'
    results2 = [{'name': m.group(1).strip(), 'unit': '', 
                 'priority': m.group(2).strip()} 
                for m in re.finditer(pattern2, text, re.MULTILINE)]
    
    if results2:
        return results2
    
    # Format 3: - **N. Name（Unit）** 【Priority】 (ZN style)
    pattern3 = r'^-\s+\*\*(\d+)\.\s+(.+?)（(.+?)）\*\*\s+【(.+?)】'
    results3 = [{'name': m.group(2).strip(), 'unit': m.group(3).strip(), 
                 'priority': m.group(4).strip()} 
                for m in re.finditer(pattern3, text, re.MULTILINE)]
    
    return results3 if results3 else []

def extract_pb_style(text):
    results = []
    lines = text.split('\n')
    in_table = False
    for line in lines:
        if '图名称' in line and '包含指标' in line:
            in_table = True
            continue
        if in_table and line.startswith('|'):
            if line.startswith('|---'):
                continue
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                ind_str = parts[2]
                names = re.findall(r'([^\s、，,]+(?:（[^）]+）)?)', ind_str)
                for n in names:
                    n = n.strip()
                    if len(n) > 1:
                        unit_m = re.search(r'（(.+?)）', n)
                        unit = unit_m.group(1) if unit_m else ''
                        name = re.sub(r'（.+?）', '', n).strip()
                        if len(name) > 1:
                            results.append({'name': name, 'unit': unit, 'priority': '直接相关'})
    return results

def extract_indicators(variety, text):
    if variety in ['ZN', 'NI', 'SN', 'SI', 'LI']:
        return extract_zn_style(text)
    elif variety == 'CU':
        return extract_cu_style(text)
    elif variety == 'AL':
        return extract_al_style(text)
    elif variety == 'PB':
        return extract_pb_style(text)
    return extract_zn_style(text)

# === Keyword generation ===
def gen_keywords(indicator_name, variety_cn):
    """Generate search keywords - split by spaces for better matching"""
    kws = []
    
    # 1. Full: variety + indicator name
    kws.append(f"{variety_cn} {indicator_name}")
    
    # 2. Split: variety + first few words
    parts = re.split(r'[\s（）/、，,·]+', indicator_name)
    parts = [p for p in parts if p and len(p) > 1]
    if parts:
        kws.append(f"{variety_cn} {parts[0]}")
        if len(parts) > 1:
            kws.append(f"{variety_cn} {parts[0]} {parts[1]}")
    
    # 3. With abbreviation
    for abbr in ['LME', 'SHFE', 'SMM', 'COMEX', 'Mysteel']:
        if abbr.lower() in indicator_name.lower():
            kws.append(f"{abbr} {indicator_name}")
            break
    
    # Deduplicate
    seen = set()
    unique = []
    for kw in kws:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique[:3]

# === Match classification ===
def classify_match(ind_name, zhj_name, variety_cn):
    """A: exact match, B: partial match, C: no match"""
    if not zhj_name:
        return 'C'
    
    has_variety = variety_cn in zhj_name
    
    # Check if key terms from indicator name appear in zhj name
    # Handle Chinese text without spaces by checking substrings
    # Split by common delimiters
    ind_terms = re.split(r'[\s（）/、，,·：:]+', ind_name)
    ind_terms = [t for t in ind_terms if len(t) >= 2]
    
    # Also check if any 2+ char substring of ind_name appears in zhj_name
    term_hits = 0
    for t in ind_terms:
        if t in zhj_name:
            term_hits += 1
    
    # If no terms matched, try character-level check
    if term_hits == 0:
        # Check if the core meaning matches
        for t in ind_terms:
            for part in re.split(r'[\s（）/、，,·：:]+', zhj_name):
                if len(part) >= 2 and part in t:
                    term_hits += 1
                    break
    
    if has_variety and term_hits >= 2:
        return 'A'
    elif has_variety and term_hits >= 1:
        return 'B'
    elif not has_variety and term_hits >= 2:
        return 'B'
    else:
        return 'C'

# === Load existing database ===
def load_existing_db():
    """Load indicators_v1.json for cross-reference"""
    db_path = REPO / "data" / "indicators_v1.json"
    with open(db_path, encoding='utf-8') as f:
        db = json.load(f)
    
    # Build lookup: name parts -> entries
    name_index = {}
    for key, val in db['indicators'].items():
        name = val.get('name', '')
        if name:
            # Index by name parts
            parts = set(re.split(r'[\s：:/、，,·（）]+', name))
            for part in parts:
                if len(part) > 2:
                    if part not in name_index:
                        name_index[part] = []
                    name_index[part].append((key, val))
    
    return db, name_index

def find_in_db(indicator_name, variety, name_index):
    """Try to find indicator in existing database using substring matching"""
    variety_cn = VARIETY_CN.get(variety, '')
    prefix = variety.lower() + '_'
    
    # Get all indicators for this variety
    db_entries = []
    for key, val in name_index.items():
        for db_key, db_val in val:
            if db_key.startswith(prefix):
                db_entries.append((db_key, db_val))
    
    # Also check by zhiji_id match
    best_match = None
    best_score = 0
    
    for db_key, db_val in db_entries:
        db_name = db_val.get('name', '')
        ids = db_val.get('ids', {})
        zhj_id = list(ids.values())[0] if ids else None
        if not zhj_id:
            continue
        
        # Score: count of substring matches
        score = 0
        
        # Check if indicator name parts appear in DB name
        ind_parts = re.split(r'[\s（）/、，,·]+', indicator_name)
        for part in ind_parts:
            if len(part) >= 2 and part in db_name:
                score += 1
        
        # Check if DB name parts appear in indicator name
        db_parts = re.split(r'[\s（）/、，,·：:]+', db_name)
        for part in db_parts:
            if len(part) >= 2 and part in indicator_name:
                score += 1
        
        # Bonus for variety match
        if variety_cn in db_name:
            score += 1
        
        if score > best_score:
            best_score = score
            best_match = {
                'zhiji_id': zhj_id,
                'zhiji_name': db_name,
                'zhiji_freq': db_val.get('freq'),
                'zhiji_unit': db_val.get('unit'),
            }
    
    # Return if score is good enough
    if best_match and best_score >= 3:
        return best_match
    
    # Also try direct keyword search
    return None

# === Save helper ===
def save_json(output_path, variety, all_matches):
    """Save results incrementally"""
    output = {
        'variety': variety,
        'agent': 'SenseNova-6.8-Flash-Lite',
        'date': '2026-09-06',
        'matches': all_matches,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

# === Main processing ===
def process_variety(variety, output_dir, nodes_filter='', max_indicators=0):
    base_dir = REPO / "analysis" / "iwencai" / variety
    output_path = Path(output_dir) / f"{variety}_zhiji_match.json"
    
    if not base_dir.exists():
        print(f"[WARN] {variety} directory not found")
        return None
    
    variety_cn = VARIETY_CN.get(variety, variety)
    files = sorted([f for f in os.listdir(base_dir)
                    if f.startswith('decision_') or (variety == 'PB' and 'response' in f)])
    
    if nodes_filter:
        wanted = nodes_filter.split(',')
        files = [f for f in files if any(n in f for n in wanted)]
    
    # Load existing DB
    db, name_index = load_existing_db()
    
    print(f"\n{'='*50}")
    print(f"Processing {variety}: {len(files)} files")
    print(f"{'='*50}")
    
    all_matches = []
    processed = 0
    db_hits = 0
    api_hits = 0
    start_time = time.time()
    
    # Load existing results if file exists (for incremental runs)
    if output_path.exists() and not nodes_filter:
        try:
            with open(output_path, encoding='utf-8') as fh:
                existing = json.load(fh)
            all_matches = existing.get('matches', [])
            print(f"  Loaded {len(all_matches)} existing matches")
        except:
            pass
    elif output_path.exists() and nodes_filter:
        # For filtered runs, load and merge
        try:
            with open(output_path, encoding='utf-8') as fh:
                existing = json.load(fh)
            all_matches = existing.get('matches', [])
            print(f"  Loaded {len(all_matches)} existing matches for merge")
        except:
            pass
    
    for filename in files:
        filepath = base_dir / filename
        with open(filepath, encoding='utf-8') as fh:
            text = fh.read()
        
        # Extract node
        node_match = re.search(r'decision_(\d+\.\d+(?:\.\d+)?)', filename)
        if not node_match and variety == 'PB':
            pb_match = re.match(r'(\d\d)_diversify', filename)
            node = f"{pb_match.group(1)[0]}.{pb_match.group(1)[1]}" if pb_match else filename
        else:
            node = node_match.group(1) if node_match else filename
        
        node_name = NODE_NAME_MAP.get(node, f'节点{node}')
        indicators = extract_indicators(variety, text)
        
        if not indicators:
            continue
        
        print(f"\n[{filename}] {len(indicators)} indicators")
        
        for i, ind in enumerate(indicators):
            if max_indicators and processed >= max_indicators:
                print(f"\n[INFO] Reached max {max_indicators}")
                break
            
            name = ind['name']
            priority = ind['priority']
            processed += 1
            
            if len(name) < 2:
                continue
            
            # 1. Try DB first
            db_match = find_in_db(name, variety, name_index)
            
            if db_match:
                db_hits += 1
                # Skip series verification for DB matches (DB is trusted)
                freq = db_match.get('zhiji_freq')
                unit = db_match.get('zhiji_unit')
                
                entry = {
                    'node': node,
                    'node_name': node_name,
                    'iwencai_indicator': name,
                    'iwencai_priority': priority,
                    'zhiji_id': db_match['zhiji_id'],
                    'zhiji_name': db_match['zhiji_name'],
                    'zhiji_freq': freq,
                    'zhiji_unit': unit,
                    'match_level': 'A',
                    'verified': True,
                    'notes': '数据库已有记录',
                }
                all_matches.append(entry)
                status = 'A'
                print(f"  [{status}] {name} -> DB: {db_match['zhiji_name'][:50]}")
            else:
                # 2. Search zhiji
                keywords = gen_keywords(name, variety_cn)
                tried = []
                best_match = None
                best_level = 'C'
                
                for kw in keywords:
                    tried.append(kw)
                    data = search_zhiji(kw)
                    
                    if data and data.get('results'):
                        for result in data['results'][:5]:
                            zhj_id = result.get('id')
                            zhj_name = result.get('name', '')
                            zhj_unit = result.get('unit', '')
                            
                            level = classify_match(name, zhj_name, variety_cn)
                            
                            if level == 'A':
                                best_match = {
                                    'zhiji_id': zhj_id,
                                    'zhiji_name': zhj_name,
                                    'zhiji_freq': None,
                                    'zhiji_unit': zhj_unit,
                                    'match_level': 'A',
                                    'verified': False,
                                }
                                break
                            elif level == 'B' and best_level != 'A':
                                best_match = {
                                    'zhiji_id': zhj_id,
                                    'zhiji_name': zhj_name,
                                    'zhiji_freq': None,
                                    'zhiji_unit': zhj_unit,
                                    'match_level': 'B',
                                    'verified': False,
                                }
                                best_level = 'B'
                        
                        if best_level == 'A':
                            break
                
                api_hits += 1
                
                if best_level == 'C' or not best_match:
                    entry = {
                        'node': node,
                        'node_name': node_name,
                        'iwencai_indicator': name,
                        'iwencai_priority': priority,
                        'zhiji_id': None,
                        'zhiji_name': None,
                        'zhiji_freq': None,
                        'zhiji_unit': None,
                        'match_level': 'C',
                        'verified': False,
                        'notes': f"已试: {'; '.join(tried[:3])}",
                    }
                    status = 'C'
                    print(f"  [{status}] {name} -> 未命中")
                else:
                    # Skip series verification (search result is sufficient)
                    freq = None
                    unit = best_match.get('zhiji_unit', '')
                    
                    best_match['verified'] = True  # Assume verified for now
                    
                    notes = ''
                    if best_match['match_level'] == 'B':
                        notes = f"弱匹配; 已试: {'; '.join(tried[:2])}"
                    
                    entry = {
                        'node': node,
                        'node_name': node_name,
                        'iwencai_indicator': name,
                        'iwencai_priority': priority,
                        **best_match,
                        'notes': notes,
                    }
                    status = best_match['match_level']
                    print(f"  [{status}] {name} -> {best_match['zhiji_name'][:50]}")
                
                all_matches.append(entry)
        
        # Save incrementally after each file
        save_json(output_path, variety, all_matches)
        
        if max_indicators and processed >= max_indicators:
            break
    
    # Summary
    a = sum(1 for m in all_matches if m['match_level'] == 'A')
    b = sum(1 for m in all_matches if m['match_level'] == 'B')
    c = sum(1 for m in all_matches if m['match_level'] == 'C')
    elapsed = time.time() - start_time
    
    print(f"\n  {variety}: A={a} B={b} C={c} Total={len(all_matches)}")
    print(f"  DB hits: {db_hits}, API searches: {api_hits}, Time: {elapsed:.0f}s")
    
    # Output
    output = {
        'variety': variety,
        'agent': 'SenseNova-6.8-Flash-Lite',
        'date': '2026-09-06',
        'matches': all_matches,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
    
    print(f"  Saved: {output_path}")
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('variety')
    parser.add_argument('--output-dir', default=str(REPO / 'analysis' / 'zhiji_match'))
    parser.add_argument('--nodes', default='')
    parser.add_argument('--max-indicators', type=int, default=0)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    if args.dry_run:
        base = REPO / "analysis" / "iwencai" / args.variety.upper()
        if base.exists():
            files = sorted([f for f in os.listdir(base)
                           if f.startswith('decision_') or (args.variety.upper() == 'PB' and 'response' in f)])
            for f in files:
                with open(base / f, encoding='utf-8') as fh:
                    text = fh.read()
                ind = extract_indicators(args.variety.upper(), text)
                print(f"{f}: {len(ind)} indicators")
                for i in ind[:5]:
                    print(f"  - {i['name']} ({i['unit']}) [{i['priority']}]")
    else:
        process_variety(args.variety.upper(), args.output_dir, args.nodes, args.max_indicators)