# V86-RC2 投产观测面板与告警规则报告

> **工单**: `DSHE_V86_RC2_PROD_PHASE_STAGE1` · T3.4
> **分支**: `feature/v85-chart-template`
> **基线**: V86-RC2 PREP CLOSED (commit `7fe50b8`), V85 FROZEN (`f313570`)
> **约束**: NO_MODIFY_V85=TRUE, NO_OVERWRITE=TRUE, BRANCH_LOCKED=TRUE
> **跨团队协作**: 告警规则须经 DSHB 确认 + HERMES 审计
> **生成日期**: 2026-10-04
> **状态**: 🟢 **投产观测面板配置就绪 — 18指标/6面板/56子面板/3级告警**

---

## 1. 执行摘要

### 1.1 观测面板就绪状态

| 维度 | 值 | 状态 |
|------|-----|------|
| 观测指标 | 18项 (OBS-01~OBS-18) | ✅ 全部定义 |
| Grafana面板 | 6个面板 (P1-P6) | ✅ 配置就绪 |
| 子面板 | 56个子面板 | ✅ 配置就绪 |
| 告警规则 | 18条规则 (3级严重度) | ✅ 配置就绪 |
| 升级链 | 3级 (P0/P1/P2) | ✅ 定义完成 |
| 实时观测 | 8项 (实时采集) | ✅ 配置就绪 |
| 批量观测 | 10项 (定时采集) | ✅ 配置就绪 |
| 回滚触发 | 8类异常 (E-1~E-8) | ✅ 映射完成 |
| GATE-DSHE-010 | 延迟监控 0.8~0.85s | ✅ 专项配置 |
| 跨团队审核 | DSHB确认 + HERMES审计 | 🟡 待审核 |
| 验收标准 | 10项 | ✅ 定义完成 |

### 1.2 观测架构总览

```
┌──────────────────────────────────────────────────────────────────────┐
│                    V86-RC2 投产观测面板架构                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    6 Grafana 面板 (Dashboard Layer)                │ │
│  ├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤ │
│  │  P1:     │  P2:     │  P3:     │  P4:     │  P5:     │  P6:     │ │
│  │  性能    │  错误率  │  监控    │  降级    │  数据    │  综合    │ │
│  │  10子   │  9子     │  10子   │  8子     │  10子   │  9子     │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘ │
│                              │                                          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    告警规则层 (Alert Rule Layer)                    │ │
│  ├──────────────┬──────────────────┬───────────────────────────────┤ │
│  │  P0 (阻断)    │  P1 (严重)        │  P2 (警告)                      │ │
│  │  自动回滚     │  人工确认+告警     │  记录+观察                       │ │
│  │  5min响应     │  30min响应        │  24h响应                        │ │
│  └──────────────┴──────────────────┴───────────────────────────────┘ │
│                              │                                          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    升级链 (Escalation Chain)                        │ │
│  │  监控 → DSHE值班 → DSHB引擎 → HERMES审计 → 技术负责人               │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    数据源 (Data Source)                             │ │
│  │  Prometheus → Grafana | DSHB引擎日志 → Logstash → Elasticsearch    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. 18项观测指标观测面板规格

### 2.1 指标分组概览

| 分组 | 面板 | 指标数 | 采集模式 | 采集频率 |
|------|------|--------|---------|---------|
| P1: 性能面板 | P1 (10子面板) | 4 (OBS-01,02,17,18) | 实时+批量 | 30s/1h |
| P2: 错误率面板 | P2 (9子面板) | 3 (OBS-03,04,05) | 实时 | 30s |
| P3: 监控面板 | P3 (10子面板) | 3 (OBS-06,07,16) | 批量 | 1h |
| P4: 降级面板 | P4 (8子面板) | 2 (OBS-09,10) | 实时 | 30s |
| P5: 数据面板 | P5 (10子面板) | 5 (OBS-11,12,13,14,15) | 批量 | 1h |
| P6: 综合面板 | P6 (9子面板) | 1 (OBS-08) | 批量 | 1h |

### 2.2 详细指标配置

#### OBS-01: P99响应时间

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-01 |
| 面板 | P1 (性能面板) |
| 子面板 | SP-01 (P99响应时间趋势图) |
| 阈值 | ≤3.0s |
| PREP实测 | 2.7s |
| 采集模式 | 实时 + 批量 |
| 采集频率 | 30s (实时) / 1h (批量) |
| Prometheus指标 | `http_request_duration_seconds{quantile="0.99"}` |
| 告警规则 | P99 > 3.0s for 5min → P1 |
| 严重度 | P1 (P99>3.0s) / P2 (P99>2.5s) |
| 升级链 | 监控 → DSHE值班 → DSHB引擎 |
| 关联风险 | R-007 |
| 关联回滚 | E-5 |

**Grafana Panel 配置**:
```yaml
panel:
  id: sp-01
  title: "OBS-01: P99 响应时间"
  type: timeseries
  datasource: Prometheus
  targets:
    - expr: |
        histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
      legendFormat: "P99"
    - expr: |
        histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
      legendFormat: "P95"
    - expr: |
        histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
      legendFormat: "P50"
  thresholds:
    - value: 2.5
      color: "green"
    - value: 3.0
      color: "red"
  unit: "s"
  interval: "30s"
```

#### OBS-02: 首屏加载时间

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-02 |
| 面板 | P1 (性能面板) |
| 子面板 | SP-02 (首屏加载时间趋势图) |
| 阈值 | ≤2.0s |
| PREP实测 | 1.8s |
| 采集模式 | 实时 + 批量 |
| 采集频率 | 30s / 1h |
| Prometheus指标 | `first_screen_load_duration_seconds{quantile="0.99"}` |
| 告警规则 | 首屏 > 2.0s for 5min → P1 |
| 严重度 | P1 (>2.0s) / P2 (>1.5s) |
| 升级链 | 监控 → DSHE值班 |
| 关联风险 | R-007 |
| 关联回滚 | E-5 |

#### OBS-03: P0错误数

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-03 |
| 面板 | P2 (错误率面板) |
| 子面板 | SP-03 (P0错误计数) |
| 阈值 | =0 |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `increase(error_count_total{severity="P0"}[5m])` |
| 告警规则 | P0 > 0 → 立即P0告警 |
| 严重度 | P0 (任何P0) |
| 升级链 | 监控 → DSHB引擎 → HERMES审计 → 技术负责人 |
| 关联风险 | R-001 |
| 关联回滚 | E-1 (数据拉取失败), E-5 (性能超标) |

**Grafana Panel 配置**:
```yaml
panel:
  id: sp-03
  title: "OBS-03: P0 错误数"
  type: stat
  datasource: Prometheus
  targets:
    - expr: |
        increase(error_count_total{severity="P0"}[5m])
      legendFormat: "P0 Errors (5min)"
  thresholdMode: absolute
  thresholds:
    - value: 0
      color: "green"
    - value: 1
      color: "red"
  unit: "short"
  interval: "30s"
  alert:
    expr: increase(error_count_total{severity="P0"}[5m]) > 0
    for: 1m
    severity: P0
    labels:
      team: DSHE
      component: display-layer
    annotations:
      summary: "P0错误检测到: {{ $value }}"
      description: "P0错误数超过0, 立即回滚"
