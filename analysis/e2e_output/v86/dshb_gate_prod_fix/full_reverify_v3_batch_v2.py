#!/usr/bin/env python3
"""
DSHB V86-RC2 全量178条指标双维度复测脚本 V2
基于 v3 重构逻辑 + 内置桥接快照自动导出 + MD5自动校验
HERMES 对齐: COMPLETED = 元数据映射完成 + API真实取数校验通过

新增 V2 能力 (对比 V1):
  ✅ 复测完成自动导出DSHE桥接快照 (v86_rc2_dshb_bridge_snapshot_for_dshe.json)
  ✅ 快照附带MD5摘要, 便于DSHE校验文件完整性
  ✅ 自动生成MD5校验清单 (MD5_CHECKSUM_LIST_dep_trigger.md)
  ✅ 自动生成Gate准入状态评估 (data_fetchable_rate ≥ 80% → READY)

工单: DSHB_V86_RC2_DEP_MONITOR_T3.4
约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
"""

import json, os, sys, time, hashlib, urllib.request, urllib.parse, urllib.error
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

# ── V2新增: 快照与MD5配置 ──
SNAPSHOT_FILE = LOG_DIR / "v86_rc2_dshb_bridge_snapshot_for_dshe.json"
MD5_MANIFEST_FILE = OUTPUT_DIR / "MD5_CHECKSUM_LIST_dep_trigger.md"
GATE_THRESHOLD = 0.80  # data_fetchable ≥ 80% → READY

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
        "User-Agent": "Mozilla/5.0 DSHB_Reverify_v3/2.0",
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


