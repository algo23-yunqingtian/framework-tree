# V86 Pre-Flight Checklist

> **Task:** DSHB_V86_RULE_ALIAS_JOIN_PROD_STRESS_GATE_ACCEPT_AND_RISK_REGISTER
> **Branch:** feature/v85-chart-template
> **Engine:** V86P1RuleEngine + V86AliasEngine (F1+F2+F3+F4)
> **Generated:** 2026-06-24
> **Status:** ACTIVE — Launch Window Ready

---

## Section 1: Checklist Overview

This pre-flight checklist covers the complete deployment lifecycle for the V86 dual-engine pipeline:

- **Rule Engine** (V86P1RuleEngine): 18 rules (6 P0 + 12 P1) at commit `f694618`
- **Alias Engine** (V86AliasEngine): 4,643 alias entries, 31 blacklist rules, mode `f3+f4` at commit `81268a6`
- **Pipeline:** raw input → alias resolution → rule evaluation → decision output

### Coverage Summary

| Phase | Window | Items | Pass/Fail Gate |
|-------|--------|-------|----------------|
| Pre-Deployment | T-24h to T-2h | 28 | Block deployment if any FAIL |
| Deployment | T-2h to T-0 | 18 | Halt and rollback on failure |
| Post-Deployment | T+0 to T+2h | 22 | Abort gray release on failure |
| Emergency | On-demand | 6 | Execute immediately on trigger |

### Required Artifacts

- [ ] V86 bundle package (expected size: ~296 KB)
- [ ] `v86-rule-engine.service` systemd unit file
- [ ] Dockerfile + docker-compose.yml (if container deployment)
- [ ] Prometheus scrape configuration
- [ ] Grafana dashboard JSON (8 panels)
- [ ] Alert rule YAML (4 critical + 4 warning rules)
- [ ] SLO definitions (5 SLOs)
- [ ] Rollback version snapshot (for Strategy A)

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

- [ ] **2.1.2 — Rule engine commit verification**
  ```bash
  git log --oneline -1 f694618
  git rev-parse --short HEAD
  ```
  **Acceptance:** `HEAD` must be `f694618` (or a descendant that includes it). Rule engine module must not have uncommitted changes:
  ```bash
  git diff --name-only f694618..HEAD -- '**/rule_engine/**' '**/v86_p1_rule/**'
  # Expected: no output (no changes since approval commit)
  ```

- [ ] **2.1.3 — Alias engine commit verification**
  ```bash
  git log --oneline -1 81268a6
  git diff --name-only 81268a6..HEAD -- '**/alias_engine/**' '**/v86_alias/**'
  # Expected: no output
  ```

- [ ] **2.1.4 — CI gate result confirmation**
  ```bash
  # Check the latest CI run summary on the deployment pipeline
  curl -s "https://ci.example.com/api/v1/projects/dshb-gate/runs/latest" \
    | jq '.status, .gates_passed, .gates_total'
  ```
  **Acceptance:** `status == "passed"`, `gates_passed == 12`, `gates_total == 12`.
  ```bash
  # Alias gate
  curl -s "https://ci.example.com/api/v1/projects/dshb-alias-gate/runs/latest" \
    | jq '.status, .gates_passed, .gates_total'
  ```
  **Acceptance:** `status == "passed"`, `gates_passed == 3`, `gates_total == 3`.

- [ ] **2.1.5 — No unexpected changes since tag**
  ```bash
  git log --oneline v86-gate-accept..HEAD
  # Expected: only merge commits and documentation updates since acceptance tag
  git diff --stat v86-gate-accept..HEAD
  ```
  **Acceptance:** No changes to engine source files, alias dictionary, or configuration files.

- [ ] **2.1.6 — Working tree cleanliness**
  ```bash
  git status --porcelain
  # Expected: no output (clean working tree)
  ```

### 2.2 Artifact Integrity

- [ ] **2.2.1 — Bundle file presence and size**
  ```bash
  ls -lh /opt/v86/artifacts/v86-bundle-*.tar.gz
  # Expected: one file, size ~296 KB
  stat --format="%s %n" /opt/v86/artifacts/v86-bundle-*.tar.gz
  ```
  **Acceptance:** Size between 290–302 KB.

