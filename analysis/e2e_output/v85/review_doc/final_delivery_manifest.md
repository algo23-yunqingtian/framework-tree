# DSHB v85 上线交付包清单
## DSH-B_REVIEW_ACCEPTANCE_SUMMARY_V85_20260928

**生成时间**: 2026-09-28T18:00:00+08:00  
**版本**: v85  
**仓库**: `git@github.com:algo23-yunqingtian/framework-tree.git`  
**分支**: `task/p0_verify`  
**基线 commit**: `3539574` (HEAD before this work order)  

---

## 一、DSHB 交付物清单

### 1.1 匹配引擎与数据链路

| # | 文件 | 路径 | 大小 | MD5 | Commit | 工单 | 状态 |
|---|------|------|------|-----|--------|------|------|
| 1 | 端到端看板 (64 TP样本) | `fp32_v85_final_board.csv` | 9,051 B | `80f07448523023362360f090186a0bdd` | `f72ceec` | DSHB_END2END_ZHIJI_DATA_FETCH | ✅ 可用 |
| 2 | 知几数据拉取结果 | `zhiji_fetch_result.json` | 134,746 B | `83f44a590fb8c3bbe6f93c6b630130f8` | `f72ceec` | DSHB_END2END_ZHIJI_DATA_FETCH | ✅ 可用 |
| 3 | 拉取汇总报告 | `zhiji_fetch_summary_report.md` | 8,107 B | `23938f357bbe48cb5506c53c20a9c2a5` | `f72ceec` | DSHB_END2END_ZHIJI_DATA_FETCH | ✅ 可用 |
| 4 | 重复ID清单 | `duplicate_id_list.json` | 7,062 B | `39d9d1c4355a232a78d8f0d4c6a40f91` | `f72ceec` | DSHB_END2END_ZHIJI_DATA_FETCH | ✅ 可用 |
| 5 | 拉取执行日志 | `fetch_log.txt` | 212 B | `376c1183ab1fa1c8d72327f1d814ca28` | `f72ceec` | DSHB_END2END_ZHIJI_DATA_FETCH | ✅ 可用 |

### 1.2 元数据质检

| # | 文件 | 路径 | 大小 | MD5 | Commit | 工单 | 状态 |
|---|------|------|------|-----|--------|------|------|
| 6 | 元数据警告清单 | `meta_check/meta_warning_list.json` | 2,993 B | `ec59c47ba49c7fdf2ffd849482d85aa2` | `ed5f7d0` | DSHB_CHECK_META_DATA_QUALITY | ✅ 可用 |
| 7 | 元数据质检汇总 | `meta_check/meta_quality_summary.md` | 6,297 B | `38ce35409d82a030820d03d81585dc28` | `ed5f7d0` | DSHB_CHECK_META_DATA_QUALITY | ✅ 可用 |
| 8 | 空数据复核报告 | `meta_check/empty_data_report.md` | 2,906 B | `97b223abb6a3d94267215c14c1b9a8f1` | `ed5f7d0` | DSHB_CHECK_META_DATA_QUALITY | ✅ 可用 |
| 9 | 单位转换映射 | `meta_check/unit_convert_mapping.json` | 27,198 B | `802c432f656771cfe9aadc564110b9ae` | `ed5f7d0` | DSHB_CHECK_META_DATA_QUALITY | ✅ 可用 |

### 1.3 元数据差距分析

| # | 文件 | 路径 | 大小 | MD5 | Commit | 工单 | 状态 |
|---|------|------|------|-----|--------|------|------|
| 10 | 缺失ID清单 | `meta_gap/meta_missing_id_list.json` | 22,091 B | `ffcc4eb43c648c57ba4fb144dd5181f7` | `4aec2f4` | DSHB_META_GAP_ANALYSIS | ✅ 可用 |
| 11 | 差距分析报告 | `meta_gap/meta_gap_analysis.md` | 11,484 B | `e4e0d507925c8489ee06939731d5867b` | `4aec2f4` | DSHB_META_GAP_ANALYSIS | ✅ 可用 |
| 12 | 数据状态标签 | `meta_gap/data_status_tag_candidate.json` | 22,219 B | `101f956c2381a208bb499dde65e7f604` | `4aec2f4` | DSHB_META_GAP_ANALYSIS | ✅ 可用 |
| 13 | 数据集口径差异 | `meta_gap/dataset_scope_diff.md` | 10,854 B | `b6547bcde200e0e6ec374ae2e1b6ade1` | `4aec2f4` | DSHB_META_GAP_ANALYSIS | ✅ 可用 |

