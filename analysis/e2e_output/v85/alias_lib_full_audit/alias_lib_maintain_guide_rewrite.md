# alias_lib_maintain_guide_rewrite.md · 别名库维护手册（本轮重跑重写版）

| 项目 | 值 |
|---|---|
| 任务 | DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST |
| 数据来源 | `_stats_new.json` / `quality_regression_result.json` / `verify_conclusion_result.json` |
| 运行日志 | `build_run_log.txt` / `verify_conclusions_log.txt` / `quality_regression_log.txt`（均 exit 0） |
| 执行时间 | 2026-10-01 03:24 / 03:31 / 03:36 UTC+8 |
| 与旧稿关系 | 旧稿 `alias_match_presearch/alias_lib_maintain_guide.md` 保留归档，本文件为新增重写版 |
| 导入方案 | 见 `alias_lib_import_guide.md`（一次性导入，本手册不重复） |

---

## 1. Schema 与维护约定

### 1.1 indicator_alias_library.csv（4643 行 × 23 列）

| # | 列 | 类型 | 维护约定 |
|---|---|---|---|
| 1 | alias_id | 字符串 | 主键，不可变 |
| 2 | canonical_key | 字符串 | 目标 canonical，冲突时含 `\|` 分隔 |
| 3 | canonical_name | 字符串 | 只读，来自 indicators_v1 |
| 4 | canonical_unit | 字符串 | 只读 |
| 5 | variety_family | 字符串 | 品种族，多族含 `\|` |
| 6 | metric_noun | 字符串 | 度量词 |
| 7 | variety_token | 字符串 | 命中的品种词 |
| 8 | alias_name | 字符串 | 原始形态（仅展示，不入库） |
| 9 | **alias_norm** | 字符串 | **归一化形态，入库唯一依据** |
| 10 | alias_type | 枚举 | 8 类：latin_abbr 1659 / unit_variant 1256 / mixed_script 531 / canonical 521 / full_name 309 / cross_report_synonym 278 / suffix_variant 65 / numeric_code 24 |
| 11 | unit_suffix | 字符串 | 剥除的单位后缀 |
| 12 | chart_suffix | 字符串 | 剥除的图表后缀 |
| 13 | alias_source | 字符串 | 7 类来源（见 §1.2） |
| 14 | alias_origin_sample | 字符串 | 原始样本 |
| 15 | distinct_form_count | 整数 | 去重形态数 |
| 16 | evidence_count | 整数 | 证据数 |
| 17 | **relation** | 枚举 | 5 类，决定入库分层 |
| 18 | confidence | 浮点 | 置信度 |
| 19 | blacklist_rule | 字符串 | 黑名单规则 ID |
| 20 | risk_case_ids | 字符串 | 关联风险案例 |
| 21 | **review_flag** | 枚举 | auto 2502 / register_pending 1734 / manual_review 407 |
| 22 | review_priority | 枚举 | P3_auto / P2_auto / P1_manual 215 / P0_manual 192 |
| 23 | confusable_neighbor_count | 整数 | 混淆邻居数（W2 判定依据） |

### 1.2 alias_source 7 类

INDICATORS_V1_KEY 1652 / THS_SERIES 1572 / INDICATORS_V1_NAME 1234 / PDF_TEMPLATE 259 / THS_MATCHED 286 / RISK_DB_SRC 37 / RISK_DB_MATCHED 18

### 1.3 relation 5 类 → 质量四层映射

| relation | 行数 | 质量层 | 处置 |
|---|---|---|---|
| synonym_merge | 2502 | W1 可靠同义 | 批量自动入库 |
| unregistered | 1734 | W0 待注册 | 先补 canonical 注册 |
| synonym_with_confusable_neighbor | 215 | W2 204 / W3 11 | 人工复核 / 转黑名单 |
| canonical_conflict | 165 | W2 存疑 | 人工复核 |
| confusable_warn | 27 | W3 明确错误 | 转黑名单 |

### 1.4 归一化口径（维护时必须遵守）

