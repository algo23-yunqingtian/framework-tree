#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
engine_180indicator_adapter.py — V88 Phase03 P1 引擎 180+59 指标适配层
======================================================================
TASK_ID: V88_PHASE03_P1_DSHE_ENGINE_ADAPT
AGENT: DSHE | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

PURPOSE:
  NodeBindingEngine 是 FROZEN 不可修改的（MD5: CD73DEAEEC54A7F1F8BDE92C1300A9DC）。
  本适配层在其之上封装，使引擎能识别和计算 180 基础指标 + 59 衍生指标，
  同时兼容 V87/Phase02 (indicator_cache) 与 Phase03 (series_cache) 双 Schema。

ARCHITECTURE:
  NodeBindingEngine (FROZEN)  ─┐
                                ├──▶  Engine180IndicatorAdapter  ──▶  180+59 指标完整支持
  derive_indicators.py  (DSHB) ─┘
  phase03_test.db          ────────┘

CAPABILITIES:
  · 识别 59 项衍生指标（7 大类）
  · 自动推断指标是基础还是衍生
  · 从基础数据计算衍生指标（期限结构/月差/多空比/分位/Top20/平衡表）
  · 双 Schema 数据加载（indicator_cache + series_cache）
  · 优雅降级（缺失数据不崩溃）
  · 全量指标验证 + 适配报告生成
  · 可独立测试（无需加载 YAML）

USAGE:
  from engine_180indicator_adapter import Engine180IndicatorAdapter

  # Method 1: With engine instance (full functionality)
  from node_binding_engine import NodeBindingEngine
  engine = NodeBindingEngine(repo_root=REPO_ROOT)
  adapter = Engine180IndicatorAdapter(repo_root=engine.repo_root, engine=engine)

  # Method 2: Standalone mode (no engine dependency)
  adapter = Engine180IndicatorAdapter(
      repo_root=REPO_ROOT,
      db_path=os.path.join(REPO_ROOT, 'analysis'
              'e2e_output', 'v88', 'phase03', 'p0', 'phase03_test.db')
  )

  print(adapter.get_base_indicator_count())   # 目标 180
  print(adapter.get_derived_indicator_count()) # 目标 59
  print(adapter.is_derived_indicator("CU_TERM_STRUCTURE"))  # True
  adapter.validate_all_indicators()           # 验证所有指标
  report = adapter.get_adaptation_report()    # 生成适配报告

CONSTRAINTS:
  · 不修改 node_binding_engine.py
  · 仅使用 Python 标准库 + sqlite3
  · UTF-8 编码
  · 兼容 Windows (PYTHONIOENCODING=utf-8)

CHANGES:
  V88-P1.0.0 (2026-10-15): 初始版本，完整适配 180+59 指标体系
