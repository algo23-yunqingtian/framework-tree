#!/usr/bin/env python3
"""Step3 拉数: 为新增的 cu_*/al_* 指标拉取知几 series 数据入库。

不改公共 refresh_cache.py 的 verified 逻辑, 独立跑:
  - 筛 indicators_v1.json 里带 _origin (Step3 新增) 的条目
  - 逐个拉 series (1.2s 限频, 与 search 阶段一致)
  - 成功 → INSERT api_cache.db + 置 verified=true
  - 失败 → 记录原因, 保留 verified=false (agent 可做备用库)
输出: analysis/iwencai/step3_fetch_report.json + 控制台汇总
"""
import argparse, json, os, sqlite3, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "scripts" / "api_cache.db"
ZHJI = Path.home() / ".hermes" / "scripts" / "zhiji_api.py"
IND = REPO / "data" / "indicators_v1.json"
OUT = REPO / "analysis" / "iwencai" / "step3_fetch_report.json"

START = "2015-01-01"
END = "2026-08-30"


def zhiji_series(zid, start, end):
    r = subprocess.run([sys.executable, str(ZHJI), "series", zid, start, end],
                       capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        return None, (r.stderr or "")[:160]
    try:
        return json.loads(r.stdout, strict=False), None
    except Exception as e:
        return None, str(e)


def build_points(pts):
    return [{"date": p["date"], "value": p["value"]} for p in pts
            if isinstance(p, dict) and p.get("date") and p.get("value") is not None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default=None, help="只拉 CU 或 AL")
    ap.add_argument("--limit", type=int, default=0, help="限制条数(调试用)")
    ap.add_argument("--resume", action="store_true", help="跳过已成功的")
    args = ap.parse_args()

    doc = json.load(open(IND, encoding="utf-8"))
    ind = doc["indicators"]

    # 已有缓存的 (code, metric)
    con = sqlite3.connect(str(DB))
    cached = set()
    try:
        for row in con.execute("SELECT code, metric FROM indicator_cache"):
            cached.add((row[0], row[1]))
    except sqlite3.OperationalError:
        pass

    # 待拉: 带 _origin 的新增条目
    targets = []
    for mid, meta in ind.items():
        if not meta.get("_origin"):
            continue
        for code, zid in (meta.get("ids") or {}).items():
            if not zid:
                continue
            if args.code and code != args.code:
                continue
            targets.append((mid, code, zid, meta))
    if args.limit:
        targets = targets[:args.limit]

    report = {}
    if args.resume and OUT.exists():
        report = json.load(open(OUT, encoding="utf-8"))

    ok = fail = skip = 0
    print("=== Step3 拉数: %d 条待处理 (已缓存 %d 跳过) ==="
          % (len(targets), sum(1 for t in targets if (t[1], t[0]) in cached)))
    for i, (mid, code, zid, meta) in enumerate(targets, 1):
        key = "%s:%s" % (code, mid)
        if (code, mid) in cached:
            skip += 1
            continue
        if args.resume and report.get(key, {}).get("ok"):
            skip += 1
            continue
        data, err = zhiji_series(zid, START, END)
        if err or not data:
            fail += 1
            report[key] = {"ok": False, "metric": mid, "code": code,
                           "zhiji_id": zid, "err": err or "空响应"}
            print("  [%d/%d] FAIL %s %s -> %s" % (i, len(targets), code, mid, (err or "")[:40]))
            continue
        pts = build_points(data.get("points", []))
        if not pts:
            fail += 1
            report[key] = {"ok": False, "metric": mid, "code": code,
                           "zhiji_id": zid, "err": "空数据"}
            continue
        pts_sorted = sorted(pts, key=lambda p: p["date"], reverse=True)  # 与已有缓存一致: 倒序(最新在前)
        payload = {
            "id": data.get("id", zid), "source": data.get("source", ""),
            "name": data.get("name", meta.get("name", "")),
            "unit": data.get("unit", meta.get("unit", "")),
            "frequency": data.get("frequency", meta.get("freq", "")),
            "src_org": data.get("src_org", ""),
            "data_start": data.get("data_start", pts_sorted[-1]["date"] if pts_sorted else ""),
            "data_latest": data.get("data_latest", pts_sorted[0]["date"] if pts_sorted else ""),
            "points": pts_sorted,
        }
        con.execute(
            "INSERT INTO indicator_cache (code, metric, zhiji_id, data_json, fetched_at, name, unit, freq) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (code, mid, zid, json.dumps(payload, ensure_ascii=False),
             __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             payload["name"], payload["unit"], payload["frequency"]))
        con.commit()
        ok += 1
        # 拉数成功 → 置 verified
        ind[mid]["verified"] = True
        report[key] = {"ok": True, "metric": mid, "code": code, "zhiji_id": zid,
                       "n_points": len(pts_sorted),
                       "latest": pts_sorted[-1]["date"],
                       "first": pts_sorted[0]["date"]}
        if i % 10 == 0 or i == len(targets):
            json.dump(report, open(OUT, "w"), ensure_ascii=False, indent=1)
            json.dump(doc, open(IND, "w"), ensure_ascii=False, indent=1)
            print("  [%d/%d] OK %s %s -> %d点 (%s~%s)  累计 成功%d 失败%d"
                  % (i, len(targets), code, mid, len(pts_sorted),
                     pts_sorted[0]["date"], pts_sorted[-1]["date"], ok, fail))
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
    json.dump(report, open(OUT, "w"), ensure_ascii=False, indent=1)
    json.dump(doc, open(IND, "w"), ensure_ascii=False, indent=1)
    con.close()
    print("\n=== 完成: 成功 %d 失败 %d ===" % (ok, fail))
    # 更新版本变更
    doc["updated"] = "2026-08-30"
    doc["change"] = doc.get("change", "") + " | Step3 拉数入库: 成功%d 失败%d, verified置真" % (ok, fail)
    json.dump(doc, open(IND, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()