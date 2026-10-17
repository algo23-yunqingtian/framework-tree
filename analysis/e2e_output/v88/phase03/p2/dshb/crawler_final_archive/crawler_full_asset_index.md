# DSHB V88 Phase03 P025 — Crawler Full Asset Index

**TASK_ID:** V88_PHASE03_P13_DSHB_P025_CRAWLER_COMPLIANCE_REVIEW_AND_SCHEDULE_VALIDATION  
**AGENT:** DSHB  
**BRANCH:** feature/v88-g1  
**DATE:** 2026-10-22  
**STATUS:** ✅ COMPLETE INVENTORY — 45 ASSETS CATALOGUED  

---

## 1. Asset Overview

| Category | Count | Total Size |
|----------|:-----:|:----------:|
| Core crawler scripts | 5 | ~70,000 B |
| Configuration files | 2 | ~4,500 B |
| Documentation (security, manual) | 2 | ~25,500 B |
| Sample data CSVs | 27 | ~18,800 B |
| Test reports & scripts | 3 | ~16,000 B |
| Field mapping script | 1 | ~18,000 B |
| P024 verification archive | 5 | ~59,000 B |
| P025 final archive | 6 | ~50,000 B |
| Log files | 1 | ~400 B |
| **Total** | **52** | **~300,000 B** |

---

## 2. Directory Structure

```
analysis/e2e_output/v88/phase03/p2/dshb/
├── crawler_archive/                          # P023: Core crawler framework
│   ├── crawler_main.py                       # Main orchestrator
│   ├── exchange_crawler.py                   # Exchange data crawler (SHFE/DCE/CZCE)
│   ├── industry_crawler.py                   # Industry fundamentals crawler (100ppi.com)
│   ├── db_interface.py                       # SQLite database interface
│   ├── db_config.json                        # Database schema configuration
│   ├── crawler_security_rule.md              # Security & risk control rules (14 items)
│   ├── samples/                              # Sample CSV data files
│   │   ├── shfe_pbu_daily_kline_sample.csv
│   │   ├── shfe_pbu_position_ranking_sample.csv
│   │   ├── shfe_pbu_warrant_registration_sample.csv
│   │   ├── shfe_znu_daily_kline_sample.csv
│   │   ├── shfe_znu_position_ranking_sample.csv
│   │   ├── shfe_znu_warrant_registration_sample.csv
│   │   ├── dce_znu_daily_kline_sample.csv
│   │   ├── dce_znu_position_ranking_sample.csv
│   │   ├── dce_znu_warrant_registration_sample.csv
│   │   ├── pb_daily_kline_sample.csv
│   │   ├── pb_position_rank_sample.csv
│   │   ├── pb_warrant_registration_sample.csv
│   │   ├── zn_daily_kline_sample.csv
│   │   ├── zn_position_rank_sample.csv
│   │   ├── zn_warrant_registration_sample.csv
│   │   ├── industry_lead_smelting_rate_sample.csv
│   │   ├── industry_zinc_smelting_rate_sample.csv
│   │   ├── industry_primary_lead_profit_sample.csv
│   │   ├── industry_recycle_lead_profit_sample.csv
│   │   ├── industry_zinc_smelting_profit_sample.csv
│   │   ├── industry_lead_social_inventory_sample.csv
│   │   ├── industry_lead_smm_inventory_sample.csv
│   │   ├── industry_zinc_social_inventory_sample.csv
│   │   ├── industry_zinc_smm_inventory_sample.csv
│   │   ├── industry_smelting_rate_sample.csv
│   │   ├── industry_profit_sample.csv
│   │   └── industry_inventory_sample.csv
│   ├── logs/                                 # Runtime logs
│   │   └── crawler_run_summary.json          # Last run summary
│   └── __pycache__/                          # Python bytecode cache (not tracked)
│
├── crawler_verification_archive/             # P024: Verification & testing
│   ├── crawler_unit_test_report.md           # 30/30 unit test report
│   ├── e2e_test_result.md                    # 31/31 E2E test result
│   ├── field_mapper.py                       # WIND field mapping script
│   ├── crawler_operation_manual.md           # Operation manual
│   ├── run_e2e_test.py                       # E2E test script
│   ├── asset_seal_v4.md                      # Asset seal with MD5/SHA256 hashes
│   └── mapped_output/                        # WIND-mapped CSV outputs (test artifacts)
│       └── wind_*.csv (27 files)
│
└── crawler_final_archive/                    # P025: Final compliance & scheduling
    ├── crawler_compliance_review.md          # Full compliance review (14 items)
    ├── schedule_validation_report.md         # Schedule validation + switch config
    ├── seal_recheck_report.md                # Asset seal recheck (38/38 MATCH)
    ├── crawler_emergency_handling.md         # Emergency handling procedures
    ├── crawler_full_asset_index.md           # This file
    └── crawler_switch.cfg                    # Global switch configuration (OFF default)
```

