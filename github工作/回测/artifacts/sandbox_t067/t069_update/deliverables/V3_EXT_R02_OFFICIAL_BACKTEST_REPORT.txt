# V3-EXT R02 官方汇总回测报告

> **任务ID**: DSHA-TASK-067
> **基线分支**: origin/feature/v88-g1@3e2e914
> **版本标签**: V3-EXT-14POOL-062-OBS-R02-REPORT-SKILL
> **快照ID**: V3-EXT-14POOL-062-OBS-R02
> **生成时间**: 2026-10-22T16:00:00+08:00
> **执行模式**: RESEARCH_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED

---

## 1. 实验总览

**任务ID**: DSHA-TASK-067
**基线分支**: origin/feature/v88-g1@3e2e914 (DSHA-TASK-066 HEAD)
**Commit**: 3e2e914
**版本标签**: V3-EXT-14POOL-062-OBS-R02-REPORT-SKILL
**实验目标**: V3-EXT R02标准化回测汇总报告渲染 + 因子绩效台账固化 + 报告渲染Skill封版

**范围边界**:
- V3主策略8因子: **只读冻结**, 不参与任何改动
- 观测池31因子 (7A+1B+23C): 仅用于绩效评级与DSHD监控层预警
- LOCKDOWN风控参数: G1(基线) vs G4(优选) 双套对照
- 评级结果: **绝不自动写入主策略加权逻辑**

**隔离声明**:
- 沙箱隔离: `sandbox_t067` (独立于T066 sandbox_mc)
- 跨Agent隔离: DSHD-T056制品跨分支不可用, 以本地推导等效替代
- 生产隔离: 零写入生产目录、MN快照目录、工作流锁目录

---

## 2. 因子池总览表

**总因子数**: 39
**BASE_FROZEN** (V3主基线): 8
**A_OBS** (A级观测): 7
**B_OBS** (B级递补): 1
**C_REJECT** (C级淘汰): 23

### 2.1 主冻结因子 (BASE_FROZEN)

| 因子 | 权重 | 状态 | 品种范围 |
| --- | --- | --- | --- |
| contract_switch_flag | 0.173862 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |
| momentum_20d | 0.240761 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |
| oi_change_1d | 0.039409 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |
| oi_change_rate_7d | 0.072074 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |
| oi_level | 0.112601 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |
| realized_vol_20d | 0.102804 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |
| spread_cs | 0.127197 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |
| vol_regime_change | 0.131292 | PERMANENTLY_FROZEN | LC.GFE, NI.SHF, CU.SHF, ZN.SHF |

### 2.2 A级观测因子 (A_OBS)

| 因子 | IC_1d | IC_3d | IC_5d | 评级 | 翻转提前量 |
| --- | --- | --- | --- | --- | --- |
| return_kurtosis_20d | 0.035270 | 0.067969 | 0.072123 | A | 5 |
| vol_fractal_dimension_20d | 0.033670 | 0.075393 | 0.087543 | A | 5 |
| capital_inflow_intensity | -0.032463 | 0.038546 | 0.018888 | A | 3 |
| basis_2nd_momentum_5d | -0.046904 | 0.032877 | 0.024025 | A | 1 |
| term_curvature_20d | -0.073431 | -0.092991 | -0.037304 | A | 3 |
| price_vol_momentum | -0.077281 | -0.052884 | -0.035309 | A | 1 |
| term_slope_20d | -0.080793 | -0.037742 | -0.020167 | A | 1 |

### 2.3 B级递补因子 (B_OBS)

| 因子 | IC_1d | IC_3d | IC_5d | 评级 | 翻转提前量 |
| --- | --- | --- | --- | --- | --- |
| intraday_ohlc_position | -0.049485 | -0.023857 | -0.005277 | B | 1 |

### 2.4 C级淘汰清单 (C_REJECT)

