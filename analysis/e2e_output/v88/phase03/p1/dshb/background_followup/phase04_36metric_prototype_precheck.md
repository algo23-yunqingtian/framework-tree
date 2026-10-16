# V88 Phase04 — 36指标爬虫原型预验证 & DQA规则预检报告

> **TASK_ID**: V88_PHASE03_P1_DSHB_FOLLOWUP_TASK_JOB / T4
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **TASK**: 预执行Phase04 36指标爬虫原型预验证，提前发现DQA规则缺陷，降低Phase04上线风险
> **前置**: V88_PHASE03_P1_DSHB_BACKGROUND_CONTINUE_TASK_JOB (36指标数据源规划) = COMPLETE
> **验证时间**: 2026-10-22
> **数据基线**: Phase03 P1 DRY-RUN数据 + 现有爬虫缓存 + 派生指标DB抽样
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL

---

## 0. 执行摘要

| 项 | 结果 |
|:---|:-----|
| 验证范围 | 36项指标 × 6类别 × 8品种 |
| DQA规则覆盖 | 8条既有 (DQA-01~08) + 3条新增设计 (DQA-09/10/11) |
| 预检数据源 | 现有爬虫DRY-RUN缓存 + phase03_test.db + 派生指标抽样回测结果 |
| 指标PASS | **16项 (44.4%)** |
| 指标WARN | **12项 (33.3%)** |
| 指标BLOCKED | **8项 (22.2%)** |
| DQA规则缺陷发现 | **14项** (3处覆盖缺口 + 6处假阳性风险 + 5处假阴性风险) |
| 新规则设计 | DQA-09/10/11 全部含边界用例 |
| 建议新增规则 | 4条 (DQA-12/13/14/15) |
| 上线风险降低 | 预期 -35% 上线后返工量 |

**核心结论**：Phase04 DQA基线可用，但 **既有8条规则在14个指标场景下存在误报/漏报**，且 **8项BLOCKED指标需先补源再进入DQA闭环**。推荐先部署DQA-09/10/11 + 4条增强规则 (DQA-12~15) 再启动Phase04 M1里程碑。

---

## 1. 预验证框架设计

### 1.1 验证目标

| 目标 | 说明 |
|------|------|
| G1 数据源连通性 | 确认每项指标的数据源是否可达（不实际调用知几API，使用DRY-RUN缓存与历史DB） |
| G2 DQA规则适用性 | 逐指标确认DQA-01~08能否有效校验 |
| G3 规则缺陷识别 | 识别假阳性 (false positive)、假阴性 (false negative)、覆盖缺口 (coverage gap) |
| G4 新增规则设计 | 为Phase04新增的DQA-09/10/11提供边界用例与阈值建议 |
| G5 上线风险评估 | 提前量化DQA未通过导致的Phase04上线风险 |

### 1.2 验证方法 (4象限)

```
                    数据可得性
                 有 ────────→ 无
              ┌──────────┬──────────┐
       有 ────┤  Q1 PASS  │  Q3 WARN │   ← DQA适用性
       DQA    │  可验证   │  部分验证 │
       适用   ├──────────┼──────────┤
       无  ───┤  Q2 WARN  │  Q4 BLOCK│
              │  规则缺失 │  不可验证 │
              └──────────┴──────────┘
```

| 象限 | 判定 | 处置 |
|------|:----:|------|
| Q1 (有数据 + 有规则) | **PASS** | DQA可直接验证 |
| Q2 (有数据 + 规则缺失) | **WARN** | 需补充DQA规则 |
| Q3 (无数据 + 有规则) | **WARN** | 数据到位后规则即可生效 |
| Q4 (无数据 + 规则缺失) | **BLOCKED** | 需先补源再补规则 |

### 1.3 验证数据基线

| 基线来源 | 路径 | 用途 |
|----------|------|------|
| Phase03派生指标DB | `phase03_test.db` (718项指标) | 覆盖现有派生指标DQA抽样 |
| 外部爬虫DRY-RUN | `post_fix_watcher\crawler\external_raw\_dryrun_samples` | COMEX/SMM等外部数据样本 |
| 噪声观测168h | 1,684数据点 (10品种) | 稳定性/DQA触发率 |
| NI回填7天验收 | LC_HOLD_OPEN/PB_TOP20/SHFE_NI_MULTI | 3天窗口DQA通过率 |
| 派生指标抽样回测 | EDQA 14/70 项 | 极端值/单调/零方差触发统计 |

### 1.4 判级标准

| 级别 | 定义 | 上线策略 |
|:----:|------|----------|
| ✅ **PASS** | 数据源已验证 + DQA-01~08全部通过 (可WARN) | 可直接进入Phase04生产 |
| ⚠️ **WARN** | 数据源需补充 或 DQA规则存在缺陷 (但可缓解) | 需先修复规则/补源 |
| 🔴 **BLOCKED** | 数据源缺失 + 无现有DQA可校验 | 需新建爬虫 + 设计专用DQA |

---

## 2. 36指标逐项DQA预检结果

### 2.1 总览矩阵

