#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_export_import.py — 评审批次批量导出/导入脚本

工单: HERMES_V85_PORTAL_FINAL_INTEGRATE_GATE_FULL_CHECK_AND_REVIEW_BATCH_PACKAGE

功能:
  1. 批量导出待人工评审条目（按批次/品种/风险筛选）
  2. 批量导入人工填写后的zhiji_id和评审结论
  3. 自动更新门户manifest

约束(T4):
  - 不调用zhiji API
  - 原始模板只读
  - 仅新增/更新manifest文件

用法:
  # 导出Batch-A待评审
  python3 batch_export_import.py --export batch_A --out review_to_fill.csv

  # 导出特定品种+风险
  python3 batch_export_import.py --export batch_C --filter variety=NI,risk=P0 --out ni_p0.csv

  # 导入评审结果
  python3 batch_export_import.py --import review_filled.csv --manifest manifest.json

  # 导出别名
  python3 batch_export_import.py --export-alias --variety NI --out ni_aliases.csv
"""

import json
import csv
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


ZHIJI_ID_PATTERN = re.compile(r'^ID[a-zA-Z0-9_]+$')


def load_batch_csv(path: str) -> List[Dict]:
    """加载批次CSV"""
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def export_batch(batch_name: str, batch_dir: str,
                 filter_str: Optional[str] = None,
                 out_path: Optional[str] = None) -> Dict:
    """
    导出批次待评审条目。

    Args:
        batch_name: batch_A / batch_B / batch_C
        batch_dir: review_batches_v5/ 目录
        filter_str: 筛选条件 "key=val,key2=val2"
        out_path: 输出CSV路径
    """
    csv_path = os.path.join(batch_dir, f'{batch_name}_review_v5.csv')
    if not os.path.exists(csv_path):
        return {'error': f'批次文件不存在: {csv_path}'}

    rows = load_batch_csv(csv_path)

    # 筛选
    if filter_str:
        filters = {}
        for pair in filter_str.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                filters[k.strip()] = v.strip()

        filtered = []
        for row in rows:
            match = True
            for k, v in filters.items():
                if row.get(k, '') != v:
                    match = False
                    break
            if match:
                filtered.append(row)
        rows = filtered

    # 输出
    if not out_path:
        out_path = f'{batch_name}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    return {
        'batch': batch_name,
        'exported': len(rows),
        'filters': filter_str or 'none',
        'output': out_path,
    }


def import_review(review_csv: str, manifest_path: str,
                   output_path: Optional[str] = None) -> Dict:
    """
    导入人工评审结果到manifest。

    评审CSV格式: template_id,series_index,manual_zhiji_id,decision,remark,reviewer,review_time
    """
    # 加载评审结果
    review_rows = []
    with open(review_csv, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            review_rows.append(row)

    # 加载manifest
    with open(manifest_path) as f:
        manifest = json.load(f)

    # 应用回写
    applied = 0
    skipped = 0
    warnings = 0
    errors = 0

    # 构建评审索引
    review_index = {}
    for r in review_rows:
        tid = r.get('template_id', '').strip()
        si = r.get('series_index', '').strip()
        if tid and si:
            review_index[(tid, si)] = r

    # 遍历manifest
    for gk, gdata in manifest.get('render_groups', {}).items():
        for task in gdata.get('tasks', []):
            tid = task.get('template_id', '')
            # 查找该模板的所有评审结果
            for (rtid, rsi), review in review_index.items():
                if rtid == tid:
                    manual_id = review.get('manual_zhiji_id', '').strip()
                    decision = review.get('decision', '').strip()

                    if manual_id:
                        # zhiji_id格式校验
                        if ZHIJI_ID_PATTERN.match(manual_id):
                            task.setdefault('manual_overrides', {})
                            task['manual_overrides'][f'series_{rsi}'] = {
                                'zhiji_id': manual_id,
                                'decision': decision,
                                'remark': review.get('remark', ''),
                                'reviewer': review.get('reviewer', ''),
                                'review_time': review.get('review_time', ''),
                                'imported_at': datetime.now().isoformat(),
                            }
                            applied += 1

                            # 根据decision更新路由
                            if decision == '通过':
                                task['status'] = 'REVIEWED_APPROVED'
                            elif decision == '驳回':
                                task['status'] = 'REVIEWED_REJECTED'
                            elif decision == '临时白名单放行':
                                task['status'] = 'WHITELISTED'
                        else:
                            warnings += 1
                    elif decision:
                        # 有decision但无zhiji_id
                        task['status'] = f'REVIEWED_{decision.upper()}'
                        applied += 1
                    else:
                        skipped += 1

    # 更新manifest版本
    manifest['v5_update'] = {
        'updated_at': datetime.now().isoformat(),
        'applied': applied,
        'skipped': skipped,
        'warnings': warnings,
        'source': review_csv,
    }

    # 写入
    if not output_path:
        output_path = manifest_path.replace('.json', '_v5_updated.json')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return {
        'applied': applied,
        'skipped': skipped,
        'warnings': warnings,
        'errors': errors,
        'output': output_path,
        'review_source': review_csv,
    }


def export_alias(alias_csv: str, variety: Optional[str] = None,
                 out_path: Optional[str] = None) -> Dict:
    """导出别名库（可按品种筛选）"""
    rows = []
    with open(alias_csv, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if variety and row.get('variety', '') != variety:
                continue
            rows.append(row)

    if not out_path:
        suffix = f'_{variety}' if variety else '_all'
        out_path = f'alias_export{suffix}_{datetime.now().strftime("%Y%m%d")}.csv'

    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    return {'exported': len(rows), 'variety': variety or 'all', 'output': out_path}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='评审批次批量导出/导入')
    parser.add_argument('--export', help='导出批次: batch_A / batch_B / batch_C')
    parser.add_argument('--import', dest='import_csv', help='导入评审结果CSV')
    parser.add_argument('--manifest', help='manifest JSON路径')
    parser.add_argument('--filter', help='筛选条件: key=val,key2=val2')
    parser.add_argument('--out', help='输出文件路径')
    parser.add_argument('--export-alias', action='store_true', help='导出别名库')
    parser.add_argument('--variety', help='品种筛选')
    args = parser.parse_args()

    # 默认路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    batch_dir = os.path.join(base_dir, 'review_batches_v5')
    alias_csv = os.path.join(base_dir, 'indicator_alias_library.csv')

    if args.export:
        result = export_batch(args.export, batch_dir, args.filter, args.out)
        print(f"导出完成: {result.get('exported', 0)}条 → {result.get('output','')}")
        return

    if args.import_csv and args.manifest:
        result = import_review(args.import_csv, args.manifest, args.out)
        print(f"导入完成: 应用{result['applied']} / 跳过{result['skipped']} / 警告{result['warnings']}")
        print(f"输出: {result['output']}")
        return

    if args.export_alias:
        result = export_alias(alias_csv, args.variety, args.out)
        print(f"别名导出: {result['exported']}条 → {result['output']}")
        return

    parser.print_help()


if __name__ == '__main__':
    main()
