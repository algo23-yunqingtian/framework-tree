"""HERMEShf: Check phase03_test.db schema and data in detail."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase03_test.db")
print(f"DB: {DB_PATH}")
print(f"Size: {os.path.getsize(DB_PATH):,} bytes")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print(f"Tables: {tables}")

# Schema of series_cache
cur.execute("SELECT sql FROM sqlite_master WHERE name='series_cache'")
sql = cur.fetchone()
print(f"series_cache schema: {sql[0] if sql else 'NOT FOUND'}")

# Row count
cur.execute("SELECT COUNT(*) FROM series_cache")
print(f"series_cache rows: {cur.fetchone()[0]:,}")

# Unique indicator_ids
cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
print(f"Unique indicator_ids: {cur.fetchone()[0]}")

# Unique indicator_id_mapped
cur.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
print(f"Unique indicator_id_mapped (non-null): {cur.fetchone()[0]}")

# Sample mapped indicators
cur.execute("SELECT DISTINCT indicator_id_mapped FROM series_cache WHERE indicator_id_mapped IS NOT NULL LIMIT 30")
mapped = [r[0] for r in cur.fetchall()]
print(f"\nSample mapped IDs ({len(mapped)}):")
for m in mapped:
    print(f"  {m}")

# Sample data rows for a mapped ID
cur.execute("SELECT indicator_id, indicator_id_mapped, commodity, date, value, source FROM series_cache WHERE indicator_id_mapped='ZN_FU00014950' LIMIT 5")
rows = cur.fetchall()
print(f"\nSample data for ZN_FU00014950 ({len(rows)} rows):")
for r in rows:
    print(f"  {r}")

# Import log
cur.execute("SELECT source_file, rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied FROM import_log ORDER BY id")
print(f"\nImport log:")
for r in cur.fetchall():
    print(f"  file={r[0]:30s} read={r[1]:>6,} ins={r[2]:>6,} skip={r[3]:>4} err={r[4]:>3} map={r[5]:>4}")

# Check for indicator_cache table
cur.execute("SELECT name FROM sqlite_master WHERE name='indicator_cache'")
ic = cur.fetchone()
print(f"\nindicator_cache table: {'EXISTS' if ic else 'NOT FOUND'}")

# Check api_cache.db
# DB_PATH = .../phase03/p0/phase03_test.db
# Need: .../framework-tree/scripts/api_cache.db
# phase03/p0 -> phase03 -> v88 -> e2e_output -> analysis -> framework-tree
p0_dir = os.path.dirname(DB_PATH)  # .../phase03/p0
phase03_dir = os.path.dirname(p0_dir)
v88_dir = os.path.dirname(phase03_dir)
e2e_dir = os.path.dirname(v88_dir)
analysis_dir = os.path.dirname(e2e_dir)
repo_root = os.path.dirname(analysis_dir)
api_db = os.path.join(repo_root, "scripts", "api_cache.db")
print(f"\napi_cache.db path: {api_db}")
if os.path.exists(api_db):
    ac = sqlite3.connect(api_db)
    cur2 = ac.cursor()
    cur2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    t2 = [r[0] for r in cur2.fetchall()]
    print(f"api_cache.db tables: {t2}")
    if 'indicator_cache' in t2:
        cur2.execute("SELECT COUNT(*) FROM indicator_cache")
        print(f"indicator_cache rows: {cur2.fetchone()[0]}")
    ac.close()

conn.close()
print("\nDone")
