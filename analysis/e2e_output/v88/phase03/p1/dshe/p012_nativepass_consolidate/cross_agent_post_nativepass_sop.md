# 跨 Agent 协同操作 SOP：P0-12 原生 PASS 后三方分工

> **TASK_ID**: V88_PHASE03_P1_DSHE_P012_NATIVE_PASS_CONSOLIDATE_AND_SYNC_JOB / T4
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **编写时间**: 2026-10-16T20:50 UTC+8
> **替代文档**: `cross_align_ARCHIVED/cross_agent_exemption_sop.md` (已废弃)
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL

---

## 1. SOP 范围

本 SOP 定义 P0-12 门禁**原生 PASS** 之后的三方（DSHE / DSHB / HERMEShf）协同流程。

**适用场景**：P0-12 原生 PASS (cpu_peak_pct=0.0654% ≤ 1.75%)，无需豁免审批。
**不适用**：豁免审批路径（已废弃，见 `cross_align_ARCHIVED/`）。

---

## 2. 前置条件

| # | 条件 | 状态 | 验证 |
|:-:|------|:----:|------|
| 1 | P0-12 三重修正完成 | ✅ | commit 55458b6 |
| 2 | cpu_peak_pct ≤ 1.75% | ✅ | 0.0654% |
| 3 | R3 E2E 8/8 PASS | ✅ | 原生 PASS 固化 |
| 4 | 4 轮独立验证可复现 | ✅ | 0.04–0.12% 区间 |
| 5 | frozen 包 v1.4.0 只读锁定 | ✅ | MD5 快照已保存 |
| 6 | R-V88-034 = CLOSED | ✅ | 风险台账已更新 |
| 7 | DSHB 台账同步补丁已输出 | ✅ | dshb_risklist_patch.md |

---

## 3. 三方协同流程

```
                    HERMEShf blocker_monitor cron (每30min)
                              │
                              ▼
                    ┌─────────────────────┐
                    │  自动触发 P0-12 门禁  │
                    │  官方核验复测         │
                    └──────────┬──────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
              ✅ PASS                  ❌ FAIL
                   │                       │
                   ▼                       ▼
         ┌─────────────────┐    ┌──────────────────────┐
         │ 分支 A: PASS     │    │ 分支 B: FAIL          │
         │ Phase03→Phase04  │    │ DSHE 可复现性排查      │
         └────────┬────────┘    └──────────┬───────────┘
                  │                         │
                  ▼                         ▼
         DSHE + DSHB 协同         DSHE 打开 debug 日志
         Phase04 bootstrap        定位根因，不回退豁免
```

---

## 4. 分支 A：HERMEShf 官方门禁 P0-12 ✅ PASS

### 4.1 触发条件

HERMEShf `blocker_monitor` cron 自动拉取执行 P0-12 门禁复测，判定 `PASS`。

### 4.2 DSHE 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| A-DSHE-1 | 确认 R-V88-034 状态 = CLOSED | P1 | 0.5h | 无 |
| A-DSHE-2 | 更新 STATUS.md 标记 `P0_12_GATE=NATIVE_PASS` | P1 | 0.5h | A-DSHE-1 |
| A-DSHE-3 | Phase03 仅剩 P0-13（DSHB 168h 噪声观测） | P2 | 0 | — |
| A-DSHE-4 | 准备 Phase04 bootstrap 元数据适配（5 项 DQA 标签） | P2 | 2.5d | DSHB DQA规则部署 |
| A-DSHE-5 | commit 推送 | P1 | 0.5h | A-DSHE-2~4 |

### 4.3 DSHB 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| A-DSHB-1 | 应用 R-V88-034 同步补丁 (dshb_risklist_patch.md) | P1 | 0.5h | 无 |
| A-DSHB-2 | 完成 P0-13 噪声基线报告（7天观测结束后） | P1 | 2.0h | 168h 观测完成 |
| A-DSHB-3 | 合并 P0-12 基线 + P0-13 噪声基线 → Phase04 长稳监控基线 | P1 | 1.0h | A-DSHE-3 + A-DSHB-2 |
| A-DSHB-4 | 更新 Phase04 数据源计划中 8 项 BLOCKED 指标爬虫进度 | P2 | 1.0h | 无 |

### 4.4 联动动作

| # | 动作 | 执行方 | 条件 |
|:-:|------|:------:|:----:|
| A-JOINT-1 | Phase03 全部门禁闭环确认 | HERMEShf | A-DSHE-5 + A-DSHB-3 |
| A-JOINT-2 | 启动 Phase04 bootstrap | HERMEShf | A-JOINT-1 |
| A-JOINT-3 | Phase03 预归档文件清单确认 | HERMEShf | A-JOINT-1 |

### 4.5 禁止动作

- ❌ DSHE 不得修改已冻结的 P0-12 采集 JSON 和 frozen 包
- ❌ DSHB 不得在 P0-13 噪声观测未满 168h 前合并基线
- ❌ 双方不得在 HERMEShf 下发 Phase03 闭环确认前启动 Phase04 正式工单

---

## 5. 分支 B：HERMEShf 官方门禁 P0-12 ❌ FAIL

### 5.1 触发条件

HERMEShf `blocker_monitor` cron 执行 P0-12 门禁复测，判定 `FAIL`。

