# DSHB P0-16 — Trigger Second Check (Dual-Key Logic Verification)

**TASK_ID**: V88_PHASE03_P6_DSHB_P016_FACTOR_COMPUTE_STANDBY
**TASK**: T2 — 双钥匙逻辑二次校验
**AGENT**: DSHB | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
**GENERATED**: 2026-10-22
**STATUS**: COMPLETE

---

## 1. Overview

This document records the **second verification** of the dual-key trigger logic in `opt_trigger/wind_online_watcher.py`. The dual-key mechanism requires BOTH `WIND_DATA_LINK_ONLINE.flag` AND `HERMES_TRIGGER_AUTHORIZED.flag` to be present before any factor calculation is authorized.

**Watcher version**: v2.0.0 (upgraded from v1.0.0 during P016)
**Script path**: `opt_trigger/wind_online_watcher.py`
**File size**: 22,717 bytes
**MD5**: `FC1B347479C066F8730548F47F3E818A`
**SHA256**: `03DF7473A600600DE16BEE332DC2ECC5C5E63A1CB697874F3966AD0EB0715C05`

---

## 2. Dual-Key Decision Matrix — Implemented

| Key A (WIND_DATA_LINK_ONLINE.flag) | Key B (HERMES_TRIGGER_AUTHORIZED.flag) | Decision | Action |
|:---:|:---:|:---:|:---:|
| ❌ ABSENT | ❌ ABSENT | `NO_FLAGS_SLEEP` | Sleep, no action |
| ✅ FOUND | ❌ ABSENT | `KEY_A_ONLY_SLEEP` | **Sleep + warning log** |
| ❌ ABSENT | ✅ FOUND | `KEY_B_ONLY_SLEEP` | **Sleep + warning log** |
| ✅ FOUND | ✅ FOUND | `DUAL_KEY_AUTHORIZED` | Proceed to precheck |

### 2.1 Implementation Verification

**Function**: `check_dual_flags()` (line ~193-260)

```python
def check_dual_flags():
    """
    Dual-key trigger check — BOTH flags must be present to authorize computation.

    Decision matrix:
    ┌──────────┬──────────────┬──────────────────────────────────────────┐
    │ Key A    │ Key B        │ Action                                   │
    ├──────────┼──────────────┼──────────────────────────────────────────┤
    │ ABSENT   │ ABSENT       │ SLEEP — no flags, no action              │
    │ FOUND    │ ABSENT       │ SLEEP — single key, warning log only     │
    │ ABSENT   │ FOUND        │ SLEEP — single key, warning log only     │
    │ FOUND    │ FOUND        │ PROCEED — dual-key authorized            │
    └──────────┴──────────────┴──────────────────────────────────────────┘
    """
    label_a = 'WIND_DATA_LINK_ONLINE.flag'
    label_b = 'HERMES_TRIGGER_AUTHORIZED.flag'
    a_present, a_info = check_single_flag(FLAG_PATH_KEY_A, label_a)
    b_present, b_info = check_single_flag(FLAG_PATH_KEY_B, label_b)
    dual_ready = a_present and b_present
    # ... decision logic ...
```

**✅ VERIFIED**: The function checks BOTH flags independently and only returns `dual_ready=True` when BOTH are present.

### 2.2 Single-Key Warning Behavior

When only Key A is present:
```python
elif a_present and not b_present:
    decision = 'KEY_A_ONLY_SLEEP'
    message = (
        f'SINGLE KEY (A only): {label_a} present but {label_b} NOT FOUND. '
        f'Calculation PROHIBITED. SLEEPING with warning log.'
    )
    append_log(f'WARNING: Key A ({label_a}) present but Key B ({label_b}) missing — SLEEP')
```

**✅ VERIFIED**: Single key triggers warning log, NOT calculation.

When only Key B is present:
```python
elif not a_present and b_present:
    decision = 'KEY_B_ONLY_SLEEP'
    message = (
        f'SINGLE KEY (B only): {label_b} present but {label_a} NOT FOUND. '
        f'Calculation PROHIBITED. SLEEPING with warning log.'
    )
    append_log(f'WARNING: Key B ({label_b}) present but Key A ({label_a}) missing — SLEEP')
```

**✅ VERIFIED**: Single key triggers warning log, NOT calculation.

---

## 3. Watch Loop Integration — `watch()` Function

### 3.1 Entry Point

The `watch()` function (line ~349) is the main entry point that:
1. Starts with `DUAL-KEY MODE` banner
2. Logs BOTH key paths
3. Calls `check_dual_flags()` on every poll
4. Only proceeds when `dual_ready=True`

