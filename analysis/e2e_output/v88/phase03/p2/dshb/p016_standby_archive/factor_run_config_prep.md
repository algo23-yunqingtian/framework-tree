# DSHB P0-16 — First Batch Factor Execution Entry Config (Config Only, Not Executed)

**TASK_ID**: V88_PHASE03_P6_DSHB_P016_FACTOR_COMPUTE_STANDBY
**TASK**: T3 — 第一批因子执行入口预配置（仅配置、不执行）
**AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
**GENERATED**: 2026-10-22
**STATUS**: COMPLETE (config prepared, no computation executed)

---

## 1. Overview

This document defines the **execution entry configuration** for the first batch of factor calculations covering varieties PB, ZN, and Recycle-PB. **This is CONFIGURATION ONLY** — no factor calculation has been or will be executed until the dual-key trigger is activated.

**Critical**: The execution entry is **LOCKED**. Only the trigger pipeline (wind_online_watcher.py → ic_ir_calc_skeleton.py) can unlock and invoke it. Manual invocation is prohibited.

---

## 2. First Batch Configuration

### 2.1 Varieties (品种列表)

| # | Variety | Symbol | Chinese | Category | Factor Candidates |
|:-:|---------|:------:|:-------:|:--------:|:------------------:|
| 1 | 铅 | PB | 铅 | Base metal | momentum, mean_reversion, volatility |
| 2 | 锌 | ZN | 锌 | Base metal | momentum, carry, term_structure |
| 3 | 再生铅 | Recycle-PB | 再生铅 | Recycled metal | momentum, policy_impact, scrap_premium |

### 2.2 Time Range (时间区间)

```yaml
date_range:
  start: "2025-01-01"       # T-1 year (lookback start)
  end: "2026-10-22"         # Current date (lookback end)
  lookback_days: 365
  forward_horizon_days: 20  # 20 trading days forward return
  data_frequency: "daily"
  timezone: "Asia/Shanghai"
```

### 2.3 Factor Definitions

#### Factor 1: Momentum 20D (momentum_20d)

```yaml
factor_id: momentum_20d
factor_name: "20-Day Momentum"
category: "momentum"
definition:
  formula: "(close[t] - close[t-20]) / close[t-20]"
  lookback_days: 20
  forward_horizon_days: 20
  universe_filter: "active contracts, liquidity > 10M USD/day"
  neutralization: "industry"
  winsorization: "percentile 1%-99%"
data_source:
  price_field: "close"
  adjusted: true
  source: "WIND_DATA_LINK (via gateway only)"
expected_quality:
  min_ic_mean: 0.03
  min_t_statistic: 1.5
  min_sample_size: 200
```

#### Factor 2: Momentum 60D (momentum_60d)

```yaml
factor_id: momentum_60d
factor_name: "60-Day Momentum"
category: "momentum"
definition:
  formula: "(close[t] - close[t-60]) / close[t-60]"
  lookback_days: 60
  forward_horizon_days: 20
  universe_filter: "active contracts, liquidity > 10M USD/day"
  neutralization: "industry"
  winsorization: "percentile 1%-99%"
data_source:
  price_field: "close"
  adjusted: true
  source: "WIND_DATA_LINK (via gateway only)"
expected_quality:
  min_ic_mean: 0.02
  min_t_statistic: 1.5
  min_sample_size: 200
```

#### Factor 3: Realized Volatility 20D (vol_20d)

```yaml
factor_id: vol_20d
factor_name: "20-Day Realized Volatility"
category: "volatility"
definition:
  formula: "std(returns[t-20:t]) * sqrt(252)"
  lookback_days: 20
  forward_horizon_days: 20
  universe_filter: "active contracts"
  neutralization: "none"
  winsorization: "percentile 5%-95%"
data_source:
  price_field: "close"
  adjusted: true
  source: "WIND_DATA_LINK (via gateway only)"
expected_quality:
  min_ic_mean: 0.01
  min_t_statistic: 1.2
  min_sample_size: 200
```

---

## 3. Execution Entry Configuration

### 3.1 Entry Point Specification

```yaml
execution_entry:
  script: "factor_workspace/pb_zn_recyclepb_v1/ic_ir_calc_skeleton.py"
  entry_function: "run_calc()"
  invoked_by: "wind_online_watcher.py"
  invocation_mode: "subprocess (child process)"
  invocation_timeout: 300  # seconds
  invocation_args:
    --factor-id: "momentum_20d"
    --variety: "PB"  # Default, configurable per batch
    --date-start: "2025-01-01"
    --date-end: "2026-10-22"
```

### 3.2 Batch Execution Order

```yaml
batch_order:
  - factor_id: "momentum_20d"
    varieties: ["PB", "ZN", "Recycle-PB"]
    description: "20-day momentum for all 3 varieties"
  - factor_id: "momentum_60d"
    varieties: ["PB", "ZN", "Recycle-PB"]
    description: "60-day momentum for all 3 varieties"
  - factor_id: "vol_20d"
    varieties: ["PB", "ZN", "Recycle-PB"]
    description: "20-day realized volatility for all 3 varieties"

total_factors: 9  # 3 factors x 3 varieties
estimated_duration: "~45s per factor (with real data)"
estimated_total: "~6-7 minutes for first batch"
```

### 3.3 Output File Naming Convention