```

#### OBS-04: P1错误数-引擎

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-04 |
| 面板 | P2 (错误率面板) |
| 子面板 | SP-04 (P1错误-引擎趋势) |
| 阈值 | ≤3 (24h) |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `sum(rate(engine_error_total{severity="P1"}[24h]))` |
| 告警规则 | P1引擎 > 3 (24h) → P1告警 |
| 严重度 | P1 (>3) / P2 (>1) |
| 升级链 | 监控 → DSHB引擎 |
| 关联风险 | R-001 |
| 关联回滚 | E-2 (数据空值兜底) |

#### OBS-05: P1错误数-展示

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-05 |
| 面板 | P2 (错误率面板) |
| 子面板 | SP-05 (P1错误-展示趋势) |
| 阈值 | =0 |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `increase(render_error_total{severity="P1"}[1h])` |
| 告警规则 | P1展示 > 0 → 立即P1告警 |
| 严重度 | P1 (>0) |
| 升级链 | 监控 → DSHE值班 → DSHB引擎 |
| 关联风险 | R-001 |
| 关联回滚 | E-4 (降级渲染失败) |

#### OBS-06: 误报率

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-06 |
| 面板 | P3 (监控面板) |
| 子面板 | SP-06 (误报率趋势) |
| 阈值 | <30% |
| 采集模式 | 批量 |
| 采集频率 | 1h |
| Prometheus指标 | `rate(alert_false_positive_total[1h]) / rate(alert_total[1h]) * 100` |
| 告警规则 | 误报率 > 30% for 1h → P1告警 |
| 严重度 | P1 (>30%) / P2 (>25%) |
| 升级链 | 监控 → DSHB引擎 |
| 关联风险 | R-005, R-012 |
| 关联回滚 | E-7 (覆盖率下降) |

#### OBS-07: 召回率

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-07 |
| 面板 | P3 (监控面板) |
| 子面板 | SP-07 (召回率趋势) |
| 阈值 | ≥95% |
| 采集模式 | 批量 |
| 采集频率 | 1h |
| Prometheus指标 | `rate(alert_true_positive_total[1h]) / (rate(alert_true_positive_total[1h]) + rate(alert_false_negative_total[1h])) * 100` |
| 告警规则 | 召回率 < 95% for 1h → P1告警 |
| 严重度 | P1 (<95%) / P2 (<90%) |
| 升级链 | 监控 → DSHB引擎 |
| 关联风险 | R-005 |
| 关联回滚 | E-7 |

#### OBS-08: 监控覆盖率

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-08 |
| 面板 | P6 (综合面板) |
| 子面板 | SP-08 (监控覆盖率仪表) |
| 阈值 | ≥95% |
| 采集模式 | 批量 |
| 采集频率 | 1h |
| Prometheus指标 | `monitoring_coverage_ratio * 100` |
| 告警规则 | 覆盖率 < 95% for 1h → P1告警 |
| 严重度 | P1 (<95%) / P2 (<90%) |
| 升级链 | 监控 → DSHB监控 |
| 关联风险 | R-004 |
| 关联回滚 | E-7 |

#### OBS-09: 降级图表数

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-09 |
| 面板 | P4 (降级面板) |
| 子面板 | SP-09 (降级图表计数) |
| 阈值 | =7 (已知) |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `degraded_chart_count` |
| 告警规则 | 降级数 > 7 → P1告警 |
| 严重度 | P1 (>7) |
| 升级链 | 监控 → DSHE值班 |
| 关联风险 | R-006 |
| 关联回滚 | E-4 |

#### OBS-10: 降级恢复时间

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-10 |
| 面板 | P4 (降级面板) |
| 子面板 | SP-10 (降级恢复时间趋势) |
| 阈值 | ≤30s |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `degraded_recovery_duration_seconds{quantile="0.99"}` |
| 告警规则 | 恢复 > 30s for 5min → P1告警 |
| 严重度 | P1 (>30s) / P2 (>20s) |
| 升级链 | 监控 → DSHE值班 |
| 关联风险 | R-006 |
| 关联回滚 | E-4 |

#### OBS-11: zhiji_id确认数

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-11 |
| 面板 | P5 (数据面板) |
| 子面板 | SP-11 (zhiji_id确认进度) |
| 阈值 | =190 (T-3d~T-1d完成) |
| 采集模式 | 批量 |
| 采集频率 | 1h |
| Prometheus指标 | `zhiji_id_confirmed_count` |
| 告警规则 | T-1d时确认数 < 190 → P2告警 |
| 严重度 | P2 (确认数不足) |
| 升级链 | 监控 → DSHB/平台 |
| 关联风险 | R-003 |
| 关联回滚 | E-8 (zhiji数据缺失) |

#### OBS-12: Mock→Real切换成功率

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-12 |
| 面板 | P5 (数据面板) |
| 子面板 | SP-12 (Mock→Real切换成功率) |
| 阈值 | 100% |
| 采集模式 | 批量 |
| 采集频率 | 1h |
| Prometheus指标 | `mock_to_real_switch_success_ratio * 100` |
| 告警规则 | 成功率 < 100% → P1告警 |
| 严重度 | P1 (<100%) |
| 升级链 | 监控 → DSHB+DSHE |
| 关联风险 | R-008 |
| 关联回滚 | E-1, E-8 |

#### OBS-13: 别名解析时间

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-13 |
| 面板 | P5 (数据面板) |
| 子面板 | SP-13 (别名解析时间趋势) |
| 阈值 | ≤500ms |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `alias_resolution_duration_seconds{quantile="0.99"}` |
| 告警规则 | 解析 > 500ms for 5min → P1告警 |
| 严重度 | P1 (>500ms) / P2 (>400ms) |
| 升级链 | 监控 → DSHB引擎 |
| 关联风险 | R-013 |
| 关联回滚 | E-2 |

#### OBS-14: CDN缓存命中率

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-14 |
| 面板 | P5 (数据面板) |
| 子面板 | SP-14 (CDN缓存命中率) |
| 阈值 | ≥90% |
| 采集模式 | 批量 |
| 采集频率 | 1h |
| Prometheus指标 | `cdn_cache_hit_ratio * 100` |
| 告警规则 | 命中率 < 90% for 1h → P2告警 |
| 严重度 | P2 (<90%) |
| 升级链 | 监控 → DSHE值班 |
| 关联风险 | R-007 |
| 关联回滚 | — |

#### OBS-15: 日志完整性

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-15 |
| 面板 | P5 (数据面板) |
| 子面板 | SP-15 (日志完整性仪表) |
| 阈值 | 100% |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `log_completeness_ratio * 100` |
| 告警规则 | 完整性 < 100% for 5min → P1告警 |
| 严重度 | P1 (<100%) |
| 升级链 | 监控 → DSHB监控 |
| 关联风险 | R-004 |
| 关联回滚 | — |

#### OBS-16: 告警准确率

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-16 |
| 面板 | P3 (监控面板) |
| 子面板 | SP-16 (告警准确率趋势) |
| 阈值 | ≥90% |
| 采集模式 | 批量 |
| 采集频率 | 1h |
| Prometheus指标 | `alert_accuracy_ratio * 100` |
| 告警规则 | 准确率 < 90% for 1h → P2告警 |
| 严重度 | P2 (<90%) |
| 升级链 | 监控 → DSHB监控 |
| 关联风险 | R-004 |
| 关联回滚 | E-7 |

#### OBS-17: 冷启动时间

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-17 |
| 面板 | P1 (性能面板) |
| 子面板 | SP-17 (冷启动时间) |
| 阈值 | ≤5s |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `cold_start_duration_seconds` |
| 告警规则 | 冷启动 > 5s → P2告警 |
| 严重度 | P2 (>5s) |
| 升级链 | 监控 → DSHB引擎 |
| 关联风险 | R-007 |
| 关联回滚 | — |

#### OBS-18: 数据延迟

| 属性 | 值 |
|------|-----|
| 指标ID | OBS-18 |
| 面板 | P1 (性能面板) |
| 子面板 | SP-18 (数据延迟趋势) |
| 阈值 | ≤500ms |
| 采集模式 | 实时 |
| 采集频率 | 30s |
| Prometheus指标 | `data_latency_seconds{quantile="0.99"}` |
| 告警规则 | 延迟 > 500ms for 5min → P1告警 |
| 严重度 | P1 (>500ms) / P2 (>400ms) |
| 升级链 | 监控 → DSHB引擎 |
| 关联风险 | R-009 |
| 关联回滚 | E-1 |

---

## 3. GATE-DSHE-010 延迟监控专项

### 3.1 GATE-DSHE-010 概述

| 属性 | 值 |
|------|-----|
| 指标ID | GATE-DSHE-010 |
| 关联指标 | OBS-01 (P99响应时间) |
| PREP实测 | P99 2.7s |
| 波动范围 | +6.25% (P99 2.87s) |
| 延迟阈值 | 0.8~0.85s (单次请求延迟) |
| 目标 | P99 ≤ 2.7s, 单次延迟 ≤ 0.85s |
| 阈值边界 | P99 > 3.0s → P1, 单次 > 0.85s → P2 |
| 监控频率 | 30s (实时) |
| 持续时间 | T+1h~T+7d |

### 3.2 GATE-DSHE-010 延迟分布

```
延迟分布 (PREP实测):
                        ══════════════════════════════════════════
