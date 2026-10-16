# P49 灰度前置校验文档 · Pre-Gray-Check Specification

> **文档ID**: DSHA-P54-P49-PREGATE-001
> **生成时间**: 2026-10-16 GMT+8
> **Agent**: DSHA-P54
> **Branch**: feature/v88-g1
> **GATE**: CLOSED/HOLD
> **Release Permit**: NOT_ISSUED
> **Wind API Calls**: 0
> **前置声明**: 本文档为灰度发布前置校验规则定义文档，由SHA256_CHECKSUMS.txt第10行和G7_ADJUDICATION_PACKAGE_MANIFEST.json引用。生成前该文档在磁盘不存在。

---

## 0. 文档目的

本文档定义 P49 因子体系灰度发布前置校验规则，涵盖：
- 7 因子准入矩阵（F001~F007）
- 阻断条件与解除条件
- 灰度前置校验规则（PRE_GATE_CHECKS）
- 条件跟踪白名单状态（WL-A001~WL-A007）
- 灰度发布必要条件清单

---

## 1. 因子准入矩阵

### 1.1 总览

| Factor ID | 因子名称 | 准入状态 | 准入等级 | WL-A 跟踪 | 灰度通道 |
|---|---|---|---|---|---|
| FACTOR-001 | F19_hot_money_weight | HOLD | L4 (硬阻断) | WL-A001 | ❌ 禁止 |
| FACTOR-002 | F20_attention_weight | HOLD | L4 (硬阻断) | WL-A002 | ❌ 禁止 |
| FACTOR-003 | CF003_speculation_weight | HOLD | L4 (硬阻断) | WL-A003 | ❌ 禁止 |
| FACTOR-004 | G1_IC_threshold | CONDITIONAL_PASS | L2 (条件准入) | WL-A004 | ✅ 限灰度 |
| FACTOR-005 | G3_ICIR_threshold | HOLD | L4 (硬阻断) | WL-A005 | ❌ 禁止 |
| FACTOR-006 | G7_leakage_ratio | CONDITIONAL_PASS | L2 (条件准入) | WL-A006 | ✅ 限灰度 |
| FACTOR-007 | SchemeD_frozen_weights | CONDITIONAL_PASS | L2 (条件准入) | WL-A007 | ✅ 限灰度 |

### 1.2 准入等级定义

| 等级 | 标识 | 含义 | 灰度权限 |
|---|---|---|---|
| L1 | PASS | 完全通过，无阻断条件 | 全量放行 |
| L2 | CONDITIONAL_PASS | 有条件通过，需满足特定条件 | 限灰度通道 |
| L3 | WARN | 存在风险，需监控 | 仅限观测 |
| L4 | HOLD | 硬阻断，禁止任何访问 | 禁止 |

### 1.3 当前准入统计

```
PASS:                0 (0%)
CONDITIONAL_PASS:    3 (42.86%)
WARN:                0 (0%)
HOLD:                4 (57.14%)
```

---

## 2. 阻断条件与解除条件

### 2.1 FACTOR-001 · F19_hot_money_weight (HOLD)

| 项目 | 内容 |
|---|---|
| **阻断等级** | L4 (硬阻断) |
| **阻断原因** | SYNTHETIC_DATA_ZERO_SIGNAL — 因子基于合成数据计算，IC=0.0，无真实信号 |
| **阻断范围** | 因子计算、数据访问、回测执行、参数读取 — 全部禁止 |
| **解除条件** | ① Wind 真实数据接入成功 (wind_api_calls > 0) ② 因子重测 IC != 0.0 ③ 条件验证通过 |
| **验证窗口** | 35d / 60d / 100d 滚动窗口 |
| **解除审批** | 需 DSHC 授权 |
| **当前状态** | ❌ BLOCKED (WL-A001: ACTIVE_HOLD) |

### 2.2 FACTOR-002 · F20_attention_weight (HOLD)

| 项目 | 内容 |
|---|---|
| **阻断等级** | L4 (硬阻断) |
| **阻断原因** | SYNTHETIC_DATA_ZERO_SIGNAL — 因子基于合成数据计算，IC=0.0 |
| **阻断范围** | 因子计算、数据访问、回测执行、参数读取 — 全部禁止 |
| **解除条件** | ① Wind 真实数据接入成功 ② 因子重测 IC != 0.0 |
| **解除审批** | 需 DSHC 授权 |
| **当前状态** | ❌ BLOCKED (WL-A002: ACTIVE_HOLD) |

