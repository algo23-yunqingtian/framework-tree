#!/usr/bin/env python3
"""
DSH-B_CHECK_META_DATA_QUALITY_V85_20260928
元数据质检脚本 — T2 (元数据批量校验) + T3 (空数据复核)

只读模式：不修改任何原始文件，不调用zhiji API
"""
import json
import csv
import os
import hashlib
from datetime import datetime, date
from collections import defaultdict, Counter

# ============================================================
# 配置
# ============================================================
BASE_DIR = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85"
META_DIR = os.path.join(BASE_DIR, "meta_check")
INDICATORS_FILE = r"D:\DSH_WORK\framework-tree\data\indicators_v1.json"
WORK_ORDER = "DSH-B_CHECK_META_DATA_QUALITY_V85_20260928"
RUN_DATE = date.today()
STALE_THRESHOLD_DAYS = 90

os.makedirs(META_DIR, exist_ok=True)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

# ============================================================
# T1: 前置校验
# ============================================================
log("=" * 72)
log(f"T1: 前置准备 — 工单 {WORK_ORDER}")
log(f"运行时间: {datetime.now().isoformat()}")
log("=" * 72)

# 读取输入文件
def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

# 1. 读取看板CSV
board_path = os.path.join(BASE_DIR, "fp32_v85_final_board.csv")
log(f"\n[1/6] 读取看板: {board_path}")
board_rows = []
with open(board_path, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        board_rows.append(row)
log(f"  看板行数: {len(board_rows)}")

# 2. 读取zhiji_fetch_result.json
fetch_path = os.path.join(BASE_DIR, "zhiji_fetch_result.json")
log(f"\n[2/6] 读取fetch结果: {fetch_path}")
fetch_data = read_json(fetch_path)
summary = fetch_data["summary"]
detailed_results = fetch_data["detailed_results"]
unique_results = fetch_data["fetch_details"]
log(f"  总TP样本: {summary['total_tp_samples']}, 唯一ID: {summary['unique_zhiji_ids']}")
log(f"  成功: {summary['success_count']}, 错误: {summary['error_count']}")

# 3. 读取duplicate_id_list.json
dup_path = os.path.join(BASE_DIR, "duplicate_id_list.json")
log(f"\n[3/6] 读取重复ID清单: {dup_path}")
dup_data = read_json(dup_path)
log(f"  重复ID数: {dup_data['duplicate_id_count']}, 可节省API调用: {dup_data['dedup_saving']}")

# 4. 读取indicators_v1.json元数据
ind_path = INDICATORS_FILE
log(f"\n[4/6] 读取指标元数据: {ind_path}")
indicators = read_json(ind_path)
log(f"  指标类别数: {len(indicators)}")

# 5. 构建unit_convert_mapping.json (工单要求但不存在，自动创建)
log(f"\n[5/6] 构建unit_convert_mapping.json")
unit_mapping = {}
for u in unique_results:
    zhiji_id = u["zhiji_id"]
    val = u["validation"]
    entry = {
        "zhiji_id": zhiji_id,
        "series_name": val.get("series_name", ""),
        "zhiji_unit": val.get("unit", ""),
        "zhiji_frequency": val.get("frequency", ""),
        "source": val.get("source", ""),
        "data_latest": val.get("data_latest", ""),
        "data_points": val.get("data_points", 0),
        "unit_match": val.get("unit_match"),
        "id_valid": val.get("id_valid", False),
        "data_success": val.get("data_success", False),
        "error_type": val.get("error_type", ""),
        "error_detail": val.get("error_detail", ""),
    }
    # 在indicators_v1.json中查找对应元数据
    meta_unit = None
    meta_freq = None
    meta_verified = None
    for cat_name, cat_data in indicators.items():
        if not isinstance(cat_data, dict) or "ids" not in cat_data:
            continue
        if not isinstance(cat_data.get("ids"), dict):
            continue
        for var, zhiji_id_in_meta in cat_data["ids"].items():
            if zhiji_id_in_meta == zhiji_id:
                meta_unit = cat_data.get("unit")
                meta_freq = cat_data.get("freq")
                meta_verified = cat_data.get("verified")
                entry["indicator_category"] = cat_name
                entry["indicator_variety"] = var
                break
        if meta_unit:
            break
    entry["meta_unit"] = meta_unit
    entry["meta_freq"] = meta_freq
    entry["meta_verified"] = meta_verified
    unit_mapping[zhiji_id] = entry

unit_map_path = os.path.join(META_DIR, "unit_convert_mapping.json")
with open(unit_map_path, "w", encoding="utf-8") as f:
    json.dump(unit_mapping, f, ensure_ascii=False, indent=2)
log(f"  写入unit_convert_mapping.json: {len(unit_mapping)}个ID")

# 6. MD5校验
log(f"\n[6/6] MD5校验:")
input_files = [
    ("fp32_v85_final_board.csv", board_path),
    ("zhiji_fetch_result.json", fetch_path),
    ("duplicate_id_list.json", dup_path),
]
expected_md5 = {
    "fp32_v85_final_board.csv": "80f07448523023362360f090186a0bdd",
    "zhiji_fetch_result.json": "83f44a590fb8c3bbe6f93c6b630130f8",
    "duplicate_id_list.json": "39d9d1c4355a232a78d8f0d4c6a40f91",
}
md5_results = {}
all_ok = True
for fname, fpath in input_files:
    actual = md5_file(fpath)
    expected = expected_md5.get(fname, "")
    match = actual.lower() == expected.lower()
    md5_results[fname] = {"actual": actual, "expected": expected, "match": match}
    status = "✅" if match else "❌"
    log(f"  {status} {fname}: {actual}")
    if not match:
        all_ok = False

if not all_ok:
    log("\n⚠️ MD5校验失败，终止任务并告警！")
    log(json.dumps(md5_results, ensure_ascii=False, indent=2))
    with open(os.path.join(META_DIR, "error_alert.txt"), "w", encoding="utf-8") as f:
        f.write("MD5校验失败！\n")
        f.write(json.dumps(md5_results, ensure_ascii=False, indent=2))
    raise SystemExit(1)

log("\n✅ MD5校验全部通过")

# ============================================================
# T2: 元数据批量校验
# ============================================================
log("\n" + "=" * 72)
log("T2: 元数据批量校验")
log("=" * 72)

warnings = []
freq_map = {"daily": "日", "weekly": "周", "monthly": "月", "quarterly": "季", "annual": "年"}
freq_map_rev = {"日": "daily", "周": "weekly", "月": "monthly", "季": "quarterly", "年": "annual"}

# 遍历unique_results中每个zhiji_id
severity_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

for zhiji_id, entry in unit_mapping.items():
    v = entry
    warning_entries = []

    # --- 2.1 单位冲突检查 ---
    zhiji_unit = v.get("zhiji_unit", "")
    meta_unit = v.get("meta_unit")
    if meta_unit and zhiji_unit:
        # 标准化比较
        zhiji_unit_norm = zhiji_unit.strip()
        meta_unit_norm = meta_unit.strip()
        if zhiji_unit_norm != meta_unit_norm:
            # 检查是否为量级冲突（吨 vs 万吨）
            if "吨" in zhiji_unit_norm and "吨" in meta_unit_norm:
                if "万" in zhiji_unit_norm and "万" not in meta_unit_norm:
                    severity = "HIGH"
                    desc = f"量级冲突: 知几={zhiji_unit_norm}, 元数据={meta_unit_norm} (需×10000)"
                elif "万" not in zhiji_unit_norm and "万" in meta_unit_norm:
                    severity = "HIGH"
                    desc = f"量级冲突: 知几={zhiji_unit_norm}, 元数据={meta_unit_norm} (需÷10000)"
                else:
                    severity = "MEDIUM"
                    desc = f"单位不一致: 知几={zhiji_unit_norm}, 元数据={meta_unit_norm}"
            else:
                severity = "HIGH"
                desc = f"单位冲突: 知几={zhiji_unit_norm}, 元数据={meta_unit_norm}"
            warning_entries.append({
                "check": "unit_conflict",
                "severity": severity,
                "detail": desc,
                "zhiji_unit": zhiji_unit,
                "meta_unit": meta_unit,
            })

    # --- 2.2 时间粒度一致性检查 ---
    zhiji_freq = v.get("zhiji_frequency", "")
    meta_freq = v.get("meta_freq")
    if meta_freq and zhiji_freq:
        meta_freq_cn = freq_map.get(meta_freq, meta_freq)
        if zhiji_freq != meta_freq_cn:
            severity = "MEDIUM"
            warning_entries.append({
                "check": "freq_mismatch",
                "severity": severity,
                "detail": f"粒度不一致: 知几={zhiji_freq}, 元数据={meta_freq} ({meta_freq_cn})",
                "zhiji_frequency": zhiji_freq,
                "meta_frequency": meta_freq,
                "meta_frequency_cn": meta_freq_cn,
            })

    # --- 2.3 长期停更检查 (>90天) ---
    data_latest_str = v.get("data_latest", "")
    if data_latest_str:
        try:
            latest_date = datetime.strptime(data_latest_str, "%Y-%m-%d").date()
            days_since = (RUN_DATE - latest_date).days
            if days_since > STALE_THRESHOLD_DAYS:
                severity = "HIGH" if days_since > 365 else "MEDIUM"
                desc = f"停更{days_since}天 (最后更新: {data_latest_str})"
                if days_since > 365:
                    desc += " — 疑似指标已下线"
                warning_entries.append({
                    "check": "stale_indicator",
                    "severity": severity,
                    "detail": desc,
                    "data_latest": data_latest_str,
                    "days_since_update": days_since,
                })
        except ValueError:
            pass  # 忽略解析错误

    # --- 2.4 数据连续性低检查 ---
    data_points = v.get("data_points", 0)
    freq = v.get("zhiji_frequency", "")
    if data_points == 0 and v.get("data_success", False):
        warning_entries.append({
            "check": "empty_data",
            "severity": "HIGH",
            "detail": "数据成功但数据点为0",
        })
    elif data_points > 0 and data_points < 5:
        warning_entries.append({
            "check": "sparse_data",
            "severity": "MEDIUM",
            "detail": f"数据点过少: {data_points}条",
        })

    # --- 2.5 单位匹配状态检查 ---
    unit_match_val = v.get("unit_match")
    if unit_match_val is False:
        warning_entries.append({
            "check": "unit_match_false",
            "severity": "MEDIUM",
            "detail": "unit_match=False — 知几返回单位与预期不一致",
        })

    # --- 汇总此ID的警告 ---
    if warning_entries:
        warnings.append({
            "zhiji_id": zhiji_id,
            "series_name": v.get("series_name", ""),
            "source": v.get("source", ""),
            "indicator_category": v.get("indicator_category", ""),
            "indicator_variety": v.get("indicator_variety", ""),
            "warnings": warning_entries,
            "warning_count": len(warning_entries),
            "max_severity": max((w["severity"] for w in warning_entries), key=lambda s: severity_rank.get(s, -1)),
        })

# ============================================================
# 输出 meta_warning_list.json
# ============================================================
meta_warning_path = os.path.join(META_DIR, "meta_warning_list.json")
meta_warning_output = {
    "work_order": WORK_ORDER,
    "generated_at": datetime.now().isoformat(),
    "total_ids_checked": len(unit_mapping),
    "total_warnings": len(warnings),
    "warnings_by_type": Counter(w["check"] for w_item in warnings for w in w_item["warnings"]),
    "warnings_by_severity": Counter(w["severity"] for w_item in warnings for w in w_item["warnings"]),
    "stale_threshold_days": STALE_THRESHOLD_DAYS,
    "warnings": warnings,
}
with open(meta_warning_path, "w", encoding="utf-8") as f:
    json.dump(meta_warning_output, f, ensure_ascii=False, indent=2)
log(f"\n✅ meta_warning_list.json 已写入 ({len(warnings)}个警告条目)")

# 统计
check_counts = Counter()
severity_counts = Counter()
for w_item in warnings:
    for w in w_item["warnings"]:
        check_counts[w["check"]] += 1
        severity_counts[w["severity"]] += 1

log(f"  警告分布: {dict(check_counts)}")
log(f"  严重度: {dict(severity_counts)}")

# ============================================================
# 输出 meta_quality_summary.md
# ============================================================
summary_lines = []
summary_lines.append("# 元数据质检汇总报告")
summary_lines.append(f"\n**工单**: {WORK_ORDER}")
summary_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
summary_lines.append(f"**质检范围**: {len(unit_mapping)} 个唯一 zhiji_id")
summary_lines.append(f"**停更阈值**: {STALE_THRESHOLD_DAYS} 天")
summary_lines.append("")

summary_lines.append("## 总体统计")
summary_lines.append(f"| 检查项 | 发现数量 |")
summary_lines.append(f"|--------|---------|")
summary_lines.append(f"| 单位冲突/不一致 | {check_counts.get('unit_conflict', 0)} |")
summary_lines.append(f"| 粒度不一致 | {check_counts.get('freq_mismatch', 0)} |")
summary_lines.append(f"| 长期停更指标 | {check_counts.get('stale_indicator', 0)} |")
summary_lines.append(f"| 稀疏数据 | {check_counts.get('sparse_data', 0)} |")
summary_lines.append(f"| 单位匹配失败 | {check_counts.get('unit_match_false', 0)} |")
summary_lines.append(f"| 空数据 | {check_counts.get('empty_data', 0)} |")
summary_lines.append(f"| **合计警告** | **{len(warnings)}** |")
summary_lines.append(f"\n## 严重度分布")
summary_lines.append(f"| 严重度 | 数量 |")
summary_lines.append(f"|--------|------|")
for sev in ["HIGH", "MEDIUM", "LOW"]:
    summary_lines.append(f"| {sev} | {severity_counts.get(sev, 0)} |")

summary_lines.append("\n## 详细警告清单")
summary_lines.append("")
summary_lines.append("### HIGH 严重度")
summary_lines.append("")
for w_item in sorted(warnings, key=lambda x: 0 if x["max_severity"] == "HIGH" else 1):
    if w_item["max_severity"] != "HIGH":
        continue
    summary_lines.append(f"#### `{w_item['zhiji_id']}` — {w_item['series_name']}")
    summary_lines.append(f"- 类别: {w_item['indicator_category']} / {w_item['indicator_variety']}")
    summary_lines.append(f"- 数据源: {w_item['source']}")
    summary_lines.append(f"- 警告数: {w_item['warning_count']}")
    for w in w_item["warnings"]:
        if w["severity"] == "HIGH":
            summary_lines.append(f"  - 🔴 [{w['check']}] {w['detail']}")
    summary_lines.append("")

summary_lines.append("### MEDIUM 严重度")
summary_lines.append("")
for w_item in sorted(warnings, key=lambda x: 0 if x["max_severity"] == "MEDIUM" else 1):
    if w_item["max_severity"] != "MEDIUM":
        continue
    summary_lines.append(f"#### `{w_item['zhiji_id']}` — {w_item['series_name']}")
    summary_lines.append(f"- 类别: {w_item['indicator_category']} / {w_item['indicator_variety']}")
    summary_lines.append(f"- 数据源: {w_item['source']}")
    summary_lines.append(f"- 警告数: {w_item['warning_count']}")
    for w in w_item["warnings"]:
        if w["severity"] == "MEDIUM":
            summary_lines.append(f"  - 🟡 [{w['check']}] {w['detail']}")
    summary_lines.append("")

# 额外：无元数据匹配的ID
no_meta_ids = [zid for zid, v in unit_mapping.items() if v.get("meta_unit") is None]
summary_lines.append(f"\n## 无元数据匹配的ID ({len(no_meta_ids)}个)")
summary_lines.append("")
summary_lines.append("以下ID未在 indicators_v1.json 中找到对应类别，单位/粒度无法交叉验证：")
for zid in no_meta_ids:
    entry = unit_mapping[zid]
    summary_lines.append(f"- `{zid}` — {entry.get('series_name','')} (知几单位: {entry.get('zhiji_unit','')}, 粒度: {entry.get('zhiji_frequency','')})")

summary_lines.append(f"\n## 数据源分布")
source_counts = Counter(v.get("source", "") for v in unit_mapping.values())
summary_lines.append(f"| 数据源 | ID数 |")
summary_lines.append(f"|--------|------|")
for src, cnt in source_counts.most_common():
    summary_lines.append(f"| {src} | {cnt} |")

summary_lines.append(f"\n## 粒度分布")
freq_counts = Counter(v.get("zhiji_frequency", "") for v in unit_mapping.values())
summary_lines.append(f"| 粒度 | ID数 |")
summary_lines.append(f"|------|------|")
for fr, cnt in freq_counts.most_common():
    summary_lines.append(f"| {fr} | {cnt} |")

# 停更指标列表
stale_items = [(zid, v) for zid, v in unit_mapping.items() 
               if v.get("data_latest") and 
               (RUN_DATE - datetime.strptime(v["data_latest"], "%Y-%m-%d").date()).days > STALE_THRESHOLD_DAYS]
summary_lines.append(f"\n## 停更指标清单 ({len(stale_items)}个, >{STALE_THRESHOLD_DAYS}天)")
summary_lines.append("")
if stale_items:
    summary_lines.append("| zhiji_id | 指标名 | 最后更新 | 停更天数 |")
    summary_lines.append("|----------|--------|----------|---------|")
    for zid, v in sorted(stale_items, key=lambda x: x[1].get("data_latest","")):
        latest = v.get("data_latest", "")
        days = (RUN_DATE - datetime.strptime(latest, "%Y-%m-%d").date()).days if latest else "?"
        summary_lines.append(f"| `{zid}` | {v.get('series_name','')} | {latest} | {days}天 |")
else:
    summary_lines.append("无停更指标。")

summary_content = "\n".join(summary_lines)
summary_path = os.path.join(META_DIR, "meta_quality_summary.md")
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary_content)
log(f"\n✅ meta_quality_summary.md 已写入")

