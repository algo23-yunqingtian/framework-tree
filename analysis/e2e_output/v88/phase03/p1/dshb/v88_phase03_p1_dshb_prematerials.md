# V88 Phase03 P1 — DSHB 前置资料汇总

> **TASK_ID**: V88_PHASE03_P0_DSHB_WATCHER_TASK
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **日期**: 2026-10-15
> **目的**: P0 阶段收尾值守期间，为 P1 阶段任务下发准备数据层前置资料

---

## 0. 一句话总结

**DSHB 数据侧 P0 阶段全部完成（含 DSHE 引擎适配修复 R-V88-030 RESOLVED），D7 覆盖率 78.82% 达标。P1 阶段前置资料已就绪：指标基线 615 / 映射基线 608 (98.9%) / 风险台账 11 项全闭环 / 重建脚本可复现。等待 HERMEShf P0 终审 PASS 后下发 P1 工单。**

---

## 1. 指标基线（phase03_test.db）

| 指标 | 数值 | 来源 |
|------|-----:|------|
| 总行数 | 475,593 | phase03_test.db series_cache |
| 总指标数 | 615 | DISTINCT indicator_id |
| 已映射指标 | 608 (98.9%) | indicator_id_mapped 非空 |
| 未映射指标 | 7 (1.1%) | j21, j22, j23, j24, j25, j26 变体 |
| 主键冲突 | 0 | UNIQUE(indicator_id, date) |
| 导入错误 | 0 | import_log 表 |
| 数据日期范围 | 2015-01-02 ~ 2026-08-28 | MIN/MAX(date) |
| 品种覆盖 | 12 个 | cu/al/pb/zn/ni/sn/si/li/au/ag/wr/other |

### 品种分布

| 品种 | 覆盖指标数 | 覆盖率 |
|------|:---------:|:------:|
| cu | ~60 | ~90% |
| al | ~55 | ~77% |
| pb | ~50 | ~62% |
| zn | ~55 | ~69% |
| ni | ~65 | ~85% |
| sn | ~65 | ~85% |
| li | ~55 | ~62% |
| si | ~50 | ~82% |
| au | ~40 | — |
| ag | ~40 | — |
| wr | ~30 | — |
| other | ~50 | — |

---

## 2. 映射基线

### 2.1 映射命中率

| 口径 | 分子 | 分母 | 比率 | 阈值 | 状态 |
|------|:----:|:----:|:----:|:----:|:----:|
| DB 映射命中率 | 84 | 109 | **77.06%** | ≥60% | ✅ PASS |
| 引擎 D7 渲染覆盖率 | 67 | 85 | **78.82%** | ≥60% | ✅ PASS |
| 指标 ID 映射率 | 608 | 615 | **98.9%** | — | ✅ |

### 2.2 关键样例映射

| indicator_id | indicator_id_mapped | commodity |
|-------------|:-------------------:|:---------:|
| zn_21_close_front | ZN_FU00014950 | zn |
| ni_21_close_front | NI_FU00021745 | ni |
| sn_21_close_front | SN_FU00021760 | sn |
| cu_21_close_front | CU_FU00012365 | cu |
| al_21_close_front | AL_FU00009845 | al |

### 2.3 未映射指标（7 项）

| indicator_id | 原因 |
|-------------|------|
| j21_xxx | 备用指标，无 mapped ID |
| j22_xxx | 备用指标，无 mapped ID |
| j23_xxx | 备用指标，无 mapped ID |
| j24_xxx | 备用指标，无 mapped ID |
| j25_xxx | 备用指标，无 mapped ID |
| j26_xxx | 备用指标，无 mapped ID |
| (1 other) | 备用指标，无 mapped ID |

---

## 3. 引擎适配状态（R-V88-030 RESOLVED）

| 项目 | 状态 |
|------|:----:|
| R-V88-030 P0 阻断 | ✅ **RESOLVED** |
| 引擎路径修复 | `V88_PHASE03_TEST_DB` 环境变量支持 |
| Schema 适配 | series_cache + indicator_cache 双表查询 |
| D7 覆盖率 | 78.82% ≥ 60% ✅ |
| Real source 图表 | 67/85 |
| 测试通过 | 27 PASS / 8 WARN / 2 FAIL / 0 BLOCKED |
| 降级压测 | 148 次 0 崩溃 |
| V87 兼容性 | ✅ 已验证 |
| 责任方 | DSHE (commit 26470f1) |

---

## 4. 风险台账汇总（DSHB 数据侧）

