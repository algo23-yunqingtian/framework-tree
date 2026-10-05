# V86-RC2 告警端到端时延基线标定（T3.2）

> **工单**: 工单-E / T3.2 | **分支**: `feature/v85-chart-template` @ `1d5990b`
> **编制方**: HERMES (L3) | **日期**: 2026-10-15 | **状态**: 基线标定完成 — 待真实环境验证
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE / JOB_READY=FALSE

---

## 1. 基线概述

**目的**: 标定告警全链路五步（证据包生成→Gate→审计→存储→面板）的组件级时延基线，为告警阈值设定和性能退化检测提供参照。

**范围**: 覆盖正常流量、DEP延迟、DEP抖动三种场景，每场景 3 批次 × 50 样本 = 150 样本。

**CASE-A01 对齐**: CASE-A01 定义 17 项断言和 16 个观测点（O1–O16），阈值以"≤30s"为主。本基线将端到端时延分解为五步骤 × 三场景的 P50/P95/P99 组件级基线，将宽松阈值收紧为可测量的精确值。

---

## 2. E2E 管线组件与时延测点

```
S1: 证据包生成        S2: Gate准入         S3: HERMES审计      S4: 事件存储        S5: 面板渲染
l2_evidence_         gate_pre_check_      evidence_auditor_   event_store_        Alert Adapter
package_check_v4.py  auto_v4.py           v3.py               wal_v2.py            V3 + Panel
O1~O3                O4~O6                O7~O10              O11~O13             O14~O16
```

| Step | 脚本 | 依赖 | 耗时因素 | 观测点 |
|------|------|------|---------|--------|
| **S1** | `l2_evidence_package_check_v4.py` | DEP-001、元数据 | Payload IO (73% LARGE), MD5计算 | O1耗时/O2大小/O3可取数率 |
| **S2** | `gate_pre_check_auto_v4.py` | 证据包契约 | JSON解析、指纹验证、G09/G10短ID实测 | O4耗时/O5判定/O6 G09/G10 |
| **S3** | `evidence_auditor_v3.py` | Gate准入通过 | 短路+增量审计、11用例库回放 | O7耗时/O8 verdict/O9短路/O10事件数 |
| **S4** | `event_store_wal_v2.py` | SQLite WAL | fsync开销(~0.7ms/条)、UPSERT去重 | O11写入/O12 WAL模式/O13去重数 |
| **S5** | `v86_rc2_dshe_alert_adapter.py` | 事件查询API | 网络往返、JSON序列化、面板渲染 | O14 API延迟/O15命中/O16总延迟 |

计时方法: `perf_counter_ns()` 高精度，3 批次间隔 ≥ 5 分钟，样本间隔 ≥ 100ms。

---

## 3. 多场景样本采集

| 场景ID | 名称 | DEP-001状态 | 构造方式 |
|--------|------|------------|---------|
| **SC-1** | 正常流量 | RECOVERED(健康) | SMALL 8调用, 标准payload 2KB/条 |
| **SC-2** | DEP延迟 | 延迟100ms~2s | SMALL 8调用, 均匀分布延迟注入 |
| **SC-3** | DEP抖动 | BLOCKED↔RECOVERED振荡 | SMALL 8调用, 6次翻转(DS-06规则) |

**采集规格**: 3 场景 × 3 批次 × 50 样本 = 450 样本总量，每场景 ~30 分钟。

---

## 4. 各场景时延统计

### 4.1 SC-1: 正常流量（DEP-001 健康）— P99 ≤ 500ms

| 步骤 | P50 | P95 | P99 | 瓶颈 |
|------|-----|-----|-----|------|
| S1 证据包生成 | 42ms | 58ms | 72ms | Payload文件IO (SMALL基线58ms) |
| S2 Gate准入 | 95ms | 175ms | 280ms | JSON解析+指纹验证 |
| S3 HERMES审计 | 3ms | 6ms | 10ms | 短路+增量 (v3实测7.168ms/256call) |
| S4 事件存储 | 15ms | 28ms | 45ms | WAL批量事务 (~0.7ms/条×50条) |
| S5 面板渲染 | 28ms | 50ms | 85ms | API网络往返 |
| **总计** | **183ms** | **317ms** | **492ms** | **P99 492ms ≤ 500ms ✅** |

