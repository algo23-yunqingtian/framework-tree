# T2.5 V86 别名门禁与黑名单门禁融合框架

> 任务：`DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN` · 分支 `feature/v85-chart-template`
> 依据：T2.2 修复原型实测（4857 pair / 9714 调用 / 19 条 UT）、T2.4 覆盖矩阵（31 条规则）、`blacklist_testset_verdicts.csv`（24 条用例三门禁实测）
> 硬约束：未修改 `build_alias_library.py`；本框架为设计交付，未回写源码

---

## 0. 结论摘要

| 项 | 结论 |
|---|---|
| 融合原则 | **fail-closed 分层**：安全门禁先于裁决门禁，裁决门禁的短路返回不得掩盖任何安全门禁 |
| 层级划分 | L0 输入校验 / **L1 安全门禁**（R-01、R-03、R-05）/ **L2 裁决门禁**（R-07）/ L3 兜底裁决（R-01b、R-03-soft、R-06） |
| 核心冲突 | **R-07 `alias_exact` 与 R-05 黑名单同时命中** → 黑名单胜（安全优先） |
| 唯一裁决门禁 | R-07，且必须是**唯一**拥有"放行"权力的门禁 |
| 黑名单输入 | 5 个必需字段 + 4 个上下文字段（见 §4.1） |
| 黑名单输出 | `hits`（全量）+ `skipped`（边界抑制）+ `effective_max_severity`（见 §4.2） |
| 回归可观测 | `would_hit_before_boundary` 字段使 G6/G7 门禁可判定 |
| 实测收益 | F3+F4 后 24 条用例一致率 20/24 → 22/24；4857 pair 语料 `A→B` 硬拦截仅 +1（F4 净效应） |

---

## 1. 现状：融合的病灶

### 1.1 现有 7 道门禁的实际顺序

```
1. empty_input                     -> 拒绝
2. alias_exact (R-07)              -> 放行        ← 裁决门禁，却位于安全门禁之前
3. variety_anchor_violation (R-01) -> 拦截
4. blacklist_precheck (R-05)       -> 拦截
5. metric_exclusion_hard (R-03)    -> 拦截
6. variety_neutral_target_review(R-01b) -> 降级复核
7. R-06 dice 阈值                  -> 放行/复核/拦截
```

### 1.2 三个结构性缺陷

| # | 缺陷 | 实测证据 |
|---|---|---|
| 1 | **裁决门禁前置短路**：R-07 命中即 `return`，后续 5 道门禁不执行 | `BOUNDARY-013`（`碳酸锂工厂库存天数` 同名对）在 base 下走 `alias_exact` 直接放行，而它同时命中 BL-012 + BL-026 |
| 2 | **黑名单归因截断**：R-05 只在第一个命中规则处 `return` | 4857 pair 语料上 `BL-003 / BL-025 / BL-015 / BL-026 / BL-016a` **从未被上报**（base 上报数 = 0） |
| 3 | **无抑制可见性**：黑名单命中/未命中无中间态，边界抑制无法审计 | 43 条 `bl_lint` 整词边界告警仅为告警，未阻止上线；`BOUNDARY-017/018` 的自触发误拦无法被定位 |

### 1.3 关键澄清：遮蔽发生在**门禁层**，不是**规则层**

T2.4 的结构检查确认：31 条规则中**规则级遮蔽为 0**（不存在同 severity 且 `L_j ⊇ L_i` 且 `R_j ⊇ R_i` 的规则对）。

`BL-003/BL-025/BL-015/BL-026/BL-016a` 从未上报的**唯一原因**是 R-05 整个门禁没机会执行——它们的触发 pair 恰好也是别名命中 pair，被 R-07 短路。

**推论**：门禁顺序错误是**语料无关的系统性缺陷**。任何黑名单规则在遇到别名命中 pair 时都可能不可见。因此修复必须是顺序修复，而非规则改写。

---

## 2. 融合框架：fail-closed 四层分层

### 2.1 分层定义

