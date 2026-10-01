#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enhanced_archive_builder.py — V85增强归档打包脚本

工单: HERMES_V85_PRE_ARCHIVE_PACKAGE_PREP_AND_RELEASE_NOTE

功能:
  1. 自动按交付目录树复制所有产出到归档目录
  2. 生成汇总MD5清单
  3. 生成git tag标记说明
  4. 依赖项校验: 检测DSHB sim_sceneA/B_result.csv, 缺失时警告不阻断

用法:
  python3 enhanced_archive_builder.py
  python3 enhanced_archive_builder.py --base /home/ubuntu/framework-tree
  python3 enhanced_archive_builder.py --output ./v85_archive
"""

import os
import sys
import shutil
import hashlib
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# V85交付目录树定义
ARCHIVE_TREE = {
    'hermes_v85_final_delivery': [
        'enhanced_review_portal_v6_final.md',
        'portal_operation_manual_v7.md',
        'v85_full_delivery_manifest_v2.md',
        'v85_delivery_readme.md',
        'delivery_package_check.py',
        'delivery_check_result.md',
        'v85_gate_final_acceptance_report.md',
        'v85_archive_folder_tree.md',
        'v85_demo_overview.md',
    ],
    'hermes_human_review_tool': [
        'enhanced_review_portal_v5_review_workbench.md',
        'portal_operation_manual_v6.md',
        'batch_export_import_v2.py',
        'batch_tool_manual.md',
        'gate_dashboard_spec.md',
        'human_review_archive_spec.md',
        'gate_pre_check.py',
        'v85_p0_risk_human_workbook.csv',
        'gate_block_tracker.csv',
        'review_batches_v6/batch_A_review_v6.csv',
        'review_batches_v6/batch_B_review_v6.csv',
        'review_batches_v6/batch_C_review_v6.csv',
        'review_batches_v6/review_checklist_v6.md',
    ],
    'hermes_portal_gate_final': [
        'enhanced_review_portal_v5_full.md',
        'portal_operation_manual_v5.md',
        'v85_gate_rerun_check_result.md',
        'mapping_fill_helper_v2.py',
        'batch_export_import.py',
        'indicator_alias_library.csv',
        'high_risk_confusion_pairs.csv',
    ],
    'hermes_portal_sim_demo': [
        'enhanced_review_portal_v6_sim_demo.md',
        'portal_operation_manual_v7_sim.md',
        'demo_data_package.md',
        'gate_sceneA_report.md',
        'gate_sceneB_report.md',
        'gate_scenario_compare.md',
        'v85_accept_demo_script.md',
    ],
    'dshb_full_integrate': [
        'semantic_blacklist_v85_final.json',
        'full_488_template_playback_result.csv',
        'cross_variety_p0_validation.csv',
        'inconsistent_risk_items.csv',
        'dsh_gate_self_check.md',
    ],
    'dshb_human_review_prep': [
        'v85_p0_risk_human_workbook.csv',
        'gate_block_tracker.csv',
        'human_review_operation_guide.md',
        'bl009a_review_package.md',
        'data_missing_p0_summary.md',
        'v86_rule_migration_checklist.md',
    ],
    'dshb_review_simulation': [
        'sim_sceneA_result.csv',
        'sim_sceneB_result.csv',
        'simulation_compare_report.md',
        'gate_block_impact_analysis.md',
        'bl009a_multi_scenario_verify.md',
        'review_consistency_check.py',
        'review_consistency_guide.md',
        'build_review_simulation.py',
        'MD5_MANIFEST.md',
        'human_review_faq.md',
    ],
    'miss_risk_mining': [
        'unified_indicator_risk_db_v2.csv',
        'dsh_gate_self_check_v2.md',
        'p0_miss_4_case_analysis.md',
        'p0_unhit_5_items_report.md',
        'blacklist_extend_candidate_v2.json',
        'rule_defect_summary.md',
    ],
    'dshb_full_integrate_extra': [
        'dshb_final_gate_acceptance.md',
    ],
    'dshb_simulation': [
        'sim_sceneA_result.csv',
        'sim_sceneB_result.csv',
    ],
}

# 依赖项(检测是否存在, 缺失仅警告)
DEPENDENCY_CHECKS = [
    {
        'name': 'DSHB sim_sceneA_result.csv',
        'path': 'dshb_review_simulation/sim_sceneA_result.csv',
        'required': False,
        'warning': 'DSHB sim_sceneA_result.csv未落盘, 场景A演示数据使用自构建版',
    },
    {
        'name': 'DSHB sim_sceneB_result.csv',
        'path': 'dshb_review_simulation/sim_sceneB_result.csv',
        'required': False,
        'warning': 'DSHB sim_sceneB_result.csv未落盘, 场景B演示数据使用自构建版',
    },
    {
        'name': 'DSHB dshb_final_gate_acceptance.md',
        'path': 'dshb_full_integrate/dsh_final_gate_acceptance.md',
        'required': False,
        'warning': 'DSHB最终Gate验收报告未落盘, 使用DSHB Gate v2自检替代',
    },
]


class EnhancedArchiveBuilder:
    """V85增强归档打包器"""

    def __init__(self, base_dir: str, output_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self.v85_dir = os.path.join(self.base_dir, 'analysis', 'e2e_output', 'v85')
        self.output_dir = os.path.abspath(output_dir)
        self.results = {
            'copied_files': [],
            'skipped_files': [],
            'md5_manifest': [],
            'dependency_warnings': [],
            'missing_files': [],
            'summary': {},
        }

    def calc_md5(self, filepath: str) -> str:
        """计算文件MD5"""
        if not os.path.exists(filepath):
            return ''
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def check_dependencies(self):
        """依赖项校验"""
        for dep in DEPENDENCY_CHECKS:
            dep_path = os.path.join(self.v85_dir, dep['path'])
            exists = os.path.exists(dep_path)
            if not exists:
                self.results['dependency_warnings'].append({
                    'name': dep['name'],
                    'path': dep['path'],
                    'required': dep['required'],
                    'warning': dep['warning'],
                    'status': 'WARN',
                })
                if dep['required']:
                    self.results['missing_files'].append(dep['name'])
            else:
                self.results['dependency_warnings'].append({
                    'name': dep['name'],
                    'path': dep['path'],
                    'status': 'OK',
                })

    def copy_files(self):
        """按目录树复制文件"""
        os.makedirs(self.output_dir, exist_ok=True)

        for subdir, files in ARCHIVE_TREE.items():
            src_dir = os.path.join(self.v85_dir, subdir)
            dst_dir = os.path.join(self.output_dir, subdir)

            if not os.path.exists(src_dir):
                # 目录不存在，跳过
                for f in files:
                    self.results['skipped_files'].append({
                        'file': os.path.join(subdir, f),
                        'reason': 'source directory not found',
                    })
                continue

            os.makedirs(dst_dir, exist_ok=True)

            for f in files:
                src = os.path.join(src_dir, f)
                dst = os.path.join(dst_dir, f)

                # 确保目标子目录存在
                os.makedirs(os.path.dirname(dst), exist_ok=True)

                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    md5 = self.calc_md5(dst)
                    self.results['copied_files'].append({
                        'file': os.path.join(subdir, f),
                        'md5': md5,
                        'size': os.path.getsize(dst),
                    })
                    self.results['md5_manifest'].append({
                        'file': os.path.join(subdir, f),
                        'md5': md5,
                    })
                else:
                    self.results['skipped_files'].append({
                        'file': os.path.join(subdir, f),
                        'reason': 'source file not found',
                    })
                    self.results['missing_files'].append(f'{subdir}/{f}')

    def generate_md5_manifest(self) -> str:
        """生成MD5清单"""
        lines = [
            '# V85 归档包 MD5清单',
            '',
            f'> 生成时间: {datetime.now().isoformat()}',
            f'> 归档目录: {self.output_dir}',
            f'> 文件数: {len(self.results["md5_manifest"])}',
            '',
            '| # | 文件 | MD5 | 大小 |',
            '|---|------|-----|------|',
        ]
        for i, item in enumerate(self.results['md5_manifest'], 1):
            lines.append(f'| {i} | {item["file"]} | `{item["md5"][:8]}` | {item.get("size", "N/A")}B |')
        return '\n'.join(lines)

    def generate_git_tag_note(self) -> str:
        """生成git tag标记说明"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True, cwd=self.base_dir
            )
            commit = result.stdout.strip()
        except:
            commit = 'N/A'

        lines = [
            '# V85 归档包 Git Tag 标记说明',
            '',
            '```',
            f'git tag -a v85-final -m "V85 Final Delivery Package',
            f'',
            f'- Commit: {commit}',
            f'- 分支: feature/v85-chart-template',
            f'- 日期: 2026-10-01',
            f'- 文件数: {len(self.results["copied_files"])}',
            f'- Gate状态: ❌ 4/5 BLOCKED (待人工评审5-7天)',
            f'',
            f'核心能力:',
            f'  - 488模板风险管控',
            f'  - 31条黑名单规则',
            f'  - 50条风险库v2',
            f'  - 864条别名库',
            f'  - 46项Gate检查',
            f'  - 人工评审工具+Gate预校验',
            f'  - 3套上线场景(基线/A/B)",',
            f'',
            f'git push origin v85-final',
            f'```',
        ]
        return '\n'.join(lines)

    def generate_report(self) -> str:
        """生成打包报告"""
        now = datetime.now().isoformat()

        # 统计
        total_copied = len(self.results['copied_files'])
        total_skipped = len(self.results['skipped_files'])
        total_warnings = len([w for w in self.results['dependency_warnings'] if w['status'] == 'WARN'])
        total_missing = len(self.results['missing_files'])

        lines = [
            '# V85 增强归档打包报告',
            '',
            f'> 生成时间: {now}',
            f'> 基线目录: {self.v85_dir}',
            f'> 归档目录: {self.output_dir}',
            '',
            '---',
            '',
            '## 一、打包总览',
            '',
            '| 项目 | 数量 | 状态 |',
            '|------|------|------|',
            f'| 已复制文件 | {total_copied} | ✅ |',
            f'| 跳过文件 | {total_skipped} | ⚠ |',
            f'| 依赖警告 | {total_warnings} | ⚠ |',
            f'| 缺失文件 | {total_missing} | {"❌" if total_missing > 0 else "✅"} |',
            '',
            f'**总判定: {"✅ PASS" if total_missing == 0 else "❌ FAIL"}**',
            '',
            '---',
            '',
            '## 二、依赖项校验',
            '',
            '| 依赖项 | 状态 | 说明 |',
            '|--------|------|------|',
        ]

        for w in self.results['dependency_warnings']:
            if w['status'] == 'WARN':
                status = '⚠ WARN'
                detail = w['warning']
            else:
                status = '✅ OK'
                detail = '存在'
            lines.append(f'| {w["name"]} | {status} | {detail} |')

        lines.extend([
            '',
            '---',
            '',
            '## 三、已复制文件清单',
            '',
            '| # | 文件 | MD5 | 大小 |',
            '|---|------|-----|------|',
        ])

        for i, f in enumerate(self.results['copied_files'], 1):
            size = f'{f["size"]:,}B' if f.get('size') else 'N/A'
            lines.append(f'| {i} | {f["file"]} | `{f["md5"][:8]}` | {size} |')

        if self.results['skipped_files']:
            lines.extend([
                '',
                '---',
                '',
                '## 四、跳过文件',
                '',
                '| 文件 | 原因 |',
                '|------|------|',
            ])
            for f in self.results['skipped_files']:
                lines.append(f'| {f["file"]} | {f["reason"]} |')

        lines.extend([
            '',
            '---',
            '',
            '## 五、后续步骤',
            '',
            '```bash',
            '# 1. 验证打包完整性',
            f'md5sum -c {os.path.join(self.output_dir, "MD5_MANIFEST.md")}',
            '',
            '# 2. 打git tag',
            'git tag -a v85-final -m "V85 Final Delivery Package"',
            'git push origin v85-final',
            '',
            '# 3. 压缩归档',
            f'tar -czf v85_final_archive_$(date +%Y%m%d).tar.gz {self.output_dir}/',
            '',
            '# 4. 异地备份',
            f'cp -r {self.output_dir} /home/ubuntu/backup/v85/',
            '```',
        ])

        return '\n'.join(lines)

    def build(self) -> Dict:
        """执行完整打包"""
        self.check_dependencies()
        self.copy_files()

        # 写入MD5清单
        md5_content = self.generate_md5_manifest()
        md5_path = os.path.join(self.output_dir, 'MD5_MANIFEST.md')
        with open(md5_path, 'w', encoding='utf-8') as f:
            f.write(md5_content)

        # 写入git tag说明
        tag_content = self.generate_git_tag_note()
        tag_path = os.path.join(self.output_dir, 'GIT_TAG_NOTE.md')
        with open(tag_path, 'w', encoding='utf-8') as f:
            f.write(tag_content)

        # 生成报告
        report = self.generate_report()
        report_path = os.path.join(self.output_dir, 'ARCHIVE_BUILD_REPORT.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # 汇总
        self.results['summary'] = {
            'copied': len(self.results['copied_files']),
            'skipped': len(self.results['skipped_files']),
            'warnings': len([w for w in self.results['dependency_warnings'] if w['status'] == 'WARN']),
            'missing': len(self.results['missing_files']),
            'md5_manifest_path': md5_path,
            'git_tag_note_path': tag_path,
            'report_path': report_path,
            'overall': 'PASS' if len(self.results['missing_files']) == 0 else 'FAIL',
        }

        return self.results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='V85增强归档打包脚本')
    parser.add_argument('--base', default='', help='基线目录')
    parser.add_argument('--output', default='', help='输出目录')
    args = parser.parse_args()

    base_dir = args.base or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'
    )
    # 如果base不存在，尝试向上搜索
    if not os.path.exists(os.path.join(base_dir, 'analysis')):
        # 从脚本目录向上找framework-tree
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = script_dir
        while 'analysis' not in os.listdir(base_dir):
            base_dir = os.path.dirname(base_dir)
            if base_dir == '/':
                break

    output_dir = args.output or os.path.join(base_dir, 'v85_final_archive')

    print(f"基线目录: {base_dir}")
    print(f"输出目录: {output_dir}")
    print()

    builder = EnhancedArchiveBuilder(base_dir, output_dir)
    results = builder.build()

    print(f"=== 打包完成 ===")
    print(f"已复制: {results['summary']['copied']}")
    print(f"跳过: {results['summary']['skipped']}")
    print(f"警告: {results['summary']['warnings']}")
    print(f"缺失: {results['summary']['missing']}")
    print(f"总判定: {results['summary']['overall']}")
    print()
    print(f"MD5清单: {results['summary']['md5_manifest_path']}")
    print(f"Git Tag说明: {results['summary']['git_tag_note_path']}")
    print(f"打包报告: {results['summary']['report_path']}")

    # 打印依赖警告
    if results['summary']['warnings'] > 0:
        print()
        print("=== 依赖警告 ===")
        for w in results['dependency_warnings']:
            if w['status'] == 'WARN':
                print(f"  ⚠ {w['name']}: {w['warning']}")


if __name__ == '__main__':
    main()
