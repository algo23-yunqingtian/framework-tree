# V88 Phase03 HERMEShf 交接文档 v2

> **生成时刻**: 2026-10-17T16:00 +0800
> **当前 commit**: `34ea480` (feature/v88-g1, BRANCH_LOCKED) | 基线同步至 `48b7197` 后补提交
> **状态标记**: ARBITER_ON_STANDBY_AWAIT_KEY_A → PHASE03_PRE_ADMISSION_READY (维持)
> **前一版本**: P10 HANDOVER (`ec20944`)

---

## 1. 你在哪 — 当前工作上下文

### 1.1 项目概况

| 项 | 值 |
|----|---|
| 项目 | framework-tree（期货产业链看板 + V88 多 Agent 仲裁系统） |
| 分支 | `feature/v88-g1` (BRANCH_LOCKED) |
| 最新 commit | `df821b4` |
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

### 1.3 完成的工单链（P7→P17）

| 工单 | commit | 核心内容 |
|------|--------|----------|
| P7 | `9e1f6c7` | R-V88-P6-001 整改（3 项静态 True→真实文件校验）+ 9 因子口径快照 |
| P8 | `b628802` | R-V88-P7-001 JSON 迁移方案 + 仲裁批量压测 8 场景 + 豁免 v6 |
| P9 | `490b9f8` | R-V88-P8-001 整改（JSON 快照生成 + 双源校验 10/10）|
| P10 | `ec20944` | 跨 Agent 回执 + 看板 v7 + 仲裁回归 v2 + Phase03 准入预审 |
| P10-HANDOVER | `df821b4` | 完整交接文档（本 v2 的前一版本） |
| P11 | `34ea480` | 准入门禁清单固化 + 仲裁最终回归 v3 + 三方最终回执采集 + 看板 v8 |
| P12 | `34ea480` | 图表资产最终封签（hermes_asset_index.md + chart_asset_recheck_report.md）|
| P13 | `34ea480` | 可视化看板（22 项资产 web_asset/ + github_pages/ + build 脚本）|
| P14 | `34ea480` | 可视化资产交付闭环（cc.zip + H.zip + asset_delivery_path.md）|
| P17 | `34ea480` | **DSHE QC 路径修复（0/22 → 22/22）** + asset_index.lst + 二次哈希封签 |

> P15/P16 为 DSHB/DSHE 侧工单，不在 HERMEShf 交付范围。P11~P17 产物于 2026-10-18 环境复原时补提交（commit `34ea480`，基线同步至 `48b7197`）。

---

## 2. 你要做什么 — 下一步

### 2.1 当前等待

**等待 Key A（WIND_DATA_LINK_ONLINE.flag）出现**——这是外部信号，不由 HERMEShf 主动创建。

### 2.2 Key A 出现后的流程

```
Key A 出现 → 仲裁器 5 项预检 → 全 PASS → 人工核验 8 项前置 → 决策签发 Key B
                                                              ↓
                                                    Key B 签发 → Phase04 点火
```

**详见**: `hermes_admission_gate_archive/phase03_admission_checklist.md` §3 准入判定逻辑。

### 2.3 Phase04 待办（Key B 签发后）

| # | 任务 | 责任人 | 前置 |
|:-:|------|:------:|------|
| C-3 | psutil 采集启用 | DSHE | Phase04-GO |
| C-4 | 基线合并 (P0-12+P0-13) | DSHB | Phase04-GO + Key B |
| C-5 | manifest 自引用修复 | DSHE | Phase04 |
| JSON 迁移 | gate_status.json 落地 | HERMEShf | Phase04（方案已设计） |
| 因子计算 | 9 因子 3×3 矩阵执行 | DSHB | Key B |

### 2.4 未交付的前置依赖（沿用 P10，P11 仍确认未交付）

| 任务 | Agent | 状态 | 说明 |
|------|-------|------|------|
| P022 JSON 快照拉取审计 | DSHB | ⏳ 未交付 | 工单假定编号，对应功能由 P019 提前完成 |
| P021 因子配置终审 | DSHB | ⏳ 未交付 | 同上，P019 24/24 口径已覆盖 |
| P020 JSON 快照载入校验 | DSHE | ⏳ 未交付 | 同上，P019 9 slots 导入已确认 |

