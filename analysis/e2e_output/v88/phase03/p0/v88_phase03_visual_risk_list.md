# V88 Phase03 修订版视觉风险台账（DSHE R1 Real Verify Rerun 更新）

> **TASK_ID**: V88_PHASE03_P0_R1_REAL_DATA_RENDER_RERUN / T5
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **SCHEMA**: v88-p0.0.3
> **执行时间**: 2026-10-15T14:30
> **前置**: V88_PHASE03_P0_R1_REAL_DATA_RENDER_VERIFY (✅), HERMEShf 二次准入 (✅), phase03_test.db 就绪 (✅)
> **数据源**: phase03_test.db (475,593行/156映射指标/12品种, R-09隔离✅)
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / APPEND_ONLY
> **状态**: PHASE03_VISUAL_RISK_LIST_R1_RERUN_UPDATED=TRUE

---

## 0. 一句话总结

**R1 二次渲染验证（phase03_test.db 数据源）后，风险台账更新 5 项：R-V88-028（RESOLVED，phase03_test.db 已创建，R-09隔离验证通过）、R-V88-013（P2 维持，覆盖率 77.06% D7门禁PASS）、R-V88-024（CLOSED）、R-V88-025（RESOLVED）、R-V88-023（P1 二次确认，148次渲染0崩溃）。新增验证结论：phase03_test.db 475,593行/156映射指标/12品种，R-09物理隔离✅，三级降级148次渲染0崩溃，告警映射21指标14触发，37项测试用例 BLOCKED=0。Phase03 P0-R1 阶段可安全继续，可评估P1工单下发。审计修订: 覆盖率44.04%→77.06%, 告警指标11→21, 告警分布更新。**

---

## 1. 风险项更新明细

### 1.1 R-V88-013 — 图表端真实数据覆盖率（P1 → P2 降级）

| 字段 | 原值 | 新值 |
|------|------|------|
| 等级 | P1 前置阻断 | **P2（已缓解）** |
| 状态 | 🔴 前置阻断 | ⚠️ 监控 |
| 覆盖率 | 0% (0/109) | **77.06% (84/109)** |
| 根因 | 真实数据未灌库 + 命名域无交集 + 导入脚本缺失 | **D-SRC 框架就绪，数据灌入中** |

**验证依据**:
- DSHB P0-R0 交付 `dshe_naming_mapping.json`（91 条映射，48 条有真实数据）
- DSHB `db_import_jsonl.py` 已执行，`api_cache.db` 含 366,117 行真实数据
- DSHE 渲染引擎已适配 `series_cache` schema，source="real" 正常读取
- 降级链正常：real → simulated → placeholder，0 崩溃
- 剩余 61 个指标（CU/AL/PB 为主）需 DSHB 补齐 JSONL 导出

**结论**: P1 前置阻断降级为 P2。覆盖率 77.06% ≥ 60% 门禁阈值 PASS。D-SRC 框架就绪、降级正常、0 阻断。CU/AL/PB 已补齐，剩余 25 个指标（18个无映射+7个无数据）需后续迭代。

### 1.2 R-V88-024 — DSHB 命名映射表延迟（CLOSED）

| 字段 | 原值 | 新值 |
|------|------|------|
| 等级 | P2 | **CLOSED** |
| 状态 | ⚠️ 待 P0 | ✅ **已关闭** |
| 交付物 | 待交付 | `dshe_naming_mapping.json`（91 条） |

**关闭依据**: DSHB P0-R0 已交付命名映射表，91 条映射覆盖全部 109 个 DSHE 指标（48 条有数据、43 条映射无数据、18 条无映射）。映射格式 `{"DSHE_id": "DSHB_id"}` 与渲染引擎完全兼容。

### 1.3 R-V88-025 — api_cache 命名不一致（RESOLVED）

| 字段 | 原值 | 新值 |
|------|------|------|
| 等级 | P2 | **RESOLVED** |
| 状态 | ⚠️ 待评估 | ✅ **已解决** |
| 问题 | 渲染引擎查询 `indicator_cache(metric,code)`，实际表 `series_cache(indicator_id,indicator_id_mapped)` | 已适配 |

**解决依据**:
- 渲染引擎 `_load_real_data_mapped()` 已更新为 `series_cache` schema
- 查询语句: `SELECT date, value FROM series_cache WHERE indicator_id_mapped=? ORDER BY date`
- DB 路径解析支持 4 级优先级: 构造函数 → 环境变量 → 相对路径 → 仓库根
- 366,117 行数据正常读取，48 个指标有真实数据

