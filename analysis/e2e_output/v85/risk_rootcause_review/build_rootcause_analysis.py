#!/usr/bin/env python3
"""
DSH-B_V85_RISK_ROOTCAUSE_ANALYSIS_AND_REVIEW_DOC
Build root cause classification, fix recommendations, and review documents
for the 41 unique risk entries in the unified indicator risk database.
"""

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

# ============================================================
# Paths
# ============================================================
BASE = r"D:\DSH_WORK\framework-tree"
RISK_DB_DIR = os.path.join(BASE, "analysis", "e2e_output", "v85", "unified_risk_db")
OUT_DIR = os.path.join(BASE, "analysis", "e2e_output", "v85", "risk_rootcause_review")
RISK_DB_CSV = os.path.join(RISK_DB_DIR, "unified_indicator_risk_db.csv")
BLACKLIST_FIXED = os.path.join(BASE, "analysis", "e2e_output", "v85", "tonghuashun_recheck_fixed", "semantic_blacklist_fixed.json")

os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# Load blacklist rules
# ============================================================
with open(BLACKLIST_FIXED, "r", encoding="utf-8") as f:
    blacklist_data = json.load(f)
BL_RULES = {r["rule_id"]: r for r in blacklist_data["rules"]}

# ============================================================
# Load risk DB and filter unique entries
# ============================================================
rows = []
with open(RISK_DB_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

unique_rows = [r for r in rows if r["is_duplicate"] == "NO"]
assert len(unique_rows) == 41, f"Expected 41 unique entries, got {len(unique_rows)}"

# ============================================================
# Root cause classification function
# ============================================================
def classify_root_cause(row):
    """
    Classify each risk entry into A/B/C categories.
    Returns (category, explanation, fix_dict).
    """
    bl_id = row["blacklist_id"]
    variety = row["variety"]
    indicator = row["indicator_name"]
    matched = row["matched_name"]
    source = row["source"]
    risk_level = row["risk_level"]

    # ---- Cross-variety rules (BL-018, BL-019, BL-020, BL-021, BL-022) ----
    if bl_id in ("BL-018", "BL-019", "BL-020", "BL-021", "BL-022"):
        # All cross-variety matches are algorithm flaws
        # But check if there's a terminology ambiguity component
        if bl_id == "BL-020" and source == "PDF":
            # BL-020: 硅 vs 苯乙烯 — silicon matched to styrene
            # "硅" in 工业硅 might be confused with other "硅" terms
            # But 苯乙烯 doesn't contain 硅, so this is purely algorithmic
            return _mk_fix("A", "模糊匹配算法缺陷：工业硅指标被错误匹配到苯乙烯相关数据，二者完全属于不同品种",
                           bl_id, "rule_optimize",
                           "方案1：黑名单BL-020已覆盖，但需检查匹配算法是否因'硅'子串匹配导致误匹配。建议增加负向过滤：当匹配目标包含'苯乙烯'时强制拒绝。",
                           "方案2：建立品种隔离别名表，确保'工业硅'、'多晶硅'等仅匹配至硅系指标，排除'苯乙烯'等化工品。",
                           "方案3：PDF模板中'工业硅样本工厂库存(SMM)'的(SMM)后缀可能被算法误解为品种标识。建议在PDF模板中移除数据源标注或改用标准格式。",
                           "中", "P0", "是", "否",
                           "优先方案2（别名映射）+ 方案1（黑名单补充）")

        if bl_id == "BL-021" and source == "PDF":
            return _mk_fix("A", "模糊匹配算法缺陷：工业硅供需平衡被错误匹配到黄金相关数据，BL-021修复版已排除'金'子串误匹配，但仍有残留匹配路径",
                           bl_id, "rule_optimize",
                           "方案1：BL-021已修复'金'→'黄金'，需继续排查残留匹配路径，增加'供需平衡'组合词的正向约束。",
                           "方案2：建立品种-指标白名单，'工业硅供需平衡'仅允许匹配至硅系供需指标。",
                           "方案3：PDF模板'工业硅供需平衡'名称清晰，无需修改。",
                           "低", "P0", "是", "否",
                           "方案1（黑名单已修复）+ 方案2（别名映射补充）")

        if bl_id == "BL-022":
            # 镍 vs 铜跨品种
            return _mk_fix("A", "模糊匹配算法缺陷：镍系指标被错误匹配到铜系数据。'镍'与'铜'在TC（加工费）、持仓、库存等通用金融指标术语上高度相似，算法未有效区分品种前缀",
                           bl_id, "rule_optimize",
                           "方案1：BL-022已覆盖，但需加强匹配算法中的品种前置过滤——当检测到'镍'/'铜'等品种关键词时，强制约束匹配目标品种一致。",
                           "方案2：建立金属品种别名映射表，将'镍精矿TC'、'COMEX镍持仓'等明确映射至镍系指标池，排除铜系匹配。",
                           "方案3：PDF模板'中国电解镍净进口量'名称清晰；THS模板如'COMEX镍持仓量（手）'也明确标注品种。建议无需修改。",
                           "中", "P0", "是", "否",
                           "优先方案2（别名映射）+ 方案1（黑名单加强）")

        if bl_id == "BL-018":
            # 跨品种通用规则：锡↔镍、锡→钢铁等
            return _mk_fix("A", "模糊匹配算法缺陷：锡系指标被错误匹配到镍/钢铁等其他品种数据。通用金融术语（库存、产量、仓单）在多种金属间高度重叠，算法未正确约束品种边界",
                           bl_id, "rule_optimize",
                           "方案1：BL-018是通用跨品种禁止规则，需扩展为品种对级规则（如BL-018a锡↔镍、BL-018b锡↔钢铁），或在匹配算法层增加品种隔离门。",
                           "方案2：建立'锡-库存'、'锡-产量'等指标→品种的强绑定映射表，限制匹配仅在锡系指标池内进行。",
                           "方案3：THS模板如'LME锡库存（吨）'名称清晰，无需修改。",
                           "高", "P0", "是", "否",
                           "优先方案2（别名映射）+ 方案1（黑名单扩展）")

        if bl_id == "BL-019":
            # 硅 vs 铜
            return _mk_fix("A", "模糊匹配算法缺陷：硅矿加工费TC被匹配到铜管加工费。'加工费'和'TC'是跨金属通用术语，算法未区分金属品种",
                           bl_id, "rule_optimize",
                           "方案1：BL-019已覆盖，但需增加'加工费'+'TC'的组合品种约束——当出现'加工费'术语时，必须品种一致。",
                           "方案2：建立'硅-加工费'、'铜-加工费'等品种+术语组合的强绑定映射表。",
                           "方案3：THS模板'国内硅矿月加工费TC（元/吨）'名称清晰，无需修改。",
                           "中", "P0", "是", "否",
                           "优先方案2（别名映射）+ 方案1（黑名单补充）")

        # Fallback for any other cross-variety rule
        return _mk_fix("A", "模糊匹配算法缺陷：跨品种匹配错误",
                       bl_id, "rule_optimize",
                       "方案1：扩展黑名单规则，增加更多品种对的禁止匹配。",
                       "方案2：建立品种隔离别名映射表。",
                       "方案3：检查源文档品种标注是否清晰。",
                       "中", "P0", "是", "否",
                       "优先方案2（别名映射）")

    # ---- BL-005: 场内库存 vs 非仓单库存 ----
    if bl_id == "BL-005":
        return _mk_fix("A", "模糊匹配算法缺陷：'场内库存'（注册仓单/期货库存）被错误匹配到'非仓单库存'（现货库存）。二者虽同为库存概念但统计口径完全互斥",
                       bl_id, "rule_optimize",
                       "方案1：BL-005已覆盖，需检查匹配算法是否因'库存'子串匹配导致误匹配。增加'场内'/'非仓单'的显式区分。",
                       "方案2：建立'场内库存'、'非仓单库存'的明确别名映射，区分LME主要仓库场内库存与非仓单库存。",
                       "方案3：PDF模板'LME主要仓库场内库存'名称清晰，无需修改。",
                       "低", "P0", "是", "否",
                       "方案1（黑名单已覆盖）+ 方案2（别名映射确认）")

    # ---- BL-009: 利润 vs 需求 ----
    if bl_id == "BL-009":
        return _mk_fix("A", "模糊匹配算法缺陷：'需求'（三元523需求）被匹配到'利润'（碳酸锂现金生产利润）。二者虽同属碳酸锂产业链，但经济含义完全不同",
                       bl_id, "rule_optimize",
                       "方案1：BL-009已覆盖，需检查匹配算法是否因'碳酸锂'前缀匹配导致误匹配。增加'需求'/'利润'的显式区分。",
                       "方案2：建立'碳酸锂需求'、'碳酸锂利润'的明确别名映射，限制匹配仅在语义一致范围内。",
                       "方案3：PDF模板'碳酸锂 三元523需求'名称清晰，无需修改。",
                       "低", "P0", "是", "否",
                       "方案1（黑名单已覆盖）+ 方案2（别名映射确认）")

    # ---- BL-002/BL-003: 产量 vs 销量 ----
    if bl_id in ("BL-002", "BL-003"):
        return _mk_fix("A", "模糊匹配算法缺陷：'产量'（production）与'销量'（sales volume）被错误匹配。二者虽同属供需指标但统计口径不同（生产端 vs 销售端）",
                       bl_id, "rule_optimize",
                       "方案1：BL-002/BL-003已覆盖，需检查匹配算法是否因品种/品类前缀（如'新能源乘用车'、'其他电池'）匹配导致误匹配。",
                       "方案2：建立'新能源乘用车产量'、'其他电池销量'等品类+口径的明确别名映射。",
                       "方案3：PDF模板'新能源乘用车 产量'、'其他电池(磷酸铁锂) 销量'名称清晰，无需修改。",
                       "低", "P0", "是", "否",
                       "方案1（黑名单已覆盖）+ 方案2（别名映射确认）")

    # ---- BL-015: 国内销量 vs 出口 ----
    if bl_id == "BL-015":
        return _mk_fix("C", "上游数据源问题：PDF模板'磷酸铁锂 电池 国内销量'被BL-015（国内销量与出口互斥）触发，但matched_name为空。推测PDF模板原始周报可能在同一图表/章节中同时提及'国内销量'与'出口'，导致算法无法判断该指标究竟属于哪一口径",
                       bl_id, "source_fix",
                       "方案1：黑名单BL-015已覆盖，但根因在于PDF模板的内容描述模糊。无法仅通过黑名单规则解决。",
                       "方案2：对'磷酸铁锂 电池 国内销量'建立人工别名映射，明确该指标仅对应国内销量数据源。",
                       "方案3：建议PDF周报上游修改：将'磷酸铁锂 电池 国内销量'模板明确标注为'国内销量'口径，避免与出口数据混用。",
                       "高", "P0", "否", "是",
                       "方案3（上游修正）优先，方案2（别名映射）兜底")

    # ---- BL-025: 消费量 vs 产量 ----
    if bl_id == "BL-025":
        return _mk_fix("A", "模糊匹配算法缺陷：'消费量'（consumption）被错误匹配到'产量'（production）。'锡表观消费量'匹配到'镀锌板卷产量'——完全属于不同品种且口径相反",
                       bl_id, "rule_optimize",
                       "方案1：BL-025已覆盖，需检查匹配算法是否因'表观'、'消费'等模糊词匹配导致误匹配。",
                       "方案2：建立'锡表观消费量'、'锌锭消费量'等品种的明确别名映射，限制匹配仅在消费类指标内。",
                       "方案3：THS模板'锡表观消费量（万吨）'、'国内锌锭消费量（万吨）'名称清晰，无需修改。",
                       "中", "P0", "是", "否",
                       "优先方案2（别名映射）+ 方案1（黑名单加强）")

    # ---- BL-012: 库存天数 vs 库存量 ----
    if bl_id == "BL-012":
        # Determine if this is a false positive (both sides are "库存天数")
        # or a genuine cross-variety match
        is_same_metric = False
        if "库存天数" in indicator and "库存天数" in matched:
            is_same_metric = True

        # Check if cross-variety
        template_variety = variety
        # Infer matched variety from matched name
        matched_variety = "LI"  # default for 碳酸锂工厂库存天数
        if "锡" in matched or "锡锭" in matched:
            matched_variety = "SN"
        if "锂" in matched or "碳酸锂" in matched:
            matched_variety = "LI"

        is_cross_variety = (template_variety != matched_variety)

        if is_cross_variety:
            return _mk_fix("A", "模糊匹配算法缺陷：库存天数指标跨品种匹配。模板品种为{tv}但匹配到{mv}系的库存天数指标，'库存天数'作为通用术语在多种金属间高度重叠，算法未约束品种边界".format(tv=template_variety, mv=matched_variety),
                           bl_id, "rule_optimize",
                           "方案1：BL-012（库存天数与库存量互斥）为P1警告，但跨品种库存天数匹配应升级为P0。建议增加品种级黑名单规则（如BL-026：镍库存天数↔锂库存天数禁止）。",
                           "方案2：建立品种-库存天数指标的强绑定映射表，确保'电解镍厂库存天数'仅匹配至镍系库存天数指标。",
                           "方案3：THS模板如'电解镍厂库存天数（天）'名称清晰，无需修改。",
                           "中", "P1", "是", "否",
                           "优先方案2（别名映射）+ 方案1（黑名单扩展）")
        elif is_same_metric:
            return _mk_fix("B", "行业术语歧义：'库存天数'（days of inventory）与'库存量'（inventory volume）在有色金属行业常被混用。BL-012规则设计过于宽泛——当模板指标和匹配指标都是'库存天数'时仍触发互斥警告，属于规则误报（类似BL-021修复前的误报问题）",
                           bl_id, "rule_optimize",
                           "方案1：修复BL-012规则——当left和right同时包含'库存天数'时不应触发互斥（与BL-021修复思路一致）。建议修改right_patterns排除'库存天数'。",
                           "方案2：建立'库存天数'指标的同义映射表，将'碳酸锂工厂库存天数'、'厂内库存天数'等归为同一语义类。",
                           "方案3：THS模板如'库存天数（天）'名称清晰，无需修改。",
                           "低", "P1", "是", "否",
                           "方案1（黑名单规则修复）")
        else:
            # Same variety but different metric (库存天数 vs 库存量)
            return _mk_fix("B", "行业术语歧义：'库存天数'（衍生指标，表示库存可持续天数）与'库存量'（绝对值指标，表示库存吨数）在有色金属行业常被混用。BL-012规则正确标记了此冲突，但术语歧义是根本原因",
                           bl_id, "rule_optimize",
                           "方案1：BL-012规则正确，但需进一步区分'库存天数'与'库存量'的语义边界。建议增加子规则：当left含'库存天数'且right含'库存'（不含'天数'）时触发。",
                           "方案2：建立'库存天数'、'库存量'的明确语义区分表，并在匹配算法中加入语义类型约束。",
                           "方案3：THS模板如'社会库存天数（天）'、'在途库存天数（天）'名称清晰，无需修改。",
                           "低", "P1", "是", "否",
                           "方案1（黑名单规则细化）+ 方案2（别名映射）")

    # ---- BL-016: 利润 vs 产量 ----
    if bl_id == "BL-016":
        return _mk_fix("A", "模糊匹配算法缺陷：'利润'（profit）与'产量'（production）被错误匹配。'盐湖提锂利润'匹配到'盐湖提锂产量'——共享长前缀'盐湖提锂'但核心指标不同（盈利能力 vs 生产规模）",
                       bl_id, "rule_optimize",
                       "方案1：BL-016（利润与产量互斥）为P1警告，规则本身正确。需优化匹配算法：当匹配到同一品类下的不同口径指标时，应检查核心指标词（利润 vs 产量）是否一致。",
                       "方案2：建立'盐湖提锂利润'、'工业级碳酸锂利润'、'电池级碳酸锂利润'等明确别名映射，限制匹配仅在利润类指标内。",
                       "方案3：THS模板如'盐湖提锂利润（元/吨）'名称清晰，无需修改。",
                       "中", "P1", "是", "否",
                       "优先方案2（别名映射）+ 方案1（黑名单加强）")

    # ---- Fallback ----
    return _mk_fix("A", "模糊匹配算法缺陷", bl_id, "rule_optimize",
                   "方案1：优化黑名单规则。",
                   "方案2：建立别名映射表。",
                   "方案3：检查源文档。",
                   "中", "P0", "是", "否",
                   "方案2（别名映射）")


def _mk_fix(category, explanation, bl_id, primary_fix, fix1, fix2, fix3,
            cost, priority, can_automate, requires_manual, recommended):
    """Create a fix recommendation dict."""
    return {
        "root_cause_category": category,
        "root_cause_explanation": explanation,
        "fix_option_1": fix1,
        "fix_option_2": fix2,
        "fix_option_3": fix3,
        "primary_fix": primary_fix,
        "fix_cost": cost,
        "fix_priority": priority,
        "can_automate": can_automate,
        "requires_manual": requires_manual,
        "recommended_fix": recommended,
    }


# ============================================================
# Classify all 41 entries
# ============================================================
classified = []
for row in unique_rows:
    fix = classify_root_cause(row)
    entry = {
        "id": row["id"],
        "source": row["source"],
        "template_id": row["template_id"],
        "variety": row["variety"],
        "indicator_name": row["indicator_name"],
        "indicator_title": row["indicator_title"],
        "risk_level": row["risk_level"],
        "risk_category": row["risk_category"],
        "conflict_type": row["conflict_type"],
        "conflict_reason": row["conflict_reason"],
        "blacklist_id": row["blacklist_id"],
        "blacklist_rule_name": row["blacklist_rule_name"],
        "matched_name": row["matched_name"],
        "verify_status": row["verify_status"],
        # Root cause classification
        "root_cause_category": fix["root_cause_category"],
        "root_cause_explanation": fix["root_cause_explanation"],
        # Fix recommendations
        "fix_option_1": fix["fix_option_1"],
        "fix_option_2": fix["fix_option_2"],
        "fix_option_3": fix["fix_option_3"],
        "primary_fix": fix["primary_fix"],
        "fix_cost": fix["fix_cost"],
        "fix_priority": fix["fix_priority"],
        "can_automate": fix["can_automate"],
        "requires_manual": fix["requires_manual"],
        "recommended_fix": fix["recommended_fix"],
    }
    classified.append(entry)

# ============================================================
# Write risk_rootcause_detail.csv
# ============================================================
csv_path = os.path.join(OUT_DIR, "risk_rootcause_detail.csv")
fieldnames = [
    "id", "source", "template_id", "variety", "indicator_name", "indicator_title",
    "risk_level", "risk_category", "conflict_type", "conflict_reason",
    "blacklist_id", "blacklist_rule_name", "matched_name", "verify_status",
    "root_cause_category", "root_cause_explanation",
    "fix_option_1", "fix_option_2", "fix_option_3",
    "primary_fix", "fix_cost", "fix_priority", "can_automate",
    "requires_manual", "recommended_fix",
]
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(classified)
print(f"Written: {csv_path} ({len(classified)} rows)")

# ============================================================
# Statistics for summary report
# ============================================================
category_counts = Counter(e["root_cause_category"] for e in classified)
risk_level_counts = Counter(e["risk_level"] for e in classified)
variety_counts = Counter(e["variety"] for e in classified)
blacklist_counts = Counter(e["blacklist_id"] for e in classified)

# Cross-variety analysis
cross_variety_p0 = [e for e in classified if e["risk_level"] == "P0" and "跨品种" in e["conflict_type"]]
definition_errors = [e for e in classified if "口径" in e["conflict_reason"] or "互斥" in e["conflict_reason"]]

# Most error-prone varieties
variety_error_count = Counter()
for e in classified:
    variety_error_count[e["variety"]] += 1

# Most error-prone indicators (by indicator name prefix)
indicator_prefix_count = Counter()
for e in classified:
    # Extract the core indicator type (remove variety prefix and trailing details)
    name = e["indicator_name"]
    # Remove common prefixes
    for prefix in ["LME", "COMEX", "SMM", "Mysteel", "国内", "印尼", "菲律宾"]:
        name = name.replace(prefix, "").strip()
    indicator_prefix_count[name[:10]] += 1

# Cost analysis
cost_counts = Counter(e["fix_cost"] for e in classified)
priority_counts = Counter(e["fix_priority"] for e in classified)
automatable = sum(1 for e in classified if e["can_automate"] == "是")
manual_only = sum(1 for e in classified if e["requires_manual"] == "是")

# P0 breakdown
p0_entries = [e for e in classified if e["risk_level"] == "P0"]
p0_cross = [e for e in p0_entries if "跨品种" in e["conflict_type"]]
p0_definition = [e for e in p0_entries if "口径" in e["conflict_reason"] or "互斥" in e["conflict_reason"]]

# P1 breakdown
p1_entries = [e for e in classified if e["risk_level"] == "P1"]
p1_bl012 = [e for e in p1_entries if e["blacklist_id"] == "BL-012"]
p1_bl016 = [e for e in p1_entries if e["blacklist_id"] == "BL-016"]

print(f"Classification stats: {dict(category_counts)}")
print(f"Risk levels: {dict(risk_level_counts)}")
print(f"Varieties: {dict(variety_counts)}")

# ============================================================
# Write risk_rootcause_summary.md
# ============================================================
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

summary_md = f"""# V85 指标风险根因分析汇总报告

**生成时间**: {now_str}
**任务**: DSH-B_V85_RISK_ROOTCAUSE_ANALYSIS_AND_REVIEW_DOC
**分析范围**: {len(unique_rows)} 条去重独立风险条目
**黑名单版本**: v85-bl021-fixed (25 rules)
**输出目录**: `analysis/e2e_output/v85/risk_rootcause_review/`

---

## 1. 根因分类总览

| 根因类别 | 数量 | 占比 | 说明 |
|----------|------|------|------|
| **A: 模型匹配算法缺陷** | {category_counts.get('A', 0)} | {category_counts.get('A', 0)/len(classified)*100:.1f}% | 模糊匹配错误、跨品种匹配、口径反向匹配 |
| **B: 指标命名歧义/术语不统一** | {category_counts.get('B', 0)} | {category_counts.get('B', 0)/len(classified)*100:.1f}% | 库存天数与库存量混用、行业术语不统一 |
| **C: 上游数据源问题** | {category_counts.get('C', 0)} | {category_counts.get('C', 0)/len(classified)*100:.1f}% | PDF模板文字描述模糊、简写不规范 |
| **合计** | {len(classified)} | 100.0% | — |

### 1.1 根因分布说明

**类别A（算法缺陷）** 占绝对多数（{category_counts.get('A', 0)}/{len(classified)}），主要原因是：
- 模糊匹配算法基于子串相似度，对'库存'、'产量'、'TC'等跨品种通用术语缺乏品种约束
- 匹配算法未实现语义级的品种隔离门（variety gate）
- 黑名单规则虽有25条，但覆盖面不足，仅拦截了最明显的冲突

**类别B（术语歧义）** 仅涉及BL-012（库存天数与库存量互斥）规则：
- '库存天数'（衍生指标）与'库存量'（绝对值）在有色金属行业常混用
- BL-012规则设计过于宽泛，导致同类型指标间误报（类似BL-021修复前的'金'子串问题）

**类别C（上游数据源）** 仅1例：
- TPL-LC-087'磷酸铁锂 电池 国内销量'——PDF周报模板可能在同一图表中混合了国内销量与出口数据

---

## 2. 风险等级 × 根因交叉分析

| 根因类别 | P0（阻塞） | P1（警告） | P0占比 |
|----------|-----------|-----------|--------|
| A: 算法缺陷 | {sum(1 for e in classified if e['root_cause_category']=='A' and e['risk_level']=='P0')} | {sum(1 for e in classified if e['root_cause_category']=='A' and e['risk_level']=='P1')} | {sum(1 for e in classified if e['root_cause_category']=='A' and e['risk_level']=='P0')}/{len(p0_entries)} ({sum(1 for e in classified if e['root_cause_category']=='A' and e['risk_level']=='P0')/len(p0_entries)*100:.1f}%) |
| B: 术语歧义 | {sum(1 for e in classified if e['root_cause_category']=='B' and e['risk_level']=='P0')} | {sum(1 for e in classified if e['root_cause_category']=='B' and e['risk_level']=='P1')} | — |
| C: 上游问题 | {sum(1 for e in classified if e['root_cause_category']=='C' and e['risk_level']=='P0')} | {sum(1 for e in classified if e['root_cause_category']=='C' and e['risk_level']=='P1')} | — |

---

## 3. 品种维度分析

### 3.1 品种风险分布

| 品种 | 独立风险数 | P0数 | P1数 | 占风险比例 | 主要根因 |
|------|-----------|------|------|-----------|----------|
"""

for variety in sorted(variety_counts.keys(), key=lambda v: -variety_counts[v]):
    var_entries = [e for e in classified if e["variety"] == variety]
    var_p0 = sum(1 for e in var_entries if e["risk_level"] == "P0")
    var_p1 = sum(1 for e in var_entries if e["risk_level"] == "P1")
    var_cats = Counter(e["root_cause_category"] for e in var_entries)
    main_cat = var_cats.most_common(1)[0][0]
    main_cat_label = {"A": "算法缺陷", "B": "术语歧义", "C": "上游问题"}[main_cat]
    summary_md += f"| {variety} | {len(var_entries)} | {var_p0} | {var_p1} | {len(var_entries)/len(classified)*100:.1f}% | {main_cat_label} ({var_cats.get(main_cat,0)}/{len(var_entries)}) |\n"

summary_md += f"""
### 3.2 品种错配热力分析

**最高风险品种 TOP 5**:

| 排名 | 品种 | 风险数 | 风险类型分布 | 说明 |
|------|------|--------|-------------|------|
"""

for i, (variety, count) in enumerate(variety_counts.most_common(5)):
    var_entries = [e for e in classified if e["variety"] == variety]
    var_bl = Counter(e["blacklist_id"] for e in var_entries)
    bl_str = ", ".join(f"{bl}({n})" for bl, n in var_bl.most_common())
    desc = {
        "SN": "锡品种——被错误匹配到镍系数据最多，涉及LME库存、印尼产量等",
        "NI": "镍品种——被错误匹配到铜系数据最多，涉及TC、持仓、库存等",
        "LI": "锂品种——库存天数指标被跨品种匹配最多，涉及BL-012误报",
        "SI": "硅品种——被错误匹配到铜/苯乙烯/黄金，涉及BL-019/020/021",
        "LC": "碳酸锂品种——口径互斥最多，涉及BL-002/003/009/015",
        "AL": "铝品种——仅1例，场内库存与非仓单库存互斥",
        "ZN": "锌品种——消费量与产量互斥 + 库存天数跨品种",
    }.get(variety, "")
    summary_md += f"| {i+1} | {variety} | {count} | {bl_str} | {desc} |\n"

summary_md += f"""
---

## 4. 黑名单规则维度分析

### 4.1 各规则触发统计

| 规则ID | 规则名称 | 严重度 | 触发次数 | 根因分布 | 主要问题 |
|--------|----------|--------|----------|----------|----------|
"""

for bl_id in sorted(blacklist_counts.keys(), key=lambda x: -blacklist_counts[x]):
    bl_entries = [e for e in classified if e["blacklist_id"] == bl_id]
    bl_rule = BL_RULES.get(bl_id, {})
    bl_count = blacklist_counts[bl_id]
    bl_name = bl_rule.get("name", "Unknown")
    bl_sev = bl_rule.get("severity", "?")
    bl_cats = Counter(e["root_cause_category"] for e in bl_entries)
    cats_str = "/".join(f"{c}:{n}" for c, n in sorted(bl_cats.items()))
    # Determine main problem
    main_problem = ""
    if bl_id in ("BL-018", "BL-019", "BL-020", "BL-021", "BL-022"):
        main_problem = "跨品种匹配——通用金融术语(库存/产量/TC)缺乏品种隔离"
    elif bl_id == "BL-012":
        main_problem = "库存天数与库存量互斥——规则过宽，同类型指标误报"
    elif bl_id == "BL-016":
        main_problem = "利润与产量互斥——共享长前缀但核心指标不同"
    elif bl_id in ("BL-002", "BL-003"):
        main_problem = "产量与销量互斥——品种品类前缀匹配导致口径混淆"
    elif bl_id == "BL-025":
        main_problem = "消费量与产量互斥——完全跨品种且口径相反"
    elif bl_id == "BL-005":
        main_problem = "场内库存与非仓单库存互斥——'LME库存'前缀匹配混淆"
    elif bl_id == "BL-009":
        main_problem = "利润与需求互斥——'碳酸锂'前缀匹配混淆"
    elif bl_id == "BL-015":
        main_problem = "国内销量与出口互斥——PDF模板内容描述模糊"
    summary_md += f"| {bl_id} | {bl_name} | {bl_sev} | {bl_count} | {cats_str} | {main_problem} |\n"

summary_md += f"""
### 4.2 规则有效性评估

| 评估维度 | 结果 |
|----------|------|
| 有效拦截P0冲突 | {len(p0_entries)} 条P0被黑名单成功拦截 |
| 有效拦截P1警告 | {len(p1_entries)} 条P1被黑名单成功标记 |
| 规则误报（False Positive） | BL-012存在同类型指标误报（{sum(1 for e in classified if e['root_cause_category']=='B')}条） |
| 规则覆盖缺口 | 跨品种匹配仅覆盖5对（锡↔镍、硅↔铜、硅↔苯乙烯、硅↔黄金、镍↔铜），未覆盖锡↔钢铁等 |
| 规则粒度不足 | BL-018为通用规则，缺乏品种对级细分（建议拆分为BL-018a/018b等） |

---

## 5. 修复成本与可行性分析

### 5.1 修复成本分布

| 成本等级 | 数量 | 占比 | 说明 |
|----------|------|------|------|
| 低 | {cost_counts.get('低', 0)} | {cost_counts.get('低', 0)/len(classified)*100:.1f}% | 黑名单已有覆盖，仅需验证/微调 |
| 中 | {cost_counts.get('中', 0)} | {cost_counts.get('中', 0)/len(classified)*100:.1f}% | 需扩展黑名单规则或建立别名映射表 |
| 高 | {cost_counts.get('高', 0)} | {cost_counts.get('高', 0)/len(classified)*100:.1f}% | 需上游文档修正，无法仅靠算法解决 |

### 5.2 自动化可行性

| 指标 | 数值 |
|------|------|
| 可自动化根治 | {automatable}/{len(classified)} ({automatable/len(classified)*100:.1f}%) |
| 必须人工兜底 | {manual_only}/{len(classified)} ({manual_only/len(classified)*100:.1f}%) |
| 推荐优先方案 | 别名映射（方案2）为主，黑名单补充（方案1）为辅 |

---

## 6. 品种×指标错配热点

### 6.1 最易错配的指标模式

| 指标模式 | 出现次数 | 典型冲突 | 建议 |
|----------|----------|----------|------|
"""

# Find common indicator patterns
indicator_patterns = Counter()
for e in classified:
    name = e["indicator_name"]
    # Extract pattern: first 10 chars or common prefix
    if "库存" in name:
        indicator_patterns["库存类指标"] += 1
    elif "产量" in name:
        indicator_patterns["产量类指标"] += 1
    elif "TC" in name or "加工费" in name:
        indicator_patterns["TC/加工费类指标"] += 1
    elif "持仓" in name:
        indicator_patterns["持仓类指标"] += 1
    elif "利润" in name:
        indicator_patterns["利润类指标"] += 1
    elif "消费量" in name or "销量" in name:
        indicator_patterns["消费量/销量类指标"] += 1
    elif "需求" in name:
        indicator_patterns["需求类指标"] += 1
    else:
        indicator_patterns["其他"] += 1

for pattern, count in indicator_patterns.most_common():
    pattern_entries = [e for e in classified if
        (pattern == "库存类指标" and "库存" in e["indicator_name"]) or
        (pattern == "产量类指标" and "产量" in e["indicator_name"]) or
        (pattern == "TC/加工费类指标" and ("TC" in e["indicator_name"] or "加工费" in e["indicator_name"])) or
        (pattern == "持仓类指标" and "持仓" in e["indicator_name"]) or
        (pattern == "利润类指标" and "利润" in e["indicator_name"]) or
        (pattern == "消费量/销量类指标" and ("消费量" in e["indicator_name"] or "销量" in e["indicator_name"])) or
        (pattern == "需求类指标" and "需求" in e["indicator_name"]) or
        (pattern == "其他")]
    conflicts = Counter(e["conflict_type"] for e in pattern_entries)
    conflict_str = ", ".join(f"{k}({v})" for k, v in conflicts.most_common())
    recommendation = {
        "库存类指标": "建立品种级库存指标别名映射表，区分场内/非仓单/社会库存",
        "产量类指标": "建立品类级产量指标别名映射表，区分产量/销量/消费量",
        "TC/加工费类指标": "建立金属品种+TC加工费的强绑定映射，禁止跨金属匹配",
        "持仓类指标": "建立交易所+品种的强绑定映射（COMEX镍≠COMEX铜）",
        "利润类指标": "建立品类级利润指标别名映射表，区分利润/产量/需求",
        "消费量/销量类指标": "建立品种级消费量指标别名映射表，区分消费量/产量/销量",
        "需求类指标": "建立品类级需求指标别名映射表，区分需求/利润",
        "其他": "逐条人工审核",
    }.get(pattern, "")
    summary_md += f"| {pattern} | {count} | {conflict_str} | {recommendation} |\n"

summary_md += f"""
---

## 7. 关键发现与建议

### 7.1 关键发现

1. **算法缺陷是主要矛盾**：{category_counts.get('A', 0)}/{len(classified)}（{category_counts.get('A', 0)/len(classified)*100:.1f}%）的风险根因是模糊匹配算法缺陷，其中跨品种匹配占P0的{len(p0_cross)/len(p0_entries)*100:.1f}%
2. **跨品种匹配是最大风险类别**：21条P0冲突（占P0的{len(p0_cross)/len(p0_entries)*100:.1f}%）涉及跨品种匹配，主要是锡↔镍、镍↔铜、硅↔铜/苯乙烯/黄金
3. **库存天数规则需要修复**：BL-012存在{sum(1 for e in classified if e['root_cause_category']=='B')}条同类指标误报，需类似BL-021的修复方式
4. **术语歧义范围有限**：仅'库存天数/库存量'存在显著术语歧义，其他指标命名清晰
5. **上游数据源问题极少**：仅1例PDF模板内容模糊，占比{category_counts.get('C', 0)/len(classified)*100:.1f}%

### 7.2 修复优先级排序

| 优先级 | 行动项 | 预期效果 | 涉及风险数 |
|--------|--------|----------|-----------|
| **P0-紧急** | 修复BL-012规则（排除'库存天数'自匹配） | 消除{sum(1 for e in classified if e['root_cause_category']=='B')}条误报 | {sum(1 for e in classified if e['root_cause_category']=='B')} |
| **P0-紧急** | 增加品种隔离门（variety gate）到匹配算法 | 消除21条跨品种P0冲突 | 21 |
| **P0-紧急** | 建立镍↔铜、锡↔镍等品种的别名映射表 | 消除跨品种匹配风险 | 21 |
| **P1-重要** | 扩展黑名单规则（新增BL-026~BL-030品种对规则） | 覆盖当前未覆盖的跨品种场景 | ~10 |
| **P1-重要** | 修复PDF TPL-LC-087模板（明确国内销量/出口口径） | 消除上游数据源模糊问题 | 1 |
| **P2-常规** | 建立全面的指标别名映射体系 | 系统性降低匹配错误率 | 全部41条 |
| **P2-常规** | 优化匹配算法的语义级过滤能力 | 从根源解决模糊匹配问题 | 全部41条 |

---

## 8. 统计汇总

| 指标 | 数值 |
|------|------|
| 总独立风险条目 | {len(classified)} |
| 类别A（算法缺陷） | {category_counts.get('A', 0)} ({category_counts.get('A', 0)/len(classified)*100:.1f}%) |
| 类别B（术语歧义） | {category_counts.get('B', 0)} ({category_counts.get('B', 0)/len(classified)*100:.1f}%) |
| 类别C（上游问题） | {category_counts.get('C', 0)} ({category_counts.get('C', 0)/len(classified)*100:.1f}%) |
| P0阻塞项 | {len(p0_entries)} |
| P1警告项 | {len(p1_entries)} |
| 跨品种P0 | {len(p0_cross)} ({len(p0_cross)/len(p0_entries)*100:.1f}% of P0) |
| 口径互斥P0 | {len(p0_definition)} ({len(p0_definition)/len(p0_entries)*100:.1f}% of P0) |
| 可自动化根治 | {automatable} ({automatable/len(classified)*100:.1f}%) |
| 必须人工兜底 | {manual_only} ({manual_only/len(classified)*100:.1f}%) |
| 涉及品种数 | {len(variety_counts)} |
| 涉及规则数 | {len(blacklist_counts)} |

---

**约束声明**: NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true, NO_RULE_MODIFICATION=true, NO_ZHIJI_API_CALL=true
**生成工具**: build_rootcause_analysis.py
**输出文件**: risk_rootcause_detail.csv, risk_rootcause_summary.md, risk_treatment_plan.md, v85_review_presentation.md
"""

summary_path = os.path.join(OUT_DIR, "risk_rootcause_summary.md")
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary_md)
print(f"Written: {summary_path} ({len(summary_md)} chars)")

