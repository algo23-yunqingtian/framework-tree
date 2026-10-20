# DSHA-P63 因子回测报告模板 · Backtest Report Template

<!-- TEMPLATE_ID: DSHA-P63-BACKTEST-REPORT-TEMPLATE-001 -->
<!-- USE: 等CSV落地后，将{{PLACEHOLDER}}替换为真实回测结果即可渲染 -->

---

## 报告头

| 字段 | 值 |
|------|-----|
| **报告版本** | v88-g1/P63 |
| **技能名称** | DSHA-P63 OFFLINE_PREP_FACTOR_REPORT_TEMPLATES |
| **Final-Lock版本** | P58 (4 assertions, lines 1438-1468) |
| **Excel隔离策略** | P60 _kill_agent_excel_only() + USER_INSTANCE_LABEL |
| **生成时间** | 2026-10-18 17:18:30 GMT+8 |
| **Agent** | DSHA-P63 |
| **GATE状态** | CLOSED |
| **RELEASE_PERMIT** | NOT_ISSUED |

> ⚠️ **安全声明**: REAL_WIND_CALL=False, WIND_API_CALLS=0
> 本报告基于仿真/离线数据生成，非真实万得行情。

---

## 环境快照区

### 系统环境

| 项目 | 值 |
|------|-----|
| 回测引擎 | DSHA-P61 Factor Backtest Output Standardize |
| 因子计算框架 | DSHA-P59 Factor Constructor |
| 数据加载模块 | DSHA-P59 Factor Data Loader |
| P60 Excel隔离 | ✅ 激活 (`_kill_agent_excel_only` + `USER_INSTANCE_LABEL`) |
| P62 监听守护 | ✅ 就绪 (8项健康校验) |
| P63 报告模板 | ✅ 预构建 |

### 参数基线

| 参数 | 值 | 来源 |
|------|-----|------|
| window_days | 60 | F007_PARAMETER_BASELINE.md (基准锚点) |
| MAX_DAYS_PER_ROUND | 10 | P62 触发器采集参数 |
| MIN_INTERVAL_SEC | 12 | P62 触发器采集参数 |
| f19_weight | frozen | DSHC 锁定 (SchemeD) |
| f20_weight | frozen | DSHC 锁定 (SchemeD) |
| cf003_weight | frozen | DSHC 锁定 (SchemeD) |
| decay_factor | frozen | DSHC 锁定 |
| G7_THRESHOLD | 0.005 | DSHC 冻结 |

---

## 因子统计区

### 回测概览

| 指标 | 值 |
|------|-----|
| 品种 | ZN.SHF |
| 因子类型 | momentum |
| 因子ID | P65-DRYRUN-MOM |
| 数据源 | SIMULATED-P65-DRYRUN |
| 交易日数 | 7 |
| 因子点数 | 7 |
| 起始日期 | 2025-01-07 |
| 结束日期 | 2025-01-15 |

### 回测指标汇总

| 指标 | 值 | 单位 | 描述 |
|------|-----|------|------|
| 累计收益率 | -0.6772% | % | 回测期间总收益率 |
| 年化收益率 | -21.7011% | % | 年化收益率 |
| 年化波动率 | 3.7796% | % | 年化标准差 |
| 日均波动率 | 0.2381% | % | 日均标准差 |
| 最大回撤 | -0.7245% | % | 最大回撤比率 |
| 夏普比率 | -7.5282 | - | 年化夏普比率 |
| IC (信息系数) | -0.435264 | - | Pearson相关系数 |
| IC_IR | -1.151599 | - | IC信息比率 |
| IC样本数 | 7 | - | IC有效样本数 |

### 因子分布统计

| 统计量 | 值 |
|--------|-----|
| 因子点数 | 7 |
| 均值 | -0.00191741 |
| 标准差 | 0.00291757 |
| 最小值 | -0.00584305 |
| 最大值 | 0.00189265 |
| 25%分位 | -0.00527003 |
| 50%分位 | -0.00151036 |
| 75%分位 | 0.00170631 |
| 正值比例 | 0.2857 |
| 负值比例 | 0.7143 |

---

## 因子明细 (7因子)

### 📊 F19 热钱持仓动量 (FACTOR-001)

| 项目 | 值 |
|------|-----|
| 状态 | HOLD |
| 风险分类 | SYNTHETIC_DATA_ZERO_SIGNAL |
| WL-A跟踪 | WL-A001 |
| 数据源 | Wind持仓量表 |
| 计算口径 | z(OI_change) * weight_f19 |
| IC字段 | OI, OI_change, date, variety |
| 清洗规则数 | 7 |

