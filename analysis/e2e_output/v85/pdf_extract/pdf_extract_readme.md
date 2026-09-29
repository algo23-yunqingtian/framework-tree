# PDF 原始提取候选指标清单 — 说明文档

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
| 总提取候选条数 | **518** |
| 其中进入匹配候选池 | **316** (True) |
| 未进入候选池 | **202** (False) |

### 按来源文件分布

- `碳酸锂周报20260823.pdf`: 145 条
- `氧化铝周报20260830.pdf`: 100 条
- `铝周报20260830.pdf`: 93 条
- `镍与不锈钢周报20260906.pdf`: 68 条
- `硅产业链周报20260906.pdf`: 63 条
- `锡周报20260905.pdf`: 49 条

### 按抽取标记分布

- `图表/时序`: 508 条
- `图表/截面`: 10 条

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
