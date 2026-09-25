# HERMES 审计回执 · 工单 HERMES_AUDIT_HIST_IND_20260924

- **审计时间**：2026-09-24
- **审计人**：Framework-Tree 主脑（只读审计模式，未修改指标库）
- **审计基线**：`origin/main @ 404f7ee`（2026-09-13 16:47）
- **被审分支**：`origin/indicator-correction-win @ 5e4efe8`（2026-09-14 09:28）
- **结论**：⛔ **驳回（BLOCK）— 工单前置条件未达成，禁止合并进 main**

---

## 一、交接自检阶段复核意见（任务目标 1）

### 1.1 结论：新 DSH-B「交接自检回执」未送达 → 工单在此阶段暂停

工单要求的第一步是"接收新 DSH-B 提交的【交接自检回执】"。经全量只读核查，**该回执不存在**：

| 核查项 | 结果 | 证据 |
|---|---|---|
| `task_queue/feedback/` 最新回执 | **止于 2026-09-14 09:15**（`REVIEW_PB_EXEC_TASK_PENDING_20260914.md`） | `ls -la task_queue/feedback/` |
| 含"交接自检/DSH-B 交接"字样的回执 | **0 份** | `grep -rl "自检回执\|交接自检\|新DSH-B" task_queue/ docs/ output/` → 无命中 |
| 远端自 2026-09-14 以来的新分支/提交 | **0** | `git log -1 origin/indicator-correction-win` = 09-14 09:28；`origin/main` = 09-13 16:47 |
| 本机 `~/task_queue` 最新文件 | 止于 2026-09-12 | mtime 扫描 |
| `task_queue/to_B/`（主脑→DSH-B 发件箱） | 仅有 09-13 两份任务卡，**无 DSH-B 回件** | `PB_EXEC_TASK_20260913.md` / `PB_PIPELINE_TASK_20260913.md` |

**含义**：DSH-B 最后一次动作停在 09-14 09:28（win 分支），此后 10 天无任何回传。"新旧 DSH-B 节点切换"的信息断层**尚未收到任何正式交接声明**，无法核验原始素材完整性与业务规则缺口。

按工单硬性约束第 1 条——"如果自检回执显示资料缺失、关键清洗规则丢失，直接暂停工单"——此处更严重：**回执本身缺失**，暂停工单，退回 FT 主脑评估风险。

---

## 二、指标合并审计结论（任务目标 2–4）

虽前置条件未达成，但按工单要求对 win 分支变更做了**只读**比对，结论为**不可直接合并**，且存在方向性错误。

### 2.1 ⛔ 结构性阻断：win 分支基于旧包装结构，与 main 的 flat-dict 结构不可直接 merge

| | `origin/main` | `origin/indicator-correction-win` |
|---|---|---|
| 提交 | `404f7ee`（09-13 16:47） | `5e4efe8`（09-14 09:28） |
| `indicators_v1.json` 结构 | **flat-dict**（指标为顶层 key） | **包装结构**（`{_meta, indicators, version, updated, change, version_changelog, 64_group}`） |
| 指标条目数 | **1584** | **1025**（位于 `indicators` 子字典内） |
| 顶层 `version` 字段 | `v3.83` | `v3.50`（`_meta.version` = `3.78` 语义，混用） |
| `_main_metric` | 有（120 条） | **无** |
| `wr*` 周报指标 | 有（wr1–wr276） | **无** |

**后果**：直接把 win merge 进 main 会产生 **144 文件 / +90944 / -24341** 行级冲突（`indicators_v1.json` 单文件 14427 insert / 13130 delete），且 merge 后的 JSON 结构会被回退为旧的包装格式，**main 上 1584 条中的 `_main_metric`(120 条) 与 `wr*`(276 条) 将整体丢失** = 基线污染。这违反 AGENTS.md §2"开工前必须 `git rebase origin/main`，指标数必须 ≥ main"。

### 2.2 ⛔ 分叉已彻底断流：win 非 main 祖先

- `git merge-base --is-ancestor 5e4efe8 origin/main` → **exit=1**（win HEAD 不是 main 祖先）
- merge-base = `f73bccb`，即 win 从**旧** main 分叉
- 分叉计数：main 领先 **145** 个提交，win 领先 **16** 个提交
- 结论：两条线已双向分叉，main 侧 145 个提交全部落在 win 之后，win 的所有变更都建在 main 尚未包含（且结构已重构）的旧基线上。

### 2.3 ⚠️ win 独有变更（16 commits）真实内容 —— 非本工单所说的"历史新增/匹配指标口径一致性"

win 独有提交实际是 **PB（铅）修正批次 + 前端/上游修复**，且**不含任何 `pb_` 前缀指标**：

| commit | 内容 |
|---|---|
| `5e4efe8` | `[B-PB-CORRECTION]` PB 修正合并：remote 964(v3.49) + PB 61 new = **1025 v3.50** |
| `fb49d34` | PB 修正批次注册：27 份 correction 文件 → **62 条新 A 级指标入库**（v3.48→v3.49） |
| `fdd1466` | `[DOC]` PB 流水线人工放行通知 + PB 发散审计（135 行/70 条子集基准/幻觉 0 条） |
| `5cd6da3` | `fix(F3+U2+U4)` 复审阻断缺陷修复 |
| `8b513fc` | `[DOC]` 三次复审报告：F3 阻断（40 处 `__tgl` 引号嵌套 + 90 处 `getElementById` 旧命名，verify_render 170→140 净损 30 页） |
| `267614d` | `fix(F1-F3+U1-U4)` 前端残余修复 + 上游 C1/C2/C3/C5 |
| `b400023` | `[DOC]` 二次修复复审报告（前置受阻·待二次修复） |
| `e9bf3d4` | `[DOC]` 审计交付物入库 5 份 |
| `1def0f2` / `78631cc` / `5a3a33b` / `6167792` / `2351c0d` / `38bf48c` / `39ffd91` / `d891991` | 前端修复、上游数据治理（阈值 5→4 + 别名词典）、chart_registry v2.0、DSH-B 角色设定与 task_queue 基础设施 |

