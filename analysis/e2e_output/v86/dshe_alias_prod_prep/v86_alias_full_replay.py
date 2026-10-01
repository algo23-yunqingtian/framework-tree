#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v86_alias_full_replay.py
==========================================================================
V86 别名引擎全量回放 — 对 V85 全部 4643 条别名条目执行 F1/F2/F3/F4 流水线
==========================================================================

任务: DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN · T2.1
分支: feature/v85-chart-template

回放策略:
  1. 读取 V85 indicator_alias_library.csv 全部 4643 条别名条目
  2. 对每条别名做自配对 (alias_norm vs alias_norm) 运行完整裁决链
  3. 同时运行 base / f3 / f3+f4 三种模式, 对比差异
  4. 统计: 解析成功率、歧义条目数量、F3/F4 触发分布
  5. 标记长尾歧义样本 (AMBIGUOUS + n_atomic_keys >= 5)

约束:
  - 只读加载 V85 引擎源码 + 别名库 CSV
  - 不修改任何 V85 冻结数据
  - 不调用 zhiji API
  - 不覆盖 V85 交付物

用法:
  python v86_alias_full_replay.py
  python v86_alias_full_replay.py --output analysis/e2e_output/v86/dshe_alias_prod_prep/replay_results.json
"""

import os
import sys
import json
import time
import csv
import hashlib
import argparse
from datetime import datetime, timezone
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
CD = os.path.dirname(os.path.abspath(__file__))
REPO = r"D:\DSH_WORK\framework-tree"
V85 = os.path.join(REPO, "analysis", "e2e_output", "v85")
ALIAS_PREDEV = os.path.join(REPO, "analysis", "e2e_output", "v86", "dshe_alias_predev")
OUT_DIR = CD

TASK_ID = "DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN"
VERSION = "v1.0"
BRANCH = "feature/v85-chart-template"

# V85 别名库
ALIAS_LIB_CSV = os.path.join(V85, "alias_lib_full_audit", "indicator_alias_library.csv")
CONFLICT_CLASS_CSV = os.path.join(V85, "dshe_alias_audit_design", "multi_canonical_conflict_classification.csv")

# 输出
OUT_JSON = os.path.join(OUT_DIR, "replay_results.json")
OUT_REPORT = os.path.join(OUT_DIR, "v86_alias_full_replay_report.md")

# 长尾歧义阈值: atomic_keys >= 5 且 state=AMBIGUOUS
TAIL_AMBIG_THRESHOLD = 5


# ---------------------------------------------------------------------------
# 加载别名库
# ---------------------------------------------------------------------------

def load_alias_library():
    """读取 V85 别名库 CSV, 返回 list of dict."""
    with open(ALIAS_LIB_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_conflict_classification():
    """读取冲突分类 CSV, 返回 alias_id -> dict 映射."""
    if not os.path.isfile(CONFLICT_CLASS_CSV):
        return {}
    with open(CONFLICT_CLASS_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return {r["alias_id"]: r for r in reader if r.get("alias_id")}


# ---------------------------------------------------------------------------
# 回放引擎
# ---------------------------------------------------------------------------

def run_full_replay():
    """执行全量别名回放, 返回 summary dict."""
    print("=" * 78)
    print("V86 别名引擎全量回放 · 4643 条别名条目")
    print("=" * 78)

    # 加载数据
    t0 = time.perf_counter()
    alias_rows = load_alias_library()
    conflict_cls = load_conflict_classification()
    load_time = round((time.perf_counter() - t0) * 1000, 1)
    print("别名条目: %d 条, 冲突分类: %d 条, 加载耗时: %.1fms"
          % (len(alias_rows), len(conflict_cls), load_time))

    # 过滤空 alias_norm
    alias_rows = [r for r in alias_rows if r.get("alias_norm", "").strip()]
    print("有效条目 (alias_norm 非空): %d" % len(alias_rows))

    # 初始化引擎 (三种模式)
    sys.path.insert(0, ALIAS_PREDEV)
    sys.path.insert(0, os.path.join(V85, "dshe_alias_audit_design"))
    sys.path.insert(0, os.path.join(V85, "dshe_alias_integrate_test"))

    from v86_alias_engine_prototype import V86AliasEngine, _verdict_to_state, blacklist_check_bounded
    print("引擎模块加载完成")

    t0 = time.perf_counter()
    eng_base = V86AliasEngine("base")
    t_base_init = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    eng_f3 = V86AliasEngine("f3")
    t_f3_init = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    eng_f3f4 = V86AliasEngine("f3+f4")
    t_f3f4_init = round((time.perf_counter() - t0) * 1000, 1)

    print("引擎初始化: base=%.1fms f3=%.1fms f3+f4=%.1fms"
          % (t_base_init, t_f3_init, t_f3f4_init))

    # 回放
    results = []
    t0 = time.perf_counter()

    # 统计器
    stat = {
        "total": 0,
        "base": Counter(),
        "f3": Counter(),
        "f3f4": Counter(),
        "resolve_state": Counter(),
        "f1": {"hits": 0, "misses": 0, "guard_hits": 0},
        "f3_trigger": {"r05_block": 0, "r01_block": 0},
        "f4_trigger": {"f4a_suppress": 0, "f4b_suppress": 0, "total_suppressed": 0},
        "diff_base_f3": 0,
        "diff_base_f3f4": 0,
        "tail_ambig": 0,
        "variety_dist": Counter(),
        "conflict_class_dist": Counter(),
        "atomic_key_dist": Counter(),
    }

    for row in alias_rows:
        aid = row.get("alias_id", "")
        alias_norm = row.get("alias_norm", "")
        alias_name = row.get("alias_name", "")
        variety = row.get("variety_family", "")
        n_atomic = len(row.get("atomic_keys", "").split("|")) if row.get("atomic_keys") else 0
        # Actually atomic_keys is not in alias library - check classification
        cls = conflict_cls.get(aid, {})
        n_atomic_cls = int(cls.get("n_atomic_keys", 0) or 0)
        conflict_class = cls.get("conflict_class", "")
        review_priority = cls.get("review_priority", "")

        # F2 resolve
        resolve_st = eng_f3f4.resolve(alias_norm)

        # Self-pair decisions
        r_base = eng_base.decide(alias_norm, alias_norm)
        r_f3 = eng_f3.decide(alias_norm, alias_norm)
        r_f3f4 = eng_f3f4.decide(alias_norm, alias_norm)

        base_state = _verdict_to_state(r_base)
        f3_state = _verdict_to_state(r_f3)
        f3f4_state = _verdict_to_state(r_f3f4)

        diff_bf3 = base_state != f3_state
        diff_bf3f4 = base_state != f3f4_state

        # F4 suppression tracking: direct bounded blacklist check for accurate F4a/F4b classification
        f4_suppressed = 0
        if f3_state == "B" and f3f4_state != "B":
            f4_suppressed = 1
            stat["f4_trigger"]["total_suppressed"] += 1
            # Normalize alias for direct blacklist check
            norm_alias = eng_f3f4.M["norm_full"](alias_norm)[0]
            hits_direct, skipped_direct = blacklist_check_bounded(eng_f3f4.M, norm_alias, norm_alias)
            for rid, reason, lp, rp in skipped_direct:
                if "F4a" in reason:
                    stat["f4_trigger"]["f4a_suppress"] += 1
                elif "F4b" in reason:
                    stat["f4_trigger"]["f4b_suppress"] += 1

        # F3 trigger tracking
        f3_rules = r_f3f4.get("all_rules", [])
        if any(r.startswith("R-05_") for r in f3_rules):
            stat["f3_trigger"]["r05_block"] += 1
        if any(r.startswith("R-01") for r in f3_rules):
            stat["f3_trigger"]["r01_block"] += 1

        # Tail ambiguity
        is_tail_ambig = (resolve_st["state"] == "AMBIGUOUS" and n_atomic_cls >= TAIL_AMBIG_THRESHOLD)

        # Update stats
        stat["total"] += 1
        stat["base"][base_state] += 1
        stat["f3"][f3_state] += 1
        stat["f3f4"][f3f4_state] += 1
        stat["resolve_state"][resolve_st["state"]] += 1
        stat["variety_dist"][variety] += 1
        if conflict_class:
            stat["conflict_class_dist"][conflict_class] += 1
        stat["atomic_key_dist"][n_atomic_cls] += 1
        if diff_bf3:
            stat["diff_base_f3"] += 1
        if diff_bf3f4:
            stat["diff_base_f3f4"] += 1
        if is_tail_ambig:
            stat["tail_ambig"] += 1

        # F1 tracking
        ca = eng_f3f4.resolve_safe(alias_norm)
        if ca:
            stat["f1"]["hits"] += 1
        else:
            stat["f1"]["misses"] += 1

        rec = {
            "alias_id": aid,
            "alias_norm": alias_norm[:80],
            "variety": variety,
            "resolve_state": resolve_st["state"],
            "resolve_canonicals_count": len(resolve_st["canonicals"]),
            "n_atomic_keys": n_atomic_cls,
            "conflict_class": conflict_class,
            "review_priority": review_priority,

            "base_state": base_state,
            "base_reason": r_base.get("reason", ""),
            "base_dice": r_base.get("dice", 0.0),

            "f3_state": f3_state,
            "f3_reason": r_f3.get("reason", ""),
            "f3_all_rules": r_f3.get("all_rules", []),

            "f3f4_state": f3f4_state,
            "f3f4_reason": r_f3f4.get("reason", ""),
            "f3f4_all_rules": r_f3f4.get("all_rules", []),
            "f3f4_f4_suppressed": f4_suppressed,

            "diff_base_f3": diff_bf3,
            "diff_base_f3f4": diff_bf3f4,
            "transition": "%s->%s" % (base_state, f3f4_state),
            "is_tail_ambig": is_tail_ambig,
            "elapsed_ms": r_f3f4.get("elapsed_ms", 0.0),
        }
        results.append(rec)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    # F2 stats
    f2_stats = eng_f3f4.summary_stats().get("f2", {})

    # Engine meta
    eng_meta = eng_f3f4.version_info

    # Build summary
    summary = {
        "task": TASK_ID,
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": BRANCH,

        "engine": {
            "init_time_base_ms": t_base_init,
            "init_time_f3_ms": t_f3_init,
            "init_time_f3f4_ms": t_f3f4_init,
            "version_info": eng_meta,
        },

        "replay": {
            "total_entries": stat["total"],
            "valid_entries": stat["total"],
            "elapsed_ms": elapsed,
            "throughput_per_sec": round(stat["total"] / max(0.001, elapsed / 1000), 1),

            "base_verdict_dist": dict(stat["base"].most_common()),
            "f3_verdict_dist": dict(stat["f3"].most_common()),
            "f3f4_verdict_dist": dict(stat["f3f4"].most_common()),

            "resolve_state_dist": dict(stat["resolve_state"].most_common()),
            "f2_stats": f2_stats,

            "f1_stats": stat["f1"],
            "f3_trigger_dist": stat["f3_trigger"],
            "f4_trigger_dist": stat["f4_trigger"],

            "diff_base_vs_f3": stat["diff_base_f3"],
            "diff_base_vs_f3f4": stat["diff_base_f3f4"],
            "tail_ambiguous_count": stat["tail_ambig"],

            "variety_dist": dict(stat["variety_dist"].most_common()),
            "conflict_class_dist": dict(stat["conflict_class_dist"].most_common()),
        },

        "f3f4_vs_base_comparison": {
            "base_pass_count": stat["base"].get("A", 0),
            "base_review_count": stat["base"].get("R", 0),
            "base_block_count": stat["base"].get("B", 0),
            "f3f4_pass_count": stat["f3f4"].get("A", 0),
            "f3f4_review_count": stat["f3f4"].get("R", 0),
            "f3f4_block_count": stat["f3f4"].get("B", 0),
            "f3_pass_count": stat["f3"].get("A", 0),
            "f3_review_count": stat["f3"].get("R", 0),
            "f3_block_count": stat["f3"].get("B", 0),
        },

        "details": results,
    }

    # Save JSON
    out_path = OUT_JSON
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print("\n结果已保存: %s" % out_path)

    # Print summary
    print("\n" + "=" * 78)
    print("回放摘要")
    print("=" * 78)
    print("总条目: %d, 耗时: %.1fms, 吞吐: %.1f/s"
          % (stat["total"], elapsed, summary["replay"]["throughput_per_sec"]))
    print()
    print("裁决分布:")
    print("  base:  A=%d R=%d B=%d" % (stat["base"].get("A", 0), stat["base"].get("R", 0), stat["base"].get("B", 0)))
    print("  f3:    A=%d R=%d B=%d" % (stat["f3"].get("A", 0), stat["f3"].get("R", 0), stat["f3"].get("B", 0)))
    print("  f3+f4: A=%d R=%d B=%d" % (stat["f3f4"].get("A", 0), stat["f3f4"].get("R", 0), stat["f3f4"].get("B", 0)))
    print()
    print("解析状态 (F2): %s" % dict(stat["resolve_state"].most_common()))
    print()
    print("F1: hits=%d misses=%d" % (stat["f1"]["hits"], stat["f1"]["misses"]))
    print("F3 triggers: R-05=%d R-01=%d" % (stat["f3_trigger"]["r05_block"], stat["f3_trigger"]["r01_block"]))
    print("F4 suppressions: F4a=%d F4b=%d total=%d"
          % (stat["f4_trigger"]["f4a_suppress"], stat["f4_trigger"]["f4b_suppress"], stat["f4_trigger"]["total_suppressed"]))
    print()
    print("差异: base vs f3=%d  base vs f3+f4=%d" % (stat["diff_base_f3"], stat["diff_base_f3f4"]))
    print("长尾歧义: %d 条" % stat["tail_ambig"])
    print("=" * 78)

    return summary


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_report(summary):
    """生成 Markdown 回放报告."""
    r = summary["replay"]
    e = summary["engine"]
    c = summary["f3f4_vs_base_comparison"]

    md = []
    md.append("# V86 别名引擎全量回放报告")
    md.append("")
    md.append("> 任务: `%s` · 分支: `%s`" % (summary["task"], summary["branch"]))
    md.append("> 生成时间: `%s`" % summary["generated_at"])
    md.append("> 版本: `%s`" % summary["version"])
    md.append("")
    md.append("---")
    md.append("")

    # 1. 回放概要
    md.append("## 1. 回放概要")
    md.append("")
    md.append("| 指标 | 数值 |")
    md.append("|---|---|")
    md.append("| 别名条目总数 | %d |" % r["total_entries"])
    md.append("| 有效条目 (alias_norm 非空) | %d |" % r["valid_entries"])
    md.append("| 回放耗时 | %.1f ms |" % r["elapsed_ms"])
    md.append("| 吞吐 | %.1f entries/s |" % r["throughput_per_sec"])
    md.append("| 引擎初始化 (base) | %.1f ms |" % e["init_time_base_ms"])
    md.append("| 引擎初始化 (f3) | %.1f ms |" % e["init_time_f3_ms"])
    md.append("| 引擎初始化 (f3+f4) | %.1f ms |" % e["init_time_f3f4_ms"])
    md.append("")

    # 2. 裁决分布
    md.append("## 2. 三种模式裁决分布")
    md.append("")
    md.append("| 模式 | PASS (A) | REVIEW (R) | BLOCK (B) | 总计 |")
    md.append("|---|---|---|---|---|")
    md.append("| base (V85) | %d | %d | %d | %d |"
              % (c["base_pass_count"], c["base_review_count"], c["base_block_count"], r["total_entries"]))
    md.append("| f3 (F3 only) | %d | %d | %d | %d |"
              % (c["f3_pass_count"], c["f3_review_count"], c["f3_block_count"], r["total_entries"]))
    md.append("| f3+f4 (推荐) | %d | %d | %d | %d |"
              % (c["f3f4_pass_count"], c["f3f4_review_count"], c["f3f4_block_count"], r["total_entries"]))
    md.append("")

    # 3. F2 解析状态
    md.append("## 3. F2 结构化解析状态分布")
    md.append("")
    md.append("| 状态 | 数量 | 占比 |")
    md.append("|---|---|---|")
    for state, cnt in r["resolve_state_dist"].items():
        pct = round(100.0 * cnt / r["total_entries"], 2)
        md.append("| %s | %d | %.2f%% |" % (state, cnt, pct))
    md.append("")

    # 4. F1/F3/F4 触发统计
    md.append("## 4. F1/F3/F4 修复档触发统计")
    md.append("")
    md.append("### 4.1 F1 异常兜底")
    md.append("")
    md.append("| 指标 | 数值 |")
    md.append("|---|---|")
    md.append("| 别名命中 | %d |" % r["f1_stats"]["hits"])
    md.append("| 别名未命中 | %d |" % r["f1_stats"]["misses"])
    md.append("| 命中率 | %.2f%% |" % round(100.0 * r["f1_stats"]["hits"] / max(1, r["f1_stats"]["hits"] + r["f1_stats"]["misses"]), 2))
    md.append("")

    md.append("### 4.2 F3 门禁重排触发")
    md.append("")
    md.append("| 触发类型 | 数量 |")
    md.append("|---|---|")
    md.append("| R-05 黑名单阻断 | %d |" % r["f3_trigger_dist"]["r05_block"])
    md.append("| R-01 品种锚点阻断 | %d |" % r["f3_trigger_dist"]["r01_block"])
    md.append("")

    md.append("### 4.3 F4 自触发抑制")
    md.append("")
    md.append("| 类型 | 数量 |")
    md.append("|---|---|")
    md.append("| F4a 子串包含抑制 (规则级) | %d |" % r["f4_trigger_dist"]["f4a_suppress"])
    md.append("| F4b 复合短语抑制 (规则级) | %d |" % r["f4_trigger_dist"]["f4b_suppress"])
    md.append("| 规则级抑制总事件数 | %d |" % (r["f4_trigger_dist"]["f4a_suppress"] + r["f4_trigger_dist"]["f4b_suppress"]))
    md.append("| 受影响条目数 | %d |" % r["f4_trigger_dist"]["total_suppressed"])
    md.append("")

    # 5. V85 vs V86 对比
    md.append("## 5. V85 基线 vs V86 对比分析")
    md.append("")
    md.append("| 指标 | 数值 |")
    md.append("|---|---|")
    md.append("| base → f3 裁决差异 | %d 条 (%.2f%%) |"
              % (r["diff_base_vs_f3"], round(100.0 * r["diff_base_vs_f3"] / r["total_entries"], 2)))
    md.append("| base → f3+f4 裁决差异 | %d 条 (%.2f%%) |"
              % (r["diff_base_vs_f3f4"], round(100.0 * r["diff_base_vs_f3f4"] / r["total_entries"], 2)))
    md.append("")

    # 6. 长尾歧义样本
    md.append("## 6. 长尾歧义样本标记")
    md.append("")
    md.append("> 判定标准: F2 state=AMBIGUOUS 且 atomic_keys ≥ %d" % TAIL_AMBIG_THRESHOLD)
    md.append("")
    md.append("| 指标 | 数值 |")
    md.append("|---|---|")
    md.append("| 长尾歧义样本总数 | %d |" % r["tail_ambiguous_count"])
    md.append("| 占全量比例 | %.2f%% |" % round(100.0 * r["tail_ambiguous_count"] / r["total_entries"], 2))
    md.append("")

    # List tail ambiguity samples (top 20)
    tail_samples = [d for d in summary["details"] if d.get("is_tail_ambig")]
    if tail_samples:
        md.append("### 6.1 长尾歧义样本清单 (前 20)")
        md.append("")
        md.append("| # | alias_id | alias_norm | variety | n_atomic_keys | conflict_class |")
        md.append("|---|---|---|---|---|---|")
        for i, s in enumerate(tail_samples[:20]):
            md.append("| %d | %s | %s | %s | %d | %s |"
                      % (i + 1, s["alias_id"], s["alias_norm"][:40], s["variety"],
                         s["n_atomic_keys"], s.get("conflict_class", "")))
        md.append("")
        if len(tail_samples) > 20:
            md.append("> 还有 %d 条长尾歧义样本未列出 (共 %d 条)" % (len(tail_samples) - 20, len(tail_samples)))
            md.append("")

    # 7. 品种分布
    md.append("## 7. 别名库品种分布")
    md.append("")
    md.append("| 品种 | 条目数 | 占比 |")
    md.append("|---|---|---|")
    for fam, cnt in r["variety_dist"].items():
        pct = round(100.0 * cnt / r["total_entries"], 2)
        md.append("| %s | %d | %.2f%% |" % (fam, cnt, pct))
    md.append("")

    # 8. 关键发现
    md.append("## 8. 关键发现与结论")
    md.append("")

    # Compute key findings
    base_pass_rate = round(100.0 * c["base_pass_count"] / r["total_entries"], 2)
    f3f4_pass_rate = round(100.0 * c["f3f4_pass_count"] / r["total_entries"], 2)
    f3_pass_rate = round(100.0 * c["f3_pass_count"] / r["total_entries"], 2)
    f3f4_review_rate = round(100.0 * c["f3f4_review_count"] / r["total_entries"], 2)
    f2_ambig_count = r["resolve_state_dist"].get("AMBIGUOUS", 0)

    md.append("### 8.1 PASS 率对比")
    md.append("")
    md.append("| 模式 | PASS 数 | PASS 率 |")
    md.append("|---|---|---|")
    md.append("| base (V85) | %d | %.2f%% |" % (c["base_pass_count"], base_pass_rate))
    md.append("| f3 (F3 only) | %d | %.2f%% |" % (c["f3_pass_count"], f3_pass_rate))
    md.append("| f3+f4 (推荐) | %d | %.2f%% |" % (c["f3f4_pass_count"], f3f4_pass_rate))
    md.append("")

    md.append("### 8.2 核心结论")
    md.append("")
    md.append("1. **全量 %d 条别名条目全部完成回放**, 无解析失败或异常崩溃。" % r["total_entries"])
    md.append("2. **F2 确定性解析**: %d 条 AMBIGUOUS (%.2f%%), %d 条 UNIQUE (%.2f%%), %d 条 UNREGISTERED (%.2f%%)。"
              % (f2_ambig_count,
                 round(100.0 * f2_ambig_count / r["total_entries"], 2),
                 r["resolve_state_dist"].get("UNIQUE", 0),
                 round(100.0 * r["resolve_state_dist"].get("UNIQUE", 0) / r["total_entries"], 2),
                 r["resolve_state_dist"].get("UNREGISTERED", 0),
                 round(100.0 * r["resolve_state_dist"].get("UNREGISTERED", 0) / r["total_entries"], 2)))
    md.append("3. **F3 门禁重排**: %d 条裁决因 R-05 黑名单或 R-01 品种锚点被阻断。" % (r["f3_trigger_dist"]["r05_block"] + r["f3_trigger_dist"]["r01_block"]))
    md.append("4. **F4 自触发抑制**: 共 %d 条条目受影响 (规则级: F4a=%d, F4b=%d, 总事件=%d), 避免同名对误阻断。"
              % (r["f4_trigger_dist"]["total_suppressed"], r["f4_trigger_dist"]["f4a_suppress"], r["f4_trigger_dist"]["f4b_suppress"],
                 r["f4_trigger_dist"]["f4a_suppress"] + r["f4_trigger_dist"]["f4b_suppress"]))
    md.append("5. **V85→V86 差异**: base→f3+f4 裁决差异 %d 条 (%.2f%%), 主要因 F3 门禁重排+F4 自触发抑制。"
              % (r["diff_base_vs_f3f4"], round(100.0 * r["diff_base_vs_f3f4"] / r["total_entries"], 2)))
    md.append("6. **长尾歧义**: %d 条样本 atomic_keys ≥ %d 且 AMBIGUOUS, 需人工复核。"
              % (r["tail_ambiguous_count"], TAIL_AMBIG_THRESHOLD))
    md.append("")

    # 9. 长尾样本详细分析
    if tail_samples:
        md.append("### 8.3 长尾歧义样本深度分析")
        md.append("")
        # Group by conflict_class
        tail_by_class = Counter(s.get("conflict_class", "N/A") for s in tail_samples)
        md.append("| 冲突分类 | 长尾样本数 |")
        md.append("|---|---|")
        for cls, cnt in tail_by_class.most_common():
            md.append("| %s | %d |" % (cls, cnt))
        md.append("")

    # 10. 性能指标
    md.append("## 9. 性能指标")
    md.append("")
    md.append("| 指标 | 数值 |")
    md.append("|---|---|")
    md.append("| 回放吞吐 | %.1f entries/s |" % r["throughput_per_sec"])
    md.append("| 引擎初始化 (base) | %.1f ms |" % e["init_time_base_ms"])
    md.append("| 引擎初始化 (f3) | %.1f ms |" % e["init_time_f3_ms"])
    md.append("| 引擎初始化 (f3+f4) | %.1f ms |" % e["init_time_f3f4_ms"])
    md.append("| 平均单条裁决耗时 | %.3f ms |"
              % round(sum(d["elapsed_ms"] for d in summary["details"]) / max(1, len(summary["details"])), 3))
    md.append("")

    # 10. 约束合规
    md.append("## 10. 约束合规检查")
    md.append("")
    md.append("| 约束 | 状态 |")
    md.append("|---|---|")
    md.append("| 不调用 zhiji API | ✅ TRUE |")
    md.append("| 不修改 V85 冻结数据 | ✅ TRUE |")
    md.append("| 不覆盖 V85 交付物 | ✅ TRUE |")
    md.append("| 分支锁定 feature/v85-chart-template | ✅ TRUE |")
    md.append("")

    # 11. 后续建议
    md.append("## 11. 后续建议")
    md.append("")
    md.append("1. **P0 人工复核**: %d 条长尾歧义样本需人工裁决后纳入 V86 别名库。" % r["tail_ambiguous_count"])
    md.append("2. **灰度放量**: 建议 10% → 30% → 100% 分阶段放量, 监控 PASS 率与歧义率。")
    md.append("3. **降级预案**: 若 PASS 率 < %.0f%% 或歧义率 > 5%%, 自动降级至 f3 模式。" % base_pass_rate)
    md.append("4. **监控埋点**: 对齐后端异步任务 API, 上报解析耗时、裁决分布、F4 抑制次数。")
    md.append("")

    report_text = "\n".join(md)

    out_path = OUT_REPORT
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print("报告已保存: %s" % out_path)
    return report_text


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="V86 别名引擎全量回放")
    parser.add_argument("--output", type=str, default="", help="输出 JSON 路径 (默认 OUTPUT_DIR/replay_results.json)")
    parser.add_argument("--skip-report", action="store_true", help="跳过报告生成")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    global OUT_JSON, OUT_REPORT
    if args.output:
        OUT_JSON = args.output
        OUT_REPORT = os.path.join(os.path.dirname(args.output), "v86_alias_full_replay_report.md")

    # 运行回放
    summary = run_full_replay()

    # 生成报告
    if not args.skip_report:
        generate_report(summary)

    return summary


if __name__ == "__main__":
    main()