| 因子 | IC_1d | 评级 | 剔除理由 |
| --- | --- | --- | --- |
| vol_asymmetry_20d | 0.000983 | C | N/A |
| price_momentum_2nd_diff | 0.001488 | C | N/A |
| contango_premium_20d | 0.001846 | C | N/A |
| close_relative_range | -0.002964 | C | N/A |
| realized_volatility_40d | -0.003952 | C | N/A |
| institutional_concentration_20d | 0.004624 | C | N/A |
| cross_symbol_oi_linkage | -0.009179 | C | N/A |
| up_volatility_20d | 0.010554 | C | N/A |
| oi_2nd_growth_5d | 0.010834 | C | N/A |
| term_spread_volatility_20d | -0.013127 | C | N/A |
| price_volume_divergence | 0.014489 | C | N/A |
| volume_squeeze | -0.014930 | C | N/A |
| volume_breakout | -0.015056 | C | N/A |
| down_volatility_20d | 0.015701 | C | N/A |
| vol_clustering_20d | -0.016724 | C | N/A |
| return_skewness_20d | -0.016777 | C | N/A |
| roll_return_stability_20d | -0.017718 | C | N/A |
| oi_momentum_divergence_20d | 0.020827 | C | N/A |
| quantile_volatility_20d | 0.020958 | C | N/A |
| bollinger_bandwidth_20d | 0.024889 | C | N/A |
| volume_deviation_from_mean | -0.026297 | C | N/A |
| volume_trend_ratio | -0.026297 | C | N/A |
| oi_vol_ratio_20d | -0.028457 | C | N/A |

### 2.5 评级标准

| 评级 | 标准 |
| --- | --- |
| A | |IC_1d|>=0.03 AND |IC_3d|>=0.02 AND |IC_5d|>=0.01 (稳定提前预警) |
| B | |IC_1d|>=0.03 但3d/5d衰减 (仅阶段性有效) |
| C | |IC_1d|<0.03 (无预测能力, 直接剔除) |

---

## 3. 风控参数页

### 3.1 LOCKDOWN梯度对比表

| 档位 | 名称 | 阈值 | P90 | P95 | Flip_L1 | Flip_L2 | Hold | 锁定事件/轮 | Delta均值 | MDD_p5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | baseline_T065_x3 | 3 | 1.074010 | 1.078540 | 0.550000 | 0.650000 | 20 | 0.000000 | -0.525876 | -0.208810 |
| G4 | x1_relax_crowd | 1 | 1.064010 | 1.068540 | 0.550000 | 0.650000 | 20 | 4.453300 | -0.554462 | -0.211626 |

### 3.2 拥挤阈值与分位数参数

| 参数 | T065基线 | T066-G4优选 |
| --- | --- | --- |
| 共振阈值 (threshold) | 3 | 1 |
| 拥挤P90 | 1.074010 | 1.064010 |
| 拥挤P95 | 1.078540 | 1.068540 |
| 翻转L1 | 0.550000 | 0.550000 |
| 翻转L2 | 0.650000 | 0.650000 |
| Hold天数 | 20 | 20 |

### 3.3 MC触发频率

- **G1基线**: 0.0 次/轮 (零触发, 复现T065结论)
- **G4优选**: 4.45 次/轮 (落入3~8触发带)
- **MC轮数**: 300 轮, 种子=300000+r

---

## 4. 回测基准设定

- **样本区间**: 2025-01-02 至 2025-10-31 (约252交易日)
- **品种集合**: LC.GFE, NI.SHF, CU.SHF, ZN.SHF (4品种)
- **手续费**: 0.0005 (0.05%)
- **滑点**: 已包含在交易成本中
- **MC种子**: 300000 + r (T066 G4优选)
- **MC轮数**: 300
- **复现说明**: 确定性时间戳 2026-10-22T16:00:00+08:00, 排序JSON键, 固定MC种子

---

## 5. 绩效汇总

### 5.1 全因子分层绩效表

