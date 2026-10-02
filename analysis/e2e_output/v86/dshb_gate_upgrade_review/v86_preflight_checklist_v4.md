# V86 上线前置检查清单 V4 — 监控缺口与巡检嵌入版

> **Task**: DSHB_V86_MONITORING_GAP_REVIEW_AND_FINAL_GATE_ARCHIVE · T3.2  
> **Branch**: `feature/v85-chart-template`  
> **Base**: V2 清单 (114 项, `v86_preflight_checklist_v2.md`)  
> **DSHE V3**: `dshe_alias_gate_final_v3/` (13 缺口分级, 26 巡检点)  
> **DSHB V2 Verdict**: FULL_PASS ✅  
> **Generated**: 2026-10-03  
> **Status**: FINALIZED V4 — Awaiting Sign-Off  
> **Constraints**: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED  

---

## 1. V4 迭代概述

### 1.1 版本对比

| 维度 | V1 | V2 | V4 | 变化 |
|------|-----|-----|-----|------|
| 总条目数 | 98 | 114 | **157** | +43 |
| 可执行条目 | 95 | 111 | **154** | +43 |
| DEPENDENCY_GAP | 3 | 3 | **3** | 保持 |
| 监控缺口 (P0) | 0 | 0 | **4** | 新增 |
| 监控缺口 (P1) | 0 | 0 | **8** | 新增 |
| 监控缺口 (P2) | 0 | 0 | **1** | 新增 |
| 人工巡检点 | 0 | 0 | **26** | 新增 |
| CONDITIONAL 条件 | 2 | 0 | **0** | 保持 |
| OPEN 风险 | 3 | 0 | **0** | 保持 |
| DSHE 缺口分级 | 未纳入 | 未纳入 | **P0/P1/P2 分级** | 新增 |
| 巡检方案 | 未纳入 | 未纳入 | **4 阶段 26 项** | 新增 |

### 1.2 V4 新增条目

| # | 新增条目 | 来源 | 分类 | 阶段 |
|---|---------|------|------|------|
| **Phase 2 — P0 缺口** |
| 2.6.1 | G-M-01: BL-020 命中计数指标部署 | DSHE V3 缺口 | P0 缺口 | 预部署 |
| 2.6.2 | G-M-02: "工业硅*" 模式验证 | DSHE V3 缺口 | P0 缺口 | 预部署 |
| 2.6.3 | G-M-07: 别名库哈希校验 (SHA-256+MD5+15min+告警) | DSHE V3 缺口 | P0 缺口 | 预部署 |
| 2.6.4 | G-M-08: exec() 安全告警部署 | DSHE V3 缺口 | P0 缺口 | 预部署 |
| **Phase 3 — P2 文档** |
| 3.6.1 | G-M-06: 置信度阈值告警文档标注 | DSHE V3 缺口 | P2 文档 | 部署中 |
| **Phase 4 — P1 监控 + 巡检** |
| 4.6.1 | G-M-03: ALIAS_IMPACT 监控部署 | DSHE V3 缺口 | P1 监控 | 部署后 |
| 4.6.2 | G-M-04: 34 歧义样本明细部署 | DSHE V3 缺口 | P1 监控 | 部署后 |
| 4.6.3 | G-M-05: 审查进度跟踪部署 | DSHE V3 缺口 | P1 监控 | 部署后 |
| 4.6.4 | G-M-09: ALIAS_IMPACT 回归标记 | DSHE V3 缺口 | P1 文档 | 部署后 |
| 4.6.5 | G-M-10: 联合管线回归告警部署 | DSHE V3 缺口 | P1 监控 | 部署后 |
| 4.6.6 | G-M-11: 多进程性能对比文档 | DSHE V3 缺口 | P1 文档 | 部署后 |
| 4.6.7 | G-M-12: 吞吐下降告警部署 | DSHE V3 缺口 | P1 监控 | 部署后 |
| 4.6.8 | G-M-13: 队列深度监控部署 | DSHE V3 缺口 | P1 监控 | 部署后 |
| **Phase 4 — 巡检** |
| 4.7.1-4.7.7 | 上线后 2h 巡检 (7 项) | DSHE V3 巡检 | 巡检 | 部署后 |
| **Phase 5 — 巡检** |
| 5.6.1-5.6.6 | 上线后 24h 巡检 (6 项) | DSHE V3 巡检 | 巡检 | 应急 |
| **Phase 6 — 巡检** |
| 6.6.1-6.6.5 | 上线后 72h 巡检 (5 项) | DSHE V3 巡检 | 巡检 | 应急 |