def compute_md5(file_path):
    """计算文件MD5 (V2新增)"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest().upper()


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


# ═══════════════════════════════════════════════════════════
# V2新增: DSHE桥接快照自动导出
# ═══════════════════════════════════════════════════════════

def generate_bridge_snapshot(all_results, summary):
    """
    V2新增: 自动生成DSHE桥接快照
    格式: 双维度校验数据包 (metadata_completion + data_fetchable)
    """
    print(f"\n{'='*70}", flush=True)
    print(f"Phase 3: 自动导出DSHE桥接快照 (V2新增)", flush=True)
    print(f"{'='*70}", flush=True)

    entries = []
    for indicator_id, record in all_results.items():
        snapshot_entry = {
            "indicator_id": record["indicator_id"],
            "semantic_id": record["semantic_id"],
            "name_cn": record["name_cn"],
            "unit": record.get("unit", ""),
            "type": record.get("type", ""),
            "batch": record.get("batch", ""),
            "category": record["category"],
            "method": record.get("method", ""),

            # 双维度
            "metadata_completion": {
                "complete": record["metadata_complete"],
                "has_short_id": bool(record.get("zhiji_short_id") and record["zhiji_short_id"] not in ("", "DERIVED")),
                "has_long_id": bool(record.get("zhiji_long_id")),
                "has_api_series_id": bool(record.get("api_series_id_from_search")),
            },
            "data_fetchable": {
                "fetchable": record["data_fetchable"],
                "data_count": record.get("data_count", 0) if record.get("test_result") else 0,
                "http_status": record.get("test_result", [{}])[0].get("http_status") if record.get("test_result") else None,
                "error_msg": record.get("fetch_error_msg"),
            },
            "dependency_block": record["dependency_block"],

            # 原始ID
            "zhiji_short_id": record.get("zhiji_short_id", ""),
            "zhiji_long_id": record.get("zhiji_long_id", ""),
            "api_series_id": record.get("api_series_id_from_search", ""),

            # 分类
            "block_reason": record.get("fetch_error_msg"),
        }

        # 添加测试详情 (如有)
        if record.get("test_result"):
            last_test = record["test_result"][-1] if isinstance(record["test_result"], list) else record["test_result"]
            snapshot_entry["last_test"] = {
                "http_status": last_test.get("http_status"),
                "api_ms": last_test.get("api_ms"),
                "data_count": last_test.get("data_count"),
                "non_zero_count": last_test.get("non_zero_count"),
                "perm_state": last_test.get("perm_state"),
                "resolved_series_id": last_test.get("resolved_series_id"),
                "error_detail": last_test.get("error_detail"),
            }

        entries.append(snapshot_entry)

    # 构建快照
    total = len(entries)
    metadata_complete = sum(1 for e in entries if e["metadata_completion"]["complete"])
    data_fetchable = sum(1 for e in entries if e["data_fetchable"]["fetchable"])
    dependency_block = sum(1 for e in entries if e["dependency_block"])

    snapshot = {
        "snapshot_metadata": {
            "title": "DSHB V86-RC2 DSHE桥接快照 — 双维度校验数据包",
            "snapshot_version": "2.0",
            "generated_by": "full_reverify_v3_batch_v2.py",
            "generated_at": datetime.now().isoformat(),
            "generated_date": datetime.now().strftime("%Y-%m-%d"),
            "source_script": "full_reverify_v3_batch_v2.py v2.0",
            "task_id": "DSHB_V86_RC2_DEP_MONITOR_T3.4",
            "test_report_id": summary.get("report_id", ""),
        },
        "dual_dimension_summary": {
            "total_entries": total,
            "metadata_completion": {
                "complete": metadata_complete,
                "rate": f"{round(metadata_complete/total*100, 1)}%" if total > 0 else "0%",
            },
            "data_fetchable": {
                "fetchable": data_fetchable,
                "rate": f"{round(data_fetchable/total*100, 1)}%" if total > 0 else "0%",
            },
            "dependency_block": {
                "blocked": dependency_block,
                "rate": f"{round(dependency_block/total*100, 1)}%" if total > 0 else "0%",
            },
            "gate_assessment": {
                "data_fetchable_rate": round(data_fetchable/total*100, 1) if total > 0 else 0.0,
                "gate_threshold": GATE_THRESHOLD * 100,
                "gate_ready": (data_fetchable / total) >= GATE_THRESHOLD if total > 0 else False,
                "gate_status": "READY" if (data_fetchable / total) >= GATE_THRESHOLD else "NOT_READY" if total > 0 else "PENDING",
            },
        },
        "entries": entries,
        "entry_count": total,
    }

    # 写入快照文件
    SNAPSHOT_FILE.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 计算MD5
    snapshot_md5 = compute_md5(SNAPSHOT_FILE)
    snapshot_size = SNAPSHOT_FILE.stat().st_size

    print(f"  快照已生成: {SNAPSHOT_FILE.name}", flush=True)
    print(f"  条目数: {total}", flush=True)
    print(f"  文件大小: {snapshot_size:,} bytes", flush=True)
    print(f"  MD5: {snapshot_md5}", flush=True)

    # 输出Gate评估
    gate_status = snapshot["dual_dimension_summary"]["gate_assessment"]["gate_status"]
    fetchable_rate = snapshot["dual_dimension_summary"]["data_fetchable"]["rate"]
    print(f"  Gate评估: {gate_status} (data_fetchable={fetchable_rate})", flush=True)

    return {
        "snapshot_file": str(SNAPSHOT_FILE),
        "md5": snapshot_md5,
        "size": snapshot_size,
        "entries": total,
        "gate_status": gate_status,
    }


# ═══════════════════════════════════════════════════════════
# V2新增: MD5校验清单自动生成
# ═══════════════════════════════════════════════════════════

def generate_md5_manifest(summary):
    """
    V2新增: 自动生成MD5校验清单
    包含所有输出文件的MD5摘要, 便于DSHE校验文件完整性
    """
    print(f"\n{'='*70}", flush=True)
    print(f"Phase 4: 生成MD5校验清单 (V2新增)", flush=True)
    print(f"{'='*70}", flush=True)

    files_to_hash = []

    # 1. 日志目录中的文件
    if LOG_DIR.exists():
        for f in sorted(LOG_DIR.iterdir()):
            if f.is_file() and f.suffix in (".json", ".md"):
                files_to_hash.append(f)

    # 2. 根目录中的关键文件
    key_files = [
        OUTPUT_DIR / "v86_rc2_prod_id_bridge_mapping_v3_retest.md",
        OUTPUT_DIR / "v86_rc2_dshb_risk_re_evaluate_v3.md",
        OUTPUT_DIR / "v86_rc2_gate_pre_submit_package_v2.md",
        OUTPUT_DIR / "v86_rc2_dshb_dp_ticket_weekly_log.md",
        OUTPUT_DIR / "dep_ready_trigger.py",
        OUTPUT_DIR / "trigger_config.yaml",
        OUTPUT_DIR / "full_reverify_v3_batch_v2.py",
    ]
    for kf in key_files:
        if kf.exists():
            files_to_hash.append(kf)

    # 3. MD5清单本身 (最后计算)
    md5_entries = []
    for fp in files_to_hash:
        md5 = compute_md5(fp)
        size = fp.stat().st_size
        rel = fp.relative_to(OUTPUT_DIR) if OUTPUT_DIR in fp.parents else fp.name
        md5_entries.append((md5, str(rel), size))
        print(f"  {md5}  {rel}  ({size:,}B)", flush=True)

    # 写入清单
    manifest_lines = [
        f"# MD5校验清单 — 全量复测自动生成",
        f"# 生成时间: {datetime.now().isoformat()}",
        f"# 脚本版本: full_reverify_v3_batch_v2.py",
        f"# 文件数: {len(md5_entries)}",
        f"# Gate状态: {summary.get('conclusion', {}).get('overall', 'UNKNOWN')}",
        f"# 数据可取率: {summary.get('dual_dimension_stats', {}).get('data_fetchable', {}).get('rate', 'N/A')}",
        f"",
    ]
    for md5, rel, size in md5_entries:
        manifest_lines.append(f"{md5}  {rel}  ({size} bytes)")

    MD5_MANIFEST_FILE.write_text("\n".join(manifest_lines), encoding="utf-8")
    manifest_md5 = compute_md5(MD5_MANIFEST_FILE)

    print(f"\n  MD5清单已保存: {MD5_MANIFEST_FILE.name}", flush=True)
    print(f"  清单MD5: {manifest_md5}", flush=True)
    print(f"  清单文件数: {len(md5_entries)}", flush=True)

    return {
        "manifest_file": str(MD5_MANIFEST_FILE),
        "manifest_md5": manifest_md5,
        "file_count": len(md5_entries),
    }


# ═══════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════

def main():
    print(f"{'='*70}", flush=True)
    print(f"DSHB V86-RC2 全量178条指标双维度复测 V2", flush=True)
    print(f"执行时间: {datetime.now().isoformat()}", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"[信息] 基于v3重构逻辑: 强制short_id作为series API唯一查询参数", flush=True)
    print(f"[信息] HERMES对齐: COMPLETED = 元数据映射完成 + API真实取数校验通过", flush=True)
    print(f"[V2新增] 内置DSHE桥接快照自动导出 + MD5自动校验", flush=True)
    print(f"[V2新增] Gate准入自动评估 (data_fetchable ≥ 80% → READY)", flush=True)
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
            print(f"  [SKIP] DERIVED条目, 无API调用", flush=True)
            test_result = None
            data_fetchable, fetch_error_msg, dep_block = (
                False, "计算推导无API调用, 依赖下游指标可取数", True
            )
        else:
            rounds = 1
            if category == "real_short_id":
                print(f"  [TEST] 使用真实short_id={short_id} 调用series API", flush=True)
            elif category == "fabricated_short_id":
                print(f"  [TEST] 使用伪造short_id={short_id} 调用series API", flush=True)
            else:
                print(f"  [TEST] 使用short_id={short_id} 调用series API", flush=True)

            results = test_short_id(short_id, entry, rounds)
            test_result = results
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
            "metadata_complete": metadata_complete,
            "data_fetchable": data_fetchable,
            "dependency_block": dep_block,
            "fetch_error_msg": fetch_error_msg,
            "test_result": test_result,
        }
        all_results[indicator_id] = record

        # 保存单条日志
        log_filename = f"{indicator_id}_{entry.get('semantic_id', 'unknown')}.json"
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

    # Gate准入评估 (V2新增)
    fetchable_rate = data_fetchable_count / total if total > 0 else 0
    gate_ready = fetchable_rate >= GATE_THRESHOLD
    gate_status = "READY" if gate_ready else "NOT_READY" if total > 0 else "PENDING"

    summary = {
        "title": "DSHB V86-RC2 全量178条指标双维度复测汇总 V2",
        "report_id": "DSHB_V86_RC2_RETEST_T3.2_V2",
        "test_time": datetime.now().isoformat(),
        "test_date": datetime.now().strftime("%Y-%m-%d"),
        "script_version": "full_reverify_v3_batch_v2.py v2.0",
        "total_entries": total,

        "dual_dimension_stats": {
            "metadata_completion": {
                "total": total,
                "complete": metadata_complete_count,
                "rate": f"{round(metadata_complete_count/total*100, 1)}%" if total > 0 else "0%",
            },
            "data_fetchable": {
                "total": total,
                "fetchable": data_fetchable_count,
                "rate": f"{round(data_fetchable_count/total*100, 1)}%" if total > 0 else "0%",
            },
            "dependency_block": {
                "total": total,
                "blocked": dependency_block_count,
                "rate": f"{round(dependency_block_count/total*100, 1)}%" if total > 0 else "0%",
            },
        },

        "category_stats": cat_stats,
        "variety_stats": variety_stats,

        "gate_assessment": {
            "data_fetchable_rate": round(fetchable_rate * 100, 1),
            "gate_threshold": GATE_THRESHOLD * 100,
            "gate_ready": gate_ready,
            "gate_status": gate_status,
            "auto_switch_condition": "data_fetchable_rate >= 80%",
        },

        "conclusion": {
            "metadata_completion_rate": f"{round(metadata_complete_count/total*100, 1)}%" if total > 0 else "0%",
            "data_fetchable_rate": f"{round(data_fetchable_count/total*100, 1)}%" if total > 0 else "0%",
            "overall": "ALL_BLOCKED_EXTERNAL_DEPENDENCY" if data_fetchable_count == 0 else (
                "PARTIAL_FETCHABLE" if data_fetchable_count < total else "FULL_FETCHABLE"
            ),
            "root_cause": "zhiji API server-side lacks short-ID prefix resolution" if data_fetchable_count == 0 else None,
            "dependency_block_count": dependency_block_count,
            "external_dependency_required": True,
            "gate_status": gate_status,
        },

        # V2新增: 快照和MD5信息将在后续阶段填充
        "snapshot_info": {},
        "md5_info": {},
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

    # ===== Phase 3: 自动生成DSHE桥接快照 (V2新增) =====
    snapshot_info = generate_bridge_snapshot(all_results, summary)

    # ===== Phase 4: 生成MD5校验清单 (V2新增) =====
    md5_info = generate_md5_manifest(summary)

    # 更新汇总JSON中的V2信息
    summary["snapshot_info"] = snapshot_info
    summary["md5_info"] = md5_info
    sp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # ===== 最终结论 =====
    print(f"\n{'='*70}", flush=True)
    print(f"=== FINAL VERDICT (V2) ===", flush=True)
    print(f"metadata_completion: {summary['dual_dimension_stats']['metadata_completion']['rate']}", flush=True)
    print(f"data_fetchable:      {summary['dual_dimension_stats']['data_fetchable']['rate']}", flush=True)
    print(f"gate_status:         {gate_status} (threshold: {GATE_THRESHOLD*100}%)", flush=True)
    print(f"{'='*70}", flush=True)

    print(f"\n=== V2新增输出 ===", flush=True)
    print(f"DSHE快照: {snapshot_info['snapshot_file']} (MD5: {snapshot_info['md5']})", flush=True)
    print(f"MD5清单:  {md5_info['manifest_file']} (MD5: {md5_info['manifest_md5']})", flush=True)
    print(f"清单文件: {md5_info['file_count']} 个", flush=True)

    # Gate状态输出
    if gate_ready:
        print(f"\n🎉 Gate准入: READY — data_fetchable_rate={summary['dual_dimension_stats']['data_fetchable']['rate']} ≥ {GATE_THRESHOLD*100}%", flush=True)
        print(f"   → 可提交Gate预审", flush=True)
    else:
        print(f"\n❌ Gate准入: NOT_READY — data_fetchable_rate={summary['dual_dimension_stats']['data_fetchable']['rate']} < {GATE_THRESHOLD*100}%", flush=True)
        print(f"   → 等待外部依赖解决后重新评估", flush=True)

    print(f"{'='*70}", flush=True)

    return summary


if __name__ == "__main__":
    main()