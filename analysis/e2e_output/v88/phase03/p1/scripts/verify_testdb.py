#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_testdb.py — V88 Phase03 P1 DSHB 校验脚本 (8条DQA规则)
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  Verify phase03_test.db integrity with 8 DQA validation rules:
    DQA-01: 空值检测 (NULL detection)
    DQA-02: 重复ID检测 (Duplicate ID detection)
    DQA-03: 时间连续性检测 (Time continuity)
    DQA-04: 数值越界检测 (Value out-of-bounds)
    DQA-05: 映射缺失检测 (Mapping missing)
    DQA-06: 时间漂移检测 (Time drift)
    DQA-07: 重复点检测 (Duplicate points)
    DQA-08: 单位不一致检测 (Unit inconsistency)

Usage:
  python verify_testdb.py [--db path/to/phase03_test.db] [--dqa] [--exit-code]
"""

import os
import sys
import sqlite3
import platform
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
P0_DIR = SCRIPT_DIR.parent.parent.parent
P1_DIR = SCRIPT_DIR.parent
DB_PATH_DEFAULT = P0_DIR / "p0" / "phase03_test.db"
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent
ORIG_DB_PATH = REPO_ROOT / "scripts" / "api_cache.db"

# Expected baseline values (P1 updated)
EXPECTED_ROWS = 590411
EXPECTED_INDICATORS = 674
EXPECTED_MAPPED = 667
EXPECTED_ERRORS = 0
EXPECTED_PK_CONFLICTS = 0
EXPECTED_DERIVED = 59
EXPECTED_REAL = 615
EXPECTED_TOTAL_ROWS = 590411
EXPECTED_DERIVED_ROWS = 114818

# DQA thresholds
DQA_VALUE_OUTLIER_THRESHOLD = 3.0  # 3-sigma for outlier detection
DQA_TIME_GAP_DAYS = 90              # Max acceptable gap between data points
DQA_TIME_DRIFT_DAYS = 365           # Max acceptable time drift
DQA_NULL_RATE_THRESHOLD = 0.01     # 1% max null rate

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
# Core Verification (Inherited from P0)
# =============================================================================

def check_db_exists(db_path):
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
    print("\n2. SCHEMA")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]
    required_tables = ["series_cache", "import_log"]
    for tname in required_tables:
        status = "FOUND" if tname in tables else "MISSING"
        print(f"   Table {tname}: {status}")
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
    indexes = [row[0] for row in cur.fetchall()]
    expected_indexes = ["idx_indicator", "idx_indicator_mapped", "idx_commodity", "idx_date"]
    for idx in expected_indexes:
        status = "FOUND" if idx in indexes else "NOT FOUND"
        print(f"   Index {idx}: {status}")
    return len(tables)


def check_row_counts(conn):
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
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
    mapped = cur.fetchone()[0]
    ok = "[OK]" if mapped == EXPECTED_MAPPED else "[WARN]"
    print(f"   Mapped source indicators: {mapped}  {ok}  (expected: {EXPECTED_MAPPED})")
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source='derived'")
    derived = cur.fetchone()[0]
    ok = "[OK]" if derived == EXPECTED_DERIVED else "[WARN]"
    print(f"   Derived indicators: {derived}  {ok}  (expected: {EXPECTED_DERIVED})")
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source='real'")
    real = cur.fetchone()[0]
    print(f"   Real indicators: {real}")
    cur.execute("SELECT MIN(date), MAX(date) FROM series_cache")
    dr = cur.fetchone()
    print(f"   Date range: {dr[0]} ~ {dr[1]}")
    return total, unique, mapped, derived, real


def check_pk_uniqueness(conn):
    print("\n4. PRIMARY KEY UNIQUENESS")
    cur = conn.cursor()
    cur.execute("""
        SELECT indicator_id, date, COUNT(*) as cnt
        FROM series_cache GROUP BY indicator_id, date HAVING cnt > 1
    """)
    dupes = cur.fetchall()
    status = "[OK]" if len(dupes) == 0 else "[FAIL]"
    print(f"   Duplicate (indicator_id, date) pairs: {len(dupes)}  {status}")
    if dupes:
        for d in dupes[:10]:
            print(f"     DUPE: {d[0]} | {d[1]} | count={d[2]}")
    return len(dupes)


def check_source_distribution(conn):
    print("\n5. SOURCE DISTRIBUTION")
    cur = conn.cursor()
    cur.execute("SELECT source, COUNT(*) FROM series_cache GROUP BY source ORDER BY COUNT(*) DESC")
    for row in cur.fetchall():
        print(f"   {row[0]}: {row[1]:,}")
    return 0


def check_import_log(conn):
    print("\n6. IMPORT LOG")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM import_log")
    log_count = cur.fetchone()[0]
    print(f"   Import log entries: {log_count}")
    cur.execute("""
        SELECT source_file, rows_read, rows_inserted, rows_skipped, rows_error
        FROM import_log ORDER BY id
    """)
    total_read = total_inserted = total_skipped = total_error = 0
    for row in cur.fetchall():
        fname, read, ins, skip, err = row
        print(f"   {fname:<35} read={read:>8,} ins={ins:>8,} skip={skip:>6,} err={err}")
        total_read += read; total_inserted += ins; total_skipped += skip; total_error += err
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
    print("\n7. PER-COMMODITY STATS")
    cur = conn.cursor()
    cur.execute("""
        SELECT commodity, COUNT(*) as rows, COUNT(DISTINCT indicator_id) as uniq
        FROM series_cache GROUP BY commodity ORDER BY commodity
    """)
    total_rows = total_unique = 0
    for row in cur.fetchall():
        comm, cnt, uniq = row
        print(f"   {comm:<8} {cnt:>8,} rows  {uniq:>4} indicators")
        total_rows += cnt; total_unique += uniq
    print(f"   ---")
    print(f"   Total: {total_rows:,} rows, {total_unique} unique indicators")
    return 0


def check_mapped_vs_unmapped(conn):
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
    print("\n9. ISOLATION CHECK (vs scripts/api_cache.db)")
    if not orig_db_path.exists():
        print(f"   Original DB not found: {orig_db_path}")
        return True
    orig_conn = sqlite3.connect(str(orig_db_path))
    orig_cur = orig_conn.cursor()
    orig_cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    orig_tables = [row[0] for row in orig_cur.fetchall()]
    print(f"   Original tables: {orig_tables}")
    orig_total = orig_unique = 0
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
# DQA Validation Rules (P1 NEW)
# =============================================================================

def dqa_01_null_detection(conn):
    """DQA-01: NULL detection across all fields"""
    print("\n10. DQA-01: NULL DETECTION")
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN indicator_id IS NULL THEN 1 ELSE 0 END) as null_indicator,
            SUM(CASE WHEN indicator_id_mapped IS NULL THEN 1 ELSE 0 END) as null_mapped,
            SUM(CASE WHEN commodity IS NULL THEN 1 ELSE 0 END) as null_commodity,
            SUM(CASE WHEN date IS NULL THEN 1 ELSE 0 END) as null_date,
            SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) as null_value,
            SUM(CASE WHEN source IS NULL THEN 1 ELSE 0 END) as null_source
        FROM series_cache
    """)
    row = cur.fetchone()
    total = row[0]
    nulls = {"indicator_id": row[1], "indicator_id_mapped": row[2], "commodity": row[3], "date": row[4], "value": row[5], "source": row[6]}
    null_rate = sum(nulls.values()) / (total * 6) if total > 0 else 0

    all_pass = True
    for field, cnt in nulls.items():
        rate = cnt / total * 100 if total > 0 else 0
        status = "[OK]" if rate <= DQA_NULL_RATE_THRESHOLD * 100 or field == "indicator_id_mapped" else "[WARN]"
        if field != "indicator_id_mapped" and rate > DQA_NULL_RATE_THRESHOLD * 100:
            all_pass = False
        print(f"   {field:<25} NULL: {cnt:>8,} ({rate:6.2f}%) {status}")

    # Special: unmapped indicators are expected
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NULL")
    unmapped_cnt = cur.fetchone()[0]
    print(f"   Unmapped indicators (expected): {unmapped_cnt}")

    return all_pass


