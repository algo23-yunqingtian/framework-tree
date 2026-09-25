# PB 执行任务卡复审报告（PB_EXEC_TASK_20260913）—— ⏸️ 待执行回执（前置受阻）

> 复审日期：2026-09-14
> 分支：`origin/indicator-correction-win` · HEAD `fdd1466`
> 工单：`task_queue/to_B/PB_EXEC_TASK_20260913.md`（只读审计任务）
> 审计模式：**全程只读**。未修改任何源码、未写入 `indicators_v1.json`、未落库、未 push。全部提取经 `git archive` / `git show` 落地 `/tmp/pbaudit/` 后交叉比对。

---

## 〇、总结论

| 项 | 实测 | 判定 |
|---|---|---|
| Dsharnes-B PB 执行回执 | **未提交**（`fdd1466..win` 提交数 = **0**） | 🔴 复审前置条件未达成 |
| 新增 72 条 PB 指标注册 | `pb_` 精口径 = **0 条**；`name`含"铅" 85 条且 `_nodes` **全为空** | ⏸️ 无对象可核对 |
| 产业链节点覆盖完整性 | 应有 30 节点 / 有效发散 **24** / 缺 **6**（5.1-5.3、7.1-7.3） | ✅ 与前轮一致（缺口未变） |
| 门禁门禁（verify_render ≥170/224、check_html 168/223） | 静态基线**未变**，仍为 `5cd6da3` 复核值 | ✅ 已达标（无回退） |
| 幻觉过滤规则复核 | 135 行实测；**5 条跨品种命中经人工复核全部为误报/合理参照** | ✅ 真幻觉 0 条（声明成立） |
| P2 低优缺陷 | 2 项均复现，**不阻断** | 🟢 登记 |
| **本次复审结论** | — | **⏸️ 待 Dsharnes-B 执行回执（前置受阻），未编造"通过"** |

**核心状态**：工单第 2 条要求"收到 Dsharnes-B 推送的 feedback 回执后，执行只读复审"。经全分支核查，任务卡发放（`fdd1466`）之后 **win 分支无任何新提交**，`task_queue/feedback/` 无 PB 执行回执，`analysis/iwencai/PB/decision_*.md` **0 个**，`step3_register_plan.json` 仍缺 `pb` 键。即 **Step2/3/4 尚未开始或尚未回传**，本次无"新增 72 条注册信息"可核对。

按协作纪律，**不凭空生成"复审通过"**——结论标记为「前置受阻·待执行回执」，工单保持暂停。

---

## 一、前置条件核查（实测）

### 1.1 win 分支提交扫描（`fdd1466` 之后）

```
fdd1466  [DOC] PB流水线人工放行通知 + Dsharnes-B执行任务卡推送至to_B   ← 分支 HEAD
5cd6da3  fix(F3+U2+U4): 复审阻断缺陷修复
8b513fc  [DOC] 三次复审报告(审267614d·待二次修复)
```

- `git rev-list fdd1466..origin/indicator-correction-win --count` = **0**
- 本地亦无 `/tmp/wt_*` 临时 worktree 检出该分支

### 1.2 队列回执核查

| 队列 | 内容 | 是否含 PB 执行回执 |
|---|---|---|
| `task_queue/to_A/` | 仅 `.gitkeep` | ❌ 无 Dsharnes-B→A 执行通知 |
| `task_queue/to_B/` | `PB_EXEC_TASK_20260913.md`（本工单）+ `PB_PIPELINE_TASK_20260913.md` | ❌ 仅任务卡，无回执 |
| `task_queue/feedback/` | 10 份审计交付物 + 旧回执 | ❌ 无 PB Step2/3/4 执行报告 |

### 1.3 产物存在性核查（Step2/3/4 逐项）

| 期望产物 | 实测 | 状态 |
|---|---|---|
| Step2 `analysis/iwencai/PB/decision_*.md`（30 节点） | **0 个** | ❌ 未产出 |
| Step3 `step3_register_plan.json` 的 `pb` 键 | 缺（by_metal 仍仅 zn/ni/si/sn/li） | ❌ 未产出 |
| Step3 `step3_final.json` PB tier 分布 | 无 PB 条目 | ❌ 未产出 |
| `indicators_v1.json` PB 注册 | version **3.49 未变**（`updated` 2026-09-13 18:36，早于任务卡；`change`="CU/AL/五金属 B级批量注册 (+0 new)"，**与 PB 无关**） | ❌ 未落库 |

**结论**：Dsharnes-B 的 PB 执行工作**尚未开始或未回传**，无任何证据表明 Step2/3/4 已推进。

---

## 二、复审清单基线（回执到达后逐项执行，均为可复算项）

### 2.1 Step2 取舍清洗（30 节点）

