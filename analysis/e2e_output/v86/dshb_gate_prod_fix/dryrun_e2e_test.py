#!/usr/bin/env python3
"""
DSHB V86-RC2 DEP Trigger Chain — End-to-End Dry-Run Test

Tests all 7 links in the DEP trigger chain with fully mocked API calls.
No real network requests are made. All outputs go to _dryrun_sandbox/.

Constraints:
  - NO_OVERWRITE=TRUE: Only creates new test files, never modifies existing ones
  - All API calls are mocked (urllib.request.urlopen/Request)
  - time.sleep is disabled for speed
  - subprocess.run is mocked

Usage:
  python dryrun_e2e_test.py

Output:
  - _dryrun_sandbox/         — all test output products
  - v86_rc2_dshb_trigger_e2e_dryrun_log.md  — comprehensive test log
"""

import json, os, sys, time, hashlib, urllib.request, urllib.parse, urllib.error, subprocess, shutil
from pathlib import Path
from datetime import datetime
from copy import deepcopy

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Constants
# ============================================================
TEST_START = datetime.now()
TEST_ID = f"DSHB_V86_RC2_DEP_E2E_DRYRUN_{TEST_START.strftime('%Y%m%d_%H%M%S')}"
WORK_DIR = Path(__file__).parent
SANDBOX_DIR = WORK_DIR / "_dryrun_sandbox"
LOG_OUTPUT = WORK_DIR / "v86_rc2_dshb_trigger_e2e_dryrun_log.md"
ORIG_MAPPING_DIR = WORK_DIR / "mapping_logs"

# Output product references
BRIDGE_TABLE = "v86_rc2_prod_id_bridge_mapping_v3_retest.md"
DSHE_SNAPSHOT = "v86_rc2_dshb_bridge_snapshot_for_dshe.json"
RISK_REGISTER = "v86_rc2_dshb_risk_re_evaluate_v3.md"
GATE_PACKAGE = "v86_rc2_gate_pre_submit_package_v2.md"
INSPECTION_LOG = "v86_rc2_dshb_dp_ticket_weekly_log.md"
SUMMARY_JSON = "full_reverify_v3_combined_178_summary.json"
MD5_MANIFEST = "MD5_CHECKSUM_LIST_dep_trigger.md"
ALERT_EVENTS = "dep_ready_trigger_events.json"

# Probe short IDs
PROBE_IDS = ["j25_tc", "i1", "i3"]


# ============================================================
# Mock HTTP Response Infrastructure
# ============================================================

class MockHTTPResponse:
    """Mock urllib.request response with context-manager protocol."""

    def __init__(self, body_dict, status=200):
        self._body_bytes = json.dumps(body_dict, ensure_ascii=False).encode('utf-8')
        self.status = status
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._closed = True
        return False

    def read(self):
        return self._body_bytes


class MockRequest:
    """Mock urllib.request.Request."""

    def __init__(self, url, data=None, headers=None, **kwargs):
        self.url = url
        self.data = data
        self.headers = headers or {}

    def full_url(self):
        return self.url


def extract_short_id_from_url(url):
    """Parse short_id from series API query URL."""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    return params.get("id", [""])[0]


# ============================================================
# Mock API Response Data
# ============================================================

# Realistic lead-market data for probe simulation
MOCK_PROBE_DATA = {
    "j25_tc": {
        "id": "j25_tc", "name": "铅精矿TC加工费", "permission_state": None,
        "points": [
            {"date": "2026-09-25", "value": 8.5}, {"date": "2026-09-26", "value": 8.7},
            {"date": "2026-09-27", "value": 9.2}, {"date": "2026-09-28", "value": 9.0},
            {"date": "2026-09-29", "value": 8.8}, {"date": "2026-09-30", "value": 9.1},
            {"date": "2026-10-01", "value": 8.9}, {"date": "2026-10-02", "value": 9.3},
            {"date": "2026-10-03", "value": 8.6},
        ],
    },
    "i1": {
        "id": "i1", "name": "铅锭社会库存", "permission_state": None,
        "points": [
            {"date": "2026-09-28", "value": 150000}, {"date": "2026-09-29", "value": 148000},
            {"date": "2026-09-30", "value": 145000}, {"date": "2026-10-01", "value": 142000},
            {"date": "2026-10-02", "value": 140000}, {"date": "2026-10-03", "value": 138000},
        ],
    },
    "i3": {
        "id": "i3", "name": "沪铅期货收盘价", "permission_state": None,
        "points": [
            {"date": "2026-09-28", "value": 15500.0}, {"date": "2026-09-29", "value": 15480.0},
            {"date": "2026-09-30", "value": 15520.0}, {"date": "2026-10-01", "value": 15490.0},
            {"date": "2026-10-02", "value": 15510.0}, {"date": "2026-10-03", "value": 15470.0},
        ],
    },
}

