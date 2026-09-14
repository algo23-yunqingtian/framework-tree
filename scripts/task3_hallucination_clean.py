#!/usr/bin/env python3
"""Task 3: Clean hallucination entries from divergence files.

Scans 198 divergence files across 7 varieties (CU/AL/ZN/NI/SN/SI/LI).
Classifies and counts three types of entries to be excluded from indicator extraction:
  1. Cross-commodity hallucinations - references to other metals' core commodities
  2. Chart name entries - chart names in the 图名称 column (not indicators)
  3. Derived forms - 环比/同比/分位数 etc. that are presentation forms, not independent indicators

Output: docs/Hallucination_Clean_Report.md with before/after comparison table
"""
import json, os, re
from datetime import datetime
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIVERGENCE_DIR = os.path.join(ROOT, "analysis", "iwencai")
REPORT_PATH = os.path.join(ROOT, "docs", "Hallucination_Clean_Report.md")

ALL_CODES = ["CU", "AL", "ZN", "NI", "SN", "SI", "LI"]
CN = {"CU": "铜", "AL": "铝", "ZN": "锌", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}

# ====== Cross-commodity patterns (tightened) ======
# Only flag when the OTHER commodity is mentioned as a PRIMARY subject,
# not as part of a legitimate cross-reference
CROSS_PATTERNS = {
    "CU": ["碳酸锂", "氢氧化锂", "锂精矿", "锂辉石", "电解铝", "锌锭", "锡锭", "工业硅", "多晶硅", "镍生铁", "高冰镍", "电解镍", "硫酸镍"],
    "AL": ["碳酸锂", "氢氧化锂", "锂精矿", "锂辉石", "铜精矿", "锌锭", "锡锭", "工业硅", "多晶硅", "镍生铁", "高冰镍", "电解镍", "硫酸镍"],
    "ZN": ["碳酸锂", "氢氧化锂", "锂精矿", "锂辉石", "氧化铝", "电解铝", "锡锭", "工业硅", "多晶硅", "镍生铁", "高冰镍", "电解镍", "硫酸镍"],
    "NI": ["碳酸锂", "氢氧化锂", "锂精矿", "锂辉石", "氧化铝", "电解铝", "锌锭", "锡锭", "工业硅", "多晶硅", "COMEX"],
    "SN": ["碳酸锂", "氢氧化锂", "锂精矿", "锂辉石", "氧化铝", "电解铝", "锌锭", "工业硅", "多晶硅", "镍生铁", "高冰镍", "电解镍", "硫酸镍", "COMEX"],
    "SI": ["碳酸锂", "氢氧化锂", "锂精矿", "锂辉石", "氧化铝", "电解铝", "锌锭", "锡锭", "镍生铁", "高冰镍", "电解镍", "硫酸镍", "COMEX", "GFEX"],
    "LI": ["氧化铝", "电解铝", "锌锭", "锡锭", "工业硅", "多晶硅", "镍生铁", "高冰镍", "电解镍", "硫酸镍", "COMEX", "GFEX"],
}

# ====== Cross-exchange rules (U4) ======
# Blacklist approach: each variety lists exchanges that are CROSS-COMMODITY (should be flagged)
# NI/SN/SI/LI should not reference COMEX (it's a US exchange, not relevant to Chinese metals)
# PB should not reference COMEX/GFEX
CROSS_EXCHANGES = {
    "PB": ["COMEX", "GFEX"],
    "LI": ["COMEX", "SHFE", "上期所"],
    "NI": ["COMEX", "GFEX"],
    "SN": ["COMEX", "GFEX"],
    "SI": ["COMEX", "SHFE", "上期所"],
}

# ====== Derived form patterns (tightened) ======
# Only flag when the indicator IS primarily a derived form
DERIVED_EXACT = [
    "环比", "同比", "增速", "增长率", "变化率", "变化方向",
    "去化速度", "累库幅度", "分位数", "分位",
    "日增减", "月增减", "周增减", "周环比", "月环比",
    "月度高点", "月度低点", "波动率", "振幅",
    "变化", "增减",
]

def is_derived_form(text):
    """Check if text is purely a derived form (not an independent indicator)."""
    t = re.sub(r"[（(][^）)]*[）)]", "", text).strip()
    if not t or len(t) < 3:
        return False
    # Check if the text matches a derived form pattern closely
    for kw in DERIVED_EXACT:
        if t == kw or t == kw + "率" or t == kw + "值":
            return True
        # Check if it's like "库存环比" or "价格同比" (base + derived)
        if t.endswith(kw) and len(t) <= len(kw) + 4:
            return True
        if t.startswith(kw) and len(t) <= len(kw) + 4:
            return True
    return False

def split_indicators(cell_text):
    """Split indicator cell text into individual indicators."""
    text = cell_text.strip()
    if not text:
        return []
    parts = re.split(r"[；;，,、/]+", text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 2]

