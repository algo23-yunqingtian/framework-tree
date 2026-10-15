#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_import_jsonl.py - V88 Phase03-P0 JSONL指标数据导入脚本
================================================================
TASK_ID: V88_PHASE03_P0_R0_NAMESPACE_MAPPING_AND_CACHE_IMPORTER
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

用途:
  读取 data/db_export/ 下 JSONL 指标数据文件,
  按命名映射表转换命名, 批量写入 api_cache.db。

输入文件:
  data/db_export/series_{ZN,NI,SI,SN,LI}.jsonl
  每行格式: {"indicator_id":"zn_21_close_front","date":"2026-08-28","value":"26485"}

输出:
  scripts/api_cache.db (SQLite, series_cache + import_log 表)

用法:
  python db_import_jsonl.py                      # 正常导入
  python db_import_jsonl.py --dry-run            # 干跑模式(仅统计不写入)
  python db_import_jsonl.py --force              # 强制模式(清空后重新导入)
  python db_import_jsonl.py --output /path/db    # 自定义输出路径

约束:
  · 仅使用 Python 标准库 (sqlite3/json/os/sys/datetime/argparse/pathlib/logging)
  · 不修改仓库任何已有文件
  · 批量插入 (batch_size=1000)
  · INSERT OR IGNORE 处理主键冲突
  · 全 UTF-8 编码
  · BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY
"""

import os
import sys
import json
import sqlite3
import argparse
import logging
from datetime import datetime
from pathlib import Path

# =============================================================================
# 配置
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent.parent  # scripts→p0→phase03→v88→e2e_output→analysis→framework-tree

# JSONL 数据文件路径
JSONL_DIR = REPO_ROOT / "data" / "db_export"
JSONL_FILES = [
    "series_ZN.jsonl",
    "series_NI.jsonl",
    "series_SI.jsonl",
    "series_SN.jsonl",
    "series_LI.jsonl",
]

# 默认数据库路径
DEFAULT_DB_PATH = REPO_ROOT / "scripts" / "api_cache.db"

# 批次大小
BATCH_SIZE = 1000

# =============================================================================
# 指标命名映射表 (DSHB indicator_id → DSHE meta_chart indicator_id)
# =============================================================================

# --- 显式映射表: 已知指标的精确映射 ---
EXPLICIT_MAPPING = {
    # ---- CU (铜) ----
    "cu_21_close_front": "CU_FU00014941",
    "cu_21_openinterest": "CU_HOLD_OPEN",
    "cu_21_openinterest_longshort": "CU_LONG_SHORT_RATIO",
    "cu_22_premium": "CU_SPOT_PREMIUM",
    "cu_21_basis": "CU_BASIS",
    "cu_23_lme_close": "LME_CU",
    "cu_23_comex_close": "COMEX_CU",
    "cu_24_openinterest_volume": "CU_MONTH_SPREAD",
    "cu_25_profit_percentile": "CU_PRICE_PERCENTILE",
    "cu_25_profit": "CU_SMELTING_PROFIT",
    "cu_26_openinterest_top20_front": "CU_TOP20_LONG",
    "cu_26_openinterest": "CU_TOP20_SHORT",
    "cu_41_output": "CU_FU00014935",
    "cu_23_inv": "FU00014813",
    "cu_42_warrant_reg": "CU_WARRANT_INVENTORY",
    "cu_43_social_stock": "CU_SOCIAL_INV",
    "cu_321_util_capacity_util": "CU_UTILIZATION",
    "cu_25_tc_conc": "CU_COST_PERCENTILE",

    # ---- AL (铝) ----
    "al_00_close_front": "AL_FU00014934",
    "al_00_openinterest_front": "AL_HOLD_OPEN",
    "al_00_premium": "AL_SPOT_PREMIUM",
    "al_00_basis": "AL_BASIS",
    "al_00_lme_close": "LME_AL",
    "al_24_lme_spread": "AL_MONTH_SPREAD",
    "al_00_cost_percentile": "AL_PRICE_PERCENTILE",
    "al_25_profit": "AL_SMELTING_PROFIT",
    "al_26_long_top20": "AL_TOP20_LONG",
    "al_26_short_top20": "AL_TOP20_SHORT",

    # ---- PB (铅) ----
    "j21_close": "PB_FU00014946",
    "j21_oi": "PB_HOLD_OPEN",
    "j22_spot": "PB_SPOT_PREMIUM",
    "j22_premium": "PB_BASIS",
    "j23_lme_cash": "LME_PB",
    "j24_spread_m": "PB_MONTH_SPREAD",
    "j24_spread_s": "PB_TERM_STRUCTURE",
    "j25_smelt_cost": "PB_SMELTING_PROFIT",

    # ---- ZN (锌) ----
    "zn_21_close_front": "ZN_FU00014950",
    "zn_21_openinterest": "ZN_HOLD_OPEN",
    "zn_21_openinterest_2": "ZN_LONG_SHORT_RATIO",
    "zn_21_premium": "ZN_SPOT_PREMIUM",
    "zn_21_basis": "ZN_BASIS",
    "zn_23_lme_close": "LME_ZN",
    "zn_23_comex": "COMEX_ZN",
    "zn_24_term_struct": "ZN_MONTH_SPREAD",
    "zn_25_profit_percentile": "ZN_PRICE_PERCENTILE",
    "zn_25_profit": "ZN_SMELTING_PROFIT",
    "zn_26_openinterest_top20": "ZN_TOP20_LONG",
    "zn_26_openinterest": "ZN_TOP20_SHORT",

    # ---- NI (镍) ----
    "ni_21_close_front": "NI_FU00014982",
    "ni_21_openinterest_front": "NI_HOLD_OPEN",
    "ni_21_percentile_openinterest": "NI_LONG_SHORT_RATIO",
    "ni_21_premium": "NI_SPOT_PREMIUM",
    "ni_22_basis": "NI_BASIS",
    "ni_21_lme_price": "LME_NI",
    "ni_24_near_price": "NI_MONTH_SPREAD",
    "ni_25_percentile_price": "NI_PRICE_PERCENTILE",
    "ni_25_profit": "NI_SMELTING_PROFIT",
    "ni_26_openinterest_top20_front": "NI_TOP20_LONG",
    "ni_26_openinterest_top20_front_2": "NI_TOP20_SHORT",

    # ---- SN (锡) ----
    "sn_21_close_front": "SN_FU00014952",
    "sn_21_openinterest": "SN_HOLD_OPEN",
    "sn_21_openinterest_3": "SN_LONG_SHORT_RATIO",
    "sn_21_premium": "SN_SPOT_PREMIUM",
    "sn_21_basis": "SN_BASIS",
    "sn_23_lme_close": "LME_SN",
    "sn_22_premium": "SN_MONTH_SPREAD",
    "sn_71_cost_percentile": "SN_PRICE_PERCENTILE",
    "sn_72_tc": "SN_SMELTING_PROFIT",
    "sn_26_openinterest_top20": "SN_TOP20_LONG",
    "sn_26_openinterest_top20_2": "SN_TOP20_SHORT",

    # ---- LI (锂/LC) ----
    "li_21_close_front": "LC_FU00015030",
    "li_21_openinterest": "LC_HOLD_OPEN",
    "li_21_openinterest_longshort": "LC_LONG_SHORT_RATIO",
    "li_21_premium": "LC_SPOT_PREMIUM",
    "li_21_basis": "LC_BASIS",
    "li_21_close": "LME_LC",
    "li_22_premium": "SPOT_LICAR",
    "li_24_close_near": "LC_MONTH_SPREAD",
    "li_25_profit": "LC_SMELTING_PROFIT",
    "li_26_openinterest_top20": "LC_TOP20_LONG",
    "li_26_openinterest_top20_2": "LC_TOP20_SHORT",

    # ---- SI (硅) ----
    "si_21_close_front_industrial_si": "SI_FU00015015",
    "si_21_openinterest": "SI_HOLD_OPEN",
    "si_21_openinterest_longshort_indus": "SI_LONG_SHORT_RATIO",
    "si_21_warrant_industrial_si": "SI_SPOT_PREMIUM",
    "si_21_basis_industrial_si": "SI_BASIS",
    "si_25_close_front_polysilicon": "LME_SI",
    "si_24_spot": "SPOT_IS",
    "si_23_close": "SI_MONTH_SPREAD",
    "si_25_profit_percentile_industrial": "SI_PRICE_PERCENTILE",
    "si_25_profit": "SI_SMELTING_PROFIT",
    "si_26_openinterest_top20": "SI_TOP20_LONG",
    "si_26_openinterest_top20_2": "SI_TOP20_SHORT",
}

# --- 品种映射 (小写前缀 → 大写代码) ---
COMMODITY_CODE_MAP = {
    "cu": "CU", "al": "AL", "pb": "PB", "zn": "ZN",
    "ni": "NI", "sn": "SN", "li": "LI", "si": "SI",
    "j": "PB",  # 铅 legacy 前缀
}

# --- 主连价格 FU 代码映射 (21_close_front 系列) ---
PRICE_FU_MAP = {
    "ZN": "FU00014950",
    "NI": "FU00014982",
    "SI": "FU00015015",
    "SN": "FU00014952",
    "LI": "FU00015030",
    "CU": "FU00014941",
    "AL": "FU00014934",
    "PB": "FU00014946",
}

# --- LME 品种代码 ---
LME_COMM_MAP = {
    "ZN": "ZN", "NI": "NI", "SI": "SI",
    "SN": "SN", "LI": "LC", "CU": "CU",
    "AL": "AL", "PB": "PB",
}


# =============================================================================
# 核心函数
# =============================================================================

def extract_commodity(indicator_id):
    """从 indicator_id 提取品种代码 (小写)"""
    if not indicator_id:
        return "unknown"
    parts = indicator_id.split("_")
    if not parts:
        return "unknown"
    code = parts[0].lower()
    # 处理 "j" (铅 legacy 前缀) → 统一返回小写品种代码
    return code


def get_mapped_id(indicator_id):
    """
    将 DSHB indicator_id 映射为 DSHE meta_chart indicator_id。

    双层映射:
      1. 显式映射表 (精确匹配)
      2. 模式映射函数 (处理变体指标)

    返回: 映射后的 meta_chart ID, 无映射时返回 None
    """
    if not indicator_id or not isinstance(indicator_id, str):
        return None

    # 第一层: 精确匹配
    if indicator_id in EXPLICIT_MAPPING:
        return EXPLICIT_MAPPING[indicator_id]

    # 第二层: 模式映射
    return pattern_map_indicator(indicator_id)


def pattern_map_indicator(indicator_id):
    """
    模式映射: 处理显式映射表未覆盖的变体指标。

    通过解析 indicator_id 结构, 按板块(21/22/23/...)和指标关键词
    进行规则匹配, 返回 DSHE meta_chart ID 或 None。
    """
    if not indicator_id:
        return None

    parts = indicator_id.split("_")
    if len(parts) < 2:
        return None

    comm_lower = parts[0]
    comm = COMMODITY_CODE_MAP.get(comm_lower)
    if not comm:
        return None

    section = parts[1] if len(parts) > 1 else ""
    metric_parts = parts[2:] if len(parts) > 2 else []
    metric_key = "_".join(metric_parts)

    # ---- 21 系列: 价格/持仓/基差/升贴水 ----
    if section == "21":
        if metric_key.startswith("close_front"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key == "close" or metric_key.startswith("close_"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key == "openinterest" or metric_key.startswith("openinterest"):
            return f"{comm}_HOLD_OPEN"
        elif metric_key in ("openinterest_front", "openinterest_longshort"):
            return f"{comm}_LONG_SHORT_RATIO"
        elif metric_key == "volume" or metric_key.startswith("volume"):
            return None  # 不在 meta_chart 中
        elif metric_key == "basis" or metric_key.startswith("basis"):
            return f"{comm}_BASIS"
        elif metric_key == "premium" or metric_key.startswith("premium"):
            return f"{comm}_SPOT_PREMIUM"
        elif metric_key == "warrant" or metric_key.startswith("warrant"):
            return f"{comm}_WARRANT"
        elif metric_key == "far_price" or metric_key == "far":
            return f"{comm}_FAR_PRICE"
        elif metric_key == "front_price" or metric_key.startswith("front_price"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key == "near_price" or metric_key == "near":
            return f"{comm}_NEAR_PRICE"
        elif "percentile" in metric_key:
            return f"{comm}_HOLD_PERCENTILE"
        elif metric_key == "lme_price" or metric_key == "lme":
            return f"LME_{comm}"
        elif metric_key.startswith("volume_top20"):
            return None  # volume, not in meta_chart
        elif metric_key == "import" or metric_key.startswith("import"):
            return f"{comm}_IMPORT"

    # ---- 22 系列: 现货升贴水 ----
    elif section == "22":
        if metric_key == "premium" or metric_key.startswith("premium"):
            return f"{comm}_SPOT_PREMIUM"
        elif metric_key == "basis" or metric_key.startswith("basis"):
            return f"{comm}_BASIS"
        elif metric_key == "price" or metric_key.startswith("price"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key == "import" or metric_key.startswith("import"):
            return f"{comm}_IMPORT"
        elif metric_key == "lme_inv" or metric_key == "lme_inventory":
            return f"LME_{comm}_INV"
        elif metric_key == "premium_ratio" or metric_key.startswith("premium_ratio"):
            return f"{comm}_SPOT_PREMIUM_RATIO"
        elif metric_key.startswith("warrant"):
            return f"{comm}_WARRANT"

    # ---- 23 系列: LME 价格 ----
    elif section == "23":
        if metric_key == "lme_close" or metric_key == "lme_cash":
            return f"LME_{comm}"
        elif metric_key == "lme_inv":
            return f"LME_{comm}_INV"
        elif metric_key == "close" or metric_key.startswith("close"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key == "comex" or metric_key == "comex_close":
            return f"COMEX_{comm}"
        elif metric_key == "premium" or metric_key.startswith("premium"):
            return f"LME_{comm}"  # LME 升贴水归入 LME 价格
        elif metric_key == "import" or metric_key.startswith("import"):
            return f"{comm}_IMPORT"

    # ---- 24 系列: 远期/近月 ----
    elif section == "24":
        if metric_key.startswith("far") or metric_key == "far_price":
            return f"{comm}_FAR_PRICE"
        elif metric_key.startswith("near") or metric_key == "near_price":
            return f"{comm}_NEAR_PRICE"
        elif metric_key == "basis" or metric_key.startswith("basis"):
            return f"{comm}_BASIS"
        elif metric_key.startswith("close"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key.startswith("warrant"):
            return f"{comm}_WARRANT"
        elif metric_key == "price" or metric_key == "price_2" or metric_key == "price_3":
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key.startswith("spot"):
            return f"{comm}_SPOT_PREMIUM"

    # ---- 25 系列: 冶炼利润/成本 ----
    elif section == "25":
        if metric_key == "profit" or metric_key.startswith("profit"):
            return f"{comm}_SMELTING_PROFIT"
        elif metric_key == "cost" or metric_key.startswith("cost"):
            return f"{comm}_REFINING_COST"
        elif metric_key == "tc" or metric_key.startswith("tc"):
            return f"{comm}_TC"
        elif metric_key == "price" or metric_key.startswith("price"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key.startswith("close"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif "percentile" in metric_key:
            return f"{comm}_PRICE_PERCENTILE"
        elif metric_key.startswith("recycle"):
            return f"{comm}_RECYCLE_OUTPUT"

    # ---- 26 系列: 持仓排名 ----
    elif section == "26":
        if "top20" in metric_key:
            # 区分多空
            if metric_key.endswith("_2") or metric_key.endswith("_short"):
                return f"{comm}_TOP20_SHORT"
            return f"{comm}_TOP20_LONG"
        elif "longshort" in metric_key or metric_key == "longshort":
            return f"{comm}_LONG_SHORT_RATIO"
        elif metric_key.startswith("openinterest"):
            return f"{comm}_HOLD_OPEN"
        elif "percentile" in metric_key:
            return f"{comm}_HOLD_PERCENTILE"
        elif metric_key.startswith("volume"):
            return None  # 不在 meta_chart 中

    # ---- 库存系列 (4x) ----
    elif section.startswith("4"):
        if metric_key == "inv" or metric_key.startswith("inv_"):
            return f"{comm}_SHFE_INV"
        elif metric_key == "social" or metric_key == "social_inv":
            return f"{comm}_SOCIAL_INV"
        elif metric_key.startswith("warrant"):
            return f"{comm}_WARRANT"
        elif metric_key == "lme_inv" or metric_key == "lme_warrant":
            return f"LME_{comm}_INV"
        elif "implicit" in metric_key:
            return f"{comm}_HIDDEN_INV"
        elif "plant" in metric_key:
            return f"{comm}_PLANT_INV"
        elif metric_key == "ratio" or metric_key == "premium":
            return f"{comm}_INV_RATIO"
        elif "days" in metric_key:
            return f"{comm}_INV_DAYS"
        elif metric_key == "inv":
            return f"{comm}_SHFE_INV"
        elif metric_key.startswith("import"):
            return f"{comm}_IMPORT"

    # ---- 供给系列 (3xx) ----
    elif section.startswith("3"):
        if metric_key.startswith("output"):
            if "recycle" in metric_key:
                return f"{comm}_RECYCLE_OUTPUT"
            return f"{comm}_REFINING_OUTPUT"
        elif metric_key.startswith("capacity"):
            if "recycle" in metric_key:
                if "util" in metric_key:
                    return f"{comm}_RECYCLE_UTIL"
                return f"{comm}_RECYCLE_CAPACITY"
            if "util" in metric_key:
                return f"{comm}_UTILIZATION"
            return f"{comm}_REFINING_CAPACITY"
        elif metric_key == "util" or metric_key == "utilization" or metric_key == "capacity_util":
            return f"{comm}_UTILIZATION"
        elif metric_key.startswith("import"):
            return f"{comm}_IMPORT"
        elif metric_key.startswith("export"):
            return f"{comm}_EXPORT"
        elif metric_key.startswith("tc"):
            return f"{comm}_TC"
        elif metric_key.startswith("profit"):
            return f"{comm}_SMELTING_PROFIT"
        elif metric_key.startswith("cost"):
            return f"{comm}_REFINING_COST"
        elif metric_key.startswith("util_"):
            return f"{comm}_UTILIZATION"
        elif metric_key == "inv":
            return f"{comm}_SHFE_INV"

    # ---- 需求系列 (5x) ----
    elif section.startswith("5"):
        if metric_key == "cons" or metric_key.startswith("cons"):
            return f"{comm}_CONSUMPTION"
        elif metric_key.startswith("output"):
            return f"{comm}_DOWNSTREAM_OUTPUT"
        elif metric_key == "util" or metric_key.startswith("util"):
            return f"{comm}_UTILIZATION"
        elif metric_key == "import":
            return f"{comm}_IMPORT"

    # ---- 进出口系列 (6x) ----
    elif section.startswith("6"):
        if metric_key.startswith("import"):
            return f"{comm}_IMPORT"
        elif metric_key.startswith("export"):
            return f"{comm}_EXPORT"
        elif "inv" in metric_key:
            return f"{comm}_SHFE_INV"
        elif metric_key.startswith("warrant"):
            return f"{comm}_WARRANT"
        elif metric_key.startswith("output"):
            return f"{comm}_EXPORT"

    # ---- 成本系列 (7x) ----
    elif section.startswith("7"):
        if metric_key.startswith("cost"):
            return f"{comm}_REFINING_COST"
        elif metric_key.startswith("profit"):
            return f"{comm}_SMELTING_PROFIT"
        elif metric_key.startswith("tc"):
            return f"{comm}_TC"
        elif metric_key.startswith("price"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None
        elif metric_key.startswith("output"):
            return f"{comm}_DOWNSTREAM_OUTPUT"
        elif metric_key.startswith("close"):
            fu = PRICE_FU_MAP.get(comm)
            return f"{comm}_{fu}" if fu else None

    return None


# =============================================================================
# 数据库操作
# =============================================================================

def setup_database(db_path):
    """初始化数据库表结构"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    # 性能优化
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_id TEXT NOT NULL,
            indicator_id_mapped TEXT,
            commodity TEXT NOT NULL,
            date TEXT NOT NULL,
            value REAL,
            source TEXT DEFAULT 'real',
            imported_at TEXT DEFAULT (datetime('now')),
            UNIQUE(indicator_id, date)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator ON series_cache(indicator_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicator_mapped ON series_cache(indicator_id_mapped)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commodity ON series_cache(commodity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON series_cache(date)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_time TEXT DEFAULT (datetime('now')),
            source_file TEXT,
            rows_read INTEGER,
            rows_inserted INTEGER,
            rows_skipped INTEGER,
            rows_error INTEGER,
            mapping_applied INTEGER,
            notes TEXT
        )
    """)

    conn.commit()
    return conn


def import_file(conn, filepath, dry_run=False):
    """
    流式导入单个 JSONL 文件。

    使用流式读取 + 批量写入, 避免将整个文件加载到内存。

    返回统计字典:
        {
            "file": str,
            "rows_read": int,
            "rows_inserted": int,
            "rows_skipped": int,
            "rows_error": int,
            "mapping_applied": int,
            "errors": list,
            "unique_indicators": set,
        }
    """
    fname = os.path.basename(str(filepath))
    logger = logging.getLogger(__name__)
    logger.info(f"[{fname}] 开始导入...")

    rows_read = 0
    rows_inserted = 0
    rows_skipped = 0
    rows_error = 0
    mapping_applied = 0
    errors = []
    unique_indicators = set()

    insert_sql = """
        INSERT OR IGNORE INTO series_cache
            (indicator_id, indicator_id_mapped, commodity, date, value, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    batch = []
    batch_count = 0

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                rows_read += 1
                line = line.strip()
                if not line:
                    continue

                # 解析 JSON
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    rows_error += 1
                    if rows_error <= 5:
                        errors.append(f"行{line_num}: JSON解析错误: {e}")
                    continue

                indicator_id = record.get("indicator_id")
                date_str = record.get("date")
                value_str = record.get("value")

                # 验证必填字段
                if not indicator_id or not date_str:
                    rows_error += 1
                    if rows_error <= 5:
                        errors.append(f"行{line_num}: 缺少 indicator_id 或 date")
                    continue

                unique_indicators.add(indicator_id)

                # 提取商品代码
                commodity = extract_commodity(indicator_id)

                # 映射 indicator_id
                mapped_id = get_mapped_id(indicator_id)
                if mapped_id:
                    mapping_applied += 1

                # 解析数值
                try:
                    value = float(value_str) if value_str is not None else None
                except (ValueError, TypeError):
                    rows_error += 1
                    if rows_error <= 5:
                        errors.append(f"行{line_num}: 数值解析失败: {value_str}")
                    continue

                # 构建插入元组 (mapped_id 为 None 时不插入, 保持 NULL)
                row = (indicator_id, mapped_id if mapped_id else None, commodity, date_str, value, "real")
                batch.append(row)

                # 批量插入
                if len(batch) >= BATCH_SIZE:
                    if not dry_run:
                        try:
                            # 先记录插入前的行数, 计算实际插入数
                            before = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                            conn.executemany(insert_sql, batch)
                            conn.commit()
                            after = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                            rows_inserted += (after - before)
                            batch_count += 1
                            rows_skipped = rows_read - rows_inserted - rows_error
                        except sqlite3.Error as e:
                            rows_error += len(batch)
                            logger.error(f"  Insert batch error: {e}")
                            conn.rollback()
                    else:
                        rows_inserted += len(batch)
                        batch_count += 1
                    batch = []

                    # 进度日志
                    if rows_read % 50000 < BATCH_SIZE:
                        logger.info(f"  [{fname}] 进度: 已处理 {rows_read:,} 行...")

            # 处理剩余批次
            if batch:
                if not dry_run:
                    try:
                        before = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                        conn.executemany(insert_sql, batch)
                        conn.commit()
                        after = conn.execute("SELECT COUNT(*) FROM series_cache").fetchone()[0]
                        rows_inserted += (after - before)
                    except sqlite3.Error as e:
                        rows_error += len(batch)
                        logger.error(f"  Insert batch error: {e}")
                        conn.rollback()
                else:
                    rows_inserted += len(batch)
                batch_count += 1
                rows_skipped = rows_read - rows_inserted - rows_error

    except Exception as e:
        errors.append(f"文件读取异常: {e}")
        logger.error(f"  [{fname}] 导入异常: {e}")

    # 写入导入日志
    if not dry_run:
        try:
            notes = "; ".join(errors[:10]) if errors else "ok"
            conn.execute(
                """INSERT INTO import_log
                   (import_time, source_file, rows_read, rows_inserted,
                    rows_skipped, rows_error, mapping_applied, notes)
                   VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)""",
                (fname, rows_read, rows_inserted, rows_skipped, rows_error, mapping_applied, notes)
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"  写入导入日志失败: {e}")

    # 打印摘要
    status = "✅" if rows_error == 0 else "⚠️"
    logger.info(
        f"{status} [{fname}] 读={rows_read:,} 插={rows_inserted:,} "
        f"跳={rows_skipped:,} 错={rows_error:,} 映射={mapping_applied:,}"
    )
    for err in errors[:5]:
        logger.warning(f"    {err}")
    if len(errors) > 5:
        logger.warning(f"    ... 及其他 {len(errors) - 5} 个错误")

    return {
        "file": fname,
        "rows_read": rows_read,
        "rows_inserted": rows_inserted,
        "rows_skipped": rows_skipped,
        "rows_error": rows_error,
        "mapping_applied": mapping_applied,
        "errors": errors,
        "unique_indicators": unique_indicators,
    }


# =============================================================================
# 报告
# =============================================================================

def print_summary(total_read, total_inserted, total_skipped, total_error, total_mapped, all_stats, dry_run):
    """打印导入摘要"""
    print("\n" + "=" * 60)
    print("  V88 Phase03-P0 JSONL Import Summary")
    print("=" * 60)
    if dry_run:
        print("  [DRY RUN] No data was written to database")

    print(f"  {'File':<25} {'Read':>8} {'Insert':>8} {'Skip':>8} {'Err':>6} {'Mapped':>8}")
    print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*6} {'-'*8}")
    for s in all_stats:
        print(f"  {s['file']:<25} {s['rows_read']:>8,} {s['rows_inserted']:>8,} {s['rows_skipped']:>8,} {s['rows_error']:>6,} {s['mapping_applied']:>8,}")
    print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*6} {'-'*8}")
    print(f"  {'Total':<25} {total_read:>8,} {total_inserted:>8,} {total_skipped:>8,} {total_error:>6,} {total_mapped:>8,}")
    print(f"  Insert rate:   {total_inserted/total_read*100:.1f}%" if total_read > 0 else "  Insert rate:   N/A")
    print("=" * 60)


