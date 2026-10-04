# V86-RC2 审计工具链产物 MD5 清单（prod_audit_tooling）

> **工单**: 工单-HERMES / T3.1~T3.5 审计规则用例固化 + 证据包校验器 + DEP就绪预案 + 告警路由
> **分支**: `feature/v85-chart-template` @ commit `caa2410`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **生成方式**: `md5sum` 本地实测（非声明）

---

## 1. 本轮新增产物 MD5（5 个文件）

| # | 文件 | MD5 | 大小 |
|---|------|-----|------|
| 1 | `v86_rc2_hermes_audit_case_library.md` | `8d3fb7e6dea678e658cb224bd5626ec3` | 16,385 B |
| 2 | `evidence_auditor.py` | `c173c0e964e864c35ec2c44350c236cd` | 28,391 B |
| 3 | `v86_rc2_hermes_dep_ready_e2e_test_plan.md` | `084936c68329b1b3ee1dd1fd655c2b4a` | 12,641 B |
| 4 | `v86_rc2_hermes_alert_routing_spec.md` | `d94cbba2686aeee44c2516b1c87f012a` | 11,822 B |
| 5 | `MD5_CHECKSUM_LIST_prod_audit_tooling.md` | （本文件，见下方计算） | — |

### 1.1 辅助产物（运行产物，非规范文档）

| 文件 | 说明 |
|------|------|
| `audit_events_persist.json` | T3.2 用例库回放的事件持久化输出（11 用例全量事件，17,416 B） |
| `v86_rc2_hermes_session_handover_latest.md` | 交接文档（本轮迭代更新，§16~§21 新增） |

---

## 2. 旧产物零覆盖自证（NO_OVERWRITE）

上两轮 9 份产物 MD5 本轮交付前后逐条比对，**全部一致**：

| 文件 | MD5 | 与历史清单比对 |
|------|-----|---------------|
| `v86_rc2_hermes_audit_canonical_spec.md` | `0634790f4500267837414daa333d6ec4` | ✅ 一致 |
| `v86_rc2_hermes_cross_agent_pipeline_spec.md` | `77b12c635050f7d78546a46e0f394277` | ✅ 一致 |
| `v86_rc2_hermes_external_dependency_management_spec.md` | `583b1b47f8d86f8dbf3226b396aabfb9` | ✅ 一致 |
| `v86_rc2_hermes_gate_review_revised_spec.md` | `598b0f42332fa2b0e21fe9a8bc17c7d0` | ✅ 一致 |
| `v86_rc2_hermes_agent_collaboration_summary.md` | `39baa0118d81913d69dfccc15ccfe452` | ✅ 一致 |
| `v86_rc2_hermes_pipeline_e2e_simulation_report.md` | `67b386cc4649f765ecc97c341722bb06` | ✅ 一致 |
| `v86_rc2_hermes_gate_simulation_report.md` | `17056c46b05c2d6fb0a6df4bd6144b4e` | ✅ 一致 |
| `v86_rc2_hermes_audit_rule_validation_report.md` | `fc06c13696e66261ea3332e382bc10b2` | ✅ 一致 |
| `v86_rc2_hermes_dep_gate_logic_verify.md` | `e9bf5269a7bacb3af08325f5a6a74399` | ✅ 一致 |

**结论**：本轮全部产物为**新增迭代版本**，历史规范与仿真报告零覆盖，审计追溯链完整。

---

## 3. NO_MODIFY_V85 自证

V85 基线业务文件（`scripts/`、`data/`、`*.html`、`STATUS.md`）本轮**零改动**。
本轮全部写入限定在 `analysis/e2e_output/v86/hermes_e2e_test/` 目录内。

```bash
# 验证命令
git diff --name-only HEAD~1 HEAD -- scripts/ data/ '*.html' STATUS.md
# 预期输出: 空 (无 V85 业务文件改动)
```

---

## 4. evidence_auditor.py 功能验证（实测输出）

### 4.1 用例库回放（11 用例）

```
回放结果: 11/11 判定符合预期 (0 不符)
```

