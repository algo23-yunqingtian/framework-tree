# DSHE-B V85 别名库抽样审计 + V86 门禁融合设计 · T2 总报告

> 任务：`DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN`
> 产物目录：`analysis/e2e_output/v85/dshe_alias_audit_design/`
> 引擎：`analysis/e2e_output/v85/alias_match_presearch/build_alias_library.py`
> md5 `d375f963678d1e89c7e9949805f8433f` · 31 条黑名单规则 · 4821 归一名语料池

---

## 0. 六个子任务与产物

| # | 子任务 | 脚本 | 主产物 |
|---|---|---|---|
| T2.1 | 别名库抽样审计 | `build_sampling_audit.py` | `alias_sampling_audit_report.md`、`alias_audit_sample.csv`（400 行） |
| T2.2 | canonical 解析缺陷定位与修复 | `canonical_resolve_fix.py` | `canonical_resolve_fix_design.md`、`canonical_resolve_fix_result.json` |
| T2.3 | 165 条多 canonical 冲突归因与方案 | `generate_conflict_classification.py` | `multi_canonical_conflicts_165.csv`、`multi_canonical_conflict_solution.md` |
| T2.4 | 24 条黑名单测试用例执行 + 机制归属 | `blacklist_testset_verdicts.py` | `blacklist_testset_verdicts.csv` |
| T2.5 | V86 门禁融合框架与 F1–F4 修复 | `canonical_resolve_fix.py`（F2/F3/F4 补丁） | `v86_gate_fusion_framework.md` |
| T2.6 | 黑名单规则有效性测试（102 用例） | `blacklist_rule_effectiveness_test.py` | `blacklist_rule_test_result.md/.json`、`regression_gate_config.json` |
| — | 覆盖率分析（规则 × 语料） | `blacklist_coverage_analysis.py` | `blacklist_rule_coverage_matrix.csv`、`blacklist_rule_testing_design.md` |
| — | 公共装载器 | `audit_kit.py` | 三引擎变体 base/f3/f3f4 + F1 守卫 + 安全 resolver |

---

## 1. 关键数字

| 指标 | 值 | 出处 |
|---|---|---|
| 别名库行数 | 4643 | T2.1 |
| 归一名唯一数 | 4821 | T2.1 |
| 多 canonical 冲突别名 | 165 | T2.1 / T2.3 |
| `resolve_canonical` 调用总数 | 9714 | T2.2 |
| 其中 KeyError | **2977（30.65 %）** | T2.2 |
| 静默空返回（`[]`） | 6737（69.35 %） | T2.2 |
| 单元测试 | 19 / 19 PASS | T2.2 |
| accept=True 变化（4857 pair） | 1844 → 1679（**−165，−8.95 %**） | T2.2 |
| 阈值判定 | −9.1 % ⇒ **PASS** | T2.2 |
| 死规则 | BL-019a、BL-020、BL-021（3 条） | T2.6 |
| lint 告警 | 43 | T2.1 |
| 有效性测试用例 | **102 条 / 7 个维度** | T2.6 |
| G1–G8 + G13 + G14 门禁 | F3+F4 下 **全 PASS** | T2.6 |

---

## 2. F1–F4 修复矩阵

| 修复 | 内容 | 修复前后（关键用例） | 门禁 |
|---|---|---|---|
| **F1** | `guard_resolve_canonical`：canonical 未命中时返回 `[]` 而非 `KeyError` | 2977 次崩溃 → 0 次 | G1_NO_CRASH |
| **F2** | `resolve_canonical_safe`：多 canonical 取交集并排序，消除顺序敏感 | 165 条冲突用例可重放 | G7 相关 |
| **F3** | 门禁顺序：`blacklist` 前移到 `alias` 之前；R-05 改为全量上报 `all_rules` | base 0/6 → f3 6/6 规则上报 | G6_ALL_RULES_COMPLETE |
| **F4** | pattern 自触发抑制（F4a 子串包含 / F4b 复合短语不相交共现） | 边界误拦 11/18 → 0/18 | G4_BOUNDARY_ZERO_FP |

**F3 与 F4 必须同批上线**（详见 §4）。

---

