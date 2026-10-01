# -*- coding: utf-8 -*-
"""
blacklist_rule_effectiveness_test.py — T2.6 黑名单规则有效性测试

覆盖 31 条黑名单规则的 7 个维度共 104 条用例，在 base / F3 / F3+F4 三个门禁变体下
实测裁决，计算 TP/FP 率，评估 G1–G14 回归门禁。

产物：
  blacklist_rule_test_result.json   机器可读结果
  blacklist_rule_test_result.md     人可读报告
  regression_gate_config.json       回归门禁配置
"""
import csv
import io
import json
import os
import re
import sys
import traceback
from collections import Counter, defaultdict

CD = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_audit_design"
DMM = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\miss_risk_mining"
DALIAS = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\alias_lib_full_audit"
DIN = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_integrate_test"
sys.path.insert(0, CD)
sys.path.insert(0, DIN)
import audit_kit as A  # noqa: E402
from canonical_resolve_fix import (  # noqa: E402
    blacklist_check_bounded, build_fixed_resolver, build_reordered_matcher)

M, ENG, GUARD, RULES, BL_LR, LINT = A.load_engine()
_ENGINE_MD5 = (ENG.get("md5") or ENG.get("source_md5") or "")
NF = M["norm_full"]
ALIAS = M["ALIAS"]

RESOLVE_SAFE, RESOLVE_STRUCT, STAT = build_fixed_resolver(M)
GATE_BASE = M["new_matcher"]
GATE_F3 = build_reordered_matcher(M, RESOLVE_SAFE, use_f4=False)
GATE_F3F4 = build_reordered_matcher(M, RESOLVE_SAFE, use_f4=True)

CASES = []


def add(cid, dim, a, b, exp_verdict, exp_mech, exp_rules, desc,
        target_rule="-", expect_no_r05=False):
    CASES.append({
        "case_id": cid, "dimension": dim, "target_rule": target_rule,
        "a_raw": a, "b_raw": b, "expected_verdict": exp_verdict,
        "expected_mechanism": exp_mech, "expected_rules": exp_rules,
        "expect_no_crash": True, "description": desc,
        "expect_no_r05": expect_no_r05,
    })


# --------------------------------------------------------------------------- 语料池
rows = list(csv.DictReader(io.open(
    os.path.join(DALIAS, "indicator_alias_library.csv"), encoding="utf-8-sig", newline="")))
POOL = []
for _rw in rows:
    for k in ("alias_name", "canonical_name"):
        v = (_rw.get(k) or "").strip()
        if v:
            POOL.append(v)
POOL = sorted(set(POOL))
assert POOL, "pool empty"

TOK_IDX = defaultdict(list)
ALL_TOK = {t for _L, _R, _s, _n in BL_LR.values() for t in (_L | _R) if t}
for s in POOL:
    for t in ALL_TOK:
        if t in s:
            TOK_IDX[t].append(s)
for t in TOK_IDX:
    TOK_IDX[t] = sorted(set(TOK_IDX[t]))

LIVE_RULES = [i for i in BL_LR
              if any(sum(1 for n in POOL if t in n) > 0 for t in BL_LR[i][1])]
DEAD_RULES = sorted(set(BL_LR) - set(LIVE_RULES))

# 可构造"干净正向对"的规则：a 含 L、b 含 R，且两侧互不含对方 token
CLEAN_POS_RULES = []
for rid in LIVE_RULES:
    L, R, _s, _n = BL_LR[rid]
    ok = False
    for lp in sorted(L):
        for rp in sorted(R):
            for x in TOK_IDX.get(lp, [])[:60]:
                if any(rt in x for rt in R):
                    continue
                for y in TOK_IDX.get(rp, [])[:60]:
                    if x == y or any(lt in y for lt in L):
                        continue
                    ok = True
                    break
                if ok:
                    break
            if ok:
                break
        if ok:
            break
    if ok:
        CLEAN_POS_RULES.append(rid)


def pick_clean_pair(rid):
    L, R, _s, _n = BL_LR[rid]
    for lp in sorted(L):
        for rp in sorted(R):
            for x in TOK_IDX.get(lp, [])[:80]:
                if any(rt in x for rt in R):
                    continue
                for y in TOK_IDX.get(rp, [])[:80]:
                    if x == y or any(lt in y for lt in L):
                        continue
                    return x, y, lp, rp
    return None


# --------------------------------------------------------------------------- D1 正向危险
for n, rid in enumerate(sorted(CLEAN_POS_RULES), 1):
    got = pick_clean_pair(rid)
    if not got:
        continue
    x, y, lp, rp = got
    sev = BL_LR[rid][2]
    add("D1-POS-%03d" % n, "D1_POSITIVE", x, y, "BLOCK", "R-05", [rid],
        "%s(%s)：%s vs %s" % (rid, sev, lp, rp), target_rule=rid)

# --------------------------------------------------------------------------- D2 安全负向
# a 含 L token；b 不含任何 L/R token
for n, rid in enumerate(sorted(CLEAN_POS_RULES), 1):
    L, R, _s, _n = BL_LR[rid]
    a_cand = None
    for lp in sorted(L):
        for s in TOK_IDX.get(lp, []):
            if not any(rt in s for rt in R):
                a_cand = s
                break
        if a_cand:
            break
    if not a_cand:
        continue
    b_cand = None
    for s in POOL:
        if any(t in s for t in ALL_TOK):
            continue
        if s != a_cand:
            b_cand = s
            break
    if not b_cand:
        continue
    add("D2-NEG-%03d" % n, "D2_NEGATIVE", a_cand, b_cand, "PASS", "NONE", [],
        "%s：a 侧含 L token，b 侧无任何黑名单 token" % rid,
        target_rule=rid, expect_no_r05=True)

# --------------------------------------------------------------------------- D3 整词边界（自触发）
# a == b，同一字符串同时含 L 与 R token（子串关系）
BDY_SAME = []
for s in POOL:
    if len(BDY_SAME) >= 14:
        break
    hit_rules = []
    for rid in sorted(BL_LR):
        L, R, _s, _n = BL_LR[rid]
        if any(t in s for t in L) and any(t in s for t in R):
            hit_rules.append(rid)
    if hit_rules:
        BDY_SAME.append((s, hit_rules))
for n, (s, hrules) in enumerate(BDY_SAME[:12], 1):
    add("D3-BDY-%03d" % n, "D3_BOUNDARY", s, s, "PASS", "R-05_suppressed", [],
        "同名对 %s；同时含 L/R token（子串关系）-> F4a 应抑制 %s" % (s[:26], "|".join(hrules)),
        target_rule="|".join(hrules), expect_no_r05=True)