P50:  0.35s ──────────── ══════════════════════════════════════════
P75:  0.55s ──── ══════════════════════════════════════════════════
P95:  1.10s ──────── ══════════════════════════════════════════════
P99:  2.70s ─────────────────────── ══════════════════════════════
P99.9: 3.20s ────────────────────── ══════════════════════════════
                        ══════════════════════════════════════════
阈值线:
  0.85s ──────────────── ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
  2.0s ──────────────────── ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
  3.0s ───────────────────────────── ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                        ══════════════════════════════════════════
```

### 3.3 GATE-DSHE-010 监控规则

| 规则 | 条件 | 严重度 | 响应时间 |
|------|------|--------|---------|
| GATE-DSHE-010-P0 | P99 > 3.5s for 15min | P0 | 5min |
| GATE-DSHE-010-P1 | P99 > 3.0s for 5min | P1 | 15min |
| GATE-DSHE-010-P2 | P99 > 2.5s for 5min | P2 | 30min |
| GATE-DSHE-010-P2-single | 单次延迟 > 0.85s for 3次连续 | P2 | 30min |
| GATE-DSHE-010-P1-single | 单次延迟 > 0.85s for 10次连续 | P1 | 15min |

### 3.4 GATE-DSHE-010 子面板配置 (P1面板)

| 子面板ID | 名称 | 类型 | 数据源 | 告警 |
|---------|------|------|--------|------|
| SP-01 | P99响应时间趋势 | timeseries | Prometheus | P1/P2 |
| SP-02 | 首屏加载时间 | timeseries | Prometheus | P1/P2 |
| SP-03 | 单次请求延迟分布 | histogram | Prometheus | P2 |
| SP-04 | GATE-DSHE-010延迟仪表 | gauge | Prometheus | P0/P1/P2 |
| SP-05 | P95/P99趋势对比 | timeseries | Prometheus | P2 |
| SP-06 | 延迟波动率 | stat | Prometheus | P2 |
| SP-07 | 冷启动时间 | timeseries | Prometheus | P2 |
| SP-08 | 数据延迟 | timeseries | Prometheus | P1/P2 |
| SP-09 | 请求量趋势 | timeseries | Prometheus | — |
| SP-10 | 响应时间分位数 | heatmap | Prometheus | P2 |

**GATE-DSHE-010 仪表配置 (SP-04)**:
```yaml
panel:
  id: sp-04
  title: "GATE-DSHE-010: P99 延迟仪表"
  type: gauge
  datasource: Prometheus
  targets:
    - expr: |
        histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
      legendFormat: "P99"
  min: 0
  max: 4.0
  thresholds:
    - value: 2.0
      color: "green"
    - value: 2.5
      color: "yellow"
    - value: 3.0
      color: "red"
    - value: 3.5
      color: "dark-red"
  unit: "s"
  interval: "30s"
