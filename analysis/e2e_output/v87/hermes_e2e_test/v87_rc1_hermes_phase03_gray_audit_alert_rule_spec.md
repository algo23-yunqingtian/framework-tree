# HERMES V87-RC1 Phase03 — 灰度审计告警规则规格书

| 项目 | 值 |
|------|---|
| 工单 | HERMES_V87_RC1_PHASE03_AUDIT_ALERT_CONFIG |
| 编制方 | HERMES |
| 日期 | 2026-10-18 |
| 对接 | DSHE L2大盘 (AUD-AL-001/002) |

---

## 1. 告警规则总览

| # | 告警ID | 名称 | 严重度 | 触发条件 |
|---|--------|------|--------|---------|
| 1 | AUD-AL-001 | 审计异常率告警 | WARN | 异常率>1% 持续5m |
| 2 | AUD-AL-002 | 审计不匹配计数告警 | CRIT | 不匹配>10次/1m |
| 3 | HERMES-AL-001 | 对账窗口失败告警 | CRIT | 窗口对账FAIL |
| 4 | HERMES-AL-002 | 事件丢失告警 | WARN | 事件偏差>0.3% |
| 5 | HERMES-AL-003 | 重复事件告警 | WARN | 去重率<100% |
| 6 | HERMES-AL-004 | 索引膨胀超限告警 | CRIT | 膨胀速率>0.018pp |
| 7 | HERMES-AL-005 | 链断裂告警 | CRIT | 链断裂>0 |

## 2. 告警规则详细规格

### 2.1 HERMES-AL-001: 对账窗口失败告警

```yaml
id: HERMES-AL-001
name: "Reconcile Window Failure"
severity: CRIT
metric: reconcile_window_fail
condition: value > 0
for: 1m
labels:
  layer: L3
  domain: audit
  traffic: 50%-gray
  source: hermes-v87
  phase: phase03
annotations:
  summary: "Reconcile window FAILED {{ $value }} times in 1m"
  description: "50%灰度对账窗口出现失败，可能为数据一致性问题"
  runbook: "https://runbooks.hermes.local/hermes-al-001"
channels:
  - type: dingtalk
    group: hermes-audit-group
  - type: pagerduty
    service: hermes-audit-svc
  - type: voice
    to: oncall-primary
enabled: true
```

### 2.2 HERMES-AL-002: 事件丢失告警

```yaml
id: HERMES-AL-002
name: "Event Loss High"
severity: WARN
metric: ev_dev_pct
condition: value > 0.3
for: 5m
labels:
  layer: L3
  domain: audit
  traffic: 50%-gray
  phase: phase03
annotations:
  summary: "Event deviation {{ $value }}% exceeds 0.3% for 5m"
  description: "50%灰度事件偏差超过0.3%持续5分钟"
  runbook: "https://runbooks.hermes.local/hermes-al-002"
channels:
  - type: dingtalk
    group: hermes-audit-group
  - type: email
    to: hermes-oncall@dshe.local
enabled: true
```

### 2.3 HERMES-AL-003: 重复事件告警

```yaml
id: HERMES-AL-003
name: "Duplicate Event Detected"
severity: WARN
metric: dup_rate
condition: value < 100
for: 5m
labels:
  layer: L3
  domain: audit
  traffic: 50%-gray
  phase: phase03
annotations:
  summary: "Dedup rate {{ $value }}% below 100% for 5m"
  description: "50%灰度去重率低于100%，可能存在重复事件"
  runbook: "https://runbooks.hermes.local/hermes-al-003"
channels:
  - type: dingtalk
    group: hermes-audit-group
enabled: true
```

### 2.4 HERMES-AL-004: 索引膨胀超限告警

```yaml
id: HERMES-AL-004
name: "Index Inflation Exceeds Limit"
severity: CRIT
metric: idx_inflation_rate
condition: value > 0.018
for: 1h
labels:
  layer: L3
  domain: audit
  traffic: 50%-gray
  phase: phase03
  category: index
annotations:
  summary: "Index inflation rate {{ $value }}pp exceeds 0.018pp"
  description: "50%灰度索引膨胀速率超过灰度阈值，需紧急关注"
  runbook: "https://runbooks.hermes.local/hermes-al-004"
channels:
  - type: dingtalk
    group: hermes-audit-group, sre-group
  - type: email
    to: hermes-oncall@dshe.local, sre@dshe.local
  - type: pagerduty
    service: hermes-audit-svc
enabled: true
```

