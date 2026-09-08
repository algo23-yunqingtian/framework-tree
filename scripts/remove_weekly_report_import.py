#!/usr/bin/env python3
"""移除 indicators_v1.json 中的周报导入指标（wr* 前缀）。

用法:
  python3 scripts/remove_weekly_report_import.py            # 先显示要删什么
  python3 scripts/remove_weekly_report_import.py --apply    # 真正删除

这是入库脚本 import_weekly_report_indicators.py 的逆操作。
更彻底的回退方式（连版本号一起回退）:
  git reset --hard PRE_WEEKLY_REPORT_IMPORT_20260909
"""
import json, sys, os, shutil

# 用仓库根目录相对路径，防止在 /tmp clone 里测试时误打主仓库
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
DST = str(ROOT / 'data/indicators_v1.json')
DRY_RUN = '--apply' not in sys.argv

def main():
    ft = json.load(open(DST))
    ver_before = ft.get('version')
    wr_keys = [k for k in ft if k.startswith('wr')]

    print(f'当前: {len(ft)} 键 / {ver_before}')
    print(f'将移除 wr* 周报导入指标: {len(wr_keys)} 条')
    if wr_keys:
        print(f'  范围: {wr_keys[0]} → {wr_keys[-1]}')
        # 按品种统计
        from collections import Counter
        vc = Counter(ft[k].get('weekly_report_import',{}).get('variety','?') for k in wr_keys)
        print(f'  按品种: {dict(vc)}')

    if not wr_keys:
        print('\n没有 wr* 键，无需操作。')
        return

    print(f'\n移除后: {len(ft)-len(wr_keys)} 键')
    if DRY_RUN:
        print('\n[DRY RUN] 未修改文件。加 --apply 真正删除。')
        return

    # 备份
    bak = DST + f'.bak_pre_remove_wr_{__import__("datetime").date.today().isoformat()}'
    shutil.copy2(DST, bak)
    print(f'\n已备份 → {bak}')

    for k in wr_keys:
        del ft[k]

    # changelog 记一笔
    ft['changelog'] = ft.get('changelog', [])
    if isinstance(ft['changelog'], list):
        ft['changelog'].insert(0, {
            'version': ver_before,
            'date': __import__('datetime').date.today().isoformat(),
            'change': f'移除周报导入指标 {len(wr_keys)} 条（wr* 前缀）',
        })
        ft['changelog'] = ft['changelog'][:50]

    tmp = DST + '.tmp'
    with open(tmp,'w') as f:
        json.dump(ft, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DST)

    print(f'完成: {len(ft)} 键')

if __name__ == '__main__':
    main()
