# V88 Phase03 P1 — HERMEShf 门禁矩阵更新报告（T0/T1）

> **TASK_ID**: V88_PHASE03_P1_HERMES_MAIN_JOB
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED: TRUE)
> **日期**: 2026-10-15
> **前置**: V88 Phase03 P0 终审完成（commit `9aec9f9`），`P0_CONTRACT_FROZEN=TRUE`，`P1_STAGE_UNLOCKED=TRUE`
> **本工单范围**: T0 门禁矩阵更新（新增 P0-12/P0-13/P0-14）+ T1 三口径自动校验加固 + T3 R-V88-033 评审（分母切换机制）
>
> **修改文件（仅 1 个）**: `analysis/e2e_output/v88/phase03/p0/scripts/p0_gate_checker.py`（1325 → 1699 行，+374 行）
> **零修改**: `node_binding_engine.py`（DSHE 责任）/ Phase02 生产链路 / `scripts/api_cache.db` / V87 基线 / Release Tag

---

## 0. 一句话结论

> **门禁矩阵扩展完成：主门禁 21 项不变 / 阶段门禁 42 → 45 项（新增 P0-12/P0-13/P0-14）。**
> **三项 P1 门禁全部代码落地并实测生效**：P0-12 CPU 基线 → UNKNOWN（待 DSHB 交付物）| P0-13 噪声率 → UNKNOWN（待 7 天静默期观测）| P0-14 180 指标扩量 → **WARN（实测 615 指标已达标 341.67%，仅缺批次交付物）**。
> **三口径自动校验 `CAL` 门禁上线并 PASS**：A=77.0642% / B=68.3168% / C=100.0000% / C'=77.0642%，`VIOLATION=0`，口径铁律三条全部代码化强制。
> **R-V88-033 评审完成**：衍生品命中 34/59 未达标 → 分母维持 50（口径 C），切换机制已就绪（命中达标后自动 50→109，无需改代码）。
> **门禁总数 22/45 判定，FAIL=0 / BLOCKED_PRE_P0=0。**

---

## 1. 门禁矩阵变更总览

| 项 | 变更前（P0 终审） | 变更后（P1 T0） | 变化 |
|---|:---:|:---:|:---:|
| 主门禁总数（矩阵基准） | 21 | 21 | 不变 |
| 主门禁实测判定数 | 22 | 22 | 不变（S-4a/S-4b 拆分） |
| 阶段门禁总数（矩阵基准） | 42 | **45** | **+3** |
| 阶段门禁实测判定数 | 42 | **45** | **+3** |
| 新增门禁 | — | P0-12 / P0-13 / P0-14 + CAL | +4（CAL 为校验门禁，不占阶段计数） |
| 门禁脚本行数 | 1325 | **1699** | +374 |

### 1.1 新增门禁定义（写入 `STAGE_GATES`）

| 门禁 | 名称 | 阈值 | Owner | 判定源 | 设计原则 |
|------|------|------|-------|--------|----------|
| **P0-12** | CPU 基线门禁(R-V88-034) | 全链路口径峰值 ≤1.75% | DSHB+HERMEShf | DSHB P0-10 专用优化前后对比产物 | 规则先就绪，等交付物 |
| **P0-13** | 告警噪声率门禁(R-V88-035) | <10%（7 天静默期） | HERMEShf | 7 天静默期告警噪声率实测产物 | 规则先就绪，等观测窗口 |
| **P0-14** | 180 指标全量校验(R-V88-036) | 独立库去重指标 ≥180 + 批次交付物 | DSHB+HERMEShf | sqlite 独立复跑 COUNT DISTINCT + 批次报告 | 双判定源，实测优先 |
| **CAL** | 三口径自动校验 | 0 VIOLATION | HERMEShf | 本次门禁报告自身（A/B/C/C'） | 铁律代码化强制 |

---

## 2. 三项 P1 门禁判定实现（T0）

### 2.1 P0-12 CPU 基线门禁 —— 口径不可比拦截

**函数**: `check_cpu_baseline_gate()`

⚠️ **核心设计（关键约束）**：本门禁**只采信全链路业务 CPU 口径**（DSHB P0-10 专用优化前后对比，同脚本/同负载/同时段采集）。

`collect_cpu_baseline()` 的渲染进程瞬时值（`psutil.Process().cpu_percent()`）**被显式排除在判定源之外**，理由：