**注意**：此分支不回到豁免方案。DSHE 启动可复现性排查，打开有限 debug 日志。

### 5.2 DSHE 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| B-DSHE-1 | 检查门禁日志，确认 FAIL 原因 | P1 | 0.5h | 无 |
| B-DSHE-2 | 检查 cpu_peak_pct.json 是否被意外修改 (MD5 比对) | P1 | 0.5h | B-DSHE-1 |
| B-DSHE-3 | 检查 HERMEShf 门禁 checker 脚本版本 | P1 | 0.5h | B-DSHE-1 |
| B-DSHE-4 | 打开有限 debug 日志（101 图表渲染逐图耗时） | P1 | 1.0h | B-DSHE-2 |
| B-DSHE-5 | 重新运行 1 轮 post_opt 基准测试 (idle=420s) | P1 | 15min | B-DSHE-1 |
| B-DSHE-6 | 比对新旧测试数据，定位偏差来源 | P1 | 1.0h | B-DSHE-5 |
| B-DSHE-7 | 若为环境差异：记录并重新部署 | P1 | 1.0d | B-DSHE-6 |
| B-DSHE-8 | 若为采集问题：修复采集脚本并重新部署 | P1 | 1.0d | B-DSHE-6 |
| B-DSHE-9 | 提交修复后重新推送 | P1 | 0.5h | B-DSHE-7/8 |

### 5.3 DSHB 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| B-DSHB-1 | 保持 P0-13 噪声观测进度 | — | 0 | 无 |
| B-DSHB-2 | 协助 DSHE 排查环境差异 | P2 | 0.5h | B-DSHE-6 |
| B-DSHB-3 | 在 DSHE 重新提交后更新合并基线计划 | P2 | 0.5h | B-DSHE-9 |

### 5.4 联动动作

| # | 动作 | 执行方 | 条件 |
|:-:|------|:------:|:----:|
| B-JOINT-1 | HERMEShf 重新触发门禁复测 | HERMEShf | B-DSHE-9 |
| B-JOINT-2 | Phase03 闭环推迟至 P0-12 重新通过 | HERMEShf | B-JOINT-1 结果 |

### 5.5 禁止动作

- ❌ **不得回退到豁免方案** — 原生 PASS 路径不可逆
- ❌ DSHE 不得直接修改 cpu_peak_pct 数值 — 必须通过新采集获取真实值
- ❌ DSHB 不得在 P0-12 重新通过前合并基线
- ❌ 双方不得隐瞒 FAIL 结果继续推进 Phase04

---

## 6. Phase03 → Phase04 衔接

### 6.1 Phase03 闭环条件

| # | 条件 | 责任方 | 状态 |
|:-:|------|:------:|:----:|
| 1 | P0-12 CPU 基线门禁 PASS | DSHE → HERMEShf | ⏳ 等待 cron |
| 2 | P0-13 噪声观测 168h 完成 | DSHB | 🟡 148/168h |
| 3 | R3 E2E 全量回归 PASS | DSHE | ✅ 8/8 |
| 4 | 风险台账全项对齐 | DSHE + DSHB | 🔄 R-V88-034 待同步 |

### 6.2 Phase04 bootstrap 前置

| # | 前置项 | 预估工时 | 负责方 |
|:-:|--------|:--------:|:------:|
| 1 | DQA 规则部署（14 项缺陷修复） | 5.0d | DSHB |
| 2 | 8 项 BLOCKED 指标爬虫新建 | 3.0d | DSHB |
| 3 | 渲染侧 5 项元数据适配 | 2.5d | DSHE |
| 4 | 长稳监控基线合并 | 1.0h | DSHB |
| 5 | Phase04 数据源计划更新 | 1.0h | DSHB |

---

## 7. 审计与同步

### 7.1 审计待命

- DSHE 保持 `<1h` 响应时间
- **不主动调用 HERMEShf 审批接口**
- 等待 `blocker_monitor` cron 自动触发官方 P0-12 复测
- 每次 cron 触发后 ≤1h 内提供审计支持

### 7.2 状态同步

| 事件 | 通知方 | 被通知方 | 通知方式 | 时效 |
|------|--------|----------|----------|:----:|
| 门禁 PASS | HERMEShf | DSHE + DSHB | cron 日志 | 即时 |
| 门禁 FAIL | HERMEShf | DSHE + DSHB | cron 日志 | 即时 |
| DSHE 修复推送 | DSHE | DSHB + HERMEShf | commit | 即时 |
| DSHB 同步补丁应用 | DSHB | DSHE + HERMEShf | commit | ≤1h |
| Phase04 bootstrap 启动 | HERMEShf | DSHE + DSHB | 新工单 | ≤24h |

---

## 8. 废弃声明

> **旧 SOP 已废弃**：`cross_align_ARCHIVED/cross_agent_exemption_sop.md`
>
> 旧 SOP 基于"豁免审批通过/驳回"分支设计，现已不适用于 P0-12 原生 PASS 场景。
> 新 SOP (本文档) 替代旧 SOP，作为 P0-12 原生 PASS 之后的唯一协同规范。

---

*Generated: 2026-10-16 UTC+8 | DSHE | P0-12 原生PASS三方协同SOP*
