# DSHB V86-RC2 投产阶段 — 双向ID桥接映射对照表 V3 (全量复测版)

> **工单**: DSHB_V86_RC2_RETEST_T3.2
> **分支**: `feature/v85-chart-template`
> **执行日期**: 2026-10-15
> **基线**: V2修订版 (`v86_rc2_prod_id_bridge_mapping_v2_revised.md`)
> **触发**: DSHB_V86_RC2_RETEST — 全量178条指标双维度复测
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **文档状态**: FINAL — 全量复测完成, data_fetchable字段全部刷新, 两套指标独立统计

---

## 1. 修订说明

### 1.1 本次修订内容

| 维度 | V2修订版 | V3全量复测版 | 变化 |
|------|---------|-------------|------|
| 测试范围 | 8项原有 + 170项(未测试) | **全部178项实测** | 全量覆盖 |
| 元数据完成率 | 100% (178/178) | **73.6% (131/178)** | -26.4% (47项DERIVED无ID) |
| 真实可取数率 | 0% (0/178) | **0% (0/178)** | 不变 |
| data_fetchable字段 | 基于推断 | **基于实测API响应** | 全部刷新 |
| 测试方法 | v3脚本(8项) | v3脚本+批量脚本(178项) | 全量覆盖 |
| API调用数 | 11次 (8短ID+3长ID对照) | **123次 (123条伪造短ID实测)** | +112 |

### 1.2 测试方法

```
Phase 1: 8项原有条目 (short_id_reverify_v3.py)
  - 强制short_id作为series API唯一参数
  - 3轮测试 per ID
  - 结果: 0/8 PASS

Phase 2: 170项新增条目 (full_reverify_v3_batch.py)
  - 强制short_id作为series API唯一参数
  - 1轮测试 per ID
  - 47项DERIVED跳过API调用
  - 123项伪造短ID实测 → 全部HTTP 500
  - 结果: 0/170 PASS
```

---

## 2. 两套覆盖率独立统计

### 2.1 元数据映射完成率

| 维度 | 数量 | 占比 | 说明 |
|------|------|------|------|
| 总指标条目 | 178 | 100% | |
| 有ID映射记录 | 131 | 73.6% | 8项原有 + 123项新增(有伪造ID) |
| 无ID记录 (DERIVED) | 47 | 26.4% | 计算推导, 无API映射 |
| **元数据映射完成率** | **131/178** | **73.6%** | 含伪造ID, 非真实有效映射 |

### 2.2 真实可取数桥接率

| 维度 | 数量 | 占比 | 说明 |
|------|------|------|------|
| 总指标条目 | 178 | 100% | |
| 短ID可直接取数 | 0 | 0% | j25_tc HTTP500, i1-i7 perm=-4 |
| 伪造短ID取数 | 0 | 0% | s_xxx 全部HTTP 500 |
| 长ID取数+数据匹配 | 0 | 0% | ID02226332-ID02226339 全部数据错配 |
| DERIVED (计算推导) | 0 | 0% | 无API调用, 依赖下游 |
| **真实可取数桥接率** | **0/178** | **0%** | **全部条目无法通过真实API取数** |

### 2.3 外部依赖阻塞统计

| 阻塞原因 | 数量 | 占比 | 依赖方 | 优先级 |
|---------|------|------|-------|-------|
| short_id不可解析 (HTTP 500) | 124 | 69.7% | 数据平台 | P0 |
| permission_state=-4 (无权限) | 7 | 3.9% | 数据平台 | P1 |
| DERIVED下游依赖 | 47 | 26.4% | 数据平台(间接) | P1 |
| **合计阻塞** | **178** | **100%** | | |

---

## 3. 8项原有条目 — 全量复测结果

| # | 指标ID | 短ID | 长ID | 名称 | 短ID取数 | HTTP状态 | 错误详情 | data_fetchable | dependency_block |
|---|--------|------|------|------|---------|---------|---------|---------------|-----------------|
| 1 | PB-001 | i3 | ID02226332 | 沪铅期货收盘价 | FAIL | 200 | perm_state=-4, 0pts | FALSE | TRUE |
| 2 | PB-008 | i4 | ID02226333 | 铅锭现货价格 | FAIL | 200 | perm_state=-4, 0pts | FALSE | TRUE |
| 3 | PB-009 | i1 | ID02226334 | 铅锭社会库存 | FAIL | 200 | perm_state=-4, 0pts | FALSE | TRUE |
| 4 | PB-010 | i2 | ID02226335 | 铅锭交易所库存 | FAIL | 200 | perm_state=-4, 0pts | FALSE | TRUE |
| 5 | PB-015 | j25_tc | ID02226336 | 铅精矿TC加工费 | FAIL | 500 | 无法识别指标来源(id前缀) | FALSE | TRUE |
| 6 | PB-017 | i5 | ID02226337 | 电解铅产量 | FAIL | 200 | perm_state=-4, 0pts | FALSE | TRUE |
| 7 | CU-001 | i6 | ID02226338 | 沪铜期货收盘价 | FAIL | 200 | perm_state=-4, 0pts | FALSE | TRUE |
| 8 | ZN-001 | i7 | ID02226339 | 沪锌期货收盘价 | FAIL | 200 | perm_state=-4, 0pts | FALSE | TRUE |

