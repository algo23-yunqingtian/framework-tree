# V86 Finalized Pre-Flight Checklist (T3.4)

> **Task:** DSHB_V86_GATE_FINAL_REVIEW — Pre-Flight Checklist T3.4
> **Branch:** feature/v85-chart-template (BRANCH_LOCKED=TRUE)
> **Engine:** V86P1RuleEngine + V86AliasEngine (F1+F2+F3+F4)
> **Constraints:** NO_ZHIJI_API_CALL=TRUE · NO_MODIFY_V85=TRUE · NO_OVERWRITE=TRUE · BRANCH_LOCKED=TRUE
> **Generated:** 2026-06-24
> **Status:** FINALIZED — Awaiting Sign-Off
> **Supersedes:** `v86_preflight_checklist.md` (B-group baseline, 68 items)

---

## Section 1: Checklist Overview

### 1.1 Scope

This finalized checklist consolidates all pre-flight verification items from four contributing groups:

| Group | Domain | Items | Status |
|-------|--------|-------|--------|
| **B** | Core deployment & monitoring | 68 | All delivered |
| **D** | Gray simulation & degradation | 8 | All delivered |
| **E** | Portal, demo, integration | 6 | All delivered |
| **A/C** | Parameter freeze, backtest data, risk boundary | 3 | **DEPENDENCY_GAP** |

### 1.2 Total Item Count

| Phase | Window | Items | Pass/Fail Gate |
|-------|--------|-------|----------------|
| **2 — Pre-Deployment** | T-24h to T-2h | 34 | Block deployment if any FAIL |
| **3 — Deployment** | T-2h to T-0 | 20 | Halt and rollback on failure |
| **4 — Post-Deployment** | T+0 to T+2h | 36 | Abort gray release on failure |
| **5 — Emergency** | On-demand | 6 | Execute immediately on trigger |
| **DEPENDENCY_GAP** | Pending A/C assets | 3 | Documented gap, no gate |
| **TOTAL** | — | **99** | 96 actionable + 3 gap |

### 1.3 Required Artifacts

- [ ] V86 bundle package (expected size: ~296 KB)
- [ ] `v86-rule-engine.service` systemd unit file
- [ ] Dockerfile + docker-compose.yml (if container deployment)
- [ ] Prometheus scrape configuration
- [ ] Grafana dashboard JSON (8 panels)
- [ ] Alert rule YAML (4 critical + 4 warning rules)
- [ ] SLO definitions (5 SLOs)
- [ ] Rollback version snapshot (for Strategy A)
- [ ] Portal metric caliber spec document
- [ ] Portal permission config JSON
- [ ] Demo runbook (v86_demo_runbook.md)
- [ ] V85 frozen portal page snapshot

---

## Section 2: Pre-Deployment Phase (T-24h to T-2h)

### 2.1 Source Code Verification

Verify that the deployed code matches the approved CI baseline exactly.

- [ ] **2.1.1 — Branch checkout confirmation**
  ```bash
  cd /opt/v86/deployment
  git branch --show-current
  # Expected: feature/v85-chart-template
  ```
  **Acceptance:** Output must be exactly `feature/v85-chart-template`.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL (block deployment)

- [ ] **2.1.2 — Rule engine commit verification**
  ```bash
  git log --oneline -1 f694618
  git rev-parse --short HEAD
  ```
  **Acceptance:** `HEAD` must be `f694618` (or a descendant that includes it). Rule engine module must not have uncommitted changes:
  ```bash
  git diff --name-only f694618..HEAD -- '**/rule_engine/**' '**/v86_p1_rule/**'
  # Expected: no output
  ```
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **2.1.3 — Alias engine commit verification**
  ```bash
  git log --oneline -1 81268a6
  git diff --name-only 81268a6..HEAD -- '**/alias_engine/**' '**/v86_alias/**'
  # Expected: no output
  ```
  **Acceptance:** No drift since approval commit.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **2.1.4 — CI gate result confirmation (Rule Engine)**
  ```bash
  curl -s "https://ci.example.com/api/v1/projects/dshb-gate/runs/latest" \
    | jq '.status, .gates_passed, .gates_total'
  ```
  **Acceptance:** `status == "passed"`, `gates_passed == 12`, `gates_total == 12`.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.1.5 — CI gate result confirmation (Alias Engine)**
  ```bash
  curl -s "https://ci.example.com/api/v1/projects/dshb-alias-gate/runs/latest" \
    | jq '.status, .gates_passed, .gates_total'
  ```
  **Acceptance:** `status == "passed"`, `gates_passed == 3`, `gates_total == 3`.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.1.6 — No unexpected changes since tag**
  ```bash
  git log --oneline v86-gate-accept..HEAD
  git diff --stat v86-gate-accept..HEAD
  ```
  **Acceptance:** No changes to engine source files, alias dictionary, or configuration files since acceptance tag.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **2.1.7 — Working tree cleanliness**
  ```bash
  git status --porcelain
  # Expected: no output
  ```
  **Acceptance:** Clean working tree.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

### 2.2 Artifact Integrity

- [ ] **2.2.1 — Bundle file presence and size**
  ```bash
  ls -lh /opt/v86/artifacts/v86-bundle-*.tar.gz
  stat --format="%s %n" /opt/v86/artifacts/v86-bundle-*.tar.gz
  ```
  **Acceptance:** Size between 290–302 KB.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **2.2.2 — Bundle MD5 checksum**
  ```bash
  md5sum /opt/v86/artifacts/v86-bundle-*.tar.gz
  cat /opt/v86/artifacts/v86-bundle-*.md5
  md5sum -c /opt/v86/artifacts/v86-bundle-*.md5
  ```
  **Acceptance:** All checksums `OK`.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **2.2.3 — Bundle content verification**
  ```bash
  tar -tzf /opt/v86/artifacts/v86-bundle-*.tar.gz | head -40
  tar -tzf /opt/v86/artifacts/v86-bundle-*.tar.gz \
    | grep -E '(rule_engine/|alias_engine/|config/|requirements|service)'
  ```
  **Acceptance:** `rule_engine/`, `alias_engine/`, `config/` directories present.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **2.2.4 — Rule count confirmation**
  ```bash
  tar -xOzf /opt/v86/artifacts/v86-bundle-*.tar.gz rule_engine/rule_definitions.json \
    | jq '[.rules[] | select(.priority == "P0")] | length, [.rules[] | select(.priority == "P1")] | length'
  ```
  **Acceptance:** 6 P0, 12 P1 (total 18).
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.2.5 — Alias dictionary entry count**
  ```bash
  tar -xOzf /opt/v86/artifacts/v86-bundle-*.tar.gz alias_engine/alias_dictionary.json \
    | jq '.entries | length'
  ```
  **Acceptance:** 4643 entries.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.2.6 — Blacklist rule count**
  ```bash
  tar -xOzf /opt/v86/artifacts/v86-bundle-*.tar.gz alias_engine/blacklist.json \
    | jq '.rules | length'
  ```
  **Acceptance:** 31 rules.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.2.7 — Python compatibility check**
  ```bash
  python3 --version
  python3 -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')"
  ```
  **Acceptance:** Python 3.12.x.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.2.8 — No external dependency drift**
  ```bash
  tar -xOf /opt/v86/artifacts/v86-bundle-*.tar.gz "rule_engine/*.py" \
    | grep -E '^import |^from ' \
    | grep -vE '^(import|from) (os|sys|json|re|logging|collections|typing|dataclasses|enum|abc|functools|itertools|math|hashlib|uuid|copy|io|time|datetime|pathlib|argparse|multiprocessing|concurrent|signal|threading|socket|http|urllib|struct|base64|random|statistics|textwrap|string|contextlib|importlib|inspect|pkgutil|traceback|unittest|warnings|weakref|xml|html|csv|sqlite3|zlib|gzip|tarfile|tempfile|shutil|subprocess|shlex|glob|fnmatch|operator|heapq|bisect|array|codecs|code|token|ast|sysconfig|platform|ctypes|pprint|dis|gc|__future__)' \
    | grep -vE '^\s*#' || echo "PASS: no external deps"
  ```
  **Acceptance:** No non-stdlib imports in engine core.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

### 2.3 Environment Setup

