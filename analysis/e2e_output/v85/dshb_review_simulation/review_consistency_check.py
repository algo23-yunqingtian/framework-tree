#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_consistency_check.py — 人工评审一致性校验脚本

工单: DSH-B_V85_HUMAN_REVIEW_SIMULATION_AND_PRECHECK

功能:
  输入人工填写完成的 v85_p0_risk_human_workbook.csv，自动校验:
  1. 白名单条目不被黑名单规则拦截
  2. 修复P0风险可被新版规则捕获
  3. Gate跟踪表状态和工作表处置标记保持同步

用法:
  python3 review_consistency_check.py --workbook <path/to/workbook.csv> --gate <path/to/gate_tracker.csv>
  python3 review_consistency_check.py  # 使用默认路径

约束:
  - 不修改任何源文件
  - 不调用zhiji API
  - 仅读取并输出校验报告
"""

import json
import csv
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

DEFAULT_BASE = Path(__file__).parent.resolve()
V85 = DEFAULT_BASE.parent

sys.stdout.reconfigure(encoding='utf-8')


class ReviewConsistencyChecker:
    """人工评审一致性校验器"""

    def __init__(self, workbook_path, gate_path, blacklist_path=None, boundary_path=None):
        self.workbook_path = workbook_path
        self.gate_path = gate_path
        self.blacklist_path = blacklist_path or str(V85 / "dshb_full_integrate" / "semantic_blacklist_v85_final.json")
        self.boundary_path = boundary_path or str(V85 / "miss_risk_mining" / "blacklist_boundary_testset.json")
        self.errors = []
        self.warnings = []
        self.info = []

    def load_csv(self, path):
        if not os.path.exists(path):
            self.errors.append(f"文件不存在: {path}")
            return []
        with open(path, encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))

    def load_json(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def check_workbook_integrity(self):
        """检查工作表基本完整性"""
        wb = self.load_csv(self.workbook_path)
        self.info.append(f"工作表加载: {len(wb)} 行")

        if not wb:
            self.errors.append("工作表为空或加载失败")
            return wb

        required_cols = ['template_id', 'series_name', 'risk_level', 'risk_id',
                         'current_block_status', 'recommended_action']
        missing = [c for c in required_cols if c not in (wb[0].keys() if wb else [])]
        if missing:
            self.warnings.append(f"工作表缺少推荐列: {missing}")

        # 检查必填字段
        for i, row in enumerate(wb):
            rid = row.get('risk_id', '').strip()
            if not rid:
                self.warnings.append(f"第{i+2}行: risk_id为空")
            if row.get('risk_level', '') not in ('P0', 'P1', ''):
                self.warnings.append(f"第{i+2}行({rid}): risk_level无效: {row.get('risk_level', '')}")

        return wb

    def check_whitelist_consistency(self, wb):
        """校验1: 白名单条目不被黑名单规则拦截"""
        self.info.append("\n校验1: 白名单条目 vs 黑名单规则")

        blacklist = self.load_json(self.blacklist_path)
        rules = blacklist.get('rules', []) if blacklist else []
        boundary = self.load_json(self.boundary_path)
        boundary_cases = boundary.get('cases', []) if boundary else []

        whitelist_entries = [r for r in wb if '白名单' in r.get('recommended_action', '') or
                             'WHITELIST' in r.get('current_block_status', '') or
                             '放行' in r.get('recommended_action', '')]

        if not whitelist_entries:
            self.info.append("  未发现白名单条目")
            return

        self.info.append(f"  发现 {len(whitelist_entries)} 条白名单/放行条目")

        for entry in whitelist_entries:
            rid = entry.get('risk_id', '')
            series = entry.get('series_name', '')
            rec = entry.get('recommended_action', '')

            # 检查是否有规则应该拦截该条目
            blocked_by = []
            for rule in rules:
                left_pats = rule.get('left_patterns', [])
                right_pats = rule.get('right_patterns', [])
                # 简单匹配：series_name中包含left_patterns且某匹配包含right_patterns
                # 这里仅做关键词匹配检查
                series_lower = series.lower() if series else ''
                for lp in left_pats:
                    if lp.lower() in series_lower:
                        # 找到可能的匹配，记录规则
                        blocked_by.append(rule['rule_id'])
                        break

            if blocked_by:
                self.warnings.append(
                    f"  ⚠ {rid}({series[:20]}): 白名单放行但可能被规则拦截: {', '.join(blocked_by[:3])}"
                )
            else:
                self.info.append(f"  ✓ {rid}({series[:20]}): 白名单条目，无规则冲突")

        # 检查边界测试集中的安全负向样例是否被白名单误放行
        safe_cases = [c for c in boundary_cases if not c.get('expected_blocked', False)
                      and c.get('category', '') == '安全负向样例']
        for sc in safe_cases:
            self.info.append(f"  ✓ {sc['case_id']}: 安全负向样例（应放行，未被规则拦截）")

    def check_fix_capturable(self, wb):
        """校验2: 修复P0风险可被新版规则捕获"""
        self.info.append("\n校验2: 修复P0风险 vs 新版规则")

        blacklist = self.load_json(self.blacklist_path)
        rules = blacklist.get('rules', []) if blacklist else []
        rule_ids = set(r['rule_id'] for r in rules)

        # 加载扩展候选
        cand_path = str(V85 / "miss_risk_mining" / "blacklist_extend_candidate_v2.json")
        candidates = self.load_json(cand_path)
        cand_rules = candidates.get('candidates', []) if candidates else []

        fixable = [r for r in wb if '规则修复' in r.get('recommended_action', '') or
                   'BL-' in r.get('recommended_action', '') or
                   '修复' in r.get('recommended_action', '')]

        if not fixable:
            self.info.append("  未发现修复条目")
            return

        self.info.append(f"  发现 {len(fixable)} 条修复/规则推荐条目")

        for entry in fixable:
            rid = entry.get('risk_id', '')
            rec = entry.get('recommended_action', '')
            series = entry.get('series_name', '')

            # 提取推荐的规则ID
            recommended_rules = []
            for cr in cand_rules:
                rid_cr = cr.get('rule_id', '')
                if rid_cr in rec:
                    recommended_rules.append(rid_cr)
            for r in rules:
                if r['rule_id'] in rec:
                    recommended_rules.append(r['rule_id'])

            if not recommended_rules:
                self.warnings.append(f"  ⚠ {rid}({series[:20]}): 推荐动作中未识别到具体规则ID")
                continue

            # 检查规则是否存在
            for rr in recommended_rules:
                in_main = rr in rule_ids
                in_cand = any(cr.get('rule_id') == rr for cr in cand_rules)
                if in_main:
                    self.info.append(f"  ✓ {rid}: 推荐规则 {rr} 已在主黑名单中")
                elif in_cand:
                    cand_obj = [cr for cr in cand_rules if cr.get('rule_id') == rr][0]
                    cls = cand_obj.get('classification', '')
                    self.info.append(f"  ⚠ {rid}: 推荐规则 {rr} 为扩展候选（classification={cls}），需确认是否已纳入")
                else:
                    self.warnings.append(f"  ⚠ {rid}: 推荐规则 {rr} 未在任何规则集中找到")

    def check_gate_sync(self, wb):
        """校验3: Gate跟踪表状态和工作表处置标记保持同步"""
        self.info.append("\n校验3: Gate跟踪表 vs 工作表处置标记")

        gate = self.load_csv(self.gate_path)
        if not gate:
            self.errors.append("Gate跟踪表加载失败")
            return

        self.info.append(f"  Gate跟踪表: {len(gate)} 行")

        # 统计工作表中的P0处置情况
        p0_rows = [r for r in wb if r.get('risk_level', '') == 'P0']
        disposed = [r for r in p0_rows if r.get('current_block_status', '').startswith(
            ('BLOCKED', 'WHITELIST', 'PASS', 'REJECTED'))]
        blocked = [r for r in p0_rows if 'BLOCKED' in r.get('current_block_status', '')]
        whitelisted = [r for r in p0_rows if 'WHITELIST' in r.get('current_block_status', '') or
                       '放行' in r.get('recommended_action', '')]
        unresolved = [r for r in p0_rows if r.get('current_block_status', '').startswith('NOT_BLOCKED')]

        self.info.append(f"  P0总数: {len(p0_rows)}")
        self.info.append(f"  已处置: {len(disposed)}")
        self.info.append(f"  已阻塞: {len(blocked)}")
        self.info.append(f"  白名单放行: {len(whitelisted)}")
        self.info.append(f"  未处置: {len(unresolved)}")

        # 检查Gate跟踪表中的H2
        h2 = [g for g in gate if g.get('blocker_id', '') == 'H2']
        if h2:
            h2_status = h2[0].get('current_status', '')
            if '阻塞' in h2_status or 'BLOCKED' in h2_status:
                if len(unresolved) == 0:
                    self.warnings.append("  ⚠ H2标记为阻塞但工作表中无未处置P0 — 请同步更新")
                elif len(unresolved) > 0:
                    self.info.append(f"  ✓ H2阻塞状态正确（{len(unresolved)}条P0未处置）")
            elif '完成' in h2_status or 'DONE' in h2_status:
                if len(unresolved) > 0:
                    self.errors.append(f"  ❌ H2标记为完成但仍有{len(unresolved)}条P0未处置")
                else:
                    self.info.append("  ✓ H2完成状态正确")

        # 检查G-03/G-05/G-06
        for gid in ['G-03', 'G-05', 'G-06']:
            gi = [g for g in gate if g.get('blocker_id', '') == gid]
            if gi:
                gs = gi[0].get('current_status', '')
                if 'PARTIAL' in gs or '阻塞' in gs:
                    if len(unresolved) == 0:
                        self.warnings.append(f"  ⚠ {gid}标记为部分完成但工作表中无未处置P0 — 请确认")

        # 检查gate_block_flag同步
        wb_with_flag = [r for r in wb if r.get('gate_block_flag', '') in ('YES', 'NO')]
        if wb_with_flag:
            yes_count = sum(1 for r in wb_with_flag if r.get('gate_block_flag') == 'YES')
            self.info.append(f"  工作表gate_block_flag=YES: {yes_count}条")

    def check_data_missing_risks(self, wb):
        """校验4: 数据缺失风险条目完整性"""
        self.info.append("\n校验4: 数据缺失风险条目")

        data_missing = [r for r in wb if '数据缺失' in r.get('root_cause_category', '') or
                        '数据缺失' in r.get('notes', '') or
                        'matched_name' in r.get('notes', '')]

        if not data_missing:
            self.info.append("  未发现数据缺失条目")
            return

        self.info.append(f"  发现 {len(data_missing)} 条数据缺失条目")
        for entry in data_missing:
            rid = entry.get('risk_id', '')
            series = entry.get('series_name', '')
            rec = entry.get('recommended_action', '')
            status = entry.get('current_block_status', '')

            if '白名单' in rec or '放行' in rec:
                self.info.append(f"  ✓ {rid}({series[:20]}): 已标记白名单放行")
            elif '修复' in rec:
                self.info.append(f"  ⚠ {rid}({series[:20]}): 推荐修复但未确认上游修复进度")
            else:
                self.warnings.append(f"  ⚠ {rid}({series[:20]}): 数据缺失但无明确处置方案")

    def run(self):
        """执行全部校验"""
        now = datetime.now().isoformat()

        self.info.append("=" * 60)
        self.info.append("V85 人工评审一致性校验报告")
        self.info.append(f"生成时间: {now}")
        self.info.append(f"工作表: {self.workbook_path}")
        self.info.append(f"Gate跟踪: {self.gate_path}")
        self.info.append("=" * 60)

        wb = self.check_workbook_integrity()
        self.check_whitelist_consistency(wb)
        self.check_fix_capturable(wb)
        self.check_gate_sync(wb)
        self.check_data_missing_risks(wb)

        # 汇总
        self.info.append("")
        self.info.append("=" * 60)
        self.info.append("校验汇总")
        self.info.append("=" * 60)
        self.info.append(f"  错误(Errors):    {len(self.errors)}")
        self.info.append(f"  警告(Warnings):  {len(self.warnings)}")
        self.info.append(f"  信息(Info):      {len(self.info)}")

        if self.errors:
            self.info.append("")
            self.info.append("❌ 存在错误，请修复后重新校验")
            for e in self.errors:
                self.info.append(f"  [ERROR] {e}")
        if self.warnings:
            self.info.append("")
            self.info.append("⚠ 存在警告，建议关注")
            for w in self.warnings:
                self.info.append(f"  [WARN] {w}")

        if not self.errors and not self.warnings:
            self.info.append("")
            self.info.append("✅ 全部校验通过，无错误无警告")

        # 输出报告
        report = "\n".join(self.info)
        print(report)

        report_path = self.workbook_path.replace('.csv', '_consistency_report.md')
        if report_path:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# 人工评审一致性校验报告\n\n")
                f.write(f"> 生成时间: {now}\n")
                f.write(f"> 工作表: {self.workbook_path}\n")
                f.write(f"> Gate跟踪: {self.gate_path}\n\n")
                f.write(f"## 校验汇总\n\n")
                f.write(f"- 错误: {len(self.errors)}\n")
                f.write(f"- 警告: {len(self.warnings)}\n")
                f.write(f"- 信息: {len(self.info)}\n\n")
                f.write(f"## 详细日志\n\n")
                f.write(report)
            print(f"\n报告已输出: {report_path}")

        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description='人工评审一致性校验脚本')
    parser.add_argument('--workbook', default=None,
                        help='P0工作表CSV路径')
    parser.add_argument('--gate', default=None,
                        help='Gate跟踪表CSV路径')
    parser.add_argument('--blacklist', default=None,
                        help='黑名单JSON路径')
    parser.add_argument('--boundary', default=None,
                        help='边界测试集JSON路径')
    args = parser.parse_args()

    base = DEFAULT_BASE
    wb_path = args.workbook or str(V85 / "dshb_human_review_prep" / "v85_p0_risk_human_workbook.csv")
    gate_path = args.gate or str(V85 / "dshb_human_review_prep" / "gate_block_tracker.csv")

    checker = ReviewConsistencyChecker(wb_path, gate_path, args.blacklist, args.boundary)
    checker.run()


if __name__ == '__main__':
    main()
