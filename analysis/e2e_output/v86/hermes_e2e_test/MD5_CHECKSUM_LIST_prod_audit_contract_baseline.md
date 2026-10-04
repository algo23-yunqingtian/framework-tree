# V86-RC2 审计器加固 + 契约基线产物 MD5 清单（prod_audit_contract_baseline）

> **工单**: 工单-HERMES / T3.1~T3.5 审计器缺陷加固 + 三方证据包契约基线 + 批量预审调度 + DEP就绪检查清单 + 事件持久化升级
> **分支**: `feature/v85-chart-template` @ commit `dcf7194`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **生成方式**: `md5sum` 本地实测 + 三脚本自检实测

---

## 1. 本轮新增产物 MD5（9 个文件）

### 1.1 可执行脚本（3 个，全部实测通过）

| # | 文件 | MD5 | 大小 | 自检 |
|---|------|-----|------|------|
| 1 | `evidence_auditor_v2.py` | `479bf91bbf24200fe9528856ead7ec8a` | 47KB | ✅ SELF-TEST PASSED（23 用例 + 17 必命中 + 4 无告警） |
| 2 | `batch_evidence_audit_runner.py` | `ce2501c66f07a3cc01af41bddcba4631` | 18KB | ✅ 7 项自检通过 |
| 3 | `audit_event_store.py` | `6d04654ac4622ef51f93c4c8463f6478` | 23KB | ✅ 11 类检查通过 |

### 1.2 规范与契约文档（5 个）

| # | 文件 | MD5 | 大小 |
|---|------|-----|------|
| 4 | `EVIDENCE_CONTRACT_V1.md` | `0784d79aa43c6ce8bcae5803fdf222e6` | 15KB |
| 5 | `v86_rc2_hermes_audit_case_library_v2.md` | `e1c8d9e046360305dfcc7680e5395935` | 11KB |
| 6 | `v86_rc2_hermes_batch_audit_report_template.md` | `341a336ded66f3306ad678f187e54f4f` | 6KB |
| 7 | `v86_rc2_hermes_dep_ready_e2e_checklist.md` | `eaa381bd97bcf7d51bc899a06eb30ddb` | 13KB |
| 8 | `v86_rc2_hermes_alert_routing_spec_v2.md` | `bf3a091e326eb8680ad0d081af80e588` | 12KB |

### 1.3 运行产物（1 个）

| # | 文件 | MD5 | 说明 |
|---|------|-----|------|
| 9 | `audit_event_store_sample.jsonl` | `cdcf307bcd7d237269f86e95c2a1795a` | 事件存储样本（41 唯一事件，49 含去重，DEP-REG-001 最差 CRITICAL） |

### 1.4 本清单

| 文件 | 说明 |
|------|------|
| `MD5_CHECKSUM_LIST_prod_audit_contract_baseline.md` | 本文件 |
| `v86_rc2_hermes_session_handover_latest.md` | 交接文档（本轮迭代更新） |
| `STATUS.md` | 近期变更记录（本轮新增） |

---

## 2. 旧产物零覆盖自证（NO_OVERWRITE）

上两轮 14 份产物 MD5 本轮交付前后逐条比对，**全部一致**：

| 文件 | MD5 | 比对 |
|------|-----|------|
| `v86_rc2_hermes_audit_case_library.md`（v1） | `8d3fb7e6dea678e658cb224bd5626ec3` | ✅ 一致 |
| `evidence_auditor.py`（v1） | `c173c0e964e864c35ec2c44350c236cd` | ✅ 一致 |
| `v86_rc2_hermes_dep_ready_e2e_test_plan.md` | `084936c68329b1b3ee1dd1fd655c2b4a` | ✅ 一致 |
| `v86_rc2_hermes_alert_routing_spec.md`（v1） | `d94cbba2686aeee44c2516b1c87f012a` | ✅ 一致 |
| `MD5_CHECKSUM_LIST_prod_audit_tooling.md` | `3f71dcaeb6431b1773524988d40e95bb` | ✅ 一致 |
| `v86_rc2_hermes_audit_canonical_spec.md` | `0634790f4500267837414daa333d6ec4` | ✅ 一致 |
| `v86_rc2_hermes_cross_agent_pipeline_spec.md` | `77b12c635050f7d78546a46e0f394277` | ✅ 一致 |
| `v86_rc2_hermes_external_dependency_management_spec.md` | `583b1b47f8d86f8dbf3226b396aabfb9` | ✅ 一致 |
| `v86_rc2_hermes_gate_review_revised_spec.md` | `598b0f42332fa2b0e21fe9a8bc17c7d0` | ✅ 一致 |
| `v86_rc2_hermes_agent_collaboration_summary.md` | `39baa0118d81913d69dfccc15ccfe452` | ✅ 一致 |
| `v86_rc2_hermes_pipeline_e2e_simulation_report.md` | `67b386cc4649f765ecc97c341722bb06` | ✅ 一致 |
| `v86_rc2_hermes_gate_simulation_report.md` | `17056c46b05c2d6fb0a6df4bd6144b4e` | ✅ 一致 |
| `v86_rc2_hermes_audit_rule_validation_report.md` | `fc06c13696e66261ea3332e382bc10b2` | ✅ 一致 |
| `v86_rc2_hermes_dep_gate_logic_verify.md` | `e9bf5269a7bacb3af08325f5a6a74399` | ✅ 一致 |

**结论**：本轮全部产物为**新增迭代版本**（v2 后缀或新文件名），历史规范、
仿真报告、v1 脚本零覆盖，审计追溯链完整。

