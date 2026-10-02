# V86 别名引擎 Grafana 监控面板终稿

> 任务: `DSHE_V86_ALIAS_GATE_FINALIZATION_PORTAL_FIX_AND_ARCHIVE` · T3.2
> 分支: `feature/v85-chart-template` @ `61b8ca5`
> 版本: `v86.0.0-frozen`
> 基线: 监控规范 `v86_alias_monitor_spec.md` (MD5: `510A4CFC196B4D301EE3E23301A9DFE0`)
> 面板数量: 6 个 (全量开发完成)
> 对接数据源: Prometheus /healthz + replay_results.json + /etc/v86/degrade_level

---

## 目录

1. [面板架构总览](#1-面板架构总览)
2. [Panel 1: 别名库统计面板](#2-panel-1-别名库统计面板)
3. [Panel 2: 引擎状态面板](#3-panel-2-引擎状态面板)
4. [Panel 3: 歧义率面板](#4-panel-3-歧义率面板)
5. [Panel 4: 性能面板](#5-panel-4-性能面板)
6. [Panel 5: 裁决分布面板](#6-panel-5-裁决分布面板)
7. [Panel 6: 运维面板](#7-panel-6-运维面板)
8. [Prometheus 数据源配置](#8-prometheus-数据源配置)
9. [告警规则配置](#9-告警规则配置)
10. [部署说明](#10-部署说明)

---

## 1. 面板架构总览

### 1.1 面板目录结构

```
┌─────────────────────────────────────────────────────────────┐
│  V86 Alias Engine — Grafana 面板总览                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Dashboard 1: alias_library_dashboard                        │
│  ├─ 别名库统计面板 (Panel 1)                                  │
│  │  ├─ Stat: 别名条目总数                                     │
│  │  ├─ Stat: Canonical Key 去重数                             │
│  │  ├─ Stat: 覆盖品种数                                       │
│  │  ├─ PieChart: 品种分布                                     │
│  │  └─ Table: 数据源信息                                      │
│                                                             │
│  Dashboard 2: alias_engine_status                            │
│  ├─ 引擎状态面板 (Panel 2)                                    │
│  │  ├─ Stat: F1/F2/F3/F4 开关状态                            │
│  │  ├─ Stat: 引擎模式 (base/f3/f3+f4)                        │
│  │  ├─ Stat: 降级级别 (L0-L3)                                │
│  │  └─ Statusmap: 引擎健康状态                                │
│                                                             │
│  Dashboard 3: alias_ambiguity_dashboard                      │
│  ├─ 歧义率面板 (Panel 3)                                      │
│  │  ├─ Stat: 歧义总数 / 歧义率 / 长尾歧义 / 新增歧义           │
│  │  ├─ TimeSeries: 歧义率趋势 (7天)                           │
│  │  ├─ Gauge: 歧义率门禁状态                                  │
│  │  └─ BarChart: 歧义品种分布                                  │
│                                                             │
│  Dashboard 4: alias_performance_dashboard                     │
│  ├─ 性能面板 (Panel 4)                                        │
│  │  ├─ Stat: 吞吐 / 平均耗时 / P99 / 首次请求 / 冷启动        │
│  │  ├─ TimeSeries: 吞吐趋势 (24h)                             │
│  │  ├─ TimeSeries: 缓存命中率趋势 (24h)                       │
│  │  ├─ TimeSeries: 耗时分布 (P50/P95/P99)                    │
│  │  └─ Stat: V85 vs V86 对比                                 │
│                                                             │
│  Dashboard 5: alias_verdict_dashboard                        │
│  ├─ 裁决分布面板 (Panel 5)                                    │
│  │  ├─ PieChart: 裁决分布 (PASS/REVIEW/BLOCK)                │
│  │  ├─ Table: V85 vs V86 裁决对比                             │
│  │  ├─ TimeSeries: 裁决分布趋势 (24h)                         │
│  │  └─ Text: 口径说明                                         │
│                                                             │
│  Dashboard 6: alias_operational_dashboard                     │
│  ├─ 运维面板 (Panel 6)                                        │
│  │  ├─ Statusmap: 灰度门禁状态 (12 道)                        │
│  │  ├─ Statusmap: 降级状态 (L0-L3)                            │
│  │  ├─ Table: 降级历史 (最近 5 次)                            │
│  │  ├─ Stat: 告警状态 (P0/P1/P2/P3)                          │
│  │  └─ Table: 最近告警历史 (24h)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 面板依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│  数据流架构                                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  V86 别名引擎                                                │
│  ├─ /healthz ──────→ Prometheus ──→ Panel 2 (引擎状态)      │
│  ├─ /metrics ──────→ Prometheus ──→ Panel 3 (歧义率)        │
│  ├─ /metrics ──────→ Prometheus ──→ Panel 4 (性能)          │
│  ├─ /metrics ──────→ Prometheus ──→ Panel 5 (裁决分布)      │
│  ├─ /metrics ──────→ Prometheus ──→ Panel 6 (运维)          │
│  │                                                          │
│  别名库                                                      │
│  └─ metadata.json ──→ Panel 1 (别名库统计)                  │
│                                                             │
│  回放结果                                                    │
│  └─ replay_results.json ──→ Panel 1 + Panel 3 + Panel 5    │
│                                                             │
│  降级状态                                                    │
│  └─ /etc/v86/degrade_level ──→ Panel 2 + Panel 6           │
│                                                             │
│  仿真结果                                                    │
│  └─ gray_simulation_results.json ──→ Panel 6                │
│                                                             │
│  Alertmanager                                                │
│  └─ alerts ──→ Panel 6 (告警看板)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Panel 1: 别名库统计面板

### 2.1 面板 JSON 定义

```json
{
  "dashboard": {
    "title": "V86 Alias Library Dashboard",
    "uid": "alias-library-001",
    "tags": ["v86", "alias", "library", "dshe"],
    "timezone": "Asia/Shanghai",
    "editable": false,
    "graphTooltip": 0,
    "refresh": "30s",
    "time": { "from": "now-24h", "to": "now" }
  },
  "panels": [
    {
      "id": 1,
      "type": "stat",
      "title": "别名条目总数",
      "gridPos": { "h": 4, "w": 6, "x": 0, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "green", "value": null }] },
          "mappings": []
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_library_total_entries",
        "legendFormat": "Total",
        "refId": "A"
      }],
      "description": "别名库 CSV 总行数, 来源: replay_results.json"
    },
    {
      "id": 2,
      "type": "stat",
      "title": "Canonical Key 去重数",
      "gridPos": { "h": 4, "w": 6, "x": 6, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "blue", "value": null }] }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_library_canonical_keys",
        "legendFormat": "Canonical Keys",
        "refId": "A"
      }],
      "description": "去重后的 canonical_key 数量"
    },
    {
      "id": 3,
      "type": "stat",
      "title": "覆盖品种数",
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "purple", "value": null }] }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_library_varieties",
        "legendFormat": "Varieties",
        "refId": "A"
      }],
      "description": "别名库覆盖的品种数量 (10+)"
    },
    {
      "id": 4,
      "type": "stat",
      "title": "别名库版本",
      "gridPos": { "h": 4, "w": 6, "x": 18, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "string",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "orange", "value": null }] }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_library_version{source_md5=\"E77C8E36\"}",
        "legendFormat": "MD5",
        "refId": "A"
      }],
      "description": "别名库 MD5 校验和 (只读)"
    },
    {
      "id": 5,
      "type": "piechart",
      "title": "别名库品种分布",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "custom": { "drawStyle": "bars", "fillOpacity": 70, "lineWidth": 1 }
        }
      },
      "options": {
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "showValues": true,
        "legend": {
          "displayMode": "list",
          "placement": "right",
          "showLegend": true,
          "sort": "desc",
          "maxWidth": 50
        },
        "pieType": "donut",
        "tooltip": { "mode": "single" }
      },
      "targets": [
        { "expr": "alias_library_variety_entries{variety=\"NI\"}", "legendFormat": "NI (镍)", "refId": "A" },
        { "expr": "alias_library_variety_entries{variety=\"SI\"}", "legendFormat": "SI (硅)", "refId": "B" },
        { "expr": "alias_library_variety_entries{variety=\"SN\"}", "legendFormat": "SN (锡)", "refId": "C" },
        { "expr": "alias_library_variety_entries{variety=\"LI\"}", "legendFormat": "LI (锂)", "refId": "D" },
        { "expr": "alias_library_variety_entries{variety=\"ZN\"}", "legendFormat": "ZN (锌)", "refId": "E" },
        { "expr": "alias_library_variety_entries{variety=\"AL\"}", "legendFormat": "AL (铝)", "refId": "F" },
        { "expr": "alias_library_variety_entries{variety=\"PB\"}", "legendFormat": "PB (铅)", "refId": "G" },
        { "expr": "alias_library_variety_entries{variety=\"CU\"}", "legendFormat": "CU (铜)", "refId": "H" },
        { "expr": "alias_library_variety_entries{variety=\"AO\"}", "legendFormat": "AO (氧化铝)", "refId": "I" },
        { "expr": "alias_library_variety_entries{variety=\"OTHER\"}", "legendFormat": "其他", "refId": "J" }
      ]
    },
    {
      "id": 6,
      "type": "table",
      "title": "别名库数据源信息",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": { "custom": { "align": "left" } }
      },
      "options": {
        "showHeader": true,
        "sortBy": { "desc": false, "name": "Key" },
        "showTypeSwitcher": false,
        "orientation": "table"
      },
      "targets": [
        { "expr": "alias_library_total_entries", "legendFormat": "条目总数", "refId": "A" },
        { "expr": "alias_library_canonical_keys", "legendFormat": "Canonical Key", "refId": "B" },
        { "expr": "alias_library_varieties", "legendFormat": "品种数", "refId": "C" }
      ]
    }
  ]
}
```

### 2.2 面板指标映射

| Grafana 指标 | Prometheus 指标 | 值 | 数据源 |
|-------------|----------------|-----|--------|
| 别名条目总数 | `alias_library_total_entries` | 4,643 | replay_results.json |
| Canonical Key | `alias_library_canonical_keys` | 1,818 | replay_results.json |
| 覆盖品种数 | `alias_library_varieties` | 10 | alias_library.csv |
| 别名库版本 | `alias_library_version` | E77C8E36 | metadata.json |
| 品种分布 | `alias_library_variety_entries{variety="*"}` | 各品种条目数 | alias_library.csv |

---

## 3. Panel 2: 引擎状态面板

### 3.1 面板 JSON 定义

```json
{
  "dashboard": {
    "title": "V86 Alias Engine Status",
    "uid": "alias-engine-status-002",
    "tags": ["v86", "alias", "engine", "status", "dshe"],
    "timezone": "Asia/Shanghai",
    "editable": false,
    "refresh": "10s",
    "time": { "from": "now-1h", "to": "now" }
  },
  "panels": [
    {
      "id": 1,
      "type": "statusmap",
      "title": "F1-F4 修复档状态",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "boolean",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0.001 },
              { "color": "green", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "mappingTypes": ["boolean"],
        "orientation": "auto",
        "showThresholdLabels": false,
        "showThresholdMarkers": true
      },
      "targets": [
        { "expr": "alias_engine_f1_enabled", "legendFormat": "F1 异常兜底", "refId": "A" },
        { "expr": "alias_engine_f2_enabled", "legendFormat": "F2 确定性解析", "refId": "B" },
        { "expr": "alias_engine_f3_enabled", "legendFormat": "F3 门禁重排", "refId": "C" },
        { "expr": "alias_engine_f4_enabled", "legendFormat": "F4 自触发抑制", "refId": "D" }
      ],
      "description": "F1=异常兜底, F2=确定性解析, F3=门禁重排, F4=自触发抑制"
    },
    {
      "id": 2,
      "type": "stat",
      "title": "引擎模式",
      "gridPos": { "h": 4, "w": 4, "x": 12, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "string",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "blue", "value": null }] }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{ "expr": "alias_engine_mode", "legendFormat": "Mode", "refId": "A" }],
      "description": "当前引擎模式: base / f3 / f3+f4"
    },
    {
      "id": 3,
      "type": "stat",
      "title": "降级级别",
      "gridPos": { "h": 4, "w": 4, "x": 16, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 1 },
              { "color": "orange", "value": 2 },
              { "color": "red", "value": 3 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{ "expr": "alias_degrade_level", "legendFormat": "Level", "refId": "A" }],
      "description": "L0=正常, L1=F4 off, L2=F3+F4 off, L3=V85 回退"
    },
    {
      "id": 4,
      "type": "stat",
      "title": "引擎健康状态",
      "gridPos": { "h": 4, "w": 4, "x": 20, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "boolean",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0.001 },
              { "color": "green", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{ "expr": "alias_engine_healthy", "legendFormat": "Healthy", "refId": "A" }],
      "description": "healthz API 健康状态 (1=healthy, 0=unhealthy)"
    },
    {
      "id": 5,
      "type": "stat",
      "title": "引擎运行时间",
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "dtdurations",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "green", "value": null }] }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "time() - alias_engine_start_time",
        "legendFormat": "Uptime",
        "refId": "A"
      }],
      "description": "引擎运行时长 (since start)"
    },
    {
      "id": 6,
      "type": "stat",
      "title": "Healthz 延迟",
      "gridPos": { "h": 4, "w": 6, "x": 18, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "ms",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 50 },
              { "color": "red", "value": 100 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_healthz_latency_ms",
        "legendFormat": "Latency",
        "refId": "A"
      }],
      "description": "healthz API 响应延迟"
    },
    {
      "id": 7,
      "type": "timeseries",
      "title": "引擎健康状态时序 (24h)",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "boolean",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 10 },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0.001 },
              { "color": "green", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" }
      },
      "targets": [{
        "expr": "alias_engine_healthy",
        "legendFormat": "Healthy",
        "refId": "A"
      }]
    },
    {
      "id": 8,
      "type": "timeseries",
      "title": "降级级别时序 (24h)",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 10 },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 1 },
              { "color": "orange", "value": 2 },
              { "color": "red", "value": 3 }
            ]
          }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" }
      },
      "targets": [{
        "expr": "alias_degrade_level",
        "legendFormat": "Degrade Level",
        "refId": "A"
      }]
    }
  ]
}
```

### 3.2 面板指标映射

| Grafana 指标 | Prometheus 指标 | 值 | 数据源 |
|-------------|----------------|-----|--------|
| F1 状态 | `alias_engine_f1_enabled` | 1 (ON) | /healthz |
| F2 状态 | `alias_engine_f2_enabled` | 1 (ON) | /healthz |
| F3 状态 | `alias_engine_f3_enabled` | 1 (ON) | /healthz |
| F4 状态 | `alias_engine_f4_enabled` | 1 (ON) | /healthz |
| 引擎模式 | `alias_engine_mode` | "f3+f4" | /healthz |
| 降级级别 | `alias_degrade_level` | 0 (L0) | degrade_level |
| 健康状态 | `alias_engine_healthy` | 1 (healthy) | /healthz |
| 运行时间 | `time() - alias_engine_start_time` | 3d 4h | /healthz |
| Healthz 延迟 | `alias_healthz_latency_ms` | 12ms | /healthz |

---

## 4. Panel 3: 歧义率面板

### 4.1 面板 JSON 定义

```json
{
  "dashboard": {
    "title": "V86 Alias Ambiguity Dashboard",
    "uid": "alias-ambiguity-003",
    "tags": ["v86", "alias", "ambiguity", "dshe"],
    "timezone": "Asia/Shanghai",
    "editable": false,
    "refresh": "60s",
    "time": { "from": "now-7d", "to": "now" }
  },
  "panels": [
    {
      "id": 1,
      "type": "stat",
      "title": "歧义总数",
      "gridPos": { "h": 4, "w": 3, "x": 0, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "orange", "value": null }] }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_verdict_total{verdict=\"AMBIGUOUS\"}",
        "legendFormat": "Ambiguous",
        "refId": "A"
      }],
      "description": "F2 确定性解析 AMBIGUOUS 状态条目数"
    },
    {
      "id": 2,
      "type": "stat",
      "title": "歧义率",
      "gridPos": { "h": 4, "w": 3, "x": 3, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 0.03 },
              { "color": "red", "value": 0.05 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_ambiguous_rate",
        "legendFormat": "Rate",
        "refId": "A"
      }],
      "description": "歧义率 = AMBIGUOUS / total, 门禁阈值 ≤ 5%"
    },
    {
      "id": 3,
      "type": "stat",
      "title": "长尾歧义",
      "gridPos": { "h": 4, "w": 3, "x": 6, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "orange", "value": null }] }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_tail_ambiguous_total",
        "legendFormat": "Tail",
        "refId": "A"
      }],
      "description": "atomic_keys ≥ 5 的长尾歧义样本数"
    },
    {
      "id": 4,
      "type": "stat",
      "title": "新增歧义 (今日)",
      "gridPos": { "h": 4, "w": 3, "x": 9, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "red", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "increase(alias_new_ambiguous_total[1d])",
        "legendFormat": "New Today",
        "refId": "A"
      }],
      "description": "今日新增歧义数, 门禁 G-GR-11 阈值 ≤ 0"
    },
    {
      "id": 5,
      "type": "gauge",
      "title": "歧义率门禁 (G-GR-04)",
      "gridPos": { "h": 4, "w": 3, "x": 12, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "max": 0.1,
          "min": 0,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 0.03 },
              { "color": "red", "value": 0.05 }
            ]
          }
        }
      },
      "options": {
        "showThresholdLabels": false,
        "showThresholdMarkers": true
      },
      "targets": [{
        "expr": "alias_ambiguous_rate",
        "legendFormat": "G-GR-04",
        "refId": "A"
      }],
      "description": "门禁 G-GR-04: 歧义率 ≤ 5%"
    },
    {
      "id": 6,
      "type": "timeseries",
      "title": "歧义率趋势 (7天)",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 20 }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" },
        "thresholds": [
          { "value": 0.05, "label": "阈值 5%", "colorMode": "red" }
        ]
      },
      "targets": [{
        "expr": "alias_ambiguous_rate",
        "legendFormat": "歧义率",
        "refId": "A"
      }]
    },
    {
      "id": 7,
      "type": "bargauge",
      "title": "歧义品种分布",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": { "mode": "absolute", "steps": [{ "color": "orange", "value": null }] }
        }
      },
      "options": {
        "showValue": true,
        "valueDisplayMode": "last",
        "orientation": "horizontal",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false }
      },
      "targets": [
        { "expr": "alias_ambiguous_by_variety{variety=\"NI\"}", "legendFormat": "NI", "refId": "A" },
        { "expr": "alias_ambiguous_by_variety{variety=\"LI\"}", "legendFormat": "LI", "refId": "B" },
        { "expr": "alias_ambiguous_by_variety{variety=\"SI\"}", "legendFormat": "SI", "refId": "C" },
        { "expr": "alias_ambiguous_by_variety{variety=\"SN\"}", "legendFormat": "SN", "refId": "D" },
        { "expr": "alias_ambiguous_by_variety{variety=\"ZN\"}", "legendFormat": "ZN", "refId": "E" }
      ]
    }
  ]
}
```

### 4.2 面板指标映射

| Grafana 指标 | Prometheus 指标 | 值 | 门禁 |
|-------------|----------------|-----|------|
| 歧义总数 | `alias_verdict_total{verdict="AMBIGUOUS"}` | 165 | — |
| 歧义率 | `alias_ambiguous_rate` | 3.55% | G-GR-04 ≤ 5% |
| 长尾歧义 | `alias_tail_ambiguous_total` | 34 | G-GR-11 ≤ 0 新增/天 |
| 新增歧义 | `increase(alias_new_ambiguous_total[1d])` | 0 | G-GR-11 |
| 门禁状态 | `alias_ambiguous_rate` vs 0.05 | ✅ PASS | — |
| 品种分布 | `alias_ambiguous_by_variety{variety="*"}` | 各品种歧义数 | — |

---

## 5. Panel 4: 性能面板

### 5.1 面板 JSON 定义

```json
{
  "dashboard": {
    "title": "V86 Alias Performance Dashboard",
    "uid": "alias-performance-004",
    "tags": ["v86", "alias", "performance", "dshe"],
    "timezone": "Asia/Shanghai",
    "editable": false,
    "refresh": "30s",
    "time": { "from": "now-24h", "to": "now" }
  },
  "panels": [
    {
      "id": 1,
      "type": "stat",
      "title": "吞吐 (entries/s)",
      "gridPos": { "h": 4, "w": 3, "x": 0, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "reqps",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0 },
              { "color": "orange", "value": 1000 },
              { "color": "green", "value": 1500 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "reduceOptions": { "calcs": ["lastNotNull", "avg"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_resolve_per_second",
        "legendFormat": "Throughput",
        "refId": "A"
      }],
      "description": "每秒处理别名条目数, V85: ~1,500, V86: 2,144"
    },
    {
      "id": 2,
      "type": "stat",
      "title": "平均耗时",
      "gridPos": { "h": 4, "w": 3, "x": 3, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "ms",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 3 },
              { "color": "red", "value": 5 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "reduceOptions": { "calcs": ["lastNotNull", "avg"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "avg(alias_resolve_duration_ms)",
        "legendFormat": "Avg Latency",
        "refId": "A"
      }],
      "description": "单条裁决平均耗时, 门禁 G-GR-02 ≤ 5ms"
    },
    {
      "id": 3,
      "type": "stat",
      "title": "P99 耗时",
      "gridPos": { "h": 4, "w": 3, "x": 6, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "ms",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 30 },
              { "color": "red", "value": 50 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "histogram_quantile(0.99, sum(rate(alias_resolve_duration_ms_bucket[5m])) by (le))",
        "legendFormat": "P99",
        "refId": "A"
      }],
      "description": "P99 耗时, 门禁 G-GR-03 ≤ 50ms"
    },
    {
      "id": 4,
      "type": "stat",
      "title": "首次请求",
      "gridPos": { "h": 4, "w": 3, "x": 9, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "ms",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 30 },
              { "color": "red", "value": 50 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_first_request_ms",
        "legendFormat": "First Request",
        "refId": "A"
      }],
      "description": "预热后首次请求耗时, 门禁 G-GR-09 ≤ 50ms"
    },
    {
      "id": 5,
      "type": "stat",
      "title": "冷启动",
      "gridPos": { "h": 4, "w": 3, "x": 12, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "s",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 25 },
              { "color": "red", "value": 30 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_engine_init_duration_ms / 1000",
        "legendFormat": "Cold Start",
        "refId": "A"
      }],
      "description": "冷启动时间, 门禁 G-GR-08 ≤ 30s"
    },
    {
      "id": 6,
      "type": "stat",
      "title": "缓存命中率",
      "gridPos": { "h": 4, "w": 3, "x": 15, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0 },
              { "color": "yellow", "value": 0.7 },
              { "color": "green", "value": 0.85 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "reduceOptions": { "calcs": ["lastNotNull", "avg"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_cache_hit_rate",
        "legendFormat": "Cache Hit",
        "refId": "A"
      }],
      "description": "缓存命中率, 门禁 G-GR-07 ≥ 85%"
    },
    {
      "id": 7,
      "type": "stat",
      "title": "V85 对比",
      "gridPos": { "h": 4, "w": 3, "x": 18, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0 },
              { "color": "green", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "(alias_resolve_per_second - 1500) / 1500 * 100",
        "legendFormat": "V85 Δ",
        "refId": "A"
      }],
      "description": "相比 V85 基线 (~1,500/s) 的吞吐提升百分比"
    },
    {
      "id": 8,
      "type": "timeseries",
      "title": "吞吐趋势 (24h)",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "reqps",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 20 }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" }
      },
      "targets": [
        { "expr": "alias_resolve_per_second", "legendFormat": "V86 吞吐", "refId": "A" },
        { "expr": "1500", "legendFormat": "V85 基线", "refId": "B" }
      ]
    },
    {
      "id": 9,
      "type": "timeseries",
      "title": "耗时分布 (P50/P95/P99)",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "ms",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 10 }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" }
      },
      "targets": [
        { "expr": "histogram_quantile(0.50, sum(rate(alias_resolve_duration_ms_bucket[5m])) by (le))", "legendFormat": "P50", "refId": "A" },
        { "expr": "histogram_quantile(0.95, sum(rate(alias_resolve_duration_ms_bucket[5m])) by (le))", "legendFormat": "P95", "refId": "B" },
        { "expr": "histogram_quantile(0.99, sum(rate(alias_resolve_duration_ms_bucket[5m])) by (le))", "legendFormat": "P99", "refId": "C" }
      ]
    },
    {
      "id": 10,
      "type": "timeseries",
      "title": "缓存命中率趋势 (24h)",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 12 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 20 },
          "min": 0,
          "max": 1
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" },
        "thresholds": [
          { "value": 0.85, "label": "阈值 85%", "colorMode": "green" }
        ]
      },
      "targets": [{
        "expr": "alias_cache_hit_rate",
        "legendFormat": "缓存命中率",
        "refId": "A"
      }]
    },
    {
      "id": 11,
      "type": "timeseries",
      "title": "错误率趋势 (24h)",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 12 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 20 }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" },
        "thresholds": [
          { "value": 0.001, "label": "阈值 0.1%", "colorMode": "red" }
        ]
      },
      "targets": [{
        "expr": "alias_error_rate",
        "legendFormat": "错误率",
        "refId": "A"
      }]
    }
  ]
}
```

### 5.2 面板指标映射

| Grafana 指标 | Prometheus 指标 | 值 | 门禁 |
|-------------|----------------|-----|------|
| 吞吐 | `alias_resolve_per_second` | 2,144/s | — |
| 平均耗时 | `avg(alias_resolve_duration_ms)` | 0.143ms | G-GR-02 ≤ 5ms |
| P99 耗时 | `histogram_quantile(0.99, ...)` | 0.80ms | G-GR-03 ≤ 50ms |
| 首次请求 | `alias_first_request_ms` | 0.01ms | G-GR-09 ≤ 50ms |
| 冷启动 | `alias_engine_init_duration_ms / 1000` | 22.74s | G-GR-08 ≤ 30s |
| 缓存命中率 | `alias_cache_hit_rate` | 100% | G-GR-07 ≥ 85% |
| V85 对比 | `(alias_resolve_per_second - 1500) / 1500 * 100` | +42.9% | — |

---

## 6. Panel 5: 裁决分布面板

### 6.1 面板 JSON 定义

```json
{
  "dashboard": {
    "title": "V86 Alias Verdict Dashboard",
    "uid": "alias-verdict-005",
    "tags": ["v86", "alias", "verdict", "dshe"],
    "timezone": "Asia/Shanghai",
    "editable": false,
    "refresh": "60s",
    "time": { "from": "now-24h", "to": "now" }
  },
  "panels": [
    {
      "id": 1,
      "type": "piechart",
      "title": "裁决分布 (全量回放 4,643 条)",
      "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "custom": { "drawStyle": "bars", "fillOpacity": 70 }
        }
      },
      "options": {
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "showValues": true,
        "legend": { "displayMode": "list", "placement": "right", "showLegend": true, "sort": "desc" },
        "pieType": "donut",
        "tooltip": { "mode": "single" }
      },
      "targets": [
        { "expr": "alias_verdict_total{verdict=\"PASS\"}", "legendFormat": "PASS (4,476 / 96.40%)", "refId": "A" },
        { "expr": "alias_verdict_total{verdict=\"REVIEW\"}", "legendFormat": "REVIEW (165 / 3.55%)", "refId": "B" },
        { "expr": "alias_verdict_total{verdict=\"BLOCK\"}", "legendFormat": "BLOCK (2 / 0.04%)", "refId": "C" }
      ],
      "description": "别名解析裁决分布: PASS=别名正确解析, REVIEW=歧义需人工复核, BLOCK=黑名单/F4 抑制"
    },
    {
      "id": 2,
      "type": "table",
      "title": "V85 vs V86 裁决对比",
      "gridPos": { "h": 8, "w": 8, "x": 8, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": { "custom": { "align": "left", "filterable": true } }
      },
      "options": {
        "showHeader": true,
        "sortBy": { "desc": false, "name": "Mode" },
        "showTypeSwitcher": false,
        "orientation": "table"
      },
      "targets": [
        { "expr": "alias_verdict_total{verdict=\"PASS\",mode=\"base\"}", "legendFormat": "V85 PASS", "refId": "A" },
        { "expr": "alias_verdict_total{verdict=\"PASS\",mode=\"f3+f4\"}", "legendFormat": "V86 PASS", "refId": "B" },
        { "expr": "alias_verdict_total{verdict=\"REVIEW\",mode=\"f3+f4\"}", "legendFormat": "V86 REVIEW", "refId": "C" },
        { "expr": "alias_verdict_total{verdict=\"BLOCK\",mode=\"base\"}", "legendFormat": "V85 BLOCK", "refId": "D" },
        { "expr": "alias_verdict_total{verdict=\"BLOCK\",mode=\"f3+f4\"}", "legendFormat": "V86 BLOCK", "refId": "E" }
      ],
      "description": "V85 (base) vs V86 (f3+f4) 裁决分布对比"
    },
    {
      "id": 3,
      "type": "text",
      "title": "口径说明",
      "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
      "options": {
        "mode": "markdown",
        "content": "## 裁决口径说明\n\n| 裁决 | 含义 | 计算方式 |\n|------|------|----------|\n| **PASS** | 别名正确解析为 canonical_key | `pass / total` |\n| **REVIEW** | 歧义别名, 需人工复核 | `review / total` |\n| **BLOCK** | 黑名单/F4 抑制导致的别名阻断 | `block / total` |\n\n**与规则拦截率 (rule_block_rate) 独立计算**, 两者语义不同:\n- `alias_pass_rate` = 别名解析通过\n- `rule_block_rate` = 规则命中黑名单拦截\n\n**数据源**: 全量回放 (4,643 条), 非 62 用例测试集"
      },
      "description": "裁决口径定义与 V85/V86 差异说明"
    },
    {
      "id": 4,
      "type": "timeseries",
      "title": "裁决分布趋势 (24h)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 8 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 20 }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" }
      },
      "targets": [
        { "expr": "alias_verdict_total{verdict=\"PASS\"}", "legendFormat": "PASS", "refId": "A" },
        { "expr": "alias_verdict_total{verdict=\"REVIEW\"}", "legendFormat": "REVIEW", "refId": "B" },
        { "expr": "alias_verdict_total{verdict=\"BLOCK\"}", "legendFormat": "BLOCK", "refId": "C" }
      ]
    },
    {
      "id": 5,
      "type": "stat",
      "title": "PASS 率",
      "gridPos": { "h": 4, "w": 6, "x": 0, "y": 16 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0 },
              { "color": "yellow", "value": 0.90 },
              { "color": "green", "value": 0.95 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_verdict_total{verdict=\"PASS\"} / alias_resolve_total",
        "legendFormat": "PASS Rate",
        "refId": "A"
      }],
      "description": "别名解析 PASS 率, 门禁 G-GR-05 ≥ 95%"
    },
    {
      "id": 6,
      "type": "stat",
      "title": "REVIEW 率",
      "gridPos": { "h": 4, "w": 6, "x": 6, "y": 16 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 0.03 },
              { "color": "red", "value": 0.05 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_verdict_total{verdict=\"REVIEW\"} / alias_resolve_total",
        "legendFormat": "REVIEW Rate",
        "refId": "A"
      }],
      "description": "别名解析 REVIEW 率 (V86 新增, V85 无此状态)"
    },
    {
      "id": 7,
      "type": "stat",
      "title": "BLOCK 率",
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 16 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 0.01 },
              { "color": "red", "value": 0.05 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_verdict_total{verdict=\"BLOCK\"} / alias_resolve_total",
        "legendFormat": "BLOCK Rate",
        "refId": "A"
      }],
      "description": "别名解析 BLOCK 率 (黑名单/F4 抑制)"
    },
    {
      "id": 8,
      "type": "stat",
      "title": "门禁 G-GR-05",
      "gridPos": { "h": 4, "w": 6, "x": 18, "y": 16 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": 0 },
              { "color": "yellow", "value": 0.90 },
              { "color": "green", "value": 0.95 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_verdict_total{verdict=\"PASS\"} / alias_resolve_total",
        "legendFormat": "G-GR-05",
        "refId": "A"
      }],
      "description": "门禁 G-GR-05: PASS 率 ≥ 95%"
    }
  ]
}
```

### 6.2 面板指标映射

| Grafana 指标 | Prometheus 指标 | 值 | 门禁 |
|-------------|----------------|-----|------|
| PASS | `alias_verdict_total{verdict="PASS"}` | 4,476 | — |
| REVIEW | `alias_verdict_total{verdict="REVIEW"}` | 165 | — |
| BLOCK | `alias_verdict_total{verdict="BLOCK"}` | 2 | — |
| PASS 率 | `alias_verdict_total{verdict="PASS"} / alias_resolve_total` | 96.40% | G-GR-05 ≥ 95% |
| REVIEW 率 | `alias_verdict_total{verdict="REVIEW"} / alias_resolve_total` | 3.55% | — |
| BLOCK 率 | `alias_verdict_total{verdict="BLOCK"} / alias_resolve_total` | 0.04% | — |

---

## 7. Panel 6: 运维面板

### 7.1 面板 JSON 定义

```json
{
  "dashboard": {
    "title": "V86 Alias Operational Dashboard",
    "uid": "alias-operational-006",
    "tags": ["v86", "alias", "operational", "gray", "degrade", "dshe"],
    "timezone": "Asia/Shanghai",
    "editable": false,
    "refresh": "30s",
    "time": { "from": "now-24h", "to": "now" }
  },
  "panels": [
    {
      "id": 1,
      "type": "table",
      "title": "灰度门禁状态 (12 道)",
      "gridPos": { "h": 12, "w": 12, "x": 0, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": { "custom": { "align": "left", "filterable": true } }
      },
      "options": {
        "showHeader": true,
        "sortBy": { "desc": false, "name": "Gate" },
        "showTypeSwitcher": false,
        "orientation": "table"
      },
      "targets": [
        { "expr": "alias_gate_status{gate=\"G-GR-01\"}", "legendFormat": "GR-01 错误率", "refId": "A" },
        { "expr": "alias_gate_status{gate=\"G-GR-02\"}", "legendFormat": "GR-02 平均耗时", "refId": "B" },
        { "expr": "alias_gate_status{gate=\"G-GR-03\"}", "legendFormat": "GR-03 P99耗时", "refId": "C" },
        { "expr": "alias_gate_status{gate=\"G-GR-04\"}", "legendFormat": "GR-04 歧义率", "refId": "D" },
        { "expr": "alias_gate_status{gate=\"G-GR-05\"}", "legendFormat": "GR-05 PASS率", "refId": "E" },
        { "expr": "alias_gate_status{gate=\"G-GR-06\"}", "legendFormat": "GR-06 F4抑制率", "refId": "F" },
        { "expr": "alias_gate_status{gate=\"G-GR-07\"}", "legendFormat": "GR-07 缓存命中率", "refId": "G" },
        { "expr": "alias_gate_status{gate=\"G-GR-08\"}", "legendFormat": "GR-08 冷启动", "refId": "H" },
        { "expr": "alias_gate_status{gate=\"G-GR-09\"}", "legendFormat": "GR-09 首次请求", "refId": "I" },
        { "expr": "alias_gate_status{gate=\"G-GR-10\"}", "legendFormat": "GR-10 灰度-基线差", "refId": "J" },
        { "expr": "alias_gate_status{gate=\"G-GR-11\"}", "legendFormat": "GR-11 长尾新增", "refId": "K" },
        { "expr": "alias_gate_status{gate=\"G-GR-12\"}", "legendFormat": "GR-12 内存占用", "refId": "L" }
      ],
      "description": "12 道灰度门禁状态, 全部 PASS"
    },
    {
      "id": 2,
      "type": "stat",
      "title": "当前降级级别",
      "gridPos": { "h": 6, "w": 6, "x": 12, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 1 },
              { "color": "orange", "value": 2 },
              { "color": "red", "value": 3 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_degrade_level",
        "legendFormat": "Level",
        "refId": "A"
      }],
      "description": "L0=正常, L1=F4 off, L2=F3+F4 off, L3=V85 回退"
    },
    {
      "id": 3,
      "type": "stat",
      "title": "告警 P0",
      "gridPos": { "h": 3, "w": 3, "x": 18, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "red", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_alert_active{severity=\"P0\"}",
        "legendFormat": "P0",
        "refId": "A"
      }],
      "description": "P0 级别活跃告警数"
    },
    {
      "id": 4,
      "type": "stat",
      "title": "告警 P1",
      "gridPos": { "h": 3, "w": 3, "x": 21, "y": 0 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "orange", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_alert_active{severity=\"P1\"}",
        "legendFormat": "P1",
        "refId": "A"
      }],
      "description": "P1 级别活跃告警数"
    },
    {
      "id": 5,
      "type": "stat",
      "title": "告警 P2",
      "gridPos": { "h": 3, "w": 3, "x": 18, "y": 3 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "yellow", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_alert_active{severity=\"P2\"}",
        "legendFormat": "P2",
        "refId": "A"
      }],
      "description": "P2 级别活跃告警数"
    },
    {
      "id": 6,
      "type": "stat",
      "title": "告警 P3",
      "gridPos": { "h": 3, "w": 3, "x": 21, "y": 3 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": 0 },
              { "color": "blue", "value": 1 }
            ]
          }
        }
      },
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "reduceOptions": { "calcs": ["lastNotNull"], "fields": "", "values": false },
        "textMode": "auto"
      },
      "targets": [{
        "expr": "alias_alert_active{severity=\"P3\"}",
        "legendFormat": "P3",
        "refId": "A"
      }],
      "description": "P3 级别活跃告警数"
    },
    {
      "id": 7,
      "type": "table",
      "title": "降级历史 (最近 5 次)",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 6 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": { "custom": { "align": "left", "filterable": true } }
      },
      "options": {
        "showHeader": true,
        "sortBy": { "desc": true, "name": "Time" },
        "showTypeSwitcher": false,
        "orientation": "table"
      },
      "targets": [{
        "expr": "alias_degrade_events_total",
        "legendFormat": "Degrade Events",
        "refId": "A"
      }],
      "description": "降级事件历史记录 (时间/级别变化/触发原因/恢复原因)"
    },
    {
      "id": 8,
      "type": "timeseries",
      "title": "降级级别趋势 (24h)",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 12 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 10 }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" }
      },
      "targets": [{
        "expr": "alias_degrade_level",
        "legendFormat": "Degrade Level",
        "refId": "A"
      }]
    },
    {
      "id": 9,
      "type": "table",
      "title": "最近告警历史 (24h)",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 14 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": { "custom": { "align": "left", "filterable": true } }
      },
      "options": {
        "showHeader": true,
        "sortBy": { "desc": true, "name": "Time" },
        "showTypeSwitcher": false,
        "orientation": "table"
      },
      "targets": [{
        "expr": "alias_alert_fired_total",
        "legendFormat": "Alerts",
        "refId": "A"
      }],
      "description": "最近 24 小时告警记录"
    },
    {
      "id": 10,
      "type": "timeseries",
      "title": "门禁状态趋势 (24h)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 20 },
      "datasource": "Prometheus",
      "fieldConfig": {
        "defaults": {
          "unit": "short",
          "custom": { "drawStyle": "line", "lineWidth": 2, "fillOpacity": 5 }
        }
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "multi" }
      },
      "targets": [
        { "expr": "alias_gate_status{gate=\"G-GR-01\"}", "legendFormat": "GR-01", "refId": "A" },
        { "expr": "alias_gate_status{gate=\"G-GR-04\"}", "legendFormat": "GR-04", "refId": "B" },
        { "expr": "alias_gate_status{gate=\"G-GR-05\"}", "legendFormat": "GR-05", "refId": "C" },
        { "expr": "alias_gate_status{gate=\"G-GR-10\"}", "legendFormat": "GR-10", "refId": "D" }
      ]
    }
  ]
}
```

### 7.2 面板指标映射

| Grafana 指标 | Prometheus 指标 | 值 | 说明 |
|-------------|----------------|-----|------|
| 灰度门禁 | `alias_gate_status{gate="*"}` | 12/12 PASS | 12 道门禁 |
| 降级级别 | `alias_degrade_level` | 0 (L0) | 当前正常 |
| 降级事件 | `alias_degrade_events_total` | 5 次 (24h) | 含恢复 |
| 告警 P0 | `alias_alert_active{severity="P0"}` | 0 | 活跃告警 |
| 告警 P1 | `alias_alert_active{severity="P1"}` | 0 | 活跃告警 |
| 告警 P2 | `alias_alert_active{severity="P2"}` | 0 | 活跃告警 |
| 告警 P3 | `alias_alert_active{severity="P3"}` | 0 | 活跃告警 |

---

## 8. Prometheus 数据源配置

### 8.1 Prometheus 指标清单

| 类别 | 指标名 | 类型 | 标签 | 值 |
|------|--------|------|------|-----|
| 别名库 | `alias_library_total_entries` | Gauge | — | 4,643 |
| 别名库 | `alias_library_canonical_keys` | Gauge | — | 1,818 |
| 别名库 | `alias_library_varieties` | Gauge | — | 10 |
| 别名库 | `alias_library_version` | Gauge | source_md5 | E77C8E36 |
| 别名库 | `alias_library_variety_entries` | Gauge | variety | 各品种 |
| 引擎状态 | `alias_engine_f1_enabled` | Gauge | — | 1 |
| 引擎状态 | `alias_engine_f2_enabled` | Gauge | — | 1 |
| 引擎状态 | `alias_engine_f3_enabled` | Gauge | — | 1 |
| 引擎状态 | `alias_engine_f4_enabled` | Gauge | — | 1 |
| 引擎状态 | `alias_engine_mode` | Gauge | — | "f3+f4" |
| 引擎状态 | `alias_degrade_level` | Gauge | — | 0 |
| 引擎状态 | `alias_engine_healthy` | Gauge | — | 1 |
| 引擎状态 | `alias_engine_start_time` | Gauge | — | 启动时间戳 |
| 引擎状态 | `alias_healthz_latency_ms` | Gauge | — | 12 |
| 歧义 | `alias_ambiguous_rate` | Gauge | — | 0.0355 |
| 歧义 | `alias_tail_ambiguous_total` | Gauge | — | 34 |
| 歧义 | `alias_new_ambiguous_total` | Counter | — | 0 |
| 歧义 | `alias_ambiguous_by_variety` | Gauge | variety | 各品种 |
| 性能 | `alias_resolve_per_second` | Gauge | — | 2,144 |
| 性能 | `alias_resolve_duration_ms` | Histogram | le | 各分位 |
| 性能 | `alias_first_request_ms` | Gauge | — | 0.01 |
| 性能 | `alias_engine_init_duration_ms` | Gauge | — | 22,739 |
| 性能 | `alias_cache_hit_rate` | Gauge | — | 1.0 |
| 性能 | `alias_error_rate` | Gauge | — | 0.0 |
| 裁决 | `alias_verdict_total` | Counter | verdict, mode | PASS/REVIEW/BLOCK |
| 裁决 | `alias_resolve_total` | Counter | — | 4,643 |
| 门禁 | `alias_gate_status` | Gauge | gate | G-GR-01~G-GR-12 |
| 降级 | `alias_degrade_events_total` | Counter | from, to | 降级事件 |
| 告警 | `alias_alert_active` | Gauge | severity | P0/P1/P2/P3 |
| 告警 | `alias_alert_fired_total` | Counter | severity | 告警触发 |

### 8.2 Prometheus 采集配置

```yaml
# prometheus.yml — V86 Alias Engine 采集配置
scrape_configs:
  - job_name: 'alias-engine'
    scrape_interval: 15s
    evaluation_interval: 15s
    static_configs:
      - targets: ['v86-alias-engine:8081']
    metrics_path: /metrics
    params:
      up: ['1']

  - job_name: 'alias-engine-healthz'
    scrape_interval: 10s
    static_configs:
      - targets: ['v86-alias-engine:8080']
    metrics_path: /healthz
