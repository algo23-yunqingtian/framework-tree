#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ths_candidate_mapping.py — THS指标映射预处理 v2（静态文本相似度召回）

工单: HERMES_V85_THS_INDICATOR_MAPPING_PREP_AND_GATE_GAP_PLAN

v2 改进:
  - 提取指标库全部指标（含无zhiji_id的，作为名称候选）
  - 品种强制约束: THS系列名中的品种词 与 指标库品种 严格匹配
  - 更好的归一化,同义词映射

约束(T4): 禁止调zhiji接口/拉时序; indicators_v1.json只读; 仅新增文件
"""
import json
import re
import sys
import csv
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# 品种词表: 中文词 -> 品种代码
VARIETY_WORDS = {
    '铝': 'AL', '沪铝': 'AL', '电解铝': 'AL', '氧化铝': 'AL', '铝锭': 'AL', '铝棒': 'AL',
    '铅': 'PB', '沪铅': 'PB', '再生铅': 'PB', '原铅': 'PB',
    '锌': 'ZN', '沪锌': 'ZN', '电解锌': 'ZN', '镀锌': 'ZN', '氧化锌': 'ZN', '锌锭': 'ZN',
    '铜': 'CU', '沪铜': 'CU', '电解铜': 'CU', '铜杆': 'CU',
    '镍': 'NI', '沪镍': 'NI', '电解镍': 'NI', '硫酸镍': 'NI', '镍铁': 'NI', '冰镍': 'NI',
    '锡': 'SN', '沪锡': 'SN', '锡锭': 'SN', '锡矿': 'SN', '锡精矿': 'SN',
    '硅': 'SI', '沪硅': 'SI', '工业硅': 'SI', '多晶硅': 'SI', '金属硅': 'SI',
    '锂': 'LI', '碳酸锂': 'LI', '氢氧化锂': 'LI', '锂矿': 'LI', '锂辉石': 'LI', '锂云母': 'LI',
}

# THS 品种代码词（THS模板品种代码已经是 AL/PB/ZN/...）
THS_VARIETY_NAME = {
    'AL': '铝', 'PB': '铅', 'ZN': '锌', 'CU': '铜',
    'NI': '镍', 'SN': '锡', 'SI': '硅', 'LI': '锂',
}

# 单位清洗
UNIT_RE = re.compile(r'(元/吨|元/kg|美元/吨|万吨|万张|元/公斤|元/金/吨|元|%|％|倍|张)')
SEAS_PATTERN = re.compile(r'[（(][^）)]*[)）]')

NOISE_WORDS = ['左右', '约', '等', '合计', '总量', '同比', '环比',
               '上期', '本期', '往年', '海内外']


def normalize(name):
    if not name:
        return ''
    s = name.strip()
    # 去括号内容（单位/国别/注释）
    s = re.sub(r'[（(][^）)]*[)）]', '', s)
    # 去单位词
    s = UNIT_RE.sub('', s)
    s = s.replace('（', '(').replace('）', ')').replace('：', ':')
    s = re.sub(r'[\s\-_/]', '', s)
    for w in NOISE_WORDS:
        s = s.replace(w, '')
    return s


def detect_variety(name, fallback=''):
    """从中文名检测品种代码"""
    for word, code in VARIETY_WORDS.items():
        if word in name:
            return code
    # 兜底: 若字面含代码
    norm = name.upper()
    for code in ['AL', 'PB', 'ZN', 'CU', 'NI', 'SN', 'SI', 'LI']:
        if code in norm:
            return code
    return fallback


def similarity(a, b):
    """标准化文本相似度 0-100，相比 v1 更严格：要求同品种优先"""
    if not a or not b:
        return 0.0
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 100.0
    # 子串匹配
    if na in nb or nb in na:
        shorter = min(len(na), len(nb))
        base = 100.0 * shorter / max(len(na), len(nb))
        return round(base, 2)
    # SequenceMatcher
    ratio = SequenceMatcher(None, na, nb).ratio() * 100
    return round(ratio, 2)


def score_with_variety(orig_name, ind_name):
    """
    综合评分: 名称相似度 + 品种一致性约束
    品种一致权重高，品种冲突强制降权。
    """
    # 基础相似度
    s = similarity(orig_name, ind_name)
    if s == 0:
        return 0.0

    # 检测 THS 名称品种 与 指标库名称品种
    ths_v = detect_variety(orig_name)
    ind_v = detect_variety(ind_name)

    if ths_v and ind_v:
        if ths_v == ind_v:
            s *= 1.3
            s = min(s, 100)
        else:
            s *= 0.3  # 品种冲突，强力降权
    elif not ths_v and not ind_v:
        pass
    elif not ths_v:
        # THS无品种词，不惩罚
        pass
    elif not ind_v:
        # 指标无品种词（通用指标），不过分惩罚
        s *= 0.9

    return round(s, 2)


def load_indicators(indicators_path):
    """提取指标库全部指标(含无id的)"""
    with open(indicators_path, encoding='utf-8') as f:
        ind = json.load(f)

    result = {}  # id -> {name, zhiji_by_variety}
    auto_id = 0

    def walk(obj, key=''):
        nonlocal auto_id
        if isinstance(obj, dict):
            # 是否是叶子指标: 有 name, 有 zhiji ids 或 unit/freq
            if 'name' in obj and isinstance(obj['name'], str) and obj['name']:
                # 确定 id: 优先用键名, 否则用 category 合成
                rid = key
                zhi = obj.get('ids', {}) if isinstance(obj.get('ids'), dict) else {}
                has_zhi = any(isinstance(v, str) and v for v in zhi.values())
                if not rid or rid in ('name', 'unit', 'freq', 'verified', 'category', 'ids'):
                    if has_zhi:
                        auto_id += 1
                        rid = f'auto_{auto_id}'
                    else:
                        rid = f'cat_{key}'
                # 只当有名字时入库
                cand = {
                    'name': obj['name'],
                    'zhiji_by_variety': zhi,
                }
                # 避免重复
                if has_zhi or (rid not in result):
                    result[rid] = cand
            # 递归
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    walk(v, k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if isinstance(v, (dict, list)):
                    walk(v, key)

    walk(ind)
    return result


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--ths', required=True)
    ap.add_argument('--indicators', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--topn', type=int, default=5)
    args = ap.parse_args()

    inds = load_indicators(args.indicators)
    with open(args.ths, encoding='utf-8') as f:
        ths = json.load(f)

    print(f'指标库指标数: {len(inds)}')
    total_series = 0
    rows = []

    # 预计算: 每个指标的品种 + 按品种建索引
    variety_index = {}  # code -> list of (id, name)
    inds_scores = {}  # id -> (name, ths_v)
    for nid, ninfo in inds.items():
        n_name = ninfo['name']
        n_v = detect_variety(n_name)
        inds_scores[nid] = (n_name, n_v)
        variety_index.setdefault(n_v, []).append(nid)

    all_ids = list(inds.keys())

    for t in ths:
        cid = t['chart_id']
        variety = t.get('meta', {}).get('variety', '')
        for idx, s in enumerate(t.get('series', [])):
            orig = s.get('original_name') or s.get('name') or ''
            total_series += 1

            # 候选指标池: 优先同品种，否则全库
            orig_v = detect_variety(orig)
            if orig_v and orig_v in variety_index:
                pool = variety_index[orig_v]
            else:
                pool = all_ids

            # 计算评分
            scored = []
            for nid in pool:
                n_name, n_v = inds_scores[nid]
                sc = score_with_variety(orig, n_name)
                if sc > 0:
                    scored.append((sc, nid, inds[nid]))
            scored.sort(key=lambda x: -x[0])
            top = scored[:args.topn]

            best_score = top[0][0] if top else 0
            if best_score >= 70:
                cat = '高置信'
            elif best_score >= 40:
                cat = '模糊待人工确认'
            else:
                cat = '无候选/低置信'

            # 最佳候选 zhiji_id
            best_zhiji = ''
            if top:
                z = top[0][2].get('zhiji_by_variety', {})
                for cur in [variety, '']:
                    v = z.get(cur)
                    if isinstance(v, str) and v:
                        best_zhiji = v
                        break
                if not best_zhiji:
                    for v in z.values():
                        if isinstance(v, str) and v:
                            best_zhiji = v
                            break

            cand_ids = '|'.join(c[1] for c in top)
            cand_scores = '|'.join(str(c[0]) for c in top)
            cand_names = '|'.join(c[2]['name'] for c in top)
            best_name = top[0][2]['name'] if top else ''

            rows.append({
                'ths_chart_id': cid,
                'variety': variety,
                'series_index': idx,
                'original_ths_name': orig,
                'candidate_indicator_ids': cand_ids,
                'candidate_scores': cand_scores,
                'candidate_names': cand_names,
                'best_match_name': best_name,
                'best_match_score': best_score,
                'best_match_zhiji_id': best_zhiji,
                'match_category': cat,
                'zhiji_id_null': 'Y' if not s.get('zhiji_id') else 'N',
            })

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / 'ths_candidate_mapping.csv'
    fields = ['ths_chart_id', 'variety', 'series_index', 'original_ths_name',
              'candidate_indicator_ids', 'candidate_scores', 'candidate_names',
              'best_match_name', 'best_match_score', 'best_match_zhiji_id',
              'match_category', 'zhiji_id_null']
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f'✅ CSV: {csv_path} ({csv_path.stat().st_size} bytes)')
    print(f'   THS series 总数: {total_series}')

    # 统计
    from collections import Counter
    cat_dist = Counter(r['match_category'] for r in rows)
    var_dist = Counter(r['variety'] for r in rows)
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_series': total_series,
        'indicator_library_count': len(inds),
        'category_distribution': dict(cat_dist),
        'variety_distribution': dict(var_dist),
    }
    with open(out_dir / 'ths_mapping_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print('=== 分类统计 ===')
    for c, n in sorted(cat_dist.items(), key=lambda x: -x[1]):
        print(f'  {c}: {n} ({n*100//total_series}%)')
    print('=== 品种分布 ===')
    for v, n in sorted(var_dist.items(), key=lambda x: -x[1]):
        print(f'  {v}: {n}')
    print('✅ 摘要: ths_mapping_summary.json')


if __name__ == '__main__':
    main()