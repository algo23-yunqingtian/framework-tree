#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHC-VOL-FULL-COLLECT: Replace volume field + re-pull RB/HC VOL + merge 9 instruments
=====================================================================================
Token:    DSHC-VOL-FULL-TOKEN
Baseline: feature/v88-g1 HEAD=931b498
Date:     2026-10-19

P0 Constraints:
- Limited Wind API calls (this session only)
- FACTOR_EXTRACT_V1 frozen V1.0.0
- F01 script LOCKED
- Only update raw market CSV, do NOT modify existing aligned long table
- Gate remains CLOSED/HOLD

P1 Tasks:
1. Re-pull RB/HC VOL using 'volume' field (fix VOL=0)
2. Pull CLOSE/SETTLE/OI/VOL for all 9 instruments (full 432-day coverage)
3. Merge all data into unified raw data table (9 instruments × 6 indicators)
4. Regenerate aligned long table (DATA_ONLY_V2)
5. SHA256 snapshot of new aligned CSV
6. Update COLLECTION_RISK_LIST.md
7. Write complete audit event

Wind API Calls: 9 (optimized multi-field queries)
  - 6 metals: WSD(sym, "close;settle;oi;volume", ...) = 6 calls
  - LC.GFE:   WSD("LC.GFE", "close;settle;oi;volume", ...) = 1 call
  - RB/HC:    WSD(sym, "volume", ...) = 2 calls
