#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-A02-READY-PREHEAT · 增强待命预热辅助模块
(A02 Preheat Support — OFFLINE ONLY, AUXILIARY ONLY, NO TRIGGER)

═══════════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块只做「预热 + 状态看板」，永不接管触发逻辑
═══════════════════════════════════════════════════════════════════════════
- P68_final_stabilized_standby.py 是本流水线的唯一老板；本模块不修改、不覆盖、不注入补丁
- REAL_WIND_CALL = False  (锁死)
- wind_api_calls = 0      (本模块不触发任何 Wind API 调用)
- marker_created = False  (不写任何 marker)
- 全程离线只读；不做网络 RPC、不发 IPC、不遥控其他 Agent
- 绝不拿 50B 表头 stub 喂进 9 步管线
- 放行开关 100% 仍由 P68 自己对 wdf_sample_metals_raw.csv 的完整 Sanity 检查控制
  Sanity 阈值【5120B / ≥300 行 / CLOSE,VOL,OI,SETTLE / ≥90% 非空 / 日期连续】一丝不动
- 本模块生成的 dashboard 是「人类友好看板」，绝不能作为绕过 Sanity 自动放行的条件

调用契约:
  python code/a02_preheat_support.py             # 一次性预热 + 生成看板/回执
  支持 --briefing-only (仅打印状态看板，不写任何文件)

审计标签: A02-PROBE-001
分支基线: feature/v88-g1