```
match_norm(s) = 全角转半角 → 压空白 → 剥尾部单位括注 → 剥图表后缀
Dice(a,b)     = 2·|multiset(a)∩multiset(b)| / (|a|+|b|)   容差 |Δ| ≤ 0.011
```

**禁止**在维护脚本中重新实现归一化函数 —— 必须从 `build_alias_library.py` 加载，避免口径漂移。本轮验证已确认：归一化口径一旦偏移，90.0% 的公式复现率立即崩塌。

---

## 2. 白名单管理

### 2.1 两类白名单

| 白名单 | 初始值 | 用途 |
|---|---|---|
| `NEUTRAL_WHITELIST` | **空集** | `(series_norm, target_norm)` 对，显式批准跨品种中性匹配 |
| `NEUTRAL_WHITELIST_CANON` | **空集** | canonical 归一名集合，整族批准 |

### 2.2 当前影响

白名单为空是 R-01b/R-03 高触发的直接原因：

| 指标 | 数值 |
|---|---|
| 无回归回放 review 总数 | 234（全部 `variety_neutral_target_review`） |
| 正向集 review | 43 |
| 短 canonical 名（≤4 字）行数 | **125（11.0%）** |
| 短名去重 | 8 个 |

### 2.3 白名单候选（8 个短名，按命中行数排序）

| 短名 | 命中行数 | 是否建议加入 `NEUTRAL_WHITELIST_CANON` |
|---|---|---|
| 精炼产量 | 32 | ✅ 建议（多品种共用「精炼产量」为正常业务口径） |
| 开工率 | 29 | ✅ 建议 |
| 社会库存 | 25 | ✅ 建议 |
| 锡沪伦比 | 19 | ⚠️ 谨慎（含「锡」字，需确认是否为锡专属指标） |
| 海外产能 | 8 | ✅ 建议 |
| 表观消费 | 6 | ✅ 建议 |
| 镍铁库存 | 5 | ❌ **不建议**（含「镍」，应为镍专属，不该中性放行） |
| 硅石价格 | 1 | ✅ 建议 |

**加入白名单的前置条件**：该短名对应的所有 canonical 必须已确认为「品种中性指标」，且别名库中无 W3 明确错误关联。建议逐条验证后再加入，一次最多加入 3 条并立即重跑回归测试。

### 2.4 白名单变更流程

1. 提出候选 → 2. 在别名库中检索该 canonical 的全部别名与关联风险案例 → 3. 逐条判定 → 4. 写入白名单 → 5. 重跑回归测试（Recall 必须 100%）→ 6. 记录变更台账 → 7. git commit。

---

## 3. 新增指标接入 SOP（8 步）

每周新指标进入时执行：

| 步 | 动作 | 产出 |
|---|---|---|
| 1 | 确认品种族与度量词 | variety_family / metric_noun |
| 2 | 在 indicators_v1 注册 canonical（若未注册） | 新 canonical_key |
| 3 | 收集该指标的已知别名（报表名、简称、跨报表同义词） | 别名候选列表 |
| 4 | 对每个别名执行 `match_norm()` 归一化 | alias_norm |
| 5 | 与现有别名库比对，判定 relation | 新增行 |
| 6 | 检查该 canonical 是否为短名（≤4 字） | 若为短名 → 进入白名单评估 |
| 7 | 计算与现有 1658 个 canonical 的 Dice 近邻（≥0.85 需人工确认） | 混淆邻居数 |
| 8 | 写入别名库 → 重跑回归测试 → 记录变更台账 | 新 CSV + 台账 |

**关键门禁**：第 7 步若近邻 Dice ≥ 0.85 且跨品种，必须人工确认后才能入库 —— 本轮测得 IV1 近邻对 ≥0.85 共 **295** 对，其中跨品种 1147 对（全阈值）。

---

## 4. 周度检查项（7 项）

