#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHFE RB/HC WDF Collection Template
====================================

Prepared by: DSHC-MAINT-01
Date:       2026-10-19
Status:     PREPARED — NOT EXECUTED (wind_api_calls=0)

Purpose:
  Ready-to-use WDF collection template for SHFE rebar (RB) and
  hot-rolled coil (HC) instruments. Mirrors the 6-metal template
  from DSHC-SKILL-FACTOR01.

Time Window:
  2025-01-02 → 2026-10-19 (identical to metals template)

Indicators:
  CLOSE, VOL, OI, SETTLE (4 indicators per symbol)

Symbols:
  RB.SHF — Shanghai Rebar (螺纹钢)
  HC.SHF — Hot-rolled Coil (热轧卷板)

Estimated API Calls:
  2 symbols × 4 indicators = 8 WSD calls
  With 3 attempts max per call: max 24 calls

Integration Notes:
  1. This template is PREPARED ONLY. No Wind API calls made.
  2. For execution, use the same F01 GUI script pattern:
     - Update $symbols array in dshc_f01_gui_fetch.ps1
     - Or use dshc_ignite_a02_wdf_fetch.ps1 with $Instruments parameter
  3. RB/HC data will produce LONG-format CSV matching the
     FACTOR_EXTRACT_V1 input schema.
  4. If data is collected, add to wdf_sample_metals_aligned.csv
     OR create separate wdf_sample_steel_aligned.csv.
  5. Factor extraction: pass new CSV to factor_extract_v1.py
     with --symbols RB.SHF,HC.SHF

Risk Notes:
  See COLLECTION_RISK_LIST.md for HIGH/LOW price rules
  affecting ATR% factor (P2备选).
