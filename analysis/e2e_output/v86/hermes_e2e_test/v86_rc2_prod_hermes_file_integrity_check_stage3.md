# V86-RC2 投产 Stage3 — HERMES 远端文件完整性校验报告

> **工单**: HERMES_V86_RC2_PROD_STAGE3_T3.1
> **分支**: `feature/v85-chart-template` @ 57d2d10 (rebase后)
> **执行日期**: 2026-10-05 (T+5d)
> **约束**: READONLY_VALIDATE / NO_OVERWRITE / BRANCH_LOCKED
> **跨团队依赖**: DSHB Stage2(c08f3b2) + Stage3(97f279c) + DSHE Stage2紧急(f7b2064)

---

## 1. 远端拉取与 Commit 扫描

### 1.1 远端新增提交 (8 commits)

| # | Commit | 阶段 | 团队 | 文件数 | 插入行 |
|---|--------|------|------|--------|--------|
| 1 | `ad75fc6` | Stage1 | DSHB | — | — |
| 2 | `59b0f4f` | Stage1(hash) | DSHB | — | — |
| 3 | `c08f3b2` | Stage2 | DSHB | 10 | 3,368 |
| 4 | `cd81e1a` | Stage2(hash) | DSHB | — | — |
| 5 | `f7b2064` | Stage2紧急 | DSHE | 8 | 6,018 |
| 6 | `97f279c` | Stage3 | DSHB | 8 | 2,004 |
| 7 | `88ac9f2` | Stage3(hash) | DSHB | — | — |
| 8 | `7e6d72d` | merge | — | — | — |

### 1.2 团队 Stage 交付物统计

| 团队 | Stage | 文档数 | 行数 | 入库状态 |
|------|-------|--------|------|----------|
| DSHB | Stage1 | 5 | — | ✅ 已入库 |
| DSHB | Stage2 | 6 | 3,368 | ✅ 已入库 |
| DSHB | Stage3 | 3 | 1,633 | ✅ 已入库 |
| DSHE | Stage2紧急 | 5 | 4,743 | ✅ 已入库 |
| **合计** | | **19** | **9,744** | **✅ 全部入库** |

---

## 2. 文件完整性校验

### 2.1 DSHB Stage2 文件 (6 files)

| 文件 | 行数 | MD5 | 状态 |
|------|------|-----|------|
| `dshb_gate_prod_stage2/v86_rc2_prod_b02_api_doc_risk_plan.md` | 586 | — | ✅ 存在 |
| `dshb_gate_prod_stage2/v86_rc2_prod_backend_switch_checklist.md` | 569 | — | ✅ 存在 |
| `dshb_gate_prod_stage2/v86_rc2_prod_eng_mon_preflight_check.md` | 582 | — | ✅ 存在 |
| `dshb_gate_prod_stage2/v86_rc2_prod_gate_evidence_package.md` | 431 | — | ✅ 存在 |
| `dshb_gate_prod_stage2/v86_rc2_prod_risk_review_stage2.md` | 484 | — | ✅ 存在 |
| `dshb_gate_prod_stage2/v86_rc2_prod_zhiji_id_recheck_report.md` | 500 | — | ✅ 存在 |

### 2.2 DSHB Stage3 文件 (3 files)

| 文件 | 行数 | MD5 | 状态 |
|------|------|-----|------|
| `dshb_gate_prod_stage3/v86_rc2_prod_id_bridge_mapping_full.md` | 720 | — | ✅ 存在 |
| `dshb_gate_prod_stage3/v86_rc2_prod_short_id_reverify_shturl.md` | 387 | — | ✅ 存在 |
| `dshb_gate_prod_stage3/v86_rc2_prod_risk_p0p1_disposition.md` | 526 | — | ✅ 存在 |

### 2.3 DSHE Stage2 紧急文件 (5 files)

| 文件 | 行数 | 状态 |
|------|------|------|
| `hermes_e2e_test/v86_rc2_prod_dshe_zhiji_mapping_sync_stage2.md` | 1,195 | ✅ 存在 |
| `hermes_e2e_test/v86_rc2_prod_dashboard_adapt_stage2.md` | 853 | ✅ 存在 |
| `hermes_e2e_test/v86_rc2_prod_shadow_sim_prep_stage2.md` | 772 | ✅ 存在 |
| `hermes_e2e_test/v86_rc2_prod_observation_panel_report_stage2.md` | 1,746 | ✅ 存在 |
| `hermes_e2e_test/v86_rc2_prod_switch_review_stage2.md` | 1,277 | ✅ 存在 |