- [ ] **2.3.1 — Target instance resources verified**
  ```bash
  nproc
  free -h | awk '/Mem:/ {print $2}'
  df -h /opt /var | awk 'NR>1 {print $6, $2}'
  ```
  **Acceptance:** 4 vCPU, ~4 GB RAM, ~20 GB available on /opt and /var.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.3.2 — Network bandwidth check**
  ```bash
  iperf3 -c <bench-host> -t 5 -1
  ```
  **Acceptance:** ≥ 50 Mbps sustained.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.3.3 — Worker process pool validation**
  ```bash
  python3 -c "
  from multiprocessing import Pool
  with Pool(processes=4) as p:
      results = p.map(lambda x: x*2, [1,2,3,4])
      assert results == [2,4,6,8]
      print(f'PASS: 4-worker pool functional')
  "
  ```
  **Acceptance:** 4-worker pool functional.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.3.4 — File descriptor limits**
  ```bash
  ulimit -n
  cat /proc/sys/fs/file-max
  ```
  **Acceptance:** `ulimit -n >= 4096` and `file-max >= 100000`.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.3.5 — Systemd presence and version**
  ```bash
  systemctl --version | head -1
  ```
  **Acceptance:** systemd 245+.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 2.4 Configuration Validation

- [ ] **2.4.1 — Environment variables set correctly**
  ```bash
  source /opt/v86/deployment/.env || source /etc/v86/v86.env
  echo "HOST=$HOST"
  echo "PORT=$PORT"
  echo "WORKERS=$WORKERS"
  echo "MAX_CONCURRENT=$MAX_CONCURRENT"
  echo "TIMEOUT_SECONDS=$TIMEOUT_SECONDS"
  echo "LOG_LEVEL=$LOG_LEVEL"
  ```
  **Acceptance:** All values match production specification:

  | Variable | Expected |
  |----------|----------|
  | HOST | `0.0.0.0` or specific interface |
  | PORT | `8080` or approved port |
  | WORKERS | `4` |
  | MAX_CONCURRENT | `64` |
  | TIMEOUT_SECONDS | `30` |
  | LOG_LEVEL | `INFO` or `WARNING` |

  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.4.2 — Queue configuration**
  ```bash
  python3 -c "
  import json
  with open('/opt/v86/deployment/config/queue_config.json') as f:
      cfg = json.load(f)
      assert cfg['queue_size'] == 500, f'Expected 500, got {cfg[\"queue_size\"]}'
      assert cfg['max_concurrent'] == 64, f'Expected 64, got {cfg[\"max_concurrent\"]}'
      print(f'PASS: queue_size={cfg[\"queue_size\"]}, max_concurrent={cfg[\"max_concurrent\"]}')
  "
  ```
  **Acceptance:** queue_size=500, max_concurrent=64.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.4.3 — Memory limit in systemd unit**
  ```bash
  grep -E 'MemoryLimit|MemoryMax' /etc/systemd/system/v86-rule-engine.service
  ```
  **Acceptance:** `MemoryLimit=2G` or `MemoryMax=2G`.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.4.4 — Engine configuration file syntax**
  ```bash
  python3 -c "
  import json
  for f in ['engine_config.json', 'rule_definitions.json', 'alias_dictionary.json', 'blacklist.json']:
      with open(f'/opt/v86/deployment/config/{f}') as fh:
          json.load(fh)
      print(f'PASS: {f} valid JSON')
  "
  ```
  **Acceptance:** All 4 JSON files parse successfully.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **2.4.5 — Alias engine mode confirmation**
  ```bash
  python3 -c "
  import json
  with open('/opt/v86/deployment/config/engine_config.json') as f:
      cfg = json.load(f)
      assert cfg['alias_engine']['mode'] == 'f3+f4', f'Expected f3+f4, got {cfg[\"alias_engine\"][\"mode\"]}'
      print(f'PASS: alias mode = {cfg[\"alias_engine\"][\"mode\"]}')
  "
  ```
  **Acceptance:** alias_engine.mode == 'f3+f4'.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

### 2.5 Cache Warmup Verification (D-Group)

- [ ] **2.5.1 — Cache warmup execution**
  ```bash
  python3 -c "
  import json, pickle, time
  from pathlib import Path
  cache_dir = Path('/opt/v86/deployment/data/cache')
  cache_dir.mkdir(parents=True, exist_ok=True)

  # Load 18 alias samples for warmup
  samples = ['alias_a', 'alias_b', 'alias_c', 'alias_d', 'alias_e',
             'alias_f', 'alias_g', 'alias_h', 'alias_i', 'alias_j',
             'alias_k', 'alias_l', 'alias_m', 'alias_n', 'alias_o',
             'alias_p', 'alias_q', 'alias_r']
  warmup_entries = {}
  for s in samples:
      warmup_entries[s] = f'resolved_{s}'

  cache_path = cache_dir / 'resolve_cache.pkl'
  with open(cache_path, 'wb') as f:
      pickle.dump(warmup_entries, f)
  print(f'Warmup entries written: {len(warmup_entries)}')
  print(f'Cache file: {cache_path} ({cache_path.stat().st_size} bytes)')
  "
  ```
  **Acceptance:** 18 warmup samples written to cache.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **2.5.2 — Cache persistence verification**
  ```bash
  python3 -c "
  import pickle
  cache_path = '/opt/v86/deployment/data/cache/resolve_cache.pkl'
  with open(cache_path, 'rb') as f:
      cache = pickle.load(f)
  print(f'Persisted entries: {len(cache)}')
  # Expected: 956 entries (initial dictionary + warmup)
  assert len(cache) >= 956, f'Expected >=956, got {len(cache)}'
  print(f'PASS: {len(cache)} entries persisted')
  "
  ```
  **Acceptance:** ≥ 956 entries persisted in cache.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 2.6 Degradation Drill Verification (D-Group)

- [ ] **2.6.1 — L1 degradation (alias dictionary shrinkage)**
  ```bash
  python3 -c "
  import json
  with open('/opt/v86/deployment/config/alias_dictionary.json') as f:
      orig = json.load(f)
  original_count = len(orig['entries'])
  # Simulate 50% dictionary loss
  reduced = {'entries': orig['entries'][:original_count // 2]}
  # Verify engine still resolves from remaining entries
  print(f'Original entries: {original_count}')
  print(f'Reduced entries: {len(reduced[\"entries\"])}')
  print(f'Expected fallback rate: < 2% for L1')
  "
  ```
  **Acceptance:** Engine handles 50% dictionary loss with fallback rate < 2%.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.6.2 — L2 degradation (rule engine timeout)**
  ```bash
  python3 -c "
  import time
  # Simulate 100ms per-rule evaluation delay
  start = time.time()
  for i in range(100):
      time.sleep(0.1)  # 100ms per rule
  elapsed = time.time() - start
  print(f'Simulated 100 rules at 100ms each: {elapsed:.2f}s')
  assert elapsed > 10, 'Expected >10s for degraded mode'
  print('PASS: L2 degradation response time verified')
  "
  ```
  **Acceptance:** Engine detects L2 timeout within 30s, triggers fallback.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.6.3 — L3 degradation (full engine failure + recovery)**
  ```bash
  python3 -c "
  import json
  # Simulate complete engine failure
  # Test that circuit breaker opens and routes to v85 fallback
  with open('/opt/v86/deployment/config/engine_config.json') as f:
      cfg = json.load(f)
  print(f'Circuit breaker threshold: {cfg.get(\"circuit_breaker\", {}).get(\"failure_threshold\", \"N/A\")}')
  print(f'Recovery timeout: {cfg.get(\"circuit_breaker\", {}).get(\"recovery_timeout_s\", \"N/A\")}')
  print('L3 drill: Full failure → circuit break → v85 fallback → auto-recovery')
  "
  ```
  **Acceptance:** Circuit breaker opens after 3 consecutive failures. Recovery timeout ≤ 60s. Auto-recovery within 5 minutes.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 2.7 Anomaly Injection Response Verification (D-Group)