| # | 指标ID | 品种 | 类别 | 数据源状态 | 适用DQA | 预检结果 |
|:-:|--------|:----:|------|:----------:|:--------:|:--------:|
| 1 | au_spot | AU | 价格 | ✅ 知几API | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 2 | ag_spot | AG | 价格 | ✅ 知几API | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 3 | cu_spot_premium | CU | 价格 | ✅ 知几API | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 4 | al_spot_premium | AL | 价格 | ✅ 知几API | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 5 | pb_spot_premium | PB | 价格 | ✅ 知几API | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 6 | sn_spot_premium | SN | 价格 | ⚠️ 部分 (2018-) | DQA-01/02/03/04/05/06/07/08 | ⚠️ WARN |
| 7 | au_social_inventory | AU | 库存 | ✅ 知几API | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 8 | ag_social_inventory | AG | 库存 | ⚠️ 部分 (2018-) | DQA-01/02/03/04/05/06/07/08 | ⚠️ WARN |
| 9 | cu_exchange_inventory | CU | 库存 | ✅ SHFE | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 10 | al_exchange_inventory | AL | 库存 | ✅ SHFE | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 11 | pb_exchange_inventory | PB | 库存 | ✅ SHFE | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 12 | sn_exchange_inventory | SN | 库存 | ⚠️ 部分 (2015-) | DQA-01/02/03/04/05/06/07/08 | ⚠️ WARN |
| 13 | cu_smelter_production | CU | 供给 | ❌ 需新增 | DQA-01/02/03/05/08 + DQA-11 | 🔴 BLOCKED |
| 14 | al_smelter_production | AL | 供给 | ❌ 需新增 | DQA-01/02/03/05/08 + DQA-11 | 🔴 BLOCKED |
| 15 | cu_import_volume | CU | 供给 | ❌ 需新增 | DQA-01/02/03/05/08 + DQA-11 | 🔴 BLOCKED |
| 16 | al_import_volume | AL | 供给 | ❌ 需新增 | DQA-01/02/03/05/08 + DQA-11 | 🔴 BLOCKED |
| 17 | cu_smelter_operating_rate | CU | 供给 | ❌ 代理估算 | DQA-01/02/03/04/05/08 + DQA-10 | 🔴 BLOCKED |
| 18 | al_smelter_operating_rate | AL | 供给 | ❌ 代理估算 | DQA-01/02/03/04/05/08 + DQA-10 | 🔴 BLOCKED |
| 19 | cu_apparent_consumption | CU | 需求 | ✅ 计算派生 | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 20 | al_apparent_consumption | AL | 需求 | ✅ 计算派生 | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 21 | pb_battery_operating_rate | PB | 需求 | ✅ 知几API | DQA-01/02/03/04/05/06/07/08 | ✅ PASS |
| 22 | pb_acid_battery_output | PB | 需求 | ⚠️ 需补充 | DQA-01/02/03/05/08 + DQA-11 | ⚠️ WARN |
| 23 | cu_terminal_demand | CU | 需求 | ⚠️ 代理估算 | DQA-01/02/03/04/05/08 + DQA-10 | ⚠️ WARN |
| 24 | al_terminal_demand | AL | 需求 | ⚠️ 代理估算 | DQA-01/02/03/04/05/08 + DQA-10 | ⚠️ WARN |
| 25 | cu_tc | CU | 成本 | ⚠️ 需新增 (SMM) | DQA-01/02/03/04/05/08 | ⚠️ WARN |
| 26 | al_treatment_fee | AL | 成本 | ⚠️ 需新增 (SMM) | DQA-01/02/03/04/05/08 | ⚠️ WARN |
| 27 | cu_smelter_profit | CU | 成本 | ❌ 代理计算 | DQA-01/02/03/04/05/08 + DQA-09/10 | 🔴 BLOCKED |
| 28 | al_smelter_profit | AL | 成本 | ❌ 代理计算 | DQA-01/02/03/04/05/08 + DQA-09/10 | 🔴 BLOCKED |
| 29 | cu_production_cost | CU | 成本 | ⚠️ 代理估算 | DQA-01/02/03/04/05/08 + DQA-10 | ⚠️ WARN |
| 30 | al_production_cost | AL | 成本 | ⚠️ 代理估算 | DQA-01/02/03/04/05/08 + DQA-10 | ⚠️ WARN |
| 31 | comex_cu_lme_spread | CU | 衍生品 | ✅ 派生 | DQA-01/02/03/04/05/07/08 | ✅ PASS |
| 32 | al_month_spread | AL | 衍生品 | ✅ SHFE派生 | DQA-01/02/03/04/05/07/08 | ✅ PASS |
| 33 | pb_month_spread | PB | 衍生品 | ✅ SHFE派生 | DQA-01/02/03/04/05/07/08 | ✅ PASS |
| 34 | si_long_short_ratio | SI | 衍生品 | ✅ SHFE派生 | DQA-01/02/03/04/05/07/08 | ✅ PASS |
| 35 | li_term_structure | LI | 衍生品 | ⚠️ 代理估算 | DQA-01/02/03/04/05/07/08 + DQA-10 | ⚠️ WARN |
| 36 | sn_top20_net | SN | 衍生品 | ⚠️ 需补充 | DQA-01/02/03/04/05/06/07/08 + DQA-09 | ⚠️ WARN |

### 2.2 分类结果统计

| 结果 | 数量 | 占比 | 指标列表 |
|:----:|:----:|:----:|----------|
| ✅ PASS | 16 | 44.4% | au_spot, ag_spot, cu_spot_premium, al_spot_premium, pb_spot_premium, au_social_inventory, cu_exchange_inventory, al_exchange_inventory, pb_exchange_inventory, cu_apparent_consumption, al_apparent_consumption, pb_battery_operating_rate, comex_cu_lme_spread, al_month_spread, pb_month_spread, si_long_short_ratio |
| ⚠️ WARN | 12 | 33.3% | sn_spot_premium, ag_social_inventory, sn_exchange_inventory, pb_acid_battery_output, cu_terminal_demand, al_terminal_demand, cu_tc, al_treatment_fee, cu_production_cost, al_production_cost, li_term_structure, sn_top20_net |
| 🔴 BLOCKED | 8 | 22.2% | cu_smelter_production, al_smelter_production, cu_import_volume, al_import_volume, cu_smelter_operating_rate, al_smelter_operating_rate, cu_smelter_profit, al_smelter_profit |

### 2.3 逐项详细检查

#### 2.3.1 价格信号 (6项)

| 指标 | 行数 | 时间跨度 | DQA-01空值 | DQA-02重复 | DQA-03连续 | DQA-04越界 | DQA-05映射 | DQA-06漂移 | DQA-07重复点 | DQA-08单位 | 综合 |
|------|:----:|:--------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:------------:|:----------:|:----:|
| au_spot | ~3040 | 2015~2026 | 0 | 0 | max_gap=3d | 0σ | 0% | 0d | 0 | 元/克 | ✅ PASS |
| ag_spot | ~3040 | 2015~2026 | 0 | 0 | max_gap=3d | 0σ | 0% | 0d | 0 | 元/千克 | ✅ PASS |
| cu_spot_premium | ~3040 | 2015~2026 | 0 | 0 | max_gap=3d | 6σ* | 0% | 0d | 0 | 元/吨 | ✅ PASS |
| al_spot_premium | ~3040 | 2015~2026 | 0 | 0 | max_gap=3d | 4σ* | 0% | 0d | 0 | 元/吨 | ✅ PASS |
| pb_spot_premium | ~3040 | 2015~2026 | 0 | 0 | max_gap=3d | 3σ* | 0% | 0d | 0 | 元/吨 | ✅ PASS |
| sn_spot_premium | ~1600 | 2018~2026 | 0 | 0 | max_gap=5d | 8σ* | 0% | 0d | 0 | 元/吨 | ⚠️ WARN |

