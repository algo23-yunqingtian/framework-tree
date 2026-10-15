#!/usr/bin/env python3
"""Validate coverage_report.json structure."""
import json
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
report_path = script_dir.parent / "coverage_report.json"
with open(str(report_path), "r", encoding="utf-8") as f:
    report = json.load(f)

print("=== JSON Structure Validation ===")
print(f"task_id: {report['task_id']}")
print(f"timestamp: {report['timestamp']}")
print(f"overall.total_indicators: {report['overall']['total_indicators']}")
print(f"overall.covered: {report['overall']['covered']}")
print(f"overall.coverage_rate_pct: {report['overall']['coverage_rate_pct']}")
print(f"overall.gate_status: {report['overall']['gate_status']}")
print(f"overall.gate_threshold_pct: {report['overall']['gate_threshold_pct']}")
print(f"overall.gate_phase: {report['overall']['gate_phase']}")
print(f"per_commodity keys: {list(report['per_commodity'].keys())}")
print(f"per_indicator count: {len(report['per_indicator'])}")
print(f"gaps.no_mapping count: {len(report['gaps']['no_mapping'])}")
print(f"gaps.no_data count: {len(report['gaps']['no_data'])}")
print(f"gaps.simulated_only count: {len(report['gaps']['simulated_only'])}")
print(f"gaps.other count: {len(report['gaps']['other'])}")
print(f"recommendations count: {len(report['recommendations'])}")

# Verify per_indicator sample
print()
print("=== Sample Per-Indicator Records ===")
for rec in report["per_indicator"][:5]:
    print(f"  {rec['meta_chart_id']:25s} | {rec['commodity']:3s} | mapped={str(rec['mapped_to']):25s} | covered={rec['coverage_status']:10s} | count={rec['record_count']} | db={rec['db_used']}")

# Find covered indicators
covered = [r for r in report["per_indicator"] if r["coverage_status"] == "covered"]
print(f"\nCovered indicators: {len(covered)}")
for rec in sorted(covered, key=lambda x: x["commodity"])[:10]:
    dr = rec.get("date_range")
    dr_str = f"{dr['start']} ~ {dr['end']}" if dr else "N/A"
    print(f"  {rec['meta_chart_id']:25s} | {rec['commodity']:3s} | {rec['chart_id']:15s} | count={rec['record_count']:3d} | range={dr_str}")

# Find simulated_only from gaps
print(f"\n=== Gap Examples ===")
for gap_type in ["no_mapping", "no_data", "simulated_only"]:
    items = report["gaps"][gap_type]
    if items:
        print(f"{gap_type}: {len(items)} items")
        for item in items[:3]:
            print(f"  {item['indicator_id']:25s} | {item['commodity']:3s} | {item['reason'][:60]}")

# Verify all required fields in per_indicator
print("\n=== Per-Indicator Field Validation ===")
required_fields = ["meta_chart_id", "chart_id", "commodity", "mapped_to", "has_mapping", "record_count", "has_real_data", "coverage_status", "date_range"]
all_valid = True
for rec in report["per_indicator"]:
    for field in required_fields:
        if field not in rec:
            print(f"  MISSING: {field} in {rec.get('meta_chart_id', '?')}")
            all_valid = False
if all_valid:
    print("  All required fields present in all per_indicator records.")

print(f"\nValidation complete.")
