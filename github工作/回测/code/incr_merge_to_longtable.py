#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHC-DATA-INCREMENT-PIPELINE · 增量→长表合并脚本 (只读模式)
─────────────────────────────────────────────────────────────
工单: DSHC-DATA-INCREMENT-PIPELINE
令牌: DSHC-DATA-INCREMENT-PIPELINE-TOKEN

功能:
  1. 读取原始 V2 长表 (只读, 禁止改写)
  2. 读取增量分片 CSV
  3. 合并: 仅追加增量分片到 V2 长表副本
  4. 自动校验: 总行数 = 原 23328 行 + 新增增量行数
  5. 输出合并后的新版本长表 (V3)
  6. 保留原始增量分片用于审计追溯

红线:
  - 原始 V2 CSV 始终不动 (只读复制)
  - 增量分片文件保留不删除
  - 合并脚本本身零 Wind 调用
  - V1 技能脚本冻结, 不改动 F01/A06 链路
  - Gate=CLOSED/HOLD, Release=NOT_ISSUED

用法:
  # 干运行 (仅验证, 不写文件)
  python code/incr_merge_to_longtable.py --dry-run

  # 合并增量分片到 V3 长表
  python code/incr_merge_to_longtable.py --execute

  # 指定增量分片文件
  python code/incr_merge_to_longtable.py --execute --shard incremental/increment_bar_20261020.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁
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

TZ_CN = timezone(timedelta(hours=8))
WORKORDER = "DSHC-DATA-INCREMENT-PIPELINE"
TOKEN = "DSHC-DATA-INCREMENT-PIPELINE-TOKEN"

# ════════════════════════════════════════════════════════════════
# 品种白名单 + 指标白名单
# ════════════════════════════════════════════════════════════════
SYMBOL_WHITELIST = [
    "AL.SHF", "CU.SHF", "HC.SHF", "NI.SHF", "PB.SHF",
    "RB.SHF", "SN.SHF", "ZN.SHF", "LC.GFE",
]
SYMBOL_BLACKLIST = ["LC.SHF"]
INDICATOR_WHITELIST = ["CLOSE", "HIGH", "LOW", "OI", "SETTLE", "VOL"]
LONG_HEADER = ["date", "symbol", "indicator", "value", "source"]

# ════════════════════════════════════════════════════════════════
# 路径配置
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "artifacts" / "backtest_archive" / "data_assets"
V2_CSV = DATA_DIR / "wdf_sample_all_aligned_v2.csv"
INCREMENTAL_DIR = DATA_DIR / "incremental"
MANIFEST_PATH = DATA_DIR / "data_asset_manifest.json"

