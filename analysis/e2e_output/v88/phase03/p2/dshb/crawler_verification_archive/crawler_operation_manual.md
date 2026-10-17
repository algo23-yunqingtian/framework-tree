# DSHB Crawler Operation Manual

TASK_ID: V88_PHASE03_P12_DSHB_P024_CRAWLER_E2E_TEST_AND_DOC
BRANCH: feature/v88-g1
BRANCH_LOCKED: TRUE

---

## 1. System Overview

### 1.1 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Crawler Framework v1.0.0                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │  crawler_main.py │───▶│  exchange_crawler.py              │  │
│  │  (Orchestrator)  │    │  SHFE / DCE / CZCE                │  │
│  │                  │    │  daily_kline / position_ranking   │  │
│  │                  │    │  warrant_registration             │  │
│  │                  │    └──────────────────────────────────┘  │
│  │                  │                                            │
│  │                  │    ┌──────────────────────────────────┐  │
│  │                  │───▶│  industry_crawler.py              │  │
│  │                  │    │  100ppi.com / 生意社               │  │
│  │                  │    │  9 fundamental indicators         │  │
│  └──────────────────┘    └──────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │  db_interface.py │    │  field_mapper.py                  │  │
│  │  (SQLite DB)     │    │  Crawler → WIND field mapping    │  │
│  │  4 tables         │    │  3 non-blocking differences      │  │
│  └──────────────────┘    └──────────────────────────────────┘  │
│                                                                   │
│  RateLimiter: ≥3.0s minimum | HTTPFetcher: 4 UA pool             │
│  Retry: 403→10s, 429→30s | Timeout: 30s                          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
Exchange Pages ──▶ exchange_crawler ──▶ CSV (WIND-aligned) ──▶ db_interface ──▶ SQLite
Industry Pages ──▶ industry_crawler ──▶ CSV (indicators)    ──▶ db_interface ──▶ SQLite
                                                                        │
                                                                        ▼
                                                                  field_mapper
                                                                        │
                                                                        ▼
                                                              WIND Standard Fields
                                                                        │
                                                                        ▼
                                                          Phase04 Factor Input (LOCKED)
```

### 1.3 File Inventory

| File | Size | Purpose |
|------|:----:|---------|
| `crawler_main.py` | 18,569 B | Main orchestrator |
| `exchange_crawler.py` | 18,931 B | Exchange public data crawler |
| `industry_crawler.py` | 15,023 B | Industry fundamentals crawler |
| `db_interface.py` | 17,165 B | SQLite database interface |
| `db_config.json` | 2,563 B | Database schema configuration |
| `field_mapper.py` | 15,455 B | Field mapping script (T2 deliverable) |
| `crawler_security_rule.md` | 8,336 B | Risk control documentation |

---

## 2. Quick Start

### 2.1 Prerequisites

```bash
# Python 3.10+ (stdlib only, no external dependencies required)
# Optional: requests, beautifulsoup4 (for live parsing, not needed for dry-run)
python --version  # 3.12.10+

# Verify module availability
python -c "import sqlite3, csv, json, urllib.request, datetime; print('All stdlib modules available')"
```

### 2.2 Environment Variables

```bash
# Required
export PYTHONIOENCODING="utf-8"
export PYTHONUNBUFFERED="1"

# Optional (for live HTTP requests only)
export CRAWLER_RATE_LIMIT="3.0"   # Minimum seconds between requests
```

### 2.3 Working Directory

```bash
cd framework-tree/analysis/e2e_output/v88/phase03/p2/dshb/crawler_archive/
```

---

## 3. Start Commands

### 3.1 List Available Modules

```bash
python crawler_main.py --list-modules
```

Output:
```
DSHB Crawler Framework v1.0.0
TASK_ID: V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT
BRANCH: feature/v88-g1

Modules:
  exchange  - Exchange public data (SHFE, DCE, CZCE)
  industry  - Industry fundamentals (100ppi.com)
  all       - Run both modules

Exchanges:
  shfe    Shanghai Futures Exchange (SHFE)
  dce     Dalian Commodity Exchange (DCE)
  czce    Zhengzhou Commodity Exchange (CZCE)

