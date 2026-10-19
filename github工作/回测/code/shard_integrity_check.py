#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHC-TASK-011 · 分片数据完整性校验脚本
──────────────────────────────────────────────────────────
工单: DSHC-TASK-011
令牌: DSHC-TASK011-PIPE-SCALE-TOKEN

功能:
  1. 自动发现所有并行分片 (parallel_shard_*.csv)
  2. 校验每一片段的行数、SHA、时间序列连续性
  3. 校验品种一致性 (每个分片仅包含对应品种数据)
  4. 生成完整性报告 JSON

治理红线:
  - wind_api_calls=0
  - Gate=CLOSED/HOLD, Release=NOT_ISSUED
  - V2 SHA 锁定不变
  - LC.SHF 黑名单, E13/E14/E15 质检规则不变

用法:
  python code/shard_integrity_check.py
  python code/shard_integrity_check.py --dir <path>
  python code/shard_integrity_check.py --json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ════════════════════════════════════════════════════════════════
# 安全锁
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
AUTO_BACKTEST = "DENIED"
RELEASE_PERMIT = "NOT_ISSUED"
GATE = "CLOSED/HOLD"
CSV_READONLY = True
V1_FROZEN = True
F01_A06_UNCHANGED = True
LC_SHF_PERMANENTLY_BLACKLISTED = True

TZ_CN = timezone(timedelta(hours=8))
WORKORDER = "DSHC-TASK-011"
TOKEN = "DSHC-TASK011-PIPE-SCALE-TOKEN"

# ════════════════════════════════════════════════════════════════
# 路径
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "artifacts" / "backtest_archive" / "data_assets"
PARALLEL_DIR = DATA_DIR / "incremental" / "parallel"
DSHA_SANDBOX_DIR = PROJECT_ROOT / "output_sample" / "parallel_shards"
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"
INTEGRITY_REPORT_PATH = DATA_DIR / "shard_integrity_report.json"

# ════════════════════════════════════════════════════════════════
# 品种 + 指标
# ════════════════════════════════════════════════════════════════
SYMBOL_WHITELIST = [
    "AL.SHF", "CU.SHF", "HC.SHF", "NI.SHF", "PB.SHF",
    "RB.SHF", "SN.SHF", "ZN.SHF", "LC.GFE",
]
SYMBOL_BLACKLIST = ["LC.SHF"]
INDICATOR_WHITELIST = ["CLOSE", "HIGH", "LOW", "OI", "SETTLE", "VOL"]
LONG_HEADER = ["date", "symbol", "indicator", "value", "source"]

# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════
def now_iso() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


def sha256_of_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def count_csv_data_rows(path: Path) -> int:
    if not path.is_file():
        return 0
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            count += 1
    return max(0, count - 1)  # subtract header


def read_csv_data_rows(path: Path) -> List[List[str]]:
    rows: List[List[str]] = []
    if not path.is_file():
        return rows
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            if row[0].strip().startswith("#"):
                continue
            if row[0].strip().lower() == "date" and len(row) >= 5:
                continue
            rows.append(row)
    return rows


def read_header(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
    return first_line


def append_audit_event(event_type: str, message: str,
                        data: Optional[Dict[str, Any]] = None) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": now_iso(),
        "event": event_type,
        "agent": WORKORDER,
        "token": TOKEN,
        "wind_api_calls": 0,
        "gate": GATE,
        "release_permit": RELEASE_PERMIT,
        "message": message,
    }
    if data:
        event["data"] = data
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ════════════════════════════════════════════════════════════════
# 分片发现
# ════════════════════════════════════════════════════════════════
def discover_shards(search_dirs: Optional[List[Path]] = None) -> List[Path]:
    """Discover all parallel shard files."""
    if search_dirs is None:
        search_dirs = [PARALLEL_DIR, DSHA_SANDBOX_DIR]
    
    shards = []
    seen = set()
    
    for d in search_dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("parallel_shard_*.csv")):
            if str(f) not in seen:
                shards.append(f)
                seen.add(str(f))
    
    return shards


