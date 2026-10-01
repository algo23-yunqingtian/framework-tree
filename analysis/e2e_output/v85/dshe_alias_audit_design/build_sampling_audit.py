# -*- coding: utf-8 -*-
"""
build_sampling_audit.py — T2.1 别名库分层抽样人工审计 + T2.3 冲突清单 + 边界测试集回放
======================================================================================

产物：
  alias_audit_sample.csv            120 条抽样审计样本清单（100 分层 + 20 跨品种）
  multi_canonical_conflicts_165.csv 165 条 alias_norm->多原子键冲突条目清单
  sampling_audit_result.json        全部量化结果（供 4 份 MD 报告取数）

判定口径：audit_kit.adjudicate（确定性规则化审计），并逐行调用真实
new_matcher + 31 条终版黑名单复核，双证据对齐。SEED=20261001。
"""
import os
import sys
import datetime
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_kit as A
import v86_kit as K                                             # noqa: E402  (via A)

BASE_COMMIT = os.environ.get("BASE_COMMIT", "")


def main():
    os.makedirs(A.OUT, exist_ok=True)
    M, eng_meta, guard, rules, bl_lr, bl_lint = A.load_engine()
    norm_full = M["norm_full"]
    dice = A.dice_chars

    # ------------------------------------------------------------------ inputs
    alias_rows = A.read_csv(A.ALIAS_CSV)
    rerated = A.read_csv(A.RERATED_CSV)
    ths = A.read_csv(A.THS_GAP_CSV)
    hrp = A.read_csv(A.HRP_CSV)
    boundary = A.read_json(A.BOUNDARY)
    play488 = A.read_csv(A.PLAY488)
    wb_dshb = A.read_csv(A.WORKBOOK_DSHB)
    wb_hermes = A.read_csv(A.WORKBOOK_HERMES)
    batches_v6 = {}
    for fn in sorted(os.listdir(A.BATCHES_V6)):
        if fn.endswith(".csv"):
            batches_v6[fn] = A.read_csv(os.path.join(A.BATCHES_V6, fn))
    manifest = A.input_manifest(
        A.ALIAS_CSV, A.RERATED_CSV, A.THS_GAP_CSV, A.HRP_CSV, A.AMBIG_CSV,
        A.BL_FINAL, A.PLAY488, A.BOUNDARY, A.DEFECT_MD, A.RISKDB_V2,
        A.WORKBOOK_DSHB, A.WORKBOOK_HERMES, A.IV1,
        *[os.path.join(A.BATCHES_V6, f) for f in sorted(batches_v6)])

    # ------------------------------------------------- alias lib index (by norm)
    norm_index = defaultdict(list)
    for r in alias_rows:
        norm_index[r["alias_norm"]].append(r)

    # =====================================================================
    # T2.1-A  分层抽样 100 条
    # =====================================================================
    by_level = defaultdict(list)
    for r in rerated:
        by_level[r["rerated_level"]].append(r)
    stratums = ["W3_高风险", "W2_待复核", "W1_可靠同义", "W0_错误别名"]
    stratum_sizes = {s: len(by_level[s]) for s in stratums}

    rng = A.seed_rng(A.SEED)
    chosen = []
    alloc_note = []
    for s in stratums:
        pool = list(by_level[s])
        if s == "W0_错误别名":
            quota = 89
            weights = Counter(r["rerate_basis"] for r in pool)
            alloc = A.largest_remainder(weights, quota, min_one=True)
            alloc_note.append({"stratum": s, "pool": len(pool), "quota": quota,
                               "basis_groups": dict(weights.most_common()),
                               "allocation_by_basis": alloc,
                               "method": "每组保底1 + 最大余数法，SEED=20261001"})
            by_basis = defaultdict(list)
            for r in pool:
                by_basis[r["rerate_basis"]].append(r)
            for basis, k in alloc.items():
                lst = sorted(by_basis[basis], key=lambda x: x["ambig_id"])
                if k <= 0:
                    continue
                if k >= len(lst):
                    sel = lst[:]
                else:
                    sel = sorted(rng.sample(lst, k), key=lambda x: x["ambig_id"])
                for r in sel:
                    r["_stratum_basis"] = basis
                chosen.extend(sel)
        else:
            alloc_note.append({"stratum": s, "pool": len(pool), "quota": len(pool),
                               "method": "层规模 < 抽样配额，全量普查（覆盖率 100%）"})
            chosen.extend(sorted(pool, key=lambda x: x["ambig_id"]))

    # =====================================================================
    # T2.1-B  跨品种错误匹配样本 20 条（THS best_match 跨品种）
    # =====================================================================
    def bv(s):
        return sorted(A.variety_of_any(s))

    cross_rows = []
    for r in ths:
        rb, cb = bv(r["variety"]), bv(r["best_match_name"])
        if rb and cb and not (set(rb) & set(cb)):
            cross_rows.append(r)
    cross_bucket_weights = Counter(r["priority_bucket"] for r in cross_rows)
    cross_var_weights = Counter(r["variety"] for r in cross_rows)
    cv_alloc = A.largest_remainder(cross_bucket_weights, 20, min_one=True)
    by_bucket = defaultdict(list)
    for r in cross_rows:
        by_bucket[r["priority_bucket"]].append(r)
    cross_chosen = []
    for bk, k in cv_alloc.items():
        lst = sorted(by_bucket[bk], key=lambda x: int(x["priority_seq"]))
        cross_chosen.extend(lst if k >= len(lst) else sorted(rng.sample(lst, k),
                                                             key=lambda x: int(x["priority_seq"])))
    cross_chosen = sorted(cross_chosen, key=lambda x: int(x["priority_seq"]))

    # =====================================================================
    # 逐条审计
    # =====================================================================
    def audit_ambig(r, sid, group):
        left = r["indicator_name"]
        right = r["candidate_match"]
        ln = norm_full(left)[0]
        cn = norm_full(right)[0] if right else ""
        d_comp = dice(ln, cn) if cn else 0.0
        eng = A.engine_decide(M, left, right) if right else {
            "accept": False, "review": False, "reason": "empty_input", "dice": 0.0}
        hits, names = A.black_hit(M, left, right) if right else ([], [])
        adj = A.adjudicate(left, right, r["dice_score"],
                           names[0] if names else "",
                           A.primary_metric_of(M, left),
                           A.primary_metric_of(M, right) if right else "")
        alias_hits = norm_index.get(r["indicator_norm"], [])
        tpl = [x for x in play488 if x["template_id"] == r["template_id"]] if r["template_id"] else []
        return {
            "sample_id": sid, "sample_group": group,
            "stratum": "%s / %s" % (r["rerated_level"], r["rerate_basis"]),
            "source_file": "ambiguous_indicator_rerated.csv",
            "source_row_id": r["ambig_id"],
            "variety": r["variety"],
            "series_name": left, "candidate_name": right,
            "series_norm": r["indicator_norm"], "candidate_norm": r["candidate_norm"],
            "alias_norm_match_rows": len(alias_hits),
            "alias_relation": alias_hits[0]["relation"] if alias_hits else "",
            "alias_review_flag": alias_hits[0]["review_flag"] if alias_hits else "",
            "alias_confidence": alias_hits[0]["confidence"] if alias_hits else "",
            "canonical_key": alias_hits[0]["canonical_key"] if alias_hits else "",
            "dice_upstream": r["dice_score"], "dice_computed": d_comp,
            "dice_delta_pp": "" if not r["dice_score"] else
                             "%.2f" % (100.0 * (float(r["dice_score"]) - d_comp)),
            "v86_accept": eng.get("accept"), "v86_review": eng.get("review"),
            "v86_reason_engine": eng.get("reason", ""),
            "v86_reason_csv": r["v86_reason"],
            "v86_reason_consistent": (1 if eng.get("reason") == r["v86_reason"] else 0),
            "blacklist_hits_engine": ";".join(hits),
            "primary_metric_left": A.primary_metric_of(M, left),
            "primary_metric_right": A.primary_metric_of(M, right) if right else "",
            "variety_left": "|".join(sorted(A.variety_of(left))),
            "variety_right": "|".join(sorted(A.variety_of(right))),
            "metric_left": "|".join(sorted(A.metric_nouns(left))),
            "metric_right": "|".join(sorted(A.metric_nouns(right))),
            "qualifier_left": "|".join(sorted(A.qualifiers(left))),
            "qualifier_right": "|".join(sorted(A.qualifiers(right))),
            "rerated_level": r["rerated_level"], "orig_risk_level": r["orig_risk_level"],
            "rerate_basis": r["rerate_basis"],
            "orig_expected_level": r["orig_expected_level"],
            "orig_consistent": r["orig_consistent"],
            "in_high_risk_pairs": r["in_high_risk_pairs"],
            "template_id": r["template_id"],
            "tpl488_rows": len(tpl),
            "tpl488_hit_csv": r["tpl488_hit"],
            "verdict": adj["verdict"], "verdict_label": adj["verdict_label"],
            "error_type": adj["error_type"], "error_reason": adj["error_reason"],
        }

    def audit_cross(r, sid):
        left, right = r["original_ths_name"], r["best_match_name"]
        d_comp = dice(norm_full(left)[0], norm_full(right)[0])
        eng = A.engine_decide(M, left, right)
        hits, names = A.black_hit(M, left, right)
        ml, mr = A.metric_nouns(left), A.metric_nouns(right)
        same_metric = (ml & mr) != set()
        sub = "X1_同名异品种" if same_metric else "X2_语义无关"
        return {
            "sample_id": sid, "sample_group": "CROSS_VARIETY",
            "stratum": "%s / %s" % (r["priority_bucket"], r["variety"]),
            "source_file": "ths_missing_alias.csv",
            "source_row_id": "seq=%s/%s" % (r["priority_seq"], r["ths_chart_id"]),
            "variety": r["variety"],
            "series_name": left, "candidate_name": right,
            "series_norm": "", "candidate_norm": "",
            "alias_norm_match_rows": 0, "alias_relation": "",
            "alias_review_flag": "", "alias_confidence": "",
            "canonical_key": r["best_match_canonical_key"],
            "dice_upstream": r["best_match_score"],
            "dice_computed": d_comp, "dice_delta_pp": "",
            "v86_accept": eng.get("accept"), "v86_review": eng.get("review"),
            "v86_reason_engine": eng.get("reason", ""),
            "v86_reason_csv": "", "v86_reason_consistent": "",
            "blacklist_hits_engine": ";".join(hits),
            "primary_metric_left": A.primary_metric_of(M, left),
            "primary_metric_right": A.primary_metric_of(M, right),
            "variety_left": "|".join(sorted(A.variety_of_any(left))),
            "variety_right": "|".join(sorted(A.variety_of(right))),
            "metric_left": "|".join(sorted(ml)),
            "metric_right": "|".join(sorted(mr)),
            "qualifier_left": "|".join(sorted(A.qualifiers(left))),
            "qualifier_right": "|".join(sorted(A.qualifiers(right))),
            "cross_subtype": sub,
            "rerated_level": "", "orig_risk_level": "", "rerate_basis": "",
            "orig_expected_level": "", "orig_consistent": "",
            "in_high_risk_pairs": "", "template_id": r["ths_chart_id"],
            "tpl488_rows": len([x for x in play488 if x["template_id"] == r["ths_chart_id"]]),
            "tpl488_hit_csv": "",
            "verdict": "E2", "verdict_label": A.VERDICT_LABELS["E2"],
            "error_type": "品种混淆",
            "error_reason": "%s: %s vs %s (best_match_score=%s)"
                            % (sub, sorted(A.variety_of(left)),
                               sorted(A.variety_of(right)), r["best_match_score"]),
        }

    samples = []
    sid = 0
    for r in sorted(chosen, key=lambda x: (stratum_key(x), x["ambig_id"])):
        sid += 1
        samples.append(audit_ambig(r, "S-%03d" % sid, "STRATIFIED_100"))
    for r in cross_chosen:
        sid += 1
        samples.append(audit_cross(r, "S-%03d" % sid))

    # audit_confidence / human_recheck_required
    for r in samples:
        ev = []
        if r["v86_reason_engine"] != r["v86_reason_csv"] and r["sample_group"] == "STRATIFIED_100":
            ev.append("引擎复核与CSV口径不一致")
        if r["verdict"] == "OK" and float(r["dice_upstream"] or 0) < 0.6:
            ev.append("dice偏低，OK 判定可能过宽")
        r["audit_confidence"] = "LOW" if ev else ("HIGH" if r["v86_reason_consistent"] == 1
                                                   or r["sample_group"] == "CROSS_VARIETY" else "MID")
        r["human_recheck_required"] = "YES" if (r["audit_confidence"] == "LOW"
                                                or r["rerated_level"] in ("W1_可靠同义", "W2_待复核", "W3_高风险")) else "NO"
        r["notes"] = "口径不一致: engine=%s vs csv=%s" % (r["v86_reason_engine"],
                                                          r["v86_reason_csv"]) if ev else ""

    FIELDS = ["sample_id", "sample_group", "stratum", "source_file", "source_row_id",
              "variety", "series_name", "candidate_name", "series_norm", "candidate_norm",
              "alias_norm_match_rows", "alias_relation", "alias_review_flag",
              "alias_confidence", "canonical_key", "dice_upstream", "dice_computed",
              "dice_delta_pp", "v86_accept", "v86_review", "v86_reason_engine",
              "v86_reason_csv", "v86_reason_consistent", "blacklist_hits_engine",
              "primary_metric_left", "primary_metric_right", "variety_left",
              "variety_right", "metric_left", "metric_right", "qualifier_left",
              "qualifier_right", "cross_subtype", "rerated_level", "orig_risk_level",
              "rerate_basis", "orig_expected_level", "orig_consistent",
              "in_high_risk_pairs", "template_id", "tpl488_rows", "tpl488_hit_csv",
              "verdict", "verdict_label", "error_type", "error_reason",
              "audit_confidence", "human_recheck_required", "notes"]
    A.write_csv(os.path.join(A.OUT, "alias_audit_sample.csv"), samples, FIELDS)

    # =====================================================================
    # 统计
    # =====================================================================
    def dist(seq):
        return dict(Counter(seq).most_common())

    stratified = [s for s in samples if s["sample_group"] == "STRATIFIED_100"]
    cross = [s for s in samples if s["sample_group"] == "CROSS_VARIETY"]

    stats = {
        "stratum_sizes": stratum_sizes,
        "sampling_allocation": alloc_note,
        "cross_variety_pool": len(cross_rows),
        "cross_variety_bucket_weights": dict(cross_bucket_weights.most_common()),
        "cross_variety_variety_weights": dict(cross_var_weights.most_common()),
        "cross_variety_allocation": cv_alloc,
        "n_samples": len(samples),
        "n_stratified": len(stratified), "n_cross": len(cross),
        "verdict_dist_all": dist(s["verdict_label"] for s in samples),
        "verdict_dist_stratified": dist(s["verdict_label"] for s in stratified),
        "error_type_dist": dist(s["error_type"] for s in samples),
        "verdict_by_rerated_level": {
            lv: dist(s["verdict_label"] for s in stratified if s["rerated_level"] == lv)
            for lv in stratums},
        "verdict_by_basis": {
            b: dist(s["verdict_label"] for s in stratified if s["rerate_basis"] == b)
            for b in set(s["rerate_basis"] for s in stratified)},
        "cross_subtype_dist": dist(s.get("cross_subtype", "") for s in cross),
        "v86_reason_engine_dist": dist(s["v86_reason_engine"] for s in stratified),
        "engine_csv_reason_consistent": dist(s["v86_reason_consistent"] for s in stratified),
        "engine_accept_dist": dist(s["v86_accept"] for s in stratified),
        "engine_review_dist": dist(s["v86_review"] for s in stratified),
        "blacklist_hit_rows": sum(1 for s in stratified if s["blacklist_hits_engine"]),
        "blacklist_hits_total": sum(len(s["blacklist_hits_engine"].split(";"))
                                    for s in stratified if s["blacklist_hits_engine"]),
        "dice_delta_nonzero": sum(1 for s in stratified if s["dice_upstream"]
                                  and abs(float(s["dice_upstream"]) - s["dice_computed"]) > 0.0001),
        "audit_confidence_dist": dist(s["audit_confidence"] for s in samples),
        "human_recheck_dist": dist(s["human_recheck_required"] for s in samples),
        "variety_dist_sampled": dist(s["variety"] for s in stratified),
    }

    # 精确率：审计 verdict=OK 的比例
    n_ok = sum(1 for s in stratified if s["verdict"] == "OK")
    stats["sampled_alias_correct_rate_pct"] = round(100.0 * n_ok / len(stratified), 2)
    stats["sampled_error_rate_pct"] = round(100.0 * (len(stratified) - n_ok) / len(stratified), 2)

    # =====================================================================
    # T2.3  165 条多原子键冲突清单
    # =====================================================================
    canon_atoms = defaultdict(set)
    for r in alias_rows:
        for a in str(r["canonical_key"]).split("|"):
            if a:
                canon_atoms[r["alias_norm"]].add(a)
    multi = {n: sorted(ks) for n, ks in canon_atoms.items() if len(ks) > 1}
    comp_rows = [r for r in alias_rows if "|" in r["canonical_key"]]
    conflict_rows = []
    by_norm = defaultdict(list)
    for r in alias_rows:
        by_norm[r["alias_norm"]].append(r)
    for norm_name, ks in sorted(multi.items(), key=lambda x: x[0]):
        rr = by_norm[norm_name][0]
        conflict_rows.append({
            "seq": "", "alias_norm": norm_name, "n_atomic_keys": len(ks),
            "atomic_keys": "|".join(ks),
            "canonical_key_composite": rr["canonical_key"],
            "canonical_name": rr["canonical_name"],
            "alias_name": rr["alias_name"],
            "variety_family": rr["variety_family"], "metric_noun": rr["metric_noun"],
            "variety_token": rr["variety_token"], "alias_type": rr["alias_type"],
            "relation": rr["relation"], "confidence": rr["confidence"],
            "review_flag": rr["review_flag"], "review_priority": rr["review_priority"],
            "alias_source": rr["alias_source"], "distinct_form_count": rr["distinct_form_count"],
            "evidence_count": rr["evidence_count"],
            "confusable_neighbor_count": rr["confusable_neighbor_count"],
            "alias_id": rr["alias_id"],
        })
    for i, r in enumerate(conflict_rows, start=1):
        r["seq"] = i
    A.write_csv(os.path.join(A.OUT, "multi_canonical_conflicts_165.csv"),
                conflict_rows,
                ["seq", "alias_norm", "n_atomic_keys", "atomic_keys",
                 "canonical_key_composite", "canonical_name", "alias_name",
                 "variety_family", "metric_noun", "variety_token", "alias_type",
                 "relation", "confidence", "review_flag", "review_priority",
                 "alias_source", "distinct_form_count", "evidence_count",
                 "confusable_neighbor_count", "alias_id"])

    dup_name = Counter(r["canonical_name"].split("|")[0] for r in alias_rows)
    dup_name_rows = sum(1 for r in alias_rows if dup_name[r["canonical_name"].split("|")[0]] > 1)
    stats["conflict_analysis"] = {
        "alias_rows_total": len(alias_rows),
        "distinct_alias_norm": len(canon_atoms),
        "alias_norm_multi_atomic_keys": len(multi),
        "rows_with_composite_canonical_key": len(comp_rows),
        "composite_rows_all_canonical_conflict":
            (sum(1 for r in comp_rows if r["relation"] == "canonical_conflict") == len(comp_rows)),
        "multi_set_equals_composite_rows":
            (len(multi) == len(comp_rows)
             and set(multi.keys()) == set(r["alias_norm"] for r in comp_rows)),
        "distinct_composite_keys": len(set(r["canonical_key"] for r in comp_rows)),
        "n_atomic_keys_dist": dist(r["n_atomic_keys"] for r in conflict_rows),
        "variety_family_dist": dist(r["variety_family"] for r in conflict_rows),
        "review_priority_dist": dist(r["review_priority"] for r in conflict_rows),
        "alias_type_dist": dist(r["alias_type"] for r in conflict_rows),
        "duplicate_canonical_name_rows": dup_name_rows,
        "duplicate_canonical_name_distinct": sum(1 for k, v in dup_name.items() if v > 1),
        "metric_noun_top": dict(Counter(r["metric_noun"] for r in conflict_rows).most_common(8)),
        "all_involving_variant_family_multiple":
            sum(1 for r in conflict_rows if "|" in r["variety_family"]),
    }

    # =====================================================================
    # 边界测试集回放（24 例）——用于验证 DSH-B 缺陷结论 + 组装测试用例包
    # =====================================================================
    blfinal_ids = sorted(rules.keys())
    boundary_replay = []
    for c in boundary["cases"]:
        left, right = c["indicator_name"], c["matched_name"]
        eng = A.engine_decide(M, left, right)
        hits, names = A.black_hit(M, left, right)
        expected = c["expected_blocked"]
        got = not eng.get("accept", True)
        boundary_replay.append({
            "case_id": c["case_id"], "case_source": c.get("case_source", ""),
            "category": c["category"], "risk_level": c.get("risk_level", ""),
            "indicator_name": left, "matched_name": right,
            "expected_blocked": expected, "expected_rule": c.get("expected_rule", ""),
            "engine_accept": eng.get("accept"), "engine_review": eng.get("review"),
            "engine_reason": eng.get("reason", ""), "engine_rule": eng.get("rule", ""),
            "engine_dice": eng.get("dice"),
            "blacklist_hits": ";".join(hits),
            "block_result": got,
            "blocked_correct": (1 if got == expected else 0),
            "rule_matches_expected": (1 if (expected and
                                            str(c.get("expected_rule", "")).split(";")[0].strip()
                                            in ";".join(hits)
                                            or eng.get("rule") == c.get("expected_rule", ""))
                                     else (1 if not expected and not hits else 0)),
            "description": c.get("description", ""),
        })
    stats["boundary_replay"] = {
        "total": len(boundary_replay),
        "blocked_correct": sum(r["blocked_correct"] for r in boundary_replay),
        "blocked_accuracy_pct": round(100.0 * sum(r["blocked_correct"] for r in boundary_replay)
                                     / len(boundary_replay), 2),
        "expected_blocked": sum(1 for r in boundary_replay if r["expected_blocked"]),
        "engine_blocked": sum(1 for r in boundary_replay if r["block_result"]),
        "false_positive": [r["case_id"] for r in boundary_replay
                           if (not r["expected_blocked"]) and r["block_result"]],
        "false_negative": [r["case_id"] for r in boundary_replay
                           if r["expected_blocked"] and not r["block_result"]],
        "rule_label_mismatch": [
            {"case_id": r["case_id"], "expected": r["expected_rule"],
             "engine_rule": r["engine_rule"], "hits": r["blacklist_hits"]}
            for r in boundary_replay
            if r["expected_blocked"] and r["block_result"]
            and r["expected_rule"] != r["engine_rule"]],
        "by_category": {cat: {"n": sum(1 for r in boundary_replay if r["category"] == cat),
                              "correct": sum(1 for r in boundary_replay
                                              if r["category"] == cat and r["blocked_correct"])}
                        for cat in set(r["category"] for r in boundary_replay)},
    }

    # =====================================================================
    # 9 条高优先级歧义（W3 6 + W2 3）
    # =====================================================================
    hp = [s for s in samples if s["rerated_level"] in ("W3_高风险", "W2_待复核")]
    stats["high_priority"] = {
        "n": len(hp),
        "rows": [{k: v for k, v in s.items()
                  if k in ("sample_id", "source_row_id", "variety", "series_name",
                           "candidate_name", "dice_upstream", "dice_computed",
                           "v86_reason_engine", "v86_reason_csv", "blacklist_hits_engine",
                           "primary_metric_left", "primary_metric_right", "variety_left",
                           "variety_right", "metric_left", "metric_right",
                           "qualifier_left", "qualifier_right", "rerated_level",
                           "rerate_basis", "alias_relation", "alias_review_flag",
                           "alias_confidence", "canonical_key", "in_high_risk_pairs",
                           "template_id", "tpl488_rows", "tpl488_hit_csv", "verdict",
                           "verdict_label", "error_type", "error_reason",
                           "audit_confidence", "notes")} for s in hp],
    }

    # =====================================================================
    # 输出
    # =====================================================================
    result = {
        "task": A.TASK,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "base_commit": BASE_COMMIT,
        "branch": "feature/v85-chart-template",
        "seed": A.SEED,
        "engine": eng_meta,
        "blacklist": {"file": A.BL_FINAL, "rules_total": len(rules),
                      "rule_ids": blfinal_ids, "bl_lint": bl_lint,
                      "injection": "K.build_bl_lr + K.apply_rules (BL_LR via __globals__)"},
        "engine_guard": guard,
        "readonly_declaration": "未修改 indicator_alias_library.csv / indicators_v1.json / GT / "
                                "semantic_blacklist_fixed.json / 终版黑名单; 无 zhiji API 调用",
        "inputs": manifest,
        "review_batches_v6": {fn: len(rows) for fn, rows in batches_v6.items()},
        "workbook_rows": {"dshb": len(wb_dshb), "hermes": len(wb_hermes)},
        "play488_rows": len(play488),
        "play488_templates": len(set(r["template_id"] for r in play488)),
        "stats": stats,
    }
    A.write_json(os.path.join(A.OUT, "sampling_audit_result.json"), result)

    # ---------------------------------------------------------- stdout 摘要
    print("=" * 78)
    print("T2.1 抽样审计完成")
    print("  样本总数 %d (分层 %d + 跨品种 %d)" % (len(samples), len(stratified), len(cross)))
    print("  跨品种候选池 %d 行" % len(cross_rows))
    print("  verdict 分布(分层): %s" % stats["verdict_dist_stratified"])
    print("  error_type 分布: %s" % stats["error_type_dist"])
    print("  抽样别名正确率 %.2f%%" % stats["sampled_alias_correct_rate_pct"])
    print("  引擎复核与 CSV 口径一致: %s" % stats["engine_csv_reason_consistent"])
    print("  dice 上游 vs 重算不一致: %d 行" % stats["dice_delta_nonzero"])
    print("  边界测试集 %d 例, 阻塞判定正确 %d (%.2f%%)"
          % (stats["boundary_replay"]["total"],
             stats["boundary_replay"]["blocked_correct"],
             stats["boundary_replay"]["blocked_accuracy_pct"]))
    print("  规则标签不匹配: %s"
          % [x["case_id"] for x in stats["boundary_replay"]["rule_label_mismatch"]])
    print("  多原子键冲突 %d 条; 与复合键行完全重合: %s"
          % (stats["conflict_analysis"]["alias_norm_multi_atomic_keys"],
             stats["conflict_analysis"]["multi_set_equals_composite_rows"]))
    print("=" * 78)


def stratum_key(r):
    order = {"W3_高风险": 0, "W2_待复核": 1, "W1_可靠同义": 2, "W0_错误别名": 3}
    return (order.get(r["rerated_level"], 9), r.get("_stratum_basis", ""))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_COMMIT = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8")
    main()