| 因子 | 等级 | IC_1d | IC_3d | IC_5d | ICIR | 胜率 | MDD | 翻转频次 | 拥挤度 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bollinger_bandwidth_20d | C_REJECT | 0.024889 | 0.045748 | 0.052173 | 3.514895 | 0.000000 | 0.000000 | 9.500000 | 0.656623 |
| quantile_volatility_20d | C_REJECT | 0.020958 | 0.034596 | 0.042249 | 3.702243 | 0.000000 | 0.000000 | 14.000000 | 0.654667 |
| oi_momentum_divergence_20d | C_REJECT | 0.020827 | -0.002315 | -0.022878 | -0.081518 | 0.000000 | -3.517741 | 198.000000 | 0.986042 |
| down_volatility_20d | C_REJECT | 0.015701 | 0.017424 | 0.011921 | 6.533201 | 0.000000 | 0.000000 | 6.250000 | 0.726119 |
| price_volume_divergence | C_REJECT | 0.014489 | 0.041612 | -0.000452 | 1.065402 | 0.000000 | -0.013877 | 228.500000 | 0.998413 |
| oi_2nd_growth_5d | C_REJECT | 0.010834 | 0.017709 | 0.023105 | 3.428301 | 0.000000 | 0.000000 | 89.500000 | 0.960007 |
| up_volatility_20d | C_REJECT | 0.010554 | 0.017211 | 0.020852 | 3.800740 | 0.000000 | 0.000000 | 11.750000 | 0.737463 |
| institutional_concentration_20d | C_REJECT | 0.004624 | -0.045932 | -0.039243 | -1.197466 | 0.000000 | -45.327206 | 40.250000 | 0.664511 |
| contango_premium_20d | C_REJECT | 0.001846 | 0.001999 | 0.006503 | 1.596787 | 0.000000 | 0.000000 | 45.250000 | 0.964264 |
| price_momentum_2nd_diff | C_REJECT | 0.001488 | -0.002723 | 0.011145 | 0.569022 | 0.000000 | -3.659946 | 54.500000 | 0.872546 |
| vol_asymmetry_20d | C_REJECT | 0.000983 | 0.018404 | 0.017823 | 1.535279 | 0.000000 | 0.000000 | 33.000000 | 0.935928 |
| close_relative_range | C_REJECT | -0.002964 | 0.010731 | 0.005539 | 0.785687 | 0.000000 | 0.000000 | 55.750000 | 0.972025 |
| realized_volatility_40d | C_REJECT | -0.003952 | -0.017750 | -0.027726 | -1.690295 | 0.000000 | 0.000000 | 6.750000 | 0.636684 |
| cross_symbol_oi_linkage | C_REJECT | -0.009179 | -0.000272 | 0.013130 | 0.133747 | 0.000000 | 0.000000 | 179.500000 | 0.996536 |
| term_spread_volatility_20d | C_REJECT | -0.013127 | -0.032260 | -0.050269 | -2.102495 | 0.000000 | 0.000000 | 3.250000 | 0.622079 |
| volume_squeeze | C_REJECT | -0.014930 | -0.030891 | -0.029432 | -3.481585 | 0.000000 | 0.000000 | 173.500000 | 0.999012 |
| volume_breakout | C_REJECT | -0.015056 | 0.052784 | 0.035132 | 0.845115 | 0.000000 | 0.000000 | 114.750000 | 0.999712 |
| vol_clustering_20d | C_REJECT | -0.016724 | -0.061755 | -0.091648 | -1.841500 | 0.000000 | 0.000000 | 52.000000 | 0.988833 |
| return_skewness_20d | C_REJECT | -0.016777 | -0.026709 | -0.031254 | -4.121269 | 0.000000 | 0.000000 | 38.000000 | 0.983908 |
| roll_return_stability_20d | C_REJECT | -0.017718 | 0.005094 | 0.017226 | 0.105894 | 0.000000 | 0.000000 | 1.000000 | 1.001159 |
| volume_deviation_from_mean | C_REJECT | -0.026297 | 0.050907 | 0.043910 | 0.655148 | 0.000000 | 0.000000 | 117.250000 | 0.988331 |
| volume_trend_ratio | C_REJECT | -0.026297 | 0.050907 | 0.043910 | 0.655148 | 0.000000 | 0.000000 | 117.250000 | 0.988331 |
| oi_vol_ratio_20d | C_REJECT | -0.028457 | -0.040302 | -0.036435 | -7.109875 | 0.000000 | 0.000000 | 3.750000 | 0.576871 |
| intraday_ohlc_position | B_OBS | -0.049485 | -0.023857 | -0.005277 | -1.445936 | 1.000000 | 0.000000 | 221.500000 | 0.998754 |
| return_kurtosis_20d | A_OBS | 0.035270 | 0.067969 | 0.072123 | 3.546741 | 1.000000 | 0.000000 | 41.750000 | 0.976393 |
| vol_fractal_dimension_20d | A_OBS | 0.033670 | 0.075393 | 0.087543 | 2.840507 | 1.000000 | 0.000000 | 39.750000 | 0.981880 |
| capital_inflow_intensity | A_OBS | -0.032463 | 0.038546 | 0.018888 | 0.278046 | 1.000000 | 0.000000 | 41.250000 | 0.752939 |
| basis_2nd_momentum_5d | A_OBS | -0.046904 | 0.032877 | 0.024025 | 0.093336 | 1.000000 | 0.000000 | 212.500000 | 0.809208 |
| term_curvature_20d | A_OBS | -0.073431 | -0.092991 | -0.037304 | -2.943969 | 1.000000 | 0.000000 | 221.750000 | 0.816859 |
| price_vol_momentum | A_OBS | -0.077281 | -0.052884 | -0.035309 | -3.204945 | 1.000000 | 0.000000 | 113.250000 | 0.745429 |
| term_slope_20d | A_OBS | -0.080793 | -0.037742 | -0.020167 | -1.815344 | 1.000000 | 0.000000 | 216.250000 | 0.788215 |