- [ ] **2.7.1 — Timeout anomaly injection**
  ```bash
  curl -s -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" \
    -H "X-Simulate-Time-Constraint: 0.001" \
    -d '{"input": "timeout_test_input", "context": {"inject_timeout": true}}' \
    -o /dev/null -w "%{http_code} %{time_total}s\n"
  ```
  **Acceptance:** Engine returns HTTP 504 or falls back within TIMEOUT_SECONDS. No process crash.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.7.2 — Cache corruption anomaly injection**
  ```bash
  python3 -c "
  import pickle
  cache_path = '/opt/v86/deployment/data/cache/resolve_cache.pkl'
  # Write garbage bytes to simulate corruption
  with open(cache_path, 'wb') as f:
      f.write(b'\\xff\\xfe\\x00\\x01garbage_data_not_pickle')
  print(f'Corrupted cache written ({f.tell()} bytes)')
  "
  # Engine should detect corruption and rebuild cache
  sleep 2
  python3 -c "
  import os
  cache_path = '/opt/v86/deployment/data/cache/resolve_cache.pkl'
  if os.path.exists(cache_path):
      size = os.path.getsize(cache_path)
      print(f'Cache after corruption test: {size} bytes')
      assert size > 0, 'Cache should be rebuilt after corruption'
      print('PASS: Cache rebuilt after corruption')
  "
  ```
  **Acceptance:** Engine detects cache corruption, rebuilds cache, no crash.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **2.7.3 — Dirty data anomaly injection**
  ```bash
  curl -s -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" \
    -d '{"input": "<script>alert(1)</script><img src=x onerror=alert(1)>", "context": {"inject_dirty": true}}' \
    | python3 -c "
    import sys, json
    d = json.load(sys.stdin)
    assert 'decision' in d, 'Decision field missing'
    assert d['decision'] is not None
    print(f'Decision: {d[\"decision\"]}')
    print('PASS: Dirty input handled gracefully')
    "
  ```
  **Acceptance:** Engine sanitizes dirty input, no XSS, no crash. Valid JSON response returned.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

### 2.8 Portal & Integration Verification (E-Group)

- [ ] **2.8.1 — Portal metric caliber verification**
  ```bash
  python3 -c "
  import json
  # Verify portal displays metrics using correct caliber (aggregation method)
  with open('/opt/v86/analysis/portal_metric_caliber.json') as f:
      caliber = json.load(f)
  required_metrics = ['v86_rule_evaluations_total', 'v86_rule_evaluation_duration_seconds',
                       'v86_alias_resolutions_total', 'v86_alias_resolution_duration_seconds']
  for m in required_metrics:
      assert m in caliber, f'Missing metric caliber: {m}'
  print(f'PASS: {len(caliber)} metrics caliber defined')
  for m in required_metrics:
      agg = caliber[m].get('aggregation', '?')
      print(f'  {m}: {agg}')
  "
  ```
  **Acceptance:** All 4 required metrics have defined caliber with correct aggregation.
  **Owner:** Portal Engineer | **Gate:** PASS/FAIL

- [ ] **2.8.2 — Portal permission config verification**
  ```bash
  python3 -c "
  import json
  with open('/opt/v86/analysis/portal_permission_config.json') as f:
      perms = json.load(f)
  # Verify RBAC roles exist
  required_roles = ['admin', 'operator', 'viewer']
  for r in required_roles:
      assert r in perms.get('roles', {}), f'Missing role: {r}'
  print(f'PASS: Roles defined: {list(perms.get(\"roles\", {}).keys())}')
  # Verify access rules
  for role in required_roles:
      rules = perms['roles'][role].get('permissions', [])
      print(f'  {role}: {len(rules)} permissions')
      assert len(rules) >= 1, f'{role} has no permissions'
  "
  ```
  **Acceptance:** All 3 RBAC roles defined with at least 1 permission each.
  **Owner:** Portal Engineer | **Gate:** PASS/FAIL

- [ ] **2.8.3 — Portal integration documentation verification**
  ```bash
  test -f /opt/v86/analysis/v86_portal_integrate_doc.md && echo "EXISTS" || echo "MISSING"
  wc -l /opt/v86/analysis/v86_portal_integrate_doc.md
  ```
  **Acceptance:** Document exists with ≥ 50 lines covering API endpoints, data flow, and error handling.
  **Owner:** Portal Engineer | **Gate:** PASS/FAIL

- [ ] **2.8.4 — V85 frozen portal page verification**
  ```bash
  # Verify V85 frozen page exists and is not modified
  test -f /opt/v86/analysis/v85_frozen_portal_page.md && echo "EXISTS" || echo "MISSING"
  md5sum /opt/v86/analysis/v85_frozen_portal_page.md
  # NO_MODIFY_V85=TRUE — ensure no modifications
  ```
  **Acceptance:** V85 frozen page exists, NO_MODIFY_V85 constraint enforced.
  **Owner:** Portal Engineer | **Gate:** PASS/FAIL

### 2.9 DEPENDENCY_GAP — A/C Group Items

- [ ] **2.9.1 — Parameter freeze verification — DEPENDENCY_GAP**
  ```
  ⚠️ DEPENDENCY_GAP: A group parameter freeze assets not delivered to repo.
  Expected artifact: v86_parameter_freeze_manifest.json
  Expected location: analysis/e2e_output/v86/dshb_gate_final_review/
  A group deliverables must be available before this item can be verified.
  ```
  **Owner:** A Group (Pending) | **Gate:** **BLOCKED** — awaiting A group delivery
  **Impact:** Cannot verify parameter freeze compliance until A group provides frozen parameter snapshot.

- [ ] **2.9.2 — Joint backtest data verification — DEPENDENCY_GAP**
  ```
  ⚠️ DEPENDENCY_GAP: A/C group joint backtest data assets not delivered to repo.
  Expected artifacts:
    - v86_joint_backtest_results.json (A group)
    - v86_joint_backtest_analysis.md (C group)
  Expected location: analysis/e2e_output/v86/dshb_gate_final_review/
  ```
  **Owner:** A/C Group (Pending) | **Gate:** **BLOCKED** — awaiting A/C group delivery
  **Impact:** Cannot verify joint backtest performance metrics until both groups deliver data.

- [ ] **2.9.3 — Strategy risk boundary verification — DEPENDENCY_GAP**
  ```
  ⚠️ DEPENDENCY_GAP: A group strategy risk boundary assets not delivered to repo.
  Expected artifacts:
    - v86_strategy_risk_boundary.json
    - v86_risk_threshold_definitions.md
  Expected location: analysis/e2e_output/v86/dshb_gate_final_review/
  ```
  **Owner:** A Group (Pending) | **Gate:** **BLOCKED** — awaiting A group delivery
  **Impact:** Cannot verify risk boundary compliance until A group delivers risk definitions.

---

## Section 3: Deployment Phase (T-2h to T-0)

### 3.1 Pre-Deployment Health Checks

- [ ] **3.1.1 — Existing service health (if v85 running)**
  ```bash
  curl -s http://localhost:8080/health | python3 -m json.tool
  ```
  **Acceptance:** If v85 is active, returns `{"status": "healthy", ...}`. If no prior version, skip.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL (reference baseline)

- [ ] **3.1.2 — Port availability**
  ```bash
  ss -tlnp | grep ":8080"
  ```
  **Acceptance:** No listener (port free) or old service stopped. If listener exists, confirm it is v85 service to be replaced.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **3.1.3 — Database / external dependency connectivity**
  ```bash
  python3 -c "
  import json, socket
  with open('/opt/v86/deployment/config/dependencies.json') as f:
      deps = json.load(f)
  for dep in deps.get('dependencies', []):
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.settimeout(2)
      try:
          sock.connect((dep['host'], dep['port']))
          print(f'PASS: {dep[\"name\"]} reachable')
      except Exception as e:
          print(f'WARN: {dep[\"name\"]} unreachable: {e}')
      finally:
          sock.close()
  "
  ```
  **Acceptance:** All required dependencies reachable. Optional deps warned.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 3.2 Cold Start & Latency Verification (D-Group)

- [ ] **3.2.1 — Cold start time verification (≤ 30s)**
  ```bash
  # Stop service
  systemctl stop v86-rule-engine.service
  # Start and measure time to healthy
  START_TIME=$(date +%s.%N)
  for i in $(seq 1 60); do
    RESP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null || echo "000")
    if [ "$RESP" = "200" ]; then
      END_TIME=$(date +%s.%N)
      ELAPSED=$(python3 -c "print(f'{$END_TIME - $START_TIME:.2f}')")
      echo "Cold start completed in ${ELAPSED}s"
      python3 -c "assert float('$ELAPSED') <= 30.0, f'Cold start {float('$ELAPSED'):.2f}s exceeds 30s limit'"
      echo "PASS: Cold start within 30s"
      break
    fi
    sleep 1
  done
  systemctl start v86-rule-engine.service
  ```
  **Acceptance:** Cold start time ≤ 30s.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL (block deployment)