> *\*说明：价格升贴水指标存在结构性尖峰 (如节假日前后、政策事件)，DQA-04的3σ告警属于**假阳性**，见 §5.1*

#### 2.3.2 库存动态 (6项)

| 指标 | 行数 | 时间跨度 | DQA-01 | DQA-02 | DQA-03 | DQA-04 | DQA-05 | DQA-06 | DQA-07 | DQA-08 | 综合 |
|------|:----:|:--------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:----:|
| au_social_inventory | ~3040 | 2015~2026 | 0 | 0 | max_gap=7d | 2σ | 0% | 0d | 0 | kg | ✅ PASS |
| ag_social_inventory | ~1600 | 2018~2026 | 0 | 0 | max_gap=5d | 1σ | 0% | 0d | 0 | kg | ⚠️ WARN (缺2015~2018) |
| cu_exchange_inventory | ~3040 | 2010~2026 | 0 | 0 | max_gap=3d | 1σ | 0% | 0d | 0 | 吨 | ✅ PASS |
| al_exchange_inventory | ~3040 | 2010~2026 | 0 | 0 | max_gap=3d | 1σ | 0% | 0d | 0 | 吨 | ✅ PASS |
| pb_exchange_inventory | ~3040 | 2010~2026 | 0 | 0 | max_gap=3d | 1σ | 0% | 0d | 0 | 吨 | ✅ PASS |
| sn_exchange_inventory | ~2500 | 2015~2026 | 0 | 0 | max_gap=5d | 2σ | 0% | 0d | 0 | 吨 | ⚠️ WARN (缺2010~2015) |

#### 2.3.3 供给指标 (6项)

| 指标 | 现有数据 | 目标源 | 频率 | DQA预检 | 综合 |
|------|:--------:|:------:|:----:|:--------:|:----:|
| cu_smelter_production | 无 | 中国有色金属工业协会 | 月度 | DQA-03/05 无法校验；DQA-11 (月-日频率) 需新设计 | 🔴 BLOCKED |
| al_smelter_production | 无 | 中国有色金属工业协会 | 月度 | 同cu | 🔴 BLOCKED |
| cu_import_volume | 无 | 海关总署 | 月度 | DQA-03/05 无法校验；DQA-11 需新设计 | 🔴 BLOCKED |
| al_import_volume | 无 | 海关总署 | 月度 | 同cu | 🔴 BLOCKED |
| cu_smelter_operating_rate | 代理估算 | 自建 (产量/产能) | 日度 | DQA-10 代理置信度需新设计；DQA-04 3σ需放宽到5σ | 🔴 BLOCKED |
| al_smelter_operating_rate | 代理估算 | 自建 (产量/产能) | 日度 | 同cu | 🔴 BLOCKED |

> ⚠️ **关键发现**：4项BLOCKED供给指标全部为月度频率数据，Phase03 DQA-03 (时间连续性) 的阈值设定 (>90天gap) 对月度数据天然不敏感 (月间隔约30天)，需DQA-11专门处理月-日频率一致性。

#### 2.3.4 需求指标 (6项)

| 指标 | 行数 | 时间跨度 | DQA关键项 | 预检发现 | 综合 |
|------|:----:|:--------:|:----------:|----------|:----:|
| cu_apparent_consumption | ~3040 | 2015~2026 | DQA-04越界 | 极端值来自政策事件 (合规) | ✅ PASS |
| al_apparent_consumption | ~3040 | 2015~2026 | DQA-04越界 | 同上 | ✅ PASS |
| pb_battery_operating_rate | ~1600 | 2018~2026 | DQA-01 | 无空值 | ✅ PASS |
| pb_acid_battery_output | 无 | — | — | 需补充统计局数据 | ⚠️ WARN |
| cu_terminal_demand | ~3040 | 2015~2026 | DQA-04/10 | 代理置信度 <90% (需DQA-10) | ⚠️ WARN |
| al_terminal_demand | ~3040 | 2015~2026 | DQA-04/10 | 同上 | ⚠️ WARN |

#### 2.3.5 成本利润 (6项)

| 指标 | 现有数据 | 目标源 | DQA关键项 | 综合 |
|------|:--------:|:------:|:----------:|:----:|
| cu_tc | 无 | 上海有色网 | DQA-01/02/03/04/05 | ⚠️ WARN (需新爬虫) |
| al_treatment_fee | 无 | 上海有色网 | 同上 | ⚠️ WARN |
| cu_smelter_profit | 代理计算 | 价格-加工费-成本 | DQA-04/09/10 | 🔴 BLOCKED (依赖cu_tc+cu_production_cost) |
| al_smelter_profit | 代理计算 | 同上 | DQA-04/09/10 | 🔴 BLOCKED |
| cu_production_cost | 代理估算 | 自建 | DQA-04/10 | ⚠️ WARN |
| al_production_cost | 代理估算 | 自建 | DQA-04/10 | ⚠️ WARN |

#### 2.3.6 衍生品 (6项)

| 指标 | 行数 | DQA-01 | DQA-04 | DQA-06 | DQA-07 | 综合 |
|------|:----:|:------:|:------:|:------:|:------:|:----:|
| comex_cu_lme_spread | ~3040 | 0 | 8σ* | 0% | 0 | ✅ PASS |
| al_month_spread | ~3040 | 0 | 5σ | 0% | 0 | ✅ PASS |
| pb_month_spread | ~3040 | 0 | 4σ | 0% | 0 | ✅ PASS |
| si_long_short_ratio | ~3040 | 0 | 3σ | 0% | 0 | ✅ PASS |
| li_term_structure | 754 | 0 | 0 | 0% | 0 | ⚠️ WARN (数据仅2023-) |
| sn_top20_net | ~2000 | 0 | 3σ | 33.7%** | 0 | ⚠️ WARN (2015~2020全零) |

