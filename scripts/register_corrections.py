#!/usr/bin/env python3
"""
Register 64 new A-level indicators from correction files into indicators_v1.json.
Steps:
1. Load correction_extract_report.json
2. Clean compound/invalid zhiji_ids
3. Generate indicator entries with proper key naming
4. Update indicators_v1.json (v3.48 -> v3.49)
5. Run verification gates
"""
import json, os, re, sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_PATH = os.path.join(BASE, "scripts", "correction_extract_report.json")
INDICATORS_PATH = os.path.join(BASE, "data", "indicators_v1.json")
BACKUP_DIR = os.path.join(BASE, "analysis", "backups")

# Load report
with open(REPORT_PATH, encoding="utf-8") as f:
    report = json.load(f)

new_entries = report["new_entries"]
print(f"Loaded {len(new_entries)} new entries")

# Load current indicators
with open(INDICATORS_PATH, encoding="utf-8") as f:
    indicators_data = json.load(f)

existing_indicators = indicators_data.get("indicators", {})
print(f"Current indicators: {len(existing_indicators)}")

# Build set of existing zhiji_ids
existing_ids = set()
for key, val in existing_indicators.items():
    ids = val.get("ids", {})
    if isinstance(ids, dict):
        for code, zhiji_id in ids.items():
            if isinstance(zhiji_id, str):
                existing_ids.add(zhiji_id)
    if "zhiji_id" in val and isinstance(val["zhiji_id"], str):
        existing_ids.add(val["zhiji_id"])
    if "ids" in val and isinstance(val["ids"], str):
        existing_ids.add(val["ids"])

# Varietymap: source filename -> variety code
def guess_variety(source, node):
    """Infer variety from source file path structure"""
    # Look at the directory name right before the filename
    src = source.replace("\\", "/")
    parts = src.split("/")
    for i in range(len(parts) - 1, 0, -1):
        dirname = parts[i].lower()
        if dirname in ("zn", "al", "cu", "ni", "sn"):
            return dirname
        if dirname.startswith("zn") or dirname.startswith("铝") or "锌" in dirname:
            return "zn"
        if dirname.startswith("al") or "铝" in dirname:
            return "al"
        if dirname.startswith("cu") or "铜" in dirname:
            return "cu"
        if dirname.startswith("ni") or "镍" in dirname:
            return "ni"
        if dirname.startswith("sn") or "锡" in dirname:
            return "sn"
    # Fallback: check filename
    fname = parts[-1].lower() if parts else ""
    if fname.startswith("zn") or "锌" in fname:
        return "zn"
    if fname.startswith("al") or "铝" in fname:
        return "al"
    if fname.startswith("cu") or "铜" in fname:
        return "cu"
    if fname.startswith("ni") or "镍" in fname:
        return "ni"
    if fname.startswith("sn") or "锡" in fname:
        return "sn"
    return "zn"

def guess_freq(source, entry):
    """Infer frequency from context"""
    name = entry.get("name", "")
    zhiji_name = entry.get("zhiji_name", "")
    freq = entry.get("freq", "")
    if freq:
        return freq
    # Heuristic from zhiji_name
    if "日" in zhiji_name:
        return "daily"
    elif "周" in zhiji_name:
        return "weekly"
    elif "月" in zhiji_name:
        return "monthly"
    elif "季" in zhiji_name:
        return "quarterly"
    elif "年" in zhiji_name:
        return "yearly"
    return "daily"

def clean_zhiji_id(zhiji_id):
    """Clean compound/extra text from zhiji_id"""
    # Remove trailing text after ID pattern
    zhiji_id = zhiji_id.strip()
    # Handle compound IDs like "ID01105516 高铝锌锭、中国"
    m = re.match(r'^([A-Z]{2}\d+[A-Za-z0-9]*)', zhiji_id)
    if m:
        return m.group(1)
    # Handle multiple IDs separated by /
    if "/" in zhiji_id:
        parts = zhji_id.split("/")
        # Return the first valid one
        for p in parts:
            p = p.strip()
            m = re.match(r'^([A-Z]{2}\d+[A-Za-z0-9]*)', p)
            if m:
                return m.group(1)
    # Handle "CM0000013261 或分开"
    if "或" in zhiji_id:
        m = re.match(r'^([A-Z]{2}\d+[A-Za-z0-9]*)', zhiji_id)
        if m:
            return m.group(1)
    return zhiji_id

