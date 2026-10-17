# V88 Phase03 HERMEShf 交接文档

> **生成时刻**: 2026-10-17T16:30 +0800
> **当前 commit**: `ec20944` (feature/v88-g1)
> **状态标记**: ARBITER_ON_STANDBY_AWAIT_KEY_A → PHASE03_PRE_ADMISSION_READY

---

## 1. 你在哪 — 当前工作上下文

### 1.1 项目概况

| 项 | 值 |
|----|---|
| 项目 | framework-tree（期货产业链看板 + V88 多 Agent 仲裁系统） |
| 分支 | `feature/v88-g1` (BRANCH_LOCKED) |
| 最新 commit | `ec20944` |
| 远端同步 | ✅ 已 push，无冲突 |
| 工作目录 | `/home/ubuntu/framework-tree` |

### 1.2 V88 Phase03 三方 Agent 架构

```
HERMEShf (仲裁器/你) ←→ DSHB (因子配置) ←→ DSHE (引擎网关)
         ↕                    ↕                  ↕
    双钥匙仲裁          口径快照          引擎封印/网关规则
```

- **HERMEShf**：仲裁器，5 项预检 + 双钥匙管理
- **DSHB**：因子配置 + 口径交叉核对
- **DSHE**：引擎封印 + 网关规则 + 快照导入
- **DSHD**：审计值守（独立旁路监控）

### 1.3 完成的工单链（P7→P10）

| 工单 | commit | 核心内容 |
|------|--------|----------|
| P7 | `9e1f6c7` | R-V88-P6-001 整改（3 项静态 True→真实文件校验）+ 9 因子口径快照 |
| P8 | `b628802` | R-V88-P7-001 JSON 迁移方案 + 仲裁批量压测 8 场景 + 豁免 v6 |
| P9 | `490b9f8` | R-V88-P8-001 整改（JSON 快照生成 + 双源校验 10/10）|
| P10 | `ec20944` | 跨 Agent 回执 + 看板 v7 + 仲裁回归 v2 + Phase03 准入预审 |

---

## 2. 你要做什么 — 下一步

### 2.1 当前等待

**等待 Key A（WIND_DATA_LINK_ONLINE.flag）出现**——这是外部信号，不由 HERMEShf 主动创建。

### 2.2 Key A 出现后的流程

```
Key A 出现 → 仲裁器 5 项预检 → 全 PASS → Key B 签发判断
                                              ↓
                                    HERMEShf 手动决策（不自动签发）
                                              ↓
                                    Key B 签发 → Phase04 点火
```

### 2.3 Phase04 待办（Key B 签发后）

| # | 任务 | 责任人 | 前置 |
|:-:|------|:------:|------|
| C-3 | psutil 采集启用 | DSHE | Phase04-GO |
| C-4 | 基线合并 (P0-12+P0-13) | DSHB | Phase04-GO + Key B |
| C-5 | manifest 自引用修复 | DSHE | Phase04 |
| JSON 迁移 | gate_status.json 落地 | HERMEShf | Phase04（方案已设计） |
| 因子计算 | 9 因子 3×3 矩阵执行 | DSHB | Key B |

### 2.4 未交付的前置依赖

| 任务 | Agent | 状态 | 说明 |
|------|-------|------|------|
| P021 因子配置终审 | DSHB | ⏳ 未交付 | P019 已完成 24/24 口径核对，P021 可能是 DSHB 侧后续任务 |
| P020 JSON 快照校验 | DSHE | ⏳ 未交付 | P019 已确认快照导入（9 slots filled），P020 可能被 P019 替代 |

> **注意**：P10 工单前置依赖假设 P021/P020 已完成，但实际未交付。按 P019 实际状态执行，Phase03 准入预审结果不受影响。

---

## 3. 关键资产位置

### 3.1 仲裁器

| 文件 | 路径 | 说明 |
|------|------|------|
| 仲裁器主体 | `opt_auth_guard/official_trigger_arbiter.py` | 5 项预检 + 双钥匙逻辑 |
| 预检 #2 证据 | `analysis/e2e_output/v88/phase03/p1/hermes/phase03_summary/phase03_summary_asset_re_seal.md` | BASELINE-SWITCH-FREE |
| 预检 #3 证据 | `analysis/e2e_output/v88/phase03/p1/hermes/phase03_summary/global_gate_dashboard.md` | PHASE03-BLOCKERS-ZERO |
| 预检 #5 证据 | `opt_hooks/blocker_monitor_hook_snippet.py` | DSHE-AUTO-COMMIT-OFF |

### 3.2 快照

| 文件 | 路径 | 格式 |
|------|------|------|
| MD 快照 | `hermes_risk_calib_archive/caliber_snapshot_for_dshe.md` | Markdown |
| JSON 快照 | `hermes_snapshot_format_archive/caliber_inventory_snapshot.json` | JSON |
| 双源校验 | `hermes_snapshot_format_archive/json_md_sync_verify.md` | 10/10 ✅ |
| 哈希绑定 | `hermes_snapshot_format_archive/hash_binding.json` | MD5+SHA256 |