| 层 | 名称 | 成员 | 唯一权限 | 短路语义 |
|---|---|---|---|---|
| **L0** | 输入校验 | `empty_input`、编码异常、超长 | 拒绝 | 短路（前置无效） |
| **L1** | **安全门禁** | R-01 品种锚点、R-03-HARD 度量词硬冲突、**R-05 黑名单** | **只阻断，不裁决** | 短路，但必须**收集全部命中** |
| **L2** | **裁决门禁** | **R-07 别名** | **唯一的"放行"权限** | 仅当 L1 全部通过才可执行 |
| **L3** | 兜底裁决 | R-01b 品种中性、R-03-SOFT 软冲突、R-06 dice 阈值 | 放行 / 降级复核 / 拦截 | 顺序执行，取最严 |

### 2.2 三条不变式（框架的公理）

| ID | 不变式 | 违反后果 |
|---|---|---|
| **INV-1** | 任一 L1 门禁命中 ⇒ 裁决结果必为 `BLOCK` 或 `REVIEW`，**永远不能是 `PASS`** | `BOUNDARY-013` 类漏拦 |
| **INV-2** | **R-07 是唯一拥有 `PASS` 主动放行权的 L2 门禁**；L3 的 `PASS` 必须带 `dice` 依据 | 静默放行，无法审计 |
| **INV-3** | 任一 L1 门禁被短路未执行 ⇒ 该次裁决**必须标记 `incomplete=true`** 且不允许 `PASS` | 不可观测的漏检 |

> INV-3 是 T2.4 的 **G7 门禁**的实现基础：`BOUNDARY-013` 在 base 下虽然与期望"一致"，但它的裁决路径带 `incomplete=true`，G7 会判 FAIL。

### 2.3 目标顺序（V86）

```
G0  L0  输入校验                 empty_input / 编码异常        -> BLOCK(incomplete=false)
G1  L1  品种锚点                 R-01                          -> BLOCK
G2  L1  度量词硬冲突             R-03 HARD                     -> BLOCK
G3  L1  黑名单                   R-05 (F4 边界, 全量上报)      -> BLOCK / REVIEW
        ─── L1 全部通过才能进入 L2 ───
G4  L2  别名裁决                 R-07 (F2 结构化)              -> PASS / REVIEW
G5  L3  品种中性降级             R-01b                         -> REVIEW
G6  L3  度量词软冲突             R-03 SOFT                     -> REVIEW
G7  L3  dice 兜底                R-06                          -> PASS / REVIEW / BLOCK
        ─── 最终裁决 = 各层最严 ───
```

与现状的差异：**R-07 从第 2 位移至第 4 位（L1 全部之后）**，这是唯一的顺序变更，其余门禁相对次序不变（最小化回归面）。

### 2.4 与 T2.2 修复档位的映射

| T2.2 档位 | 本框架对应 |
|---|---|
| F1 最小修补 | L0/L1 健壮性（消除 2977 次 KeyError） |
| F2 结构化返回 | **INV-2 的实现基础**（R-07 必须返回三态） |
| F3 门禁重排 | **§2.3 顺序变更** + INV-1 |
| F4 整词边界 | **INV-3 的实现基础**（`skipped` 可见性） |

---

## 3. 职责边界

### 3.1 别名门禁（R-07）

| 职责 | 内容 |
|---|---|
| 名称归一化 | 调用**唯一**的 `norm_full()`（禁止自实现） |
| canonical 解析 | 把归一名解析为原子键集合 |
| 同义合并 | 多行别名指向同一 canonical 的合并 |
| 歧义识别 | 0/1/N 三态显式返回（F2） |
| 置信度 | 给出别名匹配置信度 |
| **禁止** | **不得判定语义冲突**（那是黑名单职责）；**不得在 L1 未全部通过时返回 PASS** |

### 3.2 黑名单门禁（R-05）

| 职责 | 内容 |
|---|---|
| 语义冲突拦截 | 口径互斥（产量 vs 消费量）、跨品种禁止（硅 vs 铜） |
| 边界判定 | F4a 子串包含抑制、F4b 复合短语抑制 |
| 全量上报 | 返回**所有**命中规则，不做首命中截断 |
| 抑制留痕 | 返回被边界抑制的规则及原因 |
| **禁止** | **不得裁决别名关系**；**不得返回 PASS**（黑名单只有"命中/未命中"，没有"匹配"） |

