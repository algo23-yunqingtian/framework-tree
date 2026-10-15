#!/usr/bin/env python3
"""Verify phase03_test.db integrity and compare with api_cache.db"""
import sqlite3, json, sys
from pathlib import Path

P0_DIR = Path(r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0")
TEST_DB = P0_DIR / "phase03_test.db"
ORIG_DB = P0_DIR.parent.parent.parent.parent.parent / "scripts" / "api_cache.db"

print("=" * 60)
print("  T3 VERIFICATION - phase03_test.db")
print("=" * 60)

conn = sqlite3.connect(str(TEST_DB))
c = conn.cursor()

# 1. Schema
print("\n1. SCHEMA")
c.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
for r in c.fetchall():
    print(f"   {r[0]}")

# 2. Row counts
print("\n2. ROW COUNTS")
c.execute("SELECT COUNT(*) FROM series_cache")
total = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
uniq = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
mapped = c.fetchone()[0]
c.execute("SELECT MIN(date), MAX(date) FROM series_cache")
dr = c.fetchone()
print(f"   Total rows:           {total:,}")
print(f"   Unique indicator_id:  {uniq}")
print(f"   Mapped indicator_id:  {mapped}")
print(f"   Date range:           {dr[0]} ~ {dr[1]}")

# 3. Primary key uniqueness
print("\n3. PRIMARY KEY UNIQUENESS")
c.execute("""
    SELECT indicator_id, date, COUNT(*) as cnt 
    FROM series_cache GROUP BY indicator_id, date HAVING cnt > 1
""")
dupes = c.fetchall()
print(f"   Duplicate (indicator_id, date) pairs: {len(dupes)}")
for d in dupes[:5]:
    print(f"     DUPE: {d[0]} | {d[1]} | count={d[2]}")

# 4. Source distribution
print("\n4. SOURCE DISTRIBUTION")
c.execute("SELECT source, COUNT(*) FROM series_cache GROUP BY source")
for r in c.fetchall():
    print(f"   {r[0]}: {r[1]:,}")

# 5. Import log
print("\n5. IMPORT LOG")
c.execute("SELECT source_file, rows_read, rows_inserted, rows_skipped, rows_error FROM import_log ORDER BY id")
for r in c.fetchall():
    print(f"   {r[0]:<35} read={r[1]:>8,} ins={r[2]:>8,} skip={r[3]:>6,} err={r[4]}")

# 6. Per-commodity
print("\n6. PER-COMMODITY STATS")
c.execute("""
    SELECT commodity, COUNT(*) as rows, COUNT(DISTINCT indicator_id) as uniq
    FROM series_cache GROUP BY commodity ORDER BY commodity
""")
for r in c.fetchall():
    print(f"   {r[0]:<8} {r[1]:>8,} rows  {r[2]:>4} indicators")

# 7. CU/AL/PB
print("\n7. CU/AL/PB INDICATORS")
c.execute("""
    SELECT indicator_id, COUNT(*) as cnt FROM series_cache
    WHERE indicator_id LIKE 'cu_%' OR indicator_id LIKE 'al_%' OR indicator_id LIKE 'j%'
    GROUP BY indicator_id ORDER BY indicator_id
""")
for r in c.fetchall():
    print(f"   {r[0]:<45} {r[1]:>6,} rows")

# 8. Compare with original
print("\n8. COMPARISON WITH scripts/api_cache.db")
conn2 = sqlite3.connect(str(ORIG_DB))
c2 = conn2.cursor()
c2.execute("SELECT COUNT(*) FROM series_cache")
orig_total = c2.fetchone()[0]
c2.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
orig_uniq = c2.fetchone()[0]
c2.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
orig_mapped = c2.fetchone()[0]
print(f"   Original:  {orig_total:,} rows | {orig_uniq} unique | {orig_mapped} mapped")
print(f"   Test DB:   {total:,} rows | {uniq} unique | {mapped} mapped")
match = "YES" if (orig_total == total and orig_uniq == uniq and orig_mapped == mapped) else "NO"
print(f"   Match:     {match}")

# 9. Mapped vs unmapped
print("\n9. MAPPING COVERAGE")
c.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
m = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NULL")
u = c.fetchone()[0]
print(f"   Mapped:   {m} ({m/(m+u)*100:.1f}%)")
print(f"   Unmapped: {u} ({u/(m+u)*100:.1f}%)")

# 10. Verify original api_cache.db is unchanged
print("\n10. ORIGINAL DB UNCHANGED CHECK")
print(f"    Original api_cache.db rows: {orig_total:,} (should remain unchanged)")
print(f"    Phase03_test.db rows:       {total:,}")

conn.close()
conn2.close()
print("\n" + "=" * 60)
print("  VERIFICATION COMPLETE")
print("=" * 60)
