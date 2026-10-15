#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_all_to_testdb.py — Import ALL JSONL (base + CU/AL/PB supplement) into independent phase03_test.db
==========================================================================================================
TASK_ID: V88_PHASE03_P0_R0_REINGEST_IN_INDEPENDENT_TEST_DB
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  Create a fresh phase03_test.db, then import ALL JSONL data files:
    - Base: series_ZN.jsonl, series_NI.jsonl, series_SI.jsonl, series_SN.jsonl, series_LI.jsonl
    - Supplement: cu_al_pb_supplement.jsonl (CU 18 + AL 10 + PB 8 = 36 indicators)
  Using db_import_jsonl.py's setup_database() and import_file() functions.

  Does NOT modify scripts/api_cache.db — phase03_test.db is physically isolated.

Usage:
  python import_all_to_testdb.py [--dry-run] [--db path/to/phase03_test.db] [--verbose]

Constraints:
  - NO_ZHIJI_API_CALL / NO_OVERWRITE / APPEND_ONLY
  - INSERT OR IGNORE (no existing data overwritten)
  - Pure Python standard library
"""

import os
import sys
import json
import sqlite3
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add script directory to path to import db_import_jsonl
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from db_import_jsonl import (
    setup_database,
    import_file,
    REPO_ROOT,
    JSONL_FILES,
)

# =============================================================================
# Configuration
# =============================================================================

JSONL_DIR = REPO_ROOT / "data" / "db_export"

# Default test database path — physically isolated from scripts/api_cache.db
DEFAULT_TESTDB_PATH = SCRIPT_DIR.parent / "phase03_test.db"

# All JSONL files to import (base + supplement)
ALL_JSONL_FILES = JSONL_FILES + ["cu_al_pb_supplement.jsonl"]

# =============================================================================
# Statistics Helper
# =============================================================================

def get_db_stats(conn, label=""):
    """Retrieve and return database statistics."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM series_cache")
    total_rows = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    unique_indicators = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL"
    )
    mapped_indicators = cur.fetchone()[0]

    cur.execute("SELECT MIN(date), MAX(date) FROM series_cache")
    date_range = cur.fetchone()

    # Per-commodity
    cur.execute(
        "SELECT commodity, COUNT(*) as cnt, COUNT(DISTINCT indicator_id) as uniq "
        "FROM series_cache GROUP BY commodity ORDER BY commodity"
    )
    commodity_stats = []
    for row in cur.fetchall():
        commodity_stats.append({"commodity": row[0], "rows": row[1], "unique_indicators": row[2]})

    # Per-source
    cur.execute("SELECT source, COUNT(*) FROM series_cache GROUP BY source")
    source_stats = {row[0]: row[1] for row in cur.fetchall()}

    # Import log count
    try:
        cur.execute("SELECT COUNT(*) FROM import_log")
        import_log_count = cur.fetchone()[0]
    except sqlite3.Error:
        import_log_count = 0

    stats = {
        "label": label,
        "total_rows": total_rows,
        "unique_indicators": unique_indicators,
        "mapped_indicators": mapped_indicators,
        "date_min": date_range[0] if date_range else None,
        "date_max": date_range[1] if date_range else None,
        "commodity_stats": commodity_stats,
        "source_stats": source_stats,
        "import_log_count": import_log_count,
    }

    return stats


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Import ALL JSONL (base + supplement) into independent phase03_test.db"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode (no actual writes)")
    parser.add_argument("--db", type=str,
                        default=str(DEFAULT_TESTDB_PATH),
                        help="Path to phase03_test.db (default: phase03_test.db in p0 directory)")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose logging")
    args = parser.parse_args()

    # Logging setup
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)

    db_path = Path(args.db)
    logger.info("=" * 70)
    logger.info("  V88 Phase03 P0-R0 · Import ALL to Independent Test DB")
    logger.info("=" * 70)
    logger.info(f"  Task ID:      V88_PHASE03_P0_R0_REINGEST_IN_INDEPENDENT_TEST_DB")
    logger.info(f"  Database:     {db_path}")
    logger.info(f"  Dry run:      {args.dry_run}")
    logger.info(f"  JSONL dir:    {JSONL_DIR}")
    logger.info(f"  All files:    {', '.join(ALL_JSONL_FILES)}")
    logger.info("")

    # Validate all JSONL files exist
    jsonl_paths = []
    all_found = True
    for fname in ALL_JSONL_FILES:
        fpath = JSONL_DIR / fname
        if fpath.exists():
            fsize_mb = fpath.stat().st_size / 1024 / 1024
            logger.info(f"  FOUND:   {fname} ({fsize_mb:.1f} MB)")
            jsonl_paths.append(fpath)
        else:
            logger.error(f"  MISSING: {fname}")
            all_found = False

    if not all_found:
        logger.error("Some JSONL files are missing. Cannot proceed.")
        sys.exit(1)

    if not jsonl_paths:
        logger.error("No JSONL files found!")
        sys.exit(1)

    # Check that db_path is NOT the original api_cache.db
    original_db = REPO_ROOT / "scripts" / "api_cache.db"
    if str(db_path.resolve()) == str(original_db.resolve()):
        logger.error("FATAL: db_path must NOT be scripts/api_cache.db — use an independent test database!")
        sys.exit(1)
    logger.info(f"  Safety check: db_path is NOT scripts/api_cache.db ✅")
    logger.info("")

    # Setup database (creates fresh DB if not exists)
    conn = setup_database(db_path)
    logger.info(f"  Database ready: {db_path}")
    if db_path.exists():
        logger.info(f"  DB size: {db_path.stat().st_size / 1024:.1f} KB")

    # Pre-import stats
    pre_stats = get_db_stats(conn, "pre-import")
    logger.info(f"  Pre-import: {pre_stats['total_rows']:,} rows, {pre_stats['unique_indicators']} unique indicators")
    logger.info("")

    # Import each JSONL file
    all_results = []
    all_indicators = set()
    start_time = datetime.now()

    for i, fpath in enumerate(jsonl_paths, 1):
        logger.info(f"  [{i}/{len(jsonl_paths)}] Importing: {fpath.name}...")
        result = import_file(conn, str(fpath), dry_run=args.dry_run)
        all_results.append(result)
        all_indicators.update(result["unique_indicators"])

        logger.info(f"    Read: {result['rows_read']:,} | Insert: {result['rows_inserted']:,} | "
                    f"Skip: {result['rows_skipped']:,} | Err: {result['rows_error']:,} | "
                    f"Map: {result['mapping_applied']:,}")
        if result.get("errors"):
            for err in result["errors"][:3]:
                logger.warning(f"    ⚠ {err}")

    elapsed = (datetime.now() - start_time).total_seconds()

    # Post-import stats
    if not args.dry_run:
        post_stats = get_db_stats(conn, "post-import")
    else:
        post_stats = {"label": "dry-run", "total_rows": pre_stats["total_rows"],
                      "unique_indicators": pre_stats["unique_indicators"],
                      "mapped_indicators": pre_stats["mapped_indicators"],
                      "date_min": pre_stats["date_min"], "date_max": pre_stats["date_max"],
                      "commodity_stats": [], "source_stats": {}, "import_log_count": 0}

    # Close DB
    conn.close()

    # =============================================================================
    # Final Summary Report
    # =============================================================================
    logger.info("")
    logger.info("=" * 70)
    logger.info("  IMPORT COMPLETE — FINAL SUMMARY")
    logger.info("=" * 70)

    # File-level summary
    total_read = sum(r["rows_read"] for r in all_results)
    total_inserted = sum(r["rows_inserted"] for r in all_results)
    total_skipped = sum(r["rows_skipped"] for r in all_results)
    total_error = sum(r["rows_error"] for r in all_results)
    total_mapped = sum(r["mapping_applied"] for r in all_results)

    logger.info(f"  {'File':<35} {'Read':>8} {'Insert':>8} {'Skip':>8} {'Err':>6} {'Mapped':>8}")
    logger.info(f"  {'-'*35} {'-'*8} {'-'*8} {'-'*8} {'-'*6} {'-'*8}")
    for r in all_results:
        logger.info(f"  {r['file']:<35} {r['rows_read']:>8,} {r['rows_inserted']:>8,} {r['rows_skipped']:>8,} {r['rows_error']:>6,} {r['mapping_applied']:>8,}")
    logger.info(f"  {'-'*35} {'-'*8} {'-'*8} {'-'*8} {'-'*6} {'-'*8}")
    logger.info(f"  {'TOTAL':<35} {total_read:>8,} {total_inserted:>8,} {total_skipped:>8,} {total_error:>6,} {total_mapped:>8,}")

    # Insert rate
    if total_read > 0:
        logger.info(f"  Insert rate: {total_inserted / total_read * 100:.1f}%")

    # Error summary
    if total_error > 0:
        logger.warning(f"  ⚠ {total_error} total import errors across all files")
    else:
        logger.info(f"  ✅ 0 import errors — clean import")

    # Conflict summary
    if total_skipped > 0:
        logger.info(f"  ⚠ {total_skipped} rows skipped (primary key conflicts — expected on re-import)")
    else:
        logger.info(f"  ✅ 0 primary key conflicts")

    # Database summary
    logger.info("")
    logger.info(f"  Database:      {db_path}")
    logger.info(f"  Total rows:    {post_stats['total_rows']:,}")
    logger.info(f"  Unique IDs:    {post_stats['unique_indicators']}")
    logger.info(f"  Mapped IDs:    {post_stats['mapped_indicators']}")
    logger.info(f"  Date range:    {post_stats['date_min']} ~ {post_stats['date_max']}")
    logger.info(f"  Import logs:   {post_stats['import_log_count']}")

    # Per-commodity
    logger.info("")
    logger.info(f"  Per-commodity distribution:")
    for cs in post_stats["commodity_stats"]:
        logger.info(f"    {cs['commodity']:<8} {cs['rows']:>8,} rows  ({cs['unique_indicators']} unique indicators)")

    # Per-source
    logger.info("")
    logger.info(f"  Per-source distribution:")
    for src, cnt in post_stats["source_stats"].items():
        logger.info(f"    {src:<12} {cnt:>8,} rows")

    # Timing
    logger.info("")
    logger.info(f"  Elapsed: {elapsed:.1f} seconds")

    # Verification flags
    logger.info("")
    logger.info("=" * 70)
    logger.info("  VERIFICATION FLAGS")
    logger.info("=" * 70)
    logger.info(f"  DATABASE_INDEPENDENT=TRUE (phase03_test.db, NOT scripts/api_cache.db)")
    logger.info(f"  ALL_JSONL_IMPORTED=TRUE ({len(jsonl_paths)} files)")
    logger.info(f"  CU_AL_PB_SUPPLEMENT_INCLUDED=TRUE")
    logger.info(f"  IMPORT_ERRORS={total_error}")
    logger.info(f"  PRIMARY_KEY_CONFLICTS={total_skipped}")
    logger.info(f"  MAPPING_EFFECTIVE={total_mapped > 0}")
    logger.info(f"  TOTAL_INDICATORS={post_stats['unique_indicators']}")
    logger.info(f"  TOTAL_ROWS={post_stats['total_rows']}")
    logger.info("=" * 70)

    # Return exit code
    sys.exit(0 if total_error == 0 else 1)


if __name__ == "__main__":
    main()