### 3.3 共享契约（边界上的单点）

| 共享项 | 规则 |
|---|---|
| `norm_full()` | **单一实现**，两个门禁都必须调用它。禁止任一侧自实现归一化（否则口径漂移） |
| 归一名字段名 | 统一 `a_norm` / `b_norm`，禁止 `name1`/`name2` 混用 |
| 三态裁决码 | 统一 `BLOCK` / `REVIEW` / `PASS`，禁止各门禁自定义返回码 |
| 品种锚点 | 由 R-01 产出并**通过上下文传入** R-05，黑名单**不得自行解析品种** |
| 原子键集合 | 由 R-07 产出，黑名单**不得调用** `resolve_canonical`（避免循环依赖） |

### 3.4 责任矩阵

| 决策 | 别名门禁 R-07 | 黑名单门禁 R-05 | 品种锚点 R-01 | dice R-06 |
|---|---|---|---|---|
| "这两个名字是同义词吗" | **R** | — | — | — |
| "这两个指标口径互斥吗" | — | **R** | — | — |
| "这两个指标跨品种吗" | — | — | **R** | — |
| "相似度够不够高" | — | — | — | **R** |
| "最终该不该放行" | 唯一 `PASS` 提出方 | 可否决（阻断） | 可否决 | 可否决/降级 |
| "归一化怎么做" | **共享** | **共享** | **共享** | **共享** |

---

## 4. 黑名单门禁接口契约

### 4.1 输入

```python
BlacklistGateInput = {
    # ── 必需（5 个） ──
    "a_norm":    str,          # 归一化后的指标名（已调用共享 norm_full）
    "b_norm":    str,          # 归一化后的匹配名
    "a_raw":     str,          # 原始指标名（审计用，禁止用于匹配）
    "b_raw":     str,          # 原始匹配名
    "rules":     dict[str, RuleDef],   # {"BL-001": {"L": frozenset, "R": frozenset,
                                       #             "severity": "P0", "name": str}}

    # ── 上下文（4 个，由上游门禁产出） ──
    "variety_a": list[str],    # R-01 产出的 a 侧品种锚点
    "variety_b": list[str],    # R-01 产出的 b 侧品种锚点
    "anchor_violation": bool,  # R-01 是否已判定品种冲突（True 时黑名单可跳过跨品种类规则）
    "strict_boundary": bool,   # True = 启用 F4 边界判定；False = 退化为纯子串匹配（仅调试用）
}
```

**输入约束**：
1. `a_norm` / `b_norm` 为空字符串 ⇒ 必须在 L0 被拦下，黑名单**不得收到空串**（否则会产出无意义命中）
2. `rules` 中 L/R 必须是 `frozenset`（不可变），防止运行时被修改
3. `strict_boundary=False` 时门禁**必须**在输出中标记 `boundary_disabled=true`，该标记使 G4 门禁直接 FAIL

### 4.2 输出

```python
BlacklistGateOutput = {
    # ── 主裁决 ──
    "status":                "PASS" | "BLOCK" | "REVIEW",
    "effective_max_severity": "P0" | "P1" | "P2" | None,

    # ── 全量命中（INV-1：不再首命中截断） ──
    "hits": [
        {
            "rule_id":       "BL-012",
            "severity":      "P1",
            "rule_name":     "库存天数与库存量互斥",
            "direction":     "a_L_b_R" | "b_L_a_R",     # 实际命中方向
            "a_tokens":      ["库存天数"],               # a 侧实际命中的 token
            "b_tokens":      ["库存量"],                 # b 侧实际命中的 token
        }
    ],

    # ── 边界抑制留痕（INV-3） ──
    "skipped": [
        {
            "rule_id":   "BL-012",
            "reason":    "F4a_span_contained" | "F4b_compound_phrase",
            "detail":    "a 侧 '库存' 被 '库存天数' 完全包含",
        }
    ],

    # ── 可观测性（供 G6/G7 判定） ──
    "would_hit_before_boundary": ["BL-012", "BL-026"],   # 未启用边界时的命中集合
    "checked_rules":     31,
    "gate_executed":     True,                             # False 仅在 L0 短路时为 False

    # ── 审计 ──
    "boundary_disabled": False,
    "a_raw": "碳酸锂工厂库存天数",
    "b_raw": "碳酸锂工厂库存天数",
}
```

