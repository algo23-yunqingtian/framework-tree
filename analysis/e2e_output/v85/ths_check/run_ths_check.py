#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_ths_check.py

Builds a THS (同花顺) chart template list from the available iwencai
candidates + correction markdown sources, matches each template's
indicators against the HERMES `indicators_v1.json` library, checks the
template's inferred plot type against the plot types HERMES actually
renders in `chart_registry.json`, then emits a summary + two CSVs.

READ-ONLY inputs:
    framework-tree/analysis/iwencai/step3_5metals_candidates.json
    framework-tree/translation-workspace/correction/**/*iwencai*.md
    framework-tree/data/indicators_v1.json
    framework-tree/data/chart_registry.json

OUTPUTS (all written under analysis/e2e_output/v85/ths_check/):
    ths_chart_template_list.json   -- constructed intermediate template list
    ths_chart_check_summary.md     -- human-readable summary report
    ths_chart_check_result.csv     -- one row per template with match status
    ths_missing_indicator_list.csv -- deduplicated missing indicators by frequency

CONSTRAINTS:
    - Stdlib only (json, csv, difflib, os, re, collections, sys)
    - No zhiji / network calls
    - No writes outside the output directory
"""

from __future__ import annotations

import csv
import difflib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths (resolve relative to this script's location)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# SCRIPT_DIR = .../github工作/analysis/e2e_output/v85/ths_check
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

CANDIDATES_JSON = os.path.join(
    ROOT, "framework-tree", "analysis", "iwencai", "step3_5metals_candidates.json"
)
CORRECTION_DIR = os.path.join(
    ROOT, "framework-tree", "translation-workspace", "correction"
)
INDICATORS_JSON = os.path.join(ROOT, "framework-tree", "data", "indicators_v1.json")
CHART_REGISTRY_JSON = os.path.join(ROOT, "framework-tree", "data", "chart_registry.json")

OUT_DIR = SCRIPT_DIR
TEMPLATE_LIST_PATH = os.path.join(OUT_DIR, "ths_chart_template_list.json")
SUMMARY_MD_PATH = os.path.join(OUT_DIR, "ths_chart_check_summary.md")
RESULT_CSV_PATH = os.path.join(OUT_DIR, "ths_chart_check_result.csv")
MISSING_CSV_PATH = os.path.join(OUT_DIR, "ths_missing_indicator_list.csv")

VARIETY_ZH = {
    "CU": "铜", "AL": "铝", "ZN": "锌", "NI": "镍", "SN": "锡",
    "SI": "硅", "LI": "锂", "PB": "铅",
}

# ---------------------------------------------------------------------------
# Regex / noise tables
# ---------------------------------------------------------------------------
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

NOISE_EXACT = {
    "建议图数量",
    "最终保留图",
    "原因",
    "强化当前库存偏紧判断",
    "连续去库且绝对值回落至80万吨下方",
    "仓单持续下降，价格同步走强",
    "总库存维持25万吨以下，注销仓单上升",
    "厂内库存低位，出库量上升",
    "铝棒库存低位且加工费坚挺",
    "明确披露“货权不清库存”规模下降",
    "明确披露「货权不清库存」规模下降",
    "无",
    "无数据",
    "暂无",
    "N/A",
    "NA",
    "—",
    "-",
    "--",
}
# Placeholder like "无" optionally followed by a short parenthetical
_PLACEHOLDER_RE = re.compile(r"^无[（(]?[^（）()]{0,15}[)）]?$")

# Pure count-only like "5张" / "6张"
COUNT_ONLY_RE = re.compile(r"^\d+\s*张$")
# Cross-reference like "同3.1.1" / "同 2.3#4/#5"
REFERENCE_RE = re.compile(r"^同\s*[\d#]")
REFERENCE_ANYWHERE_RE = re.compile(r"同\s*\d")
# English filler words indicating a translated sentence
ENGLISH_SENTENCE_RE = re.compile(
    r"\b(in|of|for|and|the|from|by|per|to|vs|or|not|is|are|was|were|this|that|with|on|at)\b",
    re.I,
)
# Qualitative verbs that indicate a sentence about behaviour, not an indicator
QUALITATIVE_RE = re.compile(
    r"(持续|上升|下降|回落至|回落|偏紧|偏松|维持|同步|同时|且绝对|明显|显著|走弱|走强|回升|低位|高位|坚挺|收窄|扩大|下方|上方|联动)"
)
# Structure markers typical of a proper indicator name
STRUCTURE_MARKERS = ("：", ":", "（", "(", "[", "]", "]", "/", "%")

# Unit / freq regexes (extracted from indicator names)
_PAREN_RE = re.compile(r"[（(]([^()（）]{1,30})[)）]")
_UNIT_TOKENS = (
    "元/金属吨", "美元/金属吨", "元/吨", "美元/吨", "元/干吨", "美元/干吨",
    "美元/吨", "元/千克", "元/公斤", "万元", "亿美元", "万吨", "千吨", "吨", "千克", "公斤",
    "手", "美元", "元", "%", "百分比", "倍", "日", "月", "周",
)
FREQ_RE = re.compile(r"[（(]\s*(日|周|月|季|年|日度|周度|月度|季度|年度|日/周|周/日|日·周|周·月)\s*[)）]")


def normalize_name(s: str) -> str:
    """Lower-case + strip whitespace + unify bracket/colon style. For exact match."""
    if not s:
        return ""
    s = s.strip().lower()
    s = s.replace("：", ":").replace("，", ",")
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"\s+", "", s)
    return s


def is_noise(s: str) -> bool:
    """Return True if s looks like a non-indicator noise entry."""
    if not s:
        return True
    s = s.strip()
    if s in NOISE_EXACT:
        return True
    if _PLACEHOLDER_RE.match(s) and len(s) < 15:
        return True
    if COUNT_ONLY_RE.match(s):
        return True
    if REFERENCE_RE.match(s):
        return True
    if REFERENCE_ANYWHERE_RE.search(s) and len(s) < 30:
        return True
    if any(c in s for c in '"\u201c\u201d\u2018\u2019「」'):
        return True
    if not CJK_RE.search(s):
        # Pure-English string: sentences/translations
        if len(s.split()) > 3:
            return True
        if ENGLISH_SENTENCE_RE.search(s):
            return True
    if "，" in s:
        return True
    # Qualitative verb without any indicator structure marker
    if QUALITATIVE_RE.search(s) and not any(m in s for m in STRUCTURE_MARKERS):
        return True
    return False


def extract_unit_and_freq(indicators):
    """Scan indicator names for a unit and frequency hint."""
    unit = None
    freq = None
    for name in indicators:
        if unit is None:
            for m in _PAREN_RE.finditer(name):
                content = m.group(1).strip()
                # If the parenthetical content is purely a unit token, use it.
                stripped = content.replace("%", "%").strip()
                if stripped in _UNIT_TOKENS:
                    unit = stripped
                    break
                # Also try suffix match (e.g. "Zn≥99.995%（日）" — no unit here, but
                # "锌主力合约收盘价（元/吨）" has unit "元/吨").
                # Fall back: if content ends with a known unit token, use that token.
                for tok in _UNIT_TOKENS:
                    if content.endswith(tok):
                        unit = tok
                        break
                if unit:
                    break
        if freq is None:
            m = FREQ_RE.search(name)
            if m:
                f = m.group(1)
                freq = {
                    "日": "daily", "周": "weekly", "月": "monthly",
                    "季": "quarterly", "年": "yearly",
                    "日度": "daily", "周度": "weekly", "月度": "monthly",
                    "季度": "quarterly", "年度": "yearly",
                    "日/周": "daily/weekly", "周/日": "weekly/daily",
                    "日·周": "daily/weekly", "周·月": "weekly/monthly",
                }.get(f, f)
    return unit, freq


# ---------------------------------------------------------------------------
# Plot type inference + HERMES supported plot types
# ---------------------------------------------------------------------------
HERMES_SUPPORTED_PLOT_TYPES = set()  # populated by load_hermes_supported_plot_types()

# Markers inside a chart_title that indicate HERMES renders this kind of chart.
HERMES_TITLE_CLASSIFICATION = [
    ("季节图", "季节图"),
    ("·季节", "季节图"),
    ("柱状图", "柱状图"),
]

_RANK_RE = re.compile(r"前\s*(?:20|10)\s*大|前十|排名|Top\s*\d+|前\s*\d+\s*大")
_PIE_RE = re.compile(r"占比|构成|饼图|结构占比|占比图")
_PIE_EXPLICIT = re.compile(r"占比图|饼图")
_BAR_EXPLICIT = re.compile(r"柱状图|柱图")
_RANK_EXPLICIT = re.compile(r"排名图")
_SEASON_EXPLICIT = re.compile(r"季节图|季节性")
_SERIES_EXPLICIT = re.compile(r"时序图|时序")
_STATS_KEYWORDS_RE = re.compile(r"分位|均值|标准差")


def infer_plot_type(indicators):
    """Infer the THS chart plot type from a template's indicator names."""
    joined = "；".join(indicators)
    # Explicit markers in the string take precedence
    if _SERIES_EXPLICIT.search(joined):
        return "时序图"
    if _SEASON_EXPLICIT.search(joined):
        return "季节图"
    if _BAR_EXPLICIT.search(joined):
        return "柱状图"
    if _PIE_EXPLICIT.search(joined):
        return "占比图"
    if _RANK_EXPLICIT.search(joined):
        return "排名图"
    # Implicit: ranking indicators (前20大 / 前10大 / 前十)
    if _RANK_RE.search(joined):
        return "排名图"
    # Implicit: composition dominant (all indicators 占比/构成)
    if indicators and all(_PIE_RE.search(ind) for ind in indicators):
        return "占比图"
    # Implicit: statistical (only 分位/均值/标准差)
    if indicators and all(
        _STATS_KEYWORDS_RE.search(ind)
        and not re.search(
            r"价格|收盘价|库存|持仓量|成交量|产量|开工率|进口量|出口量|升贴水|基差|利润|成本|加工费|TC|仓单|社会库存|沪伦比|产能|检修|进口|出口",
            ind,
        )
        for ind in indicators
    ):
        return "统计图"
    return "时序图"


