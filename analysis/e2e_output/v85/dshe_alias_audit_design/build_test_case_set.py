# -*- coding: utf-8 -*-
"""
build_test_case_set.py — T2.6 V86 别名引擎测试用例包
=================================================================
产物：alias_test_case_set.json

五个场景族（全部来自真实输入 + 真实引擎回放，SEED=20261001）：
  TC-POS   正向同义      引擎应 accept=True
  TC-NEG   反向冲突      引擎应 accept=False 且 review=False（硬拦截）
  TC-XVAR  跨品种混淆    引擎应 accept=False 且 reason=variety_anchor_violation
  TC-MULTI 多 canon 冲突 归一化后 alias_norm 指向 >1 原子键（165 条）
  TC-MISS  缺失别名      THS 原名无 canonical 注册（2299 条 UNREGISTERED_ONLY）
每条用例记录 oracle（引擎实际输出）+ expectation（设计期望）+ verdict
（PASS / FAIL / NEEDS_HUMAN）。FAIL 用例即 V86 的缺陷回归项。
"""
import os
import sys
import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_kit as A      # noqa: E402

CD = os.path.dirname(os.path.abspath(__file__))


def main():
    M, eng_meta, guard, rules, bl_lr, bl_lint = A.load_engine()
    norm_full = M["norm_full"]
    rng = A.seed_rng(A.SEED)

    ths = A.read_csv(A.THS_GAP_CSV)
    rerated = A.read_csv(A.RERATED_CSV)
    hrp = A.read_csv(A.HRP_CSV)
    boundary = A.read_json(A.BOUNDARY)
    boundary_cases = boundary["cases"]
    conflict_rows = A.read_csv(os.path.join(CD, "multi_canonical_conflicts_165.csv"))
    samples = A.read_csv(os.path.join(CD, "alias_audit_sample.csv"))

    cases = []
    seq = Counter()

    def add(family, subgroup, left, right, expectation, source, note="", **kw):
        eng = A.engine_decide(M, left, right) if right else {
            "accept": False, "review": False, "reason": "empty_input", "dice": 0.0}
        hits, names = A.black_hit(M, left, right) if right else ([], [])
        d = None
        if right:
            d = A.dice_chars(norm_full(left)[0], norm_full(right)[0])
        v = verdict_of(expectation, eng, hits)
        seq[family] += 1
        c = {
            "tc_id": "%s-%04d" % (family, seq[family]),
            "family": family, "subgroup": subgroup,
            "left": left, "right": right,
            "source": source,
            "expectation": expectation,
            "oracle": {
                "accept": eng.get("accept"), "review": eng.get("review"),
                "reason": eng.get("reason", ""), "rule": eng.get("rule", ""),
                "canonical": eng.get("canonical", ""),
                "dice_engine": eng.get("dice"),
                "dice_independent": d,
                "blacklist_hits": hits,
            },
            "verdict": v,
            "note": note,
        }
        c.update(kw)
        cases.append(c)
        return c

    def verdict_of(exp, eng, hits):
        """比较 expectation 与 oracle，返回 'PASS' 或 'FAIL:<字段明细>'。"""
        bad = []
        if "accept" in exp and bool(eng.get("accept")) != bool(exp["accept"]):
            bad.append("accept")
        if "review" in exp and bool(eng.get("review")) != bool(exp["review"]):
            bad.append("review")
        if "reason" in exp and eng.get("reason") != exp["reason"]:
            bad.append("reason:%s!=%s" % (exp["reason"], eng.get("reason")))
        if "reason_in" in exp and eng.get("reason") not in exp["reason_in"]:
            bad.append("reason_in:%s not in %s" % (exp["reason_in"], eng.get("reason")))
        if "must_hit" in exp and not (set(exp["must_hit"]) & set(hits)):
            bad.append("must_hit:%s vs %s" % (exp["must_hit"], hits))
        if "must_not_hit" in exp and (set(exp["must_not_hit"]) & set(hits)):
            bad.append("must_not_hit violated: %s" % (set(exp["must_not_hit"]) & set(hits)))
        if exp.get("alias_exact_first") and hits and eng.get("reason") == "alias_exact":
            bad.append("alias_exact_bypasses_blacklist(hits=%s)" % hits)
        if not bad:
            return "PASS"
        return "FAIL:" + ";".join(bad)

    # ---------------------------------------------------------------- TC-POS
    # 1) 引擎判定 accept=True 的真实样本（正向同义）
    pos_from_samples = [s for s in samples
                        if s["sample_group"] == "STRATIFIED_100" and s["v86_accept"] == "True"]
    for s in pos_from_samples:
        add("TC-POS", "alias_sampling_audit", s["series_name"], s["candidate_name"],
            {"accept": True, "reason_in": ["high_dice", "mid_dice_same_variety",
                                            "low_dice_no_variety", "alias_exact"]},
            "alias_audit_sample.csv:%s" % s["sample_id"],
            note="抽样审计层内引擎自动放行样本")
    # 2) 别名精确命中（alias_exact）：R-07 的正向能力
    alias_rows = A.read_csv(A.ALIAS_CSV)
    seen_pair = set()
    n_alias_exact = 0
    for r in alias_rows:
        if r["relation"] != "synonym_merge":
            continue
        cn = r["canonical_name"].split("|")[0]
        an = r["alias_name"]
        if not cn or not an or cn == an:
            continue
        if (cn, an) in seen_pair:
            continue
        e = A.engine_decide(M, an, cn)
        if e.get("reason") == "alias_exact":
            seen_pair.add((an, cn))
            add("TC-POS", "alias_exact", an, cn,
                {"accept": True, "reason": "alias_exact", "alias_exact_first": True},
                "indicator_alias_library.csv:%s" % r["alias_id"],
                note="别名精确命中（R-07），canonical=%s" % e.get("canonical", ""))
            n_alias_exact += 1
            if n_alias_exact >= 40:
                break
    # 3) 边界测试集里的安全负向样例（期望不阻塞）
    for c in boundary_cases:
        if c["category"] == "安全负向样例":
            add("TC-POS", "boundary_safe_negative", c["indicator_name"], c["matched_name"],
                {"accept": True}, "blacklist_boundary_testset.json:%s" % c["case_id"],
                note=c.get("description", ""))

    # ---------------------------------------------------------------- TC-NEG
    for c in boundary_cases:
        if c["category"] == "正向危险样例":
            exp = {"accept": False, "review": False}
            er = str(c.get("expected_rule", "")).split(";")[0].strip()
            if er and er != "NONE":
                exp["must_hit"] = [er]
            add("TC-NEG", "boundary_dangerous", c["indicator_name"], c["matched_name"],
                exp, "blacklist_boundary_testset.json:%s" % c["case_id"],
                note="期望规则 %s" % c.get("expected_rule", ""))
    # 黑名单命中且非别名精确（应硬拦截）
    for s in samples:
        if s["sample_group"] == "STRATIFIED_100" and s["blacklist_hits_engine"] and \
           s["v86_reason_engine"] != "alias_exact":
            add("TC-NEG", "blacklist_hard_block", s["series_name"], s["candidate_name"],
                {"accept": False, "review": False, "reason": "blacklist_precheck",
                 "must_hit": s["blacklist_hits_engine"].split(";")},
                "alias_audit_sample.csv:%s" % s["sample_id"],
                note="v86_reason=%s" % s["v86_reason_engine"])
    # R-03 口径互斥硬拦截
    for s in samples:
        if s["sample_group"] == "STRATIFIED_100" and s["v86_reason_engine"] == "metric_exclusion_hard":
            add("TC-NEG", "metric_exclusion_hard", s["series_name"], s["candidate_name"],
                {"accept": False, "review": False, "reason": "metric_exclusion_hard"},
                "alias_audit_sample.csv:%s" % s["sample_id"])

    # ---------------------------------------------------------------- TC-XVAR
    for p in hrp:
        if p.get("cross_variety", "").upper() not in ("YES", "Y"):
            continue
        add("TC-XVAR", "high_risk_confusion_pairs", p["left"], p["right"],
            {"accept": False, "review": False,
             "reason_in": ["variety_anchor_violation", "blacklist_precheck"]},
            "high_risk_confusion_pairs.csv",
            note="dice=%s severity=%s" % (p.get("dice", ""), p.get("severity", "")))
    for s in samples:
        if s["sample_group"] == "CROSS_VARIETY":
            add("TC-XVAR", "ths_best_match_cross", s["series_name"], s["candidate_name"],
                {"accept": False},
                "alias_audit_sample.csv:%s (%s)" % (s["sample_id"], s["stratum"]),
                note="THS best_match 跨品种；subtype=%s" % s.get("cross_subtype", ""))
    # 高危混淆对全量（409）
    n_all = 0
    for p in hrp:
        if n_all >= 60:
            break
        add("TC-XVAR", "confusion_pair_full", p["left"], p["right"],
            {"accept": False},
            "high_risk_confusion_pairs.csv",
            note="severity=%s category=%s" % (p.get("severity", ""), p.get("category", "")))
        n_all += 1

    # ---------------------------------------------------------------- TC-MULTI
    # 165 条：alias_norm 指向多个原子键 -> 期望引擎拒绝自动合并或降级复核
    for r in conflict_rows:
        cn_parts = r["canonical_name"].split("||")
        left = r["alias_name"]
        right = cn_parts[0] if cn_parts else ""
        add("TC-MULTI", "alias_norm_multi_canonical", left, right,
            {"accept": False, "alias_exact_first": True},
            "indicator_alias_library.csv:%s" % r["alias_id"],
            note="alias_norm=%s 指向 %s 个原子键: %s"
                 % (r["alias_norm"], r["n_atomic_keys"], r["atomic_keys"][:120]),
            alias_norm=r["alias_norm"],
            n_atomic_keys=int(r["n_atomic_keys"]),
            atomic_keys=r["atomic_keys"],
            variety_family=r["variety_family"],
            relation=r["relation"],
            review_priority=r["review_priority"])

    # ---------------------------------------------------------------- TC-MISS
    unreg = [r for r in ths if r["ths_alias_status"] == "UNREGISTERED_ONLY"]
    rng.shuffle(unreg)
    for r in unreg[:80]:
        add("TC-MISS", "ths_unregistered", r["original_ths_name"], r["best_match_name"],
            {"accept": False},
            "ths_missing_alias.csv:seq=%s" % r["priority_seq"],
            note="THS 原名无 canonical 注册；best_match=%s (score=%s)"
                 % (r["best_match_name"], r["best_match_score"]))
    # 别名库未注册项
    unreg_alias = [r for r in alias_rows if r["review_flag"] == "register_pending"]
    rng.shuffle(unreg_alias)
    for r in unreg_alias[:60]:
        cn = r["canonical_name"].split("|")[0] if r["canonical_name"] else ""
        add("TC-MISS", "alias_register_pending", r["alias_name"], cn,
            {"accept": False},
            "indicator_alias_library.csv:%s" % r["alias_id"],
            note="relation=%s confidence=%s" % (r["relation"], r["confidence"]))

    # ---------------------------------------------------------------- 汇总
    fams = ["TC-POS", "TC-NEG", "TC-XVAR", "TC-MULTI", "TC-MISS"]
    summary = {}
    for f in fams:
        fc = [c for c in cases if c["family"] == f]
        passes = [c for c in fc if c["verdict"] == "PASS"]
        fails = [c for c in fc if c["verdict"] != "PASS"]
        summary[f] = {
            "n": len(fc),
            "pass": len(passes), "fail": len(fails),
            "pass_rate_pct": round(100.0 * len(passes) / len(fc), 2) if fc else 0.0,
            "fail_reason_dist": dict(Counter(
                c["verdict"].split(":")[1].split(";")[0] for c in fails).most_common()),
            "oracle_reason_dist": dict(Counter(c["oracle"]["reason"] for c in fc).most_common(8)),
        }
    fails_all = [c for c in cases if c["verdict"] != "PASS"]
    bug_families = {
        "R07_bypasses_R05": [c["tc_id"] for c in fails_all
                             if "alias_exact_bypasses_blacklist" in c["verdict"]],
        "blacklist_hit_but_accepted": [c["tc_id"] for c in fails_all
                                       if "blacklist_hit_but_accepted" in c["verdict"]],
        "safe_negative_over_blocked": [
            c["tc_id"] for c in fails_all
            if c["family"] == "TC-POS" and c["source"].startswith("blacklist_boundary")],
        "expected_rule_unreachable": [
            c["tc_id"] for c in fails_all
            if "must_hit" in c["verdict"] or "reason_in" in c["verdict"]],
    }

    out = {
        "task": A.TASK,
        "schema_version": "v1.0",
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "engine": eng_meta,
        "blacklist": {"file": A.BL_FINAL, "rules_total": len(rules),
                      "rule_ids": sorted(rules.keys())},
        "engine_guard": guard,
        "seed": A.SEED,
        "readonly_declaration": "只读；无 zhiji API 调用；不修改任何输入文件",
        "how_to_use": [
            "1) 加载引擎：audit_kit.load_engine()（exec build_alias_library.py 1..655 行）",
            "2) 对每条用例执行 audit_kit.engine_decide(M, left, right) 与 "
            "audit_kit.black_hit(M, left, right)",
            "3) 与 expectation 逐字段比较；oracle.accept/review/reason/must_hit 任一不符即 FAIL",
            "4) FAIL 用例是 V86 的缺陷回归项，修复后必须全部转 PASS",
            "5) verdict 字段以 % 分隔：PASS / FAIL:<失败字段明细>",
        ],
        "verdict_semantics": {
            "PASS": "oracle 满足 expectation 的全部字段",
            "FAIL:accept": "放行/拦截方向与期望相反",
            "FAIL:review": "硬拦截 vs 降级复核 三态不一致",
            "FAIL:reason": "判定原因与期望不同",
            "FAIL:reason_in": "判定原因不在期望集合内",
            "FAIL:must_hit": "期望的黑名单规则未命中",
            "FAIL:must_not_hit": "期望不命中的黑名单规则实际命中",
            "FAIL:blacklist_hit_but_accepted": "黑名单命中却被放行（R-07 绕过 R-05）",
            "FAIL:alias_exact_bypasses_blacklist": "alias_exact 短路与黑名单命中并存",
        },
        "family_definitions": {
            "TC-POS": "正向同义：引擎应自动放行（含 alias_exact 与边界安全负向样例）",
            "TC-NEG": "反向冲突：黑名单/口径互斥硬拦截，期望 accept=False, review=False",
            "TC-XVAR": "跨品种混淆：期望 variety_anchor_violation 或黑名单拦截",
            "TC-MULTI": "多 canon 冲突：alias_norm 指向 >1 原子键，期望不自动合并",
            "TC-MISS": "缺失别名：THS 原名 / 别名库 register_pending，期望不自动放行",
        },
        "totals": {
            "n_cases": len(cases),
            "by_family": {f: summary[f]["n"] for f in fams},
            "pass": sum(1 for c in cases if c["verdict"] == "PASS"),
            "fail": len(fails_all),
            "pass_rate_pct": round(100.0 * sum(1 for c in cases if c["verdict"] == "PASS")
                                   / len(cases), 2) if cases else 0.0,
        },
        "summary_by_family": summary,
        "defect_signature_cases": bug_families,
        "cases": cases,
    }
    A.write_json(os.path.join(CD, "alias_test_case_set.json"), out)

    print("=" * 78)
    print("T2.6 测试用例包")
    for f in fams:
        s = summary[f]
        print("  %-8s n=%-5d pass=%-5d fail=%-5d (%.2f%%)"
              % (f, s["n"], s["pass"], s["fail"], s["pass_rate_pct"]))
    print("  TOTAL    n=%-5d pass=%-5d fail=%-5d (%.2f%%)"
          % (len(cases), out["totals"]["pass"], out["totals"]["fail"],
             out["totals"]["pass_rate_pct"]))
    print("  缺陷签名用例:")
    for k, v in bug_families.items():
        print("    %-32s %d 例 %s" % (k, len(v), v[:6]))
    print("  失败原因分布 top8:",
          dict(Counter(c["verdict"].split(":")[1].split(";")[0] for c in fails_all).most_common(8)))
    print("=" * 78)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