| 口径 | 实测值 | 来源 | 可比性 |
|------|:------:|------|:------:|
| 全局主机 CPU | ~30.6% | `psutil.cpu_percent()` | ❌ 受并行 agent 污染 |
| **进程级瞬时** | 86.5%（本次实测） | `psutil.Process().cpu_percent()` | ❌ 含 YAML 加载 + Python 启动开销 |
| 进程级归一每核 | 2162.5% | 86.5 / 4 核 × 100 | ❌ 超 100% 无业务含义 |
| **全链路业务稳态** | Phase02 峰值 1.94% | DSHB 稳态观测 | ✅ **唯一判定源** |

数量级差异（86.5% vs 1.94%，差 44 倍）证明三者不可混用。**混用将导致 P0-12 恒 FAIL 的假阻断**，因此代码中 `comparability_enforced=True` 硬性拦截。

**实测判定**：

```
P0-12  UNKNOWN  全链路口径峰值 ≤1.75%（DSHB 优化前后对比）
actual : 待交付物
note   : 待 DSHB P0-10 专用优化前后对比产物（同脚本/同负载/同时段全链路口径）；
         进程级瞬时 CPU 口径不可比，不作为本门禁判定源
```

**交付物候选路径**（DSHB 落盘后自动拾取，无需改代码）：
- `analysis/e2e_output/v88/phase03/p1/dshb/p0_10_cpu_optimization_compare.json`
- `analysis/e2e_output/v88/phase03/p1/dshb/cpu_optimization_comparison.json`
- `analysis/e2e_output/v88/phase03/p1/p0_10_cpu_compare.json`

**字段兼容**：`cpu_peak_pct` / `after_peak_pct` / `after.peak_pct` / `optimized_peak_pct`；基线值同理。

### 2.2 P0-13 告警噪声率门禁 —— 观测窗口不足保护

**函数**: `check_noise_rate_gate()`

三态判定设计（避免「未观测满 7 天就判 FAIL」的假阻断）：

| 条件 | 状态 | 语义 |
|------|:----:|------|
| 交付物缺失 | `UNKNOWN` | 待静默期观测启动（非阻断） |
| 观测天数 < 7 | `WARN` | **观测不足，噪声率暂不作准**（防误判） |
| 噪声率 < 10% | `PASS` | 静默期达标 |
| 噪声率 ≥ 10% | `FAIL` | 告警噪声超标 |

**实测判定**：

```
P0-13  UNKNOWN  <10%（7 天静默期）
actual : 待交付物
note   : 待 HERMEShf 7 天静默期告警噪声率实测产物（F-4 门禁 P1 激活，阈值 <10%）
```

**兼容小数/百分数双形式**：`noise_rate=0.08` 自动归一为 `8.0`。禁止以单次告警计数替代比率口径。

### 2.3 P0-14 180 指标全量校验 —— 双判定源，实测优先

**函数**: `check_expansion_gate()`

| # | 判定源 | 性质 |
|:-:|--------|------|
| ① | 独立库 `sqlite COUNT(DISTINCT indicator_id)` 实测 | **权威**（独立复跑，非采信自报） |
| ② | DSHB 扩量批次交付物存在性 | 可追溯性 |

| 条件 | 状态 |
|------|:----:|
| 指标数 < 180 | `FAIL` |
| 指标数 ≥ 180 + 交付物缺失 | **`WARN`**（数据面达标，缺可追溯性，非能力阻断） |
| 指标数 ≥ 180 + 交付物就位 | `PASS` |
| 独立库不可读 | `UNKNOWN` |

**实测判定（本轮真实数据）**：

```
P0-14  WARN  独立库去重指标 ≥180 + 批次交付物
actual : 实测 615 指标 (映射 608, 行 475593, 达标率 341.6667%)
note   : 实测去重指标 615 ≥ 目标 180（达标率 341.6667%），但缺 DSHB 扩量批次交付物
         （批次可追溯性缺失）；数据面已达标，非能力阻断，待批次计划/执行报告补件
```

> **重要发现**：独立库去重指标实测 **615**，远超 180 目标（达标率 341.67%）。这说明 **DSHB 的「146→180 扩量」目标在 P0 阶段已通过 615 指标的全量映射清单提前达成**，180 指标是渲染侧图表可用指标的子集目标。因此 P0-14 判 WARN 而非 FAIL——**缺的是批次可追溯性文档，不是数据能力**。此项须转 DSHB 补批次执行报告，不应被误读为扩量失败。

---

## 3. 三口径自动校验（T1）—— 口径铁律代码化

### 3.1 设计：把「禁止混用」从文档约定升级为运行时强制

