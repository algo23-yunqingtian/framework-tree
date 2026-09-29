# V8.5 静态复核看板 · 最终核验归档报告

- **工单**: `HERMES_DASHBOARD_FINAL_CHECK_AND_ARCHIVE_V85_20260928`（收尾工单）
- **关联工单**: `HERMES_BUILD_REVIEW_DASHBOARD_V85_20260928`（工单 5，看板构建）
- **看板版本**: v3（最终核验归档版）
- **核验时间**: 2026-09-29
- **上游真值源**: `/home/ubuntu/analysis/temp/ind_compare_result/交接文档_会话收尾入口_20260928.md`（2026-09-28 15:03）
- **交付目录**: `analysis/e2e_output/v85/review_dashboard/`
- **提交**: `417a47a`（v2 修复版）→ 本次最终归档 commit

---

## 0. 结论

| 项 | 结论 |
|---|---|
| 看板可用性 | ✅ **可交付评审** |
| T2 四项核验 | ✅ 4/4 通过 |
| T3 缺失页面标注 | ✅ 已标注，不阻断验收 |
| 门禁 | ✅ reclaim 12/12 PASS；⚠️ check_html 266/267（li_21，非本次交付物）；⏭️ verify_render 按工单约束跳过 |
| 约束 | ✅ 零 zhiji API、红线文件零改动、REVIEW_SKIP 32/32、人工结论 32/32 留白 |
| 待办 | 2 项（li_21 页面待建、jsdom 环境依赖），均不阻塞评审 |

---

## 1. T2 看板最终核验明细

### 1.1 唯一键核验 ✅

| 核验项 | 实测 | 期望 | 结果 |
|---|---|---|---|
| `行号` 列（L1–L32）主键 | 32 行 | 32 | ✅ |
| 锚点数 | 32 | 32 | ✅ |
| 锚点唯一性 | 32/32 唯一，范围 `r1`..`r32` | 无重复 | ✅ |
| 失效锚点引用 | 0 | 0 | ✅ |
| `data-lineno` 属性（导出用） | 32 | 32 | ✅ |
| idx 列橙色警示 `!` | 33 处（32 行 + 1 列头说明） | ≥32 | ✅ |
| CSV 导出含行号 | 表头 `行号\|idx\|zhiji_id\|图表短名\|候选指标名\|人工结论` | 含行号 | ✅ |

**判定**: 行号已作为唯一主键贯穿「表格展示 → 锚点跳转 → 告警直达 → 图表速览回链 → CSV 导出」全链路；idx 列保留但带橙色警示，不再单独用于定位。

### 1.2 同 ID 重复行标签核验 ✅

| zhiji_id | 重复行 | 看板中出现 | 黄色告警标签 |
|---|---|---|---|
| `ID01370137` | 行 22（DMC利润）/ 行 24（DMC行业利润） | 23 处 | ✅ |
| `ID01464612` | 2 行 | 9 处 | ✅ |
| `ID01464616` | 2 行 | 9 处 | ✅ |

- `dup-badge` 黄色标签共 **3 组**，全部在图表速览区正常展示。
- 标签 title 提示「同一 zhiji_id 在看板出现 N 次，需人工确认冗余」。
- 是否冗余**由人工判定**，本版未自动删行（REVIEW_SKIP 保留）。

### 1.3 上游 DSHB 溯源链核验 ✅

| 上游核心产物 | 交接文档声明 MD5 | 实测 MD5 | 结果 |
|---|---|---|---|
| `v8_fix_fp_output/score_compare_v8.json` | `894f721b28c59b2a6a82457d6acc8d83` | 同左 | ✅ 一致 |
| `v8_fix_fp_output/skip_rescore_v8_fixed.json` | `370c23486ca331ec47fa582d807ec610` | 同左 | ✅ 一致 |
| `v8_fix_fp_output/fp32_v85_final_board.csv` | `a44d65f2aa09c60aa41373aa4f463e33` | 同左 | ✅ 一致 |
| `v8_fix_fp_output/fp32_v85_end2end_board.csv` | `ba94e18192f2488f8d728222fc0a630b` | 同左 | ✅ 一致 |
| `v85_end2end_output/zhiji_fetch_result.json` | `0baa89a8a254f00a85cebe651f39d658` | 同左 | ✅ 一致 |
| `v85_end2end_output/render_test_receipt.json` | `a2eb497bd108f1f381756ee2601060bc` | 同左 | ✅ 一致 |

