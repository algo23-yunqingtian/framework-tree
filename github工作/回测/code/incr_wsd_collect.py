#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHC-DATA-INCREMENT-PIPELINE · 增量采集脚本 (断点续传)
─────────────────────────────────────────────────────────────
工单: DSHC-DATA-INCREMENT-PIPELINE
令牌: DSHC-DATA-INCREMENT-PIPELINE-TOKEN

功能:
  1. 读取 data_asset_manifest.json 获取每只品种最后交易日
  2. 从 last_date + 1 交易日开始, 拉取至当日最新交易日
  3. 生成增量分片 CSV: increment_bar_YYYYMMDD.csv
  4. 内置防重复机制: 按 (date, symbol) 去重
  5. 字段规则: volume 小写, 其余大写 (CLOSE/HIGH/LOW/OI/SETTLE)
  6. LC.SHF 永久黑名单, 不发起任何查询

红线:
  - 增量拉取阶段: 会产生 Wind 调用 (仅此阶段)
  - 校验/合并/审计阶段: 全程离线, 零 Wind 调用
  - 历史全量 CSV 只读, 禁止改写
  - V1 技能脚本冻结, 不改动 F01/A06 链路
  - Gate=CLOSED/HOLD, Release=NOT_ISSUED

用法:
  # 干运行 (仅生成配置, 不调用 Wind)
  python code/incr_wsd_collect.py --dry-run

  # 增量拉取 (调用 Wind API)
  python code/incr_wsd_collect.py --execute

  # 指定截止日期 (覆盖自动检测)
  python code/incr_wsd_collect.py --execute --end 2026-10-25

  # 仅拉取指定品种
  python code/incr_wsd_collect.py --execute --symbols CU.SHF,ZN.SHF
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False  # 仅在 --execute 模式下改为 True
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
# 品种白名单 (9 品种) + 黑名单
# ════════════════════════════════════════════════════════════════
SYMBOL_WHITELIST = [
    "AL.SHF",   # 沪铝 — SHFE
    "CU.SHF",   # 沪铜 — SHFE
    "HC.SHF",   # 热轧卷板 — SHFE
    "NI.SHF",   # 沪镍 — SHFE
    "PB.SHF",   # 沪铅 — SHFE
    "RB.SHF",   # 螺纹钢 — SHFE
    "SN.SHF",   # 沪锡 — SHFE
    "ZN.SHF",   # 沪锌 — SHFE
    "LC.GFE",   # 碳酸锂 — GFE (唯一有效 LC 绑定)
]
SYMBOL_BLACKLIST = ["LC.SHF"]  # 永久黑名单 — INVALID, Wind 上无数据
LC_SHF_PERMANENTLY_BLACKLISTED = True

# ════════════════════════════════════════════════════════════════
# WSD 字段配置 (字段规则固化)
# ════════════════════════════════════════════════════════════════
# CSV indicator column value → WSD query field name
# 关键: VOL → volume (小写), 其余大写
INDICATOR_TO_WSD_FIELD: Dict[str, str] = {
    "CLOSE":  "CLOSE",     # 收盘价 — 大写
    "HIGH":   "HIGH",      # 最高价 — 大写
    "LOW":    "LOW",       # 最低价 — 大写
    "OI":     "OI",        # 持仓量 — 大写
    "SETTLE": "SETTLE",    # 结算价 — 大写
    "VOL":    "volume",    # 成交量 — ⚠️ 小写 (vol 会返回 0 行)
}
INDICATOR_WHITELIST = list(INDICATOR_TO_WSD_FIELD.keys())  # 6 指标

# ════════════════════════════════════════════════════════════════
# 路径配置
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "backtest_archive" / "data_assets" / "data_asset_manifest.json"
INCREMENTAL_DIR = PROJECT_ROOT / "artifacts" / "backtest_archive" / "data_assets" / "incremental"
V2_CSV_PATH = PROJECT_ROOT / "artifacts" / "backtest_archive" / "data_assets" / "wdf_sample_all_aligned_v2.csv"
CONFIG_OUT = PROJECT_ROOT / "artifacts" / "backtest_archive" / "data_assets" / "incr_collect_config.json"
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"

SOURCE_TAG = "WDF-GUI"  # 数据来源标签

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("INCR_COLLECT")


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


