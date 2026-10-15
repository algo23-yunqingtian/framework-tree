#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_import_jsonl.py - V88 Phase03-P0 JSONL指标数据导入脚本

用途: 读取data/db_export下JSONL指标数据文件, 按命名映射表转换命名, 批量写入api_cache.db
前置: V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER / T2
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

用法:
    python db_import_jsonl.py [--dry-run] [--force] [--output /path/to/api_cache.db]

约束: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY
"""

import os
import sys
import json
import sqlite3
import argparse
import logging
from datetime import datetime
from pathlib import Path

# =============================================================================
# 配置
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent.parent  # 6 levels up: scripts→p0→phase03→v88→e2e_output→analysis→framework-tree

# JSONL数据文件路径
JSONL_DIR = REPO_ROOT / "data" / "db_export"
JSONL_FILES = [
    "series_ZN.jsonl",
    "series_NI.jsonl",
    "series_SI.jsonl",
    "series_SN.jsonl",
    "series_LI.jsonl",
]

# 默认数据库路径
DEFAULT_DB_PATH = REPO_ROOT / "scripts" / "api_cache.db"

# 批次大小
BATCH_SIZE = 1000

# =============================================================================
# 指标命名映射表 (DSHB indicator_id → DSHE meta_chart indicator_id)
# 来源: v88_phase03_p0_namespace_mapping_table.md
# =============================================================================

INDICATOR_MAPPING = {
    # ---- CU (铜) ----
    "cu_21_close_front": "CU_FU00014941",
    "cu_21_openinterest": "CU_HOLD_OPEN",
    "cu_21_openinterest_longshort": "CU_LONG_SHORT_RATIO",
    "cu_22_premium": "CU_SPOT_PREMIUM",
    "cu_21_basis": "CU_BASIS",
    "cu_23_lme_close": "LME_CU",
    "cu_23_comex_close": "COMEX_CU",
    "cu_24_openinterest_volume": "CU_MONTH_SPREAD",
    "cu_25_profit_percentile": "CU_PRICE_PERCENTILE",
    "cu_25_profit": "CU_SMELTING_PROFIT",
    "cu_26_openinterest_top20_front": "CU_TOP20_LONG",
    "cu_26_openinterest": "CU_TOP20_SHORT",
    "cu_41_output": "CU_FU00014935",
    "cu_23_inv": "FU00014813",
    "cu_42_warrant_reg": "CU_WARRANT_INVENTORY",
    "cu_43_social_stock": "CU_SOCIAL_INV",
    "cu_321_util_capacity_util": "CU_UTILIZATION",
    "cu_25_tc_conc": "CU_COST_PERCENTILE",

    # ---- AL (铝) ----
    "al_00_close_front": "AL_FU00014934",
    "al_00_openinterest_front": "AL_HOLD_OPEN",
    "al_00_premium": "AL_SPOT_PREMIUM",
    "al_00_basis": "AL_BASIS",
    "al_00_lme_close": "LME_AL",
    "al_24_lme_spread": "AL_MONTH_SPREAD",
    "al_00_cost_percentile": "AL_PRICE_PERCENTILE",
    "al_25_profit": "AL_SMELTING_PROFIT",
    "al_26_long_top20": "AL_TOP20_LONG",
    "al_26_short_top20": "AL_TOP20_SHORT",

    # ---- PB (铅) ----
    "j21_close": "PB_FU00014946",
    "j21_oi": "PB_HOLD_OPEN",
    "j22_spot": "PB_SPOT_PREMIUM",
    "j22_premium": "PB_BASIS",
    "j23_lme_cash": "LME_PB",
    "j24_spread_m": "PB_MONTH_SPREAD",
    "j24_spread_s": "PB_TERM_STRUCTURE",
    "j25_smelt_cost": "PB_SMELTING_PROFIT",

    # ---- ZN (锌) ----
    "zn_21_close_front": "ZN_FU00014950",
    "zn_21_openinterest": "ZN_HOLD_OPEN",
    "zn_21_openinterest_2": "ZN_LONG_SHORT_RATIO",
    "zn_21_premium": "ZN_SPOT_PREMIUM",
    "zn_21_basis": "ZN_BASIS",
    "zn_23_lme_close": "LME_ZN",
    "zn_23_comex": "COMEX_ZN",
    "zn_24_term_struct": "ZN_MONTH_SPREAD",
    "zn_25_profit_percentile": "ZN_PRICE_PERCENTILE",
    "zn_25_profit": "ZN_SMELTING_PROFIT",
    "zn_26_openinterest_top20": "ZN_TOP20_LONG",
    "zn_26_openinterest": "ZN_TOP20_SHORT",

    # ---- NI (镍) ----
    "ni_21_close_front": "NI_FU00014982",
    "ni_21_openinterest_front": "NI_HOLD_OPEN",
    "ni_21_percentile_openinterest": "NI_LONG_SHORT_RATIO",
    "ni_21_premium": "NI_SPOT_PREMIUM",
    "ni_22_basis": "NI_BASIS",
    "ni_21_lme_price": "LME_NI",
    "ni_24_near_price": "NI_MONTH_SPREAD",
    "ni_25_percentile_price": "NI_PRICE_PERCENTILE",
    "ni_25_profit": "NI_SMELTING_PROFIT",
    "ni_26_openinterest_top20_front": "NI_TOP20_LONG",
    "ni_26_openinterest_top20_front_2": "NI_TOP20_SHORT",

    # ---- SN (锡) ----
    "sn_21_close_front": "SN_FU00014952",
    "sn_21_openinterest": "SN_HOLD_OPEN",
    "sn_21_openinterest_3": "SN_LONG_SHORT_RATIO",
    "sn_21_premium": "SN_SPOT_PREMIUM",
    "sn_21_basis": "SN_BASIS",
    "sn_23_lme_close": "LME_SN",
    "sn_22_premium": "SN_MONTH_SPREAD",
    "sn_71_cost_percentile": "SN_PRICE_PERCENTILE",
    "sn_72_tc": "SN_SMELTING_PROFIT",
    "sn_26_openinterest_top20": "SN_TOP20_LONG",
    "sn_26_openinterest_top20_2": "SN_TOP20_SHORT",

    # ---- LI (锂/LC) ----
    "li_21_close_front": "LC_FU00015030",
    "li_21_openinterest": "LC_HOLD_OPEN",
    "li_21_openinterest_longshort": "LC_LONG_SHORT_RATIO",
    "li_21_premium": "LC_SPOT_PREMIUM",
    "li_21_basis": "LC_BASIS",
    "li_21_close": "LME_LC",
    "li_22_premium": "SPOT_LICAR",
    "li_24_close_near": "LC_MONTH_SPREAD",
    "li_25_profit": "LC_SMELTING_PROFIT",
    "li_26_openinterest_top20": "LC_TOP20_LONG",
    "li_26_openinterest_top20_2": "LC_TOP20_SHORT",

    # ---- SI (硅) ----
    "si_21_close_front_industrial_si": "SI_FU00015015",
    "si_21_openinterest": "SI_HOLD_OPEN",
    "si_21_openinterest_longshort_indus": "SI_LONG_SHORT_RATIO",
    "si_21_warrant_industrial_si": "SI_SPOT_PREMIUM",
    "si_21_basis_industrial_si": "SI_BASIS",
    "si_25_close_front_polysilicon": "LME_SI",
    "si_24_spot": "SPOT_IS",
    "si_23_close": "SI_MONTH_SPREAD",
    "si_25_profit_percentile_industrial": "SI_PRICE_PERCENTILE",
    "si_25_profit": "SI_SMELTING_PROFIT",
    "si_26_openinterest_top20": "SI_TOP20_LONG",
    "si_26_openinterest_top20_2": "SI_TOP20_SHORT",
}

# 品种映射 (commodity code → display name)
COMMODITY_MAP = {
    "cu": "铜", "al": "铝", "pb": "铅", "zn": "锌",
    "ni": "镍", "sn": "锡", "li": "锂", "si": "硅",
    "j": "铅(legacy)",
}


def extract_commodity(indicator_id):
    """从indicator_id提取品种代码"""
    if not indicator_id:
        return "unknown"
    parts = indicator_id.split("_")
    code = parts[0].lower()
    if code == "j":
        return "j"
    return code


def get_mapped_id(indicator_id):
    """获取DSHE映射指标名"""
    return INDICATOR_MAPPING.get(indicator_id, "")


def setup_database(db_path):
    """初始化数据库表结构"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_id TEXT NOT NULL,
            indicator_id_mapped TEXT,
            commodity TEXT NOT NULL,
            date TEXT NOT NULL,
            value REAL,
            source TEXT DEFAULT 'real',
            imported_at TEXT DEFAULT (datetime('now')),
            UNIQUE(indicator_id, date)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator ON series_cache(indicator_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator_mapped ON series_cache(indicator_id_mapped)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commodity ON series_cache(commodity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON series_cache(date)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_time TEXT DEFAULT (datetime('now')),
            source_file TEXT,
            rows_read INTEGER,
            rows_inserted INTEGER,
            rows_skipped INTEGER,
            rows_error INTEGER,
            mapping_applied INTEGER,
            notes TEXT
        )
    """)

    conn.commit()
    return conn


def read_jsonl_file(filepath):
    """读取JSONL文件, 返回记录列表"""
    records = []
    errors = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if "indicator_id" not in record or "date" not in record:
                    errors += 1
                    continue
                # 转换value为float
                try:
                    record["value"] = float(record.get("value", 0))
                except (ValueError, TypeError):
                    record["value"] = None
                records.append(record)
            except json.JSONDecodeError:
                errors += 1
    return records, errors


def import_records(conn, records, source_file, dry_run=False):
    """批量导入记录到数据库"""
    cursor = conn.cursor()
    batch = []
    rows_read = len(records)
    rows_inserted = 0
    rows_skipped = 0
    rows_error = 0
    mapping_applied = 0

    for record in records:
        indicator_id = record.get("indicator_id", "")
        date = record.get("date", "")
        value = record.get("value")
        commodity = extract_commodity(indicator_id)
        mapped_id = get_mapped_id(indicator_id)

        if mapped_id:
            mapping_applied += 1

        batch.append((indicator_id, mapped_id, commodity, date, value))

        if len(batch) >= BATCH_SIZE:
            if not dry_run:
                try:
                    cursor.executemany(
                        """INSERT OR IGNORE INTO series_cache
                           (indicator_id, indicator_id_mapped, commodity, date, value)
                           VALUES (?, ?, ?, ?, ?)""",
                        batch
                    )
                    conn.commit()
                    rows_inserted += cursor.rowcount
                except sqlite3.Error as e:
                    rows_error += len(batch)
                    logging.error(f"Insert batch error: {e}")
                    conn.rollback()
            else:
                rows_inserted += len(batch)
            rows_skipped = rows_read - rows_inserted - rows_error
            batch = []

    # 处理剩余批次
    if batch:
        if not dry_run:
            try:
                cursor.executemany(
                    """INSERT OR IGNORE INTO series_cache
                       (indicator_id, indicator_id_mapped, commodity, date, value)
                       VALUES (?, ?, ?, ?, ?)""",
                    batch
                )
                conn.commit()
                rows_inserted += cursor.rowcount
            except sqlite3.Error as e:
                rows_error += len(batch)
                logging.error(f"Insert batch error: {e}")
                conn.rollback()
        else:
            rows_inserted += len(batch)
        rows_skipped = rows_read - rows_inserted - rows_error

    return rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied


def log_import(conn, source_file, rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied, notes=""):
    """记录导入日志"""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO import_log
           (import_time, source_file, rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().isoformat(), source_file, rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied, notes)
    )
    conn.commit()


def print_summary(total_read, total_inserted, total_skipped, total_error, total_mapped, dry_run):
    """打印导入摘要"""
    print("\n" + "=" * 60)
    print("  V88 Phase03-P0 JSONL Import Summary")
    print("=" * 60)
    if dry_run:
        print("  [DRY RUN] No data was written to database")
    print(f"  Rows read:     {total_read}")
    print(f"  Rows inserted: {total_inserted}")
    print(f"  Rows skipped:  {total_skipped}")
    print(f"  Rows error:    {total_error}")
    print(f"  Mapping applied: {total_mapped}")
    if total_read > 0:
        print(f"  Insert rate:   {total_inserted/total_read*100:.1f}%")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="V88 Phase03-P0 JSONL Import Script")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode - no data written")
    parser.add_argument("--force", action="store_true", help="Force re-import (clear existing data first)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_DB_PATH), help="Output database path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    db_path = Path(args.output)
    logging.info(f"Database path: {db_path}")
    logging.info(f"JSONL directory: {JSONL_DIR}")

    # 验证JSONL文件
    jsonl_paths = []
    for fname in JSONL_FILES:
        fpath = JSONL_DIR / fname
        if fpath.exists():
            jsonl_paths.append(fpath)
            logging.info(f"  Found: {fname} ({fpath.stat().st_size:,} bytes)")
        else:
            logging.warning(f"  MISSING: {fname}")

    if not jsonl_paths:
        logging.error("No JSONL files found!")
        sys.exit(1)

    # 初始化数据库
    conn = setup_database(db_path)
    cursor = conn.cursor()

    # Force mode: 清除现有数据
    if args.force and not args.dry_run:
        logging.info("Force mode: clearing existing series_cache data...")
        cursor.execute("DELETE FROM series_cache")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='series_cache'")
        conn.commit()
        logging.info("Existing data cleared.")

    # 导入每个JSONL文件
    total_read = total_inserted = total_skipped = total_error = total_mapped = 0

    for fpath in jsonl_paths:
        logging.info(f"Reading: {fpath.name}")
        records, read_errors = read_jsonl_file(fpath)
        if read_errors > 0:
            logging.warning(f"  {read_errors} read errors in {fpath.name}")

        logging.info(f"  Records read: {len(records):,}")
        rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied = import_records(
            conn, records, fpath.name, dry_run=args.dry_run
        )

        if not args.dry_run:
            log_import(conn, fpath.name, rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied)

        total_read += rows_read
        total_inserted += rows_inserted
        total_skipped += rows_skipped
        total_error += rows_error
        total_mapped += mapping_applied

        logging.info(f"  Inserted: {rows_inserted:,} | Skipped: {rows_skipped:,} | Error: {rows_error:,} | Mapped: {mapping_applied:,}")

    # 打印摘要
    print_summary(total_read, total_inserted, total_skipped, total_error, total_mapped, args.dry_run)

    # 验证导入结果
    if not args.dry_run:
        cursor.execute("SELECT COUNT(*) FROM series_cache")
        db_count = cursor.fetchone()[0]
        logging.info(f"Database total rows after import: {db_count:,}")

        cursor.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
        indicator_count = cursor.fetchone()[0]
        logging.info(f"Unique indicators in database: {indicator_count}")

        cursor.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped != ''")
        mapped_count = cursor.fetchone()[0]
        logging.info(f"Unique mapped indicators: {mapped_count}")

        cursor.execute("SELECT commodity, COUNT(*) as cnt FROM series_cache GROUP BY commodity ORDER BY commodity")
        print("\n  Per-commodity distribution:")
        for row in cursor.fetchall():
            print(f"    {row[0]}: {row[1]:,} rows")

    conn.close()
    logging.info("Import complete.")


if __name__ == "__main__":
    main()