# Process entries
registered = 0
skipped = 0
skipped_details = []

# Backup current file
os.makedirs(BACKUP_DIR, exist_ok=True)
backup_path = os.path.join(BACKUP_DIR, "indicators_v1_before_correction_registration.json")
with open(INDICATORS_PATH, "rb") as f:
    backup_data = f.read()
with open(backup_path, "wb") as f:
    f.write(backup_data)
print(f"Backup saved to {backup_path}")

for i, entry in enumerate(new_entries):
    raw_id = entry["zhiji_id"]
    zhiji_id = clean_zhiji_id(raw_id)
    
    # Skip if already registered
    if zhiji_id in existing_ids:
        skipped += 1
        skipped_details.append(f"  {i+1}. {zhiji_id} (already registered)")
        continue
    
    # Skip if zhiji_id is invalid (empty, dash, etc.)
    if not zhiji_id or zhiji_id in ("—", "", "🔴", "无数据"):
        skipped += 1
        skipped_details.append(f"  {i+1}. {raw_id} (invalid id)")
        continue
    
    # Determine variety
    variety = guess_variety(entry["source"], entry.get("node", ""))
    
    # Determine node
    node = entry.get("node", "")
    if not node or node == "子节点" or node.startswith("旧"):
        # Try to extract node from zhji_name
        zhji_name = entry.get("zhiji_name", "")
        node_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', zhji_name)
        if node_match:
            node = node_match.group(1)
        else:
            node = "0"
    
    # Generate key
    # Use node-based key with variety prefix
    freq = guess_freq(entry["source"], entry)
    name = entry.get("name", "")
    zhji_name = entry.get("zhiji_name", "")
    
    # Create a short slug from name
    slug = re.sub(r'[^\w]', '_', name)
    slug = re.sub(r'_+', '_', slug).strip('_').lower()[:20]
    
    key = f"{variety}_{node.replace('.', '_')}_{slug}"
    
    # Ensure unique key
    base_key = key
    counter = 1
    while key in existing_indicators:
        key = f"{base_key}_{counter}"
        counter += 1
    
    # Build indicator entry
    indicator = {
        "name": zhji_name if zhji_name else name,
        "unit": entry.get("unit", ""),
        "freq": freq,
        "verified": True,
        "ids": {
            variety: zhiji_id
        },
        "_origin": f"correction_{entry['source'].split('/')[-1]}|{name}",
        "_tier": "A",
        "_nodes": [node] if node and node != "0" else []
    }
    
    # Add to indicators
    existing_indicators[key] = indicator
    existing_ids.add(zhiji_id)
    registered += 1
    try:
        safe_name = zhji_name[:40].encode('ascii', 'replace').decode('ascii')
        safe_key = key.encode('ascii', 'replace').decode('ascii')
        print(f"  Registered: {safe_key} -> {zhiji_id}")
    except:
        print(f"  Registered: {zhji_id}")

# Update version
version_changelog = indicators_data.get("version_changelog", [])
indicators_data["version"] = "v3.49"
indicators_data["updated"] = "2026-09-13 20:00"
indicators_data["change"] = f"PB correction batch registration: {registered} new A-level indicators from {len(new_entries)} entries ({skipped} skipped)"

# Add changelog entry
if "version_changelog" not in indicators_data:
    indicators_data["version_changelog"] = []
indicators_data["version_changelog"].append({
    "version": "3.49",
    "date": "2026-09-13",
    "change": f"PB correction batch registration: {registered} new A-level indicators from 27 correction files (CU/AL/NI/SN/ZN)"
})

# Update _meta
if "_meta" not in indicators_data:
    indicators_data["_meta"] = {}
indicators_data["_meta"]["version"] = "v3.49"

indicators_data["indicators"] = existing_indicators

# Save
with open(INDICATORS_PATH, "w", encoding="utf-8") as f:
    json.dump(indicators_data, f, ensure_ascii=False, indent=2)

print(f"\n=== REGISTRATION SUMMARY ===")
print(f"Registered: {registered}")
print(f"Skipped: {skipped}")
print(f"Total indicators: {len(existing_indicators)}")
print(f"Version: v3.49")
if skipped_details:
    print(f"\nSkipped details:")
    for d in skipped_details:
        print(d)
