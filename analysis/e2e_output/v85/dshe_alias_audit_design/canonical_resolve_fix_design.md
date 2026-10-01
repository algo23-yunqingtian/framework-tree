# T2.2 resolve_canonical 引擎缺陷修复方案

> 任务：`DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN` · 分支 `feature/v85-chart-template`
> 验证脚本：`canonical_resolve_fix.py`（可重复运行）· 结果：`canonical_resolve_fix_result.json`
> 单元测试：**19 / 19 PASS** · 测试 pair：**4857**（play488 2566 + aliaslib 1658 + rerated 444 + selfpair 165 + boundary 24）
> 硬约束：未修改 `build_alias_library.py` 及任何 GT/黑名单文件；修复实现仅在进程内原型验证，**未回写源码**

---

## 0. 结论摘要

| 项 | 值 |
|---|---|
| 缺陷位置 | `build_alias_library.py` **L260–L266**，`resolve_canonical(nm)` |
| 缺陷类型 | 对 `ALIAS` 字典**硬索引**（`ALIAS[nm]`），未注册归一名触发 `KeyError` |
| 观测率 | 9714 次调用中 **2977 次 KeyError（30.65 %）** |
| 上一轮观测 | guard_hits=382（448 歧义全集、892 次调用、42.83 %） |
| 修复档位 | F1 最小修补 / F2 结构化返回 / F3 门禁重排 / F4 整词边界（4 档可独立上线） |
| 最关键修复 | **F2+F3：消除 167 条静默选键**（alias_exact 1824 → UNIQUE 1657 + AMBIGUOUS 复核 167） |
| 门禁遮蔽修复 | F3 后 `BL-003 / BL-025 / BL-015 / BL-026 / BL-016a` 首次可上报（原被遮蔽至 0） |
| 误伤修复 | F4：黑名单命中 239 → 释放 4（F4a 子串包含 8 次抑制 + F4b 复合短语 3 次抑制） |
| 总工时 | 9.5 人时（0.25 + 2 + 4 + 3） |

---

## 1. 缺陷定位

### 1.1 源码（L260–L266，原文）

```python
L260  def resolve_canonical(nm):
L261      s = set()
L262      s |= set(name2canon.get(nm, []))
L263      s |= set(key2canon.get(nm, []))
L264      s |= set(name2canon.get(ALIAS[nm]["light"], []))
L265      s |= set(key2canon.get(ALIAS[nm]["light"], []))
L266      return sorted(s)
```

### 1.2 根因

L262/L263 使用 `.get(nm, [])` 安全访问，但 **L264/L265 对 `ALIAS` 做硬索引 `ALIAS[nm]`**。

- `ALIAS` 仅在 `ingest()` 阶段收录 `canonical_name` 与 `alias_name`（含 `INDICATORS_V1_NAME`/`INDICATORS_V1_KEY`/`THS_MATCHED`/`RISK_DB_*` 五类来源）；
- `new_matcher()`（L475）把 `norm_full(a_raw)[0]` 与 `norm_full(b_raw)[0]` 交给 `resolve_canonical`，而这两个值来自任意输入（PDF 模板名、THS 序列名、上游检索填充名），**不在 `ALIAS` 收录范围**；
- 两者口径不一致 → `ALIAS[nm]` 必抛 `KeyError`。

### 1.3 实测量化

| 指标 | 值 |
|---|---|
| 调用总数 | 9714 |
| KeyError | **2977（30.65 %）** |
| `ALIAS` 注册条目 | 4643 |
| `name2canon` 键数 | 1234 |
| `key2canon` 键数 | 1652 |
| KeyError 样本 | `场内库存`、`注册仓单库存`、`非仓单库存`、`电解镍`、`电解铜`、`注册仓单` |

**特征**：KeyError 集中在**短度量词与实体词**（`产量`、`库存`、`注册仓单`），即那些只作为"词"而非"完整指标名"出现在输入中的 token。上一轮的 382 次（892 次调用）是本轮 2977 次的子集，差异来自测试集规模。

### 1.4 影响面

| 场景 | 后果 |
|---|---|
| 管线内无 try/except | 整批中断，**整批 TP 归零** |
| 管线内 catch 后按拒绝处理 | 相当于 2977 个**隐性硬拦截**，全部无法归因 |
| 本审计采用 `guard_resolve_canonical`（`.get()` 兜底） | 未注册名返回 `[]` → 落入模糊匹配路径，由 R-01/R-05/R-06 决定 |

---