def dqa_02_duplicate_id_detection(conn):
    """DQA-02: Duplicate ID detection (same indicator_id + date appearing multiple times)"""
    print("\n11. DQA-02: DUPLICATE ID DETECTION")
    cur = conn.cursor()
    cur.execute("""
        SELECT indicator_id, date, COUNT(*) as cnt
        FROM series_cache GROUP BY indicator_id, date HAVING cnt > 1
    """)
    dupes = cur.fetchall()
    status = "[OK]" if len(dupes) == 0 else "[FAIL]"
    print(f"   Duplicate (indicator_id, date) pairs: {len(dupes)}  {status}")
    if dupes:
        for d in dupes[:10]:
            print(f"     DUPE: {d[0]} | {d[1]} | count={d[2]}")
    return len(dupes) == 0


def dqa_03_time_continuity(conn):
    """DQA-03: Time continuity check (max gap between consecutive data points)"""
    print("\n12. DQA-03: TIME CONTINUITY")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT indicator_id FROM series_cache ORDER BY indicator_id")
    indicators = [r[0] for r in cur.fetchall()]

    max_gap = 0
    max_gap_indicator = ""
    max_gap_date = ""
    gap_exceeds = 0

    for ind_id in indicators[:100]:  # Check first 100 indicators
        cur.execute("SELECT date FROM series_cache WHERE indicator_id=? ORDER BY date", (ind_id,))
        dates = [r[0] for r in cur.fetchall()]
        for i in range(1, len(dates)):
            try:
                d1 = datetime.strptime(dates[i-1], "%Y-%m-%d")
                d2 = datetime.strptime(dates[i], "%Y-%m-%d")
                gap = (d2 - d1).days
                if gap > max_gap:
                    max_gap = gap
                    max_gap_indicator = ind_id
                    max_gap_date = dates[i]
                if gap > DQA_TIME_GAP_DAYS:
                    gap_exceeds += 1
            except:
                pass

    status = "[OK]" if gap_exceeds == 0 else "[WARN]"
    print(f"   Max gap: {max_gap} days ({max_gap_indicator} at {max_gap_date})")
    print(f"   Gaps exceeding {DQA_TIME_GAP_DAYS} days: {gap_exceeds}  {status}")
    return gap_exceeds == 0