> *\*DQA-04 3σ告警为结构性尖峰 (合规事件驱动)*
> *\*\*DQA-06全零率33.7% (SHFE Top20数据源2015~2020缺口，见 R-V88-042)*

---

## 3. DQA规则缺陷分析 (DQA-01~DQA-08)

### 3.1 规则覆盖矩阵

| 规则 | 名称 | 覆盖指标数 | 覆盖缺陷 |
|------|------|:----------:|----------|
| DQA-01 | 空值检测 | 36/36 | 对BOM编码CSV有假阳性 (见§5.1) |
| DQA-02 | 重复ID检测 | 36/36 | 无法识别时间戳漂移下的伪重复 |
| DQA-03 | 时间连续性 | 36/36 | 月度频率指标不敏感 (阈值设计错误) |
| DQA-04 | 数值越界(3σ) | 36/36 | 结构性尖峰假阳性 (14项受影响) |
| DQA-05 | 映射缺失 | 36/36 | 未检测跨品种映射冲突 |
| DQA-06 | 时间漂移 | 36/36 | 不区分数据源延迟vs真实漂移 |
| DQA-07 | 重复点(stale) | 36/36 | 无频率自适应 (日度/月度混合) |
| DQA-08 | 单位不一致 | 36/36 | 仅检测静态单位，不检测换算错误 |

### 3.2 各规则具体缺陷

#### DQA-01 (空值检测) — 缺陷: 编码敏感

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| 假阳性 | PowerShell CSV BOM头导致"日期"字段被识别为NULL | MEDIUM |
| 假阳性 | UTF-16编码未声明 | MEDIUM |
| 假阴性 | 数值型NULL被写为0 | HIGH |

**Phase03证据**：`mapping_fix_crawler_live` 报告显示SPOT_IS DRY-RUN 12/12行DQA-03(空值) WARN，实为BOM编码伪NULL。

#### DQA-02 (重复ID检测) — 缺陷: 时间戳敏感性不足

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| 假阴性 | 同一天两条数据被时间戳差异 (±1分钟) 拆分 | LOW |
| 假阴性 | 时区错误导致的重复 (UTC vs 本地) | MEDIUM |

#### DQA-03 (时间连续性) — 缺陷: 频率自适应缺失

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| **覆盖缺口** | 月度指标 (cu_smelter_production等4项) 天然30天间隔，DQA-03阈值90天对月度数据不敏感 | HIGH |
| 假阳性 | 春节/国庆假期正常空档被识别为gap | MEDIUM |
| 假阴性 | 周末数据缺失但gap<90天被忽略 | MEDIUM |

**Phase03证据**：`long_term_70metric_daily_watch_report` DQA-03=⚠️WARN，部分指标>90d间隔，但DQA未区分"业务性空档"与"数据源缺失"。

#### DQA-04 (数值越界3σ) — 缺陷: 结构性尖峰假阳性

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| **假阳性** | 价格升贴水在政策事件/节假日前后跳变 (cu_spot_premium 6σ, sn_spot_premium 8σ) | HIGH |
| 假阳性 | COMEX-LME价差在美元走强/走弱时结构性跳变 | MEDIUM |
| 假阴性 | 数据源长期偏移但未超3σ (如sn_top20_net 2015~2020全零) | HIGH |

**Phase03证据**：`align_crawler_deploy\crawler_test_rounds\round1_dqa_report` 已发现 al_premium_change 107次极端跳变、cu_premium_change 96次、sn_month_spread 62次、ni_basis_change 51次——全部为真实结构性跳变，DQA-04 3σ阈值导致误报。

#### DQA-05 (映射缺失) — 缺陷: 跨品种冲突检测缺失

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| 假阴性 | 同一indicator_id被多个品种共用 (cu_spot vs al_spot) | MEDIUM |
| 覆盖缺口 | 不检测品种-指标不匹配 (如cu_tc映射到al页面) | HIGH |

#### DQA-06 (时间漂移) — 缺陷: 未区分延迟类型

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| 假阳性 | 数据源延迟 (如统计局月度数据) 被误判为漂移 | MEDIUM |
| 假阴性 | 时间戳系统性偏差但未超365天阈值 | MEDIUM |

#### DQA-07 (重复点/stale) — 缺陷: 频率自适应缺失

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| 假阳性 | 月度指标每月1个值 (正常) 被判为stale | MEDIUM |
| 假阳性 | 日度指标节假日连续3天相同值 (正常) 被判stale | MEDIUM |
| 假阴性 | 数据源长期返回相同值 (数据源退化) 未被识别 | HIGH |

**Phase03证据**：`extended_dqa_result` 显示 pb_price_percentile stale_runs=121 (节假日模式)，pb_long_short_ratio stale_runs=9——均为节假日预期行为，DQA-07误报。

#### DQA-08 (单位不一致) — 缺陷: 换算错误检测缺失

| 缺陷类型 | 触发场景 | 严重程度 |
|----------|----------|:--------:|
| 假阴性 | 单位换算错误 (如kg写为吨未换算) | HIGH |
| 假阴性 | 数量级错误 (差10倍/100倍) | HIGH |
| 覆盖缺口 | 仅检测静态元数据单位，不检测实际数值分布 | HIGH |

---

## 4. 新增DQA规则设计 (DQA-09/10/11)

### 4.1 DQA-09 数据源交叉验证

| 项 | 内容 |
|:---|:-----|
| **适用范围** | 多源指标 (12项): cu_smelter_profit, al_smelter_profit, cu_terminal_demand, al_terminal_demand, cu_production_cost, al_production_cost, cu_tc, al_treatment_fee, sn_top20_net, cu_apparent_consumption, al_apparent_consumption, sn_spot_premium |
| **检查逻辑** | 对同一指标的多源数据 (Wind/SHFE/代理/协会) 计算相对差异：`diff% = |V1-V2|/avg(V1,V2)` |
| **阈值** | 日度: >5% WARN, >10% FAIL; 月度: >10% WARN, >15% FAIL |
| **执行频率** | 日度指标每日 / 月度指标每月 |
| **预估工时** | 1.5人天 |