```python
dual_result = check_dual_flags()
decision = dual_result['decision']
dual_ready = dual_result['dual_ready']

if not dual_ready:
    # SLEEP with decision-specific message
    logger.info(f"Decision: {decision}")
    logger.info(f"  {dual_result['message']}")
    # ...
    time.sleep(POLL_INTERVAL_SECONDS)
    continue

# ---- DUAL KEY AUTHORIZED ----
# Only reached when BOTH flags present
```

**✅ VERIFIED**: The loop calls `check_dual_flags()` and only proceeds when `dual_ready=True`.

### 3.2 Exit States

| Poll Count | Decision | `dual_ready` | Exit State |
|:---:|:---:|:---:|:---:|
| Any | `NO_FLAGS_SLEEP` | False | Sleep & retry |
| Any | `KEY_A_ONLY_SLEEP` | False | Sleep & retry |
| Any | `KEY_B_ONLY_SLEEP` | False | Sleep & retry |
| Any | `DUAL_KEY_AUTHORIZED` | True | Proceed to precheck |
| MAX_POLLS | Any | Any | `TIMEOUT_<decision>` |
| 1 | Any | Any | `<decision>_ONESHOT` |

---

## 4. Safety Properties Verification

### 4.1 No WindPy Import

```python
# ✅ VERIFIED: No WindPy import anywhere in the script
import json    # ✅ Standard library
import logging # ✅ Standard library
import os      # ✅ Standard library
import sys     # ✅ Standard library
import time    # ✅ Standard library
from datetime import datetime  # ✅ Standard library
```

**Result**: 0 WindPy imports, 0 Wind API calls, 0 external API calls.

### 4.2 No Auto-Git-Push

```python
# ✅ VERIFIED: No git commands in the script
# No 'git push', 'git commit', 'git add' strings
# No subprocess.run.*git, os.system.*git patterns
```

**Result**: 0 git commands. The watcher NEVER pushes to any remote.

### 4.3 No Hardcoded Wind Calls

The precheck function validates the skeleton script:
```python
wind_patterns = ['import WindPy', 'from WindPy', 'import wind', 'from wind',
                 'w.wss(', 'w.wset(', 'w.wsi(', 'w.wts(', 'WindPy.w.']
```

**Result**: Precheck would FAIL if any Wind call is found in the skeleton.

### 4.4 Gateway Bypass Prevention

```python
# ✅ VERIFIED: The watcher NEVER bypasses HERMES gate
# Key B (HERMES_TRIGGER_AUTHORIZED.flag) is MANDATORY
# Without Key B, calculation is PROHIBITED
# The watcher does not have a "force" or "override" mode
```

---

## 5. Current Key Status

| Key | Flag File | Status | Present |
|-----|-----------|:------:|:-------:|
| Key A | `WIND_DATA_LINK_ONLINE.flag` | ❌ NOT FOUND | False |
| Key B | `HERMES_TRIGGER_AUTHORIZED.flag` | ❌ NOT FOUND | False |
| **Dual-ready** | — | **🔴 FALSE** | **No** |

**Current decision**: `NO_FLAGS_SLEEP`
**Current action**: SLEEP — no flags, no action

---

## 6. v1.0 → v2.0 Upgrade Summary

| Property | v1.0.0 (P4) | v2.0.0 (P016) |
|----------|:-----------:|:-------------:|
| Key count | 1 (Key A only) | 2 (Key A + Key B) |
| Dual-key check | ❌ No | ✅ Yes |
| Single-key behavior | N/A | Sleep + warning log |
| `check_dual_flags()` | ❌ No | ✅ Yes |
| `check_single_flag()` | Inline only | ✅ Extracted function |
| Decision matrix | Single key | 4-state matrix |
| Warning on single key | ❌ No | ✅ Yes |
| Auto-git-push | 0 | 0 (unchanged) |
| WindPy imports | 0 | 0 (unchanged) |
| External API calls | 0 | 0 (unchanged) |

---

## 7. Conclusion

**The dual-key trigger logic is VERIFIED and CORRECTLY IMPLEMENTED.**

- Only BOTH flags present → proceed to calculation
- Single Key A only → sleep + warning log
- Single Key B only → sleep + warning log
- No flags → sleep
- 0 WindPy imports
- 0 auto-git-push commands
- 0 hardcoded Wind calls
- Gateway bypass: 0 paths (Key B is mandatory)

**The watcher is DORMANT in SLEEP mode.** No calculation will occur until both flags are placed at the repository root.

---

*Generated by DSHB Agent | V88 Phase03 P6 P0-16 Factor Compute Standby*
*T2 COMPLETE | Dual-key logic verified | Watcher v2.0.0 deployed | 0 WindPy, 0 auto-push, 0 API calls*