Constraints (8 enforced):
  [ON] NO_ZHIJI_API_CALL
  [ON] NO_OVERWRITE
  [ON] APPEND_ONLY
  [ON] DRY_RUN_DEFAULT
  [ON] RATE_LIMIT_ENFORCED
  [ON] NO_CONCURRENT_REQUESTS
  [ON] NO_FACTOR_CALCULATION
  [ON] NO_PAID_API_CALLS
```

### 3.2 Dry-Run Mode (Default, Safe)

```bash
# Full dry-run: all exchanges + industry
python crawler_main.py --module all --dry-run --rate-limit 3.0

# Exchange only
python crawler_main.py --module exchange --dry-run

# Specific exchange
python crawler_main.py --module exchange --exchange shfe --dry-run

# Industry only
python crawler_main.py --module industry --dry-run

# With verbose logging
python crawler_main.py --module all --dry-run --verbose
```

**Dry-run behavior**:
- No actual HTTP requests are made
- CSV sample files are generated with synthetic data
- Useful for testing module integration without network dependency

### 3.3 Live Mode (Real HTTP Requests)

```bash
# WARNING: Live mode makes real HTTP requests!
# Only use when WIND_DATA_LINK_ONLINE.flag is FOUND

# Full live crawl
python crawler_main.py --module all --live --rate-limit 3.0

# Single exchange live
python crawler_main.py --module exchange --exchange shfe --live --rate-limit 5.0

# Specific date
python crawler_main.py --module exchange --exchange shfe --date 2026-10-20 --live
```

**Live mode requirements**:
- WIND_DATA_LINK_ONLINE.flag must be FOUND
- HERMES_TRIGGER_AUTHORIZED.flag must be FOUND
- Both flags currently NOT_FOUND → live mode is BLOCKED

### 3.4 Database Interface

```bash
# Run self-test
python db_interface.py --selftest

# Verify integrity
python db_interface.py --verify --db-path data/factor_data.db

# Show table counts
python db_interface.py --count --db-path data/factor_data.db
```

### 3.5 Field Mapper

```bash
# Run self-test
python field_mapper.py --selftest

# Map single file
python field_mapper.py --input samples/shfe_pbu_daily_kline_sample.csv

# Map all files in directory
python field_mapper.py --input samples/ --output mapped_output/

# Specify table type
python field_mapper.py --input samples/ --output mapped_output/ --table daily_kline
```

---

## 4. Start/Stop Control

### 4.1 Normal Start

```bash
# 1. Navigate to working directory
cd framework-tree/analysis/e2e_output/v88/phase03/p2/dshb/crawler_archive/

# 2. Verify dry-run works
python crawler_main.py --module all --dry-run --rate-limit 3.0

# 3. Verify DB interface
python db_interface.py --selftest

# 4. Verify field mapper
python ../crawler_verification_archive/field_mapper.py --selftest
```

### 4.2 Stopping

```bash
# The crawler is single-process and sequential — no daemon
# Simply use Ctrl+C to stop
# No cleanup needed (APPEND_ONLY + NO_OVERWRITE)

# If a live crawl is running, Ctrl+C stops gracefully
# Any partially written CSV files are safe (last row may be incomplete)
```

### 4.3 Status Check

```bash
# Check last run summary
cat logs/crawler_run_summary.json

# Check crawler logs
tail -50 logs/crawler_*.log

# Check DB status
python db_interface.py --count --db-path data/factor_data.db
```

---

## 5. Log Viewing

### 5.1 Log File Locations

| File | Purpose |
|------|---------|
| `logs/crawler_run_summary.json` | Run summary (JSON) |
| `logs/crawler_*.log` | Crawler logs (if configured) |
| Console output | Default (stdout/stderr) |

### 5.2 Run Summary JSON

```bash
cat logs/crawler_run_summary.json
```

Example:
```json
{
  "task_id": "V88_PHASE03_P11_DSHB_P023_DATA_CRAWLER_DEVELOPMENT",
  "agent": "DSHB",
  "branch": "feature/v88-g1",
  "version": "1.0.0",
  "timestamp": "2026-10-22T17:44:31",
  "module": "all",
  "exchange": "all",
  "dry_run": true,
  "rate_limit_seconds": 3.0,
  "results_count": 18,
  "constraints_enforced": 8,
  "total_constraints": 8
}
```

### 5.3 Log Level Configuration

```bash
# Default: INFO
python crawler_main.py --module all --dry-run