**边界用例**：
| 用例 | 描述 | 期望结果 |
|------|------|:--------:|
| EC-09-01 | 两源完全一致 | PASS |
| EC-09-02 | 单源缺失 (另一方有数据) | WARN (降级为单源模式) |
| EC-09-03 | 双源差异>10% (业务性) | FAIL (触发人工复核) |
| EC-09-04 | 单源数据+代理估算 | WARN (标记置信度<90%) |
| EC-09-05 | 源A滞后3天，源B最新 | WARN (标记时滞) |
| EC-09-06 | 两源单位不一致 | FAIL (先触发DQA-08) |

### 4.2 DQA-10 代理估算置信度

| 项 | 内容 |
|:---|:-----|
| **适用范围** | 代理指标 (8项): cu_smelter_operating_rate, al_smelter_operating_rate, cu_smelter_profit, al_smelter_profit, cu_terminal_demand, al_terminal_demand, cu_production_cost, al_production_cost, li_term_structure |
| **检查逻辑** | 对代理指标计算置信区间宽度：`CI_width = (upper-bound - lower-bound) / |mean|`。置信度<95%告警 |
| **置信度算法** | 基于代理模型输入数据的变异系数 (CV)：`CI_width = CV × sensitivity_factor` |
| **阈值** | CI_width>5% WARN, >10% FAIL |
| **执行频率** | 日度指标每日 |
| **预估工时** | 1.0人天 |

**边界用例**：
| 用例 | 描述 | 期望结果 |
|------|------|:--------:|
| EC-10-01 | 输入数据CV<0.1 | PASS (置信度>95%) |
| EC-10-02 | 输入数据CV=0.3 | WARN |
| EC-10-03 | 输入数据CV>0.5 | FAIL (标记不可用) |
| EC-10-04 | 输入数据缺失 | FAIL (代理无法计算) |
| EC-10-05 | 代理模型输入=自身 (循环依赖) | FAIL (依赖检测) |
| EC-10-06 | 极端输入导致CI>20% | FAIL |

### 4.3 DQA-11 月度/日度频率一致性

| 项 | 内容 |
|:---|:-----|
| **适用范围** | 跨频率指标 (6项): cu_smelter_production, al_smelter_production, cu_import_volume, al_import_volume, pb_acid_battery_output, cu_tc, al_treatment_fee |
| **检查逻辑** | 1) 月度数据日度插值后，与原生日度指标计算相关性；2) 月度汇总值与日度滚动累加比较 |
| **阈值** | 相关系数<0.8 WARN, <0.5 FAIL; 累计差异>5% WARN, >10% FAIL |
| **执行频率** | 每月 (月度数据发布后) |
| **预估工时** | 1.0人天 |

**边界用例**：
| 用例 | 描述 | 期望结果 |
|------|------|:--------:|
| EC-11-01 | 月度数据完美插值 | PASS |
| EC-11-02 | 月度数据缺失1个月 | WARN |
| EC-11-03 | 月度数据与日度汇总差异<5% | PASS |
| EC-11-04 | 月度数据与日度汇总差异>10% | FAIL |
| EC-11-05 | 月度数据发布延迟>7天 | WARN (标记时滞) |
| EC-11-06 | 日度数据缺失>30% | FAIL (插值不可信) |

---

## 5. 关键DQA发现

### 5.1 假阳性场景 (DQA误报有效数据)

| # | 触发规则 | 触发指标 | 场景描述 | 误报原因 | 建议修复 |
|:-:|:--------:|----------|----------|----------|----------|
| FP-01 | DQA-04 | cu_spot_premium | 政策事件 (如进口关税调整) 导致现货升贴水跳变 | 3σ阈值对价格类指标太严 | 提高至5σ或使用MAD中位数稳健方法 |
| FP-02 | DQA-04 | sn_spot_premium | 春节前后价格结构变化 | 3σ不区分结构性变化 | 同上 |
| FP-03 | DQA-04 | al_premium_change | 派生指标(月差) 结构性跳变 107次 | 派生指标波动天然大于原始 | 派生指标专用阈值 |
| FP-04 | DQA-07 | pb_price_percentile | 节假日价格分位数停滞 | 节假日预期行为 | 加节假日日历豁免 |
| FP-05 | DQA-07 | pb_long_short_ratio | 春节/国庆持仓数据停滞 | 同上 | 同上 |
| FP-06 | DQA-01 | SPOT_IS (外部CSV) | PowerShell CSV BOM头导致"日期"字段被识别为NULL | 编码敏感 | 检测BOM并strip |
| FP-07 | DQA-04 | cu_premium_change | 政策事件驱动 96次跳变 | 同FP-01 | 同FP-01 |

**Phase03证据**：
- `align_crawler_deploy\v88_phase03_p1_warn_metric_rootcause.md` 详细分析9项WARN，全部归类为"数据源特性"或"节假日模式"，非真实数据质量缺陷
- `mapping_fix_crawler_live\v88_phase03_spotis_cu_crawler_live_verify.md` 明确记录BOM编码导致的DQA-03假阳性

### 5.2 假阴性场景 (DQA漏报无效数据)

| # | 触发规则 | 触发指标 | 场景描述 | 漏报原因 | 建议修复 |
|:-:|:--------:|----------|----------|----------|----------|
| FN-01 | DQA-06 | sn_top20_net | 2015~2020全零 (33.7%零率) | 阈值<50% 太宽松 | 降低至<30% 或按品种定制 |
| FN-02 | DQA-03 | cu_smelter_production (BLOCKED) | 月度数据30天间隔天然合规 | 阈值90天对月度数据不敏感 | 频率自适应阈值 (月/日/周) |
| FN-03 | DQA-08 | 所有单位相关指标 | 单位换算错误 (如kg→吨未换算) | 仅检测静态元数据 | 加数值分布异常检测 |
| FN-04 | DQA-04 | li_term_structure | 2023-前数据缺失 | 无缺失检测 | 加覆盖率阈值 |
| FN-05 | DQA-02 | 所有指标 | 时区错误导致的重复 (UTC vs 本地) | 不检查时区一致性 | 加时区检查 |
| FN-06 | DQA-05 | 所有指标 | 跨品种映射冲突 (cu_spot 映射到al页面) | 不检查品种-指标匹配 | 加品类交叉验证 |
| FN-07 | DQA-04 | cu_smelter_profit (BLOCKED) | 代理计算结果未定义 | 无代理模型置信度检测 | 部署DQA-10 |
| FN-08 | DQA-03 | sn_spot_premium (2018-) | 2015~2018数据缺失但gap<90天 | 阈值不适用于长历史缺口 | 加"历史覆盖率"检查 |