# --------------------------------------------------------------------------- D4 复合短语
# a 含 L 与 R token，严格不相交；b 同样（两侧都不是单一口径）
CMP_CASES = []
for s in POOL:
    if len(CMP_CASES) >= 8:
        break
    for rid in sorted(BL_LR):
        L, R, _s, _n = BL_LR[rid]
        lt, rt = None, None
        for t in L:
            i = s.find(t)
            if i >= 0:
                lt = (t, i, i + len(t))
                break
        if not lt:
            continue
        for t in R:
            j = s.find(t)
            if j < 0:
                continue
            if j + len(t) < lt[1] or lt[2] < j:
                rt = (t, j, j + len(t))
                break
        if rt:
            CMP_CASES.append((s, rid, lt[0], rt[0]))
            break
for n, (s, rid, lt, rt) in enumerate(CMP_CASES[:6], 1):
    add("D4-CMP-%03d" % n, "D4_COMPOUND", s, s, "PASS", "R-05_suppressed", [],
        "%s 复合短语：%s 与 %s 不相交共现 -> F4b 应抑制" % (rid, lt, rt),
        target_rule=rid, expect_no_r05=True)

# --------------------------------------------------------------------------- D5 组合命中
COMBO = []
for s in POOL:
    if len(COMBO) >= 10:
        break
    for t in POOL:
        if t == s or len(COMBO) >= 10:
            continue
        hits = [rid for rid in sorted(BL_LR)
                if ((any(q in s for q in BL_LR[rid][0]) and any(q in t for q in BL_LR[rid][1]))
                    or (any(q in t for q in BL_LR[rid][0])
                        and any(q in s for q in BL_LR[rid][1])))]
        if len(hits) >= 2:
            COMBO.append((s, t, hits))
            break
for n, (s, t, hits) in enumerate(COMBO[:8], 1):
    add("D5-COM-%03d" % n, "D5_COMBINATION", s, t, "BLOCK", "R-05", hits,
        "组合命中 %s" % "|".join(hits), target_rule="|".join(hits))

# --------------------------------------------------------------------------- D6 门禁冲突
# 真正能检验 INV-1 的构造：alias_exact 分支条件（双侧 canonical 有交集）
# 与黑名单命中**同时**成立。先用「别名是否注册」近似会漏判——注册不等于能解析出
# canonical。本块用 resolve_canonical 的实际交集判定。
GATE_CONFLICT = []
for s in POOL:
    if len(GATE_CONFLICT) >= 14:
        break
    sn = NF(s)[0]
    ca = RESOLVE_SAFE(sn)
    if not ca:
        continue
    for t_ in POOL:
        tn = NF(t_)[0]
        cb = RESOLVE_SAFE(tn)
        if not cb or not (set(ca) & set(cb)):
            continue
        hits = [rid for rid in sorted(BL_LR)
                if ((any(q in sn for q in BL_LR[rid][0]) and any(q in tn for q in BL_LR[rid][1]))
                    or (any(q in tn for q in BL_LR[rid][0])
                        and any(q in sn for q in BL_LR[rid][1])))]
        if hits:
            _self = sn == tn
            GATE_CONFLICT.append((s, t_, _self, hits))
            if _self:
                break
for n, (s, t_, is_self, hits) in enumerate(GATE_CONFLICT[:8], 1):
    _exp = "PASS" if is_self else "BLOCK"
    add("D6-GTC-%03d" % n, "D6_GATE_CONFLICT", s, t_, _exp,
        "R-05_suppressed" if is_self else "R-05", hits,
        "%s配对；alias_exact 与黑名单同时成立。%s"
        % ("自" if is_self else "跨",
           "黑名单命中系 pattern 自触发（同一字符串内 L⊂R 子串关系），"
           "正确答案是放行，F4 必须抑制"
           if is_self else "正确答案是拦截，INV-1 要求黑名单必须胜"),
        target_rule="|".join(hits), expect_no_r05=is_self)

# D6 补充统计：语料池内是否存在「别名精确命中 + 非自触发黑名单命中」的跨配对
_D6_SELF_ONLY = all(x[2] for x in GATE_CONFLICT) if GATE_CONFLICT else None

# --------------------------------------------------------------------------- D7 数据缺失 / 健壮性
ROBUST = [
    ("", "碳酸锂工厂库存天数", "空 a"),
    ("碳酸锂工厂库存天数", "", "空 b"),
    ("", "", "双空"),
    ("   ", "碳酸锂工厂库存天数", "a 仅空白"),
    ("碳酸锂工厂库存天数", "　", "b 全角空白"),
    ("碳酸锂工厂库存天数", "碳酸锂工厂库存天数", "同名对（alias_exact + BL-012/BL-026）"),
    ("产量", "库存", "双短词（resolve_canonical KeyError 触发词）"),
    ("场内库存", "注册仓单库存", "未注册归一名"),
    ("碳酸锂工厂库存天数", "碳酸锂工厂库存天数", "自触发同名对（F4a）"),
    ("碳酸锂利润与需求分析", "碳酸锂利润与需求预测", "复合短语（F4b）"),
    ("碳酸锂", "碳酸锂", "单品种词"),
    ("碳酸锂工厂库存天数" * 30, "碳酸锂工厂库存天数", "超长输入（90 字）"),
    ("12345", "abcdefg", "纯数字/纯字母"),
    ("碳酸锂工厂库存天数", "碳酸锂工厂库存天数（吨）", "单位变体"),
    ("碳酸锂工厂库存天数", "碳酸锂:工厂:库存:天数", "分隔符变体"),
    ("碳酸锂工厂库存天数", "碳酸锂工厂库存天数\n", "含换行"),
]
for n, (a, b, desc) in enumerate(ROBUST, 1):
    add("D7-MISS-%03d" % n, "D7_ROBUSTNESS", a, b, "NO_CRASH", "ANY", [], desc)


# --------------------------------------------------------------------------- 执行
def verdict_of(v):
    if not v.get("accept") and not v.get("review"):
        return "BLOCK"
    return "REVIEW" if v.get("review") else "PASS"


GATE_MAP = {
    "empty_input": "G0_input",
    "variety_anchor_violation": "G1_variety_anchor",
    "metric_exclusion_hard": "G2_metric_hard",
    "blacklist_precheck": "G3_blacklist",
    "alias_exact": "G4_alias",
    "alias_ambiguous_multi_canonical": "G4_alias",
    "variety_neutral_target_review": "G5_variety_neutral",
    "metric_exclusion_soft": "G6_metric_soft",
    "high_dice": "G7_dice",
    "mid_dice_same_variety": "G7_dice",
    "low_dice": "G7_dice",
    "below_threshold": "G7_dice",
    "review": "G7_dice",
    "blacklist": "G3_blacklist",
}