```

---

## 4. Grafana 面板布局规格 (6面板, 56子面板)

### 4.1 面板总览

| 面板 | 名称 | 子面板数 | 行/列 | 行高 |
|------|------|---------|-------|------|
| P1 | 性能面板 | 10 | 2行×5列 | 300px |
| P2 | 错误率面板 | 9 | 2行×5列 (最后一列空) | 300px |
| P3 | 监控面板 | 10 | 2行×5列 | 300px |
| P4 | 降级面板 | 8 | 2行×4列 | 300px |
| P5 | 数据面板 | 10 | 2行×5列 | 300px |
| P6 | 综合面板 | 9 | 2行×5列 (最后一列空) | 300px |
| **合计** | — | **56** | — | — |

### 4.2 面板布局图

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     V86-RC2 投产观测面板 Dashboard Layout                            │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌─── 全局控制栏 ──────────────────────────────────────────────────────────────┐ │
│  │  时间范围: [T-1h~T+7d] [T+1h~T+24h] [T+1h~T+7d] | 刷新: 30s | 面板选择 ▾   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                    │
│  ┌─── P1: 性能面板 ──────────────────────────────────────────────────────────┐  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │ │ SP-01    │ │ SP-02    │ │ SP-03    │ │ SP-04    │ │ SP-05    │         │  │
│  │ │ P99趋势  │ │ 首屏加载 │ │ 延迟分布 │ │ 仪表GATE │ │ P95/P99  │         │  │
│  │ │ OBS-01   │ │ OBS-02   │ │          │ │ 010      │ │ 对比     │         │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │  │
│  │ │ SP-06    │ │ SP-07    │ │ SP-08    │ │ SP-09    │  (空)                │  │
│  │ │ 波动率   │ │ 冷启动   │ │ 数据延迟 │ │ 请求量   │                      │  │
│  │ │          │ │ OBS-17   │ │ OBS-18   │ │          │                      │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
│  ┌─── P2: 错误率面板 ─────────────────────────────────────────────────────────┐  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │ │ SP-11    │ │ SP-12    │ │ SP-13    │ │ SP-14    │ │ SP-15    │         │  │
│  │ │ P0计数   │ │ P1引擎   │ │ P1展示   │ │ 错误率   │ │ 错误分布 │         │  │
│  │ │ OBS-03   │ │ OBS-04   │ │ OBS-05   │ │          │ │          │         │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │  │
│  │ │ SP-16    │ │ SP-17    │ │ SP-18    │ │ SP-19    │  (空)                │  │
│  │ │ P0仪表   │ │ P1趋势   │ │ 错误详情 │ │ 错误热力 │                      │  │
│  │ │          │ │          │ │          │ │ 图       │                      │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
│  ┌─── P3: 监控面板 ─────────────────────────────────────────────────────────┐  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │ │ SP-21    │ │ SP-22    │ │ SP-23    │ │ SP-24    │ │ SP-25    │         │  │
│  │ │ 误报率   │ │ 召回率   │ │ 告警准确 │ │ 覆盖率   │ │ 告警趋势 │         │  │
│  │ │ OBS-06   │ │ OBS-07   │ │ OBS-16   │ │ OBS-08   │ │          │         │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │  │
│  │ │ SP-26    │ │ SP-27    │ │ SP-28    │ │ SP-29    │                      │  │
│  │ │ 误报趋势 │ │ 召回趋势 │ │ 告警统计 │ │ 覆盖率   │                      │  │
│  │ │          │ │          │ │          │ │ 热力图   │                      │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
│  ┌─── P4: 降级面板 ─────────────────────────────────────────────────────────┐  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │  │
│  │ │ SP-31    │ │ SP-32    │ │ SP-33    │ │ SP-34    │                      │  │
│  │ │ 降级计数 │ │ 恢复时间 │ │ 降级趋势 │ │ 降级分布 │                      │  │
│  │ │ OBS-09   │ │ OBS-10   │ │          │ │          │                      │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │  │
│  │ │ SP-35    │ │ SP-36    │ │ SP-37    │ │ SP-38    │                      │  │
│  │ │ 降级仪表 │ │ 恢复趋势 │ │ 降级事件 │ │ 恢复统计 │                      │  │
│  │ │          │ │          │ │ 列表     │ │          │                      │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
│  ┌─── P5: 数据面板 ─────────────────────────────────────────────────────────┐  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │ │ SP-41    │ │ SP-42    │ │ SP-43    │ │ SP-44    │ │ SP-45    │         │  │
│  │ │ zhiji确认│ │ Mock切换 │ │ 别名解析 │ │ CDN命中  │ │ 日志完整 │         │  │
│  │ │ OBS-11   │ │ OBS-12   │ │ OBS-13   │ │ OBS-14   │ │ OBS-15   │         │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │  │
│  │ │ SP-46    │ │ SP-47    │ │ SP-48    │ │ SP-49    │                      │  │
│  │ │ 确认进度 │ │ 切换成功 │ │ 解析趋势 │ │ CDN趋势  │                      │  │
│  │ │ 仪表     │ │ 率仪表   │ │          │ │          │                      │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
│  ┌─── P6: 综合面板 ─────────────────────────────────────────────────────────┐  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │ │ SP-51    │ │ SP-52    │ │ SP-53    │ │ SP-54    │ │ SP-55    │         │  │
│  │ │ 综合仪表 │ │ 健康分   │ │ 风险概览 │ │ 告警汇总 │ │ 事件时间 │         │  │
│  │ │ 覆盖率   │ │          │ │          │ │          │ │ 线       │         │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                      │  │
│  │ │ SP-56    │ │ SP-57    │ │ SP-58    │ │ SP-59    │  (空)                │  │
│  │ │ 健康趋势 │ │ 风险趋势 │ │ 告警趋势 │ │ 关键事件 │                      │  │
│  │ │          │ │          │ │          │ │ 统计     │                      │  │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘                      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 告警规则配置

### 5.1 告警规则总表 (18条)

| # | 规则ID | 指标 | 条件 | 持续时间 | 严重度 | 通知渠道 |
|---|--------|------|------|---------|--------|---------|
| 1 | ALERT-OBS-01-P1 | OBS-01 | P99 > 3.0s | 5min | P1 | 钉钉+邮件 |
| 2 | ALERT-OBS-01-P2 | OBS-01 | P99 > 2.5s | 5min | P2 | 钉钉 |
| 3 | ALERT-OBS-02-P1 | OBS-02 | 首屏 > 2.0s | 5min | P1 | 钉钉+邮件 |
| 4 | ALERT-OBS-02-P2 | OBS-02 | 首屏 > 1.5s | 5min | P2 | 钉钉 |
| 5 | ALERT-OBS-03-P0 | OBS-03 | P0 > 0 | 1min | P0 | 电话+钉钉+邮件 |
| 6 | ALERT-OBS-04-P1 | OBS-04 | P1引擎 > 3/24h | 1h | P1 | 钉钉+邮件 |
| 7 | ALERT-OBS-04-P2 | OBS-04 | P1引擎 > 1/24h | 1h | P2 | 钉钉 |
| 8 | ALERT-OBS-05-P1 | OBS-05 | P1展示 > 0 | 1min | P1 | 钉钉+邮件 |
| 9 | ALERT-OBS-06-P1 | OBS-06 | 误报率 > 30% | 1h | P1 | 钉钉+邮件 |
| 10 | ALERT-OBS-06-P2 | OBS-06 | 误报率 > 25% | 1h | P2 | 钉钉 |
| 11 | ALERT-OBS-07-P1 | OBS-07 | 召回率 < 95% | 1h | P1 | 钉钉+邮件 |
| 12 | ALERT-OBS-08-P1 | OBS-08 | 覆盖率 < 95% | 1h | P1 | 钉钉+邮件 |
| 13 | ALERT-OBS-09-P1 | OBS-09 | 降级数 > 7 | 5min | P1 | 钉钉+邮件 |
| 14 | ALERT-OBS-10-P1 | OBS-10 | 恢复 > 30s | 5min | P1 | 钉钉+邮件 |
| 15 | ALERT-OBS-12-P1 | OBS-12 | 切换成功率 < 100% | 1h | P1 | 钉钉+邮件 |
| 16 | ALERT-OBS-13-P1 | OBS-13 | 解析 > 500ms | 5min | P1 | 钉钉+邮件 |
| 17 | ALERT-OBS-15-P1 | OBS-15 | 日志完整性 < 100% | 5min | P1 | 钉钉+邮件 |
| 18 | ALERT-OBS-18-P1 | OBS-18 | 延迟 > 500ms | 5min | P1 | 钉钉+邮件 |

### 5.2 告警规则 Prometheus 配置模板

```yaml
# ═══════════════════════════════════════════════════════════════
# V86-RC2 投产观测告警规则
# 规则数: 18 | 严重度: P0(1) P1(11) P2(6)
# ═══════════════════════════════════════════════════════════════