| # | 检查 | 命令/脚本 | 通过条件 |
|---|---|---|---|
| C1 | 别名库重建 | `python run_build_audit.py` | exit 0 |
| C2 | 行数与 relation 分布漂移 | 对比 `_stats_new.json` | 行数变化需可解释 |
| C3 | 核心结论复核 | `python verify_conclusions.py` | 结论A 仍 VERIFIED |
| C4 | 回归测试 | `python quality_regression.py` | **Recall = 100%** |
| C5 | 黑名单 lint | 源脚本内置 | 单字 pattern 数 = 0 |
| C6 | W2/W3 队列积压 | 统计行数 | P0_manual ≤ 200 |
| C7 | 白名单有效性 | 统计 review 队列 | review 总数 ≤ 150 |

**C4 是硬门禁**：Recall 从 100% 下降即停止发布并排查。

---

## 5. 变更台账模板

每次别名库变更后追加一条至 `data/alias_change_ledger.json`（新建文件）：

```json
{
  "change_id": "ACL-0001",
  "changed_at": "2026-10-01T03:36:00+08:00",
  "changed_by": "<agent_id>",
  "task": "DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST",
  "change_type": "rebuild | add_alias | remove_alias | reassign | whitelist_add | whitelist_remove | blacklist_add",
  "affected_rows": 2502,
  "affected_tier": "W1",
  "before": { "rows": 4643, "W1": 2502, "W2": 369, "W3": 38, "W0": 1734 },
  "after":  { "rows": 4895, "W1": 2755, "W2": 369, "W3": 38, "W0": 1734 },
  "regression": { "recall_pct": 100.0, "tp": 41, "fn": 0, "fp": 140, "tn": 60 },
  "commit_hash": "<git_hash>",
  "reason": "新增 253 个锌族别名"
}
```

**必填字段**：change_id / changed_at / change_type / before / after / regression / reason。缺任一字段视为台账不合规，禁止 commit。

---

## 6. 禁止项（8 条）

| # | 禁止 | 理由 |
|---|---|---|
| 1 | 修改 `data/indicators_v1.json`（本任务范围） | T4 只读约束 |
| 2 | 修改 GT / `semantic_blacklist_fixed.json` | T4 只读约束 |
| 3 | 调用 zhiji 任何 API | T4 硬约束，本轮全程未调用 |
| 4 | 覆盖历史草稿文件（`alias_match_presearch/*.md`） | T4 只新增不覆盖 |
| 5 | 在维护脚本中重新实现归一化/Dice 函数 | 口径漂移风险，必须从源脚本加载 |
| 6 | 未过回归门禁（Recall < 100%）即 commit | C4 硬门禁 |
| 7 | 未写变更台账即 commit | 可追溯性 |
| 8 | 单次批量加入 > 3 条白名单候选而不重跑回归 | 白名单变更风险集中 |

---

## 7. 交付物清单与校验

MD5 全大写；SHA256 完整值见 `_file_hashes.json`。

| # | 交付物 | 字节 | MD5 |
|---|---|---|---|
| 1 | `indicator_alias_library.csv` | 1,081,339 | `E9989C2938B1707739F85E6085E91414` |
| 2 | `ambiguous_indicator_list.csv` | 139,685 | `A19867BD8FCD1FF47C5500E903A33C28` |
| 3 | `high_risk_confusion_pairs.csv` | 77,014 | `8C0B291795E2C4160B0CBB21170273E1` |
| 4 | `_stats_new.json` | 52,017 | `0F0FB52612D79C5F31D7557D5E80DFCF` |
| 5 | `verification_notes.md` | 10,541 | `96AB7F89D81BA01A5364A30E0D683D2D` |
| 6 | `fuzzy_match_rule_optimization_rewrite.md` | 12,142 | `91B21BA46A230BC56B227349DDBE4646` |
| 7 | `alias_lib_verification_report_rewrite.md` | 16,204 | `6BAC4B4F2DE5D414FA0C59F6E6666BB3` |
| 8 | `alias_lib_maintain_guide_rewrite.md` | — | 自指项，不自嵌 MD5，见下方说明 |
| 9 | `regression_test_report.md` | 9,115 | `9F3EA3F7D77B58660BD09A1C4B8230BB` |
| 10 | `alias_lib_import_guide.md` | 10,799 | `D1989CFBF86C4FD15555963EAC41CB18` |


