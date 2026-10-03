#!/usr/bin/env python3
import sys, urllib.request, urllib.error, json, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DATA_KEY = "data_8e863643ecc13f11d2c669bdb672f7db"
DATA_BASE = "https://zhiji-ai.xyz/commodity/api"

def test(id_val, label):
    time.sleep(1.2)
    url = f"{DATA_BASE}/series?id={id_val}"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 DSHB_V3/1.0","X-Data-Key":DATA_KEY})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read().decode("utf-8","replace"))
            pts = body.get("points", [])
            nz = sum(1 for p in pts if str(p.get("value","0")) not in ("0","0.0",""))
            name = body.get("name","?")
            unit = body.get("unit","?")
            print(f"{label} {id_val} => HTTP {r.status} pts={len(pts)} nz={nz} name={name[:50]} unit={unit}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace")
        print(f"{label} {id_val} => HTTP {e.code} body={body[:120]}")
    except Exception as e:
        print(f"{label} {id_val} => ERR: {e}")

print("=== Testing all 8 known long IDs ===")
for lid in ["ID02226332","ID02226333","ID02226334","ID02226335","ID02226336","ID02226337","ID02226338","ID02226339"]:
    test(lid, "LONG")
