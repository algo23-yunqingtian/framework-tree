# V88 Phase03 跨 Agent 分工与依赖清单

> **TASK_ID**: V88_PHASE03_HERMESHF_TOP_LEVEL_PLAN_PREP
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1
> **BASELINE HEAD**: 7949949 | **生成时间**: 2026-10-15
> **用途**: DSHB（数据层）/ DSHE（可视化层）/ HERMEShf（审计层）三方 Phase03 工作边界、任务分解、依赖关系、交付物清单
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY

---

## 0. 一句话总结

**Phase03 三方分工按「DSHB 数据层 / DSHE 可视化层 / HERMEShf 审计层」清晰隔离，共 21 项子任务（DSHB 8 + DSHE 6 + HERMEShf 7），5 项跨 Agent 依赖全部显式定义消解方案，0 项冲突任务。** 目录隔离（`phase03/dshb/`、`phase03/dshe/`、`phase03/audit/`）+ 元数据 append-only 双保险，支持三方并行启动。

---

## 1. 三方职责边界总览

| 责任方 | 层 | 核心职责 | Phase03 目标覆盖 | 子任务数 |
|---|---|---|---|---|
| **DSHB** | 数据层 | 指标扩量、因子数据供给、灾备链路 | G1 主责 / G2 主责 / G3 主责 / G4 配合 | 8 |
| **DSHE** | 可视化层 | 渲染扩容、周报面板、灾备降级策略 | G1 配合 / G2 配合 / G3 配合 / G4 主责 | 6 |
| **HERMEShf** | 审计层 | 门禁复核、阈值设计、快照产出、最终验收 | G2 主责（阈值）/ 跨阶段审计 / P3 主控 | 7 |
| **合计** | — | — | 4 目标全覆盖 | **21** |

---

## 2. DSHB（数据层）任务分解

| 任务 ID | 任务 | 目标 | 阶段 | 交付物 | 前置依赖 |
|---|---|---|---|---|---|
| **DSHB-01** | 衍生指标算子库设计 | G1 | P0 | `dshb/operator_lib/design.md` | 无 |
| **DSHB-02** | 新指标接入方案（146→200+） | G1 | P0 | `dshb/expansion/new_indicator_plan.md` | DSHB-01 |
| **DSHB-03** | 灾备链路架构设计 + 切换时序协议 | G3 | P0 | `dshb/dr/architecture.md` | 无 |
| **DSHB-04** | DQA 规则扩展（适配 200+ 指标） | G1 | P1 | `dshb/dqa/rules_expanded.md` | DSHB-02 |
| **DSHB-05** | 扩量批次执行（146→180→200+）+ 长稳观测 | G1 | P1/P2 | `dshb/expansion/batch_report.md` | DSHB-04 |
| **DSHB-06** | 灾备切换仿真演练 | G3 | P1 | `dshb/dr/drill_sim_report.md` | DSHB-03 |
| **DSHB-07** | 灾备真实切换演练 + RPO 核验 | G3 | P2 | `dshb/dr/drill_real_report.md` | DSHB-06 |
| **DSHB-08** | IC/IR 采集链路增强 + 6 项备选方案长期有效性监控 | G2 | P1~P3 | `dshb/icir/enhanced_monitor.md` | Phase02 基线 |

**DSHB 阶段产出节奏**：P0（3 项设计）→ P1（3 项执行）→ P2（2 项长稳）

---

## 3. DSHE（可视化层）任务分解

| 任务 ID | 任务 | 目标 | 阶段 | 交付物 | 前置依赖 |
|---|---|---|---|---|---|
| **DSHE-01** | 新指标图表绑定 + 口径校验扩展 | G1 | P0 | `dshe/binding/new_chart_binding.md` | DSHB-02 |
| **DSHE-02** | 周报自动渲染面板迭代方案 | G4 | P0 | `dshe/weekly_panel/iteration_plan.md` | 无 |
| **DSHE-03** | 并发扩容架构设计（200→500） | G4 | P0 | `dshe/concurrency/architecture.md` | 无 |
| **DSHE-04** | 500 并发压测 + 周报面板迭代实现 | G4 | P1/P2 | `dshe/concurrency/load_test_report.md` | DSHE-02/03 + DSHB-05 |
| **DSHE-05** | 灾备期间降级渲染策略实现 | G3 | P1 | `dshe/dr/fallback_strategy.md` | DSHB-03 |
| **DSHE-06** | 因子监控图表渲染 + 并发稳定性长稳观测 | G2/G4 | P2 | `dshe/monitor/factor_panel_report.md` | DSHB-08 |

**DSHE 阶段产出节奏**：P0（3 项设计）→ P1（2 项实现）→ P2（1 项长稳）

---

## 4. HERMEShf（审计层）任务分解

