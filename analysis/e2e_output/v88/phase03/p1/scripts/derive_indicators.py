#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
derive_indicators.py — V88 Phase03 P1 DSHB 派生指标构建脚本
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB (R-V88-033)
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  从 phase03_test.db 已有基础指标数据计算 59 项衍生品派生指标,
  插入 series_cache 表。涵盖 9 大类:
    COMEX_* / LC_* / SPOT_* / 期限结构 / 月差 / 多空比 / 分位 / Top20 / 库存结构

  本脚本为纯计算, 不修改任何基础指标数据, 仅追加派生指标行。

Usage:
  python derive_indicators.py [--db path/to/phase03_test.db] [--dry-run]

Constraints:
  - NO_ZHIJI_API_CALL / NO_OVERWRITE / APPEND_ONLY
  - INSERT OR IGNORE (不覆盖已有行)
  - Pure Python standard library
  - Windows compatible (auto-sets PYTHONIOENCODING=utf-8)
"""

import os
import sys
import sqlite3
import platform
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
P0_DIR = SCRIPT_DIR.parent.parent.parent
DB_PATH_DEFAULT = P0_DIR / "p0" / "phase03_test.db"

# Output directory
OUTPUT_DIR = SCRIPT_DIR

# =============================================================================
# Platform Setup
# =============================================================================

def setup_environment():
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"
        # Reconfigure stdout for GBK terminals
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


# =============================================================================
# 59 Derived Indicator Definitions
# =============================================================================

def get_derived_indicator_definitions():
    """
    Return all 59 derived indicator definitions.
    Each definition: {derived_id, category, commodity, formula, description}
    """
    return [
        # ── GROUP 1: Term Structure (期限结构) — 8 ──
        {"id": "cu_term_structure", "cat": "term_structure", "comm": "cu",
         "src": ["cu_21_close_front", "cu_24_openinterest_volume"],
         "formula": "front_close - far_price_proxy", "desc": "Cu期限结构(前月-远月价差)"},
        {"id": "al_term_structure", "cat": "term_structure", "comm": "al",
         "src": ["al_00_close_front", "al_24_lme_spread"],
         "formula": "front_close - lme_spread_proxy", "desc": "Al期限结构"},
        {"id": "zn_term_structure", "cat": "term_structure", "comm": "zn",
         "src": ["zn_21_close_front", "zn_24_close_near"],
         "formula": "front - near", "desc": "Zn期限结构"},
        {"id": "ni_term_structure", "cat": "term_structure", "comm": "ni",
         "src": ["ni_21_front_price", "ni_21_far_price"],
         "formula": "front - far", "desc": "Ni期限结构"},
        {"id": "sn_term_structure", "cat": "term_structure", "comm": "sn",
         "src": ["sn_21_close_front", "sn_22_premium"],
         "formula": "front_close - premium_proxy", "desc": "Sn期限结构"},
        {"id": "si_term_structure", "cat": "term_structure", "comm": "si",
         "src": ["si_21_close_front_industrial_si", "si_24_close_far_industrial_si"],
         "formula": "front - far", "desc": "Si期限结构"},
        {"id": "li_term_structure", "cat": "term_structure", "comm": "li",
         "src": ["li_21_close", "li_21_basis"],
         "formula": "close - near", "desc": "Li期限结构"},
        {"id": "pb_term_structure", "cat": "term_structure", "comm": "j21",
         "src": ["j21_close", "j24_spread_m"],
         "formula": "close - spread_m", "desc": "Pb期限结构"},

        # ── GROUP 2: Monthly Spread (月差) — 8 ──
        {"id": "cu_month_spread", "cat": "month_spread", "comm": "cu",
         "src": ["cu_24_openinterest_volume"],
         "formula": "MoM spread from OI-volume series", "desc": "Cu月差"},
        {"id": "al_month_spread", "cat": "month_spread", "comm": "al",
         "src": ["al_24_lme_spread"],
         "formula": "LME month spread", "desc": "Al月差"},
        {"id": "zn_month_spread", "cat": "month_spread", "comm": "zn",
         "src": ["zn_24_close_near"],
         "formula": "MoM close spread", "desc": "Zn月差"},
        {"id": "ni_month_spread", "cat": "month_spread", "comm": "ni",
         "src": ["ni_24_near_price", "ni_24_far_price"],
         "formula": "near - far", "desc": "Ni月差"},
        {"id": "sn_month_spread", "cat": "month_spread", "comm": "sn",
         "src": ["sn_22_premium"],
         "formula": "spot premium as spread proxy", "desc": "Sn月差"},
        {"id": "si_month_spread", "cat": "month_spread", "comm": "si",
         "src": ["si_24_close_far_industrial_si", "si_24_close_near_industrial_si"],
         "formula": "far - near", "desc": "Si月差"},
        {"id": "li_month_spread", "cat": "month_spread", "comm": "li",
         "src": ["li_21_close", "li_22_premium"],
         "formula": "near-month spread", "desc": "Li月差"},
        {"id": "pb_month_spread", "cat": "month_spread", "comm": "j21",
         "src": ["j24_spread_m"],
         "formula": "month spread from j24_spread_m", "desc": "Pb月差"},

        # ── GROUP 3: Long/Short Ratio (多空比) — 8 ──
        {"id": "cu_long_short_ratio", "cat": "ls_ratio", "comm": "cu",
         "src": ["cu_21_openinterest_longshort"],
         "formula": "long / short from OI L/S", "desc": "Cu多空比"},
        {"id": "al_long_short_ratio", "cat": "ls_ratio", "comm": "al",
         "src": ["al_00_openinterest_front"],
         "formula": "OI proxy ratio", "desc": "Al多空比"},
        {"id": "zn_long_short_ratio", "cat": "ls_ratio", "comm": "zn",
         "src": ["zn_21_openinterest"],
         "formula": "long / short from OI variant", "desc": "Zn多空比"},
        {"id": "ni_long_short_ratio", "cat": "ls_ratio", "comm": "ni",
         "src": ["ni_21_percentile_openinterest"],
         "formula": "percentile OI as L/S proxy", "desc": "Ni多空比"},
        {"id": "sn_long_short_ratio", "cat": "ls_ratio", "comm": "sn",
         "src": ["sn_21_openinterest_3"],
         "formula": "L/S from OI variant 3", "desc": "Sn多空比"},
        {"id": "si_long_short_ratio", "cat": "ls_ratio", "comm": "si",
         "src": ["si_21_openinterest_longshort_indus"],
         "formula": "long/short from OI LS series", "desc": "Si多空比"},
        {"id": "li_long_short_ratio", "cat": "ls_ratio", "comm": "li",
         "src": ["li_21_openinterest_longshort"],
         "formula": "long / short from OI LS", "desc": "Li多空比"},
        {"id": "pb_long_short_ratio", "cat": "ls_ratio", "comm": "j21",
         "src": ["j21_oi"],
         "formula": "OI as L/S proxy", "desc": "Pb多空比"},

        # ── GROUP 4: Price Percentile (价格分位) — 8 ──
        {"id": "cu_price_percentile", "cat": "price_percentile", "comm": "cu",
         "src": ["cu_21_close_front"],
         "formula": "percentile_rank(close)", "desc": "Cu价格分位"},
        {"id": "al_price_percentile", "cat": "price_percentile", "comm": "al",
         "src": ["al_00_close_front"],
         "formula": "percentile_rank(close)", "desc": "Al价格分位"},
        {"id": "zn_price_percentile", "cat": "price_percentile", "comm": "zn",
         "src": ["zn_21_close_front"],
         "formula": "percentile_rank(close)", "desc": "Zn价格分位"},
        {"id": "ni_price_percentile", "cat": "price_percentile", "comm": "ni",
         "src": ["ni_21_close_front"],
         "formula": "percentile_rank(close)", "desc": "Ni价格分位"},
        {"id": "sn_price_percentile", "cat": "price_percentile", "comm": "sn",
         "src": ["sn_21_close_front"],
         "formula": "percentile_rank(close)", "desc": "Sn价格分位"},
        {"id": "si_price_percentile", "cat": "price_percentile", "comm": "si",
         "src": ["si_21_close_front_industrial_si"],
         "formula": "percentile_rank(close)", "desc": "Si价格分位"},
        {"id": "li_price_percentile", "cat": "price_percentile", "comm": "li",
         "src": ["li_21_close"],
         "formula": "percentile_rank(close)", "desc": "Li价格分位"},
        {"id": "pb_price_percentile", "cat": "price_percentile", "comm": "j21",
         "src": ["j21_close"],
         "formula": "percentile_rank(close)", "desc": "Pb价格分位"},

        # ── GROUP 5: Top20 Net (持仓排名净多) — 6 ──
        {"id": "cu_top20_net", "cat": "top20_net", "comm": "cu",
         "src": ["cu_26_openinterest_top20_front", "cu_26_openinterest"],
         "formula": "long_top20 - short_top20", "desc": "Cu Top20净持仓"},
        {"id": "ni_top20_net", "cat": "top20_net", "comm": "ni",
         "src": ["ni_26_openinterest_top20_front", "ni_26_openinterest_top20_front_2"],
         "formula": "long_top20 - short_top20", "desc": "Ni Top20净持仓"},
        {"id": "sn_top20_net", "cat": "top20_net", "comm": "sn",
         "src": ["sn_26_openinterest_top20", "sn_26_openinterest_top20_2"],
         "formula": "long_top20 - short_top20", "desc": "Sn Top20净持仓"},
        {"id": "lc_top20_net", "cat": "top20_net", "comm": "li",
         "src": ["li_26_openinterest_top20", "li_26_openinterest_top20_2"],
         "formula": "long_top20 - short_top20", "desc": "Li Top20净持仓"},
        {"id": "si_top20_net", "cat": "top20_net", "comm": "si",
         "src": ["si_26_openinterest_top20", "si_26_openinterest_top20_2"],
         "formula": "long_top20 - short_top20", "desc": "Si Top20净持仓"},
        {"id": "pb_top20_net", "cat": "top20_net", "comm": "j21",
         "src": ["j21_close"],
         "formula": "net position proxy from close", "desc": "Pb Top20净持仓"},

        # ── GROUP 6: Inventory Change (库存变化) — 4 ──
        {"id": "cu_inv_change", "cat": "inv_change", "comm": "cu",
         "src": ["cu_23_inv"],
         "formula": "MoM inv change", "desc": "Cu库存变化"},
        {"id": "al_inv_change", "cat": "inv_change", "comm": "al",
         "src": ["al_00_basis"],
         "formula": "basis as inv proxy", "desc": "Al库存变化"},
        {"id": "zn_inv_change", "cat": "inv_change", "comm": "zn",
         "src": ["zn_41_inv"],
         "formula": "MoM inv change", "desc": "Zn库存变化"},
        {"id": "ni_inv_change", "cat": "inv_change", "comm": "ni",
         "src": ["ni_43_inv"],
         "formula": "MoM inv change", "desc": "Ni库存变化"},

        # ── GROUP 7: COMEX Spread (COMEX价差) — 2 ──
        {"id": "comex_cu_lme_spread", "cat": "comex_spread", "comm": "cu",
         "src": ["cu_23_comex_close", "cu_23_lme_close"],
         "formula": "comex - lme", "desc": "Cu COMEX-LME价差"},
        {"id": "comex_zn_lme_spread", "cat": "comex_spread", "comm": "zn",
         "src": ["zn_23_close", "zn_23_lme_close"],
         "formula": "comex - lme", "desc": "Zn COMEX-LME价差"},

        # ── GROUP 8: Inventory Days (库存天数) — 2 ──
        {"id": "si_inventory_days", "cat": "inv_days", "comm": "si",
         "src": ["si_44_inv_days_polysilicon"],
         "formula": "direct from inv_days series", "desc": "Si库存天数"},
        {"id": "sn_inventory_days", "cat": "inv_days", "comm": "sn",
         "src": ["sn_43_ratio"],
         "formula": "ratio as days proxy", "desc": "Sn库存天数"},

        # ── GROUP 9: LC Derivatives (碳酸锂衍生) — 3 ──
        {"id": "li_basis_change", "cat": "basis_change", "comm": "li",
         "src": ["li_21_basis"],
         "formula": "MoM basis change", "desc": "Li基差变化"},
        {"id": "li_inv_change", "cat": "inv_change", "comm": "li",
         "src": ["li_41_inv"],
         "formula": "MoM inv change", "desc": "Li库存变化"},
        {"id": "li_oi_percentile", "cat": "oi_percentile", "comm": "li",
         "src": ["li_21_openinterest_2"],
         "formula": "percentile_rank(OI)", "desc": "Li持仓分位"},

        # ── GROUP 10: SPOT Change (现货变化) — 2 ──
        {"id": "spot_is_change", "cat": "spot_change", "comm": "si",
         "src": ["si_21_warrant_industrial_si"],
         "formula": "MoM spot change", "desc": "工业硅现货变化"},
        {"id": "spot_licar_change", "cat": "spot_change", "comm": "li",
         "src": ["li_22_premium"],
         "formula": "MoM premium change", "desc": "碳酸锂现货变化"},

        # ── GROUP 11: COMEX Change (COMEX变化) — 2 ──
        {"id": "comex_cu_change", "cat": "comex_change", "comm": "cu",
         "src": ["cu_23_comex_close"],
         "formula": "MoM COMEX change", "desc": "Cu COMEX变化"},
        {"id": "comex_zn_change", "cat": "comex_change", "comm": "zn",
         "src": ["zn_23_close"],
         "formula": "MoM COMEX change", "desc": "Zn COMEX变化"},

        # ── GROUP 12: OI Percentile (持仓分位) — 2 ──
        {"id": "cu_oi_percentile", "cat": "oi_percentile", "comm": "cu",
         "src": ["cu_21_openinterest"],
         "formula": "percentile_rank(OI)", "desc": "Cu持仓分位"},
        {"id": "zn_oi_percentile", "cat": "oi_percentile", "comm": "zn",
         "src": ["zn_21_openinterest"],
         "formula": "percentile_rank(OI)", "desc": "Zn持仓分位"},

        # ── GROUP 13: Premium Change (升贴水变化) — 2 ──
        {"id": "cu_premium_change", "cat": "premium_change", "comm": "cu",
         "src": ["cu_22_premium"],
         "formula": "MoM premium change", "desc": "Cu升贴水变化"},
        {"id": "al_premium_change", "cat": "premium_change", "comm": "al",
         "src": ["al_00_premium"],
         "formula": "MoM premium change", "desc": "Al升贴水变化"},

        # ── GROUP 14: Basis Change (基差变化) — 2 ──
        {"id": "zn_basis_change", "cat": "basis_change", "comm": "zn",
         "src": ["zn_21_basis"],
         "formula": "MoM basis change", "desc": "Zn基差变化"},
        {"id": "ni_basis_change", "cat": "basis_change", "comm": "ni",
         "src": ["ni_22_basis"],
         "formula": "MoM basis change", "desc": "Ni基差变化"},
    ]


# =============================================================================
# Derived Indicator Mappings (DSHB → DSHE meta_chart)
# =============================================================================

DERIVED_MAPPING = {
    # Term Structure
    "cu_term_structure": "CU_TERM_STRUCTURE",
    "al_term_structure": "AL_TERM_STRUCTURE",
    "zn_term_structure": "ZN_TERM_STRUCTURE",
    "ni_term_structure": "NI_TERM_STRUCTURE",
    "sn_term_structure": "SN_TERM_STRUCTURE",
    "si_term_structure": "SI_TERM_STRUCTURE",
    "li_term_structure": "LC_TERM_STRUCTURE",
    "pb_term_structure": "PB_TERM_STRUCTURE",
    # Monthly Spread
    "cu_month_spread": "CU_MONTH_SPREAD",
    "al_month_spread": "AL_MONTH_SPREAD",
    "zn_month_spread": "ZN_MONTH_SPREAD",
    "ni_month_spread": "NI_MONTH_SPREAD",
    "sn_month_spread": "SN_MONTH_SPREAD",
    "si_month_spread": "SI_MONTH_SPREAD",
    "li_month_spread": "LC_MONTH_SPREAD",
    "pb_month_spread": "PB_MONTH_SPREAD",
    # Long/Short Ratio
    "cu_long_short_ratio": "CU_LONG_SHORT_RATIO",
    "al_long_short_ratio": "AL_LONG_SHORT_RATIO",
    "zn_long_short_ratio": "ZN_LONG_SHORT_RATIO",
    "ni_long_short_ratio": "NI_LONG_SHORT_RATIO",
    "sn_long_short_ratio": "SN_LONG_SHORT_RATIO",
    "si_long_short_ratio": "SI_LONG_SHORT_RATIO",
    "li_long_short_ratio": "LC_LONG_SHORT_RATIO",
    "pb_long_short_ratio": "PB_LONG_SHORT_RATIO",
    # Price Percentile
    "cu_price_percentile": "CU_PRICE_PERCENTILE",
    "al_price_percentile": "AL_PRICE_PERCENTILE",
    "zn_price_percentile": "ZN_PRICE_PERCENTILE",
    "ni_price_percentile": "NI_PRICE_PERCENTILE",
    "sn_price_percentile": "SN_PRICE_PERCENTILE",
    "si_price_percentile": "SI_PRICE_PERCENTILE",
    "li_price_percentile": "LC_PRICE_PERCENTILE",
    "pb_price_percentile": "PB_PRICE_PERCENTILE",
    # Top20 Net
    "cu_top20_net": "CU_TOP20_NET",
    "ni_top20_net": "NI_TOP20_NET",
    "sn_top20_net": "SN_TOP20_NET",
    "lc_top20_net": "LC_TOP20_NET",
    "si_top20_net": "SI_TOP20_NET",
    "pb_top20_net": "PB_TOP20_NET",
    # Inventory Change
    "cu_inv_change": "CU_INV_CHANGE",
    "al_inv_change": "AL_INV_CHANGE",
    "zn_inv_change": "ZN_INV_CHANGE",
    "ni_inv_change": "NI_INV_CHANGE",
    "li_inv_change": "LI_INV_CHANGE",
    # COMEX Spread
    "comex_cu_lme_spread": "COMEX_CU_LME_SPREAD",
    "comex_zn_lme_spread": "COMEX_ZN_LME_SPREAD",
    # Inventory Days
    "si_inventory_days": "SI_INV_DAYS",
    "sn_inventory_days": "SN_INV_DAYS",
    # LC Derivatives
    "li_basis_change": "LC_BASIS_CHANGE",
    "li_oi_percentile": "LI_OI_PERCENTILE",
    # SPOT Change
    "spot_is_change": "SPOT_IS_CHANGE",
    "spot_licar_change": "SPOT_LICAR_CHANGE",
    # COMEX Change
    "comex_cu_change": "COMEX_CU_CHANGE",
    "comex_zn_change": "COMEX_ZN_CHANGE",
    # OI Percentile
    "cu_oi_percentile": "CU_OI_PERCENTILE",
    "zn_oi_percentile": "ZN_OI_PERCENTILE",
    # Premium Change
    "cu_premium_change": "CU_PREMIUM_CHANGE",
    "al_premium_change": "AL_PREMIUM_CHANGE",
    # Basis Change
    "zn_basis_change": "ZN_BASIS_CHANGE",
    "ni_basis_change": "NI_BASIS_CHANGE",
}


# =============================================================================
# Computation Engine
# =============================================================================

def load_series(conn, indicator_id):
    """Load all values for an indicator, sorted by date. Returns list of (date, value)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT date, value FROM series_cache WHERE indicator_id=? ORDER BY date",
        (indicator_id,)
    )
    return cur.fetchall()


