# V86-RC2 DEP恢复后运维切换SOP

> **Task:** DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.4
> **Generated:** 2026-10-15
> **Branch:** `feature/v85-chart-template`
> **Output Dir:** `analysis/e2e_output/v86/hermes_e2e_test/`
> **Status:** ✅ T3.4 COMPLETE — DEP恢复切换SOP已完善，降级策略退出、告警切换步骤完整

---

## 1. SOP概述

### 1.1 适用场景
当DSHB桥接快照中`data_fetchable`字段出现`TRUE`条目时，表示数据平台DEP恢复完成，需要执行以下切换操作：
1. 降级策略逐级退出（L1→L2→L3）
2. 面板状态徽章从🟡DEPENDENCY_BLOCK切换到🟢FULLY_AVAILABLE
3. V-FETCH告警规则切换为正常指标监控
4. 业务侧通知团队

### 1.2 前置条件

| # | 条件 | 检查方法 | 预期 |
|---|------|---------|------|
| 1 | 快照检测到data_fetchable=TRUE | `snapshot_watcher.py --once` | 恢复通知 |
| 2 | 双维度联合校验通过 | `dep_recovery_auto_verify.py --auto` | 0误判 |
| 3 | HERMES预审通过 | HERMES预审报告 | ✅ |
| 4 | DSHB确认底层数据可用 | DSHB确认函 | ✅ |
| 5 | Gate评审条件满足 | Gate准入8项 | ✅ 全部通过 |

### 1.3 约束合规

| 约束 | 值 |
|------|-----|
| `JOB_READY` | FALSE |
| `NO_ZHIJI_API_CALL` | FALSE (允许) |
| `NO_MODIFY_V85` | TRUE |
| `NO_OVERWRITE` | TRUE |
| `BRANCH_LOCKED` | TRUE |

---

## 2. 切换时间线

```
T+0    DEP恢复检测 (快照data_fetchable=TRUE)
  │
T+0h   自动触发双维度联合校验 (dep_recovery_auto_verify.py)
  │
T+1h   校验结果确认 (0误判/0渲染异常)
  │
T+2h   HERMES预审确认
  │
T+3h   DSHB底层确认
  │
T+4h   Gate评审 (8项准入条件)
  │
T+5h   降级策略退出 (L3→L2→L1)
  │
T+6h   面板状态切换 (🟡→🟢)
  │
T+7h   告警规则切换
  │
T+8h   业务侧通知
  │
T+24h  恢复后首轮验证
  │
T+7d   恢复后观测结束
```

---

## 3. 降级策略退出SOP

### 3.1 EM-05 v2.0 三级降级退出

#### L3退出 — 面板隔离退出
```
触发条件: L2静态数据已可用，缓存数据已过期
退出步骤:
  1. 确认L2静态数据已包含最新可用数据
  2. 执行面板隔离解除: EM-05 L3 → DISABLED
  3. 验证面板数据恢复实时拉取
  4. 更新面板隔离日志
  5. 记录退出时间戳
验证标准:
  - 面板显示实时数据（非静态）
  - 面板隔离标记消失
  - 数据延迟 ≤ 5min (TTL)
```

#### L2退出 — 静态降级退出
```
触发条件: L1缓存数据已可用，缓存数据已过期
退出步骤:
  1. 确认L1缓存包含有效数据
  2. 执行静态降级解除: EM-05 L2 → DISABLED
  3. 验证面板数据恢复API实时拉取
  4. 更新降级策略日志
  5. 记录退出时间戳
验证标准:
  - 面板数据来源标记为 "LIVE_API"
  - 静态数据标记消失
  - 数据更新周期 ≤ 5min
```

#### L1退出 — 缓存降级退出
```
触发条件: 所有指标data_fetchable=TRUE，API实时拉取正常
退出步骤:
  1. 确认所有178条桥接条目data_fetchable=TRUE
  2. 执行缓存降级解除: EM-05 L1 → DISABLED
  3. 清除本地缓存数据
  4. 强制刷新面板数据
  5. 更新降级策略日志
  6. 记录退出时间戳
验证标准:
  - 缓存降级标记消失
  - 所有面板数据来源为 "LIVE_API"
  - 数据完整性 178/178
```

### 3.2 降级退出顺序（强制）