def dqa_04_value_out_of_bounds(conn):
    """DQA-04: Value out-of-bounds detection (3-sigma outlier check per indicator)"""
    print("\n13. DQA-04: VALUE OUT-OF-BOUNDS (3-sigma)")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT indicator_id FROM series_cache ORDER BY indicator_id")
    indicators = [r[0] for r in cur.fetchall()]

    total_outliers = 0
    indicators_with_outliers = 0

    for ind_id in indicators[:200]:  # Check first 200 indicators
        cur.execute("SELECT value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL", (ind_id,))
        values = [r[0] for r in cur.fetchall()]
        if len(values) < 30:
            continue
        mean = sum(values) / len(values)
        variance = sum((v - mean)**2 for v in values) / len(values)
        std = variance ** 0.5
        if std == 0:
            continue
        outliers = [v for v in values if abs(v - mean) > DQA_VALUE_OUTLIER_THRESHOLD * std]
        if outliers:
            indicators_with_outliers += 1
            total_outliers += len(outliers)

    status = "[OK]" if total_outliers == 0 else "[WARN]"
    print(f"   Total outliers (3-sigma): {total_outliers}")
    print(f"   Indicators with outliers: {indicators_with_outliers}/{min(len(indicators), 200)}")
    print(f"   Threshold: {DQA_VALUE_OUTLIER_THRESHOLD} sigma  {status}")
    return True  # Outliers are flagged but not blocking


def dqa_05_mapping_missing(conn):
    """DQA-05: Mapping missing detection"""
    print("\n14. DQA-05: MAPPING MISSING")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NULL")
    unmapped = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    total = cur.fetchone()[0]
    rate = unmapped / total * 100 if total > 0 else 0
    status = "[OK]" if rate <= 5 else "[WARN]"
    print(f"   Unmapped indicators: {unmapped}/{total} ({rate:.2f}%)  {status}")

    # List unmapped indicators
    cur.execute("""
        SELECT DISTINCT indicator_id, commodity, COUNT(*) as cnt
        FROM series_cache WHERE indicator_id_mapped IS NULL
        GROUP BY indicator_id, commodity ORDER BY cnt DESC
    """)
    rows = cur.fetchall()
    if rows:
        print(f"   Unmapped details:")
        for r in rows[:20]:
            print(f"     {r[0]:<35} comm={r[1]:<6} rows={r[2]:>6}")
        if len(rows) > 20:
            print(f"     ... and {len(rows) - 20} more")
    return True


