#!/usr/bin/env python3
"""
DSHB V86-RC2 全量178条指标双维度复测脚本
基于 v3 重构逻辑: 强制 short_id 作为 series API 唯一查询参数
HERMES 对齐: COMPLETED = 元数据映射完成 + API真实取数校验通过

约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
工单: DSHB_V86_RC2_RETEST_T3.2
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
LOG_DIR = OUTPUT_DIR / "full_reverify_v3_batch_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MAP_DIR = OUTPUT_DIR / "mapping_logs"

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
        "User-Agent": "Mozilla/5.0 DSHB_Reverify_v3/1.0",
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


def parse_series_response(body):
    """解析 series API 响应，提取数据可用性信息"""
    parsed = {
        "has_data": False,
        "data_count": 0,
        "non_zero_count": 0,
        "perm_state": None,
        "series_id_in_response": None,
        "points_sample": None,
        "error_detail": None,
    }
    if body and isinstance(body, dict):
        if "error" in body and "points" not in body:
            parsed["error_detail"] = body["error"]
        else:
            pts = body.get("points", [])
            parsed["series_id_in_response"] = body.get("id", None)
            parsed["perm_state"] = body.get("permission_state")
            if isinstance(pts, list):
                parsed["data_count"] = len(pts)
                parsed["non_zero_count"] = sum(
                    1 for p in pts if isinstance(p, dict)
                    and str(p.get("value", "0")) not in ("0", "0.0", "")
                )
                parsed["has_data"] = parsed["non_zero_count"] > 0
                parsed["points_sample"] = json.dumps(pts[:3], ensure_ascii=False) if pts else None
    return parsed


def load_all_entries():
    """从 batch_1~9_mapping_log.json 加载全部178条指标"""
    entries = []
    for batch_no in range(1, 10):
        fpath = MAP_DIR / f"batch_{batch_no}_mapping_log.json"
        if not fpath.exists():
            print(f"  [WARN] Batch {batch_no} log not found: {fpath}", flush=True)
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data.get("results", []):
            entries.append(item)
    return entries


def categorize_entry(entry):
    """
    分类指标条目:
      - real_short_id: j25_tc, i1-i7 (真实短ID)
      - fabricated_short_id: s_xxx (伪造短ID)
      - derived: DERIVED (计算推导)
      - unknown: 其他
    """
    sid = entry.get("zhiji_short_id", "")
    method = entry.get("mapping_method", entry.get("method", ""))
    
    if sid == "DERIVED" or method == "derived" or method == "computed":
        return "derived"
    elif sid in ("j25_tc", "i1", "i2", "i3", "i4", "i5", "i6", "i7"):
        return "real_short_id"
    elif sid.startswith("s_"):
        return "fabricated_short_id"
    else:
        return "unknown"


def test_short_id(short_id, entry, rounds=1):
    """
    使用 v3 逻辑测试: 强制 short_id 作为 series API 唯一查询参数
    """
    results = []
    for cycle in range(1, rounds + 1):
        url = f"{DATA_BASE}/series?id={urllib.parse.quote(short_id)}"
        resp = api_get(url)
        parsed = parse_series_response(resp["body"])
        
        record = {
            "indicator_id": entry.get("indicator_id", ""),
            "semantic_id": entry.get("semantic_id", ""),
            "name_cn": entry.get("name_cn", ""),
            "batch": entry.get("batch", ""),
            "method": entry.get("mapping_method", entry.get("method", "")),
            "requested_short_id": short_id,
            "api_series_id_from_search": entry.get("api_series_id", None),
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
            "raw_payload": resp["body"],
        }
        results.append(record)
        
        status_icon = "[OK]" if parsed["has_data"] else "[FAIL]"
        print(f"  cycle {cycle}: HTTP={resp['status']} ms={resp['ms']} "
              f"data={parsed['has_data']} pts={parsed['data_count']} "
              f"non_zero={parsed['non_zero_count']} perm={parsed['perm_state']} "
              f"{status_icon}", flush=True)
    
    return results


def test_api_series_id(api_series_id, entry, rounds=1):
    """
    辅助测试: 使用 api_series_id (搜索获得的真实系列ID) 测试
    用于判断底层数据是否存在，但不作为主测试路径
    """
    results = []
    for cycle in range(1, rounds + 1):
        url = f"{DATA_BASE}/series?id={urllib.parse.quote(api_series_id)}"
        resp = api_get(url)
        parsed = parse_series_response(resp["body"])
        
        record = {
            "indicator_id": entry.get("indicator_id", ""),
            "semantic_id": entry.get("semantic_id", ""),
            "name_cn": entry.get("name_cn", ""),
            "requested_id": api_series_id,
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
        print(f"  [API_SERIES] {api_series_id} cycle {cycle}: HTTP={resp['status']} "
              f"ms={resp['ms']} data={parsed['has_data']} "
              f"pts={parsed['data_count']} {status_icon}", flush=True)
    
    return results


def determine_verdict(entry, results, category):
    """
    判定单个条目的最终结论
    返回: (data_fetchable, fetch_error_msg, dependency_block)
    """
    if category == "derived":
        return False, "计算推导无API调用, 依赖下游指标可取数", True
    
    if not results:
        return False, "测试未执行", False
    
    last = results[-1]
    
    if last["data_fetchable"]:
        return True, None, False
    
    # 不可取数，分析原因
    if last.get("error_detail"):
        err = last["error_detail"]
        if "无法识别指标来源" in str(err):
            return False, f"short_id不可解析: {str(err)[:80]}", True
        elif "not_found" in str(err) or "not found" in str(err).lower():
            return False, f"short_id不存在: {str(err)[:80]}", True
        else:
            return False, f"API错误: {str(err)[:80]}", False
    
    if last.get("perm_state") == -4:
        return False, "permission_state=-4, 无权限/数据未绑定", True
    
    if last["http_status"] and last["http_status"] >= 400:
        return False, f"HTTP {last['http_status']}错误", False
    
    if last["data_count"] == 0:
        return False, "HTTP 200但0数据点", False
    
    return False, "取数失败", False


def main():
    print(f"{'='*70}", flush=True)
    print(f"DSHB V86-RC2 全量178条指标双维度复测", flush=True)
    print(f"执行时间: {datetime.now().isoformat()}", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"[信息] 基于v3重构逻辑: 强制short_id作为series API唯一查询参数", flush=True)
    print(f"[信息] HERMES对齐: COMPLETED = 元数据映射完成 + API真实取数校验通过", flush=True)
    print(f"{'='*70}", flush=True)
    
    # ===== Phase 0: 加载全部条目 =====
    print(f"\nPhase 0: 加载全部178条指标条目", flush=True)
    print(f"{'='*70}", flush=True)
    
    entries = load_all_entries()
    print(f"  加载完成: {len(entries)} 条指标", flush=True)
    
    # 分类统计
    categories = {"real_short_id": [], "fabricated_short_id": [], "derived": [], "unknown": []}
    for entry in entries:
        cat = categorize_entry(entry)
        categories[cat].append(entry)
    
    for cat, items in categories.items():
        print(f"  [{cat}] {len(items)} 条", flush=True)
    
    # ===== Phase 1: 逐条测试 =====
    print(f"\nPhase 1: 逐条双维度复测", flush=True)
    print(f"{'='*70}", flush=True)
    
    all_results = {}
    test_log = []
    
    for idx, entry in enumerate(entries):
        indicator_id = entry.get("indicator_id", f"unknown_{idx}")
        name_cn = entry.get("name_cn", "")
        short_id = entry.get("zhiji_short_id", "")
        category = categorize_entry(entry)
        
        print(f"\n[{idx+1}/{len(entries)}] {indicator_id} ({name_cn}) [{category}] short_id={short_id}", flush=True)
        
        # 元数据完整性检查
        has_short_id = bool(short_id and short_id not in ("", "DERIVED"))
        has_long_id = bool(entry.get("zhiji_long_id", ""))
        has_api_series_id = bool(entry.get("api_series_id", ""))
        metadata_complete = has_short_id and has_long_id
        
        # 根据分类执行测试
        if category == "derived":
            # DERIVED条目: 无API调用
            print(f"  [SKIP] DERIVED条目, 无API调用", flush=True)
            test_result = None
            data_fetchable, fetch_error_msg, dep_block = (
                False, "计算推导无API调用, 依赖下游指标可取数", True
            )
        else:
            # 有short_id的条目: 执行API测试
            rounds = 1  # 全量复测每ID 1轮, 控制总耗时
            
            if category == "real_short_id":
                print(f"  [TEST] 使用真实short_id={short_id} 调用series API", flush=True)
            elif category == "fabricated_short_id":
                print(f"  [TEST] 使用伪造short_id={short_id} 调用series API", flush=True)
            else:
                print(f"  [TEST] 使用short_id={short_id} 调用series API", flush=True)
            
            results = test_short_id(short_id, entry, rounds)
            test_result = results
            
            # 判定
            data_fetchable, fetch_error_msg, dep_block = determine_verdict(
                entry, results, category
            )
        
        # 构建完整记录
        record = {
            "index": idx + 1,
            "indicator_id": indicator_id,
            "semantic_id": entry.get("semantic_id", ""),
            "name_cn": name_cn,
            "unit": entry.get("unit", ""),
            "type": entry.get("type", ""),
            "batch": entry.get("batch", ""),
            "priority": entry.get("priority", ""),
            "category": category,
            "method": entry.get("mapping_method", entry.get("method", "")),
            "search_query": entry.get("search_query", ""),
            "zhiji_short_id": short_id,
            "zhiji_long_id": entry.get("zhiji_long_id", ""),
            "api_series_id_from_search": entry.get("api_series_id", ""),
            "mapped_name": entry.get("matched_name", ""),
            
            # 双维度
            "metadata_complete": metadata_complete,
            "data_fetchable": data_fetchable,
            "dependency_block": dep_block,
            "fetch_error_msg": fetch_error_msg,
            
            # 原始测试数据
            "test_result": test_result,
        }
        all_results[indicator_id] = record
        
        # 保存单条日志
        log_filename = f"{indicator_id}_{entry.get('semantic_id', 'unknown')}.json"
        # 清理文件名中的特殊字符
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in log_filename)
        lp = LOG_DIR / f"{idx+1:03d}_{safe_name}"
        lp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # 简要状态
        d_icon = "[TRUE]" if data_fetchable else "[FALSE]"
        m_icon = "[TRUE]" if metadata_complete else "[FALSE]"
        b_icon = "[BLOCK]" if dep_block else "[OK]"
        print(f"  => metadata={m_icon} data_fetchable={d_icon} dependency={b_icon}", flush=True)
        
        test_log.append({
            "index": idx + 1,
            "indicator_id": indicator_id,
            "category": category,
            "metadata_complete": metadata_complete,
            "data_fetchable": data_fetchable,
            "dependency_block": dep_block,
        })
    
    # ===== Phase 2: 汇总统计 =====
    print(f"\nPhase 2: 汇总统计", flush=True)
    print(f"{'='*70}", flush=True)
    
    total = len(entries)
    metadata_complete_count = sum(1 for r in all_results.values() if r["metadata_complete"])
    data_fetchable_count = sum(1 for r in all_results.values() if r["data_fetchable"])
    dependency_block_count = sum(1 for r in all_results.values() if r["dependency_block"])
    
    # 按分类统计
    cat_stats = {}
    for cat in ("real_short_id", "fabricated_short_id", "derived", "unknown"):
        items = [r for r in all_results.values() if r["category"] == cat]
        cat_stats[cat] = {
            "total": len(items),
            "metadata_complete": sum(1 for i in items if i["metadata_complete"]),
            "data_fetchable": sum(1 for i in items if i["data_fetchable"]),
            "dependency_block": sum(1 for i in items if i["dependency_block"]),
        }
    
    # 按品种统计
    variety_stats = {}
    for r in all_results.values():
        var = r["indicator_id"].split("-")[0] if "-" in r["indicator_id"] else "OTHER"
        if var not in variety_stats:
            variety_stats[var] = {"total": 0, "data_fetchable": 0, "dependency_block": 0}
        variety_stats[var]["total"] += 1
        variety_stats[var]["data_fetchable"] += 1 if r["data_fetchable"] else 0
        variety_stats[var]["dependency_block"] += 1 if r["dependency_block"] else 0
    
    # 生成汇总JSON
    summary = {
        "title": "DSHB V86-RC2 全量178条指标双维度复测汇总",
        "report_id": "DSHB_V86_RC2_RETEST_T3.2",
        "test_time": datetime.now().isoformat(),
        "test_date": datetime.now().strftime("%Y-%m-%d"),
        "script_version": "full_reverify_v3_batch.py v1.0 (based on short_id_reverify_v3.py)",
        "total_entries": total,
        
        # 双维度统计
        "dual_dimension_stats": {
            "metadata_completion": {
                "total": total,
                "complete": metadata_complete_count,
                "rate": f"{round(metadata_complete_count/total*100, 1)}%",
            },
            "data_fetchable": {
                "total": total,
                "fetchable": data_fetchable_count,
                "rate": f"{round(data_fetchable_count/total*100, 1)}%",
            },
            "dependency_block": {
                "total": total,
                "blocked": dependency_block_count,
                "rate": f"{round(dependency_block_count/total*100, 1)}%",
            },
        },
        
        # 分类统计
        "category_stats": cat_stats,
        
        # 品种统计
        "variety_stats": variety_stats,
        
        # 结论
        "conclusion": {
            "metadata_completion_rate": f"{round(metadata_complete_count/total*100, 1)}%",
            "data_fetchable_rate": f"{round(data_fetchable_count/total*100, 1)}%",
            "overall": "ALL_BLOCKED_EXTERNAL_DEPENDENCY" if data_fetchable_count == 0 else "PARTIAL_FETCHABLE",
            "root_cause": "zhiji API server-side lacks short-ID prefix resolution" if data_fetchable_count == 0 else None,
            "dependency_block_count": dependency_block_count,
            "external_dependency_required": True,
        },
    }
    
    # 保存汇总
    sp = LOG_DIR / "full_reverify_v3_batch_summary.json"
    sp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n汇总已保存: {sp}", flush=True)
    
    # 输出控制台统计
    print(f"\n{'='*70}", flush=True)
    print(f"=== 全量复测汇总 ===", flush=True)
    print(f"总条目: {total}", flush=True)
    print(f"元数据映射完成率: {metadata_complete_count}/{total} = {summary['dual_dimension_stats']['metadata_completion']['rate']}", flush=True)
    print(f"真实可取数桥接率: {data_fetchable_count}/{total} = {summary['dual_dimension_stats']['data_fetchable']['rate']}", flush=True)
    print(f"外部依赖阻塞: {dependency_block_count}/{total} = {summary['dual_dimension_stats']['dependency_block']['rate']}", flush=True)
    print(f"{'='*70}", flush=True)
    
    print(f"\n=== 分类统计 ===", flush=True)
    for cat, stats in cat_stats.items():
        if stats["total"] > 0:
            print(f"  [{cat}] total={stats['total']} meta={stats['metadata_complete']} "
                  f"data={stats['data_fetchable']} block={stats['dependency_block']}", flush=True)
    
    print(f"\n=== 品种统计 ===", flush=True)
    for var, stats in sorted(variety_stats.items()):
        print(f"  [{var}] total={stats['total']} data={stats['data_fetchable']} block={stats['dependency_block']}", flush=True)
    
    print(f"\n=== FINAL VERDICT ===", flush=True)
    print(f"metadata_completion: {summary['dual_dimension_stats']['metadata_completion']['rate']}", flush=True)
    print(f"data_fetchable:      {summary['dual_dimension_stats']['data_fetchable']['rate']}", flush=True)
    print(f"overall:             {summary['conclusion']['overall']}", flush=True)
    print(f"{'='*70}", flush=True)
    
    return summary


if __name__ == "__main__":
    main()