# =============================================================================
# 主函数
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V88 Phase03-P0 JSONL Import Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python db_import_jsonl.py                  # Normal import
  python db_import_jsonl.py --dry-run        # Dry run (no DB writes)
  python db_import_jsonl.py --force          # Clear existing data and re-import
  python db_import_jsonl.py --output my.db   # Custom output path
        """
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode - no data written to DB")
    parser.add_argument("--force", action="store_true", help="Force re-import (clear existing data first)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_DB_PATH), help="Output database path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging output")
    args = parser.parse_args()

    # 日志配置
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")

    logger = logging.getLogger(__name__)
    db_path = Path(args.output)

    logger.info(f"Database path: {db_path}")
    logger.info(f"JSONL directory: {JSONL_DIR}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Force mode: {args.force}")
    logger.info("=" * 60)

    # 验证 JSONL 文件
    jsonl_paths = []
    for fname in JSONL_FILES:
        fpath = JSONL_DIR / fname
        if fpath.exists():
            fsize_mb = fpath.stat().st_size / 1024 / 1024
            logger.info(f"  Found: {fname} ({fsize_mb:.1f} MB)")
            jsonl_paths.append(fpath)
        else:
            logger.warning(f"  MISSING: {fname}")

    if not jsonl_paths:
        logger.error("No JSONL files found!")
        sys.exit(1)

    # 初始化数据库
    conn = setup_database(db_path)

    # Force 模式: 清除现有数据
    if args.force and not args.dry_run:
        logger.info("Force mode: clearing existing series_cache data...")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM series_cache")
        # 重置 AUTOINCREMENT 序列
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='series_cache'")
        except sqlite3.Error:
            pass  # sqlite_sequence 可能不存在
        conn.commit()
        logger.info("Existing data cleared.")

    # 导入每个 JSONL 文件
    all_stats = []
    all_indicators = set()
    start_time = datetime.now()

    for fpath in jsonl_paths:
        stats = import_file(conn, fpath, dry_run=args.dry_run)
        all_stats.append(stats)
        all_indicators.update(stats["unique_indicators"])

    # 总耗时
    elapsed = (datetime.now() - start_time).total_seconds()

    # 汇总统计
    total_read = sum(s["rows_read"] for s in all_stats)
    total_inserted = sum(s["rows_inserted"] for s in all_stats)
    total_skipped = sum(s["rows_skipped"] for s in all_stats)
    total_error = sum(s["rows_error"] for s in all_stats)
    total_mapped = sum(s["mapping_applied"] for s in all_stats)

    # 打印摘要
    print_summary(total_read, total_inserted, total_skipped, total_error, total_mapped, all_stats, args.dry_run)

    # 打印映射覆盖率
    mapped_count = sum(1 for ind in all_indicators if get_mapped_id(ind))
    unmapped_count = len(all_indicators) - mapped_count
    coverage_pct = mapped_count / len(all_indicators) * 100 if all_indicators else 0
    print(f"\n  Indicator coverage: {mapped_count}/{len(all_indicators)} mapped ({coverage_pct:.1f}%)")
    if unmapped_count > 0:
        unmapped_examples = sorted([i for i in all_indicators if not get_mapped_id(i)])[:10]
        print(f"  Unmapped examples: {', '.join(unmapped_examples)}")

    print(f"\n  Elapsed: {elapsed:.1f} seconds")

    # 最终数据库验证
    if not args.dry_run:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM series_cache")
        db_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT indicator_id) FROM series_cache")
        indicator_count = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(DISTINCT indicator_id_mapped) FROM series_cache WHERE indicator_id_mapped IS NOT NULL"
        )
        mapped_ind = cursor.fetchone()[0]
        cursor.execute("SELECT MIN(date), MAX(date) FROM series_cache")
        date_range = cursor.fetchone()

        print(f"\n  Database: {db_path}")
        print(f"  Total records:   {db_count:,}")
        print(f"  Unique indicators: {indicator_count:,}")
        print(f"  Mapped indicators: {mapped_ind:,}")
        print(f"  Date range:      {date_range[0]} ~ {date_range[1]}")

        # 按商品统计
        cursor.execute(
            "SELECT commodity, COUNT(*) FROM series_cache GROUP BY commodity ORDER BY commodity"
        )
        print("\n  Per-commodity distribution:")
        for row in cursor.fetchall():
            print(f"    {row[0]}: {row[1]:,} rows")

        # 按来源统计
        cursor.execute("SELECT source, COUNT(*) FROM series_cache GROUP BY source")
        print("\n  Per-source distribution:")
        for row in cursor.fetchall():
            print(f"    {row[0]}: {row[1]:,} rows")

    conn.close()
    logger.info("=" * 60)
    logger.info("Import complete.")


if __name__ == "__main__":
    main()
