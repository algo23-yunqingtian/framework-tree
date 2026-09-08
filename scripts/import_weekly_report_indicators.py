#!/usr/bin/env python3
"""把周报框架树验证通过的指标入库 framework-tree/data/indicators_v1.json。

设计原则：
1. 可回退：入库前先备份原文件，commit 前 git 有 tag 锚点 PRE_WEEKLY_REPORT_IMPORT_20260909
2. 只追加不修改：绝不改动任何既有键，新指标一律用 wr<序号> 命名空间
3. 留痕：每条记录带 weekly_report_import 元数据，便于反向追溯与批量移除
4. 版本号：v3.75 → v3.76，并写 changelog

移除命令（回退用）：
  python3 scripts/remove_weekly_report_import.py
"""
import json, sys, os, shutil, subprocess
from datetime import date

SRC = '/tmp/wr_extract/verified_final.jsonl'
# 用仓库根目录相对路径，防止在 /tmp clone 里测试时误打主仓库
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
DST = str(ROOT / 'data/indicators_v1.json')
BAK = str(pathlib.Path(DST).with_suffix('.json.bak_pre_wr20260909'))
CHANGED = '/tmp/wr_extract/import_changes.jsonl'
DRY_RUN = '--apply' not in sys.argv

# 频率映射（周报中文 → 仓库既有英文枚举）
FREQ_MAP = {'日':'daily','日度':'daily','周':'weekly','周度':'weekly',
            '月':'monthly','月度':'monthly','季':'quarterly','季度':'quarterly',
            '年':'annual','年度':'annual','季月':'quarterly','周/月':'weekly'}

# 模块 → category（对齐仓库既有 category 枚举）
def to_category(module, chart):
    m = (module or '') + (chart or '')
    for kw, cat in [
        ('库存','inventory'), ('仓单','inventory'),
        ('产量','supply'), ('产能','supply'), ('开工','supply'),
        ('矿端','supply'), ('供应','supply'), ('冶炼','supply'),
        ('出口','trade'), ('进口','trade'), ('进出口','trade'), ('贸易','trade'),
        ('成本','cost'), ('利润','cost'), ('加工费','cost'), ('成本结构','cost'),
        ('消费','demand'), ('需求','demand'), ('装机','demand'), ('终端','demand'),
        ('平衡','balance'),
    ]:
        if kw in m: return cat
    if '价格' in m or '盘面' in m or '价差' in m or '期货' in m or '基差' in m or '升贴水' in m:
        return 'price'
    return 'other'

def to_freq(f):
    return FREQ_MAP.get((f or '').strip(), 'unknown')

def main():
    recs = [json.loads(l) for l in open(SRC)]
    ft = json.load(open(DST))
    ver_before = ft.get('version')

    print(f'读入验证通过指标 {len(recs)} 条')
    print(f'目标文件 {DST} 现有 {len(ft)} 键 / {ver_before}')

    # 备份（仅 --apply 时）
    if not DRY_RUN:
        shutil.copy2(DST, BAK)
        print(f'已备份 → {BAK}')

    # 计算已有最大序号，避免与未来编号冲突
    existing_wr = [int(k[2:]) for k in ft if k.startswith('wr')]
    next_no = (max(existing_wr) + 1) if existing_wr else 1

    added, skipped = 0, 0
    changes = []
    for r in recs:
        key = f'wr{next_no}'
        entry = {
            'name': r['chart'],                  # 用周报的图表名作人类可读名
            'unit': '',                          # 周报未提供单位，留空待补
            'freq': to_freq(r['freq_report']),
            'verified': False,                   # 未经 series 拉数验证，保守标 false
            'category': to_category(r['module'], r['chart']),
            'ids': {r['code']: r['zhiji_id']},
            # ↓ 元数据：用于批量移除与追溯
            'weekly_report_import': {
                'date': '2026-09-09',
                'variety': r['variety'],
                'module': r['module'],
                'indicator_no': r['indicator_no'],
                'zhiji_name': r['zhiji_name'],
                'zhiji_source': r['zhiji_source'],
                'freq_report': r['freq_report'],
                'pres': r['pres'],
                'chart_type': r['chart_type'],
                'legend_count': r['legend_count'],
                'is_seasonal': r['is_seasonal'],
                'report_status': r['report_status'],
                'is_new_to_ft': r['is_new_to_ft'],
                'source_file': 'algo23-yunqingtian/weekly-report-tree/_HANDOVER_PACKAGE.md',
            },
        }
        ft[key] = entry
        next_no += 1
        added += 1
        changes.append({'key': key, 'code': r['code'], 'chart': r['chart'],
                        'zhiji_id': r['zhiji_id'], 'zhiji_name': r['zhiji_name'],
                        'category': entry['category'], 'freq': entry['freq'],
                        'is_new_to_ft': r['is_new_to_ft']})

    # 版本号 bump
    major_minor = ver_before.replace('v','') if ver_before else '3.75'
    try:
        ma, mi = major_minor.split('.')
        new_ver = f'v{ma}.{int(mi)+1}'
    except Exception:
        new_ver = 'v3.76'
    ft['version'] = new_ver
    ft['changelog'] = ft.get('changelog', [])
    if isinstance(ft['changelog'], list):
        ft['changelog'].insert(0, {
            'version': new_ver,
            'date': '2026-09-09',
            'change': f'导入周报指标框架树 {added} 条（来源: weekly-report-tree, 净增量 {sum(1 for c in changes if c.get("is_new_to_ft"))} 条）',
        })
        # changelog 最多保留 50 条，防止文件膨胀
        ft['changelog'] = ft['changelog'][:50]
    elif isinstance(ft['changelog'], dict):
        ft['changelog'][new_ver] = f'导入周报指标框架树 {added} 条（来源: weekly-report-tree）'

    print(f'\n=== 变更摘要 ===')
    print(f'新增指标键: {added}')
    print(f'版本号: {ver_before} → {new_ver}')
    print(f'总键数: {len(ft)-added} → {len(ft)}')

    if not DRY_RUN:
        tmp = DST + '.tmp'
        with open(tmp,'w') as f:
            json.dump(ft, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DST)
        print(f'\n已写入: {DST}')
    else:
        print('\n[DRY RUN] 未写入磁盘')

    with open(CHANGED,'w') as f:
        for c in changes:
            f.write(json.dumps(c, ensure_ascii=False, separators=(',',':'))+'\n')
    print(f'变更清单: {CHANGED} ({len(changes)} 条)')

if __name__ == '__main__':
    main()
