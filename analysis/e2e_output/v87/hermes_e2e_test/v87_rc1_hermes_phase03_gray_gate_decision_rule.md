# HERMES V87-RC1 Phase03 — 灰度 Gate 判定规则

| 项目 | 值 |
|------|---|
| 工单 | HERMES_V87_RC1_PHASE03_GATE_DECISION_RULE |
| 编制方 | HERMES |
| 日期 | 2026-10-18 |

---

## 1. 判定总览

| 判定 | 含义 | 动作 |
|------|------|------|
| **GO** | 全部通过 | 继续灰度 |
| **COND-GO** | 部分偏差，可接受 | 附约束继续 |
| **RED** | 严重问题 | 阻断灰度，回滚 |

## 2. GO 判定条件（全部满足）

| # | 条件 | 阈值 | 验证 |
|---|------|------|------|
| G01 | SHA256对账 | 100%窗口 | 实时 |
| G02 | 链断裂 | 0 | 实时 |
| G03 | 去重率 | 100% | 实时 |
| G04 | 丢包率 | ≤0.01% | 实时 |
| G05 | WAL P99 | <2000ms | 实时 |
| G06 | 索引P99 | <10ms | 实时 |
| G07 | V87字段 | 全PASS | 实时 |
| G08 | 膨胀速率 | 0.014-0.018pp | 24h趋势 |
| G09 | 优雅降级 | 正确 | 故障时 |
| G10 | 误判 | 0 | 持续 |
| G11 | 无退化趋势 | stable | 24h趋势 |
| G12 | 告警 | 0 CRIT | 持续 |

## 3. COND-GO 判定条件

| # | 条件 | 阈值 | 约束 |
|---|------|------|------|
| C01 | 9-11/12 GO条件满足 | — | 1-2项可接受偏差 |
| C02 | 膨胀速率 | 0.018-0.020pp | 降速至30% |
| C03 | 事件偏差 | 0.3-0.5% | 增加监控 |
| C04 | 模型偏差 | ≤8% | 72h后重校 |
| C05 | P2风险 | ≤1 | 附缓释方案 |
| C06 | 无P0/P1 | 必须 | 不可放宽 |

### COND-GO 附加约束

| 约束 | 内容 |
|------|------|
| 监控频率 | 从1h提升为15min |
| 重校周期 | 72h后重新校准 |
| 回滚条件 | 命中RED即回滚 |
| 持续时间 | 最多72h |

## 4. RED 判定条件（任一满足即触发）

| # | 条件 | 阈值 | 阻断 |
|---|------|------|------|
| R01 | P0缺陷 | ≥1 | 立即阻断 |
| R02 | P1缺陷 | ≥1 | 立即阻断 |
| R03 | SHA256不一致 | 任一窗口 | 立即阻断 |
| R04 | 链断裂 | >0 | 立即阻断 |
| R05 | 去重率 | <100% | 立即阻断 |
| R06 | 丢包率 | >0.015% | 立即阻断 |
| R07 | WAL P99 | ≥2500ms | 立即阻断 |
| R08 | 索引P99 | ≥12ms | 立即阻断 |
| R09 | V87字段 | 任一FAIL | 立即阻断 |
| R10 | 膨胀速率 | >0.020pp | 立即阻断 |
| R11 | 模型偏差 | >20% | 立即阻断 |
| R12 | 退化趋势 | 确认退化 | 立即阻断 |

## 5. RED 阻断指令

### 5.1 阻断动作

```yaml
red_blocking_action:
  trigger: RED condition met
  actions:
    - action: stop_gray_traffic
      description: "停止灰度流量"
      priority: immediate
    - action: rollback_to_baseline
      description: "回滚至基线流量"
      priority: immediate
    - action: freeze_release
      description: "冻结发布"
      priority: immediate
    - action: notify_all
      description: "通知三方"
      targets: [DSHB, DSHE, HERMES]
    - action: create_incident
      description: "创建事故工单"
      severity: P0/P1
  recovery:
    - action: root_cause_analysis
      priority: high
    - action: fix_and_retry
      priority: high
    - action: gradual_reenable
      priority: normal
```

### 5.2 阻断通知

| 对象 | 通知方式 | 优先级 |
|------|---------|--------|
| DSHB | dingtalk+email | P0 |
| DSHE | dingtalk+pagerduty | P0 |
| HERMES | dingtalk+voice | P0 |
| 管理层 | email | P1 |

## 6. 判定流程

```
实时对账数据
    ↓
指标采集(8窗口/天)
    ↓
GO条件检查(12项)
    ↓
├── 全部满足 → GO → 继续灰度
├── 部分偏差 → COND-GO检查
│   ├── 满足COND条件 → COND-GO → 附约束继续
│   └── 不满足 → RED
└── 命中RED条件 → RED → 阻断回滚
```

## 7. 判定时间窗口

| 判定 | 时间窗口 | 频率 |
|------|---------|------|
| 实时指标 | 3h窗口 | 8次/天 |
| 膨胀趋势 | 24h | 1次/天 |
| 综合判定 | 24h | 1次/天 |
| RED触发 | 实时 | 即时 |

## 8. 判定示例

### 8.1 GO 示例

| 条件 | 值 | 判定 |
|------|---|------|
| SHA256 | 100% | ✅ |
| 链断裂 | 0 | ✅ |
| 膨胀速率 | 0.0155pp | ✅ |
| **综合** | — | **GO** |

### 8.2 COND-GO 示例

| 条件 | 值 | 判定 |
|------|---|------|
| 膨胀速率 | 0.019pp | ⚠️ |
| 其他11项 | 全PASS | ✅ |
| **综合** | — | **COND-GO**（降速30%） |

### 8.3 RED 示例

| 条件 | 值 | 判定 |
|------|---|------|
| 链断裂 | 1 | ❌ |
| **综合** | — | **RED**（阻断回滚） |

## 9. 与 DSHE 大盘对接

| 判定 | DSHE显示 | 动作 |
|------|---------|------|
| GO | 🟢 绿色 | 继续 |
| COND-GO | 🟡 黄色 | 关注 |
| RED | 🔴 红色 | 阻断 |

## 10. 结论

| 维度 | 结论 |
|------|------|
| GO条件 | 12项 |
| COND-GO | 6条件+约束 |
| RED条件 | 12项 |
| 阻断动作 | 4项+恢复 |
| 通知 | 三方+管理层 |
| 时间窗口 | 实时+24h |
| DSHE对接 | 三色状态 |
| **判定规则** | **已锁定** ✅ |

---

*关联: v87_rc1_hermes_phase02_v87_gate_risk_checklist.md*
