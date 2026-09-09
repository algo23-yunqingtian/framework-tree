#!/usr/bin/env python3
"""周报指标入库 v2：用清洗后的 276 条**整体替换**旧的 205 条 wr* 指标。

策略：
  1. 删除所有旧 wr* 键（旧版是简单过滤，没做过清洗）
  2. 重新编号 wr1..wr276 并写入
  3. 保留非 wr 的所有既有指标（零触碰）
  4. version v3.76 → v3.77，changelog 留全链路记录
  5. 幂等：可重复执行（每次都从当前文件删除 wr* 再重写）

回退：
  git reset --hard PRE_WEEKLY_REPORT_IMPORT_20260909   # 回到周报导入前（1308 键 v3.75）
  git reset --hard d79010e                             # 回到旧 205 条版本（v3.76）
"""
import json, sys, os, re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
DST = ROOT / 'data' / 'indicators_v1.json'
SRC = '/tmp/wr_extract/final_clean.jsonl'
BAK = DST.with_name('indicators_v1.json.bak_pre_wr20260909_v2')
APPLY = '--apply' in sys.argv

# 品种 → 代码（沿用 v3.76 的 AL-AX 约定）
VAR_CODE = {
    '铝': 'AL', '氧化铝': 'AL-AX', '碳酸锂': 'LI',
    '锡': 'SN', '硅产业链': 'SI', '镍与不锈钢': 'NI',
}

def build_entry(r, n):
    """构造入库条目，schema 与 v3.76 一致"""
    key = f'wr{n}'
    code = VAR_CODE.get(r['variety'], 'X')
    # 清洗后保留标记
    return key, {
        'name': r['chart'],
        'unit': '',
        'freq': '',
        'verified': False,
        'category': 'weekly_report_import',
        'ids': {code: r['zhiji_id']},
        'weekly_report_import': {
            'date': '2026-09-09',
            'variety': r['variety'],
            'module': r['module'],
            'indicator_no': r.get('indicator_no',''),
            'zhiji_name': r['zhiji_name'],
            'zhiji_source': r.get('zhiji_source',''),
            'fix_tag': r.get('fix_tag',''),
            'fix_score': r.get('fix_score',0),
            'fix_issues': r.get('fix_issues',''),
            'old_zhiji_id': r.get('old_zhiji_id',''),
            'freq_report': r.get('freq_report',''),
            'pres': r.get('pres',''),
            'chart_type': r.get('chart_type',''),
            'legend_count': r.get('legend_count',''),
            'is_seasonal': r.get('is_seasonal',''),
            'report_status': r.get('report_status',''),
            'source_file': 'algo23-yunqingtian/weekly-report-tree/_HANDOVER_PACKAGE.md',
            'source_url': 'https://github.com/algo23-yunqingtian/weekly-report-tree/blob/main/_HANDOVER_PACKAGE.md',
        }
    }

def main():
    d = json.load(open(DST))
    n_before = len(d)

    # 1. 删除所有旧 wr*
    old_wr = sorted([k for k in d if k.startswith('wr')],
                    key=lambda x: int(re.sub(r'\D','',x)))
    for k in old_wr:
        del d[k]

    # 2. 写入新 276 条（保持清洗顺序：verified → corrected → cleaned_name → re_matched 按品种）
    recs = [json.loads(l) for l in open(SRC)]
    for n, r in enumerate(recs, 1):
        key, entry = build_entry(r, n)
        d[key] = entry

    # 3. 版本与 changelog
    d['version'] = 'v3.77'
    nl = len(d)
    from collections import Counter
    c_tag = Counter(r.get('fix_tag','') for r in recs)
    c_var = Counter(r.get('variety','') for r in recs)

    d.setdefault('changelog', []).append({
        'date': str(date.today()),
        'version': 'v3.77',
        'change': f'周报指标清洗入库：整体替换旧 205 条 → 清洗后 276 条（去重 ID、品种/子类别/地区/类型四维度约束、ID 反查真名验证）',
        'details': {
            'keys_before': n_before, 'keys_after': nl,
            'old_wr_removed': len(old_wr), 'new_wr_added': len(recs),
            'fix_tags': dict(c_tag),
            'by_variety': dict(c_var),
            'replaced_version': 'v3.76(205条)',
            'note': '清洗引擎修掉了 90 条 ID 错配（如"碳酸锂产量:新疆"从原煤改回碳酸锂），清洗 72 条多候选污染名称列；94 条上轮入库但本轮判定不合格已剔除',
        }
    })

    print(f'═══ 周报入库 v2 {"(--dry-run)" if not APPLY else "(--apply)"} ═══')
    print(f'  旧 wr* 删除: {len(old_wr)} 条')
    print(f'  新 wr* 写入: {len(recs)} 条（wr1..wr{len(recs)}）')
    print(f'  键数: {n_before} → {nl}')
    print(f'  版本: v3.76 → v3.77')
    print(f'\n  fix_tag 分布: {dict(c_tag)}')
    print(f'  按品种: {dict(c_var)}')

    # 非 wr 键完整性校验（排除 version/changelog 这两个顶层元数据键 —— 它们是设计要改的）
    META_KEYS = {'version','changelog'}
    old_src = json.load(open(DST))
    old_non_wr = {k:v for k,v in old_src.items() if not k.startswith('wr') and k not in META_KEYS}
    new_non_wr = {k:v for k,v in d.items() if not k.startswith('wr') and k not in META_KEYS}
    same = all(old_non_wr.get(k)==v for k,v in new_non_wr.items()) and len(old_non_wr)==len(new_non_wr)
    print(f'\n  非 wr 指标键完整性({len(new_non_wr)} 个): {"✓ 完全一致" if same else "✗ 异常!"}')
    if not same:
        # 打印差异定位
        for k in set(old_non_wr) ^ set(new_non_wr):
            print(f'    键差异: {k}')
        print('  终止（数据损坏风险）'); sys.exit(1)

    if not APPLY:
        print('\n[dry-run] 未写入，加 --apply 执行')
        return

    if BAK.exists():
        print(f'\n  备份已存在，保留: {BAK.name}')
    else:
        import shutil
        shutil.copy2(DST, BAK)
        print(f'\n  备份: {BAK} ({BAK.stat().st_size/1024:.0f} KB)')

    with open(DST,'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'  写入完成: {DST}')

if __name__ == '__main__':
    main()
