#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storage_layer.py — Modular Storage Layer (Phase04 Import Ready)
=================================================================
TASK_ID: V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN
AGENT:   DSHB | BRANCH: feature/v88-g1
MODULE:  Level 4 of 4 (base_request → site_parser → field_mapping → storage)

Purpose
-------
Extended database storage layer supporting all 6 table types:
  - daily_kline
  - position_ranking
  - warrant_registration
  - industry_fundamental
  - msteel_fundamental (NEW in P026)
  - customs_fundamental (NEW in P026)

Design:
  - SQLite-based (stdlib, no external dependencies)
  - Schema mirrors WIND-aligned CSV columns
  - Supports both field-mapped and raw CSV data
  - APPEND_ONLY semantics (INSERT OR IGNORE for idempotent writes)
  - Data validation and dirty data filtering

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  NO_OVERWRITE        Existing DB tables are never dropped/truncated
  APPEND_ONLY         INSERT OR IGNORE for idempotent writes
  NO_FACTOR_CALC      Factor calculation remains prohibited
"""

import os
import sys
import json
import sqlite3
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = SCRIPT_DIR.parent

TASK_ID = "V88_PHASE03_P14_DSHB_P026_CRAWLER_DATA_SOURCE_EXPANSION_AND_PHASE04_INTEGRATION_PLAN"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "2.0.0"

DEFAULT_DB_PATH = ARCHIVE_DIR / "data" / "factor_data.db"


# =============================================================================
# 0. Schema Definitions (WIND-aligned, EXTENDED)
# =============================================================================
SCHEMAS = {
    "daily_kline": {
        "description": "Daily K-line data (OHLCV) - WIND-aligned",
        "primary_key": ["date", "s_code"],
        "columns": {
            "date": "TEXT NOT NULL",
            "s_code": "TEXT NOT NULL",
            "exch_code": "TEXT NOT NULL",
            "s_open": "REAL",
            "s_high": "REAL",
            "s_low": "REAL",
            "s_close": "REAL",
            "s_volume": "INTEGER",
            "s_oi": "INTEGER",
            "s_avg_price": "REAL",
            "source_url": "TEXT",
            "update_time": "TEXT NOT NULL",
        },
    },
    "position_ranking": {
        "description": "Position ranking data - member long/short positions",
        "primary_key": ["date", "s_code", "company_name"],
        "columns": {
            "date": "TEXT NOT NULL",
            "s_code": "TEXT NOT NULL",
            "exch_code": "TEXT NOT NULL",
            "rank": "INTEGER",
            "company_name": "TEXT NOT NULL",
            "long_pos": "INTEGER",
            "short_pos": "INTEGER",
            "long_chg": "INTEGER",
            "short_chg": "INTEGER",
            "source_url": "TEXT",
            "update_time": "TEXT NOT NULL",
        },
    },
    "warrant_registration": {
        "description": "Warrant registration/cancellation data",
        "primary_key": ["date", "s_code"],
        "columns": {
            "date": "TEXT NOT NULL",
            "s_code": "TEXT NOT NULL",
            "exch_code": "TEXT NOT NULL",
            "warrant_reg": "INTEGER",
            "warrant_can": "INTEGER",
            "warrant_net": "INTEGER",
            "warrant_bal": "INTEGER",
            "source_url": "TEXT",
            "update_time": "TEXT NOT NULL",
        },
    },
    "industry_fundamental": {
        "description": "Industry fundamental indicators (100ppi) - smelting rate, profit, inventory",
        "primary_key": ["date", "ind_code"],
        "columns": {
            "date": "TEXT NOT NULL",
            "ind_code": "TEXT NOT NULL",
            "ind_name": "TEXT",
            "value": "TEXT",
            "unit": "TEXT",
            "source_url": "TEXT",
            "update_time": "TEXT NOT NULL",
        },
    },
    "msteel_fundamental": {
        "description": "Mysteel fundamental indicators - TC, utilization, inventory (NEW P026)",
        "primary_key": ["date", "ind_code"],
        "columns": {
            "date": "TEXT NOT NULL",
            "ind_code": "TEXT NOT NULL",
            "ind_name": "TEXT",
            "value": "TEXT",
            "unit": "TEXT",
            "source_url": "TEXT",
            "update_time": "TEXT NOT NULL",
        },
    },
    "customs_fundamental": {
        "description": "Customs import/export data (NEW P026)",
        "primary_key": ["date", "ind_code"],
        "columns": {
            "date": "TEXT NOT NULL",
            "ind_code": "TEXT NOT NULL",
            "ind_name": "TEXT",
            "value": "TEXT",
            "unit": "TEXT",
            "source_url": "TEXT",
            "update_time": "TEXT NOT NULL",
        },
    },
}

# Reverse mapping: table name → field-mapped column names
TABLE_FIELDS = {
    "daily_kline": ["date", "s_code", "exch_code", "s_open", "s_high", "s_low",
                    "s_close", "s_volume", "s_oi", "s_avg_price", "source_url", "update_time"],
    "position_ranking": ["date", "s_code", "exch_code", "rank", "company_name",
                         "long_pos", "short_pos", "long_chg", "short_chg", "source_url", "update_time"],
    "warrant_registration": ["date", "s_code", "exch_code", "warrant_reg", "warrant_can",
                             "warrant_net", "warrant_bal", "source_url", "update_time"],
    "industry_fundamental": ["date", "ind_code", "ind_name", "value", "unit", "source_url", "update_time"],
    "msteel_fundamental": ["date", "ind_code", "ind_name", "value", "unit", "source_url", "update_time"],
    "customs_fundamental": ["date", "ind_code", "ind_name", "value", "unit", "source_url", "update_time"],
}


# =============================================================================
# 1. Database Interface
# =============================================================================
class DatabaseInterface:
    """
    SQLite database interface for crawled data storage.
    Phase04 will use this to import cleaned CSV data into the factor calculation pipeline.
    """

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.conn = None
        self.stats = {
            "tables_created": 0,
            "rows_inserted": 0,
            "rows_ignored": 0,
            "rows_rejected": 0,
            "tables_loaded": 0,
        }

    def connect(self):
        """Connect to SQLite database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        logging.info("Connected to database: %s", self.db_path)
        return self

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("Database connection closed")

    def create_all_tables(self):
        """Create all database tables (idempotent)."""
        for table_name, schema in SCHEMAS.items():
            self.create_table(table_name)
        logging.info("All %d tables created/verified", len(SCHEMAS))
        return self

    def create_table(self, table_name: str):
        """Create a single table if it doesn't exist."""
        if table_name not in SCHEMAS:
            raise ValueError(f"Unknown table: {table_name}")

        schema = SCHEMAS[table_name]
        columns_sql = ", ".join(
            f"{col} {dtype}" for col, dtype in schema["columns"].items()
        )
        pk_sql = ", ".join(schema["primary_key"])
        pk_constraint = f"PRIMARY KEY ({pk_sql})"

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql},
            {pk_constraint}
        )
        """
        try:
            self.conn.execute(create_sql)
            self.conn.commit()
            self.stats["tables_created"] += 1
            logging.debug("Table %s created/verified", table_name)
        except sqlite3.Error as e:
            logging.error("Failed to create table %s: %s", table_name, e)
            raise

        return self

    def load_csv(self, csv_path: str, table: str) -> dict:
        """
        Load CSV file into database table (idempotent INSERT OR IGNORE).

        Args:
            csv_path: Path to CSV file
            table: Target table name

        Returns:
            Dict with insert statistics.
        """
        if not self.conn:
            self.connect()

        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        if table not in SCHEMAS:
            raise ValueError(f"Unknown table: {table}")

        fields = TABLE_FIELDS[table]
        schema = SCHEMAS[table]
        pk_cols = schema["primary_key"]

        rows_inserted = 0
        rows_ignored = 0
        rows_rejected = 0

        # (Changes tracked per-cursor via rowcount)

        with open(csv_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Filter dirty data
                if self._is_dirty_row(row, pk_cols):
                    rows_rejected += 1
                    continue

                # Prepare INSERT OR IGNORE
                try:
                    values = []
                    col_names = []
                    for field in fields:
                        col_names.append(field)
                        val = row.get(field, "")
                        # Convert to appropriate type
                        col_type = schema["columns"].get(field, "")
                        if "REAL" in col_type or "INTEGER" in col_type:
                            try:
                                val = float(val) if "REAL" in col_type else int(float(val))
                            except (ValueError, TypeError):
                                val = None
                        values.append(val)

                    placeholders = ", ".join(["?"] * len(col_names))
                    col_list = ", ".join(col_names)
                    insert_sql = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})"

                    cursor = self.conn.execute(insert_sql, values)
                    if cursor.rowcount > 0:
                        rows_inserted += 1
                    else:
                        rows_ignored += 1
                except (sqlite3.Error, TypeError, ValueError) as e:
                    rows_rejected += 1
                    logging.debug("Row rejected for %s: %s", table, e)

        self.conn.commit()
        self.stats["rows_inserted"] += rows_inserted
        self.stats["rows_ignored"] += rows_ignored
        self.stats["rows_rejected"] += rows_rejected
        self.stats["tables_loaded"] += 1

        result = {
            "table": table,
            "csv_path": str(csv_path),
            "rows_inserted": rows_inserted,
            "rows_ignored": rows_ignored,
            "rows_rejected": rows_rejected,
        }
        logging.info("Loaded %s: %d inserted, %d ignored, %d rejected",
                     table, rows_inserted, rows_ignored, rows_rejected)
        return result

    def load_records(self, records: list, table: str) -> dict:
        """
        Load list of records into database table (idempotent INSERT OR IGNORE).

        Args:
            records: List of dicts (field-mapped)
            table: Target table name

        Returns:
            Dict with insert statistics.
        """
        if not self.conn:
            self.connect()

        if table not in SCHEMAS:
            raise ValueError(f"Unknown table: {table}")

        fields = TABLE_FIELDS[table]
        schema = SCHEMAS[table]
        pk_cols = schema["primary_key"]

        rows_inserted = 0
        rows_ignored = 0
        rows_rejected = 0

        for row in records:
            if self._is_dirty_row(row, pk_cols):
                rows_rejected += 1
                continue

            try:
                values = []
                col_names = []
                for field in fields:
                    col_names.append(field)
                    val = row.get(field, "")
                    col_type = schema["columns"].get(field, "")
                    if "REAL" in col_type or "INTEGER" in col_type:
                        try:
                            val = float(val) if "REAL" in col_type else int(float(val))
                        except (ValueError, TypeError):
                            val = None
                    values.append(val)

                placeholders = ", ".join(["?"] * len(col_names))
                col_list = ", ".join(col_names)
                insert_sql = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})"
                cursor = self.conn.execute(insert_sql, values)
                if cursor.rowcount > 0:
                    rows_inserted += 1
                else:
                    rows_ignored += 1
            except (sqlite3.Error, TypeError, ValueError) as e:
                rows_rejected += 1
                logging.debug("Row rejected for %s: %s", table, e)

        self.conn.commit()
        self.stats["rows_inserted"] += rows_inserted
        self.stats["rows_ignored"] += rows_ignored
        self.stats["rows_rejected"] += rows_rejected

        result = {
            "table": table,
            "rows_inserted": rows_inserted,
            "rows_ignored": rows_ignored,
            "rows_rejected": rows_rejected,
        }
        logging.info("Loaded %s: %d inserted, %d ignored, %d rejected",
                     table, rows_inserted, rows_ignored, rows_rejected)
        return result

    def _is_dirty_row(self, row: dict, pk_cols: list) -> bool:
        """Check if row should be rejected as dirty data."""
        # Check primary key completeness
        for col in pk_cols:
            val = row.get(col, "")
            if not val or val == "[DRY-RUN]" or val.startswith("["):
                return True

        # Check for dry-run markers in any field
        for val in row.values():
            if isinstance(val, str) and val.startswith("[DRY-RUN]"):
                return True

        # Check for obviously invalid data
        # (Extended in Phase04 with more sophisticated checks)

        return False

    def query(self, table: str, conditions: dict = None) -> list:
        """Query data from table with optional conditions."""
        if not self.conn:
            raise RuntimeError("Not connected. Call connect() first.")

        sql = f"SELECT * FROM {table}"
        params = []
        if conditions:
            where_clauses = []
            for col, val in conditions.items():
                where_clauses.append(f"{col} = ?")
                params.append(val)
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)

        cursor = self.conn.execute(sql, params)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows

    def get_table_stats(self, table: str) -> dict:
        """Get row count and basic stats for a table."""
        if not self.conn:
            raise RuntimeError("Not connected.")
        cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        return {"table": table, "row_count": count}

    def get_all_stats(self) -> dict:
        """Get statistics for all tables."""
        stats = {}
        for table_name in SCHEMAS:
            try:
                stats[table_name] = self.get_table_stats(table_name)
            except:
                stats[table_name] = {"table": table_name, "error": "not_created"}
        return stats

    def get_load_stats(self) -> dict:
        """Return load statistics."""
        return dict(self.stats)


# =============================================================================
# 2. Self-test
# =============================================================================
def selftest():
    """Run self-test of storage layer."""
    import tempfile

    print("=" * 60)
    print("Storage Layer Self-Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_factor_data.db"

        # Test 1: Database connection
        db = DatabaseInterface(str(db_path))
        db.connect()
        assert db.conn is not None, "Connection failed"
        print(f"1. Database connection: PASS")

        # Test 2: Create all tables
        db.create_all_tables()
        cursor = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        assert len(tables) == 6, f"Expected 6 tables, got {len(tables)}"
        print(f"2. Create all tables: PASS ({len(tables)} tables)")

        # Test 3: Load CSV with INSERT OR IGNORE (idempotency)
        csv_path = Path(tmpdir) / "test_kline.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "date", "s_code", "exch_code", "s_open", "s_high", "s_low",
                "s_close", "s_volume", "s_oi", "s_avg_price", "source_url", "update_time"
            ])
            writer.writeheader()
            writer.writerow({
                "date": "2026-10-17", "s_code": "Pb0", "exch_code": "SHFE",
                "s_open": "16500.0", "s_high": "16800.0", "s_low": "16400.0",
                "s_close": "16700.0", "s_volume": "10000", "s_oi": "50000",
                "s_avg_price": "16600.0", "source_url": "https://www.shfe.com.cn",
                "update_time": "20261017165031"
            })
        result1 = db.load_csv(str(csv_path), "daily_kline")
        assert result1["rows_inserted"] == 1, f"Expected 1 inserted, got {result1['rows_inserted']}"
        print(f"3. Load CSV insert: PASS")

        # Test 4: Idempotency (reload same data)
        result2 = db.load_csv(str(csv_path), "daily_kline")
        assert result2["rows_ignored"] == 1, f"Expected 1 ignored, got {result2['rows_ignored']}"
        print(f"4. Idempotency (INSERT OR IGNORE): PASS")

        # Test 5: Load records in-memory (new table: msteel_fundamental)
        records = [{
            "date": "2026-10-20", "ind_code": "MSTEEL_LEAD_TC",
            "ind_name": "铅冶炼加工费", "value": "1650", "unit": "元/吨",
            "source_url": "https://www.mysteel.com/news/20261020/1.html",
            "update_time": "20261020080000"
        }]
        result3 = db.load_records(records, "msteel_fundamental")
        assert result3["rows_inserted"] == 1, f"Expected 1 inserted, got {result3['rows_inserted']}"
        print(f"5. Load records (msteel_fundamental): PASS")

        # Test 6: Load records (customs_fundamental)
        records2 = [{
            "date": "2026-10-01", "ind_code": "CUSTOMS_LEAD_ORE_IMP",
            "ind_name": "铅矿砂进口量", "value": "15000", "unit": "吨",
            "source_url": "https://www.customs.gov.cn/test.xlsx",
            "update_time": "20261020080000"
        }]
        result4 = db.load_records(records2, "customs_fundamental")
        assert result4["rows_inserted"] == 1, f"Expected 1 inserted, got {result4['rows_inserted']}"
        print(f"6. Load records (customs_fundamental): PASS")

        # Test 7: Dirty data rejection
        dirty_records = [{
            "date": "[DRY-RUN]", "ind_code": "TEST",
            "ind_name": "Test", "value": "100", "unit": "吨",
            "source_url": "test", "update_time": "20261020"
        }]
        result5 = db.load_records(dirty_records, "industry_fundamental")
        assert result5["rows_rejected"] == 1, f"Expected 1 rejected, got {result5['rows_rejected']}"
        print(f"7. Dirty data rejection: PASS")

        # Test 8: Query data
        rows = db.query("daily_kline", {"s_code": "Pb0"})
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        print(f"8. Query with conditions: PASS")

        # Test 9: Get all stats
        all_stats = db.get_all_stats()
        assert len(all_stats) == 6, f"Expected 6 table stats, got {len(all_stats)}"
        print(f"9. Get all table stats: PASS")

        db.close()
        print(f"10. Database close: PASS")

    print("=" * 60)
    print("ALL 10 TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    selftest()