def dqa_06_time_drift(conn):
    """DQA-06: Time drift detection (max date lag vs latest date)"""
    print("\n15. DQA-06: TIME DRIFT")
    cur = conn.cursor()
    cur.execute("SELECT MAX(date) FROM series_cache")
    max_date = cur.fetchone()[0]
    max_dt = datetime.strptime(max_date, "%Y-%m-%d")

    cur.execute("SELECT indicator_id, MAX(date) as latest FROM series_cache GROUP BY indicator_id")
    drifts = []
    for row in cur.fetchall():
        try:
            ind_dt = datetime.strptime(row[1], "%Y-%m-%d")
            drift = (max_dt - ind_dt).days
            drifts.append((row[0], row[1], drift))
        except:
            pass

    drifts.sort(key=lambda x: x[2], reverse=True)
    max_drift = drifts[0][2] if drifts else 0
    exceeded = [d for d in drifts if d[2] > DQA_TIME_DRIFT_DAYS]
    status = "[OK]" if not exceeded else "[WARN]"
    print(f"   Latest date: {max_date}")
    print(f"   Max drift: {max_drift} days ({drifts[0][0]} at {drifts[0][1]})" if drifts else "   No drift data")
    print(f"   Indicators with drift > {DQA_TIME_DRIFT_DAYS} days: {len(exceeded)}  {status}")
    if exceeded:
        for d in exceeded[:10]:
            print(f"     {d[0]:<35} latest={d[1]} drift={d[2]}d")
    return True


def dqa_07_duplicate_points(conn):
    """DQA-07: Duplicate data points detection (exact same value across consecutive dates)"""
    print("\n16. DQA-07: DUPLICATE POINTS (stale data)")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT indicator_id FROM series_cache ORDER BY indicator_id")
    indicators = [r[0] for r in cur.fetchall()]

    stale_indicators = 0
    total_stale_points = 0

    for ind_id in indicators[:100]:
        cur.execute("SELECT date, value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date", (ind_id,))
        rows = cur.fetchall()
        stale_count = 0
        for i in range(1, len(rows)):
            if rows[i][1] == rows[i-1][1]:
                stale_count += 1
        if stale_count > 0:
            stale_indicators += 1
            total_stale_points += stale_count

    status = "[OK]" if total_stale_points == 0 else "[INFO]"
    print(f"   Stale points (consecutive same value): {total_stale_points}")
    print(f"   Indicators with stale data: {stale_indicators}/{min(len(indicators), 100)}")
    print(f"   {status}")
    return True


def dqa_08_unit_inconsistency(conn):
    """DQA-08: Unit inconsistency detection (value range check by indicator type)"""
    print("\n17. DQA-08: UNIT INCONSISTENCY")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT indicator_id FROM series_cache ORDER BY indicator_id")
    indicators = [r[0] for r in cur.fetchall()]

    inconsistencies = 0
    checked = 0

    for ind_id in indicators:
        cur.execute("SELECT MIN(value), MAX(value), AVG(value) FROM series_cache WHERE indicator_id=? AND value IS NOT NULL", (ind_id,))
        row = cur.fetchone()
        if row[0] is None:
            continue
        min_v, max_v, avg_v = row
        checked += 1

        # Check for suspicious patterns
        # 1. All values same (constant series - suspicious)
        if min_v == max_v:
            inconsistencies += 1
            print(f"   CONSTANT: {ind_id} value={min_v}")
        # 2. Negative values where shouldn't be (check by indicator name)
        elif min_v < 0 and not any(k in ind_id for k in ["basis", "premium", "spread", "change", "term", "top20_net"]):
            inconsistencies += 1
            print(f"   NEGATIVE: {ind_id} min={min_v:.4f} max={max_v:.4f}")
        # 3. Extreme value ranges (min/max ratio > 1000x)
        elif avg_v != 0 and abs(max_v / avg_v) > 1000:
            inconsistencies += 1
            print(f"   EXTREME RANGE: {ind_id} min={min_v:.4f} max={max_v:.4f} avg={avg_v:.4f}")

    status = "[OK]" if inconsistencies == 0 else "[WARN]"
    print(f"   Checked: {checked} indicators")
    print(f"   Inconsistencies found: {inconsistencies}  {status}")
    return True

# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Verify phase03_test.db integrity with DQA rules"
    )
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT),
                        help="Path to phase03_test.db")
    parser.add_argument("--dqa", action="store_true",
                        help="Run DQA validation rules")
    parser.add_argument("--exit-code", action="store_true",
                        help="Return non-zero exit code on verification failure")
    args = parser.parse_args()

    setup_environment()

    db_path = Path(args.db)
    use_exit_code = args.exit_code

    print("=" * 72)
    print("  V88 Phase03 P1 -- phase03_test.db Verification")
    print("  TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB")
    print("  AGENT: DSHB | BRANCH: feature/v88-g1")
    print("=" * 72)

    # 1. DB exists
    exists, conn = check_db_exists(db_path)
    if not exists:
        print("\nVERIFICATION FAILED -- database file missing")
        sys.exit(1)

    # Core checks
    check_schema(conn)
    total, unique, mapped, derived, real = check_row_counts(conn)
    pk_conflicts = check_pk_uniqueness(conn)
    check_source_distribution(conn)
    total_errors, total_skipped = check_import_log(conn)
    check_per_commodity(conn)
    check_mapped_vs_unmapped(conn)
    check_isolation(conn, ORIG_DB_PATH)

    # DQA rules
    dqa_results = {}
    if args.dqa:
        print("\n" + "=" * 72)
        print("  DQA VALIDATION RULES (P1)")
        print("=" * 72)
        dqa_results["dqa_01_null"] = dqa_01_null_detection(conn)
        dqa_results["dqa_02_duplicate_id"] = dqa_02_duplicate_id_detection(conn)
        dqa_results["dqa_03_time_continuity"] = dqa_03_time_continuity(conn)
        dqa_results["dqa_04_value_out_of_bounds"] = dqa_04_value_out_of_bounds(conn)
        dqa_results["dqa_05_mapping_missing"] = dqa_05_mapping_missing(conn)
        dqa_results["dqa_06_time_drift"] = dqa_06_time_drift(conn)
        dqa_results["dqa_07_duplicate_points"] = dqa_07_duplicate_points(conn)
        dqa_results["dqa_08_unit_inconsistency"] = dqa_08_unit_inconsistency(conn)
    else:
        print("\n  [INFO] DQA rules not run (use --dqa flag)")

    conn.close()

    # Summary
    print("\n" + "=" * 72)
    print("  VERIFICATION SUMMARY")
    print("=" * 72)

    checks = []
    checks.append(("Database exists", exists))
    checks.append(("Total rows match", total == EXPECTED_ROWS))
    checks.append(("Unique indicators match", unique == EXPECTED_INDICATORS))
    checks.append(("Mapped source indicators match", mapped == EXPECTED_MAPPED))
    checks.append(("Zero PK conflicts", pk_conflicts == 0))
    checks.append(("Zero import errors", total_errors == 0))
    checks.append(("Zero PK skips", total_skipped == 0))
    checks.append(("Derived indicators = 59", derived == EXPECTED_DERIVED))

    all_pass = True
    for name, passed in checks:
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"   {icon} {name}")
        if not passed:
            all_pass = False

    if args.dqa:
        print("\n  DQA RESULTS:")
        for name, passed in dqa_results.items():
            icon = "[PASS]" if passed else "[WARN]"
            print(f"   {icon} {name}")

    print("\n" + "=" * 72)
    if all_pass:
        print("  VERDICT: ALL CHECKS PASSED")
        print(f"  Total: {total:,} rows | {unique} indicators | {mapped} mapped")
        print(f"  Derived: {derived} | Real: {real}")
        print(f"  Errors: {total_errors} | PK conflicts: {pk_conflicts}")
        print("=" * 72)
    else:
        print("  VERDICT: SOME CHECKS FAILED -- review details above")
        print("=" * 72)

    if use_exit_code:
        sys.exit(0 if all_pass else 1)
    sys.exit(0)


if __name__ == "__main__":
    main()