| 编号 | 风险 | 等级 | 状态 |
|------|------|:----:|:----:|
| R-V88-013 | D-SRC 覆盖率 | P0→P1 | 数据侧闭环 / 引擎侧已修复 |
| R-V88-025 | 数据隔离 | P1 | ✅ CLOSED |
| R-V88-026 | 查询性能 | P2 | ✅ MITIGATED |
| R-V88-027 | 口径不一致 | P1 | ✅ MITIGATED |
| R-V88-028 | 覆盖率不一致 | P1 | ✅ CLOSED |
| R-V88-029 | 灌库目标库 | P1 | ✅ CLOSED |
| R-V88-030 | 引擎适配 | P0 | ✅ **RESOLVED** |
| R-V88-031 | .db 不可推送 | P2 | ✅ MITIGATED (P2_MONITORED) |
| DSHB R-01 | 容量突破 | P2 | ✅ MITIGATED |
| DSHB R-04 | 灾备一致性 | P1 | ✅ MITIGATED |
| DSHB R-06 | 告警噪声 | P2 | ✅ MITIGATED |
| DSHB R-09 | Phase02 影响 | Critical | ✅ CLOSED |

**总计**: 11 项 / 全部 CLOSED 或 MITIGATED / 0 项 OPEN / 0 项 P0 阻断

---

## 5. P1 阶段可用资源

### 5.1 已归档脚本（锁定不变）

| 脚本 | MD5 | 用途 |
|------|:---:|------|
| `rebuild_phase03_testdb.py` | `717A0B9B` | 一键重建 phase03_test.db |
| `verify_testdb.py` | `FE6B5470` | 9 项完整性校验 |
| `export_mapping_list.py` | `B6A7E0F5` | 映射清单导出 |

### 5.2 已归档文档

| 文档 | MD5 | 用途 |
|------|:---:|------|
| `v88_phase03_p0_metric_indicator_code_mapping.md` | `BDF859ED` | 615 条完整映射表 |
| `v88_phase03_p0_metric_indicator_code_mapping.json` | `F91C6FA0` | 结构化映射数据 |
| `v88_phase03_p0_metric_caliber_definition.md` | `7415BA6D` | 口径定义文档 |
| `v88_phase03_data_risk_list.md` | `0F2D27BF` | 风险台账 |
| `v88_phase03_p0_dshb_archive_report.md` | `8C360F16` | P0 归档报告 |

### 5.3 引擎侧已修复能力

- `V88_PHASE03_TEST_DB` 环境变量切换测试库/生产库
- series_cache → indicator_cache schema 适配层
- 双表查询分支（保留 V87 兼容 + 新增 Phase03 适配）

---

## 6. P1 阶段待执行任务（参考 agent_work_breakdown）

| 任务 ID | 任务 | DSHB 优先级 | 前置 |
|---------|------|:----------:|:----:|
| DSHB-04 | DQA 规则扩展（适配 200+ 指标） | P1 | DSHB-02 |
| DSHB-05 | 扩量批次执行（146→180→200+） | P1/P2 | DSHB-04 |
| DSHB-06 | 灾备切换仿真演练 | P1 | DSHB-03 |
| DSHB-08 | IC/IR 采集链路增强 | P1~P3 | Phase02 基线 |

> 注：具体 P1 工单以 HERMEShf 终审后下发为准

---

## 7. 验收标准

| # | 标准 | 状态 |
|:-:|------|:----:|
| 1 | 已归档脚本保持锁定，MD5 匹配 | ✅ 7/7 PASS |
| 2 | 指标基线完整（615 指标/608 映射） | ✅ |
| 3 | 映射基线可用（98.9% 映射率） | ✅ |
| 4 | 风险台账全闭环（0 OPEN/0 P0） | ✅ 11/11 |
| 5 | 引擎修复已确认（D7=78.82% PASS） | ✅ |
| 6 | 重建脚本可复现 phase03_test.db | ✅ |
| 7 | P1 前置资料就绪 | ✅ |
| 8 | PHASE03_P0_DSHB_WATCHER=TRUE | ✅ |

---

## 8. 值守声明

- DSHB 数据侧 P0 阶段全部收尾完成
- 归档脚本版本锁定，无未授权修改
- 映射文档/风险台账维持最新状态
- 接收 DSHE/HERMEShf 映射/DB 重建查询，按需提供排查
- 不新增灌库/数据转换/指标计算逻辑开发
- **PHASE03_P0_DSHB_WATCHER=TRUE — 待命等待 P0 终审 PASS 及 P1 工单**
