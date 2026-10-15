# V88 Phase03 P1 — 门禁持续巡检日志（T0）

> **TASK_ID**: V88_PHASE03_P1_HERMES_FOLLOWUP_JOB
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED: TRUE)
> **巡检轮次**: R1（2026-10-15）
> **巡检范围**: 46 项阶段门禁全量在线 + P0-12/P0-13/P0-14 动态复核 + CAL 三口径运行时校验 + P0-9-AUDIT 自报口径审计
> **前置**: `V88_PHASE03_P1_HERMES_MAIN_JOB` COMPLETE（commit `083fa73`）；DSHB P1 主任务 commit `624e2b1`、DSHE P1 主任务 commit `7cbd5a4` 已落盘 37 个交付物文件

---

## 0. 本轮巡检核心结论

| 项 | R1 巡检结果（2026-10-15） | 相对 MAIN 轮变化 |
|---|:---:|:---:|
| 阶段门禁总数 | **46** | 45 → 46（+P0-9-AUDIT） |
| 门禁总数 PASS | **10** | 8 → 10 |
| 门禁总数 FAIL | **2** | 0 → 2（新增，均为真实阻断项） |
| BLOCKED_PRE_P0 | **0** | 0 → 0 |
| UNKNOWN | 23 | 25 → 23（2 项转为实质判定） |
| WARN | 0 | 1 → 0（P0-14 转 PASS） |
| verdict | **FAIL** | PASS_WITH_UNKNOWN → FAIL |
| **P1 准入判定** | **ADMIT_WITH_BLOCKERS（阻断，禁止宣布完成）** | CONDITIONAL_ADMIT → 阻断 |

> ⚠️ **关键结论**：DSHB/DSHE P1 主任务交付已落地并被本巡检完整拾取。复核结果并非「三项遗留门禁全部 PASS」，而是**两项真实阻断**：
> 1. **P0-12 FAIL** —— DSHE 交付物已提交，但**未提供全链路业务稳态 CPU 优化后数值**（仅进程级 99.34%/每核 620.87%，且报告显式声明「与 FUSE 2.0% 不可直接对比」），P0-10 优化达标性**无法判定**。
> 2. **P0-9-AUDIT FAIL** —— DSHB 自报 P0-9 = **109/109 = 100.00%**，但其计算式 `min(distinct_mapped_ids=197, 109) = 109` 为**数学恒真上界**，与 meta 侧实际可映射数无关；独立复算真实交集仅 **98/109 = 89.91%**，**虚高 10.09pp**。
>
> **P1_DONE 维持 FALSE。** T5「全部 3 项遗留门禁 PASS → FULL_ADMIT」的前提**未满足**，故**不输出闭环验收报告**（避免伪造完成状态）；本报告与风险评审报告即为本轮权威交付物。

---

## 1. 巡检流程（R1）

| 步 | 动作 | 结果 |
|:--:|------|------|
| 1 | `git pull --rebase origin feature/v88-g1` | 拾取 DSHB `624e2b1` + DSHE `7cbd5a4`，37 个新文件 |
| 2 | 扫描 `p1/dshb`、`p1/dshe`、`p1/scripts` 交付物 | P0-12/13/14 候选路径**全部命中** |
| 3 | 扩展门禁候选路径（对齐 DSHB/DSHE 实际落盘文件名） | 3 类路径全覆盖，含 md 报告末位候选 |
| 4 | 重建 `phase03_test.db` 至 P1 真实状态 | 475,593→**590,411** 行 / 615→**674** 指标 / 59 派生 114,818 行 |
| 5 | 独立运行门禁判定（不覆盖派生库） | 22/46 判定，2 FAIL |
| 6 | 全链路回归套件 24 用例 | PASS=19 / WARN=5 / BLOCKED=0 / FAIL=0 |
| 7 | R-09 生产库零污染校验 | 3 行 / code=[AO] / mtime 未变 ✅ |

### 1.1 独立库状态（重建后）

| 项 | P0 状态 | **P1 状态（本轮）** | 变化 |
|---|:------:|:------------------:|:----:|
| 总行数 | 475,593 | **590,411** | +114,818 |
| 去重指标 | 615 | **674** | +59 |
| 已映射指标 | 608 | **667** | +59 |
| 派生指标 | 0 | **59**（59/59 成功，0 失败） | 新增 |
| 库体积 | 110,252,032 B | 110,252,032 B | 不变（派生行追加） |
| `testdb_freshness_match` | False | **True** | ✅ 与 DSHB 重建产物一致 |

