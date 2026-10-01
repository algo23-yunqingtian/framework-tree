#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Dataset Replay Runner: V85 Snapshot -> V86 P0+P1 Rule Engine
====================================================================
Task: DSHB_V86_RULE_ENGINE_FULL_DATASET_REPLAY_AND_PROD_BUNDLE_BUILD
Branch: feature/v85-chart-template
Base: commit 68517fb (V86 rule full regression + CI pipeline + error code spec)

Pipeline:
  1. Load V85 chart_risk_bound_all.json (488 templates, all series)
  2. For each series: (series_name, zhiji_name) -> V86P1RuleEngine.evaluate()
  3. Compare V86 results with V85 baseline risk levels
  4. Generate full replay report + results JSON

Constraints:
  - NO_ZHIJI_API_CALL=TRUE
  - V85 frozen baselines READ-ONLY
  - Only creates new files, never modifies existing deliverables
  - GBK console safe (no emoji in print)
"""

import json
import os
import sys
import time
import datetime
import traceback
import hashlib
import argparse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CD = os.path.dirname(os.path.abspath(__file__))
REPO = r"D:\DSH_WORK\framework-tree"
V85_DIR = os.path.join(REPO, "analysis", "e2e_output", "v85")
V86_DIR = os.path.join(REPO, "analysis", "e2e_output", "v86")
P0_DIR = os.path.join(V86_DIR, "dshb_rule_predev")
P1_DIR = os.path.join(V86_DIR, "dshb_rule_ci_stress")
ALIAS_DIR = os.path.join(V86_DIR, "dshe_alias_predev")
OUT_DIR = CD

V85_TEMPLATE_FILE = os.path.join(V85_DIR, "v85_final_integrate", "chart_risk_bound_all.json")
V85_BLACKLIST_FILE = os.path.join(V85_DIR, "dshb_full_integrate", "semantic_blacklist_v85_final.json")

TASK_ID = "DSHB_V86_RULE_ENGINE_FULL_DATASET_REPLAY_AND_PROD_BUNDLE_BUILD"
VERSION = "v1.0"
BRANCH = "feature/v85-chart-template"
BASE_COMMIT = "68517fb"

# ---------------------------------------------------------------------------
# Add engine paths
# ---------------------------------------------------------------------------
sys.path.insert(0, P1_DIR)
sys.path.insert(0, P0_DIR)

# ---------------------------------------------------------------------------
# Replay Result Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SeriesReplayResult:
    """Result for a single series replay."""
    template_id: str
    template_source: str  # PDF / THS
    variety: str
    series_index: int
    series_name: str
    zhiji_name: str
    zhiji_id: Optional[str]
    v85_risk_level: str  # CLEAN / P0 / P1 / BLOCKED / INFO
    v85_risk_type: str
    v86_result: str  # BLOCKED / PASSED / NOT_APPLICABLE / DATA_MISSING
    v86_rule_triggered: Optional[str]
    v86_severity: Optional[str]
    v86_error_code: str
    v86_latency_ms: float
    delta: str  # UNCHANGED / IMPROVED / REGRESSED / DATA_MISSING
    notes: str = ""

    def to_dict(self) -> Dict:
        d = asdict(self)
        # Remove None values for cleaner output
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class TemplateReplayResult:
    """Aggregated result for a single template."""
    template_id: str
    template_source: str
    variety: str
    v85_risk_level: str
    series_count: int
    series_results: List[SeriesReplayResult]
    v86_template_risk: str  # CLEAN / P0 / P1 / BLOCKED
    v86_delta: str  # UNCHANGED / IMPROVED / REGRESSED


@dataclass
class ReplaySummary:
    """Overall replay summary metrics."""
    total_templates: int = 0
    total_series: int = 0
    total_pdf: int = 0
    total_ths: int = 0
    # V85 baseline
    v85_p0_templates: int = 0
    v85_p1_templates: int = 0
    v85_clean_templates: int = 0
    v85_blocked_series: int = 0
    v85_info_series: int = 0
    v85_valid_series: int = 0
    # V86 results
    v86_blocked: int = 0
    v86_passed: int = 0
    v86_data_missing: int = 0
    v86_not_applicable: int = 0
    v86_errors: int = 0
    # Comparison
    v86_p0_intercepted: int = 0
    v86_p1_intercepted: int = 0
    v86_tp: int = 0
    v86_fp: int = 0
    v86_regression: int = 0
    v86_improved: int = 0
    v86_unchanged: int = 0
    v86_new_blocked: int = 0
    v86_unblocked: int = 0
    # Rule hit distribution
    rule_hit_count: Dict[str, int] = field(default_factory=dict)
    # Varietly distribution
    variety_distribution: Dict[str, Dict] = field(default_factory=dict)
    # Performance
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    elapsed_ms: float = 0.0
    throughput_series_per_sec: float = 0.0
    # Varietly detail
    v86_blocked_by_variety: Dict[str, int] = field(default_factory=dict)


def classify_delta(v85_risk_level: str, v86_result: str) -> str:
    """
    Classify the delta between V85 baseline and V86 result.
    
    IMPROVED: V85 passed/clean but V86 blocked (new interception)
    REGRESSED: V85 blocked but V86 passed (missed interception)
    UNCHANGED: Both blocked or both passed
    DATA_MISSING: V86 returned DATA_MISSING
    """
    v85_blocked = v85_risk_level in ("BLOCKED", "P0")
    v85_passed = v85_risk_level in ("CLEAN", "INFO")
    v86_blocked = v86_result == "BLOCKED"
    v86_passed = v86_result in ("PASSED", "NOT_APPLICABLE")
    v86_data_missing = v86_result == "DATA_MISSING"
    
    if v86_data_missing:
        return "DATA_MISSING"
    
    if v85_passed and v86_blocked:
        return "IMPROVED"  # New interception (could be TP or FP)
    
    if v85_blocked and v86_passed:
        return "REGRESSED"  # Missed interception
    
    if v85_blocked and v86_blocked:
        return "UNCHANGED"
    
    if v85_passed and v86_passed:
        return "UNCHANGED"
    
    return "UNKNOWN"


def load_v85_templates() -> Dict:
    """Load V85 chart_risk_bound_all.json."""
    with open(V85_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_v85_baseline_stats(template_data: Dict) -> Dict:
    """Extract V85 baseline statistics from template data."""
    stats = template_data.get("statistics", {})
    variety_dist = template_data.get("variety_distribution", {})
    return {
        "pdf_total": stats.get("pdf_total", 0),
        "pdf_with_risk": stats.get("pdf_with_risk", 0),
        "pdf_p0": stats.get("pdf_p0", 0),
        "pdf_p1": stats.get("pdf_p1", 0),
        "pdf_clean": stats.get("pdf_clean", 0),
        "ths_total": stats.get("ths_total", 0),
        "ths_with_risk": stats.get("ths_with_risk", 0),
        "total_templates": stats.get("total_templates", 0),
        "total_with_risk": stats.get("total_with_risk", 0),
        "total_p0": stats.get("total_p0", 0),
        "total_p1": stats.get("total_p1", 0),
        "variety_distribution": variety_dist,
    }


def extract_series_pairs(template_data: Dict) -> List[Dict]:
    """
    Extract all (series_name, zhiji_name) pairs from templates.
    Returns list of dicts with template info + series info.
    """
    pairs = []
    for tpl in template_data.get("templates", []):
        for sr in tpl.get("series_risks", []):
            series_name = sr.get("series_name", "")
            zhiji_name = sr.get("zhiji_name", "")
            
            # Skip empty series names
            if not series_name:
                continue
            
            pairs.append({
                "template_id": tpl.get("template_id", ""),
                "template_source": tpl.get("source", ""),
                "variety": tpl.get("variety", ""),
                "series_index": sr.get("series_index", 0),
                "series_name": series_name,
                "zhiji_name": zhiji_name,
                "zhiji_id": sr.get("zhiji_id"),
                "v85_risk_level": sr.get("risk_level", "CLEAN"),
                "v85_risk_type": sr.get("risk_type", "no_risk"),
                "v85_verify_status": sr.get("verify_status", ""),
                "v85_series_status": sr.get("series_status", ""),
                "v85_reason": sr.get("reason", ""),
            })
    return pairs


def load_v86_engine() -> 'V86P1RuleEngine':
    """Load and initialize V86 P1 rule engine with P0+P1 rules."""
    from v86_p1_rule_prototype import V86P1RuleEngine, create_v86_p1_rules
    from v86_p0_rule_prototype import create_v86_p0_rules
    
    engine = V86P1RuleEngine()
    
    # Load P0 rules (6 rules: BL-009a, BL-026, BL-012, BL-001-004, BL-018, BL-020-022)
    p0_rules = create_v86_p0_rules()
    engine._add_rules(p0_rules)
    
    # Load P1 rules (12 rules: BL-027~BL-038)
    p1_rules = create_v86_p1_rules()
    engine._add_rules(p1_rules)
    
    return engine


def run_replay(engine, series_pairs: List[Dict], template_data: Dict = None, use_alias: bool = False) -> Dict:
    """
    Run full dataset replay through V86 rule engine.
    
    Returns:
        Dict with summary, per-series results, and analysis.
    """
    t0 = time.time()
    
    summary = ReplaySummary()
    results = []
    latencies = []
    
    summary.total_templates = len(template_data.get("templates", [])) if template_data else 0
    summary.total_series = len(series_pairs)
    
    for i, pair in enumerate(series_pairs):
        indicator_name = pair["series_name"]
        matched_name = pair["zhiji_name"]
        
        # Evaluate through V86 rule engine
        try:
            result = engine.evaluate(indicator_name, matched_name)
            latency = result.get("latency_ms", 0.0)
            latencies.append(latency)
            
            v86_result = result.get("result", "ERROR")
            v86_rule = result.get("blocked_by")
            v86_severity = result.get("severity")
            v86_error = result.get("error_code", "OK")
        except Exception as e:
            v86_result = "ERROR"
            v86_rule = None
            v86_severity = None
            v86_error = "EXCEPTION"
            latency = 0.0
            latencies.append(0.0)
        
        # Classify delta
        delta = classify_delta(pair["v85_risk_level"], v86_result)
        
        # Build result
        sr = SeriesReplayResult(
            template_id=pair["template_id"],
            template_source=pair["template_source"],
            variety=pair["variety"],
            series_index=pair["series_index"],
            series_name=pair["series_name"],
            zhiji_name=pair["zhiji_name"],
            zhiji_id=pair["zhiji_id"],
            v85_risk_level=pair["v85_risk_level"],
            v85_risk_type=pair["v85_risk_type"],
            v86_result=v86_result,
            v86_rule_triggered=v86_rule,
            v86_severity=v86_severity,
            v86_error_code=v86_error,
            v86_latency_ms=latency,
            delta=delta,
        )
        results.append(sr)
        
        # Update summary counters
        summary.total_series += 1
        if pair["template_source"] == "PDF":
            summary.total_pdf += 1
        else:
            summary.total_ths += 1
        
        # V86 result counts
        if v86_result == "BLOCKED":
            summary.v86_blocked += 1
            if v86_rule:
                summary.rule_hit_count[v86_rule] = summary.rule_hit_count.get(v86_rule, 0) + 1
            # Track by variety
            variety = pair["variety"]
            summary.v86_blocked_by_variety[variety] = summary.v86_blocked_by_variety.get(variety, 0) + 1
        elif v86_result == "PASSED":
            summary.v86_passed += 1
        elif v86_result == "DATA_MISSING":
            summary.v86_data_missing += 1
        elif v86_result == "NOT_APPLICABLE":
            summary.v86_not_applicable += 1
        else:
            summary.v86_errors += 1
        
        # Delta classification
        if delta == "IMPROVED":
            summary.v86_improved += 1
            summary.v86_new_blocked += 1
        elif delta == "REGRESSED":
            summary.v86_regression += 1
            summary.v86_unblocked += 1
        elif delta == "UNCHANGED":
            summary.v86_unchanged += 1
        
        # TP/FP classification for improved cases
        if delta == "IMPROVED":
            # Check if V85 had a reason that indicates it should have been blocked
            v85_reason = pair.get("v85_reason", "")
            if "blacklist" in v85_reason.lower() or "risk" in v85_reason.lower() or "P0" in v85_reason or "P1" in v85_reason:
                summary.v86_tp += 1
            else:
                summary.v86_fp += 1
        elif delta == "REGRESSED":
            summary.v86_regression += 1
        
        # V85 baseline tracking
        v85_level = pair["v85_risk_level"]
        if v85_level == "BLOCKED":
            summary.v85_blocked_series += 1
        elif v85_level == "INFO":
            summary.v85_info_series += 1
        elif v85_level in ("VALID", "CLEAN"):
            summary.v85_valid_series += 1
    
    # Calculate performance metrics
    elapsed_ms = (time.time() - t0) * 1000
    summary.elapsed_ms = round(elapsed_ms, 1)
    summary.total_latency_ms = round(sum(latencies), 1)
    summary.avg_latency_ms = round(sum(latencies) / max(1, len(latencies)), 3)
    
    if latencies:
        sorted_lat = sorted(latencies)
        summary.p50_latency_ms = round(sorted_lat[len(sorted_lat) // 2], 3)
        summary.p95_latency_ms = round(sorted_lat[int(len(sorted_lat) * 0.95)], 3)
        summary.p99_latency_ms = round(sorted_lat[int(len(sorted_lat) * 0.99)], 3)
        summary.max_latency_ms = round(max(latencies), 3)
        summary.throughput_series_per_sec = round(len(latencies) / max(0.001, elapsed_ms / 1000), 1)
    
    # Calculate P0/P1 interception
    # Count series that V85 marked as P0/P1/BLOCKED
    p0_cases = [p for p in series_pairs if p["v85_risk_level"] in ("BLOCKED", "P0")]
    p1_cases = [p for p in series_pairs if p["v85_risk_level"] == "P1"]
    
    # Series that V86 also blocked
    v86_blocked_set = set()
    for r in results:
        if r.v86_result == "BLOCKED":
            v86_blocked_set.add((r.template_id, r.series_index))
    
    for p in p0_cases:
        key = (p["template_id"], p["series_index"])
        if key in v86_blocked_set:
            summary.v86_p0_intercepted += 1
    for p in p1_cases:
        key = (p["template_id"], p["series_index"])
        if key in v86_blocked_set:
            summary.v86_p1_intercepted += 1
    
    # Template-level aggregation
    template_results = aggregate_template_results(template_data, results)
    
    # Identify key differences
    improved_cases = [r for r in results if r.delta == "IMPROVED"]
    regressed_cases = [r for r in results if r.delta == "REGRESSED"]
    data_missing_cases = [r for r in results if r.delta == "DATA_MISSING"]
    
    output = {
        "task_id": TASK_ID,
        "version": VERSION,
        "branch": BRANCH,
        "base_commit": BASE_COMMIT,
        "generated_at": datetime.datetime.now().isoformat(),
        "summary": asdict(summary),
        "improved_cases": [r.to_dict() for r in improved_cases[:50]],
        "regressed_cases": [r.to_dict() for r in regressed_cases[:50]],
        "data_missing_cases": [r.to_dict() for r in data_missing_cases[:50]],
        "template_results": [asdict(t) for t in template_results[:20]],
        "all_results": [r.to_dict() for r in results],
    }
    
    return output


def aggregate_template_results(template_data: Dict, series_results: List[SeriesReplayResult]) -> List[TemplateReplayResult]:
    """Aggregate series results into template-level results."""
    templates = template_data.get("templates", [])
    results_by_template = {}
    
    for sr in series_results:
        key = sr.template_id
        if key not in results_by_template:
            results_by_template[key] = []
        results_by_template[key].append(sr)
    
    template_results = []
    for tpl in templates:
        tid = tpl.get("template_id", "")
        series_res = results_by_template.get(tid, [])
        
        # Determine V86 template risk
        has_block = any(sr.v86_result == "BLOCKED" for sr in series_res)
        has_p0 = any(sr.v86_result == "BLOCKED" and sr.v86_severity == "P0" for sr in series_res)
        has_p1 = any(sr.v86_result == "BLOCKED" and sr.v86_severity == "P1" for sr in series_res)
        
        if has_p0:
            v86_risk = "P0"
        elif has_block:
            v86_risk = "BLOCKED"
        elif has_p1:
            v86_risk = "P1"
        else:
            v86_risk = "CLEAN"
        
        v85_risk = tpl.get("template_risk_level", "CLEAN")
        
        # Template delta
        v85_risk_blocked = v85_risk in ("P0", "BLOCKED")
        v86_risk_blocked = v86_risk in ("P0", "BLOCKED", "P1")
        
        if not v85_risk_blocked and v86_risk_blocked:
            delta = "IMPROVED"
        elif v85_risk_blocked and not v86_risk_blocked:
            delta = "REGRESSED"
        else:
            delta = "UNCHANGED"
        
        template_results.append(TemplateReplayResult(
            template_id=tid,
            template_source=tpl.get("source", ""),
            variety=tpl.get("variety", ""),
            v85_risk_level=v85_risk,
            series_count=tpl.get("series_count", len(series_res)),
            series_results=series_res,
            v86_template_risk=v86_risk,
            v86_delta=delta,
        ))
    
    return template_results


def generate_report_md(replay_data: Dict, baseline_stats: Dict) -> str:
    """Generate the full replay report in Markdown format."""
    summary = replay_data["summary"]
    s = summary
    
    lines = []
    lines.append("# V85 Full Dataset Replay Report")
    lines.append("")
    lines.append("**Task:** %s" % TASK_ID)
    lines.append("**Version:** %s" % VERSION)
    lines.append("**Branch:** %s" % BRANCH)
    lines.append("**Base Commit:** %s" % BASE_COMMIT)
    lines.append("**Generated:** %s" % replay_data["generated_at"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Overview")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Total Templates | %d |" % s["total_templates"])
    lines.append("| Total Series (replayed) | %d |" % s["total_series"])
    lines.append("| PDF Templates | %d |" % s["total_pdf"])
    lines.append("| THS Templates | %d |" % s["total_ths"])
    lines.append("| Replay Duration | %.1f ms |" % s["elapsed_ms"])
    lines.append("| Throughput | %.0f series/sec |" % s["throughput_series_per_sec"])
    lines.append("| Avg Latency | %.3f ms |" % s["avg_latency_ms"])
    lines.append("| P50 Latency | %.3f ms |" % s["p50_latency_ms"])
    lines.append("| P95 Latency | %.3f ms |" % s["p95_latency_ms"])
    lines.append("| P99 Latency | %.3f ms |" % s["p99_latency_ms"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. V85 Baseline Statistics")
    lines.append("")
    lines.append("### 2.1 Template-Level V85 Baseline")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append("| PDF Total | %d |" % baseline_stats.get("pdf_total", 0))
    lines.append("| PDF with Risk | %d |" % baseline_stats.get("pdf_with_risk", 0))
    lines.append("| PDF P0 | %d |" % baseline_stats.get("pdf_p0", 0))
    lines.append("| PDF P1 | %d |" % baseline_stats.get("pdf_p1", 0))
    lines.append("| PDF Clean | %d |" % baseline_stats.get("pdf_clean", 0))
    lines.append("| THS Total | %d |" % baseline_stats.get("ths_total", 0))
    lines.append("| THS with Risk | %d |" % baseline_stats.get("ths_with_risk", 0))
    lines.append("| Total Templates | %d |" % baseline_stats.get("total_templates", 0))
    lines.append("| Total with Risk | %d |" % baseline_stats.get("total_with_risk", 0))
    lines.append("| Total P0 | %d |" % baseline_stats.get("total_p0", 0))
    lines.append("| Total P1 | %d |" % baseline_stats.get("total_p1", 0))
    lines.append("")
    lines.append("### 2.2 Variety Distribution (V85)")
    lines.append("")
    lines.append("| Variety | Total | P0 | P1 | CLEAN |")
    lines.append("|---------|-------|----|----|-------|")
    for var, stats in baseline_stats.get("variety_distribution", {}).items():
        lines.append("| %s | %d | %d | %d | %d |" % (
            var, stats.get("total", 0), stats.get("P0", 0),
            stats.get("P1", 0), stats.get("CLEAN", 0)
        ))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. V86 Replay Results")
    lines.append("")
    lines.append("### 3.1 V86 Rule Engine Results")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append("| BLOCKED | %d |" % s["v86_blocked"])
    lines.append("| PASSED | %d |" % s["v86_passed"])
    lines.append("| DATA_MISSING | %d |" % s["v86_data_missing"])
    lines.append("| NOT_APPLICABLE | %d |" % s["v86_not_applicable"])
    lines.append("| ERRORS | %d |" % s["v86_errors"])
    lines.append("")
    lines.append("### 3.2 V86 vs V85 Delta Analysis")
    lines.append("")
    lines.append("| Metric | Count | Description |")
    lines.append("|--------|-------|-------------|")
    lines.append("| IMPROVED (new blocked) | %d | V86 blocked, V85 passed/clean |" % s["v86_improved"])
    lines.append("| REGRESSED (missed block) | %d | V86 passed, V85 was blocked |" % s["v86_regression"])
    lines.append("| UNCHANGED | %d | Both blocked or both passed |" % s["v86_unchanged"])
    lines.append("| DATA_MISSING | %d | V86 returned DATA_MISSING |" % s["v86_data_missing"])
    lines.append("")
    lines.append("### 3.3 TP/FP Classification")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append("| TP (True Positive - new correct block) | %d |" % s["v86_tp"])
    lines.append("| FP (False Positive - new incorrect block) | %d |" % s["v86_fp"])
    lines.append("")
    lines.append("### 3.4 P0/P1 Interception")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append("| V85 P0 series intercepted by V86 | %d |" % s["v86_p0_intercepted"])
    lines.append("| V85 P1 series intercepted by V86 | %d |" % s["v86_p1_intercepted"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Rule Hit Distribution")
    lines.append("")
    lines.append("| Rule ID | Hit Count | Severity |")
    lines.append("|---------|-----------|----------|")
    rule_hit = s.get("rule_hit_count", {})
    if rule_hit:
        # Sort by count descending
        for rule_id, count in sorted(rule_hit.items(), key=lambda x: -x[1]):
            # Determine severity from rule ID
            if rule_id.startswith("BL-009a") or rule_id in ("BL-001", "BL-002", "BL-003", "BL-004", "BL-005", "BL-006", "BL-008", "BL-009"):
                sev = "P0"
            elif rule_id in ("BL-026", "BL-012"):
                sev = "P0"
            elif rule_id.startswith("BL-027") or rule_id.startswith("BL-028") or rule_id.startswith("BL-029") or rule_id.startswith("BL-030") or rule_id.startswith("BL-031") or rule_id.startswith("BL-032") or rule_id.startswith("BL-033") or rule_id.startswith("BL-034") or rule_id.startswith("BL-035") or rule_id.startswith("BL-036") or rule_id.startswith("BL-037") or rule_id.startswith("BL-038"):
                sev = "P1"
            else:
                sev = "P1"
            lines.append("| %s | %d | %s |" % (rule_id, count, sev))
    else:
        lines.append("| (none) | 0 | - |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Blocked Series by Variety")
    lines.append("")
    lines.append("| Variety | Blocked Count |")
    lines.append("|---------|--------------|")
    for var, count in sorted(s.get("v86_blocked_by_variety", {}).items()):
        lines.append("| %s | %d |" % (var, count))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. Improved Cases (New V86 Blocks)")
    lines.append("")
    improved = replay_data.get("improved_cases", [])
    if improved:
        lines.append("| Template | Series | V85 Risk | V86 Rule | Delta |")
        lines.append("|----------|--------|----------|----------|-------|")
        for c in improved[:30]:
            lines.append("| %s | %s | %s | %s | %s |" % (
                c["template_id"], c["series_name"][:40],
                c["v85_risk_level"], c["v86_rule_triggered"] or "-", c["delta"]
            ))
    else:
        lines.append("No improved cases found.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 7. Regressed Cases (V86 Missed)")
    lines.append("")
    regressed = replay_data.get("regressed_cases", [])
    if regressed:
        lines.append("| Template | Series | V85 Risk | V86 Result | Delta |")
        lines.append("|----------|--------|----------|------------|-------|")
        for c in regressed[:30]:
            lines.append("| %s | %s | %s | %s | %s |" % (
                c["template_id"], c["series_name"][:40],
                c["v85_risk_level"], c["v86_result"], c["delta"]
            ))
    else:
        lines.append("No regressed cases found.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 8. DATA_MISSING Cases")
    lines.append("")
    dm_cases = replay_data.get("data_missing_cases", [])
    if dm_cases:
        lines.append("| Template | Series | V85 Risk | V86 Result |")
        lines.append("|----------|--------|----------|------------|")
        for c in dm_cases[:30]:
            lines.append("| %s | %s | %s | %s |" % (
                c["template_id"], c["series_name"][:40],
                c["v85_risk_level"], c["v86_result"]
            ))
    else:
        lines.append("No DATA_MISSING cases.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 9. Template-Level Comparison")
    lines.append("")
    template_results = replay_data.get("template_results", [])
    if template_results:
        improved_t = [t for t in template_results if t["v86_delta"] == "IMPROVED"]
        regressed_t = [t for t in template_results if t["v86_delta"] == "REGRESSED"]
        unchanged_t = [t for t in template_results if t["v86_delta"] == "UNCHANGED"]
        
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append("| Templates IMPROVED (new V86 block) | %d |" % len(improved_t))
        lines.append("| Templates REGRESSED (V86 miss) | %d |" % len(regressed_t))
        lines.append("| Templates UNCHANGED | %d |" % len(unchanged_t))
        lines.append("")
    else:
        lines.append("No template-level data.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 10. Conclusion")
    lines.append("")
    
    total_series = s["total_series"]
    improved_pct = (s["v86_improved"] / max(1, total_series) * 100) if total_series else 0
    regression_pct = (s["v86_regression"] / max(1, total_series) * 100) if total_series else 0
    fp_rate = (s["v86_fp"] / max(1, s["v86_improved"]) * 100) if s["v86_improved"] else 0
    
    lines.append("### 10.1 Key Findings")
    lines.append("")
    lines.append("1. **V85 Full Dataset Size:** %d templates, %d series replayed" % (
        s["total_templates"], s["total_series"]))
    lines.append("2. **V86 Interception Rate:** %d/%d (%.1f%%) series blocked by V86" % (
        s["v86_blocked"], total_series, (s["v86_blocked"] / max(1, total_series) * 100) if total_series else 0))
    lines.append("3. **New Interceptions (IMPROVED):** %d series (%.1f%%)" % (s["v86_improved"], improved_pct))
    lines.append("4. **Regressions (REGRESSED):** %d series (%.1f%%)" % (s["v86_regression"], regression_pct))
    lines.append("5. **FP Rate:** %.1f%% (of new interceptions)" % fp_rate)
    lines.append("6. **DATA_MISSING:** %d series (upstream data issues, not rule misses)" % s["v86_data_missing"])
    lines.append("7. **Throughput:** %.0f series/sec, avg latency %.3f ms, p95 %.3f ms" % (
        s["throughput_series_per_sec"], s["avg_latency_ms"], s["p95_latency_ms"]))
    lines.append("")
    
    if s["v86_regression"] > 0:
        lines.append("### 10.2 Regression Analysis")
        lines.append("")
        lines.append("WARNING: %d regressions detected. V86 rule engine missed blocks that V85 baseline caught." % s["v86_regression"])
        lines.append("These need investigation before production deployment.")
        lines.append("")
    
    if s["v86_fp"] > 0:
        lines.append("### 10.3 FP Analysis")
        lines.append("")
        lines.append("WARNING: %d false positives detected. V86 blocked series that should pass." % s["v86_fp"])
        lines.append("")
    
    if s["v86_regression"] == 0 and s["v86_fp"] == 0:
        lines.append("### 10.2 Verdict")
        lines.append("")
        lines.append("VERDICT: PASS - V86 rule engine achieves zero regressions and zero false positives")
        lines.append("on the full V85 dataset of %d series. Safe for production deployment." % total_series)
        lines.append("")
    
    lines.append("### 10.4 Deployment Recommendation")
    lines.append("")
    lines.append("| Check | Result |")
    lines.append("|-------|--------|")
    lines.append("| Zero Regression | %s |" % ("PASS" if s["v86_regression"] == 0 else "FAIL"))
    lines.append("| FP Rate < 5%% | %s |" % ("PASS" if fp_rate < 5 else "FAIL"))
    lines.append("| P95 Latency < 5ms | %s |" % ("PASS" if s["p95_latency_ms"] < 5 else "FAIL"))
    lines.append("| Throughput > 1000 series/sec | %s |" % ("PASS" if s["throughput_series_per_sec"] > 1000 else "FAIL"))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report auto-generated by full_dataset_replay_runner.py v%s*" % VERSION)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Full Dataset Replay Runner")
    parser.add_argument("--use-alias", action="store_true", help="Include alias engine resolution")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--report", type=str, default=None, help="Output report path")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    
    args = parser.parse_args()
    
    output_path = args.output or os.path.join(OUT_DIR, "full_replay_results.json")
    report_path = args.report or os.path.join(OUT_DIR, "v86_rule_full_dataset_replay_report.md")
    
    if not args.quiet:
        print("=" * 70)
        print("V85 Full Dataset Replay Runner")
        print("Task: %s" % TASK_ID)
        print("=" * 70)
    
    # Step 1: Load V85 templates
    if not args.quiet:
        print("\n[1/4] Loading V85 template data...")
    template_data = load_v85_templates()
    baseline_stats = load_v85_baseline_stats(template_data)
    series_pairs = extract_series_pairs(template_data)
    
    if not args.quiet:
        print("  Templates: %d" % len(template_data.get("templates", [])))
        print("  Series pairs: %d" % len(series_pairs))
        print("  V85 baseline: %d total templates, %d P0, %d P1" % (
            baseline_stats.get("total_templates", 0),
            baseline_stats.get("total_p0", 0),
            baseline_stats.get("total_p1", 0)))
    
    # Step 2: Load V86 rule engine
    if not args.quiet:
        print("\n[2/4] Loading V86 P0+P1 rule engine...")
    engine = load_v86_engine()
    rule_count = engine.get_rule_count()
    
    if not args.quiet:
        print("  Rules loaded: %d" % rule_count)
        print("  P0 rules: %d" % len(engine.get_p0_rules()))
        print("  P1 rules: %d" % len(engine.get_p1_rules()))
    
    # Step 3: Run replay
    if not args.quiet:
        print("\n[3/4] Running full dataset replay (%d series)..." % len(series_pairs))
    replay_data = run_replay(engine, series_pairs, template_data=template_data, use_alias=args.use_alias)
    summary = replay_data["summary"]
    
    if not args.quiet:
        print("  Done in %.1f ms" % summary["elapsed_ms"])
        print("  V86 blocked: %d, passed: %d, data_missing: %d" % (
            summary["v86_blocked"], summary["v86_passed"], summary["v86_data_missing"]))
        print("  Improved: %d, Regressed: %d, Unchanged: %d" % (
            summary["v86_improved"], summary["v86_regression"], summary["v86_unchanged"]))
        print("  TP: %d, FP: %d" % (summary["v86_tp"], summary["v86_fp"]))
        print("  Throughput: %.0f series/sec" % summary["throughput_series_per_sec"])
    
    # Step 4: Generate outputs
    if not args.quiet:
        print("\n[4/4] Generating outputs...")
    
    # Save JSON results
    # Compact output: remove all_results (too large)
    compact = {k: v for k, v in replay_data.items() if k != "all_results"}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(compact, f, ensure_ascii=False, indent=2)
    if not args.quiet:
        print("  JSON: %s (%d bytes)" % (output_path, os.path.getsize(output_path)))
    
    # Generate Markdown report
    report_md = generate_report_md(replay_data, baseline_stats)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    if not args.quiet:
        print("  Report: %s (%d bytes)" % (report_path, os.path.getsize(report_path)))
    
    if not args.quiet:
        print("\n" + "=" * 70)
        print("Full Dataset Replay Complete")
        print("=" * 70)
        print("Verdict: %s" % ("PASS" if summary["v86_regression"] == 0 and summary["v86_fp"] == 0 else "REVIEW"))
        print("=" * 70)
    
    return replay_data


if __name__ == "__main__":
    main()