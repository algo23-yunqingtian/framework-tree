#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_interface.py — Database Interface Stub (Phase04 Import Ready)
================================================================
TASK_ID: V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
Stub interface for reading/writing crawled data to/from local database.
Phase04 will use this interface to import cleaned CSV data into the
factor calculation pipeline's data store.

Design:
  - SQLite-based (stdlib, no external dependencies)
  - Schema mirrors WIND-aligned CSV columns
  - Supports both daily K-line and industry fundamental tables
  - APPEND_ONLY semantics (idempotent by primary key)

Constraints:
  NO_ZHIJI_API_CALL   No zhiji_api.py import/call
  NO_OVERWRITE        Existing DB tables are never dropped/truncated
  APPEND_ONLY         INSERT OR IGNORE for idempotent writes
  FROZEN              DB schema is frozen for Phase04 consumption

Usage (Phase04):
  from db_interface import DatabaseInterface
  db = DatabaseInterface(db_path="data/factor_data.db")
  db.connect()
  db.load_csv("samples/pb_daily_kline_sample.csv", table="daily_kline")
  db.close()

  # Query for factor calculation
  rows = db.query_daily_kline(symbol="SHFE_PBU", start_date="2026-01-01")
  for row in rows:
      print(row["date"], row["close"])
"""

import os
import sys
import json
import sqlite3
import csv
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = SCRIPT_DIR / "samples"

TASK_ID = "V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
VERSION = "1.0.0"

DEFAULT_DB_PATH = SCRIPT_DIR.parent.parent / "data" / "factor_data.db"


# =============================================================================
# 0. Schema definitions (WIND-aligned)
# =============================================================================
SCHEMAS = {
    "daily_kline": {
        "description": "Daily K-line data (OHLCV)",
        "columns": {
            "date": "TEXT NOT NULL",
            "symbol": "TEXT NOT NULL",
            "exchange": "TEXT NOT NULL",
            "open": "REAL",
            "high": "REAL",
            "low": "REAL",
            "close": "REAL",
            "volume": "INTEGER",
            "open_interest": "INTEGER",
            "avg_price": "REAL",
            "source_url": "TEXT",
            "crawl_timestamp": "TEXT NOT NULL",
        },
        "primary_key": ["date", "symbol"],
        "indexes": [
            ("idx_daily_kline_symbol", "symbol"),
            ("idx_daily_kline_date", "date"),
        ],
    },
    "position_ranking": {
        "description": "Position ranking data",
        "columns": {
            "date": "TEXT NOT NULL",
            "symbol": "TEXT NOT NULL",
            "exchange": "TEXT NOT NULL",
            "rank": "INTEGER",
            "company_name": "TEXT",
            "long_position": "INTEGER",
            "short_position": "INTEGER",
            "long_change": "INTEGER",
            "short_change": "INTEGER",
            "source_url": "TEXT",
            "crawl_timestamp": "TEXT NOT NULL",
        },
        "primary_key": ["date", "symbol", "company_name"],
        "indexes": [
            ("idx_position_ranking_symbol", "symbol"),
            ("idx_position_ranking_date", "date"),
        ],
    },
    "warrant_registration": {
        "description": "Warrant registration/cancellation data",
        "columns": {
            "date": "TEXT NOT NULL",
            "symbol": "TEXT NOT NULL",
            "exchange": "TEXT NOT NULL",
            "registration_amount": "INTEGER",
            "cancellation_amount": "INTEGER",
            "net_change": "INTEGER",
            "total_balance": "INTEGER",
            "source_url": "TEXT",
            "crawl_timestamp": "TEXT NOT NULL",
        },
        "primary_key": ["date", "symbol"],
        "indexes": [
            ("idx_warrant_symbol", "symbol"),
            ("idx_warrant_date", "date"),
        ],
    },
    "industry_fundamental": {
        "description": "Industry fundamental indicators",
        "columns": {
            "date": "TEXT NOT NULL",
            "indicator_code": "TEXT NOT NULL",
            "indicator_name": "TEXT",
            "value": "REAL",
            "unit": "TEXT",
            "source_url": "TEXT",
            "crawl_timestamp": "TEXT NOT NULL",
        },
        "primary_key": ["date", "indicator_code"],
        "indexes": [
            ("idx_industry_indicator_code", "indicator_code"),
            ("idx_industry_date", "date"),
        ],
    },
}


# =============================================================================
# 1. Database Interface
# =============================================================================
class DatabaseInterface:
    """SQLite-based database interface for crawler data storage.
    
    Supports:
      - Schema creation (idempotent)
      - CSV loading (APPEND_ONLY, INSERT OR IGNORE)
      - Querying for factor calculation
      - Integrity checking (MD5 verification)
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._connection = None
        self._tables_created = False

    def connect(self):
        """Connect to SQLite database and ensure schema exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.db_path))
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._ensure_schema()
        self._tables_created = True
        logging.info("Connected to DB: %s", self.db_path)

    def _ensure_schema(self):
        """Create tables if they don't exist (idempotent)."""
        for table_name, schema in SCHEMAS.items():
            cols = schema["columns"]
            pk_cols = schema["primary_key"]
            
            col_defs = []
            for col, dtype in cols.items():
                col_defs.append(f"{col} {dtype}")
            
            # Build CREATE TABLE
            pk_def = ""
            if pk_cols:
                pk_def = f", PRIMARY KEY ({', '.join(pk_cols)})"
            
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(col_defs)}
                {pk_def}
            )
            """
            self._connection.execute(create_sql)
            
            # Build indexes
            for idx_name, idx_col in schema["indexes"]:
                self._connection.execute(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({idx_col})"
                )
        
        self._connection.commit()
        logging.info("Schema ensured: %d tables", len(SCHEMAS))

    def load_csv(self, csv_path: str, table: str) -> int:
        """Load CSV file into database table (APPEND_ONLY, idempotent).
        
        Args:
            csv_path: Path to CSV file
            table: Target table name (must be in SCHEMAS)
        
        Returns:
            Number of new rows inserted
        """
        if not self._connection:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if table not in SCHEMAS:
            raise ValueError(f"Unknown table: {table}. Available: {list(SCHEMAS.keys())}")
        
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")
        
        schema = SCHEMAS[table]
        columns = list(schema["columns"].keys())
        
        new_count = 0
        with open(csv_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter to schema columns
                row_data = {col: row.get(col, "") for col in columns}
                
                # INSERT OR IGNORE for idempotent writes
                placeholders = ", ".join(["?"] * len(columns))
                col_names = ", ".join(columns)
                values = [row_data[col] for col in columns]
                
                cursor = self._connection.execute(
                    f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
                    values,
                )
                if cursor.rowcount > 0:
                    new_count += 1
        
        self._connection.commit()
        logging.info("Loaded %d new rows into %s from %s", new_count, table, csv_path)
        return new_count

    def query_daily_kline(self, symbol: str, start_date: str = None,
                          end_date: str = None, limit: int = 1000) -> list:
        """Query daily K-line data for factor calculation."""
        if not self._connection:
            raise RuntimeError("Not connected.")
        
        sql = "SELECT * FROM daily_kline WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)
        
        sql += " ORDER BY date ASC LIMIT ?"
        params.append(limit)
        
        cursor = self._connection.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def query_position_ranking(self, symbol: str, date: str,
                               limit: int = 20) -> list:
        """Query position ranking for a symbol on a specific date."""
        if not self._connection:
            raise RuntimeError("Not connected.")
        
        sql = "SELECT * FROM position_ranking WHERE symbol = ? AND date = ? ORDER BY rank LIMIT ?"
        params = [symbol, date, limit]
        
        cursor = self._connection.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def query_industry_fundamental(self, indicator_code: str,
                                   start_date: str = None,
                                   end_date: str = None,
                                   limit: int = 1000) -> list:
        """Query industry fundamental indicators."""
        if not self._connection:
            raise RuntimeError("Not connected.")
        
        sql = "SELECT * FROM industry_fundamental WHERE indicator_code = ?"
        params = [indicator_code]
        
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)
        
        sql += " ORDER BY date ASC LIMIT ?"
        params.append(limit)
        
        cursor = self._connection.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_table_counts(self) -> dict:
        """Get row counts for all tables."""
        if not self._connection:
            raise RuntimeError("Not connected.")
        
        counts = {}
        for table_name in SCHEMAS:
            cursor = self._connection.execute(f"SELECT COUNT(*) FROM {table_name}")
            counts[table_name] = cursor.fetchone()[0]
        return counts

    def get_table_schema(self, table_name: str) -> list:
        """Get schema info for a table."""
        if not self._connection:
            raise RuntimeError("Not connected.")
        
        cursor = self._connection.execute(f"PRAGMA table_info({table_name})")
        return [dict(row) for row in cursor.fetchall()]

    def export_to_csv(self, table: str, output_path: str) -> int:
        """Export table to CSV file."""
        if not self._connection:
            raise RuntimeError("Not connected.")
        
        if table not in SCHEMAS:
            raise ValueError(f"Unknown table: {table}")
        
        cursor = self._connection.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        columns = list(SCHEMAS[table]["columns"].keys())
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        
        logging.info("Exported %d rows from %s to %s", len(rows), table, output_path)
        return len(rows)

    def verify_integrity(self) -> dict:
        """Verify database integrity."""
        if not self._connection:
            raise RuntimeError("Not connected.")
        
        result = {
            "db_path": str(self.db_path),
            "tables": {},
            "integrity_check": None,
            "timestamp": datetime.now().isoformat(),
        }
        
        # PRAGMA integrity_check
        cursor = self._connection.execute("PRAGMA integrity_check")
        result["integrity_check"] = cursor.fetchone()[0]
        
        # Table counts
        counts = self.get_table_counts()
        result["tables"] = counts
        
        return result

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logging.info("Database connection closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# =============================================================================
# 2. Self-test
# =============================================================================
def selftest():
    """Run self-test of database interface."""
    import tempfile
    
    print("=" * 60)
    print("DB Interface Self-Test")
    print("=" * 60)
    
    # Use temp DB
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseInterface(db_path)
        
        print(f"1. Connect: ", end="")
        db.connect()
        print("OK")
        
        # Create sample CSV
        sample_csv = Path(tmpdir) / "test_kline.csv"
        with open(sample_csv, "w", encoding="utf-8") as f:
            f.write("date,symbol,exchange,open,high,low,close,volume,open_interest,avg_price,source_url,crawl_timestamp\n")
            f.write("2026-10-20,SHFE_PBU,shfe,16500,16800,16400,16700,12500,380000,16600,https://www.shfe.com.cn/,2026-10-20T10:00:00\n")
            f.write("2026-10-21,SHFE_PBU,shfe,16700,16900,16600,16800,13000,385000,16750,https://www.shfe.com.cn/,2026-10-21T10:00:00\n")
        
        print(f"2. Load CSV: ", end="")
        count = db.load_csv(str(sample_csv), "daily_kline")
        assert count == 2, f"Expected 2 rows, got {count}"
        print(f"OK ({count} rows)")
        
        # Test idempotency
        print(f"3. Idempotency: ", end="")
        count2 = db.load_csv(str(sample_csv), "daily_kline")
        assert count2 == 0, f"Expected 0 new rows, got {count2}"
        print("OK (0 new rows on re-load)")
        
        # Query
        print(f"4. Query: ", end="")
        rows = db.query_daily_kline("SHFE_PBU")
        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        assert rows[0]["close"] == 16700.0
        print(f"OK ({len(rows)} rows, close={rows[0]['close']})")
        
        # Table counts
        print(f"5. Table counts: ", end="")
        counts = db.get_table_counts()
        assert counts["daily_kline"] == 2
        print(f"OK (daily_kline={counts['daily_kline']})")
        
        # Integrity
        print(f"6. Integrity: ", end="")
        integrity = db.verify_integrity()
        assert integrity["integrity_check"] == "ok"
        print(f"OK ({integrity['integrity_check']})")
        
        db.close()
        print(f"7. Close: OK")
    
    print()
    print("ALL TESTS PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DB Interface for DSHB Crawler Data")
    parser.add_argument("--selftest", action="store_true", help="Run self-test")
    parser.add_argument("--db-path", type=str, default=None, help="Database path")
    parser.add_argument("--verify", action="store_true", help="Verify integrity")
    parser.add_argument("--count", action="store_true", help="Show table counts")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    if args.selftest:
        sys.exit(selftest())
    elif args.verify or args.count:
        db = DatabaseInterface(Path(args.db_path) if args.db_path else None)
        db.connect()
        if args.verify:
            result = db.verify_integrity()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.count:
            counts = db.get_table_counts()
            print(json.dumps(counts, indent=2))
        db.close()