#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step2_cache_load.py — 翻译线 Step2→Step5 桥接：把映射表 hit_id 拉数灌入 api_cache.db

从 translation-workspace/mapping/{品种}/step2_match_*.json 取 A/B 级 hit_id，
逐条 zhiji series 拉数（近 5 年），写入 scripts/api_cache.db 的 indicator_cache 表
（metric=hit_id, code=品种），供 build_translation.py 的 load_metric() 读取渲染。

用法:
  python3 scripts/step2_cache_load.py --all
  python3 scripts/step2_cache_load.py --variety ZN
  python3 scripts/step2_cache_load.py --all --only-verified  # 只灌实测有数据的
"""
import argparse, json, os, re, sqlite3, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZHJ = os.path.expanduser("~/.hermes/scripts/zhiji_api.py")
DB = os.path.join(ROOT, "scripts", "api_cache.db")
RATE = 1.1
CODE_CN = {"ZN": "锌", "CU": "铜", "AL": "铝", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}

def zhiji_series(zid, start, end):
    r = subprocess.run(["/usr/bin/python3", ZHJ, "series", zid, start, end],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout, strict=False)
    except Exception:
        return None

def build_points(pts_raw):
    return [{"date": p["date"], "value": p["value"]} for p in pts_raw
            if isinstance(p, dict) and p.get("date") and p.get("value") is not None]

def load_one(con, code, hit_id, name, start="2021-01-01", end="2026-12-31"):
    data = zhiji_series(hit_id, start, end)
    if not data:
        return (hit_id, 0, "空响应")
    pts = build_points(data.get("points", []))
    if not pts:
        return (hit_id, 0, "空数据")
    payload = {
        "id": data.get("id", hit_id),
        "source": data.get("source", ""),
        "name": data.get("name", name),
        "unit": data.get("unit", ""),
        "freq": data.get("frequency", ""),
        "points": pts,
    }
    con.execute(
        "INSERT OR REPLACE INTO indicator_cache(code, metric, zhiji_id, data_json, name, unit, freq, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        (code, hit_id, hit_id, json.dumps(payload, ensure_ascii=False),
         payload["name"], payload["unit"], payload["freq"])
    )
    con.commit()
    return (hit_id, len(pts), None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--variety")
    ap.add_argument("--only-verified", action="store_true")
    args = ap.parse_args()
    varieties = ["ZN", "CU", "AL", "NI", "SN", "SI", "LI"] if args.all or not args.variety else [args.variety]
    # 实测结果（有数据集合）——兼容两种格式: dict列表 或 (v, vv) 元组列表
    verified = set()
    if args.only_verified and os.path.exists("/tmp/series_ok.json"):
        raw = json.load(open("/tmp/series_ok.json"))
        for r in raw:
            if isinstance(r, dict) and r.get("hit_id"):
                verified.add(r["hit_id"])
            elif isinstance(r, (list, tuple)) and len(r) >= 2 and isinstance(r[1], dict) and r[1].get("hit_id"):
                verified.add(r[1]["hit_id"])
        print(f"only-verified: 加载 {len(verified)} 个有数据 ID")
    con = sqlite3.connect(DB)
    for v in varieties:
        path = os.path.join(ROOT, "translation-workspace", "mapping", v, "step2_match_%s.json" % v)
        if not os.path.exists(path):
            print(f"{v}: 无映射")
            continue
        d = json.load(open(path))
        rows = []
        for k, vv in d.items():
            if vv.get("grade") not in ("A", "B"):
                continue
            hid = vv.get("hit_id")
            if not hid:
                continue
            if args.only_verified and hid not in verified:
                continue
            rows.append((hid, vv.get("name", "") or vv.get("hit_name", "")))
        # 去重
        seen = set()
        uniq = []
        for hid, nm in rows:
            if hid in seen:
                continue
            seen.add(hid)
            uniq.append((hid, nm))
        print(f"{v}: 待灌 {len(uniq)} 条", flush=True)
        ok = 0
        for i, (hid, nm) in enumerate(uniq):
            r = load_one(con, v, hid, nm)
            if r[1] > 0:
                ok += 1
            else:
                print(f"  [空] {v} {nm[:34]} -> {hid} ({r[2]})", flush=True)
            time.sleep(RATE)
        print(f"{v}: 灌入 {ok}/{len(uniq)}", flush=True)
    con.close()
    print("全部完成")

if __name__ == "__main__":
    main()