# ============================================================
# T3: 空数据指标复核
# ============================================================
log("\n" + "=" * 72)
log("T3: 空数据指标复核")
log("=" * 72)

empty_ids = ["ID00259727", "a12804329"]
empty_details = {}

for eid in empty_ids:
    entry = unit_mapping.get(eid, {})
    empty_details[eid] = {
        "zhiji_id": eid,
        "series_name": entry.get("series_name", ""),
        "source": entry.get("source", ""),
        "zhiji_unit": entry.get("zhiji_unit", ""),
        "zhiji_frequency": entry.get("zhiji_frequency", ""),
        "data_latest": entry.get("data_latest", ""),
        "data_points": entry.get("data_points", 0),
        "error_type": entry.get("error_type", ""),
        "error_detail": entry.get("error_detail", ""),
        "meta_unit": entry.get("meta_unit"),
        "meta_freq": entry.get("meta_freq"),
        "indicator_category": entry.get("indicator_category", ""),
        "indicator_variety": entry.get("indicator_variety", ""),
    }
    
    # 查找detailed_results中的记录
    dr_matches = [d for d in detailed_results if d.get("matched_id") == eid]
    if dr_matches:
        dr = dr_matches[0]
        empty_details[eid]["chart_name"] = dr.get("chart_name", "")
        empty_details[eid]["sample_id"] = dr.get("sample_id", "")
        empty_details[eid]["variety"] = dr.get("variety", "")
        empty_details[eid]["category"] = dr.get("category", "")
    
    # 查找duplicate中的记录
    dup_matches = [d for d in dup_data.get("duplicates", []) if d.get("zhiji_id") == eid]
    if dup_matches:
        empty_details[eid]["occurrence_count"] = dup_matches[0].get("occurrence_count", 1)
    
    log(f"\n  📋 {eid} — {entry.get('series_name','')}")
    log(f"    错误类型: {entry.get('error_type','')}")
    log(f"    错误详情: {entry.get('error_detail','')}")
    log(f"    数据起始: {entry.get('data_latest','')}, 数据点: {entry.get('data_points',0)}")
    log(f"    数据源: {entry.get('source','')}, 知几单位: {entry.get('zhiji_unit','')}, 粒度: {entry.get('zhiji_frequency','')}")
    log(f"    元数据单位: {entry.get('meta_unit')}, 元数据粒度: {entry.get('meta_freq')}")