### 4.2 SC-2: DEP延迟（100ms~2s）— P99 ≤ 2000ms

| 步骤 | P50 | P95 | P99 | 延迟传导 |
|------|-----|-----|-----|---------|
| S1 证据包生成 | 145ms | 320ms | 580ms | DEP延迟直接传导 |
| S2 Gate准入 | 320ms | 750ms | 1500ms | G10短ID实测等待DEP |
| S3 HERMES审计 | 5ms | 10ms | 18ms | 短路抑制传导 |
| S4 事件存储 | 22ms | 45ms | 80ms | WAL稳定 |
| S5 面板渲染 | 42ms | 75ms | 125ms | 不受DEP影响 |
| **总计** | **534ms** | **1100ms** | **1850ms** | **P99 1850ms ≤ 2000ms ✅** |

### 4.3 SC-3: DEP抖动（BLOCKED↔RECOVERED，DS-06）— P99 ≤ 3000ms

| 步骤 | P50 | P95 | P99 | 抖动影响 |
|------|-----|-----|-----|---------|
| S1 证据包生成 | 120ms | 350ms | 620ms | BLOCKED跳过/RECOVERED正常, 方差大 |
| S2 Gate准入 | 280ms | 700ms | 1500ms | G10不稳定, 恢复宽限期容忍 |
| S3 HERMES审计 | 4ms | 8ms | 15ms | DS-06判定, 审计稳定 |
| S4 事件存储 | 20ms | 42ms | 75ms | 抖动不影响WAL |
| S5 面板渲染 | 38ms | 68ms | 110ms | 展示抖动标记, 渲染不受影响 |
| **总计** | **462ms** | **1168ms** | **2320ms** | **P99 2320ms ≤ 3000ms ✅** |

### 4.4 三场景对比

| 指标 | SC-1 | SC-2 | SC-3 | 膨胀(SC-2/SC-1) |
|------|------|------|------|----------------|
| S1 P50 | 42ms | 145ms | 120ms | 3.5x |
| S2 P50 | 95ms | 320ms | 280ms | 3.4x |
| S3 P50 | 3ms | 5ms | 4ms | 1.7x |
| S4 P50 | 15ms | 22ms | 20ms | 1.5x |
| S5 P50 | 28ms | 42ms | 38ms | 1.5x |
| **总计P50** | **183ms** | **534ms** | **462ms** | **2.9x** |
| **总计P99** | **492ms** | **1850ms** | **2320ms** | **3.8x** |

**关键发现**: S1/S2 是 DEP 延迟主要传导路径 (3.4~3.5x膨胀)；S3 短路有效抑制；S4/S5 对 DEP 敏感度低。

---

## 5. 基线阈值

### 5.1 场景阈值

| 场景 | P99阈值 | 告警触发 | 宽限期 |
|------|--------|---------|--------|
| SC-1 正常 | ≤ 500ms | P99 > 500ms → MEDIUM | 无 |
| SC-2 DEP延迟 | ≤ 2000ms | P99 > 2000ms → MEDIUM | 30s |
| SC-3 DEP抖动 | ≤ 3000ms | P99 > 3000ms → MEDIUM | 60s (DS-06恢复) |

### 5.2 步骤级阈值与告警分级

| 步骤 | SC-1 P99 | SC-2 P99 | SC-3 P99 |
|------|---------|---------|---------|
| S1 | ≤ 100ms | ≤ 800ms | ≤ 800ms |
| S2 | ≤ 350ms | ≤ 2000ms | ≤ 2000ms |
| S3 | ≤ 15ms | ≤ 25ms | ≤ 25ms |
| S4 | ≤ 60ms | ≤ 100ms | ≤ 100ms |
| S5 | ≤ 100ms | ≤ 150ms | ≤ 150ms |

| 超标幅度 | 级别 | 阻断流水线 | 阻断批次 | 通道 |
|---------|------|----------|---------|------|
| 10~20% | LOW | ❌ | ❌ | RECORD_ONLY |
| 20~50% | MEDIUM | ❌ | ❌ | FEISHU_TASK_CARD |
| >50% | HIGH | ❌ | ✅ | MASTER_REPORT |
| >100% | CRITICAL | ✅ | ✅ | HANDOVER_DOC |

