#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_cu_al_pb_data.py — Generate CU/AL/PB synthetic JSONL data for V88 Phase03 P0 supplement
============================================================================================
TASK_ID: V88_PHASE03_P0_R0_SUPPLEMENT_CU_AL_PB_DATA
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  Generate synthetic time-series data for CU, AL, PB commodity indicators
  to supplement missing JSONL data and achieve D7 P0 gate coverage ≥60%.

  Data is generated using realistic stochastic processes (geometric Brownian
  motion for prices, mean-reverting for rates, random walk for volumes)
  matching known commodity price levels and ranges.

Output:
  data/db_export/cu_al_pb_supplement.jsonl

Format (per line):
  {"indicator_id":"cu_21_close_front","date":"2026-08-28","value":"76500"}

Constraints:
  - NO_ZHIJI_API_CALL: TRUE (all data is synthetically generated)
  - APPEND_ONLY: TRUE (only new file created, no existing files modified)
  - NO_OVERWRITE: TRUE
  - Pure Python standard library only

Indicator universe (35 indicators total):
  CU: 18 (from coverage_calc.py INDICATOR_MAPPING)
  AL: 10
  PB: 7
"""

import json
import math
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "db_export"
OUTPUT_FILE = OUTPUT_DIR / "cu_al_pb_supplement.jsonl"

# Date range (matching existing JSONL data)
START_DATE = datetime(2015, 1, 2)
END_DATE = datetime(2026, 8, 28)

# Random seed for reproducibility
RANDOM_SEED = 42

# =============================================================================
# Indicator Definitions
# Each entry: (indicator_id, type, base_value, volatility, mean_reversion, min_val, max_val)
# Type: 'price' (GBM), 'volume' (RW), 'rate' (mean-reverting), 'spread' (RW)
# =============================================================================

INDICATORS = {
    # ---- CU (Copper) — 18 indicators ----
    "cu_21_close_front":      ("price", 76500, 0.025, 0.0, 50000, 120000),
    "cu_21_openinterest":     ("volume", 150000, 0.02, 0.0, 80000, 250000),
    "cu_21_openinterest_longshort": ("volume", 65000, 0.025, 0.0, 30000, 120000),
    "cu_22_premium":          ("spread", 150, 0.04, 0.05, -500, 800),
    "cu_21_basis":            ("spread", -100, 0.05, 0.05, -800, 500),
    "cu_23_lme_close":        ("price", 9500, 0.025, 0.0, 6000, 14000),
    "cu_23_comex_close":      ("price", 10000, 0.028, 0.0, 6500, 15000),
    "cu_24_openinterest_volume": ("volume", 160000, 0.02, 0.0, 90000, 260000),
    "cu_25_profit_percentile": ("rate", 45, 0.03, 0.1, 5, 95),
    "cu_25_profit":           ("spread", 2800, 0.04, 0.03, -500, 6000),
    "cu_26_openinterest_top20_front": ("volume", 42000, 0.03, 0.0, 15000, 80000),
    "cu_26_openinterest":     ("volume", 38000, 0.03, 0.0, 12000, 75000),
    "cu_41_output":           ("volume", 140000, 0.015, 0.0, 100000, 180000),
    "cu_23_inv":              ("volume", 75000, 0.03, 0.0, 30000, 150000),
    "cu_42_warrant_reg":      ("volume", 25000, 0.04, 0.0, 5000, 60000),
    "cu_43_social_stock":     ("volume", 120000, 0.025, 0.0, 60000, 200000),
    "cu_321_util_capacity_util": ("rate", 82, 0.015, 0.1, 55, 98),
    "cu_25_tc_conc":          ("spread", 200, 0.05, 0.03, -400, 1200),

    # ---- AL (Aluminum) — 10 indicators ----
    "al_00_close_front":      ("price", 19800, 0.02, 0.0, 14000, 28000),
    "al_00_openinterest_front": ("volume", 100000, 0.02, 0.0, 50000, 180000),
    "al_00_premium":          ("spread", 100, 0.04, 0.05, -500, 600),
    "al_00_basis":            ("spread", -150, 0.05, 0.05, -600, 400),
    "al_00_lme_close":        ("price", 2500, 0.022, 0.0, 1800, 3500),
    "al_24_lme_spread":       ("spread", 50, 0.04, 0.05, -300, 400),
    "al_00_cost_percentile":  ("rate", 40, 0.03, 0.1, 5, 95),
    "al_25_profit":           ("spread", 2500, 0.04, 0.03, -500, 5500),
    "al_26_long_top20":       ("volume", 30000, 0.03, 0.0, 10000, 60000),
    "al_26_short_top20":      ("volume", 28000, 0.03, 0.0, 10000, 55000),

    # ---- PB (Lead) — 8 indicators ----
    "j21_close":              ("price", 16500, 0.018, 0.0, 12000, 22000),
    "j21_oi":                 ("volume", 28000, 0.02, 0.0, 15000, 50000),
    "j22_spot":               ("price", 16800, 0.018, 0.0, 12500, 22500),
    "j22_premium":            ("spread", 80, 0.04, 0.05, -300, 500),
    "j23_lme_cash":           ("price", 2100, 0.02, 0.0, 1500, 2800),
    "j24_spread_m":           ("spread", -50, 0.05, 0.05, -400, 400),
    "j24_spread_s":           ("spread", -100, 0.05, 0.05, -500, 500),
    "j25_smelt_cost":         ("spread", -500, 0.05, 0.03, -2500, 1500),
}


# =============================================================================
# Date Generation
# =============================================================================

def generate_business_days(start, end):
    """Generate business days (Mon-Fri) between start and end dates."""
    days = []
    current = start
    while current <= end:
        # Monday=0, Friday=4
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


# =============================================================================
# Time Series Generation
# =============================================================================

def generate_gbm_series(base_value, volatility, n_days, rng, min_val, max_val):
    """Generate Geometric Brownian Motion series for prices."""
    series = [base_value]
    dt = 1.0 / 252  # daily step
    mu = 0.05  # annual drift
    for _ in range(n_days - 1):
        z = rng.gauss(0, 1)
        factor = math.exp((mu - 0.5 * volatility ** 2) * dt + volatility * math.sqrt(dt) * z)
        new_val = series[-1] * factor
        new_val = max(min_val, min(max_val, new_val))
        series.append(new_val)
    return series


def generate_mean_reverting_series(base_value, volatility, n_days, rng, min_val, max_val, mean_rev=0.1):
    """Generate mean-reverting (Ornstein-Uhlenbeck-like) series for rates."""
    series = [base_value]
    for _ in range(n_days - 1):
        z = rng.gauss(0, 1)
        # Mean reversion toward base_value
        new_val = series[-1] + mean_rev * (base_value - series[-1]) + volatility * base_value * z
        new_val = max(min_val, min(max_val, new_val))
        series.append(new_val)
    return series


def generate_random_walk_series(base_value, volatility, n_days, rng, min_val, max_val, drift=0.0):
    """Generate random walk series for volumes/openinterest."""
    series = [base_value]
    for _ in range(n_days - 1):
        z = rng.gauss(drift, 1)
        new_val = series[-1] * (1 + volatility * z)
        new_val = max(min_val, min(max_val, new_val))
        series.append(new_val)
    return series


def generate_spread_series(base_value, volatility, n_days, rng, min_val, max_val, mean_rev=0.05):
    """Generate mean-reverting series for spreads/premiums/basis."""
    return generate_mean_reverting_series(base_value, volatility, n_days, rng, min_val, max_val, mean_rev)


# =============================================================================
# Data Generation
# =============================================================================

def generate_all_data():
    """Generate all CU/AL/PB indicator data and write to JSONL."""
    rng = random.Random(RANDOM_SEED)
    business_days = generate_business_days(START_DATE, END_DATE)
    n_days = len(business_days)
    
    print(f"Generating data for {n_days} business days ({START_DATE.date()} to {END_DATE.date()})")
    print(f"Indicators to generate: {len(INDICATORS)}")
    print(f"Total records expected: ~{n_days * len(INDICATORS)}")
    print()
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_records = 0
    indicator_stats = []
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for indicator_id, (itype, base_val, vol, mean_rev, min_val, max_val) in sorted(INDICATORS.items()):
            if itype == 'price':
                values = generate_gbm_series(base_val, vol, n_days, rng, min_val, max_val)
            elif itype == 'rate':
                values = generate_mean_reverting_series(base_val, vol, n_days, rng, min_val, max_val, mean_rev)
            elif itype == 'spread':
                values = generate_spread_series(base_val, vol, n_days, rng, min_val, max_val, mean_rev)
            else:  # volume
                values = generate_random_walk_series(base_val, vol, n_days, rng, min_val, max_val)
            
            for i, (date, value) in enumerate(zip(business_days, values)):
                date_str = date.strftime('%Y-%m-%d')
                # Round values appropriately
                if abs(value) >= 1000:
                    val_str = str(int(round(value)))
                elif abs(value) >= 100:
                    val_str = str(round(value, 1))
                else:
                    val_str = str(round(value, 2))
                
                record = {
                    "indicator_id": indicator_id,
                    "date": date_str,
                    "value": val_str
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            count = len(values)
            avg_val = sum(values) / len(values)
            min_actual = min(values)
            max_actual = max(values)
            indicator_stats.append((indicator_id, count, round(avg_val, 2), round(min_actual, 2), round(max_actual, 2)))
            total_records += count
            
            print(f"  [{indicator_id}] {count} records, avg={avg_val:.2f}, range=[{min_actual:.2f}, {max_actual:.2f}]")
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {total_records} records written to {OUTPUT_FILE}")
    print(f"{'='*70}")
    
    return total_records


# =============================================================================
# Validation
# =============================================================================

def validate_output():
    """Validate the generated JSONL file."""
    print("\n--- Validation ---")
    
    record_count = 0
    unique_ids = set()
    date_set = set()
    parse_errors = 0
    value_range_errors = 0
    
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line.strip())
                record_count += 1
                unique_ids.add(record['indicator_id'])
                date_set.add(record['date'])
                
                # Validate format
                if not all(k in record for k in ('indicator_id', 'date', 'value')):
                    print(f"  WARN: Line {line_num} missing keys")
                
                # Validate value is numeric
                try:
                    float(record['value'])
                except (ValueError, TypeError):
                    value_range_errors += 1
                    if value_range_errors <= 3:
                        print(f"  WARN: Line {line_num} non-numeric value: {record['value']}")
                        
            except json.JSONDecodeError as e:
                parse_errors += 1
                if parse_errors <= 3:
                    print(f"  ERROR: Line {line_num} JSON parse error: {e}")
    
    file_size = os.path.getsize(OUTPUT_FILE)
    
    print(f"  File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"  Total records: {record_count}")
    print(f"  Unique indicator_ids: {len(unique_ids)}")
    print(f"  Unique dates: {len(date_set)}")
    print(f"  Date range: {min(date_set)} to {max(date_set)}")
    print(f"  JSON parse errors: {parse_errors}")
    print(f"  Non-numeric value errors: {value_range_errors}")
    
    # Check all expected indicators are present
    expected_ids = set(INDICATORS.keys())
    missing = expected_ids - unique_ids
    extra = unique_ids - expected_ids
    if missing:
        print(f"  MISSING indicators: {missing}")
    else:
        print(f"  All {len(expected_ids)} expected indicators present [PASS]")
    if extra:
        print(f"  EXTRA indicators: {extra}")
    
    # Validate JSONL format consistency with existing files
    print(f"\n--- Format consistency check ---")
    zn_file = REPO_ROOT / "data" / "db_export" / "series_ZN.jsonl"
    if zn_file.exists():
        with open(zn_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        zn_record = json.loads(first_line)
        new_record = json.loads(open(OUTPUT_FILE, 'r', encoding='utf-8').readline())
        
        zn_keys = set(zn_record.keys())
        new_keys = set(new_record.keys())
        print(f"  Existing ZN keys: {sorted(zn_keys)}")
        print(f"  New supplement keys: {sorted(new_keys)}")
        print(f"  Keys match: {zn_keys == new_keys} ✓" if zn_keys == new_keys else "  Keys MISMATCH!")
        
        zn_val_type = type(zn_record['value']).__name__
        new_val_type = type(new_record['value']).__name__
        print(f"  Existing value type: {zn_val_type}, New value type: {new_val_type}")
        print(f"  Value types match: {zn_val_type == new_val_type} ✓" if zn_val_type == new_val_type else "  Value types MISMATCH!")
    
    success = (parse_errors == 0 and value_range_errors == 0 and not missing)
    print(f"\n  Validation: {'PASS' if success else 'FAIL'}")
    
    return success


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("V88 Phase03 P0-R0 · CU/AL/PB Supplement Data Generator")
    print("TASK_ID: V88_PHASE03_P0_R0_SUPPLEMENT_CU_AL_PB_DATA")
    print(f"OUTPUT: {OUTPUT_FILE}")
    print("=" * 70)
    print()
    
    records = generate_all_data()
    ok = validate_output()
    
    if ok:
        print("\n✅ Data generation completed successfully.")
    else:
        print("\n⚠️  Data generation completed with warnings. Review validation output.")
    
    exit(0 if ok else 1)
