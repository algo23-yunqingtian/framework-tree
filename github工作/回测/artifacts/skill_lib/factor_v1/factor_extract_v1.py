#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FACTOR_EXTRACT_V1 — Factor Extraction Skill (V1.0.0)
=====================================================

Extracts 7 market factors from long-form commodity futures data CSVs.

Input:  Long-form CSV with columns: date, symbol, indicator, value, source
Output: Wide-form factor CSV + metadata JSON

Supported Factors (7):
  1. spread_cs            = CLOSE - SETTLE
  2. oi_level             = OI
  3. oi_change_1d         = OI(t) - OI(t-1)
  4. oi_change_rate_7d    = (OI(t) - OI(t-7)) / OI(t-7) * 100
  5. spread_pct           = (CLOSE - SETTLE) / SETTLE * 100
  6. contract_switch_flag = 1 if |CLOSE(t) - CLOSE(t-1)| / CLOSE(t-1) > 0.02
  7. momentum_20d         = (CLOSE(t) - CLOSE(t-20)) / CLOSE(t-20) * 100

Version: V1.0.0 (LOCKED)
Created: 2026-10-19
Locked by: DSHC-SKILL-FACTOR01

Usage Examples
--------------

  # Basic extraction with date range
  python artifacts/skill_lib/factor_v1/factor_extract_v1.py \\
      --csv output_sample/wdf_sample_metals_aligned.csv \\
      --start 2025-01-02 --end 2026-08-26 \\
      --outdir artifacts/skill_lib/factor_v1/output/

  # Filter to specific symbols
  python artifacts/skill_lib/factor_v1/factor_extract_v1.py \\
      --csv output_sample/wdf_sample_metals_aligned.csv \\
      --symbols CU.SHF,ZN.SHF,PB.SHF,AL.SHF,SN.SHF,NI.SHF \\
      --start 2025-01-02 --end 2026-08-26 \\
      --outdir artifacts/skill_lib/factor_v1/output/

  # All symbols, auto-blacklist (LC.GFE, LC.SHF)
  python artifacts/skill_lib/factor_v1/factor_extract_v1.py \\
      --csv output_sample/wdf_sample_metals_aligned.csv \\
      --outdir artifacts/skill_lib/factor_v1/output/
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ============================================================================
# Version Constants (V1 LOCKED — DO NOT MODIFY)
# ============================================================================

SKILL_ID: str = "FACTOR_EXTRACT_V1"
VERSION: str = "1.0.0"
VERSION_LOCKED: bool = True
CREATED_AT: str = "2026-10-19"
LOCKED_BY: str = "DSHC-SKILL-FACTOR01"

BLACKLIST: List[str] = ["LC.GFE", "LC.SHF"]
REQUIRED_INDICATORS: List[str] = ["CLOSE", "OI", "SETTLE"]
OPTIONAL_INDICATORS: List[str] = ["VOL"]
MIN_TRADING_DAYS: int = 20

REQUIRED_COLUMNS: List[str] = ["date", "symbol", "indicator", "value", "source"]

# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FACTOR_EXTRACT_V1")


# ============================================================================
# Factor Definitions
# ============================================================================

FACTOR_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "spread_cs",
        "name": "Cross-sectional Spread",
        "formula": "CLOSE - SETTLE",
        "indicators": ["CLOSE", "SETTLE"],
    },
    {
        "id": "oi_level",
        "name": "Open Interest Level",
        "formula": "OI",
        "indicators": ["OI"],
    },
    {
        "id": "oi_change_1d",
        "name": "1-Day OI Change",
        "formula": "OI(t) - OI(t-1)",
        "indicators": ["OI"],
    },
    {
        "id": "oi_change_rate_7d",
        "name": "7-Day OI Change Rate %",
        "formula": "(OI(t) - OI(t-7)) / OI(t-7) * 100",
        "indicators": ["OI"],
    },
    {
        "id": "spread_pct",
        "name": "Spread Percentage %",
        "formula": "(CLOSE - SETTLE) / SETTLE * 100",
        "indicators": ["CLOSE", "SETTLE"],
    },
    {
        "id": "contract_switch_flag",
        "name": "Contract Switch Flag",
        "formula": "abs(CLOSE(t)-CLOSE(t-1))/CLOSE(t-1) > 0.02",
        "indicators": ["CLOSE"],
    },
    {
        "id": "momentum_20d",
        "name": "20-Day Momentum %",
        "formula": "(CLOSE(t) - CLOSE(t-20)) / CLOSE(t-20) * 100",
        "indicators": ["CLOSE"],
    },
]