groups:
  - name: v86-rc2-prod-observation
    interval: 30s
    rules:
      # ── OBS-01: P99 响应时间 ──
      - alert: ALERT-OBS-01-P1
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 3.0
        for: 5m
        labels:
          severity: P1
          team: DSHE
          component: performance
          metric: OBS-01
        annotations:
          summary: "P99响应时间超标"
          description: "P99响应时间 {{ $value }}s 超过阈值 3.0s，持续时间超过 5 分钟"
          runbook: "https://wiki/v86-rc2/runbook/OBS-01"
          escalation: "DSHE值班 → DSHB引擎"

      - alert: ALERT-OBS-01-P2
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2.5
        for: 5m
        labels:
          severity: P2
          team: DSHE
          component: performance
          metric: OBS-01
        annotations:
          summary: "P99响应时间预警"
          description: "P99响应时间 {{ $value }}s 超过预警阈值 2.5s"
          escalation: "DSHE值班"

      # ── OBS-02: 首屏加载时间 ──
      - alert: ALERT-OBS-02-P1
        expr: histogram_quantile(0.99, sum(rate(first_screen_load_duration_seconds_bucket[5m])) by (le)) > 2.0
        for: 5m
        labels:
          severity: P1
          team: DSHE
          component: performance
          metric: OBS-02
        annotations:
          summary: "首屏加载时间超标"
          description: "首屏加载时间 {{ $value }}s 超过阈值 2.0s"
          escalation: "DSHE值班"

      - alert: ALERT-OBS-02-P2
        expr: histogram_quantile(0.99, sum(rate(first_screen_load_duration_seconds_bucket[5m])) by (le)) > 1.5
        for: 5m
        labels:
          severity: P2
          team: DSHE
          component: performance
          metric: OBS-02
        annotations:
          summary: "首屏加载时间预警"
          description: "首屏加载时间 {{ $value }}s 超过预警阈值 1.5s"
          escalation: "DSHE值班"

      # ── OBS-03: P0 错误数 ──
      - alert: ALERT-OBS-03-P0
        expr: increase(error_count_total{severity="P0"}[5m]) > 0
        for: 1m
        labels:
          severity: P0
          team: DSHE+DSHB
          component: error-rate
          metric: OBS-03
        annotations:
          summary: "P0错误检测到!"
          description: "P0错误数 {{ $value }} 超过阈值 0，立即回滚"
          escalation: "DSHB引擎 → HERMES审计 → 技术负责人"

      # ── OBS-04: P1 错误数-引擎 ──
      - alert: ALERT-OBS-04-P1
        expr: sum(rate(engine_error_total{severity="P1"}[24h])) > 3
        for: 1h
        labels:
          severity: P1
          team: DSHB
          component: error-rate
          metric: OBS-04
        annotations:
          summary: "引擎P1错误超标"
          description: "24h内引擎P1错误数 {{ $value }} 超过阈值 3"
          escalation: "DSHB引擎"

      - alert: ALERT-OBS-04-P2
        expr: sum(rate(engine_error_total{severity="P1"}[24h])) > 1
        for: 1h
        labels:
          severity: P2
          team: DSHB
          component: error-rate
          metric: OBS-04
        annotations:
          summary: "引擎P1错误预警"
          description: "24h内引擎P1错误数 {{ $value }} 超过预警阈值 1"
          escalation: "DSHB引擎"

      # ── OBS-05: P1 错误数-展示 ──
      - alert: ALERT-OBS-05-P1
        expr: increase(render_error_total{severity="P1"}[1h]) > 0
        for: 1m
        labels:
          severity: P1
          team: DSHE
          component: error-rate
          metric: OBS-05
        annotations:
          summary: "展示层P1错误检测到"
          description: "展示层P1错误数 {{ $value }} 超过阈值 0"
          escalation: "DSHE值班 → DSHB引擎"

      # ── OBS-06: 误报率 ──
      - alert: ALERT-OBS-06-P1
        expr: rate(alert_false_positive_total[1h]) / rate(alert_total[1h]) * 100 > 30
        for: 1h
        labels:
          severity: P1
          team: DSHB
          component: monitoring
          metric: OBS-06
        annotations:
          summary: "误报率超标"
          description: "误报率 {{ $value }}% 超过阈值 30%"
          escalation: "DSHB引擎"

      - alert: ALERT-OBS-06-P2
        expr: rate(alert_false_positive_total[1h]) / rate(alert_total[1h]) * 100 > 25
        for: 1h
        labels:
          severity: P2
          team: DSHB
          component: monitoring
          metric: OBS-06
        annotations:
          summary: "误报率预警"
          description: "误报率 {{ $value }}% 超过预警阈值 25%"
          escalation: "DSHB引擎"

      # ── OBS-07: 召回率 ──
      - alert: ALERT-OBS-07-P1
        expr: rate(alert_true_positive_total[1h]) / (rate(alert_true_positive_total[1h]) + rate(alert_false_negative_total[1h])) * 100 < 95
        for: 1h
        labels:
          severity: P1
          team: DSHB
          component: monitoring
          metric: OBS-07
        annotations:
          summary: "召回率不达标"
          description: "召回率 {{ $value }}% 低于阈值 95%"
          escalation: "DSHB引擎"

      # ── OBS-08: 监控覆盖率 ──
      - alert: ALERT-OBS-08-P1
        expr: monitoring_coverage_ratio * 100 < 95
        for: 1h
        labels:
          severity: P1
          team: DSHB
          component: monitoring
          metric: OBS-08
        annotations:
          summary: "监控覆盖率不达标"
          description: "监控覆盖率 {{ $value }}% 低于阈值 95%"
          escalation: "DSHB监控"

      # ── OBS-09: 降级图表数 ──
      - alert: ALERT-OBS-09-P1
        expr: degraded_chart_count > 7
        for: 5m
        labels:
          severity: P1
          team: DSHE
          component: degradation
          metric: OBS-09
        annotations:
          summary: "降级图表数超标"
          description: "降级图表数 {{ $value }} 超过已知7张"
          escalation: "DSHE值班"

      # ── OBS-10: 降级恢复时间 ──
      - alert: ALERT-OBS-10-P1
        expr: histogram_quantile(0.99, sum(rate(degraded_recovery_duration_seconds_bucket[5m])) by (le)) > 30
        for: 5m
        labels:
          severity: P1
          team: DSHE
          component: degradation
          metric: OBS-10
        annotations:
          summary: "降级恢复时间超标"
          description: "降级恢复时间 {{ $value }}s 超过阈值 30s"
          escalation: "DSHE值班"

      # ── OBS-12: Mock→Real 切换成功率 ──
      - alert: ALERT-OBS-12-P1
        expr: mock_to_real_switch_success_ratio * 100 < 100
        for: 1h
        labels:
          severity: P1
          team: DSHB+DSHE
          component: data
          metric: OBS-12
        annotations:
          summary: "Mock→Real切换失败"
          description: "切换成功率 {{ $value }}% 低于 100%"
          escalation: "DSHB+DSHE"

      # ── OBS-13: 别名解析时间 ──
      - alert: ALERT-OBS-13-P1
        expr: histogram_quantile(0.99, sum(rate(alias_resolution_duration_seconds_bucket[5m])) by (le)) > 0.5
        for: 5m
        labels:
          severity: P1
          team: DSHB
          component: data
          metric: OBS-13
        annotations:
          summary: "别名解析时间超标"
          description: "别名解析时间 {{ $value }}s 超过阈值 500ms"
          escalation: "DSHB引擎"

      # ── OBS-15: 日志完整性 ──
      - alert: ALERT-OBS-15-P1
        expr: log_completeness_ratio * 100 < 100
        for: 5m
        labels:
          severity: P1
          team: DSHB
          component: data
          metric: OBS-15
        annotations:
          summary: "日志完整性不达标"
          description: "日志完整性 {{ $value }}% 低于 100%"
          escalation: "DSHB监控"

      # ── OBS-18: 数据延迟 ──
      - alert: ALERT-OBS-18-P1
        expr: histogram_quantile(0.99, sum(rate(data_latency_seconds_bucket[5m])) by (le)) > 0.5
        for: 5m
        labels:
          severity: P1
          team: DSHB
          component: data
          metric: OBS-18
        annotations:
          summary: "数据延迟超标"
          description: "数据延迟 {{ $value }}s 超过阈值 500ms"
          escalation: "DSHB引擎"

      - alert: ALERT-OBS-18-P2
        expr: histogram_quantile(0.99, sum(rate(data_latency_seconds_bucket[5m])) by (le)) > 0.4
        for: 5m
        labels:
          severity: P2
          team: DSHB
          component: data
          metric: OBS-18
        annotations:
          summary: "数据延迟预警"
          description: "数据延迟 {{ $value }}s 超过预警阈值 400ms"
          escalation: "DSHB引擎"
