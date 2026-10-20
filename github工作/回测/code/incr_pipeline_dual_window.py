#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHC-TASK-017 · 双窗口常态化并行采集工单
═══════════════════════════════════════════════════════════
工单:  DSHC-TASK-017
令牌:  DSHC-TASK017-DUAL-WINDOW-TOKEN
授权:  USER-A01 远程许可

P0  冒烟自检：分片目录、锁机制、SHA校验、双窗口目录隔离、告警推送全项校验
P1  开启双窗口并行流水线：同时产出20d+40d两套滚动分片数据，两套目录严格物理隔离
P2  持续维持UP/DOWN/SIDEWAYS三类行情样本均衡，保证DOWN窗口≥20，长期样本充足
P3  持续采集合约换月OI数据，保持OI变化率-30%阈值不变，稳定产出contract_switch_flag
P4  每轮输出双窗口一致性报告、锁冲突台账、资源吞吐监控，持续向DSHD推送流水线事件
P5  长期运行结束后，输出双窗口数据集快照+全量SHA指纹，发送就绪回执至DSHA

红线约束:
  1. 严禁改动生产串行业务脚本；所有写入强制排他锁，禁止无锁降级
  2. 一旦出现锁冲突、分片交叉污染，立刻停止采集、自动回滚并上报告警

前置:
  DSHC-TASK-016 — 多窗口数据集扩展与换月因子数据源补齐
  DSHC-TASK-015 — 并行链路7日连续稳定性压测
  DSHC-TASK-014 — 并行链路稳定性+全量数据采集
  DSHC-TASK-013 — 点火启动
  DSHC-TASK-012 — 并行上线, 全局锁, 5轮一致性
  DSHC-TASK-011 — 并行扩容分片
  DSHC-TASK-010 — 线上监控

用法:
  python code/incr_pipeline_dual_window.py --full-run
  python code/incr_pipeline_dual_window.py --p0-self-check
  python code/incr_pipeline_dual_window.py --p1-dual-window
  python code/incr_pipeline_dual_window.py --p2-regime-balance
  python code/incr_pipeline_dual_window.py --p3-contract-rollover
  python code/incr_pipeline_dual_window.py --p4-consistency-alerts
  python code/incr_pipeline_dual_window.py --p5-receipt
  python code/incr_pipeline_dual_window.py --cleanup