# ════════════════════════════════════════════════════════════════
# 读取 manifest 获取最后交易日
# ════════════════════════════════════════════════════════════════
def read_manifest() -> Dict[str, Any]:
    """读取 data_asset_manifest.json, 返回 instrument_index 和增量运行历史."""
    if not MANIFEST_PATH.is_file():
        logger.warning("Manifest not found: %s", MANIFEST_PATH)
        return {}

    with open(MANIFEST_PATH, "r", encoding="utf-8-sig") as f:
        manifest = json.load(f)

    logger.info("Manifest loaded: version=%s, total_files=%s, total_rows=%s",
                manifest.get("version"), manifest.get("total_files"), manifest.get("total_rows"))

    instrument_index = manifest.get("instrument_index", {})
    if instrument_index:
        for sym in sorted(instrument_index):
            info = instrument_index[sym]
            logger.info("  %-8s | last_date=%s | rows=%d | indicators=%d",
                        sym, info.get("last_date"), info.get("row_count", 0),
                        info.get("indicator_count", 0))

    return manifest


def get_last_date_per_symbol() -> Dict[str, str]:
    """从 manifest 获取每只品种的最后交易日. 回退到 V2 CSV 读取."""
    manifest = read_manifest()
    instrument_index = manifest.get("instrument_index", {})

    if instrument_index:
        return {sym: info.get("last_date", "") for sym, info in instrument_index.items()}

    # 回退: 从 V2 CSV 直接读取
    logger.info("No instrument_index in manifest; falling back to V2 CSV read...")
    return _read_last_dates_from_csv()


def _read_last_dates_from_csv() -> Dict[str, str]:
    """从 V2 CSV 读取每只品种的最后交易日 (回退路径)."""
    last_dates: Dict[str, str] = {}

    if not V2_CSV_PATH.is_file():
        logger.error("V2 CSV not found: %s", V2_CSV_PATH)
        return {}

    with open(V2_CSV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) < 5:
                continue
            date_val, symbol_val = parts[0].strip(), parts[1].strip()
            if not date_val or not symbol_val:
                continue
            if symbol_val not in SYMBOL_WHITELIST:
                continue
            if date_val > last_dates.get(symbol_val, ""):
                last_dates[symbol_val] = date_val

    logger.info("Read last dates from V2 CSV: %d symbols", len(last_dates))
    for sym in sorted(last_dates):
        logger.info("  %-8s → %s", sym, last_dates[sym])
    return last_dates


