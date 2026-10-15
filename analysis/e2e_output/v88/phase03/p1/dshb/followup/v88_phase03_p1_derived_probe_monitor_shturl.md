# V88 Phase03 P1 — 衍生品指标探针监控运行日志

> **TASK_ID**: V88_PHASE03_P1_DSHB_FOLLOWUP_JOB (T3)
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1
> **生成时间**: 2026-10-15T16:32:22
> **探针脚本**: `derived_metric_probe.py`
> **关联风险**: R-V88-033 (59项衍生品派生指标建库)

---

## 1. 首次探测结果

| 指标 | 数值 |
|------|-----:|
| 衍生品总数 | 59 |
| 命中数 | **59** |
| 命中率 | **100.00%** |
| 分母模式 | **FULL_109** |
| P0-9分母 | **109** |
| 状态 | ✅ **ALL HIT** |

## 2. 按类别命中统计

| 类别 | 命中 | 总数 | 命中率 |
|------|:----:|:----:|:------:|
| basis_change (基差变化) | 3 | 3 | 100.00% |
| comex_change (COMEX变化) | 2 | 2 | 100.00% |
| comex_spread (COMEX价差) | 2 | 2 | 100.00% |
| inv_change (库存变化) | 5 | 5 | 100.00% |
| inv_days (库存天数) | 2 | 2 | 100.00% |
| ls_ratio (多空比) | 8 | 8 | 100.00% |
| month_spread (月差) | 8 | 8 | 100.00% |
| oi_percentile (持仓分位) | 3 | 3 | 100.00% |
| premium_change (升贴水变化) | 2 | 2 | 100.00% |
| price_percentile (价格分位) | 8 | 8 | 100.00% |
| spot_change (现货变化) | 2 | 2 | 100.00% |
| term_structure (期限结构) | 8 | 8 | 100.00% |
| top20_net (持仓排名净多) | 6 | 6 | 100.00% |

## 3. P0-9分母切换审计日志

| 时间 | 事件 | 前模式 | 当前模式 | 前分母 | 当前分母 | 命中 | 目标 |
|------|------|:------:|:--------:|:------:|:--------:|:----:|:----:|
| 2026-10-15T16:32:22 | **denominator_switch** | IN_SCOPE_50 | FULL_109 | 50 | 109 | 59/59 | 59 |

> **P0-9分母自动切换已触发**: 50 → 109 (衍生品命中59/59 = 100%)
> **审计日志文件**: `derived_probe_switch_audit.jsonl`

## 4. 59项衍生品指标完整命中清单

