#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 批量证据包预审调度器 (batch_evidence_audit_runner.py)

工单: 工单-HERMES / T3.3 批量预审调度脚本开发
分支: feature/v85-chart-template @ dcf7194
编制方: HERMES (L3 审计方)
日期: 2026-10-15

用途
----
自动读取指定目录下的 L1/L2 证据包 (EVIDENCE_CONTRACT_V1)，
批量调用 evidence_auditor_v2 校验，输出汇总预审报告：
- 每包 PASS/CONDITIONAL_PASS/FAIL 结论
- 按风险等级 (CRITICAL/HIGH/MEDIUM/LOW) 分组
- 按审计规则分组统计
- 告警汇总与责任方路由
- 机器可读 JSON + 人可读 Markdown

契约输入
--------
EVIDENCE_CONTRACT_V1.md  (T3.2, 三方证据包契约基线)
v86_rc2_dep_registry_common_spec.md  (DEP 登记与状态机)

用法
----
  python3 batch_evidence_audit_runner.py --dir <证据包目录>
  python3 batch_evidence_audit_runner.py --dir <目录> --md <报告.md> --json <报告.json>
  python3 batch_evidence_audit_runner.py --dir <目录> --l1 <L1目录> --l2 <L2目录>
  python3 batch_evidence_audit_runner.py --demo     # 用内置夹具演示批量调度
  python3 batch_evidence_audit_runner.py --self-test

约束
----
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
本调度器纯离线，不发网络请求。
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime

RUNNER_VERSION = "1.0.0"
BRANCH_BASELINE = "dcf7194"

# 规则 -> 责任方 路由表 (v86_rc2_hermes_alert_routing_spec.md §3.1)
RULE_OWNER = {
    "R-AUDIT-01": ("DSHB", "双证据 COMPLETED"),
    "R-AUDIT-02": ("DSHB", "桥接率口径"),
    "R-AUDIT-03": ("DSHE", "L2 独立调用链"),
    "R-AUDIT-04": ("DSHB", "Gate 强制项 G-09/G-10"),
    "R-CONTRACT-V1": ("提交方", "契约完整性"),
    "R-DEP-STATE": ("DSHB/DSHE", "DEP 状态机与台账"),
    "R-LEGACY-CAL": ("DSHB", "存量旧口径残留"),
}

LEVEL_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
PASS, CONDITIONAL_PASS, FAIL = "PASS", "CONDITIONAL_PASS", "FAIL"


def load_auditor():
    """动态导入 evidence_auditor_v2 (与本脚本同目录)"""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        from evidence_auditor_v2 import EvidenceAuditor, build_case_library
    except ImportError:
        raise SystemExit(
            "ERROR: 未找到 evidence_auditor_v2.py, 请置于同目录")
    return EvidenceAuditor, build_case_library


def scan_evidence_files(dirs):
    """扫描目录下所有 .json 证据包"""
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        files.extend(glob.glob(os.path.join(d, "*.json")))
    return sorted(files)


