# alias_lib_v85_final_quality_report.md — 别名库 V85 最终质量报告

| 项目 | 值 |
|---|---|
| 任务 | DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY |
| 交付目录 | `analysis/e2e_output/v85/dshe_alias_integrate_test/` |
| 分支 | `feature/v85-chart-template` |
| 生成时间(UTC+8) | 2026-10-01 |
| 判定引擎 | `alias_match_presearch/build_alias_library.py` 第 1..655 行原样加载 |
| 源 MD5 / SHA256 | `d375f963678d1e89c7e9949805f8433f` / `b756c191ee24882fe6762ece11f77b239ba36e82f28b7bc1d3783a9be4d8f570` |
| 随机种子 | `20261001` |
| 约束遵守 | 未修改 `indicators_v1.json` / GT / `semantic_blacklist_fixed.json` / PDF / THS 模板；未调用 zhiji API；未修改原始 `indicator_alias_library.csv` / `ambiguous_indicator_list.csv`（仅生成重分级副本）；无价格数据 / 策略 / PnL |

---

## 1. 交付物清单（7 份）

| # | 文件 | 说明 |
|---|---|---|
| 1 | `alias_blacklist_combine_eval.md` | 别名库 + 联合黑名单（31 条）回放评估：41 负向 + 200 正向 + 1134 无回归 |
| 2 | `ths_missing_alias.csv` | THS 指标别名覆盖专项：2359 行逐条判定 + 优先级 |
| 3 | `alias_lib_import_validate.py` | 导入链路校验脚本（V1–V9，可运行，支持 `--strict`） |
| 4 | `alias_import_validation_report.md` | 导入校验报告：**import_ready = FALSE** |
| 5 | `ambiguous_indicator_rerated.csv` | 歧义清单 448 行二次复核重分级（原文件未改动） |
| 6 | `alias_lib_v86_roadmap.md` | V86 迭代路线（10 批次，16.25–24.25 人天预估） |
| 7 | `alias_lib_v85_final_quality_report.md` | 本文件 |

支撑产物：`v86_kit.py`（共享引导）、`combine_eval.py` + `_result.json` + `_log.txt`、`ths_alias_gap.py` + `_result.json`、`ambig_rerated.py` + `_result.json` + `_log.txt`、`alias_import_validation_result.json`。

---

## 2. 覆盖度

### 2.1 测试集覆盖

| 集合 | 规模 | 说明 |
|---|---|---|
| 负向（应拦截） | 41 | P0 25 / P1 16；有目标 37 / 无目标 4 |
| 正向候选池 | 1179 | `match_type != none` 且 `verify_status ∈ {VALID, FILLED}` |
| 正向（抽样） | 200 | seed 20261001 |
| 无回归完整面 | 1134 | fuzzy_name 全量，非抽样 |
| THS 覆盖专项 | 2359 | HERMES `ths_candidate_mapping.csv` 全量 |
| 歧义二次复核 | 448 | 歧义清单全量 |
| 模板联动 | 488 | 代理数据（见 §7） |

### 2.2 别名库规模

| 项 | 值 |
|---|---|
| 别名库行数 | 4643 |
| 唯一 `alias_norm` | 2882（1761 行为 unregistered） |
| 引用 canonical 键 | 3300 个 token，**缺失 0** |
| iv1 覆盖 | 1658 键全部可达 |
| 分层 | W1 2502 / W0 1734 / W2 380 / W3 27 |
| 归一化一致性 | `alias_norm` 与 `norm_full(alias_name)` **4643/4643 一致，漂移 0** |
| schema | 23 列齐全，`alias_id` 重复 0，空值 0，非法字符 0，超长 0（最长 78） |

---

## 3. 回归指标

### 3.1 主结果（41 负向 + 200 正向，联合黑名单 31 条）

| 指标 | 值 |
|---|---|
| TP | 41 |
| FN | 0 |
| FP | 140 |
| TN | 60 |
| Accuracy | 41.91% |
| Precision | 22.65% |
| **Recall** | **100.00%** |
| **Specificity** | **42.86%** |
| F1 | 36.94% |
| BalancedAcc | 71.43% |

### 3.2 联合前后对比（BEFORE 25 条 vs AFTER 31 条）

**所有指标 delta = 0**。逐条翻转：负向 0 / 正向 0。新增 FP：0。

### 3.3 三态回放（1134 完整面）

