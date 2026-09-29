# V8.5 上线复核看板 · 评审入口

> ## 🔒 版本锁定声明
>
> | 项 | 值 |
> |---|---|
> | **锁定版本** | **v85 看板锁定** |
> | **锁定 Commit** | `c20f579`（`[AUTO] HERMES v85 静态复核看板最终核验归档`） |
> | **锁定日期** | 2026-09-29 |
> | **锁定工单** | `HERMES_V85_DASHBOARD_VERSION_LOCK_V85_20260928` |
> | **看板文件** | `review_dashboard.html`（v3 最终核验归档版） |
> | **口径对齐基准** | `STATUS.md` §「2026-09-29 收尾工单」+ `dashboard_final_check_report.md` |
> | **DSHB 发布文档** | ⚠️ `DSHB release_note_v85.md` **全机 0 命中**（工单 T1 前置读取目标不存在），如实报告，以既有 STATUS.md + v3 产物为口径基准 |
> | **产物目录** | `analysis/e2e_output/v85/review_dashboard/` |
> | **上游真值源** | `/home/ubuntu/analysis/temp/ind_compare_result/交接文档_会话收尾入口_20260928.md` |

> 工单（构建）: HERMES_BUILD_REVIEW_DASHBOARD_V85_20260928
> 工单（收尾核验）: HERMES_DASHBOARD_FINAL_CHECK_AND_ARCHIVE_V85_20260928
> 工单（本次锁定）: HERMES_V85_DASHBOARD_VERSION_LOCK_V85_20260928
> 生成时间: 2026-09-29 09:23（v3 最终核验） · **2026-09-29 追加版本锁定段**
> **第一入口 → [review_dashboard.html](review_dashboard.html)**

---

## 1. 核心交付物

| # | 文件 | 说明 |
|---|------|------|
| 1 | **[review_dashboard.html](review_dashboard.html)** | ⭐ 交互式复核看板 **v3 最终核验归档版 · v85 锁定**（纯静态，零后端，双击打开）。32 行 × 47 字段全量表 + 行号 L1–L32 唯一主键 + 颜色标记 + 15 张渲染图 + 告警直达锚点 + 人工结论填写/导出 |
| 2 | **[ACCEPTANCE_REPORT_v85.md](ACCEPTANCE_REPORT_v85.md)** | ⭐ 全链路验收汇总报告（匹配/API/绘图/告警四模块 + 能力边界 + 人工复核操作指引） |
| 3 | **[dashboard_final_check_report.md](dashboard_final_check_report.md)** | ⭐ 最终核验归档报告（收尾工单 T2 四项核验 + 门禁清单 + 3 坑修复 + 2 项待办） |
| 4 | **[dashboard_release_note.md](dashboard_release_note.md)** | ⭐ **本次新增**：看板版本锁定发布说明（修复内容、门禁结果、遗留项） |
| 5 | `dashboard_stats.json` | 看板统计数据（机器可读，供下游脚本消费） |
| 6 | `renders/` | 15 张增强渲染 PNG（从 `../renders_enhanced/` 归档拷贝） |
| 7 | `REVIEW_DASHBOARD_MD5.md` | 全部产物 MD5 校验清单（含上游 DSHB 溯源链 + 版本锁定后全量快照） |
| 8 | `build_dashboard.py` | 看板生成脚本（确定性，可重跑复现） |

---

## 2. 上游评审材料（原始，未修改，位于 `../`）

| 类别 | 文件 | 内容 |
|------|------|------|
| **就绪锁** | `JOB_READY.flag` | 就绪声明、约束声明、DSHB 侧 MD5 声明（已追加 DASHBOARD_FINAL_ARCHIVE=COMPLETED 与本次 DASHBOARD_VERSION_LOCKED=TRUE） |
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

5. 点「导出人工结论 (.csv)」下载（表头含 行号|idx|zhiji_id|图表短名|候选指标名|人工结论），交回主脑合并
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

## 5. 能力边界（v85 看板）

### 5.1 看板可做的事（4 项）
1. **展示** 32 条 FP 抑制候选行的全量字段（47 列）+ 15 张真实渲染图
2. **定位** 通过「行号 L1–L32」唯一主键（idx 列仅作辅助参考，橙色 ! 警示）
3. **告警直达** 5 条权限缺失行一键跳转；3 条看板外告警走统一告警汇总兜底
4. **人工结论采集** 就地填写 → localStorage 暂存 → 导出 CSV 交回主脑

### 5.2 看板做不到的事（7 项）
1. ❌ **自动绑定指标 ID** —— REVIEW_SKIP 32/32 保留，人工结论 32/32 留白，禁自动绑 ID（工单硬约束）
2. ❌ **修改匹配/词表/规则/GT 真值** —— 全程只读，`indicators_v1.json` MD5 未变
3. ❌ **调用 zhiji API** —— 零增量，全量复用本地缓存与上游产物
4. ❌ **修复稀疏/下线指标** —— 3 个 zhiji_id 因 FP 抑制未进看板，告警兜底不阻断
5. ❌ **合并冗余行** —— 3 组同 zhiji_id 重复行只标注黄色标签，是否合并由人工判定
6. ❌ **处理动力电池路径污染** —— 4 条弃权行根因在数据源路径编码（空格分隔），需上游规范
7. ❌ **修复 li_21 锂 2.1 盘面结构页缺失** —— 属五金属 NI/SN/SI/LI 建页待办，非本次交付物