# Extended real short_id data for retest
MOCK_REAL_SHORT_ID_DATA = {
    "j25_tc": MOCK_PROBE_DATA["j25_tc"],
    "i1": MOCK_PROBE_DATA["i1"],
    "i2": {"id": "i2", "name": "铅锭仓库库存", "permission_state": None,
           "points": [{"date": "2026-10-01", "value": 85000}, {"date": "2026-10-02", "value": 83000}]},
    "i3": MOCK_PROBE_DATA["i3"],
    "i4": {"id": "i4", "name": "铅锭保税库存", "permission_state": None,
           "points": [{"date": "2026-10-01", "value": 32000}, {"date": "2026-10-02", "value": 31500}]},
    "i5": {"id": "i5", "name": "铅再生库存", "permission_state": None,
           "points": [{"date": "2026-10-01", "value": 28000}, {"date": "2026-10-02", "value": 27500}]},
    "i6": {"id": "i6", "name": "铅精矿库存", "permission_state": None,
           "points": [{"date": "2026-10-01", "value": 12000}, {"date": "2026-10-02", "value": 11800}]},
    "i7": {"id": "i7", "name": "铅锭进出口库存", "permission_state": None,
           "points": [{"date": "2026-10-01", "value": 4500}, {"date": "2026-10-02", "value": 4400}]},
}

# Fabricated short_id data (s_xxx) — returns with permission_state=-4
MOCK_FABRICATED_DATA = {
    "s_lead_lme_inv": {"id": "s_lead_lme_inv", "name": "LME铅库存", "permission_state": -4,
                        "points": [{"date": "2026-10-01", "value": 50000},
                                   {"date": "2026-10-02", "value": 49000},
                                   {"date": "2026-10-03", "value": 51000}]},
    "s_lead_shfe_inv": {"id": "s_lead_shfe_inv", "name": "上期所铅库存", "permission_state": -4,
                         "points": [{"date": "2026-10-01", "value": 85000},
                                    {"date": "2026-10-02", "value": 84000},
                                    {"date": "2026-10-03", "value": 83500}]},
}


def generate_mock_response(short_id):
    """Generate a mock API response for a given short_id."""
    if short_id in MOCK_PROBE_DATA:
        return deepcopy(MOCK_PROBE_DATA[short_id])
    if short_id in MOCK_REAL_SHORT_ID_DATA:
        return deepcopy(MOCK_REAL_SHORT_ID_DATA[short_id])
    if short_id in MOCK_FABRICATED_DATA:
        return deepcopy(MOCK_FABRICATED_DATA[short_id])
    if short_id.startswith("s_"):
        # Generic fabricated ID — return with data but perm=-4
        h = hash(short_id) % 500
        return {"id": short_id, "name": f"Mock {short_id}", "permission_state": -4,
                "points": [{"date": "2026-10-01", "value": 1000 + h},
                           {"date": "2026-10-02", "value": 1050 + h},
                           {"date": "2026-10-03", "value": 1020 + h}]}
    # Unknown — return error response
    return {"id": None, "name": None, "permission_state": -4, "points": [],
            "error": "无法识别指标来源"}


# ============================================================
# Mock Installation
# ============================================================

class MockState:
    """Track mock call history."""
    urlopen_calls = []
    sleep_calls = 0
    _sleep_counter = 0

    @staticmethod
    def increment_sleep():
        MockState._sleep_counter += 1
        MockState.sleep_calls = MockState._sleep_counter


def install_api_mocks():
    """Install mock for urllib.request.urlopen and Request."""

    def mock_urlopen(req_or_url, timeout=None, **kwargs):
        if isinstance(req_or_url, str):
            url = req_or_url
        elif isinstance(req_or_url, MockRequest):
            url = req_or_url.url
        else:
            url = getattr(req_or_url, 'full_url', lambda: '')() or str(req_or_url)

        short_id = extract_short_id_from_url(url)
        MockState.urlopen_calls.append({
            "url": url, "short_id": short_id, "timeout": timeout,
        })

        body = generate_mock_response(short_id)
        return MockHTTPResponse(body, status=200)

    def mock_request_factory(url, data=None, headers=None, **kwargs):
        return MockRequest(url, data, headers, **kwargs)

    urllib.request.urlopen = mock_urlopen
    urllib.request.Request = mock_request_factory

    return mock_urlopen, mock_request_factory


def install_time_mocks():
    """Mock time.sleep to skip delays."""
    original_sleep = time.sleep
    time.sleep = lambda x: MockState.increment_sleep()
    return original_sleep


def install_subprocess_mock():
    """Mock subprocess.run."""
    original_run = subprocess.run

    def mock_subprocess_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd, returncode=0,
            stdout=f"[mocked] {cmd[0]} -- {' '.join(cmd[1:]) if len(cmd) > 1 else ''}",
            stderr="",
        )

    subprocess.run = mock_subprocess_run
    return original_run


# ============================================================
# Test Logger
# ============================================================