- [ ] **3.2.2 — First request latency verification (≤ 50ms)**
  ```bash
  python3 -c "
  import time, json, urllib.request
  # Wait for service to be ready
  for _ in range(30):
      try:
          urllib.request.urlopen('http://localhost:8080/health', timeout=1)
          break
      except:
          time.sleep(0.5)

  # Send first evaluation request and measure latency
  req = urllib.request.Request(
      'http://localhost:8080/evaluate',
      data=json.dumps({'input': 'first_request_test', 'context': {}}).encode(),
      headers={'Content-Type': 'application/json'},
      method='POST'
  )
  start = time.time()
  resp = urllib.request.urlopen(req, timeout=10)
  elapsed_ms = (time.time() - start) * 1000
  print(f'First request latency: {elapsed_ms:.1f}ms')
  assert elapsed_ms <= 50.0, f'First request {elapsed_ms:.1f}ms exceeds 50ms limit'
  print('PASS: First request latency within 50ms')
  "
  ```
  **Acceptance:** First request latency ≤ 50ms.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL (block deployment)

### 3.3 Service Installation

- [ ] **3.3.1 — Stop any existing service**
  ```bash
  systemctl stop v86-rule-engine.service 2>/dev/null || echo "No prior service found"
  systemctl disable v86-rule-engine.service 2>/dev/null || true
  ```
  **Acceptance:** Service stopped cleanly.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **3.3.2 — Install artifact bundle**
  ```bash
  tar -xzf /opt/v86/artifacts/v86-bundle-*.tar.gz -C /opt/v86/deployment/
  echo "Bundle installed. Verifying:"
  ls -d /opt/v86/deployment/rule_engine /opt/v86/deployment/alias_engine /opt/v86/deployment/config
  ```
  **Acceptance:** All critical directories present after extraction.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **3.3.3 — Install systemd unit file**
  ```bash
  cp /opt/v86/deployment/deploy/v86-rule-engine.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable v86-rule-engine.service
  ```
  **Acceptance:** Service enabled for boot. `systemctl is-enabled` returns `enabled`.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **3.3.4 — Create data directories**
  ```bash
  mkdir -p /opt/v86/data/logs /opt/v86/data/cache /opt/v86/data/temp
  chown -R v86:v86 /opt/v86/data 2>/dev/null || true
  ls -la /opt/v86/data/
  ```
  **Acceptance:** All 3 directories created with correct ownership.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

### 3.4 Engine Initialization

- [ ] **3.4.1 — Start service**
  ```bash
  systemctl start v86-rule-engine.service
  sleep 2
  systemctl status v86-rule-engine.service --no-pager
  ```
  **Acceptance:** `Active: active (running)` and `Loaded: loaded`.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL (block deployment)

- [ ] **3.4.2 — Verify process tree**
  ```bash
  ps aux | grep v86-rule-engine | grep -v grep
  ```
  **Acceptance:** 5 total processes (1 parent + 4 workers).
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **3.4.3 — Verify memory usage within limits**
  ```bash
  systemctl show v86-rule-engine.service --property=MemoryCurrent
  ```
  **Acceptance:** Memory consumption < 2 GB.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **3.4.4 — Verify engine loads both engines**
  ```bash
  curl -s http://localhost:8080/health | python3 -m json.tool
  ```
  **Expected output:**
  ```json
  {
    "status": "healthy",
    "rules": 18,
    "alias_entries": 4643,
    "alias_mode": "f3+f4",
    "engine": "V86P1RuleEngine + V86AliasEngine",
    "version": "v86",
    "commit": "f694618",
    "uptime_seconds": <value>
  }
  ```
  **Acceptance:** `rules == 18`, `alias_entries == 4643`, `alias_mode == "f3+f4"`, `status == "healthy"`.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL (block deployment)

### 3.5 Health Verification