- [ ] **2.2.2 — Bundle MD5 checksum**
  ```bash
  md5sum /opt/v86/artifacts/v86-bundle-*.tar.gz
  # Compare with approved baseline
  cat /opt/v86/artifacts/v86-bundle-*.md5
  # Verify match
  md5sum -c /opt/v86/artifacts/v86-bundle-*.md5
  ```
  **Acceptance:** All checksums `OK`.

- [ ] **2.2.3 — Bundle content verification**
  ```bash
  tar -tzf /opt/v86/artifacts/v86-bundle-*.tar.gz | head -40
  # Expected: rule_engine/ alias_engine/ config/ tests/ docs/
  ```
  Verify that all critical paths exist:
  ```bash
  tar -tzf /opt/v86/artifacts/v86-bundle-*.tar.gz \
    | grep -E '(rule_engine/|alias_engine/|config/|requirements|service)'
  ```
  **Acceptance:** `rule_engine/`, `alias_engine/`, `config/` directories present.

- [ ] **2.2.4 — Rule count confirmation**
  ```bash
  tar -xOzf /opt/v86/artifacts/v86-bundle-*.tar.gz rule_engine/rule_definitions.json \
    | jq '.rules | length'
  # Expected: 18
  ```
  Breakdown:
  ```bash
  tar -xOzf /opt/v86/artifacts/v86-bundle-*.tar.gz rule_engine/rule_definitions.json \
    | jq '[.rules[] | select(.priority == "P0")] | length, [.rules[] | select(.priority == "P1")] | length'
  ```
  **Acceptance:** 6 P0, 12 P1.

- [ ] **2.2.5 — Alias dictionary entry count**
  ```bash
  tar -xOzf /opt/v86/artifacts/v86-bundle-*.tar.gz alias_engine/alias_dictionary.json \
    | jq '.entries | length'
  # Expected: 4643
  ```

- [ ] **2.2.6 — Blacklist rule count**
  ```bash
  tar -xOzf /opt/v86/artifacts/v86-bundle-*.tar.gz alias_engine/blacklist.json \
    | jq '.rules | length'
  # Expected: 31
  ```

- [ ] **2.2.7 — Python compatibility check**
  ```bash
  python3 --version
  # Expected: Python 3.12.x
  python3 -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')"; \
  test $? -eq 0
  ```
  **Acceptance:** Python 3.12 confirmed. No external dependencies needed for engine core.

- [ ] **2.2.8 — No external dependency drift**
  ```bash
  # Verify that no non-stdlib import is used in engine core
  tar -xOf /opt/v86/artifacts/v86-bundle-*.tar.gz "rule_engine/*.py" \
    | grep -E '^import |^from ' \
    | grep -vE '^(import|from) (os|sys|json|re|logging|collections|typing|dataclasses|enum|abc|functools|itertools|math|hashlib|uuid|copy|io|time|datetime|pathlib|argparse|multiprocessing|concurrent|signal|threading|socket|http|urllib|struct|base64|random|statistics|textwrap|string|textwrap|contextlib|importlib|inspect|pkgutil|traceback|unittest|warnings|weakref|xml|html|csv|sqlite3|zlib|gzip|tarfile|tempfile|shutil|subprocess|shlex|glob|fnmatch|operator|heapq|bisect|array|codecs|code|token|ast|sysconfig|platform|ctypes|pprint|dis|gc|__future__|typing)' \
    | grep -vE '^\s*#' || echo "PASS: no external deps"
  ```

### 2.3 Environment Setup

- [ ] **2.3.1 — Target instance resources verified**
  ```bash
  nproc
  # Expected: 4 (4vCPU)
  free -h | awk '/Mem:/ {print $2}'
  # Expected: ~4 GB total
  df -h /opt /var | awk 'NR>1 {print $6, $2}'
  # Expected: ~20 GB available on both /opt and /var
  ```

- [ ] **2.3.2 — Network bandwidth check**
  ```bash
  # Quick throughput test
  iperf3 -c <bench-host> -t 5 -1
  # Expected: ≥ 50 Mbps sustained
  ```

- [ ] **2.3.3 — Worker process pool validation**
  ```bash
  # Ensure Python multiprocessing spawn is functional
  python3 -c "
  from multiprocessing import Pool
  with Pool(processes=4) as p:
      results = p.map(lambda x: x*2, [1,2,3,4])
      assert results == [2,4,6,8]
      print(f'PASS: 4-worker pool functional')
  "
  ```

