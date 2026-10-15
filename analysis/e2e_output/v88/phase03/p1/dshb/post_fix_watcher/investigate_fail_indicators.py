#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Investigate the 2 FAIL indicators from T1: ni_month_spread, ni_top20_net"""

import os, sys, sqlite3, json
from datetime import datetime
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUNBUFFERED"] = "1"
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DB = r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db"

def investigate(indicator_id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=?", (indicator_id,))
    cnt = cur.fetchone()[0]
    
    cur.execute("SELECT MIN(date), MAX(date) FROM series_cache WHERE indicator_id=?", (indicator_id,))
    dr = cur.fetchone()
    
    cur.execute("SELECT MIN(value), MAX(value), AVG(value) FROM series_cache WHERE indicator_id=? AND value IS NOT NULL", (indicator_id,))
    stats = cur.fetchone()
    
    cur.execute("SELECT COUNT(DISTINCT value) FROM series_cache WHERE indicator_id=? AND value IS NOT NULL", (indicator_id,))
    distinct_vals = cur.fetchone()[0]
    
    cur.execute("SELECT value, COUNT(*) as cnt FROM series_cache WHERE indicator_id=? AND value IS NOT NULL GROUP BY value ORDER BY cnt DESC LIMIT 5", (indicator_id,))
    top_vals = cur.fetchall()
    
    cur.execute("SELECT date, value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date LIMIT 10", (indicator_id,))
    first10 = cur.fetchall()
    
    cur.execute("SELECT date, value FROM series_cache WHERE indicator_id=? AND value IS NOT NULL ORDER BY date DESC LIMIT 10", (indicator_id,))
    last10 = cur.fetchall()
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("INDICATOR: %s" % indicator_id)
    print("=" * 60)
    print("  Total rows: %d" % cnt)
    print("  Date range: %s ~ %s" % (dr[0], dr[1]))
    print("  Min value: %s" % stats[0])
    print("  Max value: %s" % stats[1])
    print("  Avg value: %.6f" % stats[2])
    print("  Distinct values: %d" % distinct_vals)
    print("  Top 5 values (by frequency):")
    for row in top_vals:
        print("    %.6f x %d" % (row[0], row[1]))
    print("  First 10 data points:")
    for row in first10:
        print("    %s: %.6f" % (row[0], row[1]))
    print("  Last 10 data points:")
    for row in last10:
        print("    %s: %.6f" % (row[0], row[1]))

if __name__ == "__main__":
    print("T1 FAIL Indicator Investigation")
    print("Time: %s" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    investigate("ni_month_spread")
    investigate("ni_top20_net")