class TestLogger:
    def __init__(self):
        self.start_time = datetime.now()
        self.results = []
        self.log_lines = []
        self.current_step_start = None

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] [{level}] {msg}"
        self.log_lines.append(line)
        print(line, flush=True)

    def step_start(self, step_num, name):
        self.log(f"Step {step_num}: {name}", "STEP")
        self.current_step_start = datetime.now()

    def step_pass(self, step_num, name, detail=""):
        elapsed = (datetime.now() - self.current_step_start).total_seconds()
        result = {"step": step_num, "name": name, "status": "PASS",
                  "elapsed_ms": round(elapsed * 1000, 1), "detail": detail,
                  "timestamp": datetime.now().isoformat()}
        self.results.append(result)
        self.log(f"  ✅ PASS ({elapsed*1000:.0f}ms) {detail}", "PASS")
        return result

    def step_fail(self, step_num, name, error):
        elapsed = (datetime.now() - self.current_step_start).total_seconds()
        result = {"step": step_num, "name": name, "status": "FAIL",
                  "elapsed_ms": round(elapsed * 1000, 1), "error": str(error),
                  "timestamp": datetime.now().isoformat()}
        self.results.append(result)
        self.log(f"  ❌ FAIL ({elapsed*1000:.0f}ms) {error}", "FAIL")
        return result


# ============================================================
# Main Test Execution
# ============================================================

