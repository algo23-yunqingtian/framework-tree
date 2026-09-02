#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_plan_cache.py — 把 correction_register_plan.json 里**未在 api_cache** 的
备选 ID（smm_id / mysteel_id / ids）逐个拉取 zhiji 系列数据，并以**裸 ID** 作 metric
写入 api_cache（与旧 SI/LI 缓存的 metric 命名一致），使得 build_translation
的 load_metric(hit_id=zhiji_id, code) 能命中。

行为：
  1. 读 plan → 收集所有备选 ID（去重）
  2. 对每个 ID，若 api_cache(metric=ID, code={SI,LI}) 已有则跳过
  3. 调用 zhiji series 拉取 → 写回 api_cache，name/unit 优先取 indicators_v1 映射，
     拿不到则用 plan 里的 concept / 系列原报
  4. 1 秒限频
"""
import argparse, json, os, sqlite3, subprocess, sys, time
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "scripts" / "api_cache.db"
ZHJI = Path.home() / ".hermes" / "scripts" / "zhiji_api.py"
PLAN = ROOT / "analysis" / "iwencai" / "correction_register_plan.json"
INDICATOR_JSON = ROOT / "data" / "indicators_v1.json"


def zhiji_series(zid, start, end):
    r = subprocess.run([sys.executable, str(ZHJI), "series", zid, start, end],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None, r.stderr[:200]
    try:
        return json.loads(r.stdout, strict=False), None
    except Exception as e:
        return None, str(e)


def collect_plan_ids(plan):
    """返回 {zhiji_id: {"varieties":[...], "concept":..., "node":..., "unit":..., "freq":...}}"""
    out = {}
    for v in ["SI", "LI"]:
        for node, info in plan[v].items():
            for row in info.get("rows", []):
                ids = []
                for rid in row.get("ids", []):
                    if rid and rid not in ("null",):
                        ids.append(rid)
                for k in ["smm_id", "mysteel_id"]:
                    rid = row.get(k)
                    if rid and rid != "null" and rid not in ids:
                        ids.append(rid)
                for rid in ids:
                    if rid not in out:
                        out[rid] = {
                            "varieties": [v],
                            "concept": row.get("concept", ""),
                            "node": node,
                            "unit": row.get("unit", ""),
                            "freq": row.get("freq", ""),
                        }
                    else:
                        if v not in out[rid]["varieties"]:
                            out[rid]["varieties"].append(v)
    return out


def build_ind_mapping(ind_doc):
    """zhiji_id -> {name, unit}（基于 indicators_v1 ids 字段）"""
    m = {}
    for k, meta in ind_doc.get("indicators", {}).items():
        for code, v in (meta.get("ids") or {}).items():
            if v:
                m[v] = {
                    "name": meta.get("name", ""),
                    "unit": meta.get("unit", ""),
                    "freq": meta.get("freq", ""),
                }
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2018-01-01")
    ap.add_argument("--until", default="2026-09-01")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--varieties", default="",
                    help="逗号分隔，如 SI,LI；空=全部")
    args = ap.parse_args()

    varieties_wanted = [v for v in args.varieties.split(",") if v] if args.varieties else []

    plan = json.load(open(PLAN, encoding="utf-8"))
    ind_doc = json.load(open(INDICATOR_JSON, encoding="utf-8"))
    ind_map = build_ind_mapping(ind_doc)

    all_ids = collect_plan_ids(plan)
    con = sqlite3.connect(str(DB))
    cur = con.cursor()

    to_fetch = []
    for zid, meta in all_ids.items():
        varieties = meta["varieties"] if not varieties_wanted else \
            [v for v in varieties_wanted if v in meta["varieties"]]
        if not varieties:
            continue
        # 检查每个品种是否已有
        for v in varieties:
            exists = cur.execute(
                "SELECT COUNT(*) FROM indicator_cache WHERE metric=? AND code=?",
                (zid, v)).fetchone()[0] > 0
            if not exists:
                to_fetch.append((zid, v, meta))
                break

    print("[INFO] 待拉取 ID 数:", len(to_fetch))
    if args.dry:
        for zid, v, meta in to_fetch[:30]:
            print("  DRY", v, zid, "|", meta["concept"][:40])
        return

    stats = {"ok": 0, "empty": 0, "err": 0}
    for zid, v, meta in to_fetch:
        data, err = zhiji_series(zid, args.since, args.until)
        if err or not data:
            print("  ✗ [%s] %s  %s  ← %s" % (v, zid, meta["concept"][:30], err or "空"))
            stats["err"] += 1
            continue
        pts = [{
            "date": p["date"], "value": p["value"]
        } for p in data.get("points", [])
            if isinstance(p, dict) and p.get("date") and p.get("value") is not None]
        if not pts:
            stats["empty"] += 1
            continue
        # 拼装 payload
        base_name = ind_map.get(zid, {}).get("name", "") or meta["concept"] or ""
        unit = ind_map.get(zid, {}).get("unit", "") or meta.get("unit", "") or ""
        freq = ind_map.get(zid, {}).get("freq", "") or meta.get("freq", "") or ""
        latest = max(p["date"] for p in pts)
        payload = {
            "id": data.get("id", zid),
            "source": data.get("source", ""),
            "name": base_name,
            "unit": unit,
            "freq": freq,
            "points": pts,
        }
        con.execute(
            "INSERT OR REPLACE INTO indicator_cache(code, metric, zhiji_id, data_json, name, unit, freq, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (v, zid, zid, json.dumps(payload, ensure_ascii=False),
             base_name, unit, freq))
        print("  ✓ [%s] %s  %d pts  latest=%s  %s" % (v, zid, len(pts), latest, meta["concept"][:30]))
        stats["ok"] += 1
        time.sleep(1.0)

    con.commit()
    con.close()
    print("\n========== SUMMARY ==========")
    print(stats)


if __name__ == "__main__":
    main()