---

## 3. Core Crawler Scripts (5 files)

| # | File | Size | Language | Purpose | Status |
|:-:|------|:----:|:--------:|---------|:------:|
| 1 | `crawler_main.py` | 18,569 B | Python 3 | Main orchestrator; RateLimiter; HTTPFetcher; CLI entry point | ✅ PRODUCED |
| 2 | `exchange_crawler.py` | 18,931 B | Python 3 | SHFE/DCE/CZCE data crawler; daily_kline, position_ranking, warrant_registration | ✅ PRODUCED |
| 3 | `industry_crawler.py` | 15,023 B | Python 3 | 100ppi.com industry fundamentals; 9 indicators | ✅ PRODUCED |
| 4 | `db_interface.py` | 17,165 B | Python 3 | SQLite DB interface; 4 tables; INSERT OR IGNORE | ✅ PRODUCED |
| 5 | `field_mapper.py` | 17,854 B | Python 3 | Crawler → WIND field mapping; 3 non-blocking differences | ✅ PRODUCED |

**Core Scripts Total: 87,542 B**

### Key Class/Function Inventory

| Module | Classes | Key Functions |
|--------|---------|---------------|
| `crawler_main.py` | `RateLimiter`, `HTTPFetcher`, `CrawlerFramework` | `main()`, `list_modules()`, `parse_args()` |
| `exchange_crawler.py` | `ExchangeCrawler`, `AppendOnlyCSVWriter` | `run()`, `_fetch_data_type()`, `_parse_daily_kline()`, `_parse_position_ranking()`, `_parse_warrant_registration()` |
| `industry_crawler.py` | `IndustryCrawler`, `AppendOnlyCSVWriter` | `run()`, `_fetch_indicator()`, `_parse_response()` |
| `db_interface.py` | `DatabaseInterface` | `connect()`, `load_csv()`, `query_daily_kline()`, `query_position_ranking()`, `query_industry_fundamental()`, `verify_integrity()` |
| `field_mapper.py` | `FieldMapper` | `map_row()`, `map_file()`, `detect_table()`, `convert_timestamp()` |

---

## 4. Configuration Files (2 files)

| # | File | Size | Purpose | Key Settings |
|:-:|------|:----:|---------|-------------|
| 1 | `db_config.json` | 2,563 B | SQLite DB schema configuration | 4 tables; WIND-aligned columns; constraints; Phase04 integration mapping |
| 2 | `crawler_switch.cfg` | ~2,500 B | Global switch configuration | SWITCH=OFF; ENABLE_LIVE=false; RATE_LIMIT=3.0; PRE_FLIGHT_CHECKS |

---

## 5. Documentation Files (4 files)

| # | File | Size | Purpose | Key Sections |
|:-:|------|:----:|---------|-------------|
| 1 | `crawler_security_rule.md` | 8,336 B | Security & risk control rules | 10 sections; 14 compliance items; rate limiting; UA rotation; error handling; dry-run; audit |
| 2 | `crawler_operation_manual.md` | 17,186 B | Operation manual | Quick start; start/stop; log viewing; anti-blocking; data verification; crontab template; Windows Task Scheduler |
| 3 | `crawler_compliance_review.md` | ~9,500 B | Full compliance review | 14-item review; robots.txt; access frequency; UA rotation; backoff; data storage; risk assessment |
| 4 | `crawler_emergency_handling.md` | ~9,000 B | Emergency handling procedures | 4 scenarios (page redesign, 403, field change, timeout); backup/recovery; manual intervention |

---

## 6. Sample Data Files (27 CSV files)

### 6.1 Exchange Sample Data (15 files)