- [ ] **2.3.4 — File descriptor limits**
  ```bash
  ulimit -n
  # Expected: >= 4096
  cat /proc/sys/fs/file-max
  ```
  **Acceptance:** `ulimit -n >= 4096` and `file-max >= 100000`.

- [ ] **2.3.5 — Systemd presence and version**
  ```bash
  systemctl --version | head -1
  # Expected: systemd 245+
  ```

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
  **Expected values:**

  | Variable | Expected | Notes |
  |----------|----------|-------|
  | HOST | `0.0.0.0` or specific interface | Listen address |
  | PORT | `8080` or approved port | HTTP listen port |
  | WORKERS | `4` | Matches 4vCPU |
  | MAX_CONCURRENT | `64` | Max parallel evaluations |
  | TIMEOUT_SECONDS | `30` | Per-request timeout |
  | LOG_LEVEL | `INFO` or `WARNING` | Production log level |

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

- [ ] **2.4.3 — Memory limit in systemd unit**
  ```bash
  grep -E 'MemoryLimit|MemoryMax' /etc/systemd/system/v86-rule-engine.service
  # Expected: MemoryLimit=2G or MemoryMax=2G
  ```

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

---

## Section 3: Deployment Phase (T-2h to T-0)

### 3.1 Pre-Deployment Health Checks

- [ ] **3.1.1 — Existing service health (if v85 running)**
  ```bash
  curl -s http://localhost:8080/health | python3 -m json.tool
  # Expected: {"status": "healthy", ...} for v85
  ```
  If v85 is active, this is a reference baseline. If no prior version, skip.

- [ ] **3.1.2 — Port availability**
  ```bash
  ss -tlnp | grep ":8080"
  # Expected: no listener (port free) or old service stopped
  ```
  If a listener exists, confirm it is the v85 service that will be replaced.

- [ ] **3.1.3 — Database / external dependency connectivity**
  ```bash
  # Test any external DB connections used by the service (if applicable)
  python3 -c "
  import json, sys
  with open('/opt/v86/deployment/config/dependencies.json') as f:
      deps = json.load(f)
  for dep in deps.get('dependencies', []):
      print(f'Testing {dep[\"name\"]}: {dep[\"endpoint\"]}')
      # Attempt TCP connect with 2s timeout
      import socket
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.settimeout(2)
      try:
          sock.connect((dep['host'], dep['port']))
          print(f'PASS: {dep[\"name\"]} reachable')
      except Exception as e:
          print(f'WARN: {dep[\"name\"]} unreachable: {e}')
          # Some deps may be optional
      finally:
          sock.close()
  "
  ```

### 3.2 Service Installation

- [ ] **3.3.1 — Stop any existing service**
  ```bash
  systemctl stop v86-rule-engine.service 2>/dev/null || echo "No prior service found"
  systemctl disable v86-rule-engine.service 2>/dev/null || true
  ```

- [ ] **3.3.2 — Install artifact bundle**
  ```bash
  tar -xzf /opt/v86/artifacts/v86-bundle-*.tar.gz -C /opt/v86/deployment/
  ```

- [ ] **3.3.3 — Install systemd unit file**
  ```bash
  cp /opt/v86/deployment/deploy/v86-rule-engine.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable v86-rule-engine.service
  ```

- [ ] **3.3.4 — Create data directories**
  ```bash
  mkdir -p /opt/v86/data/logs /opt/v86/data/cache /opt/v86/data/temp
  chown -R v86:v86 /opt/v86/data 2>/dev/null || true
  ```

### 3.3 Engine Initialization

- [ ] **3.3.1 — Start service**
  ```bash
  systemctl start v86-rule-engine.service
  sleep 2
  systemctl status v86-rule-engine.service --no-pager
  ```
  **Acceptance:** `Active: active (running)` and `Loaded: loaded`.

- [ ] **3.3.2 — Verify process tree**
  ```bash
  ps aux | grep v86-rule-engine | grep -v grep
  # Expected: parent + 4 worker processes
  ```
  **Acceptance:** 5 total processes (1 parent + 4 workers).

- [ ] **3.3.3 — Verify memory usage within limits**
  ```bash
  systemctl show v86-rule-engine.service --property=MemoryCurrent
  ```
  **Acceptance:** Memory consumption < 2 GB (systemd limit).