### 1.4 评审材料

| # | 文件 | 路径 | 大小 | MD5 | Commit | 工单 | 状态 |
|---|------|------|------|-----|--------|------|------|
| 14 | **评审底稿** | `review_doc/v85_review_draft.md` | 24,270 B | `a6649a407893030e06f75a7a399fa951` | 本工单 | DSHB_REVIEW_ACCEPTANCE_SUMMARY | ✅ 可用 |
| 15 | 汇总总表 (55项×8维度) | `review_doc/final_overview_summary.csv` | 5,545 B | `3d09c01a920a802227b360b19340deff` | `3539574` | DSHB_PREPARE_REVIEW_MATERIALS | ✅ 可用 |
| 16 | 文件索引 (含commit hash) | `review_doc/file_index.csv` | 4,582 B | `f76589c0bbcdc86b0acbe0f115509b35` | `3539574` | DSHB_PREPARE_REVIEW_MATERIALS | ✅ 可用 |
| 17 | **最终交付包清单** | `review_doc/final_delivery_manifest.md` | — | — | 本工单 | DSHB_REVIEW_ACCEPTANCE_SUMMARY | ✅ 可用 |
| 18 | 聚合MD5校验清单 | `review_doc/MD5_CHECKSUM_LIST.md` | 373 B | `61dc856e131123f2dd6657c6a7c599aa` | `3539574` | DSHB_PREPARE_REVIEW_MATERIALS | ✅ 可用 |

### 1.5 就绪锁文件

| # | 文件 | 路径 | 大小 | 工单 | 状态 |
|---|------|------|------|------|------|
| 19 | 就绪锁文件 | `JOB_READY.flag` | — | 多工单追加 | ✅ 可用 |

---

## 二、HERMES 交付物清单

### 2.1 看板交付

| # | 文件 | 路径 | 说明 | 状态 |
|---|------|------|------|------|
| H1 | 静态HTML复核看板 | (HERMES 侧归档) | 消费 DSHB 交付数据渲染 FP 子集看板 | ✅ 已完成 |
| H2 | 看板核验报告 | `dashboard_final_check_report.md` | HERMES 侧归档，本仓库未同步 | ⚠️ 待同步 |
| H3 | 渲染回执 | (HERMES 侧归档) | jsdom 环境验证，266/266 页面 PASS | ✅ 已完成 |

### 2.2 HERMES 看板修复记录

| 修复项 | 描述 | 验证状态 |
|--------|------|---------|
| idx 非唯一缺陷修复 | `fp32_v85_final_board.csv` 以 `(trace_id, chart_name)` 复合键去重 | ✅ 已验证 |
| 重复指标标记 | 8 个重复 zhiji_id 已标记 `[重复:N]` 徽标 | ✅ 已验证 |
| 上游 MD5 溯源验证 | 5/5 文件 MD5 与 DSHB 交付一致，全链路闭环 | ✅ 已验证 |

---

## 三、Commit 历史与仓库路径

### 3.1 本仓库 Commit 链

| Commit | 类型 | 描述 | 工单 |
|--------|------|------|------|
| `f72ceec` | feat | zhiji 数据拉取结果 v85 | DSHB_END2END_ZHIJI_DATA_FETCH |
| `ed5f7d0` | feat | 元数据质检 v85 | DSHB_CHECK_META_DATA_QUALITY |
| `4aec2f4` | feat | 元数据差距分析 v85 | DSHB_META_GAP_ANALYSIS |
| `3539574` | docs | 上线评审材料汇总 | DSHB_PREPARE_REVIEW_MATERIALS |
| (本工单) | docs | 验收汇总文档更新 | DSHB_REVIEW_ACCEPTANCE_SUMMARY |