P0 终审在 `gate_matrix.md §5` 确立了口径铁律三条，但当时**仅是文档约定**，无法自动拦截。本次将其升级为 **`CAL` 校验门禁**，违规时直接判 `FAIL` 并阻断 verdict。

**函数**: `audit_caliber_disclosure(report)`

| 铁律 | 代码化判定条件 | 违规编号 |
|------|----------------|----------|
| **R1 禁 A 替 B** | `caliber_a_pass=True` 且 `caliber_b_pass=False` 且 `verdict=PASS` | `VIOLATION_R1_CALIBER_MIXING` |
| **R2 禁自测替 R3** | `abs(caliber_b - 78.82) < 0.01` | `VIOLATION_R2_DSHB_SELFTEST` |
| **R3 C 与 C' 必须同时披露** | `caliber_c is None` 或 `caliber_c_prime is None` | `VIOLATION_R3_CALIBER_C_DISCLOSURE` |
| 完整性 | A/B/C 任一数值缺失 | `VIOLATION_CALIBER_INCOMPLETE` |

**A 达标 + B 未达标但未误判 PASS** → 归为 `NOTE_DUAL_CALIBER_GAP`（提示项，不阻断），因为此时双口径已正确并列披露。

### 3.2 实测结果

```
CAL    PASS  0 VIOLATION
actual : A=77.0642% B=68.3168% C=100.0000% C'=77.0642% | VIOLATION=0 NOTE=0
note   : 三口径铁律全部合规：A/B 并列披露，C 与 C' 同时披露，无 DSHE 自测替代
```

| 口径 | 定义 | 实测 | 归属门禁 | 达标 |
|------|------|:----:|----------|:----:|
| **A** | DB 映射命中率（meta ∩ 独立库 / 109） | 77.0642% | P0-11 | ✅ |
| **B** | 引擎真实渲染覆盖率（source="real" 占比） | 68.3168% | D-7 | ✅ |
| **C** | 命名空间映射覆盖率（衍生品剔除，分母 50） | 100.0000% | P0-9 | ✅ |
| **C'** | 全量参考（同 C 计算，分母 109） | 77.0642% | — | 仅参考 |

**`caliber_mixing=False` / `dshe_selftest_used=False` / `disclosed_ok=True`** —— 三条铁律全部通过。

### 3.3 校验时序设计

`audit_caliber_disclosure()` 在 `run_all()` 中于 **`dual_caliber` 块构建之后、verdict 初判之后**执行，使 R1 能读取 `report["verdict"]` 完成「A 达标+B 不达标却判 PASS」的混用检测。CAL 门禁结果通过 `add()` 追加，违规时计入 `summary["FAIL"]`。

---

## 4. R-V88-033 评审：P0-9 分母切换机制（T3）

### 4.1 实测衍生品命中情况

| 项 | 数值 |
|---|:----:|
| meta_chart 总指标 | 109 |
| 衍生品总数（COMEX_/LC_/SPOT_IS + 7 类后缀） | 59 |
| **衍生品已命中（映射清单双向归一）** | **34** |
| 衍生品目标数 | 59 |
| `derivatives_available` | **False**（34 < 59） |
| 分母模式 | `IN_SCOPE_50` |

### 4.2 分母切换机制（探针式设计，无需改代码）

`check_naming_map(include_derivatives=True)` 为**探针模式**：每次 `run_all()` 执行时自动探测衍生品命中数，达标则自动切换分母 50 → 109。

```python
p09 = check_naming_map()                      # 默认：分母 50（P0 口径）
p09_probe = check_naming_map(include_derivatives=True)  # 探针：检测 59 项
r_v88_033_resolved = (p09_probe["denominator_mode"] == "FULL_109")
if r_v88_033_resolved:
    p09 = p09_probe                          # 自动切换
```

**报告字段** `r_v88_033`：

```json
{
  "resolved": false,
  "derivative_hit": 34,
  "derivative_target": 59,
  "denominator_mode": "IN_SCOPE_50",
  "note": "R-V88-033 待处置：衍生品命中 34/59，分母维持 50（口径 C），全量参考 C'=77.0642%"
}
```

### 4.3 评审结论