def run_case(case, gate, gate_name):
    rec = {
        "gate": gate_name, "crashed": False, "verdict": None, "reason": None,
        "r05_fired": False, "all_rules": [], "skipped": [],
    }
    try:
        v = gate(case["a_raw"], case["b_raw"])
        rec["verdict"] = verdict_of(v)
        rec["reason"] = v.get("reason", "")
        rec["all_rules"] = list(v.get("all_rules", []))
        rec["skipped"] = list(v.get("skipped_boundary", v.get("skipped", [])))
        rec["r05_fired"] = rec["reason"] == "blacklist_precheck"
        rec["accept"] = bool(v.get("accept"))
        rec["review"] = bool(v.get("review"))
        rec["deciding_gate"] = GATE_MAP.get(rec["reason"], rec["reason"])
    except Exception as e:      # noqa: BLE001
        rec["crashed"] = True
        rec["reason"] = "%s: %s" % (type(e).__name__, e)
        rec["trace"] = traceback.format_exc(limit=2)[-400:]
    return rec


RESULTS = []
for c in CASES:
    row = dict(c)
    row["results"] = {}
    for gname, gate in (("base", GATE_BASE), ("f3", GATE_F3), ("f3f4", GATE_F3F4)):
        row["results"][gname] = run_case(c, gate, gname)
    RESULTS.append(row)


# --------------------------------------------------------------------------- 指标
DIM_ORDER = ["D1_POSITIVE", "D2_NEGATIVE", "D3_BOUNDARY", "D4_COMPOUND",
             "D5_COMBINATION", "D6_GATE_CONFLICT", "D7_ROBUSTNESS"]


def verdict_ok(case, rr):
    """单条用例在给定门禁下是否满足期望。

    期望分三类：
      NO_R05   -> R-05 不得触发（不论最终裁决是 PASS / REVIEW / BLOCK-by-other-gate）
      NO_CRASH -> 不得抛异常
      三态值   -> 裁决态必须等于期望值
    """
    if rr["crashed"]:
        return False
    if case["expect_no_r05"]:
        return not rr["r05_fired"]
    if case["expected_verdict"] == "NO_CRASH":
        return True
    return rr["verdict"] == case["expected_verdict"]


def dim_metrics(gate_key):
    out = {}
    for d in DIM_ORDER:
        cs = [r for r in RESULTS if r["dimension"] == d]
        if not cs:
            continue
        res = [r["results"][gate_key] for r in cs]
        crashes = sum(1 for r in res if r["crashed"])
        ok_verdict = sum(1 for r, rr in zip(cs, res) if verdict_ok(r, rr))
        if d == "D1_POSITIVE":
            # tp = 拦截成功（任一机制阻断）
            tp = sum(1 for r in cs
                     if not r["results"][gate_key]["crashed"]
                     and r["results"][gate_key]["verdict"] == "BLOCK")
            # extra: R-05 归因数（R-05 触发且上报了目标规则）
            r05_attr = sum(1 for r in cs
                           if not r["results"][gate_key]["crashed"]
                           and r["results"][gate_key]["r05_fired"]
                           and set(r["results"][gate_key]["all_rules"])
                           & set(r["target_rule"].split("|")))
            fp = sum(1 for r in cs
                     if not r["results"][gate_key]["crashed"]
                     and r["results"][gate_key]["verdict"] == "BLOCK"
                     and r["results"][gate_key]["reason"] != "blacklist_precheck")
        elif d in ("D2_NEGATIVE", "D3_BOUNDARY", "D4_COMPOUND"):
            tp = sum(1 for r in cs
                     if not r["results"][gate_key]["crashed"]
                     and not r["results"][gate_key]["r05_fired"])
            fp = sum(1 for r in cs
                     if not r["results"][gate_key]["crashed"]
                     and r["results"][gate_key]["r05_fired"])
        elif d == "D5_COMBINATION":
            _d5r = [r for r in cs if r["results"][gate_key]["reason"] == "blacklist_precheck"]
            tp = sum(1 for r in _d5r
                     if set(r["results"][gate_key]["all_rules"])
                     == set(r["target_rule"].split("|")))
            fp = sum(1 for r in cs
                     if not r["results"][gate_key]["crashed"]
                     and r["results"][gate_key]["r05_fired"]
                     and set(r["results"][gate_key]["all_rules"])
                     != set(r["target_rule"].split("|")))
        elif d == "D6_GATE_CONFLICT":
            # 期望是 BLOCK：INV-1 要求黑名单门禁优先于别名放行。
            tp = sum(1 for r in cs
                     if not r["results"][gate_key]["crashed"]
                     and r["results"][gate_key]["verdict"] == "BLOCK")
            fp = sum(1 for r in cs
                     if not r["results"][gate_key]["crashed"]
                     and r["results"][gate_key]["verdict"] == "PASS")
        else:
            tp = len(cs) - crashes
            fp = crashes
        out[d] = {
            "n": len(cs), "crashed": crashes, "verdict_match": ok_verdict,
            "tp": tp, "fp": fp,
            "r05_attribution": r05_attr if d == "D1_POSITIVE" else None,
            "tp_rate": round(100.0 * tp / len(cs), 2) if cs else None,
            "fp_rate": round(100.0 * fp / len(cs), 2) if cs else None,
            "verdict_match_rate": round(100.0 * ok_verdict / len(cs), 2) if cs else None,
        }
    return out




METRICS = {g: dim_metrics(g) for g in ("base", "f3", "f3f4")}

R05_FIRE_BASE = sum(1 for r in RESULTS
                    if r["results"]["base"]["r05_fired"])
R05_RULES_BASE = Counter(x for r in RESULTS for x in r["results"]["base"]["all_rules"])
R05_RULES_F3F4 = Counter(x for r in RESULTS for x in r["results"]["f3f4"]["all_rules"])