## 3. 有效性测试：102 用例 / 7 维度

| 维度 | 条数 | 目的 | base | f3 | **f3+f4** |
|---|---|---|---|---|---|
| D1_POSITIVE | 26 | 每条活规则 ≥1 条应拦截对 | 100 % | 100 % | 100 % |
| D2_NEGATIVE | 26 | a 含 L token、b 无黑名单 token | 100 % | 100 % | 100 % |
| D3_BOUNDARY | 12 | 同串 L/R 子串关系（F4a） | 50 % | 8.3 % | **100 %** |
| D4_COMPOUND | 6 | 同串 L/R 不相交共现（F4b） | 16.7 % | 0 % | **100 %** |
| D5_COMBINATION | 8 | 命中 ≥2 条规则，全量上报 | 100 % | 100 % | **100 %** |
| D6_GATE_CONFLICT | 8 | alias_exact ∩ 黑名单同时成立 | 100 % | 0 % | **100 %** |
| D7_ROBUSTNESS | 16 | 空值/超长/短词/编码异常 | 100 % | 100 % | 100 % |
| **整体** | **102** | | **89.2 %** | **75.5 %** | **100.0 %** |

D1 拦截机制分布（三变体完全相同）：`G1_variety_anchor` 16 / 26 · `G3_blacklist` 10 / 26。

---

## 4. 四条最重要的结论

### 4.1 只有 F3+F4 全部转绿；F3 单独上线是**双重负收益**

F3 把 R-05 提到别名门禁之前，更多原本被 `alias_exact` 直接放行的 pair 进入 R-05 检查，其中大量是 pattern 自触发：

- G4 边界误拦：base **11/18** → f3 **17/18**（恶化 6 条）→ f3+f4 **0/18**
- D6 自配对：base **PASS × 8** → f3 **BLOCK × 8**（8 条把误报当真实冲突拦截）→ f3+f4 **PASS × 8**
- 整体一致率：base 89.2 % → f3 **75.5 %**（低于 base）→ f3+f4 100 %

**F3 必须与 F4 同批上线**。

### 4.2 INV-1（黑名单优先于别名放行）在本语料上**不可判定**

语料池 4821 个归一名中，`alias_exact` 分支条件（双侧 canonical 有交集）与黑名单命中**同时成立的 pair 共 14 条，全部是自配对**（`a == b`，如 `碳酸锂工厂库存天数` ↔ 自身）：

```
SMM 再生铅原料库存天数          rules=['BL-012','BL-026']
碳酸锂工厂库存天数              rules=['BL-012','BL-026']
铜：火法：仓单溢价均价：上海     rules=['BL-023']
SMM 精炼铅成本及利润: 硫酸价格   rules=['BL-017']
... 共 14 条
```

这些配对的黑名单命中**本身就是 pattern 自触发误报**（BL-012 的 L 侧 `库存天数` 与 R 侧 `库存` 在同一字符串内构成子串关系），所以正确答案是**放行**。语料中**不存在**「别名精确命中 + 真实黑名单冲突」的跨配对。

因此 G7 只能给出 **N/A** 而不能给 PASS/FAIL——把它记成 PASS 是过度声明。

**补齐方向**：引入外部构造的跨配对（同 canonical 的多品种别名 ↔ 另一 canonical 的黑名单命中别名），本轮未构造。

### 4.3 黑名单门禁的边际贡献是 **10/26 = 38.5 %**

D1 用例的拦截被多层门禁分担，三变体拦截率均为 100 %：

| 裁决门禁 | 独占裁决 |
|---|---|
| R-01 品种锚点 | 16 / 26 |
| R-05 黑名单 | **10 / 26** |

黑名单门禁的价值**不是提升拦截率**，而是**提升可归因性与可解释性**——把「被某个模糊规则拦住」变成「被 BL-005 第 3 条 pattern 拦住，因为 a 侧命中『锌锭』、b 侧命中『表观消费』」。

**但这意味着 R-05 自身精度的统计功效不足**：17 条活规则的 D1 用例全部被 R-01 先行拦截，R-05 从未裁决，其精度在本语料上**无法评估**。

补齐方向：为这 17 条规则构造**同品种跨度量词**用例（品种相同使 R-01 不触发，仅 R-05 可能裁决）。