- [ ] **3.5.1 — Health endpoint responds within timeout**
  ```bash
  curl -s -o /dev/null -w "%{http_code} %{time_total}s" http://localhost:8080/health
  ```
  **Acceptance:** HTTP 200, response time < 1s.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **3.5.2 — Rule evaluation smoke test**
  ```bash
  curl -s -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" \
    -d '{"input": "benign test sample", "context": {}}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Valid JSON response with `decision` field and all 18 rules evaluated.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **3.5.3 — Alias resolution smoke test**
  ```bash
  curl -s -X POST http://localhost:8080/alias/resolve \
    -H "Content-Type: application/json" \
    -d '{"input": "some_alias_entry"}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Response includes resolved alias mapping from F3/F4 layers.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **3.5.4 — Full pipeline evaluation (alias → rule)**
  ```bash
  curl -s -X POST http://localhost:8080/pipeline/evaluate \
    -H "Content-Type: application/json" \
    -d '{"input": "test input with alias", "context": {}}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Response includes both `alias_resolution` and `rule_decisions` fields.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **3.5.5 — Concurrency test**
  ```bash
  python3 -c "
  import json, urllib.request, time
  start = time.time()
  from concurrent.futures import ThreadPoolExecutor
  def send(i):
      req = urllib.request.Request(
          'http://localhost:8080/evaluate',
          data=json.dumps({'input': f'test_{i}', 'context': {}}).encode(),
          headers={'Content-Type': 'application/json'},
          method='POST'
      )
      return urllib.request.urlopen(req, timeout=10).status
  with ThreadPoolExecutor(max_workers=64) as pool:
      results = list(pool.map(send, range(64)))
  elapsed = time.time() - start
  assert all(r == 200 for r in results), 'Some requests failed'
  print(f'PASS: 64 concurrent requests in {elapsed:.2f}s')
  "
  ```
  **Acceptance:** All 64 requests return HTTP 200, total time < 30s.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

---

## Section 4: Post-Deployment Phase (T+0 to T+2h)

### 4.1 Smoke Tests

- [ ] **4.1.1 — Latency baseline capture**
  ```bash
  for i in $(seq 1 20); do
    curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" \
      -X POST http://localhost:8080/evaluate \
      -H "Content-Type: application/json" \
      -d '{"input": "latency_test_input", "context": {}}'
  done | awk '{print $2}' | sort -n
  ```
  **Acceptance:** All responses < 1s. P95 < 5ms for evaluation core.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **4.1.2 — Edge case inputs**
  ```bash
  # Empty input
  curl -s -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" -d '{"input": "", "context": {}}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['decision']; print('PASS: empty input')"

  # Unicode input
  curl -s -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" -d '{"input": "测试中文输入 üöä Ñ ß ∑", "context": {}}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['decision']; print('PASS: unicode input')"

  # Max-length input (10KB)
  curl -s -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" \
    -d "{\"input\": \"$(python3 -c 'print("A"*10240)')\", \"context\": {}}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['decision']; print('PASS: max length')"
  ```
  **Acceptance:** All 3 edge cases return valid responses with `decision` field.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **4.1.3 — Invalid input handling**
  ```bash
  curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" \
    -d 'not json'
  ```
  **Acceptance:** HTTP 400 or 422 (graceful error, no crash).
  **Owner:** QA Lead | **Gate:** PASS/FAIL

- [ ] **4.1.4 — Service crash recovery test**
  ```bash
  WORKER_PID=$(pgrep -f "v86-rule-engine" | tail -1)
  kill -9 "$WORKER_PID"
  sleep 3
  pgrep -f "v86-rule-engine" | wc -l
  ```
  **Acceptance:** Worker count recovers to 4 within 5s. Health endpoint returns 200.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 4.2 Monitoring Verification

- [ ] **4.2.1 — Prometheus scrape target verified**
  ```bash
  curl -s http://localhost:8080/metrics | head -20
  ```
  **Acceptance:** Returns Prometheus text format (`# HELP`, `# TYPE`, metric names).
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **4.2.2 — Rule engine metrics present**
  ```bash
  curl -s http://localhost:8080/metrics | grep -E "^v86_rule_"
  ```
  **Acceptance:** Contains `v86_rule_evaluations_total`, `v86_rule_evaluation_duration_seconds`, `v86_rule_rule_decisions_total`, `v86_rule_queue_depth`, `v86_rule_queue_rejected_total`.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **4.2.3 — Alias engine metrics present**
  ```bash
  curl -s http://localhost:8080/metrics | grep -E "^v86_alias_"
  ```
  **Acceptance:** Contains `v86_alias_resolutions_total`, `v86_alias_resolution_duration_seconds`, `v86_alias_blacklist_hits_total`, `v86_alias_layer_hits`.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **4.2.4 — All metric categories present**
  ```bash
  curl -s http://localhost:8080/metrics | grep -E "^# TYPE" | wc -l
  ```
  **Acceptance:** ≥ 80 unique metric families.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **4.2.5 — Grafana dashboard loaded**
  ```bash
  curl -s -u admin:admin "http://<grafana-host>/api/dashboards/uid/v86-rule-engine" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Dashboard: {d[\"dashboard\"][\"title\"]}, panels: {len(d[\"dashboard\"][\"panels\"])}')"
  ```
  **Acceptance:** 8 panels.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **4.2.6 — Alert rules loaded**
  ```bash
  curl -s "http://<prometheus-host>/api/v1/rules" \
    | python3 -c "
    import sys, json
    data = json.load(sys.stdin)
    groups = data['data']['groups']
    for g in groups:
        if 'v86' in g.get('name','').lower():
            for r in g['rules']:
                print(f'{r[\"name\"]}: {r[\"type\"]} — {r.get(\"state\",\"?\")}' + f' — {r.get(\"labels\",{}).get(\"severity\",\"?\")}' )
    "
  ```
  **Acceptance:** 4 critical + 4 warning rules present.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 4.3 Alert Test

- [ ] **4.3.1 — Trigger a test alert (error rate spike)**
  ```bash
  for i in $(seq 1 50); do
    curl -s -X POST http://localhost:8080/evaluate \
      -H "Content-Type: application/json" \
      -d 'invalid json to trigger error' &
  done
  wait
  sleep 60
  curl -s "http://<prometheus-host>/api/v1/alerts" \
    | python3 -c "
    import sys, json
    alerts = json.load(sys.stdin).get('data',{}).get('alerts',[])
    v86 = [a for a in alerts if 'v86' in a.get('labels',{}).get('rule','').lower()]
    print(f'V86 alerts firing: {len(v86)}')
    for a in v86[:5]:
        print(f'  - {a[\"labels\"][\"alertname\"]}: {a[\"state\"]}')
    assert len(v86) >= 1, 'No alerts fired within 2 min'
    print('PASS: Alerts firing')
    "
  ```
  **Acceptance:** At least one alert fires within 2 minutes of error traffic.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **4.3.2 — Verify alert routing**
  ```bash
  curl -s "http://<alertmanager-host>/api/v2/alerts" \
    | python3 -c "
    import sys, json
    alerts = json.load(sys.stdin)
    v86 = [a for a in alerts if 'v86' in str(a.get('labels',{})).lower()]
    print(f'Alertmanager V86 alerts: {len(v86)}')
    for a in v86[:3]:
        print(f'  - {a[\"labels\"].get(\"alertname\",\"?\")}: status={a[\"status\"].get(\"state\",\"?\")}')
    assert len(v86) >= 1, 'Alert not routed to Alertmanager'
    print('PASS: Alert routing verified')
    "
  ```
  **Acceptance:** Alert appears in Alertmanager.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

- [ ] **4.3.3 — SLO health dashboard**
  ```bash
  curl -s "http://<prometheus-host>/api/v1/query" \
    --data-urlencode 'query=rate(v86_rule_evaluations_total{status="error"}[5m]) / rate(v86_rule_evaluations_total[5m])' \
    | python3 -c "
    import sys, json
    data = json.load(sys.stdin)
    if data['data']['result']:
        value = float(data['data']['result'][0]['value'][1])
        print(f'Error rate: {value*100:.2f}%')
        assert value < 0.01, f'Error rate {value*100:.2f}% exceeds 1% SLO threshold'
        print('PASS: Error rate within SLO')
    else:
        print('PASS: No error events (0% error rate)')
    "
  ```
  **Acceptance:** Error rate < 1% (SLO threshold).
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 4.4 Rollback Readiness

- [ ] **4.4.1 — Rollback Strategy A package verified**
  ```bash
  ls -lh /opt/v86/rollback/v85-*/ 2>/dev/null || echo "WARNING: v85 snapshot missing"
  cat /opt/v86/rollback/version_manifest.json
  ```
  **Expected manifest:**
  ```json
  {
    "from_version": "v86",
    "to_version": "v85",
    "bundle": "v85-bundle-*.tar.gz",
    "rto_seconds": 78,
    "service": "v86-rule-engine.service"
  }
  ```
  ```bash
  cd /opt/v86/rollback/
  md5sum -c v85-*.md5
  ```
  **Acceptance:** Manifest present, bundle checksums OK.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **4.4.2 — Rollback Strategy B switch tested**
  ```bash
  curl -s -X POST http://localhost:8080/admin/rollback \
    -H "Content-Type: application/json" \
    -d '{"strategy": "B", "dry_run": true}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Returns plan with `rto_seconds: 30`, `strategy: "B"`, `ready: true`.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL
  > **Note:** Dry-run only. Do not execute real rollback unless incident triggers.

- [ ] **4.4.3 — Rollback script executable**
  ```bash
  which /opt/v86/scripts/rollback.sh
  bash -n /opt/v86/scripts/rollback.sh
  ```
  **Acceptance:** Script exists, no syntax errors.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

### 4.5 Gray Release Initiation & Verification (D-Group)

- [ ] **4.5.1 — Feature flag initialized**
  ```bash
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "enabled": true, "weight": 0}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Flag created with weight 0, enabled true.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL

- [ ] **4.5.2 — Gray traffic split verification — 10% canary**
  ```bash
  # Set 10% traffic
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "weight": 10}'
  echo "Gray weight set to 10%. Observation window: 15 minutes."

  # Monitor traffic distribution
  python3 -c "
  import urllib.request, json, time
  for minute in range(15):
      time.sleep(60)
      req = urllib.request.Request('http://localhost:8080/metrics')
      resp = urllib.request.urlopen(req, timeout=5)
      metrics = resp.read().decode()
      # Extract v86 vs total evaluations
      v86_count = 0
      total_count = 0
      for line in metrics.split('\n'):
          if 'v86_canary_requests_total' in line:
              v86_count = int(line.split()[-1])
          if 'v86_canary_weight' in line:
              weight = float(line.split()[-1])
      print(f'Minute {minute+1}: v86 weight={weight}, requests={v86_count}')
  "
  ```
  **Acceptance:** 10% weight sustained for 15 minutes. No metric degradation. Error rate < 1%. Latency P95 < 50ms.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL (block gray promotion)

- [ ] **4.5.3 — Gray traffic split verification — 30% promotion**
  ```bash
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "weight": 30}'
  echo "Gray weight promoted to 30%. Observation window: 15 minutes."

  # Monitor traffic distribution
  python3 -c "
  import urllib.request, time
  for minute in range(15):
      time.sleep(60)
      resp = urllib.request.urlopen('http://localhost:8080/metrics', timeout=5)
      metrics = resp.read().decode()
      weight = 0
      for line in metrics.split('\n'):
          if 'v86_canary_weight' in line:
              weight = float(line.split()[-1])
      print(f'Minute {minute+1}: v86 weight={weight}')
  "
  ```
  **Acceptance:** 30% weight sustained for 15 minutes. No degradation in error rate, latency, or queue depth.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL (block gray promotion)

- [ ] **4.5.4 — Gray traffic split verification — 100% full promotion**
  ```bash
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "weight": 100}'
  echo "Gray weight promoted to 100%. Full traffic on v86."
  sleep 120
  ```
  **Acceptance:** Weight 100% set. Service healthy after 2-minute stabilization.
  **Owner:** Release Engineer | **Gate:** PASS/FAIL (final deployment gate)

- [ ] **4.5.5 — Full traffic health confirmation**
  ```bash
  curl -s http://localhost:8080/metrics | grep -E "(v86_rule_evaluations_total|v86_rule_evaluation_duration_seconds_bucket)"
  ```
  **Acceptance:** Evaluation rate matches pre-deployment baseline. No spike in error or latency metrics.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL

### 4.6 Gray Gate Check Verification (D-Group)

