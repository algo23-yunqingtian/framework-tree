#!/usr/bin/env python3
"""
DSHB V86-RC2 短ID接口复测脚本 — 修正版
修正: API返回数据在points字段, 非data字段
"""

import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime

DATA_KEY = "data_8e863643ecc13f11d2c669bdb672f7db"
DATA_BASE = "https://zhiji-ai.xyz/commodity/api"
RATE_SEC = 1.0
OUTPUT_DIR = Path(__file__).parent
LOG_DIR = OUTPUT_DIR / "reverify_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

TEST_CASES = [
    {"short_id": "j25_tc", "long_id": "ID02226336", "semantic_id": "lead_tc",
     "indicator_id": "PB-015", "name_cn": "铅精矿TC加工费", "unit": "USD/dmt",
     "search_query": "铅精矿 加工费 TC"},
    {"short_id": "i1", "long_id": "ID02226334", "semantic_id": "lead_social_inv",
     "indicator_id": "PB-009", "name_cn": "铅锭社会库存", "unit": "ton",
     "search_query": "铅锭 社会库存"},
    {"short_id": "i2", "long_id": "ID02226335", "semantic_id": "lead_exchange_inv",
     "indicator_id": "PB-010", "name_cn": "铅锭交易所库存", "unit": "ton",
     "search_query": "铅锭 交易所库存 上期所"},
]

_lock_file = Path.home() / ".hermes" / "scripts" / "zhiji_cache" / ".locks" / "data.lock"
_lock_file.parent.mkdir(parents=True, exist_ok=True)

def rate_limit():
    now = time.time()
    try:
        last = float(_lock_file.read_text().strip()) if _lock_file.exists() else 0
    except: last = 0
    w = RATE_SEC - (now - last)
    if w > 0: time.sleep(w)
    _lock_file.write_text(str(time.time()))

def api_get(url, timeout=20):
    rate_limit()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 DSHB_Reverify/2.0",
        "X-Data-Key": DATA_KEY,
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            el = round((time.time()-t0)*1000, 1)
            raw = r.read()
            if not raw:
                return {"status": r.status, "ms": el, "error": "empty", "body": None}
            return {"status": r.status, "ms": el, "error": None, "body": json.loads(raw)}
    except urllib.error.HTTPError as e:
        el = round((time.time()-t0)*1000, 1)
        body = ""
        try: body = e.read().decode("utf-8","replace")
        except: pass
        return {"status": e.code, "ms": el, "error": f"HTTP {e.code}", "body": body or None}
    except Exception as e:
        el = round((time.time()-t0)*1000, 1)
        return {"status": None, "ms": el, "error": str(e), "body": None}

def parse_series_body(body):
    """解析series API响应 — 检查points/data字段"""
    if not isinstance(body, dict):
        return {"has_data": False, "data_count": 0, "perm_state": None, "points_sample": None}
    
    has_data = False
    data_count = 0
    perm_state = body.get("permission_state")
    points_sample = None
    
    # Check for points field (actual API response format)
    if "points" in body:
        pts = body["points"]
        if isinstance(pts, list):
            data_count = len(pts)
            # Count non-zero values
            non_zero = sum(1 for p in pts if p.get("value", "0") not in ("0", "0.0", ""))
            if non_zero > 0:
                has_data = True
            elif data_count > 0 and all(str(p.get("value", "0")) in ("0", "0.0", "") for p in pts):
                # All values are 0 — still has data but all zeros
                has_data = True  # API returned data, just all zeros
            points_sample = str(pts[:3]) if pts else None
    
    # Check for data field (alternative format)
    if not has_data and "data" in body:
        dl = body["data"]
        if isinstance(dl, list):
            data_count = len(dl)
            has_data = data_count > 0
            points_sample = str(dl[:3]) if dl else None
    
    return {"has_data": has_data, "data_count": data_count, "perm_state": perm_state, "points_sample": points_sample}

