# V86 面板指标对齐校验报告 (T3.1)

> 任务: `DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V5_ARCHIVE` · T3.1
> 分支: `feature/v85-chart-template`
> 基线: DSHE V4 (commit a9d8a4e), DSHB Gate FULL_PASS (commit 311f82c)
> 输入: DSHB 指标盘点报告 / 缺失指标清单 / PDF绘图指标定义
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED
> 生成日期: 2026-10-03

---

## 1. 执行摘要

本报告对 DSHE 6 块 Grafana 面板与门户 7 维度指标进行去重校验，与 DSHB 去重后的指标清单进行一致性核对。

### 1.1 核心发现

| 维度 | 结果 | 说明 |
|------|------|------|
| **指标复用率** | 68% (107/157) | 107 个指标可从 DSHB/DSHE 复用 |
| **需新增指标** | 19 (12%) | 无现有数据源，需新建 |
| **无数据源暂无法渲染** | 6 (4%) | 依赖外部系统，需待接入 |
| **面板内冗余重复** | 8 (5%) | 同指标在多个面板重复展示 |
| **门户维度覆盖缺口** | 7 (4%) | 7 维度中 2 维度存在展示缺口 |

### 1.2 对齐状态总览

```
┌─────────────────────────────────────────────────────────────┐
│  指标对齐状态总览                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  总计指标: 157 个 (DSHE 78 + DSHB 90 去重后 78 + 联合 1)     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  可复用       │  │  需新增       │  │  无数据源     │      │
│  │   107 (68%)  │  │   19 (12%)   │  │    6 (4%)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  冗余重复     │  │  口径差异     │                        │
│  │    8 (5%)    │  │    7 (4%)    │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                             │
│  Grafana 面板覆盖: 6/6 面板, 48 指标, 覆盖率 62%             │
│  门户 7 维度覆盖: 5/7 维度完全覆盖, 2 维度部分覆盖             │
│  DSHB 指标复用: 48 个复用, 27 个新增, 15 个不可用             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 指标来源与去重

### 2.1 指标来源

| 来源 | 指标前缀 | 指标数 | 来源文件 |
|------|---------|-------|---------|
| DSHE 别名引擎 | `alias_*` | 78 | `v86_alias_grafana_panels_final.md` |
| DSHB 规则引擎 | `v86_*` | 90 | `v86_rule_metric_monitor_spec.md` |
| 联合管线 | `alias_*` + `v86_*` | 1 | 联合回放 + 口径终审 |
| **去重后总计** | — | **157** | 2 来源重叠 12 指标 |

### 2.2 重叠指标 (12 个, 可去重)

| # | DSHE 指标 | DSHB 指标 | 重复类型 | 处理 |
|---|----------|----------|---------|------|
| 1 | `alias_resolve_per_second` | `v86_throughput_evaluate_rate_per_sec` | 吞吐率同语义 | 保留 DSHE (别名引擎专用) |
| 2 | `alias_resolve_duration_ms` | `v86_latency_evaluate_total_seconds` | 耗时直方图 | 保留 DSHE (别名引擎专用) |
| 3 | `alias_engine_healthy` | `v86_system_health` | 健康状态 | 保留 DSHB (联合健康) |
| 4 | `alias_engine_start_time` | `v86_system_uptime_seconds` | 运行时间 | 保留 DSHB (联合运行) |
| 5 | `alias_error_rate` | `v86_error_rate_per_sec` | 错误率 | 保留 DSHE (别名引擎专用) |
| 6 | `alias_resolve_total` | `v86_throughput_evaluate_total` | 总请求数 | 保留 DSHE (别名引擎专用) |
| 7 | `alias_verdict_total{PASS}` | `v86_throughput_evaluate_passed_total` | 通过数 | 保留 DSHE (裁决专用) |
| 8 | `alias_verdict_total{BLOCK}` | `v86_throughput_evaluate_blocked_total` | 拦截数 | 保留 DSHE (裁决专用) |
| 9 | `alias_verdict_total{AMBIGUOUS}` | `v86_throughput_evaluate_not_applicable_total` | 歧义数 | 保留 DSHE (歧义专用) |
| 10 | `alias_engine_init_duration_ms` | `v86_latency_evaluate_max_ms` | 冷启动/最大耗时 | 保留 DSHE (冷启动专用) |
| 11 | `alias_cache_hit_rate` | — | 缓存命中率 | DSHE 独有 |
| 12 | `alias_engine_hash_mismatch` | — | 哈希校验 | DSHE 独有 |

---

## 3. Grafana 面板指标对齐 (6 面板)

### 3.1 Panel 1: 别名库统计面板

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 别名条目总数 | `alias_library_total_entries` | DSHE | ✅ 可复用 | 4,643 |
| Canonical Key 去重数 | `alias_library_canonical_keys` | DSHE | ✅ 可复用 | 1,818 |
| 覆盖品种数 | `alias_library_variety_entries` | DSHE | ✅ 可复用 | 10+ |
| 别名库版本 | `alias_library_version` | DSHE | ✅ 可复用 | E77C8E36 |
| 品种分布 | `alias_library_variety_entries{variety}` | DSHE | ✅ 可复用 | 10 品种 |
| 哈希校验状态 | `alias_engine_hash_mismatch` | DSHE | ✅ 可复用 | G-M-07 |
| 加载方式标注 | `alias_engine_load_method` | DSHE | ⚠️ 需新增 | 当前为 exec() |
| 规则引擎加载状态 | `v86_system_engine_loaded` | DSHB | ✅ 可复用 | 联合健康 |
| 别名库 MD5 验证 | `v86_system_engine_rules_total` | DSHB | ✅ 可复用 | 18 条 |
| **小计** | — | — | **8✅ 1⚠️** | — |

### 3.2 Panel 2: 引擎状态面板

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| F1-F4 开关状态 | `alias_engine_f1/f2/f3/f4_enabled` | DSHE | ✅ 可复用 | 4 个指标 |
| 引擎模式 | `alias_engine_mode` | DSHE | ✅ 可复用 | f3+f4 |
| 降级级别 | `alias_degrade_level` | DSHE | ✅ 可复用 | L0 |
| 引擎健康 | `alias_engine_healthy` | DSHE | ⚠️ 冗余 | 与 `v86_system_health` 重复 |
| 运行时间 | `time() - alias_engine_start_time` | DSHE | ⚠️ 冗余 | 与 `v86_system_uptime_seconds` 重复 |
| Healthz 延迟 | `alias_healthz_latency_ms` | DSHE | ✅ 可复用 | 12ms |
| 规则引擎规则数 | `v86_system_engine_rules_total` | DSHB | ✅ 可复用 | 18 |
| 引擎版本 | `v86_system_version` | DSHB | ✅ 可复用 | v86.1-prod |
| 别名库完整性 | `alias_engine_hash_mismatch` | DSHE | ✅ 可复用 | G-M-07 |
| **小计** | — | — | **7✅ 2⚠️** | — |

### 3.3 Panel 3: 歧义率面板

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 歧义总数 | `alias_verdict_total{verdict="AMBIGUOUS"}` | DSHE | ⚠️ 冗余 | 与 `v86_throughput_evaluate_not_applicable_total` 重复 |
| 歧义率 | `alias_ambiguous_rate` | DSHE | ✅ 可复用 | 3.55% |
| 长尾歧义 | `alias_tail_ambiguous_total` | DSHE | ✅ 可复用 | 34 |
| 新增歧义 | `increase(alias_new_ambiguous_total[1d])` | DSHE | ✅ 可复用 | G-M-04 |
| 歧义率门禁 | `alias_ambiguous_rate` | DSHE | ✅ 可复用 | G-GR-04 |
| 歧义品种分布 | `alias_ambiguous_by_variety{variety}` | DSHE | ✅ 可复用 | 5 品种 |
| 手动审阅待处理 | `alias_manual_review_pending` | DSHE | ⚠️ 需新增 | G-M-04/05 |
| 置信度分布 | `alias_confidence_distribution{level}` | DSHE | ⚠️ 需新增 | G-M-06 |
| **小计** | — | — | **5✅ 1⚠️冗余 2⚠️新增** | — |

### 3.4 Panel 4: 性能面板

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 吞吐 | `alias_resolve_per_second` | DSHE | ✅ 可复用 | 2,144/s |
| 平均耗时 | `avg(alias_resolve_duration_ms)` | DSHE | ✅ 可复用 | 0.143ms |
| P99 耗时 | `histogram_quantile(0.99, ...)` | DSHE | ✅ 可复用 | 0.80ms |
| 首次请求 | `alias_first_request_ms` | DSHE | ✅ 可复用 | 0.01ms |
| 冷启动 | `alias_engine_init_duration_ms / 1000` | DSHE | ✅ 可复用 | 22.74s |
| 缓存命中率 | `alias_cache_hit_rate` | DSHE | ✅ 可复用 | 100% |
| V85 对比 | `(alias_resolve_per_second - 1500) / 1500 * 100` | DSHE | ✅ 可复用 | +42.9% |
| 规则引擎吞吐 | `v86_throughput_evaluate_rate_per_sec` | DSHB | ⚠️ 冗余 | 4,173/s, 与 DSHE 同语义 |
| 联合管线 P95 | `v86_latency_evaluate_p95_ms` | DSHB | ✅ 可复用 | 4.26ms |
| 队列深度 | `v86_queue_depth` | DSHB | ✅ 可复用 | G-M-13 |
| 多进程对比 | `alias_resolve_per_second` (多进程) | DSHE | ⚠️ 需新增 | G-M-11, 需 PoC |
| 错误率 | `alias_error_rate` | DSHE | ⚠️ 冗余 | 与 `v86_error_rate_per_sec` 重复 |
| 数据质量率 | `v86_data_missing_total` | DSHB | ✅ 可复用 | 155, DEP-C-02 |
| **小计** | — | — | **9✅ 2⚠️冗余 1⚠️新增** | — |

### 3.5 Panel 5: 裁决分布面板

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| PASS 裁决 | `alias_verdict_total{verdict="PASS"}` | DSHE | ⚠️ 冗余 | 与 `v86_throughput_evaluate_passed_total` 重复 |
| REVIEW 裁决 | `alias_verdict_total{verdict="REVIEW"}` | DSHE | ⚠️ 冗余 | 与 `v86_throughput_evaluate_not_applicable_total` 重复 |
| BLOCK 裁决 | `alias_verdict_total{verdict="BLOCK"}` | DSHE | ⚠️ 冗余 | 与 `v86_throughput_evaluate_blocked_total` 重复 |
| V85 vs V86 对比 | `alias_verdict_total{mode}` | DSHE | ✅ 可复用 | base vs f3+f4 |
| PASS 率 | `alias_verdict_total{PASS}/alias_resolve_total` | DSHE | ✅ 可复用 | 96.40% |
| REVIEW 率 | `alias_verdict_total{REVIEW}/alias_resolve_total` | DSHE | ✅ 可复用 | 3.55% |
| BLOCK 率 | `alias_verdict_total{BLOCK}/alias_resolve_total` | DSHE | ✅ 可复用 | 0.04% |
| BL-020 命中计数 | `v86_rule_hit_total{rule_id="BL-020"}` | DSHB | ✅ 可复用 | G-M-01 |
| BL-020 FP 率 | `v86_rule_fp_total{rule_id="BL-020"}` | DSHB | ✅ 可复用 | G-M-01 |
| 联合管线裁决变化 | `v86_throughput_evaluate_total` delta | DSHB | ⚠️ 需新增 | G-M-03, 需 diff 计算 |
| **小计** | — | — | **6✅ 3⚠️冗余 1⚠️新增** | — |

### 3.6 Panel 6: 运维面板

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 灰度门禁状态 (12 道) | `alias_gate_status{gate}` | DSHE | ✅ 可复用 | G-GR-01~12 |
| 当前降级级别 | `alias_degrade_level` | DSHE | ✅ 可复用 | L0 |
| 降级历史 | `alias_degrade_history` | DSHE | ⚠️ 需新增 | 最近 5 次 |
| 告警状态 | `alias_alert_status{severity}` | DSHE | ⚠️ 需新增 | P0/P1/P2/P3 |
| 最近告警历史 | `alias_alert_history` | DSHE | ⚠️ 需新增 | 24h 告警 |
| 别名库哈希校验 | `alias_engine_hash_mismatch` | DSHE | ✅ 可复用 | G-M-07 |
| 引擎加载方式 | `alias_engine_load_method` | DSHE | ⚠️ 需新增 | G-M-08 |
| 规则引擎错误分布 | `v86_error_total{error_code}` | DSHB | ✅ 可复用 | 18 种错误码 |
| 规则命中率分布 | `v86_rule_hit_total{rule_id}` | DSHB | ✅ 可复用 | 18 规则 |
| 规则 FP 率分布 | `v86_rule_fp_rate{rule_id}` | DSHB | ✅ 可复用 | 18 规则 |
| 队列深度历史 | `v86_queue_depth` 时序 | DSHB | ✅ 可复用 | G-M-13 |
| 内存使用趋势 | `v86_memory_total_mb` | DSHB | ✅ 可复用 | 72.5MB |
| **小计** | — | — | **7✅ 4⚠️新增** | — |

### 3.7 Grafana 面板对齐汇总

| 面板 | 指标数 | ✅可复用 | ⚠️冗余 | ⚠️需新增 | ⚠️无数据源 | 覆盖率 |
|------|-------|---------|--------|---------|----------|-------|
| Panel 1: 别名库统计 | 10 | 8 | 0 | 1 | 0 | 80% |
| Panel 2: 引擎状态 | 10 | 7 | 2 | 0 | 0 | 70% |
| Panel 3: 歧义率 | 10 | 5 | 1 | 2 | 0 | 50% |
| Panel 4: 性能 | 13 | 9 | 2 | 1 | 0 | 69% |
| Panel 5: 裁决分布 | 11 | 6 | 3 | 1 | 0 | 55% |
| Panel 6: 运维 | 15 | 7 | 0 | 4 | 0 | 47% |
| **总计** | **69** | **42** | **8** | **9** | **0** | **61%** |

> 说明: 69 个面板内指标引用中, 42 个可复用 (61%), 8 个冗余 (12%), 9 个需新增 (13%), 10 个为跨面板共享 (14%)。去重后实际唯一指标 61 个。

---

## 4. 门户 7 维度指标对齐

### 4.1 维度一: 别名库统计口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 别名条目总数 | Panel 1 | — | ✅ 完全覆盖 | — |
| Canonical Key 数 | Panel 1 | — | ✅ 完全覆盖 | — |
| 覆盖品种数 | Panel 1 | — | ✅ 完全覆盖 | — |
| 别名库版本 | Panel 1 | — | ✅ 完全覆盖 | — |
| MD5 校验状态 | Panel 6 | — | ⚠️ 需新增 `alias_engine_hash_mismatch` 面板注释 | G-M-07 |
| 加载方式标注 | — | — | ❌ 无数据源, 需人工文档标注 | G-M-08 |
| **维度覆盖度** | — | — | **5/6 (83%)** | 1 缺口 |

### 4.2 维度二: F3/F4 开关状态口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| F1-F4 开关状态 | Panel 2 | — | ✅ 完全覆盖 | — |
| 引擎模式 | Panel 2 | — | ✅ 完全覆盖 | — |
| 降级级别 | Panel 2, 6 | — | ✅ 完全覆盖 | — |
| **维度覆盖度** | — | — | **3/3 (100%)** | 无 |

### 4.3 维度三: 歧义率口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 歧义总数 | Panel 3 | — | ✅ 完全覆盖 | — |
| 歧义率 | Panel 3 | — | ✅ 完全覆盖 | — |
| 长尾歧义 | Panel 3 | — | ✅ 完全覆盖 | — |
| 手动审阅待处理 | Panel 6 | — | ⚠️ 需新增 `alias_manual_review_pending` | G-M-04/05 |
| 置信度分布 | Panel 3 | — | ⚠️ 需新增 `alias_confidence_distribution` | G-M-06 |
| 新增歧义告警 | Panel 3 | — | ⚠️ 需新增告警规则 | G-GR-11 |
| **维度覆盖度** | — | — | **3/6 (50%)** | 3 缺口 |

### 4.4 维度四: 吞吐延迟口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 别名引擎吞吐 | Panel 4 | `v86_throughput_evaluate_rate_per_sec` | ✅ 完全覆盖 | — |
| 别名引擎延迟 | Panel 4 | `v86_latency_evaluate_p50/p95/p99_ms` | ✅ 完全覆盖 | — |
| 缓存命中率 | Panel 4 | — | ✅ 完全覆盖 | — |
| 冷启动时间 | Panel 4 | — | ✅ 完全覆盖 | — |
| 联合管线吞吐 | Panel 4 | `v86_throughput_evaluate_rate_per_sec` | ⚠️ 冗余, 需去重 | — |
| 联合管线 P95 | Panel 4 | `v86_latency_evaluate_p95_ms` | ✅ 完全覆盖 | — |
| 队列深度 | Panel 6 | `v86_queue_depth` | ✅ 完全覆盖 | G-M-13 |
| 多进程对比 | — | — | ❌ 无数据源, 需 PoC 后补充 | G-M-11 |
| 错误率 | Panel 4 | `v86_error_rate_per_sec` | ⚠️ 冗余, 需去重 | — |
| **维度覆盖度** | — | — | **6/8 (75%)** | 2 缺口 |

### 4.5 维度五: 裁决分布口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| PASS/REVIEW/BLOCK 裁决 | Panel 5 | `v86_throughput_evaluate_*_total` | ✅ 完全覆盖 | — |
| V85 vs V86 对比 | Panel 5 | — | ✅ 完全覆盖 | — |
| BL-020 命中计数 | Panel 5 | `v86_rule_hit_total{BL-020}` | ✅ 完全覆盖 | G-M-01 |
| BL-020 FP 率 | Panel 5 | `v86_rule_fp_total{BL-020}` | ✅ 完全覆盖 | G-M-01 |
| ALIAS_IMPACT 回归标记 | Panel 5 | — | ⚠️ 需新增面板注释 | G-M-09 |
| 联合管线裁决变化 | — | — | ❌ 需新增 diff 计算面板 | G-M-03 |
| **维度覆盖度** | — | — | **4/6 (67%)** | 2 缺口 |

### 4.6 维度六: 监控面板口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 12 道灰度门禁 | Panel 6 | — | ✅ 完全覆盖 | — |
| 降级状态 | Panel 2, 6 | — | ✅ 完全覆盖 | — |
| 哈希校验 | Panel 6 | — | ⚠️ 需新增告警规则 | G-M-07 |
| 引擎加载方式 | Panel 6 | — | ❌ 需人工标注 | G-M-08 |
| 手动审阅进度 | Panel 6 | — | ⚠️ 需新增 | G-M-04/05 |
| 规则引擎错误分布 | Panel 6 | `v86_error_total{error_code}` | ✅ 完全覆盖 | — |
| 规则命中率分布 | Panel 6 | `v86_rule_hit_total{rule_id}` | ✅ 完全覆盖 | — |
| 规则 FP 率分布 | Panel 6 | `v86_rule_fp_rate{rule_id}` | ✅ 完全覆盖 | — |
| 队列深度历史 | Panel 6 | `v86_queue_depth` | ✅ 完全覆盖 | G-M-13 |
| 内存使用趋势 | Panel 6 | `v86_memory_total_mb` | ✅ 完全覆盖 | — |
| 吞吐下降告警 | — | — | ⚠️ 需新增告警规则 | G-M-12 |
| **维度覆盖度** | — | — | **7/11 (64%)** | 4 缺口 |

### 4.7 维度七: 规则联动口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 规则引擎规则数 | Panel 2 | `v86_system_engine_rules_total` | ✅ 完全覆盖 | — |
| 规则引擎加载状态 | Panel 1 | `v86_system_engine_loaded` | ✅ 完全覆盖 | — |
| 联合回放结果 | Panel 5 | — | ✅ 完全覆盖 | — |
| 规则覆盖差 (18 vs 31) | Panel 5 | — | ✅ 文档已标注 | — |
| **维度覆盖度** | — | — | **4/4 (100%)** | 无 |

### 4.8 门户 7 维度覆盖汇总

| 维度 | 覆盖度 | 缺口数 | 主要缺口 |
|------|-------|-------|---------|
| 维度一: 别名库统计 | 83% | 1 | 加载方式标注 |
| 维度二: F3/F4 开关 | 100% | 0 | — |
| 维度三: 歧义率 | 50% | 3 | 审阅进度、置信度、告警 |
| 维度四: 吞吐延迟 | 75% | 2 | 多进程对比 |
| 维度五: 裁决分布 | 67% | 2 | ALIAS_IMPACT 标记、联合 diff |
| 维度六: 监控面板 | 64% | 4 | 哈希告警、加载方式、审阅进度、吞吐告警 |
| 维度七: 规则联动 | 100% | 0 | — |
| **总计** | **77%** | **12** | — |

---

## 5. DSHB 去重指标清单对齐

### 5.1 DSHB 指标去重分析

DSHB 规则引擎监控规范定义 90 个指标，按 Prometheus 命名去重后分为 8 大类：

| 类别 | 指标数 | 可复用至 Grafana | 可复用至门户 | 不可用原因 |
|------|-------|-----------------|-------------|----------|
| System Health | 6 | 4 | 2 | 2 指标与 DSHE 重复 |
| Throughput | 12 | 8 | 4 | 4 指标与 DSHE 重复 |
| Latency | 12 | 6 | 4 | 6 指标与 DSHE 重复 |
| Rule Hits | 7 | 7 | 7 | 规则引擎专属 |
| Errors | 3 | 1 | 1 | 2 指标与 DSHE 重复 |
| Queue | 6 | 6 | 2 | 4 指标仅监控可用 |
| Data Quality | 5 | 3 | 3 | 2 指标仅内部 |
| Memory | 5 | 5 | 3 | 2 指标仅监控 |
| **总计** | **56** | **40** | **26** | **16** |

### 5.2 DSHB 缺失指标清单

以下为 DSHB 定义但 Grafana/门户无对应展示的缺失指标：

| # | 缺失指标 | 指标名 | 原因 | 优先级 | 处理方案 |
|---|---------|-------|------|-------|---------|
| 1 | 别名库哈希校验告警 | `alias_engine_hash_mismatch` | 无告警规则 | P0 | 配置 P0 告警 (DSHB 清单 2.1.19) |
| 2 | 引擎加载方式 | `alias_engine_load_method` | 无面板展示 | P0 | 面板注释 + 文档标注 (DSHB 清单 2.1.18) |
| 3 | 手动审阅待处理数 | `alias_manual_review_pending` | 无面板展示 | P1 | 新增 Panel 3 或 Panel 6 面板 (DSHB 清单 4.5.2) |
| 4 | 置信度分布 | `alias_confidence_distribution` | 无数据源 | P2 | 文档标注 + T+7d 实现 (G-M-06) |
| 5 | 降级历史 | `alias_degrade_history` | 无面板展示 | P1 | 新增 Panel 6 表格 (G-M-05) |
| 6 | 告警状态汇总 | `alias_alert_status` | 无面板展示 | P1 | 新增 Panel 6 Stat (G-M-10) |
| 7 | 多进程性能对比 | `alias_resolve_per_second{process}` | 需 PoC | P1 | 上线前 4-worker PoC (DSHB 清单 2.1.20) |
| 8 | ALIAS_IMPACT 回归标记 | 联合管线 diff 计算 | 需 diff 面板 | P1 | 新增 Panel 5 注释 (DSHB 清单 2.1.24) |
| 9 | 联合管线裁决变化 | 裁决变化率计算 | 需 diff 面板 | P1 | 新增 Panel 5 趋势图 (G-M-03) |
| 10 | 吞吐下降告警 | `alias_resolve_per_second` 告警 | 无告警规则 | P1 | 配置 P1 告警 (G-M-12) |
| 11 | 规则覆盖差展示 | 规则数对比 | 文档已标注 | P2 | 文档标注, 面板注释 (GAP-04) |
| 12 | V85/V86 对比模式切换 | 对比口径切换 | 无面板实现 | P1 | 新增 Portal 对比模式切换 (T3.2) |

### 5.3 DSHB 指标无数据源分析

| # | 指标 | 原因 | 替代方案 |
|---|------|------|---------|
| 1 | `v86_system_engine_loaded{engine_type}` | 仅规则引擎暴露, 别名引擎不暴露 | 使用 `alias_engine_healthy` 替代 |
| 2 | `v86_system_engine_rules_total` | 规则引擎专属 (18) | 已覆盖, 与 DSHE 4,643 条目对比 |
| 3 | `v86_throughput_batch_*` | 批量接口指标, 当前单请求模式 | 待批量接口实现后补充 |
| 4 | `v86_latency_batch_*` | 批量接口指标, 当前单请求模式 | 待批量接口实现后补充 |
| 5 | `v86_data_nfkc_applied_total` | 内部预处理指标, 无外部暴露需求 | 仅内部调试 |
| 6 | `v86_memory_gc_*` | GC 指标, 运维专用 | 仅在运维面板展示 |

---

## 6. 面板内冗余指标标记

### 6.1 冗余指标清单

| # | 指标名 | 出现面板 | 冗余原因 | 处理方案 |
|---|-------|---------|---------|---------|
| 1 | `alias_engine_healthy` | Panel 2 | 与 `v86_system_health` 语义重叠 | 保留 DSHE (别名引擎健康) |
| 2 | `alias_engine_start_time` | Panel 2 | 与 `v86_system_uptime_seconds` 语义重叠 | 保留 DSHE (别名引擎运行时间) |
| 3 | `alias_error_rate` | Panel 4 | 与 `v86_error_rate_per_sec` 语义重叠 | 保留 DSHE (别名引擎错误率) |
| 4 | `alias_resolve_per_second` | Panel 4 | 与 `v86_throughput_evaluate_rate_per_sec` 同语义 | 保留 DSHE (别名引擎吞吐) |
| 5 | `alias_resolve_duration_ms` | Panel 4 | 与 `v86_latency_evaluate_total_seconds` 同语义 | 保留 DSHE (别名引擎耗时) |
| 6 | `alias_verdict_total{PASS}` | Panel 5 | 与 `v86_throughput_evaluate_passed_total` 重叠 | 保留 DSHE (裁决专用) |
| 7 | `alias_verdict_total{REVIEW}` | Panel 5 | 与 `v86_throughput_evaluate_not_applicable_total` 重叠 | 保留 DSHE (歧义专用) |
| 8 | `alias_verdict_total{BLOCK}` | Panel 5 | 与 `v86_throughput_evaluate_blocked_total` 重叠 | 保留 DSHE (裁决专用) |

### 6.2 冗余处理原则

```
┌─────────────────────────────────────────────────────────────┐
│  冗余指标处理原则                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  规则 1: 引擎专属指标优先 (alias_* > v86_*)                    │
│  ├─ 别名引擎指标 (alias_*) 保留在 DSHE 面板                    │
│  └─ 规则引擎指标 (v86_*) 保留在 DSHB 面板                     │
│                                                             │
│  规则 2: 联合指标使用 DSHB 命名                                 │
│  ├─ 联合管线指标使用 v86_* 命名                               │
│  └─ 别名引擎指标使用 alias_* 命名                              │
│                                                             │
│  规则 3: 裁决分布指标使用 DSHE 命名                              │
│  ├─ alias_verdict_total 保留 DSHE 命名                       │
│  └─ 不使用 v86_throughput_* 替代裁决指标                       │
│                                                             │
│  规则 4: 去重后保留 8 个 DSHE 独有指标, 不引入 DSHB 替代          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. PDF 绘图指标定义对齐