### 4.4 G1 在本测试中**不可证伪**

base / f3 / f3f4 三个变体均由 `audit_kit.load_engine()` 装载，而该装载器已安装 F1 守卫，因此三者恒为 PASS。未打补丁的引擎不会通过 G1（2977/9714 = 30.65 % 崩溃）。

G1 必须在**未打补丁**的引擎上验证，或在引擎 md5 校验中固定「F1 已安装」状态。

---

## 5. 14 道回归门禁归属

| 门禁 | 级别 | 责任层 | 实测 |
|---|---|---|---|
| G1_NO_CRASH | P0 | T2.2（未打补丁引擎） | 未打补丁 30.65 % 崩溃；打补丁 0 |
| G2_LIVE_RULE_COVERAGE | P0 | T2.6 | 28/28 PASS |
| G3_P0_BLOCK_RATE | P0 | T2.6 | 16/16 PASS |
| G3b_P0_R05_ATTRIBUTION | INFO | T2.6 | 37.5 %（不设门槛） |
| G4_BOUNDARY_ZERO_FP | P0 | T2.6 | base FAIL → f3+f4 **0/18 PASS** |
| G5_SAFE_NEG_FP_LE_1 | P1 | T2.6 | 0.0 % PASS |
| G6_ALL_RULES_COMPLETE | P1 | T2.6 | base 0/6 → f3 6/6 **PASS** |
| G7_INV1_BLACKLIST_BEATS_ALIAS | P1 | T2.6 | **N/A**（跨配对 0 条） |
| G8_OVERALL_MATCH_GE_98 | P0 | T2.6 | base 89.2 % → f3+f4 **100 % PASS** |
| G9_UNIT_TESTS_PASS | P0 | T2.2 | 19/19 PASS |
| G10_CORPUS_DIFF_BOUNDED | P1 | T2.2 | −8.95 % ≤ 9.1 % PASS |
| G11_EXPECTED_RULE_EXISTS | P1 | T2.4 前置修正项 | 待执行：`BL-009a` × 3 → `BL-009` |
| G12_MECHANISM_ATTRIBUTION | P1 | T2.4 前置修正项 | 待执行：BOUNDARY-014/016/020/022 归因 R-01 |
| G13_TRISTATE_EXPECTATION | P1 | T2.6 | 102/102 带三态或机制期望 |
| G14_DEAD_RULE_EXCLUDED | P1 | T2.6 | PASS（3 条死规则未进入期望） |

---

## 6. 剩余风险与后续动作

| 风险 | 影响 | 后续动作 |
|---|---|---|
| G7 不可判定 | INV-1 无实证 | 引入外部跨配对样例（同 canonical 多品种别名 ↔ 异 canonical 黑名单别名） |
| 17 条活规则 R-05 未裁决 | R-05 精度统计功效不足 | 构造同品种跨度量词用例隔离 R-05 |
| G1 在打补丁变体上不可证伪 | 无法证明 F1 有效 | 在未打补丁引擎上单跑 G1，或固定引擎 md5 |
| 期望值来自规则语义推断 | 非人工标注 | 首轮人工复核 26 条 D1 + 8 条 D6 期望后冻结 |
| F4b 抑制不区分方向 | 可能放过真实复合短语冲突 | 对 P0 规则保留 F4b 抑制前告警上报 |
| 3 条死规则 | 语料零命中且 lint 未捕获 | 下线 BL-019a/BL-020/BL-021，或补充语料覆盖 |
| G11/G12 前置修正未执行 | 历史 24 条用例期望字段错误 | 修正 `BL-009a` × 3 与 4 条边界用例归因 |

---

## 7. 上线建议

1. **同批上线 F1 + F3 + F4**（F2 可单独，无门禁回归风险）。禁止单独上线 F3。
2. 上线后以 F3+F4 为基线，冻结 `regression_gate_config.json` v1.1 的 11 道门禁，作为 V86 回归门禁套件。
3. G7 在补齐跨配对样例前**不得计为 PASS**。
4. 首轮人工复核 D1（26）+ D6（8）用例期望后，将其冻结为回归基线。