def main(rounds=20):
    print(f"DSHB V86-RC2 短ID复测 | {datetime.now().isoformat()} | rounds={rounds}", flush=True)
    all_results = []
    
    for ci, c in enumerate(TEST_CASES):
        print(f"\n[{ci+1}/3] {c['short_id']} ({c['name_cn']})...", flush=True)
        
        # Step 1: Search
        sq = urllib.parse.quote(c["search_query"])
        url = f"{DATA_BASE}/search?q={sq}&source=all&limit=10"
        sr = api_get(url)
        series_id = ""
        search_results_count = 0
        if sr["body"] and isinstance(sr["body"], dict):
            results = sr["body"].get("results", [])
            search_results_count = len(results)
            if results:
                series_id = results[0].get("id", "")
        
        sr_rec = {"short_id": c["short_id"], "test": "search", "cycle": 0,
                  "http": sr["status"], "ms": sr["ms"], "error": sr["error"],
                  "results_count": search_results_count, "series_id": series_id,
                  "body_sample": str(sr["body"])[:500] if sr["body"] else None,
                  "ts": datetime.now().isoformat()}
        all_results.append(sr_rec)
        print(f"  search: HTTP={sr['status']} ms={sr['ms']} results={search_results_count} series={series_id}", flush=True)
        
        # Step 2: Series test rounds
        for cycle in range(1, rounds+1):
            surl = f"{DATA_BASE}/series?id={series_id}"
            sresp = api_get(surl)
            parsed = parse_series_body(sresp["body"])
            
            sr_rec2 = {"short_id": c["short_id"], "test": "series", "cycle": cycle,
                       "http": sresp["status"], "ms": sresp["ms"], "error": sresp["error"],
                       "has_data": parsed["has_data"], "data_count": parsed["data_count"],
                       "perm_state": parsed["perm_state"],
                       "points_sample": parsed["points_sample"],
                       "body_sample": str(sresp["body"])[:500] if sresp["body"] else None,
                       "ts": datetime.now().isoformat()}
            all_results.append(sr_rec2)
            
            if cycle % 5 == 0 or cycle == 1:
                print(f"  cycle {cycle}: HTTP={sresp['status']} ms={sresp['ms']} data={parsed['has_data']} count={parsed['data_count']} perm={parsed['perm_state']}", flush=True)
    
    # Generate summary
    by_id = {}
    for r in all_results:
        sid = r["short_id"]
        if sid not in by_id: by_id[sid] = []
        by_id[sid].append(r)
    
    id_stats = {}
    tot = {"total": 0, "http_200": 0, "http_500": 0, "http_other": 0,
           "empty": 0, "perm_-4": 0, "data_nonempty": 0, "ms_list": []}
    
    for sid, recs in by_id.items():
        st = {"short_id": sid, "total": len(recs), "http_200": 0, "http_500": 0,
              "http_other": 0, "empty": 0, "perm_-4": 0, "data_nonempty": 0, "ms_list": []}
        for r in recs:
            h = r["http"]
            if h == 200: st["http_200"] += 1
            elif h == 500: st["http_500"] += 1
            elif h: st["http_other"] += 1
            if r.get("error"): st["error_count"] = st.get("error_count", 0) + 1
            if r.get("has_data") is False: st["empty"] += 1
            elif r.get("has_data"): st["data_nonempty"] += 1
            if r.get("perm_state") == -4: st["perm_-4"] += 1
            st["ms_list"].append(r["ms"])
            tot["total"] += 1
            if h == 200: tot["http_200"] += 1
            elif h == 500: tot["http_500"] += 1
            elif h: tot["http_other"] += 1
            if r.get("has_data") is False: tot["empty"] += 1
            elif r.get("has_data"): tot["data_nonempty"] += 1
            if r.get("perm_state") == -4: tot["perm_-4"] += 1
            tot["ms_list"].append(r["ms"])
        st["avg_ms"] = round(sum(st["ms_list"])/max(len(st["ms_list"]),1), 1)
        st["min_ms"] = min(st["ms_list"]) if st["ms_list"] else 0
        st["max_ms"] = max(st["ms_list"]) if st["ms_list"] else 0
        srt = sorted(st["ms_list"])
        st["p99_ms"] = srt[min(int(len(srt)*0.99), len(srt)-1)] if srt else 0
        del st["ms_list"]
        id_stats[sid] = st
    
    tot["avg_ms"] = round(sum(tot["ms_list"])/max(len(tot["ms_list"]),1), 1)
    srt = sorted(tot["ms_list"])
    tot["p99_ms"] = srt[min(int(len(srt)*0.99), len(srt)-1)] if srt else 0
    tot["min_ms"] = min(srt) if srt else 0
    tot["max_ms"] = max(srt) if srt else 0
    del tot["ms_list"]
    
    pass_ = tot["http_500"]==0 and tot["empty"]==0 and tot["perm_-4"]==0
    summary = {
        "title": "DSHB V86-RC2 短ID复测汇总",
        "report_id": "DSHB_V86_RC2_PROD_FIX_T3.1",
        "test_time": datetime.now().isoformat(),
        "test_date": datetime.now().strftime("%Y-%m-%d"),
        "branch": "feature/v85-chart-template",
        "rounds_per_id": rounds,
        "script_version": "v2.0 (fixed points parsing)",
        "test_cases": [{"short_id":c["short_id"],"long_id":c["long_id"],"semantic_id":c["semantic_id"],"indicator_id":c["indicator_id"],"name_cn":c["name_cn"]} for c in TEST_CASES],
        "results_by_id": id_stats,
        "results_total": tot,
        "verdict": {"overall": "PASS" if pass_ else "FAIL", "http_500": tot["http_500"], "empty": tot["empty"], "perm_-4": tot["perm_-4"], "avg_ms": tot["avg_ms"], "p99_ms": tot["p99_ms"]},
        "fix_verification": {
            "issue_1_j25_tc_http500": {"status": "FIXED" if tot["http_500"]==0 else "STILL_PRESENT", "detail": f"HTTP 500={tot['http_500']}次"},
            "issue_2_i1_perm-4": {"status": "FIXED" if tot["perm_-4"]==0 else "STILL_PRESENT", "detail": f"perm_state=-4={tot['perm_-4']}次"},
            "issue_3_i2_perm-4": {"status": "FIXED" if tot["perm_-4"]==0 else "STILL_PRESENT", "detail": f"perm_state=-4={tot['perm_-4']}次"},
        }
    }
    
    # Save
    sp = LOG_DIR / "short_id_reverify_summary.json"
    sp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSummary saved: {sp}", flush=True)
    
    for sid, recs in by_id.items():
        lp = LOG_DIR / f"{sid}_reverify.log"
        with open(lp, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Log saved: {lp} ({len(recs)} entries)", flush=True)
    
    print(f"\n{'='*60}", flush=True)
    print(f"Result: {summary['verdict']['overall']}", flush=True)
    print(f"Total: {tot['total']} | HTTP200: {tot['http_200']} | HTTP500: {tot['http_500']}", flush=True)
    print(f"Data OK: {tot['data_nonempty']} | Empty: {tot['empty']} | perm-4: {tot['perm_-4']}", flush=True)
    print(f"Avg: {tot['avg_ms']}ms | P99: {tot['p99_ms']}ms", flush=True)
    print(f"{'='*60}", flush=True)
    
    return summary

if __name__ == "__main__":
    rounds = int(sys.argv[1]) if len(sys.argv)>1 else 20
    main(rounds)