> **重要修正**：P1 首轮巡检时本地库仍为 P0 状态（615 指标），导致 P0-14 的实测值偏低。经核实 `r3_auto_retest.sh` 阶段 1 调用的是 **P0 版重建脚本**（不含派生逻辑），而 DSHB 的派生逻辑在 `p1/scripts/derive_indicators.py`。本轮已独立执行该脚本完成派生，**此后所有 P0-14/口径 A/口径 B 判定均基于 P1 真实库状态**。

---

## 2. 46 项阶段门禁全量状态

### 2.1 实测 PASS（10 项）

| 门禁 | 实测 | 阈值 | 较 MAIN 轮 |
|------|------|------|:----------:|
| **D-7**（口径 B） | **80.1980%** | ≥60% | 68.32% → **80.20%（+11.88pp）** |
| **P0-11**（口径 A） | **89.9083%**（98/109） | ≥60% | 77.06% → **89.91%（+12.84pp）** |
| **P0-9**（口径 C） | 100.0000%（98/50，IN_SCOPE_50） | ≥95% | 100%（分母切换前提未达，维持 50） |
| **P0-14** | 674 指标 / 667 映射 / 590,411 行（达标率 374.44%） | ≥180 + 批次交付物 | WARN → **PASS** |
| **P0-13** | 9.5432% 噪声率（590,411 数据点 / 56,344 噪声点） | <10% | UNKNOWN → **PASS** |
| **CAL** | A/B/C/C' 全披露，VIOLATION=0 | 0 VIOLATION | PASS → PASS |
| R-1 / R-2 / R-3 | 0 ERROR / 101 渲染 / 三级降级 0 崩溃 | — | 全 PASS |
| R-4 | p99=39.193 ms | <500 ms | PASS |

### 2.2 FAIL（2 项，真实阻断）

#### P0-12 CPU 基线门禁 → **FAIL**

| 项 | 值 |
|---|---|
| 交付物 | `p1/dshe/v88_phase03_p1_cpu_baseline_contrast_report.md` ✅ **已提交** |
| `artifact_delivered` | **True** |
| `artifact_declares_incomparable` | **True**（报告原文「进程级瞬时值与 Phase02 FUSE 2.0% 全链路业务稳态均值不可直接对比」） |
| `declares_optimized_full_chain` | **False** |
| 提取到的全链路优化后峰值 | **None** |
| 阈值 | 全链路业务稳态峰值 ≤1.75% |

**判定理由**：交付物已提交但**未提供任何全链路业务稳态 CPU 优化后数值**。报告仅含：
- 进程级瞬时峰值 **99.34%**（每核 **620.87%**，CPU 均值 97.73%）
- P99 时延 629.4 ms
- 及一段**口径不可比声明**

这属于「已交付但口径不符」，判 **FAIL 而非 UNKNOWN**——若判 UNKNOWN 将使该门禁永久悬置，交付方可用「已提交报告」规避提供可判定数据。

> ⚠️ **防误判记录（本轮踩坑）**：首轮巡检时，门禁曾把该报告中的 `2.0% (FUSE)` **误识别为优化后峰值**并判 FAIL。经复核，2.0% 是 Phase02 **熔断阈值**（对照值），1.94% 是 Phase02 **峰值**（历史值），二者均非本次优化后实测值。已加固 `_extract_full_chain_cpu_peak()`：
> - 增加**阈值语境过滤**（`FUSE`/`阈值`/`threshold`/`熔断`/`Phase02`/`历史`/`对标`/`基准`/`参考`/`参照`/`目标`）
> - 增加 `_md_declares_optimized_full_chain()` 声明校验（须同时出现「优化后」+「全链路」语境）
> - 增加 `artifact_declares_incomparable` 标记（报告显式声明「不可比」即视为未提供判定数据）

#### P0-9-AUDIT 自报口径审计 → **FAIL**（本轮新增门禁）

| 项 | DSHB 自报 | HERMEShf 独立复算 |
|---|:--------:|:-----------------:|
| 分子 | **109** | **98** |
| 分母 | 109 | 109 |
| 覆盖率 | **100.00%** | **89.9083%** |
| `distinct_mapped_ids` | 197 | 864（双向键） |
| 衍生品命中 | 未披露 | **48/59** |
| 分母模式 | FULL_109（已切） | **IN_SCOPE_50** |

**捕获的 3 项违规**：

