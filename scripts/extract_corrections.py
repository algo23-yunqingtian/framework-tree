#!/usr/bin/env python3
"""
Extract A-level indicators from 27 correction files, compare with indicators_v1.json,
identify gaps. Output a structured JSON report.
"""
import os, re, json, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORRECTION_DIR = os.path.join(BASE, "translation-workspace", "correction")
INDICATORS_PATH = os.path.join(BASE, "data", "indicators_v1.json")

# All correction files to process
CORRECTION_FILES = []

# Root-level ZN files
for f in ["ZN_supply_correction_20260901.md", "ZN_库存_correction_20260901.md",
          "ZN_进出口_correction_20260901.md", "ZN_需求_correction_20260901.md"]:
    p = os.path.join(CORRECTION_DIR, f)
    if os.path.exists(p):
        CORRECTION_FILES.append(p)

# Per-variety directories: AL, CU, NI, SN (new format)
for variety in ["AL", "CU", "NI", "SN"]:
    d = os.path.join(CORRECTION_DIR, variety)
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith("_correction_20260902.md"):
                CORRECTION_FILES.append(os.path.join(d, f))

# cu-al-ni-sn batch directory (v3 format with _correct_ suffix)
CUALNI_DIR = os.path.join(CORRECTION_DIR, "cu-al-ni-sn")
if os.path.isdir(CUALNI_DIR):
    for sub in sorted(os.listdir(CUALNI_DIR)):
        subpath = os.path.join(CUALNI_DIR, sub)
        if os.path.isdir(subpath):
            for f in sorted(os.listdir(subpath)):
                if f.endswith("_correct_20260902.md") and "_iwencai" not in f:
                    CORRECTION_FILES.append(os.path.join(subpath, f))

print(f"Found {len(CORRECTION_FILES)} correction files")
for f in CORRECTION_FILES:
    print(f"  {os.path.relpath(f, BASE)}")

# Load existing indicators
print("\n--- Loading indicators_v1.json ---")
with open(INDICATORS_PATH, encoding="utf-8") as f:
    indicators_data = json.load(f)
existing_indicators = indicators_data.get("indicators", {})
print(f"Existing indicators: {len(existing_indicators)}")

# Extract A-level indicators from correction files
all_a_level = []