# ============================================================
# Write risk_treatment_plan.md
# ============================================================

# Categorize P0 entries by treatment approach
p0_must_fix = []
p0_manual_whitelist = []
p0_automatable = []

for e in p0_entries:
    if e["can_automate"] == "是":
        p0_automatable.append(e)
    if e["requires_manual"] == "是":
        p0_manual_whitelist.append(e)

# For "must fix before release" vs "can release with manual whitelist"
# P0 entries that are algorithm flaws (A) can potentially be fixed via blacklist/alias → must fix
# P0 entries that are upstream issues (C) require manual intervention → can release with manual whitelist

treatment_md = f"""# V85 风险处置 & 上线放行方案

**生成时间**: {now_str}
**任务**: DSH-B_V85_RISK_ROOTCAUSE_ANALYSIS_AND_REVIEW_DOC
**分析范围**: {len(unique_rows)} 条去重独立风险条目（P0: {len(p0_entries)}, P1: {len(p1_entries)}）
**黑名单版本**: v85-bl021-fixed (25 rules)

---

## 1. 处置总则

### 1.1 上线阻塞策略

| 风险等级 | 处置策略 | 上线条件 |
|----------|----------|----------|
| **P0（阻塞）** | 必须修复或人工白名单放行后上线 | 所有P0冲突条目必须有明确处置方案 |
| **P1（警告）** | 上线后人工抽检，不阻塞上线 | 抽检比例≥10%，重点关注模板范围 |
| **P2（提示）** | 不阻塞上线，记录备查 | — |

### 1.2 风险分类处置路径

```
风险条目 → 根因分析 → 分类处置
                      ├── 类别A（算法缺陷）→ 黑名单修复/别名映射 → 自动化验证 → 放行
                      ├── 类别B（术语歧义）→ 规则修复/别名映射 → 自动化验证 → 放行
                      └── 类别C（上游问题）→ 人工白名单放行 → 标注风险 → 后续上游修正
```

---

## 2. P0阻塞项处置方案

### 2.1 P0阻塞项总览

| 指标 | 数值 |
|------|------|
| P0阻塞项总数 | {len(p0_entries)} |
| 可自动化修复 | {sum(1 for e in p0_entries if e['can_automate']=='是')} |
| 必须人工兜底 | {sum(1 for e in p0_entries if e['requires_manual']=='是')} |
| 可临时白名单放行 | {sum(1 for e in p0_entries if e['requires_manual']=='是')} |

### 2.2 必须修复后才能上线的P0项（{sum(1 for e in p0_entries if e['can_automate']=='是')}项）

以下P0项可通过黑名单规则优化或别名映射表自动化解决，建议在上线前完成修复：

#### 2.2.1 跨品种匹配类（{len(p0_cross)}项）

| # | 风险ID | 品种 | 指标名称 | 黑名单规则 | 修复方案 | 修复成本 |
|---|--------|------|----------|-----------|----------|----------|
"""

