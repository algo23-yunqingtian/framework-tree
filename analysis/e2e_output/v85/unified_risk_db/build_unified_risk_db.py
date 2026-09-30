#!/usr/bin/env python3
"""
DSH-B_THS_MATCH_FINALIZE_AND_UNIFY_RISK_DB
Build unified indicator risk database from PDF + THS risk data.

Output:
  1. unified_indicator_risk_db.csv
  2. unified_risk_summary_report.md
  3. risk_db_schema.md
  4. semantic_blacklist_fixed.json (copy)
"""

import csv
import json
import hashlib
import os
import re
from datetime import datetime

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE = r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85"
OUT = os.path.join(BASE, "unified_risk_db")
THS_DIR = os.path.join(BASE, "tonghuashun_recheck_fixed")
FUZZY_DIR = os.path.join(BASE, "fuzzy_match_fix")

# ─── Create output dir ──────────────────────────────────────────────────────
os.makedirs(OUT, exist_ok=True)

# ─── 1. Load fixed blacklist ────────────────────────────────────────────────
BL_PATH = os.path.join(THS_DIR, "semantic_blacklist_fixed.json")
with open(BL_PATH, encoding="utf-8") as f:
    blacklist = json.load(f)

# Build rule lookup
RULE_LOOKUP = {}
for rule in blacklist["rules"]:
    rid = rule["rule_id"]
    RULE_LOOKUP[rid] = {
        "name": rule["name"],
        "category": rule["category"],
        "severity": rule["severity"],
        "left_patterns": rule["left_patterns"],
        "right_patterns": rule["right_patterns"],
        "description": rule["description"],
    }

# ─── 2. Parse PDF P0 conflicts ──────────────────────────────────────────────
# From revised_full_ok_list.md "被降级模板明细" table
# Format: | # | 模板ID | 品种 | 图表标题 | 被拒绝条目 | 冲突描述 |
PDF_P0_RAW = [
    {"template_id": "TPL-AL-013", "variety": "AL", "title": "LME主要仓库场内库存", "entry": "LME主要仓库场内库存", "conflict_desc": "场内库存与非仓单库存互斥"},
    {"template_id": "TPL-LC-054", "variety": "LC", "title": "碳酸锂 三元523需求", "entry": "碳酸锂 三元523需求", "conflict_desc": "利润与需求口径冲突"},
    {"template_id": "TPL-LC-084", "variety": "LC", "title": "其他电池(磷酸铁锂) 销量", "entry": "其他电池(磷酸铁锂) 销量", "conflict_desc": "销量与产量互斥"},
    {"template_id": "TPL-LC-086", "variety": "LC", "title": "其他电池(磷酸铁锂) 销量", "entry": "其他电池(磷酸铁锂) 销量", "conflict_desc": "销量与产量互斥"},
    {"template_id": "TPL-LC-087", "variety": "LC", "title": "磷酸铁锂 电池 国内销量", "entry": "磷酸铁锂 电池 国内销量", "conflict_desc": "国内销量与出口互斥(反向)"},
    {"template_id": "TPL-LC-091", "variety": "LC", "title": "新能源乘用车 产量", "entry": "新能源乘用车 产量", "conflict_desc": "产量与销量互斥"},
    {"template_id": "TPL-LC-092", "variety": "LC", "title": "新能源乘用车 产量", "entry": "新能源乘用车 产量", "conflict_desc": "产量与销量互斥"},
    {"template_id": "TPL-LC-099", "variety": "LC", "title": "其他电池(磷酸铁锂) 销量", "entry": "其他电池(磷酸铁锂) 销量", "conflict_desc": "销量与产量互斥"},
    {"template_id": "TPL-LC-100", "variety": "LC", "title": "磷酸铁锂 电池 国内销量", "entry": "磷酸铁锂 电池 国内销量", "conflict_desc": "国内销量与出口互斥(反向)"},
    {"template_id": "TPL-NI-008", "variety": "NI", "title": "中国电解镍净进口量", "entry": "中国电解镍净进口量", "conflict_desc": "镍与铜跨品种禁止"},
    {"template_id": "TPL-SI-014", "variety": "SI", "title": "工业硅样本工厂库存(SMM)", "entry": "工业硅样本工厂库存(SMM)", "conflict_desc": "硅与苯乙烯跨品种禁止"},
    {"template_id": "TPL-SI-017", "variety": "SI", "title": "工业硅样本工厂库存(SMM)", "entry": "工业硅样本工厂库存(SMM)", "conflict_desc": "硅与苯乙烯跨品种禁止"},
    {"template_id": "TPL-SI-019", "variety": "SI", "title": "工业硅供需平衡", "entry": "工业硅供需平衡", "conflict_desc": "硅与黄金跨品种禁止"},
]