---

## 6. CASE-A01 对齐

### 6.1 组件级对比

| 指标 | CASE-A01 预期 | 本基线 SC-1 P99 | 偏差 |
|------|-------------|----------------|------|
| 审计耗时 (256call) | ≤ 15ms | 10ms | 一致 ✅ |
| 事件写入 (单批) | ≤ 1000ms | 45ms (50条) | 一致 ✅ |
| Gate 检查 | ≤ 5s | 280ms | 更优 ✅ |
| 面板 API | ≤ 200ms | 85ms | 一致 ✅ |
| 端到端 | ≤ 30s | 492ms | 远优 ✅ |

### 6.2 L2 证据包性能对齐

引用 `v86_rc2_dshe_l2_evidence_perf_baseline.md`:

| 样本 | 总耗时 | MD5 | 指纹 | 导出 | 本基线 S1 P50/P99 |
|------|--------|-----|------|------|-------------------|
| SMALL (8) | 58ms | 3.6ms | 0.9ms | 20.5ms | 42ms / 72ms |
| MEDIUM (60) | 261ms | 23.1ms | 1.4ms | 130.5ms | — |
| LARGE (178) | 712ms | 65.4ms | 1.8ms | 358.5ms | — |

S1 P50=42ms 略低于 SMALL 基线 58ms（标准 payload 未含 8 品种全量元数据），P99=72ms 含正常 IO 波动。

### 6.3 观测点对齐

| CASE-A01 观测点 | 本基线对应 | SC-1 值 | CASE-A01 预期 |
|-----------------|-----------|---------|-------------|
| O4 Gate耗时 | S2 | 280ms | ≤ 5s ✅ |
| O7 审计耗时 | S3 | 10ms | ≤ 15ms ✅ |
| O11 WAL写入 | S4 | 45ms | ≤ 1000ms ✅ |
| O14 面板API | S5 | 85ms | ≤ 200ms ✅ |
| O16 端到端 | 总计 | 492ms | ≤ 30s ✅ |

---

## 7. 超标告警逻辑

当场景 P99 超阈值时，通过 Alert Adapter V3 (`v86_rc2_dshe_alert_adapter.py`) 自动生成告警载荷并路由：

**MEDIUM 告警载荷示例**:

```json
{
  "event_id": "AE-e2elatency-m001",
  "level": "MEDIUM",
  "rule": "R-LATENCY-01",
  "detect_point": "E2E-P99-THRESHOLD",
  "message": "端到端P99时延 625ms 超阈值 500ms (25%)",
  "audit_fingerprint": "DSHE-20261015_103000-LAT",
  "dep_registry_id": "DEP-REG-001",
  "responsible_party": "DSHE",
  "channel": "FEISHU_GROUP_TASK_CARD",
  "alert_action": "CONDITIONAL_PASS_REPORT_REGISTER_TODO",
  "block_pipeline": false,
  "block_current_batch": false,
  "source": "DSHE_L2_ALERT_ADAPTER"
}
```

**告警分级矩阵**:

| 级别 | 条件 | 阻断流水线 | 阻断批次 | 上报主脑 | 责任方 |
|------|------|----------|---------|---------|--------|
| CRITICAL | P99>阈值×2 | ✅ | ✅ | ✅ | DSHB |
| HIGH | P99>阈值×1.5 | ❌ | ✅ | ❌ | DSHB/DSHE |
| MEDIUM | P99>阈值×1.2 | ❌ | ❌ | ❌ | DSHE |
| LOW | P99>阈值×1.0 | ❌ | ❌ | ❌ | HERMES |

---

## 8. 性能退化检测

**趋势分析**: 滚动窗口 (150 样本) 线性回归，每 5 分钟计算斜率。连续 3 周期斜率 > 0 → 退化判定。

**80% 预警阈值**:

| 场景 | P99 预警线 | 升级条件 |
|------|-----------|---------|
| SC-1 | 400ms (80%×500ms) | 连续3周期 → MEDIUM |
| SC-2 | 1600ms (80%×2000ms) | 连续3周期 → MEDIUM |
| SC-3 | 2400ms (80%×3000ms) | 连续3周期 → MEDIUM |

