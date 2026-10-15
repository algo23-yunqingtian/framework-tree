# V88 Phase02 渲染链路抽样回放验证报告（S-01~S-20）

> **TASK_ID**: V88_PHASE02_HERMESHF_FINAL_REPORT_AMEND_AND_SAMPLE_VERIFY
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 | **BASELINE HEAD**: 1a1fcd4
> **生成时间**: 2026-10-15
> **验证方法**: HERMEShf 调用 `NodeBindingEngine.render_with_fallback()` **真实执行** DSHE 预定义 S-01~S-20 抽样矩阵，采集 `source` / `render_time_ms` / `placeholder` / `render_data_points`，与 DSHE 上报口径交叉比对
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY
> **状态**: **SAMPILE_VERIFY_COMPLETE（发现 1 项 P1 阻断级差异）**

---

## 0. 一句话结论

**20/20 张抽样图表渲染链路可回放、时延全部达标（max 4.63ms，余量 99.1%）、0 崩溃、0 placeholder——渲染引擎机制层面 PASS。** 但交叉比对发现 **1 项 P1 阻断级差异（D-SRC）**：全量 101 张图表 100% 返回 `source="simulated"`，DSHB 推送日志声称的 `real=980` 无真实数据落地支撑；根因为 `api_cache.db` 仅含 3 行 `code='AO'` 数据，与 109 个图表指标**零交集**。该项须纳入 Phase02 遗留风险与 Phase03-P0 优先项，**不可在总报告中记为已验收**（详见 §5）。

---

## 1. 抽样矩阵与执行结果

### 1.1 抽样设计

| 维度 | 设计 | 实际覆盖 |
|---|---|---|
| 品种 | 8 品种（cu/al/pb/zn/ni/sn/li/si） | **8/8** ✅ |
| 节点 | 12 节点（按可用性降级匹配） | **3/3**（p1/p3/p4）⚠️ |
| 数据状态 | matchable + pending_data 双路径 | **11 matchable + 9 pending_data** |
| 图表 | 20 张独立抽样 | **20/20 执行成功** |

> **节点覆盖说明**：抽样按「品种+节点+数据状态」优先匹配，无匹配时按品种降级、再按节点降级。实际图表库节点集中于 p1/p3/p4，12 节点全覆盖在 Phase02 已验收的引擎级门禁 `test_05_node_coverage_12` 中验证；本次抽样侧重品种×数据源交叉，非节点全覆盖。

### 1.2 20 项逐条结果