> ⚠️ **过程记录**：本轮开发中曾误将 v1 用例库内容覆盖写入 `v86_rc2_hermes_audit_case_library.md`，
> 已通过 `git checkout HEAD --` 恢复至原 MD5 `8d3fb7e6`，并改用新文件名
> `v86_rc2_hermes_audit_case_library_v2.md` 承载 v2 内容。该违规在本清单中如实记录。

---

## 3. NO_MODIFY_V85 自证

V85 基线业务文件（`scripts/`、`data/`、`*.html`、`STATUS.md` 业务段）本轮**零改动**。
本轮全部写入限定在 `analysis/e2e_output/v86/hermes_e2e_test/` 目录内，
另加 STATUS.md 变更记录（pre-commit hook 强制要求，属协作协议而非业务代码）。

```bash
git diff --name-only HEAD~1 HEAD -- scripts/ data/ '*.html'
# 预期: 空
```

---

## 4. 三脚本自检实测输出

### 4.1 evidence_auditor_v2.py

```
======================================================================
  evidence_auditor_v2 自回归测试  (auditor v2.0.0, contract EVIDENCE_CONTRACT_V1)
======================================================================
  用例数: 23  |  断言数: 17 必命中 + 4 无误报  |  基线: dcf7194
  ✅ 全部通过: 23 用例判定 + 17 必命中断言 + 4 无告警断言
  结论: SELF-TEST PASSED
```
exit code = 0

### 4.2 batch_evidence_audit_runner.py

```
batch_evidence_audit_runner 自检
  用例包数: 23
  判定分布: PASS=4 CONDITIONAL=2 FAIL=17
  等级分布: CRIT=39 HIGH=6 MED=2 LOW=0
  责任方路由: DSHB(36), DSHB/DSHE(4), DSHE(5), 提交方(2)
  总判定: BLOCKED
  ✅ 7 项自检全部通过
  结论: SELF-TEST PASSED
```
exit code = 0

### 4.3 audit_event_store.py

```
audit_event_store 自检
  检查项: 11 类 (归一化/幂等/校验/存储/去重/检索/统计/导入/规则集)
  ✅ 11 类检查全部通过
  结论: SELF-TEST PASSED
```
exit code = 0

### 4.4 v1 兼容回归（NO_OVERWRITE 验证）

```
回放结果: 11/11 判定符合预期 (0 不符)
```
v1 `evidence_auditor.py` 未被破坏，仍 11/11。

---

## 5. zhiji 实测取证记录（2026-10-15）

| ID | 实测结果 | 判定 |
|----|---------|------|
| `ID02226332`（对照组，长ID） | HTTP 200，8 点，value=30700/20875/26950… 非零 | ✅ 环境健康 |
| `j25_tc`（短ID） | HTTP 500「无法识别指标来源(id前缀)」@ commodity_api.py:443 | DEP-001 阻塞 |
| `s_001` | HTTP 500（同左） | 伪造ID |
| `i1` | permission_state=-4，0 点 | 未映射/无权限 |

DEP-001 形态与前四轮完全一致，仍 OPEN。

---

## 6. 状态标记

| 标记 | 值 | 说明 |
|------|-----|------|
| **HERMES_PROD_PHASE_AUDIT_CONTRACT_BASELINE_DONE** | **TRUE** | 本轮 T5 六项完成标准全部满足 |
| HERMES_AUDIT_CASE_LIBRARY_V2_ARCED | TRUE | CASE-LIB v2.0，23 用例，自回归 PASS |
| HERMES_EVIDENCE_CONTRACT_V1_BASELINE | TRUE | 三方证据包契约基线 |
| HERMES_BATCH_AUDIT_RUNNER_READY | TRUE | 批量预审调度器 |
| HERMES_DEP_READY_E2E_CHECKLIST_READY | TRUE | 76 项逐点清单，8 阶段 |
| HERMES_AUDIT_EVENT_STORE_V2_READY | TRUE | 事件持久化 v2，三方上报 + DEP 关联 |
| HERMES_PROD_PHASE_AUDIT_TOOLING_DONE | TRUE | 上轮保持 |
| HERMES_PROD_PHASE_PIPELINE_SIM_DONE | TRUE | 更早轮保持 |
| HERMES_PROD_PHASE_AUDIT_STANDARD_DONE | TRUE | 更早轮保持 |
| **JOB_READY** | **FALSE** | DEP-001 仍 OPEN |
| **GATE_DECISION** | **NOT_READY** | G-09/G-10 未就绪 |

---

## 7. 交付清单核对（T5 完成标准）

| # | 完成标准 | 状态 | 证据 |
|---|---------|------|------|
| 1 | evidence_auditor_v2 自带 self-test 自回归，新增多类边界场景 | ✅ | `--self-test` PASSED，23 用例 8 大类 + 17 必命中断言 |
| 2 | EVIDENCE_CONTRACT_V1 契约基线发布，三方对齐 | ✅ | `EVIDENCE_CONTRACT_V1.md`（11 章，含变更流程 + 三方矩阵） |
| 3 | 批量预审调度脚本，输出汇总预审报告 | ✅ | `batch_evidence_audit_runner.py`，7 段报告 + 4 维分组，7 项自检通过 |
| 4 | DEP 就绪 E2E 全链路勾选检查清单 | ✅ | `dep_ready_e2e_checklist.md`，76 项 8 阶段 |
| 5 | 审计事件持久化升级，支持接收关联 DEP 登记ID 存储三方告警 | ✅ | `audit_event_store.py`，三方上报 + 6 维检索 + 4 维统计，11 类自检通过 |
| 6 | 全部产物入库，MD5 校验 PASS | ✅ | 本清单 §1 + §2 零覆盖自证 |

**全部产物 MD5 校验 PASS，`HERMES_PROD_PHASE_AUDIT_CONTRACT_BASELINE_DONE=TRUE`**
