# V86 回滚预案 V7

> **Task**: DSHB_V86_RELEASE_CANDIDATE_PREPARATION_V7 · T3.3
> **Branch**: `feature/v85-chart-template`
> **DSHB V6 Base**: `c4ccfd5` (V6 上线准入评估 + Gate 判定)
> **DSHE V6 Base**: `05352a5` (DSHE_V86_ALIAS_V6_ITERATION)
> **约束**: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED
> **生成日期**: 2026-10-03

---

## 1. 执行摘要

本报告定义 V86 发布后的回滚触发条件、回滚步骤、回滚目标版本与回滚后验证项, 确保在发布异常时可快速恢复至稳定状态。

| 维度 | 值 |
|------|-----|
| 回滚策略 | 三步回滚 (分支回滚 → 指标回滚 → 页面回滚) |
| 回滚目标 | V85 FROZEN (commit f313570) |
| 预估回滚时间 | 16 分钟 (Strategy A) / 30 分钟 (Strategy B) |
| 回滚触发条件 | 5 项触发条件 |
| 回滚验证项 | 10 项验证 |

### 1.1 回滚策略总览

```
┌─────────────────────────────────────────────────────────────┐
│  ROLLBACK PLAN OVERVIEW V7                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             ║
│  ROLLBACK STRATEGIES:                                       ║
│                                                             ║
│  Strategy A: Quick Rollback (16 min)                         ║
│  ├─ Branch:   feature/v85-chart-template → revert commit    ║
│  ├─ Metrics:  降级指标回退 (7 张图表)                          ║
│  ├─ Pages:    V86 页面标记为不可用                             ║
│  └─ Use Case: 发布后 2h 内异常                                 ║
│                                                             ║
│  Strategy B: Full Rollback (30 min)                          ║
│  ├─ Branch:   feature/v85-chart-template → main revert      ║
│  ├─ Metrics:  全部 V86 指标回退                               ║
│  ├─ Pages:    V86 页面删除                                   ║
│  ├─ Tags:     v86-rc1 tag 删除                               ║
│  └─ Use Case: 发布后 2h+ 异常                                 ║
│                                                             ║
│  ROLLBACK TARGET: V85 FROZEN (f313570)                       ║
│                                                             ║
│  TRIGGERS: 5 conditions                                      ║
│  VALIDATION: 10 items                                        ║
│                                                             ║
│  ═══════════════════════════════════════                      ║
│  ROLLBACK READY: YES ✅                                      ║
│  ═══════════════════════════════════════                      ║
│                                                             ║
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 回滚触发条件

### 2.1 一级触发条件 (立即回滚)

| # | 触发条件 | 判定标准 | 响应时间 | 回滚策略 |
|---|---------|---------|---------|---------|
| T-01 | P0 告警触发 | 任一 P0 告警活跃 | 5 分钟 | Strategy B |
| T-02 | 引擎不可用 | healthz ≠ 200 持续 5 分钟 | 5 分钟 | Strategy B |
| T-03 | 裁决错误率>5% | PASS 率 <91% | 10 分钟 | Strategy B |
| T-04 | 数据一致性异常 | 31/31 回测不通过 | 15 分钟 | Strategy B |
| T-05 | 安全漏洞 | exec() 等安全告警触发 | 立即 | Strategy B |

### 2.2 二级触发条件 (评估后回滚)

| # | 触发条件 | 判定标准 | 评估时间 | 回滚策略 |
|---|---------|---------|---------|---------|
| T-06 | 吞吐量下降>30% | <1,500/s 持续 30 分钟 | 30 分钟 | Strategy A |
| T-07 | 延迟 P95>10ms | 持续 30 分钟 | 30 分钟 | Strategy A |
| T-08 | 歧义率>6% | 持续 1 小时 | 1 小时 | Strategy A |
| T-09 | 队列深度>1000 | 持续 30 分钟 | 30 分钟 | Strategy A |
| T-10 | 多个降级图表不可用 | >3 张降级图表异常 | 1 小时 | Strategy A |

### 2.3 三级触发条件 (观察后回滚)

| # | 触发条件 | 判定标准 | 观察时间 | 回滚策略 |
|---|---------|---------|---------|---------|
| T-11 | 监控覆盖率<65% | 持续 24 小时 | 24 小时 | Strategy A |
| T-12 | 34 歧义审阅进度<5/34 | T+24h | 24 小时 | 不阻塞 |
| T-13 | Prometheus 部署延迟>72h | 持续 72 小时 | 72 小时 | 不阻塞 |

### 2.4 触发条件决策矩阵

```
                    影响程度
                  低      中      高
              ┌─────┬─────┬─────┐
         高   │     │     │     │
              │     │ T-03│T-01 │
              │     │ T-04│T-02 │
              │     │     │T-05 │
              ├─────┼─────┼─────┤
         中   │     │T-06 │     │
              │     │T-07 │     │
              │     │T-08 │     │
              │     │T-09 │     │
              ├─────┼─────┼─────┤
         低   │T-12 │     │     │
              │T-13 │     │     │
              └─────┴─────┴─────┘
        
        可能性 ↑
