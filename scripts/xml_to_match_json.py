#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xml_to_match_json.py — 把 Agent B 的 XML 版 Step2 结果转成标准 step2_match_{品种}.json

背景：过滤引擎 build_translation.py / step2_cache_load.py 只认 JSON（json.load）。
B 的 step2_zhiji_verify 若把结果存成 XML，本脚本负责转换。

用法：
  python3 scripts/xml_to_match_json.py --xml /path/to/step2_SN.xml --variety SN
  python3 scripts/xml_to_match_json.py --xml /path/to/step2_SN.xml --variety SN --dry   # 先看探测结果

输出：translation-workspace/mapping/{品种}/step2_match_{品种}.json（覆盖式，注意备份原文件）

字段契约（与 A 的 step2_match 完全一致）：
  条目 key 任意（建议 "subnode|name"），value 必须含:
    grade: "A"|"B"|"C"（A=命中且关键词命中, B=仅品种词, C=未命中/错配）
    hit_id / hit_name / name / subnode
转换器自动探测 XML 字段名；探测不到时打印 XML 结构让你填 FIELD_MAP。
"""
import argparse, json, os, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 字段名映射（key=XML tag 常见变体 → value=标准字段）
FIELD_MAP = {
    "name": "name", "indicator": "name", "indicator_name": "name", "指标": "name", "指标名": "name",
    "grade": "grade", "level": "grade", "命中等级": "grade",
    "hit_id": "hit_id", "id": "hit_id", "zhiji_id": "hit_id", "indicator_id": "hit_id", "ID": "hit_id",
    "hit_name": "hit_name", "matched_name": "hit_name", "matched": "hit_name", "命中指标": "hit_name", "命中名": "hit_name",
    "subnode": "subnode", "node": "subnode", "板块": "subnode", "子节点": "subnode",
}

def detect_items(root):
    """返回候选条目列表（元素）。启发式：找包含多个字段标签的元素。"""
    def walk(elem, depth=0):
        cands = []
        if depth <= 6:
            children = list(elem)
            if children and len(children) >= 1:
                # 直接子元素数 2..20 视为条目候选
                if 2 <= len(children) <= 20:
                    cands.append(elem)
                for c in children:
                    cands.extend(walk(c, depth + 1))
        return cands
    return walk(root)

def parse_item(elem):
    """从元素提取标准字段。返回 dict 或 None。"""
    out = {}
    for child in elem:
        tag = child.tag
        std = FIELD_MAP.get(tag)
        if std and std not in out:
            val = (child.text or "").strip()
            if val:
                out[std] = val
    # 属性（如 <item name=".." id=".."/>）
    for k, v in (elem.attrib or {}).items():
        std = FIELD_MAP.get(k)
        if std and std not in out and v:
            out[std] = v.strip()
    return out if ("name" in out or any(k in out for k in ("hit_id", "hit_name"))) else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True, help="B 的 XML 文件路径")
    ap.add_argument("--variety", required=True, help="品种代码 SN/SI/LI")
    ap.add_argument("--dry", action="store_true", help="只探测不写文件")
    args = ap.parse_args()

    if not os.path.exists(args.xml):
        print(f"❌ XML 不存在: {args.xml}")
        sys.exit(1)

    root = ET.parse(args.xml).getroot()
    items = []
    # 先看根是否直接就是条目集合
    direct = [e for e in list(root) if len(list(e)) >= 2]
    allc = detect_items(root)
    # 去重（按 id 属性/子标签）
    seen = set()
    unique_cands = []
    for e in (direct or allc):
        s = ET.tostring(e, encoding="unicode")
        if s in seen:
            continue
        seen.add(s)
        unique_cands.append(e)

    parsed = []
    for e in unique_cands:
        p = parse_item(e)
        if p:
            parsed.append(p)

    if not parsed:
        print("❌ 未能从 XML 识别条目。请把 XML 开头 20 行发给 A，A 会补 FIELD_MAP。")
        print("   XML 根标签:", root.tag)
        print("   顶层子标签:", [c.tag for c in list(root)][:12])
        sys.exit(1)

    # 组装标准 JSON
    out = {}
    for p in parsed:
        name = p.get("name") or p.get("hit_name") or "未知指标"
        sub = p.get("subnode", "?")
        key = f"{sub}|{name}"
        out[key] = {
            "grade": p.get("grade", "C"),
            "hit_id": p.get("hit_id", ""),
            "hit_name": p.get("hit_name", ""),
            "name": name,
            "subnode": sub,
        }

    print(f"✅ 解析 {len(parsed)} 条 (grade: "
          f"A={sum(1 for v in out.values() if v['grade']=='A')}, "
          f"B={sum(1 for v in out.values() if v['grade']=='B')}, "
          f"C={sum(1 for v in out.values() if v['grade']=='C')})")
    if args.dry:
        # 打印前 5 条供检查
        for k, v in list(out.items())[:5]:
            print("  ", k, "->", v)
        return

    outdir = os.path.join(ROOT, "translation-workspace", "mapping", args.variety)
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "step2_match_%s.json" % args.variety)
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"✅ 已写入: {outpath}")

if __name__ == "__main__":
    main()