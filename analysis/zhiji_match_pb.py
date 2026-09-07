"""
PB 知几匹配 v4 — 从 divergence 文件提取指标 + 知几搜索
格式：tab 分隔表格，指标用 ①②③ 编号
"""
import sys, os, re, json, subprocess, time
from pathlib import Path
from collections import Counter

ZHIJI_API = str(Path.home() / '.hermes' / 'scripts' / 'zhiji_api.py')
PYTHON = sys.executable
IN_DIR = Path('analysis/iwencai/PB')
OUT_DIR = Path('analysis/zhiji_match_v4')
VARIETY = 'PB'
VARIETY_CN = '铅'

# ---- 知几 API 调用（1秒限频 + 缓存）----
_last = [0.0]
_cache = {}
def zhiji(args, timeout=30):
    key = tuple(args)
    if key in _cache: return _cache[key]
    wait = 1.0 - (time.time() - _last[0])
    if wait > 0: time.sleep(wait)
    _last[0] = time.time()
    try:
        r = subprocess.run([PYTHON, ZHIJI_API] + list(args),
                           capture_output=True, text=True, timeout=timeout,
                           encoding='utf-8', errors='replace')
        if r.returncode != 0: return None
        data = json.loads(r.stdout)
        _cache[key] = data
        return data
    except Exception:
        return None

def search(q): return zhiji(('search', q))
def series(sid):
    return zhiji(('series', sid, '2025-01-01', '2026-09-06'))

def series_nonempty(sid):
    d = series(sid)
    if not d: return False
    pts = d.get('data') or d.get('series') or d.get('points') or []
    return len(pts) >= 3

# ---- PB 专用指标提取 ----
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮'

def extract_pb_indicators(text):
    """从 divergence 文件提取指标名"""
    indicators = set()
    # Pattern 1: ①name（unit）②name（unit）...
    for m in re.finditer(r'([' + CIRCLED + r'])([^①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮\n]+)', text):
        name = m.group(2).strip()
        # Remove trailing unit in parentheses
        name = re.sub(r'（[^）]*）$', '', name).strip()
        if len(name) >= 2 and len(name) <= 30:
            indicators.add(name)
    
    # Pattern 2: 从表格行提取（tab分隔，第3列是"包含指标"）
    lines = text.split('\n')
    for line in lines:
        if '\t' in line and ('指标' in line or '序号' in line):
            parts = line.split('\t')
            if len(parts) >= 3:
                ind_str = parts[2]
                for m in re.finditer(r'([' + CIRCLED + r'])([^\n①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]+)', ind_str):
                    name = m.group(2).strip()
                    name = re.sub(r'（[^）]*）$', '', name).strip()
                    if len(name) >= 2 and len(name) <= 30:
                        indicators.add(name)
    
    return list(indicators)

def gen_keywords(target):
    """生成搜索关键词"""
    kws = []
    # 1) 原词 + 品种词
    kws.append(VARIETY_CN + ' ' + target)
    # 2) 按分隔符拆词
    parts = [p for p in re.split(r'[\s（）/、，,·：:]+', target) if len(p) >= 2]
    if parts:
        kws.append(' '.join([VARIETY_CN] + parts[:2]))
        if len(parts) > 2:
            kws.append(' '.join([VARIETY_CN, parts[0], parts[-1]]))
    # 3) 铅专用同义词
    SYNONYMS = {
        '铅锭': ['铅锭', '电解铅'],
        '原生铅': ['原生铅', '电解铅', '铅锭'],
        '再生铅': ['再生铅', '还原铅', '二次铅'],
        '粗铅': ['粗铅', '原生铅'],
        '铅精矿': ['铅精矿', '铅矿', '铅矿石'],
        '铅蓄电池': ['铅蓄电池', '蓄电池', '铅酸电池'],
        '废电瓶': ['废电瓶', '废旧电池', '废铅蓄电池'],
        'SOC': ['SOC', '荷电状态'],
    }
    for kw_old, kws_new in SYNONYMS.items():
        if kw_old in target:
            for syn in kws_new:
                t2 = target.replace(kw_old, syn)
                if t2 != target:
                    kws.append(VARIETY_CN + ' ' + t2)
                    break
    # 去重
    seen, out = set(), []
    for kw in kws:
        if kw not in seen:
            seen.add(kw); out.append(kw)
    return out[:6]

