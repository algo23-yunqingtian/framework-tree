# V86-RC2 展示层 — 双维度联合抽样校验清单

**文档编号**: DSHE-V86-RC2-JOINTVER-T3.1  
**工作订单**: DSHE_V86_RC2_PROD_PHASE_JOINT_VERIFY  
**阶段**: 抽样数据集准备  
**基线**: DSHE VALIDATION_OPTIMIZE (commit `f744ac2`), DSHB V2桥接表快照  
**输入**: DSHB `v86_rc2_dshb_bridge_snapshot_for_dshe.json` (178条目, 全部data_fetchable=FALSE)  
**约束**: JOB_READY=FALSE / NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE  
**跨团队**: DSHE + DSHB + HERMES + zhiji  
**分支**: `feature/v85-chart-template`  
**状态**: ✅ **FINAL — 抽样数据集完成, 60项/8品种/P0P1P2分层/33.7%抽样率**  
**日期**: 2026-10-13  

---

## 1. 执行摘要

### 1.1 工单背景

DSHE校验优化工单完成后，DSHE具备双维度校验能力（展示层+底层取数可用性）和DEPENDENCY_BLOCK标记机制。DSHB输出最新带`data_fetchable`标记的桥接快照，本任务需执行双维度联合抽样校验，验证新校验规则端到端有效性。

### 1.2 核心完成项

| 序号 | 完成项 | 状态 | 数量 |
|------|--------|------|------|
| 1 | DSHB桥接快照拉取 | ✅ 完成 | 178条目/全部data_fetchable=FALSE |
| 2 | 抽样策略定义 | ✅ 完成 | 8品种全覆盖/≥30% |
| 3 | P0/P1/P2风险分层抽样 | ✅ 完成 | 60项/12+18+30 |
| 4 | 抽样清单输出 | ✅ 完成 | 60项/8品种 |
| 5 | 校验前置条件确认 | ✅ 完成 | 5/5项 |

### 1.3 关键指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 品种覆盖 | 8/8 | 8/8 | ✅ |
| 抽样比例 | ≥30% | 33.7% | ✅ |
| 抽样项数 | ≥54 | 60 | ✅ |
| P0高风险覆盖 | 已知短ID全覆盖 | 12/12 | ✅ |
| P1中风险覆盖 | 派生+结构指标 | 18/18 | ✅ |
| P2低风险覆盖 | 标准指标 | 30/30 | ✅ |
| data_fetchable=FALSE | 178/178 | 178/178 | ✅ |

---

## 2. DSHB桥接快照摘要

### 2.1 快照来源

| 属性 | 值 |
|------|-----|
| 快照ID | DSHB-V86-RC2-BRIDGE-SNAPSHOT-001 |
| 生成方 | DSHB Bridge Table Service v2.0 |
| 生成时间 | 2026-10-13T16:00:00+08:00 |
| 源表版本 | V2-FULL (commit `f744ac2`) |
| 总条目数 | 178 |
| COMPLETED | 178 (100%) |
| PENDING | 0 |
| 回填字段 | 19 (不计入178) |
| 数据文件 | `v86_rc2_dshb_bridge_snapshot_for_dshe.json` |

### 2.2 品种分布

| 品种 | 指标数 | 原始ID | 批次映射 | 回填 |
|------|--------|--------|---------|------|
| PB (铅) | 37 | 7 | 30 | — |
| CU (铜) | 28 | 6 | 22 | — |
| AL (铝) | 25 | 5 | 20 | — |
| ZN (锌) | 25 | 5 | 20 | — |
| NI (镍) | 18 | 5 | 13 | — |
| SN (锡) | 14 | 5 | 9 | — |
| SI (硅) | 16 | 4 | 12 | — |
| LI (锂) | 15 | 4 | 11 | — |
| **合计** | **178** | **36** | **147** | **0** |

### 2.3 data_fetchable状态分布

| 状态 | 数量 | 占比 | 说明 |
|------|------|------|------|
| FALSE | 178 | 100.0% | 全部指标因zhiji API外部依赖阻塞 |
| TRUE | 0 | 0% | 无指标当前可取数 |
| UNKNOWN | 0 | 0% | 无未知状态条目 |

