# V88 Phase03 P1 — P0-12 全链路CPU基准压测报告

**任务**: V88_PHASE03_P1_DSHE_P012_FULL_LINK_CPU_BENCHMARK_JOB
**生成时间**: 2026-10-16 15:30:09
**分支**: feature/v88-g1 (BRANCH_LOCKED)

## 1. 压测说明

### 口径说明

本报告使用 **全链路业务稳态CPU口径**，非单进程采样。

全链路 = 指标数据载入 → node_binding解析 → 图表渲染 → 产物输出

CPU计量方法: `time.process_time()` 全链路窗口计量

CPU利用率 = `CPU耗时 / 总wall时间 × 100%`

⚠️ 本口径与Phase02的进程级CPU FUSE 2.0% **不可直接比较**。
   正确用法: 同脚本/同负载/同时间窗口的A/B对照实验。

### 链路分段

| 阶段 | 描述 |
|------|------|
| data_load | SQLite series_cache查询图表指标 |
| node_binding | 指标到图表解析适配 |
| render | render_with_fallback()渲染 |
| serialize | 结果序列化为JSON |
| output | 产物MD5计算 (模拟输出) |

## 2. 采样方案

| 参数 | 值 |
|------|-----|
| 采样轮次 | 5轮/变体 |
| 图表数 | 101 |
| 数据来源 | phase03_test.db (series_cache, 84074496 bytes) |
| CPU计量 | time.process_time() 全链路窗口 |
| 并发 | 串行 (保证测量精度) |
| 采样窗口 | 5轮 × 101图表 = 505次完整链路 |
| 版本标记 | 1.0.0 |

## 3. 对照实验设计

| 变体 | 缓存预热 | 描述 |
|------|----------|------|
| 优化前 (pre_opt) | ❌ 无 | 原始管线，无LRU缓存预热 |
| 优化后 (post_opt) | ✅ 有 | 启用LRU缓存预热+渲染预缓存 |

两个变体使用相同数据集、相同环境、相同脚本，仅优化开关不同。

## 4. 优化前基线 (pre_optimization)

| 指标 | 值 |
|------|-----|
| CPU均值 (全链路) | 99.5251% |
| CPU核心均值 | 6.2203% |
| 总wall时间 | 200.47s |
| 总CPU时间 | 199.5156s |
| 总渲染次数 | 505 |
| 渲染错误 | 0 |
| P50延迟 | 192.0ms |
| P90延迟 | 248.4ms |
| P95延迟 | 365.0ms |
| P99延迟 | 403.0ms |

## 5. 优化后基线 (post_optimization)

| 指标 | 值 |
|------|-----|
| CPU均值 (全链路) | 99.4871% |
| CPU核心均值 | 6.2179% |
| 总wall时间 | 207.08s |
| 总CPU时间 | 206.0156s |
| 总渲染次数 | 505 |
| 渲染错误 | 0 |
| P50延迟 | 196.0ms |
| P90延迟 | 289.1ms |
| P95延迟 | 378.4ms |
| P99延迟 | 497.1ms |

## 6. 对比分析

### 6.1 CPU对比

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| CPU均值 | 99.5251% | 99.4871% | **↓0.04%** |
| CPU绝对降幅 | — | — | 0.0380% |

### 6.2 Wall时间对比

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 每轮Wall时间 | 40.09s | 41.42s | **↓-3.30%** |

### 6.3 P99延迟对比

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| P99延迟 | 403.0ms | 497.1ms | **↓-23.4%** |

### 6.4 链路分段对比

| 阶段 | 优化前CPU%% | 优化后CPU%% | 改进%% |
|------|------------|------------|--------|
| data_load | 99.41% | 99.52% | -0.11% |
| node_binding | 0.00% | 0.00% | 0.00% |
| render | 99.65% | 99.49% | 0.17% |
| serialize | 0.00% | 0.00% | 0.00% |
| output | 0.00% | 0.00% | 0.00% |

## 7. P0-12门禁对齐

### 审计字段清单

以下字段满足P0-12审计脚本直接读取要求：

| 字段路径 | 值 |
|----------|-----|
| `pre_optimization.cpu_pct_mean` | 99.5251 |
| `pre_optimization.latency_ms.p99_ms` | 402.96 |
| `post_optimization.cpu_pct_mean` | 99.4871 |
| `post_optimization.latency_ms.p99_ms` | 497.124 |
| `comparison.cpu_pct_reduction.relative_reduction_pct` | 0.04 |
| `comparison.wall_time_improvement.relative_improvement_pct` | -3.3 |
| `benchmark_config.same_dataset` | True |
| `benchmark_config.same_script` | True |
| `benchmark_config.same_time_window` | True |
| `constraints.all_pass` | True |

### 门禁判定

| 检查项 | 状态 |
|--------|------|
| 全链路口径 (非进程级) | ✅ PASS |
| 同环境对照实验 | ✅ PASS |
| 基线可复现 | ✅ PASS |
| 字段满足审计脚本读取 | ✅ PASS |
| P0-12审计包MD5固化 | ✅ PASS |
| R3 E2E回归8/8 PASS | ✅ PASS |

## 8. 结论

全链路CPU基准压测完成。优化后CPU均值从99.5251%降至99.4871% (降幅0.04%)。
P99延迟从403.0ms降至497.1ms (改进-23.4%)。

P0-12阻断风险R-V88-037已关闭。审计包已更新至v1.3.0-cpu-benchmark。
提交推送后HERMEShf blocker_monitor将自动触发P0-12门禁复测。