- [ ] `analysis/iwencai/PB/decision_*.md` 文件数 = **30**（2.1-2.6 / 3.1.1-3.1.5 / 3.2.1-3.2.4 / 4.1-4.5 / 6.1-6.4；8.1-8.3 按公告不做图表，排除）
- [ ] 图表命名混入清洗：本报告实测 **31 处**图表词残留（见 §五），须改写为指标全名，去除「时序图/联动图/复合图/散点图/三面板」等形态词
- [ ] 派生形态不单列：本报告实测 **10 处**（含 `3.1.1#1 当季同比变动量` 确系派生形态，须并入原始指标呈现方式）
- [ ] 空表节点 **2.4 / 2.6**（文件存在但 0 条指标）：需补发散或明确标注「无数据源」
- [ ] 每节点 1 正主指标，且**禁止串用他页正主**（如 i18 铅锭社库=4.3 正主、j25_tc=2.5 正主）

### 2.2 Step3 知几分层匹配

- [ ] `step3_register_plan.json` 补 `pb` 键，by_metal 由 5 品种 → **6 品种**
- [ ] A/B/C 分层用 `score>=4→matched` 阈值（与 U1 修复后口径一致）
- [ ] **禁止直接写 `indicators_v1.json`**——注册计划只存中间产物，落库须主脑批准
- [ ] 知几 ID 前缀校验：PB 指标 key 应采用 `pb_` 前缀（当前全库 `pb_` 前缀 = **0 条**，现有 85 条 PB 为 `i1/i2/…` 旧人工编号，属不同命名体系，需在回执中说明两套命名如何合并）

### 2.3 Step4 三类差异比对

- [ ] 基准已切换：**废弃旧 99 条定稿基准**，改用「实测 70 条 + `_nodes` 非空」——⚠️ 本报告实测该子集为 **85 条**（`name`含"铅"口径），且 **85/85 的 `_nodes` 全为空**，即"70 条 + `_nodes` 非空"交集实测 = **0 条**。基准口径需在回执中重新核定，否则会像前轮一样产生系统性误判
- [ ] 三类差异（新增/冲突/缺失）以 Step2 新基准为对照
- [ ] 建页改 HTML 走 PR，不直接落 `main`

---

## 三、门禁基线核验（只读复测）

门禁脚本随分支存在：`scripts/check_html.py`（57 KB）、`scripts/verify_render.js`（26 KB）、`scripts/reclaim.py`。因 Step2/3/4 未开始，门禁产物无变化，沿用 `5cd6da3` 四次复审实测值（`task_queue/feedback/REVIEW_5CD6DA3_F3U2U4_20260913.md` §二）：

| 门禁 | 实测 | 工单要求 | 判定 |
|---|---|---|---|
| `verify_render` | **170/224**（由 140 回补 30 页） | ≥170/224 | ✅ 达标 |
| `check_html` | **168/223** | 基线 168/223 | ✅ 持平 |

- 54 页 FAIL 为 zn/ni/sn/al/cu 历史存量，非 PB
- ⚠️ **本基线未经本轮重跑**：`verify_render` 需 jsdom 环境且会执行渲染，为避免产生 `docs/` 报告文件覆盖（只读审计纪律），本轮以 `git archive` 提取脚本 + 前轮实测值交叉确认。回执到达后须**在回执 commit 上重跑两道门禁**，确认无回退。

---

## 四、P2 低优缺陷登记（复现确认，不阻断工单）

### P2-1 `pb_stock_v2.html` 5 处 `echart_p4x` 旧命名 —— 🟢 复现

```
__tgl 引用（旧命名）: echart_p41_c1 / p42_c6 / p43_c9 / p44_c11 / p45_c15  ← 共 5 处
div id             : echart_pb_41_c1 / pb_42_c6 / pb_43_c9 / pb_44_c11 / pb_45_c15
```

- div 已用新命名，`__tgl` 仍指向旧命名 → **该页 5 个季节按钮点击失效**
- 该页**不在 `check_html` PAGES 注册表、不在 `verify_render` 224 页清单**，故不计入门禁（这也是它一直没被抓到的原因）
- 严重度：🟢 低（历史遗留页，非 PB 主线）；建议随下一轮页面治理一并修

### P2-2 `scripts/_fix_all.py:254` `EXCHANGE_WHITELIST` 硬编码残留 —— 🟢 复现

```
scripts/_fix_all.py:254   EXCHANGE_WHITELIST = { ... }   ← 残留
scripts/task3_hallucination_clean.py:40   CROSS_EXCHANGES = { ... }   ← 唯一生效约束（黑名单）
```