**溯源链路 6/6 一致**。本看板数据源 `fp32_v85_final_filtered_board.csv` 由工单 1→2→3→4 逐步加工而来，可完整追溯至 DSHB 真值产物。

### 1.4 STATUS.md 与协议合规核验 ✅

| 核验项 | 结果 |
|---|---|
| STATUS.md「近期变更记录」含工单 5 完整记录 | ✅ 含 T2/T3/T4、交接文档 §6 坑修复、约束、已知问题注 |
| pre-commit hook 已安装 | ✅ `git config core.hooksPath = scripts/hooks` |
| 本次提交使用 `--no-verify` | ❌ 未使用（已走正常 pre-commit） |
| `data/indicators_v1.json` MD5 | `4db5418d1b6d40a69c5dc2659040e754`（未变） |
| `data/tree_config.json` MD5 | `9b98c8afc855...`（未变） |

---

## 2. T3 缺失页面标注 ✅

`li_21` 锂 2.1 盘面结构页面**已在看板首页标注**：

> ℹ️ **范围说明（不阻断验收）**：`li_21` 锂 2.1 盘面结构页面标记为【NI/SN/SI/LI 待建页面，非本次交付物】，属 STATUS.md 记载的五金属建页待办（ZN 29 页已完成，NI/SN/SI/LI 数据已拉、JSONL 已导、待建页）。该页面不在本复核看板范围内，`scripts/check_html.py` 报 266/267 的唯一 FAIL 项即为此页面（本地未跟踪/缺失），不影响本看板验收结论。

**实测证据**:
- `li_21*.html` 在仓库根目录不存在（`ls: cannot access`）
- `git ls-files | grep "^li_21"` 为空 → 从未被 git 跟踪
- 非本工单产物，属 STATUS.md §8「五金属 NI/SN/SI/LI Step4 建页待做」待办

---

## 3. 门禁测试结果清单

| # | 门禁 | 命令 | 结果 | 定性 |
|---|---|---|---|---|
| 1 | 上线自检 | `bash scripts/bootstrap_agent.sh` | 🔴 2 项 ❌ | 均为历史遗留/环境项，非本工单可解（见下） |
| 2 | 静态校验 | `python3 scripts/check_html.py` | 266/267 ❌ | 唯一 FAIL = `li_21`（非本次交付物） |
| 3 | 渲染校验 | `node scripts/verify_render.js` | ⏭️ **跳过** | 按工单 T1.3 约束，jsdom 依赖缺失标记为环境低优先级运维问题 |
| 4 | 格式契约+产物完整性 | `python3 scripts/reclaim.py` | ✅ **PASS=12 FAIL=0** | 全部通过，可 merge 回收 |

### 3.1 bootstrap 自检 2 项 ❌ 说明

| ❌ 项 | 内容 | 定性 |
|---|---|---|
| [1/6] git 基线 | `?? task_queue/to_A/` 未跟踪 | **历史遗留**：交接文档 §6.7 明确记载「与本任务无关，勿动」。全程未跟踪、未提交、未删除 |
| [4/6] 门禁快检 | check_html FAIL | 即 `li_21`，已标注为非本次交付物 |

**[3/6] 指标基线提示** `version v3.83` 与脚本注释「当前应=196/3.42」不符 —— 属脚本内注释陈旧，非本次改动引入（`indicators_v1.json` MD5 未变），列为观察项。

### 3.2 verify_render.js 跳过依据

```
code: 'MODULE_NOT_FOUND'
requireStack: ['/tmp/node_modules/jsdom/...']
```

- 根因：`/tmp/node_modules` jsdom 依赖不完整（环境故障，非产物问题）
- 工单 T1.3 明确约束：**不改动 /tmp 临时 node_modules，不安装 jsdom 依赖，跳过执行**
- 处置：标记为【环境低优先级运维问题，不阻塞评审】，不修复、不重试

---

## 4. 已修复的 3 个核心坑点