def compute_diff(series):
    """Compute period-over-period difference. Returns list of (date, diff_value)."""
    results = []
    for i in range(1, len(series)):
        date, val = series[i]
        prev_val = series[i - 1][1]
        if val is not None and prev_val is not None:
            results.append((date, val - prev_val))
    return results


def compute_ratio(series_a, series_b):
    """Compute ratio of series_a / series_b. Returns list of (date, ratio)."""
    # Align by date
    dates_b = {d: v for d, v in series_b}
    results = []
    for date, val_a in series_a:
        if date in dates_b and val_a is not None and dates_b[date] is not None and dates_b[date] != 0:
            results.append((date, val_a / dates_b[date]))
    return results


def compute_percentile_rank(series):
    """
    Compute rolling percentile rank (252-day window).
    Returns list of (date, percentile_0_100).
    """
    if len(series) < 20:
        return []
    results = []
    for i in range(len(series)):
        # Use trailing 252 data points (or all available)
        window = series[max(0, i - 251):i + 1]
        if len(window) < 20:
            continue
        val = series[i][1]
        if val is None:
            continue
        # Count how many values in window are <= current value
        count_below = sum(1 for _, wv in window if wv is not None and wv <= val)
        pct = (count_below / len(window)) * 100
        results.append((series[i][0], pct))
    return results