| Case | 图表ID | 标题 | 品种 | 节点 | 数据状态 | source | placeholder | 数据点 | 时延中位(ms) | 时延最大(ms) | <500ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S-01 | `cu_p1_ts_01` | 铜 盘面结构 主连结算价 | cu | p1 | matchable | `simulated` | False | 1 | 1.76 | 4.63 | ✅ |
| S-02 | `cu_p4_ts_02` | 铜 价差体系 期限结构 | cu | p4 | pending_data | `simulated` | False | 1 | 1.61 | 1.66 | ✅ |
| S-03 | `cu_p4_ts_02` | 铜 价差体系 期限结构 | cu | p4 | pending_data | `simulated` | False | 1 | 1.6 | 1.64 | ✅ |
| S-04 | `al_p1_ts_01` | 铝 盘面结构 主连结算价 | al | p1 | matchable | `simulated` | False | 1 | 1.64 | 1.74 | ✅ |
| S-05 | `al_p4_ts_02` | 铝 价差体系 期限结构 | al | p4 | pending_data | `simulated` | False | 1 | 1.59 | 1.61 | ✅ |
| S-06 | `al_p1_ts_01` | 铝 盘面结构 主连结算价 | al | p1 | matchable | `simulated` | False | 1 | 1.55 | 1.56 | ✅ |
| S-07 | `pb_p1_ts_01` | 铅 盘面结构 主连结算价 | pb | p1 | matchable | `simulated` | False | 1 | 1.56 | 1.56 | ✅ |
| S-08 | `pb_p3_ts_02` | 铅 海外价格 COMEX铅 | pb | p3 | pending_data | `simulated` | False | 1 | 1.56 | 1.58 | ✅ |
| S-09 | `zn_p1_ts_01` | 锌 盘面结构 主连结算价 | zn | p1 | matchable | `simulated` | False | 1 | 1.56 | 1.58 | ✅ |
| S-10 | `zn_p4_ts_02` | 锌 价差体系 期限结构 | zn | p4 | pending_data | `simulated` | False | 1 | 1.56 | 1.56 | ✅ |
| S-11 | `ni_p1_ts_01` | 镍 盘面结构 主连结算价 | ni | p1 | matchable | `simulated` | False | 1 | 1.58 | 1.61 | ✅ |
| S-12 | `ni_p3_ts_02` | 镍 海外价格 COMEX镍 | ni | p3 | pending_data | `simulated` | False | 1 | 1.54 | 1.56 | ✅ |
| S-13 | `sn_p1_ts_01` | 锡 盘面结构 主连结算价 | sn | p1 | matchable | `simulated` | False | 1 | 1.55 | 1.58 | ✅ |
| S-14 | `sn_p1_ts_01` | 锡 盘面结构 主连结算价 | sn | p1 | matchable | `simulated` | False | 1 | 1.53 | 1.55 | ✅ |
| S-15 | `li_p1_ts_01` | 锂 盘面结构 主连结算价 | li | p1 | matchable | `simulated` | False | 1 | 1.53 | 1.53 | ✅ |
| S-16 | `li_p3_ts_01` | 锂 海外价格 LME锂 | li | p3 | pending_data | `simulated` | False | 1 | 1.54 | 1.54 | ✅ |
| S-17 | `si_p1_ts_01` | 硅 盘面结构 主连结算价 | si | p1 | matchable | `simulated` | False | 1 | 1.55 | 1.58 | ✅ |
| S-18 | `si_p3_ts_01` | 硅 海外价格 LME硅 | si | p3 | pending_data | `simulated` | False | 1 | 1.55 | 1.55 | ✅ |
| S-19 | `cu_p4_ts_02` | 铜 价差体系 期限结构 | cu | p4 | pending_data | `simulated` | False | 1 | 1.54 | 1.54 | ✅ |
| S-20 | `li_p1_ts_01` | 锂 盘面结构 主连结算价 | li | p1 | matchable | `simulated` | False | 1 | 1.55 | 1.56 | ✅ |

---

## 2. 渲染质量指标汇总

| 指标 | 值 | 阈值 | 判定 |
|---|---|---|---|
| 抽样执行率 | **20/20（100%）** | 20/20 | ✅ PASS |
| 渲染成功率（renderable=True） | **20/20** | 100% | ✅ PASS |
| 崩溃数 | **0** | =0 | ✅ PASS |
| placeholder 触发数 | **0/20** | =0 | ✅ PASS |
| 数据点非空率 | **20/20** | 100% | ✅ PASS |
| 渲染时延中位数（min/max） | 1.53 / 1.76 ms | — | ✅ |
| 渲染时延平均值 | 1.57 ms | — | ✅ |
| 渲染时延最大值 | **4.63 ms** | <500ms | ✅ PASS（余量 99.1%）|
| P99 达标 | **PASS** | <500ms | ✅ |

**渲染引擎机制判定：PASS。** 三级降级链路（real→simulated→placeholder）完整可运行，无阻断级渲染异常。

---

## 3. 数据源真实性交叉比对（核心）

### 3.1 全量 101 张图表 source 分布（HERMEShf 实测）

```
(data_status, source, placeholder) → count
  ('matchable',    'simulated', False) → 85   ← 全量匹配类图表
  ('pending_data', 'simulated', False) → 16   ← 全量 pending 图表
  ('matchable',    'real',      False) → 0    ← ⚠️ 无任何真实数据渲染
  ('*',            'placeholder',*)  → 0      ← 无占位符
```

| 项 | DSHE 声称 | HERMEShf 实测 | 差异 |
|---|---|---|---|
| 图表总数 | 101 | **101** | ✅ 一致 |
| matchable 数 | 85 | **85** | ✅ 一致 |
| pending_data 数 | 16 | **16** | ✅ 一致 |
| real source 图表数 | 隐含 980 推送 real | **0** | ❌ **D-SRC** |
| simulated source | 隐含 42 sim | **101（100%）** | ❌ **D-SRC** |

