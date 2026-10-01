# -*- coding: utf-8 -*-
"""
blacklist_coverage_analysis.py — T2.4 黑名单规则覆盖度分析

对 31 条黑名单规则逐条判定：
  R1 可达性：在当前门禁顺序（alias_exact 前置）下，是否可能被 R-05 上报
  R2 现有覆盖：24 条 boundary testset 中是否被引用
  R3 数据支撑：别名库中是否存在真实触发对（L token 在 a、R token 在 b）
  R4 遮蔽风险：是否存在同 severity 且 L 交集非空的规则
产物：blacklist_rule_coverage_matrix.csv
"""
import csv
import io
import json
import sys
from collections import Counter, defaultdict

CD = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_audit_design"
DTC = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_audit_design_testcase"
DMM = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\miss_risk_mining"
DIN = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_integrate_test"
sys.path.insert(0, CD)
sys.path.insert(0, DIN)
import audit_kit as A  # noqa: E402

M, em, guard, rules, bl_lr, lint = A.load_engine()
BL = M["BL_LR"]
NF = M["norm_full"]

ALIAS_ROWS = list(csv.DictReader(
    io.open(r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\alias_lib_full_audit"
            r"\indicator_alias_library.csv", encoding="utf-8-sig", newline="")))
NAMES = sorted({NF(r["alias_name"])[0] for r in ALIAS_ROWS if r["alias_name"].strip()})
CANON = sorted({NF(r["canonical_name"])[0] for r in ALIAS_ROWS if r["canonical_name"].strip()})
POOL = NAMES + CANON
assert POOL, "alias pool empty"

TS = json.load(io.open(DMM + r"\blacklist_boundary_testset.json", encoding="utf-8"))["cases"]

# 每 token 命中的池内名字（预计算，pool 约 4000）
tok_idx = defaultdict(list)
for s in POOL:
    for t in {x for r in BL.values() for x in (r[0] | r[1])}:
        if t and t in s:
            tok_idx[t].append(s)
for t in tok_idx:
    tok_idx[t] = sorted(set(tok_idx[t]))

sev_order = {"P0": 0, "P1": 1, "P2": 2}
ids = sorted(BL.keys())
ids_by_sev = sorted(BL.keys(), key=lambda i: (sev_order.get(BL[i][2], 9), i))
iter_seq = list(BL.keys())          # 实际迭代顺序


def reachable_in_gate(i):
    """给定规则 i，若存在更早迭代的同 severity 规则 j 满足 L_j ⊇ L_i 且 R_j ⊇ R_i，则被遮蔽。"""
    pos = iter_seq.index(i)
    Ji = BL[i][0]; Ri = BL[i][1]
    blockers = []
    for j in iter_seq[:pos]:
        if BL[j][2] != BL[i][2]:
            continue
        Lj, Rj = BL[j][0], BL[j][1]
        if (set(Ji) <= set(Lj) and set(Ri) <= set(Rj)):
            blockers.append(j)
    return blockers


rows_out = []
for i in ids:
    L, R, sev, nm = BL[i]
    # R3 真实触发对
    pos_pairs = []
    for lp in sorted(L):
        for rp in sorted(R):
            xs = tok_idx.get(lp, [])
            ys = tok_idx.get(rp, [])
            if not xs or not ys:
                continue
            # 取 L token 不在 y、R token 不在 x 的真实对（避免同串自触发）
            best = None
            for x in xs[:40]:
                for y in ys[:40]:
                    if x == y:
                        continue
                    if any(rp2 in x for rp2 in R) or any(lp2 in y for lp2 in L):
                        continue
                    best = (x, y, lp, rp)
                    break
                if best:
                    break
            if best:
                pos_pairs.append(best)
                if len(pos_pairs) >= 3:
                    break
        if len(pos_pairs) >= 3:
            break
    # 负样本：只含 L token、无 R token 的孤立名字（不应被拦截）
    neg_single = tok_idx.get(sorted(L)[0], [])[:3]
    # R2 现有覆盖
    referenced = sorted({c["expected_rule"] for c in TS if i in str(c.get("expected_rule"))})
    ref_cases = [c["case_id"] for c in TS if i in str(c.get("expected_rule"))]
    blockers = reachable_in_gate(i)
    overlaps = sorted({j for j in ids if j != i and BL[j][2] == sev
                       and (set(L) & set(BL[j][0]))})
    lint_n = sum(1 for x in lint if x["rule_id"] == i)
    rows_out.append({
        "rule_id": i, "severity": sev, "rule_name": nm,
        "n_L_tokens": len(L), "n_R_tokens": len(R),
        "L_tokens": "|".join(sorted(L)), "R_tokens": "|".join(sorted(R)),
        "gate_iter_order": iter_seq.index(i) + 1,
        "shadowed_by": "|".join(blockers) or "-",
        "reachable_in_current_gate": "NO" if blockers else "YES",
        "same_sev_L_overlap_rules": "|".join(overlaps) or "-",
        "n_overlap_rules": len(overlaps),
        "testset_referenced": "YES" if referenced else "NO",
        "testset_cases": "|".join(ref_cases) or "-",
        "real_trigger_pairs_found": len(pos_pairs),
        "example_positive_pair": (pos_pairs[0][0] + "  <->  " + pos_pairs[0][1]) if pos_pairs else "-",
        "example_tokens": (pos_pairs[0][2] + " vs " + pos_pairs[0][3]) if pos_pairs else "-",
        "neg_single_example": "|".join(neg_single) or "-",
        "lint_warnings": lint_n,
        "coverage_status": (
            "COVERED" if (referenced and not blockers) else
            ("REFERENCED_BUT_UNREACHABLE" if referenced else
             ("UNCOVERED_REACHABLE" if not blockers else "UNCOVERED_SHADOWED"))),
    })

with io.open(CD + r"\blacklist_rule_coverage_matrix.csv", "w", encoding="utf-8-sig",
             newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
    w.writeheader()
    w.writerows(rows_out)

st = Counter(x["coverage_status"] for x in rows_out)
print("=" * 78)
print("T2.4 黑名单规则覆盖度矩阵")
print("=" * 78)
print("规则总数 %d (P0 %d / P1 %d / P2 %d)" % (len(ids),
      sum(1 for x in rows_out if x["severity"] == "P0"),
      sum(1 for x in rows_out if x["severity"] == "P1"),
      sum(1 for x in rows_out if x["severity"] == "P2")))
print("现状覆盖状态:", dict(st.most_common()))
print("testset 引用规则数: %d/%d (%.1f%%)" % (sum(1 for x in rows_out
      if x["testset_referenced"] == "YES"), len(ids),
      100.0 * sum(1 for x in rows_out if x["testset_referenced"] == "YES") / len(ids)))
print("当前门禁不可达（被遮蔽）: %d" % sum(1 for x in rows_out
                                        if x["reachable_in_current_gate"] == "NO"))
print("有遮蔽的规则:", [(x["rule_id"], x["shadowed_by"]) for x in rows_out
                       if x["reachable_in_current_gate"] == "NO"])
print("有真实触发对支撑: %d/%d" % (sum(1 for x in rows_out if x["real_trigger_pairs_found"] > 0),
                                  len(ids)))
print("lint 告警: 总计 %d, 涉及规则 %d/%d" % (len(lint),
      sum(1 for x in rows_out if x["lint_warnings"] > 0), len(ids)))
print("池规模: alias_name %d + canonical_name %d = %d" % (len(NAMES), len(CANON), len(POOL)))
print("输出: blacklist_rule_coverage_matrix.csv (%d 行)" % len(rows_out))
print("=" * 78)