- [ ] **3.3.4 — Verify engine loads both engines**
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
  **Acceptance:** `rules == 18`, `alias_entries == 4643`, `status == "healthy"`.

### 3.4 Health Verification

- [ ] **3.4.1 — Health endpoint responds within timeout**
  ```bash
  curl -s -o /dev/null -w "%{http_code} %{time_total}s" http://localhost:8080/health
  ```
  **Acceptance:** HTTP 200, response time < 1s.

- [ ] **3.4.2 — Rule evaluation smoke test**
  ```bash
  curl -s -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" \
    -d '{"input": "benign test sample", "context": {}}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Valid JSON response with `decision` field and all 18 rules evaluated.

- [ ] **3.4.3 — Alias resolution smoke test**
  ```bash
  curl -s -X POST http://localhost:8080/alias/resolve \
    -H "Content-Type: application/json" \
    -d '{"input": "some_alias_entry"}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Response includes resolved alias mapping from F3/F4 layers.

- [ ] **3.4.4 — Full pipeline evaluation (alias → rule)**
  ```bash
  curl -s -X POST http://localhost:8080/pipeline/evaluate \
    -H "Content-Type: application/json" \
    -d '{"input": "test input with alias", "context": {}}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Response includes both `alias_resolution` and `rule_decisions` fields.

- [ ] **3.4.5 — Concurrency test**
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
  **Acceptance:** All responses < 1s. P95 < 5ms for evaluation core (measure via metrics).

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

- [ ] **4.1.3 — Invalid input handling**
  ```bash
  curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8080/evaluate \
    -H "Content-Type: application/json" \
    -d 'not json'
  ```
  **Acceptance:** HTTP 400 or 422 (graceful error, no crash).

- [ ] **4.1.4 — Service crash recovery test**
  ```bash
  # Kill a worker process and verify parent restarts it
  WORKER_PID=$(pgrep -f "v86-rule-engine" | tail -1)
  kill -9 "$WORKER_PID"
  sleep 3
  pgrep -f "v86-rule-engine" | wc -l
  ```
  **Acceptance:** Worker count recovers to 4 within 5s. Health endpoint still returns 200.

### 4.2 Monitoring Verification

- [ ] **4.2.1 — Prometheus scrape target verified**
  ```bash
  curl -s http://localhost:8080/metrics | head -20
  ```
  **Acceptance:** Returns Prometheus text format (`# HELP`, `# TYPE`, metric names).

- [ ] **4.2.2 — Rule engine metrics present**
  ```bash
  curl -s http://localhost:8080/metrics | grep -E "^v86_rule_"
  ```
  **Expected metrics include:**
  - `v86_rule_evaluations_total` — total evaluation counter
  - `v86_rule_evaluation_duration_seconds` — latency histogram
  - `v86_rule_rule_decisions_total` — per-rule decision counter
  - `v86_rule_queue_depth` — current queue depth
  - `v86_rule_queue_rejected_total` — queue rejections

- [ ] **4.2.3 — Alias engine metrics present**
  ```bash
  curl -s http://localhost:8080/metrics | grep -E "^v86_alias_"
  ```
  **Expected metrics include:**
  - `v86_alias_resolutions_total`
  - `v86_alias_resolution_duration_seconds`
  - `v86_alias_blacklist_hits_total`
  - `v86_alias_layer_hits` (F1/F2/F3/F4 breakdown)

- [ ] **4.2.4 — All metric categories present**
  ```bash
  curl -s http://localhost:8080/metrics | grep -E "^# TYPE" | wc -l
  ```
  **Acceptance:** ≥ 80 unique metric families (90 metrics across 8 categories).

- [ ] **4.2.5 — Grafana dashboard loaded**
  ```bash
  # Check dashboard is provisioned
  curl -s -u admin:admin "http://<grafana-host>/api/dashboards/uid/v86-rule-engine" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Dashboard: {d[\"dashboard\"][\"title\"]}, panels: {len(d[\"dashboard\"][\"panels\"])}')"
  ```
  **Acceptance:** 8 panels.

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

### 4.3 Alert Test

