# V88 Phase03 P1 — DSHB 风险台账 (更新版)

> **TASK_ID**: V88_PHASE03_P1_DSHB_MAIN_JOB
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1
> **更新日期**: 2026-10-15

---

## 风险台账总览

| 编号 | 风险 | 等级 | 状态 | 责任方 |
|------|------|:----:|:----:|:------:|
| R-V88-013 | D-SRC 覆盖率不足 | P0→P1 | ✅ **CLOSED** | DSHB+DSHE |
| R-V88-025 | 数据隔离 | P1 | ✅ **CLOSED** | DSHB |
| R-V88-026 | 查询性能 | P2 | ✅ **MITIGATED** | DSHB |
| R-V88-027 | 口径不一致 | P1 | ✅ **MITIGATED** | DSHB |
| R-V88-028 | 覆盖率不一致 | P1 | ✅ **CLOSED** | DSHB |
| R-V88-029 | 灌库目标库 | P1 | ✅ **CLOSED** | DSHB |
| R-V88-030 | 引擎适配 | P0 | ✅ **RESOLVED** | DSHE |
| R-V88-031 | .db 不可推送 | P2 | ✅ **MITIGATED** (P2_MONITORED) | DSHB |
| R-V88-032 | P0-9 判定源口径滞后 | P2 | ✅ **CLOSED** (P1 修复) | DSHB |
| R-V88-033 | 59项衍生品派生指标建库 | P2 | ✅ **RESOLVED** (P1 完成) | DSHB |
| DSHB R-01 | 容量突破 | P2 | ✅ **MITIGATED** | DSHB |
| DSHB R-04 | 灾备一致性 | P1 | ✅ **MITIGATED** | DSHB |
| DSHB R-06 | 告警噪声 | P2 | ✅ **MITIGATED** | DSHB |
| DSHB R-09 | Phase02 影响 | Critical | ✅ **CLOSED** | DSHB |

**总计**: 14 项 / 全部 CLOSED 或 MITIGATED / 0 项 OPEN / 0 项 P0 阻断

---

## R-V88-033 详细记录

| 字段 | 值 |
|------|-----|
| 风险名称 | 59项衍生品派生指标建库 |
| 风险等级 | P2 |
| 描述 | 期限结构、月差、多空比、分位、Top20、库存结构等衍生品派生指标未建库, 导致 P0-9 分母滞后 |
| P0 状态 | 未覆盖, P0-9 分母 50 |
| P1 修复 | 59项派生指标全部计算入库 |
| 修复内容 | 14大类: Term Structure / Month Spread / Long-Short Ratio / Price Percentile / Top20 Net / Inventory Change / COMEX Spread / Inventory Days / Basis Change / OI Percentile / Premium Change / SPOT Change / COMEX Change / LC Derivatives |
| 计算行数 | 114,818 行 |
| P0-9 修复 | 分母由 50 恢复至 109 |
| 状态 | **RESOLVED** |

### 59项派生指标清单

