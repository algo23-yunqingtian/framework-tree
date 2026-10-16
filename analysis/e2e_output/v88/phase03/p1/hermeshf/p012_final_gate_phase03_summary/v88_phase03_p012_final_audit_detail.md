# V88 Phase03 P1 — P0-12 最终 CPU 审计明细报告（更新版）

> **TASK_ID**: `V88_PHASE03_P1_HERMESHF_P012_FINAL_GATE_AND_PHASE03_SUMMARY_JOB`（T2 更新）
> **AGENT**: HERMEShf | **BRANCH**: `feature/v88-g1`（BRANCH_LOCKED: TRUE）
> **更新**: 2026-10-16 UTC+8 — DSHB commit `604d0d2` 落地后全链路 CPU 基准审计
> **NO_OVERWRITE**: TRUE | **NO_ZHIJI_API_CALL**: TRUE

---

## 0. 结论

DSHE 已提交全链路 CPU 基准（commit `604d0d2`），但 **P0-12 维持 FAIL**。根因：

1. **路径不在候选列表中**：JSON 在 `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_compare.json`，门禁候选路径列表未包含此路径
2. **字段名不匹配**：DSHE 用嵌套字段 `pre_optimization.cpu_pct_mean`，门禁期望顶层 `cpu_peak_pct` / `after_peak_pct`
3. **口径与阈值不符**：DSHE 的 `cpu_pct_mean=99.4871%` 是 `cpu_sec/wall_sec*100`（CPU 时间比率），非 Phase02 FUSE 口径的"全链路业务稳态 CPU 均值"。per_core 为 6.2179%，远超 1.75% 阈值

---

## 1. DSHE 全链路 CPU 基准交付物

| 交付物 | 路径 | 状态 |
|--------|------|:----:|
| 全链路 CPU 对比 JSON | `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_compare.json` | ✅ 已提交 |
| 冻结包 v1.3.0 | `p1/dshe/render_archive_phase04_prep/frozen_p012_gate_package/` | ✅ 已提交 |
| 增强审计 JSON | `p1/dshe/render_archive_phase04_prep/frozen_p012_gate_package/p012_enhanced_cpu_baseline_audit.json` | ✅ 10/10 PASS |
| 压测脚本 | `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_benchmark.py` | ✅ |
| R3 E2E 回归 | `p1/dshe/p012_cpu_benchmark/v88_phase03_r3_e2e_regression_after_cpu_opt.json` | ✅ 8/8 PASS |

---

## 2. 审计发现

### 2.1 路径不匹配（根因 #1）

| 项 | 值 |
|----|-----|
| DSHE 实际路径 | `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_compare.json` |
| 门禁候选路径 | `p1/dshe/cpu_peak_pct.json` 等 18 条，**不含 `p012_cpu_benchmark/` 子目录** |
| 修复建议 | 在 `p0_gate_checker.py` 候选路径中添加 `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_compare.json` |

### 2.2 字段名不匹配（根因 #2）

| 门禁期望 | DSHE 实际 |
|----------|-----------|
| `cpu_peak_pct`（顶层） | `pre_optimization.cpu_pct_mean`（嵌套） |
| `after_peak_pct`（顶层） | `post_optimization.cpu_pct_mean`（嵌套） |
| `cpu_baseline_pct`（顶层） | `comparison.cpu_pct_reduction.pre_opt`（嵌套） |

**DSHE 的 `p012_gate_readiness.fields_for_audit_script`** 已声明兼容：
```json
{
  "audit_script_compatible": true,
  "hermes_audit_prepared": true,
  "fields_for_audit_script": [
    "pre_optimization.cpu_pct_mean",
    "post_optimization.cpu_pct_mean",
    "comparison.cpu_pct_reduction.relative_reduction_pct",
    ...
  ]
}
```

但门禁脚本 `check_p012()` 不读取此声明，只搜索 `cpu_peak_pct` / `after_peak_pct`。

### 2.3 CPU 口径与阈值（根因 #3）

| 维度 | DSHE 值 | 门禁期望 | 差异 |
|------|---------|---------|------|
| 测量方法 | `time.process_time()` CPU 时间窗口 | `psutil.cpu_percent()` 或全链路业务稳态 | ❌ 方法不同 |
| 公式 | `cpu_sec / wall_sec * 100` | 系统 CPU 占用率 | ❌ 公式不同 |
| 优化后 CPU | 99.4871% | ≤1.75% | ❌ 超阈值 56x |
| 每核 CPU | 6.2179% | ≤1.75% | ❌ 超阈值 3.5x |
| 优化幅度 | 0.038%（absolute） | — | ⚠️ 极小 |
| P99 延迟改善 | -23.37%（恶化） | — | ⚠️ 负优化 |

