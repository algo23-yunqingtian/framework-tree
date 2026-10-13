# HERMES V87-RC1 Phase02 — 三方需求终审会议纪要

| 项目 | 值 |
|------|---|
| 工单 | HERMES_V87_RC1_PHASE02_3PARTY_REQUIREMENT_FINAL_ALIGN |
| 分支 | feature/v87-rc1-g1 @ d251dbb |
| 编制方 | HERMES |
| 日期 | 2026-10-18 |
| 参与方 | HERMES (L3审计) + DSHB (L1业务) + DSHE (L2展示) |

---

## 1. 会议信息

| 维度 | 值 |
|------|---|
| 日期 | 2026-10-18 |
| 方式 | 远程协同（git分支+文档评审） |
| 参与方 | HERMES / DSHB / DSHE |
| 前置文档 | DSHE `requirement_spec_lock.md` v1.0.0-lock |
| Phase01基线 | V87-RC1 基线已LOCKED |

## 2. V87 事件 Schema 最终定义

### 2.1 完整事件结构

```protobuf
message V87Event {
  // === V86继承字段 ===
  string event_id = 1;        // 事件唯一ID
  int64 timestamp = 2;        // 事件时间戳
  int32 event_count = 3;      // 事件计数
  double loss_rate = 4;       // 丢包率
  
  // === V87新增字段（5个）===
  string event_type = 5;      // 事件类型枚举
  int32 priority = 6;         // 事件优先级(1-5)
  string trace_id = 7;        // 链路追踪ID
  string batch_id = 8;        // 批量处理标识
  int32 retry_count = 9;      // 重试次数
}
```

### 2.2 字段口径终审

| # | 字段 | 类型 | 口径定义 | 取值范围 | 三方一致 |
|---|------|------|---------|---------|---------|
| 1 | event_type | string | 事件分类 | DATA_WRITE / DATA_READ / BATCH_OP / RETRY / HEARTBEAT | ✅ |
| 2 | priority | int32 | 事件优先级 | 1(最高) ~ 5(最低) | ✅ |
| 3 | trace_id | string | 全链路追踪 | UUID v4 格式 | ✅ |
| 4 | batch_id | string | 批量标识 | batch-{YYYYMMDD}-{seq} | ✅ |
| 5 | retry_count | int32 | 重试次数 | 0~3 (max 3) | ✅ |

### 2.3 字段校验规则

| 字段 | 校验方式 | 阈值 | 三方一致 |
|------|---------|------|---------|
| event_type | 枚举一致性 | 100% | ✅ |
| priority | 数值一致性 | 100% | ✅ |
| trace_id | SHA256一致性 | 必须一致 | ✅ |
| batch_id | SHA256一致性 | 必须一致 | ✅ |
| retry_count | 数值一致性 | 100% | ✅ |

## 3. 接口协议对齐

### 3.1 L3→L2 审计接口

| 接口 | 协议 | 说明 | 对齐状态 |
|------|------|------|---------|
| 审计对账接口 | gRPC unary | HERMES L3→DSHE L2 | ✅ 已对齐 |
| 异常检测接口 | gRPC unary | HERMES L3→DSHE L2 | ✅ 已对齐 |

### 3.2 L1→L3 数据接口

| 接口 | 协议 | 说明 | 对齐状态 |
|------|------|------|---------|
| 事件推送接口 | Kafka topic | DSHB L1→HERMES L3 | ✅ 已对齐 |
| WAL数据接口 | gRPC stream | DSHB L1→HERMES L3 | ✅ 已对齐 |

## 4. 指标体系对齐

### 4.1 审计指标

| 指标 | 采集频率 | 三方一致 |
|------|---------|---------|
| SHA256对账 | 15s | ✅ |
| 事件偏差 | 15s | ✅ |
| 丢包偏差 | 15s | ✅ |
| V87字段一致性 | 15s | ✅ |

### 4.2 性能指标

| 指标 | V87目标 | 三方一致 |
|------|--------|---------|
| 吞吐 | ≥900 ev/s | ✅ |
| WAL P99 | <3ms | ✅ |
| 索引P99 | <7ms | ✅ |
| 丢包 | <0.005% | ✅ |

## 5. 告警规则对齐

| 级别 | 审计触发条件 | 三方一致 |
|------|------------|---------|
| CRIT | SHA256不一致 / 链断裂>0 / 去重<100% | ✅ |
| WARN | 事件偏差>0.3% / 丢包偏差>0.3pp | ✅ |
| INFO | V87字段降级触发 | ✅ |

## 6. Gate 审查节点对齐

| 阶段 | 流量 | 审计交付物 | 三方一致 |
|------|------|----------|---------|
| Phase03 | 50% | 灰度对账+字段验证 | ✅ |
| Phase04 | 75% | 爬坡对账+模型校准 | ✅ |
| Phase05 | 100% | 全量Gate审计 | ✅ |
| Phase06 | 100% | 72h长稳+模型终校 | ✅ |
| Phase07 | 100% | 30天GA | ✅ |
| Phase08 | 100% | 90天归档 | ✅ |

## 7. 分歧解决

| # | 议题 | DSHB方案 | DSHE方案 | HERMES方案 | 最终决议 |
|---|------|---------|---------|-----------|---------|
| 1 | trace_id格式 | 自增序列 | UUID | UUID v4 | **UUID v4**（HERMES方案） |
| 2 | retry_count上限 | 5 | 3 | 3 | **3**（DSHE+HERMES方案） |
| 3 | 批量大小 | 1000 | 500 | 500 | **500**（DSHE+HERMES方案） |
| 4 | 对账窗口 | 4/天 | 8/天 | 8/天 | **8/天**（继承V86） |

## 8. 终审结论

| 维度 | 结论 |
|------|------|
| 事件Schema | ✅ 锁定（9字段） |
| 字段口径 | ✅ 5/5三方一致 |
| 接口协议 | ✅ gRPC+Kafka |
| 指标体系 | ✅ 4维度对齐 |
| 告警规则 | ✅ CRIT/WARN/INFO |
| Gate节点 | ✅ Phase03~08 |
| 分歧解决 | ✅ 4项全部解决 |
| **终审状态** | **LOCKED** 🔒 |

---

*关联: v87_rc1_e_l2_dashboard_phase01_requirement_spec_lock.md (DSHE)*