```

---

## 3. 回滚步骤

### 3.1 Strategy A: 快速回滚 (16 分钟)

#### 3.1.1 回滚流程

```
T+0min ─── 触发回滚决策
    │
T+2min ─── Step 1: 分支回滚 (revert commit)
    │
T+5min ─── Step 2: 降级指标回退 (7 张图表标记)
    │
T+8min ─── Step 3: V86 页面标记为不可用
    │
T+10min ── Step 4: 通知相关方
    │
T+12min ── Step 5: 回滚验证
    │
T+16min ── Step 6: 回滚确认
```

#### 3.1.2 Step 1: 分支回滚 (2 分钟)

```bash
# 1. 确认当前 main 的 V86 commit
git log --oneline -5 origin/main

# 2. Revert V86 合并 commit
git revert <v86-merge-commit> --no-edit

# 3. 推送回滚 commit
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main

# 4. 确认回滚
git log --oneline -3 origin/main
```

#### 3.1.3 Step 2: 降级指标回退 (3 分钟)

| 回滚项 | 操作 | 预计耗时 |
|--------|------|---------|
| 7 张降级图表标记 | 添加 `.degraded` CSS 类 | 2 分钟 |
| 降级状态记录 | 记录降级原因与时间 | 1 分钟 |

#### 3.1.4 Step 3: V86 页面标记 (3 分钟)

| 页面 | 操作 | 状态 |
|------|------|------|
| v86_gate_overview.html | 添加不可用标记 | ⚠️ |
| v86_risk_monitoring.html | 添加不可用标记 | ⚠️ |
| v86_inspection_timeline.html | 添加不可用标记 | ⚠️ |
| v86_p0_gap_special.html | 添加不可用标记 | ⚠️ |
| v86_global_metric_list.html | 添加不可用标记 | ⚠️ |
| v86_metric_alignment.html | 添加不可用标记 | ⚠️ |
| v86_chart_consistency.html | 添加不可用标记 | ⚠️ |

#### 3.1.5 Step 4: 通知 (2 分钟)

| 通知对象 | 通知内容 | 渠道 |
|---------|---------|------|
| DSHB Team | 回滚原因 + 时间 + 影响 | 即时通讯 |
| DSHE Team | 回滚影响评估 | 即时通讯 |
| SRE | 回滚完成确认 | 即时通讯 |
| Platform | 降级指标状态 | 即时通讯 |

#### 3.1.6 Step 5: 回滚验证 (4 分钟)

| # | 验证项 | 预期 | 验证方式 |
|---|-------|------|---------|
| 1 | main 分支已回滚 | revert commit 存在 | git log |
| 2 | V86 页面不可访问 | 404 或标记 | HTTP 检查 |
| 3 | 7 张图表降级标记 | .degraded 类存在 | HTML 检查 |
| 4 | 引擎状态 | healthz 200 | API 检查 |
| 5 | 裁决分布 | PASS>96% | Prometheus |

#### 3.1.7 Step 6: 回滚确认 (2 分钟)

| 确认项 | 确认人 | 记录 |
|--------|--------|------|
| 回滚完成 | DSHB | 回滚记录文档 |
| 影响评估 | SRE | 影响报告 |
| 后续计划 | Platform | 修复计划 |

### 3.2 Strategy B: 完整回滚 (30 分钟)

#### 3.2.1 回滚流程

```
T+0min ─── 触发回滚决策
    │
T+2min ─── Step 1: 分支完整回滚
    │
T+8min ─── Step 2: V86 指标全部回退
    │
T+14min ── Step 3: V86 页面删除
    │
T+18min ── Step 4: Git tag 清理
    │
T+20min ── Step 5: 通知相关方
    │
T+24min ── Step 6: 回滚验证
    │
T+30min ── Step 7: 回滚确认
```

#### 3.2.2 Step 1: 分支完整回滚 (6 分钟)

```bash
# 1. 确认 V86 所有 commit
git log --oneline origin/main | grep -i "v86"

# 2. 逐条 revert V86 commit (从新到旧)
git revert <commit5> --no-edit
git revert <commit4> --no-edit
# ... 逐条 revert