# Verbose: DEBUG
python crawler_main.py --module all --dry-run --verbose
```

---

## 6. Anti-Blocking Risk Troubleshooting

### 6.1 Common Issues

| Issue | Symptom | Cause | Resolution |
|-------|---------|-------|------------|
| 403 Forbidden | `[403 BLOCKED]` in output | IP blocked by exchange | Increase rate limit; check UA rotation |
| 429 Too Many Requests | `[429] Rate limited` | Too many requests | Wait 30s backoff; increase interval |
| Timeout | `HTTP 408` or timeout error | Network slow | Increase timeout (default 30s) |
| Empty data | Rows with all zeros | Dry-run synthetic data | Switch to `--live` mode |
| Encoding error | `UnicodeDecodeError` | Chinese site uses GBK | HTTPFetcher auto-falls back to GBK |

### 6.2 Rate Limit Tuning

```bash
# Default: 3.0 seconds (minimum, hard floor)
python crawler_main.py --module all --live --rate-limit 3.0

# Recommended for first live run: 5.0 seconds
python crawler_main.py --module all --live --rate-limit 5.0

# Conservative: 10.0 seconds
python crawler_main.py --module all --live --rate-limit 10.0
```

**Note**: RateLimiter enforces hard floor of 3.0s regardless of configured value.

### 6.3 User-Agent Rotation

The HTTPFetcher rotates between 4 User-Agents automatically:

```python
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ... Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) ... Chrome/120.0.0.0",
]
```

Rotation is based on `hash(datetime.now()) % len(UA_POOL)`.

### 6.4 Retry Logic

| Error Code | Backoff | Max Retries |
|:----------:|:-------:|:-----------:|
| 403 | 10s | 3 |
| 429 | 30s | 3 |
| Other HTTP | 5s | 3 |
| Network error | 5s | 3 |

**Note**: All retries are sequential (no concurrent). After max retries, returns error string.

---

## 7. Data Verification Steps

### 7.1 CSV Verification

```bash
# Check sample CSV structure
head -3 samples/shfe_pbu_daily_kline_sample.csv

# Verify WIND-aligned columns
head -1 samples/shfe_pbu_daily_kline_sample.csv
# Expected: date,symbol,exchange,open,high,low,close,volume,open_interest,avg_price,source_url,crawl_timestamp
```

### 7.2 DB Verification

```bash
# Run integrity check
python db_interface.py --verify --db-path data/factor_data.db

# Check table counts
python db_interface.py --count --db-path data/factor_data.db
```

### 7.3 Field Mapping Verification

```bash
# Run field mapper self-test
python field_mapper.py --selftest

# Map a file and verify output
python field_mapper.py --input samples/shfe_pbu_daily_kline_sample.csv
cat wind_shfe_pbu_daily_kline_sample.csv
# Verify: s_code=Pb0, exch_code=SHFE, update_time=20261017165031
```

### 7.4 End-to-End Verification

```bash
# 1. Run dry-run
python crawler_main.py --module all --dry-run --rate-limit 3.0

# 2. Load to DB
python db_interface.py --selftest

# 3. Map fields
python field_mapper.py --input samples/ --output mapped_output/

# 4. Verify mapped output
head -3 mapped_output/wind_shfe_pbu_daily_kline_sample.csv
```

---

## 8. Scheduled Task Template (Crontab)

### 8.1 Default Configuration: DISABLED

The scheduled crawler task is **DISABLED BY DEFAULT**. Automatic crawling requires:
1. WIND_DATA_LINK_ONLINE.flag = FOUND
2. HERMES_TRIGGER_AUTHORIZED.flag = FOUND
3. Manual activation of the cron entry

### 8.2 Crontab Template

```bash
# ============================================================
# DSHB Crawler Scheduled Task Template
# BRANCH: feature/v88-g1 (BRANCH_LOCKED)
# WARNING: Auto-crawl is DISABLED BY DEFAULT
# ============================================================
#
# Format: minute hour day month weekday command
#
# Uncomment and set WIND_DATA_LINK_ONLINE=TRUE to enable
#
# ============================================================

