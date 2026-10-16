# V88 Phase03 P1 — P0-12 三重修复复核审计明细报告

> **TASK_ID**: `V88_PHASE03_P1_HERMESHF_P012_TRIPLEFIX_RECHECK_AND_PHASE03_PRE_ARCHIVE_JOB`（T2+T3）
> **AGENT**: HERMEShf | **BRANCH**: `feature/v88-g1`（BRANCH_LOCKED: TRUE）
> **生成时间**: 2026-10-16 UTC+8
> **NO_OVERWRITE**: TRUE | **NO_ZHIJI_API_CALL**: TRUE

---

## 0. 结论

DSHE commit `d5c4713` 为远程分支合并（STATUS.md/JOB_READY.flag 冲突解决），**未修改 JSON 内容**。三重不匹配**全部维持**，P0-12 **仍 FAIL**。

---

## 1. DSHE 提交审计

### 1.1 提交信息

| 项 | 值 |
|----|-----|
| Commit | `d5c4713` |
| 标题 | `merge: V88_PHASE03_P1_DSHE_P012_CPU_JSON_RECTIFY merge remote` |
| 实际内容 | STATUS.md + JOB_READY.flag 冲突解决 |
| JSON 修改 | ❌ **未修改** |

### 1.2 与预期对比

| 预期修复 | 实际状态 | 判定 |
|----------|:--------:|:----:|
| 添加顶层 `cpu_peak_pct` 字段 | ❌ 仍不存在 | FAIL |
| 添加顶层 `after_peak_pct` 字段 | ❌ 仍不存在 | FAIL |
| 修正 CPU 口径 | ❌ 仍为 `time.process_time()` | FAIL |
| 路径纳入候选列表 | ❌ 门禁脚本未更新 | FAIL |

---

## 2. 三重不匹配复核

### 2.1 ① 路径不匹配（FAIL）

| 项 | 值 |
|----|-----|
| JSON 实际路径 | `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_compare.json` |
| 门禁候选路径 | 18 条，**不含 `p012_cpu_benchmark/`** |
| 门禁脚本检查 | `p012_cpu_benchmark` in source: **False** |
| 判定 | ❌ **FAIL** |

### 2.2 ② 字段不匹配（FAIL）

| 门禁期望字段 | DSHE 实际 | 存在？ |
|-------------|-----------|:------:|
| `cpu_peak_pct`（顶层） | `pre_optimization.cpu_pct_mean`（嵌套） | ❌ |
| `after_peak_pct`（顶层） | `post_optimization.cpu_pct_mean`（嵌套） | ❌ |
| `cpu_baseline_pct`（顶层） | `comparison.cpu_pct_reduction.pre_opt`（嵌套） | ❌ |

**DSHE 顶层 23 个 key**（无 `cpu_peak_pct` / `after_peak_pct`）：
```
task_id, task, schema_version, agent, branch, branch_locked,
generated, caliber_declaration, comparability_note,
artifact_declares_incomparable, environment, engine_info,
constraints, benchmark_config, full_link_pipeline_stages,
pre_optimization, post_optimization, comparison,
p012_gate_readiness, per_round_detail, status, status_reason, log_lines
```

### 2.3 ③ 口径不匹配（FAIL）

| 项 | DSHE 值 | 门禁期望 | 判定 |
|----|---------|---------|:----:|
| 测量方法 | `time.process_time()` | 系统 CPU 占用率 | ❌ |
| 公式 | `cpu_sec / wall_sec * 100` | 全链路业务稳态 CPU | ❌ |
| 优化后 CPU | 99.4871% | ≤1.75% | ❌ 超 56x |
| per_core | 6.2179% | ≤1.75% | ❌ 超 3.5x |
| 优化幅度 | 0.038% | — | ⚠️ 极小 |
| P99 改善 | -23.37% | — | ⚠️ 恶化 |

---

## 3. P0-12 判定

| 检查项 | 结果 |
|--------|:----:|
| ① 路径合规 | ❌ FAIL |
| ② 顶层字段 | ❌ FAIL |
| ③ CPU 口径 | ❌ FAIL |
| ④ per_core ≤1.75% | ❌ FAIL |
| **P0-12 综合** | **🔴 FAIL** |

---

## 4. DSHE 修复建议（优先级排序）

| # | 行动 | 说明 |
|---|------|------|
| 1 | **添加顶层字段** | `{"cpu_peak_pct": X.XX, "after_peak_pct": Y.YY}`，X.YY 为优化后全链路业务稳态 CPU 均值 |
| 2 | **修正 CPU 口径** | 从 `time.process_time()/wall_time*100`（CPU 时间比率 ≈100%）改为系统级全链路业务稳态 CPU（通常 <5%） |
| 3 | **路径纳入候选列表** | 在 `p0_gate_checker.py` 的 `_p012_candidate_paths()` 中添加 `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_compare.json` |
| 4 | **验证优化效果** | 当前优化幅度仅 0.038%，P99 恶化 23.37%，需排查优化策略有效性 |

---

*Report Generated: 2026-10-16 UTC+8 | Agent: HERMEShf | Branch: feature/v88-g1*
*Status: P0-12 FAIL (TRIPLE MISMATCH UNCHANGED, DSHE d5c4713=MERGE ONLY)*
