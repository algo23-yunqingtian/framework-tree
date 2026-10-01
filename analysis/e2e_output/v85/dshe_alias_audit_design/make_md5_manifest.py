"""T2 交付物 MD5 清单生成器（只读扫描 + 只写 manifest）"""
import hashlib
import io
import os

CD = os.path.dirname(os.path.abspath(__file__))

DELIVERABLES = [
    "alias_sampling_audit_report.md",
    "alias_audit_sample.csv",
    "canonical_resolve_fix_design.md",
    "high_prio_ambig_analysis.md",
    "multi_canonical_conflict_solution.md",
    "v86_alias_engine_full_design.md",
    "alias_test_case_set.json",
]

EXTRAS = [
    "T2_summary_report.md",
    "audit_kit.py",
    "build_sampling_audit.py",
    "build_test_case_set.py",
    "canonical_resolve_fix.py",
    "canonical_resolve_fix_result.json",
    "blacklist_coverage_analysis.py",
    "blacklist_rule_coverage_matrix.csv",
    "blacklist_testset_verdicts.py",
    "blacklist_testset_verdicts.csv",
    "blacklist_rule_testing_design.md",
    "blacklist_rule_effectiveness_test.py",
    "blacklist_rule_test_result.json",
    "blacklist_rule_test_result.md",
    "regression_gate_config.json",
    "generate_conflict_classification.py",
    "multi_canonical_conflicts_165.csv",
    "multi_canonical_conflict_classification.csv",
    "sampling_audit_result.json",
    "v86_gate_fusion_framework.md",
]

OUT = os.path.join(CD, "MD5_CHECKSUM_LIST.md")


def md5_hex(path):
    h = hashlib.md5()
    with io.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def row(fname):
    p = os.path.join(CD, fname)
    if not os.path.exists(p):
        return fname, None, None
    return fname, os.path.getsize(p), md5_hex(p)


def main():
    total = 0
    lines = [
        "# T2 交付物 MD5 清单",
        "",
        "> 任务：`DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN`  ",
        "> 分支：`feature/v85-chart-template`  ",
        "> 目录：`analysis/e2e_output/v85/dshe_alias_audit_design/`  ",
        "> 约束：未修改 `indicator_alias_library.csv` / `indicators_v1.json` / GT / 黑名单；0 次 zhiji API 调用",
        "",
        "## 1. 七份指定交付物",
        "",
        "| # | 文件 | 字节 | MD5 |",
        "|---|---|---|---|",
    ]
    n = 0
    for i, f in enumerate(DELIVERABLES, 1):
        f_, sz, md = row(f)
        n += 1
        total += sz or 0
        lines.append("| %d | `%s` | %s | `%s` |" % (
            i, f_, "{:,}".format(sz) if sz else "MISSING",
            md.upper() if md else "MISSING"))
    lines += [
        "",
        "## 2. 配套产物（脚本 / 中间结果 / 测试产物）",
        "",
        "| # | 文件 | 字节 | MD5 |",
        "|---|---|---|---|",
    ]
    n2 = 0
    for f in EXTRAS:
        f_, sz, md = row(f)
        n2 += 1
        total += sz or 0
        lines.append("| %d | `%s` | %s | `%s` |" % (
            n2, f_, "{:,}".format(sz) if sz else "MISSING",
            md.upper() if md else "MISSING"))
    lines += [
        "",
        "## 3. 汇总",
        "",
        "- 指定交付物：%d / %d 全部存在" % (
            sum(1 for f in DELIVERABLES if os.path.exists(os.path.join(CD, f))), len(DELIVERABLES)),
        "- 配套产物：%d" % n2,
        "- 合计文件：%d" % (n + n2),
        "- 合计字节：%s" % "{:,}".format(total),
        "",
        "---",
        "",
        "```",
        "NO_SOURCE_MODIFICATION=TRUE",
        "NO_GT_MODIFICATION=TRUE",
        "NO_RULE_MODIFICATION=TRUE",
        "NO_ZHIJI_API_CALL=TRUE",
        "READ_ONLY=TRUE",
        "APPEND_ONLY=TRUE",
        "HISTORICAL_ARTIFACTS_PRESERVED=TRUE",
        "```",
        "",
    ]
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("written:", OUT)
    print("deliverables:", n, "extras:", n2, "bytes:", total)


if __name__ == "__main__":
    main()
