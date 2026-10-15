#!/usr/bin/env python3
"""List all indicators grouped by commodity from phase03_test.db"""
import sqlite3
import sys
from pathlib import Path

db_path = Path(r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

print("=" * 80)
print("ALL INDICATORS IN phase03_test.db")
print("=" * 80)

cur.execute("SELECT COUNT(*) FROM series_cache")
total = cur.fetchone()[0]
print(f"Total rows: {total:,}")

cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
total_ind = cur.fetchone()[0]
print(f"Total indicators: {total_ind}")

print()
for comm in ['cu', 'al', 'pb', 'zn', 'ni', 'sn', 'li', 'si', 'j']:
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE commodity=?", (comm,))
    cnt = cur.fetchone()[0]
    if cnt == 0:
        continue
    print(f"\n--- {comm.upper()} ({cnt} indicators) ---")
    cur.execute("SELECT DISTINCT indicator_id FROM series_cache WHERE commodity=? ORDER BY indicator_id", (comm,))
    for row in cur.fetchall():
        print(f"  {row[0]}")

# Also check for any other commodities
cur.execute("SELECT commodity, COUNT(DISTINCT indicator_id) FROM series_cache GROUP BY commodity ORDER BY commodity")
print("\n\nCOMMODITY SUMMARY:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} indicators")

conn.close()