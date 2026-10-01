# T2.3 多 Canonical 冲突解决：三套候选方案 + 推荐

> 任务：`DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN` · 分支 `feature/v85-chart-template`
> 产物：`multi_canonical_conflicts_165.csv`（165 条冲突清单，20 列）、`multi_canonical_conflict_classification.csv`（A/B 分类 + 处置建议）
> 生成脚本：`generate_conflict_classification.py`（可重复运行，无外部 API）
> 硬约束：未修改 `indicator_alias_library.csv` / `indicators_v1.json` / `build_alias_library.py`

---

## 0. 结论摘要

| 项 | 值 |
|---|---|
| BLOCK 规模 | **165 个 `alias_norm` 指向 >1 个原子键**（V7 severity=BLOCK） |
| 涉及原子键 | **583** 个，**全部互不相同**（0 个原子键跨行复用） |
| 全部标记 | `relation=canonical_conflict` × 165、`review_flag=manual_review` × 165、`review_priority=P0_manual` × 165、`confidence=0.55` × 165 |
| 根因 | **`indicators_v1` 重复建号**，非别名库自身错误（详见 §1.4） |
| A 类（重复注册，可自动合并） | **47 行（28.5%）**，116 原子键 → 合并至 43 唯一 base |
| B 类（真实不同指标，须裁决） | **118 行（71.5%）**，467 原子键 |
| 推荐 | **方案二（人工裁决）为主干 + 方案三（拆分表示）为前置 + A 类自动合并为预清洗** |
| 推荐总工时 | **≈ 4.75 人天**（预清洗 0.5 + 裁决 2.1 + 结构修复 2.15） |
| 导入现状 | 165 条**未进入**自动写入集（V9：`multi_key=0`、`single_key=2502`、`alias_writes_planned=2253`）→ BLOCK 是"卡住"而非"写错" |

---

## 1. 现状与根因

### 1.1 规模

| 口径 | 值 |
|---|---|
| 别名库总行 | 4643 |
| distinct `canonical_name`（全库行 scope） | 1405 |
| distinct `canonical_name`（V7 canonical-form scope） | 1239 |
| distinct `alias_norm` | 2882 |
| **`alias_norm` → >1 原子键（BLOCK）** | **165** |
| `canonical_name` → >1 原子键（全库行 scope） | **327**（1158 原子键） |
| `canonical_name` → >1 原子键（V7 scope） | 170 |
| `alias_is_other_canonical` | **0**（V7 原子键修正后，此前"165 行互指环"系复合键比较口径错误） |
| `alias_norm_is_self_canonical` | 1230 |

**已确认的复合键陷阱**：复合键（`|` 连接）是"多目标"而**非歧义**。V7 修正后 `alias_is_other_canonical=0`，别名互指环不存在。

### 1.2 键数分布

| 原子键数 | 行数 | 累计 |
|---|---|---|
| 2 | 75 | 45.5 % |
| 3 | 36 | 67.3 % |
| 4 | 20 | 79.4 % |
| 5 | 11 | 86.1 % |
| 6 | 7 | 89.7 % |
| 7 | 4 | 91.5 % |
| 8 | 4 | 93.3 % |
| 9 | 3 | 95.2 % |
| 10 | 1 | 95.8 % |
| 11 | 1 | 96.4 % |
| 12 | 2 | 97.6 % |
| **16** | 1 | **100 %** |

**长尾极重**：`A-03858 精炼镍：库存：中国：27家样本仓库（周）` 映射 **16** 个原子键（`ni_43_inv` / `ni_44_inv_2..6` 等）；`A-00054 GFEX：工业硅：主力合约：单边交易：持仓量（日）` 映射 **12** 个。

### 1.3 来源结构

| 维度 | 分布 |
|---|---|
| `variety_family` | SI 36、NI 31、LI 27、SN 22、ZN 20、CU 6、AL 5、PB 5、混合/未识别 13 |
| `alias_type` | canonical 81、mixed_script 45、cross_report_synonym 19、unit_variant 11、numeric_code 8、suffix_variant 1 |
| `alias_source` | INDICATORS_V1_NAME 138（**83.6 %**）、+THS_MATCHED 19、+THS_SERIES 7、+PDF_TEMPLATE 1 |
| `metric_noun` | 全部 165 非空；43 行为 `未识别`，其余为真实度量词（产量 25、持仓量\|持仓 12、库存 11 …） |

