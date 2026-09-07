"""
知几匹配 v4 重判器 — 只重判 B 级条目（A 级不动、C 级不动）
================================================================
用法:
    python3 zhiji_match_v4_recheck.py                      # 重判全部 7 品种 B 级
    python3 zhiji_match_v4_recheck.py --variety CU         # 只重判铜
    python3 zhiji_match_v4_recheck.py --dry-run            # 不写文件，只出统计

原理（对应 COLLAB_TASK_ZHJI_MATCH_V4_20260907.md 的 8 条规则）:
    1. 对每条 B 级：先做 3 道互斥检查（八概念/产业链上下游/地域）
       - 现有候选与目标概念不符 → 标记 MISMATCH，用改良搜索词重搜
    2. 重搜命中 A（品种词+核心词双匹配 + series 非空）→ 升级为 A，替换 zhiji_id
    3. 重搜只命中 B 或未命中 → 降级为 C（zhiji_id 置空，notes 写"需外部源"）
    4. 概念相符的 B 级原样保留（真弱匹配，如频率/口径差异）
    5. 单一 ID 复用 >3 次 → 强制转人工复核标记
================================================================
"""
import sys, os, re, json, subprocess, time, argparse
from pathlib import Path
from collections import Counter

# ============ 可配置：两个平台路径 ============
ZHIJI_API = str(Path.home() / '.hermes' / 'scripts' / 'zhiji_api.py')
PYTHON = sys.executable
IN_DIR   = Path('analysis/zhiji_match')      # v3 产物（输入）
OUT_DIR  = Path('analysis/zhiji_match_v4')   # v4 产物（输出）
# =============================================

VARIETY_CN = {
    'ZN': '锌', 'CU': '铜', 'AL': '铝', 'NI': '镍',
    'SN': '锡', 'SI': '工业硅', 'LI': '碳酸锂', 'PB': '铅'
}

# ---- 规则1：八概念维度 ----
CONCEPT_KWS = {
    '加工费': ['TC', '加工费', 'RC', '折价系数', '扣率', 'TC指数'],
    '库存':   ['库存', '仓单', '厂库', '社库', '隐性库存', '在途'],
    '进口量': ['进口量', '进口数量', '进口总量', '进口数'],
    '产量':   ['产量', '产出'],
    '开工率': ['开工率', '产能利用率', '利用率'],
    '利润':   ['利润', '毛利', '盈亏'],
    '价格':   ['价格', '结算价', '收盘价', '最高价', '最低价', '指数', '比值',
                '升贴水', '升水', '贴水', '现货价', '市场价', '均价', '溢价', '折价'],
    '订单':   ['订单', '排产', '接单', '开工订单', '在手订单'],
}
def concept(name):
    if not name: return set()
    name = str(name)
    return {c for c, kws in CONCEPT_KWS.items() if any(k in name for k in kws)}

# ---- 规则2：产业链上下游（品种无关的通用环节词）----
CHAIN_UP   = ['氧化铝', '铜矿', '铜精矿', '硅矿', '硅石', '镍矿', '镍精矿',
              '锌矿', '锌精矿', '铅矿', '铅精矿', '锡矿', '锡精矿', '锂矿', '锂辉石', '锂云母', '矿石']
CHAIN_MID  = ['电解铝', '铝锭', '粗铜', '电解铜', '阴极铜', '工业硅', '金属硅',
              'NPI', 'MHP', '电解镍', '精炼镍', '再生铅', '精炼锌', '电解锌', '精炼锡', '精锡',
              '碳酸锂', '氢氧化锂', '镍铁', '高冰镍']
CHAIN_DOWN = ['铝加工', '铝板带', '铝箔', '铜板带', '铜管', '多晶硅', '有机硅',
              '不锈钢', '铅酸电池', '镀锌', '焊锡', '锡焊料', '正极', '电池']
def chain_level(name):
    if not name: return None
    name = str(name)
    if any(k in name for k in CHAIN_DOWN): return 'down'
    if any(k in name for k in CHAIN_MID):  return 'mid'
    if any(k in name for k in CHAIN_UP):   return 'up'
    return None

# ---- 规则3：地域互斥 ----
OVERSEAS = ['海外', '国外', '全球', '印尼', '美国', '巴西', '南非', '智利', '秘鲁', '蒙古',
            '澳大利亚', '缅甸', '俄罗斯', '菲律宾', '加拿大', '几内亚', '哈萨克斯坦', '马来西亚']
