#!/usr/bin/env python3
"""按 v4 定稿刷新 api_cache：补充 v4 新增的关键 zhiji_id。"""
import subprocess, sys, json, sqlite3, os, time
from pathlib import Path

DB = Path("/home/ubuntu/framework-tree/scripts/api_cache.db")
ZHJI = Path.home() / ".hermes" / "scripts" / "zhiji_api.py"
IND = Path("/home/ubuntu/framework-tree/data/indicators_v1.json")

meta = json.loads(IND.read_text(encoding="utf-8"))
meta_by_id = {k: v for k, v in meta["indicators"].items() if k.startswith("i")}

# v4 定稿新增的 zhiji_id（indicators_v1.json 里没覆盖到的 v4 新发现）
# 用 v4_zhiji_verified_20260827.json 里的 A 命中 ID 追加
V4_NEW = [
    # key=指标码,  value=(name, zhiji_id, unit, freq)
    ("i19", ("LME铅注册仓单_新加坡",       "FU00023414", "吨",   "daily")),
    ("i20", ("LME铅注销仓单_新加坡",       "FU00023622", "吨",   "daily")),
    ("i21", ("LME铅分仓库注册_新加坡",     "a10017113",  "吨",   "daily")),
    ("i22", ("LME铅分仓库注销_新加坡",     "a10017166",  "吨",   "daily")),
    ("i23", ("LME铅非仓单_亚洲新加坡(隐性)", "FU00103556", "吨", "daily")),
    ("i24", ("LME铅入库量_新加坡",         "FU00023194", "吨",   "daily")),
    ("i25", ("LME铅出库量_新加坡",         "FU00022450", "吨",   "daily")),
    ("i29", ("LME铅注册仓单_仁川",         "a10100437",  "吨",   "daily")),
    ("i30", ("LME铅非注册仓单_迪拜",       "a12809923",  "吨",   "daily")),
    ("i31", ("铅锭现货库存_全国(Mysteel)", "ID00188315", "万吨", "daily")),
]

def zhiji_series(zid, start="2018-01-01", end="2026-09-01"):
    r = subprocess.run(
        [sys.executable, str(ZHJI), "series", zid, start, end],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        return None, r.stderr[:200]
    try:
        return json.loads(r.stdout, strict=False), None
    except Exception as e:
        return None, str(e)

con = sqlite3.connect(str(DB))
summary = []
for key, (name, zid, unit, freq) in V4_NEW:
    print(f"[{key}] {name} ← {zid}")
    data, err = zhiji_series(zid)
    if err or not data:
        print(f"  ✗ {err}")
        summary.append((key, zid, 0, "-", err))
        continue
    pts = [{"date": p["date"], "value": p["value"]} for p in data.get("points", [])
           if isinstance(p, dict) and p.get("date") and p.get("value") is not None]
    if not pts:
        print(f"  ✗ 空数据")
        summary.append((key, zid, 0, "-", "empty"))
        continue
    payload = {"id": data.get("id", zid), "source": data.get("source", ""),
               "name": data.get("name", name), "unit": data.get("unit", unit),
               "freq": data.get("frequency", freq), "points": pts}
    con.execute(
        "INSERT OR REPLACE INTO indicator_cache(code, metric, zhiji_id, data_json, name, unit, freq, fetched_at) "
        "VALUES ('PB', ?, ?, ?, ?, ?, ?, datetime('now'))",
        (key, zid, json.dumps(payload, ensure_ascii=False),
         payload["name"], payload["unit"], payload["freq"]))
    latest = sorted(pts, key=lambda p: p["date"])[-1]["date"]
    print(f"  ✓ {len(pts)} pts, latest={latest}")
    summary.append((key, zid, len(pts), latest, None))
    time.sleep(1.0)

con.commit()
con.close()
print("\nSUMMARY:")
for k, z, n, ld, e in summary:
    print(f"  {k:<4} {z:<15} n={n:<5} latest={ld}  {e or 'ok'}")
