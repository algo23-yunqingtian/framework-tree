#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache_coverage_calc.py — V88 Phase03 P0-R0 Namespace Mapping & Cache Importer Coverage Calculator
===================================================================================================
TASK_ID: V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER
AGENT: DSHE
BRANCH: feature/v88-g1
PURPOSE: Calculate real data coverage rate against DSHE meta_chart indicator definitions.
         Output coverage report that can drive D7 gate decisions.

Coverage Definition:
  An indicator is "covered" if it has at least 1 record in api_cache.db with source='real'.
  Coverage rate = (covered indicators) / (total DSHE indicators) × 100%

Gate Thresholds:
  P1 (Gate D-7 Phase 1): ≥60% coverage
  P3 (Gate D-7 Phase 3): ≥95% coverage
  P0 (prototype, current): ≥60% threshold

CLI:
  python cache_coverage_calc.py [--db /path/to/api_cache.db] [--output-dir /path/to/output/] [--threshold 60.0]

Constraints:
  - ONLY Python standard library + PyYAML (sqlite3, json, os, sys, yaml, argparse, pathlib, datetime)
  - NO pandas, numpy, or other external dependencies
  - Handles empty database gracefully (report 0% coverage)
  - Handles missing tables gracefully

Outputs:
  1. Console output with coverage summary
  2. JSON report: coverage_report.json
  3. Markdown report: v88_phase03_p0_coverage_report.md