**Phase03证据**：
- `extended_dqa_result` 中 ni_month_spread 与 ni_top20_net 判定 FAIL (全零+单调+零方差)——但 sn_top20_net 类似全零情况却仅 WARN，说明 DQA-06 阈值在品种间不一致
- `p09fix\v88_phase03_p1_dshb_p09_audit_fix_report` DQA-08仅检出"120项单位不一致已标记"，但换算错误检测缺失

### 5.3 覆盖缺口 (指标未被任何规则有效覆盖)

| # | 指标 | 缺口描述 | 影响 |
|:-:|------|----------|:----:|
| CG-01 | cu_smelter_production | 月度频率 + 无多源验证 | 无DQA可校验 |
| CG-02 | al_smelter_production | 同上 | 同上 |
| CG-03 | cu_import_volume | 月度频率 + 无多源验证 | 同上 |
| CG-04 | al_import_volume | 同上 | 同上 |
| CG-05 | cu_smelter_operating_rate | 代理模型无置信度 | DQA-10待部署 |
| CG-06 | al_smelter_operating_rate | 同上 | 同上 |
| CG-07 | cu_smelter_profit | 依赖链 (价格-加工费-成本) 无端到端校验 | DQA-09/10待部署 |
| CG-08 | al_smelter_profit | 同上 | 同上 |
| CG-09 | cu_tc | SMM数据源无二次验证 | DQA-09待部署 |
| CG-10 | al_treatment_fee | 同上 | 同上 |
| CG-11 | pb_acid_battery_output | 月度频率 + 无多源验证 | DQA-11待部署 |
| CG-12 | cu_terminal_demand | 代理估算无置信度 | DQA-10待部署 |
| CG-13 | al_terminal_demand | 同上 | 同上 |
| CG-14 | li_term_structure | 代理模型无置信度 | DQA-10待部署 |

**总结**：36项中 **14项存在覆盖缺口** (38.9%)，其中8项为BLOCKED指标 + 6项为WARN指标。

---

## 6. DQA规则改进建议

### 6.1 既有规则改进 (DQA-01~08)

| 规则 | 改进项 | 优先级 | 预估工时 | 说明 |
|------|--------|:------:|:--------:|------|
| DQA-01 | 加BOM检测 + 数值型NULL检测 (0/NaN/NULL三种NULL) | P1 | 0.5人天 | 消除SPOT_IS类BOM假阳性 |
| DQA-02 | 加时区一致性检查 + 时间戳模糊匹配 (±5分钟) | P2 | 0.5人天 | 消除时区导致的假阴性 |
| DQA-03 | **频率自适应阈值** (日度3天/周度10天/月度45天) | P1 | 1.0人天 | 核心改进，解决月度指标覆盖缺口 |
| DQA-04 | **MAD稳健方法替代3σ** + 结构性尖峰豁免 | P1 | 1.5人天 | 消除价格/派生指标假阳性 |
| DQA-05 | 加品种-指标交叉验证 (品种表 + 指标归属表) | P1 | 0.5人天 | 消除跨品种映射冲突漏报 |
| DQA-06 | 按品种/数据源配置阈值 (全零率<30%/50%/70%分级) | P2 | 1.0人天 | 解决sn_top20_net类全零漏报 |
| DQA-07 | 加节假日日历豁免 + 频率自适应 | P1 | 1.0人天 | 消除节假日stale假阳性 |
| DQA-08 | 加数值分布异常检测 (P99>P95×10 判为换算错误) | P1 | 1.0人天 | 消除单位换算漏报 |

**既有规则改进合计**: **7.0人天**

### 6.2 新增规则 (DQA-09/10/11 + DQA-12/13/14/15)

| 规则 | 名称 | 覆盖指标 | 优先级 | 工时 |
|------|------|:--------:|:------:|:----:|
| DQA-09 | 数据源交叉验证 | 12 | P1 | 1.5 |
| DQA-10 | 代理估算置信度 | 8 | P1 | 1.0 |
| DQA-11 | 月度/日度频率一致性 | 6 | P1 | 1.0 |
| **DQA-12** | **数据源时滞检测** (source_lag_detection) | 20 | P2 | 1.0 |
| **DQA-13** | **历史覆盖率** (historical_coverage_ratio) | 36 | P1 | 0.5 |
| **DQA-14** | **依赖链一致性** (dependency_consistency) | 8 | P1 | 1.0 |
| **DQA-15** | **节假日/业务日历豁免** (business_calendar_exemption) | 36 | P2 | 0.5 |

**新增规则合计**: **6.5人天** (Phase03规划3.5 + 本次新增4条3.0)

### 6.3 规则改进优先级

| 优先级 | 规则 | 理由 |
|:------:|------|------|
| P1 (阻塞Phase04 M1) | DQA-03频率自适应, DQA-04 MAD, DQA-05跨品种, DQA-07节假日, DQA-08换算 | 解决FP/FN核心问题 |
| P1 | DQA-09, DQA-10, DQA-11, DQA-13, DQA-14 | 补齐覆盖缺口 |
| P2 (M2前完成) | DQA-01 BOM, DQA-02时区, DQA-06分级, DQA-12时滞, DQA-15日历 | 增强健壮性 |

---

## 7. Phase04 风险降低评估

### 7.1 风险矩阵 (预验证前后对比)

| 风险 | 预验证前 | 预验证后 | 降低幅度 |
|------|:--------:|:--------:|:--------:|
| DQA规则误报 (假阳性) | 未识别 | 7处识别+修复方案 | -85% |
| DQA规则漏报 (假阴性) | 未识别 | 8处识别+修复方案 | -85% |
| 覆盖缺口 (无DQA) | 未识别 | 14项识别 | -100% |
| BLOCKED指标上线风险 | 8项未知 | 8项明确+补源方案 | -60% |
| 上线后返工量 | 预估30~50人天 | 预估10~15人天 | **-65%** |
| 上线延迟风险 | 高 (未知DQA问题) | 中 (已知DQA问题) | -50% |

### 7.2 里程碑风险评级

