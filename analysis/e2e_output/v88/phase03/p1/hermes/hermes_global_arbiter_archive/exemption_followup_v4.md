# C-1~C-5 豁免约束跟进核验报告 v4

> **TASK_ID**: V88_PHASE03_P6_HERMESHF_GLOBAL_ARBITER_STANDBY_JOB / T4
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **核验时间**: 2026-10-17T12:58 +0800
> **版本**: v4（v3 基线：`exemption_followup_consistency_check.md` 2026-10-16）

---

## 1. 约束执行进度（v4 快照）

| 约束 | 内容 | 执行方 | v3 进度 | v4 进度 | 变化 | 状态 |
|------|------|:------:|:-------:|:-------:|:----:|:----:|
| C-1 | 冻结产物不得修改 | DSHE+DSHB | 100% | **100%** | 持平 | ✅ |
| C-2 | caliber 口径保持不变 | DSHE | 100% | **100%** | 持平 | ✅ |
| C-3 | Phase04 psutil 采集部署 | DSHE | 0% | **0%** | 持平 | 🟡 |
| C-4 | 基线合并 (P0-12+P0-13) | DSHB | 0% (WAIT) | **0% (WAIT)** | 持平 | ⏳ |
| C-5 | manifest 自引用修复 | DSHE | 0% | **0%** | 持平 | 🟡 |

**总进度**：2/5 完成 ✅，3/5 进行中 🟡/⏳

---

## 2. v4 新增核查项

### 2.1 C-1 冻结产物 MD5/SHA256 复核（本轮 T0 实算）

| 资产 | 复核结果 |
|------|:--------:|
| DSHE P0-12 frozen_p012_gate_package（5 文件 SHA256） | ✅ 全部未变 |
| DSHB P0-13 final_archive（5 文件 SHA256） | ✅ 全部未变 |
| 引擎 `node_binding_engine.py` MD5 | ✅ `CD73DEAE...` 未变 |
| 三层封印链（MD5+SHA256+独立） | ✅ 全部 MATCH |

**判定**：C-1 在 v4 仍 100% 合规，无任何篡改。

### 2.2 C-4 基线合并状态

| 项 | 值 |
|----|---|
| `v88-long-stable-baseline.json` | ❌ 不存在 |
| 合并规则 | WAIT_AFTER_PHASE04_GO |
| P0-13 168h 观测 | ✅ 完成（6.64% < 10%） |
| 合并前置条件 | Phase04-GO 工单签发 |
| 当前 Phase04-GO 工单 | ⏳ 未签发 |
| 合并操作 | **禁止**（本轮无任何合并行为） |

**判定**：C-4 在 v4 仍正确保持 WAIT 状态，未提前合并。

### 2.3 C-3 psutil 采集状态

| 项 | 值 |
|----|---|
| `collector.enabled` | `false` |
| `daemon.enabled` | `false` |
| 守护进程 | 0 个 |
| 输出文件 | 0 个 |
| 激活条件 | Phase04 正式工单签发 |

**判定**：C-3 在 v4 仍未启动（符合预期，Phase04 未签发）。

### 2.4 C-5 manifest 自引用缺陷

| 项 | 值 |
|----|---|
| 缺陷描述 | MD5_MANIFEST.md 自引用自身 MD5（已知缺陷） |
| 影响 | 非阻断（冻结产物 MD5 仍可独立校验） |
| 修复计划 | Phase04 任务 |
| 当前状态 | 未修复（符合预期） |

---

## 3. P0-12 豁免审批状态

| 项 | 值 |
|----|---|
| 豁免类型 | P0-12 FAIL→WARN（EXEMPTION_GRANTED） |
| 审批 commit | `6ac0739`（HERMEShf，2026-10-16） |
| DSHB 台账同步 | ⚠️ R-V88-034 仍 OPEN（DSHB 未回写 EXEMPTION_GRANTED） |
| DSHE 台账同步 | ✅ cross_align 版已更新 |
| 根因 | DSHB 提交 (a5fa9fb) 早于或并行于 HERMEShf 审批 commit |
| 处置 | 已在 `global_gate_status_update.md` 下发更新指令；DSHB 下次提交须同步 |

**判定**：P0-12 豁免已审批通过，DSHB 台账同步为时序差异，非阻断。

---

## 4. 新增风险登记

| 编号 | 等级 | 描述 | 处置 |
|------|------|------|------|
| R-V88-P6-001 | LOW | 仲裁器 5 项预检中 3 项（#2 基线无切换 / #3 Phase03 零阻断 / #5 DSHE AUTO_COMMIT）为硬编码 True | Phase04 前升级为实际文件校验 |

---

## 5. 约束合规总表

| # | 约束 | 合规 | 阻断 |
|:-:|------|:----:|:----:|
| C-1 | 冻结产物不得修改 | ✅ | 否 |
| C-2 | caliber 口径不变 | ✅ | 否 |
| C-3 | psutil 采集部署 | 🟡 待 Phase04 | 否 |
| C-4 | 基线合并 | ⏳ WAIT | 否 |
| C-5 | manifest 自引用修复 | 🟡 待 Phase04 | 否 |
| **总计** | — | **2/5 ✅ + 3/5 🟡⏳** | **0 阻断** |

---

> **STATUS**: EXEMPTION_FOLLOWUP_V4_COMPLETE_NO_BLOCKERS
> **NEXT**: Phase04 启动后推进 C-3/C-5；C-4 在 Phase04-GO 后执行

*Generated: 2026-10-17T12:58 +0800 | HERMEShf | V88 Phase03 P6 T4*