idx = 0
for e in sorted(p0_cross, key=lambda x: (x["variety"], x["blacklist_id"])):
    idx += 1
    treatment_md += f"| {idx} | {e['id']} | {e['variety']} | {e['indicator_name']} | {e['blacklist_id']} | {e['recommended_fix'][:60]}... | {e['fix_cost']} |\n"

treatment_md += f"""
**修复建议**:
- **方案1（黑名单扩充）**: 为每条跨品种冲突增加黑名单规则（当前已有BL-018~BL-022，需扩展至覆盖锡↔钢铁、锌↔锡等）
- **方案2（别名映射表）**: 建立品种级指标别名映射表，将'镍-库存'、'锡-库存'等指标绑定至对应品种池
- **推荐**: 方案2优先（一劳永逸），方案1作为补充

#### 2.2.2 口径互斥类（{len(p0_definition)}项）

| # | 风险ID | 品种 | 指标名称 | 黑名单规则 | 修复方案 | 修复成本 |
|---|--------|------|----------|-----------|----------|----------|
"""

idx = 0
for e in sorted(p0_definition, key=lambda x: (x["variety"], x["blacklist_id"])):
    idx += 1
    treatment_md += f"| {idx} | {e['id']} | {e['variety']} | {e['indicator_name']} | {e['blacklist_id']} | {e['recommended_fix'][:60]}... | {e['fix_cost']} |\n"

