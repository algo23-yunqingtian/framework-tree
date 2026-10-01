# -*- coding: utf-8 -*-
"""
blacklist_testset_verdicts.py — 对 24 条 boundary testset 跑 base / fixed 门禁，
输出期望可达性与不一致清单（T2.4 / T2.6 的事实基线）。
产物：blacklist_testset_verdicts.csv
"""
import csv
import io
import json
import sys

CD = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_audit_design"
DMM = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\miss_risk_mining"
DIN = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_integrate_test"
sys.path.insert(0, CD)
sys.path.insert(0, DIN)
import audit_kit as A  # noqa: E402
from canonical_resolve_fix import (  # noqa: E402
    blacklist_check_bounded, build_fixed_resolver, build_reordered_matcher)

M, em, guard, rules, bl_lr, lint = A.load_engine()
NF = M["norm_full"]
TS = json.load(io.open(DMM + r"\blacklist_boundary_testset.json", encoding="utf-8"))["cases"]

resolve_safe, resolve_structured, stat = build_fixed_resolver(M)
fixed = build_reordered_matcher(M, resolve_safe, use_f4=True)
fixed_f3 = build_reordered_matcher(M, resolve_safe, use_f4=False)

rows_out = []
for c in TS:
    a, b = c["indicator_name"], c["matched_name"]
    ra = NF(a)[0]; rb = NF(b)[0]
    vb = M["new_matcher"](a, b)
    vf = fixed(a, b)
    v3 = fixed_f3(a, b)
    _, skipped = blacklist_check_bounded(M, ra, rb)
    hits_all = []
    for rid, (L, R, sev, nm) in M["BL_LR"].items():
        if (any(q in ra for q in L) and any(q in rb for q in R)) or \
           (any(q in rb for q in L) and any(q in ra for q in R)):
            hits_all.append(rid)

    def verdict(v):
        return "BLOCK" if (not v["accept"] and not v["review"]) else \
               ("REVIEW" if v["review"] else "PASS")

    exp_blocked = c["expected_blocked"]
    ok_base = (verdict(vb) == "BLOCK") == exp_blocked
    ok_fix = (verdict(vf) == "BLOCK") == exp_blocked
    expected_rule = str(c.get("expected_rule", ""))
    rule_missing = [r for r in expected_rule.split(";")
                    if r.strip() and r.strip() != "NONE" and r.strip() not in M["BL_LR"]]
    reachable = all(r.strip() in hits_all
                    for r in expected_rule.split(";") if r.strip() != "NONE") if \
        expected_rule.strip() != "NONE" else True
    rows_out.append({
        "case_id": c["case_id"], "category": c["category"], "risk_level": c["risk_level"],
        "indicator_name": a, "matched_name": b,
        "expected_blocked": exp_blocked, "expected_rule": expected_rule,
        "rules_referenced_but_not_exist": "|".join(rule_missing) or "-",
        "rules_actually_hit_full_substring": "|".join(hits_all) or "-",
        "all_expected_rules_hit": "YES" if reachable else "NO",
        "verdict_base": verdict(vb), "base_reason": vb.get("reason", ""),
        "verdict_f3": verdict(v3), "f3_reason": v3.get("reason", ""),
        "verdict_f3f4": verdict(vf), "f3f4_reason": vf.get("reason", ""),
        "f3f4_all_rules": "|".join(vf.get("all_rules", [])) or "-",
        "base_matches_expectation": "YES" if ok_base else "NO",
        "f3f4_matches_expectation": "YES" if ok_fix else "NO",
        "verdict_changed_by_fix": "YES" if verdict(vb) != verdict(vf) else "NO",
    })

with io.open(CD + r"\blacklist_testset_verdicts.csv", "w", encoding="utf-8-sig",
             newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    w.writerows(rows_out)

from collections import Counter  # noqa: E402
print("=" * 78)
print("24 条 boundary testset 在 base / F3 / F3+F4 下的裁决")
print("=" * 78)
print("类别:", dict(Counter(x["category"] for x in rows_out).most_common()))
print("expected_blocked:", dict(Counter(x["expected_blocked"] for x in rows_out).most_common()))
print("base 与期望一致: %d/24" % sum(1 for x in rows_out
                                    if x["base_matches_expectation"] == "YES"))
print("F3+F4 与期望一致: %d/24" % sum(1 for x in rows_out
                                     if x["f3f4_matches_expectation"] == "YES"))
print("裁决被修复改变: %d/24" % sum(1 for x in rows_out
                                   if x["verdict_changed_by_fix"] == "YES"))
print("期望规则不存在（testset 缺陷）: %d/24" % sum(
    1 for x in rows_out if x["rules_referenced_but_not_exist"] != "-"))
print("  涉及用例:", [(x["case_id"], x["rules_referenced_but_not_exist"])
                     for x in rows_out if x["rules_referenced_but_not_exist"] != "-"])
print("期望规则未被完整命中: %d/24" % sum(1 for x in rows_out
                                        if x["all_expected_rules_hit"] == "NO"))
print("  涉及用例:", [(x["case_id"], x["expected_rule"], x["rules_actually_hit_full_substring"])
                     for x in rows_out if x["all_expected_rules_hit"] == "NO"])
print("base 不一致用例:", [(x["case_id"], x["expected_blocked"], x["verdict_base"],
                          x["base_reason"]) for x in rows_out
                          if x["base_matches_expectation"] == "NO"])
print("F3+F4 不一致用例:", [(x["case_id"], x["expected_blocked"], x["verdict_f3f4"],
                           x["f3f4_reason"]) for x in rows_out
                            if x["f3f4_matches_expectation"] == "NO"])
print("裁决变化明细:", [(x["case_id"], x["verdict_base"], "->", x["verdict_f3f4"],
                        x["f3f4_reason"]) for x in rows_out
                       if x["verdict_changed_by_fix"] == "YES"])
print("输出: blacklist_testset_verdicts.csv")
print("=" * 78)
