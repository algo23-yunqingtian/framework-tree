#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_phase03_testdb.py — V88 Phase03 P0 DSHB Artifact Archive
==================================================================
TASK_ID: V88_PHASE03_P0_DSHB_ARTIFACT_ARCHIVE
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  One-click rebuild of phase03_test.db from source JSONL files.
  Guarantees 475,593 rows, 615 unique indicators, 0 primary key conflicts.

  This script is the canonical way to reproduce phase03_test.db on any node.
  It orchestrates:
    1. import_all_to_testdb.py  — import ALL JSONL (base 5 + CU/AL/PB supplement)
    2. verify_testdb.py          — integrity verification against expected baselines

Usage:
  python rebuild_phase03_testdb.py [--dry-run] [--db path/to/phase03_test.db]

Constraints:
  - NO_ZHIJI_API_CALL / NO_OVERWRITE / APPEND_ONLY
  - Pure Python standard library (no external dependencies)
  - Does NOT modify scripts/api_cache.db
  - Windows compatible (auto-sets PYTHONIOENCODING=utf-8)

Expected Output (verified baseline):
  Total rows:      475,593
  Unique indicators: 615
  Mapped indicators: 156
  Import errors:    0
  PK conflicts:     0
  Import files:     6 (series_ZN/NI/SI/SN/LI + cu_al_pb_supplement)

Author: DSHB Agent
Date:   2026-10-15
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
P0_DIR = SCRIPT_DIR.parent
DEFAULT_DB_PATH = P0_DIR / "phase03_test.db"

# Expected baseline values (from verified import on 2026-10-15)
EXPECTED_ROWS = 475593
EXPECTED_INDICATORS = 615
EXPECTED_MAPPED = 156
EXPECTED_ERRORS = 0
EXPECTED_PK_CONFLICTS = 0
EXPECTED_FILES = 6  # ZN/NI/SI/SN/LI + cu_al_pb_supplement

# =============================================================================
# Platform Setup
# =============================================================================

def setup_environment():
    """Configure environment for Windows GBK console compatibility."""
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"


def run_script(script_path, args=None, label=""):
    """Run a Python script as a subprocess and return exit code."""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print(f"\n{'='*72}")
    print(f"  Running: {label or script_path.name}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*72}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Print stdout
    if result.stdout:
        print(result.stdout)
    # Print stderr
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode


def check_jsonl_files():
    """Verify all required JSONL files exist in data/db_export/."""
    jsonl_dir = SCRIPT_DIR.parent.parent.parent.parent.parent / "data" / "db_export"
    required_files = [
        "series_ZN.jsonl",
        "series_NI.jsonl",
        "series_SI.jsonl",
        "series_SN.jsonl",
        "series_LI.jsonl",
        "cu_al_pb_supplement.jsonl",
    ]

    all_found = True
    total_size_mb = 0.0

    print("\n" + "=" * 72)
    print("  JSONL Source File Check")
    print("=" * 72)
    print(f"  JSONL directory: {jsonl_dir}")
    print()

    for fname in required_files:
        fpath = jsonl_dir / fname
        if fpath.exists():
            fsize_mb = fpath.stat().st_size / (1024 * 1024)
            total_size_mb += fsize_mb
            print(f"  ✅ FOUND:  {fname:<40} ({fsize_mb:6.1f} MB)")
        else:
            print(f"  ❌ MISSING: {fname:<40}")
            all_found = False

    print()
    print(f"  Total size: {total_size_mb:.1f} MB")
    print(f"  All files found: {all_found}")
    print("=" * 72)

    return all_found, required_files


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P0 — One-click rebuild phase03_test.db",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode (no actual writes)")
    parser.add_argument("--db", type=str,
                        default=str(DEFAULT_DB_PATH),
                        help="Path to phase03_test.db")
    args = parser.parse_args()

    setup_environment()

    db_path = Path(args.db)
    dry_run = args.dry_run

    print("=" * 72)
    print("  V88 Phase03 P0 · DSHB Artifact Archive")
    print("  TASK_ID: V88_PHASE03_P0_DSHB_ARTIFACT_ARCHIVE")
    print("  REBUILD phase03_test.db")
    print("=" * 72)
    print(f"  DB path:   {db_path}")
    print(f"  Dry run:   {dry_run}")
    print(f"  Expected:  {EXPECTED_ROWS:,} rows, {EXPECTED_INDICATORS} indicators")
    print(f"             {EXPECTED_MAPPED} mapped, {EXPECTED_ERRORS} errors")
    print(f"             {EXPECTED_PK_CONFLICTS} PK conflicts")

    # Step 1: Verify source files
    print("\n" + "#" * 72)
    print("#  STEP 1: Verify JSONL source files")
    print("#" * 72)
    all_found, required_files = check_jsonl_files()
    if not all_found:
        print("\n❌ FATAL: Missing JSONL files. Cannot proceed.")
        sys.exit(1)

    # Step 2: Clean existing DB (if not dry run)
    if not dry_run and db_path.exists():
        print(f"\n  Removing existing DB: {db_path}")
        db_path.unlink()
        print(f"  ✅ Removed")
    elif dry_run:
        print(f"\n  [DRY RUN] Would remove existing DB: {db_path}")

    # Step 3: Import all JSONL
    print("\n" + "#" * 72)
    print("#  STEP 2: Import ALL JSONL into phase03_test.db")
    print("#" * 72)
    import_script = SCRIPT_DIR / "import_all_to_testdb.py"
    import_args = ["--db", str(db_path)]
    if dry_run:
        import_args.append("--dry-run")
    ret = run_script(import_script, import_args, "Import all JSONL")
    if ret != 0:
        print(f"\n❌ FATAL: Import failed with exit code {ret}")
        sys.exit(1)

    if dry_run:
        print("\n" + "=" * 72)
        print("  [DRY RUN COMPLETE] No changes made.")
        print("=" * 72)
        sys.exit(0)

    # Step 4: Verify
    print("\n" + "#" * 72)
    print("#  STEP 3: Verify phase03_test.db integrity")
    print("#" * 72)
    verify_script = SCRIPT_DIR / "verify_testdb.py"
    verify_args = ["--db", str(db_path)]
    ret = run_script(verify_script, verify_args, "Verify test DB")
    if ret != 0:
        print(f"\n❌ FATAL: Verification failed with exit code {ret}")
        sys.exit(1)

    # Step 5: Final check
    print("\n" + "=" * 72)
    print("  REBUILD COMPLETE")
    print("=" * 72)
    print(f"  Database: {db_path}")
    print(f"  Expected: {EXPECTED_ROWS:,} rows | {EXPECTED_INDICATORS} indicators")
    print(f"  Expected: {EXPECTED_MAPPED} mapped | {EXPECTED_ERRORS} errors")
    print(f"  Expected: {EXPECTED_PK_CONFLICTS} PK conflicts")
    print("=" * 72)

    sys.exit(0)


import argparse  # noqa: E402 — at bottom for argparse usage in main()

if __name__ == "__main__":
    main()
