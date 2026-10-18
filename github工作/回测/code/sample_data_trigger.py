#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
# Force UTF-8 output for Chinese console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""
DSHA-P60 · 小样数据落地自动回调触发器
(Sample Data Trigger — Auto-Callback on CSV Landing)

═══════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不触发任何 Wind API 调用
═══════════════════════════════════════════════════════════════════
REAL_WIND_CALL: False (不可修改)
wind_api_calls: 0
gate: CLOSED/HOLD | release_permit: NOT_ISSUED

调用链路 (DSHA-P59 → P60):
  artifacts/sample_output/*.csv (新生成)
    → factor_data_loader.load_factor_data(data_path=csv_path)
    → factor_constructor.compute_factor_from_data(data)
    → backtest_skeleton.run_backtest(factor_data, price_data)
    → backtest_skeleton.save_backtest_result(result)
    → code/backtest_output/

保护机制:
  - 仅在小样采集完成后触发 (检测新 CSV 文件)
  - 无新 CSV 文件时直接返回 WAIT 状态
  - 通过 .trigger_state.json 记录已处理文件状态
  - 不修改 REAL_WIND_CALL, 不创建 marker

作者: DSHA-P60
基线: feature/v88-g1 @ c214cdf
"""

import csv
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 — 不可切换 (本轮工作)
# ════════════════════════════════════════════════════════════════

REAL_WIND_CALL = False
WIND_API_CALLS = 0

# ════════════════════════════════════════════════════════════════
# 项目路径与目录绑定
# ════════════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "artifacts", "sample_output")
BACKTEST_OUTPUT_DIR = os.path.join(CODE_DIR, "backtest_output")
TRIGGER_STATE_FILE = os.path.join(SAMPLE_OUTPUT_DIR, ".trigger_state.json")
TRIGGER_LOG_PATH = os.path.join(SAMPLE_OUTPUT_DIR, "trigger_run_log.jsonl")

# 状态常量
STATUS_WAIT = "WAIT"        # 等待新数据
STATUS_TRIGGERED = "TRIGGERED"  # 已触发
STATUS_SKIPPED = "SKIPPED"  # 跳过 (已处理过)
STATUS_ERROR = "ERROR"      # 错误
STATUS_DONE = "DONE"        # 完成

# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════


def _file_sha256(filepath: str) -> str:
    """计算文件 SHA256 哈希值。"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def _load_trigger_state() -> Dict[str, Any]:
    """
    加载触发器状态文件。

    状态文件格式:
    {
        "last_trigger_timestamp": "2026-10-18T12:04:21+00:00",
        "processed_files": {
            "ZN.SHF_close_simulated.csv": {
                "sha256": "abc123...",
                "processed_at": "2026-10-18T12:04:21+00:00",
                "status": "TRIGGERED"
            }
        }
    }

    返回:
        状态字典
    """
    if not os.path.exists(TRIGGER_STATE_FILE):
        return {
            "last_trigger_timestamp": None,
            "processed_files": {}
        }
    try:
        with open(TRIGGER_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "last_trigger_timestamp": None,
            "processed_files": {}
        }


def _save_trigger_state(state: Dict[str, Any]) -> None:
    """保存触发器状态文件。"""
    os.makedirs(os.path.dirname(TRIGGER_STATE_FILE), exist_ok=True)
    with open(TRIGGER_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _log_trigger(event_type: str, details: Dict = None) -> None:
    """
    写入触发器运行日志 (JSONL 格式)。

    参数:
        event_type: 事件类型标识
        details: 附加信息字典
    """
    os.makedirs(os.path.dirname(TRIGGER_LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "phase": "DSHA-P60",
        "wind_api_calls": WIND_API_CALLS,
        "real_wind_call": REAL_WIND_CALL,
        "details": details or {},
    }
    with open(TRIGGER_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _scan_sample_csvs() -> List[str]:
    """
    扫描 artifacts/sample_output/ 目录下的 CSV 文件。

    排除状态文件 (.trigger_state.json) 和日志文件。

    返回:
        CSV 文件完整路径列表
    """
    if not os.path.isdir(SAMPLE_OUTPUT_DIR):
        return []

    csv_files = []
    for f in glob.glob(os.path.join(SAMPLE_OUTPUT_DIR, "*.csv")):
        # 排除隐藏文件和状态文件
        basename = os.path.basename(f)
        if basename.startswith('.'):
            continue
        csv_files.append(f)

    return sorted(csv_files)


# ════════════════════════════════════════════════════════════════
# 回调触发主流程
# ════════════════════════════════════════════════════════════════


def check_new_csv_files() -> Dict[str, Any]:
    """
    检查是否有新生成的 CSV 文件。

    通过与状态文件中的 SHA256 哈希值对比来判断文件是否为新/已修改。

    返回:
        {
            "status": "NEW_FOUND" / "NO_NEW_FILES",
            "new_files": [filepath, ...],
            "modified_files": [filepath, ...],
            "unchanged_files": [filepath, ...],
            "total_csv_count": int
        }
    """
    csv_files = _scan_sample_csvs()
    state = _load_trigger_state()
    processed_files = state.get("processed_files", {})

    new_files = []
    modified_files = []
    unchanged_files = []

    for csv_path in csv_files:
        basename = os.path.basename(csv_path)
        current_hash = _file_sha256(csv_path)

        if basename in processed_files:
            prev_hash = processed_files[basename].get("sha256", "")
            if prev_hash == current_hash:
                unchanged_files.append(csv_path)
            else:
                modified_files.append(csv_path)
        else:
            new_files.append(csv_path)

    has_new = len(new_files) + len(modified_files) > 0

    result = {
        "status": "NEW_FOUND" if has_new else "NO_NEW_FILES",
        "new_files": new_files,
        "modified_files": modified_files,
        "unchanged_files": unchanged_files,
        "total_csv_count": len(csv_files),
    }

    _log_trigger("CSV_SCAN", {
        "total_csv": len(csv_files),
        "new": len(new_files),
        "modified": len(modified_files),
        "unchanged": len(unchanged_files),
        "new_files": [os.path.basename(f) for f in new_files],
        "modified_files": [os.path.basename(f) for f in modified_files],
    })

    return result


def run_pipeline_for_csv(csv_path: str) -> Dict[str, Any]:
    """
    对单个 CSV 文件执行完整的因子+回测管道。

    调用链路:
      1. factor_data_loader.load_factor_data(data_path=csv_path)
      2. factor_constructor.compute_factor_from_data(data)
      3. backtest_skeleton.run_backtest(factor_data, price_data)
      4. backtest_skeleton.save_backtest_result(result)

    参数:
        csv_path: CSV 文件完整路径

    返回:
        {
            "status": "OK" / "ERROR" / "WAIT",
            "csv_path": str,
            "factor_result": dict,
            "backtest_result": dict,
            "backtest_files": {"md": path, "json": path},
            "notes": [str, ...]
        }
    """
    result = {
        "status": STATUS_ERROR,
        "csv_path": csv_path,
        "factor_result": None,
        "backtest_result": None,
        "backtest_files": None,
        "notes": [],
        "wind_api_calls": WIND_API_CALLS,
        "real_wind_call": REAL_WIND_CALL,
    }

    notes = result["notes"]

    # ── 步骤 0: 文件存在性检查 ──
    if not os.path.exists(csv_path):
        result["status"] = STATUS_WAIT
        notes.append(f"CSV文件不存在: {csv_path}")
        _log_trigger("PIPELINE_WAIT", {"csv": csv_path, "reason": "file_not_found"})
        return result

    # ── 步骤 1: 数据加载 ──
    print(f"  📦 [P60] Step 1: 加载数据 {os.path.basename(csv_path)}...")
    try:
        from factor_data_loader import load_factor_data
        data = load_factor_data(data_path=csv_path, verbose=False)

        if data.get("status") == "WAIT" or not data.get("values"):
            result["status"] = STATUS_WAIT
            notes.append("数据加载返回 WAIT 或空数据")
            _log_trigger("PIPELINE_WAIT", {
                "csv": csv_path,
                "reason": "empty_or_wait",
                "loader_status": data.get("status"),
            })
            return result

        notes.append(f"数据加载成功: {len(data.get('values', []))} 个数据点")
        print(f"     ✅ 加载 {len(data.get('values', []))} 个数据点 "
              f"({data.get('symbol', '?')} / {data.get('indicator', '?')})")

    except Exception as e:
        result["status"] = STATUS_ERROR
        notes.append(f"数据加载异常: {e}")
        _log_trigger("PIPELINE_ERROR", {"csv": csv_path, "step": "load", "error": str(e)})
        return result

    # ── 步骤 2: 因子计算 (momentum 因子) ──
    print(f"  📊 [P60] Step 2: 计算因子...")
    try:
        from factor_constructor import compute_factor_from_data
        factor_result = compute_factor_from_data(data, factor_type="momentum")

        if factor_result.get("status") == "NO_DATA":
            result["status"] = STATUS_WAIT
            notes.append("因子计算返回 NO_DATA (数据点不足)")
            _log_trigger("PIPELINE_WAIT", {
                "csv": csv_path,
                "reason": "factor_no_data",
            })
            return result

        result["factor_result"] = {
            "factor_type": factor_result.get("factor_type"),
            "factor_length": len(factor_result.get("factor_values", [])),
            "param_validation": factor_result.get("param_validation", {}).get("overall_passed"),
        }
        notes.append(f"因子计算成功: {factor_result.get('factor_type', '?')} "
                     f"({len(factor_result.get('factor_values', []))} 个值)")
        print(f"     ✅ {factor_result.get('factor_type', '?')} 因子 "
              f"({len(factor_result.get('factor_values', []))} 个值)")

    except Exception as e:
        result["status"] = STATUS_ERROR
        notes.append(f"因子计算异常: {e}")
        _log_trigger("PIPELINE_ERROR", {"csv": csv_path, "step": "factor", "error": str(e)})
        return result

    # ── 步骤 3: 回测计算 ──
    print(f"  📈 [P60] Step 3: 执行回测...")
    try:
        from backtest_skeleton import run_backtest, save_backtest_result

        # 构建 factor_data 和 price_data
        factor_data = {
            "factor_type": factor_result.get("factor_type", "momentum"),
            "factor_values": factor_result.get("factor_values", []),
            "factor_dates": factor_result.get("factor_dates", []),
        }
        price_data = data  # factor_data_loader 输出即为价格数据

        backtest_result = run_backtest(factor_data, price_data)

        if backtest_result.get("status") == "WAIT":
            result["status"] = STATUS_WAIT
            notes.append("回测返回 WAIT (输入不足)")
            _log_trigger("PIPELINE_WAIT", {
                "csv": csv_path,
                "reason": "backtest_wait",
                "backtest_status": backtest_result.get("status"),
            })
            return result

        if backtest_result.get("status") == "ERROR":
            result["status"] = STATUS_ERROR
            notes.append(f"回测错误: {backtest_result.get('error', 'unknown')}")
            _log_trigger("PIPELINE_ERROR", {
                "csv": csv_path,
                "step": "backtest",
                "error": backtest_result.get("error", "unknown"),
            })
            return result

        result["backtest_result"] = {
            "status": backtest_result.get("status"),
            "summary": backtest_result.get("summary", {}),
        }
        notes.append(f"回测完成: 累计收益={backtest_result.get('summary', {}).get('cumulative_return', 'N/A'):.4f}")

    except Exception as e:
        result["status"] = STATUS_ERROR
        notes.append(f"回测异常: {e}")
        _log_trigger("PIPELINE_ERROR", {"csv": csv_path, "step": "backtest_run", "error": str(e)})
        return result

    # ── 步骤 4: 保存回测结果 ──
    print(f"  💾 [P60] Step 4: 保存回测结果...")
    try:
        from backtest_skeleton import save_backtest_result
        backtest_files = save_backtest_result(backtest_result)
        result["backtest_files"] = backtest_files
        result["status"] = STATUS_TRIGGERED
        notes.append(f"结果已保存: MD={os.path.basename(backtest_files.get('md', '?'))}, "
                     f"JSON={os.path.basename(backtest_files.get('json', '?'))}")
        print(f"     ✅ 回测结果已保存")

    except Exception as e:
        result["status"] = STATUS_ERROR
        notes.append(f"结果保存异常: {e}")
        _log_trigger("PIPELINE_ERROR", {"csv": csv_path, "step": "save", "error": str(e)})
        return result

    _log_trigger("PIPELINE_COMPLETE", {
        "csv": csv_path,
        "status": "TRIGGERED",
        "factor_type": result["factor_result"]["factor_type"],
        "factor_length": result["factor_result"]["factor_length"],
        "backtest_md": backtest_files.get("md"),
        "backtest_json": backtest_files.get("json"),
    })

    return result


def trigger_on_sample_landing() -> Dict[str, Any]:
    """
    主入口: 检查小样数据落地并触发回测管道。

    流程:
      1. 扫描 artifacts/sample_output/*.csv
      2. 对比状态文件检测新/修改文件
      3. 无新文件 → 返回 WAIT
      4. 有新文件 → 逐个执行回测管道
      5. 更新状态文件

    返回:
        {
            "status": "WAIT" / "TRIGGERED" / "SKIPPED" / "ERROR",
            "new_files_triggered": [filepath, ...],
            "files_skipped": [filepath, ...],
            "total_new": int,
            "total_skipped": int,
            "details": [dict, ...]
        }
    """
    print("=" * 70)
    print("DSHA-P60 · 小样数据落地自动回调触发器")
    print("=" * 70)
    print(f"📂 扫描目录: {SAMPLE_OUTPUT_DIR}")
    print(f"🔒 REAL_WIND_CALL={REAL_WIND_CALL} | wind_api_calls={WIND_API_CALLS}")
    print()

    # ── 步骤 1: 扫描并检测新文件 ──
    scan_result = check_new_csv_files()

    if scan_result["status"] == "NO_NEW_FILES":
        print(f"  ⏳ [P60] 未发现新的CSV文件，返回 WAIT")
        print(f"     当前CSV数量: {scan_result['total_csv_count']}")
        print(f"     未变化文件: {len(scan_result['unchanged_files'])}")
        print()
        print("=" * 70)
        print("状态: WAIT — 等待小样采集完成后 CSV 落地")
        print("=" * 70)

        return {
            "status": STATUS_WAIT,
            "new_files_triggered": [],
            "files_skipped": [],
            "total_new": 0,
            "total_skipped": 0,
            "details": [],
            "scan": scan_result,
        }

    # ── 步骤 2: 执行回测管道 ──
    files_to_process = scan_result["new_files"] + scan_result["modified_files"]
    details = []
    triggered = []
    state = _load_trigger_state()

    print(f"  🔄 [P60] 检测到 {len(files_to_process)} 个新/修改的CSV文件，开始触发回测管道...")
    print("-" * 50)

    for csv_path in files_to_process:
        basename = os.path.basename(csv_path)
        print(f"\n  📁 处理: {basename}")

        pipeline_result = run_pipeline_for_csv(csv_path)
        details.append({
            "csv": csv_path,
            "status": pipeline_result["status"],
            "notes": pipeline_result["notes"],
        })

        if pipeline_result["status"] == STATUS_TRIGGERED:
            triggered.append(csv_path)
            # 更新状态文件
            current_hash = _file_sha256(csv_path)
            state["processed_files"][basename] = {
                "sha256": current_hash,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "status": "TRIGGERED",
            }
        else:
            # 非 TRIGGERED 状态也记录，避免重复触发
            if csv_path in [f for f in files_to_process if f not in triggered]:
                state["processed_files"][basename] = {
                    "sha256": _file_sha256(csv_path),
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "status": pipeline_result["status"],
                }

    # ── 步骤 3: 保存状态 ──
    state["last_trigger_timestamp"] = datetime.now(timezone.utc).isoformat()
    _save_trigger_state(state)

    # ── 步骤 4: 输出摘要 ──
    final_status = STATUS_TRIGGERED if triggered else STATUS_SKIPPED

    print()
    print("=" * 70)
    print(f"📊 触发结果摘要")
    print("=" * 70)
    print(f"  总CSV文件:          {scan_result['total_csv_count']}")
    print(f"  新/修改文件:        {len(files_to_process)}")
    print(f"  成功触发回测:       {len(triggered)}")
    print(f"  跳过 (已处理):      {scan_result['total_csv_count'] - len(files_to_process)}")
    print(f"  回测输出目录:       {BACKTEST_OUTPUT_DIR}")
    print()

    if triggered:
        print(f"  ✅ 成功触发的文件:")
        for f in triggered:
            print(f"     - {os.path.basename(f)}")
        print()

    if details:
        print(f"  📋 详情:")
        for d in details:
            status_icon = "✅" if d["status"] == STATUS_TRIGGERED else "⚠️"
            print(f"     {status_icon} {os.path.basename(d['csv'])}: {d['status']}")
            for note in d.get("notes", []):
                print(f"        • {note}")
        print()

    print("=" * 70)
    print(f"状态: {final_status}")
    print("=" * 70)

    return {
        "status": final_status,
        "new_files_triggered": triggered,
        "files_skipped": scan_result["unchanged_files"],
        "total_new": len(files_to_process),
        "total_skipped": len(scan_result["unchanged_files"]),
        "details": details,
        "scan": scan_result,
    }


# ════════════════════════════════════════════════════════════════
# 模块导入支持 — 供其他脚本直接调用
# ════════════════════════════════════════════════════════════════

def trigger_callback(data_path: Optional[str] = None) -> Dict[str, Any]:
    """
    轻量回调接口 — 供外部直接调用。

    参数:
        data_path: 可选的 CSV 文件路径
                   None 时自动扫描 artifacts/sample_output/

    返回:
        触发结果字典
    """
    if data_path:
        # 直接指定路径 — 执行单文件管道
        if not os.path.exists(data_path):
            return {
                "status": STATUS_WAIT,
                "reason": f"文件不存在: {data_path}",
                "wind_api_calls": WIND_API_CALLS,
                "real_wind_call": REAL_WIND_CALL,
            }
        return run_pipeline_for_csv(data_path)
    else:
        # 自动扫描 — 执行完整触发流程
        return trigger_on_sample_landing()


# ════════════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    result = trigger_on_sample_landing()
    sys.exit(0)
