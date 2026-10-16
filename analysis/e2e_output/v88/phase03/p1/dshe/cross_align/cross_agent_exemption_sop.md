# 跨 Agent 豁免审批协同操作 SOP

> **TASK_ID**: V88_PHASE03_P1_DSHE_P012_EXEMPTION_PREPARE_AND_CROSS_AGENT_ALIGN_JOB / T4
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **编写时间**: 2026-10-16 UTC+8
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL

---

## 1. SOP 范围

本 SOP 定义 HERMEShf 对 P0-12 CPU 阈值豁免审批的两种结果场景下，DSHE 与 DSHB 各自动作，防止审批结果下发后两边动作冲突、漏项。

**审批对象**：R-V88-034，P0-12 门禁 `cpu_peak_pct=99.4871%` 超标豁免申请（FAIL→WARN）

---

## 2. 分支 A：HERMEShf 审批通过豁免

### 2.1 触发条件

HERMEShf 审批 P0-12 豁免申请通过，P0-12 状态从 `EXEMPTION_REQUESTED` → `WARN (EXEMPTION_GRANTED)`

### 2.2 DSHE 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| A-DSHE-1 | 更新 R-V88-034 状态为 `✅ EXEMPTION_GRANTED` | P1 | 0.5h | 无 |
| A-DSHE-2 | P0-12 基线归档：`baseline_export.json` 标记为 `FROZEN_FINAL` | P1 | 0.5h | A-DSHE-1 |
| A-DSHE-3 | 准备 Phase04 元数据适配（5 项 DQA 标签） | P2 | 2.5d | DSHB DQA规则部署 |
| A-DSHE-4 | 更新 `STATUS.md` 标记 `P0_12_GATE=EXEMPTION_GRANTED` | P1 | 0.5h | A-DSHE-1 |
| A-DSHE-5 | commit 推送 | P1 | 0.5h | A-DSHE-2~4 |

### 2.3 DSHB 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| A-DSHB-1 | 更新 DSHB 风险台账 R-V88-034 为 `✅ EXEMPTION_GRANTED` | P1 | 0.5h | 无 |
| A-DSHB-2 | 完成 P0-13 噪声基线报告（7天观测结束后） | P1 | 2.0h | 168h 观测完成 |
| A-DSHB-3 | 合并 P0-12 基线 + P0-13 噪声基线 → Phase04 长稳监控基线 | P1 | 1.0h | A-DSHE-2 + A-DSHB-2 |
| A-DSHB-4 | 更新 Phase04 数据源计划中 8 项 BLOCKED 指标爬虫进度 | P2 | 1.0h | 无 |

### 2.4 联动动作

| # | 动作 | 执行方 | 条件 |
|:-:|------|:------:|:----:|
| A-JOINT-1 | Phase03 全部门禁闭环确认 | HERMEShf | A-DSHE-5 + A-DSHB-3 |
| A-JOINT-2 | 启动 Phase04 初始化 | HERMEShf | A-JOINT-1 |
| A-JOINT-3 | Phase03 预归档文件清单确认 | HERMEShf | A-JOINT-1 |

### 2.5 禁止动作

- ❌ DSHE 不得修改已冻结的 P0-12 采集 JSON 和 frozen 包
- ❌ DSHB 不得在 P0-13 噪声观测未满 168h 前合并基线
- ❌ 双方不得在 HERMEShf 下发 Phase03 闭环确认前启动 Phase04 正式工单

---

## 3. 分支 B：HERMEShf 驳回豁免

### 3.1 触发条件

HERMEShf 驳回 P0-12 豁免申请，要求 DSHE 进一步降低 CPU 数值。

### 3.2 DSHE 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| B-DSHE-1 | 更新 R-V88-034 状态为 `🔴 EXEMPTION_REJECTED` | P1 | 0.5h | 无 |
| B-DSHE-2 | 解冻 P0-12 采集脚本（`collect_cpu_baseline.py`） | P1 | 0.5h | B-DSHE-1 |
| B-DSHE-3 | 部署 psutil 系统级 CPU 采集脚本（替代 process_time 口径） | P1 | 2.0d | B-DSHE-2 |
| B-DSHE-4 | 执行精度降级方案评估（预留开关） | P1 | 1.0d | B-DSHE-1 |
| B-DSHE-5 | 重新采集 CPU 基线，输出新 JSON | P1 | 1.0d | B-DSHE-3 |
| B-DSHE-6 | 重新提交门禁校验 | P1 | 0.5h | B-DSHE-5 |
| B-DSHE-7 | 更新 frozen 包版本（v4.0.0） | P1 | 1.0h | B-DSHE-6 |
| B-DSHE-8 | 重新提交豁免申请或直接 PASS | P1 | 0.5h | B-DSHE-7 |
| B-DSHE-9 | commit 推送 | P1 | 0.5h | B-DSHE-8 |