# ---- 概念维度（简化版）----
CONCEPT_KWS = {
    '价格': ['价格', '结算价', '收盘价', '最高价', '最低价', '指数', '比值',
             '升贴水', '升水', '贴水', '现货价', '市场价', '均价', '溢价', '折价'],
    '库存': ['库存', '仓单', '厂库', '社库', '隐性库存', '在途'],
    '产量': ['产量', '产出'],
    '开工率': ['开工率', '产能利用率', '利用率'],
    '利润': ['利润', '毛利', '盈亏'],
    '加工费': ['加工费', 'TC', 'RC'],
    '进口量': ['进口量', '进口数量', '进口总量', '进口数'],
}
def concept(name):
    if not name: return set()
    name = str(name)
    return {c for c, kws in CONCEPT_KWS.items() if any(k in name for k in kws)}

def seg(s):
    return [x for x in re.split(r'[:：\s/\-（）()]', str(s)) if len(x) >= 2]

def strong_match(target, zhj_name):
    """A级判定"""
    if not zhj_name: return False
    if VARIETY_CN not in zhj_name: return False
    sa, sb = seg(target), seg(zhj_name)
    core = [x for x in sa if len(x) >= 3]
    if not core: return False
    hit = any(x == y or (len(x) >= 3 and (x in y or y in x)) for x in core for y in sb)
    if not hit: return False
    ct, cc = concept(target), concept(zhj_name)
    if ct and cc and not (ct & cc):
        return False
    return True

# ---- 主流程 ----
def process_variety():
    files = sorted([f for f in os.listdir(IN_DIR) if f.startswith('divergence_') and f.endswith('.md')])
    all_matches = []
    
    for fname in files:
        node = fname.replace('divergence_', '').replace('.md', '')
        fpath = IN_DIR / fname
        text = fpath.read_text(encoding='utf-8')
        
        indicators = extract_pb_indicators(text)
        if not indicators:
            print(f'  {fname}: 0 indicators')
            continue
        
        print(f'  {fname}: {len(indicators)} indicators')
        
        for ind_name in indicators:
            found = None
            for kw in gen_keywords(ind_name):
                d = search(kw)
                if not d or not d.get('results'): continue
                for r in d['results'][:10]:
                    rid, rname = r.get('id'), r.get('name', '')
                    if not rid or not rname: continue
                    if strong_match(ind_name, rname) and series_nonempty(rid):
                        found = {'zhiji_id': rid, 'zhiji_name': rname,
                                 'zhiji_unit': r.get('unit', ''),
                                 'match_level': 'A', 'verified': True,
                                 'notes': f'PB重搜命中; 搜索词:{kw}'}
                        break
                if found: break
            
            if found:
                entry = {
                    'node': node,
                    'node_name': node,
                    'iwencai_indicator': ind_name,
                    'iwencai_priority': '',
                    **found
                }
            else:
                entry = {
                    'node': node,
                    'node_name': node,
                    'iwencai_indicator': ind_name,
                    'iwencai_priority': '',
                    'zhiji_id': None,
                    'zhiji_name': None,
                    'zhiji_freq': None,
                    'zhiji_unit': None,
                    'match_level': 'C',
                    'verified': False,
                    'notes': '知几无此指标，需外部源'
                }
            all_matches.append(entry)
    
    # Save
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_data = {
        'variety': VARIETY,
        'agent': 'SenseNova-6.8-Flash-Lite',
        'date': time.strftime('%Y-%m-%d'),
        'matches': all_matches
    }
    out_path = OUT_DIR / f'{VARIETY}_zhiji_match.json'
    json.dump(out_data, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    
    # Stats
    a = sum(1 for m in all_matches if m['match_level'] == 'A')
    c = sum(1 for m in all_matches if m['match_level'] == 'C')
    print(f'\n=== PB 汇总 ===')
    print(f'  Total: {len(all_matches)}')
    print(f'  A: {a}')
    print(f'  C: {c}')
    print(f'  Output: {out_path}')

if __name__ == '__main__':
    process_variety()