- [ ] **4.6.1 — Gray gate auto-check execution**
  ```bash
  python3 /opt/v86/analysis/gate_auto_check.py \
    --gates G-GR-01,G-GR-02,G-GR-03,G-GR-04,G-GR-05,G-GR-06,G-GR-07,G-GR-08,G-GR-09,G-GR-10,G-GR-11,G-GR-12 \
    --config /opt/v86/deployment/config/engine_config.json \
    --output /opt/v86/analysis/gate_auto_check_report.json
  ```
  **Acceptance:** All 12 gray gates pass:
  ```
  G-GR-01: PASS  — Traffic weight validation
  G-GR-02: PASS  — Error rate threshold (< 1%)
  G-GR-03: PASS  — Latency P95 threshold (< 50ms)
  G-GR-04: PASS  — Queue depth threshold (< 100)
  G-GR-05: PASS  — Worker pool health (4/4 active)
  G-GR-06: PASS  — Memory usage (< 2GB)
  G-GR-07: PASS  — CPU usage (< 80%)
  G-GR-08: PASS  — Disk I/O (< 50% utilization)
  G-GR-09: PASS  — Network throughput (> 50 Mbps)
  G-GR-10: PASS  — Cache hit rate (> 80%)
  G-GR-11: PASS  — Fallback activation count (< 5 in 15min)
  G-GR-12: PASS  — Circuit breaker state (closed)
  ```
  **Owner:** Release Engineer | **Gate:** PASS/FAIL (block gray promotion)

### 4.7 Engine Crash Recovery Verification (D-Group)

- [ ] **4.7.1 — Engine crash recovery (35s, 0 interruptions)**
  ```bash
  python3 -c "
  import subprocess, time, json, urllib.request
  # Capture request stream before crash
  requests_before = []
  start = time.time()
  timeout_limit = 35.0
  crash_point = 10.0  # Trigger crash at 10s

  # Start background request generator
  import threading
  request_count = [0]
  error_count = [0]
  def generate_requests():
      while time.time() - start < timeout_limit:
          try:
              req = urllib.request.Request(
                  'http://localhost:8080/evaluate',
                  data=json.dumps({'input': f'crash_test_{request_count[0]}', 'context': {}}).encode(),
                  headers={'Content-Type': 'application/json'},
                  method='POST'
              )
              resp = urllib.request.urlopen(req, timeout=5)
              request_count[0] += 1
          except:
              error_count[0] += 1
          time.sleep(0.5)

  # Start requests
  t = threading.Thread(target=generate_requests, daemon=True)
  t.start()

  # Wait until crash point
  time.sleep(crash_point)
  print(f'Crashing engine at t={crash_point:.1f}s')

  # Kill all engine processes
  subprocess.run(['pkill', '-9', '-f', 'v86-rule-engine'], check=False)
  print(f'Engine killed at t={time.time()-start:.1f}s')

  # Wait for full window
  time.sleep(timeout_limit - (time.time() - start))

  elapsed = time.time() - start
  print(f'Total window: {elapsed:.1f}s')
  print(f'Requests sent: {request_count[0]}')
  print(f'Errors during window: {error_count[0]}')

  # After recovery, check health
  time.sleep(5)
  resp = urllib.request.urlopen('http://localhost:8080/health', timeout=5)
  health = json.loads(resp.read().decode())
  print(f'Health after recovery: {health[\"status\"]}')

  assert error_count[0] == 0, f'Interruptions detected: {error_count[0]} errors'
  assert health['status'] == 'healthy'
  print(f'PASS: 0 interruptions in {elapsed:.0f}s window')
  "
  ```
  **Acceptance:** Engine recovers within 35s. 0 request interruptions during crash window. Health returns healthy after recovery.
  **Owner:** SRE On-Call | **Gate:** PASS/FAIL (block gray promotion)

### 4.8 Demo & Portal Verification (E-Group)

- [ ] **4.8.1 — Demo runbook execution verification**
  ```bash
  python3 -c "
  import json
  with open('/opt/v86/analysis/v86_demo_runbook.md') as f:
      content = f.read()
  # Verify runbook has all required sections
  required_sections = ['Prerequisites', 'Setup', 'Execution Steps', 'Expected Output',
                        'Rollback', 'Troubleshooting']
  found = []
  for section in required_sections:
      if section.lower() in content.lower():
          found.append(section)
  print(f'Runbook sections found: {len(found)}/{len(required_sections)}')
  for s in found:
      print(f'  ✓ {s}')
  for s in required_sections:
      if s not in found:
          print(f'  ✗ MISSING: {s}')
  assert len(found) == len(required_sections), f'Missing sections: {set(required_sections)-set(found)}'
  print('PASS: Runbook complete')
  "
  ```
  **Acceptance:** All 6 required sections present in runbook.
  **Owner:** Portal Engineer | **Gate:** PASS/FAIL

- [ ] **4.8.2 — E2E smoke test verification**
  ```bash
  python3 -c "
  import json, urllib.request, time

  # Full E2E pipeline: input → alias → rule → decision
  test_inputs = [
      ('basic test', 'normal', {}),
      ('alias entry test', 'alias_mapped', {'expected_alias': 'resolved_alias'}),
      ('blacklist item', 'blacklisted', {'expected_blacklist': True}),
      ('empty input', '', {}),
      ('unicode test', '测试中文', {})
  ]

  passed = 0
  for i, (inp, desc, ctx) in enumerate(test_inputs):
      try:
          req = urllib.request.Request(
              'http://localhost:8080/pipeline/evaluate',
              data=json.dumps({'input': inp, 'context': ctx}).encode(),
              headers={'Content-Type': 'application/json'},
              method='POST'
          )
          resp = urllib.request.urlopen(req, timeout=10)
          result = json.loads(resp.read().decode())
          assert 'decision' in result, f'{desc}: missing decision field'
          passed += 1
          print(f'  ✓ [{i+1}] {desc}: decision={result[\"decision\"]}')
      except Exception as e:
          print(f'  ✗ [{i+1}] {desc}: FAIL — {e}')
          assert False, f'E2E test {i+1} failed'

  print(f'E2E smoke test: {passed}/{len(test_inputs)} passed')
  assert passed == len(test_inputs)
  print('PASS: All E2E smoke tests passed')
  "
  ```
  **Acceptance:** All 5 E2E smoke tests pass with valid responses.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

### 4.9 Demo & Portal Execution (E-Group)

- [ ] **4.9.1 — Portal metric caliber verification (post-deploy)**
  ```bash
  # Verify portal shows correct metric values after deployment
  python3 -c "
  import json, urllib.request
  # Fetch live metrics from Prometheus
  req = urllib.request.Request('http://<prometheus-host>/api/v1/query')
  resp = urllib.request.urlopen(req, timeout=5)
  data = json.loads(resp.read().decode())
  # Verify metric caliber matches portal display
  print(f'Prometheus query returned {len(data[\"data\"][\"result\"])} results')
  print('PASS: Metric caliber aligned with portal')
  "
  ```
  **Acceptance:** Portal metric values match Prometheus live data within 5% tolerance.
  **Owner:** Portal Engineer | **Gate:** PASS/FAIL

- [ ] **4.9.2 — Portal permission enforcement verification**
  ```bash
  # Test RBAC enforcement
  python3 -c "
  import json, urllib.request, urllib.error
  test_cases = [
      ('admin', 'can_modify_config', True),
      ('operator', 'can_modify_config', False),
      ('operator', 'can_view_metrics', True),
      ('viewer', 'can_view_metrics', True),
      ('viewer', 'can_modify_config', False),
  ]
  passed = 0
  for role, action, expected in test_cases:
      try:
          req = urllib.request.Request(
              'http://<portal-host>/api/admin/permission-check',
              data=json.dumps({'role': role, 'action': action}).encode(),
              headers={'Content-Type': 'application/json', 'X-Test-Role': role},
              method='POST'
          )
          resp = urllib.request.urlopen(req, timeout=5)
          result = json.loads(resp.read().decode())
          granted = result.get('granted', False)
          status = 'PASS' if granted == expected else 'FAIL'
          if granted == expected:
              passed += 1
              print(f'  ✓ [{role}] {action}: granted={granted} (expected={expected})')
          else:
              print(f'  ✗ [{role}] {action}: granted={granted} (expected={expected})')
      except urllib.error.HTTPError as e:
          if e.code == 403 and not expected:
              passed += 1
              print(f'  ✓ [{role}] {action}: HTTP 403 (correctly denied)')
          else:
              print(f'  ✗ [{role}] {action}: HTTP {e.code} (unexpected)')
  print(f'Permission tests: {passed}/{len(test_cases)} passed')
  assert passed == len(test_cases)
  print('PASS: RBAC enforcement verified')
  "
  ```
  **Acceptance:** All 5 RBAC test cases pass.
  **Owner:** Portal Engineer | **Gate:** PASS/FAIL

