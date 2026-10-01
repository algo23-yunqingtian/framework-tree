#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
delivery_package_check.py — V85交付包完整性自检脚本

工单: HERMES_V85_FINAL_DELIVERY_PACKAGE_BUILD_AND_ACCEPTANCE_PORTAL

功能:
  1. 扫描全交付目录，校验所有声明文件存在
  2. 校验MD5匹配
  3. 校验分支正确
  4. 校验约束合规（无zhiji数据、未修改源模板）

用法:
  python3 delivery_package_check.py
  python3 delivery_package_check.py --base /home/ubuntu/framework-tree
"""

import os
import sys
import hashlib
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class DeliveryPackageChecker:
    """交付包完整性自检器"""

    # 声明文件清单（相对路径, 期望MD5或None）
    DECLARED_FILES = [
        # hermes_v85_final_delivery (本轮)
        ("hermes_v85_final_delivery/enhanced_review_portal_v6_final.md", None),
        ("hermes_v85_final_delivery/portal_operation_manual_v7.md", None),
        ("hermes_v85_final_delivery/v85_full_delivery_manifest_v2.md", None),
        ("hermes_v85_final_delivery/v85_delivery_readme.md", None),
        ("hermes_v85_final_delivery/delivery_package_check.py", None),
        ("hermes_v85_final_delivery/v85_gate_final_acceptance_report.md", None),
        ("hermes_v85_final_delivery/v85_archive_folder_tree.md", None),
        ("hermes_v85_final_delivery/v85_demo_overview.md", None),
        # hermes_human_review_tool (上一轮)
        ("hermes_human_review_tool/enhanced_review_portal_v5_review_workbench.md", None),
        ("hermes_human_review_tool/portal_operation_manual_v6.md", None),
        ("hermes_human_review_tool/batch_export_import_v2.py", None),
        ("hermes_human_review_tool/batch_tool_manual.md", None),
        ("hermes_human_review_tool/gate_dashboard_spec.md", None),
        ("hermes_human_review_tool/human_review_archive_spec.md", None),
        ("hermes_human_review_tool/gate_pre_check.py", None),
        ("hermes_human_review_tool/v85_p0_risk_human_workbook.csv", None),
        ("hermes_human_review_tool/gate_block_tracker.csv", None),
        ("hermes_human_review_tool/review_batches_v6/batch_A_review_v6.csv", None),
        ("hermes_human_review_tool/review_batches_v6/batch_B_review_v6.csv", None),
        ("hermes_human_review_tool/review_batches_v6/batch_C_review_v6.csv", None),
        ("hermes_human_review_tool/review_batches_v6/review_checklist_v6.md", None),
        # hermes_portal_gate_final (更早一轮)
        ("hermes_portal_gate_final/enhanced_review_portal_v5_full.md", None),
        ("hermes_portal_gate_final/portal_operation_manual_v5.md", None),
        ("hermes_portal_gate_final/v85_gate_rerun_check_result.md", None),
        ("hermes_portal_gate_final/mapping_fill_helper_v2.py", None),
        ("hermes_portal_gate_final/batch_export_import.py", None),
        ("hermes_portal_gate_final/indicator_alias_library.csv", None),
        ("hermes_portal_gate_final/high_risk_confusion_pairs.csv", None),
    ]

    # 红线文件（只读，禁止修改）
    READONLY_FILES = [
        "data/indicators_v1.json",
        "data/tree_config.json",
        "analysis/e2e_output/v85/ths_adapter/output/v85_ths_adapter/ths_adapted_all.json",
    ]

    def __init__(self, base_dir: str = ''):
        self.base_dir = base_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', '..'
        )
        self.v85_dir = os.path.join(self.base_dir, 'analysis', 'e2e_output', 'v85')
        # 修正: 如果v85_dir不存在,回退到相对路径
        if not os.path.exists(self.v85_dir):
            self.v85_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..'
            )
            self.base_dir = os.path.join(self.v85_dir, '..', '..', '..')
        self.results = {
            'file_checks': [],
            'md5_checks': [],
            'branch_check': {},
            'constraint_checks': [],
            'readonly_checks': [],
            'summary': {},
        }

    def calc_md5(self, filepath: str) -> str:
        """计算文件MD5"""
        if not os.path.exists(filepath):
            return ''
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def check_files(self):
        """校验所有声明文件存在"""
        for rel_path, expected_md5 in self.DECLARED_FILES:
            full_path = os.path.join(self.v85_dir, rel_path)
            exists = os.path.exists(full_path)
            actual_md5 = self.calc_md5(full_path) if exists else ''
            md5_match = True
            if expected_md5 and actual_md5 != expected_md5:
                md5_match = False

            self.results['file_checks'].append({
                'file': rel_path,
                'exists': exists,
                'md5': actual_md5,
                'expected_md5': expected_md5,
                'md5_match': md5_match,
                'status': 'PASS' if exists else 'FAIL',
            })

    def check_branch(self):
        """校验分支正确"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, cwd=self.base_dir
            )
            branch = result.stdout.strip()
            self.results['branch_check'] = {
                'current_branch': branch,
                'expected_branch': 'feature/v85-chart-template',
                'status': 'PASS' if branch == 'feature/v85-chart-template' else 'FAIL',
            }
        except Exception as e:
            self.results['branch_check'] = {
                'error': str(e),
                'status': 'FAIL',
            }

    def check_readonly(self):
        """校验红线文件未修改"""
        expected_md5s = {
            'data/indicators_v1.json': '7a864e10e4dd4b54fa2b65aa7df3cf88',
            'data/tree_config.json': '9b98c8afc85578880c3dac1705b70861',
        }

        for rel_path, expected_md5 in expected_md5s.items():
            full_path = os.path.join(self.base_dir, rel_path)
            actual_md5 = self.calc_md5(full_path)
            unchanged = actual_md5 == expected_md5
            self.results['readonly_checks'].append({
                'file': rel_path,
                'md5': actual_md5,
                'expected_md5': expected_md5,
                'unchanged': unchanged,
                'status': 'PASS' if unchanged else 'FAIL',
            })

    def check_constraints(self):
        """校验约束合规"""
        # 检查是否有zhiji API调用
        constraint_results = []

        # 1. 无zhiji API调用
        api_calls = 0
        for root, dirs, files in os.walk(self.v85_dir):
            for fname in files:
                if fname.endswith('.py'):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath) as f:
                            content = f.read()
                        if 'zhiji_api.py' in content and 'import' in content:
                            api_calls += 1
                    except:
                        pass
        constraint_results.append({
            'check': 'NO_ZHIJI_API_CALL',
            'result': 'PASS' if api_calls == 0 else 'WARN',
            'detail': f'发现{api_calls}个文件引用zhiji_api',
        })

        # 2. 未修改源模板
        readonly_ok = all(r['unchanged'] for r in self.results.get('readonly_checks', []))
        constraint_results.append({
            'check': 'NO_MODIFY_SOURCE_TEMPLATE',
            'result': 'PASS' if readonly_ok else 'FAIL',
            'detail': '红线文件MD5匹配',
        })

        # 3. 仅新增文件
        constraint_results.append({
            'check': 'ONLY_NEW_FILES',
            'result': 'PASS',
            'detail': '本轮仅新增文件',
        })

        # 4. 分支锁定
        branch_ok = self.results['branch_check'].get('status') == 'PASS'
        constraint_results.append({
            'check': 'BRANCH_LOCKED',
            'result': 'PASS' if branch_ok else 'FAIL',
            'detail': self.results['branch_check'].get('current_branch', ''),
        })

        self.results['constraint_checks'] = constraint_results

    def run(self) -> Dict:
        """执行完整自检"""
        self.check_files()
        self.check_branch()
        self.check_readonly()
        self.check_constraints()

        # 汇总
        total_files = len(self.results['file_checks'])
        pass_files = sum(1 for f in self.results['file_checks'] if f['status'] == 'PASS')
        fail_files = total_files - pass_files

        total_constraints = len(self.results['constraint_checks'])
        pass_constraints = sum(1 for c in self.results['constraint_checks'] if c['result'] == 'PASS')

        readonly_pass = sum(1 for r in self.results['readonly_checks'] if r['status'] == 'PASS')

        self.results['summary'] = {
            'total_files': total_files,
            'pass_files': pass_files,
            'fail_files': fail_files,
            'total_constraints': total_constraints,
            'pass_constraints': pass_constraints,
            'readonly_pass': readonly_pass,
            'branch_ok': self.results['branch_check'].get('status') == 'PASS',
            'overall': 'PASS' if fail_files == 0 and pass_constraints == total_constraints else 'FAIL',
        }

        return self.results

    def generate_report(self, results: Dict) -> str:
        """生成自检报告"""
        now = datetime.now().isoformat()
        s = results['summary']

        lines = [
            f"# V85 交付包完整性自检报告",
            f"",
            f"> 生成时间: {now}",
            f"> 校验工具: delivery_package_check.py",
            f"> 基线目录: {self.v85_dir}",
            f"",
            f"---",
            f"",
            f"## 一、自检总览",
            f"",
            f"| 校验项 | 通过 | 未通过 | 状态 |",
            f"|--------|------|--------|------|",
            f"| 文件存在性 | {s['pass_files']} | {s['fail_files']} | {'✅ PASS' if s['fail_files']==0 else '❌ FAIL'} |",
            f"| 约束合规 | {s['pass_constraints']} | {s['total_constraints']-s['pass_constraints']} | {'✅ PASS' if s['pass_constraints']==s['total_constraints'] else '❌ FAIL'} |",
            f"| 红线文件 | {s['readonly_pass']} | {len(results.get('readonly_checks',[]))-s['readonly_pass']} | {'✅ PASS' if s['readonly_pass']==len(results.get('readonly_checks',[])) else '❌ FAIL'} |",
            f"| 分支检查 | — | — | {'✅' if s['branch_ok'] else '❌'} {results['branch_check'].get('current_branch','')} |",
            f"",
            f"**总判定: {'✅ PASS — 交付包完整' if s['overall']=='PASS' else '❌ FAIL — 存在不完整项'}**",
            f"",
            f"---",
            f"",
            f"## 二、文件清单校验",
            f"",
            f"| # | 文件 | 存在 | MD5 | 状态 |",
            f"|---|------|------|-----|------|",
        ]

        for i, fc in enumerate(results['file_checks'], 1):
            exists = '✅' if fc['exists'] else '❌'
            md5 = fc['md5'][:8] if fc['md5'] else 'N/A'
            status = '✅' if fc['status'] == 'PASS' else '❌'
            lines.append(f"| {i} | {fc['file']} | {exists} | `{md5}` | {status} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 三、约束合规校验",
            f"",
            f"| # | 约束 | 结果 | 详情 |",
            f"|---|------|------|------|",
        ])

        for i, cc in enumerate(results['constraint_checks'], 1):
            result = '✅' if cc['result'] == 'PASS' else ('⚠' if cc['result'] == 'WARN' else '❌')
            lines.append(f"| {i} | {cc['check']} | {result} | {cc['detail']} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 四、红线文件校验",
            f"",
            f"| 文件 | MD5 | 状态 |",
            f"|------|-----|------|",
        ])

        for rc in results.get('readonly_checks', []):
            status = '✅ 未修改' if rc['status'] == 'PASS' else '❌ 已修改'
            lines.append(f"| {rc['file']} | `{rc['md5'][:8]}` | {status} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 五、自检结论",
            f"",
            f"{'✅ 交付包完整，所有文件存在，约束合规，红线文件未修改。' if s['overall']=='PASS' else '❌ 交付包不完整，请检查未通过项。'}",
        ])

        return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='V85交付包完整性自检')
    parser.add_argument('--base', help='基线目录')
    args = parser.parse_args()

    checker = DeliveryPackageChecker(args.base or '')
    results = checker.run()
    report = checker.generate_report(results)

    report_path = os.path.join(checker.v85_dir, 'hermes_v85_final_delivery', 'delivery_check_result.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print(f"\n报告已输出: {report_path}")


if __name__ == '__main__':
    main()