**口径声明**：
> "FULL-LINK BUSINESS STEADY-STATE CPU. Uses `time.process_time()` for CPU wall-clock accounting. NOT process-level instantaneous CPU (psutil.cpu_percent). NOT directly comparable with Phase02's process-level CPU FUSE 2.0%."

**问题**：`time.process_time() / wall_time * 100` 计算的是"进程 CPU 时间占墙钟时间的比率"，本质是**单进程 CPU 占用率**（接近 100% 表示 CPU 密集型），不是 Phase02 FUSE 的"全链路业务稳态 CPU 均值"（系统级 CPU 占用率，通常 <5%）。

---

## 3. 对比数据

### 3.1 优化前后对比

| 指标 | 优化前 | 优化后 | 变化 |
|------|:------:|:------:|:----:|
| CPU 均值 | 99.5251% | 99.4871% | -0.038% |
| P99 延迟 | 402.96ms | 497.12ms | +23.37%（恶化） |
| 墙钟时间 | 40.09s/轮 | 41.42s/轮 | +3.30%（恶化） |
| 渲染次数 | 505 | 505 | 不变 |
| 错误数 | 0 | 0 | 不变 |

### 3.2 分阶段对比

| 阶段 | 优化前 CPU% | 优化后 CPU% | 变化 |
|------|:-----------:|:-----------:|:----:|
| data_load | 99.414% | 99.522% | +0.11% |
| node_binding | 0.0% | 0.0% | 0 |
| render | 99.6547% | 99.4876% | -0.17% |
| serialize | 0.0% | 0.0% | 0 |
| output | 0.0% | 0.0% | 0 |

---

## 4. 门禁 FAIL 判定

| 检查项 | 结果 | 说明 |
|--------|:----:|------|
| 路径匹配 | ❌ FAIL | `p012_cpu_benchmark/` 不在候选列表 |
| 字段匹配 | ❌ FAIL | `cpu_peak_pct` 不存在 |
| CPU 口径 | ⚠️ WARN | 声明全链路但实为进程 CPU 比率 |
| CPU 阈值 | ❌ FAIL | 99.4871% >> 1.75% |
| 优化效果 | ⚠️ WARN | 优化幅度仅 0.038%，P99 恶化 23.37% |

**P0-12 判定：FAIL**（3 项 FAIL + 2 项 WARN）

---

## 5. DSHE 修复建议

| 优先级 | 行动 | 说明 |
|:------:|------|------|
| P0 | 添加顶层 `cpu_peak_pct` 字段 | 格式：`{"cpu_peak_pct": X.XX}`，X.XX 为全链路业务稳态 CPU 均值 |
| P0 | 添加顶层 `after_peak_pct` 字段 | 优化后全链路 CPU 均值 |
| P1 | 修正 CPU 口径 | 从 `time.process_time()/wall_time` 改为全链路业务稳态 CPU（含数据供给+推送+渲染的系统级 CPU） |
| P1 | 路径纳入候选列表 | 在 `p0_gate_checker.py` 中添加 `p1/dshe/p012_cpu_benchmark/` 子目录 |
| P2 | 验证优化效果 | 当前优化幅度仅 0.038%，P99 反而恶化 23.37%，需排查 |

---

## 6. 替代方案：门禁脚本适配

若 DSHE 确认 `time.process_time()` 口径为"全链路业务 CPU"（与 Phase02 不可比但内部自洽），则需：
1. 修改 `p0_gate_checker.py::check_p012()` 支持嵌套字段提取
2. 添加 `p012_cpu_benchmark/` 候选路径
3. 调整阈值（当前 1.75% 不适用于 CPU 时间比率口径）

---

*Report Generated: 2026-10-16 UTC+8 | Agent: HERMEShf | Branch: feature/v88-g1*
*Status: P0-12 FAIL (3 FAIL + 2 WARN, PATH+FIELD+CALIBER MISMATCH)*
*下一步: DSHE 修复 JSON 字段/口径/路径，或 HERMEShf 适配门禁脚本*
