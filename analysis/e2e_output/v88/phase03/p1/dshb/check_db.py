#!/usr/bin/env python3
"""Check DB state after derivation"""
import sqlite3
import sys
from pathlib import Path

db_path = Path(r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

print("=== DB STATE AFTER DERIVATION ===")
cur.execute("SELECT COUNT(*) FROM series_cache")
print(f"Total rows: {cur.fetchone()[0]:,}")

cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
print(f"Unique indicators: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
print(f"Distinct mapped IDs: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source='derived'")
print(f"Derived indicators: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source='real'")
print(f"Real indicators: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM series_cache WHERE source='derived'")
print(f"Derived rows: {cur.fetchone()[0]:,}")

cur.execute("SELECT COUNT(*) FROM series_cache WHERE source='real'")
print(f"Real rows: {cur.fetchone()[0]:,}")

cur.execute("SELECT MIN(date), MAX(date) FROM series_cache")
print(f"Date range: {cur.fetchone()}")

# P0-9 denominator check: count distinct indicator_ids that have a mapped value
cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
mapped_source = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
total_source = cur.fetchone()[0]
print(f"\nP0-9 numerator (source indicators with mapping): {mapped_source}")
print(f"P0-9 denominator (total source indicators): {total_source}")

# Count distinct mapped IDs (DSHE meta_chart side)
cur.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL")
dshe_ids = cur.fetchone()[0]
print(f"DSHE meta_chart indicator count (distinct mapped): {dshe_ids}")

conn.close()