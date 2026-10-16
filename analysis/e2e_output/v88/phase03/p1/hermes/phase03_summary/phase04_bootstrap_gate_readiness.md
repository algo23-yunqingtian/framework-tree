# Phase04 Bootstrap 门控就绪草稿 (READY-ON-TRIGGER)

> **TASK_ID**: V88_PHASE03_P1_HERMES_EXEMPTION_FOLLOWUP_AND_PHASE03_SUMMARY_AUDIT_JOB / T4
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **状态**: 📦 **READY-ON-TRIGGER — 不正式下发，等待 P0-13 闭环信号**
> **编写时间**: 2026-10-16 UTC+8

---

## 1. 激活条件

| # | 条件 | 当前状态 | 激活信号 |
|:-:|------|:--------:|----------|
| 1 | P0-13 噪声观测 168h 完成 | 🟡 148/168h (88.1%) | `noise_7d_checkpoint.json` 中 `observation_hours >= 168` |
| 2 | P0-13 门禁判定 PASS | 🟡 PENDING | `noise_rate_pct < 10` |
| 3 | Phase03 阻断清零 | ✅ 0 阻断 | 已满足 |
| 4 | DSHB 台账 R-V88-034 同步 | ⚠️ 待 DSHB 更新 | DSHB 下次 commit |

**激活路径**：条件 1+2 满足 → p013_complete_watcher 钩子通知 HERMEShf → HERMEShf 确认 Phase03 闭环 → 激活 Phase04 Bootstrap 工单。

> ⚠️ 本文件仅为准备就绪包，**不激活执行**。Phase04 大工单须由 HERMEShf 在 P0-13 闭环后正式下发。

---

## 2. Phase04 目标

| 里程碑 | 目标 | 时间 |
|--------|------|:----:|
| M1 | 数据源补充 (8 项 WARN → PASS) + DQA 规则改进 (DQA-03/04/05/07/08) | 第 2 周 |
| M2 | 新建爬虫 (8 项 BLOCKED) + DQA-09/10/11 部署 | 第 5 周 |
| M3 | 代理模型优化 (6 项 WARN) + DQA-10 置信度闭环 | 第 8 周 |
| M4 | 数据回填 (11 项) + DQA-11 频率一致性 | 第 10 周 |
| M5 | DSHE 对接 (36 项全上) + 渲染侧 DQA 标签适配 | 第 12 周 |

---

## 3. Phase04 门控清单

### 3.1 P0-12 遗留项

| # | 任务 | 来源 | 执行方 | 优先级 |
|:-:|------|------|:------:|:------:|
| 1 | psutil 系统级 CPU 采集部署 | C-3 约束 | DSHE | P1 (M1 前) |
| 2 | manifest 自引用 MD5 修复 | C-5 约束 | DSHE | P2 |
| 3 | ALTERNATIVE-01 重新评估 | T0 归档 | DSHE+HERMEShf | P2 (M1 后) |
| 4 | 渲染侧 DQA 元数据适配 (5 项) | DQA 影响评估 | DSHE | P1 (M1 前) |

### 3.2 P0-13 遗留项

| # | 任务 | 执行方 | 优先级 |
|:-:|------|:------:|:------:|
| 1 | 完成 168h 噪声观测 | DSHB | P0 (当前) |
| 2 | P0-13 门禁判定 | DSHB+HERMEShf | P0 |
| 3 | 基线合并 (P0-12+P0-13) | DSHB | P1 |

### 3.3 数据源补充

| # | 指标 | 状态 | 目标 | 执行方 |
|:-:|------|:----:|:----:|:------:|
| 1 | 36 项 DQA 全 PASS | 16/36 | 36/36 | DSHB |
| 2 | 8 项 BLOCKED 指标爬虫 | 0/8 | 8/8 | DSHB |
| 3 | DQA-09~15 新规则部署 | 0/7 | 7/7 | DSHB |
| 4 | Wind 数据源授权 | 方案完成 | 2-4 周授权 | DSHB |

---

## 4. Phase04 Bootstrap 工单草稿

```
TASK_ID: V88_PHASE04_BOOTSTRAP_JOB (草稿，未下发)
AGENT: HERMES
BRANCH: feature/v88-g1
触发条件: P0-13 闭环信号 + Phase03 阻断清零确认

任务目标:
1. 激活 Phase04 M1 里程碑
2. DSHE 部署 psutil 采集脚本 (C-3)
3. DSHB 启动 8 项 BLOCKED 指标爬虫建设
4. DSHB 部署 DQA-09~15 新规则
5. DSHE 实施渲染侧 DQA 元数据适配 (5 项, 2.5 人天)
6. 修复 manifest 自引用 MD5 缺陷 (C-5)
7. 建立 Phase04 长稳监控基线 (P0-12+P0-13 合并)

注意:
- 不得修改 Phase03 冻结产物
- ALTERNATIVE-01 (55458b6) 重新评估须新 HERMEShf 审批
- DQA 规则改进须按 P1/P2 优先级实施
```

---

## 5. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|:----:|:----:|------|
| P0-13 噪声率超 10% | 低 (当前 9.49%) | Phase03 延期 | DSHB 持续观测+噪声治理 |
| Wind 授权延迟 (>4 周) | 中 | M2 延期 | 备选数据源方案 |
| psutil 环境不稳定 | 中 | C-3 延期 | 55458b6 已验证可用 |
| DQA 规则开发延期 | 中 | M1 延期 | P1/P2 分级实施 |

---

## 6. 不激活声明

> 🚨 本文件是 **READY-ON-TRIGGER** 状态的准备就绪包。
>
> - ❌ 不正式下发 Phase04 大工单
> - ❌ 不激活任何 Phase04 执行动作
> - ❌ 不修改 Phase03 冻结产物
> - ✅ 仅在 P0-13 闭环信号触发后由 HERMEShf 正式激活
>
> 任何 agent 不得在 HERMEShf 正式下发 Phase04 工单前执行本文件中的任务。

---

*Generated: 2026-10-16 UTC+8 | HERMEShf | Phase04 Bootstrap 门控就绪草稿 (READY-ON-TRIGGER)*