- [ ] **4.3.1 — Trigger a test alert (error rate spike)**
  ```bash
  # Generate error traffic to trip the alert threshold
  for i in $(seq 1 50); do
    curl -s -X POST http://localhost:8080/evaluate \
      -H "Content-Type: application/json" \
      -d 'invalid json to trigger error' &
  done
  wait
  sleep 60
  # Check if alert fired
  curl -s "http://<prometheus-host>/api/v1/alerts" \
    | python3 -c "
  import sys, json
  alerts = json.load(sys.stdin).get('data',{}).get('alerts',[])
  v86 = [a for a in alerts if 'v86' in a.get('labels',{}).get('rule','').lower()]
  print(f'V86 alerts firing: {len(v86)}')
  for a in v86[:5]:
      print(f'  - {a[\"labels\"][\"alertname\"]}: {a[\"state\"]}')
  "
  ```
  **Acceptance:** At least one alert fires within 2 minutes of error traffic.

- [ ] **4.3.2 — Verify alert routing**
  ```bash
  # Check Alertmanager received the alert
  curl -s "http://<alertmanager-host>/api/v2/alerts" \
    | python3 -c "
  import sys, json
  alerts = json.load(sys.stdin)
  v86 = [a for a in alerts if 'v86' in str(a.get('labels',{})).lower()]
  print(f'Alertmanager V86 alerts: {len(v86)}')
  for a in v86[:3]:
      print(f'  - {a[\"labels\"].get(\"alertname\",\"?\")}: status={a[\"status\"].get(\"state\",\"?\")}')
  "
  ```

- [ ] **4.3.3 — SLO health dashboard**
  ```bash
  # Verify SLO burn rate is below thresholds
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
  "
  ```

### 4.4 Rollback Readiness

- [ ] **4.4.1 — Rollback Strategy A package verified**
  ```bash
  ls -lh /opt/v86/rollback/v85-*/ 2>/dev/null || echo "WARNING: v85 snapshot missing"
  cat /opt/v86/rollback/version_manifest.json
  ```
  **Expected manifest content:**
  ```json
  {
    "from_version": "v86",
    "to_version": "v85",
    "bundle": "v85-bundle-*.tar.gz",
    "rto_seconds": 78,
    "service": "v86-rule-engine.service"
  }
  ```
  Verify bundle checksum:
  ```bash
  cd /opt/v86/rollback/
  md5sum -c v85-*.md5
  ```

- [ ] **4.4.2 — Rollback Strategy B switch tested**
  ```bash
  # Strategy B uses dynamic version switch without restart
  curl -s -X POST http://localhost:8080/admin/rollback \
    -H "Content-Type: application/json" \
    -d '{"strategy": "B", "dry_run": true}' \
    | python3 -m json.tool
  ```
  **Acceptance:** Returns plan with `rto_seconds: 30`, `strategy: "B"`, `ready: true`.
  > **Note:** This is a dry-run only. Do not execute real rollback unless incident triggers.

- [ ] **4.4.3 — Rollback script executable**
  ```bash
  which /opt/v86/scripts/rollback.sh
  bash -n /opt/v86/scripts/rollback.sh
  # Expected: no syntax errors
  ```

### 4.5 Gray Release Initiation

- [ ] **4.5.1 — Feature flag initialized**
  ```bash
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "enabled": true, "weight": 0}' \
    | python3 -m json.tool
  ```

- [ ] **4.5.2 — Canarize at 10% for 15 minutes**
  ```bash
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "weight": 10}'
  ```
  **Observation window:** 15 minutes. Monitor:
  ```bash
  watch -n 30 'curl -s http://localhost:8080/metrics | grep "v86_rule_evaluations_total"'
  ```

- [ ] **4.5.3 — Promote to 30% if 10% is stable**
  ```bash
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "weight": 30}'
  ```
  **Observation window:** 15 minutes.

- [ ] **4.5.4 — Promote to 100% if 30% is stable**
  ```bash
  curl -s -X POST http://localhost:8080/admin/flags \
    -H "Content-Type: application/json" \
    -d '{"flag": "v86", "weight": 100}'
  ```

- [ ] **4.5.5 — Full traffic health confirmation**
  ```bash
  sleep 120
  curl -s http://localhost:8080/metrics | grep -E "(v86_rule_evaluations_total|v86_rule_evaluation_duration_seconds_bucket)"
  ```
  **Acceptance:** Evaluation rate matches pre-deployment baseline, no spike in error or latency metrics.

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

### E6. Force Worker Restart

