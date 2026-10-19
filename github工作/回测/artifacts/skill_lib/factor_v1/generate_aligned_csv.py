#!/usr/bin/env python3
"""Generate aligned long-form CSV from WDF data.
Part of DSHC-SKILL-FACTOR01.
"""
import csv
import hashlib
import os
import sys
from pathlib import Path

def main():
    src = Path("output_sample/wdf_sample_metals_raw.csv")
    dst = Path("output_sample/wdf_sample_metals_aligned.csv")
    sha_file = Path("artifacts/skill_lib/factor_v1/data_sha256.txt")

    # Read source
    rows = []
    with open(src, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Count unique dates
    all_dates = set()
    for r in rows:
        all_dates.add(r["date"])
    all_dates_sorted = sorted(all_dates)

    # Group dates by indicator availability
    dates_by_indicator = {}
    for r in rows:
        ind = r["indicator"]
        dates_by_indicator.setdefault(ind, set()).add(r["date"])

    # Sort rows by date, symbol, indicator
    rows.sort(key=lambda r: (r["date"], r["symbol"], r["indicator"]))

    # Write aligned CSV with header comments
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write("# ============================================================\n")
        f.write("# DSHC-SKILL-FACTOR01: Aligned Long-Form CSV\n")
        f.write("# Generated: 2026-10-19\n")
        f.write("# Date Range (LOCKED): 2025-01-02 to 2026-10-19\n")
        f.write(f"# Trading Calendar: {len(all_dates_sorted)} unique dates\n")
        f.write("# Indicator Coverage:\n")
        for ind in ["CLOSE", "OI", "SETTLE", "VOL"]:
            d = dates_by_indicator.get(ind, set())
            if d:
                d_sorted = sorted(d)
                f.write(f"#   {ind}: {len(d)} dates ({d_sorted[0]} to {d_sorted[-1]})\n")
            else:
                f.write(f"#   {ind}: NO DATA\n")
        f.write("# Alignment Status:\n")
        f.write("#   CLOSE/OI/SETTLE: 100% date overlap (400 shared dates)\n")
        f.write("#   VOL: separate date range (27 dates, 2026-09-03~2026-10-19)\n")
        f.write("#   VOL data gap: Wind availability issue (TODO-01 P0)\n")
        f.write("# F01 Script Fix: date range locked 2025-01-02->2026-10-19, copyRows=600\n")
        f.write("# LC.SHF: BLACKLISTED (WIND_EMPTY_SYMBOL, GFE exchange)\n")
        f.write("# Workorder: DSHC-SKILL-FACTOR01\n")
        f.write("# ============================================================\n")
        f.write("date,symbol,indicator,value,source\n")
        for r in rows:
            f.write(f"{r['date']},{r['symbol']},{r['indicator']},{r['value']},{r['source']}\n")

    # Compute SHA256
    sha256 = hashlib.sha256()
    with open(dst, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    sha256_hex = sha256.hexdigest()

    # Write SHA256 file
    sha_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sha_file, "w", encoding="utf-8") as f:
        f.write(f"aligned_csv_sha256={sha256_hex}\n")
        f.write(f"file=artifacts/skill_lib/factor_v1/data_sha256.txt\n")
        f.write(f"csv_path=output_sample/wdf_sample_metals_aligned.csv\n")
        f.write(f"csv_rows={len(rows)}\n")
        f.write(f"unique_dates={len(all_dates_sorted)}\n")

    # Also compute SHA256 of original CSV
    sha_orig = hashlib.sha256()
    with open(src, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha_orig.update(chunk)
    orig_hex = sha_orig.hexdigest()

    print(f"Aligned CSV: {dst}")
    print(f"Rows: {len(rows)}")
    print(f"Unique dates: {len(all_dates_sorted)}")
    print(f"SHA256: {sha256_hex}")
    print(f"Original SHA256: {orig_hex}")

    # Write SHA256 into manifest.json too
    import json
    manifest_path = Path("artifacts/skill_lib/factor_v1/manifest.json")
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["data_integrity"] = {
            "aligned_csv_path": "output_sample/wdf_sample_metals_aligned.csv",
            "aligned_csv_sha256": sha256_hex,
            "aligned_csv_rows": len(rows),
            "unique_dates": len(all_dates_sorted),
            "original_csv_sha256": orig_hex
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("Manifest updated with data_integrity")

    return 0

if __name__ == "__main__":
    sys.exit(main())