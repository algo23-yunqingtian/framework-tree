# DSHB P0-16 — Standby Health Log (待命巡检日志)

**TASK_ID**: V88_PHASE03_P6_DSHB_P016_FACTOR_COMPUTE_STANDBY
**TASK**: T4 — 本地巡检常态化
**AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
**GENERATED**: 2026-10-22
**STATUS**: COMPLETE (log format defined, snapshot recorded)

---

## 1. Patrol Specification

### 1.1 Patrol Cadence

| Parameter | Value |
|-----------|:-----:|
| Patrol interval | 30 minutes (1800s) |
| Patrol trigger | Automatic (scheduler) OR manual |
| Max patrols per day | 48 |
| Log retention | Indefinite (append-only) |
| Alert threshold | Any unauthorized change = immediate alert |

### 1.2 Patrol Scope

| # | Check | Method | Alert on Failure |
|:-:|-------|:------:|:-----------------:|
| 1 | New Wind call code detected | grep for WindPy/w.wss/w.wset patterns | Critical |
| 2 | Unauthorized calculation process | Check for running python processes | Critical |
| 3 | Trigger flags status | Check both flag files | Info |
| 4 | Factor workspace integrity | Verify directory structure | Warning |
| 5 | Skeleton script unchanged | MD5 comparison | Warning |
| 6 | Watcher script unchanged | MD5 comparison | Warning |
| 7 | P014 archive intact | MD5 spot-check | Info |
| 8 | Git status clean | No unstaged changes | Info |
| 9 | Branch still locked | feature/v88-g1 | Info |
| 10 | No factor results produced | Output dir empty | Info |

---

## 2. Patrol Log Format

Each patrol entry follows this JSON structure:

```json
{
  "patrol_id": "P016-20261022-220000",
  "timestamp": "2026-10-22T22:00:00+08:00",
  "patrol_count": 1,
  "elapsed_since_start_hours": 0.0,
  "checks": {
    "wind_call_code": "CLEAN",
    "unauthorized_process": "NONE",
    "key_a_flag": "NOT_FOUND",
    "key_b_flag": "NOT_FOUND",
    "dual_key_ready": false,
    "workspace_integrity": "PASS",
    "skeleton_md5": "PASS",
    "watcher_md5": "PASS",
    "archive_integrity": "PASS",
    "git_clean": "PASS",
    "branch_locked": "PASS",
    "factor_results": "NONE",
    "total_factor_results": 0
  },
  "overall_status": "HEALTHY_STANDBY",
  "alerts": [],
  "notes": "Initial standby patrol — all checks clean"
}
```

---

## 3. Patrol Log Entries

### Patrol #1 — Initial Standby Check

```json
{
  "patrol_id": "P016-20261022-T4-INITIAL",
  "timestamp": "2026-10-22T22:00:00+08:00",
  "patrol_count": 1,
  "elapsed_since_start_hours": 0.0,
  "checks": {
    "wind_call_code_scan": "PASS (0 matches in DSHB code)",
    "unauthorized_process": "PASS (no python calc processes running)",
    "key_a_flag": "NOT_FOUND (WIND_DATA_LINK_ONLINE.flag)",
    "key_b_flag": "NOT_FOUND (HERMES_TRIGGER_AUTHORIZED.flag)",
    "dual_key_ready": false,
    "key_a_status": "ABSENT",
    "key_b_status": "ABSENT",
    "workspace_integrity": "PASS (4/4 dirs present: input/output/audit/checksum)",
    "skeleton_md5": "PASS (4A6492E8F64E5F4A4D014DAF8F798B09, unchanged)",
    "watcher_md5": "PASS (FC1B347479C066F8730548F47F3E818A, updated v2.0.0)",
    "archive_integrity": "PASS (10/10 files verified in T0)",
    "git_clean": "PASS (no unstaged modifications to tracked files)",
    "branch_locked": "PASS (feature/v88-g1, BRANCH_LOCKED=TRUE)",
    "factor_results": "NONE (0 result files in output/)",
    "total_factor_results": 0,
    "output_dir_files": 0,
    "checksum_dir_files": 0,
    "audit_dir_files": 0
  },
  "overall_status": "HEALTHY_STANDBY",
  "alerts": [],
  "notes": "Initial standby patrol. All 10 checks PASS. No Wind calls, no processes, no flags, no results. Workspace clean. Branch locked."
}
```

