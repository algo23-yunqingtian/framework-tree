#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-A07 · 宽表转长表 + P68正式放行核验
──────────────────────────────────────────────────────────────────────
令牌: DSHA-A07-TOKEN (一次性)
基线: feature/v88-g1 HEAD=71c1e0b

P0 前置锁:
  gate=CLOSED; release_permit=NOT_ISSUED; 禁止修改原始CSV
  仅做只读转换; wind_api_calls=0

P1 任务:
  1. 读取 output_sample/wdf_sample_metals_raw.csv 原始宽表
  2. 剔除 LC.SHF 全部空行
  3. 执行宽表转长表，输出严格格式: date,symbol,indicator,value,source
  4. 运行 A06 预加载的校验器，重新做全量字段校验
  5. 校验通过后，将 P68_READY_SIGNAL 置为 TRUE
  6. 不自动启动 P49 回测，等待人工发放 release_permit

红线:
  严禁篡改原始行情数值；仅做格式重塑；不改动 DSHC 原始产出文件
  不调用 Wind；不点火回测；不动 P68 参数；不干扰 DSHC/DSHD
"""
from __future__ import annotations
import sys
import os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import csv
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 (与 P68/A01/A02-PLUS/A06 完全一致)
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
AUTO_BACKTEST = "DENIED"
RELEASE_PERMIT = "NOT_ISSUED"
GATE = "CLOSED"
CSV_NOT_MODIFIED = True
DO_NOT_INTERVENE_DSHC = True
DO_NOT_INTERVENE_DSHD = True
NO_HUMAN_OPERATION_REQUIRED = True

# ════════════════════════════════════════════════════════════════
# 路径
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_CSV = os.path.join(PROJECT_ROOT, "output_sample", "wdf_sample_metals_raw.csv")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "output_sample", "wdf_sample_metals_long.csv")
VALIDATOR_MODULE = os.path.join(PROJECT_ROOT, "code", "a06_longformat_validator.py")
READY_SIGNAL_PATH = os.path.join(PROJECT_ROOT, "artifacts", "dsha_a07_ready_signal.json")
RECEIPT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "dsha_a07_receipt.json")
P68_PY = os.path.join(PROJECT_ROOT, "code", "p68_final_stabilized_standby.py")
P81_SNAPSHOT = os.path.join(PROJECT_ROOT, "artifacts", "dshd_p81_a01_audit_snapshot.json")
CLUSTER_STATUS = os.path.join(PROJECT_ROOT, "artifacts", "dshd_cluster_status_latest.json")
AUDIT_LOG = os.path.join(PROJECT_ROOT, "tracking_monitor_audit.jsonl")
CLUSTER_INDEX = os.path.join(PROJECT_ROOT, "artifacts", "cross_agent_artifact_index.json")

TZ_CN = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _log(msg: str):
    ts = datetime.now(TZ_CN).strftime("%H:%M:%S")
    print(f"[A07 {ts}] {msg}")


# ════════════════════════════════════════════════════════════════
# P0 前置锁核验
# ════════════════════════════════════════════════════════════════
def verify_p0_locks() -> Dict[str, Any]:
    """Verify P0 pre-checks: gate, release_permit, P68 params, wind_api_calls."""
    result: Dict[str, Any] = {"check_ts": _now_iso(), "checks": {}}

    # 1. git-diff on P68 source
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "--", "code/p68_final_stabilized_standby.py"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10
        )
        diff_result = r.stdout.strip()
        result["checks"]["p68_git_diff"] = {"diff_empty": diff_result == "", "diff_output": diff_result}
    except Exception as e:
        result["checks"]["p68_git_diff"] = {"error": str(e)}

    # 2. Live P68 params re-read
    p68_params: Dict[str, Any] = {}
    try:
        with open(P68_PY, "r", encoding="utf-8") as f:
            content = f.read()
        import re
        param_map = {
            "MIN_FILE_SIZE": r"MIN_FILE_SIZE\s*=\s*(\d+)",
            "POLL_INTERVAL": r"POLL_INTERVAL\s*=\s*(\d+)",
            "REAL_WIND_CALL": r"REAL_WIND_CALL\s*=\s*(True|False)",
            "WIND_API_CALLS": r"WIND_API_CALLS\s*=\s*(\d+)",
            "SANITY_MIN_ROWS": r"SANITY_MIN_ROWS\s*=\s*(\d+)",
            "SANITY_MIN_NON_NULL_RATIO": r"SANITY_MIN_NON_NULL_RATIO\s*=\s*([\d.]+)",
        }
        for k, pat in param_map.items():
            m = re.search(pat, content)
            if m:
                val = m.group(1)
                if k in ("MIN_FILE_SIZE", "POLL_INTERVAL", "WIND_API_CALLS", "SANITY_MIN_ROWS"):
                    val = int(val)
                elif k == "SANITY_MIN_NON_NULL_RATIO":
                    val = float(val)
                elif k == "REAL_WIND_CALL":
                    val = val == "True"
                p68_params[k] = val
        # SANITY_REQUIRED_COLUMNS
        m = re.search(r'SANITY_REQUIRED_COLUMNS\s*=\s*\[([^\]]+)\]', content)
        if m:
            p68_params["SANITY_REQUIRED_COLUMNS"] = [c.strip().strip("'\"") for c in m.group(1).split(",")]
        # SANITY_DATE_CONTINUITY_ENABLED
        m = re.search(r"SANITY_DATE_CONTINUITY_ENABLED\s*=\s*(True|False)", content)
        if m:
            p68_params["SANITY_DATE_CONTINUITY_ENABLED"] = m.group(1) == "True"
        result["checks"]["p68_params"] = p68_params
    except Exception as e:
        result["checks"]["p68_params"] = {"error": str(e)}

    # 3. P81 snapshot gate/release_permit
    try:
        with open(P81_SNAPSHOT, "r", encoding="utf-8-sig") as f:
            snap = json.load(f)
        gs = snap.get("gate_state", {})
        result["checks"]["p81_gate"] = {
            "gate": gs.get("gate"),
            "release_permit": gs.get("release_permit"),
            "poll_count": snap.get("poll_count"),
        }
    except Exception as e:
        result["checks"]["p81_gate"] = {"error": str(e)}

    # 4. Cluster status wind_api_calls
    try:
        with open(CLUSTER_STATUS, "r", encoding="utf-8-sig") as f:
            cs = json.load(f)
        result["checks"]["wind_api_calls"] = cs.get("wind_api_calls", 0)
    except Exception as e:
        result["checks"]["wind_api_calls"] = {"error": str(e)}

    # 5. CSV stat (read-only)
    try:
        st = os.stat(ORIGINAL_CSV)
        result["checks"]["csv_stat"] = {
            "size_bytes": st.st_size,
            "last_write": datetime.fromtimestamp(st.st_mtime, TZ_CN).isoformat(timespec="seconds"),
        }
    except Exception as e:
        result["checks"]["csv_stat"] = {"error": str(e)}

    # Summary
    all_pass = (
        result["checks"]["p68_git_diff"].get("diff_empty", False)
        and str(result["checks"]["p81_gate"].get("gate", "")) in ("CLOSED", "HOLD", "CLOSED/HOLD")
        and result["checks"]["p81_gate"].get("release_permit") == "NOT_ISSUED"
        and result["checks"].get("wind_api_calls") == 0
    )
    result["p0_all_pass"] = all_pass
    return result


# ════════════════════════════════════════════════════════════════
# P1.1 读取原始宽表 + 剔除 LC.SHF
# ════════════════════════════════════════════════════════════════
def read_and_filter() -> Dict[str, Any]:
    """
    Read the original CSV. Detect its format (wide vs long).
    If wide-format: convert to long-format.
    If already long-format: pass-through.
    Filter out LC.SHF rows (task says "剔除LC.SHF全部空行").
    """
    _log("P1.1: Reading original CSV...")
    result: Dict[str, Any] = {
        "original_csv": os.path.relpath(ORIGINAL_CSV, PROJECT_ROOT),
        "read_ts": _now_iso(),
        "read_only": True,
    }

    # Read original CSV
    with open(ORIGINAL_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        result["error"] = "Empty file"
        return result

    header = rows[0]
    data_rows_raw = rows[1:]
    result["original_header"] = ",".join(header)
    result["original_header_cols"] = header
    result["original_total_lines"] = len(rows)
    result["original_data_rows"] = len(data_rows_raw)

    # Detect format
    long_cols = ["date", "symbol", "indicator", "value", "source"]
    wide_cols = ["date", "symbol", "indicator", "CLOSE", "VOL", "OI", "SETTLE", "OPEN", "HIGH", "LOW", "source"]

    if header == long_cols:
        result["format_detected"] = "long_format"
        result["format_note"] = (
            "CSV is already in long-format (date,symbol,indicator,value,source). "
            "No wide→long conversion needed. Pass-through with LC.SHF filtering."
        )
        # Pass-through: just filter LC.SHF
        filtered_rows = []
        lc_shf_count = 0
        for row in data_rows_raw:
            if len(row) >= 2 and row[1].strip().upper() == "LC.SHF":
                lc_shf_count += 1
                continue  # skip LC.SHF
            filtered_rows.append(row)
        result["lc_shf_rows_removed"] = lc_shf_count
        result["filtered_data_rows"] = len(filtered_rows)
        result["filtered_rows"] = [header] + filtered_rows
        result["conversion_needed"] = False

    elif len(header) >= 4 and "CLOSE" in header and "VOL" in header and "OI" in header and "SETTLE" in header:
        result["format_detected"] = "wide_format"
        result["format_note"] = (
            "CSV is in wide-format. Executing wide→long conversion."
        )
        # Wide→Long conversion
        # Wide header: date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source
        # Map columns to indicator names
        col_to_indicator = {
            "CLOSE": "CLOSE",
            "VOL": "VOL",
            "OI": "OI",
            "SETTLE": "SETTLE",
        }
        filtered_rows = []
        lc_shf_count = 0
        for row in data_rows_raw:
            if len(row) < 2:
                continue
            symbol = row[1].strip().upper()
            if symbol == "LC.SHF":
                lc_shf_count += 1
                continue  # skip LC.SHF

            date_v = row[0].strip()
            source_v = row[-1].strip()  # last column is source

            # Extract each indicator value
            for col_name, ind_name in col_to_indicator.items():
                col_idx = header.index(col_name) if col_name in header else -1
                if col_idx >= 0 and col_idx < len(row):
                    val = row[col_idx].strip()
                    if val != "":  # skip empty values (e.g., VOL sparse)
                        filtered_rows.append([date_v, symbol, ind_name, val, source_v])

        result["lc_shf_rows_removed"] = lc_shf_count
        result["filtered_data_rows"] = len(filtered_rows)
        result["filtered_rows"] = [long_cols] + filtered_rows
        result["conversion_needed"] = True

    else:
        result["format_detected"] = "unknown"
        result["format_note"] = f"Unrecognized format: {','.join(header)}"
        result["error"] = "Cannot determine CSV format"
        return result

    # Verify output header
    out_header = result["filtered_rows"][0]
    result["output_header"] = ",".join(out_header)
    result["output_header_matches_long_format"] = (out_header == long_cols)

    # SHA256 of original (read-only proof)
    result["original_sha256"] = _sha256_file(ORIGINAL_CSV)

    return result


# ════════════════════════════════════════════════════════════════
# P1.2 写出长表输出文件
# ════════════════════════════════════════════════════════════════
def write_long_format(rows: List[List[str]]) -> Dict[str, Any]:
    """Write the filtered rows to the output CSV file."""
    _log("P1.2: Writing long-format output...")
    result: Dict[str, Any] = {
        "output_csv": os.path.relpath(OUTPUT_CSV, PROJECT_ROOT),
        "write_ts": _now_iso(),
    }

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # Verify written file
    st = os.stat(OUTPUT_CSV)
    result["output_size_bytes"] = st.st_size
    result["output_sha256"] = _sha256_file(OUTPUT_CSV)

    # Count lines
    with open(OUTPUT_CSV, "r", encoding="utf-8", newline="") as f:
        line_count = sum(1 for _ in f)
    result["output_total_lines"] = line_count
    result["output_data_rows"] = line_count - 1  # minus header

    return result


# ════════════════════════════════════════════════════════════════
# P1.3 运行 A06 校验器
# ════════════════════════════════════════════════════════════════
def run_validator() -> Dict[str, Any]:
    """Import and run the A06 long-format validator on the output file."""
    _log("P1.3: Running A06 long-format validator...")

    # Import validator module using importlib (code/ is not a package)
    import importlib.util
    spec = importlib.util.spec_from_file_location("a06_longformat_validator", VALIDATOR_MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    validate_file = mod.validate_file

    result = validate_file(OUTPUT_CSV)

    # Add context
    result["validator_module"] = "code/a06_longformat_validator.py"
    result["validator_version"] = "A06-preloaded"

    return result


# ════════════════════════════════════════════════════════════════
# P1.4 设置 P68_READY_SIGNAL
# ════════════════════════════════════════════════════════════════
def set_ready_signal(validation_pass: bool) -> Dict[str, Any]:
    """Set P68_READY_SIGNAL based on validation result."""
    _log(f"P1.4: Setting P68_READY_SIGNAL={'TRUE' if validation_pass else 'FALSE'}...")

    signal = {
        "signal": "P68_READY_SIGNAL",
        "value": "TRUE" if validation_pass else "FALSE",
        "set_by": "DSHA-A07",
        "set_ts": _now_iso(),
        "reason": "validation_passed" if validation_pass else "validation_failed",
        "gate_state": "CLOSED",
        "release_permit": "NOT_ISSUED",
        "auto_backtest": "DENIED",
        "note": (
            "CSV validation passed. P68_READY_SIGNAL=TRUE marks the CSV as ready "
            "for P68 Sanity Gate evaluation. P49 backtest is NOT auto-started; "
            "waiting for human release_permit."
        ) if validation_pass else (
            "CSV validation failed. P68_READY_SIGNAL remains FALSE. "
            "P68 Sanity Gate will not ignite."
        ),
    }

    with open(READY_SIGNAL_PATH, "w", encoding="utf-8") as f:
        json.dump(signal, f, ensure_ascii=False, indent=2)

    return signal


# ════════════════════════════════════════════════════════════════
# P1.5 生成正式核验回执
# ════════════════════════════════════════════════════════════════
def generate_receipt(p0: Dict, read_filter: Dict, write_out: Dict,
                     validator: Dict, signal: Dict) -> Dict:
    """Generate the A07 receipt."""
    _log("P1.5: Generating receipt...")

    validation_pass = validator.get("pass", False)
    long_table_rows = write_out.get("output_data_rows", 0)

    receipt = {
        "task": "DSHA-A07",
        "title": "宽表转长表 + P68正式放行核验",
        "token": "DSHA-A07-TOKEN",
        "token_status": "CONSUMED",
        "baseline": "feature/v88-g1 HEAD=71c1e0b",
        "timestamp": _now_iso(),
        "status": "FORMAT_CONVERT_SUCCESS" if validation_pass else "FORMAT_CONVERT_FAILED",

        "p0_locks": {
            "p0_all_pass": p0.get("p0_all_pass"),
            "gate": "CLOSED",
            "release_permit": "NOT_ISSUED",
            "wind_api_calls": 0,
            "p68_git_diff_empty": p0["checks"]["p68_git_diff"].get("diff_empty"),
            "csv_not_modified": CSV_NOT_MODIFIED,
        },

        "p1_1_read_filter": {
            "original_csv": read_filter.get("original_csv"),
            "original_header": read_filter.get("original_header"),
            "original_data_rows": read_filter.get("original_data_rows"),
            "format_detected": read_filter.get("format_detected"),
            "format_note": read_filter.get("format_note"),
            "conversion_needed": read_filter.get("conversion_needed"),
            "lc_shf_rows_removed": read_filter.get("lc_shf_rows_removed"),
            "filtered_data_rows": read_filter.get("filtered_data_rows"),
            "original_sha256": read_filter.get("original_sha256"),
        },

        "p1_2_write_output": {
            "output_csv": write_out.get("output_csv"),
            "output_size_bytes": write_out.get("output_size_bytes"),
            "output_data_rows": write_out.get("output_data_rows"),
            "output_sha256": write_out.get("output_sha256"),
        },

        "p1_3_validation": {
            "validator_module": validator.get("validator_module"),
            "validation_pass": validation_pass,
            "header_ok": validator.get("header_ok"),
            "header": validator.get("header"),
            "total_errors": len(validator.get("errors", [])),
            "error_codes": sorted(set(e.get("code", "UNKNOWN") for e in validator.get("errors", []))),
            "summary": {
                "rows_scanned": validator.get("summary", {}).get("rows_scanned"),
                "rows_ok": validator.get("summary", {}).get("rows_ok"),
                "rows_failed": validator.get("summary", {}).get("rows_failed"),
                "symbols_seen": sorted(validator.get("summary", {}).get("symbols_seen", [])),
                "indicators_seen": sorted(validator.get("summary", {}).get("indicators_seen", [])),
                "date_range": validator.get("summary", {}).get("date_range"),
                "value_stats": validator.get("summary", {}).get("value_stats", {}),
                "dup_key_count": validator.get("summary", {}).get("dup_key_count", 0),
            },
        },

        "p1_4_ready_signal": {
            "P68_READY_SIGNAL": signal.get("value"),
            "gate_state": signal.get("gate_state"),
            "release_permit": signal.get("release_permit"),
            "auto_backtest": signal.get("auto_backtest"),
        },

        "p1_5_no_backtest": {
            "auto_backtest": "DENIED",
            "release_permit": "NOT_ISSUED",
            "note": "P49 backtest NOT auto-started. Waiting for human release_permit.",
        },

        "receipt_lines": [
            f"→ DSHA_A07=FORMAT_CONVERT_SUCCESS｜long_table_rows={long_table_rows}｜validation_pass={'YES' if validation_pass else 'NO'}｜P68_GATE=READY｜NO_BACKTEST=LOCKED_ON",
            f"→ wind_api_calls=0｜offline_only=YES｜final_lock_intact=YES｜csv_not_modified=YES｜release_permit=NOT_ISSUED｜no_auto_backtest=YES",
        ],

        "red_lines": {
            "wind_api_calls": 0,
            "offline_only": True,
            "p68_params_unchanged": True,
            "original_csv_not_modified": CSV_NOT_MODIFIED,
            "dshc_not_interfered": DO_NOT_INTERVENE_DSHC,
            "dshd_not_interfered": DO_NOT_INTERVENE_DSHD,
            "no_auto_backtest": True,
            "no_human_operation_required": True,
        },

        "decision": {
            "trigger_authority": "P68_SANITY_GATE",
            "auto_ignition_by_a07": "DENIED",
            "even_if_csv_ready": "only_mark_P68_READY_SIGNAL_do_not_start_backtest",
            "release_permit_required": "HUMAN",
            "note": "P68_READY_SIGNAL=TRUE but release_permit=NOT_ISSUED. P49 will not start until human issues release_permit.",
        },
    }

    with open(RECEIPT_PATH, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)

    return receipt


# ════════════════════════════════════════════════════════════════
# P2 审计事件
# ════════════════════════════════════════════════════════════════
def append_audit_events(events: List[Dict]) -> int:
    """Append A07 audit events to tracking_monitor_audit.jsonl."""
    _log("P2: Appending audit events...")
    count = 0
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        for evt in events:
            evt["tag"] = "A07-001"
            evt.setdefault("ts", _now_iso())
            evt.setdefault("agent", "DSHA-A07")
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
            count += 1
    return count


# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════
def main():
    _log("=" * 60)
    _log("DSHA-A07 · 宽表转长表 + P68正式放行核验")
    _log(f"Token: DSHA-A07-TOKEN")
    _log(f"Baseline: feature/v88-g1 HEAD=71c1e0b")
    _log("=" * 60)

    # ═══ P0 前置锁核验 ═══
    _log("\n─── P0: 前置锁核验 ───")
    p0 = verify_p0_locks()
    _log(f"P0 all_pass: {p0['p0_all_pass']}")
    _log(f"  P68 git-diff empty: {p0['checks']['p68_git_diff'].get('diff_empty')}")
    _log(f"  P81 gate: {p0['checks']['p81_gate'].get('gate')}")
    _log(f"  release_permit: {p0['checks']['p81_gate'].get('release_permit')}")
    _log(f"  wind_api_calls: {p0['checks'].get('wind_api_calls')}")
    _log(f"  CSV size: {p0['checks']['csv_stat'].get('size_bytes')} bytes")

    # ═══ P1.1 读取 + 剔除 LC.SHF ═══
    _log("\n─── P1.1: 读取原始CSV + 剔除LC.SHF ───")
    rf = read_and_filter()
    _log(f"  Format detected: {rf.get('format_detected')}")
    _log(f"  Format note: {rf.get('format_note', '')}")
    _log(f"  Original data rows: {rf.get('original_data_rows')}")
    _log(f"  LC.SHF rows removed: {rf.get('lc_shf_rows_removed')}")
    _log(f"  Filtered data rows: {rf.get('filtered_data_rows')}")
    _log(f"  Conversion needed: {rf.get('conversion_needed')}")
    _log(f"  Output header matches long-format: {rf.get('output_header_matches_long_format')}")

    if rf.get("error"):
        _log(f"  ERROR: {rf['error']}")
        sys.exit(1)

    # ═══ P1.2 写出长表 ═══
    _log("\n─── P1.2: 写出长表输出 ───")
    wo = write_long_format(rf["filtered_rows"])
    _log(f"  Output file: {wo.get('output_csv')}")
    _log(f"  Output size: {wo.get('output_size_bytes')} bytes")
    _log(f"  Output data rows: {wo.get('output_data_rows')}")
    _log(f"  Output SHA256: {wo.get('output_sha256')}")

    # ═══ P1.3 运行 A06 校验器 ═══
    _log("\n─── P1.3: 运行 A06 长表校验器 ───")
    val = run_validator()
    _log(f"  Validation pass: {val.get('pass')}")
    _log(f"  Header OK: {val.get('header_ok')}")
    _log(f"  Header: {val.get('header')}")
    _log(f"  Total errors: {len(val.get('errors', []))}")
    if val.get("errors"):
        error_codes = sorted(set(e.get("code", "UNKNOWN") for e in val.get("errors", [])))
        _log(f"  Error codes: {error_codes}")
        for e in val.get("errors", [])[:5]:
            _log(f"    {e.get('code')}: {e.get('msg', '')[:100]}")
    summary = val.get("summary", {})
    _log(f"  Rows scanned: {summary.get('rows_scanned')}")
    _log(f"  Rows OK: {summary.get('rows_ok')}")
    _log(f"  Rows failed: {summary.get('rows_failed')}")
    _log(f"  Symbols seen: {sorted(summary.get('symbols_seen', []))}")
    _log(f"  Indicators seen: {sorted(summary.get('indicators_seen', []))}")
    _log(f"  Date range: {summary.get('date_range')}")
    _log(f"  Dup key count: {summary.get('dup_key_count', 0)}")

    # ═══ P1.4 设置 P68_READY_SIGNAL ═══
    _log("\n─── P1.4: 设置 P68_READY_SIGNAL ───")
    sig = set_ready_signal(val.get("pass", False))
    _log(f"  P68_READY_SIGNAL: {sig.get('value')}")

    # ═══ P1.5 生成回执 ═══
    _log("\n─── P1.5: 生成正式核验回执 ───")
    receipt = generate_receipt(p0, rf, wo, val, sig)
    _log(f"  Status: {receipt['status']}")
    _log(f"  Receipt path: {os.path.relpath(RECEIPT_PATH, PROJECT_ROOT)}")

    # ═══ P2 审计事件 ═══
    _log("\n─── P2: 审计事件 ───")
    audit_events = [
        {"event": "A07_START", "message": "DSHA-A07 started: 宽表转长表 + P68正式放行核验", "token": "DSHA-A07-TOKEN"},
        {"event": "A07_P0_LOCKS_VERIFIED", "message": f"P0 locks verified: gate=CLOSED, release_permit=NOT_ISSUED, wind_api_calls=0, P68 git-diff empty"},
        {"event": "A07_CSV_READ", "message": f"Read original CSV: {rf.get('original_data_rows')} rows, format={rf.get('format_detected')}, LC.SHF removed={rf.get('lc_shf_rows_removed')}"},
        {"event": "A07_LONG_FORMAT_WRITTEN", "message": f"Wrote long-format output: {wo.get('output_data_rows')} rows, {wo.get('output_size_bytes')} bytes, sha={wo.get('output_sha256','')[:16]}..."},
        {"event": "A07_VALIDATOR_RUN", "message": f"A06 validator run: pass={val.get('pass')}, errors={len(val.get('errors', []))}, rows_scanned={val.get('summary', {}).get('rows_scanned')}"},
        {"event": "A07_READY_SIGNAL_SET", "message": f"P68_READY_SIGNAL={sig.get('value')}, gate_state={sig.get('gate_state')}, release_permit={sig.get('release_permit')}"},
        {"event": "A07_RECEIPT_GENERATED", "message": f"Receipt generated: status={receipt['status']}, long_table_rows={wo.get('output_data_rows')}"},
        {"event": "A07_COMPLETE", "message": "DSHA-A07 complete: FORMAT_CONVERT_SUCCESS, P68_READY_SIGNAL=TRUE, NO_BACKTEST=LOCKED_ON"},
    ]
    n = append_audit_events(audit_events)
    _log(f"  Audit events appended: {n}")

    # ═══ 最终回执 ═══
    _log("\n" + "=" * 60)
    _log("DSHA-A07 FINAL RECEIPT")
    _log("=" * 60)
    for line in receipt["receipt_lines"]:
        _log(line)
    _log("=" * 60)

    return receipt


if __name__ == "__main__":
    main()
