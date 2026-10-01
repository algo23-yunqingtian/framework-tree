# V86 别名引擎监控指标规范

> 任务: `DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN` · T2.5
> 分支: `feature/v85-chart-template`
> 对齐后端异步任务 API: E commit `bcd64dd`

---

## 1. 监控体系总览

### 1.1 指标分类

```
┌─────────────────────────────────────────────────────────────┐
│                    V86 Alias Engine Metrics                   │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│  系统层  │  引擎层  │  业务层  │  性能层  │  可用性层      │
│  System  │  Engine  │  Business│  Perf    │  Availability  │
├──────────┼──────────┼──────────┼──────────┼────────────────┤
│ CPU      │ Init Time│ Verdict  │ Latency  │ Error Rate     │
│ Memory   │ Resolve  │ Dist     │ Throughput│ Uptime         │
│ Disk I/O │ Stats    │ F1/F2    │ Cache Hit │ Degrade Level  │
│ Network  │ F3/F4    │ Stats    │ Rate      │ Pod Status     │
└──────────┴──────────┴──────────┴──────────┴────────────────┘
```

### 1.2 数据源

| 数据源 | 采集方式 | 采集频率 | 存储 |
|---|---|---|---|
| Prometheus Metrics | `/metrics` endpoint | 15s | Prometheus TSDB |
| Application Logs | JSON structured logs | 实时 | Loki |
| Health Check | `/healthz` endpoint | 10s | Kubernetes |
| Task API Events | 后端异步任务回调 | 实时 | PostgreSQL |
| Trace (OpenTelemetry) | SDK instrumentation | 实时 | Jaeger |

---

## 2. 核心指标定义

### 2.1 解析吞吐指标

| 指标名 | 类型 | 单位 | 说明 | 阈值 |
|---|---|---|---|---|
| `alias_resolve_total` | Counter | count | 总解析请求数 | - |
| `alias_resolve_per_second` | Gauge | req/s | 实时解析吞吐 | 目标 ≥ 1500/s |
| `alias_resolve_batch_size` | Histogram | count | 批量解析大小分布 | P50=10, P99=100 |
| `alias_resolve_throughput_p50` | Histogram | req/s | 吞吐 P50 | ≥ 1500/s |
| `alias_resolve_throughput_p99` | Histogram | req/s | 吞吐 P99 | ≥ 800/s |

**Prometheus 格式**:
```
alias_resolve_total{mode="f3+f4", variety="LI"} 123456
alias_resolve_per_second{mode="f3+f4"} 1850.0
```

**埋点位置**: `V86AliasEngine.decide()` 方法出口

---

### 2.2 冷/热启动耗时

| 指标名 | 类型 | 单位 | 说明 | 阈值 |
|---|---|---|---|---|
| `alias_engine_init_duration_ms` | Histogram | ms | 引擎冷启动耗时 | P99 ≤ 30,000ms |
| `alias_engine_init_duration_p50` | Histogram | ms | 冷启动 P50 | ≤ 20,000ms |
| `alias_engine_init_duration_p99` | Histogram | ms | 冷启动 P99 | ≤ 30,000ms |
| `alias_first_request_duration_ms` | Histogram | ms | 首次请求耗时 (预热后) | P99 ≤ 50ms |
| `alias_warmup_duration_ms` | Histogram | ms | 预热耗时 | ≤ 5,000ms |
| `alias_warmup_samples_loaded` | Gauge | count | 预热样本数 | ≥ 18 |
| `alias_cache_persist_duration_ms` | Histogram | ms | 缓存持久化耗时 | ≤ 1,000ms |

**Prometheus 格式**:
```
alias_engine_init_duration_ms{mode="f3+f4"} 22000.0
alias_engine_init_duration_ms_bucket{le="30000", mode="f3+f4"} 1
alias_first_request_duration_ms{mode="f3+f4"} 0.01
alias_warmup_samples_loaded 18
```

**埋点位置**:
- `V86AliasEngine.__init__()`: init_duration
- `alias_engine_warmup_optimize.py --warmup`: warmup_duration
- `resolve_cached()`: first_request_duration

---

### 2.3 缓存命中率

