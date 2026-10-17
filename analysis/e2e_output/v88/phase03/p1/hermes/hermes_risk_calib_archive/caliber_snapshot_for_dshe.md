# 9 项指标官方口径快照 (Caliber Snapshot for DSHE+DSHB)

> **TASK_ID**: V88_PHASE03_P7_HERMESHF_P6_RISK_FIX_AND_CALIB_SNAPSHOT_JOB / T1
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **快照时刻**: 2026-10-17T14:15 +0800
> **分发对象**: DSHB + DSHE（双向口径对齐用）
> **前置背景**: DSHB P019 `partial_indicator_cross_check.md` 明确记录"HERMEShf 快照未收到用现有口径源"，本快照填补该缺口

---

## 1. 9 因子矩阵定义

> **来源**：`analysis/e2e_output/v88/phase03/p2/dshb/p016_standby_archive/factor_run_config_prep.md` (DSHB T3)
> **公式**：3 因子 × 3 品种 = 9 个因子计算单元
> **状态**：LOCKED（配置已冻结，未执行计算，等待双钥匙激活）

### 1.1 三因子定义

| # | factor_id | 因子名 | category | 公式 | lookback | forward | 中性化 | 缩尾 |
|:-:|-----------|--------|----------|------|:--------:|:-------:|:------:|:----:|
| F1 | `momentum_20d` | 20日动量 | momentum | `(close[t] - close[t-20]) / close[t-20]` | 20d | 20d | industry | 1%-99% |
| F2 | `momentum_60d` | 60日动量 | momentum | `(close[t] - close[t-60]) / close[t-60]` | 60d | 20d | industry | 1%-99% |
| F3 | `vol_20d` | 20日实现波动率 | volatility | `std(returns[t-20:t]) * sqrt(252)` | 20d | 20d | none | 5%-95% |

### 1.2 三品种定义

| # | 品种中文名 | 品种代码 | 类别 | 因子套 |
|:-:|-----------|:--------:|------|--------|
| V1 | 铅 | PB | 基础金属 | momentum, mean_reversion, volatility |
| V2 | 锌 | ZN | 基础金属 | momentum, carry, term_structure |
| V3 | 再生铅 | Recycle-PB | 再生金属 | momentum, policy_impact, scrap_premium |

### 1.3 9 因子完整矩阵

| # | 因子ID | 品种 | 数据字段 | 调整类型 | 数据源 | 预期质量 |
|:-:|--------|:----:|:--------:|:--------:|--------|----------|
| 1 | momentum_20d | PB | close | 后复权 | WIND_DATA_LINK | IC≥0.03, t≥1.5, N≥200 |
| 2 | momentum_20d | ZN | close | 后复权 | WIND_DATA_LINK | IC≥0.03, t≥1.5, N≥200 |
| 3 | momentum_20d | Recycle-PB | close | 后复权 | WIND_DATA_LINK | IC≥0.03, t≥1.5, N≥200 |
| 4 | momentum_60d | PB | close | 后复权 | WIND_DATA_LINK | IC≥0.02, t≥1.5, N≥200 |
| 5 | momentum_60d | ZN | close | 后复权 | WIND_DATA_LINK | IC≥0.02, t≥1.5, N≥200 |
| 6 | momentum_60d | Recycle-PB | close | 后复权 | WIND_DATA_LINK | IC≥0.02, t≥1.5, N≥200 |
| 7 | vol_20d | PB | close | 后复权 | WIND_DATA_LINK | IC≥0.01, t≥1.2, N≥200 |
| 8 | vol_20d | ZN | close | 后复权 | WIND_DATA_LINK | IC≥0.01, t≥1.2, N≥200 |
| 9 | vol_20d | Recycle-PB | close | 后复权 | WIND_DATA_LINK | IC≥0.01, t≥1.2, N≥200 |

---

## 2. 口径元数据固化

### 2.1 数据口径

| 维度 | 口径值 | 说明 |
|------|--------|------|
| price_field | `close` | 收盘价 |
| adjusted | `true` | 后复权 |
| data_source | `WIND_DATA_LINK (via gateway only)` | 仅通过 Wind 网关获取 |
| universe_filter | `active contracts, liquidity > 10M USD/day` | 活跃合约+流动性过滤 |
| date_start | 2025-01-01 | 回测起始 |
| date_end | 2026-10-22 | 回测截止 |
| min_sample_size | 200 | 最小样本量 |

