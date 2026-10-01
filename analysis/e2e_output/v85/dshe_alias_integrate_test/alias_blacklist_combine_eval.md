# alias_blacklist_combine_eval.md — 别名库 + 联合黑名单 回放质量评估

| 项目 | 值 |
|---|---|
| 任务 | DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY · T2.1 |
| 脚本 | `dshe_alias_integrate_test/combine_eval.py` → `combine_eval_result.json` / `combine_eval_log.txt` |
| 判定引擎 | `alias_match_presearch/build_alias_library.py` 第 1..655 行原样加载（分节标记在第 656 行，写文件语句已排除） |
| 源 MD5 / SHA256 | `d375f963678d1e89c7e9949805f8433f` / `b756c191ee24882fe6762ece11f77b239ba36e82f28b7bc1d3783a9be4d8f570` |
| 随机种子 | `20261001`（与上一轮回归一致，测试集可复现） |
| 生成时间(UTC+8) | 2026-10-01 12:24:37 |
| 约束 | 不调用 zhiji API；不修改 `indicators_v1.json` / `semantic_blacklist_fixed.json` / 别名库 CSV；纯文本 token 静态回放；无价格数据 / 策略 / PnL |

---

## 0. 输入可用性（T1 声明 vs 实测）

| 输入 | 状态 | 规模 |
|---|---|---|
| `indicator_alias_library.csv` | FOUND | 4643 行 |
| `ambiguous_indicator_list.csv` | FOUND | 448 行 |
| `high_risk_confusion_pairs.csv` | FOUND | 409 行 |
| `semantic_blacklist_fixed.json` | FOUND | 25 条规则 |
| `blacklist_extend_candidate.json` | FOUND | 8 条候选 |
| HERMES `ths_candidate_mapping.csv` | FOUND | 2359 行 |
| `data/indicators_v1.json`（只读） | FOUND | 1658 键 |
| **DSH-B `semantic_blacklist_v85_final.json`** | **MISSING** | — |
| **DSH-B `full_488_template_playback_result.csv`** | **MISSING** | — |

**替代方案（两处，均已实测）**

1. 联合黑名单 = `semantic_blacklist_fixed.json`（25 条基线）+ `blacklist_extend_candidate.json` 中 `status != not_recommended` 的 **6 条**扩展 → **31 条**。
2. 488 模板回放 = `v85_final_integrate/ths_render_task_summary.csv`（488）+ `v85_render_fix_review_package/render_simulation_log_fixed.csv`（488）作代理。**该代理仅含模板级最终状态，不含逐 pair 的黑名单命中证据，不能替代 DSH-B 回放文件**——本文的 488 结论只用于联动叙事，不参与 TP/TN/FP/FN 计算。

---

## 1. 联合黑名单构成

| rule_id | 父规则 | 级别 | L_gen→L_eff | R_gen→R_eff | 名称 |
|---|---|---|---|---|---|
| BL-018a | BL-018 | P0 | 7→6 | 7→7 | 锡与镍跨品种禁止 |
| BL-018b | BL-018 | P0 | 3→2 | 5→5 | 锡与钢铁跨品种禁止 |
| BL-019a | BL-019 | P0 | 4→4 | 4→4 | 硅加工费与铜加工费跨品种禁止 |
| BL-026 | BL-012 | P0 | 1→1 | 1→1 | 库存天数跨品种禁止 |
| BL-016a | BL-016 | P1 | 5→5 | 4→4 | 利润与产量互斥（含碳酸锂子品类） |
| BL-025a | BL-025 | P0 | 4→4 | 4→4 | 消费量与产量互斥（含锡锌子品类） |
| BL-NEW-01 | — | — | — | — | 所有库存类指标互斥（**拒绝**，not_recommended） |
| BL-NEW-02 | — | — | — | — | — （**拒绝**，not_recommended） |

lint 丢弃 3 个 pattern（长度 < `MIN_PATTERN_LEN`），整词边界告警 1 个。**采纳 6 / 拒绝 2**。

注入方式：改写模块全局 `BL_LR` 后 `new_matcher` 立即生效（`new_matcher` 经 `__globals__` 解析，函数体未重写）。

---

## 2. 测试集

