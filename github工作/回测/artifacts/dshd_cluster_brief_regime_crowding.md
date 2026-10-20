# DSHD 监控文档 — Regime识别 + 拥挤度监控 (独立持久化)

> 生成时间: 2026-10-20T11:42:17+08:00
> 任务: DSHD-TASK-042-MONITOR
> 令牌: DSHD-TASK042-TOKEN
> 模式: AUDIT_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD
> 注意: 本文件独立于 P81 集群简报 (dshd_cluster_brief.md), 不会被 5 分钟巡检覆盖。
> 数据真源: p82_regime_state.json + p82_crowding_state.json + p82_crowding_baseline.json

---

## 十二、Regime 行情自动识别

> 检测器: DSHD-TASK039-REGIME-DETECT
> 版本: 1.0.0
> 锁定: True
> TASK-042 巡检时间: 2026-10-20T11:42:17+08:00

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
> 基线运行次数: 9
> TASK-042 巡检时间: 2026-10-20T11:42:17+08:00

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
| 基线运行次数 | 9 |

---

## 十四、TASK-042 监控治理状态

> 任务: DSHD-TASK-042-MONITOR
> 巡检时间: 2026-10-20T11:42:17+08:00
> 令牌: DSHD-TASK042-TOKEN

### 14.1 监控覆盖

| 子任务 | 状态 | 详情 |
|---|---|---|
| P0 事件流监听 | ✅ | DSHC 8个事件文件, DSHA=NO |
| P1 进程巡检 | ✅ | P81 Watch=RUN, P80=ALIVE |
| P1① 内存软重启 | ✅ | 0 次重启触发 |
| P1② 文件锁强制 | ✅ | 全程带锁读写, 无降级fallback |
| P2 拥挤度计算 | ✅ | P90=47.6, 告警=7因子 |
| P3 Regime识别 | ✅ | DOWN=INSUFFICIENT_DATA, 20天窗口强制 |
| P4 风险台账 | ✅ | v4.2.0, 23条, 清理0条重复 |
| P5 文档维护 | ✅ | 本文件已更新 |
| P6 P80保活 | ✅ | P80 Phase2=ALIVE |

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
*本文件由 DSHD-TASK-042-MONITOR 自动生成*
*2026-10-20T11:42:17+08:00*
---

## TASK-047 回测引擎升级+动态权重优化 — 拥挤度/风险推送

> 任务: DSHA-TASK047-ENGINE-OPTIMIZE
> 时间: 2026-10-20T11:44:31+08:00
> 令牌: DSHD-TASK047-CROWDING-PUSH-TOKEN
> 模式: AUDIT_READ_ONLY · wind_api_calls=0
> 引擎: Set-E (threshold=0.3, rebalance=5, vol=0.15)

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

### 动态权重优化 (P4)

| Alpha | 夏普 | 收益 | 拥挤度 |
|---|---|---|---|
| alpha=0.3 | 3.1630 | 0.2195 | 1.1100x |
| alpha=0.4 | 3.1953 | 0.2152 | 1.0808x |
| alpha=0.5 | 3.2892 | 0.2217 | 1.0561x |
| alpha=0.6 | 3.4293 | 0.2298 | 1.0359x |
| alpha=0.7 | 3.3316 | 0.2201 | 1.0202x |

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
| 阈值 | 1.5x |
| 告警 | ✅ 未触发 |

### 回测风险指标 (Set-E引擎)

| 方案 | 最大回撤 | 夏普 | 收益 | 回撤阈值 |
|---|---|---|---|---|
| group_a_equal_weight | -0.0171 | 2.9109 | 0.1867 | ✅ |
| group_b_fixed_ic_weight | -0.0193 | 2.8899 | 0.2014 | ✅ |
| group_c_dynamic_regime | -0.0180 | 3.4293 | 0.2298 | ✅ |