| | keep | review | block |
|---|---|---|---|
| 基线 25 | 303 | 234 | 597 |
| 联合 31 | 303 | 234 | 597 |
| delta | 0 | 0 | 0 |

状态翻转 **0 / 1134**。联合黑名单规则触发：BL-012 12、BL-016 4、BL-001 2；扩展规则触发计数为空。

### 3.4 拦截门禁归因

| 门禁 | 负向 41 | 正向 200 |
|---|---|---|
| `variety_anchor_violation`（R-01 品种锚点） | 22 | 55 |
| `blacklist_precheck`（黑名单） | 15 | 3 |
| `no_match_target_recorded` | 4 | — |
| `variety_neutral_target_review`（R-01b） | — | 43 |
| `below_threshold` | — | 39 |

**黑名单在负向面承担 15/41（36.6%），在正向面仅承担 3/140（2.1%）。** 主导门禁是 R-01 品种锚点与阈值判定，不是黑名单。

### 3.5 注入机制自检

| 探针 | 门禁移动 |
|---|---|
| BL-018a | ✓（`variety_neutral_target_review` → `blacklist_precheck`） |
| BL-018b | ✓（同上） |
| BL-019a | ✗（真实语料中 R-01 均触发，无可用探针；L 命中 48 / R 命中 0） |
| BL-026 | ✗（父规则 BL-012 已覆盖） |
| BL-016a | ✗（上游已覆盖） |
| BL-025a | ✗（上游已覆盖） |

**2/6 门禁移动 → BL_LR 注入生效，零边际不是注入失败，而是子规则被父规则遮蔽。**

---

## 4. THS 别名覆盖专项

| 状态 | 行数 | 占比 |
|---|---|---|
| `UNREGISTERED_ONLY`（库中有形态但无 canonical） | 2299 | 97.46% |
| `RESOLVED_ALIAS_HIT`（别名已可解析） | 55 | 2.33% |
| `TARGET_HIT`（缺别名映射） | 5 | 0.21% |
| `MISSING`（别名库完全无该形态） | **0** | 0% |

- 未覆盖合计 **2304 / 2359 = 97.67%**
- 真正缺别名映射：**5 条**；缺 canonical 注册：**2299 条**
- **MISSING = 0**：别名库对 THS 名称形态的采集已饱和，瓶颈完全在 canonical 注册侧

### 4.1 优先级分桶

| 桶 | 行数 |
|---|---|
| P0_UNREG_NO_CANDIDATE | 302 |
| P1_UNREG_AMBIGUOUS | 1185 |
| P2_UNREG_HIGHCONF | 812 |
| P0_TGT_NO_CANDIDATE | 5 |
| P9_RESOLVED_HIGH / P9_RESOLVED_AMBIG | 52 / 3 |

### 4.2 品种分布

| 品种 | 未解析 | 占比 |
|---|---|---|
| NI | 741 | 32.1% |
| SN | 536 | 23.3% |
| ZN | 381 | 16.5% |
| SI | 324 | 14.1% |
| LI | 209 | 9.1% |
| AL | 69 | 3.0% |
| CU | 39 | 1.7% |

### 4.3 候选质量（关键风险）

未解析 2304 行的 `best_match` 跨品种审计：**442 行（19.2%）是跨品种错误候选**，例：

| THS 图 | 图表品种 | THS 系列名 | best_match | 候选品种 |
|---|---|---|---|---|
| THS-CU-4.4 | CU | Cancelled warrants | 硫化镍矿：产量：伦丁矿业：Eagle矿区 | NI |
| THS-CU-4.3 | CU | 上海、广东…区域库存 | 多晶硅区域库存 | SI |
| THS-AL-3.2 | AL | 综合使用电价 | 工业硅电价 | SI |
| THS-LI-2.1 | LI | 成交量（手） | 沪铅主力连续成交量 | PB |

**按 best_match 直接注册会把 19.2% 的错误固化进 `indicators_v1.json`。**

---

## 5. 歧义清单二次复核

| 新等级 | 行数 | 占比 | 主要依据 |
|---|---|---|---|
| W0_错误别名 | 437 | 97.5% | V86 硬拦截 434（`variety_anchor_violation` 250 / `blacklist_precheck` 183） |
| W3_高风险 | 6 | 1.3% | RISK_DB P0 4 + 降级复核 2 |
| W2_待复核 | 3 | 0.7% | dice 边界 |
| W1_可靠同义 | 2 | 0.4% | V86 通过 + synonym_merge |

