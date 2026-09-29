#!/usr/bin/env python3
"""
DSH-B_EXPORT_PDF_EXTRACT_CANDIDATES_V85_20260929
T2: 导出 PDF 原始提取候选指标清单

数据源:
  - snapshot_pdf_local/local_pdf_raw_extract_snapshot_20260924.csv  (518 indicators from PDF)
  - snapshot_pdf_local/pdf_indicator_page_map.json                   (page-level mapping)
  - snapshot_pdf_local/pdf_zhji_pre_match.json                       (zhiji pre-match results)
  - snapshot_pdf_local/pdf_source_manifest.json                      (PDF source manifest)

输出:
  - analysis/e2e_output/v85/pdf_extract/pdf_extract_all_candidates.csv
  - analysis/e2e_output/v85/pdf_extract/pdf_extract_readme.md

约束: 只读源文件, 不做匹配, 不修改 indicators_v1.json, 零 zhiji API 调用
"""

import csv
import json
import os
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────────────
REPO = Path(r"D:\DSH_WORK\framework-tree")
SRC_CSV  = REPO / "snapshot_pdf_local" / "local_pdf_raw_extract_snapshot_20260924.csv"
PAGE_MAP = REPO / "snapshot_pdf_local" / "pdf_indicator_page_map.json"
PRE_MATCH = REPO / "snapshot_pdf_local" / "pdf_zhji_pre_match.json"
SRC_MANIFEST = REPO / "snapshot_pdf_local" / "pdf_source_manifest.json"

OUT_DIR   = REPO / "analysis" / "e2e_output" / "v85" / "pdf_extract"
OUT_CSV   = OUT_DIR / "pdf_extract_all_candidates.csv"
OUT_README = OUT_DIR / "pdf_extract_readme.md"

# ── 读取源数据 ────────────────────────────────────────────────────

def load_source_csv(path):
    """读取源 CSV, 返回 list[dict]"""
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 数据加载 ──────────────────────────────────────────────────────
src_rows    = load_source_csv(SRC_CSV)
page_map_data = load_json(PAGE_MAP)
pre_match_data = load_json(PRE_MATCH)
manifest_data = load_json(SRC_MANIFEST)

# ── 构建索引 ──────────────────────────────────────────────────────

# page_map index: (品种, 图表名) → {pdf_file, page_found, search_text, status}
page_map_index = {}
for entry in page_map_data.get("page_map", []):
    key = (entry["品种"], entry["图表名"])
    page_map_index[key] = entry

# pre_match index: (品种, 图表名) → {match_type, match_confidence, 错误匹配标记}
pre_match_index = {}
for entry in pre_match_data.get("results", []):
    key = (entry["品种"], entry["图表名"])
    pre_match_index[key] = entry

# PDF 文件列表
pdf_files = {f["filename"]: f for f in manifest_data.get("files", [])}

# ── 构建输出 ──────────────────────────────────────────────────────

# note 映射: 根据模块/图表类型推断抽取标记
# CSV 中 图表类型 字段值为: "时序" / "截面"
# CSV 中 呈现方式 字段值为: "时序折线" / "截面柱状/饼图"
NOTE_BY_CHART_TYPE = {
    "时序": "图表/时序",
    "截面": "图表/截面",
}

def determine_note(src_row):
    """根据图表类型确定抽取标记 (图表/正文/表格等)"""
    chart_type = src_row.get("图表类型", "").strip()
    display = src_row.get("呈现方式", "").strip()

    # 根据图表类型推断抽取标记
    note = NOTE_BY_CHART_TYPE.get(chart_type, "正文")

    return note


output_rows = []
for row in src_rows:
    variety = row.get("品种", "").strip()
    chart_name = row.get("图表名", "").strip()
    status = row.get("状态", "").strip()
    display_method = row.get("呈现方式", "").strip()
    chart_type = row.get("图表类型", "").strip()
    zhiji_id = row.get("zhiji_ID", "").strip()
    zhiji_name = row.get("zhiji名称", "").strip()
    module = row.get("模块", "").strip()

    # ── source_file ──
    pm_key = (variety, chart_name)
    pm_entry = page_map_index.get(pm_key, {})
    source_file = pm_entry.get("pdf_file", "")

    # ── page_num ──
    page_found = pm_entry.get("page_found", "")
    page_list = pm_entry.get("page_list", [])
    if page_list and isinstance(page_list, list) and len(page_list) > 0:
        page_num_str = ",".join(str(p) for p in page_list)
    elif page_found is not None:
        page_num_str = str(page_found)
    else:
        page_num_str = ""

    # ── raw_original_text ──
    search_text = pm_entry.get("search_text", "")

    # ── extracted_indicator_name ──
    extracted_name = chart_name

    # ── is_in_top3_candidate ──
    # 判断: 如果状态不是"无结果" (即有匹配), 则进入候选池
    # 同时检查 pre_match 的 match_type
    pm_key2 = (variety, chart_name)
    pm_entry2 = pre_match_index.get(pm_key2, {})
    match_type = pm_entry2.get("match_type", "")

    if status in ("全匹配", "部分匹配") or match_type == "matched":
        is_in_top3 = "True"
    else:
        is_in_top3 = "False"

    # ── note ──
    note = determine_note(row)

    output_rows.append({
        "source_file": source_file,
        "page_num": page_num_str,
        "raw_original_text": search_text,
        "extracted_indicator_name": extracted_name,
        "is_in_top3_candidate": is_in_top3,
        "note": note,
    })