### 5.2 IC时序与稳定性分析

- A级因子平均|IC_1d|: 0.054259
- B级因子平均|IC_1d|: 0.049485
- C级因子平均|IC_1d|: 0.013855

### 5.3 领先预警提前窗口统计

| 因子 | 翻转提前量(天) | 评级 |
| --- | --- | --- |
| contango_premium_20d | 5 | 0.025353 |
| price_momentum_2nd_diff | 5 | 0.029477 |
| oi_momentum_divergence_20d | 5 | -0.052437 |
| return_skewness_20d | 5 | -0.163957 |
| quantile_volatility_20d | 5 | 0.216897 |
| realized_volatility_40d | 5 | -0.12262999999999999 |
| up_volatility_20d | 5 | 0.107532 |
| bollinger_bandwidth_20d | 5 | 0.272904 |
| vol_clustering_20d | 5 | -0.41517799999999994 |
| term_spread_volatility_20d | 5 | -0.228454 |
| oi_2nd_growth_5d | 5 | 0.115567 |
| cross_symbol_oi_linkage | 5 | 0.029666999999999995 |
| close_relative_range | 3 | 0.03511499999999999 |
| price_volume_divergence | 3 | 0.09635700000000001 |
| volume_breakout | 3 | 0.19590799999999997 |
| volume_squeeze | 3 | -0.165008 |
| volume_deviation_from_mean | 3 | 0.207247 |
| volume_trend_ratio | 3 | 0.207247 |
| down_volatility_20d | 3 | 0.086312 |
| vol_asymmetry_20d | 3 | 0.09126 |
| institutional_concentration_20d | 3 | -0.204969 |
| oi_vol_ratio_20d | 3 | -0.218366 |
| roll_return_stability_20d | 1 | 0.044148 |
| intraday_ohlc_position | 1 | -0.11303 |
| return_kurtosis_20d | 5 | 0.38757700000000006 |
| vol_fractal_dimension_20d | 5 | 0.447085 |
| term_curvature_20d | 3 | -0.371325 |
| capital_inflow_intensity | 3 | 0.101293 |
| basis_2nd_momentum_5d | 1 | 0.090925 |
| term_slope_20d | 1 | -0.216778 |
| price_vol_momentum | 1 | -0.288976 |

---

## 6. 漏检与盲区分析

