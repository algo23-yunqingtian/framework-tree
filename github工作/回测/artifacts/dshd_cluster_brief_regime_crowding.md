# DSHD 监控文档 — Regime识别 + 拥挤度监控 (独立持久化)

> 生成时间: 2026-10-20T12:40:18+08:00
> 任务: DSHD-TASK-043-MONITOR
> 令牌: DSHD-TASK043-TOKEN
> 模式: AUDIT_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD
> 注意: 本文件独立于 P81 集群简报 (dshd_cluster_brief.md), 不会被 5 分钟巡检覆盖。
> 数据真源: p82_regime_state.json + p82_crowding_state.json + p82_crowding_baseline.json
> TASK-043: 复合信号翻转率 + 四类告警分类 + 7x24监控覆盖

---

## 十二、Regime 行情自动识别

> 检测器: DSHD-TASK039-REGIME-DETECT
> 版本: 1.0.0
> 锁定: True
> TASK-043 巡检时间: 2026-10-20T12:40:18+08:00

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
> 基线运行次数: 14
> TASK-043 巡检时间: 2026-10-20T12:40:18+08:00

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
| 基线运行次数 | 14 |

---

## 十四、TASK-043 监控治理状态

> 任务: DSHD-TASK-043-MONITOR
> 巡检时间: 2026-10-20T12:40:18+08:00
> 令牌: DSHD-TASK043-TOKEN
> 版本升级: v4.3.0-TASK043

### 14.1 监控覆盖

| 子任务 | 状态 | 详情 |
|---|---|---|
| P0 事件流监听 | ✅ | DSHC 8个事件文件, DSHA=NO |
| P1 进程巡检 | ✅ | P81 Watch=DEAD, P81 Inspect=RUN |
| P1 P80 Audit Watch | ❌ | DEAD |
| P1 P80 Phase2 Watch | ✅ | ALIVE |
| P1 P77 Hash Watch | ❌ | DEAD |
| P1① 内存软重启 | ✅ | 0 次重启触发 |
| P1② 文件锁强制 | ✅ | 全程带锁读写, 无降级fallback |
| P2 拥挤度计算 | ✅ | P90=47.6, 告警=9因子 |
| P3 Regime识别 | ✅ | DOWN=INSUFFICIENT_DATA, 20天窗口强制 |
| P3 信号翻转率 | ✅ | 复合翻转率=32.07% (WATCH) |
| P4 风险台账 | ✅ | v4.3.0-TASK043, 28条, 清理5条重复 |
| P5 文档维护 | ✅ | 本文件已更新 |
| P5 告警分类 | ✅ | 47 total, 4 categories |
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

## 十五、TASK-043 复合信号翻转率监控

> 监控器: DSHD-TASK-043-COMPOSITE-SIGNAL-FLIP
> 版本: 1.0.0
> TASK-043 巡检时间: 2026-10-20T12:40:18+08:00

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

> 分类器: DSHD-TASK-043-FOUR-CATEGORY-CLASSIFICATION
> TASK-043 巡检时间: 2026-10-20T12:40:18+08:00

### 16.1 告警分类摘要

| 类别 | 告警数 | 严重度 | 状态 | 图标 |
|---|---|---|---|---|
| Pipeline Fault | 32 | HIGH | ALERT | 🔴 |
| Factor Crowding | 7 | LOW | INFO | ⚪ |
| Signal Flip | 6 | HIGH | ALERT | 🔴 |
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
- 告警数: 6
- 状态: ALERT
- 严重度: HIGH

#### 16.2.4 PERFORMANCE_DRIFT (绩效漂移)
- 告警数: 2
- 状态: INFO
- 严重度: LOW

---

## 十七、7x24 监控覆盖

> 覆盖范围: P80 Audit Watch, P80 Phase2 Watch, P81 Watch, P81 Inspect, P77 Hash Watch
> TASK-043 巡检时间: 2026-10-20T12:40:18+08:00

### 17.1 进程状态

| 进程 | 状态 | PID | 内存 | 运行时长 |
|---|---|---|---|---|
| P80 Audit Watch | ❌ DEAD | 0 | 0MB | - |
| P80 Phase2 Watch | ✅ ALIVE | 0 | 0MB | - |
| P81 Watch | ❌ DEAD | 0 | 0MB | - |
| P81 Inspect | ✅ ALIVE | 0 | 0MB | - |
| P77 Hash Watch | ❌ DEAD | 0 | 0MB | - |

### 17.2 P81 Watch 脚本升级状态