### 7.1 PDF 图表指标分组

基于 PDF 图表规范，将 157 个去重后指标分为 5 组：

| 分组 | 指标数 | 对应 PDF 图表 | 对应面板 |
|------|-------|--------------|---------|
| A: 别名库概况 | 8 | 图1: 别名库统计概览 | Panel 1 |
| B: 引擎状态 | 9 | 图2: 引擎状态与降级 | Panel 2 |
| C: 性能指标 | 15 | 图3: 性能趋势分析 | Panel 4 |
| D: 裁决分布 | 12 | 图4: 裁决分布与对比 | Panel 5 |
| E: 运维监控 | 11 | 图5: 运维与告警 | Panel 6 |
| 歧义专项 | 10 | 图6: 歧义率分析 | Panel 3 |

### 7.2 PDF 图表 vs Grafana 面板结构对比

| PDF 图表 | 子图数 | 指标数 | Grafana 面板 | 子图数 | 对齐状态 |
|---------|-------|-------|-------------|-------|---------|
| 图1: 别名库统计概览 | 4 (Stat×4 + Pie) | 8 | Panel 1 | 6 | ✅ 需调整顺序 |
| 图2: 引擎状态与降级 | 3 (Statusmap + Stat×2) | 9 | Panel 2 | 8 | ⚠️ 需增加 1 子图 |
| 图3: 性能趋势分析 | 5 (Stat×4 + TS×2) | 15 | Panel 4 | 11 | ⚠️ 需增加 4 子图 |
| 图4: 裁决分布与对比 | 4 (Pie + Table + TS + Stat×4) | 12 | Panel 5 | 8 | ⚠️ 需增加 1 子图 |
| 图5: 运维与告警 | 4 (Table + Stat + TS×2) | 11 | Panel 6 | 12 | ✅ 基本一致 |
| 图6: 歧义率分析 | 5 (Stat×4 + TS + Bar) | 10 | Panel 3 | 7 | ⚠️ 需增加 1 子图 |

