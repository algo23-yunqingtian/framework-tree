#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mapping_fill_helper.py — THS指标人工映射回写辅助脚本

工单: HERMES_V85_THS_INDICATOR_MAPPING_PREP_AND_GATE_GAP_PLAN

功能:
  1. --export unfilled : 导出待人工匹配清单(无候选+模糊待确认所有series) CSV
  2. --export highconf : 导出高置信候选清单(供批量回填)
  3. --verify : 校验已填写zhiji_id合法性
  4. --apply --input x.csv : 读取人工填写结果，回写进 ths_adapted_all.json(副本)
                            与 ths_render_task_manifest_fixed.json

schema校验: 填入id合法性(正则), 非法 id 拒写

约束(T4):
  - 禁止调用zhiji接口，不做时序拉取
  - ths_adapted_all.json 原始文件只读, 回写仅写 _mapped 副本
  - 不修改已有 render 脚本/白名单
  - 仅新增文件
"""
import json
import re
import csv
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# zhiji_id 合法格式
VALID_ZHJI = re.compile(r'^(a\d+|kline:[A-Z]+:[A-Z0-9]+|ID[A-Za-z0-9_]+|FU[A-Za-z0-9]+|\d{6,})$')

COL_MATCH = 'manual_zhiji_id'


def validate_zhiji_id(zid):
    """校验 zhiji_id 合法性, 返回 (ok, error_msg)"""
    if not zid or not str(zid).strip():
        return (False, '空值')
    z = str(zid).strip()
    if VALID_ZHJI.match(z):
        return (True, '')
    return (False, f'格式非法: {z}')


class MappingFillHelper:
    def __init__(self, mapping_csv, ths_json, manifest_json):
        self.mapping_csv = mapping_csv
        self.ths_json = ths_json
        self.manifest_json = manifest_json
        self.rows = list(csv.DictReader(open(mapping_csv, encoding='utf-8-sig')))

    def export_unfilled(self, out_path):
        """导出无候选+模糊待确认清单"""
        fields = ['ths_chart_id', 'variety', 'series_index', 'original_ths_name',
                  'candidate_indicator_ids', 'best_match_name', 'best_match_score',
                  'best_match_zhiji_id', 'manual_zhiji_id']
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            w.writeheader()
            cnt = 0
            for r in self.rows:
                if r['match_category'] in ('模糊待人工确认', '无候选/低置信'):
                    w.writerow({
                        'ths_chart_id': r['ths_chart_id'],
                        'variety': r['variety'],
                        'series_index': r['series_index'],
                        'original_ths_name': r['original_ths_name'],
                        'candidate_indicator_ids': r['candidate_indicator_ids'],
                        'best_match_name': r['best_match_name'],
                        'best_match_score': r['best_match_score'],
                        'best_match_zhiji_id': r['best_match_zhiji_id'],
                        'manual_zhiji_id': '',
                    })
                    cnt += 1
        print(f'✅ 待人工匹配清单: {out_path} ({cnt} 条)')

    def export_highconf(self, out_path):
        """导出高置信候选(批量回填用)"""
        fields = ['ths_chart_id', 'variety', 'series_index', 'original_ths_name',
                  'best_match_name', 'best_match_score', 'best_match_zhiji_id',
                  'manual_zhiji_id']
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            w.writeheader()
            cnt = 0
            for r in self.rows:
                if r['match_category'] == '高置信' and r.get('best_match_zhiji_id'):
                    w.writerow({
                        'ths_chart_id': r['ths_chart_id'],
                        'variety': r['variety'],
                        'series_index': r['series_index'],
                        'original_ths_name': r['original_ths_name'],
                        'best_match_name': r['best_match_name'],
                        'best_match_score': r['best_match_score'],
                        'best_match_zhiji_id': r['best_match_zhiji_id'],
                        'manual_zhiji_id': r['best_match_zhiji_id'],  # 预填候选
                    })
                    cnt += 1
        print(f'✅ 高置信候选: {out_path} ({cnt} 条)')

    def verify(self, input_csv):
        """校验已填 manual_zhiji_id"""
        invalid = []
        with open(input_csv, encoding='utf-8-sig') as f:
            for i, row in enumerate(csv.DictReader(f)):
                z = (row.get(COL_MATCH) or '').strip()
                if not z:
                    continue
                ok, err = validate_zhiji_id(z)
                if not ok:
                    invalid.append((i + 2, row.get('ths_chart_id', ''),
                                    row.get('series_index', ''), z, err))
        if invalid:
            print(f'❌ {len(invalid)} 条非法 id:')
            for i, tid, sidx, z, err in invalid[:20]:
                print(f'  行{i}: {tid}/s{sidx} = {z} ({err})')
            return False
        print('✅ 全部已填 zhiji_id 合法')
        return True

    def apply(self, input_csv, out_ths_path, out_manifest):
        """回写人工填写结果"""
        if not self.verify(input_csv):
            sys.exit('❌ schema校验失败, 未回写')

        # 读取人工填写
        decisions = {}
        with open(input_csv, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                z = (row.get(COL_MATCH) or '').strip()
                if not z:
                    continue
                chart = row.get('ths_chart_id') or ''
                try:
                    sidx = int(row.get('series_index') or 0)
                except (ValueError, TypeError):
                    sidx = 0
                if chart:
                    decisions[(chart, sidx)] = z

        # 读取原始 THS 模板(只读源)
        ths_data = json.load(open(self.ths_json, encoding='utf-8'))
        applied = 0
        matched_series = set()
        for t in ths_data:
            cid = t.get('chart_id', '')
            for s_idx, s in enumerate(t.get('series', [])):
                key = (cid, s_idx)
                if key in decisions:
                    s['zhiji_id'] = decisions[key]
                    s['status'] = 'mapped'
                    s['note'] = f'人工映射 {datetime.now().strftime("%Y-%m-%d")} via mapping_fill_helper'
                    applied += 1
                    matched_series.add(key)
        with open(out_ths_path, 'w', encoding='utf-8') as f:
            json.dump(ths_data, f, ensure_ascii=False, indent=2)

        # 回写 manifest 元数据
        manifest_applied = 0
        if out_manifest and os.path.exists(self.manifest_json):
            manifest = json.load(open(self.manifest_json, encoding='utf-8'))
            manifest.setdefault('metadata', {})['mapping_applied'] = {
                'count': applied,
                'at': datetime.now().isoformat(),
            }
            with open(out_manifest, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            manifest_applied = len(decisions)

        print(f'✅ 回写{applied}条zhiji_id 到 {out_ths_path}')
        print(f'   manifest更新: {manifest_applied} 条决策记录')
        unmapped = set(decisions) - matched_series
        if unmapped:
            print(f'⚠️ {len(unmapped)}条未找到对应series(可能chart_id/series_index不匹配)')


def main():
    ap = argparse.ArgumentParser(description='THS指标人工映射回写辅助')
    ap.add_argument('--mapping', default=os.path.join(os.path.dirname(__file__), 'ths_candidate_mapping.csv'))
    ap.add_argument('--ths', required=False,
                    help='原始THS模板(只读源)')
    ap.add_argument('--manifest', default=None)
    ap.add_argument('--export', choices=['unfilled', 'highconf'])
    ap.add_argument('--verify', help='校验已填 CSV')
    ap.add_argument('--apply', help='回写 CSV')
    ap.add_argument('--out-json', default=None, help='回写输出的THS副本路径')
    ap.add_argument('--out-manifest', default=None, help='回写manifest输出')
    args = ap.parse_args()

    if not os.path.exists(args.mapping):
        sys.exit(f'❌ 候选CSV不存在: {args.mapping}')

    helper = MappingFillHelper(args.mapping, args.ths or '', args.manifest or '')

    if args.export:
        out = f'ths_match_{args.export}.csv'
        if args.export == 'unfilled':
            helper.export_unfilled(out)
        else:
            helper.export_highconf(out)
        return

    if args.verify:
        ok = helper.verify(args.verify)
        sys.exit(0 if ok else 1)

    if args.apply:
        if not args.out_json:
            stem = os.path.splitext(os.path.basename(args.apply))[0]
            args.out_json = f'ths_adapted_{stem}_mapped.json'
        helper.apply(args.apply, args.out_json, args.out_manifest)
        return

    ap.print_help()


if __name__ == '__main__':
    main()