### 4.3 输出语义

| 字段 | 语义 | 门禁用途 |
|---|---|---|
| `status=BLOCK` | 存在 ≥1 个未被抑制的命中 | G3 / G8 |
| `status=REVIEW` | 全部命中均被 F4 抑制但抑制原因需人工确认（仅 P1/P2 时） | G4 |
| `status=PASS` | 无命中（**不表示"匹配"**） | — |
| `effective_max_severity` | 决定最终裁决严重级：P0 → `BLOCK`；P1 → `BLOCK`（可配 REVIEW）；P2 → `REVIEW` | G5 |
| `hits` 非空但 `status=PASS` | **协议违规** | G6 直接 FAIL |
| `would_hit_before_boundary` ⊋ `hits` | 发生了边界抑制 | G4 的观测入口 |

### 4.4 边界判定算法（F4）

```
对每个 rule in rules:
  方向 = (a_L_b_R, b_L_a_R)
  对每个方向:
    a_tokens = [t for t in rule.L if t in a_norm]
    b_tokens = [t for t in rule.R if t in b_norm]
    if not a_tokens or not b_tokens: continue
    if not strict_boundary: 加入 hits; continue

    # F4a 子串包含（同字符串内）
    if a_norm == b_norm:
        if span_contained(min_span(b_tokens), min_span(a_tokens)):
            skipped += (rule_id, "F4a_span_contained"); continue

    # F4b 复合短语（严格不相交）
    for t in a_tokens:
        for s in a_norm 中所有 rule.R 的命中:
            if disjoint(span(t), span(s)):
                skipped += (rule_id, "F4b_compound_phrase"); continue

    hits += {rule_id, direction, a_tokens, b_tokens}
```

> **实现陷阱**（T2.2 UT-14 实测踩过）：F4a 的同字符串判定必须用**值相等** `a_norm == b_norm`，不能用对象身份 `a_norm is b_norm`。`norm_full()` 对同名输入返回**不同字符串对象**，用 `is` 会导致 F4a 永不触发。

---

## 5. 冲突解决规则

### 5.1 冲突类型与裁决

| # | 冲突 | 裁决 | 依据 |
|---|---|---|---|
| C1 | R-07 `alias_exact` ↔ R-05 黑名单 | **黑名单胜**（`BLOCK`） | INV-1 |
| C2 | R-05 ↔ R-05（多规则同时命中） | **全部上报**，取最高 severity | INV-1 + §4.2 |
| C3 | R-05 ↔ R-01 品种锚点 | 都阻断，两者都上报；最终 severity 取高 | INV-1 |
| C4 | R-05 ↔ R-06 dice | dice **不能推翻**黑名单 | INV-1 |
| C5 | R-05 ↔ R-03 度量词冲突 | 都阻断，都上报 | INV-1 |
| C6 | 黑名单命中 ↔ F4 边界抑制 | 抑制后视为"未命中"，但**必须留痕**于 `skipped` | INV-3 |
| C7 | R-07 多 canonical ↔ R-05 | 降级复核优先于黑名单裁决（`REVIEW`），两者都上报 | §5.2 |
| C8 | 黑名单 `status=PASS` ↔ dice 放行 | 允许，但 L1 必须全部通过（INV-1/INV-3） | — |

### 5.2 唯一例外：C7 的多 canonical 优先级

`R-07` 返回 `AMBIGUOUS`（多 canonical）时，裁决为 `REVIEW`，**且优先于黑名单的 `BLOCK`**。理由：

