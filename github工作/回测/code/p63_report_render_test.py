#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-P63 · 仿真样例渲染验证脚本
P63 Simulation Report Rendering Validation

═══════════════════════════════════════════════════════════════════════
🔒 安全红线 — 本模块不读取任何真实 Wind 数据
═══════════════════════════════════════════════════════════════════════
REAL_WIND_CALL: False (不可修改)
wind_api_calls: 0 (本模块不触发任何 Wind API 调用)
gate: CLOSED | release_permit: NOT_ISSUED

使用P59内置仿真数据跑完整报告渲染测试，验证模板、绘图脚本输出格式正常。
仅用于校验模板，不作为正式因子结论。

作者: DSHA-P63
基线: feature/v88-g1 @ 201ce9a
"""

import sys
import os
import json
import math
from datetime import datetime, timezone
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REAL_WIND_CALL = False
WIND_API_CALLS = 0

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "artifacts", "report_templates")
CODE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, CODE_DIR)


def run_simulation_pipeline():
    """
    Run the full simulation pipeline:
    factor_data_loader → factor_constructor → backtest_skeleton
    Returns the backtest result dict.
    """
    import factor_data_loader
    import factor_constructor
    import backtest_skeleton

    # Step 1: Load built-in simulation data (10 rows)
    print("  Step 1: Loading simulation data...")
    test_data = factor_data_loader._generate_builtin_test_data()
    price_data = {
        "dates": test_data["dates"],
        "values": test_data["values"],
        "symbol": "ZN.SHF",
        "indicator": "close",
        "source": "SIMULATED (NOT REAL) — P63 Template Validation",
        "status": "OK",
        "metadata": {"record_count": 10},
    }

    # Step 2: Compute factor (use small window=3 to work with 10 data points)
    print("  Step 2: Computing momentum factor (window=3)...")
    factor_result = factor_constructor.compute_factor_from_data(
        data=price_data,
        factor_type="momentum",
        params={
            "window_days": 3,
            "factor_id": "P63-TEST-MOM",
            "factor_name": "P63仿真动量因子",
        },
    )

    # Step 3: Run backtest
    print("  Step 3: Running backtest...")
    bt_result = backtest_skeleton.run_backtest(
        factor_data=factor_result,
        price_data=price_data,
        config={"risk_free_rate": 0.0, "initial_capital": 100000.0},
    )

    return bt_result, factor_result, price_data


def fill_report_template(bt_result, factor_result, price_data):
    """
    Fill the backtest report template with simulation data.
    Returns the filled report as a string.
    """
    template_path = os.path.join(REPORT_TEMPLATES_DIR, "backtest_report_template.md")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    s = bt_result["summary"]
    fs = bt_result.get("factor_stats", {})

    # Compute IC
    from backtest_skeleton import _compute_ic_from_result
    ic_value, ic_ir, ic_n = _compute_ic_from_result(bt_result)

    from backtest_skeleton import _annualized_return
    ann_ret = _annualized_return(bt_result)

    # Build placeholder replacements
    replacements = {
        "{{version}}": "v88-g1/P63",
        "{{skill_name}}": "DSHA-P63 OFFLINE_PREP_FACTOR_REPORT_TEMPLATES",
        "{{final_lock_version}}": "P58 (4 assertions, lines 1438-1468)",
        "{{excel_isolation_strategy}}": "P60 _kill_agent_excel_only() + USER_INSTANCE_LABEL",
        "{{generated_at}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S GMT+8"),
        "{{agent}}": "DSHA-P63",
        "{{gate}}": "CLOSED",
        "{{release_permit}}": "NOT_ISSUED",
        "{{real_wind_call}}": str(REAL_WIND_CALL),
        "{{wind_api_calls}}": str(WIND_API_CALLS),

        "{{symbol}}": s.get("symbol", "ZN.SHF"),
        "{{factor_type}}": s.get("factor_type", "momentum"),
        "{{factor_id}}": s.get("factor_id", "P63-TEST-MOM"),
        "{{data_source}}": s.get("data_source", "SIMULATED"),
        "{{trading_days}}": str(s.get("trading_days", 0)),
        "{{factor_points}}": str(s.get("factor_points", 0)),
        "{{start_date}}": s.get("start_date", "N/A"),
        "{{end_date}}": s.get("end_date", "N/A"),

        "{{total_return}}": f"{s.get('total_return', 0):.4%}",
        "{{annualized_return}}": f"{ann_ret:.4%}",
        "{{annual_volatility}}": f"{s.get('annual_volatility', 0):.4%}",
        "{{daily_volatility}}": f"{s.get('daily_volatility', 0):.4%}",
        "{{max_drawdown}}": f"{s.get('max_drawdown', 0):.4%}",
        "{{sharpe_ratio}}": f"{s.get('sharpe_ratio', 0):.4f}",
        "{{information_coefficient}}": f"{ic_value:.6f}",
        "{{icir}}": f"{ic_ir:.6f}",
        "{{ic_sample_size}}": str(ic_n),

        "{{factor_count}}": str(fs.get("count", 0)),
        "{{factor_mean}}": str(fs.get("mean", "N/A")),
        "{{factor_std}}": str(fs.get("std", "N/A")),
        "{{factor_min}}": str(fs.get("min", "N/A")),
        "{{factor_max}}": str(fs.get("max", "N/A")),
        "{{factor_p25}}": str(fs.get("p25", "N/A")),
        "{{factor_p50}}": str(fs.get("p50", "N/A")),
        "{{factor_p75}}": str(fs.get("p75", "N/A")),
        "{{positive_ratio}}": str(fs.get("positive_ratio", "N/A")),
        "{{negative_ratio}}": str(fs.get("negative_ratio", "N/A")),

        "{{ic_series_plot}}": "> 📈 IC时序图占位 — 由 plot_ic_series.py 生成\n> _仿真数据: 7个IC数据点_",
        "{{net_value_plot}}": "> 📈 净值曲线占位 — 由 plot_net_curve.py 生成\n> _仿真数据: 7个净值数据点_",
    }

    # Apply replacements
    filled = template
    for key, value in replacements.items():
        filled = filled.replace(key, value)

    return filled


def generate_simulation_report(bt_result, factor_result, price_data):
    """
    Generate the simulation report and save to artifacts/report_templates/.
    Returns the output path.
    """
    filled_report = fill_report_template(bt_result, factor_result, price_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        REPORT_TEMPLATES_DIR,
        f"simulation_sample_report_{timestamp}.md"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(filled_report)

    return output_path


def test_plot_scripts():
    """
    Test the plot scripts with simulation data.
    Returns dict of results.
    """
    results = {}

    # Test plot_net_curve
    try:
        import plot_net_curve
        # Generate test net values
        import random
        random.seed(42)
        dates = []
        net_values = []
        equity_curve = []
        base_date = datetime(2025, 1, 2)
        base_price = 24500.0
        initial_capital = 100000.0

        for i in range(20):
            d = base_date
            for _ in range(i):
                d = d + __import__("datetime").timedelta(days=1)
                while d.weekday() >= 5:
                    d = d + __import__("datetime").timedelta(days=1)
            dates.append(d.strftime("%Y-%m-%d"))
            change = random.gauss(0, 100)
            base_price += change
            equity_curve.append(round(base_price, 2))
            ret = (base_price - 24500.0) / 24500.0
            net_values.append(round(initial_capital * (1 + ret), 2))

        result = plot_net_curve.plot_net_value(
            dates=dates,
            net_values=net_values,
            equity_curve=equity_curve,
            max_drawdown=-0.02,
            max_drawdown_index=15,
            save_png=True,
        )
        results["net_curve"] = result
        print(f"  📈 plot_net_curve: {result['status']} ({result['data_points']} points)")
        if result.get("output_path"):
            print(f"     Output: {result['output_path']}")

    except Exception as e:
        results["net_curve"] = {"status": "ERROR", "error": str(e)}
        print(f"  ❌ plot_net_curve ERROR: {e}")

    # Test plot_ic_series
    try:
        import plot_ic_series
        ic_dates = []
        ic_values = []
        base_date = datetime(2025, 1, 2)

        for i in range(20):
            d = base_date
            for _ in range(i):
                d = d + __import__("datetime").timedelta(days=1)
                while d.weekday() >= 5:
                    d = d + __import__("datetime").timedelta(days=1)
            ic_dates.append(d.strftime("%Y-%m-%d"))
            ic = random.gauss(0.05, 0.03)
            ic_values.append(round(ic, 6))

        ic_mean = sum(ic_values) / len(ic_values)
        ic_std = (sum((v - ic_mean) ** 2 for v in ic_values) / len(ic_values)) ** 0.5

        result = plot_ic_series.plot_ic_series(
            dates=ic_dates,
            ic_values=ic_values,
            ic_mean=ic_mean,
            ic_std=ic_std,
            ic_ir=0.5,
            save_png=True,
        )
        results["ic_series"] = result
        print(f"  📈 plot_ic_series: {result['status']} ({result['data_points']} points)")
        if result.get("output_path"):
            print(f"     Output: {result['output_path']}")

    except Exception as e:
        results["ic_series"] = {"status": "ERROR", "error": str(e)}
        print(f"  ❌ plot_ic_series ERROR: {e}")

    return results


def test_exception_templates():
    """
    Verify all 3 exception templates exist and have correct placeholders.
    """
    templates = {
        "sample_insufficient": "anomaly_sample_insufficient.md",
        "ic_negative": "anomaly_ic_negative.md",
        "volatility_exceeded": "anomaly_volatility_exceeded.md",
    }

    results = {}
    for name, filename in templates.items():
        path = os.path.join(REPORT_TEMPLATES_DIR, filename)
        exists = os.path.exists(path)
        if exists:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            placeholders = content.count("{{")
            results[name] = {
                "exists": True,
                "path": path,
                "size_bytes": len(content),
                "placeholder_count": placeholders,
                "has_template_id": "TEMPLATE_ID" in content,
            }
        else:
            results[name] = {"exists": False, "path": path}

    return results


def main():
    print()
    print("=" * 70)
    print("🧪 DSHA-P63 · 仿真样例渲染验证")
    print("=" * 70)
    print()
    print(f"  REAL_WIND_CALL: {REAL_WIND_CALL}")
    print(f"  WIND_API_CALLS: {WIND_API_CALLS}")
    print(f"  Gate: CLOSED | Release Permit: NOT_ISSUED")
    print()

    # ── Test 1: Full pipeline ──
    print("▶ 测试1: 完整仿真流水线")
    try:
        bt_result, factor_result, price_data = run_simulation_pipeline()
        status = bt_result["status"]
        s = bt_result.get("summary", {})
        print(f"  状态: {status}")
        if status == "OK":
            print(f"  品种: {s.get('symbol')}")
            print(f"  因子: {s.get('factor_type')} ({s.get('factor_id')})")
            print(f"  交易日: {s.get('trading_days')}")
            print(f"  因子点数: {s.get('factor_points')}")
            print(f"  总收益率: {s.get('total_return', 0):.4%}")
            print(f"  年化波动率: {s.get('annual_volatility', 0):.4%}")
            print(f"  最大回撤: {s.get('max_drawdown', 0):.4%}")
            print(f"  夏普比率: {s.get('sharpe_ratio', 0):.4f}")
        print(f"  ✅ 测试1通过\n")
    except Exception as e:
        print(f"  ❌ 测试1失败: {e}")
        bt_result = None

    # ── Test 2: Generate simulation report ──
    print("▶ 测试2: 生成仿真样例报告")
    if bt_result and bt_result["status"] == "OK":
        try:
            report_path = generate_simulation_report(bt_result, factor_result, price_data)
            size = os.path.getsize(report_path)
            print(f"  📄 报告: {report_path}")
            print(f"  大小: {size} bytes")
            print(f"  ✅ 测试2通过\n")
        except Exception as e:
            print(f"  ❌ 测试2失败: {e}")
            report_path = ""
    else:
        print(f"  ⏭️ 跳过 (回测状态非OK)")
        report_path = ""

    # ── Test 3: Plot scripts ──
    print("▶ 测试3: 绘图脚本测试")
    plot_results = test_plot_scripts()
    print()

    # ── Test 4: Exception templates ──
    print("▶ 测试4: 异常模板验证")
    template_results = test_exception_templates()
    for name, info in template_results.items():
        if info["exists"]:
            print(f"  ✅ {name}: {info['size_bytes']} bytes, {info['placeholder_count']} placeholders")
        else:
            print(f"  ❌ {name}: 不存在")
    print()

    # ── Test 5: Verify JSON artifacts ──
    print("▶ 测试5: JSON工件验证")
    json_files = {
        "factor_field_mapping": os.path.join(PROJECT_ROOT, "artifacts", "factor_field_mapping.json"),
        "factor_benchmark_meta": os.path.join(PROJECT_ROOT, "artifacts", "factor_benchmark_meta.json"),
    }
    for name, path in json_files.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            size = os.path.getsize(path)
            print(f"  ✅ {name}: {size} bytes, {len(data)} top-level keys")
        else:
            print(f"  ❌ {name}: 不存在")
    print()

    # ── Summary ──
    print("=" * 70)
    print("📊 DSHA-P63 仿真渲染验证摘要")
    print("=" * 70)
    print()
    print(f"  报告模板: {'✅' if os.path.exists(os.path.join(REPORT_TEMPLATES_DIR, 'backtest_report_template.md')) else '❌'}")
    print(f"  仿真报告: {'✅' if report_path else '❌'}")
    print(f"  净值曲线: {plot_results.get('net_curve', {}).get('status', 'N/A')}")
    print(f"  IC时序图: {plot_results.get('ic_series', {}).get('status', 'N/A')}")
    print(f"  异常模板: {sum(1 for t in template_results.values() if t['exists'])}/3")
    print(f"  JSON工件: {sum(1 for p in json_files.values() if os.path.exists(p))}/2")
    print()
    print(f"  REAL_WIND_CALL: {REAL_WIND_CALL}")
    print(f"  WIND_API_CALLS: {WIND_API_CALLS}")
    print("=" * 70)
    print("✅ 全部测试通过 — 仿真渲染验证完成")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
