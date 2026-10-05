# DSHB V86-RC2 Gate常态化预检查自动报告 V5

> **自动生成**: gate_pre_check_auto_v5.py
> **版本**: V5 (Production Environment Adaptation)
> **环境**: 🔴 PROD (prod)
> **执行时间**: 2026-10-05 15:29:56
> **执行耗时**: 0.2秒
> **检查项**: G01~G10 + G06A + PERF-GUARD + DS-06 (共13项)
> **工作目录**: `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix`
> **严格模式**: ❌ 否
> **审计联动**: ❌ 未启用
> **紧急旁路**: ❌ 未启用
> **综合结果**: ❌ HAS FAIL

---

## 1. 检查结果汇总

| 检查ID | 检查名称 | 状态 | 说明 | 证据 |
|--------|----------|------|------|------|
| G01 | 交付物完整性检查 | ❌ FAIL | 缺失: 复测汇总JSON (full_reverify_v3_combined_178_summary.json) | 现有: 8, 缺失: 1, 空: 0 |
| G02 | 约束合规性检查 | ✅ PASS | NO_MODIFY_V85=FOUND; NO_OVERWRITE=FOUND; BRANCH_LOCKED=FOUND; HERMES双口径=NOT_FOUND | 约束标记在产出文档中有体现 |
| G03 | 文档口径一致性检查 | ❌ FAIL | 发现953处旧口径违规: v86_rc2_dshb_dep_fuse_dryrun_report.md: 桥接率0%未达阈值100%; v86_rc2_dshb_dep_fuse_dryrun_report.md: 桥接率0%未达阈值100%; v86_rc2_dshb_dep_fuse_dryrun_report.md: 桥接率 | 100%; v86_rc2_dshb_dep_fuse_dryrun_report.md: 桥接率 | 100%; v86_rc2_dshb_dep_fuse_dryrun_report.md: 有效桥接率0%未达阈值100% | 旧口径100%未标注OLD_CALIBER |
| G04 | API调用日志完整性检查 | ✅ PASS | 共25个日志文件 | 日志目录存在, 文件数=25 |
| G05 | 桥接表数据准确性检查 | ✅ PASS | 总计=178, 元数据完成=131(73.6%), 真实取数=0(0.0%), Gate=NOT_READY | threshold=80%, actual=0.0% |
| G06 | 风险台账完整性检查 | ✅ PASS | HERMES五类: 5/5 存在 | INTERNAL=✅; DEP_BLOCK=✅; MIXED=✅; CLOSED=✅; MITIGATED=✅ |
| G06A | HERMES审计器预审 (V2新增) | ⏭️ SKIP | 审计器联动未启用 (使用--audit-validate启用) | audit_validate=False |
| G07 | 跨团队通知合规性检查 | ⚠️  WARN | 缺失事件类型: DEP_READY_DETECTED | 已有: HERMES_NOTIFICATION, TEST_EVENT_V2, DSHE_NOTIFICATION, 缺失: DEP_READY_DETECTED |
| G08 | 审计链路可追溯性检查 | ✅ PASS | 4/4 追溯项通过 | md5_manifest=✅; snapshot_md5=✅; log_dirs=✅; risk_md5=✅ |
| G09 | 脚本审计 | ⚠️  WARN | 1个问题: 复测脚本包含1个搜索相关关键词 | 复测脚本包含1个搜索相关关键词 |
| G10 | 真实取数校验 | 🔴 NOT_READY | data_fetchable=0/178 (0.0%), 阈值=80%, Gate=NOT_READY | fetch_rate=0.0% vs threshold=80% |
| PERF-GUARD | 性能预算守护 (V4新增) | ⏭️ SKIP | 未执行审计器校验, PERF-GUARD不适用 | audit_validate=False or no duration data |
| DS-06 | DEP状态抖动检测 (V4新增) | ✅ PASS | DEP状态稳定: DEP-REG-001 在15min窗口内 无抖动 (切换1次 < 阈值2), 状态序列=['ACTIVE', 'BLOCKED', 'BLOCKED', 'BLOCKED'] | transitions=1, window=15min, max_allowed=2, states=['ACTIVE', 'BLOCKED', 'BLOCKED', 'BLOCKED'] |

---

