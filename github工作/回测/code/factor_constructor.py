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
DSHA-P59 · 基础因子构造模块
(Factor Constructor — OFFLINE ONLY, NO REAL WIND DATA)

═══════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不读取任何真实 Wind 数据
═══════════════════════════════════════════════════════════════════════
REAL_WIND_CALL: False (不可修改)
wind_api_calls: 0 (本模块不触发任何 Wind API 调用)
gate: CLOSED/HOLD | release_permit: NOT_ISSUED

数据流:
  factor_data_loader.load_factor_data() → 本模块 → backtest_skeleton

参数基线校验:
  复用 F007 参数基线文档定义:
    - window_days = 60 (基准锚点, 35~100 验证范围)
    - f19_weight / f20_weight / cf003_weight: frozen
    - decay_factor: frozen

输出目录:
  code/factor_offline_result/

作者: DSHA-P59
基线: feature/v88-g1
"""

import json
import os
import sys
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 — 不可切换 (本轮工作)
# ════════════════════════════════════════════════════════════════

REAL_WIND_CALL = False
WIND_API_CALLS = 0

# ════════════════════════════════════════════════════════════════
# 项目路径
# ════════════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTOR_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "factor_offline_result"
)

# ════════════════════════════════════════════════════════════════
# F007 参数基线定义 (复用 F007_PARAMETER_BASELINE.md)
# ════════════════════════════════════════════════════════════════

F007_PARAMETER_BASELINE = {
    "window_days": {
        "value": 60,
        "unit": "days",
        "definition": "合成因子计算的标准滚动窗口",
        "is_baseline": True,
        "verification_range": [35, 60, 80, 100],
    },
    "weights": {
        "f19_weight": {"value": "frozen", "mutable": False},
        "f20_weight": {"value": "frozen", "mutable": False},
        "cf003_weight": {"value": "frozen", "mutable": False},
    },
    "decay_factor": {
        "value": "frozen",
        "mutable": False,
    },
    "drift_thresholds": {
        "ranking_correlation": {
            "warning": 0.80,
            "critical": 0.60,
            "metric": "spearman_rho",
        },
        "direction_consistency": {
            "warning": 0.20,
            "critical": 0.40,
            "metric": "disagreement_ratio",
        },
        "ic_volatility": {
            "warning": "2x_baseline_std",
            "critical": "3x_baseline_std",
        },
    },
}

# ════════════════════════════════════════════════════════════════
# 参数基线校验函数
# ════════════════════════════════════════════════════════════════

def validate_parameter_baseline(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    校验因子计算参数是否符合 F007 基线定义。

    Args:
        params: 待校验的参数字典

    Returns:
        校验结果字典
    """
    errors = []
    warnings = []
    passed_checks = 0
    total_checks = 0

    # 1. window_days 校验
    total_checks += 1
    if "window_days" not in params:
        errors.append("缺少参数: window_days")
    else:
        wd = params["window_days"]
        baseline_wd = F007_PARAMETER_BASELINE["window_days"]["value"]
        if wd == baseline_wd:
            passed_checks += 1
        elif wd in F007_PARAMETER_BASELINE["window_days"]["verification_range"]:
            warnings.append(
                f"window_days={wd} 在验证范围内 (非基准值 {baseline_wd})"
            )
        else:
            errors.append(
                f"window_days={wd} 超出有效范围 "
                f"{F007_PARAMETER_BASELINE['window_days']['verification_range']}"
            )

    # 2. 权重冻结校验
    total_checks += 1
    weights = params.get("weights", {})
    frozen = True
    for wname in ["f19_weight", "f20_weight", "cf003_weight"]:
        wval = weights.get(wname, None)
        if wval != "frozen" and wval is not None:
            frozen = False
            warnings.append(f"{wname}={wval} 应为 frozen")
    if frozen:
        passed_checks += 1
    else:
        warnings.append("部分权重未冻结, 可能需要复核")

    # 3. decay_factor 冻结校验
    total_checks += 1
    df = params.get("decay_factor", None)
    if df == "frozen" or df is None:
        passed_checks += 1
    else:
        warnings.append(f"decay_factor={df} 应为 frozen")

    return {
        "overall_passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
    }