## 2. 修复档位

### F1 · 最小修补（0.25 人时，零行为变化）

```diff
- s |= set(name2canon.get(ALIAS[nm]["light"], []))
- s |= set(key2canon.get(ALIAS[nm]["light"], []))
+ rec = ALIAS.get(nm)
+ if rec is not None:
+     light = rec.get("light", "")
+     s |= set(name2canon.get(light, []))
+     s |= set(key2canon.get(light, []))
```

- 2 行改 5 行，**已注册名行为零变化**（UT-03 断言：`resolve_safe` 对已注册名与原实现完全一致）
- 未注册名返回 `[]`（UT-02 断言：不抛异常）
- **不解决**：未注册名的语义状态被静默吞掉、多 canonical 歧义、R-07 短路黑名单
- 风险：**极低**。建议作为第一步立即上线。

### F2 · 结构化返回（2 人时）

```python
def resolve_structured(nm):
    return {"state": "UNREGISTERED" | "NO_MATCH" | "UNIQUE" | "AMBIGUOUS",
            "canonicals": [...], "alias": bool, "light": str}
```

把 **0 / 1 / N** 三种状态显式化，让调用方不再需要靠"空列表"猜测原因。实测断言：

| 测试 | 输入 | state |
|---|---|---|
| UT-04 | `产量`（未注册） | `UNREGISTERED` |
| UT-05 | `碳酸锂工厂库存天数`（单键） | `UNIQUE` |
| UT-06 | `GFEX：工业硅：主力合约：单边交易：持仓量（日）`（12 个原子键） | `AMBIGUOUS` |

### F3 · 门禁重排（4 人时）

| 序 | 原顺序 | 修复后 |
|---|---|---|
| 1 | `empty_input` | `empty_input` |
| 2 | **`alias_exact` (R-07) ← 放行型门禁** | `variety_anchor_violation` (R-01) |
| 3 | `variety_anchor_violation` (R-01) | `blacklist_precheck` (R-05，**收集全部命中**) |
| 4 | `blacklist_precheck` (R-05) | `alias_exact` (R-07，**仅 UNIQUE 放行**) |
| 5 | `metric_exclusion_hard` (R-03) | `metric_exclusion_hard` (R-03) |
| 6 | `variety_neutral_target_review` (R-01b) | `variety_neutral_target_review` (R-01b) |
| 7 | R-06 阈值 | R-06 阈值 |

**两个关键改进**：
1. **R-07 是放行型门禁，不能位于安全门禁之前**。原顺序下 R-07 命中即返回，黑名单永远不会执行 → 见 BOUNDARY-013（`碳酸锂工厂库存天数` 双侧命中 BL-012 + BL-026，却因 `alias_exact` 自动放行）。UT-07 断言：F3 下改判 `blacklist_precheck`。
2. **R-05 原实现只上报首条命中规则**（`for rid, ... in BL_LR.items(): ... return`），导致后续命中的规则永远无法被观测到。修复后返回 `all_rules` 列表。UT-08 断言：`{"BL-012","BL-026"}` 全部上报；UT-09 断言：`国内销量 ↔ 出口` 现在能上报 `BL-015`。

### F4 · 整词边界 + 同侧纯度（3 人时）

黑名单的 L/R 语义是"x 侧讲 A、y 侧讲 B"。实测发现两类误触发：

| 子规则 | 条件 | 例 |
|---|---|---|
| **F4a** 子串包含 | L 与 R 在同一字符串内都命中，且一侧匹配区间被另一侧**完全包含** | BL-012：`库存` ⊂ `库存天数`（同为 `锡厂库存天数（天）`） |
| **F4b** 复合短语 | 同一字符串内 L 与 R 以**严格不相交**区间同时出现 | BL-009：`碳酸锂利润与需求分析` 同时含 `利润`(3-5) 与 `需求`(6-8) |

> **注意实现陷阱**：F4a 必须用**值相等**（`a == b`）而非对象身份（`a is b`）比较两侧字符串——`norm_full` 两次调用返回内容相同但对象不同的字符串，用 `is` 会导致 F4a 永不触发（本方案首次实现时踩过此坑，UT-07/UT-08 一度失败）。

实测（4857 pair）：黑名单命中 239 → **释放 4**（F4a 抑制 8 次 + F4b 抑制 3 次），仍拦截 235。UT-14/UT-16/UT-17/UT-19 覆盖正误两侧。

