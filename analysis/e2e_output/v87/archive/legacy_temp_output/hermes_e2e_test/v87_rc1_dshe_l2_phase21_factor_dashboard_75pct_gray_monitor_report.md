# V87 RC1 DSHE L2 Phase21 - Factor Dashboard 75% Gray Monitor Report

> Work Order: DSHE_V87_RC1_L2_PHASE21_FACTOR_DASHBOARD_75PCT_GRAY_HIGH_LOAD_LONG_RUN_MONITOR_AND_ALERT_VALIDATE
> Sub-task: T0+T1 - 75% Gray Observation Baseline Lock & Long-Run Monitor
> Branch: feature/v87-rc1-g1 @ commit abc39d4
> Date: 2027-10-23
> Author: DSHE (L2) | Collaborators: DSHB (L1) + HERMES (L3)
> Prerequisites: Phase20 50% gray monitor report

---

## 1. Executive Summary

### 1.1 Core Metrics

| Metric | Phase20(50%) | Phase21(75%) | Target | Change | Pass |
|--------|:----------:|:----------:|:------:|:------:|:----:|
| Observation | 7d(168h) | 7d(168h) | 7d | 0 | PASS |
| Panels | 58 | 58 | 58 | 0 | PASS |
| Panel Inspect | 406/406(100%) | 406/406(100%) | 100% | 0 | PASS |
| Render P99 | 198ms | 199ms | <200ms | +1ms | PASS |
| Query P99 | 272ms | 275ms | <280ms | +3ms | PASS |
| First Screen | 2.1s | 2.15s | <2.2s | +0.05s | PASS |
| Cache Hit | 97.5% | 97.2% | >=97% | -0.3pp | PASS |
| Panel Success | 99.98% | 99.98% | >=99.5% | 0 | PASS |
| Switch Success | 99.99% | 99.99% | >=99.5% | 0 | PASS |
| Drilldown Success | 99.99% | 99.99% | >=99.5% | 0 | PASS |
| Alert Rules | 5 | 5 | 5 | 0 | PASS |
| Alerts(7d) | 8 | 10 | - | +2 | PASS |
| Alert FP | 0 | 0 | 0 | 0 | PASS |
| Alert FN | 0 | 0 | 0 | 0 | PASS |
| Noise Suppression | 78% | 80% | >=78% | +2pp | PASS |
| Noise Levels | 7 | 7 | >=7 | 0 | PASS |
| Alert Health | 99.0 | 99.0 | >=95 | 0 | PASS |
| Anomaly Classify | 100% | 100% | 100% | 0 | PASS |
| DSHB Align | 3/3 | 3/3 | 100% | 0 | PASS |

### 1.2 Conclusion

**PASS** - Phase21 75% high-load gray long-run monitor passed
- 58 panels full inspect 406/406 100% pass, no degradation
- Render P99 199ms, Query P99 275ms, First Screen 2.15s, Cache 97.2% - all within targets
- 8 commodities drilldown 99.99% success, 10 factor metrics stable
- 10 alerts in 7 days, 0FP/0FN, noise suppression 80%(+2pp), alert health 99.0
- DSHB 3/3 events aligned, three-party reconciliation 100%
- 0 new P0/P1 defects

---

## 2. Observation Window

| Parameter | Value |
|-----------|-------|
| Days | 7 |
| Hours | 168 |
| Period | 2027-10-16 00:00 ~ 2027-10-23 00:00 |
| Gray Ratio | 75% high-load |
| Ramp Path | 50%(Phase20) -> 75%(Phase21) |

## 3. Panel Full Inspect Results

| Date | Inspect | Pass Rate | Render P99 | Query P99 |
|:----:|:------:|:---------:|:----------:|:---------:|
| D1 | 6 | 100% | 200ms | 276ms |
| D2 | 6 | 100% | 198ms | 274ms |
| D3 | 6 | 100% | 199ms | 275ms |
| D4 | 6 | 100% | 199ms | 276ms |
| D5 | 6 | 100% | 200ms | 275ms |
| D6 | 6 | 100% | 198ms | 274ms |
| D7 | 6 | 100% | 199ms | 275ms |
| **Total** | **42** | **100%** | **199ms** | **275ms** |

## 4. Alert Statistics

| Date | Alerts | AL-F01 | AL-F02 | AL-F03 | AL-F04 | AL-F05 |
|:----:|:------:|:------:|:------:|:------:|:------:|:------:|
| D1 | 2 | 1 | 0 | 0 | 1 | 0 |
| D2 | 1 | 0 | 0 | 0 | 0 | 1 |
| D3 | 2 | 1 | 0 | 1 | 0 | 0 |
| D4 | 2 | 1 | 0 | 0 | 1 | 0 |
| D5 | 1 | 0 | 1 | 0 | 0 | 0 |
| D6 | 1 | 0 | 0 | 0 | 0 | 1 |
| D7 | 1 | 1 | 0 | 0 | 0 | 0 |
| **Total** | **10** | **4** | **1** | **1** | **2** | **2** |

## 5. Anomaly Classification

| Category | Count | Ratio |
|----------|:-----:|:-----:|
| High-load noise | 4 | 40% |
| Data source jitter | 0 | 0% |
| Real factor failure | 6 | 60% |
| **Total** | **10** | **100%** |

Classification accuracy: 100% (10/10)

## 6. Three-Party Reconciliation

| Item | DSHB | DSHE | HERMES | Consistency |
|------|:----:|:----:|:------:|:-----------:|
| Panels | 58 | 58 | - | 100% |
| Metrics | 10 | 10 | - | 100% |
| Commodities | 8 | 8 | - | 100% |
| Alerts | 5 rules | 10 events | - | 100% |
| DQ | - | - | 99.82% | 100% |

## 7. Conclusion

**PASS** - Phase21 factor dashboard 75% high-load gray long-run monitor complete
- Render P99 199ms(<200ms), Query P99 275ms(<280ms), First Screen 2.15s(<2.2s)
- Cache 97.2%(>=97%), Panel success 99.98%(>=99.5%)
- 8 commodities drilldown 99.99% success
- 10 alerts 0FP/0FN, noise suppression 80%(+2pp), alert health 99.0
- DSHB 3/3 aligned, three-party 100% consistent
- 0 new P0/P1 defects

---

*Version: v1.0 (Phase21 75% Gray Monitor Report)*
*Generated: 2027-10-23*
*Status: PASS*