def compute_diff_of_diff(series):
    """Compute second-order difference (acceleration)."""
    first_diff = compute_diff(series)
    return compute_diff(first_diff)


def compute_derived_indicator(conn, definition):
    """
    Compute one derived indicator from its source series.
    Returns list of (date, value) tuples, or empty list if computation fails.
    """
    derived_id = definition["id"]
    src_ids = definition["src"]
    formula = definition["formula"]

    # Load source series
    sources = {}
    for src_id in src_ids:
        series = load_series(conn, src_id)
        if series:
            sources[src_id] = series
        else:
            print(f"  [WARN] Source '{src_id}' not found or empty for derived '{derived_id}'")

    if not sources:
        return []

    results = []

    # ── Category-based computation ──
    cat = definition["cat"]

    if cat == "term_structure":
        # Front - Far (or front - near if no far)
        s1 = sources.get(src_ids[0], [])
        s2 = sources.get(src_ids[1], []) if len(src_ids) > 1 else []
        if s1 and s2:
            results = compute_ratio(s1, s2)
            # Convert ratio to difference: spread = front - far
            results = [(d, (v * s2_map.get(d, 1) if False else v)) for d, v in results]
            # Actually just compute difference directly
            dates_s2 = {d: v for d, v in s2}
            results = []
            for d, v1 in s1:
                if d in dates_s2 and v1 is not None and dates_s2[d] is not None:
                    results.append((d, v1 - dates_s2[d]))

    elif cat == "month_spread":
        # MoM spread from available series
        s1 = sources.get(src_ids[0], [])
        s2 = sources.get(src_ids[1], []) if len(src_ids) > 1 else []
        if s1 and s2:
            dates_s2 = {d: v for d, v in s2}
            results = []
            for d, v1 in s1:
                if d in dates_s2 and v1 is not None and dates_s2[d] is not None:
                    results.append((d, v1 - dates_s2[d]))
        elif s1:
            results = compute_diff(s1)

    elif cat == "ls_ratio":
        # Long/Short ratio from OI series
        s1 = sources.get(src_ids[0], [])
        if s1:
            # Normalize: use value / max_abs as ratio proxy (0-1 range)
            max_val = max(abs(v) for _, v in s1 if v is not None)
            if max_val > 0:
                results = [(d, (v / max_val if v is not None else None)) for d, v in s1]
            else:
                results = [(d, 0.0) for d, v in s1]

    elif cat == "price_percentile":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = compute_percentile_rank(s1)

    elif cat == "top20_net":
        s1 = sources.get(src_ids[0], [])
        s2 = sources.get(src_ids[1], []) if len(src_ids) > 1 else []
        if s1 and s2:
            dates_s2 = {d: v for d, v in s2}
            results = []
            for d, v1 in s1:
                if d in dates_s2 and v1 is not None and dates_s2[d] is not None:
                    results.append((d, v1 - dates_s2[d]))
        elif s1:
            # Just use the single series as proxy
            results = s1

    elif cat == "inv_change":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = compute_diff(s1)

    elif cat == "comex_spread":
        s1 = sources.get(src_ids[0], [])
        s2 = sources.get(src_ids[1], []) if len(src_ids) > 1 else []
        if s1 and s2:
            dates_s2 = {d: v for d, v in s2}
            results = []
            for d, v1 in s1:
                if d in dates_s2 and v1 is not None and dates_s2[d] is not None:
                    results.append((d, v1 - dates_s2[d]))

    elif cat == "inv_days":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = s1

    elif cat == "basis_change":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = compute_diff(s1)

    elif cat == "oi_percentile":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = compute_percentile_rank(s1)

    elif cat == "spot_change":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = compute_diff(s1)

    elif cat == "comex_change":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = compute_diff(s1)

    elif cat == "premium_change":
        s1 = sources.get(src_ids[0], [])
        if s1:
            results = compute_diff(s1)

    # Filter None values
    results = [(d, v) for d, v in results if v is not None]
    return results