---

## 6. 遗留待办清单（分级）

### P0 · 阻断项（1 项，需人工）
| # | 待办 | 说明 |
|---|------|------|
| 1 | **32 条 `人工结论(待填)` 全空** | 工单硬约束要求人工填，禁 agent 代填。16 放行→核对候选对题度；11 拦截→确认拦截；5 弃权→动力电池 4 条候选实为正确需路径修复、DMC 周度产量确认弃权 |

### P1 · 需人工决策（3 项）
| # | 待办 | 说明 |
|---|------|------|
| 2 | **ID02069937 单位冲突** | 锂矿库存·贸易商：看板=吨，API=万吨（差 10 倍），需人工决定用哪个为准 |
| 3 | **ID01370137 看板重复行** | 第 22/24 行同一指标（有机硅DMC生产毛利·季），确认是否冗余删行 |
| 4 | **39 条缺失 ID 是否录入 indicators_v1.json** | 元数据缺失率 70.9%（39/55），走正规注册链路 |

### P2 · 环境/结构性（4 项，均不阻断验收）
| # | 待办 | 说明 |
|---|------|------|
| 5 | **li_21 锂 2.1 盘面结构页面待建设** | 属五金属 NI/SN/SI/LI 建页待办；数据已拉、JSONL 已导，待同花顺发散→注册→建页。看板首页已标注【非本次交付物】 |
| 6 | **jsdom 依赖环境问题** | `/tmp/node_modules` jsdom 依赖不完整致 `verify_render.js` 无法执行。环境级问题，与产物无关。本工单约束不处理 |
| 7 | **PDF 短名→registry 长标题别名映射** | `chart_registry_name_align_v9.csv` 记录 26 条 token 零命中，根治需别名表 |
| 8 | **动力电池路径格式污染** | 4 条弃权行候选路径用空格分隔而非 `\|`，属数据源路径编码问题，需知几注册侧规范化 |

### P3 · 观察项（1 项）
| # | 待办 | 说明 |
|---|------|------|
| 9 | **JOB_READY.flag MD5 声明不一致** | flag 生成于 DSH-B T1 阶段（2026-09-28T14:52），此后工单 2/3 对看板做去重/单位映射/告警回填加工致内容变更。根因已记入 REVIEW_DASHBOARD_MD5.md §5，**不修正**（如实记录） |

---

## 7. 约束声明（本工单已遵守）

- ✅ 全程零 zhiji API 调用
- ✅ 未修改 `data/indicators_v1.json`（MD5 `4db5418d1b6d40a69c5dc2659040e754`）
- ✅ 未修改 `data/tree_config.json`
- ✅ 未修改匹配规则 / 词表
- ✅ 未修改 GT 真值
- ✅ 保留 REVIEW_SKIP（32/32 行）
- ✅ 人工结论列留白（32/32 行）
- ✅ 未改动 /tmp node_modules，未安装 jsdom 依赖
- ✅ 原始历史文件完整保留，未覆盖、未删除
- ✅ 仅新增归档文件到 `analysis/e2e_output/v85/review_dashboard/`
- ✅ 未使用 `--no-verify`，走正常 pre-commit hook

---

## 8. 版本锁定核验快照（T2 · 2026-09-29）

| 核验项 | 实测 | 期望 | 结果 |
|--------|------|------|------|
| `行号` 列（L1–L32）主键 | 32 行 | 32 | ✅ |
| 锚点数 `id="rN"` | 32 | 32 | ✅ |
| 锚点唯一性 | 32/32 唯一，范围 r1..r32 | 无重复 | ✅ |
| 失效锚点引用 `href="#rN"` | 0 / 53 引用 | 0 | ✅ |
| `data-lineno` 属性（导出用） | 32 | 32 | ✅ |
| idx 列橙色警示 `!` | 32 处（32 行） | ≥32 | ✅ |
| CSV 导出功能（btnExport→Blob→URL.createObjectURL） | 完整可用，表头 `行号\|idx\|zhiji_id\|图表短名\|候选指标名\|人工结论` | 完整 | ✅ |
| renders/ 图片引用 | 15 唯一引用 0 缺失 | 15 存在 | ✅ |
| dashboard_index.md 相对链接 | 0 断链 | 0 | ✅ |
| ACCEPTANCE_REPORT_v85.md 相对链接 | 0 断链 | 0 | ✅ |
| dashboard_final_check_report.md 相对链接 | 0 断链 | 0 | ✅ |
| REVIEW_DASHBOARD_MD5.md 相对链接 | 0 断链 | 0 | ✅ |
| 上游 DSHB 溯源链 MD5 | 6/6 一致 | 全一致 | ✅ |
| 32 行复核页面全部可用 | 32/32 | 32 | ✅ |

---

*入口文档结束 · 详见 [dashboard_release_note.md](dashboard_release_note.md)（本次版本锁定发布说明）与 [ACCEPTANCE_REPORT_v85.md](ACCEPTANCE_REPORT_v85.md)*
