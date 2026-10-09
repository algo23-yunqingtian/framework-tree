# HERMES V86-RC2 Phase21 — 三方基线对齐报告

| 项目 | 值 |
|------|---|
| 工单 | HERMES_V86_RC2_PHASE21_3WAY_BASELINE_ALIGN_ACTIVE |
| 对齐版本 | v2.0-phase21 |
| 对齐时间 | 2026-10-09 01:43:45 UTC |
| 编制方 | HERMES |

---

## 1. 对齐维度

### 1.1 事件计数口径

| 方 | 口径 | 定义 |
|----|------|------|
| HERMES | events_written_dedup | 去重后持久化事件数（标准口径） |
| DSHB | events_generated | DEP 原始事件数 |
| DSHE | events_consumed | L2 消费计数 |
| **标准定义** | 以 HERMES events_written_dedup 为准，DSHB/DSHE 允许 ≤0.5% 抖动 | ✅ 对齐 |

### 1.2 对账窗口

| 维度 | HERMES | DSHB | DSHE | 对齐 |
|------|--------|------|------|------|
| 窗口数/天 | 8 | 8 | 8 | ✅ |
| 窗口时长 | 3h | 3h | 3h | ✅ |
| 校验方式 | SHA256 哈希抽样 | 同 | 同 | ✅ |

### 1.3 指标定义

| 指标 | 统一定义 | 对齐 |
|------|---------|------|
| wal_p99 | 写入延迟 P99 (ms), latency_write_ms.p99_est | ✅ |
| idx_p99 | 索引构建 P99 (ms), latency_index_ms.p99_est | ✅ |
| loss_pct | event_loss_rate_pct = write_fail / total_accepted × 100 | ✅ |
| chain_broken | 哈希链断裂计数，确定应为 0 | ✅ |
| dup_capture_rate | dup_captured / dup_injected × 100，应为 100% | ✅ |
| index_inflation_pct | 索引大小增长占初始基线比例 | ✅ |

### 1.4 阈值体系

| 指标 | WARN | CRITICAL | 对齐 |
|------|------|----------|------|
| loss_pct | 0.01% | 0.05% | ✅ |
| wal_p99 | 2000ms | 5000ms | ✅ |
| idx_p99 | 10ms | 20ms | ✅ |
| index_inflation | 8.0% | 10.0% | ✅ |
| reconcile_dev | 0.5% | — | ✅ |

## 2. Phase20 一致性确认

Phase20 50% 72h 三方对账结果：
- 24/24 窗口全 PASS
- 最大事件偏差 0.0071%
- 最大丢包偏差 0.092pp
- SHA256 24/24 一致

**Phase20 基线已确认一致** ✅

## 3. Phase21 75% 对账验证

| 维度 | Day1 | Day2 | Day3 | 判定 |
|------|------|------|------|------|
| 最大事件偏差 | 0.1988% | 0.1939% | 0.1991% | ✅ ≤0.5% |
| 最大丢包偏差 | 0.085pp | 0.089pp | 0.086pp | ✅ ≤0.5% |
| SHA256 一致 | 8/8 | 8/8 | 8/8 | ✅ |

## 4. 基线锁定

- Phase21 基线已锁定 ✅
- 所有指标定义、窗口口径、阈值体系三方一致
- 后续 StageF 75% 正式运行时直接复用此基线

---

*数据来源: /tmp/phase21_75pct_audit_data.json → three_way_baseline_alignment*
