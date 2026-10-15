#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_load.py - V88 Phase03-P0 缓存数据库查询工具

用途: 为DSHE渲染层提供api_cache.db查询接口, 支持按原始指标名或DSHE图表指标名查询时序数据
前置: V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER / T2
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

用法:
    python db_load.py list                              # 列出所有指标
    python db_load.py info <indicator_id>              # 查看指标信息
    python db_load.py query <indicator_id> [--start DATE] [--end DATE]  # 查询时序
    python db_load.py query --mapped <meta_chart_id>   # 按DSHE图表指标名查询
    python db_load.py stats                            # 查看导入统计

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
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent.parent

DEFAULT_DB_PATH = REPO_ROOT / "scripts" / "api_cache.db"


# =============================================================================
# 数据库操作
# =============================================================================

def get_connection(db_path=None):
    """获取数据库连接"""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    if not os.path.exists(str(db_path)):
        return None
    return sqlite3.connect(str(db_path))


def table_exists(conn, table_name):
    """检查表是否存在"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def get_series(indicator_id, start_date=None, end_date=None, db_path=None):
    """获取单个指标的时间序列数据"""
    conn = get_connection(db_path)
    if conn is None:
        return []
    if not table_exists(conn, "series_cache"):
        conn.close()
        return []

    cursor = conn.cursor()
    query = "SELECT date, value, source FROM series_cache WHERE indicator_id = ?"
    params = [indicator_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [{"date": r[0], "value": r[1], "source": r[2]} for r in rows]


def get_series_mapped(meta_chart_id, start_date=None, end_date=None, db_path=None):
    """按DSHE图表指标名查询时序数据"""
    conn = get_connection(db_path)
    if conn is None:
        return []
    if not table_exists(conn, "series_cache"):
        conn.close()
        return []

    cursor = conn.cursor()
    query = "SELECT date, value, source FROM series_cache WHERE indicator_id_mapped = ?"
    params = [meta_chart_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [{"date": r[0], "value": r[1], "source": r[2]} for r in rows]


def get_all_indicators(db_path=None):
    """列出所有唯一的指标"""
    conn = get_connection(db_path)
    if conn is None:
        return []
    if not table_exists(conn, "series_cache"):
        conn.close()
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT indicator_id, indicator_id_mapped, commodity, 
               COUNT(*) as record_count,
               MIN(date) as date_start,
               MAX(date) as date_end,
               SUM(CASE WHEN source = 'real' THEN 1 ELSE 0 END) as real_count
        FROM series_cache
        GROUP BY indicator_id
        ORDER BY commodity, indicator_id
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "indicator_id": r[0],
            "indicator_id_mapped": r[1] or "",
            "commodity": r[2],
            "record_count": r[3],
            "date_range": f"{r[4]} ~ {r[5]}",
            "real_count": r[6],
        }
        for r in rows
    ]


def get_indicator_info(indicator_id, db_path=None):
    """获取单个指标的元信息"""
    conn = get_connection(db_path)
    if conn is None:
        return None
    if not table_exists(conn, "series_cache"):
        conn.close()
        return None

    cursor = conn.cursor()
    cursor.execute("""
        SELECT indicator_id, indicator_id_mapped, commodity,
               COUNT(*) as record_count,
               MIN(date) as date_start,
               MAX(date) as date_end,
               SUM(CASE WHEN source = 'real' THEN 1 ELSE 0 END) as real_count,
               SUM(CASE WHEN source = 'simulated' THEN 1 ELSE 0 END) as sim_count
        FROM series_cache
        WHERE indicator_id = ?
        GROUP BY indicator_id
    """, (indicator_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "indicator_id": row[0],
        "indicator_id_mapped": row[1] or "",
        "commodity": row[2],
        "record_count": row[3],
        "date_start": row[4],
        "date_end": row[5],
        "real_count": row[6],
        "simulated_count": row[7],
    }


def get_source_counts(db_path=None):
    """获取source类型分布"""
    conn = get_connection(db_path)
    if conn is None:
        return {}
    if not table_exists(conn, "series_cache"):
        conn.close()
        return {}

    cursor = conn.cursor()
    cursor.execute("SELECT source, COUNT(*) FROM series_cache GROUP BY source")
    rows = cursor.fetchall()
    conn.close()

    return {r[0]: r[1] for r in rows}


def get_import_stats(db_path=None):
    """获取导入日志统计"""
    conn = get_connection(db_path)
    if conn is None:
        return []
    if not table_exists(conn, "import_log"):
        conn.close()
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT import_time, source_file, rows_read, rows_inserted, 
               rows_skipped, rows_error, mapping_applied
        FROM import_log
        ORDER BY import_time DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "import_time": r[0],
            "source_file": r[1],
            "rows_read": r[2],
            "rows_inserted": r[3],
            "rows_skipped": r[4],
            "rows_error": r[5],
            "mapping_applied": r[6],
        }
        for r in rows
    ]


# =============================================================================
# CLI接口
# =============================================================================

def cli_list(db_path=None):
    """CLI: 列出所有指标"""
    indicators = get_all_indicators(db_path)
    if not indicators:
        print("No indicators found in database.")
        return

    print(f"\n{'='*80}")
    print(f"  V88 Phase03-P0 Cache Indicators ({len(indicators)} total)")
    print(f"{'='*80}")
    print(f"  {'Indicator ID':<40} {'Mapped ID':<25} {'Commodity':<10} {'Records':>8} {'Real':>6}")
    print(f"  {'-'*40} {'-'*25} {'-'*10} {'-'*8} {'-'*6}")
    for ind in indicators:
        print(f"  {ind['indicator_id']:<40} {ind['indicator_id_mapped']:<25} {ind['commodity']:<10} {ind['record_count']:>8,} {ind['real_count']:>6,}")
    print(f"{'='*80}")


def cli_info(indicator_id, db_path=None):
    """CLI: 查看指标信息"""
    info = get_indicator_info(indicator_id, db_path)
    if info is None:
        print(f"Indicator '{indicator_id}' not found in database.")
        return

    print(f"\n{'='*60}")
    print(f"  Indicator Info: {indicator_id}")
    print(f"{'='*60}")
    for k, v in info.items():
        print(f"  {k:<20}: {v}")
    print(f"{'='*60}")


def cli_query(indicator_id, mapped=None, start=None, end=None, db_path=None):
    """CLI: 查询时序数据"""
    if mapped:
        data = get_series_mapped(mapped, start, end, db_path)
        print(f"\nQuerying by mapped ID: {mapped}")
    else:
        data = get_series(indicator_id, start, end, db_path)
        print(f"\nQuerying by indicator ID: {indicator_id}")

    if not data:
        print("  No data found.")
        return

    print(f"  {'Date':<15} {'Value':>15} {'Source':<10}")
    print(f"  {'-'*15} {'-'*15} {'-'*10}")
    for d in data[:50]:  # Limit to 50 rows
        print(f"  {d['date']:<15} {str(d['value']):>15} {d['source']:<10}")

    if len(data) > 50:
        print(f"  ... ({len(data) - 50} more rows)")
    print(f"  Total: {len(data)} rows")


def cli_stats(db_path=None):
    """CLI: 显示导入统计"""
    print(f"\n{'='*60}")
    print(f"  V88 Phase03-P0 Import Statistics")
    print(f"{'='*60}")

    conn = get_connection(db_path)
    if conn is None:
        print("  Database not found.")
        return

    if table_exists(conn, "series_cache"):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM series_cache")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
        unique_ind = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped != ''")
        mapped_ind = cursor.fetchone()[0]
        cursor.execute("SELECT MIN(date), MAX(date) FROM series_cache")
        date_range = cursor.fetchone()
        print(f"  Total records:    {total:,}")
        print(f"  Unique indicators: {unique_ind}")
        print(f"  Mapped indicators: {mapped_ind}")
        print(f"  Date range:       {date_range[0]} ~ {date_range[1]}")

    if table_exists(conn, "import_log"):
        print(f"\n  {'='*40}")
        print(f"  Import Log:")
        print(f"  {'='*40}")
        stats = get_import_stats(db_path)
        for s in stats[:10]:
            print(f"  [{s['import_time'][:19]}] {s['source_file']}: read={s['rows_read']:,} ins={s['rows_inserted']:,} skip={s['rows_skipped']:,} err={s['rows_error']:,} mapped={s['mapping_applied']:,}")

    conn.close()
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="V88 Phase03-P0 Cache DB Query Tool")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Database path")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list command
    subparsers.add_parser("list", help="List all indicators")

    # info command
    info_parser = subparsers.add_parser("info", help="Show indicator info")
    info_parser.add_argument("indicator_id", type=str, help="Indicator ID")

    # query command
    query_parser = subparsers.add_parser("query", help="Query time series")
    query_parser.add_argument("indicator_id", type=str, nargs="?", help="Indicator ID")
    query_parser.add_argument("--mapped", type=str, help="Query by DSHE meta_chart indicator ID")
    query_parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    query_parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")

    # stats command
    subparsers.add_parser("stats", help="Show import statistics")

    args = parser.parse_args()
    db_path = args.db

    if args.command == "list":
        cli_list(db_path)
    elif args.command == "info":
        cli_info(args.indicator_id, db_path)
    elif args.command == "query":
        if args.mapped:
            cli_query(None, mapped=args.mapped, start=args.start, end=args.end, db_path=db_path)
        elif args.indicator_id:
            cli_query(args.indicator_id, start=args.start, end=args.end, db_path=db_path)
        else:
            parser.error("Specify indicator_id or --mapped")
    elif args.command == "stats":
        cli_stats(db_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