| 集合 | 规模 | 构成 |
|---|---|---|
| 负向（应拦截） | 41 | `risk_rootcause_detail.csv`，P0 25 / P1 16；有匹配目标 37，无目标 4 |
| 正向候选池 | 1179 | `match_type != none` 且 `verify_status ∈ {VALID, FILLED}` |
| 正向（抽样） | 200 | seed `20261001`；`fuzzy_name` 184 / `exact_name` 14 / `fuzzy_key` 2；VALID 96 / FILLED 104 |

正向池全量分布：`fuzzy_name` FILLED 597 / VALID 513、`exact_name` VALID 31 / FILLED 21、`fuzzy_key` FILLED 11 / VALID 6。

---

## 3. 主结果：BEFORE(25 条) vs AFTER(31 条)

| 指标 | BEFORE(25) | AFTER(31) | delta |
|---|---|---|---|
| TP | 41 | 41 | 0 |
| FN | 0 | 0 | 0 |
| FP | 140 | 140 | 0 |
| TN | 60 | 60 | 0 |
| Accuracy | 41.91% | 41.91% | +0.00 |
| Precision | 22.65% | 22.65% | +0.00 |
| **Recall** | **100.00%** | **100.00%** | +0.00 |
| Specificity | 42.86% | 42.86% | +0.00 |
| F1 | 36.94% | 36.94% | +0.00 |
| BalancedAcc | 71.43% | 71.43% | +0.00 |

- 逐条翻转：**负向 0 条 / 正向 0 条**。
- 负向拦截原因（两侧完全相同）：`variety_anchor_violation` 22、`blacklist_precheck` 15、`no_match_target_recorded` 4。
- 正向被拦原因（两侧完全相同）：`variety_anchor_violation` 55、`variety_neutral_target_review` 43、`below_threshold` 39、`blacklist_precheck` 3。
- R-07 别名库直查命中：负向 0 / 正向 14 —— **别名库仍不参与匹配链路**（历史限制未解除）。
- 新增 FP 审计：**AFTER 相对 BEFORE 多拦截 0 条**（跨品种 0 / 非跨品种 0）。

> **结论 A：6 条 DSH-B 扩展规则在本回归套件上零边际贡献。** 全部 41 条负向案例已被 `variety_anchor_violation`(R-01) 与 `blacklist_precheck`（父规则 BL-018/BL-016/BL-012 等）覆盖，子规则无一触发。

### 3.1 三种配置对照的边际归因

| 配置 | 负向拦截合计 | 负向黑名单拦截 | 正向拦截合计 | 正向黑名单拦截 |
|---|---|---|---|---|
| base_only (25) | 41 | 15 | 140 | 3 |
| base + 任一新规则 | 41 | 15 | 140 | 3 |
| 仅 1 条新规则 | 41 | 0 | 140 | 0 |

- 6 条新规则的**「本规则直接命中」合计 0 行**（负向 + 正向）。
- 关键读数：`仅 1 条新规则` 时负向仍拦 41、正向仍拦 140 —— **说明这些拦截全部来自非黑名单门禁**（`variety_anchor_violation` / `below_threshold` / `metric_exclusion_hard` / `variety_neutral_target_review`），黑名单在本套件上不是主导门禁。
- 「仅 1 条新规则」下黑名单拦截 = 0，即 6 条新规则单独使用时在 41+200 上完全不命中。

---

## 4. 注入机制自检（证明 BL_LR 改写确实生效）

构造真实语料探针（真实名称池 3103 个 = indicators_v1 名 + ths series/matched）：

| 探针 | left | right | 基线判定 → 联合判定 | 门禁移动 |
|---|---|---|---|---|
| BL-018a | WSA：粗钢：表观消费量：全球（年） | COMEX镍持仓量（手） | `variety_neutral_target_review` → `blacklist_precheck`(BL-018a) | **✓** |
| BL-018b | JFX,ICDX: 锡锭_月累计成交量: 日度 | 热轧普碳钢：标准轨道钢：产量：日本（年） | `variety_neutral_target_review` → `blacklist_precheck`(BL-018b) | **✓** |
| BL-019a | — | — | 语料命中 L=48 R=0，无可用探针（R-01 均触发） | ✗ |
| BL-026 | SMM 再生铅原料库存天数 | SMM: 再生铅冶炼企业原料库存天数: 周度 | `blacklist_precheck` → `blacklist_precheck` | ✗（上游已覆盖） |
| BL-016a | NPI冶炼利润（元/吨） | 再生碳酸锂产量（万吨LCE） | `blacklist_precheck` → `blacklist_precheck` | ✗（上游已覆盖） |
| BL-025a | 焊锡表观消费量时序图 | 国内锡锭产量 | `blacklist_precheck` → `blacklist_precheck` | ✗（上游已覆盖） |

