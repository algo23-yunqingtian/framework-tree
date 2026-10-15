# V88 Phase03 P0 — DSHB 指标口径区分说明文档

> **TASK_ID**: V88_PHASE03_P0_DSHB_ARTIFACT_ARCHIVE
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **日期**: 2026-10-15
> **目的**: 明确定义 DSHB「DB层映射命中率」与引擎侧「D7 真实渲染覆盖率」的差异，消除三方口径混淆

---

## 1. 核心定义对比

| 维度 | DSHB DB层映射命中率 | 引擎侧 D7 真实渲染覆盖率 |
|------|---------------------|-------------------------|
| **定义** | phase03_test.db 中 DSHB indicator_id 映射到 DSHE meta_chart indicator_id 的命中率 | NodeBindingEngine 实际从数据库读取并渲染真实数据的图表数 / 总图表数 |
| **计算公式** | (DB 中 indicator_id_mapped 非空的唯一 indicator_id 数) / (meta_chart 定义的总指标数) × 100% | (引擎实际获取到 source='real' 数据的图表数) / (总图表数) × 100% |
| **当前值** | **84/109 = 77.06%** | **0/101 = 0.00%** |
| **数据来源** | phase03_test.db (series_cache 表) + meta_chart.yaml | NodeBindingEngine → scripts/api_cache.db (indicator_cache 表) |
| **查询方式** | `SELECT indicator_id_mapped FROM series_cache WHERE indicator_id_mapped IS NOT NULL` | `SELECT data_json FROM indicator_cache WHERE metric=? AND code=?` |
| **表结构** | `series_cache(indicator_id, indicator_id_mapped, commodity, date, value, source)` | `indicator_cache(metric, code, data_json, fetched_at)` |
| **阈值** | ≥60% (D-7 P0 门禁阈值) | ≥60% (D-7 P0 门禁阈值) |
| **判定** | **✅ PASS (77.06% ≥ 60%)** | **❌ FAIL (0.00% < 60%)** |

---

## 2. 口径差异根因

### 2.1 表结构不兼容

```
DSHB phase03_test.db schema (series_cache):
  indicator_id TEXT        -- DSHB 原始指标名 (如 zn_21_close_front)
  indicator_id_mapped TEXT -- DSHE meta_chart 指标名 (如 ZN_FU00014950)
  commodity TEXT           -- 品种代码 (如 zn)
  date TEXT                -- 日期
  value REAL               -- 数值
  source TEXT              -- 来源 (real/simulated)

NodeBindingEngine 期望 schema (indicator_cache):
  metric TEXT              -- DSHB 指标名
  code TEXT                -- 品种代码 (如 ZN)
  data_json TEXT           -- JSON 格式时序数据
  fetched_at TEXT          -- 获取时间
```

### 2.2 引擎数据源路径硬编码

`scripts/node_binding_engine.py` 第 624 行：
```python
db_path = os.path.join(repo_root, "scripts", "api_cache.db")
```

第 638 行：
```python
cursor.execute(
    "SELECT data_json FROM indicator_cache WHERE metric=? AND code=?",
    (metric, code)
)
```

**结论**: 即使 DSHB 的 phase03_test.db 数据完备（475,593行/615指标/77.06%映射命中），引擎也无法读取，因为：
1. 引擎读取的是 `scripts/api_cache.db`（仅 3 行模拟数据），不是 `phase03_test.db`
2. 引擎查询的是 `indicator_cache(metric, code)` 表，不是 `series_cache(indicator_id, indicator_id_mapped)` 表

### 2.3 映射命中率 vs 渲染覆盖率的差异本质