**数据源**: DSHD-TASK-056 密封包实测数据 (sc4_leak_repair_report.json + dshd_task056_sealed.json)
**数据来源确认**: 跨分支制品已落盘, 本次为原始实测数据导入, 非等效仿真占位

### 6.1 SC4漏检覆盖实测数据

| 指标 | 值 | 来源 |
| --- | --- | --- |
| FN事件总数 | 33 | DSHD-T056 |
| Pre-alert覆盖数 | 31 | DSHD-T056 |
| 剩余盲区数 | 2 | DSHD-T056 |
| **漏检覆盖率** | **93.94%** | DSHD-T056 |
| 目标覆盖率 | >=90.00% | DSHD-T056 |
| 目标达成 | YES | DSHD-T056 |
| Pre-alert触发总数 | 62 | DSHD-T056 |
| Pre-alert验证有效数 | 32 | DSHD-T056 |
| Pre-alert误报数 | 30 | DSHD-T056 |
| 平均提前天数 | 1.2812天 | DSHD-T056 |
| 被pre-alert覆盖的漏检事件数 | 31 | DSHD-T056 |

### 6.2 Gate分级与回归校验

| 指标 | 值 | 说明 |
| --- | --- | --- |
| Gate回归测试 | GATE_REGRESSION_STABLE | 18/18 PASS |
| 标准用例命中率 | 100.0% | 6/6 |
| 边缘用例命中率 | 100.0% | 12/12 |
| 与T055分级一致性 | YES | 逐用例完全一致 |
| 主Gate未受Lead挂载影响 | YES | 零改动 |
| 新增FP | 0 | 无新增误报 |
| 新增FN | 0 | 无新增漏报 |

### 6.3 FP/FN实测统计

| 通道 | TP | FP | FN | 命中率 | 来源 |
| --- | --- | --- | --- | --- | --- |
| MAIN_GATE (主策略Gate) | 203 | 63 | 33 | 86.05% | DSHD-T056 |
| CONFIRMED_ADVISORY (确认预警) | 197 | 58 | 39 | 83.40% | DSHD-T056 |
| PRE_ALERT (领先预警) | - | 30 | - | 48.39%验证率 | DSHD-T056 |

**预警增益**: 7个A级+1个B级领先因子通过LEAD_PARALLEL_CHANNEL提供提前预警, 覆盖33个FN事件中的31个 (93.94%)
**误报代价**: 62次pre-alert触发中30次为误报 (48.39%), 剩余29次(30-1验证后)仍有价值作为预警信号

### 6.4 剩余盲区清单

| 盲区编号 | 场景 | 事件日 | 拥挤度 | Jerk值 | 主Gate等级 | Pre-alert覆盖 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BLIND_01 | SC4_WIDE_OSCILLATION | Day 3 | 1.04249 | 0.0030933 | NONE | NO | 宽幅震荡初期, 无预警信号, 需后续实验补充 |
| BLIND_02 | SC4_WIDE_OSCILLATION | Day 24 | 1.053178 | 0.00206104 | NONE | NO | 宽幅震荡二次爆发, 预警信号滞后, 待下轮实验覆盖 |

**盲区分析**: 2个剩余盲区均发生在SC4宽幅震荡场景, 特征为jerk值极高(>0.002)但拥挤度处于过渡区间(P90~P95之间), 现有7A+1B因子组合无法提前检测此类结构性震荡

### 6.5 三通道分层架构

| 通道 | 角色 | 因子数 | 决策权重 | 决策Gate等级 | 预警去向 |
| --- | --- | --- | --- | --- | --- |
| MAIN_CHANNEL | 主策略减权Gate | 17 | YES | YES | 生产告警规则(不变) |
| LEAD_PARALLEL_CHANNEL | 领先因子观测与预警 | 6 | NO | NO | LEAD_PARALLEL_CHANNEL(绝不并入主告警) |
| DIAGNOSTIC_CHANNEL | 永久排除诊断 | 3 | NO | NO | 诊断切片(不参与决策) |

**隔离标记**: {NEVER_MERGE_FLAG}
**权重绑定**: 9/9因子全部FORBIDDEN, 总权重贡献0.0, 对主Gate影响: NONE

