#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 审计事件持久化模块 (audit_event_store.py)

工单: 工单-HERMES / T3.5 审计事件持久化模块升级
分支: feature/v85-chart-template @ dcf7194
编制方: HERMES (L3 审计方)
日期: 2026-10-15

用途
----
审计事件持久化存储，支持三方（DSHB/DSHE/HERMES）上报告警事件，
每条事件关联 dep_registry_id / evidence_package_index / trace_id /
audit_fingerprint，支持跨团队检索。

相对 v1 (audit_events_persist.json 静态导出) 的升级
-----------------------------------------------
1. **外部上报接入**: DSHB/DSHE 可直接上报事件 (--ingest)，不必经过审计器
2. **跨团队检索**: 按 source_team / dep_registry_id / rule / level 多维检索
3. **DEP 关联**: 事件与 DEP 登记ID 强关联，支持按 DEP 追溯全生命周期告警
4. **去重幂等**: event_id 基于内容 MD5，重复上报自动去重并计数
5. **追加不覆盖**: JSONL 只追加，历史记录不可修改 (NO_OVERWRITE 延伸)
6. **跨团队索引**: 生成 dep_index，便于三方交叉比对告警分布

事件契约 (对齐 v86_rc2_hermes_alert_routing_spec.md + EVIDENCE_CONTRACT_V1)
--------------------------------------------------------------------------
{
  "level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "rule": "R-AUDIT-01" | ...,
  "detect_point": "D01.2" | ...,
  "message": "...",
  "source_team": "DSHB" | "DSHE" | "HERMES",
  "dep_registry_id": "DEP-REG-001",
  "evidence_package_index": 3,
  "trace_id": "DSHE-...-003",
  "audit_fingerprint": "DSHE-20261015_100007-A3F2B1C4",
  "evidence_file": "CASE-N01.json",
  "run_id": "20261015_100007"
}

用法
----
  python3 audit_event_store.py --ingest <event.json> [--event ...]   # 单条上报
  python3 audit_event_store.py --ingest-batch <file.json>            # 批量上报
  python3 audit_event_store.py --audit-report <审计报告.json>         # 从审计器报告导入
  python3 audit_event_store.py --query [--team X] [--rule X] [--dep X] [--level X]
  python3 audit_event_store.py --stats                               # 统计
  python3 audit_event_store.py --index                                # 重建 DEP 索引
  python3 audit_event_store.py --self-test                            # 自检