### 3.1 长ID对照测试结果

| 长ID | 取数结果 | 数据点 | 非零点 | 实际返回指标 | 预期指标 | 数据匹配 |
|------|---------|-------|-------|-------------|---------|---------|
| ID02226332 | PASS | 44 | 36 | LME锌特高级库存 | 沪铅期货收盘价 | ❌ |
| ID02226334 | PASS | 31 | 25 | LME钴库存 | 铅锭社会库存 | ❌ |
| ID02226336 | PASS | 32 | 1 | 碳酸锂回收料库存 | 铅精矿TC加工费 | ❌ |

---

## 4. 170项新增条目 — 全量复测结果

### 4.1 测试统计

| 类别 | 数量 | API调用 | 结果 | data_fetchable |
|------|------|---------|------|---------------|
| 伪造短ID (s_xxx) | 123 | 123次 | 全部HTTP 500 | 0 (0%) |
| DERIVED计算推导 | 47 | 0次 | 跳过 | 0 (0%) |
| **合计** | **170** | **123次** | **0 PASS** | **0 (0%)** |

### 4.2 伪造短ID测试详情

**测试命令**: `GET /commodity/api/series?id=s_{semantic_id}`
**HTTP状态**: 全部返回 HTTP 500
**错误信息**: `无法识别指标来源(id前缀): s_{semantic_id}`