# 根因分类
root_causes = {}
for eid in empty_ids:
    d = empty_details[eid]
    latest = d.get("data_latest", "")
    src = d.get("source", "")
    
    if not latest:
        root_causes[eid] = {
            "category": "① 知几无该序列",
            "detail": "知几API返回ID但无时间范围数据，可能该ID已被下架",
            "severity": "HIGH",
        }
    else:
        try:
            latest_date = datetime.strptime(latest, "%Y-%m-%d").date()
            days_stale = (RUN_DATE - latest_date).days
            if days_stale > 365:
                root_causes[eid] = {
                    "category": "② 指标已下线/长期停更",
                    "detail": f"最后更新 {latest}，已停更 {days_stale} 天。该指标可能已停止采集或被下架。",
                    "severity": "HIGH",
                }
            elif days_stale > 90:
                root_causes[eid] = {
                    "category": "② 指标已下线/长期停更",
                    "detail": f"最后更新 {latest}，已停更 {days_stale} 天。超过90天阈值。",
                    "severity": "MEDIUM",
                }
            else:
                root_causes[eid] = {
                    "category": "③ 接口权限/范围问题",
                    "detail": f"最后更新 {latest} 在阈值内，但API返回空数据。可能是请求时间范围不匹配或权限限制。",
                    "severity": "LOW",
                }
        except ValueError:
            root_causes[eid] = {
                "category": "未知",
                "detail": f"data_latest={latest} 格式异常，无法判断",
                "severity": "MEDIUM",
            }

