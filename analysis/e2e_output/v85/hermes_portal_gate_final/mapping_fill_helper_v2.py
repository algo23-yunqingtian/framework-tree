#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mapping_fill_helper_v2.py — 人工zhiji_id回写增强版

工单: HERMES_V85_PORTAL_FINAL_INTEGRATE_GATE_FULL_CHECK_AND_REVIEW_BATCH_PACKAGE
升级自: mapping_fill_helper.py v1.0

v2新增:
  1. 别名库辅助提示 — 人工填写zhiji_id时自动展示候选别名
  2. 高危混淆指标预警 — 命中混淆对时预警
  3. 写入校验日志 — 记录每次回写操作

约束(T4):
  - 不调用zhiji API
  - 原始模板只读，仅写回manifest
  - indicators_v1.json、tree_config.json只读

用法:
  python3 mapping_fill_helper_v2.py --alias indicator_alias_library.csv \\
    --confusion high_risk_confusion_pairs.csv \\
    --manifest ths_render_task_manifest_fixed.json \\
    --review review_filled.csv --apply
"""

import json
import csv
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

ZHIJI_ID_PATTERN = re.compile(r'^ID[a-zA-Z0-9_]+$')


class AliasLibrary:
    """别名库加载器"""

    def __init__(self, alias_path: Optional[str] = None):
        self.aliases: Dict[str, Dict] = {}  # ths_name → alias info
        self.stats = {'total': 0, 'loaded': 0}

        if alias_path and os.path.exists(alias_path):
            self.load(alias_path)

    def load(self, path: str):
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                ths_name = row.get('ths_indicator_name', '')
                if ths_name:
                    self.aliases[ths_name] = {
                        'zhiji_name': row.get('zhiji_indicator_name', ''),
                        'zhiji_id': row.get('zhiji_id', ''),
                        'score': float(row.get('similarity_score', 0) or 0),
                        'variety': row.get('variety', ''),
                        'alias_id': row.get('alias_id', ''),
                    }
                    self.stats['loaded'] += 1
        self.stats['total'] = len(self.aliases)

    def lookup(self, indicator_name: str) -> Optional[Dict]:
        """查找指标名的别名推荐"""
        return self.aliases.get(indicator_name)

    def suggest(self, indicator_name: str) -> List[Tuple[str, str, float]]:
        """模糊查找别名建议（前缀匹配）"""
        results = []
        for ths_name, info in self.aliases.items():
            if indicator_name and indicator_name in ths_name:
                results.append((info['zhiji_name'], info['zhiji_id'], info['score']))
        results.sort(key=lambda x: -x[2])
        return results[:5]


class ConfusionPairChecker:
    """高危混淆对检查器"""

    def __init__(self, confusion_path: Optional[str] = None):
        self.pairs: List[Dict] = []
        self.by_chart: Dict[str, List[Dict]] = {}

        if confusion_path and os.path.exists(confusion_path):
            self.load(confusion_path)

    def load(self, path: str):
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                self.pairs.append(row)
                cid = row.get('chart_id', '')
                if cid:
                    self.by_chart.setdefault(cid, []).append(row)

    def check(self, chart_id: str, indicator_name: str = '') -> List[Dict]:
        """检查指标是否命中混淆对"""
        hits = []
        # 按chart_id查找
        if chart_id in self.by_chart:
            for pair in self.by_chart[chart_id]:
                if (indicator_name and
                    (indicator_name in pair.get('indicator_a', '') or
                     indicator_name in pair.get('indicator_b', ''))):
                    hits.append(pair)
        # 按指标名查找
        for pair in self.pairs:
            if indicator_name:
                if indicator_name in pair.get('indicator_a', '') or indicator_name in pair.get('indicator_b', ''):
                    if pair not in hits:
                        hits.append(pair)
        return hits


class MappingFillHelperV2:
    """人工zhiji_id回写工具 v2"""

    def __init__(self, alias_path: Optional[str] = None,
                 confusion_path: Optional[str] = None):
        self.alias_lib = AliasLibrary(alias_path)
        self.confusion_checker = ConfusionPairChecker(confusion_path)
        self.log: List[Dict] = []

    def validate_zhiji_id(self, zhiji_id: str) -> Tuple[bool, str]:
        """校验zhiji_id格式"""
        if not zhiji_id:
            return False, 'zhiji_id为空'
        zhiji_id = zhiji_id.strip()
        if ZHIJI_ID_PATTERN.match(zhiji_id):
            return True, '格式合规'
        return False, f'格式不合规: {zhiji_id} (应为 ^ID[a-zA-Z0-9_]+$)'

    def fill_with_alias_hint(self, template_id: str, series_index: int,
                             indicator_name: str,
                             manual_zhiji_id: str = '') -> Dict:
        """
        人工填写zhiji_id时提供别名提示+混淆预警。

        返回:
          {
            'template_id': str,
            'series_index': int,
            'indicator_name': str,
            'alias_match': dict or None,
            'alias_suggestions': list,
            'confusion_warning': list,
            'zhiji_id_validation': tuple,
            'log_entry': dict,
          }
        """
        result = {
            'template_id': template_id,
            'series_index': series_index,
            'indicator_name': indicator_name,
            'alias_match': None,
            'alias_suggestions': [],
            'confusion_warning': [],
            'zhiji_id_validation': (False, ''),
        }

        # 别名匹配
        alias = self.alias_lib.lookup(indicator_name)
        if alias:
            result['alias_match'] = alias
        else:
            suggestions = self.alias_lib.suggest(indicator_name)
            result['alias_suggestions'] = suggestions

        # 混淆预警
        confusion_hits = self.confusion_checker.check(template_id, indicator_name)
        if confusion_hits:
            result['confusion_warning'] = confusion_hits

        # zhiji_id校验
        if manual_zhiji_id:
            valid, msg = self.validate_zhiji_id(manual_zhiji_id)
            result['zhiji_id_validation'] = (valid, msg)

        # 写入日志
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'template_id': template_id,
            'series_index': series_index,
            'indicator_name': indicator_name,
            'manual_zhiji_id': manual_zhiji_id,
            'alias_matched': alias is not None,
            'alias_zhiji_id': alias['zhiji_id'] if alias else '',
            'confusion_hits': len(confusion_hits),
            'validation_passed': result['zhiji_id_validation'][0],
            'validation_message': result['zhiji_id_validation'][1],
        }
        self.log.append(log_entry)

        return result

    def apply_review_results(self, review_csv_path: str,
                             manifest_path: str,
                             output_path: str) -> Dict:
        """
        应用评审结果CSV到manifest。

        评审CSV格式: template_id,series_index,manual_zhiji_id,decision,remark
        """
        # 加载评审结果
        review_results = []
        with open(review_csv_path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                review_results.append(row)

        # 加载manifest
        with open(manifest_path) as f:
            manifest = json.load(f)

        # 应用回写
        applied = 0
        skipped = 0
        warnings = 0

        # 构建索引
        review_index = {}
        for r in review_results:
            tid = r.get('template_id', '')
            si = int(r.get('series_index', -1))
            review_index[(tid, si)] = r

        # 遍历manifest中的任务
        for gk, gdata in manifest.get('render_groups', {}).items():
            for task in gdata.get('tasks', []):
                tid = task.get('template_id', '')
                # 查找该模板的评审结果
                for (rtid, rsi), review in review_index.items():
                    if rtid == tid:
                        # 应用回写
                        manual_id = review.get('manual_zhiji_id', '')
                        decision = review.get('decision', '')

                        if manual_id:
                            valid, msg = self.validate_zhiji_id(manual_id)
                            if valid:
                                # 回写
                                task.setdefault('manual_overrides', {})
                                task['manual_overrides'][f'series_{rsi}'] = {
                                    'zhiji_id': manual_id,
                                    'decision': decision,
                                    'remark': review.get('remark', ''),
                                    'reviewer': review.get('reviewer', ''),
                                    'review_time': review.get('review_time', ''),
                                }
                                applied += 1
                            else:
                                warnings += 1
                                self.log.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'template_id': tid,
                                    'warning': f'zhiji_id格式不合规: {manual_id}',
                                    'message': msg,
                                })
                        else:
                            skipped += 1

        # 写入更新后的manifest
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        # 写入校验日志
        log_path = output_path.replace('.json', '_fill_log.json')
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, ensure_ascii=False, indent=2)

        return {
            'applied': applied,
            'skipped': skipped,
            'warnings': warnings,
            'output_path': output_path,
            'log_path': log_path,
            'total_log_entries': len(self.log),
        }

    def print_hint(self, result: Dict):
        """打印别名提示+混淆预警"""
        print(f"\n{'='*60}")
        print(f"模板: {result['template_id']} | series[{result['series_index']}]")
        print(f"指标名: {result['indicator_name']}")

        if result['alias_match']:
            a = result['alias_match']
            print(f"\n✅ 别名匹配 (score={a['score']}, {a['alias_id']}):")
            print(f"   zhiji名: {a['zhiji_name']}")
            print(f"   zhiji_id: {a['zhiji_id']}")
            print(f"   品种: {a['variety']}")
        elif result['alias_suggestions']:
            print(f"\n💡 别名建议 (模糊匹配):")
            for name, zid, score in result['alias_suggestions']:
                print(f"   {name} → {zid} (score={score})")
        else:
            print(f"\n❌ 无别名匹配")

        if result['confusion_warning']:
            print(f"\n⚠️  混淆预警 ({len(result['confusion_warning'])}条):")
            for c in result['confusion_warning']:
                print(f"   [{c.get('severity','')}] {c.get('indicator_a','')} ↔ {c.get('indicator_b','')}")
                print(f"       组: {c.get('conflict_group','')} | {c.get('impact','')}")

        if result['zhiji_id_validation'][0]:
            print(f"\n✅ zhiji_id校验: {result['zhiji_id_validation'][1]}")
        elif result['zhiji_id_validation'][1]:
            print(f"\n❌ zhiji_id校验: {result['zhiji_id_validation'][1]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='人工zhiji_id回写工具 v2')
    parser.add_argument('--alias', help='别名库CSV路径')
    parser.add_argument('--confusion', help='混淆对CSV路径')
    parser.add_argument('--manifest', help='manifest JSON路径')
    parser.add_argument('--review', help='评审结果CSV路径')
    parser.add_argument('--output', default='manifest_filled.json', help='输出路径')
    parser.add_argument('--apply', action='store_true', help='应用评审结果')
    parser.add_argument('--hint', nargs=3, metavar=('TEMPLATE_ID', 'SERIES_INDEX', 'INDICATOR_NAME'),
                        help='查询单条指标别名提示')
    args = parser.parse_args()

    helper = MappingFillHelperV2(args.alias, args.confusion)

    if args.hint:
        tid, si, name = args.hint
        result = helper.fill_with_alias_hint(tid, int(si), name)
        helper.print_hint(result)
        return

    if args.apply and args.review and args.manifest:
        stats = helper.apply_review_results(args.review, args.manifest, args.output)
        print(f"\n{'='*60}")
        print(f"回写完成:")
        print(f"  应用: {stats['applied']}")
        print(f"  跳过: {stats['skipped']}")
        print(f"  警告: {stats['warnings']}")
        print(f"  输出: {stats['output_path']}")
        print(f"  日志: {stats['log_path']}")
        return

    print("用法: --hint TEMPLATE_ID SERIES_INDEX INDICATOR_NAME")
    print("     --apply --review review.csv --manifest manifest.json")


if __name__ == '__main__':
    main()