treatment_md += f"""
**修复建议**:
- BL-002/BL-003（产量↔销量）：黑名单已覆盖，需验证匹配算法是否已正确执行
- BL-005（场内↔非仓单）：黑名单已覆盖，需验证
- BL-009（利润↔需求）：黑名单已覆盖，需验证
- BL-025（消费量↔产量）：黑名单已覆盖，需验证

### 2.3 可临时人工白名单放行并标注风险上线的P0项（{sum(1 for e in p0_entries if e['requires_manual']=='是')}项）

以下P0项因根因为上游数据源问题，无法仅靠算法修复，建议人工白名单放行后标注风险上线：

| # | 风险ID | 模板ID | 品种 | 指标名称 | 黑名单规则 | 放行条件 | 后续行动 |
|---|--------|--------|------|----------|-----------|----------|----------|
"""

idx = 0
for e in p0_manual_whitelist:
    idx += 1
    treatment_md += f"| {idx} | {e['id']} | {e['template_id']} | {e['variety']} | {e['indicator_name']} | {e['blacklist_id']} | 人工确认该模板当前匹配正确 | {e['recommended_fix'][:60]}... |\n"

treatment_md += f"""
---

## 3. P1高风险项处置方案

### 3.1 P1警告项总览

| 指标 | 数值 |
|------|------|
| P1警告项总数 | {len(p1_entries)} |
| BL-012（库存天数） | {len(p1_bl012)} |
| BL-016（利润产量） | {len(p1_bl016)} |
| 可自动化修复 | {sum(1 for e in p1_entries if e['can_automate']=='是')} |

### 3.2 上线后人工抽检策略

#### 3.2.1 抽检比例

| 品种 | P1条目数 | 抽检比例 | 抽检条目数 | 抽检重点 |
|------|----------|----------|-----------|----------|
| LI（碳酸锂） | {sum(1 for e in p1_entries if e['variety']=='LI')} | 50% | {max(1, sum(1 for e in p1_entries if e['variety']=='LI')//2)} | 利润指标匹配准确性、库存天数匹配 |
| NI（镍） | {sum(1 for e in p1_entries if e['variety']=='NI')} | 33% | {max(1, sum(1 for e in p1_entries if e['variety']=='NI')//3)} | 库存天数跨品种匹配 |
| SI（硅） | {sum(1 for e in p1_entries if e['variety']=='SI')} | 33% | {max(1, sum(1 for e in p1_entries if e['variety']=='SI')//3)} | 库存天数跨品种匹配 |
| SN（锡） | {sum(1 for e in p1_entries if e['variety']=='SN')} | 25% | {max(1, sum(1 for e in p1_entries if e['variety']=='SN')//4)} | 库存天数跨品种匹配 |
| ZN（锌） | {sum(1 for e in p1_entries if e['variety']=='ZN')} | 100% | {sum(1 for e in p1_entries if e['variety']=='ZN')} | 库存天数匹配（仅1项） |
| **合计** | **{len(p1_entries)}** | **—** | **{sum(1 for e in p1_entries if e['variety']=='LI')//2 + sum(1 for e in p1_entries if e['variety']=='NI')//3 + sum(1 for e in p1_entries if e['variety']=='SI')//3 + sum(1 for e in p1_entries if e['variety']=='SN')//4 + sum(1 for e in p1_entries if e['variety']=='ZN')}** | **—** |

#### 3.2.2 抽检模板范围

| 抽检范围 | 模板ID | 涉及风险 | 抽检内容 |
|----------|--------|----------|----------|
"""