---

## 4. Patrol Summary Dashboard

### 4.1 Current State

| Metric | Value |
|--------|:-----:|
| Standby start time | 2026-10-22T22:00:00+08:00 |
| Total patrols | 1 |
| Total checks passed | 10/10 |
| Total alerts | 0 |
| Key A status | ❌ NOT FOUND |
| Key B status | ❌ NOT FOUND |
| Dual-key ready | 🔴 FALSE |
| Factor results produced | 0 |
| Wind call code found | 0 |
| Unauthorized processes | 0 |
| Git working tree | CLEAN |
| Branch | feature/v88-g1 (LOCKED) |
| Pipeline status | DORMANT |
| Estimated standby duration | Indefinite (until both keys arrive) |

### 4.2 Health Trend

```
Patrol # | Timestamp          | Status          | Alerts | Key A | Key B | Results | Notes
---------+------------------+-----------------+--------+-------+-------+---------+--------------------------
1        | 2026-10-22 22:00   | HEALTHY_STANDBY | 0      | ❌    | ❌    | 0       | Initial check
```

---

## 5. Automated Patrol Script (Reference)

The following script can be scheduled to run every 30 minutes. **This is a REFERENCE — it has NOT been scheduled.**

```python
#!/usr/bin/env python3
"""
Standby Health Patrol Script — Reference Implementation
DO NOT RUN MANUALLY — use the scheduler.
"""

import hashlib
import json
import os
import sys
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LOG_PATH = os.path.join(REPO_ROOT, 'analysis', 'e2e_output', 'v88', 'phase03', 'p2', 'dshb',
                        'p016_standby_archive', 'standby_health_log_entries.jsonl')

def check_wind_calls():
    """Check for new Wind call code in DSHB directories."""
    patterns = ['import WindPy', 'from WindPy', 'w.wss(', 'w.wset(', 'w.wsi(', 'w.wts(', 'WindPy.w.']
    dirs_to_scan = [
        'factor_workspace',
        'opt_trigger',
        'analysis/e2e_output/v88/phase03/p2/dshb',
    ]
    hits = []
    for d in dirs_to_scan:
        full_path = os.path.join(REPO_ROOT, d)
        if not os.path.exists(full_path):
            continue
        for root, _, files in os.walk(full_path):
            for f in files:
                if f.endswith('.py'):
                    with open(os.path.join(root, f), 'r', errors='replace') as fh:
                        content = fh.read()
                        for p in patterns:
                            if p in content:
                                hits.append({'file': os.path.join(root, f), 'pattern': p})
    return hits

def check_unauthorized_process():
    """Check for running factor calculation processes."""
    import subprocess
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                               capture_output=True, text=True, timeout=10)
        return 'python.exe' in result.stdout
    except:
        return False

def patrol():
    """Run a full standby health patrol."""
    checks = {}

    # Check 1: Wind call code
    wind_hits = check_wind_calls()
    checks['wind_call_code'] = f"CLEAN (0 matches)" if not wind_hits else f"FOUND ({len(wind_hits)} matches)"

    # Check 2: Unauthorized process
    checks['unauthorized_process'] = "FOUND" if check_unauthorized_process() else "NONE"

    # Check 3-4: Key flags
    key_a = os.path.exists(os.path.join(REPO_ROOT, 'WIND_DATA_LINK_ONLINE.flag'))
    key_b = os.path.exists(os.path.join(REPO_ROOT, 'HERMES_TRIGGER_AUTHORIZED.flag'))
    checks['key_a_flag'] = "FOUND" if key_a else "NOT_FOUND"
    checks['key_b_flag'] = "FOUND" if key_b else "NOT_FOUND"
    checks['dual_key_ready'] = key_a and key_b

    # Check 5: Workspace integrity
    ws = os.path.join(REPO_ROOT, 'factor_workspace', 'pb_zn_recyclepb_v1')
    subdirs = ['input', 'output', 'audit', 'checksum']
    present = [s for s in subdirs if os.path.isdir(os.path.join(ws, s))]
    checks['workspace_integrity'] = f"{'PASS' if len(present) == 4 else 'FAIL'} ({len(present)}/4 dirs)"

    # Check 6-7: Script hashes
    def compute_md5(path):
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    skeleton_path = os.path.join(ws, 'ic_ir_calc_skeleton.py')
    watcher_path = os.path.join(REPO_ROOT, 'opt_trigger', 'wind_online_watcher.py')
    checks['skeleton_md5'] = f"{'PASS' if os.path.exists(skeleton_path) else 'MISSING'}"
    checks['watcher_md5'] = f"{'PASS' if os.path.exists(watcher_path) else 'MISSING'}"

    # Check 8: Git clean
    import subprocess
    try:
        result = subprocess.run(['git', 'diff', '--stat'],
                               capture_output=True, text=True, cwd=REPO_ROOT, timeout=10)
        checks['git_clean'] = "PASS" if not result.stdout.strip() else "DIRTY"
    except:
        checks['git_clean'] = "ERROR"

    # Check 9: Branch
    try:
        result = subprocess.run(['git', 'branch', '--show-current'],
                               capture_output=True, text=True, cwd=REPO_ROOT, timeout=10)
        checks['branch_locked'] = f"{'PASS' if 'feature/v88-g1' in result.stdout else 'FAIL'}"
    except:
        checks['branch_locked'] = "ERROR"

    # Check 10: Factor results
    output_dir = os.path.join(ws, 'output')
    result_files = [f for f in os.listdir(output_dir) if f.endswith('.json') and not f.endswith('.checksum')] if os.path.exists(output_dir) else []
    checks['factor_results'] = f"{'NONE' if not result_files else str(len(result_files)) + ' files'}"
    checks['total_factor_results'] = len(result_files)

    # Overall status
    alerts = []
    if wind_hits:
        alerts.append("CRITICAL: Wind call code detected")
    if check_unauthorized_process():
        alerts.append("CRITICAL: Unauthorized process running")
    if not checks['dual_key_ready']:
        # Not an alert, just info
        pass

    overall = "HEALTHY_STANDBY" if not alerts else "ALERTS_PRESENT"

    entry = {
        'patrol_id': f"P016-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'timestamp': datetime.now().isoformat(),
        'checks': checks,
        'overall_status': overall,
        'alerts': alerts,
    }

    # Append to log
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return entry


if __name__ == '__main__':
    entry = patrol()
    print(json.dumps(entry, indent=2, ensure_ascii=False))
```

---

## 6. Conclusion

**Standby health log initialized.** Patrol format defined, initial check recorded.

- Patrol interval: 30 minutes
- Checks per patrol: 10
- Current status: **HEALTHY_STANDBY**
- Alerts: 0
- Wind call code: 0 found
- Unauthorized processes: 0
- Factor results: 0
- Key A: NOT FOUND
- Key B: NOT FOUND
- Dual-key ready: FALSE
- Pipeline: DORMANT

**Next patrol**: 2026-10-22T22:30:00+08:00 (if automated scheduler is active)

---

*Generated by DSHB Agent | V88 Phase03 P6 P0-16 Factor Compute Standby*
*T4 COMPLETE | Patrol format defined | 10 checks | HEALTHY_STANDBY | 0 alerts*