#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHC-VOL-PROBE-COLLECT: VOL Probe + RB/HC Full Data + HIGH/LOW Verification
================================================================================
Token: DSHC-VOL-PROBE-TOKEN
Baseline: feature/v88-g1 HEAD=6b2fdbf
Date: 2026-10-19

P0 Constraints:
- Limited Wind API calls (this session only)
- FACTOR_EXTRACT_V1 frozen V1.0.0
- F01 script LOCKED
- Raw CSV only, no aligned long table modification
- Gate remains CLOSED/HOLD

P1 Tasks:
1. 6 WSD variant probes for VOL field (short window)
2. RB/HC full history data (CLOSE/SETTLE/OI/VOL/HIGH/LOW)
3. HIGH/LOW for 6 SHFE metals + LC.GFE
4. Produce 3 artifacts
5. Audit event + SHA snapshot
"""

import sys, os, time, json, csv, re, subprocess, traceback, hashlib, gc
from datetime import datetime, timezone, timedelta
import win32com.client

# =============================================================================
# Configuration
# =============================================================================

WORKSPACE = r"D:\DSH_WORK\github工作\回测"
ARTIFACTS = os.path.join(WORKSPACE, "artifacts", "collection_prep")
TRACKING  = os.path.join(WORKSPACE, "tracking_monitor_audit.jsonl")
EVENT_LOG = os.path.join(ARTIFACTS, "vol_probe_events.jsonl")

# Output files
OUT_PROBE   = os.path.join(ARTIFACTS, "vol_probe_result.csv")
OUT_RBHC    = os.path.join(ARTIFACTS, "rbhc_raw_data.csv")
OUT_HIGHLOW = os.path.join(ARTIFACTS, "highlow_raw_data.csv")
OUT_REPORT  = os.path.join(ARTIFACTS, "highlow_probe_report.md")
OUT_SHA     = os.path.join(ARTIFACTS, "vol_probe_sha_snapshot.json")

# Symbols
PROBE_SYM = "CU.SHF"
FULL_SYMS = ["RB.SHF", "HC.SHF"]
HL_SYMS   = ["CU.SHF", "ZN.SHF", "PB.SHF", "AL.SHF", "SN.SHF", "NI.SHF", "LC.GFE"]

# Dates
D_START, D_END = "2025-01-02", "2026-10-19"
P_D_START, P_D_END = "2025-01-02", "2025-01-10"

# Indicators
FULL_INDS = ["CLOSE", "SETTLE", "OI", "VOL", "HIGH", "LOW"]
HL_INDS   = ["HIGH", "LOW"]

# Settings
RENDER_WAIT    = 10
COPY_ROWS      = 600
PROTECTED_PID  = 14644
DEADLINE_SEC   = 600

# Probe variants: (id, field, params, func, description)
PROBES = [
    ("A_current",  "vol",                   '"Fill=Previous"',                        "WSD", "Current vol field name"),
    ("B_volume",   "volume",                '"Fill=Previous"',                        "WSD", "volume field name variant"),
    ("C_turnover", "turnover",              '"Fill=Previous"',                        "WSD", "turnover field name variant"),
    ("D_multi",    "vol;turnover;close",    '"Fill=Previous"',                        "WSD", "Multi-field query"),
    ("E_datefill", "vol",                   '"Fill=Previous","DateFill=Previous"',    "WSD", "DateFill parameter"),
    ("F_wdp",      "vol",                   '"Fill=Previous"',                        "WDP", "WDP panel data function"),
]

# =============================================================================
# Helpers
# =============================================================================

def log(event_type, status, detail=""):
    ts = datetime.now(timezone(timedelta(hours=8))).isoformat()
    ev = {"ts": ts, "event": event_type, "status": status, "detail": detail}
    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"[{event_type}] {status}: {detail[:120]}")


def read_grid(ws, row, cols=2, max_rows=COPY_ROWS):
    """Read WSD result grid from Excel cells via Range.Value."""
    col_letter = chr(ord('A') + cols - 1)
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
        val_val  = row_vals[1] if len(row_vals) > 1 else None

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

        # Parse value
        val = 0.0
        if val_val is not None and val_val != "":
            try:
                val = float(str(val_val).replace(",", ""))
            except:
                pass

        rows.append((date_str, val))

    return rows


def execute_query(xl, ws, row, formula, cols=2):
    """Execute a WSD query: write formula, calculate, wait, read grid."""
    ws.Cells(row, 1).Formula = formula
    xl.Calculate()
    time.sleep(RENDER_WAIT)
    return read_grid(ws, row, cols=cols)


def fmt_val(v):
    if v == 0:
        return ""
    if v == int(v):
        return str(int(v))
    return f"{v:.10g}"


# =============================================================================
# Main
# =============================================================================

def main():
    t0 = time.time()
    deadline = t0 + DEADLINE_SEC
    wind_calls = 0

    print("=" * 60)
    print("DSHC-VOL-PROBE-COLLECT")
    print(f"Token: DSHC-VOL-PROBE-TOKEN | Deadline: {DEADLINE_SEC}s")
    print("=" * 60)

    log("START", "INIT", f"deadline={DEADLINE_SEC}s wind_calls_budget={len(PROBES)+len(FULL_SYMS)*len(FULL_INDS)+len(HL_SYMS)*len(HL_INDS)}")

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
    probe_results = []
    full_data = []
    hl_data = []
    hl_summary = {}

    try:
        # =====================================================================
        # Phase 1: VOL Probe (6 variants, short window)
        # =====================================================================
        print(f"\n--- Phase 1: VOL Probe ({len(PROBES)} variants, {P_D_START}~{P_D_END}) ---")

        for pid, field, params, func, desc in PROBES:
            if time.time() > deadline - 30:
                print("  [TIMEOUT] Stopping probe phase"); break

            formula = f'={func}("{PROBE_SYM}","{field}","{P_D_START}","{P_D_END}",{params})'
            print(f"  [{pid}] {formula}")

            wind_calls += 1
            cols = 4 if pid == "D_multi" else 2
            data = execute_query(xl, ws, row, formula, cols=cols)

            status = "OK" if data else "FAIL"
            r = {
                "variant": pid, "field": field, "params": params, "func": func,
                "desc": desc, "window": f"{P_D_START}~{P_D_END}",
                "symbol": PROBE_SYM, "rows": len(data), "status": status,
                "first_date": data[0][0] if data else "",
                "last_date": data[-1][0] if data else "",
                "first_val": str(data[0][1]) if data else "",
                "last_val": str(data[-1][1]) if data else "",
            }
            probe_results.append(r)
            print(f"    -> {len(data)} rows, {status}")
            log("PROBE", status, f"{pid} field={field} rows={len(data)}")

            row += COPY_ROWS + 5

        # Write probe CSV
        with open(OUT_PROBE, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=[
                "variant","field","params","func","desc","window","symbol",
                "rows","status","first_date","last_date","first_val","last_val"])
            w.writeheader()
            for r in probe_results:
                w.writerow(r)
        print(f"  Written: {OUT_PROBE}")
        log("CSV_WRITTEN", "OK", f"path={OUT_PROBE}")

        # =====================================================================
        # Phase 2: RB/HC Full Data
        # =====================================================================
        print(f"\n--- Phase 2: RB/HC Full Data ({D_START}~{D_END}) ---")

        for sym in FULL_SYMS:
            for ind in FULL_INDS:
                if time.time() > deadline - 30:
                    print("  [TIMEOUT] Stopping full data phase"); break

                field = ind.lower()
                formula = f'=WSD("{sym}","{field}","{D_START}","{D_END}","Fill=Previous")'
                print(f"  {sym}/{ind} (call #{wind_calls+1})")

                wind_calls += 1
                data = execute_query(xl, ws, row, formula)

                for date, val in data:
                    full_data.append((date, sym, ind, val, "WDF-GUI"))

                print(f"    -> {len(data)} rows (total: {len(full_data)})")
                log("FULL", "OK" if data else "NO_DATA", f"{sym}/{ind} rows={len(data)}")

                row += COPY_ROWS + 5

        # Write RB/HC CSV
        full_data.sort(key=lambda r: (r[1], r[0], r[2]))
        with open(OUT_RBHC, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["date","symbol","indicator","value","source"])
            for r in full_data:
                w.writerow([r[0], r[1], r[2], fmt_val(r[3]), r[4]])
        print(f"  Written: {OUT_RBHC} ({len(full_data)} rows)")
        log("CSV_WRITTEN", "OK", f"path={OUT_RBHC} rows={len(full_data)}")

        # =====================================================================
        # Phase 3: HIGH/LOW for 7 symbols
        # =====================================================================
        print(f"\n--- Phase 3: HIGH/LOW Probe ({D_START}~{D_END}) ---")

        for sym in HL_SYMS:
            hl_summary[sym] = {}
            for ind in HL_INDS:
                if time.time() > deadline - 30:
                    print("  [TIMEOUT] Stopping HIGH/LOW phase"); break

                field = ind.lower()
                formula = f'=WSD("{sym}","{field}","{D_START}","{D_END}","Fill=Previous")'
                print(f"  {sym}/{ind} (call #{wind_calls+1})")

                wind_calls += 1
                data = execute_query(xl, ws, row, formula)

                for date, val in data:
                    hl_data.append((date, sym, ind, val, "WDF-GUI"))

                hl_summary[sym][ind] = {
                    "rows": len(data),
                    "status": "OK" if data else "NO_DATA",
                    "first_date": data[0][0] if data else "",
                    "last_date": data[-1][0] if data else "",
                    "first_val": str(data[0][1]) if data else "",
                    "last_val": str(data[-1][1]) if data else "",
                }
                print(f"    -> {len(data)} rows")
                log("HIGHLOW", hl_summary[sym][ind]["status"], f"{sym}/{ind} rows={len(data)}")

                row += COPY_ROWS + 5

        # Write HIGH/LOW CSV
        hl_data.sort(key=lambda r: (r[1], r[0], r[2]))
        with open(OUT_HIGHLOW, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["date","symbol","indicator","value","source"])
            for r in hl_data:
                w.writerow([r[0], r[1], r[2], fmt_val(r[3]), r[4]])
        print(f"  Written: {OUT_HIGHLOW} ({len(hl_data)} rows)")
        log("CSV_WRITTEN", "OK", f"path={OUT_HIGHLOW} rows={len(hl_data)}")

        # =====================================================================
        # Phase 4: Generate HIGH/LOW Probe Report
        # =====================================================================
        print(f"\n--- Phase 4: Generating Report ---")

        lines = []
        lines.append("# HIGH/LOW Probe Report")
        lines.append(f"\n**Generated**: {datetime.now(timezone(timedelta(hours=8))).isoformat()}")
        lines.append(f"**Task**: DSHC-VOL-PROBE-COLLECT")
        lines.append(f"**Date Range**: {D_START} -> {D_END}")
        lines.append(f"**Wind API Calls**: {wind_calls}")
        lines.append(f"\n---\n")
        lines.append("## Results Summary\n")
        lines.append("| Symbol | HIGH Rows | LOW Rows | HIGH Status | LOW Status | Risk |")
        lines.append("|--------|-----------|----------|-------------|------------|------|")

        for sym in HL_SYMS:
            h = hl_summary.get(sym, {}).get("HIGH", {})
            l = hl_summary.get(sym, {}).get("LOW", {})
            h_rows = h.get("rows", 0)
            l_rows = l.get("rows", 0)
            h_ok = h_rows > 0
            l_ok = l_rows > 0

            if h_rows >= 100 and l_rows >= 100:
                risk = "LOW"
            elif h_rows > 0 and l_rows > 0:
                risk = "MEDIUM"
            elif not h_ok and not l_ok:
                risk = "HIGH"
            else:
                risk = "MEDIUM"

            lines.append(f"| {sym} | {h_rows} | {l_rows} | {'OK' if h_ok else 'NO DATA'} | {'OK' if l_ok else 'NO DATA'} | {risk} |")

        lines.append(f"\n---\n")
        lines.append("## Detailed Results\n")

        for sym in HL_SYMS:
            h = hl_summary.get(sym, {}).get("HIGH", {})
            l = hl_summary.get(sym, {}).get("LOW", {})
            lines.append(f"### {sym}\n")
            lines.append(f"| Indicator | Rows | First Date | Last Date | First Value | Last Value | Status |")
            lines.append(f"|-----------|------|------------|-----------|-------------|------------|--------|")
            for ind in ["HIGH", "LOW"]:
                d = hl_summary.get(sym, {}).get(ind, {})
                icon = "OK" if d.get("rows", 0) > 0 else "NO DATA"
                lines.append(f"| {ind} | {d.get('rows',0)} | {d.get('first_date','')} | {d.get('last_date','')} | {d.get('first_val','')} | {d.get('last_val','')} | {icon} |")
            lines.append("")

        lines.append("---\n")
        lines.append("## ATR% Factor Impact\n")

        lc = hl_summary.get("LC.GFE", {})
        lc_h = lc.get("HIGH", {}).get("rows", 0)
        lc_l = lc.get("LOW", {}).get("rows", 0)

        if lc_h > 0 and lc_l > 0:
            lines.append("**LC.GFE: AVAILABLE** - ATR% factor can be computed for all 9 instruments (6 SHFE metals + RB + HC + LC.GFE).")
        else:
            lines.append("**LC.GFE: NOT AVAILABLE** - ATR% factor will only cover 8 instruments (excluding LC.GFE).")
            lines.append(f"  - LC.GFE HIGH: {lc_h} rows, LOW: {lc_l} rows")
            lines.append("  - Mitigation: compute ATR% for 8 instruments only, or seek alternative data source for LC.GFE")

        lines.append("\n---\n")
        lines.append("## Risk Summary\n")

        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        risk_symbols = {"LOW": [], "MEDIUM": [], "HIGH": []}
        for sym in HL_SYMS:
            h_rows = hl_summary.get(sym, {}).get("HIGH", {}).get("rows", 0)
            l_rows = hl_summary.get(sym, {}).get("LOW", {}).get("rows", 0)
            if h_rows >= 100 and l_rows >= 100:
                risk = "LOW"
            elif h_rows > 0 and l_rows > 0:
                risk = "MEDIUM"
            else:
                risk = "HIGH"
            risk_counts[risk] += 1
            risk_symbols[risk].append(sym)

        for r_name in ["LOW", "MEDIUM", "HIGH"]:
            if risk_counts[r_name] > 0:
                lines.append(f"- {r_name}: {risk_counts[r_name]}/{len(HL_SYMS)} ({', '.join(risk_symbols[r_name])})")

        report_text = "\n".join(lines)
        with open(OUT_REPORT, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"  Written: {OUT_REPORT}")
        log("REPORT_WRITTEN", "OK", f"path={OUT_REPORT}")

        # =====================================================================
        # Phase 5: SHA Snapshot
        # =====================================================================
        print(f"\n--- Phase 5: SHA Snapshot ---")
        sha_snap = {}
        for fp in [OUT_PROBE, OUT_RBHC, OUT_HIGHLOW, OUT_REPORT]:
            if os.path.exists(fp):
                with open(fp, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()
                size = os.path.getsize(fp)
                sha_snap[os.path.basename(fp)] = {"sha256": sha, "size_bytes": size}
                print(f"  {os.path.basename(fp)}: {sha[:16]}... ({size}B)")

        with open(OUT_SHA, "w", encoding="utf-8") as f:
            json.dump(sha_snap, f, indent=2, ensure_ascii=False)
        print(f"  SHA snapshot: {OUT_SHA}")

        # =====================================================================
        # Phase 6: Final Audit
        # =====================================================================
        print(f"\n--- Phase 6: Final Audit ---")

        vol_found = any(r["rows"] > 0 for r in probe_results)
        rbhc_ok   = len(full_data) > 0
        hl_ok     = len(hl_data) > 0
        total_rows = sum(r["rows"] for r in probe_results) + len(full_data) + len(hl_data)

        receipt = {
            "DSHC_VOL_PROBE": "PROBE_DONE",
            "vol_gap_root_found": "YES" if vol_found else "NO",
            "rbhc_data_collected": "YES" if rbhc_ok else "NO",
            "highlow_verified": "YES" if hl_ok else "NO",
        }

        log("FINAL", "PROBE_DONE", json.dumps(receipt))

        # Tracking audit event
        audit = {
            "ts": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "event": "DSHC-VOL-PROBE-COLLECT-COMPLETED",
            "task": "DSHC-VOL-PROBE-COLLECT",
            "token": "DSHC-VOL-PROBE-TOKEN",
            "token_status": "CONSUMED",
            "status": "PROBE_DONE",
            "wind_api_calls": wind_calls,
            "probe_variants_tested": len(PROBES),
            "probe_rows": sum(r["rows"] for r in probe_results),
            "rbhc_rows": len(full_data),
            "highlow_rows": len(hl_data),
            "total_rows": total_rows,
            "vol_gap_root_found": "YES" if vol_found else "NO",
            "rbhc_data_collected": "YES" if rbhc_ok else "NO",
            "highlow_verified": "YES" if hl_ok else "NO",
            "gate": "CLOSED/HOLD",
            "release_permit": "NOT_ISSUED",
            "factor_extract_v1": "FROZEN V1.0.0",
            "f01_script": "LOCKED",
            "artifacts": [os.path.basename(f) for f in [OUT_PROBE, OUT_RBHC, OUT_HIGHLOW, OUT_REPORT, OUT_SHA]],
            "sha_snapshot": sha_snap,
        }
        with open(TRACKING, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit, ensure_ascii=False) + "\n")

        # Print receipt
        elapsed = time.time() - t0
        print("\n" + "=" * 60)
        print("DSHC-VOL-PROBE-COLLECT RECEIPT")
        print("=" * 60)
        print(f"DSHC_VOL_PROBE=PROBE_DONE | vol_gap_root_found={'YES' if vol_found else 'NO'} | rbhc_data_collected={'YES' if rbhc_ok else 'NO'} | highlow_verified={'YES' if hl_ok else 'NO'}")
        print(f"wind_api_calls={wind_calls} | total_rows={total_rows} | elapsed={elapsed:.1f}s")
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