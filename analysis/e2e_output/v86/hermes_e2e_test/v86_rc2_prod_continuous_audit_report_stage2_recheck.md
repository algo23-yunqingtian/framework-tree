# V86-RC2 投产 Stage2 复核审计报告 — 持续审计 + 跨团队基线一致性

> **工单**: HERMES_V86_RC2_PROD_STAGE2_RECHECK
> **分支**: `feature/v85-chart-template` @ `af1e5fb`
> **日期**: 2026-10-05 (T+3d)
> **模式**: READONLY_VALIDATE=TRUE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 1. 执行摘要

### 1.1 复核范围
- 拉取 `feature/v85-chart-template` 远端最新提交（rebase 整合 3 个新 commit）
- 审计 DSHE 投产阶段提交的 5 份新文档（commit `649f1f4` + `027f2d1`）
- 校验 PREP 8 项冻结基线完整性
- 交叉比对 DSHB 底层 zhiji ID 映射与 DSHE 展示层指标绑定

### 1.2 关键发现

| 维度 | 结论 | 严重度 |
|------|------|--------|
| DSHE Stage1 投产文档 | ✅ 已提交（5 份 / 4,649 行） | — |
| DSHB Stage2 紧急整改 | 🔴 **未提交**（0 commit） | P0 |
| 跨团队基线一致性 | 🔴 **映射体系完全断裂** | P0 |
| R-S01 闭环判定 | 🔴 **未闭环** | P0 |
| 短 ID 故障修复 | 🔴 **全部未修复**（j25_tc HTTP 500, i1/i2/i11 permission=-4） | P0 |
| PREP 8 项冻结 | ✅ 零违规 | — |

### 1.3 R-S01 闭环判定

**判定结论：🔴 R-S01 未闭环 — 跨团队基线不一致风险持续存在**

核心证据：
1. **DSHE 使用自定义语义化 ID**（`pb_inventory_society` 等 190 项），非 zhiji 系统 ID
2. **DSHB 使用 zhiji 短 ID/长 ID**（`j25_tc`/`ID02226332` 等 576 项）
3. **两侧映射文档中无任何交叉引用**：DSHE 文档全文搜索 `j25_tc`/`ID0xxx` 命中 0 次
4. **短 ID 故障持续**：`j25_tc` HTTP 500, `i1/i2/i11` permission_state=-4
5. **DSHB 紧急整改未提交**：无 ENG-01、无短 ID 修复、无 ID 映射、无口径对齐

---

## 2. 远端提交审计

### 2.1 rebase 整合记录

| 项目 | 内容 |
|------|------|
| 拉取前本地 HEAD | `913392b`（HERMES Stage2 初审） |
| 远端 FETCH_HEAD | `28b4747` |
| 远端新增 commit | 3 个（`027f2d1` + `649f1f4` + `28b4747`） |
| rebase 后本地 HEAD | `af1e5fb` |
| 冲突文件 | `JOB_READY.flag`（已解决，两侧标记块均保留） |

### 2.2 远端新增 commit 清单

| Commit | 时间 | 作者 | 描述 |
|--------|------|------|------|
| `027f2d1` | 10-03 19:25 | agent-2 | [A] DSHE PROD PHASE STAGE1 T3.5: 投产切换与回滚评审报告 |
| `649f1f4` | 10-03 19:32 | agent-2 | [A] DSHE PROD PHASE STAGE1: 展示层双口径适配+zhiji映射同步+影子仿真+观测大盘+切换回滚 |
| `28b4747` | 10-03 19:35 | agent-2 | chore: update commit hash references to 649f1f4 in DSHE_PROD_PHASE_STAGE1 files |

**关键发现**：DSHE 提交的是 **PROD_PHASE_STAGE1**（投产阶段第一批），非工单声称的 "Stage2 紧急整改交付物"。DSHB **无任何新提交**。

### 2.3 DSHE Stage1 交付物清单

| 文件 | 行数 | 内容 |
|------|------|------|
| `v86_rc2_prod_dashboard_adapt_report.md` | 835 | Dashboard 双口径适配报告（36 图表 / 178 指标） |
| `v86_rc2_prod_dshe_zhiji_mapping_sync.md` | 798 | zhiji_id 映射同步报告（190 项 / 7 已确认 / 183 待确认） |
| `v86_rc2_prod_shadow_sim_prep.md` | 1253 | 影子仿真环境 & 一键切换脚本准备文档 |
| `v86_rc2_prod_observation_panel_report.md` | 1231 | 投产观测面板与告警规则报告（18 项观测指标） |
| `v86_rc2_prod_switch_review.md` | 932 | 投产切换与回滚评审报告（7 步演练 / 3 级回滚 / 19 风险） |

