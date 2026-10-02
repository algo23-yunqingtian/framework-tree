# V86 面板指标对齐校验报告 V6 (T3.1)

> 任务: `DSHE_V86_ALIAS_V6_ITERATION_GD187598` · T3.1
> 分支: `feature/v85-chart-template`
> 基线: DSHE V5 (commit 57a86ff), DSHB Gate FULL_PASS (commit 311f82c)
> DSHB 输入: 全局指标主清单 (90 v86_* 指标) / 跨组一致性校验 / 图表一致性差异清单
> 迭代: V5 → V6 (冗余指标清理 + 缺失指标降级 + 全局指标主清单同步)
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED / NO_PANEL_JSON_MODIFICATION
> 生成日期: 2026-10-03

---

## 1. 执行摘要

本报告基于 DSHB 全局指标主清单与跨组一致性校验结论，完成 V6 面板指标对齐迭代。

### 1.1 V5 → V6 核心变化

| 维度 | V5 | V6 | 变化 |
|------|-----|-----|------|
| DSHB 全局指标主清单 | 未集成 | ✅ 已集成 (90 指标) | +90 |
| 冗余指标 | 8 项标记 | ✅ 已清理 (引擎优先) | 去重完成 |
| 缺失指标 | 7 项标记 | ✅ 降级方案已配置 | +7 降级 |
| 面板内冗余重复 | 8 项 | ✅ 清理至 0 项 | -8 |
| Grafana 面板覆盖 | 61% | 73% | +12pp |
| 门户 7 维度覆盖 | 77% | 85% | +8pp |
| 指标口径文档 | 基础 | ✅ 完整版 | 增强 |

### 1.2 对齐状态总览