```
L3退出 → L2退出 → L1退出 (必须按此顺序，禁止跳过)
```

| 顺序 | 步骤 | 持续时间 | 验证 |
|------|------|---------|------|
| 1 | L3面板隔离退出 | ~30min | 面板实时数据 |
| 2 | L2静态降级退出 | ~30min | API实时拉取 |
| 3 | L1缓存降级退出 | ~30min | 178/178实时数据 |

---

## 4. 面板状态切换SOP

### 4.1 面板徽章切换

| 面板 | 当前状态 | 目标状态 | 切换条件 |
|------|---------|---------|---------|
| PB_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有PB指标data_fetchable=TRUE |
| CU_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有CU指标data_fetchable=TRUE |
| AL_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有AL指标data_fetchable=TRUE |
| ZN_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有ZN指标data_fetchable=TRUE |
| NI_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有NI指标data_fetchable=TRUE |
| SN_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有SN指标data_fetchable=TRUE |
| SI_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有SI指标data_fetchable=TRUE |
| LI_Price_Panel | 🟡 DEPENDENCY_BLOCKED | 🟢 FULLY_AVAILABLE | 所有LI指标data_fetchable=TRUE |

### 4.2 面板横幅切换

```
当前: [DEPENDENCY_BLOCK] 数据获取受限 - zhiji API外部依赖阻塞
目标: [FULLY_AVAILABLE] 数据获取正常 - 所有指标可用
```

### 4.3 面板状态验证

| 检查项 | 预期 | 验证方法 |
|--------|------|---------|
| 徽章颜色 | 🟢 绿色 | 面板截图 |
| 徽章文字 | FULLY_AVAILABLE | 面板截图 |
| 横幅内容 | 数据获取正常 | 面板截图 |
| 数据延迟 | ≤ 5min | Prometheus指标 |
| 数据完整性 | 178/178 | 桥接快照校验 |

---

## 5. 告警规则切换SOP

### 5.1 V-FETCH告警规则切换

| 规则ID | 规则名称 | 当前状态 | 目标状态 | 切换动作 |
|--------|---------|---------|---------|---------|
| R-DSHE-ID-48 | V-FETCH-01 面板取数阻塞 | ✅ 触发 | ❌ 静默 | 关闭告警 |
| R-DSHE-ID-49 | V-FETCH-02 告警规则阻塞 | ✅ 触发 | ❌ 静默 | 关闭告警 |
| R-DSHE-ID-50 | V-FETCH-03 日志状态阻塞 | ✅ 触发 | ❌ 静默 | 关闭告警 |
| R-DSHE-ID-51 | V-FETCH-04 跨Agent链路阻塞 | ✅ 触发 | ❌ 静默 | 关闭告警 |
| R-DSHE-ID-52 | V-FETCH-05 面板可用率异常 | ❌ 未触发 | ✅ 启用 | 启用告警 |
| R-DSHE-ID-53 | V-FETCH-06 数据流延迟异常 | ❌ 未触发 | ✅ 启用 | 启用告警 |

### 5.2 正常指标监控告警启用

| 规则ID | 规则名称 | 阈值 | 严重度 | 切换动作 |
|--------|---------|------|--------|---------|
| R-DSHE-001 | 面板加载超时 | >5s | P1 | 启用 |
| R-DSHE-002 | 数据延迟异常 | >15min | P2 | 启用 |
| R-DSHE-003 | 面板渲染错误 | >0次 | P1 | 启用 |
| R-DSHE-004 | 数据完整性异常 | <178/178 | P0 | 启用 |
| R-DSHE-005 | 缓存命中率异常 | <50% | P2 | 启用 |
| R-DSHE-006 | 降级策略触发 | 非预期触发 | P1 | 启用 |

### 5.3 告警切换验证

| 检查项 | 预期 | 验证方法 |
|--------|------|---------|
| V-FETCH-01~04 | ❌ 已静默 | 告警历史查询 |
| V-FETCH-05~06 | ✅ 已启用 | 告警规则配置 |
| R-DSHE-001~006 | ✅ 已启用 | 告警规则配置 |
| 告警触发 | 0误报 | 24小时观测 |
| 告警触发 | 0漏报 | 模拟测试 |

---

## 6. 业务侧通知SOP

### 6.1 通知模板

#### 通知1: 恢复通知