# ════════════════════════════════════════════════════════════════
# 单分片完整性检查
# ════════════════════════════════════════════════════════════════
def check_single_shard(shard_path: Path) -> Dict[str, Any]:
    """Check integrity of a single shard file."""
    result = {
        "shard_file": shard_path.name,
        "shard_path": str(shard_path),
        "status": "PASS",
    }
    
    # 1. File exists
    if not shard_path.is_file():
        result["status"] = "FAIL"
        result["error"] = "File not found"
        return result
    
    # 2. File size
    result["size_bytes"] = shard_path.stat().st_size
    
    # 3. Header format
    header = read_header(shard_path)
    expected_header = ",".join(LONG_HEADER)
    result["header"] = header
    result["header_expected"] = expected_header
    result["header_ok"] = (header == expected_header)
    if not result["header_ok"]:
        result["status"] = "FAIL"
        result["error"] = f"Header mismatch: got {header!r}, expected {expected_header!r}"
        return result
    
    # 4. Row count
    row_count = count_csv_data_rows(shard_path)
    result["row_count"] = row_count
    
    # 5. SHA256
    sha = sha256_of_file(shard_path)
    result["sha256"] = sha
    
    # 6. Expected SHA from snapshot
    snapshot_path = shard_path.with_suffix(".sha.json")
    expected_sha = None
    if snapshot_path.is_file():
        try:
            with open(snapshot_path, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
            expected_sha = snapshot.get("sha256")
        except (json.JSONDecodeError, OSError):
            pass
    
    result["expected_sha"] = expected_sha
    result["sha_ok"] = (sha == expected_sha) if expected_sha else None
    if result["sha_ok"] is False:
        result["status"] = "FAIL"
        result["error"] = f"SHA mismatch: got {sha[:16]}, expected {(expected_sha or '')[:16]}"
        return result
    
    # 7. Read all data rows
    rows = read_csv_data_rows(shard_path)
    
    # 8. Symbol consistency
    symbols_found = set()
    for row in rows:
        if len(row) >= 2:
            symbols_found.add(row[1].strip())
    result["symbols_found"] = sorted(symbols_found)
    result["symbol_consistent"] = len(symbols_found) <= 1
    if not result["symbol_consistent"]:
        result["status"] = "FAIL"
        result["error"] = f"Multiple symbols in single shard: {sorted(symbols_found)}"
        return result
    
    # 9. Indicator consistency
    indicators_found = set()
    for row in rows:
        if len(row) >= 3:
            indicators_found.add(row[2].strip().upper())
    result["indicators_found"] = sorted(indicators_found)
    valid_indicators = indicators_found.issubset(set(INDICATOR_WHITELIST))
    result["indicators_valid"] = valid_indicators
    if not valid_indicators:
        invalid = indicators_found - set(INDICATOR_WHITELIST)
        result["status"] = "FAIL"
        result["error"] = f"Invalid indicators: {sorted(invalid)}"
        return result
    
    # 10. Blacklist check (E13)
    for sym in symbols_found:
        if sym in SYMBOL_BLACKLIST:
            result["status"] = "FAIL"
            result["error"] = f"Blacklisted symbol in shard: {sym}"
            return result
    
    # 11. Field case check (E14)
    for row in rows:
        if len(row) >= 3:
            ind = row[2].strip()
            if ind.lower() in ("vol", "volume") and ind not in ("VOL",):
                result["status"] = "FAIL"
                result["error"] = f"E14 field case error: {ind!r}"
                return result
    
    # 12. Time series continuity
    dates_found = []
    for row in rows:
        if len(row) >= 1:
            d = row[0].strip()
            if d and d != "date":
                dates_found.append(d)
    
    unique_dates = sorted(set(dates_found))
    result["dates_count"] = len(unique_dates)
    
    time_continuous = True
    date_gaps = []
    for i in range(1, len(unique_dates)):
        try:
            d1 = datetime.strptime(unique_dates[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(unique_dates[i], "%Y-%m-%d")
            if d2 < d1:
                time_continuous = False
            elif (d2 - d1).days > 7:  # Allow weekends (5 days gap is normal)
                date_gaps.append({
                    "from": unique_dates[i-1],
                    "to": unique_dates[i],
                    "gap_days": (d2 - d1).days,
                })
        except ValueError:
            time_continuous = False
    
    result["time_continuous"] = time_continuous
    result["date_gaps"] = date_gaps
    
    if not time_continuous:
        result["status"] = "FAIL"
        result["error"] = "Time series not continuous (dates out of order)"
        return result
    
    # 13. Non-empty check (data rows)
    result["has_data"] = row_count > 0
    if row_count == 0:
        result["note"] = "Empty shard (dry-run skeleton, header only)"
    
    return result


# ════════════════════════════════════════════════════════════════
# 全量完整性检查
# ════════════════════════════════════════════════════════════════
def run_integrity_check(search_dirs: Optional[List[Path]] = None) -> Dict[str, Any]:
    """Run integrity check on all discovered shards."""
    shards = discover_shards(search_dirs)
    
    if not shards:
        return {
            "status": "NO_SHARDS",
            "total_shards": 0,
            "all_ok": True,
            "shards": [],
            "created_at": now_iso(),
            "workorder": WORKORDER,
            "token": TOKEN,
        }
    
    results = []
    all_ok = True
    
    for shard_path in shards:
        result = check_single_shard(shard_path)
        results.append(result)
        if result["status"] != "PASS":
            all_ok = False
    
    summary = {
        "status": "PASS" if all_ok else "FAIL",
        "total_shards": len(results),
        "all_ok": all_ok,
        "shards_pass": sum(1 for r in results if r["status"] == "PASS"),
        "shards_fail": sum(1 for r in results if r["status"] != "PASS"),
        "shards_with_data": sum(1 for r in results if r.get("has_data")),
        "shards_empty": sum(1 for r in results if not r.get("has_data")),
        "sha_verified": sum(1 for r in results if r.get("sha_ok") is True),
        "sha_missing_snapshot": sum(1 for r in results if r.get("sha_ok") is None),
        "created_at": now_iso(),
        "workorder": WORKORDER,
        "token": TOKEN,
        "search_dirs": [str(d) for d in (search_dirs or [PARALLEL_DIR, DSHA_SANDBOX_DIR])],
    }
    
    report = {
        "report_id": "DSHC-TASK011-SHARD-INTEGRITY-REPORT",
        "summary": summary,
        "shards": results,
        "constraints": {
            "wind_api_calls": 0,
            "gate": GATE,
            "release_permit": RELEASE_PERMIT,
            "lc_shf_blacklisted": True,
            "e13_e14_e15_unchanged": True,
        },
    }
    
    # Write report
    INTEGRITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INTEGRITY_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="shard_integrity_check.py",
        description=f"{WORKORDER} · 分片数据完整性校验",
    )
    parser.add_argument("--dir", type=str, default=None,
                        help="自定义分片目录 (默认: incremental/parallel/ + output_sample/parallel_shards/)")
    parser.add_argument("--json", action="store_true",
                        help="输出 JSON 格式")
    parser.add_argument("--verbose", action="store_true",
                        help="详细输出")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    
    search_dirs = None
    if args.dir:
        search_dirs = [Path(args.dir)]
    
    print("=" * 60)
    print(f"{WORKORDER} · 分片数据完整性校验")
    print(f"Gate: {GATE} | Release: {RELEASE_PERMIT} | Wind calls: 0")
    print("=" * 60)
    
    report = run_integrity_check(search_dirs)
    summary = report.get("summary", {})
    
    print(f"\n发现分片: {summary.get('total_shards', 0)}")
    print(f"通过:     {summary.get('shards_pass', 0)}")
    print(f"失败:     {summary.get('shards_fail', 0)}")
    print(f"有数据:   {summary.get('shards_with_data', 0)}")
    print(f"空壳:     {summary.get('shards_empty', 0)}")
    print(f"SHA验证:  {summary.get('sha_verified', 0)}")
    print(f"SHA缺失:  {summary.get('sha_missing_snapshot', 0)}")
    
    print(f"\n总状态: {summary.get('status', 'UNKNOWN')}")
    
    # Detail
    if args.verbose or args.json:
        for shard in report.get("shards", []):
            status = "PASS" if shard["status"] == "PASS" else "FAIL"
            print(f"\n  [{status}] {shard['shard_file']}")
            print(f"    Rows: {shard.get('row_count', 0)} | "
                  f"SHA: {(shard.get('sha256') or 'N/A')[:16]} | "
                  f"Symbols: {shard.get('symbols_found', [])}")
            if shard.get("date_gaps"):
                print(f"    Date gaps: {shard['date_gaps']}")
            if shard.get("error"):
                print(f"    Error: {shard['error']}")
    
    if args.json:
        print(f"\n{'=' * 60}")
        print("JSON Report:")
        print("=" * 60)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    
    return 0 if summary.get("all_ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