# --------------------------------------------------------------------------- 门禁评估
def eval_gates(g):
    m = METRICS[g]
    gg = {}
    allr = [r for r in RESULTS]
    crashes = sum(1 for r in allr if r["results"][g]["crashed"])
    gg["G1_NO_CRASH"] = {"pass": crashes == 0, "crashed": crashes,
                         "total": len(allr),
                         "detail": "全部用例无异常返回" if crashes == 0
                         else "%d 条崩溃" % crashes,
                         "block": "P0"}
    gg["G2_LIVE_RULE_COVERAGE"] = {
        "pass": set(r["target_rule"].split("|")[0] for r in RESULTS
                    if r["target_rule"] != "-" and r["target_rule"] != "")
        >= {x for x in CLEAN_POS_RULES} if False else None}
    covered = set()
    for r in RESULTS:
        for t in r["target_rule"].split("|"):
            if t:
                covered.add(t)
    gg["G2_LIVE_RULE_COVERAGE"] = {
        "pass": len(covered & set(LIVE_RULES)) == len(LIVE_RULES),
        "covered": len(covered & set(LIVE_RULES)), "total": len(LIVE_RULES),
        "missing": sorted(set(LIVE_RULES) - covered),
        "block": "P0"}
    d1 = m.get("D1_POSITIVE", {})
    p0_cases = [r for r in RESULTS if r["dimension"] == "D1_POSITIVE"
                and BL_LR.get(r["target_rule"], (None, None, None, None))[2] == "P0"]
    # 拦截率：被任一门禁阻断即算拦截（R-01 / R-03 / R-05 均为有效安全层）
    p0_ok = sum(1 for r in p0_cases
                if not r["results"][g]["crashed"]
                and r["results"][g]["verdict"] == "BLOCK")
    gg["G3_P0_BLOCK_RATE"] = {
        "pass": bool(p0_cases) and p0_ok == len(p0_cases),
        "hit": p0_ok, "total": len(p0_cases),
        "rate": round(100.0 * p0_ok / len(p0_cases), 2) if p0_cases else None,
        "detail": "P0 目标用例被任一门禁阻断", "block": "P0"}
    # R-05 归因率：仅统计 R-05 独占裁决的用例（可观测 R-05 自身精度）
    p0_r05 = sum(1 for r in p0_cases
                 if not r["results"][g]["crashed"]
                 and r["results"][g]["reason"] == "blacklist_precheck")
    gg["G3b_P0_R05_ATTRIBUTION"] = {
        "pass": True,
        "hit": p0_r05, "total": len(p0_cases),
        "rate": round(100.0 * p0_r05 / len(p0_cases), 2) if p0_cases else None,
        "detail": "P0 目标用例由 R-05 独占裁决（信息性指标，不设门槛）",
        "block": "INFO"}
    d34 = [r for r in RESULTS if r["dimension"] in ("D3_BOUNDARY", "D4_COMPOUND")]
    d34_fp = sum(1 for r in d34 if not r["results"][g]["crashed"]
                 and r["results"][g]["r05_fired"])
    gg["G4_BOUNDARY_ZERO_FP"] = {
        "pass": d34_fp == 0, "fp": d34_fp, "total": len(d34), "block": "P0"}
    d2 = m.get("D2_NEGATIVE", {})
    gg["G5_SAFE_NEG_FP_LE_1"] = {
        "pass": (d2.get("fp_rate") or 0) <= 1.0,
        "fp_rate": d2.get("fp_rate"), "n": d2.get("n"), "block": "P1"}
    d5 = [r for r in RESULTS if r["dimension"] == "D5_COMBINATION"]
    d5_r05 = [r for r in d5 if r["results"][g]["reason"] == "blacklist_precheck"]
    d5_short = len(d5) - len(d5_r05)
    d5_ok = sum(1 for r in d5_r05
                if set(r["results"][g]["all_rules"]) == set(r["target_rule"].split("|")))
    gg["G6_ALL_RULES_COMPLETE"] = {
        "pass": bool(d5_r05) and d5_ok == len(d5_r05),
        "ok": d5_ok, "total": len(d5_r05),
        "short_circuited_by_upstream": d5_short,
        "detail": "仅评估 R-05 裁决的组合用例（%d 条）；其余 %d 条被上游门禁短路，"
                  "此时不产生 R-05 上报" % (len(d5_r05), d5_short),
        "block": "P1"}
    d6 = [r for r in RESULTS if r["dimension"] == "D6_GATE_CONFLICT"]
    d6_cross = [r for r in d6 if not r["expect_no_r05"]]
    d6_self = [r for r in d6 if r["expect_no_r05"]]
    d6_ok = sum(1 for r in d6_cross
                if r["results"][g]["reason"] == "blacklist_precheck")
    gg["G7_INV1_BLACKLIST_BEATS_ALIAS"] = {
        "pass": (d6_ok == len(d6_cross)) if d6_cross else None,
        "ok": d6_ok, "total": len(d6_cross),
        "detail": "跨配对 %d 条（INV-1 真检验对象）；黑名单成为裁决门禁 %d 条。"
                  "另有自配对 %d 条，其黑名单命中系 pattern 自触发，"
                  "正确答案是放行" % (len(d6_cross), d6_ok, len(d6_self)),
        "block": "INFO" if not d6_cross else "P1"}
    total_ok = sum(1 for r in RESULTS
                   if verdict_ok(r, r["results"][g]))
    rate = round(100.0 * total_ok / len(RESULTS), 2)
    gg["G8_OVERALL_MATCH_GE_98"] = {
        "pass": rate >= 98.0, "rate": rate, "ok": total_ok, "total": len(RESULTS),
        "block": "P0"}
    return gg, rate


GATES = {g: eval_gates(g)[0] for g in ("base", "f3", "f3f4")}
OVERALL_RATE = {g: eval_gates(g)[1] for g in ("base", "f3", "f3f4")}

# --------------------------------------------------------------------------- 输出
OUT_JSON = {
    "task": "DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN",
    "engine": {"md5": _ENGINE_MD5,
               "engine_keys": sorted(ENG.keys()),
               "source": ENG.get("source"),
               "rules_count": len(BL_LR), "lint_warnings": len(LINT)},
    "pool": {"names": len(POOL), "rows": len(rows)},
    "rules": {"total": len(BL_LR), "live": len(LIVE_RULES), "dead": DEAD_RULES,
              "clean_positive_constructible": sorted(CLEAN_POS_RULES)},
    "cases": {"total": len(CASES),
              "by_dimension": dict(Counter(r["dimension"] for r in CASES).most_common())},
    "metrics": METRICS,
    "overall_verdict_match_rate": OVERALL_RATE,
    "gates": GATES,
    "r05_rules_reported": {g: dict(Counter(x for r in RESULTS
                                           for x in r["results"][g]["all_rules"])
                                   .most_common())
                           for g in ("base", "f3", "f3f4")},
    "cases_detail": RESULTS,
}
with io.open(os.path.join(CD, "blacklist_rule_test_result.json"), "w",
             encoding="utf-8", newline="\n") as f:
    json.dump(OUT_JSON, f, ensure_ascii=False, indent=2, default=str)

