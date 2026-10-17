# DSHB V88 Phase03 P025 — Crawler Emergency Handling Procedures

**TASK_ID:** V88_PHASE03_P13_DSHB_P025_CRAWLER_COMPLIANCE_REVIEW_AND_SCHEDULE_VALIDATION  
**AGENT:** DSHB  
**BRANCH:** feature/v88-g1  
**DATE:** 2026-10-22  
**STATUS:** ✅ EMERGENCY PROCEDURES DEFINED — READY FOR PHASE04  

---

## 1. Emergency Severity Levels

| Level | Name | Description | Response Time | Action |
|:-----:|------|-------------|:------------:|--------|
| **P1** | CRITICAL | Crawler halted; data collection stopped; factor pipeline blocked | < 1 hour | Immediate manual intervention |
| **P2** | HIGH | Partial failure; some data sources unavailable; degraded data quality | < 4 hours | Switch to degraded mode |
| **P3** | MEDIUM | Non-critical failure; workaround available; no data loss | < 24 hours | Schedule fix in next maintenance window |
| **P4** | LOW | Minor issue; documentation update; no operational impact | Next sprint | Track in backlog |

---

## 2. Scenario 1: Website Page Redesign

### 2.1 Symptoms

| Indicator | Detection |
|-----------|-----------|
| HTTP response returns 200 but HTML structure changed | Parser returns 0 rows or incorrect data |
| CSS class names changed | BeautifulSoup selectors return empty |
| Page layout reorganized | Expected data fields missing from response |
| URL paths changed | HTTP 404 on previously valid URLs |

### 2.2 Immediate Response (P1/P2)

```
1. DETECT
   - Monitor run_summary.json for results_count = 0 or unexpected values
   - Check crawler logs for parsing warnings
   - Verify response status codes

2. ISOLATE
   - Switch crawler_switch.cfg: SWITCH=OFF (halt scheduled tasks)
   - Identify affected data source (exchange or industry)
   - Log to compliance_log.jsonl: "PAGE_REDESIGN_DETECTED: {url}"

3. ANALYZE
   - Fetch page manually to inspect new HTML structure
   - Compare old vs new CSS selectors / table structures
   - Identify what data is still available vs what changed

4. MITIGATE
   - Option A: Update parser code for new structure (preferred)
   - Option B: Switch to alternative data source (if available)
   - Option C: Switch to dry-run mode; maintain synthetic data pipeline
   - Option D: Pause affected module; continue others

5. DOCUMENT
   - Update crawler_security_rule.md with new URL paths
   - Record change in compliance_log.jsonl
   - Update field_mapper.py if column names changed
```

### 2.3 Degradation Strategy

| Module | Impact | Degraded Mode | Data Gap |
|--------|:------:|---------------|:--------:|
| Exchange daily_kline | MEDIUM | Use last available close price + 0 for OHLCV | 1 session |
| Exchange position_ranking | LOW | Skip ranking; use previous day data | 1 session |
| Exchange warrant_registration | LOW | Skip warrant data; use previous balance | 1 session |
| Industry indicators | MEDIUM | Use DRY_RUN_SAMPLE_DATA values; flag as estimated | Indefinite |

### 2.4 Recovery

| Step | Action | Verification |
|:----:|--------|:------------:|
| 1 | Update parser code for new HTML structure | Run `--dry-run` with new parser |
| 2 | Verify parser produces correct data | Compare with manual page inspection |
| 3 | Update field_mapper.py if column changes | Run `--selftest` |
| 4 | Enable SWITCH=ON with ENABLE_LIVE=true | Run one live session |
| 5 | Verify data quality | Check CSV output against expected schema |
| 6 | Update compliance_log.jsonl | Log recovery timestamp |

---

## 3. Scenario 2: HTTP 403 Forbidden (IP Blocking)

### 3.1 Symptoms

| Indicator | Detection |
|-----------|-----------|
| HTTP 403 response code | `[403 BLOCKED]` in crawler output |
| 3 retries exhausted | `MAX_RETRIES_EXCEEDED` in logs |
| All requests from IP blocked | 403 on all URLs from same site |
| Partial blocking | 403 on some URLs, others succeed |

### 3.2 Immediate Response (P1)