> **只有 2 行的原子键前缀跨了不同字母段**（`A-00524 SMM铅锭五地社库 → i18/i3`、`A-03113 工业硅社会库存 → si/wr227`），但这是键 ID 命名约定差异，**不构成真实跨品种冲突**。→ 165 条冲突**全部是同品种内部**的多指标问题。

### 1.4 根因：`indicators_v1` 重复建号（不是别名库错误）

关键证据链：

1. **全部 165 条冲突行**的 `canonical_name` 都落在"canonical_name → >1 原子键"的 327 个重复集合内（165/165 = 100 %）。
2. 反过来，327 个重复 canonical_name 中有 **162 个不产生 alias_norm 冲突**——因为它们经不同来源（alias / canonical 注册）进入，alias_norm 各异。
3. 全库 165 条冲突涉及 **583 个原子键，跨行复用数为 0** → 冲突**完全由行内**多键引起，不是跨行合并错误。
4. V4 分层：W1_可靠同义 2502、W2_存疑 380、W3_明确错误 27、W0_待注册 1734。**165 条冲突不在 W1 内**，全部被标 `manual_review`。

**结论**：别名库忠实地反映了 `indicators_v1` 中"同一 canonical_name 被建了多个 key"的事实。V7 的 BLOCK 是**正确拦截了一个上游数据缺陷**，而不是别名库自身的 bug。

> 这也解释了为何 165 条的 `confidence` 全部是 0.55（下限档）：构建管线已知其不可自动落定。

### 1.5 A/B 分类（`multi_canonical_conflict_classification.csv`）

原子键结构为 `<variety>_<seq>_<metric>[_qualifier…]`；剥离全部 `_N` 纯数字尾缀后比较：

| 类别 | 行数 | 占比 | 含义 | 处置 |
|---|---|---|---|---|
| **A_重复注册** | **47** | 28.5 % | 行内原子键仅 `_N` 尾缀差异 → 同一指标被重复建号 | **自动合并至 base** |
| B_真实不同指标 | **118** | 71.5 % | 存在不同 base → 真实不同指标 | 见细分 |
| └ 不同序号不同度量词 | 80 | 48.5 % | 口径完全不同（如 `si_21_openinterest` vs `si_26_percentile_openinterest`） | **人工裁决** |
| └ 同序号不同度量词 | 25 | 15.2 % | 同 seq 不同 metric（`al_41_lme_warrant` / `al_41_warrant` / `al_41_warrant_ratio`） | 人工裁决（按度量词择优） |
| └ 不同序号同度量词 | 12 | 7.3 % | 同 metric 不同 seq → 口径粒度/区域变体（`si_21_warrant` / `si_22_warrant` / `si_24_warrant`） | 人工裁决（建议保留最窄口径） |
| └ 同序号同度量词仅尾缀差异 | 1 | 0.6 % | 结构同 A | 自动合并 |

**处置汇总**：`auto_merge` 48 行 / 116 原子键；`manual` 117 行 / 467 原子键。

**A 类跨行 base 复用**：`zn_314_import`、`si_24_spot`、`ni_322_util`、`sn_22_premium` 各被 2 行共享 → 合并时必须跨行去重。

### 1.6 典型样例

| 类别 | alias_id | alias_norm | 原子键 | 问题定性 |
|---|---|---|---|---|
| A | A-00067 | `GFEX:碳酸锂:指数合约:收盘价(日` | `li_21_close \| li_21_close_2` | 重复建号 |
| A | A-00065 | `GFEX:碳酸锂:单边交易:持仓量(日` | `li_21_openinterest \| _2 \| _3` | 重复建号 ×3 |
| B | A-00058 | `GFEX:工业硅:单边交易:持仓量(日` | `si_21_openinterest_industrial_si \| si_26_percentile_openinterest_indu` | **绝对值 vs 分位数**，口径完全不同 |
| B | A-00066 | `GFEX:碳酸锂:基差(日` | `li_21_basis \| li_22_basis_carbonate_battery` | 通用 vs 电池级 |
| B | A-00061 | `GFEX:碳酸锂:主力合约:收盘价(日` | `li_21_close_front \| li_24_close_far \| li_24_close_near` | 近月/远月 |
| B | A-00542 | `USGS:精炼锌:消费进口量:美国(年` | `zn_314_import_3 \| zn_314_import_4` | 重复建号（但跨行共享 base） |
| B | A-00054 | `GFEX:工业硅:主力合约:单边交易:持仓量(日` | **12 个键** | 多口径混合 |

