# DSHD 监控文档 — Regime识别 + 拥挤度监控 (独立持久化)

> 生成时间: 2026-10-20T17:16:21+08:00
> 任务: DSHD-TASK-046-MONITOR
> 令牌: DSHD-TASK046-TOKEN
> 模式: AUDIT_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD
> 注意: 本文件独立于 P81 集群简报 (dshd_cluster_brief.md), 不会被 5 分钟巡检覆盖。
> 数据真源: p82_regime_state.json + p82_crowding_state.json + p82_crowding_baseline.json
> TASK-044: 进程自愈 + 双窗口翻转率 + 告警治理

---

## 十二、Regime 行情自动识别

> 检测器: DSHD-TASK039-REGIME-DETECT
> 版本: 1.0.0
> 锁定: True
> TASK-044 巡检时间: 2026-10-20T17:16:21+08:00

### 12.1 行情分布

| 行情 | 天数 | 占比 | 状态 |
|---|---|---|---|
| UP | 37 | 8.4% |  |
| DOWN | 7 | 1.6% | ⚠ INSUFFICIENT_DATA |
| SIDEWAYS | 386 | 88.1% |  |
| UNKNOWN | 2 | 0.5% | 边界情况 |

### 12.2 DOWN 行情处理

> DOWN 行情天数: 7, 低于 20 天最小窗口
> 处理策略: INSUFFICIENT_DATA, 不产生 UNKNOWN 无效告警
> 20天最小窗口规则: 强制执行

---

## 十三、因子拥挤度监控

> 监控器: DSHD-TASK039-CROWDING-MONITOR
> 版本: 1.0.0
> P90 基线阈值: 47.6
> 基线运行次数: 19
> TASK-044 巡检时间: 2026-10-20T17:16:21+08:00

### 13.1 告警阈值

| 参数 | 值 |
|---|---|
| 拥挤度告警分位数 | 90% |
| 方向性集中度阈值 | 0.7 |
| 值集中度HHI阈值 | 0.25 |
| IC衰减阈值 | 0.3 |
| P90分位数基线 | 47.6 |
| 告警严重度 | MEDIUM |

### 13.2 因子拥挤度详情

| 因子 | 拥挤度 | P90阈值 | 告警标志 | 状态 |
|---|---|---|---|---|
| oi_change_1d | 37.1 | 47.6 | VALUE_CONCENTRATED | ⚠ MEDIUM |
| oi_change_rate_7d | 20.19 | 47.6 | VALUE_CONCENTRATED | ⚠ MEDIUM |
| oi_level | 46.84 | 47.6 | DIRECTIONAL_CROWDED | ⚠ MEDIUM |
| realized_vol_20d | 47.58 | 47.6 | DIRECTIONAL_CROWDED,VALUE_CONCENTRATED | ⚠ MEDIUM |
| vol_regime_change | 15.64 | 47.6 | VALUE_CONCENTRATED | ⚠ MEDIUM |
| spread_cs | 24.92 | 47.6 | VALUE_CONCENTRATED | ⚠ MEDIUM |
| momentum_20d | 16.94 | 47.6 | VALUE_CONCENTRATED | ⚠ MEDIUM |

### 13.3 组合整体拥挤度

| 指标 | 值 |
|---|---|
| 整体等级 | CROWDING_LOW |
| 告警因子数 | 7 |
| P90基线阈值 | 47.6 |
| 基线运行次数 | 19 |

---

## 十四、TASK-046 监控治理状态

> 任务: DSHD-TASK-046-MONITOR
> 巡检时间: 2026-10-20T17:16:21+08:00
> 令牌: DSHD-TASK046-TOKEN
> 版本升级: v4.4.0-TASK044 -> v4.4.1-TASK046

### 14.1 监控覆盖

| 子任务 | 状态 | 详情 |
|---|---|---|
| P0 事件流监听 | ✅ | DSHC 8个事件文件, DSHA=NO |
| P1 进程巡检 | ✅ | P81 Watch=RUN, P81 Inspect=DEAD |
| P1 P80 Audit Watch | ✅ | ALIVE |
| P1 P80 Phase2 Watch | ❌ | DEAD |
| P1 P77 Hash Watch | ✅ | ALIVE |
| P1① 内存软重启 | ✅ | 0 次重启触发 |
| P1② 文件锁强制 | ✅ | 全程带锁读写, 无降级fallback |
| P2 拥挤度计算 | ✅ | P90=47.6, 告警=9因子 |
| P3 Regime识别 | ✅ | DOWN=INSUFFICIENT_DATA, 20天窗口强制 |
| P3 信号翻转率 | ✅ | 复合翻转率=32.07% (WATCH) |
| P4 风险台账 | ✅ | v4.4.1-TASK046, 30条, 清理7条重复 |
| P5 文档维护 | ✅ | 本文件已更新 |
| P5 告警分类 | ✅ | 52 total, 4 categories |
| P6 P80/P81/P77保活 | ✅ | 7x24覆盖 |