def classify_indicator(indicator, code):
    """Classify an indicator as 'ok', 'cross_commodity', or 'derived'."""
    t = indicator.strip()
    if not t or len(t) <= 2:
        return "ok"

    # Check cross-commodity (commodity names)
    for other_var in CROSS_PATTERNS.get(code, []):
        if other_var in t:
            return "cross_commodity"

    # U3/U4: Check cross-exchange references
    # E.g., LI/NI/SN referencing COMEX, PB referencing GFEX
    for other_ex in CROSS_EXCHANGES.get(code, []):
        if other_ex in t:
            return "cross_commodity"

    # Check derived form
    if is_derived_form(t):
        return "derived"

    return "ok"

def is_chart_name(text):
    """Check if text is a chart name (for 图名称 column entries)."""
    t = re.sub(r"[（(][^）)]*[）)]", "", text).strip()
    if not t or len(t) < 4:
        return False
    # Chart names typically end with 图 or contain em-dash
    if t.endswith("图") and len(t) >= 5:
        return True
    if re.search(r"[—\-–].+[—\-–]", t) and "图" in t:
        return True
    return False

def parse_tables(filepath):
    """Parse all tables from a divergence file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    rows = []
    in_table = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect markdown table header
        if stripped.startswith("|") and "---" not in stripped and "序号" in stripped:
            in_table = True
            continue

        # Skip separator
        if in_table and "---" in stripped:
            continue

        # Parse markdown table row
        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 3:
                chart_name = cells[1] if len(cells) > 1 else ""
                indicator_cell = cells[2] if len(cells) > 2 else ""
                rows.append({
                    "line": i + 1,
                    "chart_name": chart_name,
                    "indicator_cell": indicator_cell,
                })
            continue

        # Detect tab-separated rows
        if "\t" in stripped and re.match(r"^\d+\t", stripped):
            parts = stripped.split("\t")
            if len(parts) >= 3:
                chart_name = parts[1] if len(parts) > 1 else ""
                indicator_cell = parts[2] if len(parts) > 2 else ""
                rows.append({
                    "line": i + 1,
                    "chart_name": chart_name,
                    "indicator_cell": indicator_cell,
                })
            continue

        if in_table and not stripped.startswith("|") and "\t" not in stripped:
            in_table = False

    return rows

def main():
    print("=" * 60)
    print("Task 3: Hallucination Cleaning from Divergence Files")
    print("=" * 60)

    all_files = []
    for code in ALL_CODES:
        code_dir = os.path.join(DIVERGENCE_DIR, code)
        if os.path.isdir(code_dir):
            for fname in sorted(os.listdir(code_dir)):
                if fname.startswith("divergence_") and fname.endswith(".md"):
                    all_files.append((code, os.path.join(code_dir, fname)))

    print("Found %d divergence files" % len(all_files))

    results = []
    all_entries = []  # (code, fname, entry_text, class, source_col)

    for code, filepath in all_files:
        fname = os.path.basename(filepath)
        rows = parse_tables(filepath)

        # Count chart names from 图名称 column
        chart_name_count = 0
        for row in rows:
            cn = row["chart_name"]
            if cn and is_chart_name(cn):
                chart_name_count += 1
                all_entries.append((code, fname, "[图名] " + cn[:60], "chart_name", "图名称列"))

        # Count indicators from 包含指标 column
        indicator_count = 0
        cross_count = 0
        derived_count = 0

        for row in rows:
            indicators = split_indicators(row["indicator_cell"])
            for ind in indicators:
                indicator_count += 1
                cls = classify_indicator(ind, code)
                all_entries.append((code, fname, ind[:60], cls, "指标列"))
                if cls == "cross_commodity":
                    cross_count += 1
                elif cls == "derived":
                    derived_count += 1

        total_before = chart_name_count + indicator_count
        total_removed = chart_name_count + cross_count + derived_count
        total_after = total_before - total_removed

        results.append({
            "code": code,
            "file": fname,
            "before": total_before,
            "after": total_after,
            "removed": total_removed,
            "cross": cross_count,
            "chart": chart_name_count,
            "derived": derived_count,
        })

    # Aggregate
    total_before = sum(r["before"] for r in results)
    total_after = sum(r["after"] for r in results)
    total_cross = sum(r["cross"] for r in results)
    total_chart = sum(r["chart"] for r in results)
    total_derived = sum(r["derived"] for r in results)
    total_removed = total_cross + total_chart + total_derived

    per_code = defaultdict(lambda: {"files": 0, "before": 0, "removed": 0, "after": 0, "cross": 0, "chart": 0, "derived": 0})
    for r in results:
        pc = per_code[r["code"]]
        pc["files"] += 1
        pc["before"] += r["before"]
        pc["removed"] += r["removed"]
        pc["after"] += r["after"]
        pc["cross"] += r["cross"]
        pc["chart"] += r["chart"]
        pc["derived"] += r["derived"]

    # Collect examples
    cross_examples = [(c, f, ind) for c, f, ind, cls, _ in all_entries if cls == "cross_commodity"]
    chart_examples = [(c, f, ind) for c, f, ind, cls, _ in all_entries if cls == "chart_name"]
    derived_examples = [(c, f, ind) for c, f, ind, cls, _ in all_entries if cls == "derived"]

    # Report
    lines = [
        "# 幻觉清洗对照表",
        "",
        "**执行时间**: %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "**范围**: 7品种 (CU/AL/ZN/NI/SN/SI/LI) 共 %d 个 divergence 文件" % len(all_files),
        "",
        "## 一、清洗统计总表",
        "",
        "| 品种 | 文件数 | 清洗前条目 | 剔除数 | 清洗后条目 | 剔除率 | 跨品种幻觉 | 图表名条目 | 派生形态 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for code in ALL_CODES:
        if code in per_code:
            pc = per_code[code]
            rate = 100.0 * pc["removed"] / max(1, pc["before"])
            lines.append("| %s(%s) | %d | %d | %d | %d | %.0f%% | %d | %d | %d |" % (
                code, CN[code], pc["files"], pc["before"], pc["removed"], pc["after"],
                rate, pc["cross"], pc["chart"], pc["derived"]))

    rate_all = 100.0 * total_removed / max(1, total_before)
    lines.append("| **合计** | **%d** | **%d** | **%d** | **%d** | **%.0f%%** | **%d** | **%d** | **%d** |" % (
        len(all_files), total_before, total_removed, total_after,
        rate_all, total_cross, total_chart, total_derived))

    # Examples
    lines += ["", "## 二、跨品种幻觉示例 (共 %d 条)" % total_cross, "",
              "| # | 品种 | 文件 | 条目 |", "|---|---|---|---|"]
    for i, (c, f, ind) in enumerate(cross_examples[:20], 1):
        lines.append("| %d | %s | %s | %s |" % (i, c, f, ind))
    if total_cross > 20:
        lines.append("| ... | (共 %d 条) | | |" % total_cross)

    lines += ["", "## 三、图表名条目示例 (共 %d 条)" % total_chart, "",
              "| # | 品种 | 文件 | 条目 |", "|---|---|---|---|"]
    for i, (c, f, ind) in enumerate(chart_examples[:20], 1):
        lines.append("| %d | %s | %s | %s |" % (i, c, f, ind))
    if total_chart > 20:
        lines.append("| ... | (共 %d 条) | | |" % total_chart)

    lines += ["", "## 四、派生形态示例 (共 %d 条)" % total_derived, "",
              "| # | 品种 | 文件 | 条目 |", "|---|---|---|---|"]
    for i, (c, f, ind) in enumerate(derived_examples[:20], 1):
        lines.append("| %d | %s | %s | %s |" % (i, c, f, ind))
    if total_derived > 20:
        lines.append("| ... | (共 %d 条) | | |" % total_derived)

    lines += ["", "## 五、逐文件明细 (仅显示有剔除的文件)", "",
              "| 品种 | 文件 | 清洗前 | 剔除 | 清洗后 | 跨品种 | 图表名 | 派生 |",
              "|---|---|---|---|---|---|---|---|"]
    for r in results:
        if r["removed"] > 0:
            lines.append("| %s | %s | %d | %d | %d | %d | %d | %d |" % (
                r["code"], r["file"], r["before"], r["removed"], r["after"],
                r["cross"], r["chart"], r["derived"]))

    lines += [
        "",
        "## 六、分类说明",
        "",
        "| 类别 | 定义 | 处理方式 |",
        "|---|---|---|",
        "| 跨品种幻觉 | 在某品种文件中出现其他品种核心商品名(如CU文件出现碳酸锂) | 标记剔除, 归入备用库 |",
        "| 图表名条目 | 图名称列中的图表标题(非数据指标) | 分离至图表配置区, 不计入指标 |",
        "| 派生形态 | 环比/同比/分位数/去化速度等派生指标 | 归入原始指标的呈现方式, 不单列 |",
        "",
        "## 七、排除项汇总",
        "",
        "- 清洗前总条目: **%d**" % total_before,
        "- 清洗后保留: **%d**" % total_after,
        "- 总剔除: **%d** (%.1f%%)" % (total_removed, rate_all),
        "  - 跨品种幻觉: %d 条" % total_cross,
        "  - 图表名条目: %d 条" % total_chart,
        "  - 派生形态: %d 条" % total_derived,
        "",
        "> 注: 清洗后文件保留原始内容, 本表提供对照分析。下游管线读取 divergence 时,",
        "> 应跳过图表名条目和派生形态, 仅提取独立基础指标。",
    ]

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n=== Hallucination Clean Summary ===")
    print("Files processed: %d" % len(all_files))
    print("Total entries before: %d" % total_before)
    print("Total removed: %d (%.1f%%)" % (total_removed, rate_all))
    print("  Cross-commodity: %d" % total_cross)
    print("  Chart names: %d" % total_chart)
    print("  Derived forms: %d" % total_derived)
    print("Total after: %d" % total_after)
    print("Report: %s" % REPORT_PATH)
    print("Done!")

if __name__ == "__main__":
    main()
