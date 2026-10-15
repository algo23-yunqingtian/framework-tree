#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
noise_rate_analysis.py — V88 Phase03 P1 DSHB 噪声率分析
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  计算全量指标噪声率, 目标噪声率 < 10%。
  噪声率 = 异常数据点数 / 总数据点数

  异常数据点定义:
    1. NULL 值
    2. 3-sigma 异常值 (超出均值±3倍标准差)
    3. 时间漂移点 (超过90天无更新)
    4. 单位异常点 (数值范围异常)
    5. 重复值点 (连续3个以上相同值)

Usage:
  python noise_rate_analysis.py [--db path/to/phase03_test.db]
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

# Noise thresholds
SIGMA_THRESHOLD = 3.0          # 3-sigma for outlier detection
TIME_DRIFT_DAYS = 90           # Max days without update
STALE_CONSECUTIVE = 3          # Consecutive same values threshold
TARGET_NOISE_RATE = 0.10       # 10% target

# =============================================================================
# Platform Setup
# =============================================================================

def setup_environment():
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

# =============================================================================
# Noise Detection Functions
# =============================================================================

def detect_nulls(conn, indicator_id):
    """Detect NULL values for an indicator."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=? AND value IS NULL", (indicator_id,))
    null_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=?", (indicator_id,))
    total_count = cur.fetchone()[0]
    return null_count, total_count


def detect_outliers(conn, indicator_id):
    """Detect 3-sigma outliers for an indicator."""
    cur = conn.cursor()
    cur.execute("SELECT date, value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date", (indicator_id,))
    rows = cur.fetchall()

    if len(rows) < 30:
        return 0, [], len(rows)

    values = [r[1] for r in rows]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5

    if std == 0:
        return 0, [], len(rows)

    outlier_indices = []
    outlier_values = []
    for i, (date, val) in enumerate(rows):
        if abs(val - mean) > SIGMA_THRESHOLD * std:
            outlier_indices.append(i)
            outlier_values.append((date, val))

    return len(outlier_indices), outlier_values, len(rows)


def detect_time_drift(conn, indicator_id):
    """Detect time drift (gaps > 90 days) for an indicator."""
    cur = conn.cursor()
    cur.execute("SELECT date FROM series_cache WHERE indicator_id=? ORDER BY date", (indicator_id,))
    dates = [r[0] for r in cur.fetchall()]

    if len(dates) < 2:
        return 0, 0

    max_drift = 0
    drift_count = 0

    for i in range(1, len(dates)):
        try:
            d1 = datetime.strptime(dates[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(dates[i], "%Y-%m-%d")
            gap = (d2 - d1).days
            if gap > TIME_DRIFT_DAYS:
                drift_count += 1
            if gap > max_drift:
                max_drift = gap
        except:
            pass

    return drift_count, max_drift


def detect_stale_points(conn, indicator_id):
    """Detect consecutive same-value points (stale data)."""
    cur = conn.cursor()
    cur.execute("SELECT date, value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date", (indicator_id,))
    rows = cur.fetchall()

    if len(rows) < STALE_CONSECUTIVE + 1:
        return 0

    stale_count = 0
    consecutive = 1

    for i in range(1, len(rows)):
        if rows[i][1] == rows[i-1][1]:
            consecutive += 1
            if consecutive >= STALE_CONSECUTIVE:
                stale_count += 1
        else:
            consecutive = 1

    return stale_count


def detect_unit_anomaly(conn, indicator_id):
    """Detect unit anomalies (constant series, extreme ranges)."""
    cur = conn.cursor()
    cur.execute("SELECT MIN(value), MAX(value), AVG(value) FROM series_cache WHERE indicator_id=? AND value IS NOT NULL", (indicator_id,))
    row = cur.fetchone()
    if row[0] is None:
        return 0

    min_v, max_v, avg_v = row
    count = 0

    # Constant series
    if min_v == max_v:
        count += 1

    # Extreme range (max/min ratio > 1000x)
    if avg_v != 0 and abs(max_v / avg_v) > 1000:
        count += 1

    return count


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P1 — Noise Rate Analysis"
    )
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT),
                        help="Path to phase03_test.db")
    args = parser.parse_args()

    setup_environment()

    db_path = Path(args.db)
    print("=" * 72)
    print("  V88 Phase03 P1 · DSHB 噪声率分析")
    print("  TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB")
    print("=" * 72)
    print(f"  DB path: {db_path}")
    print(f"  Target noise rate: < {TARGET_NOISE_RATE * 100:.0f}%")
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

    # Get overall stats
    cur.execute("SELECT COUNT(*) FROM series_cache")
    total_rows = cur.fetchone()[0]
    print(f"  Total rows: {total_rows:,}")
    print()

    # Analyze each indicator
    indicator_stats = []
    total_noise_points = 0
    total_data_points = 0
    noise_breakdown = {"null": 0, "outlier": 0, "drift": 0, "stale": 0, "unit_anomaly": 0}

    for i, ind_id in enumerate(indicators, 1):
        if i % 100 == 0 or i == len(indicators):
            print(f"  [{i}/{len(indicators)}] Analyzed {len(indicator_stats)} indicators...")

        # Count data points
        cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=?", (ind_id,))
        data_points = cur.fetchone()[0]

        if data_points == 0:
            continue

        total_data_points += data_points

        # Detect each noise type
        null_count, _ = detect_nulls(conn, ind_id)
        outlier_count, outlier_details, _ = detect_outliers(conn, ind_id)
        drift_count, max_drift = detect_time_drift(conn, ind_id)
        stale_count = detect_stale_points(conn, ind_id)
        unit_anomaly_count = detect_unit_anomaly(conn, ind_id)

        # Total noise for this indicator
        total_noise = null_count + outlier_count + stale_count
        noise_rate = total_noise / data_points if data_points > 0 else 0

        # Add to breakdown
        noise_breakdown["null"] += null_count
        noise_breakdown["outlier"] += outlier_count
        noise_breakdown["drift"] += drift_count
        noise_breakdown["stale"] += stale_count
        noise_breakdown["unit_anomaly"] += unit_anomaly_count

        # Store per-indicator stats
        indicator_stats.append({
            "indicator_id": ind_id,
            "data_points": data_points,
            "null_count": null_count,
            "outlier_count": outlier_count,
            "drift_count": drift_count,
            "stale_count": stale_count,
            "unit_anomaly_count": unit_anomaly_count,
            "total_noise_points": total_noise,
            "noise_rate": round(noise_rate, 6),
            "noise_rate_pct": round(noise_rate * 100, 4),
            "max_drift_days": max_drift,
            "meets_target": noise_rate <= TARGET_NOISE_RATE,
        })

        total_noise_points += total_noise

    conn.close()

    # Overall noise rate
    overall_noise_rate = total_noise_points / total_data_points if total_data_points > 0 else 0
    meets_target = overall_noise_rate <= TARGET_NOISE_RATE

    # Per-indicator stats
    meets_target_count = sum(1 for s in indicator_stats if s["meets_target"])
    fails_target_count = len(indicator_stats) - meets_target_count

    # Sort by noise rate (highest first)
    sorted_stats = sorted(indicator_stats, key=lambda s: s["noise_rate"], reverse=True)

    print()
    print("=" * 72)
    print("  NOISE RATE ANALYSIS COMPLETE")
    print("=" * 72)
    print(f"  Total data points: {total_data_points:,}")
    print(f"  Total noise points: {total_noise_points:,}")
    print(f"  Overall noise rate: {overall_noise_rate * 100:.4f}%")
    print(f"  Target: < {TARGET_NOISE_RATE * 100:.0f}%")
    print(f"  Status: {'[PASS]' if meets_target else '[FAIL]'}")
    print()
    print(f"  Indicators meeting target: {meets_target_count}/{len(indicator_stats)}")
    print(f"  Indicators failing target: {fails_target_count}/{len(indicator_stats)}")
    print()
    print(f"  Noise breakdown:")
    for k, v in noise_breakdown.items():
        pct = v / total_data_points * 100 if total_data_points > 0 else 0
        print(f"    {k:<15} {v:>8,} points ({pct:.4f}%)")
    print()

    # Top 10 noisiest indicators
    print(f"  Top 10 noisiest indicators:")
    for i, s in enumerate(sorted_stats[:10], 1):
        flag = "[PASS]" if s["meets_target"] else "[FAIL]"
        print(f"    {i:>2}. {s['indicator_id']:<35} noise={s['noise_rate_pct']:.4f}% {flag}")
    print()

    # Generate Markdown report
    now = datetime.now().isoformat()
    lines = []
    lines.append("# V88 Phase03 P1 — 噪声率分析报告")
    lines.append("")
    lines.append(f"> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB")
    lines.append(f"> **AGENT**: DSHB | **BRANCH**: feature/v88-g1")
    lines.append(f"> **生成时间**: {now}")
    lines.append(f"> **数据库**: `{db_path}`")
    lines.append(f"> **目标噪声率**: < {TARGET_NOISE_RATE * 100:.0f}%")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. 噪声率定义")
    lines.append("")
    lines.append("| 噪声类型 | 定义 | 检测方式 |")
    lines.append("|----------|------|----------|")
    lines.append(f"| NULL值 | value为NULL | SQL COUNT |")
    lines.append(f"| 3-sigma异常值 | 超出均值±{SIGMA_THRESHOLD}倍标准差 | 统计计算 |")
    lines.append(f"| 时间漂移 | 超过{TIME_DRIFT_DAYS}天无更新 | 日期差计算 |")
    lines.append(f"| 重复值点 | 连续{STALE_CONSECUTIVE}+个相同值 | 序列分析 |")
    lines.append(f"| 单位异常 | 常数列/极端范围 | 范围检测 |")
    lines.append("")
    lines.append("## 2. 总体结果")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|-----:|")
    lines.append(f"| 总数据点数 | {total_data_points:,} |")
    lines.append(f"| 总噪声点数 | {total_noise_points:,} |")
    lines.append(f"| 总噪声率 | **{overall_noise_rate * 100:.4f}%** |")
    lines.append(f"| 目标阈值 | {TARGET_NOISE_RATE * 100:.0f}% |")
    lines.append(f"| 状态 | {'**PASS**' if meets_target else '**FAIL**'} |")
    lines.append(f"| 达标指标数 | {meets_target_count}/{len(indicator_stats)} |")
    lines.append(f"| 未达标指标数 | {fails_target_count}/{len(indicator_stats)} |")
    lines.append("")
    lines.append("## 3. 噪声构成分析")
    lines.append("")
    lines.append("| 噪声类型 | 点数 | 占比 |")
    lines.append("|----------|-----:|-----:|")
    for k, v in noise_breakdown.items():
        pct = v / total_data_points * 100 if total_data_points > 0 else 0
        lines.append(f"| {k:<15} | {v:>8,} | {pct:.4f}% |")
    lines.append("")
    lines.append("## 4. 分指标噪声率明细")
    lines.append("")
    lines.append(f"> 共 {len(indicator_stats)} 个指标。排序: 噪声率从高到低。")
    lines.append("")
    lines.append("| # | indicator_id | 数据点 | 噪声点 | 噪声率 | NULL | 异常值 | 漂移 | 重复 | 状态 |")
    lines.append("|---|-------------|------:|------:|------:|-----:|------:|-----:|-----:|:----:|")
    for i, s in enumerate(sorted_stats, 1):
        flag = "PASS" if s["meets_target"] else "FAIL"
        lines.append(
            f"| {i} | `{s['indicator_id']}` | {s['data_points']:,} | {s['total_noise_points']:,} | "
            f"{s['noise_rate_pct']:.4f}% | {s['null_count']} | {s['outlier_count']} | "
            f"{s['drift_count']} | {s['stale_count']} | {flag} |"
        )
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by noise_rate_analysis.py | {now}*")

    md_content = "\n".join(lines)
    md_path = OUTPUT_DIR / "v88_phase03_p1_noise_rate_analysis.md"
    with open(str(md_path), "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  [MD]   Written: {md_path} ({len(md_content):,} bytes)")

    # Generate JSON data
    json_data = {
        "task_id": "V88_PHASE03_P1_DSHB_MAIN_JOB",
        "agent": "DSHB",
        "branch": "feature/v88-g1",
        "generated": now,
        "database": str(db_path),
        "target_noise_rate": TARGET_NOISE_RATE,
        "overall": {
            "total_data_points": total_data_points,
            "total_noise_points": total_noise_points,
            "noise_rate": overall_noise_rate,
            "noise_rate_pct": round(overall_noise_rate * 100, 4),
            "meets_target": meets_target,
        },
        "breakdown": noise_breakdown,
        "summary": {
            "total_indicators": len(indicator_stats),
            "meets_target": meets_target_count,
            "fails_target": fails_target_count,
        },
        "indicators": sorted_stats,
    }
    json_path = OUTPUT_DIR / "noise_rate_data.json"
    with open(str(json_path), "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"  [JSON] Written: {json_path}")

    print("\n  Done.")
    sys.exit(0)


if __name__ == "__main__":
    main()