---

## 2. 三套候选方案

### 方案一 · 自动择优

**做法**：写评分器对每行 N 个候选原子键打分，自动选定唯一 canonical。候选评分维度：base 最短、seq 最小、metric_noun 匹配、原子键被引用次数、别名来源优先级（INDICATORS_V1_NAME > THS_MATCHED > PDF_TEMPLATE）。

| 项 | 评估 |
|---|---|
| 工时 | **2.5 人天**（评分器 1.0 + 幂等/回滚/审计 1.0 + 抽检 100 条 0.5） |
| 覆盖率 | 165/165 = 100 % |
| 精度 | A 类 47 行 ≈ 100 %；**B 类 117 行存在系统性误判风险** |
| 主要风险 | ①「不同序号不同度量词」80 行的评分维度**无法区分口径**（`si_21_openinterest` vs `si_26_percentile_openinterest` 在任何结构维度上都是平手）→ 必然按任意规则（如 seq 最小）择一，**系统性偏向某一口径**；② 误判不可见：一旦入库，`alias_norm → canonical` 变为单值，错误被永久固化；③ 会掩盖 §1.4 的上游重复建号缺陷 |
| 可回滚性 | 中（需保留原 composite key 与审计日志） |
| 与 T2.2 的关系 | 与 F2/F3 的 AMBIGUOUS 降级复核**语义冲突**：F2/F3 明确拒绝静默选键，方案一就是静默选键的"可审计版" |

### 方案二 · 人工裁决

**做法**：按 §1.5 的 A/B 分类，A 类自动合并（48 行），B 类 117 行由业务方逐行裁决，裁决结果写回别名库并固化审计轨迹。

| 项 | 评估 |
|---|---|
| 工时 | **2.1 人天**（裁决 1.6 + 入库校验 0.5） |
| 裁决工时明细 | 80 行「不同序号不同度量词」× 8 min = 10.7 h；37 行结构化 × 3 min = 1.9 h；合计 ≈ 12.6 h ≈ 1.6 人天 |
| 覆盖率 | 165/165 = 100 % |
| 精度 | 100 %（口径判断由领域专家作出） |
| 主要风险 | ① 裁决标准不一致（需先出 1 页裁决准则）；② 产出慢；③ 新增注册会继续产生同类冲突，需配套**准入规则** |
| 可回滚性 | 高（裁决记录可追溯、可重开） |
| 与既有流程的契合 | **165 行全部已是 `review_flag=manual_review` / `P0_manual`** → 人工裁决队列**已存在**，方案二是把它执行掉，而非新增流程 |

### 方案三 · 拆分别名条目

**做法**：把 1 行（`alias_norm → composite canonical_key`）拆成 N 行（每行一个原子键），别名库 schema 允许 `alias_norm` 非唯一。165 行 → **583 行**。

| 项 | 评估 |
|---|---|
| 工时 | **1.5 人天**（schema 变更 0.5 + 拆分脚本 0.5 + 校验 0.5） |
| 覆盖率 | 165/165（但**冲突并未消除**） |
| 信息损失 | **0** |
| 主要风险 | ① **拆分别名条目不等于解决冲突**——只是把"隐式 1:N"变成"显式 1:N"；② 拆分后 `resolve_canonical` 返回 N 值，若不配 T2.2 的 F2/F3，**会把 165 行的静默选键放大成 583 行的静默选键**；③ `alias_id` 唯一性、`alias_norm` 唯一索引、下游 1226 行"已在 IV1 name 内"的匹配逻辑都需同步 |
| 可回滚性 | 中（需保留原始 165 行） |
| 定位 | **表示层基础设施**，不是解决方案 |

### 2.x 方案对比矩阵