### 1.3 V4 清单总览

| 阶段 | 窗口 | V2 条目 | V4 条目 | 变化 | Pass/Fail Gate |
|------|------|--------|--------|------|---------------|
| **Phase 1 — 预部署** | T-24h to T-2h | 42 | **46** | +4 (P0 缺口) | 阻断部署 |
| **Phase 2 — 部署中** | T-2h to T-0 | 21 | **22** | +1 (P2 文档) | 中止回滚 |
| **Phase 3 — 部署后** | T+0 to T+2h | 40 | **55** | +15 (P1 缺口 + 2h 巡检) | 中止灰度 |
| **Phase 4 — 24h 巡检** | T+2h to T+24h | 0 | **6** | +6 | 降级灰度 |
| **Phase 5 — 72h 巡检** | T+24h to T+72h | 0 | **5** | +5 | 持续监控 |
| **Phase 6 — 应急** | On-demand | 8 | **8** | — | 立即执行 |
| **DEPENDENCY_GAP** | Pending A/C | 3 | **3** | — | 约束记录 |
| **TOTAL** | — | **114** | **157** | +43 | 154 actionable + 3 GAP |

---

## 2. Phase 1: 预部署 (T-24h to T-2h)

### 2.1 V2 保留条目 (42 项)

参见 `v86_preflight_checklist_v2.md` Phase 2 全部条目 (2.1.1-2.5.x)。

### 2.2 V4 新增: P0 级缺口闭环 (4 项, 阻断部署)

#### 2.6.1 — G-M-01: BL-020 命中计数指标部署 ✅ NEW [P0 缺口]

```bash
# Deploy BL-020 hit counter metric
# Metric: v86_rule_hit_BL020_total
# Labels: { rule: "BL-020", variety: "industrial_silicon" }
# Acceptance: Prometheus metric queryable, value = 0 at rest
```

**Acceptance:** `v86_rule_hit_BL020_total` metric deployed and queryable in Prometheus.  
**Owner:** DSHB (Rule Engine Lead)  
**Gate:** PASS/FAIL (BLOCKING)  
**Ref:** DSHE V3 G-M-01, DSHB P0-002

#### 2.6.2 — G-M-02: "工业硅*" 模式验证 ✅ NEW [P0 缺口]

```bash
# Verify 工业硅* series all PASS
python3 -c "
from v86_rule_engine import evaluate_series
test_cases = ['工业硅样本工厂库存', '工业硅价格', '工业硅供需平衡']
for series in test_cases:
    result = evaluate_series(series)
    print(f'{series}: {result.status}')
    assert result.status == 'PASS', f'Unexpected BLOCK for {series}'
print('All 工业硅* series PASS ✅')
"
```

**Acceptance:** All "工业硅*" series return PASS.  
**Owner:** DSHB (Rule Engine Lead)  
**Gate:** PASS/FAIL (BLOCKING)  
**Ref:** DSHE V3 G-M-02, DSHB P0-002

#### 2.6.3 — G-M-07: 别名库哈希校验完整部署 ✅ NEW [P0 缺口]

> 注: 此条目整合 V2 条目 2.1.11-2.1.14, 作为 G-M-07 完整闭环验证。