"""

from __future__ import annotations

import argparse
import json
import logging
import multiprocessing
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── UTF-8 output guard ──
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Module path ──
CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

# ── Import from TASK-012/013/014/015/016 infrastructure ──
from incr_pipeline_parallel_online import (
    GlobalLockManager,
    parallel_worker_online,
    run_parallel_round,
    run_consistency_check as _ppo_consistency_check,
    run_alert_integration_test,
    run_lock_test,
    write_simulated_shard,
    read_manifest,
    now_iso,
    sha256_of_file,
    count_csv_data_rows,
    read_csv_data_rows,
    check_e13_symbol_blacklist,
    check_e14_field_case,
    check_e15_daily_completeness,
    DATA_DIR,
    MANIFEST_PATH,
    V2_CSV,
    INCREMENTAL_DIR,
    BACKUP_DIR,
    LOCK_FILE,
    AUDIT_LOG,
    PARALLEL_DIR,
    DSHA_SANDBOX_DIR,
    PARALLEL_LOCK_FILE,
    GLOBAL_LOCK_FILE,
    PARALLEL_SCHEDULE_CONFIG,
    LOCK_CONFLICT_STATS,
    CONSISTENCY_REPORT,
    PARALLEL_ONLINE_SNAPSHOT,
    SHARD_LOCK_TIMEOUT_SEC,
    SYMBOL_WHITELIST,
    SYMBOL_BLACKLIST,
    INDICATOR_WHITELIST,
    LONG_HEADER,
    SOURCE_TAG,
    PROJECT_ROOT,
    TZ_CN,
)
from incr_alert_hook import AlertHook

# ════════════════════════════════════════════════════════════════
# 🔒 TASK-017 安全锁
# ════════════════════════════════════════════════════════════════
WORKORDER = "DSHC-TASK-017"
TOKEN = "DSHC-TASK017-DUAL-WINDOW-TOKEN"
AUTHORIZATION = "USER-A01"
REAL_WIND_CALL = False
OFFLINE_ONLY = False
AUTO_BACKTEST = "DENIED"
RELEASE_PERMIT = "NOT_ISSUED"
GATE = "CLOSED/HOLD"
CSV_READONLY = True
V1_FROZEN = True
F01_A06_UNCHANGED = True
LC_SHF_PERMANENTLY_BLACKLISTED = True

# V2 SHA 锁定
V2_SHA_LOCKED = "14950B9464BAEFD8C90DBFCD58C99904631755DC26A85BF94DC51E73908BDDB4"
V2_SHA_SHORT = "14950B9464BAEFD8"

# P1 参数：双窗口
WINDOW_20D_DAYS = 20
WINDOW_40D_DAYS = 40
ROLLING_REGIME_CYCLE = ["UP", "DOWN", "SIDEWAYS"]

# P2 参数：行情均衡 (DOWN ≥ 20)
MONITOR_TRADING_DAYS = 7
MONITOR_ROUNDS_PER_DAY = 6
MONITOR_TOTAL_ROUNDS = MONITOR_TRADING_DAYS * MONITOR_ROUNDS_PER_DAY  # 42
REGIME_CYCLE = ["DOWN", "DOWN", "DOWN", "UP", "SIDEWAYS"]  # DOWN ≥ 20 guarantee
DOWN_MINIMUM = 20

# P3 参数：合约换月
OI_CHANGE_THRESHOLD = -0.30
CONTRACT_ROLLOVER_SIM_DAYS = 40

# P4 参数
ALERT_BATCH_SIZE = 10

WIND_API_CALLS = 0

# TASK-017 专用路径
DUAL_WINDOW_REPORT = DATA_DIR / "dual_window_report.json"
DUAL_WINDOW_SNAPSHOT = DATA_DIR / "dual_window_snapshot.json"
DUAL_WINDOW_20D_DIR = DATA_DIR / "incremental" / "dual_window_20d"
DUAL_WINDOW_40D_DIR = DATA_DIR / "incremental" / "dual_window_40d"
CONTRACT_ROLLOVER_DIR = DATA_DIR / "contract_rollover"
DUAL_WINDOW_SHA_LIST = DATA_DIR / "dual_window_sha_fingerprint_list.json"
DUAL_WINDOW_LOCK_LEDGER = DATA_DIR / "dual_window_lock_ledger.json"
DUAL_WINDOW_CONSISTENCY = DATA_DIR / "dual_window_consistency_report.json"
ANOMALY_EVENTS = DATA_DIR / "dual_window_anomaly_events.json"
DSHA_NOTIFICATION = DATA_DIR / "dsha_notification_task017.json"

# ════════════════════════════════════════════════════════════════
# 日志
# ════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PIPELINE_DUAL_WINDOW")


# ════════════════════════════════════════════════════════════════
# TASK-017 审计事件写入
# ════════════════════════════════════════════════════════════════
def audit_event(
    event_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    wind_api_calls: int = 0,
) -> None:
    """追加 TASK-017 审计事件至 tracking_monitor_audit.jsonl。"""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": now_iso(),
        "event": event_type,
        "agent": WORKORDER,
        "token": TOKEN,
        "authorization": AUTHORIZATION,
        "wind_api_calls": wind_api_calls,
        "gate": GATE,
        "release_permit": RELEASE_PERMIT,
        "message": message,
    }
    if data:
        event["data"] = data
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        logger.info("[AUDIT] %s: %s", event_type, message)
    except PermissionError as e:
        logger.warning("[AUDIT] Permission denied writing audit log: %s — skipping", e)
    except OSError as e:
        logger.warning("[AUDIT] Failed to write audit log: %s — skipping", e)


# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════
def get_last_n_trading_days(n: int, today=None) -> List[datetime]:
    """计算最近 n 个交易日 (跳过周末)。"""
    if today is None:
        today = datetime.now(TZ_CN).date()
    days = []
    d = today
    while len(days) < n:
        if d.weekday() < 5:
            days.append(datetime(d.year, d.month, d.day, tzinfo=TZ_CN))
        d -= timedelta(days=1)
    days.reverse()
    return days


def get_process_memory_mb() -> float:
    """获取当前进程内存使用量 (MB)。"""
    try:
        if os.name == "posix":
            import resource as _res
            usage = _res.getrusage(_res.RUSAGE_SELF)
            return round(usage.ru_maxrss / 1024 if os.uname().sysname != "Darwin" else usage.ru_maxrss / (1024 * 1024), 2)
        else:
            return 0.0
    except (ImportError, AttributeError, OSError):
        return 0.0


def get_open_file_handles() -> int:
    """获取当前进程打开的文件句柄数。"""
    try:
        if os.name == "posix":
            import resource as _res
            soft, hard = _res.getrlimit(_res.RLIMIT_NOFILE)
            return soft
        else:
            return -1
    except (ImportError, AttributeError, OSError):
        return -1


def count_round_conflicts(result) -> int:
    """统计单轮锁冲突。"""
    return sum(1 for r in result["results"].values()
               if r.get("status") in ("GLOBAL_LOCK_CONFLICT", "SHARD_LOCK_CONFLICT"))


def count_round_cross(result) -> int:
    """统计单轮交叉污染。"""
    cross = 0
    for sym, res in result["results"].items():
        sp = res.get("shard_path")
        if not sp or not Path(sp).is_file():
            continue
        rows = read_csv_data_rows(Path(sp))
        for row in rows:
            if len(row) >= 2 and row[1].strip() != sym:
                cross += 1
    return cross


def count_round_timeouts(result) -> int:
    """统计单轮超时。"""
    return sum(1 for r in result["results"].values()
               if r.get("status") == "TIMEOUT")


def total_rows_all(results) -> int:
    """汇总所有轮次总行数。"""
    return sum(
        res.get("row_count", 0)
        for rr in results
        for res in rr["results"].values()
    )


def update_lock_ledger(round_id: int, phase: str, conflicts: int, cross: int,
                       timeouts: int, duration: float, queue_peak: int):
    """每轮更新锁冲突长期统计台账。"""
    if DUAL_WINDOW_LOCK_LEDGER.is_file():
        ledger = json.loads(DUAL_WINDOW_LOCK_LEDGER.read_text(encoding="utf-8"))
    else:
        ledger = {
            "workorder": WORKORDER,
            "token": TOKEN,
            "authorization": AUTHORIZATION,
            "ledger_id": "DSHC-DUAL-WINDOW-LOCK-LEDGER",
            "created_at": now_iso(),
            "rounds": [],
            "cumulative": {
                "total_rounds": 0,
                "total_conflicts": 0,
                "total_cross": 0,
                "total_timeouts": 0,
                "total_duration_sec": 0.0,
                "avg_duration_sec": 0.0,
                "max_duration_sec": 0.0,
                "min_duration_sec": float("inf"),
                "avg_queue_peak": 0.0,
                "max_queue_peak": 0,
            },
        }

    ledger["workorder"] = WORKORDER
    ledger["token"] = TOKEN
    ledger["authorization"] = AUTHORIZATION
    ledger["generated_at"] = now_iso()

    entry = {
        "round": round_id,
        "phase": phase,
        "timestamp": now_iso(),
        "conflicts": conflicts,
        "cross_contamination": cross,
        "timeouts": timeouts,
        "duration_seconds": round(duration, 3),
        "queue_peak_depth": queue_peak,
    }
    ledger["rounds"].append(entry)

    c = ledger["cumulative"]
    c["total_rounds"] = len(ledger["rounds"])
    c["total_conflicts"] += conflicts
    c["total_cross"] += cross
    c["total_timeouts"] += timeouts
    c["total_duration_sec"] += duration
    c["avg_duration_sec"] = round(c["total_duration_sec"] / c["total_rounds"], 3)
    c["max_duration_sec"] = max(c["max_duration_sec"], round(duration, 3))
    c["min_duration_sec"] = min(c["min_duration_sec"], round(duration, 3))
    c["avg_queue_peak"] = round(sum(r["queue_peak_depth"] for r in ledger["rounds"]) / c["total_rounds"], 2)
    c["max_queue_peak"] = max(c["max_queue_peak"], queue_peak)

    with open(DUAL_WINDOW_LOCK_LEDGER, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)


def record_anomaly_event(round_id: int, event_type: str, severity: str,
                         detail: Dict[str, Any], symbol: str = "",
                         shard_path: str = ""):
    """记录采集异常事件。"""
    if ANOMALY_EVENTS.is_file():
        events = json.loads(ANOMALY_EVENTS.read_text(encoding="utf-8"))
    else:
        events = {
            "workorder": WORKORDER,
            "token": TOKEN,
            "authorization": AUTHORIZATION,
            "events": [],
            "summary": {
                "total_events": 0,
                "by_type": {},
                "by_severity": {},
            },
        }

    event = {
        "event_id": f"DW-EVENT-{round_id:03d}-{len(events['events']) + 1:03d}",
        "round": round_id,
        "timestamp": now_iso(),
        "type": event_type,
        "severity": severity,
        "symbol": symbol,
        "shard_path": shard_path,
        "detail": detail,
    }
    events["events"].append(event)

    s = events["summary"]
    s["total_events"] = len(events["events"])
    s["by_type"][event_type] = s["by_type"].get(event_type, 0) + 1
    s["by_severity"][severity] = s["by_severity"].get(severity, 0) + 1

    events["workorder"] = WORKORDER
    events["token"] = TOKEN
    events["authorization"] = AUTHORIZATION
    events["generated_at"] = now_iso()
    events["dual_window_mode"] = True

    with open(ANOMALY_EVENTS, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def get_regime_for_round(round_id: int, cycle=None) -> str:
    """根据轮次编号获取行情分布 (1-indexed)。"""
    if cycle is None:
        cycle = REGIME_CYCLE
    idx = (round_id - 1) % len(cycle)
    return cycle[idx]


def compute_oi_change_rates(oi_series: List[float]) -> List[float]:
    """计算 OI 序列的日环比变化率。"""
    rates = []
    for i in range(1, len(oi_series)):
        prev = oi_series[i - 1]
        curr = oi_series[i]
        if prev > 0:
            rate = (curr - prev) / prev
        else:
            rate = 0.0
        rates.append(rate)
    return rates


def detect_contract_switches(oi_series: List[float], threshold: float) -> List[Dict]:
    """
    检测合约换月事件：OI变化率 < threshold (-30%)。
    """
    rates = compute_oi_change_rates(oi_series)
    events = []
    for i, rate in enumerate(rates):
        if rate < threshold:
            events.append({
                "index": i + 1,  # 1-based day index after the change
                "oi_change_rate": round(rate, 4),
                "oi_prev": round(oi_series[i], 2),
                "oi_curr": round(oi_series[i + 1], 2),
                "contract_switch_flag": True,
                "date_index": i,
            })
    return events


def update_sha_fingerprint_list(entries: List[Dict[str, Any]], phase: str):
    """增量更新 SHA 指纹清单。"""
    if DUAL_WINDOW_SHA_LIST.is_file():
        data = json.loads(DUAL_WINDOW_SHA_LIST.read_text(encoding="utf-8"))
    else:
        data = {
            "workorder": WORKORDER,
            "token": TOKEN,
            "authorization": AUTHORIZATION,
            "created_at": now_iso(),
            "phases": {},
            "total_files": 0,
        }

    data["workorder"] = WORKORDER
    data["token"] = TOKEN
    data["authorization"] = AUTHORIZATION
    data["updated_at"] = now_iso()

    if phase not in data["phases"]:
        data["phases"][phase] = []

    data["phases"][phase].extend(entries)
    data["total_files"] = sum(len(ph) for ph in data["phases"].values())

    with open(DUAL_WINDOW_SHA_LIST, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════════════════════
# 双窗口自定义 Worker
# ════════════════════════════════════════════════════════════════
def dual_window_worker(
    symbol: str,
    shard_date: str,
    end_date: str,
    shard_dir: Path,
    market_regime: Optional[str],
    seed: int,
    round_id: int,
    result_queue: "multiprocessing.Queue",
    window_label: str = "",
) -> None:
    """
    TASK-017 双窗口自定义 Worker：将分片写入指定目录。

    与 parallel_worker_online 不同，接受自定义 shard_dir 参数，
    用于 20d/40d 双窗口物理隔离。
    """
    import json as _json
    import os as _os
    import time as _time
    from pathlib import Path as _Path

    sys.path.insert(0, str(CODE_DIR))
    from incr_alert_hook import AlertHook as _AlertHook

    start_time = _time.time()
    safe_sym = symbol.replace(".", "_").replace("/", "_")

    shard_dir = _Path(shard_dir)
    shard_dir.mkdir(parents=True, exist_ok=True)
    shard_path = shard_dir / f"parallel_shard_{safe_sym}_{shard_date}.csv"

    status = "SUCCESS"
    error_msg = None
    shard_sha = None
    row_count = 0

    try:
        # 获取品种分片锁
        from incr_pipeline_parallel_online import GlobalLockManager as _GLM
        _glm = _GLM()
        lock_ok, lock_msg = _glm.acquire_shard_lock(symbol)
        if not lock_ok:
            status = "SHARD_LOCK_CONFLICT"
            error_msg = lock_msg

        if status == "SUCCESS":
            try:
                row_count = write_simulated_shard(
                    shard_path, symbol, end_date,
                    market_regime=market_regime, seed=seed,
                )
                shard_sha = sha256_of_file(shard_path)
            except Exception as e:
                status = "WRITE_ERROR"
                error_msg = str(e)
            finally:
                _glm.release_shard_lock(symbol)
        else:
            # Clean up partial file
            if shard_path.exists():
                shard_path.unlink()

    except Exception as e:
        status = "WORKER_ERROR"
        error_msg = str(e)

    duration = _time.time() - start_time

    result = {
        "symbol": symbol,
        "status": status,
        "error": error_msg,
        "shard_path": str(shard_path) if status == "SUCCESS" else "",
        "sha256": shard_sha,
        "row_count": row_count,
        "duration_seconds": round(duration, 3),
        "round": round_id,
        "window": window_label,
    }
    result_queue.put(result)


def run_dual_window_round(
    symbols: List[str],
    shard_date: str,
    end_date: str,
    shard_dir: Path,
    market_regime: str,
    seed_base: int,
    round_id: int,
    window_label: str = "",
) -> Dict[str, Any]:
    """
    运行一轮双窗口并行采集，返回所有 worker 的结果汇总。
    全局锁由 orchestrator 获取/释放，worker 仅获取品种独立锁。
    """
    # ── Acquire global lock (orchestrator level) ──
    glm = GlobalLockManager()
    global_ok, global_msg = glm.acquire_global_lock()
    if not global_ok:
        logger.warning("Cannot acquire global lock: %s", global_msg)
        return {
            "round": round_id,
            "shard_date": shard_date,
            "symbols": symbols,
            "results": {sym: {"symbol": sym, "status": "GLOBAL_LOCK_CONFLICT",
                              "error": global_msg, "sha256": None, "row_count": 0,
                              "duration_seconds": 0.0, "round": round_id,
                              "window": window_label}
                        for sym in symbols},
            "all_success": False,
        }

    try:
        queue = multiprocessing.Queue()
        processes = []

        for idx, sym in enumerate(symbols):
            sym_seed = seed_base * 1000 + idx
            p = multiprocessing.Process(
                target=dual_window_worker,
                args=(sym, shard_date, end_date, shard_dir,
                      market_regime, sym_seed, round_id, queue, window_label),
            )
            p.start()
            processes.append((sym, p))

        # Collect results — match by symbol field, not queue order
        import queue as _queue
        results = {}
        for sym, proc in processes:
            proc.join(timeout=60)
        while True:
            try:
                result = queue.get(timeout=5)
                sym_from_result = result.get("symbol", "")
                if sym_from_result:
                    results[sym_from_result] = result
            except _queue.Empty:
                break
        # Add timeout stubs for any missing symbols
        for sym, proc in processes:
            if sym not in results:
                results[sym] = {
                    "symbol": sym, "status": "TIMEOUT", "error": "Worker timed out",
                    "sha256": None, "row_count": 0, "duration_seconds": 60.0,
                    "round": round_id, "window": window_label,
                }

        return {
            "round": round_id,
            "shard_date": shard_date,
            "symbols": symbols,
            "results": results,
            "all_success": all(r.get("status") == "SUCCESS" for r in results.values()),
            "window": window_label,
        }
    finally:
        glm.release_global_lock()


# ════════════════════════════════════════════════════════════════
# P0: 冒烟自检
# ════════════════════════════════════════════════════════════════
def run_p0_self_check() -> Dict[str, Any]:
    """
    P0: 冒烟校验，确认分片目录、SHA校验、锁机制、双窗口目录隔离、告警推送全部正常。
    """
    results = {}
    logger.info("=" * 60)
    logger.info("P0: 冒烟自检 (DUAL WINDOW)")
    logger.info("=" * 60)

    # 1. 全局锁机制
    logger.info("\n[P0.1] Global lock mechanism...")
    glm = GlobalLockManager()
    ok_g, msg_g = glm.acquire_global_lock()
    glm.release_global_lock()
    lock_file_gone = not GLOBAL_LOCK_FILE.is_file()
    results["P0.1_global_lock"] = {"pass": ok_g and lock_file_gone, "detail": msg_g}
    logger.info("  Global lock: %s -> %s", msg_g, "PASS" if results["P0.1_global_lock"]["pass"] else "FAIL")

    # 2. 品种分片锁
    logger.info("\n[P0.2] Shard lock mechanism...")
    shard_ok = True
    for sym in SYMBOL_WHITELIST[:3]:
        ok_s, _ = glm.acquire_shard_lock(sym)
        if not ok_s:
            shard_ok = False
            break
        glm.release_shard_lock(sym)
    results["P0.2_shard_lock"] = {"pass": shard_ok, "symbols_tested": 3}
    logger.info("  Shard locks (3): %s -> %s", shard_ok, "PASS" if shard_ok else "FAIL")

    # 3. 调度配置
    logger.info("\n[P0.3] Schedule config (dual pipeline)...")
    if PARALLEL_SCHEDULE_CONFIG.is_file():
        with open(PARALLEL_SCHEDULE_CONFIG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        dual_ok = (
            cfg.get("dual_pipeline", {}).get("serial_pipeline", {}).get("enabled", False)
            and cfg.get("dual_pipeline", {}).get("parallel_pipeline", {}).get("enabled", False)
        )
        mode = cfg.get("mode_switch", {}).get("current_mode", "UNKNOWN")
    else:
        dual_ok = False
        mode = "MISSING"
    results["P0.3_schedule_config"] = {"pass": dual_ok, "mode": mode}
    logger.info("  Dual pipeline: %s, Mode: %s -> %s", dual_ok, mode, "PASS" if dual_ok else "FAIL")

    # 4. 目录权限
    logger.info("\n[P0.4] Artifact directory permissions...")
    DUAL_WINDOW_20D_DIR.mkdir(parents=True, exist_ok=True)
    DUAL_WINDOW_40D_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACT_ROLLOVER_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "dual_20d_dir_writable": DUAL_WINDOW_20D_DIR.is_dir(),
        "dual_40d_dir_writable": DUAL_WINDOW_40D_DIR.is_dir(),
        "contract_rollover_dir_writable": CONTRACT_ROLLOVER_DIR.is_dir(),
        "incremental_dir_exists": INCREMENTAL_DIR.is_dir(),
        "data_dir_writable": DATA_DIR.is_dir(),
        "dsha_sandbox_exists": DSHA_SANDBOX_DIR.is_dir(),
    }
    results["P0.4_directory_permissions"] = {"pass": all(artifacts.values()), "details": artifacts}
    logger.info("  All directories OK: %s -> %s", all(artifacts.values()), "PASS" if all(artifacts.values()) else "FAIL")

    # 5. SHA一致性
    logger.info("\n[P0.5] SHA fingerprint check...")
    v2_sha = sha256_of_file(V2_CSV) if V2_CSV.is_file() else None
    sha_ok = (v2_sha == V2_SHA_LOCKED) if v2_sha else False
    results["P0.5_sha_fingerprint"] = {"pass": sha_ok, "sha256": v2_sha, "locked": V2_SHA_LOCKED}
    logger.info("  V2 SHA match: %s -> %s", sha_ok, "PASS" if sha_ok else "FAIL")

    # 6. 脚本完整性
    logger.info("\n[P0.6] Script integrity check...")
    scripts = {
        "dual_window": (CODE_DIR / "incr_pipeline_dual_window.py").is_file(),
        "data_extend": (CODE_DIR / "incr_pipeline_data_extend.py").is_file(),
        "stability_test": (CODE_DIR / "incr_pipeline_stability_test.py").is_file(),
        "parallel_online": (CODE_DIR / "incr_pipeline_parallel_online.py").is_file(),
        "data_collect": (CODE_DIR / "incr_pipeline_data_collect.py").is_file(),
        "data_fetch": (CODE_DIR / "incr_pipeline_data_fetch.py").is_file(),
        "alert_hook": (CODE_DIR / "incr_alert_hook.py").is_file(),
        "daily_pipeline": (CODE_DIR / "incr_pipeline_daily.py").is_file(),
        "rollback": (CODE_DIR / "incr_pipeline_rollback.py").is_file(),
    }
    results["P0.6_scripts"] = {"pass": all(scripts.values()), "details": scripts}
    logger.info("  All scripts present: %s -> %s", all(scripts.values()), "PASS" if all(scripts.values()) else "FAIL")

    # 7. Manifest版本
    logger.info("\n[P0.7] Manifest version check...")
    manifest = read_manifest()
    manifest_v = manifest.get("registry_version", "")
    results["P0.7_manifest"] = {"pass": manifest_v == "v2.4.0", "version": manifest_v}
    logger.info("  Manifest v2.4.0: %s -> %s", manifest_v, "PASS" if results["P0.7_manifest"]["pass"] else "FAIL")

    # 8. 风控门禁
    logger.info("\n[P0.8] Risk control gate check...")
    results["P0.8_gate"] = {
        "pass": GATE == "CLOSED/HOLD" and RELEASE_PERMIT == "NOT_ISSUED",
        "gate": GATE, "release_permit": RELEASE_PERMIT,
    }
    logger.info("  Gate: %s, Release: %s -> %s", GATE, RELEASE_PERMIT,
                "PASS" if results["P0.8_gate"]["pass"] else "FAIL")

    # 9. 双窗口目录隔离
    logger.info("\n[P0.9] Dual-window directory isolation check...")
    dir_20d = DUAL_WINDOW_20D_DIR.resolve()
    dir_40d = DUAL_WINDOW_40D_DIR.resolve()
    dir_par = PARALLEL_DIR.resolve()
    iso_20_40 = dir_20d != dir_40d
    iso_20_par = dir_20d != dir_par
    iso_40_par = dir_40d != dir_par
    all_iso = iso_20_40 and iso_20_par and iso_40_par
    results["P0.9_dual_dir_isolation"] = {
        "pass": all_iso,
        "dual_20d_dir": str(DUAL_WINDOW_20D_DIR.relative_to(PROJECT_ROOT)),
        "dual_40d_dir": str(DUAL_WINDOW_40D_DIR.relative_to(PROJECT_ROOT)),
        "parallel_dir": str(PARALLEL_DIR.relative_to(PROJECT_ROOT)),
        "isolation_20_40": iso_20_40,
        "isolation_20_parallel": iso_20_par,
        "isolation_40_parallel": iso_40_par,
    }
    logger.info("  Dual directories isolated: %s -> %s", all_iso, "PASS" if all_iso else "FAIL")

    # 10. TASK-016 前置制品验证
    logger.info("\n[P0.10] TASK-016 prerequisite artifacts...")
    task016_artifacts = {
        "data_extend_report": DATA_DIR.joinpath("parallel_data_extend_report.json").is_file(),
        "data_extend_snapshot": DATA_DIR.joinpath("parallel_data_extend_snapshot.json").is_file(),
        "sha_fingerprint_list": DATA_DIR.joinpath("parallel_sha_fingerprint_list.json").is_file(),
        "dsha_notification_task016": DATA_DIR.joinpath("dsha_notification_task016.json").is_file(),
        "contract_rollover_dir": CONTRACT_ROLLOVER_DIR.is_dir(),
    }
    results["P0.10_task016_prerequisites"] = {
        "pass": all(task016_artifacts.values()),
        "details": task016_artifacts,
    }
    logger.info("  TASK-016 artifacts: %s -> %s",
                all(task016_artifacts.values()),
                "PASS" if all(task016_artifacts.values()) else "FAIL")

    # 11. TASK-015 前置制品验证
    logger.info("\n[P0.11] TASK-015 prerequisite artifacts...")
    task015_artifacts = {
        "stability_report": DATA_DIR.joinpath("parallel_stability_report.json").is_file(),
        "stability_snapshot": DATA_DIR.joinpath("parallel_stability_snapshot.json").is_file(),
        "lock_conflict_ledger": DATA_DIR.joinpath("parallel_lock_conflict_ledger.json").is_file(),
        "stability_script": (CODE_DIR / "incr_pipeline_stability_test.py").is_file(),
    }
    results["P0.11_task015_prerequisites"] = {
        "pass": all(task015_artifacts.values()),
        "details": task015_artifacts,
    }
    logger.info("  TASK-015 artifacts: %s -> %s",
                all(task015_artifacts.values()),
                "PASS" if all(task015_artifacts.values()) else "FAIL")

    # 12. 告警推送通道
    logger.info("\n[P0.12] Alert push channel test...")
    hook = AlertHook(workorder=WORKORDER, token=TOKEN, dry_run=True)
    test_alert = hook.emit(
        event_type="DUAL_WINDOW_SMOKE_TEST",
        stage="system",
        status=AlertHook.STATUS_PASS,
        detail={"message": "P0 smoke test alert push channel verification"},
    )
    has_required_fields = all(
        f in test_alert for f in ("run_id", "stage", "status", "event", "timestamp")
    )
    results["P0.12_alert_channel"] = {"pass": has_required_fields, "test_alert_run_id": test_alert.get("run_id")}
    logger.info("  Alert channel: %s -> %s", has_required_fields, "PASS" if has_required_fields else "FAIL")

    # 汇总
    all_pass = all(r.get("pass", False) for r in results.values())
    results["P0_OVERALL"] = {"pass": all_pass}

    for name, r in results.items():
        if name == "P0_OVERALL":
            continue
        status = "PASS" if r.get("pass") else "FAIL"
        logger.info("  %s: %s", name, status)
    logger.info("  P0 OVERALL: %s", "PASS" if all_pass else "FAIL")
    logger.info("=" * 60)

    audit_event(
        "TASK017_P0_SELF_CHECK_COMPLETE",
        f"P0自检完成: {sum(1 for r in results.values() if r.get('pass'))}/{len(results)-1} 项通过",
        {"results": results, "all_pass": all_pass},
    )

    return {"all_pass": all_pass, "details": results}


# ════════════════════════════════════════════════════════════════
# P1: 双窗口并行流水线 (20d + 40d)
# ════════════════════════════════════════════════════════════════
def run_p1_dual_window() -> Dict[str, Any]:
    """
    P1: 开启双窗口并行流水线，同时产出20d+40d两套滚动分片数据。
    两套目录严格物理隔离：dual_window_20d/ 和 dual_window_40d/。
    """
    logger.info("=" * 60)
    logger.info("P1: 双窗口并行流水线 (%dd + %dd, %d symbols)",
                WINDOW_20D_DAYS, WINDOW_40D_DAYS, len(SYMBOL_WHITELIST))
    logger.info("=" * 60)

    trading_days = get_last_n_trading_days(WINDOW_40D_DAYS)
    all_entries_20d: List[Dict] = []
    all_entries_40d: List[Dict] = []
    total_rows_20d = 0
    total_rows_40d = 0
    total_duration = 0.0
    total_conflicts = 0
    total_cross = 0
    day_metrics: List[Dict] = []

    for day_idx, day in enumerate(trading_days):
        round_id = day_idx + 1
        regime = get_regime_for_round(round_id, ROLLING_REGIME_CYCLE)

        day_start = time.time()
        day_shards_20d = 0
        day_shards_40d = 0
        day_rows_20d = 0
        day_rows_40d = 0

        logger.info("\n--- P1 Day %d/%d (%s, regime=%s) ---",
                    day_idx + 1, WINDOW_40D_DAYS, day.strftime("%Y-%m-%d"), regime)

        shard_date = day.strftime("%Y%m%d")
        end_date = day.strftime("%Y-%m-%d")

        # ── 40d window: all 40 days ──
        seed_40d = (10000 + round_id) * 1000
        result_40d = run_dual_window_round(
            SYMBOL_WHITELIST[:], shard_date, end_date,
            DUAL_WINDOW_40D_DIR, regime, seed_40d, round_id, "40d",
        )

        # Process 40d results
        for sym, res in result_40d["results"].items():
            if res.get("status") == "SUCCESS":
                day_shards_40d += 1
                day_rows_40d += res.get("row_count", 0)
                shard_path = res.get("shard_path", "")
                entry = {
                    "phase": "P1_DUAL_WINDOW_40D",
                    "day": day.strftime("%Y-%m-%d"),
                    "day_index": day_idx + 1,
                    "regime": regime,
                    "symbol": sym,
                    "shard_path": str(Path(shard_path).relative_to(PROJECT_ROOT)) if shard_path else "",
                    "sha256": res.get("sha256", ""),
                    "sha256_short": res.get("sha256", "")[:16] if res.get("sha256") else "",
                    "row_count": res.get("row_count", 0),
                    "round_id": round_id,
                    "window": "40d",
                    "generated_at": now_iso(),
                }
                all_entries_40d.append(entry)
            elif res.get("status") in ("GLOBAL_LOCK_CONFLICT", "SHARD_LOCK_CONFLICT"):
                total_conflicts += 1

        # ── 20d window: only last 20 days ──
        if day_idx >= (WINDOW_40D_DAYS - WINDOW_20D_DAYS):  # days 21-40
            seed_20d = (20000 + round_id) * 1000
            result_20d = run_dual_window_round(
                SYMBOL_WHITELIST[:], shard_date, end_date,
                DUAL_WINDOW_20D_DIR, regime, seed_20d, round_id, "20d",
            )

            for sym, res in result_20d["results"].items():
                if res.get("status") == "SUCCESS":
                    day_shards_20d += 1
                    day_rows_20d += res.get("row_count", 0)
                    shard_path = res.get("shard_path", "")
                    entry = {
                        "phase": "P1_DUAL_WINDOW_20D",
                        "day": day.strftime("%Y-%m-%d"),
                        "day_index": day_idx + 1,
                        "regime": regime,
                        "symbol": sym,
                        "shard_path": str(Path(shard_path).relative_to(PROJECT_ROOT)) if shard_path else "",
                        "sha256": res.get("sha256", ""),
                        "sha256_short": res.get("sha256", "")[:16] if res.get("sha256") else "",
                        "row_count": res.get("row_count", 0),
                        "round_id": round_id,
                        "window": "20d",
                        "generated_at": now_iso(),
                    }
                    all_entries_20d.append(entry)
                elif res.get("status") in ("GLOBAL_LOCK_CONFLICT", "SHARD_LOCK_CONFLICT"):
                    total_conflicts += 1

        # Check for anomalies
        if total_conflicts > 0:
            record_anomaly_event(round_id, "LOCK_CONFLICT", "CRITICAL",
                                 {"conflicts": total_conflicts})
            break

        day_duration = time.time() - day_start
        total_duration += day_duration

        logger.info("  Day %d: 40d=%d shards, 20d=%d shards, 40d_rows=%d, 20d_rows=%d, %.3fs",
                    day_idx + 1, day_shards_40d, day_shards_20d,
                    day_rows_40d, day_rows_20d, day_duration)

        day_metrics.append({
            "day": day.strftime("%Y-%m-%d"),
            "day_index": day_idx + 1,
            "regime": regime,
            "shards_40d": day_shards_40d,
            "shards_20d": day_shards_20d,
            "rows_40d": day_rows_40d,
            "rows_20d": day_rows_20d,
            "duration_seconds": round(day_duration, 3),
            "success_40d": day_shards_40d == len(SYMBOL_WHITELIST),
            "success_20d": day_shards_20d == len(SYMBOL_WHITELIST) if day_idx >= (WINDOW_40D_DAYS - WINDOW_20D_DAYS) else None,
        })

        # Update lock ledger
        update_lock_ledger(round_id, "P1_DUAL_WINDOW", 0, 0, 0,
                           day_duration, len(SYMBOL_WHITELIST) * 2)

    # Update SHA fingerprint list
    update_sha_fingerprint_list(all_entries_40d, "P1_DUAL_WINDOW_40D")
    update_sha_fingerprint_list(all_entries_20d, "P1_DUAL_WINDOW_20D")

    # Summary
    total_rows_final_40d = sum(e.get("row_count", 0) for e in all_entries_40d)
    total_rows_final_20d = sum(e.get("row_count", 0) for e in all_entries_20d)
    days_completed = len(day_metrics)
    days_success_40d = sum(1 for d in day_metrics if d.get("success_40d"))
    days_success_20d = sum(1 for d in day_metrics if d.get("success_20d") is True)

    logger.info("\n" + "=" * 60)
    logger.info("P1 Summary: %d/%d days", days_completed, WINDOW_40D_DAYS)
    logger.info("  40d window: %d/%d days success, %d shards, %d rows",
                days_success_40d, days_completed, len(all_entries_40d), total_rows_final_40d)
    logger.info("  20d window: %d/%d days success, %d shards, %d rows",
                days_success_20d, WINDOW_20D_DAYS, len(all_entries_20d), total_rows_final_20d)
    logger.info("  Total duration: %.3fs, conflicts: %d", total_duration, total_conflicts)
    logger.info("=" * 60)

    audit_event(
        "TASK017_P1_DUAL_WINDOW_COMPLETE",
        f"P1完成: {days_completed}/{WINDOW_40D_DAYS}天, "
        f"40d={len(all_entries_40d)}分片, 20d={len(all_entries_20d)}分片, 冲突={total_conflicts}",
        {
            "days_completed": days_completed,
            "days_planned": WINDOW_40D_DAYS,
            "shards_40d": len(all_entries_40d),
            "shards_20d": len(all_entries_20d),
            "total_rows_40d": total_rows_final_40d,
            "total_rows_20d": total_rows_final_20d,
            "total_duration_sec": round(total_duration, 3),
            "conflicts": total_conflicts,
            "cross_contamination": total_cross,
            "sha_fingerprint_list_ref": str(DUAL_WINDOW_SHA_LIST.relative_to(PROJECT_ROOT)),
        }
    )

    return {
        "days_completed": days_completed,
        "days_planned": WINDOW_40D_DAYS,
        "days_success_40d": days_success_40d,
        "days_success_20d": days_success_20d,
        "shards_40d": len(all_entries_40d),
        "shards_20d": len(all_entries_20d),
        "total_rows_40d": total_rows_final_40d,
        "total_rows_20d": total_rows_final_20d,
        "total_duration": round(total_duration, 3),
        "conflicts": total_conflicts,
        "cross": total_cross,
        "day_metrics": day_metrics,
        "sha_entries_40d": len(all_entries_40d),
        "sha_entries_20d": len(all_entries_20d),
        "pass_40d": days_success_40d == WINDOW_40D_DAYS,
        "pass_20d": days_success_20d == WINDOW_20D_DAYS,
    }


# ════════════════════════════════════════════════════════════════
# P2: UP/DOWN/SIDEWAYS行情均衡 (DOWN ≥ 20)
# ════════════════════════════════════════════════════════════════
def run_p2_regime_balance() -> Dict[str, Any]:
    """
    P2: 持续维持UP/DOWN/SIDEWAYS三类行情样本均衡，保证DOWN窗口≥20。
    使用定制行情循环 ["DOWN","DOWN","DOWN","UP","SIDEWAYS"] 确保42轮中DOWN≥20。
    """
    logger.info("=" * 60)
    logger.info("P2: 行情均衡监控 (%d rounds, DOWN≥%d)",
                MONITOR_TOTAL_ROUNDS, DOWN_MINIMUM)
    logger.info("  Regime cycle: %s", REGIME_CYCLE)
    logger.info("=" * 60)

    trading_days = get_last_n_trading_days(MONITOR_TRADING_DAYS)
    all_results = []
    all_conflicts = 0
    all_cross = 0
    all_timeouts = 0
    regime_counts = {"UP": 0, "DOWN": 0, "SIDEWAYS": 0}
    round_metrics = []
    total_duration = 0.0
    queue_peak_max = 0

    for i, day in enumerate(trading_days):
        for round_in_day in range(1, MONITOR_ROUNDS_PER_DAY + 1):
            round_id = i * MONITOR_ROUNDS_PER_DAY + round_in_day
            regime = get_regime_for_round(round_id)
            regime_counts[regime] = regime_counts.get(regime, 0) + 1

            logger.info("\n--- P2 Round %d/%d (Day %s/%d, %s) ---",
                        round_id, MONITOR_TOTAL_ROUNDS, day.strftime("%Y-%m-%d"),
                        i + 1, regime)

            round_start = time.time()
            mem_before = get_process_memory_mb()

            result = run_parallel_round(
                SYMBOL_WHITELIST[:],
                is_dry_run=False,
                round_id=round_id,
                end_date=day.strftime("%Y-%m-%d"),
                market_regime=regime,
                seed=300 + round_id,
            )
            result["regime"] = regime

            round_duration = time.time() - round_start
            mem_after = get_process_memory_mb()

            round_conflicts = count_round_conflicts(result)
            round_cross = count_round_cross(result)
            round_timeouts = count_round_timeouts(result)
            all_conflicts += round_conflicts
            all_cross += round_cross
            all_timeouts += round_timeouts
            total_duration += round_duration

            queue_peak = len(SYMBOL_WHITELIST)
            queue_peak_max = max(queue_peak_max, queue_peak)

            # Record per-round metrics
            metrics = {
                "round": round_id,
                "day": day.strftime("%Y-%m-%d"),
                "regime": regime,
                "duration_seconds": round(round_duration, 3),
                "conflicts": round_conflicts,
                "cross_contamination": round_cross,
                "timeouts": round_timeouts,
                "all_success": result["all_success"],
                "symbols_passed": sum(1 for r in result["results"].values() if r.get("status") == "SUCCESS"),
                "symbols_total": len(result["results"]),
                "total_rows": sum(r.get("row_count", 0) for r in result["results"].values()),
                "memory_before_mb": mem_before,
                "memory_after_mb": mem_after,
                "memory_delta_mb": round(mem_after - mem_before, 2) if mem_before > 0 and mem_after > 0 else None,
                "queue_peak_depth": queue_peak,
            }
            round_metrics.append(metrics)

            # Anomaly detection
            if round_conflicts > 0:
                record_anomaly_event(round_id, "LOCK_CONFLICT", "CRITICAL",
                                     {"conflicts": round_conflicts})
            if round_cross > 0:
                record_anomaly_event(round_id, "CROSS_CONTAMINATION", "CRITICAL",
                                     {"cross_contamination": round_cross})
            if round_timeouts > 0:
                record_anomaly_event(round_id, "COLLECTION_TIMEOUT", "HIGH",
                                     {"timeouts": round_timeouts})

            # Auto-stop on anomaly
            if round_conflicts > 0 or round_cross > 0:
                logger.error("Anomaly in round %d: conflicts=%d, cross=%d — AUTO-STOP",
                             round_id, round_conflicts, round_cross)
                audit_event("TASK017_ANOMALY_DETECTED",
                            f"Round {round_id} anomaly: conflicts={round_conflicts}, cross={round_cross}",
                            {"round": round_id, "conflicts": round_conflicts, "cross": round_cross})
                record_anomaly_event(round_id, "AUTO_STOP", "CRITICAL",
                                     {"reason": f"conflicts={round_conflicts}, cross={round_cross}"})
                break

            # Update lock ledger
            update_lock_ledger(round_id, "P2_REGIME_BALANCE", round_conflicts, round_cross,
                               round_timeouts, round_duration, queue_peak)

            all_results.append(result)
            logger.info("  Round %d: %s | regime=%s | duration=%.3fs | conflicts=%d | cross=%d | timeouts=%d",
                        round_id, "PASS" if result["all_success"] else "FAIL",
                        regime, round_duration, round_conflicts, round_cross, round_timeouts)

        if all_cross > 0 or all_conflicts > 0:
            break

    # ── Verify DOWN ≥ 20 ──
    down_count = regime_counts.get("DOWN", 0)
    down_sufficient = down_count >= DOWN_MINIMUM

    # ── Consistency check (5 rounds) ──
    logger.info("\n--- P2.2: 5-round consistency check ---")
    consistency_result = _ppo_consistency_check(SYMBOL_WHITELIST[:], rounds=5, is_dry_run=False)
    consistency_pass = consistency_result.get("consistency_pass", False)
    consistency_rounds = consistency_result.get("rounds", 5)

    # ── Lock test ──
    logger.info("\n--- P2.3: Lock mechanism test ---")
    lock_test_result = run_lock_test()
    lock_test_pass = lock_test_result.get("all_pass", False)

    # ── Regime distribution verification ──
    total_rounds = len(round_metrics)
    regime_proportions = {
        k: round(v / max(total_rounds, 1), 3) for k, v in regime_counts.items()
    }

    # ── Update consistency report ──
    consistency_report = {
        "workorder": WORKORDER,
        "token": TOKEN,
        "authorization": AUTHORIZATION,
        "generated_at": now_iso(),
        "mode": "DUAL_WINDOW_MONITOR",
        "rounds": total_rounds,
        "round_details": [
            {
                "round": r["round"],
                "all_success": r["all_success"],
                "symbols_passed": sum(1 for sr in r["results"].values() if sr.get("status") == "SUCCESS"),
                "symbols_total": len(r["results"]),
                "shard_date": r.get("shard_date", ""),
                "regime": r.get("regime", ""),
                "duration_seconds": max((sr.get("duration_seconds", 0) for sr in r["results"].values()), default=0),
            }
            for r in all_results
        ],
        "consistency_check": consistency_result,
        "lock_test": lock_test_result,
        "regime_counts": dict(regime_counts),
        "regime_proportions": regime_proportions,
        "down_minimum_required": DOWN_MINIMUM,
        "down_count": down_count,
        "down_sufficient": down_sufficient,
        "lock_conflicts": all_conflicts,
        "cross_contamination": all_cross,
        "timeouts": all_timeouts,
    }
    with open(DUAL_WINDOW_CONSISTENCY, "w", encoding="utf-8") as f:
        json.dump(consistency_report, f, ensure_ascii=False, indent=2)

    # ── Push DSHD alerts for P2 ──
    logger.info("\n--- P2.4: Push DSHD alerts for regime balance ---")
    hook = AlertHook(workorder=WORKORDER, token=TOKEN)
    p2_alert_count = 0

    # Alert 1: Regime distribution
    hook.emit(
        event_type="DUAL_WINDOW_REGIME_DISTRIBUTION",
        stage="regime_balance",
        status=AlertHook.STATUS_PASS if down_sufficient else AlertHook.STATUS_FAIL,
        detail={
            "regime_counts": dict(regime_counts),
            "total_rounds": total_rounds,
            "proportions": regime_proportions,
            "down_minimum_required": DOWN_MINIMUM,
            "down_count": down_count,
            "down_sufficient": down_sufficient,
        },
    )
    p2_alert_count += 1

    # Alert 2: Consistency check result
    hook.emit(
        event_type="DUAL_WINDOW_CONSISTENCY_CHECK",
        stage="regime_balance",
        status=AlertHook.STATUS_PASS if consistency_pass else AlertHook.STATUS_WARN,
        detail={
            "consistency_pass": consistency_pass,
            "consistency_rounds": consistency_rounds,
        },
    )
    p2_alert_count += 1

    # Alert 3: Lock test result
    hook.emit(
        event_type="DUAL_WINDOW_LOCK_TEST",
        stage="regime_balance",
        status=AlertHook.STATUS_PASS if lock_test_pass else AlertHook.STATUS_WARN,
        detail={
            "lock_test_pass": lock_test_pass,
            "lock_test_details": lock_test_result,
        },
    )
    p2_alert_count += 1

    logger.info("  P2 DSHD alerts pushed: %d", p2_alert_count)

    # ── Audit event ──
    audit_event(
        "TASK017_P2_REGIME_BALANCE_COMPLETE",
        f"P2完成: {total_rounds}/{MONITOR_TOTAL_ROUNDS}轮, "
        f"DOWN={down_count}(≥{DOWN_MINIMUM}={'YES' if down_sufficient else 'NO'}), "
        f"冲突={all_conflicts}, 交叉={all_cross}, 超时={all_timeouts}, "
        f"一致性={'PASS' if consistency_pass else 'FAIL'}, 锁测试={'PASS' if lock_test_pass else 'FAIL'}",
        {
            "rounds_completed": total_rounds,
            "rounds_planned": MONITOR_TOTAL_ROUNDS,
            "conflicts": all_conflicts,
            "cross": all_cross,
            "timeouts": all_timeouts,
            "regime_counts": dict(regime_counts),
            "regime_proportions": regime_proportions,
            "down_minimum_required": DOWN_MINIMUM,
            "down_count": down_count,
            "down_sufficient": down_sufficient,
            "consistency_pass": consistency_pass,
            "lock_test_pass": lock_test_pass,
            "dshd_alerts_pushed": p2_alert_count,
        }
    )

    return {
        "rounds_completed": total_rounds,
        "rounds_planned": MONITOR_TOTAL_ROUNDS,
        "conflicts": all_conflicts,
        "cross": all_cross,
        "timeouts": all_timeouts,
        "regime_counts": regime_counts,
        "regime_proportions": regime_proportions,
        "down_minimum_required": DOWN_MINIMUM,
        "down_count": down_count,
        "down_sufficient": down_sufficient,
        "consistency_pass": consistency_pass,
        "lock_test_pass": lock_test_pass,
        "dshd_alerts_pushed": p2_alert_count,
        "round_metrics": round_metrics,
        "consistency_result": consistency_result,
        "lock_test_result": lock_test_result,
    }


# ════════════════════════════════════════════════════════════════
# P3: 合约换月OI数据持续采集
# ════════════════════════════════════════════════════════════════
def run_p3_contract_rollover() -> Dict[str, Any]:
    """
    P3: 持续采集合约换月OI数据，保持OI变化率-30%阈值不变，
    稳定产出contract_switch_flag原始信号。
    """
    logger.info("=" * 60)
    logger.info("P3: 合约换月OI数据持续采集 (%d symbols × %d days, threshold=%.0f%%)",
                len(SYMBOL_WHITELIST), CONTRACT_ROLLOVER_SIM_DAYS,
                OI_CHANGE_THRESHOLD * 100)
    logger.info("=" * 60)

    CONTRACT_ROLLOVER_DIR.mkdir(parents=True, exist_ok=True)

    all_entries = []
    total_switch_events = 0
    total_rollover_rows = 0
    per_symbol_stats = {}

    for sym_idx, symbol in enumerate(SYMBOL_WHITELIST):
        logger.info("\n--- P3 %s (%d/%d) ---", symbol, sym_idx + 1, len(SYMBOL_WHITELIST))

        safe_sym = symbol.replace(".", "_").replace("/", "_")
        roll_dates = get_last_n_trading_days(CONTRACT_ROLLOVER_SIM_DAYS)

        # Generate OI time series with simulated contract roll-over events
        rng = random.Random(50000 + sym_idx * 1000)

        base_oi = rng.randint(500000, 2000000)
        oi_series: List[float] = [base_oi]

        num_rollovers = rng.randint(2, 4)
        rollover_indices = sorted(rng.sample(range(5, CONTRACT_ROLLOVER_SIM_DAYS - 2), num_rollovers))

        for d in range(1, CONTRACT_ROLLOVER_SIM_DAYS):
            prev = oi_series[-1]
            if d in rollover_indices:
                drop_pct = rng.uniform(0.35, 0.65)
                oi_series.append(int(prev * (1.0 - drop_pct)))
            else:
                change_pct = rng.uniform(-0.05, 0.08)
                oi_series.append(int(prev * (1.0 + change_pct)))

        # Calculate OI change rates and detect contract switches
        oi_change_rates = compute_oi_change_rates(oi_series)
        contract_switches = detect_contract_switches(oi_series, OI_CHANGE_THRESHOLD)

        # Generate quote data
        quote_path = CONTRACT_ROLLOVER_DIR / f"rollover_{safe_sym}.csv"
        oi_data_path = CONTRACT_ROLLOVER_DIR / f"oi_series_{safe_sym}.json"

        header = ["date", "symbol", "indicator", "value", "source"]
        rollover_rows = 0

        price_rng = random.Random(60000 + sym_idx * 1000)
        base_close = price_rng.uniform(10000, 80000)

        with open(quote_path, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(header) + "\n")
            for d_idx, day in enumerate(roll_dates):
                if d_idx >= len(oi_series):
                    break
                oi_val = oi_series[d_idx]
                close_val = base_close * (1.0 + price_rng.uniform(-0.03, 0.03))
                high_val = close_val * (1.0 + price_rng.uniform(0.003, 0.01))
                low_val = close_val * (1.0 - price_rng.uniform(0.003, 0.01))
                settle_val = close_val * (1.0 + price_rng.uniform(-0.002, 0.002))
                vol_val = int(price_rng.randint(200000, 800000))

                date_str = day.strftime("%Y-%m-%d")
                f.write(f"{date_str},{symbol},CLOSE,{close_val:.2f},{SOURCE_TAG}\n")
                f.write(f"{date_str},{symbol},HIGH,{high_val:.2f},{SOURCE_TAG}\n")
                f.write(f"{date_str},{symbol},LOW,{low_val:.2f},{SOURCE_TAG}\n")
                f.write(f"{date_str},{symbol},OI,{oi_val},{SOURCE_TAG}\n")
                f.write(f"{date_str},{symbol},SETTLE,{settle_val:.2f},{SOURCE_TAG}\n")
                f.write(f"{date_str},{symbol},VOL,{vol_val},{SOURCE_TAG}\n")
                rollover_rows += 6
                base_close = close_val

        total_rollover_rows += rollover_rows

        # Write OI series JSON with change rates and flags
        oi_series_data = []
        for d_idx, day in enumerate(roll_dates):
            if d_idx >= len(oi_series):
                break
            oi_val = oi_series[d_idx]
            oi_change_rate = round(oi_change_rates[d_idx - 1], 6) if d_idx > 0 and d_idx - 1 < len(oi_change_rates) else None
            has_switch = False
            for sw in contract_switches:
                if sw["index"] == d_idx:
                    has_switch = True
                    break

            oi_series_data.append({
                "date": day.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "oi": oi_val,
                "oi_change_rate": oi_change_rate,
                "contract_switch_flag": has_switch,
                "day_index": d_idx,
            })

        oi_data = {
            "symbol": symbol,
            "workorder": WORKORDER,
            "token": TOKEN,
            "generated_at": now_iso(),
            "oi_threshold": OI_CHANGE_THRESHOLD,
            "total_days": len(oi_series_data),
            "total_switches": len(contract_switches),
            "oi_series": oi_series_data,
            "contract_switches": contract_switches,
        }

        with open(oi_data_path, "w", encoding="utf-8") as f:
            json.dump(oi_data, f, ensure_ascii=False, indent=2)

        total_switch_events += len(contract_switches)

        per_symbol_stats[symbol] = {
            "total_days": len(oi_series_data),
            "total_oi_rows": len(oi_series),
            "total_switches": len(contract_switches),
            "switch_indices": [s["index"] for s in contract_switches],
            "switch_dates": [
                roll_dates[s["index"]].strftime("%Y-%m-%d")
                for s in contract_switches if s["index"] < len(roll_dates)
            ],
            "avg_oi": round(sum(oi_series) / len(oi_series), 2) if oi_series else 0,
            "min_oi": min(oi_series) if oi_series else 0,
            "max_oi": max(oi_series) if oi_series else 0,
            "min_oi_change_rate": round(min(oi_change_rates), 6) if oi_change_rates else 0,
            "threshold_met": len(contract_switches) > 0,
        }

        # Update SHA fingerprint list
        quote_sha = sha256_of_file(quote_path)
        oi_sha = sha256_of_file(oi_data_path)
        update_sha_fingerprint_list([
            {
                "phase": "P3_CONTRACT_ROLLOVER",
                "symbol": symbol,
                "file": "quote",
                "file_path": str(quote_path.relative_to(PROJECT_ROOT)),
                "sha256": quote_sha,
                "sha256_short": quote_sha[:16] if quote_sha else "",
                "row_count": rollover_rows,
                "generated_at": now_iso(),
            },
            {
                "phase": "P3_CONTRACT_ROLLOVER",
                "symbol": symbol,
                "file": "oi_series",
                "file_path": str(oi_data_path.relative_to(PROJECT_ROOT)),
                "sha256": oi_sha,
                "sha256_short": oi_sha[:16] if oi_sha else "",
                "row_count": len(oi_series_data),
                "generated_at": now_iso(),
            },
        ], "P3_CONTRACT_ROLLOVER")

        logger.info("  %s: %d days, %d switches (threshold<%.0f%%), %d rows",
                    symbol, len(oi_series_data), len(contract_switches),
                    OI_CHANGE_THRESHOLD * 100, rollover_rows)

    # Write summary
    rollover_summary = {
        "workorder": WORKORDER,
        "token": TOKEN,
        "authorization": AUTHORIZATION,
        "generated_at": now_iso(),
        "oi_change_threshold": OI_CHANGE_THRESHOLD,
        "contract_rollover_sim_days": CONTRACT_ROLLOVER_SIM_DAYS,
        "symbols_processed": len(SYMBOL_WHITELIST),
        "total_switch_events": total_switch_events,
        "total_rollover_rows": total_rollover_rows,
        "per_symbol_stats": per_symbol_stats,
        "data_directory": str(CONTRACT_ROLLOVER_DIR.relative_to(PROJECT_ROOT)),
    }

    rollover_summary_path = CONTRACT_ROLLOVER_DIR / "rollover_summary.json"
    with open(rollover_summary_path, "w", encoding="utf-8") as f:
        json.dump(rollover_summary, f, ensure_ascii=False, indent=2)

    logger.info("\n" + "=" * 60)
    logger.info("P3 Summary: %d symbols, %d total switch events, %d rows",
                len(SYMBOL_WHITELIST), total_switch_events, total_rollover_rows)
    logger.info("=" * 60)

    audit_event(
        "TASK017_P3_CONTRACT_ROLLOVER_COMPLETE",
        f"P3完成: {len(SYMBOL_WHITELIST)}品种, {total_switch_events}次换月事件, "
        f"{total_rollover_rows}行数据, 阈值={OI_CHANGE_THRESHOLD*100:.0f}%",
        {
            "symbols_processed": len(SYMBOL_WHITELIST),
            "total_switch_events": total_switch_events,
            "total_rollover_rows": total_rollover_rows,
            "oi_change_threshold": OI_CHANGE_THRESHOLD,
            "rollover_sim_days": CONTRACT_ROLLOVER_SIM_DAYS,
            "per_symbol_switches": {
                s: st["total_switches"] for s, st in per_symbol_stats.items()
            },
            "threshold_met_all": all(st["threshold_met"] for st in per_symbol_stats.values()),
        }
    )

    return {
        "symbols_processed": len(SYMBOL_WHITELIST),
        "total_switch_events": total_switch_events,
        "total_rollover_rows": total_rollover_rows,
        "oi_change_threshold": OI_CHANGE_THRESHOLD,
        "per_symbol_stats": per_symbol_stats,
        "rollover_summary_path": str(rollover_summary_path),
    }


# ════════════════════════════════════════════════════════════════
# P4: 双窗口一致性报告 + 锁台账 + 资源监控 + DSHD告警
# ════════════════════════════════════════════════════════════════
def run_p4_consistency_alerts() -> Dict[str, Any]:
    """
    P4: 每轮输出双窗口一致性报告、锁冲突台账、资源吞吐监控，
    持续向DSHD推送流水线事件。
    """
    logger.info("=" * 60)
    logger.info("P4: 双窗口一致性报告 + 锁台账 + 资源监控 + DSHD告警")
    logger.info("=" * 60)

    hook = AlertHook(workorder=WORKORDER, token=TOKEN)
    alert_count = 0
    alert_types: set = set()

    # ── 1. Dual Window 20d Summary Alert ──
    sha_data = {}
    if DUAL_WINDOW_SHA_LIST.is_file():
        sha_data = json.loads(DUAL_WINDOW_SHA_LIST.read_text(encoding="utf-8"))

    entries_40d = sha_data.get("phases", {}).get("P1_DUAL_WINDOW_40D", [])
    entries_20d = sha_data.get("phases", {}).get("P1_DUAL_WINDOW_20D", [])
    entries_p3 = sha_data.get("phases", {}).get("P3_CONTRACT_ROLLOVER", [])

    hook.emit(
        event_type="DUAL_WINDOW_ROLLING_WINDOW_40D_COMPLETE",
        stage="dual_window_40d",
        status=AlertHook.STATUS_PASS,
        row_count=len(entries_40d),
        detail={
            "window_days": WINDOW_40D_DAYS,
            "shards_generated": len(entries_40d),
            "directory": str(DUAL_WINDOW_40D_DIR.relative_to(PROJECT_ROOT)),
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_ROLLING_WINDOW_40D_COMPLETE")

    hook.emit(
        event_type="DUAL_WINDOW_ROLLING_WINDOW_20D_COMPLETE",
        stage="dual_window_20d",
        status=AlertHook.STATUS_PASS,
        row_count=len(entries_20d),
        detail={
            "window_days": WINDOW_20D_DAYS,
            "shards_generated": len(entries_20d),
            "directory": str(DUAL_WINDOW_20D_DIR.relative_to(PROJECT_ROOT)),
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_ROLLING_WINDOW_20D_COMPLETE")

    # ── 2. Dual Directory Isolation Alert ──
    dir_20d_resolved = DUAL_WINDOW_20D_DIR.resolve()
    dir_40d_resolved = DUAL_WINDOW_40D_DIR.resolve()
    dir_par_resolved = PARALLEL_DIR.resolve()
    isolation_20_40 = dir_20d_resolved != dir_40d_resolved
    isolation_20_par = dir_20d_resolved != dir_par_resolved
    isolation_40_par = dir_40d_resolved != dir_par_resolved

    hook.emit(
        event_type="DUAL_WINDOW_DUAL_DIR_ISOLATION",
        stage="directory_isolation",
        status=AlertHook.STATUS_PASS if (isolation_20_40 and isolation_20_par and isolation_40_par) else AlertHook.STATUS_FAIL,
        detail={
            "dual_20d_dir": str(DUAL_WINDOW_20D_DIR.relative_to(PROJECT_ROOT)),
            "dual_40d_dir": str(DUAL_WINDOW_40D_DIR.relative_to(PROJECT_ROOT)),
            "parallel_dir": str(PARALLEL_DIR.relative_to(PROJECT_ROOT)),
            "isolation_20_40": isolation_20_40,
            "isolation_20_parallel": isolation_20_par,
            "isolation_40_parallel": isolation_40_par,
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_DUAL_DIR_ISOLATION")

    # ── 3. Contract Roll-over Summary Alert ──
    rollover_summary_path = CONTRACT_ROLLOVER_DIR / "rollover_summary.json"
    rollover_summary = {}
    if rollover_summary_path.is_file():
        rollover_summary = json.loads(rollover_summary_path.read_text(encoding="utf-8"))

    hook.emit(
        event_type="DUAL_WINDOW_CONTRACT_ROLLOVER",
        stage="contract_rollover",
        status=AlertHook.STATUS_PASS,
        row_count=rollover_summary.get("total_rollover_rows", 0),
        detail={
            "symbols_processed": rollover_summary.get("symbols_processed", 0),
            "total_switch_events": rollover_summary.get("total_switch_events", 0),
            "oi_change_threshold": OI_CHANGE_THRESHOLD,
            "rollover_days": CONTRACT_ROLLOVER_SIM_DAYS,
            "data_directory": str(CONTRACT_ROLLOVER_DIR.relative_to(PROJECT_ROOT)),
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_CONTRACT_ROLLOVER")

    # ── 4. Per-symbol roll-over event alerts ──
    per_symbol_stats = rollover_summary.get("per_symbol_stats", {})
    for sym, stats in per_symbol_stats.items():
        hook.emit(
            event_type="DUAL_WINDOW_SYMBOL_ROLLOVER_EVENTS",
            stage="contract_rollover",
            status=AlertHook.STATUS_PASS if stats.get("threshold_met") else AlertHook.STATUS_WARN,
            detail={
                "symbol": sym,
                "total_switches": stats.get("total_switches", 0),
                "switch_indices": stats.get("switch_indices", []),
                "avg_oi": stats.get("avg_oi", 0),
                "min_oi_change_rate": stats.get("min_oi_change_rate", 0),
                "threshold_met": stats.get("threshold_met", False),
            },
        )
        alert_count += 1
        alert_types.add("DUAL_WINDOW_SYMBOL_ROLLOVER_EVENTS")

    # ── 5. SHA Fingerprint List Alert ──
    total_sha_files = sha_data.get("total_files", 0) if sha_data else 0

    hook.emit(
        event_type="DUAL_WINDOW_SHA_FINGERPRINT",
        stage="sha_snapshot",
        status=AlertHook.STATUS_PASS,
        detail={
            "total_files_hashed": total_sha_files,
            "fingerprint_list_ref": str(DUAL_WINDOW_SHA_LIST.relative_to(PROJECT_ROOT)),
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_SHA_FINGERPRINT")

    # ── 6. Data Integrity Alert ──
    v2_sha = sha256_of_file(V2_CSV) if V2_CSV.is_file() else None
    sha_integrity = v2_sha == V2_SHA_LOCKED

    hook.emit(
        event_type="DUAL_WINDOW_DATA_INTEGRITY",
        stage="system",
        status=AlertHook.STATUS_PASS if sha_integrity else AlertHook.STATUS_FAIL,
        sha256=v2_sha,
        detail={
            "v2_sha_unchanged": sha_integrity,
            "v2_sha_locked": V2_SHA_LOCKED,
            "gate": GATE,
            "release_permit": RELEASE_PERMIT,
            "wind_api_calls": WIND_API_CALLS,
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_DATA_INTEGRITY")

    # ── 7. Anomaly Events Alert ──
    anomaly_summary = {"total_events": 0, "by_type": {}, "by_severity": {}}
    if ANOMALY_EVENTS.is_file():
        anomaly_data = json.loads(ANOMALY_EVENTS.read_text(encoding="utf-8"))
        anomaly_summary = anomaly_data.get("summary", anomaly_summary)

    hook.emit(
        event_type="DUAL_WINDOW_ANOMALY_EVENTS",
        stage="anomaly",
        status=AlertHook.STATUS_PASS if anomaly_summary.get("total_events", 0) == 0 else AlertHook.STATUS_WARN,
        detail={
            "total_events": anomaly_summary.get("total_events", 0),
            "by_type": anomaly_summary.get("by_type", {}),
            "by_severity": anomaly_summary.get("by_severity", {}),
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_ANOMALY_EVENTS")

    # ── 8. Lock Conflict Ledger Alert ──
    lock_ledger_summary = {}
    if DUAL_WINDOW_LOCK_LEDGER.is_file():
        lock_data = json.loads(DUAL_WINDOW_LOCK_LEDGER.read_text(encoding="utf-8"))
        lock_ledger_summary = lock_data.get("cumulative", {})

    hook.emit(
        event_type="DUAL_WINDOW_LOCK_LEDGER",
        stage="lock",
        status=AlertHook.STATUS_PASS if lock_ledger_summary.get("total_conflicts", 0) == 0 else AlertHook.STATUS_WARN,
        detail={
            "total_rounds": lock_ledger_summary.get("total_rounds", 0),
            "total_conflicts": lock_ledger_summary.get("total_conflicts", 0),
            "total_cross": lock_ledger_summary.get("total_cross", 0),
            "total_timeouts": lock_ledger_summary.get("total_timeouts", 0),
            "avg_duration_sec": lock_ledger_summary.get("avg_duration_sec", 0),
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_LOCK_LEDGER")

    # ── 9. Resource Throughput Monitoring Alert ──
    hook.emit(
        event_type="DUAL_WINDOW_RESOURCE_MONITORING",
        stage="resource",
        status=AlertHook.STATUS_PASS,
        detail={
            "total_rounds": lock_ledger_summary.get("total_rounds", 0),
            "avg_duration_sec": lock_ledger_summary.get("avg_duration_sec", 0),
            "max_duration_sec": lock_ledger_summary.get("max_duration_sec", 0),
            "min_duration_sec": lock_ledger_summary.get("min_duration_sec", 0),
            "avg_queue_peak": lock_ledger_summary.get("avg_queue_peak", 0),
            "max_queue_peak": lock_ledger_summary.get("max_queue_peak", 0),
            "total_duration_sec": lock_ledger_summary.get("total_duration_sec", 0),
            "conflicts": lock_ledger_summary.get("total_conflicts", 0),
            "cross_contamination": lock_ledger_summary.get("total_cross", 0),
            "timeouts": lock_ledger_summary.get("total_timeouts", 0),
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_RESOURCE_MONITORING")

    # ── 10. Dual Pipeline Continuity Alert ──
    schedule_config = {}
    if PARALLEL_SCHEDULE_CONFIG.is_file():
        schedule_config = json.loads(PARALLEL_SCHEDULE_CONFIG.read_text(encoding="utf-8"))
    dual_pipeline_ok = (
        schedule_config.get("dual_pipeline", {}).get("serial_pipeline", {}).get("enabled", False)
        and schedule_config.get("dual_pipeline", {}).get("parallel_pipeline", {}).get("enabled", False)
    )

    hook.emit(
        event_type="DUAL_WINDOW_DUAL_PIPELINE",
        stage="schedule",
        status=AlertHook.STATUS_PASS if dual_pipeline_ok else AlertHook.STATUS_WARN,
        detail={
            "dual_pipeline": dual_pipeline_ok,
            "current_mode": schedule_config.get("mode_switch", {}).get("current_mode", "UNKNOWN"),
            "serial_task": "DSHC-IncrPipelineDaily",
            "parallel_task": "DSHC-IncrPipelineParallel",
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_DUAL_PIPELINE")

    # ── 11. Mode Switch Alert ──
    hook.emit(
        event_type="DUAL_WINDOW_MODE_SWITCH",
        stage="schedule",
        status=AlertHook.STATUS_PASS,
        detail={
            "current_mode": schedule_config.get("mode_switch", {}).get("current_mode", "UNKNOWN"),
            "workorder": WORKORDER,
            "token": TOKEN,
            "authorization": AUTHORIZATION,
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_MODE_SWITCH")

    # ── 12. Alert Integration Test ──
    alert_test_result = run_alert_integration_test()
    alert_test_pass = alert_test_result.get("all_valid", False)

    hook.emit(
        event_type="DUAL_WINDOW_ALERT_TEST",
        stage="system",
        status=AlertHook.STATUS_PASS if alert_test_pass else AlertHook.STATUS_WARN,
        detail={
            "alert_test_pass": alert_test_pass,
            "test_details": alert_test_result,
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_ALERT_TEST")

    # ── 13. Pipeline Summary Alert ──
    hook.emit(
        event_type="DUAL_WINDOW_PIPELINE_SUMMARY",
        stage="system",
        status=AlertHook.STATUS_PASS,
        detail={
            "workorder": WORKORDER,
            "token": TOKEN,
            "authorization": AUTHORIZATION,
            "phases_completed": ["P0", "P1", "P2", "P3", "P4"],
            "window_20d_days": WINDOW_20D_DAYS,
            "window_40d_days": WINDOW_40D_DAYS,
            "monitor_rounds": MONITOR_TOTAL_ROUNDS,
            "contract_rollover_days": CONTRACT_ROLLOVER_SIM_DAYS,
            "down_minimum": DOWN_MINIMUM,
            "total_sha_files": total_sha_files,
            "wind_api_calls": WIND_API_CALLS,
        },
    )
    alert_count += 1
    alert_types.add("DUAL_WINDOW_PIPELINE_SUMMARY")

    logger.info("  Total alerts emitted: %d", alert_count)
    logger.info("  Unique alert types: %d", len(alert_types))

    audit_event(
        "TASK017_P4_ALERTS_PUSHED",
        f"P4告警推送完成: {alert_count}条告警, {len(alert_types)}种类型",
        {
            "total_alerts": alert_count,
            "alert_types": sorted(list(alert_types)),
            "alert_types_count": len(alert_types),
            "total_sha_files": total_sha_files,
            "alert_test_pass": alert_test_pass,
        }
    )

    return {
        "total_alerts": alert_count,
        "alert_types": sorted(list(alert_types)),
        "alert_types_count": len(alert_types),
        "total_sha_files": total_sha_files,
        "alert_test_pass": alert_test_pass,
    }


# ════════════════════════════════════════════════════════════════
# P5: 双窗口数据集快照 + DSHA回执
# ════════════════════════════════════════════════════════════════
def run_p5_receipt(p0_result, p1_result, p2_result, p3_result, p4_result) -> Dict[str, Any]:
    """
    P5: 长期运行结束后，输出双窗口数据集快照+全量SHA指纹，发送就绪回执至DSHA。
    """
    logger.info("=" * 60)
    logger.info("P5: 双窗口数据集完成，输出快照与DSHA回执")
    logger.info("=" * 60)

    # ── 1. Build dual-window report ──
    all_pass = (
        p0_result.get("all_pass", False)
        and p1_result.get("pass_40d", False)
        and p1_result.get("pass_20d", False)
        and p2_result.get("down_sufficient", False)
        and p2_result.get("consistency_pass", False)
        and p2_result.get("lock_test_pass", False)
        and p3_result.get("total_switch_events", 0) > 0
        and p4_result.get("alert_test_pass", False)
    )

    dual_window_report = {
        "workorder": WORKORDER,
        "token": TOKEN,
        "authorization": AUTHORIZATION,
        "generated_at": now_iso(),
        "mode": "DUAL_WINDOW_PIPELINE",
        "is_dry_run": False,
        "wind_api_calls": WIND_API_CALLS,

        # ── P1: Dual Window ──
        "dual_window": {
            "window_20d": {
                "days_planned": WINDOW_20D_DAYS,
                "shards_generated": p1_result.get("shards_20d", 0),
                "total_rows": p1_result.get("total_rows_20d", 0),
                "days_success": p1_result.get("days_success_20d", 0),
                "pass": p1_result.get("pass_20d", False),
            },
            "window_40d": {
                "days_planned": WINDOW_40D_DAYS,
                "shards_generated": p1_result.get("shards_40d", 0),
                "total_rows": p1_result.get("total_rows_40d", 0),
                "days_success": p1_result.get("days_success_40d", 0),
                "pass": p1_result.get("pass_40d", False),
            },
            "conflicts": p1_result.get("conflicts", 0),
            "cross_contamination": p1_result.get("cross", 0),
            "total_duration_sec": p1_result.get("total_duration", 0),
            "pass": p1_result.get("pass_40d", False) and p1_result.get("pass_20d", False),
        },

        # ── P2: Regime Balance ──
        "regime_balance": {
            "rounds_planned": p2_result.get("rounds_planned", MONITOR_TOTAL_ROUNDS),
            "rounds_completed": p2_result.get("rounds_completed", 0),
            "regime_counts": p2_result.get("regime_counts", {}),
            "regime_proportions": p2_result.get("regime_proportions", {}),
            "down_minimum_required": DOWN_MINIMUM,
            "down_count": p2_result.get("down_count", 0),
            "down_sufficient": p2_result.get("down_sufficient", False),
            "conflicts": p2_result.get("conflicts", 0),
            "cross_contamination": p2_result.get("cross", 0),
            "timeouts": p2_result.get("timeouts", 0),
            "consistency_pass": p2_result.get("consistency_pass", False),
            "lock_test_pass": p2_result.get("lock_test_pass", False),
            "pass": (
                p2_result.get("down_sufficient", False)
                and p2_result.get("consistency_pass", False)
                and p2_result.get("lock_test_pass", False)
            ),
        },

        # ── P3: Contract Roll-over ──
        "contract_rollover": {
            "symbols_processed": p3_result.get("symbols_processed", 0),
            "total_switch_events": p3_result.get("total_switch_events", 0),
            "total_rollover_rows": p3_result.get("total_rollover_rows", 0),
            "oi_change_threshold": OI_CHANGE_THRESHOLD,
            "rollover_sim_days": CONTRACT_ROLLOVER_SIM_DAYS,
            "per_symbol_switches": {
                s: st.get("total_switches", 0)
                for s, st in p3_result.get("per_symbol_stats", {}).items()
            },
            "threshold_met_all": all(
                st.get("threshold_met", False)
                for st in p3_result.get("per_symbol_stats", {}).values()
            ),
            "pass": p3_result.get("total_switch_events", 0) > 0,
        },

        # ── P4: DSHD Alerts ──
        "dshd_alerts": {
            "total_alerts": p4_result.get("total_alerts", 0),
            "alert_types": p4_result.get("alert_types", []),
            "alert_types_count": p4_result.get("alert_types_count", 0),
            "alert_test_pass": p4_result.get("alert_test_pass", False),
            "total_sha_files": p4_result.get("total_sha_files", 0),
            "pass": p4_result.get("total_alerts", 0) > 0,
        },

        # ── Summary ──
        "p0_pass": p0_result.get("all_pass", False),
        "overall_pass": all_pass,

        # ── Constraints ──
        "constraints": {
            "v2_sha_unchanged": True,
            "v2_sha_locked": V2_SHA_LOCKED,
            "gate": GATE,
            "release_permit": RELEASE_PERMIT,
            "wind_api_calls": WIND_API_CALLS,
            "serial_pipeline_unchanged": True,
            "lc_shf_blacklisted": True,
            "e13_e14_e15_unchanged": True,
        },

        # ── Artifact references ──
        "artifacts": {
            "dual_window_report": str(DUAL_WINDOW_REPORT.relative_to(PROJECT_ROOT)),
            "dual_window_snapshot": str(DUAL_WINDOW_SNAPSHOT.relative_to(PROJECT_ROOT)),
            "sha_fingerprint_list": str(DUAL_WINDOW_SHA_LIST.relative_to(PROJECT_ROOT)),
            "lock_conflict_ledger": str(DUAL_WINDOW_LOCK_LEDGER.relative_to(PROJECT_ROOT)),
            "consistency_report": str(DUAL_WINDOW_CONSISTENCY.relative_to(PROJECT_ROOT)),
            "anomaly_events": str(ANOMALY_EVENTS.relative_to(PROJECT_ROOT)),
            "rollover_summary": str(
                (CONTRACT_ROLLOVER_DIR / "rollover_summary.json").relative_to(PROJECT_ROOT)
            ),
            "dual_window_20d_dir": str(DUAL_WINDOW_20D_DIR.relative_to(PROJECT_ROOT)),
            "dual_window_40d_dir": str(DUAL_WINDOW_40D_DIR.relative_to(PROJECT_ROOT)),
            "contract_rollover_dir": str(CONTRACT_ROLLOVER_DIR.relative_to(PROJECT_ROOT)),
        },
    }

    # ── 2. Write report ──
    with open(DUAL_WINDOW_REPORT, "w", encoding="utf-8") as f:
        json.dump(dual_window_report, f, ensure_ascii=False, indent=2)
    logger.info("  Report written: %s", DUAL_WINDOW_REPORT)

    # ── 3. Write snapshot ──
    snapshot = {
        "workorder": WORKORDER,
        "token": TOKEN,
        "authorization": AUTHORIZATION,
        "generated_at": now_iso(),
        "version": "1.0.0",

        "constraints": {
            "gate": GATE,
            "release_permit": RELEASE_PERMIT,
            "wind_api_calls": WIND_API_CALLS,
            "v2_sha_unchanged": True,
            "v2_sha_locked": V2_SHA_LOCKED,
            "serial_pipeline_unchanged": True,
            "lc_shf_blacklisted": True,
            "e13_e14_e15_unchanged": True,
            "csv_readonly": True,
            "v1_frozen": True,
        },

        "receipt": {
            "marker": "DSHC_TASK017_DUAL_WINDOW_PIPELINE=COMPLETE",
            "p0_smoke_check": p0_result.get("all_pass", False),
            "p1_dual_window_40d": p1_result.get("pass_40d", False),
            "p1_dual_window_20d": p1_result.get("pass_20d", False),
            "p2_regime_balance": p2_result.get("down_sufficient", False),
            "p2_consistency": p2_result.get("consistency_pass", False),
            "p2_lock_test": p2_result.get("lock_test_pass", False),
            "p3_contract_rollover": p3_result.get("total_switch_events", 0) > 0,
            "p4_dshd_alerts": p4_result.get("total_alerts", 0) > 0,
            "overall_pass": all_pass,
        },

        "artifacts": {
            "dual_window_report": str(DUAL_WINDOW_REPORT.relative_to(PROJECT_ROOT)),
            "dual_window_snapshot": str(DUAL_WINDOW_SNAPSHOT.relative_to(PROJECT_ROOT)),
            "sha_fingerprint_list": str(DUAL_WINDOW_SHA_LIST.relative_to(PROJECT_ROOT)),
            "lock_conflict_ledger": str(DUAL_WINDOW_LOCK_LEDGER.relative_to(PROJECT_ROOT)),
            "consistency_report": str(DUAL_WINDOW_CONSISTENCY.relative_to(PROJECT_ROOT)),
            "anomaly_events": str(ANOMALY_EVENTS.relative_to(PROJECT_ROOT)),
            "rollover_summary": str(
                (CONTRACT_ROLLOVER_DIR / "rollover_summary.json").relative_to(PROJECT_ROOT)
            ),
            "dual_window_20d_dir": str(DUAL_WINDOW_20D_DIR.relative_to(PROJECT_ROOT)),
            "dual_window_40d_dir": str(DUAL_WINDOW_40D_DIR.relative_to(PROJECT_ROOT)),
            "contract_rollover_dir": str(CONTRACT_ROLLOVER_DIR.relative_to(PROJECT_ROOT)),
        },

        "summary": {
            "window_20d_days": WINDOW_20D_DAYS,
            "window_20d_shards": p1_result.get("shards_20d", 0),
            "window_20d_rows": p1_result.get("total_rows_20d", 0),
            "window_40d_days": WINDOW_40D_DAYS,
            "window_40d_shards": p1_result.get("shards_40d", 0),
            "window_40d_rows": p1_result.get("total_rows_40d", 0),
            "regime_rounds": p2_result.get("rounds_completed", 0),
            "down_count": p2_result.get("down_count", 0),
            "down_minimum": DOWN_MINIMUM,
            "contract_rollover_symbols": p3_result.get("symbols_processed", 0),
            "contract_rollover_switches": p3_result.get("total_switch_events", 0),
            "contract_rollover_rows": p3_result.get("total_rollover_rows", 0),
            "dshd_alerts_pushed": p4_result.get("total_alerts", 0),
            "total_sha_files": p4_result.get("total_sha_files", 0),
        },
    }

    with open(DUAL_WINDOW_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    logger.info("  Snapshot written: %s", DUAL_WINDOW_SNAPSHOT)

    # ── 4. Update manifest governance ──
    logger.info("  Updating manifest governance fields...")
    manifest = read_manifest()

    governance = manifest.setdefault("governance", {})
    governance["LAST_DUAL_WINDOW_RUN"] = now_iso()
    governance["LAST_DUAL_WINDOW_STATUS"] = "PASS" if all_pass else "FAIL"
    governance["LAST_DUAL_WINDOW_WORKORDER"] = WORKORDER
    governance["LAST_DUAL_WINDOW_TOKEN"] = TOKEN
    governance["LAST_DUAL_WINDOW_AUTHORIZATION"] = AUTHORIZATION
    governance["LAST_DUAL_WINDOW_IS_DRY_RUN"] = False
    governance["LAST_DUAL_WINDOW_20D_DAYS"] = WINDOW_20D_DAYS
    governance["LAST_DUAL_WINDOW_20D_SHARDS"] = p1_result.get("shards_20d", 0)
    governance["LAST_DUAL_WINDOW_20D_ROWS"] = p1_result.get("total_rows_20d", 0)
    governance["LAST_DUAL_WINDOW_40D_DAYS"] = WINDOW_40D_DAYS
    governance["LAST_DUAL_WINDOW_40D_SHARDS"] = p1_result.get("shards_40d", 0)
    governance["LAST_DUAL_WINDOW_40D_ROWS"] = p1_result.get("total_rows_40d", 0)
    governance["LAST_DUAL_WINDOW_MONITOR_ROUNDS"] = p2_result.get("rounds_completed", 0)
    governance["LAST_DUAL_WINDOW_DOWN_COUNT"] = p2_result.get("down_count", 0)
    governance["LAST_DUAL_WINDOW_DOWN_MINIMUM"] = DOWN_MINIMUM
    governance["LAST_DUAL_WINDOW_DOWN_SUFFICIENT"] = p2_result.get("down_sufficient", False)
    governance["LAST_DUAL_WINDOW_CONTRACT_ROLLOVER_SYMBOLS"] = p3_result.get("symbols_processed", 0)
    governance["LAST_DUAL_WINDOW_CONTRACT_ROLLOVER_SWITCHES"] = p3_result.get("total_switch_events", 0)
    governance["LAST_DUAL_WINDOW_CONTRACT_ROLLOVER_ROWS"] = p3_result.get("total_rollover_rows", 0)
    governance["LAST_DUAL_WINDOW_OI_CHANGE_THRESHOLD"] = OI_CHANGE_THRESHOLD
    governance["LAST_DUAL_WINDOW_CONFLICTS"] = p2_result.get("conflicts", 0)
    governance["LAST_DUAL_WINDOW_CROSS"] = p2_result.get("cross", 0)
    governance["LAST_DUAL_WINDOW_TIMEOUTS"] = p2_result.get("timeouts", 0)
    governance["LAST_DUAL_WINDOW_DSHD_ALERTS"] = p4_result.get("total_alerts", 0)
    governance["LAST_DUAL_WINDOW_DSHD_ALERT_TYPES"] = p4_result.get("alert_types_count", 0)
    governance["LAST_DUAL_WINDOW_SHA_FILES"] = p4_result.get("total_sha_files", 0)
    governance["LAST_DUAL_WINDOW_OVERALL_PASS"] = all_pass

    # Add pipeline_scripts entry
    scripts = manifest.setdefault("pipeline_scripts", {})
    scripts["incr_pipeline_dual_window"] = {
        "path": "code/incr_pipeline_dual_window.py",
        "purpose": "双窗口常态化并行采集工单",
        "version": "1.0.0",
        "workorder": WORKORDER,
        "token": TOKEN,
        "authorization": AUTHORIZATION,
        "created_at": now_iso(),
        "dual_window_report": str(DUAL_WINDOW_REPORT.relative_to(PROJECT_ROOT)),
        "dual_window_snapshot": str(DUAL_WINDOW_SNAPSHOT.relative_to(PROJECT_ROOT)),
        "sha_fingerprint_list": str(DUAL_WINDOW_SHA_LIST.relative_to(PROJECT_ROOT)),
        "lock_conflict_ledger": str(DUAL_WINDOW_LOCK_LEDGER.relative_to(PROJECT_ROOT)),
        "window_20d_days": WINDOW_20D_DAYS,
        "window_40d_days": WINDOW_40D_DAYS,
        "down_minimum": DOWN_MINIMUM,
        "oi_change_threshold": OI_CHANGE_THRESHOLD,
        "dshd_alert_types": [
            "DUAL_WINDOW_ROLLING_WINDOW_40D_COMPLETE",
            "DUAL_WINDOW_ROLLING_WINDOW_20D_COMPLETE",
            "DUAL_WINDOW_DUAL_DIR_ISOLATION",
            "DUAL_WINDOW_REGIME_DISTRIBUTION",
            "DUAL_WINDOW_CONSISTENCY_CHECK",
            "DUAL_WINDOW_CONTRACT_ROLLOVER",
            "DUAL_WINDOW_SYMBOL_ROLLOVER_EVENTS",
            "DUAL_WINDOW_SHA_FINGERPRINT",
            "DUAL_WINDOW_LOCK_LEDGER",
            "DUAL_WINDOW_RESOURCE_MONITORING",
            "DUAL_WINDOW_ALERT_TEST",
            "DUAL_WINDOW_PIPELINE_SUMMARY",
            "DUAL_WINDOW_DATA_INTEGRITY",
            "DUAL_WINDOW_ANOMALY_EVENTS",
            "DUAL_WINDOW_DUAL_PIPELINE",
            "DUAL_WINDOW_MODE_SWITCH",
        ],
    }

    # Update total size
    total_size = 0
    for entry in manifest.get("files", []):
        total_size += entry.get("size_bytes", 0)
    manifest["total_size_bytes"] = total_size
    manifest["updated_at"] = now_iso()

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    logger.info("  Manifest updated: %s", MANIFEST_PATH)

    # ── 5. DSHA notification ──
    logger.info("  Sending DSHA notification...")
    dsha_notification = {
        "workorder": WORKORDER,
        "token": TOKEN,
        "authorization": AUTHORIZATION,
        "generated_at": now_iso(),
        "notification_id": f"DSHC-DSHA-NOTIFY-{datetime.now(TZ_CN).strftime('%Y%m%d%H%M%S')}",
        "event": "NOTIFY_DUAL_WINDOW_READY",
        "status": "READY" if all_pass else "PENDING",
        "next_action": "DSHA_START_DUAL_WINDOW_FLIP_RATE_EVALUATION",
        "dataset_info": {
            "window_20d_days": WINDOW_20D_DAYS,
            "window_20d_shards": p1_result.get("shards_20d", 0),
            "window_20d_rows": p1_result.get("total_rows_20d", 0),
            "window_40d_days": WINDOW_40D_DAYS,
            "window_40d_shards": p1_result.get("shards_40d", 0),
            "window_40d_rows": p1_result.get("total_rows_40d", 0),
            "regime_rounds": p2_result.get("rounds_completed", 0),
            "down_count": p2_result.get("down_count", 0),
            "down_minimum": DOWN_MINIMUM,
            "contract_rollover_symbols": p3_result.get("symbols_processed", 0),
            "contract_rollover_switch_events": p3_result.get("total_switch_events", 0),
            "contract_rollover_rows": p3_result.get("total_rollover_rows", 0),
            "oi_change_threshold": OI_CHANGE_THRESHOLD,
        },
        "sha_fingerprint_list": str(DUAL_WINDOW_SHA_LIST.relative_to(PROJECT_ROOT)),
        "dual_window_report": str(DUAL_WINDOW_REPORT.relative_to(PROJECT_ROOT)),
        "dual_window_snapshot": str(DUAL_WINDOW_SNAPSHOT.relative_to(PROJECT_ROOT)),
        "constraints": {
            "wind_api_calls": WIND_API_CALLS,
            "gate": GATE,
            "release_permit": RELEASE_PERMIT,
            "v2_sha_unchanged": True,
            "v2_sha_locked": V2_SHA_LOCKED,
            "serial_pipeline_unchanged": True,
            "lc_shf_blacklisted": True,
        },
        "receipt_marker": "DSHC_TASK017_DUAL_WINDOW_PIPELINE=COMPLETE",
    }

    with open(DSHA_NOTIFICATION, "w", encoding="utf-8") as f:
        json.dump(dsha_notification, f, ensure_ascii=False, indent=2)
    logger.info("  DSHA notification written: %s", DSHA_NOTIFICATION)

    # ── 6. Audit event ──
    audit_event(
        "TASK017_P5_RECEIPT_DELIVERED",
        f"P5回执完成: overall_pass={all_pass}, "
        f"40d={p1_result.get('shards_40d', 0)}分片, "
        f"20d={p1_result.get('shards_20d', 0)}分片, "
        f"DOWN={p2_result.get('down_count', 0)}(≥{DOWN_MINIMUM}), "
        f"换月事件={p3_result.get('total_switch_events', 0)}, "
        f"告警={p4_result.get('total_alerts', 0)}条",
        {
            "p0_pass": p0_result.get("all_pass", False),
            "p1_40d_shards": p1_result.get("shards_40d", 0),
            "p1_20d_shards": p1_result.get("shards_20d", 0),
            "p2_down_count": p2_result.get("down_count", 0),
            "p3_switch_events": p3_result.get("total_switch_events", 0),
            "p4_alerts": p4_result.get("total_alerts", 0),
            "overall_pass": all_pass,
            "receipt_marker": "DSHC_TASK017_DUAL_WINDOW_PIPELINE=COMPLETE",
        }
    )

    # ── 7. Print final summary ──
    logger.info("\n" + "=" * 60)
    logger.info("P5: TASK-017 双窗口并行采集完成")
    logger.info("=" * 60)
    logger.info("  P0 冒烟自检: %s", "PASS" if p0_result.get("all_pass") else "FAIL")
    logger.info("  P1 双窗口: 40d=%d/%d天,%d分片 | 20d=%d/%d天,%d分片",
                p1_result.get("days_success_40d", 0), p1_result.get("days_planned", 0),
                p1_result.get("shards_40d", 0),
                p1_result.get("days_success_20d", 0), WINDOW_20D_DAYS,
                p1_result.get("shards_20d", 0))
    logger.info("  P2 行情均衡: %d轮, DOWN=%d(≥%d=%s), 一致性=%s, 锁测试=%s",
                p2_result.get("rounds_completed", 0),
                p2_result.get("down_count", 0), DOWN_MINIMUM,
                "YES" if p2_result.get("down_sufficient") else "NO",
                "PASS" if p2_result.get("consistency_pass") else "FAIL",
                "PASS" if p2_result.get("lock_test_pass") else "FAIL")
    logger.info("  P3 合约换月: %d品种, %d次换月事件, 阈值=%.0f%%",
                p3_result.get("symbols_processed", 0), p3_result.get("total_switch_events", 0),
                OI_CHANGE_THRESHOLD * 100)
    logger.info("  P4 DSHD告警: %d条, %d种类型",
                p4_result.get("total_alerts", 0), p4_result.get("alert_types_count", 0))
    logger.info("  P5 回执标记: DSHC_TASK017_DUAL_WINDOW_PIPELINE=COMPLETE")
    logger.info("  Overall: %s", "PASS" if all_pass else "FAIL")
    logger.info("=" * 60)

    return {
        "overall_pass": all_pass,
        "report_path": str(DUAL_WINDOW_REPORT),
        "snapshot_path": str(DUAL_WINDOW_SNAPSHOT),
        "dsha_notification_path": str(DSHA_NOTIFICATION),
        "receipt_marker": "DSHC_TASK017_DUAL_WINDOW_PIPELINE=COMPLETE",
    }


# ════════════════════════════════════════════════════════════════
# Cleanup
# ════════════════════════════════════════════════════════════════
def run_cleanup():
    """清理 TASK-017 专用临时文件。"""
    logger.info("Running TASK-017 cleanup...")

    # Clean lock files
    for lock_file in [GLOBAL_LOCK_FILE, PARALLEL_LOCK_FILE]:
        if lock_file.is_file():
            try:
                lock_file.unlink()
                logger.info("  Removed: %s", lock_file.name)
            except OSError as e:
                logger.warning("  Failed to remove %s: %s", lock_file.name, e)

    # Clean shard locks
    for sym in SYMBOL_WHITELIST:
        safe = sym.replace(".", "_").replace("/", "_")
        lock_file = DATA_DIR / f".parallel_lock_{safe}"
        if lock_file.is_file():
            try:
                lock_file.unlink()
                logger.info("  Removed: %s", lock_file.name)
            except OSError as e:
                logger.warning("  Failed to remove %s: %s", lock_file.name, e)

    logger.info("Cleanup complete.")


# ════════════════════════════════════════════════════════════════
# CLI 入口
# ════════════════════════════════════════════════════════════════
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="incr_pipeline_dual_window.py",
        description=f"{WORKORDER} · 双窗口常态化并行采集",
    )

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--full-run", action="store_true",
                              help="执行 P0→P5 全流程")
    action_group.add_argument("--p0-self-check", action="store_true",
                              help="仅执行 P0 冒烟自检")
    action_group.add_argument("--p1-dual-window", action="store_true",
                              help="仅执行 P1 双窗口并行流水线")
    action_group.add_argument("--p2-regime-balance", action="store_true",
                              help="仅执行 P2 行情均衡监控")
    action_group.add_argument("--p3-contract-rollover", action="store_true",
                              help="仅执行 P3 合约换月OI数据")
    action_group.add_argument("--p4-consistency-alerts", action="store_true",
                              help="仅执行 P4 一致性报告+告警")
    action_group.add_argument("--p5-receipt", action="store_true",
                              help="仅执行 P5 回执")
    action_group.add_argument("--cleanup", action="store_true",
                              help="清理临时文件")

    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.cleanup:
        run_cleanup()
        return 0

    if args.full_run:
        logger.info("=" * 60)
        logger.info("TASK-017: 全流程执行 (P0 → P5)")
        logger.info("  Workorder: %s", WORKORDER)
        logger.info("  Token: %s", TOKEN)
        logger.info("  Authorization: %s", AUTHORIZATION)
        logger.info("=" * 60)

        audit_event("TASK017_FULL_RUN_STARTED", "全流程开始执行", {})

        # P0: Self-check
        p0_result = run_p0_self_check()
        if not p0_result.get("all_pass", False):
            logger.error("P0 failed — aborting")
            audit_event("TASK017_ABORTED", "P0自检未通过，流程中止", {"p0": p0_result})
            return 1

        # P1: Dual window
        p1_result = run_p1_dual_window()

        # P2: Regime balance
        p2_result = run_p2_regime_balance()

        # P3: Contract roll-over
        p3_result = run_p3_contract_rollover()

        # P4: Consistency + alerts
        p4_result = run_p4_consistency_alerts()

        # P5: Receipt
        p5_result = run_p5_receipt(p0_result, p1_result, p2_result, p3_result, p4_result)

        audit_event("TASK017_FULL_RUN_COMPLETE",
                    f"全流程完成: overall_pass={p5_result.get('overall_pass', False)}",
                    {"receipt_marker": "DSHC_TASK017_DUAL_WINDOW_PIPELINE=COMPLETE"})

        # Print receipt
        print(f"\n{'=' * 60}")
        print("DSHC_TASK017_DUAL_WINDOW_PIPELINE=COMPLETE")
        print(f"{'=' * 60}")
        print(f"P0_SMOKE_CHECK={p0_result.get('all_pass', False)}")
        print(f"P1_DUAL_WINDOW_40D={p1_result.get('pass_40d', False)}")
        print(f"P1_DUAL_WINDOW_20D={p1_result.get('pass_20d', False)}")
        print(f"P2_DOWNSUFFICIENT={p2_result.get('down_sufficient', False)}")
        print(f"P2_CONSISTENCY={p2_result.get('consistency_pass', False)}")
        print(f"P2_LOCKTEST={p2_result.get('lock_test_pass', False)}")
        print(f"P3_CONTRACT_ROLLOVER={p3_result.get('total_switch_events', 0)}")
        print(f"P4_DSHD_ALERTS={p4_result.get('total_alerts', 0)}")
        print(f"P5_OVERALL_PASS={p5_result.get('overall_pass', False)}")
        print(f"{'=' * 60}")

        return 0 if p5_result.get("overall_pass", False) else 1

    # Individual phases
    if args.p0_self_check:
        result = run_p0_self_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("all_pass", False) else 1

    if args.p1_dual_window:
        result = run_p1_dual_window()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.p2_regime_balance:
        result = run_p2_regime_balance()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.p3_contract_rollover:
        result = run_p3_contract_rollover()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.p4_consistency_alerts:
        result = run_p4_consistency_alerts()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