# ── 写入 CSV ──────────────────────────────────────────────────────
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIELDNAMES = ["source_file", "page_num", "raw_original_text",
              "extracted_indicator_name", "is_in_top3_candidate", "note"]

with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"✅ CSV 写入: {OUT_CSV}")
print(f"   总行数: {len(output_rows)}")

# ── 统计 ──────────────────────────────────────────────────────────
total_candidates = len(output_rows)
in_pool = sum(1 for r in output_rows if r["is_in_top3_candidate"] == "True")
not_in_pool = total_candidates - in_pool

# 按来源统计
source_counts = {}
for r in output_rows:
    sf = r["source_file"] if r["source_file"] else "(未映射)"
    source_counts[sf] = source_counts.get(sf, 0) + 1

# 按 note 统计
note_counts = {}
for r in output_rows:
    n = r["note"]
    note_counts[n] = note_counts.get(n, 0) + 1

print(f"\n📊 统计:")
print(f"   总提取候选条数: {total_candidates}")
print(f"   进入匹配候选池: {in_pool}")
print(f"   未进入候选池:   {not_in_pool}")
print(f"   按来源文件: {source_counts}")
print(f"   按抽取标记: {note_counts}")

# ── 写入 README ───────────────────────────────────────────────────
readme_content = f"""# PDF 原始提取候选指标清单 — 说明文档

## 概述

本文件是 DSH 从**本地 PDF 周报**解析得到的全部原始候选指标集合。

> ⚠️ 本文件是【文本抽取阶段产出】，**还未做指标库匹配**。  
> 包含原始候选名称、来源文件、页码，以及是否进入匹配候选池的标记。

## 文件路径

| 项目 | 路径 |
|------|------|
| CSV 完整候选清单 | `analysis/e2e_output/v85/pdf_extract/pdf_extract_all_candidates.csv` |
| 本说明文档 | `analysis/e2e_output/v85/pdf_extract/pdf_extract_readme.md` |
| 源数据 (CSV) | `snapshot_pdf_local/local_pdf_raw_extract_snapshot_20260924.csv` |
| 源数据 (页码映射) | `snapshot_pdf_local/pdf_indicator_page_map.json` |
| 源数据 (预匹配结果) | `snapshot_pdf_local/pdf_zhji_pre_match.json` |
| 源数据 (PDF 清单) | `snapshot_pdf_local/pdf_source_manifest.json` |

## 统计

| 指标 | 数值 |
|------|------|
| 总提取候选条数 | **{total_candidates}** |
| 其中进入匹配候选池 | **{in_pool}** (True) |
| 未进入候选池 | **{not_in_pool}** (False) |

### 按来源文件分布

"""

for sf, cnt in sorted(source_counts.items(), key=lambda x: -x[1]):
    readme_content += f"- `{sf}`: {cnt} 条\n"

readme_content += f"\n### 按抽取标记分布\n\n"

for note, cnt in sorted(note_counts.items(), key=lambda x: -x[1]):
    readme_content += f"- `{note}`: {cnt} 条\n"

readme_content += f"""
## 字段说明

| 字段 | 说明 |
|------|------|
| `source_file` | 来源 PDF 文件名 |
| `page_num` | 在 PDF 中出现的页码 (可能多页, 逗号分隔) |
| `raw_original_text` | PDF 原文搜索关键词 (DSH 用于定位指标名) |
| `extracted_indicator_name` | DSH 提取出的指标名称 (图表名) |
| `is_in_top3_candidate` | 是否进入匹配候选池 (True/False) |
| `note` | 抽取标记 (正文/图表/正文/图表/截面等) |

## 数据来源说明

- 数据源: 本地 PDF 周报 (6 份 PDF 文件)
- 原始快照日期: 2026-09-24
- PDF 清单: 氧化铝周报20260830, 硅产业链周报20260906, 碳酸锂周报20260823, 铝周报20260830, 锡周报20260905, 镍与不锈钢周报20260906
- 与 HERMES 云同花顺问财 MD 指标独立分属

## 约束

- ✅ 只导出，不做任何匹配
- ✅ 不修改 indicators_v1.json
- ✅ 不调用 zhiji API
- ✅ 保留全部原始抽取结果，不过滤、不丢弃任何提取条目

---

*生成时间: 2026-09-29*  
*工单: DSH-B_EXPORT_PDF_EXTRACT_CANDIDATES_V85_20260929*
"""

with open(OUT_README, "w", encoding="utf-8") as f:
    f.write(readme_content)

print(f"\n✅ README 写入: {OUT_README}")
print("🎯 任务完成")