### 🔍 F20 市场关注度 (FACTOR-002)

| 项目 | 值 |
|------|-----|
| 状态 | HOLD |
| 风险分类 | SYNTHETIC_DATA_ZERO_SIGNAL |
| WL-A跟踪 | WL-A002 |
| 数据源 | Wind新闻舆情表 |
| 计算口径 | clip(sentiment_score, -1, 1) * w_s + z(search_volume) * w_v |
| IC字段 | sentiment_score, search_volume, date, variety |
| 清洗规则数 | 7 |

### ⚖️ CF003 投机情绪 (FACTOR-003)

| 项目 | 值 |
|------|-----|
| 状态 | HOLD |
| 风险分类 | SYNTHETIC_DATA_ZERO_SIGNAL |
| WL-A跟踪 | WL-A003 |
| 数据源 | Wind交易所持仓明细表 |
| 计算口径 | z(exchange_oi) * w_e + clip(long_oi/short_oi, 0.1, 10) * w_r |
| IC字段 | exchange_oi, long_oi, short_oi, date, variety |
| 清洗规则数 | 8 |
| ⚠️ 异常规则 | 100%坏样本清洗率预警 (CRITICAL) |

### 📐 G1 IC阈值 (FACTOR-004)

| 项目 | 值 |
|------|-----|
| 状态 | CONDITIONAL_PASS |
| 风险分类 | THRESHOLD_STABILITY_DEFECT |
| WL-A跟踪 | WL-A004 |
| 数据源 | Wind因子IC计算表 |
| 计算口径 | IC = corr(factor_t, forward_return_{t+1}) over window |
| IC字段 | IC_score, forecast_return, realized_return, date, variety |
| 清洗规则数 | 10 |
| 参数 | ic_threshold=TBD, ic_window=60, ic_significance=0.05 |

### 📈 G3 ICIR阈值 (FACTOR-005)

| 项目 | 值 |
|------|-----|
| 状态 | HOLD |
| 风险分类 | ICIR_DEFINITION_REDESIGN_REQUIRED |
| WL-A跟踪 | WL-A005 |
| 数据源 | Wind因子ICIR计算表 |
| 计算口径 | ICIR = rolling_mean(IC) / rolling_std(IC) |
| IC字段 | rolling_ICIR, IC_std, date, variety |
| 清洗规则数 | 7 |
| 参数 | icir_threshold=N/A, icir_window=60, icir_min_periods=30 |

### 🔒 G7 信息泄漏检测 (FACTOR-006)

| 项目 | 值 |
|------|-----|
| 状态 | CONDITIONAL_PASS |
| 风险分类 | LEAKAGE_BOUNDARY_FALSE_ALARM |
| WL-A跟踪 | WL-A006 |
| 数据源 | Wind因子计算管线 |
| 计算口径 | flag if leakage_score > 0.005 (G7_THRESHOLD) |
| IC字段 | leakage_score, info_score, date, variety, factor_id |
| 清洗规则数 | 9 |
| 参数 | leakage_threshold=0.005 (frozen/DSHC) |

### 🧬 F007 多因子合成 (FACTOR-007)

| 项目 | 值 |
|------|-----|
| 状态 | CONDITIONAL_PASS |
| 风险分类 | MULTI_WINDOW_INSTABILITY |
| WL-A跟踪 | WL-A007 |
| 数据源 | Wind多因子合成表 |
| 计算口径 | SchemeD = f19*w_f19 + f20*w_f20 + cf003*w_cf003 |
| IC字段 | F19_score, F20_score, CF003_score, decay_score, date, variety |
| 清洗规则数 | 10 |
| 窗口 | 60日 (基准), 35/80/100日 (验证范围) |

---

## IC时序图

<!-- IC_SERIES_PLOT_PLACEHOLDER -->
<!-- 由 plot_ic_series.py 生成，数据入口: factor_values + forward_returns -->

> 📈 IC时序图占位 — 由 plot_ic_series.py 生成
> _仿真数据: 7个IC数据点_

---

## 净值曲线

<!-- NET_VALUE_PLOT_PLACEHOLDER -->
<!-- 由 plot_net_curve.py 生成，数据入口: dates + net_values + equity_curve -->

> 📈 净值曲线占位 — 由 plot_net_curve.py 生成
> _仿真数据: 7个净值数据点_