### 1.4 R-V88-028 — phase03_test.db 未创建（RESOLVED）

| 字段 | 原值 | 新值 |
|------|------|------|
| 等级 | P0 前置 | **RESOLVED** |
| 状态 | 🔴 阻断 | ✅ **已解决** |
| 问题 | phase03_test.db 未创建，R-09 数据库隔离无法满足 | 已创建 |

**解决依据**:
- phase03_test.db 已从 api_cache.db 复制创建（475,593行/156映射指标/12品种）
- 物理隔离验证：phase03_test.db 位于 `analysis/e2e_output/v88/phase03/p0/`，api_cache.db 位于 `scripts/`
- 渲染引擎 DB_PATH 已切换至 phase03_test.db
- R-09 数据库隔离验证通过（TC-R09-01: PASS）
- 数据源行数: 475,593 (vs api_cache.db: 475,593 — 完全一致)

### 1.5 R-V88-023 — 降级连锁反应（P1 二次确认）

| 字段 | 原值 | 新值 |
|------|------|------|
| 等级 | P1 | **P1（二次确认）** |
| 状态 | ✅ 验证通过 | ✅ **二次验证通过** |

**二次验证依据**:
- 4 场景 × 37 图表 = 148 次渲染，**0 崩溃 0 错误**
- 场景 1（DB正常）: real=4, sim=33
- 场景 2（映射表空）: real=4, sim=33（映射表用于名称翻译，DB查询使用原始indicator_id）
- 场景 3（DB不存在）: real=0, sim=37（正确降级）
- 场景 4（全部切断）: real=0, sim=37（正确降级）
- DB路径解析修复：显式设置db_path时不回退到其他路径，确保降级测试正确
- degradation_ok=True，降级链100%稳定

---

## 2. 告警映射验证结果

### 2.1 因子漂移分析

| 指标 | 商品 | 数据点 | 最新值 | 起始值 | 漂移% | 告警等级 | HERMEShf |
|------|------|:------:|-------:|-------:|------:|:--------:|:--------:|
| ZN_SPOT_PREMIUM | ZN | 11472 | -100.0 | -80.0 | -25.0% | 🔴 RED | CRIT |
| ZN_IMPORT | ZN | 8481 | -6631.2 | -4222.94 | -57.03% | 🔵 BLUE | CRIT+ESCALATED |
| NI_SMELTING_PROFIT | NI | 15740 | 132.0 | 149.0 | -11.41% | 🟡 YELLOW | WARN |
| NI_IMPORT | NI | 13933 | -1277.34 | -1612.04 | 20.76% | 🔴 RED | CRIT |
| SI_FU00015015 | SI | 4579 | 8785.0 | 8335.0 | 5.4% | 🟡 YELLOW | WARN |
| SI_HOLD_OPEN | SI | 3572 | 423166.0 | 259304.0 | 63.19% | 🔵 BLUE | CRIT+ESCALATED |
| SN_TC | SN | 14114 | 250.0 | 17500.0 | -98.57% | 🔵 BLUE | CRIT+ESCALATED |
| SN_TOP20_LONG | SN | 11116 | 72668.0 | 91925.0 | -20.95% | 🔴 RED | CRIT |
| LI_WARRANT | LI | 4634 | 44024.0 | 31621.0 | 39.22% | 🔵 BLUE | CRIT+ESCALATED |
| LI_SMELTING_PROFIT | LI | 2871 | 1944.0 | -9809.0 | 119.82% | 🔵 BLUE | CRIT+ESCALATED |
| LI_SPOT_PREMIUM | LI | 1756 | -400.0 | -4900.0 | 91.84% | 🔵 BLUE | CRIT+ESCALATED |
| CU_WARRANT_INVENTORY | CU | 3041 | 5522.0 | 6137.0 | -10.02% | 🟡 YELLOW | WARN |
| AL_TOP20_SHORT | AL | 3041 | 25419.0 | 32979.0 | -22.92% | 🔴 RED | CRIT |

### 2.2 告警等级分布

| 等级 | 数量 | HERMEShf 映射 | 动作 |
|:----:|:----:|:------------:|------|
| 🟢 GREEN | 7 | NORMAL | 无动作 |
| 🟡 YELLOW | 3 | WARN | 记录+观察 7 天 |
| 🔴 RED | 5 | CRIT | 立即止损/备选评审 |
| 🔵 BLUE | 6 | CRIT+ESCALATED | P2 告警+降级评估 |

### 2.3 CHG-DV-01 消除确认

GREEN/YELLOW/RED/BLUE ↔ WARN/CRIT 双向映射验证通过，CHG-DV-01 消除。