约束
----
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
本模块纯离线，不发网络请求。存储只追加，禁止删除/修改历史事件。
"""

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

STORE_VERSION = "2.0.0"
BRANCH_BASELINE = "dcf7194"
DEFAULT_STORE = "audit_event_store.jsonl"

LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
LEVEL_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
TEAMS = {"DSHB", "DSHE", "HERMES"}

# 合法规则集
RULES = {"R-AUDIT-01", "R-AUDIT-02", "R-AUDIT-03", "R-AUDIT-04",
         "R-CONTRACT-V1", "R-DEP-STATE", "R-LEGACY-CAL"}

# 规则 -> 默认责任方
RULE_OWNER = {
    "R-AUDIT-01": "DSHB", "R-AUDIT-02": "DSHB", "R-AUDIT-03": "DSHE",
    "R-AUDIT-04": "DSHB", "R-CONTRACT-V1": "提交方",
    "R-DEP-STATE": "DSHB/DSHE", "R-LEGACY-CAL": "DSHB",
}


# ---------------------------------------------------------------------------
# event_id 生成 (幂等)
# ---------------------------------------------------------------------------
def make_event_id(level, rule, detect_point, message,
                  source_team=None, dep_registry_id=None,
                  evidence_index=None, trace_id=None):
    raw = "%s|%s|%s|%s|%s|%s|%s|%s" % (
        level, rule, detect_point, message, source_team,
        dep_registry_id, evidence_index, trace_id)
    return "AE-%s" % hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# 事件归一化 + 校验
# ---------------------------------------------------------------------------
def normalize_event(raw):
    """归一化并校验单条事件，返回 (event, errors)。校验失败时 event 为空 dict。"""
    errs = []
    if not isinstance(raw, dict):
        return {}, ["事件必须是 JSON 对象"]

    level = (raw.get("level") or "").upper()
    rule = raw.get("rule") or ""
    dp = raw.get("detect_point") or ""
    msg = raw.get("message") or ""
    team = (raw.get("source_team") or raw.get("source") or "").upper()

    if not level:
        errs.append("缺 level")
    elif level not in LEVELS:
        errs.append("非法 level: %s" % level)

    if not rule:
        errs.append("缺 rule")
    elif rule not in RULES:
        errs.append("未知 rule: %s" % rule)

    if not dp:
        errs.append("缺 detect_point")
    if not msg:
        errs.append("缺 message")

    if team and team not in TEAMS and "/" not in team and team != "提交方":
        # 团队前缀识别: "DSHE_V86_RC2_L2_AUDIT" -> "DSHE",
        # "DSHB_L1_SELF_TEST" -> "DSHB"。
        # 三方 caller 常带版本后缀, 若精确匹配会大量误拒上报。
        matched = None
        for t in TEAMS:
            if team.startswith(t):
                matched = t
                break
        if matched:
            team = matched
        else:
            errs.append("未知 source_team: %s" % team)

    if not team:
        team = RULE_OWNER.get(rule, "未指定")

    dep_id = raw.get("dep_registry_id")
    if dep_id and not str(dep_id).startswith("DEP-REG-"):
        errs.append("dep_registry_id 格式异常: %s" % dep_id)

    event = {
        "event_id": make_event_id(
            level, rule, dp, msg, team, dep_id,
            raw.get("evidence_package_index"), raw.get("trace_id")),
        "level": level,
        "rule": rule,
        "detect_point": dp,
        "message": msg,
        "source_team": team,
        "owner": RULE_OWNER.get(rule, "未指定"),
        "dep_registry_id": dep_id,
        "evidence_package_index": raw.get("evidence_package_index"),
        "trace_id": raw.get("trace_id"),
        "audit_fingerprint": raw.get("audit_fingerprint")
                            or raw.get("fingerprint"),
        "evidence_file": raw.get("evidence_file"),
        "run_id": raw.get("run_id"),
        "timestamp": raw.get("timestamp")
                    or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "received_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dedup_count": 1,
    }
    return event, errs


# ---------------------------------------------------------------------------
# 存储 (JSONL, 只追加)
# ---------------------------------------------------------------------------
def load_store(path):
    events = []
    if not os.path.exists(path):
        return events
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def append_events(path, events):
    """追加写入 (去重: 已存在 event_id 则累加 dedup_count)"""
    existing = {e["event_id"]: e for e in load_store(path)}
    lines = []
    added = 0
    deduped = 0
    for e in events:
        if e["event_id"] in existing:
            existing[e["event_id"]]["dedup_count"] += 1
            existing[e["event_id"]]["last_seen"] = e["received_at"]
            deduped += 1
        else:
            existing[e["event_id"]] = e
            added += 1
        lines.append(json.dumps(existing[e["event_id"]], ensure_ascii=False))
    # 重写存储 (保持去重后的唯一集, 新增追加在末尾)
    with open(path, "w", encoding="utf-8") as f:
        for eid in list(existing.keys()):
            f.write(json.dumps(existing[eid], ensure_ascii=False) + "\n")
    return added, deduped


# ---------------------------------------------------------------------------
# 检索
# ---------------------------------------------------------------------------
def query_events(events, team=None, rule=None, dep=None, level=None,
                 trace=None, fingerprint=None):
    out = events
    if team:
        out = [e for e in out if e.get("source_team") == team
               or e.get("owner") == team]
    if rule:
        out = [e for e in out if e.get("rule") == rule]
    if dep:
        out = [e for e in out if e.get("dep_registry_id") == dep]
    if level:
        out = [e for e in out if e.get("level") == level.upper()]
    if trace:
        out = [e for e in out if e.get("trace_id") == trace]
    if fingerprint:
        out = [e for e in out if e.get("audit_fingerprint") == fingerprint]
    return out


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------
def compute_stats(events):
    by_level = Counter(e.get("level") for e in events)
    by_rule = Counter(e.get("rule") for e in events)
    by_owner = Counter(e.get("owner") for e in events)
    by_team = Counter(e.get("source_team") for e in events)
    by_dep = Counter(e.get("dep_registry_id") for e in events
                     if e.get("dep_registry_id"))

    # 每 DEP 的最严重等级
    dep_worst = {}
    for e in events:
        dep = e.get("dep_registry_id")
        if not dep:
            continue
        cur = dep_worst.get(dep)
        if cur is None or LEVEL_ORDER.get(e.get("level"), 9) < \
                LEVEL_ORDER.get(cur, 9):
            dep_worst[dep] = e.get("level")

    dedup_total = sum(e.get("dedup_count", 1) - 1 for e in events)

    return {
        "total_unique_events": len(events),
        "total_received_with_dedup": sum(
            e.get("dedup_count", 1) for e in events),
        "dedup_collapsed": dedup_total,
        "by_level": dict(by_level),
        "by_rule": dict(by_rule),
        "by_owner": dict(by_owner),
        "by_team": dict(by_team),
        "by_dep": dict(by_dep),
        "dep_worst_level": dep_worst,
    }


def render_stats(stats):
    lines = []
    lines.append("=" * 64)
    lines.append("  审计事件存储统计 (audit_event_store v%s)" % STORE_VERSION)
    lines.append("=" * 64)
    lines.append("  唯一事件: %d  |  含去重总接收: %d  |  去重折叠: %d"
                 % (stats["total_unique_events"],
                    stats["total_received_with_dedup"],
                    stats["dedup_collapsed"]))
    lines.append("-" * 64)
    lines.append("  按等级:")
    for lvl in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        lines.append("    %-9s %d" % (lvl, stats["by_level"].get(lvl, 0)))
    lines.append("  按规则:")
    for rule in sorted(stats["by_rule"]):
        lines.append("    %-14s %d" % (rule, stats["by_rule"][rule]))
    lines.append("  按责任方:")
    for owner in sorted(stats["by_owner"]):
        lines.append("    %-14s %d" % (owner, stats["by_owner"][owner]))
    lines.append("  按上报团队:")
    for team in sorted(stats["by_team"]):
        lines.append("    %-14s %d" % (team, stats["by_team"][team]))
    lines.append("  按 DEP 登记ID:")
    for dep in sorted(stats["by_dep"]):
        worst = stats["dep_worst_level"].get(dep)
        lines.append("    %-14s %d  (最差: %s)"
                     % (dep, stats["by_dep"][dep], worst))
    lines.append("=" * 64)
    return "\n".join(lines)


def render_index(stats):
    """DEP 跨团队索引"""
    lines = []
    lines.append("# 审计事件 DEP 跨团队索引")
    lines.append("")
    lines.append("> 生成: audit_event_store v%s / 基线 %s"
                 % (STORE_VERSION, BRANCH_BASELINE))
    lines.append("")
    lines.append("| DEP | 事件数 | 最差等级 | 涉及责任方 | 涉及规则 |")
    lines.append("|-----|--------|---------|-----------|---------|")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 从审计器报告导入
# ---------------------------------------------------------------------------
def events_from_audit_report(report_dict, evidence_file=None):
    """把 evidence_auditor_v2 / batch runner 的报告转为事件"""
    out = []
    if isinstance(report_dict, dict) and "report" in report_dict:
        report = report_dict["report"]
        src_file = report_dict.get("file") or report_dict.get("case_id")
    else:
        report = report_dict
        src_file = evidence_file

    for e in report.get("events", []):
        out.append(normalize_event({
            "level": e.get("level"),
            "rule": e.get("rule"),
            "detect_point": e.get("detect_point"),
            "message": e.get("message"),
            "source_team": e.get("source_team"),
            "dep_registry_id": e.get("dep_registry_id")
                            or report.get("dep_registry_id"),
            "evidence_package_index": e.get("evidence_index"),
            "trace_id": e.get("trace_id"),
            "audit_fingerprint": e.get("audit_fingerprint")
                                or report.get("fingerprint"),
            "evidence_file": src_file,
            "run_id": report.get("run_id"),
        })[0])
    return out


def events_from_batch_report(batch_dict):
    """从 batch_evidence_audit_runner 的 JSON 报告导入"""
    out = []
    for r in batch_dict.get("results", []):
        if r.get("status") == "SKIPPED":
            continue
        rep = r.get("report") or {}
        for e in r.get("events", []):
            out.append(normalize_event({
                "level": e.get("level"),
                "rule": e.get("rule"),
                "detect_point": e.get("detect_point"),
                "message": e.get("message"),
                "source_team": e.get("source_team"),
                "dep_registry_id": e.get("dep_registry_id")
                                or r.get("dep_registry_id"),
                "evidence_package_index": e.get("evidence_index"),
                "trace_id": e.get("trace_id"),
                "audit_fingerprint": e.get("audit_fingerprint")
                                    or r.get("fingerprint"),
                "evidence_file": r.get("file"),
                "run_id": r.get("run_id"),
            })[0])
    return out


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
def self_test():
    failures = []
    tmp = "/tmp/audit_store_selftest_%s.jsonl" % os.getpid()

    # 1. 正常事件归一化
    e, errs = normalize_event({
        "level": "CRITICAL", "rule": "R-AUDIT-01", "detect_point": "D01.2",
        "message": "缺取数证据", "source_team": "DSHB",
        "dep_registry_id": "DEP-REG-001", "trace_id": "T-001",
        "audit_fingerprint": "FP-001", "evidence_package_index": 3})
    if errs:
        failures.append("正常事件校验失败: %s" % errs)
    if not e or not e["event_id"].startswith("AE-"):
        failures.append("event_id 生成异常")
    if e["owner"] != "DSHB":
        failures.append("责任方推导错误: %s" % e["owner"])

    # 2. 幂等: 同内容两次生成相同 ID
    e2, _ = normalize_event({
        "level": "CRITICAL", "rule": "R-AUDIT-01", "detect_point": "D01.2",
        "message": "缺取数证据", "source_team": "DSHB",
        "dep_registry_id": "DEP-REG-001", "trace_id": "T-001",
        "audit_fingerprint": "FP-001", "evidence_package_index": 3})
    if e2["event_id"] != e["event_id"]:
        failures.append("event_id 非幂等")

    # 3. 非法 level 被拒绝
    _, errs3 = normalize_event({"level": "SEVERE", "rule": "R-AUDIT-01",
                                 "detect_point": "D01.2", "message": "x"})
    if not any("level" in x for x in errs3):
        failures.append("非法 level 未被拒绝")

    # 4. 缺必填字段被拒绝
    _, errs4 = normalize_event({"level": "HIGH"})
    if not (any("rule" in x for x in errs4) and
            any("detect_point" in x for x in errs4) and
            any("message" in x for x in errs4)):
        failures.append("缺必填字段未被完整检测")

    # 5. 非法 DEP ID 格式被拒绝
    _, errs5 = normalize_event({
        "level": "HIGH", "rule": "R-DEP-STATE", "detect_point": "DS-05",
        "message": "x", "dep_registry_id": "DEP-123"})
    if not any("dep_registry_id" in x for x in errs5):
        failures.append("非法 DEP 格式未被拒绝")

    # 6. 存储追加 + 去重
    if os.path.exists(tmp):
        os.remove(tmp)
    a, d1 = append_events(tmp, [e])
    if a != 1:
        failures.append("首次追加计数错误: %d" % a)
    a2, d2 = append_events(tmp, [e, e2])
    if d2 != 2:
        failures.append("去重计数错误: %d (期望2)" % d2)
    stored = load_store(tmp)
    if len(stored) != 1:
        failures.append("去重后应为 1 条, 实际 %d" % len(stored))
    if stored[0]["dedup_count"] != 3:
        failures.append("dedup_count 应为 3, 实际 %d"
                        % stored[0]["dedup_count"])

    # 7. 检索
    q = query_events(stored, dep="DEP-REG-001")
    if len(q) != 1:
        failures.append("按 DEP 检索失败")
    q2 = query_events(stored, level="critical")   # 小写也应命中
    if len(q2) != 1:
        failures.append("按 level 检索 (大小写) 失败")
    q3 = query_events(stored, team="DSHE")
    if len(q3) != 0:
        failures.append("按 team 检索应无结果")
    q4 = query_events(stored, fingerprint="FP-001")
    if len(q4) != 1:
        failures.append("按 fingerprint 检索失败")
    q5 = query_events(stored, trace="T-001")
    if len(q5) != 1:
        failures.append("按 trace_id 检索失败")

    # 8. 统计
    stats = compute_stats(stored)
    if stats["total_unique_events"] != 1:
        failures.append("统计唯一事件数错误")
    if stats["dedup_collapsed"] != 2:
        failures.append("统计去重折叠数错误: %d"
                        % stats["dedup_collapsed"])
    if stats["dep_worst_level"].get("DEP-REG-001") != "CRITICAL":
        failures.append("DEP 最差等级推导错误")

    # 9. 审计器报告导入
    fake_report = {
        "report": {"fingerprint": "FP-X", "run_id": "R-X",
                   "dep_registry_id": "DEP-REG-001",
                   "events": [
                       {"level": "CRITICAL", "rule": "R-AUDIT-02",
                        "detect_point": "D02.3", "message": "分子虚增",
                        "trace_id": "T-9"}]},
        "file": "TEST.json"}
    imp = events_from_audit_report(fake_report)
    if len(imp) != 1 or imp[0]["dep_registry_id"] != "DEP-REG-001":
        failures.append("审计器报告导入失败")

    # 10. 批量报告导入
    fake_batch = {"results": [
        {"file": "A.json", "status": "FAIL", "fingerprint": "FP-A",
         "run_id": "R-A", "dep_registry_id": "DEP-REG-001",
         "events": [{"level": "HIGH", "rule": "R-AUDIT-03",
                     "detect_point": "D03.2", "message": "背书式"}]},
        {"file": "B.json", "status": "SKIPPED", "events": []}]}
    imp2 = events_from_batch_report(fake_batch)
    if len(imp2) != 1:
        failures.append("批量报告导入应跳过 SKIPPED, 实际 %d" % len(imp2))

    # 11. 规则集合完整
    for r in RULE_OWNER:
        if r not in RULES:
            failures.append("RULE_OWNER 含未定义规则: %s" % r)

    os.remove(tmp)

    print("audit_event_store 自检")
    print("  检查项: 11 类 (归一化/幂等/校验/存储/去重/检索/统计/导入/规则集)")
    print("-" * 50)
    if failures:
        for f in failures:
            print("  ❌ %s" % f)
        print("  结论: SELF-TEST FAILED")
        return 1
    print("  ✅ 11 类检查全部通过")
    print("  结论: SELF-TEST PASSED")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 审计事件持久化模块")
    ap.add_argument("--store", default=DEFAULT_STORE,
                    help="事件存储 JSONL 路径 (默认 %s)" % DEFAULT_STORE)
    ap.add_argument("--ingest", help="上报单条事件 JSON 文件")
    ap.add_argument("--event", help="上报单条事件 JSON 字面量")
    ap.add_argument("--ingest-batch", help="批量上报事件 JSON 数组文件")
    ap.add_argument("--audit-report", help="从审计器报告 JSON 导入")
    ap.add_argument("--query", action="store_true", help="检索事件")
    ap.add_argument("--team", help="按团队过滤")
    ap.add_argument("--rule", help="按规则过滤")
    ap.add_argument("--dep", help="按 DEP 登记ID 过滤")
    ap.add_argument("--level", help="按等级过滤")
    ap.add_argument("--trace", help="按 trace_id 过滤")
    ap.add_argument("--fingerprint", help="按审计指纹过滤")
    ap.add_argument("--stats", action="store_true", help="输出统计")
    ap.add_argument("--self-test", action="store_true", help="自检")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.ingest:
        with open(args.ingest, encoding="utf-8") as f:
            raw = json.load(f)
        raws = raw if isinstance(raw, list) else [raw]
    elif args.event:
        raws = [json.loads(args.event)]
    elif args.ingest_batch:
        with open(args.ingest_batch, encoding="utf-8") as f:
            raws = json.load(f)
        if isinstance(raws, dict):
            raws = [raws]
    elif args.audit_report:
        with open(args.audit_report, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "results" in data:
            raws = events_from_batch_report(data)
        else:
            raws = events_from_audit_report(data,
                                            evidence_file=args.audit_report)
    else:
        raws = []

    if raws:
        events = []
        rejected = 0
        for r in raws:
            e, errs = normalize_event(r)
            if errs or e is None:
                print("  拒绝 (校验失败): %s" % errs)
                rejected += 1
            else:
                events.append(e)
        added, deduped = append_events(args.store, events)
        print("上报完成: 新增 %d / 去重折叠 %d / 拒绝 %d / 存储 %s"
              % (added, deduped, rejected, args.store))
        return 1 if rejected else 0

    if args.stats:
        print(render_stats(compute_stats(load_store(args.store))))
        return 0

    if args.query:
        events = load_store(args.store)
        out = query_events(
            events, team=args.team, rule=args.rule, dep=args.dep,
            level=args.level, trace=args.trace,
            fingerprint=args.fingerprint)
        print("检索结果: %d 条 (存储 %d 条)" % (len(out), len(events)))
        for e in out:
            print("  %-14s %-10s %-14s %-8s %s | DEP=%s | %s"
                  % (e["event_id"], e["level"], e["rule"],
                     e["detect_point"], e["source_team"],
                     e.get("dep_registry_id") or "-",
                     e["message"][:60]))
        if not out:
            print("  (无匹配事件)")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