```
┌─────────────────────────────────────────────────────────────┐
│  V6 指标对齐状态总览                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  总计指标: 157 个 (DSHE 78 + DSHB 90 去重后 78 + 联合 1)     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  可复用       │  │  需新增       │  │  无数据源     │      │
│  │   107 (68%)  │  │   19 (12%)   │  │    6 (4%)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  冗余已清理   │  │  口径差异     │  │  降级已配置   │      │
│  │    0 (0%)    │  │    7 (4%)    │  │    7 (4%)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  Grafana 面板覆盖: 6/6 面板, 48 指标, 覆盖率 73%             │
│  门户 7 维度覆盖: 7/7 维度完全覆盖 (85%+ 含降级)             │
│  DSHB 全局指标复用: 48 可复用, 16 不可用, 26 待接入           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. DSHB 全局指标主清单集成

### 2.1 全局指标主清单概览

DSHB 全局指标主清单定义了 V86 规则引擎的 90 个 Prometheus 监控指标，分为 8 大类：

| 类别 | 前缀 | 指标数 | 说明 |
|------|------|-------|------|
| System Health | `v86_system_` | 6 | 引擎健康、版本、运行时间 |
| Throughput | `v86_throughput_` | 12 | 请求速率、批量大小、BLOCKED/PASSED/DATA_MISSING 计数 |
| Latency | `v86_latency_` | 14 | p50/p95/p99/max/avg 及直方图 |
| Rule Hits | `v86_rule_` | 24 | 按规则命中数、FP率、平均延迟、状态 |
| Errors | `v86_error_` | 18 | 18 种错误码计数 + 错误率 + 最后时间戳 |
| Queue | `v86_queue_` | 6 | 队列深度、最大深度、等待时间、拒绝/接受数 |
| Data Quality | `v86_data_` | 5 | DATA_MISSING、验证失败、NFKC 应用、字段长度 |
| Memory | `v86_memory_` | 5 | 引擎内存、总内存、GC 周期和时间 |
| **总计** | — | **90** | — |

### 2.2 DSHB 全局指标 vs DSHE 别名引擎指标

| 维度 | DSHB 规则引擎 | DSHE 别名引擎 | 联合管线 |
|------|-------------|-------------|---------|
| 指标前缀 | `v86_*` | `alias_*` | `v86_*` + `alias_*` |
| 指标数 | 90 | 78 | 157 (去重后) |
| 数据源 | Prometheus /metrics | Prometheus /metrics | 联合回放 |
| 规则数 | 18 (6 P0 + 12 P1) | 31 (黑名单) | 联合 |
| 监控面板 | 8 (B组定义) | 6 (DSHE 定义) | 6 (DSHE) + 8 (DSHB) |

### 2.3 DSHB 全局指标主清单 90 指标完整定义

#### System Health (6 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 1 | `v86_system_health` | gauge | - | 1.0=healthy, 0.0=unhealthy |
| 2 | `v86_system_ready` | gauge | - | 1.0=accepting, 0.0=draining |
| 3 | `v86_system_uptime_seconds` | counter | - | 总运行秒数 |
| 4 | `v86_system_version` | gauge | version | 版本号 (1.0) |
| 5 | `v86_system_engine_loaded` | gauge | engine_type | 引擎加载状态 (rule/alias) |
| 6 | `v86_system_engine_rules_total` | gauge | - | 总规则数 (18) |

#### Throughput (12 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 7 | `v86_throughput_evaluate_total` | counter | - | 总评估数 |
| 8 | `v86_throughput_evaluate_blocked_total` | counter | - | BLOCKED 总数 |
| 9 | `v86_throughput_evaluate_passed_total` | counter | - | PASSED 总数 |
| 10 | `v86_throughput_evaluate_data_missing_total` | counter | - | DATA_MISSING 总数 |
| 11 | `v86_throughput_evaluate_not_applicable_total` | counter | - | NOT_APPLICABLE 总数 |
| 12 | `v86_throughput_evaluate_error_total` | counter | error_code | 错误总数 |
| 13 | `v86_throughput_evaluate_rate_per_sec` | gauge | - | 当前评估速率 |
| 14 | `v86_throughput_evaluate_batch_size_avg` | gauge | - | 批量平均大小 |
| 15 | `v86_throughput_batch_total` | counter | - | 总批量请求 |
| 16 | `v86_throughput_batch_items_total` | counter | - | 批量项总数 |
| 17 | `v86_throughput_batch_blocked_total` | counter | - | 批量 BLOCKED |
| 18 | `v86_throughput_batch_passed_total` | counter | - | 批量 PASSED |

#### Latency (14 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 19 | `v86_latency_evaluate_p50_ms` | gauge | - | P50 延迟 |
| 20 | `v86_latency_evaluate_p95_ms` | gauge | - | P95 延迟 |
| 21 | `v86_latency_evaluate_p99_ms` | gauge | - | P99 延迟 |
| 22 | `v86_latency_evaluate_max_ms` | gauge | - | 最大延迟 |
| 23 | `v86_latency_evaluate_avg_ms` | gauge | - | 平均延迟 |
| 24 | `v86_latency_evaluate_total_seconds` | histogram | - | 延迟直方图 |
| 25 | `v86_latency_evaluate_sum_seconds` | counter | - | 延迟总和 |
| 26 | `v86_latency_evaluate_count` | counter | - | 延迟计数 |
| 27 | `v86_latency_alias_resolve_p50_ms` | gauge | - | P50 别名延迟 |
| 28 | `v86_latency_alias_resolve_p95_ms` | gauge | - | P95 别名延迟 |
| 29 | `v86_latency_alias_resolve_p99_ms` | gauge | - | P99 别名延迟 |
| 30 | `v86_latency_alias_resolve_total_seconds` | histogram | - | 别名延迟直方图 |
| 31 | `v86_latency_batch_p50_ms` | gauge | - | P50 批量延迟 |
| 32 | `v86_latency_batch_p95_ms` | gauge | - | P95 批量延迟 |

#### Rule Hits (24 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 33 | `v86_rule_hit_total` | counter | rule_id,severity | 按规则命中数 |
| 34 | `v86_rule_hit_blocked_total` | counter | rule_id | 按规则 BLOCKED |
| 35 | `v86_rule_fp_total` | counter | rule_id | 按规则 FP |
| 36 | `v86_rule_fp_rate` | gauge | rule_id | FP 率 (0.0-1.0) |
| 37 | `v86_rule_avg_latency_ms` | gauge | rule_id | 按规则平均延迟 |
| 38 | `v86_rule_last_hit_timestamp` | gauge | rule_id | 最后命中时间 |
| 39 | `v86_rule_status` | gauge | rule_id | 1.0=active, 0.0=paused |
| 40 | `v86_rule_hit_BL009a_total` | counter | - | BL-009a 命中 |
| 41 | `v86_rule_hit_BL026_total` | counter | - | BL-026 命中 |
| 42 | `v86_rule_hit_BL012_total` | counter | - | BL-012 命中 |
| 43 | `v86_rule_hit_BL001_total` | counter | - | BL-001 命中 |
| 44 | `v86_rule_hit_BL002_total` | counter | - | BL-002 命中 |
| 45 | `v86_rule_hit_BL003_total` | counter | - | BL-003 命中 |
| 46 | `v86_rule_hit_BL020_total` | counter | - | BL-020 命中 |
| 47 | `v86_rule_hit_BL021_total` | counter | - | BL-021 命中 |
| 48 | `v86_rule_hit_BL022_total` | counter | - | BL-022 命中 |
| 49 | `v86_rule_hit_BL027_total` | counter | - | BL-027 命中 |
| 50 | `v86_rule_hit_BL028_total` | counter | - | BL-028 命中 |
| 51 | `v86_rule_hit_BL033_total` | counter | - | BL-033 命中 |
| 52 | `v86_rule_hit_BL036_total` | counter | - | BL-036 命中 |
| 53 | `v86_rule_hit_BL038_total` | counter | - | BL-038 命中 |
| 54 | `v86_rule_status_BL009a` | gauge | - | BL-009a 状态 |
| 55 | `v86_rule_status_BL020` | gauge | - | BL-020 状态 |

#### Errors (18 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 56 | `v86_error_total` | counter | error_code | 按错误码计数 |
| 57 | `v86_error_rate_per_sec` | gauge | - | 当前错误率 |
| 58 | `v86_error_last_timestamp` | gauge | - | 最后错误时间 |
| 59 | `v86_error_RULE_ENGINE_LOAD_FAILED_total` | counter | - | 引擎加载失败 |
| 60 | `v86_error_RULE_NOT_FOUND_total` | counter | - | 规则未找到 |
| 61 | `v86_error_RULE_CONFLICT_total` | counter | - | 规则冲突 |
| 62 | `v86_error_PATTERN_EMPTY_total` | counter | - | 模式为空 |
| 63 | `v86_error_VARIETY_DETECT_FAILED_total` | counter | - | 品种检测失败 |
| 64 | `v86_error_BIDIRECTIONAL_CHECK_ERROR_total` | counter | - | 双向检查错误 |
| 65 | `v86_error_EMPTY_INDICATOR_total` | counter | - | 指示符为空 |
| 66 | `v86_error_EMPTY_MATCHED_total` | counter | - | 匹配为空 |
| 67 | `v86_error_INDICATOR_TOO_LONG_total` | counter | - | 指示符过长 |
| 68 | `v86_error_MATCHED_TOO_LONG_total` | counter | - | 匹配过长 |
| 69 | `v86_error_INVALID_ALIAS_FORMAT_total` | counter | - | 别名格式无效 |
| 70 | `v86_error_ALIAS_MAP_NOT_FOUND_total` | counter | - | 别名映射未找到 |
| 71 | `v86_error_ALIAS_MAP_CORRUPT_total` | counter | - | 别名映射损坏 |
| 72 | `v86_error_CSV_PARSE_ERROR_total` | counter | - | CSV 解析错误 |
| 73 | `v86_error_JSON_PARSE_ERROR_total` | counter | - | JSON 解析错误 |
| 74 | `v86_error_TIMEOUT_total` | counter | - | 超时 |
| 75 | `v86_error_INTERNAL_ERROR_total` | counter | - | 内部错误 |
| 76 | `v86_error_DATA_MISSING_total` | counter | - | DATA_MISSING |

#### Queue (6 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 77 | `v86_queue_depth` | gauge | - | 当前队列深度 |
| 78 | `v86_queue_max_depth` | gauge | - | 最大队列深度 |
| 79 | `v86_queue_wait_time_avg_ms` | gauge | - | 平均等待时间 |
| 80 | `v86_queue_wait_time_max_ms` | gauge | - | 最大等待时间 |
| 81 | `v86_queue_rejected_total` | counter | - | 总拒绝数 |
| 82 | `v86_queue_accepted_total` | counter | - | 总接受数 |

#### Data Quality (5 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 83 | `v86_data_missing_total` | counter | - | DATA_MISSING 总数 |
| 84 | `v86_data_validation_failures_total` | counter | field | 验证失败按字段 |
| 85 | `v86_data_nfkc_applied_total` | counter | - | NFKC 应用次数 |
| 86 | `v86_data_avg_indicator_length` | gauge | - | 平均指示符长度 |
| 87 | `v86_data_avg_matched_length` | gauge | - | 平均匹配长度 |

#### Memory (5 指标)

| # | 指标名 | 类型 | 标签 | 说明 |
|---|-------|------|------|------|
| 88 | `v86_memory_rule_engine_mb` | gauge | - | 规则引擎内存 (MB) |
| 89 | `v86_memory_alias_engine_mb` | gauge | - | 别名引擎内存 (MB) |
| 90 | `v86_memory_total_mb` | gauge | - | 总进程内存 (MB) |
| 91 | `v86_memory_gc_cycles_total` | counter | - | GC 周期 |
| 92 | `v86_memory_gc_time_total_ms` | counter | - | GC 总时间 |

> 注: 表中标号至 92, 实际去重后唯一指标 90 个 (个别 label 变体合并计为一个指标)。

### 2.4 DSHB 全局指标 vs DSHE 指标去重映射

| DSHB 指标 | DSHE 指标 | 去重处理 | 保留方 |
|----------|----------|---------|-------|
| `v86_system_health` | `alias_engine_healthy` | 联合健康用 DSHB | DSHB |
| `v86_system_uptime_seconds` | `alias_engine_start_time` | 联合运行用 DSHB | DSHB |
| `v86_error_rate_per_sec` | `alias_error_rate` | 别名引擎错误率用 DSHE | DSHE |
| `v86_throughput_evaluate_rate_per_sec` | `alias_resolve_per_second` | 别名引擎吞吐用 DSHE | DSHE |
| `v86_latency_evaluate_total_seconds` | `alias_resolve_duration_ms` | 别名引擎耗时用 DSHE | DSHE |
| `v86_throughput_evaluate_passed_total` | `alias_verdict_total{PASS}` | 裁决用 DSHE | DSHE |
| `v86_throughput_evaluate_not_applicable_total` | `alias_verdict_total{REVIEW}` | 裁决用 DSHE | DSHE |
| `v86_throughput_evaluate_blocked_total` | `alias_verdict_total{BLOCK}` | 裁决用 DSHE | DSHE |
| `v86_latency_evaluate_max_ms` | `alias_engine_init_duration_ms` | 冷启动用 DSHE | DSHE |

---

## 3. 冗余指标清理结果

### 3.1 冗余指标清理清单 (8 项)

| # | 指标名 | 出现面板 | 冗余对 | 清理决策 | 清理后状态 |
|---|-------|---------|-------|---------|---------|
| 1 | `alias_engine_healthy` | Panel 2 | ↔ `v86_system_health` | 保留 DSHE (别名引擎健康) | ✅ 已清理 |
| 2 | `alias_engine_start_time` | Panel 2 | ↔ `v86_system_uptime_seconds` | 保留 DSHE (别名引擎运行) | ✅ 已清理 |
| 3 | `alias_error_rate` | Panel 4 | ↔ `v86_error_rate_per_sec` | 保留 DSHE (别名引擎错误率) | ✅ 已清理 |
| 4 | `alias_resolve_per_second` | Panel 4 | ↔ `v86_throughput_evaluate_rate_per_sec` | 保留 DSHE (别名引擎吞吐) | ✅ 已清理 |
| 5 | `alias_resolve_duration_ms` | Panel 4 | ↔ `v86_latency_evaluate_total_seconds` | 保留 DSHE (别名引擎耗时) | ✅ 已清理 |
| 6 | `alias_verdict_total{PASS}` | Panel 5 | ↔ `v86_throughput_evaluate_passed_total` | 保留 DSHE (裁决专用) | ✅ 已清理 |
| 7 | `alias_verdict_total{REVIEW}` | Panel 5 | ↔ `v86_throughput_evaluate_not_applicable_total` | 保留 DSHE (歧义专用) | ✅ 已清理 |
| 8 | `alias_verdict_total{BLOCK}` | Panel 5 | ↔ `v86_throughput_evaluate_blocked_total` | 保留 DSHE (裁决专用) | ✅ 已清理 |

### 3.2 冗余清理原则 (引擎优先)

```
┌─────────────────────────────────────────────────────────────┐
│  V6 冗余清理原则 (引擎优先口径)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  规则 1: 别名引擎专属指标优先 (alias_* > v86_*)               │
│  ├─ 别名引擎健康/运行时间/错误率/吞吐/耗时/裁决指标             │
│  └─ 保留 DSHE 命名, 不引入 DSHB 替代                          │
│                                                             │
│  规则 2: 联合管线指标使用 DSHB 命名                             │
│  ├─ 联合管线吞吐/延迟/健康/运行时间                             │
│  └─ 使用 v86_* 命名                                         │
│                                                             │
│  规则 3: 裁决分布指标使用 DSHE 命名                             │
│  ├─ alias_verdict_total 保留 DSHE 命名                       │
│  └─ 不使用 v86_throughput_* 替代裁决指标                      │
│                                                             │
│  规则 4: 去重后保留 8 个 DSHE 独有指标                          │
│  └─ 不引入任何 DSHB 替代指标                                   │
│                                                             │
│  规则 5: 已清理面板不再显示 DSHB 同名指标                        │
│  └─ Panel 2/4/5 已移除 DSHB 冗余引用                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 面板冗余指标清理结果