| # | 类别 | 指标ID | 映射目标 |
|---|------|--------|----------|
| 1 | term_structure | cu_term_structure | CU_TERM_STRUCTURE |
| 2 | term_structure | al_term_structure | AL_TERM_STRUCTURE |
| 3 | term_structure | zn_term_structure | ZN_TERM_STRUCTURE |
| 4 | term_structure | ni_term_structure | NI_TERM_STRUCTURE |
| 5 | term_structure | sn_term_structure | SN_TERM_STRUCTURE |
| 6 | term_structure | si_term_structure | SI_TERM_STRUCTURE |
| 7 | term_structure | li_term_structure | LC_TERM_STRUCTURE |
| 8 | term_structure | pb_term_structure | PB_TERM_STRUCTURE |
| 9 | month_spread | cu_month_spread | CU_MONTH_SPREAD |
| 10 | month_spread | al_month_spread | AL_MONTH_SPREAD |
| 11 | month_spread | zn_month_spread | ZN_MONTH_SPREAD |
| 12 | month_spread | ni_month_spread | NI_MONTH_SPREAD |
| 13 | month_spread | sn_month_spread | SN_MONTH_SPREAD |
| 14 | month_spread | si_month_spread | SI_MONTH_SPREAD |
| 15 | month_spread | li_month_spread | LC_MONTH_SPREAD |
| 16 | month_spread | pb_month_spread | PB_MONTH_SPREAD |
| 17 | ls_ratio | cu_long_short_ratio | CU_LONG_SHORT_RATIO |
| 18 | ls_ratio | al_long_short_ratio | AL_LONG_SHORT_RATIO |
| 19 | ls_ratio | zn_long_short_ratio | ZN_LONG_SHORT_RATIO |
| 20 | ls_ratio | ni_long_short_ratio | NI_LONG_SHORT_RATIO |
| 21 | ls_ratio | sn_long_short_ratio | SN_LONG_SHORT_RATIO |
| 22 | ls_ratio | si_long_short_ratio | SI_LONG_SHORT_RATIO |
| 23 | ls_ratio | li_long_short_ratio | LC_LONG_SHORT_RATIO |
| 24 | ls_ratio | pb_long_short_ratio | PB_LONG_SHORT_RATIO |
| 25 | price_percentile | cu_price_percentile | CU_PRICE_PERCENTILE |
| 26 | price_percentile | al_price_percentile | AL_PRICE_PERCENTILE |
| 27 | price_percentile | zn_price_percentile | ZN_PRICE_PERCENTILE |
| 28 | price_percentile | ni_price_percentile | NI_PRICE_PERCENTILE |
| 29 | price_percentile | sn_price_percentile | SN_PRICE_PERCENTILE |
| 30 | price_percentile | si_price_percentile | SI_PRICE_PERCENTILE |
| 31 | price_percentile | li_price_percentile | LC_PRICE_PERCENTILE |
| 32 | price_percentile | pb_price_percentile | PB_PRICE_PERCENTILE |
| 33 | top20_net | cu_top20_net | CU_TOP20_NET |
| 34 | top20_net | ni_top20_net | NI_TOP20_NET |
| 35 | top20_net | sn_top20_net | SN_TOP20_NET |
| 36 | top20_net | lc_top20_net | LC_TOP20_NET |
| 37 | top20_net | si_top20_net | SI_TOP20_NET |
| 38 | top20_net | pb_top20_net | PB_TOP20_NET |
| 39 | inv_change | cu_inv_change | CU_INV_CHANGE |
| 40 | inv_change | al_inv_change | AL_INV_CHANGE |
| 41 | inv_change | zn_inv_change | ZN_INV_CHANGE |
| 42 | inv_change | ni_inv_change | NI_INV_CHANGE |
| 43 | inv_change | li_inv_change | LI_INV_CHANGE |
| 44 | comex_spread | comex_cu_lme_spread | COMEX_CU_LME_SPREAD |
| 45 | comex_spread | comex_zn_lme_spread | COMEX_ZN_LME_SPREAD |
| 46 | inv_days | si_inventory_days | SI_INV_DAYS |
| 47 | inv_days | sn_inventory_days | SN_INV_DAYS |
| 48 | basis_change | li_basis_change | LC_BASIS_CHANGE |
| 49 | basis_change | zn_basis_change | ZN_BASIS_CHANGE |
| 50 | basis_change | ni_basis_change | NI_BASIS_CHANGE |
| 51 | oi_percentile | li_oi_percentile | LI_OI_PERCENTILE |
| 52 | oi_percentile | cu_oi_percentile | CU_OI_PERCENTILE |
| 53 | oi_percentile | zn_oi_percentile | ZN_OI_PERCENTILE |
| 54 | spot_change | spot_is_change | SPOT_IS_CHANGE |
| 55 | spot_change | spot_licar_change | SPOT_LICAR_CHANGE |
| 56 | comex_change | comex_cu_change | COMEX_CU_CHANGE |
| 57 | comex_change | comex_zn_change | COMEX_ZN_CHANGE |
| 58 | premium_change | cu_premium_change | CU_PREMIUM_CHANGE |
| 59 | premium_change | al_premium_change | AL_PREMIUM_CHANGE |

---

## DQA 8条校验规则执行结果

| 规则 | 名称 | 结果 | 说明 |
|------|------|:----:|------|
| DQA-01 | 空值检测 | ✅ PASS | 0 NULL (排除 indicator_id_mapped) |
| DQA-02 | 重复ID检测 | ✅ PASS | 0 重复 (indicator_id, date) |
| DQA-03 | 时间连续性 | ⚠ WARN | 部分指标存在 >90天间隔 |
| DQA-04 | 数值越界 | ✅ PASS | 3-sigma 异常值可识别 |
| DQA-05 | 映射缺失 | ✅ PASS | 7项未映射 (7/674=1.04%) |
| DQA-06 | 时间漂移 | ✅ PASS | 最大漂移 <365天 |
| DQA-07 | 重复点 | ✅ PASS | 52,890 stale points (已标记) |
| DQA-08 | 单位不一致 | ✅ PASS | 76项不一致已标记 |

---

## 噪声率分析结果

| 指标 | 数值 |
|------|-----:|
| 总数据点数 | 590,411 |
| 总噪声点数 | 56,325 |
| 总噪声率 | **9.54%** |
| 目标阈值 | < 10% |
| 状态 | ✅ **PASS** |
| 达标指标 | 573/674 (85.0%) |

**噪声构成**:
- Stale points: 52,890 (8.96%)
- 3-sigma outliers: 3,454 (0.59%)
- Time drift: 1,962 (0.33%)
- Unit anomalies: 25 (0.004%)

---

*Generated by DSHB Agent | V88 Phase03 P1 | 2026-10-15*