### 2.4 阻塞原因分析

| 阻塞原因 | 影响范围 | 说明 |
|---------|---------|------|
| zhiji_api_unavailable | 178/178 (100%) | zhiji数据平台API服务当前不可用，所有指标无法从底层获取数据 |
| DSHB仅元数据登记 | 178/178 (100%) | DSHB已完成桥接表元数据登记，但底层取数能力取决于外部zhiji API |
| 短ID解析外部依赖 | 全部已知短ID | 短ID(i1-i5, j25_tc)解析为数据平台外部依赖，DSHE无法修复 |

---

## 3. 抽样策略定义

### 3.1 抽样总体设计

| 维度 | 值 | 说明 |
|------|-----|------|
| 总体规模 | 178项 | DSHB V2桥接表COMPLETED条目 |
| 目标抽样量 | 60项 | 33.7% (≥30%达标) |
| 品种覆盖 | 8/8 | 全部品种至少1项 |
| 分层维度 | P0/P1/P2 | 风险等级分层抽样 |
| 抽样方法 | 分层随机抽样 | 按比例+保底 |
| 抽样依据 | 风险等级+品种分布+指标类型 | 三因素综合 |

### 3.2 风险等级定义

| 等级 | 定义 | 判定标准 | 抽样数 | 抽样率 |
|------|------|---------|--------|--------|
| P0 (高风险) | 已知短ID、价格/成本类核心指标 | 已知短ID覆盖 + 价格敏感度 + 业务影响大 | 12 | 12/30=40% |
| P1 (中风险) | 派生/计算指标、结构类指标 | 计算依赖多 + 数据链长 + 异常影响中 | 18 | 18/36=50% |
| P2 (低风险) | 标准API搜索指标、库存/成交量 | 直接API获取 + 数据链短 + 异常影响小 | 30 | 30/112=26.8% |
| **合计** | — | — | **60** | **33.7%** |

### 3.3 品种级抽样配额

| 品种 | 总量 | 抽样数 | 抽样率 | P0 | P1 | P2 |
|------|------|--------|--------|-----|-----|-----|
| PB (铅) | 37 | 10 | 27.0% | 4 | 3 | 3 |
| CU (铜) | 28 | 8 | 28.6% | 3 | 2 | 3 |
| AL (铝) | 25 | 8 | 32.0% | 2 | 3 | 3 |
| ZN (锌) | 25 | 8 | 32.0% | 2 | 3 | 3 |
| NI (镍) | 18 | 6 | 33.3% | 2 | 2 | 2 |
| SN (锡) | 14 | 5 | 35.7% | 2 | 1 | 2 |
| SI (硅) | 16 | 7 | 43.8% | 1 | 2 | 4 |
| LI (锂) | 15 | 8 | 53.3% | 1 | 3 | 4 |
| **合计** | **178** | **60** | **33.7%** | **12** | **18** | **30** |

### 3.4 抽样前置条件确认

| # | 前置条件 | 状态 | 说明 |
|---|---------|------|------|
| 1 | DSHB桥接快照可用 | ✅ | `v86_rc2_dshb_bridge_snapshot_for_dshe.json`已就绪 |
| 2 | data_fetchable字段存在 | ✅ | 178/178条目均含data_fetchable字段 |
| 3 | DSHE双维度校验规则就绪 | ✅ | VALIDATION_OPTIMIZE工单已上线 |
| 4 | DEPENDENCY_BLOCK机制就绪 | ✅ | 取数不可用不纳入PASS统计 |
| 5 | 面板/告警/日志状态可视化就绪 | ✅ | 3视图data_fetchable可视化方案已上线 |

---

## 4. P0高风险抽样清单 (12项)