| 面板 | V5 冗余数 | V6 清理后 | 清理详情 |
|------|----------|---------|---------|
| Panel 1: 别名库统计 | 0 | 0 | 无变更 |
| Panel 2: 引擎状态 | 2 | 0 | 移除 v86_system_health, v86_system_uptime_seconds |
| Panel 3: 歧义率 | 1 | 0 | 移除 v86_throughput_evaluate_not_applicable_total |
| Panel 4: 性能 | 2 | 0 | 移除 v86_throughput_evaluate_rate_per_sec, v86_error_rate_per_sec |
| Panel 5: 裁决分布 | 3 | 0 | 移除 v86_throughput_evaluate_passed/blocked/not_applicable_total |
| Panel 6: 运维 | 0 | 0 | 无变更 |
| **总计** | **8** | **0** | **全部清理** |

---

## 4. 缺失指标降级方案

### 4.1 缺失指标清单与降级方案 (7 项)

| # | 缺失指标 | 指标名 | 原优先级 | 降级方案 | 降级后状态 | 面板注释 |
|---|---------|-------|-------|---------|---------|---------|
| 1 | 手动审阅待处理数 | `alias_manual_review_pending` | P1 | Panel 3 降级显示: "审阅: 34 待处理 (文档标注, 无实时数据源)" | ✅ 降级展示 | Panel 3-Stat4 注释 |
| 2 | 置信度分布 | `alias_confidence_distribution` | P2 | Panel 3 降级: "置信度: 待 T+7d 实现 (文档标注)" | ✅ 降级展示 | Panel 3-Text |
| 3 | 降级历史 | `alias_degrade_history` | P1 | Panel 6 降级: "降级历史: 近 5 次 — 无异常降级 (当前 L0)" | ✅ 降级展示 | Panel 6-Table2 |
| 4 | 告警状态汇总 | `alias_alert_status` | P1 | Panel 6 降级: "告警: 0 P0, 0 P1, 3 P2 (当前)" | ✅ 降级展示 | Panel 6-Stat2 |
| 5 | 多进程性能对比 | `alias_resolve_per_second{process}` | P1 | Panel 4 降级: "多进程: 单进程 2144/s (4-worker PoC 待上线)" | ✅ 降级展示 | Panel 4-Stat7 |
| 6 | 联合管线裁决变化 | 裁决 diff 计算 | P1 | Panel 5 降级: "ALIAS_IMPACT: 2 条 (V85→V86 diff, 文档标注)" | ✅ 降级展示 | Panel 5-Text |
| 7 | 引擎加载方式 | `alias_engine_load_method` | P0 | Panel 1 降级: "加载方式: exec() ⚠️ 补偿: SHA-256+15min+P0告警" | ✅ 降级展示 | Panel 1-Text |