| # | File | Size | Symbol | Data Type | Source |
|:-:|------|:----:|:------:|-----------|:------:|
| 1 | `shfe_pbu_daily_kline_sample.csv` | 229 B | SHFE_PBU | Daily K-line | SHFE |
| 2 | `shfe_pbu_position_ranking_sample.csv` | 867 B | SHFE_PBU | Position Ranking | SHFE |
| 3 | `shfe_pbu_warrant_registration_sample.csv` | 225 B | SHFE_PBU | Warrant Reg | SHFE |
| 4 | `shfe_znu_daily_kline_sample.csv` | 229 B | SHFE_ZNU | Daily K-line | SHFE |
| 5 | `shfe_znu_position_ranking_sample.csv` | 867 B | SHFE_ZNU | Position Ranking | SHFE |
| 6 | `shfe_znu_warrant_registration_sample.csv` | 225 B | SHFE_ZNU | Warrant Reg | SHFE |
| 7 | `dce_znu_daily_kline_sample.csv` | 236 B | DCE_ZNU | Daily K-line | DCE |
| 8 | `dce_znu_position_ranking_sample.csv` | 887 B | DCE_ZNU | Position Ranking | DCE |
| 9 | `dce_znu_warrant_registration_sample.csv` | 230 B | DCE_ZNU | Warrant Reg | DCE |
| 10 | `pb_daily_kline_sample.csv` | 1,599 B | SHFE_PBU | Daily K-line (5d) | SHFE |
| 11 | `pb_position_rank_sample.csv` | 1,517 B | SHFE_PBU | Position Rank (5d) | SHFE |
| 12 | `pb_warrant_registration_sample.csv` | 1,273 B | SHFE_PBU | Warrant Reg (5d) | SHFE |
| 13 | `zn_daily_kline_sample.csv` | 1,599 B | SHFE_ZNU | Daily K-line (5d) | SHFE |
| 14 | `zn_position_rank_sample.csv` | 1,525 B | SHFE_ZNU | Position Rank (5d) | SHFE |
| 15 | `zn_warrant_registration_sample.csv` | 1,278 B | SHFE_ZNU | Warrant Reg (5d) | SHFE |

**Exchange Samples: 15 files, ~13,000 B**

### 6.2 Industry Sample Data (12 files)

| # | File | Size | Indicator | Unit |
|:-:|------|:----:|-----------|:----:|
| 1 | `industry_lead_smelting_rate_sample.csv` | 222 B | Lead Smelting Rate | percentage |
| 2 | `industry_zinc_smelting_rate_sample.csv` | 221 B | Zinc Smelting Rate | percentage |
| 3 | `industry_primary_lead_profit_sample.csv` | 216 B | Primary Lead Profit | CNY/ton |
| 4 | `industry_recycle_lead_profit_sample.csv` | 215 B | Recycled Lead Profit | CNY/ton |
| 5 | `industry_zinc_smelting_profit_sample.csv` | 217 B | Zinc Smelting Profit | CNY/ton |
| 6 | `industry_lead_social_inventory_sample.csv` | 222 B | Lead Social Inventory | tons |
| 7 | `industry_lead_smm_inventory_sample.csv` | 221 B | Lead SMM Inventory | tons |
| 8 | `industry_zinc_social_inventory_sample.csv` | 220 B | Zinc Social Inventory | tons |
| 9 | `industry_zinc_smm_inventory_sample.csv` | 219 B | Zinc SMM Inventory | tons |
| 10 | `industry_smelting_rate_sample.csv` | 1,468 B | Smelting Rate (5d) | percentage |
| 11 | `industry_profit_sample.csv` | 2,083 B | Profit (5d) | CNY/ton |
| 12 | `industry_inventory_sample.csv` | 2,843 B | Inventory (5d) | tons |

**Industry Samples: 12 files, ~8,800 B**

**Total Sample Files: 27, ~22,000 B**

---

## 7. Test Reports & Scripts (3 files)

| # | File | Size | Purpose | Results |
|:-:|------|:----:|---------|:-------:|
| 1 | `crawler_unit_test_report.md` | 5,137 B | 30 unit tests across 4 modules | ✅ 30/30 PASS |
| 2 | `e2e_test_result.md` | 7,092 B | 31 E2E integration tests | ✅ 31/31 PASS |
| 3 | `run_e2e_test.py` | 3,819 B | E2E test execution script | ✅ Runnable |