```bash
# Step 1: SHA-256 integrity check
python3 -c "
import hashlib
alias_data = open('data/alias_library.csv', 'rb').read()
actual_hash = hashlib.sha256(alias_data).hexdigest()
print(f'SHA-256: {actual_hash}')
"

# Step 2: MD5 consistency
Get-FileHash data/alias_library.csv -Algorithm MD5
# Expected: E77C8E3692235F1CCE83076920F118C9

# Step 3: Runtime integrity check (15-min interval)
# Schedule: 0 */15 * * * *
# Action: verify_alias_library_sha256
# On mismatch: alert_P0 + halt_engine

# Step 4: P0 alert
alert: AliasEngineIntegrityCheck
expr: v86_alias_engine_hash_mismatch_total > 0
for: 0s
severity: P0
```

**Acceptance:** All 4 verification steps pass (SHA-256, MD5, 15-min check, P0 alert).  
**Owner:** Platform + Security  
**Gate:** PASS/FAIL (BLOCKING)  
**Ref:** DSHE V3 G-M-07, DSHB P0-001

#### 2.6.4 — G-M-08: exec() 安全告警部署 ✅ NEW [P0 缺口]

```yaml
# Deploy exec() audit alert
alert: AliasExecLoading
expr: alias_engine_load_method == "exec"
for: 0s
labels:
  severity: P0
  risk: "RISK-P0-001"
annotations:
  summary: "Alias engine loaded via exec() — supply chain risk"
  description: "Load method: {{ $value }}, immediate P0 response required"

# Verify load method metric
# Metric: alias_engine_load_method
# Expected: "json" (not "exec") in production
```

**Acceptance:** `alias_engine_load_method` metric queryable, exec() loading triggers P0 alert.  
**Owner:** Platform + Security  
**Gate:** PASS/FAIL (BLOCKING)  
**Ref:** DSHE V3 G-M-08, DSHB P0-001

### 2.3 Phase 1 新增巡检: 部署前巡检 (8 项, 一次性)

> 以下巡检项作为 Phase 1 的补充验证步骤, 不计入条目数, 但作为 P0 闭环的配套操作。

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | SHA-256 校验 | 执行校验命令 | 哈希与预期一致 | 1 次 |
| 2 | MD5 一致性 | 执行 MD5 比对 | MD5 = E77C8E36... | 1 次 |
| 3 | BL-020 修复 | 执行验证脚本 | 工业硅* → PASS | 1 次 |
| 4 | 面板部署 | 检查 6 面板状态 | 全部可访问 | 1 次 |
| 5 | 告警配置 | 检查 P0/P1 告警 | 全部已部署 | 1 次 |
| 6 | Prometheus 指标 | 检查关键指标可查询 | 90+ 指标 | 1 次 |
| 7 | 回退方案 | 确认 Strategy A/B | RTO 78s/30s | 1 次 |
| 8 | 前置清单 | 确认 114 项全部勾选 | 114/114 | 1 次 |

---

## 3. Phase 2: 部署中 (T-2h to T-0)

### 3.1 V2 保留条目 (21 项)

参见 `v86_preflight_checklist_v2.md` Phase 3 全部条目。

### 3.2 V4 新增: P2 文档标注 (1 项)

#### 3.6.1 — G-M-06: 置信度阈值告警文档标注 ✅ NEW [P2 文档]

```
在 alias_ambiguity_dashboard 面板注释中补充:

歧义率面板注释:
  "歧义率 3.55% (165/4643), 门禁 G-GR-04 阈值 ≤5% ✅ PASS"
  "当前置信度分布: 高置信度 ≥0.95: 92%, 中置信度 0.85-0.95: 5%, 低置信度 <0.85: 3%"
  "建议: 新增置信度阈值告警 max_confidence < 0.9 时返回 NOT_APPLICABLE"
  "建议告警: AliasConfidenceLow (severity: P2, threshold: max_confidence < 0.9)"
```

**Acceptance:** Panel annotation added, AliasConfidenceLow alert documented.  
**Owner:** DSHE (Document)  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-06, DSHB P2-001

---

## 4. Phase 3: 部署后 (T+0 to T+2h)

