#!/usr/bin/env python3
"""
Extract duplicate zhiji IDs from zhiji_fetch_result.json
T3 of DSH-B_GITHUB_SHARE_PUSH_V85_20260928
"""
import json, sys, os
from collections import defaultdict

INPUT = r"D:\DSH_WORK\framework-tree\analysis_temp\end2end_zhiji_fetch\zhiji_fetch_result.json"
OUTPUT = r"D:\DSH_WORK\framework-tree\analysis_temp\end2end_zhiji_fetch\duplicate_id_list.json"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

# Collect all matched_id occurrences
id_occurrences = defaultdict(list)
for entry in data["detailed_results"]:
    mid = entry.get("matched_id", "")
    id_occurrences[mid].append({
        "trace_id": entry.get("trace_id"),
        "sample_id": entry.get("sample_id"),
        "chart_name": entry.get("chart_name"),
        "matched_name": entry.get("matched_name"),
        "variety": entry.get("variety"),
        "data_points": entry.get("data_points"),
        "unit": entry.get("unit"),
        "data_success": entry.get("data_success")
    })

# Find IDs with >1 occurrence
duplicates = []
total_entries = len(data["detailed_results"])
unique_count = len(id_occurrences)
dup_id_count = 0
dup_entry_count = 0

for mid, occ_list in sorted(id_occurrences.items(), key=lambda x: len(x[1]), reverse=True):
    if len(occ_list) > 1:
        dup_id_count += 1
        dup_entry_count += len(occ_list)
        duplicates.append({
            "zhiji_id": mid,
            "occurrence_count": len(occ_list),
            "entries": occ_list
        })

result = {
    "work_order": "DSH-B_GITHUB_SHARE_PUSH_V85_20260928",
    "source_file": "zhiji_fetch_result.json",
    "total_entries": total_entries,
    "unique_zhiji_ids": unique_count,
    "duplicate_id_count": dup_id_count,
    "duplicate_entry_count": dup_entry_count,
    "dedup_saving": total_entries - unique_count,
    "note": "HERMES 清理看板时，相同 zhiji_id 只保留 1 条，避免重复 API 请求",
    "duplicates": duplicates
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"✅ duplicate_id_list.json written")
print(f"   Total entries: {total_entries}")
print(f"   Unique IDs:    {unique_count}")
print(f"   Duplicate IDs: {dup_id_count}")
print(f"   Duplicate entries (extra): {total_entries - unique_count}")
print(f"   Output: {OUTPUT}")