### 3.2 差异 D-SRC 根因链（已定位到代码行）

```
render_with_fallback() 三级降级链:
  Step 1  real_data = self._load_real_data(cb)      ← 全部返回 None
  Step 2  sim_data  = self._generate_simulated_data(cb)  ← 101/101 命中
  Step 3  placeholder = self._generate_placeholder(cb)   ← 未触发

_load_real_data() 实现:
  db_path = scripts/api_cache.db          ← 文件存在
  SELECT data_json FROM indicator_cache
    WHERE metric=? AND code=?             ← 0 行命中

api_cache.db 实际内容:
  表 indicator_cache: 3 行, code 唯一值=1('AO'), metric 唯一值=3('wr50','wr52','wr56')
  图表指标数: 109, 图表指标 ∩ db metric = 0 (空集)
```

**根因定论**：真实数据层 `api_cache.db` 未灌入 8 品种（CU/AL/PB/ZN/NI/SN/LI/SI）的任何指标数据，仅有 3 行无关的 `code='AO'` 条目。因此所有图表在 Step 1 必然落空，100% 降级至 simulated。DSHB 推送日志的 `real=980 / sim=42` 为 DSHB 数据供给引擎的**自计数口径**，其 50 条 sample_entries 中 44 条 `render_mode='real'` 亦为自计，**不代表图表端实际渲染到真实数据**。

### 3.3 与已知约束的关系（非违规）

| 检查 | 结论 |
|---|---|
| NO_ZHIJI_API_CALL | ✅ 合规——全程零知几 API 调用，数据为离线仿真。本阶段设计即如此 |
| NO_MODIFY_V87 | ✅ 合规——`api_cache.db` 属工作区缓存（不进 git），非 V87 资产 |
| 数据真实性门禁 | ⚠️ **Phase02 门禁矩阵未设置「真实数据覆盖率」门禁项**——这是门禁设计缺口，非执行违规 |

---

## 4. 6 项 DSHB pending 指标可定位性核验

| # | 指标 ID | 图表命中数 | 判定 |
|---|---|---|---|
| — | `CU_SMELTER_MAINTENANCE` | **0** | ⚠️ D-PND |
| — | `NI_SMELTER_MAINTENANCE` | **0** | ⚠️ D-PND |
| — | `SI_SMELTER_MAINTENANCE` | **0** | ⚠️ D-PND |
| — | `CU_SPOT_INQUIRY_FREQ` | **0** | ⚠️ D-PND |
| — | `LC_SPOT_INQUIRY_FREQ` | **0** | ⚠️ D-PND |
| — | `SI_SPOT_INQUIRY_FREQ` | **0** | ⚠️ D-PND |

**差异 D-PND（MEDIUM）**：6 项 DSHB pending 备选指标在 101 张图表的指标绑定中**均未出现**。Phase02 声称的「DSHE 降级渲染 6/6 验证」实为 `pending_data` 状态图表（16 张）的 simulated 降级渲染验证，**并非这 6 项具体备选指标的图表绑定验证**。备选方案有效性（IC/IR 数值 5[Y]+1[R]）在 DSHB 侧日志层面成立，但未贯通至图表绑定层。

---

## 5. 差异清单与分级

| 编号 | 级别 | 差异 | 证据 | 处置建议 |
|---|:---:|---|---|---|
| **D-SRC** | **🔴 P1 阻断** | 101/101 图表 100% simulated，`real=980` 无落地支撑 | api_cache.db 3 行 code='AO'，指标交集=0 | 修正总报告 §2.2「真实数据覆盖率」为 0%，新增门禁项，纳入 Phase03-P0 |
| **D-PND** | 🟡 MEDIUM | 6 项 pending 备选指标在图表层 0 绑定 | 6/6 图表命中数=0 | 总报告补充说明：备选有效性仅 DSHB 日志层成立 |
| D-LAT | ✅ 无差异 | P99 时延 | 实测 max 4.63ms ≪ 190.47ms | 总报告保留 190.47ms（并发压测口径），补注单机抽样口径 4.63ms |
| D-TOT | ✅ 无差异 | 图表总数/状态分布 | 101/85/16 全一致 | 无需修正 |
| D-PHB | ✅ 无差异 | placeholder | 0/20 触发 | 无需修正 |