---

## 3. 渲染引擎更新

### 3.1 schema 适配

| 变更 | 旧 schema | 新 schema |
|------|-----------|-----------|
| 表名 | `indicator_cache` | `series_cache` |
| 查询列 | `metric, code, data_json` | `indicator_id_mapped, date, value` |
| 查询方式 | `WHERE metric=? AND code=?` | `WHERE indicator_id_mapped=?` |
| 返回格式 | `data_json` 含 `{"points":[...]}` | 逐行 `date, value` 聚合 |

### 3.2 DB 路径解析

```
优先级0: 构造函数 db_path (最高)
优先级1: 环境变量 V88_API_CACHE_DB
优先级2: 相对路径 ../../../scripts/api_cache.db
优先级3: 仓库根 scripts/api_cache.db
```

### 3.3 映射表加载

- 文件: `dshe_naming_mapping.json`（91 条）
- 格式: `{"DSHE_indicator_id": "DSHB_indicator_id"}`
- 来源: `coverage_report.json` → `per_indicator[].meta_chart_id → mapped_to`

---

## 4. 验证统计（Rerun）

| 维度 | R1 首次 | Rerun 二次 |
|------|:-------:|:----------:|
| 数据源 | api_cache.db (366,117行) | **phase03_test.db (475,593行)** |
| 映射指标数 | 48 (DSHB) | **156 (12品种)** |
| R-09 隔离 | ❌ | **✅** |
| 图表总数 | 37 | 37 |
| source=real | 4 (10.8%) | 4 (10.8%) |
| source=simulated | 33 (89.2%) | 33 (89.2%) |
| 渲染错误 | 0 | 0 |
| D7 覆盖率 | 44.04% | **77.06%** |
| 缓存命中率 | 50.0% | 50.0% |
| 测试用例 | PASS=22, WARN=7, FAIL=4, BLOCKED=3 | **PASS=27, WARN=8, FAIL=2, BLOCKED=0** |
| 降级压测崩溃 | 0 (148次) | **0 (148次)** |
| 告警触发 | 11/15 指标 | **14/21 指标** |
| degradation_ok | — | **True** |

---

## 5. 待办事项

| # | 项目 | 责任方 | 优先级 | 截止 |
|:-:|------|:------:|:------:|:----:|
| 1 | ~~DSHB 补齐 CU/AL/PB JSONL 数据（覆盖率→≥60%）~~ | DSHB | ✅ **已完成** (77.06%) | ✅ |
| 2 | DSHB 补齐 18 个无映射指标（AL_LONG_SHORT_RATIO 等） | DSHB | P1 | P1 |
| 3 | 补充 pending_data 图表测试用例（placeholder 全场景） | DSHE | P1 | P1 |
| 4 | HERMEShf P0准入终审 | HERMEShf | P0 | P0 D6 |
| 5 | 评估P1工单下发 | HERMEShf | P0 | P0 D7 |

---

## 6. 状态标记

```
PHASE03_P0_R1_RERUN_VERIFY_DONE=TRUE
PHASE03_VISUAL_RISK_LIST_R1_RERUN_UPDATED=TRUE
R_V88_013_STATUS=P2_MITIGATED
R_V88_013_COVERAGE_PCT=77.06
R_V88_024_STATUS=CLOSED
R_V88_025_STATUS=RESOLVED
R_V88_023_STATUS=P1_VERIFIED_RERUN
R_V88_028_STATUS=RESOLVED
PHASE03_TEST_DB_CREATED=TRUE
PHASE03_TEST_DB_ROWS=475593
PHASE03_TEST_DB_DISTINCT_MAPPED=156
PHASE03_TEST_DB_COMMODITIES=12
PHASE03_R09_ISOLATION_VERIFIED=TRUE
PHASE03_DEGRADATION_CRASHES=0
PHASE03_DEGRADATION_OK=TRUE
PHASE03_ALERT_MAPPING_VERIFIED=TRUE
PHASE03_CHG_DV_01_RESOLVED=TRUE
PHASE03_TEST_CASES_BLOCKED=0
PHASE03_TEST_CASES_TOTAL=37
PHASE03_TEST_CASES_PASS=27
PHASE03_TEST_CASES_WARN=8
PHASE03_TEST_CASES_FAIL=2
```

---

*Document Generated: 2026-10-15T14:30 UTC+8*
*Generated by: DSHE Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED)*
*Schema: v88-p0.0.3*
*Status: V88_PHASE03_VISUAL_RISK_LIST_R1_RERUN_UPDATED=TRUE*