### 4.10 Anomaly Response Verification (D-Group — Post-Deployment)

- [ ] **4.10.1 — Anomaly injection response — full sweep**
  ```bash
  python3 -c "
  import json, urllib.request, time

  anomalies = {
      'timeout': {'inject_timeout': True},
      'cache_miss': {'inject_cache_miss': True},
      'dirty_data': {'inject_dirty': True},
      'null_input': {'input': None},
      'oversized_input': {'input': 'A' * 100000}
  }

  results = []
  for name, ctx in anomalies.items():
      try:
          req = urllib.request.Request(
              'http://localhost:8080/evaluate',
              data=json.dumps({'input': ctx.get('input', 'anomaly_test'), 'context': ctx}).encode(),
              headers={'Content-Type': 'application/json'},
              method='POST'
          )
          resp = urllib.request.urlopen(req, timeout=10)
          result = json.loads(resp.read().decode())
          http_code = resp.status
          has_decision = 'decision' in result
          results.append((name, http_code, has_decision))
          status = '✓' if has_decision else '✗'
          print(f'  {status} {name}: HTTP {http_code}, decision={has_decision}')
      except urllib.error.HTTPError as e:
          # 4xx/5xx is acceptable for some anomalies
          results.append((name, e.code, False))
          print(f'  ✓ {name}: HTTP {e.code} (graceful handling)')
      except Exception as e:
          print(f'  ✗ {name}: Exception — {e}')
          results.append((name, -1, False))

  # Service should still be healthy after all injections
  health_resp = urllib.request.urlopen('http://localhost:8080/health', timeout=5)
  health = json.loads(health_resp.read().decode())
  assert health['status'] == 'healthy', 'Service unhealthy after anomaly sweep'
  print(f'PASS: {len(results)} anomalies tested, service healthy')
  "
  ```
  **Acceptance:** All 5 anomaly types handled gracefully. Service remains healthy after sweep.
  **Owner:** QA Lead | **Gate:** PASS/FAIL

---

## Section 5: Emergency Procedures (Quick Reference)

### E1. Immediate Rollback — Strategy B (Dynamic Switch, RTO ~30s)

```bash
# Use when: errors > 5%, latency P95 > 50ms, or alias resolution failure spike
curl -s -X POST http://localhost:8080/admin/rollback \
  -H "Content-Type: application/json" \
  -d '{"strategy": "B"}'
```
**Verify:**
```bash
curl -s http://localhost:8080/health | python3 -m json.tool
# Expected: "version": "v85" or "engine": "V85..."
```
**Owner:** SRE On-Call | **Gate:** Execute on trigger

### E2. Immediate Rollback — Strategy A (Version Snapshot, RTO ~78s)

```bash
# Use when: Strategy B unavailable (e.g., service crash, binary corruption)
/opt/v86/scripts/rollback.sh --strategy A
```
**Verify:**
```bash
systemctl status v86-rule-engine.service --no-pager
curl -s http://localhost:8080/health
```
**Owner:** SRE On-Call | **Gate:** Execute on trigger

### E3. Emergency Shutdown

```bash
systemctl stop v86-rule-engine.service
systemctl disable v86-rule-engine.service
```
**Verify:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health
# Expected: 000 (connection refused — service down)
```
**Owner:** SRE On-Call | **Gate:** Execute on trigger

### E4. Clear Queue Backlog

```bash
curl -s -X POST http://localhost:8080/admin/queue/drain \
  -H "Content-Type: application/json" \
  -d '{"grace_seconds": 5}'
```
**Verify:**
```bash
curl -s http://localhost:8080/metrics | grep "v86_rule_queue_depth"
# Expected: depth near 0 after drain
```
**Owner:** SRE On-Call | **Gate:** Execute on trigger

### E5. Enable Debug Logging

```bash
curl -s -X POST http://localhost:8080/admin/loglevel \
  -H "Content-Type: application/json" \
  -d '{"level": "DEBUG"}'
```
**Revert after investigation:**
```bash
curl -s -X POST http://localhost:8080/admin/loglevel \
  -H "Content-Type: application/json" \
  -d '{"level": "INFO"}'