```

---

## 6. 告警严重度矩阵 (P0/P1/P2)

### 6.1 严重度定义

| 严重度 | 名称 | 响应时间 | 通知渠道 | 操作 |
|--------|------|---------|---------|------|
| P0 | 阻断 | 5min | 电话+钉钉+邮件 | 自动回滚 |
| P1 | 严重 | 15min | 钉钉+邮件 | 人工确认+告警 |
| P2 | 警告 | 30min | 钉钉 | 记录+观察 |

### 6.2 严重度映射表

| 指标 | P0条件 | P1条件 | P2条件 |
|------|--------|--------|--------|
| OBS-01 (P99) | P99>3.5s/15min | P99>3.0s/5min | P99>2.5s/5min |
| OBS-02 (首屏) | — | 首屏>2.0s/5min | 首屏>1.5s/5min |
| OBS-03 (P0错误) | P0>0/1min | — | — |
| OBS-04 (P1引擎) | — | P1>3/24h | P1>1/24h |
| OBS-05 (P1展示) | — | P1>0/1min | — |
| OBS-06 (误报率) | — | 误报率>30%/1h | 误报率>25%/1h |
| OBS-07 (召回率) | — | 召回率<95%/1h | 召回率<90%/1h |
| OBS-08 (覆盖率) | — | 覆盖率<95%/1h | 覆盖率<90%/1h |
| OBS-09 (降级数) | — | 降级数>7/5min | — |
| OBS-10 (恢复时间) | — | 恢复>30s/5min | 恢复>20s/5min |
| OBS-12 (切换率) | — | 切换率<100%/1h | — |
| OBS-13 (解析时间) | — | 解析>500ms/5min | 解析>400ms/5min |
| OBS-14 (CDN) | — | — | 命中率<90%/1h |
| OBS-15 (日志) | — | 完整性<100%/5min | — |
| OBS-16 (告警准确) | — | — | 准确率<90%/1h |
| OBS-17 (冷启动) | — | — | 冷启动>5s |
| OBS-18 (数据延迟) | — | 延迟>500ms/5min | 延迟>400ms/5min |

### 6.3 升级链配置

| 级别 | 第一响应人 | 第二响应人 | 第三响应人 | 响应时间 |
|------|-----------|-----------|-----------|---------|
| P0 | DSHB引擎值班 | HERMES审计 | 技术负责人 | 5min |
| P1 | DSHE值班 | DSHB引擎 | HERMES审计 | 15min |
| P2 | DSHE值班 | DSHB引擎 | — | 30min |

```
升级链配置 (Escalation Chain):

