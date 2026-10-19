#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-A06 · CSV Poller (READ-ONLY)
────────────────────────────────────────────────────────────────────────
目标:  持续只读轮询 output_sample/wdf_sample_metals_raw.csv，每次输出行数/大小/sha256/null率/表头校验结果到 artifacts/dsha_csv_poll_log.json

红线:  只读；不修改/写入CSV；不发起Wind调用；不点火P49；即使达标也只标记 P68_READY_SIGNAL=TRUE，等人工 release_permit

规则:
  - 表头必须为 date,symbol,indicator,value,source
  - 达标: 行数≥300 && 文件大小≥5120 && non_null≥0.90
  - 达标仅标记, 不自动启动回测

用法:
  python code/a06_csv_poller.py --cycles N          # 默认3, 每周期15秒
  python code/a06_csv_poller.py --cycles 1          # 单周期快照
  python code/a06_csv_poller.py --interval 15       # 覆盖轮询间隔
"""
from __future__ import annotations
import sys
import os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 (不可修改)
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
READ_ONLY_CSV = True
AUTO_BACKTEST = "DENIED"
RELEASE_PERMIT = "NOT_ISSUED"
GATE = "CLOSED"

# ════════════════════════════════════════════════════════════════
# P68_SANITY_GATE 只读镜像 (阈值一丝不动)
# ════════════════════════════════════════════════════════════════
P68_MIN_SIZE = 5120
P68_MIN_ROWS = 300
P68_NON_NULL_RATIO = 0.90
P68_REQUIRED_COLUMNS = ["CLOSE", "VOL", "OI", "SETTLE"]
P68_DATE_CONTINUITY = True

# ════════════════════════════════════════════════════════════════
# A06 长表目标 header (工单要求)
# ════════════════════════════════════════════════════════════════
LONG_HEADER = "date,symbol,indicator,value,source"
LONG_HEADER_COLS = ["date", "symbol", "indicator", "value", "source"]

# ════════════════════════════════════════════════════════════════
# 路径
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_CSV = os.path.join(PROJECT_ROOT, "output_sample", "wdf_sample_metals_raw.csv")
LOG_PATH = os.path.join(PROJECT_ROOT, "artifacts", "dsha_csv_poll_log.json")

TZ_CN = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


def sha256_of_file(path: str) -> Optional[str]:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest().upper()
    except FileNotFoundError:
        return None


def read_header_only(path: str) -> Tuple[Optional[List[str]], Optional[str], int]:
    """返回 (header_cols, header_line_raw, header_field_count)；文件不存在返回 (None,None,0)。"""
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            first = f.readline()
            if not first:
                return None, None, 0
            first = first.rstrip("\r\n")
            cols = next(csv.reader([first]))
            return cols, first, len(cols)
    except FileNotFoundError:
        return None, None, 0


def count_lines_and_nulls(path: str) -> Dict[str, Any]:
    """单次只读遍历: 计算行数、各列非空计数、日期格式命中数。只读打开。"""
    result: Dict[str, Any] = {
        "line_count": 0,
        "data_rows": 0,
        "null_counts_by_col": {},
        "non_null_counts_by_col": {},
        "date_format_hits": 0,
        "date_format_misses": 0,
        "parse_errors": 0,
    }
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            header_cols = reader.fieldnames or []
            col_names = list(header_cols)
            for col in col_names:
                result["null_counts_by_col"][col] = 0
                result["non_null_counts_by_col"][col] = 0
            for row in reader:
                result["line_count"] += 1
                result["data_rows"] += 1
                for col in col_names:
                    v = row.get(col)
                    if v is None or str(v).strip() == "":
                        result["null_counts_by_col"][col] += 1
                    else:
                        result["non_null_counts_by_col"][col] += 1
                # 尝试识别 date 列
                date_v = row.get("date")
                if date_v and str(date_v).strip():
                    dv = str(date_v).strip()
                    try:
                        datetime.strptime(dv, "%Y-%m-%d")
                        result["date_format_hits"] += 1
                    except ValueError:
                        result["date_format_misses"] += 1
    except FileNotFoundError:
        return result
    except Exception as e:
        result["parse_errors"] += 1
        result["error"] = str(e)
    return result


def compute_non_null_ratio(line_stats: Dict[str, Any]) -> Optional[float]:
    """按工单语义: 关键数值列 (value, 或 wide-format 下 CLOSE/VOL/OI/SETTLE) 的非空比例。"""
    if not line_stats["data_rows"]:
        return None
    col_names = list(line_stats["non_null_counts_by_col"].keys())
    # 长表: 优先用 value 列
    if "value" in col_names:
        return line_stats["non_null_counts_by_col"]["value"] / line_stats["data_rows"]
    # wide-format: 取 4 个核心列的平均非空比
    core = [c for c in P68_REQUIRED_COLUMNS if c in col_names]
    if not core:
        return None
    ratios = [line_stats["non_null_counts_by_col"][c] / line_stats["data_rows"] for c in core]
    return sum(ratios) / len(ratios)


def poll_once(poll_index: int, prev_sha: Optional[str]) -> Dict[str, Any]:
    """执行一次只读校验，返回结果字典。"""
    exists = os.path.isfile(TARGET_CSV)
    rec: Dict[str, Any] = {
        "poll_index": poll_index,
        "ts": _now_iso(),
        "target_path": os.path.relpath(TARGET_CSV, PROJECT_ROOT),
        "exists": exists,
        "read_only": True,
        "auto_backtest": AUTO_BACKTEST,
        "release_permit": RELEASE_PERMIT,
        "gate": GATE,
        "p68_ready_signal": False,
        "reason": "",
    }
    if not exists:
        rec["reason"] = "FILE_MISSING"
        return rec

    size = os.path.getsize(TARGET_CSV)
    sha = sha256_of_file(TARGET_CSV)
    header_cols, header_raw, header_field_count = read_header_only(TARGET_CSV)
    stats = count_lines_and_nulls(TARGET_CSV)
    ratio = compute_non_null_ratio(stats)

    header_ok = (header_cols == LONG_HEADER_COLS)
    header_matches_wide = header_cols and "CLOSE" in header_cols and "VOL" in header_cols

    size_ok = size >= P68_MIN_SIZE
    rows_ok = stats["data_rows"] >= P68_MIN_ROWS
    non_null_ok = (ratio is not None) and (ratio >= P68_NON_NULL_RATIO)
    header_ok_for_a06 = header_ok  # 仅长表 header 达标

    ready = bool(size_ok and rows_ok and non_null_ok)
    # 注意: header_ok 不作为达标条件的一部分（达标规则工单明确列为 3 项）；但记录 header 校验状态
    # 若 CSV 是 wide-format 且工单要求 long-format，则标记 HEADER_FORMAT_MISMATCH 提示未来需转换

    rec.update({
        "size_bytes": size,
        "sha256": sha,
        "sha256_changed_since_prev": (prev_sha is not None and sha != prev_sha),
        "header_raw": header_raw,
        "header_columns": header_cols,
        "header_field_count": header_field_count,
        "header_matches_long_format": header_ok,
        "header_matches_wide_format": header_matches_wide,
        "data_rows": stats["data_rows"],
        "line_count": stats["line_count"],
        "non_null_ratio_core": ratio,
        "null_counts_by_col": stats["null_counts_by_col"],
        "non_null_counts_by_col": stats["non_null_counts_by_col"],
        "date_format_hits": stats["date_format_hits"],
        "date_format_misses": stats["date_format_misses"],
        "checks": {
            "size_ge_5120": size_ok,
            "rows_ge_300": rows_ok,
            "non_null_ge_0_90": non_null_ok,
            "header_long_format": header_ok,
        },
        "p68_ready_signal": ready,
    })
    if ready:
        rec["reason"] = "P68_READY_SIGNAL_TRUE_PENDING_HUMAN_RELEASE_PERMIT"
    else:
        fails = []
        if not size_ok:
            fails.append(f"size={size}<{P68_MIN_SIZE}")
        if not rows_ok:
            fails.append(f"rows={stats['data_rows']}<{P68_MIN_ROWS}")
        if not non_null_ok:
            fails.append(f"non_null={ratio}<{P68_NON_NULL_RATIO}")
        if header_cols is None:
            fails.append("no_header")
        rec["reason"] = "BELOW_THRESHOLD: " + "; ".join(fails) if fails else "BELOW_THRESHOLD"

    return rec


def load_log() -> List[Dict[str, Any]]:
    if os.path.isfile(LOG_PATH):
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "polls" in data:
                return data["polls"]
            if isinstance(data, list):
                return data
        except Exception:
            return []
    return []


def save_log(polls: List[Dict[str, Any]], meta: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "poller_id": "DSHA-A06-CSV-POLLER",
                "target": os.path.relpath(TARGET_CSV, PROJECT_ROOT),
                "rules": {
                    "long_format_header": LONG_HEADER,
                    "min_size_bytes": P68_MIN_SIZE,
                    "min_rows": P68_MIN_ROWS,
                    "min_non_null_ratio": P68_NON_NULL_RATIO,
                    "wide_format_header_observed": "date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source",
                    "header_check_semantics": "工单要求 long-format header；wide-format 记录为 HEADER_FORMAT_MISMATCH (不参与达标判定)",
                },
                "red_lines": {
                    "read_only": True,
                    "csv_not_modified": True,
                    "wind_api_calls": 0,
                    "offline_only": True,
                    "auto_backtest": "DENIED",
                    "release_permit": "NOT_ISSUED",
                    "p68_gate_unchanged": True,
                },
                "meta": meta,
                "polls": polls,
            },
            f, ensure_ascii=False, indent=2,
        )


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=3, help="轮询周期数 (默认3)")
    ap.add_argument("--interval", type=int, default=15, help="轮询间隔秒 (默认15)")
    ap.add_argument("--no-sleep", action="store_true", help="周期之间不 sleep (仅调试)")
    args = ap.parse_args(argv)

    polls = load_log()
    prev_sha: Optional[str] = polls[-1].get("sha256") if polls else None
    session_id = f"A06-CSV-POLLER-{int(time.time())}"

    new_recs: List[Dict[str, Any]] = []
    for i in range(args.cycles):
        rec = poll_once(len(polls) + len(new_recs), prev_sha)
        rec["session_id"] = session_id
        new_recs.append(rec)
        print(f"[{rec['ts']}] poll#{rec['poll_index']} "
              f"size={rec.get('size_bytes')} sha={str(rec.get('sha256'))[:12]}... "
              f"rows={rec.get('data_rows')} header_long={rec.get('header_matches_long_format')} "
              f"ratio={rec.get('non_null_ratio_core')} ready={rec.get('p68_ready_signal')} "
              f"reason={rec.get('reason')}", flush=True)
        if rec.get("sha256"):
            prev_sha = rec["sha256"]
        if i < args.cycles - 1 and not args.no_sleep:
            time.sleep(args.interval)

    polls.extend(new_recs)
    meta = {
        "run_session_id": session_id,
        "started_at": new_recs[0]["ts"] if new_recs else _now_iso(),
        "ended_at": new_recs[-1]["ts"] if new_recs else _now_iso(),
        "cycles_executed": len(new_recs),
        "interval_sec": args.interval,
        "prev_sha_before_session": polls[-len(new_recs) - 1]["sha256"] if (polls and len(new_recs) < len(polls)) and "sha256" in polls[-len(new_recs) - 1] else None,
    }
    save_log(polls, meta)

    any_ready = any(p.get("p68_ready_signal") for p in new_recs)
    print(f"\n[dsha-a06] cycles={len(new_recs)} any_ready={any_ready} log={os.path.relpath(LOG_PATH, PROJECT_ROOT)}")
    if any_ready:
        print("⚠️ P68_READY_SIGNAL=TRUE 已标记，但 A06 不点火，等待人工 release_permit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
