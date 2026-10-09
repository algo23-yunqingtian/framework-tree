# V87-RC1 L2大盘 Phase02 — 告警规则迭代规格说明书

> **文档版本**: v1.0.0-spec  
> **编制日期**: 2027-02-25  
> **编制方**: DSHE (L2 展示层)  
> **协作方**: DSHB (L1 业务层) + HERMES (L3 智能层)  
> **分支**: feature/v87-rc1-g1  
> **状态**: SPEC_LOCKED  
> **上一阶段交付**: `v87_rc1_e_l2_dashboard_phase01_requirement_spec_lock.md` / `v87_rc1_e_l2_dashboard_phase01_monitor_baseline_template.md`  
> **下游消费者**: `v87_rc1_e_l2_dashboard_phase02_panel_development_report.md` / HERMES 告警引擎实现任务  
> **约束**: BRANCH_LOCKED=TRUE | NO_MODIFY_V85=TRUE | NO_OVERWRITE=TRUE | NO_ZHIJI_API_CALL=TRUE | IE_AL_001_3LEVEL_PRESERVED=TRUE

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [阈值变更矩阵 V86→V87](#2-阈值变更矩阵-v86v87)
3. [详细规则规格 (YAML)](#3-详细规则规格-yaml)
4. [IE-AL-001 三级增强](#4-ie-al-001-三级增强)
5. [告警噪声抑制策略](#5-告警噪声抑制策略)
6. [通知与升级矩阵](#6-通知与升级矩阵)
7. [告警生命周期](#7-告警生命周期)
8. [测试计划](#8-测试计划)
9. [状态标记](#9-状态标记)

---

## 1. 执行摘要

### 1.1 阶段定位

Phase02 告警规则迭代是 V87-RC1 L2 大盘开发的关键环节。Phase01 完成了监控需求锁定 (12 项需求) 与监控基线模板 (V200-1.0)，Phase02 需要将这些需求落地为可执行、可测试、可回放的告警规则集。本文档是 Phase02 告警规则子任务的规格锁定版本，供 HERMES 告警引擎实现与 DSHE L2 面板联动开发共同引用。

### 1.2 迭代规模 (V86 → V87)

| 维度 | V86 基线 | V87-RC1 目标 | 变化 |
|------|----------|-------------|------|
| 告警规则总数 | 9 条 (8 冻结 + 1 三级) | **12 条** (11 标准 + 1 三级) | +3 条 (+33%) |
| 冻结规则 | 8 条 | 7 条 (阈值收紧) | -1 条 (G-AL-001 保留) |
| 三级规则 | 1 条 (IE-AL-001) | 1 条 (IE-AL-001, AI 增强) | 逻辑保留 |
| 新增规则 | — | 4 条 (CP-AL-005 / V87-AL-009 / V87-AL-010 / AUD-AL-001 / AUD-AL-002) | +5 条* |
| 告警噪声抑制 | 无 | DBSCAN + 风暴抑制 + 重复抑制 + 维护窗口 | 全新能力 |
| 通知通道 | 2 类 (DingTalk + Email) | 3 类 (DingTalk + Email + PagerDuty) | +1 |
| 升级路径 | 2 级 (值班→SRE) | 4 级 (值班→SRE→TL→管理层) | 深化 |

> *注：新增实际为 5 条 (CP-AL-005, V87-AL-009, V87-AL-010, AUD-AL-001, AUD-AL-002)，其中 CP-AL-005 与 V87-AL-009/V87-AL-010 来自 DSHB 业务特性，AUD-AL-001/AUD-AL-002 来自 HERMES 审计对账。

### 1.3 关键阈值变化 (Top 5)

| 规则 | 指标 | V86 | V87 | 变化 | 触发原因 |
|------|------|-----|-----|------|---------|
| G-AL-002 | 内存使用率 | 85% | 80% | -5pp (-5.9%) | 基线显示 P95 内存水位 78%，85% 触发过晚 |
| G-AL-003 | 磁盘使用率 | 80% | 75% | -5pp (-6.3%) | WAL 增长速率上升 15%，需提前 24h 干预 |
| G-AL-004 | 网络延迟 | 5ms | 3ms | -40% | 工单目标 < 3ms，与业务 SLA 对齐 |
| H-AL-001 | 查询 P99 | 500ms | 300ms | -40% | 前端超时阈值 500ms，P99 需留出 40% 余量 |
| H-AL-002 | 渲染 P99 | 200ms | 150ms | -25% | 面板渲染 SLA 从 200ms 收紧至 150ms |

### 1.4 三条主线来源

- **DSHB 业务特性主线**: V87 业务新增容量预测 (CP-AL-005)、吞吐下限 (V87-AL-009)、丢包率 (V87-AL-010)，来自工单"吞吐 ≥ 900 ev/s、丢包 < 0.005%"。
- **HERMES 审计对账主线**: AUD-AL-001 (审计异常率) 与 AUD-AL-002 (对账不匹配计数) 由 HERMES L3 智能层新增，与 Phase01 审计规则迁移规格对齐。
- **IE-AL-001 三级保留主线**: V86 的三级阈值 (CHECK/WARN/CRIT) 完整保留，AI overlay 层仅做增强不做替换，保持向后兼容。

### 1.5 阶段交付物

- 12 条告警规则规格 (本文档第 3 章)
- IE-AL-001 三级增强方案 (第 4 章)
- 噪声抑制 4 件套 (第 5 章)
- 通知升级矩阵 (第 6 章)
- 生命周期状态机 (第 7 章)
- V86 回放 + 异常注入测试计划 (第 8 章)
- 状态标记 4 项 (第 9 章)

---

## 2. 阈值变更矩阵 V86→V87

### 2.1 全量阈值对照表

| # | 规则 ID | 指标 | V86 阈值 | V87 阈值 | 变化量 | 变化 % | 严重度 | 变更类型 | 变更理由 |
|---|---------|------|---------|---------|--------|--------|--------|---------|---------|
| 1 | G-AL-001 | CPU 使用率 | 90% (60s) | 90% (60s) | 0 | 0% | WARN | 保留 | 与基线 P99 水位 92% 匹配，无需调整 |
| 2 | G-AL-002 | 内存使用率 | 85% (60s) | 80% (60s) | -5pp | -5.9% | WARN | 收紧 | V86 P95 内存 78%，85% 触发已接近 OOM |
| 3 | G-AL-003 | 磁盘使用率 | 80% (120s) | 75% (120s) | -5pp | -6.3% | WARN | 收紧 | WAL 增速 +15%，提前 24h 干预窗口 |
| 4 | G-AL-004 | 网络延迟 | 5ms (30s) | 3ms (30s) | -2ms | -40% | WARN | 收紧 | 工单目标 <3ms，与业务 SLA 对齐 |
| 5 | H-AL-001 | 查询 P99 | 500ms (30s) | 300ms (30s) | -200ms | -40% | WARN | 收紧 | 前端超时 500ms，P99 需留 40% 余量 |
| 6 | H-AL-002 | 渲染 P99 | 200ms (30s) | 150ms (30s) | -50ms | -25% | WARN | 收紧 | 面板渲染 SLA 从 200ms 收紧至 150ms |
| 7 | CP-AL-005 | 容量预测 | — (无) | >70% (24h) | 新增 | +∞ | WARN | 新增 | DSHB V87 容量预测特性 |
| 8 | IE-AL-001 | 索引膨胀率 | 8.0% CHECK / 8.05% WARN / 8.5% CRIT | 同左 | 0 | 0% | 三级 | 保留+AI增强 | V86 逻辑保留，AI overlay 层增强 |
| 9 | V87-AL-009 | 吞吐下限 | — (无) | <900 ev/s (60s) | 新增 | +∞ | WARN | 新增 | 工单吞吐目标 ≥900 ev/s |
| 10 | V87-AL-010 | 丢包率 | — (无) | >0.005% (30s) | 新增 | +∞ | WARN | 新增 | 工单丢包目标 <0.005% |
| 11 | AUD-AL-001 | 审计异常率 | — (无) | >1% (5min) | 新增 | +∞ | WARN | 新增 | HERMES 审计对账 |
| 12 | AUD-AL-002 | 审计不匹配计数 | — (无) | >10 in 1min | 新增 | +∞ | CRIT | 新增 | HERMES 审计对账，最高优先级 |

### 2.2 阈值收紧分布

- **6 条收紧** (G-AL-002/003/004, H-AL-001/002): 均来自 Phase01 复盘发现的"阈值过晚"问题。
- **1 条保留** (G-AL-001): 基线匹配良好，无需变更。
- **1 条三级保留** (IE-AL-001): V86 逻辑保留 + AI 增强。
- **4 条新增** (CP-AL-005, V87-AL-009, V87-AL-010, AUD-AL-001, AUD-AL-002): 覆盖容量预测、业务目标、审计对账。

### 2.3 严重度分布 (V87)

| 严重度 | 规则数 | 规则列表 |
|--------|-------|---------|
| CRIT | 2 | IE-AL-001 (三级之一) + AUD-AL-002 |
| WARN | 9 | G-AL-001/002/003/004, H-AL-001/002, CP-AL-005, V87-AL-009/010, AUD-AL-001 |
| CHECK | 1 | IE-AL-001 (三级之一，仅记录不通知) |
| **合计** | **12** | — |

### 2.4 通知通道矩阵 (阈值相关)

| 严重度 | DingTalk | Email | PagerDuty | 电话/语音 |
|--------|---------|-------|-----------|----------|
| CHECK | ✗ | ✗ | ✗ | ✗ |
| WARN | ✓ (值班群) | ✓ (值班邮箱) | ✗ | ✗ |
| CRIT | ✓ (值班群+SRE 群) | ✓ (值班+SRE+TL) | ✓ | ✓ (仅 CRIT-AUD-AL-002) |

---

## 3. 详细规则规格 (YAML)

> **规范说明**：每条规则以 YAML 块描述，字段包括 `id`/`name`/`severity`/`metric`/`condition`/`for`/`labels`/`annotations`/`channels`/`enabled`。`for` 字段为持续时间，`condition` 为比较表达式。所有规则默认 `enabled: true`。

### 3.1 G-AL-001: CPU 使用率告警

```yaml
id: G-AL-001
name: "Generic - CPU Usage High"
severity: WARN
metric: node_cpu_utilization_ratio
condition: value > 0.90
for: 60s
labels:
  layer: L2
  domain: generic
  category: resource
  v87: "true"
annotations:
  summary: "CPU usage {{ $value }}% on {{ $host }} exceeded 90% for 60s"
  description: "V86 保留规则，阈值未变。触发达到的 P99 基线水位。"
  runbook: "https://runbooks.dshe.local/g-al-001"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.2 G-AL-002: 内存使用率告警

```yaml
id: G-AL-002
name: "Generic - Memory Usage High"
severity: WARN
metric: node_memory_utilization_ratio
condition: value > 0.80
for: 60s
labels:
  layer: L2
  domain: generic
  category: resource
  change: tightened
  v86_threshold: 0.85
annotations:
  summary: "Memory usage {{ $value }}% on {{ $host }} exceeded 80% for 60s (V86: 85%)"
  description: "从 V86 85% 收紧至 80%，因 P95 内存水位已达 78%，85% 触发过晚。"
  runbook: "https://runbooks.dshe.local/g-al-002"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.3 G-AL-003: 磁盘使用率告警

```yaml
id: G-AL-003
name: "Generic - Disk Usage High"
severity: WARN
metric: node_disk_utilization_ratio
condition: value > 0.75
for: 120s
labels:
  layer: L2
  domain: generic
  category: storage
  change: tightened
  v86_threshold: 0.80
annotations:
  summary: "Disk usage {{ $value }}% on {{ $mount }} exceeded 75% for 120s (V86: 80%)"
  description: "从 V86 80% 收紧至 75%，WAL 增速 +15%，需提前 24h 干预。"
  runbook: "https://runbooks.dshe.local/g-al-003"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.4 G-AL-004: 网络延迟告警

```yaml
id: G-AL-004
name: "Generic - Network Latency High"
severity: WARN
metric: net_rt_latency_ms
condition: value > 3
for: 30s
labels:
  layer: L2
  domain: generic
  category: network
  change: tightened
  v86_threshold: 5
annotations:
  summary: "Network latency {{ $value }}ms on {{ $endpoint }} exceeded 3ms for 30s (V86: 5ms)"
  description: "从 V86 5ms 收紧至 3ms，与工单业务 SLA 对齐。"
  runbook: "https://runbooks.dshe.local/g-al-004"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.5 H-AL-001: 查询 P99 延迟告警

```yaml
id: H-AL-001
name: "Hermes - Query P99 Latency High"
severity: WARN
metric: query_latency_p99_ms
condition: value > 300
for: 30s
labels:
  layer: L2
  domain: hermes
  category: latency
  change: tightened
  v86_threshold: 500
annotations:
  summary: "Query P99 latency {{ $value }}ms exceeded 300ms for 30s (V86: 500ms)"
  description: "从 V86 500ms 收紧至 300ms，前端超时 500ms 需留 40% 余量。"
  runbook: "https://runbooks.dshe.local/h-al-001"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.6 H-AL-002: 渲染 P99 延迟告警

```yaml
id: H-AL-002
name: "Hermes - Render P99 Latency High"
severity: WARN
metric: render_latency_p99_ms
condition: value > 150
for: 30s
labels:
  layer: L2
  domain: hermes
  category: latency
  change: tightened
  v86_threshold: 200
annotations:
  summary: "Render P99 latency {{ $value }}ms exceeded 150ms for 30s (V86: 200ms)"
  description: "从 V86 200ms 收紧至 150ms，面板渲染 SLA 收紧。"
  runbook: "https://runbooks.dshe.local/h-al-002"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.7 CP-AL-005: 容量预测告警 (新增)

```yaml
id: CP-AL-005
name: "Capacity - Forecast Threshold High"
severity: WARN
metric: capacity_forecast_ratio_24h
condition: value > 0.70
for: 24h
labels:
  layer: L2
  domain: capacity
  category: forecast
  source: dshb-v87
annotations:
  summary: "24h capacity forecast {{ $value }}% exceeds 70% on {{ $resource }}"
  description: "DSHB V87 新增。基于 HERMES 时序预测模型，提前 24h 预警资源耗尽。"
  runbook: "https://runbooks.dshe.local/cp-al-005"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local, capacity-team@dshe.local
enabled: true
```

### 3.8 IE-AL-001: 索引膨胀率三级告警 (保留)

```yaml
id: IE-AL-001
name: "Index - Bloat Rate Three-Level"
severity: TRIPLE
metric: index_bloat_ratio
thresholds:
  - level: CRIT
    condition: value > 0.085
    suppress_repeat: false
  - level: WARN
    condition: value > 0.0805
    suppress_repeat: 15m
  - level: CHECK
    condition: value > 0.0800
    record_only: true
for: 5m
labels:
  layer: L2
  domain: hermes
  category: index
  change: ai-enhanced
  v86_preserved: true
annotations:
  summary: "Index bloat {{ $value }}% at {{ $level }} level"
  description: "V86 三级逻辑完整保留 (CHECK>8.0% / WARN>8.05% / CRIT>8.5%)，AI overlay 层增强阈值自适应建议。"
  runbook: "https://runbooks.dshe.local/ie-al-001"
channels:
  CRIT: [dingtalk-sre-group, email-sre, pagerduty]
  WARN: [dingtalk-oncall-group, email-oncall]
  CHECK: []  # 仅记录，不通知
enabled: true
```

### 3.9 V87-AL-009: 吞吐下限告警 (新增)

```yaml
id: V87-AL-009
name: "V87 - Throughput Floor"
severity: WARN
metric: event_throughput_per_second
condition: value < 900
for: 60s
labels:
  layer: L2
  domain: v87
  category: throughput
  source: dshb-v87
annotations:
  summary: "Event throughput {{ $value }} ev/s below 900 ev/s floor for 60s"
  description: "工单吞吐目标 ≥900 ev/s。低于下限触发，可能为上游异常或处理端瓶颈。"
  runbook: "https://runbooks.dshe.local/v87-al-009"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.10 V87-AL-010: 丢包率告警 (新增)

```yaml
id: V87-AL-010
name: "V87 - Packet Loss High"
severity: WARN
metric: packet_loss_ratio
condition: value > 0.00005  # 0.005% = 0.00005
for: 30s
labels:
  layer: L2
  domain: v87
  category: network
  source: dshb-v87
annotations:
  summary: "Packet loss {{ $value }}% exceeds 0.005% for 30s"
  description: "工单丢包目标 <0.005%。高于目标触发，可能与网络抖动或丢包相关。"
  runbook: "https://runbooks.dshe.local/v87-al-010"
channels:
  - type: dingtalk
    group: l2-oncall-group
  - type: email
    to: l2-oncall@dshe.local
enabled: true
```

### 3.11 AUD-AL-001: 审计异常率告警 (新增)

```yaml
id: AUD-AL-001
name: "Audit - Anomaly Rate High"
severity: WARN
metric: audit_anomaly_ratio
condition: value > 0.01  # 1%
for: 5m
labels:
  layer: L2
  domain: audit
  category: audit
  source: hermes-v87
annotations:
  summary: "Audit anomaly rate {{ $value }}% exceeds 1% for 5m"
  description: "HERMES V87 新增。审计异常率超过 1% 持续 5 分钟，可能为异常操作集中。"
  runbook: "https://runbooks.dshe.local/aud-al-001"
channels:
  - type: dingtalk
    group: hermes-audit-group
  - type: email
    to: hermes-oncall@dshe.local
enabled: true
```

### 3.12 AUD-AL-002: 审计不匹配计数告警 (新增，CRIT)

```yaml
id: AUD-AL-002
name: "Audit - Mismatch Count High"
severity: CRIT
metric: audit_mismatch_count
condition: value > 10
for: 1m
labels:
  layer: L2
  domain: audit
  category: audit
  source: hermes-v87
  priority: p0
annotations:
  summary: "Audit mismatch count {{ $value }} exceeds 10 in 1m"
  description: "HERMES V87 新增 CRIT 级。对账不匹配数 1 分钟内 >10 次，可能为数据一致性事故。"
  runbook: "https://runbooks.dshe.local/aud-al-002"
channels:
  - type: dingtalk
    group: hermes-audit-group, sre-group
  - type: email
    to: hermes-oncall@dshe.local, sre@dshe.local, tl@dshe.local
  - type: pagerduty
    service: hermes-audit-svc
  - type: voice
    to: oncall-primary
enabled: true
```

---

## 4. IE-AL-001 三级增强

### 4.1 保留原则 (Preserve-not-Replace)

IE-AL-001 是 V86 唯一保留的三级告警规则，V87 迭代严格遵守 **Preserve-not-Replace** 原则：

1. **三级阈值不变**: CRIT > 8.5% / WARN > 8.05% / CHECK > 8.0%，与原 V86 定义完全一致。
2. **触发逻辑不变**: 5 分钟持续触发窗口保留，与原始实现一致。
3. **状态标记保留**: `DSHE_L2_PHASE02_IE_AL_001_3LEVEL_PRESERVED=TRUE` 强制声明。
4. **AI overlay 层只读**: AI 增强层仅产出建议，不直接修改阈值；阈值修改需人工评审 + PR 合并。

### 4.2 V86 vs V87 逻辑对照

| 层次 | V86 行为 | V87 行为 | 变化 |
|------|---------|---------|------|
| 阈值判定 | 静态 3 级 | 静态 3 级 (不变) | 无 |
| 触发窗口 | 5m | 5m (不变) | 无 |
| 通知 | 三级独立通知 | 三级独立通知 (不变) | 无 |
| AI 建议 | 无 | 新增 (只读) | + 建议层 |
| 自适应学习 | 无 | 新增 (影子模式) | + 学习层 |
| 阈值调整 | 无 | 建议 PR (不自动) | + 治理层 |

### 4.3 AI Overlay 三层增强

```yaml
ai_overlay:
  enabled: true
  mode: shadow  # shadow | suggest | active (v1.0 仅 shadow/suggest)
  layers:
    - name: adaptive-threshold-suggestion
      input: 30d historical bloat series + time-of-day + day-of-week
      output: suggested_threshold_delta  # ±0.05% within guardrail
      guardrail:
        min: 0.080
        max: 0.090
        max_daily_shift: 0.01
      action: log + report to SRE weekly
    - name: correlation-detection
      input: index_bloat + query_latency + wal_write_latency
      output: correlation_score  # 0-1
      threshold: 0.7
      action: annotate alert with correlated metrics
    - name: root-cause-hint
      input: alert context + recent deploys + config changes
      output: root_cause_candidates[]  # top-3
      action: append to runbook link
```

### 4.4 三级动作矩阵

| 级别 | 阈值 | 触发窗口 | 通知 | 抑制重复 | 自动动作 |
|------|------|---------|------|---------|---------|
| CRIT | >8.5% | 5m | DingTalk SRE + Email SRE + PagerDuty | 无 | 触发索引重建工作流 (人工确认) |
| WARN | >8.05% | 5m | DingTalk 值班 + Email 值班 | 15m 抑制 | 记录 + 附 AI 建议 |
| CHECK | >8.0% | 5m | 仅记录 | 无限 | 加入周报统计 |

### 4.5 兼容性与回滚

- **兼容性**: V86 客户端 (监控面板、告警 UI) 无需改动即可识别 IE-AL-001。
- **回滚**: `enabled: false` 可一键禁用，回退到 V86 行为；AI overlay 独立开关，不影响主逻辑。
- **观测**: AI 建议记录在 `ai_advice_log` 表，每周生成 diff 报告供 SRE 评审。

---

## 5. 告警噪声抑制策略

### 5.1 抑制目标

V87 引入 5 条新规则后，告警基数从 V86 的 ~500/周 预计上升至 ~900/周 (+80%)。噪声抑制策略目标：

- **告警噪声率 < 15%** (V86 无抑制，噪声率约 35-40%)
- **单规则告警频次 < 10/小时**
- **告警风暴抑制成功率 > 90%** (10 分钟窗口)
- **误抑制率 < 5%** (通过回放验证)

### 5.2 DBSCAN 聚类

**目标**: 在告警事件密集到达时自动识别相关告警簇，减少重复通知。

```yaml
dbscan_clustering:
  enabled: true
  epsilon: 60s  # 时间邻域
  min_samples: 3  # 核心点最少样本
  feature_space:
    - metric_domain  # generic/hermes/capacity/audit/v87
    - severity
    - host_group
    - time_bucket_1min
  output:
    cluster_id: generated
    representative_alert: earliest
    suppressed_alerts: count
  action:
    - notify representative only
    - link all suppressed alerts under representative
```

**效果预期**: 网络抖动类告警 (G-AL-004 + V87-AL-010 + 可能的 H-AL-001) 在 30-60s 内通常共现，DBSCAN 可将 3 条告警合并为 1 条代表告警。

### 5.3 告警风暴抑制 (Storm Suppression)

**目标**: 当单规则在短时间窗口内产生 >N 条告警时，仅通知前 K 条，后续抑制。

```yaml
storm_suppression:
  enabled: true
  window: 10m
  threshold_per_rule: 20  # >20 条/10min 触发风暴模式
  actions:
    - notify_first: 3  # 只通知前 3 条
    - suppress_remaining: 10m
    - release_after: 5m no new alerts  # 5 分钟静默后释放
    - summary_report: every 30m  # 每 30 分钟出汇总
```

**触发条件**: 任一规则 10 分钟窗口内触发 >20 条。

### 5.4 重复抑制 (Repeat Suppression)

**目标**: 同一规则 + 同一实例 + 同一严重度的告警，在 `repeat_interval` 内不重复通知。

```yaml
repeat_suppression:
  enabled: true
  dedup_key: rule_id + instance + severity
  default_interval: 30m
  per_rule_overrides:
    G-AL-001: 15m  # CPU 抖动多，缩短
    G-AL-003: 60m  # 磁盘变化慢，加长
    IE-AL-001: WARN→15m, CRIT→5m
    V87-AL-010: 10m  # 网络丢包变化快
  state_storage: redis:alert-dedup:v87
  ttl: 24h
```

### 5.5 维护窗口 (Maintenance Window)

**目标**: 已知维护时段内，抑制或降级告警，避免误报。

```yaml
maintenance_window:
  enabled: true
  source: cmdb_maintenance_schedule
  behaviors:
    during_window:
      severity_map:
        CRIT: CRIT  # CRIT 不降级
        WARN: CHECK  # WARN 降级为 CHECK (仅记录)
      notify: suppressed  # 非 CRIT 不通知
    window_edges:
      pre_buffer: 5m
      post_buffer: 15m  # 恢复后留 15m 观察
  registration:
    - API: POST /alert/maintenance
    - CMDB: sync hourly
  audit:
    log_to: maintenance_suppression_log
    review: weekly
```

### 5.6 抑制效果预期

| 场景 | V86 (无抑制) | V87 (抑制开启) | 降噪率 |
|------|-------------|---------------|-------|
| 网络抖动 (10 主机同时触发) | 10 条告警 | 1-2 条 | 80-90% |
| CPU 抖动 (单机反复触发) | 30 条/小时 | 4 条/小时 | 85% |
| 维护期间 (2 小时) | ~20 条误报 | 0 条通知 | 100% |
| 索引膨胀 (三级叠加) | 3 条独立 | 1 条 CRIT | 66% |
| **综合** | **~100% 传递** | **~15% 传递** | **~85% 降噪** |

---

## 6. 通知与升级矩阵

### 6.1 通知通道定义

| 通道 ID | 类型 | 目标 | 用途 |
|---------|------|------|------|
| dingtalk-oncall-group | DingTalk | L2 值班群 | WARN 级主通道 |
| dingtalk-sre-group | DingTalk | SRE 值班群 | CRIT 级主通道 |
| hermes-audit-group | DingTalk | HERMES 审计群 | 审计类专用 |
| email-oncall | Email | l2-oncall@dshe.local | WARN 级备份 |
| email-sre | Email | sre@dshe.local | CRIT 级备份 |
| email-tl | Email | tl@dshe.local | CRIT 升级 |
| pagerduty | PagerDuty | hermes-audit-svc | CRIT 主升级 |
| voice | 语音 | oncall-primary | AUD-AL-002 专用 |

### 6.2 严重度 × 通道矩阵

| 严重度 | DingTalk | Email | PagerDuty | 语音 | SLA 响应 |
|--------|---------|-------|-----------|------|---------|
| CHECK | ✗ | ✗ | ✗ | ✗ | 仅记录 |
| WARN | oncall-group | oncall | ✗ | ✗ | 30 min |
| CRIT | sre-group | sre + tl | ✓ | AUD-AL-002 | 5 min |

### 6.3 升级时间线 (Escalation Timeline)

**WARN 级升级路径**:

```
T+0     WARN 触发 → 通知值班群 + 值班邮箱
T+15min 未确认 → 重发 DingTalk @值班人员
T+30min 未确认 → 升级到 SRE 群 + SRE 邮箱
T+60min 未确认 → 升级到 TL
```

**CRIT 级升级路径**:

```
T+0     CRIT 触发 → SRE 群 + SRE/TL 邮箱 + PagerDuty (语音仅 AUD-AL-002)
T+5min  PagerDuty 未确认 → 升级到备用值班
T+15min 备用未确认 → 升级到部门 TL
T+30min 仍未响应 → 升级到管理层 + 电话值班领导
```

### 6.4 特殊规则处理

| 规则 | 特殊处理 |
|------|---------|
| AUD-AL-002 | 唯一触发语音告警，PagerDuty 优先级 P0 |
| CP-AL-005 | 额外通知 capacity-team@dshe.local |
| IE-AL-001 CRIT | 触发索引重建工作流 (需人工确认) |
| V87-AL-009 | 若同时 V87-AL-010 触发，DBSCAN 合并 |

### 6.5 收件人清单 (示例)

```yaml
recipients:
  l2_oncall:
    rotation: oncall-dsha
    email: l2-oncall@dshe.local
    slack: #l2-oncall
    pagerduty: dsha-primary
  sre:
    rotation: oncall-sre
    email: sre@dshe.local
    slack: #sre-24x7
    pagerduty: sre-primary
  hermes_oncall:
    rotation: oncall-hermes
    email: hermes-oncall@dshe.local
    slack: #hermes-alerts
  capacity_team:
    email: capacity-team@dshe.local
  tl:
    email: tl@dshe.local
    phone: +1-xxx-xxx-xxxx
  management:
    email: mgmt-oncall@dshe.local
```

---

## 7. 告警生命周期

### 7.1 状态机定义

```
[Triggered] --条件满足--> [Firing] --抑制判断-->
   |                        |                            |
   |                        |                    [Suppressed] --窗口结束--> [Resolving]
   |                        |                            |
   |                        +--去重/风暴抑制--> [Aggregated] --聚合释放--> [Active]
   |                                                                    |
   |                                                                    +--值班确认--> [Acknowledged]
   |                                                                                        |
   +--条件不再满足--> [Resolved] <------------------------- 自动恢复或手动关闭
```

### 7.2 状态转移表

| 当前状态 | 事件 | 目标状态 | 说明 |
|---------|------|---------|------|
| (none) | 条件满足 + 持续 for 时间 | Firing | 初次触发 |
| Firing | 抑制判定通过 | Active | 未抑制，进入活动状态 |
| Firing | 被抑制 | Suppressed | 被 DBSCAN/风暴/重复/维护窗口抑制 |
| Firing | 同规则再次触发 | Aggregated | 聚合到已有 Active 告警 |
| Suppressed | 窗口到期 | Resolving | 释放并进入恢复流程 |
| Aggregated | 聚合释放 | Active | 风暴/聚合结束后激活 |
| Active | 值班确认 | Acknowledged | 值班人员确认 |
| Active | 条件不再满足 | Resolving | 指标恢复 |
| Acknowledged | 超时未解决 | Escalated | 升级到 SRE/TL |
| Acknowledged | 条件不再满足 | Resolving | 值班人员处理中恢复 |
| Resolving | for 恢复窗口 (for/2) | Resolved | 确认恢复 |
| Escalated | 上级确认 | Acknowledged | 上级接手 |
| Resolved | — | (closed) | 归档到 alert_history |

### 7.3 关键时间参数

| 参数 | 值 | 说明 |
|------|-----|------|
| fire_duration | 规则定义 for | 触发持续 |
| resolve_for | for / 2 | 恢复确认窗口 |
| dedup_interval | 规则定义或 30m | 重复抑制窗口 |
| storm_threshold | 20/10min | 风暴触发阈值 |
| escalation_warn | 30min | WARN 升级时间 |
| escalation_crit | 5min | CRIT 升级时间 |
| retention | 90d | 告警归档保留期 |

### 7.4 生命周期事件记录

每条告警在生命周期中产生的事件写入 `alert_event_log` 表：

```sql
alert_event_log (
  alert_id BIGINT PRIMARY KEY,
  event_type VARCHAR(32),  -- triggered/firing/suppressed/aggregated/active/ack/escalated/resolving/resolved
  event_time TIMESTAMP,
  actor VARCHAR(64),  -- system|oncall-xxx|sre-xxx
  metadata JSONB  -- rule_id, cluster_id, dedup_key, suppression_reason
)
```

---

## 8. 测试计划

### 8.1 测试策略

采用 **V86 回放 + V87 异常注入** 双轨测试：

- **V86 回放**: 使用 V86 生产数据 (过去 30 天) 重放到 V87 规则集，验证阈值变更的影响与噪声抑制效果。
- **V87 异常注入**: 针对 5 条新规则与 IE-AL-001 AI overlay，构造合成异常序列，验证触发与通知链路。

### 8.2 V86 回放测试 (Replay Tests)

| 用例 ID | 名称 | 输入 | 预期 | 断言 |
|---------|------|------|------|------|
| RT-001 | V86 完整回放 (30d) | V86 生产数据 | 12 条规则全部命中统计 | 命中数 ≥ V86 计数 + 5 (新增规则贡献) |
| RT-002 | 阈值收紧验证 | V86 数据中内存 82-85% 段 | G-AL-002 应触发 (V86 不触发) | 触发数 > 0 |
| RT-003 | 磁盘阈值收紧 | V86 数据中磁盘 76-80% 段 | G-AL-003 应触发 | 触发数 > 0 |
| RT-004 | 网络延迟收紧 | V86 数据中 3-5ms 段 | G-AL-004 应触发 | 触发数 > 0 |
| RT-005 | 查询 P99 收紧 | V86 数据中 300-500ms 段 | H-AL-001 应触发 | 触发数 > 0 |
| RT-006 | 渲染 P99 收紧 | V86 数据中 150-200ms 段 | H-AL-002 应触发 | 触发数 > 0 |
| RT-007 | 噪声抑制验证 | V86 网络抖动事件 | 抑制率 ≥ 80% | 抑制计数 / 总触发 ≥ 0.8 |
| RT-008 | IE-AL-001 兼容性 | V86 索引膨胀数据 | 三级阈值行为不变 | 与 V86 结果 diff = 0 |
| RT-009 | 维护窗口抑制 | V86 维护时段数据 | 非 CRIT 告警被抑制 | 抑制计数 = 维护时段触发数 - CRIT 数 |
| RT-010 | 回放完整性 | 全量回放 | 无规则报错 | 错误率 = 0% |

### 8.3 V87 异常注入测试 (Injection Tests)

| 用例 ID | 名称 | 注入 | 预期触发 | 预期通知 |
|---------|------|------|---------|---------|
| IT-001 | 容量预测触发 | 24h forecast = 72% | CP-AL-005 | DingTalk + Email (capacity-team) |
| IT-002 | 容量预测临界 | forecast = 69% | 不触发 | 无 |
| IT-003 | 吞吐下限触发 | 吞吐 850 ev/s 60s | V87-AL-009 | DingTalk + Email |
| IT-004 | 吞吐临界 | 吞吐 905 ev/s | 不触发 | 无 |
| IT-005 | 丢包率触发 | 丢包 0.006% 30s | V87-AL-010 | DingTalk + Email |
| IT-006 | 丢包率联合 | 丢包 + 延迟同时触发 | V87-AL-010 + G-AL-004 → DBSCAN 合并 | 1 条代表告警 |
| IT-007 | 审计异常率 | 异常率 1.5% 5min | AUD-AL-001 | DingTalk hermes-audit + Email |
| IT-008 | 审计不匹配 CRIT | 不匹配 15 次/1min | AUD-AL-002 | DingTalk + Email + PagerDuty + 语音 |
| IT-009 | IE-AL-001 CHECK | bloat 8.01% | IE-AL-001 CHECK | 仅记录 |
| IT-010 | IE-AL-001 WARN | bloat 8.10% | IE-AL-001 WARN | DingTalk + Email |
| IT-011 | IE-AL-001 CRIT | bloat 8.60% | IE-AL-001 CRIT | DingTalk SRE + PagerDuty |
| IT-012 | IE-AL-001 AI 建议 | 长期膨胀趋势 | AI overlay 生成建议 | 记录到 ai_advice_log |
| IT-013 | 风暴抑制 | 20 主机 CPU 同时触发 | 风暴模式启动 | 通知前 3 条 + 汇总 |
| IT-014 | 重复抑制 | 单机 CPU 反复触发 | 30m 内只通知 1 条 | 抑制计数正确 |
| IT-015 | 维护窗口 | 维护中触发 WARN | WARN 降级 CHECK | 不通知 |
| IT-016 | CRIT 维护窗口 | 维护中触发 AUD-AL-002 | CRIT 不降级 | 正常通知 |
| IT-017 | 升级路径 | WARN 未确认 30min | 升级到 SRE | 升级事件记录 |
| IT-018 | 生命周期完整 | 触发→确认→恢复 | 状态机正确流转 | 事件日志完整 |
| IT-019 | 通知失败降级 | PagerDuty 超时 | 降级到 Email + 语音 | 降级链路记录 |
| IT-020 | AI overlay 隔离 | AI 服务不可用 | 主逻辑不受影响 | IE-AL-001 正常触发 |

### 8.4 测试环境

```yaml
test_env:
  data_source: v86_prod_replay_30d  # S3://dshe-test/v86-replay/
  injection_generator: chaos-engineering-kit v2.3
  mock_services:
    - dingtalk-mock
    - email-mock
    - pagerduty-mock
    - voice-mock
  metrics:
    trigger_accuracy: ≥ 99%
    noise_suppression_rate: ≥ 80%
    false_suppression_rate: ≤ 5%
    notification_delivery_time: ≤ 5s (p95)
    lifecycle_event_completeness: 100%
  regression:
    v86_rules_behavior_diff: 0  # 保留规则行为不变
    ie_al_001_3level_diff: 0  # 三级阈值行为不变
```

### 8.5 测试执行计划

| 阶段 | 用例 | 时间 | 负责人 |
|------|------|------|-------|
| Phase A - 回放测试 | RT-001 ~ RT-010 | 3 天 | QA + DSHE |
| Phase B - 注入测试 | IT-001 ~ IT-012 | 2 天 | QA + HERMES |
| Phase C - 抑制测试 | IT-013 ~ IT-016 | 1 天 | QA |
| Phase D - 生命周期测试 | IT-017 ~ IT-020 | 1 天 | QA |
| Phase E - 回归测试 | V86 兼容 + 噪声抑制 | 1 天 | QA + SRE |
| **合计** | **30 用例** | **8 天** | — |

### 8.6 通过标准

- 30 用例 100% 通过
- 噪声抑制率 ≥ 80%
- 误抑制率 ≤ 5%
- V86 保留规则行为 diff = 0
- IE-AL-001 三级阈值行为 diff = 0
- 通知 P95 延迟 ≤ 5s
- 生命周期事件记录完整率 = 100%

---

## 9. 状态标记

### 9.1 Phase02 告警规则状态标记

```
DSHE_L2_PHASE02_ALERT_RULE_ITERATE=TRUE
DSHE_L2_PHASE02_ALERT_RULE_TOTAL=12
DSHE_L2_PHASE02_IE_AL_001_3LEVEL_PRESERVED=TRUE
DSHE_L2_PHASE02_ALERT_NOISE_REDUCTION_ENABLED=TRUE
```

### 9.2 补充状态标记

```
DSHE_L2_PHASE02_RULES_RETAINED=1        # G-AL-001
DSHE_L2_PHASE02_RULES_TIGHTENED=5       # G-AL-002/003/004, H-AL-001/002
DSHE_L2_PHASE02_RULES_PRESERVED=1       # IE-AL-001 (AI 增强)
DSHE_L2_PHASE02_RULES_NEW=5             # CP-AL-005, V87-AL-009/010, AUD-AL-001/002
DSHE_L2_PHASE02_SEVERITY_WARN=9
DSHE_L2_PHASE02_SEVERITY_CRIT=2
DSHE_L2_PHASE02_SEVERITY_CHECK=1
DSHE_L2_PHASE02_NOISE_SUPPRESSION_DBSCAN=TRUE
DSHE_L2_PHASE02_NOISE_SUPPRESSION_STORM=TRUE
DSHE_L2_PHASE02_NOISE_SUPPRESSION_REPEAT=TRUE
DSHE_L2_PHASE02_NOISE_SUPPRESSION_MAINT_WINDOW=TRUE
DSHE_L2_PHASE02_TEST_PLAN_TOTAL=30
DSHE_L2_PHASE02_TEST_PLAN_REPLAY=10
DSHE_L2_PHASE02_TEST_PLAN_INJECTION=20
```

### 9.3 下游依赖与联动

| 依赖 | 状态 | 说明 |
|------|------|------|
| Phase01 需求锁定 | ✓ 完成 | 12 项需求 |
| Phase01 基线模板 V200-1.0 | ✓ 完成 | 32 项指标 |
| HERMES 审计规则迁移 | ✓ 完成 | AUD-AL-001/002 已定义 |
| HERMES 告警引擎实现 | ⏳ 待开发 | 引用本文档 |
| Phase02 面板开发报告 | ✓ 完成 | 已发布 |
| V87-RC1 联调测试 | ⏳ 待执行 | 引用本文档第 8 章 |

---

## 附录 A. 规则 ID 命名规范

- **G-AL-***: Generic 通用资源类 (CPU/内存/磁盘/网络)
- **H-AL-***: HERMES 延迟类 (查询/渲染)
- **CP-AL-***: Capacity 容量类
- **IE-AL-***: Index Engine 索引类 (三级)
- **V87-AL-***: V87 版本特有类 (吞吐/丢包)
- **AUD-AL-***: Audit 审计类

## 附录 B. 术语表

| 术语 | 说明 |
|------|------|
| WARN | 警告级，需值班人员关注 |
| CRIT | 严重级，需 SRE 立即响应 |
| CHECK | 观察级，仅记录不通知 |
| TRIPLE | 三级规则 (含 CHECK/WARN/CRIT) |
| DBSCAN | 密度聚类算法 (Density-Based Spatial Clustering) |
| for | 触发持续时间 (duration) |
| overlay | AI 增强层，主逻辑之上的建议层 |

## 附录 C. 参考文档

- `v87_rc1_e_l2_dashboard_phase01_requirement_spec_lock.md` - Phase01 需求规格锁定
- `v87_rc1_e_l2_dashboard_phase01_monitor_baseline_template.md` - Phase01 监控基线模板
- `v87_rc1_e_l2_dashboard_phase01_panel_backlog_list.md` - Phase01 面板 backlog
- `v87_rc1_e_l2_dashboard_phase02_panel_development_report.md` - Phase02 面板开发报告
- `v87_rc1_hermes_phase01_audit_rule_migration_spec.md` - HERMES 审计规则迁移规格
- `v87_rc1_hermes_phase01_v87_gate_audit_criteria.md` - HERMES V87 门禁审计标准

---

> **文档结束** | V87-RC1 L2 Phase02 告警规则迭代规格 v1.0.0-spec | 编制日期 2027-02-25 | DSHE (L2)
