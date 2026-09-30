#!/usr/bin/env python3
"""
DSH-B_B2_MISSING_INDICATOR_PREP_TASK
Prepares draft indicators for B2 missing-indicator entries.

Reads:
  - missing_classify.csv
  - pdf_chart_meta_all_v2.json
  - indicators_v1.json (READ ONLY)

Outputs:
  - b2_missing_preview.csv
  - b2_missing_indicators_draft.md
  - b2_missing_stat.md
"""

import csv
import json
import re
import os
from collections import Counter
from difflib import SequenceMatcher
from datetime import datetime

BASE = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\pdf_extract"
INDICATORS_PATH = r"D:\DSH_WORK\framework-tree\data\indicators_v1.json"
OUT_DIR = BASE

# ──────────────────────────────────────────────
# 1. Load indicators_v1
# ──────────────────────────────────────────────
with open(INDICATORS_PATH, "r", encoding="utf-8") as f:
    indicators_raw = json.load(f)

indicators_list = []
for key, entry in indicators_raw.items():
    if not isinstance(entry, dict):
        continue
    name = entry.get("name", "")
    ids = entry.get("ids", {})
    unit = entry.get("unit", "")
    freq = entry.get("freq", "")
    category = entry.get("category", "")
    varieties = list(ids.keys()) if isinstance(ids, dict) else []
    indicators_list.append({
        "key": key, "name": name, "unit": unit, "freq": freq,
        "category": category, "varieties": varieties, "ids": ids,
    })

print(f"Loaded {len(indicators_list)} indicators from indicators_v1.json")

# ──────────────────────────────────────────────
# 2. Load missing_classify.csv, filter B2 entries
# ──────────────────────────────────────────────
csv_path = os.path.join(BASE, "missing_classify.csv")
with open(csv_path, "r", encoding="utf-8-sig") as f:
    all_rows = list(csv.DictReader(f))

print(f"Total rows: {len(all_rows)}")

b2_rows = [r for r in all_rows if "B2" in r.get("root_cause", "")]
print(f"B2 entries: {len(b2_rows)}")

# ──────────────────────────────────────────────
# 3. Load chart meta
# ──────────────────────────────────────────────
v2_path = os.path.join(BASE, "pdf_chart_meta_all_v2.json")
with open(v2_path, "r", encoding="utf-8") as f:
    chart_meta = {c["chart_local_id"]: c for c in json.load(f).get("charts", [])}

# ──────────────────────────────────────────────
# 4. Cleaning & inference
# ──────────────────────────────────────────────

SUFFIXES = [r"-当月值$", r"-累计值$", r":当月值$", r":累计值$", r"：当月值$", r"：累计值$"]

FREQ_KEYWORDS = {
    "日度": "daily", "日": "daily",
    "周度": "weekly", "周": "weekly",
    "月度": "monthly", "月": "monthly",
    "季度": "quarterly", "季": "quarterly",
}

VARIETY_MAP = {
    "铝": "AL", "电解铝": "AL", "氧化铝": "AL",
    "铜": "CU", "沪铜": "CU",
    "铅": "PB", "沪铅": "PB",
    "锌": "ZN", "沪锌": "ZN",
    "镍": "NI", "沪镍": "NI", "精炼镍": "NI", "镍铁": "NI",
    "锡": "SN", "沪锡": "SN",
    "工业硅": "SI", "硅": "SI", "多晶硅": "SI",
    "碳酸锂": "LC", "锂": "LC", "氢氧化锂": "LC",
    "不锈钢": "NI", "铬": "NI",
    "光伏": "SI", "组件": "SI",
}

DIMENSION_PATTERNS = [
    (r"价格|均价|现货价|FOB|CIF|现金利润|利润", "价格"),
    (r"库存|社库|厂库|仓单|库存天数|库存变化", "库存"),
    (r"产量|产|开工率|产能|运行产能", "产量"),
    (r"消费|表观消费|终端消费", "消费"),
    (r"进口|出口|净进口|净出口|进出口|到港", "进出口"),
    (r"持仓|成交|基差|月间结构|盘面|盘面结构|连[一二三四五]", "期货"),
    (r"销量|零售|批发", "销量"),
    (r"装机|装机容量", "装机"),
    (r"投资|完成投资", "投资"),
    (r"TC|加工费|折扣|折镍价|折锡价", "加工费"),
    (r"亏损|盈利", "利润"),
    (r"开工", "开工率"),
    (r"周转天数", "库存"),
    (r"平衡", "平衡"),
    (r"比值|相关|Yoy|yoy|同比|累计同比", "统计"),
]

