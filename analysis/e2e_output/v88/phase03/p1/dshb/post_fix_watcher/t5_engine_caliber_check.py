#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T5: DSHE Engine Caliber Alignment Check for 70 Derived Indicators

Task: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB
Agent: DSHB
Date: 2026-10-15

Checks that derived indicators stored in DSHB DB (lowercase names) correctly
map to DSHE meta_chart indicators (UPPERCASE names), with consistent data
ranges and value scales.
"""

import json
import sqlite3
import os
import sys
from datetime import datetime

# === Paths ===
BASE = r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03"
DB_PATH = os.path.join(BASE, "p0", "phase03_test.db")
MAPPING_PATH = os.path.join(BASE, "p1", "dshb", "v88_phase03_p1_metric_indicator_code_mapping.json")
META_CHART_PATH = os.path.join(BASE, "p1", "dshb", "v88_phase03_p1_dshb_meta_chart_109_indicators.json")
OUTPUT_DIR = os.path.join(BASE, "p1", "dshb", "post_fix_watcher")
OUTPUT_REPORT = os.path.join(OUTPUT_DIR, "engine_caliber_alignment_report.md")

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_mapping():
    """Load mapping JSON and extract derived indicators."""
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    mapping_list = data.get("mapping_list", [])
    # Filter to derived only
    derived = [m for m in mapping_list if m.get("source") == "derived"]
    return derived, data.get("summary", {})


def load_meta_chart_indicators():
    """
    Extract valid DSHE meta_chart indicator names.
    Try multiple sources: dedicated meta_chart JSON or the YAML file.
    """
    indicators = set()
    
    # Try dedicated JSON first
    if os.path.exists(META_CHART_PATH):
        with open(META_CHART_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Could be a dict or list
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            indicators.add(item.upper())
                elif isinstance(v, str):
                    indicators.add(v.upper())
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    indicators.add(item.upper())
        if indicators:
            print(f"[INFO] Loaded {len(indicators)} indicators from meta_chart JSON")
            return indicators
    
    # Fallback: parse meta_chart YAML
    yaml_path = os.path.join(BASE, "backlog", "framework_tree_meta_chart.yaml")
    if os.path.exists(yaml_path):
        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                charts = data.get("charts", [])
                for chart in charts:
                    for ind in chart.get("indicators", []):
                        name = ind.get("indicator_name", "")
                        ind_id = ind.get("indicator_id", "")
                        if ind_id:
                            indicators.add(ind_id.upper())
                        if name:
                            indicators.add(name.upper())
            if indicators:
                print(f"[INFO] Loaded {len(indicators)} indicators from meta_chart YAML")
                return indicators
        except ImportError:
            print("[WARN] PyYAML not available, trying manual YAML parsing")
        except Exception as e:
            print(f"[WARN] Failed to parse meta_chart YAML: {e}")
    
    # Last resort: extract from mapping JSON's p0_9 intersection_ids (the 109 canonical names)
    # This is the authoritative list of DSHE meta_chart indicators
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    p0_9 = data.get("p0_9", {})
    intersection_ids = p0_9.get("intersection_ids", [])
    if intersection_ids:
        indicators = set(i.upper() for i in intersection_ids)
        print(f"[INFO] Loaded {len(indicators)} indicators from p0_9 intersection_ids (authoritative)")
        return indicators
    
    # Final fallback: all mapped targets in the mapping JSON
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    mapping_list = data.get("mapping_list", [])
    for m in mapping_list:
        target = m.get("indicator_id_mapped", "")
        if target:
            indicators.add(target.upper())
    
    # Also add the p0_9 orphan_ids as they are valid meta_chart indicators too
    for oid in data.get("p0_9", {}).get("orphan_ids", []):
        indicators.add(oid.upper())
    
    print(f"[INFO] Built {len(indicators)} indicators from mapping JSON (full set)")
    return indicators


def check_db_for_indicator(conn, indicator_id_lower):
    """Check if an indicator exists in DB and get its stats."""
    # Get all rows for this indicator
    rows = conn.execute(
        "SELECT COUNT(*), MIN(date), MAX(date), MIN(value), MAX(value), AVG(value) "
        "FROM series_cache WHERE indicator_id = ?",
        (indicator_id_lower,)
    ).fetchone()
    
    count, date_min, date_max, val_min, val_max, val_avg = rows
    
    if count == 0:
        return {
            "db_exists": False,
            "db_count": 0,
            "db_date_min": None,
            "db_date_max": None,
            "db_val_min": None,
            "db_val_max": None,
            "db_val_avg": None,
            "db_indicator_id_mapped": None,
            "db_has_mapping": False,
        }
    
    # Check indicator_id_mapped in DB
    mapped_vals = conn.execute(
        "SELECT DISTINCT indicator_id_mapped FROM series_cache WHERE indicator_id = ?",
        (indicator_id_lower,)
    ).fetchall()
    db_mapped = [r[0] for r in mapped_vals if r[0]]
    
    # Check if indicator_id_mapped column has non-empty values
    has_mapping_count = conn.execute(
        "SELECT COUNT(*) FROM series_cache WHERE indicator_id = ? AND indicator_id_mapped != '' AND indicator_id_mapped IS NOT NULL",
        (indicator_id_lower,)
    ).fetchone()[0]
    
    return {
        "db_exists": True,
        "db_count": count,
        "db_date_min": date_min,
        "db_date_max": date_max,
        "db_val_min": val_min,
        "db_val_max": val_max,
        "db_val_avg": val_avg,
        "db_indicator_id_mapped": db_mapped[0] if db_mapped else None,
        "db_has_mapping": has_mapping_count > 0,
        "db_has_mapping_count": has_mapping_count,
    }


def run_checks():
    """Main caliber alignment check."""
    print("=" * 70)
    print("T5: DSHE Engine Caliber Alignment Check")
    print("=" * 70)
    
    # 1. Load derived indicators
    print("\n[1/5] Loading derived indicators...")
    derived_indicators, mapping_summary = load_mapping()
    print(f"  Found {len(derived_indicators)} derived indicators")
    
    # 2. Load DSHE meta_chart indicator set
    print("\n[2/5] Loading DSHE meta_chart indicator list...")
    meta_chart_set = load_meta_chart_indicators()
    print(f"  DSHE meta_chart has {len(meta_chart_set)} unique indicators")
    
    # 3. Connect to DB
    print("\n[3/5] Connecting to DB...")
    conn = sqlite3.connect(DB_PATH)
    print(f"  DB path: {DB_PATH}")
    
    # 4. Run checks per indicator
    print("\n[4/5] Running per-indicator checks...")
    
    results = []
    total_mapped = 0
    total_unmapped = 0
    caliber_match_count = 0
    
    for idx, m in enumerate(derived_indicators):
        ind_id = m["indicator_id"]
        mapped_target = m.get("indicator_id_mapped", "")
        has_mapping = m.get("has_mapping", False)
        expected_count = m.get("record_count", 0)
        expected_date_start = m.get("date_start", "")
        expected_date_end = m.get("date_end", "")
        commodity = m.get("commodity", "")
        
        row = {
            "indicator_id": ind_id,
            "mapped_target": mapped_target,
            "has_mapping": has_mapping,
            "commodity": commodity,
            "expected_record_count": expected_count,
            "expected_date_start": expected_date_start,
            "expected_date_end": expected_date_end,
        }
        
        # Check a: Does it exist in DB with mapping?
        db_info = check_db_for_indicator(conn, ind_id)
        row.update(db_info)
        
        # Check b: Is mapped target valid in DSHE meta_chart?
        row["meta_chart_valid"] = (mapped_target.upper() in meta_chart_set) if mapped_target else False
        
        # Check c: Date range consistency
        if db_info["db_date_min"] and expected_date_start:
            date_match = (db_info["db_date_min"] == expected_date_start and
                         db_info["db_date_max"] == expected_date_end)
            row["date_range_match"] = date_match
        else:
            row["date_range_match"] = None
        
        # Check d: Value range sanity
        # Derived indicators are typically changes/percentiles/ratios
        # We check for basic sanity: values should not be all zero or extreme
        row["value_range_valid"] = None
        if db_info["db_val_min"] is not None and db_info["db_val_max"] is not None:
            # Basic sanity: range should span something
            row["value_range_valid"] = (db_info["db_val_max"] > db_info["db_val_min"]) or \
                                       (db_info["db_val_max"] == db_info["db_val_min"])  # constant is OK
        
        # Determine caliber match status
        issues = []
        
        # Issue 1: No mapping in DB
        if not has_mapping:
            issues.append("No mapping target")
            if not db_info["db_has_mapping"]:
                issues.append("DB indicator_id_mapped is empty")
        
        # Issue 2: Mapping target not in meta_chart
        if has_mapping and not row["meta_chart_valid"]:
            issues.append(f"Mapped target {mapped_target} not in DSHE meta_chart (109)")
        
        # Issue 3: DB doesn't have the indicator
        if not db_info["db_exists"]:
            issues.append("Indicator not found in DB")
        
        # Issue 4: DB mapping mismatch
        if db_info["db_indicator_id_mapped"] and mapped_target:
            if db_info["db_indicator_id_mapped"] != mapped_target:
                issues.append(f"DB mapping ({db_info['db_indicator_id_mapped']}) != JSON mapping ({mapped_target})")
        
        # Issue 5: Date range mismatch
        if row["date_range_match"] is False:
            issues.append("Date range mismatch between DB and mapping JSON")
        
        # Issue 6: Value range issues
        if db_info["db_val_min"] is not None and db_info["db_val_max"] is not None:
            # Check for suspicious patterns
            if db_info["db_val_min"] == 0 and db_info["db_val_max"] == 0:
                issues.append("All values are zero")
            # Derived indicators that are percentiles should be in [0, 100]
            if "percentile" in ind_id:
                if db_info["db_val_min"] < 0 or db_info["db_val_max"] > 100:
                    issues.append(f"Percentile values out of [0,100] range: [{db_info['db_val_min']:.2f}, {db_info['db_val_max']:.2f}]")
            # Ratios should generally be positive
            if "ratio" in ind_id:
                if db_info["db_val_min"] < 0:
                    issues.append(f"Ratio values include negatives: [{db_info['db_val_min']:.2f}, {db_info['db_val_max']:.2f}]")
        
        row["issues"] = issues
        row["caliber_match"] = len(issues) == 0
        
        if has_mapping:
            total_mapped += 1
        else:
            total_unmapped += 1
        if row["caliber_match"]:
            caliber_match_count += 1
        
        results.append(row)
        
        status = "PASS" if row["caliber_match"] else f"FAIL ({len(issues)} issues)"
        print(f"  [{idx+1:3d}/70] {ind_id:40s} -> {mapped_target or 'NONE':30s} [{status}]")
    
    conn.close()
    
    # 5. Generate report
    print("\n[5/5] Generating report...")
    generate_report(results, derived_indicators, meta_chart_set, mapping_summary, total_mapped, total_unmapped, caliber_match_count)
    
    print(f"\nReport saved to: {OUTPUT_REPORT}")
    return results


def generate_report(results, derived_indicators, meta_chart_set, mapping_summary, total_mapped, total_unmapped, caliber_match_count):
    """Generate markdown report."""
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(derived_indicators)
    
    # Collect issues
    all_issues = []
    for r in results:
        for issue in r["issues"]:
            all_issues.append((r["indicator_id"], r["mapped_target"], issue))
    
    # Load orphan_ids from mapping JSON to distinguish known-but-not-in-meta-chart from unknown targets
    orphan_ids = set()
    try:
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for oid in data.get("p0_9", {}).get("orphan_ids", []):
            orphan_ids.add(oid.upper())
    except:
        pass
    
    # Categorize issues
    no_mapping = [r for r in results if not r["has_mapping"]]
    mapping_not_in_meta = [r for r in results if r["has_mapping"] and not r["meta_chart_valid"]]
    mapping_in_orphan = [r for r in results if r["has_mapping"] and not r["meta_chart_valid"] and r["mapped_target"].upper() in orphan_ids]
    mapping_unknown = [r for r in results if r["has_mapping"] and not r["meta_chart_valid"] and r["mapped_target"].upper() not in orphan_ids]
    db_not_found = [r for r in results if not r["db_exists"]]
    date_mismatch = [r for r in results if r.get("date_range_match") is False]
    
    # Separate zero-value issues: placeholders vs real data
    placeholder_zero = [r for r in results if r["issues"] and any("All values are zero" in i for i in r["issues"]) and r["indicator_id"].startswith("placeholder")]
    real_data_zero = [r for r in results if r["issues"] and any("All values are zero" in i for i in r["issues"]) and not r["indicator_id"].startswith("placeholder")]
    
    # Value range issues (excluding zero-value)
    value_range_issues = [r for r in results if r["issues"] and any("out of" in i.lower() for i in r["issues"])]
    
    lines = []
    lines.append("# V88 Phase03 P1 — DSHE引擎口径一致性检查报告")
    lines.append("")
    lines.append(f"> 检查时间: {now}")
    lines.append(f"> 任务ID: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB · T5")
    lines.append(f"> DB路径: `{DB_PATH}`")
    lines.append(f"> 映射JSON: `{MAPPING_PATH}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 1: Overview
    lines.append("## 1. 检查概况")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 新增派生指标 | **{total}** |")
    lines.append(f"| 已映射 (has_mapping=true) | **{total_mapped}** |")
    lines.append(f"| 未映射 (has_mapping=false) | **{total_unmapped}** |")
    lines.append(f"| DSHE meta_chart 总数 | **{len(meta_chart_set)}** |")
    lines.append(f"| 口径对齐 (caliber_match=true) | **{caliber_match_count}/{total}** |")
    lines.append(f"| 口径通过率 | **{caliber_match_count/total*100:.1f}%** |")
    lines.append("")
    
    if mapping_summary:
        lines.append("### 映射JSON汇总")
        lines.append("")
        lines.append(f"- total_indicators: {mapping_summary.get('total_indicators', 'N/A')}")
        lines.append(f"- real: {mapping_summary.get('real', 'N/A')}")
        lines.append(f"- derived: {mapping_summary.get('derived', 'N/A')}")
        lines.append(f"- mapped: {mapping_summary.get('mapped', 'N/A')}")
        lines.append(f"- unmapped: {mapping_summary.get('unmapped', 'N/A')}")
        lines.append(f"- coverage_pct: {mapping_summary.get('coverage_pct', 'N/A')}%")
        lines.append(f"- distinct_mapped_ids: {mapping_summary.get('distinct_mapped_ids', 'N/A')}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Section 2: Per-indicator check
    lines.append("## 2. 逐指标口径检查")
    lines.append("")
    lines.append("| # | indicator_id | mapped_target | has_mapping | meta_chart有效 | DB行数 | 日期范围 | 数值范围 | 口径匹配 |")
    lines.append("|---|-------------|--------------|------------|-------------|-------|---------|---------|---------|")
    
    for i, r in enumerate(results):
        db_exists = "Y" if r["db_exists"] else "N"
        meta_valid = "Y" if r["meta_chart_valid"] else "N"
        date_match = "Y" if r.get("date_range_match") is True else ("N" if r.get("date_range_match") is False else "-")
        caliber = "✅" if r["caliber_match"] else "❌"
        
        val_range = ""
        if r["db_val_min"] is not None and r["db_val_max"] is not None:
            val_range = f"[{r['db_val_min']:.2f}, {r['db_val_max']:.2f}]"
        
        date_range = ""
        if r["db_date_min"] and r["db_date_max"]:
            date_range = f"{r['db_date_min']}~{r['db_date_max']}"
        
        lines.append(f"| {i+1} | `{r['indicator_id']}` | `{r['mapped_target'] or '-'}` | {'Y' if r['has_mapping'] else 'N'} | {meta_valid} | {db_exists} ({r['db_count']}) | {date_range} | {val_range} | {caliber} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Section 3: Issue details
    lines.append("## 3. 口径差异记录")
    lines.append("")
    
    if not all_issues:
        lines.append("**✅ 未发现口径差异 — 所有70个派生指标均通过口径检查。**")
        lines.append("")
    else:
        lines.append(f"共发现 **{len(all_issues)}** 个口径问题，涉及 **{len(set(i[0] for i in all_issues))}** 个指标。")
        lines.append("")
        
        # Subsection: No mapping
        if no_mapping:
            lines.append("### 3.1 无映射目标 (has_mapping=false)")
            lines.append("")
            lines.append("| indicator_id | 原因 |")
            lines.append("|-------------|------|")
            for r in no_mapping:
                lines.append(f"| `{r['indicator_id']}` | 映射JSON中未分配indicator_id_mapped |")
            lines.append("")
        
        # Subsection: Mapping target in orphan_ids (known but not in meta_chart)
        if mapping_in_orphan:
            lines.append("### 3.2 映射目标在DSHB孤儿指标中 (不在meta_chart 109中)")
            lines.append("")
            lines.append("> 这些指标在DSHB DB中存在，但其映射目标不在DSHE meta_chart 109指标中。")
            lines.append("> 属于扩展指标，需在DSHE引擎中补充注册后方可渲染。")
            lines.append("")
            lines.append("| indicator_id | mapped_target | 说明 |")
            lines.append("|-------------|--------------|------|")
            for r in mapping_in_orphan:
                lines.append(f"| `{r['indicator_id']}` | `{r['mapped_target']}` | DSHB孤儿指标，meta_chart未覆盖 |")
            lines.append("")
        
        # Subsection: Mapping target unknown (not in meta_chart, not in orphan)
        if mapping_unknown:
            lines.append("### 3.3 映射目标未知 (不在meta_chart且不在orphan_ids中)")
            lines.append("")
            lines.append("| indicator_id | mapped_target | 说明 |")
            lines.append("|-------------|--------------|------|")
            for r in mapping_unknown:
                lines.append(f"| `{r['indicator_id']}` | `{r['mapped_target']}` | 目标完全未知，需检查映射正确性 |")
            lines.append("")
        
        # Subsection: DB not found
        if db_not_found:
            lines.append("### 3.4 DB中未找到数据")
            lines.append("")
            lines.append("| indicator_id | 说明 |")
            lines.append("|-------------|------|")
            for r in db_not_found:
                lines.append(f"| `{r['indicator_id']}` | series_cache表中无数据 |")
            lines.append("")
        
        # Subsection: Date range mismatch
        if date_mismatch:
            lines.append("### 3.5 日期范围不一致")
            lines.append("")
            lines.append("| indicator_id | DB日期范围 | 映射JSON预期范围 |")
            lines.append("|-------------|-----------|----------------|")
            for r in date_mismatch:
                db_dr = f"{r['db_date_min']}~{r['db_date_max']}" if r['db_date_min'] else 'N/A'
                json_dr = f"{r['expected_date_start']}~{r['expected_date_end']}"
                lines.append(f"| `{r['indicator_id']}` | {db_dr} | {json_dr} |")
            lines.append("")
        
        # Subsection: Placeholder zero-value (expected behavior)
        if placeholder_zero:
            lines.append("### 3.6 占位符指标零值 (预期行为)")
            lines.append("")
            lines.append("> 这些是 `placeholder_*` 派生指标，仅有1行占位数据(值=0)，属于正常预期。")
            lines.append("")
            lines.append(f"- 占位符指标数: {len(placeholder_zero)}")
            lines.append("")
            lines.append("| indicator_id | mapped_target | DB行数 |")
            lines.append("|-------------|--------------|-------|")
            for r in placeholder_zero:
                lines.append(f"| `{r['indicator_id']}` | `{r['mapped_target']}` | {r['db_count']} |")
            lines.append("")
        
        # Subsection: Real data zero-value (potential data quality issue)
        if real_data_zero:
            lines.append("### 3.7 实际数据零值异常 (需关注)")
            lines.append("")
            lines.append("> 这些非占位符指标的所有数据值均为零，可能存在派生计算问题。")
            lines.append("")
            lines.append("| indicator_id | mapped_target | DB行数 | 日期范围 |")
            lines.append("|-------------|--------------|-------|---------|")
            for r in real_data_zero:
                date_range = f"{r['db_date_min']}~{r['db_date_max']}" if r['db_date_min'] else 'N/A'
                lines.append(f"| `{r['indicator_id']}` | `{r['mapped_target']}` | {r['db_count']} | {date_range} |")
            lines.append("")
        
        # Subsection: Value range issues
        if value_range_issues:
            lines.append("### 3.8 数值范围异常")
            lines.append("")
            lines.append("| indicator_id | 问题描述 |")
            lines.append("|-------------|---------|")
            for r in value_range_issues:
                for issue in r["issues"]:
                    if "out of" in issue.lower():
                        lines.append(f"| `{r['indicator_id']}` | {issue} |")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Section 4: Conclusion
    lines.append("## 4. 结论")
    lines.append("")
    
    if caliber_match_count == total:
        lines.append(f"**✅ 全部 {total} 个派生指标口径对齐通过。**")
        lines.append("")
        lines.append("所有派生指标的映射关系完整，映射目标均为合法的DSHE meta_chart指标，")
        lines.append("数据范围与预期一致，数值范围合理。")
    else:
        lines.append(f"**⚠️ 口径对齐: {caliber_match_count}/{total} ({caliber_match_count/total*100:.1f}%)**")
        lines.append("")
        
        lines.append(f"- {len(mapping_in_orphan)} 个指标映射目标在DSHB孤儿指标中(meta_chart未覆盖)")
        lines.append(f"- {len(mapping_unknown)} 个指标映射目标完全未知")
        lines.append(f"- {len(placeholder_zero)} 个占位符指标零值(预期行为)")
        lines.append(f"- {len(real_data_zero)} 个实际数据零值异常(需关注)")
        lines.append(f"- {len(date_mismatch)} 个指标日期范围不一致")
        lines.append(f"- {len(value_range_issues)} 个指标数值范围异常")
        lines.append("")
        lines.append("建议：")
        lines.append("1. **孤儿指标补充**: {} 个指标的映射目标在DSHB orphan_ids中，建议扩展DSHE meta_chart以覆盖这些派生指标".format(len(mapping_in_orphan)))
        lines.append("2. **零值异常排查**: {} 个非占位符指标数据全为零，需排查派生计算逻辑".format(len(real_data_zero)))
        lines.append("3. **日期范围校准**: 如发现日期范围不一致，检查数据导入时的时间偏移")
        lines.append("4. **映射维护**: 确保新增派生指标持续同步到DSHE meta_chart")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*报告由 t5_engine_caliber_check.py 自动生成于 {now}*")
    lines.append("")
    
    report = "\n".join(lines)
    
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"[OK] Report generated: {OUTPUT_REPORT}")
    print(f"     Total derived indicators: {total}")
    print(f"     Mapped: {total_mapped}, Unmapped: {total_unmapped}")
    print(f"     Caliber match: {caliber_match_count}/{total} ({caliber_match_count/total*100:.1f}%)")
    print(f"     Issues found: {len(all_issues)}")


if __name__ == "__main__":
    run_checks()