| 任务 ID | 任务 | 目标 | 阶段 | 交付物 | 前置依赖 |
|---|---|---|---|---|---|
| **HERMES-01** | Phase03 顶层规划 + 门禁矩阵 + 分工矩阵 | — | 计划期 | `phase03/plan/`（3 份，本工单） | Phase02 ACCEPTED |
| **HERMES-02** | 新增因子监控阈值设计 + 告警规则 | G2 | P0 | `audit/factor_threshold_plan.md` | Phase02 IC/IR 基线 |
| **HERMES-03** | MD5 行尾规范化校验脚本 | R-V88-009 | P0 | `audit/scripts/md5_normalize.py` | Phase02 CRLF 根因 |
| **HERMES-04** | P0 接口契约评审 + 依赖矩阵确认 | — | P0 | `audit/p0_contract_review.md` | DSHB/DSHE P0 产出 |
| **HERMES-05** | P1 仿真正门门禁复核（独立复跑） | G1~G4 | P1 | `audit/p1_simulation_audit.md` | DSHB/DSHE P1 产出 |
| **HERMES-06** | P2 长稳审计 + 告警噪声率调参 | G2 | P2 | `audit/p2_longstability_audit.md` | DSHB/DSHE P2 产出 |
| **HERMES-07** | P3 三方联合验收主控 + Phase03_ACCEPT 判定 | — | P3 | `audit/v88_phase03_final_acceptance_report.md` | 三方 P2 完成 |

**HERMEShf 阶段产出节奏**：计划期（1 项）→ P0（3 项）→ P1（1 项）→ P2（1 项）→ P3（1 项）

---

## 5. 跨 Agent 依赖关系（5 项）

| 依赖 ID | 依赖关系 | 类型 | 风险等级 | 消解方案 | 检查时机 |
|---|---|---|---|---|---|
| **DEP-1** | G1 扩量（DSHB-05）→ G4 并发扩容（DSHE-04） | 强依赖（串行） | P2 | P1 阶段先扩量后并发压测；扩量完成标记作为 DSHE-04 进入条件 | P1 中期 |
| **DEP-2** | G2 IC/IR 继承 → Phase02 基线 `ic_ir_baseline_v1` | 强依赖（已完成） | INFO | 基线冻结只读，Phase03 只引用不修改 | P0 |
| **DEP-3** | G3 灾备切换（DSHB-07）→ DSHE 降级策略（DSHE-05） | 强依赖 | P1 | 切换时序协议中 T-30min 预热缓存 + T+5min 切回通知 | P1 仿真 |
| **DEP-4** | G2 因子 CRIT 告警 → G1 扩量暂停 | 条件依赖 | P1 | 扩量批次间隔 ≥3 天，留出告警响应窗口 | P1/P2 每批次 |
| **DEP-5** | P3 金丝雀 → DSHB/DSHE 双方 P2 完成 | 强依赖 | P1 | P3 进入条件要求双方 P2 完成标记，单方未 READY 不启动 | P3 入口 |

### 5.1 依赖链路图

```
Phase02 ACCEPTED (7949949)
        │
        ▼
  ┌─────────────────────────────────────────┐
  │  P0 原型（并行，3 天）                     │
  │  DSHB-01/02/03  DSHE-01/02/03  HERMES-02/03/04 │
  └────────────────────┬────────────────────┘
                       │ P0_CONTRACT_FROZEN
                       ▼
  ┌─────────────────────────────────────────┐
  │  P1 仿真（串行点：DEP-1）                  │
  │  DSHB-04/05 ──DEP-1──▶ DSHE-04          │
  │  DSHB-06 ──DEP-3──▶ DSHE-05   HERMES-05 │
  └────────────────────┬────────────────────┘
                       │ P1_SIMULATION_PASS
                       ▼
  ┌─────────────────────────────────────────┐
  │  P2 长稳（7 天，DEP-4 批次窗口）           │
  │  DSHB-05/07/08  DSHE-04/06  HERMES-06   │
  └────────────────────┬────────────────────┘
                       │ P2_LONGSTABILITY_PASS (DEP-5)
                       ▼
  ┌─────────────────────────────────────────┐
  │  P3 金丝雀（4 天，HERMES 主控）           │
  │  三方联合验收 ──▶ PHASE03_ACCEPT         │
  └─────────────────────────────────────────┘
```

---

## 6. 冲突任务检查（结论：无冲突）

### 6.1 目录隔离检查

| 目录 | 写入方 | 阶段 | 冲突风险 |
|---|---|---|---|
| `phase03/dshb/` | DSHB | P0~P3 | 无（独占） |
| `phase03/dshe/` | DSHE | P0~P3 | 无（独占） |
| `phase03/audit/` | HERMEShf | P0~P3 | 无（独占） |
| `phase03/plan/` | HERMEShf（仅计划期） | 计划期 | 无（一次性） |
| `STATUS.md` | 三方 | 全程 | 低（append-only，字节级冲突范式） |
| `JOB_READY.flag` | 三方 | 全程 | 低（append-only） |
| `MD5_MANIFEST` | 三方 | 全程 | 低（append-only） |

