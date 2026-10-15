#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
noise_7d_observation.py — V88 Phase03 P1 DSHB 7天噪声率静默观测脚本
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_FOLLOWUP_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  启动7x24h静默采集，每小时计算噪声率时序，满7天后生成总结报告。
  禁止提前判定结果。

  噪声率 = 异常数据点数 / 总数据点数
  目标: < 10%

  异常数据点定义 (同P1 noise_rate_analysis.py):
    1. NULL 值
    2. 3-sigma 异常值
    3. 时间漂移点 (>90天无更新)
    4. 单位异常点
    5. 重复值点 (连续3个以上相同值)

  门禁关联: P0-13 (告警噪声率门禁, <10%, 7天静默期)
  验收方式: 满7天后输出 v88_phase03_p1_noise_7d_summary.md

Usage:
  python noise_7d_observation.py [--db path/to/phase03_test.db] [--once] [--resume]

  --once    : 执行单次观测并退出 (不启动守护循环)
  --resume  : 从已有日志继续 (不重置观测计数器)

Output:
  - noise_7d_log.jsonl     : 每小时噪声率时序日志 (JSON Lines)
  - noise_7d_checkpoint.json : 观测状态检查点 (含累计天数)
"""

import os
import sys
import sqlite3
import platform
import argparse
import json
import math
from pathlib import Path
from datetime import datetime, timedelta
import time

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
FOLLOWUP_DIR = SCRIPT_DIR
DHB_DIR = FOLLOWUP_DIR.parent
P1_DIR = DHB_DIR.parent
PHASE03_DIR = P1_DIR.parent
DB_PATH_DEFAULT = PHASE03_DIR / "p0" / "phase03_test.db"
OUTPUT_DIR = FOLLOWUP_DIR

# Noise thresholds (same as P1 noise_rate_analysis.py)
SIGMA_THRESHOLD = 3.0
TIME_DRIFT_DAYS = 90
STALE_CONSECUTIVE = 3
TARGET_NOISE_RATE = 0.10

# Observation configuration
OBSERVATION_HOURS = 168       # 7 days * 24 hours
OBSERVATION_INTERVAL_SEC = 3600  # 1 hour interval
LOG_FILE = "noise_7d_log.jsonl"
CHECKPOINT_FILE = "noise_7d_checkpoint.json"
SUMMARY_FILE = "v88_phase03_p1_noise_7d_summary.md"

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
# Noise Detection Functions (inherited from P1 noise_rate_analysis.py)
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
    """Detect 3-sigma outliers for an indicator (Python approach, same as P1 noise_rate_analysis.py)."""
    cur = conn.cursor()
    cur.execute("SELECT date, value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date", (indicator_id,))
    rows = cur.fetchall()
    if len(rows) < 30:
        return 0
    values = [r[1] for r in rows]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5
    if std == 0:
        return 0
    outlier_count = sum(1 for v in values if abs(v - mean) > SIGMA_THRESHOLD * std)
    return outlier_count


def detect_time_drift(conn, indicator_id):
    """Detect time drift (gaps > 90 days). Returns count of gaps (not points)."""
    cur = conn.cursor()
    cur.execute("SELECT date FROM series_cache WHERE indicator_id=? ORDER BY date", (indicator_id,))
    dates = [r[0] for r in cur.fetchall()]
    if len(dates) < 2:
        return 0
    drift_count = 0
    for i in range(1, len(dates)):
        try:
            d1 = datetime.strptime(dates[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(dates[i], "%Y-%m-%d")
            if (d2 - d1).days > TIME_DRIFT_DAYS:
                drift_count += 1
        except:
            pass
    return drift_count


def detect_unit_anomalies(conn, indicator_id):
    """Detect unit anomalies (constant series, extreme ranges). Returns indicator-level flag (0 or 1)."""
    cur = conn.cursor()
    cur.execute("SELECT MIN(value), MAX(value), AVG(value) FROM series_cache WHERE indicator_id=? AND value IS NOT NULL", (indicator_id,))
    row = cur.fetchone()
    if row[0] is None:
        return 0
    min_v, max_v, avg_v = row
    count = 0
    if min_v == max_v:
        count += 1
    if avg_v != 0 and abs(max_v / avg_v) > 1000:
        count += 1
    return count


def detect_stale_points(conn, indicator_id):
    """Detect stale points (consecutive same-value points). Returns count of individual stale points."""
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


def compute_noise_rate(conn, indicator_id):
    """Compute noise rate for a single indicator (same approach as P1 noise_rate_analysis.py).
    
    total_noise = null_count + outlier_count + stale_count
    drift and unit_anomaly are reported separately but NOT added to total_noise.
    """
    total = 0
    noise = 0

    null_count, total_count = detect_nulls(conn, indicator_id)
    noise += null_count
    total += total_count

    outlier_count = detect_outliers(conn, indicator_id)
    noise += outlier_count

    stale_count = detect_stale_points(conn, indicator_id)
    noise += stale_count

    if total == 0:
        return 0.0, 0, 0

    rate = noise / total
    return rate, noise, total


def compute_global_noise_rate(conn):
    """Compute global noise rate across all indicators (same approach as P1 noise_rate_analysis.py)."""
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT indicator_id FROM series_cache ORDER BY indicator_id")
    indicators = [row[0] for row in cur.fetchall()]

    total_points = 0
    total_noise = 0
    noise_breakdown = {"null": 0, "outlier": 0, "drift": 0, "stale": 0, "unit_anomaly": 0}
    indicator_rates = []

    for ind in indicators:
        cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=?", (ind,))
        data_points = cur.fetchone()[0]
        if data_points == 0:
            continue

        total_points += data_points

        null_count, _ = detect_nulls(conn, ind)
        outlier_count = detect_outliers(conn, ind)
        drift_count = detect_time_drift(conn, ind)
        stale_count = detect_stale_points(conn, ind)
        unit_count = detect_unit_anomalies(conn, ind)

        # Only null + outlier + stale count toward noise rate
        noise = null_count + outlier_count + stale_count
        rate = noise / data_points if data_points > 0 else 0.0

        noise_breakdown["null"] += null_count
        noise_breakdown["outlier"] += outlier_count
        noise_breakdown["drift"] += drift_count
        noise_breakdown["stale"] += stale_count
        noise_breakdown["unit_anomaly"] += unit_count

        indicator_rates.append({
            "indicator_id": ind,
            "noise_rate": round(rate, 6),
            "noise_count": noise,
            "total_count": data_points
        })

        total_noise += noise

    global_rate = total_noise / total_points if total_points > 0 else 0.0
    return {
        "global_noise_rate": round(global_rate, 6),
        "total_points": total_points,
        "total_noise": total_noise,
        "indicator_count": len(indicators),
        "indicators_at_target": sum(1 for r in indicator_rates if r["noise_rate"] < TARGET_NOISE_RATE),
        "noise_breakdown": noise_breakdown,
        "indicator_rates": indicator_rates
    }

# =============================================================================
# Observation State Management
# =============================================================================

def load_checkpoint():
    """Load checkpoint from disk."""
    checkpoint_path = OUTPUT_DIR / CHECKPOINT_FILE
    if checkpoint_path.exists():
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_checkpoint(state):
    """Save checkpoint to disk."""
    checkpoint_path = OUTPUT_DIR / CHECKPOINT_FILE
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def append_log(entry):
    """Append observation entry to JSONL log."""
    log_path = OUTPUT_DIR / LOG_FILE
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_log():
    """Load all entries from JSONL log."""
    log_path = OUTPUT_DIR / LOG_FILE
    entries = []
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries

# =============================================================================
# Summary Generation
# =============================================================================

def generate_summary(all_entries):
    """Generate 7-day observation summary markdown."""
    if not all_entries:
        return "# V88 Phase03 P1 — 7天噪声率静默观测总结\n\n> 无观测数据"

    total_obs = len(all_entries)
    obs_hours = total_obs
    obs_days = obs_hours / 24.0
    is_complete = obs_hours >= OBSERVATION_HOURS

    rates = [e["global_noise_rate"] for e in all_entries]
    avg_rate = sum(rates) / len(rates) if rates else 0.0
    min_rate = min(rates) if rates else 0.0
    max_rate = max(rates) if rates else 0.0

    # Noise breakdown by type
    total_points_sum = sum(e.get("total_points", 0) for e in all_entries)
    total_noise_sum = sum(e.get("total_noise", 0) for e in all_entries)
    overall_rate = total_noise_sum / total_points_sum if total_points_sum > 0 else 0.0

    # Hourly time series data
    time_series = []
    for e in all_entries:
        time_series.append({
            "timestamp": e["timestamp"],
            "noise_rate": e["global_noise_rate"],
            "hour_index": e["observation_hour"]
        })

    lines = []
    lines.append("# V88 Phase03 P1 — 7天噪声率静默观测总结")
    lines.append("")
    lines.append("> **TASK_ID**: V88_PHASE03_P1_DSHB_FOLLOWUP_JOB")
    lines.append("> **AGENT**: DSHB | **BRANCH**: feature/v88-g1")
    lines.append("> **生成时间**: %s" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    lines.append("> **观测窗口**: %d 小时 (%.2f 天)" % (obs_hours, obs_days))
    lines.append("> **观测完成**: %s" % ("是" if is_complete else "否 (%d/%d 小时)" % (obs_hours, OBSERVATION_HOURS)))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. 观测概述")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|-----:|")
    lines.append("| 观测次数 | %d |" % total_obs)
    lines.append("| 观测小时数 | %d |" % obs_hours)
    lines.append("| 观测天数 | %.2f |" % obs_days)
    lines.append("| 是否满7天 | %s |" % ("是" if is_complete else "否"))
    lines.append("")
    lines.append("## 2. 噪声率统计")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|-----:|")
    lines.append("| 平均噪声率 | %.4f%% |" % (avg_rate * 100))
    lines.append("| 最低噪声率 | %.4f%% |" % (min_rate * 100))
    lines.append("| 最高噪声率 | %.4f%% |" % (max_rate * 100))
    lines.append("| 总数据点 | %d |" % total_points_sum)
    lines.append("| 总噪声点 | %d |" % total_noise_sum)
    lines.append("| 整体噪声率 | %.4f%% |" % (overall_rate * 100))
    lines.append("| 目标阈值 | <10%% |")
    lines.append("| 状态 | %s |" % ("PASS" if overall_rate < TARGET_NOISE_RATE else "FAIL"))
    lines.append("")
    lines.append("## 3. 逐次观测时序")
    lines.append("")
    lines.append("| # | 时间戳 | 噪声率 | 数据点 | 噪声点 |")
    lines.append("|:-:|--------|-------:|------:|------:|")
    for i, e in enumerate(all_entries):
        lines.append("| %d | %s | %.4f%% | %d | %d |" % (
            i + 1,
            e["timestamp"],
            e["global_noise_rate"] * 100,
            e.get("total_points", 0),
            e.get("total_noise", 0)
        ))
    lines.append("")
    lines.append("## 4. 门禁判定 (P0-13)")
    lines.append("")
    if is_complete:
        if overall_rate < TARGET_NOISE_RATE:
            lines.append("> **P0-13 状态**: **PASS** — 7天静默期噪声率 %.4f%% < 10%% 阈值" % (overall_rate * 100))
        else:
            lines.append("> **P0-13 状态**: **FAIL** — 7天静默期噪声率 %.4f%% >= 10%% 阈值" % (overall_rate * 100))
    else:
        lines.append("> **P0-13 状态**: **WARN** — 观测不足7天 (%d/%d小时), 噪声率暂不作准" % (obs_hours, OBSERVATION_HOURS))
        lines.append("> 当前累积噪声率: %.4f%%" % (overall_rate * 100))
    lines.append("")
    lines.append("## 5. 观测日志文件")
    lines.append("")
    lines.append("- `noise_7d_log.jsonl`: 逐小时观测时序 (%d 条记录)" % total_obs)
    lines.append("- `noise_7d_checkpoint.json`: 观测状态检查点")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by noise_7d_observation.py | %s*" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    return "\n".join(lines)

# =============================================================================
# Main Observation Loop
# =============================================================================

def observe_once(db_path, state):
    """Execute a single noise observation."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    print("[OBSERVE] Computing noise rate at %s..." % datetime.now().strftime("%H:%M:%S"))

    result = compute_global_noise_rate(conn)

    # Build observation entry
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "observation_hour": state["observation_hour"],
        "global_noise_rate": result["global_noise_rate"],
        "total_points": result["total_points"],
        "total_noise": result["total_noise"],
        "indicator_count": result["indicator_count"],
        "indicators_at_target": result["indicators_at_target"],
        "target_rate": TARGET_NOISE_RATE
    }

    append_log(entry)
    state["observation_hour"] += 1
    state["last_observed_at"] = entry["timestamp"]
    save_checkpoint(state)

    print("[OBSERVE] Noise rate: %.4f%% | Points: %d | Noise: %d | Hour: %d/%d" % (
        result["global_noise_rate"] * 100,
        result["total_points"],
        result["total_noise"],
        state["observation_hour"],
        OBSERVATION_HOURS
    ))

    conn.close()

    # Check if observation complete
    if state["observation_hour"] >= OBSERVATION_HOURS:
        print("[OBSERVE] 7-day observation complete!")
        generate_summary(load_log())
        summary_path = OUTPUT_DIR / SUMMARY_FILE
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(generate_summary(load_log()))
        print("[OBSERVE] Summary written to %s" % summary_path)
        state["observation_complete"] = True
        save_checkpoint(state)
        return True

    return False


