# Official P0-12 Event Archive — 双基线归档与时间线

> **TASK_ID**: V88_PHASE03_P1_HERMES_EXEMPTION_FOLLOWUP_AND_PHASE03_SUMMARY_AUDIT_JOB / T0
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **归档时间**: 2026-10-16 UTC+8
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL

---

## 1. P0-12 完整事件时间线

| # | 时间 | Commit | 事件 | cpu_peak_pct | 口径 | 门禁判定 | 责任方 |
|:-:|------|--------|------|:------------:|------|:--------:|:------:|
| 1 | 10-16 | 604d0d2 | P0-12 首次提交 — 三重不匹配 | — | process_time | 🔴 FAIL (路径+字段+口径全不对) | DSHE |
| 2 | 10-16 | d5c4713 | P0-12 第二次 — merge-only | — | process_time | 🔴 FAIL (仍不匹配) | DSHE |
| 3 | 10-16 | c271f59 | P0-12 FINAL_TRIPLEFIX — 路径+字段+口径三重修复 | 99.4871% | process_time (口径名改为 full_chain_business_steady_state) | 🔴 FAIL (数值超标) | DSHE |
| 4 | 10-16 | **55458b6** | **P0-12 GATE_TRIPLE_FIX — psutil 系统级口径** | **0.0654%** | **psutil.cpu_times() 系统级** | **✅ PASS** | DSHE |
| 5 | 10-16 | b1987a4 | P0-12 CPU_EXCEPTION_HANDLER — 回退 process_time 口径 + 豁免申请 | 99.4871% | process_time | 🔴 FAIL → 豁免申请 | DSHE |
| 6 | 10-16 | 8523a19 | P0-12 EXEMPTION_PREP — 冻结+跨Agent对齐+基线导出 | 99.4871% | process_time | EXEMPTION_REQUESTED | DSHE |
| 7 | 10-16 | **6ac0739** | **HERMEShf 审批 APPROVED** — FAIL→WARN | 99.4871% | process_time | **⚠️ WARN (EXEMPTION_GRANTED)** | HERMEShf |

---

## 2. 双基线身份定义

### 2.1 Active 基线（豁免版 v1.4.0-exemption）

| 字段 | 值 |
|------|---|
| **身份** | **ACTIVE — Phase03 官方门禁基线** |
| Commit | b1987a4 (JSON) → 8523a19 (冻结) → 6ac0739 (HERMEShf 审批) |
| 文件路径 | `p1/dshe/p012_final_triplefix/frozen_p012_gate_package/v88_p012_full_link_cpu_compare.json` |
| MD5 | **C10D5A32ECCB8A0D5866B872538F7C5A** |
| 口径 | `time.process_time()/wall_time*100` (进程级 CPU 比率) |
| cpu_peak_pct | **99.4871%** |
| per_core | 6.2179% |
| schema_version | v88-p012-full-link-cpu.2.0 |
| caliber | full_chain_business_steady_state |
| 门禁判定 | ⚠️ **WARN (EXEMPTION_GRANTED)** |
| 审批方 | HERMEShf (commit 6ac0739) |
| 约束 | C-1~C-5 生效 |
| 状态 | 🔒 **FROZEN — 当前活跃门禁基线** |

### 2.2 Alternative 基线（psutil 原生 PASS 版）

| 字段 | 值 |
|------|---|
| **身份** | **ALTERNATIVE-01 — 归档备选基线（禁止静默切换）** |
| Commit | 55458b6 |
| 文件路径 | `p1/dshe/p012_triple_fix/v88_p012_full_link_cpu_compare.json` |
| MD5 | **FC4ED25A3AA35F0B0D33922B41E64F32** |
| 口径 | `psutil.cpu_times()` (系统级全链路稳态 CPU) |
| cpu_peak_pct | **0.0654%** |
| per_core | 0.0654% (16 核分摊后仍为 0.0654%) |
| schema_version | v88-p012-full-link-cpu.2.0-steady-state |
| caliber | full_chain_business_steady_state |
| caliber_comparable_with_phase02 | ✅ true |
| artifact_declares_incomparable | false |
| 门禁判定 | ✅ **PASS (原生通过，无需豁免)** |
| 状态 | 📦 **ARCHIVED — 仅 Phase04 重新评估后可启用** |

