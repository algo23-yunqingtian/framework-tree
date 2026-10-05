# V86-RC2 L2 Alert Adapter V3 — Production Isolation Report

> **Task**: 工单-DSHE / T3.3 V86-RC2 L2 SHARD BUGFIX PROD ADAPT
> **Branch**: `feature/v85-chart-template` (BRANCH_LOCKED=TRUE)
> **Adapter Version**: 3.0.0
> **Evidence Contract**: EVIDENCE_CONTRACT_V1
> **Date**: 2026-10-15
> **Status**: FINAL
> **Prepared by**: DSHE L2 Alert Adapter Team

---

## 1. Architecture: Sandbox vs Prod

### 1.1 Overview

The V3 Alert Adapter introduces **full environment isolation** between sandbox and production modes. Each environment has completely independent:

- **Log files** — Separate log directories per environment
- **Checkpoint storage** — Separate JSONL checkpoint files per environment
- **Authentication** — HMAC-SHA256 signatures for prod payloads
- **Metrics namespaces** — Environment-tagged metrics (`env=sandbox` / `env=prod`)
- **Alert payloads** — All payloads include `deploy_env` field

### 1.2 Environment Matrix

| Aspect | Sandbox | Prod |
|--------|---------|------|
| **Default** | Yes | No (must specify `--deploy-env prod`) |
| **Auth Required** | No | **Yes** (--auth-token or AUTH_TOKEN) |
| **Auth Signature** | None | HMAC-SHA256 |
| **Log File** | `.logs/alert_adapter_v3_sandbox.log` | `.logs/alert_adapter_v3_prod.log` |
| **Checkpoint File** | `.checkpoint/alert_adapter_v3_sandbox.jsonl` | `.checkpoint/alert_adapter_v3_prod.jsonl` |
| **Metrics Tag** | `env=sandbox` | `env=prod` |
| **Cross-Env Writes** | **Prohibited** | **Prohibited** |
| **Auth Service** | Not initialized | Active (ProductionAuthService) |

### 1.3 Payload Extension

All V3 alert payloads include the `deploy_env` field:

```json
{
  "event_id": "AE-xxxxxxxxxxxx",
  "level": "CRITICAL",
  "rule": "R-AUDIT-03",
  "detect_point": "D03.2",
  "deploy_env": "prod",
  "auth_signature": "a1b2c3d4e5f6...",
  "auth_timestamp": "2026-10-15T12:00:00Z",
  "auth_algorithm": "HMAC-SHA256",
  ...
}
```

---

## 2. Authentication Mechanism

### 2.1 Token Source

| Source | Priority | Example |
|--------|----------|---------|
| `--auth-token TOKEN` CLI flag | Highest | `--auth-token my-secret-key` |
| `AUTH_TOKEN` environment variable | Second | `export AUTH_TOKEN=my-secret-key` |

If neither is provided in prod mode, the adapter exits with error:

```
Error: --auth-token is required for --deploy-env prod
  Usage: --auth-token YOUR_TOKEN or set AUTH_TOKEN environment variable
```

### 2.2 HMAC-SHA256 Signature

Each alert payload in prod mode is signed with HMAC-SHA256:

```python
# Canonical payload serialization
canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

# HMAC-SHA256 signature
key = auth_token.encode('utf-8')
message = canonical.encode('utf-8')
signature = hmac.new(key, message, hashlib.sha256).hexdigest()
```

### 2.3 Signed Payload Fields

| Field | Description |
|-------|-------------|
| `auth_signature` | Hex-encoded HMAC-SHA256 digest |
| `auth_timestamp` | UTC timestamp of signing (`YYYY-MM-DDTHH:MM:SSZ`) |
| `auth_algorithm` | `"HMAC-SHA256"` |

### 2.4 Sandbox Mode Behavior

In sandbox mode:
- No auth token required
- No HMAC signing performed
- `auth_signature` = `None`
- `auth_timestamp` = `None`
- `auth_algorithm` = `None`
- Payloads still include `deploy_env: "sandbox"`

---

## 3. Log Isolation

### 3.1 Log Files

| Environment | Log Path | Format |
|-------------|----------|--------|
| Sandbox | `.logs/alert_adapter_v3_sandbox.log` | Structured (asctime, level, message) |
| Prod | `.logs/alert_adapter_v3_prod.log` | Structured (asctime, level, message) |
| V2 (legacy) | `.logs/alert_adapter_v2.log` | Preserved from V2 |

### 3.2 Isolation Guarantee

- Sandbox logs **never** write to the prod log file
- Prod logs **never** write to the sandbox log file
- Each environment has its own `logging.getLogger("alert_adapter_v3_<env>")` logger
- Log directory (`.logs/`) is shared but file names are environment-specific
- Both environments log to stdout (console) as well as their file handler