### 2.5 HERMES-AL-005: 链断裂告警

```yaml
id: HERMES-AL-005
name: "Chain Broken Detected"
severity: CRIT
metric: chain_broken
condition: value > 0
for: 1m
labels:
  layer: L3
  domain: audit
  traffic: 50%-gray
  phase: phase03
  priority: p0
annotations:
  summary: "Chain broken {{ $value }} times in 1m"
  description: "50%灰度检测到链断裂，可能为数据丢失事故"
  runbook: "https://runbooks.hermes.local/hermes-al-005"
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

## 3. 对接 DSHE 告警

### 3.1 DSHE 已有审计告警

| 告警ID | 严重度 | 条件 | HERMES对接 |
|--------|--------|------|-----------|
| AUD-AL-001 | WARN | 异常率>1%/5m | ✅ 上报 |
| AUD-AL-002 | CRIT | 不匹配>10/1m | ✅ 上报 |

### 3.2 HERMES 新增告警

| 告警ID | 严重度 | 条件 | DSHE对接 |
|--------|--------|------|---------|
| HERMES-AL-001 | CRIT | 窗口FAIL | ✅ 映射AUD-AL-002 |
| HERMES-AL-002 | WARN | 事件偏差>0.3% | ✅ 映射AUD-AL-001 |
| HERMES-AL-003 | WARN | 去重<100% | ✅ 映射AUD-AL-001 |
| HERMES-AL-004 | CRIT | 膨胀>0.018pp | ✅ 映射IE-AL-001 |
| HERMES-AL-005 | CRIT | 链断裂>0 | ✅ 映射AUD-AL-002 |

## 4. 告警升级链路

```
HERMES L3 告警触发
    ↓
HERMES-AL-001~005
    ↓
映射 DSHE AUD-AL-001/002 + IE-AL-001
    ↓
DSHE L2 大盘展示
    ↓
通知: dingtalk + email + pagerduty + voice
```

## 5. 告警去重与抑制

| 机制 | 配置 |
|------|------|
| 去重窗口 | 5分钟 |
| 抑制规则 | CRIT告警抑制同组WARN |
| 静默期 | 故障处理后15分钟 |
| 告警恢复 | 自动恢复通知 |

## 6. 灰度告警阈值特殊配置

| 告警 | 50%灰度阈值 | 说明 |
|------|-----------|------|
| 膨胀速率 | 0.018pp | 50%缩放(100%的0.035pp上限) |
| 事件偏差 | 0.3% | WARN阈值 |
| 膨胀观察 | 0.0157pp | 基线 |

## 7. 告警验证

| 验证项 | 预期 | 实际 | 判定 |
|--------|------|------|------|
| HERMES-AL-001 触发 | CRIT | ✅ | ✅ |
| HERMES-AL-002 触发 | WARN | ✅ | ✅ |
| HERMES-AL-003 触发 | WARN | ✅ | ✅ |
| HERMES-AL-004 触发 | CRIT | ✅ | ✅ |
| HERMES-AL-005 触发 | CRIT | ✅ | ✅ |
| DSHE上报 | 成功 | ✅ | ✅ |
| 通知通道 | 全通道 | ✅ | ✅ |

**7/7 告警验证通过** ✅

## 8. 结论

| 维度 | 结论 |
|------|------|
| HERMES告警 | 5条 |
| DSHE对接 | AUD-AL-001/002 |
| 严重度 | CRIT×3 + WARN×2 |
| 通知 | dingtalk+email+pagerduty+voice |
| 去重抑制 | 5分钟窗口 |
| 灰度阈值 | 0.018pp |
| 验证 | 7/7 PASS |
| **告警配置** | **完成** ✅ |

---

*关联: v87_rc1_e_l2_dashboard_phase02_alert_rule_iteration_spec.md (DSHE)*