| 指标名 | 类型 | 单位 | 说明 | 阈值 |
|---|---|---|---|---|
| `alias_cache_lookup_total` | Counter | count | 缓存查询总数 | - |
| `alias_cache_hit_total` | Counter | count | 缓存命中数 | - |
| `alias_cache_miss_total` | Counter | count | 缓存未命中数 | - |
| `alias_cache_hit_rate` | Gauge | % | 缓存命中率 | ≥ 85% |
| `alias_cache_size` | Gauge | count | 当前缓存条目数 | ≤ 1024 |
| `alias_cache_eviction_total` | Counter | count | 缓存驱逐次数 | - |
| `alias_cache_persist_success_total` | Counter | count | 缓存持久化成功数 | - |
| `alias_cache_persist_fail_total` | Counter | count | 缓存持久化失败数 | - |

**Prometheus 格式**:
```
alias_cache_lookup_total{mode="f3+f4"} 50000
alias_cache_hit_total{mode="f3+f4"} 49500
alias_cache_miss_total{mode="f3+f4"} 500
alias_cache_hit_rate 0.99
alias_cache_size 956
alias_cache_eviction_total 44
```

**计算方式**:
```python
hit_rate = hit_total / lookup_total if lookup_total > 0 else 0.0
```

**埋点位置**: `alias_engine_warmup_optimize.py` 的 `resolve_cached()` 方法

---

### 2.4 歧义数量指标

| 指标名 | 类型 | 单位 | 说明 | 阈值 |
|---|---|---|---|---|
| `alias_resolve_state_total` | Counter | count | 按解析状态计数 | - |
| `alias_resolve_state_total{state="UNIQUE"}` | Counter | count | 唯一解析数 | - |
| `alias_resolve_state_total{state="AMBIGUOUS"}` | Counter | count | 歧义解析数 | ≤ 5% of total |
| `alias_resolve_state_total{state="NO_MATCH"}` | Counter | count | 无匹配数 | - |
| `alias_resolve_state_total{state="UNREGISTERED"}` | Counter | count | 未注册数 | ≤ 1% |
| `alias_ambiguous_rate` | Gauge | % | 歧义率 | ≤ 5% |
| `alias_tail_ambiguous_total` | Counter | count | 长尾歧义累计数 | 新增 ≤ 0/天 |
| `alias_ambiguous_max_canonicals` | Histogram | count | 歧义最大 canonical 数 | P99 ≤ 10 |

**Prometheus 格式**:
```
alias_resolve_state_total{mode="f3+f4", state="UNIQUE"} 2713
alias_resolve_state_total{mode="f3+f4", state="AMBIGUOUS"} 165
alias_resolve_state_total{mode="f3+f4", state="NO_MATCH"} 1751
alias_resolve_state_total{mode="f3+f4", state="UNREGISTERED"} 14
alias_ambiguous_rate{mode="f3+f4"} 0.0355
alias_tail_ambiguous_total 34
```

**埋点位置**: `V86AliasEngine.resolve()` 方法

---

### 2.5 错误码分布

| 错误码 | 说明 | 严重级别 | 处理动作 |
|---|---|---|---|
| `E000` | 正常 | INFO | - |
| `E001` | 空输入 | INFO | 阻断 |
| `E002` | 未注册别名 | WARN | 返回 NO_MATCH |
| `E003` | 歧义解析 | WARN | 返回 AMBIGUOUS, 需人工复核 |
| `E004` | 黑名单阻断 | INFO | 正常阻断 |
| `E005` | 品种锚点冲突 | INFO | 正常阻断 |
| `E006` | 度量词冲突 | INFO | 正常阻断 |
| `E007` | 低于阈值 | INFO | 正常阻断 |
| `E100` | 引擎初始化失败 | ERROR | 降级 + 告警 |
| `E101` | 解析超时 | ERROR | 降级 + 告警 |
| `E102` | 内存不足 | CRITICAL | 降级 L3 + 告警 |
| `E103` | 缓存持久化失败 | WARN | 记录日志, 不降级 |
| `E104` | 引擎崩溃 | CRITICAL | K8s 重启 + 降级 L3 |
| `E200` | 任务 API 超时 | ERROR | 重试 3 次 |
| `E201` | 任务幂等冲突 | WARN | 返回缓存结果 |

