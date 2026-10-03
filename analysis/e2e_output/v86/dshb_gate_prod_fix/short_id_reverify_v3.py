#!/usr/bin/env python3
"""
DSHB V86-RC2 短ID接口复测脚本 — v3.0 重构版
修正: 
  1. 强制将short_id传入series API, 禁止自动替换为long_id
  2. 严格区分元数据映射成功 vs 接口真实可取数
  3. 双字段记录: requested_short_id + resolved_series_id
  4. 完整保存原始API payload
  5. 区分"元数据OK但无数据"场景

HERMES对齐: COMPLETED = 元数据映射完成 + API真实取数校验通过

约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
"""

import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DATA_KEY = "data_8e863643ecc13f11d2c669bdb672f7db"
DATA_BASE = "https://zhiji-ai.xyz/commodity/api"
RATE_SEC = 1.2
OUTPUT_DIR = Path(__file__).parent
LOG_DIR = OUTPUT_DIR / "reverify_v3_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOCK_FILE = Path.home() / ".hermes" / "scripts" / "zhiji_cache" / ".locks" / "data.lock"
_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

def rate_limit():
    now = time.time()
    try:
        last = float(_LOCK_FILE.read_text().strip()) if _LOCK_FILE.exists() else 0
    except:
        last = 0
    wait = RATE_SEC - (now - last)
    if wait > 0:
        time.sleep(wait)
    _LOCK_FILE.write_text(str(time.time()))

def api_get(url, timeout=20):
    rate_limit()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 DSHB_Reverify/3.0",
        "X-Data-Key": DATA_KEY,
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            el = round((time.time() - t0) * 1000, 1)
            raw = r.read()
            body = json.loads(raw.decode('utf-8', 'replace')) if raw else None
            return {"status": r.status, "ms": el, "error": None, "body": body}
    except urllib.error.HTTPError as e:
        el = round((time.time() - t0) * 1000, 1)
        raw = e.read().decode('utf-8', 'replace')
        try:
            body = json.loads(raw)
        except:
            body = raw
        return {"status": e.code, "ms": el, "error": f"HTTP {e.code}", "body": body}
    except Exception as e:
        el = round((time.time() - t0) * 1000, 1)
        return {"status": None, "ms": el, "error": str(e), "body": None}


def test_short_id_direct(short_id, rounds=3):
    """
    核心: 强制使用short_id作为series API唯一查询参数
    禁止任何替换/绕过逻辑
    返回: 原始API payload + 解析结果
    """
    results = []
    for cycle in range(1, rounds + 1):
        url = f"{DATA_BASE}/series?id={urllib.parse.quote(short_id)}"
        resp = api_get(url)
        
        # 解析series响应
        parsed = {"has_data": False, "data_count": 0, "non_zero_count": 0,
                  "perm_state": None, "series_id_in_response": None,
                  "points_sample": None, "error_detail": None}
        
        if resp["body"] and isinstance(resp["body"], dict):
            # 检查是否为error响应
            if "error" in resp["body"] and "points" not in resp["body"]:
                parsed["error_detail"] = resp["body"]["error"]
                parsed["series_id_in_response"] = None
            else:
                pts = resp["body"].get("points", [])
                parsed["series_id_in_response"] = resp["body"].get("id", None)
                parsed["perm_state"] = resp["body"].get("permission_state")
                if isinstance(pts, list):
                    parsed["data_count"] = len(pts)
                    parsed["non_zero_count"] = sum(
                        1 for p in pts if str(p.get("value", "0")) not in ("0", "0.0", "")
                    )
                    parsed["has_data"] = parsed["non_zero_count"] > 0
                    parsed["points_sample"] = json.dumps(pts[:3], ensure_ascii=False) if pts else None
        
        record = {
            "requested_short_id": short_id,
            "cycle": cycle,
            "ts": datetime.now().isoformat(),
            "http_status": resp["status"],
            "api_ms": resp["ms"],
            "api_error": resp["error"],
            "data_fetchable": parsed["has_data"],
            "data_count": parsed["data_count"],
            "non_zero_count": parsed["non_zero_count"],
            "perm_state": parsed["perm_state"],
            "resolved_series_id": parsed["series_id_in_response"],
            "error_detail": parsed["error_detail"],
            "points_sample": parsed["points_sample"],
            "raw_payload": resp["body"],  # 完整原始payload
        }
        results.append(record)
        
        status_icon = "[OK]" if parsed["has_data"] else "[FAIL]"
        print(f"  cycle {cycle}/{rounds}: HTTP={resp['status']} "
              f"ms={resp['ms']} data={parsed['has_data']} "
              f"pts={parsed['data_count']} non_zero={parsed['non_zero_count']} "
              f"perm={parsed['perm_state']} {status_icon}", flush=True)
    
    return results