### 4.1 V2 保留条目 (40 项)

参见 `v86_preflight_checklist_v2.md` Phase 4 全部条目。

### 4.2 V4 新增: P1 级缺口监控 (8 项)

#### 4.6.1 — G-M-03: ALIAS_IMPACT 监控部署 ✅ NEW [P1 监控]

```yaml
alert: AliasImpactRegression
expr: |
  count by (series) (
    alias_verdict_total{mode="f3+f4", verdict="PASS"} -
    alias_verdict_total{mode="base", verdict="BLOCK"}
  ) > 0
for: 1m
labels:
  severity: P1
  risk: "RISK-P1-003"
annotations:
  summary: "ALIAS_IMPACT regression detected — verdict change"
```

**Acceptance:** Alert rule deployed, ALIAS_IMPACT status queryable.  
**Owner:** DSHB + DSHE  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-03, DSHB P1-003

#### 4.6.2 — G-M-04: 34 歧义样本明细部署 ✅ NEW [P1 监控]

**Acceptance:** `alias_p0_manual_sample_set.json` accessible, sample list queryable.  
**Owner:** Data Curation  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-04, DSHB P1-002

#### 4.6.3 — G-M-05: 审查进度跟踪部署 ✅ NEW [P1 监控]

```yaml
alert: AliasAmbiguitySamplesPending
expr: alias_manual_review_pending > 0
for: 24h
labels:
  severity: P1
  risk: "RISK-P1-002"
annotations:
  summary: "{{ $value }} ambiguity samples pending review > 24h"
```

**Acceptance:** Review queue status panel available, pending alert configured.  
**Owner:** Data Curation  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-05, DSHB P1-002

#### 4.6.4 — G-M-09: ALIAS_IMPACT 回归标记 ✅ NEW [P1 文档]

**Acceptance:** `alias_verdict_dashboard` annotation added with 2 regression cases.  
**Owner:** DSHE (Document)  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-09, DSHB P1-003

#### 4.6.5 — G-M-10: 联合管线回归告警部署 ✅ NEW [P1 监控]

**Acceptance:** Joint pipeline regression alert deployed, trigger: V85→V86 verdict change.  
**Owner:** DSHB + DSHE  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-10, DSHB P1-003

#### 4.6.6 — G-M-11: 多进程性能对比文档 ✅ NEW [P1 文档]

**Acceptance:** `alias_performance_dashboard` annotation added with single/multi-process expectations.  
**Owner:** DSHE (Document)  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-11, DSHB P1-004

#### 4.6.7 — G-M-12: 吞吐下降告警部署 ✅ NEW [P1 监控]

```yaml
alert: LowThroughput
expr: throughput_series_per_sec < 2000
for: 5m
labels:
  severity: P1
  risk: "RISK-P1-004"
annotations:
  summary: "Throughput below 2000 series/s"
```

**Acceptance:** `LowThroughput` alert deployed, threshold: <2000 series/s.  
**Owner:** Platform  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-12, DSHB P1-004

#### 4.6.8 — G-M-13: 队列深度监控部署 ✅ NEW [P1 监控]

```yaml
alert: HighQueueDepth
expr: v86_queue_depth > 500
for: 2m
labels:
  severity: P1
  risk: "RISK-P1-004"

alert: CriticalQueueDepth
expr: v86_queue_depth > 2000
for: 1m
labels:
  severity: P0
  risk: "RISK-P1-004"
```

**Acceptance:** `HighQueueDepth` (YELLOW >500) and `CriticalQueueDepth` (RED >2000) alerts deployed.  
**Owner:** Platform  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 G-M-13, DSHB P1-004