def get_default_params() -> Dict[str, Any]:
    """
    返回 F007 基准参数集 (离线默认值)。
    """
    return {
        "window_days": F007_PARAMETER_BASELINE["window_days"]["value"],
        "weights": {
            "f19_weight": "frozen",
            "f20_weight": "frozen",
            "cf003_weight": "frozen",
        },
        "decay_factor": "frozen",
        "factor_id": "FACTOR-007",
        "factor_name": "F007 合成因子",
    }


# ════════════════════════════════════════════════════════════════
# 基础因子计算接口
# ════════════════════════════════════════════════════════════════

def compute_momentum_factor(
    prices: List[float],
    window: int = 60,
) -> List[float]:
    """
    动量因子 (Momentum): N日收益率。

    Args:
        prices: 价格序列
        window: 滚动窗口

    Returns:
        动量因子序列 (长度 = len(prices) - window)
    """
    if len(prices) < window + 1:
        return []

    factors = []
    for i in range(window, len(prices)):
        ret = (prices[i] - prices[i - window]) / prices[i - window]
        factors.append(round(ret, 8))

    return factors


def compute_volatility_factor(
    prices: List[float],
    window: int = 20,
) -> List[float]:
    """
    波动率因子: N日收益率标准差。

    Args:
        prices: 价格序列
        window: 滚动窗口

    Returns:
        波动率因子序列
    """
    if len(prices) < window + 1:
        return []

    factors = []
    for i in range(window, len(prices)):
        window_returns = []
        for j in range(i - window + 1, i + 1):
            if j > 0:
                r = (prices[j] - prices[j - 1]) / prices[j - 1]
                window_returns.append(r)
        if window_returns:
            mean_r = sum(window_returns) / len(window_returns)
            var = sum((r - mean_r) ** 2 for r in window_returns) / len(window_returns)
            factors.append(round(math.sqrt(var), 8))
        else:
            factors.append(0.0)

    return factors


def compute_mean_reversion_factor(
    prices: List[float],
    window: int = 60,
) -> List[float]:
    """
    均值回归因子: 当前价格与N日均值的偏离度 (Z-score)。

    Args:
        prices: 价格序列
        window: 滚动窗口

    Returns:
        均值回归因子序列
    """
    if len(prices) < window:
        return []

    factors = []
    for i in range(window - 1, len(prices)):
        slice_ = prices[i - window + 1: i + 1]
        mean = sum(slice_) / len(slice_)
        var = sum((v - mean) ** 2 for v in slice_) / len(slice_)
        std = math.sqrt(var)
        if std > 0:
            z = (prices[i] - mean) / std
            factors.append(round(z, 8))
        else:
            factors.append(0.0)

    return factors