### 3.3 DSHB 动作清单

| # | 动作 | 优先级 | 预估工时 | 依赖 |
|:-:|------|:------:|:--------:|:----:|
| B-DSHB-1 | 更新 DSHB 风险台账 R-V88-034 为 `🔴 EXEMPTION_REJECTED` | P1 | 0.5h | 无 |
| B-DSHB-2 | 继续噪声观测（不影响 P0-13 进度） | — | 0 | 无 |
| B-DSHB-3 | 协助 DSHE 确认 psutil 采集环境 | P2 | 0.5h | B-DSHE-3 |
| B-DSHB-4 | 在 DSHE 重新提交后更新合并基线计划 | P2 | 0.5h | B-DSHE-8 |

### 3.4 联动动作

| # | 动作 | 执行方 | 条件 |
|:-:|------|:------:|:----:|
| B-JOINT-1 | HERMEShf 重新审批 P0-12 | HERMEShf | B-DSHE-9 |
| B-JOINT-2 | Phase03 闭环推迟至 P0-12 重新通过 | HERMEShf | B-JOINT-1 结果 |

### 3.5 禁止动作

- ❌ DSHE 不得直接修改 `cpu_peak_pct` 数值——必须通过新采集方法获取真实值
- ❌ DSHE 不得跳过 psutil 系统级采集直接改口径——被驳回意味着口径修复不被认可
- ❌ DSHB 不得在 P0-12 重新通过前合并基线
- ❌ 双方不得隐瞒驳回结果继续推进 Phase04

---

## 4. 精度降级方案（分支 B 备选预案）

若 psutil 采集后 CPU 仍超标，DSHE 预留以下开关：

| 开关 | 机制 | CPU 预期降幅 | 业务影响 | 实施难度 |
|------|------|:------------:|----------|:--------:|
| `RENDER_PRECISION_LOW` | 降低图表渲染精度（采样点数减半） | ~25% | 图表细节损失 | 低 |
| `RENDER_ASYNC_QUEUE` | 异步渲染排队（非阻塞返回） | ~0% (峰值延迟到其他时段) | 首次渲染延迟 | 中 |
| `RENDER_BATCH_MODE` | 批量渲染（合并多图表为单次计算） | ~15% | 响应延迟增加 | 中 |
| `RENDER_CACHE_TTL_EXTENDED` | 延长缓存有效期 | ~50% (缓存命中时) | 数据新鲜度降低 | 低 |

**实施条件**：精度降级需 HERMEShf 批准 `RENDER_DEGRADE_FLAG`，DSHE 不得自行开启。

---

## 5. 审批状态双向同步机制

| 事件 | 通知方 | 被通知方 | 通知方式 | 时效 |
|------|--------|----------|----------|:----:|
| 豁免提交 | DSHE | DSHB + HERMEShf | commit + 风险台账更新 | 即时 |
| 豁免通过 | HERMEShf | DSHE + DSHB | 新工单下发 | ≤24h |
| 豁免驳回 | HERMEShf | DSHE + DSHB | 新工单下发 | ≤24h |
| 重新提交 | DSHE | DSHB + HERMEShf | commit + 风险台账更新 | 即时 |
| psutil 采集完成 | DSHE | DSHB + HERMEShf | commit + 新 JSON | 即时 |
| 基线合并完成 | DSHB | DSHE + HERMEShf | commit + 合并 JSON | ≤1h |

**同步检查清单**：
- [ ] DSHE 风险台账 R-V88-034 状态与 DSHB 一致
- [ ] frozen 包版本号在双方台账中一致
- [ ] 基线 JSON 的 `source_md5` 在双方记录中一致
- [ ] Phase03 闭环确认前双方台账无 OPEN/REJECTED 项

---

## 6. 防冲突原则

1. **DSHE 先行原则**：CPU 采集和优化是 DSHE 职责，DSHB 不得越俎代庖
2. **DSHB 等待原则**：DSHB 合并基线必须等 DSHE 基线冻结后才能进行
3. **HERMEShf 裁决原则**：审批结果由 HERMEShf 统一下发，双方不得自行协商变更门禁状态
4. **单向冻结原则**：一旦 frozen 包版本升级，旧版本不得回退

---

*Generated: 2026-10-16 UTC+8 | DSHE | 跨Agent协同SOP覆盖审批通过/驳回两条路径*