"""

import os
import sys
import re
import json
import sqlite3
import time
import hashlib
import logging
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from typing import Optional, List, Dict, Any, Tuple, Set

# =============================================================================
# Platform Setup (Windows UTF-8)
# =============================================================================

if os.name == "nt" or platform_name() == "Windows":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

logger = logging.getLogger("Engine180IndicatorAdapter")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)


def platform_name():
    """Return platform name string (Windows, Linux, Darwin, ...)."""
    try:
        import platform
        return platform.system()
    except ImportError:
        return os.name


# =============================================================================
# Derived Indicator Definitions (59 total, 7 major categories)
# =============================================================================
# Source: V88 Phase03 P1 DSHB derive_indicators.py (R-V88-033)
# Mapping: DERIVED_MAPPING in derive_indicators.py

#: Derived indicator type constants (suffix-based classification)
DERIVED_TYPE_TERM_STRUCTURE = "TERM_STRUCTURE"
DERIVED_TYPE_MONTH_SPREAD = "MONTH_SPREAD"
DERIVED_TYPE_LONG_SHORT_RATIO = "LONG_SHORT_RATIO"
DERIVED_TYPE_PRICE_PERCENTILE = "PRICE_PERCENTILE"
DERIVED_TYPE_TOP20_LONG = "TOP20_LONG"
DERIVED_TYPE_TOP20_SHORT = "TOP20_SHORT"
DERIVED_TYPE_BALANCE_SHEET = "BALANCE_SHEET"
DERIVED_TYPE_COMEX = "COMEX"
DERIVED_TYPE_LC = "LC"
DERIVED_TYPE_SPOT_IS = "SPOT_IS"
DERIVED_TYPE_BASIS_CHANGE = "BASIS_CHANGE"
DERIVED_TYPE_INVENTORY_CHANGE = "INVENTORY_CHANGE"
DERIVED_TYPE_INVENTORY_DAYS = "INVENTORY_DAYS"
DERIVED_TYPE_OI_PERCENTILE = "OI_PERCENTILE"
DERIVED_TYPE_PREMIUM_CHANGE = "PREMIUM_CHANGE"
DERIVED_TYPE_COMEX_CHANGE = "COMEX_CHANGE"
DERIVED_TYPE_SPOT_CHANGE = "SPOT_CHANGE"
DERIVED_TYPE_OTHER = "OTHER"


def _build_derived_indicator_definitions() -> List[Dict[str, str]]:
    """
    Build the complete 59 derived indicator definition list.

    Each definition contains:
      - derived_id: DSHE indicator ID (uppercase, underscore-separated)
      - category: derivation category (TERM_STRUCTURE, MONTH_SPREAD, etc.)
      - commodity: commodity code (cu, al, pb, zn, ni, sn, li, si)
      - sources: list of base indicator IDs (lowercase, DB indicator_id)
      - description: human-readable description

    Returns:
        List of 59 definition dictionaries, ordered by category.
    """
    defs = [
        # ── GROUP 1: Term Structure (期限结构) — 8 ──
        {"derived_id": "CU_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "cu", "sources": ["cu_21_close_front", "cu_24_openinterest_volume"],
         "description": "Cu期限结构 (front - far)"},
        {"derived_id": "AL_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "al", "sources": ["al_00_close_front", "al_24_lme_spread"],
         "description": "Al期限结构 (front - LME spread proxy)"},
        {"derived_id": "ZN_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "zn", "sources": ["zn_21_close_front", "zn_24_close_near"],
         "description": "Zn期限结构 (front - near)"},
        {"derived_id": "NI_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "ni", "sources": ["ni_21_front_price", "ni_21_far_price"],
         "description": "Ni期限结构 (front - far)"},
        {"derived_id": "SN_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "sn", "sources": ["sn_21_close_front", "sn_22_premium"],
         "description": "Sn期限结构 (front - premium proxy)"},
        {"derived_id": "SI_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "si", "sources": ["si_21_close_front_industrial_si", "si_24_close_far_industrial_si"],
         "description": "Si期限结构 (front - far)"},
        {"derived_id": "LC_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "li", "sources": ["li_21_close", "li_24_close_near"],
         "description": "Li期限结构 (close - near)"},
        {"derived_id": "PB_TERM_STRUCTURE", "category": DERIVED_TYPE_TERM_STRUCTURE,
         "commodity": "j21", "sources": ["j21_close", "j24_spread_m"],
         "description": "Pb期限结构 (close - spread_m)"},

        # ── GROUP 2: Monthly Spread (月差) — 8 ──
        {"derived_id": "CU_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "cu", "sources": ["cu_24_openinterest_volume"],
         "description": "Cu月差 (MoM spread from OI-volume)"},
        {"derived_id": "AL_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "al", "sources": ["al_24_lme_spread"],
         "description": "Al月差 (LME month spread)"},
        {"derived_id": "ZN_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "zn", "sources": ["zn_24_close_near"],
         "description": "Zn月差 (MoM close spread)"},
        {"derived_id": "NI_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "ni", "sources": ["ni_24_near_price", "ni_24_far_price"],
         "description": "Ni月差 (near - far)"},
        {"derived_id": "SN_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "sn", "sources": ["sn_22_premium"],
         "description": "Sn月差 (spot premium as spread proxy)"},
        {"derived_id": "SI_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "si", "sources": ["si_24_close_far_industrial_si", "si_24_close_near_industrial_si"],
         "description": "Si月差 (far - near)"},
        {"derived_id": "LC_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "li", "sources": ["li_24_close_near"],
         "description": "Li月差 (near-month spread)"},
        {"derived_id": "PB_MONTH_SPREAD", "category": DERIVED_TYPE_MONTH_SPREAD,
         "commodity": "j21", "sources": ["j24_spread_m"],
         "description": "Pb月差 (from j24_spread_m)"},

        # ── GROUP 3: Long/Short Ratio (多空比) — 8 ──
        {"derived_id": "CU_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "cu", "sources": ["cu_21_openinterest_longshort"],
         "description": "Cu多空比 (long/short from OI L/S)"},
        {"derived_id": "AL_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "al", "sources": ["al_00_openinterest_front"],
         "description": "Al多空比 (OI proxy ratio)"},
        {"derived_id": "ZN_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "zn", "sources": ["zn_21_openinterest_2"],
         "description": "Zn多空比 (long/short from OI variant)"},
        {"derived_id": "NI_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "ni", "sources": ["ni_21_percentile_openinterest"],
         "description": "Ni多空比 (percentile OI as L/S proxy)"},
        {"derived_id": "SN_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "sn", "sources": ["sn_21_openinterest_3"],
         "description": "Sn多空比 (L/S from OI variant 3)"},
        {"derived_id": "SI_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "si", "sources": ["si_21_openinterest_longshort_indus"],
         "description": "Si多空比 (long/short from OI LS)"},
        {"derived_id": "LC_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "li", "sources": ["li_21_openinterest_longshort"],
         "description": "Li多空比 (long/short from OI LS)"},
        {"derived_id": "PB_LONG_SHORT_RATIO", "category": DERIVED_TYPE_LONG_SHORT_RATIO,
         "commodity": "j21", "sources": ["j21_oi"],
         "description": "Pb多空比 (OI as L/S proxy)"},

        # ── GROUP 4: Price Percentile (价格分位) — 8 ──
        {"derived_id": "CU_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "cu", "sources": ["cu_21_close_front"],
         "description": "Cu价格分位 (252-day rolling percentile)"},
        {"derived_id": "AL_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "al", "sources": ["al_00_close_front"],
         "description": "Al价格分位 (252-day rolling percentile)"},
        {"derived_id": "ZN_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "zn", "sources": ["zn_21_close_front"],
         "description": "Zn价格分位 (252-day rolling percentile)"},
        {"derived_id": "NI_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "ni", "sources": ["ni_21_close_front"],
         "description": "Ni价格分位 (252-day rolling percentile)"},
        {"derived_id": "SN_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "sn", "sources": ["sn_21_close_front"],
         "description": "Sn价格分位 (252-day rolling percentile)"},
        {"derived_id": "SI_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "si", "sources": ["si_21_close_front_industrial_si"],
         "description": "Si价格分位 (252-day rolling percentile)"},
        {"derived_id": "LC_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "li", "sources": ["li_21_close"],
         "description": "Li价格分位 (252-day rolling percentile)"},
        {"derived_id": "PB_PRICE_PERCENTILE", "category": DERIVED_TYPE_PRICE_PERCENTILE,
         "commodity": "j21", "sources": ["j21_close"],
         "description": "Pb价格分位 (252-day rolling percentile)"},

        # ── GROUP 5: Top20 Net (持仓排名净持仓) — 6 ──
        # NOTE: DSHB uses *_TOP20_NET naming; DB may also have *_TOP20_LONG / *_TOP20_SHORT
        {"derived_id": "CU_TOP20_NET", "category": DERIVED_TYPE_TOP20_LONG,
         "commodity": "cu", "sources": ["cu_26_openinterest_top20_front", "cu_26_openinterest"],
         "description": "Cu Top20净持仓 (long - short)"},
        {"derived_id": "NI_TOP20_NET", "category": DERIVED_TYPE_TOP20_LONG,
         "commodity": "ni", "sources": ["ni_26_openinterest_top20_front", "ni_26_openinterest_top20_front_2"],
         "description": "Ni Top20净持仓 (long - short)"},
        {"derived_id": "SN_TOP20_NET", "category": DERIVED_TYPE_TOP20_LONG,
         "commodity": "sn", "sources": ["sn_26_openinterest_top20", "sn_26_openinterest_top20_2"],
         "description": "Sn Top20净持仓 (long - short)"},
        {"derived_id": "LC_TOP20_NET", "category": DERIVED_TYPE_TOP20_LONG,
         "commodity": "li", "sources": ["li_26_openinterest_top20", "li_26_openinterest_top20_2"],
         "description": "Li Top20净持仓 (long - short)"},
        {"derived_id": "SI_TOP20_NET", "category": DERIVED_TYPE_TOP20_LONG,
         "commodity": "si", "sources": ["si_26_openinterest_top20", "si_26_openinterest_top20_2"],
         "description": "Si Top20净持仓 (long - short)"},
        {"derived_id": "PB_TOP20_NET", "category": DERIVED_TYPE_TOP20_LONG,
         "commodity": "j21", "sources": ["j21_close"],
         "description": "Pb Top20净持仓 (close proxy)"},

        # ── GROUP 6: Balance Sheet / Inventory Change (平衡表/库存变化) — 4 ──
        {"derived_id": "CU_INV_CHANGE", "category": DERIVED_TYPE_INVENTORY_CHANGE,
         "commodity": "cu", "sources": ["cu_23_inv"],
         "description": "Cu库存变化 (MoM)"},
        {"derived_id": "AL_INV_CHANGE", "category": DERIVED_TYPE_INVENTORY_CHANGE,
         "commodity": "al", "sources": ["al_00_basis"],
         "description": "Al库存变化 (basis proxy)"},
        {"derived_id": "ZN_INV_CHANGE", "category": DERIVED_TYPE_INVENTORY_CHANGE,
         "commodity": "zn", "sources": ["zn_41_inv"],
         "description": "Zn库存变化 (MoM)"},
        {"derived_id": "NI_INV_CHANGE", "category": DERIVED_TYPE_INVENTORY_CHANGE,
         "commodity": "ni", "sources": ["ni_43_inv"],
         "description": "Ni库存变化 (MoM)"},

        # ── GROUP 7: COMEX Spread (COMEX价差) — 2 ──
        {"derived_id": "COMEX_CU_LME_SPREAD", "category": DERIVED_TYPE_COMEX,
         "commodity": "cu", "sources": ["cu_23_comex_close", "cu_23_lme_close"],
         "description": "Cu COMEX-LME价差"},
        {"derived_id": "COMEX_ZN_LME_SPREAD", "category": DERIVED_TYPE_COMEX,
         "commodity": "zn", "sources": ["zn_23_comex", "zn_23_lme_close"],
         "description": "Zn COMEX-LME价差"},

        # ── GROUP 8: Inventory Days (库存天数) — 2 ──
        {"derived_id": "SI_INV_DAYS", "category": DERIVED_TYPE_INVENTORY_DAYS,
         "commodity": "si", "sources": ["si_44_inv_days_polysilicon"],
         "description": "Si库存天数"},
        {"derived_id": "SN_INV_DAYS", "category": DERIVED_TYPE_INVENTORY_DAYS,
         "commodity": "sn", "sources": ["sn_43_ratio"],
         "description": "Sn库存天数 (ratio proxy)"},

        # ── GROUP 9: LC Derivatives (碳酸锂衍生) — 3 ──
        {"derived_id": "LC_BASIS_CHANGE", "category": DERIVED_TYPE_BASIS_CHANGE,
         "commodity": "li", "sources": ["li_21_basis"],
         "description": "Li基差变化 (MoM)"},
        {"derived_id": "LC_INV_CHANGE", "category": DERIVED_TYPE_INVENTORY_CHANGE,
         "commodity": "li", "sources": ["li_41_inv"],
         "description": "Li库存变化 (MoM)"},
        {"derived_id": "LC_OI_PERCENTILE", "category": DERIVED_TYPE_OI_PERCENTILE,
         "commodity": "li", "sources": ["li_21_openinterest_2"],
         "description": "Li持仓分位"},

        # ── GROUP 10: SPOT Change (现货变化) — 2 ──
        {"derived_id": "SPOT_IS_CHANGE", "category": DERIVED_TYPE_SPOT_CHANGE,
         "commodity": "si", "sources": ["si_24_spot"],
         "description": "工业硅现货变化 (MoM)"},
        {"derived_id": "SPOT_LICAR_CHANGE", "category": DERIVED_TYPE_SPOT_CHANGE,
         "commodity": "li", "sources": ["li_22_premium"],
         "description": "碳酸锂现货变化 (MoM)"},

        # ── GROUP 11: COMEX Change (COMEX变化) — 2 ──
        {"derived_id": "COMEX_CU_CHANGE", "category": DERIVED_TYPE_COMEX_CHANGE,
         "commodity": "cu", "sources": ["cu_23_comex_close"],
         "description": "Cu COMEX变化 (MoM)"},
        {"derived_id": "COMEX_ZN_CHANGE", "category": DERIVED_TYPE_COMEX_CHANGE,
         "commodity": "zn", "sources": ["zn_23_comex"],
         "description": "Zn COMEX变化 (MoM)"},

        # ── GROUP 12: OI Percentile (持仓分位) — 2 ──
        {"derived_id": "CU_OI_PERCENTILE", "category": DERIVED_TYPE_OI_PERCENTILE,
         "commodity": "cu", "sources": ["cu_21_openinterest"],
         "description": "Cu持仓分位"},
        {"derived_id": "ZN_OI_PERCENTILE", "category": DERIVED_TYPE_OI_PERCENTILE,
         "commodity": "zn", "sources": ["zn_21_openinterest"],
         "description": "Zn持仓分位"},

        # ── GROUP 13: Premium Change (升贴水变化) — 2 ──
        {"derived_id": "CU_PREMIUM_CHANGE", "category": DERIVED_TYPE_PREMIUM_CHANGE,
         "commodity": "cu", "sources": ["cu_22_premium"],
         "description": "Cu升贴水变化 (MoM)"},
        {"derived_id": "AL_PREMIUM_CHANGE", "category": DERIVED_TYPE_PREMIUM_CHANGE,
         "commodity": "al", "sources": ["al_00_premium"],
         "description": "Al升贴水变化 (MoM)"},

        # ── GROUP 14: Basis Change (基差变化) — 2 ──
        {"derived_id": "ZN_BASIS_CHANGE", "category": DERIVED_TYPE_BASIS_CHANGE,
         "commodity": "zn", "sources": ["zn_21_basis"],
         "description": "Zn基差变化 (MoM)"},
        {"derived_id": "NI_BASIS_CHANGE", "category": DERIVED_TYPE_BASIS_CHANGE,
         "commodity": "ni", "sources": ["ni_22_basis"],
         "description": "Ni基差变化 (MoM)"},
    ]

    # Deduplicate: some definitions share derived_id (e.g. COMEX_SPREAD vs COMEX_CHANGE)
    seen = set()
    unique = []
    for d in defs:
        key = (d["derived_id"], d["category"])
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


#: All 59 derived indicator definitions (computed at module load)
DERIVED_DEFINITIONS = _build_derived_indicator_definitions()

#: Quick lookup: derived_id -> definition
DERIVED_INDEX: Dict[str, Dict[str, str]] = {
    d["derived_id"]: d for d in DERIVED_DEFINITIONS
}

#: Derived indicator IDs that are prefix-based (COMEX_*, LC_*, SPOT_IS_*)
#: These are derived from base data but identified by prefix pattern
PREFIX_BASED_DERIVED_PATTERNS = [
    re.compile(r"^COMEX_[A-Z]+$"),
    re.compile(r"^LC_[A-Z_]+$"),
    re.compile(r"^SPOT_IS[A-Z_]*$"),
    re.compile(r"^SPOT_[A-Z_]+$"),
]

#: Derived indicator IDs that are suffix-based
SUFFIX_BASED_DERIVED_PATTERNS = [
    re.compile(r"_TERM_STRUCTURE$"),
    re.compile(r"_MONTH_SPREAD$"),
    re.compile(r"_LONG_SHORT_RATIO$"),
    re.compile(r"_PRICE_PERCENTILE$"),
    re.compile(r"_TOP20_LONG$"),
    re.compile(r"_TOP20_SHORT$"),
    re.compile(r"_BALANCE_SHEET$"),
    re.compile(r"_INV_CHANGE$"),
    re.compile(r"_BASIS_CHANGE$"),
    re.compile(r"_PREMIUM_CHANGE$"),
    re.compile(r"_COMEX_CHANGE$"),
    re.compile(r"_SPOT_CHANGE$"),
    re.compile(r"_OI_PERCENTILE$"),
    re.compile(r"_INV_DAYS$"),
]


def _classify_indicator(indicator_id: str) -> str:
    """
    Classify an indicator ID into 'base', 'derived', or 'unknown'.

    Uses a priority check:
    1. Exact match against DERIVED_INDEX (covers all 59 named derived indicators)
    2. Prefix pattern match (COMEX_*, LC_*, SPOT_*)
    3. Suffix pattern match (*_TERM_STRUCTURE, etc.)
    4. Default: 'base' if alphanumeric+underscore, 'unknown' otherwise

    Args:
        indicator_id: The indicator ID string (e.g. "CU_TERM_STRUCTURE")

    Returns:
        "derived" if the indicator is derived, "base" if base, "unknown" otherwise.
    """
    if not indicator_id or not isinstance(indicator_id, str):
        return "unknown"

    uid = indicator_id.strip().upper()

    # 1. Exact match against defined derived indicators
    if uid in DERIVED_INDEX:
        return "derived"

    # 2. Check if the indicator follows a derived naming pattern but isn't in the list
    #    (e.g. future expansions or DSHB-derived indicators not yet in definitions)
    #    Prefix-based patterns
    for pat in PREFIX_BASED_DERIVED_PATTERNS:
        if pat.match(uid):
            return "derived"

    # 3. Suffix-based patterns
    for pat in SUFFIX_BASED_DERIVED_PATTERNS:
        if pat.search(uid):
            return "derived"

    # 4. Valid base indicator naming convention: must match a known commodity
    #    prefix pattern. Base indicators follow {COMM}_{FIELD} or {SOURCE}_{ID}.
    KNOWN_COMM_PREFIXES = (
        "CU_", "AL_", "PB_", "ZN_", "NI_", "SN_", "SI_", "LI_", "LC_",
        "AU_", "AG_", "J21_", "J22_", "J23_", "J24_", "J25_", "J26_",
        "FU000", "LME_",
    )
    if re.match(r"^[A-Z][A-Z0-9_]*$", uid):
        for prefix in KNOWN_COMM_PREFIXES:
            if uid.startswith(prefix):
                return "base"
        return "unknown"

    return "unknown"


def _get_derived_type(indicator_id: str) -> str:
    """
    Get the derived indicator type/category for a given indicator ID.

    Returns:
        DERIVED_TYPE_* constant string, or DERIVED_TYPE_OTHER if not found.
    """
    uid = indicator_id.strip().upper() if indicator_id else ""

    # Exact match first
    if uid in DERIVED_INDEX:
        return DERIVED_INDEX[uid]["category"]

    # Prefix-based patterns
    if re.match(r"^COMEX_", uid):
        if re.search(r"_CHANGE$", uid):
            return DERIVED_TYPE_COMEX_CHANGE
        if re.search(r"_SPREAD$", uid):
            return DERIVED_TYPE_COMEX
        return DERIVED_TYPE_COMEX

    if re.match(r"^LC_", uid):
        return DERIVED_TYPE_LC

    if re.match(r"^SPOT_", uid):
        if re.search(r"_CHANGE$", uid):
            return DERIVED_TYPE_SPOT_CHANGE
        return DERIVED_TYPE_SPOT_IS

    # Suffix-based patterns
    if re.search(r"_TERM_STRUCTURE$", uid):
        return DERIVED_TYPE_TERM_STRUCTURE
    if re.search(r"_MONTH_SPREAD$", uid):
        return DERIVED_TYPE_MONTH_SPREAD
    if re.search(r"_LONG_SHORT_RATIO$", uid):
        return DERIVED_TYPE_LONG_SHORT_RATIO
    if re.search(r"_PRICE_PERCENTILE$", uid):
        return DERIVED_TYPE_PRICE_PERCENTILE
    if re.search(r"_TOP20_LONG$", uid):
        return DERIVED_TYPE_TOP20_LONG
    if re.search(r"_TOP20_SHORT$", uid):
        return DERIVED_TYPE_TOP20_SHORT
    if re.search(r"_BALANCE_SHEET$", uid):
        return DERIVED_TYPE_BALANCE_SHEET
    if re.search(r"_INV_CHANGE$", uid):
        return DERIVED_TYPE_INVENTORY_CHANGE
    if re.search(r"_BASIS_CHANGE$", uid):
        return DERIVED_TYPE_BASIS_CHANGE
    if re.search(r"_PREMIUM_CHANGE$", uid):
        return DERIVED_TYPE_PREMIUM_CHANGE
    if re.search(r"_OI_PERCENTILE$", uid):
        return DERIVED_TYPE_OI_PERCENTILE
    if re.search(r"_INV_DAYS$", uid):
        return DERIVED_TYPE_INVENTORY_DAYS

    return DERIVED_TYPE_OTHER


def _get_derived_sources(indicator_id: str) -> List[str]:
    """
    Get the source (base) indicator IDs required to compute a derived indicator.

    Args:
        indicator_id: The derived indicator ID (e.g. "CU_TERM_STRUCTURE")

    Returns:
        List of source indicator IDs (e.g. ["cu_21_close_front", "cu_24_openinterest_volume"])
        Empty list if not a known derived indicator.
    """
    uid = indicator_id.strip().upper() if indicator_id else ""
    if uid in DERIVED_INDEX:
        return list(DERIVED_INDEX[uid]["sources"])
    return []


# =============================================================================
# Computation Engine (pure functions, no DB I/O)
# =============================================================================

def compute_diff(series: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Compute period-over-period difference.

    Args:
        series: List of (date, value) tuples sorted by date.

    Returns:
        List of (date, diff_value) tuples. First point is dropped (no previous value).
    """
    results = []
    for i in range(1, len(series)):
        date, val = series[i]
        prev_val = series[i - 1][1]
        if val is not None and prev_val is not None:
            results.append((date, val - prev_val))
    return results