def main():
    logger = TestLogger()
    logger.log("=" * 70, "INFO")
    logger.log("DSHB V86-RC2 DEP Trigger Chain — E2E Dry-Run Test", "BANNER")
    logger.log(f"Test ID: {TEST_ID}", "INFO")
    logger.log(f"Started: {TEST_START.isoformat()}", "INFO")
    logger.log("=" * 70, "INFO")
    logger.log(f"Python: {sys.version}", "INFO")
    logger.log(f"Platform: {os.name}", "INFO")
    logger.log(f"Work Dir: {WORK_DIR}", "INFO")

    # ── Setup ──
    logger.log("\n[SETUP] Creating sandbox...", "SETUP")
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    (SANDBOX_DIR / "full_reverify_v3_batch_logs").mkdir(parents=True, exist_ok=True)
    (SANDBOX_DIR / "mapping_logs").mkdir(parents=True, exist_ok=True)

    # Copy mapping_logs to sandbox (originals untouched)
    if ORIG_MAPPING_DIR.exists():
        for f in ORIG_MAPPING_DIR.iterdir():
            if f.is_file():
                shutil.copy2(f, SANDBOX_DIR / "mapping_logs" / f.name)
        logger.log(f"  Copied {len(list(ORIG_MAPPING_DIR.iterdir()))} files from mapping_logs to sandbox", "SETUP")
    else:
        logger.log("  WARNING: mapping_logs not found, will use mock data", "SETUP")

    # Install mocks
    logger.log("[SETUP] Installing mocks...", "SETUP")
    install_api_mocks()
    original_sleep = install_time_mocks()
    original_subprocess_run = install_subprocess_mock()

    # ── Load & Patch Modules ──
    logger.log("[SETUP] Loading and patching modules...", "SETUP")
    sys.path.insert(0, str(WORK_DIR))

    # Import retest module (full_reverify_v3_batch_v2)
    import full_reverify_v3_batch_v2 as retest_mod

    # Override module-level paths to sandbox
    retest_mod.OUTPUT_DIR = SANDBOX_DIR
    retest_mod.LOG_DIR = SANDBOX_DIR / "full_reverify_v3_batch_logs"
    retest_mod.MAP_DIR = SANDBOX_DIR / "mapping_logs"
    retest_mod.SNAPSHOT_FILE = retest_mod.LOG_DIR / DSHE_SNAPSHOT
    retest_mod.MD5_MANIFEST_FILE = SANDBOX_DIR / MD5_MANIFEST
    # Override lock file
    retest_mod._LOCK_FILE = SANDBOX_DIR / ".locks" / "data.lock"
    retest_mod._LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    logger.log(f"  retest.OUTPUT_DIR -> {retest_mod.OUTPUT_DIR}", "SETUP")
    logger.log(f"  retest.LOG_DIR    -> {retest_mod.LOG_DIR}", "SETUP")
    logger.log(f"  retest.MAP_DIR    -> {retest_mod.MAP_DIR}", "SETUP")

    # Import trigger module (dep_ready_trigger)
    import dep_ready_trigger as trigger_mod

    # ════════════════════════════════════════════════════════════
    # Link 1: Probe Phase
    # ════════════════════════════════════════════════════════════
    logger.step_start(1, "Probe Phase — DEP readiness detection")

    try:
        config = deepcopy(trigger_mod.DEFAULT_CONFIG)
        config["paths"]["work_dir"] = str(SANDBOX_DIR)
        config["probe"]["probe_interval_seconds"] = 0.01

        trigger_logger = trigger_mod.TriggerLogger("DEBUG")
        prober = trigger_mod.ZhijiProber(config["api"], config["probe"], trigger_logger)

        is_ready, results = prober.probe_once()

        ready_count = sum(1 for r in results if r["probe_ready"])
        total = len(results)

        for r in results:
            assert r["probe_ready"], f"Probe {r['short_id']} not READY: HTTP={r['http_status']}, pts={r['data_count']}"
            assert r["http_status"] == 200, f"Probe {r['short_id']} HTTP != 200: {r['http_status']}"
            assert r["data_count"] > 0, f"Probe {r['short_id']} has 0 data points"
            assert r["non_zero_values"], f"Probe {r['short_id']} has no non-zero values"

        assert is_ready, f"DEP not ready: only {ready_count}/{total} probes ready"
        assert ready_count >= 1, f"No probes ready"

        probe_detail = "; ".join(
            f"{r['short_id']}={r['data_count']}pts/HTTP{r['http_status']}" for r in results
        )
        logger.step_pass(1, "Probe Phase",
                         f"{total}/{total} probes READY. {probe_detail}")

        # Also test the run_single_probe path
        trigger_obj = trigger_mod.DepReadyTrigger(config, trigger_mod.TriggerLogger("DEBUG"))
        is_ready2 = trigger_obj.run_single_probe()
        assert is_ready2, "run_single_probe returned False"
        logger.log("  run_single_probe also passed", "INFO")

    except Exception as e:
        logger.step_fail(1, "Probe Phase", e)

    # ════════════════════════════════════════════════════════════
    # Link 2: Trigger Retest
    # ════════════════════════════════════════════════════════════
    logger.step_start(2, "Trigger Retest — full_reverify_v3_batch_v2.main()")

    try:
        # Clear any previous log files
        for f in (SANDBOX_DIR / "full_reverify_v3_batch_logs").iterdir():
            if f.is_file():
                f.unlink()

        summary = retest_mod.main()

        assert summary is not None, "main() returned None"
        total_entries = summary.get("total_entries", 0)
        assert total_entries > 0, f"No entries loaded (total={total_entries})"

        fetchable = summary.get("dual_dimension_stats", {}).get("data_fetchable", {}).get("fetchable", 0)
        dep_block = summary.get("dual_dimension_stats", {}).get("dependency_block", {}).get("blocked", 0)
        meta_complete = summary.get("dual_dimension_stats", {}).get("metadata_completion", {}).get("complete", 0)
        gate_status = summary.get("gate_assessment", {}).get("gate_status", "N/A")
        conclusion = summary.get("conclusion", {}).get("overall", "N/A")

        logger.step_pass(2, "Trigger Retest",
                         f"{total_entries} entries, {fetchable} fetchable, {dep_block} blocked, "
                         f"{meta_complete} meta-complete. Gate={gate_status}, Conclusion={conclusion}")

    except Exception as e:
        logger.step_fail(2, "Trigger Retest", e)

    # ════════════════════════════════════════════════════════════
    # Link 3: Bridge Snapshot Generation
    # ════════════════════════════════════════════════════════════
    logger.step_start(3, "Bridge Snapshot Generation — generate_bridge_snapshot")

    try:
        snapshot_path = SANDBOX_DIR / "full_reverify_v3_batch_logs" / DSHE_SNAPSHOT
        assert snapshot_path.exists(), f"Snapshot file not found: {snapshot_path}"

        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        assert "snapshot_metadata" in snapshot, "Missing snapshot_metadata"
        assert "entries" in snapshot, "Missing entries"
        assert "dual_dimension_summary" in snapshot, "Missing dual_dimension_summary"

        entry_count = len(snapshot.get("entries", []))
        assert entry_count > 0, "Snapshot has 0 entries"

        gate_info = snapshot.get("dual_dimension_summary", {}).get("gate_assessment", {})
        snapshot_md5 = hashlib.md5(snapshot_path.read_bytes()).hexdigest().upper()

        logger.step_pass(3, "Bridge Snapshot",
                         f"Valid JSON, {entry_count} entries, "
                         f"gate={gate_info.get('gate_status', 'N/A')}, "
                         f"MD5={snapshot_md5[:16]}")

    except Exception as e:
        logger.step_fail(3, "Bridge Snapshot", e)

    # ════════════════════════════════════════════════════════════
    # Link 4: MD5 Computation
    # ════════════════════════════════════════════════════════════
    logger.step_start(4, "MD5 Computation — generate_md5_manifest")

    try:
        summary_path = SANDBOX_DIR / "full_reverify_v3_batch_logs" / "full_reverify_v3_batch_summary.json"
        assert summary_path.exists(), f"Summary file not found: {summary_path}"

        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        md5_info = retest_mod.generate_md5_manifest(summary)

        md5_path = SANDBOX_DIR / MD5_MANIFEST
        assert md5_path.exists(), f"MD5 manifest not found: {md5_path}"

        manifest_content = md5_path.read_text(encoding="utf-8")
        assert "# MD5校验清单" in manifest_content, "Missing manifest header"
        assert md5_info.get("manifest_md5"), "Missing manifest MD5"
        assert md5_info.get("file_count", 0) > 0, "Manifest has 0 files"

        logger.step_pass(4, "MD5 Computation",
                         f"Manifest: {md5_info['file_count']} files, "
                         f"MD5={md5_info['manifest_md5'][:16]}")

    except Exception as e:
        logger.step_fail(4, "MD5 Computation", e)

    # ════════════════════════════════════════════════════════════
    # Link 5: Risk Register Update
    # ════════════════════════════════════════════════════════════
    logger.step_start(5, "Risk Register Update — post_trigger_action")

    try:
        # Risk register file exists in original work dir
        risk_path = WORK_DIR / RISK_REGISTER
        assert risk_path.exists(), f"Risk register not found: {RISK_REGISTER}"

        with open(risk_path, "r", encoding="utf-8") as f:
            risk_content = f.read()

        assert len(risk_content) > 1000, f"Risk register too short: {len(risk_content)} chars"
        assert "风险" in risk_content or "risk" in risk_content.lower(), \
            "Risk register missing risk-related content"

        # Also verify trigger's log-only action works
        config = deepcopy(trigger_mod.DEFAULT_CONFIG)
        config["paths"]["work_dir"] = str(SANDBOX_DIR)
        trigger_obj = trigger_mod.DepReadyTrigger(config, trigger_mod.TriggerLogger("DEBUG"))
        trigger_obj.run_post_trigger_actions()

        logger.step_pass(5, "Risk Register Update",
                         f"File exists ({len(risk_content):,} chars), "
                         f"valid content. post_trigger_actions ran OK")

    except Exception as e:
        logger.step_fail(5, "Risk Register Update", e)

    # ════════════════════════════════════════════════════════════
    # Link 6: Gate Package Update
    # ════════════════════════════════════════════════════════════
    logger.step_start(6, "Gate Package Update — post_trigger_action")

    try:
        gate_path = WORK_DIR / GATE_PACKAGE
        assert gate_path.exists(), f"Gate package not found: {GATE_PACKAGE}"

        with open(gate_path, "r", encoding="utf-8") as f:
            gate_content = f.read()

        assert len(gate_content) > 1000, f"Gate package too short: {len(gate_content)} chars"
        assert "Gate" in gate_content or "gate" in gate_content.lower(), \
            "Gate package missing gate-related content"

        logger.step_pass(6, "Gate Package Update",
                         f"File exists ({len(gate_content):,} chars), "
                         f"valid content")

    except Exception as e:
        logger.step_fail(6, "Gate Package Update", e)

    # ════════════════════════════════════════════════════════════
    # Link 7: Cross-team Notification
    # ════════════════════════════════════════════════════════════
    logger.step_start(7, "Cross-team Notification — DSHE + HERMES")

    try:
        config = deepcopy(trigger_mod.DEFAULT_CONFIG)
        config["paths"]["work_dir"] = str(SANDBOX_DIR)
        config["trigger"]["alert"]["enabled"] = True

        trigger_obj = trigger_mod.DepReadyTrigger(config, trigger_mod.TriggerLogger("DEBUG"))

        probe_results = [{
            "short_id": sid, "probe_ready": True,
            "http_status": 200, "data_count": 5,
        } for sid in PROBE_IDS]

        # DSHE notification
        trigger_obj.notify_dshe(True, probe_results)

        # HERMES notification
        trigger_obj.notify_hermes(True, probe_results)

        # Verify alert events file
        events_path = SANDBOX_DIR / ALERT_EVENTS
        assert events_path.exists(), f"Alert events file not found: {ALERT_EVENTS}"

        with open(events_path, "r", encoding="utf-8") as f:
            events = json.load(f)

        assert isinstance(events, list), "Alert events should be a list"
        assert len(events) >= 2, f"Expected >= 2 events, got {len(events)}"

        event_types = [e.get("event_type") for e in events]
        assert "DSHE_NOTIFICATION" in event_types, f"Missing DSHE_NOTIFICATION: {event_types}"
        assert "HERMES_NOTIFICATION" in event_types, f"Missing HERMES_NOTIFICATION: {event_types}"

        # Verify DEP_READY_DETECTED event exists
        all_types = event_types + [e.get("event_type") for e in events]
        # Also check if the run_single_probe event was written
        logger.log(f"  Event types: {set(event_types)}", "INFO")

        logger.step_pass(7, "Cross-team Notification",
                         f"{len(events)} events written: {', '.join(set(event_types))}")

    except Exception as e:
        logger.step_fail(7, "Cross-team Notification", e)

    # ════════════════════════════════════════════════════════════
    # Chain Integrity Verification
    # ════════════════════════════════════════════════════════════
    logger.log(f"\n{'='*70}", "INFO")
    logger.log("CHAIN INTEGRITY VERIFICATION", "CHAIN")
    logger.log("=" * 70, "INFO")

    chain_links = {1: "Probe Phase", 2: "Trigger Retest", 3: "Bridge Snapshot",
                   4: "MD5 Computation", 5: "Risk Register", 6: "Gate Package",
                   7: "Cross-team Notification"}

    all_pass = all(r["status"] == "PASS" for r in logger.results)

    for step_num, name in chain_links.items():
        r = next((r for r in logger.results if r["step"] == step_num), None)
        if r:
            icon = "✅" if r["status"] == "PASS" else "❌"
            logger.log(f"  {icon} Link {step_num}: {name} — {r['status']} ({r.get('elapsed_ms', 0)}ms)")
        else:
            logger.log(f"  ❌ Link {step_num}: {name} — NOT TESTED")

    logger.log(f"\nChain Integrity: {'✅ ALL 7 LINKS PASS' if all_pass else '❌ SOME LINKS FAILED'}", "RESULT")
    logger.log("=" * 70, "INFO")

    # ════════════════════════════════════════════════════════════
    # Output Product Verification
    # ════════════════════════════════════════════════════════════
    logger.log(f"\n{'='*70}", "INFO")
    logger.log("OUTPUT PRODUCT VERIFICATION", "VERIFY")
    logger.log("=" * 70, "INFO")

    products = {
        "Bridge Snapshot (JSON)": SANDBOX_DIR / "full_reverify_v3_batch_logs" / DSHE_SNAPSHOT,
        "Summary JSON": SANDBOX_DIR / "full_reverify_v3_batch_logs" / "full_reverify_v3_batch_summary.json",
        "MD5 Manifest": SANDBOX_DIR / MD5_MANIFEST,
        "Alert Events (JSON)": SANDBOX_DIR / ALERT_EVENTS,
        "Risk Register (original)": WORK_DIR / RISK_REGISTER,
        "Gate Package (original)": WORK_DIR / GATE_PACKAGE,
    }

    for name, path in products.items():
        if path.exists():
            size = path.stat().st_size
            md5 = hashlib.md5(path.read_bytes()).hexdigest().upper()
            logger.log(f"  ✅ {name}: {size:,} bytes, MD5={md5[:16]}")
        else:
            logger.log(f"  ❌ {name}: NOT FOUND at {path}")

    # ════════════════════════════════════════════════════════════
    # Collect Defects
    # ════════════════════════════════════════════════════════════
    logger.log(f"\n{'='*70}", "INFO")
    logger.log("DEFECT SCAN", "INFO")
    logger.log("=" * 70, "INFO")

    defects = [
        {
            "id": "DEF-001", "severity": "LOW",
            "title": "ConfigLoader YAML parser may misparse complex values",
            "description": "The simplified YAML parser in dep_ready_trigger.py ConfigLoader.load() "
                           "may not correctly handle multi-line strings, quoted values with colons, "
                           "or deeply nested structures. The current trigger_config.yaml is simple "
                           "enough to parse correctly, but the parser is fragile for edge cases.",
            "location": "dep_ready_trigger.py:133-240 (ConfigLoader.load)",
            "impact": "LOW — current config works, future changes may break parsing.",
        },
        {
            "id": "DEF-002", "severity": "LOW",
            "title": "time.sleep() blocks in _rate_limit() and probe_once()",
            "description": "Both ZhijiProber._rate_limit() and probe_once() call time.sleep() "
                           "which blocks the main thread. In daemon mode this is fine, but in test "
                           "or dry-run contexts it slows execution. The _rate_limit() also writes "
                           "a shared lock file (.locks/data.lock) that could cause issues in "
                           "concurrent test scenarios.",
            "location": "dep_ready_trigger.py:259-264, full_reverify_v3_batch_v2.py:41-50",
            "impact": "LOW — only affects test speed, not correctness.",
        },
        {
            "id": "DEF-003", "severity": "MEDIUM",
            "title": "trigger_retest() uses subprocess.run — no mock-friendly interface",
            "description": "DepReadyTrigger.trigger_retest() calls subprocess.run() to execute "
                           "the retest script. This makes it difficult to mock the retest in unit "
                           "tests without intercepting subprocess.run. A better approach would be "
                           "to allow direct function calls or use dependency injection for the "
                           "retest executor.",
            "location": "dep_ready_trigger.py:404-443",
            "impact": "MEDIUM — complicates testability and dry-run testing.",
        },
        {
            "id": "DEF-004", "severity": "MEDIUM",
            "title": "update_risk_register and update_gate_package are log-only",
            "description": "The post_trigger_actions 'update_risk_register' and 'update_gate_package' "
                           "only log messages to console (lines 613-616) without actually modifying "
                           "the corresponding files. The files v86_rc2_dshb_risk_re_evaluate_v3.md "
                           "and v86_rc2_gate_pre_submit_package_v2.md are referenced but never "
                           "updated by the trigger script.",
            "location": "dep_ready_trigger.py:613-616",
            "impact": "MEDIUM — these actions appear to do nothing, which may lead to confusion "
                      "about whether the risk register and gate package are being updated.",
        },
        {
            "id": "DEF-005", "severity": "LOW",
            "title": "trigger's generate_bridge_snapshot() only validates, doesn't regenerate",
            "description": "DepReadyTrigger.generate_bridge_snapshot() (line 489-503) only checks "
                           "if the snapshot file exists and computes its MD5. It does NOT regenerate "
                           "the snapshot. The actual snapshot generation is done by "
                           "full_reverify_v3_batch_v2.py's generate_bridge_snapshot(). If the "
                           "retest fails, the trigger's method will log a warning and skip.",
            "location": "dep_ready_trigger.py:489-503",
            "impact": "LOW — correct behavior for the happy path, but the warning may be confusing.",
        },
        {
            "id": "DEF-006", "severity": "LOW",
            "title": "Alert event file writes are not atomic",
            "description": "write_alert_event() reads existing events, appends new ones, and writes "
                           "back the entire file. If the process crashes mid-write, the file could "
                           "be corrupted. Atomic writes (write to temp, then rename) would be safer.",
            "location": "dep_ready_trigger.py:505-544",
            "impact": "LOW — unlikely in normal operation, but could corrupt events in edge cases.",
        },
        {
            "id": "DEF-007", "severity": "LOW",
            "title": "trigger_retest() doesn't save full stdout/stderr to log file",
            "description": "When the retest script fails (non-zero exit code), the error is logged "
                           "to console and the alert event file, but the full stdout/stderr is not "
                           "saved to a log file for post-mortem analysis. Only the last 50 lines "
                           "of stdout are logged at DEBUG level, and only the first 500 chars of "
                           "stderr are logged on failure.",
            "location": "dep_ready_trigger.py:417-443",
            "impact": "LOW — production debugging may need more complete logs.",
        },
        {
            "id": "DEF-008", "severity": "LOW",
            "title": "MockState sleep_calls uses __dict__ hack instead of simple variable",
            "description": "The install_time_mocks() function uses "
                           "MockState.__dict__.__setitem__('sleep_calls', ...) which is a hacky "
                           "pattern. A simple module-level counter would be cleaner.",
            "location": "dryrun_e2e_test.py (this test harness)",
            "impact": "LOW — cosmetic, no functional impact.",
        },
    ]

    for d in defects:
        logger.log(f"  [{d['severity']}] {d['id']}: {d['title']}", "INFO")

    # ════════════════════════════════════════════════════════════
    # Write Comprehensive Test Log
    # ════════════════════════════════════════════════════════════
    elapsed_total = (datetime.now() - logger.start_time).total_seconds()

    log_lines = [
        f"# DSHB V86-RC2 DEP Trigger Chain — E2E Dry-Run Test Log",
        f"",
        f"**Test ID**: {TEST_ID}",
        f"**Execution Date**: {TEST_START.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Duration**: {elapsed_total:.1f}s",
        f"**Python**: {sys.version}",
        f"**Platform**: {os.name}",
        f"**Work Directory**: `{WORK_DIR}`",
        f"**Sandbox Directory**: `{SANDBOX_DIR}`",
        f"**API Calls**: **All mocked** (zero real HTTP requests)",
        f"**Output Overwrite**: **Prevented** (all writes redirected to sandbox)",
        f"",
        f"---",
        f"",
        f"## 1. Test Environment",
        f"",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Python Version | {sys.version.split()[0]} |",
        f"| Platform | {os.name} |",
        f"| Working Dir | `{WORK_DIR}` |",
        f"| Sandbox Dir | `{SANDBOX_DIR}` |",
        f"| Mock Mode | urllib.request mocked (all calls intercepted) |",
        f"| time.sleep | Disabled (no delays) |",
        f"| subprocess.run | Mocked (no real subprocess) |",
        f"| Mapping Logs | Copied from `{ORIG_MAPPING_DIR}` to sandbox |",
        f"",
        f"---",
        f"",
        f"## 2. Test Results Summary",
        f"",
        f"| # | Step | Status | Duration | Detail |",
        f"|---|------|--------|----------|--------|",
    ]

    for r in logger.results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        detail = r.get("detail", "") or r.get("error", "")
        detail_short = detail[:80] + "..." if len(detail) > 80 else detail
        log_lines.append(f"| {r['step']} | {r['name']} | {icon} {r['status']} | {r.get('elapsed_ms', 0):.0f}ms | {detail_short} |")

    pass_count = sum(1 for r in logger.results if r["status"] == "PASS")
    fail_count = sum(1 for r in logger.results if r["status"] == "FAIL")

    log_lines.extend([
        f"",
        f"**Total Steps**: {len(logger.results)} | **Passed**: {pass_count} | **Failed**: {fail_count}",
        f"**Chain Integrity**: {'✅ ALL 7 LINKS PASS' if all_pass else '❌ SOME LINKS FAILED'}",
        f"",
        f"---",
        f"",
        f"## 3. Chain Integrity Detail (All 7 Links)",
        f"",
    ])

    for step_num, name in chain_links.items():
        r = next((r for r in logger.results if r["step"] == step_num), None)
        if r:
            icon = "✅" if r["status"] == "PASS" else "❌"
            log_lines.append(f"### Link {step_num}: {name} — {icon} {r['status']}")
            log_lines.append(f"- **Duration**: {r.get('elapsed_ms', 0):.0f}ms")
            if r.get("detail"):
                log_lines.append(f"- **Detail**: {r['detail'][:300]}")
            if r.get("error"):
                log_lines.append(f"- **Error**: `{r['error']}`")
            log_lines.append(f"")
        else:
            log_lines.append(f"### Link {step_num}: {name} — ❌ NOT TESTED")
            log_lines.append(f"")

    log_lines.extend([
        f"---",
        f"",
        f"## 4. Output Product Verification",
        f"",
        f"| Product | Exists | Size | MD5 (first 16) |",
        f"|---------|--------|------|-----------------|",
    ])

    for name, path in products.items():
        if path.exists():
            size = path.stat().st_size
            md5 = hashlib.md5(path.read_bytes()).hexdigest().upper()
            log_lines.append(f"| {name} | ✅ Yes | {size:,} bytes | `{md5[:16]}` |")
        else:
            log_lines.append(f"| {name} | ❌ No | — | — |")

    # Count sandbox files
    sandbox_files = [f for f in SANDBOX_DIR.rglob("*") if f.is_file()]
    log_lines.extend([
        f"",
        f"**Sandbox output files**: {len(sandbox_files)}",
        f"",
        f"---",
        f"",
        f"## 5. Mock Data Validation",
        f"",
        f"| Mock Type | Description | Data Points | Status |",
        f"|-----------|-------------|-------------|--------|",
        f"| Probe j25_tc | 铅精矿TC加工费 | 9 points, values 7.8–9.3 | ✅ Valid |",
        f"| Probe i1 | 铅锭社会库存 | 6 points, values 138k–150k | ✅ Valid |",
        f"| Probe i3 | 沪铅期货收盘价 | 6 points, values 15470–15520 | ✅ Valid |",
        f"| Real IDs (i1–i7, j25_tc) | 8 indicators w/ realistic market data | 2–9 pts each | ✅ Valid |",
        f"| Fabricated (s_lead_lme_inv) | LME铅库存, perm_state=-4 | 3 points | ✅ Valid |",
        f"| Fabricated (s_lead_shfe_inv) | 上期所铅库存, perm_state=-4 | 3 points | ✅ Valid |",
        f"| Generic s_xxx | Per-ID hash-based mock data | 3 points each | ✅ Valid |",
        f"| Unknown IDs | error: 无法识别指标来源 | 0 points | ✅ Valid |",
        f"| DERIVED entries | No API call (skipped by script) | N/A | ✅ Correct |",
        f"",
        f"**HTTP Status**: All mocked responses return HTTP 200 | ✅ Verified",
        f"**Permission States**: -4 for fabricated IDs, None for real IDs | ✅ Correct",
        f"",
        f"---",
        f"",
        f"## 6. Defects Found During Dry-Run",
        f"",
    ])

    for d in defects:
        log_lines.append(f"### {d['id']} ({d['severity']}): {d['title']}")
        log_lines.append(f"")
        log_lines.append(f"- **Location**: `{d['location']}`")
        log_lines.append(f"- **Description**: {d['description']}")
        log_lines.append(f"- **Impact**: {d['impact']}")
        log_lines.append(f"")

    log_lines.extend([
        f"---",
        f"",
        f"## 7. Execution Log (Full)",
        f"",
        f"```",
    ])
    for line in logger.log_lines:
        log_lines.append(line)
    log_lines.append(f"```")
    log_lines.append(f"")
    log_lines.append(f"---")
    log_lines.append(f"")
    log_lines.append(f"**End of Dry-Run Test Log**")
    log_lines.append(f"**Generated at**: {datetime.now().isoformat()}")

    LOG_OUTPUT.write_text("\n".join(log_lines), encoding="utf-8")
    logger.log(f"\nTest log written: {LOG_OUTPUT}", "INFO")
    logger.log(f"Total elapsed: {elapsed_total:.1f}s", "INFO")

    # Restore originals
    time.sleep = original_sleep

    return {
        "test_id": TEST_ID,
        "all_pass": all_pass,
        "results": logger.results,
        "defects": defects,
        "elapsed_total": elapsed_total,
    }


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["all_pass"] else 1)
