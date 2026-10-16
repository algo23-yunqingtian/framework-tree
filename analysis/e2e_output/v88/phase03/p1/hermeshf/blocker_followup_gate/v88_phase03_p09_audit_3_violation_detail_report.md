# V88 Phase03 P1 — P0-9-AUDIT 三条违规专项审计报告

> **TASK_ID**: `V88_PHASE03_P1_HERMESHF_BLOCKER_FOLLOWUP_AUDIT_GATE_JOB`（T1）
> **AGENT**: HERMEShf | **BRANCH**: `feature/v88-g1`（BRANCH_LOCKED: TRUE）
> **生成时间**: 2026-10-16 UTC+8
> **NO_OVERWRITE**: TRUE | **NO_ZHIJI_API_CALL**: TRUE
> **审计源**: `p0_gate_checker.py::audit_p09()` 独立复算 vs DSHB 自报

---

## 0. 一句话结论

P0-9-AUDIT 三条违规的**根因均为 `export_mapping_list.py` 第99-100行 `min(distinct_mapped_ids, 109)` 恒真上界**，导致自报覆盖率虚高 10.09pp。DSHB 已在 commit `499ff25` 中修复为 `p0_9_numerator = len(p0_9_intersection)`（真实交集），**三条违规已全部消除，P0-9-AUDIT 从 FAIL 跃迁至 PASS**。

---

## 1. 违规明细（历史状态，修复前快照）

### 1.1 ORPHAN_NUMERATOR

| 属性 | 值 |
|------|-----|
| **违规类型** | `ORPHAN_NUMERATOR` |
| **描述** | 自报分子 = 分母 = 109，但 `distinct_mapped_ids = 237 > 109`（min() 恒真上界） |
| **自报分子** | 109（`min(distinct_mapped_ids=237, 109) = 109`） |
| **真实分子** | 98（meta 侧可映射数 ∩ mapped 交集） |
| **虚高贡献** | 109 - 98 = 11 个孤儿指标被计入分子 |
| **代码位置** | `p1/scripts/export_mapping_list.py` 原第99-100行 |

**检测逻辑**（`p0_gate_checker.py::audit_p09()`）：
```
ORPHAN_NUMERATOR —— 自报分子==分母 但 distinct_mapped_ids >> 分母
                    （min() 恒真上界：min(X, N) ≤ N 恒成立）
```

**定位堆栈**：
1. `export_mapping_list.py` → `p0_9_numerator = min(distinct_mapped_ids, 109)` → 恒为 109
2. `p0_gate_checker.py::audit_p09()` → 独立复算 `intersection_count = 98`（meta ∩ mapped 真实交集）
3. 偏差 = 109 - 98 = 11 → 虚高 10.09pp

### 1.2 DIVERGENCE

| 属性 | 值 |
|------|-----|
| **违规类型** | `DIVERGENCE` |
| **描述** | 自报覆盖率 100.00% vs 独立复算 89.9083%，偏离 10.09pp（阈值 1pp） |
| **自报覆盖率** | 100.00%（109/109） |
| **独立复算覆盖率** | 89.9083%（98/109） |
| **偏离值** | 10.0917pp |
| **阈值** | > 1pp 即违规 |
| **虚高贡献** | 10.09pp（与 ORPHAN_NUMERATOR 同根因） |

### 1.3 DENOMINATOR_NOT_READY

| 属性 | 值 |
|------|-----|
| **违规类型** | `DENOMINATOR_NOT_READY` |
| **描述** | 自报分母已切 109，但衍生品命中仅 48/59（未达 59/59 阈值） |
| **自报分母** | 109（已切换） |
| **衍生品命中** | 48/59（缺口 11 项） |
| **阈值** | 59/59 方可切分母 |
| **缺口项** | COMEX_AL/NI/PB/SN/ZN(仅建CU) / CU_BALANCE_SHEET / LC_FU00015030 / LC_HOLD_OPEN / PB_TOP20_LONG\|SHORT / SPOT_IS 水平值 |

---

## 2. 虚高 10.09pp 拆解

| 维度 | 自报值 | 独立复算值 | 差值 | 根因 |
|------|--------|-----------|------|------|
| 分子 | 109 | 98 | +11 | `min(237, 109)=109` 恒真上界 |
| 分母 | 109 | 109 | 0 | 一致 |
| 覆盖率 | 100.00% | 89.9083% | +10.09pp | 分子虚高传导 |
| 衍生品命中 | — | 48/59 | -11 | 11项衍生品无 meta 映射 |

**10.09pp 虚高归因**：
- **11 个孤儿指标**（`distinct_mapped_ids=237` 中有 11 个不在 DSHE 109 项清单内）被 `min()` 恒真上界计入分子
- **11 项衍生品缺口**（48/59）未被检出为分母切换前提未满足

---

## 3. 修复验证（commit `499ff25` 之后）

| 检查项 | 修复前 | 修复后 | 状态 |
|--------|--------|--------|------|
| `export_mapping_list.py` 第141行 | `min(distinct_mapped_ids, 109)` | `len(p0_9_intersection)` | ✅ 已修复 |
| P0-9 自报覆盖率 | 100.00% | 100.0000% | ✅ 一致 |
| P0-9-AUDIT 独立复算 | 89.9083% | 100.0000% | ✅ 收敛 |
| 虚高偏差 | 10.09pp | 0.00pp | ✅ 消除 |
| 衍生品命中 | 48/59 | 59/59 | ✅ 补齐 |
| P0-9-AUDIT verdict | **FAIL** | **PASS** | ✅ 跃迁 |

**实测命令**：
```bash
python3 p0_gate_checker.py --json
# → P0-9-AUDIT: PASS | 自报1份 | 独立复算 100.0000% (交集109/0) | 衍生品命中 59/59
```

---

## 4. IDENTITY_FORM 变体检测说明

本轮新增的 `IDENTITY_FORM` 违规类型用于捕获分母误用恒等式变体：
- 分子 == 分母但 `distinct_mapped_ids >> 分母`（分母 ≠ 109 的变体）
- 与 `ORPHAN_NUMERATOR` 互补：前者检测分母被替换为恒等值，后者检测分子被 min() 抬高

**本轮实测**：IDENTITY_FORM 未触发新违规（DSHB 修复后分子=分母=109 且 `distinct_mapped_ids` 与交集一致）。

---

## 5. 交付DSHB参考

| 项 | 说明 |
|----|------|
| 违规来源 | `p1/scripts/export_mapping_list.py` 第99-100行（原） |
| 修复commit | `499ff25`（DSHB P09FIX） |
| 修复后行号 | 第141行 `p0_9_numerator = len(p0_9_intersection)` |
| 衍生品补齐 | 11项缺口已补齐（48/59 → 59/59） |
| 分母切换 | 109 已生效（59/59 达标） |
| 验收状态 | P0-9-AUDIT PASS，0 违规 |

---

*Report Generated: 2026-10-16 UTC+8 | Agent: HERMEShf | Branch: feature/v88-g1*
*Status: P0-9-AUDIT 3 VIOLATIONS RESOLVED (commit 499ff25)*