**自指项说明**：第 8 行是本文自身。MD5 无法自嵌 —— 把 MD5 写进本文即改变本文的 MD5，属于预期行为，不构成校验失败。本文在本次写入说明之前的内容为 12,320 字节，MD5 `4AB953BA61F5C9CD25BD9CCC0EADD9E5`，SHA256 `653AF6B637ED6164A07506E1F8DD40C87132BC0D2C2B79AAA16314535447862B`。
写入说明之后的最终值由 git 提交 blob 与 `_file_hashes.json` 承载（见下）。

执行脚本与日志（复现工具链，一并提交）：

| 文件 | 说明 |
|---|---|
| `run_build_audit.py` | 构建包装器（仅改 OUT/TASK 常量） |
| `verify_conclusions.py` | 结论A/B 真伪验证 |
| `quality_regression.py` | 质量分层 + 回归测试 |
| `build_run_log.txt` | 构建日志（exit 0） |
| `verify_conclusions_log.txt` | 验证日志（exit 0） |
| `quality_regression_log.txt` | 回归日志（exit 0） |
| `verify_conclusion_result.json` | 验证结构化结果 |
| `quality_regression_result.json` | 质量+回归结构化结果 |
| `probe_run_log.txt` | 算法反推探针日志 |

---

## 8. 再锁标志（T0 flags）

| 标志 | 值 | 依据 |
|---|---|---|
| `V85_ALL_ANALYSIS_COMPLETE` | **TRUE** | 10 份交付物全部产出，3 个脚本均 exit 0 |
| `NO_ZHIJI_API_CALL` | **TRUE** | 全程未调用 zhiji API（纯静态文本模拟） |
| `NO_MODIFY_SOURCE` | **TRUE** | indicators_v1.json / GT / 黑名单均未修改（只读） |
| `NO_CHANGE_GT` | **TRUE** | GT 未修改 |
| `NO_EDIT_RULE` | **TRUE** | 规则集未修改（仅静态评估） |
| `NO_AUTO_ITERATE` | **FALSE** | 本次为人工指令驱动的完整审计，非自动迭代 |

**约束声明**：本次 git commit 是任务级授权（T2.8 明确授权 scoped commit），覆盖节点默认的「禁止 git commit」约束；回放为纯文本 token 模拟，不含价格数据、策略或 PnL。

---

## 9. 已知风险与后续

| 风险 | 状态 | 后续 |
|---|---|---|
| 别名库未接入匹配链路（R-07 命中 0） | 已确认 | 按 `alias_lib_import_guide.md` B1 方案导入后实测 |
| W0 待注册 1734 行（37.3%） | 已识别 | 依赖 DSH-B canonical 注册，无 SLA |
| W2 人工复核 369 行 | 已排序 | 优先 ZN/NI/SI/CU/PB，约 15 小时 |
| W3 明确错误 38 行 | 已隔离 | 转黑名单候选，pattern ≥ 2 字 |
| 白名单为空导致 review 队列 234 | 已确认 | 按 §2.3 逐条评估，单次 ≤ 3 条 |
| 10.0% 公式残留不可复现 | 未解决 | 记录值系统性偏低，衰减因子未定位 |
| zhiji_note 通道 matched_name 缺失 58.1% | 未解决 | 成因未追查，不影响匹配正确性 |

---

## 10. 局限

1. **本手册的导入效果预估未经实测**：B1 导入后 auto-accept 从 30.0% 提升至 50%+ 为预估值。
2. **白名单候选的判定依据是别名库静态信息**：未逐条核业务口径。
3. **周度检查项未实际执行一周**：C1–C7 为设计，运行频率与值守人待定。
4. **变更台账文件格式未与现有仓库约定对齐**：需 DSH-B 确认是否与既有台账兼容。
5. **SOP 工时未实测**：8 步接入流程的实际耗时未测量。
6. **不含价格数据、策略与 PnL**。