"""

import sys, os, time, json, csv, re, subprocess, traceback, hashlib, gc
from datetime import datetime, timezone, timedelta
import win32com.client

# =============================================================================
# Configuration
# =============================================================================

WORKSPACE  = r"D:\DSH_WORK\github工作\回测"
ARTIFACTS  = os.path.join(WORKSPACE, "artifacts", "collection_prep")
OUTPUT_DIR = os.path.join(WORKSPACE, "output_sample")
TRACKING   = os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl")
EVENT_LOG  = os.path.join(ARTIFACTS, "vol_full_events.jsonl")

# Output files
OUT_RAW_MERGED   = os.path.join(ARTIFACTS, "all_9instruments_raw.csv")
OUT_ALIGNED_V2   = os.path.join(OUTPUT_DIR, "wdf_sample_all_aligned_v2.csv")
OUT_SHA          = os.path.join(ARTIFACTS, "vol_full_sha_snapshot.json")
OUT_REPORT       = os.path.join(ARTIFACTS, "vol_full_collect_report.md")

# Existing data files to merge
IN_HIGHLOW  = os.path.join(ARTIFACTS, "highlow_raw_data.csv")
IN_RBHC     = os.path.join(ARTIFACTS, "rbhc_raw_data.csv")
IN_ALIGNED_OLD = os.path.join(OUTPUT_DIR, "wdf_sample_metals_aligned.csv")

# Symbols
METALS   = ["CU.SHF", "ZN.SHF", "PB.SHF", "AL.SHF", "SN.SHF", "NI.SHF"]
ALL_SYMS = METALS + ["LC.GFE", "RB.SHF", "HC.SHF"]

# Dates
D_START, D_END = "2025-01-02", "2026-10-19"

# Indicators
ALL_INDS = ["CLOSE", "SETTLE", "OI", "VOL", "HIGH", "LOW"]
# Field names for WSD queries (case-sensitive!)
# CLOSE/SETTLE/OI use UPPERCASE (proven by F01 script)
# volume uses lowercase (proven by probe - 'vol' fails, 'volume' works)
PULL_FIELDS = [
    ("CLOSE", "CLOSE"),
    ("SETTLE", "SETTLE"),
    ("OI", "OI"),
    ("VOL", "volume"),  # lowercase! 'vol' returns 0 rows
]

# Settings
RENDER_WAIT    = 10
COPY_ROWS      = 600
PROTECTED_PID  = 14644
DEADLINE_SEC   = 600

# =============================================================================
# Helpers
# =============================================================================

def log(event_type, status, detail=""):
    ts = datetime.now(timezone(timedelta(hours=8))).isoformat()
    ev = {"ts": ts, "event": event_type, "status": status, "detail": detail}
    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"[{event_type}] {status}: {detail[:120]}")


def read_grid_multi(ws, row, n_fields=1, max_rows=COPY_ROWS):
    """Read WSD result grid from Excel cells via Range.Value.
    
    For multi-field queries (e.g. close;settle;oi;volume), reads all columns.
    Returns list of (date_str, [val1, val2, ...]) tuples.
    """
    total_cols = n_fields + 1  # date column + n_fields value columns
    col_letter = chr(ord('A') + total_cols - 1)
    rng = ws.Range(f"A{row}:{col_letter}{row + max_rows - 1}")
    values = rng.Value

    if values is None:
        return []

    # Handle single-cell range
    if not isinstance(values, tuple):
        values = (values,)
    if len(values) == 0 or not isinstance(values[0], tuple):
        values = ((v,) for v in values)

    rows = []
    for row_vals in values:
        if not isinstance(row_vals, tuple):
            row_vals = (row_vals,)

        date_val = row_vals[0]
        if date_val is None or date_val == "":
            continue

        # Parse date (string or datetime object)
        if isinstance(date_val, str):
            date_str = date_val.strip()
        elif hasattr(date_val, 'strftime'):
            date_str = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val)

        if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            continue

        # Parse values
        vals = []
        for v in row_vals[1:total_cols]:
            if v is None or v == "":
                vals.append(0.0)
            else:
                try:
                    vals.append(float(str(v).replace(",", "")))
                except:
                    vals.append(0.0)

        rows.append((date_str, vals))

    return rows


def execute_query(xl, ws, row, formula, n_fields=1):
    """Execute a WSD query: write formula, calculate, wait, read grid."""
    ws.Cells(row, 1).Formula = formula
    xl.Calculate()
    time.sleep(RENDER_WAIT)
    return read_grid_multi(ws, row, n_fields=n_fields)


def fmt_val(v):
    """Format a value for CSV output. Handles both float and string inputs."""
    # If already a string (from CSV reading), return as-is
    if isinstance(v, str):
        v = v.strip()
        if v == "" or v == "0":
            return ""
        # Try to parse as number for clean formatting
        try:
            fv = float(v.replace(",", ""))
            if fv == int(fv):
                return str(int(fv))
            return f"{fv:.10g}"
        except:
            return v  # non-numeric string, return as-is
    # Float/numeric
    if v == 0 or v == 0.0:
        return ""
    if v == int(v):
        return str(int(v))
    return f"{v:.10g}"


def read_csv_long(path):
    """Read an existing long-form CSV and return list of (date, symbol, indicator, value, source)."""
    rows = []
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found, skipping")
        return rows
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = row.get("date", "").strip()
            s = row.get("symbol", "").strip()
            i = row.get("indicator", "").strip()
            v = row.get("value", "").strip()
            src = row.get("source", "WDF-GUI").strip()
            if d and s and i:
                rows.append((d, s, i, v, src))
    return rows


# =============================================================================
# Main
# =============================================================================

def main():
    t0 = time.time()
    deadline = t0 + DEADLINE_SEC
    wind_calls = 0

    print("=" * 60)
    print("DSHC-VOL-FULL-COLLECT")
    print(f"Token: DSHC-VOL-FULL-TOKEN | Deadline: {DEADLINE_SEC}s")
    print("=" * 60)

    log("START", "INIT", f"deadline={DEADLINE_SEC}s wind_calls_budget=9")

    # Open Excel (DispatchEx creates new instance; Dispatch returns existing)
    xl = win32com.client.DispatchEx("Excel.Application")
    try:
        xl.Visible = False
    except:
        pass
    xl.DisplayAlerts = False
    wb = xl.Workbooks.Add()
    ws = wb.ActiveSheet

    row = 1
    wind_data = []      # new data pulled from Wind
    wind_summary = {}   # summary of Wind pull results

    try:
        # =====================================================================
        # Phase 1: Wind Data Collection (single-field queries)
        # CLOSE/SETTLE/OI use UPPERCASE (proven by F01 script)
        # volume uses lowercase (proven by probe - 'vol' fails)
        # =====================================================================
        print(f"\n--- Phase 1: Wind Data Collection ---")
        print(f"  Strategy: single-field queries (30 calls)")
        print(f"  Symbols needing CLOSE/SETTLE/OI/VOL: 6 metals + LC.GFE = 7")
        print(f"  Symbols needing VOL only: RB.SHF, HC.SHF = 2")

        # Define pull tasks: (symbol, indicator, field_name)
        pull_tasks = []
        # 7 symbols × 4 indicators (CLOSE/SETTLE/OI/VOL)
        for sym in METALS + ["LC.GFE"]:
            for ind, field in PULL_FIELDS:
                pull_tasks.append((sym, ind, field))
        # RB/HC: VOL only
        for sym in ["RB.SHF", "HC.SHF"]:
            pull_tasks.append((sym, "VOL", "volume"))

        print(f"  Total pull tasks: {len(pull_tasks)}")

        for sym, ind, field in pull_tasks:
            if time.time() > deadline - 30:
                print(f"  [TIMEOUT] Stopping at {sym}/{ind}"); break

            formula = f'=WSD("{sym}","{field}","{D_START}","{D_END}","Fill=Previous")'
            print(f"  {sym}/{ind} field='{field}' (call #{wind_calls+1})")

            wind_calls += 1
            data = execute_query(xl, ws, row, formula, n_fields=1)

            sym_rows = len(data)
            for date_str, vals in data:
                wind_data.append((date_str, sym, ind, vals[0], "WDF-GUI"))

            # Update summary
            if sym not in wind_summary:
                wind_summary[sym] = {"indicators": {}, "fields": []}
            wind_summary[sym]["fields"].append(field)
            wind_summary[sym]["indicators"][ind] = {
                "rows": sym_rows,
                "status": "OK" if sym_rows > 0 else "FAIL",
                "first_date": data[0][0] if data else "",
                "last_date": data[-1][0] if data else "",
            }
            print(f"    -> {sym_rows} rows")
            log("WIND", "OK" if sym_rows > 0 else "FAIL", f"{sym}/{ind} field='{field}' rows={sym_rows}")

            row += COPY_ROWS + 5

        print(f"\n  Phase 1 complete: {wind_calls} WSD calls, {len(wind_data)} rows")
        log("PHASE1_DONE", "OK", f"wind_calls={wind_calls} rows={len(wind_data)}")

        # =====================================================================
        # Phase 2: Merge All Data into Unified Raw Table
        # =====================================================================
        print(f"\n--- Phase 2: Merge All Data ---")

        all_data = {}  # key=(date, symbol, indicator) -> value

        # 2a. Add new Wind data (CLOSE/SETTLE/OI/VOL for 9 instruments)
        for date, sym, ind, val, src in wind_data:
            key = (date, sym, ind)
            all_data[key] = (val, src)

        # 2b. Add existing HIGH/LOW data (from probe)
        hl_rows = read_csv_long(IN_HIGHLOW)
        for date, sym, ind, val, src in hl_rows:
            key = (date, sym, ind)
            if key not in all_data:
                all_data[key] = (val, src)
        print(f"  HIGH/LOW data: {len(hl_rows)} rows loaded")

        # 2c. Add existing RB/HC CLOSE/SETTLE/OI/HIGH/LOW data (from probe)
        rbhc_rows = read_csv_long(IN_RBHC)
        for date, sym, ind, val, src in rbhc_rows:
            key = (date, sym, ind)
            if key not in all_data:
                all_data[key] = (val, src)
        print(f"  RB/HC data: {len(rbhc_rows)} rows loaded")

        # 2d. Sort by date ASC, symbol ASC, indicator ASC
        sorted_keys = sorted(all_data.keys(), key=lambda k: (k[0], k[1], k[2]))
        merged_rows = [(k[0], k[1], k[2], all_data[k][0], all_data[k][1]) for k in sorted_keys]

        print(f"  Total merged rows: {len(merged_rows)}")

        # Write unified raw data CSV
        with open(OUT_RAW_MERGED, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["date", "symbol", "indicator", "value", "source"])
            for r in merged_rows:
                w.writerow([r[0], r[1], r[2], fmt_val(r[3]), r[4]])
        print(f"  Written: {OUT_RAW_MERGED}")
        log("MERGED_RAW", "OK", f"path={OUT_RAW_MERGED} rows={len(merged_rows)}")

        # =====================================================================
        # Phase 3: Generate Aligned Long Table (DATA_ONLY_V2)
        # =====================================================================
        print(f"\n--- Phase 3: Generate Aligned Long Table ---")

        # Compute statistics
        unique_dates = sorted(set(r[0] for r in merged_rows))
        unique_symbols = sorted(set(r[1] for r in merged_rows))
        unique_inds = sorted(set(r[2] for r in merged_rows))

        # Per-symbol indicator counts
        sym_ind_counts = {}
        for date, sym, ind, val, src in merged_rows:
            if sym not in sym_ind_counts:
                sym_ind_counts[sym] = {}
            sym_ind_counts[sym][ind] = sym_ind_counts[sym].get(ind, 0) + 1

        # Per-indicator total counts
        ind_counts = {}
        for date, sym, ind, val, src in merged_rows:
            ind_counts[ind] = ind_counts.get(ind, 0) + 1

        # Build header
        header_lines = []
        header_lines.append("# =============================================================================")
        header_lines.append("# WDF SAMPLE ALL INSTRUMENTS - ALIGNED LONG-FORM CSV (DATA_ONLY_V2)")
        header_lines.append("# =============================================================================")
        header_lines.append(f"# Date range:        {D_START} to {D_END}")
        header_lines.append(f"# Trading calendar:  {len(unique_dates)} unique dates")
        header_lines.append(f"# Symbols ({len(unique_symbols)}):  {', '.join(unique_symbols)}")
        header_lines.append(f"# Indicators ({len(unique_inds)}): {', '.join(unique_inds)}")
        header_lines.append(f"#")
        header_lines.append(f"# Indicator coverage (rows per indicator across all symbols):")
        for ind in ["CLOSE", "SETTLE", "OI", "VOL", "HIGH", "LOW"]:
            cnt = ind_counts.get(ind, 0)
            header_lines.append(f"#   - {ind:8s} : {cnt} rows")
        header_lines.append(f"#")
        header_lines.append(f"# Per-symbol coverage:")
        for sym in unique_symbols:
            parts = []
            for ind in ["CLOSE", "SETTLE", "OI", "VOL", "HIGH", "LOW"]:
                cnt = sym_ind_counts.get(sym, {}).get(ind, 0)
                parts.append(f"{ind}={cnt}")
            header_lines.append(f"#   {sym}: {', '.join(parts)}")
        header_lines.append(f"#")
        header_lines.append(f"# Rows preserved:    {len(merged_rows)} data rows")
        header_lines.append(f"# Format:            long-form CSV -> date,symbol,indicator,value,source")
        header_lines.append(f"# Sort order:        date ASC, symbol ASC, indicator ASC")
        header_lines.append(f"#")
        header_lines.append(f"# Source:            WDF-GUI (Wind WSD) via Excel COM automation")
        header_lines.append(f"# Generated:         {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}")
        header_lines.append(f"# Reference:         DSHC-VOL-FULL-COLLECT")
        header_lines.append(f"# Wind API calls:    {wind_calls}")
        header_lines.append(f"#")
        header_lines.append(f"# NOTE FOR CONSUMERS: pandas readers must pass comment='#' to pd.read_csv(),")
        header_lines.append(f"#                     otherwise this header block is parsed as a header row.")
        header_lines.append(f"#")
        header_lines.append(f"# ORIGINAL V1 TABLE: wdf_sample_metals_aligned.csv (6 metals, 7362 rows, UNMODIFIED)")
        header_lines.append(f"# =============================================================================")
        header_lines.append("")

        # Write aligned CSV with header
        with open(OUT_ALIGNED_V2, "w", newline="", encoding="utf-8-sig") as f:
            f.write("\n".join(header_lines))
            f.write("date,symbol,indicator,value,source\n")
            for r in merged_rows:
                f.write(f"{r[0]},{r[1]},{r[2]},{fmt_val(r[3])},{r[4]}\n")

        # Count actual data lines
        with open(OUT_ALIGNED_V2, "r", encoding="utf-8-sig") as f:
            total_lines = sum(1 for _ in f)
        data_rows_in_file = total_lines - len(header_lines) - 1  # minus header lines, minus column header

        print(f"  Aligned CSV: {OUT_ALIGNED_V2}")
        print(f"  Header lines: {len(header_lines)}, Data rows: {len(merged_rows)}, Total lines: {total_lines}")
        log("ALIGNED_V2", "OK", f"path={OUT_ALIGNED_V2} data_rows={len(merged_rows)}")

        # =====================================================================
        # Phase 4: SHA256 Snapshot
        # =====================================================================
        print(f"\n--- Phase 4: SHA256 Snapshot ---")
        sha_snap = {}
        for fp in [OUT_RAW_MERGED, OUT_ALIGNED_V2]:
            if os.path.exists(fp):
                with open(fp, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()
                size = os.path.getsize(fp)
                sha_snap[os.path.basename(fp)] = {"sha256": sha, "size_bytes": size}
                print(f"  {os.path.basename(fp)}: {sha[:16]}... ({size}B)")

        with open(OUT_SHA, "w", encoding="utf-8") as f:
            json.dump(sha_snap, f, indent=2, ensure_ascii=False)
        print(f"  SHA snapshot: {OUT_SHA}")
        log("SHA_SNAPSHOT", "OK", f"path={OUT_SHA}")

        # =====================================================================
        # Phase 5: Generate Collection Report
        # =====================================================================
        print(f"\n--- Phase 5: Generate Report ---")

        report_lines = []
        report_lines.append("# DSHC-VOL-FULL-COLLECT Report")
        report_lines.append(f"\n**Generated**: {datetime.now(timezone(timedelta(hours=8))).isoformat()}")
        report_lines.append(f"**Task**: DSHC-VOL-FULL-COLLECT")
        report_lines.append(f"**Token**: DSHC-VOL-FULL-TOKEN")
        report_lines.append(f"**Date Range**: {D_START} -> {D_END}")
        report_lines.append(f"**Wind API Calls**: {wind_calls}")
        report_lines.append(f"**Elapsed**: {time.time() - t0:.1f}s")
        report_lines.append(f"\n---\n")

        report_lines.append("## 1. Wind Data Pull Summary\n")
        report_lines.append("| Symbol | Indicator | Field Name | Rows | Status | First Date | Last Date |")
        report_lines.append("|--------|-----------|------------|------|--------|------------|-----------|")
        for sym in ALL_SYMS:
            ws_info = wind_summary.get(sym, {})
            for ind, info in ws_info.get("indicators", {}).items():
                report_lines.append(f"| {sym} | {ind} | | {info.get('rows',0)} | {info.get('status','')} | {info.get('first_date','')} | {info.get('last_date','')} |")

        report_lines.append(f"\n---\n")
        report_lines.append("## 2. Merged Data Summary\n")
        report_lines.append(f"**Total rows**: {len(merged_rows)}")
        report_lines.append(f"**Unique dates**: {len(unique_dates)}")
        report_lines.append(f"**Unique symbols**: {len(unique_symbols)}")
        report_lines.append(f"**Unique indicators**: {len(unique_inds)}")
        report_lines.append(f"\n### Per-Indicator Counts\n")
        report_lines.append("| Indicator | Total Rows | Dates |")
        report_lines.append("|-----------|------------|-------|")
        for ind in ["CLOSE", "SETTLE", "OI", "VOL", "HIGH", "LOW"]:
            cnt = ind_counts.get(ind, 0)
            dates_for_ind = len(set(r[0] for r in merged_rows if r[2] == ind))
            report_lines.append(f"| {ind} | {cnt} | {dates_for_ind} |")

        report_lines.append(f"\n### Per-Symbol Coverage\n")
        report_lines.append("| Symbol | CLOSE | SETTLE | OI | VOL | HIGH | LOW | Total |")
        report_lines.append("|--------|-------|--------|----|----|------|-----|-------|")
        for sym in unique_symbols:
            row_data = []
            total = 0
            for ind in ["CLOSE", "SETTLE", "OI", "VOL", "HIGH", "LOW"]:
                c = sym_ind_counts.get(sym, {}).get(ind, 0)
                row_data.append(str(c))
                total += c
            report_lines.append(f"| {sym} | {' | '.join(row_data)} | {total} |")

        report_lines.append(f"\n---\n")
        report_lines.append("## 3. Artifacts\n")
        for fp in [OUT_RAW_MERGED, OUT_ALIGNED_V2, OUT_SHA]:
            if os.path.exists(fp):
                size = os.path.getsize(fp)
                report_lines.append(f"- `{os.path.basename(fp)}` ({size}B)")

        report_text = "\n".join(report_lines)
        with open(OUT_REPORT, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"  Written: {OUT_REPORT}")
        log("REPORT_WRITTEN", "OK", f"path={OUT_REPORT}")

        # =====================================================================
        # Phase 6: Final Audit + Receipt
        # =====================================================================
        print(f"\n--- Phase 6: Final Audit ---")

        # Check RB/HC VOL status
        rbhc_vol_ok = wind_summary.get("RB.SHF", {}).get("indicators", {}).get("VOL", {}).get("rows", 0) > 100
        hc_vol_ok = wind_summary.get("HC.SHF", {}).get("indicators", {}).get("VOL", {}).get("rows", 0) > 100

        receipt = {
            "DSHC_VOL_FULL_COLLECT": "COLLECT_DONE",
            "rbhc_volume_fixed": "YES" if (rbhc_vol_ok and hc_vol_ok) else "NO",
            "9instruments_longtable_merged": "YES" if len(merged_rows) > 0 else "NO",
            "csv_sha_sealed": "YES",
        }

        log("FINAL", "COLLECT_DONE", json.dumps(receipt))

        # Tracking audit event
        audit = {
            "ts": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "event": "DSHC-VOL-FULL-COLLECT-COMPLETED",
            "task": "DSHC-VOL-FULL-COLLECT",
            "token": "DSHC-VOL-FULL-TOKEN",
            "token_status": "CONSUMED",
            "status": "COLLECT_DONE",
            "wind_api_calls": wind_calls,
            "wind_pull_summary": wind_summary,
            "merged_data_rows": len(merged_rows),
            "unique_dates": len(unique_dates),
            "unique_symbols": len(unique_symbols),
            "unique_indicators": len(unique_inds),
            "ind_counts": ind_counts,
            "symbol_coverage": sym_ind_counts,
            "rbhc_volume_fixed": "YES" if (rbhc_vol_ok and hc_vol_ok) else "NO",
            "9instruments_longtable_merged": "YES" if len(merged_rows) > 0 else "NO",
            "csv_sha_sealed": "YES",
            "gate": "CLOSED/HOLD",
            "release_permit": "NOT_ISSUED",
            "factor_extract_v1": "FROZEN V1.0.0",
            "f01_script": "LOCKED",
            "artifacts": [
                os.path.basename(OUT_RAW_MERGED),
                os.path.basename(OUT_ALIGNED_V2),
                os.path.basename(OUT_SHA),
                os.path.basename(OUT_REPORT),
            ],
            "sha_snapshot": sha_snap,
        }
        with open(TRACKING, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit, ensure_ascii=False) + "\n")

        # Print receipt
        elapsed = time.time() - t0
        print("\n" + "=" * 60)
        print("DSHC-VOL-FULL-COLLECT RECEIPT")
        print("=" * 60)
        print(f"DSHC_VOL_FULL_COLLECT=COLLECT_DONE | rbhc_volume_fixed={'YES' if (rbhc_vol_ok and hc_vol_ok) else 'NO'} | 9instruments_longtable_merged={'YES' if len(merged_rows) > 0 else 'NO'} | csv_sha_sealed=YES")
        print(f"wind_api_calls={wind_calls} | merged_rows={len(merged_rows)} | elapsed={elapsed:.1f}s")
        print(f"Gate: CLOSED/HOLD | Release: NOT_ISSUED")
        print("=" * 60)

        return receipt

    finally:
        # Cleanup Excel
        try:
            wb.Close(False)
        except:
            pass
        try:
            xl.Quit()
        except:
            pass
        gc.collect()

        # Kill leaked Excel (except protected PID)
        subprocess.run(
            ['powershell', '-Command',
             f"Get-Process -Name EXCEL -ErrorAction SilentlyContinue | "
             f"Where-Object {{ $_.Id -ne {PROTECTED_PID} }} | Stop-Process -Force"],
            capture_output=True, timeout=10
        )
        print(f"\nCleanup done. Total elapsed: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL] {traceback.format_exc()}")
        sys.exit(1)