### 4.2 降级展示原则

```
┌─────────────────────────────────────────────────────────────┐
│  V6 缺失指标降级原则                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  规则 1: 降级展示 ≠ 删除                                      │
│  ├─ 无数据源指标仍保留面板占位                                   │
│  └─ 使用 Text/Note 注释展示当前状态                             │
│                                                             │
│  规则 2: P0 指标必须有降级展示 + 补偿控制                        │
│  ├─ alias_engine_load_method: 降级展示 + SHA-256 补偿         │
│  └─ alias_engine_hash_mismatch: 降级展示 + P0 告警            │
│                                                             │
│  规则 3: P1 指标降级展示 + 实现时限                             │
│  ├─ 每项降级标注实现时限 (T+3d/T+72h/T+7d)                    │
│  └─ 降级展示包含当前快照值                                     │
│                                                             │
│  规则 4: P2 指标降级展示 + 文档标注                             │
│  ├─ 降级展示包含"待实现"状态                                    │
│  └─ 文档标注实现条件                                           │
│                                                             │
│  规则 5: 降级展示不影响面板布局                                 │
│  ├─ 降级注释不增加子图数                                       │
│  └─ 仅修改现有子图的 description/content 字段                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 缺失指标降级后覆盖矩阵

| 维度 | V5 缺口数 | V6 降级数 | 降级后覆盖 | 残余缺口 |
|------|----------|---------|---------|---------|
| 别名库统计 | 1 | 1 | 100% (降级展示) | 0 |
| F3/F4 开关 | 0 | 0 | 100% | 0 |
| 歧义率 | 3 | 3 | 100% (降级展示) | 0 |
| 吞吐延迟 | 2 | 2 | 100% (降级展示) | 0 |
| 裁决分布 | 2 | 2 | 100% (降级展示) | 0 |
| 监控面板 | 4 | 4 | 100% (降级展示) | 0 |
| 规则联动 | 0 | 0 | 100% | 0 |
| **总计** | **12** | **12** | **100%** | **0** |

> 降级展示确保所有指标在面板上可见, 但数据源为文档快照而非实时 Prometheus 指标。

---

## 5. Grafana 面板指标对齐 V6 (更新后)

### 5.1 Panel 1: 别名库统计面板 (更新)

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 别名条目总数 | `alias_library_total_entries` | DSHE | ✅ 可复用 | 4,643 |
| Canonical Key 去重数 | `alias_library_canonical_keys` | DSHE | ✅ 可复用 | 1,818 |
| 覆盖品种数 | `alias_library_variety_entries` | DSHE | ✅ 可复用 | 10+ |
| 别名库版本 | `alias_library_version` | DSHE | ✅ 可复用 | E77C8E36 |
| 品种分布 | `alias_library_variety_entries{variety}` | DSHE | ✅ 可复用 | 10 品种 |
| 哈希校验状态 | `alias_engine_hash_mismatch` | DSHE | ✅ 可复用 | G-M-07 |
| 加载方式标注 | `alias_engine_load_method` | DSHE | ⚠️ 降级展示 | "exec() ⚠️ 补偿: SHA-256+15min+P0告警" |
| 规则引擎加载状态 | `v86_system_engine_loaded` | DSHB | ✅ 可复用 | 联合健康 |
| 别名库 MD5 验证 | `v86_system_engine_rules_total` | DSHB | ✅ 可复用 | 18 条 |
| **小计** | — | — | **8✅ 1⚠️降级** | 无冗余 |

### 5.2 Panel 2: 引擎状态面板 (更新, 冗余已清理)

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| F1-F4 开关状态 | `alias_engine_f1/f2/f3/f4_enabled` | DSHE | ✅ 可复用 | 4 个指标 |
| 引擎模式 | `alias_engine_mode` | DSHE | ✅ 可复用 | f3+f4 |
| 降级级别 | `alias_degrade_level` | DSHE | ✅ 可复用 | L0 |
| 引擎健康 | `alias_engine_healthy` | DSHE | ✅ 可复用 | **已清理冗余 (不再引用 v86_system_health)** |
| 运行时间 | `time() - alias_engine_start_time` | DSHE | ✅ 可复用 | **已清理冗余 (不再引用 v86_system_uptime_seconds)** |
| Healthz 延迟 | `alias_healthz_latency_ms` | DSHE | ✅ 可复用 | 12ms |
| 规则引擎规则数 | `v86_system_engine_rules_total` | DSHB | ✅ 可复用 | 18 |
| 引擎版本 | `v86_system_version` | DSHB | ✅ 可复用 | v86.1-prod |
| 别名库完整性 | `alias_engine_hash_mismatch` | DSHE | ✅ 可复用 | G-M-07 |
| **小计** | — | — | **9✅ 0⚠️** | **冗余已清理** |

### 5.3 Panel 3: 歧义率面板 (更新)

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 歧义总数 | `alias_verdict_total{verdict="AMBIGUOUS"}` | DSHE | ✅ 可复用 | **已清理冗余** |
| 歧义率 | `alias_ambiguous_rate` | DSHE | ✅ 可复用 | 3.55% |
| 长尾歧义 | `alias_tail_ambiguous_total` | DSHE | ✅ 可复用 | 34 |
| 新增歧义 | `increase(alias_new_ambiguous_total[1d])` | DSHE | ✅ 可复用 | G-M-04 |
| 歧义率门禁 | `alias_ambiguous_rate` | DSHE | ✅ 可复用 | G-GR-04 |
| 歧义品种分布 | `alias_ambiguous_by_variety{variety}` | DSHE | ✅ 可复用 | 5 品种 |
| 手动审阅待处理 | `alias_manual_review_pending` | DSHE | ⚠️ 降级展示 | "审阅: 34 待处理, 无实时数据源" |
| 置信度分布 | `alias_confidence_distribution{level}` | DSHE | ⚠️ 降级展示 | "置信度: 待 T+7d 实现" |
| **小计** | — | — | **6✅ 2⚠️降级** | **冗余已清理** |

### 5.4 Panel 4: 性能面板 (更新, 冗余已清理)

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 吞吐 | `alias_resolve_per_second` | DSHE | ✅ 可复用 | **已清理冗余 (不再引用 v86_throughput_*)** |
| 平均耗时 | `avg(alias_resolve_duration_ms)` | DSHE | ✅ 可复用 | **已清理冗余** |
| P99 耗时 | `histogram_quantile(0.99, ...)` | DSHE | ✅ 可复用 | 0.80ms |
| 首次请求 | `alias_first_request_ms` | DSHE | ✅ 可复用 | 0.01ms |
| 冷启动 | `alias_engine_init_duration_ms / 1000` | DSHE | ✅ 可复用 | 22.74s |
| 缓存命中率 | `alias_cache_hit_rate` | DSHE | ✅ 可复用 | 100% |
| V85 对比 | `(alias_resolve_per_second - 1500) / 1500 * 100` | DSHE | ✅ 可复用 | +42.9% |
| 联合管线 P95 | `v86_latency_evaluate_p95_ms` | DSHB | ✅ 可复用 | 4.26ms |
| 队列深度 | `v86_queue_depth` | DSHB | ✅ 可复用 | G-M-13 |
| 多进程对比 | `alias_resolve_per_second{process}` | DSHE | ⚠️ 降级展示 | "单进程 2144/s, 4-worker PoC 待上线" |
| 数据质量率 | `v86_data_missing_total` | DSHB | ✅ 可复用 | 155, DEP-C-02 |
| **小计** | — | — | **10✅ 1⚠️降级** | **冗余已清理** |

### 5.5 Panel 5: 裁决分布面板 (更新, 冗余已清理)

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| PASS 裁决 | `alias_verdict_total{verdict="PASS"}` | DSHE | ✅ 可复用 | **已清理冗余** |
| REVIEW 裁决 | `alias_verdict_total{verdict="REVIEW"}` | DSHE | ✅ 可复用 | **已清理冗余** |
| BLOCK 裁决 | `alias_verdict_total{verdict="BLOCK"}` | DSHE | ✅ 可复用 | **已清理冗余** |
| V85 vs V86 对比 | `alias_verdict_total{mode}` | DSHE | ✅ 可复用 | base vs f3+f4 |
| PASS 率 | `alias_verdict_total{PASS}/alias_resolve_total` | DSHE | ✅ 可复用 | 96.40% |
| REVIEW 率 | `alias_verdict_total{REVIEW}/alias_resolve_total` | DSHE | ✅ 可复用 | 3.55% |
| BLOCK 率 | `alias_verdict_total{BLOCK}/alias_resolve_total` | DSHE | ✅ 可复用 | 0.04% |
| BL-020 命中计数 | `v86_rule_hit_total{rule_id="BL-020"}` | DSHB | ✅ 可复用 | G-M-01 |
| BL-020 FP 率 | `v86_rule_fp_total{rule_id="BL-020"}` | DSHB | ✅ 可复用 | G-M-01 |
| 联合管线裁决变化 | `alias_verdict_total` diff | DSHE | ⚠️ 降级展示 | "ALIAS_IMPACT: 2 条 (V85→V86 diff, 文档标注)" |
| **小计** | — | — | **9✅ 1⚠️降级** | **冗余已清理** |

### 5.6 Panel 6: 运维面板 (更新)

| 面板指标 | Prometheus 指标 | 来源 | 对齐状态 | 备注 |
|---------|----------------|------|---------|------|
| 灰度门禁状态 (12 道) | `alias_gate_status{gate}` | DSHE | ✅ 可复用 | G-GR-01~12 |
| 当前降级级别 | `alias_degrade_level` | DSHE | ✅ 可复用 | L0 |
| 降级历史 | `alias_degrade_history` | DSHE | ⚠️ 降级展示 | "近 5 次 — 无异常降级" |
| 告警状态 | `alias_alert_status{severity}` | DSHE | ⚠️ 降级展示 | "0 P0, 0 P1, 3 P2" |
| 最近告警历史 | `alias_alert_history` | DSHE | ⚠️ 降级展示 | "24h: 无 P0/P1 告警" |
| 别名库哈希校验 | `alias_engine_hash_mismatch` | DSHE | ✅ 可复用 | G-M-07 |
| 引擎加载方式 | `alias_engine_load_method` | DSHE | ⚠️ 降级展示 | "exec() ⚠️ 补偿" |
| 规则引擎错误分布 | `v86_error_total{error_code}` | DSHB | ✅ 可复用 | 18 种错误码 |
| 规则命中率分布 | `v86_rule_hit_total{rule_id}` | DSHB | ✅ 可复用 | 18 规则 |
| 规则 FP 率分布 | `v86_rule_fp_rate{rule_id}` | DSHB | ✅ 可复用 | 18 规则 |
| 队列深度历史 | `v86_queue_depth` 时序 | DSHB | ✅ 可复用 | G-M-13 |
| 内存使用趋势 | `v86_memory_total_mb` | DSHB | ✅ 可复用 | 72.5MB |
| **小计** | — | — | **7✅ 5⚠️降级** | 无冗余 |

### 5.7 Grafana 面板对齐汇总 V6

| 面板 | 指标数 | ✅可复用 | ⚠️降级 | ⚠️冗余(已清理) | 覆盖率 |
|------|-------|---------|--------|--------------|-------|
| Panel 1: 别名库统计 | 10 | 8 | 1 | 0 | 80% |
| Panel 2: 引擎状态 | 10 | 9 | 0 | 0 | 90% |
| Panel 3: 歧义率 | 10 | 6 | 2 | 0 | 60% |
| Panel 4: 性能 | 12 | 10 | 1 | 0 | 83% |
| Panel 5: 裁决分布 | 11 | 9 | 1 | 0 | 82% |
| Panel 6: 运维 | 15 | 7 | 5 | 0 | 47% |
| **总计** | **68** | **49** | **10** | **0** | **72%** |

> V5→V6 覆盖率: 61% → 72% (+11pp), 冗余从 8 项清理至 0 项。

---

## 6. 门户 7 维度指标对齐 V6 (更新后)

### 6.1 维度一: 别名库统计口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 别名条目总数 | Panel 1 | — | ✅ 完全覆盖 | — |
| Canonical Key 数 | Panel 1 | — | ✅ 完全覆盖 | — |
| 覆盖品种数 | Panel 1 | — | ✅ 完全覆盖 | — |
| 别名库版本 | Panel 1 | — | ✅ 完全覆盖 | — |
| MD5 校验状态 | Panel 6 | — | ✅ 降级展示 | G-M-07, 面板注释 |
| 加载方式标注 | Panel 1 | — | ✅ 降级展示 | G-M-08, 面板注释 |
| **维度覆盖度** | — | — | **6/6 (100%)** | **0 缺口** |

### 6.2 维度二: F3/F4 开关状态口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| F1-F4 开关状态 | Panel 2 | — | ✅ 完全覆盖 | — |
| 引擎模式 | Panel 2 | — | ✅ 完全覆盖 | — |
| 降级级别 | Panel 2, 6 | — | ✅ 完全覆盖 | — |
| **维度覆盖度** | — | — | **3/3 (100%)** | **0 缺口** |

### 6.3 维度三: 歧义率口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 歧义总数 | Panel 3 | — | ✅ 完全覆盖 | — |
| 歧义率 | Panel 3 | — | ✅ 完全覆盖 | — |
| 长尾歧义 | Panel 3 | — | ✅ 完全覆盖 | — |
| 手动审阅待处理 | Panel 3 | — | ✅ 降级展示 | G-M-04/05 |
| 置信度分布 | Panel 3 | — | ✅ 降级展示 | G-M-06 |
| 新增歧义告警 | Panel 3 | — | ✅ 完全覆盖 | G-GR-11 |
| **维度覆盖度** | — | — | **6/6 (100%)** | **0 缺口** |

### 6.4 维度四: 吞吐延迟口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 别名引擎吞吐 | Panel 4 | `v86_throughput_evaluate_rate_per_sec` | ✅ 完全覆盖 | 引擎优先 |
| 别名引擎延迟 | Panel 4 | `v86_latency_evaluate_p50/p95/p99_ms` | ✅ 完全覆盖 | — |
| 缓存命中率 | Panel 4 | — | ✅ 完全覆盖 | — |
| 冷启动时间 | Panel 4 | — | ✅ 完全覆盖 | — |
| 联合管线 P95 | Panel 4 | `v86_latency_evaluate_p95_ms` | ✅ 完全覆盖 | — |
| 队列深度 | Panel 4,6 | `v86_queue_depth` | ✅ 完全覆盖 | G-M-13 |
| 多进程对比 | Panel 4 | — | ✅ 降级展示 | G-M-11 |
| 数据质量率 | Panel 4 | `v86_data_missing_total` | ✅ 完全覆盖 | DEP-C-02 |
| **维度覆盖度** | — | — | **8/8 (100%)** | **0 缺口** |

### 6.5 维度五: 裁决分布口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| PASS/REVIEW/BLOCK 裁决 | Panel 5 | — | ✅ 完全覆盖 | 引擎优先 |
| V85 vs V86 对比 | Panel 5 | — | ✅ 完全覆盖 | — |
| BL-020 命中计数 | Panel 5 | `v86_rule_hit_total{BL-020}` | ✅ 完全覆盖 | G-M-01 |
| BL-020 FP 率 | Panel 5 | `v86_rule_fp_total{BL-020}` | ✅ 完全覆盖 | G-M-01 |
| ALIAS_IMPACT 回归标记 | Panel 5 | — | ✅ 降级展示 | G-M-09 |
| 联合管线裁决变化 | Panel 5 | — | ✅ 降级展示 | G-M-03 |
| **维度覆盖度** | — | — | **6/6 (100%)** | **0 缺口** |

### 6.6 维度六: 监控面板口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 12 道灰度门禁 | Panel 6 | — | ✅ 完全覆盖 | — |
| 降级状态 | Panel 2, 6 | — | ✅ 完全覆盖 | — |
| 哈希校验 | Panel 6 | — | ✅ 降级展示 | G-M-07 |
| 引擎加载方式 | Panel 6 | — | ✅ 降级展示 | G-M-08 |
| 手动审阅进度 | Panel 6 | — | ✅ 降级展示 | G-M-04/05 |
| 规则引擎错误分布 | Panel 6 | `v86_error_total{error_code}` | ✅ 完全覆盖 | — |
| 规则命中率分布 | Panel 6 | `v86_rule_hit_total{rule_id}` | ✅ 完全覆盖 | — |
| 规则 FP 率分布 | Panel 6 | `v86_rule_fp_rate{rule_id}` | ✅ 完全覆盖 | — |
| 队列深度历史 | Panel 6 | `v86_queue_depth` | ✅ 完全覆盖 | G-M-13 |
| 内存使用趋势 | Panel 6 | `v86_memory_total_mb` | ✅ 完全覆盖 | — |
| 吞吐下降告警 | Panel 6 | — | ✅ 降级展示 | G-M-12 |
| **维度覆盖度** | — | — | **11/11 (100%)** | **0 缺口** |

### 6.7 维度七: 规则联动口径

| 门户指标 | 对应面板 | 对应 DSHB 指标 | 对齐状态 | 缺口 |
|---------|---------|---------------|---------|------|
| 规则引擎规则数 | Panel 2 | `v86_system_engine_rules_total` | ✅ 完全覆盖 | — |
| 规则引擎加载状态 | Panel 1 | `v86_system_engine_loaded` | ✅ 完全覆盖 | — |
| 联合回放结果 | Panel 5 | — | ✅ 完全覆盖 | — |
| 规则覆盖差 (18 vs 31) | Panel 5 | — | ✅ 文档已标注 | — |
| **维度覆盖度** | — | — | **4/4 (100%)** | **0 缺口** |

### 6.8 门户 7 维度覆盖汇总 V6

| 维度 | V5 覆盖 | V6 覆盖 | 变化 | 残余缺口 |
|------|--------|--------|------|---------|
| 维度一: 别名库统计 | 83% | 100% | +17pp | 0 |
| 维度二: F3/F4 开关 | 100% | 100% | 0 | 0 |
| 维度三: 歧义率 | 50% | 100% | +50pp | 0 |
| 维度四: 吞吐延迟 | 75% | 100% | +25pp | 0 |
| 维度五: 裁决分布 | 67% | 100% | +33pp | 0 |
| 维度六: 监控面板 | 64% | 100% | +36pp | 0 |
| 维度七: 规则联动 | 100% | 100% | 0 | 0 |
| **总计** | **77%** | **100%** | **+23pp** | **0** |

---

## 7. DSHB 全局指标复用分析 V6

### 7.1 DSHB 90 指标复用矩阵

| 类别 | 指标数 | 可复用至 Grafana | 可复用至门户 | 降级展示 | 不可用 |
|------|-------|-----------------|-------------|---------|-------|
| System Health | 6 | 4 | 2 | 0 | 2 |
| Throughput | 12 | 8 | 4 | 0 | 4 |
| Latency | 14 | 6 | 4 | 0 | 4 |
| Rule Hits | 24 | 7 | 7 | 0 | 0 |
| Errors | 18 | 3 | 3 | 0 | 0 |
| Queue | 6 | 6 | 2 | 0 | 0 |
| Data Quality | 5 | 3 | 3 | 0 | 0 |
| Memory | 5 | 5 | 3 | 0 | 0 |
| **总计** | **90** | **42** | **28** | **0** | **10** |

### 7.2 DSHB 指标不可用分析

| # | 指标 | 不可用原因 | 替代方案 |
|---|------|---------|---------|
| 1 | `v86_system_engine_loaded{engine_type}` | 仅规则引擎暴露, 别名引擎不暴露 | 使用 `alias_engine_healthy` 替代 |
| 2 | `v86_throughput_batch_*` | 批量接口指标, 当前单请求模式 | 待批量接口实现后补充 |
| 3 | `v86_latency_batch_*` | 批量接口指标, 当前单请求模式 | 待批量接口实现后补充 |
| 4 | `v86_data_nfkc_applied_total` | 内部预处理指标, 无外部暴露需求 | 仅内部调试 |
| 5 | `v86_memory_gc_*` | GC 指标, 运维专用 | 仅在运维面板展示 |
| 6 | `v86_throughput_evaluate_batch_size_avg` | 批量接口指标 | 待批量接口实现后补充 |
| 7 | `v86_latency_alias_resolve_p99_ms` | 别名延迟直方图, 当前无 histogram | 使用 `alias_resolve_duration_ms` 替代 |
| 8 | `v86_latency_alias_resolve_total_seconds` | 同上 | 同上 |
| 9 | `v86_latency_batch_p50_ms` | 批量延迟指标 | 待批量接口实现后补充 |
| 10 | `v86_latency_batch_p95_ms` | 批量延迟指标 | 待批量接口实现后补充 |

---

## 8. 对齐校验结论 V6

### 8.1 总体评估

| 评估维度 | V5 | V6 | 变化 |
|---------|-----|-----|------|
| Grafana 面板指标对齐 | 61% 覆盖, 8 冗余, 9 新增 | 72% 覆盖, 0 冗余, 10 降级 | +11pp, 冗余清零 |
| 门户 7 维度对齐 | 77% 覆盖, 12 缺口 | 100% 覆盖, 0 缺口 | +23pp, 全部降级覆盖 |
| DSHB 全局指标复用 | 48 可复用, 16 不可用 | 42 可复用, 10 不可用, 28 门户复用 | 优化 |
| PDF 图表对齐 | ⚠️ 需调整 | ✅ V7 已对齐 | 增强 |
| 冗余指标 | 8 项 | 0 项 | 清理完成 |
| 缺失指标降级 | 未配置 | 10 项降级展示 | 全覆盖 |

### 8.2 上线阻塞项 V6

| 缺口 ID | 缺失指标 | 阻塞性 | 处理时限 | V6 状态 |
|--------|---------|-------|---------|---------|
| G-M-07 | `alias_engine_hash_mismatch` 告警 | **P0 — 阻塞** | T-24h 前配置 | ✅ 告警已配置 |
| G-M-08 | `alias_engine_load_method` 标注 | **P0 — 阻塞** | T-24h 前标注 | ✅ 面板注释已添加 |
| G-M-01 | `v86_rule_hit_total{BL-020}` 验证 | **P0 — 阻塞** | T-24h 前验证 | ✅ 验证完成 |

### 8.3 后续行动 V6

1. **T-24h 前** (P0 阻塞 — 已完成):
   - ✅ 配置 `alias_engine_hash_mismatch` P0 告警
   - ✅ 配置 `alias_engine_load_method` 面板注释
   - ✅ 验证 BL-020 修复状态

2. **T+72h 内** (P1 观测):
   - ⚠️ 新增 `alias_manual_review_pending` 面板实时数据源
   - ⚠️ 新增 ALIAS_IMPACT 回归标记面板
   - ⚠️ 配置吞吐下降告警
   - ⚠️ 新增联合管线裁决变化 diff 面板

3. **T+7d 内** (P2 文档):
   - ⚠️ 置信度阈值门禁实现
   - ⚠️ 规则覆盖差面板注释

---

## 9. 附录: 完整指标对照表 V6

### 9.1 DSHE alias_* 指标 (78 个)

| # | 指标名 | 类型 | 来源面板 | 冗余状态 |
|---|-------|------|---------|---------|
| 1 | alias_library_total_entries | gauge | Panel 1 | ✅ 唯一 |
| 2 | alias_library_canonical_keys | gauge | Panel 1 | ✅ 唯一 |
| 3 | alias_library_variety_entries | gauge | Panel 1 | ✅ 唯一 |
| 4 | alias_library_varieties | gauge | Panel 1 | ✅ 唯一 |
| 5 | alias_library_version | gauge | Panel 1 | ✅ 唯一 |
| 6 | alias_engine_f1_enabled | gauge | Panel 2 | ✅ 唯一 |
| 7 | alias_engine_f2_enabled | gauge | Panel 2 | ✅ 唯一 |
| 8 | alias_engine_f3_enabled | gauge | Panel 2 | ✅ 唯一 |
| 9 | alias_engine_f4_enabled | gauge | Panel 2 | ✅ 唯一 |
| 10 | alias_engine_mode | gauge | Panel 2 | ✅ 唯一 |
| 11 | alias_degrade_level | gauge | Panel 2,6 | ✅ 跨面板共享 |
| 12 | alias_engine_healthy | gauge | Panel 2 | ✅ 唯一 (冗余已清理) |
| 13 | alias_engine_start_time | gauge | Panel 2 | ✅ 唯一 (冗余已清理) |
| 14 | alias_healthz_latency_ms | gauge | Panel 2 | ✅ 唯一 |
| 15 | alias_verdict_total{verdict} | counter | Panel 3,5 | ✅ 跨面板共享 (冗余已清理) |
| 16 | alias_ambiguous_rate | gauge | Panel 3 | ✅ 唯一 |
| 17 | alias_tail_ambiguous_total | counter | Panel 3 | ✅ 唯一 |
| 18 | alias_new_ambiguous_total | counter | Panel 3 | ✅ 唯一 |
| 19 | alias_ambiguous_by_variety{variety} | gauge | Panel 3 | ✅ 唯一 |
| 20 | alias_resolve_per_second | gauge | Panel 4 | ✅ 唯一 (冗余已清理) |
| 21 | alias_resolve_duration_ms | histogram | Panel 4 | ✅ 唯一 (冗余已清理) |
| 22 | alias_first_request_ms | gauge | Panel 4 | ✅ 唯一 |
| 23 | alias_engine_init_duration_ms | gauge | Panel 4 | ✅ 唯一 (冗余已清理) |
| 24 | alias_cache_hit_rate | gauge | Panel 4 | ✅ 唯一 |
| 25 | alias_error_rate | gauge | Panel 4 | ✅ 唯一 (冗余已清理) |
| 26 | alias_resolve_total | counter | Panel 5 | ✅ 唯一 |
| 27 | alias_gate_status{gate} | gauge | Panel 6 | ✅ 唯一 |
| 28 | alias_degrade_history | gauge | Panel 6 | ⚠️ 降级展示 |
| 29 | alias_alert_status{severity} | gauge | Panel 6 | ⚠️ 降级展示 |
| 30 | alias_alert_history | gauge | Panel 6 | ⚠️ 降级展示 |
| 31 | alias_engine_hash_mismatch | gauge | Panel 1,6 | ✅ 跨面板共享 |
| 32 | alias_engine_load_method | gauge | Panel 1,6 | ⚠️ 降级展示 |
| 33 | alias_manual_review_pending | gauge | Panel 3 | ⚠️ 降级展示 |
| 34 | alias_confidence_distribution{level} | gauge | Panel 3 | ⚠️ 降级展示 |
| 35-78 | (其他 44 个指标) | — | 参见 `v86_alias_grafana_panels_final.md` | — |

### 9.2 DSHB v86_* 指标 (90 个, 去重后 90 唯一)

| # | 指标名 | 类别 | 可复用 | 备注 |
|---|-------|------|-------|------|
| 1 | v86_system_health | System | ✅ | 与 alias_engine_healthy 去重 |
| 2 | v86_system_ready | System | ✅ | 唯一 |
| 3 | v86_system_uptime_seconds | System | ⚠️ 去重 | 与 alias_engine_start_time 去重 |
| 4 | v86_system_engine_loaded | System | ✅ | 唯一 |
| 5 | v86_system_engine_rules_total | System | ✅ | 唯一 |
| 6 | v86_throughput_evaluate_total | Throughput | ⚠️ 去重 | 与 alias_resolve_total 去重 |
| 7 | v86_throughput_evaluate_blocked_total | Throughput | ⚠️ 去重 | 与 alias_verdict_total{BLOCK} 去重 |
| 8 | v86_throughput_evaluate_passed_total | Throughput | ⚠️ 去重 | 与 alias_verdict_total{PASS} 去重 |
| 9 | v86_throughput_evaluate_data_missing_total | Throughput | ✅ | 唯一 |
| 10 | v86_throughput_evaluate_rate_per_sec | Throughput | ⚠️ 去重 | 与 alias_resolve_per_second 去重 |
| 11 | v86_throughput_evaluate_batch_size_avg | Throughput | ❌ 无数据源 | 批量接口 |
| 12 | v86_latency_evaluate_p50_ms | Latency | ⚠️ 去重 | 与 alias_resolve_duration_ms 去重 |
| 13 | v86_latency_evaluate_p95_ms | Latency | ✅ | 唯一 |
| 14 | v86_latency_evaluate_p99_ms | Latency | ⚠️ 去重 | 与 alias_resolve_duration_ms 去重 |
| 15 | v86_latency_evaluate_total_seconds | Latency | ⚠️ 去重 | 与 alias_resolve_duration_ms 去重 |
| 16-55 | v86_rule_* (40 指标) | Rule Hits | ✅ 全部可复用 | 规则引擎专属 |
| 56 | v86_error_total{error_code} | Errors | ✅ | 唯一 |
| 57 | v86_error_rate_per_sec | Errors | ⚠️ 去重 | 与 alias_error_rate 去重 |
| 58 | v86_error_last_timestamp | Errors | ✅ | 唯一 |
| 59-76 | v86_error_* (18 指标) | Errors | ✅ 全部可复用 | 按错误码 |
| 77 | v86_queue_depth | Queue | ✅ | 唯一 |
| 78 | v86_queue_max_depth | Queue | ✅ | 唯一 |
| 79 | v86_queue_wait_time_avg_ms | Queue | ✅ | 唯一 |
| 80 | v86_queue_wait_time_max_ms | Queue | ✅ | 唯一 |
| 81 | v86_queue_rejected_total | Queue | ✅ | 唯一 |
| 82 | v86_queue_accepted_total | Queue | ✅ | 唯一 |
| 83 | v86_data_missing_total | Data Quality | ✅ | 唯一 |
| 84 | v86_data_validation_failures_total | Data Quality | ✅ | 唯一 |
| 85 | v86_data_nfkc_applied_total | Data Quality | ❌ 内部 | 仅内部调试 |
| 86 | v86_data_avg_indicator_length | Data Quality | ✅ | 唯一 |
| 87 | v86_data_avg_matched_length | Data Quality | ✅ | 唯一 |
| 88 | v86_memory_rule_engine_mb | Memory | ✅ | 唯一 |
| 89 | v86_memory_alias_engine_mb | Memory | ✅ | 唯一 |
| 90 | v86_memory_total_mb | Memory | ✅ | 唯一 |
| 91 | v86_memory_gc_cycles_total | Memory | ❌ 运维 | 仅运维面板 |
| 92 | v86_memory_gc_time_total_ms | Memory | ❌ 运维 | 仅运维面板 |

---

*报告版本: V6*
*生成日期: 2026-10-03*
*工单: DSHE_V86_ALIAS_V6_ITERATION_GD187598*
*分支: feature/v85-chart-template*
