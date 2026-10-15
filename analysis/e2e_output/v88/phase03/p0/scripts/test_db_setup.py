#!/usr/bin/env python3
"""Create test API cache DB with sample data for coverage calc testing."""
import sqlite3
import json
import os

test_db = "test_api_cache.db"
if os.path.exists(test_db):
    os.remove(test_db)

conn = sqlite3.connect(test_db)
conn.execute("""
    CREATE TABLE indicator_cache (
        code TEXT NOT NULL,
        metric TEXT NOT NULL,
        zhiji_id TEXT,
        data_json TEXT,
        name TEXT,
        unit TEXT,
        freq TEXT,
        fetched_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY(code, metric)
    )
""")

def insert_payload(code, metric, zhiji_id, payload, name, unit, freq):
    conn.execute(
        "INSERT OR REPLACE INTO indicator_cache(code, metric, zhiji_id, data_json, name, unit, freq, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        (code, metric, zhiji_id, json.dumps(payload), name, unit, freq)
    )

# CU - close front (real data)
insert_payload("CU", "cu_21_close_front", "FU00014941", {
    "id": "t1", "source": "real", "name": "close", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 75000.0}, {"date": "2026-10-02", "value": 75200.0}, {"date": "2026-10-03", "value": 75100.0}]
}, "主连", "元/吨", "daily")

# CU - spot premium (real data)
insert_payload("CU", "cu_22_premium", "ID123", {
    "id": "t2", "source": "real", "name": "premium", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": -200.0}, {"date": "2026-10-02", "value": -150.0}]
}, "现货升贴水", "元/吨", "daily")

# CU - basis (real data)
insert_payload("CU", "cu_21_basis", "ID456", {
    "id": "t3", "source": "real", "name": "basis", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-09-20", "value": 500.0}, {"date": "2026-09-21", "value": 450.0}]
}, "基差", "元/吨", "daily")

# CU - LME close (real data)
insert_payload("CU", "cu_23_lme_close", "ID789", {
    "id": "t4", "source": "real", "name": "LME close", "unit": "USD", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 9500.0}]
}, "LME铜", "USD", "daily")

# AL - close front (real data)
insert_payload("AL", "al_00_close_front", "FU00014934", {
    "id": "t5", "source": "real", "name": "al close", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 19500.0}, {"date": "2026-10-02", "value": 19600.0}]
}, "主连", "元/吨", "daily")

# AL - spot premium (real data)
insert_payload("AL", "al_00_premium", "ID999", {
    "id": "t6", "source": "real", "name": "al premium", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 100.0}]
}, "升贴水", "元/吨", "daily")

# PB - close (j21_close, real data)
insert_payload("PB", "j21_close", "FU00014946", {
    "id": "t7", "source": "real", "name": "pb close", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 16000.0}, {"date": "2026-10-02", "value": 16100.0}]
}, "主连", "元/吨", "daily")

# ZN - close front (real data)
insert_payload("ZN", "zn_21_close_front", "FU00014950", {
    "id": "t8", "source": "real", "name": "zn close", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-09-15", "value": 23000.0}, {"date": "2026-09-16", "value": 23100.0}, {"date": "2026-09-17", "value": 23200.0}]
}, "主连", "元/吨", "daily")

# ZN - LME close (real data)
insert_payload("ZN", "zn_23_lme_close", "ID001", {
    "id": "t9", "source": "real", "name": "ZN LME", "unit": "USD", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 2800.0}]
}, "LME锌", "USD", "daily")

# NI - close front (real data)
insert_payload("NI", "ni_21_close_front", "FU00014982", {
    "id": "t10", "source": "real", "name": "ni close", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 128000.0}]
}, "主连", "元/吨", "daily")

# NI - basis (real data)
insert_payload("NI", "ni_22_basis", "ID002", {
    "id": "t11", "source": "real", "name": "NI basis", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 300.0}]
}, "基差", "元/吨", "daily")

# SN - close front (simulated only - empty points)
insert_payload("SN", "sn_21_close_front", "FU00014952", {
    "id": "t12", "source": "simulated", "name": "sn close", "unit": "元/吨", "freq": "daily",
    "points": []
}, "主连", "元/吨", "daily")

# SN - basis (real data)
insert_payload("SN", "sn_21_basis", "ID003", {
    "id": "t13", "source": "real", "name": "SN basis", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": -100.0}]
}, "基差", "元/吨", "daily")

# LI/LC - close front (real data)
insert_payload("LC", "li_21_close_front", "FU00015030", {
    "id": "t14", "source": "real", "name": "lc close", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-08-01", "value": 85000.0}, {"date": "2026-08-15", "value": 86000.0}]
}, "主连", "元/吨", "daily")

# SI - close front (real data)
insert_payload("SI", "si_21_close_front_industrial_si", "FU00015015", {
    "id": "t15", "source": "real", "name": "si close", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 15000.0}, {"date": "2026-10-02", "value": 15100.0}]
}, "主连", "元/吨", "daily")

# SI - spot (real data)
insert_payload("SI", "si_24_spot", "ID004", {
    "id": "t16", "source": "real", "name": "IS spot", "unit": "元/吨", "freq": "daily",
    "points": [{"date": "2026-10-01", "value": 14500.0}]
}, "工业硅现货", "元/吨", "daily")

conn.commit()
conn.close()
print(f"Test DB created: {test_db}")
print(f"Size: {os.path.getsize(test_db)} bytes")

# Verify
conn = sqlite3.connect(test_db)
rows = conn.execute("SELECT code, metric FROM indicator_cache").fetchall()
print(f"Rows inserted: {len(rows)}")
for r in rows:
    print(f"  {r[0]:4s} | {r[1]}")
conn.close()
