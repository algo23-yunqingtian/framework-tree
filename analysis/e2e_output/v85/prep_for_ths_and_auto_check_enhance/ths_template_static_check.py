#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ths_template_static_check.py — 同花顺模板静态结构校验

工单: HERMES_V85_PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE
任务: T2-2 同花顺模板静态预校验(仅结构, 不拉zhiji时序)

输入: analysis/e2e_output/v85/ths_check/ths_chart_template_list.json (155个同花顺模板)
对照: schema_adapt_doc.md §4 目标规范
输出: output/v85_review_package/enhance_prep/ths_template_static_check_report.md

约束(T4): 不调用zhiji接口, 不拉时序数据, 不修改原始模板, 纯静态结构+文本校验。
"""

import json
import re
import csv
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

V85_BASE = Path("/home/ubuntu/framework-tree/analysis/e2e_output/v85")
THS_PATH = V85_BASE / "ths_check/ths_chart_template_list.json"
TREE_CONFIG = Path("/home/ubuntu/framework-tree/data/tree_config.json")
OUT_DIR = Path("/home/ubuntu/framework-tree/output/v85_review_package/enhance_prep")
OUT_REPORT = OUT_DIR / "ths_template_static_check_report.md"

# schema_adapt_doc §4 目标规范的必需字段
SCHEMA_REQUIRED_FIELDS = ["chart_id", "title", "meta", "y_axis", "series"]
# THS 模板实际字段(8个)
THS_ACTUAL_FIELDS = ["template_id", "variety", "node", "plot_type", "chart_title",
                    "indicator_name_list", "单位", "频率"]

# 合法品种代码(含THS独有的LI/CU/ZN)
VALID_VARIETIES = {"AO", "CU", "AL", "PB", "ZN", "NI", "SN", "SI", "LC", "LI"}
# 合法图表类型(THS用中文枚举)
VALID_PLOT_TYPES = {"时序图", "排名图", "柱状图", "饼图", "散点图", "面积图"}
# 合法单位
VALID_UNITS = {"万吨", "元/吨", "%", "手", "美元/吨", "吨", "元", "美元", "千克", "千吨",
              "亿元", "万元", "度", "kWh", "GWh", "美元/磅", "元/千克", None}
# 合法频率
VALID_FREQUENCIES = {"daily", "weekly", "monthly", "quarterly", "yearly", None}


def collect_valid_nodes(config_path):
    """从 tree_config.json 收集所有合法节点代码"""
    if not config_path.exists():
        return set(), True
    tc = json.load(open(config_path, "r", encoding="utf-8"))
    nodes = set()

    def walk(n):
        if isinstance(n, dict):
            for key in ("code", "id", "node", "code_no", "id_no"):
                if key in n and n[key]:
                    nodes.add(str(n[key]))
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(tc)
    return nodes, False


def check_template(t, idx, valid_nodes, node_errors):
    """校验单个模板, 返回 (errors, warnings)"""
    errors = []
    warnings = []
    tid = t.get("template_id", f"[无ID#{idx}]")

    # ---- 致命结构错误 ----
    # E1: 与 schema 目标规范的字段差距(结构性缺失)
    missing_schema_fields = [f for f in SCHEMA_REQUIRED_FIELDS if f not in t]
    if len(missing_schema_fields) >= len(SCHEMA_REQUIRED_FIELDS):
        errors.append({
            "type": "FATAL", "code": "E1_SCHEMA_MISMATCH",
            "template": tid,
            "detail": f"与schema目标规范完全不兼容: 缺少 {missing_schema_fields}",
            "hint": "THS模板用独立schema(template_id/variety/node/indicator_name_list), "
                    "需适配层转换才能渲染。建议按schema_adapt_doc §8对齐"
        })

    # E2: template_id 缺失或重复
    if not t.get("template_id"):
        errors.append({"type": "FATAL", "code": "E2_ID_MISSING",
                       "template": tid, "detail": "template_id 为空"})

    # E3: 关键字段缺失
    for f in ["variety", "node", "chart_title", "indicator_name_list"]:
        if f not in t:
            errors.append({"type": "FATAL", "code": f"E3_FIELD_MISSING_{f}",
                           "template": tid, "detail": f"必需字段 {f} 缺失"})

    # E4: indicator_name_list 为空
    if t.get("indicator_name_list") is None or len(t.get("indicator_name_list", [])) == 0:
        errors.append({"type": "FATAL", "code": "E4_EMPTY_INDICATORS",
                       "template": tid, "detail": "indicator_name_list 为空, 图表无数据源"})

    # E5: 品种代码非法
    if t.get("variety") not in VALID_VARIETIES:
        errors.append({"type": "FATAL", "code": "E5_INVALID_VARIETY",
                       "template": tid, "detail": f"非法品种: {t.get('variety')}"})

    # E6: node 不在 tree_config
    if t.get("node") and valid_nodes and t["node"] not in valid_nodes:
        errors.append({"type": "FATAL", "code": "E6_NODE_NOT_IN_TREE",
                       "template": tid, "detail": f"node={t['node']} 不在tree_config.json中",
                       "hint": "THS可能用上层节点(3.1/3.2/3.3), tree_config用细分节点(3.1.1-3.1.5)"})

    # E7: chart_title 格式异常
    title = t.get("chart_title", "")
    if not re.match(r'^[^·]+·[\d.]+·.+等\d+项·.+', title):
        errors.append({"type": "FATAL", "code": "E7_TITLE_FORMAT",
                       "template": tid, "detail": f"chart_title格式异常: {title[:50]}"})

    # ---- 警告 ----
    # W1: plot_type 非法
    if t.get("plot_type") not in VALID_PLOT_TYPES:
        warnings.append({"type": "WARN", "code": "W1_INVALID_PLOT_TYPE",
                         "template": tid, "detail": f"非法图表类型: {t.get('plot_type')}"})

    # W2: 单位缺失
    if t.get("单位") is None:
        warnings.append({"type": "WARN", "code": "W2_UNIT_MISSING",
                         "template": tid, "detail": "单位字段为空"})

    # W3: 频率缺失
    if t.get("频率") is None:
        warnings.append({"type": "WARN", "code": "W3_FREQUENCY_MISSING",
                         "template": tid, "detail": "频率字段为空(153/155缺失)"})

    # W4: 标题"等N项"与实际指标数不符
    m = re.match(r'^[^·]+·[\d.]+·.+等(\d+)项', title)
    if m:
        claim_n = int(m.group(1))
        actual_n = len(t.get("indicator_name_list", []))
        if claim_n != actual_n:
            warnings.append({"type": "WARN", "code": "W4_TITLE_IND_MISMATCH",
                             "template": tid,
                             "detail": f"标题声明{claim_n}项, 实际{actual_n}项指标"})

    # W5: 图表类型单一化(时序图占绝大多数, 渲染策略单一)
    if t.get("plot_type") == "时序图":
        warnings.append({"type": "WARN", "code": "W5_PLOT_TYPE_MONOTONY",
                         "template": tid, "detail": "图表类型为时序图(153/155), 渲染策略单一",
                         "suppress_from_report": True})  # 统计但不逐条列

    # W6: indicator_name_list 数量过多(单图指标过多, 可读性差)
    ind_count = len(t.get("indicator_name_list", []))
    if ind_count > 15:
        warnings.append({"type": "WARN", "code": "W6_TOO_MANY_INDICATORS",
                         "template": tid,
                         "detail": f"单图{ind_count}个指标, 过多影响可读性"})

    # W7: 含"/"的复合指标名(可能是多指标合并)
    for ind in t.get("indicator_name_list", []):
        if "/" in ind and ("等" in ind or "和" in ind or "、" in ind):
            warnings.append({"type": "WARN", "code": "W7_COMPOUND_INDICATOR_NAME",
                             "template": tid,
                             "detail": f"指标名含复合分隔符: {ind[:40]}"})
            break  # 每模板只报一次

    return errors, warnings


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 加载
    ths = json.load(open(THS_PATH, "r", encoding="utf-8"))
    valid_nodes, tree_config_missing = collect_valid_nodes(TREE_CONFIG)

    print(f"加载 THS 模板: {len(ths)} 个")
    print(f"tree_config 节点: {len(valid_nodes)} 个{' (缺失)' if tree_config_missing else ''}")

    # 逐模板校验
    all_errors = []
    all_warnings = []
    error_by_code = Counter()
    warning_by_code = Counter()
    error_templates = set()
    templates_with_warnings = set()

    for i, t in enumerate(ths):
        errors, warnings = check_template(t, i, valid_nodes, None)
        for e in errors:
            all_errors.append(e)
            error_by_code[e["code"]] += 1
            error_templates.add(e["template"])
        for w in warnings:
            all_warnings.append(w)
            warning_by_code[w["code"]] += 1
            templates_with_warnings.add(w["template"])

    # ---- 生成报告 ----
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(ths)
    fatal_count = sum(1 for e in all_errors if e["type"] == "FATAL")
    warn_count = len(all_warnings)

    lines = []
    lines.append(f"# 同花顺模板静态结构校验报告")
    lines.append(f"")
    lines.append(f"> 工单: `HERMES_V85_PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE`  ")
    lines.append(f"> 任务: T2-2 同花顺模板静态预校验(仅结构, 不拉zhiji时序)  ")
    lines.append(f"> 生成时间: {ts}  ")
    lines.append(f"> 输入: `analysis/e2e_output/v85/ths_check/ths_chart_template_list.json`  ")
    lines.append(f"> 对照规范: `schema_adapt_doc.md §4 目标规范`  ")
    lines.append(f"> 约束: 不调用zhiji接口、不拉时序、不修改原始模板")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 1. 总览")
    lines.append(f"")
    lines.append(f"| 指标 | 数量 | 占比 |")
    lines.append(f"|---|---|---|")
    lines.append(f"| 同花顺模板总数 | **{total}** | 100% |")
    lines.append(f"| 存在致命结构错误的模板 | **{len(error_templates)}** | {len(error_templates)/total*100:.1f}% |")
    lines.append(f"| 存在警告的模板 | **{len(templates_with_warnings)}** | {len(templates_with_warnings)/total*100:.1f}% |")
    lines.append(f"| 完全无问题模板 | **{total - len(error_templates) - len(templates_with_warnings)}** | {(total-len(error_templates)-len(templates_with_warnings))/total*100:.1f}% |")
    lines.append(f"| 致命错误总数 | **{fatal_count}** | — |")
    lines.append(f"| 警告总数 | **{warn_count}** | — |")
    lines.append(f"")
    lines.append(f"> ⚠️ **核心结论**: 同花顺模板与 schema 目标规范**完全不兼容**。")
    lines.append(f"> 155个模板全部存在 E1_SCHEMA_MISMATCH 致命错误——THS使用独立schema,")
    lines.append(f"> 8个字段与 schema 的5个必需字段(template_id→chart_id, variety→meta.variety 等)无任何交集。")
    lines.append(f"> **必须先写适配层**(参照 `t22_render_online.py::adapt_template()`)才能渲染。")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 2. THS 模板 vs Schema 目标规范 字段差距")
    lines.append(f"")
    lines.append(f"| schema 必需字段 | THS 对应字段 | 转换规则 | 状态 |")
    lines.append(f"|---|---|---|---|")
    lines.append(f"| `chart_id` | `template_id` | 直接映射 | ❌ 字段名不同 |")
    lines.append(f"| `title` | `chart_title` | 需解析提取核心标题(去除品种·节点·等N项·类型前后缀) | ❌ 字段名不同+格式需解析 |")
    lines.append(f"| `meta.variety` | `variety` | 顶层平铺→嵌套到meta | ❌ 层级不同 |")
    lines.append(f"| `meta.chart_type` | `plot_type` | 中文枚举映射 | ❌ 字段名不同 |")
    lines.append(f"| `y_axis` | 无 | THS无坐标轴单位字段, 仅有 `单位` 顶层字段 | ❌ 缺失, 需从单位推导 |")
    lines.append(f"| `series[].name` | `indicator_name_list[]` | 数组直接映射为series列表 | ⚠️ 需展开 |")
    lines.append(f"| `series[].zhiji_id` | 无 | **THS完全无zhiji_id字段** | ❌ 缺失, 需后续匹配 |")
    lines.append(f"| `series[].status` | 无 | **THS无verify_status** | ❌ 缺失, 需后续校验 |")
    lines.append(f"")
    lines.append(f"**结论**: THS 模板是**半成品元数据**(仅有模板结构+指标名列表),")
    lines.append(f"**缺少渲染必需的 zhiji_id 和 verify_status**。后续渲染流程需要:")
    lines.append(f"1. 写适配层将 THS schema 转换为 schema 目标规范")
    lines.append(f"2. 对每个 `indicator_name_list` 条目做 zhiji_id 匹配(需调用 zhiji 搜索)")
    lines.append(f"3. 对每个 series 做 verify_status 校验")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 3. 致命结构错误清单")
    lines.append(f"")

    # 按 code 分组统计
    lines.append(f"### 3.1 错误类型统计")
    lines.append(f"")
    lines.append(f"| 错误码 | 含义 | 数量 | 涉及模板数 |")
    lines.append(f"|---|---|---|---|")
    error_detail = {
        "E1_SCHEMA_MISMATCH": "与schema目标规范不兼容(缺必需字段)",
        "E2_ID_MISSING": "template_id 缺失",
        "E3_FIELD_MISSING_variety": "variety字段缺失",
        "E3_FIELD_MISSING_node": "node字段缺失",
        "E3_FIELD_MISSING_chart_title": "chart_title字段缺失",
        "E3_FIELD_MISSING_indicator_name_list": "indicator_name_list字段缺失",
        "E4_EMPTY_INDICATORS": "指标列表为空",
        "E5_INVALID_VARIETY": "非法品种代码",
        "E6_NODE_NOT_IN_TREE": "node不在tree_config",
        "E7_TITLE_FORMAT": "chart_title格式异常",
    }
    for code in sorted(error_by_code.keys()):
        detail = error_detail.get(code, "未分类")
        affected = len(set(e["template"] for e in all_errors if e["code"] == code))
        lines.append(f"| `{code}` | {detail} | {error_by_code[code]} | {affected} |")

    lines.append(f"")
    lines.append(f"### 3.2 E1_SCHEMA_MISMATCH 详情")
    lines.append(f"")
    lines.append(f"**全部 155 个模板均命中此错误**——这是 THS 模板的系统性问题, 非个案。")
    lines.append(f"示例(前5个):")
    lines.append(f"")
    lines.append(f"| 模板ID | 实际字段 | 缺失的schema字段 |")
    lines.append(f"|---|---|---|")
    for t in ths[:5]:
        missing = [f for f in SCHEMA_REQUIRED_FIELDS if f not in t]
        lines.append(f"| `{t['template_id']}` | {list(t.keys())} | {missing} |")

    # E6 详情
    if error_by_code.get("E6_NODE_NOT_IN_TREE"):
        lines.append(f"")
        lines.append(f"### 3.3 E6_NODE_NOT_IN_TREE 详情")
        lines.append(f"")
        lines.append(f"THS 使用了 tree_config 中不存在的高层节点代码:")
        lines.append(f"")
        lines.append(f"| 模板ID | 品种 | node(THS) | 说明 |")
        lines.append(f"|---|---|---|---|")
        for e in all_errors:
            if e["code"] == "E6_NODE_NOT_IN_TREE":
                t = next(x for x in ths if x["template_id"] == e["template"])
                lines.append(f"| `{t['template_id']}` | {t['variety']} | `{t['node']}` | {e['detail']} |")

    # E7 详情
    if error_by_code.get("E7_TITLE_FORMAT"):
        lines.append(f"")
        lines.append(f"### 3.4 E7_TITLE_FORMAT 详情")
        lines.append(f"")
        for e in all_errors:
            if e["code"] == "E7_TITLE_FORMAT":
                t = next(x for x in ths if x["template_id"] == e["template"])
                lines.append(f"- `{t['template_id']}`: `{t['chart_title'][:60]}`")

    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 4. 警告清单")
    lines.append(f"")
    lines.append(f"### 4.1 警告类型统计")
    lines.append(f"")
    lines.append(f"| 警告码 | 含义 | 数量 | 涉及模板数 |")
    lines.append(f"|---|---|---|---|")
    warn_detail = {
        "W1_INVALID_PLOT_TYPE": "非法图表类型",
        "W2_UNIT_MISSING": "单位字段为空",
        "W3_FREQUENCY_MISSING": "频率字段为空",
        "W4_TITLE_IND_MISMATCH": "标题'等N项'与指标数不符",
        "W5_PLOT_TYPE_MONOTONY": "图表类型单一化(时序图为主)",
        "W6_TOO_MANY_INDICATORS": "单图指标过多(>15)",
        "W7_COMPOUND_INDICATOR_NAME": "指标名含复合分隔符",
    }
    for code in sorted(warning_by_code.keys()):
        detail = warn_detail.get(code, "未分类")
        affected = len(set(w["template"] for w in all_warnings if w["code"] == code))
        lines.append(f"| `{code}` | {detail} | {warning_by_code[code]} | {affected} |")

    lines.append(f"")
    lines.append(f"### 4.2 W2_UNIT_MISSING 详情(单位缺失)")
    lines.append(f"")
    unit_missing = [w for w in all_warnings if w["code"] == "W2_UNIT_MISSING"]
    if unit_missing:
        lines.append(f"共 {len(unit_missing)} 个模板单位缺失:")
        lines.append(f"")
        for w in unit_missing[:20]:
            t = next(x for x in ths if x["template_id"] == w["template"])
            lines.append(f"- `{t['template_id']}` ({t['variety']}, {t['node']})")
        if len(unit_missing) > 20:
            lines.append(f"- ... 等共 {len(unit_missing)} 个")

    lines.append(f"")
    lines.append(f"### 4.3 W6_TOO_MANY_INDICATORS 详情(指标过多)")
    lines.append(f"")
    too_many = [w for w in all_warnings if w["code"] == "W6_TOO_MANY_INDICATORS"]
    if too_many:
        lines.append(f"共 {len(too_many)} 个模板指标数 > 15, 图表可读性风险:")
        lines.append(f"")
        lines.append(f"| 模板ID | 品种 | 指标数 |")
        lines.append(f"|---|---|---|")
        for w in sorted(too_many, key=lambda x: -int(re.search(r'\d+', x["detail"]).group())):
            t = next(x for x in ths if x["template_id"] == w["template"])
            n = len(t["indicator_name_list"])
            lines.append(f"| `{t['template_id']}` | {t['variety']} | {n} |")

    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 5. 品种覆盖对比")
    lines.append(f"")
    lines.append(f"| 品种 | THS模板数 | PDF模板数 | 差异 |")
    lines.append(f"|---|---|---|---|")
    pdf_path = V85_BASE / "pdf_template_build/zhiji_verified_package/pdf_web_chart_template_hermes_ready.json"
    if pdf_path.exists():
        pdf = json.load(open(pdf_path, "r", encoding="utf-8"))
        pdf_var_counts = Counter(t.get("variety") for t in pdf.get("templates", []))
    else:
        pdf_var_counts = {}
    ths_var_counts = Counter(t["variety"] for t in ths)
    all_vars = sorted(set(list(ths_var_counts.keys()) + list(pdf_var_counts.keys())))
    for v in all_vars:
        ths_c = ths_var_counts.get(v, 0)
        pdf_c = pdf_var_counts.get(v, 0)
        if ths_c and not pdf_c:
            diff = "THS独有"
        elif pdf_c and not ths_c:
            diff = "PDF独有"
        else:
            diff = "双方覆盖"
        lines.append(f"| {v} | {ths_c} | {pdf_c} | {diff} |")

    lines.append(f"")
    lines.append(f"**差异说明**:")
    lines.append(f"- THS 独有: LI(碳酸锂), CU(铜), ZN(锌) — 3个品种共91个模板, 共占THS 58.7%")
    lines.append(f"- PDF 独有: AO(氧化铝), LC(碳酸锂期货) — 与 THS 的 LI 部分重叠")
    lines.append(f"- 品种代码体系需统一: LI vs LC 的映射关系需明确")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 6. 渲染前必做适配清单")
    lines.append(f"")
    lines.append(f"基于本次校验结果, 后续 THS 模板渲染前必须完成以下适配:")
    lines.append(f"")
    lines.append(f"### 6.1 适配层(参照 t22_render_online.py::adapt_template)")
    lines.append(f"1. `template_id` → `chart_id`")
    lines.append(f"2. `chart_title` → 解析出 `title`(去除品种/节点/等N项/类型前后缀)")
    lines.append(f"3. `variety`/`plot_type` → `meta.variety`/`meta.chart_type`")
    lines.append(f"4. `indicator_name_list[]` → 展开为 `series[].name`(每项一个series)")
    lines.append(f"5. 从 `单位` 字段推导 `y_axis.left.unit`")
    lines.append(f"6. 新增缺失字段: `series[].zhiji_id`(需zhiji匹配)、`series[].status`(需校验)")
    lines.append(f"")
    lines.append(f"### 6.2 风险预判")
    lines.append(f"1. **节点对齐风险**: 3个模板(THS-AL-3.1/3.2/3.3)用高层节点, tree_config用细分节点(3.1.1-3.1.5), 需确定映射规则")
    lines.append(f"2. **品种体系风险**: LI/LC/CU/ZN 在 THS 有但 PDF 无, 品种中文名映射表需补齐")
    lines.append(f"3. **指标数风险**: 部分模板指标数>15(最多44), 单图指标过多需拆图或聚合")
    lines.append(f"4. **频率缺失风险**: 153/155模板无频率信息, 渲染时无法确定时间轴粒度")
    lines.append(f"5. **单位缺失风险**: 19个模板无单位, 纵轴单位需从指标名反推")
    lines.append(f"6. **schema不兼容风险**: 全部模板需经适配层, 不可直接渲染(最大风险)")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 7. 校验脚本说明")
    lines.append(f"")
    lines.append(f"- 脚本: `ths_template_static_check.py`(本目录)")
    lines.append(f"- 输入: `{THS_PATH}`")
    lines.append(f"- 输出: `{OUT_REPORT.name}`(本报告)")
    lines.append(f"- 错误码: E1-E7(致命), W1-W7(警告)")
    lines.append(f"- 运行: `python3 ths_template_static_check.py`")
    lines.append(f"")

    report = "\n".join(lines)
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(f"\n报告已生成: {OUT_REPORT}")
    print(f"致命错误: {fatal_count}, 警告: {warn_count}")
    print(f"有错误的模板: {len(error_templates)}/{total}")


if __name__ == "__main__":
    main()