log(f"\n  📋 根因分类:")
for eid, rc in root_causes.items():
    log(f"    {eid}: {rc['category']} — {rc['detail']}")

# ============================================================
# 输出 empty_data_report.md
# ============================================================
ed_lines = []
ed_lines.append("# 空数据指标复核报告")
ed_lines.append(f"\n**工单**: {WORK_ORDER}")
ed_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
ed_lines.append(f"**复核对象**: 2 条返回空序列的 zhiji_id")
ed_lines.append("")

for eid in empty_ids:
    d = empty_details[eid]
    rc = root_causes[eid]
    ed_lines.append(f"## `{eid}` — {d.get('series_name','')}")
    ed_lines.append("")
    ed_lines.append("### 基本信息")
    ed_lines.append(f"| 字段 | 值 |")
    ed_lines.append(f"|------|-----|")
    ed_lines.append(f"| zhiji_id | `{eid}` |")
    ed_lines.append(f"| 指标名称 | {d.get('series_name','')} |")
    ed_lines.append(f"| 数据源 | {d.get('source','')} |")
    ed_lines.append(f"| 看板样本 | {d.get('chart_name','')} (sample: {d.get('sample_id','')}) |")
    ed_lines.append(f"| 图表分类 | {d.get('category','')} |")
    ed_lines.append(f"| 出现次数 | {d.get('occurrence_count', 'N/A')} |")
    ed_lines.append(f"|")
    ed_lines.append(f"| **知几侧信息** | |")
    ed_lines.append(f"| 知几单位 | {d.get('zhiji_unit','')} |")
    ed_lines.append(f"| 知几粒度 | {d.get('zhiji_frequency','')} |")
    ed_lines.append(f"| 数据起始 | {d.get('data_latest','N/A')} |")
    ed_lines.append(f"| 数据点 | {d.get('data_points',0)} |")
    ed_lines.append(f"| 错误类型 | {d.get('error_type','')} |")
    ed_lines.append(f"| 错误详情 | {d.get('error_detail','')} |")
    ed_lines.append(f"|")
    ed_lines.append(f"| **framework-tree元数据** | |")
    ed_lines.append(f"| 指标类别 | {d.get('indicator_category','N/A')} |")
    ed_lines.append(f"| 品种 | {d.get('indicator_variety','N/A')} |")
    ed_lines.append(f"| 元数据单位 | {d.get('meta_unit','N/A')} |")
    ed_lines.append(f"| 元数据粒度 | {d.get('meta_freq','N/A')} |")
    ed_lines.append("")
    
    ed_lines.append("### 根因分析")
    ed_lines.append(f"**分类**: {rc['category']}")
    ed_lines.append(f"**严重度**: {rc['severity']}")
    ed_lines.append(f"**分析**: {rc['detail']}")
    ed_lines.append("")
    
    ed_lines.append("### 建议")
    if rc["category"].startswith("①"):
        ed_lines.append("- 该ID可能已从知几下架，建议检查是否有替代指标")
        ed_lines.append("- 若需要此数据，需在indicators_v1.json中寻找替代ID")
    elif rc["category"].startswith("②"):
        ed_lines.append("- 该指标已长期未更新，建议标记为'已废弃'")
        ed_lines.append("- 检查是否有同类指标在活跃更新中可替代")
    elif rc["category"].startswith("③"):
        ed_lines.append("- 建议检查API请求参数（时间范围、权限）")
        ed_lines.append("- 可尝试缩小时间范围或检查X-Data-Key有效性")
    ed_lines.append("")

