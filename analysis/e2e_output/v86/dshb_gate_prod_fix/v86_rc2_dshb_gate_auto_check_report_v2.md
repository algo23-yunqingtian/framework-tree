# DSHB V86-RC2 Gate常态化预检查自动报告 V2

> **自动生成**: gate_pre_check_auto_v2.py
> **版本**: V2 (集成HERMES evidence_auditor)
> **执行时间**: 2026-10-04 16:39:04
> **执行耗时**: 0.4秒
> **检查项**: G01~G10 + G06A (共11项)
> **工作目录**: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix`
> **严格模式**: ❌ 否
> **审计联动**: ✅ 启用
> **综合结果**: ❌ HAS FAIL

---

## 1. 检查结果汇总

| 检查ID | 检查名称 | 状态 | 说明 | 证据 |
|--------|----------|------|------|------|
| G01 | 交付物完整性检查 | ❌ FAIL | 缺失: 复测汇总JSON (full_reverify_v3_combined_178_summary.json) | 现有: 8, 缺失: 1, 空: 0 |
| G02 | 约束合规性检查 | ✅ PASS | NO_MODIFY_V85=FOUND; NO_OVERWRITE=FOUND; BRANCH_LOCKED=FOUND; HERMES双口径=NOT_FOUND | 约束标记在产出文档中有体现 |
| G03 | 文档口径一致性检查 | ❌ FAIL | 发现70处旧口径违规: v86_rc2_dshb_id_mapping_batch_plan.md: 桥接率 | ≥80% | 178/178=100%; v86_rc2_dshb_id_mapping_batch_plan.md: 有效桥接率 | ≥80% | 178/178=100%; v86_rc2_dshb_id_mapping_final_summary.md: 桥接率100%; v86_rc2_dshb_id_mapping_final_summary.md: 桥接率=100%; v86_rc2_dshb_id_mapping_final_summary.md: 桥接率=100% | 旧口径100%未标注OLD_CALIBER |
| G04 | API调用日志完整性检查 | ✅ PASS | 共25个日志文件 | 日志目录存在, 文件数=25 |
| G05 | 桥接表数据准确性检查 | ✅ PASS | 总计=178, 元数据完成=131(73.6%), 真实取数=0(0.0%), Gate=NOT_READY | threshold=80%, actual=0.0% |
| G06 | 风险台账完整性检查 | ✅ PASS | HERMES五类: 5/5 存在 | INTERNAL=✅; DEP_BLOCK=✅; MIXED=✅; CLOSED=✅; MITIGATED=✅ |
| G06A | HERMES审计器预审 (V2新增) | ❌ FAIL | 审计结论=FAIL, Gate阻断 (G-06/G-09/G-10至少一项不通过) | verdict=FAIL, gate=NOT_READY, CRITICAL=1, HIGH=5 |
| G07 | 跨团队通知合规性检查 | ⚠️  WARN | 缺失事件类型: DEP_READY_DETECTED | 已有: DSHE_NOTIFICATION, HERMES_NOTIFICATION, TEST_EVENT_V2, 缺失: DEP_READY_DETECTED |
| G08 | 审计链路可追溯性检查 | ✅ PASS | 4/4 追溯项通过 | md5_manifest=✅; snapshot_md5=✅; log_dirs=✅; risk_md5=✅ |
| G09 | 脚本审计 | ⚠️  WARN | 1个问题: 复测脚本包含1个搜索相关关键词 | 复测脚本包含1个搜索相关关键词 |
| G10 | 真实取数校验 | 🔴 NOT_READY | data_fetchable=0/178 (0.0%), 阈值=80%, Gate=NOT_READY | fetch_rate=0.0% vs threshold=80% |

---

## 2. 统计摘要

| 指标 | 值 |
|------|-----|
| 总检查项 | 11 |
| ✅ PASS | 5 |
| ❌ FAIL | 3 |
| ⚠️  WARN | 3 |
| ❌ ERROR | 0 |
| ⏭️ SKIP | 0 |
| 通过率 | 45% |

---

## 2.5 HERMES审计器预审结果 (V2新增)

| 字段 | 值 |
|------|-----|
| 审计器路径 | `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\hermes_e2e_test\evidence_auditor.py` |
| 审计器可用 | ✅ 是 |
| 审计结论 | FAIL |
| Gate结论 | NOT_READY |
| CRITICAL事件 | 1 |
| HIGH事件 | 5 |
| MEDIUM事件 | 0 |
| 总事件数 | 6 |
| 错误 | 无 |

### 审计事件列表 (前10条)

| # | 级别 | 规则 | 检测点 | 描述 |
|---|------|------|--------|------|
| 1 | HIGH | R-AUDIT-04 | D04.5 | ������ȡ��δͨ��, �޷��ж��������� -> G-10 �����ж� |
| 2 | HIGH | R-AUDIT-04 | DEP-CLASS | ���� DEPENDENCY_BLOCK �����ⲿ����֤��, ����Ϊ�ڲ�ȱ��: PB-001 |
| 3 | HIGH | R-AUDIT-04 | DEP-CLASS | ���� DEPENDENCY_BLOCK �����ⲿ����֤��, ����Ϊ�ڲ�ȱ��: PB-008 |
| 4 | HIGH | R-AUDIT-04 | DEP-CLASS | ���� DEPENDENCY_BLOCK �����ⲿ����֤��, ����Ϊ�ڲ�ȱ��: PB-009 |
| 5 | HIGH | R-AUDIT-04 | DEP-GATE | ȫ����Ŀ DEP ����, �������ڲ� P0/P1, �� Gate ά�� NOT_READY |
| 6 | CRITICAL | R-AUDIT-02 | G-06 | ��Ч�Ž��� 0.0000 δ����ֵ 100% -> Gate ǿ����� |

---

## 3. 告警

- 🔔 G03-FAIL: 70处旧口径违规
- 🔔 G06A-FAIL: 审计阻断, 1个CRITICAL事件
- 🔔 G09: 1个脚本问题

---

## 4. Gate准入状态

| 状态项 | 值 |
|--------|-----|
| G05 桥接表准确率 | 总计=178, 元数据完成=131(73.6%), 真实取数=0(0.0%), Gate=NOT_READY |
| G10 真实取数率 | data_fetchable=0/178 (0.0%), 阈值=80%, Gate=NOT_READY |
| G06A 审计器预审 | 审计结论=FAIL, Gate阻断 (G-06/G-09/G-10至少一项不通过) |
| Gate综合状态 | NOT_READY |

---

## 5. 约束合规声明

| 约束 | 值 |
|------|-----|
| NO_ZHIJI_API_CALL | FALSE (PROD_PHASE_ENABLED) |
| NO_MODIFY_V85 | TRUE |
| NO_OVERWRITE | TRUE |
| BRANCH_LOCKED | TRUE |
| 双指标强制输出 | 元数据完成率 + 真实有效桥接率 |
| 流水线退回旧日志作废 | 每次复测生成独立日志 |
| DEP_BLOCK不计入内部缺陷 | HERMES五类分类对齐 |
| Gate准入不豁免 | data_fetchable ≥ 80% → READY |
| 审计FAIL阻断Gate | G06A=FAIL → NOT_READY |

---

**报告生成时间**: 2026-10-04 16:39:04
**报告版本**: V2.0
**关联工单**: DSHB_V86_RC2_GATE_AUDIT_INTEGRATION_T3.2