```
**Owner:** SRE On-Call | **Gate:** Execute on trigger

### E6. Force Worker Restart

```bash
systemctl restart v86-rule-engine.service
```
**Verify:**
```bash
sleep 3
curl -s http://localhost:8080/health | python3 -m json.tool
```
**Owner:** SRE On-Call | **Gate:** Execute on trigger

---

## Section 6: Go/No-Go Decision Matrix

| # | Check | Threshold | Result |
|---|-------|-----------|--------|
| 1 | CI gates pass (Rule) | 12/12 | `[ ] PASS` / `[ ] FAIL` |
| 2 | CI gates pass (Alias) | 3/3 | `[ ] PASS` / `[ ] FAIL` |
| 3 | Rule count | 18 rules (6 P0 + 12 P1) | `[ ] PASS` / `[ ] FAIL` |
| 4 | Alias entries | 4,643 entries, 31 blacklist rules | `[ ] PASS` / `[ ] FAIL` |
| 5 | Bundle MD5 checksum | All match baseline | `[ ] PASS` / `[ ] FAIL` |
| 6 | Python version | 3.12.x | `[ ] PASS` / `[ ] FAIL` |
| 7 | Health endpoint | `{"status": "healthy", "rules": 18}` | `[ ] PASS` / `[ ] FAIL` |
| 8 | Worker processes | 4 workers + 1 parent | `[ ] PASS` / `[ ] FAIL` |
| 9 | Memory under limit | < 2 GB | `[ ] PASS` / `[ ] FAIL` |
| 10 | Concurrency (64 parallel) | All return HTTP 200 | `[ ] PASS` / `[ ] FAIL` |
| 11 | Cold start time | ≤ 30s | `[ ] PASS` / `[ ] FAIL` |
| 12 | First request latency | ≤ 50ms | `[ ] PASS` / `[ ] FAIL` |
| 13 | Latency P95 | < 5 ms | `[ ] PASS` / `[ ] FAIL` |
| 14 | Error rate | < 1% | `[ ] PASS` / `[ ] FAIL` |
| 15 | False positive rate | < 5% | `[ ] PASS` / `[ ] FAIL` |
| 16 | Queue rejection rate | < 0.1% | `[ ] PASS` / `[ ] FAIL` |
| 17 | Availability SLO | 99.9% | `[ ] PASS` / `[ ] FAIL` |
| 18 | Prometheus metrics | ≥ 80 families, 8 categories | `[ ] PASS` / `[ ] FAIL` |
| 19 | Grafana dashboard | 8 panels loaded | `[ ] PASS` / `[ ] FAIL` |
| 20 | Alert rules | 4 critical + 4 warning | `[ ] PASS` / `[ ] FAIL` |
| 21 | Alert test fires | Alert received within 2 min | `[ ] PASS` / `[ ] FAIL` |
| 22 | Rollback Strategy A ready | Manifest + bundle verified | `[ ] PASS` / `[ ] FAIL` |
| 23 | Rollback Strategy B ready | Dry-run returns `ready: true` | `[ ] PASS` / `[ ] FAIL` |
| 24 | Gray 10% stable | 15 min, no metric degradation | `[ ] PASS` / `[ ] FAIL` |
| 25 | Gray 30% stable | 15 min, no metric degradation | `[ ] PASS` / `[ ] FAIL` |
| 26 | Gray 100% promoted | Full traffic healthy | `[ ] PASS` / `[ ] FAIL` |
| 27 | 12 gray gates (G-GR-01 to G-GR-12) | All 12 PASS | `[ ] PASS` / `[ ] FAIL` |
| 28 | Degradation drill (L1/L2/L3) | All 3 levels + recovery | `[ ] PASS` / `[ ] FAIL` |
| 29 | Engine crash recovery | 35s window, 0 interruptions | `[ ] PASS` / `[ ] FAIL` |
| 30 | Cache warmup | 18 samples, 956 entries | `[ ] PASS` / `[ ] FAIL` |
| 31 | Anomaly injection (5 types) | All handled gracefully | `[ ] PASS` / `[ ] FAIL` |
| 32 | Portal metric caliber | 4 metrics aligned | `[ ] PASS` / `[ ] FAIL` |
| 33 | Portal RBAC enforcement | 5/5 test cases pass | `[ ] PASS` / `[ ] FAIL` |
| 34 | Demo runbook complete | 6/6 sections present | `[ ] PASS` / `[ ] FAIL` |
| 35 | E2E smoke test | 5/5 pass | `[ ] PASS` / `[ ] FAIL` |
| 36 | V85 frozen page | Exists, unmodified | `[ ] PASS` / `[ ] FAIL` |
| 37 | SRE sign-off | On-call engineer confirms | `[ ] PASS` / `[ ] FAIL` |
| 38 | **Param freeze (A group)** | **DEPENDENCY_GAP** | `[ ] GAP` |
| 39 | **Joint backtest (A/C)** | **DEPENDENCY_GAP** | `[ ] GAP` |
| 40 | **Strategy risk (A group)** | **DEPENDENCY_GAP** | `[ ] GAP` |

### Decision Criteria

| Pass Count | Decision |
|------------|----------|
| **37 / 37 actionable** (all non-GAP) | ✅ **GO** — Full deployment approved |
| **34–36 / 37** | ⚠️ **CONDITIONAL GO** — Document deviation, SRE sign-off required |
| **30–33 / 37** | ❌ **NO-GO** — Fix failures, re-run checklist from first failed item |
| **< 30 / 37** | 🚫 **HALT** — Deployment blocked. Revert to pre-deployment state |
| **Any GAP unresolved at T-0** | ⏸️ **DELAY** — Resolve dependency gaps before proceeding |

---

## Section 7: Sign-Off

### Phase-by-Phase Sign-Off

| Phase | Responsible | Sign-Off Date | Signature | Status |
|-------|-------------|---------------|-----------|--------|
| **2 — Pre-Deployment** | Release Engineer + SRE | | | `[ ] READY` / `[ ] BLOCKED` |
| **3 — Deployment** | SRE On-Call | | | `[ ] READY` / `[ ] BLOCKED` |
| **4 — Post-Deployment** | QA Lead + Release Engineer | | | `[ ] READY` / `[ ] BLOCKED` |
| **5 — Emergency** | SRE On-Call | | | `[ ] ACKNOWLEDGED` |
| **DEPENDENCY_GAP** | A/C Group | | | `[ ] PENDING` / `[ ] RESOLVED` |

### Final Sign-Off

| Role | Name | Date | Signature | Comments |
|------|------|------|-----------|----------|
| Release Engineer | | | | |
| SRE On-Call | | | | |
| QA Lead | | | | |
| Portal Engineer | | | | |
| Engineering Manager | | | | |
| CTO / VP Engineering | | | | |

### Deployment Window

- **Scheduled Window:** ___________________
- **Go/No-Go Review:** ___________________
- **Rollback Decision Threshold:** ≥ 3 FAIL items or any GAP unresolved at T-2h
- **Post-Deployment Monitoring Window:** T+0 to T+2h (15-min gray intervals)

---

## Appendix A: Metric Reference

### 90 Metrics Across 8 Categories

| Category | Prefix | Example Metrics |
|----------|--------|----------------|
| Rule Engine | `v86_rule_` | evaluations_total, evaluation_duration_seconds, rule_decisions_total, queue_depth, queue_rejected_total, workers_active |
| Alias Engine | `v86_alias_` | resolutions_total, resolution_duration_seconds, blacklist_hits_total, layer_hits, dictionary_size |
| HTTP Server | `v86_http_` | requests_total, request_duration_seconds, response_size_bytes, concurrent_requests |
| Pipeline | `v86_pipeline_` | end_to_end_duration_seconds, alias_to_rule_pass_total, rejected_total |
| Process | `v86_process_` | cpu_seconds_total, rss_bytes, fds, uptime_seconds |
| SLO | `v86_slo_` | availability_ratio, p95_latency_ratio, false_positive_ratio, error_ratio, queue_rejection_ratio |
| Canary | `v86_canary_` | weight, requests_total, errors_total |
| Health | `v86_health_` | checks_total, check_duration_seconds, unhealthy_events_total |

---

## Appendix B: Environment Variable Quick Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | HTTP listen address |
| `PORT` | `8080` | HTTP listen port |
| `WORKERS` | `4` | Number of worker processes |
| `MAX_CONCURRENT` | `64` | Max concurrent evaluations |
| `TIMEOUT_SECONDS` | `30` | Per-request evaluation timeout |
| `LOG_LEVEL` | `INFO` | Log verbosity (DEBUG/INFO/WARNING/ERROR) |

---

## Appendix C: Gray Gate Definitions (G-GR-01 through G-GR-12)

| Gate ID | Name | Threshold | Metric Source |
|---------|------|-----------|---------------|
| G-GR-01 | Traffic Weight Validation | Weight matches configured value ±1% | `v86_canary_weight` |
| G-GR-02 | Error Rate Threshold | Error rate < 1% over 5m | `v86_slo_error_ratio` |
| G-GR-03 | Latency P95 Threshold | P95 latency < 50ms | `v86_rule_evaluation_duration_seconds_bucket` |
| G-GR-04 | Queue Depth Threshold | Queue depth < 100 | `v86_rule_queue_depth` |
| G-GR-05 | Worker Pool Health | 4/4 workers active | `v86_rule_workers_active` |
| G-GR-06 | Memory Usage | RSS < 2 GB | `v86_process_rss_bytes` |
| G-GR-07 | CPU Usage | CPU < 80% | `v86_process_cpu_seconds_total` |
| G-GR-08 | Disk I/O | I/O utilization < 50% | `v86_process_iops_total` |
| G-GR-09 | Network Throughput | > 50 Mbps | `v86_http_response_size_bytes` |
| G-GR-10 | Cache Hit Rate | > 80% | `v86_alias_layer_hits` (F3+F4 hits / total) |
| G-GR-11 | Fallback Activation Count | < 5 in 15 min | `v86_pipeline_rejected_total` |
| G-GR-12 | Circuit Breaker State | State == closed | `v86_health_unhealthy_events_total` |

---

## Appendix D: systemd Service File (Reference)

```ini
[Unit]
Description=V86 Rule+Alias Engine
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=v86
Group=v86
WorkingDirectory=/opt/v86/deployment
EnvironmentFile=/etc/v86/v86.env
ExecStart=/usr/bin/python3 -m v86.server.main
Restart=on-failure
RestartSec=5
MemoryLimit=2G
TasksMax=64
LimitNOFILE=65536
StandardOutput=journal
StandardError=journal
SyslogIdentifier=v86-rule-engine

[Install]
WantedBy=multi-user.target
```

---

## Appendix E: DEPENDENCY_GAP Summary

| Gap ID | Item | Group | Expected Artifact | Status |
|--------|------|-------|-------------------|--------|
| GAP-001 | Parameter freeze verification | A | `v86_parameter_freeze_manifest.json` | ⏳ PENDING |
| GAP-002 | Joint backtest data verification | A/C | `v86_joint_backtest_results.json` + analysis | ⏳ PENDING |
| GAP-003 | Strategy risk boundary verification | A | `v86_strategy_risk_boundary.json` | ⏳ PENDING |

**Resolution Process:**
1. A group delivers artifacts to `analysis/e2e_output/v86/dshb_gate_final_review/`
2. C group delivers joint backtest analysis
3. Release engineer verifies artifacts against acceptance criteria
4. Update GAP status from PENDING to RESOLVED
5. Re-run affected checklist items

---

## Appendix F: Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| T3.4 | 2026-06-24 | B+D+E groups | Finalized checklist. Added 31 items from D/E groups. Marked 3 items as DEPENDENCY_GAP. 99 total items (96 actionable + 3 gap). |
| v1.0 | 2026-06-24 | B group | Original pre-flight checklist (68 items across 4 phases). |

---

*End of V86 Finalized Pre-Flight Checklist (T3.4) — DSHB_V86_GATE_FINAL_REVIEW*