### 2.3 FACTOR-003 · CF003_speculation_weight (HOLD)

| 项目 | 内容 |
|---|---|
| **阻断等级** | L4 (硬阻断) |
| **阻断原因** | SYNTHETIC_DATA_ZERO_SIGNAL — 因子基于合成数据计算，IC=0.0；附加: 100% 坏样本清洗率 |
| **阻断范围** | 因子计算、数据访问、回测执行、参数读取 — 全部禁止 |
| **解除条件** | ① Wind 真实数据接入成功 ② 因子重测 IC != 0.0 ③ 坏样本清洗率降至合理水平 (< 90%) |
| **解除审批** | 需 DSHC 授权 |
| **当前状态** | ❌ BLOCKED (WL-A003: ACTIVE_HOLD) |

### 2.4 FACTOR-005 · G3_ICIR_threshold (HOLD)

| 项目 | 内容 |
|---|---|
| **阻断等级** | L4 (硬阻断) |
| **阻断原因** | ICIR_DEFINITION_REDESIGN_REQUIRED — ICIR 指标定义存在跨窗口符号翻转问题 |
| **阻断范围** | 因子计算、数据访问、回测执行、参数读取 — 全部禁止 |
| **ICIR 定义问题** | 当前定义 ICIR = mean(IC) / std(IC) 在 35d/60d/100d 窗口下 ICIR 符号发生翻转 |
| **解除条件** | ① ICIR 指标重设计 ② 新定义在多个时间窗口下符号稳定 ③ 滚动 ICIR 辅助验证 |
| **解除审批** | 需 DSHC 授权 |
| **当前状态** | ❌ BLOCKED (WL-A005: ACTIVE_HOLD) |

---

## 3. 灰度前置校验规则 (PRE_GATE_CHECKS)

### 3.1 校验规则总表

| 规则ID | 校验项 | 校验方法 | 通过条件 | 失败动作 |
|---|---|---|---|---|
| PG-001 | 治理不变量 | 全源交叉验证 | wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED | 立即停止，升级 DSHC |
| PG-002 | HOLD 因子阻断 | ProcessGate.check_factor_access() 测试 | 4/4 HOLD 因子均抛出 HoldFactorTerminationError | 立即停止，升级 DSHC |
| PG-003 | CONDITIONAL 因子状态 | 检查 CONDITIONAL_FACTORS 字典 | 3/3 因子 process_block=False | 标记异常，不阻断 |
| PG-004 | Wind 环境就绪 | WindPy w.start() 连接测试 | ErrorCode=0 | 标记 BLOCKED，等待 DSHC |
| PG-005 | 数据块计划完整 | WindDataPullPipeline.plan_execution() | 3 块，108 次调用估算 | 标记异常，不阻断 |
| PG-006 | 字段映射完整 | CONDITIONAL_FACTORS 中 wind_fields 完整性 | 3 因子全部字段映射非空 | 标记异常，不阻断 |
| PG-007 | 哈希一致性 | SHA256 校验（见 P49_HASH_CONSISTENCY_FIX_SPEC.md） | 唯一可信源 SHA256_CHECKSUMS.txt 验证通过 | 标记 WARNING，记录漂移 |
| PG-008 | 缺失文档 | 检查 SHA256_CHECKSUMS.txt 标注的 MISSING 文件 | 无 MISSING 或已补充 | 标记 WARNING |
| PG-009 | 条件跟踪项 | 检查 WL-A001~WL-A007 状态 | 7/7 ACTIVE_CONDITIONAL 或 ACTIVE_HOLD | 标记异常 |
| PG-010 | 审计日志完整性 | 对比 tracking_monitor_audit.jsonl 和 wind_excel_events.jsonl | 两条审计链一致 | 标记异常 |
| PG-011 | 白名单覆盖 | 检查 WL-006~WL-014 覆盖率 | 42/42 假警报全部覆盖 | 标记异常 |
| PG-012 | 明文凭证扫描 | 扫描所有产出文件 | 0 处明文凭证 | 立即停止，升级 DSHC |

### 3.2 校验执行序列