- 原 P0 251 → W0 243 / W3 6 / W1 2；原 P1 176 → W0 173 / W2 3；原 P2 21 → 全部 W0
- **与上一轮分级一致性 56.2%**（252 一致 / 196 不一致），不一致方向：W2→W0 173、W1→W0 21、W3→W1 2
- 需人工的真实条目：**W3 6 + W2 3 = 9 行**（其余 437 行只需确认「不应合并」）
- 488 模板联动：41 行命中模板（CLEAN 19 / P0 13 / P1 9；PENDING_MATCH 33 / BLOCKED 5 / RENDERED 2），407 行用品种级弱证据
- 别名库 `relation` 覆盖：448 行中 232 行有标注，**216 行无标注**
- 命中高危混淆对：4 行

---

## 6. 缺陷清单

| # | 缺陷 | 位置 | 严重度 | 实测影响 |
|---|---|---|---|---|
| D1 | `resolve_canonical` 对 `ALIAS[nm]` 硬索引 | `build_alias_library.py` L264–265 | **P0** | 未入库归一名抛 `KeyError`；歧义清单面触发 **382 次**；41+200 面 0 次 |
| D2 | 6 条 DSH-B 扩展黑名单规则零边际贡献 | 联合黑名单 31 条 | P1 | 41+200 与 1134 三面全部不触发；「本规则直接命中」合计 0 行 |
| D3 | R-07 别名库直查未接入匹配链路 | 规则集编排 | P1 | 负向命中 **0**、正向 14 —— 别名库对匹配零贡献 |
| D4 | 导入门禁 G1–G8 与 `review_flag` 标签等价 | 导入校验 V5 | P1 | 2502 条 100% 通过、0 剔除 —— 门禁无独立筛查力 |
| D5 | `alias_norm` → 多个原子键 | 别名库 | **P0** | **165 行**别名归一不唯一，导入后指向歧义 |
| D6 | `canonical_name` → 多个原子键 | 别名库 / iv1 | P1 | 170 个正名对应多个 key（孪生 key） |
| D7 | R-01b 中性目标白名单为空 | 规则集编排 | P1 | 43 条正向被无差别降级为 review |
| D8 | THS `best_match` 跨品种错误 | HERMES mapping | **P0** | 2304 未解析行中 **442 行（19.2%）** 候选品种错误 |
| D9 | 448 歧义行中 216 行无别名库标注 | 别名库覆盖 | P2 | 三分之一歧义条目无法用别名库交叉验证 |
| D10 | 别名库 1761 行 `alias_norm` 无 canonical 绑定 | 别名库 | P2 | 37.9% 行无法解析（与 W0_待注册 1734 高度重叠） |
| D11 | 上一轮口径错误（已更正） | — | — | 「165 行互指环」为复合键比较口径错误，原子键比较后清零；原报告已标注更正 |

---

## 7. 上线风险

| 风险 | 等级 | 说明 |
|---|---|---|
| 直接导入别名库将引入 165 行歧义映射 | **高** | D5：`alias_import_validate.py` 判定 `import_ready = FALSE` |
| 按 THS best_match 批量注册 canonical | **高** | D8：19.2% 候选跨品种错误，将固化进唯一真源且回滚成本高 |
| 门禁 100% 通过率造成虚假安全感 | 中 | D4：2253 条写入的真实质量未经验证，需抽检 100 条 |
| 引擎 KeyError 导致判定中断 | 中 | D1：41+200 面未触发，但歧义面 382 次；任何新语料接入都可能复现 |
| Precision 22.65% 被误读为规则缺陷 | 中 | 实为标签噪声（55 条跨品种 FP 实为 V86 正确拦截） |
| 两处 DSH-B 输入缺失 | 中 | `semantic_blacklist_v85_final.json`、`full_488_template_playback_result.csv` 缺失，已用代理替代，见 §8 |
| 回归抽样误差 | 低 | 正向 200 为 1179 池抽样；已用 1134 完整面交叉验证 |

---

## 8. 人工工作量预估

