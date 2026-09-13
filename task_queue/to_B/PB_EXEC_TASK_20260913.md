# 【任务卡·执行授权】PB 发散流水线 Step2/3/4 落库

> 生成：2026-09-13 · 审计侧（爱马仕）· 分支 `indicator-correction-win` @ `5cd6da3`
> 受众：Dsharnes-B（CU-Agent，写权限线）
> **性质：执行任务卡**（区别于 `PB_PIPELINE_TASK_20260913.md` 的「材料交接·暂不执行」任务书）
>
> ⚠️ **状态（2026-09-13 更新）：✅ 已人工放行。** 解锁条件 1-5 全部满足，**Dsharnes-B 可立即接手执行 Step2/3/4**。
>
> **放行说明**：主脑已于 2026-09-13 下达放行指令，本卡由主脑审计侧 push 至 `origin/indicator-correction-win` 的 `task_queue/to_B/`（Dsharnes-B 收件箱）。收到本卡即视为执行授权。

---

## 0. 一句话状态

**F3 两项 P0 回归已修复、门禁已回绿、四次复审已通过——PB 流水线解锁条件 1-4 全部满足，可以接手执行 Step2/3/4 落库了。** 解锁条件 5（主脑明确放行）是最后一道人工闸门。

---

## 1. 前置状态核实（审计侧已实测，Dsharnes-B 可直接采信）

| 项 | 实测 | 依据报告 |
|---|---|---|
| F3-回归1 `__tgl` 引号嵌套 | **40 → 0** ✓ | REVIEW_5CD6DA3 §二① |
| F3-回归2 `getElementById` 旧命名 | **90 → 0** ✓ | REVIEW_5CD6DA3 §二② |
| `verify_render` | **170/224**（≥170 达标，由 140 回补 30 页）| REVIEW_5CD6DA3 §二③ |
| `check_html` | **168/223**（-1 为预期收紧，非退化）| REVIEW_5CD6DA3 §二④ |
| U2 SHFE 别名 | 本次真实新增 **9 条**（+84 行）| REVIEW_5CD6DA3 §三 |
| U4 死代码 `EXCHANGE_WHITELIST` | 已清理，仅留 `CROSS_EXCHANGES` 黑名单 | REVIEW_5CD6DA3 §四 |
| 四次复审结论 | **✅ 通过** | REVIEW_5CD6DA3 §一 |
| `indicators_v1.json` | version **3.49 未变**，PB 指标 **0 条**（仍锁死）| REVIEW_5CD6DA3 §六 |

### `check_html` 169→168 的 -1 归因（已确认非功能退化）

唯一净增 FAIL 页是 `pb_32_3_regen_supply` + `pb_stock_v2`，触发原因是 `5cd6da3` 给 `check_html.py` 新增了 6 项 JS 引用一致性检查，**首次静态检出**了 `pb_stock_v2` 5 处 `__tgl` 旧命名（`echart_p4x_c*` 非 `echart_pb_4x_c*`）与 `pb_32_3` 命名异常。这是**门禁变严抓到了真缺陷**，不是功能回退。其余 54 页 FAIL 与上轮完全一致（均为 zn/ni/sn/al/cu 历史存量，非 PB）。

---

## 2. 执行范围（Step2/3/4，你负责；indicators_v1.json 落库需主脑批准）

### Step 2 —— 取舍改写清洗（基于已审计的 27 个 divergence）

- **基准切换（重要）**：**废弃旧 99 条指标定稿基准**，改用**实测 70 条 + `_nodes` 非空**作为 Step4 差异比对新标准。
  - 原因：任务书撰写时 HEAD=`78631cc`，关于 PB 现状的描述已过时——任务书称 99 条，实测 `indicators_v1.json` PB 子集仅 **70 条**，差额 29 条（疑含 `pb_prompt/定稿_v2~v4.md` 未入库条目）。
  - **口径备注**：报告中的「PB=70 条」特指 **PB 旧人工指标子集**（`id` 以 `pb_` 开头或 `name` 含"铅"），**不是** `indicators_v1.json` 全库总条数（全库实测 **964 条**，含五金属）。避免后续混淆。
- 对 Step1 已审计的 **135 行原始发散结果**执行：
  - **图表命名混入 45 处**：改写为指标全名（如 `LME：铅：期货库存（日）`），去除「联动图/复合图/时序图」等图表类型词。
  - **派生形态真混入约 2-4 条**（`当季同比变动量` 类）：归入其原始指标的呈现方式，不单列。
  - 数据源清单、知几命中样例见审计报告 §二。
- 产物写 `analysis/iwencai/PB/decision_*.md`（30 个节点）。