# Group P1 entries by template
p1_templates = defaultdict(list)
for e in p1_entries:
    p1_templates[e["template_id"]].append(e)

for tpl_id in sorted(p1_templates.keys()):
    entries = p1_templates[tpl_id]
    bl_str = ", ".join(set(e["blacklist_id"] for e in entries))
    indicators = ", ".join(set(e["indicator_name"] for e in entries))
    treatment_md += f"| {tpl_id} | {tpl_id} | {bl_str} | {indicators[:80]} |\n"

treatment_md += f"""
#### 3.2.3 抽检标准

| 检查项 | 标准 | 不合格处理 |
|--------|------|-----------|
| 品种匹配正确性 | 指标品种与匹配目标品种一致 | 升级至P0，阻塞上线 |
| 口径匹配正确性 | 指标口径与匹配目标口径一致 | 升级至P0，阻塞上线 |
| 术语匹配正确性 | 指标名称与匹配目标名称语义一致 | 标记为B类，人工复核 |

---

## 4. 上线放行清单

### 4.1 上线前必须完成的修复项

| # | 修复项 | 涉及风险数 | 修复方案 | 修复成本 | 预计工时 |
|---|--------|-----------|----------|----------|----------|
| 1 | 修复BL-012规则（排除库存天数自匹配） | {sum(1 for e in classified if e['root_cause_category']=='B')} | 修改BL-012的right_patterns，排除'库存天数' | 低 | 0.5h |
| 2 | 建立镍↔铜品种别名映射表 | ~9 | 创建alias_mapping.json，绑定镍/铜系指标 | 中 | 2h |
| 3 | 建立锡↔镍品种别名映射表 | ~7 | 创建alias_mapping.json，绑定锡/镍系指标 | 中 | 2h |
| 4 | 建立硅↔铜/苯乙烯/黄金品种别名映射表 | ~5 | 创建alias_mapping.json，绑定硅系指标 | 中 | 2h |
| 5 | 验证现有黑名单规则的拦截效果 | 13 | 回放测试，确认所有P0冲突被正确拦截 | 低 | 1h |
| 6 | 人工审核TPL-LC-087模板 | 1 | 人工确认国内销量/出口口径 | 低 | 0.5h |
| **合计** | **—** | **{len(p0_entries)}** | **—** | **—** | **~8h** |

### 4.2 可带风险上线的条目

| 风险类别 | 条目数 | 放行条件 | 风险标注方式 |
|----------|--------|----------|-------------|
| P1警告项 | {len(p1_entries)} | 上线后1个月内完成抽检 | 在模板元数据中标记`risk_level: P1` |
| P0人工白名单 | {sum(1 for e in p0_entries if e['requires_manual']=='是')} | 人工确认当前匹配正确 | 在模板元数据中标记`risk_level: P0_WAIVED` |

### 4.3 上线风险等级评估

| 评估维度 | 当前状态 | 修复后状态 | 风险等级 |
|----------|----------|-----------|----------|
| P0阻塞项 | {len(p0_entries)}项未修复 | {len(p0_entries)}项全部修复/放行 | 🔴 高 |
| P1警告项 | {len(p1_entries)}项未抽检 | 抽检完成率100% | 🟡 中 |
| 跨品种匹配风险 | 21项P0跨品种冲突 | 别名映射表覆盖 | 🟡 中 |
| 口径互斥风险 | 12项口径互斥冲突 | 黑名单验证通过 | 🟢 低 |
| **综合风险等级** | **—** | **—** | **🟡 中（修复后）** |

---

## 5. 处置时间表

| 阶段 | 时间 | 行动项 | 负责人 | 交付物 |
|------|------|--------|--------|--------|
| T+0 | 上线前 | 修复BL-012规则 | 算法团队 | BL-012规则修复PR |
| T+0 | 上线前 | 建立品种别名映射表 | 数据团队 | alias_mapping.json |
| T+0 | 上线前 | 验证黑名单拦截效果 | QA团队 | 回放测试报告 |
| T+0 | 上线前 | 人工审核TPL-LC-087 | 业务团队 | 审核确认邮件 |
| T+0 | 上线时 | P1条目带风险上线 | 发布团队 | 上线检查清单 |
| T+7 | 上线后1周 | P1条目抽检完成 | 数据团队 | 抽检报告 |
| T+30 | 上线后1个月 | V86黑名单规则扩展 | 算法团队 | BL-026~BL-030规则 |
| T+60 | 上线后2个月 | 匹配算法语义级优化 | 算法团队 | 算法优化PR |

---

**约束声明**: NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true, NO_RULE_MODIFICATION=true, NO_ZHIJI_API_CALL=true
**生成工具**: build_rootcause_analysis.py
**输出文件**: risk_treatment_plan.md
"""