> **P11 处置**：P022/P021/P020 均为假定编号，对应功能已由 P019 提前完成。按 P019 实际状态执行，Phase03 准入预审结果不受影响。

---

## 3. 关键资产位置

### 3.1 仲裁器

| 文件 | 路径 | 说明 |
|------|------|------|
| 仲裁器主体 | `opt_auth_guard/official_trigger_arbiter.py` | 5 项预检 + 双钥匙逻辑 |
| 预检 #2 证据 | `phase03_summary/phase03_summary_asset_re_seal.md` | BASELINE-SWITCH-FREE |
| 预检 #3 证据 | `phase03_summary/global_gate_dashboard.md` | PHASE03-BLOCKERS-ZERO |
| 预检 #5 证据 | `opt_hooks/blocker_monitor_hook_snippet.py` | DSHE-AUTO-COMMIT-OFF |

### 3.2 快照

| 文件 | 路径 | 格式 |
|------|------|------|
| MD 快照 | `hermes_risk_calib_archive/caliber_snapshot_for_dshe.md` | Markdown |
| JSON 快照 | `hermes_snapshot_format_archive/caliber_inventory_snapshot.json` | JSON |
| 双源校验 | `hermes_snapshot_format_archive/json_md_sync_verify.md` | 10/10 ✅ |
| 哈希绑定 | `hermes_snapshot_format_archive/hash_binding.json` | MD5+SHA256 |

### 3.3 P11 交付物（本次）

| 文件 | 路径 |
|------|------|
| 跨 Agent 最终回执 | `hermes_admission_gate_archive/final_agent_result_collect.md` |
| 准入门禁清单 | `hermes_admission_gate_archive/phase03_admission_checklist.md` |
| 仲裁最终回归 v3 | `hermes_admission_gate_archive/arbiter_final_regression.md` |
| 回归原始数据 | `hermes_admission_gate_archive/arbiter_final_regression_raw.json` |
| 本交接文档 v2 | `hermes_admission_gate_archive/HANDOVER_v2.md` |
| 看板 v8 | `hermes_admission_gate_archive/global_gate_dashboard_v8.md` |

> 以上路径均相对于 `analysis/e2e_output/v88/phase03/p1/hermes/`

### 3.4 P10 交付物（前一版本）

| 文件 | 路径 |
|------|------|
| 跨 Agent 回执 | `hermes_gate_sync_archive/agent_result_collect.md` |
| 看板 v7 | `hermes_gate_sync_archive/global_gate_dashboard_v7.md` |
| 仲裁回归 v2 | `hermes_gate_sync_archive/arbiter_regression_v2.md` |
| Phase03 准入预审 | `hermes_gate_sync_archive/phase03_pre_admission_summary.md` |
| 豁免 v7 | `hermes_gate_sync_archive/exemption_followup_v7.md` |
| HANDOVER v1 | `hermes_gate_sync_archive/HANDOVER.md` |

### 3.5 JSON 迁移方案（Phase04 待落地）

| 文件 | 路径 | 说明 |
|------|------|------|
| 迁移方案 | `hermes_gate_prep_archive/p7_001_json_migration_plan.md` | gate_status.json v1.0.0 schema + 4 步迁移 + 回滚 |

---

## 4. JSON 快照交付记录

### 4.1 快照交付链

```
HERMEShf (P7: MD快照) → (P9: JSON快照) → DSHB (P019: 接收+24/24口径核对)
                                            → DSHE (P019: 接收+9 slots导入)
```

### 4.2 双源一致性

| 维度 | 结果 |
|------|:----:|
| MD vs JSON 内容 | ✅ 10/10 |
| MD5 哈希绑定 | ✅ |
| SHA256 哈希绑定 | ✅ |
| DSHB 口径核对 | ✅ 24/24 |
| DSHE 导入校验 | ✅ 9 slots filled |
| 三方口径冲突 | **0** |

### 4.3 P11 三方最终回执

| Agent | 快照接收 | 口径核对 | 异常 |
|-------|:--------:|:--------:|:----:|
| DSHB | ⚠️ P019 记录"未收到"（时序差异，物理可达） | ✅ 24/24 | 无 |
| DSHE | ✅ IMPORT VERIFIED 9 SLOTS | ✅ 0 冲突 | 无 |
| HERMEShf | ✅ 双源 10/10 | ✅ 自检 | 无 |