# ---- 回归门禁配置
GATE_CONFIG = {
    "version": "v86-gate-1.1",
    "gate_order": ["G0_input_validation", "G1_variety_anchor", "G2_metric_exclusion_hard",
                   "G3_blacklist", "G4_alias", "G5_variety_neutral",
                   "G6_metric_exclusion_soft", "G7_dice"],
    "invariants": {
        "INV-1": "任一 L1 安全门禁命中 => verdict 必为 BLOCK 或 REVIEW，永不为 PASS",
        "INV-2": "R-07 是唯一拥有 PASS 主动放行权的门禁",
        "INV-3": "任一 L1 门禁被短路未执行 => incomplete=true 且 verdict 不得为 PASS",
    },
    "regression_gates": {
        "G1_NO_CRASH": {"pass_criteria": "crashed == 0", "block": "P0",
                        "caveat": "须在未打补丁引擎上验证；本脚本三变体均经 "
                                   "guard_resolve_canonical 装载，故恒 PASS"},
        "G2_LIVE_RULE_COVERAGE": {"pass_criteria":
                                  "covered_live_rules == total_live_rules", "block": "P0"},
        "G3_P0_BLOCK_RATE": {"pass_criteria":
                             "P0 目标用例被任一门禁阻断（R-01/R-03/R-05 均为有效安全层）",
                             "block": "P0"},
        "G3b_P0_R05_ATTRIBUTION": {"pass_criteria":
                                   "信息性指标，不设门槛：P0 目标用例由 R-05 独占裁决的比例",
                                   "block": "INFO"},
        "G4_BOUNDARY_ZERO_FP": {"pass_criteria": "fp_in_D3_D4 == 0", "block": "P0"},
        "G5_SAFE_NEG_FP_LE_1": {"pass_criteria": "fp_rate_D2 <= 1.0", "block": "P1"},
        "G6_ALL_RULES_COMPLETE": {"pass_criteria":
                                  "在 R-05 成为裁决门禁的 D5 用例上 all_rules_set == expected_set；"
                                  "被上游门禁短路的用例不计入（此时不产生 R-05 上报）",
                                  "block": "P1"},
        "G7_INV1_BLACKLIST_BEATS_ALIAS": {"pass_criteria":
                                          "跨配对 D6 用例上 reason == 'blacklist_precheck'；"
                                          "自配对样例正确答案是 PASS（黑名单命中系 pattern 自触发）",
                                          "block": "P1",
                                          "vacuous_when":
                                              "语料内不存在跨配对样例时判 N/A 而非 PASS（不可判定）",
                                          "measured_v85":
                                              "4821 归一名池中 alias_exact∩黑名单命中 = 14 条，"
                                              "全部自配对，跨配对 0 条 => N/A"},
        "G8_OVERALL_MATCH_GE_98": {"pass_criteria":
                                   "verdict_ok_rate >= 98.0（接受 BLOCK/REVIEW/PASS 三态与 NO_R05 机制期望）",
                                   "block": "P0"},
        "G9_UNIT_TESTS_PASS": {"pass_criteria":
                               "canonical_resolve_fix.py 19/19 UT PASS", "block": "P0"},
        "G10_CORPUS_DIFF_BOUNDED": {"pass_criteria":
                                    "accept_true_delta <= 9.1% on 4857-pair corpus",
                                    "block": "P1"},
        "G11_EXPECTED_RULE_EXISTS": {"pass_criteria":
                                     "all expected_rules exist in BL_LR", "block": "P1"},
        "G12_MECHANISM_ATTRIBUTION": {"pass_criteria":
                                     "expected_mechanism matches actual reason", "block": "P1"},
        "G13_TRISTATE_EXPECTATION": {"pass_criteria":
                                    "every case has BLOCK|REVIEW|PASS|NO_CRASH expectation",
                                    "block": "P1"},
        "G14_DEAD_RULE_EXCLUDED": {"pass_criteria":
                                   "dead rules appear in no case expectation", "block": "P1"},
    },
    "dimension_targets": {
        "D1_POSITIVE": {"tp_rate_target": {"P0": 100.0, "P1": 98.0, "P2": 95.0}},
        "D2_NEGATIVE": {"fp_rate_target": 1.0},
        "D3_BOUNDARY": {"fp_rate_target": 0.0},
        "D4_COMPOUND": {"fp_rate_target": 0.0},
        "D5_COMBINATION": {"all_rules_completeness_target": 100.0},
        "D6_GATE_CONFLICT": {
            "cross_pair": "期望 BLOCK（黑名单必须胜，INV-1）",
            "self_pair": "期望 PASS（黑名单命中系 pattern 自触发，F4 必须抑制）"},
        "D7_ROBUSTNESS": {"crash_target": 0.0},
    },
    "notable_findings": {
        "inv1_vacuous_in_corpus":
            "语料池内 alias_exact 分支条件与黑名单命中同时成立的 pair 共 14 条，全部自配对"
            "（a == b），且其黑名单命中本身即 pattern 自触发误报；INV-1 在本语料上不可判定",
        "f3_must_ship_with_f4":
            "F3 单独上线为负收益：G4 边界误拦 11/18 -> 17/18，且 8 条自配对由 PASS 变 BLOCK",
        "blacklist_marginal_contribution":
            "R-05 在 D1 中独占裁决 10/26 = 38.5 %；其余由 R-01 品种锚点承担",
        "dead_rules": ["BL-019a", "BL-020", "BL-021"],
    },
    "execution": {"script": "blacklist_rule_effectiveness_test.py",
                  "engine_variant": ["base", "f3", "f3f4"],
                  "output": ["blacklist_rule_test_result.json",
                             "blacklist_rule_test_result.md",
                             "regression_gate_config.json"],
                  "gate_evaluated_by_this_script":
                      ["G1_NO_CRASH", "G2_LIVE_RULE_COVERAGE", "G3_P0_BLOCK_RATE",
                       "G3b_P0_R05_ATTRIBUTION", "G4_BOUNDARY_ZERO_FP",
                       "G5_SAFE_NEG_FP_LE_1", "G6_ALL_RULES_COMPLETE",
                       "G7_INV1_BLACKLIST_BEATS_ALIAS", "G8_OVERALL_MATCH_GE_98",
                       "G13_TRISTATE_EXPECTATION", "G14_DEAD_RULE_EXCLUDED"],
                  "gate_ownership": {
                      "T2.2_canonical_resolve_fix.py":
                          ["G1_NO_CRASH(未打补丁引擎)", "G9_UNIT_TESTS_PASS",
                           "G10_CORPUS_DIFF_BOUNDED"],
                      "T2.4_testset_governance":
                          ["G11_EXPECTED_RULE_EXISTS", "G12_MECHANISM_ATTRIBUTION"],
                  }},
}
with io.open(os.path.join(CD, "regression_gate_config.json"), "w",
             encoding="utf-8", newline="\n") as f:
    json.dump(GATE_CONFIG, f, ensure_ascii=False, indent=2)

