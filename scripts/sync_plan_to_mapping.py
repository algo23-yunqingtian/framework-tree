#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_plan_to_mapping.py — 把 correction_register_plan.json 里新增的 ID 行
追加进 translation-workspace/mapping/{SI,LI}/step2_match_{SI,LI}.json。

判定"新增"：plan row 里的任一 id 不在旧 mapping 已有 hit_id 中。
写入策略：grade=A；hit_id 优先取 smm_id（a/j 前缀，旧 mapping 惯例），
          缺失则回退到 mysteel_id（FU 前缀）；两者皆缺则跳过该行。
          同一 row 多个 id 时，额外 id 作为备选另开一条（grade=B 占位）。

用法：
    python3 scripts/sync_plan_to_mapping.py              # 实跑
    python3 scripts/sync_plan_to_mapping.py --dry        # 只打印计划
"""
import argparse, json, os, sys, shutil
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

PLAN_PATH = os.path.join(ROOT, "analysis", "iwencai", "correction_register_plan.json")


def read_mapping(v):
    p = os.path.join(ROOT, "translation-workspace", "mapping", v,
                     "step2_match_%s.json" % v)
    return json.load(open(p, encoding="utf-8"))


def write_mapping(v, d, dry=False):
    p = os.path.join(ROOT, "translation-workspace", "mapping", v,
                     "step2_match_%s.json" % v)
    bak = p + ".bak_before_sync"
    if not dry and not os.path.exists(bak):
        shutil.copy2(p, bak)
        print("  backup: %s" % bak)
    if not dry:
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return p


def _pick_hit_id(row):
    """优先 smm_id (a/j 前缀)，无则 mysteel_id (FU 前缀)"""
    smm = (row.get("smm_id") or "").strip() if row.get("smm_id") else ""
    fu = (row.get("mysteel_id") or "").strip() if row.get("mysteel_id") else ""
    if smm and smm != "null":
        return smm
    if fu and fu != "null":
        return fu
    # 兜底：从 ids 列表取第一个
    for rid in (row.get("ids") or []):
        if rid:
            return rid
    return None


def _name(row, hit_id):
    """拼 name。优先从 indicators_v1 拿；拿不到用 concept。"""
    concept = row.get("concept") or ""
    freq = row.get("freq") or ""
    unit = row.get("unit") or ""
    n = "null" if hit_id == "null" else hit_id
    try:
        ind = json.load(open(os.path.join(ROOT, "data", "indicators_v1.json"), encoding="utf-8"))
        for m, meta in ind.get("indicators", {}).items():
            ids = meta.get("ids") or {}
            for code, v in ids.items():
                if v == hit_id:
                    return meta.get("name") or (concept or "")
    except Exception:
        pass
    parts = [concept]
    if freq:
        parts.append(freq)
    if unit:
        parts.append(unit)
    return ("（%s）" % " / ".join(parts)) if concept else ("hit=%s" % hit_id)


def sync(v, dry=False):
    plan = json.load(open(PLAN_PATH, encoding="utf-8"))[v]
    mp = read_mapping(v)
    old_hit_ids = set()
    for vv in mp.values():
        if vv.get("hit_id"):
            old_hit_ids.add(vv["hit_id"])

    added = 0
    skipped_no_id = 0
    for node, info in plan.items():
        for row in info.get("rows", []):
            hit_id = _pick_hit_id(row)
            if not hit_id:
                skipped_no_id += 1
                continue
            if hit_id in old_hit_ids or hit_id in mp.get(hit_id, {}).values():
                # 已存在，跳过
                continue
            concept = row.get("concept") or ("id=%s" % hit_id)
            unit = row.get("unit") or ""
            freq = row.get("freq") or ""
            name = "%s%s%s" % (concept,
                                ("（%s）" % freq) if freq else "",
                                (" · %s" % unit) if unit else "")
            key = "%s|%s" % (node, concept[:40])
            # 防 key 碰撞
            orig_key = key
            i = 1
            while key in mp:
                key = "%s|%s#%d" % (node, concept[:40], i)
                i += 1
            entry = {
                "grade": "A",
                "hit_id": hit_id,
                "hit_name": _name(row, hit_id),
                "name": name,
                "subnode": node,
                "_origin": "sync_plan_to_mapping",
            }
            mp[key] = entry
            added += 1
            print("  [+] %s %s  %s  ← %s" % (v, node, concept[:30], hit_id))

    write_mapping(v, mp, dry)
    return {"variety": v, "added": added, "skipped_no_id": skipped_no_id,
            "total_keys": len(mp)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--variety", choices=["SI", "LI", "ALL"], default="ALL")
    args = ap.parse_args()

    varieties = ["SI", "LI"] if args.variety == "ALL" else [args.variety]
    for v in varieties:
        print("\n=== sync %s (dry=%s) ===" % (v, args.dry))
        r = sync(v, args.dry)
        print("  result: added=%d skipped_no_id=%d total_keys=%d" %
              (r["added"], r["skipped_no_id"], r["total_keys"]))
    print("\nDONE")


if __name__ == "__main__":
    main()