# 汇总
ed_lines.append("## 汇总")
ed_lines.append("")
ed_lines.append("| zhiji_id | 指标名 | 根因分类 | 严重度 |")
ed_lines.append("|----------|--------|---------|--------|")
for eid in empty_ids:
    d = empty_details[eid]
    rc = root_causes[eid]
    ed_lines.append(f"| `{eid}` | {d.get('series_name','')} | {rc['category']} | {rc['severity']} |")

ed_lines.append(f"\n## 空数据对看板的影响")
ed_lines.append(f"- 涉及看板样本数: {len(detailed_results)} 个 TP 样本中，这 2 条ID影响 2 个样本")
ed_lines.append(f"- 受影响sample: `FUZ_001` (A00价格), `POS_026` (电解铝:社库+厂库)")
ed_lines.append(f"- 注: 这2个样本虽然`pass_mark`为【放行】，但实际数据为空，**HERMES看板需注意排除或标记**")

ed_content = "\n".join(ed_lines)
ed_path = os.path.join(META_DIR, "empty_data_report.md")
with open(ed_path, "w", encoding="utf-8") as f:
    f.write(ed_content)
log(f"\n✅ empty_data_report.md 已写入")

# ============================================================
# T4: 提交产物
# ============================================================
log("\n" + "=" * 72)
log("T4: 提交产物到共享仓库")
log("=" * 72)

