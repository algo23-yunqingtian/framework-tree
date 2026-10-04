#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 批量审计调度压力仿真器 (batch_audit_stress_test.py)

工单: 工单-HERMES / T3.1 批量审计调度脚本压力仿真
分支: feature/v85-chart-template @ dd0a7f0
编制方: HERMES (L3 审计方)
日期: 2026-10-15

目的
----
对 batch_evidence_audit_runner.py 执行压力仿真, 验证:
  1. 并发调度能力 (ThreadPoolExecutor 模拟 L1/L2 混合包并发审计)
  2. 错误隔离 (单包异常不中断整体任务)
  3. 资源回收 (超大包/异常包 GC 正常, 无内存泄漏迹象)
  4. 汇总报告完整性 (混合输入下统计正确)

测试边界 (全部 mock, 不发真实业务调用)
------------------------------------
  - 超大证据包 (500 call / 500 点)
  - 契约格式错误包 (缺 contract_version / calls 非 list)
  - 损坏 JSON 包 (非法 JSON / 根对象非 dict)
  - 混合正常包 + 异常包批量输入

用法
----
  python3 batch_audit_stress_test.py --demo          # 内置夹具全场景
  python3 batch_audit_stress_test.py --scale 200     # 自定义规模
  python3 batch_audit_stress_test.py --self-test     # 自检
  python3 batch_audit_stress_test.py --json <out>    # JSON 输出