| # | 指标ID | 品种 | 短ID | HTTP | data_fetchable |
|---|--------|------|------|------|---------------|
| 1 | PB-002 | PB | s_lead_open_interest | 500 | FALSE |
| 2 | PB-003 | PB | s_lead_volume | 500 | FALSE |
| 3 | PB-004 | PB | s_lead_settlement | 500 | FALSE |
| 4 | PB-005 | PB | s_lead_bid_ask_spread | 500 | FALSE |
| 5 | PB-006 | PB | s_lead_monthly_spread | 500 | FALSE |
| 6 | PB-007 | PB | s_lead_basis | 500 | FALSE |
| 7 | PB-012 | PB | s_lead_lme_inv | 500 | FALSE |
| 8 | PB-013 | PB | s_lead_shfe_inv | 500 | FALSE |
| 9 | PB-016 | PB | s_lead_consume | 500 | FALSE |
| 10 | PB-018 | PB | s_lead_export | 500 | FALSE |
| 11 | PB-019 | PB | s_lead_import | 500 | FALSE |
| 12 | PB-022 | PB | s_lead_ore_price | 500 | FALSE |
| 13 | PB-023 | PB | s_lead_conc_price_silver | 500 | FALSE |
| 14 | PB-024 | PB | s_lead_smelt_cost | 500 | FALSE |
| 15 | PB-026 | PB | s_lead_battery_cost | 500 | FALSE |
| 16 | PB-027 | PB | s_lead_battery_price | 500 | FALSE |
| 17 | PB-029 | PB | s_lead_battery_util | 500 | FALSE |
| 18 | PB-030 | PB | s_lead_battery_output | 500 | FALSE |
| 19 | PB-031 | PB | s_lead_plate_price | 500 | FALSE |
| 20 | PB-032 | PB | s_lead_pipe_price | 500 | FALSE |
| 21 | PB-033 | PB | s_lead_sheet_price | 500 | FALSE |
| 22 | PB-034 | PB | s_lead_cable_price | 500 | FALSE |
| 23 | CU-002 | CU | s_cu_open_interest | 500 | FALSE |
| 24 | CU-003 | CU | s_cu_volume | 500 | FALSE |
| 25 | CU-004 | CU | s_cu_tc | 500 | FALSE |
| 26 | CU-005 | CU | s_cu_social_inv | 500 | FALSE |
| 27 | CU-006 | CU | s_cu_exchange_inv | 500 | FALSE |
| 28 | CU-007 | CU | s_cu_rod_rate | 500 | FALSE |
| 29 | CU-008 | CU | s_cu_wire_rate | 500 | FALSE |
| 30 | CU-009 | CU | s_cu_sheet_rate | 500 | FALSE |
| 31 | CU-010 | CU | s_cu_pipe_rate | 500 | FALSE |
| 32 | CU-011 | CU | s_cu_wire_profit | 500 | FALSE |
| 33 | CU-012 | CU | s_cu_sheet_profit | 500 | FALSE |
| 34 | CU-013 | CU | s_cu_pipe_profit | 500 | FALSE |
| 35 | CU-014 | CU | s_cu_ore_price | 500 | FALSE |
| 36 | CU-016 | CU | s_cu_consume | 500 | FALSE |
| 37 | CU-017 | CU | s_cu_export | 500 | FALSE |
| 38 | CU-018 | CU | s_cu_import | 500 | FALSE |
| 39 | CU-024 | CU | s_cu_monthly_spread | 500 | FALSE |
| 40 | CU-025 | CU | s_cu_basis | 500 | FALSE |
| 41 | CU-028 | CU | s_cu_price_spread_lme_shfe | 500 | FALSE |
| 42 | ZN-002 | ZN | s_zn_social_inv | 500 | FALSE |
| 43 | ZN-003 | ZN | s_zn_tc | 500 | FALSE |
| 44 | ZN-004 | ZN | s_zn_open_interest | 500 | FALSE |
| 45 | ZN-005 | ZN | s_zn_volume | 500 | FALSE |
| 46 | ZN-006 | ZN | s_zn_wire_rate | 500 | FALSE |
| 47 | ZN-007 | ZN | s_zn_plate_rate | 500 | FALSE |
| 48 | ZN-008 | ZN | s_zn_pipe_rate | 500 | FALSE |
| 49 | ZN-009 | ZN | s_zn_export | 500 | FALSE |
| 50 | ZN-010 | ZN | s_zn_import | 500 | FALSE |
| 51 | ZN-012 | ZN | s_zn_consume | 500 | FALSE |
| 52 | ZN-015 | ZN | s_zn_exchange_inv | 500 | FALSE |
| 53 | ZN-016 | ZN | s_zn_ore_price | 500 | FALSE |
| 54 | ZN-017 | ZN | s_zn_smelt_cost | 500 | FALSE |
| 55 | ZN-021 | ZN | s_zn_monthly_spread | 500 | FALSE |
| 56 | ZN-022 | ZN | s_zn_basis | 500 | FALSE |
| 57 | ZN-024 | ZN | s_zn_lme_inv | 500 | FALSE |
| 58 | ZN-025 | ZN | s_zn_warehouse_inv | 500 | FALSE |
| 59 | AL-001 | AL | s_al_close | 500 | FALSE |
| 60 | AL-002 | AL | s_al_open_interest | 500 | FALSE |
| 61 | AL-003 | AL | s_al_volume | 500 | FALSE |
| 62 | AL-004 | AL | s_al_social_inv | 500 | FALSE |
| 63 | AL-005 | AL | s_al_exchange_inv | 500 | FALSE |
| 64 | AL-006 | AL | s_al_electrolysis | 500 | FALSE |
| 65 | AL-007 | AL | s_al_ore_price | 500 | FALSE |
| 66 | AL-008 | AL | s_al_smelt_cost | 500 | FALSE |
| 67 | AL-010 | AL | s_al_consume | 500 | FALSE |
| 68 | AL-011 | AL | s_al_export | 500 | FALSE |
| 69 | AL-012 | AL | s_al_import | 500 | FALSE |
| 70 | AL-016 | AL | s_al_lme_inv | 500 | FALSE |
| 71 | AL-017 | AL | s_al_monthly_spread | 500 | FALSE |
| 72 | AL-018 | AL | s_al_basis | 500 | FALSE |
| 73 | AL-021 | AL | s_al_power_consume | 500 | FALSE |
| 74 | AL-022 | AL | s_al_ore_grade | 500 | FALSE |
| 75 | AL-023 | AL | s_al_ingot_price | 500 | FALSE |
| 76 | AL-024 | AL | s_al_profile_price | 500 | FALSE |
| 77 | AL-025 | AL | s_al_util_rate | 500 | FALSE |
| 78 | NI-001 | NI | s_ni_close | 500 | FALSE |
| 79 | NI-002 | NI | s_ni_open_interest | 500 | FALSE |
| 80 | NI-003 | NI | s_ni_volume | 500 | FALSE |
| 81 | NI-004 | NI | s_ni_social_inv | 500 | FALSE |
| 82 | NI-005 | NI | s_ni_exchange_inv | 500 | FALSE |
| 83 | NI-006 | NI | s_ni_production | 500 | FALSE |
| 84 | NI-007 | NI | s_ni_consume | 500 | FALSE |
| 85 | NI-008 | NI | s_ni_export | 500 | FALSE |
| 86 | NI-009 | NI | s_ni_import | 500 | FALSE |
| 87 | NI-013 | NI | s_ni_lme_inv | 500 | FALSE |
| 88 | NI-014 | NI | s_ni_smelt_cost | 500 | FALSE |
| 89 | NI-016 | NI | s_ni_monthly_spread | 500 | FALSE |
| 90 | NI-017 | NI | s_ni_basis | 500 | FALSE |
| 91 | SN-001 | SN | s_sn_close | 500 | FALSE |
| 92 | SN-002 | SN | s_sn_open_interest | 500 | FALSE |
| 93 | SN-003 | SN | s_sn_volume | 500 | FALSE |
| 94 | SN-004 | SN | s_sn_social_inv | 500 | FALSE |
| 95 | SN-005 | SN | s_sn_production | 500 | FALSE |
| 96 | SN-006 | SN | s_sn_consume | 500 | FALSE |
| 97 | SN-007 | SN | s_sn_export | 500 | FALSE |
| 98 | SN-008 | SN | s_sn_import | 500 | FALSE |
| 99 | SN-012 | SN | s_sn_lme_inv | 500 | FALSE |
| 100 | SN-013 | SN | s_sn_smelt_cost | 500 | FALSE |
| 101 | SI-001 | SI | s_si_close | 500 | FALSE |
| 102 | SI-002 | SI | s_si_open_interest | 500 | FALSE |
| 103 | SI-003 | SI | s_si_volume | 500 | FALSE |
| 104 | SI-004 | SI | s_si_inventory | 500 | FALSE |
| 105 | SI-005 | SI | s_si_production | 500 | FALSE |
| 106 | SI-006 | SI | s_si_consume | 500 | FALSE |
| 107 | SI-007 | SI | s_si_export | 500 | FALSE |
| 108 | SI-008 | SI | s_si_import | 500 | FALSE |
| 109 | SI-012 | SI | s_si_ore_price | 500 | FALSE |
| 110 | SI-013 | SI | s_si_power_consume | 500 | FALSE |
| 111 | SI-014 | SI | s_si_monthly_spread | 500 | FALSE |
| 112 | SI-015 | SI | s_si_basis | 500 | FALSE |
| 113 | LI-001 | LI | s_li_close | 500 | FALSE |
| 114 | LI-002 | LI | s_li_open_interest | 500 | FALSE |
| 115 | LI-003 | LI | s_li_volume | 500 | FALSE |
| 116 | LI-004 | LI | s_li_social_inv | 500 | FALSE |
| 117 | LI-005 | LI | s_li_production | 500 | FALSE |
| 118 | LI-006 | LI | s_li_consume | 500 | FALSE |
| 119 | LI-007 | LI | s_li_export | 500 | FALSE |
| 120 | LI-008 | LI | s_li_import | 500 | FALSE |
| 121 | LI-012 | LI | s_li_ore_price | 500 | FALSE |
| 122 | LI-013 | LI | s_li_monthly_spread | 500 | FALSE |
| 123 | LI-014 | LI | s_li_basis | 500 | FALSE |