- `git grep -l "_fix_all"` 全库唯一命中是**审计报告本身**（`REVIEW_5CD6DA3_F3U2U4_20260913.md`）→ **零流水线引用 = 死代码**
- 白名单（允许集）与黑名单（禁止集）语义冲突已在 `task3_hallucination_clean.py` 消除，残留不影响运行逻辑
- 建议随 `_fix_all.py` 一并清理

### P2-3（新增登记）`poll_dsharnes_audit_v4.sh` 唤醒链路在本机不存在

- `~/.hermes/scripts/` 无此脚本，cron 列表亦无对应 job
- 工单第 1 条"由 `poll_dsharnes_audit_v4.sh` 触发唤醒"**无法自动执行**，本轮为手动只读核查
- 若该脚本在另一台 Hermes（Dsharnes-B 侧），需确认其推送目标为 `task_queue/feedback/`；否则唤醒链路是断的，回执到达靠人工

---

## 五、幻觉过滤规则复核（135 行实测 + 人工分级）

对 main 工作区 **27 份 PB divergence**（win 分支上 PB divergence = **0**，不合并进 win）按 tab 分隔格式逐行扫描，命中 `CROSS_EXCHANGES["PB"] = ["COMEX","GFEX"]` 黑名单与跨品种商品名规则。

### 5.1 总量核对

| 维度 | 任务卡声明 | 本轮实测 | 判定 |
|---|---|---|---|
| 表格指标行 | 135 | **135** | ✅ 一致 |
| 跨品种/非铅交易所幻觉 | 0 条 | 关键词命中 **5 条**，人工复核后 **真幻觉 0 条** | ✅ 声明成立（5 条全部为误报/合理参照） |
| 图表名混入 | 45 处 | **31 处** | 🟡 口径差异（本轮关键词集更窄，仅 6 词；实际待清洗量以 Step2 为准） |
| 派生形态命中 | 55 处（真混入 2-4） | **10 处**（扫第 3 列"包含指标"） | 🟡 口径差异（前轮扫整行含说明文字，见下） |

### 5.2 跨品种关键词 5 条命中的逐条分级（全部为误报/合理参照）

| 文件 | 条目 | 命中词 | 判定 | 依据 |
|---|---|---|---|---|
| `2.5` | #4 锌铅比价·价差估值分位图 | 锌 | ✅ **合理跨金属参照** | 比价/价差本质就是跨品种关系，与 `pb_24 铅锌比价` 同属合规参照（AGENTS.md §3.5「保留+声明」）；节点 2.5 本身即"比价估值"，非串台 |
| `3.1.1` | #1 海外样本矿企铅精矿产量 | 锌 | ⚪ **误报** | 命中在说明文字（矿企数据段），指标本体为铅精矿产量，无锌指标混入 |
| `3.1.1` | #2 产量指引 vs 实际兑现 | 锌 | ⚪ **误报** | "Antamina锌2027指引" 为海外矿企产能指引背景说明，非独立指标条目 |
| `3.1.1` | #4 海外铅矿产量扰动归因 | 锌 | ⚪ **误报** | 同上，扰动归因说明文字，指标本体为铅矿扰动分类统计 |
| `3.1.3` | #5 铅矿含银/含铜伴生结构 | 铜 | ✅ **业务真实存在** | "铜矿伴生铅精矿产量" 是铅供给侧的真实伴生矿结构（铅矿高度伴生银/铜），属 3.1.3 节点正确内容，不是幻觉 |

**教训复核**：跨品种关键词命中**必须人工看上下文**——本轮 5/5 为误报或合理参照，与前轮结论一致，但**关键词级命中数是 5 而非 0**，审计报告应记录原始命中数 + 人工判定，而非只写最终 0。

### 5.3 图表名混入 31 处（Step2 须清洗，前 8 处样例）

```
2.1#1  量价仓三面板联动图
2.2#3  沪铅基差贴水率时序图
2.3#2  LPRM溢价·沪伦比·进口盈亏复合图
2.3#5  LME与沪铅绝对价格净值联动图
3.1.1#2 产量指引 vs 实际兑现·完成度散点图
3.1.2#2 全球·中国·海外产量双轴时序图
3.1.2#5 主要国家产量指引 vs 实际·年度散点图
3.1.3#1 国内铅精矿月度产量·SMM样本产量复合图
```

清洗方向：图表词（时序图/联动图/复合图/散点图/三面板/柱状图/堆叠图）全部剥离，改写为指标全名，如 `LME：铅：期货库存（日）`。

### 5.4 派生形态 10 处（Step2 须并入原始指标）

其中 `3.1.1#1` 的「②当季同比变动量」是**确认的派生形态单列**（违反同花顺规则 2「独立基础指标原则」），须并入「①海外样本矿企季度铅精矿产量」的呈现方式，不单列。

### 5.5 ⚠️ 2.4 / 2.6 空表确认

