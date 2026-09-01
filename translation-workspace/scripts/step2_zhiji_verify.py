#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step2_zhiji_verify.py — 指标翻译线 Step2：知几 API 验证（v2 灵活解析版）

从 Step1 audit 文件表格中提取 SMM/Mysteel/LME 精确指标名（9 种表头变体）→
清洗 → 构造知几搜索词（品种+空格+关键词，skill: 中文分词盲区解法）→
zhiji_api.py search → 输出映射表(概念名 → 知几ID → score → 置信度 A/B/C)。

表头变体处理：不依赖固定列号，识别"指标名列"（表头含 SMM官方/Mysteel官方/LME/
指标名/核心指标/推荐指标/建议指标/保留指标/平台搜索框命中名 等），取该列值作为候选名。
同时兼容 CU/AL 的"图名称|核心指标"格式（核心指标列即精确名）。

用法:
  python step2_zhiji_verify.py --all                  # 全部 4 品种
  python step2_zhiji_verify.py --variety NI --dry     # 单品种只解析
  python step2_zhiji_verify.py --all --dry            # 全量解析检查(不搜索)
  python step2_zhiji_verify.py --variety ZN           # 单品种搜索
  python step2_zhiji_verify.py --retry-failed         # 补跑 C 级

产物: translation-workspace/mapping/{品种}/step2_match_{品种}.json
状态: translation-workspace/mapping/_step2_state.json (断点续跑)
"""
import argparse, json, os, re, subprocess, sys, time, glob

BASE = "/home/ubuntu/framework-tree"
AUDIT_ROOT = os.path.join(BASE, "translation-workspace", "audit")
MAPPING_ROOT = os.path.join(BASE, "translation-workspace", "mapping")
STATE = os.path.join(MAPPING_ROOT, "_step2_state.json")
ZHJ = "/home/ubuntu/.hermes/scripts/zhiji_api.py"
RATE_LIMIT = 1.1       # 知几 API 限流 1次/秒
SCORE_A = 12           # ≥12 A命中
SCORE_B = 6            # 6-11 B弱匹配, <6 C未命中

# 表头含以下关键词的列 = 指标名列
NAME_COL_HINTS = ["SMM官方", "Mysteel官方", "LME英文", "LME常见", "LME精确", "LME官方",
                  "指标名", "核心指标", "推荐指标", "建议指标", "保留指标", "建议核心",
                  "平台搜索框命中名", "平台命名", "建议搜索名", "可能命名"]
# 表头 = 图名/子节点等 非指标列（用来跳过）
SKIP_HDR_HINTS = ["图名称", "子节点", "删除指标", "删除理由", "保留理由", "处理意见",
                  "处理方式", "处理结果", "调整", "原指标", "原归属", "使用结论",
                  "判断目的", "说明", "理由", "频率", "可得性", "单位", "备注",
                  "图表数", "变化", "作用", "目的"]


def parse_audit_tables(path):
    """解析 audit 文件表格 → [{subnode, chart, names:[]}]，names 为提取的候选指标名（去重）"""
    rows = []
    lines = open(path, encoding="utf-8").read().split("\n")
    current_sub = ""
    name_cols = None  # 当前表头下的指标名列索引集合
    chart_col = None  # 图名列索引
    for ln in lines:
        s = ln.strip()
        m = re.match(r"^(?:子节点\s*)?(\d+\.\d+)", s)
        if m and len(s) < 25:
            current_sub = m.group(1)
        if "\t" not in s:
            continue
        cells = [c.strip() for c in s.split("\t")]
        if len(cells) < 2:
            continue
        # 表头识别
        is_header = any("名称" in c or "命名" in c or "指标" in c or "图名" in c for c in cells[:6])
        if is_header and any(("官方" in c or "命名" in c or "指标" in c or "搜索框" in c) for c in cells[:6]):
            name_cols = set()
            chart_col = None
            for i, c in enumerate(cells):
                if any(h in c for h in NAME_COL_HINTS):
                    name_cols.add(i)
                if any(h in c for h in ["图名称", "子节点"]):
                    chart_col = i
            # 若表头只识别到 chart 列而没有指标列，跳过（这是删除表/理由表）
            if not name_cols:
                name_cols = None
            continue
        if name_cols is None:
            continue
        # 数据行：跳过说明性行
        first = cells[0]
        if re.match(r"^\d+$", first):
            continue
        if any(("：" in first and len(first) > 15) or len(first) > 25 for first in [cells[0]]):
            continue
        if len(first) < 2:
            continue
        names = []
        for i in name_cols:
            if i < len(cells):
                v = cells[i]
                if v and v != "无" and "无统一" not in v[:8]:
                    names.append(v)
        if not names:
            continue
        chart = cells[chart_col] if chart_col is not None and chart_col < len(cells) else first
        rows.append({"subnode": current_sub, "chart": chart, "names": names})
    return rows


def zhiji_search(query, limit=10):
    r = subprocess.run(["/usr/bin/python3", ZHJ, "search", query, "all", str(limit)],
                       capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"error": f"parse fail: {r.stdout[:200]}"}


def main():
    # ⚠️ 已废弃（2026-09-01）：旧的分词+自动匹配机制被同花顺AI纠正取代。
    # 原 build_search_terms / grade_hit / clean_name 函数已删除。
    # 新流程：同花顺AI逐节点纠正指标名 → 人工录入正确映射 → zhiji_api 手动验证。
    print("⚠️ step2_zhiji_verify.py 已废弃，请使用同花顺AI纠正流程，不要再运行本脚本。")
    return


if __name__ == "__main__":
    main()