| 维度 | 方案一 自动择优 | 方案二 人工裁决 | 方案三 拆分别名条目 |
|---|---|---|---|
| 工时 | 2.5 人天 | 2.1 人天 | 1.5 人天 |
| 冲突是否真正消除 | 否（选一掩埋） | **是** | **否**（只显式化） |
| B 类 117 行精度 | **低**（结构维度平手） | **高** | 不适用 |
| 信息损失 | 高（165 行各丢 N−1 个候选） | 中（117 行各丢 N−1，A 类 0） | **0** |
| 误判可见性 | **差**（入库后固化） | 好（审计轨迹） | 好（结构可见） |
| 上游缺陷暴露 | **掩盖** | **暴露** | 暴露 |
| 依赖 | 无 | 业务方投入 | T2.2 的 F2/F3 |
| 与 F2/F3 一致性 | **冲突** | 一致 | 依赖 |

---

## 3. 推荐方案：**方案二 为主干，方案三 为前置，A 类自动合并为预清洗**

### 3.1 为什么不是纯方案一

117 行 B 类中 **80 行（48.5 %）属"不同序号不同度量词"**，在这类行上，所有结构维度（base 长度、seq 大小、metric_noun、引用计数）都**无法区分**候选口径——例如 `si_21_openinterest_industrial_si` 与 `si_26_percentile_openinterest_indu` 表达的是"持仓量绝对值"与"持仓量分位数"，两者语义正交。任何自动评分器必然退化为"按 seq 最小择优"这类任意规则，**系统性地把某一口径固化进生产库**。这是不可接受的风险。

### 3.2 为什么不是纯方案三

方案三**不消除冲突**，只把隐式 1:N 变成显式 1:N。且拆分后 `resolve_canonical` 返回 N 值，若不同时上 T2.2 的 F2（结构化返回）+ F3（AMBIGUOUS 降级复核），会把静默选键从 165 行**放大**到 583 行。方案三必须作为基础设施单独存在，不能作为"解决方案"单独交付。

### 3.3 为什么方案二 + 预清洗是最优

1. **精准匹配问题类型**：117 行 B 类是**口径语义判断**问题，只有领域知识能裁决；48 行 A 类是**数据缺陷**，可机械修复。混合处置 = 把人力用在真正需要人的地方。
2. **暴露而非掩盖上游缺陷**：§1.4 已确认 327 个 canonical_name 重复建号是根因。方案二会把"应保留哪个 key"的裁决显式记录，从而反向推动 `indicators_v1` 的重复建号清理（该项因 T4 硬约束本轮不可执行，但裁决记录就是清理清单）。
3. **复用既有流程**：165 行**全部**已是 `manual_review` / `P0_manual`，方案二不是新增流程，而是把已存在的队列执行掉。
4. **工时最低且精度最高**：2.1 人天 vs 方案一 2.5 人天，同时精度从"低"升到"100 %"。

### 3.4 执行步骤

```
阶段 0  前置（0.5 人天）
   0.1  方案三最小版：仅为 165 行补充 N 个原子键的独立记录，保留原 composite 行做对照
   0.2  同步 T2.2 的 F1（消除 resolve_canonical 崩溃，0.25 人时）
   0.3  产出裁决包：alias_norm + N 个 canonical_name + metric_noun + alias_type + 建议
         （multi_canonical_conflict_classification.csv 已具备）

阶段 1  预清洗（0.5 人天）
   1.1  A 类 48 行自动合并：剥离 _N 尾缀，47+1 行合并至 43 唯一 base
   1.2  跨行 base 去重：zn_314_import / si_24_spot / ni_322_util / sn_22_premium
   1.3  冲突数从 165 降至 117

阶段 2  人工裁决（1.6 人天）
   2.1  先出 1 页裁决准则（口径优先级：最窄地域 > 最窄合约 > 绝对值 > 分位数 …）
   2.2  80 行「不同序号不同度量词」逐行裁决（每行 8 min）
   2.3  37 行结构化裁决（每行 3 min）
   2.4  裁决记录固化：裁决人 / 时间 / 选定 key / 丢弃 key / 理由

阶段 3  入库与校验（0.5 人天）
   3.1  裁决结果写回别名库（canonical_key 变单值）
   3.2  重跑 alias_import_validation.py：V7 alias_norm_multi_canonical 应从 165 降至 0
   3.3  重跑 build_test_case_set.py + 488 条回放，确认 TP/FP 不回退

阶段 4  准入规则（持续）
   4.1  在 build_alias_library.py 的 ingest 阶段增加"同 canonical_name 多 key 拦截"
   4.2  把 bl_lint 的 43 条整词边界告警升级为阻断（配合 T2.2 的 F4）
```