1. **ORPHAN_NUMERATOR** —— 自报分子 109 = 分母 109，但 `distinct_mapped_ids=197 > 109`，说明分子由 `min(197, 109)` 得出，属**数学恒真上界**；独立复算真实交集仅 98，自报覆盖率虚高，与 meta 侧实际可映射数无关。
2. **DIVERGENCE** —— 自报 100.00% vs 独立复算 89.91%，**偏离 10.09pp**（阈值 1pp）。
3. **DENOMINATOR_NOT_READY** —— 自报分母已切 109，但衍生品命中 **48/59 未达阈值 59**，分母切换前提不满足。

**根因定位**：`analysis/e2e_output/v88/phase03/p1/scripts/export_mapping_list.py` 第 99-100 行：

```python
p0_9_denominator = 109  # Fixed denominator per P1 requirement
p0_9_numerator = min(distinct_mapped_ids, p0_9_denominator)   # ← min(197,109)=109 恒真
```

`distinct_mapped_ids` 统计的是 `indicator_id_mapped` 去重数（197 个代码），而 P0-9 定义为 `|meta_indicator ∩ mapped_indicator| / |meta_indicator|`（meta 侧 109 个指标中实际可映射的数量）。二者是**完全不同的口径**，`min()` 只是把它们压到同一上限，产出必然 100%。

---

## 3. 未命中衍生品清单（R-V88-033 真实缺口 11 项）

| # | meta 衍生品指标 | 映射清单近似项 | 缺口性质 |
|:-:|----------------|----------------|----------|
| 1 | `COMEX_AL` | COMEX_CU / COMEX_CU_CHANGE / COMEX_CU_LME_SPREAD | 仅建 CU 品种 COMEX，缺 AL 品种 |
| 2 | `COMEX_NI` | 同上 | 缺 NI 品种 |
| 3 | `COMEX_PB` | 同上 | 缺 PB 品种 |
| 4 | `COMEX_SN` | 同上 | 缺 SN 品种 |
| 5 | `COMEX_ZN` | 同上 | 缺 ZN 品种 |
| 6 | `CU_BALANCE_SHEET` | **无** | 持仓平衡表完全缺失 |
| 7 | `LC_FU00015030` | **无** | LC 期权链特定合约缺失 |
| 8 | `LC_HOLD_OPEN` | **无** | LC 持仓未平仓缺失 |
| 9 | `PB_TOP20_LONG` | PB_TOP20_NET | 仅建 NET，缺多空拆分 |
| 10 | `PB_TOP20_SHORT` | PB_TOP20_NET | 仅建 NET，缺多空拆分 |
| 11 | `SPOT_IS` | SPOT_IS_CHANGE | 仅建变化量，缺水平值 |

> **缺口归因**：DSHB 已建 59 项派生指标（13 个类目全部执行成功），但**派生的是「变化量/比率/分位」类指标**（`*change`、`*_ratio`、`*_percentile`、`*_net`、`*_spread`），而 meta 侧 11 项未命中指标需要的是**水平值/多品种扩展/持仓结构类**指标（`COMEX_AL`、`TOP20_LONG/SHORT`、`BALANCE_SHEET`、`HOLD_OPEN`、`SPOT_IS`）。这是**指标类型覆盖缺口**，不是派生脚本执行失败。

---

## 4. CAL 三口径运行时校验（T1）

| 口径 | 实测 | 归属 | 达标 | 变化 |
|------|:----:|------|:----:|:----:|
| **A** | 89.9083% | P0-11 | ✅ | 77.06% → 89.91% |
| **B** | 80.1980% | D-7 | ✅ | 68.32% → 80.20% |
| **C** | 100.0000% | P0-9 | ✅ | 100%（分母维持 50） |
| **C'** | 89.9083% | 全量参考 | — | 77.06% → 89.91% |

```
CAL    PASS  0 VIOLATION
A=89.9083% B=80.1980% C=100.0000% C'=89.9083% | VIOLATION=0 NOTE=0
```

| 铁律 | 结果 |
|------|:----:|
| R1 禁 A 替 B | ✅ `caliber_mixing=False` |
| R2 禁自测替 R3 | ✅ `dshe_selftest_used=False`（验收依据为 80.1980% R3 全量） |
| R3 C 与 C' 同时披露 | ✅ C=100.0000% + C'=89.9083% 并列 |

> **注意**：`CAL` 与 `P0-9-AUDIT` 是两道独立防线。`CAL` 校验**门禁报告自身**的披露合规性（本次 PASS）；`P0-9-AUDIT` 校验**交付方自报值**是否可信（本次 FAIL）。前者管「报告怎么写」，后者管「交付方说什么」，二者互补。

---

## 5. 回归 24 用例（T4 前置核验）

```
verdict: PASS_WITH_WARN | 汇总: {PASS: 19, WARN: 5, FAIL: 0, BLOCKED: 0}
```

