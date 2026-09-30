# 门户版本变更记录

> 工单: `HERMES_V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIMULATION`  
> 覆盖版本: v1 → v2 → v3 → v4

---

## v4 — 增强版（本次工单）

**工单**: `HERMES_V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIMULATION`  
**日期**: 2026-09-30  
**分支**: `feature/v85-chart-template` @ `5012efa`

### 新增功能

| # | 功能 | 说明 |
|---|------|------|
| 1 | 多维度批量筛选 | 按来源(PDF/THS)、风险等级(P0/P1/CLEAN)、品种、图表类型组合筛选；支持多选批量导出 |
| 2 | 模板详情弹窗 | 点击展开单张图表卡片，展示全套元数据：图表类型、复合绘图样式、图例指标列表、每条指标风险说明、黑名单规则编号、冲突根因预留字段 |
| 3 | 全局可视化大盘 | 渲染队列占比饼图(文本内嵌)、品种分布柱状图、风险类型分布统计；Markdown内嵌简易可视化 |
| 4 | PDF/THS差异对比面板 | 品种覆盖对比、图表类型分布差异、指标体系对比（匹配率/可渲染/阻塞/平均series数） |
| 5 | 人工评审操作区 | 在门户内标记评审结果（通过/驳回/临时白名单放行），记录评审人/时间/备注，落盘到独立CSV |
| 6 | 渲染流程仿真模拟 | 488模板全量仿真跑批，5阶段链路(加载→schema→语义→路由→渲染)，输出失败场景清单和容错评估 |
| 7 | DSHB动态加载 | 预留CSV加载入口，DSHB提交后一键替换风险标签，输出diff报告 |
| 8 | 结构化日志 | 每次扫描输出JSONL结构化日志，记录每条模板命中的规则ID、风险描述 |

### 新增文件

| 文件 | 大小 | 说明 |
|------|------|------|
| enhanced_review_portal.md | 12KB | 评审门户 v4 |
| portal_operation_manual.md | 7KB | 操作手册 |
| render_simulation_report.md | 6KB | 仿真评估报告 |
| render_simulation_log.csv | 81KB | 仿真全量日志(488行) |
| enhanced_auto_semantic_check.py | 31KB | 校验器 v3.0 |
| portal_changelog.md | 本文件 | 变更记录 |
| render_scan_log.jsonl | ~1MB | 结构化校验日志(10050条) |
| render_simulation_stats.json | — | 仿真统计 |

### 关键数字

- 模板总数: 488 (PDF 333 + THS 155)
- 仿真: 88渲染成功 + 267 P0阻塞 + 131 THS待匹配 + 1渲染失败 + 1入复核队列
- 校验日志: 10,050 条 JSONL
- P0回归: 6/6 通过

---

## v3 — 最终整合版

**工单**: `HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE`  
**日期**: 2026-09-30  
**分支**: `feature/v85-chart-template` @ `5012efa`

### 新增功能

| # | 功能 | 说明 |
|---|------|------|
| 1 | 全局总统计面板 | 模板总览(488) + 风险分布 + 品种分布 + 渲染队列概览 |
| 2 | 统一风险库接入 | semantic_blacklist_hermes_fixed.json v2.0-fixed (10组) |
| 3 | PDF/THS双源合并看板 | 来源标签 + 状态标记规则 |
| 4 | 分级渲染任务清单 | 89可渲染 + 132复核 + 267阻塞 |
| 5 | 导出功能 | CSV摘要 + 批量校验命令 |

### 新增文件

| 文件 | 说明 |
|------|------|
| chart_risk_bound_all.json (1.6MB) | 488模板风险绑定 |
| updated_auto_semantic_check.py (25KB) | 校验器 v2.0 |
| ths_render_task_list.json (125KB) | 分级渲染任务清单 |
| ths_render_task_manifest.json (518KB) | 完整渲染任务编排 |
| ths_render_prep_script.py (11KB) | 渲染编排脚本 |
| final_integrated_review_portal.md (16KB) | 评审门户 v3 |

---

## v2 — 语义黑名单升级版

**工单**: `HERMES_SEMANTIC_BLACKLIST_UPDATE_AND_PORTAL_UPGRADE`  
**日期**: 2026-09-30

### 新增功能

| # | 功能 | 说明 |
|---|------|------|
| 1 | PDF/THS双来源 | 新增同花顺模板评审入口 + 来源区分标签 |
| 2 | 黑名单版本标注 | v1.0 → v2.0-fixed (BL-021修复) |
| 3 | 黑名单复测报告 | 新旧命中差异对比 |

### 新增文件

| 文件 | 说明 |
|------|------|
| semantic_blacklist_hermes_fixed.json | 黑名单 v2.0-fixed (10组) |
| comparison_v1.0_vs_v2.0.json | 新旧对比 (8 P0 + 2 P1) |
| updated_auto_semantic_check.py | 校验器 v2.0 (BL-021修复) |
| final_review_portal.md | 评审门户 v2 |

---

## v1 — 初始版

**工单**: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  
**日期**: 2026-09-29

### 新增功能

| # | 功能 | 说明 |
|---|------|------|
| 1 | 评审门户初始版 | PDF 333模板评审入口 |
| 2 | 模糊匹配抽检 | 124条模糊匹配样本 |
| 3 | 异常指标清单 | 5 INVALID + 2 MISSING |

### 新增文件

| 文件 | 说明 |
|------|------|
| review_portal.md | 评审门户 v1 |
| fuzzy_match_sample_checklist.md | 模糊匹配抽检清单 |
| abnormal_indicator_list.csv | 异常指标清单 |

---

## 版本演进路线图

```
v1 (2026-09-29)                v2 (2026-09-30)              v3 (2026-09-30)              v4 (2026-09-30)
HERMES_V85_ARTIFICIAL    →    HERMES_SEMANTIC_       →    HERMES_THS_RENDER_     →    HERMES_V85_REVIEW_PORTAL
_REVIEW_PREP                  BLACKLIST_UPDATE             PREP_AND_PORTAL             _ENHANCE_AND_RENDER
                             _AND_PORTAL_UPGRADE          _FINAL_INTEGRATE            _SIMULATION
                             
PDF 333模板评审               +THS 155模板入口              +488模板风险绑定            +多维筛选+详情弹窗
+模糊匹配抽检                 +黑名单v2.0-fixed             +分级渲染任务清单           +全局可视化大盘
+异常指标清单                  +BL-021修复                   +全局统计面板               +PDF/THS差异对比
                              +新旧对比                    +导出功能                   +人工评审操作区
                                                                                      +渲染仿真模拟
                                                                                      +DSHB动态加载
                                                                                      +结构化日志
```