**分级判定**：1 项 P1 阻断（D-SRC）· 1 项 MEDIUM（D-PND）· 3 项无差异 · 0 项 P0

**渲染侧指标可信度结论**：渲染引擎**机制可信**（链路完整、时延达标、零崩溃），但渲染**数据真实性不可信**（100% simulated）。按工单「无阻断问题则确认渲染侧指标可信」——**存在 1 项 P1 阻断，故不签署「渲染侧指标可信」，改为签署「渲染引擎机制可信 + 数据真实性待 Phase03 解决」**。

---

## 6. 归档与移交

| 项 | 内容 |
|---|---|
| 新增风险 | **R-V88-013（P1）**：图表端真实数据覆盖率 0%，`api_cache.db` 未灌入 8 品种指标数据 |
| 新增风险 | **R-V88-014（MEDIUM）**：6 项 pending 备选指标未绑定至图表层 |
| Phase03 移交 | R-V88-013 → Phase03-P0 优先项（与 G1 指标扩量合并：扩量必须含真实数据灌库，否则 200+ 指标仍为 0% 覆盖率） |
| Phase03 移交 | R-V88-014 → Phase03-P0（DSHE 图表绑定扩展） |
| 门禁新增 | Phase03 门禁矩阵新增「真实数据覆盖率 ≥95%」项（D-7），否则 D-5 扩量门禁无意义 |
| 原始数据 | 20 项抽样明细（含 chart_id/source/latency/indicators）随本报告归档 |

---

## 7. 抽样原始明细（附录）