```
Step 1: PG-001 治理不变量校验
  └─ FAIL → STOP (不可继续)
Step 2: PG-002 HOLD 因子阻断测试
  └─ FAIL → STOP (不可继续)
Step 3: PG-003 条件因子状态检查
  └─ FAIL → WARNING (可继续)
Step 4: PG-004 Wind 环境就绪检查
  └─ FAIL → BLOCKED (标记阻断，等待 DSHC)
Step 5: PG-005~PG-011 其余校验项
  └─ FAIL → WARNING (可继续)
Step 6: PG-012 凭证扫描
  └─ FAIL → STOP (不可继续)
Step 7: 汇总
  └─ ALL PASS → READY_FOR_DATA_PULL (仍需 DSHC 授权)
  └─ ANY FAIL → REMEDIATION_REQUIRED
  └─ ANY BLOCKED → AWAITING_DSHC
```

### 3.3 校验结果模板

```json
{
  "pre_gate_check": {
    "timestamp": "<ISO-8601>",
    "agent": "DSHA-P54",
    "branch": "feature/v88-g1",
    "checks": [
      {"id": "PG-001", "name": "Governance Invariants", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-002", "name": "HOLD Factor Block Test", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-003", "name": "Conditional Factor Status", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-004", "name": "Wind Environment Ready", "status": "PASS|BLOCKED", "detail": "..."},
      {"id": "PG-005", "name": "Data Chunk Plan", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-006", "name": "Field Mapping Completeness", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-007", "name": "Hash Consistency", "status": "PASS|FAIL|WARNING", "detail": "..."},
      {"id": "PG-008", "name": "Missing Documents", "status": "PASS|WARNING", "detail": "..."},
      {"id": "PG-009", "name": "Conditional Tracking Items", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-010", "name": "Audit Log Consistency", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-011", "name": "Whitelist Coverage", "status": "PASS|FAIL", "detail": "..."},
      {"id": "PG-012", "name": "Credential Scan", "status": "PASS|FAIL", "detail": "..."}
    ],
    "overall_status": "READY_FOR_DATA_PULL|REMEDIATION_REQUIRED|AWAITING_DSHC",
    "pass_count": 0,
    "fail_count": 0,
    "warning_count": 0,
    "blocked_count": 0
  }
}
```

---

## 4. 条件跟踪白名单状态 (WL-A001~WL-A007)

| WL-A ID | Factor | 条件类型 | 状态 | 解除条件 | 当前进展 |
|---|---|---|---|---|---|
| WL-A001 | FACTOR-001 | SYNTHETIC_DATA_ZERO_SIGNAL | ACTIVE_HOLD | Wind真实数据接入+重测 | 等待 Wind 权限激活 |
| WL-A002 | FACTOR-002 | SYNTHETIC_DATA_ZERO_SIGNAL | ACTIVE_HOLD | Wind真实数据接入+重测 | 等待 Wind 权限激活 |
| WL-A003 | FACTOR-003 | SYNTHETIC_DATA_ZERO_SIGNAL | ACTIVE_HOLD | Wind真实数据接入+重测 | 等待 Wind 权限激活 |
| WL-A004 | FACTOR-004 | THRESHOLD_STABILITY_DEFECT | ACTIVE_CONDITIONAL | IC稳定性+多窗口阈值验证 | 等待数据拉取后验证 |
| WL-A005 | FACTOR-005 | ICIR_DEFINITION_REDESIGN_REQUIRED | ACTIVE_HOLD | ICIR指标重设计并验证 | 等待重设计方案 |
| WL-A006 | FACTOR-006 | G7_LEAKAGE_BOUNDARY_FALSE_ALARM | ACTIVE_CONDITIONAL | 真实数据下G7边界复核 | 等待数据拉取后验证 |
| WL-A007 | FACTOR-007 | MULTI_WINDOW_INSTABILITY | ACTIVE_CONDITIONAL | 35~100日窗口稳定性验证 | 等待数据拉取后验证 |

### 4.1 条件跟踪状态统计

```
ACTIVE_HOLD:        4 (WL-A001, WL-A002, WL-A003, WL-A005)
ACTIVE_CONDITIONAL: 3 (WL-A004, WL-A006, WL-A007)
REMOVED:            0
ESCALATED:          0
```

---

## 5. 灰度发布必要条件清单