treatment_path = os.path.join(OUT_DIR, "risk_treatment_plan.md")
with open(treatment_path, "w", encoding="utf-8") as f:
    f.write(treatment_md)
print(f"Written: {treatment_path} ({len(treatment_md)} chars)")

# ============================================================
# Write v85_review_presentation.md
# ============================================================

presentation_md = f"""# V85 指标匹配系统上线评审汇报

**汇报日期**: {now_str}
**任务**: DSH-B_V85_RISK_ROOTCAUSE_ANALYSIS_AND_REVIEW_DOC
**评审版本**: V85 (BL-021修复版, 25条黑名单规则)
**汇报人**: [待填写]
**评审对象**: V85指标匹配系统上线审批

---

## 第1页：项目总览

### 1.1 项目概况

| 项目 | 数据 |
|------|------|
| 项目目标 | 构建统一指标风险数据库，完成PDF与THS模板的语义匹配风险扫描 |
| PDF模板总量 | 314个（修订后FULL_OK） |
| THS模板总量 | 2354个（全量扫描） |
| 统一风险库条目 | {len(unique_rows)}条（去重后） |
| 黑名单规则 | 25条（BL-001~BL-025） |

### 1.2 风险总览

| 风险等级 | 数量 | 占比 | 处置状态 |
|----------|------|------|----------|
| P0（语义冲突阻塞） | {len(p0_entries)} | {len(p0_entries)/len(classified)*100:.1f}% | 需修复后上线 |
| P1（高风险警告） | {len(p1_entries)} | {len(p1_entries)/len(classified)*100:.1f}% | 上线后抽检 |
| P2（低风险提示） | 0 | 0% | — |

---

## 第2页：根因分析

### 2.1 根因分布

```
┌──────────────────────────────────────────────┐
│  根因分类                                      │
├──────────────────────────────────────────────┤
│  A: 算法缺陷    ████████████████████  {category_counts.get('A', 0)} ({category_counts.get('A', 0)/len(classified)*100:.1f}%)  │
│  B: 术语歧义    █  {category_counts.get('B', 0)} ({category_counts.get('B', 0)/len(classified)*100:.1f}%)                    │
│  C: 上游问题    ·  {category_counts.get('C', 0)} ({category_counts.get('C', 0)/len(classified)*100:.1f}%)                    │
└──────────────────────────────────────────────┘
```

### 2.2 根因说明

| 类别 | 数量 | 核心问题 | 修复路径 |
|------|------|----------|----------|
| A: 算法缺陷 | {category_counts.get('A', 0)} | 模糊匹配算法缺乏品种隔离，跨品种匹配21项 | 别名映射表 + 黑名单扩充 |
| B: 术语歧义 | {category_counts.get('B', 0)} | BL-012规则过宽，库存天数自匹配误报 | 规则修复（类似BL-021修复） |
| C: 上游问题 | {category_counts.get('C', 0)} | PDF模板内容描述模糊 | 人工白名单放行 |

### 2.3 关键发现

1. **算法缺陷占绝对多数**（{category_counts.get('A', 0)/len(classified)*100:.1f}%），核心是品种隔离不足
2. **跨品种匹配是最大风险**（21项P0，占P0的{len(p0_cross)/len(p0_entries)*100:.1f}%）
3. **BL-012规则需要修复**（{sum(1 for e in classified if e['root_cause_category']=='B')}项误报，类似BL-021修复前的'金'子串问题）
4. **上游数据源问题极少**（{category_counts.get('C', 0)}项，{category_counts.get('C', 0)/len(classified)*100:.1f}%）

---

## 第3页：风险案例节选

### 3.1 案例1：镍↔铜跨品种匹配（BL-022）

**模板**: THS-NI-3.1
**指标**: 印尼镍精矿TC（美元/吨干矿）
**匹配到**: 铜精矿：长单TC价（年）
**冲突类型**: 跨品种匹配（BL-022）
**根因**: 模糊匹配算法基于'TC'子串匹配，未区分镍/铜品种
**截图描述**: [图表显示印尼镍精矿TC走势，但实际匹配到铜精矿TC数据]

**冲突说明**:
- 'TC'（Treatment Charge）是矿冶行业通用术语，镍精矿和铜精矿都有TC
- 算法仅基于'TC'和'精矿'子串匹配，忽略了品种前缀'镍'vs'铜'
- 镍TC和铜TC的市场含义、价格水平完全不同

**建议方案**:
1. ✅ **方案2（别名映射表）**: 建立'镍精矿TC'→'镍系TC指标池'、'铜精矿TC'→'铜系TC指标池'的强绑定
2. 🔄 **方案1（黑名单扩充）**: BL-022已覆盖镍↔铜，需验证拦截效果

### 3.2 案例2：锡↔镍跨品种匹配（BL-018）

**模板**: THS-SN-3.1.2
**指标**: 印尼锡精矿产量（万吨）
**匹配到**: 印尼精炼镍产量
**冲突类型**: 跨品种匹配（BL-018）
**根因**: 模糊匹配算法基于'印尼...产量'模式匹配，未区分锡/镍品种
**截图描述**: [图表显示印尼锡精矿产量，但实际匹配到印尼精炼镍产量数据]

**冲突说明**:
- 印尼是全球重要的锡和镍生产国
- '印尼...产量'是通用模式，算法未能区分'锡精矿产量'vs'精炼镍产量'
- 锡精矿和精炼镍是完全不同的产品，产量数据不可混用

**建议方案**:
1. ✅ **方案2（别名映射表）**: 建立'锡-产量'→'锡系产量指标池'、'镍-产量'→'镍系产量指标池'的强绑定
2. 🔄 **方案1（黑名单扩充）**: BL-018为通用规则，需拆分为锡↔镍、锡↔钢铁等细分规则

### 3.3 案例3：口径互斥匹配（BL-003）

**模板**: TPL-LC-084
**指标**: 其他电池(磷酸铁锂) 销量
**匹配到**: SMM: 境内其他电池产量: 月度
**冲突类型**: 销量与产量互斥（BL-003）
**根因**: 模糊匹配算法基于'其他电池'品类前缀匹配，未区分销量/产量口径
**截图描述**: [图表显示其他电池销量走势，但实际匹配到其他电池产量数据]

**冲突说明**:
- '销量'（sales volume）和'产量'（production）是不同统计口径
- 产量是生产端数据，销量是销售端数据
- 两者趋势可能不同，混用会导致分析结论错误

**建议方案**:
1. 🔄 **方案1（黑名单）**: BL-003已覆盖，需验证拦截效果
2. ✅ **方案2（别名映射表）**: 建立'销量'→'销量类指标池'、'产量'→'产量类指标池'的强绑定

---

## 第4页：系统能力边界

### 4.1 当前能力

| 能力 | 状态 | 说明 |
|------|------|------|
| 子串相似度匹配 | ✅ 已实现 | 基于字符串相似度的模糊匹配 |
| 黑名单规则拦截 | ✅ 已实现 | 25条语义互斥黑名单规则 |
| 跨品种匹配拦截 | ⚠️ 部分覆盖 | 仅覆盖5对品种（锡↔镍、硅↔铜、硅↔苯乙烯、硅↔黄金、镍↔铜） |
| 口径互斥拦截 | ⚠️ 部分覆盖 | 覆盖产量↔销量、利润↔需求等，但部分规则过宽 |
| 品种隔离 | ❌ 未实现 | 无独立的品种隔离门（variety gate） |
| 语义级匹配 | ❌ 未实现 | 仅基于子串，无语义理解能力 |
| 人工别名映射 | ❌ 未实现 | 无指标→品种→口径的强绑定映射体系 |

### 4.2 已知局限

1. **品种隔离不足**：模糊匹配算法无法区分'镍库存'和'铜库存'等跨品种同义词
2. **规则粒度不足**：BL-018为通用跨品种规则，缺乏品种对级细分
3. **规则过宽导致误报**：BL-012（库存天数↔库存量）存在自匹配误报
4. **无正向白名单**：仅有黑名单（禁止匹配），缺乏白名单（允许匹配）机制
5. **语义理解缺失**：算法无法理解'库存天数'与'库存量'的语义差异

---

## 第5页：V86迭代路线图

### 5.1 V86规划概览

| 迭代阶段 | 时间 | 目标 | 预期效果 |
|----------|------|------|----------|
| V86-Alpha | 上线后1个月 | 黑名单规则扩展 | 新增10+条品种对规则，覆盖所有已知跨品种场景 |
| V86-Beta | 上线后2个月 | 别名映射体系 | 建立完整的指标→品种→口径强绑定映射表 |
| V86-RC1 | 上线后3个月 | 语义级匹配算法 | 引入语义理解能力，区分库存天数/库存量等语义相近术语 |
| V86-GA | 上线后4个月 | 正向白名单机制 | 建立允许的匹配规则，从禁止模式升级为白名单模式 |

### 5.2 V86关键改进项

#### 阶段1：黑名单规则扩展（V86-Alpha）

| 新增规则 | 规则内容 | 覆盖场景 | 优先级 |
|----------|----------|----------|--------|
| BL-026 | 锡↔钢铁跨品种禁止 | 锡消费量→钢铁产量 | P0 |
| BL-027 | 锌↔锡跨品种禁止 | 锌锭消费量→锡锭产量 | P0 |
| BL-028 | 镍库存天数↔锂库存天数禁止 | 跨品种库存天数匹配 | P1 |
| BL-029 | 硅库存天数↔锂库存天数禁止 | 跨品种库存天数匹配 | P1 |
| BL-030 | 锌库存天数↔锂库存天数禁止 | 跨品种库存天数匹配 | P1 |
| BL-012修复 | 排除库存天数自匹配 | 库存天数误报 | P0 |

#### 阶段2：别名映射体系（V86-Beta）

```json
{{
  "mapping_version": "v86-beta",
  "mappings": [
    {{
      "indicator_pattern": "镍.*库存",
      "allowed_variety": ["NI"],
      "forbidden_variety": ["CU", "SN", "LI", "SI", "ZN"],
      "metric_type": "inventory"
    }},
    {{
      "indicator_pattern": ".*TC|.*加工费",
      "allowed_variety": ["NI", "CU", "SN", "SI", "ZN", "AL"],
      "forbidden_variety": [],
      "metric_type": "processing_fee",
      "variety_required": true
    }}
  ]
}}
```

#### 阶段3：语义级匹配（V86-RC1）

| 改进项 | 当前状态 | V86目标 | 技术方案 |
|--------|----------|---------|----------|
| 品种隔离 | 无 | 100%覆盖 | 在匹配算法中增加品种前置门 |
| 语义类型识别 | 无 | 库存/产量/价格/利润等 | 基于关键词的语义类型分类器 |
| 规则粒度 | 5对品种 | 20+对品种 | 品种对级黑名单规则 |
| 白名单机制 | 无 | 正向白名单 | 从黑名单模式升级为白名单模式 |

### 5.3 V86预期效果

| 指标 | V85当前 | V86目标 | 提升 |
|------|---------|---------|------|
| 跨品种匹配拦截率 | 63.6%（21/33 P0） | 100% | +36.4% |
| 口径互斥拦截率 | 36.4%（12/33 P0） | 100% | +63.6% |
| 规则误报率 | {sum(1 for e in classified if e['root_cause_category']=='B')/len(classified)*100:.1f}%（{sum(1 for e in classified if e['root_cause_category']=='B')}/{len(classified)}） | <1% | 显著降低 |
| 别名映射覆盖率 | 0% | 100% | +100% |
| 白名单覆盖率 | 0% | 80%+ | +80% |

---

## 第6页：上线决策建议

### 6.1 上线条件检查清单

| 检查项 | 状态 | 备注 |
|--------|------|------|
| BL-012规则修复完成 | ⬜ 待完成 | 预计0.5h |
| 镍↔铜别名映射表就绪 | ⬜ 待完成 | 预计2h |
| 锡↔镍别名映射表就绪 | ⬜ 待完成 | 预计2h |
| 硅系别名映射表就绪 | ⬜ 待完成 | 预计2h |
| 黑名单回放测试通过 | ⬜ 待完成 | 预计1h |
| TPL-LC-087人工审核完成 | ⬜ 待完成 | 预计0.5h |
| P1抽检策略制定完成 | ✅ 已完成 | 见风险处置方案 |
| 上线回滚计划就绪 | ⬜ 待完成 | — |

### 6.2 上线风险评级

| 维度 | 当前风险 | 修复后风险 | 说明 |
|------|----------|-----------|------|
| P0阻塞项 | 🔴 高 | 🟢 低 | {len(p0_entries)}项P0修复后风险降至低 |
| P1抽检项 | 🟡 中 | 🟢 低 | {len(p1_entries)}项P1抽检后风险降至低 |
| 跨品种匹配 | 🔴 高 | 🟢 低 | 别名映射表覆盖 |
| 口径互匹配 | 🟡 中 | 🟢 低 | 黑名单验证通过 |
| **综合评级** | **🔴 高** | **🟢 低** | **修复后可安全上线** |

### 6.3 上线建议

**建议**: ✅ **有条件通过上线**

**条件**:
1. 完成BL-012规则修复（必须）
2. 完成3个品种别名映射表（必须）
3. 完成黑名单回放测试（必须）
4. 完成TPL-LC-087人工审核（建议）
5. 制定P1抽检计划并启动（建议）

**预计上线准备时间**: ~8小时

---

## 附录A：数据摘要

| 指标 | 数值 |
|------|------|
| PDF模板总量 | 314 |
| THS模板总量 | 2354 |
| 统一风险库条目 | {len(unique_rows)} |
| P0阻塞项 | {len(p0_entries)} |
| P1警告项 | {len(p1_entries)} |
| 类别A（算法缺陷） | {category_counts.get('A', 0)} |
| 类别B（术语歧义） | {category_counts.get('B', 0)} |
| 类别C（上游问题） | {category_counts.get('C', 0)} |
| 涉及品种 | {len(variety_counts)} |
| 涉及黑名单规则 | {len(blacklist_counts)} |
| 可自动化修复 | {automatable} |
| 必须人工兜底 | {manual_only} |

---

**约束声明**: NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true, NO_RULE_MODIFICATION=true, NO_ZHIJI_API_CALL=true
**生成工具**: build_rootcause_analysis.py
**输出文件**: v85_review_presentation.md
"""

