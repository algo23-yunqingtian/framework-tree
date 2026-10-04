# DSHB V86-RC2 Gate审计集成验证报告

> **工单**: DSHB_V86_RC2_GATE_AUDIT_INTEGRATION_T3.2
> **分支**: `feature/v85-chart-template` (BRANCH_LOCKED=TRUE)
> **执行日期**: 2026-10-16
> **脚本版本**: gate_pre_check_auto_v2.py (V2)
> **审计器**: evidence_auditor.py (V1.0.0)
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 1. 集成架构

### 1.1 集成方式

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Gate Pre-Check V2 Architecture                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐    │
│  │ G01~G05      │     │  G06A (V2 NEW)   │     │ G07~G10      │    │
│  │ 基础检查     │────▶│  HERMES审计器     │────▶│ 基础检查     │    │
│  │              │     │  evidence_auditor │     │              │    │
│  └──────────────┘     └────────┬─────────┘     └──────────────┘    │
│                                │                                     │
│                         ┌──────▼──────┐                              │
│                         │ PASS/FAIL   │                              │
│                         │ CONDITIONAL │                              │
│                         └──────┬──────┘                              │
│                                │                                     │
│                    ┌───────────┼───────────┐                         │
│                    ▼           ▼           ▼                         │
│              ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│              │   PASS   │ │  WARN    │ │   FAIL   │                 │
│              │ 放行Gate  │ │ 条件放行  │ │ 阻断Gate │                 │
│              └──────────┘ └──────────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 集成参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--audit-validate` | 启用审计器联动 | 否 |
| `--audit-file <path>` | 指定审计证据包JSON | 自动构建L1证据包 |
| `--strict` | 严格模式 (FAIL即阻断) | 否 |

### 1.3 判定联动逻辑

| 审计器结论 | Gate G06A状态 | Gate综合影响 |
|------------|---------------|-------------|
| PASS | ✅ PASS | 不阻断 |
| CONDITIONAL_PASS | ⚠️ WARN | 不阻断, 但标记告警 |
| FAIL | ❌ FAIL | **直接阻断Gate → NOT_READY** |
| SKIP | ⏭️ SKIP | 不启用审计联动 |

---

## 2. 集成验证测试结果

### 2.1 测试场景总览

| # | 场景 | 审计输入 | 预期审计结论 | 预期Gate影响 | 实测结果 |
|---|------|----------|-------------|-------------|----------|
| 1 | 正常场景 (全部可取数) | 模拟全量取数成功 | PASS | Gate READY | ✅ 通过 |
| 2 | DEP全阻塞场景 | 全部data_fetchable=FALSE | FAIL | Gate NOT_READY | ✅ 通过 |
| 3 | 旧口径造假场景 | bridge_rate=1.0, real=0.0 | FAIL | Gate NOT_READY | ✅ 通过 |
| 4 | 部分恢复场景 | 50%取数成功 | FAIL (低于阈值) | Gate NOT_READY | ✅ 通过 |
| 5 | 审计器不可用场景 | auditor_path不存在 | SKIP | 不阻断 | ✅ 通过 |

### 2.2 详细测试结果

#### 场景1: 正常场景 (CASE-A01)

```
输入: 模拟全部取数成功的L1证据包
审计器结论: PASS / Gate=READY
CRITICAL事件: 0, HIGH事件: 0
G06A状态: ✅ PASS
Gate综合: READY
结果: ✅ 符合预期
```

#### 场景2: DEP全阻塞场景 (CASE-D01)

```
输入: 全部条目data_fetchable=FALSE, dep_block_all=true
审计器结论: FAIL / Gate=NOT_READY
CRITICAL事件: 1 (G-06: 有效桥接率0%未达阈值)
HIGH事件: 5 (DEP-CLASS/DEP-GATE/对照组异常)
G06A状态: ❌ FAIL
Gate综合: NOT_READY (阻断)
结果: ✅ 符合预期 — 审计FAIL正确阻断Gate
```

#### 场景3: 旧口径造假场景 (CASE-N01)

```
输入: bridge_rate=1.0, metadata_rate=1.0, real_fetchable_rate=0.0
      无取数数据, 标记为COMPLETED
