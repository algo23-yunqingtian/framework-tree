# HERMES V87-RC1 Phase03 — 实时对账部署规格书

| 项目 | 值 |
|------|---|
| 工单 | HERMES_V87_RC1_PHASE03_REAL_TIME_RECONCILE_DEPLOY |
| 编制方 | HERMES |
| 日期 | 2026-10-18 |
| 脚本版本 | V87 RC1 V2.0 |

---

## 1. 部署架构

### 1.1 双链路隔离设计

```
DSHB (50%灰度流量) ──┬── [灰度对账链路] ── HERMES L3 ── SHA256+5字段 ── DSHE L2大盘
                     │
DSHB (50%基线流量) ──┴── [基线对账链路] ── HERMES L3 ── SHA256+5字段 ── DSHE L2大盘
```

### 1.2 双链路独立性

| 维度 | 灰度链路 | 基线链路 |
|------|---------|---------|
| 流量 | 50% V87 | 50% V86 |
| 对账脚本 | V87 V2.0 | V86 V1.0 |
| 字段校验 | SHA256+5字段 | SHA256 |
| 数据隔离 | 独立缓存 | 独立缓存 |
| 告警 | 独立告警组 | 独立告警组 |

**两链路完全隔离，互不影响** ✅

## 2. 对账任务配置

### 2.1 灰度对账任务

```yaml
task: v87_gray_reconcile
version: v87-rc1-v2.0
traffic: 50%-gray
schema: V87Event (9 fields)
reconcile:
  method: SHA256 + 5-field
  fields:
    base: event_count, loss_rate
    v87: event_type, priority, trace_id, batch_id, retry_count
  windows_per_day: 8
  window_interval: 3h
thresholds:
  ev_dev_pct: 0.5
  loss_dev_pp: 0.5
  sha256_required: true
  field_match_required: true
alerts:
  on_failure: AUD-AL-002 (CRIT)
  on_anomaly: AUD-AL-001 (WARN)
delivery:
  to: DSHE-L2
  protocol: gRPC unary
```

### 2.2 基线对账任务

```yaml
task: v86_baseline_reconcile
version: v86-rc2-v1.0
traffic: 50%-baseline
schema: V86Event (4 fields)
reconcile:
  method: SHA256
  windows_per_day: 8
thresholds:
  ev_dev_pct: 0.5
  loss_dev_pp: 0.5
```

## 3. 数据流

### 3.1 单窗口对账流程

```
1. 采集: HERMES/DSHB/DSHE 各侧窗口数据
2. SHA256: 三方数据摘要计算
3. 基础校验: event_count + loss_rate 偏差
4. V87字段校验: event_type/priority/trace_id/batch_id/retry_count
5. 综合判定: GO / WARN / RED
6. 告警推送: 异常→AUD-AL-001/002
7. 结果上报: DSHE L2 大盘
```

### 3.2 对账周期

| 维度 | 值 |
|------|---|
| 窗口间隔 | 3小时 |
| 窗口数/天 | 8 |
| 单窗口耗时 | ~0.70ms |
| 日对账总耗时 | ~5.6ms |

## 4. 隔离保障

### 4.1 数据隔离

| 维度 | 隔离方式 |
|------|---------|
| 缓存 | 灰度/基线独立内存池 |
| 对账结果 | 独立存储 |
| 告警 | 独立告警组 |
| 上报 | 独立gRPC通道 |

### 4.2 故障隔离

| 场景 | 处理 |
|------|------|
| 灰度链路故障 | 不影响基线链路 |
| 基线链路故障 | 不影响灰度链路 |
| 审计引擎故障 | 触发AUD-AL-002 |

## 5. 资源分配

| 资源 | 灰度链路 | 基线链路 | 合计 |
|------|---------|---------|------|
| 内存 | ~8MB | ~7MB | ~15MB |
| 对账缓存 | ~1.5MB | ~1.5MB | ~3MB |
| CPU | ~50% | ~50% | 100% |

## 6. 部署验证

| 验证项 | 预期 | 实际 | 判定 |
|--------|------|------|------|
| 灰度链路启动 | 成功 | ✅ | ✅ |
| 基线链路启动 | 成功 | ✅ | ✅ |
| 两链路隔离 | 互不影响 | ✅ | ✅ |
| V87字段校验 | 生效 | ✅ | ✅ |
| 告警对接 | 就绪 | ✅ | ✅ |
| DSHE上报 | 成功 | ✅ | ✅ |

**6/6 部署验证通过** ✅

## 7. 运维配置

| 配置项 | 值 |
|--------|---|
| 健康检查 | 每5分钟 |
| 自动重启 | 异常自动恢复 |
| 日志 | 结构化JSON |
| 监控 | Prometheus指标 |
| 扩缩容 | 按需 |

## 8. 结论

| 维度 | 结论 |
|------|------|
| 架构 | 双链路隔离 |
| 脚本 | V87 V2.0 + V86 V1.0 |
| 字段校验 | SHA256+5字段 |
| 窗口 | 8/天 |
| 隔离 | 数据+故障+告警 |
| 资源 | ~15MB内存 |
| 部署验证 | 6/6 PASS |
| **部署状态** | **完成** ✅ |

---

*关联: v87_rc1_hermes_phase03_real_time_reconcile_deploy_spec.md*