# ============================================================================
# Data Quality Diagnostics
# ============================================================================

class DataQualityReport:
    """Collects data quality diagnostics during processing."""

    def __init__(self) -> None:
        self.date_misalignment: List[Dict[str, str]] = []
        self.pk_duplicates: List[Dict[str, str]] = []
        self.null_values: List[Dict[str, str]] = []
        self.symbol_skipped: List[str] = []
        self.symbol_date_count: Dict[str, int] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date_misalignment": self.date_misalignment,
            "pk_duplicates": self.pk_duplicates,
            "null_values": self.null_values,
            "symbol_skipped": self.symbol_skipped,
            "symbol_date_count": self.symbol_date_count,
        }


def check_primary_key_duplicates(
    df: pd.DataFrame, report: DataQualityReport
) -> pd.DataFrame:
    """Detect and log primary key (date, symbol, indicator) duplicates."""
    dupes = df[df.duplicated(subset=["date", "symbol", "indicator"], keep=False)]
    if not dupes.empty:
        dupes_summary = (
            dupes.groupby(["date", "symbol", "indicator"])
            .size()
            .reset_index(name="count")
        )
        for _, row in dupes_summary.iterrows():
            report.pk_duplicates.append(
                {
                    "date": str(row["date"]),
                    "symbol": str(row["symbol"]),
                    "indicator": str(row["indicator"]),
                    "count": int(row["count"]),
                }
            )
        logger.warning(
            "Found %d primary key duplicate groups (%d total rows)",
            len(dupes_summary),
            len(dupes),
        )
        # Keep first occurrence
        df = df.drop_duplicates(subset=["date", "symbol", "indicator"], keep="first")
    else:
        logger.info("No primary key duplicates found.")
    return df


def check_null_values(
    df: pd.DataFrame, report: DataQualityReport
) -> None:
    """Detect and log rows with null values in required columns."""
    for col in ["date", "symbol", "indicator", "value"]:
        nulls = df[df[col].isna()]
        if not nulls.empty:
            for _, row in nulls.iterrows():
                report.null_values.append(
                    {
                        "column": col,
                        "date": str(row.get("date", "N/A")),
                        "symbol": str(row.get("symbol", "N/A")),
                        "indicator": str(row.get("indicator", "N/A")),
                    }
                )
    if report.null_values:
        logger.warning("Found %d rows with null values.", len(report.null_values))
    else:
        logger.info("No null values detected in required columns.")


def check_date_misalignment(
    df: pd.DataFrame, report: DataQualityReport
) -> None:
    """Detect date misalignment: symbols should share the same trading calendar.

    Compares per-symbol trading date sets and reports dates present for one
    symbol but missing for others.
    """
    if df.empty:
        return

    symbol_dates: Dict[str, set] = {}
    for symbol, group in df.groupby("symbol"):
        dates = set(group["date"].astype(str))
        symbol_dates[str(symbol)] = dates
        report.symbol_date_count[str(symbol)] = len(dates)

    if len(symbol_dates) < 2:
        return

    # Find the most common dates as a reference set
    all_dates: List[str] = []
    for dates in symbol_dates.values():
        all_dates.extend(dates)
    if not all_dates:
        return

    from collections import Counter

    date_counter = Counter(all_dates)
    total_symbols = len(symbol_dates)
    # A date that appears for at least 50% of symbols is "expected"
    threshold = total_symbols * 0.5
    expected_dates = {d for d, cnt in date_counter.items() if cnt >= threshold}

    for symbol, dates in symbol_dates.items():
        missing = expected_dates - dates
        extra = dates - expected_dates
        for d in sorted(missing):
            report.date_misalignment.append(
                {
                    "symbol": symbol,
                    "missing_date": d,
                    "reason": "date present for other symbols but missing for this one",
                }
            )
        for d in sorted(extra):
            report.date_misalignment.append(
                {
                    "symbol": symbol,
                    "extra_date": d,
                    "reason": "date present only for this symbol, not for others",
                }
            )

    if report.date_misalignment:
        logger.warning(
            "Found %d date misalignment entries across %d symbols.",
            len(report.date_misalignment),
            len(symbol_dates),
        )
    else:
        logger.info("All symbols share consistent trading calendar.")


