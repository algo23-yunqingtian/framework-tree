#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
derived_metric_probe.py — V88 Phase03 P1 DSHB 衍生品指标命中探针
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_FOLLOWUP_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  持续轮询59项衍生品指标命中计数，记录每日命中数量。
  监控34→59达标触发事件；当命中全部59项，触发P0-9分母自动切换(50→109)。
  记录切换审计日志。

  门禁关联: R-V88-033 (59项衍生品派生指标建库)
  验收方式: 探针式自动探测，命中达标后自动切至分母109

  判定逻辑:
    - 查询 phase03_test.db 中59项衍生品指标的命中情况
    - 统计命中数 / 目标数(59)
    - 命中全部59项 → 触发分母切换50→109
    - 输出每日命中计数时序日志

Usage:
  python derived_metric_probe.py [--db path/to/phase03_test.db] [--once] [--resume]

  --once    : 执行单次探测并退出
  --resume  : 从已有日志继续

Output:
  - derived_probe_log.jsonl   : 逐日命中计数时序
  - derived_probe_checkpoint.json : 探针状态检查点
"""

import os
import sys
import sqlite3
import platform
import argparse
import json
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

# Observation configuration
PROBE_INTERVAL_SEC = 3600  # 1 hour interval for probing
LOG_FILE = "derived_probe_log.jsonl"
CHECKPOINT_FILE = "derived_probe_checkpoint.json"
AUDIT_FILE = "derived_probe_switch_audit.jsonl"

# =============================================================================
# Derived Indicator Registry (59 items from P1)
# =============================================================================

DERIVED_INDICATORS = {
    "term_structure": [
        ("cu_term_structure", "CU_TERM_STRUCTURE"),
        ("al_term_structure", "AL_TERM_STRUCTURE"),
        ("zn_term_structure", "ZN_TERM_STRUCTURE"),
        ("ni_term_structure", "NI_TERM_STRUCTURE"),
        ("sn_term_structure", "SN_TERM_STRUCTURE"),
        ("si_term_structure", "SI_TERM_STRUCTURE"),
        ("li_term_structure", "LC_TERM_STRUCTURE"),
        ("pb_term_structure", "PB_TERM_STRUCTURE"),
    ],
    "month_spread": [
        ("cu_month_spread", "CU_MONTH_SPREAD"),
        ("al_month_spread", "AL_MONTH_SPREAD"),
        ("zn_month_spread", "ZN_MONTH_SPREAD"),
        ("ni_month_spread", "NI_MONTH_SPREAD"),
        ("sn_month_spread", "SN_MONTH_SPREAD"),
        ("si_month_spread", "SI_MONTH_SPREAD"),
        ("li_month_spread", "LC_MONTH_SPREAD"),
        ("pb_month_spread", "PB_MONTH_SPREAD"),
    ],
    "ls_ratio": [
        ("cu_long_short_ratio", "CU_LONG_SHORT_RATIO"),
        ("al_long_short_ratio", "AL_LONG_SHORT_RATIO"),
        ("zn_long_short_ratio", "ZN_LONG_SHORT_RATIO"),
        ("ni_long_short_ratio", "NI_LONG_SHORT_RATIO"),
        ("sn_long_short_ratio", "SN_LONG_SHORT_RATIO"),
        ("si_long_short_ratio", "SI_LONG_SHORT_RATIO"),
        ("li_long_short_ratio", "LC_LONG_SHORT_RATIO"),
        ("pb_long_short_ratio", "PB_LONG_SHORT_RATIO"),
    ],
    "price_percentile": [
        ("cu_price_percentile", "CU_PRICE_PERCENTILE"),
        ("al_price_percentile", "AL_PRICE_PERCENTILE"),
        ("zn_price_percentile", "ZN_PRICE_PERCENTILE"),
        ("ni_price_percentile", "NI_PRICE_PERCENTILE"),
        ("sn_price_percentile", "SN_PRICE_PERCENTILE"),
        ("si_price_percentile", "SI_PRICE_PERCENTILE"),
        ("li_price_percentile", "LC_PRICE_PERCENTILE"),
        ("pb_price_percentile", "PB_PRICE_PERCENTILE"),
    ],
    "top20_net": [
        ("cu_top20_net", "CU_TOP20_NET"),
        ("ni_top20_net", "NI_TOP20_NET"),
        ("sn_top20_net", "SN_TOP20_NET"),
        ("lc_top20_net", "LC_TOP20_NET"),
        ("si_top20_net", "SI_TOP20_NET"),
        ("pb_top20_net", "PB_TOP20_NET"),
    ],
    "inv_change": [
        ("cu_inv_change", "CU_INV_CHANGE"),
        ("al_inv_change", "AL_INV_CHANGE"),
        ("zn_inv_change", "ZN_INV_CHANGE"),
        ("ni_inv_change", "NI_INV_CHANGE"),
        ("li_inv_change", "LI_INV_CHANGE"),
    ],
    "comex_spread": [
        ("comex_cu_lme_spread", "COMEX_CU_LME_SPREAD"),
        ("comex_zn_lme_spread", "COMEX_ZN_LME_SPREAD"),
    ],
    "inv_days": [
        ("si_inventory_days", "SI_INV_DAYS"),
        ("sn_inventory_days", "SN_INV_DAYS"),
    ],
    "basis_change": [
        ("li_basis_change", "LC_BASIS_CHANGE"),
        ("zn_basis_change", "ZN_BASIS_CHANGE"),
        ("ni_basis_change", "NI_BASIS_CHANGE"),
    ],
    "oi_percentile": [
        ("li_oi_percentile", "LI_OI_PERCENTILE"),
        ("cu_oi_percentile", "CU_OI_PERCENTILE"),
        ("zn_oi_percentile", "ZN_OI_PERCENTILE"),
    ],
    "spot_change": [
        ("spot_is_change", "SPOT_IS_CHANGE"),
        ("spot_licar_change", "SPOT_LICAR_CHANGE"),
    ],
    "comex_change": [
        ("comex_cu_change", "COMEX_CU_CHANGE"),
        ("comex_zn_change", "COMEX_ZN_CHANGE"),
    ],
    "premium_change": [
        ("cu_premium_change", "CU_PREMIUM_CHANGE"),
        ("al_premium_change", "AL_PREMIUM_CHANGE"),
    ],
}

TOTAL_DERIVED = sum(len(v) for v in DERIVED_INDICATORS.values())
TARGET_HIT = TOTAL_DERIVED  # 59

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
# Probe Logic
# =============================================================================

def probe_derived_hits(conn):
    """Probe all 59 derived indicators for hit count."""
    cur = conn.cursor()

    results = {}
    for category, items in DERIVED_INDICATORS.items():
        category_results = []
        for derived_id, mapped_id in items:
            # Check if this derived indicator exists in the DB
            cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=? AND value IS NOT NULL", (derived_id,))
            row_count = cur.fetchone()[0]

            # Check if it's mapped (from series_cache)
            cur.execute("SELECT indicator_id_mapped FROM series_cache WHERE indicator_id=? AND indicator_id_mapped IS NOT NULL LIMIT 1", (derived_id,))
            meta_row = cur.fetchone()
            mapped_id_actual = meta_row[0] if meta_row else None

            category_results.append({
                "derived_id": derived_id,
                "mapped_id": mapped_id,
                "mapped_id_actual": mapped_id_actual,
                "row_count": row_count,
                "is_hit": row_count > 0,
                "is_mapped": mapped_id_actual is not None
            })
        results[category] = category_results

    # Compute totals
    total_hit = 0
    total_mapped = 0
    all_items = []
    for category, items in results.items():
        for item in items:
            all_items.append(item)
            if item["is_hit"]:
                total_hit += 1
            if item["is_mapped"]:
                total_mapped += 1

    hit_pct = round(total_hit / TOTAL_DERIVED * 100, 2) if TOTAL_DERIVED > 0 else 0.0

    # Check if all 59 hit → denominator switch
    all_hit = (total_hit >= TOTAL_DERIVED)
    denominator_mode = "FULL_109" if all_hit else "IN_SCOPE_50"

    # Build summary
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total_derived": TOTAL_DERIVED,
        "total_hit": total_hit,
        "total_mapped": total_mapped,
        "hit_pct": hit_pct,
        "all_hit": all_hit,
        "denominator_mode": denominator_mode,
        "p0_9_denominator": 109 if all_hit else 50,
        "by_category": {}
    }

    for category, items in results.items():
        cat_hit = sum(1 for i in items if i["is_hit"])
        cat_total = len(items)
        summary["by_category"][category] = {
            "hit": cat_hit,
            "total": cat_total,
            "hit_pct": round(cat_hit / cat_total * 100, 2) if cat_total > 0 else 0.0
        }

    summary["items"] = all_items

    return summary

# =============================================================================
# State Management
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
    """Append probe entry to JSONL log."""
    log_path = OUTPUT_DIR / LOG_FILE
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def append_audit(entry):
    """Append audit entry to audit log."""
    audit_path = OUTPUT_DIR / AUDIT_FILE
    with open(audit_path, "a", encoding="utf-8") as f:
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
# Main Probe
# =============================================================================

def probe_once(db_path, state):
    """Execute a single probe."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    print("[PROBE] Probing 59 derived indicators at %s..." % datetime.now().strftime("%H:%M:%S"))

    result = probe_derived_hits(conn)

    # Build log entry (compact)
    log_entry = {
        "timestamp": result["timestamp"],
        "probe_round": state["probe_round"],
        "total_derived": result["total_derived"],
        "total_hit": result["total_hit"],
        "hit_pct": result["hit_pct"],
        "denominator_mode": result["denominator_mode"],
        "p0_9_denominator": result["p0_9_denominator"],
        "all_hit": result["all_hit"]
    }

    append_log(log_entry)
    state["probe_round"] += 1
    state["last_probed_at"] = result["timestamp"]
    state["last_hit"] = result["total_hit"]
    state["last_hit_pct"] = result["hit_pct"]
    state["last_denominator_mode"] = result["denominator_mode"]
    save_checkpoint(state)

    print("[PROBE] Hit: %d/%d (%.2f%%) | Mode: %s | Denominator: %d" % (
        result["total_hit"], result["total_derived"],
        result["hit_pct"],
        result["denominator_mode"],
        result["p0_9_denominator"]
    ))

    # Check for denominator switch event
    prev_mode = state.get("prev_denominator_mode", "IN_SCOPE_50")
    curr_mode = result["denominator_mode"]

    if prev_mode != curr_mode:
        # Denominator switch detected
        audit_entry = {
            "timestamp": result["timestamp"],
            "event": "denominator_switch",
            "prev_mode": prev_mode,
            "curr_mode": curr_mode,
            "prev_denominator": 50 if prev_mode == "IN_SCOPE_50" else 109,
            "curr_denominator": 109 if curr_mode == "FULL_109" else 50,
            "total_hit": result["total_hit"],
            "total_derived": result["total_derived"],
            "hit_pct": result["hit_pct"],
            "probe_round": state["probe_round"],
            "note": "P0-9分母自动切换: %d→%d (衍生品命中%d/%d)" % (
                50 if prev_mode == "IN_SCOPE_50" else 109,
                109 if curr_mode == "FULL_109" else 50,
                result["total_hit"],
                result["total_derived"]
            )
        }
        append_audit(audit_entry)
        print("[AUDIT] ** DENOMINATOR SWITCH ** %s → %s (denominator: %d → %d)" % (
            prev_mode, curr_mode,
            50 if prev_mode == "IN_SCOPE_50" else 109,
            109 if curr_mode == "FULL_109" else 50
        ))

    state["prev_denominator_mode"] = curr_mode
    save_checkpoint(state)

    conn.close()
    return result