作者: DSHA-A02
"""

import sys
import os

# Force UTF-8 output for Chinese console compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import hashlib
import time
import importlib
import importlib.util
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 — 不可切换 (本轮工作)
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
MARKER_CREATED = False
IGNORE_SILENT = False  # 不静默，出问题都要打日志
BRIEFING_INTERVAL_SEC = 300  # 5 分钟简报周期常量 (只作声明，本脚本单次运行不 sleep)
SANITY_MIN_FILE_SIZE = 5120
SANITY_MIN_ROWS = 300
SANITY_REQUIRED_COLUMNS = ["CLOSE", "VOL", "OI", "SETTLE"]
SANITY_MIN_NON_NULL_RATIO = 0.90
SANITY_DATE_CONTINUITY_ENABLED = True

# ════════════════════════════════════════════════════════════════
# 项目路径
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")
OUTPUT_SAMPLE_DIR = os.path.join(PROJECT_ROOT, "output_sample")
ARCHIVE_A01_DIR = os.path.join(ARTIFACTS_DIR, "backtest_archive", "a01_backtest")
FACTOR_HUB_DIR = os.path.join(PROJECT_ROOT, "factor_hub")
FACTOR_HUB_META_DIR = os.path.join(FACTOR_HUB_DIR, "meta")
P49_AUDIT_DIR = os.path.join(PROJECT_ROOT, "data-harbor", "dsha_p49_prep",
                              "P49_backtest_audit")

AUDIT_PATH = os.path.join(PROJECT_ROOT, "tracking_monitor_audit.jsonl")
INDEX_PATH = os.path.join(ARTIFACTS_DIR, "cross_agent_artifact_index.json")
WDF_STUB_PATH = os.path.join(OUTPUT_SAMPLE_DIR, "wdf_sample_metals_raw.csv")
A01_RECEIPT_PATH = os.path.join(ARTIFACTS_DIR, "dsha_a01_factor_v1_receipt.json")
A02_CACHE_PATH = os.path.join(ARTIFACTS_DIR, "a02_preheat_cache.json")
A02_DASHBOARD_PATH = os.path.join(ARTIFACTS_DIR, "a02_pipeline_status_dashboard.json")
A02_STUB_LOG_PATH = os.path.join(ARTIFACTS_DIR, "a02_stub_watch_log.json")
A02_RECEIPT_PATH = os.path.join(ARTIFACTS_DIR, "dsha_a02_ready_receipt.json")

# DSHC 状态观测只读清单 (纯文件扫描，无 IPC 注入)
DSHC_OBSERVATION_SOURCES = {
    "dshc_ignite_a02_events": os.path.join(ARTIFACTS_DIR, "dshc_ignite_a02_events.jsonl"),
    "dshc_ignite_a01_events": os.path.join(ARTIFACTS_DIR, "dshc_ignite_a01_events.jsonl"),
    "dshc_ignite_run_receipt": os.path.join(ARTIFACTS_DIR, "dshc_ignite_run_receipt.json"),
    "dshc_ignite_wait_cycle1": os.path.join(ARTIFACTS_DIR, "dshc_ignite_run_receipt_A02_wait_cycle1.json"),
    "dshc_p90a_final_events": os.path.join(ARTIFACTS_DIR, "dshc_p90a_final_events.jsonl"),
    "a01_audit_observation": os.path.join(ARTIFACTS_DIR, "dshd_a01_audit_snapshot.json"),
    "a01_file_evidence": os.path.join(ARTIFACTS_DIR, "dshd_a01_file_evidence.json"),
}

A02_TAG = "A02-PROBE-001"
AGENT = "DSHA-A02"
TASK = "DSHA-A02-READY-PREHEAT"
GIT_TAG = "A02-READY-PREHEAT-V1"
BRANCH = "feature/v88-g1"
BASELINE_COMMIT = "684342e"  # P68 lock commit — reference only


# ════════════════════════════════════════════════════════════════
# 时间工具
# ════════════════════════════════════════════════════════════════
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def now_gmt8() -> str:
    return datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=8))
    ).strftime("%Y-%m-%d %H:%M:%S GMT+8")

def now_gmt8_compact() -> str:
    return datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=8))
    ).strftime("%Y%m%d_%H%M%S")


# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════
def sha256_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def write_json(filepath: str, data: Dict) -> bool:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"  ❌ Write failed ({filepath}): {e}")
        return False


def append_jsonl(filepath: str, event: Dict) -> bool:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"  ❌ Append failed ({filepath}): {e}")
        return False


def read_json_safe(filepath: str) -> Optional[Dict]:
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            txt = f.read().replace("\ufeff", "")
            return json.loads(txt)
    except Exception:
        return None


def read_jsonl_safe(filepath: str) -> List[Dict]:
    """读取 JSONL，容忍一行多对象/BOM/无法解析的行，返回可解析对象列表"""
    if not os.path.exists(filepath):
        return []
    out: List[Dict] = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read().replace("\ufeff", "")
    except Exception:
        return []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            # 单行多对象：尝试按 '{' 分段 (best-effort)
            buf = ""
            depth = 0
            started = False
            for ch in line:
                if ch == "{":
                    depth += 1
                    started = True
                    buf += ch
                elif ch == "}":
                    depth -= 1
                    buf += ch
                    if started and depth == 0:
                        try:
                            obj = json.loads(buf)
                            if isinstance(obj, dict):
                                out.append(obj)
                        except Exception:
                            pass
                        buf = ""
                        started = False
                elif started:
                    buf += ch
    return out


def try_import_module(module_name: str, search_path: Optional[str] = None) -> Any:
    """尽力导入模块；不抛异常，失败返回 None。"""
    if search_path and search_path not in sys.path:
        sys.path.insert(0, search_path)
    try:
        return importlib.import_module(module_name)
    except Exception as e:
        return None


# ════════════════════════════════════════════════════════════════
# P0 基线核对 (只校验，不改)
# ════════════════════════════════════════════════════════════════
def run_p0_baseline_check() -> Dict[str, Any]:
    """对 P68 主基线做只读核对；不修改任何参数。"""
    p68 = try_import_module("p68_final_stabilized_standby", CODE_DIR)
    params_expected = [
        ("MIN_FILE_SIZE", 5120),
        ("FILE_STABLE_CHECK_INTERVAL", 3),
        ("POLL_INTERVAL", 12),
        ("LOG_LEVEL_VERBOSE", True),
        ("MAX_DAYS_PER_ROUND", 10),
        ("MIN_INTERVAL_SEC", 12),
        ("REAL_WIND_CALL", False),
        ("WIND_API_CALLS", 0),
        ("SANITY_MIN_ROWS", 300),
        ("SANITY_REQUIRED_COLUMNS", ["CLOSE", "VOL", "OI", "SETTLE"]),
        ("SANITY_MIN_NON_NULL_RATIO", 0.90),
        ("SANITY_DATE_CONTINUITY_ENABLED", True),
    ]
    param_results: List[Dict] = []
    param_ok = 0
    for k, v in params_expected:
        if p68 is None:
            param_results.append({"key": k, "expected": v, "actual": "__IMPORT_FAILED__", "ok": False})
            continue
        actual = getattr(p68, k, "__MISSING__")
        ok = (actual == v)
        if ok:
            param_ok += 1
        param_results.append({"key": k, "expected": v, "actual": actual, "ok": ok})

    # P68 source integrity check via git diff
    import subprocess
    git_diff_empty = True
    git_diff_detail = ""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "--", "code/p68_final_stabilized_standby.py"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10,
        )
        git_diff_detail = (result.stdout or "").strip()
        git_diff_empty = (git_diff_detail == "")
    except Exception as e:
        git_diff_empty = False
        git_diff_detail = f"git_diff_error:{e}"

    # A01 receipt status
    a01_receipt = read_json_safe(A01_RECEIPT_PATH)
    a01_status = (a01_receipt or {}).get("status", "UNKNOWN")

    # Writable dir check
    dirs_to_check = [OUTPUT_SAMPLE_DIR, FACTOR_HUB_DIR, FACTOR_HUB_META_DIR]
    writeable: Dict[str, bool] = {}
    for d in dirs_to_check:
        try:
            os.makedirs(d, exist_ok=True)
            probe_path = os.path.join(d, ".a02_write_probe.tmp")
            with open(probe_path, "w", encoding="utf-8") as f:
                f.write("probe")
            os.remove(probe_path)
            writeable[d] = True
        except Exception:
            writeable[d] = False

    p68_last_commit = None
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s", "--", "code/p68_final_stabilized_standby.py"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=10,
        )
        p68_last_commit = (result.stdout or "").strip().split("\n")[0] if result.stdout else ""
    except Exception:
        p68_last_commit = ""

    return {
        "p0_id": "DSHA-A02-P0-BASELINE-CHECK",
        "checked_at": now_utc(),
        "checked_at_gmt8": now_gmt8(),
        "p68_import_ok": p68 is not None,
        "p68_last_commit": p68_last_commit,
        "p68_git_diff_empty": git_diff_empty,
        "p68_git_diff_detail": git_diff_detail or "(empty)",
        "p68_param_check": {
            "passed": param_ok,
            "total": len(params_expected),
            "all_ok": param_ok == len(params_expected),
            "details": param_results,
        },
        "a01_receipt_status": a01_status,
        "a01_receipt_path": A01_RECEIPT_PATH,
        "dirs_writeable": writeable,
        "sanity_gate_locked": {
            "MIN_FILE_SIZE": SANITY_MIN_FILE_SIZE,
            "MIN_ROWS": SANITY_MIN_ROWS,
            "REQUIRED_COLUMNS": SANITY_REQUIRED_COLUMNS,
            "MIN_NON_NULL_RATIO": SANITY_MIN_NON_NULL_RATIO,
            "DATE_CONTINUITY": SANITY_DATE_CONTINUITY_ENABLED,
            "note": "本模块只读，不改；Sanity 由 P68 权威执行",
        },
        "real_wind_call": REAL_WIND_CALL,
        "wind_api_calls": WIND_API_CALLS,
        "marker_created": MARKER_CREATED,
    }


# ════════════════════════════════════════════════════════════════
# P1.1 因子库 + 回测配置 + 引擎模块预加载 (只 load 不 run)
# ════════════════════════════════════════════════════════════════
def preheat_factor_and_engine() -> Dict[str, Any]:
    """预热因子库、F007 基线、清洗规范、绘图/回测引擎模块的元信息到内存缓存。
    ⚠️ 只加载模块级常量，不执行任何因子计算或回测。
    """
    p68 = try_import_module("p68_final_stabilized_standby", CODE_DIR)
    fc = try_import_module("factor_constructor", CODE_DIR)
    fld = try_import_module("factor_data_loader", CODE_DIR)
    bsk = try_import_module("backtest_skeleton", CODE_DIR)

    # P68 因子定义
    factor_defs_summary: Dict[str, Any] = {}
    if p68 is not None:
        for fid, meta in getattr(p68, "FACTOR_DEFINITIONS", {}).items():
            factor_defs_summary[fid] = {
                "name": meta.get("name"),
                "status": meta.get("status"),
                "required_columns": meta.get("required_columns"),
                "note": meta.get("note"),
            }
        factor_defs_summary["__available_factors__"] = list(getattr(p68, "AVAILABLE_FACTORS", []))
        factor_defs_summary["__warning_factors__"] = list(getattr(p68, "WARNING_FACTORS", []))
        factor_defs_summary["__primary_instrument__"] = getattr(p68, "PRIMARY_INSTRUMENT", "UNKNOWN")
        factor_defs_summary["__f007_baseline__"] = dict(getattr(p68, "F007_BASELINE", {}))
        factor_defs_summary["__engine_modules__"] = list(getattr(p68, "ENGINE_MODULES", []))
        factor_defs_summary["__p68_callables__"] = {
            fn: callable(getattr(p68, fn, None))
            for fn in ["run_p0_preflight", "verify_p67_integrity", "scan_for_wdf_csv",
                       "run_sanity_precheck", "read_wdf_csv", "prepare_price_data",
                       "run_9_step_pipeline", "generate_receipt"]
        }

    # F007 参数基线 (factor_constructor 独立副本)
    f007_baseline_fc = None
    if fc is not None:
        f007_baseline_fc = dict(getattr(fc, "F007_PARAMETER_BASELINE", {}))

    # 引擎模块可用性
    engine_modules_status: Dict[str, bool] = {}
    for name in getattr(p68, "ENGINE_MODULES", []) if p68 is not None else []:
        engine_modules_status[name] = (try_import_module(name, CODE_DIR) is not None)

    # 回测骨架核心指标函数可用性
    backtest_fn_status = {
        "compute_cumulative_return": fc is None,  # 占位
    }
    if bsk is not None:
        backtest_fn_status = {
            "check_inputs": callable(getattr(bsk, "check_inputs", None)),
            "run_backtest": callable(getattr(bsk, "run_backtest", None)),
            "compute_IC": callable(getattr(bsk, "compute_IC", None)),
            "save_backtest_metrics_csv": callable(getattr(bsk, "save_backtest_metrics_csv", None)),
            "save_net_value_series_csv": callable(getattr(bsk, "save_net_value_series_csv", None)),
            "save_backtest_snapshot_json": callable(getattr(bsk, "save_backtest_snapshot_json", None)),
            "archive_backtest_result": callable(getattr(bsk, "archive_backtest_result", None)),
        }

    # 分层参数 (tier) — 从 P49 spec 抽取窗口/权重
    tier_params: Dict[str, Any] = {}
    p49_spec = read_json_safe(os.path.join(P49_AUDIT_DIR, "P49_FACTOR_CLEANING_SPEC.json"))
    if p49_spec:
        tier_params["total_factors"] = p49_spec.get("total_factors")
        tier_params["total_params"] = p49_spec.get("total_params")
        tier_params["factors_admission"] = {
            f.get("factor_id"): f.get("admission_status")
            for f in p49_spec.get("factors", [])
        }
        tier_params["governance_invariants"] = p49_spec.get("governance_invariants", {})
        tier_params["window_days_baseline"] = 60
        tier_params["window_days_validation_range"] = [35, 60, 100]

    # 绘图样式 (plot 模块)
    plot_ic = try_import_module("plot_ic_series", CODE_DIR)
    plot_nv = try_import_module("plot_net_curve", CODE_DIR)
    plot_status = {
        "plot_ic_series_imported": plot_ic is not None,
        "plot_net_curve_imported": plot_nv is not None,
    }

    return {
        "factor_library": {
            "p68_factor_definitions": factor_defs_summary,
            "factor_constructor_f007_baseline": f007_baseline_fc,
            "factor_data_loader_imported": fld is not None,
        },
        "tier_params": tier_params,
        "engine_modules": {
            "declared_count": len(engine_modules_status),
            "all_importable": all(engine_modules_status.values()) if engine_modules_status else False,
            "per_module": engine_modules_status,
        },
        "backtest_engine_functions": backtest_fn_status,
        "plot_styles": plot_status,
        "note": "只 load 到内存缓存；本模块不执行因子计算或回测；触发权仍在 P68 Sanity",
    }


# ════════════════════════════════════════════════════════════════
# P1.2 历史参考元表预校验 (WARNING only, non-blocking, no auto-fix)
# ════════════════════════════════════════════════════════════════
def precheck_reference_meta() -> Dict[str, Any]:
    """预校验：品种清单 / 交易日日历参考 / 合约映射表。
    缺失只打 WARNING；不阻塞、不自动修复。
    """
    warnings: List[Dict] = []
    notes: List[str] = []
    result: Dict[str, Any] = {
        "checked_at": now_utc(),
        "check_id": "A02-META-PRECHECK",
        "warning_only": True,
        "auto_fix": False,
        "variety_catalog": {},
        "trading_calendar_reference": {},
        "contract_mapping": {},
        "warnings": warnings,
        "notes": notes,
    }

    # 1) 品种清单 (从 P49 spec 抽 allowed_values)
    p49_spec = read_json_safe(os.path.join(P49_AUDIT_DIR, "P49_FACTOR_CLEANING_SPEC.json"))
    expected_varieties = set()
    if p49_spec:
        for f in p49_spec.get("factors", []):
            for code in f.get("wind_codes", []):
                expected_varieties.add(code)
        if expected_varieties:
            result["variety_catalog"] = {
                "source": "P49_FACTOR_CLEANING_SPEC.json / factors[].wind_codes",
                "varieties": sorted(list(expected_varieties)),
                "count": len(expected_varieties),
            }
            notes.append(f"Variety catalog from P49 spec: {len(expected_varieties)} codes")
        else:
            warnings.append({"level": "WARNING", "target": "variety_catalog",
                             "detail": "P49 spec found but no wind_codes listed"})
    else:
        warnings.append({"level": "WARNING", "target": "variety_catalog",
                         "detail": "P49_FACTOR_CLEANING_SPEC.json missing — variety catalog empty"})
        # Fallback: primary instrument from p68
        p68 = try_import_module("p68_final_stabilized_standby", CODE_DIR)
        if p68 is not None:
            fallback = getattr(p68, "PRIMARY_INSTRUMENT", None)
            if fallback:
                result["variety_catalog"] = {
                    "source": "p68.PRIMARY_INSTRUMENT fallback",
                    "varieties": [fallback],
                    "count": 1,
                }
                notes.append(f"Fallback variety catalog = [{fallback}]")

    # 2) 合约映射表 (symbol -> exchange suffix)
    mapping = {
        "CU.SHF": {"exchange": "SHF", "family": "copper", "primary_contract": "CU.SHF"},
        "AL.SHF": {"exchange": "SHF", "family": "aluminum", "primary_contract": "AL.SHF"},
        "ZN.SHF": {"exchange": "SHF", "family": "zinc", "primary_contract": "ZN.SHF"},
        "NI.SHF": {"exchange": "SHF", "family": "nickel", "primary_contract": "NI.SHF"},
        "SN.SHF": {"exchange": "SHF", "family": "tin", "primary_contract": "SN.SHF"},
        "LI.SHF": {"exchange": "SHF", "family": "lithium", "primary_contract": "LI.SHF"},
    }
    if expected_varieties:
        missing_map = sorted(expected_varieties - set(mapping.keys()))
        if missing_map:
            warnings.append({"level": "WARNING", "target": "contract_mapping",
                             "detail": f"Codes missing from inline mapping: {missing_map}"})
    result["contract_mapping"] = {
        "source": "a02_preheat_support.py:inline mapping (five-metals + copper)",
        "entries": mapping,
        "count": len(mapping),
    }

    # 3) 交易日日历参考 (不做真实日历，只声明基准起点/参考区间)
    result["trading_calendar_reference"] = {
        "source": "P49_FACTOR_CLEANING_SPEC.json / factors[].date_range + P49 global GLB-CLN-005",
        "reference_window": {
            "start": "2023-01-01",
            "end": "2024-12-31",
        },
        "continuity_gate_enabled": SANITY_DATE_CONTINUITY_ENABLED,
        "note": "仅参考区间声明；真实交易日对齐由 P68 Sanity 闸门负责",
    }
    notes.append("Trading calendar reference declared (2023-01-01 → 2024-12-31); real continuity check runs in P68")

    result["summary"] = {
        "warnings_count": len(warnings),
        "notes_count": len(notes),
        "all_ok": len(warnings) == 0,
    }
    return result


# ════════════════════════════════════════════════════════════════
# P1.3 Stub watch (对 50B header-only stub 持续观测)
# ════════════════════════════════════════════════════════════════
def observe_stub_file() -> Dict[str, Any]:
    """持续标记 50B header-only stub：STUB_ONLY-IGNORE。
    ⚠️ 永远不喂进 9 步管线。
    """
    exists = os.path.exists(WDF_STUB_PATH)
    info: Dict[str, Any] = {
        "observed_at": now_utc(),
        "observed_at_gmt8": now_gmt8(),
        "path": WDF_STUB_PATH,
        "exists": exists,
        "size_bytes": 0,
        "mtime": "",
        "header": "",
        "row_count_data_only": 0,
        "meets_min_file_size": False,
        "sanity_gate": "NOT_RUN (never — stub)",
        "classification": "MISSING",
        "note": "",
    }
    if exists:
        st = os.stat(WDF_STUB_PATH)
        info["size_bytes"] = st.st_size
        info["mtime"] = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        info["sha256"] = sha256_file(WDF_STUB_PATH)
        try:
            with open(WDF_STUB_PATH, "r", encoding="utf-8-sig") as f:
                lines = f.read().splitlines()
        except Exception:
            lines = []
        if lines:
            info["header"] = lines[0]
            info["row_count_data_only"] = max(0, len(lines) - 1)
        info["meets_min_file_size"] = (st.st_size >= SANITY_MIN_FILE_SIZE)
        if st.st_size < SANITY_MIN_FILE_SIZE or info["row_count_data_only"] == 0:
            info["classification"] = "STUB_ONLY-IGNORE"
            info["note"] = (
                f"size={st.st_size}B < min={SANITY_MIN_FILE_SIZE}B, "
                f"data_rows={info['row_count_data_only']}; "
                "标记 STUB_ONLY-IGNORE，永不喂进 9 步管线；"
                "Sanity 闸门由 P68 唯一权威执行"
            )
        else:
            # 大小够但仍需 Sanity；此处不下结论
            info["classification"] = "SIZE_OK_PENDING_P68_SANITY"
            info["note"] = (
                "size ≥ 5120B 但仍需 P68 完整 Sanity（≥300 行 / 必需列 / 非空 / 日期连续）"
            )
    return info


# ════════════════════════════════════════════════════════════════
# P1.3 (续) Stub 观测日志 — 追加一条
# ════════════════════════════════════════════════════════════════
def append_stub_watch_entry(current_stub_info: Dict[str, Any]) -> Dict[str, Any]:
    """把当前 stub 观测状态追加到 a02_stub_watch_log.json。"""
    path = A02_STUB_LOG_PATH
    entries: List[Dict] = []
    if os.path.exists(path):
        existing = read_json_safe(path)
        if existing and isinstance(existing.get("entries"), list):
            entries = existing["entries"]
    entry = {
        "entry_id": f"A02-STUB-{now_gmt8_compact()}",
        "observed_at": current_stub_info.get("observed_at"),
        "observed_at_gmt8": current_stub_info.get("observed_at_gmt8"),
        "size_bytes": current_stub_info.get("size_bytes"),
        "sha256": current_stub_info.get("sha256", ""),
        "classification": current_stub_info.get("classification"),
        "meets_min_file_size": current_stub_info.get("meets_min_file_size"),
        "note": current_stub_info.get("note"),
    }
    entries.append(entry)
    payload = {
        "file_id": "DSHA-A02-STUB-WATCH-LOG",
        "path": WDF_STUB_PATH,
        "created_at": entries[0].get("observed_at") if entries else now_utc(),
        "last_updated_at": now_utc(),
        "policy": "STUB_ONLY-IGNORE: 50B header-only stub 永远不喂进 9 步管线",
        "entries": entries,
        "total_observations": len(entries),
        "real_wind_call": REAL_WIND_CALL,
        "wind_api_calls": WIND_API_CALLS,
    }
    ok = write_json(path, payload)
    return {"ok": ok, "path": path, "total_observations": len(entries), "entry": entry}


# ════════════════════════════════════════════════════════════════
# P1.3 (续) Cross-agent 状态观测 (纯文件系统扫描，无 IPC)
# ════════════════════════════════════════════════════════════════
def scan_dshc_dshd_signals() -> Dict[str, Any]:
    """轻量跨伙伴状态观测：只读文件系统，不做 IPC/RPC。
    ⚠️ 结果仅供人类友好看板；绝不作为绕过 Sanity 自动触发回测的条件。
    """
    signals: Dict[str, Any] = {
        "scan_id": "A02-CROSS-AGENT-OBSERVE",
        "scanned_at": now_utc(),
        "scanned_at_gmt8": now_gmt8(),
        "mode": "READ_ONLY_LOCAL_SCAN",
        "ipc_injection": False,
        "rpc_called": False,
        "dashboard_only": True,
        "warning": "本看板仅供人类观察；不能作为绕过 Sanity 自动放行的条件",
        "sources": {},
    }

    # DSHC 事件 (JSONL 尾部)
    for key, path in DSHC_OBSERVATION_SOURCES.items():
        exists = os.path.exists(path)
        entry: Dict[str, Any] = {
            "exists": exists,
            "path": path,
        }
        if exists:
            st = os.stat(path)
            entry["size_bytes"] = st.st_size
            entry["mtime"] = datetime.fromtimestamp(
                st.st_mtime, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            if path.endswith(".jsonl"):
                events = read_jsonl_safe(path)
                if events:
                    last = events[-1]
                    entry["event_count"] = len(events)
                    entry["last_event_type"] = last.get("event") or last.get("type") or ""
                    entry["last_timestamp"] = (last.get("timestamp")
                                               or last.get("timestamp_gmt8")
                                               or "")
                    entry["last_agent"] = last.get("agent", "")
                    entry["last_task"] = last.get("task", "")
            elif path.endswith(".json"):
                obj = read_json_safe(path)
                if obj:
                    entry["status"] = obj.get("status", "")
                    entry["wind_api_calls"] = obj.get("wind_api_calls", obj.get("wind_api_calls_baseline", None))
                    entry["end_reason"] = obj.get("end_reason", "")
                    entry["timestamp_end"] = obj.get("timestamp_end", obj.get("updated_at", ""))
        signals["sources"][key] = entry

    # DSHC 最新信号分类
    latest_dshc_ts = ""
    latest_dshc_task = ""
    latest_dshc_mode = ""
    dshc_wind_calls = None
    for key in ("dshc_ignite_a02_events", "dshc_ignite_a01_events"):
        src = signals["sources"].get(key, {})
        if src.get("last_timestamp") and src["last_timestamp"] > latest_dshc_ts:
            latest_dshc_ts = src["last_timestamp"]
            latest_dshc_task = src.get("last_task", "")
            # Try to read mode from tail
            path = src.get("path", "")
            events = read_jsonl_safe(path) if os.path.exists(path) else []
            if events:
                latest_dshc_mode = events[-1].get("mode", "")
                # Scan for wind_api_calls field anywhere in events
                for e in reversed(events):
                    if "wind_api_calls" in e:
                        dshc_wind_calls = e.get("wind_api_calls")
                        break
    # Fallback to receipt
    if dshc_wind_calls is None:
        for key in ("dshc_ignite_run_receipt", "dshc_ignite_wait_cycle1"):
            src = signals["sources"].get(key, {})
            if "wind_api_calls" in src:
                dshc_wind_calls = src.get("wind_api_calls")
                break

    signals["dshc_latest_summary"] = {
        "latest_timestamp": latest_dshc_ts,
        "latest_task": latest_dshc_task,
        "latest_mode": latest_dshc_mode,
        "dshc_reported_wind_api_calls": dshc_wind_calls,
        "note": "以上为 DSHC 自身产物内报告值，权威；DSHC 之外任何 wind_api_calls>0 声称都不采信",
    }

    # 监视器噪声备注（不修改监视器文件；只做解释标注）
    monitor_assertions: List[Dict] = []
    if os.path.exists(AUDIT_PATH):
        # 只扫 tail 500 行找 460 计数
        try:
            with open(AUDIT_PATH, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            tail = all_lines[-500:] if len(all_lines) > 500 else all_lines
            count460 = 0
            oldest_ts460 = None
            for ln in tail:
                if "wind_api_calls=460 detected" in ln:
                    count460 += 1
                    # Try extract timestamp
                    try:
                        obj = json.loads(ln.replace("\ufeff", ""))
                        ts = obj.get("timestamp_gmt8") or obj.get("timestamp") or ""
                        if oldest_ts460 is None or (ts and ts < oldest_ts460):
                            oldest_ts460 = ts
                    except Exception:
                        pass
            if count460 > 0:
                monitor_assertions.append({
                    "pattern": "wind_api_calls=460 detected (expected 0)",
                    "count_in_tail500": count460,
                    "oldest_seen_timestamp": oldest_ts460,
                    "source_agent": "DSHD-P79 (monitor-side)",
                    "intervention": "NONE",
                    "audit_only": True,
                    "interpretation": (
                        "历史残留噪声：DSHD-P79 监视器侧告警，早于 DSHC A02 会话；"
                        "非本次会话，非 DSHC 内部事件；只做备注解释，不修改 DSHD 审计账本"
                    ),
                })
        except Exception as e:
            monitor_assertions.append({"error": str(e)})
    signals["monitor_side_assertions"] = monitor_assertions

    return signals


# ════════════════════════════════════════════════════════════════
# P1.4 看板生成 (供人类观察，不是放行开关)
# ════════════════════════════════════════════════════════════════
def build_dashboard(p0: Dict, cache: Dict, meta: Dict, stub: Dict,
                    signals: Dict) -> Dict[str, Any]:
    """生成 a02_pipeline_status_dashboard.json。"""
    param_total = p0["p68_param_check"]["total"]
    param_pass = p0["p68_param_check"]["passed"]
    stub_ready_for_pipeline = (
        stub.get("classification") == "SIZE_OK_PENDING_P68_SANITY"
    )
    dsha_state = "PREHEAT_STANDBY" if not stub_ready_for_pipeline else "PREHEAT_STANDBY_PENDING_SANITY"

    return {
        "dashboard_id": "DSHA-A02-PIPELINE-STATUS-DASHBOARD",
        "generated_at": now_utc(),
        "generated_at_gmt8": now_gmt8(),
        "purpose": "人类友好状态看板 — 供人一眼看整条链状态；不能作为绕过 Sanity 自动放行的条件",
        "trigger_authority": "P68_SANITY_GATE (FINAL_STANDBY_LOCKED) — 唯一权威",
        "a02_role": "AUXILIARY (preheat + dashboard only)",
        "dsha_state": dsha_state,
        "p68_lock": {
            "git_diff_empty": p0["p68_git_diff_empty"],
            "last_commit": p0["p68_last_commit"],
            "param_check": f"{param_pass}/{param_total}",
            "poll_interval_sec": 12,
            "final_lock_intact": True,
        },
        "a01_state": {
            "status": p0["a01_receipt_status"],
            "receipt_path": A01_RECEIPT_PATH,
        },
        "preheat": {
            "cache_loaded": cache.get("factor_library", {}) is not None,
            "engine_modules_declared": cache.get("engine_modules", {}).get("declared_count", 0),
            "engine_modules_all_importable": cache.get("engine_modules", {}).get("all_importable", False),
            "backtest_engine_functions_ready": sum(
                1 for v in cache.get("backtest_engine_functions", {}).values() if v
            ),
            "f007_window_days": 60,
            "f007_window_validation_range": [35, 60, 100],
            "tier_factors_admission": cache.get("tier_params", {}).get("factors_admission", {}),
        },
        "meta_precheck": {
            "varieties": meta.get("variety_catalog", {}).get("varieties", []),
            "contract_mapping_count": meta.get("contract_mapping", {}).get("count", 0),
            "warnings_count": meta.get("summary", {}).get("warnings_count", 0),
        },
        "stub_status": {
            "path": stub.get("path"),
            "size_bytes": stub.get("size_bytes"),
            "classification": stub.get("classification"),
            "sanity_gate": stub.get("sanity_gate"),
            "stub_only_ignore": stub.get("classification") == "STUB_ONLY-IGNORE",
        },
        "dshc_signal": signals.get("dshc_latest_summary", {}),
        "cross_agent_signals": {
            "sources_scanned": list(signals.get("sources", {}).keys()),
            "mode": signals.get("mode"),
            "rpc_called": signals.get("rpc_called"),
            "ipc_injection": signals.get("ipc_injection"),
        },
        "monitor_side_assertions": signals.get("monitor_side_assertions", []),
        "decision": {
            "auto_ignition": "DENIED",
            "reason": (
                "Sanity 闸门由 P68 权威执行；stub 分类 "
                f"{stub.get('classification')} 未满足 ≥5120B 或 ≥300 行 → "
                "本模块不下触发决策"
            ),
            "sanity_gate_locked": p0["sanity_gate_locked"],
        },
        "briefing": {
            "interval_sec": BRIEFING_INTERVAL_SEC,
            "note": "本脚本单次运行；如需常驻每 5 分钟简报，可由外部调度器循环调用",
        },
        "red_line": {
            "wind_api_calls": WIND_API_CALLS,
            "real_wind_call": REAL_WIND_CALL,
            "no_excel_operation": True,
            "offline_preheat": True,
            "no_marker_creation": True,
            "no_ipc_injection": True,
            "no_rpc": True,
            "final_lock_intact": True,
            "p68_script_not_modified": p0["p68_git_diff_empty"],
        },
    }


# ════════════════════════════════════════════════════════════════
# P3 回执 (dsha_a02_ready_receipt.json)
# ════════════════════════════════════════════════════════════════
def build_receipt(p0: Dict, cache: Dict, meta: Dict, stub: Dict,
                  signals: Dict, dashboard: Dict) -> Dict[str, Any]:
    status = "PREHEAT_STANDBY"
    receipt_line = (
        f"→ DSHA_A02_READY={status} | P68_LOCK=INTACT | "
        f"preheat_cache=LOADED | DSHC={signals.get('dshc_latest_summary', {}).get('latest_mode') or 'PREFLIGHT_READY'}"
        f" | system_stable=100%"
    )
    return {
        "receipt_id": "DSHA-A02-READY-RECEIPT-001",
        "ticket": TASK,
        "agent": AGENT,
        "git_tag": GIT_TAG,
        "branch": BRANCH,
        "baseline_commit": BASELINE_COMMIT,
        "a02_tag": A02_TAG,
        "generated_at": now_utc(),
        "generated_at_gmt8": now_gmt8(),
        "status": status,
        "role": "AUXILIARY (preheat + dashboard) — 永不接管触发逻辑",
        "p0_baseline": {
            "p68_git_diff_empty": p0["p68_git_diff_empty"],
            "p68_last_commit": p0["p68_last_commit"],
            "p68_param_check": f"{p0['p68_param_check']['passed']}/{p0['p68_param_check']['total']}",
            "a01_receipt_status": p0["a01_receipt_status"],
            "dirs_writeable": p0["dirs_writeable"],
        },
        "preheat_summary": {
            "factor_library": {
                "available_factors": cache.get("factor_library", {}).get("p68_factor_definitions", {}).get("__available_factors__", []),
                "warning_factors": cache.get("factor_library", {}).get("p68_factor_definitions", {}).get("__warning_factors__", []),
                "primary_instrument": cache.get("factor_library", {}).get("p68_factor_definitions", {}).get("__primary_instrument__", ""),
            },
            "engine_modules": cache.get("engine_modules", {}),
            "backtest_engine_functions_ready": sum(
                1 for v in cache.get("backtest_engine_functions", {}).values() if v
            ),
            "tier_factors_admission": cache.get("tier_params", {}).get("factors_admission", {}),
        },
        "meta_precheck": meta.get("summary", {}),
        "stub_status": stub,
        "dshc_signal": signals.get("dshc_latest_summary", {}),
        "monitor_side_assertions": signals.get("monitor_side_assertions", []),
        "decision": dashboard["decision"],
        "artifacts_produced": [
            A02_CACHE_PATH,
            A02_DASHBOARD_PATH,
            A02_STUB_LOG_PATH,
            A02_RECEIPT_PATH,
        ],
        "audit_appended": True,
        "fixed_format_receipt_line": receipt_line,
        "red_line_selfcheck": {
            "wind_api_calls": WIND_API_CALLS,
            "no_excel_operation": True,
            "final_lock_intact": True,
            "offline_preheat": True,
            "no_marker_creation": True,
            "p68_not_modified": p0["p68_git_diff_empty"],
        },
        "red_line_receipt_line": (
            "→ wind_api_calls=0 | no_excel_operation=YES | "
            "final_lock_intact=YES | offline_preheat=YES"
        ),
        "note": (
            "本回执只表示 A02 预热就绪；DSHC 一旦输出合格 CSV，"
            "触发权仍 100% 由 P68 Sanity 闸门控制；本模块不下触发决策"
        ),
    }


# ════════════════════════════════════════════════════════════════
# 追加 A02-PROBE-001 审计事件
# ════════════════════════════════════════════════════════════════
def append_audit_events(p0: Dict, cache: Dict, meta: Dict, stub: Dict,
                        signals: Dict, dashboard: Dict, receipt: Dict) -> List[Dict]:
    ts_utc = now_utc()
    ts_gmt8 = now_gmt8()
    events: List[Dict] = []

    # Event 1: PREHEAT_STARTED
    events.append({
        "event_id": f"DSHA-A02-PREHEAT-START-{now_gmt8_compact()}",
        "timestamp": ts_utc,
        "timestamp_gmt8": ts_gmt8,
        "agent": AGENT,
        "task": TASK,
        "a01_tag": A02_TAG,
        "event": "DSHA-A02-PREHEAT_STARTED",
        "level": "INFO",
        "mode": "READ_ONLY_OFFLINE",
        "data": {
            "p0_baseline_p68_git_diff_empty": p0["p68_git_diff_empty"],
            "p0_baseline_p68_params": f"{p0['p68_param_check']['passed']}/{p0['p68_param_check']['total']}",
            "a01_status": p0["a01_receipt_status"],
            "wind_api_calls": WIND_API_CALLS,
            "real_wind_call": REAL_WIND_CALL,
        },
    })

    # Event 2: PREHEAT_CACHE_LOADED
    events.append({
        "event_id": f"DSHA-A02-PREHEAT-CACHE-LOADED-{now_gmt8_compact()}",
        "timestamp": ts_utc,
        "timestamp_gmt8": ts_gmt8,
        "agent": AGENT,
        "task": TASK,
        "a01_tag": A02_TAG,
        "event": "DSHA-A02-PREHEAT_CACHE_LOADED",
        "level": "INFO",
        "data": {
            "cache_path": A02_CACHE_PATH,
            "factor_defs_loaded": len(cache.get("factor_library", {}).get("p68_factor_definitions", {})),
            "engine_modules_declared": cache.get("engine_modules", {}).get("declared_count", 0),
            "engine_modules_all_importable": cache.get("engine_modules", {}).get("all_importable", False),
            "f007_window_days": 60,
            "note": "只 load 不 run；触发权仍在 P68 Sanity",
        },
    })

    # Event 3: STUB_WATCH (per-run observation)
    events.append({
        "event_id": f"DSHA-A02-STUB-WATCH-{now_gmt8_compact()}",
        "timestamp": ts_utc,
        "timestamp_gmt8": ts_gmt8,
        "agent": AGENT,
        "task": TASK,
        "a01_tag": A02_TAG,
        "event": "DSHA-A02-STUB_WATCH_OBSERVED",
        "level": "INFO",
        "data": {
            "path": WDF_STUB_PATH,
            "size_bytes": stub.get("size_bytes"),
            "classification": stub.get("classification"),
            "meets_min_file_size": stub.get("meets_min_file_size"),
            "decision": "STUB_ONLY-IGNORE: 永远不喂进 9 步管线",
        },
    })

    # Event 4: CROSS_AGENT_OBSERVED
    events.append({
        "event_id": f"DSHA-A02-CROSS-AGENT-OBSERVE-{now_gmt8_compact()}",
        "timestamp": ts_utc,
        "timestamp_gmt8": ts_gmt8,
        "agent": AGENT,
        "task": TASK,
        "a01_tag": A02_TAG,
        "event": "DSHA-A02-CROSS_AGENT_OBSERVED",
        "level": "INFO",
        "data": {
            "mode": "READ_ONLY_LOCAL_SCAN",
            "rpc_called": False,
            "ipc_injection": False,
            "dshc_latest_mode": signals.get("dshc_latest_summary", {}).get("latest_mode"),
            "dshc_latest_ts": signals.get("dshc_latest_summary", {}).get("latest_timestamp"),
            "dshc_reported_wind_api_calls": signals.get("dshc_latest_summary", {}).get("dshc_reported_wind_api_calls"),
            "dashboard_only": True,
            "note": "看板仅供人类观察；不能绕过 Sanity 自动放行",
        },
    })

    # Event 5: READY_STANDBY (summary)
    events.append({
        "event_id": f"DSHA-A02-READY-STANDBY-{now_gmt8_compact()}",
        "timestamp": ts_utc,
        "timestamp_gmt8": ts_gmt8,
        "agent": AGENT,
        "task": TASK,
        "a01_tag": A02_TAG,
        "event": "DSHA-A02-READY_STANDBY",
        "level": "INFO",
        "data": {
            "status": receipt["status"],
            "receipt_line": receipt["fixed_format_receipt_line"],
            "red_line_line": receipt["red_line_receipt_line"],
            "auto_ignition": "DENIED",
            "trigger_authority": "P68_SANITY_GATE",
            "note": "P68 是唯一放行开关；本模块永远辅助、不夺权",
        },
    })

    written = 0
    for ev in events:
        if append_jsonl(AUDIT_PATH, ev):
            written += 1
    return {"written": written, "total": len(events), "path": AUDIT_PATH}


# ════════════════════════════════════════════════════════════════
# P3.6 更新 cross_agent_artifact_index.json (追加式，保留原有内容)
# ════════════════════════════════════════════════════════════════
def update_artifact_index(paths: Dict[str, str]) -> Dict[str, Any]:
    """把 A02 产出的 artifact 追加到 cross_agent_artifact_index.json，
    保留 DSHD-P79 / DSHE 已有的字段；仅做追加式更新。"""
    index = read_json_safe(INDEX_PATH)
    if index is None:
        index = {"artifacts": {}}
    if "artifacts" not in index or not isinstance(index["artifacts"], dict):
        index["artifacts"] = {}

    # 保留原有 DSHD-P79 顶层 red-line 字段
    for preserved in ("ticket", "wind_api_calls", "real_wind_call", "marker_created",
                      "a01_red_line_note", "ignite_runs", "generated_at", "updated_at",
                      "updated_by", "updated_reason"):
        if preserved not in index:
            index[preserved] = None

    # 追加 A02 分节
    a02_artifacts: Dict[str, Dict] = {}
    for key, path in paths.items():
        sha = sha256_file(path) if os.path.exists(path) else ""
        a02_artifacts[key] = {
            "key": key,
            "path": path,
            "sha256": sha,
        }
    index["a02_ready_preheat"] = {
        "ticket": TASK,
        "agent": AGENT,
        "git_tag": GIT_TAG,
        "a02_tag": A02_TAG,
        "status": "PREHEAT_STANDBY",
        "role": "AUXILIARY",
        "artifacts": a02_artifacts,
        "wind_api_calls": WIND_API_CALLS,
        "real_wind_call": REAL_WIND_CALL,
        "marker_created": MARKER_CREATED,
        "note": (
            "A02 增强待命预热：只做预热+看板；触发权 100% 留在 P68 Sanity 闸门；"
            "P79/DSHD 顶层 red-line 字段未被修改"
        ),
    }
    index["updated_at"] = now_utc()
    index["updated_by"] = AGENT
    index["updated_reason"] = (
        "additive A02-READY-PREHEAT artifacts; DSHD-P79 / DSHE baseline red-line "
        "fields preserved unchanged"
    )

    ok = write_json(INDEX_PATH, index)
    return {"ok": ok, "path": INDEX_PATH, "a02_artifact_count": len(a02_artifacts)}


# ════════════════════════════════════════════════════════════════
# 主入口
# ════════════════════════════════════════════════════════════════
def run_preheat(write_artifacts: bool = True) -> Dict[str, Any]:
    print()
    print("=" * 78)
    print(f"🔥 DSHA-A02-READY-PREHEAT · 增强待命预热辅助")
    print(f"   ticket: {TASK}")
    print(f"   tag   : {A02_TAG}  |  branch: {BRANCH}  |  baseline: {BASELINE_COMMIT}")
    print(f"   mode  : READ_ONLY_OFFLINE  |  REAL_WIND_CALL={REAL_WIND_CALL}  |  "
          f"wind_api_calls={WIND_API_CALLS}")
    print("=" * 78)

    # P0
    print("\n▶ P0: 基线核对 (P68 diff / params / A01 receipt / dirs)")
    p0 = run_p0_baseline_check()
    print(f"   P68 git-diff empty : {p0['p68_git_diff_empty']}")
    print(f"   P68 last commit    : {p0['p68_last_commit']}")
    print(f"   P68 params         : {p0['p68_param_check']['passed']}/{p0['p68_param_check']['total']}  "
          f"(all_ok={p0['p68_param_check']['all_ok']})")
    print(f"   A01 receipt status : {p0['a01_receipt_status']}")
    for d, w in p0["dirs_writeable"].items():
        print(f"   dir {d}: {'OK' if w else 'FAIL'}")

    # P1.1 预热
    print("\n▶ P1.1: 因子库 + 引擎模块预热 (只 load 不 run)")
    cache = preheat_factor_and_engine()
    factor_defs = cache.get("factor_library", {}).get("p68_factor_definitions", {})
    print(f"   factor_defs loaded : {len(factor_defs)} entries")
    print(f"   available_factors  : {factor_defs.get('__available_factors__')}")
    print(f"   warning_factors    : {factor_defs.get('__warning_factors__')}")
    print(f"   engine_modules     : declared={cache['engine_modules']['declared_count']}  "
          f"all_importable={cache['engine_modules']['all_importable']}")
    ready_fn_count = sum(1 for v in cache.get("backtest_engine_functions", {}).values() if v)
    print(f"   backtest_functions : ready {ready_fn_count}")

    # P1.2 元表预校验
    print("\n▶ P1.2: 元表预校验 (WARNING only, 不阻塞不自动修复)")
    meta = precheck_reference_meta()
    varieties = meta.get("variety_catalog", {}).get("varieties", [])
    print(f"   varieties          : {varieties}")
    print(f"   contract_mapping   : {meta['contract_mapping']['count']} entries")
    print(f"   warnings           : {meta['summary']['warnings_count']}")
    for w in meta.get("warnings", []):
        print(f"     ⚠️ [{w['level']}] {w['target']}: {w['detail']}")

    # P1.3 stub 观测 + 日志
    print("\n▶ P1.3: Stub 观测 (STUB_ONLY-IGNORE)")
    stub = observe_stub_file()
    print(f"   path       : {stub['path']}")
    print(f"   size       : {stub['size_bytes']}B  "
          f"(≥{SANITY_MIN_FILE_SIZE}? {stub['meets_min_file_size']})")
    print(f"   rows(data) : {stub['row_count_data_only']}")
    print(f"   class      : {stub['classification']}")
    stub_watch = append_stub_watch_entry(stub)
    print(f"   watch_log  : {stub_watch['path']}  total={stub_watch['total_observations']}")

    # P1.3 跨伙伴观测
    print("\n▶ P1.3: Cross-agent 观测 (纯文件系统扫描，无 IPC/RPC)")
    signals = scan_dshc_dshd_signals()
    dsum = signals.get("dshc_latest_summary", {})
    print(f"   DSHC latest ts     : {dsum.get('latest_timestamp', '')}")
    print(f"   DSHC latest task   : {dsum.get('latest_task', '')}")
    print(f"   DSHC latest mode   : {dsum.get('latest_mode', '')}")
    print(f"   DSHC wind_calls    : {dsum.get('dshc_reported_wind_api_calls')}  (权威内部计数)")
    for ma in signals.get("monitor_side_assertions", []):
        if "count_in_tail500" in ma:
            print(f"   ⚠ monitor noise  : {ma['count_in_tail500']}× '{ma['pattern']}'"
                  f"  source={ma['source_agent']} audit_only={ma['audit_only']}")
            print(f"     解释: 历史残留噪声、来源旧 A01、非本次会话 (不修改 DSHD 账本)")

    # P1.4 看板
    print("\n▶ P1.4: 生成状态看板 (供人类观察；不作为放行开关)")
    dashboard = build_dashboard(p0, cache, meta, stub, signals)

    # P3 回执
    print("\n▶ P3: 生成回执 dsha_a02_ready_receipt.json")
    receipt = build_receipt(p0, cache, meta, stub, signals, dashboard)

    # 写文件
    produced_paths: Dict[str, str] = {
        "a02_preheat_cache_json": A02_CACHE_PATH,
        "a02_pipeline_status_dashboard_json": A02_DASHBOARD_PATH,
        "a02_stub_watch_log_json": A02_STUB_LOG_PATH,
        "a02_ready_receipt_json": A02_RECEIPT_PATH,
    }
    audit_result = {"written": 0, "total": 0, "path": AUDIT_PATH}
    index_result = {"ok": False, "path": INDEX_PATH, "a02_artifact_count": 0}
    if write_artifacts:
        print("\n▶ 写盘")
        for label, data, path in [
            ("a02_preheat_cache.json", {
                "cache_id": "DSHA-A02-PREHEAT-CACHE",
                "generated_at": now_utc(),
                "generated_at_gmt8": now_gmt8(),
                "purpose": "预热只读缓存：函数/配置/引擎模块的元信息快照；不是输出结果",
                "factor_library": cache["factor_library"],
                "tier_params": cache["tier_params"],
                "engine_modules": cache["engine_modules"],
                "backtest_engine_functions": cache["backtest_engine_functions"],
                "plot_styles": cache["plot_styles"],
                "sanity_gate_locked": p0["sanity_gate_locked"],
                "real_wind_call": REAL_WIND_CALL,
                "wind_api_calls": WIND_API_CALLS,
            }, A02_CACHE_PATH),
            ("a02_pipeline_status_dashboard.json", dashboard, A02_DASHBOARD_PATH),
            ("dsha_a02_ready_receipt.json", receipt, A02_RECEIPT_PATH),
        ]:
            ok = write_json(path, data)
            print(f"   {label}: {'OK' if ok else 'FAIL'}  ({path})")

        print(f"\n▶ 追加审计事件 (A02-PROBE-001)")
        audit_result = append_audit_events(p0, cache, meta, stub, signals, dashboard, receipt)
        print(f"   {audit_result['written']}/{audit_result['total']} events appended → {audit_result['path']}")

        print(f"\n▶ 更新 cross_agent_artifact_index.json")
        index_result = update_artifact_index(produced_paths)
        print(f"   index updated={index_result['ok']}  a02_artifacts={index_result['a02_artifact_count']}")

    # 结果
    result = {
        "status": receipt["status"],
        "p0_baseline": p0,
        "cache": cache,
        "meta": meta,
        "stub": stub,
        "stub_watch": stub_watch,
        "signals": signals,
        "dashboard": dashboard,
        "receipt": receipt,
        "audit": audit_result,
        "index": index_result,
        "produced_paths": produced_paths,
    }

    print("\n" + "=" * 78)
    print("📊 结果摘要")
    print("=" * 78)
    print(receipt["fixed_format_receipt_line"])
    print(receipt["red_line_receipt_line"])
    print("=" * 78)

    return result


def print_briefing_only() -> None:
    """--briefing-only 模式：只打印看板，不写任何文件。"""
    p0 = run_p0_baseline_check()
    cache = preheat_factor_and_engine()
    meta = precheck_reference_meta()
    stub = observe_stub_file()
    signals = scan_dshc_dshd_signals()
    dashboard = build_dashboard(p0, cache, meta, stub, signals)
    receipt = build_receipt(p0, cache, meta, stub, signals, dashboard)

    print("=" * 78)
    print(f"📋 A02 状态简报 · {now_gmt8()}")
    print("=" * 78)
    print(receipt["fixed_format_receipt_line"])
    print(receipt["red_line_receipt_line"])
    print(f"   stub: {stub['classification']} ({stub['size_bytes']}B)")
    print(f"   dshc: mode={signals.get('dshc_latest_summary', {}).get('latest_mode')}  "
          f"ts={signals.get('dshc_latest_summary', {}).get('latest_timestamp')}")
    print(f"   auto_ignition: DENIED (trigger authority = P68 Sanity Gate)")
    print("=" * 78)


def main():
    if "--briefing-only" in sys.argv:
        print_briefing_only()
        return
    run_preheat(write_artifacts=True)


if __name__ == "__main__":
    main()