> **R-V88-033 评审完成，状态维持 🟡 P2（DSHB），不阻断 P1。**
>
> 1. 衍生品命中 34/59（57.6%），**未达分母切换阈值**，P0-9 维持分母 50 口径，`coverage_pct=100.0000%` PASS。
> 2. **切换机制已代码就绪**：DSHB 补齐衍生品 59 项派生库后，下次 R3 复测自动切至分母 109（口径 C 与 C' 收敛），无需任何代码修改。
> 3. 衍生品 59 项**无直接序列**（需多条现货序列派生计算），DSHE 侧以 simulated 降级渲染（已计入 D-7 `simulated=32`），因此 **C=100% 与 D-7=68.32% 不矛盾**——前者度量命名映射完整性，后者度量渲染能力。
> 4. **验收方式**：`check_naming_map(include_derivatives=True)["denominator_mode"] == "FULL_109"`，可脚本核验。

---

## 5. R3 端到端复测结果（tag=`r3_p1_e2e`）

```
[0/5] 前置校验    : ✅ 引擎已适配 V88_PHASE03_TEST_DB（R-V88-030 RESOLVED）
[1/5] 重建 DB     : ✅ 110,252,032 字节（15s < 300s 阈值）
[2/5] 环境变量注入 : V88_PHASE03_TEST_DB=.../phase03_test.db
[3/5] 门禁判定    : exit=0, verdict=PASS_WITH_UNKNOWN
                    summary={PASS:8, FAIL:0, NOT_APPLICABLE:34, BLOCKED_PRE_P0:0, UNKNOWN:25, WARN:1}
[4/5] 回归套件    : exit=0, 24 用例 {PASS:19, WARN:5, BLOCKED:0, FAIL:0}
[5/5] R-09 隔离   : ✅ 3 行 / code=[AO] / mtime 09-09 17:56 未变
```

### 5.1 门禁判定明细（9 项实测）

| 门禁 | 状态 | 实测 | 阈值 |
|------|:----:|------|------|
| **P0-9** | ✅ PASS | 100.0000% (84/50, IN_SCOPE_50) | ≥95% |
| **P0-11** | ✅ PASS | 77.0642% (84/109) | ≥60% |
| **D-7** | ✅ PASS | 68.3168% (real=69/sim=32) | ≥60% |
| **CAL** | ✅ PASS | A/B/C/C' 全部披露，VIOLATION=0 | 0 VIOLATION |
| **P0-12** | ❓ UNKNOWN | 待 DSHB 交付物 | 峰值 ≤1.75% |
| **P0-13** | ❓ UNKNOWN | 待 7 天静默期 | <10% |
| **P0-14** | ⚠️ WARN | 实测 615 ≥ 180（341.67%），缺批次交付物 | ≥180 + 交付物 |
| **P0-10** | ⚪ N/A | 进程级 86.5%（不可比，判定权移交 DSHB） | ≤1.75% |
| **R-V88-033** | 🟡 待处置 | 衍生品命中 34/59，分母维持 50 | 59 |

### 5.2 回归 24 用例 WARN 明细（全部为 P1 交付物待落地，非缺陷）

| 用例 | 状态 | 说明 | 归属 |
|------|:----:|------|------|
| A-4 DQA 规则升级 | ⚠️ WARN | 期望 8 条（Phase02 5 条），DQA 规则为 DSHB P1 交付物 | DSHB |
| A-5 扩量批次计划 | ⚠️ WARN | 目标 146→180，批次计划属 DSHB P1 交付物 | DSHB |
| C-5 CPU FUSE 余量 | ⚠️ WARN | 进程 86.5%（口径不可比声明，判定权移交 DSHB 全链路口径） | DSHB |
| D-2 阈值三档可触发 | ⚠️ WARN | GREEN/YELLOW/RED/BLUE ↔ WARN/CRIT 映射表待 DSHE 落地 | DSHE |
| D-3 告警噪声率 | ⚠️ WARN | 目标 <10%，须 7 天静默期实测 | HERMEShf |

> **验收标准「24 回归用例无 BLOCKED、无 FAIL」已达成**：`BLOCKED=0 / FAIL=0`。5 项 WARN 均为 P1 阶段交付物（A-4/A-5 → DSHB，C-5 口径声明，D-2 → DSHE，D-3 → 静默期观测），非缺陷。

---

## 6. 跨 Agent 交叉核验（DSHB/DSHE 前置资料）

### 6.1 数据层口径核验（DSHB 前置资料 vs HERMEShf 独立实测）

| 项 | DSHB 自报 | HERMEShf 实测 | 一致性 |
|---|:--------:|:------------:|:------:|
| 总行数 | 475,593 | 475,593 | ✅ 一致 |
| 总指标数 | 615 | 615 | ✅ 一致 |
| 已映射指标 | 608 (98.9%) | 608 | ✅ 一致 |
| DB 映射命中率 | 84/109 = 77.06% | 84/109 = 77.0642% | ✅ 一致（口径 A） |
| 主键冲突 / 导入错误 | 0 / 0 | 0 / 0 | ✅ 一致 |