```json
[
 {
  "case": "S-01",
  "chart_id": "cu_p1_ts_01",
  "title": "铜 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "cu",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "CU_FU00014941"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.76,
  "lat_max": 4.63
 },
 {
  "case": "S-02",
  "chart_id": "cu_p4_ts_02",
  "title": "铜 价差体系 期限结构",
  "chart_type": "time_series",
  "commodity": "cu",
  "node": "p4",
  "data_status": "pending_data",
  "indicators": [
   "CU_TERM_STRUCTURE"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.61,
  "lat_max": 1.66
 },
 {
  "case": "S-03",
  "chart_id": "cu_p4_ts_02",
  "title": "铜 价差体系 期限结构",
  "chart_type": "time_series",
  "commodity": "cu",
  "node": "p4",
  "data_status": "pending_data",
  "indicators": [
   "CU_TERM_STRUCTURE"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.6,
  "lat_max": 1.64
 },
 {
  "case": "S-04",
  "chart_id": "al_p1_ts_01",
  "title": "铝 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "al",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "AL_FU00014934"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.64,
  "lat_max": 1.74
 },
 {
  "case": "S-05",
  "chart_id": "al_p4_ts_02",
  "title": "铝 价差体系 期限结构",
  "chart_type": "time_series",
  "commodity": "al",
  "node": "p4",
  "data_status": "pending_data",
  "indicators": [
   "AL_TERM_STRUCTURE"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.59,
  "lat_max": 1.61
 },
 {
  "case": "S-06",
  "chart_id": "al_p1_ts_01",
  "title": "铝 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "al",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "AL_FU00014934"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.55,
  "lat_max": 1.56
 },
 {
  "case": "S-07",
  "chart_id": "pb_p1_ts_01",
  "title": "铅 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "pb",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "PB_FU00014946"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.56,
  "lat_max": 1.56
 },
 {
  "case": "S-08",
  "chart_id": "pb_p3_ts_02",
  "title": "铅 海外价格 COMEX铅",
  "chart_type": "time_series",
  "commodity": "pb",
  "node": "p3",
  "data_status": "pending_data",
  "indicators": [
   "COMEX_PB"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.56,
  "lat_max": 1.58
 },
 {
  "case": "S-09",
  "chart_id": "zn_p1_ts_01",
  "title": "锌 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "zn",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "ZN_FU00014950"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.56,
  "lat_max": 1.58
 },
 {
  "case": "S-10",
  "chart_id": "zn_p4_ts_02",
  "title": "锌 价差体系 期限结构",
  "chart_type": "time_series",
  "commodity": "zn",
  "node": "p4",
  "data_status": "pending_data",
  "indicators": [
   "ZN_TERM_STRUCTURE"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.56,
  "lat_max": 1.56
 },
 {
  "case": "S-11",
  "chart_id": "ni_p1_ts_01",
  "title": "镍 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "ni",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "NI_FU00014982"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.58,
  "lat_max": 1.61
 },
 {
  "case": "S-12",
  "chart_id": "ni_p3_ts_02",
  "title": "镍 海外价格 COMEX镍",
  "chart_type": "time_series",
  "commodity": "ni",
  "node": "p3",
  "data_status": "pending_data",
  "indicators": [
   "COMEX_NI"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.54,
  "lat_max": 1.56
 },
 {
  "case": "S-13",
  "chart_id": "sn_p1_ts_01",
  "title": "锡 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "sn",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "SN_FU00014952"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.55,
  "lat_max": 1.58
 },
 {
  "case": "S-14",
  "chart_id": "sn_p1_ts_01",
  "title": "锡 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "sn",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "SN_FU00014952"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.53,
  "lat_max": 1.55
 },
 {
  "case": "S-15",
  "chart_id": "li_p1_ts_01",
  "title": "锂 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "li",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "LC_FU00015030"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.53,
  "lat_max": 1.53
 },
 {
  "case": "S-16",
  "chart_id": "li_p3_ts_01",
  "title": "锂 海外价格 LME锂",
  "chart_type": "time_series",
  "commodity": "li",
  "node": "p3",
  "data_status": "pending_data",
  "indicators": [
   "LME_LC"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.54,
  "lat_max": 1.54
 },
 {
  "case": "S-17",
  "chart_id": "si_p1_ts_01",
  "title": "硅 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "si",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "SI_FU00015015"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.55,
  "lat_max": 1.58
 },
 {
  "case": "S-18",
  "chart_id": "si_p3_ts_01",
  "title": "硅 海外价格 LME硅",
  "chart_type": "time_series",
  "commodity": "si",
  "node": "p3",
  "data_status": "pending_data",
  "indicators": [
   "LME_SI"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.55,
  "lat_max": 1.55
 },
 {
  "case": "S-19",
  "chart_id": "cu_p4_ts_02",
  "title": "铜 价差体系 期限结构",
  "chart_type": "time_series",
  "commodity": "cu",
  "node": "p4",
  "data_status": "pending_data",
  "indicators": [
   "CU_TERM_STRUCTURE"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.54,
  "lat_max": 1.54
 },
 {
  "case": "S-20",
  "chart_id": "li_p1_ts_01",
  "title": "锂 盘面结构 主连结算价",
  "chart_type": "time_series",
  "commodity": "li",
  "node": "p1",
  "data_status": "matchable",
  "indicators": [
   "LC_FU00015030"
  ],
  "source": "simulated",
  "placeholder": false,
  "renderable": true,
  "points": 1,
  "lat_med": 1.55,
  "lat_max": 1.56
 }
]
```

---

## 8. 验收标准对照

| # | 验收标准 | 达成 | 说明 |
|---|---|---|---|
| 1 | 20 项抽样回放执行完毕 | ✅ | 20/20，0 崩溃 |
| 2 | 无阻断级渲染异常 | ⚠️ | 渲染机制 0 阻断；**数据真实性 1 项 P1（D-SRC）** |
| 3 | 指标交叉比对记录完整归档 | ✅ | §3 交叉比对 + §7 原始明细 |
| 4 | 无阻断问题则确认渲染侧指标可信 | ❌→改签 | 存在 P1，改签「引擎机制可信 + 数据真实性待解决」 |

*Document Generated: 2026-10-15 UTC+8*
*Generated by: HERMEShf Agent（真实执行 NodeBindingEngine，非采信 DSHE 自报）*
*Branch: feature/v88-g1 (BASELINE 1a1fcd4)*
*Status: SAMPLE_VERIFY_COMPLETE_WITH_1_P1_BLOCKING*