### Step 3 —— 知几分层匹配

- 知几 API **在线可用**（已验：`search "SHFE铅主力合约收盘价"` → 9 条命中，含 Mysteel `FU00015390` + SMM `a10118360`）。
- 按 `step3_judge_rules.py` `score>=4→matched` 阈值分层 A/B/C。
- `step3_register_plan.json` 补 `pb` 键（当前 by_metal 仅 zn/ni/si/sn/li，**缺 pb**）。
- **不直接写 `indicators_v1.json`**——注册计划先存中间产物，落库由主脑批准。

### Step 4 —— 三类差异比对

- 以 Step2 新基准（实测 70 条 + `_nodes` 非空）为对照，对 27 个 divergence 做三类差异比对：新增/冲突/缺失。
- 建页改 HTML（`pb_*.html`）属源码改动，**走 PR 流程**，主脑 review 后 merge。

---

## 3. 节点覆盖现状（决定 Step2 工作量）

| 状态 | 节点 |
|---|---|
| ✅ 已有 divergence（27 个）| 2.1-2.6 / 3.1.1-3.1.5 / 3.2.1-3.2.4 / 4.1-4.5 / 6.1-6.4 / 8.1-8.3 |
| ❌ **缺失（需新发散）** | **5.1 / 5.2 / 5.3（需求）、7.1 / 7.2 / 7.3（成本利润）** |
| ⚠️ 空表 | 2.4 / 2.6（文件存在但 0 行表格指标）|
| ⛔ 应排除 | 8.1-8.3（板块 8 按任务书不做图表）|

> 有效应发散 30 节点 = 27 - 3（8.x）+ 0；当前有效 24，缺 6。
> 6 个缺失节点补发散需同花顺浏览器通道，约 6×(50s 冷却+生成)≈20-30 分钟。

---

## 4. 幻觉审计统计（Step1 已审计，你可直接采信）

| 维度 | 结果 |
|---|---|
| 跨品种/非铅幻觉（COMEX/GFEX/碳酸锂等）| **0 条 / 135 表格指标行**（优于五金属基线 6.9%）|
| 图表命名混入 | 45 处（需 Step2 清洗）|
| 派生形态命中 | 55 处，复核后真混入约 2-4 条 |
| 数据源分布 | LME 331 / SMM 193 / Mysteel 82 / 海关 41 / 同花顺 28 / ILZSG 18 / SHFE 10 / 生意社 6 |

---

## 5. git 基线处理（你开工前必做）

```bash
git fetch origin
# win 分叉自 f73bccc，与 main 双向分叉（main 领先10，win 领先8）
# PB divergence 27 个在 main 上（f20acb3），win 分支上 PB=0（未 rebase）
# 决策：不要直接 rebase win 到 main（会引入10提交、可能冲突）
# 不要反向 rebase（SOUL.md 红线：禁止把 win 审计交付物误提交 main）
# 建议：在 task/* 分支上新发散 6 节点，Step2/3 产物存 analysis/，落库走 PR
```

- `indicators_v1.json` 全库 964 条 / version 3.49 —— 开工前确认基线，改公共文件前先 `git pull` 看主脑最近改动。
- 改产物文件需同步 `STATUS.md`（pre-commit hook 强制）。
- push：`GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin HEAD:<你的分支>`。

---

## 6. 放行闸门（人工）

**本卡生成 ≠ 已启动。** Dsharnes-B 收到本卡后：

1. 若已收到主脑「开始执行」放行指令 → 按 §2 Step2/3/4 执行，产物走 PR。
2. 若未收到放行指令 → **保持暂停**，勿动 `indicators_v1.json`、勿建页。
3. 执行完成后回传 `task_queue/to_A/`，主脑复审 `verify_render`/`check_html`/指标质量/幻觉。

---

## 7. 交付物索引

| 文件 | 内容 | 状态 |
|---|---|---|
| `task_queue/feedback/REVIEW_5CD6DA3_F3U2U4_20260913.md` | 四次复审（✅ 通过）| 已入库 |
| `task_queue/feedback/PB_DIVERGENCE_AUDIT_20260913.md` | 6 节点发散审计（⏸️ Step2/3/4 未执行）| 已入库 |
| `task_queue/to_B/PB_PIPELINE_TASK_20260913.md` | 完整版任务书（181 行，材料交接）| 已入库 |
| **本文件** | **执行任务卡（F3 已修，可接手 Step2/3/4）** | **本次生成** |

---

## 8. 红线

- 主脑审计侧全程只读，未碰 `indicators_v1.json`、未建页、未发通知触发执行。
- 执行放行由主脑人工下达，本卡不自动触发 Dsharnes-B。
