#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_load.py - V88 Phase03-P0 缓存数据库查询工具
================================================================
TASK_ID: V88_PHASE03_P0_R0_NAMESPACE_MAPPING_AND_CACHE_IMPORTER
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

用途:
  为 DSHE 渲染层提供 api_cache.db 查询接口,
  支持按原始指标名或 DSHE 图表指标名查询时序数据。

用法:
  python db_load.py list                              # 列出所有指标
  python db_load.py info <indicator_id>              # 查看指标信息
  python db_load.py query <indicator_id> [--start DATE] [--end DATE]  # 查询时序
  python db_load.py query --mapped <meta_chart_id>   # 按 DSHE 图表指标名查询
  python db_load.py stats                            # 查看导入统计
  python db_load.py --help                           # 完整帮助

约束:
  · 仅使用 Python 标准库 (sqlite3/json/os/sys/datetime/argparse/pathlib/logging)
  · 不修改仓库任何已有文件
  · 全 UTF-8 编码
  · BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY
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

TABLE_SERIES_CACHE = "series_cache"
TABLE_IMPORT_LOG = "import_log"


# =============================================================================
# 数据库连接管理
# =============================================================================

def get_connection(db_path=None):
    """
    获取数据库连接。
    返回连接对象, 数据库不存在或表不存在时返回 None。
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    db_path = Path(db_path)
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # 允许列名访问

    # 检查 series_cache 表是否存在
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (TABLE_SERIES_CACHE,)
    )
    if cursor.fetchone() is None:
        conn.close()
        return None

    return conn


# =============================================================================
# 查询函数 (核心 API)
# =============================================================================

def get_series(indicator_id, start_date=None, end_date=None, db_path=None):
    """
    获取单个指标的时序数据。

    参数:
        indicator_id: DSHB 原始指标 ID (如 "zn_21_close_front")
        start_date: 开始日期 (YYYY-MM-DD), 可选
        end_date: 结束日期 (YYYY-MM-DD), 可选
        db_path: 数据库路径, 可选

    返回:
        list[dict]: [{"date": str, "value": float, "source": str}, ...]
        按日期倒序排列 (最新在前)
    """
    conn = get_connection(db_path)
    if conn is None:
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
    """
    按 DSHE 图表指标名查询时序数据。

    参数:
        meta_chart_id: DSHE meta_chart 指标 ID (如 "ZN_FU00014950")
        start_date: 开始日期 (YYYY-MM-DD), 可选
        end_date: 结束日期 (YYYY-MM-DD), 可选
        db_path: 数据库路径, 可选

    返回:
        list[dict]: [{"date": str, "value": float, "source": str}, ...]
        按日期倒序排列 (最新在前)
    """
    conn = get_connection(db_path)
    if conn is None:
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
    """
    列出所有唯一指标及其元信息。

    返回:
        list[dict]: [{"indicator_id": str, "indicator_id_mapped": str,
                       "commodity": str, "record_count": int,
                       "date_range": str, "real_count": int}, ...]
    """
    conn = get_connection(db_path)
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT indicator_id,
               COALESCE(indicator_id_mapped, '') AS indicator_id_mapped,
               commodity,
               COUNT(*) AS record_count,
               MIN(date) AS date_start,
               MAX(date) AS date_end,
               SUM(CASE WHEN source = 'real' THEN 1 ELSE 0 END) AS real_count
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
    """
    获取单个指标的元信息。

    参数:
        indicator_id: 指标 ID
        db_path: 数据库路径, 可选

    返回:
        dict 或 None: {"indicator_id", "indicator_id_mapped", "commodity",
                       "record_count", "date_start", "date_end",
                       "real_count", "simulated_count"}
    """
    conn = get_connection(db_path)
    if conn is None:
        return None

    cursor = conn.cursor()
    cursor.execute("""
        SELECT indicator_id,
               COALESCE(indicator_id_mapped, '') AS indicator_id_mapped,
               commodity,
               COUNT(*) AS record_count,
               MIN(date) AS date_start,
               MAX(date) AS date_end,
               SUM(CASE WHEN source = 'real' THEN 1 ELSE 0 END) AS real_count,
               SUM(CASE WHEN source = 'simulated' THEN 1 ELSE 0 END) AS sim_count
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
    """
    获取 source 类型分布 (real vs simulated 等)。

    返回:
        dict: {"real": int, "simulated": int, ...}
    """
    conn = get_connection(db_path)
    if conn is None:
        return {}

    cursor = conn.cursor()
    cursor.execute(
        "SELECT source, COUNT(*) FROM series_cache GROUP BY source ORDER BY COUNT(*) DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return {r[0]: r[1] for r in rows}


def get_commodity_counts(db_path=None):
    """
    获取按品种分布的统计。

    返回:
        dict: {"zn": int, "ni": int, ...}
    """
    conn = get_connection(db_path)
    if conn is None:
        return {}

    cursor = conn.cursor()
    cursor.execute(
        "SELECT commodity, COUNT(*) FROM series_cache GROUP BY commodity ORDER BY COUNT(*) DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return {r[0]: r[1] for r in rows}


def get_import_stats(db_path=None):
    """
    获取导入日志统计。

    返回:
        list[dict]: [{"import_time", "source_file", "rows_read",
                       "rows_inserted", "rows_skipped", "rows_error",
                       "mapping_applied"}, ...]
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 检查 import_log 表是否存在
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (TABLE_IMPORT_LOG,)
    )
    if cursor.fetchone() is None:
        conn.close()
        return []

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


def get_overall_stats(db_path=None):
    """
    获取整体数据库统计。

    返回:
        dict: {"total_records", "unique_indicators", "mapped_indicators",
               "date_range", "source_counts", "commodity_counts"}
    """
    conn = get_connection(db_path)
    if conn is None:
        return {}

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM series_cache")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    unique_ind = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache "
        "WHERE indicator_id_mapped IS NOT NULL"
    )
    mapped_ind = cursor.fetchone()[0]
    cursor.execute("SELECT MIN(date), MAX(date) FROM series_cache")
    date_range = cursor.fetchone()

    source_counts = get_source_counts(db_path)
    commodity_counts = get_commodity_counts(db_path)

    conn.close()

    return {
        "total_records": total,
        "unique_indicators": unique_ind,
        "mapped_indicators": mapped_ind,
        "date_range": f"{date_range[0]} ~ {date_range[1]}" if date_range else "N/A",
        "source_counts": source_counts,
        "commodity_counts": commodity_counts,
    }


# =============================================================================
# CLI 接口
# =============================================================================

def cli_list(db_path=None):
    """CLI: 列出所有指标"""
    indicators = get_all_indicators(db_path)
    if not indicators:
        print("No indicators found in database.")
        return

    print(f"\n{'='*90}")
    print(f"  V88 Phase03-P0 Cache Indicators ({len(indicators)} total)")
    print(f"{'='*90}")
    print(f"  {'Indicator ID':<42} {'Mapped ID':<25} {'Comm':<5} {'Count':>6} {'Real':>6}")
    print(f"  {'-'*42} {'-'*25} {'-'*5} {'-'*6} {'-'*6}")
    for ind in indicators:
        print(f"  {ind['indicator_id']:<42} {ind['indicator_id_mapped']:<25} {ind['commodity']:<5} {ind['record_count']:>6,} {ind['real_count']:>6,}")
    print(f"{'='*90}")
    print(f"  Date range: {indicators[0]['date_range'] if indicators else 'N/A'}")


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


def cli_query(indicator_id, mapped=None, start=None, end=None, limit=50, db_path=None):
    """CLI: 查询时序数据"""
    if mapped:
        data = get_series_mapped(mapped, start, end, db_path)
        print(f"\nQuerying by mapped ID: {mapped}")
    elif indicator_id:
        data = get_series(indicator_id, start, end, db_path)
        print(f"\nQuerying by indicator ID: {indicator_id}")
    else:
        print("Error: specify indicator_id or --mapped")
        return

    if not data:
        print("  No data found.")
        return

    print(f"  {'Date':<15} {'Value':>15} {'Source':<10}")
    print(f"  {'-'*15} {'-'*15} {'-'*10}")
    for d in data[:limit]:
        val_str = f"{d['value']:.2f}" if d['value'] is not None else "NULL"
        print(f"  {d['date']:<15} {val_str:>15} {d['source']:<10}")

    if len(data) > limit:
        print(f"  ... ({len(data) - limit} more rows)")
    print(f"  Total: {len(data)} rows")


def cli_stats(db_path=None):
    """CLI: 显示导入统计"""
    print(f"\n{'='*60}")
    print(f"  V88 Phase03-P0 Import Statistics")
    print(f"{'='*60}")

    # 整体统计
    stats = get_overall_stats(db_path)
    if stats:
        print(f"  Total records:    {stats['total_records']:,}")
        print(f"  Unique indicators: {stats['unique_indicators']:,}")
        print(f"  Mapped indicators: {stats['mapped_indicators']:,}")
        print(f"  Date range:       {stats['date_range']}")

        if stats["commodity_counts"]:
            print(f"\n  Per-commodity:")
            for comm, cnt in stats["commodity_counts"].items():
                print(f"    {comm}: {cnt:,} rows")

        if stats["source_counts"]:
            print(f"\n  Per-source:")
            for src, cnt in stats["source_counts"].items():
                print(f"    {src}: {cnt:,} rows")
    else:
        print("  Database not found or empty.")

    # 导入日志
    import_logs = get_import_stats(db_path)
    if import_logs:
        print(f"\n  {'='*40}")
        print(f"  Import Log (latest 20):")
        print(f"  {'='*40}")
        print(f"  {'Time':<20} {'File':<20} {'Read':>6} {'Ins':>6} {'Skip':>6} {'Err':>4} {'Map':>6}")
        print(f"  {'-'*20} {'-'*20} {'-'*6} {'-'*6} {'-'*6} {'-'*4} {'-'*6}")
        for s in import_logs[:20]:
            print(f"  {s['import_time'][:19]:<20} {s['source_file']:<20} {s['rows_read']:>6,} {s['rows_inserted']:>6,} {s['rows_skipped']:>6,} {s['rows_error']:>4,} {s['mapping_applied']:>6,}")

    print(f"{'='*60}")


def cli_dump_json(indicator_id, start=None, end=None, mapped=None, db_path=None):
    """CLI: 以 JSON 格式输出时序数据 (方便程序调用)"""
    if mapped:
        data = get_series_mapped(mapped, start, end, db_path)
    elif indicator_id:
        data = get_series(indicator_id, start, end, db_path)
    else:
        print("Error: specify indicator_id or --mapped", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(data, ensure_ascii=False, indent=2))


# =============================================================================
# 主入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V88 Phase03-P0 Cache DB Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  list                              List all indicators
  info <indicator_id>              Show indicator metadata
  query <indicator_id>            Query time series data
  query --mapped <meta_chart_id>  Query by DSHE chart indicator ID
  stats                            Show import statistics
  dump <indicator_id>             Output JSON data for programmatic use

Options:
  --start DATE                    Start date filter (YYYY-MM-DD)
  --end DATE                      End date filter (YYYY-MM-DD)
  --limit N                       Max rows to display (default: 50)
  --db PATH                       Database path (default: api_cache.db)
  --json                          Output as JSON (for dump command)

Examples:
  python db_load.py list
  python db_load.py info zn_21_close_front
  python db_load.py query zn_21_close_front --start 2026-08-01 --end 2026-08-28
  python db_load.py query --mapped ZN_FU00014950
  python db_load.py stats
  python db_load.py dump zn_21_close_front --json
        """
    )
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Database path")
    parser.add_argument("--json", action="store_true", help="Output data as JSON")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list 命令
    subparsers.add_parser("list", help="List all indicators")

    # info 命令
    info_parser = subparsers.add_parser("info", help="Show indicator info")
    info_parser.add_argument("indicator_id", type=str, help="Indicator ID")

    # query 命令
    query_parser = subparsers.add_parser("query", help="Query time series")
    query_parser.add_argument("indicator_id", type=str, nargs="?", help="Indicator ID (or use --mapped)")
    query_parser.add_argument("--mapped", type=str, help="Query by DSHE meta_chart indicator ID")
    query_parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    query_parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    query_parser.add_argument("--limit", type=int, default=50, help="Max rows to display")

    # stats 命令
    subparsers.add_parser("stats", help="Show import statistics")

    # dump 命令 (JSON 输出)
    dump_parser = subparsers.add_parser("dump", help="Output time series as JSON")
    dump_parser.add_argument("indicator_id", type=str, nargs="?", help="Indicator ID (or use --mapped)")
    dump_parser.add_argument("--mapped", type=str, help="Query by DSHE meta_chart indicator ID")
    dump_parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    dump_parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")

    args = parser.parse_args()
    db_path = args.db

    if args.command == "list":
        cli_list(db_path)
    elif args.command == "info":
        cli_info(args.indicator_id, db_path)
    elif args.command == "query":
        if args.mapped:
            cli_query(None, mapped=args.mapped, start=args.start, end=args.end, limit=args.limit, db_path=db_path)
        elif args.indicator_id:
            cli_query(args.indicator_id, start=args.start, end=args.end, limit=args.limit, db_path=db_path)
        else:
            parser.error("Specify indicator_id or --mapped")
    elif args.command == "stats":
        cli_stats(db_path)
    elif args.command == "dump":
        cli_dump_json(args.indicator_id, start=args.start, end=args.end, mapped=args.mapped, db_path=db_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