DOMESTIC = ['中国', '国内', '广西', '云南', '四川', '新疆', '内蒙', '江苏', '山东',
            '安徽', '湖南', '浙江', '广东', '上海', '宁夏', '青海', '江西', '河南']
def geo_mismatch(target, cand):
    """目标要求海外，候选只有国内 → True（反之不互斥，国内指标可覆盖）"""
    t_ov = any(w in str(target) for w in OVERSEAS)
    c_ov = any(w in str(cand)  for w in OVERSEAS)
    if t_ov and not c_ov:
        # 特例：全球总量（ILZSG/USGS 全球）算海外可接受
        if any(w in str(cand) for w in ['全球', '世界']):
            return False
        return True
    return False

# ---- 规则4：同义词展开（改良搜索词生成）----
SYNONYMS = {
    '加工费': ['加工费', 'TC', 'RC'],
    'TC':     ['TC', '加工费', 'TC指数'],
    '进口量': ['进口量', '进口数量', '进口', '进口总量'],
    '库存':   ['库存', '社库', '厂库', '仓单'],
    '社会库存': ['社会库存', '社库', '现货库存', '库存'],
    '开工率': ['开工率', '产能利用率', '利用率'],
    '硅矿':   ['硅石', '硅矿', '石英矿', '金属硅 原料'],
    '工业硅': ['工业硅', '金属硅'],
    '铝锭':   ['铝锭', '电解铝'],
    '电解铝': ['电解铝', '铝锭', '原铝'],
    '镍精矿': ['镍精矿', '镍矿', '镍 精矿'],
    '海外':   ['全球', '海外', '国外'],
}
def gen_keywords_v4(target, variety_cn):
    target = str(target)
    kws = []
    # 1) 原词整句（拆空格）
    kws.append(' '.join([variety_cn, target]))
    # 2) 按分隔符拆词组合
    parts = [p for p in re.split(r'[\s（）/、，,·：:]+', target) if len(p) >= 2]
    if parts:
        kws.append(' '.join([variety_cn] + parts[:2]))
        if len(parts) > 2:
            kws.append(' '.join([variety_cn, parts[0], parts[-1]]))
    # 3) 同义词替换
    for kw_old, kws_new in SYNONYMS.items():
        if kw_old in target:
            for syn in kws_new:
                t2 = target.replace(kw_old, syn)
                if t2 != target:
                    kws.append(' '.join([variety_cn, t2]))
                    break
    # 4) 地域展开：海外 → 主要产地
    if '海外' in target:
        kws.append(' '.join([variety_cn, '全球', '产量']))
        kws.append(' '.join([variety_cn, '产量', '全球']))
    # 5) 平台前缀（若目标含交易所/平台名）
    for abbr in ['LME', 'SHFE', 'SMM', 'COMEX', 'Mysteel', 'ILZSG', 'USGS']:
        if abbr.lower() in target.lower():
            kws.append(f"{abbr} {variety_cn} {target}")
            break
    # 去重，最多 8 个
    seen, out = set(), []
    for kw in kws:
        if kw not in seen:
            seen.add(kw); out.append(kw)
    return out[:8]

# ---- 知几 API 调用（1 秒限频 + 缓存）----
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

# ---- 规则5：遍历前10条 + 品种词&核心词双匹配 ----
def seg(s):
    return [x for x in re.split(r'[:：\s/\-（）()]', str(s)) if len(x) >= 2]

def strong_match(target, zhj_name, variety_cn):
    """A 级判定：品种词 + 至少一个>=3字核心词双命中 + 概念维度兼容"""
    if not zhj_name: return False
    # 品种词匹配（精确，不允许单字简称——"硅"命中"磷锂铝石"是假阳性）
    vn = variety_cn
    if vn == '工业硅':
        if '工业硅' not in zhj_name and '金属硅' not in zhj_name: return False
    elif vn == '碳酸锂':
        if '碳酸锂' not in zhj_name and '锂' not in zhj_name.split('：')[0]: return False
    elif vn not in zhj_name:
        return False
    sa, sb = seg(target), seg(zhj_name)
    core = [x for x in sa if len(x) >= 3]
    if not core: return False
    hit = any(x == y or (len(x) >= 3 and (x in y or y in x)) for x in core for y in sb)
    if not hit: return False
    # 概念互斥最后一道闸
    ct, cc = concept(target), concept(zhj_name)
    if ct and cc and not (ct & cc):
        return False
    return True

