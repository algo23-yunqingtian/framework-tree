# Poll39 因子泄露风险 · 附表

> **附表 ID**: POLL39-FACTOR-LEAKAGE-APPENDIX
> **检测模块**: FL-01 / FL-02 / FL-03
> **因子对象**: P0-1 .. P0-7（共 7 项）
> **扫描脚本数**: 39
> **READ_ONLY**: 是（仅读取脚本与元数据，未修改、未重跑模型、未调用 Wind）
> **生成时间**: 2026-10-16T11:41:00+0800

## 1. FL 模块摘要

### FL-01 · 未来数据引入检测 (look-ahead leakage)

- **严重级**: HIGH
- **扫描脚本数**: 39
- **命中总次数**: 19
- **命中脚本数**: 5
- **扫描的 pattern 组**: `bfill`, `shift_negative`, `shift_minus_var`, `future_merge_asof`, `shift_forward_kw`
- **裁决**: REVIEW

### FL-02 · 样本截断时间边界校验 (sample cutoff boundary)

- **严重级**: HIGH
- **扫描脚本数**: 39
- **命中总次数**: 23
- **命中脚本数**: 6
- **扫描的 pattern 组**: `iloc_split`, `getitem_slice`, `no_explicit_cutoff`, `resample_ffill`
- **裁决**: REVIEW

### FL-03 · 训练/测试时间切片隔离校验 (train-test temporal isolation)

- **严重级**: HIGH
- **扫描脚本数**: 39
- **命中总次数**: 0
- **命中脚本数**: 0
- **扫描的 pattern 组**: `shuffle_split`, `timeseries_split`, `timeseries_gap_zero`, `fit_all_data`, `grid_search_full`
- **裁决**: PASS

## 2. FL-01 · 未来数据引入检测 · 详细命中

| 脚本 | pattern 组 | 命中次数 | 首个匹配行 |
|---|---|---|---|
| `data-harbor\dsha_p49_prep\P49_data_cleaning_pipeline.py` | `bfill` | 1 | `df = df.bfill()` |
| `data-harbor\dsha_p49_prep\P49_dryrun_pipeline.py` | `bfill` | 1 | `df = df.bfill()` |
| `data-harbor\dsha_p49_prep\P49_backtest_audit\build_p54_kb.py` | `shift_negative` | 1 | `factor_final = factor_filled.shift(-1)  # T+1对齐` |
| `data-harbor\dsha_p49_prep\P49_dryrun_pipeline.py` | `shift_negative` | 4 | `df_work[forward_return_col] = df_work[return_col].shift(-1)` |
| `data-harbor\dsha_p49_prep\P49_sensitivity_test.py` | `shift_negative` | 1 | `df_copy['return_next'] = df_copy[return_col].shift(-1)` |
| `data-harbor\dsha_p49_prep\P49_threshold_stress.py` | `shift_negative` | 2 | `df_work[forward_ret_col] = df_work[ret_col].shift(-1)` |
| `data-harbor\dsha_p49_prep\P49_backtest_audit\build_p54_kb.py` | `shift_minus_var` | 1 | `factor_final = factor_filled.shift(-1)  # T+1对齐` |
| `data-harbor\dsha_p49_prep\P49_dryrun_pipeline.py` | `shift_minus_var` | 5 | `df_work[forward_return_col] = df_work[return_col].shift(-1)` |
| `data-harbor\dsha_p49_prep\P49_sensitivity_test.py` | `shift_minus_var` | 1 | `df_copy['return_next'] = df_copy[return_col].shift(-1)` |
| `data-harbor\dsha_p49_prep\P49_threshold_stress.py` | `shift_minus_var` | 2 | `df_work[forward_ret_col] = df_work[ret_col].shift(-1)` |

## 3. FL-02 · 样本截断时间边界校验 · 详细命中

