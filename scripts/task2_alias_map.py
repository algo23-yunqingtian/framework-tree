#!/usr/bin/env python3
"""Task 2: Build THS-to-Zhiji alias dictionary.

Maps THS natural language short names (e.g. "LME锌库存") to
Zhiji registered full names (e.g. "LME：锌：3个月合约：收盘价").

Covers all registered indicators (621+ A-grade + B-grade).
Eliminates the 84-100% false-loss rate caused by name mismatch.

Output: docs/alias_metadb/thsh_zhiji_alias_map.json
"""
import json, os, re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IND_PATH = os.path.join(ROOT, "data", "indicators_v1.json")
FINAL_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_final.json")
FINAL_5M_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_final_5m.json")
SEARCH_5M_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_search_results_5m.json")
VERIFY_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_verify_summary.json")
OUT_DIR = os.path.join(ROOT, "docs", "alias_metadb")
OUT_PATH = os.path.join(OUT_DIR, "thsh_zhiji_alias_map.json")

CN = {"CU": "铜", "AL": "铝", "ZN": "锌", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}

# THS name patterns: short forms used in iwencai/decision context
# e.g. "LME锌库存" → "LME：锌：3个月合约：收盘价"
# e.g. "沪铜收盘价" → "上期所：铜：主力合约：收盘价"

def build_ths_name(query, zhiji_name, code):
    """Build a THS-style short name from the query and Zhiji name."""
    # If query already looks like a THS name, use it
    # Otherwise, create a shortened version
    n = re.sub(r"【[^】]*】", "", query).strip()
    # Remove parenthetical units
    n = re.sub(r"[（(][^）)]*[）)]", "", n).strip()
    # Remove trailing commas/periods
    n = n.rstrip(",;。、 ")
    return n