**指标定义**:
```
alias_error_total{code="E001", mode="f3+f4"} 123
alias_error_rate{code="E001", mode="f3+f4"} 0.001
```

**埋点位置**: `V86AliasEngine.decide()` 方法, 根据 `verdict` 和 `reason` 映射错误码

---

### 2.6 解析耗时分布

| 指标名 | 类型 | 单位 | 说明 | 阈值 |
|---|---|---|---|---|
| `alias_resolve_duration_ms` | Histogram | ms | 单条裁决耗时 | P50 ≤ 0.5, P99 ≤ 5 |
| `alias_resolve_duration_p50` | Histogram | ms | P50 | ≤ 0.5ms |
| `alias_resolve_duration_p95` | Histogram | ms | P95 | ≤ 2ms |
| `alias_resolve_duration_p99` | Histogram | ms | P99 | ≤ 5ms |
| `alias_resolve_duration_max` | Histogram | ms | 最大值 | ≤ 50ms |
| `alias_decide_duration_ms` | Histogram | ms | decide() 总耗时 (含 resolve) | P99 ≤ 50ms |

**Prometheus 格式**:
```
alias_resolve_duration_ms_bucket{le="0.5", mode="f3+f4"} 85%
alias_resolve_duration_ms_bucket{le="2.0", mode="f3+f4"} 95%
alias_resolve_duration_ms_bucket{le="5.0", mode="f3+f4"} 99%
alias_resolve_duration_ms_bucket{le="50.0", mode="f3+f4"} 100%
```

**埋点位置**: `V86AliasEngine.decide()` 方法 (`elapsed_ms` 字段)

---

### 2.7 F1/F2/F3/F4 修复档指标

| 指标名 | 类型 | 单位 | 说明 |
|---|---|---|---|
| `alias_f1_guard_hit_total` | Counter | count | F1 异常兜底触发次数 |
| `alias_f1_alias_miss_total` | Counter | count | F1 别名未命中次数 |
| `alias_f2_unique_total` | Counter | count | F2 唯一解析次数 |
| `alias_f2_ambiguous_total` | Counter | count | F2 歧义解析次数 |
| `alias_f2_no_match_total` | Counter | count | F2 无匹配次数 |
| `alias_f2_unregistered_total` | Counter | count | F2 未注册次数 |
| `alias_f3_r05_trigger_total` | Counter | count | F3 R-05 黑名单触发次数 |
| `alias_f3_r01_trigger_total` | Counter | count | F3 R-01 品种锚点触发次数 |
| `alias_f4_f4a_suppress_total` | Counter | count | F4a 子串包含抑制次数 |
| `alias_f4_f4b_suppress_total` | Counter | count | F4b 复合短语抑制次数 |
| `alias_f4_total_suppress_total` | Counter | count | F4 总抑制次数 |

**Prometheus 格式**:
```
alias_f1_guard_hit_total 465
alias_f2_unique_total 2713
alias_f2_ambiguous_total 165
alias_f3_r05_trigger_total 2
alias_f4_f4a_suppress_total 132
alias_f4_f4b_suppress_total 46
alias_f4_total_suppress_total 51
```

---

## 3. 裁决分布指标

### 3.1 三态裁决计数

```
alias_verdict_total{verdict="PASS", mode="f3+f4"} 4476
alias_verdict_total{verdict="REVIEW", mode="f3+f4"} 165
alias_verdict_total{verdict="BLOCK", mode="f3+f4"} 2
```

### 3.2 裁决理由分布

```
alias_verdict_reason_total{reason="alias_exact", mode="f3+f4"} 4476
alias_verdict_reason_total{reason="alias_ambiguous_multi_canonical", mode="f3+f4"} 165
alias_verdict_reason_total{reason="blacklist_precheck", mode="f3+f4"} 2
alias_verdict_reason_total{reason="below_threshold", mode="f3+f4"} 0
```

### 3.3 按品种分类