| 批次 | 内容 | 预估人天 |
|---|---|---|
| B9 | 引擎缺陷修复（3 处） | 0.5–1.0 |
| B1 | 别名库导入 + 165 冲突裁定 + 100 抽检 | 1.5–2.5 |
| B6 | 高危混淆对 P0 102 条 | 3.5 |
| B2 | THS NI 注册 746 | 3.5–5.0 |
| B8 | FP 标签清理 140 | 1.0–1.5 |
| B3 | THS SN+ZN 注册 917 | 4.0–6.0 |
| B4 | THS SI+LI+AL+CU 注册 876 | 3.5–5.0 |
| B7 | 歧义清单真实需人工 9 行 | 0.5 |
| B5 | TARGET_HIT 5 条 | 0.25 |
| B10 | 488 模板补位 155 | 取决于 B2–B4 |
| **合计** | | **16.25–24.25** |

**性价比结论**：B8 + B9（合计 1.5–2.5 人天）对回归指标的改善预期远高于 B2–B4（11–16 人天，且对当前回归套件**无直接影响**）。

---

## 9. 诚实披露

1. **两项必需输入缺失，未虚构**：`semantic_blacklist_v85_final.json` 与 `full_488_template_playback_result.csv` 在 `analysis/e2e_output/v85/` 下不存在。联合黑名单改用 `semantic_blacklist_fixed.json`(25) + `blacklist_extend_candidate.json` 中采纳的 6 条；488 回放改用 `v85_final_integrate/ths_render_task_summary.csv` + `v85_render_fix_review_package/render_simulation_log_fixed.csv` 作代理。**该代理仅含模板级最终状态，无逐 pair 黑名单证据，不参与 TP/TN/FP/FN 计算。**
2. **零边际结论的可靠性**：6 条扩展规则在三个面（41+200、1134、逐规则单测）全部 delta=0。已用 2/6 探针证明注入机制生效，可排除「注入失败」这一替代解释；剩余解释为「子规则被父规则/上游门禁遮蔽」。
3. **`resolve_canonical` 守卫仅进程内生效**：本轮加 `.get()` 兜底避免 KeyError，**未改写源文件**，源脚本缺陷仍在（D1）。
4. **所有指标收益预估未经实测**：`alias_lib_v86_roadmap.md` 中的收益方向与幅度均为线性外推，唯一实测锚点为当前基线（Recall 100% / Specificity 42.86%）。
5. **Precision 22.65% 不可直接解读**：其中 55 条 FP 为旧流水线跨品种错配（V86 拦截正确）、43 条为品种中性需人工确认、39 条为相似度不足、3 条黑名单命中。真实规则质量应通过标签清理后重算评估。
6. **上一轮报告的口径错误已更正**（D11）：「165 行互指环」系复合键比较所致，改用原子键比较后 `alias_is_other_canonical = 0`；真实阻断项是「`alias_norm` 指向多个原子键」165 行，数量巧合相同但性质不同。
7. **未修改任何上游真源**：`indicators_v1.json`、GT、`semantic_blacklist_fixed.json`、PDF/THS 模板、原始别名库与歧义清单 CSV 全部只读；所有产物写入 `dshe_alias_integrate_test/` 新目录。
8. **未调用 zhiji API**，无任何价格数据、策略与 PnL 计算；判定为纯文本 token 静态回放。
9. **B1 门禁有效性未经验证**：2502 条 100% 通过源于门禁条件与 `review_flag` 标签上游等价，属**未知风险**，需补抽检。
10. **448 行歧义中 216 行无别名库标注**，其分级主要依赖 V86 几何判定而非别名库交叉验证。

---

## 10. 结论

1. **拦截能力达标**：Recall 100%、FN 0、488 模板 234 个 fully_blocked —— 风险阻断面完整。
2. **别名库本体质量良好**：schema、归一化口径、键引用完整性全绿（漂移 0 / 悬挂键 0 / 非法字符 0）。
3. **但当前不可导入**：165 行别名归一不唯一（BLOCK）+ 门禁无独立筛查力（WARN），`import_ready = FALSE`。
4. **最大瓶颈不在别名库，在 canonical 注册**：THS 侧 2299 条 `UNREGISTERED_ONLY`，且别名形态采集已饱和（MISSING = 0）。
5. **最大风险在候选质量**：19.2% 的 THS best_match 跨品种错误，盲目注册将污染唯一真源。
6. **最高性价比改进是工程项而非标注项**：修复 D1（KeyError）+ 接入 R-07（D3）+ 启用 R-01b 白名单（D7），合计约 1 人天，可解锁别名库对匹配链路的贡献。
7. **本轮对上一轮的两处实质修正**：44.0% 分歧率口径（298 行缺失被计入，语义冲突实为 17.7%）、165 行互指环口径（实为多键归一，非循环引用）。