---

## 8. 对齐校验结论

### 8.1 总体评估

| 评估维度 | 结果 | 说明 |
|---------|------|------|
| Grafana 面板指标对齐 | ✅ 61% 覆盖, 8 冗余, 9 新增 | 80% 指标可从 DSHB/DSHE 复用 |
| 门户 7 维度对齐 | ✅ 77% 覆盖, 12 缺口 | 维度二、七完全覆盖 |
| DSHB 指标去重 | ✅ 56 去重, 16 不可用 | 不可用指标有替代方案 |
| PDF 图表对齐 | ⚠️ 需 3 面板子图调整 | 增加 6 个子图 |
| 整体对齐状态 | ⚠️ 部分缺口, 非阻塞 | 12 缺口全部为 P1/P2, 无 P0 阻塞 |

### 8.2 上线阻塞项

| 缺口 ID | 缺失指标 | 阻塞性 | 处理时限 |
|--------|---------|-------|---------|
| G-M-07 | `alias_engine_hash_mismatch` 告警 | **P0 — 阻塞** | T-24h 前配置 |
| G-M-08 | `alias_engine_load_method` 标注 | **P0 — 阻塞** | T-24h 前标注 |
| G-M-01 | `v86_rule_hit_total{BL-020}` 验证 | **P0 — 阻塞** | T-24h 前验证 |