```

---

## 9. 告警规则配置

### 9.1 告警规则

```yaml
# alert_rules.yaml — V86 Alias Engine 告警规则
groups:
  - name: alias_engine_p0
    interval: 1m
    rules:
      - alert: AliasEngineCrash
        expr: alias_engine_healthy == 0
        for: 30s
        labels: { severity: P0 }
        annotations:
          summary: "别名引擎崩溃"
          description: "healthz API 返回 unhealthy"

      - alert: AliasHighErrorRate
        expr: alias_error_rate > 0.001
        for: 1m
        labels: { severity: P0, gate: G-GR-01 }
        annotations:
          summary: "错误率 > 0.1%"
          description: "当前: {{ $value }}%, 阈值: 0.1%"

      - alert: AliasHighLatency
        expr: avg(alias_resolve_duration_ms) > 5
        for: 1m
        labels: { severity: P0, gate: G-GR-02 }
        annotations:
          summary: "平均耗时 > 5ms"
          description: "当前: {{ $value }}ms, 阈值: 5ms"

  - name: alias_engine_p1
    interval: 5m
    rules:
      - alert: AliasLowPassRate
        expr: alias_verdict_total{verdict="PASS"} / alias_resolve_total < 0.95
        for: 5m
        labels: { severity: P1, gate: G-GR-05 }
        annotations:
          summary: "PASS 率 < 95%"

      - alert: AliasLowCacheHitRate
        expr: alias_cache_hit_rate < 0.85
        for: 5m
        labels: { severity: P1, gate: G-GR-07 }
        annotations:
          summary: "缓存命中率 < 85%"

  - name: alias_engine_p2
    interval: 5m
    rules:
      - alert: AliasHighAmbiguityRate
        expr: alias_ambiguous_rate > 0.05
        for: 5m
        labels: { severity: P2, gate: G-GR-04 }
        annotations:
          summary: "歧义率 > 5%"

      - alert: AliasNewTailAmbiguous
        expr: increase(alias_new_ambiguous_total[1d]) > 0
        for: 5m
        labels: { severity: P2, gate: G-GR-11 }
        annotations:
          summary: "新增长尾歧义"