### 14.2 内存超限处理

| PID | 内存 | 阈值 | 动作 | 重启成功 |
|---|---|---|---|---|
| - | - | 256MB | NO_ALERT | - |

### 14.3 软重启执行记录

| PID | 重启前内存 | 已停止 | 已重启 | 错误 |
|---|---|---|---|---|
| - | - | - | - | - |

### 14.4 文件锁状态

| 项目 | 状态 |
|---|---|
| p81_file_lock.ps1 | ✅ EXISTS (7763 B) |
| 写入锁超时 | 30s |
| 重试次数 | 10 |
| Fallback | ❌ 禁用 (强制带锁) |

### 14.5 红线约束

| 约束 | 状态 |
|---|---|
| wind_api_calls | 0 ✅ |
| Gate | CLOSED/HOLD ✅ |
| Release | NOT_ISSUED ✅ |
| IC翻转门禁 | 硬锁定不变 ✅ |
| 绩效漂移门禁 | 硬锁定不变 ✅ |
| 文件锁保护 | 30s超时 ✅ 强制带锁 ✅ |

---

## 十五、TASK-046 复合信号翻转率监控 (20d)

> 监控器: DSHD-TASK-046-COMPOSITE-SIGNAL-FLIP
> 版本: 1.0.0
> TASK-044 巡检时间: 2026-10-20T17:16:21+08:00

### 15.1 翻转率阈值

| 参数 | 值 |
|---|---|
| ALERT 阈值 | 50% |
| WATCH 阈值 | 30% |
| 复合计算 | 所有因子翻转率的算术平均 |

### 15.2 因子翻转率详情

| 因子 | 翻转率 | 状态 | 图标 |
|---|---|---|---|
| oi_change_1d | 30.00% | WATCH | 🟡 |
| oi_change_rate_7d | 45.00% | WATCH | 🟡 |
| oi_level | 50.00% | ALERT | 🔴 |
| realized_vol_20d | 63.16% | ALERT | 🔴 |
| vol_regime_change | 47.37% | WATCH | 🟡 |
| spread_cs | 0.00% | STABLE | 🟢 |
| momentum_20d | 21.05% | STABLE | 🟢 |
| contract_switch_flag | 0.00% | STABLE | 🟢 |
| **COMPOSITE** | **32.07%** | **WATCH** | 🟡 |

### 15.3 复合翻转率摘要

| 指标 | 值 |
|---|---|
| 复合翻转率 | 32.07% |
| 整体状态 | WATCH |
| ALERT因子数 | 2 |
| WATCH因子数 | 3 |
| STABLE因子数 | 3 |
| 监控因子总数 | 8 |

---

## 十六、四类告警分类

> 分类器: DSHD-TASK-046-FOUR-CATEGORY-CLASSIFICATION
> TASK-044 巡检时间: 2026-10-20T17:16:21+08:00

### 16.1 告警分类摘要

| 类别 | 告警数 | 严重度 | 状态 | 图标 |
|---|---|---|---|---|
| Pipeline Fault | 32 | HIGH | ALERT | 🔴 |
| Factor Crowding | 7 | LOW | INFO | ⚪ |
| Signal Flip | 11 | HIGH | ALERT | 🔴 |
| Performance Drift | 2 | LOW | INFO | ⚪ |

### 16.2 各类别详情

#### 16.2.1 PIPELINE_FAULT (管道故障)
- 告警数: 32
- 状态: ALERT
- 严重度: HIGH

#### 16.2.2 FACTOR_CROWDING (因子拥挤度)
- 告警数: 7
- 状态: INFO
- 严重度: LOW

#### 16.2.3 SIGNAL_FLIP (信号翻转)
- 告警数: 11
- 状态: ALERT
- 严重度: HIGH

#### 16.2.4 PERFORMANCE_DRIFT (绩效漂移)
- 告警数: 2
- 状态: INFO
- 严重度: LOW

