#!/usr/bin/env python3
"""
DSH-B_CHART_META_JOIN_MATCH_BOARD_TASK
T2: JOIN chart metadata with v85 final board, classify missing items.

Inputs:
  - pdf_chart_meta_all.json        (543 charts, 148 missing_in_legend items)
  - fp32_v85_final_board.csv       (64 board rows)
  - indicators_v1.json             (full indicator library)
  - pdf_extract_all_candidates.csv (518 DSH-extracted indicator names)

Outputs:
  1. fp32_v85_board_with_chart_meta.csv  (board + chart metadata)
  2. missing_classify.csv                (148 missing items classified)
  3. chart_missing_summary.md            (summary report)

Constraints:
  - Read-only: no modification to indicators_v1, GT, matching rules
  - No zhiji API calls
  - All new files, no modification to historical files
"""
import csv, json, os, re, sys
from pathlib import Path
from collections import defaultdict

# ── Paths ──
REPO = Path(r"D:\DSH_WORK\framework-tree")
OUT_DIR = REPO / "analysis" / "e2e_output" / "v85" / "pdf_extract"
BOARD_CSV = REPO / "analysis" / "e2e_output" / "v85" / "fp32_v85_final_board.csv"
CHART_JSON = OUT_DIR / "pdf_chart_meta_all.json"
DSH_CSV = OUT_DIR / "pdf_extract_all_candidates.csv"
INDICATORS_V1 = REPO / "data" / "indicators_v1.json"
LOG_FILE = r"D:\DSH_WORK\join_match_log.txt"

OUT_BOARD = OUT_DIR / "fp32_v85_board_with_chart_meta.csv"
OUT_MISSING = OUT_DIR / "missing_classify.csv"
OUT_MD = OUT_DIR / "chart_missing_summary.md"

# ── Variety → Source File Mapping ──
VARIETY_TO_SOURCE = {
    "氧化铝": "氧化铝周报20260830.pdf",
    "铝": "铝周报20260830.pdf",
    "碳酸锂": "碳酸锂周报20260823.pdf",
    "镍": "镍与不锈钢周报20260906.pdf",
    "硅": "硅产业链周报20260906.pdf",
    "锡": "锡周报20260905.pdf",
}

# ── Normalization helpers ──
def norm(s):
    """Normalize Chinese text for comparison: full-width → half-width, unify punctuation."""
    if not s:
        return ""
    s = s.strip()
    # Full-width → half-width for common chars
    trans = str.maketrans("：，（）【】－—～", ":,()[]--~")
    s = s.translate(trans)
    # Normalize whitespace
    s = re.sub(r'\s+', '', s)
    # Normalize dashes/hyphens
    s = s.replace("－", "-").replace("—", "-").replace("–", "-")
    # Remove leading/trailing punctuation
    s = s.strip("-_:,·.、 ")
    return s

def fuzzy_contain(a, b):
    """Check if a is a fuzzy substring of b or vice versa (lenient, for board JOIN)."""
    if not a or not b:
        return False
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    # Exact
    if na == nb:
        return True
    # Substring (either direction)
    if na in nb or nb in na:
        return True
    # Check significant token overlap (for names with multiple parts)
    na_parts = re.split(r'[-:（）()·,，、/]', na)
    nb_parts = re.split(r'[-:（）()·,，、/]', nb)
    # If any meaningful part (len >= 2) matches
    for p in na_parts:
        if len(p) >= 2 and p in nb:
            return True
    for p in nb_parts:
        if len(p) >= 2 and p in na:
            return True
    return False

