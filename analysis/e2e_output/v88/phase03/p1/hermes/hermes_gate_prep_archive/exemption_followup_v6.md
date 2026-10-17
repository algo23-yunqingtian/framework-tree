# C-1~C-5 豁免约束跟进核验报告 v6

> **TASK_ID**: V88_PHASE03_P8_HERMESHF_P7_GATE_MONITOR_UPGRADE_PREP_JOB / T2
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **核验时间**: 2026-10-17T14:55 +0800
> **版本**: v6（v5 基线：`hermes_risk_calib_archive/exemption_followup_v5.md`）

---

## 1. 约束执行进度（v6 快照）

| 约束 | 内容 | 执行方 | v5 进度 | v6 进度 | 变化 | 状态 |
|------|------|:------:|:-------:|:-------:|:----:|:----:|
| C-1 | 冻结产物不得修改 | DSHE+DSHB | 100% | **100%** | 持平 | ✅ |
| C-2 | caliber 口径保持不变 | DSHE | 100% | **100%** | 持平 | ✅ |
| C-3 | Phase04 psutil 采集部署 | DSHE | 0% | **0%** | 持平 | 🟡 |
| C-4 | 基线合并 (P0-12+P0-13) | DSHB | 0% (WAIT) | **0% (WAIT)** | 持平 | ⏳ |
| C-5 | manifest 自引用修复 | DSHE | 0% | **0%** | 持平 | 🟡 |

**总进度**：2/5 完成 ✅，3/5 进行中 🟡/⏳，0 阻断

---

## 2. v6 细化：3 项 🟡 待办卡点详情

### 2.1 C-3 Phase04 psutil 采集部署

| 维度 | 详情 |
|------|------|
| **卡点** | psutil collector/daemon 当前 `enabled=false`，需 Phase04 启动后激活 |
| **责任人** | DSHE |
| **前置依赖** | Phase04-GO 工单签发 + Key A 出现 + Key B 签发 |
| **预估交付条件** | Phase04 工单启动后，DSHE 执行 psutil 启用 + daemon 部署 + 3 轮稳定性验证 |
| **当前状态** | `psutil_lock_recheck_v3.md` 确认 enabled=false, daemon=false, 0 进程, 0 输出 |
| **依赖 DSHB** | 否（DSHE 独立部署） |
| **依赖 DSHE** | 自身 |
| **依赖 HERMEShf** | Phase04 工单签发 |

### 2.2 C-4 基线合并 (P0-12+P0-13)

| 维度 | 详情 |
|------|------|
| **卡点** | `v88-long-stable-baseline.json` 未创建，基线合并 WAIT |
| **责任人** | DSHB |
| **前置依赖** | Phase04-GO 工单签发（合并规则: WAIT_AFTER_PHASE04_GO） |
| **预估交付条件** | Phase04-GO 后，DSHB 执行 P0-12+P0-13 基线合并 → 生成 `v88-long-stable-baseline.json` |
| **当前状态** | P0-13 168h 观测完成（6.64% < 10%），合并条件满足但未执行 |
| **依赖 DSHB** | 自身 |
| **依赖 DSHE** | 否 |
| **依赖 HERMEShf** | Phase04 工单签发 + Key B 签发 |

### 2.3 C-5 manifest 自引用修复

| 维度 | 详情 |
|------|------|
| **卡点** | `MD5_MANIFEST.md` 自引用自身 MD5（已知缺陷，非阻断） |
| **责任人** | DSHE |
| **前置依赖** | Phase04 启动（缺陷修复安排在 Phase04 任务中） |
| **预估交付条件** | Phase04 中，DSHE 修改 manifest 生成逻辑，移除自引用循环 |
| **当前状态** | 缺陷存在但非阻断（冻结产物 MD5 仍可独立校验） |
| **依赖 DSHB** | 否 |
| **依赖 DSHE** | 自身 |
| **依赖 HERMEShf** | Phase04 工单签发 |

