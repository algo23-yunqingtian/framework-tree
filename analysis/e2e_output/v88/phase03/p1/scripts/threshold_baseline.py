#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
threshold_baseline.py — V88 Phase03 P1 DSHB 三级阈值基线
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  计算全量指标三级阈值基线 (正常/预警/熔断),
  为 CPU 熔断阈值配置提供数据底座。

  三级阈值:
    NORMAL:    P10 ~ P90 (正常波动区间)
    WARNING:   P05 ~ P10 或 P90 ~ P95 (预警区间)
    TRIP:      < P05 或 > P95 (熔断区间)

  使用全量历史数据计算百分位, 确保基线覆盖完整时间跨度。

Usage:
  python threshold_baseline.py [--db path/to/phase03_test.db]
"""

import os
import sys
import sqlite3
import platform
import argparse
import json
from pathlib import Path
from datetime import datetime
import math

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
P0_DIR = SCRIPT_DIR.parent.parent.parent
P1_DIR = SCRIPT_DIR.parent
DB_PATH_DEFAULT = P0_DIR / "p0" / "phase03_test.db"
OUTPUT_DIR = P1_DIR / "dshb"

# Percentile thresholds for three levels
NORMAL_LO = 10    # P10
NORMAL_HI = 90    # P90
WARN_LO = 5       # P05
WARN_HI = 95      # P95
TRIP_LO = 0       # < P05
TRIP_HI = 100     # > P95


def setup_environment():
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def compute_percentile(values, percentile):
    """Compute percentile from a sorted list of values."""
    if not values:
        return 0
    sorted_vals = sorted(values)
    k = (percentile / 100.0) * (len(sorted_vals) - 1)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_vals) else f
    d = k - f
    result = sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])
    return round(result, 6)


def classify_threshold(value, thresholds):
    """Classify a value into NORMAL/WARNING/TRIP based on thresholds."""
    if value is None:
        return "UNKNOWN"
    if value < thresholds["trip_lo"] or value > thresholds["trip_hi"]:
        return "TRIP"
    if value < thresholds["warn_lo"] or value > thresholds["warn_hi"]:
        return "WARNING"
    return "NORMAL"


def compute_indicator_thresholds(conn, indicator_id):
    """Compute three-level thresholds for a single indicator."""
    cur = conn.cursor()
    cur.execute("SELECT value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date", (indicator_id,))
    values = [r[0] for r in cur.fetchall()]

    if len(values) < 10:
        return None

    # Basic stats
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5
    min_v = min(values)
    max_v = max(values)

    # Percentile thresholds
    p05 = compute_percentile(values, 5)
    p10 = compute_percentile(values, 10)
    p25 = compute_percentile(values, 25)
    p50 = compute_percentile(values, 50)
    p75 = compute_percentile(values, 75)
    p90 = compute_percentile(values, 90)
    p95 = compute_percentile(values, 95)

    # Three-level thresholds
    thresholds = {
        "normal_lo": p10,
        "normal_hi": p90,
        "warn_lo": p05,
        "warn_hi": p95,
        "trip_lo": p05,
        "trip_hi": p95,
    }

    # Current value and classification
    cur.execute("SELECT value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date DESC LIMIT 1", (indicator_id,))
    cur_val = cur.fetchone()
    current_value = cur_val[0] if cur_val else None
    classification = classify_threshold(current_value, thresholds)

    # Recent volatility (last 20 values std)
    recent = values[-20:] if len(values) >= 20 else values
    recent_mean = sum(recent) / len(recent)
    recent_std = (sum((v - recent_mean) ** 2 for v in recent) / len(recent)) ** 0.5

    # Range (max - min) as volatility proxy
    range_v = max_v - min_v

    return {
        "indicator_id": indicator_id,
        "data_points": len(values),
        "stats": {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(min_v, 4),
            "max": round(max_v, 4),
            "range": round(range_v, 4),
            "recent_std_20d": round(recent_std, 4),
        },
        "percentiles": {
            "p05": round(p05, 4),
            "p10": round(p10, 4),
            "p25": round(p25, 4),
            "p50": round(p50, 4),
            "p75": round(p75, 4),
            "p90": round(p90, 4),
            "p95": round(p95, 4),
        },
        "thresholds": thresholds,
        "current_value": round(current_value, 4) if current_value is not None else None,
        "classification": classification,
    }


def generate_threshold_report(all_thresholds, db_path):
    """Generate Markdown threshold baseline report."""
    now = datetime.now().isoformat()
    total = len(all_thresholds)
    normal_count = sum(1 for t in all_thresholds if t["classification"] == "NORMAL")
    warning_count = sum(1 for t in all_thresholds if t["classification"] == "WARNING")
    trip_count = sum(1 for t in all_thresholds if t["classification"] == "TRIP")

    # Group by commodity
    by_comm = {}
    for t in all_thresholds:
        ind_id = t["indicator_id"]
        # Extract commodity from indicator_id prefix
        parts = ind_id.split("_")
        comm = parts[0] if parts else "unknown"
        if comm not in by_comm:
            by_comm[comm] = []
        by_comm[comm].append(t)

    lines = []
    lines.append("# V88 Phase03 P1 — 三级阈值基线文档")
    lines.append("")
    lines.append(f"> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB")
    lines.append(f"> **AGENT**: DSHB | **BRANCH**: feature/v88-g1")
    lines.append(f"> **生成时间**: {now}")
    lines.append(f"> **数据库**: `{db_path}`")
    lines.append(f"> **目的**: 为 CPU 熔断阈值配置提供数据底座")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. 阈值定义")
    lines.append("")
    lines.append("| 级别 | 百分位区间 | 含义 | 动作 |")
    lines.append("|------|-----------|------|------|")
    lines.append("| **正常** | P10 ~ P90 | 正常波动区间 | 持续监控 |")
    lines.append("| **预警** | P05~P10 或 P90~P95 | 异常波动预警 | 发出告警 |")
    lines.append("| **熔断** | < P05 或 > P95 | 极端异常 | 触发熔断 |")
    lines.append("")
    lines.append("## 2. 总体统计")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|-----:|")
    lines.append(f"| 总指标数 | {total} |")
    lines.append(f"| 正常区间 | {normal_count} ({normal_count/total*100:.1f}%) |")
    lines.append(f"| 预警区间 | {warning_count} ({warning_count/total*100:.1f}%) |")
    lines.append(f"| 熔断区间 | {trip_count} ({trip_count/total*100:.1f}%) |")
    lines.append("")

    # Per-commodity summary
    lines.append("## 3. 分品种统计")
    lines.append("")
    lines.append("| 品种 | 指标数 | 正常 | 预警 | 熔断 |")
    lines.append("|------|------:|-----:|-----:|-----:|")
    for comm in sorted(by_comm.keys()):
        items = by_comm[comm]
        n = sum(1 for t in items if t["classification"] == "NORMAL")
        w = sum(1 for t in items if t["classification"] == "WARNING")
        t = sum(1 for t in items if t["classification"] == "TRIP")
        lines.append(f"| {comm:<8} | {len(items):>5} | {n:>5} | {w:>5} | {t:>5} |")
    lines.append("")

    # Detailed table (top 50 indicators by volatility)
    sorted_by_vol = sorted(all_thresholds, key=lambda t: t["stats"]["range"], reverse=True)
    lines.append("## 4. 波动率排名 (Top 50)")
    lines.append("")
    lines.append("| # | indicator_id | 数据点 | 均值 | 标准差 | 波动范围 | P10 | P90 | 当前值 | 级别 |")
    lines.append("|---|-------------|------:|-----:|------:|--------:|----:|----:|------:|:----:|")
    for i, t in enumerate(sorted_by_vol[:50], 1):
        lines.append(
            f"| {i} | `{t['indicator_id']}` | {t['data_points']:,} | {t['stats']['mean']:.2f} | "
            f"{t['stats']['std']:.2f} | {t['stats']['range']:.2f} | {t['thresholds']['normal_lo']:.2f} | "
            f"{t['thresholds']['normal_hi']:.2f} | {t['current_value']:.2f} | {t['classification']} |"
        )
    lines.append("")

    # All indicators detail
    lines.append("## 5. 全量阈值明细")
    lines.append("")
    lines.append(f"> 共 {total} 个指标。完整 JSON 数据见 `threshold_baseline_data.json`。")
    lines.append("")
    lines.append("| # | indicator_id | P05 | P10 | P50 | P90 | P95 | 当前值 | 级别 |")
    lines.append("|---|-------------|----:|----:|----:|----:|----:|------:|:----:|")
    for i, t in enumerate(all_thresholds, 1):
        cv = t['current_value']
        cv_str = f"{cv:.2f}" if cv is not None else "N/A"
        lines.append(
            f"| {i} | `{t['indicator_id']}` | {t['percentiles']['p05']:.2f} | {t['percentiles']['p10']:.2f} | "
            f"{t['percentiles']['p50']:.2f} | {t['percentiles']['p90']:.2f} | {t['percentiles']['p95']:.2f} | "
            f"{cv_str} | {t['classification']} |"
        )
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by threshold_baseline.py | {now}*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P1 — Three-Level Threshold Baseline"
    )
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT),
                        help="Path to phase03_test.db")
    args = parser.parse_args()

    setup_environment()

    db_path = Path(args.db)
    print("=" * 72)
    print("  V88 Phase03 P1 · DSHB 三级阈值基线")
    print("  TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB")
    print("=" * 72)
    print(f"  DB path: {db_path}")
    print()

    if not db_path.exists():
        print(f"  DATABASE NOT FOUND: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Get all indicators
    cur.execute("SELECT DISTINCT indicator_id FROM series_cache ORDER BY indicator_id")
    indicators = [r[0] for r in cur.fetchall()]
    print(f"  Total indicators: {len(indicators)}")
    print()

    all_thresholds = []
    for i, ind_id in enumerate(indicators, 1):
        if i % 100 == 0 or i == len(indicators):
            print(f"  [{i}/{len(indicators)}] Computed {len(all_thresholds)} thresholds...")

        result = compute_indicator_thresholds(conn, ind_id)
        if result:
            all_thresholds.append(result)

    conn.close()

    print(f"\n  Computed {len(all_thresholds)} indicator thresholds")

    # Classify summary
    normal = sum(1 for t in all_thresholds if t["classification"] == "NORMAL")
    warning = sum(1 for t in all_thresholds if t["classification"] == "WARNING")
    trip = sum(1 for t in all_thresholds if t["classification"] == "TRIP")
    print(f"  NORMAL: {normal} | WARNING: {warning} | TRIP: {trip}")

    # Generate Markdown report
    md_content = generate_threshold_report(all_thresholds, db_path)
    md_path = OUTPUT_DIR / "v88_phase03_p1_3level_threshold_baseline.md"
    with open(str(md_path), "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n  [MD]   Written: {md_path} ({len(md_content):,} bytes)")

    # Generate JSON data
    now = datetime.now().isoformat()
    json_data = {
        "task_id": "V88_PHASE03_P1_DSHB_MAIN_JOB",
        "agent": "DSHB",
        "branch": "feature/v88-g1",
        "generated": now,
        "database": str(db_path),
        "threshold_definitions": {
            "normal": "P10 ~ P90",
            "warning": "P05~P10 or P90~P95",
            "trip": "< P05 or > P95",
        },
        "summary": {
            "total_indicators": len(all_thresholds),
            "normal": normal,
            "warning": warning,
            "trip": trip,
        },
        "thresholds": all_thresholds,
    }
    json_path = OUTPUT_DIR / "threshold_baseline_data.json"
    with open(str(json_path), "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"  [JSON] Written: {json_path} ({len(json.dumps(json_data)):,} bytes)")

    print("\n  Done.")
    sys.exit(0)


if __name__ == "__main__":
    main()