output_files = [
    "unit_convert_mapping.json",
    "meta_warning_list.json",
    "meta_quality_summary.md",
    "empty_data_report.md",
]
log(f"\n生成文件:")
for fname in output_files:
    fpath = os.path.join(META_DIR, fname)
    size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
    log(f"  {fname}: {size:,} B")

# 生成MD5校验清单
md5_lines = ["# MD5 校验清单 — 元数据质检"]
md5_lines.append(f"\n**工单**: {WORK_ORDER}")
md5_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
md5_lines.append("")
md5_lines.append("| 文件 | 大小 | MD5 |")
md5_lines.append("|------|------|-----|")
for fname in output_files:
    fpath = os.path.join(META_DIR, fname)
    size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
    md5 = md5_file(fpath) if os.path.exists(fpath) else "N/A"
    md5_lines.append(f"| `{fname}` | {size:,} B | `{md5}` |")
md5_lines.append("")
md5_lines.append("## 约束声明")
md5_lines.append("- NO_SOURCE_MODIFICATION=true")
md5_lines.append("- NO_GT_MODIFICATION=true")
md5_lines.append("- NO_RULE_MODIFICATION=true")
md5_lines.append("- NO_ZHIJI_API_CALL=true")
md5_lines.append("- READ_ONLY=true")
md5_lines.append("- APPEND_ONLY=true")

md5_path = os.path.join(META_DIR, "MD5_CHECKSUM_LIST.md")
with open(md5_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md5_lines))
log(f"\n✅ MD5_CHECKSUM_LIST.md 已写入")

# ============================================================
# 写入运行日志
# ============================================================
log_path = os.path.join(META_DIR, "run_log.txt")
with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

log(f"\n{'='*72}")
log("✅ 元数据质检全部完成")
log(f"输出目录: {META_DIR}")
log(f"生成文件: {', '.join(output_files)}")
log(f"日志: {log_path}")
log(f"{'='*72}")
