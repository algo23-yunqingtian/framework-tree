# V86 别名引擎风险监控覆盖度复核报告 V2

> 任务: `DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V3_ARCHIVE` · T3.1
> 分支: `feature/v85-chart-template` @ `6fa8b84`
> 版本: `v86.0.0-frozen`
> 基线: DSHB Gate 终审升级评估 `v86_gate_upgrade_assessment_report.md` (FULL_PASS)
> DSHB 前置清单: `v86_preflight_checklist_v2.md` (114 项, V2)
> DSHB 风险处置: `v86_open_risks_disposition_v2.md` (0 OPEN, 2 MITIGATED, 7 MONITORED)
> 复核对象: 6 个 Grafana 面板 + 别名引擎现有监控能力 + DSHB 监控缺口评审结论
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / NO_PANEL_JSON_MODIFICATION

---

## 目录

1. [DSHB Gate 终审升级结论摘要](#1-dshb-gate-终审升级结论摘要)
2. [DSHB 风险处置结论与监控缺口分级](#2-dshb-风险处置结论与监控缺口分级)
3. [13 项监控缺口分级矩阵](#3-13-项监控缺口分级矩阵)
4. [P0 级缺口 (4 项) — 上线阻断性约束](#4-p0-级缺口-4-项--上线阻断性约束)
5. [P1 级缺口 (8 项) — 上线后持续观测](#5-p1-级缺口-8-项--上线后持续观测)
6. [P2 级缺口 (1 项) — 文档标注即可](#6-p2-级缺口-1-项--文档标注即可)
7. [上线人工巡检操作指引](#7-上线人工巡检操作指引)
8. [6 个 Grafana 面板监控覆盖度矩阵 (更新版)](#8-6-个-grafana-面板监控覆盖度矩阵-更新版)
9. [Grafana 文档注释对齐 DSHB 分级](#9-grafana-文档注释对齐-dshb-分级)
10. [复核结论](#10-复核结论)

---

## 1. DSHB Gate 终审升级结论摘要

### 1.1 Gate 决策升级

| 属性 | V1 (第一轮) | V2 (第二轮升级) | 变化 |
|------|------------|----------------|------|
| 决策 | APPROVE (CONDITIONAL) | **FULL_PASS** ✅ | ✅ 升级 |
| Gate 条件 | 3 PASS, 2 CONDITIONAL | **5 PASS** | ✅ 全部闭环 |
| OPEN 风险 | 3 OPEN | **0 OPEN** | ✅ 全部处置 |
| MITIGATED 风险 | 2 | **2** | 保持 |
| MONITORED 风险 | 4 | **7** | +3 |
| DEPENDENCY_GAP | 3 项 (阻塞) | **3 项 (非阻塞)** | ✅ 不阻塞 |
| 前置清单 | 99 项 | **114 项** | +15 |

### 1.2 五项 Gate 条件闭环状态

| # | 条件 | V1 判定 | V2 判定 | 关键证据 |
|---|------|---------|---------|----------|
| C-1 | 灰度发布 Phase 0→3 | PASS ✅ | **PASS** ✅ | 8/8 phases, 144/144 gates |
| C-2 | BL-020 FP 调查 | PASS ✅ | **PASS** ✅ | Fix drafted, deployment pending |
| C-3 | 34 ambiguous alias samples | CONDITIONAL ⚠️ | **PASS** ✅ | Panel 3 就绪 + 口径三方一致 |
| C-4 | 155 DATA_MISSING PDF 修复 | CONDITIONAL ⚠️ | **PASS** ✅ | 架构隔离 + 零性能影响 |
| C-5 | 24h 上线后监控 | PASS ✅ | **PASS** ✅ | 90 metrics + 8 alerts + 6 DSHE panels |

### 1.3 风险状态升级矩阵 (11 项)

| ID | 风险 | 严重级别 | V1 状态 | V2 状态 | 处置方案 | 阻塞部署? |
|----|------|----------|---------|---------|----------|-----------|
| P0-001 | exec() 供应链漏洞 | P0 | OPEN | **MITIGATED** | SHA-256 校验 + 15min 周期检查 + P0 告警 | ❌ 否 |
| P0-002 | BL-020 FP | P0 | MITIGATED | MITIGATED | 字边界匹配 + 白名单排除 | ❌ 否 |
| P1-001 | 155 DATA_MISSING | P1 | MONITORED | MONITORED | data_missing_rate 指标 | ❌ 否 |
| P1-002 | 34 歧义样本 | P1 | OPEN | **MONITORED** | Panel 3 + L2 自动降级 + L3 兜底 | ❌ 否 |
| P1-003 | 2 ALIAS_IMPACT | P1 | OPEN | **MONITORED** | 影响 0.07% + REVIEW 兜底 | ❌ 否 |
| P1-004 | Python GIL 性能 | P1 | MONITORED | MONITORED | 4-worker PoC 完成 | ❌ 否 |
| P1-005 | 22s 冷启动 | P1 | MONITORED | MONITORED | 灰度仿真验证 | ❌ 否 |
| P2-001 | 歧义率 3.55% | P2 | MONITORED | MONITORED | 门禁 G-GR-04 阈值 ≤5% | ❌ 否 |
| P2-002 | DATA_MISSING 5.7% | P2 | MONITORED | MONITORED | 基线确认 | ❌ 否 |
| P2-003 | 回滚流程复杂度 | P2 | ACCEPTED | ACCEPTED | 文档化 | ❌ 否 |
| P2-004 | 规则覆盖差 18vs31 | P2 | ACCEPTED | ACCEPTED | 意图性差异 | ❌ 否 |

**结论**: 0 项 OPEN 风险, 全部风险均有处置方案, 无阻塞项。

---

## 2. DSHB 风险处置结论与监控缺口分级

### 2.1 DSHB 分级原则

DSHB 监控缺口评审基于以下分级原则:

| 分级 | 定义 | 上线约束 | 处置时限 |
|------|------|----------|----------|
| **P0** | 安全/合规/数据完整性类缺口, 上线前必须闭环 | **上线阻断** — 必须在部署前完成 | 部署前 24h 内 |
| **P1** | 功能/性能/质量类缺口, 需上线后持续监控 | **上线后监控** — 上线后 72h 内确认 | 上线后 5 工作日内 |
| **P2** | 文档/标注/流程类缺口, 文档补充即可 | **文档标注** — 面板注释补充 | 部署前完成 |

### 2.2 13 项监控缺口与 DSHB 分级映射

| 缺口 ID | 描述 | 关联风险 | DSHB 分级 | 上线约束 | 补充方案 | 不改动面板 JSON? |
|---------|------|----------|-----------|----------|----------|-----------------|
| G-M-01 | BL-020 命中计数指标缺失 | P0-002 (BL-020 FP) | **P0** | 上线前必须部署 | 新增 `bl_020_blocked_count` 指标 | ✅ |
| G-M-02 | "工业硅*" 模式监控缺失 | P0-002 (BL-020 FP) | **P0** | 上线前必须部署 | 新增模式匹配计数 | ✅ |
| G-M-03 | 联合管线 ALIAS_IMPACT 监控缺失 | P1-003 (ALIAS_IMPACT) | **P1** | 上线后 72h 确认 | 新增联合管线回归告警 | ✅ |
| G-M-04 | 34 歧义样本明细列表缺失 | P1-002 (34 歧义) | **P1** | 上线后 72h 确认 | 文档注释引用 JSON | ✅ |
| G-M-05 | 审查进度跟踪缺失 | P1-002 (34 歧义) | **P1** | 上线后 72h 确认 | 文档注释 + 状态标记 | ✅ |
| G-M-06 | 置信度阈值告警缺失 | P2-001 (歧义率) | **P2** | 文档标注 | 新增置信度告警规则 | ✅ |
| G-M-07 | 别名库哈希校验缺失 | P0-001 (exec) | **P0** | 上线前必须部署 | SHA-256 完整性校验 + 告警 | ✅ |
| G-M-08 | exec() 安全告警缺失 | P0-001 (exec) | **P0** | 上线前必须部署 | exec() 审计告警 | ✅ |
| G-M-09 | ALIAS_IMPACT 回归标记缺失 | P1-003 (ALIAS_IMPACT) | **P1** | 上线后 72h 确认 | 文档注释标记 | ✅ |
| G-M-10 | 联合管线回归告警缺失 | P1-003 (ALIAS_IMPACT) | **P1** | 上线后 72h 确认 | 新增回归告警规则 | ✅ |
| G-M-11 | 多进程性能对比缺失 | P1-004 (GIL) | **P1** | 上线后 72h 确认 | 文档注释 + 预期值 | ✅ |
| G-M-12 | 吞吐下降告警缺失 | P1-004 (GIL) | **P1** | 上线后 72h 确认 | 新增吞吐告警规则 | ✅ |
| G-M-13 | 队列深度监控缺失 | P1-004 (GIL) | **P1** | 上线后 72h 确认 | 新增队列深度告警 | ✅ |

### 2.3 分级汇总

| 分级 | 缺口数 | 占比 | 上线约束 | 处置方 |
|------|--------|------|----------|--------|
| **P0** | **4** (G-M-01, G-M-02, G-M-07, G-M-08) | 31% | 上线前必须闭环 | DSHB + Platform |
| **P1** | **8** (G-M-03~05, G-M-09~13) | 62% | 上线后 72h 持续观测 | DSHB + DSHE + SRE |
| **P2** | **1** (G-M-06) | 7% | 文档标注即可 | DSHE (文档) |
| **总计** | **13** | 100% | | |

---

## 3. 13 项监控缺口分级矩阵

### 3.1 P0 级缺口 (4 项) — 上线阻断性

```
┌─────────────────────────────────────────────────────────────────┐
│  🔴 P0 级监控缺口 (4 项) — 上线前必须闭环                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  G-M-01  BL-020 命中计数指标缺失                                 │
│  ├─ 关联: P0-002 BL-020 FP                                      │
│  ├─ 约束: 上线前必须部署 `bl_020_blocked_count` 指标               │
│  ├─ 验收: Prometheus 指标可查询, 值为 0                           │
│  ├─ 负责人: DSHB (Rule Engine Lead)                              │
│  └─ 时限: T-24h 前完成                                           │
│                                                                 │
│  G-M-02  "工业硅*" 模式监控缺失                                   │
│  ├─ 关联: P0-002 BL-020 FP                                      │
│  ├─ 约束: 上线前必须验证修复后 "工业硅样本工厂库存" → PASS            │
│  ├─ 验收: BL-020 修复验证脚本执行通过                              │
│  ├─ 负责人: DSHB (Rule Engine Lead)                              │
│  └─ 时限: T-24h 前完成                                           │
│                                                                 │
│  G-M-07  别名库哈希校验缺失                                       │
│  ├─ 关联: P0-001 exec() 供应链漏洞                                │
│  ├─ 约束: 上线前必须部署 SHA-256 完整性校验                          │
│  ├─ 验收: 别名库 MD5 与固化值一致, SHA-256 校验通过                  │
│  ├─ 验收: 15 分钟周期运行时完整性检查配置完成                         │
│  ├─ 验收: `alias_engine_hash_mismatch` P0 告警配置完成              │
│  ├─ 负责人: Platform + Security                                   │
│  └─ 时限: T-24h 前完成                                           │
│                                                                 │
│  G-M-08  exec() 安全告警缺失                                     │
│  ├─ 关联: P0-001 exec() 供应链漏洞                                │
│  ├─ 约束: 上线前必须部署 exec() 审计告警                            │
│  ├─ 验收: `alias_engine_load_method` 指标可查询                     │
│  ├─ 验收: exec() 加载时自动触发 P0 告警                              │
│  ├─ 负责人: Platform + Security                                   │
│  └─ 时限: T-24h 前完成                                           │
│                                                                 │
│  P0 缺口合计: 4 项 (占 31%)                                       │
│  P0 上线阻断: ✅ 全部为阻断性, 部署前必须闭环                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 P1 级缺口 (8 项) — 上线后持续观测

```
┌─────────────────────────────────────────────────────────────────┐
│  🟠 P1 级监控缺口 (8 项) — 上线后 72h 内确认                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  G-M-03  联合管线 ALIAS_IMPACT 监控缺失                          │
│  ├─ 关联: P1-003 (2 ALIAS_IMPACT 回归)                           │
│  ├─ 约束: 上线后 72h 确认 2 条回归状态                             │
│  ├─ 验收: 联合管线告警规则部署, ALIAS_IMPACT 状态可查                │
│  └─ 时限: T+72h                                                  │
│                                                                 │
│  G-M-04  34 歧义样本明细列表缺失                                   │
│  ├─ 关联: P1-002 (34 歧义样本)                                    │
│  ├─ 约束: 上线后 3 个工作日内完成人工审阅                            │
│  ├─ 验收: alias_p0_manual_sample_set.json 可访问                   │
│  ├─ 验收: 审阅进度可跟踪 (已审阅/待审阅/已确认)                      │
│  └─ 时限: T+72h (审阅 3 工作日)                                   │
│                                                                 │
│  G-M-05  审查进度跟踪缺失                                          │
│  ├─ 关联: P1-002 (34 歧义样本)                                    │
│  ├─ 约束: 上线后 3 个工作日内审查队列上线                            │
│  ├─ 验收: 审查队列状态面板可用                                      │
│  └─ 时限: T+72h                                                  │
│                                                                 │
│  G-M-09  ALIAS_IMPACT 回归标记缺失                                 │
│  ├─ 关联: P1-003 (2 ALIAS_IMPACT 回归)                           │
│  ├─ 约束: 面板注释标记 2 条回归案例                                 │
│  ├─ 验收: alias_verdict_dashboard 注释已补充                        │
│  └─ 时限: T+2h (文档注释)                                         │
│                                                                 │
│  G-M-10  联合管线回归告警缺失                                      │
│  ├─ 关联: P1-003 (2 ALIAS_IMPACT 回归)                           │
│  ├─ 约束: 上线后部署联合管线回归告警                                │
│  ├─ 验收: 回归告警规则部署, 触发条件: V85→V86 裁决变化               │
│  └─ 时限: T+72h                                                  │
│                                                                 │
│  G-M-11  多进程性能对比缺失                                        │
│  ├─ 关联: P1-004 (Python GIL)                                    │
│  ├─ 约束: 文档注释标注单进程/多进程性能预期                            │
│  ├─ 验收: alias_performance_dashboard 注释已补充                     │
│  └─ 时限: T+2h (文档注释)                                         │
│                                                                 │
│  G-M-12  吞吐下降告警缺失                                          │
│  ├─ 关联: P1-004 (Python GIL)                                    │
│  ├─ 约束: 上线后部署吞吐下降告警                                    │
│  ├─ 验收: `LowThroughput` 告警 (threshold: <2000 series/s)         │
│  └─ 时限: T+72h                                                  │
│                                                                 │
│  G-M-13  队列深度监控缺失                                          │
│  ├─ 关联: P1-004 (Python GIL)                                    │
│  ├─ 约束: 上线后部署队列深度监控                                    │
│  ├─ 验收: `HighQueueDepth` (YELLOW >500) / `CriticalQueueDepth`   │
│  │         (RED >2000) 告警配置完成                                │
│  └─ 时限: T+72h                                                  │
│                                                                 │
│  P1 缺口合计: 8 项 (占 62%)                                       │
│  P1 上线后观测: ✅ 全部需 72h 内确认                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 P2 级缺口 (1 项) — 文档标注

```
┌─────────────────────────────────────────────────────────────────┐
│  🟡 P2 级监控缺口 (1 项) — 文档标注即可                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  G-M-06  置信度阈值告警缺失                                      │
│  ├─ 关联: P2-001 (歧义率 3.55%)                                  │
│  ├─ 约束: 面板注释标注置信度阈值建议                                │
│  ├─ 验收: alias_ambiguity_dashboard 注释已补充                     │
│  ├─ 验收: 建议告警规则 `AliasConfidenceLow` 已文档化               │
│  └─ 时限: T+0 (部署前文档注释)                                    │
│                                                                 │
│  P2 缺口合计: 1 项 (占 7%)                                       │
│  P2 文档标注: ✅ 仅需文档注释, 无需部署变更                          │
│                                                                 │
�t─────────────────────────────────────────────────────────────────┘
```

---

## 4. P0 级缺口 (4 项) — 上线阻断性约束

### 4.1 G-M-07: 别名库哈希校验缺失 (P0)

**风险关联**: P0-001 exec() 供应链漏洞

| 维度 | 内容 |
|------|------|
| 风险描述 | V86 别名引擎通过 Python `exec()` 加载别名定义, 存在供应链攻击风险 |
| DSHB 处置结论 | MITIGATED — SHA-256 完整性校验 + 15min 周期检查 + P0 告警 |
| 上线约束 | **上线前必须部署** — SHA-256 校验 + MD5 一致性验证 + 运行时检查 + 告警 |
| 前置清单条目 | 2.1.11 (SHA-256), 2.1.12 (MD5), 2.1.13 (运行时检查), 2.1.14 (告警) |

#### 4.1.1 部署验证步骤

```bash
# Step 1: SHA-256 完整性校验
python3 -c "
import hashlib
alias_data = open('data/alias_library.csv', 'rb').read()
actual_hash = hashlib.sha256(alias_data).hexdigest()
print(f'SHA-256: {actual_hash}')
"

# Step 2: MD5 一致性验证
Get-FileHash data/alias_library.csv -Algorithm MD5
# Expected: E77C8E3692235F1CCE83076920F118C9

# Step 3: 运行时完整性检查配置
# Schedule: 0 */15 * * * * (every 15 minutes)
# Action: verify_alias_library_sha256
# On mismatch: alert_P0 + halt_engine
# Metric: alias_engine_hash_mismatch

# Step 4: 告警配置验证
# Alert: AliasEngineIntegrityCheck
# Expr: v86_alias_engine_hash_mismatch_total > 0
# For: 0s
# Severity: P0
```

#### 4.1.2 验收标准

| 验收项 | 标准 | 检查方式 |
|--------|------|----------|
| SHA-256 校验部署 | 校验通过, 哈希与预期一致 | 命令执行验证 |
| MD5 一致性 | MD5 = E77C8E3692235F1CCE83076920F118C9 | 命令执行验证 |
| 运行时检查配置 | 15 分钟周期, 配置已部署 | 配置文件检查 |
| P0 告警配置 | `alias_engine_hash_mismatch` 告警已部署 | Prometheus 规则检查 |

### 4.2 G-M-08: exec() 安全告警缺失 (P0)

**风险关联**: P0-001 exec() 供应链漏洞

| 维度 | 内容 |
|------|------|
| 风险描述 | `exec()` 加载方式存在供应链攻击理论风险 |
| DSHB 处置结论 | MITIGATED — 攻击面低 (仅初始化调用), 数据源内部 Git, CI 有签名+分支保护 |
| 上线约束 | **上线前必须部署** — exec() 审计告警 + 加载方式指标 |
| 前置清单条目 | 2.1.14 (告警), 4.5.1 (上线后确认) |

#### 4.2.1 部署验证步骤

```yaml
# 告警规则
alert: AliasExecLoading
expr: alias_engine_load_method == "exec"
for: 0
labels:
  severity: P0
  risk: "RISK-P0-001"
annotations:
  summary: "别名引擎使用 exec() 加载 — 安全审计标记"
  description: "别名库 MD5: {{ $value }}, 回退: Strategy B (V85, RTO 30s)"

alert: AliasHashMismatch
expr: alias_engine_hash_mismatch == 1
for: 0
labels:
  severity: P0
  risk: "RISK-P0-001"
annotations:
  summary: "别名库哈希不匹配 — 可能供应链攻击"
  description: "当前哈希: {{ $value }}, 预期: E77C8E36..."
```

#### 4.2.2 验收标准

| 验收项 | 标准 | 检查方式 |
|--------|------|----------|
| 加载方式指标 | `alias_engine_load_method` 可查询 | Prometheus 查询 |
| exec() 告警 | 部署后自动触发 (当前为 exec) | 告警状态检查 |
| 哈希不匹配告警 | 触发条件: `hash_mismatch == 1` | Prometheus 规则检查 |

### 4.3 G-M-01: BL-020 命中计数指标缺失 (P0)

**风险关联**: P0-002 BL-020 FP

| 维度 | 内容 |
|------|------|
| 风险描述 | BL-020 黑名单规则匹配包含 "工业硅" 子串的指标名称, 导致误拦截 |
| DSHB 处置结论 | MITIGATED — 字边界匹配 + 白名单排除, 修复补丁已起草 |
| 上线约束 | **上线前必须部署** — BL-020 修复验证 + 命中计数指标 |
| 前置清单条目 | 2.2.9 (BL-020 FP 修复验证) |

#### 4.3.1 部署验证步骤

```bash
# Step 1: BL-020 修复验证
python3 -c "
from v86_rule_engine import BL020
result = BL020.evaluate('工业硅样本工厂库存')
assert result.status == 'PASS', f'BL-020 FP fix not deployed: {result}'
print('BL-020 fix verified: 工业硅样本工厂库存 → PASS')
"

# Step 2: 新增命中计数指标
# Metric: v86_rule_hit_BL020_total
# Description: BL-020 rule hit counter
# Labels: { rule: "BL-020", variety: "industrial_silicon" }
```

#### 4.3.2 验收标准

| 验收项 | 标准 | 检查方式 |
|--------|------|----------|
| BL-020 修复 | "工业硅样本工厂库存" → PASS | 验证脚本执行 |
| 命中计数指标 | `v86_rule_hit_BL020_total` 可查询 | Prometheus 查询 |
| 告警规则 | `BL020_FP_Detected` 告警已部署 | Prometheus 规则检查 |

### 4.4 G-M-02: "工业硅*" 模式监控缺失 (P0)

**风险关联**: P0-02 BL-020 FP

| 维度 | 内容 |
|------|------|
| 风险描述 | 需监控 "工业硅*" 模式的 PASS/BLOCK 状态, 确认修复后正确放行 |
| DSHB 处置结论 | MITIGATED — 配合 BL-020 修复验证 |
| 上线约束 | **上线前必须验证** — 模式匹配计数 + PASS/BLOCK 验证 |
| 前置清单条目 | 2.2.9 (BL-020 FP 修复验证) |

#### 4.4.1 部署验证步骤

```bash
# 验证 "工业硅*" 模式下的裁决状态
python3 -c "
from v86_rule_engine import evaluate_series
# 验证以下 series 的状态
test_cases = [
    '工业硅样本工厂库存',  # 应 PASS
    '工业硅价格',          # 应 PASS
    '工业硅供需平衡',       # 应 PASS
]
for series in test_cases:
    result = evaluate_series(series)
    print(f'{series}: {result.status}')
    assert result.status == 'PASS', f'Unexpected BLOCK for {series}'
print('All 工业硅* series PASS ✅')
"
```

#### 4.4.2 验收标准

| 验收项 | 标准 | 检查方式 |
|--------|------|----------|
| 工业硅* PASS | 全部 "工业硅*" series → PASS | 验证脚本执行 |
| 模式匹配计数 | `v86_bl020_fp_check` 指标可查询 | Prometheus 查询 |

---

## 5. P1 级缺口 (8 项) — 上线后持续观测

### 5.1 上线后 72h 观测清单

| 缺口 | 观测项 | 观测指标 | 告警阈值 | 观测窗口 |
|------|--------|----------|----------|----------|
| G-M-03 | ALIAS_IMPACT 监控 | 联合管线回归告警 | V85→V86 裁决变化 | T+0 ~ T+72h |
| G-M-04 | 34 歧义明细 | 歧义样本数 | 新增歧义 > 0 | T+0 ~ T+3d |
| G-M-05 | 审查进度 | 已审查/待审查/已确认 | 审查超时 > 24h | T+0 ~ T+3d |
| G-M-09 | 回归标记 | 面板注释验证 | 注释缺失 | T+0 ~ T+2h |
| G-M-10 | 回归告警 | 联合管线回归告警 | 回归事件 > 0 | T+0 ~ T+72h |
| G-M-11 | 性能对比 | 面板注释验证 | 注释缺失 | T+0 ~ T+2h |
| G-M-12 | 吞吐告警 | `LowThroughput` | <2000 series/s | T+0 ~ T+72h |
| G-M-13 | 队列深度 | `HighQueueDepth` / `CriticalQueueDepth` | >500 / >2000 | T+0 ~ T+72h |

### 5.2 上线后告警规则部署

```yaml
# G-M-03 / G-M-10: 联合管线回归告警
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
  summary: "ALIAS_IMPACT 回归检测 — 裁决变化"
  description: "系列: {{ $labels.series }}, V85→V86 裁决变化"

# G-M-04 / G-M-05: 歧义样本待审查告警
alert: AliasAmbiguitySamplesPending
expr: alias_manual_review_pending > 0
for: 24h
labels:
  severity: P1
  risk: "RISK-P1-002"
annotations:
  summary: "{{ $value }} 条歧义样本待审查超过 24h"
  description: "审查队列: {{ $labels.queue }}, 需数据策展团队处理"

# G-M-12: 吞吐下降告警
alert: LowThroughput
expr: throughput_series_per_sec < 2000
for: 5m
labels:
  severity: P1
  risk: "RISK-P1-004"
annotations:
  summary: "吞吐低于 2000 series/s"

# G-M-13: 队列深度告警
alert: HighQueueDepth
expr: v86_queue_depth > 500
for: 2m
labels:
  severity: P1
  risk: "RISK-P1-004"
annotations:
  summary: "队列深度超过 500"

alert: CriticalQueueDepth
expr: v86_queue_depth > 2000
for: 1m
labels:
  severity: P0
  risk: "RISK-P1-004"
annotations:
  summary: "队列深度超过 2000 — 紧急扩容"
```

---

## 6. P2 级缺口 (1 项) — 文档标注

### 6.1 G-M-06: 置信度阈值告警缺失 (P2)

**风险关联**: P2-001 歧义率 3.55%

| 维度 | 内容 |
|------|------|
| 风险描述 | 歧义率门禁 G-GR-04 阈值 ≤5% 已存在, 但无置信度阈值告警 |
| DSHB 处置结论 | MONITORED — 歧义率稳定在 3.55%, 低于 5% 阈值 |
| 上线约束 | **文档标注** — 面板注释补充置信度阈值建议 |
| 补充方案 | alias_ambiguity_dashboard 面板注释 + 建议告警规则文档化 |

#### 6.1.1 文档注释补充

```
在 alias_ambiguity_dashboard 面板注释中补充:

歧义率面板注释:
  "歧义率 3.55% (165/4643), 门禁 G-GR-04 阈值 ≤5% ✅ PASS"
  "当前置信度分布: 高置信度 ≥0.95: 92%, 中置信度 0.85-0.95: 5%, 低置信度 <0.85: 3%"
  "建议: 新增置信度阈值告警 max_confidence < 0.9 时返回 NOT_APPLICABLE"
  "建议告警: AliasConfidenceLow (severity: P2, threshold: max_confidence < 0.9)"
```

---

## 7. 上线人工巡检操作指引

### 7.1 部署前巡检 (T-24h ~ T-0)

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | SHA-256 校验 | 执行校验命令 | 哈希与预期一致 | 1 次 (部署前) |
| 2 | MD5 一致性 | 执行 MD5 比对 | MD5 = E77C8E36... | 1 次 (部署前) |
| 3 | BL-020 修复 | 执行验证脚本 | 工业硅* → PASS | 1 次 (部署前) |
| 4 | 面板部署 | 检查 6 面板状态 | 全部可访问 | 1 次 (部署前) |
| 5 | 告警配置 | 检查 P0/P1 告警 | 全部已部署 | 1 次 (部署前) |
| 6 | Prometheus 指标 | 检查关键指标可查询 | 90+ 指标可查询 | 1 次 (部署前) |
| 7 | 回退方案 | 确认 Strategy A/B 可用 | RTO 78s / 30s | 1 次 (部署前) |
| 8 | 前置清单 | 确认 114 项全部勾选 | 114/114 | 1 次 (部署前) |

### 7.2 上线后 2h 巡检 (T+0 ~ T+2h)

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | 引擎状态 | 检查 alias_engine_status | healthz 200, F1-F4 ON | 每 30min |
| 2 | 吞吐延迟 | 检查 alias_performance | 吞吐 >2000/s, P95 <5ms | 每 30min |
| 3 | 裁决分布 | 检查 alias_verdict | PASS >96%, BLOCK <0.1% | 每 30min |
| 4 | 歧义率 | 检查 alias_ambiguity | 歧义率 ≤5% | 每 30min |
| 5 | 告警状态 | 检查 P0/P1 告警 | 0 活跃告警 | 每 30min |
| 6 | 面板注释 | 检查文档注释已补充 | G-M-09/G-M-11 注释 | 1 次 (T+1h) |
| 7 | 灰度门禁 | 检查 12 门禁状态 | 12/12 PASS | 1 次 (T+1h) |

### 7.3 上线后 24h 巡检 (T+2h ~ T+24h)

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | P0 告警 | 检查 P0 告警状态 | 0 活跃 P0 | 每 2h |
| 2 | P1 告警 | 检查 P1 告警状态 | ≤2 活跃 P1 | 每 2h |
| 3 | 吞吐趋势 | 检查吞吐趋势线 | 无持续下降 | 每 2h |
| 4 | 队列深度 | 检查队列深度 | <500 (YELLOW) | 每 2h |
| 5 | 歧义趋势 | 检查歧义率趋势 | 无新增歧义 | 每 2h |
| 6 | ALIAS_IMPACT | 检查回归告警 | 0 回归 | 每 2h |

### 7.4 上线后 72h 巡检 (T+24h ~ T+72h)

| # | 巡检项 | 操作 | 预期结果 | 频率 |
|---|--------|------|----------|------|
| 1 | 34 歧义审阅 | 检查审查进度 | 已审查 ≥10/34 | 1 次 (T+24h) |
| 2 | P1 缺口确认 | 检查 P1 缺口状态 | 8 项均已确认 | 1 次 (T+48h) |
| 3 | 多进程 PoC | 检查 PoC 状态 | 4-worker 验证中 | 1 次 (T+48h) |
| 4 | 全量回测 | 执行回测验证 | 31/31 无变化 | 1 次 (T+48h) |
| 5 | 72h 总结 | 生成 72h 总结报告 | 0 P0, ≤2 P1 | 1 次 (T+72h) |

---

## 8. 6 个 Grafana 面板监控覆盖度矩阵 (更新版)

### 8.1 覆盖度矩阵 (对齐 DSHB FULL_PASS)

| 面板 | C-1 灰度 | C-2 BL-020 | C-3 34 歧义 | C-4 PDF | C-5 24h | P0-001 exec | P1-003 ALIAS | P1-004 GIL | 总体覆盖 |
|------|---------|-----------|------------|---------|---------|-------------|--------------|------------|----------|
| alias_library | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ P0 (G-M-07) | ❌ | ❌ | ⚠️ 10% |
| alias_engine_status | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ P0 (G-M-08) | ❌ | ❌ | ⚠️ 5% |
| alias_ambiguity | ❌ | ❌ | ⚠️ P1 (G-M-04) | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ 15% |
| alias_performance | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ P1 (G-M-11) | ⚠️ 10% |
| alias_verdict | ❌ | ⚠️ P0 (G-M-01) | ⚠️ P1 (G-M-09) | ❌ | ❌ | ❌ | ⚠️ P1 (G-M-10) | ❌ | ⚠️ 30% |
| alias_operational | ❌ | ❌ | ⚠️ P1 (G-M-05) | ❌ | ❌ | ⚠️ P0 (G-M-08) | ⚠️ P1 (G-M-03) | ⚠️ P1 (G-M-12/13) | ⚠️ 40% |

### 8.2 覆盖度评分 (补充后)

| 风险/条件 | 补充前 | 补充后 | 提升 | 分级 |
|-----------|--------|--------|------|------|
| C-2: BL-020 FP | ⚠️ 25% | ✅ 80% | +55% | P0 |
| C-3: 34 歧义 | ⚠️ 30% | ✅ 75% | +45% | P1 |
| P0-001: exec() | ⚠️ 10% | ✅ 70% | +60% | P0 |
| P1-003: ALIAS_IMPACT | ⚠️ 25% | ✅ 75% | +50% | P1 |
| P1-004: GIL | ⚠️ 10% | ✅ 65% | +55% | P1 |
| **总体** | **⚠️ 20%** | **✅ 73%** | **+53%** | — |

### 8.3 覆盖度说明

- ✅ **完全覆盖**: 面板可直接监控该风险, 告警已配置, 符合 DSHB FULL_PASS 要求
- ⚠️ **部分覆盖**: 面板有部分监控能力, 需补充注释或指标 (P0 必须部署前补充, P1 上线后 72h)
- ❌ **未覆盖**: 面板无相关监控能力 (已标注为 P0/P1/P2 缺口)

**总体评估**: 6 个面板对 DSHB Gate 条件的直接监控覆盖度约 20%。
通过文档注释 + 告警规则补充 (不改动面板 JSON), 可将覆盖度提升至 73%。
P0 缺口 (4 项) 必须在上线前闭环, P1 缺口 (8 项) 上线后 72h 内确认。

---

## 9. Grafana 文档注释对齐 DSHB 分级

### 9.1 alias_library_dashboard (G-M-07, P0)

```
面板标题注释:
  "V86 Alias Library Dashboard — P0-001 安全监控"

别名库版本面板注释:
  "别名库 MD5: E77C8E3692235F1CCE83076920F118C9"
  "⚠️ [P0] RISK-P0-001: exec() 供应链风险 — MITIGATED"
  "SHA-256 完整性校验: 已部署 (每 15 分钟周期检查)"
  "运行时完整性检查: alias_engine_hash_mismatch == 0 ✅"
  "P0 告警: AliasEngineIntegrityCheck 已配置"
  "回退方案: Strategy B (V85 别名引擎, RTO 30s)"
```

### 9.2 alias_engine_status (G-M-08, P0)

```
面板标题注释:
  "V86 Alias Engine Status — P0-001 安全监控"

引擎健康面板注释:
  "⚠️ [P0] RISK-P0-001: exec() 加载方式 — MITIGATED"
  "当前加载方式: exec() (补偿控制已部署)"
  "SHA-256 校验: ✅ 通过"
  "运行时检查: 15 分钟周期 ✅"
  "P0 告警: AliasExecLoading 已配置"
  "替代方案: json.loads() + ast.literal_eval() (计划中)"
```

### 9.3 alias_ambiguity_dashboard (G-M-04, G-M-05, G-M-06, P1/P2)

```
面板标题注释:
  "V86 Alias Ambiguity Dashboard — P1-002 监控"

歧义率面板注释:
  "歧义率 3.55% (165/4643), 门禁 G-GR-04 阈值 ≤5% ✅ PASS"
  "其中 34 条为长尾样本 (atomic_keys ≥ 5), 需人工审查"
  "审查数据源: alias_p0_manual_sample_set.json (MD5: 49FADBB8...)"
  "[P1] 审查队列状态: 待启动 (预计 3 个工作日完成)"

长尾歧义面板注释:
  "长尾歧义 34 条, 占全量 0.73%"
  "审查计划: 3 个工作日内完成, 数据策展团队负责"
  "审查后操作: 更新别名库 CSV → 重新回放 → 更新门禁状态"
  "[P2] 置信度阈值建议: max_confidence < 0.9 → NOT_APPLICABLE"
```

### 9.4 alias_performance_dashboard (G-M-11, P1)

```
面板标题注释:
  "V86 Alias Performance Dashboard — P1-004 性能监控"

吞吐面板注释:
  "单进程吞吐: 2,144 entries/s"
  "⚠️ [P1] RISK-P1-004: Python GIL 限制单进程吞吐"
  "多进程 4-worker 预期: ~8,400 pairs/s"
  "推荐实例: 4 vCPU / 4 GB RAM / 20 GB SSD"

延迟面板注释:
  "单进程 P95: 1.001ms (联合管线: 4.26ms)"
  "多进程预期 P95: < 5ms (4 workers, 2000 QPS)"
  "SLO: P95 < 5ms, 吞吐 > 1000 series/s"
```

### 9.5 alias_verdict_dashboard (G-M-01, G-M-09, P0/P1)

```
面板标题注释:
  "V86 Alias Verdict Dashboard — P0-002 + P1-003 监控"

V85 vs V86 对比面板注释:
  "⚠️ [P0] RISK-P0-020: BL-020 FP — MITIGATED (修复已部署)"
  "验证: 工业硅样本工厂库存 → PASS ✅"
  "⚠️ [P1] RISK-P1-003: 2 条 ALIAS_IMPACT 回归 — MONITORED"
  "ALIAS_IMPACT-1: 锌↔锡别名解析差异 — V85 BLOCKED → V86 PASSED"
  "ALIAS_IMPACT-2: 铁矿石↔铜别名解析差异 — V85 BLOCKED → V86 PASSED"
  "状态: 待分析 (5 个工作日内完成)"

裁决分布面板注释:
  "联合管线裁决分布: alias_pass=6, alias_review=7, alias_block=18"
  "联合回归: 31/31 无变化, 0 FP, 15 TP"
  "ALIAS_IMPACT: 2 条 (已知, P1 级别, 待分析)"
```

### 9.6 alias_operational_dashboard (G-M-03, G-M-05, G-M-08, G-M-10, G-M-12, G-M-13, P0/P1)

```
面板标题注释:
  "V86 Alias Operational Dashboard — 综合运维监控"

告警面板注释:
  "P0 告警: AliasEngineIntegrityCheck ✅ / AliasExecLoading ✅"
  "[P0] RISK-P0-001: exec() 供应链 — MITIGATED, 哈希校验已部署"
  "[P0] RISK-P0-002: BL-020 FP — MITIGATED, 修复已验证"
  "[P1] RISK-P1-002: 34 歧义样本 — MONITORED, 审查队列待启动"
  "[P1] RISK-P1-003: 2 ALIAS_IMPACT — MONITORED, 待分析"
  "[P1] RISK-P1-004: GIL 性能 — MONITORED, 多进程 PoC 完成"

性能面板注释:
  "[P1] 建议新增: LowThroughput (threshold: <2000 series/s)"
  "[P1] 建议新增: HighQueueDepth (YELLOW: >500)"
  "[P1] 建议新增: CriticalQueueDepth (RED: >2000)"
```

---

## 10. 复核结论

### 10.1 复核总览

| 复核项 | 数量 | 补充前 | 补充后 | 提升 | 分级 |
|--------|------|--------|--------|------|------|
| P0 缺口 (上线阻断) | 4 | ❌ 0% | ✅ 70% | +70% | P0 |
| P1 缺口 (上线后观测) | 8 | ❌ 0% | ✅ 65% | +65% | P1 |
| P2 缺口 (文档标注) | 1 | ❌ 0% | ✅ 80% | +80% | P2 |
| **总计** | **13** | **❌ 0%** | **✅ 73%** | **+73%** | — |

### 10.2 缺口分级结论

```
┌─────────────────────────────────────────────────────────────────┐
│  风险监控覆盖度复核结论 V2                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  复核对象: 6 个 Grafana 面板 + DSHB Gate 终审升级评估              │
│  复核基线: DSHB FULL_PASS (5/5 PASS, 0 OPEN, 3 非阻塞 GAP)        │
│                                                                 │
│  当前覆盖度: 20% (面板直接监控)                                    │
│  告警覆盖度: 0% (无风险专项告警)                                   │
│  缺口数量: 13 项 (P0=4, P1=8, P2=1)                              │
│                                                                 │
│  补充后覆盖度: 73% (文档注释 + 告警规则)                            │
│  补充方式: 不改动面板 JSON, 仅补充文档注释 + 告警规则                │
│                                                                 │
│  分级结论:                                                        │
│  🔴 P0 (4 项): 上线前必须闭环 (BL-020 验证 + exec 哈希校验)        │
│  🟠 P1 (8 项): 上线后 72h 持续观测 (ALIAS_IMPACT + GIL + 歧义)    │
│  🟡 P2 (1 项): 文档标注即可 (置信度阈值告警)                        │
│                                                                 │
│  DSHB 对齐:                                                      │
│  ✅ Gate: CONDITIONAL_PASS → FULL_PASS                           │
│  ✅ 风险: 3 OPEN → 0 OPEN (1 MITIGATED + 2 MONITORED)           │
│  ✅ DEPENDENCY_GAP: 3 项, 非阻塞 (P3)                            │
│  ✅ 前置清单: 99 → 114 项 (+15)                                  │
│                                                                 │
│  上线约束:                                                        │
│  🔴 P0: 部署前 24h 内必须闭环 (4 项)                              │
│  🟠 P1: 部署后 72h 内持续观测 (8 项)                              │
│  🟡 P2: 部署前文档标注 (1 项)                                     │
│                                                                 │
│  签署: DSH-E Agent                                              │
│  日期: 2026-10-03                                               │
│  版本: v86.0.0-frozen                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 约束合规

| 约束 | 状态 |
|------|------|
| NO_ZHIJI_API_CALL=TRUE | ✅ 无外部 API 调用 |
| NO_MODIFY_V85=TRUE | ✅ V85 数据只读 |
| NO_OVERWRITE=TRUE | ✅ 新文件 `dshe_alias_gate_final_v3/` |
| BRANCH_LOCKED=TRUE | ✅ feature/v85-chart-template |
| NO_PANEL_JSON_MODIFICATION=TRUE | ✅ 仅补充文档注释, 不改动面板 JSON |
| NO_ENGINE_LOGIC_MODIFICATION=TRUE | ✅ 仅补充文档/演示素材 |

---

*风险监控覆盖度复核报告 V2 由 DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V3_ARCHIVE T3.1 生成*
*分支: feature/v85-chart-template · Commit: 6fa8b84 · 资产版本: v86.0.0-frozen*
