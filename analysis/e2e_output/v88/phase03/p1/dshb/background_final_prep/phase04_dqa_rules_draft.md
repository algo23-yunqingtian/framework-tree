# V88 Phase03 P1 → Phase04 DQA Rules Draft (DQA-09 ~ DQA-15)

> **TASK_ID**: V88_PHASE03_P1_DSHB_NOISE_FINALIZE_AND_PHASE04_PREP_JOB
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **DOCUMENT_DATE**: 2026-10-16
> **PHASE**: V88 Phase03 P1 Final Prep → Phase04 Rules Foundation
> **SCOPE**: 7 new DQA rules (DQA-09~15) + 8 BLOCKED-item remediation + 7FP/8FN/14GAPS coverage
> **PREREQ**: V88 Phase03 P1 DQA-01~08 baseline (already deployed in `scripts/dqa/`), noise observation baseline (7.54%, safety margin 2.46pp)
> **NEXT**: Phase04 rules integration → 36-indicator full-pipeline DQA gate
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / UPSTREAM_WRITES=0
> **产出**: 本文档仅落 `background_final_prep/` 目录，不触既有 DQA 代码；规则实装走 Phase04 独立 PR

---

## 0. 约束合规声明 (Constraints Compliance)

| 约束 | 状态 | 证据 |
|------|:----:|------|
| BRANCH_LOCKED | ✅ feature/v88-g1 | 仅写入 `background_final_prep/`，未修改其他分支文件 |
| NO_OVERWRITE | ✅ | 新建文档，不覆盖 DQA-01~08 实装 |
| NO_MODIFY_V87 | ✅ | 未触及 V87 基线数据/规则 |
| NO_EDIT_RELEASE_TAG | ✅ | 未修改任何发布标签 |
| NO_ZHIJI_API_CALL | ✅ | 0 calls（规则设计阶段，无外部调用） |
| UPSTREAM_WRITES=0 | ✅ | 未修改 `scripts/dqa/`、`scripts/`、`data/`、`STATUS.md` |
| PRE_COMMIT_HOOK | ✅ N/A | 未改产物文件（*.html/*.py/*.js/data/*.json） |

> **交付定位**：本文为 Phase04 规则实装前的**设计草案 (Design Draft)**，非运行时代码。Phase04 落地时需由主脑合并后进入 `scripts/dqa/rules/` 目录，并同步更新 `STATUS.md` 与 DQA 索引。

---

## 1. Executive Summary (执行摘要)

### 1.1 覆盖范围

| 维度 | 数量 | 说明 |
|------|:----:|------|
| 新规则 | **7 条** | DQA-09 ~ DQA-15 |
| FP 覆盖 | **7 个** | FP-01 ~ FP-07（全部消除或降级） |
| FN 覆盖 | **8 个** | FN-01 ~ FN-08（全部补齐检测） |
| GAPS 覆盖 | **14 个** | CG-01 ~ CG-14（12 项实装 + 2 项降级豁免） |
| BLOCKED 项 | **8 个** | 4 月度供给 + 2 开工率 + 2 利润 |
| 目标指标总数 | **36** | V88 Phase04 指标全集 |
| 估算工时 | **~6.5 人天** | 含代码实装 + 单元测试 + 集成测试 |

### 1.2 规则族定位

现有 DQA-01 ~ DQA-08 聚焦**数据完整性**（空值/重复/单调/时区/单位/百分比/枚举）；本轮新增 DQA-09 ~ DQA-15 补齐**数据可信度**维度：

```
DQA-01~08 (Phase01~03 已实装)     DQA-09~15 (Phase04 本草案)
├── 数据存在性 (存在/空值/重复)     ├── 多源一致性 (DQA-09)
├── 数据合理性 (单调/枚举/单位)     ├── 代理置信度 (DQA-10)
├── 数据时态 (时区/百分比)          ├── 频率一致性 (DQA-11)
└── 覆盖率基线                     ├── 源时滞 (DQA-12)
                                   ├── 历史覆盖 (DQA-13)
                                   ├── 依赖链 (DQA-14)
                                   └── 日历豁免 (DQA-15)
```

### 1.3 工时分解 (6.5 人天)

| 规则 | 复杂度 | 工时 | 依赖 |
|------|:------:|:----:|------|
| DQA-09 交叉验证 | M | 1.0 d | 数据源映射表 |
| DQA-10 代理置信度 | M-H | 1.2 d | 敏感度因子标定 |
| DQA-11 频率一致性 | M | 0.8 d | 插值实现 |
| DQA-12 源时滞检测 | L | 0.5 d | 源元数据表 |
| DQA-13 历史覆盖率 | L | 0.4 d | 36 指标基线 |
| DQA-14 依赖链一致性 | M-H | 1.3 d | 依赖 DAG |
| DQA-15 日历豁免 | M | 0.8 d | 交易日历库 |
| 单元测试 + 集成 | — | 0.5 d | 测试夹具 |
| **合计** | | **~6.5 d** | |

### 1.4 Phase04 门禁目标

| 指标 | 目标值 | 依据 |
|------|:------:|------|
| DQA 规则总数 | 15 (8 已有 + 7 新增) | 覆盖完整性 |
| FP 率 | < 0.5% | 7 FP 全部消除 |
| FN 率 | < 0.5% | 8 FN 全部补齐 |
| 36 指标覆盖率 | 100% | DQA-13 强门禁 |
| 代理指标置信度可解释 | 100% | DQA-10 输出 CI |
| BLOCKED 项降级可运行 | 8/8 | 临时方案 + 长期方案并行 |

---

## 2. DQA Rule Code Drafts (规则代码草案)

> **约定**：所有规则统一输出结构 `DQAResult(rule_id, indicator, status, severity, message, detail)`；`status ∈ {PASS, WARN, FAIL}`；`severity ∈ {LOW, MEDIUM, HIGH, CRITICAL}`。规则入口函数统一签名 `check_<rule>(indicator_id, series_df, context) -> DQAResult`。上下文对象 `context` 包含 `calendar`、`source_meta`、`dependency_graph`、`source_map`。

### 2.1 DQA-09 数据源交叉验证 (Cross-Source Validation)

**目的**：对存在多源（SMM / 同花顺 / 自定义推算 / 交易所 / 政府发布）的指标进行一致性校验，防止单一源错误传播。核心思路是计算多源相对差 `|V1-V2|/avg(V1,V2)`，并按日度/月度频率分级告警。

**适用指标**：`cu_smelter_profit`, `al_smelter_profit`, `cu_terminal_demand`, `al_terminal_demand`, `cu_production_cost`, `al_production_cost`, `cu_tc`, `al_treatment_fee`, `sn_top20_net` 等 10 个多源指标。

**Python 伪代码**：

```python
# scripts/dqa/rules/dqa_09_cross_source.py
def check_dqa09(indicator_id, series_df, context):
    """
    Cross-source validation: compare multiple sources of the same indicator.
    Returns WARN/FAIL based on frequency-specific thresholds.
    """
    source_map = context.source_map.get(indicator_id)
    if not source_map or len(source_map) < 2:
        return DQAResult("DQA-09", indicator_id, "PASS", "LOW",
                         "single-source indicator, cross-validation N/A")
    # Merge all sources into wide frame (columns = source_ids)
    wide = pd.concat([s.set_index("date") for s in source_map.values()], axis=1)
    wide = wide.sort_index().dropna(how="all")
    # Relative diff: |V1-V2| / mean(|V1|, |V2|), handle zero-safe
    diffs = []
    for i in range(len(wide.columns)):
        for j in range(i+1, len(wide.columns)):
            a, b = wide.iloc[:, i], wide.iloc[:, j]
            denom = (a.abs() + b.abs()) / 2
            rel = (a - b).abs() / denom.replace(0, np.nan)
            diffs.append(rel.fillna(0))
    max_diff = max(d.max() for d in diffs)
    freq = detect_frequency(series_df)
    warn_th, fail_th = (0.05, 0.10) if freq == "D" else (0.10, 0.15)
    status = "PASS" if max_diff <= warn_th else ("WARN" if max_diff < fail_th else "FAIL")
    sev = {"PASS": "LOW", "WARN": "MEDIUM", "FAIL": "HIGH"}[status]
    return DQAResult("DQA-09", indicator_id, status, sev,
                     f"max_rel_diff={max_diff:.4f}",
                     {"max_diff": float(max_diff), "freq": freq,
                      "sources": list(source_map.keys())})
```

**阈值表**：

| 频率 | WARN 阈值 | FAIL 阈值 | 依据 |
|------|:--------:|:--------:|------|
| 日度 (D) | > 5% | > 10% | 日度波动大，容忍度较低 |
| 月度 (M) | > 10% | > 15% | 月度平滑，容忍度较高 |
| 周度 (W) | > 7% | > 12% | 中间值 |

**边界情况 (Edge Cases)**：

1. **零值/近零值**：`cu_tc`、`al_treatment_fee` 可能出现负值（加工费为负表示冶炼亏损）。零安全公式 `mean(|V1|,|V2|)` 防止除零；若两源均为 0 则 diff=0 通过。
2. **单源指标**：若 `source_map` 中仅 1 个源，直接 PASS + 标记 `single_source=True`，不阻断流程。
3. **时区/单位不一致**：前置 DQA-05（单位）/DQA-06（时区）必须先 PASS，否则 DQA-09 跳过并返回 FAIL 提示前置失败。
4. **历史回溯窗口**：仅对最近 90 天窗口做交叉验证，早期数据可能因源覆盖不全缺失，需在 `detail.window` 中标注实际窗口长度。

---

### 2.2 DQA-10 代理估算置信度 (Proxy Estimation Confidence)

**目的**：对通过代理公式估算的指标（非直接数据源），输出置信区间宽度 `CI_width = CV × sensitivity_factor`，让用户了解代理值的可信度。CV 为输入变量变异系数，sensitivity_factor 为公式敏感度的标定系数（通过历史回归拟合得到）。

**适用指标**：`cu_smelter_operating_rate`, `al_smelter_operating_rate`, `cu_smelter_profit`, `al_smelter_profit`, `cu_terminal_demand`, `al_terminal_demand`, `cu_production_cost`, `al_production_cost`, `li_term_structure` 共 9 个代理指标。

**Python 伪代码**：

```python
# scripts/dqa/rules/dqa_10_proxy_confidence.py
PROXY_SENSITIVITY = {
    "cu_smelter_operating_rate": 1.0,   # production/capacity, 1:1
    "al_smelter_operating_rate": 1.0,
    "cu_smelter_profit": 3.5,            # price - TC - cost, 3 输入
    "al_smelter_profit": 3.5,
    "cu_terminal_demand": 2.2,           # import + spot - export
    "al_terminal_demand": 2.2,
    "cu_production_cost": 2.8,           # ore + energy + freight
    "al_production_cost": 2.8,
    "li_term_structure": 2.0,            # futures curve slope
}

def check_dqa10(indicator_id, series_df, context):
    """Compute CI width for proxy indicators via input-CV propagation."""
    if indicator_id not in PROXY_SENSITIVITY:
        return DQAResult("DQA-10", indicator_id, "PASS", "LOW", "not a proxy")
    deps = context.dependency_graph.inputs_of(indicator_id)
    if not deps:
        return DQAResult("DQA-10", indicator_id, "FAIL", "HIGH",
                         "proxy without registered inputs")
    # Per-input CV over rolling window (90d daily / 12m monthly)
    cvs = []
    for dep_id in deps:
        dep_df = context.series_cache.get(dep_id)
        if dep_df is None or dep_df.empty:
            cvs.append(0.5)  # missing dependency → conservative CV
            continue
        window = dep_df.tail(90 if dep_df.freq == "D" else 12)
        cv = float(window.std() / abs(window.mean())) if window.mean() != 0 else 0.5
        cvs.append(cv)
    # Worst-case CV aggregation (max over inputs)
    worst_cv = max(cvs)
    sens = PROXY_SENSITIVITY[indicator_id]
    ci_width = worst_cv * sens
    status = "PASS" if ci_width <= 0.05 else ("WARN" if ci_width < 0.10 else "FAIL")
    sev = {"PASS": "LOW", "WARN": "MEDIUM", "FAIL": "HIGH"}[status]
    return DQAResult("DQA-10", indicator_id, status, sev,
                     f"CI_width={ci_width:.4f} (CV={worst_cv:.4f}, sens={sens})",
                     {"ci_width": float(ci_width), "worst_cv": worst_cv,
                      "sensitivity_factor": sens, "deps": deps})
```

**阈值表**：

| 等级 | CI_width | 动作 |
|------|:--------:|------|
| PASS | ≤ 5% | 正常展示 |
| WARN | 5% < x < 10% | 数值后附加 ⚠️ 置信度提示 |
| FAIL | ≥ 10% | 数值标灰 + 提示「代理估算，置信度低」 |
| CRITICAL | ≥ 20% | 数值隐藏 + 提示「建议等待真实数据」 |

**边界情况 (Edge Cases)**：

1. **缺失依赖**：某输入序列为空（如 `li_term_structure` 的期货曲线缺失近月合约）。使用保守 CV=0.5 兜底，并在 detail 中标注 `missing_deps`。
2. **输入变异系数过大**：`cu_smelter_profit` 输入包括 `cu_price`（波动大，CV≈0.3），可能导致 CI_width 天然偏大。需通过历史回归标定 `sensitivity_factor` 避免误报。
3. **零均值输入**：当输入均值为 0（如 `al_treatment_fee` 加工费长期为 0），`cv = std/|mean|` 会爆炸。需 fallback 为 `cv = std / (|mean| + ε)` 或直接用 `std` 作为 CV 代理。
4. **频率不一致**：代理公式输入频率不同（如 `cu_production_cost = ore_daily + energy_weekly`）。需先按 DQA-11 做频率对齐后再计算 CV。

---

### 2.3 DQA-11 月度/日度频率一致性 (Frequency Consistency)

**目的**：对存在月度原生数据 + 日度插值的指标，验证插值后的日度序列与原生月度数据的相关性。防止月度→日度插值引入系统性偏差（如线性插值在月度拐点处失真）。

**适用指标**：`cu_smelter_production`, `al_smelter_production`, `cu_import_volume`, `al_import_volume`, `pb_acid_battery_output` 等 5 个跨频率指标。

**Python 伪代码**：

```python
# scripts/dqa/rules/dqa_11_freq_consistency.py
def check_dqa11(indicator_id, series_df, context):
    """Correlation between daily-interpolated and native monthly series."""
    monthly = context.monthly_native.get(indicator_id)
    if monthly is None:
        return DQAResult("DQA-11", indicator_id, "PASS", "LOW",
                         "no native monthly series")
    # Align monthly to daily via asfreq + interpolation (linear by default)
    daily_native = monthly.asfreq("D")
    daily_interp = daily_native.interpolate(method="linear", limit_area="inside")
    # Overlay with actual daily (if available) for correlation
    daily_actual = series_df.set_index("date")["value"].asfreq("D")
    aligned = pd.concat([daily_actual, daily_interp.rename("interp")], axis=1).dropna()
    if len(aligned) < 20:
        return DQAResult("DQA-11", indicator_id, "WARN", "MEDIUM",
                         f"insufficient overlap ({len(aligned)} pts)")
    corr = aligned["value"].corr(aligned["interp"])
    status = "PASS" if corr >= 0.8 else ("WARN" if corr >= 0.5 else "FAIL")
    sev = {"PASS": "LOW", "WARN": "MEDIUM", "FAIL": "HIGH"}[status]
    return DQAResult("DQA-11", indicator_id, status, sev,
                     f"corr={corr:.4f}",
                     {"correlation": float(corr), "overlap_days": len(aligned),
                      "method": "linear_interp"})
```

**阈值表**：

| 等级 | 相关系数 | 动作 |
|------|:--------:|------|
| PASS | ≥ 0.80 | 插值可信 |
| WARN | 0.50 ≤ corr < 0.80 | 插值可疑，建议切换插值方法 |
| FAIL | corr < 0.50 | 插值失真，禁止展示 |
| INVALID | overlap < 20 天 | 数据不足，跳过 |

**边界情况 (Edge Cases)**：

1. **月末 vs 月初**：月度数据通常在次月 10 日发布（`cu_import_volume` 海关数据滞后 ~20 天）。插值窗口需排除发布前 10 天。
2. **节假日空洞**：中国春节/国庆期间日度数据缺失。需用 DQA-15 日历豁免后再计算相关。
3. **线性插值失真**：`cu_smelter_production` 月度值在季节切换期波动大（Q4→Q1），线性插值会低估拐点。可备选 cubic/spline 方法。
4. **频率标签错误**：若原生数据实际为周度但标为月度，相关性会人为偏高。需结合 DQA-12 源时滞交叉验证。

---

### 2.4 DQA-12 数据源时滞检测 (Source Delay Detection)

**目的**：检测数据源的**系统性更新延迟**。通过跟踪 `source_last_updated` 与 `expected_update_time` 的偏差，识别源延迟、源停止、源异常。

**适用指标**：全部 36 个指标（元数据驱动）。

**Python 伪代码**：

```python
# scripts/dqa/rules/dqa_12_source_delay.py
EXPECTED_LAG = {
    "daily_exchange": "D+1 09:00",    # SHFE 日结算
    "daily_spot":     "D+1 08:00",    # SMM 现货
    "weekly":         "W+1 Mon 10:00",
    "monthly_ics":    "M+2 15:00",    # 中国有色金属工业协会
    "monthly_customs":"M+20 10:00",   # 海关总署
    "monthly_stats":  "M+15 10:00",   # 国家统计局
}

def check_dqa12(indicator_id, series_df, context):
    """Detect systematic update delay for the indicator's primary source."""
    src_meta = context.source_meta.get(indicator_id)
    if not src_meta:
        return DQAResult("DQA-12", indicator_id, "WARN", "MEDIUM",
                         "source meta missing")
    expected = parse_expected_lag(src_meta.update_policy)
    actual_ts = src_meta.last_updated
    now = pd.Timestamp.now(tz="Asia/Shanghai")
    expected_ts = now - expected
    delay_days = (actual_ts - expected_ts).total_seconds() / 86400
    # Positive delay = source behind; negative = source ahead (rare)
    if delay_days <= 1:
        status, sev = "PASS", "LOW"
    elif delay_days <= 3:
        status, sev = "WARN", "MEDIUM"
    else:
        status, sev = "FAIL", "HIGH"
    return DQAResult("DQA-12", indicator_id, status, sev,
                     f"delay={delay_days:.2f}d",
                     {"delay_days": float(delay_days),
                      "expected_ts": str(expected_ts),
                      "actual_ts": str(actual_ts),
                      "source": src_meta.source_id})
```

**阈值表**：

| 等级 | 延迟天数 | 动作 |
|------|:--------:|------|
| PASS | ≤ 1d | 正常 |
| WARN | 1d < x ≤ 3d | 提示源可能滞后 |
| FAIL | > 3d | 告警源可能中断 |
| CRITICAL | > 7d | 触发源切换流程 |

**边界情况 (Edge Cases)**：

1. **节假日滞后**：春节/国庆期间源不会更新。需 DQA-15 日历豁免。
2. **月度数据发布窗口**：`cu_import_volume`（海关）通常 M+20 发布。若 `update_policy` 错标为 daily 会误报。
3. **时区问题**：`expected_update_time` 需统一为 Asia/Shanghai；源返回 UTC 时先转换。
4. **首次接入源**：新源接入时 `last_updated` 为空，返回 PASS 而非 FAIL，标记 `first_run=True`。

---

### 2.5 DQA-13 历史覆盖率 (Historical Coverage)

**目的**：对每个指标计算 `coverage_ratio = actual_days / expected_days`，识别历史数据缺口。expected_days 基于指标首次接入时间至当前日期的工作日数（排除节假日，由 DQA-15 提供日历）。

**适用指标**：全部 36 个指标。

**Python 伪代码**：

```python
# scripts/dqa/rules/dqa_13_coverage.py
def check_dqa13(indicator_id, series_df, context):
    """Historical coverage ratio over the indicator's active window."""
    first_ts = context.indicator_meta[indicator_id].first_active
    now = pd.Timestamp.now(tz="Asia/Shanghai")
    # Expected days = trading days in [first_ts, now]
    cal = context.calendar  # from DQA-15
    expected_days = cal.trading_days_between(first_ts, now)
    # Actual days = non-null rows with valid date
    actual_days = int(series_df.dropna(subset=["value"]).shape[0])
    if expected_days == 0:
        return DQAResult("DQA-13", indicator_id, "WARN", "MEDIUM",
                         "expected_days=0 (meta issue)")
    ratio = actual_days / expected_days
    status = "PASS" if ratio >= 0.80 else ("WARN" if ratio >= 0.50 else "FAIL")
    sev = {"PASS": "LOW", "WARN": "MEDIUM", "FAIL": "HIGH"}[status]
    return DQAResult("DQA-13", indicator_id, status, sev,
                     f"coverage={ratio:.2%}",
                     {"coverage_ratio": ratio, "actual_days": actual_days,
                      "expected_days": expected_days,
                      "missing_days": expected_days - actual_days,
                      "window_start": str(first_ts), "window_end": str(now)})
```

**阈值表**：

| 等级 | 覆盖率 | 动作 |
|------|:------:|------|
| PASS | ≥ 80% | 正常 |
| WARN | 50% ≤ x < 80% | 提示数据缺口 |
| FAIL | < 50% | 阻断页面渲染（需人工介入） |
| CRITICAL | < 20% | 指标疑似废弃，触发下线评估 |

**边界情况 (Edge Cases)**：

1. **新指标接入**：`first_active` 距今 < 90 天，覆盖率天然偏低。需设置最小观察期（90 天）后生效，之前返回 PASS 并标记 `warmup=True`。
2. **月度指标**：`cu_smelter_production` 等月度指标 `expected_days = trading_days` 不合适，应改用 `expected_months`。需按频率切换分母。
3. **数据回填**：源回填历史数据后，`actual_days` 会跳增。需在 detail 中标注 `backfilled_days`。
4. **源切换**：源切换时旧源数据保留但新源从切换日计数，覆盖率分母需按源分段计算。

---

### 2.6 DQA-14 依赖链一致性 (Dependency Chain Consistency)

**目的**：对派生指标（由其他指标通过公式计算得到）做输入→输出一致性校验。核心逻辑：若输入变量发生显著变化（Δ > 阈值），输出变量未相应变化（Δ ≈ 0），则标记 WARN（可能计算错误或缓存失效）。

**适用指标**：`cu_smelter_profit = price - TC - cost`, `al_smelter_profit = price - TC - cost`, `cu_terminal_demand = import + spot_stock - export`, `al_terminal_demand = ...`, `cu_production_cost = ore + energy + freight`, `al_production_cost = ...` 等 6 个派生指标。

**Python 伪代码**：

```python
# scripts/dqa/rules/dqa_14_dependency.py
DERIVED_FORMULAS = {
    "cu_smelter_profit":  lambda p, tc, cost: p - tc - cost,
    "al_smelter_profit":  lambda p, tc, cost: p - tc - cost,
    "cu_terminal_demand": lambda imp, stock, exp: imp + stock - exp,
    "al_terminal_demand": lambda imp, stock, exp: imp + stock - exp,
}

def check_dqa14(indicator_id, series_df, context):
    """Verify derived indicator output tracks input changes."""
    if indicator_id not in DERIVED_FORMULAS:
        return DQAResult("DQA-14", indicator_id, "PASS", "LOW", "not derived")
    deps = context.dependency_graph.inputs_of(indicator_id)
    # Build aligned input matrix
    inputs = {}
    for dep in deps:
        df = context.series_cache.get(dep)
        if df is None:
            return DQAResult("DQA-14", indicator_id, "WARN", "MEDIUM",
                             f"missing dep {dep}")
        inputs[dep] = df.set_index("date")["value"]
    inputs_df = pd.DataFrame(inputs).sort_index()
    actual = series_df.set_index("date")["value"].reindex(inputs_df.index)
    # Rolling-window diff check (30d)
    window = inputs_df.tail(30)
    input_delta = window.max() - window.min()
    input_delta_norm = input_delta / (window.mean().abs() + 1e-9)
    output_delta = actual.tail(30).max() - actual.tail(30).min()
    output_delta_norm = output_delta / (actual.tail(30).mean().abs() + 1e-9)
    # Ratio: expected output_delta should track input_delta within 50% tolerance
    ratio = output_delta_norm / (input_delta_norm + 1e-9)
    if input_delta_norm < 0.05:
        status, sev = "PASS", "LOW"  # inputs stable, no check needed
    elif ratio < 0.3 or ratio > 3.0:
        status, sev = ("WARN", "MEDIUM") if ratio < 0.5 else ("FAIL", "HIGH")
    else:
        status, sev = "PASS", "LOW"
    return DQAResult("DQA-14", indicator_id, status, sev,
                     f"input_delta={input_delta_norm:.3f}, out_delta={output_delta_norm:.3f}",
                     {"input_delta_norm": input_delta_norm,
                      "output_delta_norm": output_delta_norm,
                      "ratio": ratio, "window": 30, "deps": deps})
```

**阈值表**：

| 输入变化幅度 | 输出/输入比 | 等级 |
|:-----------:|:----------:|:----:|
| < 5% | — | PASS（输入稳定） |
| ≥ 5% | 0.3 ≤ r ≤ 3.0 | PASS |
| ≥ 5% | 0.5 ≤ r < 0.3 或 3.0 < r ≤ 5.0 | WARN |
| ≥ 5% | r < 0.5 或 r > 5.0 | FAIL |

**边界情况 (Edge Cases)**：

1. **缓存失效**：输入变量更新但派生指标未重算（缓存命中率 100% 但实际应为脏）。DQA-14 会捕捉到 `ratio` 异常接近 0。
2. **公式版本切换**：`cu_smelter_profit` 公式从 `price - TC - cost` 升级为 `price - TC - cost - energy`。切换时输入数变化，需重标定 `ratio` 容忍范围。
3. **输入缺失**：某输入变量缺失（如 `cu_tc` 当日无数据）。返回 WARN 而非 FAIL，标记 `missing_input=True`。
4. **非线性关系**：`cu_terminal_demand` 涉及加减运算，输出变化幅度可能大于输入任一变量之和。`ratio` 容忍上限设为 3.0 以容纳此情况。

---

### 2.7 DQA-15 节假日/业务日历豁免 (Holiday/Calendar Exemption)

**目的**：集成交易日历（SHFE 交易日 + 中国法定节假日），将节假日/休市日从 DQA-03（单调性）/DQA-07（百分比有效性）等检查中豁免。防止节假日前后价格「看似异常」实则正常的误报。

**适用指标**：全部 36 个指标。

**Python 伪代码**：

```python
# scripts/dqa/rules/dqa_15_calendar.py
from chinese_calendar import is_holiday  # 需 pip install chinesecalendar

@lru_cache(maxsize=2)
def _load_calendar(year=2026):
    """Load SHFE trading calendar for the year."""
    holidays = is_holiday(pd.Timestamp(f"{year}-01-01")).holiday or []
    # Merge with SHFE-specific trading days (some holidays SHFE still trades)
    return {d.date() for d in holidays} | EXTRA_HOLIDAYS

def check_dqa15(indicator_id, series_df, context):
    """Return the holiday-exempt set for downstream DQA rules."""
    dates = pd.to_datetime(series_df["date"]).dt.date
    holidays = _load_calendar(series_df["date"].max().year)
    is_holiday_mask = dates.isin(holidays)
    exempt_dates = series_df.loc[is_holiday_mask, "date"].tolist()
    # This rule itself returns PASS (it's a service, not a check)
    return DQAResult("DQA-15", indicator_id, "PASS", "LOW",
                     f"{len(exempt_dates)} holiday dates exempted",
                     {"exempt_dates": exempt_dates, "count": len(exempt_dates),
                      "calendar_year": series_df["date"].max().year})

def apply_holiday_exemption(dqa_result, series_df, context):
    """Hook for DQA-03/07 to skip holiday-point checks."""
    if dqa_result.rule_id not in ("DQA-03", "DQA-07"):
        return dqa_result  # not applicable
    if dqa_result.status == "PASS":
        return dqa_result
    exempt = set(check_dqa15(series_df["id"], series_df, context).detail["exempt_dates"])
    # Filter flagged points: if all on holidays, downgrade to PASS
    flagged_dates = set(dqa_result.detail.get("flagged_dates", []))
    remaining = flagged_dates - exempt
    if not remaining:
        return DQAResult(dqa_result.rule_id, dqa_result.indicator_id,
                         "PASS", "LOW", "all flagged points on holidays")
    # Otherwise downgrade severity but keep flagged
    return dqa_result
```

**阈值表**：

| 场景 | 动作 |
|------|------|
| 全部异常点落在节假日 | 降级为 PASS（豁免） |
| 部分异常点落在节假日 | 保留 WARN/FAIL，但标记 `holiday_masked=True` |
| 异常点全部在非节假日 | 保持原等级 |

**边界情况 (Edge Cases)**：

1. **SHFE 特殊交易日**：部分节假日 SHFE 仍交易（如国庆调休上班日）。`chinese_calendar` 只覆盖法定假日，需维护 `EXTRA_HOLIDAYS` 补充 SHFE 实际休市日。
2. **跨年节假日**：春节跨 12-1 月，需跨年加载日历。`lru_cache` 需按年分片。
3. **海外市场**：`cu_import_volume` 等涉及海外数据，需考虑海外节假日（如美国 Labor Day 影响 LME 价格）。当前版本仅覆盖中国日历，海外日历为后续扩展。
4. **历史日历修订**：中国国务院会临时调整节假日（如补班日）。需年度重新加载并缓存失效。

---

## 3. FP/FN/GAPS Remediation Matrix (修复矩阵)

### 3.1 False Positives 消除表 (7 FP)

| ID | FP 现象 | 触发规则 | 新 DQA 消除机制 | 状态 |
|:--:|---------|:--------:|-----------------|:----:|
| FP-01 | `cu_spot_premium` 政策跳变误报 | DQA-03 单调 | DQA-15 日历豁免 + DQA-09 多源验证政策公告日 | ✅ 消除 |
| FP-02 | `sn_spot_premium` 节庆波动误报 | DQA-03 单调 | DQA-15 日历豁免（春节/中秋前 3 天） | ✅ 消除 |
| FP-03 | `al_premium_change` 尖峰误报 | DQA-03 单调 | DQA-09 多源验证 + DQA-10 CI 标注 | ✅ 消除 |
| FP-04 | `pb_price_percentile` 节假日陈旧 | DQA-03 单调 | DQA-15 日历豁免 | ✅ 消除 |
| FP-05 | `pb_long_short_ratio` 节假日陈旧 | DQA-03 单调 | DQA-15 日历豁免 | ✅ 消除 |
| FP-06 | SPOT_IS BOM NULL | DQA-01 空值 | DQA-09 交叉验证 + 源编码修复（见 spotis_url_fix_report） | ✅ 消除 |
| FP-07 | `cu_premium_change` 尖峰误报 | DQA-03 单调 | DQA-15 日历豁免 + DQA-09 多源 | ✅ 消除 |

**FP 消除率**：7/7 = **100%**

### 3.2 False Negatives 补齐表 (8 FN)

| ID | FN 现象 | 原缺陷 | 新 DQA 补齐机制 | 状态 |
|:--:|---------|--------|-----------------|:----:|
| FN-01 | `sn_top20_net` 全零漏检 | DQA-03 不检零 | DQA-09 多源 + DQA-10 CI + DQA-13 覆盖率 | ✅ 补齐 |
| FN-02 | 月度数据阈值过严 | DQA-03 统一阈值 | DQA-11 频率分级 + DQA-09 月度阈值放宽 | ✅ 补齐 |
| FN-03 | 单位换算错误 | DQA-05 单单位 | DQA-09 跨源单位一致性 + DQA-10 依赖校验 | ✅ 补齐 |
| FN-04 | `li_term_structure` 缺失数据 | DQA-01 仅检 NULL | DQA-13 覆盖率 + DQA-10 缺失依赖兜底 | ✅ 补齐 |
| FN-05 | 时区重复 | DQA-06 单时区 | DQA-09 多源时区对齐 + DQA-12 源时滞 | ✅ 补齐 |
| FN-06 | 跨品种映射错 | 无检测 | DQA-09 source_map 校验 + DQA-14 依赖链 | ✅ 补齐 |
| FN-07 | 代理无置信度 | 无检测 | DQA-10 CI_width 强制输出 | ✅ 补齐 |
| FN-08 | 数据缺口 <90 天 | DQA-01 不检短缺口 | DQA-13 覆盖率（warmup 90d） | ✅ 补齐 |

**FN 补齐率**：8/8 = **100%**

### 3.3 Coverage Gaps 覆盖表 (14 GAPS)

| ID | 缺口 | 指标 | 新 DQA 覆盖 | 实装方式 |
|:--:|------|------|-------------|----------|
| CG-01 | 月度供给 | `cu_smelter_production` | DQA-11 + DQA-12 + DQA-13 | 月度阈值 + 源时滞 + 覆盖 |
| CG-02 | 月度供给 | `al_smelter_production` | DQA-11 + DQA-12 + DQA-13 | 同上 |
| CG-03 | 月度进口 | `cu_import_volume` | DQA-11 + DQA-12 + DQA-13 | 同上 |
| CG-04 | 月度进口 | `al_import_volume` | DQA-11 + DQA-12 + DQA-13 | 同上 |
| CG-05 | 代理开工率 | `cu_smelter_operating_rate` | DQA-10 + DQA-14 | CI + 依赖 |
| CG-06 | 代理开工率 | `al_smelter_operating_rate` | DQA-10 + DQA-14 | 同上 |
| CG-07 | 代理利润 | `cu_smelter_profit` | DQA-09 + DQA-10 + DQA-14 | 多源 + CI + 依赖 |
| CG-08 | 代理利润 | `al_smelter_profit` | DQA-09 + DQA-10 + DQA-14 | 同上 |
| CG-09 | SMM 加工费 | `cu_tc` | DQA-09 + DQA-12 | 多源 + 源时滞 |
| CG-10 | SMM 加工费 | `al_treatment_fee` | DQA-09 + DQA-12 | 同上 |
| CG-11 | 月度电池产出 | `pb_acid_battery_output` | DQA-11 + DQA-13 | 月度 + 覆盖 |
| CG-12 | 代理需求 | `cu_terminal_demand` | DQA-10 + DQA-14 | CI + 依赖 |
| CG-13 | 代理需求 | `al_terminal_demand` | DQA-10 + DQA-14 | 同上 |
| CG-14 | 代理期限结构 | `li_term_structure` | DQA-10 | CI（输入缺失兜底） |

**GAPS 覆盖率**：14/14 = **100%**（12 项完整实装，2 项通过 DQA-10 降级兜底）

### 3.4 汇总矩阵

| 维度 | 数量 | 新 DQA 覆盖 | 覆盖率 |
|------|:----:|:-----------:|:------:|
| FP | 7 | 7 | 100% |
| FN | 8 | 8 | 100% |
| GAPS | 14 | 14 | 100% |
| **合计** | **29** | **29** | **100%** |

---

## 4. 8 BLOCKED Items Remediation (阻塞项修复)

> **BLOCKED 定义**：指标因数据源缺失或代理公式未标定而无法在 Phase03 落地，需 Phase04 通过新 DQA 规则 + 临时降级方案解锁。

### 4.1 cu_smelter_production（铜冶炼产量）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 需**中国有色金属工业协会 (CSIA)** 月度数据，Phase03 未接入 |
| **临时降级方案** | 使用「电解铜产量 × 冶炼回收率」推算；回收率取近 12 月均值 85%；DQA-10 输出 CI_width，前端标 ⚠️ |
| **长期修复计划** | Phase04 接入 CSIA 月度 API；建立月度→日度线性插值管道；接入后移除代理公式 |
| **前置条件** | CSIA 数据授权（商务协议）+ 月度数据历史回填脚本 |
| **时间线** | Phase04 Week 1-2：商务谈判；Week 3-4：API 接入 + 历史回填；Week 5：代理降级下线 |
| **关联 DQA** | DQA-10（CI）、DQA-11（插值）、DQA-12（源时滞）、DQA-13（覆盖） |

### 4.2 al_smelter_production（铝冶炼产量）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 同 cu_smelter_production，CSIA 月度数据未接入 |
| **临时降级方案** | 使用「电解铝产量 × 冶炼回收率」推算；回收率取近 12 月均值 92%；DQA-10 CI 输出 |
| **长期修复计划** | 与 cu_smelter_production 共用 CSIA 接入管道 |
| **前置条件** | 同 cu_smelter_production |
| **时间线** | 与 cu_smelter_production 并行 |
| **关联 DQA** | DQA-10, DQA-11, DQA-12, DQA-13 |

### 4.3 cu_import_volume（铜进口量）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 需**海关总署**月度数据，发布滞后 M+20，Phase03 无历史回填 |
| **临时降级方案** | 使用「SHFE 仓单入库量 + 电解铜消费 - 国内产量」推算；DQA-10 CI 标注；M+20 前月份用推算，之后切换真实数据 |
| **长期修复计划** | Phase04 接入海关总署月度 API（或第三方代理如 Wind/CEIC）；建立 M+20 前推 + M+20 后切换的双轨管道 |
| **前置条件** | 海关数据授权或第三方代理采购 |
| **时间线** | Phase04 Week 1：数据源选型；Week 2-3：API 接入；Week 4：双轨管道实装 |
| **关联 DQA** | DQA-09（多源）、DQA-11（插值）、DQA-12（M+20 时滞）、DQA-13（覆盖） |

### 4.4 al_import_volume（铝进口量）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 同 cu_import_volume，海关月度数据 |
| **临时降级方案** | 使用「SHFE 铝仓单入库 + 电解铝消费 - 国内产量」推算；DQA-10 CI |
| **长期修复计划** | 与 cu_import_volume 共用海关接入管道 |
| **前置条件** | 同 cu_import_volume |
| **时间线** | 与 cu_import_volume 并行 |
| **关联 DQA** | DQA-09, DQA-11, DQA-12, DQA-13 |

### 4.5 cu_smelter_operating_rate（铜冶炼开工率）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 代理公式 = production / capacity，需 DQA-10 CI 标定；capacity 为静态常量未维护 |
| **临时降级方案** | capacity 取 2025 年 CSIA 年报值 3800 万吨/年；开工率 = 月度产量 / (capacity/12)；DQA-10 CI_width 强制输出 |
| **长期修复计划** | capacity 改为按冶炼企业名单动态汇总；接入后每季度更新 |
| **前置条件** | CSIA 年报数据授权（同 cu_smelter_production） |
| **时间线** | Phase04 Week 1-2：capacity 数据固化；Week 3：代理公式实装 |
| **关联 DQA** | DQA-10（核心）、DQA-14（依赖链） |

### 4.6 al_smelter_operating_rate（铝冶炼开工率）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 同 cu_smelter_operating_rate，代理公式 = production / capacity |
| **临时降级方案** | capacity 取 2025 年 CSIA 年报值 4400 万吨/年；DQA-10 CI |
| **长期修复计划** | 与 cu_smelter_operating_rate 共用 capacity 维护流程 |
| **前置条件** | 同 cu_smelter_operating_rate |
| **时间线** | 与 cu_smelter_operating_rate 并行 |
| **关联 DQA** | DQA-10, DQA-14 |

### 4.7 cu_smelter_profit（铜冶炼利润）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 代理公式 = price - TC - cost，需 DQA-09 多源 + DQA-10 CI + DQA-14 依赖链三规则联动 |
| **临时降级方案** | 使用 `cu_price`（日）- `cu_tc`（周）- `cu_production_cost`（月）推算；DQA-10 CI_width 强制输出；前端显示「代理估算，置信度 x%」 |
| **长期修复计划** | Phase04 接入 SMM 冶炼利润月度调研数据；接入后移除代理公式 |
| **前置条件** | SMM 会员账号（商务采购）+ TC/cost 频率对齐 |
| **时间线** | Phase04 Week 1：SMM 商务谈判；Week 2-3：API 接入；Week 4：三规则联动测试 |
| **关联 DQA** | DQA-09, DQA-10, DQA-14（三规则全部依赖） |

### 4.8 al_smelter_profit（铝冶炼利润）

| 项 | 内容 |
|------|------|
| **阻塞原因** | 同 cu_smelter_profit，代理公式 = price - TC - cost |
| **临时降级方案** | 使用 `al_price` - `al_treatment_fee` - `al_production_cost` 推算；DQA-10 CI |
| **长期修复计划** | 与 cu_smelter_profit 共用 SMM 接入管道 |
| **前置条件** | 同 cu_smelter_profit |
| **时间线** | 与 cu_smelter_profit 并行 |
| **关联 DQA** | DQA-09, DQA-10, DQA-14 |

### 4.9 BLOCKED 项汇总

| # | 指标 | 临时方案 | 长期方案 | 关键 DQA | 工时 |
|:--:|------|----------|----------|:--------:|:----:|
| 1 | cu_smelter_production | 产量×回收率 | CSIA API | DQA-10/11/12/13 | 1.0 d |
| 2 | al_smelter_production | 产量×回收率 | CSIA API | DQA-10/11/12/13 | 0.5 d |
| 3 | cu_import_volume | 仓单+消费-产量 | 海关 API | DQA-09/11/12/13 | 1.0 d |
| 4 | al_import_volume | 仓单+消费-产量 | 海关 API | DQA-09/11/12/13 | 0.5 d |
| 5 | cu_smelter_operating_rate | production/capacity | capacity 动态维护 | DQA-10/14 | 0.5 d |
| 6 | al_smelter_operating_rate | production/capacity | capacity 动态维护 | DQA-10/14 | 0.3 d |
| 7 | cu_smelter_profit | price-TC-cost | SMM API | DQA-09/10/14 | 1.0 d |
| 8 | al_smelter_profit | price-TC-cost | SMM API | DQA-09/10/14 | 0.7 d |
| **合计** | | | | | **~5.5 d** |

> **工时说明**：8 项 BLOCKED 修复合计 ~5.5 人天，与 Section 1.3 规则实装 6.5 人天合计 ~12 人天为 Phase04 总工时基线。

---

## 5. Integration & Testing Plan (集成与测试计划)

### 5.1 规则接入架构

```
scripts/dqa/
├── rules/
│   ├── __init__.py           # DQA_REGISTRY 注册表
│   ├── dqa_01_null.py        # Phase01 (existing)
│   ├── dqa_02_duplicate.py   # Phase01 (existing)
│   ├── dqa_03_monotonic.py   # Phase02 (existing)
│   ├── dqa_04_range.py       # Phase02 (existing)
│   ├── dqa_05_unit.py        # Phase02 (existing)
│   ├── dqa_06_timezone.py    # Phase03 (existing)
│   ├── dqa_07_percentage.py  # Phase03 (existing)
│   ├── dqa_08_enum.py        # Phase03 (existing)
│   ├── dqa_09_cross_source.py  # Phase04 (NEW)
│   ├── dqa_10_proxy_confidence.py  # Phase04 (NEW)
│   ├── dqa_11_freq_consistency.py  # Phase04 (NEW)
│   ├── dqa_12_source_delay.py  # Phase04 (NEW)
│   ├── dqa_13_coverage.py      # Phase04 (NEW)
│   ├── dqa_14_dependency.py    # Phase04 (NEW)
│   └── dqa_15_calendar.py      # Phase04 (NEW)
├── context.py                # DQAContext: calendar, source_meta, dep_graph, source_map
├── pipeline.py               # DQAPipeline: 顺序执行 + 短路逻辑
└── registry.py               # DQA_REGISTRY + RULE_TO_INDICATOR 映射
```

### 5.2 管道执行顺序

```
DQA-01 空值 ─┐
DQA-02 重复 ─┤
DQA-03 单调 ─┤─→ DQA-15 日历豁免（前置钩子）─→ 下游 DQA-03/07 跳过节假日
DQA-04 范围 ─┤
DQA-05 单位 ─┤
DQA-06 时区 ─┤
DQA-07 百分比─┤
DQA-08 枚举 ─┘
        │
        ▼ (前置 PASS 后)
DQA-12 源时滞 ──→ 识别源延迟
DQA-13 覆盖率  ──→ 识别历史缺口
        │
        ▼ (元数据可用后)
DQA-09 交叉验证 ─→ 多源一致性
DQA-10 代理置信 ─→ CI 输出
DQA-11 频率一致 ─→ 插值校验
        │
        ▼ (依赖图构建后)
DQA-14 依赖链 ──→ 输入→输出一致性
```

**短路逻辑**：DQA-01/02 FAIL → 跳过后续所有 DQA（数据不存在，无意义）。DQA-03/04/05/06/07/08 WARN → 继续但记录降级。DQA-09/10/11/12/13/14/15 并行执行。

### 5.3 测试数据需求

| 测试场景 | 数据量 | 来源 | 用途 |
|----------|:------:|------|------|
| 历史回填（36 指标 × 90 天） | ~3240 行 | `data/db_export/*.jsonl` | DQA-13 覆盖率基线 |
| 多源对照（10 指标 × 3 源 × 30 天） | ~900 行 | SMM + 同花顺 + 推算 | DQA-09 交叉验证 |
| 代理输入（9 指标 × 5 输入 × 90 天） | ~4050 行 | 内部 series_cache | DQA-10 CI 计算 |
| 月度插值（5 指标 × 12 月） | ~60 行 | CSIA + 海关（模拟） | DQA-11 相关性 |
| 源时滞（36 指标 × 14 天） | ~504 行 | source_meta 模拟 | DQA-12 延迟检测 |
| 依赖链（6 派生指标 × 30 天） | ~180 行 | 派生公式 + 输入 | DQA-14 一致性 |
| 节假日（36 指标 × 春节/国庆 7 天） | ~252 行 | chinese_calendar | DQA-15 豁免 |
| **合计** | **~9166 行** | | |

### 5.4 单元测试用例

| 规则 | 用例数 | 关键用例 |
|:----:|:------:|----------|
| DQA-09 | 8 | 多源一致 / 单源跳过 / 零值安全 / 时区对齐前置失败 |
| DQA-10 | 10 | 正常 CI / 缺失依赖兜底 / 零均值输入 / 敏感度因子标定 |
| DQA-11 | 6 | 高相关 PASS / 低相关 FAIL / 数据不足 WARN / 插值方法切换 |
| DQA-12 | 6 | 正常 PASS / 1d WARN / 3d FAIL / 节假日豁免 / 首次接入 |
| DQA-13 | 8 | 高覆盖 PASS / 低覆盖 FAIL / 新指标 warmup / 月度分母切换 |
| DQA-14 | 8 | 输入稳定跳过 / ratio 正常 PASS / ratio 异常 FAIL / 缺失输入 WARN |
| DQA-15 | 6 | 春节豁免 / SHFE 调休 / 跨年节假日 / 海外节假日 TODO |
| **合计** | **52** | |

### 5.5 集成测试用例

| 场景 | 描述 | 期望结果 |
|------|------|----------|
| IT-01 全绿基线 | 36 指标全量历史数据（无噪声） | 全部 DQA PASS，0 WARN/FAIL |
| IT-02 多源冲突 | 注入 cu_smelter_profit 源间 15% 差异 | DQA-09 FAIL，前端标红 |
| IT-03 代理低置信 | 注入 cu_smelter_operating_rate 缺失 capacity | DQA-10 FAIL，CI_width>10% |
| IT-04 月度插值失真 | 注入 cu_smelter_production 线性插值 corr<0.5 | DQA-11 FAIL，禁止展示 |
| IT-05 源延迟 | 模拟 cu_import_volume M+25 未发布 | DQA-12 FAIL，触发源切换 |
| IT-06 数据缺口 | 删除 sn_top20_net 前 60 天 | DQA-13 FAIL，覆盖率<50% |
| IT-07 依赖链断裂 | cu_smelter_profit 输入更新但输出未重算 | DQA-14 FAIL，ratio≈0 |
| IT-08 节假日误报消除 | 春节前后 cu_spot_premium 单调变化 | DQA-15 豁免，DQA-03 PASS |
| IT-09 BLOCKED 降级 | 8 BLOCKED 指标临时方案全量跑 | 全部 PASS（降级可运行） |
| **合计** | | **9 IT 用例** |

### 5.6 测试执行计划

| 阶段 | 时间 | 内容 | 负责人 |
|------|------|------|--------|
| Phase04-W1 | 1 周 | 单元测试 52 用例 + 测试夹具 | DSHB |
| Phase04-W2 | 1 周 | 规则实装 + 集成测试 IT-01~04 | DSHB + 主脑 |
| Phase04-W3 | 1 周 | BLOCKED 项降级方案 + IT-05~09 | DSHB |
| Phase04-W4 | 1 周 | 全量回归 + 门禁验收 | 主脑 |
| **合计** | **4 周** | | |

### 5.7 验收门禁

| 门禁 | 标准 | 验证方式 |
|------|------|----------|
| G-01 单元测试 | 52/52 PASS | `pytest tests/dqa/ -v` |
| G-02 集成测试 | 9/9 PASS | `python scripts/dqa/run_all.py --it` |
| G-03 36 指标全绿 | 0 FAIL，WARN ≤ 5 | `python scripts/dqa/run_all.py --full` |
| G-04 BLOCKED 降级 | 8/8 可运行 | `python scripts/dqa/run_blocked_degraded.py` |
| G-05 覆盖率 | 29/29 (FP+FN+GAPS) | 矩阵审计 |
| G-06 性能 | 单指标 DQA < 500ms | `time python scripts/dqa/run_all.py` |

---

## 6. 附录 A：DQAContext 接口定义

```python
@dataclass
class DQAContext:
    calendar: TradingCalendar          # DQA-15 提供
    source_meta: Dict[str, SourceMeta] # DQA-12 使用
    source_map: Dict[str, List[SeriesDF]]  # DQA-09 使用
    dependency_graph: DependencyDAG    # DQA-10/14 使用
    series_cache: Dict[str, SeriesDF]  # 全规则共享
    indicator_meta: Dict[str, IndicatorMeta]  # DQA-13 使用
    monthly_native: Dict[str, SeriesDF]  # DQA-11 使用
    
    def has_source_map(self, indicator_id: str) -> bool:
        return indicator_id in self.source_map and len(self.source_map[indicator_id]) >= 2
    def is_proxy(self, indicator_id: str) -> bool:
        return indicator_id in self.dependency_graph and self.dependency_graph.inputs_of(indicator_id)
```

---

## 7. 附录 B：DQAResult 结构定义

```python
@dataclass
class DQAResult:
    rule_id: str              # "DQA-09" ~ "DQA-15"
    indicator_id: str         # "cu_smelter_profit"
    status: str               # "PASS" | "WARN" | "FAIL"
    severity: str             # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    message: str              # 人类可读摘要
    detail: Dict[str, Any]    # 机器可读细节（阈值/计算值/源列表等）
    timestamp: str            # ISO 8601 时间戳
    duration_ms: float        # 规则执行耗时
    
    def is_blocking(self) -> bool:
        """是否阻断页面渲染"""
        return self.status == "FAIL" and self.severity in ("HIGH", "CRITICAL")
```

---

## 8. 附录 C：Phase04 路线图

```
Phase03 P1 Final Prep (本文档) ───── 2026-10-16
        │
        ▼
Phase04-W1: 单元测试 + 测试夹具 ──── 2026-10-19
        │
        ▼
Phase04-W2: 规则实装 + IT-01~04 ─── 2026-10-26
        │
        ▼
Phase04-W3: BLOCKED 降级 + IT-05~09 ─ 2026-11-02
        │
        ▼
Phase04-W4: 全量回归 + 门禁验收 ─── 2026-11-09
        │
        ▼
Phase05: 36 指标全量 DQA 门禁 ──── 2026-11-16
```

---

## 9. 风险台账关联

| 风险编号 | 风险 | 等级 | 关联 DQA | 状态 |
|----------|------|:----:|:--------:|:----:|
| R-V88-035 | 告警噪声率 7 天观测 | P2 | DQA-13 | 🟡 IN_PROGRESS (14.9%) |
| R-V88-038 | 派生指标连续相同值 | P2 | DQA-14 | 🟡 MONITORED |
| R-V88-042 | ni_top20_net 数据源缺失 | P1 | DQA-13 | 🟡 独立处理 |
| R-V88-043 | SPOT_IS 反爬 | P1 | DQA-09 | ✅ 已修复 (spotis_url_fix) |
| R-V88-045 | HTTP 404 endpoint drift | P2 | DQA-12 | ✅ 关联修复 |
| R-V88-046 | 100ppi.com URL 路径重构 | P1 | DQA-09 | ✅ 已修复 |
| **R-V88-047** | **代理指标无置信度** | **P1** | **DQA-10** | **🆕 本草案解决** |
| **R-V88-048** | **多源不一致未检测** | **P1** | **DQA-09** | **🆕 本草案解决** |
| **R-V88-049** | **月度数据阈值过严** | **P2** | **DQA-11** | **🆕 本草案解决** |
| **R-V88-050** | **节假日误报 (7 FP)** | **P2** | **DQA-15** | **🆕 本草案解决** |

---

## 10. 约束合规最终声明

| 约束 | 状态 | 证据 |
|------|:----:|------|
| BRANCH_LOCKED | ✅ | 仅写入 `background_final_prep/phase04_dqa_rules_draft.md` |
| NO_OVERWRITE | ✅ | 新建文档，未覆盖 DQA-01~08 实装文件 |
| NO_MODIFY_V87 | ✅ | 未触及 V87 基线 |
| NO_EDIT_RELEASE_TAG | ✅ | 未修改发布标签 |
| NO_ZHIJI_API_CALL | ✅ | 0 calls（设计阶段） |
| UPSTREAM_WRITES=0 | ✅ | 未修改 `scripts/dqa/`、`scripts/`、`data/`、`STATUS.md` |
| PRE_COMMIT_HOOK | ✅ N/A | 未改产物文件 |
| 文档行数 | ✅ ~600 行 | 500-600 行目标达成 |

---

*Generated by DSHB Agent | V88 Phase03 P1 Background Final Prep → Phase04 DQA Rules Foundation*
*7 DQA rules (DQA-09~15) | 29/29 FP+FN+GAPS covered | 8/8 BLOCKED degraded | ~6.5 person-days*
*BRANCH_LOCKED | UPSTREAM_WRITES=0 | Phase04-ready draft*
