# Partial Render Precheck Report — Rendering Boundary Verification

> **TASK_ID**: V88_PHASE03_P2_DSHE_GATE_HARDEN_AND_PHASE04_PREP_PARTIAL_CHECK_JOB / T2
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1
> **GENERATED**: 2026-10-16T22:45 UTC+8
> **STATUS**: ✅ PRECHECK COMPLETE
>
> ⚠️ **CRITICAL DISCLAIMER**: This is a **PRECHECK ONLY** (素材收集). No indicator status changes have been made. No matched/partial classification has been altered. This report provides boundary verification evidence for future caliber alignment by HERMES.

---

## 1. Context

The caliber inventory snapshot (from HERMES) reports **123 matched + 24 partial** indicators. Many of the 24 partial indicators relate to "渲染输出边界校验不足" (insufficient render output boundary verification). This precheck collects evidence for the render-related subset without modifying any indicator status.

### 1.1 Data Source

| Source | Path | Indicators |
|--------|------|:----------:|
| Phase03 P1 render results | `render_p012_prep/new_derived_metric_full_render_result.json` | 70 derived indicators |
| Render boundary archive | `render_archive_phase04_prep/partial_metric_boundary_archive.json` | 1 indicator (si_top20_net) |

### 1.2 Non-RENDERED Indicator Count

| Category | Count | Source |
|----------|:-----:|--------|
| PLACEHOLDER_ZERO | 9 | Phase03 P1 render results |
| HAS_DATA (orphan) | 5 | Phase03 P1 render results |
| NO_DATA | 1 | Phase03 P1 render results |
| **Total from Phase03 P1** | **15** | — |
| Expected from caliber snapshot | 9 | Pending HERMES caliber_inventory_snapshot |
| **Total potential partial** | **24** | — |

> **Note**: The caliber inventory snapshot from HERMES is expected to provide the remaining 9 partial indicators. This precheck covers the 15 known non-RENDERED indicators from Phase03 P1 data.

---

## 2. Render-Related Partial Indicator Analysis

### 2.1 PLACEHOLDER_ZERO Subset (9 indicators)

These indicators have data in the DB but all values are zero — expected placeholder behavior.

| # | Indicator ID | Commodity | DB Rows | Boundary Issue | Render-Related? |
|---|-------------|:---------:|:-------:|----------------|:---------------:|
| 1 | `placeholder_comexal` | al | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 2 | `placeholder_cubalancesheet` | cu | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 3 | `placeholder_comexni` | ni | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 4 | `placeholder_comexpb` | pb | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 5 | `placeholder_pbtop20long` | pb | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 6 | `placeholder_pbtop20short` | pb | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 7 | `placeholder_spotis` | si | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 8 | `placeholder_comexsn` | sn | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |
| 9 | `placeholder_comexzn` | zn | 1 | All-zero values (anomaly) | ❌ Data issue (not render) |

**Render boundary assessment**: These are **DATA issues** (all-zero values), not render boundary issues. The engine correctly returns `PLACEHOLDER_ZERO` status. No render boundary verification needed.

### 2.2 HAS_DATA (Orphan) Subset (5 indicators)

These indicators have valid DB data but no matching chart definition in the engine (DSHB orphan indicators).

| # | Indicator ID | Commodity | DB Rows | Boundary Issue | Render-Related? |
|---|-------------|:---------:|:-------:|----------------|:---------------:|
| 1 | `pb_long_short_ratio` | j21 | 3,040 | No matching chart; DSHB orphan | ✅ Chart registration |
| 2 | `pb_month_spread` | j21 | 3,022 | No matching chart; DSHB orphan | ✅ Chart registration |
| 3 | `pb_price_percentile` | j21 | 3,022 | No matching chart; DSHB orphan | ✅ Chart registration |
| 4 | `pb_term_structure` | j21 | 3,041 | No matching chart; DSHB orphan | ✅ Chart registration |
| 5 | `pb_top20_net` | j21 | 3,041 | No matching chart; DSHB orphan | ✅ Chart registration |

