#!/usr/bin/env python3
"""
DSHB V86-RC2 文档口径常态化巡检脚本
自动扫描新增文档，检测旧口径"桥接率100%"违规表述，输出告警。
杜绝旧口径表述复现。

工单: DSHB_V86_RC2_DOC_CALIBER_SCANNER_T3.5
约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

用法:
  python3 doc_caliber_scanner.py                          # 扫描当前目录
  python3 doc_caliber_scanner.py --dir <path>             # 扫描指定目录
  python3 doc_caliber_scanner.py --fix                    # 自动修复(标注OLD_CALIBER)
  python3 doc_caliber_scanner.py --report <path>          # 输出报告到指定文件
"""

import os, sys, re, json
from pathlib import Path
from datetime import datetime
from copy import deepcopy

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════
DEFAULT_CONFIG = {
    "scan_dir": str(Path(__file__).parent),
    "file_patterns": ["*.md", "*.json", "*.txt", "*.py"],
    "report_file": "v86_rc2_dshb_doc_caliber_scan_report.md",
    "hermes_caliber": {
        "metadata_completion_rate": 0.736,
        "data_fetchable_rate": 0.0,
        "effective_bridge_rate": 0.0,
        "threshold": 0.80,
    },
    "old_caliber_markers": [
        "OLD_CALIBER",
        "HERMES_INVALID",
        "HERMES_REVISED",
        "METADATA_ONLY",
    ],
}

# ═══════════════════════════════════════════════════════════
# 旧口径违规模式
# ═══════════════════════════════════════════════════════════
VIOLATION_PATTERNS = [
    {
        "id": "V001",
        "pattern": r"桥接率[^\n]*(?:100%|100%)",
        "description": "桥接率100%违规表述",
        "severity": "CRITICAL",
    },
    {
        "id": "V002",
        "pattern": r"有效桥接率[^\n]*(?:100%|100%)",
        "description": "有效桥接率100%违规表述",
        "severity": "CRITICAL",
    },
    {
        "id": "V003",
        "pattern": r"COMPLETED[^\n]*(?:100%|100%)",
        "description": "COMPLETED率100%违规表述",
        "severity": "CRITICAL",
    },
    {
        "id": "V004",
        "pattern": r"100%[^\n]*桥接",
        "description": "100%+桥接 违规表述",
        "severity": "CRITICAL",
    },
    {
        "id": "V005",
        "pattern": r"BRIDGE_RATE[^\n]*100",
        "description": "BRIDGE_RATE=100% 违规",
        "severity": "CRITICAL",
    },
    {
        "id": "V006",
        "pattern": r"元数据完成率[^\n]*等同于[^\n]*有效桥接率",
        "description": "元数据完成率等同于有效桥接率",
        "severity": "HIGH",
    },
    {
        "id": "V007",
        "pattern": r"100%[^\n]*有效桥接",
        "description": "100%+有效桥接 违规",
        "severity": "CRITICAL",
    },
]