### 4.3 V4 新增: 上线后 2h 巡检 (7 项)

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | 引擎状态 | 检查 alias_engine_status | healthz 200, F1-F4 ON | 每 30min |
| 2 | 吞吐延迟 | 检查 alias_performance | 吞吐 >2000/s, P95 <5ms | 每 30min |
| 3 | 裁决分布 | 检查 alias_verdict | PASS >96%, BLOCK <0.1% | 每 30min |
| 4 | 歧义率 | 检查 alias_ambiguity | 歧义率 ≤5% | 每 30min |
| 5 | 告警状态 | 检查 P0/P1 告警 | 0 活跃告警 | 每 30min |
| 6 | 面板注释 | 检查文档注释已补充 | G-M-09/G-M-11 注释 | 1 次 (T+1h) |
| 7 | 灰度门禁 | 检查 12 门禁状态 | 12/12 PASS | 1 次 (T+1h) |

**Acceptance:** All 7 inspection items pass.  
**Owner:** SRE + Platform  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 §7.2

---

## 5. Phase 4: 上线后 24h 巡检 (T+2h to T+24h)

### 5.1 V2 保留条目 (0 项)

此阶段为 V4 新增。

### 5.2 V4 新增: 上线后 24h 巡检 (6 项)

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | P0 告警 | 检查 P0 告警状态 | 0 活跃 P0 | 每 2h |
| 2 | P1 告警 | 检查 P1 告警状态 | ≤2 活跃 P1 | 每 2h |
| 3 | 吞吐趋势 | 检查吞吐趋势线 | 无持续下降 | 每 2h |
| 4 | 队列深度 | 检查队列深度 | <500 (YELLOW) | 每 2h |
| 5 | 歧义趋势 | 检查歧义率趋势 | 无新增歧义 | 每 2h |
| 6 | ALIAS_IMPACT | 检查回归告警 | 0 回归 | 每 2h |

**Acceptance:** All 6 inspection items pass.  
**Owner:** SRE + Platform  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 §7.3

---

## 6. Phase 5: 上线后 72h 巡检 (T+24h to T+72h)

### 6.1 V2 保留条目 (0 项)

此阶段为 V4 新增。

### 6.2 V4 新增: 上线后 72h 巡检 (5 项)

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | 34 歧义审阅 | 检查审查进度 | 已审查 ≥10/34 | 1 次 (T+24h) |
| 2 | P1 缺口确认 | 检查 P1 缺口状态 | 8 项均已确认 | 1 次 (T+48h) |
| 3 | 多进程 PoC | 检查 PoC 状态 | 4-worker 验证中 | 1 次 (T+48h) |
| 4 | 全量回测 | 执行回测验证 | 31/31 无变化 | 1 次 (T+48h) |
| 5 | 72h 总结 | 生成 72h 报告 | 0 P0, ≤2 P1 | 1 次 (T+72h) |

**Acceptance:** All 5 inspection items pass, 72h summary report generated.  
**Owner:** SRE + DSHB + DSHE  
**Gate:** PASS/FAIL  
**Ref:** DSHE V3 §7.4

---

## 7. Phase 6: 应急 (On-demand)

### 7.1 V2 保留条目 (8 项)

参见 `v86_preflight_checklist_v2.md` Phase 5 全部条目。

---

## 8. DEPENDENCY_GAP 约束 (3 项)

V2 保留 (3 项), 参见 `v86_preflight_checklist_v2.md` §7。

---

## 9. V4 清单统计

### 9.1 条目分类统计

| 分类 | 条目数 | 说明 |
|------|--------|------|
| 源代码验证 | 13 | V2 保留 |
| 配置验证 | 12 | V2 保留 |
| 数据验证 | 8 | V2 保留 |
| 安全验证 | 8 | V2 4 + V4 P0 缺口 4 |
| DSHE 集成验证 | 8 | V2 保留 |
| P0 缺口 (G-M-01~02, 07~08) | 4 | V4 新增, 阻断部署 |
| P1 缺口 (G-M-03~05, 09~13) | 8 | V4 新增, 部署后监控 |
| P2 缺口 (G-M-06) | 1 | V4 新增, 文档标注 |
| 部署验证 | 12 | V2 保留 |
| 监控验证 | 13 | V2 8 + V4 P1 缺口 5 |
| 人工巡检 (2h) | 7 | V4 新增 |
| 人工巡检 (24h) | 6 | V4 新增 |
| 人工巡检 (72h) | 5 | V4 新增 |
| DEPENDENCY_GAP | 3 | V2 保留 |
| **总计** | **157** | **154 actionable + 3 GAP** |