| 用例 | 状态 | 指标 | 归因 | 是否可解锁 |
|------|:----:|------|------|:----------:|
| A-4 DQA 规则升级 | ⚠️ WARN | 期望 8 条（Phase02 5 条） | DSHB 已交付 DQA 8 条（7 PASS + 1 WARN：DQA-03 时间连续性） | 🟡 逻辑门禁 P1/P2 判定，回归套件仍标 WARN |
| A-5 扩量批次计划 | ⚠️ WARN | 146→180 | P0-14 已 PASS（674 指标），批次交付物就位 | 🟡 同上 |
| C-5 CPU FUSE 余量 | ⚠️ WARN | 进程 87.5% / 每核 2187.5% | 口径不可比声明，判定权移交 DSHB 全链路口径 | 🔴 同 P0-12，DSHE 未提供全链路值 |
| D-2 阈值三档可触发 | ⚠️ WARN | GREEN/YELLOW/RED/BLUE ↔ WARN/CRIT | DSHE 已交付四级映射表 + DSHB 已交付三级阈值基线（652 指标） | 🟡 逻辑门禁 P1/P2 判定 |
| D-3 告警噪声率 | ⚠️ WARN | <10%（7 天静默期） | **P0-13 门禁已权威判定 PASS（9.5432%）** | 🟢 门禁层已解锁，回归层维持 WARN（观测窗口声明缺失） |

> **回归层与门禁层差异说明**：D-3 已由 **P0-13 门禁 PASS**（权威判定），回归套件 D-3 维持 WARN 是因该用例沿用「7 天静默期」措辞而未读取门禁判定结果。**门禁层为准**。A-4/A-5/D-2 为逻辑门禁在 P1/P2 判定，回归层仅作观测，不阻断。

---

## 6. 交付物拾取能力升级（本轮改造）

| 项 | MAIN 轮 | FOLLOWUP 轮 |
|---|:------:|:-----------:|
| P0-12 候选路径 | 3 条（仅 dshb） | **10 条**（dshb + dshe，含 md 末位候选） |
| P0-13 候选路径 | 3 条（仅 hermes） | **7 条**（dshb + dshe + hermes） |
| P0-14 候选路径 | 3 条 | **5 条**（含 `derived_indicator_stats.json`） |
| P0-12 md 解析 | 不支持 | **支持**（严格口径过滤 + 阈值语境排除 + 声明校验） |
| P0-13 嵌套结构 | 不支持 | **支持**（`overall.noise_rate` / `breakdown` / `meets_target`） |
| P0-14 派生证据 | 不支持 | **支持**（`derived_*` 字段 + `testdb_freshness_match` 新鲜度核验） |
| 映射清单选取 | 固定 P0 路径 | **动态** `_latest_mapping_json()`（p1/dshb > p1 > p0） |
| P0-9 自报审计 | 无 | **新增** `audit_self_reported_p09()` |

> **本轮踩坑（已修复）**：DSHB/DSHE 实际落盘文件名与 MAIN 轮预设候选路径**完全不一致**（DSHB 噪声率在 `p1/dshb/noise_rate_data.json` 而非预设的 `p1/hermes/alert_noise_rate_report.json`；DSHE CPU 是 md 报告而非 json）。若不扩展路径，三项门禁会**全部维持 UNKNOWN**，形成「交付物已到位但门禁不认」的假悬置。

---

## 7. 下一轮巡检触发条件

| 触发事件 | 门禁 | 预期转态 |
|----------|------|----------|
| DSHB 提供全链路业务稳态 CPU 优化前后对比（同脚本/同负载/同时段，输出 `cpu_peak_pct` JSON） | P0-12 | FAIL → PASS/FAIL |
| DSHB 修复 `export_mapping_list.py` P0-9 计算（改 `min()` 为 `meta ∩ mapped` 真实交集） | P0-9-AUDIT | FAIL → PASS |
| DSHB 补齐 11 项缺失衍生品（5 COMEX 品种 + BALANCE_SHEET + LC×2 + TOP20 多空 + SPOT_IS） | R-V88-033 | 48/59 → 59/59，自动触发分母 50→109 |
| 上述全部达成 | T5 | 输出 `FULL_ADMIT` + P1 闭环验收报告 |

---

*Report Generated: 2026-10-15 UTC+8*
*Generated by: HERMEShf Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED: TRUE)*
*Status: PHASE03_P1_GATE_CONTINUOUS_MONITOR_R1=COMPLETE | PHASE03_P1_DONE=FALSE | P1_ADMIT=ADMIT_WITH_BLOCKERS*