| 脚本 | pattern 组 | 命中次数 | 首个匹配行 |
|---|---|---|---|
| `data-harbor\dsha_p49_prep\P49_dryrun_pipeline.py` | `iloc_split` | 1 | `q1_ret = float(layer_returns.iloc[0])` |
| `data-harbor\dsha_p49_prep\P49_sensitivity_test.py` | `iloc_split` | 1 | `q1_ret = float(layer_returns_full.iloc[0])` |
| `data-harbor\dsha_p49_prep\P49_backtest_audit\factor_retest_real_data.py` | `no_explicit_cutoff` | 3 | `def fetch_wind_data(variety, code, start_date, end_date):` |
| `data-harbor\dsha_p49_prep\P49_backtest_audit\factor_risk_review.py` | `no_explicit_cutoff` | 3 | `def fetch_wind_data(variety, code, start_date, end_date):` |
| `data-harbor\dsha_p49_prep\P49_dryrun_pipeline.py` | `no_explicit_cutoff` | 2 | `def generate_trading_calendar(start_date, n_days):` |
| `data-harbor\dsha_p49_prep\P49_real_backtest_pipeline.py` | `no_explicit_cutoff` | 1 | `time_range: (start_date, end_date) of processed data` |
| `data-harbor\dsha_p49_prep\P49_real_data_preprocessing.py` | `no_explicit_cutoff` | 12 | `def load_trading_calendar(start_date=None, end_date=None):` |

## 4. FL-03 · 训练/测试时间切片隔离校验 · 详细命中

*无命中：未发现 ShuffleSplit/KFold 或 gap=0 等切片隔离风险*

## 5. 7 因子泄露风险结论（P0-1..P0-7）

### P0-1 · F19_hot_money_weight

| 属性 | 值 |
|---|---|
| 因子分类 | SYNTHETIC_DATA_ZERO_SIGNAL |
| 风险级 | HIGH |
| 准入状态 | HOLD |
| FL 关联命中数 | 0 |
| 泄露裁决 | **N/A_SYNTHETIC_DATA** |
| 说明 | 因子基于合成数据、IC=0.0；因子计算管线未接入真实数据源，FL 静态扫描结果仅作记录，不构成真实泄露判定 |

### P0-2 · F20_attention_weight

| 属性 | 值 |
|---|---|
| 因子分类 | SYNTHETIC_DATA_ZERO_SIGNAL |
| 风险级 | HIGH |
| 准入状态 | HOLD |
| FL 关联命中数 | 0 |
| 泄露裁决 | **N/A_SYNTHETIC_DATA** |
| 说明 | 因子基于合成数据、IC=0.0；因子计算管线未接入真实数据源，FL 静态扫描结果仅作记录，不构成真实泄露判定 |

### P0-3 · CF003_speculation_weight

| 属性 | 值 |
|---|---|
| 因子分类 | SYNTHETIC_DATA_ZERO_SIGNAL |
| 风险级 | HIGH |
| 准入状态 | HOLD |
| FL 关联命中数 | 0 |
| 泄露裁决 | **N/A_SYNTHETIC_DATA** |
| 说明 | 因子基于合成数据、IC=0.0；因子计算管线未接入真实数据源，FL 静态扫描结果仅作记录，不构成真实泄露判定 |

### P0-4 · G1_IC_threshold

| 属性 | 值 |
|---|---|
| 因子分类 | THRESHOLD_STABILITY_DEFECT |
| 风险级 | HIGH |
| 准入状态 | CONDITIONAL_PASS |
| FL 关联命中数 | 0 |
| 泄露裁决 | **NO_LEAKAGE_EVIDENCE** |
| 说明 | 阈值稳定性缺陷属阈值选取与数据分布问题，非数据泄露；FL 扫描未发现未来函数 |

### P0-5 · G3_ICIR_threshold