---

## 8. P025 Final Archive (6 files)

| # | File | Size | Purpose |
|:-:|------|:----:|---------|
| 1 | `crawler_compliance_review.md` | ~9,500 B | Full compliance review (14 items + robots.txt) |
| 2 | `schedule_validation_report.md` | ~8,500 B | Schedule validation + switch config + dry-run simulation |
| 3 | `seal_recheck_report.md` | ~9,000 B | Asset seal recheck (38/38 MATCH) |
| 4 | `crawler_emergency_handling.md` | ~9,000 B | Emergency handling procedures (4 scenarios) |
| 5 | `crawler_full_asset_index.md` | (this file) | Full asset inventory |
| 6 | `crawler_switch.cfg` | ~2,500 B | Global switch configuration (OFF default) |

---

## 9. Database Schema Inventory

### 9.1 Tables (4)

| # | Table | Description | Primary Key | Columns |
|:-:|-------|-------------|-------------|:-------:|
| 1 | `daily_kline` | Daily K-line (OHLCV) | (date, symbol) | 12 |
| 2 | `position_ranking` | Position ranking (member positions) | (date, symbol, company_name) | 12 |
| 3 | `warrant_registration` | Warrant registration/cancellation | (date, symbol) | 9 |
| 4 | `industry_fundamental` | Industry fundamental indicators | (date, indicator_code) | 7 |

### 9.2 Data Types (3)

| Type | Description | Columns | Idempotent Keys |
|------|-------------|:-------:|-----------------|
| `daily_kline` | Open/High/Low/Close/Volume/OI/AvgPrice | 12 | (date, symbol) |
| `position_ranking` | Member long/short positions and changes | 12 | (date, symbol, company_name) |
| `warrant_registration` | Registration/cancellation/net/total | 9 | (date, symbol) |
| `industry_fundamental` | Smelting rate, profit, inventory | 7 | (date, indicator_code) |

### 9.3 Field Mappings (3 Non-Blocking Differences)

| Diff | Crawler | WIND | Impact | Resolution |
|:----:|---------|------|:------:|-----------|
| D1 | `SHFE_PBU` | `Pb0` | Symbol lookup only | `SYMBOL_MAP` in field_mapper.py |
| D2 | `shfe` | `SHFE` | Display only | `EXCHANGE_MAP` in field_mapper.py |
| D3 | `ISO 8601` | `YYYYMMDDHHMMSS` | Display only | `convert_timestamp()` in field_mapper.py |

---

## 10. API Endpoints Inventory

### 10.1 Exchange APIs (9 URLs)

| Exchange | Data Type | URL | Public? |
|----------|-----------|-----|:-------:|
| SHFE | Daily K-line | `https://www.shfe.com.cn/cn/business/data/dailydata/` | ✅ |
| SHFE | Position Ranking | `https://www.shfe.com.cn/cn/business/data/positionranking/` | ✅ |
| SHFE | Warrant Reg | `https://www.shfe.com.cn/cn/business/data/warrant/` | ✅ |
| DCE | Daily K-line | `https://www.dce.com.cn/publicweb/quotesdata/dailyQuotes.html` | ✅ |
| DCE | Position Ranking | `https://www.dce.com.cn/publicweb/quotesdata/memberRankings.html` | ✅ |
| DCE | Warrant Reg | `https://www.dce.com.cn/publicweb/quotesdata/warrant.html` | ✅ |
| CZCE | Daily K-line | `https://www.czce.com.cn/cn/BB2729010175/BB2729010176.htm` | ✅ |
| CZCE | Position Ranking | `https://www.czce.com.cn/cn/BB2729010175/BB2729010177.htm` | ✅ |
| CZCE | Warrant Reg | `https://www.czce.com.cn/cn/BB2729010175/BB2729010178.htm` | ✅ |

### 10.2 Industry APIs (4 URLs)

| Source | Data Type | URL | Public? |
|--------|-----------|-----|:-------:|
| 100ppi | Lead smelting | `https://www.100ppi.com/sf/20261005-lead-scrapping.html` | ✅ |
| 100ppi | Zinc smelting | `https://www.100ppi.com/sf/20261005-zinc-smelting.html` | ✅ |
| 100ppi | Lead profit | `https://www.100ppi.com/sf/20261005-lead-profit.html` | ✅ |
| 100ppi | Lead inventory | `https://www.100ppi.com/sf/20261005-lead-inventory.html` | ✅ |