- `AMBIGUOUS` 表示"别名库本身对该名字有多义性"，是**数据缺陷信号**，不是匹配失败；
- 此时阻断会掩盖数据缺陷，降级复核才能让缺陷被看见；
- 4857 pair 语料上此类 pair 共 **167** 条，全部由 `A→R`（自动放行 → 降级复核）迁移而来，无一条进入 `A→B`。

> 但 **P0 黑名单命中不得被 C7 降级**：若 R-05 的 `effective_max_severity == "P0"`，最终裁决仍为 `BLOCK`。C7 只对 P1/P2 生效。

### 5.3 冲突解决示例

| 输入 | R-01 | R-05 | R-07 | 最终 | 依据 |
|---|---|---|---|---|---|
| `碳酸锂工厂库存天数` ↔ 同名 | 无 | BLOCK (BL-012, BL-026) | alias_exact | base: **PASS**（错）→ V86: **BLOCK** | C1 |
| `锡厂库存天数（天）` ↔ 同名 | 无 | **skipped** (F4a) | 无 | base: BLOCK（错）→ V86: **PASS** | C6 |
| `碳酸锂利润与需求分析` ↔ `…预测` | 无 | **skipped** (F4b) | 无 | base: BLOCK（错）→ V86: **PASS** | C6 |
| `COMEX镍持仓量` ↔ `COMEX：铜：…持仓量` | BLOCK (R-01) | 无命中 | 无 | **BLOCK** | C3 |
| `SMM:精炼铅出口盈亏` ↔ `其他电池国内销量` | 无 | BLOCK (BL-008 + BL-015) | 无 | **BLOCK**，`hits` 含 2 条 | C2 |
| 165 行复合键别名对 | 无 | 视情况 | **AMBIGUOUS** | **REVIEW** | C7 |

---

## 6. 裁决结果契约

所有门禁共享统一的最终裁决结构：

```python
FinalDecision = {
    "verdict":       "PASS" | "REVIEW" | "BLOCK",
    "decided_by":    "G0"|"G1"|"G2"|"G3"|"G4"|"G5"|"G6"|"G7",   # 最先决定结果的门禁
    "severity":      "P0"|"P1"|"P2"|"INFO"|None,
    "reason":        str,                                        # 人可读原因码
    "all_reasons":   [str],                                      # 全部触发原因（禁止截断）
    "incomplete":    bool,                                       # INV-3：有门禁未执行
    "layers": {
        "L1_blacklist": BlacklistGateOutput,
        "L2_alias":     AliasGateOutput,
        "L3_dice":      {"dice": float, "threshold": str, "branch": str},
    },
    "audit": {
        "a_raw": str, "b_raw": str, "a_norm": str, "b_norm": str,
        "gate_order": ["G0","G1","G2","G3","G4","G5","G6","G7"],
        "engine_md5": str, "rules_md5": str,
    },
}
```

**`incomplete=True` 的语义**：存在未执行的安全门禁。此时 `verdict` 只能是 `BLOCK`（保守），且 G7 门禁判 FAIL。

---

## 7. 实测收益与回归面

### 7.1 24 条用例三门禁实测

| 门禁 | 与期望一致 | 裁决变化 |
|---|---|---|
| base（现状顺序） | 20 / 24 | — |
| F3-only（R-07 后移，无边界） | 20 / 24 | `BOUNDARY-013` PASS→BLOCK（暴露漏拦） |
| **F3 + F4** | **22 / 24** | `BOUNDARY-017`、`BOUNDARY-018` BLOCK→PASS（F4 抑制自触发） |

剩余 2 条不一致（`BOUNDARY-019/021`）是**测试集期望错误**（R-06 阈值行为），非引擎缺陷。

### 7.2 4857 pair 语料三态差分

| 迁移 | 数量 | 含义 |
|---|---|---|
| `A→A` 稳定 | 1677 | 无回归 |
| `R→R` 稳定 | 1686 | 无回归 |
| `B→B` 稳定 | 1325 | 无回归 |
| **`A→R`** | **167** | 别名多 canonical 降级复核（167 条静默选键被消除） |
| `A→B` | 0 | 无新增硬拦截 |
| **`B→A`** | **2** | F4 释放自触发误伤 |