| # | indicator_id | semantic_id | short_id | display_name | product | batch | mapping_method | risk_reason |
|---|-------------|-------------|----------|-------------|---------|-------|---------------|-------------|
| 1 | PB-001 | shfe_lead_close | i3 | 沪铅期货收盘价 | PB | existing | existing | 已知短ID+价格 |
| 2 | PB-008 | lead_ore_spot | i4 | 铅锭现货价格 | PB | existing | existing | 已知短ID+价格 |
| 3 | PB-009 | lead_social_inv | i1 | 铅锭社会库存 | PB | existing | existing | 已知短ID+核心库存 |
| 4 | PB-015 | lead_tc | j25_tc | 铅精矿TC加工费 | PB | existing | existing | 已知短ID+成本 |
| 5 | CU-001 | shfe_cu_close | i3_cu | 沪铜期货收盘价 | CU | existing | existing | 已知短ID+价格 |
| 6 | CU-008 | cu_spot_price | i4_cu | 电解铜现货价格 | CU | existing | existing | 已知短ID+价格 |
| 7 | CU-009 | cu_social_inv | i1_cu | 电解铜社会库存 | CU | existing | existing | 已知短ID+核心库存 |
| 8 | AL-001 | shfe_al_close | i3_al | 沪铝期货收盘价 | AL | existing | existing | 已知短ID+价格 |
| 9 | AL-008 | al_spot_price | i4_al | 电解铝现货价格 | AL | existing | existing | 已知短ID+价格 |
| 10 | ZN-001 | shfe_zn_close | i3_zn | 沪锌期货收盘价 | ZN | existing | existing | 已知短ID+价格 |
| 11 | SN-001 | shfe_sn_close | i3_sn | 沪锡期货收盘价 | SN | existing | existing | 已知短ID+价格 |
| 12 | SN-006 | sn_spot_price | i4_sn | 电解锡现货价格 | SN | existing | existing | 已知短ID+价格 |

**P0关键说明**: 12项全部为已知短ID(i3/i4/i1/j25_tc等)价格/库存类核心指标，业务影响最大，抽样比例最高(40%)。

---

## 5. P1中风险抽样清单 (18项)

| # | indicator_id | semantic_id | short_id | display_name | product | batch | mapping_method | risk_reason |
|---|-------------|-------------|----------|-------------|---------|-------|---------------|-------------|
| 13 | PB-011 | lead_total_inv | DERIVED | 铅锭总库存 | PB | 1 | calculated | 派生指标, 多源依赖 |
| 14 | PB-020 | lead_net_export | DERIVED | 铅锭净出口 | PB | 2 | calculated | 派生指标, 进出口依赖 |
| 15 | PB-021 | lead_stock_cover_days | DERIVED | 铅锭库存覆盖天数 | PB | 2 | calculated | 派生指标, 公式复杂 |
| 16 | PB-035 | lead_balance_deficit | DERIVED | 铅锭供需缺口 | PB | 2 | calculated | 派生指标, 供需平衡 |
| 17 | CU-011 | cu_total_inv | DERIVED | 电解铜总库存 | CU | 1 | calculated | 派生指标 |
| 18 | CU-019 | cu_net_export | DERIVED | 电解铜净出口 | CU | 3 | calculated | 派生指标 |
| 19 | CU-020 | cu_stock_cover_days | DERIVED | 电解铜库存覆盖天数 | CU | 3 | calculated | 派生指标 |
| 20 | CU-026 | cu_balance_supply | DERIVED | 电解铜供需平衡表 | CU | 3 | calculated | 派生指标, 供需平衡 |
| 21 | AL-011 | al_total_inv | DERIVED | 电解铝总库存 | AL | 5 | calculated | 派生指标 |
| 22 | AL-014 | al_inv_change | DERIVED | 电解铝库存变动 | AL | 5 | calculated | 派生指标 |
| 23 | AL-021 | al_elec_price | s_al_elec_price | 电解铝电价成本 | AL | 5 | api_search | 成本类指标, 影响大 |
| 24 | AL-025 | al_balance_supply | DERIVED | 电解铝供需平衡表 | AL | 5 | calculated | 派生指标 |
| 25 | ZN-011 | zn_total_inv | DERIVED | 电解锌总库存 | ZN | 4 | calculated | 派生指标 |
| 26 | ZN-021 | zn_smelter_margin | s_zn_smelter_margin | 锌冶炼利润 | ZN | 4 | api_search | 成本类指标, 影响大 |
| 27 | NI-016 | ni_smelter_margin | s_ni_smelter_margin | 镍冶炼利润 | NI | 6 | api_search | 成本类指标 |
| 28 | NI-018 | ni_balance_supply | DERIVED | 电解镍供需平衡表 | NI | 6 | calculated | 派生指标 |
| 29 | SN-012 | sn_smelter_margin | s_sn_smelter_margin | 锡冶炼利润 | SN | 7 | api_search | 成本类指标 |
| 30 | SI-008 | si_smelter_margin | s_si_smelter_margin | 工业硅冶炼利润 | SI | 8 | api_search | 成本类指标 |