### 6.2 渲染侧口径核验（DSHE 前置资料 vs HERMEShf R3 全量）

| 项 | DSHE 自测 | HERMEShf R3 全量 | 处置 |
|---|:--------:|:----------------:|------|
| 覆盖率 | **78.82%**（67/85，抽样） | **68.3168%**（69/101，全量） | ⚠️ 差 10.5pp，**以 R3 全量为唯一验收依据** |
| 分母 | 85（matchable 图表） | 101（全量图表） | 差值源于采样范围，非矛盾 |
| 引擎 MD5 | `cd73deaeec54a7f1f8bde92c1300a9dc` | 本轮 grep 探测已适配 | ✅ R-V88-030 RESOLVED |

> **口径铁律 R2 已由 `CAL` 门禁自动强制**：若后续任一报告以 78.82% 作为 D-7 验收依据，`CAL` 门禁将立即判 FAIL 并阻断 verdict。本次 `dshe_selftest_used=False`。

### 6.3 三方口径无混用声明

- 口径 A（77.0642%）仅用于 P0-11（数据层就绪度辅助），**未用于声称 D-7 达标**。
- 口径 B（68.3168%）为 D-7 唯一验收依据，来源 HERMEShf 独立复跑 101 张图表。
- 口径 C（100.0000%）与 C'（77.0642%）**已同时披露**，衍生品剔除已显式声明为范围界定（34/59 命中，未达切换阈值）。
- 零处「以 A 替 B」「以自测替 R3」混用。

---

## 7. 交付物清单（本报告对应）

| # | 文件 | 内容 |
|:-:|------|------|
| 1 | `v88_phase03_p1_hermes_gate_update_report.md` | **本文**：门禁矩阵更新 + 三口径校验 + R-V88-033 评审 |
| 2 | `p0_gate_checker.py` | 更新后脚本（1699 行，+374 行） |

---

## 8. 约束合规（10/10）

- ✅ `node_binding_engine.py` 未修改（DSHE 责任）
- ✅ Phase02 生产链路零修改
- ✅ `scripts/api_cache.db` 只读零污染（3 行 / code=[AO] / mtime 09-09 17:56 未变）
- ✅ `phase03_test.db` 未入库（AGENTS.md §7 红线，运行时重建 15s）
- ✅ V87 基线零修改 / Release Tag 未改
- ✅ 零知几 API 调用（全部离线 sqlite + 本地文件）
- ✅ P0 既有资产 append-only（`p0_gate_checker.py` 仅增量新增函数与字段，未改写 P0-9/P0-10/P0-11 既有判定逻辑）
- ✅ 旧口径留档不删（`legacy_jsonl_intersection` 保留观测）
- ✅ BRANCH_LOCKED / NO_OVERWRITE
- ✅ MD5 口径 LF 规范化

---

## 9. 已踩坑记录（避免下一轮重蹈）

1. **`resolve_testdb_path()` 返回元组 `(path, source)`**，不是裸路径 —— 首次接入 P0-14 时按裸路径 `sqlite3.connect(db)` 导致 UNKNOWN 假阴性，须 `db, _src = resolve_testdb_path()` 解包。
2. **`fmt_pct()` 已内含 `%` 字符** —— 在 f-string/`%` 格式化中再写 `%s%%` 会得到 `77.0642%%`（双百分号）。统一用 `%s`。
3. **P0-14 达标但缺交付物应判 WARN 而非 UNKNOWN** —— WARN 是 P1 阶段的真实状态（数据面达标、文档缺失），折算为 UNKNOWN 会掩盖「缺批次可追溯性」这一真实问题。
4. **进程级 CPU 实测 86.5%（归一每核 2162.5%）** —— 该值远超 FUSE 2.0%，若误用作 P0-12 判定源会恒 FAIL。已通过 `comparability_enforced=True` 硬性排除，并在 P0-12/C-5 两处显式声明。
5. **CAL 校验必须在 verdict 初判之后执行** —— R1 检测需要读取 `report["verdict"]`；若放在 dual_caliber 构建之前，A 达标+B 不达标却判 PASS 的混用无法被检出。

---

*Report Generated: 2026-10-15*
*Generated by: HERMEShf Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED: TRUE)*
*Status: PHASE03_P1_GATE_UPDATE=COMPLETE | PHASE03_P1_CALIBER_AUDIT=ACTIVE | PHASE03_P1_HERMES_MAIN=IN_PROGRESS*
