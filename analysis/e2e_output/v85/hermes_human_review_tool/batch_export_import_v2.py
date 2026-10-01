#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_export_import_v2.py — 升级版批量导入导出工具

工单: HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP
升级自: batch_export_import.py v1.0

v2新增:
  1. 批量导出待回填THS条目（Batch-B 155条）
  2. 回填校验规则：别名库校验+高危混淆对校验+跨品种风险强提醒
  3. 回填完成后自动生成变更日志
  4. P0风险工作表导出/导入/处置

约束(T4):
  - 不调用zhiji API
  - 原始ths_adapted_all.json只读，仅生成副本
  - 仅新增文件，不覆盖

用法:
  # 导出Batch-B待回填THS条目
  python3 batch_export_import_v2.py --export-batch B --out ths_to_fill.csv

  # 导入回填结果(含跨品种校验)
  python3 batch_export_import_v2.py --import ths_filled.csv --apply --manifest manifest.json

  # 导出P0风险工作表
  python3 batch_export_import_v2.py --export-risk --out risk_to_fill.csv

  # 筛选P0阻塞风险
  python3 batch_export_import_v2.py --filter-risk blocked --out p0_blocked.csv
"""

import json
import csv
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


ZHIJI_ID_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]+$')


class CrossVarietyChecker:
    """跨品种风险检查器"""

    VARIETY_KEYWORDS = {
        'AL': ['铝', '氧化铝', '电解铝'],
        'AO': ['氧化铝', '铝土矿'],
        'CU': ['铜', '精铜', '电解铜'],
        'LC': ['碳酸锂', '锂', '磷酸铁锂'],
        'LI': ['锂', '碳酸锂', '氢氧化锂'],
        'NI': ['镍', '电解镍', '硫酸镍'],
        'SI': ['硅', '工业硅', '多晶硅'],
        'SN': ['锡', '精锡', '焊锡'],
        'ZN': ['锌', '精锌', '氧化锌'],
    }

    def check(self, indicator_name: str, expected_variety: str) -> List[Dict]:
        """检查指标名是否跨品种"""
        warnings = []
        if not indicator_name or not expected_variety:
            return warnings

        for var, keywords in self.VARIETY_KEYWORDS.items():
            if var == expected_variety:
                continue
            for kw in keywords:
                if kw in indicator_name:
                    warnings.append({
                        'type': 'CROSS_VARIETY',
                        'severity': 'P0',
                        'message': f'指标名含"{kw}"(品种{var})，但模板品种为{expected_variety}',
                        'blacklist_id': 'BL-022',
                        'action': '阻止回填，需人工确认',
                    })
                    break
        return warnings


class AliasChecker:
    """别名库校验器"""

    def __init__(self, alias_csv: Optional[str] = None):
        self.aliases: Dict[str, Dict] = {}
        if alias_csv and os.path.exists(alias_csv):
            self.load(alias_csv)

    def load(self, path: str):
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                ths_name = row.get('ths_indicator_name', '')
                if ths_name:
                    self.aliases[ths_name] = row

    def check(self, indicator_name: str) -> Optional[Dict]:
        return self.aliases.get(indicator_name)


class ConfusionChecker:
    """高危混淆对校验器"""

    def __init__(self, confusion_csv: Optional[str] = None):
        self.pairs: List[Dict] = []
        if confusion_csv and os.path.exists(confusion_csv):
            self.load(confusion_csv)

    def load(self, path: str):
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                self.pairs.append(row)

    def check(self, chart_id: str = '', indicator_name: str = '') -> List[Dict]:
        hits = []
        for pair in self.pairs:
            if chart_id and pair.get('chart_id') == chart_id:
                hits.append(pair)
            elif indicator_name:
                if indicator_name in pair.get('indicator_a', '') or indicator_name in pair.get('indicator_b', ''):
                    hits.append(pair)
        return hits


class BatchExportImportV2:
    """升级版批量导入导出"""

    def __init__(self, base_dir: str = ''):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.cross_checker = CrossVarietyChecker()
        
        # 加载别名库和混淆对
        alias_path = os.path.join(self.base_dir, '..', 'hermes_portal_gate_final', 'indicator_alias_library.csv')
        confusion_path = os.path.join(self.base_dir, '..', 'hermes_portal_gate_final', 'high_risk_confusion_pairs.csv')
        
        self.alias_checker = AliasChecker(alias_path)
        self.confusion_checker = ConfusionChecker(confusion_path)
        
        self.change_log: List[Dict] = []

    def export_batch(self, batch_name: str, out_path: str,
                     filter_str: Optional[str] = None) -> Dict:
        """导出批次待评审条目"""
        batch_dir = os.path.join(self.base_dir, 'review_batches_v6')
        csv_path = os.path.join(batch_dir, f'{batch_name}_review_v6.csv')
        
        if not os.path.exists(csv_path):
            # 回退到v5
            batch_dir = os.path.join(self.base_dir, '..', 'hermes_portal_gate_final', 'review_batches_v5')
            csv_path = os.path.join(batch_dir, f'{batch_name}_review_v5.csv')
        
        if not os.path.exists(csv_path):
            return {'error': f'批次文件不存在: {csv_path}'}

        rows = []
        with open(csv_path, encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))

        # 筛选
        if filter_str:
            filters = {}
            for pair in filter_str.split(','):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    filters[k.strip()] = v.strip()
            rows = [r for r in rows if all(r.get(k) == v for k, v in filters.items())]

        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

        return {'exported': len(rows), 'output': out_path}

    def export_risk_workbook(self, out_path: str,
                             filter_str: Optional[str] = None) -> Dict:
        """导出P0风险工作表"""
        risk_csv = os.path.join(self.base_dir, 'v85_p0_risk_human_workbook.csv')
        
        if not os.path.exists(risk_csv):
            return {'error': f'风险工作表不存在: {risk_csv}'}

        rows = []
        with open(risk_csv, encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))

        # 筛选
        if filter_str:
            if 'blocked' in filter_str:
                rows = [r for r in rows if r.get('gate_blocked') == 'YES']
            elif 'variety=' in filter_str:
                variety = filter_str.split('=')[1]
                rows = [r for r in rows if r.get('variety') == variety]

        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

        return {'exported': len(rows), 'output': out_path}

    def import_with_validation(self, review_csv: str,
                                 manifest_path: str,
                                 output_path: Optional[str] = None) -> Dict:
        """
        导入评审结果（含跨品种校验+别名校验+混淆预警）。
        """
        # 加载评审结果
        review_rows = []
        with open(review_csv, encoding='utf-8-sig') as f:
            review_rows = list(csv.DictReader(f))

        # 加载manifest
        with open(manifest_path) as f:
            manifest = json.load(f)

        applied = 0
        skipped = 0
        warnings = 0
        cross_variety_blocks = 0
        alias_matches = 0
        confusion_warnings = 0

        # 构建评审索引
        review_index = {}
        for r in review_rows:
            tid = r.get('template_id', '').strip()
            si = r.get('series_index', '0').strip()
            if tid:
                review_index[(tid, si)] = r

        # 遍历manifest
        for gk, gdata in manifest.get('render_groups', {}).items():
            for task in gdata.get('tasks', []):
                tid = task.get('template_id', '')
                variety = task.get('variety', '')
                
                for (rtid, rsi), review in review_index.items():
                    if rtid != tid:
                        continue
                    
                    manual_id = review.get('manual_zhiji_id', '').strip()
                    indicator_name = review.get('indicator_name', review.get('title', ''))
                    decision = review.get('decision', '').strip()

                    if not manual_id and not decision:
                        skipped += 1
                        continue

                    # === 跨品种风险校验 ===
                    cross_warnings = self.cross_checker.check(indicator_name, variety)
                    if cross_warnings:
                        cross_variety_blocks += len(cross_warnings)
                        self.change_log.append({
                            'timestamp': datetime.now().isoformat(),
                            'type': 'CROSS_VARIETY_BLOCK',
                            'template_id': tid,
                            'indicator': indicator_name,
                            'variety': variety,
                            'warnings': cross_warnings,
                        })
                        # 跨品种P0 → 阻止回填
                        if any(w['severity'] == 'P0' for w in cross_warnings):
                            continue

                    # === 别名库校验 ===
                    alias = self.alias_checker.check(indicator_name)
                    if alias:
                        alias_matches += 1

                    # === 混淆对校验 ===
                    confusion_hits = self.confusion_checker.check(tid, indicator_name)
                    if confusion_hits:
                        confusion_warnings += len(confusion_hits)

                    # === zhiji_id格式校验 ===
                    if manual_id:
                        if ZHIJI_ID_PATTERN.match(manual_id):
                            task.setdefault('manual_overrides', {})
                            task['manual_overrides'][f'series_{rsi}'] = {
                                'zhiji_id': manual_id,
                                'decision': decision,
                                'remark': review.get('remark', ''),
                                'reviewer': review.get('reviewer', ''),
                                'review_time': review.get('review_time', ''),
                                'alias_matched': alias is not None,
                                'confusion_warnings': len(confusion_hits),
                                'imported_at': datetime.now().isoformat(),
                            }
                            applied += 1
                            
                            self.change_log.append({
                                'timestamp': datetime.now().isoformat(),
                                'type': 'APPLY',
                                'template_id': tid,
                                'series_index': rsi,
                                'zhiji_id': manual_id,
                                'decision': decision,
                                'alias_matched': alias is not None,
                                'confusion_count': len(confusion_hits),
                            })
                        else:
                            warnings += 1
                    elif decision:
                        task['status'] = f'REVIEWED_{decision.upper()}'
                        applied += 1

        # 更新manifest
        manifest['v6_update'] = {
            'updated_at': datetime.now().isoformat(),
            'applied': applied,
            'skipped': skipped,
            'warnings': warnings,
            'cross_variety_blocks': cross_variety_blocks,
            'alias_matches': alias_matches,
            'confusion_warnings': confusion_warnings,
            'source': review_csv,
        }

        if not output_path:
            output_path = manifest_path.replace('.json', '_v6_updated.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        # 写入变更日志
        log_path = output_path.replace('.json', '_change_log.json')
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.change_log, f, ensure_ascii=False, indent=2)

        return {
            'applied': applied,
            'skipped': skipped,
            'warnings': warnings,
            'cross_variety_blocks': cross_variety_blocks,
            'alias_matches': alias_matches,
            'confusion_warnings': confusion_warnings,
            'output': output_path,
            'log_path': log_path,
            'total_log_entries': len(self.change_log),
        }

    def filter_risk(self, filter_str: str, out_path: str) -> Dict:
        """筛选P0风险"""
        return self.export_risk_workbook(out_path, filter_str)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='升级版批量导入导出工具 v2')
    parser.add_argument('--export-batch', help='导出批次: batch_A/B/C')
    parser.add_argument('--export-risk', action='store_true', help='导出P0风险工作表')
    parser.add_argument('--filter-risk', help='筛选P0风险: blocked / variety=XX')
    parser.add_argument('--import', dest='import_csv', help='导入评审结果CSV')
    parser.add_argument('--manifest', help='manifest JSON路径')
    parser.add_argument('--filter', help='筛选条件: key=val,key2=val2')
    parser.add_argument('--out', help='输出文件路径')
    parser.add_argument('--apply', action='store_true', help='应用回写')
    args = parser.parse_args()

    tool = BatchExportImportV2()

    if args.export_batch:
        result = tool.export_batch(args.export_batch, args.out or f'{args.export_batch}_export.csv', args.filter)
        print(f"导出完成: {result.get('exported', 0)}条 → {result.get('output','')}")
        return

    if args.export_risk:
        result = tool.export_risk_workbook(args.out or 'risk_export.csv')
        print(f"风险导出: {result.get('exported', 0)}条 → {result.get('output','')}")
        return

    if args.filter_risk:
        result = tool.filter_risk(args.filter_risk, args.out or 'risk_filtered.csv')
        print(f"风险筛选: {result.get('exported', 0)}条 → {result.get('output','')}")
        return

    if args.import_csv and args.manifest:
        result = tool.import_with_validation(args.import_csv, args.manifest, args.out)
        print(f"导入完成:")
        print(f"  应用: {result['applied']}")
        print(f"  跳过: {result['skipped']}")
        print(f"  警告: {result['warnings']}")
        print(f"  跨品种阻断: {result['cross_variety_blocks']}")
        print(f"  别名匹配: {result['alias_matches']}")
        print(f"  混淆预警: {result['confusion_warnings']}")
        print(f"  输出: {result['output']}")
        print(f"  日志: {result['log_path']}")
        return

    parser.print_help()


if __name__ == '__main__':
    main()