**关键取证（口径与主键）**：

1. **`pb_` 前缀指标 = 0 条**（实测）。win 声称的"61/62 条 PB 新 A 级指标"采用的是 **`i*` 旧编号体系**，非 `pb_` 前缀——与 main 上五金属/铜铝的 `cu_/al_/zn_/ni_/sn_/si_/li_/pb_` 前缀是**两套命名体系**。这就是工单所担心的"同名指标、不同口径"风险的实际形态，但方向相反：不是假阳性匹配，而是**新旧两套 ID 体系并存**。
2. **`_main_metric` 字段缺失**：main 侧 120 条正主映射在 win 上不存在 → 合并后所有依赖 `_main_metric` 的主图选择会回退兜底（历史已多次因此串台，见 skill 根因 F）。
3. **`wr*` 276 条周报指标缺失**：合并后周报看板数据源整体丢失。
4. **F3 缺陷状态未知**：win 侧 `8b513fc` 自述 F3 阻断（verify_render 170→140），`5cd6da3` 声称已修，但**该修复建立在旧基线上，在 main 1584 条/新结构上从未验证**。

### 2.4 关于工单点名的三项风险

| 工单风险项 | 核查结果 |
|---|---|
| 新旧 DSH-B 节点切换信息断层、隐性清洗规则丢失 | **确认成立**：DSH-B 10 天无回传，无交接自检回执；"清洗规则"载体（v1.1 角色定义 + task_queue 基础设施）都在 win 上，而 win 已断流 |
| 同名指标、不同口径造成 `zhiji_id` 假阳性匹配 | **形态不同但存在**：win 用 `i*` 旧编号 / main 用 `pb_` 新前缀，两套 ID 体系；win 的 61 条 PB 新指标未在主键唯一性层面与 main 的 1584 条做过交集核验 |
| win/main 分支分叉、历史 PB 标签错乱引发基线污染 | **确认成立且为最高优先级**：双向分叉 145↔16，win 旧结构合并会回退 main 结构，`_main_metric`+`wr*` 共 396 条附属数据丢失 |

---

## 三、风险条目清单

| # | 风险 | 严重度 | 类型 |
|---|---|---|---|
| R1 | 新 DSH-B「交接自检回执」完全缺失，工单前置条件未达成 | 🔴 阻断 | 交接断层 |
| R2 | win 非 main 祖先，双向分叉 145↔16，不可直接 merge | 🔴 阻断 | 分支分叉 |
| R3 | win 为旧包装结构 vs main flat-dict；合并将丢失 `_main_metric`(120) + `wr*`(276) = 396 条附属数据 | 🔴 阻断 | 基线污染 |
| R4 | `indicators_v1.json` 单文件 14427+/13130- 冲突面，无法安全自动合并 | 🔴 阻断 | 合并可行性 |
| R5 | win 的 61 条 PB 新 A 级指标用 `i*` 旧编号，与 main `pb_` 前缀体系未做主键/口径交集核验 | 🟡 待核 | 口径一致性 |
| R6 | F3 修复（`5cd6da3`）建立在旧基线，未在 main 新结构上验证 | 🟡 待核 | 回归风险 |
| R7 | DSH-B 已 10 天（09-14 09:28 起）无回传，节点是否仍存活未知 | 🟡 流程 | 可达性 |

---

## 四、授权决定

**⛔ 驳回合并授权。** 不授权 FT 主脑安排 win 分支向 main 合并。

依据工单硬性约束："审计不通过禁止合并进 main 正式基线"、"所有落地执行必须人工放行"。

### 退回 DSH-B / FT 主脑的修正要求

在重新提交审计前，必须完成以下三项：

1. **补交「交接自检回执」**（工单目标 1 的前置）：明确声明新旧 DSH-B 节点切换范围、原始素材清单、业务清洗规则清单（含 `i*`→`pb_` 命名迁移映射）。
2. **win 分支 rebase 到最新 main**（`git rebase origin/main`），并在**新结构**（flat-dict）上重做 PB 修正注册——禁止在旧包装结构上继续产出。rebase 后指标数必须 ≥ main 的 1584。
3. **提交指标变更清单**：逐条列出 61 条 PB 新 A 级指标的 `key / 指标名 / zhiji_id / 节点 / 数据来源`，并附与 main 1584 条的**主键唯一性核验结果**（`zhiji_id` 冲突数须为 0）与高风险错配条目标记。

完成 1–3 后重新提交，本工单进入任务目标 2 的正式指标合并审计流程。

---

## 五、审计方法说明（可复算）

全程只读，未修改 `indicators_v1.json`、未改任何指标库/看板文件、未 checkout 任何分支：

```bash
git fetch origin --prune
git merge-base --is-ancestor 5e4efe8 origin/main          # exit=1 → 非祖先
git rev-list --count origin/main..origin/indicator-correction-win   # 16
git rev-list --count origin/indicator-correction-win..origin/main   # 145
git diff --stat origin/main...origin/indicator-correction-win       # 144 files
git show origin/main:data/indicators_v1.json             # 结构+计数（只读）
git show origin/indicator-correction-win:data/indicators_v1.json
git log --oneline origin/main..origin/indicator-correction-win
ls -la task_queue/feedback/ task_queue/to_B/
grep -rl "自检回执\|交接自检\|新DSH-B" task_queue/ docs/ output/
```