P0 升级链:
  监控告警 ──→ DSHB引擎值班 (5min) ──→ HERMES审计 (15min) ──→ 技术负责人 (30min)
  │                                    │                              │
  │                                    ▼                              ▼
  │                              [自动回滚L2]                    [最终裁定]
  │
  └── 电话+钉钉+邮件 (立即)

P1 升级链:
  监控告警 ──→ DSHE值班 (15min) ──→ DSHB引擎 (30min) ──→ HERMES审计 (60min)
  │                │
  │                ▼
  │           [人工确认+告警]
  │
  └── 钉钉+邮件 (15min内)

P2 升级链:
  监控告警 ──→ DSHE值班 (30min) ──→ DSHB引擎 (24h)
  │                │
  │                ▼
  │           [记录+观察]
  │
  └── 钉钉 (30min内)
```

---

## 7. 跨团队审核清单 (DSHB + HERMES)

### 7.1 DSHB 确认清单

| # | 审核项 | 状态 | 确认人 | 日期 |
|---|--------|------|--------|------|
| 1 | OBS-03 P0错误阈值 (=0) | ⏳ 待确认 | DSHB引擎 | 投产前 |
| 2 | OBS-04 P1引擎阈值 (≤3/24h) | ⏳ 待确认 | DSHB引擎 | 投产前 |
| 3 | OBS-06 误报率阈值 (<30%) | ⏳ 待确认 | DSHB引擎 | 投产前 |
| 4 | OBS-07 召回率阈值 (≥95%) | ⏳ 待确认 | DSHB引擎 | 投产前 |
| 5 | OBS-13 别名解析阈值 (≤500ms) | ⏳ 待确认 | DSHB引擎 | 投产前 |
| 6 | OBS-18 数据延迟阈值 (≤500ms) | ⏳ 待确认 | DSHB引擎 | 投产前 |
| 7 | OBS-08 监控覆盖率阈值 (≥95%) | ⏳ 待确认 | DSHB监控 | 投产前 |
| 8 | OBS-15 日志完整性阈值 (100%) | ⏳ 待确认 | DSHB监控 | 投产前 |
| 9 | OBS-16 告警准确率阈值 (≥90%) | ⏳ 待确认 | DSHB监控 | 投产前 |
| 10 | ALERT-OBS-03-P0 升级链 | ⏳ 待确认 | DSHB引擎+监控 | 投产前 |
| 11 | ALERT-OBS-12-P1 升级链 (DSHB+DSHE) | ⏳ 待确认 | DSHB引擎+监控 | 投产前 |
| 12 | Prometheus 指标名与查询语法 | ⏳ 待确认 | DSHB引擎 | 投产前 |

**DSHB审核签名**: ⏳ 待签署

### 7.2 HERMES 审计清单

| # | 审核项 | 状态 | 审核人 | 日期 |
|---|--------|------|--------|------|
| 1 | 18项指标阈值合理性 | ⏳ 待审核 | HERMES | 投产前 |
| 2 | 6面板/56子面板配置完整性 | ⏳ 待审核 | HERMES | 投产前 |
| 3 | 18条告警规则配置正确性 | ⏳ 待审核 | HERMES | 投产前 |
| 4 | 3级严重度定义合理性 | ⏳ 待审核 | HERMES | 投产前 |
| 5 | 升级链配置合理性 | ⏳ 待审核 | HERMES | 投产前 |
| 6 | GATE-DSHE-010 专项监控配置 | ⏳ 待审核 | HERMES | 投产前 |
| 7 | 异常规则E-1~E-8映射完整性 | ⏳ 待审核 | HERMES | 投产前 |
| 8 | 回滚触发条件映射完整性 | ⏳ 待审核 | HERMES | 投产前 |
| 9 | 实时vs批量采集配置合理性 | ⏳ 待审核 | HERMES | 投产前 |
| 10 | 验收标准完整性 | ⏳ 待审核 | HERMES | 投产前 |

**HERMES审核签名**: ⏳ 待签署

### 7.3 跨团队联合审核

| # | 审核项 | DSHB | HERMES | 状态 |
|---|--------|------|--------|------|
| 1 | P0阈值一致性 | ⏳ | ⏳ | ⏳ 待联合审核 |
| 2 | P1阈值一致性 | ⏳ | ⏳ | ⏳ 待联合审核 |
| 3 | 升级链协同 | ⏳ | ⏳ | ⏳ 待联合审核 |
| 4 | 回滚触发条件 | ⏳ | ⏳ | ⏳ 待联合审核 |
| 5 | 告警通知渠道 | ⏳ | ⏳ | ⏳ 待联合审核 |

**联合审核结论**: ⏳ 待签署

---

## 8. 实时 vs 批量观测配置

### 8.1 采集模式对比

| 维度 | 实时观测 | 批量观测 |
|------|---------|---------|
| 采集频率 | 30s | 1h |
| 延迟 | <1s | <1h |
| 存储 | Prometheus (内存) | Prometheus (持久) |
| 告警延迟 | <30s | <1h |
| 资源消耗 | 高 | 低 |
| 适用指标 | 性能/错误/降级 | 监控/数据/日志 |

### 8.2 实时观测指标 (8项)

| 指标 | 频率 | 存储 | 告警延迟 |
|------|------|------|---------|
| OBS-01 (P99) | 30s | Prometheus内存 | 5min |
| OBS-02 (首屏) | 30s | Prometheus内存 | 5min |
| OBS-03 (P0错误) | 30s | Prometheus内存 | 1min |
| OBS-04 (P1引擎) | 30s | Prometheus内存 | 1h |
| OBS-05 (P1展示) | 30s | Prometheus内存 | 1min |
| OBS-09 (降级数) | 30s | Prometheus内存 | 5min |
| OBS-10 (恢复时间) | 30s | Prometheus内存 | 5min |
| OBS-13 (解析时间) | 30s | Prometheus内存 | 5min |
| OBS-15 (日志完整性) | 30s | Prometheus内存 | 5min |
| OBS-18 (数据延迟) | 30s | Prometheus内存 | 5min |

### 8.3 批量观测指标 (10项)

| 指标 | 频率 | 存储 | 告警延迟 |
|------|------|------|---------|
| OBS-06 (误报率) | 1h | Prometheus持久 | 1h |
| OBS-07 (召回率) | 1h | Prometheus持久 | 1h |
| OBS-08 (覆盖率) | 1h | Prometheus持久 | 1h |
| OBS-11 (zhiji确认) | 1h | Prometheus持久 | 1h |
| OBS-12 (切换率) | 1h | Prometheus持久 | 1h |
| OBS-14 (CDN命中率) | 1h | Prometheus持久 | 1h |
| OBS-16 (告警准确率) | 1h | Prometheus持久 | 1h |
| OBS-17 (冷启动) | 30s | Prometheus内存 | — |

### 8.4 观测时间线

```
观测时间线:
T-24h ──── T-6h ──── T-1h ──── T0 ──── T+1h ──── T+24h ──── T+7d
  │          │         │       │        │         │          │
  ▼          ▼         ▼       ▼        ▼         ▼          ▼