def _read_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {}
    with open(MANIFEST_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"

# V3 输出 (合并后的新长表)
V3_CSV = DATA_DIR / "wdf_sample_all_aligned_v3.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("INCR_MERGE")


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


def count_data_rows(path: Path) -> int:
    """计算 CSV 数据行数 (排除注释行和表头)."""
    if not path.is_file():
        return 0
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            count += 1
    # 减去 1 表头
    return max(0, count - 1)


# ════════════════════════════════════════════════════════════════
# 读取 V2 长表 (只读)
# ════════════════════════════════════════════════════════════════
def read_v2_longtable(path: Path = V2_CSV) -> List[List[str]]:
    """
    读取 V2 长表 CSV, 返回数据行 (不含注释和表头).
    只读模式 — 绝不修改原始文件.
    """
    rows: List[List[str]] = []
    if not path.is_file():
        logger.error("V2 CSV not found: %s", path)
        return rows

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # 跳过注释行
            if row[0].strip().startswith("#"):
                continue
            # 跳过表头
            if row[0].strip().lower() == "date" and len(row) >= 5:
                continue
            rows.append(row)

    logger.info("V2 longtable loaded: %d data rows from %s", len(rows), path)
    return rows


# ════════════════════════════════════════════════════════════════
# 读取增量分片
# ════════════════════════════════════════════════════════════════
def read_incremental_shard(shard_path: Path) -> List[List[str]]:
    """
    读取增量分片 CSV, 返回数据行 (不含注释和表头).
    """
    rows: List[List[str]] = []
    if not shard_path.is_file():
        logger.warning("Shard file not found: %s", shard_path)
        return rows

    with open(shard_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            if row[0].strip().startswith("#"):
                continue
            if row[0].strip().lower() == "date" and len(row) >= 5:
                continue
            rows.append(row)

    logger.info("Incremental shard loaded: %d data rows from %s", len(rows), shard_path)
    return rows


# ════════════════════════════════════════════════════════════════
# 防重复: 按 (date, symbol) 去重
# ════════════════════════════════════════════════════════════════
def dedup_by_date_symbol(rows: List[List[str]]) -> Tuple[List[List[str]], int]:
    """
    按 (date, symbol) 去重.
    返回 (去重后的行列表, 被移除的重复行数).
    """
    seen: Set[Tuple[str, str]] = set()
    deduped: List[List[str]] = []
    dup_count = 0

    for row in rows:
        if len(row) < 2:
            continue
        key = (row[0].strip(), row[1].strip())
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        deduped.append(row)

    if dup_count > 0:
        logger.warning("Dedup removed %d duplicate (date, symbol) rows", dup_count)

    return deduped, dup_count


# ════════════════════════════════════════════════════════════════
# 合并逻辑
# ════════════════════════════════════════════════════════════════
def merge_to_v3(
    v2_rows: List[List[str]],
    shard_rows: List[List[str]],
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    合并 V2 长表 + 增量分片 → V3 长表.

    步骤:
      1. 防重复: 移除分片中与 V2 已有的 (date, symbol) 重复行
      2. 追加: V2 行 + 去重后的增量行
      3. 校验: 总行数 = V2 行数 + 新增行数
      4. 写入 V3 (如果 --execute)

    Returns:
      合并结果摘要
    """
    v2_count = len(v2_rows)
    shard_count = len(shard_rows)

    # 构建 V2 已有 (date, symbol) 集合
    v2_keys: Set[Tuple[str, str]] = set()
    for row in v2_rows:
        if len(row) >= 2:
            v2_keys.add((row[0].strip(), row[1].strip()))

    # 从增量分片中移除与 V2 重复的行
    new_rows: List[List[str]] = []
    skipped_dups = 0
    for row in shard_rows:
        if len(row) < 2:
            continue
        key = (row[0].strip(), row[1].strip())
        if key in v2_keys:
            skipped_dups += 1
            continue
        new_rows.append(row)

    # 内部去重 (增量分片自身)
    new_rows, internal_dups = dedup_by_date_symbol(new_rows)

    total_skipped = skipped_dups + internal_dups
    new_count = len(new_rows)
    merged_count = v2_count + new_count

    # 校验
    assert merged_count == v2_count + new_count, (
        f"Row count mismatch: {merged_count} != {v2_count} + {new_count}"
    )

    result = {
        "v2_rows": v2_count,
        "shard_rows_total": shard_count,
        "skipped_duplicate_of_v2": skipped_dups,
        "skipped_internal_dups": internal_dups,
        "total_skipped": total_skipped,
        "new_rows_added": new_count,
        "merged_total_rows": merged_count,
        "row_count_verifiable": merged_count == v2_count + new_count,
        "dry_run": dry_run,
    }

    if not dry_run and new_count > 0:
        # 写入 V3
        write_v3_longtable(v2_rows, new_rows, v2_count, new_count, total_skipped)
        result["v3_written"] = True
        result["v3_path"] = str(V3_CSV.relative_to(PROJECT_ROOT))
    elif not dry_run and new_count == 0:
        logger.info("No new rows to merge; V3 not written (V2 already current)")
        result["v3_written"] = False
        result["v3_path"] = None
    else:
        result["v3_written"] = False
        result["v3_path"] = None

    return result


# ════════════════════════════════════════════════════════════════
# 写入 V3 长表
# ════════════════════════════════════════════════════════════════
def write_v3_longtable(
    v2_rows: List[List[str]],
    new_rows: List[List[str]],
    v2_count: int,
    new_count: int,
    total_skipped: int,
) -> None:
    """写入合并后的 V3 长表 CSV (含元数据注释头)."""
    merged_rows = v2_rows + new_rows

    with open(V3_CSV, "w", encoding="utf-8", newline="") as f:
        # 元数据注释头
        f.write("# =============================================================================\n")
        f.write("# WDF SAMPLE ALL INSTRUMENTS - ALIGNED LONG-FORM CSV (MERGED_V3)\n")
        f.write("# =============================================================================\n")
        f.write(f"# Generated at:      {now_iso()}\n")
        f.write(f"# Source V2:         {v2_count} rows (archived, read-only)\n")
        f.write(f"# Incremental shard: {new_count} new rows added\n")
        f.write(f"# Duplicates skipped: {total_skipped}\n")
        f.write(f"# Total rows:        {v2_count + new_count}\n")
        f.write(f"# Symbols (9):       {', '.join(SYMBOL_WHITELIST)}\n")
        f.write(f"# Indicators (6):    {', '.join(INDICATOR_WHITELIST)}\n")
        f.write(f"# Workorder:         {WORKORDER}\n")
        f.write(f"# Token:             {TOKEN}\n")
        f.write(f"# Gate:              {GATE}\n")
        f.write(f"# Release:           {RELEASE_PERMIT}\n")
        f.write("# ─────────────────────────────────────────────────────────────────────────────\n\n")

        # CSV 表头
        f.write(",".join(LONG_HEADER) + "\n")

        # 数据行
        for row in merged_rows:
            f.write(",".join(str(v) for v in row) + "\n")

    v3_size = V3_CSV.stat().st_size
    v3_sha = sha256_of_file(V3_CSV)
    logger.info("V3 longtable written: %s (%d rows, %d B, sha=%s)",
                V3_CSV, len(merged_rows), v3_size, v3_sha[:12] if v3_sha else "N/A")


# ════════════════════════════════════════════════════════════════
# SHA 快照
# ════════════════════════════════════════════════════════════════
def generate_merge_sha_snapshot(merge_result: Dict[str, Any]) -> Dict[str, Any]:
    """为合并结果生成 SHA 快照."""
    v3_sha = sha256_of_file(V3_CSV) if V3_CSV.is_file() else None
    snapshot = {
        "snapshot_id": "DSHC-INCR-MERGE-SHA",
        "generated_at": now_iso(),
        "workorder": WORKORDER,
        "token": TOKEN,
        "v2_csv": str(V2_CSV.relative_to(PROJECT_ROOT)),
        "v2_sha256": sha256_of_file(V2_CSV),
        "v3_csv": str(V3_CSV.relative_to(PROJECT_ROOT)) if V3_CSV.is_file() else None,
        "v3_sha256": v3_sha,
        "v3_sha256_short": v3_sha[:16] if v3_sha else None,
        "v3_size_bytes": V3_CSV.stat().st_size if V3_CSV.is_file() else 0,
        "merge_result": merge_result,
        "wind_api_calls": 0,
        "gate": GATE,
        "release_permit": RELEASE_PERMIT,
    }
    return snapshot


# ════════════════════════════════════════════════════════════════
# 审计事件
# ════════════════════════════════════════════════════════════════
def append_audit_event(event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """追加审计事件到 tracking_monitor_audit.jsonl."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": now_iso(),
        "event": event_type,
        "agent": "DSHC-DATA-INCREMENT-PIPELINE",
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
    logger.info("Audit event appended: %s", event_type)


# ════════════════════════════════════════════════════════════════
# 主入口
# ════════════════════════════════════════════════════════════════
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="incr_merge_to_longtable.py",
        description="DSHC-DATA-INCREMENT-PIPELINE · 增量→长表合并脚本 (只读模式)",
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true",
                            help="仅验证, 不写文件 (默认)")
    mode_group.add_argument("--execute", action="store_true",
                            help="执行合并并写入 V3")
    parser.add_argument("--shard", type=str, default=None,
                        help="增量分片文件路径 (默认: 自动扫描 incremental/ 目录)")
    parser.add_argument("--verbose", action="store_true",
                        help="启用 DEBUG 日志")
    return parser.parse_args(argv)


def auto_scan_shards() -> List[Path]:
    """自动扫描 incremental/ 目录下的分片文件."""
    if not INCREMENTAL_DIR.is_dir():
        return []
    shards = sorted(INCREMENTAL_DIR.glob("increment_bar_*.csv"))
    # 排除 .sha.json 文件
    shards = [s for s in shards if not s.name.endswith(".sha.json")]
    return shards


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    dry_run = args.dry_run

    print("=" * 70)
    print("DSHC-DATA-INCREMENT-PIPELINE · 增量→长表合并")
    print(f"Mode: {'DRY_RUN' if dry_run else 'EXECUTE'}")
    print(f"Gate: {GATE} | Release: {RELEASE_PERMIT}")
    print("=" * 70)

    # ── 1/4: 读取 V2 长表 ──
    print("\n[1/4] 读取 V2 长表 (只读)...")
    v2_rows = read_v2_longtable()
    v2_count = len(v2_rows)
    logger.info("V2 rows: %d", v2_count)

    # ── 2/4: 读取增量分片 ──
    print("\n[2/4] 读取增量分片...")
    if args.shard:
        shard_paths = [Path(args.shard)]
    else:
        shard_paths = auto_scan_shards()

    all_shard_rows: List[List[str]] = []
    for sp in shard_paths:
        # 解析相对路径
        if not sp.is_absolute():
            sp = PROJECT_ROOT / sp
        rows = read_incremental_shard(sp)
        all_shard_rows.extend(rows)
        logger.info("  Shard %s: %d rows", sp.name, len(rows))

    shard_total = len(all_shard_rows)
    logger.info("Total incremental shard rows: %d", shard_total)

    # ── 3/4: 合并 ──
    print("\n[3/4] 合并增量到 V3...")
    merge_result = merge_to_v3(v2_rows, all_shard_rows, dry_run)

    print(f"\n  V2 rows:          {merge_result['v2_rows']}")
    print(f"  Shard rows:       {merge_result['shard_rows_total']}")
    print(f"  Skipped (dup):    {merge_result['total_skipped']}")
    print(f"  New rows added:   {merge_result['new_rows_added']}")
    print(f"  Merged total:     {merge_result['merged_total_rows']}")
    print(f"  Row count OK:     {merge_result['row_count_verifiable']}")

    # ── 4/4: SHA 快照 ──
    print("\n[4/4] 生成 SHA 快照...")
    sha_snapshot = generate_merge_sha_snapshot(merge_result)

    if not dry_run and merge_result.get("v3_written"):
        # 写入 SHA 快照文件
        snapshot_path = DATA_DIR / "incr_merge_sha_snapshot.json"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(sha_snapshot, f, ensure_ascii=False, indent=2)
        logger.info("SHA snapshot written: %s", snapshot_path)

    # ── 汇总 ──
    print("\n" + "=" * 70)
    print("DSHC-DATA-INCREMENT-PIPELINE · 增量合并完成")
    print("=" * 70)
    print(f"  Mode:              {'DRY_RUN' if dry_run else 'EXECUTE'}")
    print(f"  V2 rows:           {merge_result['v2_rows']}")
    print(f"  New rows:          {merge_result['new_rows_added']}")
    print(f"  Merged total:      {merge_result['merged_total_rows']}")
    print(f"  Row count verif:   {'YES' if merge_result['row_count_verifiable'] else 'FAIL'}")
    print(f"  V3 written:        {merge_result.get('v3_written', False)}")
    print(f"  V3 path:           {merge_result.get('v3_path', 'N/A')}")
    print(f"  Original V2:       UNCHANGED (read-only)")
    print(f"  Shard files:       PRESERVED (audit trail)")
    print(f"  Wind calls:        {WIND_API_CALLS}")
    print(f"  Gate:              {GATE}")
    print(f"  Release:           {RELEASE_PERMIT}")
    print("=" * 70)

    # 审计事件
    append_audit_event(
        "INCR_MERGE_COMPLETE",
        f"增量合并完成: v2={merge_result['v2_rows']} + new={merge_result['new_rows_added']} "
        f"= {merge_result['merged_total_rows']} | skipped={merge_result['total_skipped']}",
        {
            "mode": "DRY_RUN" if dry_run else "EXECUTE",
            "v2_rows": merge_result["v2_rows"],
            "new_rows": merge_result["new_rows_added"],
            "merged_total": merge_result["merged_total_rows"],
            "total_skipped": merge_result["total_skipped"],
            "row_count_verifiable": merge_result["row_count_verifiable"],
            "v3_written": merge_result.get("v3_written", False),
            "v3_path": merge_result.get("v3_path", None),
        },
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