# ═══════════════════════════════════════════════════════════
# 口径扫描引擎
# ═══════════════════════════════════════════════════════════
class CaliberScanner:
    """文档口径扫描引擎"""

    def __init__(self, config=None, auto_fix=False):
        self.config = config or DEFAULT_CONFIG
        self.scan_dir = Path(self.config["scan_dir"])
        self.auto_fix = auto_fix
        self.violations = []  # [(file, line_num, pattern_id, severity, line_text, fixed)]
        self.scanned_files = 0
        self.total_matches = 0
        self.start_time = datetime.now()

    def scan_file(self, filepath):
        """扫描单个文件"""
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return []

        violations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pat_info in VIOLATION_PATTERNS:
                matches = re.findall(pat_info["pattern"], line)
                for match in matches:
                    # 检查是否已标注OLD_CALIBER
                    is_marked = any(
                        marker in line for marker in self.config["old_caliber_markers"]
                    )

                    if is_marked:
                        # 已标注, 不算违规 (但统计)
                        violations.append({
                            "file": str(filepath.relative_to(self.scan_dir)),
                            "line_num": line_num,
                            "pattern_id": pat_info["id"],
                            "description": pat_info["description"],
                            "severity": pat_info["severity"],
                            "line_text": line.strip()[:200],
                            "is_marked": True,
                            "fixed": False,
                        })
                    else:
                        violations.append({
                            "file": str(filepath.relative_to(self.scan_dir)),
                            "line_num": line_num,
                            "pattern_id": pat_info["id"],
                            "description": pat_info["description"],
                            "severity": pat_info["severity"],
                            "line_text": line.strip()[:200],
                            "is_marked": False,
                            "fixed": False,
                        })

        return violations

    def scan_all(self):
        """扫描所有文件"""
        all_violations = []

        for pattern in self.config["file_patterns"]:
            for filepath in self.scan_dir.rglob(pattern):
                if not filepath.is_file():
                    continue
                # 跳过虚拟环境和构建目录
                if any(skip in str(filepath) for skip in [".git", "__pycache__", "node_modules"]):
                    continue

                self.scanned_files += 1
                file_violations = self.scan_file(filepath)
                all_violations.extend(file_violations)

                if self.auto_fix and not filepath.suffix == ".py":
                    # 自动修复: 为未标注的违规行添加OLD_CALIBER标记
                    for v in file_violations:
                        if not v["is_marked"] and v["severity"] == "CRITICAL":
                            # 读取文件, 添加标注
                            content = filepath.read_text(encoding="utf-8", errors="replace")
                            lines = content.split("\n")
                            if v["line_num"] <= len(lines):
                                old_line = lines[v["line_num"] - 1]
                                new_line = old_line.rstrip() + " [OLD_CALIBER - METADATA_ONLY, HERMES_INVALID]"
                                lines[v["line_num"] - 1] = new_line
                                filepath.write_text("\n".join(lines), encoding="utf-8")
                                v["fixed"] = True
                            break  # 每个文件只修复一次

        self.violations = all_violations
        self.total_matches = len(all_violations)
        return all_violations

    def generate_report(self):
        """生成扫描报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        critical_count = sum(1 for v in self.violations if v["severity"] == "CRITICAL")
        high_count = sum(1 for v in self.violations if v["severity"] == "HIGH")
        marked_count = sum(1 for v in self.violations if v["is_marked"])
        unmarked_count = sum(1 for v in self.violations if not v["is_marked"])
        fixed_count = sum(1 for v in self.violations if v["fixed"])

        lines = [
            f"# DSHB V86-RC2 文档口径扫描报告",
            f"",
            f"> **自动生成**: doc_caliber_scanner.py",
            f"> **扫描时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> **扫描耗时**: {duration:.1f}秒",
            f"> **扫描目录**: `{self.scan_dir}`",
            f"> **扫描文件数**: {self.scanned_files}",
            f"> **总匹配数**: {self.total_matches}",
            f"> **CRITICAL违规**: {critical_count}",
            f"> **HIGH违规**: {high_count}",
            f"> **已标注(合规)**: {marked_count}",
            f"> **未标注(违规)**: {unmarked_count}",
            f"> **自动修复**: {fixed_count} {'✅' if fixed_count > 0 else '(未启用--fix)'}",
            f"",
            f"---",
            f"",
            f"## 1. 扫描结果",
            f"",
        ]

        if unmarked_count == 0:
            lines.append(f"### ✅ 全部通过 — 未发现未标注的旧口径违规表述")
            lines.append(f"")
        else:
            lines.append(f"### ❌ 发现 {unmarked_count} 处未标注的旧口径违规")
            lines.append(f"")
            lines.append(f"| # | 文件 | 行号 | 违规ID | 严重度 | 描述 | 匹配内容 |")
            lines.append(f"|---|------|------|--------|--------|------|----------|")

            idx = 0
            for v in self.violations:
                if not v["is_marked"]:
                    idx += 1
                    lines.append(
                        f"| {idx} | `{v['file']}` | L{v['line_num']} | "
                        f"{v['pattern_id']} | {v['severity']} | "
                        f"{v['description']} | {v['line_text'][:100]} |"
                    )

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 2. 已标注的旧口径记录 (合规保留)",
            f"",
        ])

        if marked_count > 0:
            lines.append(f"| # | 文件 | 行号 | 违规ID | 匹配内容 |")
            lines.append(f"|---|------|------|--------|----------|")
            idx = 0
            for v in self.violations:
                if v["is_marked"]:
                    idx += 1
                    lines.append(
                        f"| {idx} | `{v['file']}` | L{v['line_num']} | "
                        f"{v['pattern_id']} | {v['line_text'][:100]} |"
                    )
        else:
            lines.append(f"无已标注的旧口径记录。")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 3. HERMES双口径基线",
            f"",
            f"| 指标 | 值 | 来源 |",
            f"|------|-----|------|",
            f"| 元数据映射完成率 | {self.config['hermes_caliber']['metadata_completion_rate']*100:.1f}% | 131/178 |",
            f"| 真实有效桥接率 | {self.config['hermes_caliber']['data_fetchable_rate']*100:.1f}% | 0/178 |",
            f"| 有效桥接率 | {self.config['hermes_caliber']['effective_bridge_rate']*100:.1f}% | 0/178 |",
            f"| Gate阈值 | {self.config['hermes_caliber']['threshold']*100:.0f}% | data_fetchable ≥ 阈值 → READY |",
            f"",
            f"---",
            f"",
            f"## 4. 约束合规声明",
            f"",
            f"| 约束 | 值 |",
            f"|------|-----|",
            f"| NO_ZHIJI_API_CALL | FALSE |",
            f"| NO_MODIFY_V85 | TRUE |",
            f"| NO_OVERWRITE | TRUE |",
            f"| BRANCH_LOCKED | TRUE |",
            f"| 双指标强制输出 | 元数据完成率 + 真实有效桥接率 |",
            f"| 流水线退回旧日志作废 | 不可复用 |",
            f"| DEP_BLOCK不计入内部缺陷 | HERMES五类分类 |",
            f"| Gate准入不豁免 | data_fetchable < 80% → NOT_READY |",
            f"",
            f"---",
            f"",
            f"**报告生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**报告版本**: V1.0",
            f"**关联工单**: DSHB_V86_RC2_DOC_CALIBER_SCANNER_T3.5",
            f"",
        ])

        report_content = "\n".join(lines)

        report_path = self.scan_dir / self.config["report_file"]
        report_path.write_text(report_content, encoding="utf-8")

        return report_path, report_content


# ═══════════════════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════════════════
def parse_args(args):
    opts = {
        "dir": None,
        "fix": False,
        "report": None,
    }
    i = 0
    while i < len(args):
        if args[i] == "--dir" and i + 1 < len(args):
            opts["dir"] = args[i + 1]
            i += 2
        elif args[i] == "--fix":
            opts["fix"] = True
            i += 1
        elif args[i] == "--report" and i + 1 < len(args):
            opts["report"] = args[i + 1]
            i += 2
        else:
            i += 1
    return opts


def main():
    opts = parse_args(sys.argv[1:])

    config = deepcopy(DEFAULT_CONFIG)
    if opts["dir"]:
        config["scan_dir"] = str(Path(opts["dir"]).resolve())
    if opts["report"]:
        config["report_file"] = str(Path(opts["report"]).resolve())

    scanner = CaliberScanner(config=config, auto_fix=opts["fix"])

    # 执行扫描
    violations = scanner.scan_all()

    # 生成报告
    report_path, report_content = scanner.generate_report()

    # 输出摘要到stdout
    print(f"\n{'='*60}")
    print(f"  文档口径扫描完成")
    print(f"  扫描文件: {scanner.scanned_files}")
    print(f"  总匹配: {scanner.total_matches}")
    print(f"  CRITICAL: {sum(1 for v in violations if v['severity'] == 'CRITICAL')}")
    print(f"  HIGH: {sum(1 for v in violations if v['severity'] == 'HIGH')}")
    print(f"  已标注(合规): {sum(1 for v in violations if v['is_marked'])}")
    print(f"  未标注(违规): {sum(1 for v in violations if not v['is_marked'])}")
    print(f"  自动修复: {sum(1 for v in violations if v['fixed'])}")
    print(f"  报告: {report_path}")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