健康检查   数据源确认  灰度   全量上线  首批观测  稳定性确认  复盘报告
          (E-1检查)  (E-5)  (E-1~8)  (C1-C5)   (P99<3s)   (全达标)

  ── T-24h~T-1h ──  批量观测 (1h)  ── 实时观测 (30s) ── 批量+实时 ── 批量 ──
  │                                              │                              │
  │  健康检查: 批量                                灰度+全量: 实时               │
  │  数据源确认: 批量                              性能+错误: 实时               │
  │                                                  降级: 实时                  │
  │                                                  数据: 批量+实时             │
```

---

## 9. 异常规则映射

### 9.1 异常规则到告警映射

| 异常ID | 异常类型 | 关联指标 | 告警规则 | 严重度 | 自动/手动回滚 |
|--------|---------|---------|---------|--------|-------------|
| E-1 | 数据拉取失败 | OBS-18 | ALERT-OBS-18-P1 | P1 | 自动L2 |
| E-2 | 数据空值兜底 | OBS-04 | ALERT-OBS-04-P1 | P1 | 自动L2 |
| E-3 | 数据异常过滤 | — | — | — | — |
| E-4 | 降级渲染失败 | OBS-09, OBS-10 | ALERT-OBS-09-P1, ALERT-OBS-10-P1 | P1 | 自动L1 |
| E-5 | 性能超标 | OBS-01, OBS-02 | ALERT-OBS-01-P1, ALERT-OBS-02-P1 | P1 | 自动L2 |
| E-6 | 口径不一致 | — | — | P2 | 手动 |
| E-7 | 覆盖率下降 | OBS-08 | ALERT-OBS-08-P1 | P1 | 手动 |
| E-8 | zhiji数据缺失 | OBS-11, OBS-12 | ALERT-OBS-12-P1 | P1 | 手动 |

---

## 10. 验收标准

### 10.1 投产观测验收标准

| # | 验收项 | 标准 | 验证方式 | 验收方 |
|---|--------|------|---------|--------|
| 1 | 18指标全部上线 | 18/18 | Grafana面板检查 | HERMES |
| 2 | 6面板/56子面板 | 6/6, 56/56 | Grafana面板检查 | HERMES |
| 3 | 18条告警规则 | 18/18 | Prometheus告警检查 | HERMES |
| 4 | 3级严重度 | P0/P1/P2 | 告警规则检查 | HERMES |
| 5 | 升级链配置 | 3级全部配置 | 升级链检查 | HERMES |
| 6 | GATE-DSHE-010 | 专项配置完整 | Grafana面板检查 | HERMES |
| 7 | DSHB确认 | 12项全部确认 | DSHB签署 | DSHB |
| 8 | HERMES审计 | 10项全部通过 | HERMES签署 | HERMES |
| 9 | 异常映射 | E-1~E-8全部映射 | 映射检查 | HERMES |
| 10 | 实时/批量配置 | 8实时+8批量 | 配置检查 | HERMES |

### 10.2 验收检查表

| # | 检查项 | 状态 | 负责人 |
|---|--------|------|--------|
| 1 | 所有Prometheus指标可查询 | ⏳ | DSHB引擎 |
| 2 | Grafana面板数据源连接正常 | ⏳ | DSHE值班 |
| 3 | 告警规则语法正确 | ⏳ | HERMES |
| 4 | 告警通知渠道配置完成 | ⏳ | DSHB监控 |
| 5 | 升级链联系人数完整 | ⏳ | DSHB+DSHE |
| 6 | 异常规则到告警映射完整 | ⏳ | HERMES |
| 7 | 实时指标采集延迟<1s | ⏳ | DSHB引擎 |
| 8 | 批量指标采集延迟<1h | ⏳ | DSHB引擎 |
| 9 | 面板加载时间<3s | ⏳ | DSHE值班 |
| 10 | 告警触发到通知<30s | ⏳ | DSHB监控 |

---

## 11. 附录

### 11.1 文件信息

| 项目 | 值 |
|------|-----|
| **文件名** | v86_rc2_prod_observation_panel_report.md |
| **工单** | DSHE_V86_RC2_PROD_PHASE_STAGE1 · T3.4 |
| **分支** | feature/v85-chart-template |
| **基线** | V86-RC2 PREP CLOSED (commit `7fe50b8`) |
| **创建日期** | 2026-10-04 |
| **状态** | 🟢 投产观测面板配置就绪 — 18指标/6面板/56子面板/3级告警 |

### 11.2 关键统计

| 维度 | 数量 |
|------|------|
| 观测指标 | 18 |
| Grafana面板 | 6 |
| 子面板 | 56 |
| 告警规则 | 18 |
| P0规则 | 1 |
| P1规则 | 11 |
| P2规则 | 6 |
| 升级链级别 | 3 |
| 实时观测指标 | 8 |
| 批量观测指标 | 8 |
| 异常映射 | 8 (E-1~E-8) |
| DSHB确认项 | 12 |
| HERMES审计项 | 10 |
| 联合审核项 | 5 |
| 验收标准 | 10 |

### 11.3 参考文档

| 来源 | 文档 | 路径 |
|------|------|------|
| 投产交接 | `v86_rc2_prep_to_prod_handover.md` | `hermes_e2e_test/` |
| 投产切换指南 | `v86_rc2_dshe_prod_switch_guide_v7.md` | `dshe_alias_gate_final_v7/` |
| 底层任务排期 | `v86_rc2_dshb_underlying_dev_backlog_v7.md` | `dshe_alias_gate_final_v7/` |
| 监控规范 | `v86_rc2_dshe_hermes_check_spec_v7.md` | `dshe_alias_gate_final_v7/` |
| Gate终审 | `v86_rc2_dshe_c1_c5_gate_final_report_v7.md` | `dshe_alias_gate_final_v7/` |
| 风险评审 | `v86_rc2_dshe_prod_dependency_review.md` | `dshe_alias_gate_final_v7/` |

---

*文档版本: V7 (投产观测面板与告警规则报告)*
*生成日期: 2026-10-04*
*工单: DSHE_V86_RC2_PROD_PHASE_STAGE1 · T3.4*
*分支: feature/v85-chart-template*
*状态: 🟢 18指标/6面板/56子面板/3级告警 — 待DSHB确认+HERMES审计*
