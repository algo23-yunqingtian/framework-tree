#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""白名单约束发散产物的脚本化质量审计（口径修正版 2026-09-07）

背景 / 为什么重写：
  原内联审计只做「name 字面比对」，导致系统性误判：
    - 同花顺常按 ID 标注引用（FU00014813）或按中文名引用（镍矿:进口数量:菲律宾→中国（月）），
      甚至两者都不写、只用业务名称描述 → name 字面命中率虚低（48.2%），5 个任务被误判为 0 覆盖。
    - 实测这 5 个「0 覆盖」产物内容全部合格（有子类、有图表设计、声明未编造），
      属审计方法缺陷，非同花顺缺陷。
  本脚本改为 name + ID 双匹配（name 字面 OR id 字面 OR id 出现在产物引用 ID 集合中），
  并额外报告「白名单外引用 ID」——这才是「未遵守白名单」的真正信号。

用法：
  python3 scripts/whitelist_audit.py                 # 审计全部产物，打印表格 + 写 _quality_audit.json
  python3 scripts/whitelist_audit.py --json-only     # 只写 json 不打印
  python3 scripts/whitelist_audit.py --strict        # 把「白名单外引用ID>0」视为不合格
"""
import argparse
import json
import os
import re
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(BASE, "analysis", "knowledge_base.json")
OUT_DIR = os.path.join(BASE, "analysis", "iwencai_whitelist")

# 知几/同花顺常见 ID 形态：FU/a1xxxxxx(期货行情)、IDxxxxxxxx(指标)、CMxxxxxxxxxx(海关)、i/j+数字(铅)
ID_PATTERN = re.compile(r"\b(FU\d{6,8}|a1\d{6,8}|ID\d{8}|CM\d{9,12}|[ij]\d{3,5})\b")
# 图表设计条目：表格中以序号开头的行。
# 注意：同花顺返回的表格分隔符是 TAB（\t）而非 |，且同一份产物可能用 | 或 TAB。
# 必须同时匹配两种，否则 table_rows 恒为 0（实测踩坑）。
TABLE_ROW_PATTERN = re.compile(r"(?m)^\s*\d+\s*[|｜\t]")


def load_kb():
    with open(KB_PATH, encoding="utf-8") as f:
        return json.load(f)


def audit_one(variety, board, text, whitelist):
    """审计单个产物。返回记录 dict。"""
    cited_ids = set(ID_PATTERN.findall(text))
    wl_ids = {w["id"] for w in whitelist if w.get("id")}

    matched = []
    for w in whitelist:
        iid = w.get("id", "")
        nm = w.get("name", "")
        ok = False
        if iid and iid in cited_ids:
            ok = True
        elif iid and iid in text:
            ok = True
        elif nm and nm in text:
            ok = True
        if ok:
            matched.append(w)

    out_of_list = sorted(cited_ids - wl_ids)
    table_rows = len(TABLE_ROW_PATTERN.findall(text))  # 注意 findall 不带 flags，靠 pattern 内嵌 (?m)

    # 子类标题：同花顺格式多变，实测至少 4 种：
    #   阿拉伯数字「1. xxx」、中文序号「一、xxx」「（一）xxx」、
    #   「子类1：xxx」「子目录一：xxx」
    # 全部纳入，避免误判合格产物为无结构（NI_cost 实测踩坑）。
    has_subdir = bool(re.search(
        r"(?m)^\s*("
        r"\d+[.、]"                      # 1. / 1、
        r"|[一二三四五六七八九十]+[.、]"  # 一、/ 一.
        r"|[（(][一二三四五六七八九十\d][)）]"  # （一）/ (1)
        r"|子类\s*\d+"                    # 子类1
        r"|子目录\s*[一二三四五六七八九十\d]"  # 子目录一
        r")",
        text,
    ))
    declares_no_fabrication = any(kw in text for kw in ["未编造", "无编造", "不编造", "未列", "不派生"])

    return {
        "variety": variety,
        "board": board,
        "whitelist_count": len(whitelist),
        "chars": len(text),
        "cited_ids": len(cited_ids),
        "matched": len(matched),
        "coverage_pct": round(100.0 * len(matched) / max(len(whitelist), 1), 1),
        "table_rows": table_rows,
        "has_subdir": has_subdir,
        "declares_no_fabrication": declares_no_fabrication,
        "out_of_list_ids": out_of_list,
        "out_of_list_count": len(out_of_list),
        "has_answer": len(text) > 300,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    kb = load_kb()
    results = []
    for fn in sorted(os.listdir(OUT_DIR)):
        if not fn.endswith("_whitelist.md") or fn.startswith("_"):
            continue
        task = fn[: -len("_whitelist.md")]
        parts = task.split("_")
        if len(parts) != 2:
            continue
        variety, board = parts
        text = open(os.path.join(OUT_DIR, fn), encoding="utf-8").read()
        whitelist = kb.get(variety, {}).get(board, [])
        rec = audit_one(variety, board, text, whitelist)
        rec["task"] = task
        # 合格判定：有答案 + 有子类结构 + 覆盖率>0 或白名单本就极小
        rec["pass"] = bool(rec["has_answer"] and rec["has_subdir"] and (rec["coverage_pct"] > 0 or rec["whitelist_count"] <= 4))
        if args.strict:
            rec["pass"] = rec["pass"] and rec["out_of_list_count"] == 0
        results.append(rec)

    results.sort(key=lambda r: r["task"])

    out_json = os.path.join(OUT_DIR, "_quality_audit.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)

    if args.json_only:
        return

    # --- 打印 ---
    covs = [r["coverage_pct"] for r in results]
    total_ooo = len({i for r in results for i in r["out_of_list_ids"]})
    fails = [r["task"] for r in results if not r["pass"]]

    print(f"{'task':<18}{'wl':>4}{'match':>6}{'cov%':>7}{'tbl':>5}{'外源':>5}  pass")
    for r in results:
        mark = "OK" if r["pass"] else "FAIL"
        print(
            f"{r['task']:<18}{r['whitelist_count']:>4}{r['matched']:>6}"
            f"{r['coverage_pct']:>7}{r['table_rows']:>5}{r['out_of_list_count']:>5}  {mark}"
        )

    print()
    print(f"产物数: {len(results)}")
    print(f"覆盖率: avg={round(sum(covs)/len(covs),1)}%  min={min(covs)}%  max={max(covs)}%")
    print(f"白名单外引用ID(去重): {total_ooo}  <- 唯一真实违规信号")
    print(f"不合格: {len(fails)} {fails}")

    g = defaultdict(list)
    for r in results:
        g[r["variety"]].append(r["coverage_pct"])
    print("\n按品种覆盖率:")
    for v in sorted(g):
        print(f"  {v}: n={len(g[v])} avg={round(sum(g[v])/len(g[v]),1)}%")


if __name__ == "__main__":
    main()