REGION_KEYWORDS = [
    ("中国", "中国"), ("全国", "中国"),
    ("山东", "山东"), ("内蒙古", "内蒙古"), ("广东", "广东"),
    ("江苏", "江苏"), ("浙江", "浙江"), ("上海", "上海"),
    ("天津", "天津"), ("河南", "河南"), ("广西", "广西"),
    ("几内亚", "几内亚"), ("印尼", "印尼"), ("南非", "南非"),
    ("菲律宾", "菲律宾"), ("澳大利亚", "澳大利亚"),
    ("中东", "中东"), ("EU", "EU"), ("北美", "北美"),
    ("东南亚", "东南亚"), ("印度", "印度"),
    ("LME", "LME"), ("SHFE", "SHFE"), ("上期所", "SHFE"),
    ("SMM", "SMM"), ("海关", "中国"),
    ("MHP", "印尼"), ("RKEF", "印尼"),
]

# Known noise texts (exact match after cleaning)
NOISE_TEXTS = {
    # Unit labels
    "万吨", "吨", "元", "天", "亿个", "GW", "GWh", "Gwh", "MWH", "MWh",
    "万万吨", "吨吨", "万万吨吨万吨", "元/吨元/吨",
    "天万吨", "亿个GW", "万金属吨", "金属吨金属吨", "万实物吨万金属吨",
    "万实物吨", "%%%/金属吨", "%/金属吨100", "%%%/金属吨",
    "度", "万元", "美元", "%", "%%", "%%%",
    # Axis label noise
    "汇总1", "平均价:", "日度", "周度", "月度",
    # Chart artifacts
    "0万吨", "0美元/吨", "春节",
    "图图：：SLMHFEE持铝仓近情3况月持仓",
    "吨）", "元/50基吨",
    # Paragraph fragments
    "度相比前期进一步加", "波动。", "显，近期累库放缓",
    "矿1.21亿吨，同比增加", "万吨（17.2%", "其中，几内亚9841",
    "吨，同比增加1884", "），贡献增",
    "（铁合金在线口径）",
    # Legend fragment noise
    "SMM锂盐价格走势图（元/吨）",
    "有色风偏回归，银漫选厂风险资产",
    "复产、采区待验收，低库避险", "存提供基本面支撑",
    "或有限。", "样本白电总用锡Yoy",
    # Short axis fragments
    "GWh", "Gwh", "MWH", "万辆",
    "吨吨", "万万吨",
    # English acronyms that are not indicator names
    "SPX", "Yoy", "vs", "Curve",
    # Chart title fragments (not indicators)
    "SMM锂盐价格走势图",
    # Corrupted unit labels
    "万吨9", "万吨万吨", "万万吨吨万吨", "元/吨元/吨", "万吨吨",
    # Paragraph fragments that got partially cleaned
    "（铁合金在线口径", "铁合金在线口径",
    # More noise texts
    "单小幅增加", "万吨仓单过期", "万吨%", "短期观望策略",
    "万金属吨万金属吨", "累计同比（截至6月", "当月值",
    "60日滚动相关图：锡", "图：铬矿价格：不同品味",
    # Unit labels
    "元/金属吨", "金属吨", "美元/湿吨", "元/度吨",
}


def is_noise_text(text):
    """Check if text is clearly noise, not a valid indicator name."""
    t = text.strip()
    if not t or t in NOISE_TEXTS:
        return True
    return False