# ============================================================================
# Data Loading
# ============================================================================

def load_long_form_csv(
    csv_path: str,
    report: DataQualityReport,
) -> pd.DataFrame:
    """Load and validate a long-form CSV file.

    Expected columns: date, symbol, indicator, value, source
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    logger.info("Loading CSV: %s", csv_path)
    df = pd.read_csv(csv_path, comment="#", dtype={"date": str, "symbol": str, "indicator": str, "source": str})

    # Validate required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV missing required columns: {missing_cols}. Found: {list(df.columns)}")

    # Ensure value is numeric
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        bad_rows = df[df["date"].isna()]
        logger.warning("Found %d rows with unparseable dates.", len(bad_rows))
        df = df.dropna(subset=["date"])

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    logger.info(
        "Loaded %d rows, %d symbols, date range: %s to %s",
        len(df),
        df["symbol"].nunique(),
        df["date"].min(),
        df["date"].max(),
    )

    # Run data quality checks
    check_primary_key_duplicates(df, report)
    check_null_values(df, report)
    check_date_misalignment(df, report)

    return df


# ============================================================================
# Factor Computation
# ============================================================================

def pivot_to_wide(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Pivot long-form data to wide form: one row per (date, symbol),
    with each indicator as a column.
    """
    wide = df.pivot_table(
        index=["date", "symbol"],
        columns="indicator",
        values="value",
        aggfunc="first",
    ).reset_index()

    # Ensure expected indicator columns exist
    for ind in REQUIRED_INDICATORS + OPTIONAL_INDICATORS:
        if ind not in wide.columns:
            wide[ind] = np.nan
            logger.warning("Indicator '%s' not found in data; filled with NaN.", ind)

    return wide