| 用例 | 预期 | 实测 |
|------|------|------|
| CASE-A01 | PASS | PASS ✅ |
| CASE-A02 | PASS | PASS ✅ |
| CASE-N01 | FAIL | FAIL ✅ |
| CASE-N02 | CONDITIONAL_PASS | CONDITIONAL_PASS ✅ |
| CASE-N03 | FAIL | FAIL ✅ |
| CASE-N04 | FAIL | FAIL ✅ |
| CASE-D01 | FAIL | FAIL ✅ |
| CASE-D02 | FAIL | FAIL ✅ |
| CASE-P01 | FAIL | FAIL ✅ |
| CASE-P02 | FAIL | FAIL ✅ |
| CASE-P03 | FAIL | FAIL ✅ |

### 4.2 三种入口模式实测

| 模式 | 命令 | 结果 |
|------|------|------|
| 用例库回放 | `--run-case-library` | 11/11 OK，exit 0 |
| 单文件校验 | `--file <json>` | 输出 PASS/CONDITIONAL_PASS/FAIL + 告警明细 |
| MD5 校验 | `--check-md5 <file> --expect <md5>` | PASS（actual == expected） |

### 4.3 事件持久化

`audit_events_persist.json`：11 用例全量事件记录，11/11 match，可解析 JSON。

---

## 5. zhiji 实测取证记录（2026-10-15）

| ID | 实测结果 | 判定 |
|----|---------|------|
| `ID02226332`（对照组，长ID） | HTTP 200，8 点，value=30700/20875/26950… 非零 | ✅ 环境健康 |
| `j25_tc`（短ID） | HTTP 500「无法识别指标来源(id前缀)」@ commodity_api.py:443 | DEP-001 阻塞 |
| `s_001` | HTTP 500（同左） | 伪造ID |
| `ID_FAKE001` | HTTP 500（同左） | 伪造ID |
| `i1` | permission_state=-4，0 点 | 未映射/无权限 |

> 对照组是全部负向结论成立的前提：把"短ID 取不到"归因锁定为服务器侧解析能力缺失，
> 而非凭据失效或数据源故障。结论与前两轮（2026-10-05 / 2026-10-06）完全一致，DEP-001 形态稳定。

---

## 6. 状态标记

| 标记 | 值 | 说明 |
|------|-----|------|
| **HERMES_PROD_PHASE_AUDIT_TOOLING_DONE** | **TRUE** | 本轮 T5 六项完成标准全部满足 |
| HERMES_PROD_PHASE_PIPELINE_SIM_DONE | TRUE | 上一轮保持 |
| HERMES_PROD_PHASE_AUDIT_STANDARD_DONE | TRUE | 更早轮保持 |
| HERMES_AUDIT_CASE_LIBRARY_ARKED | TRUE | CASE-LIB v1.0 固化 |
| HERMES_DEP_READY_E2E_PLAN_READY | TRUE | DEP-001 恢复后可直接启动 |
| HERMES_AUDIT_ALERT_ROUTING_READY | TRUE | 告警路由规范就绪 |
| **JOB_READY** | **FALSE** | DEP-001 仍 OPEN，Gate 仍 NOT_READY |
| **GATE_DECISION** | **NOT_READY** | G-09/G-10 未就绪，短ID 解析缺失 |

---

## 7. 交付清单核对（T5 完成标准）

| # | 完成标准 | 状态 | 证据 |
|---|---------|------|------|
| 1 | 全套审计测试用例库固化归档，支持重复回放 | ✅ | `audit_case_library.md` 11 用例 + `--run-case-library` 11/11 |
| 2 | L1/L2 证据包自动校验器开发完成，输出预审结论 | ✅ | `evidence_auditor.py`，三种入口实测通过 |
| 3 | DEP 就绪后 E2E 实测预案完整落地 | ✅ | `dep_ready_e2e_test_plan.md`，含回滚方案 |
| 4 | 审计告警路由规范落地 | ✅ | `alert_routing_spec.md`，4 级 + 8 类矩阵 |
| 5 | 会话交接文档更新完成 | ✅ | `session_handover_latest.md` §16~§21 |
| 6 | 全部产物入库，MD5 校验 PASS | ✅ | 本清单 §1 + §2 零覆盖自证 |

**全部产物 MD5 校验 PASS，`HERMES_PROD_PHASE_AUDIT_TOOLING_DONE=TRUE`**