```
标题: [DSHE V86-RC2] DEP恢复通知 — 数据获取已恢复正常

内容:
  时间: {recovery_time}
  状态: ✅ 已恢复
  范围: 全部8品种178项指标
  恢复率: {recovery_rate}%
  验证: 双维度联合校验通过 (0误判)
  影响: 面板状态从 🟡DEPENDENCY_BLOCK 切换为 🟢FULLY_AVAILABLE
  操作: 无操作需要，面板将自动刷新

  降级策略: L1/L2/L3已逐级退出
  告警规则: V-FETCH已静默，正常监控已启用
```

#### 通知2: 切换完成通知

```
标题: [DSHE V86-RC2] DEP恢复切换完成 — 全量恢复确认

内容:
  时间: {switch_complete_time}
  状态: ✅ 切换完成
  验证: 178/178 指标FULLY_AVAILABLE
  面板: 8/8 面板状态🟢FULLY_AVAILABLE
  告警: 0误报/0漏报
  降级: 全部退出
  TTL: 正常刷新

  后续观测: 7天稳定期，每周一巡检
  报告: v86_rc2_dshe_recovery_verify_report.md
```

### 6.2 通知渠道

| 渠道 | 接收方 | 通知类型 |
|------|--------|---------|
| 邮件 | DSHB+DSHE+HERMES团队 | 恢复通知+切换完成 |
| Slack/企业微信 | 运维值班群 | 恢复通知 |
| 工单系统 | Gate评审组 | 切换完成 |
| 文档 | 运维手册更新 | 切换完成 |

### 6.3 通知时序

| 时间点 | 通知内容 | 渠道 |
|--------|---------|------|
| T+5h | DEP恢复检测通知 | Slack+邮件 |
| T+8h | 切换完成通知 | 邮件+工单 |
| T+24h | 恢复后首轮验证结果 | 邮件 |
| T+7d | 恢复观测结束报告 | 邮件+文档 |

---

## 7. 回滚SOP

### 7.1 回滚触发条件

| # | 触发条件 | 严重程度 | 回滚动作 |
|---|---------|---------|---------|
| 1 | 切换后面板数据异常 | P0 | 立即回滚至DEPENDENCY_BLOCK |
| 2 | 告警误报率>10% | P1 | 回滚告警规则 |
| 3 | 数据完整性<178/178 | P0 | 回滚面板状态 |
| 4 | 降级策略未完全退出 | P1 | 重新执行退出 |
| 5 | 业务侧发现数据不一致 | P0 | 全面回滚 |

### 7.2 回滚步骤

```
回滚步骤 (反向执行):
  1. 面板状态切换回 🟡DEPENDENCY_BLOCK
  2. 告警规则切换回V-FETCH系列
  3. 降级策略重新启用 L1→L2→L3
  4. 通知业务侧回滚
  5. 记录回滚原因
  6. 更新HERMES审计记录
```

### 7.3 回滚验证

| 检查项 | 预期 |
|--------|------|
| 面板徽章 | 🟡 DEPENDENCY_BLOCKED |
| 横幅 | 数据获取受限 |
| 告警 | V-FETCH-01~04触发 |
| 降级 | L1缓存降级启用 |
| 日志 | data_fetch_status=DEPENDENCY_BLOCK |

---

## 8. 检查清单

### 8.1 切换前检查

- [ ] 快照检测到data_fetchable=TRUE
- [ ] 双维度联合校验0误判
- [ ] HERMES预审通过
- [ ] DSHB底层确认
- [ ] Gate评审8项准入
- [ ] 回滚预案就绪
- [ ] 通知模板准备

### 8.2 切换中检查

- [ ] L3面板隔离退出
- [ ] L2静态降级退出
- [ ] L1缓存降级退出
- [ ] 面板状态切换
- [ ] 告警规则切换
- [ ] 缓存清理
- [ ] 日志记录

### 8.3 切换后检查

- [ ] 面板数据实时刷新
- [ ] 告警0误报
- [ ] 告警0漏报
- [ ] 降级策略全部退出
- [ ] 业务侧通知
- [ ] HERMES审计记录
- [ ] 观测日志更新

---

*Generated: 2026-10-15*
*Task: DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.4*
*Branch: feature/v85-chart-template*
*Status: T3.4 COMPLETE — DEP恢复切换SOP已完善*