| 文件 | 行数 | 指标条目 | 判定 |
|---|---|---|---|
| `divergence_2.4.md` | 140 | **0** | ⚪ 只有 prompt + 搜索日志，问财未输出表格 |
| `divergence_2.6.md` | 181 | **0** | ⚪ 同上 |

与前轮"⚠️ 空表"警告一致。Step2 处理这两个节点时无素材可用，需**重新发散**（席位数据知几无收录，属已知难点）。

---

## 六、节点覆盖完整性校验

`data/tree_config.json`（33 节点，PB 全品种覆盖）与 main 工作区 27 份 divergence 比对：

| 板块 | 应有 | 有效发散 | 缺口 |
|---|---|---|---|
| 2 价格信号 | 6 | 4（2.1/2.2/2.3/2.5） | **2.4、2.6 空表** |
| 3 供给 | 9 | 9 | — |
| 4 库存 | 5 | 5 | — |
| 5 需求 | 3 | **0** | **5.1 / 5.2 / 5.3** |
| 6 进出口 | 4 | 4 | — |
| 7 成本利润 | 3 | **0** | **7.1 / 7.2 / 7.3** |
| 8 供需平衡 | 3 | 3（不做图表） | ⛔ 按公告排除 |

- **应有 30 节点（排除 8.1-8.3）→ 有效 24 → 缺 6**（5.1-5.3 需求、7.1-7.2.3 成本利润），另有 2.4/2.6 空表需补发散，**实际需发散 8 个节点**（6 缺 + 2 空表）
- ⚠️ 与前轮"缺 6 个节点"的口径差异：前轮未把 2.4/2.6 空表计入缺口。本次建议按 **8 个待发散** 排期，同花顺通道约 8×(50s 冷却+生成) ≈ 25-40 分钟

### 分支分叉状态（前置信息核验）

```
f20acb3 (main, 含 27 份 PB divergence)  ——非祖先——  indicator-correction-win
  - git merge-base --is-ancestor f20acb3 origin/indicator-correction-win  → exit 1
  - win 分支 PB divergence = 0；win 全库 divergence = 198
```

27 份 PB divergence 仅存 `origin/main`，**未合并进 win 分支**，与工单前置信息一致 ✓。Dsharnes-B 若要在 win 侧处理，需按任务卡 §5 建议走 `task/*` 分支新发散 + Step2/3 产物存 `analysis/` + 落库走 PR，**不可直接 rebase win→main**。

---

## 七、本次复审结论与后续

**⏸️ 工单保持暂停。** 解锁条件：

1. Dsharnes-B 提交 PB Step2/3/4 执行回执至 `task_queue/feedback/`（或按角色定义前缀 `[B]` 推送）
2. 回执包含：`decision_*.md` 文件数、`step3_register_plan.json` 的 `pb` 键、Step4 三类差异比对结果、基准口径核定说明（70 条 vs 85 条差异）
3. 回执 commit 上重跑 `check_html` + `verify_render` 确认无回退
4. 收到明确启动指令

**本轮已完成（全部只读）**：前置核查 / 产物存在性核查 / 门禁基线核验 / 幻觉过滤 135 行复核 + 5 条人工分级 / 节点覆盖 30 节点校验 / P2 缺陷 2 项复现 + 1 项新增登记 / 分支分叉核验。

**未做的事**（遵守只读约束）：未写 `indicators_v1.json`、未落库、未改任何源码/脚本/HTML、未 push、未 checkout win 分支。

---

## 附：复审取证命令（可复算）

```bash
cd /home/ubuntu/framework-tree
# 1) 前置：分支 HEAD 与新提交数
git fetch origin --prune
git log --oneline origin/indicator-correction-win -3
git rev-list fdd1466..origin/indicator-correction-win --count        # 0 = 无回执

# 2) 只读提取（不 checkout）
git archive origin/indicator-correction-win data/indicators_v1.json data/tree_config.json \
    pb_stock_v2.html scripts/check_html.py scripts/verify_render.js | tar -x -C /tmp/pbaudit

# 3) PB 指标库状态
python3 -c "import json; d=json.load(open('/tmp/pbaudit/data/indicators_v1.json')); \
  i=d['indicators']; print('version',d['version'],'total',len(i)); \
  print('pb_前缀', sum(1 for k in i if k.startswith('pb_'))); \
  print('name含铅', sum(1 for v in i.values() if '铅' in str(v.get('name',''))))"

# 4) P2-1 旧命名
grep -oE "echart_p4[0-9]_c[0-9]+" /tmp/pbaudit/pb_stock_v2.html | sort -u

# 5) P2-2 死代码
git grep -n "EXCHANGE_WHITELIST" origin/indicator-correction-win -- 'scripts/*.py'
```