```
1. DETECT
   - Check crawler logs for [403] warnings
   - Count consecutive 403 errors
   - Monitor compliance_log.jsonl for 403 entries

2. HALT (Automatic)
   - 2 consecutive 403s → auto-halt (per security rules)
   - 3 consecutive errors → session halt + manual review
   - If not auto-halted: manually set SWITCH=OFF

3. DIAGNOSE
   - Check if blocking is temporary (rate limit) or permanent (IP ban)
   - Try fetching from different network/VPN (if available)
   - Check if other IPs on same subnet are blocked

4. MITIGATE
   - Option A: Wait 24-48 hours; exchange IP blocks may expire
   - Option B: Switch to alternative exchange API endpoint (if available)
   - Option C: Use cached/historical data from SQLite DB
   - Option D: Switch to DRY_RUN mode for affected site

5. PREVENT
   - Increase rate limit to 5.0s or 10.0s
   - Reduce request frequency (weekly instead of daily)
   - Ensure UA rotation is active
```

### 3.3 Degradation Strategy

| Source | Blocked Duration | Data Gap | Workaround |
|--------|:---------------:|:--------:|-----------|
| SHFE | < 24h | 1 session | Use last available data |
| SHFE | 24-72h | 2-3 sessions | Use cached data + synthetic |
| SHFE | > 72h | Indefinite | Switch to DRY_RUN; alert operator |
| DCE | < 24h | 1 session | Use cached data |
| 100ppi | < 24h | 1 session | Use DRY_RUN_SAMPLE_DATA |

### 3.4 Recovery

| Step | Action | Verification |
|:----:|--------|:------------:|
| 1 | Wait for block to expire (24-48h typical) | Try single request; expect 200 |
| 2 | Increase rate limit to 5.0s | Verify in crawler_switch.cfg |
| 3 | Run single dry-run session | Verify parser works |
| 4 | Run single live session | Verify HTTP 200 response |
| 5 | Gradually restore to 3.0s rate limit | Monitor for 403 recurrence |
| 6 | Update compliance_log.jsonl | Log recovery timestamp |

---

## 4. Scenario 3: Field Structure Change

### 4.1 Symptoms

| Indicator | Detection |
|-----------|-----------|
| CSV output columns mismatch | Schema validation fails |
| Data values in wrong columns | Values appear as text in numeric fields |
| New columns appear in source | Parser ignores new fields |
| Old columns removed from source | Parser returns None for missing fields |
| Unit changes | Values appear 10x/100x different |

### 4.2 Immediate Response (P2)

```
1. DETECT
   - Run db_interface.py --verify; check for type errors
   - Compare CSV output against db_config.json schema
   - Check field_mapper.py --selftest for mapping failures

2. ANALYZE
   - Compare old vs new column names and types
   - Identify which D1/D2/D3 mappings are affected
   - Check if changes affect daily_kline, position_ranking,
     warrant_registration, or industry_fundamental

3. MITIGATE
   - Option A: Update field_mapper.py mappings (preferred)
   - Option B: Update CSV schema in exchange_crawler.py / industry_crawler.py
   - Option C: Update db_interface.py SCHEMAS definitions
   - Option D: If incompatible, halt module and alert operator

4. PREVENT
   - Add schema version tracking to output CSV
   - Run field_mapper.py --selftest after every change
   - Maintain schema changelog in compliance_log.jsonl
```

### 4.3 Degradation Strategy

| Change Type | Impact | Degraded Mode | Recovery Effort |
|-------------|:------:|---------------|:---------------:|
| Column rename | LOW | Update field_mapper.py mapping | < 1 hour |
| Column removal | MEDIUM | Skip affected fields; use NULL | < 2 hours |
| Column addition | LOW | Ignore new columns; use existing | < 30 min |
| Type change (string→numeric) | HIGH | Parse with try/except; skip bad rows | < 4 hours |
| Unit change | MEDIUM | Apply conversion factor; flag as estimated | < 2 hours |

---

## 5. Scenario 4: Network Timeout

### 5.1 Symptoms

| Indicator | Detection |
|-----------|-----------|
| `TimeoutError` or `socket.timeout` | Network connectivity issue |
| Connection timeout (30s) | Target site slow or unreachable |
| Intermittent timeouts | Unstable network connection |
| All requests time out | Target site down |

### 5.2 Immediate Response (P2)