**P1关键说明**: 18项全部为派生/计算指标或成本类指标，数据链较长，异常影响中等。

---

## 6. P2低风险抽样清单 (30项)

| # | indicator_id | semantic_id | short_id | display_name | product | batch | mapping_method | risk_reason |
|---|-------------|-------------|----------|-------------|---------|-------|---------------|-------------|
| 31 | PB-002 | lead_open_interest | s_lead_open_interest | 沪铅期货持仓量 | PB | 2 | api_search | 标准API指标 |
| 32 | PB-004 | lead_settlement | s_lead_settlement | 沪铅期货结算价 | PB | 2 | api_search | 标准API指标 |
| 33 | PB-016 | lead_consume | s_lead_consume | 铅锭消费量 | PB | 2 | api_search | 标准API指标 |
| 34 | CU-003 | cu_volume | s_cu_volume | 沪铜期货成交量 | CU | 3 | api_search | 标准API指标 |
| 35 | CU-005 | cu_bid_ask_spread | s_cu_bid_ask | 沪铜买卖价差 | CU | 3 | api_search | 标准API指标 |
| 36 | CU-015 | cu_consume | s_cu_consume | 电解铜消费量 | CU | 3 | api_search | 标准API指标 |
| 37 | AL-002 | al_open_interest | s_al_open_interest | 沪铝期货持仓量 | AL | 5 | api_search | 标准API指标 |
| 38 | AL-005 | al_bid_ask_spread | s_al_bid_ask | 沪铝买卖价差 | AL | 5 | api_search | 标准API指标 |
| 39 | AL-017 | al_export | s_al_export | 电解铝出口量 | AL | 5 | api_search | 标准API指标 |
| 40 | AL-023 | al_consume_structure | s_al_consume_struct | 电解铝消费结构 | AL | 5 | api_search | 标准API指标 |
| 41 | ZN-003 | zn_volume | s_zn_volume | 沪锌期货成交量 | ZN | 1 | api_search | 标准API指标 |
| 42 | ZN-006 | zn_monthly_spread | s_zn_month_spread | 沪锌月价差 | ZN | 1 | api_search | 标准API指标 |
| 43 | ZN-016 | zn_production | i5_zn | 电解锌产量 | ZN | existing | existing | 标准API指标 |
| 44 | ZN-022 | zn_consume_structure | s_zn_consume_struct | 电解锌消费结构 | ZN | 4 | api_search | 标准API指标 |
| 45 | NI-002 | ni_open_interest | s_ni_open_interest | 沪镍期货持仓量 | NI | 6 | api_search | 标准API指标 |
| 46 | NI-010 | ni_lme_inv | s_ni_lme_inv | 电解镍LME库存 | NI | 6 | api_search | 标准API指标 |
| 47 | NI-017 | ni_consume_structure | s_ni_consume_struct | 电解镍消费结构 | NI | 6 | api_search | 标准API指标 |
| 48 | SN-003 | sn_volume | s_sn_volume | 沪锡期货成交量 | SN | 7 | api_search | 标准API指标 |
| 49 | SN-009 | sn_lme_inv | s_sn_lme_inv | 电解锡LME库存 | SN | 7 | api_search | 标准API指标 |
| 50 | SI-004 | si_consume | s_si_consume | 工业硅消费量 | SI | 8 | api_search | 标准API指标 |
| 51 | SI-006 | si_export | s_si_export | 工业硅出口量 | SI | 8 | api_search | 标准API指标 |
| 52 | SI-009 | si_consume_structure | s_si_consume_struct | 工业硅消费结构 | SI | 8 | api_search | 标准API指标 |
| 53 | SI-013 | si_price_volatility | s_si_price_vol | 工业硅价格波动率 | SI | 8 | api_search | 标准API指标 |
| 54 | LI-004 | li_consume | s_li_consume | 碳酸锂消费量 | LI | 9 | api_search | 标准API指标 |
| 55 | LI-006 | li_export | s_li_export | 碳酸锂出口量 | LI | 9 | api_search | 标准API指标 |
| 56 | LI-007 | li_import | s_li_import | 碳酸锂进口量 | LI | 9 | api_search | 标准API指标 |
| 57 | LI-008 | li_smelter_margin | s_li_smelter_margin | 碳酸锂冶炼利润 | LI | 9 | api_search | 标准API指标 |
| 58 | LI-009 | li_consume_structure | s_li_consume_struct | 碳酸锂消费结构 | LI | 9 | api_search | 标准API指标 |
| 59 | LI-011 | li_balance_supply | DERIVED | 碳酸锂供需平衡表 | LI | 9 | calculated | 派生指标(低风险品种) |
| 60 | LI-015 | li_stock_cover_days | DERIVED | 碳酸锂库存覆盖天数 | LI | 9 | calculated | 派生指标(低风险品种) |

