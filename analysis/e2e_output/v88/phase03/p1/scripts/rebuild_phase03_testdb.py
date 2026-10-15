#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_phase03_testdb.py — V88 Phase03 P1 DSHB 重建脚本
==================================================================
TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

Purpose:
  One-click rebuild of phase03_test.db from source JSONL files + derive 59 indicators.
  P1 update: includes derived indicator generation step.

Usage:
  python rebuild_phase03_testdb.py [--dry-run] [--db path/to/phase03_test.db]
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
P0_DIR = SCRIPT_DIR.parent.parent.parent
P1_DIR = SCRIPT_DIR.parent
DEFAULT_DB_PATH = P0_DIR / "p0" / "phase03_test.db"

EXPECTED_ROWS = 590411
EXPECTED_INDICATORS = 674
EXPECTED_MAPPED = 667
EXPECTED_ERRORS = 0
EXPECTED_PK_CONFLICTS = 0
EXPECTED_DERIVED = 59


def setup_environment():
    if platform.system() == "Windows":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUNBUFFERED"] = "1"
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def run_script(script_path, args=None, label=""):
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    print(f"\n{'='*72}")
    print(f"  Running: {label or script_path.name}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*72}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def check_jsonl_files():
    jsonl_dir = SCRIPT_DIR.parent.parent.parent.parent.parent / "data" / "db_export"
    required_files = [
        "series_ZN.jsonl", "series_NI.jsonl", "series_SI.jsonl",
        "series_SN.jsonl", "series_LI.jsonl", "cu_al_pb_supplement.jsonl",
    ]
    all_found = True
    total_size_mb = 0.0
    print("\n" + "=" * 72)
    print("  JSONL Source File Check")
    print("=" * 72)
    for fname in required_files:
        fpath = jsonl_dir / fname
        if fpath.exists():
            fsize_mb = fpath.stat().st_size / (1024 * 1024)
            total_size_mb += fsize_mb
            print(f"  [OK] FOUND:  {fname:<40} ({fsize_mb:6.1f} MB)")
        else:
            print(f"  [FAIL] MISSING: {fname:<40}")
            all_found = False
    print()
    print(f"  Total size: {total_size_mb:.1f} MB")
    print(f"  All files found: {all_found}")
    print("=" * 72)
    return all_found, required_files


def main():
    import argparse
    parser = argparse.ArgumentParser(description="V88 Phase03 P1 — One-click rebuild")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Path to phase03_test.db")
    args = parser.parse_args()

    setup_environment()
    db_path = Path(args.db)
    dry_run = args.dry_run

    print("=" * 72)
    print("  V88 Phase03 P1 · DSHB 一键重建")
    print("  TASK_ID: V88_PHASE03_P1_DSHB_MAIN_JOB")
    print("=" * 72)
    print(f"  DB path:   {db_path}")
    print(f"  Dry run:   {dry_run}")
    print(f"  Expected:  {EXPECTED_ROWS:,} rows, {EXPECTED_INDICATORS} indicators")
    print(f"             {EXPECTED_MAPPED} mapped, {EXPECTED_DERIVED} derived")
    print(f"             {EXPECTED_ERRORS} errors, {EXPECTED_PK_CONFLICTS} PK conflicts")

    # Step 1: Verify source files
    print("\n" + "#" * 72)
    print("#  STEP 1: Verify JSONL source files")
    print("#" * 72)
    all_found, required_files = check_jsonl_files()
    if not all_found:
        print("\n  FATAL: Missing JSONL files.")
        sys.exit(1)

    # Step 2: Clean existing DB
    if not dry_run and db_path.exists():
        print(f"\n  Removing existing DB: {db_path}")
        db_path.unlink()
        print(f"  [OK] Removed")
    elif dry_run:
        print(f"\n  [DRY RUN] Would remove existing DB: {db_path}")

    # Step 3: Import all JSONL
    print("\n" + "#" * 72)
    print("#  STEP 2: Import ALL JSONL into phase03_test.db")
    print("#" * 72)
    import_script = SCRIPT_DIR / "import_all_to_testdb.py"
    if not import_script.exists():
        import_script = P0_DIR / "scripts" / "import_all_to_testdb.py"
    import_args = ["--db", str(db_path)]
    if dry_run:
        import_args.append("--dry-run")
    ret = run_script(import_script, import_args, "Import all JSONL")
    if ret != 0:
        print(f"\n  FATAL: Import failed with exit code {ret}")
        sys.exit(1)

    if dry_run:
        print("\n" + "=" * 72)
        print("  [DRY RUN COMPLETE] No changes made.")
        print("=" * 72)
        sys.exit(0)

    # Step 4: Derive 59 indicators (P1 NEW)
    print("\n" + "#" * 72)
    print("#  STEP 3: Derive 59 indicators (P1)")
    print("#" * 72)
    derive_script = SCRIPT_DIR / "derive_indicators.py"
    derive_args = ["--db", str(db_path)]
    ret = run_script(derive_script, derive_args, "Derive 59 indicators")
    if ret != 0:
        print(f"\n  FATAL: Derivation failed with exit code {ret}")
        sys.exit(1)

    # Step 5: Verify
    print("\n" + "#" * 72)
    print("#  STEP 4: Verify phase03_test.db integrity")
    print("#" * 72)
    verify_script = SCRIPT_DIR / "verify_testdb.py"
    verify_args = ["--db", str(db_path), "--dqa"]
    ret = run_script(verify_script, verify_args, "Verify test DB")
    if ret != 0:
        print(f"\n  FATAL: Verification failed with exit code {ret}")
        sys.exit(1)

    print("\n" + "=" * 72)
    print("  REBUILD COMPLETE")
    print("=" * 72)
    print(f"  Database: {db_path}")
    print(f"  Expected: {EXPECTED_ROWS:,} rows | {EXPECTED_INDICATORS} indicators")
    print(f"  Expected: {EXPECTED_MAPPED} mapped | {EXPECTED_DERIVED} derived")
    print(f"  Expected: {EXPECTED_ERRORS} errors | {EXPECTED_PK_CONFLICTS} PK conflicts")
    print("=" * 72)

    sys.exit(0)


if __name__ == "__main__":
    main()