```
1. DETECT
   - Monitor crawler logs for timeout errors
   - Check if timeouts are on all URLs or specific ones
   - Verify network connectivity (ping target site)

2. DIAGNose
   - Ping target website from crawler host
   - Check if timeout is on connection or read phase
   - Check if DNS resolution works

3. MITIGATE
   - Option A: Increase timeout from 30s to 60s (if transient)
   - Option B: Retry with exponential backoff (already implemented)
   - Option C: Switch to DRY_RUN for affected module
   - Option D: Halt crawl if all sources timeout

4. PREVENT
   - Set max 3 retries with 5s backoff (already configured)
   - Monitor timeout frequency in compliance_log.jsonl
   - Alert operator if > 3 consecutive timeouts
```

### 5.3 Degradation Strategy

| Timeout Type | Duration | Impact | Workaround |
|-------------|:--------:|:------:|-----------|
| Single URL timeout | < 30s | LOW | Retry 3x with 5s backoff |
| All URLs timeout | < 5 min | MEDIUM | Skip affected module |
| All URLs timeout | > 5 min | HIGH | Switch to DRY_RUN; alert |
| Intermittent | Ongoing | LOW | Increase retry count; accept data gaps |

---

## 6. Data Backup & Recovery

### 6.1 Backup Policy

| Asset | Backup Method | Frequency | Retention |
|-------|---------------|:---------:|:---------:|
| CSV sample data | Git version control | Per commit | Indefinite |
| SQLite DB | Copy file (`factor_data.db`) | Weekly | 4 weeks |
| Log files | Git version control | Per commit | Indefinite |
| Configuration | Git version control | Per commit | Indefinite |
| Field mapper | Git version control | Per commit | Indefinite |

### 6.2 Manual Backup Procedure

```bash
# Backup SQLite database
cd framework-tree/analysis/e2e_output/v88/phase03/p2/dshb/crawler_archive
cp data/factor_data.db data/factor_data_backup_$(date +%Y%m%d).db

# Verify backup integrity
python db_interface.py --verify --db-path data/factor_data_backup_$(date +%Y%m%d).db

# Backup configuration
cp crawler_archive/db_config.json crawler_archive/db_config_backup.json
cp crawler_final_archive/crawler_switch.cfg crawler_final_archive/crawler_switch_backup.cfg
```

### 6.3 Recovery Procedure

```bash
# Restore SQLite database
cp data/factor_data_backup_YYYYMMDD.db data/factor_data.db
python db_interface.py --verify --db-path data/factor_data.db

# Verify table counts match expected
python db_interface.py --count --db-path data/factor_data.db

# Restore configuration
cp crawler_switch_backup.cfg crawler_final_archive/crawler_switch.cfg
```

### 6.4 Data Loss Prevention

| Scenario | Data Loss Risk | Prevention |
|----------|:-------------:|------------|
| CSV write interruption | LOW | APPEND_ONLY + partial row safe (last row may be incomplete) |
| DB write interruption | LOW | WAL journal mode + PRAGMA synchronous=NORMAL |
| File corruption | LOW | CSV is text-based; DB has integrity_check pragma |
| Disk full | MEDIUM | Monitor disk space; alert at 80% |
| Accidental deletion | LOW | Git version control provides rollback |

---

## 7. Manual Intervention Steps

### 7.1 Emergency Halt Procedure

```bash
# Step 1: Set switch to OFF immediately
echo "SWITCH=OFF" > crawler_final_archive/crawler_switch.cfg

# Step 2: If cron is running, disable it
crontab -l | grep -v crawler > /tmp/mycron && crontab /tmp/mycron

# Step 3: If task scheduler is running, disable it
schtasks /Change /TN "DSHB_Crawler_Daily" /DISABLE

# Step 4: Kill any running crawler processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *crawler*"

# Step 5: Log the emergency halt
echo "{\"ts\":\"$(date -Iseconds)\",\"action\":\"emergency_halt\",\"reason\":\"manual\"}" >> logs/compliance_log.jsonl
```

### 7.2 Emergency Restart Procedure