---

## 风险备注

### ⚠️ 数据局限性

- 本报告基于**仿真/离线数据**生成，非真实万得行情
- REAL_WIND_CALL = False，WIND_API_CALLS = 0
- 因子计算使用内置随机游走模拟价格序列 (seed=42)

### ⚠️ 因子状态提醒

- **HOLD因子** (4个): FACTOR-001/002/003/005 — 当前阶段不执行清洗规则
- **CONDITIONAL_PASS因子** (3个): FACTOR-004/006/007 — 条件约束验证中
- G7_THRESHOLD=0.005 由 DSHC 冻结，不可修改
- F007权重 (f19/f20/cf003) 由 DSHC 冻结，SchemeD方案

### ⚠️ 统计意义门槛

- 最少交易日数: 61 (window_days=60 + 1)
- 最少因子点数: 30 (IC计算统计意义门槛)
- 当前仿真数据: 7 个因子点

### ⚠️ 漂移预警阈值

| 维度 | WARNING | CRITICAL |
|------|---------|----------|
| 排名相关性 (Spearman ρ) | < 0.80 | < 0.60 |
| 方向一致性 (不一致比例) | > 20% | > 40% |
| 分布形态 (KS检验p值) | < 0.10 | < 0.05 |
| 权重贡献变化率 | > 15% | > 30% |
| IC波动 (std) | > 2×基准std | > 3×基准std |

---

## 故障回滚提示

### 回滚条件

以下情况触发自动回滚:

1. **CRITICAL级漂移**: 任一漂移维度达到CRITICAL阈值 → 停止窗口扩展，升级DSHC审核
2. **ESCALATION**: 连续3个窗口WARNING → 暂停F007条件验证
3. **IC极端异常**: |IC| > 3 × IC_std → 排除异常行，标记复核
4. **清洗率过高**: cleaning_rate > 0.95 → 升级DSHC审核
5. **数据完整性失败**: 全局校验 (NaN/Inf/重复/日期范围) 任一失败 → 排除行

### 回滚操作

```
1. 回退到最近一次 HEALTHY 状态的快照 (artifacts/dsha_p62_listener_snapshot.json)
2. 检查最终锁定断言 (P58 Final-Lock 4 assertions) 是否完好
3. 确认 REAL_WIND_CALL = False, WIND_API_CALLS = 0
4. 确认 G7_THRESHOLD = 0.005 未被修改
5. 确认 MAX_DAYS_PER_ROUND = 10, MIN_INTERVAL_SEC = 12
6. 联系 DSHC 人工审核
```

### 回滚检查清单

- [ ] REAL_WIND_CALL = False ✅
- [ ] WIND_API_CALLS = 0 ✅
- [ ] MAX_DAYS_PER_ROUND = 10 ✅
- [ ] MIN_INTERVAL_SEC = 12 ✅
- [ ] G7_THRESHOLD = 0.005 ✅
- [ ] F007 window_days = 60 ✅
- [ ] Final-Lock 4 assertions intact ✅
- [ ] P60 Excel isolation active ✅
- [ ] P62 health check PASS ✅
- [ ] artifacts/sample_fetch_allow.marker NOT EXISTS ✅

---

## 附录: 输出文件清单

| 文件 | 路径 | 描述 |
|------|------|------|
| 回测指标CSV | artifacts/backtest_archive/{ts}/backtest_metrics_*.csv | 结构化指标表格 |
| 时序净值CSV | artifacts/backtest_archive/{ts}/net_value_series_*.csv | 日期/价格/因子/收益/净值 |
| 回测快照JSON | artifacts/backtest_archive/{ts}/backtest_snapshot_*.json | 仪表盘读取 |
| IC时序图 | artifacts/backtest_archive/{ts}/ic_series_*.png | IC计算可视化 |
| 净值曲线 | artifacts/backtest_archive/{ts}/net_value_*.png | 净值走势可视化 |

---

> **DSHA-P63 声明**: 本报告模板为离线预构建产物，未调用任何Wind API。
> 所有治理不变量保持: wind_api_calls=0, backtest_started=false, gate=CLOSED, release_permit=NOT_ISSUED。
> 等DSHD/DSHC创建 marker 并设置 REAL_WIND_CALL=True 后，可直接套用模板渲染真实回测报告。

_生成时间: 2026-10-18 17:18:30 GMT+8 | Agent: DSHA-P63 | Branch: feature/v88-g1_