def test_long_id_control(long_id, rounds=2):
    """
    对照测试: 使用真实long_id查询, 确认API本身正常工作
    """
    results = []
    for cycle in range(1, rounds + 1):
        url = f"{DATA_BASE}/series?id={urllib.parse.quote(long_id)}"
        resp = api_get(url)
        
        parsed = {"has_data": False, "data_count": 0, "non_zero_count": 0,
                  "perm_state": None, "series_id_in_response": None,
                  "points_sample": None}
        
        if resp["body"] and isinstance(resp["body"], dict):
            pts = resp["body"].get("points", [])
            parsed["series_id_in_response"] = resp["body"].get("id", None)
            parsed["perm_state"] = resp["body"].get("permission_state")
            if isinstance(pts, list):
                parsed["data_count"] = len(pts)
                parsed["non_zero_count"] = sum(
                    1 for p in pts if str(p.get("value", "0")) not in ("0", "0.0", "")
                )
                parsed["has_data"] = parsed["non_zero_count"] > 0
                parsed["points_sample"] = json.dumps(pts[:3], ensure_ascii=False) if pts else None
        
        record = {
            "requested_id": long_id,
            "cycle": cycle,
            "ts": datetime.now().isoformat(),
            "http_status": resp["status"],
            "api_ms": resp["ms"],
            "api_error": resp["error"],
            "data_fetchable": parsed["has_data"],
            "data_count": parsed["data_count"],
            "non_zero_count": parsed["non_zero_count"],
            "perm_state": parsed["perm_state"],
            "resolved_series_id": parsed["series_id_in_response"],
            "points_sample": parsed["points_sample"],
            "raw_payload": resp["body"],
        }
        results.append(record)
        
        status_icon = "[OK]" if parsed["has_data"] else "[FAIL]"
        print(f"  [CONTROL] {long_id} cycle {cycle}/{rounds}: HTTP={resp['status']} "
              f"ms={resp['ms']} data={parsed['has_data']} "
              f"pts={parsed['data_count']} non_zero={parsed['non_zero_count']} {status_icon}", flush=True)
    
    return results


# ===== 测试用例定义 =====
# 短ID: zhiji API中已知存在的短ID标识
SHORT_ID_CASES = [
    {"short_id": "j25_tc", "expected_long_id": "ID02226336", "expected_name": "铅精矿TC加工费"},
    {"short_id": "i1", "expected_long_id": "ID02226334", "expected_name": "铅锭社会库存"},
    {"short_id": "i2", "expected_long_id": "ID02226335", "expected_name": "铅锭交易所库存"},
    {"short_id": "i3", "expected_long_id": "ID02226332", "expected_name": "沪铅期货收盘价"},
    {"short_id": "i4", "expected_long_id": "ID02226333", "expected_name": "铅锭现货价格"},
    {"short_id": "i5", "expected_long_id": "ID02226337", "expected_name": "电解铅产量"},
    {"short_id": "i6", "expected_long_id": "ID02226338", "expected_name": "沪铜期货收盘价"},
    {"short_id": "i7", "expected_long_id": "ID02226339", "expected_name": "铜精矿TC加工费"},
]