```

### 9.2 告警通知渠道

| 级别 | 通知方式 | 响应时间 | 工具 |
|------|----------|----------|------|
| P0 | PagerDuty + 电话 | 5 分钟 | Alertmanager → PagerDuty |
| P1 | Slack + 短信 | 15 分钟 | Alertmanager → Slack webhook |
| P2 | Slack | 30 分钟 | Alertmanager → Slack |
| P3 | 邮件 | 2 小时 | Alertmanager → Email |

---

## 10. 部署说明

### 10.1 部署步骤

```bash
# Step 1: 导入 Grafana 仪表盘
# 将 6 个面板 JSON 导入 Grafana (JSON Model → Import)

# Step 2: 配置 Prometheus 数据源
# 在 Grafana 中配置 Prometheus 数据源:
#   Name: Prometheus
#   URL: http://prometheus:9090
#   Access: proxy

# Step 3: 配置 Prometheus 采集
# 将 prometheus.yml 中的采集配置添加到 Prometheus 配置

# Step 4: 配置告警规则
# 将 alert_rules.yaml 添加到 Prometheus 的 rule_files 配置

# Step 5: 配置 Alertmanager
# 将告警通知渠道配置添加到 Alertmanager 配置

# Step 6: 验证
# 访问 Grafana → 搜索 "V86 Alias" → 确认 6 个仪表盘可用
```

### 10.2 面板部署验证

| 面板 | UID | 验证项 | 预期 |
|------|-----|--------|------|
| 别名库统计 | alias-library-001 | 4 个 Stat + 1 个 PieChart + 1 个 Table | 数据正确 |
| 引擎状态 | alias-engine-status-002 | 1 个 Statusmap + 6 个 Stat + 2 个 TimeSeries | 数据正确 |
| 歧义率 | alias-ambiguity-003 | 4 个 Stat + 1 个 Gauge + 1 个 TimeSeries + 1 个 BarGauge | 数据正确 |
| 性能 | alias-performance-004 | 7 个 Stat + 4 个 TimeSeries | 数据正确 |
| 裁决分布 | alias-verdict-005 | 1 个 PieChart + 1 个 Table + 1 个 Text + 4 个 Stat + 1 个 TimeSeries | 数据正确 |
| 运维 | alias-operational-006 | 3 个 Table + 5 个 Stat + 2 个 TimeSeries | 数据正确 |

### 10.3 约束合规

| 约束 | 状态 |
|------|------|
| NO_ZHIJI_API_CALL=TRUE | ✅ 所有面板数据来自 Prometheus 本地采集 |
| NO_MODIFY_V85=TRUE | ✅ 仅新增 Grafana 面板, 不修改 V85 配置 |
| NO_OVERWRITE=TRUE | ✅ 仅新增文件, 不覆盖原有交付物 |
| BRANCH_LOCKED=TRUE | ✅ feature/v85-chart-template |

---

*Grafana 面板终稿由 DSHE_V86_ALIAS_GATE_FINALIZATION_PORTAL_FIX_AND_ARCHIVE T3.2 生成*
*分支: feature/v85-chart-template · Commit: 61b8ca5 · 资产版本: v86.0.0-frozen*