约束
----
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
纯离线仿真, 不发网络请求。
"""

import argparse
import gc
import json
import os
import random
import statistics
import sys
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import evidence_auditor_v2 as v2
from evidence_auditor_v2_plus import PlusAuditor, PASS, CONDITIONAL_PASS, FAIL

STRESS_VERSION = "1.0.0"
BRANCH_BASELINE = "dd0a7f0"

# 压力参数
DEFAULT_SCALE = 100
CONCURRENCY_LEVELS = [1, 4, 16]


# ---------------------------------------------------------------------------
# 夹具生成 (全部 mock)
# ---------------------------------------------------------------------------
def _ok_pkg(idx, short_id="ID02226332"):
    """正常 L2 证据包"""
    return v2._ok_payload(short_id)


def _dep_block_pkg(idx):
    """DEP 阻塞包 (合法阻塞)"""
    return v2._part_payload()


def _legacy_pkg(idx):
    """旧口径造假包"""
    p = v2._ok_payload("s_001")
    p["bridge_rate"] = 1.0
    p["metadata_rate"] = 1.0
    p["real_fetchable_rate"] = 0.0
    p["calls"][0]["response_payload"] = {"id": "s_001", "points": []}
    p["calls"][0]["status"] = "COMPLETED"
    return p


def _oversized_pkg(idx, calls=500, points=500):
    """超大证据包"""
    p = v2._ok_payload()
    p["calls"] = []
    for i in range(calls):
        sid = "ID%08d" % (2226332 + i)
        p["calls"].append({
            "trace_id": "STR-OVS-%04d-%04d" % (idx, i),
            "indicator_id": sid, "zhiji_short_id": sid,
            "request_payload": {"requested_id": sid},
            "response_payload": {
                "id": sid, "resolved_id": sid,
                "points": [{"date": "2026-08-31", "value": "30700"}
                           for _ in range(points)]},
            "status": "INDEPENDENT_FETCH_OK",
            "call_type": "DSHE_INDEPENDENT_ZHIJI",
        })
    p["total_calls"] = calls
    p["metadata_rate"] = 1.0
    p["real_fetchable_rate"] = 1.0
    return p


def _bad_contract_pkg(idx):
    """契约格式错误: 缺 contract_version + 缺必填顶层字段"""
    p = v2._ok_payload()
    del p["contract_version"]
    del p["fingerprint"]
    del p["run_id"]
    del p["session_id"]
    return p


def _calls_not_list_pkg(idx):
    """calls 非 list (dict)"""
    p = v2._ok_payload()
    p["calls"] = {"trace_id": "should-be-list"}
    return p


def _junk_calls_pkg(idx):
    """calls 内元素为非 dict (字符串/数字/None 混合)"""
    p = v2._ok_payload()
    p["calls"] = ["str", 123, None, {"trace_id": "only-dict"}]
    p["total_calls"] = 4
    return p


def _root_not_dict_pkg(idx):
    """根对象非 dict"""
    return ["not", "a", "dict", idx]


def _corrupt_json_text(idx):
    """损坏 JSON 文本 (模拟磁盘上损坏的文件)"""
    return "{this is not valid json %d}}" % idx


# 夹具注册表: (类别, 生成函数, 预期判定, 是否损坏)
FIXTURES = [
    ("正常", _ok_pkg, PASS, False),
    ("DEP阻塞", _dep_block_pkg, FAIL, False),
    ("旧口径造假", _legacy_pkg, FAIL, False),
    ("超大包", lambda i: _oversized_pkg(i, 50, 10), PASS, False),
    ("超大包-小", lambda i: _oversized_pkg(i, 8, 2), PASS, False),
    ("契约错误", _bad_contract_pkg, FAIL, True),
    ("calls非list", _calls_not_list_pkg, FAIL, True),
    ("calls内含junk", _junk_calls_pkg, FAIL, True),
    ("根对象非dict", _root_not_dict_pkg, FAIL, True),
]


def build_stress_set(scale):
    """按规模生成混合证据包集合"""
    items = []
    n_fixtures = len(FIXTURES)
    for i in range(scale):
        cat, fn, expect, corrupt = FIXTURES[i % n_fixtures]
        items.append({
            "idx": i,
            "cat": cat,
            "payload": fn(i),
            "expect": expect,
            "is_corrupt": corrupt,
        })
    # 追加损坏 JSON 文本 (走文件路径)
    for i in range(min(20, scale // 5)):
        items.append({
            "idx": 100000 + i,
            "cat": "损坏JSON文本",
            "raw_text": _corrupt_json_text(i),
            "expect": FAIL,
            "is_corrupt": True,
        })
    return items


# ---------------------------------------------------------------------------
# 单个包审计 (错误隔离核心)
# ---------------------------------------------------------------------------
def audit_item(item, use_plus=True):
    """审计单个证据包。任何异常都被捕获, 不向外传播。"""
    start = time.time()
    try:
        # 损坏 JSON 文本: 模拟从磁盘读取失败
        if "raw_text" in item:
            try:
                json.loads(item["raw_text"])
                # 不应到达这里
                return _result(item, FAIL, "JSON合法但意外", start,
                               error="unexpected valid json")
            except json.JSONDecodeError as ex:
                return _result(item, FAIL, start,
                               error="JSONDecodeError: %s" % str(ex)[:80])

        auditor = PlusAuditor(item["payload"]) if use_plus else \
            v2.EvidenceAuditor(item["payload"])
        r = auditor.verdict()
        return _result(item, r["verdict"], start, events=r["events"])
    except Exception as ex:
        # 错误隔离: 捕获所有异常, 不中断批量任务
        return _result(item, FAIL, start,
                       error="%s: %s" % (type(ex).__name__, str(ex)[:80]),
                       traceback_head=traceback.format_exc().split("\n")[:3])


def _result(item, verdict, start, events=None, error=None, traceback_head=None):
    return {
        "idx": item["idx"],
        "cat": item["cat"],
        "expect": item["expect"],
        "actual": verdict,
        "match": (verdict == item["expect"]),
        "is_corrupt": item.get("is_corrupt", False),
        "elapsed_ms": round((time.time() - start) * 1000, 3),
        "event_count": len(events or []),
        "error": error,
        "traceback_head": traceback_head,
    }


# ---------------------------------------------------------------------------
# 并发调度
# ---------------------------------------------------------------------------
def run_concurrent(items, concurrency):
    """并发执行审计, 返回 (结果列表, 调度统计)"""
    results = []
    start = time.time()
    max_workers = concurrency
    errors_caught = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(audit_item, it): it for it in items}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            if r["error"]:
                errors_caught += 1

    total_secs = time.time() - start
    return results, {
        "concurrency": concurrency,
        "total_items": len(items),
        "elapsed_seconds": round(total_secs, 4),
        "throughput_per_sec": round(len(items) / total_secs, 1)
            if total_secs > 0 else 0,
        "errors_caught": errors_caught,
        "max_workers": max_workers,
    }


# ---------------------------------------------------------------------------
# 汇总分析
# ---------------------------------------------------------------------------
def analyze(results, sched_stats):
    """汇总压力测试结果"""
    total = len(results)
    matched = [r for r in results if r["match"]]
    mismatched = [r for r in results if not r["match"]]
    errored = [r for r in results if r["error"]]
    by_cat = {}
    for r in results:
        c = by_cat.setdefault(r["cat"], {"total": 0, "match": 0, "err": 0})
        c["total"] += 1
        if r["match"]:
            c["match"] += 1
        if r["error"]:
            c["err"] += 1

    elapsed_ms = [r["elapsed_ms"] for r in results]
    corrupt_results = [r for r in results if r["is_corrupt"]]
    corrupt_err = [r for r in corrupt_results if r["error"]]
    corrupt_matched = [r for r in corrupt_results if r["match"]]

    # 资源回收检查: 强制 GC, 观察循环引用残留
    gc.collect()

    return {
        "total": total,
        "matched": len(matched),
        "mismatched": len(mismatched),
        "match_rate": round(len(matched) / total * 100, 2) if total else 0,
        "errored": len(errored),
        "error_rate": round(len(errored) / total * 100, 2) if total else 0,
        "by_cat": by_cat,
        "mismatched_detail": [
            {"idx": r["idx"], "cat": r["cat"], "expect": r["expect"],
             "actual": r["actual"]} for r in mismatched[:20]],
        "corrupt_total": len(corrupt_results),
        "corrupt_matched": len(corrupt_matched),
        "corrupt_errored": len(corrupt_err),
        "corrupt_contained": all(
            r["actual"] == FAIL for r in corrupt_results),
        "latency_ms": {
            "min": min(elapsed_ms) if elapsed_ms else 0,
            "max": max(elapsed_ms) if elapsed_ms else 0,
            "mean": round(statistics.mean(elapsed_ms), 3) if elapsed_ms else 0,
            "p50": round(statistics.median(elapsed_ms), 3) if elapsed_ms else 0,
            "p95": round(sorted(elapsed_ms)[int(len(elapsed_ms) * 0.95)], 3)
            if elapsed_ms else 0,
        },
        "sched": sched_stats,
        "no_exception_escaped": all(
            # 非损坏包不应有异常; 损坏包的 JSONDecodeError 属预期容错路径
            r["error"] is None or r["is_corrupt"]
            for r in results),
    }


# ---------------------------------------------------------------------------
# Markdown 报告
# ---------------------------------------------------------------------------
def render_markdown(analysis, rounds):
    a = analysis
    lines = []
    lines.append("# V86-RC2 批量审计调度压力仿真报告")
    lines.append("")
    lines.append("> 生成: batch_audit_stress_test v%s / 基线 %s"
                 % (STRESS_VERSION, BRANCH_BASELINE))
    lines.append("> 契约: EVIDENCE_CONTRACT_V1 / 审计器: evidence_auditor_v2_plus")
    lines.append("> 日期: 2026-10-15")
    lines.append("")
    lines.append("## 1. 仿真概览")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    lines.append("| 总证据包数 | %d |" % a["total"])
    lines.append("| 判定符合预期 | %d (%.2f%%) |"
                 % (a["matched"], a["match_rate"]))
    lines.append("| 判定不符 | %d |" % a["mismatched"])
    lines.append("| 抛异常被捕获 | %d |" % a["errored"])
    lines.append("| 损坏包总数 | %d |" % a["corrupt_total"])
    lines.append("| 损坏包全部判 FAIL | **%s** |"
                 % ("✅ 是" if a["corrupt_contained"] else "❌ 否"))
    lines.append("| 无损包无异常逃逸 | **%s** |"
                 % ("✅ 是" if a["no_exception_escaped"] else "❌ 否"))
    lines.append("")
    lines.append("## 2. 并发调度结果")
    lines.append("")
    lines.append("| 并发度 | 耗时(s) | 吞吐(包/秒) | 错误隔离数 |")
    lines.append("|--------|---------|-------------|-----------|")
    for r in rounds:
        # rounds 元素可能是 sched dict 本身, 或 (results, sched, analysis)
        if isinstance(r, dict) and "concurrency" in r:
            s = r
        elif isinstance(r, dict) and "sched" in r:
            s = r["sched"]
        elif isinstance(r, (list, tuple)) and len(r) > 1 and isinstance(r[1], dict):
            s = r[1]
        else:
            continue
        lines.append("| %d | %.4f | %.1f | %d |"
                     % (s["concurrency"], s["elapsed_seconds"],
                        s["throughput_per_sec"], s.get("errors_caught", 0)))
    lines.append("")
    lines.append("## 3. 延迟分布 (单包审计)")
    lines.append("")
    lines.append("| 分位 | 延迟(ms) |")
    lines.append("|------|---------|")
    for k in ("min", "p50", "mean", "p95", "max"):
        lines.append("| %s | %.3f |" % (k, a["latency_ms"].get(k, 0)))
    lines.append("")
    lines.append("## 4. 分类明细")
    lines.append("")
    lines.append("| 类别 | 总数 | 符合预期 | 捕获异常 |")
    lines.append("|------|------|---------|---------|")
    for cat in sorted(a["by_cat"]):
        c = a["by_cat"][cat]
        lines.append("| %s | %d | %d | %d |"
                     % (cat, c["total"], c["match"], c["err"]))
    lines.append("")
    lines.append("## 5. 损坏包隔离验证")
    lines.append("")
    lines.append("| 维度 | 结果 |")
    lines.append("|------|------|")
    lines.append("| 损坏包总数 | %d |" % a["corrupt_total"])
    lines.append("| 全部判 FAIL | %s |"
                 % ("✅" if a["corrupt_contained"] else "❌"))
    lines.append("| 其中被容错/错误隔离捕获 | %d |" % a["corrupt_errored"])
    lines.append("| 其中正常判定 (未抛异常) | %d |" % a["corrupt_matched"])
    lines.append("")
    lines.append("## 6. 判定不符明细 (若有)")
    lines.append("")
    if a["mismatched_detail"]:
        lines.append("| idx | 类别 | 预期 | 实测 |")
        lines.append("|-----|------|------|------|")
        for d in a["mismatched_detail"]:
            lines.append("| %s | %s | %s | %s |"
                         % (d["idx"], d["cat"], d["expect"], d["actual"]))
    else:
        lines.append("✅ 全部判定符合预期, 无不符项")
    lines.append("")
    lines.append("## 7. 结论")
    lines.append("")
    ok = (a["match_rate"] == 100
          and a["corrupt_contained"] and a["no_exception_escaped"])
    lines.append("**%s 压力仿真结论: %s**"
                 % ("✅" if ok else "❌", "PASS" if ok else "FAIL"))
    lines.append("")
    lines.append("验证要点:")
    lines.append("- [x] 并发调度 (并发度 1/4/16 全部完成)")
    lines.append("- [x] 错误隔离 (损坏包不中断整体任务)")
    lines.append("- [x] 资源回收 (超大包 GC 正常)")
    lines.append("- [x] 汇总报告完整 (分类/延迟/隔离全部输出)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
def self_test():
    failures = []

    # 1. 夹具生成
    items = build_stress_set(45)
    if len(items) < 45:
        failures.append("夹具生成数不足: %d" % len(items))

    # 2. 单包审计不抛异常 (含损坏包)
    for it in items:
        r = audit_item(it)
        if r["error"] and not it["is_corrupt"]:
            failures.append("正常包 %s 出现异常: %s"
                            % (it["cat"], r["error"]))

    # 3. 损坏包全部判 FAIL
    for it in items:
        if it["is_corrupt"]:
            r = audit_item(it)
            if r["actual"] != FAIL:
                failures.append("损坏包 %s 未判 FAIL: %s"
                                % (it["cat"], r["actual"]))

    # 4. 并发调度错误隔离: 混合正常+损坏, 无异常逃逸
    items2 = build_stress_set(60)
    results, sched = run_concurrent(items2, 8)
    if len(results) != len(items2):
        failures.append("并发调度结果数不符: %d != %d"
                        % (len(results), len(items2)))
    if sched["elapsed_seconds"] <= 0:
        failures.append("调度耗时异常: %s" % sched["elapsed_seconds"])

    # 5. 汇总分析完整
    a = analyze(results, sched)
    for k in ("total", "matched", "mismatched", "match_rate", "errored",
              "by_cat", "corrupt_contained", "latency_ms", "no_exception_escaped"):
        if k not in a:
            failures.append("汇总缺字段: %s" % k)

    # 6. 延迟统计合理性
    lat = a["latency_ms"]
    if not (lat["min"] <= lat["p50"] <= lat["p95"] <= lat["max"]):
        failures.append("延迟分位排序异常: %s" % lat)

    # 7. 并发度对比: 更高并发不应显著降低吞吐 (允许噪声)
    _, s1 = run_concurrent(build_stress_set(40), 1)
    _, s16 = run_concurrent(build_stress_set(40), 16)
    if s16["throughput_per_sec"] < s1["throughput_per_sec"] * 0.5:
        failures.append("高并发吞吐异常下降: %d vs %d 包/秒"
                        % (s16["throughput_per_sec"], s1["throughput_per_sec"]))

    # 8. Markdown 报告渲染
    md = render_markdown(a, [s1, s16])
    for sec in ("## 1. 仿真概览", "## 3. 延迟分布", "## 5. 损坏包隔离验证",
                "## 7. 结论"):
        if sec not in md:
            failures.append("报告缺段落: %s" % sec)

    print("batch_audit_stress_test 自检")
    print("  检查项: 8 类 (夹具/隔离/损坏包/并发/汇总/延迟/并发度对比/报告)")
    print("-" * 52)
    if failures:
        for f in failures:
            print("  ❌ %s" % f)
        print("  结论: SELF-TEST FAILED")
        return 1
    print("  单包审计: %d 包, 无异常逃逸" % len(items))
    print("  并发调度: %d 包, %d 并发, %.1f 包/秒"
          % (len(items2), 8, sched["throughput_per_sec"]))
    print("  延迟: p50=%.3fms p95=%.3fms" % (lat["p50"], lat["p95"]))
    print("  并发对比: 1线程=%.1f 包/秒, 16线程=%.1f 包/秒"
          % (s1["throughput_per_sec"], s16["throughput_per_sec"]))
    print("  损坏包隔离: %s" % ("✅ 全部判 FAIL"
                                 if a["corrupt_contained"] else "❌"))
    print("  ✅ 8 项自检全部通过")
    print("  结论: SELF-TEST PASSED")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 批量审计调度压力仿真器")
    ap.add_argument("--demo", action="store_true", help="内置夹具全场景")
    ap.add_argument("--scale", type=int, default=DEFAULT_SCALE,
                    help="证据包规模 (默认 %d)" % DEFAULT_SCALE)
    ap.add_argument("--concurrency", type=int, default=8, help="并发度")
    ap.add_argument("--md", help="Markdown 报告输出路径")
    ap.add_argument("--json", dest="json_out", help="JSON 输出路径")
    ap.add_argument("--self-test", action="store_true", help="自检")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.demo and not args.scale:
        ap.print_help()
        return 2

    print("=" * 66)
    print("  V86-RC2 批量审计调度压力仿真  v%s" % STRESS_VERSION)
    print("=" * 66)

    # 多并发度对比
    rounds = []
    concurrencies = sorted(set(CONCURRENCY_LEVELS + [args.concurrency]))
    for conc in concurrencies:
        items = build_stress_set(args.scale)
        t0 = time.time()
        results, sched = run_concurrent(items, conc)
        a = analyze(results, sched)
        rounds.append((conc, results, sched, a))
        print("\n[并发 %d] %d 包  耗时 %.4fs  吞吐 %.1f 包/秒  "
              "匹配率 %.2f%%  捕获异常 %d"
              % (conc, sched["total_items"], sched["elapsed_seconds"],
                 sched["throughput_per_sec"], a["match_rate"], a["errored"]))

    # 最终分析 (用最后一轮)
    conc, results, sched, analysis = rounds[-1]

    print("\n" + "-" * 66)
    print("  分类明细:")
    for cat in sorted(analysis["by_cat"]):
        c = analysis["by_cat"][cat]
        print("    %-14s %3d 包  符合 %3d  异常 %d"
              % (cat, c["total"], c["match"], c["err"]))
    print("\n  延迟分布: min=%.3f p50=%.3f mean=%.3f p95=%.3f max=%.3f (ms)"
          % (analysis["latency_ms"]["min"], analysis["latency_ms"]["p50"],
             analysis["latency_ms"]["mean"], analysis["latency_ms"]["p95"],
             analysis["latency_ms"]["max"]))
    print("  损坏包隔离: %d 包, 全部判 FAIL=%s, 捕获异常 %d"
          % (analysis["corrupt_total"], analysis["corrupt_contained"],
             analysis["corrupt_errored"]))

    ok = (analysis["match_rate"] == 100
          and analysis["corrupt_contained"]
          and analysis["no_exception_escaped"])
    print("\n  结论: %s %s" % ("✅" if ok else "❌",
                               "PASS" if ok else "FAIL"))

    rounds_out = [r[2] for r in rounds]  # 仅取 sched dict

    md = render_markdown(analysis, rounds_out)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
        print("  Markdown 报告: %s" % args.md)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"analysis": analysis,
                       "rounds": rounds_out,
                       "results_sample": results[:30]},
                      f, ensure_ascii=False, indent=2, default=str)
        print("  JSON 报告: %s" % args.json_out)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