# 长ID对照: 已确认可正常取数的长ID
LONG_ID_CONTROLS = [
    "ID02226332",  # 沪铅期货收盘价
    "ID02226334",  # 铅锭社会库存
    "ID02226336",  # 铅精矿TC加工费
]

ROUNDS = 3


def main():
    print(f"{'='*70}", flush=True)
    print(f"DSHB V86-RC2 短ID复测 v3.0 (重构版)", flush=True)
    print(f"执行时间: {datetime.now().isoformat()}", flush=True)
    print(f"rounds_per_id={ROUNDS}", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"\n[警告] v3.0 强制使用short_id作为series API查询参数", flush=True)
    print(f"[警告] 禁止自动替换为long_id — 如short_id不可用将直接失败", flush=True)
    print(f"{'='*70}", flush=True)
    
    all_short_results = {}
    all_control_results = {}
    
    # ===== Phase 1: 短ID直接测试 =====
    print(f"\n{'='*70}", flush=True)
    print(f"Phase 1: 短ID直接测试 (强制short_id入参)", flush=True)
    print(f"{'='*70}", flush=True)
    
    for case in SHORT_ID_CASES:
        sid = case["short_id"]
        print(f"\n[{sid}] 期望long_id={case['expected_long_id']} ({case['expected_name']})", flush=True)
        
        results = test_short_id_direct(sid, ROUNDS)
        all_short_results[sid] = results
        
        # 判定
        if results:
            last = results[-1]
            if last["data_fetchable"]:
                verdict = "PASS"
            elif last.get("error_detail"):
                verdict = f"FAIL (server error: {last['error_detail'][:50]})"
            elif last.get("perm_state") == -4:
                verdict = "FAIL (permission_state=-4, 无权限/无数据)"
            elif last["data_count"] == 0:
                verdict = "FAIL (HTTP 200但0数据点)"
            else:
                verdict = "FAIL"
            print(f"  => {sid}: {verdict}", flush=True)
    
    # ===== Phase 2: 长ID对照测试 =====
    print(f"\n{'='*70}", flush=True)
    print(f"Phase 2: 长ID对照测试 (确认API本身正常)", flush=True)
    print(f"{'='*70}", flush=True)
    
    for lid in LONG_ID_CONTROLS:
        print(f"\n[CONTROL] {lid}", flush=True)
        results = test_long_id_control(lid, 2)
        all_control_results[lid] = results
        if results:
            last = results[-1]
            if last["data_fetchable"]:
                print(f"  => {lid}: PASS (API正常)", flush=True)
            else:
                print(f"  => {lid}: FAIL (API异常)", flush=True)
    
    # ===== Phase 3: 汇总 =====
    print(f"\n{'='*70}", flush=True)
    print(f"Phase 3: 汇总", flush=True)
    print(f"{'='*70}", flush=True)
    
    # 短ID统计
    short_pass = 0
    short_fail = 0
    short_stats = {}
    for sid, results in all_short_results.items():
        if results:
            last = results[-1]
            passed = last["data_fetchable"]
            if passed:
                short_pass += 1
            else:
                short_fail += 1
            
            total_cycles = len(results)
            pass_cycles = sum(1 for r in results if r["data_fetchable"])
            avg_ms = round(sum(r["api_ms"] for r in results) / total_cycles, 1) if total_cycles else 0
            
            short_stats[sid] = {
                "short_id": sid,
                "total_cycles": total_cycles,
                "pass_cycles": pass_cycles,
                "fail_cycles": total_cycles - pass_cycles,
                "pass_rate": f"{round(pass_cycles/total_cycles*100, 1)}%",
                "avg_ms": avg_ms,
                "last_verdict": "PASS" if passed else "FAIL",
                "last_error": results[-1].get("error_detail") or 
                             (f"perm_state={results[-1]['perm_state']}" if results[-1].get("perm_state") is not None else None),
            }
    
    # 长ID统计
    control_pass = 0
    control_fail = 0
    control_stats = {}
    for lid, results in all_control_results.items():
        if results:
            last = results[-1]
            passed = last["data_fetchable"]
            if passed:
                control_pass += 1
            else:
                control_fail += 1
            avg_ms = round(sum(r["api_ms"] for r in results) / len(results), 1)
            control_stats[lid] = {
                "long_id": lid,
                "total_cycles": len(results),
                "pass_cycles": sum(1 for r in results if r["data_fetchable"]),
                "pass_rate": f"{round(sum(1 for r in results if r['data_fetchable'])/len(results)*100, 1)}%",
                "avg_ms": avg_ms,
                "last_verdict": "PASS" if passed else "FAIL",
            }
    
    # 生成汇总
    summary = {
        "title": "DSHB V86-RC2 短ID复测 v3.0 汇总",
        "report_id": "DSHB_V86_RC2_SELF_CHECK_T3.1",
        "test_time": datetime.now().isoformat(),
        "test_date": datetime.now().strftime("%Y-%m-%d"),
        "script_version": "v3.0 (short_id forced as series parameter)",
        "rounds_per_id": ROUNDS,
        
        "short_id_results": {
            "total": len(SHORT_ID_CASES),
            "pass": short_pass,
            "fail": short_fail,
            "pass_rate": f"{round(short_pass/len(SHORT_ID_CASES)*100, 1)}%",
            "details": short_stats,
        },
        "long_id_control_results": {
            "total": len(LONG_ID_CONTROLS),
            "pass": control_pass,
            "fail": control_fail,
            "pass_rate": f"{round(control_pass/len(LONG_ID_CONTROLS)*100, 1)}%",
            "details": control_stats,
        },
        
        "conclusion": {
            "short_id_resolvable": short_pass > 0,
            "long_id_working": control_pass > 0,
            "overall": "SHORT_ID_NOT_RESOLVABLE_BY_SERVER" if short_pass == 0 else "SHORT_ID_RESOLVABLE",
            "root_cause": "server-side zhiji API lacks short-ID prefix resolution" if short_pass == 0 else None,
            "dependency_block": True if short_pass == 0 else False,
            "action_required": "Request data platform to enable short-ID prefix resolution" if short_pass == 0 else None,
        },
    }
    
    # 保存汇总
    sp = LOG_DIR / "short_id_reverify_v3_summary.json"
    sp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSummary saved: {sp}", flush=True)
    
    # 保存每个short_id的完整日志 (含raw_payload)
    for sid, results in all_short_results.items():
        lp = LOG_DIR / f"{sid}_reverify_v3.json"
        lp.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Log saved: {lp} ({len(results)} cycles)", flush=True)
    
    # 保存长ID对照日志
    for lid, results in all_control_results.items():
        lp = LOG_DIR / f"{lid}_control_v3.json"
        lp.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Control log saved: {lp}", flush=True)
    
    # 输出最终结论
    print(f"\n{'='*70}", flush=True)
    print(f"=== FINAL VERDICT ===", flush=True)
    print(f"Short IDs tested: {len(SHORT_ID_CASES)} | PASS: {short_pass} | FAIL: {short_fail}", flush=True)
    print(f"Long IDs tested:  {len(LONG_ID_CONTROLS)} | PASS: {control_pass} | FAIL: {control_fail}", flush=True)
    print(f"Short ID resolvable: {summary['conclusion']['short_id_resolvable']}", flush=True)
    print(f"Root cause: {summary['conclusion']['root_cause'] or 'N/A'}", flush=True)
    print(f"Dependency block: {summary['conclusion']['dependency_block']}", flush=True)
    print(f"{'='*70}", flush=True)
    
    return summary


if __name__ == "__main__":
    main()