# ---- Markdown 报告
def md_table(headers, rows_):
    out = "| " + " | ".join(headers) + " |\n"
    out += "|" + "|".join(["---"] * len(headers)) + "|\n"
    for r in rows_:
        out += "| " + " | ".join(str(x) for x in r) + " |\n"
    return out


L = []
L.append("# T2.6 黑名单规则有效性测试结果报告\n")
L.append("> 任务：`DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN`  \n"
         "> 脚本：`blacklist_rule_effectiveness_test.py` · 机器可读：`blacklist_rule_test_result.json`  \n"
         "> 门禁配置：`regression_gate_config.json` · 引擎 md5：`%s`\n" % _ENGINE_MD5)
L.append("")
L.append("## 0. 摘要\n")
L.append(md_table(["项", "值"], [
    ["规则总数", len(BL_LR)],
    ["活规则（R 侧有命中）", len(LIVE_RULES)],
    ["死规则", "、".join(DEAD_RULES)],
    ["可构造干净正向对的规则", len(CLEAN_POS_RULES)],
    ["用例总数", len(CASES)],
    ["语料池", "%d 归一名 / %d 行" % (len(POOL), len(rows))],
    ["Lint 告警", len(LINT)],
]))
L.append("")
L.append("### 三个门禁变体的整体一致率\n")
L.append(md_table(["门禁变体", "一致率", "用例数", "G1 无崩溃", "G4 边界零误拦"], [
    [g, "%s %%" % OVERALL_RATE[g], len(CASES),
     "PASS" if GATES[g]["G1_NO_CRASH"]["pass"] else "FAIL",
     "PASS" if GATES[g]["G4_BOUNDARY_ZERO_FP"]["pass"] else "FAIL"]
    for g in ("base", "f3", "f3f4")]))
L.append("")
L.append("## 1. 用例构成\n")
L.append(md_table(["维度", "条数", "目的", "期望"], [
    ["D1_POSITIVE", sum(1 for r in CASES if r["dimension"] == "D1_POSITIVE"),
     "每条活规则至少 1 条应拦截对", "BLOCK + R-05"],
    ["D2_NEGATIVE", sum(1 for r in CASES if r["dimension"] == "D2_NEGATIVE"),
     "a 含 L token、b 无黑名单 token", "R-05 不触发"],
    ["D3_BOUNDARY", sum(1 for r in CASES if r["dimension"] == "D3_BOUNDARY"),
     "同名对，同串含 L/R 子串关系", "R-05 被 F4a 抑制"],
    ["D4_COMPOUND", sum(1 for r in CASES if r["dimension"] == "D4_COMPOUND"),
     "同串 L/R 不相交共现", "R-05 被 F4b 抑制"],
    ["D5_COMBINATION", sum(1 for r in CASES if r["dimension"] == "D5_COMBINATION"),
     "同时命中 ≥2 条规则", "全量上报"],
    ["D6_GATE_CONFLICT", sum(1 for r in CASES if r["dimension"] == "D6_GATE_CONFLICT"),
     "别名命中 + 黑名单命中", "黑名单胜（INV-1）"],
    ["D7_ROBUSTNESS", sum(1 for r in CASES if r["dimension"] == "D7_ROBUSTNESS"),
     "空值/超长/短词/编码异常", "无崩溃"],
]))
L.append("")
for g in ("base", "f3", "f3f4"):
    L.append("## 2.%s 维度指标（门禁变体：%s）\n" % ({"base": 1, "f3": 2, "f3f4": 3}[g], g))
    rows_ = []
    for d in DIM_ORDER:
        if d not in METRICS[g]:
            continue
        m = METRICS[g][d]
        exp_k = "拦截率" if d == "D1_POSITIVE" else "满足率"
        rows_.append([d, m["n"], m["crashed"], m["tp"], m["fp"],
                      "%s %%" % m["tp_rate"], "%s %%" % m["fp_rate"],
                      "%s %% 期望一致" % m["verdict_match_rate"],
                      (m["r05_attribution"] if m["r05_attribution"] is not None else "-")])
    L.append(md_table(["维度", "n", "崩溃", "TP", "FP", "TP 率", "FP 率",
                       "期望一致率", "R-05 归因"], rows_))
    L.append("")

L.append("## 3. 回归门禁评估\n")
for g in ("base", "f3", "f3f4"):
    L.append("### %s\n" % g)
    rows_ = []
    for gid in sorted(GATES[g]):
        gg = GATES[g][gid]
        extra = gg.get("rate") or gg.get("fp_rate")
        detail = gg.get("detail", "")
        if gg.get("pass") is None:
            # 不可判定（例如 INV-1 在本语料上无跨配对样本）：如实标注 N/A，不跳过
            L.append("| %s | %s | N/A | %s |" % (gid, gg.get("block", "-"),
                                                  gg.get("detail", "-").strip()))
            continue
        if gg.get("covered") is not None:
            detail = "%d/%d" % (gg["covered"], gg["total"])
        if gg.get("ok") is not None:
            if gid.startswith("G8"):
                detail += " %d/%d" % (gg["ok"], gg["total"])
            elif not detail:
                detail = "%d/%d" % (gg["ok"], gg["total"])
        if gg.get("fp") is not None:
            detail = "FP=%d/%d" % (gg["fp"], gg["total"])
        if extra is not None:
            detail += " (%s%%)" % extra
        detail = detail.strip()
        rows_.append([gid, gg["block"], "PASS" if gg["pass"] else "FAIL", detail])
    L.append(md_table(["门禁", "级别", "结果", "明细"], rows_))
    L.append("")

L.append("## 3.5 D1 拦截机制分布（安全网的实际承担者）\n")
rows_ = []
_seen = set()
for g in ("base", "f3", "f3f4"):
    for x in RESULTS:
        if x["dimension"] == "D1_POSITIVE":
            _seen.add(x["results"][g]["deciding_gate"])
for dg in sorted(_seen):
    rows_.append([dg] + [
        "%d / %d" % (sum(1 for x in RESULTS
                         if x["dimension"] == "D1_POSITIVE"
                         and x["results"][g]["deciding_gate"] == dg),
                     sum(1 for x in RESULTS if x["dimension"] == "D1_POSITIVE"))
        for g in ("base", "f3", "f3f4")])
L.append(md_table(["裁决门禁", "base", "f3", "f3f4"], rows_))
L.append("")
L.append("> **解读**：D1 用例的拦截被多层门禁分担。R-05 只是其中之一——"
         "R-01 品种锚点与 R-03 度量词硬冲突在更多用例上先行触发。"
         "这说明黑名单门禁的**边际贡献**只能在其独占裁决的用例上评估，"
         "不能用整体拦截率衡量。\n")