"""

import argparse
import json
import os
import sqlite3
import sys
import yaml
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants & Paths
# ---------------------------------------------------------------------------

TASK_ID = "V88_PHASE03_P0_R0_NAME_MAPPING_AND_CACHE_IMPORTER"
SCHEMA_VERSION = "v88-p0.0.1"
GATE_PHASE = "P0"
GATE_THRESHOLD_PCT = 60.0

SCRIPT_DIR = Path(__file__).resolve().parent
# Script is at: framework-tree/analysis/e2e_output/v88/phase03/p0/scripts/
# framework-tree is 6 levels up from scripts/
FRAMEWORK_TREE = SCRIPT_DIR.parent.parent.parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent  # phase03/p0/
DEFAULT_DB_PATH = FRAMEWORK_TREE / "scripts" / "api_cache.db"
META_CHART_YAML_PATH = (
    FRAMEWORK_TREE
    / "analysis"
    / "e2e_output"
    / "v88"
    / "backlog"
    / "framework_tree_meta_chart.yaml"
)

# ---------------------------------------------------------------------------
# DSHE → DSHB Indicator Mapping
# Keys: DSHE indicator_id (from meta_chart.yaml)
# Values: DSHB metric code (stored in api_cache.db indicator_cache.metric)
#         None means no mapping exists
# ---------------------------------------------------------------------------

INDICATOR_MAPPING = {
    # CU (20 indicators)
    "CU_FU00014941": "cu_21_close_front",
    "CU_HOLD_OPEN": "cu_21_openinterest",
    "CU_LONG_SHORT_RATIO": "cu_21_openinterest_longshort",
    "CU_SPOT_PREMIUM": "cu_22_premium",
    "CU_BASIS": "cu_21_basis",
    "LME_CU": "cu_23_lme_close",
    "COMEX_CU": "cu_23_comex_close",
    "CU_MONTH_SPREAD": "cu_24_openinterest_volume",
    "CU_TERM_STRUCTURE": None,  # no mapping
    "CU_PRICE_PERCENTILE": "cu_25_profit_percentile",
    "CU_SMELTING_PROFIT": "cu_25_profit",
    "CU_TOP20_LONG": "cu_26_openinterest_top20_front",
    "CU_TOP20_SHORT": "cu_26_openinterest",
    "CU_FU00014935": "cu_41_output",
    "FU00014813": "cu_23_inv",
    "CU_WARRANT_INVENTORY": "cu_42_warrant_reg",
    "CU_SOCIAL_INV": "cu_43_social_stock",
    "CU_UTILIZATION": "cu_321_util_capacity_util",
    "CU_COST_PERCENTILE": "cu_25_tc_conc",
    "CU_BALANCE_SHEET": None,
    # AL (13 indicators)
    "AL_FU00014934": "al_00_close_front",
    "AL_HOLD_OPEN": "al_00_openinterest_front",
    "AL_LONG_SHORT_RATIO": None,
    "AL_SPOT_PREMIUM": "al_00_premium",
    "AL_BASIS": "al_00_basis",
    "LME_AL": "al_00_lme_close",
    "COMEX_AL": None,
    "AL_MONTH_SPREAD": "al_24_lme_spread",
    "AL_TERM_STRUCTURE": None,
    "AL_PRICE_PERCENTILE": "al_00_cost_percentile",
    "AL_SMELTING_PROFIT": "al_25_profit",
    "AL_TOP20_LONG": "al_26_long_top20",
    "AL_TOP20_SHORT": "al_26_short_top20",
    # PB (13 indicators)
    "PB_FU00014946": "j21_close",
    "PB_HOLD_OPEN": "j21_oi",
    "PB_LONG_SHORT_RATIO": None,
    "PB_SPOT_PREMIUM": "j22_spot",
    "PB_BASIS": "j22_premium",
    "LME_PB": "j23_lme_cash",
    "COMEX_PB": None,
    "PB_MONTH_SPREAD": "j24_spread_m",
    "PB_TERM_STRUCTURE": "j24_spread_s",
    "PB_PRICE_PERCENTILE": None,
    "PB_SMELTING_PROFIT": "j25_smelt_cost",
    "PB_TOP20_LONG": None,
    "PB_TOP20_SHORT": None,
    # ZN (13 indicators)
    "ZN_FU00014950": "zn_21_close_front",
    "ZN_HOLD_OPEN": "zn_21_openinterest",
    "ZN_LONG_SHORT_RATIO": "zn_21_openinterest_2",
    "ZN_SPOT_PREMIUM": "zn_21_premium",
    "ZN_BASIS": "zn_21_basis",
    "LME_ZN": "zn_23_lme_close",
    "COMEX_ZN": "zn_23_comex",
    "ZN_MONTH_SPREAD": "zn_24_term_struct",
    "ZN_TERM_STRUCTURE": None,
    "ZN_PRICE_PERCENTILE": "zn_25_profit_percentile",
    "ZN_SMELTING_PROFIT": "zn_25_profit",
    "ZN_TOP20_LONG": "zn_26_openinterest_top20",
    "ZN_TOP20_SHORT": "zn_26_openinterest",
    # NI (13 indicators)
    "NI_FU00014982": "ni_21_close_front",
    "NI_HOLD_OPEN": "ni_21_openinterest_front",
    "NI_LONG_SHORT_RATIO": "ni_21_percentile_openinterest",
    "NI_SPOT_PREMIUM": "ni_21_premium",
    "NI_BASIS": "ni_22_basis",
    "LME_NI": "ni_21_lme_price",
    "COMEX_NI": None,
    "NI_MONTH_SPREAD": "ni_24_near_price",
    "NI_TERM_STRUCTURE": None,
    "NI_PRICE_PERCENTILE": "ni_25_percentile_price",
    "NI_SMELTING_PROFIT": "ni_25_profit",
    "NI_TOP20_LONG": "ni_26_openinterest_top20_front",
    "NI_TOP20_SHORT": "ni_26_openinterest_top20_front_2",
    # SN (13 indicators)
    "SN_FU00014952": "sn_21_close_front",
    "SN_HOLD_OPEN": "sn_21_openinterest",
    "SN_LONG_SHORT_RATIO": "sn_21_openinterest_3",
    "SN_SPOT_PREMIUM": "sn_21_premium",
    "SN_BASIS": "sn_21_basis",
    "LME_SN": "sn_23_lme_close",
    "COMEX_SN": None,
    "SN_MONTH_SPREAD": "sn_22_premium",
    "SN_TERM_STRUCTURE": None,
    "SN_PRICE_PERCENTILE": "sn_71_cost_percentile",
    "SN_SMELTING_PROFIT": "sn_72_tc",
    "SN_TOP20_LONG": "sn_26_openinterest_top20",
    "SN_TOP20_SHORT": "sn_26_openinterest_top20_2",
    # LI/LC (13 indicators)
    "LC_FU00015030": "li_21_close_front",
    "LC_HOLD_OPEN": "li_21_openinterest",
    "LC_LONG_SHORT_RATIO": "li_21_openinterest_longshort",
    "LC_SPOT_PREMIUM": "li_21_premium",
    "LC_BASIS": "li_21_basis",
    "LME_LC": "li_21_close",
    "SPOT_LICAR": "li_22_premium",
    "LC_MONTH_SPREAD": "li_24_close_near",
    "LC_TERM_STRUCTURE": None,
    "LC_PRICE_PERCENTILE": None,
    "LC_SMELTING_PROFIT": "li_25_profit",
    "LC_TOP20_LONG": "li_26_openinterest_top20",
    "LC_TOP20_SHORT": "li_26_openinterest_top20_2",
    # SI (13 indicators)
    "SI_FU00015015": "si_21_close_front_industrial_si",
    "SI_HOLD_OPEN": "si_21_openinterest",
    "SI_LONG_SHORT_RATIO": "si_21_openinterest_longshort_indus",
    "SI_SPOT_PREMIUM": "si_21_warrant_industrial_si",
    "SI_BASIS": "si_21_basis_industrial_si",
    "LME_SI": "si_25_close_front_polysilicon",
    "SPOT_IS": "si_24_spot",
    "SI_MONTH_SPREAD": "si_23_close",
    "SI_TERM_STRUCTURE": None,
    "SI_PRICE_PERCENTILE": "si_25_profit_percentile_industrial",
    "SI_SMELTING_PROFIT": "si_25_profit",
    "SI_TOP20_LONG": "si_26_openinterest_top20",
    "SI_TOP20_SHORT": "si_26_openinterest_top20_2",
}

# Commodity code mapping (YAML commodity key → DB indicator_cache.code)
# YAML charts use lowercase commodity (cu, al, pb, zn, ni, sn, li, si)
# DB uses uppercase codes (CU, AL, PB, ZN, NI, SN, LC, SI)
COMMODITY_DB_CODE = {
    "cu": "CU",
    "al": "AL",
    "pb": "PB",
    "zn": "ZN",
    "ni": "NI",
    "sn": "SN",
    "li": "LC",
    "si": "SI",
}

# Commodity label mapping for display
COMMODITY_LABELS = {
    "cu": "铜(CU)",
    "al": "铝(AL)",
    "pb": "铅(PB)",
    "zn": "锌(ZN)",
    "ni": "镍(NI)",
    "sn": "锡(SN)",
    "li": "锂(LC)",
    "si": "硅(SI)",
}

# Commodity order for consistent output
COMMODITY_ORDER = ["cu", "al", "pb", "zn", "ni", "sn", "li", "si"]


# ---------------------------------------------------------------------------
# YAML Loading
# ---------------------------------------------------------------------------

def load_meta_chart(yaml_path):
    """Load framework_tree_meta_chart.yaml and extract indicator metadata.

    Returns:
        dict: {indicator_id: {chart_id, commodity, indicator_name, chart_title}}
    """
    if not yaml_path.exists():
        print(f"[WARN] YAML file not found: {yaml_path}")
        return {}

    with open(str(yaml_path), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    charts = data.get("charts", [])
    indicator_meta = {}

    for chart in charts:
        chart_id = chart.get("chart_id", "")
        commodity = chart.get("commodity", "")
        chart_title = chart.get("title", "")

        for ind in chart.get("indicators", []):
            iid = ind.get("indicator_id")
            name = ind.get("indicator_name", "")
            if iid:
                indicator_meta[iid] = {
                    "chart_id": chart_id,
                    "commodity": commodity,
                    "indicator_name": name,
                    "chart_title": chart_title,
                }

    return indicator_meta


def get_unique_indicator_ids(yaml_path):
    """Extract sorted unique indicator_ids from YAML charts."""
    meta = load_meta_chart(yaml_path)
    return sorted(meta.keys()), meta


# ---------------------------------------------------------------------------
# Database Access
# ---------------------------------------------------------------------------

def detect_db_schema(db_path):
    """Detect available tables in api_cache.db.

    Returns:
        dict: {"exists": bool, "size_bytes": int, "tables": list, "has_series_cache": bool, "has_indicator_cache": bool}
    """
    info = {
        "exists": False,
        "size_bytes": 0,
        "tables": [],
        "has_series_cache": False,
        "has_indicator_cache": False,
    }

    if not db_path.exists():
        return info

    info["exists"] = True
    info["size_bytes"] = db_path.stat().st_size

    if info["size_bytes"] == 0:
        return info

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        info["tables"] = tables
        info["has_series_cache"] = "series_cache" in tables
        info["has_indicator_cache"] = "indicator_cache" in tables
        conn.close()
    except sqlite3.DatabaseError as e:
        info["error"] = str(e)
    except Exception as e:
        info["error"] = str(e)

    return info


def _extract_commodity_from_metric_code(metric_code):
    """Extract commodity key from DSHB metric code prefix.

    E.g.: 'cu_21_close_front' → 'cu', 'j21_close' → 'pb', 'li_21_close' → 'li'
    """
    if not metric_code:
        return None
    mc = metric_code.lower()
    # Check longest prefixes first
    for prefix in ["si_", "li_", "ni_", "zn_", "cu_", "al_", "sn_"]:
        if mc.startswith(prefix):
            return prefix.rstrip("_")
    if mc.startswith("j") and not mc.startswith("j2") is False:
        # j prefix (铅/lead) - j21, j22, j23, j24, j25, j26 etc.
        return "pb"
    if mc.startswith("j"):
        return "pb"
    # Check for numeric-only patterns (j21, j22, etc.)
    return None


def get_indicator_coverage_from_series_cache(conn, indicator_id):
    """Check coverage from series_cache table (task-described schema).

    Returns:
        dict: {"record_count": int, "has_real_data": bool, "date_range": dict|None}
    """
    cursor = conn.cursor()

    # Check total records for this indicator
    cursor.execute(
        "SELECT COUNT(*) FROM series_cache WHERE indicator_id=?",
        (indicator_id,),
    )
    total_count = cursor.fetchone()[0]

    # Check for real data (source='real')
    cursor.execute(
        "SELECT COUNT(*) FROM series_cache WHERE indicator_id=? AND source='real'",
        (indicator_id,),
    )
    real_count = cursor.fetchone()[0]

    # Get date range for real data
    date_range = None
    if real_count > 0:
        cursor.execute(
            "SELECT MIN(date), MAX(date) FROM series_cache "
            "WHERE indicator_id=? AND source='real'",
            (indicator_id,),
        )
        row = cursor.fetchone()
        if row and row[0] and row[1]:
            date_range = {"start": row[0], "end": row[1]}

    return {
        "record_count": real_count,
        "has_real_data": real_count > 0,
        "total_records": total_count,
        "date_range": date_range,
    }


def get_indicator_coverage_from_indicator_cache(conn, commodity_code, metric_code):
    """Check coverage from indicator_cache table (actual DB schema).

    Queries the indicator_cache table for code+metric, parses data_json
    to check for real points data.

    Returns:
        dict: {"record_count": int, "has_real_data": bool, "date_range": dict|None, "has_row": bool}
    """
    cursor = conn.cursor()

    cursor.execute(
        "SELECT data_json FROM indicator_cache WHERE code=? AND metric=?",
        (commodity_code, metric_code),
    )
    row = cursor.fetchone()

    if not row or not row[0]:
        return {
            "record_count": 0,
            "has_real_data": False,
            "has_row": False,
            "date_range": None,
        }

    try:
        data = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return {
            "record_count": 0,
            "has_real_data": False,
            "has_row": True,
            "date_range": None,
        }

    points = data.get("points", [])
    if not isinstance(points, list):
        points = []

    # Filter for points with non-null values
    valid_points = [
        p for p in points
        if isinstance(p, dict) and p.get("date") and p.get("value") is not None
    ]

    # Check source field (if present in data_json)
    source = data.get("source", "")
    has_real_source = (
        isinstance(source, str) and source.lower() in ("real", "zhiji", "ths", "iwencai")
    )

    # Determine coverage: need at least 1 valid point
    has_real_data = len(valid_points) > 0

    # Calculate date range
    date_range = None
    if valid_points:
        dates = [p["date"] for p in valid_points if isinstance(p.get("date"), str)]
        if dates:
            dates_sorted = sorted(dates)
            date_range = {"start": dates_sorted[0], "end": dates_sorted[-1]}

    return {
        "record_count": len(valid_points),
        "has_real_data": has_real_data,
        "has_row": True,
        "date_range": date_range,
        "source": source,
    }


def check_indicator_coverage(db_path, indicator_id, dshb_metric_code, commodity_key):
    """Check if an indicator has real data in the database.

    Tries both series_cache and indicator_cache table schemas.

    Returns:
        dict: {"has_mapping": bool, "record_count": int, "has_real_data": bool,
               "date_range": dict|None, "db_used": str, "gap_reason": str|None}
    """
    result = {
        "has_mapping": dshb_metric_code is not None,
        "record_count": 0,
        "has_real_data": False,
        "date_range": None,
        "db_used": "none",
        "gap_reason": None,
    }

    if not dshb_metric_code:
        result["gap_reason"] = "no_mapping"
        return result

    if not db_path.exists():
        result["gap_reason"] = "db_missing"
        return result

    db_size = db_path.stat().st_size
    if db_size == 0:
        result["gap_reason"] = "db_empty"
        return result

    try:
        conn = sqlite3.connect(str(db_path))
    except sqlite3.DatabaseError:
        result["gap_reason"] = "db_error"
        return result

    try:
        cursor = conn.cursor()

        # Check available tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        # Strategy 1: Try series_cache table (task-described schema)
        if "series_cache" in tables:
            cov = get_indicator_coverage_from_series_cache(conn, indicator_id)
            result.update(cov)
            result["db_used"] = "series_cache"
            if not cov["has_real_data"]:
                if cov["total_records"] > 0:
                    result["gap_reason"] = "simulated_only"
                else:
                    result["gap_reason"] = "no_data"
            return result

        # Strategy 2: Use indicator_cache table (actual DB schema)
        if "indicator_cache" in tables:
            # Determine DB commodity code
            db_commodity = COMMODITY_DB_CODE.get(commodity_key, "")

            cov = get_indicator_coverage_from_indicator_cache(
                conn, db_commodity, dshb_metric_code
            )
            result.update(cov)
            result["db_used"] = "indicator_cache"
            if not cov["has_real_data"]:
                if cov["has_row"]:
                    result["gap_reason"] = "simulated_only"
                else:
                    result["gap_reason"] = "no_data"
            return result

        # No known tables
        result["gap_reason"] = "no_matching_table"
        result["db_used"] = "unknown"

    except sqlite3.DatabaseError as e:
        result["gap_reason"] = f"db_error: {e}"
        result["db_used"] = "error"

    finally:
        conn.close()

    return result


# ---------------------------------------------------------------------------
# Coverage Calculation
# ---------------------------------------------------------------------------

def calculate_coverage(db_path, yaml_path, threshold_pct):
    """Calculate overall, per-commodity, and per-indicator coverage.

    Returns:
        dict: Complete coverage report data structure.
    """
    timestamp = datetime.now().isoformat()

    # 1. Load indicator metadata from YAML
    indicator_ids, indicator_meta = get_unique_indicator_ids(yaml_path)
    total_indicators = len(indicator_ids)

    # 2. Detect DB schema
    db_info = detect_db_schema(db_path)

    # 3. Check coverage for each indicator
    per_indicator = []
    gaps = {"no_mapping": [], "no_data": [], "simulated_only": [], "other": []}

    # Track per-commodity coverage
    commodity_coverage = {}
    for comm in COMMODITY_ORDER:
        commodity_coverage[comm] = {"total": 0, "covered": 0, "rate_pct": 0.0}

    covered_count = 0

    for iid in indicator_ids:
        # Get metadata from YAML
        meta = indicator_meta.get(iid, {})
        commodity = meta.get("commodity", "")
        chart_id = meta.get("chart_id", "")
        indicator_name = meta.get("indicator_name", "")

        # Get mapping
        dshb_metric = INDICATOR_MAPPING.get(iid)
        has_mapping = dshb_metric is not None

        # Check DB coverage
        cov = check_indicator_coverage(
            db_path, iid, dshb_metric, commodity
        )

        is_covered = cov["has_real_data"]
        if is_covered:
            covered_count += 1

        # Build per-indicator record
        record = {
            "meta_chart_id": iid,
            "chart_id": chart_id,
            "commodity": commodity,
            "indicator_name": indicator_name,
            "mapped_to": dshb_metric,
            "has_mapping": has_mapping,
            "record_count": cov["record_count"],
            "has_real_data": cov["has_real_data"],
            "coverage_status": "covered" if is_covered else "uncovered",
            "date_range": cov["date_range"],
            "db_used": cov["db_used"],
        }
        per_indicator.append(record)

        # Track commodity coverage
        if commodity in commodity_coverage:
            commodity_coverage[commodity]["total"] += 1
            if is_covered:
                commodity_coverage[commodity]["covered"] += 1

        # Track gaps
        gap_reason = cov.get("gap_reason", "no_data")
        if gap_reason == "no_mapping":
            gaps["no_mapping"].append({
                "indicator_id": iid,
                "commodity": commodity,
                "chart_id": chart_id,
                "indicator_name": indicator_name,
                "reason": "No DSHB metric mapping defined",
            })
        elif gap_reason in ("no_data", "db_missing", "db_empty", "db_error", "no_matching_table"):
            gaps["no_data"].append({
                "indicator_id": iid,
                "commodity": commodity,
                "chart_id": chart_id,
                "indicator_name": indicator_name,
                "mapped_to": dshb_metric,
                "reason": f"Mapped metric not found in database (gap: {gap_reason})",
            })
        elif gap_reason == "simulated_only":
            gaps["simulated_only"].append({
                "indicator_id": iid,
                "commodity": commodity,
                "chart_id": chart_id,
                "indicator_name": indicator_name,
                "mapped_to": dshb_metric,
                "reason": "Mapped metric exists but has no real data points",
            })
        elif gap_reason:
            gaps["other"].append({
                "indicator_id": iid,
                "commodity": commodity,
                "chart_id": chart_id,
                "indicator_name": indicator_name,
                "reason": f"Gap: {gap_reason}",
            })

    # 4. Calculate coverage rates
    coverage_rate = (covered_count / total_indicators * 100.0) if total_indicators > 0 else 0.0
    gate_status = "PASS" if coverage_rate >= threshold_pct else "FAIL"

    for comm in COMMODITY_ORDER:
        tc = commodity_coverage[comm]["total"]
        cc = commodity_coverage[comm]["covered"]
        commodity_coverage[comm]["rate_pct"] = (cc / tc * 100.0) if tc > 0 else 0.0

    # 5. Build recommendations
    recommendations = []
    if coverage_rate < threshold_pct:
        recommendations.append(
            f"Overall coverage ({coverage_rate:.1f}%) is below P0 gate threshold ({threshold_pct:.0f}%). "
            f"Need to import {total_indicators - covered_count} more indicators to reach gate."
        )
    if gaps["no_mapping"]:
        recommendations.append(
            f"{len(gaps['no_mapping'])} indicators have no DSHB metric mapping. "
            f"Update INDICATOR_MAPPING in cache_coverage_calc.py to add mappings."
        )
    if gaps["no_data"]:
        recommendations.append(
            f"{len(gaps['no_data'])} mapped indicators are missing from api_cache.db. "
            f"Run refresh_cache.py or db_import_jsonl.py to import data."
        )
    if gaps["simulated_only"]:
        recommendations.append(
            f"{len(gaps['simulated_only'])} indicators have cache entries but no real data points. "
            f"Re-fetch from source with source='real' data."
        )
    if not recommendations:
        recommendations.append(
            f"Coverage {coverage_rate:.1f}% meets P0 gate threshold ({threshold_pct:.0f}%). "
            f"All indicators with mappings have real data in cache."
        )

    # 6. Build final report
    report = {
        "task_id": TASK_ID,
        "schema_version": SCHEMA_VERSION,
        "timestamp": timestamp,
        "db_path": str(db_path.relative_to(FRAMEWORK_TREE)) if db_path.is_absolute() and FRAMEWORK_TREE in db_path.parents else str(db_path),
        "db_exists": db_info["exists"],
        "db_size_bytes": db_info["size_bytes"],
        "db_tables": db_info["tables"],
        "yaml_path": str(yaml_path.relative_to(FRAMEWORK_TREE)) if yaml_path.is_absolute() and FRAMEWORK_TREE in yaml_path.parents else str(yaml_path),
        "overall": {
            "total_indicators": total_indicators,
            "covered": covered_count,
            "coverage_rate_pct": round(coverage_rate, 2),
            "gate_threshold_pct": threshold_pct,
            "gate_status": gate_status,
            "gate_phase": GATE_PHASE,
        },
        "per_commodity": commodity_coverage,
        "per_indicator": per_indicator,
        "gaps": gaps,
        "recommendations": recommendations,
    }

    return report


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_json_report(report, output_dir):
    """Write JSON coverage report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "coverage_report.json"
    with open(str(json_path), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[JSON] Report written: {json_path}")
    return json_path


def generate_markdown_report(report, output_dir):
    """Generate Markdown coverage report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "v88_phase03_p0_coverage_report.md"

    overall = report["overall"]
    coverage_rate = overall["coverage_rate_pct"]
    total = overall["total_indicators"]
    covered = overall["covered"]
    threshold = overall["gate_threshold_pct"]
    gate_status = overall["gate_status"]

    lines = []

    # Header
    lines.append("# V88 Phase03 P0-R0 Coverage Report")
    lines.append("")
    lines.append(f"> **Task ID**: {report['task_id']}")
    lines.append(f"> **Schema**: {report['schema_version']}")
    lines.append(f"> **Generated**: {report['timestamp']}")
    lines.append(f"> **DB Path**: `{report['db_path']}`")
    lines.append(f"> **Gate Phase**: {overall['gate_phase']}")
    lines.append("")

    # Summary
    lines.append("## 1. Overall Coverage Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total DSHE Indicators | {total} |")
    lines.append(f"| Covered (real data) | {covered} |")
    lines.append(f"| Coverage Rate | {coverage_rate:.2f}% |")
    lines.append(f"| Gate Threshold | {threshold:.0f}% |")
    lines.append(f"| Gate Status | **{gate_status}** |")
    lines.append("")

    if gate_status == "PASS":
        lines.append(f"> [PASS] Coverage {coverage_rate:.1f}% >= {threshold:.0f}% threshold")
    else:
        lines.append(f"> [FAIL] Coverage {coverage_rate:.1f}% < {threshold:.0f}% threshold")
    lines.append("")

    # Per-Commodity Coverage
    lines.append("## 2. Per-Commodity Coverage")
    lines.append("")
    lines.append("| Commodity | Total | Covered | Rate | Status |")
    lines.append("|-----------|-------|---------|------|--------|")
    for comm in COMMODITY_ORDER:
        cc = report["per_commodity"].get(comm, {})
        tc = cc.get("total", 0)
        cov = cc.get("covered", 0)
        rate = cc.get("rate_pct", 0.0)
        status = "PASS" if rate >= threshold else ("FAIL" if tc > 0 else "N/A")
        label = COMMODITY_LABELS.get(comm, comm.upper())
        lines.append(f"| {label} | {tc} | {cov} | {rate:.1f}% | {status} |")
    lines.append("")

    # Coverage Progress Bar (text)
    lines.append("### Coverage Progress")
    lines.append("")
    bar_width = 40
    filled = int(bar_width * coverage_rate / 100.0)
    bar = "█" * filled + "░" * (bar_width - filled)
    lines.append(f"```")
    lines.append(f"[{bar}] {coverage_rate:.1f}% / {threshold:.0f}% threshold")
    lines.append(f"```")
    lines.append("")

    # Per-Commodity Bar Chart
    lines.append("### Per-Commodity Bar Chart")
    lines.append("")
    lines.append("```")
    for comm in COMMODITY_ORDER:
        cc = report["per_commodity"].get(comm, {})
        rate = cc.get("rate_pct", 0.0)
        tc = cc.get("total", 0)
        if tc == 0:
            continue
        label = comm.upper()
        bar_str = "█" * int(bar_width * rate / 100.0) + "░" * (bar_width - int(bar_width * rate / 100.0))
        lines.append(f"{label:3s} [{bar_str}] {rate:5.1f}% ({cc.get('covered',0)}/{tc})")
    lines.append("```")
    lines.append("")

    # Gap Analysis
    lines.append("## 3. Gap Analysis")
    lines.append("")

    gap_sections = [
        ("no_mapping", "3.1 No Mapping (DSHE → DSHB mapping missing)"),
        ("no_data", "3.2 No Data (Mapped metric not found in DB)"),
        ("simulated_only", "3.3 Simulated Only (Entry exists but no real points)"),
        ("other", "3.4 Other Gaps"),
    ]

    for gap_key, gap_title in gap_sections:
        gap_items = report["gaps"].get(gap_key, [])
        if not gap_items:
            lines.append(f"### {gap_title}")
            lines.append("")
            lines.append(f"No items in this category. [OK]")
            lines.append("")
            continue

        lines.append(f"### {gap_title}")
        lines.append("")
        lines.append(f"**Count**: {len(gap_items)}")
        lines.append("")
        lines.append("| # | Indicator ID | Commodity | Chart ID | Indicator Name | Mapped To | Reason |")
        lines.append("|---|-------------|-----------|----------|---------------|-----------|--------|")
        for i, item in enumerate(gap_items, 1):
            iid = item.get("indicator_id", "")
            comm = item.get("commodity", "")
            chart_id = item.get("chart_id", "")
            name = item.get("indicator_name", "")
            mapped = item.get("mapped_to", "")
            reason = item.get("reason", "")
            comm_label = COMMODITY_LABELS.get(comm, comm.upper())
            lines.append(f"| {i} | `{iid}` | {comm_label} | `{chart_id}` | {name} | `{mapped or 'N/A'}` | {reason} |")
        lines.append("")

    # Per-Indicator Detail (covered indicators)
    covered_indicators = [r for r in report["per_indicator"] if r["coverage_status"] == "covered"]
    if covered_indicators:
        lines.append("## 4. Covered Indicators Detail")
        lines.append("")
        lines.append(f"**Total covered**: {len(covered_indicators)} / {total}")
        lines.append("")
        lines.append("| # | Indicator ID | Commodity | Chart ID | Records | Date Range |")
        lines.append("|---|-------------|-----------|----------|---------|------------|")
        for i, rec in enumerate(sorted(covered_indicators, key=lambda x: (x["commodity"], x["meta_chart_id"])), 1):
            iid = rec["meta_chart_id"]
            comm = rec["commodity"]
            chart_id = rec["chart_id"]
            count = rec["record_count"]
            dr = rec.get("date_range")
            dr_str = f"{dr['start']} ~ {dr['end']}" if dr else "N/A"
            comm_label = COMMODITY_LABELS.get(comm, comm.upper())
            lines.append(f"| {i} | `{iid}` | {comm_label} | `{chart_id}` | {count} | {dr_str} |")
        lines.append("")

    # Recommendations
    lines.append("## 5. Recommendations")
    lines.append("")
    for i, rec in enumerate(report.get("recommendations", []), 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    # Gate Decision
    lines.append("## 6. Gate Decision")
    lines.append("")
    lines.append(f"| Gate Phase | Threshold | Actual | Status |")
    lines.append(f"|------------|-----------|--------|--------|")
    lines.append(f"| {overall['gate_phase']} | {threshold:.0f}% | {coverage_rate:.2f}% | **{gate_status}** |")
    lines.append("")

    if gate_status == "PASS":
        lines.append(f"> **[PASS] D7 Gate Decision: PASS**")
        lines.append(f">")
        lines.append(f"> Coverage rate {coverage_rate:.1f}% exceeds the P0 threshold of {threshold:.0f}%.")
        lines.append(f"> Proceed to next phase (P1) when ready.")
    else:
        deficit = total - covered
        lines.append(f"> **[FAIL] D7 Gate Decision: FAIL**")
        lines.append(f">")
        lines.append(f"> Coverage rate {coverage_rate:.1f}% is below the P0 threshold of {threshold:.0f}%.")
        lines.append(f"> Need to cover at least {int(total * threshold / 100.0)} indicators to pass.")
        lines.append(f"> Currently {deficit} indicators are uncovered.")
        lines.append(f">")
        lines.append(f"> **Required actions**:")
        lines.append(f"> 1. Run `refresh_cache.py` to import missing real data into api_cache.db")
        if report["gaps"]["no_mapping"]:
            lines.append(f"> 2. Update INDICATOR_MAPPING for {len(report['gaps']['no_mapping'])} unmapped indicators")
        if report["gaps"]["simulated_only"]:
            lines.append(f"> 3. Re-fetch {len(report['gaps']['simulated_only'])} indicators with source='real' data")

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by cache_coverage_calc.py · {report['timestamp']}*")
    lines.append("")

    md_content = "\n".join(lines)
    with open(str(md_path), "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[MD]   Report written: {md_path}")
    return md_path


# ---------------------------------------------------------------------------
# Console Output
# ---------------------------------------------------------------------------

def print_console_summary(report):
    """Print coverage summary to console."""
    overall = report["overall"]
    total = overall["total_indicators"]
    covered = overall["covered"]
    rate = overall["coverage_rate_pct"]
    threshold = overall["gate_threshold_pct"]
    status = overall["gate_status"]

    print()
    print("=" * 72)
    print(f"  V88 Phase03 P0-R0 | Cache Coverage Calculator")
    print(f"  Task: {TASK_ID}")
    print(f"  Time: {report['timestamp']}")
    print("=" * 72)
    print()

    # Overall
    print(f"  Overall Coverage: {covered}/{total} = {rate:.2f}%")
    print(f"  Gate Threshold:  {threshold:.0f}% ({overall['gate_phase']})")
    print(f"  Gate Status:     [{'PASS' if status == 'PASS' else 'FAIL'}]")
    print()

    # DB Info
    print(f"  DB Path:    {report['db_path']}")
    print(f"  DB Exists:  {report['db_exists']}")
    print(f"  DB Size:    {report['db_size_bytes']:,} bytes")
    print(f"  DB Tables:  {', '.join(report['db_tables']) if report['db_tables'] else '(none)'}")
    print()

    # Per-Commodity
    print(f"  {'Commodity':<12} {'Total':>5} {'Cov':>5} {'Rate':>7} {'Status'}")
    print(f"  {'-'*12} {'-'*5} {'-'*5} {'-'*7} {'-'*8}")
    for comm in COMMODITY_ORDER:
        cc = report["per_commodity"].get(comm, {})
        tc = cc.get("total", 0)
        cov = cc.get("covered", 0)
        r = cc.get("rate_pct", 0.0)
        label = COMMODITY_LABELS.get(comm, comm.upper())
        if tc > 0:
            status_str = "PASS" if r >= threshold else "FAIL"
            print(f"  {label:<12} {tc:>5} {cov:>5} {r:>6.1f}% {status_str}")
        else:
            print(f"  {label:<12} {tc:>5} {cov:>5} {'N/A':>7} {'N/A'}")
    print()

    # Gap Summary
    gaps = report["gaps"]
    total_gaps = sum(len(v) for v in gaps.values())
    print(f"  Gap Summary:")
    for key, count in [
        ("no_mapping", gaps["no_mapping"]),
        ("no_data", gaps["no_data"]),
        ("simulated_only", gaps["simulated_only"]),
        ("other", gaps["other"]),
    ]:
        label_map = {
            "no_mapping": "No Mapping (DSHE→DSHB)",
            "no_data": "No Data in DB",
            "simulated_only": "Simulated Only",
            "other": "Other",
        }
        print(f"    {label_map[key]:<28}: {len(count):>3}")
    print(f"    {'TOTAL GAPS':<28}: {total_gaps:>3}")
    print()

    # Recommendations
    print(f"  Recommendations:")
    for i, rec in enumerate(report.get("recommendations", []), 1):
        print(f"    {i}. {rec}")
    print()
    print("=" * 72)
    print()


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P0-R0 Cache Coverage Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cache_coverage_calc.py
  python cache_coverage_calc.py --db /path/to/api_cache.db
  python cache_coverage_calc.py --output-dir /path/to/output/
  python cache_coverage_calc.py --threshold 95.0  # P3 threshold
        """,
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"Path to api_cache.db (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory for reports (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=GATE_THRESHOLD_PCT,
        help=f"Gate threshold percentage (default: {GATE_THRESHOLD_PCT})",
    )
    parser.add_argument(
        "--yaml",
        default=str(META_CHART_YAML_PATH),
        help=f"Path to meta_chart YAML (default: {META_CHART_YAML_PATH})",
    )

    args = parser.parse_args()

    # Ensure UTF-8 stdout (Windows GBK terminal compatibility)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    db_path = Path(args.db)
    output_dir = Path(args.output_dir)
    yaml_path = Path(args.yaml)

    print(f"cache_coverage_calc.py | V88 Phase03 P0-R0")
    print(f"  DB:      {db_path}")
    print(f"  YAML:    {yaml_path}")
    print(f"  Output:  {output_dir}")
    print(f"  Gate:    {GATE_PHASE} >= {args.threshold:.0f}%")
    print()

    # Validate inputs
    if not yaml_path.exists():
        print(f"[ERROR] YAML file not found: {yaml_path}")
        sys.exit(1)

    # Calculate coverage
    report = calculate_coverage(db_path, yaml_path, args.threshold)

    # Print console summary
    print_console_summary(report)

    # Generate reports
    json_path = generate_json_report(report, output_dir)
    md_path = generate_markdown_report(report, output_dir)

    # Final summary
    print(f"  Reports saved to: {output_dir}/")
    print(f"    - coverage_report.json ({json_path.stat().st_size:,} bytes)")
    print(f"    - v88_phase03_p0_coverage_report.md ({md_path.stat().st_size:,} bytes)")
    print()

    # Exit code: 0 = PASS, 1 = FAIL
    exit_code = 0 if report["overall"]["gate_status"] == "PASS" else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