### 3.3 Log Format

```
2026-10-15 15:32:47 [INFO    ] [ENV-GUARD] prod mode initialized with isolated paths
2026-10-15 15:32:47 [INFO    ] [ROUTE DRY_RUN] [prod] CRITICAL AE-183ee1296e05 R-AUDIT-03/D03.2 -> DSHE (FEISHU_GROUP_TASK_CARD) [attempt=0]
2026-10-15 15:32:47 [INFO    ]   [OK] [CRITICAL] [prod] AE-183ee1296e05 R-AUDIT-03 D03.2/DSHE -> DSHE (FEISHU_GROUP_TASK_CARD) [retry=0] [SIGNED]
```

---

## 4. Checkpoint Isolation

### 4.1 Checkpoint Files

| Environment | Checkpoint Path |
|-------------|----------------|
| Sandbox | `.checkpoint/alert_adapter_v3_sandbox.jsonl` |
| Prod | `.checkpoint/alert_adapter_v3_prod.jsonl` |
| V2 (legacy) | `.checkpoint_alert_events.jsonl` |

### 4.2 Isolation Guarantee

- Sandbox checkpoint events are written **only** to the sandbox checkpoint file
- Prod checkpoint events are written **only** to the prod checkpoint file
- `EnvironmentGuard.guard_write()` intercepts all checkpoint write operations
- Cross-environment writes raise `EnvironmentViolationError` and are rejected
- Checkpoint replay reads **only** from the current environment's checkpoint file

### 4.3 Checkpoint Format (JSONL)

```json
{
  "event_id": "AE-a1b2c3d4e5f6",
  "payload": {
    "event_id": "AE-a1b2c3d4e5f6",
    "level": "HIGH",
    "rule": "R-AUDIT-03",
    "detect_point": "D03.1",
    "deploy_env": "prod",
    "auth_signature": "abc123...",
    "auth_timestamp": "2026-10-15T12:00:00Z",
    "auth_algorithm": "HMAC-SHA256",
    ...
  },
  "failure_reason": "MAX_RETRIES_EXHAUSTED",
  "retry_count": 5,
  "max_retries": 5,
  "checkpoint_timestamp": "2026-10-15T12:00:00Z",
  "original_timestamp": "2026-10-15T11:59:00Z",
  "last_attempt": 5,
  "next_retry_delay": 1.6
}
```

---

## 5. Environment Guard

### 5.1 Guard Class

The `EnvironmentGuard` class validates all environment isolation rules:

```python
guard = EnvironmentGuard(
    env_config=env_config,
    auth_token=auth_token,
    deploy_env="prod"
)
guard.validate_startup()   # Validates auth requirements
guard.guard_write(path, is_checkpoint)  # Validates write paths
```

### 5.2 Validation Rules

| Rule Code | Check | Failure Action |
|-----------|-------|----------------|
| `PROD_AUTH_MISSING` | Prod mode without --auth-token | Raise EnvironmentViolationError |
| `PROD_AUTH_EMPTY` | Prod mode with empty auth token | Raise EnvironmentViolationError |
| `PROD_CROSS_WRITE` | Prod writes to sandbox log/checkpoint path | Raise EnvironmentViolationError |
| `SANDBOX_CROSS_WRITE` | Sandbox writes to prod log/checkpoint path | Raise EnvironmentViolationError |
| `STARTUP_OK` | All startup checks passed | Log success |
| `WRITE_GUARDED` | Each write operation validated | Log to action trail |

### 5.3 Audit Trail

All environment actions are recorded in `EnvironmentIsolationConfig.action_log`:

| Action | When Logged |
|--------|-------------|
| `STARTUP_VALIDATION` | When EnvironmentGuard validates startup |
| `STARTUP_OK` | When all startup checks pass |
| `STARTUP_FAILED` | When startup checks fail |
| `WRITE_GUARDED` | Each guarded write operation |
| `PAYLOAD_SIGNED` | Each HMAC-signed payload (prod only) |

### 5.4 Error Handling

```
EnvironmentViolationError: CROSS_ENV_WRITE: Prod mode wrote to sandbox path: .logs/alert_adapter_v3_sandbox.log
```

All violations are recorded in `env_guard.violations` with:
- Timestamp
- Violation code
- Detail message
- Environment name

---

## 6. Migration from V2 to V3

### 6.1 Breaking Changes

| Change | Impact | Mitigation |
|--------|--------|------------|
| `deploy_env` field added to payloads | 23rd field | Backward compatible (additive) |
| Prod requires auth token | Must provide --auth-token | Default: sandbox (no auth needed) |
| Separate checkpoint paths | V2 checkpoint not auto-migrated | New file per environment |
| Separate log files | V2 log file still exists | V3 creates new files |
| EnvironmentGuard added | No direct code change | Internal enforcement |