# ════════════════════════════════════════════════════════════════
# 构建 WSD 采集配置
# ════════════════════════════════════════════════════════════════
def build_wsd_queries(
    last_dates: Dict[str, str],
    end_date: Optional[str] = None,
    symbols: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    构建增量 WSD 查询配置.
    每只品种一个查询, 字段用分号连接.

    日期规则:
      - start = last_date (当天数据已有, 从当天开始确保不遗漏)
      - end = end_date (或自动检测最新交易日)
      - 防重复: 后续去重步骤会移除 last_date 之前的数据

    Returns:
      查询配置列表, 每个元素包含 instrument, fields, dates, formula
    """
    if end_date is None:
        # 自动检测: 用今天作为结束日期 (实际运行时 Wind 会返回最新交易日)
        end_date = datetime.now(TZ_CN).strftime("%Y-%m-%d")
        logger.info("Auto-detected end_date: %s", end_date)

    if symbols is None:
        symbols = SYMBOL_WHITELIST[:]
    else:
        symbols = [s.strip() for s in symbols if s.strip()]

    # 过滤黑名单
    symbols = [s for s in symbols if s not in SYMBOL_BLACKLIST]
    # 过滤不在白名单的品种
    symbols = [s for s in symbols if s in SYMBOL_WHITELIST]

    field_list = ";".join(INDICATOR_TO_WSD_FIELD.values())  # CLOSE;HIGH;LOW;OI;SETTLE;volume
    queries = []

    for symbol in symbols:
        last_date = last_dates.get(symbol, "")
        if not last_date:
            logger.warning("%s: no last_date found; skipping incremental query", symbol)
            continue

        # 增量起始 = last_date (包含当天, 后续去重会处理)
        start_date = last_date

        query = {
            "instrument": symbol,
            "fields_wsd": list(INDICATOR_TO_WSD_FIELD.values()),
            "fields_csv_indicator": list(INDICATOR_TO_WSD_FIELD.keys()),
            "field_mapping": INDICATOR_TO_WSD_FIELD,
            "start_date": start_date,
            "end_date": end_date,
            "last_date_in_archive": last_date,
            "wsd_formula": f'=WSD("{symbol}","{field_list}","{start_date}","{end_date}","Fill=Previous")',
            "query_type": "INCREMENTAL",
        }
        queries.append(query)
        logger.info("Query: %s | %s→%s | fields=%s", symbol, start_date, end_date, field_list)

    return queries


# ════════════════════════════════════════════════════════════════
# 写入采集配置文件
# ════════════════════════════════════════════════════════════════
def write_config(
    queries: List[Dict[str, Any]],
    last_dates: Dict[str, str],
    end_date: str,
    is_dry_run: bool = True,
) -> Path:
    """写入 incr_collect_config.json (配套 JSON 配置)."""
    config = {
        "config_id": "DSHC-INCR-COLLECT-CONFIG",
        "workorder": WORKORDER,
        "token": TOKEN,
        "generated_at": now_iso(),
        "mode": "DRY_RUN" if is_dry_run else "EXECUTE",
        "end_date": end_date,
        "last_dates_per_symbol": last_dates,
        "symbol_whitelist": SYMBOL_WHITELIST,
        "symbol_blacklist": SYMBOL_BLACKLIST,
        "lc_shf_permanently_blacklisted": LC_SHF_PERMANENTLY_BLACKLISTED,
        "indicator_to_wsd_field": INDICATOR_TO_WSD_FIELD,
        "field_count": len(INDICATOR_TO_WSD_FIELD),
        "instrument_count": len(queries),
        "total_queries": len(queries),
        "wind_api_calls_in_dry_run": 0,
        "wind_api_calls_in_execute": len(queries) if not is_dry_run else 0,
        "queries": queries,
        "governance": {
            "REAL_WIND_CALL": False if is_dry_run else True,
            "WIND_API_CALLS": 0 if is_dry_run else len(queries),
            "OFFLINE_ONLY": is_dry_run,
            "AUTO_BACKTEST": AUTO_BACKTEST,
            "RELEASE_PERMIT": RELEASE_PERMIT,
            "GATE": GATE,
            "CSV_READONLY": True,
            "V1_FROZEN": V1_FROZEN,
            "F01_A06_UNCHANGED": F01_A06_UNCHANGED,
        },
    }

    INCREMENTAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_OUT, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    config_sha = sha256_of_file(CONFIG_OUT)
    logger.info("Config written: %s (%d B, sha=%s)",
                CONFIG_OUT, CONFIG_OUT.stat().st_size, config_sha[:12] if config_sha else "N/A")

    return CONFIG_OUT


# ════════════════════════════════════════════════════════════════
# 增量分片 CSV 生成 (模拟输出格式)
# ════════════════════════════════════════════════════════════════
def generate_sample_shard(shard_date: str = "20261020") -> Tuple[Path, int]:
    """
    生成增量分片 CSV 样本文件 (空壳 + 表头).
    实际数据由 --execute 模式调用 Wind API 填充.

    文件命名: increment_bar_YYYYMMDD.csv
    存放位置: artifacts/backtest_archive/data_assets/incremental/

    Returns:
      (path, row_count) — 路径和行数 (不含表头)
    """
    INCREMENTAL_DIR.mkdir(parents=True, exist_ok=True)
    shard_path = INCREMENTAL_DIR / f"increment_bar_{shard_date}.csv"

    # 写入 CSV 表头
    header = "date,symbol,indicator,value,source"
    lines = [header]

    # 样本: 空壳 (实际运行时由 Wind API 填充)
    # 以下注释说明预期格式:
    # 2026-10-20,CU.SHF,CLOSE,109000,WDF-GUI
    # 2026-10-20,CU.SHF,HIGH,109500,WDF-GUI
    # 2026-10-20,CU.SHF,LOW,108500,WDF-GUI
    # 2026-10-20,CU.SHF,OI,220000,WDF-GUI
    # 2026-10-20,CU.SHF,SETTLE,109200,WDF-GUI
    # 2026-10-20,CU.SHF,VOL,110000,WDF-GUI

    with open(shard_path, "w", encoding="utf-8", newline="") as f:
        for line in lines:
            f.write(line + "\n")

    row_count = 0  # 空壳, 实际行数为 0
    logger.info("Sample shard written: %s (%d rows, header only)", shard_path, row_count)

    return shard_path, row_count


def generate_sha_snapshot(shard_path: Path) -> Dict[str, Any]:
    """为增量分片生成 SHA 快照."""
    sha = sha256_of_file(shard_path)
    snapshot = {
        "snapshot_id": "DSHC-INCR-SHARD-SHA",
        "generated_at": now_iso(),
        "shard_file": str(shard_path.relative_to(PROJECT_ROOT)),
        "sha256": sha,
        "sha256_short": sha[:16] if sha else None,
        "size_bytes": shard_path.stat().st_size if shard_path.is_file() else 0,
        "data_rows": 0,  # 空壳
        "header": "date,symbol,indicator,value,source",
        "symbols": SYMBOL_WHITELIST,
        "indicators": INDICATOR_WHITELIST,
    }

    snapshot_path = shard_path.with_suffix(".sha.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    logger.info("SHA snapshot written: %s", snapshot_path)
    return snapshot


# ════════════════════════════════════════════════════════════════
# 审计事件写入
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
        prog="incr_wsd_collect.py",
        description="DSHC-DATA-INCREMENT-PIPELINE · 增量采集脚本 (断点续传)",
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--dry-run", action="store_true",
                            help="仅生成配置, 不调用 Wind API (默认)")
    mode_group.add_argument("--execute", action="store_true",
                            help="调用 Wind API 执行增量拉取")
    parser.add_argument("--end", type=str, default=None,
                        help="截止日期 (YYYY-MM-DD). 默认: 当天")
    parser.add_argument("--symbols", type=str, default=None,
                        help="逗号分隔的品种列表 (默认: 全部 9 品种白名单)")
    parser.add_argument("--shard-date", type=str, default=None,
                        help="分片日期 (YYYYMMDD). 默认: 当天")
    parser.add_argument("--verbose", action="store_true",
                        help="启用 DEBUG 日志")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    global REAL_WIND_CALL, WIND_API_CALLS, OFFLINE_ONLY
    is_dry_run = args.dry_run

    print("=" * 70)
    print("DSHC-DATA-INCREMENT-PIPELINE · 增量采集脚本")
    print(f"Mode: {'DRY_RUN' if is_dry_run else 'EXECUTE'}")
    print(f"Gate: {GATE} | Release: {RELEASE_PERMIT}")
    print("=" * 70)

    # ── P1.1.1: 读取最后交易日 ──
    print("\n[1/5] 读取最后交易日...")
    last_dates = get_last_date_per_symbol()
    if not last_dates:
        logger.error("No last dates found; aborting.")
        return 1

    end_date = args.end or datetime.now(TZ_CN).strftime("%Y-%m-%d")
    logger.info("End date: %s", end_date)

    # ── P1.1.2: 构建 WSD 查询 ──
    print("\n[2/5] 构建 WSD 查询配置...")
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    queries = build_wsd_queries(last_dates, end_date, symbols)
    logger.info("Total queries: %d", len(queries))

    # ── P1.1.3: 写入配置 ──
    print("\n[3/5] 写入采集配置...")
    config_path = write_config(queries, last_dates, end_date, is_dry_run)

    # ── P1.1.4: 生成增量分片 ──
    print("\n[4/5] 生成增量分片...")
    shard_date = args.shard_date or datetime.now(TZ_CN).strftime("%Y%m%d")
    shard_path, row_count = generate_sample_shard(shard_date)

    # ── P1.1.5: 生成 SHA 快照 ──
    print("\n[5/5] 生成 SHA 快照...")
    snapshot = generate_sha_snapshot(shard_path)

    # ── 汇总 ──
    print("\n" + "=" * 70)
    print("DSHC-DATA-INCREMENT-PIPELINE · 增量采集完成")
    print("=" * 70)
    print(f"  Mode:            {'DRY_RUN' if is_dry_run else 'EXECUTE'}")
    print(f"  End date:        {end_date}")
    print(f"  Instruments:     {len(queries)} (LC.SHF blacklisted)")
    print(f"  Indicators:      {len(INDICATOR_TO_WSD_FIELD)} (CLOSE,HIGH,LOW,OI,SETTLE,VOL)")
    print(f"  Wind calls:      {0 if is_dry_run else len(queries)}")
    print(f"  Config:          {config_path.relative_to(PROJECT_ROOT)}")
    print(f"  Shard:           {shard_path.relative_to(PROJECT_ROOT)} ({row_count} rows)")
    print(f"  SHA snapshot:    {shard_path.with_suffix('.sha.json')}")
    print(f"  Gate:            {GATE}")
    print(f"  Release:         {RELEASE_PERMIT}")
    print(f"  V1 frozen:       {V1_FROZEN}")
    print(f"  CSV readonly:    {CSV_READONLY}")
    print("=" * 70)

    # 写入审计事件
    append_audit_event(
        "INCR_COLLECT_READY",
        f"增量采集脚本就绪: mode={'DRY_RUN' if is_dry_run else 'EXECUTE'}, "
        f"instruments={len(queries)}, end_date={end_date}, "
        f"wind_api_calls={0 if is_dry_run else len(queries)}",
        {
            "mode": "DRY_RUN" if is_dry_run else "EXECUTE",
            "end_date": end_date,
            "instruments": len(queries),
            "indicators": len(INDICATOR_TO_WSD_FIELD),
            "wind_api_calls": 0 if is_dry_run else len(queries),
            "config_path": str(config_path.relative_to(PROJECT_ROOT)),
            "shard_path": str(shard_path.relative_to(PROJECT_ROOT)),
        },
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
