#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 correction/SI、LI 对照表 md → 结构化注册计划 JSON（dry-run 用）。

v2 修复（2026-09-02 交接文档 P0）：
1. 标题正则支持多点号节点：`## 3.2.1 精炼产量` → node=3.2.1（旧版截成 3.2 + title ".1 ..."）
2. 概念列按表头定位：从「概念指标 / 指标」列取概念名（旧版取成行号 1/2/3）
3. 按列判缺项：SMM/Mysteel 某一列 🔴缺项 不再整行丢弃，另一列有效 ID 仍保留
   （旧版整行含"缺项"即丢 → SI 5.1/7.1、LI 7.1 等节点 0 条）

提取逻辑：
- 每个 '## X.Y... 板块名' 标题 = 一个节点段
- 表头行（含"zhiji_id"）→ 定位 概念列 / 知几·SMM列 / 知几·Mysteel列 / 频率列 / 单位列
- 数据行：概念非空 && 至少一列提取到有效 ID（FU/ID/CM/RE/[ajsn] 开头）
- 某列值为 🔴/—/空 或含 移出/缺项/幻觉 → 该列无 ID
- 输出：{code: {node: {title, rows: [{concept, ids, smm_id, mysteel_id, unit, freq}]}}}
"""
import json, re, sys, os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORR = REPO / "translation-workspace" / "correction"

ID_RE = re.compile(r"(?<![A-Za-z0-9])(?:FU\d{5,8}|ID\d{5,10}|CM\d{7,10}|RE\d{5,10}|[ajsn]\d{5,10})")
NODE_RE = re.compile(r"^#+\s*(\d+(?:\.\d+)*)\s*(.*)$")
FREQ_MAP = {"日": "daily", "周": "weekly", "月": "monthly", "季": "quarterly",
            "半年": "halfyear", "年": "yearly"}

def norm_node(match):
    """从 NODE_RE 匹配组构造规范化节点键：'3.2 .1 精炼产量' → ('3.2.1', '精炼产量')。"""
    nd, title = match.group(1), match.group(2).strip()
    # 标题若以 '.N' 开头（如 ".1 精炼产量"），合并进节点号（对应源文件 "3.2 .1" 带空格写法）
    m = re.match(r"^\.(\d+)\s*(.*)$", title)
    if m:
        nd = nd + "." + m.group(1)
        title = m.group(2).strip()
    return nd, title

def cell_valid_ids(cell):
    """从单元格提取有效 ID 列表；无效（🔴/—/空/含移出缺项幻觉）→ []"""
    if not cell:
        return []
    c = cell.strip()
    if not c or c in ("—", "-", "🔴") or c.startswith("🔴"):
        return []
    if any(k in c for k in ("移出", "缺项", "幻觉")):
        return []
    # 剥 markdown 粗体/行内代码，再取 ID
    c = re.sub(r"[*\`]", "", c)
    return list(dict.fromkeys(ID_RE.findall(c)))

def parse_freq(s):
    if not s:
        return None
    for k in ["日", "周", "月", "季", "半年", "年"]:
        if k in s:
            return FREQ_MAP[k]
    return None

def parse_file(path):
    """返回 {node: {title, rows}}。仅解析 '## X.Y' 数字节点段。"""
    nodes = {}
    cur_node = None
    cols = None  # 表头列映射
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for raw in lines:
        line = raw.rstrip("\n")
        m = NODE_RE.match(line)
        if m:
            nd, title = norm_node(m)
            # 完整节点号(如 5.3)→ 新节点；非完整标题(如 "需求指标体系（最终）" 即 5.3.final)
            # 挂在当前有效节点下，作为该节点的汇总子表
            if re.match(r"^\d+(\.\d+)+$", nd):
                cur_node = nd
            elif nd and cur_node is not None:
                cur_node = cur_node + ".final"
            cols = None
            nodes.setdefault(cur_node, {"title": title, "rows": []})
            continue
        if cur_node is None or not line.startswith("|"):
            continue
        if "|---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        ncols = len(cells)
        # 表头识别：首列 "#" 即表头（行号列）；或「概念/指标 + 频率 + 单位」三件套齐全
        is_concept_hdr = (cells[0] == "#")
        header_markers = is_concept_hdr or (any(c in ("概念指标", "指标") for c in cells)
                                            and "频率" in cells and "单位" in cells)
        # 列宽与当前表头不一致 → 重置（同节点存在两张不同列宽的表）
        cols_reset = cols is not None and ncols != cols.get("_ncols")
        if header_markers or cols_reset:
            smm = next((i for i, c in enumerate(cells) if "知几·SMM" in c), None)
            mysteel = next((i for i, c in enumerate(cells) if "知几·Mysteel" in c), None)
            # generic：既含 zhiji_id/知几 又非 smm/mysteel；无则退回 zhiji_id 或"来源"列
            generic = next((i for i, c in enumerate(cells)
                            if ("zhiji_id" in c or "知几" in c) and i not in (smm, mysteel)), None)
            if generic is None and not smm and not mysteel:
                generic = next((i for i, c in enumerate(cells) if "zhiji_id" in c), None)
                if generic is None:
                    generic = next((i for i, c in enumerate(cells) if c == "来源"), None)
            cols = {
                "concept": next((i for i, c in enumerate(cells)
                                 if c in ("概念指标", "指标")), None),
                "smm": smm,
                "mysteel": mysteel,
                "generic": generic,
                "freq": next((i for i, c in enumerate(cells) if c == "频率"), None),
                "unit": next((i for i, c in enumerate(cells) if c == "单位"), None),
                "_ncols": ncols,
            }
            continue
        if cols is None or ncols != cols.get("_ncols"):
            continue
        ci = cols["concept"]
        if ci is None or ci >= len(cells) or not cells[ci]:
            continue
        concept = cells[ci]
        if concept.startswith("#") or concept in ("指标", "概念指标") or len(concept) > 40:
            continue
        # 更名/替换概念：'A→**B**' 取箭头后新名 B（去掉 markdown 星号）
        concept_clean = re.sub(r"^.*?→", "", concept).strip()
        concept_clean = re.sub(r"[*`]", "", concept_clean).strip()
        if not concept_clean:
            continue
        # 无更名且整行含"移出"（概念本身被移出）→ 跳过；更名行是替换为新概念，保留
        if "→" not in concept and ("移出" in line or "幻觉" in line):
            continue
        smm_ids = cell_valid_ids(cells[cols["smm"]]) if cols["smm"] is not None and cols["smm"] < len(cells) else []
        ms_ids = cell_valid_ids(cells[cols["mysteel"]]) if cols["mysteel"] is not None and cols["mysteel"] < len(cells) else []
        gen_ids = cell_valid_ids(cells[cols["generic"]]) if cols["generic"] is not None and cols["generic"] < len(cells) else []
        all_ids = list(dict.fromkeys(smm_ids + ms_ids + gen_ids))
        if not all_ids:
            continue
        smm_id = smm_ids[0] if smm_ids else (gen_ids[0] if gen_ids else None)
        unit = cells[cols["unit"]] if cols["unit"] is not None and cols["unit"] < len(cells) else ""
        freq = parse_freq(cells[cols["freq"]]) if cols["freq"] is not None and cols["freq"] < len(cells) else None
        nodes[cur_node]["rows"].append({
            "concept": concept_clean,
            "ids": all_ids,
            "smm_id": smm_ids[0] if smm_ids else None,
            "mysteel_id": ms_ids[0] if ms_ids else None,
            "unit": unit,
            "freq": freq,
        })
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
                plan[nd]["rows"].extend(info["rows"])
        out[code] = plan
    outfile = REPO / "analysis" / "iwencai" / "correction_register_plan.json"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(outfile, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for code in ["SI", "LI"]:
        total = 0
        for nd in sorted(out.get(code, {}),
                        key=lambda x: [int(p) for p in x.replace(".final", "").split(".")]):
            n = len(out[code][nd]["rows"])
            total += n
            print(f"{code} {nd} {out[code][nd]['title']}: {n} 条")
        print(f"{code} 合计: {total} 条\n")
    print("输出:", outfile)

if __name__ == "__main__":
    main()