### 6.2 并行任务时序检查

| 检查项 | 结果 |
|---|---|
| P0 三方并行 | ✅ 无依赖，可同时启动 |
| P1 DEP-1 串行点 | ✅ 已定义顺序（扩量→并发） |
| P1 DEP-3 串行点 | ✅ 已定义时序协议 |
| P2 DEP-4 条件依赖 | ✅ 3 天批次缓冲窗 |
| P3 DEP-5 入口条件 | ✅ 双方 P2 完成才启动 |
| **冲突任务数** | **0** |

### 6.3 共享资源检查

| 资源 | 处理方式 |
|---|---|
| Phase02 归档资产 | **只读**，禁止修改（NO_OVERWRITE） |
| Phase02 IC/IR 基线 | **冻结** 为 `ic_ir_baseline_v1`，只读引用 |
| CPU FUSE 2.0% | **不修改**，并发扩容须在此阈值内验证 |
| 知几 API | **禁用**（NO_ZHIJI_API_CALL），仿真用离线数据 |
| 文件锁 | 同服务器写元数据前 `acquire`，跨服务器走 git rebase |

---

## 7. 三方交付物清单汇总

| # | 责任方 | 交付物 | 阶段 |
|---|---|---|---|
| 1 | HERMEShf | `plan/v88_phase03_top_level_plan.md` | 计划期 ✅ 本工单 |
| 2 | HERMEShf | `plan/v88_phase03_gate_matrix.md` | 计划期 ✅ 本工单 |
| 3 | HERMEShf | `plan/v88_phase03_agent_work_breakdown.md` | 计划期 ✅ 本工单 |
| 4 | DSHB | `dshb/operator_lib/design.md` | P0 |
| 5 | DSHB | `dshb/expansion/new_indicator_plan.md` | P0 |
| 6 | DSHB | `dshb/dr/architecture.md` | P0 |
| 7 | DSHE | `dshe/binding/new_chart_binding.md` | P0 |
| 8 | DSHE | `dshe/weekly_panel/iteration_plan.md` | P0 |
| 9 | DSHE | `dshe/concurrency/architecture.md` | P0 |
| 10 | HERMEShf | `audit/factor_threshold_plan.md` | P0 |
| 11 | HERMEShf | `audit/scripts/md5_normalize.py` | P0 |
| 12 | HERMEShf | `audit/p0_contract_review.md` | P0 |
| 13 | DSHB | `dshb/dqa/rules_expanded.md` | P1 |
| 14 | DSHB | `dshb/dr/drill_sim_report.md` | P1 |
| 15 | DSHB | `dshb/icir/enhanced_monitor.md` | P1 |
| 16 | DSHE | `dshe/dr/fallback_strategy.md` | P1 |
| 17 | DSHE | `dshe/concurrency/load_test_report.md` | P1/P2 |
| 18 | HERMEShf | `audit/p1_simulation_audit.md` | P1 |
| 19 | DSHB | `dshb/expansion/batch_report.md` | P2 |
| 20 | DSHB | `dshb/dr/drill_real_report.md` | P2 |
| 21 | DSHE | `dshe/monitor/factor_panel_report.md` | P2 |
| 22 | HERMEShf | `audit/p2_longstability_audit.md` | P2 |
| 23 | HERMEShf | `audit/v88_phase03_final_acceptance_report.md` | P3 |

**合计 23 份交付物**（本工单 3 份 + P0 6 份 + P1 4 份 + P2 4 份 + P3 1 份）

---

## 8. 启动条件与下一步

### 8.1 三方启动条件

| 责任方 | 启动条件 | 当前状态 |
|---|---|---|
| DSHB | Phase03_PLAN_PREP_COMPLETE=TRUE + 用户批准 | ✅ 本工单完成，待用户批准 |
| DSHE | Phase03_PLAN_PREP_COMPLETE=TRUE + 用户批准 | ✅ 本工单完成，待用户批准 |
| HERMEShf | 本工单完成 | ✅ 已完成 |

### 8.2 下一步动作

1. **用户拍板**：确认 Phase03 四目标优先级 + 19 天工期 → 批准 DSHB/DSHE 进入 P0
2. **DSHB**：启动 DSHB-01/02/03（算子库 + 扩量方案 + 灾备架构）
3. **DSHE**：启动 DSHE-01/02/03（图表绑定 + 周报面板 + 并发扩容方案）
4. **HERMEShf**：启动 HERMES-02/03/04（阈值设计 + MD5 脚本 + 契约评审）
5. **对齐窗口**：P0 阶段结束（D3）三方对齐评审 → `P0_CONTRACT_FROZEN`

---

*Document Generated: 2026-10-15 UTC+8*
*Generated by: HERMEShf Agent*
*Branch: feature/v88-g1 (BASELINE 7949949)*
*Status: V88_PHASE03_AGENT_WORK_BREAKDOWN_READY*
*Note: 本文件为新建文件，append-only 原则下未修改任何既有资产*