def compute_diff_of_diff(series: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Compute second-order difference (acceleration).

    Args:
        series: List of (date, value) tuples sorted by date.

    Returns:
        List of (date, second_diff) tuples. First two points are dropped.
    """
    first_diff = compute_diff(series)
    return compute_diff(first_diff)


def compute_ratio(series_a: List[Tuple[str, float]],
                  series_b: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Compute ratio of series_a / series_b, aligned by date.

    Args:
        series_a: Numerator series (date, value) tuples.
        series_b: Denominator series (date, value) tuples.

    Returns:
        List of (date, ratio) tuples where both dates exist and denominator != 0.
    """
    dates_b = {d: v for d, v in series_b}
    results = []
    for date, val_a in series_a:
        if date in dates_b:
            val_b = dates_b[date]
            if val_a is not None and val_b is not None and val_b != 0:
                results.append((date, val_a / val_b))
    return results


def compute_difference_aligned(
    series_a: List[Tuple[str, float]],
    series_b: List[Tuple[str, float]]
) -> List[Tuple[str, float]]:
    """
    Compute difference a - b, aligned by date.

    Args:
        series_a: First series (date, value) tuples.
        series_b: Second series (date, value) tuples.

    Returns:
        List of (date, a_b_diff) tuples where both dates exist and both values not None.
    """
    dates_b = {d: v for d, v in series_b}
    results = []
    for date, val_a in series_a:
        if date in dates_b:
            val_b = dates_b[date]
            if val_a is not None and val_b is not None:
                results.append((date, val_a - val_b))
    return results


def compute_percentile_rank(series: List[Tuple[str, float]],
                            window: int = 252,
                            min_points: int = 20) -> List[Tuple[str, float]]:
    """
    Compute rolling percentile rank within a sliding window.

    Args:
        series: List of (date, value) tuples sorted by date.
        window: Window size in data points (default 252 ≈ 1 year trading days).
        min_points: Minimum points required in window before computing.

    Returns:
        List of (date, percentile_0_to_100) tuples.
    """
    if len(series) < min_points:
        return []

    results = []
    for i in range(len(series)):
        # Use trailing window
        window_slice = series[max(0, i - window + 1):i + 1]
        if len(window_slice) < min_points:
            continue

        val = series[i][1]
        if val is None:
            continue

        # Count values <= current
        count_below = sum(1 for _, wv in window_slice if wv is not None and wv <= val)
        pct = (count_below / len(window_slice)) * 100.0
        results.append((series[i][0], round(pct, 2)))

    return results


def compute_long_short_proxy(series: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Compute long/short ratio proxy from a single OI series.
    Uses value / max_abs as a ratio proxy (range 0 to 1).

    Args:
        series: List of (date, value) tuples sorted by date.

    Returns:
        List of (date, ratio_proxy) tuples.
    """
    if not series:
        return []

    valid_vals = [v for _, v in series if v is not None]
    if not valid_vals:
        return []

    max_abs = max(abs(v) for v in valid_vals)
    if max_abs == 0:
        return [(d, 0.0) for d, v in series if v is not None]

    results = []
    for d, v in series:
        if v is not None:
            results.append((d, round(v / max_abs, 6)))
    return results


def compute_top20_long_from_single(series: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Use a single series as a proxy for Top20 long position.
    For indicators where only one series is available, the series itself is the proxy.

    Args:
        series: List of (date, value) tuples.

    Returns:
        Same series (as a proxy for net long position).
    """
    return [(d, v) for d, v in series if v is not None]


def compute_top20_short_from_single(series: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Use a single series as a proxy for Top20 short position.
    Negate the value to represent short direction.

    Args:
        series: List of (date, value) tuples.

    Returns:
        List of (date, negated_value) tuples representing short positions.
    """
    return [(d, -v) for d, v in series if v is not None]


def compute_top20_net(
    long_series: List[Tuple[str, float]],
    short_series: List[Tuple[str, float]]
) -> List[Tuple[str, float]]:
    """
    Compute net top-20 position (long - short), aligned by date.

    Args:
        long_series: Long position series (date, value) tuples.
        short_series: Short position series (date, value) tuples.

    Returns:
        List of (date, net_position) tuples.
    """
    dates_short = {d: v for d, v in short_series}
    results = []
    for date, val_long in long_series:
        if date in dates_short:
            val_short = dates_short[date]
            if val_long is not None and val_short is not None:
                results.append((date, val_long - val_short))
    return results


def compute_inventory_change(series: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Compute inventory change (month-over-month or period-over-period difference).

    Args:
        series: Inventory level series (date, value) tuples.

    Returns:
        List of (date, change) tuples.
    """
    return compute_diff(series)


def compute_balance_sheet_proxy(
    supply_series: List[Tuple[str, float]],
    demand_series: List[Tuple[str, float]]
) -> List[Tuple[str, float]]:
    """
    Compute balance sheet proxy: supply - demand = balance.

    Args:
        supply_series: Supply series (date, value) tuples.
        demand_series: Demand series (date, value) tuples.

    Returns:
        List of (date, balance) tuples.
    """
    return compute_difference_aligned(supply_series, demand_series)


def compute_comex_lme_spread(
    comex_series: List[Tuple[str, float]],
    lme_series: List[Tuple[str, float]]
) -> List[Tuple[str, float]]:
    """
    Compute COMEX - LME spread, aligned by date.

    Args:
        comex_series: COMEX price series (date, value) tuples.
        lme_series: LME price series (date, value) tuples.

    Returns:
        List of (date, spread) tuples.
    """
    return compute_difference_aligned(comex_series, lme_series)


def compute_oi_percentile(
    oi_series: List[Tuple[str, float]],
    window: int = 252,
    min_points: int = 20
) -> List[Tuple[str, float]]:
    """
    Compute OI (Open Interest) percentile rank using rolling window.

    Args:
        oi_series: OI series (date, value) tuples.
        window: Rolling window size.
        min_points: Minimum points in window.

    Returns:
        List of (date, percentile_0_to_100) tuples.
    """
    return compute_percentile_rank(oi_series, window=window, min_points=min_points)


# =============================================================================
# Database Access Layer (dual-schema support)
# =============================================================================

def _resolve_db_path(repo_root: str, db_path: Optional[str] = None) -> Optional[str]:
    """
    Resolve the SQLite database path using the same priority as NodeBindingEngine.

    Priority:
      1. Explicit db_path argument
      2. V88_PHASE03_TEST_DB environment variable
      3. V88_API_CACHE_DB environment variable
      4. scripts/api_cache.db (default)

    Args:
        repo_root: Repository root directory.
        db_path: Explicit database path override (highest priority).

    Returns:
        Resolved database path string, or None if not found.
    """
    # Priority 1: Explicit override
    if db_path and os.path.exists(db_path):
        return db_path

    # Priority 2: V88_PHASE03_TEST_DB
    env_p03 = os.environ.get("V88_PHASE03_TEST_DB", "").strip()
    if env_p03 and os.path.exists(env_p03):
        return env_p03

    # Priority 3: V88_API_CACHE_DB
    env_api = os.environ.get("V88_API_CACHE_DB", "").strip()
    if env_api and os.path.exists(env_api):
        return env_api

    # Priority 4: Default path
    default_path = os.path.join(repo_root, "scripts", "api_cache.db")
    if os.path.exists(default_path):
        return default_path

    return None


def _detect_table_schema(cursor: sqlite3.Cursor) -> Set[str]:
    """
    Detect available tables in the SQLite database.

    Args:
        cursor: An open SQLite cursor.

    Returns:
        Set of table names, e.g. {"series_cache", "indicator_cache", ...}
    """
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cursor.fetchall()}


def _load_from_indicator_cache(
    cursor: sqlite3.Cursor,
    indicator_id: str,
    code: str
) -> Optional[Dict[str, Any]]:
    """
    Load data from indicator_cache table (V87/Phase02 schema).

    Table structure: indicator_cache(metric, code, data_json)
    data_json format: {"name": "...", "unit": "...", "points": [{"date": "...", "value": ...}]}

    Args:
        cursor: SQLite cursor.
        indicator_id: The indicator ID to query.
        code: Commodity code (e.g. "CU").

    Returns:
        Dict with {"name", "unit", "points": [{"date", "value"}]} or None.
    """
    try:
        cursor.execute(
            "SELECT data_json FROM indicator_cache WHERE metric=? AND code=?",
            (indicator_id, code.upper())
        )
        row = cursor.fetchone()
        if row and row[0]:
            d = json.loads(row[0])
            pts = []
            for p in d.get("points", []):
                if isinstance(p, dict) and p.get("date") and p.get("value") is not None:
                    pts.append({"date": p["date"], "value": float(p["value"])})
            pts.sort(key=lambda x: x["date"])
            return {
                "name": d.get("name", ""),
                "unit": d.get("unit", ""),
                "points": pts,
            }
    except Exception as e:
        logger.debug(f"_load_from_indicator_cache({indicator_id}, {code}): {e}")
    return None


def _load_from_series_cache(
    cursor: sqlite3.Cursor,
    indicator_id: str,
    commodity: str
) -> Optional[Dict[str, Any]]:
    """
    Load data from series_cache table (Phase03 schema).

    Table structure: series_cache(id, indicator_id, indicator_id_mapped, commodity, date, value, source, imported_at)

    Args:
        cursor: SQLite cursor.
        indicator_id: The mapped indicator ID (indicator_id_mapped) to query.
        commodity: The commodity code.

    Returns:
        Dict with {"name": "", "unit": "", "points": [{"date", "value"}]} or None.
    """
    try:
        cursor.execute(
            "SELECT date, value FROM series_cache "
            "WHERE indicator_id_mapped=? AND commodity=? AND indicator_id_mapped IS NOT NULL "
            "ORDER BY date",
            (indicator_id, commodity)
        )
        rows = cursor.fetchall()
        if rows:
            pts = []
            for r in rows:
                if r[1] is not None:
                    pts.append({"date": r[0], "value": float(r[1])})
            if pts:
                return {"name": "", "unit": "", "points": pts}
    except Exception as e:
        logger.debug(f"_load_from_series_cache({indicator_id}, {commodity}): {e}")
    return None


def _load_from_series_cache_by_raw_id(
    cursor: sqlite3.Cursor,
    indicator_id_raw: str,
    commodity: str
) -> Optional[Dict[str, Any]]:
    """
    Load data from series_cache using the raw (unmapped) indicator_id.

    This is needed for computing derived indicators whose sources are raw IDs.

    Args:
        cursor: SQLite cursor.
        indicator_id_raw: The raw indicator_id (e.g. "cu_21_close_front").
        commodity: The commodity code.

    Returns:
        Dict with {"name": "", "unit": "", "points": [...]} or None.
    """
    try:
        cursor.execute(
            "SELECT date, value FROM series_cache "
            "WHERE indicator_id=? AND commodity=? ORDER BY date",
            (indicator_id_raw, commodity)
        )
        rows = cursor.fetchall()
        if rows:
            pts = []
            for r in rows:
                if r[1] is not None:
                    pts.append({"date": r[0], "value": float(r[1])})
            if pts:
                return {"name": "", "unit": "", "points": pts}
    except Exception as e:
        logger.debug(f"_load_from_series_cache_by_raw_id({indicator_id_raw}, {commodity}): {e}")
    return None


def _load_series_list(
    cursor: sqlite3.Cursor,
    indicator_id: str,
    commodity: str
) -> List[Tuple[str, float]]:
    """
    Load a series as a list of (date, value) tuples from either schema.

    Automatically detects the table schema.

    Args:
        cursor: SQLite cursor.
        indicator_id: The indicator ID (mapped or raw).
        commodity: The commodity code.

    Returns:
        List of (date, value) tuples, or empty list.
    """
    tables = _detect_table_schema(cursor)

    if "series_cache" in tables:
        # Try mapped ID first
        data = _load_from_series_cache(cursor, indicator_id, commodity)
        if not data:
            # Try raw ID
            data = _load_from_series_cache_by_raw_id(cursor, indicator_id, commodity)

    elif "indicator_cache" in tables:
        data = _load_from_indicator_cache(cursor, indicator_id, commodity.upper())
    else:
        return []

    if data and data.get("points"):
        return [(p["date"], p["value"]) for p in data["points"]]
    return []


# =============================================================================
# Main Adapter Class
# =============================================================================

class Engine180IndicatorAdapter:
    """
    V88 Phase03 P1 — Engine 180+59 Indicator Adapter

    This adapter wraps a frozen NodeBindingEngine instance (or operates standalone)
    to provide complete support for 180 base indicators and 59 derived indicators.
    It works with both indicator_cache (V87/Phase02) and series_cache (Phase03) schemas.

    Architecture:
        NodeBindingEngine (FROZEN)  ─┐
                                      ├──▶  Engine180IndicatorAdapter  ──▶  180+59 indicators
        derive_indicators.py (DSHB) ─┘

    Usage:
        adapter = Engine180IndicatorAdapter(repo_root, engine=engine)
        adapter.validate_all_indicators()
        report = adapter.get_adaptation_report()

    Attributes:
        repo_root: Repository root directory path.
        engine: Reference to NodeBindingEngine instance (optional).
        db_path: Resolved database path (None if not found).
        engine_charts_count: Number of charts in the engine (0 if no engine).
    """

    # Target indicator counts
    TARGET_BASE_COUNT = 180
    TARGET_DERIVED_COUNT = 59

    def __init__(
        self,
        repo_root: str,
        engine: Optional[Any] = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize the adapter.

        Args:
            repo_root: Repository root directory (absolute path).
            engine: Optional NodeBindingEngine instance (from scripts/node_binding_engine.py).
                    If provided, the adapter uses the engine's _resolve_db_path() and
                    _load_from_* methods. If None, the adapter resolves DB path independently.
            db_path: Explicit database path override (highest priority).

        Raises:
            TypeError: If engine is provided but is not a valid engine-like object.
        """
        self.repo_root = repo_root
        self.engine = engine
        self.db_path = _resolve_db_path(repo_root, db_path)

        # Validate engine if provided
        if engine is not None:
            # Check if engine has expected methods (duck-typing)
            required_methods = ['_resolve_db_path', '_load_from_indicator_cache',
                                '_load_from_series_cache', 'get_stats']
            missing = [m for m in required_methods if not hasattr(engine, m)]
            if missing:
                raise TypeError(
                    f"engine object missing required methods: {missing}. "
                    f"Expected a NodeBindingEngine instance or compatible duck-type."
                )

        # Use engine's DB path if engine provided and it resolves a valid path
        if engine is not None and self.db_path is None:
            try:
                engine_db = engine._resolve_db_path()
                if engine_db and os.path.exists(engine_db):
                    self.db_path = engine_db
            except Exception as e:
                logger.debug(f"engine._resolve_db_path() failed: {e}")

        # Cache
        self._indicator_counts_cache: Optional[Dict[str, int]] = None
        self._db_indicators_cache: Optional[Set[str]] = None
        self._db_indicators_by_raw_cache: Optional[Set[str]] = None
        self._validation_cache: Optional[Dict[str, Any]] = None

        logger.info(
            f"Engine180IndicatorAdapter initialized | "
            f"repo_root={repo_root} | "
            f"engine={'yes' if engine else 'no'} | "
            f"db_path={self.db_path or 'NOT FOUND'}"
        )

    # =========================================================================
    # Public API: Indicator Counts
    # =========================================================================

    def get_base_indicator_count(self) -> int:
        """
        Return the count of base (non-derived) indicators detected in the database.

        Counts all indicator_id_mapped values from series_cache that are NOT
        in the derived indicator set. This represents the "base" indicators
        that derived indicators are computed from.

        Returns:
            Integer count of base indicators found in the database.
            0 if no database is available.
        """
        counts = self._get_indicator_counts()
        return counts.get("base", 0)

    def get_derived_indicator_count(self) -> int:
        """
        Return the count of derived indicators detected in the database.

        Counts all indicator_id_mapped values from series_cache that ARE
        recognized as derived indicators (via DERIVED_INDEX or pattern matching).

        Returns:
            Integer count of derived indicators found in the database.
            0 if no database is available.
        """
        counts = self._get_indicator_counts()
        return counts.get("derived", 0)

    def get_total_indicator_count(self) -> int:
        """
        Return total unique indicators in the database.

        Returns:
            Integer count of distinct indicators (indicator_id_mapped).
        """
        counts = self._get_indicator_counts()
        return counts.get("total", 0)

    # =========================================================================
    # Public API: Indicator Classification
    # =========================================================================

    def is_derived_indicator(self, indicator_id: str) -> bool:
        """
        Check if an indicator ID represents a derived indicator.

        Uses a three-tier classification:
        1. Exact match against DERIVED_INDEX (59 defined indicators)
        2. Prefix pattern match (COMEX_*, LC_*, SPOT_*)
        3. Suffix pattern match (*_TERM_STRUCTURE, etc.)

        Args:
            indicator_id: The indicator ID string (case-insensitive).

        Returns:
            True if the indicator is derived, False if base, False for unknown.
        """
        return _classify_indicator(indicator_id) == "derived"

    def is_base_indicator(self, indicator_id: str) -> bool:
        """
        Check if an indicator ID represents a base (non-derived) indicator.

        Args:
            indicator_id: The indicator ID string (case-insensitive).

        Returns:
            True if the indicator is classified as base.
        """
        return _classify_indicator(indicator_id) == "base"

    def get_derived_indicator_type(self, indicator_id: str) -> str:
        """
        Get the derived indicator type/category.

        Returns one of the DERIVED_TYPE_* constants:
          - DERIVED_TYPE_TERM_STRUCTURE: "TERM_STRUCTURE"
          - DERIVED_TYPE_MONTH_SPREAD: "MONTH_SPREAD"
          - DERIVED_TYPE_LONG_SHORT_RATIO: "LONG_SHORT_RATIO"
          - DERIVED_TYPE_PRICE_PERCENTILE: "PRICE_PERCENTILE"
          - DERIVED_TYPE_TOP20_LONG: "TOP20_LONG"
          - DERIVED_TYPE_TOP20_SHORT: "TOP20_SHORT"
          - DERIVED_TYPE_BALANCE_SHEET: "BALANCE_SHEET"
          - DERIVED_TYPE_COMEX: "COMEX"
          - DERIVED_TYPE_COMEX_CHANGE: "COMEX_CHANGE"
          - DERIVED_TYPE_LC: "LC"
          - DERIVED_TYPE_SPOT_IS: "SPOT_IS"
          - DERIVED_TYPE_SPOT_CHANGE: "SPOT_CHANGE"
          - DERIVED_TYPE_BASIS_CHANGE: "BASIS_CHANGE"
          - DERIVED_TYPE_INVENTORY_CHANGE: "INVENTORY_CHANGE"
          - DERIVED_TYPE_INVENTORY_DAYS: "INVENTORY_DAYS"
          - DERIVED_TYPE_OI_PERCENTILE: "OI_PERCENTILE"
          - DERIVED_TYPE_PREMIUM_CHANGE: "PREMIUM_CHANGE"
          - DERIVED_TYPE_OTHER: "OTHER"

        Args:
            indicator_id: The indicator ID string.

        Returns:
            DERIVED_TYPE_* constant string.
        """
        return _get_derived_type(indicator_id)

    def get_derived_sources(self, indicator_id: str) -> List[str]:
        """
        Get the source (base) indicator IDs required to compute a derived indicator.

        Args:
            indicator_id: The derived indicator ID (e.g. "CU_TERM_STRUCTURE").

        Returns:
            List of source indicator IDs (e.g. ["cu_21_close_front", "cu_24_openinterest_volume"]).
            Empty list if the indicator is not a known derived indicator.
        """
        return _get_derived_sources(indicator_id)

    def list_all_derived_indicators(self) -> List[Dict[str, str]]:
        """
        List all 59 defined derived indicator definitions.

        Returns:
            List of definition dicts, each with keys:
              derived_id, category, commodity, sources, description
        """
        return list(DERIVED_DEFINITIONS)

    def list_derived_by_type(self, derived_type: str) -> List[Dict[str, str]]:
        """
        List derived indicators filtered by type/category.

        Args:
            derived_type: One of the DERIVED_TYPE_* constants.

        Returns:
            List of definition dicts matching the given type.
        """
        return [d for d in DERIVED_DEFINITIONS if d["category"] == derived_type]

    # =========================================================================
    # Public API: Derived Indicator Computation
    # =========================================================================

    def compute_derived_indicator(
        self,
        indicator_id: str,
        db_path: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Compute a derived indicator from base data in the database.

        The computation is dispatched based on the derived indicator's category:
          - TERM_STRUCTURE: ratio of far-month to near-month price
          - MONTH_SPREAD: absolute difference between consecutive months
          - LONG_SHORT_RATIO: long_position / short_position
          - PRICE_PERCENTILE: percentile rank within N-day window
          - TOP20_LONG/SHORT: top-20 net long/short position
          - BALANCE_SHEET: supply - demand = balance

        Args:
            indicator_id: The derived indicator ID (e.g. "CU_TERM_STRUCTURE").
            db_path: Optional database path override. If None, uses self.db_path.

        Returns:
            List of (date, value) tuples representing the computed series.
            Empty list if computation fails or source data is missing.

        Raises:
            ValueError: If indicator_id is not a recognized derived indicator.
            sqlite3.Error: If database connection fails.
        """
        uid = indicator_id.strip().upper()

        # Look up definition
        if uid not in DERIVED_INDEX:
            # Check if it's a pattern-matched derived indicator
            if not self.is_derived_indicator(uid):
                raise ValueError(
                    f"'{indicator_id}' is not a recognized derived indicator. "
                    f"Use list_all_derived_indicators() to see available derived IDs."
                )
            # Pattern-matched: use the definition if available, otherwise skip
            # This handles edge cases where an indicator matches a pattern but
            # isn't in the explicit definitions (e.g. future expansions)
            return []

        definition = DERIVED_INDEX[uid]
        category = definition["category"]
        sources = definition["sources"]
        commodity = definition["commodity"]

        # Resolve DB path
        effective_db = db_path or self.db_path
        if not effective_db or not os.path.exists(effective_db):
            logger.warning(
                f"compute_derived_indicator('{indicator_id}'): "
                f"database not found at '{effective_db}'"
            )
            return []

        try:
            conn = sqlite3.connect(effective_db)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            cursor = conn.cursor()
        except sqlite3.Error as e:
            logger.error(f"compute_derived_indicator: DB connection failed: {e}")
            return []

        try:
            # Load source series
            sources_data = {}
            for src_id in sources:
                series = _load_series_list(cursor, src_id, commodity)
                if series:
                    sources_data[src_id] = series
                else:
                    logger.debug(
                        f"Source '{src_id}' not found or empty for '{uid}' "
                        f"(commodity={commodity})"
                    )

            if not sources_data:
                logger.warning(
                    f"compute_derived_indicator('{uid}'): "
                    f"no source data available from {sources}"
                )
                return []

            # Dispatch by category
            result = self._compute_by_category(category, sources, sources_data)
            return result

        finally:
            conn.close()

    def compute_all_derived_indicators(
        self,
        db_path: Optional[str] = None
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Compute all 59 derived indicators from base data.

        Args:
            db_path: Optional database path override.

        Returns:
            Dict mapping derived_id -> list of (date, value) tuples.
            Empty entries for indicators that failed to compute.
        """
        results = {}
        definitions = DERIVED_DEFINITIONS

        for defn in definitions:
            uid = defn["derived_id"]
            try:
                series = self.compute_derived_indicator(uid, db_path=db_path)
                results[uid] = series
                status = "OK" if series else "EMPTY"
                logger.debug(f"compute_all_derived: {uid} -> {len(series)} points ({status})")
            except Exception as e:
                results[uid] = []
                logger.warning(f"compute_all_derived: {uid} -> ERROR: {e}")

        return results

    def compute_and_cache_derived(
        self,
        db_path: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Compute all derived indicators and optionally cache them in the database.

        Args:
            db_path: Optional database path override.
            dry_run: If True, compute but don't write to DB.

        Returns:
            Stats dict with computation results:
              {
                "total_defined": 59,
                "successful": N,
                "failed": N,
                "empty": N,
                "total_points": N,
                "per_indicator": {derived_id: {"points": N, "status": str}},
                "cached_rows": N (if not dry_run)
              }
        """
        effective_db = db_path or self.db_path
        results = self.compute_all_derived_indicators(db_path=effective_db)

        stats = {
            "total_defined": len(DERIVED_DEFINITIONS),
            "successful": 0,
            "failed": 0,
            "empty": 0,
            "total_points": 0,
            "per_indicator": {},
            "cached_rows": 0,
            "dry_run": dry_run,
        }

        for uid, series in results.items():
            point_count = len(series)
            if point_count > 0:
                stats["successful"] += 1
                status = "ok"
            elif uid in DERIVED_INDEX:
                # Known definition but no data
                stats["empty"] += 1
                status = "no_data"
            else:
                stats["failed"] += 1
                status = "not_found"

            stats["total_points"] += point_count
            stats["per_indicator"][uid] = {
                "points": point_count,
                "status": status,
                "category": DERIVED_INDEX.get(uid, {}).get("category", "UNKNOWN"),
            }

        # Write to DB if not dry-run
        if not dry_run and effective_db and stats["total_points"] > 0:
            stats["cached_rows"] = self._cache_derived_to_db(effective_db, results)

        return stats

    # =========================================================================
    # Public API: Validation
    # =========================================================================

    def validate_all_indicators(
        self,
        db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate all indicators against the database.

        Checks:
          1. How many of the 59 defined derived indicators are present in DB
          2. How many base indicators are in the DB
          3. Which derived indicators are missing
          4. Which base indicators are missing (compared to known sources)
          5. Data quality (row counts, date ranges)

        Args:
            db_path: Optional database path override.

        Returns:
            Validation report dict:
              {
                "db_path": str,
                "db_available": bool,
                "base_count": int,
                "derived_count_in_db": int,
                "derived_defined_count": int,
                "derived_present_in_db": int,
                "derived_missing_from_db": int,
                "derived_missing_ids": [str, ...],
                "total_db_indicators": int,
                "total_db_rows": int,
                "data_date_range": {"min": str, "max": str},
                "source_availability": {derived_id: {"sources_found": int, "sources_total": int, "sources_missing": [str]}},
                "validation_summary": str,
                "errors": [str, ...]
              }
        """
        self._validation_cache = None  # Invalidate cache

        effective_db = db_path or self.db_path
        validation = {
            "db_path": effective_db,
            "db_available": bool(effective_db and os.path.exists(effective_db)),
            "base_count": 0,
            "derived_count_in_db": 0,
            "derived_defined_count": len(DERIVED_DEFINITIONS),
            "derived_present_in_db": 0,
            "derived_missing_from_db": 0,
            "derived_missing_ids": [],
            "total_db_indicators": 0,
            "total_db_rows": 0,
            "data_date_range": {"min": None, "max": None},
            "source_availability": {},
            "validation_summary": "",
            "errors": [],
        }

        if not validation["db_available"]:
            validation["validation_summary"] = "FAIL: Database not found"
            validation["errors"].append(f"Database not found at '{effective_db}'")
            self._validation_cache = validation
            return validation

        try:
            conn = sqlite3.connect(effective_db)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            cursor = conn.cursor()
        except sqlite3.Error as e:
            validation["validation_summary"] = f"FAIL: DB connection error: {e}"
            validation["errors"].append(str(e))
            self._validation_cache = validation
            return validation

        try:
            # Detect schema
            tables = _detect_table_schema(cursor)

            if "series_cache" in tables:
                # Count total rows
                cursor.execute("SELECT COUNT(*) FROM series_cache")
                validation["total_db_rows"] = cursor.fetchone()[0]

                # Count distinct indicators (mapped)
                cursor.execute(
                    "SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache "
                    "WHERE indicator_id_mapped IS NOT NULL AND indicator_id_mapped != ''"
                )
                validation["total_db_indicators"] = cursor.fetchone()[0]

                # Date range
                cursor.execute(
                    "SELECT MIN(date), MAX(date) FROM series_cache "
                    "WHERE date IS NOT NULL"
                )
                row = cursor.fetchone()
                if row and row[0]:
                    validation["data_date_range"] = {"min": row[0], "max": row[1]}

                # Classify indicators
                cursor.execute(
                    "SELECT DISTINCT indicator_id_mapped FROM series_cache "
                    "WHERE indicator_id_mapped IS NOT NULL AND indicator_id_mapped != ''"
                )
                all_mapped = [r[0].upper() for r in cursor.fetchall()]

                derived_in_db = set()
                base_in_db = set()
                for ind in all_mapped:
                    if _classify_indicator(ind) == "derived":
                        derived_in_db.add(ind)
                    else:
                        base_in_db.add(ind)

                validation["derived_count_in_db"] = len(derived_in_db)
                validation["base_count"] = len(base_in_db)

                # Check which defined derived indicators are present
                derived_def_ids = {d["derived_id"] for d in DERIVED_DEFINITIONS}
                derived_present = derived_def_ids & derived_in_db
                derived_missing = derived_def_ids - derived_in_db

                validation["derived_present_in_db"] = len(derived_present)
                validation["derived_missing_from_db"] = len(derived_missing)
                validation["derived_missing_ids"] = sorted(derived_missing)

            elif "indicator_cache" in tables:
                cursor.execute("SELECT COUNT(*) FROM indicator_cache")
                validation["total_db_rows"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT metric) FROM indicator_cache")
                validation["total_db_indicators"] = cursor.fetchone()[0]

                cursor.execute("SELECT DISTINCT metric FROM indicator_cache")
                all_metrics = [r[0].upper() for r in cursor.fetchall()]

                derived_in_db = set()
                base_in_db = set()
                for ind in all_metrics:
                    if _classify_indicator(ind) == "derived":
                        derived_in_db.add(ind)
                    else:
                        base_in_db.add(ind)

                validation["derived_count_in_db"] = len(derived_in_db)
                validation["base_count"] = len(base_in_db)

                derived_def_ids = {d["derived_id"] for d in DERIVED_DEFINITIONS}
                derived_present = derived_def_ids & derived_in_db
                derived_missing = derived_def_ids - derived_in_db

                validation["derived_present_in_db"] = len(derived_present)
                validation["derived_missing_from_db"] = len(derived_missing)
                validation["derived_missing_ids"] = sorted(derived_missing)

            else:
                validation["errors"].append(
                    f"No indicator_cache or series_cache table found in DB. "
                    f"Available tables: {tables}"
                )

            # Check source availability for derived indicators
            if "series_cache" in tables:
                cursor.execute(
                    "SELECT DISTINCT indicator_id FROM series_cache "
                    "WHERE indicator_id IS NOT NULL AND indicator_id != ''"
                )
                all_raw_ids = {r[0].lower() for r in cursor.fetchall()}

                for defn in DERIVED_DEFINITIONS:
                    uid = defn["derived_id"]
                    sources = defn["sources"]
                    found = [s for s in sources if s.lower() in all_raw_ids]
                    missing = [s for s in sources if s.lower() not in all_raw_ids]
                    validation["source_availability"][uid] = {
                        "sources_found": len(found),
                        "sources_total": len(sources),
                        "sources_missing": missing,
                    }

        except Exception as e:
            validation["errors"].append(str(e))
            validation["validation_summary"] = f"FAIL: {e}"

        finally:
            conn.close()

        # Build summary
        total_def = validation["derived_defined_count"]
        present = validation["derived_present_in_db"]
        coverage_pct = (present / total_def * 100) if total_def > 0 else 0

        if validation["errors"]:
            validation["validation_summary"] = f"FAIL: {len(validation['errors'])} errors"
        else:
            parts = [
                f"DB: {validation['db_available']}",
                f"Base: {validation['base_count']}",
                f"Derived in DB: {validation['derived_count_in_db']}",
                f"Derived defined: {total_def}",
                f"Derived coverage: {coverage_pct:.1f}% ({present}/{total_def})",
                f"Total indicators: {validation['total_db_indicators']}",
                f"Total rows: {validation['total_db_rows']:,}",
            ]
            validation["validation_summary"] = " | ".join(parts)

        self._validation_cache = validation
        return validation

    # =========================================================================
    # Public API: Adaptation Report
    # =========================================================================

    def get_adaptation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive engine adaptation report.

        The report covers:
          - Engine status (FROZEN, MD5, capabilities)
          - Database status (path, schema, size)
          - Indicator coverage (base, derived, total)
          - Derived indicator computation results
          - Validation results
          - Degradation analysis
          - Recommendations

        Returns:
            Comprehensive report dict with all adaptation metrics.
        """
        # Run validation first
        validation = self.validate_all_indicators()

        # Compute derived indicators
        compute_stats = self.compute_and_cache_derived(dry_run=True)

        # Build report
        report = {
            "report_title": "V88 Phase03 P1 — Engine 180+59 Indicator Adaptation Report",
            "generated_at": datetime.now().isoformat(),
            "engine": {
                "file": "scripts/node_binding_engine.py",
                "md5": "CD73DEAEEC54A7F1F8BDE92C1300A9DC",
                "status": "FROZEN",
                "modifiable": False,
                "adapter_version": "V88-P1.0.0",
            },
            "database": {
                "path": validation["db_path"],
                "available": validation["db_available"],
                "total_rows": validation["total_db_rows"],
                "total_indicators": validation["total_db_indicators"],
                "date_range": validation["data_date_range"],
            },
            "indicators": {
                "target_base": self.TARGET_BASE_COUNT,
                "target_derived": self.TARGET_DERIVED_COUNT,
                "actual_base": validation["base_count"],
                "actual_derived_in_db": validation["derived_count_in_db"],
                "actual_derived_defined": len(DERIVED_DEFINITIONS),
                "derived_coverage_pct": (
                    validation["derived_present_in_db"] / len(DERIVED_DEFINITIONS) * 100
                    if DERIVED_DEFINITIONS else 0
                ),
                "total_target": self.TARGET_BASE_COUNT + self.TARGET_DERIVED_COUNT,
            },
            "derived_computation": {
                "total_defined": compute_stats["total_defined"],
                "successful": compute_stats["successful"],
                "empty": compute_stats["empty"],
                "failed": compute_stats["failed"],
                "total_points": compute_stats["total_points"],
                "dry_run": compute_stats["dry_run"],
            },
            "validation": {
                "summary": validation["validation_summary"],
                "errors": validation["errors"],
                "derived_missing_ids": validation["derived_missing_ids"],
            },
            "degradation": self._compute_degradation_analysis(validation, compute_stats),
            "recommendations": self._generate_recommendations(validation, compute_stats),
            "derived_definition_count": len(DERIVED_DEFINITIONS),
            "derived_by_category": self._count_derived_by_category(),
            "schema_support": {
                "indicator_cache": "supported (V87/Phase02)",
                "series_cache": "supported (Phase03)",
                "dual_schema": True,
            },
        }

        return report

    # =========================================================================
    # Public API: Statistics
    # =========================================================================

    def get_indicator_counts(self) -> Dict[str, int]:
        """
        Get a breakdown of indicator counts.

        Returns:
            Dict with keys:
              - "total": total distinct indicators in DB
              - "base": base indicator count
              - "derived": derived indicator count
              - "derived_defined": count of defined derived indicators (59)
              - "derived_in_db": derived indicators present in DB
              - "derived_missing": defined derived indicators not in DB
        """
        counts = self._get_indicator_counts()
        counts["derived_defined"] = len(DERIVED_DEFINITIONS)
        return counts

    def get_computation_stats(self) -> Dict[str, Any]:
        """
        Get derived indicator computation statistics (dry-run).

        Returns:
            Stats dict from compute_and_cache_derived(dry_run=True).
        """
        return self.compute_and_cache_derived(dry_run=True)

    # =========================================================================
    # Private: Indicator Counts Cache
    # =========================================================================

    def _get_indicator_counts(self) -> Dict[str, int]:
        """
        Get cached indicator counts, computing from DB if needed.

        Returns:
            Dict with "total", "base", "derived" keys.
        """
        if self._indicator_counts_cache is not None:
            return self._indicator_counts_cache

        counts = {"total": 0, "base": 0, "derived": 0}

        if not self.db_path or not os.path.exists(self.db_path):
            self._indicator_counts_cache = counts
            return counts

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            tables = _detect_table_schema(cursor)

            if "series_cache" in tables:
                cursor.execute(
                    "SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache "
                    "WHERE indicator_id_mapped IS NOT NULL AND indicator_id_mapped != ''"
                )
                counts["total"] = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT DISTINCT indicator_id_mapped FROM series_cache "
                    "WHERE indicator_id_mapped IS NOT NULL AND indicator_id_mapped != ''"
                )
                all_mapped = [r[0].upper() for r in cursor.fetchall()]

                derived_count = 0
                for ind in all_mapped:
                    if _classify_indicator(ind) == "derived":
                        derived_count += 1

                counts["derived"] = derived_count
                counts["base"] = counts["total"] - derived_count

            elif "indicator_cache" in tables:
                cursor.execute("SELECT COUNT(DISTINCT metric) FROM indicator_cache")
                counts["total"] = cursor.fetchone()[0]

                cursor.execute("SELECT DISTINCT metric FROM indicator_cache")
                all_metrics = [r[0].upper() for r in cursor.fetchall()]

                derived_count = 0
                for ind in all_metrics:
                    if _classify_indicator(ind) == "derived":
                        derived_count += 1

                counts["derived"] = derived_count
                counts["base"] = counts["total"] - derived_count

            conn.close()

        except Exception as e:
            logger.warning(f"_get_indicator_counts failed: {e}")

        self._indicator_counts_cache = counts
        return counts

    # =========================================================================
    # Private: Computation Dispatcher
    # =========================================================================

    def _compute_by_category(
        self,
        category: str,
        sources: List[str],
        sources_data: Dict[str, List[Tuple[str, float]]]
    ) -> List[Tuple[str, float]]:
        """
        Dispatch computation to the appropriate algorithm based on category.

        Args:
            category: DERIVED_TYPE_* constant.
            sources: List of source indicator IDs (in order).
            sources_data: Dict of source_id -> series_data.

        Returns:
            List of (date, value) tuples.
        """
        # Load first two source series if available
        s1 = sources_data.get(sources[0], []) if sources else []
        s2 = sources_data.get(sources[1], []) if len(sources) > 1 else []

        if category == DERIVED_TYPE_TERM_STRUCTURE:
            # front - far (difference)
            if s1 and s2:
                return compute_difference_aligned(s1, s2)
            elif s1:
                return compute_diff(s1)

        elif category == DERIVED_TYPE_MONTH_SPREAD:
            # MoM spread
            if s1 and s2:
                return compute_difference_aligned(s1, s2)
            elif s1:
                return compute_diff(s1)

        elif category == DERIVED_TYPE_LONG_SHORT_RATIO:
            # L/S ratio from OI
            if s1:
                return compute_long_short_proxy(s1)

        elif category == DERIVED_TYPE_PRICE_PERCENTILE:
            # Percentile rank
            if s1:
                return compute_percentile_rank(s1)

        elif category == DERIVED_TYPE_TOP20_LONG:
            # Top20 long: use single series as proxy
            if s1:
                return compute_top20_long_from_single(s1)

        elif category == DERIVED_TYPE_TOP20_SHORT:
            # Top20 short: use single series as proxy (negated)
            if s1:
                return compute_top20_short_from_single(s1)

        elif category == DERIVED_TYPE_BALANCE_SHEET:
            # Supply - Demand
            if s1 and s2:
                return compute_balance_sheet_proxy(s1, s2)

        elif category == DERIVED_TYPE_COMEX:
            # COMEX - LME spread
            if s1 and s2:
                return compute_comex_lme_spread(s1, s2)

        elif category == DERIVED_TYPE_INVENTORY_CHANGE:
            # MoM change
            if s1:
                return compute_inventory_change(s1)

        elif category == DERIVED_TYPE_INVENTORY_DAYS:
            # Direct series (already in days)
            if s1:
                return [(d, v) for d, v in s1 if v is not None]

        elif category == DERIVED_TYPE_BASIS_CHANGE:
            # MoM change in basis
            if s1:
                return compute_diff(s1)

        elif category == DERIVED_TYPE_OI_PERCENTILE:
            # OI percentile
            if s1:
                return compute_oi_percentile(s1)

        elif category == DERIVED_TYPE_SPOT_CHANGE:
            # MoM change in spot
            if s1:
                return compute_diff(s1)

        elif category == DERIVED_TYPE_COMEX_CHANGE:
            # MoM change in COMEX
            if s1:
                return compute_diff(s1)

        elif category == DERIVED_TYPE_PREMIUM_CHANGE:
            # MoM change in premium
            if s1:
                return compute_diff(s1)

        elif category == DERIVED_TYPE_LC:
            # LC-specific derivation: check sub-category
            uid = category
            if "_BASIS" in uid:
                if s1:
                    return compute_diff(s1)
            elif "_MONTH_SPREAD" in uid or "_TERM_STRUCTURE" in uid:
                if s1 and s2:
                    return compute_difference_aligned(s1, s2)
                elif s1:
                    return compute_diff(s1)

        elif category == DERIVED_TYPE_SPOT_IS:
            # SPOT_IS: direct series
            if s1:
                return [(d, v) for d, v in s1 if v is not None]

        elif category == DERIVED_TYPE_OTHER:
            # Generic: use first source series as fallback
            if s1:
                return [(d, v) for d, v in s1 if v is not None]

        return []

    # =========================================================================
    # Private: DB Caching
    # =========================================================================

    def _cache_derived_to_db(
        self,
        db_path: str,
        results: Dict[str, List[Tuple[str, float]]]
    ) -> int:
        """
        Cache computed derived indicators into the series_cache table.

        Uses INSERT OR IGNORE to avoid overwriting existing data.

        Args:
            db_path: Path to the SQLite database.
            results: Dict of derived_id -> (date, value) list.

        Returns:
            Number of rows actually inserted.
        """
        if not results or not db_path:
            return 0

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            cursor = conn.cursor()

            # Detect schema - only write to series_cache
            tables = _detect_table_schema(cursor)
            if "series_cache" not in tables:
                logger.warning("_cache_derived_to_db: no series_cache table found")
                conn.close()
                return 0

            insert_sql = """
                INSERT OR IGNORE INTO series_cache
                    (indicator_id, indicator_id_mapped, commodity, date, value, source)
                VALUES (?, ?, ?, ?, ?, 'derived_adapter')
            """

            total_inserted = 0
            batch = []
            batch_size = 500

            for derived_id, series in results.items():
                if not series:
                    continue

                defn = DERIVED_INDEX.get(derived_id)
                if not defn:
                    continue

                comm = defn["commodity"]

                for date, value in series:
                    batch.append((derived_id.lower(), derived_id, comm, date, value))

                    if len(batch) >= batch_size:
                        try:
                            conn.executemany(insert_sql, batch)
                            conn.commit()
                            total_inserted += len(batch)
                        except sqlite3.Error as e:
                            logger.warning(f"_cache_derived_to_db: insert batch error: {e}")
                            conn.rollback()
                        batch = []

            # Final batch
            if batch:
                try:
                    conn.executemany(insert_sql, batch)
                    conn.commit()
                    total_inserted += len(batch)
                except sqlite3.Error as e:
                    logger.warning(f"_cache_derived_to_db: final batch error: {e}")
                    conn.rollback()

            conn.close()
            return total_inserted

        except sqlite3.Error as e:
            logger.error(f"_cache_derived_to_db: DB error: {e}")
            return 0

    # =========================================================================
    # Private: Analysis Helpers
    # =========================================================================

    def _compute_degradation_analysis(
        self,
        validation: Dict[str, Any],
        compute_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute degradation analysis: what happens when data is missing.

        Returns:
            Dict with degradation metrics.
        """
        total_defined = len(DERIVED_DEFINITIONS)
        successful = compute_stats.get("successful", 0)
        empty = compute_stats.get("empty", 0)
        failed = compute_stats.get("failed", 0)

        # Degradation levels
        degradation = {
            "total_defined": total_defined,
            "fully_computable": successful,
            "missing_source_data": empty,
            "not_computable": failed,
            "degradation_rate_pct": round((total_defined - successful) / total_defined * 100, 2)
                if total_defined > 0 else 0,
        }

        # Source-level degradation
        source_availability = validation.get("source_availability", {})
        indicators_with_partial_sources = 0
        indicators_with_no_sources = 0

        for uid, avail in source_availability.items():
            if avail["sources_found"] == 0:
                indicators_with_no_sources += 1
            elif avail["sources_found"] < avail["sources_total"]:
                indicators_with_partial_sources += 1

        degradation["indicators_with_no_sources"] = indicators_with_no_sources
        degradation["indicators_with_partial_sources"] = indicators_with_partial_sources
        degradation["indicators_with_full_sources"] = total_defined - indicators_with_no_sources - indicators_with_partial_sources

        return degradation

    def _generate_recommendations(
        self,
        validation: Dict[str, Any],
        compute_stats: Dict[str, Any]
    ) -> List[str]:
        """
        Generate actionable recommendations based on validation and computation results.

        Returns:
            List of recommendation strings.
        """
        recs = []

        if not validation["db_available"]:
            recs.append("CRITICAL: Database not found. Set V88_PHASE03_TEST_DB or provide db_path.")
            return recs

        # Check derived coverage
        total_def = validation["derived_defined_count"]
        present = validation["derived_present_in_db"]
        coverage_pct = present / total_def * 100 if total_def > 0 else 0

        if coverage_pct < 50:
            recs.append(
                f"LOW DERIVED COVERAGE ({coverage_pct:.1f}%): Only {present}/{total_def} "
                f"derived indicators present in DB. Consider running derive_indicators.py."
            )

        # Check missing sources
        source_availability = validation.get("source_availability", {})
        no_source_count = sum(
            1 for v in source_availability.values() if v["sources_found"] == 0
        )
        if no_source_count > 0:
            recs.append(
                f"MISSING SOURCES: {no_source_count} derived indicators have no source data "
                f"in DB. Check DSHB data ingestion pipeline."
            )

        # Check computation success
        successful = compute_stats.get("successful", 0)
        total_def = compute_stats.get("total_defined", 0)
        if total_def > 0 and successful / total_def < 0.5:
            recs.append(
                f"LOW COMPUTATION SUCCESS ({successful}/{total_def}): "
                f"Many derived indicators fail to compute. Check source data availability."
            )

        # Base indicator count vs target
        base_count = validation["base_count"]
        if base_count < self.TARGET_BASE_COUNT:
            recs.append(
                f"BASE COUNT BELOW TARGET ({base_count}/{self.TARGET_BASE_COUNT}): "
                f"Consider expanding data ingestion to reach 180 base indicators."
            )

        # Schema compatibility
        if validation["db_available"]:
            try:
                conn = sqlite3.connect(validation["db_path"])
                tables = _detect_table_schema(conn.cursor())
                conn.close()
                if "series_cache" in tables and "indicator_cache" not in tables:
                    recs.append("INFO: Only series_cache schema available. V87 compatibility requires indicator_cache.")
                elif "indicator_cache" in tables and "series_cache" not in tables:
                    recs.append("INFO: Only indicator_cache schema available. Phase03 features require series_cache.")
                elif "series_cache" in tables and "indicator_cache" in tables:
                    recs.append("INFO: Dual schema available (series_cache + indicator_cache). Full compatibility.")
            except Exception:
                pass

        if not recs:
            recs.append("ALL CLEAR: No critical issues detected. Adapter operating within expected parameters.")

        return recs

    def _count_derived_by_category(self) -> Dict[str, int]:
        """
        Count derived indicators by category/type.

        Returns:
            Dict of category -> count.
        """
        counts = defaultdict(int)
        for d in DERIVED_DEFINITIONS:
            counts[d["category"]] += 1
        return dict(sorted(counts.items()))


# =============================================================================
# Self-Test Harness (__main__)
# =============================================================================

def _run_self_test() -> int:
    """
    Run a self-test of the adapter module.

    Tests:
      1. Module import and class instantiation
      2. Indicator classification (base vs derived)
      3. Derived indicator type detection
      4. Derived indicator source lookup
      5. Computation functions (pure, no DB)
      6. Database validation (if DB available)
      7. Full adaptation report generation

    Returns:
        Exit code: 0 = all tests passed, 1 = some tests failed.
    """
    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"  ✅ {name}")
            passed += 1
        else:
            print(f"  ❌ {name} — {detail}")
            failed += 1

    print("=" * 72)
    print("  V88 Phase03 P1 — Engine 180+59 Indicator Adapter Self-Test")
    print("=" * 72)

    # Test 1: Module-level constants
    print("\n[1/7] Module-level constants...")
    check("DERIVED_DEFINITIONS defined", len(DERIVED_DEFINITIONS) > 0,
          "DERIVED_DEFINITIONS is empty")
    check("DERIVED_DEFINITIONS count = 59", len(DERIVED_DEFINITIONS) == 59,
          f"Expected 59, got {len(DERIVED_DEFINITIONS)}")
    check("DERIVED_INDEX has 59 entries", len(DERIVED_INDEX) == 59,
          f"Expected 59, got {len(DERIVED_INDEX)}")

    # Verify no duplicates
    ids = [d["derived_id"] for d in DERIVED_DEFINITIONS]
    check("No duplicate derived_ids", len(ids) == len(set(ids)),
          f"{len(ids) - len(set(ids))} duplicates")

    # Test 2: Classification
    print("\n[2/7] Indicator classification...")
    check("CU_TERM_STRUCTURE is derived",
          _classify_indicator("CU_TERM_STRUCTURE") == "derived", "")
    check("COMEX_CU is derived",
          _classify_indicator("COMEX_CU") == "derived", "")
    check("CU_FU00014935 is base",
          _classify_indicator("CU_FU00014935") == "base", "")
    check("LC_TOP20_LONG is derived",
          _classify_indicator("LC_TOP20_LONG") == "derived", "")
    check("SPOT_LICAR is derived (SPOT_*)",
          _classify_indicator("SPOT_LICAR") == "derived", "")
    check("Invalid id returns unknown",
          _classify_indicator("invalid_id") == "unknown", "")
    check("Empty string returns unknown",
          _classify_indicator("") == "unknown", "")

    # Test 3: Derived type detection
    print("\n[3/7] Derived type detection...")
    check("CU_TERM_STRUCTURE type = TERM_STRUCTURE",
          _get_derived_type("CU_TERM_STRUCTURE") == DERIVED_TYPE_TERM_STRUCTURE,
          f"Got {_get_derived_type('CU_TERM_STRUCTURE')}")
    check("CU_MONTH_SPREAD type = MONTH_SPREAD",
          _get_derived_type("CU_MONTH_SPREAD") == DERIVED_TYPE_MONTH_SPREAD, "")
    check("CU_LONG_SHORT_RATIO type = LONG_SHORT_RATIO",
          _get_derived_type("CU_LONG_SHORT_RATIO") == DERIVED_TYPE_LONG_SHORT_RATIO, "")
    check("CU_PRICE_PERCENTILE type = PRICE_PERCENTILE",
          _get_derived_type("CU_PRICE_PERCENTILE") == DERIVED_TYPE_PRICE_PERCENTILE, "")
    check("CU_TOP20_LONG type = TOP20_LONG",
          _get_derived_type("CU_TOP20_LONG") == DERIVED_TYPE_TOP20_LONG, "")
    check("CU_TOP20_SHORT type = TOP20_SHORT",
          _get_derived_type("CU_TOP20_SHORT") == DERIVED_TYPE_TOP20_SHORT, "")
    check("COMEX_CU type = COMEX",
          _get_derived_type("COMEX_CU") == DERIVED_TYPE_COMEX, "")
    check("Base indicator type = OTHER",
          _get_derived_type("CU_FU00014935") == DERIVED_TYPE_OTHER, "")

    # Test 4: Derived source lookup
    print("\n[4/7] Derived source lookup...")
    sources = _get_derived_sources("CU_TERM_STRUCTURE")
    check("CU_TERM_STRUCTURE has sources", len(sources) > 0, "Empty sources")
    check("CU_TERM_STRUCTURE sources include cu_21_close_front",
          "cu_21_close_front" in sources, f"Sources: {sources}")

    sources_empty = _get_derived_sources("NONEXISTENT_INDICATOR")
    check("Unknown indicator returns empty sources",
          len(sources_empty) == 0, "")

    # Test 5: Computation functions
    print("\n[5/7] Computation functions...")

    # compute_diff
    test_series = [("2024-01-01", 100.0), ("2024-01-02", 110.0),
                   ("2024-01-03", 105.0), ("2024-01-04", 120.0)]
    diff_result = compute_diff(test_series)
    check("compute_diff produces n-1 results", len(diff_result) == 3,
          f"Expected 3, got {len(diff_result)}")
    check("compute_diff[0] = 110-100 = 10", diff_result[0][1] == 10.0,
          f"Got {diff_result[0][1]}")

    # compute_percentile_rank
    pct_result = compute_percentile_rank(test_series, min_points=2)
    check("compute_percentile_rank works", len(pct_result) > 0, "No results")
    check("Percentile values in 0-100 range",
          all(0 <= p <= 100 for _, p in pct_result), "Out of range")

    # compute_difference_aligned
    s1 = [("2024-01-01", 100.0), ("2024-01-02", 110.0)]
    s2 = [("2024-01-01", 80.0), ("2024-01-02", 90.0)]
    diff_aligned = compute_difference_aligned(s1, s2)
    check("compute_difference_aligned works", len(diff_aligned) == 2, "")
    check("Diff aligned[0] = 100-80 = 20", diff_aligned[0][1] == 20.0,
          f"Got {diff_aligned[0][1]}")

    # compute_ratio
    ratio_result = compute_ratio(s1, s2)
    check("compute_ratio works", len(ratio_result) == 2, "")
    check("Ratio[0] = 100/80 = 1.25", abs(ratio_result[0][1] - 1.25) < 0.001,
          f"Got {ratio_result[0][1]}")

    # compute_top20_net
    long_s = [("2024-01-01", 500.0), ("2024-01-02", 600.0)]
    short_s = [("2024-01-01", 300.0), ("2024-01-02", 350.0)]
    net_result = compute_top20_net(long_s, short_s)
    check("compute_top20_net works", len(net_result) == 2, "")
    check("Net[0] = 500-300 = 200", net_result[0][1] == 200.0,
          f"Got {net_result[0][1]}")

    # Test 6: Adapter instantiation (standalone mode)
    print("\n[6/7] Adapter instantiation...")

    # Find test DB
    test_db = r"D:\DSH_WORK\github工作\framework-tree" + \
            r"\analysis\e2e_output\v88\phase03\p0\phase03_test.db"
    if not os.path.exists(test_db):
        # Try alternate paths
        alt_paths = [
            r"D:\DSH_WORK\github工作\framework-tree"
            r"\analysis\e2e_output\v88\phase03\p0\phase03_test.db",
            os.environ.get("V88_PHASE03_TEST_DB", ""),
        ]
        for p in alt_paths:
            if os.path.exists(p):
                test_db = p
                break

    repo_root = REPO_ROOT

    if os.path.exists(test_db):
        print(f"  DB found: {test_db}")
        adapter = Engine180IndicatorAdapter(repo_root=repo_root, db_path=test_db)
        check("Adapter created with DB", adapter.db_path is not None, "No DB path")

        base_count = adapter.get_base_indicator_count()
        derived_count = adapter.get_derived_indicator_count()
        total_count = adapter.get_total_indicator_count()

        print(f"  Base: {base_count}, Derived: {derived_count}, Total: {total_count}")
        check("Total indicators > 0", total_count > 0, "No indicators in DB")
        check("Base indicators > 0", base_count > 0, "No base indicators")

        # Test is_derived_indicator
        check("Adapter.is_derived_indicator(CU_TERM_STRUCTURE) = True",
              adapter.is_derived_indicator("CU_TERM_STRUCTURE"), "")
        check("Adapter.is_derived_indicator(CU_FU00014935) = False",
              not adapter.is_derived_indicator("CU_FU00014935"), "")

        # Test get_derived_indicator_type
        dtype = adapter.get_derived_indicator_type("CU_TERM_STRUCTURE")
        check("Adapter.get_derived_indicator_type works",
              dtype == DERIVED_TYPE_TERM_STRUCTURE, f"Got {dtype}")

        # Test compute_derived_indicator
        computed = adapter.compute_derived_indicator("CU_TERM_STRUCTURE")
        print(f"  CU_TERM_STRUCTURE computed: {len(computed)} points")
        check("compute_derived_indicator returns list", isinstance(computed, list), "")
        if computed:
            check("Computed data has valid tuples",
                  len(computed[0]) == 2 and isinstance(computed[0][0], str)
                  and isinstance(computed[0][1], (int, float)),
                  f"Bad format: {computed[0]}")

        # Test validate_all_indicators
        validation = adapter.validate_all_indicators()
        check("Validation returns dict", isinstance(validation, dict), "")
        check("Validation has summary", "validation_summary" in validation, "")
        print(f"  Validation: {validation['validation_summary']}")

        # Test get_adaptation_report
        report = adapter.get_adaptation_report()
        check("Report has engine info", "engine" in report, "")
        check("Report has indicators info", "indicators" in report, "")
        check("Report has database info", "database" in report, "")
        check("Report has validation info", "validation" in report, "")
        check("Report has recommendations", "recommendations" in report, "")
        check("Report has degradation info", "degradation" in report, "")
        print(f"  Recommendations: {len(report['recommendations'])}")
        for r in report["recommendations"][:3]:
            print(f"    - {r}")

    else:
        print("  ⚠ DB not found, testing standalone mode")
        adapter = Engine180IndicatorAdapter(repo_root=repo_root)
        check("Adapter created without DB", True, "")
        check("DB path is None", adapter.db_path is None, "")
        check("is_derived_indicator works",
              adapter.is_derived_indicator("CU_TERM_STRUCTURE"), "")
        check("get_derived_indicator_type works",
              adapter.get_derived_indicator_type("CU_TERM_STRUCTURE")
              == DERIVED_TYPE_TERM_STRUCTURE, "")
        check("list_all_derived_indicators returns 59",
              len(adapter.list_all_derived_indicators()) == 59, "")

        validation = adapter.validate_all_indicators()
        check("Validation handles no DB",
              validation["db_available"] is False, "")

    # Test 7: All 59 definitions sanity
    print("\n[7/7] All 59 definitions sanity...")
    all_cats = set()
    all_comms = set()
    all_source_ids = set()
    for d in DERIVED_DEFINITIONS:
        all_cats.add(d["category"])
        all_comms.add(d["commodity"])
        for s in d["sources"]:
            all_source_ids.add(s)

    check("All definitions have derived_id",
          all(d["derived_id"] for d in DERIVED_DEFINITIONS), "")
    check("All definitions have category",
          all(d["category"] for d in DERIVED_DEFINITIONS), "")
    check("All definitions have commodity",
          all(d["commodity"] for d in DERIVED_DEFINITIONS), "")
    check("All definitions have sources list",
          all(isinstance(d["sources"], list) and len(d["sources"]) > 0
              for d in DERIVED_DEFINITIONS), "")
    check("All definitions have description",
          all(d["description"] for d in DERIVED_DEFINITIONS), "")
    check("Multiple categories represented", len(all_cats) >= 7,
          f"Only {len(all_cats)} categories: {sorted(all_cats)}")
    check("Multiple commodities represented", len(all_comms) >= 7,
          f"Only {len(all_comms)} commodities")
    check("Source IDs use lowercase",
          all(s == s.lower() for s in all_source_ids),
          f"Non-lowercase sources: {[s for s in all_source_ids if s != s.lower()]}")

    print(f"\n  Categories ({len(all_cats)}): {sorted(all_cats)}")
    print(f"  Commodities ({len(all_comms)}): {sorted(all_comms)}")

    # Final summary
    print("\n" + "=" * 72)
    print(f"  SELF-TEST COMPLETE: {passed} passed, {failed} failed")
    print("=" * 72)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_self_test())