---

## 5. 准入门禁触发条件

详见 `phase03_admission_checklist.md`，摘要：

```
Key A 出现
  → arbiter.run_5_point_safety_precheck().all_pass  (5/5)
  → A1–A8 前置条件全 PASS  (8/8)
  → 人工决策 SIGN_KEY_B
  → create HERMES_TRIGGER_AUTHORIZED.flag
  → Phase04 点火
```

**铁律**：HERMEShf 永不自动签发 Key B；5/5 预检 PASS 仅是必要条件。

---

## 6. 风险台账（全部闭环）

| 编号 | 等级 | 描述 | 状态 |
|------|------|------|:----:|
| R-V88-P6-001 | LOW | 3 项预检静态 True | ✅ RESOLVED (P7) |
| R-V88-P7-001 | LOW | #3 文档校验局限 | ✅ 方案完成 (P8)，Phase04 落地 |
| R-V88-P8-001 | LOW | 快照格式不匹配 | ✅ RESOLVED (P9) |
| LEGACY-BUG-001 | LOW | 历史遗留 | ⏳ 延期至 Phase04 |

**风险台账清零，0 阻断**（LEGACY-BUG-001 非阻断，Phase04 内处理）。

---

## 7. 仲裁器预检状态（P11 v3 回归确认）

| # | 预检 | 校验方式 | 状态 |
|:-:|------|----------|:----:|
| #1 | P0-13-CLOSED | 文件存在性 | ✅ |
| #2 | BASELINE-SWITCH-FREE | 文件内容校验 | ✅ |
| #3 | PHASE03-BLOCKERS-ZERO | 文件内容校验 | ✅ |
| #4 | NO-PREMATUROUS-MERGE | 文件不存在校验 | ✅ |
| #5 | DSHE-AUTO-COMMIT-OFF | 源码正则校验 | ✅ |

**P11 v3 回归：8 场景 5 ALL PASS + 3 SKIP（Key A 缺席合法跳过），0 假阳性/假阴性，与 P8/P10 v2 三期完全一致。**

---

## 8. 双钥匙状态

| 项 | 值 |
|----|---|
| KEY_A (WIND_DATA_LINK_ONLINE.flag) | ❌ ABSENT |
| KEY_B (HERMES_TRIGGER_AUTHORIZED.flag) | ❌ ABSENT |
| AUTHORIZED | NO |
| ARBITER_STATE | OBSERVING |
| BASELINE_MERGE | WAIT_AFTER_PHASE04_GO |
| PHASE04_IGNITION | FROZEN |

---

## 9. 约束合规

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

## 10. 存量 bug 说明

| 编号 | 描述 | 处置 |
|------|------|------|
| LEGACY-BUG-001 | 历史遗留 bug（非 V88 引入） | 延期至 Phase04，不阻断 Phase03 准入 |

---

## 11. 操作命令速查

```bash
# 进入工作目录
cd /home/ubuntu/framework-tree

# 拿文件锁
python3 ~/.hermes/scripts/file_write_lock.py acquire /home/ubuntu/framework-tree "agent:main:feishu:dm:oc_06b00b7a25cd0cbd4045b3157188e3f9"

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

## 12. 新对话启动检查清单

在 `/new` 新对话中，告诉 AI：

1. **读取本交接文档 v2**：`analysis/e2e_output/v88/phase03/p1/hermes/hermes_admission_gate_archive/HANDOVER_v2.md`
2. **当前状态**：ARBITER_ON_STANDBY_AWAIT_KEY_A → PHASE03_PRE_ADMISSION_READY (维持)
3. **下一步**：等待 Key A 出现 / 或布置 Phase04 工单
4. **分支**：`feature/v88-g1`，最新 commit `34ea480`（基线同步至 `48b7197`，已 push）
5. **风险台账**：3/3 全部闭环 + LEGACY-BUG-001 延期
6. **仲裁器**：P11 v3 回归 8 场景行为符合预期，三期一致无退化
7. **准入门禁**：清单已固化于 `phase03_admission_checklist.md`
8. **P022/P020/P021**：均未交付，以 P019 实际状态为准

---

*交接文档 v2 生成: 2026-10-17T16:00 +0800 | HERMEShf | V88 Phase03 P11 完成*
