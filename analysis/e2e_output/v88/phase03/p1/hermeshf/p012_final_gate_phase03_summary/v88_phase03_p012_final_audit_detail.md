# V88 Phase03 P1 — P0-12 最终 CPU 审计明细报告

> **TASK_ID**: `V88_PHASE03_P1_HERMESHF_P012_FINAL_GATE_AND_PHASE03_SUMMARY_JOB`（T2）
> **AGENT**: HERMEShf | **BRANCH**: `feature/v88-g1`（BRANCH_LOCKED: TRUE）
> **生成时间**: 2026-10-16 UTC+8
> **NO_OVERWRITE**: TRUE | **NO_ZHIJI_API_CALL**: TRUE

---

## 0. 结论

P0-12 **维持 FAIL**。DSHE 当前交付物为进程级 CPU 基线（`psutil_available=False`，CPU 指标为 `null`）+ 审计就绪声明（`cpu_baseline_audit_results.json`），**不含门禁要求的全链路业务稳态 CPU 优化前后对比 JSON**（`cpu_peak_pct` 字段）。DSHE 需交付含 `cpu_peak_pct` / `after_peak_pct` 的 JSON 文件方可 PASS。

---

## 1. DSHE 交付物清单

| 交付物 | 路径 | 口径 | 是否满足门禁 |
|--------|------|------|:-----------:|
| 长稳测试结果 | `p1/dshe/longrun_perf_results.json` | 进程级（P99=388.642ms） | ❌ |
| CPU 基线审计 | `p1/dshe/post_perf_validate/cpu_baseline_audit_results.json` | 审计非对比 | ❌ |
| CPU 基线对比报告 | `p1/dshe/v88_phase03_p1_cpu_baseline_contrast_report.md` | 进程级，声明不可比 | ❌ |
| **全链路 CPU 对比 JSON** | **`cpu_peak_pct.json` 等** | **全链路业务稳态** | **❌ 不存在** |

---

## 2. P0-12 门禁判定逻辑

### 2.1 门禁阈值

```
全链路业务稳态 CPU 优化后峰值 ≤ 1.75%
```

### 2.2 审计逻辑（`p0_gate_checker.py::check_p012()`）

门禁从**18 条候选路径**中按优先级搜索 CPU 交付物，提取 `cpu_peak_pct` 字段：
1. **JSON 优先**：解析 JSON 中的 `cpu_peak_pct` / `after_peak_pct` 字段
2. **MD 回退**：若 JSON 不存在，从 MD 报告中用 `_extract_full_chain_cpu_peak()` 三段过滤提取

### 2.3 三段过滤规则

| 阶段 | 规则 | 目的 |
|------|------|------|
| ① 排除 | `进程级` / `每核` / `瞬时` / `psutil` / `per_core` | 数量级不可比 |
| ② 必须 | `全链路` / `full_chain` / `full-chain` / `稳态` / `steady` | 确认全链路口径 |
| ③ 排除阈值 | `FUSE` / `阈值` / `threshold` / `Phase02` / `基准` | 排除参照值 |
| ④ 必须优化 | `优化后` / `after` / `优化` | 确认是优化结果 |

---

## 3. DSHE 交付物逐项审计

### 3.1 longrun_perf_results.json

| 字段 | 值 | 门禁判定 |
|------|-----|:--------:|
| `metrics.cpu.peak_pct` | **null** | ❌ 无数据 |
| `metrics.cpu.mean_pct` | **null** | ❌ 无数据 |
| `metrics.cpu.fuse_threshold_pct` | 2.0 | — |
| `metrics.cpu.caliber` | `"process-level instantaneous"` | ❌ 进程级 |
| `psutil_available` | **False** | ❌ 无法采集 |
| `phase02_comparison.phase02_p99_ms` | 39.193 | — |
| `phase02_comparison.p99_delta_pct` | 891.61% | ⚠️ 口径不可比 |

**判定**：CPU 指标全部为 `null`（`psutil_available=False`），无法提取任何 CPU 峰值。

### 3.2 cpu_baseline_audit_results.json

| 字段 | 值 | 门禁判定 |
|------|-----|:--------:|
| `baseline_data.engine_md5` | `cd73deaeec54a7f1f8bde92c1300a9dc` | — |
| `comparability_analysis.comparability` | **False** | ❌ 口径不可比 |
| `comparability_analysis.reason` | 进程级 vs 全链路差异 ~45-52x | ❌ |
| `p0_12_gate_readiness.status` | **True** | ⚠️ 审计就绪非对比就绪 |
| `verdict` | **WARN** | ⚠️ 缺 `artifact_declares_incomparable` |

**判定**：这是审计就绪声明，不是全链路对比数据。

### 3.3 v88_phase03_p1_cpu_baseline_contrast_report.md

| 检查项 | 结果 | 说明 |
|--------|:----:|------|
| 含"全链路"关键词 | ✅ | 但仅用于说明 Phase02 FUSE 2.0% 是全链路 |
| 含"优化后"关键词 | ❌ | 报告描述基线，非优化结果 |
| 进程级声明 | ✅ | 明确声明进程级不可比 |
| 全链路优化后实测值 | ❌ | **不存在** |

**判定**：MD 报告中"全链路"仅用于说明 Phase02 基线，不含本次优化后的全链路实测值。三段过滤不会匹配。

---

## 4. P0-12 当前状态

| 维度 | 值 |
|------|-----|
| 门禁状态 | **FAIL** |
| 门禁实际输出 | `已交付但口径不符（无全链路优化后数值）` |
| 全链路 CPU 峰值 | 未提取（无数据源） |
| 阈值 | ≤ 1.75% |
| DSHE 交付口径 | 进程级（`psutil_available=False`） |
| 缺少的交付物 | `cpu_peak_pct.json` 或含 `after_peak_pct` 的 JSON |

---

## 5. DSHE 优化方向

| 优先级 | 行动 | 说明 |
|:------:|------|------|
| P0 | 提供全链路业务稳态 CPU 优化前后对比 JSON | 格式：`{"cpu_peak_pct": X.XX, "after_peak_pct": Y.YY}` |
| P0 | 口径必须为全链路业务稳态 | 包含数据供给 + 推送 + 渲染的全链路 CPU |
| P1 | 安装 psutil 采集进程级 CPU | 当前 `psutil_available=False`，无法采集 |
| P2 | 声明 `artifact_declares_incomparable=true` | 消除审计 WARN |

---

*Report Generated: 2026-10-16 UTC+8 | Agent: HERMEShf | Branch: feature/v88-g1*
*Status: P0-12 FAIL (MAINTAINED, WAITING FOR DSHE FULL-CHAIN CPU JSON)*