---

## 3. PREP 8 项冻结基线校验

### 3.1 冻结条目完整性

| # | 冻结条目 | 状态 | 校验方式 |
|---|----------|------|----------|
| 1 | PREP 封板决议 | ✅ 未篡改 | MD5 对比 |
| 2 | 全量归档快照（132 文件） | ✅ 未篡改 | MD5 对比 |
| 3 | 投产交接总文档 | ✅ 未篡改 | MD5 对比 |
| 4 | PREP 阶段 commit 链 | ✅ 未篡改 | git log 校验 |
| 5 | 132 文件 MD5 清单 | ✅ 全部匹配 | 逐项校验 |
| 6 | V85 基线 | ✅ 未修改 | git diff 确认 |
| 7 | PREP 8 项冻结声明 | ✅ 未篡改 | 文档内容校验 |
| 8 | BRANCH_LOCKED | ✅ 合规 | 分支确认 |

**结论**：PREP 8 项冻结基线零违规 ✅

### 3.2 Stage1 产物零覆盖校验

| 文件 | Stage1 MD5 | 复核 MD5 | 状态 |
|------|-----------|---------|------|
| `v86_rc2_prod_continuous_audit_report.md` | `d83f3a7a34ed487839b508ff118c9c44` | `d83f3a7a34ed487839b508ff118c9c44` | ✅ 一致 |
| `v86_rc2_prod_shadow_compare_report.md` | `e00e564b6db35612965c0d7178558f32` | `e00e564b6db35612965c0d7178558f32` | ✅ 一致 |
| `v86_rc2_prod_progress_risk_tracking.md` | `505630f4c95f84afa9c29c9c55af0b18` | `505630f4c95f84afa9c29c9c55af0b18` | ✅ 一致 |
| `v86_rc2_gray_gate_audit_package.md` | `e7fdc18d5da17c50d1eb87c89e11a93a` | `e7fdc18d5da17c50d1eb87c89e11a93a` | ✅ 一致 |

**结论**：Stage1 产物零覆盖 ✅

---

## 4. 跨团队基线一致性校验（T4.6 最高优先级）

### 4.1 DSHB 底层 ID 映射体系

| 维度 | 内容 |
|------|------|
| ID 体系 | zhiji 系统短 ID + 长 ID 混合 |
| 典型 ID | `j25_tc`（铅精矿加工费短ID）, `ID02226332`（LME 镍库存长ID） |
| 总量 | 576 项 backlog |
| 已验证 | 3 项（PB/CU/ZN 各 1 项） |
| 验证率 | 0.5% |
| 短 ID 故障 | `j25_tc` HTTP 500, `i1/i2/i11` permission=-4 |

### 4.2 DSHE 展示层 ID 映射体系

| 维度 | 内容 |
|------|------|
| ID 体系 | 自定义语义化英文标识符 |
| 典型 ID | `pb_inventory_society`（铅锭社会库存）, `cu_inventory_society`（铜锭社会库存） |
| 总量 | 190 项（7 已确认 / 183 待确认） |
| 确认率 | 3.7% |
| 关联 zhiji 系统 ID | **0 项**（文档全文搜索 `j25_tc`/`ID0xxx` 命中 0 次） |

### 4.3 一致性交叉校验矩阵

| 校验维度 | DSHB 侧 | DSHE 侧 | 一致性 |
|----------|---------|---------|--------|
| ID 编码体系 | zhiji 短ID/长ID | 自定义语义化ID | 🔴 **完全不同** |
| 交叉引用字段 | 无 DSHE ID 引用 | 无 DSHB ID 引用 | 🔴 **零交叉** |
| 口径定义对齐 | DSHB 口径（Gate评审+线上告警） | DSHE 口径（Gate评审视图+线上告警视图） | 🟡 文档描述对齐，无字段级映射 |
| 指标总数 | 576 项 backlog | 178 指标 + 19 回填字段 | 🔴 **数量级不匹配** |
| 短 ID 修复 | 无提交 | 无提交 | 🔴 **未修复** |
| ENG-01 | 无提交 | 无提交 | 🔴 **未启动** |