for filepath in CORRECTION_FILES:
    relpath = os.path.relpath(filepath, BASE)
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  SKIP {relpath}: {e}")
        continue

    lines = content.split("\n")
    a_count = 0
    b_count = 0
    c_count = 0

    current_node = ""
    for line in lines:
        # Track section headers for ZN old format node extraction
        header_match = re.match(r'^##\s+([\d.]+)\s', line)
        if header_match:
            current_node = header_match.group(1)

        if re.match(r'\|\s*\d+', line):
            parts = [p.strip() for p in line.split("|")]

            # Variable-length row: scan for level marker and zhiji_id pattern
            if len(parts) >= 5:
                # Scan for level marker (✅A/⚠️B/❌C) anywhere in parts
                level_marker = ""
                level_idx = -1
                for i, p in enumerate(parts):
                    if "✅" in p and "A" in p:
                        level_marker, level_idx = "A", i
                        break
                    elif "⚠" in p and "B" in p:
                        level_marker, level_idx = "B", i
                        break
                    elif "❌" in p and "C" in p:
                        level_marker, level_idx = "C", i
                        break

                if level_marker and level_idx >= 0:
                    # New format with level marker: find zhiji_id by scanning backward from level
                    zhiji_id = ""
                    zhiji_name = ""
                    name = parts[3].strip() if len(parts) > 3 else ""
                    node = parts[2].strip() if len(parts) > 2 else ""

                    # Look for zhiji_id scanning ALL parts before level (pick the last ID-pattern match)
                    for j in range(level_idx - 1, -1, -1):
                        val = parts[j].strip()
                        if re.match(r'^(ID|FU|a10|CM|LC|RE)\d+[A-Za-z0-9]*', val):
                            zhiji_id = val
                            zhiji_name = parts[j+1].strip() if j+1 < len(parts) else ""
                            break

                    if level_marker == "A" and zhiji_id and zhiji_id not in ("—", "", "🔴", "无数据"):
                        a_count += 1
                        all_a_level.append({
                            "source": relpath,
                            "node": node,
                            "name": name,
                            "zhiji_id": zhiji_id,
                            "zhiji_name": zhiji_name,
                            "level": "A",
                            "format": "new_with_marker"
                        })
                    elif level_marker == "B":
                        b_count += 1
                    elif level_marker == "C":
                        c_count += 1
                elif len(parts) >= 10:
                    # ZN old format or new format without level marker
                    # Check if parts[7] or parts[8] contains A/B/C level
                    for check_idx in [7, 8]:
                        if check_idx < len(parts):
                            p = parts[check_idx].strip()
                            if p == "A":
                                level_marker = "A"
                                break
                            elif p == "B":
                                level_marker = "B"
                                break
                            elif p == "C":
                                level_marker = "C"
                                break

                    if level_marker == "A":
                        # New format (AL/CU/NI/SN without emoji): parts[5]=zhiji_id, parts[6]=zhiji_name
                        zhiji_id = parts[5].strip() if len(parts) > 5 else ""
                        zhiji_name = parts[6].strip() if len(parts) > 6 else ""
                        name = parts[3].strip() if len(parts) > 3 else ""
                        node = parts[2].strip() if len(parts) > 2 else ""

                        if zhiji_id and zhiji_id not in ("—", "", "🔴"):
                            a_count += 1
                            all_a_level.append({
                                "source": relpath,
                                "node": node,
                                "name": name,
                                "zhiji_id": zhiji_id,
                                "zhiji_name": zhiji_name,
                                "level": "A",
                                "format": "new_plain"
                            })
                    elif not level_marker and len(parts) >= 11:
                        # ZN old format: parts[6]=zhiji_id, parts[7]=zhiji_name
                        zhiji_id = parts[6].strip()
                        zhiji_name = parts[7].strip()
                        concept = parts[2].strip()
                        freq = parts[8].strip()
                        unit = parts[9].strip()

                        zhiji_id_clean = zhiji_id.replace("**", "")
                        if zhiji_id_clean and "缺项" not in zhiji_id_clean and "同上" not in zhiji_id_clean and zhiji_id_clean not in ("—", "", "🔴"):
                            a_count += 1
                            all_a_level.append({
                                "source": relpath,
                                "node": current_node,
                                "name": concept,
                                "zhiji_id": zhiji_id_clean,
                                "zhiji_name": zhiji_name.replace("**", ""),
                                "level": "A",
                                "format": "zn_old",
                                "freq": freq,
                                "unit": unit
                            })

            # New format (AL/CU/NI/SN): 10 parts (0=empty, 1=#, 2=node, 3=name, 4=keywords, 5=zhiji_id, 6=zhiji_name, 7=level, 8=notes, 9=empty)
            elif len(parts) == 10:
                level = parts[7].strip()
                zhiji_id = parts[5].strip()
                zhiji_name = parts[6].strip()
                node = parts[2].strip()
                name = parts[3].strip()

                if level == "A":
                    a_count += 1
                    if zhiji_id and zhiji_id not in ("—", "", "🔴"):
                        all_a_level.append({
                            "source": relpath,
                            "node": node,
                            "name": name,
                            "zhiji_id": zhiji_id,
                            "zhiji_name": zhiji_name,
                            "level": "A",
                            "format": "new"
                        })
                elif level == "B":
                    b_count += 1
                elif level == "C":
                    c_count += 1

    print(f"  {relpath}: A={a_count} B={b_count} C={c_count}")

print(f"\n--- Extracted {len(all_a_level)} A-level entries ---")

# Deduplicate by zhiji_id
seen_ids = set()
unique_a = []
for entry in all_a_level:
    key = entry["zhiji_id"]
    if key not in seen_ids:
        seen_ids.add(key)
        unique_a.append(entry)

print(f"Unique by zhiji_id: {len(unique_a)}")

# Check which are already in indicators_v1.json
existing_ids = set()
for key, val in existing_indicators.items():
    ids = val.get("ids", {})
    if isinstance(ids, dict):
        for variety_code, zhiji_id in ids.items():
            existing_ids.add(zhiji_id)
    # Also check zhiji_id field directly
    if "zhiji_id" in val:
        existing_ids.add(val["zhiji_id"])
    # Also check ids as string
    if "ids" in val and isinstance(val["ids"], str):
        existing_ids.add(val["ids"])

print(f"\nExisting indicator IDs in JSON: {len(existing_ids)}")

# Find which A-level entries are NOT yet registered
new_entries = []
already_registered = 0
for entry in unique_a:
    if entry["zhiji_id"] in existing_ids:
        already_registered += 1
    else:
        new_entries.append(entry)

print(f"Already registered: {already_registered}")
print(f"Not yet registered (new): {len(new_entries)}")

# Output results
output = {
    "correction_files_processed": len(CORRECTION_FILES),
    "total_a_level_extracted": len(all_a_level),
    "unique_a_level": len(unique_a),
    "already_registered": already_registered,
    "not_registered": len(new_entries),
    "new_entries": new_entries
}

outpath = os.path.join(BASE, "scripts", "correction_extract_report.json")
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nReport saved to {outpath}")
print(f"\n=== SUMMARY ===")
print(f"Correction files: {len(CORRECTION_FILES)}")
print(f"A-level extracted: {len(all_a_level)}")
print(f"Unique A-level: {len(unique_a)}")
print(f"Already registered: {already_registered}")
print(f"New to register: {len(new_entries)}")