def strict_fuzzy_contain(a, b):
    """Check if a is a fuzzy substring of b or vice versa (strict, for classification)."""
    if not a or not b:
        return False
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    # Exact
    if na == nb:
        return True
    # Substring (either direction) - but only if the shorter string is >= 4 chars
    shorter = na if len(na) < len(nb) else nb
    longer = nb if len(na) < len(nb) else na
    if len(shorter) >= 4 and shorter in longer:
        return True
    # Check significant token overlap (for names with multiple parts)
    na_parts = re.split(r'[-:（）()·,，、/]', na)
    nb_parts = re.split(r'[-:（）()·,，、/]', nb)
    # Count meaningful parts (len >= 4) that match
    na_meaningful = [p for p in na_parts if len(p) >= 4]
    nb_meaningful = [p for p in nb_parts if len(p) >= 4]
    match_count = 0
    for p in na_meaningful:
        if p in nb:
            match_count += 1
    for p in nb_meaningful:
        if p in na:
            match_count += 1
    # Require at least 2 significant token matches, and at least 60% of parts
    total_parts = max(len(na_meaningful), len(nb_meaningful), 1)
    if match_count >= 2 and match_count / total_parts >= 0.6:
        return True
    return False

def is_indicator_like(text):
    """Check if text looks like a real indicator name (not noise)."""
    t = text.strip()
    if not t or len(t) > 50:
        return False
    # Reject pure numbers, units, dates
    if re.match(r'^[\d.,:（）()/\-]+$', t):
        return False
    if t in {"元", "元/吨", "吨", "万吨", "千吨", "%", "万元", "亿美元",
             "万美元", "美元/吨", "美元", "元/千克", "元/kg", "元/克",
             "元/公斤", "万张", "张", "pp", "bp", "bps", "万吨/日",
             "万吨/周", "万吨/月", "万吨/年", "元/吨·日", "元/吨·天",
             "元/吨·月", "元/吨·年", "元/吨·周", "美元/吨·日", "美元/吨·天",
             "美元/吨·月", "美元/吨·年", "美元/吨·周", "美元/吨·年",
             "亿美元/吨", "亿元", "亿元/吨", "元/吨·月", "元/吨·周",
             "元/吨·年", "元/吨·天", "元/吨·日", "元/吨·月", "元/吨·周",
             "元/吨·年", "元/吨·天", "元/吨·日", "元/吨·月", "元/吨·周",
             "元/吨·年", "元/吨·天", "元/吨·日", "元/吨·月", "元/吨·周",
             "元/吨·年", "元/吨·天", "元/吨·日"}:
        return False
    # Reject date patterns
    date_pats = [r'^\d{1,2}月$', r'^\d{4}年$', r'^\d{4}-\d{2}(-\d{2})?$',
                 r'^\d{4}/\d{2}(/\d{2})?$', r'^\d{4}\.\d{2}(\.\d{2})?$',
                 r'^[Qq][1-4]$', r'^H[12]$', r'^\d{4}$', r'^\d{2}/\d{2}$',
                 r'^\d{4}-\d{2}$']
    if any(re.match(p, t) for p in date_pats):
        return False
    # Reject common axis labels
    if t in {"日", "月", "年", "周", "日度", "月度", "年度", "周度", "季度",
             "累计", "同比", "环比", "平均", "合计", "总量", "总消费", "总量",
             "当月", "上月", "本年", "本年累计"}:
        return False
    # Reject fragments (too short, or mostly punctuation)
    if len(t) < 2:
        return False
    punct_ratio = sum(1 for c in t if c in '：:，,、/—-()（）[]【】·.。 ') / len(t)
    if punct_ratio > 0.5:
        return False
    # Reject repeated characters
    if len(set(t)) < len(t) * 0.3:
        return False
    # Reject text that looks like a paragraph (too many chars, multiple punctuation)
    if len(t) > 30 and sum(1 for c in t if c in '：:，,、（）()') >= 3:
        return False
    # Reject text with Chinese punctuation that indicates paragraph context
    if re.search(r'，|。|；', t):
        return False
    # Reject text that is a number with unit (e.g., "1.21亿吨", "9841吨", "1884吨")
    if re.match(r'^[\d.]+\s*(亿吨|万吨|千万吨|百万吨|万吨|千吨|吨|美元|元|万元|亿元|亿美元|万吨/年|万吨/月|万吨/日|万吨/周|美元/吨|元/吨|元/千克|元/kg|元/克|元/公斤|万张|张|pp|bp|bps|GWh|MWh|MW|GW|kW|kVA|MVA|MW|GW|%)$', t):
        return False
    # Reject text with a period/Chinese period in the middle (paragraph fragment)
    if '。' in t and not t.endswith('。'):
        return False
    # Reject percentage signs that look like data values (e.g. "17.2%", "25%")
    if re.match(r'^[\d.]+%$', t):
        return False
    # Reject text that ends with colon (chart subtitle fragment)
    if t.endswith(':') or t.endswith('：'):
        return False
    # Reject pure unit labels (e.g., "GWh", "MWh", "GW", "MW")
    if t.upper() in {"GWH", "MWH", "GW", "MW", "KW", "KVA", "MVA", "KWH", "MW·H", "GWH·D"}:
        return False
    # Reject "汇总" fragments
    if t.startswith("汇总") or t == "汇总1":
        return False
    # Reject Chinese text that is just a short fragment (<= 2 chars) mixed with punctuation
    if len(t) <= 3 and sum(1 for c in t if c in '：:（）()[]【】·、,.。；') >= 1:
        return False
    return True


