# V86-RC2 批量预审汇总报告模板

> **工单**: 工单-HERMES / T3.3 批量预审调度脚本开发
> **分支**: `feature/v85-chart-template` @ commit `dcf7194`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **生成工具**: `batch_evidence_audit_runner.py` v1.0.0
> **契约**: EVIDENCE_CONTRACT_V1
> **用途**: 批量证据包审计报告的**结构模板 + 实测样例**。调度器 `--md` 参数会生成同结构报告。

---

## 0. 使用方式

```bash
cd analysis/e2e_output/v86/hermes_e2e_test

# 批量审计指定目录 (L1 + L2 分开或合并)
python3 batch_evidence_audit_runner.py --dir <证据包目录> \
  --md batch_report.md --json batch_report.json

# L1/L2 分目录审计
python3 batch_evidence_audit_runner.py \
  --l1 <DSHB_L1目录> --l2 <DSHE_L2目录> --md batch_report.md

# 内置夹具演示 (23 用例)
python3 batch_evidence_audit_runner.py --demo --md batch_report.md

# 自检 (7 项断言)
python3 batch_evidence_audit_runner.py --self-test
```

**退出码**：`0` = 无 CRITICAL；`1` = 有 CRITICAL（阻断）；`2` = 用法/扫描错误。

---

## 1. 报告结构（7 段固定结构）

| 段 | 内容 | 判定用途 |
|----|------|---------|
| §1 总体结论 | 扫描数/审计数/跳过数/总判定/Gate 汇总 | 一眼看结论 |
| §2 按判定分组 | PASS / CONDITIONAL_PASS / FAIL 包数 | 放行比例 |
| §3 按风险等级分组 | CRITICAL / HIGH / MEDIUM / LOW 告警数 | 阻断强度 |
| §4 按审计规则分组 | 各规则告警数 + 责任方 | 缺陷归因 |
| §5 告警责任方路由 | DSHB / DSHE / 提交方 分组 | 派工 |
| §6 逐包明细 | 每包判定 + Gate 三指标 + DEP | 逐包追溯 |
| §7 CRITICAL 告警清单 | 全量 CRITICAL 明细 | 必须处置项 |

---

## 2. 实测样例（2026-10-15，23 用例演示）

### 2.1 总体结论

| 指标 | 值 |
|------|-----|
| 扫描文件 | 23 |
| 实际审计 | 23 |
| 跳过（非证据包） | 0 |
| **总判定** | **BLOCKED** |
| 最严重等级 | CRITICAL |
| Gate READY | 0 |
| Gate NOT_READY | 23 |

### 2.2 按判定分组

| 判定 | 包数 | 占比 |
|------|------|------|
| PASS | 4 | 17.4% |
| CONDITIONAL_PASS | 2 | 8.7% |
| FAIL | 17 | 73.9% |

> 注：此演示集刻意包含大量负向用例，占比不代表真实交付质量。

### 2.3 按风险等级分组

| 等级 | 告警数 |
|------|--------|
| CRITICAL | 39 |
| HIGH | 6 |
| MEDIUM | 2 |
| LOW | 0 |

### 2.4 按审计规则分组

| 规则 | 责任方 | 告警数 |
|------|--------|--------|
| R-AUDIT-01 双证据 | DSHB | 4 |
| R-AUDIT-02 桥接率口径 | DSHB | 8 |
| R-AUDIT-03 L2 独立链 | DSHE | 5 |
| R-AUDIT-04 Gate 强制项 | DSHB | 24 |
| R-CONTRACT-V1 契约完整性 | 提交方 | 2 |
| R-DEP-STATE DEP 状态机 | DSHB/DSHE | 4 |
| R-LEGACY-CAL 存量旧口径 | DSHB | 3 |

### 2.5 告警责任方路由