### 3.2 仓库路径

```
仓库地址: git@github.com:algo23-yunqingtian/framework-tree.git
分支:     task/p0_verify
基线:     3539574 (HEAD before this work order)
目标目录: analysis/e2e_output/v85/
           └─ review_doc/          (评审材料)
           └─ meta_check/          (元数据质检)
           └─ meta_gap/            (差距分析)
           └─ JOB_READY.flag       (就绪锁)
           └─ *.csv, *.json, *.md  (核心数据文件)
```

---

## 四、MD5 全量校验清单

### 4.1 核心数据文件

| 文件 | MD5 | 工单 |
|------|-----|------|
| `fp32_v85_final_board.csv` | `80f07448523023362360f090186a0bdd` | `f72ceec` |
| `zhiji_fetch_result.json` | `83f44a590fb8c3bbe6f93c6b630130f8` | `f72ceec` |
| `zhiji_fetch_summary_report.md` | `23938f357bbe48cb5506c53c20a9c2a5` | `f72ceec` |
| `duplicate_id_list.json` | `39d9d1c4355a232a78d8f0d4c6a40f91` | `f72ceec` |
| `fetch_log.txt` | `376c1183ab1fa1c8d72327f1d814ca28` | `f72ceec` |

### 4.2 元数据质检文件

| 文件 | MD5 | 工单 |
|------|-----|------|
| `meta_check/meta_warning_list.json` | `ec59c47ba49c7fdf2ffd849482d85aa2` | `ed5f7d0` |
| `meta_check/meta_quality_summary.md` | `38ce35409d82a030820d03d81585dc28` | `ed5f7d0` |
| `meta_check/empty_data_report.md` | `97b223abb6a3d94267215c14c1b9a8f1` | `ed5f7d0` |
| `meta_check/unit_convert_mapping.json` | `802c432f656771cfe9aadc564110b9ae` | `ed5f7d0` |

### 4.3 元数据差距分析文件

| 文件 | MD5 | 工单 |
|------|-----|------|
| `meta_gap/meta_missing_id_list.json` | `ffcc4eb43c648c57ba4fb144dd5181f7` | `4aec2f4` |
| `meta_gap/meta_gap_analysis.md` | `e4e0d507925c8489ee06939731d5867b` | `4aec2f4` |
| `meta_gap/data_status_tag_candidate.json` | `101f956c2381a208bb499dde65e7f604` | `4aec2f4` |
| `meta_gap/dataset_scope_diff.md` | `b6547bcde200e0e6ec374ae2e1b6ade1` | `4aec2f4` |

### 4.4 评审材料文件

| 文件 | MD5 | 工单 |
|------|-----|------|
| `review_doc/v85_review_draft.md` | `a6649a407893030e06f75a7a399fa951` | 本工单 |
| `review_doc/final_overview_summary.csv` | `3d09c01a920a802227b360b19340deff` | `3539574` |
| `review_doc/file_index.csv` | `f76589c0bbcdc86b0acbe0f115509b35` | `3539574` |
| `review_doc/MD5_CHECKSUM_LIST.md` | `61dc856e131123f2dd6657c6a7c599aa` | `3539574` |

---

## 五、交付状态区分

### 【本次交付可用】✅

| # | 交付物 | 说明 |
|---|--------|------|
| 1 | 匹配引擎 (v7 规则) | P=100%, R=74.24%, F1=85.22%, FP=0 |
| 2 | 端到端数据链路 | 64 TP / 55 唯一 ID / 96.36% 成功率 |
| 3 | 元数据质检 | 4 警告 (2 HIGH), 全部分类标注 |
| 4 | 元数据差距分析 | 39/55 缺失 ID 清单 + 根因分类 |
| 5 | 异常指标台账 | 5 个异常 (1 下线, 1 权限, 2 稀疏, 2 单位) |
| 6 | 评审底稿 | 7 章节 + HERMES 修复记录 + 风险清单 |
| 7 | 汇总总表 | 55 项指标 × 8 维度 |
| 8 | 文件索引 | 全量产物 + commit hash + MD5 |
| 9 | HERMES 看板修复 | idx 修复 + 重复标记 + MD5 溯源闭环 |
| 10 | 就绪锁文件 | JOB_READY.flag 全量标记 |
| 11 | 最终交付包清单 | 本文档 |