```
alias_resolve_by_variety{variety="LI", mode="f3+f4"} 371
alias_resolve_by_variety{variety="NI", mode="f3+f4"} 671
alias_resolve_by_variety{variety="SI", mode="f3+f4"} 401
alias_resolve_by_variety{variety="SN", mode="f3+f4"} 396
alias_resolve_by_variety{variety="ZN", mode="f3+f4"} 354
alias_resolve_by_variety{variety="AL", mode="f3+f4"} 198
alias_resolve_by_variety{variety="PB", mode="f3+f4"} 159
alias_resolve_by_variety{variety="CU", mode="f3+f4"} 150
```

---

## 4. 后端埋点规范对齐

### 4.1 异步任务 API 对齐

后端异步任务 API (E commit `bcd64dd`) 定义:

```json
{
  "task_type": "dshe_alias_resolve",
  "payload": {
    "alias_names": ["碳酸锂工厂库存天数", "电解铜库存"],
    "engine_variant": "f3+f4",
    "version_tag": "v86.0.0"
  },
  "idempotency_key": "SHA256(payload)[:32]",
  "ttl_hours": 24
}
```

### 4.2 任务回调指标

```
alias_task_total{task_type="dshe_alias_resolve"} 10000
alias_task_success_total{task_type="dshe_alias_resolve"} 9950
alias_task_fail_total{task_type="dshe_alias_resolve"} 50
alias_task_duration_ms{task_type="dshe_alias_resolve"} 120.0
alias_task_cache_hit_total{task_type="dshe_alias_resolve"} 8000
alias_task_idempotent_hit_total{task_type="dshe_alias_resolve"} 500
```

### 4.3 埋点映射表

| 引擎方法 | 指标 | 后端字段 |
|---|---|---|
| `V86AliasEngine.decide()` | `alias_resolve_duration_ms` | `response.elapsed_ms` |
| `V86AliasEngine.resolve()` | `alias_resolve_state_total` | `response.canonical_state` |
| `V86AliasEngine.resolve_safe()` | `alias_f1_alias_miss_total` | `response.guard_hit` |
| `smoke_test()` | `alias_smoke_pass_total` | `response.smoke_status` |
| `alias_task_adapter.submit()` | `alias_task_total` | `task.status` |
| `alias_task_adapter.poll()` | `alias_task_duration_ms` | `task.elapsed_ms` |

---

## 5. Grafana 仪表盘配置

### 5.1 Dashboard JSON 结构

```json
{
  "title": "V86 Alias Engine - Production Dashboard",
  "tags": ["v86", "alias", "production"],
  "panels": [
    {
      "title": "Resolution Throughput (req/s)",
      "targets": [{
        "expr": "rate(alias_resolve_total[5m])",
        "legendFormat": "{{mode}}"
      }]
    },
    {
      "title": "Latency P50/P99 (ms)",
      "targets": [
        {"expr": "histogram_quantile(0.50, rate(alias_resolve_duration_ms_bucket[5m]))", "legendFormat": "P50"},
        {"expr": "histogram_quantile(0.99, rate(alias_resolve_duration_ms_bucket[5m]))", "legendFormat": "P99"}
      ]
    },
    {
      "title": "Cache Hit Rate (%)",
      "targets": [{
        "expr": "alias_cache_hit_rate * 100",
        "legendFormat": "{{mode}}"
      }]
    },
    {
      "title": "Verdict Distribution",
      "type": "piechart",
      "targets": [
        {"expr": "sum by (verdict) (alias_verdict_total)", "legendFormat": "{{verdict}}"}
      ]
    },
    {
      "title": "Error Rate (%)",
      "targets": [{
        "expr": "sum(rate(alias_error_total[5m])) / sum(rate(alias_resolve_total[5m])) * 100",
        "legendFormat": "Error Rate"
      }]
    },
    {
      "title": "Ambiguity Rate (%)",
      "targets": [{
        "expr": "alias_ambiguous_rate * 100",
        "legendFormat": "{{mode}}"
      }]
    },
    {
      "title": "Engine Mode & Degrade Level",
      "type": "stat",
      "targets": [
        {"expr": "alias_engine_mode", "legendFormat": "Mode"},
        {"expr": "alias_degrade_level", "legendFormat": "Degrade"}
      ]
    }
  ]
}
```

### 5.2 告警规则 (Prometheus)

