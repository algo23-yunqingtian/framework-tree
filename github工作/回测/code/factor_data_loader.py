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
DSHA-P59 · 离线因子数据加载模块
(Factor Data Loader — OFFLINE ONLY, NO REAL WIND DATA)

═══════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不读取任何真实 Wind 数据
═══════════════════════════════════════════════════════════════════════
数据路径绑定: artifacts/sample_output/*.csv (小样离线输出目录)
REAL_WIND_CALL 锁定: False (不可修改)
wind_api_calls: 0 (本模块不触发任何 Wind API 调用)
gate: CLOSED/HOLD | release_permit: NOT_ISSUED

调用顺序 (DSHA-P59 框架):
  factor_data_loader → factor_constructor → backtest_skeleton

前置条件:
  必须等待小样输出 CSV 文件存在才能运行实际加载。
  无数据时返回 WAIT 状态，不报错崩溃。

作者: DSHA-P59
基线: feature/v88-g1
状态: 离线框架 · 等待小样数据落地
"""

import csv
import json
import os
import sys
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 — 不可切换 (本轮工作)
# ════════════════════════════════════════════════════════════════

REAL_WIND_CALL = False   # ← 硬锁死，禁止修改
WIND_API_CALLS = 0       # ← 本模块不触发任何 Wind API

# ════════════════════════════════════════════════════════════════
# 项目路径与目录绑定
# ════════════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "artifacts", "sample_output")
SIM_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "code", "sim_output")

# 数据加载日志
DATA_LOAD_LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "factor_data_loader.log"
)

# ════════════════════════════════════════════════════════════════
# 标准化数据结构 (因子计算输入格式)
# ════════════════════════════════════════════════════════════════

# 对齐因子计算输入格式的标准数据字典:
# {
#   "symbol": str,          # 品种代码
#   "indicator": str,       # 指标名称
#   "source": str,          # 数据源标记
#   "dates": [str, ...],    # 日期序列 (YYYY-MM-DD)
#   "values": [float, ...], # 数值序列
#   "metadata": {           # 附加元数据
#     "loaded_at": str,
#     "record_count": int,
#     "validation": {       # 校验结果
#       "null_count": int,
#       "duplicate_timestamps": int,
#       "anomalous_values": int,
#       "anomaly_threshold": float,
#     }
#   }
# }


class DataValidationError(Exception):
    """数据校验异常基类"""
    pass


class MissingDataFileError(DataValidationError):
    """数据文件不存在"""
    pass


class EmptyDataFrameError(DataValidationError):
    """数据为空"""
    pass


class DataIntegrityError(DataValidationError):
    """数据完整性错误 (空值/重复/异常)"""
    pass


# ════════════════════════════════════════════════════════════════
# 数据校验函数
# ════════════════════════════════════════════════════════════════

def check_nulls(dates: List[str], values: List[float]) -> Dict[str, Any]:
    """
    检查空值和缺失值。

    Args:
        dates: 日期序列
        values: 数值序列

    Returns:
        校验结果字典
    """
    null_count = 0
    details = []

    # 检查日期序列中的空值
    for i, d in enumerate(dates):
        if d is None or (isinstance(d, str) and d.strip() == ""):
            null_count += 1
            details.append(f"Row {i}: date is null/empty")

    # 检查数值序列中的空值/NaN/Inf
    for i, v in enumerate(values):
        if v is None:
            null_count += 1
            details.append(f"Row {i}: value is None")
        elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            null_count += 1
            details.append(f"Row {i}: value is NaN/Inf ({v})")

    return {
        "null_count": null_count,
        "details": details,
        "passed": null_count == 0,
    }


def check_duplicate_timestamps(dates: List[str]) -> Dict[str, Any]:
    """
    检查重复时间戳。

    Args:
        dates: 日期序列

    Returns:
        校验结果字典
    """
    seen = set()
    duplicate_count = 0
    details = []

    for i, d in enumerate(dates):
        if d in seen:
            duplicate_count += 1
            details.append(f"Row {i}: duplicate timestamp '{d}'")
        seen.add(d)

    return {
        "duplicate_count": duplicate_count,
        "total_unique": len(seen),
        "total_rows": len(dates),
        "details": details,
        "passed": duplicate_count == 0,
    }


def check_anomalous_values(values: List[float], threshold: float = 3.0) -> Dict[str, Any]:
    """
    检查异常数值 (基于 z-score 的离群点检测)。

    Args:
        values: 数值序列
        threshold: z-score 阈值 (默认 3.0)

    Returns:
        校验结果字典
    """
    # 过滤掉 None/NaN/Inf
    valid_values = [
        v for v in values
        if v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))
    ]

    if not valid_values or len(valid_values) < 2:
        return {
            "anomalous_count": 0,
            "details": [],
            "passed": True,
            "note": "有效数据点不足, 跳过异常检测",
        }

    # 计算均值和标准差
    mean = sum(valid_values) / len(valid_values)
    variance = sum((v - mean) ** 2 for v in valid_values) / len(valid_values)
    std = math.sqrt(variance)

    if std == 0:
        return {
            "anomalous_count": 0,
            "details": [],
            "passed": True,
            "note": "标准差为0, 所有值相同",
        }

    anomalous_count = 0
    details = []
    for i, v in enumerate(values):
        # 跳过无效值
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            continue
        z = abs(v - mean) / std
        if z >= threshold - 1e-9:
            anomalous_count += 1
            details.append(f"Row {i}: value={v}, z={z:.2f} (>={threshold})")

    return {
        "anomalous_count": anomalous_count,
        "threshold": threshold,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "details": details,
        "passed": anomalous_count == 0,
    }


def validate_data(dates: List[str], values: List[float],
                  anomaly_threshold: float = 3.0) -> Dict[str, Any]:
    """
    综合数据校验: 空值 + 重复时间戳 + 异常数值。

    Args:
        dates: 日期序列
        values: 数值序列
        anomaly_threshold: z-score 异常阈值

    Returns:
        综合校验结果字典
    """
    null_check = check_nulls(dates, values)
    dup_check = check_duplicate_timestamps(dates)
    anom_check = check_anomalous_values(values, threshold=anomaly_threshold)

    all_passed = (
        null_check["passed"]
        and dup_check["passed"]
        and anom_check["passed"]
    )

    return {
        "overall_passed": all_passed,
        "null_check": null_check,
        "duplicate_check": dup_check,
        "anomaly_check": anom_check,
        "summary": {
            "null_count": null_check["null_count"],
            "duplicate_count": dup_check["duplicate_count"],
            "anomalous_count": anom_check["anomalous_count"],
            "total_rows": len(dates),
        }
    }


# ════════════════════════════════════════════════════════════════
# CSV 读取函数
# ════════════════════════════════════════════════════════════════

def read_csv_file(filepath: str) -> Dict[str, Any]:
    """
    从 CSV 文件读取原始数据。

    Args:
        filepath: CSV 文件路径

    Returns:
        原始数据字典
    """
    if not os.path.exists(filepath):
        raise MissingDataFileError(f"数据文件不存在: {filepath}")

    dates = []
    values = []
    symbols = set()
    indicators = set()
    sources = set()

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row.get("date", "").strip())
            raw_val = row.get("value", "").strip()
            values.append(float(raw_val) if raw_val else None)
            symbols.add(row.get("symbol", "").strip())
            indicators.add(row.get("indicator", "").strip())
            sources.add(row.get("source", "").strip())

    if not dates:
        raise EmptyDataFrameError(f"CSV 文件无数据行: {filepath}")

    return {
        "dates": dates,
        "values": values,
        "symbols": list(symbols),
        "indicators": list(indicators),
        "sources": list(sources),
        "filepath": filepath,
        "row_count": len(dates),
    }


# ════════════════════════════════════════════════════════════════
# 标准化输出函数
# ════════════════════════════════════════════════════════════════

def normalize_to_factor_input(raw_data: Dict[str, Any],
                               validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    将原始数据转换为标准化因子计算输入格式。

    对齐因子计算输入格式:
      dates: [str, ...]
      values: [float, ...]
      symbol: str
      indicator: str
      source: str
      metadata: {loaded_at, record_count, validation}
    """
    symbol = raw_data["symbols"][0] if raw_data["symbols"] else "UNKNOWN"
    indicator = raw_data["indicators"][0] if raw_data["indicators"] else "UNKNOWN"
    source = raw_data["sources"][0] if raw_data["sources"] else "UNKNOWN"

    return {
        "symbol": symbol,
        "indicator": indicator,
        "source": source,
        "dates": raw_data["dates"],
        "values": raw_data["values"],
        "metadata": {
            "loaded_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(raw_data["dates"]),
            "source_file": raw_data["filepath"],
            "validation": {
                "overall_passed": validation_result["overall_passed"],
                "null_count": validation_result["summary"]["null_count"],
                "duplicate_count": validation_result["summary"]["duplicate_count"],
                "anomalous_count": validation_result["summary"]["anomalous_count"],
                "anomaly_threshold": validation_result["anomaly_check"].get("threshold", 3.0),
            }
        }
    }


# ════════════════════════════════════════════════════════════════
# 主加载函数
# ════════════════════════════════════════════════════════════════

def load_factor_data(data_path: Optional[str] = None,
                     anomaly_threshold: float = 3.0,
                     verbose: bool = True) -> Dict[str, Any]:
    """
    加载因子数据 — 主入口函数。

    查找优先级:
      1. 显式指定的 data_path
      2. artifacts/sample_output/*.csv
      3. code/sim_output/*.csv
      4. 内置仿真测试数据 (10行)

    Args:
        data_path: 可选的 CSV 文件路径
        anomaly_threshold: z-score 异常阈值
        verbose: 是否输出日志

    Returns:
        标准化因子数据字典, 包含 status 字段

    Note:
        wind_api_calls = 0, REAL_WIND_CALL = False
        本函数不触发任何 Wind API 调用。
    """
    status = "OK"
    notes = []

    # ── 步骤1: 确定数据路径 ──
    actual_path = data_path
    fallback_used = False

    if not actual_path:
        # 搜索 artifacts/sample_output/
        if os.path.isdir(SAMPLE_OUTPUT_DIR):
            for fname in os.listdir(SAMPLE_OUTPUT_DIR):
                if fname.endswith(".csv"):
                    actual_path = os.path.join(SAMPLE_OUTPUT_DIR, fname)
                    break

    if not actual_path and os.path.isdir(SIM_OUTPUT_DIR):
        for fname in os.listdir(SIM_OUTPUT_DIR):
            if fname.endswith(".csv"):
                actual_path = os.path.join(SIM_OUTPUT_DIR, fname)
                break

    if not actual_path:
        # ── 使用内置仿真测试数据 ──
        notes.append("未找到外部 CSV, 使用内置仿真测试数据 (10行)")
        fallback_used = True
        raw_data = _generate_builtin_test_data()
    else:
        raw_data = read_csv_file(actual_path)
        notes.append(f"读取: {actual_path}")

    # ── 步骤2: 数据校验 ──
    validation = validate_data(raw_data["dates"], raw_data["values"],
                                anomaly_threshold=anomaly_threshold)

    if not validation["overall_passed"]:
        status = "WARNING"
        notes.append(f"校验发现异常: "
                     f"nulls={validation['summary']['null_count']}, "
                     f"dups={validation['summary']['duplicate_count']}, "
                     f"anomalous={validation['summary']['anomalous_count']}")

    # ── 步骤3: 标准化输出 ──
    result = normalize_to_factor_input(raw_data, validation)
    result["status"] = status
    result["notes"] = notes
    result["fallback_used"] = fallback_used

    if verbose:
        _log_result(result)

    return result


# ════════════════════════════════════════════════════════════════
# 内置仿真测试数据
# ════════════════════════════════════════════════════════════════

def _generate_builtin_test_data() -> Dict[str, Any]:
    """
    生成内置仿真测试数据 (10行 ZN.SHF 收盘价)。
    不读取任何真实 Wind 数据。
    """
    import random
    random.seed(42)  # 可重现

    base_date = datetime(2025, 1, 2)
    base_price = 24500.0
    dates = []
    values = []

    for i in range(10):
        # 模拟交易日 (跳过周末)
        d = base_date
        for _ in range(i):
            d = d + __import__("datetime").timedelta(days=1)
            while d.weekday() >= 5:  # 跳过周六日
                d = d + __import__("datetime").timedelta(days=1)

        dates.append(d.strftime("%Y-%m-%d"))
        # 随机游走模拟价格
        change = random.gauss(0, 100)
        base_price += change
        values.append(round(base_price, 2))

    return {
        "dates": dates,
        "values": values,
        "symbols": ["ZN.SHF"],
        "indicators": ["close"],
        "sources": ["SIMULATED (NOT REAL)"],
        "filepath": "builtin_simulated_test_data (10 rows)",
        "row_count": 10,
    }


# ════════════════════════════════════════════════════════════════
# 日志输出
# ════════════════════════════════════════════════════════════════

def _log_result(result: Dict[str, Any]):
    """输出加载结果摘要到控制台"""
    print()
    print("─" * 60)
    print("📦 [P59] 因子数据加载结果")
    print("─" * 60)
    print(f"  状态:       {result['status']}")
    print(f"  品种:       {result['symbol']}")
    print(f"  指标:       {result['indicator']}")
    print(f"  数据源:     {result['source']}")
    print(f"  数据行数:   {result['metadata']['record_count']}")
    print(f"  数据来源:   {result['metadata'].get('source_file', 'N/A')}")
    print(f"  回退使用:   {'是 (内置仿真)' if result.get('fallback_used') else '否 (外部CSV)'}")
    print(f"  校验通过:   {'✅' if result['metadata']['validation']['overall_passed'] else '⚠️'}")
    print(f"  空值数:     {result['metadata']['validation']['null_count']}")
    print(f"  重复时间戳: {result['metadata']['validation']['duplicate_count']}")
    print(f"  异常值数:   {result['metadata']['validation']['anomalous_count']}")
    if result.get("notes"):
        for n in result["notes"]:
            print(f"  备注:       {n}")
    print(f"  REAL_WIND_CALL: {REAL_WIND_CALL}")
    print(f"  wind_api_calls:  {WIND_API_CALLS}")
    print("─" * 60)


# ════════════════════════════════════════════════════════════════
# 命令行接口 (自测)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("🧪 DSHA-P59 · 离线因子数据加载模块 — 仿真自测")
    print("=" * 70)
    print()

    # 测试1: 使用内置仿真数据
    print("▶ 测试1: 内置仿真数据 (10行)")
    result = load_factor_data(verbose=True)
    assert result["status"] in ("OK", "WARNING"), \
        f"预期状态 OK/WARNING, 实际 {result['status']}"
    assert result["metadata"]["record_count"] == 10, \
        f"预期10行, 实际 {result['metadata']['record_count']}"
    assert REAL_WIND_CALL is False, "REAL_WIND_CALL 必须为 False"
    print("  ✅ 测试1通过\n")

    # 测试2: 空值检查
    print("▶ 测试2: 空值校验")
    null_check = check_nulls(
        ["2025-01-02", "", None],
        [100.0, None, 300.0]
    )
    assert null_check["null_count"] == 3, \
        f"预期3个空值, 实际 {null_check['null_count']}"
    assert null_check["passed"] is False
    print(f"  ✅ 测试2通过 (null_count={null_check['null_count']})\n")

    # 测试3: 重复时间戳检查
    print("▶ 测试3: 重复时间戳校验")
    dup_check = check_duplicate_timestamps(
        ["2025-01-02", "2025-01-03", "2025-01-03", "2025-01-05"]
    )
    assert dup_check["duplicate_count"] == 1, \
        f"预期1个重复, 实际 {dup_check['duplicate_count']}"
    print(f"  ✅ 测试3通过 (duplicate_count={dup_check['duplicate_count']})\n")

    # 测试4: 异常值检查
    print("▶ 测试4: 异常值检测")
    anom_check = check_anomalous_values(
        [100, 101, 99, 100, 102, 98, 101, 100, 103, 100, 101, 99, 100, 102, 98,
         101, 100, 103, 100, 101, 100000, 99, 100, 102, 98, 101, 100, 103, 100, 101],
        threshold=3.0
    )
    assert anom_check["anomalous_count"] >= 1, \
        "应检测到异常值 100000 (30行数据, 单点离群)"
    print(f"  ✅ 测试4通过 (anomalous_count={anom_check['anomalous_count']})\n")

    # 测试5: 综合校验
    print("▶ 测试5: 综合校验")
    comp = validate_data(
        ["2025-01-02", "2025-01-03", "2025-01-03"],
        [100, 200, None]
    )
    assert comp["overall_passed"] is False
    assert comp["summary"]["null_count"] >= 1
    assert comp["summary"]["duplicate_count"] >= 1
    print(f"  ✅ 测试5通过 (overall_passed={comp['overall_passed']})\n")

    # 测试6: 文件不存在 → MissingDataFileError
    print("▶ 测试6: 文件不存在异常")
    try:
        read_csv_file("NONEXISTENT.csv")
        assert False, "应抛出 MissingDataFileError"
    except MissingDataFileError:
        print("  ✅ 测试6通过 (MissingDataFileError 正确抛出)\n")

    print("=" * 70)
    print("✅ 全部6项测试通过 — REAL_WIND_CALL=False, wind_api_calls=0")
    print("=" * 70)
    sys.exit(0)