**F4 与 `bl_lint` 的关系**：`build_alias_library.py` 的 `bl_lint` 已产出 **43 条**整词边界告警（BL-001/016/025 各 3 条；BL-002/003/008/009/010/011/015/017/018/019/022/023/024/018a/018b 各 2 条；BL-004/012/013/014 各 1 条），但**仅为告警、未阻止上线**。F4 是把告警升级为运行时约束。

---

## 3. 行为差分（4857 pair，同一引擎、同一输入）

### 3.1 三态迁移

| 迁移 | 数量 | 含义 |
|---|---|---|
| `R→R` | 1686 | 降级复核稳定 |
| `A→A` | 1677 | 自动放行稳定 |
| `B→B` | 1325 | 硬拦截稳定 |
| **`A→R`** | **167** | 自动放行 → 降级复核（**全部为多 canonical 别名对**） |
| **`B→A`** | **2** | 硬拦截 → 自动放行（**全部为 F4 释放的自触发误伤**） |

`accept=True`：1844 → 1679（**−165**）；`accept=False`：3013 → 3178（+165）。

### 3.2 alias_exact 拆解

| | base | fixed |
|---|---|---|
| `alias_exact` 总数 | 1824 | 1657（UNIQUE） |
| `alias_ambiguous_multi_canonical` | 0（不存在该状态） | **167（新增降级复核）** |
| **静默选键** | **167** | **0** |

**静默选键的机制**：R-07 在 `len(set(ca) & set(cb)) > 1` 时执行 `sorted(...)[0]`，即**按字典序取第一个原子键**，其余 N−1 个变体永久不可达且无任何日志。实测样例：

| 输入 | `resolve_canonical` 返回 | 排序首键 | 被静默丢弃 |
|---|---|---|---|
| `GFEX：工业硅：主力合约：单边交易：持仓量（日）` | 12 个原子键 | `si_21_openinterest` | 11 个 |
| `GFEX：工业硅：仓单数量（日）` | 10 个原子键 | `si_21_warrant_industrial_si` | 9 个 |
| `COMEX：铜：主力合约：收盘价（日）` | 2 个原子键 | `cu_23_comex_close` | 1 个 |

### 3.3 门禁遮蔽解除

| 规则 | base 上报次数 | fixed 上报次数 |
|---|---|---|
| BL-003 | 0 | >0 |
| BL-025 | 0 | >0 |
| BL-015 | 0 | >0 |
| BL-026 | 0 | >0 |
| BL-016a | 0 | >0 |

> 这与上一轮"6 条 DSH-B 扩展规则零边际贡献、注入探针 2/6"的现象同源：规则本身命中（BL-018a 命中 13 pair、BL-026 命中 19 pair），但**引擎从未上报过它们**。上一轮把原因归为"零边际贡献"，本轮定位到**结构性归因遮蔽**（R-07/R-01 前置 + R-05 只报首条）。

---

## 4. TP/FP 影响预估

| 影响项 | 数量 | 方向 |
|---|---|---|
| 崩溃消除 | **2977** 次调用 | 从"中断/隐性拒绝"变为"正常判定" |
| `A→R` 降级复核 | **167** | 别名侧 **TP 净增益**（原为静默错误入库） |
| `B→A` 放行 | **2** | **FP 修复**而非 FP 引入（均为 pattern 自触发的同名对） |
| 稳定不变 | 4388（90.3 %） | 无副作用面 |

**说明**：
- `A→R` 的 167 条若维持原行为，会被当作"正确的别名映射"写入生产库——这是**别名侧 TP 缺失**（本应拒绝的映射被接受）。
- `B→A` 的 2 条全部是 BL-012/BL-026 的同字符串自触发，放行后走 R-07 `alias_exact`（唯一键），语义正确。
- **`A→R` 会扩大人工复核队列 167 条**，这是可接受的代价，也是 F2 显式化歧义状态的必然结果。

---

## 5. 回归风险评估