**Total API Endpoints: 13 (9 exchange + 4 industry)**

---

## 11. Target Varieties (3)

| Variety | Name | SHFE Symbol | DCE Symbol | WIND Symbol | Data Types |
|---------|------|:-----------:|:----------:|:-----------:|:----------:|
| `pb` | Lead (Pb) | SHFE_PBU | — | SHFE_PBU / Pb0 | 3 |
| `zn` | Zinc (Zn) | SHFE_ZNU | DCE_ZNU | SHFE_ZNU / Zn0 | 3 |
| `recycle_pb` | Recycled Lead | — | — | SHFE_PBU_PROXY | 3 |

---

## 12. Constraints (12)

| # | Constraint | Status | Enforced By |
|:-:|------------|:------:|-------------|
| 1 | BRANCH_LOCKED | ✅ `feature/v88-g1` | Git branch lock |
| 2 | NO_OVERWRITE | ✅ | CSV append mode; DB INSERT OR IGNORE |
| 3 | NO_MODIFY_V87 | ✅ | Not touched |
| 4 | NO_EDIT_RELEASE_TAG | ✅ | Not touched |
| 5 | NO_ZHIJI_API_CALL | ✅ | 0 zhiji_api.py imports |
| 6 | UPSTREAM_WRITES | ✅ 0 | Not touched |
| 7 | FROZEN_CODE_UNMODIFIED | ✅ | No code mods |
| 8 | NO_MANUAL_INTERVENTION | ✅ | SWITCH=OFF; dual keys required |
| 9 | CALIBER_NOT_MODIFIED | ✅ | Not touched |
| 10 | NO_FINAL_BASELINE | ✅ | None |
| 11 | NO_WINDPY_CALL | ✅ | 0 windpy imports |
| 12 | NO_AUTO_PUSH | ✅ | 0 push |
| **Total** | **12/12** | **✅ ALL COMPLIANT** | |

---

## 13. Phase04 Integration Readiness

| Item | Status | Notes |
|------|:------:|-------|
| Core crawler code | ✅ READY | 5 scripts, all tested |
| Database interface | ✅ READY | 4 tables, INSERT OR IGNORE |
| Field mapper | ✅ READY | 3 differences resolved |
| Security rules | ✅ READY | 14 compliance items enforced |
| Operation manual | ✅ READY | Full start/stop/troubleshooting |
| Compliance review | ✅ READY | 14/14 PASS |
| Schedule config | ✅ READY | SWITCH=OFF (default safe) |
| Emergency procedures | ✅ READY | 4 scenarios documented |
| Asset seal | ✅ READY | 38/38 hashes verified |
| **Live parsing** | ❌ PENDING | Marked as TODO in code |
| **Dual keys** | ❌ NOT FOUND | WIND_DATA_LINK_ONLINE.flag + HERMES_TRIGGER_AUTHORIZED.flag |
| **Live HTTP requests** | ❌ BLOCKED | SWITCH=OFF + dual keys NOT_FOUND |

---

## 14. Summary

| Metric | Value |
|--------|:-----:|
| Total assets | 52 |
| Core scripts | 5 |
| Configuration files | 2 |
| Documentation | 4 |
| Sample data CSVs | 27 |
| Test reports & scripts | 3 |
| P025 final archive | 6 |
| Log files | 1 |
| API endpoints | 13 |
| Target varieties | 3 |
| Data types | 3 |
| Indicators (industry) | 9 |
| DB tables | 4 |
| Constraints | 12/12 |
| Compliance items | 14/14 |
| Unit tests | 30/30 PASS |
| E2E tests | 31/31 PASS |
| Field mapper tests | 21/21 PASS |
| HTTP requests | 0 |
| Factor calculation | PROHIBITED |
| Dual key status | NOT_FOUND |
| **Switch status** | **OFF** |

---

Generated: 2026-10-22 UTC+8 | DSHB | TASK_ID: V88_PHASE03_P13_DSHB_P025_CRAWLER_COMPLIANCE_REVIEW_AND_SCHEDULE_VALIDATION