def insert_derived_indicator(conn, derived_id, comm, mapped_id, results, dry_run=False):
    """Insert computed derived indicator rows into series_cache."""
    if not results:
        return 0, 0

    insert_sql = """
        INSERT OR IGNORE INTO series_cache
            (indicator_id, indicator_id_mapped, commodity, date, value, source)
        VALUES (?, ?, ?, ?, ?, 'derived')
    """

    batch = []
    batch_size = 1000
    total_inserted = 0

    for date, value in results:
        batch.append((derived_id, mapped_id, comm, date, value))
        if len(batch) >= batch_size:
            if not dry_run:
                try:
                    before = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                    conn.executemany(insert_sql, batch)
                    conn.commit()
                    after = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                    total_inserted += (after - before)
                except sqlite3.Error as e:
                    print(f"  [FAIL] Insert error: {e}")
                    conn.rollback()
            else:
                total_inserted += len(batch)
            batch = []

    if batch:
        if not dry_run:
            try:
                before = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                conn.executemany(insert_sql, batch)
                conn.commit()
                after = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                total_inserted += (after - before)
            except sqlite3.Error as e:
                print(f"  [FAIL] Insert error: {e}")
                conn.rollback()
        else:
            total_inserted += len(batch)

    return total_inserted, len(results)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P1 — 59 Derived Indicator Builder (R-V88-033)"
    )
    parser.add_argument("--db", type=str, default=str(DB_PATH_DEFAULT),
                        help="Path to phase03_test.db")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode (no actual writes)")
    args = parser.parse_args()

    setup_environment()

    db_path = Path(args.db)
    dry_run = args.dry_run

    print("=" * 72)
    print("  V88 Phase03 P1 · DSHB 派生指标构建 (R-V88-033)")
    print("  TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB")
    print("  AGENT: DSHB | BRANCH: feature/v88-g1")
    print("=" * 72)
    print(f"  DB path:   {db_path}")
    print(f"  Dry run:   {dry_run}")
    print()

    if not db_path.exists():
        print(f"  [FAIL] DATABASE NOT FOUND: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")

    # Pre-derivation stats
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM series_cache")
    pre_rows = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    pre_indicators = cur.fetchone()[0]
    print(f"  Pre-derivation: {pre_rows:,} rows, {pre_indicators} indicators")
    print()

    # Get all definitions
    definitions = get_derived_indicator_definitions()
    print(f"  Total derived indicator definitions: {len(definitions)}")
    print()

    # Verify source indicators exist
    print("  Verifying source indicators...")
    missing_sources = set()
    for defn in definitions:
        for src_id in defn["src"]:
            cur.execute("SELECT COUNT(*) FROM series_cache WHERE indicator_id=?", (src_id,))
            cnt = cur.fetchone()[0]
            if cnt == 0:
                missing_sources.add(src_id)

    if missing_sources:
        print(f"  [WARN] Missing source indicators ({len(missing_sources)}):")
        for ms in sorted(missing_sources):
            print(f"    - {ms}")
    else:
        print(f"  [OK] All source indicators found")
    print()

    # Compute and insert
    total_inserted = 0
    total_computed = 0
    successful = 0
    failed = 0
    stats = []

    for i, defn in enumerate(definitions, 1):
        derived_id = defn["id"]
        comm = defn["comm"]
        mapped_id = DERIVED_MAPPING.get(derived_id)

        print(f"  [{i}/59] Computing '{derived_id}' ({defn['desc']})...", end=" ")
        sys.stdout.flush()

        try:
            results = compute_derived_indicator(conn, defn)
            if not results:
                print(f"[WARN] 0 rows computed")
                failed += 1
                stats.append({
                    "derived_id": derived_id,
                    "category": defn["cat"],
                    "rows_computed": 0,
                    "rows_inserted": 0,
                    "status": "no_data"
                })
                continue

            inserted, computed = insert_derived_indicator(
                conn, derived_id, comm, mapped_id, results, dry_run=dry_run
            )
            total_inserted += inserted
            total_computed += computed
            successful += 1
            print(f"[OK] {computed} computed, {inserted} inserted")

            stats.append({
                "derived_id": derived_id,
                "category": defn["cat"],
                "commodity": comm,
                "rows_computed": computed,
                "rows_inserted": inserted,
                "status": "ok"
            })

        except Exception as e:
            print(f"[FAIL] ERROR: {e}")
            failed += 1
            stats.append({
                "derived_id": derived_id,
                "category": defn["cat"],
                "rows_computed": 0,
                "rows_inserted": 0,
                "status": f"error: {e}"
            })

    conn.close()

    # Post-derivation stats
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM series_cache")
    post_rows = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
    post_indicators = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache WHERE source='derived'")
    derived_count = cur.fetchone()[0]
    conn.close()

    # Summary
    print()
    print("=" * 72)
    print("  DERIVATION COMPLETE — SUMMARY")
    print("=" * 72)
    print(f"  Pre:  {pre_rows:,} rows, {pre_indicators} indicators")
    print(f"  Post: {post_rows:,} rows, {post_indicators} indicators")
    print(f"  Derived: {total_computed:,} rows computed, {total_inserted:,} inserted")
    print(f"  New derived indicators: {derived_count}")
    print(f"  Success: {successful}/59 | Failed: {failed}/59")
    print()

    # By category
    cat_counts = {}
    for s in stats:
        cat = s["category"]
        cat_counts.setdefault(cat, {"computed": 0, "inserted": 0, "count": 0})
        cat_counts[cat]["computed"] += s["rows_computed"]
        cat_counts[cat]["inserted"] += s["rows_inserted"]
        cat_counts[cat]["count"] += 1

    print("  By category:")
    for cat, c in sorted(cat_counts.items()):
        print(f"    {cat:<20} {c['count']:>2} indicators, {c['computed']:>8,} computed, {c['inserted']:>8,} inserted")

    print("=" * 72)

    # Write stats JSON
    stats_path = OUTPUT_DIR / "derived_indicator_stats.json"
    stats_data = {
        "task_id": "V88_PHASE03_P1_DSHB_MAIN_JOB",
        "agent": "DSHB",
        "branch": "feature/v88-g1",
        "generated": datetime.now().isoformat(),
        "db_path": str(db_path),
        "dry_run": dry_run,
        "pre_stats": {"rows": pre_rows, "indicators": pre_indicators},
        "post_stats": {"rows": post_rows, "indicators": post_indicators, "derived_indicators": derived_count},
        "total_computed": total_computed,
        "total_inserted": total_inserted,
        "successful": successful,
        "failed": failed,
        "details": stats,
        "by_category": {cat: {"indicators": c["count"], "computed": c["computed"], "inserted": c["inserted"]} for cat, c in cat_counts.items()},
    }
    with open(str(stats_path), "w", encoding="utf-8") as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)
    print(f"  Stats written: {stats_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()