| # | 交接文档 §6 原文 | v1 缺陷 | v3 修复 |
|---|---|---|---|
| 坑 1 | **idx 列非全局唯一**（9 组重复），行定位须用「行号+图表短名」二元组 | 全部锚点用 idx；32 行仅 18 个不同 idx（idx30×4、idx36×3、idx37×3、idx39×3、idx32×3、idx5/6/31/34×2），评审无法唯一定位 | 新增 `行号` L1–L32 主键列；idx 列加橙色 `!` 警示；锚点/告警直达/图表回链/CSV 导出全部改用行号 |
| 坑 2 | **ID01370137 重复行**（同一指标两条冗余行），冗余待人工确认 | 未标注 | 图表速览黄色 `同ID重复行` 标签，共 3 组（ID01370137 / ID01464612 / ID01464616），冗余与否交人工判定 |
| 坑 3 / P2 | **DSHB 产物位置**本机 0 命中，需真实上游路径 | MD5 清单仅含仓库内文件，无上游溯源链 | 定位真实上游 `/home/ubuntu/analysis/temp/ind_compare_result/`；`REVIEW_DASHBOARD_MD5.md` §4 记录 6 个上游产物 MD5，**6/6 一致** |

> 首版遗漏根因：交接文档位于 `/home/ubuntu/analysis/temp/ind_compare_result/`（**非 git 仓库**），首次检索仅在 framework-tree 仓库内搜索导致未命中。已在记忆持久化该路径。

---

## 5. 遗留待办（2 项，均不阻塞评审）

| # | 待办 | 优先级 | 说明 |
|---|---|---|---|
| 1 | **li_21 锂 2.1 盘面结构页面待建设** | 中 | 属五金属 NI/SN/SI/LI 建页待办（STATUS.md §8）；数据已拉、JSONL 已导，待同花顺发散→注册→建页。看板首页已标注【非本次交付物】 |
| 2 | **jsdom 依赖环境问题** | 低 | `/tmp/node_modules` jsdom 依赖不完整致 `verify_render.js` 无法执行。环境级问题，与产物无关。修复方式：重装 `/tmp/node_modules` jsdom 依赖。本工单约束不处理 |

### 5.1 其余已知项（承接自工单 5，未变）

- **JOB_READY.flag 声明 MD5 与实际不一致**：flag 生成于 DSH-B T1 阶段（2026-09-28T14:52），此后工单 2/3 对看板做了去重/单位映射/告警回填加工致内容变更。根因已记入 `REVIEW_DASHBOARD_MD5.md` §5，**不修正**（如实记录）。
- **稀疏/下线 = 0 非漏检**：3 个 zhiji_id（ID00259727 停更1446天、CM0000053686 稀疏1点、a10166705 稀疏2点）经 FP 抑制未进看板，告警已兜底于 `unified_warning_summary.md` §2.2。
- **人工复核 4 项**（承接自上游工单）：39 条缺失 ID 是否录入 indicators_v1.json；4 条异常指标处置；POS 子集纳入方案；MD5 不一致低风险巡检。

---

## 6. 约束遵守声明

| 约束 | 实测 |
|---|---|
| 零 zhiji API 调用 | ✅ 全程复用本地缓存与上游产物 |
| `indicators_v1.json` 未修改 | ✅ MD5 `4db5418d1b6d40a69c5dc2659040e754` |
| `tree_config.json` 未修改 | ✅ MD5 `9b98c8afc855...` |
| GT 真值 / 匹配规则 未修改 | ✅ |
| 不改动 /tmp node_modules、不安装 jsdom | ✅ 未执行 |
| 不删除、不覆盖历史文件 | ✅ 仅新增归档文件 + 更新看板构建产物与 STATUS.md |
| REVIEW_SKIP 保留 | ✅ 32/32 |
| 人工结论列空白 | ✅ 32/32 留白，**禁止自动绑定指标 ID** |
| 仅新增归档文件 | ✅ `dashboard_final_check_report.md`（新增）+ `JOB_READY.flag` 追加标记 |
| 不使用 `--no-verify` | ✅ 走正常 pre-commit |

---

## 7. 交付物清单

`analysis/e2e_output/v85/review_dashboard/`:

| 文件 | 用途 |
|---|---|
| `review_dashboard.html` | **静态复核看板（v3 最终版）**，纯 html+css+内联 JS，零后端 |
| `dashboard_index.md` | 评审入口文档 |
| `ACCEPTANCE_REPORT_v85.md` | 四模块全链路验收报告 |
| **`dashboard_final_check_report.md`** | **本报告（最终核验归档）** |
| `REVIEW_DASHBOARD_MD5.md` | MD5 校验清单（本工单产物 + 上游 DSHB 链 + 已知不一致） |
| `dashboard_stats.json` | 看板构建统计 |
| `build_dashboard.py` | 确定性构建脚本（可重跑） |
| `renders/` | 15 张增强渲染 PNG（相对路径引用） |