def main():
    setup_environment()

    parser = argparse.ArgumentParser(description="V88 Phase03 P1 DSHB 7-day noise observation")
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT), help="Path to phase03_test.db")
    parser.add_argument("--once", action="store_true", help="Execute single observation and exit")
    parser.add_argument("--resume", action="store_true", help="Resume from existing checkpoint")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print("[ERROR] DB not found: %s" % db_path)
        print("[ERROR] Run rebuild_phase03_testdb.py first")
        sys.exit(1)

    # Load or create checkpoint
    state = None
    if args.resume:
        state = load_checkpoint()
        if state:
            print("[RESUME] Loaded checkpoint: hour=%d, complete=%s" % (
                state["observation_hour"], state.get("observation_complete", False)))
            if state.get("observation_complete", False):
                print("[RESUME] Observation already complete. Generating summary...")
                summary = generate_summary(load_log())
                summary_path = OUTPUT_DIR / SUMMARY_FILE
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary)
                print("[RESUME] Summary written to %s" % summary_path)
                return
        else:
            print("[RESUME] No existing checkpoint, starting fresh")
            state = None

    if state is None:
        state = {
            "task_id": "V88_PHASE03_P1_DSHB_FOLLOWUP_JOB",
            "agent": "DSHB",
            "branch": "feature/v88-g1",
            "started_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "observation_hour": 0,
            "observation_complete": False,
            "target_noise_rate": TARGET_NOISE_RATE,
            "observation_hours_required": OBSERVATION_HOURS,
            "log_file": LOG_FILE,
            "checkpoint_file": CHECKPOINT_FILE
        }
        save_checkpoint(state)
        print("[START] New observation started at %s" % state["started_at"])

    if args.once:
        # Single observation mode
        observe_once(db_path, state)
        return

    # Daemon mode: continuous observation loop
    print("[DAEMON] Starting 7x24h noise observation...")
    print("[DAEMON] Interval: %d seconds | Duration: %d hours" % (
        OBSERVATION_INTERVAL_SEC, OBSERVATION_HOURS))
    print("[DAEMON] Press Ctrl+C to stop")
    print()

    try:
        while not state.get("observation_complete", False):
            complete = observe_once(db_path, state)
            if complete:
                print("[DAEMON] Observation complete!")
                break
            # Sleep until next observation
            if state["observation_hour"] < OBSERVATION_HOURS:
                print("[DAEMON] Sleeping %d seconds until next observation..." % OBSERVATION_INTERVAL_SEC)
                time.sleep(OBSERVATION_INTERVAL_SEC)
    except KeyboardInterrupt:
        print()
        print("[DAEMON] Stopped by user. Progress saved to %s" % CHECKPOINT_FILE)
        print("[DAEMON] Resume with: python noise_7d_observation.py --resume")
        sys.exit(0)


if __name__ == "__main__":
    main()