**门禁移动 2/6，联合后由新增规则直接触发 2/6 → 注入机制生效**，零边际不是注入失败，而是子规则被父规则/上游门禁完全遮蔽。

---

## 5. 1134 条 fuzzy_name 完整面无回归回放

| 项 | 基线 25 | 联合 31 | delta |
|---|---|---|---|
| keep | 303 | 303 | 0 |
| review | 234 | 234 | 0 |
| block | 597 | 597 | 0 |
| 状态翻转 | — | — | **0 / 1134** |

联合后黑名单规则触发：`BL-012` 12、`BL-016` 4、`BL-001` 2；**扩展规则触发计数为空**。

---

## 6. 488 模板回放联动（代理数据）

| 项 | 值 |
|---|---|
| 行数 | 488（summary 488 / simulation 488，一一对应） |
| source | PDF 333 / THS 155 |
| risk_level | P0 267 / CLEAN 157 / P1 64 |
| final_status | BLOCKED 232 / PENDING_MATCH 155 / RENDERED 88 / PARTIAL_RENDERED 8 / QUEUED_FOR_REVIEW 4 / RENDER_FAILED 1 |
| route_reason | 全部 series 无效(P0/BLOCKED) 231；THS 模板无 zhiji_id 155；CLEAN 可渲染 89；部分 series 无效降级 8；P0 白名单放行人工复核 3；P1 需人工复核 1；P0 语义冲突阻塞 1 |
| fully_blocked=True / partial_blocked=True | 234 / 8 |
| invalid_series / valid_series 合计 | 260 / 101 |

---

## 7. 优劣分析

**优势（联合后仍然成立的）**
- Recall 100.00%、FN 0：41 条历史 P0/P1 全部拦截，无漏放。
- 零误拦增量：正向 FP 恒为 140，6 条新规则未引入任何新增误拦。
- 纵深防御结构合理：`variety_anchor_violation`(R-01) 承担 22/41 负向拦截，黑名单仅承担 15/41，门禁分层有效。
- 注入链路可验证：BL_LR 改写被 `new_matcher` 感知（2/6 探针门禁移动）。

**劣势 / 缺陷**
1. **扩展规则零边际**：6 条新规则在 41+200 与 1134 三个面上全部不触发。其价值仅是「若上游门禁失效时兜底」，无法用现有套件验证。
2. **黑名单不是主导门禁**：正向 140 条被拦中 137 条（97.9%）来自非黑名单门禁；黑名单仅拦 3 条正向。
3. **R-07 别名库直查仍为 0 命中（负向）**：别名库未接入匹配链路，历史限制未解除，无法追溯修正历史错配。
4. **`resolve_canonical` 硬索引缺陷**：`build_alias_library.py` 第 264-265 行对 `ALIAS[nm]` 硬索引，未入库归一名抛 `KeyError`。本轮在本套件上守卫触发 **0 次**（41+200 全部为已入库名），但歧义清单面上触发 **382 次**（见 T2.4），属真实缺陷。
5. **488 联动为代理数据**：`full_488_template_playback_result.csv` 缺失，代理仅含模板级状态，无逐 pair 证据。
6. Precision 22.65% 偏低源于标签噪声（详见 `alias_lib_v85_final_quality_report.md` 第 6 节），非规则集缺陷。

---

## 8. 边界与披露

1. **两项必需输入缺失**（`semantic_blacklist_v85_final.json` / `full_488_template_playback_result.csv`），已用上述替代方案完成评估，未虚构数据。
2. `resolve_canonical` 守卫仅在当前进程内生效（`.get()` 兜底），**未改写源文件**。
3. 「联合黑名单」是 DSH-B 扩充候选的本地采纳视图，非 DSH-B 官方最终版；若 DSH-B 后续修改候选状态，需重跑本脚本。
4. 正向集 200 为抽样（池 1179），指标存在抽样误差；1134 完整面回放已作为无抽样交叉验证。
5. 全部结论可由 `combine_eval.py` + seed `20261001` 复现。