### 3.5 工时汇总

| 阶段 | 工时 | 说明 |
|---|---|---|
| 阶段 0 前置 | 0.5 人天 | 方案三最小版 + T2.2 F1 |
| 阶段 1 预清洗 | 0.5 人天 | A 类 48 行自动合并 |
| 阶段 2 人工裁决 | 1.6 人天 | B 类 117 行 |
| 阶段 3 入库校验 | 0.5 人天 | 写回 + 重跑验证 |
| **合计** | **3.1 人天** | + T2.2 的 F2/F3/F4（6 人时 ≈ 0.75 人天）= **3.85 人天** |

> 若把 T2.2 的完整四档修复（9.5 人时 ≈ 1.2 人天）一并计入，总投入 **4.3 人天**。

---

## 4. 风险分析

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| C1 | 裁决标准不一致，不同裁决人对同一行给出不同结论 | 中 | 阶段 2.1 先出 1 页裁决准则；对 80 行高风险行做双人交叉裁决 |
| C2 | 人工裁决 117 行耗时超出预算 | 中 | 按 n_atomic_keys 降序处理；n=2 的 42 行优先（占 35.9 %） |
| C3 | 裁决结果与 `indicators_v1` 后续变更冲突 | 中 | 裁决记录绑定 `indicators_v1` md5（`ebcbd9a7…`），上游变更后重开 |
| C4 | 阶段 0 的方案三最小版破坏 `alias_id` 唯一性 | 中 | 新增行用派生 `alias_id`（如 `A-00067#2`），保留原行不删除 |
| C5 | 阶段 3 写回后 V7 未归零 | 低 | 以 `alias_norm_multi_canonical == 0` 为完成判据 |
| C6 | 上游 `indicators_v1` 重复建号未被清理，新注册继续产生同类冲突 | **高** | 阶段 4 准入拦截；裁决记录即为清理清单（327 个重复 canonical_name） |
| C7 | T2.2 的 F2/F3 未上线即执行阶段 0，导致静默选键放大 | **高** | 阶段 0 必须与 F1 同批上线；F2/F3 未上线前不得执行方案三拆分 |
| C8 | 327 个重复 canonical_name 中有 162 个未进入 165 清单，裁决后仍留在别名库 | 中 | 单独出一份 `duplicate_canonical_name_327.csv` 供 C6 使用 |

---

## 5. 与既有结论的衔接

| 既有结论 | 本轮衔接 |
|---|---|
| V7 `alias_norm_multi_canonical=165`（BLOCK） | 已量化根因：**165 行 100 % 落在 indicators_v1 的 327 个重复建号集合内**，BLOCK 拦截正确 |
| V7 `duplicate_canonical_name=170`（WARN） | 与 BLOCK 同源；本轮全库行 scope 独立核算为 **327**（1158 原子键），差异来自 V7 的 canonical-form scope 口径 |
| V7 `alias_is_other_canonical=0` | 已确认"165 行互指环"是复合键比较口径错误，别名互指环不存在 |
| V5 `gate_not_independent`（2502/2502 全通过） | 165 条冲突**不在** W1 内、不在 B1 候选内、不在 alias_writes_planned=2253 内 → **BLOCK 是"卡住"而非"写错"** |
| T2.2 F1–F4 | 阶段 0 依赖 F1；阶段 0 的方案三拆分**必须**依赖 F2/F3，否则静默选键放大 3.5 倍 |

---

## 6. 产物清单

| 文件 | 内容 |
|---|---|
| `multi_canonical_conflicts_165.csv` | 165 条冲突清单（seq、alias_id、alias_norm、n_atomic_keys、atomic_keys、canonical_key_composite、canonical_name、alias_name、variety_family、metric_noun、alias_type、relation、confidence、review_flag、review_priority、alias_source、distinct_form_count、evidence_count、confusable_neighbor_count） |
| `multi_canonical_conflict_classification.csv` | 上表 + A/B 分类 7 列（`conflict_class`、`conflict_subtype`、`n_unique_base`、`unique_base`、`recommended_action`、`action_mode`） |
| `generate_conflict_classification.py` | 分类生成脚本（可重复运行） |
| `canonical_resolve_fix_design.md` / `canonical_resolve_fix.py` | T2.2 修复方案与验证（19/19 单元测试 PASS） |
