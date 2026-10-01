# -*- coding: utf-8 -*-
"""
ths_alias_gap.py — T2.2 THS 指标别名覆盖专项评估
==================================================
DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY

做的事：
  读取 HERMES ths_candidate_mapping.csv (2359 行) 的三类 THS 指标
  (高置信 864 / 模糊待人工确认 1188 / 无候选-低置信 307)，逐条判定其在
  indicator_alias_library.csv 中是否已有同义别名或可解析 canonical，输出
  ths_missing_alias.csv —— 按优先级排序的 V86 别名库迭代素材。

判定口径（全部走原 build_alias_library.py 的归一化函数，不重新实现）：
  RESOLVED_ALIAS_HIT : 库内存在带 canonical 的别名行 (relation != unregistered)
                       或该名可直接解析到 canonical -> 别名库已可解析, 已覆盖
  UNREGISTERED_ONLY  : 库内有该形态的别名行, 但 canonical 为空 (relation=unregistered)
                       -> 别名库知道形态却给不出正主, 需走 B4 canonical 注册通道
  TARGET_HIT         : THS 原名自身不可解析, 但 HERMES best_match 可解析到 canonical
                       -> 缺的是「THS 原名 -> canonical」这一条映射
  MISSING            : 别名库完全无该形态 -> 需新建别名映射

优先级排序：UNREGISTERED_ONLY(无候选) > TARGET_HIT(无候选) > UNREGISTERED_ONLY(模糊)
           > TARGET_HIT(模糊) > TARGET_HIT/UNREGISTERED(高置信) > 已覆盖类
约束：不修改原始别名库 CSV；不调用 zhiji API；纯文本静态匹配。
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
OUT_CSV = os.path.join(OUTDIR, "ths_missing_alias.csv")
OUT_JSON = os.path.join(OUTDIR, "ths_alias_gap_result.json")
LOG = os.path.join(OUTDIR, "ths_alias_gap_log.txt")

buf = []


def pr(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    buf.append(s)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    pr("=" * 78)
    pr("ths_alias_gap.py · THS 指标别名覆盖专项评估 (T2.2)")
    pr("任务 : %s" % K.INTEGRATION_TASK)
    pr("执行时间(UTC+8): %s" % TS)
    head, cut, m5, s256 = K.cut_source()
    pr("判定引擎: build_alias_library.py 第1..%d行 (MD5 %s)" % (cut, m5))
    pr("=" * 78)

    M = K.load_engine()
    match_norm = M["match_norm"]
    norm_full = M["norm_full"]
    resolve_canonical = M["resolve_canonical"]
    canon = M["canon"]

    # ---- 别名库索引（只读）----
    ALIAS = list(csv.DictReader(open(K.ALIAS_CSV, encoding="utf-8-sig", newline="")))
    alias_norm_idx = defaultdict(list)     # alias_norm -> [row]
    for r in ALIAS:
        alias_norm_idx[r["alias_norm"]].append(r)
    canon_name_idx = defaultdict(list)     # match_norm(canonical_name) -> [row]
    canon_name_raw = defaultdict(list)
    for r in ALIAS:
        cn = r["canonical_name"]
        canon_name_raw[cn].append(r)
        for part in cn.split("||"):
            if part.strip():
                canon_name_idx[match_norm(part)].append(r)
    # iv1 canonical 名（用于区分"已是正名"）
    iv1_names = set()
    for k, v in M["iv1"].items():
        if isinstance(v, dict) and "name" in v:
            n = str(v["name"])
            iv1_names.add(match_norm(n))
            iv1_names.add(norm_full(n)[0])

    pr("\n【1】别名库索引")
    pr("  别名库行数          : %d" % len(ALIAS))
    pr("  唯一 alias_norm     : %d" % len(alias_norm_idx))
    pr("  唯一 canonical_name : %d (拆 || 后 %d 个归一名)"
       % (len(canon_name_raw), len(canon_name_idx)))
    pr("  indicators_v1 正名归一形态 (match_norm+norm_full 合并): %d" % len(iv1_names))

    # ---- HERMES mapping ----
    HM = list(csv.DictReader(open(K.HERMES_MAPPING, encoding="utf-8-sig", newline="")))
    pr("\n【2】HERMES THS 候选映射")
    pr("  行数            : %d" % len(HM))
    pr("  match_category  : %s" % dict(Counter(r["match_category"] for r in HM)))
    pr("  zhiji_id_null=Y : %d / %d (全部无 zhiji_id, 待别名链路补位)"
       % (sum(1 for r in HM if r["zhiji_id_null"] == "Y"), len(HM)))
    pr("  distinct variety: %d -> %s"
       % (len(set(r["variety"] for r in HM)),
          dict(Counter(r["variety"] for r in HM).most_common())))

    CAT_ORDER = {"无候选/低置信": 0, "模糊待人工确认": 1, "高置信": 2}
    rows = []
    stat = Counter()
    for r in HM:
        name = r["original_ths_name"].strip()
        nm_full = norm_full(name)[0]      # alias-merge 形态 (alias_norm 列口径)
        nm_match = match_norm(name)       # series 侧形态 (与原模糊匹配一致)
        bm = (r.get("best_match_name") or "").strip()
        bm_full = norm_full(bm)[0] if bm else ""
        bm_nm = match_norm(bm) if bm else ""
        hit_rows = alias_norm_idx.get(nm_full) or alias_norm_idx.get(nm_match) or []
        hit_canon = canon_name_idx.get(nm_match) or canon_name_idx.get(nm_full) or []
        resolved_hits = [r for r in hit_rows
                         if r["canonical_key"].strip() and r["relation"] != "unregistered"]
        unreg_hits = [r for r in hit_rows if r not in resolved_hits]

        # canonical 解析（对 THS 原名与其 best_match 分别试）
        def resolve_safe(nf):
            if not nf:
                return []
            try:
                return resolve_canonical(nf)
            except Exception:
                return []
        canon_of_name = resolve_safe(nm_full)
        canon_of_bm = resolve_safe(bm_full)
        is_iv1_name = (nm_full in iv1_names) or (nm_match in iv1_names)

        if resolved_hits or canon_of_name or hit_canon or is_iv1_name:
            status = "RESOLVED_ALIAS_HIT"
        elif hit_rows:
            status = "UNREGISTERED_ONLY"
        elif canon_of_bm:
            status = "TARGET_HIT"
        else:
            status = "MISSING"
        stat[status] += 1

        # 优先级：未解析且无候选者最优先
        c = CAT_ORDER.get(r["match_category"], 9)
        if status == "UNREGISTERED_ONLY":
            p = c * 10 + 0
        elif status == "TARGET_HIT":
            p = c * 10 + 2
        elif status == "MISSING":
            p = c * 10 + 1
        else:  # RESOLVED_ALIAS_HIT (已覆盖)
            p = 90 + c

        action = {
            "UNREGISTERED_ONLY": "B4 通道: 库内有形态但无 canonical, 需 DSH-B 补 canonical 注册后回填映射",
            "TARGET_HIT": "补「THS 原名 -> best_match 的 canonical」别名映射 (人工确认后写入)",
            "MISSING": "新建别名映射: THS 原名 -> 人工确认的 canonical (V86 必补)",
            "RESOLVED_ALIAS_HIT": "已可解析到 canonical, 无需新增 (仅需 zhiji_id 回填链路验证)",
        }[status]

        rows.append({
            "priority_rank": p,
            "priority_bucket": {
                0: "P0_UNREG_NO_CANDIDATE", 1: "P0_MISS_NO_CANDIDATE", 2: "P0_TGT_NO_CANDIDATE",
                10: "P1_UNREG_AMBIGUOUS", 11: "P1_MISS_AMBIGUOUS", 12: "P1_TGT_AMBIGUOUS",
                20: "P2_UNREG_HIGHCONF", 21: "P2_MISS_HIGHCONF", 22: "P2_TGT_HIGHCONF",
                90: "P9_RESOLVED", 91: "P9_RESOLVED_AMBIG", 92: "P9_RESOLVED_HIGH",
            }.get(p, "P9"),
            "ths_chart_id": r["ths_chart_id"], "variety": r["variety"],
            "series_index": r["series_index"], "original_ths_name": name,
            "match_category": r["match_category"], "best_match_name": bm,
            "best_match_score": r["best_match_score"],
            "ths_alias_status": status,
            "alias_form_hits": len(hit_rows),
            "alias_resolved_hits": len(resolved_hits),
            "alias_unregistered_hits": len(unreg_hits),
            "is_indicators_v1_name": "Y" if is_iv1_name else "N",
            "resolution_canonical_key": "|".join(canon_of_name[:2]) if canon_of_name else "",
            "resolution_alias_id": "|".join(x["alias_id"] for x in resolved_hits[:2]),
            "unregistered_alias_id": "|".join(x["alias_id"] for x in unreg_hits[:2]),
            "best_match_canonical_key": "|".join(canon_of_bm[:2]) if canon_of_bm else "",
            "candidate_indicator_ids": r["candidate_indicator_ids"],
            "candidate_names": r["candidate_names"],
            "recommended_action": action,
        })

    rows.sort(key=lambda x: (x["priority_rank"], x["variety"], x["ths_chart_id"],
                             int(x["series_index"]) if x["series_index"].isdigit() else 0))
    for i, r in enumerate(rows, 1):
        r["priority_seq"] = i

    # ---- 输出 CSV ----
    cols = ["priority_seq", "priority_rank", "priority_bucket", "ths_chart_id", "variety",
            "series_index", "original_ths_name", "match_category", "ths_alias_status",
            "alias_form_hits", "alias_resolved_hits", "alias_unregistered_hits",
            "is_indicators_v1_name", "resolution_canonical_key", "resolution_alias_id",
            "unregistered_alias_id", "best_match_canonical_key",
            "best_match_name", "best_match_score", "recommended_action",
            "candidate_indicator_ids", "candidate_names"]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    ORDER = ["UNREGISTERED_ONLY", "TARGET_HIT", "MISSING", "RESOLVED_ALIAS_HIT"]
    MEAN = {"UNREGISTERED_ONLY": "库内有形态但无 canonical, 需补注册",
            "TARGET_HIT": "原名缺映射, best_match 可解析",
            "MISSING": "别名库完全无该形态",
            "RESOLVED_ALIAS_HIT": "已可解析到 canonical, 已覆盖"}
    pr("\n【3】THS 别名覆盖判定结果")
    pr("  %-19s %6s %7s %s" % ("状态", "行数", "占比", "含义"))
    for st in ORDER:
        pr("  %-19s %6d %6.1f%%  %s" % (st, stat[st], 100.0 * stat[st] / len(rows), MEAN[st]))
    gap = stat["UNREGISTERED_ONLY"] + stat["TARGET_HIT"] + stat["MISSING"]
    pr("  需补工作 (UNREGISTERED+TARGET+MISSING) = %d / %d = %.1f%%"
       % (gap, len(rows), 100.0 * gap / len(rows)))
    pr("  其中真正缺别名映射 (TARGET_HIT+MISSING) = %d (%.1f%%)"
       % (stat["TARGET_HIT"] + stat["MISSING"],
          100.0 * (stat["TARGET_HIT"] + stat["MISSING"]) / len(rows)))
    pr("  其中缺 canonical 注册 (UNREGISTERED_ONLY) = %d (%.1f%%)"
       % (stat["UNREGISTERED_ONLY"], 100.0 * stat["UNREGISTERED_ONLY"] / len(rows)))

    pr("\n  优先级分桶:")
    for k, v in Counter(r["priority_bucket"] for r in rows).most_common():
        pr("    %-24s %5d" % (k, v))

    pr("\n  未覆盖三类 × HERMES 分类 交叉表:")
    pr("  %-19s %12s %14s %14s" % ("状态", "无候选/低置信", "模糊待人工确认", "高置信"))
    for st in ["UNREGISTERED_ONLY", "TARGET_HIT", "MISSING"]:
        cc = Counter(r["match_category"] for r in rows if r["ths_alias_status"] == st)
        pr("  %-19s %12d %14d %14d"
           % (st, cc.get("无候选/低置信", 0), cc.get("模糊待人工确认", 0), cc.get("高置信", 0)))

    pr("\n  UNREGISTERED_ONLY 按品种 (Top12) — V86 canonical 注册重点:")
    for k, v in Counter(r["variety"] for r in rows
                        if r["ths_alias_status"] == "UNREGISTERED_ONLY").most_common(12):
        pr("    %-6s %5d" % (k, v))
    pr("  TARGET_HIT 按品种:")
    for k, v in Counter(r["variety"] for r in rows
                        if r["ths_alias_status"] == "TARGET_HIT").most_common(12):
        pr("    %-6s %5d" % (k, v))
    pr("  MISSING 按品种:")
    for k, v in Counter(r["variety"] for r in rows if r["ths_alias_status"] == "MISSING") \
            .most_common(12):
        pr("    %-6s %5d" % (k, v))

    pr("\n  待补别名 Top25 明细 (priority_seq 前 25):")
    pr("  %-6s %-6s %-3s %-32s %-12s %-19s %s"
       % ("chart", "variety", "idx", "original_ths_name", "category", "status", "best_match"))
    for r in rows[:25]:
        pr("  %-6s %-6s %-3s %-32s %-12s %-19s %s"
           % (r["ths_chart_id"][:6], r["variety"], r["series_index"][:3],
              r["original_ths_name"][:32], r["match_category"][:12], r["ths_alias_status"],
              r["best_match_name"][:20]))

    # ---- best_match 跨品种审计 (未解析行的候选可靠性) ----
    metal_families = M["metal_families"]
    VAR2FAM = {"NI": "NI", "SN": "SN", "ZN": "ZN", "SI": "SI", "LI": "LI",
               "AL": "AL", "CU": "CU"}
    gap_rows = [r for r in rows if r["ths_alias_status"] != "RESOLVED_ALIAS_HIT"]
    bv_cross = bv_same = bv_none = bv_other = 0
    bv_cross_detail = []
    for r in gap_rows:
        chart_var = VAR2FAM.get(r["variety"])
        if not chart_var:
            bv_other += 1
            continue
        bm_fam = set(metal_families(r["best_match_name"] or ""))
        if not bm_fam:
            bv_none += 1
            continue
        if chart_var in bm_fam:
            bv_same += 1
        else:
            bv_cross += 1
            if len(bv_cross_detail) < 20:
                bv_cross_detail.append({"chart": r["ths_chart_id"], "variety": r["variety"],
                                        "name": r["original_ths_name"][:28],
                                        "best_match": r["best_match_name"][:28],
                                        "bm_variety": sorted(bm_fam)})
    pr("\n  未解析 %d 行的 best_match 跨品种审计 (候选可靠性):" % len(gap_rows))
    pr("    同品种        : %5d" % bv_same)
    pr("    跨品种 (错误) : %5d  (%.1f%%)" % (bv_cross, 100.0 * bv_cross / len(gap_rows)))
    pr("    无品种标记    : %5d" % bv_none)
    pr("    图表品种不在语料族表: %d" % bv_other)
    for x in bv_cross_detail[:12]:
        pr("      %-12s %-3s %-28s -> %-28s (%s)" % (x["chart"], x["variety"],
                                                      x["name"], x["best_match"],
                                                      ",".join(x["bm_variety"])))

    # ---- 按品种估算新增别名量 ----
    per_variety = defaultdict(lambda: Counter())
    for r in rows:
        if r["ths_alias_status"] in ("UNREGISTERED_ONLY", "TARGET_HIT", "MISSING"):
            per_variety[r["variety"]][r["ths_alias_status"]] += 1
    pr("\n  按品种待补量 (V86 迭代估算):")
    pr("  %-8s %16s %10s %8s %8s" % ("variety", "UNREGISTERED_ONLY", "TARGET", "MISSING", "合计"))
    for v, c in sorted(per_variety.items(), key=lambda kv: -sum(kv[1].values())):
        pr("  %-8s %16d %10d %8d %8d"
           % (v, c["UNREGISTERED_ONLY"], c["TARGET_HIT"], c["MISSING"], sum(c.values())))

    res = {
        "task": K.INTEGRATION_TASK, "generated_at": TS,
        "source_norm": "build_alias_library.py::match_norm/norm_full (原样加载)",
        "hermes_rows": len(HM), "alias_lib_rows": len(ALIAS),
        "hermes_match_category_dist": dict(Counter(r["match_category"] for r in HM)),
        "coverage_status": dict(stat),
        "gap_total": gap,
        "gap_pct": round(100.0 * gap / len(rows), 2),
        "need_alias_mapping": stat["TARGET_HIT"] + stat["MISSING"],
        "need_canonical_registration": stat["UNREGISTERED_ONLY"],
        "priority_bucket_dist": dict(Counter(r["priority_bucket"] for r in rows)),
        "gap_by_category": {st: dict(Counter(r["match_category"] for r in rows
                                              if r["ths_alias_status"] == st))
                            for st in ["UNREGISTERED_ONLY", "TARGET_HIT", "MISSING"]},
        "gap_by_variety": {st: dict(Counter(r["variety"] for r in rows
                                             if r["ths_alias_status"] == st))
                           for st in ["UNREGISTERED_ONLY", "TARGET_HIT", "MISSING"]},
        "per_variety_gap": {v: dict(c) for v, c in per_variety.items()},
        "best_match_cross_variety_audit": {
            "gap_rows": len(gap_rows), "same_variety": bv_same, "cross_variety": bv_cross,
            "no_variety_token": bv_none, "chart_variety_unknown": bv_other,
            "cross_variety_pct": round(100.0 * bv_cross / len(gap_rows), 2) if gap_rows else 0.0,
            "cross_variety_samples": bv_cross_detail,
        },
        "top25_gap": rows[:25],
        "output_csv": os.path.basename(OUT_CSV), "output_rows": len(rows),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    pr("\n已写出: %s (%d 行, %d bytes)" % (OUT_CSV, len(rows), os.path.getsize(OUT_CSV)))
    pr("已写出: %s" % OUT_JSON)
    pr("=" * 78)
    open(LOG, "w", encoding="utf-8").write("\n".join(buf))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
