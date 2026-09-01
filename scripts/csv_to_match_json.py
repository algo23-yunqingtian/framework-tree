#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv_to_match_json.py — 把 Agent B 的 CSV 版 Step2 结果转成标准 step2_match_{品种}.json

CSV 列头（B 确认）：
  品种 / 板块 / 子节点 / 图名称 / 同花顺概念名 / 知几ID / 知几名称 / 置信度

字段映射:
  subnode ← 子节点
  name    ← 图名称        ← 待用户确认：若要看原始概念名则改为"同花顺概念名"
  hit_id  ← 知几ID
  hit_name← 知几名称
  grade   ← 置信度 (A/B/C)

用法:
  python3 scripts/csv_to_match_json.py --csv /path/to/B映射.csv
  python3 scripts/csv_to_match_json.py --csv /path/to/B映射.csv --name-field 同花顺概念名

输出: translation-workspace/mapping/{品种}/step2_match_{品种}.json (每个品种一个)
"""
import argparse, csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def find_col(headers, candidates, label):
    """模糊匹配列名，找不到报错。"""
    for c in candidates:
        for h in headers:
            if c in h:
                return h
    print(f"❌ 找不到 {label} 列。已知表头: {headers}")
    sys.exit(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--name-field", default="图名称",
                    help="name 取哪个字段（图名称 或 同花顺概念名），默认 图名称")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"❌ CSV 不存在: {args.csv}")
        sys.exit(1)

    with open(args.csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        col_v = find_col(headers, ["品种"], "品种")
        col_sub = find_col(headers, ["子节点", "节点"], "子节点")
        col_name = find_col(headers, [args.name_field], "name字段(%s)" % args.name_field)
        col_concept = find_col(headers, ["同花顺", "概念"], "同花顺概念名")
        col_id = find_col(headers, ["知几ID", "知几 ID", "ID", "id"], "知几ID")
        col_hname = find_col(headers, ["知几名称", "知几名"], "知几名称")
        col_grade = find_col(headers, ["置信度", "等级", "grade", "命中"], "置信度(grade)")

        rows = list(reader)

    print(f"✅ 读入 {len(rows)} 行，字段: 品种={col_v} 子节点={col_sub} "
          f"name={col_name} 概念名={col_concept} 知几ID={col_id} "
          f"知几名称={col_hname} 置信度={col_grade}")

    # 按品种分组
    from collections import defaultdict
    by_v = defaultdict(dict)
    for r in rows:
        v = (r.get(col_v) or "").strip().upper()
        if not v:
            continue
        sub = (r.get(col_sub) or "?").strip()
        name = (r.get(col_name) or "").strip()
        concept = (r.get(col_concept) or "").strip()
        hid = (r.get(col_id) or "").strip()
        hname = (r.get(col_hname) or "").strip()
        grade = (r.get(col_grade) or "C").strip().upper()
        key = "%s|%s" % (sub, name or concept or "未知")
        by_v[v][key] = {
            "grade": grade, "hit_id": hid, "hit_name": hname,
            "name": name or concept, "subnode": sub,
        }

    if args.dry:
        for v in sorted(by_v):
            g = by_v[v]
            print(f"  {v}: {len(g)} 条 (A={sum(1 for x in g.values() if x['grade']=='A')}/"
                  f"B={sum(1 for x in g.values() if x['grade']=='B')}/"
                  f"C={sum(1 for x in g.values() if x['grade']=='C')})")
        return

    total = 0
    for v, d in by_v.items():
        outdir = os.path.join(ROOT, "translation-workspace", "mapping", v)
        os.makedirs(outdir, exist_ok=True)
        outpath = os.path.join(outdir, "step2_match_%s.json" % v)
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(f"✅ {outpath}  ({len(d)} 条)")
        total += len(d)
    print(f"共 {len(by_v)} 品种 / {total} 条")

if __name__ == "__main__":
    main()