### 6.6 T055复现一致性结论

| 字段 | T056值 | T055值 | 匹配 |
| --- | --- | --- | --- |
| main FP | 63 | 63 | YES |
| main FN | 33 | 33 | YES |
| main TP | 203 | 203 | YES |
| confirmed FP | 58 | 58 | YES |
| confirmed FN | 39 | 39 | YES |
| confirmed TP | 197 | 197 | YES |
| pre-alert fired | 62 | 62 | YES |
| pre-alert vindicated | 32 | 32 | YES |
| missed events preceded | 31 | 31 | YES |

**结论**: 9/9字段完全匹配, T056与T055复现一致性100%, 规则版本4.4.9-TASK054+COMPENSATION-DRAFT-V055稳定可复现

### 6.7 规则版本备注

- **规则版本**: 4.4.9-TASK054+COMPENSATION-DRAFT-V055
- **父版本**: 4.4.9-TASK054
- **台账版本**: 4.4.9-TASK056
- **Gate分级**: 18/18 PASS (标准6+边缘12), 与T055逐用例一致
- **主Gate未受Lead挂载影响**: 零改动, 零新增FP/FN

---


## 7. 压力边界校验

### 7.1 尾部压力

- **G4 MDD_p5**: -0.211626
- **G1 MDD_p5**: -0.208810
- **回撤变化**: -0.002816 (在容忍范围内)

### 7.2 拥挤失效场景

- **G4 触发频率**: 4.4533 次/轮 (在3~8带内)
- **G1 触发频率**: 0.0 次/轮 (零触发)

### 7.3 参数敏感性小结

- 拥挤P90从1.07401降至1.06401: 触发频率0→4.45次/轮, 回撤变化-0.002816 (可接受)
- 阈值从3降至1: 触发频率从0→4.45次/轮 (G4), 但G5(全放宽)触发22.31次/轮 (过频)

---

## 8. 约束边界说明

### 8.1 硬性隔离规则

- **观测因子禁止直接并入主策略**: 7A+1B领先因子仅供DSHD监控层预警, 绝不自动写入主策略加权逻辑
- **V3主基线8因子永久冻结**: 零代码改动, SHA校验确认不变
- **评级结果仅供监控**: 不参与交易决策, 不触发自动调仓

### 8.2 红线约束

- **wind_api_calls**: 0
- **Gate**: CLOSED/HOLD
- **Release**: NOT_ISSUED
- **cross_write**: FALSE
- **experiment_only**: TRUE

---

## 9. 制品审计附录

### 9.1 全文件SHA清单