def is_evidence_package(path):
    """判断 JSON 是否为证据包 (含 calls 或 contract_version)"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False, None
        if "contract_version" in data or "calls" in data or \
                "fingerprint" in data:
            return True, data
        return False, None
    except (json.JSONDecodeError, OSError):
        return False, None


def audit_one(path, EvidenceAuditor):
    """审计单个证据包"""
    ok, data = is_evidence_package(path)
    if not ok:
        return {
            "file": os.path.basename(path),
            "path": path,
            "status": "SKIPPED",
            "reason": "非证据包格式 (缺 contract_version/calls/fingerprint)",
        }
    report = EvidenceAuditor(data).verdict()
    return {
        "file": os.path.basename(path),
        "path": path,
        "status": report["verdict"],
        "fingerprint": report.get("fingerprint"),
        "run_id": report.get("run_id"),
        "dep_registry_id": report.get("dep_registry_id"),
        "gate_result": report.get("gate_result"),
        "gate_g06": report.get("gate_g06_real_fetchable_rate"),
        "gate_g09": report.get("gate_g09_script_audit"),
        "gate_g10": report.get("gate_g10_data_fetch"),
        "events_summary": report["events_summary"],
        "events_by_rule": report.get("events_by_rule", {}),
        "events": report["events"],
        "report": report,
    }


def summarize(results):
    """汇总批量审计结果"""
    audited = [r for r in results if r["status"] != "SKIPPED"]
    skipped = [r for r in results if r["status"] == "SKIPPED"]

    by_verdict = {PASS: 0, CONDITIONAL_PASS: 0, FAIL: 0}
    for r in audited:
        by_verdict[r["status"]] = by_verdict.get(r["status"], 0) + 1

    # 按风险等级汇总
    by_level = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in audited:
        for lvl in by_level:
            by_level[lvl] += r["events_summary"].get(lvl, 0)

    # 按规则汇总
    by_rule = {}
    for r in audited:
        for rule, cnt in (r.get("events_by_rule") or {}).items():
            by_rule[rule] = by_rule.get(rule, 0) + cnt

    # 按责任方路由
    by_owner = {}
    for rule, cnt in by_rule.items():
        owner, desc = RULE_OWNER.get(rule, ("未知", rule))
        by_owner.setdefault(owner, {"rules": {}, "total": 0})
        by_owner[owner]["rules"][rule] = by_rule[rule]
        by_owner[owner]["total"] += cnt

    # Gate 汇总
    gate_ready = sum(1 for r in audited if r.get("gate_result") == "READY")
    gate_not = sum(1 for r in audited if r.get("gate_result") == "NOT_READY")

    # 最严重等级
    worst = None
    if by_level["CRITICAL"]:
        worst = "CRITICAL"
    elif by_level["HIGH"]:
        worst = "HIGH"
    elif by_level["MEDIUM"]:
        worst = "MEDIUM"
    elif by_level["LOW"]:
        worst = "LOW"

    return {
        "runner_version": RUNNER_VERSION,
        "baseline": BRANCH_BASELINE,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_files_scanned": len(results),
        "audited": len(audited),
        "skipped": len(skipped),
        "by_verdict": by_verdict,
        "by_level": by_level,
        "by_rule": by_rule,
        "by_owner": by_owner,
        "gate_ready": gate_ready,
        "gate_not_ready": gate_not,
        "worst_level": worst,
        "overall_verdict": (
            "BLOCKED" if by_level["CRITICAL"] else
            "CONDITIONAL" if by_level["HIGH"] or by_level["MEDIUM"] else
            "PASS"),
    }


def render_markdown(summary, results):
    lines = []
    lines.append("# V86-RC2 批量证据包预审汇总报告")
    lines.append("")
    lines.append("> 生成时间: %s" % summary["generated_at"])
    lines.append("> 调度器: batch_evidence_audit_runner v%s"
                 % summary["runner_version"])
    lines.append("> 基线: %s" % summary["baseline"])
    lines.append("> 契约: EVIDENCE_CONTRACT_V1")
    lines.append("")
    lines.append("## 1. 总体结论")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    lines.append("| 扫描文件 | %d |" % summary["total_files_scanned"])
    lines.append("| 实际审计 | %d |" % summary["audited"])
    lines.append("| 跳过 (非证据包) | %d |" % summary["skipped"])
    lines.append("| **总判定** | **%s** |" % summary["overall_verdict"])
    lines.append("| 最严重等级 | %s |" % (summary["worst_level"] or "无"))
    lines.append("| Gate READY | %d |" % summary["gate_ready"])
    lines.append("| Gate NOT_READY | %d |" % summary["gate_not_ready"])
    lines.append("")
    lines.append("## 2. 按判定分组")
    lines.append("")
    lines.append("| 判定 | 包数 |")
    lines.append("|------|------|")
    for k in (PASS, CONDITIONAL_PASS, FAIL):
        lines.append("| %s | %d |" % (k, summary["by_verdict"].get(k, 0)))
    lines.append("")
    lines.append("## 3. 按风险等级分组")
    lines.append("")
    lines.append("| 等级 | 告警数 |")
    lines.append("|------|--------|")
    for lvl in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        lines.append("| %s | %d |" % (lvl, summary["by_level"].get(lvl, 0)))
    lines.append("")
    lines.append("## 4. 按审计规则分组")
    lines.append("")
    if summary["by_rule"]:
        lines.append("| 规则 | 责任方 | 告警数 |")
        lines.append("|------|--------|--------|")
        for rule in sorted(summary["by_rule"]):
            owner, desc = RULE_OWNER.get(rule, ("未知", ""))
            lines.append("| %s (%s) | %s | %d |"
                         % (rule, desc, owner, summary["by_rule"][rule]))
    else:
        lines.append("_(无告警)_")
    lines.append("")
    lines.append("## 5. 告警责任方路由")
    lines.append("")
    if summary["by_owner"]:
        lines.append("| 责任方 | 告警数 | 涉及规则 |")
        lines.append("|--------|--------|---------|")
        for owner in sorted(summary["by_owner"]):
            o = summary["by_owner"][owner]
            rules = ", ".join(sorted(o["rules"]))
            lines.append("| %s | %d | %s |" % (owner, o["total"], rules))
    else:
        lines.append("_(无告警, 无需路由)_")
    lines.append("")
    lines.append("## 6. 逐包明细")
    lines.append("")
    lines.append("| 文件 | 判定 | Gate | G-06 | G-09 | G-10 | CRIT | HIGH | DEP |")
    lines.append("|------|------|------|------|------|------|------|------|-----|")
    for r in sorted(results, key=lambda x: x["file"]):
        if r["status"] == "SKIPPED":
            lines.append("| %s | SKIP | - | - | - | - | - | - | - |"
                         % r["file"])
            continue
        s = r["events_summary"]
        g06 = r.get("gate_g06")
        g06 = ("%.2f" % g06) if g06 is not None else "-"
        lines.append("| %s | %s | %s | %s | %s | %s | %d | %d | %s |"
                     % (r["file"], r["status"], r.get("gate_result"),
                        g06, r.get("gate_g09"), r.get("gate_g10"),
                        s["CRITICAL"], s["HIGH"],
                        r.get("dep_registry_id") or "-"))
    lines.append("")
    lines.append("## 7. CRITICAL 告警清单")
    lines.append("")
    crit_lines = []
    for r in results:
        if r["status"] == "SKIPPED":
            continue
        for e in r["events"]:
            if e["level"] == "CRITICAL":
                crit_lines.append(
                    "- **%s** [%s/%s] %s" % (r["file"], e["rule"],
                                             e["detect_point"], e["message"]))
    if crit_lines:
        lines.extend(crit_lines)
    else:
        lines.append("_(无 CRITICAL 告警)_")
    lines.append("")
    return "\n".join(lines)


def run_demo(EvidenceAuditor, build_case_library):
    """用内置用例库夹具演示批量调度"""
    cases = build_case_library()
    demo_dir = "/tmp/evidence_demo_%s" % datetime.now().strftime("%Y%m%d%H%M%S")
    os.makedirs(demo_dir, exist_ok=True)
    for cid in sorted(cases):
        path = os.path.join(demo_dir, "%s.json" % cid)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cases[cid]["payload"], f, ensure_ascii=False)
    return demo_dir


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 批量证据包预审调度器")
    ap.add_argument("--dir", help="证据包目录 (可多次指定, 或用逗号分隔)")
    ap.add_argument("--l1", help="L1 (DSHB) 证据包目录")
    ap.add_argument("--l2", help="L2 (DSHE) 证据包目录")
    ap.add_argument("--md", help="Markdown 报告输出路径")
    ap.add_argument("--json", dest="json_out", help="JSON 报告输出路径")
    ap.add_argument("--demo", action="store_true", help="内置夹具演示")
    ap.add_argument("--self-test", action="store_true", help="自检")
    args = ap.parse_args(argv)

    EvidenceAuditor, build_case_library = load_auditor()

    if args.self_test:
        return self_test(EvidenceAuditor, build_case_library)

    # 确定扫描目录
    dirs = []
    if args.demo:
        dirs = [run_demo(EvidenceAuditor, build_case_library)]
    else:
        for spec in filter(None, [args.dir]):
            dirs.extend([d.strip() for d in spec.split(",") if d.strip()])
        if args.l1:
            dirs.append(args.l1)
        if args.l2:
            dirs.append(args.l2)

    if not dirs:
        ap.print_help()
        print("\nERROR: 必须指定 --dir / --l1 / --l2 之一, 或用 --demo")
        return 2

    files = scan_evidence_files(dirs)
    if not files:
        print("ERROR: 目录下无 JSON 文件: %s" % dirs)
        return 2

    print("批量预审: 扫描 %d 个 JSON 文件 (%s)" % (len(files), ", ".join(dirs)))
    print("-" * 70)

    results = []
    for f in files:
        r = audit_one(f, EvidenceAuditor)
        results.append(r)
        if r["status"] == "SKIPPED":
            print("  %-46s SKIP  %s" % (r["file"], r["reason"]))
        else:
            s = r["events_summary"]
            print("  %-46s %-16s CRIT=%d HIGH=%d"
                  % (r["file"], r["status"], s["CRITICAL"], s["HIGH"]))

    summary = summarize(results)
    print("-" * 70)
    print("汇总: 审计 %d / 跳过 %d  |  PASS=%d CONDITIONAL=%d FAIL=%d"
          % (summary["audited"], summary["skipped"],
             summary["by_verdict"].get(PASS, 0),
             summary["by_verdict"].get(CONDITIONAL_PASS, 0),
             summary["by_verdict"].get(FAIL, 0)))
    print("等级: CRITICAL=%d HIGH=%d MEDIUM=%d LOW=%d  |  总判定: %s"
          % (summary["by_level"]["CRITICAL"], summary["by_level"]["HIGH"],
             summary["by_level"]["MEDIUM"], summary["by_level"]["LOW"],
             summary["overall_verdict"]))

    if summary["by_owner"]:
        print("路由:")
        for owner in sorted(summary["by_owner"]):
            print("  -> %s: %d 告警 (%s)"
                  % (owner, summary["by_owner"][owner]["total"],
                     ", ".join(sorted(summary["by_owner"][owner]["rules"]))))

    md = render_markdown(summary, results)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
        print("Markdown 报告: %s" % args.md)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "results": results}, f,
                      ensure_ascii=False, indent=2)
        print("JSON 报告: %s" % args.json_out)

    return 1 if summary["by_level"]["CRITICAL"] else 0


def self_test(EvidenceAuditor, build_case_library):
    """自检: 批量调度 + 汇总逻辑正确性"""
    failures = []
    demo_dir = run_demo(EvidenceAuditor, build_case_library)
    files = scan_evidence_files([demo_dir])

    # 1. 全部用例被识别为证据包
    if len(files) != len(build_case_library()):
        failures.append("扫描文件数 %d != 用例数 %d"
                        % (len(files), len(build_case_library())))

    results = [audit_one(f, EvidenceAuditor) for f in files]
    if any(r["status"] == "SKIPPED" for r in results):
        failures.append("有用例被误判为 SKIP: %s"
                        % [r["file"] for r in results
                           if r["status"] == "SKIPPED"])

    summary = summarize(results)

    # 2. 汇总计数一致
    if summary["audited"] + summary["skipped"] != summary["total_files_scanned"]:
        failures.append("汇总计数不一致")
    total_by_verdict = sum(summary["by_verdict"].values())
    if total_by_verdict != summary["audited"]:
        failures.append("by_verdict 合计 %d != audited %d"
                        % (total_by_verdict, summary["audited"]))

    # 3. 等级汇总 = 各包之和
    for lvl in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        manual = sum(r["events_summary"].get(lvl, 0) for r in results)
        if summary["by_level"][lvl] != manual:
            failures.append("%s 汇总 %d != 手动统计 %d"
                            % (lvl, summary["by_level"][lvl], manual))

    # 4. 路由责任方覆盖
    for rule in summary["by_rule"]:
        if rule not in RULE_OWNER:
            failures.append("规则无路由映射: %s" % rule)

    # 5. 判定与最差等级一致
    if summary["by_level"]["CRITICAL"] and summary["overall_verdict"] != "BLOCKED":
        failures.append("有 CRITICAL 但总判定非 BLOCKED")
    if not summary["by_level"]["CRITICAL"] and not summary["by_level"]["HIGH"] \
            and summary["overall_verdict"] not in ("PASS", "CONDITIONAL"):
        failures.append("无 CRITICAL/HIGH 但总判定异常: %s"
                        % summary["overall_verdict"])

    # 6. Markdown 渲染含关键段落
    md = render_markdown(summary, results)
    for sec in ("## 1. 总体结论", "## 3. 按风险等级分组",
                "## 5. 告警责任方路由", "## 6. 逐包明细", "## 7. CRITICAL 告警清单"):
        if sec not in md:
            failures.append("Markdown 缺段落: %s" % sec)

    # 7. 清理
    for f in files:
        os.remove(f)
    os.rmdir(demo_dir)

    print("batch_evidence_audit_runner 自检")
    print("  用例包数: %d" % len(files))
    print("  判定分布: PASS=%d CONDITIONAL=%d FAIL=%d"
          % (summary["by_verdict"].get(PASS, 0),
             summary["by_verdict"].get(CONDITIONAL_PASS, 0),
             summary["by_verdict"].get(FAIL, 0)))
    print("  等级分布: CRIT=%d HIGH=%d MED=%d LOW=%d"
          % (summary["by_level"]["CRITICAL"], summary["by_level"]["HIGH"],
             summary["by_level"]["MEDIUM"], summary["by_level"]["LOW"]))
    print("  责任方路由: %s"
          % ", ".join("%s(%d)" % (k, v["total"])
                      for k, v in sorted(summary["by_owner"].items())))
    print("  总判定: %s" % summary["overall_verdict"])
    print("-" * 50)
    if failures:
        for f in failures:
            print("  ❌ %s" % f)
        print("  结论: SELF-TEST FAILED")
        return 1
    print("  ✅ 7 项自检全部通过")
    print("  结论: SELF-TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