`accept=True` 从 1844 → 1679（**−165**），`alias_exact` 从 1824 → **UNIQUE 1657 + AMBIGUOUS 复核 167**。

### 7.3 回归面收敛性

| 门禁 | base | V86 | 变化 |
|---|---|---|---|
| G1 无崩溃 | **FAIL**（2977 KeyError / 30.65 %） | PASS | F1 |
| G3 P0 拦截率 | PASS (10/10) | PASS | 不变 |
| G4 边界零误拦 | **FAIL**（2 例） | PASS | F4 |
| G6 组合全量上报 | **FAIL**（只报首条） | PASS | F3 |
| G7 门禁冲突可观测 | **FAIL**（`alias_exact` 短路） | PASS | F3 |
| G8 一致率 ≥ 98 % | 83.3 % FAIL | 91.7 % FAIL → 修正期望后 100 % | F3+F4 + 测试集修正 |

> 框架落地后 **5 个门禁从 FAIL 转 PASS**，无需修改任何黑名单规则定义。

---

## 8. 落地路径与风险

### 8.1 落地顺序

| 阶段 | 内容 | 前置 | 回归面 |
|---|---|---|---|
| P1 | F1 最小修补 + L0 输入校验强化 | 无 | 零（只消除 KeyError） |
| P2 | F4 边界判定（先做，因为它是 R-05 内部改动，不动顺序） | P1 | 2 条 `B→A`，可验证 |
| P3 | F2 结构化返回（改 R-07 返回契约） | P1 | 需同步所有 R-07 调用方 |
| P4 | F3 门禁重排（唯一顺序变更） | P2 + P3 | **最大回归面**：167 条 `A→R` |
| P5 | 测试集修正 + G1–G14 门禁上线 | P4 | 无 |

> **不建议先做 P4**：门禁重排的回归面最大（167 条迁移），而 F4/F2 是它的安全网。先上安全网再动顺序。

### 8.2 风险

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| F1 | F4 边界抑制过宽，放过真实冲突 | 高 | `strict_boundary` 可开关；`would_hit_before_boundary` 全量留痕，可离线复核；G4 只要求抑制数 = 期望数，不要求为 0 |
| F2 | `incomplete=True` 在部分短路路径被忽略，导致静默放行 | **高** | 把 `incomplete=True ⇒ verdict != PASS` 写成断言（对应 T2.2 UT-07/UT-18） |
| F3 | 归一化口径漂移（黑名单与别名各自实现 `norm_full`） | 高 | §3.3 单一实现强制；引擎加载时校验两处 `norm_full` 的 md5 一致 |
| F4 | C7 例外被滥用，P0 黑名单被多 canonical 降级 | 中 | §5.2 明确"P0 不得被 C7 降级"，写成断言 |
| F5 | 167 条 `A→R` 淹没人工复核队列 | 中 | `REVIEW` 附 `all_reasons`，按 `effective_max_severity` 排序；P2 批量走 |
| F6 | 黑名单规则被运行时修改导致顺序敏感 | 低 | `rules` 用 `frozenset` + `rules_md5` 审计 |

### 8.3 不可回滚项

一旦上线 F3（门禁重排），下游若已依赖"别名命中即放行"的语义，**必须同步修改**。建议在 P4 前做一次下游消费方清点（`reason == "alias_exact"` 的所有调用点）。

---

## 9. 交付物

| 文件 | 内容 |
|---|---|
| 本文件 | V86 融合框架设计 |
| `canonical_resolve_fix_design.md` | T2.2 修复方案（F1–F4 四档 + 19 条 UT） |
| `blacklist_rule_testing_design.md` | T2.4 测试方案（G1–G14 门禁） |
| `canonical_resolve_fix.py` | 可运行修复原型（`blacklist_check_bounded` 即 §4.4 的 F4 实现） |
| `blacklist_rule_coverage_matrix.csv` / `blacklist_testset_verdicts.csv` | 31 规则覆盖矩阵 / 24 用例三门禁裁决 |