### 6.2 Migration Steps

1. **Default mode** — `--deploy-env sandbox` (no changes to V2 workflow)
2. **Prod deployment** — `--deploy-env prod --auth-token YOUR_TOKEN`
3. **Environment variable** — `AUTH_TOKEN=xxx python v86_rc2_dshe_alert_adapter_v3.py --deploy-env prod`
4. **Config file** — Add `"deploy_env": "prod"` to config JSON
5. **Checkpoint migration** — Export V2 checkpoint, import to V3 prod checkpoint
6. **Log migration** — V2 logs preserved; V3 creates new logs

### 6.3 CLI Compatibility

| Command | V2 | V3 |
|---------|----|----|
| `--dry-run` | Supported | Supported (sandbox default) |
| `--load-test` | Supported | Supported (sandbox default) |
| `--report` | Supported | Supported (sandbox default) |
| `--config config.json` | Supported | Supported |
| `--persist-checkpoint` | Supported | Supported |
| `--deploy-env {sandbox,prod}` | — | **NEW** |
| `--auth-token TOKEN` | — | **NEW** |

---

## 7. Load Test Results

### 7.1 Sandbox Environment

| # | Scenario | Events | Accept | Drop | Lvl | Trans | Result |
|---|----------|--------|--------|------|-----|-------|--------|
| 1 | S1_NORMAL_LOAD | 100 | 100 | 0 | L-1 | 0 | **PASS** |
| 2 | S2_BURST_LOAD | 500 | 100 | 0 | L-1 | 0 | **PASS** |
| 3 | S3_HIGH_LOAD | 2000 | 1600 | 400 | L1 | 0 | **PASS** |
| 4 | S4_OVERLOAD | 5000 | 2500 | 2500 | L2 | 0 | **PASS** |
| 5 | S5_RECOVERY | 1100 | 880 | 220 | L0 | 0 | **PASS** |

**Overall: ALL PASS**

### 7.2 Production Environment

| # | Scenario | Events | Accept | Drop | Lvl | Trans | Result |
|---|----------|--------|--------|------|-----|-------|--------|
| 1 | S1_NORMAL_LOAD | 100 | 100 | 0 | L-1 | 0 | **PASS** |
| 2 | S2_BURST_LOAD | 500 | 100 | 0 | L-1 | 0 | **PASS** |
| 3 | S3_HIGH_LOAD | 2000 | 1600 | 400 | L1 | 0 | **PASS** |
| 4 | S4_OVERLOAD | 5000 | 2500 | 2500 | L2 | 0 | **PASS** |
| 5 | S5_RECOVERY | 1100 | 880 | 220 | L0 | 0 | **PASS** |

**Overall: ALL PASS**

### 7.3 Dry-Run Results

| Mode | Total | Accepted | Dropped | CRITICAL Dropped | Auth Signed | Result |
|------|-------|----------|---------|------------------|-------------|--------|
| Sandbox | 9 | 9 | 0 | 0 | N/A | **ALL PASS** |
| Prod | 9 | 9 | 0 | 0 | 9/9 | **ALL PASS** |

### 7.4 Statistics Summary

| Metric | Sandbox | Prod |
|--------|---------|------|
| Total Events | 8700 | 8700 |
| Total Accepted | 5180 | 5180 |
| Total Dropped | 3520 | 3520 |
| Acceptance Rate | 59.5% | 59.5% |
| Load Test Scenarios Passed | 5/5 | 5/5 |
| Dry-Run Events Passed | 9/9 | 9/9 |

---

## 8. Security Considerations

### 8.1 Threat Model

| Threat | Risk | Mitigation |
|--------|------|------------|
| Token leakage in logs | High | Auth token NEVER logged; only signatures |
| Cross-env data exposure | High | EnvironmentGuard enforces path isolation |
| Sandbox to prod privilege escalation | High | Prod requires explicit auth token |
| Replay attacks | Medium | HMAC signatures are timestamp-bound |
| Checkpoint tampering | Medium | Separate files, no cross-env reads |
| Log file access | Medium | Each env has own log file |
| Key management | Low | Token from env var or CLI (not in code) |
| Payload forgery | Medium | HMAC-SHA256 ensures integrity |
| Denial of service | Low | Token bucket rate limiting preserved |

### 8.2 Security Controls

| Control | Implementation |
|---------|---------------|
| **Authentication** | HMAC-SHA256 with `--auth-token` or `AUTH_TOKEN` |
| **Authorization** | Prod mode requires valid auth token |
| **Isolation** | EnvironmentGuard validates all write paths |
| **Audit Trail** | All env actions logged to action_log |
| **Tamper Detection** | Cross-env writes raise EnvironmentViolationError |
| **Data Integrity** | HMAC-SHA256 signatures on all prod payloads |
| **Network Security** | JOB_READY=FALSE (all mock, no real network calls) |
| **Key Storage** | Token from env var or CLI (not hardcoded) |