# ── Load data ──
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_csv(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load_board():
    return load_csv(BOARD_CSV)

def load_charts():
    data = load_json(CHART_JSON)
    return data["charts"]

def load_indicators_v1():
    """Load indicators_v1 and build lookup set of all indicator names."""
    data = load_json(INDICATORS_V1)
    names = set()
    for key, val in data.items():
        # key is like "主连", "LME库存", "社库"
        names.add(key)
        names.add(key.strip())
        if isinstance(val, dict):
            name = val.get("name", "")
            if name:
                names.add(name)
                names.add(name.strip())
    return names

def load_dsh_candidates():
    """Load DSH-extracted indicator names from PDF extraction."""
    rows = load_csv(DSH_CSV)
    names = set()
    for r in rows:
        n = r.get("extracted_indicator_name", "").strip()
        if n:
            names.add(n)
    return names


# ── Build chart index for fast lookup ──
def build_chart_index(charts):
    """Build index: (source_file, extracted_indicator_name) → chart.
    Also index by chart_title for fallback matching."""
    by_source_indicator = defaultdict(list)
    by_source_title = defaultdict(list)
    for ch in charts:
        sf = ch["source_file"]
        # Index by each extracted indicator name
        for ind in ch.get("extracted_indicator_list", []):
            by_source_indicator[(sf, ind)].append(ch)
        # Also index by chart_title
        title = ch.get("chart_title", "")
        if title:
            by_source_title[(sf, title)].append(ch)
    return by_source_indicator, by_source_title


# ── Match board row to chart ──
def match_board_to_chart(row, charts, by_source_indicator, by_source_title):
    """Match a board row to chart(s). Returns best matching chart or None."""
    variety = row.get("variety", "")
    source_file = VARIETY_TO_SOURCE.get(variety, "")
    if not source_file:
        return None
    
    chart_name = row.get("chart_name", "").strip()
    if not chart_name:
        return None
    
    best_chart = None
    best_score = 0
    
    # 1) Exact match against extracted_indicator_list
    if (source_file, chart_name) in by_source_indicator:
        return by_source_indicator[(source_file, chart_name)][0]
    
    # 2) Try matching against chart_titles
    if (source_file, chart_name) in by_source_title:
        return by_source_title[(source_file, chart_name)][0]
    
    # 3) Fuzzy match against extracted_indicator_list
    for (sf, ind), ch_list in by_source_indicator.items():
        if sf != source_file:
            continue
        if fuzzy_contain(chart_name, ind):
            score = 2
            if best_score < score:
                best_score = score
                best_chart = ch_list[0]
    
    # 4) Fuzzy match against chart_titles
    for (sf, title), ch_list in by_source_title.items():
        if sf != source_file:
            continue
        if fuzzy_contain(chart_name, title):
            score = 1
            if best_score < score:
                best_score = score
                best_chart = ch_list[0]
    
    return best_chart


# ── Match missing item against indicators_v1 ──
def match_missing_against_library(missing_text, indicator_names, dsh_names):
    """Try to match a missing legend item against indicators_v1 and DSH names.
    
    Returns:
        (branch, matched_name, match_source)
        branch: "A" = PDF parsing issue (indicator exists in library),
                "B" = library gap (no indicator exists)
    """
    nt = norm(missing_text)
    if not nt or len(nt) < 2:
        return "B", "", ""
    
    # Quick reject: clearly not an indicator name
    if not is_indicator_like(missing_text):
        return "B", "", ""
    
    # 1) Exact match against indicators_v1 names
    for ind_name in indicator_names:
        ni = norm(ind_name)
        if not ni:
            continue
        if nt == ni:
            return "A", ind_name, "indicators_v1_exact"
    
    # 2) Exact match against DSH candidates
    for dsh_name in dsh_names:
        nd = norm(dsh_name)
        if not nd:
            continue
        if nt == nd:
            return "A", dsh_name, "dsh_candidates_exact"
    
    # 3) Fuzzy match against indicators_v1
    for ind_name in indicator_names:
        ni = norm(ind_name)
        if not ni or len(ni) < 2:
            continue
        if strict_fuzzy_contain(nt, ni):
            return "A", ind_name, "indicators_v1_fuzzy"
    
    # 4) Fuzzy match against DSH candidates
    for dsh_name in dsh_names:
        nd = norm(dsh_name)
        if not nd or len(nd) < 2:
            continue
        if strict_fuzzy_contain(nt, nd):
            return "A", dsh_name, "dsh_candidates_fuzzy"
    
    return "B", "", ""


# ── Main ──
def main():
    log = open(LOG_FILE, "w", encoding="utf-8")
    def p(*a, **kw):
        print(*a, **kw)
        print(*a, **kw, file=log)
    
    p("=" * 60)
    p("DSH-B_CHART_META_JOIN_MATCH_BOARD_TASK")
    p("=" * 60)
    
    # ── Load data ──
    p("\n[1] Loading data...")
    board_rows = load_board()
    charts = load_charts()
    indicator_names = load_indicators_v1()
    dsh_names = load_dsh_candidates()
    
    p(f"  Board rows: {len(board_rows)}")
    p(f"  Charts: {len(charts)}")
    p(f"  Indicators_v1 names: {len(indicator_names)}")
    p(f"  DSH candidates: {len(dsh_names)}")
    
    # Build chart index
    by_source_indicator, by_source_title = build_chart_index(charts)
    p(f"  Chart index: {len(by_source_indicator)} indicator entries, {len(by_source_title)} title entries")
    
    # ── JOIN: Add chart metadata to board rows ──
    p("\n[2] JOIN: Adding chart metadata to board...")
    
    board_with_meta = []
    matched_count = 0
    unmatched_board = []
    
    for i, row in enumerate(board_rows):
        chart = match_board_to_chart(row, charts, by_source_indicator, by_source_title)
        
        if chart:
            matched_count += 1
            row_out = dict(row)
            row_out["chart_local_id"] = chart.get("chart_local_id", "")
            row_out["chart_page_num"] = chart.get("page_num", "")
            row_out["chart_title"] = chart.get("chart_title", "")
            row_out["source_chart_plot_style"] = chart.get("plot_style", "")
            row_out["chart_axis_info"] = chart.get("axis_info", "")
            row_out["full_chart_legend"] = " | ".join(chart.get("legend_list", []))
            row_out["chart_missing_in_legend"] = " | ".join(chart.get("missing_in_legend", []))
            row_out["chart_legend_count"] = len(chart.get("legend_list", []))
            row_out["chart_missing_count"] = len(chart.get("missing_in_legend", []))
        else:
            row_out = dict(row)
            row_out["chart_local_id"] = ""
            row_out["chart_page_num"] = ""
            row_out["chart_title"] = ""
            row_out["source_chart_plot_style"] = ""
            row_out["chart_axis_info"] = ""
            row_out["full_chart_legend"] = ""
            row_out["chart_missing_in_legend"] = ""
            row_out["chart_legend_count"] = ""
            row_out["chart_missing_count"] = ""
            unmatched_board.append(row.get("chart_name", ""))
        
        board_with_meta.append(row_out)
    
    p(f"  Board rows matched to charts: {matched_count}/{len(board_rows)}")
    if unmatched_board:
        p(f"  Unmatched board chart_names ({len(unmatched_board)}):")
        for n in unmatched_board:
            p(f"    - {n}")
    
    # ── Collect all missing_in_legend items ──
    p("\n[3] Collecting missing_in_legend items...")
    
    all_missing = []
    for chart in charts:
        for miss in chart.get("missing_in_legend", []):
            all_missing.append({
                "source_file": chart["source_file"],
                "page_num": chart["page_num"],
                "chart_local_id": chart["chart_local_id"],
                "chart_title": chart["chart_title"],
                "plot_style": chart["plot_style"],
                "missing_text": miss,
                "legend_list": chart.get("legend_list", []),
                "extracted_indicator_list": chart.get("extracted_indicator_list", []),
                "axis_info": chart.get("axis_info", ""),
                "note": chart.get("note", ""),
            })
    
    p(f"  Total missing items: {len(all_missing)}")
    
    # ── Classify missing items ──
    p("\n[4] Classifying missing items...")
    
    classify_rows = []
    branch_a_count = 0
    branch_b_count = 0
    
    for item in all_missing:
        branch, matched_name, match_source = match_missing_against_library(
            item["missing_text"], indicator_names, dsh_names
        )
        if branch == "A":
            branch_a_count += 1
        else:
            branch_b_count += 1
        
        # Determine sub-type for Branch A
        if branch == "A":
            if "exact" in match_source:
                root_cause = "A1_精确匹配到库(解析遗漏)"
            else:
                root_cause = "A2_模糊匹配到库(命名差异)"
        else:
            # Branch B sub-types
            if not is_indicator_like(item["missing_text"]):
                root_cause = "B1_噪声文本(非指标名)"
            else:
                root_cause = "B2_指标名无库元数据(库缺失)"
        
        row_out = {
            "source_file": item["source_file"],
            "page_num": item["page_num"],
            "chart_local_id": item["chart_local_id"],
            "chart_title": item["chart_title"],
            "plot_style": item["plot_style"],
            "axis_info": item["axis_info"],
            "missing_text": item["missing_text"],
            "branch": branch,
            "branch_label": "A:PDF解析漏提取" if branch == "A" else "B:指标库缺失",
            "root_cause": root_cause,
            "matched_indicator": matched_name,
            "match_source": match_source,
            "legend_list": " | ".join(item["legend_list"]),
            "extracted_list": " | ".join(item["extracted_indicator_list"]),
            "note": item["note"],
        }
        classify_rows.append(row_out)
    
    p(f"  Branch A (PDF parsing issue): {branch_a_count}")
    p(f"  Branch B (library gap): {branch_b_count}")
    
    # ── Write outputs ──
    p("\n[5] Writing outputs...")
    
    # 1. Board with chart metadata
    board_fields = list(board_rows[0].keys()) if board_rows else []
    meta_fields = ["chart_local_id", "chart_page_num", "chart_title",
                   "source_chart_plot_style", "chart_axis_info",
                   "full_chart_legend", "chart_missing_in_legend",
                   "chart_legend_count", "chart_missing_count"]
    all_board_fields = board_fields + meta_fields
    
    with open(OUT_BOARD, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=all_board_fields)
        w.writeheader()
        for row in board_with_meta:
            w.writerow({k: row.get(k, "") for k in all_board_fields})
    p(f"  Written: {OUT_BOARD} ({len(board_with_meta)} rows)")
    
    # 2. Missing classification
    miss_fields = ["source_file", "page_num", "chart_local_id", "chart_title",
                   "plot_style", "axis_info", "missing_text", "branch",
                   "branch_label", "root_cause", "matched_indicator",
                   "match_source", "legend_list", "extracted_list", "note"]
    
    with open(OUT_MISSING, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=miss_fields)
        w.writeheader()
        for row in classify_rows:
            w.writerow({k: row.get(k, "") for k in miss_fields})
    p(f"  Written: {OUT_MISSING} ({len(classify_rows)} rows)")
    
    # 3. Summary Markdown
    write_summary_md(all_missing, classify_rows, board_with_meta, matched_count)
    p(f"  Written: {OUT_MD}")
    
    # ── Summary stats ──
    p("\n[6] Summary statistics")
    p(f"  Board rows total: {len(board_rows)}")
    p(f"  Board rows matched: {matched_count} ({matched_count/len(board_rows)*100:.1f}%)")
    p(f"  Total missing items: {len(all_missing)}")
    p(f"  Branch A (PDF parsing issue): {branch_a_count} ({branch_a_count/len(all_missing)*100:.1f}%)")
    p(f"  Branch B (library gap): {branch_b_count} ({branch_b_count/len(all_missing)*100:.1f}%)")
    
    # Breakdown by source
    from collections import Counter
    source_counter = Counter(c["source_file"] for c in classify_rows)
    p(f"\n  Missing items by source PDF:")
    for src, cnt in sorted(source_counter.items()):
        p(f"    {src}: {cnt}")
    
    # Breakdown by chart title (top 10)
    title_counter = Counter(c["chart_title"] for c in classify_rows)
    p(f"\n  Top charts with missing items:")
    for title, cnt in title_counter.most_common(10):
        p(f"    {title}: {cnt}")
    
    p("\nDone!")
    log.close()


def write_summary_md(all_missing, classify_rows, board_with_meta, matched_count):
    """Generate the markdown summary report."""
    from collections import Counter, defaultdict
    
    total = len(all_missing)
    branch_a = sum(1 for c in classify_rows if c["branch"] == "A")
    branch_b = sum(1 for c in classify_rows if c["branch"] == "B")
    
    # Sub-classification
    root_cause_counter = Counter(c["root_cause"] for c in classify_rows)
    
    # By source PDF
    source_counter = Counter(c["source_file"] for c in classify_rows)
    
    # By chart title
    title_counter = Counter(c["chart_title"] for c in classify_rows)
    
    # By plot_style
    style_counter = Counter(c["plot_style"] for c in classify_rows)
    
    # Multi-legend charts
    multi_legend_charts = [c for c in all_missing if len(c.get("legend_list", [])) > 2]
    
    # Contract series (合约序列)
    contract_patterns = re.compile(r'(连[一二三四五]|Cash|连续合约|0-3M|3M|远月|月差|价差|合约)')
    contract_items = [c for c in all_missing if contract_patterns.search(c["missing_text"])]
    
    # Downstream consumption (下游消费)
    downstream_patterns = re.compile(r'(消费|交通|建筑|家电|电力|终端|下游|需求)')
    downstream_items = [c for c in all_missing if downstream_patterns.search(c["missing_text"])]
    
    # Board join stats
    board_total = len(board_with_meta)
    
    lines = []
    lines.append("# 图表元数据漏提取汇总报告")
    lines.append("")
    lines.append("## 1. 总体概览")
    lines.append("")
    lines.append("| 维度 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 复核看板总行数 | {board_total} |")
    lines.append(f"| 看板行匹配到图表 | {matched_count} ({matched_count/board_total*100:.1f}%) |")
    lines.append(f"| 漏提取图例总数 | {total} |")
    lines.append(f"| Branch A (PDF解析问题) | {branch_a} ({branch_a/total*100:.1f}%) |")
    lines.append(f"| Branch B (指标库缺失) | {branch_b} ({branch_b/total*100:.1f}%) |")
    lines.append("")
    
    lines.append("## 2. 根因细分")
    lines.append("")
    lines.append("| 根因分类 | 数量 | 占比 | 说明 |")
    lines.append("|----------|------|------|------|")
    for cause, cnt in sorted(root_cause_counter.items()):
        pct = cnt / total * 100
        desc = ""
        if "A1" in cause:
            desc = "精确匹配到指标库，PDF解析层漏提取"
        elif "A2" in cause:
            desc = "模糊匹配到指标库，命名差异导致未提取"
        elif "B1" in cause:
            desc = "噪声文本（单位/日期/碎片），非指标名"
        elif "B2" in cause:
            desc = "指标名但指标库无对应元数据"
        lines.append(f"| {cause} | {cnt} | {pct:.1f}% | {desc} |")
    lines.append("")
    
    lines.append("## 3. 按来源PDF分布")
    lines.append("")
    lines.append("| 来源PDF | 漏提取数 | 占比 |")
    lines.append("|---------|---------|------|")
    for src, cnt in sorted(source_counter.items(), key=lambda x: -x[1]):
        lines.append(f"| {src} | {cnt} | {cnt/total*100:.1f}% |")
    lines.append("")
    
    lines.append("## 4. 按绘图类型分布")
    lines.append("")
    lines.append("| 绘图类型 | 漏提取数 |")
    lines.append("|----------|---------|")
    for style, cnt in sorted(style_counter.items(), key=lambda x: -x[1]):
        lines.append(f"| {style} | {cnt} |")
    lines.append("")
    
    lines.append("## 5. 重点高亮：Top漏检图表")
    lines.append("")
    lines.append("| 图表标题 | 来源 | 漏提取数 | 漏提取内容 |")
    lines.append("|----------|------|---------|-----------|")
    for title, cnt in title_counter.most_common(15):
        items = [c["missing_text"] for c in classify_rows if c["chart_title"] == title]
        src = ""
        for c in classify_rows:
            if c["chart_title"] == title:
                src = c["source_file"]
                break
        lines.append(f"| {title} | {src} | {cnt} | {' | '.join(items)} |")
    lines.append("")
    
    lines.append("## 6. 重点高亮：多图例图表")
    lines.append("")
    lines.append(f"共 {len(multi_legend_charts)} 个漏提取项来自多图例图表(>2图例)。")
    lines.append("")
    lines.append("| 图表 | 来源 | 图例数 | 漏提取项 |")
    lines.append("|------|------|--------|---------|")
    seen = set()
    for c in multi_legend_charts:
        key = (c["source_file"], c["chart_local_id"])
        if key in seen:
            continue
        seen.add(key)
        legend_count = len(c.get("legend_list", []))
        miss_texts = [m["missing_text"] for m in all_missing 
                      if m["chart_local_id"] == c["chart_local_id"] and m["source_file"] == c["source_file"]]
        lines.append(f"| {c['chart_title']} | {c['source_file']} | {legend_count} | {' | '.join(miss_texts)} |")
    lines.append("")
    
    lines.append("## 7. 重点高亮：合约序列漏检")
    lines.append("")
    if contract_items:
        lines.append(f"共 {len(contract_items)} 项合约序列相关漏检：")
        lines.append("")
        lines.append("| 图表 | 来源 | 漏提取项 | 分类 |")
        lines.append("|------|------|---------|------|")
        for c in classify_rows:
            if contract_patterns.search(c["missing_text"]):
                lines.append(f"| {c['chart_title']} | {c['source_file']} | {c['missing_text']} | {c['branch']} |")
        lines.append("")
    else:
        lines.append("无合约序列相关漏检。")
        lines.append("")
    
    lines.append("## 8. 重点高亮：下游消费板块漏检")
    lines.append("")
    if downstream_items:
        lines.append(f"共 {len(downstream_items)} 项下游消费相关漏检：")
        lines.append("")
        lines.append("| 图表 | 来源 | 漏提取项 | 分类 |")
        lines.append("|------|------|---------|------|")
        for c in classify_rows:
            if downstream_patterns.search(c["missing_text"]):
                lines.append(f"| {c['chart_title']} | {c['source_file']} | {c['missing_text']} | {c['branch']} |")
        lines.append("")
    else:
        lines.append("无下游消费板块相关漏检。")
        lines.append("")
    
    lines.append("## 9. 完整漏提取清单")
    lines.append("")
    lines.append("| # | 来源PDF | 图表 | 页码 | 漏提取文本 | 分类 | 根因 | 匹配指标 |")
    lines.append("|---|---------|------|------|-----------|------|------|---------|")
    for i, c in enumerate(classify_rows, 1):
        lines.append(f"| {i} | {c['source_file']} | {c['chart_title']} | {c['page_num']} | {c['missing_text']} | {c['branch']} | {c['root_cause']} | {c['matched_indicator']} |")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*报告生成: DSH-B_CHART_META_JOIN_MATCH_BOARD_TASK*")
    
    content = "\n".join(lines)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