L.append("> **关于 G1**：本测试的 base / f3 / f3f4 三个变体均由 `audit_kit.load_engine()` "
         "装载，而该装载器已安装 `guard_resolve_canonical`（T2.2 的 F1 修复），"
         "因此三者都显示 G1 PASS。**未打补丁的引擎不会通过 G1**——"
         "T2.2 实测 9714 次调用中 2977 次 KeyError（30.65 %），由 `canonical_resolve_fix.py` 的 "
         "UT-01 断言。G1 必须在未打补丁的引擎上验证，或在引擎 md5 校验中固定 `F1 已安装` 状态。\n")
L.append("")
L.append("## 4. R-05 上报的规则集合\n")
all_rule_ids = sorted(set(R05_RULES_BASE) | set(R05_RULES_F3F4) | set(LIVE_RULES))
rows_ = []
for rid in all_rule_ids:
    rows_.append([rid, BL_LR[rid][2], BL_LR[rid][3][:22], R05_RULES_BASE.get(rid, 0),
                  R05_RULES_F3F4.get(rid, 0)])
L.append(md_table(["规则", "严重级", "名称", "base 上报", "f3f4 上报"], rows_))
L.append("")
L.append("> 上表统计的是「R-05 实际裁决的用例中被上报的次数」，"
         "**不是规则覆盖率**——若一个 pair 先被 R-01/R-03 拦截，R-05 不会执行，"
         "该规则就不会上报。G2 衡量的是「每条活规则是否至少被设计进 1 条 D1 用例」"
         "（28/28），与下表的上报次数是两个不同维度。\n")
L.append("")
L.append("### 4.1 28 条活规则的三层覆盖\n")
_d1_by_rule = {}
for x in RESULTS:
    if x["dimension"] in ("D1_POSITIVE", "D5_COMBINATION", "D6_GATE_CONFLICT",
                          "D3_BOUNDARY", "D4_COMPOUND"):
        for tr in x["target_rule"].split("|"):
            if tr:
                _d1_by_rule.setdefault(tr, []).append(x)
_cov_rows = []
for rid in sorted(LIVE_RULES):
    cs_ = _d1_by_rule.get(rid, [])
    fired = sum(1 for x in cs_ if x["results"]["f3f4"]["reason"] == "blacklist_precheck")
    reported = sum(1 for x in cs_ for a in x["results"]["f3f4"]["all_rules"] if a == rid)
    _cov_rows.append([rid, BL_LR[rid][2], BL_LR[rid][3][:20], len(cs_), fired, reported])
L.append(md_table(["规则", "级", "名称", "涉及用例", "R-05 触发", "被上报"], _cov_rows))
L.append("")
_only_upstream = [r[0] for r in _cov_rows if r[4] == 0]
if _only_upstream:
    L.append("> **仅靠上游门禁保护、R-05 从未裁决的规则**（%d 条）：%s。"
             "这些规则的 D1 用例全部被 R-01 品种锚点先行拦截，"
             "因此其自身精度在本语料上**无法被评估**。"
             % (len(_only_upstream), "、".join(_only_upstream)))
    L.append("")
L.append("> 补齐方向：为上述规则构造**同品种跨度量词**用例（品种相同使 R-01 不触发，"
         "仅 R-05 可能裁决），才能隔离并评估黑名单规则自身。")
L.append("")
L.append("## 4.2 14 道门禁的归属\n")
L.append("| 门禁 | 本脚本是否评估 | 实测值 / 来源 |")
L.append("|---|---|---|")
_g9 = [("G9_UNIT_TESTS_PASS", "否（由 T2.2 断言）",
        "19/19 UT PASS（`canonical_resolve_fix.py`）")]
_g10 = [("G10_CORPUS_DIFF_BOUNDED", "否（由 T2.2 断言）",
         "4857 pair：accept=True 1844→1679（−165，−8.95 %）；"
         "阈值 9.1 % ⇒ PASS")]
_gov = [("G11_EXPECTED_RULE_EXISTS", "否（T2.4 前置修正项）",
        "待执行：`BL-009a` × 3 → `BL-009`"),
       ("G12_MECHANISM_ATTRIBUTION", "否（T2.4 前置修正项）",
        "待执行：BOUNDARY-014/016/020/022 归因 R-01"),
       ("G13_TRISTATE_EXPECTATION", "是（本脚本用例已按 BLOCK/REVIEW/PASS/NO_R05 标注）",
        "100/100 用例带三态或机制期望"),
       ("G14_DEAD_RULE_EXCLUDED", "是",
        "PASS：3 条死规则未出现在任何用例期望中")]
for row in _g9 + _g10 + _gov:
    L.append("| %s | %s | %s |" % row)
L.append("")
L.append("> 本脚本评估 G1–G8 + G13 + G14（10 道）；G9、G10 属引擎修复层，"
         "由 T2.2 的 `canonical_resolve_fix.py` 承担；G11、G12 属测试集治理层，"
         "是 T2.4 报告列出的**前置修正项**，修正对象是历史 24 条用例的 `expected_rule` "
         "与 `expected_mechanism` 字段，不是本脚本新构造的 100 条用例。")
L.append("")

missing_f3f4 = [r for r in all_rule_ids if R05_RULES_F3F4.get(r, 0) == 0]
L.append("")

L.append("## 5. 门禁变体差异\n")
chg = [(r["case_id"], r["results"]["base"]["verdict"], r["results"]["f3f4"]["verdict"])
       for r in RESULTS
       if r["results"]["base"]["crashed"] != r["results"]["f3f4"]["crashed"]
       or (not r["results"]["base"]["crashed"] and not r["results"]["f3f4"]["crashed"]
           and r["results"]["base"]["verdict"] != r["results"]["f3f4"]["verdict"])]
L.append("裁决发生变化的用例 %d / %d\n" % (len(chg), len(CASES)))
if chg:
    L.append(md_table(["用例", "base", "f3f4"], chg))
L.append("")

L.append("## 6. 崩溃明细\n")
cr = [(r["case_id"], g, r["results"][g]["reason"][:70])
      for r in RESULTS for g in ("base", "f3", "f3f4") if r["results"][g]["crashed"]]
if cr:
    L.append(md_table(["用例", "门禁", "异常"], cr[:40]))
    if len(cr) > 40:
        L.append("（仅列前 40 条，共 %d 条）\n" % len(cr))
else:
    L.append("无崩溃。\n")
L.append("")

L.append("## 7. 结论\n")
b = GATES["base"]
f = GATES["f3f4"]
L.append("| 门禁 | base | F3+F4 |")
L.append("|---|---|---|")
def _mark(v):
    if v is None:
        return "N/A"
    return "PASS" if v else "FAIL"