| # | 指标ID | 行数 | 映射目标 | 状态 |
|:-:|--------|:----:|----------|:----:|
| 1 | cu_term_structure | 3,041 | CU_TERM_STRUCTURE | ✅ HIT |
| 2 | al_term_structure | 3,041 | AL_TERM_STRUCTURE | ✅ HIT |
| 3 | zn_term_structure | 2,833 | ZN_TERM_STRUCTURE | ✅ HIT |
| 4 | ni_term_structure | 1,659 | NI_TERM_STRUCTURE | ✅ HIT |
| 5 | sn_term_structure | 1,535 | SN_TERM_STRUCTURE | ✅ HIT |
| 6 | si_term_structure | 893 | SI_TERM_STRUCTURE | ✅ HIT |
| 7 | li_term_structure | 754 | LC_TERM_STRUCTURE | ✅ HIT |
| 8 | pb_term_structure | 3,041 | PB_TERM_STRUCTURE | ✅ HIT |
| 9 | cu_month_spread | 3,040 | CU_MONTH_SPREAD | ✅ HIT |
| 10 | al_month_spread | 3,040 | AL_MONTH_SPREAD | ✅ HIT |
| 11 | zn_month_spread | 2,832 | ZN_MONTH_SPREAD | ✅ HIT |
| 12 | ni_month_spread | 1,659 | NI_MONTH_SPREAD | ✅ HIT |
| 13 | sn_month_spread | 1,537 | SN_MONTH_SPREAD | ✅ HIT |
| 14 | si_month_spread | 893 | SI_MONTH_SPREAD | ✅ HIT |
| 15 | li_month_spread | 436 | LC_MONTH_SPREAD | ✅ HIT |
| 16 | pb_month_spread | 3,040 | PB_MONTH_SPREAD | ✅ HIT |
| 17 | cu_long_short_ratio | 3,041 | CU_LONG_SHORT_RATIO | ✅ HIT |
| 18 | al_long_short_ratio | 3,041 | AL_LONG_SHORT_RATIO | ✅ HIT |
| 19 | zn_long_short_ratio | 345 | ZN_LONG_SHORT_RATIO | ✅ HIT |
| 20 | ni_long_short_ratio | 346 | NI_LONG_SHORT_RATIO | ✅ HIT |
| 21 | sn_long_short_ratio | 345 | SN_LONG_SHORT_RATIO | ✅ HIT |
| 22 | si_long_short_ratio | 893 | SI_LONG_SHORT_RATIO | ✅ HIT |
| 23 | li_long_short_ratio | 754 | LC_LONG_SHORT_RATIO | ✅ HIT |
| 24 | pb_long_short_ratio | 3,041 | PB_LONG_SHORT_RATIO | ✅ HIT |
| 25 | cu_price_percentile | 3,022 | CU_PRICE_PERCENTILE | ✅ HIT |
| 26 | al_price_percentile | 3,022 | AL_PRICE_PERCENTILE | ✅ HIT |
| 27 | zn_price_percentile | 2,814 | ZN_PRICE_PERCENTILE | ✅ HIT |
| 28 | ni_price_percentile | 2,760 | NI_PRICE_PERCENTILE | ✅ HIT |
| 29 | sn_price_percentile | 2,760 | SN_PRICE_PERCENTILE | ✅ HIT |
| 30 | si_price_percentile | 874 | SI_PRICE_PERCENTILE | ✅ HIT |
| 31 | li_price_percentile | 735 | LC_PRICE_PERCENTILE | ✅ HIT |
| 32 | pb_price_percentile | 3,022 | PB_PRICE_PERCENTILE | ✅ HIT |
| 33 | cu_top20_net | 3,041 | CU_TOP20_NET | ✅ HIT |
| 34 | ni_top20_net | 2,779 | NI_TOP20_NET | ✅ HIT |
| 35 | sn_top20_net | 2,779 | SN_TOP20_NET | ✅ HIT |
| 36 | lc_top20_net | 754 | LC_TOP20_NET | ✅ HIT |
| 37 | si_top20_net | 893 | SI_TOP20_NET | ✅ HIT |
| 38 | pb_top20_net | 3,041 | PB_TOP20_NET | ✅ HIT |
| 39 | cu_inv_change | 3,040 | CU_INV_CHANGE | ✅ HIT |
| 40 | al_inv_change | 3,040 | AL_INV_CHANGE | ✅ HIT |
| 41 | zn_inv_change | 516 | ZN_INV_CHANGE | ✅ HIT |
| 42 | ni_inv_change | 499 | NI_INV_CHANGE | ✅ HIT |
| 43 | li_inv_change | 17 | LI_INV_CHANGE | ✅ HIT |
| 44 | comex_cu_lme_spread | 3,041 | COMEX_CU_LME_SPREAD | ✅ HIT |
| 45 | comex_zn_lme_spread | 1,051 | COMEX_ZN_LME_SPREAD | ✅ HIT |
| 46 | si_inventory_days | 133 | SI_INV_DAYS | ✅ HIT |
| 47 | sn_inventory_days | 2,496 | SN_INV_DAYS | ✅ HIT |
| 48 | li_basis_change | 753 | LC_BASIS_CHANGE | ✅ HIT |
| 49 | zn_basis_change | 2,833 | ZN_BASIS_CHANGE | ✅ HIT |
| 50 | ni_basis_change | 2,777 | NI_BASIS_CHANGE | ✅ HIT |
| 51 | li_oi_percentile | 735 | LI_OI_PERCENTILE | ✅ HIT |
| 52 | cu_oi_percentile | 3,022 | CU_OI_PERCENTILE | ✅ HIT |
| 53 | zn_oi_percentile | 326 | ZN_OI_PERCENTILE | ✅ HIT |
| 54 | spot_is_change | 773 | SPOT_IS_CHANGE | ✅ HIT |
| 55 | spot_licar_change | 438 | SPOT_LICAR_CHANGE | ✅ HIT |
| 56 | comex_cu_change | 3,040 | COMEX_CU_CHANGE | ✅ HIT |
| 57 | comex_zn_change | 2,832 | COMEX_ZN_CHANGE | ✅ HIT |
| 58 | cu_premium_change | 3,040 | CU_PREMIUM_CHANGE | ✅ HIT |
| 59 | al_premium_change | 3,040 | AL_PREMIUM_CHANGE | ✅ HIT |

## 5. 文件清单

| 文件 | 描述 |
|------|------|
| `derived_probe_log.jsonl` | 探针时序日志 (JSON Lines) |
| `derived_probe_checkpoint.json` | 探针状态检查点 |
| `derived_probe_switch_audit.jsonl` | 分母切换审计日志 |
| `derived_metric_probe.py` | 探针监控脚本 |

## 6. 门禁状态更新

| 门禁 | 前状态 | 当前状态 | 说明 |
|------|:------:|:--------:|------|
| P0-9 | IN_SCOPE_50 | **FULL_109** | 衍生品59/59命中, 分母50→109 |
| R-V88-033 | 🟡 OPEN | ✅ **RESOLVED** | 59项衍生品全部命中 |

---

*Generated by derived_metric_probe.py | V88 Phase03 P1 Followup | 2026-10-15*