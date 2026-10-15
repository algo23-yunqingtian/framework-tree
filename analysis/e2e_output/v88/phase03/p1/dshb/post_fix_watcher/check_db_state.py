#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check current DB state: indicator counts, derived indicators, P0-9 mappings."""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db"

def main():
    if not os.path.exists(DB_PATH):
        print("DB not found: %s" % DB_PATH)
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    cur = conn.cursor()
    
    # 1. Total rows
    cur.execute("SELECT COUNT(*) FROM series_cache")
    total_rows = cur.fetchone()[0]
    print("[1] Total rows in series_cache: %d" % total_rows)
    
    # 2. Distinct indicator IDs
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    distinct_inds = cur.fetchone()[0]
    print("[2] Distinct indicator IDs: %d" % distinct_inds)
    
    # 3. Indicators with 'derived' source
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source='derived'")
    derived_count = cur.fetchone()[0]
    print("[3] Derived source indicators: %d" % derived_count)
    
    # 4. Indicators with source != 'derived'
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source != 'derived' OR source IS NULL")
    non_derived_count = cur.fetchone()[0]
    print("[4] Non-derived indicators: %d" % non_derived_count)
    
    # 5. P0-9 mapping check
    cur.execute("SELECT indicator_id, COUNT(*) as cnt FROM series_cache GROUP BY indicator_id HAVING COUNT(*) > 0 ORDER BY indicator_id")
    all_indicators = [row[0] for row in cur.fetchall()]
    
    # DSHE meta_chart indicators (109)
    DSHE_META_CHART_109 = [
        "AL_IMPORT_EXPORT_DATA", "AL_SOCIAL_INVENTORY", "AL_SUPPLY_CONSUMPTION_BALANCE",
        "AL_TAX_EXPORT_REBATE", "COMEX_AL", "COMEX_NI", "COMEX_PB", "COMEX_SN", "COMEX_ZN",
        "CU_BALANCE_SHEET", "CU_FG_IMPORT_EXPORT", "CU_FG_SOCIAL_INVENTORY",
        "CU_FG_SUPPLY_CONSUMPTION_BALANCE", "CU_FG_TAX_EXPORT_REBATE",
        "CU_HOLDER_POSITION", "CU_INVENTORY", "CU_LME_SPOT_PREMIUM",
        "CU_LME_TAX_EXPORT_REBATE", "CU_LME_STOCK", "CU_LME_TRIPLE_ROLL",
        "CU_PRECIOUS_METAL", "CU_SCM_SUPPLY_CONSUMPTION_BALANCE",
        "CU_SOCIAL_INVENTORY", "CU_SUPPLY_CONSUMPTION_BALANCE",
        "CU_TAX_EXPORT_REBATE", "CU_TAX_IMPORT", "LC_FU00015030", "LC_HOLD_OPEN",
        "LC_HOLD_OPEN_POSITION", "LC_POSITION_HOLDER",
        "LME_AL", "LME_CU", "LME_NI", "LME_NI_LME", "LME_PB", "LME_SN", "LME_ZN",
        "NI_CONSUMPTION", "NI_FG_IMPORT_EXPORT", "NI_FG_TAX_EXPORT_REBATE",
        "NI_HOLDER_POSITION", "NI_INVENTORY", "NI_LME_TAX_EXPORT_REBATE",
        "NI_SOCIAL_INVENTORY", "NI_SUPPLY_CONSUMPTION_BALANCE",
        "NI_TAX_EXPORT_REBATE", "NI_TAX_IMPORT", "PB_CATHODE_INVENTORY",
        "PB_DIECASTING_INVENTORY", "PB_IMPORT_EXPORT_DATA",
        "PB_INVENTORY", "PB_RECYCLING_INVENTORY", "PB_REFINING_INVENTORY",
        "PB_SUPPLY_CONSUMPTION_BALANCE", "PB_TAX_EXPORT_REBATE",
        "PB_TAX_IMPORT", "PB_TOP20_LONG", "PB_TOP20_SHORT",
        "SI_INVENTORY", "SI_PRICE", "SN_LME_CASH_SETTLEMENT",
        "SN_LME_CASH_PREMIUM", "SN_LME_TAX_EXPORT_REBATE",
        "SN_SOCIAL_INVENTORY", "SN_SUPPLY_CONSUMPTION_BALANCE",
        "SN_TAX_EXPORT_REBATE", "SN_TAX_IMPORT",
        "SPOT_A", "SPOT_A_PREMIUM", "SPOT_B", "SPOT_B_PREMIUM",
        "SPOT_CU", "SPOT_CU_PREMIUM", "SPOT_IN", "SPOT_IN_PREMIUM",
        "SPOT_IS", "SPOT_J", "SPOT_J_PREMIUM", "SPOT_K",
        "SPOT_K_PREMIUM", "SPOT_L", "SPOT_L_PREMIUM",
        "SPOT_M", "SPOT_M_PREMIUM", "SPOT_N", "SPOT_N_PREMIUM",
        "SPOT_O", "SPOT_O_PREMIUM", "SPOT_P", "SPOT_P_PREMIUM",
        "SPOT_Q", "SPOT_Q_PREMIUM", "SPOT_R", "SPOT_R_PREMIUM",
        "SPOT_S", "SPOT_S_PREMIUM", "SPOT_T", "SPOT_T_PREMIUM",
        "SPOT_U", "SPOT_U_PREMIUM", "SPOT_V", "SPOT_V_PREMIUM",
        "SPOT_W", "SPOT_W_PREMIUM", "SPOT_X", "SPOT_X_PREMIUM",
        "SPOT_Y", "SPOT_Y_PREMIUM", "SPOT_Z", "SPOT_Z_PREMIUM",
        "ZN_IMPORT_EXPORT_DATA", "ZN_INVENTORY", "ZN_SOCIAL_INVENTORY",
        "ZN_SUPPLY_CONSUMPTION_BALANCE", "ZN_TAX_EXPORT_REBATE",
        "ZN_TAX_IMPORT"
    ]
    
    db_set = set(all_indicators)
    meta_set = set(DSHE_META_CHART_109)
    intersection = meta_set & db_set
    missing = meta_set - db_set
    orphan = db_set - meta_set
    
    print("\n[5] P0-9 Audit:")
    print("    DSHE meta_chart indicators: %d" % len(meta_set))
    print("    DB distinct mapped IDs: %d" % len(db_set))
    print("    Real intersection: %d" % len(intersection))
    print("    Missing from DB: %d" % len(missing))
    if missing:
        print("      Missing: %s" % sorted(missing))
    print("    Orphan (DB only): %d" % len(orphan))
    coverage = len(intersection) / len(meta_set) * 100 if meta_set else 0
    print("    Coverage: %.4f%%" % coverage)
    
    # 6. Derived indicator details (source='derived')
    print("\n[6] Derived Indicators (source='derived'):")
    cur.execute("SELECT indicator_id, COUNT(*) as cnt, MIN(date), MAX(date) FROM series_cache WHERE source='derived' GROUP BY indicator_id ORDER BY indicator_id")
    derived_rows = cur.fetchall()
    for row in derived_rows:
        print("    %s: %d rows, range [%s ~ %s]" % (row[0], row[1], row[2], row[3]))
    
    # 7. All indicators summary by prefix
    print("\n[7] Indicators by prefix:")
    prefix_map = {}
    for ind in all_indicators:
        prefix = ind.split('_')[0] if '_' in ind else ind
        if prefix not in prefix_map:
            prefix_map[prefix] = []
        prefix_map[prefix].append(ind)
    for prefix in sorted(prefix_map.keys()):
        print("    %s: %d indicators" % (prefix, len(prefix_map[prefix])))
    
    # 8. Data point distribution
    print("\n[8] Data point distribution:")
    cur.execute("SELECT MIN(date), MAX(date) FROM series_cache")
    row = cur.fetchone()
    print("    Date range: %s ~ %s" % (row[0], row[1]))
    cur.execute("SELECT COUNT(DISTINCT date) FROM series_cache")
    distinct_dates = cur.fetchone()[0]
    print("    Distinct dates: %d" % distinct_dates)
    
    conn.close()
    print("\n[Done] Check completed at %s" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

if __name__ == "__main__":
    main()