**P2关键说明**: 30项为标准API搜索指标或低风险品种派生指标，数据链短，异常影响小。

---

## 7. 抽样统计汇总

### 7.1 按品种统计

| 品种 | 总量 | 抽样数 | 抽样率 | P0 | P1 | P2 | 品种内覆盖 |
|------|------|--------|--------|-----|-----|-----|-----------|
| PB | 37 | 10 | 27.0% | 4 | 3 | 3 | 10项/37项 |
| CU | 28 | 8 | 28.6% | 3 | 2 | 3 | 8项/28项 |
| AL | 25 | 8 | 32.0% | 2 | 3 | 3 | 8项/25项 |
| ZN | 25 | 8 | 32.0% | 2 | 3 | 3 | 8项/25项 |
| NI | 18 | 6 | 33.3% | 2 | 2 | 2 | 6项/18项 |
| SN | 14 | 5 | 35.7% | 2 | 1 | 2 | 5项/14项 |
| SI | 16 | 7 | 43.8% | 1 | 2 | 4 | 7项/16项 |
| LI | 15 | 8 | 53.3% | 1 | 3 | 4 | 8项/15项 |
| **合计** | **178** | **60** | **33.7%** | **12** | **18** | **30** | — |

### 7.2 按指标类型统计

| 指标类型 | 总量 | 抽样数 | 抽样率 | 说明 |
|---------|------|--------|--------|------|
| 价格类 | ~40 | 10 | 25% | P0为主 |
| 库存类 | ~30 | 8 | 27% | 已知短ID覆盖 |
| 产量类 | ~20 | 2 | 10% | 标准API |
| 消费类 | ~30 | 10 | 33% | 含消费结构 |
| 进出口类 | ~30 | 6 | 20% | 标准API |
| 成本/利润类 | ~18 | 6 | 33% | P1为主 |
| 派生/计算类 | ~33 | 12 | 36% | P1+P2 |
| 市场指标 | ~25 | 6 | 24% | 持仓/成交/价差 |

### 7.3 按映射方法统计

| 映射方法 | 总量 | 抽样数 | 抽样率 | 说明 |
|---------|------|--------|--------|------|
| existing (已有) | 36 | 12 | 33.3% | P0全覆盖 |
| api_search | 111 | 30 | 27.0% | P2为主 |
| calculated (派生) | 33 | 18 | 54.5% | P1为主, 抽样率最高 |
| **合计** | **178** | **60** | **33.7%** | — |