### 2.2 统计口径

| 口径 | 定义 | 当前值 | 阈值 |
|------|------|:------:|:----:|
| DSHB DB层映射命中率 | phase03_test.db 中 indicator_id_mapped 非空数 / meta_chart 总指标数 | 84/109 = 77.06% | ≥60% |
| 引擎侧 D7 真实渲染覆盖率 | 引擎实际获取 source='real' 数据图表数 / 总图表数 | 0/101 = 0.00% | ≥60% |
| 图表口径（Chart Caliber） | 以图表为统计单位 | 88张（63 matchable + 25 pending_data） | — |
| 指标口径（Indicator Caliber） | 以指标为统计单位 | 123 matched + 24 partial + 0 missing | — |

> **口径差异说明**：DSHB DB层映射命中率 PASS(77.06%)，引擎侧 D7 渲染覆盖率 FAIL(0%)——根因是引擎数据源路径硬编码到 `scripts/api_cache.db`，无法读取 DSHB 的 `phase03_test.db`。此差异为已知问题，不影响因子计算口径（因子计算使用 close price series，通过 Wind 网关获取）。

---

## 3. 品种映射固化

| DSHB indicator_id | DSHE meta_chart indicator_id | 品种 | 数据状态 |
|-------------------|-----------------------------|:----:|:--------:|
| pb_21_close_front | PB_FU00014950 | PB | ✅ base price |
| zn_21_close_front | ZN_FU00014950 | ZN | ✅ base price |
| recycle_pb_21_close | RECYCLEPB_FU00014950 | Recycle-PB | ✅ base price |

> **映射说明**：9 因子所需指标均为 close price series（基础价格数据），**不在 P019 的 24-partial 清单中**。P019 已确认"9 因子所需指标属于基础价格数据，不受 partial 状态影响"。

---

## 4. 与 P019 交叉核对一致性

> **来源**：`analysis/e2e_output/v88/phase03/p2/dshb/p019_calib_archive/partial_indicator_cross_check.md`

| 核对项 | P019 结论 | 本快照 | 一致性 |
|--------|-----------|--------|:------:|
| 9 因子配置 | 3x3 LOCKED | 3x3 LOCKED | ✅ |
| 品种列表 | PB, ZN, Recycle-PB | PB, ZN, Recycle-PB | ✅ |
| 因子列表 | momentum_20d, momentum_60d, vol_20d | 同左 | ✅ |
| 数据源 | WIND_DATA_LINK (via gateway) | WIND_DATA_LINK (via gateway) | ✅ |
| 执行状态 | not executed | LOCKED | ✅ |
| 24-partial 关联 | 0/24（9 因子不依赖 partial 指标） | 确认 | ✅ |

---

## 5. 双向分发指令

### 5.1 → DSHE

DSHE 应使用本快照中 §1 的 9 因子矩阵定义和 §2 的口径元数据，校验因子运行时监控规则（`gate_rules/factor_runtime_rules_v1.yaml`）中的指标是否与本快照一致。如有偏差，DSHE 需更新规则并提交。

### 5.2 → DSHB

DSHB 应使用本快照中 §3 的品种映射，校验 `factor_run_config_prep.md` 中的品种-指标映射是否与本快照一致。P019 已用"现有口径源"完成 24-partial 交叉核对（24/24 PASS），本快照补齐了 DSHB 等待的 HERMEShf 口径源。

---

## 6. 口径快照结论

| 项 | 值 |
|----|---|
| 9 因子定义 | ✅ 完整固化 |
| 品种映射 | ✅ 3 品种 9 因子 |
| 口径元数据 | ✅ close + 后复权 + WIND_DATA_LINK |
| 与 P019 一致性 | ✅ 6/6 对齐 |
| 执行状态 | LOCKED（等待双钥匙） |
| 双向分发 | ✅ DSHE + DSHB |

**STATUS**: CALIBER_SNAPSHOT_GENERATED_DISTRIBUTED_TO_DSHB_DSHE

*Generated: 2026-10-17T14:15 +0800 | HERMEShf | V88 Phase03 P7 T1*