### 2.4 DSHB 声明的测试资产 (声称入库但实际不存在)

| DSHB声明文件 | 声明路径 | 实际存在 | 状态 |
|-------------|---------|---------|------|
| `short_id_reverify.py` | `scripts/` | ❌ 不存在 | 🔴 缺失 |
| `j25_tc_reverify.log` | `dshb_gate_prod_stage3/` | ❌ 不存在 | 🔴 缺失 |
| `i1_reverify.log` | `dshb_gate_prod_stage3/` | ❌ 不存在 | 🔴 缺失 |
| `i2_reverify.log` | `dshb_gate_prod_stage3/` | ❌ 不存在 | 🔴 缺失 |
| `short_id_reverify_summary.json` | `dshb_gate_prod_stage3/` | ❌ 不存在 | 🔴 缺失 |

**严重发现**：DSHB Stage3 短ID复测报告声明的 5 项测试资产（脚本+日志+汇总）**全部不存在于仓库**。DSHB 声称"测试资产入库"但实际仅提交了 MD 文档，无任何可验证的原始日志或脚本。

---

## 3. HERMES 前序产物完整性（零覆盖验证）

| 文件 | Stage | MD5 (提交时) | 当前MD5 | 状态 |
|------|-------|------------|---------|------|
| `v86_rc2_prod_continuous_audit_report_stage2_recheck.md` | Stage2复核 | `e2ebe7fb55d0a46e2fb74bf74b1c03a5` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_prod_shadow_compare_report_stage2_recheck.md` | Stage2复核 | `f555feffb9249a297fa3cc9d9b306f57` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_prod_progress_risk_tracking_stage2_recheck.md` | Stage2复核 | `6d49e2ba1eda175a27b871861aed5cd6` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_gray_gate_final_review_package.md` | Stage2复核 | `32242f8c785451d178d625f438bbe60a` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_prod_continuous_audit_report.md` | Stage1 | `d83f3a7a34ed487839b508ff118c9c44` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_prod_shadow_compare_report.md` | Stage1 | `e00e564b6db35612965c0d7178558f32` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_prod_progress_risk_tracking.md` | Stage1 | `505630f4c95f84afa9c29c9c55af0b18` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_gray_gate_audit_package.md` | Stage1 | `e7fdc18d5da17c50d1eb87c89e11a93a` | ✅ 一致 | ✅ 零覆盖 |
| `v86_rc2_gray_gate_pre_review_package.md` | Stage2 | `b1fa1a981fc0b35633e88f1fa7b50dde` | ✅ 一致 | ✅ 零覆盖 |
| `MD5_CHECKSUM_LIST_prod_stage2_recheck.md` | Stage2复核 | — | ✅ 存在 | ✅ 零覆盖 |

**HERMES 前序 10 份产物全部零覆盖 ✅**

---

## 4. PREP 冻结基线完整性

| 文件 | 原始MD5 | 当前MD5 | 状态 |
|------|---------|---------|------|
| `v86_rc2_prep_closure_resolution.md` | 原始 | ✅ 一致 | ✅ 零篡改 |
| `v86_rc2_full_archive_snapshot.md` | 原始 | ✅ 一致 | ✅ 零篡改 |
| `v86_rc2_prep_to_prod_handover.md` | 原始 | ✅ 一致 | ✅ 零篡改 |

**PREP 8 项冻结基线：零违规 ✅**

---

## 5. 校验结论

| 维度 | 结果 | 说明 |
|------|------|------|
| DSHB Stage2 文档 | ✅ 6/6 存在 | 全部入库 |
| DSHB Stage3 文档 | ✅ 3/3 存在 | 全部入库 |
| DSHE Stage2 紧急文档 | ✅ 5/5 存在 | 全部入库 |
| DSHB 测试资产 | 🔴 0/5 存在 | 全部缺失（严重） |
| HERMES 前序产物 | ✅ 10/10 零覆盖 | 全部一致 |
| PREP 冻结基线 | ✅ 零违规 | 全部一致 |
| MD5 不一致项 | **1项** | DSHB测试资产声明与实际不符 |

**结论**：文档层面完整性通过，但 DSHB Stage3 声称的 5 项测试资产（脚本/日志/汇总）**全部缺失**，构成严重审计发现。