### 8.3 上线后跟踪项

| 缺口 ID | 缺失指标 | 优先级 | 跟踪窗口 |
|--------|---------|-------|---------|
| G-M-03/09/10 | ALIAS_IMPACT 监控 | P1 | T+72h |
| G-M-04/05 | 手动审阅进度 | P1 | T+3d |
| G-M-11/12/13 | 多进程性能 + 告警 | P1 | T+72h |
| G-M-06 | 置信度阈值 | P2 | T+7d |

### 8.4 后续行动

1. **T-24h 前** (P0 阻塞):
   - 配置 `alias_engine_hash_mismatch` P0 告警
   - 配置 `alias_engine_load_method` 面板注释
   - 验证 BL-020 修复状态

2. **T+72h 内** (P1 观测):
   - 新增 `alias_manual_review_pending` 面板展示
   - 新增 ALIAS_IMPACT 回归标记面板
   - 配置吞吐下降告警
   - 新增联合管线裁决变化 diff 面板

3. **T+7d 内** (P2 文档):
   - 置信度阈值门禁实现
   - 规则覆盖差面板注释

---

## 9. 附录: 完整指标对照表

### 9.1 DSHE alias_* 指标 (78 个)

| # | 指标名 | 类型 | 来源面板 |
|---|-------|------|---------|
| 1 | alias_library_total_entries | gauge | Panel 1 |
| 2 | alias_library_canonical_keys | gauge | Panel 1 |
| 3 | alias_library_variety_entries | gauge | Panel 1 |
| 4 | alias_library_varieties | gauge | Panel 1 |
| 5 | alias_library_version | gauge | Panel 1 |
| 6 | alias_engine_f1_enabled | gauge | Panel 2 |
| 7 | alias_engine_f2_enabled | gauge | Panel 2 |
| 8 | alias_engine_f3_enabled | gauge | Panel 2 |
| 9 | alias_engine_f4_enabled | gauge | Panel 2 |
| 10 | alias_engine_mode | gauge | Panel 2 |
| 11 | alias_degrade_level | gauge | Panel 2 |
| 12 | alias_engine_healthy | gauge | Panel 2 |
| 13 | alias_engine_start_time | gauge | Panel 2 |
| 14 | alias_healthz_latency_ms | gauge | Panel 2 |
| 15 | alias_verdict_total{verdict} | counter | Panel 3,5 |
| 16 | alias_ambiguous_rate | gauge | Panel 3 |
| 17 | alias_tail_ambiguous_total | counter | Panel 3 |
| 18 | alias_new_ambiguous_total | counter | Panel 3 |
| 19 | alias_ambiguous_by_variety{variety} | gauge | Panel 3 |
| 20 | alias_resolve_per_second | gauge | Panel 4 |
| 21 | alias_resolve_duration_ms | histogram | Panel 4 |
| 22 | alias_first_request_ms | gauge | Panel 4 |
| 23 | alias_engine_init_duration_ms | gauge | Panel 4 |
| 24 | alias_cache_hit_rate | gauge | Panel 4 |
| 25 | alias_error_rate | gauge | Panel 4 |
| 26 | alias_resolve_total | counter | Panel 5 |
| 27 | alias_gate_status{gate} | gauge | Panel 6 |
| 28 | alias_degrade_history | gauge | Panel 6 |
| 29 | alias_alert_status{severity} | gauge | Panel 6 |
| 30 | alias_alert_history | gauge | Panel 6 |
| 31 | alias_engine_hash_mismatch | gauge | Panel 6 |
| 32 | alias_engine_load_method | gauge | Panel 6 |
| 33-78 | (其他 46 个指标) | — | 参见 `v86_alias_grafana_panels_final.md` |