"""

import json
from pathlib import Path


# ============================================================================
# Template Configuration (for reference / manual execution)
# ============================================================================

TEMPLATE_CONFIG = {
    "task_id": "SHFE_RB_HC_WDF_PREP",
    "version": "1.0.0",
    "prepared_by": "DSHC-MAINT-01",
    "prepared_at": "2026-10-19",
    "wind_api_calls": 0,
    "executed": False,
    "execution_status": "PREPARED_ONLY",
    "time_window": {
        "start": "2025-01-02",
        "end": "2026-10-19",
        "note": "Identical to metals template (DSHC-SKILL-FACTOR01)"
    },
    "indicators": ["CLOSE", "VOL", "OI", "SETTLE"],
    "symbols": {
        "RB.SHF": {
            "exchange": "SHFE",
            "name_cn": "螺纹钢",
            "name_en": "Rebar",
            "status": "NEW",
            "wind_code": "RB.SHF",
        },
        "HC.SHF": {
            "exchange": "SHFE",
            "name_cn": "热轧卷板",
            "name_en": "Hot-rolled Coil",
            "status": "NEW",
            "wind_code": "HC.SHF",
        },
    },
    "api_calls_estimated": {
        "total_wsd_calls": 8,
        "max_attempts_per_call": 3,
        "max_total_calls": 24,
        "fields_per_call": "CLOSE;VOL;OI;SETTLE",
    },
    "output_format": {
        "type": "long_form_csv",
        "columns": ["date", "symbol", "indicator", "value", "source"],
        "encoding": "utf-8",
    },
    "wind_formula_template": 'WSD("{symbol}","CLOSE;VOL;OI;SETTLE","{start}","{end}","Fill=Previous")',
    "f01_script_integration": {
        "primary": "scripts/dshc_f01_gui_fetch.ps1",
        "integration_point": "Update $symbols array: add 'RB.SHF','HC.SHF'",
        "locked": True,
        "locked_version": "v1.0 @ 593d688",
    },
    "factor_integration": {
        "skill": "FACTOR_EXTRACT_V1",
        "version": "1.0.0",
        "supported_factors": [
            "spread_cs", "oi_level", "oi_change_1d",
            "oi_change_rate_7d", "spread_pct",
            "contract_switch_flag", "momentum_20d",
        ],
        "note": "All 7 factors use only CLOSE/OI/SETTLE. No additional work needed.",
    },
}


# ============================================================================
# Sample Output (simulated, for schema verification)
# ============================================================================

SAMPLE_OUTPUT = {
    "description": "Simulated sample rows — NOT real data. Shows expected CSV format.",
    "columns": ["date", "symbol", "indicator", "value", "source"],
    "sample_rows": [
        ["2025-01-02", "RB.SHF", "CLOSE", 3650.0, "SHFE"],
        ["2025-01-02", "RB.SHF", "SETTLE", 3648.0, "SHFE"],
        ["2025-01-02", "RB.SHF", "OI", 1850000.0, "SHFE"],
        ["2025-01-02", "RB.SHF", "VOL", 245000.0, "SHFE"],
        ["2025-01-03", "RB.SHF", "CLOSE", 3680.0, "SHFE"],
        ["2025-01-03", "RB.SHF", "SETTLE", 3678.0, "SHFE"],
        ["2025-01-03", "RB.SHF", "OI", 1860000.0, "SHFE"],
        ["2025-01-03", "RB.SHF", "VOL", 251000.0, "SHFE"],
        ["2025-01-02", "HC.SHF", "CLOSE", 3420.0, "SHFE"],
        ["2025-01-02", "HC.SHF", "SETTLE", 3418.0, "SHFE"],
        ["2025-01-02", "HC.SHF", "OI", 920000.0, "SHFE"],
        ["2025-01-02", "HC.SHF", "VOL", 180000.0, "SHFE"],
    ],
}


if __name__ == "__main__":
    import json

    print("=" * 60)
    print("SHFE RB/HC WDF Collection Template")
    print(f"  Version: {TEMPLATE_CONFIG['version']}")
    print(f"  Prepared by: {TEMPLATE_CONFIG['prepared_by']}")
    print(f"  Time window: {TEMPLATE_CONFIG['time_window']['start']} → {TEMPLATE_CONFIG['time_window']['end']}")
    print(f"  Symbols: {', '.join(TEMPLATE_CONFIG['symbols'].keys())}")
    print(f"  Indicators: {', '.join(TEMPLATE_CONFIG['indicators'])}")
    print(f"  Estimated API calls: {TEMPLATE_CONFIG['api_calls_estimated']['total_wsd_calls']} WSD / {TEMPLATE_CONFIG['api_calls_estimated']['max_total_calls']} max")
    print(f"  Wind API calls made: {TEMPLATE_CONFIG['wind_api_calls']}")
    print(f"  Execution status: {TEMPLATE_CONFIG['execution_status']}")
    print("=" * 60)

    # Write template config JSON
    config_path = Path(__file__).parent / "shfe_rb_hc_template.json"
    output = {
        "template_config": TEMPLATE_CONFIG,
        "sample_output": SAMPLE_OUTPUT,
        "generated_at": "2026-10-19",
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nTemplate config written: {config_path}")

    # Write simulated sample CSV
    csv_path = Path(__file__).parent / "shfe_rb_hc_sample.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("# SHFE RB/HC WDF Collection Template\n")
        f.write("# NOTE: Simulated sample data — NOT real Wind data\n")
        f.write("# Prepared: DSHC-MAINT-01 | 2026-10-19\n")
        f.write("# Real execution requires Wind API calls (not performed)\n")
        f.write("#\n")
        f.write("date,symbol,indicator,value,source\n")
        for row in SAMPLE_OUTPUT["sample_rows"]:
            f.write(",".join(str(v) for v in row) + "\n")
    print(f"Sample CSV written: {csv_path}")

    print("\n" + "=" * 60)
    print("STATUS: PREPARED — NOT EXECUTED")
    print("wind_api_calls=0")
    print("No real data has been collected.")
    print("=" * 60)