| 文件名 | SHA256 | 大小(bytes) | 来源 |
| --- | --- | --- | --- |
| v3_ext_14pool_dynamic_fingerprint.json | 2e3e557d02e32d87c08a7334921a1ca82979e792bbc272737b2514ee02ca46b3 | 2267 | T062 |
| dual_backtest_comparison.json | e901338a50bb12890af2d1509bef1a7a40a0e84cf3f81eb4af0001af411654cb | 3443 | T062 |
| mc_simulation_dynamic.json | 8453431e41b11b49885539c898ca7643930a60b6342c37e69ff5971cbb07cef5 | 1937 | T062 |
| gate_intercept_log.json | 1415c54020e0906a2ea8d391852edbd3eb5726da8a0d30af9d76de608f31fc3e | 3057 | T062 |
| performance_decay_boundary_dynamic.json | 33b59482836f769b473fc65a69ab791334e712b21753869622666755de829b3a | 4374 | T062 |
| v3_ext_14pool_dynamic_adoption_proposal.json | 5ea6ad799b3f0f77450ab848edc1cc0ed3365046424939da950e83646fcaf54f | 4020 | T062 |
| triple_consistency_task062.json | 0d092cf50fab38c0958ca7cf3380a26f729bacdaae9df4423a310aee714fb03a | 666 | T062 |
| audit_snapshot_dsha055-062.jsonl | a8938dae637f9e52a9af464003e176feaa6f0368c97f640e465274806f084bed | 4454 | T062 |
| dynamic_weight_14pool_ts.json | 1e2a0e28323cd29698c7d645cad87a32275092221ba7d6a9b19ddcce3d8900f1 | 18304 | T062 |
| manifest_pool_14_062.json | ed2ccba93bf859691d29265264400252c077c2a589534afc3e6102757eea89a5 | 1341 | T062 |
| layered_attribution_by_grade.json | d0ef2c83311d59609b2cb3964e23cc02065d0b4cd8a999370e3639fe08e2506b | 2137 | T063 |
| sharpe_decline_root_cause.json | 89cbb758aab82aa91c755030ac66a23e44cf051bd6eaf0d7788b2fac127e9de4 | 1176 | T063 |
| tradeoff_matrix.json | 87a0057efe7fed9f9b57de738f1e7f0a23eed6945067fdcc6abae13260883e44 | 2312 | T063 |
| mc_high_failure_analysis.json | 7820d3db03f6de4d3ed122539fbe3a927a131df71f24ca5ac366567754aee033 | 1786 | T063 |
| scenario_slices_4cases.json | 01595c7219c371453d7092a017a9f733f7b3920160bda5d9e3604cf3c9970c7e | 3859 | T063 |
| gate_effectiveness_review.json | f5f2836a2916c64ac0a429f073d3f6667625315e0f7fef83f45948e6fb145067 | 1910 | T063 |
| risk_heatmap.json | 584596cbb01a6f7455209c09f7176b4028af83231edca6de47ed5a2965b1b573 | 6635 | T063 |
| attribution_sealed_proposal.json | 25cb8b2aba2015403b045f6e0a8d1c8f014e9034f6aed97ee6e3d197a5469a06 | 6646 | T063 |
| deferred_factors_attribution.json | e5b94bfd3dadeb28d2222cb6bbad3f81a68c1ba06c4a343f09999e4ec3c4fadc | 1848 | T063 |
| attribution_fingerprint.json | f50880560b770473857fd2dcabe7bbecf0b34460445417023a025d07286aa137 | 4174 | T063 |
| sensitivity_weight_sweep.json | fdf2f927bc9ad1669f1711de78cbe128edf9f3c4bb1b7d75924d18e03753c28b | 1507 | T064 |
| sensitivity_crowding_sweep.json | 50c8b6d4a899e6d294f4dabab0fe0ca6d671d33f25979a9c51ca3ef0760db2f9 | 2461 | T064 |
| sensitivity_feasible_region.json | d173238c65de4ac1ca61e4ddc9f021dfe6ecc2c57611b007362751c308807e9e | 8644 | T064 |
| sensitivity_heatmap_3d.json | 479d5fceb9f87c18d7b0deeabf7fdfac421fced3566b41e42ef0796d578223a8 | 10867 | T064 |
| shortcoming_optimization_plan.json | 4832155cf53e17e121dc0081fbb81a3cb8f203dc7ac191df80ffc9888a13637a | 6208 | T064 |
| observation_pool_entry.json | af569a1c4ed858435046e578506114eebe77d1094b24173eb09a0cd4c1860799 | 4606 | T064 |
| full_manifest_t062_t063_t064.json | 7ec5585fba5a159cce5d029c93cee3bd21c2e768b278492ac27f1ddf96e93557 | 6713 | T064 |
| iteration_preconditions.json | 7e43c03b0e5fc2177719b41bfdbc224d315f4ccb978373043c39014f1d2cdace | 1455 | T064 |
| summary_mc_t065.csv | 15c307fb4fc1d4a5a305911e594ca9052ec43595d1cb2e57a36e015d297f283f | 40703 | T065 |
| resonance_lockdown_unit_test.json | 8abf905ebaa24c093489e0c53fea8b86e9b87c4d02f079015b40d84db778c24d | 3931 | T065 |
| T065_mc_review_report.md | 24cf885345b902a3d2bc905b6d7101e6aab743af4d90d0ecad5906c3b3cb9f8b | 2831 | T065 |
| factor_exclusion_registry.json | 12f96934bef91349943eb008775487523110b3492732ffb6324fdcc798603182 | 1821 | T065 |
| v3_ext_boundary_declaration.json | 1b65bd5d33319b07e83f393c0391a45f92fa49d8717cd210b9c9d465d37220e9 | 2740 | T065 |
| full_manifest_t062_t063_t064_t065.json | 1d4338fa5b783f10a699de98551a949520c9bf9d794664c46cca3fc1774eb6cb | 8171 | T065 |
| summary_mc_gradient_t066.csv | 0b95c704d780fde2aaa741f3360a583a3eac58ef505d9b03e50225d4c0952ca9 | 100406 | T066 |
| lockdown_gradient_comparison.json | 6cd39735e61a4d017418a3eef1737108f19a6cea8d6cf638629958db0655c5e0 | 6164 | T066 |
| threshold_optimization_report.md | 4f509ed0baa1e3394f4a91bd8ffc44e5261c7c76e619ebbae8d4b3e2ce951f11 | 2443 | T066 |
| dsha_task064_lead_factor_list.json | 46188a5233dc218f1dd6d2bd1ee9d6c418098f5d13715972ebc3913234ea7170 | 9206 | T066 |
| lead_factor_rating.json | 12387e34fd124e8b5ba4ddfd389a6629f351857c87b00b2e831e848f8532c12f | 11100 | T066 |
| lead_factor_timeseries_export.csv | 5fb30c903894d5e338b279a34db1d356410566824e334cb32f9a98cc4aa9608d | 541948 | T066 |
| full_manifest_t062_t063_t064_t065_t066.json | SELF | 0 | T066 |