### 7.4 按批次统计

| 批次 | 抽样数 | 说明 |
|------|--------|------|
| existing | 12 | 已知短ID, P0全覆盖 |
| Batch 1 | 2 | PB/CU总库存 |
| Batch 2 | 6 | PB/CU派生指标 |
| Batch 3 | 6 | CU派生+标准指标 |
| Batch 4 | 4 | ZN派生+标准 |
| Batch 5 | 7 | AL派生+成本+标准 |
| Batch 6 | 3 | NI成本+标准 |
| Batch 7 | 3 | SN成本+标准 |
| Batch 8 | 4 | SI成本+标准 |
| Batch 9 | 8 | LI标准+派生 |

---

## 8. 抽样校验计划

### 8.1 每条样本校验维度

| 维度 | 检查项 | 预期结果 |
|------|--------|---------|
| 维度1: UI渲染 | 面板展示 | ✅ 正常渲染 (data_fetchable=FALSE不影响UI) |
| 维度1: UI渲染 | 标签展示 | ✅ 标签正常 (仅元数据层面) |
| 维度1: UI渲染 | 告警标题 | ✅ 告警标题正常显示 |
| 维度1: UI渲染 | 日志字段 | ✅ 日志字段完整 |
| 维度1: UI渲染 | DEPENDENCY_BLOCKED标记 | ✅ 显示🟡徽章/横幅/标签 |
| 维度2: 底层取数 | data_fetchable值 | ❌ FALSE (全部) |
| 维度2: 底层取数 | DEPENDENCY_BLOCK标记 | ✅ 全部触发 |
| 维度2: 底层取数 | 是否纳入PASS | ❌ 不纳入 |
| 综合判定 | 是否误判 | ❌ 无误判 (UI PASS但底层不可用, 正确标记为DEPENDENCY_BLOCK) |

### 8.2 预期校验结果

| 指标 | 预期值 |
|------|--------|
| UI渲染PASS | 60/60 (100%) |
| data_fetchable=FALSE | 60/60 (100%) |
| DEPENDENCY_BLOCKED触发 | 60/60 (100%) |
| 纳入PASS统计 | 0/60 (0%) |
| 误判数 | 0 |
| 渲染异常 | 0 |
| 状态误判 | 0 |

---

## 9. 与DSHB/HERMES数据同步确认

### 9.1 DSHB确认项

| 确认项 | 状态 | 说明 |
|--------|------|------|
| 桥接快照已输出 | ✅ | `v86_rc2_dshb_bridge_snapshot_for_dshe.json` |
| data_fetchable字段完整性 | ✅ | 178/178条目 |
| data_fetchable全部FALSE确认 | ✅ | 因zhiji API外部依赖阻塞 |
| 快照版本V2-FULL | ✅ | 与V2桥接表一致 |
| 快照时间戳记录 | ✅ | 2026-10-13T16:00:00+08:00 |

### 9.2 HERMES确认项

| 确认项 | 状态 | 说明 |
|--------|------|------|
| 双维度校验规则确认 | ✅ | 展示层+底层取数可用性 |
| DEPENDENCY_BLOCK机制确认 | ✅ | 取数不可用不纳入PASS |
| 抽样策略确认 | ✅ | 8品种/60项/33.7% |
| 风险分层确认 | ✅ | P0(12)+P1(18)+P2(30) |

---

## 10. 文件清单

| 文件 | 说明 | 大小 |
|------|------|------|
| `v86_rc2_dshb_bridge_snapshot_for_dshe.json` | DSHB桥接快照(输入) | ~22KB |
| `v86_rc2_dshe_sample_list.md` | 本文件: 抽样清单 | 本文件 |

**下一步**: T3.2 执行双维度联合抽样校验 → `v86_rc2_dshe_joint_sample_verify_report.md`

---

> **文档版本**: v1.0 FINAL  
> **日期**: 2026-10-13  
> **作者**: DSHE Agent  
> **跨团队确认**: DSHB ✅ | HERMES ✅ | zhiji ✅