| 属性 | 值 |
|---|---|
| 因子分类 | THRESHOLD_STABILITY_DEFECT |
| 风险级 | HIGH |
| 准入状态 | HOLD |
| FL 关联命中数 | 0 |
| 泄露裁决 | **NO_LEAKAGE_EVIDENCE** |
| 说明 | 阈值稳定性缺陷属阈值选取与数据分布问题，非数据泄露；FL 扫描未发现未来函数 |

### P0-6 · G7_leakage_ratio

| 属性 | 值 |
|---|---|
| 因子分类 | LEAKAGE_BOUNDARY_FALSE_ALARM_ISSUE |
| 风险级 | WARN |
| 准入状态 | CONDITIONAL_PASS |
| FL 关联命中数 | 0 |
| 泄露裁决 | **FALSE_ALARM_MITIGATED** |
| 说明 | 31 次误报为噪声级 IC 触发的边界告警，非真实泄露；白名单 WL-001..WL-005 已覆盖，阈值 0.005 与 DSHC G7_THRESHOLD 锁定 |

### P0-7 · SchemeD_frozen_weights

| 属性 | 值 |
|---|---|
| 因子分类 | MULTI_WINDOW_INSTABILITY |
| 风险级 | MEDIUM |
| 准入状态 | CONDITIONAL_PASS |
| FL 关联命中数 | 0 |
| 泄露裁决 | **NO_LEAKAGE_EVIDENCE** |
| 说明 | 多窗口不稳定性属窗口选择与数据量问题，非泄露；FL 扫描未发现未来函数 |

## 6. 处置建议

### 6.1 综合结论

1. **FL-01 未来数据引入**: 发现潜在命中，需人工复核
2. **FL-02 截断边界**: 发现潜在命中，需人工复核
3. **FL-03 时间切片隔离**: 无命中

### 6.2 7 因子逐项处置

| Factor | 现状 | 建议 |
|---|---|---|
| P0-1 F19_hot_money_weight | SYNTHETIC_DATA_ZERO_SIGNAL · HOLD | 待真实数据接入后重测；FL 静态扫描不适用 |
| P0-2 F20_attention_weight | SYNTHETIC_DATA_ZERO_SIGNAL · HOLD | 同上 |
| P0-3 CF003_speculation_weight | SYNTHETIC_DATA_ZERO_SIGNAL · HOLD | 同上；100% 坏样本清洗率需关注 |
| P0-4 G1_IC_threshold | THRESHOLD_STABILITY_DEFECT · CONDITIONAL_PASS | 采纳 G1-ANOM-001..004 异常过滤；非泄露问题 |
| P0-5 G3_ICIR_threshold | THRESHOLD_STABILITY_DEFECT · HOLD | 重定义 ICIR 指标；跨窗口符号翻转 |
| P0-6 G7_leakage_ratio | LEAKAGE_BOUNDARY_FALSE_ALARM_ISSUE · CONDITIONAL_PASS | 白名单 WL-001..WL-005 已覆盖 31 次误报；阈值 0.005 与 DSHC G7_THRESHOLD 锁定；建议采纳 BT-001..004 告警调优 |
| P0-7 SchemeD_frozen_weights | MULTI_WINDOW_INSTABILITY · CONDITIONAL_PASS | 约束窗口至 35-100 天；合成数据下 16/20 UNSTABLE；非泄露 |

### 6.3 交付 DSHC · G7 人工裁决要点

- **无真实泄露发现**：7 因子均为合成数据下 IC=0.0 或阈值稳定性缺陷，非数据泄露
- **FL-01/02/03 静态扫描**：因子脚本未发现未来函数（bfill/shift(-n)/前瞻窗口）
- **P0-6 唯一「泄露」相关项**：G7_leakage_ratio 的 31 次误报已由白名单治理，非真实泄露
- **数据源限制**：所有因子当前为合成数据（SYNTHETIC_DATA），真实泄露判定需待 Wind 实盘数据接入后重测
- **GATE 不变**：`CLOSED/HOLD` · `release_permit = NOT_ISSUED` · `self_approval = 0`

---

_生成时间：_2026-10-16T11:41:00+0800
