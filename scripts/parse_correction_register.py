#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 correction/SI、LI 对照表 md → 结构化注册计划 JSON（dry-run 用）。

提取逻辑：
- 每个 '## X.Y 板块名' 标题 = 一个节点段
- 表格行：概念指标 | 旧映射 | 旧命中 | ... | 知几·SMM id | 知几·Mysteel id | 频率 | 单位 | 备注
- 跳过包含 🔴 移出 / 缺项 / 幻觉 的行；从 SMM/Mysteel 列提取真实 zhiji_id（排除 🔴、—、空）
- 输出：{code: {node: [{concept, smm_id, mysteel_id, unit, freq}]}}
"""
import json, re, sys, os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORR = REPO / "translation-workspace" / "correction"

def parse_node_from_header(h):
    m = re.match(r"^#+\s*(\d+\.\d+)\s*(.*)$", h)
    if m:
        return m.group(1), m.group(2).strip()
    return None, None

def clean_id(s):
    if not s:
        return None
    s = s.strip()
    if not s or s.startswith("🔴") or s in ("—", "-", "—", "—", "—"):
        return None
    # 取第一个 token 形式 id（允许 FU/ID/CM/a/j/s/n 前缀）
    m = re.search(r"([A-Za-z]{1,2}\d{5,15})", s)
    if m:
        return m.group(1)
    return None

def parse_freq(s):
    if not s:
        return None
    for k in ["日", "周", "月", "季", "半年", "年"]:
        if k in s:
            return {"日": "daily", "周": "weekly", "月": "monthly",
                    "季": "quarterly", "半年": "halfyear", "年": "yearly"}[k]
    return None

def parse_file(path):
    nodes = {}
    cur_node = None
    cur_title = None
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        nd, title = parse_node_from_header(line)
        if nd:
            cur_node = nd
            cur_title = title
            nodes.setdefault(cur_node, {"title": title, "rows": []})
            i += 1
            continue
        if cur_node and line.startswith("|") and "概念指标" not in line and "|---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            # 需要至少 5 列；尝试定位概念列(0) 和 最后含 id 的列
            if len(cells) >= 5:
                concept = cells[0]
                # 跳过表头行
                if not concept or concept.startswith("#") or concept == "":
                    i += 1
                    continue
                # 从整行提取所有 id
                all_ids = re.findall(r"(?<![A-Za-z])(?:FU\d{5,8}|ID\d{5,10}|CM\d{7,10}|[ajsn]\d{5,10})", line)
                # 排除 🔴 移出/缺项 的行
                if "移出" in line or "缺项" in line or "幻觉" in line:
                    i += 1
                    continue
                # 排除纯表头/汇总行
                if concept in ("指标", "概念指标", "同花顺·SMM全称", "补充") or len(concept) > 40:
                    i += 1
                    continue
                if all_ids:
                    nodes[cur_node]["rows"].append({
                        "concept": concept,
                        "ids": all_ids,
                        "unit": cells[-3] if len(cells) >= 4 else None,
                        "freq": cells[-2] if len(cells) >= 5 else None,
                    })
        i += 1
    return nodes

def main():
    out = {}
    for code in ["SI", "LI"]:
        d = CORR / code
        if not d.exists():
            continue
        plan = {}
        for f in sorted(d.glob("*_correction_*.md")):
            nodes = parse_file(f)
            for nd, info in nodes.items():
                plan.setdefault(nd, {"title": info["title"], "rows": []})
                for row in info["rows"]:
                    plan[nd]["rows"].append(row)
        out[code] = plan
    outfile = REPO / "analysis" / "iwencai" / "correction_register_plan.json"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(outfile, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 汇总
    for code in ["SI", "LI"]:
        total = 0
        for nd, info in out.get(code, {}).items():
            n = len(info["rows"])
            total += n
            print(f"{code} {nd} {info['title']}: {n} 条")
        print(f"{code} 合计: {total} 条\n")
    print("输出:", outfile)

if __name__ == "__main__":
    main()
