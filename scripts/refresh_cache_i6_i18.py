#!/usr/bin/env python3
"""
refresh_cache_i6_i12.py
用 indicators_v1.json (v4 已验证 ID) 刷新 api_cache.db 的 i6~i12 缓存。
用法: python3 refresh_cache_i6_i12.py
"""
import subprocess, sys, json, sqlite3, os, time
from pathlib import Path

DB = Path("/home/ubuntu/framework-tree/scripts/api_cache.db")
ZHJI = Path.home() / ".hermes" / "scripts" / "zhiji_api.py"
INDICATOR_JSON = Path("/home/ubuntu/framework-tree/data/indicators_v1.json")

# 从 indicators_v1.json 读 v4 已验证 ID
meta = json.loads(INDICATOR_JSON.read_text(encoding="utf-8"))
meta_by_id = {k: v for k, v in meta["indicators"].items() if k.startswith("i")}

def zhiji_series(zhiji_id, start="2018-01-01", end="2026-09-01"):
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

TARGETS = ["i6", "i7", "i8", "i9", "i10", "i11", "i12",
           "i13", "i14", "i15", "i16", "i17", "i18"]

con = sqlite3.connect(str(DB))
summary = []
for mid in TARGETS:
    entry = meta_by_id.get(mid)
    if not entry or not entry.get("verified"):
        print(f"⚠ {mid} 未验证或未在指标库中，跳过")
        continue
    zhiji_id = entry["ids"].get("PB")
    if not zhiji_id:
        print(f"⚠ {mid} 无 PB zhiji_id，跳过")
        continue
    print(f"\n[{mid}] {entry['name']} ← {zhiji_id}")
    data, err = zhiji_series(zhiji_id)
    if err or not data:
        print(f"  ✗ ERR: {err}")
        summary.append((mid, zhiji_id, 0, "-", err))
        continue
    pts = build_points(data.get("points", []))
    if not pts:
        print(f"  ✗ 空数据")
        summary.append((mid, zhiji_id, 0, "-", "空"))
        continue
    payload = {
        "id": data.get("id", zhiji_id),
        "source": data.get("source", ""),
        "name": data.get("name", entry["name"]),
        "unit": data.get("unit", entry.get("unit", "")),
        "freq": data.get("frequency", entry.get("freq", "")),
        "points": pts,
    }
    con.execute(
        "INSERT OR REPLACE INTO indicator_cache(code, metric, zhiji_id, data_json, name, unit, freq, fetched_at) "
        "VALUES ('PB', ?, ?, ?, ?, ?, ?, datetime('now'))",
        (mid, zhiji_id, json.dumps(payload, ensure_ascii=False),
         payload["name"], payload["unit"], payload["freq"])
    )
    latest = pts[-1]["date"]
    print(f"  ✓ {len(pts)} pts, latest={latest}")
    summary.append((mid, zhiji_id, len(pts), latest, None))
    time.sleep(1.0)

con.commit()
con.close()

print("\n========== SUMMARY ==========")
print(f"{'id':<6} {'zhiji_id':<15} {'n':>6} {'latest':<12} note")
print("-" * 60)
for mid, zid, n, ld, err in summary:
    print(f"{mid:<6} {zid:<15} {n:>6} {str(ld):<12} {err or 'ok'}")