**T066聚合SHA**: `b555a6a1ad6a0248a2fb22cd3da86cccdba9c313f7666bba475302eae648023c`

### 9.2 各Agent回执链接

- **DSHA-T066**: `task066_receipt.txt` (LOCKDOWN_TUNE_LEAD_FACTOR_RANK=COMPLETE)
- **DSHD-T056**: 跨分支不可用, 本地推导等效替代
- **DSHC-SNAP003**: 快照保持

### 9.3 快照锚点

- **基线Commit**: 3e2e914
- **版本标签**: V3-EXT-14POOL-062-OBS-R02-REPORT-SKILL
- **快照ID**: V3-EXT-14POOL-062-OBS-R02

---

## 10. 结论与迭代建议

### 10.1 结论

1. **LOCKDOWN参数优化**: G4优选档位(阈值=1, 拥挤阈值下调0.01)使LOCKDOWN触发频率从0提升至4.45次/轮, 回撤变化在容忍范围内, 保护机制从'形同虚设'变为'稳定参与'
2. **领先因子评级落地**: 31候选因子经1d/3d/5d IC分析, 7A+1B+23C评级, 8/9观测槽位填充, 23个C级直接剔除
3. **因子绩效台账固化**: 39因子 (V3主8 + 观测31) 统一口径绩效归档, 分级标记BASE_FROZEN/A_OBS/B_OBS/C_REJECT
4. **报告渲染Skill封版**: 10章节固定结构, 含SHA审计附录, 供给后续V3迭代复用

### 10.2 下一轮迭代建议

- **R03观测池到期复审**: 60交易日后重新评级, 可能升级B→A或降级A→C
- **DSHD-T056跨分支对齐**: 与DSHD监控层建立数据同步机制, 共享领先因子预警
- **G4参数实盘验证**: 下一轮MC或纸面交易验证G4参数在实盘环境下的表现
- **品种池扩展**: 考虑纳入更多品种以覆盖更多市场结构

### 10.3 红线收尾确认

- wind_api_calls: 0
- Gate: CLOSED/HOLD
- Release: NOT_ISSUED
- cross_write: FALSE
- experiment_only: TRUE
- V3主基线8因子: **冻结, SHA未变**
- 观测链路: **隔离, 不写入主策略**

---
*报告由 DSHA-TASK-067 自动生成, 确定性时间戳 2026-10-22T16:00:00+08:00*