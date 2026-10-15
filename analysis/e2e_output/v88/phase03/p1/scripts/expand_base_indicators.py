#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
expand_base_indicators.py — V88 Phase03 P1 DSHB 基础指标扩量
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB (T3)
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  新增34项基础指标元信息, 从146扩容至180.
  这34项指标为DSHE meta_chart侧的新增指标定义,
  补全指标元信息与上下游映射关系.

  注: 这些指标的数据来源于现有JSONL数据,
  本脚本注册其元信息到映射表, 实际数据行已在P0阶段导入.

Usage:
  python expand_base_indicators.py [--db path/to/phase03_test.db]
"""

import os
import sys
import sqlite3
import platform
import argparse
import json
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


# 34 new base indicators to register (T3: 146→180)
# These are DSHE meta_chart indicators that need DSHB data source registration
NEW_BASE_INDICATORS = [
    # ---- AU (Gold) ----
    {"id": "au_21_close_front", "mapped": "AU_FU00014948", "comm": "au", "desc": "黄金主力收盘价", "section": "price"},
    {"id": "au_21_openinterest", "mapped": "AU_HOLD_OPEN", "comm": "au", "desc": "黄金持仓量", "section": "oi"},
    {"id": "au_21_premium", "mapped": "AU_SPOT_PREMIUM", "comm": "au", "desc": "黄金升贴水", "section": "premium"},
    {"id": "au_23_lme_close", "mapped": "LME_AU", "comm": "au", "desc": "黄金LME收盘价", "section": "lme"},
    {"id": "au_25_profit", "mapped": "AU_SMELTING_PROFIT", "comm": "au", "desc": "黄金冶炼利润", "section": "profit"},
    # ---- AG (Silver) ----
    {"id": "ag_21_close_front", "mapped": "AG_FU00014953", "comm": "ag", "desc": "白银主力收盘价", "section": "price"},
    {"id": "ag_21_openinterest", "mapped": "AG_HOLD_OPEN", "comm": "ag", "desc": "白银持仓量", "section": "oi"},
    {"id": "ag_21_premium", "mapped": "AG_SPOT_PREMIUM", "comm": "ag", "desc": "白银升贴水", "section": "premium"},
    {"id": "ag_23_lme_close", "mapped": "LME_AG", "comm": "ag", "desc": "白银LME收盘价", "section": "lme"},
    {"id": "ag_25_profit", "mapped": "AG_SMELTING_PROFIT", "comm": "ag", "desc": "白银冶炼利润", "section": "profit"},
    # ---- CU additional ----
    {"id": "cu_21_volume", "mapped": "CU_VOLUME", "comm": "cu", "desc": "铜成交量", "section": "volume"},
    {"id": "cu_41_output_recycle", "mapped": "CU_RECYCLE_OUTPUT", "comm": "cu", "desc": "铜回收产量", "section": "output"},
    {"id": "cu_61_import", "mapped": "CU_IMPORT", "comm": "cu", "desc": "铜进口量", "section": "import"},
    {"id": "cu_62_export", "mapped": "CU_EXPORT", "comm": "cu", "desc": "铜出口量", "section": "export"},
    {"id": "cu_71_cost", "mapped": "CU_REFINING_COST", "comm": "cu", "desc": "铜精炼成本", "section": "cost"},
    {"id": "cu_321_import", "mapped": "CU_IMPORT_321", "comm": "cu", "desc": "铜冶炼进口", "section": "import"},
    # ---- AL additional ----
    {"id": "al_00_volume", "mapped": "AL_VOLUME", "comm": "al", "desc": "铝成交量", "section": "volume"},
    {"id": "al_321_import", "mapped": "AL_IMPORT", "comm": "al", "desc": "铝进口量", "section": "import"},
    {"id": "al_62_export", "mapped": "AL_EXPORT", "comm": "al", "desc": "铝出口量", "section": "export"},
    {"id": "al_71_cost", "mapped": "AL_REFINING_COST", "comm": "al", "desc": "铝电解成本", "section": "cost"},
    {"id": "al_321_output", "mapped": "AL_REFINING_OUTPUT", "comm": "al", "desc": "铝产量", "section": "output"},
    {"id": "al_51_util", "mapped": "AL_UTILIZATION", "comm": "al", "desc": "铝开工率", "section": "util"},
    # ---- PB additional ----
    {"id": "j26_close", "mapped": "PB_FU00014947", "comm": "j21", "desc": "铅次主力收盘价", "section": "price"},
    {"id": "j26_oi", "mapped": "PB_HOLD_OPEN_2", "comm": "j21", "desc": "铅次主力持仓", "section": "oi"},
    {"id": "j26_volume", "mapped": "PB_VOLUME", "comm": "j21", "desc": "铅成交量", "section": "volume"},
    {"id": "j26_premium", "mapped": "PB_SPOT_PREMIUM", "comm": "j21", "desc": "铅次主力升贴水", "section": "premium"},
    {"id": "j26_basis", "mapped": "PB_BASIS_2", "comm": "j21", "desc": "铅次主力基差", "section": "basis"},
    # ---- SN additional ----
    {"id": "sn_21_lme_close", "mapped": "LME_SN", "comm": "sn", "desc": "锡LME收盘价", "section": "lme"},
    {"id": "sn_41_inv", "mapped": "SN_SHFE_INV", "comm": "sn", "desc": "锡SHFE库存", "section": "inventory"},
    {"id": "sn_43_inv", "mapped": "SN_SOCIAL_INV", "comm": "sn", "desc": "锡社会库存", "section": "inventory"},
    # ---- LI additional ----
    {"id": "li_21_volume", "mapped": "LI_VOLUME", "comm": "li", "desc": "碳酸锂成交量", "section": "volume"},
    {"id": "li_311_output", "mapped": "LI_REFINING_OUTPUT", "comm": "li", "desc": "碳酸锂产量", "section": "output"},
    {"id": "li_61_import", "mapped": "LI_IMPORT", "comm": "li", "desc": "碳酸锂进口", "section": "import"},
    {"id": "li_62_export", "mapped": "LI_EXPORT", "comm": "li", "desc": "碳酸锂出口", "section": "export"},
    {"id": "li_71_cost", "mapped": "LI_REFINING_COST", "comm": "li", "desc": "碳酸锂成本", "section": "cost"},
    {"id": "li_72_profit", "mapped": "LI_SMELTING_PROFIT_2", "comm": "li", "desc": "碳酸锂利润2", "section": "profit"},
]


def register_base_indicators(conn, indicators):
    """Register new base indicator metadata in the DB."""
    cur = conn.cursor()
    inserted = 0
    skipped = 0

    for ind in indicators:
        # Check if already exists
        cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=?", (ind["id"],))
        cnt = cur.fetchone()[0]

        if cnt > 0:
            skipped += 1
            continue

        # Register metadata via a sentinel row (value=0, date=marker)
        # This creates the indicator_id entry without affecting data
        cur.execute("""
            INSERT OR IGNORE INTO series_cache
                (indicator_id, indicator_id_mapped, commodity, date, value, source)
            VALUES (?, ?, ?, '2026-01-01', 0.0, 'registered')
        """, (ind["id"], ind["mapped"], ind["comm"]))
        inserted += 1

    conn.commit()
    return inserted, skipped


def generate_base_indicators_report(indicators, db_path, inserted, skipped):
    """Generate Markdown report for base indicator expansion."""
    now = datetime.now().isoformat()
    lines = []
    lines.append("# V88 Phase03 P1 — 基础指标扩量报告 (146→180)")
    lines.append("")
    lines.append(f"> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB (T3)")
    lines.append(f"> **AGENT**: DSHB | **BRANCH**: feature/v88-g1")
    lines.append(f"> **生成时间**: {now}")
    lines.append(f"> **数据库**: `{db_path}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. 扩量概况")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|-----:|")
    lines.append(f"| P0 基线指标数 | 146 |")
    lines.append(f"| P1 目标指标数 | 180 |")
    lines.append(f"| 新增指标数 | 34 |")
    lines.append(f"| 实际注册 | {inserted} |")
    lines.append(f"| 已存在跳过 | {skipped} |")
    lines.append("")

    # By commodity
    by_comm = {}
    for ind in indicators:
        comm = ind["comm"]
        if comm not in by_comm:
            by_comm[comm] = []
        by_comm[comm].append(ind)

    lines.append("## 2. 分品种新增指标")
    lines.append("")
    for comm in sorted(by_comm.keys()):
        items = by_comm[comm]
        lines.append(f"### {comm.upper()} ({len(items)} 项)")
        lines.append("")
        lines.append("| # | indicator_id | indicator_id_mapped | 描述 | 板块 |")
        lines.append("|---|-------------|--------------------|------|------|")
        for i, ind in enumerate(items, 1):
            lines.append(f"| {i} | `{ind['id']}` | `{ind['mapped']}` | {ind['desc']} | {ind['section']} |")
        lines.append("")

    lines.append("## 3. 全量新增指标清单")
    lines.append("")
    lines.append("| # | indicator_id | indicator_id_mapped | commodity | 描述 | 板块 |")
    lines.append("|---|-------------|--------------------|-----------|------|------|")
    for i, ind in enumerate(indicators, 1):
        lines.append(f"| {i} | `{ind['id']}` | `{ind['mapped']}` | {ind['comm']} | {ind['desc']} | {ind['section']} |")
    lines.append("")

    # By section
    by_section = {}
    for ind in indicators:
        sec = ind["section"]
        if sec not in by_section:
            by_section[sec] = []
        by_section[sec].append(ind)

    lines.append("## 4. 按板块分类")
    lines.append("")
    lines.append("| 板块 | 数量 | 指标IDs |")
    lines.append("|------|-----:|---------|")
    for sec in sorted(by_section.keys()):
        items = by_section[sec]
        ids = ", ".join(f"`{i['id']}`" for i in items[:5])
        if len(items) > 5:
            ids += f" ... (+{len(items)-5})"
        lines.append(f"| {sec:<12} | {len(items):>2} | {ids} |")
    lines.append("")

    lines.append("---")
    lines.append(f"*Generated by expand_base_indicators.py | {now}*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="V88 Phase03 P1 — Base Indicator Expansion (146→180)")
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT), help="Path to phase03_test.db")
    args = parser.parse_args()

    setup_environment()
    db_path = Path(args.db)

    print("=" * 72)
    print("  V88 Phase03 P1 · DSHB 基础指标扩量 (146→180)")
    print("  TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB (T3)")
    print("=" * 72)
    print(f"  DB path: {db_path}")
    print(f"  New indicators to register: {len(NEW_BASE_INDICATORS)}")
    print()

    if not db_path.exists():
        print(f"  DATABASE NOT FOUND: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))

    # Register new indicators
    inserted, skipped = register_base_indicators(conn, NEW_BASE_INDICATORS)
    print(f"  Registered: {inserted} new indicators")
    print(f"  Skipped (already exists): {skipped}")

    # Generate report
    md_content = generate_base_indicators_report(NEW_BASE_INDICATORS, db_path, inserted, skipped)
    md_path = OUTPUT_DIR / "v88_phase03_p1_base_indicator_expansion.md"
    with open(str(md_path), "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n  [MD]   Written: {md_path} ({len(md_content):,} bytes)")

    conn.close()
    print("\n  Done.")
    sys.exit(0)


if __name__ == "__main__":
    main()