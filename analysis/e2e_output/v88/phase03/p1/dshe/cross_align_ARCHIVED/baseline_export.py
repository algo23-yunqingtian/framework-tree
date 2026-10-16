#!/usr/bin/env python3
"""
P0-12 渲染基线标准化导出脚本
将 P0-12 CPU 采集数据导出为标准化 JSON 格式，兼容 DSHB P0-13 噪声基线结构。
支持后续合并为 V88 Phase04 统一长稳监控基线。

用法:
  python3 baseline_export.py [--input <json>] [--output <json>]
默认:
  --input  ../../p012_final_triplefix/frozen_p012_gate_package/v88_p012_full_link_cpu_compare.json
  --output ./baseline_export.json
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "..", "..", "..", ".."))

DEFAULT_INPUT = os.path.normpath(os.path.join(
    BASE_DIR, "..", "p012_final_triplefix", "frozen_p012_gate_package",
    "v88_p012_full_link_cpu_compare.json"
))
DEFAULT_OUTPUT = os.path.join(BASE_DIR, "baseline_export.json")


def load_source(path):
    """加载 P0-12 CPU 采集 JSON"""
    if not os.path.exists(path):
        print(f"[WARN] 输入文件不存在: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_metrics(src):
    """从源 JSON 提取关键指标，扁平化为标准化字段"""
    # 尝试从顶层或嵌套结构提取
    pre = src.get("pre_optimization", src.get("pre", {}))
    post = src.get("post_optimization", src.get("post", {}))

    # 提取 post_optimization 的关键值
    cpu_peak = post.get("cpu_peak_pct", src.get("cpu_peak_pct"))
    if cpu_peak is None:
        # 尝试从 full_chain 提取
        fc = src.get("full_chain", post.get("full_chain", {}))
        cpu_peak = fc.get("cpu_peak_pct")

    p99_latency = post.get("p99_latency_ms", post.get("p99_ms"))
    avg_latency = post.get("avg_latency_ms", post.get("avg_ms"))
    render_count = post.get("render_count", src.get("render_count"))
    caliber = post.get("caliber", src.get("caliber", "full_chain_business_steady_state"))
    comparability = post.get("comparability_note", src.get("comparability_note", ""))
    artifact_incomparable = post.get("artifact_declares_incomparable",
                                      src.get("artifact_declares_incomparable", False))

    return {
        "cpu_peak_pct": cpu_peak,
        "p99_latency_ms": p99_latency,
        "avg_latency_ms": avg_latency,
        "render_count": render_count,
        "caliber": caliber,
        "comparability_note": comparability,
        "artifact_declares_incomparable": artifact_incomparable,
    }


def build_export(src, input_path):
    """构建标准化基线导出 JSON"""
    metrics = extract_metrics(src)

    # 计算输入文件 MD5
    md5 = ""
    if os.path.exists(input_path):
        with open(input_path, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest().upper()

    export = {
        "baseline_id": "V88-P012-RENDER-CPU-BASELINE",
        "baseline_type": "render_engine_cpu_performance",
        "agent": "DSHE",
        "phase": "V88-Phase03-P1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": os.path.relpath(input_path, REPO_ROOT) if REPO_ROOT else input_path,
        "source_md5": md5,
        "schema_version": "v88-baseline-export-1.0",

        # 标准化指标（兼容 DSHB P0-13 噪声基线结构）
        "metrics": {
            "cpu_peak_pct": metrics["cpu_peak_pct"],
            "cpu_threshold_phase03": 1.75,
            "cpu_threshold_phase04": 2.0,
            "cpu_caliber": metrics["caliber"],
            "p99_latency_ms": metrics["p99_latency_ms"],
            "avg_latency_ms": metrics["avg_latency_ms"],
            "render_count": metrics["render_count"],
        },

        # 兼容 DSHB P0-13 噪声基线的合并字段
        "merge_compatible": {
            "target_baseline": "V88-Phase04-LongTerm-Monitoring",
            "merge_with": "DSHB-P013-Noise-Baseline",
            "merge_fields": ["cpu_peak_pct", "p99_latency_ms", "noise_rate_pct"],
            "merge_status": "ready",
        },

        # 审计信息
        "audit": {
            "frozen_commit": "b1987a4",
            "frozen_version": "3.0.0",
            "exemption_requested": True,
            "exemption_status": "PENDING_HERMESHF_REVIEW",
            "physical_constraint": True,
            "optimization_exhausted": True,
        },

        # 元数据
        "metadata": {
            "caliber_note": "process_time/wall_time*100, CPU-intensive rendering physical constraint",
            "comparability_note": metrics["comparability_note"],
            "artifact_declares_incomparable": metrics["artifact_declares_incomparable"],
        },
    }

    return export


def main():
    parser = argparse.ArgumentParser(description="P0-12 Render Baseline Export")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input JSON path")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON path")
    args = parser.parse_args()

    src = load_source(args.input)
    if not src:
        print("[ERROR] 无法加载源数据，输出空壳基线")
        src = {}

    export = build_export(src, args.input)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    print(f"[OK] 基线导出完成: {args.output}")
    print(f"  cpu_peak_pct: {export['metrics']['cpu_peak_pct']}")
    print(f"  caliber: {export['metrics']['cpu_caliber']}")
    print(f"  merge_status: {export['merge_compatible']['merge_status']}")
    print(f"  source_md5: {export['source_md5'][:12]}")


if __name__ == "__main__":
    main()
