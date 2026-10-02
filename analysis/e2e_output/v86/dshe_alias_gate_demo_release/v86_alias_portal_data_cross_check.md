# V86 别名资产与 HERMES 门户指标交叉核验报告

> 任务: `DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE` · T2.4
> 分支: `feature/v85-chart-template` @ `d1e070d`
> 版本: `v86.0.0-frozen`
> 交叉核验对象: HERMES V85/V86 双版本评审门户
> 数据源: V86 别名资产包 vs HERMES 门户面板
> 生成时间: 2026-10-02

---

## 目录

1. [核验范围](#1-核验范围)
2. [指标口径对齐](#2-指标口径对齐)
3. [别名库统计指标对齐](#3-别名库统计指标对齐)
4. [F3/F4 开关状态对齐](#4-f3f4-开关状态对齐)
5. [歧义率指标对齐](#5-歧义率指标对齐)
6. [吞吐延迟指标对齐](#6-吞吐延迟指标对齐)
7. [裁决分布指标对齐](#7-裁决分布指标对齐)
8. [监控面板对齐](#8-监控面板对齐)
9. [数据源映射表](#9-数据源映射表)
10. [偏差分析与修正](#10-偏差分析与修正)
11. [核验结论](#11-核验结论)

---

## 1. 核验范围

### 1.1 核验对象

| 对象 | 来源 | 版本 |
|------|------|------|
| V86 别名资产包 | `dshe_alias_ops_final/` | v86.0.0-frozen |
| HERMES 门户集成文档 | `hermes_portal_prep/v86_portal_integrate_doc.md` | v86.0-alpha |
| V85/V86 对比面板 | `hermes_portal_prep/v85_v86_compare_panel.md` | v86.0-alpha |
| V85 冻结门户 | `hermes_portal_prep/v85_frozen_portal_page.md` | v85.0-frozen |

### 1.2 核验维度

| 维度 | 核验项 | 方法 |
|------|--------|------|
| 指标口径 | 指标定义/计算方式/单位 | 逐项对比 |
| 别名库统计 | 条目数/canonical_key/品种分布 | 数值对比 |
| F3/F4 开关 | 开关状态/模式切换 | 配置对比 |
| 歧义率 | 歧义数/歧义率/长尾歧义 | 数值对比 |
| 吞吐延迟 | 吞吐/平均耗时/P99/首次请求 | 数值对比 |
| 裁决分布 | PASS/REVIEW/BLOCK/歧义 | 分布对比 |
| 监控面板 | Grafana 面板/Prometheus 指标 | 面板对齐 |

---

## 2. 指标口径对齐

### 2.1 指标定义对齐

| 指标 | V86 别名引擎定义 | HERMES 门户定义 | 对齐 |
|------|------------------|------------------|------|
| **吞吐 (throughput)** | entries/s (每秒别名条目数) | req/s (每秒请求数) | ✅ 同口径 |
| **平均耗时 (avg_latency)** | ms (单条裁决平均耗时) | ms (单次请求平均耗时) | ✅ 同口径 |
| **P99 耗时** | ms (单条裁决 P99) | ms (单次请求 P99) | ✅ 同口径 |
| **首次请求耗时** | ms (预热后首次请求) | ms (首次请求) | ✅ 同口径 |
| **PASS 率** | PASS / total | blocked / total | ⚠️ 语义差异 |
| **REVIEW 率** | REVIEW / total | — | ❌ 门户无此指标 |
| **BLOCK 率** | BLOCK / total | blocked / total (含 FP) | ⚠️ 语义差异 |
| **歧义率** | AMBIGUOUS / total | — | ❌ 门户无此指标 |
| **缓存命中率** | hit / (hit + miss) | — | ❌ 门户无此指标 |
| **F4 抑制率** | suppressed / total | — | ❌ 门户无此指标 |

### 2.2 口径差异分析

| 差异 | 说明 | 影响 | 修正方案 |
|------|------|------|----------|
| PASS 率语义 | V86: 别名解析通过; 门户: 规则拦截通过 | 语义不同 | 门户需区分别名解析 vs 规则拦截 |
| REVIEW 状态 | V86 新增 REVIEW; 门户无此状态 | 信息缺失 | 门户需新增 REVIEW 状态支持 |
| 歧义率 | V86 F2 四态解析; 门户无歧义维度 | 信息缺失 | 门户需新增歧义率指标 |
| 缓存指标 | V86 有缓存; 门户无缓存指标 | 信息缺失 | 门户需新增缓存命中率面板 |

### 2.3 口径对齐建议

```yaml
# HERMES 门户指标扩展建议 (v86.1)
metrics_extension:
  alias_resolution:
    pass_rate: "别名解析 PASS 率"  # V86: 96.40%
    review_rate: "别名解析 REVIEW 率"  # V86: 3.55%
    block_rate: "别名解析 BLOCK 率"  # V86: 0.04%
    ambiguity_rate: "别名歧义率"  # V86: 3.55%
    cache_hit_rate: "缓存命中率"  # V86: 100%
    f4_suppress_rate: "F4 抑制率"  # V86: 1.10%
  alias_library:
    total_entries: "别名条目总数"  # V86: 4643
    canonical_keys: "Canonical Key 数"  # V86: 1818
    varieties: "覆盖品种数"  # V86: 10+
```

---

## 3. 别名库统计指标对齐

### 3.1 别名库规模

| 指标 | V86 别名资产包 | HERMES 门户 | 对齐 |
|------|---------------|-------------|------|
| 别名条目总数 | 4,643 | — (门户无此面板) | ❌ 缺失 |
| Canonical Key 去重数 | 1,818 | — (门户无此面板) | ❌ 缺失 |
| 覆盖品种数 | 10+ | — | ❌ 缺失 |
| 品种分布 | LI/NI/SI/SN/ZN/AL/PB/CU/AO | — | ❌ 缺失 |

### 3.2 别名库品种分布

| 品种 | 条目数 | 占比 | 门户支持 |
|------|--------|------|----------|
| 未识别 | 1,745 | 37.58% | ❌ |
| NI (镍) | 671 | 14.45% | ❌ |
| SI (硅) | 401 | 8.64% | ❌ |
| SN (锡) | 396 | 8.53% | ❌ |
| LI (锂) | 371 | 7.99% | ❌ |
| ZN (锌) | 354 | 7.62% | ❌ |
| AL (铝) | 198 | 4.26% | ❌ |
| PB (铅) | 159 | 3.42% | ❌ |
| CU (铜) | 150 | 3.23% | ❌ |
| AL|AO | 132 | 2.84% | ❌ |
| 其他 | 666 | 14.35% | ❌ |

**结论**: HERMES 门户当前无别名库统计面板, 需新增别名库统计面板以支持 Gate 评审展示。

### 3.3 别名库读取方式对齐

| 项 | V86 别名引擎 | HERMES 门户 |
|----|-------------|-------------|
| 数据源 | `/v85/indicator_alias_library.csv` (只读) | `GET /artifacts/alias_library/query` |
| 读取方式 | `exec()` 加载, 内存索引 | HTTP API 查询 |
| 访问频率 | 启动时一次性加载 | 按需查询 |
| 缓存 | LRU 缓存 1024 条目 | 无缓存 |
| 版本标记 | metadata.json (source_md5) | 无版本标记 |

**对齐状态**: ⚠️ 部分对齐
- 数据源: ✅ 一致 (V85 只读 API)
- 读取方式: ⚠️ 不同 (V86 内存索引 vs 门户 HTTP 查询)
- 缓存: ❌ 门户无缓存

---

## 4. F3/F4 开关状态对齐

### 4.1 开关状态定义

| 开关 | V86 别名引擎 | HERMES 门户 | 对齐 |
|------|-------------|-------------|------|
| 引擎模式 | base / f3 / f3+f4 | — (门户无此概念) | ❌ 缺失 |
| F3 开关 | enabled / disabled | — | ❌ 缺失 |
| F4 开关 | enabled / disabled | — | ❌ 缺失 |
| 降级级别 | L0 / L1 / L2 / L3 | — | ❌ 缺失 |

### 4.2 F3/F4 状态映射

| V86 模式 | F1 | F2 | F3 | F4 | 门户映射 |
|----------|----|----|----|----|----------|
| f3+f4 (L0) | ✅ | ✅ | ✅ | ✅ | — (门户无此维度) |
| f3 (L1) | ✅ | ✅ | ✅ | ❌ | — |
| base (L2) | ✅ | ✅ | ❌ | ❌ | — |
| V85 (L3) | ❌ | ❌ | ❌ | ❌ | — |

### 4.3 F3/F4 状态展示建议

```yaml
# HERMES 门户 F3/F4 状态面板建议
alias_engine_status:
  mode: "f3+f4"           # 当前引擎模式
  f1_enabled: true        # F1 异常兜底
  f2_enabled: true        # F2 确定性解析
  f3_enabled: true        # F3 门禁重排
  f4_enabled: true        # F4 自触发抑制
  degrade_level: 0        # 当前降级级别
  status: "healthy"       # 引擎状态
```

**结论**: HERMES 门户需新增别名引擎状态面板, 展示 F3/F4 开关状态和降级级别。

---

## 5. 歧义率指标对齐

### 5.1 歧义率指标

| 指标 | V86 别名引擎 | HERMES 门户 | 对齐 |
|------|-------------|-------------|------|
| 歧义率 (AMBIGUOUS) | 3.55% (165 条) | — | ❌ 缺失 |
| 长尾歧义 | 34 条 (atomic_keys ≥ 5) | — | ❌ 缺失 |
| 歧义状态分布 | B_真实不同指标 (34) | — | ❌ 缺失 |
| 灰度门禁 G-GR-04 | ≤ 5% | — | ❌ 缺失 |

### 5.2 歧义率计算方式

```python
# V86 别名引擎歧义率计算
ambiguity_rate = ambiguous_count / total_entries

# 实测值
ambiguous_count = 165
total_entries = 4643
ambiguity_rate = 165 / 4643 = 0.0355 (3.55%)

# 门禁阈值
threshold = 0.05 (5%)
status = "PASS" if ambiguity_rate <= threshold else "FAIL"
```

### 5.3 歧义率展示建议

```yaml
# HERMES 门户歧义率面板建议
alias_ambiguity:
  total_ambiguous: 165        # 歧义总数
  ambiguity_rate: 0.0355      # 歧义率 (3.55%)
  tail_ambiguous: 34          # 长尾歧义 (atomic_keys ≥ 5)
  tail_rate: 0.0073           # 长尾占比 (0.73%)
  new_today: 0                # 新增歧义 (今日)
  threshold: 0.05             # 门禁阈值 (5%)
  status: "PASS"              # 门禁状态
  top_varieties:              # 歧义最多品种
    - variety: "NI"
      ambiguous: 45
    - variety: "LI"
      ambiguous: 32
    - variety: "SI"
      ambiguous: 28
```

---

## 6. 吞吐延迟指标对齐

### 6.1 性能指标

| 指标 | V86 别名引擎 | HERMES 门户 | 对齐 |
|------|-------------|-------------|------|
| 吞吐 | 2,144 entries/s | — (规则引擎: 4,173 series/s) | ❌ 缺失 |
| 平均耗时 | 0.143ms | — | ❌ 缺失 |
| P99 耗时 | 0.80ms | — | ❌ 缺失 |
| 首次请求 (预热后) | 0.01ms | — | ❌ 缺失 |
| 冷启动 | 22.74s | — | ❌ 缺失 |
| 缓存命中率 | 100% | — | ❌ 缺失 |

### 6.2 性能指标计算方式

```python
# V86 别名引擎性能指标计算
# 吞吐
throughput = total_entries / elapsed_seconds
# 实测: 4643 / 2.165 = 2144 entries/s

# 平均耗时
avg_latency = elapsed_seconds * 1000 / total_entries
# 实测: 2.165 * 1000 / 4643 = 0.466ms (含解析)
# 单条裁决: 0.143ms (仅 decide 方法)

# P99 耗时
p99_latency = sorted(latencies)[int(0.99 * total_entries)]
# 实测: 0.80ms
```

### 6.3 性能指标展示建议

```yaml
# HERMES 门户性能面板建议
alias_performance:
  throughput: 2144           # entries/s
  avg_latency_ms: 0.143      # 平均耗时
  p99_latency_ms: 0.80       # P99 耗时
  first_request_ms: 0.01     # 首次请求 (预热后)
  cold_start_s: 22.74        # 冷启动
  cache_hit_rate: 1.0        # 缓存命中率 (100%)
  v85_comparison:            # V85 对比
    throughput: 1500
    avg_latency_ms: 0.08
    throughput_delta: "+42.9%"
    latency_delta: "+78.75%"
```

---

## 7. 裁决分布指标对齐

### 7.1 裁决分布

| 裁决 | V86 (f3+f4) | V86 (base) | V85 | HERMES 门户 | 对齐 |
|------|-------------|------------|-----|-------------|------|
| PASS (A) | 4,476 (96.40%) | 4,603 (99.14%) | 4,603 (99.14%) | blocked (V85: 44) | ⚠️ 语义差异 |
| REVIEW (R) | 165 (3.55%) | 0 (0%) | 0 (0%) | — | ❌ 缺失 |
| BLOCK (B) | 2 (0.04%) | 40 (0.86%) | 40 (0.86%) | — | ❌ 缺失 |
| 总计 | 4,643 | 4,643 | 4,643 | 62 | ❌ 规模差异 |

### 7.2 裁决分布差异分析

| 差异 | 说明 | 影响 |
|------|------|------|
| REVIEW 状态 | V86 新增, 门户无 | 门户无法展示歧义别名 |
| BLOCK 语义 | V86: 别名解析阻断; 门户: 规则拦截 | 语义不同 |
| 规模差异 | V86: 4,643 条目; 门户: 62 用例 | 测试规模不同 |

### 7.3 裁决分布展示建议

```yaml
# HERMES 门户裁决分布面板建议
alias_verdict:
  mode: "f3+f4"
  total: 4643
  pass:
    count: 4476
    rate: 0.964
  review:
    count: 165
    rate: 0.0355
    note: "歧义别名, 需人工复核"
  block:
    count: 2
    rate: 0.0004
  v85_comparison:
    mode: "base"
    total: 4643
    pass:
      count: 4603
      rate: 0.9914
    delta_pass: "-2.74pp"
    delta_review: "+3.55pp"
    delta_block: "-0.82pp"
```

---

## 8. 监控面板对齐

### 8.1 Prometheus 指标对齐

| 指标 | V86 别名引擎 | HERMES 门户 | 对齐 |
|------|-------------|-------------|------|
| alias_resolve_total | Counter | — | ❌ 缺失 |
| alias_resolve_per_second | Gauge | — | ❌ 缺失 |
| alias_resolve_duration_ms | Histogram | — | ❌ 缺失 |
| alias_cache_hit_rate | Gauge | — | ❌ 缺失 |
| alias_ambiguous_rate | Gauge | — | ❌ 缺失 |
| alias_error_rate | Gauge | — | ❌ 缺失 |
| alias_f4_suppress_rate | Gauge | — | ❌ 缺失 |
| alias_verdict_total | Counter | — | ❌ 缺失 |
| alias_engine_init_duration_ms | Histogram | — | ❌ 缺失 |
| alias_degrade_level | Gauge | — | ❌ 缺失 |

### 8.2 Grafana 面板对齐

| 面板 | V86 别名引擎 | HERMES 门户 | 对齐 |
|------|-------------|-------------|------|
| 引擎健康状态 | ✅ | ❌ | 缺失 |
| 裁决分布 | ✅ | ❌ | 缺失 |
| 性能指标 | ✅ | ❌ | 缺失 |
| 缓存指标 | ✅ | ❌ | 缺失 |
| F3/F4 指标 | ✅ | ❌ | 缺失 |
| 降级状态 | ✅ | ❌ | 缺失 |
| 规则指标对比 | — | ✅ | 已有 |
| 测试样本 | — | ✅ | 已有 |
| 异步任务 | — | ✅ | 已有 |

### 8.3 监控面板对齐建议

```yaml
# HERMES 门户新增别名引擎监控面板
alias_engine_dashboard:
  panels:
    - title: "别名引擎健康状态"
      type: "stat"
      metrics:
        - "alias_engine_healthy"
        - "alias_degrade_level"
        - "alias_mode"
    - title: "别名裁决分布"
      type: "piechart"
      metrics:
        - "alias_verdict_total"
      dimensions: ["verdict"]
    - title: "别名性能"
      type: "timeseries"
      metrics:
        - "alias_resolve_per_second"
        - "alias_resolve_duration_ms"
        - "alias_cache_hit_rate"
    - title: "别名歧义"
      type: "timeseries"
      metrics:
        - "alias_ambiguous_rate"
        - "alias_tail_ambiguous_total"
    - title: "F3/F4 修复档"
      type: "stat"
      metrics:
        - "alias_f3_trigger_total"
        - "alias_f4_suppress_total"
```

---

## 9. 数据源映射表

### 9.1 V86 别名资产 → HERMES 门户数据源映射

| V86 别名资产 | 数据源文件 | HERMES 门户端点 | 对齐 |
|-------------|-----------|-----------------|------|
| 别名库 | `/v85/indicator_alias_library.csv` | `GET /artifacts/alias_library/query` | ✅ |
| 别名库 MD5 | `MD5_CHECKSUM_LIST.md` | `GET /artifacts/alias_library/verify` | ✅ |
| 回放结果 | `replay_results.json` | — (门户无回放面板) | ❌ 缺失 |
| 裁决分布 | `v86_alias_full_replay_report.md` | — | ❌ 缺失 |
| 性能指标 | `v86_alias_full_replay_report.md` §9 | — | ❌ 缺失 |
| F1/F2/F3/F4 统计 | `v86_alias_full_replay_report.md` §4-6 | — | ❌ 缺失 |
| 灰度门禁状态 | `v86_alias_gray_full_simulation.md` | — | ❌ 缺失 |
| 降级状态 | `/etc/v86/degrade_level` | — | ❌ 缺失 |
| 监控指标 | `/metrics` (Prometheus) | — | ❌ 缺失 |
| 长尾歧义样本 | `v86_alias_full_replay_report.md` §6 | — | ❌ 缺失 |

### 9.2 数据流映射

```
V86 别名引擎
  │
  ├── 别名库 (只读) ──────────→ GET /artifacts/alias_library/query
  │
  ├── 回放结果 ────────────────→ ❌ 门户无面板
  │
  ├── Prometheus 指标 ────────→ ❌ 门户无面板
  │
  ├── 灰度门禁 ────────────────→ ❌ 门户无面板
  │
  ├── 降级状态 ────────────────→ ❌ 门户无面板
  │
  └── F1/F2/F3/F4 统计 ──────→ ❌ 门户无面板
```

### 9.3 数据源对齐状态总结

| 数据源 | 对齐状态 | 说明 |
|--------|----------|------|
| 别名库数据 | ✅ 对齐 | 通过 V85 只读 API |
| 别名库 MD5 | ✅ 对齐 | 通过 verify 端点 |
| 回放结果 | ❌ 缺失 | 门户无回放面板 |
| 裁决分布 | ❌ 缺失 | 门户无别名裁决面板 |
| 性能指标 | ❌ 缺失 | 门户无别名性能面板 |
| F1-F4 统计 | ❌ 缺失 | 门户无修复档面板 |
| 灰度门禁 | ❌ 缺失 | 门户无灰度面板 |
| 降级状态 | ❌ 缺失 | 门户无降级面板 |
| 监控指标 | ❌ 缺失 | 门户无 Prometheus 面板 |

---

## 10. 偏差分析与修正

### 10.1 偏差分析

| 偏差类型 | 数量 | 影响 | 严重级别 |
|----------|------|------|----------|
| 指标口径差异 | 4 | 语义不一致 | 中 |
| 指标缺失 | 16 | 信息不完整 | 高 |
| 面板缺失 | 6 | 展示不完整 | 高 |
| 数据源缺失 | 7 | 数据不可达 | 高 |

### 10.2 修正建议

#### 短期 (v86.0.0, Gate 评审前)

| 修正项 | 方法 | 工作量 |
|--------|------|--------|
| 别名库统计面板 | 新增 Grafana 面板 | 2h |
| F3/F4 状态面板 | 新增 Grafana 面板 | 1h |
| 裁决分布面板 | 新增 Grafana 面板 | 2h |
| 性能指标面板 | 新增 Grafana 面板 | 2h |
| 歧义率面板 | 新增 Grafana 面板 | 1h |
| 降级状态面板 | 新增 Grafana 面板 | 1h |
| **总计** | | **9h** |

#### 中期 (v86.1)

| 修正项 | 方法 | 工作量 |
|--------|------|--------|
| Prometheus 指标集成 | 接入 V86 别名引擎指标 | 4h |
| 回放结果面板 | 新增回放结果展示 | 8h |
| F1-F4 统计面板 | 新增修复档统计 | 4h |
| 灰度门禁面板 | 新增灰度门禁状态 | 4h |
| **总计** | | **20h** |

### 10.3 指标口径修正

```yaml
# 口径修正建议
metrics_corrections:
  # 1. PASS 率语义修正
  alias_pass_rate:
    definition: "别名解析 PASS 率 (别名正确解析为 canonical_key)"
    formula: "pass_count / total_entries"
    v86_value: 0.964
    note: "与规则拦截率不同, 需区分展示"

  # 2. BLOCK 率语义修正
  alias_block_rate:
    definition: "别名解析 BLOCK 率 (黑名单/歧义阻断)"
    formula: "block_count / total_entries"
    v86_value: 0.0004
    note: "与规则拦截率不同"

  # 3. REVIEW 状态新增
  alias_review_rate:
    definition: "别名解析 REVIEW 率 (歧义别名, 需人工复核)"
    formula: "review_count / total_entries"
    v86_value: 0.0355
    note: "V86 新增状态, V85 无此状态"

  # 4. 歧义率新增
  alias_ambiguity_rate:
    definition: "别名歧义率 (F2 AMBIGUOUS 状态)"
    formula: "ambiguous_count / total_entries"
    v86_value: 0.0355
    note: "与 REVIEW 率数值相同但语义不同"
```

---

## 11. 核验结论

### 11.1 核验结果

| 核验维度 | 对齐项 | 缺失项 | 偏差项 | 状态 |
|----------|--------|--------|--------|------|
| 指标口径 | 4 | 4 | 4 | ⚠️ 部分对齐 |
| 别名库统计 | 2 | 5 | 0 | ⚠️ 部分对齐 |
| F3/F4 开关 | 0 | 4 | 0 | ❌ 缺失 |
| 歧义率 | 0 | 4 | 0 | ❌ 缺失 |
| 吞吐延迟 | 0 | 6 | 0 | ❌ 缺失 |
| 裁决分布 | 0 | 4 | 2 | ❌ 缺失 |
| 监控面板 | 0 | 6 | 0 | ❌ 缺失 |
| **总计** | **6** | **33** | **6** | **⚠️ 需修正** |

### 11.2 核验结论

1. **别名库数据源**: ✅ 对齐 — 通过 V85 只读 API 可读取
2. **指标口径**: ⚠️ 部分对齐 — PASS/BLOCK 语义需区分, REVIEW/歧义率需新增
3. **F3/F4 开关状态**: ❌ 缺失 — 门户无别名引擎状态面板
4. **歧义率指标**: ❌ 缺失 — 门户无歧义维度
5. **吞吐延迟指标**: ❌ 缺失 — 门户无别名性能面板
6. **裁决分布**: ❌ 缺失 — 门户无别名裁决面板
7. **监控面板**: ❌ 缺失 — 门户无 Prometheus 指标面板

### 11.3 Gate 评审影响评估

| 影响 | 评估 | 缓解措施 |
|------|------|----------|
| 评审现场展示 | ⚠️ 门户无法展示别名引擎状态 | 使用离线数据 + PPT 素材 |
| 指标口径理解 | ⚠️ 需解释 PASS/REVIEW/BLOCK 差异 | 使用 KB 问答手册 |
| 数据一致性 | ✅ 别名库数据源一致 | 无需修正 |
| 实时监控 | ❌ 门户无法监控别名引擎 | 使用独立 Grafana 仪表盘 |

### 11.4 建议行动项

| 优先级 | 行动 | 负责人 | 截止 |
|--------|------|--------|------|
| P0 | 新增别名引擎状态面板 (F3/F4/降级) | 门户开发 | Gate 评审前 |
| P0 | 新增裁决分布面板 (PASS/REVIEW/BLOCK) | 门户开发 | Gate 评审前 |
| P0 | 新增性能指标面板 (吞吐/耗时/缓存) | 门户开发 | Gate 评审前 |
| P1 | 新增歧义率面板 (AMBIGUOUS/长尾) | 门户开发 | v86.1 |
| P1 | 接入 Prometheus 指标 | 门户开发 | v86.1 |
| P2 | 新增回放结果面板 | 门户开发 | v86.2 |
| P2 | 新增 F1-F4 统计面板 | 门户开发 | v86.2 |

### 11.5 约束合规

| 约束 | 状态 |
|------|------|
| NO_ZHIJI_API_CALL=TRUE | ✅ 无外部 API 调用 |
| NO_MODIFY_V85=TRUE | ✅ V85 数据只读 |
| NO_OVERWRITE=TRUE | ✅ 仅新增文件 |
| BRANCH_LOCKED=TRUE | ✅ feature/v85-chart-template |

---

*门户数据交叉核验报告由 DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE T2.4 生成*
*分支: feature/v85-chart-template · Commit: d1e070d · 资产版本: v86.0.0-frozen*
