"""HERMEShf T0: Inspect phase03_test.db schema, tables, row counts."""
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "phase03_test.db"
)

print(f"DB_PATH: {DB_PATH}")
print(f"Exists: {os.path.exists(DB_PATH)}")
print(f"Size: {os.path.getsize(DB_PATH):,} bytes")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("\n=== TABLES ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    print(f"  {t}")

print("\n=== SCHEMA ===")
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
for name, sql in cur.fetchall():
    print(f"\n-- {name} --")
    print(sql)

print("\n=== INDEXES ===")
cur.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name")
for name, tbl, sql in cur.fetchall():
    print(f"  {tbl}.{name}: {sql}")

print("\n=== ROW COUNTS ===")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"  {t}: {cnt:,}")

print("\n=== INDICATOR_CACHE sample (first 5) ===")
cur.execute("SELECT * FROM indicator_cache LIMIT 5")
for row in cur.fetchall():
    print(f"  {row}")

print("\n=== DISTINCT metrics (sample) ===")
cur.execute("SELECT DISTINCT metric FROM indicator_cache LIMIT 20")
metrics = [r[0] for r in cur.fetchall()]
print(f"  total metrics: {len(metrics)}")
for m in metrics:
    print(f"    {m}")

print("\n=== DISTINCT codes (sample) ===")
cur.execute("SELECT DISTINCT code FROM indicator_cache LIMIT 20")
codes = [r[0] for r in cur.fetchall()]
print(f"  total codes: {len(codes)}")
for c in codes:
    print(f"    {c}")

print("\n=== SERIES_CACHE if exists ===")
if 'series_cache' in tables:
    cur.execute("SELECT COUNT(*) FROM series_cache")
    print(f"  series_cache rows: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    print(f"  unique indicator_ids: {cur.fetchone()[0]}")
    cur.execute("SELECT indicator_id, date, value FROM series_cache LIMIT 5")
    for row in cur.fetchall():
        print(f"    {row}")

conn.close()
print("\n=== Done ===")