def load_hermes_supported_plot_types():
    """Derive HERMES-supported plot types by inspecting chart titles.

    HERMES charts are essentially time-series line charts (1 or more series),
    plus a handful of seasonality charts. We classify every chart title and
    record the union of plot types observed.
    """
    supported = set()
    counts = Counter()
    with open(CHART_REGISTRY_JSON, encoding="utf-8") as f:
        reg = json.load(f)
    charts = reg.get("charts", [])
    for c in charts:
        t = c.get("chart_title", "") or ""
        # Seasonality
        if "季节图" in t or "·季节" in t:
            supported.add("季节图")
            counts["季节图"] += 1
        # vs-style 2-series comparison is still a time-series chart
        else:
            supported.add("时序图")
            counts["时序图"] += 1
    return supported, counts


# ---------------------------------------------------------------------------
# Template construction
# ---------------------------------------------------------------------------
def build_templates():
    """Collect THS template candidates from both sources, dedupe, filter noise.

    Returns a list of template dicts.
    """
    # variant: {(variety, node): {"variety": ..., "node": ..., "indicators": [...]}}
    merged = {}

    def add(variety: str, node: str, indicators):
        variety = (variety or "").strip().upper()
        node = (node or "").strip()
        if not variety or not node:
            return
        key = (variety, node)
        bucket = merged.setdefault(key, {"variety": variety, "node": node, "indicators": []})
        seen = set(bucket["indicators"])
        for ind in indicators:
            ind = (ind or "").strip()
            if not ind or is_noise(ind):
                continue
            if ind not in seen:
                seen.add(ind)
                bucket["indicators"].append(ind)

    # ---- Primary source: candidates JSON -------------------------------
    if os.path.exists(CANDIDATES_JSON):
        with open(CANDIDATES_JSON, encoding="utf-8") as f:
            data = json.load(f)
        primary_added = 0
        for variety, nodes in data.items():
            if not isinstance(nodes, dict):
                continue
            for node, inds in nodes.items():
                if not isinstance(inds, list):
                    continue
                add(variety, str(node), inds)
                primary_added += 1
        print(f"[build] candidates JSON: {primary_added} (variety,node) buckets added")

    # ---- Secondary source: correction .md files -----------------------
    md_files = []
    for root, _dirs, files in os.walk(CORRECTION_DIR):
        for fn in files:
            if fn.lower().endswith(".md") and "iwencai" in fn.lower():
                md_files.append(os.path.join(root, fn))
    md_files.sort()

    node_line_re = re.compile(r"^\s*[-*+]\s*([\d][\d.]*)\s*\|\s*(.+?)\s*$")
    correction_templates = 0
    correction_indicators = 0
    for path in md_files:
        fname = os.path.basename(path)
        # Variety from filename prefix (before first "_")
        m = re.match(r"^([A-Za-z]+)_", fname)
        variety = m.group(1).upper() if m else ""
        if not variety or len(variety) > 3:
            # Fall back to parent dir name if filename didn't hint
            parent = os.path.basename(os.path.dirname(path))
            if re.match(r"^[A-Za-z]{1,3}$", parent):
                variety = parent.upper()
        if not variety:
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                m = node_line_re.match(line)
                if not m:
                    continue
                node = m.group(1)
                rest = m.group(2).strip()
                # Split by Chinese / ASCII semicolon only (indicator delimiter)
                parts = [p.strip() for p in re.split(r"[；;]", rest)]
                template_indicators = []
                for p in parts:
                    p = p.strip().rstrip("，,")
                    if not p or is_noise(p):
                        continue
                    template_indicators.append(p)
                    correction_indicators += 1
                if template_indicators:
                    add(variety, node, template_indicators)
                    correction_templates += 1

    print(f"[build] correction MD files scanned: {len(md_files)}")
    print(f"[build] correction MD lines producing a template: {correction_templates}")
    print(f"[build] correction MD indicators kept after noise filter: {correction_indicators}")

    # ---- Build final template list -------------------------------------
    templates = []
    for (variety, node), info in sorted(merged.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        indicators = list(info["indicators"])
        # Final intra-template dedup (preserve order)
        seen = set()
        unique = []
        for ind in indicators:
            if ind not in seen:
                seen.add(ind)
                unique.append(ind)
        indicators = unique
        if not indicators:
            continue

        # Auto-generated template_id (unique per variety+node)
        template_id = f"THS-{variety}-{node}"

        # Plot type
        plot_type = infer_plot_type(indicators)

        # Unit / freq inference
        unit, freq = extract_unit_and_freq(indicators)

        # Chart title: first indicator (with node + variety + plot_type hints)
        variety_zh = VARIETY_ZH.get(variety, variety)
        if len(indicators) == 1:
            title_body = indicators[0]
        elif len(indicators) == 2:
            title_body = f"{indicators[0]} vs {indicators[1]}"
        else:
            title_body = f"{indicators[0]} 等{len(indicators)}项"
        chart_title = f"{variety_zh} · {node} · {title_body} · {plot_type}"

        templates.append({
            "template_id": template_id,
            "variety": variety,
            "node": node,
            "plot_type": plot_type,
            "chart_title": chart_title,
            "indicator_name_list": indicators,
            "单位": unit,
            "频率": freq,
        })

    print(f"[build] final template count: {len(templates)}")
    return templates


# ---------------------------------------------------------------------------
# Indicators index
# ---------------------------------------------------------------------------
def build_indicators_index():
    """Load indicators_v1.json and build matching indexes."""
    with open(INDICATORS_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    entries = []
    for key, val in raw.items():
        if key.startswith("_") or key in ("version", "change", "updated"):
            continue
        if not isinstance(val, dict):
            continue
        name = val.get("name")
        if not name:
            continue
        entries.append({
            "id": key,
            "name": name,
            "unit": val.get("unit") or "",
            "freq": val.get("freq") or "",
            "verified": bool(val.get("verified")),
            "ids": val.get("ids") or {},
        })
    names = [e["name"] for e in entries]
    by_norm = defaultdict(list)
    for e in entries:
        by_norm[normalize_name(e["name"])].append(e)
    print(f"[index] indicators_v1: {len(entries)} entries indexed, {len(names)} raw names")
    return entries, names, by_norm


def match_indicator(name, names, by_norm, fallback_pool=None):
    """Return (matched_entry_or_None, match_kind).

    match_kind ∈ {"exact", "fuzzy", "none"}
    """
    if not name:
        return None, "none"
    norm = normalize_name(name)
    if norm in by_norm:
        return by_norm[norm][0], "exact"
    # Fuzzy fallback (case/whitespace-stripped names)
    if fallback_pool is None:
        fallback_pool = names
    close = difflib.get_close_matches(norm, [normalize_name(n) for n in names], n=1, cutoff=0.6)
    if close:
        # Map back to entry
        for e_norm, ents in by_norm.items():
            if e_norm == close[0]:
                return ents[0], "fuzzy"
    return None, "none"


# ---------------------------------------------------------------------------
# Per-template match + classify
# ---------------------------------------------------------------------------
def classify_template(matched, missing, plot_supported):
    total = len(matched) + len(missing)
    if total == 0:
        return "EMPTY_TEMPLATE"
    if not missing and plot_supported:
        return "FULL_MATCH"
    if not matched:  # all missing
        return "ALL_MISS"
    if missing:  # some missing
        return "PARTIAL_MISS"
    # all matched but plot type not supported
    return "PLOT_TYPE_NOT_SUPPORT"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------
def write_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_csv(rows, path, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def join_list(lst, sep=";"):
    return sep.join(lst) if lst else ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("THS chart template → HERMES indicators matching check")
    print("=" * 72)
    print(f"ROOT = {ROOT}")
    print(f"OUT_DIR = {OUT_DIR}")

    os.makedirs(OUT_DIR, exist_ok=True)

    # ---- 1. Build template list --------------------------------------
    print("\n[1/6] Building THS chart template list ...")
    templates = build_templates()
    write_json(templates, TEMPLATE_LIST_PATH)
    print(f"    -> wrote {TEMPLATE_LIST_PATH} ({len(templates)} templates)")

    # ---- 2. Load indicators index ------------------------------------
    print("\n[2/6] Loading indicators_v1 index ...")
    entries, names, by_norm = build_indicators_index()

    # ---- 3. Load HERMES supported plot types -------------------------
    print("\n[3/6] Loading HERMES chart registry (supported plot types) ...")
    hermes_supported, hermes_counts = load_hermes_supported_plot_types()
    print(f"    HERMES supported plot types: {sorted(hermes_supported)}")
    print(f"    HERMES chart title counts by plot type: {dict(hermes_counts)}")

    # ---- 4. Per-template matching + classification -------------------
    print("\n[4/6] Matching indicators and classifying templates ...")
    status_counter = Counter()
    result_rows = []
    variety_missing_counter = Counter()
    variety_total_counter = Counter()
    plot_type_counter = Counter()
    plot_type_unsupported_counter = Counter()
    missing_indicator_freq = Counter()
    missing_indicator_templates = defaultdict(list)
    exact_match_count = 0
    fuzzy_match_count = 0

    for t in templates:
        indicators = t["indicator_name_list"]
        matched_names = []
        matched_ids = []
        missing_names = []
        for ind in indicators:
            e, kind = match_indicator(ind, names, by_norm)
            if e is not None:
                matched_names.append(ind)
                matched_ids.append(e["id"])
                if kind == "exact":
                    exact_match_count += 1
                else:
                    fuzzy_match_count += 1
            else:
                missing_names.append(ind)
                missing_indicator_freq[ind] += 1
                if t["template_id"] not in missing_indicator_templates[ind]:
                    missing_indicator_templates[ind].append(t["template_id"])

        plot_supported = t["plot_type"] in hermes_supported
        status = classify_template(matched_names, missing_names, plot_supported)
        status_counter[status] += 1
        plot_type_counter[t["plot_type"]] += 1
        if not plot_supported:
            plot_type_unsupported_counter[t["plot_type"]] += 1
        variety_total_counter[t["variety"]] += 1
        if status != "FULL_MATCH":
            variety_missing_counter[t["variety"]] += 1

        result_rows.append({
            "template_id": t["template_id"],
            "variety": t["variety"],
            "chart_title": t["chart_title"],
            "plot_type": t["plot_type"],
            "all_ths_indicators": join_list(indicators),
            "matched_indicators": join_list(matched_names),
            "missing_indicators": join_list(missing_names),
            "matched_ids": join_list(matched_ids),
            "status": status,
        })

    print(f"    status distribution: {dict(status_counter)}")
    print(f"    exact matches: {exact_match_count}, fuzzy matches: {fuzzy_match_count}")

    # ---- 5. Write result CSV -----------------------------------------
    print("\n[5/6] Writing result CSV ...")
    write_csv(
        result_rows,
        RESULT_CSV_PATH,
        ["template_id", "variety", "chart_title", "plot_type",
         "all_ths_indicators", "matched_indicators", "missing_indicators",
         "matched_ids", "status"],
    )
    print(f"    -> wrote {RESULT_CSV_PATH} ({len(result_rows)} rows)")

    # ---- 5b. Missing indicator CSV -----------------------------------
    print("\n[5b/6] Writing missing indicator CSV ...")
    missing_rows = []
    for name, count in sorted(
        missing_indicator_freq.items(), key=lambda kv: (-kv[1], kv[0])
    ):
        missing_rows.append({
            "indicator_name": name,
            "reference_count": count,
            "sample_template_ids": join_list(missing_indicator_templates[name][:5]),
        })
    write_csv(missing_rows, MISSING_CSV_PATH,
              ["indicator_name", "reference_count", "sample_template_ids"])
    print(f"    -> wrote {MISSING_CSV_PATH} ({len(missing_rows)} rows)")

    # ---- 6. Summary markdown -----------------------------------------
    print("\n[6/6] Writing summary markdown ...")
    total = len(templates)
    lines = []
    lines.append("# THS Chart Template → HERMES 指标匹配检查报告")
    lines.append("")
    lines.append(f"- 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- THS 模板总数: **{total}**")
    lines.append(f"- 品种 (variety): {', '.join(sorted({t['variety'] for t in templates}))}")
    lines.append(f"- HERMES 支持 plot type: {', '.join(sorted(hermes_supported))}")
    lines.append("")
    lines.append("## 1. 分类统计")
    lines.append("")
    lines.append("| 状态 | 数量 | 占比 |")
    lines.append("|---|---:|---:|")
    total_for_pct = sum(status_counter.values()) or 1
    for st in ("FULL_MATCH", "PARTIAL_MISS", "ALL_MISS", "PLOT_TYPE_NOT_SUPPORT", "EMPTY_TEMPLATE"):
        c = status_counter.get(st, 0)
        lines.append(f"| {st} | {c} | {c * 100 / total_for_pct:.1f}% |")
    lines.append("")
    lines.append(f"- 完全匹配 (all indicators in indicators_v1 + plot 支持): **{status_counter.get('FULL_MATCH', 0)}**")
    lines.append(f"- 部分缺失 (some indicators missing): **{status_counter.get('PARTIAL_MISS', 0)}**")
    lines.append(f"- 全部缺失 (all indicators missing): **{status_counter.get('ALL_MISS', 0)}**")
    lines.append(f"- 图型不支持 (all matched, plot 不在 HERMES 支持集): **{status_counter.get('PLOT_TYPE_NOT_SUPPORT', 0)}**")
    lines.append("")
    lines.append(f"- 指标精确匹配次数: {exact_match_count}")
    lines.append(f"- 指标模糊匹配次数: {fuzzy_match_count}")
    lines.append(f"- 唯一缺失指标数: {len(missing_indicator_freq)}")
    lines.append("")
    lines.append("> **⚠️ 方法说明**: 模糊匹配使用 `difflib.get_close_matches(cutoff=0.6)`，"
                 "对中文文本会产生**假阳性**（如「沪铝」误配到「沪铅」），"
                 "因此 FULL_MATCH 数偏乐观、缺失指标数偏保守。"
                 "请结合 `matched_ids` 列人工复核关键字段的实际匹配对象。")
    lines.append("")

    # 2. By variety
    lines.append("## 2. 按品种统计 (missing templates)")
    lines.append("")
    lines.append("| 品种 | 模板总数 | 非 FULL_MATCH | 缺失率 |")
    lines.append("|---|---:|---:|---:|")
    for v in sorted(variety_total_counter.keys()):
        tot = variety_total_counter[v]
        miss = variety_missing_counter.get(v, 0)
        pct = miss * 100 / tot if tot else 0
        lines.append(f"| {v} | {tot} | {miss} | {pct:.1f}% |")
    lines.append("")

    # 3. Plot type distribution
    lines.append("## 3. THS plot type 分布 (与 HERMES 支持情况)")
    lines.append("")
    lines.append("| plot_type | 模板数 | HERMES 支持 |")
    lines.append("|---|---:|:---:|")
    for pt in sorted(plot_type_counter.keys()):
        sup = "✅" if pt in hermes_supported else "❌"
        lines.append(f"| {pt} | {plot_type_counter[pt]} | {sup} |")
    lines.append("")
    if plot_type_unsupported_counter:
        lines.append("**HERMES 不支持的 plot type 明细:**")
        for pt, c in sorted(plot_type_unsupported_counter.items(), key=lambda kv: -kv[1]):
            lines.append(f"- {pt}: {c} 个模板")
    else:
        lines.append("所有 THS 模板 plot type 均被 HERMES 支持。")
    lines.append("")

    # 4. High-risk templates (ALL_MISS + PLOT_TYPE_NOT_SUPPORT)
    high_risk = [r for r in result_rows if r["status"] in ("ALL_MISS", "PLOT_TYPE_NOT_SUPPORT")]
    high_risk.sort(key=lambda r: (r["status"], r["variety"], r["template_id"]))
    lines.append("## 4. 高风险模板清单 (ALL_MISS + PLOT_TYPE_NOT_SUPPORT)")
    lines.append("")
    lines.append(f"共 **{len(high_risk)}** 个高风险模板。")
    lines.append("")
    if high_risk:
        lines.append("| template_id | 品种 | plot_type | status | 缺失指标数 | 示例缺失指标 |")
        lines.append("|---|---|---|---|---:|---|")
        for r in high_risk[:50]:  # cap for readability
            miss_n = len([x for x in r["missing_indicators"].split(";") if x]) if r["missing_indicators"] else 0
            sample = (r["missing_indicators"].split(";")[:2] or ["—"])
            sample_str = ", ".join(sample).replace("|", "/")
            lines.append(f"| {r['template_id']} | {r['variety']} | {r['plot_type']} | {r['status']} | {miss_n} | {sample_str} |")
        if len(high_risk) > 50:
            lines.append(f"| ... | ... | ... | ... | ... | (另有 {len(high_risk) - 50} 条，见 CSV) |")
    else:
        lines.append("_无高风险模板。_")
    lines.append("")

    # 5. Top missing indicators
    lines.append("## 5. Top 缺失指标 (按被引用次数)")
    lines.append("")
    if missing_indicator_freq:
        lines.append("| # | 指标名 | 引用次数 | 示例 template_id |")
        lines.append("|---:|---|---:|---|")
        for i, (name, cnt) in enumerate(
            sorted(missing_indicator_freq.items(), key=lambda kv: (-kv[1], kv[0]))[:30], 1
        ):
            ids = missing_indicator_templates[name][:3]
            lines.append(f"| {i} | {name.replace('|', '/')} | {cnt} | {', '.join(ids)} |")
    else:
        lines.append("_无缺失指标。_")
    lines.append("")

    # 6. Output files
    lines.append("## 6. 输出文件")
    lines.append("")
    for p in [TEMPLATE_LIST_PATH, RESULT_CSV_PATH, MISSING_CSV_PATH, SUMMARY_MD_PATH]:
        try:
            size = os.path.getsize(p)
        except OSError:
            size = -1
        lines.append(f"- `{os.path.relpath(p, ROOT)}` ({size} B)")
    lines.append("")

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"    -> wrote {SUMMARY_MD_PATH}")

    # ---- Final stdout summary -----------------------------------------
    print("\n" + "=" * 72)
    print("DONE")
    print("=" * 72)
    print(f"Total templates:           {total}")
    print(f"FULL_MATCH:                {status_counter.get('FULL_MATCH', 0)}")
    print(f"PARTIAL_MISS:              {status_counter.get('PARTIAL_MISS', 0)}")
    print(f"ALL_MISS:                  {status_counter.get('ALL_MISS', 0)}")
    print(f"PLOT_TYPE_NOT_SUPPORT:     {status_counter.get('PLOT_TYPE_NOT_SUPPORT', 0)}")
    print(f"Unique missing indicators: {len(missing_indicator_freq)}")
    print(f"Exact matches:             {exact_match_count}")
    print(f"Fuzzy matches:             {fuzzy_match_count}")
    print(f"Output dir:                {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