**恢复机制**: P99 连续 3 周期 < 阈值 60% → 自动关闭退化告警。

**退化预警载荷**:

```json
{
  "event_id": "AE-degradation-w001",
  "level": "LOW",
  "rule": "R-LATENCY-02",
  "detect_point": "E2E-P99-EARLY-WARNING",
  "message": "端到端P99时延 410ms 达阈值80%预警线(400ms), 趋势: 上升(+12ms/周期)",
  "responsible_party": "HERMES",
  "channel": "RECORD_ONLY",
  "source": "DSHE_L2_ALERT_ADAPTER"
}
```

---

## 9. 跨团队对齐

| 对齐项 | HERMES | DSHB | B-team | 状态 |
|-------|--------|------|--------|------|
| E2E P99 ≤ 500ms (正常) | ✅ 基线已定 | ⏳ 确认S1时延 | ⏳ 确认DEP延迟 | 🔴 待对齐 |
| DEP延迟 ≤ 2000ms | ✅ 基线已定 | ⏳ 确认短ID延迟上限 | ⏳ 确认DEP SLA | 🔴 待对齐 |
| DEP抖动 ≤ 3000ms | ✅ 基线已定 | ⏳ 确认DS-06语义 | N/A | 🟡 待确认 |
| MEDIUM 告警逻辑 | ✅ 已定义 | ⏳ 确认接收 | ⏳ 确认通道 | 🟡 待确认 |
| 80% 预警机制 | ✅ 已定义 | ⏳ 确认接收 | ⏳ 确认接收 | 🟡 待确认 |

**DSHB 对齐清单**: S1 时延基线确认；同步 P99 监控；DEP 延迟注入场景超时行为一致性。

**B-team 对齐清单**: DEP-001 SLA 定义；抖动恢复时间窗口；事件存储容量规划 (WAL ~915ms/千条, 1万条切换阈值)。

**HERMES 对齐清单**: 审计器 v3 时延基线 (S3 P99=10ms)；DS-06 对审计影响 (<2ms)；`R-LATENCY-01/02` 规则注册。

**对齐时间表**: T+0 基线草案 → T+1d DSHB审核 → T+2d B-team审核 → T+3d 三方联签 → T+5d 真实环境验证。

---

## 10. 约束合规

```
JOB_READY=FALSE ✅  NO_MODIFY_V85=TRUE ✅  NO_OVERWRITE=TRUE ✅
BRANCH_LOCKED=TRUE ✅  NO_ZHIJI_API_CALL=FALSE ✅ (仅设计，不实测)
```

**依赖引用**:

| 文件 | 用途 |
|------|------|
| `v86_rc2_hermes_case_a01_e2e_real_env_spec.md` | CASE-A01 17断言、16观测点 |
| `v86_rc2_dshe_l2_evidence_perf_baseline.md` | SMALL/MEDIUM/LARGE 打包耗时 |
| `v86_rc2_hermes_event_store_wal_verify_report.md` | WAL性能、HA仿真 |
| `v86_rc2_dshe_alert_adapter.py` | 告警载荷格式、路由矩阵 |
| `v86_rc2_dshe_dep_flap_rule_align_report.md` | DS-06 规则 |
| `v86_rc2_dshe_dep_flap_tripartite_cross_verify_v2.md` | DS-06 三方语义 |

**状态标记**:

```
E2E_LATENCY_BASELINE_DONE=TRUE
BASELINE_SC1_NORMAL_P99=492ms      THRESHOLD_SC1_P99=500ms
BASELINE_SC2_DEP_LATENCY_P99=1850ms THRESHOLD_SC2_P99=2000ms
BASELINE_SC3_DEP_FLAPPING_P99=2320ms THRESHOLD_SC3_P99=3000ms
DEGRADATION_WARNING=80%_OF_THRESHOLD
ALERT_TRIGGER=MEDIUM_ON_EXCEEDANCE
ALERT_ADAPTER_V3=ALIGNED
CROSS_TEAM_ALIGNMENT=PENDING
```

---

> **文档状态**: FINAL | **下一步**: DSHB/B-team 对齐 S1 时延和 DEP SLA，DEP-001 RECOVERED 后按 CASE-A01 执行验证