### 4.4 R-S01 闭环判定

**判定：🔴 R-S01 未闭环**

闭环条件清单：

| # | 闭环条件 | 当前状态 | 差距 |
|---|----------|----------|------|
| 1 | DSHB 提交短 ID 修复 | 🔴 未提交 | 完全缺失 |
| 2 | DSHB 提交 ENG-01 | 🔴 未提交 | 完全缺失 |
| 3 | DSHB 提交 ID 映射表 | 🔴 未提交 | 完全缺失 |
| 4 | DSHB 提交口径对齐文档 | 🔴 未提交 | 完全缺失 |
| 5 | DSHE 展示层映射更新 | 🟡 提交了映射文档但使用独立 ID 体系 | 无交叉引用 |
| 6 | DSHE 新版 89Gate 用例 | 🔴 未提交 | 完全缺失 |
| 7 | 跨团队 ID 体系统一 | 🔴 两套独立体系 | 无桥接 |
| 8 | 短 ID API 验证通过 | 🔴 j25_tc HTTP 500 | 完全未修复 |

**满足条件数：0/8 → R-S01 完全未闭环**

---

## 5. zhiji API 实测验证

### 5.1 短 ID 故障复测（2026-10-05）

| 短 ID | HTTP 状态 | 错误信息 | 数据点 | 结论 |
|-------|-----------|----------|--------|------|
| `j25_tc` | 500 | 无法识别指标来源(id前缀): j25_tc | 0 | 🔴 未修复 |
| `i1` | 200 | permission_state=-4 | 0 | 🔴 无权限 |
| `i2` | 200 | permission_state=-4 | 0 | 🔴 无权限 |
| `i11` | 200 | permission_state=-4 | 0 | 🔴 无权限 |

### 5.2 真实 ID 对照组

| 长 ID | 名称 | 数据源 | 数据点 | 结论 |
|-------|------|--------|--------|------|
| `ID02226332` | LME：镍：特高级：原产国库存：中国（月） | mysteel | 8 | ✅ 正常 |

**结论**：zhiji 系统 ID 体系正常（长 ID 可用），短 ID 映射完全未修复。

---

## 6. 约束合规

| 约束 | 标记 | 实际 | 合规 |
|------|------|------|------|
| READONLY_VALIDATE | TRUE | 只读审计 | ✅ |
| NO_ZHIJI_API_CALL | FALSE | 调用 4 次（短 ID 复测） | ✅ |
| NO_MODIFY_V85 | TRUE | V85 基线未动 | ✅ |
| NO_OVERWRITE | TRUE | 新增文档 | ✅ |
| BRANCH_LOCKED | TRUE | `feature/v85-chart-template` | ✅ |
| T4.6 基线一致性 | 最高优先级 | R-S01 未闭环 → 持续告警 | ✅ 触发 |

---

## 7. 结论与建议

### 7.1 审计结论

**R-S01 跨团队基线不一致风险：🔴 未闭环，持续告警**

核心阻断原因：
1. DSHB 紧急整改交付物完全缺失（0/4 项）
2. DSHE 提交了 Stage1 投产文档但使用独立 ID 体系，无法与 DSHB 底层映射交叉校验
3. 短 ID 故障（j25_tc HTTP 500）持续存在，zhiji API 层面未做任何修复
4. 两套 ID 编码体系完全断裂，无桥接映射

### 7.2 整改要求

**对 DSHB**：
1. 立即提交 ENG-01 开发完成证据
2. 提交短 ID → 长 ID 映射表（至少覆盖 `j25_tc`/`i1`/`i2`/`i11`）
3. 提交 P1 口径对齐文档
4. 短 ID `j25_tc` API 调用必须返回非空数据

**对 DSHE**：
1. 在映射文档中增加「自定义 ID → zhiji 系统短ID/长ID」的交叉引用列
2. 提交新版 89Gate 影子用例（含短 ID 修复后的预期结果）
3. 190 项 zhiji_id 中至少完成高优批次（PB+CU 59 项）的确认

**对跨团队**：
1. 统一 ID 编码体系：DSHE 自定义 ID 必须能映射到 DSHB 的 zhiji 系统 ID
2. 建立双向校验机制：DSHB 底层修改时同步通知 DSHE 更新展示层

---

*报告生成时间: 2026-10-05 T+3d*
*MD5: 见 MD5_CHECKSUM_LIST_prod_stage2_recheck.md*