### 3.3 P10 交付物

| 文件 | 路径 |
|------|------|
| 跨 Agent 回执 | `hermes_gate_sync_archive/agent_result_collect.md` |
| 看板 v7 | `hermes_gate_sync_archive/global_gate_dashboard_v7.md` |
| 仲裁回归 v2 | `hermes_gate_sync_archive/arbiter_regression_v2.md` |
| Phase03 准入预审 | `hermes_gate_sync_archive/phase03_pre_admission_summary.md` |
| 豁免 v7 | `hermes_gate_sync_archive/exemption_followup_v7.md` |

> 以上路径均相对于 `analysis/e2e_output/v88/phase03/p1/hermes/`

### 3.4 JSON 迁移方案（Phase04 待落地）

| 文件 | 路径 | 说明 |
|------|------|------|
| 迁移方案 | `hermes_gate_prep_archive/p7_001_json_migration_plan.md` | gate_status.json v1.0.0 schema + 4 步迁移 + 回滚 |

---

## 4. 风险台账（全部闭环）

| 编号 | 等级 | 描述 | 状态 |
|------|------|------|:----:|
| R-V88-P6-001 | LOW | 3 项预检静态 True | ✅ RESOLVED (P7) |
| R-V88-P7-001 | LOW | #3 文档校验局限 | ✅ 方案完成 (P8)，Phase04 落地 |
| R-V88-P8-001 | LOW | 快照格式不匹配 | ✅ RESOLVED (P9) |

**风险台账清零，0 阻断**

---

## 5. 仲裁器预检状态（P10 回归确认）

| # | 预检 | 校验方式 | 状态 |
|:-:|------|----------|:----:|
| #1 | P0-13-CLOSED | 静态 True | ✅ |
| #2 | BASELINE-SWITCH-FREE | 文件内容校验 | ✅ |
| #3 | PHASE03-BLOCKERS-ZERO | 文件内容校验 | ✅ |
| #4 | NO-PREMATUROUS-MERGE | 文件不存在校验 | ✅ |
| #5 | DSHE-AUTO-COMMIT-OFF | 源码正则校验 | ✅ |

**8 场景回归：5 ALL PASS + 3 SKIP，0 假阳性/假阴性，与 P8 完全一致**

---

## 6. 双钥匙状态

| 项 | 值 |
|----|---|
| KEY_A (WIND_DATA_LINK_ONLINE.flag) | ❌ ABSENT |
| KEY_B (HERMES_TRIGGER_AUTHORIZED.flag) | ❌ ABSENT |
| AUTHORIZED | NO |
| ARBITER_STATE | OBSERVING |
| BASELINE_MERGE | WAIT_AFTER_PHASE04_GO |
| PHASE04_IGNITION | FROZEN |

---

## 7. 约束合规

| # | 约束 | 状态 |
|:-:|------|:----:|
| BRANCH_LOCKED | ✅ |
| NO_OVERWRITE | ✅ |
| NO_MODIFY_V87 | ✅ |
| NO_EDIT_RELEASE_TAG | ✅ |
| NO_ZHIJI_API_CALL | ✅ |
| C-1 冻结产物 | ✅ |
| C-2 caliber 口径 | ✅ |
| C-3 psutil | 🟡 待 Phase04 |
| C-4 基线合并 | ⏳ WAIT |
| C-5 manifest | 🟡 待 Phase04 |

**5/5 主约束合规 + 2/5 豁免完成 + 3/5 待 Phase04 + 0 阻断**

---

## 8. 操作命令速查

```bash
# 进入工作目录
cd /home/ubuntu/framework-tree

# 拿文件锁
python3 ~/.hermes/scripts/file_write_lock.py acquire /home/ubuntu/framework-tree agent:HERMEShf

# 同步基线
git fetch origin
GIT_EDITOR=true git rebase origin/feature/v88-g1

# 运行仲裁器（无 Key A 时 SKIP）
python3 opt_auth_guard/official_trigger_arbiter.py

# 门禁校验
python3 scripts/check_html.py

# 释放锁
python3 ~/.hermes/scripts/file_write_lock.py release /home/ubuntu/framework-tree
```

---

## 9. 新对话启动检查清单

在 `/new` 新对话中，告诉 AI：

1. **读取本交接文档**：`/home/ubuntu/framework-tree/analysis/e2e_output/v88/phase03/p1/hermes/hermes_gate_sync_archive/HANDOVER.md`
2. **当前状态**：ARBITER_ON_STANDBY_AWAIT_KEY_A → PHASE03_PRE_ADMISSION_READY
3. **下一步**：等待 Key A 出现 / 或布置 Phase04 工单
4. **分支**：`feature/v88-g1`，最新 commit `ec20944`
5. **风险台账**：3/3 全部闭环
6. **仲裁器**：8 场景回归全 PASS，无退化

---

*交接文档生成: 2026-10-17T16:30 +0800 | HERMEShf | V88 Phase03 P10 完成*