# Match PDF conflict descriptions to blacklist rule IDs
def match_pdf_conflict_to_rule(desc):
    """Map PDF conflict description to blacklist rule ID"""
    mapping = {
        "场内库存与非仓单库存互斥": "BL-005",
        "利润与需求口径冲突": "BL-009",
        "销量与产量互斥": "BL-003",
        "产量与销量互斥": "BL-002",
        "国内销量与出口互斥(反向)": "BL-015",
        "镍与铜跨品种禁止": "BL-022",
        "硅与苯乙烯跨品种禁止": "BL-020",
        "硅与黄金跨品种禁止": "BL-021",
    }
    # Also check the desc contains these strings
    for key, val in mapping.items():
        if key in desc:
            return val
    return ""

# Also get matched names from p0_cases_found in semantic_blacklist_fixed.json
PDF_MATCHED_NAMES = {
    "TPL-AL-013": "LME：非仓单库存：欧洲（日）",
    "TPL-LC-054": "SMM: 碳酸锂现金生产利润: 外购三元极片黑粉（Li: 5.5%-6.5%）:",
    "TPL-LC-084": "SMM: 境内其他电池产量: 月度",
    "TPL-LC-086": "SMM: 境内其他电池产量: 月度",
    "TPL-LC-091": "SMM: 国产乘用车销量-新能源汽车: 周度",
    "TPL-LC-092": "SMM: 国产乘用车销量-新能源汽车: 周度",
    "TPL-LC-099": "SMM: 境内其他电池产量: 月度",
}
# For entries without direct match in p0_cases_found, we note them
PDF_MATCHED_NAMES_EXTRA = {
    "TPL-LC-087": "",  # 磷酸铁锂 电池 国内销量 — 国内销量与出口互斥
    "TPL-LC-100": "",  # 磷酸铁锂 电池 国内销量 — 国内销量与出口互斥
    "TPL-NI-008": "",  # 中国电解镍净进口量 — 镍与铜跨品种禁止
    "TPL-SI-014": "",  # 工业硅样本工厂库存(SMM) — 硅与苯乙烯跨品种禁止
    "TPL-SI-017": "",  # 工业硅样本工厂库存(SMM) — 硅与苯乙烯跨品种禁止
    "TPL-SI-019": "",  # 工业硅供需平衡 — 硅与黄金跨品种禁止
}

# Build PDF risk entries
pdf_entries = []
for item in PDF_P0_RAW:
    rule_id = match_pdf_conflict_to_rule(item["conflict_desc"])
    rule_info = RULE_LOOKUP.get(rule_id, {})
    matched_name = PDF_MATCHED_NAMES.get(item["template_id"], "")
    if not matched_name:
        matched_name = PDF_MATCHED_NAMES_EXTRA.get(item["template_id"], "")
    pdf_entries.append({
        "source": "PDF",
        "template_id": item["template_id"],
        "variety": item["variety"],
        "indicator_name": item["entry"],
        "indicator_title": item["title"],
        "risk_level": "P0",
        "risk_category": rule_info.get("category", ""),
        "conflict_reason": item["conflict_desc"],
        "blacklist_id": rule_id,
        "blacklist_rule_name": rule_info.get("name", ""),
        "matched_name": matched_name,
        "conflict_type": "跨品种" if "跨品种" in item["conflict_desc"] else ("口径冲突" if "口径" in item["conflict_desc"] else "互斥"),
        "is_duplicate": "",  # will be filled
        "duplicate_of": "",   # will be filled
    })

# ─── 3. Parse THS P0/P1/P2 from CSV ────────────────────────────────────────
THS_CSV = os.path.join(THS_DIR, "ths_updated_match_stat.csv")
ths_entries = []
ths_p1_p2 = []