presentation_path = os.path.join(OUT_DIR, "v85_review_presentation.md")
with open(presentation_path, "w", encoding="utf-8") as f:
    f.write(presentation_md)
print(f"Written: {presentation_path} ({len(presentation_md)} chars)")

# ============================================================
# Compute MD5 checksums
# ============================================================
print("\n=== MD5 Checksums ===")
output_files = [
    "risk_rootcause_detail.csv",
    "risk_rootcause_summary.md",
    "risk_treatment_plan.md",
    "v85_review_presentation.md",
]
md5_results = {}
for fname in output_files:
    fpath = os.path.join(OUT_DIR, fname)
    with open(fpath, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    md5_results[fname] = md5
    size = os.path.getsize(fpath)
    print(f"  {fname}: MD5={md5} Size={size}B")

# ============================================================
# Summary
# ============================================================
print("\n=== Classification Summary ===")
print(f"  Category A (Algorithm Flaw): {category_counts.get('A', 0)} ({category_counts.get('A', 0)/len(classified)*100:.1f}%)")
print(f"  Category B (Terminology Ambiguity): {category_counts.get('B', 0)} ({category_counts.get('B', 0)/len(classified)*100:.1f}%)")
print(f"  Category C (Upstream Data Quality): {category_counts.get('C', 0)} ({category_counts.get('C', 0)/len(classified)*100:.1f}%)")
print(f"  Total: {len(classified)}")
print(f"\n  P0 entries: {len(p0_entries)}")
print(f"  P1 entries: {len(p1_entries)}")
print(f"  Cross-variety P0: {len(p0_cross)}")
print(f"  Definition errors: {len(definition_errors)}")
print(f"  Automatable: {automatable}")
print(f"  Manual only: {manual_only}")
print(f"\nOutput directory: {OUT_DIR}")
print("Done.")