---

## 十七、7x24 监控覆盖

> 覆盖范围: P80 Audit Watch, P80 Phase2 Watch, P81 Watch, P81 Inspect, P77 Hash Watch
> TASK-044 巡检时间: 2026-10-20T17:16:21+08:00

### 17.1 进程状态

| 进程 | 状态 | PID | 内存 | 运行时长 |
|---|---|---|---|---|
| P80 Audit Watch | ✅ ALIVE | 0 | 0MB | - |
| P80 Phase2 Watch | ❌ DEAD | 0 | 0MB | - |
| P81 Watch | ✅ ALIVE | 0 | 0MB | - |
| P81 Inspect | ❌ DEAD | 0 | 0MB | - |
| P77 Hash Watch | ✅ ALIVE | 0 | 0MB | - |

### 17.2 P81 Watch 脚本升级状态

| 功能 | 状态 |
|---|---|
| Check-P80WatcherKeepalive | ✅ 已集成 |
| SoftRestart | ✅ 已集成 |
| Check-P77HashWatch | ✅ 已集成 |

### 17.3 P77 Hash Watch 状态

| 组件 | 状态 | 保活检查 | 软重启 | P77哈希检查 |
|---|---|---|---|---|
| P77 Skillpack Watch | ✅ ALIVE | ❌ | ❌ | ✅ |

---

## 18. TASK052 — V3策略预发布评审包 + 上线门禁校验

> 生成时间: 2026-10-20T17:16:56+08:00
> Token: DSHA-TASK052-V3-REVIEW-PACKAGE-TOKEN
> 模式: READ_ONLY | wind=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED
> 评审状态: **READY_FOR_REVIEW**

### 18.1 上线门禁核验结果 — 6/6 PASS

| 门禁 | 阈值 | 实际值 | 余量 | 结果 |
|------|------|--------|------|------|
| Gate 1: 夏普比率 | >=3.4 | 3.4890 | +0.0890 | PASS |
| Gate 2: 拥挤度 | <=1.1x | 1.0359x | +0.0641 | PASS |
| Gate 3: 高相关因子对 | =0 | 0 | — | PASS |
| Gate 4: 回放偏差 | <=±0.005 | 0.000000 | +0.005 | PASS |
| Gate 5: 压力/边界拥挤度 | <=1.1x | 1.0359x | +0.0641 | PASS |
| Gate 6: 审计链路 | 完整 | 完整 | — | PASS |

### 18.2 评审包内容 (15文件, 33,280B)

| 类别 | 文件 | 说明 |
|------|------|------|
| 策略定义 | final_weight_rules.json | V3冻结权重规则 |
| 回测指标 | dual_window_backtest_metrics.json | 双窗口回测 |
| 风险验证 | risk_validation_final.json | 拥挤度/HHI/相关性 |
| 版本冻结 | version_freeze_document.json | 5个变体历史 |
| 验收文档 | v3_acceptance_document.json | TASK051验证 |
| 换月因子 | contract_switch_flag_final.json | 换月标记因子 |
| 参数对比 | tradeoff_evaluation.json, dual_window_comparison_report.json, comparison_backtest_metrics.json | 参数对比分析 |
| 生产配置 | factor_weight_prod.json, factor_enable_config.json | SHA指纹验证 |
| 评审摘要 | p1_review_summary.json | TASK049-051汇总 |
| 门禁回执 | gate_summary_receipt.json | 6门禁结果 |
| 运维文档 | v3_strategy_om_documentation.md | 信号逻辑/指标/告警/兜底 |
| 分支冻结 | branch_freeze_marker.json | 策略侧冻结标记 |
| DSHD推送 | dshd_task052_v3_review_package_push.json | 评审就绪推送 |

### 18.3 安全约束确认

| 约束 | 状态 |
|------|------|
| V3策略未修改 | YES |
| 因子定义未修改 | YES |
| 引擎参数未修改 | YES |
| 生产配置未修改 | YES (SHA一致) |
| 只读回放模式 | YES |
| wind_api_calls=0 | YES |
| Gate=CLOSED/HOLD | YES |
| Release=NOT_ISSUED | YES |
| 分支策略侧冻结 | STRATEGY_SIDE_FROZEN |

---

*本文件由 DSHD-TASK-046-MONITOR 自动生成*
*2026-10-20T17:16:21+08:00*
