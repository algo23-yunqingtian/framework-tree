# -*- coding: utf-8 -*-
"""
ambig_rerated.py — T2.4 歧义指标二次复核: 重分级 + 488 模板回放触发案例
=======================================================================
DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY

输入:
  alias_lib_full_audit/ambiguous_indicator_list.csv  (448 行, 只读)
  alias_lib_full_audit/indicator_alias_library.csv    (4643 行, 只读)
  alias_lib_full_audit/high_risk_confusion_pairs.csv  (409 行, 只读)
  alias_lib_full_audit/combine_eval_result.json       (本轮 V86 联合评估结果)
  v85_final_integrate/ths_render_task_summary.csv     (488 模板任务, 只读)
  v85_render_fix_review_package/render_simulation_log_fixed.csv (488 模板回放, 只读)

输出:
  ambiguous_indicator_rerated.csv  (448 行, 新增列; 不修改原始 ambiguous 文件)
  ambiguous_rerated_result.json

重分级口径 (四档, 由 V86 判定 + 别名库标注 + 高危混淆对三源交叉):
  W0_错误别名  : V86 硬拦截 (blacklist_precheck / variety_anchor_violation /
                 metric_exclusion_hard) 或 别名库 relation ∈ {confusable_warn,
                 canonical_conflict} —— 应转为黑名单条目或反向别名
  W3_高风险    : V86 判 review (variety_neutral_target_review) 或 RISK_DB 来源 P0
  W2_待复核    : dice 落在 0.75–0.85 边界带, 或 V86 未给出明确 accept/block
  W1_可靠同义  : V86 accept 且别名库 relation == synonym_merge 且无冲突标注

488 模板触发案例:
  template_id 命中 488 模板集合 -> 取该模板的 risk_level / fully_blocked /
  route_reason / final_status 作为触发证据;
  未命中 -> 取该歧义品种在 488 集合中的模板级聚合分布作为弱证据。
约束: 不修改原始 ambiguous_indicator_list.csv; 不调用 zhiji API; 纯静态回放。
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v86_kit as K

TS = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
OUTDIR = K.OUT
OUT_CSV = os.path.join(OUTDIR, "ambiguous_indicator_rerated.csv")
OUT_JSON = os.path.join(OUTDIR, "ambiguous_rerated_result.json")
LOG = os.path.join(OUTDIR, "ambiguous_rerated_log.txt")
AUD = os.path.dirname(K.ALIAS_CSV)

AMBIG_CSV = os.path.join(AUD, "ambiguous_indicator_list.csv")
HRP_CSV = os.path.join(AUD, "high_risk_confusion_pairs.csv")
COMBINE_JSON = os.path.join(OUTDIR, "combine_eval_result.json")
TPL488_CSV = os.path.join(os.path.dirname(AUD), "v85_final_integrate",
                          "ths_render_task_summary.csv")
SIM488_CSV = os.path.join(os.path.dirname(AUD), "v85_render_fix_review_package",
                          "render_simulation_log_fixed.csv")

HARD_REASONS = {"blacklist_precheck", "variety_anchor_violation", "metric_exclusion_hard",
                "alias_conflict", "canonical_conflict", "no_match_target_recorded"}
REVIEW_REASONS = {"variety_neutral_target_review", "review"}
DICE_LOW, DICE_HIGH = 0.75, 0.85

buf = []


def pr(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    buf.append(s)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    pr("=" * 78)
    pr("ambig_rerated.py · 歧义指标二次复核 + 488 模板回放触发案例 (T2.4)")
    pr("执行时间(UTC+8): %s" % TS)
    pr("=" * 78)

    # ---- 输入存在性 ----
    need = {"ambiguous": AMBIG_CSV, "alias_lib": K.ALIAS_CSV, "hrp": HRP_CSV,
            "tpl488": TPL488_CSV, "sim488": SIM488_CSV, "combine": COMBINE_JSON}
    for k, p in need.items():
        pr("  %-10s %-62s %s" % (k, os.path.relpath(p, os.path.dirname(AUD)),
                                 "FOUND" if os.path.exists(p) else "MISSING"))
    if not os.path.exists(AMBIG_CSV):
        pr("FATAL: ambiguous_indicator_list.csv 缺失, 退出")
        sys.exit(2)

    # ---- 加载引擎 (与原 build_alias_library.py 一致) ----
    M = K.load_engine()
    new_matcher = M["new_matcher"]
    metal_families = M["metal_families"]
    norm_light = M["norm_light"]
    # 守卫: 原 resolve_canonical 对未入库归一名硬索引 ALIAS[nm] -> KeyError。
    # 守卫后语义 = 未入库则跳过别名侧解析 (等价于查无此项), 不改写源文件。
    guard = K.guard_resolve_canonical(M)
    pr("resolve_canonical 守卫: patched=%s, ALIAS 条目 %d"
       % (guard["patched"], guard["total_alias_entries"]))

    def decide(a, b):
        try:
            return new_matcher(a, b)
        except Exception as e:
            return {"accept": None, "review": None, "reason": "ERROR:%s:%s"
                    % (type(e).__name__, e), "rule": ""}

    amb = list(csv.DictReader(open(AMBIG_CSV, encoding="utf-8-sig", newline="")))
    ali = list(csv.DictReader(open(K.ALIAS_CSV, encoding="utf-8-sig", newline="")))
    hrp = list(csv.DictReader(open(HRP_CSV, encoding="utf-8-sig", newline=""))) if \
        os.path.exists(HRP_CSV) else []

    # ---- 索引 ----
    alias_by_norm = defaultdict(list)
    for r in ali:
        alias_by_norm[r["alias_norm"].strip()].append(r)
    alias_by_id = {r["alias_id"]: r for r in ali}
    hrp_pairs = set()
    hrp_by_pair = {}
    for r in hrp:
        key = (r.get("alias_norm_l", r.get("left", "")), r.get("alias_norm_r", r.get("right", "")))
        hrp_pairs.add(key)
        hrp_by_pair[key] = r
    pr("\n歧义清单 %d 行 | 别名库 %d 行 | 高危混淆对 %d 行" % (len(amb), len(ali), len(hrp)))
    if hrp:
        pr("  高危混淆对列名: %s" % list(hrp[0].keys()))

    # ---- 488 模板集合 ----
    tpl488 = {}
    if os.path.exists(TPL488_CSV):
        for r in csv.DictReader(open(TPL488_CSV, encoding="utf-8-sig", newline="")):
            tpl488[r["template_id"]] = r
    sim488 = {}
    if os.path.exists(SIM488_CSV):
        for r in csv.DictReader(open(SIM488_CSV, encoding="utf-8-sig", newline="")):
            sim488[r["template_id"]] = r
    var488 = defaultdict(Counter)
    for tid, r in tpl488.items():
        var488[r["variety"]]["templates"] += 1
        var488[r["variety"]]["risk_" + r["risk_level"]] += 1
    for tid, r in sim488.items():
        var488[r["variety"]]["fully_blocked_" + r["fully_blocked"]] += 1
        var488[r["variety"]]["final_" + r["final_status"]] += 1
    pr("488 模板集合: summary %d 行 | simulation %d 行 | 品种分布 %s"
       % (len(tpl488), len(sim488),
          {k: v["templates"] for k, v in sorted(var488.items())}))

    # ---- 联合评估 (V86) 指标快照, 用于重分级说明 ----
    combine = {}
    if os.path.exists(COMBINE_JSON):
        combine = json.load(open(COMBINE_JSON, encoding="utf-8"))
    v86 = combine.get("v86_confusion", combine.get("confusion", {}))
    pr("V86 联合评估快照: %s" % json.dumps(v86, ensure_ascii=False)[:200])

    # ---- 逐行重分级 ----
    OUT_COLS = list(amb[0].keys()) + [
        "v86_accept", "v86_review", "v86_reason", "v86_rule", "v86_blacklist_rule",
        "alias_relation", "alias_review_flag", "alias_confusable_neighbor_count",
        "in_high_risk_pairs", "orig_risk_level", "orig_expected_level", "orig_consistent",
        "rerated_level", "rerate_basis",
        "rerate_delta", "tpl488_hit", "tpl488_risk_level", "tpl488_fully_blocked",
        "tpl488_route_reason", "tpl488_final_status", "tpl488_trigger",
    ]
    out = []
    lvl_cnt = Counter()
    delta_cnt = Counter()
    basis_cnt = Counter()
    trigger_cnt = Counter()
    w0_samples, w3_samples, w1_samples = [], [], []
    for r in amb:
        a = r["indicator_name"]
        b = r["candidate_match"]
        d = decide(a, b)
        an, bn = r["indicator_norm"].strip(), r["candidate_norm"].strip()
        rows_a = alias_by_norm.get(an, [])
        rows_b = alias_by_norm.get(bn, [])
        rel = rows_a[0]["relation"] if rows_a else ""
        flag = rows_a[0]["review_flag"] if rows_a else ""
        try:
            cnb = int(float(rows_a[0]["confusable_neighbor_count"])) if rows_a else 0
        except ValueError:
            cnb = 0
        in_hrp = (an, bn) in hrp_pairs or (bn, an) in hrp_pairs
        try:
            dice_v = float(r["dice_score"])
        except ValueError:
            dice_v = 0.0
        orig_level = r["risk_level"]

        # ---- 分级 ----
        if d["reason"] in HARD_REASONS or rel in ("confusable_warn", "canonical_conflict"):
            lvl = "W0_错误别名"
            basis = "V86硬拦截(%s)" % d["reason"] if d["reason"] in HARD_REASONS \
                else "别名库标注(%s)" % rel
        elif in_hrp and orig_level == "P0":
            lvl = "W3_高风险"
            basis = "高危混淆对+P0"
        elif d["reason"] in REVIEW_REASONS or (r["ambiguity_source"] == "RISK_DB"
                                               and orig_level == "P0"):
            lvl = "W3_高风险"
            basis = "V86降级复核(%s)" % d["reason"] if d["reason"] in REVIEW_REASONS \
                else "RISK_DB_P0"
        elif DICE_LOW <= dice_v < DICE_HIGH:
            lvl = "W2_待复核"
            basis = "dice边界(%s)" % r["dice_score"]
        elif d.get("accept") is True and rel == "synonym_merge":
            lvl = "W1_可靠同义"
            basis = "V86通过+synonym_merge"
        elif d.get("accept") is True:
            lvl = "W1_可靠同义"
            basis = "V86通过(%s)" % d["reason"]
        elif d.get("accept") is None and d["reason"].startswith("ERROR"):
            lvl = "W2_待复核"
            basis = "引擎异常(%s)" % d["reason"][:28]
        else:
            lvl = "W2_待复核"
            basis = "未决(%s)" % d["reason"]

        # ---- 488 触发 ----
        tid = r["template_id"].strip()
        t_hit = tid in tpl488
        if t_hit:
            t = tpl488[tid]
            s = sim488.get(tid, {})
            t_risk = t["risk_level"]
            t_fb = s.get("fully_blocked", "")
            t_rr = s.get("route_reason", "")
            t_fs = s.get("final_status", "")
            t_trig = "命中模板 %s (risk=%s, fully_blocked=%s, status=%s)" \
                     % (tid, t_risk, t_fb, t_fs)
        else:
            vv = var488.get(r["variety"], Counter())
            t_risk = "N/A"
            t_fb = "N/A"
            t_rr = "N/A"
            t_fs = "N/A"
            t_trig = "无模板命中; 品种%s在488中模板%d个, P0=%d, CLEAN=%d" \
                     % (r["variety"], vv.get("templates", 0),
                        vv.get("risk_P0", 0), vv.get("risk_CLEAN", 0))

        # 原 review_priority -> 期望等级 (用于一致性比对)
        exp_map = {"P0_manual": "W3_高风险", "P1_manual": "W2_待复核", "P2_auto": "W1_可靠同义"}
        exp = exp_map.get(r["review_priority"], "N/A")
        consistent = (lvl == exp) or (
            r["review_priority"] == "P0_manual" and lvl == "W0_错误别名")
        order = {"W0_错误别名": 0, "W3_高风险": 1, "W2_待复核": 2, "W1_可靠同义": 3}
        delta = order.get(lvl, 9) - order.get(exp, 9) if exp != "N/A" else 0

        out.append({
            "ambig_id": r["ambig_id"], "indicator_name": a, "indicator_norm": an,
            "variety": r["variety"], "candidate_match": b, "candidate_norm": bn,
            "ambiguity_source": r["ambiguity_source"], "risk_level": orig_level,
            "blacklist_rule": r["blacklist_rule"], "blacklist_name": r["blacklist_name"],
            "conflict_type": r["conflict_type"], "conflict_reason": r["conflict_reason"],
            "dice_score": r["dice_score"], "template_id": tid,
            "origin_source": r["origin_source"], "review_priority": r["review_priority"],
            "review_action": r["review_action"],
            "v86_accept": "" if d["accept"] is None else str(d["accept"]).lower(),
            "v86_review": "" if d.get("review") is None else str(d["review"]).lower(),
            "v86_reason": d["reason"], "v86_rule": d.get("rule", ""),
            "v86_blacklist_rule": d.get("blacklist_rule", "") or r["blacklist_rule"],
            "alias_relation": rel, "alias_review_flag": flag,
            "alias_confusable_neighbor_count": cnb,
            "in_high_risk_pairs": "Y" if in_hrp else "N",
            "orig_risk_level": orig_level, "orig_expected_level": exp,
            "orig_consistent": "Y" if consistent else "N",
            "rerated_level": lvl,
            "rerate_basis": basis, "rerate_delta": delta,
            "tpl488_hit": "Y" if t_hit else "N", "tpl488_risk_level": t_risk,
            "tpl488_fully_blocked": t_fb, "tpl488_route_reason": t_rr,
            "tpl488_final_status": t_fs, "tpl488_trigger": t_trig,
        })
        lvl_cnt[lvl] += 1
        delta_cnt[delta] += 1
        basis_cnt[basis.split("(")[0]] += 1
        trigger_cnt["hit" if t_hit else "miss"] += 1
        if lvl == "W0_错误别名" and len(w0_samples) < 12:
            w0_samples.append({"id": r["ambig_id"], "a": a[:26], "b": b[:26],
                               "basis": basis, "tpl": t_trig[:40]})
        if lvl == "W3_高风险" and len(w3_samples) < 12:
            w3_samples.append({"id": r["ambig_id"], "a": a[:26], "b": b[:26],
                               "basis": basis, "tpl": t_trig[:40]})
        if lvl == "W1_可靠同义" and len(w1_samples) < 8:
            w1_samples.append({"id": r["ambig_id"], "a": a[:26], "b": b[:26],
                               "basis": basis, "tpl": t_trig[:40]})

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(out)

    pr("\n" + "=" * 78)
    pr("【重分级结果】共 %d 行 (原等级 P0/P1/P2, 新等级 W0/W1/W2/W3)" % len(out))
    pr("  %-14s %6s %8s" % ("新等级", "行数", "占比"))
    ORDER = ["W0_错误别名", "W3_高风险", "W2_待复核", "W1_可靠同义"]
    for l in ORDER:
        pr("  %-14s %6d %7.1f%%" % (l, lvl_cnt[l], 100.0 * lvl_cnt[l] / len(out)))
    pr("\n  分级依据分布:")
    for k, v in basis_cnt.most_common():
        pr("    %-26s %5d" % (k, v))
    pr("\n  V86 判定分布: %s"
       % dict(Counter(o["v86_reason"] for o in out).most_common()))
    pr("  守卫触发 %d 次 (未入库归一名, 已跳过别名侧解析); 样例: %s"
       % (guard["guard_hits"], guard["missing_samples"][:6]))
    pr("  等级变动 (0=不变, 负=降级更严, 正=放宽): %s" % dict(sorted(delta_cnt.items())))
    pr("  原 P0 251 行中: %s"
       % dict(Counter(o["rerated_level"] for o in out if o["orig_risk_level"] == "P0")))
    pr("  原 P1 176 行中: %s"
       % dict(Counter(o["rerated_level"] for o in out if o["orig_risk_level"] == "P1")))
    pr("  原 P2 21 行中: %s"
       % dict(Counter(o["rerated_level"] for o in out if o["orig_risk_level"] == "P2")))
    n_cons = sum(1 for o in out if o["orig_consistent"] == "Y")
    pr("\n【与原分级一致性】")
    pr("  一致 %d 行 (%.1f%%) | 不一致 %d 行 (%.1f%%)"
       % (n_cons, 100.0 * n_cons / len(out), len(out) - n_cons,
          100.0 * (len(out) - n_cons) / len(out)))
    pr("  不一致方向 (期望 -> 实际):")
    dirc = Counter((o["orig_expected_level"], o["rerated_level"]) for o in out
                   if o["orig_consistent"] == "N")
    for (a, b), n in dirc.most_common():
        pr("    %-14s -> %-14s %5d" % (a, b, n))

    pr("\n【488 模板回放触发】")
    pr("  模板级命中 %d 行 / 品种级弱证据 %d 行" % (trigger_cnt["hit"], trigger_cnt["miss"]))
    hit_rows = [o for o in out if o["tpl488_hit"] == "Y"]
    if hit_rows:
        pr("  命中模板分布: %s"
           % dict(Counter(o["tpl488_risk_level"] for o in hit_rows)))
        pr("  命中模板 final_status: %s"
           % dict(Counter(o["tpl488_final_status"] for o in hit_rows)))
        pr("  命中模板 fully_blocked: %s"
           % dict(Counter(o["tpl488_fully_blocked"] for o in hit_rows)))
    else:
        pr("  488 模板集合中无可与歧义清单直接关联的 template_id")

    pr("\n【W0 样本】")
    for s in w0_samples:
        pr("  %s | %s -> %s | %s | %s" % (s["id"], s["a"], s["b"], s["basis"], s["tpl"]))
    pr("\n【W3 样本】")
    for s in w3_samples:
        pr("  %s | %s -> %s | %s | %s" % (s["id"], s["a"], s["b"], s["basis"], s["tpl"]))
    pr("\n【W1 样本】")
    for s in w1_samples:
        pr("  %s | %s -> %s | %s | %s" % (s["id"], s["a"], s["b"], s["basis"], s["tpl"]))

    res = {
        "task": K.INTEGRATION_TASK, "generated_at": TS,
        "inputs": {k: (os.path.exists(p) and os.path.getsize(p)) for k, p in need.items()},
        "rows": len(out), "level_dist": dict(lvl_cnt),
        "level_dist_pct": {l: round(100.0 * lvl_cnt[l] / len(out), 2) for l in ORDER},
        "basis_dist": dict(basis_cnt),
        "v86_reason_dist": dict(Counter(o["v86_reason"] for o in out)),
        "engine_guard": {"patched": guard["patched"], "guard_hits": guard["guard_hits"],
                         "total_alias_entries": guard["total_alias_entries"],
                         "missing_samples": guard["missing_samples"],
                         "note": "build_alias_library.py 第264-265行对 ALIAS[nm] 硬索引, "
                                 "未入库归一名抛 KeyError; 本脚本进程内加 .get() 守卫, 未改写源文件"},
        "rerate_delta_dist": dict(sorted(delta_cnt.items())),
        "consistency_with_original": {
            "consistent": n_cons, "inconsistent": len(out) - n_cons,
            "consistent_pct": round(100.0 * n_cons / len(out), 2),
            "inconsistent_direction": [{"expected": a, "actual": b, "n": n}
                                       for (a, b), n in dirc.most_common()],
        },
        "by_orig_level": {lv: dict(Counter(o["rerated_level"] for o in out
                                           if o["orig_risk_level"] == lv))
                          for lv in ("P0", "P1", "P2")},
        "tpl488": {"hit": trigger_cnt["hit"], "miss": trigger_cnt["miss"],
                   "hit_risk_level": dict(Counter(o["tpl488_risk_level"] for o in hit_rows)),
                   "hit_final_status": dict(Counter(o["tpl488_final_status"] for o in hit_rows)),
                   "hit_fully_blocked": dict(Counter(o["tpl488_fully_blocked"] for o in hit_rows)),
                   "template_set_size": len(tpl488), "simulation_set_size": len(sim488),
                   "by_variety_templates": {k: v["templates"] for k, v in sorted(var488.items())}},
        "in_high_risk_pairs": sum(1 for o in out if o["in_high_risk_pairs"] == "Y"),
        "samples": {"W0": w0_samples, "W3": w3_samples, "W1": w1_samples},
        "v86_snapshot": v86,
        "output_csv": os.path.basename(OUT_CSV),
        "columns_added": OUT_COLS[len(amb[0].keys()):],
        "original_untouched": True,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    open(LOG, "w", encoding="utf-8").write("\n".join(buf))
    pr("\n已写出: %s (%d 行, %d bytes)" % (OUT_CSV, len(out), os.path.getsize(OUT_CSV)))
    pr("已写出: %s" % OUT_JSON)
    pr("已写出: %s" % LOG)
    pr("=" * 78)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