```
factor_workspace/pb_zn_recyclepb_v1/output/
├── ic_result_momentum_20d_PB.json
├── ic_result_momentum_20d_PB.json.checksum
├── ic_result_momentum_20d_ZN.json
├── ic_result_momentum_20d_ZN.json.checksum
├── ic_result_momentum_20d_Recycle-PB.json
├── ic_result_momentum_20d_Recycle-PB.json.checksum
├── ic_result_momentum_60d_PB.json
├── ... (similar pattern for all 9 factors)
├── ir_result_momentum_20d_PB.json
├── ir_result_momentum_20d_PB.json.checksum
├── ... (similar pattern)
├── factor_meta_momentum_20d.json
├── factor_meta_momentum_20d.json.checksum
├── ... (similar pattern)

checksum/
└── batch_v1_dual_checksum_manifest.json  # Aggregate checksum for entire batch
```

---

## 4. Lock Mechanism

### 4.1 Execution Lock Status

| Lock | Type | Status | Bypass |
|------|------|:------:|:------:|
| Dual-key trigger | File flag | 🔒 LOCKED | Only both flags unlock |
| Skeleton `run_calc()` gate | Runtime check | 🔒 LOCKED | Checks both flags at runtime |
| Precheck validation | Runtime check | 🔒 LOCKED | Must pass before calc |
| Manual CLI invocation | Allowed but gated | 🔒 LOCKED | Will abort if no dual-key |

### 4.2 Lock Verification

```
$ python factor_workspace/pb_zn_recyclepb_v1/ic_ir_calc_skeleton.py --check-trigger
⛔ TRIGGER INACTIVE: WIND_DATA_LINK_ONLINE.flag NOT FOUND
   Factor calculation PROHIBITED. No data source confirmed.
   Awaiting external placement of WIND_DATA_LINK_ONLINE.flag.
```

**✅ VERIFIED**: Manual invocation returns `ABORTED` when dual-key is not present.

---

## 5. Configuration File (Config Only — NOT Executed)

The following configuration has been prepared for the first batch. It will be used by the trigger pipeline once both keys are present.

```python
# factor_run_config_v1.py — PREPARATION ONLY, NOT EXECUTED
# This file is a CONFIGURATION REFERENCE, not executable code.
# It defines what WILL be computed when dual-key trigger fires.

FIRST_BATCH_CONFIG = {
    'batch_id': 'v88_first_batch_p016',
    'status': 'PREPARED_NOT_EXECUTED',
    'trigger_required': ['WIND_DATA_LINK_ONLINE.flag', 'HERMES_TRIGGER_AUTHORIZED.flag'],
    'trigger_mode': 'DUAL_KEY_ONLY',
    'varieties': ['PB', 'ZN', 'Recycle-PB'],
    'factors': [
        {'id': 'momentum_20d', 'name': '20-Day Momentum', 'category': 'momentum'},
        {'id': 'momentum_60d', 'name': '60-Day Momentum', 'category': 'momentum'},
        {'id': 'vol_20d', 'name': '20-Day Realized Volatility', 'category': 'volatility'},
    ],
    'date_range': {
        'start': '2025-01-01',
        'end': '2026-10-22',
        'lookback_days': 365,
        'forward_horizon_days': 20,
    },
    'data_source': 'WIND_DATA_LINK (via approved gateway only)',
    'output_dir': 'factor_workspace/pb_zn_recyclepb_v1/output/',
    'output_standard': 'v88-factor-output-v2.0',
    'checksum': 'MD5+SHA256 dual per file',
    'estimated_duration_seconds': 420,  # ~7 minutes
    'execution_allowed': False,
    'execution_note': 'This config is PREPARATION ONLY. '
                      'No computation will occur until dual-key trigger activates.',
}
```

---

## 6. Pre-Flight Checklist (For When Keys Arrive)

When both trigger flags are placed, the following checks will automatically execute:

| # | Check | Automated? | Must Pass |
|:-:|-------|:----------:|:---------:|
| 1 | Key A (WIND_DATA_LINK_ONLINE.flag) present | ✅ Yes | Required |
| 2 | Key B (HERMES_TRIGGER_AUTHORIZED.flag) present | ✅ Yes | Required |
| 3 | Both flags non-empty, valid size | ✅ Yes | Required |
| 4 | Factor skeleton exists and valid | ✅ Yes | Required |
| 5 | Workspace directories exist | ✅ Yes | Required |
| 6 | No WindPy in skeleton | ✅ Yes | Required |
| 7 | No auto-push in skeleton | ✅ Yes | Required |
| 8 | Data ingestion pipeline ready | ❌ Manual | Required |
| 9 | Wind API gateway authorized | ❌ Manual | Required |
| 10 | Output dir writable | ✅ Yes | Required |
| 11 | Checksum generation enabled | ✅ Yes | Required |
| 12 | Audit log dir writable | ✅ Yes | Required |

---

## 7. Conclusion

**First batch factor execution entry is CONFIGURED AND LOCKED.**

- 3 factors x 3 varieties = 9 factor calculations prepared
- Date range: 2025-01-01 to 2026-10-22
- Output standard: v88-factor-output-v2.0 (MD5+SHA256 dual checksum)
- Execution status: **LOCKED — awaiting dual-key trigger**
- Manual invocation: **PROHIBITED** (will abort)
- Estimated duration: ~7 minutes (when keys arrive)

**No factor calculation has been executed.** No data has been pulled. No Wind API calls have been made.

---

*Generated by DSHB Agent | V88 Phase03 P6 P0-16 Factor Compute Standby*
*T3 COMPLETE | 9 factors configured (3x3) | LOCKED | No execution | Awaiting dual-key*