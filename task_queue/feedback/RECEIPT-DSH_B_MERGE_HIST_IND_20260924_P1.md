# 交接自检回执：DSH_B_MERGE_HIST_IND_20260924 · 阶段1

> **回执编号**: RECEIPT-DSH_B_MERGE_HIST_IND_20260924-P1
> **发送者**: 新 DSH-B（sensenova-6.8-flash-lite / DeepSeek Harness）
> **接收者**: Framework-Tree 主脑（Hermes）
> **生成时间**: 2026-09-24
> **工单编号**: DSH_B_MERGE_HIST_IND_20260924
> **分支**: indicator-correction-win（全程只读，未修改任何禁止文件）
> **优先级**: P0（最高优先级，交接自检）

---

## 一、旧 DSH-B 已完成工作梳理

### 1.1 PB_EXEC_TASK_20260913（PB 修正批次注册）

| 项目 | 数据 | 状态 |
|------|------|------|
| 原始修正文件 | 46 份（28 份原始 + 18 份 cu-al-ni-sn v3 对照） | ✅ 本地在 `translation-workspace/correction/` |
| 解析格式 | 3 种（ZN 旧版 11 列 / AL 新格式 10 列 / cu-al-ni-sn v3 11-12 列含 A/B/C 标记） | ✅ 已文档化于 `scripts/extract_corrections.py` |
| A 级条目提取 | 801 条 | ✅ `scripts/correction_extract_report.json` |
| zhiji_id 去重 | 257 条唯一 ID（193 已注册 + 64 新注册） | ✅ |
| 实际注册 | 62 条（2 条因 ID 重复跳过） | ✅ `indicators_v1.json` 930→1025 |
| 版本升级 | v3.48→v3.49→v3.50（Win 分支） | ✅ |
| 门禁 | check_html 223/223 + verify_render 224/224 ALL PASS | ✅ |

### 1.2 前端修复与上游治理（2026-09-13）

| 任务 | 成果 | 文件 |
|------|------|------|
| R1 标记逻辑修正 | 60 条 ⚪→🟢 | `docs/CHART_REGISTRY.md` |
| R2 全量重跑 build | 清除 62 张 A vs A 自对比图 | `scripts/chart_kits.py` + 62 个 HTML |
| R3 Coverage 报告 | 双口径覆盖率 | `docs/Coverage_Report.md` |
| R4 div-id 修正 | pb_stock_v2 15 张图表 div-id 统一 | `pb_stock_v2.html` |
| F1-F3 缺陷修复 | R1 计数、Coverage 重写、div-id+JS 修复 | 30 个 PB HTML |
| U1-U4 上游修复 | CU 匹配率、SHFE 别名、幻觉清洗、CROSS_PATTERNS | 多个脚本+报告 |
| 知几匹配阈值修复 | 阈值 5→4，v3.49 964 指标 | `scripts/step3_judge_rules.py` |
| THS→知几别名词典 | 2176 条别名映射 | `docs/alias_metadb/thsh_zhiji_alias_map.json` |
| 幻觉清洗 | 198 文件扫描，372 条剔除（6.9%） | `docs/Hallucination_Clean_Report.md` |

### 1.3 审计交付物（只读）

| # | 交付物 | 路径 |
|---|--------|------|
| 1 | 前端指标定义 vs GitHub Pages 一致性核验 | `work_log/hermes_daily_report/audit_indicator_vs_frontend_20260913.md` |
| 2 | 上游链路审计（同花顺→转录→知几） | `task_queue/feedback/AUDIT_UPSTREAM_CHAIN_20260913.md` |
| 3 | chart_registry v2.0 复审 | `task_queue/feedback/REVIEW_CHART_REGISTRY_V2_20260913.md` |
| 4 | 1def0f2 + 78631cc 复审 | `task_queue/feedback/REVIEW_1DEF0F2_AND_78631CC_20260913.md` |
| 5 | PB 版本分叉审计（Win v3.50 vs Main v3.83） | `周报工作区/audit_framework_tree_version_divergence_20260913.md` |

---

## 二、自检清单逐条回复

### ① 是否拿到旧 DSH-B 全部本地原始资料副本？

**结论：基本完整，但存在已知的数据源缺口。**

