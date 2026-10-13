#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V88 Framework Tree Metadata Injection Test
===========================================
TASK_ID: V87_RC1_G1_DSHE_FOLLOWUP
AGENT: DSHE
BRANCH: feature/v87-rc1-g1
PURPOSE: Verify framework_tree_meta_chart.yaml can be loaded and validated
         against tree_config.json with all 6 validation rules enforced.
"""

import json
import time
import sys
import os
from collections import defaultdict

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
YAML_PATH = os.path.join(REPO_ROOT, 'analysis', 'e2e_output', 'v88', 'backlog',
                         'framework_tree_meta_chart.yaml')
TREE_CONFIG_PATH = os.path.join(REPO_ROOT, 'data', 'tree_config.json')
RESULT_DIR = os.path.dirname(__file__)

# ---------------------------------------------------------------------------
# Try to import YAML; fall back to text-mode if unavailable
# ---------------------------------------------------------------------------
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ---------------------------------------------------------------------------
# Result accumulators
# ---------------------------------------------------------------------------
test_results = []
load_times = {}
errors = []
warnings = []
info_msgs = []


def log_result(rule_id, chart_id, status, message):
    """Record a single test result."""
    test_results.append({
        'rule': rule_id,
        'chart': chart_id,
        'status': status,
        'message': message
    })
    if status == 'ERROR':
        errors.append(f"[{rule_id}] {chart_id}: {message}")
    elif status == 'WARN':
        warnings.append(f"[{rule_id}] {chart_id}: {message}")


# ---------------------------------------------------------------------------
# Phase 1: Load tree_config.json
# ---------------------------------------------------------------------------
def load_tree_config():
    """Load and index tree_config.json for validation reference."""
    t0 = time.time()
    with open(TREE_CONFIG_PATH, 'r', encoding='utf-8') as f:
        tc = json.load(f)
    load_times['tree_config_load'] = time.time() - t0

    # Build node index: id -> {name, q, comms, category}
    node_index = {}
    for cat in tc.get('categories', []):
        for child in cat.get('children', []):
            node_id = child['id']
            node_index[node_id] = {
                'name': child['name'],
                'q': child['q'],
                'comms': set(child.get('comms', [])),
                'category': cat['id'],
                'code': child.get('code', '')
            }

    # Build commodity index
    commodity_index = {}
    for comm in tc.get('commodities', []):
        commodity_index[comm['id']] = comm

    load_times['tree_config_index_build'] = time.time() - t0

    print(f"  [tree_config] Loaded {len(node_index)} nodes, {len(commodity_index)} commodities")
    return node_index, commodity_index


# ---------------------------------------------------------------------------
# Phase 2: Load YAML metadata
# ---------------------------------------------------------------------------
def load_yaml_metadata():
    """Parse framework_tree_meta_chart.yaml into structured data."""
    t0 = time.time()

    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        raw = f.read()

    load_times['yaml_read'] = time.time() - t0
    print(f"  [yaml_read] Raw file: {len(raw)} bytes, {len(raw.splitlines())} lines")

    if HAS_YAML:
        t0 = time.time()
        data = yaml.safe_load(raw)
        load_times['yaml_parse'] = time.time() - t0
        print(f"  [yaml_parse] Parsed via PyYAML v{yaml.__version__}")
    else:
        # Fallback: minimal regex parser for the charts section
        print("  [yaml_parse] PyYAML not available, using minimal parser")
        data = parse_yaml_minimal(raw)

    charts = data.get('charts', [])
    load_times['yaml_chart_extract'] = time.time() - t0
    print(f"  [yaml_charts] Extracted {len(charts)} chart definitions")

    return data, charts


def parse_yaml_minimal(raw):
    """
    Minimal fallback parser for charts:
    Extracts chart_id, tree_node_id, commodity, chart_type, title, indicators,
    data_status, business_description from the charts: section.
    """
    result = {'charts': []}
    lines = raw.splitlines()
    in_charts = False
    current_chart = None
    current_indicators = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Detect charts: section start
        if line.strip() == 'charts:':
            in_charts = True
            i += 1
            continue

        if not in_charts:
            i += 1
            continue

        # End of charts section (top-level key)
        if line and not line.startswith(' ') and not line.startswith('#') and line.strip() != '':
            if current_chart:
                current_chart['indicators'] = current_indicators
                result['charts'].append(current_chart)
                current_chart = None
                current_indicators = []
            i += 1
            continue

        # New chart start
        if line.strip().startswith('- chart_id:'):
            if current_chart:
                current_chart['indicators'] = current_indicators
                result['charts'].append(current_chart)
            current_chart = {}
            current_indicators = []
            val = line.split(':', 1)[1].strip().strip('"')
            current_chart['chart_id'] = val
            i += 1
            continue

        # Key-value within chart
        if current_chart and ':' in line and not line.strip().startswith('-'):
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip().strip('"')
            # Skip indicators list marker
            if key == 'indicators':
                i += 1
                continue
            if key == 'business_description':
                current_chart['business_description'] = val
            elif key == 'data_status':
                current_chart['data_status'] = val
            elif key == 'chart_type':
                current_chart['chart_type'] = val
            elif key == 'tree_node_id':
                current_chart['tree_node_id'] = val
            elif key == 'commodity':
                current_chart['commodity'] = val
            elif key == 'title':
                current_chart['title'] = val
            elif key == 'pending_reason':
                current_chart['pending_reason'] = val
            elif key == 'weekly_render':
                current_chart['weekly_render'] = val.lower() == 'true'
            i += 1
            continue

        # Indicator within chart
        if current_chart and line.strip().startswith('- indicator_name:'):
            ind = {}
            val = line.split(':', 1)[1].strip().strip('"')
            ind['indicator_name'] = val
            current_indicators.append(ind)
            i += 1
            continue
        if current_chart and current_indicators and line.strip().startswith('  indicator_id:'):
            val = line.split(':', 1)[1].strip().strip('"')
            current_indicators[-1]['indicator_id'] = val
            i += 1
            continue

        i += 1

    # Last chart
    if current_chart:
        current_chart['indicators'] = current_indicators
        result['charts'].append(current_chart)

    return result


# ---------------------------------------------------------------------------
# Phase 3: Validation rules
# ---------------------------------------------------------------------------
def run_validations(charts, node_index, commodity_index):
    """Execute all 6 validation rules against loaded charts."""

    valid_chart_types = {"time_series", "gauge", "distribution", "stacked_bar",
                         "heatmap", "radar", "sankey", "treemap"}
    valid_statuses = {"matchable", "pending_data", "deprecated"}

    t0 = time.time()
    rule_pass_counts = defaultdict(int)
    rule_fail_counts = defaultdict(int)

    # Track topic_tag removal
    topic_tag_found = []

    for chart in charts:
        cid = chart.get('chart_id', 'UNKNOWN')

        # === Rule 1: no_cross_node_binding ===
        node_id = chart.get('tree_node_id', '')
        if node_id in node_index:
            node = node_index[node_id]
            chart_commodity = chart.get('commodity', '')
            if chart_commodity not in node['comms']:
                log_result('no_cross_node_binding', cid, 'ERROR',
                           f"Commodity '{chart_commodity}' not in node '{node_id}' comms scope")
                rule_fail_counts['no_cross_node_binding'] += 1
            else:
                rule_pass_counts['no_cross_node_binding'] += 1
        else:
            log_result('no_cross_node_binding', cid, 'ERROR',
                       f"Unknown node '{node_id}', cannot verify comms scope")
            rule_fail_counts['no_cross_node_binding'] += 1

        # === Rule 2: tree_node_id_valid ===
        if node_id and node_id in node_index:
            rule_pass_counts['tree_node_id_valid'] += 1
        elif node_id:
            log_result('tree_node_id_valid', cid, 'ERROR',
                       f"Invalid tree_node_id: '{node_id}' not in tree_config")
            rule_fail_counts['tree_node_id_valid'] += 1
        else:
            log_result('tree_node_id_valid', cid, 'ERROR',
                       "Missing tree_node_id")
            rule_fail_counts['tree_node_id_valid'] += 1

        # === Rule 3: commodity_valid ===
        comm = chart.get('commodity', '')
        if comm and comm in commodity_index:
            rule_pass_counts['commodity_valid'] += 1
        elif comm:
            log_result('commodity_valid', cid, 'ERROR',
                       f"Invalid commodity: '{comm}' not in tree_config")
            rule_fail_counts['commodity_valid'] += 1
        else:
            log_result('commodity_valid', cid, 'ERROR',
                       "Missing commodity")
            rule_fail_counts['commodity_valid'] += 1

        # === Rule 4: auto_inherit_description ===
        if node_id and node_id in node_index:
            node = node_index[node_id]
            expected = f"{node['name']}({node['q']})"
            actual = chart.get('business_description', '')
            if actual != expected:
                log_result('auto_inherit_description', cid, 'WARN',
                           f"Description mismatch: expected '{expected}', got '{actual}'")
                rule_fail_counts['auto_inherit_description'] += 1
            else:
                rule_pass_counts['auto_inherit_description'] += 1

        # === Rule 5: chart_type_valid ===
        ct = chart.get('chart_type', '')
        if ct in valid_chart_types:
            rule_pass_counts['chart_type_valid'] += 1
        else:
            log_result('chart_type_valid', cid, 'ERROR',
                       f"Invalid chart_type: '{ct}'")
            rule_fail_counts['chart_type_valid'] += 1

        # === Rule 6: data_status_valid ===
        ds = chart.get('data_status', '')
        if ds in valid_statuses:
            rule_pass_counts['data_status_valid'] += 1
        else:
            log_result('data_status_valid', cid, 'ERROR',
                       f"Invalid data_status: '{ds}'")
            rule_fail_counts['data_status_valid'] += 1

        # === Topic tag removal check ===
        if 'topic_tag' in chart:
            topic_tag_found.append(cid)

    load_times['validation_total'] = time.time() - t0

    return rule_pass_counts, rule_fail_counts, topic_tag_found


def run_negative_tests(charts, node_index, commodity_index):
    """Run negative test cases (illegal cross-node bindings)."""
    print("\n  === Negative Tests (illegal binding interception) ===")
    neg_results = []

    # Test 1: si_p6_bar_01 is already known invalid (si not in p6 comms)
    t1_chart = next((c for c in charts if c.get('chart_id') == 'si_p6_bar_01'), None)
    if t1_chart:
        t1 = dict(t1_chart)
        node_id = t1['tree_node_id']
        node = node_index.get(node_id, {})
        comms = node.get('comms', set())
        blocked = t1['commodity'] not in comms
        neg_results.append({'test': 'TC-01 si_p6 (known invalid: si not in p6 comms)', 'blocked': blocked})
        print(f"  TC-01: si_p6 (si not in p6 comms) = {'BLOCKED' if blocked else 'NOT BLOCKED!'}")
    else:
        neg_results.append({'test': 'TC-01 si_p6_bar_01 not found', 'blocked': False})
        print(f"  TC-01: si_p6_bar_01 chart not found")

    # Test 2: Bind li to p6 (li IS in p6 comms, so this should PASS)
    t2_chart = next((c for c in charts if c.get('commodity') == 'li' and c.get('tree_node_id') == 'p6'), None)
    if t2_chart:
        t2 = dict(t2_chart)
        node_id2 = t2['tree_node_id']
        node2 = node_index.get(node_id2, {})
        comms2 = node2.get('comms', set())
        passed2 = t2['commodity'] in comms2
        neg_results.append({'test': 'TC-02 li_p6 (li in p6 comms, should PASS)', 'passed': passed2})
        print(f"  TC-02: li_p6 (li in p6 comms) = {'PASS' if passed2 else 'FAIL!'}")
    else:
        neg_results.append({'test': 'TC-02 li_p6 not found', 'passed': False})
        print(f"  TC-02: li_p6 chart not found")

    # Test 3: Force-combine si with p6 (known invalid)
    t3 = dict(charts[0])
    t3['chart_id'] = 'NEG-TEST-03'
    t3['tree_node_id'] = 'p6'
    t3['commodity'] = 'si'
    node3 = node_index.get('p6', {})
    comms3 = node3.get('comms', set())
    blocked3 = t3['commodity'] not in comms3
    neg_results.append({'test': 'TC-03 cross: si commodity on p6 node', 'blocked': blocked3})
    print(f"  TC-03: cross si->p6 = {'BLOCKED' if blocked3 else 'NOT BLOCKED!'}")

    # Test 3: Invalid node ID
    t3 = dict(charts[0])
    t3['chart_id'] = 'NEG-TEST-03'
    t3['tree_node_id'] = 'ZZ_INVALID'
    blocked3 = t3['tree_node_id'] not in node_index
    neg_results.append({'test': 'TC-03 invalid node ID', 'blocked': blocked3})
    print(f"  TC-03: invalid node ID = {'BLOCKED' if blocked3 else 'NOT BLOCKED!'}")

    # Test 4: Invalid commodity
    t4 = dict(charts[0])
    t4['chart_id'] = 'NEG-TEST-04'
    t4['commodity'] = 'XX_INVALID'
    blocked4 = t4['commodity'] not in commodity_index
    neg_results.append({'test': 'TC-04 invalid commodity', 'blocked': blocked4})
    print(f"  TC-04: invalid commodity = {'BLOCKED' if blocked4 else 'NOT BLOCKED!'}")

    # Test 5: Valid binding (should PASS)
    t5 = dict(charts[0])  # Original cu chart - should be valid
    node_id5 = t5.get('tree_node_id', '')
    node5 = node_index.get(node_id5, {})
    comms5 = node5.get('comms', set())
    passed5 = t5.get('commodity', '') in comms5
    neg_results.append({'test': 'TC-05 valid cu binding', 'passed': passed5})
    print(f"  TC-05: valid cu binding = {'PASS' if passed5 else 'FAIL!'}")

    # Test 6: topic_tag field should not exist
    topic_tag_present = any('topic_tag' in c for c in charts)
    blocked6 = not topic_tag_present
    neg_results.append({'test': 'TC-06 topic_tag removed', 'removed': blocked6})
    print(f"  TC-06: topic_tag removed = {'REMOVED' if blocked6 else 'STILL PRESENT!'}")

    print(f"\n  Negative test results: {sum(1 for r in neg_results if (r.get('blocked') or r.get('passed') or r.get('removed')) )}/{len(neg_results)} passed")
    return neg_results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("V88 Framework Tree Metadata Injection Test")
    print(f"TASk_ID: V87_RC1_G1_DSHE_FOLLOWUP")
    print(f"YAML: {os.path.basename(YAML_PATH)}")
    print(f"Tree Config: tree_config.json")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC+8')}")
    print("=" * 70)

    # Phase 1: Load tree_config.json
    print("\n[Phase 1] Loading tree_config.json...")
    node_index, commodity_index = load_tree_config()

    # Phase 2: Load YAML metadata
    print("\n[Phase 2] Loading framework_tree_meta_chart.yaml...")
    yaml_data, charts = load_yaml_metadata()

    # Phase 3: Run validation rules
    print("\n[Phase 3] Running 6 validation rules...")
    rule_pass, rule_fail, topic_tag_found = run_validations(charts, node_index, commodity_index)

    # Phase 4: Run negative tests
    print("\n[Phase 4] Running negative test cases...")
    neg_results = run_negative_tests(charts, node_index, commodity_index)

    # Phase 5: Compile summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    # Load timing
    print(f"\n--- Load Timing ---")
    for k, v in load_times.items():
        print(f"  {k}: {v*1000:.2f} ms")

    # Validation summary
    print(f"\n--- Validation Summary ({len(charts)} charts) ---")
    for rule in ['no_cross_node_binding', 'tree_node_id_valid', 'commodity_valid',
                 'auto_inherit_description', 'chart_type_valid', 'data_status_valid']:
        p = rule_pass.get(rule, 0)
        f = rule_fail.get(rule, 0)
        status = "PASS" if f == 0 else f"{f} FAIL/WARN"
        print(f"  {rule:30s} : PASS={p:4d}  {status}")

    total_checks = sum(rule_pass.values()) + sum(rule_fail.values())
    total_pass = sum(rule_pass.values())
    total_fail = sum(rule_fail.values())
    print(f"\n  TOTAL: {total_checks} checks, {total_pass} PASS, {total_fail} FAIL/WARN")

    # Error/Warning details
    if errors:
        print(f"\n--- ERRORS ({len(errors)}) ---")
        for e in errors:
            print(f"  {e}")
    else:
        print(f"\n--- ERRORS: 0 ---")

    if warnings:
        print(f"\n--- WARNINGS ({len(warnings)}) ---")
        for w in warnings:
            print(f"  {w}")
    else:
        print(f"\n--- WARNINGS: 0 ---")

    # Topic tag check
    print(f"\n--- topic_tag Removal ---")
    if topic_tag_found:
        print(f"  FAIL: topic_tag still present in {len(topic_tag_found)} charts: {topic_tag_found}")
    else:
        print(f"  PASS: topic_tag field completely removed from all charts")

    # Data status distribution
    print(f"\n--- Data Status Distribution ---")
    status_dist = defaultdict(int)
    for c in charts:
        status_dist[c.get('data_status', 'unknown')] += 1
    for s, cnt in sorted(status_dist.items()):
        print(f"  {s:15s} : {cnt}")

    # Category distribution
    print(f"\n--- Category Distribution ---")
    cat_dist = defaultdict(int)
    for c in charts:
        nid = c.get('tree_node_id', '')
        if nid in node_index:
            cat_dist[node_index[nid]['category']] += 1
        else:
            cat_dist['unknown'] += 1
    for cat, cnt in sorted(cat_dist.items()):
        print(f"  {cat:15s} : {cnt}")

    # Commodity distribution
    print(f"\n--- Commodity Distribution ---")
    comm_dist = defaultdict(int)
    for c in charts:
        comm_dist[c.get('commodity', 'unknown')] += 1
    for comm, cnt in sorted(comm_dist.items()):
        print(f"  {comm:10s} : {cnt}")

    # Write detailed results to JSON
    output = {
        'test_metadata': {
            'task_id': 'V87_RC1_G1_DSHE_FOLLOWUP',
            'agent': 'DSHE',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC+8'),
            'yaml_file': 'framework_tree_meta_chart.yaml',
            'yaml_size_bytes': os.path.getsize(YAML_PATH),
            'tree_config_file': 'tree_config.json'
        },
        'load_timing_ms': {k: round(v * 1000, 2) for k, v in load_times.items()},
        'total_charts_loaded': len(charts),
        'validation_summary': {
            rule: {
                'pass': rule_pass.get(rule, 0),
                'fail': rule_fail.get(rule, 0)
            } for rule in ['no_cross_node_binding', 'tree_node_id_valid', 'commodity_valid',
                           'auto_inherit_description', 'chart_type_valid', 'data_status_valid']
        },
        'total_checks': total_checks,
        'total_pass': total_pass,
        'total_fail': total_fail,
        'errors': errors,
        'warnings': warnings,
        'topic_tag_present': len(topic_tag_found) > 0,
        'data_status_distribution': dict(status_dist),
        'negative_tests': neg_results,
        'negative_tests_passed': sum(1 for r in neg_results if (r.get('blocked') or r.get('passed') or r.get('removed'))),
        'negative_tests_total': len(neg_results)
    }

    result_path = os.path.join(RESULT_DIR, 'meta_injection_test_results.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Results written to: {result_path}")

    # Final verdict
    print("\n" + "=" * 70)
    all_errors = len(errors)
    all_neg_passed = output['negative_tests_passed'] == output['negative_tests_total']
    topic_removed = not output['topic_tag_present']

    if all_errors == 0 and all_neg_passed and topic_removed:
        print("FINAL VERDICT: [PASS] METADATA INJECTION TEST PASSED")
        print("=" * 70)
        return 0
    else:
        print(f"FINAL VERDICT: [FAIL] METADATA INJECTION TEST FAILED")
        print(f"  Errors: {all_errors}")
        print(f"  Negative tests: {output['negative_tests_passed']}/{output['negative_tests_total']} passed")
        print(f"  topic_tag removed: {topic_removed}")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