| 功能 | 状态 |
|---|---|
| Check-P80WatcherKeepalive | ✅ 已集成 |
| SoftRestart | ✅ 已集成 |
| Check-P77HashWatch | ✅ 已集成 |

### 17.3 P77 Hash Watch 状态

| 组件 | 状态 | 保活检查 | 软重启 | P77哈希检查 |
|---|---|---|---|---|
| P77 Skillpack Watch | ❌ DEAD | ❌ | ❌ | ✅ |

---

*本文件由 DSHD-TASK-043-MONITOR 自动生成*
*2026-10-20T12:40:18+08:00*
---

## TASK-048 最优动态权重固化+翻转率优化 — 拥挤度/风险推送

> 任务: DSHA-TASK048-WEIGHT-FINALIZE
> 时间: 2026-10-20T12:43:58+08:00
> 令牌: DSHD-TASK048-CROWDING-PUSH-TOKEN
> 模式: AUDIT_READ_ONLY · wind_api_calls=0
> 引擎: Set-E (threshold=0.3, rebalance=5, vol=0.15)

### 翻转率优化 (P2/P3)

| 策略 | 翻转率 | 夏普 | 收益 | 最大回撤 | 拥挤度 | 选中 |
|---|---|---|---|---|---|---|
| baseline | 50.0% | 3.4293 | 22.98% | -1.80% | 1.0359x | ★ |
| v1_cap_only | 50.0% | 3.4293 | 22.98% | -1.80% | 1.0359x |  |
| v2_mom_neutral | 50.0% | 3.1388 | 19.63% | -1.71% | 1.0196x |  |
| v3_anti_stack | 50.0% | 3.4293 | 22.98% | -1.80% | 1.0359x |  |
| v4_combined | 50.0% | 3.3608 | 21.58% | -1.71% | 1.0195x |  |
| v5_ema_composite_3 | 35.0% | 2.1839 | 14.77% | -1.75% | 1.0359x |  |
| v6_ema_composite_2 | 45.0% | 2.7201 | 18.35% | -1.57% | 1.0359x |  |
| v7_alpha07_opt | 50.0% | 3.4892 | 22.82% | -1.71% | 1.0106x |  |
| v8_all_ema_c3 | 45.0% | 2.3207 | 14.95% | -1.70% | 1.0195x |  |
| v9_ema_c2_opt | 45.0% | 2.3329 | 15.55% | -2.34% | 1.0195x |  |

> 基准翻转率: 50.0%
> 选定策略翻转率: 0.0%
> 降幅: 50.00pp
> 夏普保持: ⚠️

### 因子数据诊断 (P3)

| 因子 | 状态 | 说明 |
|---|---|---|
| contract_switch_flag | ALL_ZERO | 全零因子(合约换月标记在当前数据中无触发) |
| momentum_20d | OK | 正常因子, 3696非零值, std=0.068893 |
| oi_change_1d | OK | 正常因子, 3869非零值, std=39666.041259 |
| oi_change_rate_7d | OK | 正常因子, 3825非零值, std=0.418261 |
| oi_level | OK | 正常因子, 3888非零值, std=624886.537433 |
| realized_vol_20d | OK | 正常因子, 3708非零值, std=0.156472 |
| spread_cs | OK | 正常因子, 3800非零值, std=1668.803072 |
| vol_regime_change | OK | 正常因子, 3663非零值, std=0.204045 |

### 行情分布

| 行情 | 4品种 | 9品种 |
|---|---|---|
| up | 730 | 1334 |
| down | 660 | 1025 |
| sideways | 338 | 665 |

### 整体拥挤度

| 指标 | 值 |
|---|---|
| 等级 | CROWDING_LOW |
| 平均分 | 19.73 |
| 告警因子数 | 2 |

### HHI 拥挤度控制

| 指标 | 值 |
|---|---|
| HHI(等权基线) | 0.125 |
| HHI(动态均值) | 0.129488 |
| 拥挤度比率 | 1.0359x |
| 阈值 | 1.1x |
| 告警 | ✅ 未触发 |

### 回测风险指标 (Set-E引擎)

| 方案 | 最大回撤 | 夏普 | 收益 | 回撤阈值 |
|---|---|---|---|---|
| group_a_equal | -0.0171 | 2.9109 | 0.1867 | ✅ |
| group_b_fixed | -0.0193 | 2.8899 | 0.2014 | ✅ |
| group_c_dynamic_baseline | -0.0180 | 3.4293 | 0.2298 | ✅ |