| 资产类别 | 状态 | 说明 |
|----------|------|------|
| Git 仓库 | ✅ 完整 | `indicator-correction-win` 分支 @ 5e4efe8，1025 指标，v3.50 |
| 主分支备份 | ✅ 完整 | `main` 分支 404f7ee 可访问（v3.83，1580 指标，扁平格式） |
| 翻译线修正文件 | ✅ 完整 | `translation-workspace/correction/` 下 CU/AL/NI/SN/ZN 共 46 份原始文件 |
| 同花顺审计结果 | ✅ 完整 | `translation-workspace/audit/` 下 4 品种 23 份审计报告 |
| Step2 映射结果 | ✅ 完整 | `translation-workspace/mapping/` 含 ZN/CU/AL/NI/SI/SN/LI 映射 JSON+CSV |
| Step3 分层结果 | ✅ 完整 | `analysis/iwencai/step3_slices/` + `step3_final*.json` |
| Divergence 发散文件 | ✅ 完整 | `analysis/iwencai/{品种}/divergence_*.md` 全品种全板块 |
| Decision 决策文件 | ✅ 完整 | `analysis/iwencai/{品种}/decision_*.md` 全品种全板块 |
| 指标备份 | ✅ 完整 | `analysis/backups/` 含 v3.41(196)→v3.49(964)→v3.50(1025) 全链条 |
| 历史项目 prompt | ✅ 完整 | `pb_prompt/` 含 v8/v9/v10/v19 全版本 |
| Windows agent 交接文档 | ✅ 完整 | `HANDOVER_WINDOWS_AGENT.md` |
| 铅库存早期交接 | ✅ 完整 | `pb_prompt/handover_20260827_v2.md` |
| **⚠️ 已知缺口** | | |
| 旧 DSH-B 本地草稿（跨 session） | ❌ **缺失** | 旧 DSH-B 各 session 的本地草稿不跨 session 继承，如旧 session 中有临时未提交的草稿文件，当前 session 不可见 |
| `data-harbor` 归档目录 | ❌ **缺失** | ROLE_DEF §六.2 要求"所有实验产出归档至 data-harbor"，但该目录在本地不存在（可能仅在旧服务器） |
| `/home/ubuntu/` 路径文件 | ❌ **缺失** | 旧交接文档中引用大量 `/home/ubuntu/analysis/` 路径（Linux 服务器），当前 Windows 机器不可访问 |
| 回测数据/CSV | ⚠️ **可见但禁止修改** | `D:\DSH_WORK\github工作\回测\` 和 `li_nonlinear_lgb\` 下大量 CSV 可见，但本工单禁止修改回测数据 |

---

### ② 是否理解旧 DSH-B 当年清洗 46 份表格时的特殊格式兼容规则、异常值剔除逻辑？

**结论：核心逻辑已掌握，部分细节需 FT 主脑确认。**

#### 已掌握的规则

| 规则类别 | 内容 | 来源 |
|----------|------|------|
| **格式兼容 1** | ZN 旧版 11 列表格：`概念指标 | 旧映射 | 同花顺纠正·SMM全称 | 同花顺纠正·Mysteel全称 | 知几·SMM zhiji_id | 知几·Mysteel zhiji_id | 频率 | 单位` | `METHODOLOGY_INDICATOR_CORRECTION.md` |
| **格式兼容 2** | AL 新格式 10 列：含 ✅A/⚠️B/❌C 标记（同花顺 AI 直接判定分级） | `extract_corrections.py` 实测 |
| **格式兼容 3** | cu-al-ni-sn v3 11-12 列：含知几搜索补充字段 | `correction_extract_report.json` 实测 |
| **异常值剔除** | 跨品种幻觉（COMEX/GFEX 出现在 PB/NI/SN 等非对应品种） | `task3_hallucination_clean.py` + `U4 CROSS_PATTERNS` |
| **异常值剔除** | 图表类型命名（时序图/联动图/监控图/复合图）混入指标列 | PB 发散审计 45 条 |
| **异常值剔除** | 派生形态（同比/环比/分位数/去化/增速）单列为指标 | 真混入 2-4 条 |
| **异常值剔除** | zhiji_id 为 FU*（占位）标记为 B 级待验证 | `METHODOLOGY_INDICATOR_CORRECTION.md` |
| **异常值剔除** | 知几搜索结果含 C 级（品种词不匹配或核心关键词缺失）→进备用库 | `step3_judge_rules.py` |
| **指标取舍 5 规则** | 归属优先 / 去重 / 数据可得性 / 正主 vs 辅助 / 产出可查 | `AGENTS.md` §3.5 |
| **正主防串用** | 已在别页做正主的指标禁止重复当正主 | `AGENTS.md` §3.5 |
| **知几匹配阈值** | score≥12=A / 6-11=B / <6=C，阈值已从 5 调至 4 | `matching_report.md` + `STATUS.md` |
| **品种词权重** | 金属词在 zhiji 低权重，查仓单别放金属名 | `HANDOVER_WINDOWS_AGENT.md` §4.1 |

#### 需 FT 主脑确认的细节

| # | 待确认项 | 原因 |
|---|----------|------|
| 1 | **B/C 级过滤条目的具体判定标准** | `correction_extract_report.json` 仅记录 A 级条目（801 条），B/C 级条目的过滤规则未显性文档化。当前理解：B 级=知几搜索结果置信度中等，C 级=品种词或核心关键词不匹配。但 46 份原始表格中同花顺 AI 自己标注的 ✅A/⚠️B/❌C 标记与知几分层的优先级关系不明确 |
| 2 | **62 条新注册指标中 2 条因 ID 重复跳过** | `RECEIPT-PB-EXEC-20260913.md` 提到"2 条因 ID 重复跳过"，但未说明具体是哪 2 条、跳过的判定逻辑（取先到还是取后到？） |
| 3 | **62 条注册态指标的数据拉取状态** | 所有 62 条为注册态（verified=true），但 api_cache.db 数据尚未拉取。是否有部分已拉取？旧 session 是否曾尝试拉取？ |

---

### ③ 是否清楚 zhji_id 匹配规则，以及历史 PB 标签错乱、win/main 分支分叉的背景？

**结论：匹配规则完全掌握；分支分叉全貌清楚；PB 标签错乱细节已充分理解。**

#### zhji_id 匹配规则（完全掌握）

| 层级 | 规则 | 实现 |
|------|------|------|
| Step1 | 同花顺发散获取概念指标 | `divergence_*.md` |
| Step2 | 压缩搜索词→知几 API search | `METHODOLOGY_INDICATOR_CORRECTION.md` |
| Step3 | 按品种词+核心关键词命中分层 A/B/C | `step3_judge_rules.py` |
| Step4 | A 级注册入 `indicators_v1.json` | `step3_register.py` / `register_corrections.py` |
| 别名映射 | THS→知几 2176 条别名对照 | `alias_metadb/thsh_zhiji_alias_map.json` |
| 已知 ID 格式 | a*digits（观数据）/ ID*digits（SMM/Mysteel）/ FU*digits（占位）/ j*digits（自定义） | |

#### PB 标签错乱历史（完全掌握）

| 事件 | 影响 | 文档 |
|------|------|------|
| v3.49 changelog 声称"PB correction 61 条新 A 级指标"，实际注册的是 CU/AL/NI/SN/ZN 指标 | PB 侧 0 条新增，标签错乱 | `PB_DIVERGENCE_AUDIT_20260913.md` |
| PB j/i 前缀 3 处 zhji_id 重叠（a12767751/a12810628/a12813406） | j 前缀指标被双重映射到 i 前缀 ID | `audit_indicator_vs_frontend_20260913.md` |
| al_51_cons 名称为"氟化铝：表观消费量"但归属需求 5.1（氟化铝是助熔剂/成本板块材料） | 语义错配 | `PB_DIVERGENCE_AUDIT_20260913.md` |
| 91 条 PB 指标 _nodes=[] 全缺失 | 无法追溯节点归属 | `STATUS.md` PB 缺陷登记 |
| 70 条 pb_ 前缀指标仅存于 Main（v3.83），Win 侧为 0 | Win/Main 结构性分叉 | `周报工作区/audit_framework_tree_version_divergence_20260913.md` |
| WR (Weekly Report) 276 条指标仅存于 Main | 分支差异最大单一来源 | 同上 |

#### Win/Main 分支分叉背景（完全掌握）

| 维度 | Win 分支 (5e4efe8) | Main 分支 (404f7ee) |
|------|-------------------|---------------------|
| 版本 | v3.50 | v3.83 |
| 指标数 | 1,025 | 1,580 |
| 数据格式 | 嵌套 `indicators` dict | 扁平根级结构 |
| 分叉点 | 自 f73bccb 分叉 | 已领先 Win 10 提交 |
| Win 独有 | 97 条（ZN:47, NI:16, CU:14, AL:11） | — |
| Main 独有 | — | 652 条（WR:276, pb_:70, 金属:306） |
| 共有但字段冲突 | 928 条中 519 条有字段差异 | |
| 结论 | **不具备直接合并条件** | |

---

### ④ 是否识别出交接文档没有记录的规则缺口？

**结论：识别出 8 项规则缺口，逐条列出如下。**

#### 缺口清单

| # | 缺口描述 | 严重度 | 影响 |
|---|----------|--------|------|
| **G1** | **PB 原始修正文件的 B/C 级条目去向未文档化** | 🔴 高 | 46 份修正文件中，同花顺 AI 标注的 ⚠️B 和 ❌C 条目（估计 200-400 条）被丢弃，无存档、无说明。若需回溯"为什么某指标未注册"，当前无法回答 |
| **G2** | **62 条注册态指标 api_cache.db 拉取状态未跟踪** | 🟡 中 | 旧 DSH-B 完成注册后，api_cache.db 数据尚未拉取（STATUS.md 已记录"待拉取"）。旧 session 结束前是否曾部分拉取？当前无法追溯。需 FT 主脑确认 |
| **G3** | **PB 标签错乱的修复方案未决策** | 🔴 高 | v3.49 changelog 错误声称 PB correction 实际注册 CU/AL/NI/SN/ZN。changelog 错误本身未修正，PB 70 条指标仅存于 Main。缺少修复决策记录 |
| **G4** | **data-harbor 归档规范执行无证据** | 🟡 中 | ROLE_DEF §六.2 要求"所有实验产出归档至 data-harbor"，但本地无 data-harbor 目录。旧 DSH-B 可能仅在记忆中使用过该规范而未落盘。新 DSH-B 将严格遵守 |
| **G5** | **changelog version/v 键名不一致无统一规则** | 🟢 低 | v3.49 的 changelog 中，entry #0 使用 `version` 键，#1-#25 使用 `v`，#26-#27 又用 `version`。无统一命名规范文档 |
| **G6** | **LI 指标 zhji_id 缺失 23 条（Win 侧空 {}）的处置决策缺失** | 🟡 中 | Win 侧 23 条 LI 指标 zhji_id 为空 `{}`，Main 侧有真实 ID（部分为 a10172975 等 GFEX 格式）。无文档说明这些 LI 指标是故意留空还是遗漏 |
| **G7** | **B/C 级过滤条目的后续处理流程缺失** | 🟡 中 | 同花顺 AI 标注为 ⚠️B（待验证）和 ❌C（不合格）的条目，在 `correction_extract_report.json` 中被完全跳过。没有"备用库"机制记录这些条目的来源、原因、后续激活条件 |
| **G8** | **旧 DSH-B 本地草稿的 session 隔离无存档机制** | 🟢 低 | 旧 DSH-B 各 session 的中间草稿不跨 session 继承，也无主动存档机制。如某 session 生成了半成品表格或清洗脚本但未 git commit，当前 session 不可见 |

---

## 三、自检结论

| 项目 | 状态 | 说明 |
|------|------|------|
| 交接资产完整性 | ⚠️ **基本完整** | 核心文件全在，但 data-harbor 缺失、旧 session 草稿不可追溯 |
| 格式兼容规则理解 | ⚠️ **基本理解** | 3 种表格格式已掌握，但 B/C 级过滤标准需 FT 主脑补充 |
| zhji_id 匹配规则 | ✅ **完全掌握** | Step1→Step4 全流程、阈值、别名映射、ID 格式 |
| 分支分叉背景 | ✅ **完全掌握** | Win v3.50(1025) vs Main v3.83(1580)，结构性分叉，不可直接合并 |
| 规则缺口识别 | ⚠️ **8 项缺口已识别** | 含 3 项 🔴 高严重度（B/C 级去向、PB 标签错乱修复、PB 标签错乱修复） |

### 自检结论判定

**自检状态：⚠️ 条件通过**

- ✅ 资产完整性达标（核心文件全在）
- ✅ 规则理解达标（匹配规则、分支背景完全掌握）
- ⚠️ 发现 8 项规则缺口，其中 3 项需 FT 主脑明确裁决
- ❌ **在 FT 主脑确认上述缺口处置方案前，不建议进入阶段 2**

### 阶段 2 准入条件

待 FT 主脑回复确认后，以下 3 项可解锁阶段 2：

1. **确认 B/C 级过滤条目处置方案**（G1/G7）：废弃封存？保留备用库？还是需追溯？
2. **确认 62 条注册态数据拉取状态**（G2）：已有部分拉取？全未拉取？
3. **确认 PB 标签错乱的修复方向**（G3）：是否需修正 changelog？PB 70 条是否计划迁移至 Win？

---

## 四、红线声明

- ✅ 本阶段全程只读，未修改 `data/indicators_v1.json`、`scripts/chart_kits.py`、`data/tree_config.json`、门禁脚本
- ✅ 未提交 main 分支任何修改
- ✅ 未修改回测原始数据（`回测/`、`li_nonlinear_lgb/` 下 CSV 未触碰）
- ✅ 未隐瞒发现的资料缺失与规则缺口，已显性上报 8 项
- ⚠️ 阶段 2 须待 FT 主脑确认后方可启动

---

*回执结束。等待 FT 主脑确认后进入阶段 2。*