| 责任方 | 告警数 | 涉及规则 |
|--------|--------|---------|
| **DSHB** | 36 | R-AUDIT-01, R-AUDIT-02, R-AUDIT-04, R-LEGACY-CAL |
| **DSHE** | 5 | R-AUDIT-03 |
| **DSHB/DSHE** | 4 | R-DEP-STATE |
| 提交方 | 2 | R-CONTRACT-V1 |

### 2.6 逐包明细（节选）

| 文件 | 判定 | Gate | G-06 | G-09 | G-10 | CRIT | HIGH | DEP |
|------|------|------|------|------|------|------|------|-----|
| CASE-A01.json | PASS | NOT_READY | 1.00 | PASS | PASS | 0 | 0 | - |
| CASE-N01.json | FAIL | NOT_READY | 0.00 | FAIL | FAIL | 9 | 0 | - |
| CASE-D01.json | FAIL | NOT_READY | 0.00 | PASS | PASS | 1 | 1 | DEP-REG-001 |
| CASE-X02.json | FAIL | NOT_READY | 1.00 | PASS | PASS | 1 | 0 | DEP-REG-001 |

> **注**：Gate 结论与预审结论是**两个独立维度**。
> - `verdict=FAIL` 表示证据包本身不合格；
> - `gate_result=NOT_READY` 表示即使包合格，Gate 准入也未满足（如桥接率未达阈值）。
> - CASE-A01 `PASS` 但 `NOT_READY` 是预期行为：DEP-001 未就绪时 G-10 无法通过。

---

## 3. 汇总逻辑校验（调度器 --self-test 7 项断言）

| # | 断言 | 说明 |
|---|------|------|
| 1 | 全部用例被识别为证据包 | 防扫描/识别逻辑漏包 |
| 2 | 无用例被误判 SKIP | 防格式识别误杀 |
| 3 | 汇总计数一致（审计+跳过=扫描） | 防计数错误 |
| 4 | by_verdict 合计 = audited | 防判定分组漏计 |
| 5 | 等级汇总 = 各包之和（4 等级分别核对） | 防等级聚合错误 |
| 6 | 所有规则都有路由映射 | 防告警无人认领 |
| 7 | 总判定与最差等级一致 + Markdown 7 段完整 | 防结论错误/渲染缺段 |

实测：`✅ 7 项自检全部通过 / SELF-TEST PASSED / EXIT=0`

---

## 4. 集成建议

### 4.1 与流水线的挂载点

```
L1 DSHB 自测包  ┐
                ├─→ batch_evidence_audit_runner.py --md report.md
L2 DSHE 证据包  ┘        │
                        ▼
              L3 HERMES 预审（按 report §5 路由派工）
```

### 4.2 与 CI 的挂载

```bash
# pre-commit 或 CI 步骤: 有 CRITICAL 即阻断
python3 batch_evidence_audit_runner.py --dir <包目录> || {
  echo "❌ 存在 CRITICAL 告警, 阻断流水线"; exit 1; }
python3 evidence_auditor_v2.py --self-test || {
  echo "❌ 审计器自回归失败"; exit 1; }
```

### 4.3 报告留存

- Markdown 报告：人读，随交付物入库；
- JSON 报告：机读，接入告警事件持久化（见 T3.5）；
- 退出码：CI 门禁。

---

## 5. 模板完整性自证

| 要素 | 状态 |
|------|------|
| 调度器脚本 | `batch_evidence_audit_runner.py`（18KB，实测通过） |
| 报告段结构 | 7 段固定 |
| 分组维度 | 判定 / 等级 / 规则 / 责任方 4 维 |
| 责任方路由 | 7 规则 → DSHB/DSHE/DSHB-DSHE/提交方 |
| 自检断言 | 7 项，全部通过 |
| 退出码语义 | 0/1/2 三级 |
| CI 集成 | 两级门禁（调度器 + 审计器自回归） |

**状态标记**：`HERMES_BATCH_AUDIT_RUNNER_READY=TRUE`