def compute_factors(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute all 7 factors for each (date, symbol) row.

    Parameters
    ----------
    df : pd.DataFrame
        Wide-form DataFrame with columns: date, symbol, CLOSE, SETTLE, OI, VOL

    Returns
    -------
    pd.DataFrame
        Wide-form DataFrame with all factor columns added.
    """
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    # Ensure numeric types
    for col in ["CLOSE", "SETTLE", "OI", "VOL"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Group by symbol for shift operations
    df["spread_cs"] = df["CLOSE"] - df["SETTLE"]

    df["oi_level"] = df["OI"]

    df["oi_change_1d"] = df.groupby("symbol")["OI"].diff(1)

    df["oi_change_rate_7d"] = (
        (df.groupby("symbol")["OI"].shift(0) - df.groupby("symbol")["OI"].shift(7))
        / df.groupby("symbol")["OI"].shift(7)
        * 100.0
    )

    df["spread_pct"] = (df["CLOSE"] - df["SETTLE"]) / df["SETTLE"] * 100.0

    close_pct_change = (
        (df.groupby("symbol")["CLOSE"].shift(0) - df.groupby("symbol")["CLOSE"].shift(1))
        / df.groupby("symbol")["CLOSE"].shift(1)
        * 100.0
    )
    df["contract_switch_flag"] = np.where(close_pct_change.abs() > 2.0, 1, 0)

    df["momentum_20d"] = (
        (df.groupby("symbol")["CLOSE"].shift(0) - df.groupby("symbol")["CLOSE"].shift(20))
        / df.groupby("symbol")["CLOSE"].shift(20)
        * 100.0
    )

    # Fill contract_switch_flag NaN (first row per symbol) with 0
    df["contract_switch_flag"] = df["contract_switch_flag"].fillna(0).astype(int)

    return df


# ============================================================================
# Output Generation
# ============================================================================

def write_outputs(
    factor_df: pd.DataFrame,
    report: DataQualityReport,
    outdir: str,
    source_csv: str,
    symbols_used: List[str],
    date_range: Tuple[str, str],
) -> Tuple[str, str]:
    """Write factor data CSV and metadata JSON to the output directory.

    Returns
    -------
    Tuple[str, str]
        (csv_path, json_path) of the written files.
    """
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    # --- Factor CSV ---
    output_columns = [
        "date",
        "symbol",
        "CLOSE",
        "SETTLE",
        "OI",
        "VOL",
        "spread_cs",
        "oi_level",
        "oi_change_1d",
        "oi_change_rate_7d",
        "spread_pct",
        "contract_switch_flag",
        "momentum_20d",
    ]

    # Only keep columns that exist in the dataframe
    existing_columns = [c for c in output_columns if c in factor_df.columns]
    csv_output = factor_df[existing_columns].copy()
    csv_path = out_path / "factors_output.csv"
    csv_output.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info("Factor CSV written: %s (%d rows, %d cols)", csv_path, len(csv_output), len(existing_columns))

    # --- Metadata JSON ---
    meta = {
        "skill_id": SKILL_ID,
        "version": VERSION,
        "version_locked": VERSION_LOCKED,
        "created_at": CREATED_AT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_csv": str(source_csv),
        "symbols_used": symbols_used,
        "symbols_blacklisted": BLACKLIST,
        "date_range": {
            "start": date_range[0],
            "end": date_range[1],
        },
        "output_columns": existing_columns,
        "factor_count": len(FACTOR_DEFINITIONS),
        "factors": FACTOR_DEFINITIONS,
        "data_quality": report.to_dict(),
        "row_count": int(len(csv_output)),
        "row_per_symbol": {
            s: int(count) for s, count in zip(csv_output["symbol"].unique(), csv_output.groupby("symbol").size().values)
        },
        "input_format": {
            "type": "long_form_csv",
            "columns": REQUIRED_COLUMNS,
            "delimiter": ",",
        },
        "output_format": {
            "type": "wide_form_csv",
            "columns": existing_columns,
            "delimiter": ",",
        },
        "data_requirements": {
            "required_indicators": REQUIRED_INDICATORS,
            "optional_indicators": OPTIONAL_INDICATORS,
            "min_trading_days": MIN_TRADING_DAYS,
        },
        "constraints": {
            "wind_api_calls": 0,
            "offline_only": True,
            "f01_script_locked": True,
            "f01_script_version": "v1.0 @ 593d688",
            "f01_script_params_only": True,
        },
    }

    json_path = out_path / "factors_metadata.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logger.info("Metadata JSON written: %s", json_path)

    return str(csv_path), str(json_path)


# ============================================================================
# Main Pipeline
# ============================================================================

def extract_factors(
    csv_path: str,
    symbols: Optional[List[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    outdir: str = "artifacts/skill_lib/factor_v1/output/",
) -> Tuple[pd.DataFrame, DataQualityReport, List[str]]:
    """Run the complete factor extraction pipeline.

    Parameters
    ----------
    csv_path : str
        Path to the long-form CSV file.
    symbols : list of str, optional
        Whitelist of symbols to include. If None, all symbols (minus blacklist) are used.
    start : str, optional
        Start date filter (YYYY-MM-DD). Inclusive.
    end : str, optional
        End date filter (YYYY-MM-DD). Inclusive.
    outdir : str
        Output directory path.

    Returns
    -------
    Tuple[pd.DataFrame, DataQualityReport, List[str]]
        (factor_df, report, list_of_output_paths)
    """
    logger.info("=" * 60)
    logger.info("FACTOR_EXTRACT_V1 v%s (LOCKED=%s)", VERSION, VERSION_LOCKED)
    logger.info("=" * 60)

    report = DataQualityReport()

    # 1. Load and validate data
    df = load_long_form_csv(csv_path, report)

    # 2. Apply symbol whitelist
    all_symbols = sorted(df["symbol"].unique().tolist())
    if symbols is not None:
        symbols = [s.strip() for s in symbols if s.strip()]
        df = df[df["symbol"].isin(symbols)]
        logger.info("Applied symbol whitelist: %s", symbols)
    else:
        symbols = all_symbols
        logger.info("No symbol whitelist specified; using all %d symbols.", len(all_symbols))

    # 3. Apply blacklist
    before_count = len(df)
    df = df[~df["symbol"].isin(BLACKLIST)]
    skipped = [s for s in BLACKLIST if s in df["symbol"].unique()]
    report.symbol_skipped = skipped
    if skipped:
        logger.info("Blacklisted symbols skipped: %s", skipped)
    else:
        logger.info("No blacklisted symbols found in data.")

    if df.empty:
        raise ValueError("No data remaining after symbol filtering. Check --symbols parameter.")

    # 4. Apply date filters
    if start:
        df = df[df["date"] >= start]
        logger.info("Applied start date filter: >= %s", start)
    if end:
        df = df[df["date"] <= end]
        logger.info("Applied end date filter: <= %s", end)

    if df.empty:
        raise ValueError("No data remaining after date filtering. Check --start/--end parameters.")

    # 5. Determine effective date range and symbols
    date_min = df["date"].min()
    date_max = df["date"].max()
    used_symbols = sorted(df["symbol"].unique().tolist())
    logger.info(
        "Effective range: %s to %s | Symbols: %s",
        date_min,
        date_max,
        ", ".join(used_symbols),
    )

    # 6. Pivot to wide form
    wide_df = pivot_to_wide(df)
    logger.info(
        "Pivoted to %d rows (date, symbol pairs), %d columns",
        len(wide_df),
        len(wide_df.columns),
    )

    # 7. Compute factors
    factor_df = compute_factors(wide_df)
    logger.info("Computed %d factors for %d rows.", len(FACTOR_DEFINITIONS), len(factor_df))

    # 8. Write outputs
    out_paths = write_outputs(
        factor_df=factor_df,
        report=report,
        outdir=outdir,
        source_csv=csv_path,
        symbols_used=used_symbols,
        date_range=(date_min, date_max),
    )

    # 9. Summary
    logger.info("=" * 60)
    logger.info("EXTRACTION COMPLETE")
    logger.info("  Rows:        %d", len(factor_df))
    logger.info("  Symbols:     %s", ", ".join(used_symbols))
    logger.info("  Date range:  %s to %s", date_min, date_max)
    logger.info("  CSV output:  %s", out_paths[0])
    logger.info("  JSON output: %s", out_paths[1])
    if report.pk_duplicates:
        logger.info("  PK dupes:    %d groups", len(report.pk_duplicates))
    if report.null_values:
        logger.info("  Null vals:   %d", len(report.null_values))
    if report.date_misalignment:
        logger.info("  Misaligned:  %d entries", len(report.date_misalignment))
    logger.info("=" * 60)

    return factor_df, report, out_paths


# ============================================================================
# CLI Entry Point
# ============================================================================

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="factor_extract_v1.py",
        description=(
            "FACTOR_EXTRACT_V1 — Extract 7 market factors from long-form commodity data CSV. "
            "Version %s (LOCKED)." % VERSION
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --csv data/aligned.csv --symbols CU.SHF,ZN.SHF --outdir output/\n"
            "  %(prog)s --csv data/aligned.csv --start 2025-01-02 --end 2026-08-26\n"
            "  %(prog)s --csv data/aligned.csv\n"
        ),
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to input long-form CSV (columns: date,symbol,indicator,value,source)",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated symbol whitelist (e.g. CU.SHF,ZN.SHF,PB.SHF). Blacklist always applied.",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date filter (YYYY-MM-DD, inclusive)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date filter (YYYY-MM-DD, inclusive)",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="artifacts/skill_lib/factor_v1/output/",
        help="Output directory for factor CSV and metadata JSON (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point.

    Returns
    -------
    int
        Exit code: 0 on success, non-zero on failure.
    """
    args = parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse symbols
    symbols_list: Optional[List[str]] = None
    if args.symbols:
        symbols_list = [s.strip() for s in args.symbols.split(",") if s.strip()]

    try:
        extract_factors(
            csv_path=args.csv,
            symbols=symbols_list,
            start=args.start,
            end=args.end,
            outdir=args.outdir,
        )
        return 0
    except FileNotFoundError as e:
        logger.error("File error: %s", e)
        return 1
    except ValueError as e:
        logger.error("Data error: %s", e)
        return 2
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return 99


if __name__ == "__main__":
    sys.exit(main())