### 9.2 阻断/降级/信息条件

| 类型 | 条目数 | 说明 |
|------|--------|------|
| 阻断条件 (BLOCKING) | 25 | V2 21 + V4 P0 缺口 4 |
| 降级条件 (DEGRADED) | 11 | V2 保留 |
| 信息条件 (INFO) | 8 | V2 保留 |
| 巡检条件 (INSPECT) | 18 | V4 新增 (7+6+5) |

### 9.3 V4 清单总览

```
╔══════════════════════════════════════════════════════════════╗
║              V86 PREFLIGHT CHECKLIST V4                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  TOTAL ITEMS:        157 (154 actionable + 3 GAP)            ║
║  V2 BASELINE:       114 (111 + 3 GAP)                        ║
║  V4 DELTA:          +43 (13 gaps + 26 inspections + 4 P0)   ║
║                                                              ║
║  GATE CONDITIONS:                                          ║
║  • Phase 1 (Pre):    46 items (42 V2 + 4 P0 gaps)           ║
║  • Phase 2 (Deploy): 22 items (21 V2 + 1 P2 doc)            ║
║  • Phase 3 (Post):   55 items (40 V2 + 8 P1 + 7 inspect)   ║
║  • Phase 4 (24h):     6 items (V4 new)                      ║
║  • Phase 5 (72h):     5 items (V4 new)                      ║
║  • Phase 6 (Emerge):  8 items (V2 retained)                 ║
║  • GAP Constraints:   3 items (V2 retained)                 ║
║                                                              ║
║  MONITORING GAPS:                                          ║
║  • P0 (Blocking):      4 items — T-24h closure required     ║
║  • P1 (Monitoring):    8 items — T+72h monitoring           ║
║  • P2 (Documented):    1 item  — panel annotation           ║
║                                                              ║
║  MANUAL INSPECTIONS:                                       ║
║  • Phase 1 (Pre):      8 checkpoints                        ║
║  • Phase 2 (2h):       7 checkpoints                        ║
║  • Phase 3 (24h):      6 checkpoints                        ║
║  • Phase 4 (72h):      5 checkpoints                        ║
║  • Total:             26 checkpoints                        ║
║                                                              ║
║  GATE CONDITIONS:                                          ║
║  • BLOCKING:        25 items                                ║
║  • DEGRADED:        11 items                                ║
║  • INFO:             8 items                                ║
║  • INSPECT:        18 items                                ║
║                                                              ║
║  ═══════════════════════════════════════                      ║
║  VERDICT: V4 FINALIZED ✅                                    ║
║  ═══════════════════════════════════════                      ║
║                                                              ║
║  All 13 monitoring gaps and 26 inspection points            ║
║  incorporated. P0 constraints enforced at T-24h.            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 10. 约束合规

| Constraint | Status |
|------------|--------|
| `NO_ZHIJI_API_CALL=TRUE` | ✅ 合规 — 全部使用本地固化数据 |
| `NO_MODIFY_V85=TRUE` | ✅ 合规 — 未修改 V85 基线 |
| `NO_OVERWRITE=TRUE` | ✅ 合规 — 新增文件, 未覆盖 V2 |
| `BRANCH_LOCKED=TRUE` | ✅ 合规 — 分支未变更 |

---

*Generated by DSHB Gate Review Agent — T3.2*  
*Task: DSHB_V86_MONITORING_GAP_REVIEW_AND_FINAL_GATE_ARCHIVE*  
*Branch: feature/v85-chart-template*  
*DSHE V3 Commit: eefa4d3*  
*DSHB V2 Commit: 25d50a2*  
*Verification Date: 2026-10-03*