```bash
systemctl restart v86-rule-engine.service
```
**Verify:**
```bash
sleep 3
curl -s http://localhost:8080/health | python3 -m json.tool
```

---

## Section 6: Go/No-Go Decision Matrix

| # | Check | Threshold | Result |
|---|-------|-----------|--------|
| 1 | CI gates pass | 12/12 + 3/3 | `[ ] PASS` / `[ ] FAIL` |
| 2 | Rule count | 18 rules (6 P0 + 12 P1) | `[ ] PASS` / `[ ] FAIL` |
| 3 | Alias entries | 4,643 entries, 31 blacklist rules | `[ ] PASS` / `[ ] FAIL` |
| 4 | Bundle MD5 checksum | All match baseline | `[ ] PASS` / `[ ] FAIL` |
| 5 | Python version | 3.12.x | `[ ] PASS` / `[ ] FAIL` |
| 6 | Health endpoint | `{"status": "healthy", "rules": 18}` | `[ ] PASS` / `[ ] FAIL` |
| 7 | Worker processes | 4 workers + 1 parent | `[ ] PASS` / `[ ] FAIL` |
| 8 | Memory under limit | < 2 GB | `[ ] PASS` / `[ ] FAIL` |
| 9 | Concurrency (64 parallel) | All return HTTP 200 | `[ ] PASS` / `[ ] FAIL` |
| 10 | Latency P95 | < 5 ms | `[ ] PASS` / `[ ] FAIL` |
| 11 | Error rate | < 1% | `[ ] PASS` / `[ ] FAIL` |
| 12 | False positive rate | < 5% | `[ ] PASS` / `[ ] FAIL` |
| 13 | Queue rejection rate | < 0.1% | `[ ] PASS` / `[ ] FAIL` |
| 14 | Availability SLO | 99.9% | `[ ] PASS` / `[ ] FAIL` |
| 15 | Prometheus metrics | ≥ 80 families, 8 categories | `[ ] PASS` / `[ ] FAIL` |
| 16 | Grafana dashboard | 8 panels loaded | `[ ] PASS` / `[ ] FAIL` |
| 17 | Alert rules | 4 critical + 4 warning | `[ ] PASS` / `[ ] FAIL` |
| 18 | Alert test fires | Alert received within 2 min | `[ ] PASS` / `[ ] FAIL` |
| 19 | Rollback Strategy A ready | Manifest + bundle verified | `[ ] PASS` / `[ ] FAIL` |
| 20 | Rollback Strategy B ready | Dry-run returns `ready: true` | `[ ] PASS` / `[ ] FAIL` |
| 21 | Gray release 10% stable | 15 min, no metric degradation | `[ ] PASS` / `[ ] FAIL` |
| 22 | Gray release 30% stable | 15 min, no metric degradation | `[ ] PASS` / `[ ] FAIL` |
| 23 | Gray release 100% promoted | Full traffic healthy | `[ ] PASS` / `[ ] FAIL` |
| 24 | SRE sign-off | On-call engineer confirms | `[ ] PASS` / `[ ] FAIL` |

### Decision Criteria

| Pass Count | Decision |
|------------|----------|
| 24 / 24 | ✅ **GO** — Full deployment approved |
| 21–23 / 24 | ⚠️ **CONDITIONAL GO** — Document deviation, SRE sign-off required |
| 18–20 / 24 | ❌ **NO-GO** — Fix failures, re-run checklist from first failed item |
| < 18 / 24 | 🚫 **HALT** — Deployment blocked. Revert to pre-deployment state |

### Sign-Off Log

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Release Engineer | | | |
| SRE On-Call | | | |
| QA Lead | | | |
| Engineering Manager | | | |

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

## Appendix B: Environment Variable Quick Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | HTTP listen address |
| `PORT` | `8080` | HTTP listen port |
| `WORKERS` | `4` | Number of worker processes |
| `MAX_CONCURRENT` | `64` | Max concurrent evaluations |
| `TIMEOUT_SECONDS` | `30` | Per-request evaluation timeout |
| `LOG_LEVEL` | `INFO` | Log verbosity (DEBUG/INFO/WARNING/ERROR) |

## Appendix C: systemd Service File (Reference)

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

*End of V86 Pre-Flight Checklist — DSHB_V86_RULE_ALIAS_JOIN_PROD_STRESS_GATE_ACCEPT_AND_RISK_REGISTER*
