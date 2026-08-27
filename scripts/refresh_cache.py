#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_cache.py — 统一缓存刷新脚本（v1.3 合并版）
===================================================
合并 refresh_cache_i6_i18.py + refresh_v4_new_ids.py，单一真源 = data/indicators_v1.json。

用法:
  python3 refresh_cache.py                      # 刷新 PB 全部 verified=true 的 i 指标
  python3 refresh_cache.py --metrics i6,i7,i8   # 只刷新指定指标
  python3 refresh_cache.py --code ZN            # 刷新其他品种（需 JSON 内已有 ids.ZN）
  python3 refresh_cache.py --since 2018-01-01 --until 2026-09-01

行为:
  读 indicators_v1.json → 取 verified=true 且有 code 品种 ID 的条目
  → 逐个系列拉取 → INSERT OR REPLACE 写入 api_cache.db → 1 秒限频 → 汇总表
"""
import subprocess, sys, json, sqlite3, os, time, argparse
from pathlib import Path

DB = Path("/home/ubuntu/framework-tree/scripts/api_cache.db")
ZHJI = Path.home() / ".hermes" / "scripts" / "zhiji_api.py"
INDICATOR_JSON = Path("/home/ubuntu/framework-tree/data/indicators_v1.json")

def zhiji_series(zhiji_id, start, end):
    r = subprocess.run(
        [sys.executable, str(ZHJI), "series", zhiji_id, start, end],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        return None, r.stderr[:200]
    try:
        return json.loads(r.stdout, strict=False), None
    except Exception as e:
        return None, str(e)

def build_points(pts_raw):
    return [{"date": p["date"], "value": p["value"]} for p in pts_raw
            if isinstance(p, dict) and p.get("date") and p.get("value") is not None]

def refresh_one(con, code, mid, meta, start, end):
    """拉取单个指标并写缓存。返回 (mid, zhiji_id, n_pts, latest, err)
    注意: zhiji series 返回 points 为倒序(最新在前)，pts[-1] 是最早点；
    latest 用 max() 取真实最新日期。"""
    zhiji_id = meta["ids"].get(code)
    if not zhiji_id:
        return (mid, None, 0, "-", f"无{code} ID")
    data, err = zhiji_series(zhiji_id, start, end)
    if err or not data:
        return (mid, zhiji_id, 0, "-", err or "空响应")
    pts = build_points(data.get("points", []))
    if not pts:
        return (mid, zhiji_id, 0, "-", "空数据")
    payload = {
        "id": data.get("id", zhiji_id),
        "source": data.get("source", ""),
        "name": data.get("name", meta["name"]),
        "unit": data.get("unit", meta.get("unit", "")),
        "freq": data.get("frequency", meta.get("freq", "")),
        "points": pts,
    }
    con.execute(
        "INSERT OR REPLACE INTO indicator_cache(code, metric, zhiji_id, data_json, name, unit, freq, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        (code, mid, zhiji_id, json.dumps(payload, ensure_ascii=False),
         payload["name"], payload["unit"], payload["freq"])
    )
    latest = max(p["date"] for p in pts) if pts else "-"
    return (mid, zhiji_id, len(pts), latest, None)

def main():
    ap = argparse.ArgumentParser(description="统一缓存刷新")
    ap.add_argument("--metrics", default=None, help="逗号分隔的指标列表，如 i6,i7,i8；默认全部 verified")
    ap.add_argument("--code", default="PB", help="品种代码，默认 PB")
    ap.add_argument("--since", default="2018-01-01")
    ap.add_argument("--until", default="2026-09-01")
    args = ap.parse_args()

    meta = json.loads(INDICATOR_JSON.read_text(encoding="utf-8"))
    i_entries = {k: v for k, v in meta["indicators"].items() if k.startswith("i")}
    if args.metrics:
        wanted = set(m.strip() for m in args.metrics.split(","))
        i_entries = {k: v for k, v in i_entries.items() if k in wanted}

    targets = [(mid, m) for mid, m in i_entries.items()
               if m.get("verified") and m.get("ids", {}).get(args.code)]
    if not targets:
        print(f"⚠ 无满足条件指标: code={args.code} metrics={args.metrics or 'all'}")
        sys.exit(1)

    con = sqlite3.connect(str(DB))
    summary = []
    print(f"[INFO] 开始刷新 {len(targets)} 个 {args.code} 指标 → api_cache.db")
    for mid, entry in targets:
        print(f"[{mid}] {entry['name']} ← {entry['ids'][args.code]}")
        r = refresh_one(con, args.code, mid, entry, args.since, args.until)
        if r[4]:
            print(f"  ✗ {r[4]}")
        else:
            print(f"  ✓ {r[2]} pts, latest={r[3]}")
        summary.append(r)
        time.sleep(1.0)

    con.commit()
    con.close()
    print("\n========== SUMMARY ==========")
    print(f"{'id':<6} {'zhiji_id':<16} {'n':>6} {'latest':<12} note")
    print("-" * 64)
    for mid, zid, n, ld, err in summary:
        print(f"{mid:<6} {str(zid):<16} {n:>6} {str(ld):<12} {err or 'ok'}")
    ok = sum(1 for s in summary if not s[4])
    print(f"\n[OK] {ok}/{len(summary)} 成功")

if __name__ == "__main__":
    main()