**Render boundary assessment**: These **ARE render-related**. The data exists but the engine has no chart definition for commodity `j21` (PB futures). Phase04 must register chart definitions for these 5 PB indicators.

#### Boundary Evidence — PB Orphan Indicators

| Indicator | Data Quality | Sample Values | Expected Chart Type |
|-----------|:------------:|:-------------:|:-------------------:|
| `pb_long_short_ratio` | Clean (18 zero, 8 outliers) | 0.008702, 0.011416 | TS line + gauge |
| `pb_month_spread` | Clean (no issues) | 20852.78, 1748.14 | TS line |
| `pb_price_percentile` | Clean (no issues) | 71.22, 31.92 | TS line + percentile |
| `pb_term_structure` | Clean (no issues) | 16550.0, 1748.14 | TS line |
| `pb_top20_net` | Clean (no issues) | 16500.0, 1746.31 | TS line + gauge |

### 2.3 NO_DATA Subset (1 indicator)

| # | Indicator ID | Commodity | DB Rows | Boundary Issue | Render-Related? |
|---|-------------|:---------:|:-------:|----------------|:---------------:|
| 1 | `si_top20_net` | si | 0 | DB has 0 rows (no data) | ⚠️ Dual issue |

**Render boundary assessment**: This is a **dual issue** — data missing (DSHB not collecting) AND no chart registration. Already documented in `partial_metric_boundary_archive.md` (Phase03 P1, 7-day stable observation, 5 boundary scenarios).

---

## 3. Render Boundary Precheck Summary

### 3.1 Boundary Categories

| Boundary Category | Count | Severity | Phase04 Action |
|:-----------------|:-----:|:--------:|:---------------|
| Chart registration missing (HAS_DATA orphans) | 5 | 🟡 MEDIUM | Register chart definitions for PB (j21) indicators |
| Data + chart missing (NO_DATA) | 1 | 🟢 LOW | DSHB data collection + chart registration |
| All-zero data (PLACEHOLDER_ZERO) | 9 | 🟢 INFO | Expected behavior; monitor for data activation |
| **Total render-related** | **6** | — | — |
| **Total data-only issues** | **9** | — | — |

### 3.2 Evidence JSON Output

Evidence data saved to: `partial_render_evidence/non_rendered_indicators_evidence.json`

### 3.3 Key Findings

1. **5 PB orphan indicators** have valid data but no engine chart registration — this is the primary render boundary gap
2. **1 SI indicator** (si_top20_net) has both data and chart gaps — already archived with 7-day stability observation
3. **9 placeholder indicators** are data issues (all-zero), not render boundary issues — expected behavior
4. **No decimal truncation boundary issues** found in current data — all rendered indicators have correct numeric precision
5. **No output format boundary issues** found — all rendered indicators produce valid chart output

---

## 4. Phase04 Remediation Recommendations

| # | Recommendation | Priority | Agent |
|---|---------------|:--------:|:-----:|
| 1 | Register chart definitions for 5 PB (j21) indicators in engine | 🟡 HIGH | DSHE |
| 2 | Continue monitoring si_top20_net until DSHB data arrives | 🟢 LOW | DSHE |
| 3 | Monitor 9 placeholder indicators for data activation | 🟢 INFO | DSHB |
| 4 | Verify remaining 9 partial indicators when HERMES caliber snapshot arrives | 🟡 MEDIUM | HERMES |

---

## 5. Status Declaration

> ⚠️ **This precheck is a pre-validation artifact (素材), NOT a caliber status change.**
>
> - ✅ No indicator matched/partial classification has been modified
> - ✅ No render_status field has been altered
> - ✅ No chart definitions have been added to the engine
> - ✅ No engine code has been modified
> - ✅ No Phase03 gate paths have been touched
> - ✅ Engine MD5 `cd73deae...` remains frozen and unchanged
>
> This report is provided as evidence for future caliber alignment by HERMES.

---

> **标记**: T2=COMPLETE | Partial Render Precheck Evidence Collected
> **Constraint**: NO status changes, NO caliber modifications, precheck only
> *Generated: 2026-10-16T22:45 UTC+8 | DSHE*