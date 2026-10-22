#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
read_only_skill_v3_backtest_report_r02 - table_formatter.py
Markdown表格格式化脚本 (Skill模块)
"""

def fmt_value(v):
    """格式化单个值"""
    if v is None or v == "":
        return "-"
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v)

def render_md_table(headers, rows):
    """渲染Markdown表格"""
    if not headers:
        return ""
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        lines.append("| " + " | ".join(fmt_value(v) for v in r) + " |")
    return "\n".join(lines)