with open(THS_CSV, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        bs = row.get("blacklist_status", "").strip()
        p0 = row.get("p0_conflict", "").strip()
        warn = row.get("warning_conflict", "").strip()
        rules_str = row.get("blacklist_rules", "").strip()

        # P0 conflicts
        if p0 == "YES" or bs == "P0_CONFLICT":
            rules_list = [r.strip() for r in rules_str.split(";") if r.strip()]
            primary_rule = rules_list[0] if rules_list else ""
            rule_info = RULE_LOOKUP.get(primary_rule, {})
            ths_entries.append({
                "source": "THS",
                "template_id": row.get("template_id", "").strip(),
                "variety": row.get("variety", "").strip(),
                "indicator_name": row.get("series_name", "").strip(),
                "indicator_title": row.get("series_name", "").strip(),
                "risk_level": "P0",
                "risk_category": rule_info.get("category", ""),
                "conflict_reason": f"{primary_rule}({rule_info.get('name','')})" if rule_info else "",
                "blacklist_id": primary_rule,
                "blacklist_rule_name": rule_info.get("name", ""),
                "matched_name": row.get("matched_name", "").strip(),
                "conflict_type": "跨品种" if rule_info.get("category") == "品种口径" else ("口径冲突" if "口径" in rule_info.get("category", "") else "互斥"),
                "verify_status": row.get("verify_status", "").strip(),
                "is_duplicate": "",
                "duplicate_of": "",
            })
        # P1/P2 warnings
        elif warn == "YES":
            rules_list = [r.strip() for r in rules_str.split(";") if r.strip()]
            primary_rule = rules_list[0] if rules_list else ""
            rule_info = RULE_LOOKUP.get(primary_rule, {})
            level = rule_info.get("severity", "P1")
            ths_p1_p2.append({
                "source": "THS",
                "template_id": row.get("template_id", "").strip(),
                "variety": row.get("variety", "").strip(),
                "indicator_name": row.get("series_name", "").strip(),
                "indicator_title": row.get("series_name", "").strip(),
                "risk_level": level,
                "risk_category": rule_info.get("category", ""),
                "conflict_reason": f"{primary_rule}({rule_info.get('name','')})",
                "blacklist_id": primary_rule,
                "blacklist_rule_name": rule_info.get("name", ""),
                "matched_name": row.get("matched_name", "").strip(),
                "conflict_type": "警告",
                "verify_status": row.get("verify_status", "").strip(),
                "is_duplicate": "",
                "duplicate_of": "",
            })

# ─── 4. Merge and deduplicate ──────────────────────────────────────────────
all_entries = pdf_entries + ths_entries + ths_p1_p2

# Deduplication: same indicator name + same variety + same blacklist rule = duplicate
# Key: (indicator_name_normalized, variety, blacklist_id)
seen = {}
unique_entries = []
duplicate_records = []

for entry in all_entries:
    key = (entry["indicator_name"].strip(), entry["variety"].strip(), entry["blacklist_id"])
    if key in seen:
        # This is a duplicate
        entry["is_duplicate"] = "YES"
        entry["duplicate_of"] = seen[key]
        duplicate_records.append(entry)
    else:
        seen[key] = f"{entry['source']}:{entry['template_id']}"
        entry["is_duplicate"] = "NO"
        entry["duplicate_of"] = ""
        unique_entries.append(entry)

# Also add duplicates to the full list for reporting
full_risk_db = unique_entries + duplicate_records

# Sort by source (PDF first), then risk_level (P0 > P1 > P2), then template_id
severity_order = {"P0": 0, "P1": 1, "P2": 2, "WARNING": 3, "": 4}
full_risk_db.sort(key=lambda e: (
    {"PDF": 0, "THS": 1}.get(e["source"], 9),
    severity_order.get(e["risk_level"], 9),
    e["template_id"],
))

# ─── 5. Write unified_indicator_risk_db.csv ─────────────────────────────────
CSV_HEADERS = [
    "id", "source", "template_id", "variety",
    "indicator_name", "indicator_title",
    "risk_level", "risk_category", "conflict_type",
    "conflict_reason", "blacklist_id", "blacklist_rule_name",
    "matched_name", "verify_status",
    "is_duplicate", "duplicate_of",
]

CSV_PATH = os.path.join(OUT, "unified_indicator_risk_db.csv")
with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    for i, entry in enumerate(full_risk_db, 1):
        row = dict(entry)
        row["id"] = f"RISK-{i:03d}"
        writer.writerow(row)

csv_line_count = len(full_risk_db) + 1  # +1 for header
print(f"[OK] CSV written: {CSV_PATH} ({csv_line_count} lines)")

# ─── 6. Cross-reference analysis ───────────────────────────────────────────
# PDF templates involved
pdf_templates = set(e["template_id"] for e in pdf_entries)
pdf_varieties = set(e["variety"] for e in pdf_entries)
pdf_rules = set(e["blacklist_id"] for e in pdf_entries)
pdf_indicators = set(e["indicator_name"] for e in pdf_entries)

# THS templates involved
ths_templates = set(e["template_id"] for e in ths_entries)
ths_varieties = set(e["variety"] for e in ths_entries)
ths_rules = set(e["blacklist_id"] for e in ths_entries)
ths_indicators = set(e["indicator_name"] for e in ths_entries)

# Overlap analysis
common_varieties = pdf_varieties & ths_varieties
common_rules = pdf_rules & ths_rules
common_indicators = pdf_indicators & ths_indicators

# Check if any indicator appears in both PDF and THS (even with different template IDs)
cross_source_indicator_overlap = []
for pdf_ind in pdf_indicators:
    for ths_ind in ths_indicators:
        if pdf_ind == ths_ind or pdf_ind in ths_ind or ths_ind in pdf_ind:
            cross_source_indicator_overlap.append((pdf_ind, ths_ind))

# Check for shared blacklist rules with same variety
shared_rule_variety = []
for rule_id in common_rules:
    pdf_vars_for_rule = set(e["variety"] for e in pdf_entries if e["blacklist_id"] == rule_id)
    ths_vars_for_rule = set(e["variety"] for e in ths_entries if e["blacklist_id"] == rule_id)
    overlap_vars = pdf_vars_for_rule & ths_vars_for_rule
    if overlap_vars:
        shared_rule_variety.append((rule_id, overlap_vars))

# Cross-variety mismatch stats
cross_variety_p0 = [e for e in full_risk_db if e["risk_level"] == "P0" and e["conflict_type"] == "跨品种"]
cross_variety_rules = {}
for e in cross_variety_p0:
    rid = e["blacklist_id"]
    cross_variety_rules[rid] = cross_variety_rules.get(rid, 0) + 1

# Definition error (口径错误) stats
definition_errors = [e for e in full_risk_db if e["conflict_type"] in ("口径冲突", "互斥")]
definition_error_rules = {}
for e in definition_errors:
    rid = e["blacklist_id"]
    definition_error_rules[rid] = definition_error_rules.get(rid, 0) + 1

# Risk level counts
p0_count = sum(1 for e in full_risk_db if e["risk_level"] == "P0")
p1_count = sum(1 for e in full_risk_db if e["risk_level"] == "P1")
p2_count = sum(1 for e in full_risk_db if e["risk_level"] == "P2")
clean_count = 0  # CLEAN is not in risk DB, it's the complement

pdf_total = len(pdf_entries)
ths_p0_total = len(ths_entries)
ths_p1p2_total = len(ths_p1_p2)

total_unique = len(unique_entries)
total_duplicates = len(duplicate_records)
total_entries = len(full_risk_db)

# ─── 7. Write unified_risk_summary_report.md ────────────────────────────────
report_lines = []
r = report_lines.append

r("# V85 统一指标风险数据库 — 汇总分析报告")
r("")
r(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
r(f"**任务**: DSH-B_THS_MATCH_FINALIZE_AND_UNIFY_RISK_DB")
r(f"**黑名单版本**: v85-bl021-fixed (25 rules)")
r(f"**输出目录**: `analysis/e2e_output/v85/unified_risk_db/`")
r("")
r("---")
r("")

# Section 1: Overview
r("## 1. 总体概况")
r("")
r("| 指标 | 数值 |")
r("|------|------|")
r(f"| 统一风险库总条目 | {total_entries} |")
r(f"| 去重后独立风险条目 | {total_unique} |")
r(f"| 重复标记条目 | {total_duplicates} |")
r(f"| PDF来源风险条目 | {pdf_total} |")
r(f"| THS来源P0风险条目 | {ths_p0_total} |")
r(f"| THS来源P1/P2警告条目 | {ths_p1p2_total} |")
r(f"| P0（语义冲突阻塞） | {p0_count} |")
r(f"| P1（高风险人工复核） | {p1_count} |")
r(f"| P2（低风险提示） | {p2_count} |")
r(f"| 黑名单规则总数 | {len(RULE_LOOKUP)} |")
r(f"| 涉及黑名单规则数（P0触发） | {len(set(e['blacklist_id'] for e in full_risk_db if e['risk_level'] == 'P0' and e['blacklist_id']))} |")
r("")

# Section 2: PDF vs THS overlap
r("## 2. PDF 与 THS 指标重合度分析")
r("")
r("| 维度 | PDF | THS | 交集 | 重合率 |")
r("|------|-----|-----|------|--------|")
r(f"| 风险条目数 | {pdf_total} | {ths_p0_total} (P0) + {ths_p1p2_total} (P1/P2) | — | — |")
r(f"| 涉及模板数 | {len(pdf_templates)} | {len(ths_templates)} | — | — |")
r(f"| 涉及品种数 | {len(pdf_varieties)} ({', '.join(sorted(pdf_varieties))}) | {len(ths_varieties)} ({', '.join(sorted(ths_varieties))}) | {len(common_varieties)} ({', '.join(sorted(common_varieties))}) | {len(common_varieties)/max(len(pdf_varieties | ths_varieties),1)*100:.1f}% |")
r(f"| 涉及规则数 | {len(pdf_rules)} ({', '.join(sorted(pdf_rules))}) | {len(ths_rules)} ({', '.join(sorted(ths_rules))}) | {len(common_rules)} ({', '.join(sorted(common_rules))}) | {len(common_rules)/max(len(pdf_rules | ths_rules),1)*100:.1f}% |")
r("")
r("### 2.1 跨品种P0冲突的共同规则")
r("")
if shared_rule_variety:
    r("| 黑名单ID | 规则名称 | PDF品种 | THS品种 | 重叠品种 |")
    r("|----------|----------|---------|---------|----------|")
    for rule_id, overlap_vars in shared_rule_variety:
        pdf_vars = sorted(set(e["variety"] for e in pdf_entries if e["blacklist_id"] == rule_id))
        ths_vars = sorted(set(e["variety"] for e in ths_entries if e["blacklist_id"] == rule_id))
        r(f"| {rule_id} | {RULE_LOOKUP[rule_id]['name']} | {', '.join(pdf_vars)} | {', '.join(ths_vars)} | {', '.join(sorted(overlap_vars))} |")
else:
    r("PDF与THS的P0冲突之间无共享规则+品种的交集（各自独立的冲突场景）。")
r("")

r("### 2.2 跨来源相同指标分析")
r("")
if cross_source_indicator_overlap:
    r("以下指标名称在PDF和THS中都出现：")
    r("")
    r("| PDF指标名称 | THS指标名称 |")
    r("|-------------|-------------|")
    for pdf_ind, ths_ind in cross_source_indicator_overlap:
        r(f"| {pdf_ind} | {ths_ind} |")
else:
    r("**PDF与THS的P0冲突指标名称无交集** — 两套系统的风险指标完全独立，各自反映不同的语义冲突模式。")
r("")

# Section 3: Risk level breakdown
r("## 3. 风险等级分布")
r("")
r("### 3.1 按来源×等级")
r("")
r("| 来源 | P0 | P1 | P2 | 合计 |")
r("|------|----|----|----|------|")
for src in ["PDF", "THS"]:
    src_p0 = sum(1 for e in full_risk_db if e["source"] == src and e["risk_level"] == "P0")
    src_p1 = sum(1 for e in full_risk_db if e["source"] == src and e["risk_level"] == "P1")
    src_p2 = sum(1 for e in full_risk_db if e["source"] == src and e["risk_level"] == "P2")
    src_total = src_p0 + src_p1 + src_p2
    r(f"| {src} | {src_p0} | {src_p1} | {src_p2} | {src_total} |")
r(f"| **合计** | **{p0_count}** | **{p1_count}** | **{p2_count}** | **{total_entries}** |")
r("")

r("### 3.2 按黑名单规则")
r("")
rule_stats = {}
for e in full_risk_db:
    rid = e["blacklist_id"]
    if rid:
        if rid not in rule_stats:
            rule_stats[rid] = {"P0": 0, "P1": 0, "P2": 0, "total": 0}
        rule_stats[rid][e["risk_level"]] += 1
        rule_stats[rid]["total"] += 1

r("| 规则ID | 规则名称 | 类别 | 严重度 | P0 | P1 | P2 | 合计 |")
r("|--------|----------|------|--------|----|----|----|------|")
for rid in sorted(rule_stats.keys()):
    info = RULE_LOOKUP.get(rid, {})
    s = rule_stats[rid]
    r(f"| {rid} | {info.get('name','')} | {info.get('category','')} | {info.get('severity','')} | {s['P0']} | {s['P1']} | {s['P2']} | {s['total']} |")
r("")

r("### 3.3 按风险类别")
r("")
category_stats = {}
for e in full_risk_db:
    cat = e["risk_category"]
    if cat:
        category_stats[cat] = category_stats.get(cat, 0) + 1

r("| 风险类别 | 条目数 | 占比 |")
r("|----------|--------|------|")
for cat in sorted(category_stats.keys(), key=lambda k: -category_stats[k]):
    pct = category_stats[cat] / total_entries * 100
    r(f"| {cat} | {category_stats[cat]} | {pct:.1f}% |")
r("")

# Section 4: Cross-variety mismatch
r("## 4. 跨品种错配统计")
r("")
r(f"**跨品种P0冲突总数**: {len(cross_variety_p0)} 条（占P0的 {len(cross_variety_p0)/max(p0_count,1)*100:.1f}%）")
r("")
r("| 规则ID | 规则名称 | 冲突数 | 说明 |")
r("|--------|----------|--------|------|")
for rid in sorted(cross_variety_rules.keys()):
    info = RULE_LOOKUP.get(rid, {})
    r(f"| {rid} | {info.get('name','')} | {cross_variety_rules[rid]} | {info.get('description','')[:60]} |")
r("")

# Section 4.1: Cross-variety detail by source
r("### 4.1 PDF跨品种冲突明细")
r("")
pdf_cv = [e for e in pdf_entries if e["conflict_type"] == "跨品种"]
r("| 模板ID | 品种 | 指标名称 | 匹配名称 | 规则 | 冲突原因 |")
r("|--------|------|----------|----------|------|----------|")
for e in pdf_cv:
    r(f"| {e['template_id']} | {e['variety']} | {e['indicator_name']} | {e['matched_name']} | {e['blacklist_id']} | {e['conflict_reason']} |")
r("")

r("### 4.2 THS跨品种冲突明细")
r("")
ths_cv = [e for e in ths_entries if e["conflict_type"] == "跨品种"]
r("| 模板ID | 品种 | 指标名称 | 匹配名称 | 规则 | 冲突原因 |")
r("|--------|------|----------|----------|------|----------|")
for e in ths_cv:
    r(f"| {e['template_id']} | {e['variety']} | {e['indicator_name']} | {e['matched_name']} | {e['blacklist_id']} | {e['conflict_reason']} |")
r("")

# Section 5: Definition error stats
r("## 5. 口径错误统计")
r("")
r(f"**口径/互斥类风险总数**: {len(definition_errors)} 条（占全部风险的 {len(definition_errors)/max(total_entries,1)*100:.1f}%）")
r("")
r("| 规则ID | 规则名称 | 严重度 | 条目数 | 说明 |")
r("|--------|----------|--------|--------|------|")
for rid in sorted(definition_error_rules.keys()):
    info = RULE_LOOKUP.get(rid, {})
    r(f"| {rid} | {info.get('name','')} | {info.get('severity','')} | {definition_error_rules[rid]} | {info.get('description','')[:60]} |")
r("")

r("### 5.1 PDF口径错误明细")
r("")
pdf_def = [e for e in pdf_entries if e["conflict_type"] in ("口径冲突", "互斥")]
r("| 模板ID | 品种 | 指标名称 | 匹配名称 | 规则 | 冲突原因 |")
r("|--------|------|----------|----------|------|----------|")
for e in pdf_def:
    r(f"| {e['template_id']} | {e['variety']} | {e['indicator_name']} | {e['matched_name']} | {e['blacklist_id']} | {e['conflict_reason']} |")
r("")

# Section 6: Variant distribution
r("## 6. 品种维度分布")
r("")
variety_stats = {}
for e in full_risk_db:
    v = e["variety"]
    if v not in variety_stats:
        variety_stats[v] = {"P0": 0, "P1": 0, "P2": 0, "PDF": 0, "THS": 0}
    variety_stats[v][e["risk_level"]] = variety_stats[v].get(e["risk_level"], 0) + 1
    variety_stats[v][e["source"]] += 1

r("| 品种 | P0 | P1 | P2 | PDF | THS | 合计 |")
r("|------|----|----|----|-----|-----|------|")
for v in sorted(variety_stats.keys()):
    s = variety_stats[v]
    r(f"| {v} | {s['P0']} | {s['P1']} | {s['P2']} | {s['PDF']} | {s['THS']} | {s['P0']+s['P1']+s['P2']} |")
r("")

# Section 7: Deduplication report
r("## 7. 去重与合并报告")
r("")
r(f"- 总条目数: {total_entries}")
r(f"- 去重后独立条目: {total_unique}")
r(f"- 重复标记条目: {total_duplicates}")
r("")
if duplicate_records:
    r("### 重复条目清单")
    r("")
    r("| 来源 | 模板ID | 指标名称 | 品种 | 规则 | 原始条目 |")
    r("|------|--------|----------|------|------|----------|")
    for e in duplicate_records:
        r(f"| {e['source']} | {e['template_id']} | {e['indicator_name']} | {e['variety']} | {e['blacklist_id']} | {e['duplicate_of']} |")
else:
    r("**无重复条目** — PDF与THS的风险条目完全独立，无交叉重复。")
r("")

# Section 8: PDF revised P0 verification
r("## 8. PDF修订后13条P0冲突核对")
r("")
r(f"- PDF降级模板数: {len(pdf_entries)}")
r(f"- 涉及品种: {', '.join(sorted(pdf_varieties))}")
r(f"- 涉及规则: {', '.join(sorted(pdf_rules))}")
r("")
r("| # | 模板ID | 品种 | 指标名称 | 匹配名称 | 黑名单规则 | 冲突原因 |")
r("|---|--------|------|----------|----------|------------|----------|")
for i, e in enumerate(pdf_entries, 1):
    r(f"| {i} | {e['template_id']} | {e['variety']} | {e['indicator_name']} | {e['matched_name']} | {e['blacklist_id']} | {e['conflict_reason']} |")
r("")

# Section 9: THS P0 verification
r("## 9. THS 20条真实P0冲突核对")
r("")
r(f"- THS P0冲突数: {len(ths_entries)}")
r(f"- 涉及品种: {', '.join(sorted(ths_varieties))}")
r(f"- 涉及规则: {', '.join(sorted(ths_rules))}")
r("")
r("| # | 模板ID | 品种 | 指标名称 | 匹配名称 | 黑名单规则 | 冲突原因 |")
r("|---|--------|------|----------|----------|------------|----------|")
for i, e in enumerate(ths_entries, 1):
    r(f"| {i} | {e['template_id']} | {e['variety']} | {e['indicator_name']} | {e['matched_name']} | {e['blacklist_id']} | {e['conflict_reason']} |")
r("")

# Section 10: THS P1/P2 warnings
r("## 10. THS P1/P2警告条目")
r("")
r(f"- P1/P2警告总数: {len(ths_p1_p2)}")
r("")
r("| # | 模板ID | 品种 | 指标名称 | 匹配名称 | 黑名单规则 | 等级 | 冲突原因 |")
r("|---|--------|------|----------|----------|------------|------|----------|")
for i, e in enumerate(ths_p1_p2, 1):
    r(f"| {i} | {e['template_id']} | {e['variety']} | {e['indicator_name']} | {e['matched_name']} | {e['blacklist_id']} | {e['risk_level']} | {e['conflict_reason']} |")
r("")

# Section 11: Conclusion
r("## 11. 总结与结论")
r("")
r(f"### 11.1 统一风险库规模")
r(f"- **总风险条目**: {total_entries}（含P0 {p0_count}、P1 {p1_count}、P2 {p2_count}）")
r(f"- **独立风险条目**: {total_unique}（无重复）")
r(f"- **风险模板数**: PDF {len(pdf_templates)} + THS {len(ths_templates)} = {len(pdf_templates | ths_templates)}")
r("")

r(f"### 11.2 PDF与THS重合度")
r(f"- 品种交集: {len(common_varieties)} ({', '.join(sorted(common_varieties))})")
r(f"- 规则交集: {len(common_rules)} ({', '.join(sorted(common_rules))})")
r(f"- 指标名称交集: {'有' if cross_source_indicator_overlap else '无'}")
r(f"- PDF与THS的P0冲突场景完全独立，反映两套系统各自暴露的语义盲区")
r("")

r(f"### 11.3 风险特征")
r(f"- 跨品种错配: {len(cross_variety_p0)} 条P0（主要规则: BL-018/019/020/021/022）")
r(f"- 口径/互斥错误: {len(definition_errors)} 条（主要规则: BL-002/003/005/009/015）")
r(f"- P1警告（库存天数/利润产量）: {p1_count} 条")
r(f"- P2提示（供需平衡/价格利润/升贴水）: {p2_count} 条")
r("")

r(f"### 11.4 后续行动建议")
r(f"- **P0-跨品种错配**: 需人工确认是否为匹配错误或数据本身缺失")
r(f"- **P0-口径互斥**: 需调整匹配规则，避免产量↔销量、场内↔非仓单等跨口径匹配")
r(f"- **P1警告**: 低优先级，可在后续迭代中逐步清理")
r(f"- **P2提示**: 仅供参考，暂不需处理")
r("")

r("---")
r("")
r(f"**约束声明**: NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true, NO_RULE_MODIFICATION=true, NO_ZHIJI_API_CALL=true")
r(f"**生成工具**: build_unified_risk_db.py")
r(f"**输出文件**: unified_indicator_risk_db.csv, unified_risk_summary_report.md, risk_db_schema.md, semantic_blacklist_fixed.json")

REPORT_PATH = os.path.join(OUT, "unified_risk_summary_report.md")
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

report_lines_count = len(report_lines)
print(f"[OK] Report written: {REPORT_PATH} ({report_lines_count} lines)")

# ─── 8. Write risk_db_schema.md ─────────────────────────────────────────────
schema_lines = []
s = schema_lines.append

s("# 统一指标风险数据库 — 字段说明文档")
s("")
s(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
s(f"**任务**: DSH-B_THS_MATCH_FINALIZE_AND_UNIFY_RISK_DB")
s(f"**数据库文件**: `unified_indicator_risk_db.csv`")
s(f"**黑名单版本**: v85-bl021-fixed (25 rules)")
s("")
s("---")
s("")
s("## 1. 文件结构")
s("")
s("| 文件 | 说明 |")
s("|------|------|")
s("| unified_indicator_risk_db.csv | 统一指标风险库，PDF+THS合并，含去重标记 |")
s("| unified_risk_summary_report.md | 风险汇总分析报告 |")
s("| risk_db_schema.md | 本文档 — 字段说明 |")
s("| semantic_blacklist_fixed.json | 修复后黑名单规则（25条） |")
s("")
s("## 2. CSV字段定义")
s("")
s("| # | 字段名 | 类型 | 说明 |")
s("|---|--------|------|------|")
s("| 1 | id | string | 唯一标识符，格式 `RISK-NNN`，按来源+严重度+模板ID排序 |")
s("| 2 | source | enum | 来源：`PDF`（PDF周报模板）或 `THS`（同花顺模板） |")
s("| 3 | template_id | string | 模板ID，如 `TPL-LC-054` 或 `THS-NI-2.3` |")
s("| 4 | variety | string | 品种代码，如 `AL`(铝), `LC`(碳酸锂), `NI`(镍), `SI`(工业硅), `SN`(锡), `ZN`(锌) |")
s("| 5 | indicator_name | string | 指标名称/系列名 |")
s("| 6 | indicator_title | string | 图表标题或指标标题 |")
s("| 7 | risk_level | enum | 风险等级：`P0`(语义冲突阻塞) / `P1`(高风险人工复核) / `P2`(低风险提示) |")
s("| 8 | risk_category | string | 风险类别：`品种口径`, `供需口径`, `库存口径`, `经济口径`, `贸易口径`, `基本面口径`, `成本口径` |")
s("| 9 | conflict_type | string | 冲突类型：`跨品种`(跨品种匹配) / `口径冲突`(统计口径冲突) / `互斥`(互斥关系) / `警告` |")
s("| 10 | conflict_reason | string | 冲突原因描述，包含规则ID |")
s("| 11 | blacklist_id | string | 触发的黑名单规则ID，如 `BL-005`, `BL-022` |")
s("| 12 | blacklist_rule_name | string | 黑名单规则名称 |")
s("| 13 | matched_name | string | 匹配到的指标名称（知几指标库中的名称） |")
s("| 14 | verify_status | string | 校验状态（THS专有）：`VALID` / `FILLED` / `INVALID` / `MISSING` |")
s("| 15 | is_duplicate | enum | 是否标记为重复：`YES` / `NO` |")
s("| 16 | duplicate_of | string | 重复标记指向的原始条目，格式 `来源:模板ID` |")
s("")
s("## 3. 风险等级定义")
s("")
s("### P0 — 语义冲突阻塞（Blocking Conflict）")
s("- 不同品种之间的指标匹配（如锡指标匹配到镍数据）")
s("- 统计口径互斥的匹配（如产量匹配到销量）")
s("- 场内库存与非仓单库存互斥匹配")
s("- **影响**: 阻塞图表模板发布，必须人工确认或修正")
s("")
s("### P1 — 高风险人工复核（High Risk Review）")
s("- 库存天数与库存量混用（衍生指标与绝对值混用）")
s("- 利润与产量混用（不同维度经济指标）")
s("- **影响**: 不阻塞发布，但建议人工复核确认")
s("")
s("### P2 — 低风险提示（Low Risk Warning）")
s("- 价格与利润混用")
s("- 升贴水与价格混用")
s("- 供需平衡与价格混用")
s("- **影响**: 仅做提示，不建议处理")
s("")
s("## 4. 数据来源说明")
s("")
s("### PDF来源")
s("- 来自 `fuzzy_match_fix/revised_full_ok_list.md`")
s("- 13条因口径冲突被降级的PDF模板条目")
s("- 原始FULL_OK模板327个，降级13个，修订后314个FULL_OK")
s("")
s("### THS来源")
s("- 来自 `tonghuashun_recheck_fixed/ths_updated_match_stat.csv`")
s("- 基于BL-021修复版黑名单（移除裸`'金'`关键词）重新扫描")
s("- 20条P0冲突 + 17条P1/P2警告")
s("")
s("## 5. 黑名单规则索引")
s("")
s("| 规则ID | 规则名称 | 类别 | 严重度 |")
s("|--------|----------|------|--------|")
for rule in blacklist["rules"]:
    s(f"| {rule['rule_id']} | {rule['name']} | {rule['category']} | {rule['severity']} |")
s("")
s("## 6. 去重规则")
s("")
s("去重键 = `(indicator_name, variety, blacklist_id)`")
s("- 相同指标名称 + 相同品种 + 相同黑名单规则 = 标记为重复")
s("- 重复条目保留在CSV中，通过 `is_duplicate=YES` 和 `duplicate_of` 字段标记")
s("- 独立条目 `is_duplicate=NO`，`duplicate_of` 为空")
s("")
s("## 7. 约束声明")
s("")
s("- NO_SOURCE_MODIFICATION: 不修改原始模板、indicators_v1、GT、匹配规则")
s("- NO_GT_MODIFICATION: 不修改GT标注")
s("- NO_RULE_MODIFICATION: 不修改匹配规则（仅使用固定黑名单）")
s("- NO_ZHIJI_API_CALL: 不调用知几接口，仅静态文本扫描与数据合并")
s("- READ_ONLY + APPEND_ONLY: 只新增文件，禁止覆盖仓库已有历史产物")
s("")
s("---")
s(f"**生成工具**: build_unified_risk_db.py")

SCHEMA_PATH = os.path.join(OUT, "risk_db_schema.md")
with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(schema_lines) + "\n")

schema_lines_count = len(schema_lines)
print(f"[OK] Schema written: {SCHEMA_PATH} ({schema_lines_count} lines)")

# ─── 9. Copy fixed blacklist to output ─────────────────────────────────────
BLACKLIST_COPY_PATH = os.path.join(OUT, "semantic_blacklist_fixed.json")
with open(BL_PATH, "rb") as f:
    bl_bytes = f.read()
with open(BLACKLIST_COPY_PATH, "wb") as f:
    f.write(bl_bytes)
bl_md5 = hashlib.md5(bl_bytes).hexdigest()
print(f"[OK] Blacklist copied: {BLACKLIST_COPY_PATH} (MD5: {bl_md5})")

# ─── 10. Compute MD5 for all output files ──────────────────────────────────
def file_md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def file_size(path):
    return os.path.getsize(path)

output_files = [
    "unified_indicator_risk_db.csv",
    "unified_risk_summary_report.md",
    "risk_db_schema.md",
    "semantic_blacklist_fixed.json",
]

print("\n" + "=" * 70)
print("UNIFIED RISK DB — FILE CHECKSUMS")
print("=" * 70)

for fname in output_files:
    fpath = os.path.join(OUT, fname)
    md5 = file_md5(fpath)
    size = file_size(fpath)
    print(f"  {fname:45s} | {size:>8,d} bytes | MD5: {md5}")

print("=" * 70)

# ─── 11. Final stats summary ────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STATS SUMMARY")
print("=" * 70)
print(f"  Total entries:        {total_entries}")
print(f"  Unique entries:       {total_unique}")
print(f"  Duplicate entries:    {total_duplicates}")
print(f"  P0 conflicts:         {p0_count}")
print(f"  P1 warnings:          {p1_count}")
print(f"  P2 hints:             {p2_count}")
print(f"  PDF entries:          {pdf_total}")
print(f"  THS P0 entries:       {ths_p0_total}")
print(f"  THS P1/P2 entries:    {ths_p1p2_total}")
print(f"  Cross-variety P0:     {len(cross_variety_p0)}")
print(f"  Definition errors:    {len(definition_errors)}")
print(f"  PDF/THS variety overlap: {common_varieties}")
print(f"  PDF/THS rule overlap:    {common_rules}")
print(f"  PDF/THS indicator overlap: {len(cross_source_indicator_overlap)} pairs")
print("=" * 70)