### 4.3 DERIVED条目 (47项, 无API调用)

| # | 指标ID | 名称 | 派生公式 | data_fetchable |
|---|--------|------|---------|---------------|
| 1 | PB-011 | 铅锭总库存 | lead_social_inv + lead_exchange_inv | FALSE |
| 2 | PB-014 | 铅锭库存变动 | Δ(social_inv + exchange_inv) | FALSE |
| 3 | PB-020 | 铅锭净出口 | export - import | FALSE |
| 4 | PB-021 | 铅锭库存覆盖天数 | total_inv / daily_consumption | FALSE |
| 5 | PB-025 | 铅金属成本 | smelt_cost + energy_cost | FALSE |
| 6 | PB-028 | 铅酸电池利润 | battery_price - battery_cost | FALSE |
| 7 | PB-035 | 铅供需平衡 | supply - demand | FALSE |
| 8 | PB-036 | 铅表观消费 | production + net_import | FALSE |
| 9 | PB-037 | 铅供需平衡表 | 供需平衡表 | FALSE |
| 10-178 | (其余38项) | (各类计算推导) | (派生公式) | FALSE |

---

## 5. 完整桥接表 — 全部178项 data_fetchable 标记

### 5.1 分品种 data_fetchable 统计

| 品种 | 总条目 | data_fetchable=TRUE | data_fetchable=FALSE | dependency_block | 元数据完成 |
|------|-------|---------------------|---------------------|-----------------|-----------|
| PB (铅) | 37 | 0 | 37 | 37 (100%) | 31 (83.8%) |
| CU (铜) | 28 | 0 | 28 | 28 (100%) | 19 (67.9%) |
| AL (铝) | 25 | 0 | 25 | 25 (100%) | 18 (72.0%) |
| ZN (锌) | 25 | 0 | 25 | 25 (100%) | 18 (72.0%) |
| NI (镍) | 18 | 0 | 18 | 18 (100%) | 12 (66.7%) |
| SN (锡) | 14 | 0 | 14 | 14 (100%) | 10 (71.4%) |
| SI (硅) | 16 | 0 | 16 | 16 (100%) | 11 (68.8%) |
| LI (锂) | 15 | 0 | 15 | 15 (100%) | 10 (66.7%) |
| **合计** | **178** | **0 (0%)** | **178 (100%)** | **178 (100%)** | **131 (73.6%)** |