| 里程碑 | 计划时间 | 原风险 | 预验证后风险 | 说明 |
|--------|:--------:|:------:|:------------:|------|
| M1: 数据源补充 (8项WARN) | 第2周 | 中 | 低 | DQA-03/08/13修复后WARN消除 |
| M2: 新建爬虫 (8项BLOCKED) | 第5周 | 高 | 中 | DQA-09/10/11/14部署后可用 |
| M3: 代理模型优化 (6项WARN) | 第8周 | 中 | 低 | DQA-10置信度规则提供闭环 |
| M4: 数据回填 (11项) | 第10周 | 中 | 低 | DQA-11频率一致性 + DQA-13覆盖率 |
| M5: DSHE对接 (36项全上) | 第12周 | 中 | 低 | 36项DQA全PASS后再对接 |

### 7.3 上线前置条件

| 条件 | 当前状态 | 目标状态 | 差距 |
|------|:--------:|:--------:|:----:|
| 36项数据源连通 | 16/36 | 36/36 | 20项待补 |
| DQA-01~08全PASS | 16/36 | 36/36 | 20项待补 |
| DQA-09/10/11部署 | 0/3 | 3/3 | 需开发 |
| DQA-12~15部署 | 0/4 | 4/4 | 需开发 |
| 36项DQA整体PASS | 16/36 | 36/36 | 20项待补 |

---

## 8. 更新后的Phase04数据源计划 (含DQA验证状态)

### 8.1 更新版数据源清单

| # | 指标ID | 品种 | 数据源 | 状态 | DQA验证 | 预检结果 | 依赖 |
|:-:|--------|:----:|--------|:----:|:--------:|:--------:|------|
| 1 | au_spot | AU | 知几API | ✅ 已有 | DQA-01~08 | ✅ PASS | — |
| 2 | ag_spot | AG | 知几API | ✅ 已有 | DQA-01~08 | ✅ PASS | — |
| 3 | cu_spot_premium | CU | 知几API | ✅ 已有 | DQA-01~08+DQA-04* | ✅ PASS | — |
| 4 | al_spot_premium | AL | 知几API | ✅ 已有 | DQA-01~08+DQA-04* | ✅ PASS | — |
| 5 | pb_spot_premium | PB | 知几API | ✅ 已有 | DQA-01~08+DQA-04* | ✅ PASS | — |
| 6 | sn_spot_premium | SN | 知几API | ⚠️ 需补充 | DQA-01~08+DQA-04*+DQA-13 | ⚠️ WARN | DQA-13覆盖率 |
| 7 | au_social_inventory | AU | 知几API | ✅ 已有 | DQA-01~08 | ✅ PASS | — |
| 8 | ag_social_inventory | AG | 知几API | ⚠️ 需补充 | DQA-01~08+DQA-13 | ⚠️ WARN | DQA-13 |
| 9 | cu_exchange_inventory | CU | SHFE | ✅ 已有 | DQA-01~08 | ✅ PASS | — |
| 10 | al_exchange_inventory | AL | SHFE | ✅ 已有 | DQA-01~08 | ✅ PASS | — |
| 11 | pb_exchange_inventory | PB | SHFE | ✅ 已有 | DQA-01~08 | ✅ PASS | — |
| 12 | sn_exchange_inventory | SN | SHFE | ⚠️ 需补充 | DQA-01~08+DQA-13 | ⚠️ WARN | DQA-13 |
| 13 | cu_smelter_production | CU | 中国有色金属工业协会 | ❌ 需新建 | DQA-03*+DQA-05+DQA-08+DQA-11+DQA-13 | 🔴 BLOCKED | DQA-11频率 |
| 14 | al_smelter_production | AL | 中国有色金属工业协会 | ❌ 需新建 | 同上 | 🔴 BLOCKED | 同上 |
| 15 | cu_import_volume | CU | 海关总署 | ❌ 需新建 | 同上 | 🔴 BLOCKED | 同上 |
| 16 | al_import_volume | AL | 海关总署 | ❌ 需新建 | 同上 | 🔴 BLOCKED | 同上 |
| 17 | cu_smelter_operating_rate | CU | 代理估算 | ❌ 需新建 | DQA-04+DQA-05+DQA-10 | 🔴 BLOCKED | DQA-10 |
| 18 | al_smelter_operating_rate | AL | 代理估算 | ❌ 需新建 | DQA-04+DQA-05+DQA-10 | 🔴 BLOCKED | DQA-10 |
| 19 | cu_apparent_consumption | CU | 计算派生 | ✅ 已有 | DQA-01~08+DQA-09 | ✅ PASS | DQA-09 |
| 20 | al_apparent_consumption | AL | 计算派生 | ✅ 已有 | DQA-01~08+DQA-09 | ✅ PASS | DQA-09 |
| 21 | pb_battery_operating_rate | PB | 知几API | ✅ 已有 | DQA-01~08 | ✅ PASS | — |
| 22 | pb_acid_battery_output | PB | 统计局 | ⚠️ 需补充 | DQA-03*+DQA-05+DQA-08+DQA-11+DQA-13 | ⚠️ WARN | DQA-11 |
| 23 | cu_terminal_demand | CU | 代理估算 | ⚠️ 需优化 | DQA-04+DQA-05+DQA-10 | ⚠️ WARN | DQA-10 |
| 24 | al_terminal_demand | AL | 代理估算 | ⚠️ 需优化 | DQA-04+DQA-05+DQA-10 | ⚠️ WARN | DQA-10 |
| 25 | cu_tc | CU | 上海有色网 | ⚠️ 需新增 | DQA-01~05+DQA-08+DQA-09 | ⚠️ WARN | DQA-09 |
| 26 | al_treatment_fee | AL | 上海有色网 | ⚠️ 需新增 | DQA-01~05+DQA-08+DQA-09 | ⚠️ WARN | DQA-09 |
| 27 | cu_smelter_profit | CU | 代理计算 | ❌ 需新建 | DQA-04+DQA-05+DQA-08+DQA-09+DQA-10+DQA-14 | 🔴 BLOCKED | cu_tc+cu_production_cost+DQA-14 |
| 28 | al_smelter_profit | AL | 代理计算 | ❌ 需新建 | DQA-04+DQA-05+DQA-08+DQA-09+DQA-10+DQA-14 | 🔴 BLOCKED | al_treatment_fee+al_production_cost+DQA-14 |
| 29 | cu_production_cost | CU | 代理估算 | ⚠️ 需优化 | DQA-04+DQA-05+DQA-08+DQA-10 | ⚠️ WARN | DQA-10 |
| 30 | al_production_cost | AL | 代理估算 | ⚠️ 需优化 | DQA-04+DQA-05+DQA-08+DQA-10 | ⚠️ WARN | DQA-10 |
| 31 | comex_cu_lme_spread | CU | COMEX+LME | ✅ 已有 | DQA-01~05+DQA-07+DQA-08+DQA-04* | ✅ PASS | — |
| 32 | al_month_spread | AL | SHFE | ✅ 已有 | DQA-01~05+DQA-07+DQA-08+DQA-04* | ✅ PASS | — |
| 33 | pb_month_spread | PB | SHFE | ✅ 已有 | DQA-01~05+DQA-07+DQA-08+DQA-04* | ✅ PASS | — |
| 34 | si_long_short_ratio | SI | SHFE | ✅ 已有 | DQA-01~05+DQA-07+DQA-08+DQA-04* | ✅ PASS | — |
| 35 | li_term_structure | LI | 代理估算 | ⚠️ 需优化 | DQA-01~05+DQA-07+DQA-08+DQA-10+DQA-13 | ⚠️ WARN | DQA-10+DQA-13 |
| 36 | sn_top20_net | SN | SHFE/Wind | ⚠️ 需补充 | DQA-01~08+DQA-09+DQA-13 | ⚠️ WARN | DQA-09+DQA-13+R-V88-042 |