---

## 3. 依赖关系图

```
Phase04-GO 工单签发 (HERMEShf)
  ├── Key A 出现 (外部) → 5 项预检 → Key B 签发 (HERMEShf)
  │     ├── C-3: DSHE 启用 psutil 采集
  │     ├── C-4: DSHB 执行基线合并
  │     └── C-5: DSHE 修复 manifest 自引用
  └── Phase04 正式启动
        ├── 因子计算激活 (DSHB)
        ├── 网关规则升级 (DSHE)
        └── R-V88-P7-001 JSON 迁移落地 (HERMEShf)
```

**关键路径**：Phase04-GO 工单签发 → Key A → Key B → C-3/C-4/C-5 并行推进

---

## 4. 风险台账（v6 更新）

| 编号 | 等级 | 描述 | v5 状态 | v6 状态 | 变化 |
|------|------|------|:-------:|:-------:|:----:|
| R-V88-P6-001 | LOW | 3 项预检静态 True | ✅ RESOLVED | ✅ RESOLVED | 持平 |
| R-V88-P7-001 | LOW | #3 文档校验局限 | 🟡 待 Phase04 | ✅ **方案完成** | 进展 |
| R-V88-P8-001 | LOW | 快照分发格式不匹配 | — | 🟡 新登记 | 新增 |

### 4.1 R-V88-P8-001 新增

| 项 | 值 |
|----|---|
| 编号 | R-V88-P8-001 |
| 等级 | LOW |
| 描述 | HERMEShf P7 下发 `caliber_snapshot_for_dshe.md`（Markdown 格式），但 DSHE P018 的导入通道期望 `caliber_inventory_snapshot.json`（JSON 格式），格式不匹配 |
| 影响 | DSHE 尚未实际导入快照（仅预留了通道模板） |
| 处置 | Phase04 前 HERMEShf 补充 JSON 格式快照，或在 DSHE 导入逻辑中增加 Markdown 解析 |
| 阻断性 | 非阻断（DSHB P019 已用现有口径源完成 24/24 交叉核对） |

---

## 5. 三方就绪状态

| Agent | 最新任务 | 状态 | 就绪标记 |
|-------|---------|------|----------|
| HERMEShf | P8 门禁看板升级准备 | 进行中 | ARBITER_ON_STANDBY_AWAIT_KEY_A |
| DSHB | P020 前置预检 | 进行中 | FACTOR_STANDBY_AWAIT_DUAL_KEYS |
| DSHE | P018 门禁清理 | ✅ 完成 | GATE_ON_WATCH_AWAIT_DUAL_KEYS |

---

## 6. 基线合并状态（不变）

| 项 | 值 |
|----|---|
| `v88-long-stable-baseline.json` | ❌ 不存在 |
| 合并规则 | WAIT_AFTER_PHASE04_GO |
| 合并操作 | **禁止**（本轮无任何合并行为） |

---

## 7. 约束合规总表

| # | 约束 | 合规 | 阻断 |
|:-:|------|:----:|:----:|
| C-1 | 冻结产物不得修改 | ✅ | 否 |
| C-2 | caliber 口径不变 | ✅ | 否 |
| C-3 | psutil 采集部署 | 🟡 待 Phase04 | 否 |
| C-4 | 基线合并 | ⏳ WAIT | 否 |
| C-5 | manifest 自引用修复 | 🟡 待 Phase04 | 否 |
| **总计** | — | **2/5 ✅ + 3/5 🟡⏳** | **0 阻断** |

---

> **STATUS**: EXEMPTION_FOLLOWUP_V6_COMPLETE_3_YELLOW_DETAILED
> **NEXT**: Phase04 启动后并行推进 C-3/C-4/C-5

*Generated: 2026-10-17T14:55 +0800 | HERMEShf | V88 Phase03 P8 T2*