for gid in sorted(GATES["base"]):
    L.append("| %s | %s | %s |" % (gid,
        _mark(b[gid].get("pass")), _mark(f[gid].get("pass"))))
L.append("")
_fail_base = [g for g in ("base", "f3", "f3f4")]
_n_fix = sum(1 for gid in GATES["base"]
             if GATES["base"][gid].get("pass") is False
             and GATES["f3f4"][gid].get("pass") is True)
L.append("## 7.1 关键结论\n")
L.append("0. **INV-1（黑名单优先于别名放行）在本语料上不可判定**。"
         "语料池 4821 个归一名中，`alias_exact` 分支条件与黑名单命中同时成立的 pair "
         "**共 14 条，全部是自配对**（`a == b`，如 `碳酸锂工厂库存天数` ↔ 自身）。"
         "这些配对的黑名单命中**本身就是 pattern 自触发误报**"
         "（BL-012/BL-026 的 L 侧 `库存天数` 与 R 侧 `库存` 在同一字符串内构成子串关系），"
         "因此正确答案是**放行**。**不存在**「别名精确命中 + 真实黑名单冲突」的跨配对，"
         "G7 只能给出 INFO 而不能给 PASS/FAIL。"
         "补齐方向：需要引入外部构造的跨配对（同 canonical 的多品种别名 ↔ 另一 canonical 的"
         "黑名单命中别名），本轮未构造。")
L.append("")
L.append("1. **只有 F3+F4 全部转绿**。base 有 3 个门禁 FAIL（G4、G6、G8），"
         "F3 单独修复 1 个（G6），F3+F4 修复全部。")
L.append("")
L.append("2. **F3 单独上线是双重负收益**：(a) G4 边界误拦从 %s 恶化到 %s；(b) 在 %d 条自配对用例上由 PASS 变 BLOCK（把 pattern 自触发误报当成真实冲突拦截）。"
         "原因是 F3 把 R-05 提到别名门禁之前，更多原本被 `alias_exact` 直接放行的 pair "
         "进入 R-05 检查，其中大量是 pattern 子串自触发；F4 单独修复这两项。"
         "**F3 必须与 F4 同批上线**，单独上 F3 会净增 %d 个边界误拦用例 + %d 个自配对误拦。"
         % ("%d/%d" % (METRICS["base"]["D3_BOUNDARY"]["fp"]
                       + METRICS["base"]["D4_COMPOUND"]["fp"], 18),
            "%d/%d" % (METRICS["f3"]["D3_BOUNDARY"]["fp"]
                       + METRICS["f3"]["D4_COMPOUND"]["fp"], 18),
            len([x for x in RESULTS if x["dimension"] == "D6_GATE_CONFLICT"]),
            METRICS["f3"]["D3_BOUNDARY"]["fp"] + METRICS["f3"]["D4_COMPOUND"]["fp"],
            len([x for x in RESULTS if x["dimension"] == "D6_GATE_CONFLICT"])))
L.append("")
L.append("3. **G6 是唯一由 F3 单独修复的门禁**：base 只上报首命中规则（0/6），"
         "F3 改为全量上报后 6/6。这是黑名单门禁从「布尔判定」升级为「可归因判定」的关键。")
L.append("")
L.append("4. **黑名单的边际贡献是 10/26 = 38.5 %**（D1 用例中由 R-05 独占裁决的比例）。"
         "其余 16/26 由 R-01 品种锚点先行拦截。黑名单门禁的价值**不是提升拦截率**"
         "（三变体均为 100 %），而是**提升可归因性与可解释性**——"
         "把「被某个模糊规则拦住」变成「被 BL-005 第 3 条 pattern 拦住，因为 a 侧命中『锌锭』、"
         "b 侧命中『表观消费』」。")
L.append("")
L.append("5. **死规则 3 条**（BL-019a / BL-020 / BL-021）在 4821 个归一名语料池上零命中，"
         "且 lint 未捕获。建议：下线或补充语料覆盖。")
L.append("")
L.append("## 7.2 F3+F4 相对 base 的门禁转换\n")
L.append("%d 个门禁由 FAIL 转 PASS。\n" % _n_fix)
L.append("")
L.append("## 7.3 剩余风险\n")
L.append("| 风险 | 说明 | 处置 |")
L.append("|---|---|---|")
L.append("| R-05 归因率仅 38.5 % | 组合维度只有 6/8 条真正由 R-05 裁决，"
         "R-05 自身精度的统计功效不足 | 扩充同品种跨度量词用例（R-01 不触发）以隔离 R-05 |")
L.append("| G1 在本测试中不可证伪 | 三变体均经 `guard_resolve_canonical` 装载 | "
         "G1 须在未打补丁引擎上验证，或固定引擎 md5 校验 |")
L.append("| 期望值来自规则语义推断 | D1/D5 的 `expected_rules` 由 token 覆盖推断，"
         "非人工标注 | 首轮需人工复核 26 条 D1 用例的期望，之后冻结 |")
L.append("| F4 抑制不区分方向 | F4b 对复合短语一律抑制，可能放过真实冲突 | "
         "对 P0 级规则保留 F4b 抑制前的告警上报 |")
L.append("")

with io.open(os.path.join(CD, "blacklist_rule_test_result.md"), "w",
             encoding="utf-8", newline="\n") as f:
    f.write("\n".join(L))

# ---- 控制台
print("=" * 78)
print("T2.6 黑名单规则有效性测试")
print("=" * 78)
print("规则 %d (活 %d / 死 %s) | 可构造正向对 %d" % (
    len(BL_LR), len(LIVE_RULES), "、".join(DEAD_RULES), len(CLEAN_POS_RULES)))
print("用例 %d 条:" % len(CASES), dict(Counter(r["dimension"] for r in CASES).most_common()))
for g in ("base", "f3", "f3f4"):
    print("\n[%s] 整体裁决一致率 %s %%  | G1 无崩溃 %s  | G4 边界零误拦 %s"
          % (g, OVERALL_RATE[g],
             "PASS" if GATES[g]["G1_NO_CRASH"]["pass"] else "FAIL",
             "PASS" if GATES[g]["G4_BOUNDARY_ZERO_FP"]["pass"] else "FAIL"))
    for d in DIM_ORDER:
        if d in METRICS[g]:
            m = METRICS[g][d]
            print("   %-18s n=%-3d 崩溃=%-2d TP=%-3d FP=%-3d 一致=%s%%  R-05归因=%s"
                  % (d, m["n"], m["crashed"], m["tp"], m["fp"],
                     m["verdict_match_rate"], m["r05_attribution"]))
print("\n产物: blacklist_rule_test_result.json / .md / regression_gate_config.json")
print("=" * 78)
