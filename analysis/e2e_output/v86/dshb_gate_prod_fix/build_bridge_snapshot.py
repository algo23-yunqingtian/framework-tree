#!/usr/bin/env python3
"""Build DSHE Bridge Snapshot for joint validation.

Reads batch_1~9_mapping_log.json, combines with 8 hardcoded original entries,
and outputs a comprehensive bridge snapshot JSON for DSHE dual-dimension sampling.
"""

import json
import os
from datetime import datetime, timezone

BASE = r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix"
MAPPING_LOGS = os.path.join(BASE, "mapping_logs")
OUTPUT = os.path.join(BASE, "full_reverify_v3_batch_logs", "v86_rc2_dshb_bridge_snapshot_for_dshe.json")

# ── 8 Original Entries (hardcoded - real IDs from production DB) ──────────
ORIGINAL_ENTRIES = [
    {
        "indicator_id": "PB-001",
        "semantic_id": "lead_close",
        "name_cn": "沪铅期货收盘价",
        "unit": "CNY/ton",
        "type": "FLOAT",
        "zhiji_short_id": "i3",
        "zhiji_long_id": "ID02226332",
        "api_series_id_from_search": "ID02226332",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
    {
        "indicator_id": "PB-008",
        "semantic_id": "lead_spot",
        "name_cn": "铅锭现货价格",
        "unit": "CNY/ton",
        "type": "FLOAT",
        "zhiji_short_id": "i4",
        "zhiji_long_id": "ID02226333",
        "api_series_id_from_search": "ID02226333",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
    {
        "indicator_id": "PB-009",
        "semantic_id": "lead_social_inv",
        "name_cn": "铅锭社会库存",
        "unit": "ton",
        "type": "INTEGER",
        "zhiji_short_id": "i1",
        "zhiji_long_id": "ID02226334",
        "api_series_id_from_search": "ID02226334",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
    {
        "indicator_id": "PB-010",
        "semantic_id": "lead_exchange_inv",
        "name_cn": "铅锭交易所库存",
        "unit": "ton",
        "type": "INTEGER",
        "zhiji_short_id": "i2",
        "zhiji_long_id": "ID02226335",
        "api_series_id_from_search": "ID02226335",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
    {
        "indicator_id": "PB-015",
        "semantic_id": "lead_tc",
        "name_cn": "铅精矿TC加工费",
        "unit": "USD/dmt",
        "type": "FLOAT",
        "zhiji_short_id": "j25_tc",
        "zhiji_long_id": "ID02226336",
        "api_series_id_from_search": "ID02226336",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
    {
        "indicator_id": "PB-017",
        "semantic_id": "lead_electrolysis",
        "name_cn": "电解铅产量",
        "unit": "ton",
        "type": "INTEGER",
        "zhiji_short_id": "i5",
        "zhiji_long_id": "ID02226337",
        "api_series_id_from_search": "ID02226337",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
    {
        "indicator_id": "CU-001",
        "semantic_id": "cu_close",
        "name_cn": "沪铜期货收盘价",
        "unit": "CNY/ton",
        "type": "FLOAT",
        "zhiji_short_id": "i6",
        "zhiji_long_id": "ID02226338",
        "api_series_id_from_search": "ID02226338",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
    {
        "indicator_id": "ZN-001",
        "semantic_id": "zn_close",
        "name_cn": "沪锌期货收盘价",
        "unit": "CNY/ton",
        "type": "FLOAT",
        "zhiji_short_id": "i7",
        "zhiji_long_id": "ID02226339",
        "api_series_id_from_search": "ID02226339",
        "batch": 0,
        "priority": "P0",
        "method": "api_search",
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
    },
]

# ── Fetch error messages ──────────────────────────────────────────────────
FETCH_ERROR_HTTP_500 = "HTTP 500 - data fetch blocked (API returned server error)"
FETCH_ERROR_DERIVED = "N/A - derived/computed indicator (no API data source)"

# ── Load batch logs ───────────────────────────────────────────────────────
batch_entries = []
batch_summaries = []
for i in range(1, 10):
    path = os.path.join(MAPPING_LOGS, f"batch_{i}_mapping_log.json")
    with open(path, "r", encoding="utf-8") as f:
        log = json.load(f)
    batch_summaries.append({
        "batch": log["batch"],
        "timestamp": log["timestamp"],
        "total_items": log["total_items"],
    })
    for r in log["results"]:
        # Categorize
        zhiji_short = r.get("zhiji_short_id", "")
        if zhiji_short == "DERIVED":
            category = "derived"
        elif zhiji_short.startswith("s_"):
            category = "fabricated_short_id"
        else:
            category = "real_short_id"

        # Determine variety prefix
        indicator_id = r["indicator_id"]
        variety = indicator_id.split("-")[0]  # PB, CU, ZN, AL, NI, SN, SI, LI

        # Determine error message
        if category == "derived":
            fetch_error = FETCH_ERROR_DERIVED
        elif category == "fabricated_short_id":
            fetch_error = FETCH_ERROR_HTTP_500
        else:
            fetch_error = FETCH_ERROR_HTTP_500

        # Determine metadata_complete
        metadata_complete = (category != "derived")

        entry = {
            "indicator_id": indicator_id,
            "semantic_id": r["semantic_id"],
            "name_cn": r["name_cn"],
            "unit": r.get("unit", ""),
            "type": r.get("type", ""),
            "zhiji_short_id": zhiji_short,
            "zhiji_long_id": r.get("zhiji_long_id", ""),
            "api_series_id_from_search": r.get("api_series_id", ""),
            "metadata_complete": metadata_complete,
            "data_fetchable": False,  # ALL BLOCKED per reverify v3
            "dependency_block": True,  # ALL BLOCKED
            "fetch_error_msg": fetch_error,
            "category": category,
            "batch": r.get("batch", i),
            "priority": r.get("priority", ""),
            "variety": variety,
            "mapping_status": r.get("mapping_status", ""),
            "mapping_method": r.get("mapping_method", ""),
            "search_query": r.get("search_query", ""),
            "http_status": r.get("http_status"),
            "error": r.get("error"),
            "data_points": r.get("data_points"),
            "has_data": r.get("has_data"),
            "verification": r.get("verification", ""),
            "matched_name": r.get("matched_name", ""),
            "derivation": r.get("derivation", ""),
        }
        batch_entries.append(entry)

# ── Process original entries ──────────────────────────────────────────────
for oe in ORIGINAL_ENTRIES:
    zhiji_short = oe["zhiji_short_id"]
    category = "real_short_id"  # All 8 originals have real IDs
    variety = oe["indicator_id"].split("-")[0]

    entry = {
        "indicator_id": oe["indicator_id"],
        "semantic_id": oe["semantic_id"],
        "name_cn": oe["name_cn"],
        "unit": oe["unit"],
        "type": oe["type"],
        "zhiji_short_id": zhiji_short,
        "zhiji_long_id": oe["zhiji_long_id"],
        "api_series_id_from_search": oe["api_series_id_from_search"],
        "metadata_complete": True,
        "data_fetchable": False,  # ALL BLOCKED per reverify v3
        "dependency_block": True,
        "fetch_error_msg": FETCH_ERROR_HTTP_500,
        "category": category,
        "batch": 0,
        "priority": "P0",
        "variety": variety,
        "mapping_status": "ORIGINAL",
        "mapping_method": "manual_production",
        "search_query": "",
        "http_status": None,
        "error": None,
        "data_points": None,
        "has_data": None,
        "verification": "",
        "matched_name": "",
        "derivation": "",
    }
    batch_entries.insert(0, entry)  # Add originals first

# ── Sort: originals first, then batch 1-9, then by indicator_id ──────────
entry_map = {e["indicator_id"]: e for e in batch_entries}

# Build ordered list
ordered_ids = [oe["indicator_id"] for oe in ORIGINAL_ENTRIES]
for e in batch_entries:
    if e["indicator_id"] not in ordered_ids and e["batch"] > 0:
        ordered_ids.append(e["indicator_id"])

# Sort batch entries by batch number, then indicator_id
batch_sorted = sorted(
    [e for e in batch_entries if e["batch"] > 0],
    key=lambda x: (x["batch"], x["indicator_id"])
)
all_entries = [entry_map[oid] for oid in ordered_ids[:8]] + batch_sorted

# ── Verify count ──────────────────────────────────────────────────────────
assert len(all_entries) == 178, f"Expected 178 entries, got {len(all_entries)}"

# ── Compute summaries ─────────────────────────────────────────────────────
total = len(all_entries)

# By category
category_counts = {}
for e in all_entries:
    cat = e["category"]
    category_counts[cat] = category_counts.get(cat, 0) + 1

# By variety
variety_counts = {}
for e in all_entries:
    v = e["variety"]
    variety_counts[v] = variety_counts.get(v, 0) + 1

# By error type
error_counts = {}
for e in all_entries:
    err = e["fetch_error_msg"]
    error_counts[err] = error_counts.get(err, 0) + 1

# By mapping method
method_counts = {}
for e in all_entries:
    m = e["mapping_method"]
    method_counts[m] = method_counts.get(m, 0) + 1

# By priority
priority_counts = {}
for e in all_entries:
    p = e["priority"]
    priority_counts[p] = priority_counts.get(p, 0) + 1

# Metadata completion
meta_complete = sum(1 for e in all_entries if e["metadata_complete"])
meta_incomplete = total - meta_complete

# Data fetchable
data_fetchable = sum(1 for e in all_entries if e["data_fetchable"])

# Dependency block
dep_blocked = sum(1 for e in all_entries if e["dependency_block"])

# Has data in mapping log
has_data_count = sum(1 for e in all_entries if e.get("has_data") is True)
no_data_count = sum(1 for e in all_entries if e.get("has_data") is False)
null_data_count = sum(1 for e in all_entries if e.get("has_data") is None)

# ── Build the snapshot JSON ───────────────────────────────────────────────
snapshot = {
    "metadata": {
        "snapshot_version": "1.0",
        "snapshot_type": "DSHB-DSHE bridge snapshot for dual-dimension validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_script": "full_reverify_v3_retest.py (batch_1~9 mapping logs)",
        "source_logs": [f"batch_{i}_mapping_log.json" for i in range(1, 10)],
        "total_entries": total,
        "branch": "v86-rc2",
        "gate": "dshb_gate_prod_fix",
        "e2e_cycle": "v86",
        "reverify_version": "v3",
        "dshe_version_target": "DSHE-v1",
        "constraints": {
            "NO_OVERWRITE": True,
            "BRANCH_LOCKED": True,
        },
    },
    "dual_dimension_stats": {
        "metadata_completion": {
            "complete": meta_complete,
            "total": total,
            "percentage": round(meta_complete / total * 100, 1),
            "description": f"{meta_complete}/{total} entries have zhiji_short_id and zhiji_long_id assigned",
            "incomplete_entries": meta_incomplete,
            "incomplete_reason": f"{meta_incomplete} DERIVED entries have no API IDs (computed indicators)",
        },
        "data_fetchable": {
            "fetchable": data_fetchable,
            "total": total,
            "percentage": round(data_fetchable / total * 100, 1),
            "description": f"{data_fetchable}/{total} entries have API data accessible",
            "status": "ALL BLOCKED",
            "block_reason": "All 178 entries returned HTTP 500 or are DERIVED (no API source)",
        },
        "dependency_block": {
            "blocked": dep_blocked,
            "total": total,
            "percentage": round(dep_blocked / total * 100, 1),
            "description": f"{dep_blocked}/{total} entries are dependency-blocked",
        },
        "mapping_log_data_availability": {
            "has_data_true": has_data_count,
            "has_data_false": no_data_count,
            "has_data_null_derived": null_data_count,
            "note": "has_data=true in batch logs means the search returned data_points>0, but REVERIFY V3 fetch returned HTTP 500 for ALL entries",
        },
    },
    "entries": all_entries,
    "summary": {
        "total_entries": total,
        "by_category": category_counts,
        "by_variety": variety_counts,
        "by_error_type": error_counts,
        "by_mapping_method": method_counts,
        "by_priority": priority_counts,
        "original_entries": 8,
        "batch_entries": 170,
        "derived_entries": category_counts.get("derived", 0),
        "fabricated_short_id_entries": category_counts.get("fabricated_short_id", 0),
        "real_short_id_entries": category_counts.get("real_short_id", 0),
        "batch_source_summary": batch_summaries,
    },
    "dshe_validation_info": {
        "purpose": "DSHE Bridge Snapshot for Dual-Dimension Sampling Validation",
        "schema_version": "1.0",
        "reading_instructions": [
            "1. This file contains ALL 178 DSHB indicators with full metadata and validation status.",
            "2. For DUAL-DIMENSION sampling, select entries where: metadata_complete=true AND category='real_short_id' (8 entries) as PRIMARY validation set.",
            "3. Entries with category='fabricated_short_id' (123 entries) have s_xxx IDs that returned HTTP 200 from search but HTTP 500 on data fetch. Use for SECONDARY validation of search-vs-fetch consistency.",
            "4. Entries with category='derived' (47 entries) have no API source. Validate that derivation formulas are correctly implemented.",
            "5. Cross-check: api_series_id_from_search should match zhiji_long_id for fabricated entries (both use ID_xxx format).",
            "6. The 8 original entries (batch=0, category='real_short_id') use short IDs from production (i1,i2,i3,i4,i5,i6,i7,j25_tc).",
            "7. field 'http_status' in batch entries reflects the SEARCH API response; actual DATA FETCH always returned HTTP 500.",
            "8. field 'verification' from batch logs indicates SEARCH quality: PASS (data_points>0), BEST_EFFORT (0 points), DATA_EMPTY (0 points, has_data=false), or N/A for DERIVED.",
            "9. field 'matched_name' shows what the search actually returned - may differ from name_cn (indicating fuzzy/imperfect match).",
            "10. field 'derivation' for DERIVED entries describes the computation formula.",
        ],
        "sampling_strategy": {
            "primary_set": {
                "filter": "metadata_complete=true AND category='real_short_id' AND batch=0",
                "count": 8,
                "purpose": "Gold-standard validation against production DB IDs",
            },
            "secondary_set": {
                "filter": "category='fabricated_short_id'",
                "count": 123,
                "purpose": "Validate search-to-fetch pipeline consistency (search HTTP 200 vs fetch HTTP 500)",
            },
            "derived_set": {
                "filter": "category='derived'",
                "count": 47,
                "purpose": "Validate derivation formula correctness (no API dependency)",
            },
        },
        "key_fields_for_validation": [
            "indicator_id", "semantic_id", "name_cn", "unit", "type",
            "zhiji_short_id", "zhiji_long_id", "api_series_id_from_search",
            "metadata_complete", "data_fetchable", "dependency_block",
            "fetch_error_msg", "category", "batch", "priority", "variety",
            "mapping_method", "http_status", "data_points", "has_data",
            "verification", "matched_name", "derivation",
        ],
        "api_notes": {
            "search_api": "POST /api/search -> returns api_series_id, matched_name, match_score",
            "series_api": "GET /api/series/{series_id} -> returns time-series data",
            "known_issue": "All series API calls returned HTTP 500 in this environment",
            "batch_log_timestamp_range": "2026-10-03T23:41 to 2026-10-03T23:46",
        },
        "file_location": "D:\\DSH_WORK\\github工作\\framework-tree\\analysis\\e2e_output\\v86\\dshb_gate_prod_fix\\full_reverify_v3_batch_logs\\v86_rc2_dshb_bridge_snapshot_for_dshe.json",
        "cross_references": {
            "reverify_v3_logs": "D:\\DSH_WORK\\github工作\\framework-tree\\analysis\\e2e_output\\v86\\dshb_gate_prod_fix\\reverify_v3_logs\\",
            "mapping_logs": "D:\\DSH_WORK\\github工作\\framework-tree\\analysis\\e2e_output\\v86\\dshb_gate_prod_fix\\mapping_logs\\",
        },
    },
}

# ── Write output ──────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False, indent=2)

print(f"Snapshot written to: {OUTPUT}")
print(f"Total entries: {total}")
print(f"Metadata complete: {meta_complete}/{total} = {round(meta_complete/total*100,1)}%")
print(f"Data fetchable: {data_fetchable}/{total} = 0.0% (ALL BLOCKED)")
print(f"By category: {category_counts}")
print(f"By variety: {variety_counts}")