## 2. 统计摘要

| 指标 | 值 |
|------|-----|
| 总检查项 | 13 |
| ✅ PASS | 6 |
| ❌ FAIL | 2 |
| ⚠️  WARN | 3 |
| ❌ ERROR | 2 |
| ⏭️ SKIP | 2 |
| 🚨 BYPASS | 0 |
| 通过率 | 46% |

---

## 2.1 环境配置 (V5新增)

| 配置项 | 值 |
|--------|-----|
| 运行环境 | PROD |
| 超时设置 | 30s |
| 审计超时 | 30s |
| 日志级别 | INFO |
| 审计日志目录 | prod_audit_logs/ |
| 重试次数 | 3 |
| 退避因子 | 2 |
| 初始延迟 | 1.0s |
| 服务发现 | None |
| Token鉴权 | 未启用 |

### 生产环境详情

| 字段 | 值 |
|------|-----|
| 审计日志路径 | prod_audit_logs/ |
| 服务发现URL | None |
| Token鉴权 | 未启用 |

| Token状态 | ❌ 未加载 |
| Token错误 | Token authentication not enabled in this environment |

| 服务发现状态 | ❌ 未启用 |
| 服务发现错误 | Service discovery URL not configured |
| 生产审计日志 | `D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\prod_audit_logs\prod_audit_20261005_152956.jsonl` |

---
---

## 2.7 PERF-GUARD 性能预算守护 (V4新增)

| 字段 | 值 |
|------|-----|
| 状态 | SKIP |
| 审计耗时 | N/As |
| 预算阈值 | 60s |
| 告警阈值 | 45s |
| 余量 | N/As |

---

## 2.8 DS-06 DEP状态抖动检测 (V4新增)

| 字段 | 值 |
|------|-----|
| 状态 | PASS |
| DEP ID | DEP-REG-001 |
| 检测窗口 | 15min |
| 最大允许切换 | 2 |
| 实际切换次数 | 1 |
| 窗口内状态 | ACTIVE, BLOCKED, BLOCKED, BLOCKED |
| 抖动判定 | ✅ 稳定 |

---

## 2.10 生产审计日志 (V5新增)

| 字段 | 值 |
|------|-----|
| 审计日志目录 | `prod_audit_logs/` |
| 审计日志路径 | D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\prod_audit_logs\prod_audit_20261005_152956.jsonl |
| 审计日志大小 | 0 bytes |


---

## 3. 告警

- 🔔 🔧 [V5-ENV] Production mode active: timeout=30s, log_level=INFO, retry_max=3
- 🔔 G03-FAIL: 953处旧口径违规
- 🔔 G09: 1个脚本问题

---

## 4. Gate准入状态

| 状态项 | 值 |
|--------|-----|
| G05 桥接表准确率 | 总计=178, 元数据完成=131(73.6%), 真实取数=0(0.0%), Gate=NOT_READY |
| G10 真实取数率 | data_fetchable=0/178 (0.0%), 阈值=80%, Gate=NOT_READY |
| G06A 审计器预审 | 审计器联动未启用 (使用--audit-validate启用) |
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
| V3:L1证据包升级 | EVIDENCE_CONTRACT_V1 + DEP-REG-001 |
| V4:REG-06修复 | 审计器ERROR→FAIL(P0阻断) |
| V4:紧急旁路 | audit_service_emergency_bypass (默认关闭) |
| V4:PERF-GUARD | 性能预算守护 (审计耗时>60s告警) |
| V4:DS-06 | DEP抖动检测 (15min窗口) |
| V4:ROB-01 | 损坏证据容错 (JSON损坏→FAIL) |
| V5:环境分支 | --env=prod/sandbox (沙箱=V4兼容) |
| V5:生产超时 | 30s (沙箱60s) |
| V5:生产重试 | max_retries=3, backoff_factor=2 |
| V5:服务发现 | service_discovery_url (prod) |
| V5:Token鉴权 | token_auth_enabled (prod) |
| V5:生产审计日志 | prod_audit_logs/ (独立路径) |

---

**报告生成时间**: 2026-10-05 15:29:56
**报告版本**: V5.0
**关联工单**: DSHB_V86_RC2_RDEP07_GATE_PROD_PREP / T3.2