# 3. 推送回滚
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main

# 4. 确认回滚
git log --oneline -10 origin/main
```

#### 3.2.3 Step 2: V86 指标全部回退 (6 分钟)

| 回滚项 | 操作 | 预计耗时 |
|--------|------|---------|
| 7 张降级图表 | 删除降级标记 | 2 分钟 |
| V86 Prometheus 指标 | 标记为 disabled | 2 分钟 |
| Grafana 面板 | 恢复至 V85 配置 | 2 分钟 |

#### 3.2.4 Step 3: V86 页面删除 (6 分钟)

| 页面 | 操作 | 状态 |
|------|------|------|
| v86_gate_overview.html | 删除 | ❌ |
| v86_risk_monitoring.html | 删除 | ❌ |
| v86_inspection_timeline.html | 删除 | ❌ |
| v86_p0_gap_special.html | 删除 | ❌ |
| v86_global_metric_list.html | 删除 | ❌ |
| v86_metric_alignment.html | 删除 | ❌ |
| v86_chart_consistency.html | 删除 | ❌ |

#### 3.2.5 Step 4: Git tag 清理 (2 分钟)

```bash
# 1. 删除本地 tag
git tag -d v86-rc1

# 2. 删除远端 tag
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin :refs/tags/v86-rc1
```

#### 3.2.6 Step 5: 通知 (2 分钟)

同 Strategy A Step 4。

#### 3.2.7 Step 6: 回滚验证 (4 分钟)

| # | 验证项 | 预期 | 验证方式 |
|---|-------|------|---------|
| 1 | main 分支已完整回滚 | 无 V86 commit | git log |
| 2 | V86 页面不存在 | 404 | HTTP 检查 |
| 3 | V86 指标已 disabled | disabled 状态 | Prometheus |
| 4 | Git tag 已删除 | tag 不存在 | git tag |
| 5 | 引擎状态 | healthz 200 | API 检查 |
| 6 | 裁决分布 | PASS>96% | Prometheus |

#### 3.2.8 Step 7: 回滚确认 (2 分钟)

同 Strategy A Step 6。

---

## 4. 回滚目标版本

### 4.1 目标版本定义

| 属性 | 值 |
|------|-----|
| 回滚目标 | V85 FROZEN |
| Commit | `f313570` |
| Tag | `v85-final-persist` |
| 状态 | FROZEN (稳定版) |
| 验证时间 | 2026-09 (V85 发布) |

### 4.2 回滚前后对比

| 维度 | V86-RC1 (当前) | V85 FROZEN (回滚目标) | 差异 |
|------|---------------|---------------------|------|
| 指标数 | 178 | ~78 (基线) | -100 |
| 图表数 | 36 | 0 | -36 |
| Gate 条件 | 5/5 PASS | N/A | N/A |
| 版本链路 | V1→V7 | N/A | N/A |
| 页面数 | ~660 | ~625 | -35 |
| 页面状态 | 部分降级 | 稳定运行 | 回滚 |

### 4.3 回滚影响评估

| 影响项 | 影响程度 | 可接受? | 说明 |
|--------|---------|--------|------|
| V86 功能丢失 | 中 | ✅ | V86 为新增, 非回滚 |
| 7 张降级图表回退 | 低 | ✅ | 降级方案本身即回退 |
| Prometheus 指标回退 | 低 | ✅ | 新增指标回退 |
| Grafana 面板回退 | 低 | ✅ | 新增面板回退 |
| V86 页面回退 | 低 | ✅ | 新增页面回退 |
| Git tag 删除 | 低 | ✅ | 新增 tag 删除 |
| **总体影响** | **低** | **✅** | **仅回退 V86 新增内容** |

---

## 5. 回滚后验证项

### 5.1 回滚后 5 分钟验证

| # | 验证项 | 预期 | 验证方式 | 失败处理 |
|---|-------|------|---------|---------|
| 1 | main 分支回滚 | revert commit 存在 | git log | 立即修复 |
| 2 | 引擎健康 | healthz 200 | curl | 检查配置 |
| 3 | 裁决分布 | PASS>96% | Prometheus | 检查规则 |
| 4 | 吞吐量 | >2000/s | Prometheus | 检查负载 |
| 5 | 延迟 P95 | <5ms | Prometheus | 检查性能 |

### 5.2 回滚后 30 分钟验证

| # | 验证项 | 预期 | 验证方式 | 失败处理 |
|---|-------|------|---------|---------|
| 6 | V86 页面不可访问 | 404 或标记 | HTTP 检查 | 检查部署 |
| 7 | V86 指标已回退 | disabled | Prometheus | 检查配置 |
| 8 | Git tag 状态 | 已删除/已回退 | git tag | 检查 tag |
| 9 | 告警状态 | 0 活跃 P0 | 告警面板 | 检查告警 |
| 10 | 页面渲染 | 242/242 PASS | verify_render | 检查渲染 |

### 5.3 回滚后 2 小时验证

| # | 验证项 | 预期 | 验证方式 | 失败处理 |
|---|-------|------|---------|---------|
| 11 | 回测一致性 | 31/31 PASS | 回测脚本 | 检查规则 |
| 12 | 歧义率 | ≤5% | Prometheus | 检查别名库 |
| 13 | 队列深度 | <500 | Prometheus | 检查负载 |
| 14 | 监控覆盖率 | >70% | Prometheus | 检查监控 |
| 15 | 灰度门禁 | 12/12 PASS | 门禁面板 | 检查门禁 |

---

## 6. 回滚后恢复计划

### 6.1 问题分析

| 步骤 | 负责人 | 产出 | 时限 |
|------|--------|------|------|
| 1 | 收集回滚日志 | SRE | 回滚后 1h |
| 2 | 分析回滚原因 | DSHB+DSHE | 回滚后 24h |
| 3 | 制定修复计划 | DSHB+Platform | 回滚后 48h |
| 4 | 修复实施 | DSHB+Platform | 回滚后 7d |
| 5 | 修复验证 | DSHB+SRE | 回滚后 7d |
| 6 | 重新发布 | DSHB | 回滚后 14d |

### 6.2 重新发布条件

| 条件 | 要求 | 说明 |
|------|------|------|
| 问题修复 | 回滚原因已修复 | 根因分析完成 |
| 回归测试 | 31/31 PASS | 全量回测通过 |
| Gate 重新评估 | 5/5 PASS | Gate 条件重新满足 |
| P0 清零 | 0 | 无新 P0 |
| 回滚影响消除 | 全部消除 | 所有回滚影响已恢复 |

---

## 7. 回滚预案结论

```
╔══════════════════════════════════════════════════════════════╗
║       ROLLBACK PLAN VERDICT V7                                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ROLLBACK STRATEGIES:                                       ║
║  ├─ Strategy A: Quick Rollback (16 min) ✅                   ║
║  └─ Strategy B: Full Rollback (30 min) ✅                     ║
║                                                              ║
║  ROLLBACK TARGET: V85 FROZEN (f313570) ✅                     ║
║                                                              ║
║  TRIGGERS:                                                  ║
║  ├─ Tier 1 (Immediate): 5 conditions ✅                      ║
║  ├─ Tier 2 (Evaluated): 5 conditions ✅                       ║
║  └─ Tier 3 (Observed):  3 conditions ✅                       ║
║                                                              ║
║  VALIDATION:                                               ║
║  ├─ 5min:     5 items ✅                                     ║
║  ├─ 30min:    5 items ✅                                      ║
║  └─ 2h:       5 items ✅                                     ║
║                                                              ║
║  IMPACT ASSESSMENT:                                         ║
║  ├─ V86 Features:   Lost (acceptable) ✅                      ║
║  ├─ V85 Stability:  Maintained ✅                             ║
║  └─ Overall:        Low impact ✅                             ║
║                                                              ║
║  ═══════════════════════════════════════                      ║
║  VERDICT: ROLLBACK PLAN COMPLETE ✅                           ║
║  ROLLBACK READY: YES ✅                                       ║
║  ═══════════════════════════════════════                      ║
║                                                              ║
║  Generated: 2026-10-03                                       ║
║  Branch: feature/v85-chart-template                          ║
║  DSHB V6 Commit: c4ccfd5                                    ║
║  DSHE V6 Commit: 05352a5                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 8. 约束合规

| Constraint | Status |
|------------|--------|
| `NO_ZHIJI_API_CALL=TRUE` | ✅ 合规 — 全部基于本地固化数据 |
| `NO_MODIFY_V85=TRUE` | ✅ 合规 — 未修改 V85 基线 |
| `NO_OVERWRITE=TRUE` | ✅ 合规 — 仅新增 V7 文件 |
| `BRANCH_LOCKED=TRUE` | ✅ 合规 — 分支未变更 |

---

*Generated by DSHB Gate Review Agent — T3.3*
*Task: DSHB_V86_RELEASE_CANDIDATE_PREPARATION_V7*
*Branch: feature/v85-chart-template*
*DSHB V6 Commit: c4ccfd5*
*DSHE V6 Commit: 05352a5*
*Verification Date: 2026-10-03*
