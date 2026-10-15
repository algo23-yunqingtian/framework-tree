#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_cu_al_pb_supplement.py — Import CU/AL/PB supplement JSONL into api_cache.db
================================================================================
TASK_ID: V88_PHASE03_P0_R0_SUPPLEMENT_CU_AL_PB_DATA
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  Import the generated CU/AL/PB supplement JSONL data into api_cache.db
  using the existing db_import_jsonl.py import logic.

Usage:
  python import_cu_al_pb_supplement.py [--dry-run]

Constraints:
  - NO_ZHIJI_API_CALL / NO_OVERWRITE / APPEND_ONLY
  - INSERT OR IGNORE (no existing data overwritten)
  - Pure Python standard library
"""

import os
import sys
import sqlite3
import logging
import argparse
from pathlib import Path

# Add parent directory to path to import db_import_jsonl
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from db_import_jsonl import (
    setup_database,
    import_file,
    REPO_ROOT,
    DEFAULT_DB_PATH,
    JSONL_FILES,
)

# =============================================================================
# Configuration
# =============================================================================

SUPPLEMENT_FILE = REPO_ROOT / "data" / "db_export" / "cu_al_pb_supplement.jsonl"

# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Import CU/AL/PB supplement JSONL into api_cache.db"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode (no actual writes)")
    parser.add_argument("--db", type=str,
                        default=str(DEFAULT_DB_PATH),
                        help="Path to api_cache.db")
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
    logger.info(f"Database: {db_path}")
    logger.info(f"Supplement file: {SUPPLEMENT_FILE}")
    logger.info(f"Dry run: {args.dry_run}")

    # Validate supplement file exists
    if not SUPPLEMENT_FILE.exists():
        logger.error(f"Supplement file not found: {SUPPLEMENT_FILE}")
        sys.exit(1)

    # Check file size
    file_size = SUPPLEMENT_FILE.stat().st_size
    logger.info(f"File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

    # Setup database
    conn = setup_database(db_path)
    logger.info("Database connection established")

    # Get pre-import stats
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM series_cache")
    pre_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    pre_unique = cur.fetchone()[0]
    logger.info(f"Pre-import: {pre_total:,} total rows, {pre_unique} unique indicators")

    # Import the supplement file
    logger.info("Importing supplement file...")
    result = import_file(conn, str(SUPPLEMENT_FILE), dry_run=args.dry_run)

    # Get post-import stats
    if not args.dry_run:
        cur.execute("SELECT COUNT(*) FROM series_cache")
        post_total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
        post_unique = cur.fetchone()[0]

        # Count CU/AL/PB rows
        cur.execute("""
            SELECT COUNT(*) FROM series_cache 
            WHERE indicator_id LIKE 'cu_%' OR indicator_id LIKE 'al_%' OR indicator_id LIKE 'j%'
        """)
        cu_al_pb_rows = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(DISTINCT indicator_id) FROM series_cache
            WHERE indicator_id LIKE 'cu_%' OR indicator_id LIKE 'al_%' OR indicator_id LIKE 'j%'
        """)
        cu_al_pb_unique = cur.fetchone()[0]

        logger.info(f"Post-import: {post_total:,} total rows, {post_unique} unique indicators")
        logger.info(f"CU/AL/PB: {cu_al_pb_rows:,} rows, {cu_al_pb_unique} unique indicators")
        logger.info(f"Delta: +{post_total - pre_total:,} rows, +{post_unique - pre_unique} unique indicators")
    else:
        logger.info("Dry run complete - no data written")

    # Summary
    logger.info(f"Import summary:")
    logger.info(f"  File: {result['file']}")
    logger.info(f"  Rows read: {result['rows_read']:,}")
    logger.info(f"  Rows inserted: {result['rows_inserted']:,}")
    logger.info(f"  Rows skipped (conflicts): {result['rows_skipped']:,}")
    logger.info(f"  Rows error: {result['rows_error']:,}")
    logger.info(f"  Mapping applied: {result['mapping_applied']:,}")
    if result.get('errors'):
        logger.warning(f"  Errors: {result['errors'][:5]}")

    conn.close()
    logger.info("Done")

    return 0 if result['rows_error'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
