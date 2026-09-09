#!/usr/bin/env python3
"""
拉 wr* (周报指标) 已 verified 的数据进 api_cache.db。
refresh_cache.py 只认 i*/j*/cu_/al_ 前缀，wr* 需独立脚本。
用法: python3 fetch_wr_cache.py wr34,wr35,wr38,wr40
"""
import subprocess, sys, json, sqlite3, time
from pathlib import Path

DB = Path("/home/ubuntu/framework-tree/scripts/api_cache.db")
ZHJI = Path.home() / ".hermes" / "scripts" / "zhiji_api.py"
IND = Path("/home/ubuntu/framework-tree/data/indicators_v1.json")

def zhiji_series(zid, start, end):
    r = subprocess.run([sys.executable, str(ZHJI), "series", zid, start, end],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None, r.stderr[:200]
    try:
        return json.loads(r.stdout, strict=False), None
    except Exception as e:
        return None, str(e)

def main():
    wanted = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    meta = json.loads(IND.read_text(encoding="utf-8"))
    wr = {k: v for k, v in meta.items() if k.startswith("wr") and v.get("verified")}
    if wanted:
        wr = {k: v for k, v in wr.items() if k in wanted}
    con = sqlite3.connect(str(DB))
    start, end = "2018-01-01", "2026-09-01"
    print(f"[INFO] 拉取 {len(wr)} 个 wr* 指标 → api_cache.db (code=AO)")
    ok = 0
    for i, (mid, entry) in enumerate(wr.items()):
        ids = entry.get("ids", {})
        # wr 的 ids key 可能是 AL-AX 或标准 code，取第一个值
        zid = next(iter(ids.values()), None)
        if not zid:
            print(f"  ✗ {mid}: 无 ID")
            continue
        if i > 0:
            time.sleep(1.1)
        data, err = zhiji_series(zid, start, end)
        if err or not data or "error" in data:
            print(f"  ✗ {mid} {zid}: {err or data.get('error','')}"[:80])
            continue
        pts = [{"date": p["date"], "value": p["value"]} for p in data.get("points", [])
               if isinstance(p, dict) and p.get("date") and p.get("value") is not None]
        if not pts:
            print(f"  ✗ {mid} {zid}: 空数据")
            continue
        payload = {"id": data.get("id", zid), "source": data.get("source",""),
                   "name": data.get("name", entry.get("name")),
                   "unit": data.get("unit", entry.get("unit","")),
                   "freq": data.get("frequency", entry.get("freq","")),
                   "points": pts}
        con.execute("INSERT OR REPLACE INTO indicator_cache(code,metric,zhiji_id,data_json,name,unit,freq,fetched_at) "
                    "VALUES (?,?,?,?,?,?,?,datetime('now'))",
                    ("AO", mid, zid, json.dumps(payload, ensure_ascii=False),
                     payload["name"], payload["unit"], payload["freq"]))
        latest = max(p["date"] for p in pts)
        print(f"  ✓ {mid} {zid}: {len(pts)} pts, {pts[-1]['date']}~{latest}, unit={payload['unit']}")
        ok += 1
    con.commit()
    con.close()
    print(f"\n[OK] {ok}/{len(wr)} 成功")

if __name__ == "__main__":
    main()