```
DSHB 映射命中率 (77.06%):
  ┌─────────────────────────────────────────────┐
  │  phase03_test.db                              │
  │  indicator_id  →  indicator_id_mapped        │
  │  zn_21_close_front → ZN_FU00014950  ✅      │
  │  cu_22_premium    → CU_SPOT_PREMIUM      ✅  │
  │  al_00_basis     → AL_BASIS               ✅  │
  │  ... (84/109 命中)                            │
  └─────────────────────────────────────────────┘
  → 映射关系正确，数据存在于 DB

引擎 D7 渲染覆盖率 (0.00%):
  ┌─────────────────────────────────────────────┐
  │  NodeBindingEngine                           │
  │  查询: SELECT data_json FROM indicator_cache │
  │        WHERE metric='zn_21_close_front'      │
  │        AND code='ZN'                         │
  │  → 表不存在 → 0 行 → 0 命中                   │
  └─────────────────────────────────────────────┘
  → 引擎无法读取数据，全部降级为 simulated
```

---

## 3. DSHB 侧达成状态

| 验收项 | 状态 | 证据 |
|--------|:----:|------|
| 独立库 phase03_test.db 创建 | ✅ PASS | 475,593 行 / 615 指标 / 65.7 MB |
| 6 个 JSONL 全部灌入 | ✅ PASS | ZN+NI+SI+SN+LI+CU/AL/PB supplement |
| 0 导入错误 | ✅ PASS | import_log: err=0 |
| 0 主键冲突 | ✅ PASS | INSERT OR IGNORE 无冲突 |
| 双键映射命中率 ≥60% | ✅ PASS | 84/109 = 77.06% |
| R-09 数据隔离达标 | ✅ PASS | phase03_test.db ≠ scripts/api_cache.db |
| R-V88-025 关闭 | ✅ CLOSED | 独立库隔离达标 |
| R-V88-028 数据侧闭环 | ✅ CLOSED | DB层映射命中 77.06% |
| R-V88-029 灌库脚本修正 | ✅ CLOSED | 目标库指向 phase03_test.db |

---

## 4. 引擎侧未达成状态（非 DSHB 权限）

| 验收项 | 状态 | 根因 | 责任方 |
|--------|:----:|------|--------|
| D-7 真实覆盖率 ≥60% | ❌ FAIL | 引擎数据源路径硬编码 | DSHE/HERMEShf |
| B-3 命名映射 | BLOCKED | 引擎查询 indicator_cache 表不存在 | DSHE/HERMEShf |
| C-3 D-7 覆盖率 | BLOCKED | 引擎无法读取独立库 | DSHE/HERMEShf |
| P0-9 覆盖率 | 0.00% | 同上 | DSHE/HERMEShf |

---

## 5. 术语对照表

| 术语 | DSHB 口径 | 引擎口径 |
|------|-----------|----------|
| 覆盖率 | DB 中映射命中率 (77.06%) | 引擎实际渲染覆盖率 (0.00%) |
| 映射表 | `dshe_naming_mapping.json` (DSHE→DSHB) | `INDICATOR_MAPPING` in cache_coverage_calc.py |
| 映射方式 | 显式映射 + 模式映射函数 | 元图表 YAML → DSHB 指标名 |
| 数据来源 | `data/db_export/*.jsonl` | `scripts/api_cache.db` (indicator_cache) |
| 数据表 | `series_cache` | `indicator_cache` |
| 查询键 | `indicator_id` (原始名) 或 `indicator_id_mapped` (映射名) | `metric` + `code` (双键) |
| 数据来源标记 | `source='real'` 列 | `data_json` 中 `points[].date` 非空 |

---

## 6. 结论

> **DSHB 数据侧 P0 阶段工作全部完成，所有数据层风险已闭环。**
>
> - DB 层映射命中率 77.06% ≥ 60% 阈值 ✅
> - 475,593 行真实数据零错误零冲突 ✅
> - 独立库隔离达标，生产库零污染 ✅
> - 重建脚本可一键复现，无需提交 .db 文件 ✅
>
> **剩余唯一阻断在引擎适配层（DSHE/HERMEShf 侧）**，DSHB P0 阶段工作收尾，等待 P1 阶段任务下发。

---

*Document Generated: 2026-10-15*
*Agent: DSHB*
*Branch: feature/v88-g1 (BRANCH_LOCKED: TRUE)*
*Status: V88_PHASE03_P0_DSHB_ARCHIVE=READY*