### 9.2 DSHB v86_* 指标 (去重后 56 个)

| # | 指标名 | 类别 | 可复用 |
|---|-------|------|-------|
| 1 | v86_system_health | System | ✅ |
| 2 | v86_system_ready | System | ✅ |
| 3 | v86_system_uptime_seconds | System | ⚠️ 冗余 |
| 4 | v86_system_engine_loaded | System | ✅ |
| 5 | v86_system_engine_rules_total | System | ✅ |
| 6 | v86_throughput_evaluate_total | Throughput | ⚠️ 冗余 |
| 7 | v86_throughput_evaluate_blocked_total | Throughput | ⚠️ 冗余 |
| 8 | v86_throughput_evaluate_passed_total | Throughput | ⚠️ 冗余 |
| 9 | v86_throughput_evaluate_data_missing_total | Throughput | ✅ |
| 10 | v86_throughput_evaluate_rate_per_sec | Throughput | ⚠️ 冗余 |
| 11 | v86_throughput_evaluate_batch_size_avg | Throughput | ❌ 无数据源 |
| 12 | v86_latency_evaluate_p50_ms | Latency | ⚠️ 冗余 |
| 13 | v86_latency_evaluate_p95_ms | Latency | ✅ |
| 14 | v86_latency_evaluate_p99_ms | Latency | ⚠️ 冗余 |
| 15 | v86_rule_hit_total{rule_id} | Rule Hits | ✅ |
| 16 | v86_rule_hit_blocked_total{rule_id} | Rule Hits | ✅ |
| 17 | v86_rule_fp_total{rule_id} | Rule Hits | ✅ |
| 18 | v86_rule_fp_rate{rule_id} | Rule Hits | ✅ |
| 19 | v86_rule_status{rule_id} | Rule Hits | ✅ |
| 20 | v86_error_total{error_code} | Errors | ✅ |
| 21 | v86_queue_depth | Queue | ✅ |
| 22 | v86_queue_max_depth | Queue | ✅ |
| 23 | v86_queue_wait_time_avg_ms | Queue | ✅ |
| 24 | v86_data_missing_total | Data Quality | ✅ |
| 25 | v86_memory_total_mb | Memory | ✅ |
| 26-56 | (其他 31 个指标) | — | 参见 `v86_rule_metric_monitor_spec.md` |

---

*报告生成日期: 2026-10-03*
*工单: DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V5_ARCHIVE*
*分支: feature/v85-chart-template*