| ID | 风险 | 等级 | 缓解 |
|---|---|---|---|
| R1 | R-05 的 `reason` 从"首条命中规则"变为"首个上报 + `all_rules` 全量"，下游若按 `rule_id` 精确匹配会失配 | **高** | 同步更新所有消费 `reason.rule` 的下游；保留 `rule` 字段为首条以兼容 |
| R2 | 新增 `alias_ambiguous_multi_canonical` 降级复核路径，人工复核队列 +167 | 中 | 复核队列按 `n_atomic_keys` 降序处理 |
| R3 | `alias_exact` 从 1824 降至 1657，别名库自动放行率下降 9.1 % | 中 | 167 条转为复核而非拒绝，不产生拒绝率上升 |
| R4 | `blacklist_boundary_testset.json` 24 例中 **8 例的 `expected_rule` 在新门禁下不可达** | **高** | 重建测试集期望：BL-009a 不存在于终版黑名单；R-01 先于 R-05 使 BL-022/BL-018/BL-018a 的期望不可达（详见 T2.6） |
| R5 | F4 若配置过宽，可能放过真实冲突 | 中 | F4 仅对"同侧纯度不足"的方向跳过，跨字符串冲突不受影响；UT-16 断言 `库存天数 ↔ 库存量` 仍命中 |
| R6 | F1 单独上线 | **极低** | 零行为变化，只消除崩溃，是安全的第一步 |

---

## 6. 单元测试（19 / 19 PASS）

| ID | 断言 | 结果 |
|---|---|---|
| UT-01 | 原实现：未注册归一名 `产量` → KeyError（**缺陷复现**） | PASS |
| UT-02 | F1：`resolve_safe("产量")` 返回 `[]` 且不抛异常 | PASS |
| UT-03 | F1：`resolve_safe` 对已注册名与原实现完全一致 | PASS |
| UT-04 | F2：未注册名 `state=UNREGISTERED` | PASS |
| UT-05 | F2：单键 `state=UNIQUE` | PASS |
| UT-06 | F2：复合键 alias_norm `state=AMBIGUOUS`（12 原子键） | PASS |
| UT-07 | F3-only：R-07 与黑名单同时命中 → 黑名单优先 | PASS |
| UT-08 | F3-only：黑名单上报全部命中规则而非首条 | PASS |
| UT-09 | F3：`BL-015` 不再被 `BL-008` 遮蔽 | PASS |
| UT-10 | F3：AMBIGUOUS 别名对降级复核而非自动放行 | PASS |
| UT-11 | F3：空输入 → `empty_input`（不变） | PASS |
| UT-12 | F3：跨品种 → `variety_anchor_violation`（不变） | PASS |
| UT-13 | F3：2 键别名对 → AMBIGUOUS 降级复核 | PASS |
| UT-14 | F4：BL-012 pattern 自触发的同名对不再命中 | PASS |
| UT-15 | F3：1 键别名对 → `alias_exact` 自动放行 | PASS |
| UT-16 | F4：合法跨字符串冲突仍命中（`库存天数 ↔ 库存量`） | PASS |
| UT-17 | F4：BL-009 复合短语自触发不再命中 | PASS |
| UT-18 | F3+F4：BOUNDARY-013 恢复不阻塞（走 `alias_exact`） | PASS |
| UT-19 | F3+F4：BOUNDARY-017/018 类复合短语误伤修复 | PASS |

---

## 7. 上线顺序建议

```
第 1 步  F1  最小修补        0.25 人时   零行为变化，立即上线，消除 2977 次崩溃
第 2 步  F2  结构化返回      2   人时   同步调用方，消除 silent-fail
第 3 步  F3  门禁重排 + R-05 全量上报  4  人时   消除 167 条静默选键 + 解除 5 条规则遮蔽
第 4 步  F4  整词边界 + 同侧纯度     3   人时   修复 9 类 pattern 误伤
并行     重建 blacklist_boundary_testset.json 的 24 例期望（8 例不可达）
```

**不建议跳步**：F1 与 F2 是 F3 的前置（F3 依赖结构化状态区分 UNIQUE/AMBIGUOUS）；F4 独立于 F3 但依赖 F2 的调用约定。

---

## 8. 与上一轮的关系

| 上一轮结论 | 本轮定性 |
|---|---|
| "L264–265 硬索引缺陷，guard_hits=382，需修复" | **确认**，并在 4857 pair / 9714 次调用上量化为 2977 次（30.65 %） |
| "6 条 DSH-B 扩展规则零边际贡献，by_this_rule=0" | **原因更正**：不是零贡献，是**结构性归因遮蔽**（R-07/R-01 前置 + R-05 只报首条）。BL-018a 实际命中 13 pair、BL-026 命中 19 pair，但引擎上报 0 |
| "注入探针 2/6" | 仍成立但**结论方向相反**：探针证明注入机制未失效，遮蔽发生在归因层而非注入层 |
| "D1 引擎缺陷需修复" | 由 D1 单一缺陷扩展为 **F1–F4 四档缺陷**，其中 F3 的静默选键影响面（167 条）大于 F1 的崩溃 |