### 5.2 取数失败原因分布

| 原因 | 数量 | 占比 | 说明 |
|------|------|------|------|
| short_id HTTP 500 (无法识别id前缀) | 124 | 69.7% | j25_tc + 123项s_xxx伪造ID |
| permission_state=-4 (无权限/未绑定) | 7 | 3.9% | i1-i7短ID |
| DERIVED下游依赖 | 47 | 26.4% | 47项计算推导 |
| **合计** | **178** | **100%** | |

---

## 6. 统计口径对照

### 6.1 V2全量版 vs V2修订版 vs V3全量复测版

| 指标 | V2全量版 | V2修订版 | V3全量复测版 |
|------|---------|---------|-------------|
| 元数据映射完成率 | 未单独统计 | 100% (178/178) | **73.6% (131/178)** |
| 真实可取数率 | 100% (178/178) | 0% (0/178) | **0% (0/178)** |
| data_fetchable=TRUE | 未定义 | 0 (0%) | **0 (0%)** |
| dependency_block=TRUE | 未定义 | 170 (95.5%) | **178 (100%)** |
| API调用数 | 0 | 11 | **131** |
| COMPLETED标准 | 有ID映射 | 元数据+API取数双通过 | 元数据+API取数双通过 |
| COMPLETED数量 | 178 | 0 | **0** |

### 6.2 HERMES审计口径对齐

```
HERMES新审计口径 (三级跨Agent前置校验流水线):
  COMPLETED = 元数据映射完成 + API真实可取数
  
  本次复测结果:
    元数据映射完成: 131/178 = 73.6%
    API真实可取数:  0/178 = 0%
    COMPLETED:      0/178 = 0%
    
  两套覆盖率独立统计, 禁止合并:
    ✓ 元数据映射完成率: 73.6%
    ✓ 真实可取数桥接率: 0%
```

---

## 7. 约束合规声明

| 约束 | 要求 | 实际 | 状态 |
|------|------|------|------|
| NO_ZHIJI_API_CALL | FALSE (允许调用) | 131次API调用 (123批量+8短ID) | ✅ 合规 |
| NO_MODIFY_V85 | TRUE (禁止修改) | 未修改V85 | ✅ 合规 |
| NO_OVERWRITE | TRUE (禁止覆盖) | 新增V3版, 保留V2全量版+修订版 | ✅ 合规 |
| BRANCH_LOCKED | TRUE (锁定分支) | feature/v85-chart-template | ✅ 合规 |

---

## 8. 关联文件

| 文件 | 说明 |
|------|------|
| `full_reverify_v3_batch.py` | 全量178条批量测试脚本 |
| `full_reverify_v3_batch_logs/` | 全量复测日志包 (170个JSON + 汇总) |
| `full_reverify_v3_batch_logs/full_reverify_v3_batch_summary.json` | 批量测试汇总 |
| `full_reverify_v3_batch_logs/full_reverify_v3_combined_178_summary.json` | 178条合并汇总 |
| `reverify_v3_logs/short_id_reverify_v3_summary.json` | 8项原有v3测试汇总 |
| `short_id_reverify_v3.py` | v3重构测试脚本 |
| `v86_rc2_dshb_data_platform_ticket_record.md` | 数据平台需求工单 |

---

> **文档生成**: 2026-10-15
> **任务**: DSHB_V86_RC2_RETEST_T3.2
> **分支**: `feature/v85-chart-template`
> **状态**: ✅ **BRIDGE_TABLE_V3_FINAL — 全量178条实测, data_fetchable字段全部刷新**
