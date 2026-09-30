#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t21_fetch_zhiji.py — T2.1 zhiji 真实时序批量拉取

功能:
  1. 从 DSHB 交付模板包提取全部 zhiji_id（含 VALID/FILLED/INVALID）
  2. 去重后按 1s 限速批量调用 zhiji_api.py series 拉取真实时序
  3. 结果落本地 JSON 缓存（可断点续跑），失败记录原因
  4. 输出 fetch_summary.json 供后续渲染消费

约束（T4）:
  - 仅测试分支 feature/v85-chart-template
  - 不修改 indicators_v1.json / tree_config.json
  - 不接生产发布
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ZHIJI_API = os.path.expanduser("~/.hermes/scripts/zhiji_api.py")
PKG_DIR = Path(__file__).resolve().parent
TEMPLATE_JSON = PKG_DIR / "pdf_web_chart_template_hermes_ready.json"
FETCH_DIR = PKG_DIR / "zhiji_data_cache"
SUMMARY_JSON = PKG_DIR / "fetch_summary.json"
PROGRESS_JSON = PKG_DIR / "fetch_progress.json"

DATE_START = "2021-01-01"
DATE_END = "2026-08-31"
RATE_LIMIT_SEC = 1.0   # zhiji 1秒限频
TIMEOUT_SEC = 90


def load_unique_ids():
    """从模板包提取唯一 zhiji_id → {id: [series_name, ...]}"""
    with open(TEMPLATE_JSON, encoding="utf-8") as f:
        data = json.load(f)

    id_map = {}
    for t in data["templates"]:
        for s in t.get("series", []):
            zid = s.get("zhiji_id")
            if not zid:
                continue
            id_map.setdefault(zid, {"names": [], "verify_status": set(), "templates": set()})
            id_map[zid]["names"].append(s.get("name", ""))
            id_map[zid]["verify_status"].add(s.get("verify_status", ""))
            id_map[zid]["templates"].add(t["template_id"])
    return data, id_map


def fetch_one(zhiji_id: str, retries: int = 2):
    """调用 zhiji_api.py series 拉取单个指标时序，返回 (ok, data_or_err)"""
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(
                ["python3", ZHIJI_API, "series", zhiji_id, DATE_START, DATE_END],
                capture_output=True, text=True, timeout=TIMEOUT_SEC,
            )
            out = (r.stdout or "").strip()
            if r.returncode != 0 or not out:
                err = (r.stderr or out or "empty output")[:200]
                if attempt < retries:
                    time.sleep(2)
                    continue
                return False, {"error": err, "returncode": r.returncode}

            payload = json.loads(out)
            if "error" in payload:
                if attempt < retries:
                    time.sleep(2)
                    continue
                return False, {"error": payload["error"]}

            points = payload.get("points", [])
            return True, {
                "id": zhiji_id,
                "name": payload.get("name", ""),
                "unit": payload.get("unit", ""),
                "frequency": payload.get("frequency", ""),
                "source": payload.get("source", ""),
                "data_start": payload.get("data_start", ""),
                "data_latest": payload.get("data_latest", ""),
                "points": [[p["date"], _to_float(p.get("value"))] for p in points],
                "point_count": len(points),
            }
        except subprocess.TimeoutExpired:
            if attempt < retries:
                time.sleep(2)
                continue
            return False, {"error": "timeout"}
        except json.JSONDecodeError as e:
            return False, {"error": f"json_decode: {e}"}
        except Exception as e:  # noqa: BLE001
            return False, {"error": f"{type(e).__name__}: {e}"}
    return False, {"error": "exhausted_retries"}


def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def main():
    FETCH_DIR.mkdir(parents=True, exist_ok=True)
    data, id_map = load_unique_ids()
    unique_ids = sorted(id_map.keys())
    total = len(unique_ids)

    print(f"=== T2.1 zhiji 批量拉取 ===")
    print(f"模板总数: {len(data['templates'])}")
    print(f"唯一 zhiji_id: {total}")

    # 断点续跑：跳过已缓存成功的
    ok_ids, fail_ids = [], []
    failed = {}
    start = time.time()

    for i, zid in enumerate(unique_ids, 1):
        cache = FETCH_DIR / f"{zid}.json"
        if cache.exists():
            try:
                with open(cache, encoding="utf-8") as f:
                    cached = json.load(f)
                if cached.get("ok"):
                    ok_ids.append(zid)
                    continue
            except (json.JSONDecodeError, KeyError):
                pass

        ok, payload = fetch_one(zid)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"ok": ok, "id": zid, "data": payload}, f, ensure_ascii=False)

        if ok:
            ok_ids.append(zid)
            status = f"OK {payload.get('point_count', 0)}pts"
        else:
            fail_ids.append(zid)
            failed[zid] = payload.get("error", "unknown")[:200]
            status = f"FAIL {failed[zid][:60]}"

        if i % 10 == 0 or i == total:
            el = time.time() - start
            rate = i / el if el > 0 else 0
            eta = (total - i) / rate if rate > 0 else 0
            print(f"[{i}/{total}] {zid} -> {status} | {rate:.2f}/s eta {eta:.0f}s")

        with open(PROGRESS_JSON, "w", encoding="utf-8") as f:
            json.dump({"done": i, "total": total, "ok": len(ok_ids), "fail": len(fail_ids)}, f)

        time.sleep(RATE_LIMIT_SEC)

    elapsed = time.time() - start
    summary = {
        "task": "T2.1 zhiji bulk fetch",
        "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_sec": round(elapsed, 1),
        "date_range": [DATE_START, DATE_END],
        "total_unique_ids": total,
        "success": len(ok_ids),
        "failed": len(fail_ids),
        "success_rate": round(len(ok_ids) / total * 100, 2) if total else 0,
        "failed_detail": failed,
        "id_status_map": {
            zid: {
                "names": id_map[zid]["names"],
                "verify_status": sorted(id_map[zid]["verify_status"]),
                "templates": sorted(id_map[zid]["templates"]),
                "fetch_ok": zid in ok_ids,
            }
            for zid in unique_ids
        },
    }
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n=== 拉取完成 ===")
    print(f"耗时: {elapsed:.0f}s ({total} IDs)")
    print(f"成功: {len(ok_ids)} | 失败: {len(fail_ids)} | 成功率: {summary['success_rate']}%")
    if failed:
        print(f"失败明细:")
        for zid, err in failed.items():
            print(f"  {zid}: {err}")
    print(f"摘要: {SUMMARY_JSON}")

    return 0 if len(fail_ids) < total else 1


if __name__ == "__main__":
    sys.exit(main())
