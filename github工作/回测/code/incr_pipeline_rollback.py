#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHC-DATA-INCR-SCHEDULE-ROLLBACK · 事务回滚备份脚本
────────────────────────────────────────────────────────────
工单: DSHC-DATA-INCR-SCHEDULE-ROLLBACK
令牌: DSHC-DATA-INCR-SCHEDULE-TOKEN

功能:
  1. 手动/自动备份 manifest + V3 长表 + SHA 快照
  2. 从备份恢复
  3. 清理不完整增量分片
  4. 备份清单管理

用法:
  # 创建备份
  python code/incr_pipeline_rollback.py --backup

  # 从最新备份恢复
  python code/incr_pipeline_rollback.py --restore

  # 列出所有备份
  python code/incr_pipeline_rollback.py --list

  # 清理不完整分片
  python code/incr_pipeline_rollback.py --cleanup-shards

  # 删除指定备份
  python code/incr_pipeline_rollback.py --delete-backup <backup_id>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
WORKORDER = "DSHC-DATA-INCR-SCHEDULE-ROLLBACK"
TOKEN = "DSHC-DATA-INCR-SCHEDULE-TOKEN"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "artifacts" / "backtest_archive" / "data_assets"
MANIFEST_PATH = DATA_DIR / "data_asset_manifest.json"
V3_CSV = DATA_DIR / "wdf_sample_all_aligned_v3.csv"
INCREMENTAL_DIR = DATA_DIR / "incremental"
BACKUP_DIR = DATA_DIR / ".backup"
MERGE_SHA_SNAPSHOT = DATA_DIR / "incr_merge_sha_snapshot.json"
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PIPELINE_ROLLBACK")


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


def append_audit_event(event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
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


def backup_all() -> Dict[str, Any]:
    """创建全量备份."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_id = f"DSHC-BACKUP-{datetime.now(TZ_CN).strftime('%Y%m%d%H%M%S')}"
    backup_dir = BACKUP_DIR / backup_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    backups = {}
    for label, src in [
        ("manifest", MANIFEST_PATH),
        ("v3_csv", V3_CSV),
        ("sha_snapshot", MERGE_SHA_SNAPSHOT),
    ]:
        if src.is_file():
            dst = backup_dir / src.name
            shutil.copy2(src, dst)
            backups[label] = {
                "path": str(dst.relative_to(PROJECT_ROOT)),
                "sha256": sha256_of_file(dst),
                "size_bytes": dst.stat().st_size,
            }

    meta = {
        "backup_id": backup_id,
        "created_at": now_iso(),
        "files": {k: v["path"] for k, v in backups.items()},
        "sha256s": {k: v["sha256"] for k, v in backups.items()},
        "gate": GATE,
        "release_permit": RELEASE_PERMIT,
    }
    meta_path = backup_dir / "backup_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 更新备份索引
    index_path = BACKUP_DIR / "backup_index.json"
    index = {"backups": []}
    if index_path.is_file():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    index["backups"].append({
        "backup_id": backup_id,
        "created_at": meta["created_at"],
        "file_count": len(backups),
        "paths": {k: v["path"] for k, v in backups.items()},
    })
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    logger.info("Backup created: %s (%d files)", backup_id, len(backups))
    append_audit_event("ROLLBACK_BACKUP_CREATED", f"备份创建: {backup_id}", meta)

    return meta


def restore_latest() -> int:
    """从最新备份恢复."""
    index_path = BACKUP_DIR / "backup_index.json"
    if not index_path.is_file():
        logger.error("No backup index found.")
        return 1

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    if not index.get("backups"):
        logger.error("No backups available.")
        return 1

    latest = index["backups"][-1]
    backup_dir = BACKUP_DIR / latest["backup_id"]

    restored = []
    for label, rel_path in latest["paths"].items():
        src = backup_dir / Path(rel_path).name
        if label == "manifest":
            target = MANIFEST_PATH
        elif label == "v3_csv":
            target = V3_CSV
        elif label == "sha_snapshot":
            target = MERGE_SHA_SNAPSHOT
        else:
            continue
        if src.is_file():
            shutil.copy2(src, target)
            restored.append(str(target.relative_to(PROJECT_ROOT)))

    logger.info("Restore complete: %d files", len(restored))
    append_audit_event("ROLLBACK_RESTORE", f"从备份恢复: {latest['backup_id']}",
                        {"backup_id": latest["backup_id"], "restored": restored})
    return 0


def list_backups() -> int:
    """列出所有备份."""
    index_path = BACKUP_DIR / "backup_index.json"
    if not index_path.is_file():
        print("No backups found.")
        return 0

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    print(f"{'Backup ID':<45} {'Created':<25} {'Files':>5}")
    print("-" * 80)
    for b in index.get("backups", []):
        print(f"{b['backup_id']:<45} {b['created_at']:<25} {b['file_count']:>5}")
    return len(index.get("backups", []))


def cleanup_shards() -> int:
    """清理今日生成的不完整增量分片."""
    today = datetime.now(TZ_CN).strftime("%Y%m%d")
    cleaned = []

    for pattern in [f"increment_bar_{today}.*"]:
        for f in INCREMENTAL_DIR.glob(pattern):
            if f.suffix == ".csv":
                f.unlink()
                cleaned.append(str(f.relative_to(PROJECT_ROOT)))
            elif f.name.endswith(".sha.json"):
                f.unlink()
                cleaned.append(str(f.relative_to(PROJECT_ROOT)))

    print(f"Cleaned {len(cleaned)} shard files")
    append_audit_event("ROLLBACK_CLEANUP_SHARDS", f"清理分片: {len(cleaned)} 个",
                        {"cleaned": cleaned, "date": today})
    return len(cleaned)


def delete_backup(backup_id: str) -> int:
    """删除指定备份."""
    backup_dir = BACKUP_DIR / backup_id
    if not backup_dir.is_dir():
        logger.error("Backup not found: %s", backup_id)
        return 1

    shutil.rmtree(backup_dir)
    logger.info("Backup deleted: %s", backup_id)

    # 更新索引
    index_path = BACKUP_DIR / "backup_index.json"
    if index_path.is_file():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        index["backups"] = [b for b in index.get("backups", []) if b["backup_id"] != backup_id]
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    append_audit_event("ROLLBACK_BACKUP_DELETED", f"备份删除: {backup_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="增量管道事务回滚备份脚本")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup", action="store_true", help="创建备份")
    group.add_argument("--restore", action="store_true", help="从最新备份恢复")
    group.add_argument("--list", action="store_true", help="列出备份")
    group.add_argument("--cleanup-shards", action="store_true", help="清理不完整分片")
    group.add_argument("--delete-backup", type=str, default=None, help="删除指定备份")

    args = parser.parse_args()

    if args.backup:
        meta = backup_all()
        print(f"Backup created: {meta['backup_id']}")
        return 0
    elif args.restore:
        return restore_latest()
    elif args.list:
        return list_backups()
    elif args.cleanup_shards:
        return cleanup_shards()
    elif args.delete_backup:
        return delete_backup(args.delete_backup)
    return 1


if __name__ == "__main__":
    sys.exit(main())