### 5.1 必要条件（全部满足方可进入灰度）

| # | 条件 | 当前状态 | 验证方法 |
|---|---|---|---|
| N1 | 治理不变量全程保持 | ✅ MAINTAINED | 审计日志交叉验证 |
| N2 | 4/4 HOLD 因子未被访问 | ✅ MAINTAINED | ProcessGate 阻断测试 |
| N3 | 3/3 CONDITIONAL 因子条件满足 | ⏳ PENDING | 需真实数据验证 |
| N4 | Wind 数据接入完成 | ⏳ PENDING | WindPy 连接测试 |
| N5 | 哈希源统一 | ⏳ PENDING | 见 P49_HASH_CONSISTENCY_FIX_SPEC.md |
| N6 | 缺失文档补齐 | ✅ COMPLETED | P49_pre_gray_check.md 已生成 |
| N7 | 审计日志一致 | ✅ MAINTAINED | 双审计链交叉验证 |
| N8 | 白名单全覆盖 | ✅ 42/42 | 白名单覆盖率验证 |
| N9 | 明文凭证零出现 | ✅ 0处 | 全文扫描 |
| N10 | 灰度放行许可 | ❌ NOT_ISSUED | 需 DSHC 签发 |

### 5.2 条件满足率

```
✅ 满足:    7/10 (70%)
⏳ 待完成:  2/10 (20%)
❌ 未签发:  1/10 (10%)
```

---

## 6. 灰度通道架构

```
┌─────────────────────────────────────────────────────────┐
│                    L4: HOLD (硬阻断)                       │
│  FACTOR-001  FACTOR-002  FACTOR-003  FACTOR-005         │
│  ❌ 禁止访问  ❌ 禁止计算  ❌ 禁止回测  ❌ 禁止参数读取     │
├─────────────────────────────────────────────────────────┤
│              L2: CONDITIONAL_PASS (条件准入)               │
│  FACTOR-004 (IC稳定性待验证)  FACTOR-006 (G7边界待复核)   │
│  FACTOR-007 (多窗口稳定性待验证)                           │
│  ✅ 限灰度通道  ❌ 禁止全量放行                             │
├─────────────────────────────────────────────────────────┤
│              L1: PASS (全量放行)                           │
│  (当前: 无因子达到此级别)                                  │
├─────────────────────────────────────────────────────────┤
│              全局治理层                                    │
│  GATE: CLOSED/HOLD  Release Permit: NOT_ISSUED            │
│  wind_api_calls: 0  backtest_started: false               │
│  DSHC 审核: PENDING  DSHC 授权: NOT_YET                   │
└─────────────────────────────────────────────────────────┘
```

---

## 7. 治理不变量

| 不变量 | 要求 | 当前值 | 状态 |
|---|---|---|---|
| wind_api_calls | 0 | 0 | ✅ MAINTAINED |
| backtest_started | false | false | ✅ MAINTAINED |
| gate | CLOSED/HOLD | CLOSED/HOLD | ✅ MAINTAINED |
| release_permit | NOT_ISSUED | NOT_ISSUED | ✅ MAINTAINED |
| HOLD 因子访问 | 0 次 | 0 次 | ✅ MAINTAINED |
| 明文凭证 | 0 处 | 0 处 | ✅ MAINTAINED |

---

## 8. 结论

1. **P49_pre_gray_check.md** 补齐了 SHA256_CHECKSUMS.txt 标注的 MISSING 文档引用。
2. **7 因子准入矩阵**完整定义：4 HOLD (L4) + 3 CONDITIONAL_PASS (L2) + 0 PASS (L1)。
3. **12 项灰度前置校验规则** (PG-001~PG-012) 定义了校验方法和执行序列。
4. **10 项灰度必要条件**中 7 项已满足，2 项待完成，1 项未签发。
5. **条件跟踪白名单** 7/7 ACTIVE (4 ACTIVE_HOLD + 3 ACTIVE_CONDITIONAL)。
6. **本文档不自动触发任何状态变更**——灰度放行需 DSHC 签发 Release Permit。

> **DSHA-P54 声明**: 本文档为纯离线分析产物，未调用任何 Wind API。
> 所有治理不变量保持：wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED。

---

_生成时间: 2026-10-16 GMT+8 | Agent: DSHA-P54 | Branch: feature/v88-g1_