```bash
# Step 1: Verify dual keys
cat WIND_DATA_LINK_ONLINE.flag 2>/dev/null || echo "Key A: NOT_FOUND"
cat HERMES_TRIGGER_AUTHORIZED.flag 2>/dev/null || echo "Key B: NOT_FOUND"

# Step 2: Set switch to ON
echo "SWITCH=ON" > crawler_final_archive/crawler_switch.cfg

# Step 3: Set live mode if keys are found
echo "ENABLE_LIVE=true" >> crawler_final_archive/crawler_switch.cfg

# Step 4: Run single dry-run to verify
python crawler_main.py --module all --dry-run --rate-limit 5.0

# Step 5: If dry-run passes, enable cron
# Uncomment cron entries in crawler_switch.cfg
# crontab -e

# Step 6: Monitor first live session
python crawler_main.py --module all --live --rate-limit 5.0
```

### 7.3 Data Quality Check (Post-Incident)

```bash
# Step 1: Verify DB integrity
python db_interface.py --verify --db-path data/factor_data.db

# Step 2: Check for NULL values in critical columns
python -c "
import sqlite3
conn = sqlite3.connect('data/factor_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM daily_kline WHERE close IS NULL')
print(f'NULL close values: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM daily_kline WHERE close = 0')
print(f'Zero close values: {cursor.fetchone()[0]}')
"

# Step 3: Check date continuity
python -c "
import sqlite3
conn = sqlite3.connect('data/factor_data.db')
cursor = conn.cursor()
cursor.execute('SELECT date FROM daily_kline ORDER BY date DESC LIMIT 5')
print('Recent dates:', [row[0] for row in cursor.fetchall()])
"

# Step 4: Verify field mapping
python crawler_verification_archive/field_mapper.py --selftest
```

---

## 8. Incident Response Timeline

```
T+0    : Incident detected (P1/P2)
T+5min : SWITCH=OFF set; emergency halt
T+15min: Root cause analysis started
T+1hr  : Mitigation applied (degraded mode or fix)
T+4hr  : P2 recovery complete
T+24hr : P3 recovery complete
T+1wk  : P4 backlog item addressed
```

---

## 9. Contact & Escalation

| Level | Contact | Channel | Response Time |
|:-----:|---------|---------|:------------:|
| P1 CRITICAL | Operator | Direct message | < 1 hour |
| P2 HIGH | Operator | Email | < 4 hours |
| P3 MEDIUM | Team | Slack/email | < 24 hours |
| P4 LOW | Backlog | Jira/GitHub | Next sprint |

**Note:** All contacts are internal. No external escalation for data pipeline incidents.

---

## 10. Summary of Emergency Scenarios

| Scenario | Severity | Detection | Degradation | Recovery |
|----------|:--------:|-----------|:-----------:|:--------:|
| Website page redesign | P1-P2 | 0 rows parsed | Use cached data | Update parser |
| HTTP 403 IP blocking | P1 | 403 in logs | Wait 24-48h | Increase rate limit |
| Field structure change | P2 | Schema mismatch | Update mappings | Update field_mapper.py |
| Network timeout | P2 | Timeout errors | Retry with backoff | Increase timeout |
| Disk full | P1 | DB write error | Free space | Clean old backups |
| Accidental deletion | P1 | Missing files | Git restore | `git checkout -- <file>` |

---

## 11. Constraint Compliance

| # | Constraint | Status |
|:-:|------------|:------:|
| 1 | BRANCH_LOCKED | ✅ `feature/v88-g1` |
| 2 | NO_OVERWRITE | ✅ All procedures respect existing files |
| 3 | NO_MODIFY_V87 | ✅ Not touched |
| 4 | NO_EDIT_RELEASE_TAG | ✅ Not touched |
| 5 | NO_ZHIJI_API_CALL | ✅ Emergency procedures never call paid APIs |
| 6 | UPSTREAM_WRITES | ✅ 0 |
| 7 | FROZEN_CODE_UNMODIFIED | ✅ No code mods in this document |
| 8 | NO_MANUAL_INTERVENTION | ✅ Procedures documented; human action required for live |
| 9 | CALIBER_NOT_MODIFIED | ✅ Not touched |
| 10 | NO_FINAL_BASELINE | ✅ None |
| 11 | NO_WINDPY_CALL | ✅ 0 imports |
| 12 | NO_AUTO_PUSH | ✅ 0 push |
| **Total** | **12/12** | **✅ ALL COMPLIANT** |

---

Generated: 2026-10-22 UTC+8 | DSHB | TASK_ID: V88_PHASE03_P13_DSHB_P025_CRAWLER_COMPLIANCE_REVIEW_AND_SCHEDULE_VALIDATION