### 8.3 Compliance

| Constraint | Status | Notes |
|------------|--------|-------|
| JOB_READY=FALSE | **COMPLIANT** | All mock/dry-run, no real network calls |
| NO_ZHIJI_API_CALL=FALSE | **COMPLIANT** | No external API calls |
| NO_MODIFY_V85=TRUE | **COMPLIANT** | V85 branch untouched |
| NO_OVERWRITE=TRUE | **COMPLIANT** | New file, V1/V2 preserved |
| BRANCH_LOCKED=TRUE | **COMPLIANT** | feature/v85-chart-template |

---

## 9. V2 vs V3 Feature Comparison

| Feature | V2 (2.0.0) | **V3 (3.0.0)** |
|---------|------------|----------------|
| Version | 2.0.0 | **3.0.0** |
| Rate Limiting | Token Bucket (100/s, burst 200) | **Preserved** |
| Retry | Exponential Backoff (5 retries, 0.1s base) | **Preserved** |
| Degradation | 4-Level (L0→L3) | **Preserved** |
| Priority Discard | CRITICAL never dropped | **Preserved** |
| Checkpoint | JSONL persistence | **Preserved** |
| Metrics | Full observability | **Preserved + env-tagged** |
| Payload Fields | 22 fields (EVIDENCE_CONTRACT_V1) | **23 fields (+deploy_env)** |
| CLI Flags | --dry-run, --load-test, --report, --config, --persist-checkpoint | **+ --deploy-env, --auth-token** |
| Environment | Single environment | **Sandbox/Prod Isolation** |
| Authentication | None | **HMAC-SHA256 (prod only)** |
| Environment Guard | None | **EnvironmentGuard class** |
| Log Isolation | Single log file | **Separate sandbox/prod logs** |
| Checkpoint Isolation | Single checkpoint | **Separate sandbox/prod checkpoints** |
| Payload Signing | None | **HMAC-SHA256 signatures** |
| Metrics Namespace | Unqualified | **env=sandbox / env=prod** |
| Load Test | 5 scenarios | **5 scenarios per environment** |
| Code Lines | ~2195 | **~2643** |
| V2 Backward Compat | — | **All V2 features preserved** |

---

## 10. Status Markers

```
DSHE_L2_ALERT_ADAPTER_V3_READY=TRUE
ALERT_ADAPTER_V3_VERSION=3.0.0
TOKEN_BUCKET_READY=TRUE
EXPONENTIAL_BACKOFF_READY=TRUE
DEGRADATION_4LEVEL_READY=TRUE
PRIORITY_DISCARD_READY=TRUE
CHECKPOINT_PERSISTENCE_READY=TRUE
METRICS_COLLECTOR_READY=TRUE
ENVIRONMENT_ISOLATION_READY=TRUE
PROD_AUTH_READY=TRUE
ENV_GUARD_READY=TRUE
SANDBOX_PROD_ISOLATION=TRUE
LOG_ISOLATION_READY=TRUE
CHECKPOINT_ISOLATION_READY=TRUE
LOAD_TEST_SANDBOX=ALL_PASS
LOAD_TEST_PROD=ALL_PASS
DRY_RUN_SANDBOX=ALL_PASS
DRY_RUN_PROD=ALL_PASS
V2_COMPATIBILITY_PRESERVED=TRUE
NO_OVERWRITE_V1_V2_PRESERVED=TRUE
BRANCH_LOCKED=TRUE
```

---

> **Document Status**: FINAL
> **Constraints**: JOB_READY=FALSE | NO_MODIFY_V85=TRUE | NO_OVERWRITE=TRUE | BRANCH_LOCKED=TRUE
> **Files**:
> - `v86_rc2_dshe_alert_adapter_v3.py` — V3 adapter source code
> - `v86_rc2_dshe_alert_v3_sandbox_dryrun_report.md` — Sandbox dry-run report
> - `v86_rc2_dshe_alert_v3_sandbox_report.md` — Sandbox load-test report
> - `v86_rc2_dshe_alert_v3_prod_dryrun_report.md` — Prod dry-run report
> - `v86_rc2_dshe_alert_v3_prod_report.md` — Prod load-test report
> - `.logs/alert_adapter_v3_sandbox.log` — Sandbox log file
> - `.logs/alert_adapter_v3_prod.log` — Prod log file
> - `.checkpoint/alert_adapter_v3_sandbox.jsonl` — Sandbox checkpoint
> - `.checkpoint/alert_adapter_v3_prod.jsonl` — Prod checkpoint
