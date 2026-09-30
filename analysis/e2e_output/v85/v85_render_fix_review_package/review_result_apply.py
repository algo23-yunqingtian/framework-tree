#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_result_apply.py — 评审结果回写脚本

工单: HERMES_RENDER_SCRIPT_FIX_AND_MANUAL_REVIEW_PACKAGE

功能:
  1. 读取人工填写的评审结果 CSV
  2. 回写更新门户内标记状态
  3. 输出更新后的 chart_risk_bound_all_reviewed.json（不覆盖原始文件）

约束:
  - chart_risk_bound_all.json 只读，不修改
  - 输出另存为 chart_risk_bound_all_reviewed.json
  - 不调用 zhiji 接口

用法:
  python3 review_result_apply.py --review review_decisions.csv --bound chart_risk_bound_all.json --out chart_risk_bound_all_reviewed.json
  python3 review_result_apply.py --review review_decisions.csv --dry-run  # 仅预览，不输出文件
"""

import json
import csv
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


# 评审决策映射
DECISION_MAP = {
    '通过': 'APPROVED',
    '驳回': 'REJECTED',
    '临时白名单放行': 'WHITELISTED',
}

# 新状态对应的渲染分组
STATUS_TO_GROUP = {
    'APPROVED': 'can_render',
    'REJECTED': 'blocked',
    'WHITELISTED': 'review_first',
}


class ReviewResultApplier:
    """评审结果回写器"""

    def __init__(self, bound_path: str):
        with open(bound_path, encoding='utf-8') as f:
            self.bound = json.load(f)
        self.bound_index = {t['template_id']: t for t in self.bound.get('templates', [])}
        self.review_results = {}
        self.stats = {
            'total_reviews': 0,
            'approved': 0,
            'rejected': 0,
            'whitelisted': 0,
            'invalid': 0,
            'not_found': 0,
        }

    def load_review_csv(self, csv_path: str) -> int:
        """加载评审结果 CSV"""
        count = 0
        with open(csv_path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tid = row.get('template_id', '').strip()
                if not tid:
                    continue

                decision = row.get('decision', '').strip()
                new_status = DECISION_MAP.get(decision, row.get('new_status', 'UNKNOWN').strip())

                self.review_results[tid] = {
                    'reviewer': row.get('reviewer', '').strip(),
                    'review_time': row.get('review_time', '').strip(),
                    'decision': decision,
                    'new_status': new_status,
                    'remark': row.get('remark', '').strip(),
                    'previous_risk_level': row.get('previous_risk_level', '').strip(),
                }
                count += 1

                # 统计
                if new_status == 'APPROVED':
                    self.stats['approved'] += 1
                elif new_status == 'REJECTED':
                    self.stats['rejected'] += 1
                elif new_status == 'WHITELISTED':
                    self.stats['whitelisted'] += 1
                else:
                    self.stats['invalid'] += 1

        self.stats['total_reviews'] = count
        return count

    def apply_reviews(self) -> Dict[str, Any]:
        """应用评审结果到绑定数据，返回更新后的数据"""
        templates = []
        reviewed_count = 0

        for t in self.bound.get('templates', []):
            tid = t['template_id']
            entry = dict(t)  # 浅拷贝

            if tid in self.review_results:
                rr = self.review_results[tid]
                entry['review_status'] = {
                    'reviewer': rr['reviewer'],
                    'review_time': rr['review_time'],
                    'decision': rr['decision'],
                    'new_status': rr['new_status'],
                    'remark': rr['remark'],
                    'previous_risk_level': rr['previous_risk_level'],
                    'applied_at': datetime.now().isoformat(),
                }

                # 更新模板级状态
                if rr['new_status'] == 'APPROVED':
                    entry['template_risk_level'] = 'CLEAN'
                    entry['render_group_after_review'] = 'can_render'
                elif rr['new_status'] == 'REJECTED':
                    entry['render_group_after_review'] = 'blocked'
                elif rr['new_status'] == 'WHITELISTED':
                    entry['render_group_after_review'] = 'review_first'
                    entry['whitelist_expiry'] = '7d'

                reviewed_count += 1
            else:
                entry['review_status'] = {
                    'status': 'PENDING_REVIEW',
                    'reviewer': '',
                    'decision': '',
                }

            templates.append(entry)

        result = {
            'metadata': {
                'source': 'chart_risk_bound_all.json',
                'reviewed_at': datetime.now().isoformat(),
                'review_tool': 'review_result_apply.py',
                'original_template_count': len(self.bound.get('templates', [])),
                'reviewed_count': reviewed_count,
                'unreviewed_count': len(self.bound.get('templates', [])) - reviewed_count,
                'review_stats': self.stats,
            },
            'statistics': self.bound.get('statistics', {}),
            'variety_distribution': self.bound.get('variety_distribution', {}),
            'templates': templates,
        }

        return result

    def generate_review_summary(self) -> str:
        """生成评审汇总 Markdown"""
        s = self.stats
        total = len(self.bound.get('templates', []))
        reviewed = s['total_reviews']
        pending = total - reviewed

        lines = [
            '# 评审结果汇总',
            '',
            '> 生成时间: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '',
            '## 评审统计',
            '',
            '| 指标 | 数量 |',
            '|------|------|',
            '| 模板总数 | %d |' % total,
            '| 已评审 | %d |' % reviewed,
            '| 未评审 | %d |' % pending,
            '| 评审完成率 | %d%% |' % (reviewed * 100 // total),
            '',
            '## 评审结果分布',
            '',
            '| 结果 | 数量 | 占比 |',
            '|------|------|------|',
            '| ✅ 通过 (APPROVED) | %d | %d%% |' % (s['approved'], s['approved']*100//max(reviewed,1)),
            '| ❌ 驳回 (REJECTED) | %d | %d%% |' % (s['rejected'], s['rejected']*100//max(reviewed,1)),
            '| 🔄 临时白名单 (WHITELISTED) | %d | %d%% |' % (s['whitelisted'], s['whitelisted']*100//max(reviewed,1)),
            '| ⚠️ 无效决策 | %d | - |' % s['invalid'],
            '',
            '## 评审明细',
            '',
            '| 模板ID | 评审人 | 决策 | 新状态 | 备注 |',
            '|--------|--------|------|--------|------|',
        ]

        for tid in sorted(self.review_results.keys()):
            rr = self.review_results[tid]
            lines.append('| %s | %s | %s | %s | %s |' % (
                tid, rr['reviewer'], rr['decision'], rr['new_status'], rr['remark'][:40]
            ))

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='评审结果回写脚本')
    parser.add_argument('--review', required=True, help='评审结果 CSV 路径')
    parser.add_argument('--bound', default='chart_risk_bound_all.json', help='原始绑定 JSON 路径')
    parser.add_argument('--out', default='chart_risk_bound_all_reviewed.json', help='输出 JSON 路径')
    parser.add_argument('--summary', default='review_summary.md', help='评审汇总 MD 路径')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不输出文件')
    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.review):
        print('❌ 评审结果 CSV 不存在: %s' % args.review)
        print('   请先创建评审结果 CSV（格式见 review_checklist.md）')
        print('   示例 CSV:')
        print('   template_id,source,reviewer,review_time,decision,remark,previous_risk_level,new_status')
        print('   TPL-LC-091,PDF,张三,2026-09-30 16:00:00,通过,图表合理,CLEAN,APPROVED')
        sys.exit(1)

    if not os.path.exists(args.bound):
        print('❌ 绑定 JSON 不存在: %s' % args.bound)
        sys.exit(1)

    applier = ReviewResultApplier(args.bound)
    count = applier.load_review_csv(args.review)
    print('✅ 加载评审结果: %d 条' % count)

    result = applier.apply_reviews()
    print('   已评审: %d | 未评审: %d' % (
        result['metadata']['reviewed_count'],
        result['metadata']['unreviewed_count'],
    ))
    print('   通过: %d | 驳回: %d | 白名单: %d | 无效: %d' % (
        applier.stats['approved'], applier.stats['rejected'],
        applier.stats['whitelisted'], applier.stats['invalid'],
    ))

    if args.dry_run:
        print('\n🔄 DRY RUN 模式，未输出文件')
        summary = applier.generate_review_summary()
        print(summary)
        return

    # 输出 reviewed JSON
    out_path = Path(args.out)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('\n✅ 输出: %s (%d bytes)' % (out_path, os.path.getsize(out_path)))

    # 输出评审汇总
    summary_path = Path(args.summary)
    summary = applier.generate_review_summary()
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print('✅ 评审汇总: %s (%d bytes)' % (summary_path, os.path.getsize(summary_path)))


if __name__ == '__main__':
    main()