def main():
    print("=" * 60)
    print("Task 2: Build THS-to-Zhiji Alias Dictionary")
    print("=" * 60)

    doc = json.load(open(IND_PATH, encoding="utf-8"))
    ind = doc["indicators"]

    # Load final.json files for query→zhiji mapping
    final_cu_al = json.load(open(FINAL_PATH, encoding="utf-8"))
    final_5m = json.load(open(FINAL_5M_PATH, encoding="utf-8"))

    # Build mapping: {ths_name: {zhiji_name, zhiji_id, code, tier, nodes, indicator_key}}
    alias_map = {}
    stats = {"total_registered": 0, "mapped": 0, "by_tier": {}, "by_code": {}}

    # Process indicators_v1.json - these are already registered
    for key, v in ind.items():
        stats["total_registered"] += 1
        code = None
        for c in ["CU", "AL", "ZN", "NI", "SN", "SI", "LI", "PB"]:
            if c in (v.get("ids") or {}):
                code = c
                break
        if not code:
            # Try lowercase prefix
            kparts = key.split("_")
            if kparts:
                code = kparts[0].upper()
                if code not in CN:
                    code = None

        zhiji_name = v.get("name", "")
        zhiji_id = ""
        for c in ["CU", "AL", "ZN", "NI", "SN", "SI", "LI", "PB"]:
            idv = (v.get("ids") or {}).get(c)
            if idv:
                zhiji_id = idv
                break

        tier = v.get("_tier", "")
        origin = v.get("_origin", "")

        # Extract THS name from origin or create one
        ths_name = ""
        if origin:
            # _origin format: "step3_CU_query..." or "step3_5m_ZN_query..."
            m = re.match(r"step3_(?:5m_)?([A-Z]+)_(.+)", origin)
            if m:
                ths_name = m.group(2)
        if not ths_name:
            # Fallback: use the indicator name as THS name
            ths_name = zhiji_name

        # Build a short THS-style name
        short_ths = build_ths_name(ths_name, zhiji_name, code or "")

        entry = {
            "zhiji_name": zhiji_name,
            "zhiji_id": zhiji_id,
            "code": code or "",
            "tier": tier or "unknown",
            "indicator_key": key,
            "unit": v.get("unit", ""),
            "freq": v.get("freq", ""),
        }

        # Add to alias map (both short and long THS names)
        if short_ths and short_ths not in alias_map:
            alias_map[short_ths] = entry
            stats["mapped"] += 1

        # Also add the query name as alias if different
        if ths_name and ths_name != short_ths and ths_name not in alias_map:
            alias_map[ths_name] = entry
            stats["mapped"] += 1

        # Track by tier and code
        t = tier or "unknown"
        stats["by_tier"][t] = stats["by_tier"].get(t, 0) + 1
        c = code or "unknown"
        stats["by_code"][c] = stats["by_code"].get(c, 0) + 1

    # Also process from final.json files to get THS query names for registered indicators
    # This ensures we capture the exact THS names used in decision/divergence
    query_to_indicator = {}

    for code in ["CU", "AL"]:
        for q, v in final_cu_al.get(code, {}).items():
            if v.get("tier") in ("A", "B") and v.get("chosen"):
                zhiji_id = v["chosen"].get("id", "")
                zhiji_name = v["chosen"].get("name", "")
                # Find which indicator key maps to this zhiji_id
                for key, iv in ind.items():
                    for c, idv in (iv.get("ids") or {}).items():
                        if idv == zhiji_id:
                            if q not in alias_map:
                                alias_map[q] = {
                                    "zhiji_name": zhiji_name,
                                    "zhiji_id": zhiji_id,
                                    "code": code,
                                    "tier": v["tier"],
                                    "indicator_key": key,
                                    "unit": iv.get("unit", ""),
                                    "freq": iv.get("freq", ""),
                                }
                                stats["mapped"] += 1
                            break

    for code in ["ZN", "NI", "SN", "SI", "LI"]:
        for q, v in final_5m.get(code, {}).items():
            if v.get("tier") == "B" and v.get("chosen"):
                zhiji_id = v["chosen"].get("id", "")
                zhiji_name = v["chosen"].get("name", "")
                for key, iv in ind.items():
                    for c, idv in (iv.get("ids") or {}).items():
                        if idv == zhiji_id:
                            if q not in alias_map:
                                alias_map[q] = {
                                    "zhiji_name": zhiji_name,
                                    "zhiji_id": zhiji_id,
                                    "code": code,
                                    "tier": "B",
                                    "indicator_key": key,
                                    "unit": iv.get("unit", ""),
                                    "freq": iv.get("freq", ""),
                                }
                                stats["mapped"] += 1
                            break

    # Add common THS short-form aliases for frequent patterns
    # These are natural language short names commonly used in THS context
    ths_patterns = []
    for ths, entry in list(alias_map.items()):
        code = entry["code"]
        zhiji = entry["zhiji_name"]
        # Create shorter aliases
        short = re.sub(r"（[^）]*）", "", zhiji)
        short = re.sub(r"\([^)]*\)", "", short)
        short = re.sub(r"：", "", short)
        short = short.strip()
        if short != ths and len(short) >= 4 and short not in alias_map:
            alias_map[short] = entry
            stats["mapped"] += 1
            ths_patterns.append((short, zhiji))

    # Output JSON
    os.makedirs(OUT_DIR, exist_ok=True)
    output = {
        "_meta": {
            "description": "THS自然语言简称 → 知几注册全称 映射表",
            "version": "1.0",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "indicators_v1.json v3.49 + step3_final.json",
            "total_aliases": len(alias_map),
            "total_registered_indicators": stats["total_registered"],
            "coverage_note": "覆盖已注册指标+步三最终判定结果",
        },
        "by_tier": stats["by_tier"],
        "by_code": stats["by_code"],
        "aliases": dict(sorted(alias_map.items(), key=lambda x: x[0])),
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n=== Alias Map Statistics ===")
    print("Total registered indicators: %d" % stats["total_registered"])
    print("Total aliases created: %d" % len(alias_map))
    print("\nBy tier:")
    for t, c in sorted(stats["by_tier"].items()):
        print("  %s: %d" % (t, c))
    print("\nBy code:")
    for c, cnt in sorted(stats["by_code"].items(), key=lambda x: -x[1]):
        print("  %s: %d" % (c, cnt))
    print("\nOutput: %s" % OUT_PATH)
    print("Done!")

if __name__ == "__main__":
    main()
