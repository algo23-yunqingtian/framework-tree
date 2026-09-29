# V8.5 上线复核看板 · 评审入口

> 工单: HERMES_BUILD_REVIEW_DASHBOARD_V85_20260928
> 生成时间: 2026-09-29 09:23
> **第一入口 → [review_dashboard.html](review_dashboard.html)**

---

## 1. 核心交付物

| # | 文件 | 说明 |
|---|------|------|
| 1 | **[review_dashboard.html](review_dashboard.html)** | ⭐ 交互式复核看板（纯静态，零后端，双击打开）。32 行 × 47 字段全量表 + 颜色标记 + 15 张渲染图 + 告警直达锚点 + 人工结论填写/导出 |
| 2 | **[ACCEPTANCE_REPORT_v85.md](ACCEPTANCE_REPORT_v85.md)** | ⭐ 全链路验收汇总报告（匹配/API/绘图/告警四模块 + 能力边界 + 人工复核操作指引） |
| 3 | `dashboard_stats.json` | 看板统计数据（机器可读，供下游脚本消费） |
| 4 | `renders/` | 15 张增强渲染 PNG（从 `../renders_enhanced/` 归档拷贝） |
| 5 | `build_dashboard.py` | 看板生成脚本（确定性，可重跑复现） |
| 6 | `REVIEW_DASHBOARD_MD5.md` | 全部产物 MD5 校验清单 |

---

## 2. 上游评审材料（原始，未修改，位于 `../`）

| 类别 | 文件 | 内容 |
|------|------|------|
| **就绪锁** | `JOB_READY.flag` | 就绪声明、约束声明、DSHB 侧 MD5 声明 |
| **看板（最终过滤版）** | `fp32_v85_final_filtered_board.csv` | ⭐ 本看板数据源，32 行 × 47 列 |
| **统一告警汇总** | `unified_warning_summary.md` | ⭐ 告警回填 + 看板外告警兜底 |
| **端到端总汇** | `final_e2e_summary.md` | 四阶段链路总览 + 渲染清单 |
| **看板清洗报告** | `board_clean_and_unit_fix_report.md` | 去重 3 条 + 单位映射表 |
| **MD5 清单** | `MD5_CHECKSUM_LIST.md` | DSHB 拉取阶段校验清单 |
| **API 拉取** | `zhiji_fetch_result.json` | 55 ID 全量时序数据 |
| **API 汇总** | `zhiji_fetch_summary_report.md` | 拉取 53/55 成功报告 |
| **重复 ID 清单** | `duplicate_id_list.json` | 8 个重复 ID 组（去重依据） |

### 元数据质检（`../meta_check/`）

| 文件 | 内容 |
|------|------|
| [`meta_quality_summary.md`](../meta_check/meta_quality_summary.md) | 55 ID 质检汇总：4 警告 ID / 7 条告警 |
| [`meta_warning_list.json`](../meta_check/meta_warning_list.json) | 警告明细（机器可读） |
| [`empty_data_report.md`](../meta_check/empty_data_report.md) | 空数据报告 |
| [`unit_convert_mapping.json`](../unit_convert_mapping.json) | 单位换算映射表（吨↔万吨） |

### 元数据缺口分析（`../meta_gap/`）

| 文件 | 内容 |
|------|------|
| [`meta_gap_analysis.md`](../meta_gap/meta_gap_analysis.md) | 39/55 元数据缺失根因分析（100% 属「indicators_v1 未收录」） |
| [`meta_missing_id_list.json`](../meta_gap/meta_missing_id_list.json) | 缺失 ID 清单 |
| [`dataset_scope_diff.md`](../meta_gap/dataset_scope_diff.md) | 数据集口径差异 |
| [`data_status_tag_candidate.json`](../meta_gap/data_status_tag_candidate.json) | data_status 标签候选 |

### 渲染产物

| 目录 | 内容 |
|------|------|
| `../renders_enhanced/` | 15 张增强渲染 PNG（权威源） |
| `../render/` | 首次渲染 PNG（历史保留） |
| `renders/`（本目录） | 15 张归档拷贝，供看板相对路径引用 |

---

## 3. 评审流程速览

```
1. 打开 review_dashboard.html
   └─ 概览：12 统计卡 + 状态分布（正常27 / 权限缺失5 / 稀疏0 / 下线0）

2. 告警直达 → 5 条权限缺失行（一键锚点跳转）
   └─ 另 3 条看板外告警见 unified_warning_summary.md §2.2

3. 图表速览 → 15 张渲染图（点击开大图，卡片颜色=状态）

4. 全量表 → 32 行 × 47 字段
   ├─ 放行 16 行：确认候选语义 + 单位匹配 + 填人工结论
   ├─ 拦截 11 行：直接废弃（跨域脏候选，最终分=0）
   └─ 弃权  5 行：路径污染，确认需修路径而非改规则

5. 点「导出人工结论 (.csv)」下载，交回主脑合并
```

---

## 4. 关键结论

| 项 | 值 |
|----|----|
| 匹配误绑定率 | **0 条**（跨域脏候选 100% 拦截） |
| zhiji API 增量消耗 | **0 次**（全量复用缓存） |
| 去重节省 API 调用 | **3 次**（3 组重复 zhiji_id） |
| 单位换算生效 | **1 条**（ID02069937，万吨→吨 ×10000） |
| 告警回填修复 | **5 行**（unified_warning 列） |
| 看板外告警兜底 | **3 ID / 5 条**（不丢失） |
| 渲染成功 / 失败 | **15 / 0** |
| REVIEW_SKIP 保留 | **32/32** |
| 人工结论留白 | **32/32** |
| 元数据缺失率 | 70.9%（39/55，100% 为 indicators_v1 未收录） |
| 上线判定 | ⚠️ **可进入人工复核候选池，禁止自动绑定 ID** |

---

## 5. 约束声明（本工单已遵守）

- ✅ 全程零 zhiji API 调用
- ✅ 未修改 `data/indicators_v1.json`
- ✅ 未修改匹配规则 / 词表
- ✅ 未修改 GT 真值
- ✅ 保留 REVIEW_SKIP（32/32 行）
- ✅ 人工结论列留白（32/32 行）
- ✅ 原始历史文件完整保留，未覆盖、未删除
- ✅ 新增产物仅写入 `analysis/e2e_output/v85/review_dashboard/`

---

*入口文档结束 · 详见 ACCEPTANCE_REPORT_v85.md*