# --- DAILY CRAWL (disabled by default) ---
# # Weekdays at 06:00 UTC+8 — after market close data available
# WIND_DATA_LINK_ONLINE=TRUE 0 6 * * 1-5 \
#   cd /path/to/crawler_archive && \
#   python crawler_main.py --module all --live --rate-limit 5.0 \
#   2>&1 | tee -a logs/crawler_cron.log

# --- EXCHANGE ONLY (disabled by default) ---
# # Weekdays at 06:30 UTC+8 — exchange data ready
# 0 6 * * 1-5 cd /path/to/crawler_archive && \
#   python crawler_main.py --module exchange --live --rate-limit 5.0 \
#   2>&1 | tee -a logs/exchange_cron.log

# --- INDUSTRY ONLY (disabled by default) ---
# # Weekdays at 07:00 UTC+8 — industry data ready
# 0 7 * * 1-5 cd /path/to/crawler_archive && \
#   python crawler_main.py --module industry --live --rate-limit 5.0 \
#   2>&1 | tee -a logs/industry_cron.log

# --- DAILY FIELD MAPPING (disabled by default) ---
# # After crawl, map fields to WIND standard
# 30 7 * * 1-5 cd /path/to/crawler_archive && \
#   python ../crawler_verification_archive/field_mapper.py \
#   --input samples/ --output mapped_output/ \
#   2>&1 | tee -a logs/field_map_cron.log

# --- WEEKLY INTEGRITY CHECK (disabled by default) ---
# # Sunday at 09:00 UTC+8 — weekly DB integrity verification
# 0 9 * * 0 cd /path/to/crawler_archive && \
#   python db_interface.py --verify --db-path data/factor_data.db \
#   2>&1 | tee -a logs/integrity_check.log
```

### 8.3 Enable/Disable Switch

```bash
# To enable automatic crawling:
# 1. Verify both keys are FOUND
#    cat WIND_DATA_LINK_ONLINE.flag   # should exist
#    cat HERMES_TRIGGER_AUTHORIZED.flag  # should exist
# 2. Uncomment the cron entries above
# 3. Set WIND_DATA_LINK_ONLINE=TRUE in the cron command
# 4. Edit crontab: crontab -e
# 5. Verify: crontab -l

# To disable:
# 1. Comment out the cron entries
# 2. Or set WIND_DATA_LINK_ONLINE=FALSE
```

### 8.4 Windows Task Scheduler Alternative

For Windows environments (Task Scheduler):

```xml
<!-- crawler_daily_task.xml — Windows Task Scheduler template -->
<!-- Disabled by default; import to enable -->
<Task>
  <RegistrationInfo>
    <Description>DSHB Crawler Daily Run (DISABLED BY DEFAULT)</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-01T06:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysOfWeek>
          <Monday/>
          <Tuesday/>
          <Wednesday/>
          <Thursday/>
          <Friday/>
        </DaysOfWeek>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>
        crawler_main.py --module all --live --rate-limit 5.0
      </Arguments>
      <WorkingDirectory>
        /path/to/crawler_archive
      </WorkingDirectory>
    </Exec>
  </Actions>
  <Settings>
    <Enabled>false</Enabled>
    <AllowStartOnDemand>true</AllowStartOnDemand>
  </Settings>
</Task>
```

---

## 9. Compliance Checklist

| # | Requirement | Status |
|:-:|-------------|:------:|
| 1 | Rate limit ≥3.0s | ✅ Enforced |
| 2 | No concurrent requests | ✅ Sequential only |
| 3 | UA rotation | ✅ 4 UA pool |
| 4 | Dry-run default | ✅ Default |
| 5 | No factor calculation | ✅ Prohibited |
| 6 | No paid API calls | ✅ None |
| 7 | APPEND_ONLY writes | ✅ CSV + DB |
| 8 | NO_OVERWRITE | ✅ Idempotent |
| 9 | Anti-blocking retry | ✅ 403/429 handled |
| 10 | Scheduled task disabled | ✅ Default OFF |
| 11 | No zhiji API calls | ✅ Never imported |
| 12 | 12 constraints | ✅ 12/12 |

---

Generated: 2026-10-22 UTC+8 | DSHB | TASK_ID: V88_PHASE03_P12_DSHB_P024_CRAWLER_E2E_TEST_AND_DOC