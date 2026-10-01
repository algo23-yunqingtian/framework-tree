# -*- coding: utf-8 -*-
"""
generate_conflict_classification.py — 为 165 条多 canonical 冲突条目生成 A/B 分类清单

分类口径：
  原子键结构 <variety>_<seq>_<metric>[_qualifier...]，尾缀 _N 视为「同键重复注册」。
  剥离全部 _N 尾缀后：
    base 集合唯一  -> A_重复注册（可自动合并，冲突为数据缺陷产物）
    base 集合多值  -> B_真实不同指标（须人工裁决或显式保留歧义）
  B 类再按 (seq 集合, metric 集合) 细分四类。
产物：multi_canonical_conflict_classification.csv
"""
import csv
import io
import os
import re
import sys

CD = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_audit_design"
SRC = os.path.join(CD, "multi_canonical_conflicts_165.csv")
OUT = os.path.join(CD, "multi_canonical_conflict_classification.csv")


def base_of(k):
    """剥离全部纯数字尾缀。"""
    return re.sub(r"(_\d+)+$", "", k.strip())


def sm_of(k):
    m = re.match(r"^([a-z]+)_(\d+)_(.*)$", k.strip())
    return (m.group(1), m.group(2), m.group(3)) if m else (None, None, None)


def classify(keys):
    bases = {base_of(k) for k in keys}
    if len(bases) == 1:
        return "A_重复注册", "仅 _N 尾缀差异", "自动合并至 base", "auto_merge"
    sm = [sm_of(k) for k in keys]
    seqs, mets = {s[1] for s in sm}, {s[2] for s in sm}
    if len(seqs) > 1 and len(mets) > 1:
        return "B_真实不同指标", "不同序号不同度量词", "人工裁决", "manual"
    if len(seqs) > 1 and len(mets) == 1:
        return "B_真实不同指标", "不同序号同度量词", "人工裁决（建议保留最窄口径）", "manual"
    if len(seqs) == 1 and len(mets) > 1:
        return "B_真实不同指标", "同序号不同度量词", "人工裁决（建议按度量词择优）", "manual"
    return "B_真实不同指标", "同序号同度量词仅尾缀差异", "自动合并至 base", "auto_merge"


def main():
    with io.open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    seqn = [int(x["seq"].strip(" ")) for x in rows]
    assert len(rows) == 165, "expected 165 rows, got %d" % len(rows)

    out_rows = []
    for x in rows:
        keys = [k.strip() for k in x["atomic_keys"].split("|") if k.strip()]
        cls, subtype, rec, act = classify(keys)
        bases = sorted({base_of(k) for k in keys})
        out_rows.append({
            "seq": x["seq"],
            "alias_id": x["alias_id"],
            "alias_norm": x["alias_norm"],
            "alias_name": x["alias_name"],
            "n_atomic_keys": x["n_atomic_keys"],
            "atomic_keys": x["atomic_keys"],
            "variety_family": x["variety_family"],
            "metric_noun": x["metric_noun"],
            "alias_type": x["alias_type"],
            "alias_source": x["alias_source"],
            "relation": x["relation"],
            "confidence": x["confidence"],
            "review_flag": x["review_flag"],
            "review_priority": x["review_priority"],
            "conflict_class": cls,
            "conflict_subtype": subtype,
            "n_unique_base": len(bases),
            "unique_base": "|".join(bases),
            "recommended_action": rec,
            "action_mode": act,
        })

    fields = list(out_rows[0].keys())
    with io.open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    # 汇总
    from collections import Counter
    cls = Counter(x["conflict_class"] for x in out_rows)
    sub = Counter(x["conflict_subtype"] for x in out_rows)
    mode = Counter(x["action_mode"] for x in out_rows)
    by_variety = Counter(x["variety_family"] for x in out_rows)
    by_type = Counter(x["alias_type"] for x in out_rows)
    n_by_class = Counter(int(x["n_atomic_keys"]) for x in out_rows)

    a_bases = {base_of(x["atomic_keys"].split("|")[0].strip())
               for x in out_rows if x["conflict_class"] == "A_重复注册"}
    a_merged_total = sum(1 for x in out_rows if x["conflict_class"] == "A_重复注册")
    atomic_total = sum(int(x["n_atomic_keys"]) for x in out_rows)

    print("=" * 78)
    print("165 条多 canonical 冲突 A/B 分类")
    print("=" * 78)
    print("冲突分类: %s" % dict(cls))
    print("B 类细分: %s" % dict(sub.most_common()))
    print("处置方式: %s" % dict(mode))
    print("A 类行 %d, 合并后唯一 base %d, 去重收益 %d 键"
          % (a_merged_total, len(a_bases), a_merged_total - len(a_bases)))
    print("原子键总计 %d, 去重后 %d" % (atomic_total,
                                       sum(1 for x in out_rows
                                           for k in x["atomic_keys"].split("|") if k.strip())))
    print("品种分布: %s" % dict(by_variety.most_common()))
    print("alias_type: %s" % dict(by_type.most_common()))
    print("n_atomic_keys 分布: %s" % dict(sorted(n_by_class.items(), key=lambda kv: -kv[1])))
    print("输出: %s (%d 行, %d 列)" % (OUT, len(out_rows), len(fields)))
    print("=" * 78)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