### 2.3 双基线切换规则

> **🚨 禁止静默切换门禁基线。**

| 规则 | 说明 |
|------|------|
| 1 | Phase03 当前活跃门禁基线 = **豁免版 v1.4.0-exemption** (b1987a4→6ac0739) |
| 2 | ALTERNATIVE-01 (55458b6) 仅作为归档记录，**不得**替代活跃基线 |
| 3 | 任何人不得在未经 HERMEShf 新工单审批的情况下切换门禁基线 |
| 4 | ALTERNATIVE-01 的重新启用条件：Phase04 新工单 + HERMEShf 审批 + psutil 采集环境校验 + DSHB P0-13 基线兼容性验证 |
| 5 | 切换时须更新本归档文件的 `ACTIVE` 标记 |

---

## 3. 版本故事

### 3.1 为什么存在双基线

1. **55458b6 (Alternative)**：DSHE 在三重修复中尝试了 `psutil.cpu_times()` 系统级口径，结果 **0.0654%**，原生通过 P0-12 门禁 (≤1.75%)。此基线与 Phase02 FUSE 1.94% 可比 (`caliber_comparable_with_phase02=true`)。

2. **b1987a4 (Active)**：DSHE 后续选择了 `time.process_time()` 进程级口径，结果 **99.4871%**，超标 57 倍。提交了豁免申请，论证高 CPU 为渲染引擎物理固有约束。HERMEShf 审批通过豁免。

3. **为什么选择了豁免版而非 PASS 版**：
   - 55458b6 的 psutil 系统级口径在 Windows 环境 (DESKTOP-OM3O97G, AMD64) 采集
   - b1987a4 的 process_time 口径在 Linux 环境 (6.8.0-117-generic) 采集
   - 两个基线产自**不同运行环境**，口径差异巨大
   - DSHE 在后续 b1987a4 中回退到 process_time 口径，可能因 psutil 环境依赖不稳定或测量方法论争议
   - HERMEShf 审批豁免时已知 55458b6 PASS 基线存在，但基于豁免材料论证的充分性批准了 WARN

4. **事实归档**：两个基线都合法存在，各有利弊。Phase03 活跃基线选择豁免版，备选基线归档保留。

### 3.2 已知风险

| 风险 | 说明 | 缓解 |
|------|------|------|
| 基线混淆 | 后续 agent 可能误用 ALTERNATIVE-01 替代 active 基线 | 本归档文件明确身份标记 |
| 口径争议 | process_time vs psutil 口径选择缺乏正式裁决 | C-3 约束要求 Phase04 部署 psutil 采集 |
| 环境差异 | 两基线产自不同 OS | Phase04 须在同一环境重新采集 |

---

## 4. Commit 索引

| Commit | SHA | 类型 | 关键产出 |
|--------|-----|------|----------|
| 604d0d2 | 604d0d2 | DSHE 首次 | 三重不匹配 FAIL |
| d5c4713 | d5c4713 | DSHE 第二次 | merge-only FAIL |
| c271f59 | c271f59 | DSHE FINAL_TRIPLEFIX | 三重修复完成，数值超标 FAIL |
| **55458b6** | 55458b6 | DSHE GATE_TRIPLE_FIX | psutil 系统级口径 PASS (0.0654%) |
| b1987a4 | b1987a4 | DSHE CPU_EXCEPTION_HANDLER | process_time 口径 + 豁免申请 |
| 8523a19 | 8523a19 | DSHE EXEMPTION_PREP | 冻结 + 跨Agent对齐 + 基线导出 |
| **6ac0739** | 6ac0739 | HERMEShf 审批 | APPROVED, FAIL→WARN |

---

## 5. 双基线 MD5 指纹

| 基线 | 文件 | MD5 (完整) |
|------|------|-----------|
| Active (豁免版) | `p012_final_triplefix/frozen_p012_gate_package/v88_p012_full_link_cpu_compare.json` | C10D5A32ECCB8A0D5866B872538F7C5A |
| Alternative-01 | `p012_triple_fix/v88_p012_full_link_cpu_compare.json` | FC4ED25A3AA35F0B0D33922B41E64F32 |

---

*Generated: 2026-10-16 UTC+8 | HERMEShf | Official P0-12 Event Archive — 双基线归档完成*