def compute_factor_from_data(
    data: Dict[str, Any],
    factor_type: str = "momentum",
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    从标准化数据计算因子 — 主接口。

    预留接入 ZN.SHF 收盘价序列入口:
      data = factor_data_loader.load_factor_data()

    Args:
        data: factor_data_loader 输出的标准化数据字典
        factor_type: 因子类型 (momentum / volatility / mean_reversion)
        params: 可选参数覆盖

    Returns:
        因子计算结果字典
    """
    if params is None:
        params = get_default_params()

    # 参数基线校验
    param_validation = validate_parameter_baseline(params)

    # 提取价格序列
    prices = data.get("values", [])
    dates = data.get("dates", [])
    symbol = data.get("symbol", "UNKNOWN")
    indicator = data.get("indicator", "UNKNOWN")

    window = params.get("window_days", 60)

    # 根据 factor_type 选择计算函数
    if factor_type == "momentum":
        factor_values = compute_momentum_factor(prices, window=window)
    elif factor_type == "volatility":
        factor_values = compute_volatility_factor(prices, window=min(window, 20))
    elif factor_type == "mean_reversion":
        factor_values = compute_mean_reversion_factor(prices, window=window)
    else:
        raise ValueError(f"不支持的因子类型: {factor_type}")

    # 因子序列长度: 数据长度 - window (对于动量因子)
    factor_count = len(factor_values)
    date_offset = len(prices) - factor_count  # 前 N 个日期无因子值

    # 对齐因子日期
    factor_dates = dates[date_offset:] if factor_count > 0 else []

    # 构建结果
    result = {
        "factor_type": factor_type,
        "factor_id": params.get("factor_id", "FACTOR-007"),
        "factor_name": params.get("factor_name", "F007 合成因子"),
        "symbol": symbol,
        "indicator": indicator,
        "window_days": window,
        "factor_count": factor_count,
        "factor_dates": factor_dates,
        "factor_values": factor_values,
        "params": params,
        "param_validation": param_validation,
        "data_source": data.get("source", "UNKNOWN"),
        "data_status": data.get("status", "UNKNOWN"),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "real_wind_call": REAL_WIND_CALL,
        "wind_api_calls": WIND_API_CALLS,
        "notes": [],
    }

    # 如果因子值为空, 添加提示
    if factor_count == 0:
        result["status"] = "NO_DATA"
        result["notes"].append(
            f"数据量不足 (需要 > {window} 行), 仅 {len(prices)} 行可用"
        )
    else:
        result["status"] = "OK"

    return result


# ════════════════════════════════════════════════════════════════
# 因子结果保存
# ════════════════════════════════════════════════════════════════

def save_factor_result(result: Dict[str, Any],
                       output_dir: Optional[str] = None) -> str:
    """
    保存因子计算结果到离线结果目录。

    Args:
        result: compute_factor_from_data 输出的结果字典
        output_dir: 输出目录 (默认 code/factor_offline_result/)

    Returns:
        输出文件路径
    """
    if output_dir is None:
        output_dir = FACTOR_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    factor_type = result.get("factor_type", "unknown")
    symbol = result.get("symbol", "UNKNOWN")
    window = result.get("window_days", 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{factor_type}_{symbol}_w{window}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # 写入 JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return filepath


# ════════════════════════════════════════════════════════════════
# 日志输出
# ════════════════════════════════════════════════════════════════

def _print_factor_summary(result: Dict[str, Any]):
    """打印因子计算结果摘要"""
    print()
    print("─" * 60)
    print("📊 [P59] 因子计算结果")
    print("─" * 60)
    print(f"  状态:         {result['status']}")
    print(f"  因子类型:     {result['factor_type']}")
    print(f"  因子ID:       {result['factor_id']}")
    print(f"  品种:         {result['symbol']}")
    print(f"  窗口:         {result['window_days']}日")
    print(f"  因子点数量:   {result['factor_count']}")
    if result["factor_count"] > 0:
        fv = result["factor_values"]
        print(f"  因子范围:     {min(fv):.6f} ~ {max(fv):.6f}")
        print(f"  因子均值:     {sum(fv)/len(fv):.6f}")
        print(f"  因子首日:     {result['factor_dates'][0]}")
        print(f"  因子末日:     {result['factor_dates'][-1]}")
    print(f"  数据源:       {result['data_source']}")
    print(f"  参数校验:     {'✅ 通过' if result['param_validation']['overall_passed'] else '⚠️ 有警告'}")
    for w in result["param_validation"]["warnings"]:
        print(f"    ⚠️ {w}")
    if result.get("notes"):
        for n in result["notes"]:
            print(f"  备注:         {n}")
    print(f"  REAL_WIND_CALL: {REAL_WIND_CALL}")
    print(f"  wind_api_calls:  {WIND_API_CALLS}")
    print("─" * 60)


# ════════════════════════════════════════════════════════════════
# 命令行接口 (自测)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("🧪 DSHA-P59 · 基础因子构造模块 — 仿真自测")
    print("=" * 70)
    print()

    # 引入数据加载模块
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import factor_data_loader

    # 测试1: 参数基线校验
    print("▶ 测试1: F007参数基线校验")
    default_params = get_default_params()
    param_check = validate_parameter_baseline(default_params)
    assert param_check["overall_passed"] is True, \
        f"基准参数应通过校验: {param_check['errors']}"
    print(f"  ✅ 测试1通过 (checks: {param_check['passed_checks']}/{param_check['total_checks']})\n")

    # 测试2: 动量因子计算
    print("▶ 测试2: 动量因子 (Momentum)")
    # 使用内置仿真数据
    test_data = factor_data_loader._generate_builtin_test_data()
    factor_result = compute_factor_from_data(
        data={
            "dates": test_data["dates"],
            "values": test_data["values"],
            "symbol": "ZN.SHF",
            "indicator": "close",
            "source": "SIMULATED (NOT REAL)",
            "status": "OK",
        },
        factor_type="momentum",
        params={"window_days": 5, "factor_id": "TEST-MOM", "factor_name": "测试动量"},
    )
    assert factor_result["status"] == "OK"
    print(f"  ✅ 测试2通过 (factor_count={factor_result['factor_count']})\n")

    # 测试3: 波动率因子
    print("▶ 测试3: 波动率因子 (Volatility)")
    vol_result = compute_factor_from_data(
        data={
            "dates": test_data["dates"],
            "values": test_data["values"],
            "symbol": "ZN.SHF",
            "indicator": "close",
            "source": "SIMULATED (NOT REAL)",
            "status": "OK",
        },
        factor_type="volatility",
        params={"window_days": 5, "factor_id": "TEST-VOL", "factor_name": "测试波动率"},
    )
    assert vol_result["status"] == "OK"
    print(f"  ✅ 测试3通过 (factor_count={vol_result['factor_count']})\n")

    # 测试4: 均值回归因子
    print("▶ 测试4: 均值回归因子 (Mean Reversion)")
    mr_result = compute_factor_from_data(
        data={
            "dates": test_data["dates"],
            "values": test_data["values"],
            "symbol": "ZN.SHF",
            "indicator": "close",
            "source": "SIMULATED (NOT REAL)",
            "status": "OK",
        },
        factor_type="mean_reversion",
        params={"window_days": 5, "factor_id": "TEST-MR", "factor_name": "测试均值回归"},
    )
    assert mr_result["status"] == "OK"
    print(f"  ✅ 测试4通过 (factor_count={mr_result['factor_count']})\n")

    # 测试5: 数据不足时 NO_DATA 状态
    print("▶ 测试5: 数据不足 → NO_DATA 状态")
    no_data_result = compute_factor_from_data(
        data={
            "dates": ["2025-01-02"],
            "values": [24500.0],
            "symbol": "ZN.SHF",
            "indicator": "close",
            "source": "SIMULATED",
            "status": "OK",
        },
        factor_type="momentum",
        params={"window_days": 60},
    )
    assert no_data_result["status"] == "NO_DATA", \
        f"数据不足应为 NO_DATA, 实际 {no_data_result['status']}"
    print(f"  ✅ 测试5通过 (status={no_data_result['status']})\n")

    # 测试6: 参数超出范围警告
    print("▶ 测试6: 参数超出范围 → 警告")
    bad_params = get_default_params()
    bad_params["window_days"] = 200
    bad_check = validate_parameter_baseline(bad_params)
    assert bad_check["overall_passed"] is False
    assert len(bad_check["errors"]) > 0
    print(f"  ✅ 测试6通过 (errors={len(bad_check['errors'])})\n")

    # 测试7: 保存因子结果
    print("▶ 测试7: 保存因子结果到离线目录")
    output_path = save_factor_result(factor_result)
    assert os.path.exists(output_path), f"文件不存在: {output_path}"
    print(f"  ✅ 测试7通过 (saved to: {output_path})\n")

    print("=" * 70)
    print("✅ 全部7项测试通过 — REAL_WIND_CALL=False, wind_api_calls=0")
    print("=" * 70)
    sys.exit(0)