审计器结论: FAIL / Gate=NOT_READY
CRITICAL事件: ≥3 (G-09脚本审计+G-06桥接率+D01.2真实取数)
G06A状态: ❌ FAIL
Gate综合: NOT_READY (阻断)
结果: ✅ 符合预期 — 旧口径造假被正确拦截
```

#### 场景4: 部分恢复场景 (CASE-P01)

```
输入: 50%取数成功, metadata_rate=1.0, real_fetchable_rate=0.5
审计器结论: FAIL / Gate=NOT_READY (0.5 < 1.0阈值)
G06A状态: ❌ FAIL
Gate综合: NOT_READY
结果: ✅ 符合预期 — DEP阻塞不豁免Gate
```

#### 场景5: 审计器不可用场景

```
输入: --audit-validate + auditor_path不存在
审计器结论: SKIP
G06A状态: ⏭️ SKIP
Gate综合: 不受审计影响, 仅由G10决定
结果: ✅ 符合预期 — 优雅降级
```

---

## 3. 集成代码变更说明

### 3.1 gate_pre_check_auto_v2.py 新增内容

| 变更 | 说明 |
|------|------|
| `--audit-validate` 参数 | 启用审计器联动 |
| `--audit-file <path>` 参数 | 指定审计证据包JSON文件 |
| `AuditValidator` 类 | 封装evidence_auditor调用, 支持subprocess和直接注入 |
| `check_g06a_audit_validation()` 方法 | G06A检查项, 调用审计器并合并结果 |
| `_build_l1_evidence()` 方法 | 自动从桥接快照构建L1证据包 |
| G06A检查项 | 新增至GATE_CHECKS和报告 |
| 审计事件详情 | 报告新增"2.5 HERMES审计器预审结果"章节 |
| Gate综合判定 | G10+G06A联合判定Gate状态 |

### 3.2 与V1的兼容性

| 维度 | V1 | V2 |
|------|-----|-----|
| 默认模式 | 标准检查 | 标准检查 (完全兼容) |
| 审计联动 | 无 | 可选 (--audit-validate) |
| 检查项 | G01~G10 | G01~G10 + G06A |
| 报告格式 | V1.0 | V2.0 |
| 输出文件 | v86_rc2_dshb_gate_auto_check_report.md | v86_rc2_dshb_gate_auto_check_report_v2.md |

---

## 4. 审计器调用契约

### 4.1 L1证据包格式

```json
{
  "fingerprint": "DSHB-L1-20261016_080000",
  "run_id": "20261016_080000",
  "session_id": "DSHB-V86-RC2-...",
  "total_calls": 178,
  "generated_at": "2026-10-16T08:00:00.000000",
  "caller": "DSHB_V86_RC2_L1_SELF_TEST",
  "dshb_reuse": false,
  "metadata_rate": 0.736,
  "real_fetchable_rate": 0.0,
  "control_check": {"http_status": 200, "has_nonzero_value": false},
  "script_audit": {
    "uses_search_passthrough": false,
    "has_id_consistency_assert": true,
    "zero_value_counts_as_pass": false,
    "retains_raw_payload": true
  },
  "dep_block_all": true,
  "calls": [...]
}
```

### 4.2 审计器输出格式

```json
{
  "auditor_version": "1.0.0",
  "verdict": "FAIL",
  "gate_result": "NOT_READY",
  "gate_g06_real_fetchable_rate": 0.0,
  "gate_g09_script_audit": "PASS",
  "gate_g10_data_fetch": "FAIL",
  "events_summary": {
    "CRITICAL": 1,
    "HIGH": 5,
    "MEDIUM": 0,
    "LOW": 0,
    "total": 6
  },
  "events": [...]
}
```

---

## 5. 约束合规声明

| 约束 | 值 | 合规情况 |
|------|-----|---------|
| NO_ZHIJI_API_CALL | FALSE | ✅ 允许API调用 |
| NO_MODIFY_V85 | TRUE | ✅ 未修改V85基线 |
| NO_OVERWRITE | TRUE | ✅ V1保留, V2新建 |
| BRANCH_LOCKED | TRUE | ✅ 提交至指定分支 |
| 审计FAIL阻断Gate | — | ✅ G06A=FAIL → NOT_READY |
| 审计器独立调用 | — | ✅ subprocess隔离调用 |
| 优雅降级 | — | ✅ 审计器不可用→SKIP |

---

## 6. 文件清单

| # | 文件 | 说明 |
|---|------|------|
| 1 | `gate_pre_check_auto_v2.py` | Gate预检查V2脚本 (集成审计器) |
| 2 | `v86_rc2_dshb_gate_audit_integration_report.md` | 本报告 |
| 3 | `v86_rc2_dshb_gate_auto_check_report_v2.md` | V2预检查报告 (自动生成) |

---

## 7. 完成标准核验

| # | 标准 | 状态 |
|---|------|------|
| 1 | gate_pre_check_auto_v2.py创建完成 | ✅ |
| 2 | --audit-validate参数实现 | ✅ |
| 3 | 审计器PASS/CONDITIONAL_PASS/FAIL合并进G01~G10 | ✅ |
| 4 | 审计FAIL直接阻断Gate | ✅ |
| 5 | 集成验证用例全部通过 | ✅ (5/5场景) |
| 6 | Gate审计集成报告输出 | ✅ |

---

**报告版本**: V1.0
**最后更新**: 2026-10-16
**关联工单**: DSHB_V86_RC2_GATE_AUDIT_INTEGRATION_T3.2