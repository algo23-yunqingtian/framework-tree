#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B 三品种 LI/SI/SN 的 A 级语义校验 + 系列实测。
  1) 语义校验：hit_name 含品种关键词的保留 A 级，否则降级到 B 或剔除
  2) series 实测：对语义通过且 grade=A/B 的 hit_id 拉 series 确认有数据

输出：/tmp/series_ok.json
     translation-workspace/mapping/{V}/step2_match_{V}.json（原地降级/剔除）
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZHJ = os.path.expanduser("~/.hermes/scripts/zhiji_api.py")

VARIETY_KW = {
    "LI": ["碳酸锂", "氢氧化锂", "锂电池", "电池级", "工业级", "锂"],
    "SI": ["工业硅", "有机硅", "多晶硅", "硅"],
    "SN": ["锡", "焊锡", "精锡"],
}
NEG_KW = {
    "LI": ["铅", "铜", "铝", "锌", "镍", "锡", "工业硅", "水泥", "溴化锂"],
    "SI": ["铅", "铜", "铝", "锌", "镍", "锂"],
    "SN": ["铅", "铜", "铝", "锌", "镍", "锂", "工业硅"],
}


def zhiji_series(zid, start="2021-01-01", end="2026-12-31"):
    r = subprocess.run(["/usr/bin/python3", ZHJ, "series", zid, start, end],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout, strict=False)
    except Exception:
        return None


def semantic_ok(v, hit_name, name):
    hay = (hit_name or "") + "|" + (name or "")
    main_kw = VARIETY_KW[v]
    neg = NEG_KW[v]
    if any(kw in hay for kw in neg):
        return False
    return any(kw in hay for kw in main_kw)


def main():
    verified = []
    for v in ["LI", "SI", "SN"]:
        path = os.path.join(ROOT, "translation-workspace", "mapping", v,
                            "step2_match_%s.json" % v)
        if not os.path.exists(path):
            print(f"{v}: 无映射，跳过", flush=True)
            continue
        d = json.load(open(path, encoding="utf-8"))

        kept_ids = []
        to_pop = []
        for k, vv in d.items():
            grade = vv.get("grade")
            if grade not in ("A", "B"):
                continue
            hid = vv.get("hit_id")
            if not hid:
                continue
            ok = semantic_ok(v, vv.get("hit_name", ""), vv.get("name", ""))
            if ok:
                kept_ids.append(hid)
            else:
                if grade == "A":
                    vv["grade"] = "B"
                    print(f"  降级 A→B [{v}] {vv.get('name','')[:30]} | {vv.get('hit_name','')[:40]}", flush=True)
                else:
                    to_pop.append(k)
                    print(f"  剔除 B [{v}] {vv.get('name','')[:30]} | {vv.get('hit_name','')[:40]}", flush=True)
        for k in to_pop:
            d.pop(k, None)

        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

        # series 实测
        seen = set()
        uniq = []
        for hid in kept_ids:
            if hid in seen:
                continue
            seen.add(hid)
            uniq.append(hid)

        print(f"\n{v}: 语义保留 {len(uniq)} 条，开始 series 实测...")
        for i, hid in enumerate(uniq):
            try:
                data = zhiji_series(hid)
                if data and data.get("points"):
                    verified.append({"variety": v, "hit_id": hid, "n": len(data["points"]), "ok": True})
                    print(f"  [{i+1}/{len(uniq)}] OK {hid}  n={len(data['points'])}", flush=True)
                else:
                    verified.append({"variety": v, "hit_id": hid, "n": 0, "ok": False})
                    print(f"  [{i+1}/{len(uniq)}] 空  {hid}", flush=True)
            except Exception as e:
                verified.append({"variety": v, "hit_id": hid, "n": 0, "ok": False, "err": str(e)})
                print(f"  [{i+1}/{len(uniq)}] ERR {hid}: {e}", flush=True)
            time.sleep(0.4)

    out_path = "/tmp/series_ok.json"
    json.dump(verified, open(out_path, "w"))
    ok_n = sum(1 for x in verified if x["ok"])
    print(f"\n写入 {out_path} 共 {len(verified)} 条，有数据 {ok_n} / 无数据 {len(verified)-ok_n}")


if __name__ == "__main__":
    main()