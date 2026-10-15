import sqlite3, json, os

DB = r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db"

conn = sqlite3.connect(DB)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", tables)

for t in tables:
    cols = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
    print(f"\nTable: {t[0]}")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
    cnt = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"  Row count: {cnt}")
    if cnt > 0:
        row = conn.execute(f"SELECT * FROM {t[0]} LIMIT 1").fetchone()
        print(f"  Sample: {row}")

conn.close()