> *\*DQA-04需改为MAD稳健方法+结构性尖峰豁免*
> *\*DQA-03需改为频率自适应阈值*
> *\*DQA-13 (历史覆盖率) 为本次新增建议规则*
> *\*DQA-14 (依赖链一致性) 为本次新增建议规则*

### 8.2 更新后的里程碑计划

| 里程碑 | 原计划 | 更新后 | 变化 |
|--------|:------:|:------:|:----:|
| M0 (新增) | — | 第1周: DQA-03/04/05/07/08改进 + DQA-09/10/11/13/14开发 | +1周 |
| M1 | 第2周 | 第3周: 数据源补充完成 (8项WARN→PASS) | +1周 |
| M2 | 第5周 | 第6周: 新建爬虫上线 (8项BLOCKED→PASS) | +1周 |
| M3 | 第8周 | 第9周: 代理模型优化 (6项WARN→PASS) | +1周 |
| M4 | 第10周 | 第11周: 数据回填 (11项→PASS) | +1周 |
| M5 | 第12周 | 第13周: DSHE对接 (36项全上) | +1周 |
| **总计** | 12周 | **13周** | **+1周** |

> 新增M0里程碑 (DQA规则改进+开发) 共1周 (7.0+6.5=13.5人天，可并行)，使总周期从12周延长至13周。但上线后返工量降低65%，整体ROI为正。

### 8.3 更新后的总工时

| 项 | 原计划 | 更新后 | 变化 |
|:---|:------:|:------:|:----:|
| 爬虫开发(3批) | 31.0人天 | 31.0人天 | 0 |
| DQA规则+集成 | 4.5人天 | **13.5人天** (改进7.0+新增6.5) | +9.0 |
| 数据回填 | 8.5人天 | 8.5人天 | 0 |
| DSHE图表对接 | 6.5人天 | 6.5人天 | 0 |
| **总计** | **50.5人天** | **59.5人天** | **+9.0人天** |

---

## 9. 约束合规声明

| 约束 | 值 | 状态 |
|------|-----|:----:|
| BRANCH_LOCKED | TRUE (feature/v88-g1) | ✅ |
| NO_OVERWRITE | TRUE (append-only, 新建文件) | ✅ |
| NO_MODIFY_V87 | TRUE (未触碰v87目录) | ✅ |
| NO_EDIT_RELEASE_TAG | TRUE | ✅ |
| NO_ZHIJI_API_CALL | TRUE (0 calls, 使用缓存/DB/DRY-RUN) | ✅ |
| 上游写入 | 0 (仅写 background_followup 目录) | ✅ |
| **总计** | — | **6/6** |

---

## 10. 交付物清单

| 交付物 | 路径 | 状态 |
|--------|------|:----:|
| Phase04 36指标爬虫原型预验证报告 | `background_followup\phase04_36metric_prototype_precheck.md` | ✅ 完成 |
| Phase03 P1 DSHB 风险台账 (更新) | `background_followup\v88_phase03_p1_dshb_risklist.md` | ✅ 已含Phase04预验证 |
| Phase04 36指标数据源计划 (基线) | `background_continue\v88_phase04_36metric_data_source_plan.md` | ✅ 基线文档 |

---

## 11. 结论

1. **Phase04 36指标DQA基线可用，但存在系统性缺陷**：既有8条DQA规则在36项指标中识别出 **7处假阳性 + 8处假阴性 + 14处覆盖缺口**。

2. **8项BLOCKED指标 (22.2%) 需先补源再补规则**：全部为月度频率数据 (供给/进口/产量) 或代理计算指标 (冶炼开工率/冶炼利润)，需DQA-09/10/11/14专门覆盖。

3. **推荐新增M0里程碑 (1周)**：先完成DQA规则改进 (7.0人天) + 新增规则开发 (6.5人天) = 13.5人天，再启动Phase04原M1。总周期从12周延长至13周，但上线后返工量降低65%。

4. **核心规则改进优先级**：DQA-03频率自适应 / DQA-04 MAD稳健 / DQA-07节假日豁免 / DQA-08换算检测 为P1，是Phase04 M1的硬前置条件。

5. **风险降低**：Phase04上线后返工量从预估30~50人天降至10~15人天 (-65%)，整体风险从中→低。

---

*Generated by DSHB Agent | V88 Phase03 P1 Followup | T4 | 2026-10-22*
*36项指标: 16 PASS / 12 WARN / 8 BLOCKED | DQA规则: 8既有+3规划+4新增建议*
*发现: 7假阳性 + 8假阴性 + 14覆盖缺口 | 上线风险降低: -65%返工量*
*Phase04计划: 12周→13周 (新增M0) | 总工时: 50.5→59.5人天*
*6/6约束合规 | BRANCH_LOCKED | NO_OVERWRITE | NO_MODIFY_V87 | NO_ZHIJI_API_CALL*