def main():
    setup_environment()

    parser = argparse.ArgumentParser(description="V88 Phase03 P1 DSHB derived metric probe monitor")
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT), help="Path to phase03_test.db")
    parser.add_argument("--once", action="store_true", help="Execute single probe and exit")
    parser.add_argument("--resume", action="store_true", help="Resume from existing checkpoint")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print("[ERROR] DB not found: %s" % db_path)
        print("[ERROR] Run rebuild_phase03_testdb.py first")
        sys.exit(1)

    # Load or create checkpoint
    if args.resume:
        state = load_checkpoint()
        if state:
            print("[RESUME] Loaded checkpoint: round=%d, hit=%d/%d" % (
                state["probe_round"], state.get("last_hit", 0), TOTAL_DERIVED))
        else:
            print("[RESUME] No existing checkpoint, starting fresh")
            state = None
    else:
        state = None

    if state is None:
        state = {
            "task_id": "V88_PHASE03_P1_DSHB_FOLLOWUP_JOB",
            "agent": "DSHB",
            "branch": "feature/v88-g1",
            "started_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "probe_round": 0,
            "total_derived": TOTAL_DERIVED,
            "target_hit": TOTAL_DERIVED,
            "prev_denominator_mode": "IN_SCOPE_50",
            "log_file": LOG_FILE,
            "checkpoint_file": CHECKPOINT_FILE,
            "audit_file": AUDIT_FILE
        }
        save_checkpoint(state)
        print("[START] New probe started at %s" % state["started_at"])

    if args.once:
        # Single probe mode
        result = probe_once(db_path, state)

        # Print detailed hit breakdown
        print("\n[DETAIL] Per-category hit breakdown:")
        for cat, data in sorted(result["by_category"].items()):
            print("  %-20s %d/%d (%.2f%%)" % (cat, data["hit"], data["total"], data["hit_pct"]))

        print("\n[DETAIL] Per-indicator detail:")
        for item in result["items"]:
            hit_mark = "[HIT]" if item["is_hit"] else "[---]"
            print("  %s %-30s rows=%-6d mapped=%s" % (
                hit_mark, item["derived_id"], item["row_count"],
                item["mapped_id_actual"] if item["mapped_id_actual"] else "N/A"
            ))

        if result["all_hit"]:
            print("\n[TRIGGER] All %d derived indicators hit! P0-9 denominator switched to 109." % TOTAL_DERIVED)
        else:
            print("\n[STATUS] %d/%d hit (%.2f%%). Pending: %d indicators. Denominator: %d" % (
                result["total_hit"], TOTAL_DERIVED, result["hit_pct"],
                TOTAL_DERIVED - result["total_hit"],
                result["p0_9_denominator"]
            ))

        return

    # Daemon mode: continuous probe loop
    print("[DAEMON] Starting derived metric probe monitor...")
    print("[DAEMON] Interval: %d seconds | Target: %d/%d hit" % (
        PROBE_INTERVAL_SEC, TOTAL_DERIVED, TOTAL_DERIVED))
    print("[DAEMON] Press Ctrl+C to stop")
    print()

    try:
        while True:
            result = probe_once(db_path, state)

            # Check if all hit
            if result["all_hit"]:
                print("\n[DAEMON] All %d derived indicators hit! P0-9 denominator switched to 109." % TOTAL_DERIVED)
                print("[DAEMON] Switch audit logged. Monitor continues for confirmation.")

            # Sleep until next probe
            print("[DAEMON] Sleeping %d seconds..." % PROBE_INTERVAL_SEC)
            time.sleep(PROBE_INTERVAL_SEC)
    except KeyboardInterrupt:
        print()
        print("[DAEMON] Stopped by user. Progress saved to %s" % CHECKPOINT_FILE)
        print("[DAEMON] Resume with: python derived_metric_probe.py --resume")
        sys.exit(0)


if __name__ == "__main__":
    main()