# ---- 主流程 ----
def recheck(variety, dry_run=False):
    vn = VARIETY_CN.get(variety, variety)
    in_path = IN_DIR / f'{variety}_zhiji_match.json'
    if not in_path.exists():
        print(f'  [!] 缺输入 {in_path}'); return None
    data = json.load(open(in_path, encoding='utf-8'))
    matches = data.get('matches', [])
    reuse = Counter(m['zhiji_id'] for m in matches if m.get('zhiji_id') and m['match_level'] in ('A', 'B'))

    stats = Counter(); replaced = []
    out_matches = []
    for m in matches:
        lvl = m.get('match_level', 'C')
        target = m.get('iwencai_indicator', '')
        cand_name = m.get('zhiji_name') or ''
        cand_id = m.get('zhiji_id')

        if lvl == 'A':
            # 防御性检查（已审过，一般不动）
            if cand_id and reuse.get(cand_id, 0) > 3:
                m['notes'] = (m.get('notes') or '') + '; ⚠️REUSE>3 需人工复核'
            out_matches.append(m); stats['A保留'] += 1; continue

        if lvl == 'C':
            out_matches.append(m); stats['C保留'] += 1; continue

        # ---- B 级：三道互斥检查 ----
        ct = concept(target)
        cc = concept(cand_name)
        chk = []
        if ct and cc and not (ct & cc):
            chk.append('概念不符')
        cl_t, cl_c = chain_level(target), chain_level(cand_name)
        if cl_t and cl_c and cl_t != cl_c:
            chk.append(f'环节不符({cl_t}≠{cl_c})')
        if geo_mismatch(target, cand_name):
            chk.append('地域不符')

        if not chk and cand_id and series_nonempty(cand_id):
            # 概念相符 + series 有数 → 真弱匹配，保留 B（仅频率/口径差异）
            m['notes'] = (m.get('notes') or '') + '; v4保留:概念相符series非空'
            out_matches.append(m); stats['B保留(真弱匹配)'] += 1
            continue

        # ---- 需要重搜 ----
        reason = '; '.join(chk) if chk else 'series空'
        found = None
        for kw in gen_keywords_v4(target, vn):
            d = search(kw)
            if not d or not d.get('results'): continue
            for r in d['results'][:10]:
                rid, rname = r.get('id'), r.get('name', '')
                if not rid or not rname: continue
                if strong_match(target, rname, vn) and series_nonempty(rid):
                    found = {'zhiji_id': rid, 'zhiji_name': rname,
                             'zhiji_unit': r.get('unit', ''),
                             'match_level': 'A', 'verified': True,
                             'notes': f'v4重搜命中(原B因:{reason}); 搜索词:{kw}'}
                    break
            if found: break

        if found:
            if reuse.get(found['zhiji_id'], 0) > 3:
                found['notes'] += '; ⚠️REUSE>3 需人工复核'
            nm = dict(m); nm.update(found); nm['zhiji_freq'] = m.get('zhiji_freq')
            out_matches.append(nm); stats['B升级A'] += 1
            replaced.append((target, cand_name, found['zhiji_name'], found['zhiji_id'], reason))
        else:
            nm = dict(m)
            nm['zhiji_id'] = None; nm['zhiji_name'] = None
            nm['zhiji_freq'] = None; nm['zhiji_unit'] = None
            nm['match_level'] = 'C'; nm['verified'] = False
            nm['notes'] = f"v4降级C:{reason}; 知几无此指标需外部源"
            out_matches.append(nm); stats['B降级C'] += 1

    print(f'\n=== {variety} 重判结果 ===')
    for k, v in stats.most_common(): print(f'  {k}: {v}')
    print(f'\n  升级明细（{len(replaced)}条）：')
    for t, old, new, nid, reason in replaced[:20]:
        print(f'    [{t}]\n      ✗ {old}\n      ✓ {new} ({nid}) [因:{reason}]')

    if not dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        data['matches'] = out_matches
        data['_meta'] = data.get('_meta', {})
        data['_meta']['v4_recheck'] = dict(stats)
        data['_meta']['recheck_date'] = time.strftime('%Y-%m-%d %H:%M')
        out_path = OUT_DIR / f'{variety}_zhiji_match_v4.json'
        json.dump(data, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'  ✅ 写入 {out_path}')
    return stats

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--variety', default='')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    vs = [args.variety] if args.variety else list(VARIETY_CN)
    total = Counter()
    for v in vs:
        st = recheck(v, args.dry_run)
        if st: total.update(st)
    print('\n===== 汇总 =====')
    for k, v in total.most_common(): print(f'  {k}: {v}')
