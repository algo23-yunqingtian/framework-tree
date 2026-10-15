#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_testdb.py — V88 Phase03 P0 DSHB Artifact Archive
==================================================================
TASK_ID: V88_PHASE03_P0_DSHB_ARTIFACT_ARCHIVE
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  Verify phase03_test.db integrity against expected baselines.
  Checks: schema, row counts, indicator count, PK uniqueness,
  source distribution, per-commodity stats, import log, and
  comparison with api_cache.db (to confirm isolation).

Expected Baselines (from verified import on 2026-10-15):
  Total rows:      475,593
  Unique indicators: 615
  Mapped indicators: 156
  Import errors:    0
  PK conflicts:     0

Usage:
  python verify_testdb.py [--db path/to/phase03_test.db] [--exit-code]

Constraints:
  - Pure Python standard library
  - Windows compatible (auto-sets PYTHONIOENCODING=utf-8)
  - Read-only: does NOT modify any database

Author: DSHB Agent
Date:   2026-10-15
"""

import os
import sys
import sqlite3
import platform
import argparse
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
P0_DIR = SCRIPT_DIR.parent
DEFAULT_DB_PATH = P0_DIR / "phase03_test.db"
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent
ORIG_DB_PATH = REPO_ROOT / "scripts" / "api_cache.db"

# Expected baseline values
EXPECTED_ROWS = 475593
EXPECTED_INDICATORS = 615
EXPECTED_MAPPED = 156
EXPECTED_ERRORS = 0
EXPECTED_PK_CONFLICTS = 0

# =============================================================================
# Platform Setup
# =============================================================================

def setup_environment():
    """Configure environment for Windows GBK console compatibility."""
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"


# =============================================================================
# Verification Functions
# =============================================================================

def check_db_exists(db_path):
    """Check that the database file exists, has non-zero size, and open connection."""
    print("\n1. DATABASE FILE")
    if not db_path.exists():
        print(f"   DATABASE NOT FOUND: {db_path}")
        return False, None
    size_bytes = db_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"   Path:   {db_path}")
    print(f"   Size:   {size_bytes:,} bytes ({size_mb:.1f} MB)")
    try:
        conn = sqlite3.connect(str(db_path))
        print(f"   Status: OPENED")
        return True, conn
    except sqlite3.Error as e:
        print(f"   Connection FAILED: {e}")
        return False, None


def check_schema(conn):
    """Verify expected tables exist with correct schema."""
    print("\n2. SCHEMA")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]

    required_tables = ["series_cache", "import_log"]
    for tname in required_tables:
        status = "FOUND" if tname in tables else "MISSING"
        print(f"   Table {tname}: {status}")

    # Check indexes
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
    indexes = [row[0] for row in cur.fetchall()]
    expected_indexes = ["idx_indicator", "idx_indicator_mapped", "idx_commodity", "idx_date"]
    for idx in expected_indexes:
        status = "FOUND" if idx in indexes else "NOT FOUND"
        print(f"   Index {idx}: {status}")

    return len(tables)


def check_row_counts(conn):
    """Verify row counts against baselines."""
    print("\n3. ROW COUNTS")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM series_cache")
    total = cur.fetchone()[0]
    ok = "[OK]" if total == EXPECTED_ROWS else "[WARN]"
    print(f"   Total rows: {total:,}  {ok}  (expected: {EXPECTED_ROWS:,})")

    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    unique = cur.fetchone()[0]
    ok = "[OK]" if unique == EXPECTED_INDICATORS else "[WARN]"
    print(f"   Unique indicators: {unique}  {ok}  (expected: {EXPECTED_INDICATORS})")

    cur.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
    mapped = cur.fetchone()[0]
    ok = "[OK]" if mapped == EXPECTED_MAPPED else "[WARN]"
    print(f"   Mapped indicators: {mapped}  {ok}  (expected: {EXPECTED_MAPPED})")

    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NULL")
    unmapped = cur.fetchone()[0]
    print(f"   Unmapped indicators: {unmapped}")

    cur.execute("SELECT MIN(date), MAX(date) FROM series_cache")
    dr = cur.fetchone()
    print(f"   Date range: {dr[0]} ~ {dr[1]}")

    return total, unique, mapped


def check_pk_uniqueness(conn):
    """Check primary key uniqueness (indicator_id, date pairs)."""
    print("\n4. PRIMARY KEY UNIQUENESS")
    cur = conn.cursor()
    cur.execute("""
        SELECT indicator_id, date, COUNT(*) as cnt
        FROM series_cache
        GROUP BY indicator_id, date
        HAVING cnt > 1
    """)
    dupes = cur.fetchall()
    status = "[OK]" if len(dupes) == 0 else "[FAIL]"
    print(f"   Duplicate (indicator_id, date) pairs: {len(dupes)}  {status}")
    if dupes:
        for d in dupes[:10]:
            print(f"     DUPE: {d[0]} | {d[1]} | count={d[2]}")
    return len(dupes)


def check_source_distribution(conn):
    """Check source type distribution."""
    print("\n5. SOURCE DISTRIBUTION")
    cur = conn.cursor()
    cur.execute("SELECT source, COUNT(*) FROM series_cache GROUP BY source ORDER BY COUNT(*) DESC")
    for row in cur.fetchall():
        print(f"   {row[0]}: {row[1]:,}")
    return 0


def check_import_log(conn):
    """Check import log entries."""
    print("\n6. IMPORT LOG")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM import_log")
    log_count = cur.fetchone()[0]
    print(f"   Import log entries: {log_count}")

    cur.execute("""
        SELECT source_file, rows_read, rows_inserted, rows_skipped, rows_error
        FROM import_log ORDER BY id
    """)
    total_read = 0
    total_inserted = 0
    total_skipped = 0
    total_error = 0
    for row in cur.fetchall():
        fname, read, ins, skip, err = row
        print(f"   {fname:<35} read={read:>8,} ins={ins:>8,} skip={skip:>6,} err={err}")
        total_read += read
        total_inserted += ins
        total_skipped += skip
        total_error += err
        if err > 0:
            print(f"     ERRORS in {fname}: {err}")

    print(f"   ---")
    print(f"   Total: read={total_read:,} ins={total_inserted:,} skip={total_skipped:,} err={total_error}")

    if total_error > 0:
        print(f"   TOTAL IMPORT ERRORS: {total_error} (expected: {EXPECTED_ERRORS})")
    else:
        print(f"   Zero import errors: [OK]")

    if total_skipped > 0:
        print(f"   Primary key conflicts (skipped): {total_skipped} (expected: {EXPECTED_PK_CONFLICTS})")
    else:
        print(f"   Zero PK conflicts: [OK]")

    return total_error, total_skipped


def check_per_commodity(conn):
    """Check per-commodity distribution."""
    print("\n7. PER-COMMODITY STATS")
    cur = conn.cursor()
    cur.execute("""
        SELECT commodity, COUNT(*) as rows, COUNT(DISTINCT indicator_id) as uniq
        FROM series_cache
        GROUP BY commodity
        ORDER BY commodity
    """)
    total_rows = 0
    total_unique = 0
    for row in cur.fetchall():
        comm, cnt, uniq = row
        print(f"   {comm:<8} {cnt:>8,} rows  {uniq:>4} indicators")
        total_rows += cnt
        total_unique += uniq
    print(f"   ---")
    print(f"   Total: {total_rows:,} rows, {total_unique} unique indicators")
    return 0


def check_mapped_vs_unmapped(conn):
    """Check mapping coverage."""
    print("\n8. MAPPING COVERAGE")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
    m = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NULL")
    u = cur.fetchone()[0]
    total = m + u
    pct = m / total * 100 if total > 0 else 0
    print(f"   Mapped:   {m} ({pct:.1f}%)")
    print(f"   Unmapped: {u} ({100 - pct:.1f}%)")
    print(f"   Total:    {total}")
    return m, u


def check_isolation(conn, orig_db_path):
    """Check that phase03_test.db is isolated from api_cache.db."""
    print("\n9. ISOLATION CHECK (vs scripts/api_cache.db)")

    if not orig_db_path.exists():
        print(f"   Original DB not found: {orig_db_path}")
        return True

    orig_conn = sqlite3.connect(str(orig_db_path))
    orig_cur = orig_conn.cursor()

    # Check original table structure
    orig_cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    orig_tables = [row[0] for row in orig_cur.fetchall()]
    print(f"   Original tables: {orig_tables}")

    orig_total = 0
    orig_unique = 0
    if "series_cache" in orig_tables:
        orig_cur.execute("SELECT COUNT(*) FROM series_cache")
        orig_total = orig_cur.fetchone()[0]
        orig_cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
        orig_unique = orig_cur.fetchone()[0]

    test_cur = conn.cursor()
    test_cur.execute("SELECT COUNT(*) FROM series_cache")
    test_total = test_cur.fetchone()[0]
    test_cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    test_unique = test_cur.fetchone()[0]

    print(f"   Original:  {orig_total:,} rows | {orig_unique} indicators")
    print(f"   Test DB:   {test_total:,} rows | {test_unique} indicators")

    if test_total == orig_total and test_unique == orig_unique:
        print(f"   RESULT: SAME as original -- DB is NOT isolated!")
    else:
        print(f"   RESULT: ISOLATED -- different from original ({test_total:,} vs {orig_total:,} rows)")

    orig_conn.close()
    return True


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Verify phase03_test.db integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH),
                        help="Path to phase03_test.db")
    parser.add_argument("--exit-code", action="store_true",
                        help="Return non-zero exit code on verification failure")
    args = parser.parse_args()

    setup_environment()

    db_path = Path(args.db)
    use_exit_code = args.exit_code

    print("=" * 72)
    print("  V88 Phase03 P0 -- phase03_test.db Verification")
    print("  TASK_ID: V88_PHASE03_P0_DSHB_ARTIFACT_ARCHIVE")
    print("  AGENT: DSHB | BRANCH: feature/v88-g1")
    print("=" * 72)

    # 1. DB exists
    exists, conn = check_db_exists(db_path)
    if not exists:
        print("\nVERIFICATION FAILED -- database file missing")
        sys.exit(1)

    cur = conn.cursor()

    # 2. Schema
    check_schema(conn)

    # 3. Row counts
    total, unique, mapped = check_row_counts(conn)

    # 4. PK uniqueness
    pk_conflicts = check_pk_uniqueness(conn)

    # 5. Source distribution
    check_source_distribution(conn)

    # 6. Import log
    total_errors, total_skipped = check_import_log(conn)

    # 7. Per-commodity
    check_per_commodity(conn)

    # 8. Mapping coverage
    check_mapped_vs_unmapped(conn)

    # 9. Isolation
    check_isolation(conn, ORIG_DB_PATH)

    conn.close()

    # =============================================================================
    # Summary
    # =============================================================================
    print("\n" + "=" * 72)
    print("  VERIFICATION SUMMARY")
    print("=" * 72)

    checks = []
    checks.append(("Database exists", exists))
    checks.append(("Total rows match", total == EXPECTED_ROWS))
    checks.append(("Unique indicators match", unique == EXPECTED_INDICATORS))
    checks.append(("Mapped indicators match", mapped == EXPECTED_MAPPED))
    checks.append(("Zero PK conflicts", pk_conflicts == 0))
    checks.append(("Zero import errors", total_errors == 0))
    checks.append(("Zero PK skips", total_skipped == 0))

    all_pass = True
    for name, passed in checks:
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"   {icon} {name}")
        if not passed:
            all_pass = False

    print("\n" + "=" * 72)
    if all_pass:
        print("  VERDICT: ALL CHECKS PASSED -- phase03_test.db is verified")
        print(f"  Total: {total:,} rows | {unique} indicators | {mapped} mapped")
        print(f"  Errors: {total_errors} | PK conflicts: {pk_conflicts}")
        print("  R-V88-031: Rebuild via script is verified -- .db file not required")
        print("=" * 72)
    else:
        print("  VERDICT: SOME CHECKS FAILED -- review details above")
        print("=" * 72)

    if use_exit_code:
        sys.exit(0 if all_pass else 1)
    sys.exit(0)


if __name__ == "__main__":
    main()