def clean_indicator_name(raw):
    """Clean an indicator name: strip suffixes, units, noise."""
    name = raw.strip()
    # Remove "中国:" prefix
    name = re.sub(r"^中国[:：]", "", name)
    # Remove suffixes
    for s in SUFFIXES:
        name = re.sub(s, "", name, count=1)
    # Remove unit labels in parentheses
    name = re.sub(
        r"[（(][^）)]*(?:元|吨|万元|万吨|美元|GWh|GW|亿个|MWH|MWh|万金属吨|金属吨|实物吨|基吨|50基吨|湿吨|百吨|度吨|50基吨|万金属吨)[^）)]*[）)]?",
        "", name)
    # Remove standalone unit tokens
    name = re.sub(
        r"\b(?:万万吨吨万吨|万万吨|吨吨|元/吨元/吨|天万吨|亿个GW|万金属吨|金属吨金属吨|万实物吨万金属吨|万实物吨|Gwh|GWh|MWHMWH|MWH|%%%/金属吨|%/金属吨100|%%%/金属吨|%%%/金属吨|%%%/金属吨)\b",
        "", name)
    # Remove leftover punctuation
    name = re.sub(r"^[（(]+", "", name).strip()  # leading parens
    name = re.sub(r"[（(]+$", "", name).strip()    # trailing parens
    name = re.sub(r"[，。、；：（）()\[\]{}|/\\,\.\;\:\?\?]+$", "", name).strip()
    name = re.sub(r"[:：-]{2,}", ":", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def infer_variety(name):
    for kw, code in VARIETY_MAP.items():
        if kw in name:
            return code
    return ""


def infer_dimension(name):
    for pat, dim in DIMENSION_PATTERNS:
        if re.search(pat, name):
            return dim
    return "其他"


def infer_region(name):
    for kw, region in REGION_KEYWORDS:
        if kw in name:
            return region
    return "中国"


def infer_freq(name, chart_title=""):
    for kw, freq in FREQ_KEYWORDS.items():
        if kw in name or kw in chart_title:
            return freq
    if any(k in name for k in ["库存", "价格", "盘面", "结构", "月间"]):
        return "daily"
    if any(k in name for k in ["产量", "开工", "库存天数"]):
        return "weekly"
    return "unknown"


def infer_unit(name, chart_title=""):
    combined = name + " " + chart_title
    units = [
        ("元/吨", "元/吨"), ("美元/吨", "美元/吨"), ("美元/湿吨", "美元/湿吨"),
        ("元/金属吨", "元/金属吨"), ("元/度吨", "元/度吨"), ("元/50基吨", "元/50基吨"),
        ("万吨", "万吨"), ("吨", "吨"), ("万金属吨", "万金属吨"), ("金属吨", "金属吨"),
        ("万实物吨", "万实物吨"), ("实物吨", "实物吨"),
        ("万辆", "万辆"), ("GWh", "GWh"), ("GW", "GW"),
        ("亿个", "亿个"), ("MWH", "MWh"), ("MWh", "MWh"),
        ("%", "%"), ("美元", "美元"), ("万元", "万元"),
        ("元", "元"), ("天", "天"),
    ]
    for pat, unit in units:
        if pat.lower() in combined.lower():
            return unit
    return ""


def get_source_pdf(row):
    return re.sub(r"\d{8}\.pdf$", "", row.get("source_file", ""))


def fuzzy_search(name, candidates, top_k=3, threshold=0.3):
    results = []
    q = name.lower().strip()
    if not q:
        return []
    for c in candidates:
        t = c["name"].lower().strip()
        if not t:
            continue
        r = SequenceMatcher(None, q, t).ratio()
        if q in t or t in q:
            r = max(r, 0.7)
        if r >= threshold:
            results.append((r, c))
    results.sort(key=lambda x: -x[0])
    return results[:top_k]


# ──────────────────────────────────────────────
# 5. Process B2 entries
# ──────────────────────────────────────────────
entries = []
for row in b2_rows:
    raw = row.get("missing_text", "").strip()
    chart_title = row.get("chart_title", "").strip()
    chart_id = row.get("chart_local_id", "").strip()
    source_file = row.get("source_file", "").strip()
    legend_list_str = row.get("legend_list", "")
    plot_style = row.get("plot_style", "")
    axis_info = row.get("axis_info", "")
    page_num = row.get("page_num", "")
    chart_ctx = chart_meta.get(chart_id, {})

    cleaned = clean_indicator_name(raw)
    noise = is_noise_text(cleaned)

    # If cleaned is empty, use chart_title for inference context
    infer_text = cleaned if cleaned else chart_title

    # Use combined context (cleaned + chart_title) for inference
    combined_ctx = cleaned + " " + chart_title

    variety = infer_variety(combined_ctx)
    dimension = infer_dimension(combined_ctx)
    region = infer_region(combined_ctx)
    freq = infer_freq(cleaned if cleaned else chart_title, chart_title)
    unit = infer_unit(cleaned, chart_title)

    similar = fuzzy_search(cleaned, indicators_list, top_k=3, threshold=0.3)
    similar_names = [f"{s['name']}({s['key']})" for _, s in similar]

    # Priority: use cleaned_name primarily (not chart_title for priority)
    priority = "P2"

    if not noise and cleaned:
        p0_kw = [
            "Cash", "连续合约", "连一", "连二", "连三", "连四", "连五",
            "交通运输", "家电", "房屋建筑", "电力", "净出口",
            "盘面结构", "月间结构", "期月结构",
            "铝终端消费", "总消费",
        ]
        p1_kw = [
            "库存", "库存天数", "库存变化", "分地区", "分仓库",
            "进口", "出口", "到港", "分国别", "净进口", "净出口",
            "社库", "厂库", "仓单", "交割库",
            "铝水比例", "废铝", "铝板", "铝棒",
            "铝材", "铝合金", "原料库存",
            "期货库存", "持仓", "比值",
            "India", "Russia",
            # 期权/期货指标
            "Δ", "IV", "期权", "Risk", "Reversal",
            # 下游消费细分
            "亏损", "利润", "盈利",
            # 电力/基建
            "电网", "投资", "线路",
            # 新能源
            "动力电池", "新能源", "光伏", "组件",
            # 产能/产量细分
            "硫酸镍", "冰镍", "精炼镍", "电解镍", "镍铁", "高碳铬铁",
            "铬矿", "镍矿",
        ]
        for kw in p0_kw:
            if kw in cleaned:
                priority = "P0"
                break
        if priority != "P0":
            for kw in p1_kw:
                if kw in cleaned:
                    priority = "P1"
                    break
    else:
        # Noise text: auto P2 (it's not a real indicator)
        priority = "P2"

    # Tag if noise
    label = ""
    if noise:
        label = "噪声文本(非指标名)"
    elif not cleaned:
        label = "清洗后为空"
    elif len(cleaned) <= 2 and not any('\u4e00' <= ch <= '\u9fff' for ch in cleaned):
        label = "疑似噪声"

    entries.append({
        "priority": priority,
        "source_pdf": get_source_pdf(row),
        "page_num": page_num,
        "chart_local_id": chart_id,
        "chart_title": chart_title,
        "plot_style": plot_style,
        "axis_info": axis_info,
        "raw_text": raw,
        "cleaned_name": cleaned,
        "variety": variety,
        "dimension": dimension,
        "region": region,
        "freq": freq,
        "unit": unit,
        "similar_candidates": similar_names,
        "legend_list": legend_list_str,
        "is_noise": noise,
        "label": label,
    })

# Stats
n_noise = sum(1 for e in entries if e["is_noise"])
print(f"\nProcessed {len(entries)} entries ({n_noise} noise)")

# ──────────────────────────────────────────────
# 6. Output: b2_missing_preview.csv
# ──────────────────────────────────────────────
csv_out = os.path.join(OUT_DIR, "b2_missing_preview.csv")
fieldnames = [
    "priority", "label", "source_pdf", "page_num", "chart_local_id",
    "chart_title", "plot_style", "axis_info",
    "raw_text", "cleaned_name", "variety", "region", "dimension", "freq", "unit",
    "similar_candidates", "legend_list",
]

with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for e in sorted(entries, key=lambda x: (
        0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
        x["source_pdf"], x["chart_local_id"])):
        w.writerow({
            "priority": e["priority"],
            "label": e["label"],
            "source_pdf": e["source_pdf"],
            "page_num": e["page_num"],
            "chart_local_id": e["chart_local_id"],
            "chart_title": e["chart_title"],
            "plot_style": e["plot_style"],
            "axis_info": e["axis_info"],
            "raw_text": e["raw_text"],
            "cleaned_name": e["cleaned_name"],
            "variety": e["variety"],
            "region": e["region"],
            "dimension": e["dimension"],
            "freq": e["freq"],
            "unit": e["unit"],
            "similar_candidates": " | ".join(e["similar_candidates"]),
            "legend_list": e["legend_list"],
        })

print(f"\nWritten: {csv_out}")

# ──────────────────────────────────────────────
# 7. Output: b2_missing_indicators_draft.md
# ──────────────────────────────────────────────
p0 = [e for e in entries if e["priority"] == "P0"]
p1 = [e for e in entries if e["priority"] == "P1"]
p2_real = [e for e in entries if e["priority"] == "P2" and not e["is_noise"]]
p2_noise = [e for e in entries if e["priority"] == "P2" and e["is_noise"]]

DIM_SHORT = {
    "价格": "price", "库存": "stock", "产量": "output",
    "消费": "consumption", "进出口": "trade", "期货": "futures",
    "销量": "sales", "装机": "install", "投资": "invest",
    "加工费": "tc", "利润": "profit", "开工率": "util",
    "平衡": "balance", "其他": "misc", "统计": "stat",
}


def make_draft_json(entry, idx):
    dim_s = DIM_SHORT.get(entry["dimension"], "misc")
    key = f"b2_{idx:03d}_{dim_s}"
    name = entry["cleaned_name"] or "(空)"
    freq_val = entry["freq"] if entry["freq"] in ["daily", "weekly", "monthly"] else "(待确认)"
    unit_val = entry["unit"] or "(待确认)"

    # Try to suggest variety ID from similar
    ids = {}
    for sim_name, sim_entry in fuzzy_search(entry["cleaned_name"], indicators_list, top_k=1, threshold=0.5):
        if sim_entry["ids"]:
            for vc, vi in sim_entry["ids"].items():
                ids[vc] = f"(待查:{vi})"

    return json.dumps({
        key: {
            "name": name,
            "unit": unit_val,
            "freq": freq_val,
            "verified": False,
            "category": f"b2_missing_{dim_s}",
            "ids": ids if ids else {},
            "_origin": "b2_missing_prep",
            "_meta": {
                "source_pdf": entry["source_pdf"],
                "chart_local_id": entry["chart_local_id"],
                "chart_title": entry["chart_title"],
                "priority": entry["priority"],
                "variety_hint": entry["variety"] or "(待确认)",
                "region_hint": entry["region"],
                "dimension": entry["dimension"],
                "similar_in_db": " | ".join(entry["similar_candidates"]) if entry["similar_candidates"] else "无",
                "raw_text": entry["raw_text"],
                "note": "人工复核后录入",
            }
        }
    }, ensure_ascii=False, indent=2)


md = []
md.append("# B2 缺失指标录入草稿")
md.append("")
md.append("> 自动生成，人工复核后复制粘贴到 `indicators_v1.json`")
md.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
md.append(f"> 条目总数: {len(entries)} (有效指标: {len(entries) - n_noise}, 噪声: {n_noise})")
md.append("")

def emit(title, group, color):
    md.append(f"## {color} {title} ({len(group)} 条)")
    md.append("")
    if not group:
        md.append("*（无）*\n")
        return
    md.append("| # | 指标名 | 品种 | 地域 | 频率 | 单位 | 相似候选 | 来源 |")
    md.append("|---|--------|------|------|------|------|----------|------|")
    for i, e in enumerate(group, 1):
        sim = " | ".join(e["similar_candidates"][:2]) if e["similar_candidates"] else "—"
        md.append(
            f"| {i} | `{e['cleaned_name']}` | {e['variety'] or '—'} | {e['region']} | "
            f"{e['freq']} | {e['unit'] or '—'} | {sim} | {e['source_pdf']} {e['chart_local_id']} |")
    md.append("")
    # JSON for up to 15
    lim = min(len(group), 15)
    md.append(f"<details><summary>{color} JSON 录入片段（前 {lim} 条）</summary>\n")
    for i, e in enumerate(group[:lim], 1):
        md.append(f"### {i}. {e['cleaned_name']}")
        md.append("")
        md.append("```json")
        md.append(make_draft_json(e, i))
        md.append("```\n")
    md.append("</details>\n")

emit("P0 — 周报高频图表（优先录入）", p0, "🔴")
emit("P1 — 中频出现指标", p1, "🟡")
emit("P2 — 低频偶现有效指标", p2_real, "🟢")
emit("P2 — 噪声文本（非真实指标，供参考）", p2_noise, "⚪")

md_path = os.path.join(OUT_DIR, "b2_missing_indicators_draft.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print(f"Written: {md_path}")

# ──────────────────────────────────────────────
# 8. Output: b2_missing_stat.md
# ──────────────────────────────────────────────
has_similar = sum(1 for e in entries if e["similar_candidates"])
n_valid = len(entries) - n_noise

st = []
st.append("# B2 缺失指标统计报告")
st.append("")
st.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.append(f"> 来源: `missing_classify.csv` | 指标库: `indicators_v1.json` ({len(indicators_list)} 条)")
st.append("")

st.append("## 总览")
st.append("")
st.append(f"- B2 总条目: **{len(entries)}**")
st.append(f"- 有效指标名: **{n_valid}**")
st.append(f"- 噪声文本(非指标名): **{n_noise}**")
st.append(f"- P0 🔴 高频优先: **{len(p0)}**")
st.append(f"- P1 🟡 中频: **{len(p1)}**")
st.append(f"- P2 🟢 低频有效: **{len(p2_real)}**")
st.append(f"- P2 ⚪ 噪声: **{len(p2_noise)}**")
st.append("")

st.append("## 来源 PDF 分布")
st.append("")
st.append("| PDF 来源 | 条目数 | 有效 | 噪声 | P0 | P1 | P2有效 |")
st.append("|----------|--------|------|------|----|----|--------|")
pdf_ctr = Counter(e["source_pdf"] for e in entries)
for pdf, cnt in sorted(pdf_ctr.items(), key=lambda x: -x[1]):
    sub = [e for e in entries if e["source_pdf"] == pdf]
    n_ok = sum(1 for e in sub if not e["is_noise"])
    n_ns = sum(1 for e in sub if e["is_noise"])
    st.append(f"| {pdf} | {cnt} | {n_ok} | {n_ns} | "
              f"{sum(1 for e in sub if e['priority']=='P0')} | "
              f"{sum(1 for e in sub if e['priority']=='P1')} | "
              f"{sum(1 for e in sub if e['priority']=='P2' and not e['is_noise'])} |")
st.append("")

st.append("## 指标维度分布（有效指标）")
st.append("")
valid_entries = [e for e in entries if not e["is_noise"]]
dim_ctr = Counter(e["dimension"] for e in valid_entries)
st.append("| 维度 | 条目数 | 占比 |")
st.append("|------|--------|------|")
for dim, cnt in sorted(dim_ctr.items(), key=lambda x: -x[1]):
    st.append(f"| {dim} | {cnt} | {cnt/len(valid_entries)*100:.1f}% |")
st.append("")

st.append("## 品种分布（有效指标）")
st.append("")
var_ctr = Counter(e["variety"] if e["variety"] else "未识别" for e in valid_entries)
st.append("| 品种 | 条目数 | 占比 |")
st.append("|------|--------|------|")
for var, cnt in sorted(var_ctr.items(), key=lambda x: -x[1]):
    st.append(f"| {var} | {cnt} | {cnt/len(valid_entries)*100:.1f}% |")
st.append("")

st.append("## 频率分布（有效指标）")
st.append("")
freq_ctr = Counter(e["freq"] for e in valid_entries)
st.append("| 频率 | 条目数 |")
st.append("|------|--------|")
for freq, cnt in sorted(freq_ctr.items(), key=lambda x: -x[1]):
    st.append(f"| {freq} | {cnt} |")
st.append("")

st.append("## 模糊匹配统计")
st.append("")
st.append(f"- 有相似候选: **{has_similar}** ({has_similar/len(entries)*100:.1f}%)")
st.append(f"- 无相似候选: **{len(entries)-has_similar}** ({(len(entries)-has_similar)/len(entries)*100:.1f}%)")
st.append("")

st.append("## 优先级规则")
st.append("")
st.append("| 优先级 | 数量 | 规则 |")
st.append("|--------|------|------|")
st.append("| P0 🔴 |  | 期货次合约(Cash/连三/连四/连五)、铝下游消费细分(交通运输/家电/房屋建筑/电力)、盘面结构 |")
st.append(f"| | {len(p0)} | |")
st.append("| P1 🟡 |  | 分地区库存、分国别进出口、社库/厂库/仓单 |")
st.append(f"| | {len(p1)} | |")
st.append("| P2 🟢 |  | 低频偶现有效指标 |")
st.append(f"| | {len(p2_real)} | |")
st.append("| P2 ⚪ |  | 噪声文本(非真实指标) |")
st.append(f"| | {len(p2_noise)} | |")
st.append("")

st.append("## 操作说明")
st.append("")
st.append("1. 查看 `b2_missing_preview.csv` 获取完整条目")
st.append("2. 查看 `b2_missing_indicators_draft.md` 获取 JSON 录入片段")
st.append("3. **P0 优先处理**，P1 次之，P2 可暂缓")
st.append("4. 注意检查模糊匹配候选，避免重复录入")
st.append("5. 噪声文本行（⚪）可直接跳过，无需录入")
st.append("")

stat_path = os.path.join(OUT_DIR, "b2_missing_stat.md")
with open(stat_path, "w", encoding="utf-8") as f:
    f.write("\n".join(st))
print(f"Written: {stat_path}")

print("\n" + "=" * 60)
print("DONE. Summary:")
print(f"  Total B2: {len(entries)} (valid: {n_valid}, noise: {n_noise})")
print(f"  P0: {len(p0)}, P1: {len(p1)}, P2(real): {len(p2_real)}, P2(noise): {len(p2_noise)}")
print(f"  With similar: {has_similar}")
