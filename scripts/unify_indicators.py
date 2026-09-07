#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一两 agent 产物格式 → analysis/unified_indicators.json

数据源1: analysis/knowledge_base.json       (白名单, 我的产物, 1192条)
数据源2: analysis/zhiji_match_v4/*.json      (v4匹配, 另一agent, 2667条)
输出:   analysis/unified_indicators.json     (统一格式, 可直接用于建页)

统一格式:
{
  "variety": "CU",
  "board": "price",
  "node": "2.1",
  "node_name": "盘面结构",
  "indicators": [
    {
      "id": "FU00014999",
      "name": "SHFE：镍：主力合约：收盘价（日）",
      "freq": "daily",          # 标准化英文频率
      "freq_raw": "日",          # 原始频率(可空)
      "unit": "元/吨",
      "points": 2779,            # 数据点数
      "last_date": "2026-08-28",
      "match_level": "A",        # A/B/C
      "verified": true,          # 是否已验证
      "sources": ["whitelist","v4"]  # 来源
    }
  ]
}

用法:
  python3 scripts/unify_indicators.py
  python3 scripts/unify_indicators.py --variety CU
"""
import argparse
import json
import os
import re
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(BASE, "analysis", "knowledge_base.json")
V4_DIR = os.path.join(BASE, "analysis", "zhiji_match_v4")
OUT_PATH = os.path.join(BASE, "analysis", "unified_indicators.json")

# 板块映射（v4用node如"2.1"→board"price"）
NODE_BOARD_MAP = {
    "2": "price", "3": "supply", "4": "inventory",
    "5": "demand", "6": "trade", "7": "cost", "8": "balance",
}
BOARD_CN = {
    "price": "价格", "supply": "供给", "inventory": "库存",
    "demand": "需求", "trade": "进出口", "cost": "成本", "balance": "平衡",
}

# 频率标准化映射
FREQ_MAP = {
    "日": "daily", "daily": "daily", "D": "daily", "d": "daily",
    "周": "weekly", "weekly": "weekly", "W": "weekly", "w": "weekly",
    "月": "monthly", "monthly": "monthly", "M": "monthly", "m": "monthly",
    "季": "quarterly", "quarterly": "quarterly", "Q": "quarterly", "q": "quarterly",
    "年": "yearly", "yearly": "yearly", "Y": "yearly", "y": "yearly",
    None: "unknown", "": "unknown", "null": "unknown",
}


def normalize_freq(raw):
    if raw is None:
        return "unknown"
    raw = str(raw).strip()
    return FREQ_MAP.get(raw, FREQ_MAP.get(raw.lower(), "unknown"))


def node_to_board(node):
    """'2.1' → 'price', '3.1.1' → 'supply'"""
    if not node:
        return None
    top = str(node).split(".")[0]
    return NODE_BOARD_MAP.get(top)


def load_whitelist():
    """加载白名单知识库"""
    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)
    result = defaultdict(lambda: defaultdict(list))
    for variety, boards in kb.items():
        if not isinstance(boards, dict):
            continue
        for board, items in boards.items():
            if not isinstance(items, list):
                continue
            for w in items:
                result[variety][board].append({
                    "id": w.get("id", ""),
                    "name": w.get("name", ""),
                    "freq": normalize_freq(w.get("freq")),
                    "freq_raw": w.get("freq"),
                    "unit": w.get("unit", ""),
                    "points": w.get("points", 0),
                    "last_date": w.get("last_date", ""),
                    "match_level": w.get("match_level", "A"),  # 白名单默认A级
                    "verified": True,
                    "sources": ["whitelist"],
                    "iwencai_indicator": "",
                    "iwencai_priority": "",
                    "notes": "",
                })
    return result


def load_v4():
    """加载v4匹配产物"""
    result = defaultdict(lambda: defaultdict(list))
    if not os.path.isdir(V4_DIR):
        return result
    for fn in sorted(os.listdir(V4_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(V4_DIR, fn), encoding="utf-8") as f:
            d = json.load(f)
        variety = d.get("variety", fn.split("_")[0])
        for m in d.get("matches", []):
            node = m.get("node", "")
            board = node_to_board(node)
            if not board:
                continue
            result[variety][board].append({
                "id": m.get("zhiji_id", ""),
                "name": m.get("zhiji_name", ""),
                "freq": normalize_freq(m.get("zhiji_freq")),
                "freq_raw": m.get("zhiji_freq"),
                "unit": m.get("zhiji_unit", ""),
                "points": 0,  # v4没有points字段
                "last_date": "",
                "match_level": m.get("match_level", "C"),
                "verified": m.get("verified", False),
                "sources": ["v4"],
                "iwencai_indicator": m.get("iwencai_indicator", ""),
                "iwencai_priority": m.get("iwencai_priority", ""),
                "node": node,
                "node_name": m.get("node_name", ""),
                "notes": m.get("notes", ""),
            })
    return result


def merge(wl, v4):
    """合并两套数据：按 (variety, board, id) 去重合并"""
    merged = defaultdict(lambda: defaultdict(dict))

    # 先放白名单（高质量，优先）
    for variety, boards in wl.items():
        for board, items in boards.items():
            for item in items:
                key = item["id"]
                if not key:
                    continue
                if key not in merged[variety][board]:
                    merged[variety][board][key] = item
                else:
                    # 合并sources
                    existing = merged[variety][board][key]
                    existing["sources"] = sorted(set(existing["sources"] + item["sources"]))

    # 再放v4（补充白名单没有的）
    for variety, boards in v4.items():
        for board, items in boards.items():
            for item in items:
                key = item["id"]
                if not key:
                    continue
                if key not in merged[variety][board]:
                    merged[variety][board][key] = item
                else:
                    # 白名单已有→补v4的元信息
                    existing = merged[variety][board][key]
                    existing["sources"] = sorted(set(existing["sources"] + item["sources"]))
                    if not existing.get("iwencai_indicator"):
                        existing["iwencai_indicator"] = item.get("iwencai_indicator", "")
                    if not existing.get("iwencai_priority"):
                        existing["iwencai_priority"] = item.get("iwencai_priority", "")
                    if not existing.get("node"):
                        existing["node"] = item.get("node", "")
                    if not existing.get("node_name"):
                        existing["node_name"] = item.get("node_name", "")
                    if not existing.get("notes"):
                        existing["notes"] = item.get("notes", "")
                    # v4的match_level覆盖（更准确）
                    existing["match_level"] = item.get("match_level", existing["match_level"])

    # 转dict→list
    output = defaultdict(lambda: defaultdict(list))
    stats = {"varieties": 0, "boards": 0, "total": 0, "by_source": {"whitelist_only": 0, "v4_only": 0, "both": 0}}
    for variety in sorted(merged):
        stats["varieties"] += 1
        for board in sorted(merged[variety]):
            stats["boards"] += 1
            items = list(merged[variety][board].values())
            output[variety][board] = items
            stats["total"] += len(items)
            for item in items:
                s = item["sources"]
                if "whitelist" in s and "v4" in s:
                    stats["by_source"]["both"] += 1
                elif "whitelist" in s:
                    stats["by_source"]["whitelist_only"] += 1
                else:
                    stats["by_source"]["v4_only"] += 1

    return output, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variety", help="只输出指定品种")
    args = ap.parse_args()

    print("加载白名单...")
    wl = load_whitelist()
    wl_total = sum(len(items) for v in wl.values() for b in v.values() for items in [b] for _ in [1])
    print(f"  白名单: {wl_total} 条")

    print("加载v4...")
    v4 = load_v4()
    v4_total = sum(len(items) for v in v4.values() for b in v.values() for items in [b] for _ in [1])
    print(f"  v4: {v4_total} 条")

    print("合并...")
    merged, stats = merge(wl, v4)

    if args.variety:
        merged = {args.variety: merged.get(args.variety, {})}

    # 写入
    out = {"_meta": {"generator": "unify_indicators.py", "stats": stats}, "data": dict(merged)}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # 打印统计
    print(f"\n=== 统一指标表统计 ===")
    print(f"品种数: {stats['varieties']}")
    print(f"板块数: {stats['boards']}")
    print(f"总指标数: {stats['total']}")
    print(f"来源: 白名单独有={stats['by_source']['whitelist_only']} v4独有={stats['by_source']['v4_only']} 两源都有={stats['by_source']['both']}")

    # 按品种×板块
    print(f"\n{'品种':<5}{'price':>7}{'supply':>8}{'inv':>6}{'dem':>6}{'trade':>7}{'cost':>6}{'bal':>6}{'合计':>7}")
    for v in sorted(merged):
        counts = {b: len(merged[v].get(b, [])) for b in ["price","supply","inventory","demand","trade","cost","balance"]}
        total = sum(counts.values())
        print(f"{v:<5}{counts['price']:>7}{counts['supply']:>8}{counts['inventory']:>6}{counts['demand']:>6}{counts['trade']:>7}{counts['cost']:>6}{counts['balance']:>6}{total:>7}")

    # 频率标准化检查
    print(f"\n频率标准化检查:")
    freq_stats = defaultdict(int)
    for v in merged:
        for b in merged[v]:
            for item in merged[v][b]:
                freq_stats[item["freq"]] += 1
    for f, c in sorted(freq_stats.items(), key=lambda x: -x[1]):
        print(f"  {f}: {c}")

    print(f"\n输出: {OUT_PATH} ({os.path.getsize(OUT_PATH)//1024}KB)")


if __name__ == "__main__":
    main()
