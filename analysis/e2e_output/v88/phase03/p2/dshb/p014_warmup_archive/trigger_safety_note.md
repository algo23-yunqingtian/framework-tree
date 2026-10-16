# Trigger Safety Note — WIND_DATA_LINK_ONLINE Watcher

> **TASK_ID**: V88_PHASE03_P4_DSHB_P014_READY_FOR_FACTOR_CALC
> **AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **GENERATED**: 2026-10-22T22:10:00
> **JOB**: V88_PHASE03_P4_DSHB_P014_READY_FOR_FACTOR_CALC / T4
> **STATUS**: ✅ COMPLETE — Watcher deployed, default SLEEP, no flag = no action

---

## 1. Watcher Deployment

| Property | Value |
|----------|-------|
| Script | `opt_trigger/wind_online_watcher.py` |
| Lines | ~320 |
| Default state | **SLEEP** (indefinite) |
| Poll interval | 300s (5 minutes) |
| Flag path | `WIND_DATA_LINK_ONLINE.flag` (repo root) |
| Factor calc path | `factor_workspace/pb_zn_recyclepb_v1/ic_ir_calc_skeleton.py` |
| Status file | `opt_trigger/wind_watcher_status.json` |
| Log file | `opt_trigger/wind_watcher.log` |

---

## 2. Safety Guarantees

### 2.1 Default Sleep Behavior

```
┌─────────────────────────────────────────────────────┐
│  WIND_ONLINE_WATCHER.py                              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  START → check_flag_exists()                         │
│    │                                                  │
│    ├── FLAG NOT FOUND ──→ log → SLEEP 300s → retry  │
│    │                                                  │
│    └── FLAG FOUND ──→ precheck()                     │
│                              │                        │
│                              ├── FAIL ──→ log →      │
│                              │         SLEEP 300s    │
│                              │         retry          │
│                              │                        │
│                              └── PASS ──→ invoke     │
│                                        calc entry    │
│                                        (gated)      │
└─────────────────────────────────────────────────────┘
```

**Key guarantee**: Without `WIND_DATA_LINK_ONLINE.flag`, the watcher **sleeps indefinitely**. No action is taken. No API call is made. No gateway is bypassed.

### 2.2 What the Watcher Does NOT Do

| Prohibition | Enforcement |
|-------------|:-----------:|
| ❌ Import WindPy | Verified: 0 WindPy imports |
| ❌ Call any Wind API | Verified: 0 Wind calls |
| ❌ Pull external data | Verified: no network calls |
| ❌ Execute git push | Verified: 0 git commands |
| ❌ Modify files outside designated output | Verified: only status/log files |
| ❌ Bypass HERMES release gate | Verified: no gate logic modified |
| ❌ Bypass dual-lock policy | Verified: no merge logic |
| ❌ Start factor calculation without flag | Verified: flag is sole gate |
| ❌ Call factor calculation without precheck | Verified: precheck is mandatory |
| ❌ Execute any hardcoded API call | Verified: skeleton is inert |

### 2.3 Defense in Depth

| Layer | Gate | Mechanism |
|:----:|------|-----------|
| 1 | Watcher loop | Sleeps until flag found |
| 2 | Flag validation | Checks existence, size, age |
| 3 | Pre-check | Validates workspace, no hardcoded Wind calls, no auto-push |
| 4 | Factor calc skeleton | Re-checks flag (independent verification) |
| 5 | Factor calc stub | Returns STUB_INERT without real data |
| 6 | HERMES gate | Dual-lock policy not bypassed |

---

## 3. Flag Detection Protocol

```python
# Flag must satisfy ALL conditions:
1. File exists at: REPO_ROOT/WIND_DATA_LINK_ONLINE.flag
2. File is non-empty (> 0 bytes)
3. File size <= 1 MB
4. File age >= 0 seconds (configurable)

# If any condition fails → SLEEP_AND_RETRY
# If all pass → PROCEED_TO_PRECHECK
```

### Flag File Example

```
WIND_DATA_LINK_ONLINE.flag — Example content (not required):

# WIND_DATA_LINK_ONLINE.flag
# Data link status: ONLINE
# Authorized at: 2026-10-23T08:00:00
# Authorized by: HERMES
# Data source: Wind terminal
# Scope: PB, ZN, Recycle-PB factors only
# Expiry: 2026-10-30T00:00:00
# Notes: First batch of non-ferrous metals factor small-sample
```

The flag file content is **not parsed** by the watcher — only existence, size, and age are checked. Content validation is left to downstream systems.

---

## 4. Pre-Check Protocol

Before allowing factor calculation, the watcher runs these checks:

| # | Check | Method | Failure Action |
|:-:|-------|--------|:--------------:|
| 1 | Skeleton exists | `os.path.exists(FACTOR_CALC_PATH)` | FAIL → SLEEP |
| 2 | Workspace input/ | `os.path.isdir(...)` | FAIL → SLEEP |
| 3 | Workspace output/ | `os.path.isdir(...)` | FAIL → SLEEP |
| 4 | Workspace audit/ | `os.path.isdir(...)` | FAIL → SLEEP |
| 5 | Workspace checksum/ | `os.path.isdir(...)` | FAIL → SLEEP |
| 6 | No WindPy imports in skeleton | Pattern scan | FAIL → SLEEP |
| 7 | No auto-push in skeleton | Pattern scan | FAIL → SLEEP |

**All 7 checks must pass** before factor calculation is invoked.

---

## 5. Operational Modes

| Mode | Command | Behavior |
|------|---------|----------|
| Watch (default) | `python wind_online_watcher.py` | Sleep until flag found, then calc |
| Check only | `python wind_online_watcher.py --check-only` | Check flag once, exit |
| Custom interval | `python wind_online_watcher.py --interval 60` | Poll every 60s |
| Limited polls | `python wind_online_watcher.py --max-polls 10` | Exit after 10 polls |

---

## 6. Safety Assertion

> **✅ Trigger safety verified.**
>
> - **No flag = No action** — watcher sleeps indefinitely without `WIND_DATA_LINK_ONLINE.flag`
> - **No WindPy imports** — verified in both watcher and skeleton scripts
> - **No auto-push** — no git commands in any deployed script
> - **No API calls** — no external network calls of any kind
> - **No gateway bypass** — HERMES release gate and dual-lock policy untouched
> - **Defense in depth** — 6 independent safety layers
> - **Skeleton is inert** — returns STUB_INERT without real data
>
> **Status**: TRIGGER_SAFE — watcher dormant, awaiting flag

---

*Generated by DSHB Agent | V88 Phase03 P4 T4 Trigger Safety Note*
*6 safety layers | No flag = No action | No WindPy | No auto-push | No API calls*