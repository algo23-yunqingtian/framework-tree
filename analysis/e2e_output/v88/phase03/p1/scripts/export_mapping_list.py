#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_mapping_list.py — V88 Phase03 P1 DSHB 映射清单导出
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  Export complete mapping list from phase03_test.db as Markdown and JSON.
  P1 update: includes 59 derived indicators, P0-9 denominator restored to 109.

Usage:
  python export_mapping_list.py [--db path/to/phase03_test.db]
"""

import os
import sys
import sqlite3
import json
import platform
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
P0_DIR = SCRIPT_DIR.parent.parent.parent
P1_DIR = SCRIPT_DIR.parent
DB_PATH_DEFAULT = P0_DIR / "p0" / "phase03_test.db"
OUTPUT_DIR = P1_DIR / "dshb"


def setup_environment():
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def export_mapping(conn, db_path):
    cur = conn.cursor()
    cur.execute("""
        SELECT indicator_id, indicator_id_mapped, commodity,
               COUNT(*) as record_count, MIN(date) as date_start, MAX(date) as date_end,
               MIN(source) as source_type
        FROM series_cache
        GROUP BY indicator_id, indicator_id_mapped, commodity
        ORDER BY commodity, indicator_id
    """)
    rows = cur.fetchall()
    mapping_list = []
    for row in rows:
        ind_id, mapped_id, commodity, count, date_start, date_end, source = row
        has_mapping = mapped_id is not None and mapped_id != ''
        mapping_list.append({
            "indicator_id": ind_id,
            "indicator_id_mapped": mapped_id if has_mapping else "",
            "commodity": commodity,
            "has_mapping": has_mapping,
            "record_count": count,
            "date_start": date_start,
            "date_end": date_end,
            "source": source,
        })
    return mapping_list


def generate_markdown(mapping_list, db_path):
    now = datetime.now().isoformat()
    total = len(mapping_list)
    mapped = sum(1 for m in mapping_list if m["has_mapping"])
    unmapped = total - mapped
    pct = mapped / total * 100 if total > 0 else 0
    derived_count = sum(1 for m in mapping_list if m["source"] == "derived")
    real_count = sum(1 for m in mapping_list if m["source"] == "real")

    by_commodity = {}
    for m in mapping_list:
        comm = m["commodity"]
        if comm not in by_commodity:
            by_commodity[comm] = {"total": 0, "mapped": 0, "unmapped": 0, "derived": 0, "real": 0}
        by_commodity[comm]["total"] += 1
        if m["has_mapping"]:
            by_commodity[comm]["mapped"] += 1
        else:
            by_commodity[comm]["unmapped"] += 1
        if m["source"] == "derived":
            by_commodity[comm]["derived"] += 1
        else:
            by_commodity[comm]["real"] += 1

    # P0-9 metric
    # Count distinct mapped indicator_ids (DSHE meta_chart side)
    distinct_mapped_ids = len(set(m['indicator_id_mapped'] for m in mapping_list if m['has_mapping']))
    p0_9_denominator = 109  # Fixed denominator per P1 requirement
    p0_9_numerator = min(distinct_mapped_ids, p0_9_denominator)
    p0_9_pct = p0_9_numerator / p0_9_denominator * 100

    lines = []
    lines.append("# V88 Phase03 P1 — Metric/Indicator/Code Complete Mapping List")
    lines.append("")
    lines.append(f"> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB")
    lines.append(f"> **AGENT**: DSHB | **BRANCH**: feature/v88-g1")
    lines.append(f"> **生成时间**: {now}")
    lines.append(f"> **数据库**: `{db_path}`")
    lines.append(f"> **目的**: Complete export of all indicator_id / indicator_id_mapped / commodity mappings")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total unique indicators | {total} |")
    lines.append(f"| Real indicators | {real_count} |")
    lines.append(f"| Derived indicators | {derived_count} |")
    lines.append(f"| Mapped indicators | {mapped} ({pct:.1f}%) |")
    lines.append(f"| Unmapped indicators | {unmapped} ({100 - pct:.1f}%) |")
    lines.append(f"| Distinct mapped IDs (DSHE meta_chart) | {distinct_mapped_ids} |")
    lines.append(f"| P0-9 denominator (restored) | {p0_9_denominator} |")
    lines.append(f"| P0-9 numerator | {p0_9_numerator} |")
    lines.append(f"| P0-9 coverage | **{p0_9_pct:.2f}%** |")
    lines.append("")

    # Per-commodity summary
    lines.append("## 2. Per-Commodity Mapping Coverage")
    lines.append("")
    lines.append("| Commodity | Total | Real | Derived | Mapped | Unmapped | Coverage % |")
    lines.append("|-----------|------:|-----:|--------:|-------:|---------:|-----------:|")
    for comm in sorted(by_commodity.keys()):
        d = by_commodity[comm]
        cov = d["mapped"] / d["total"] * 100 if d["total"] > 0 else 0
        lines.append(f"| {comm:<8} | {d['total']:>5} | {d['real']:>4} | {d['derived']:>7} | {d['mapped']:>6} | {d['unmapped']:>8} | {cov:>9.1f}% |")
    lines.append("")

    # Derived indicators detail
    derived_list = [m for m in mapping_list if m["source"] == "derived"]
    if derived_list:
        lines.append("## 3. Derived Indicators (59 R-V88-033)")
        lines.append("")
        lines.append(f"> {len(derived_list)} derived indicators computed from base data.")
        lines.append("")
        lines.append("| # | indicator_id | indicator_id_mapped | commodity | records |")
        lines.append("|---|-------------|--------------------|-----------|--------:|")
        for i, m in enumerate(derived_list, 1):
            mapped_str = m["indicator_id_mapped"] if m["indicator_id_mapped"] else "(unmapped)"
            lines.append(f"| {i} | `{m['indicator_id']}` | `{mapped_str}` | {m['commodity']} | {m['record_count']:,} |")
        lines.append("")

    # Complete mapping table (first 100)
    lines.append("## 4. Complete Mapping Table (Top 100)")
    lines.append("")
    lines.append(f"> {total} rows total. Showing first 100 sorted by commodity, then indicator_id.")
    lines.append("")
    lines.append("| # | indicator_id | indicator_id_mapped | commodity | source | records |")
    lines.append("|---|-------------|--------------------|-----------|--------|--------:|")
    for i, m in enumerate(mapping_list[:100], 1):
        mapped_str = m["indicator_id_mapped"] if m["indicator_id_mapped"] else "(unmapped)"
        lines.append(f"| {i} | `{m['indicator_id']}` | `{mapped_str}` | {m['commodity']} | {m['source']} | {m['record_count']:,} |")
    lines.append("")

    # Unmapped indicators
    unmapped_list = [m for m in mapping_list if not m["has_mapping"]]
    if unmapped_list:
        lines.append("## 5. Unmapped Indicators")
        lines.append("")
        lines.append(f"> {len(unmapped_list)} indicators have no mapping.")
        lines.append("")
        lines.append("| # | indicator_id | commodity | source | records |")
        lines.append("|---|-------------|-----------|--------|--------:|")
        for i, m in enumerate(unmapped_list, 1):
            lines.append(f"| {i} | `{m['indicator_id']}` | {m['commodity']} | {m['source']} | {m['record_count']:,} |")
        lines.append("")

    lines.append("## 6. P0-9 Coverage Report")
    lines.append("")
    lines.append("| 口径 | 分子 | 分母 | 比率 | 状态 |")
    lines.append("|------|:----:|:----:|:----:|:----:|")
    lines.append(f"| DB映射命中率 (P0-9) | {p0_9_numerator} | {p0_9_denominator} | **{p0_9_pct:.2f}%** | {'PASS' if p0_9_pct >= 60 else 'FAIL'} |")
    lines.append(f"| DSHE指标数 | {distinct_mapped_ids} | - | - | - |")
    lines.append(f"| 总指标数 | {total} | - | - | - |")
    lines.append(f"| 派生指标数 | {derived_count} | - | - | - |")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by export_mapping_list.py | {now}*")

    return "\n".join(lines)


def generate_json(mapping_list, db_path):
    now = datetime.now().isoformat()
    total = len(mapping_list)
    mapped = sum(1 for m in mapping_list if m["has_mapping"])
    derived_count = sum(1 for m in mapping_list if m["source"] == "derived")
    distinct_mapped = len(set(m['indicator_id_mapped'] for m in mapping_list if m['has_mapping']))
    pct = mapped / total * 100 if total > 0 else 0

    data = {
        "task_id": "V88_PHASE03_P1_DSHB_MAIN_JOB",
        "agent": "DSHB",
        "branch": "feature/v88-g1",
        "generated": now,
        "database": str(db_path),
        "summary": {
            "total_indicators": total,
            "real": sum(1 for m in mapping_list if m["source"] == "real"),
            "derived": derived_count,
            "mapped": mapped,
            "unmapped": total - mapped,
            "coverage_pct": round(pct, 2),
            "distinct_mapped_ids": distinct_mapped,
        },
        "p0_9": {
            "denominator": 109,
            "numerator": min(distinct_mapped, 109),
            "coverage_pct": round(min(distinct_mapped, 109) / 109 * 100, 2),
        },
        "mapping_list": mapping_list,
    }

    return json.dumps(data, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Export mapping list from phase03_test.db (P1)")
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT), help="Path to phase03_test.db")
    args = parser.parse_args()

    setup_environment()
    db_path = Path(args.db)
    print(f"Exporting mapping list from: {db_path}")

    conn = sqlite3.connect(str(db_path))
    mapping_list = export_mapping(conn, db_path)
    conn.close()

    md_content = generate_markdown(mapping_list, db_path)
    md_path = OUTPUT_DIR / "v88_phase03_p1_metric_indicator_code_mapping.md"
    with open(str(md_path), "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[MD]   Written: {md_path} ({len(md_content):,} bytes)")

    json_content = generate_json(mapping_list, db_path)
    json_path = OUTPUT_DIR / "v88_phase03_p1_metric_indicator_code_mapping.json"
    with open(str(json_path), "w", encoding="utf-8") as f:
        f.write(json_content)
    print(f"[JSON] Written: {json_path} ({len(json_content):,} bytes)")

    total = len(mapping_list)
    mapped = sum(1 for m in mapping_list if m["has_mapping"])
    derived = sum(1 for m in mapping_list if m["source"] == "derived")
    print(f"\n  Total indicators: {total}")
    print(f"  Mapped: {mapped} ({mapped/total*100:.1f}%)")
    print(f"  Derived: {derived}")
    print(f"\n  Export complete.")


if __name__ == "__main__":
    main()