```yaml
groups:
  - name: v86-alias-alerts
    rules:
      - alert: AliasEngineHighErrorRate
        expr: sum(rate(alias_error_total[5m])) / sum(rate(alias_resolve_total[5m])) > 0.001
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Alias engine error rate > 0.1%"
          description: "Error rate {{ $value | humanizePercentage }} exceeds threshold"

      - alert: AliasEngineHighLatency
        expr: histogram_quantile(0.99, rate(alias_resolve_duration_ms_bucket[5m])) > 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alias engine P99 latency > 50ms"
          description: "P99 latency {{ $value | humanizeDuration }} exceeds threshold"

      - alert: AliasEngineHighAmbiguity
        expr: alias_ambiguous_rate > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Alias engine ambiguity rate > 5%"
          description: "Ambiguity rate {{ $value | humanizePercentage }} exceeds threshold"

      - alert: AliasEngineLowCacheHitRate
        expr: alias_cache_hit_rate < 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alias cache hit rate < 85%"
          description: "Cache hit rate {{ $value | humanizePercentage }} below threshold"

      - alert: AliasEngineHighMemory
        expr: process_resident_memory_bytes{container="v86-alias"} > 512 * 1024 * 1024
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Alias engine memory > 512MB"
          description: "Memory usage {{ $value | humanize1024 }} exceeds limit"

      - alert: AliasEngineDown
        expr: up{job="v86-alias"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Alias engine pod down"
          description: "Engine pod {{ $labels.pod }} is not responding"
```

---

## 6. 日志规范

### 6.1 结构化日志格式

```json
{
  "timestamp": "2026-10-02T01:20:45.123Z",
  "level": "INFO",
  "service": "v86-alias-engine",
  "version": "v86.0.0",
  "mode": "f3+f4",
  "request_id": "req-abc123",
  "event": "resolve",
  "alias_name": "碳酸锂工厂库存天数",
  "canonical_state": "UNIQUE",
  "canonical_count": 1,
  "verdict": "PASS",
  "reason": "alias_exact",
  "elapsed_ms": 0.01,
  "cache_hit": true,
  "f4_suppressed": 0
}
```

### 6.2 日志级别

| 级别 | 条件 | 示例 |
|---|---|---|
| DEBUG | 调试信息 | 缓存查询详情 |
| INFO | 正常操作 | 解析成功, 裁决结果 |
| WARN | 可恢复异常 | 歧义解析, 缓存未命中 |
| ERROR | 需关注异常 | 解析超时, 任务失败 |
| CRITICAL | 系统故障 | 引擎崩溃, 内存不足 |

---

## 7. 性能基线

### 7.1 回放实测基线

| 指标 | 实测值 | 目标 | 状态 |
|---|---|---|---|
| 解析吞吐 | 2144 entries/s | ≥ 1500/s | ✅ 达标 |
| 平均单条耗时 | 0.143ms | ≤ 0.5ms | ✅ 达标 |
| 引擎冷启动 | 22,000ms | ≤ 30,000ms | ✅ 达标 |
| 首次请求 (预热后) | 0.01ms | ≤ 50ms | ✅ 达标 |
| 缓存命中率 | 100% | ≥ 85% | ✅ 达标 |
| PASS 率 | 96.40% | ≥ 95% | ✅ 达标 |
| 歧义率 | 3.55% | ≤ 5% | ✅ 达标 |
| 内存占用 | 128MB | ≤ 512MB | ✅ 达标 |

### 7.2 容量规划

| 场景 | QPS | 内存 | CPU | 磁盘 |
|---|---|---|---|---|
| 低负载 | 500/s | 64MB | 0.1 core | 10MB |
| 中负载 | 1500/s | 128MB | 0.3 core | 50MB |
| 高负载 | 2000/s | 256MB | 0.5 core | 100MB |
| 极限 | 5000/s | 512MB | 1 core | 200MB |

---

## 8. 约束合规

| 约束 | 状态 |
|---|---|
| 不调用 zhiji API | ✅ TRUE |
| 不修改 V85 冻结数据 | ✅ TRUE |
| 不覆盖 V85 交付物 | ✅ TRUE |
| 分支锁定 feature/v85-chart-template | ✅ TRUE |