### 【待后续迭代】📋

| # | 任务 | 优先级 | 阻塞性 | 说明 |
|---|------|--------|--------|------|
| 1 | 批量导入 P0 的 22 个缺失 ID | P0 | ⚠️ 有条件 | 7天内完成 indicators_v1 补充 |
| 2 | 建立 POS 告警分流通道 | P1 | ⚠️ 有条件 | 2周内, 解决 27 个 POS-only ID 告警漏报 |
| 3 | HERMES 审核范围扩展评估 | P1 | ⚠️ 有条件 | 2周内, FP→全量 64 样本 |
| 4 | li_21 锂2.1 页面搭建 | P2 | ❌ 非阻塞 | 碳酸锂页面, 不影响铝产业链交付 |
| 5 | verify_render.js jsdom 依赖安装 | P3 | ❌ 非阻塞 | 运维侧处理, 恢复自动化渲染验证 |
| 6 | HERMES 看板核验报告同步 | P3 | ❌ 非阻塞 | dashboard_final_check_report.md 需从 HERMES 侧归档至本仓库 |
| 7 | 补充碳酸锂正样本测试 | P2 | ❌ 非阻塞 | 下轮迭代扩展品种覆盖 |

---

## 六、HERMES 读取指令

HERMES 侧消费 DSHB 交付数据的建议读取顺序:

```
# 就绪确认
1.  JOB_READY.flag                           — 确认 STATUS=READY, REVIEW_MATERIAL_READY=COMPLETED

# 数据拉取结果
2.  fp32_v85_final_board.csv                 — 64 TP 样本看板
3.  duplicate_id_list.json                   — 8 个重复 ID 去重参考
4.  zhiji_fetch_result.json                  — 完整时序数据 (55 ID, 12,858 数据点)
5.  zhiji_fetch_summary_report.md            — 拉取汇总报告

# 元数据质检
6.  meta_check/meta_warning_list.json        — 4 警告 (2 HIGH)
7.  meta_check/meta_quality_summary.md       — 质检汇总
8.  meta_check/empty_data_report.md          — 空数据复核

# 差距分析
9.  meta_gap/meta_missing_id_list.json       — 39 缺失 ID 清单
10. meta_gap/data_status_tag_candidate.json   — 5 种数据状态标签
11. meta_gap/dataset_scope_diff.md           — FP/POS 口径差异

# 评审材料
12. review_doc/v85_review_draft.md            — 完整评审底稿
13. review_doc/final_overview_summary.csv     — 汇总数据表
14. review_doc/file_index.csv                 — 全量产物索引
15. review_doc/final_delivery_manifest.md     — 最终交付包清单
```

---

## 七、约束合规验证

| 约束 | 要求 | 验证结果 |
|------|------|---------|
| indicators_v1.json | 只读, 无修改 | ✅ 未触碰 |
| GT (Ground Truth) | 只读, 无修改 | ✅ 未触碰 |
| 匹配规则 | 只读, 无修改 | ✅ 未触碰 |
| zhiji API | 零新增调用 | ✅ 未调用 |
| 历史工单产物 | 不覆盖, 仅追加 | ✅ 全部保留 |
| 额度消耗 | 零 zhiji 额度 | ✅ 零消耗 |

---

*文档生成: DSH-B_REVIEW_ACCEPTANCE_SUMMARY_V85_20260928*  
*仓库: git@github.com:algo23-yunqingtian/framework-tree.git*  
*分支: task/p0_verify*  
*数据截止: 2026-09-28T18:00:00+08:00*