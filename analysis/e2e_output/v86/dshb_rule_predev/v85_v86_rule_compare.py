#!/usr/bin/env python3
"""
V85 → V86 Rule Metrics Comparison Script
===========================================
任务: DSHB_V86_RULE_ENGINE_PREDEV_AND_BL_REGRESSION_TEST · T2.4
分支: feature/v85-chart-template

功能:
  1. 自动读取V85快照结果（sim_sceneA/B_result.csv, cross_variety_p0_validation.csv）
  2. 执行V86原型引擎全量回放
  3. 逐case对比V85/V86指标差异
  4. 输出指标差异汇总，标记规则改动带来的指标变化
  5. 输出变更影响矩阵和回归风险评估

使用:
  python v85_v86_rule_compare.py --help
  python v85_v86_rule_compare.py --v85-baseline sim_sceneA_result.csv
  python v85_v86_rule_compare.py --v85-baseline sim_sceneB_result.csv --output report.md
"""

import json
import csv
import os
import sys
import argparse
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

# Import V86 engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v86_p0_rule_prototype import (
    V86RuleEngine, create_v86_p0_rules, BlacklistRule, RuleSeverity, RuleStatus,
    MatchResult, load_test_cases_from_csv, RegressionTestRunner
)

VERSION = "v1.0"
TASK_ID = "DSHB_V86_RULE_ENGINE_PREDEV_AND_BL_REGRESSION_TEST"
BRANCH = "feature/v85-chart-template"


# =============================================================================
# Section 1: Data Models
# =============================================================================

@dataclass
class CaseComparison:
    """Single case comparison between V85 baseline and V86 prototype."""
    case_id: str
    source_type: str
    template_id: str
    indicator_name: str
    matched_name: str
    risk_id: str
    risk_level: str
    
    # V85 baseline
    v85_status: str
    v85_rule: str
    v85_tp: int
    v85_fp: int
    
    # V86 result
    v86_status: str
    v86_rule: str
    v86_tp: int
    v86_fp: int
    
    # Diff
    status_changed: bool
    rule_changed: bool
    tp_change: int
    fp_change: int
    change_type: str  # IMPROVEMENT / REGRESSION / UNCHANGED / NEW_BLOCK / NEW_PASS


@dataclass
class MetricSummary:
    """Aggregate metrics for V85 vs V86 comparison."""
    v85_total_cases: int = 0
    v85_blocked: int = 0
    v85_passed: int = 0
    v85_data_missing: int = 0
    v85_tp: int = 0
    v85_fp: int = 0
    v85_p0_interception_rate: float = 0.0
    
    v86_total_cases: int = 0
    v86_blocked: int = 0
    v86_passed: int = 0
    v86_data_missing: int = 0
    v86_tp: int = 0
    v86_fp: int = 0
    v86_p0_interception_rate: float = 0.0
    
    # Deltas
    delta_blocked: int = 0
    delta_tp: int = 0
    delta_fp: int = 0
    delta_p0_rate: float = 0.0
    total_improvements: int = 0
    total_regressions: int = 0
    total_new_blocks: int = 0
    total_new_passes: int = 0
    total_unchanged: int = 0


# =============================================================================
# Section 2: Comparison Engine
# =============================================================================

class V85V86Comparator:
    """
    Compares V85 baseline results with V86 prototype engine output.
    
    Reads V85 simulation results, runs V86 engine, and computes
    per-case and aggregate metric differences.
    """
    
    def __init__(self, v85_baseline_path: str, output_dir: str = "."):
        self.v85_baseline_path = v85_baseline_path
        self.output_dir = output_dir
        self.comparisons: List[CaseComparison] = []
        self.summary = MetricSummary()
    
    def load_v85_baseline(self) -> List[Dict]:
        """Load V85 baseline results from CSV."""
        records = []
        with open(self.v85_baseline_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
        return records
    
    def run_v86_engine(self, records: List[Dict]) -> List[Dict]:
        """Run V86 prototype engine against V85 test cases."""
        engine = V86RuleEngine(rules=create_v86_p0_rules())
        
        # Add complementarity and cross-variety rules for complete comparison
        extra_rules = [
            BlacklistRule(
                rule_id="BL-009",
                name="利润与需求互斥",
                category="经济口径",
                severity=RuleSeverity.P0,
                left_patterns=["利润", "盈利", "盈亏", "毛利"],
                right_patterns=["需求", "需求量", "需求侧"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-018",
                name="跨品种匹配禁止(锡↔镍)",
                category="品种口径",
                severity=RuleSeverity.P0,
                left_patterns=["锡", "锡锭", "锡矿"],
                right_patterns=["镍", "镍板", "镍豆", "镍铁", "镍矿"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-018a",
                name="锡与镍跨品种禁止(扩展)",
                category="品种口径",
                severity=RuleSeverity.P0,
                left_patterns=["锡", "锡锭", "锡矿", "锡精矿", "LME锡", "焊锡", "表观消费量"],
                right_patterns=["镍", "镍板", "镍豆", "镍铁", "镍矿", "COMEX镍", "LME镍", "精炼镍"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-016",
                name="利润与产量互斥",
                category="经济口径",
                severity=RuleSeverity.P1,
                left_patterns=["利润", "盈利", "盈亏"],
                right_patterns=["产量", "产出"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-025",
                name="消费量与产量互斥(反向)",
                category="供需口径",
                severity=RuleSeverity.P0,
                left_patterns=["消费量", "消费"],
                right_patterns=["产量", "产出", "生产量"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-015",
                name="国内销量与出口互斥(反向)",
                category="贸易口径",
                severity=RuleSeverity.P0,
                left_patterns=["国内销量", "内销", "国内销售"],
                right_patterns=["出口", "出口量"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-005",
                name="场内库存与非仓单库存互斥",
                category="库存口径",
                severity=RuleSeverity.P0,
                left_patterns=["场内库存", "注册仓单", "期货库存", "注册仓单库存"],
                right_patterns=["非仓单", "非仓单库存", "社会库存", "厂内库存", "社会仓库库存"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-003",
                name="销量与产量互斥",
                category="供需口径",
                severity=RuleSeverity.P0,
                left_patterns=["销量", "销售量"],
                right_patterns=["产量", "产出", "生产量"],
                status=RuleStatus.ACTIVE,
            ),
            BlacklistRule(
                rule_id="BL-002",
                name="产量与销量互斥",
                category="供需口径",
                severity=RuleSeverity.P0,
                left_patterns=["产量", "产出", "生产量"],
                right_patterns=["销量", "销售量", "销售金额"],
                status=RuleStatus.ACTIVE,
            ),
        ]
        engine._add_rules(extra_rules)
        
        v86_results = []
        for record in records:
            indicator = record.get("indicator_name", "")
            matched = record.get("matched_name", "")
            risk_id = record.get("risk_id", "")
            risk_level = record.get("risk_level", "")
            
            result = engine.evaluate(indicator, matched)
            
            v86_record = dict(record)
            v86_record["_v86_result"] = result["result"]
            v86_record["_v86_rule"] = result["blocked_by"] or ""
            v86_record["_v86_triggered"] = result["triggered_rules"]
            v86_record["_v86_severity"] = result["severity"]
            v86_record["_v86_pdf_fix_needed"] = result.get("pdf_fix_needed", False)
            
            v86_results.append(v86_record)
        
        return v86_results
    
    def compare(self, records: List[Dict], v86_results: List[Dict]):
        """Compare V85 baseline with V86 results case by case."""
        self.comparisons = []
        
        for v85_rec, v86_rec in zip(records, v86_results):
            comparison = CaseComparison(
                case_id=v85_rec.get("case_id", ""),
                source_type=v85_rec.get("source_type", ""),
                template_id=v85_rec.get("template_id", ""),
                indicator_name=v85_rec.get("indicator_name", ""),
                matched_name=v85_rec.get("matched_name", ""),
                risk_id=v85_rec.get("risk_id", ""),
                risk_level=v85_rec.get("risk_level", ""),
                v85_status=v85_rec.get("new_status", "").strip(),
                v85_rule=v85_rec.get("rule_applied", "").strip(),
                v85_tp=int(v85_rec.get("tp_change", "0") or "0"),
                v85_fp=int(v85_rec.get("fp_change", "0") or "0"),
                v86_status=v86_rec.get("_v86_result", ""),
                v86_rule=v86_rec.get("_v86_rule", ""),
                v86_tp=0,
                v86_fp=0,
                status_changed=False,
                rule_changed=False,
                tp_change=0,
                fp_change=0,
                change_type="UNCHANGED",
            )
            
            # Determine change type
            v85_blocked = v85_rec.get("new_status", "").strip() in ("BLOCKED",)
            v86_blocked = v86_rec.get("_v86_result", "") == "BLOCKED"
            
            comparison.status_changed = v85_blocked != v86_blocked
            comparison.rule_changed = (v85_rec.get("rule_applied", "").strip() or "") != (v86_rec.get("_v86_rule", "") or "")
            
            # Compute TP/FP changes
            v85_expected_blocked = v85_rec.get("new_status", "").strip() == "BLOCKED"
            v86_actual_blocked = v86_blocked
            
            if v85_expected_blocked and v86_actual_blocked:
                comparison.v86_tp = 1  # TP maintained
                comparison.change_type = "UNCHANGED"
            elif not v85_expected_blocked and v86_actual_blocked:
                comparison.v86_tp = 1  # New TP
                comparison.change_type = "NEW_BLOCK"
                comparison.tp_change = 1
            elif v85_expected_blocked and not v86_actual_blocked:
                comparison.change_type = "REGRESSION"
                comparison.tp_change = -1
            else:
                # Both not blocked - check if it's an improvement (new pass)
                v85_was_blocked = v85_rec.get("old_status", "").strip() == "BLOCKED"
                if v85_was_blocked and not v85_blocked and not v86_blocked:
                    comparison.change_type = "UNCHANGED"
                elif not v85_was_blocked and not v85_blocked and not v86_blocked:
                    comparison.change_type = "UNCHANGED"
                else:
                    comparison.change_type = "UNCHANGED"
            
            # FP detection: if V85 expected PASS but V86 blocks
            v85_expected_pass = v85_rec.get("new_status", "").strip() == "PASS"
            if v85_expected_pass and v86_actual_blocked:
                comparison.v86_fp = 1
                comparison.change_type = "NEW_FP"
                comparison.fp_change = 1
            
            self.comparisons.append(comparison)
        
        self._compute_summary(records, v86_results)
    
    def _compute_summary(self, records: List[Dict], v86_results: List[Dict]):
        """Compute aggregate metrics summary."""
        s = self.summary
        
        s.v85_total_cases = len(records)
        s.v85_blocked = sum(1 for r in records if r.get("new_status", "").strip() == "BLOCKED")
        s.v85_passed = sum(1 for r in records if r.get("new_status", "").strip() == "PASS")
        s.v85_data_missing = sum(1 for r in records if r.get("new_status", "").strip() in ("DATA_MISSING", "N/A"))
        s.v85_tp = sum(1 for r in records if r.get("new_status", "").strip() == "BLOCKED")
        s.v85_fp = sum(1 for r in records if r.get("new_status", "").strip() == "PASS" and r.get("old_status", "").strip() == "BLOCKED")
        
        s.v86_total_cases = len(v86_results)
        s.v86_blocked = sum(1 for r in v86_results if r.get("_v86_result", "") == "BLOCKED")
        s.v86_passed = sum(1 for r in v86_results if r.get("_v86_result", "") == "PASSED")
        s.v86_data_missing = sum(1 for r in v86_results if r.get("_v86_result", "") == "DATA_MISSING")
        s.v86_tp = sum(1 for c in self.comparisons if c.v86_tp == 1)
        s.v86_fp = sum(1 for c in self.comparisons if c.v86_fp == 1)
        
        # Deltas
        s.delta_blocked = s.v86_blocked - s.v85_blocked
        s.delta_tp = s.v86_tp - s.v85_tp
        s.delta_fp = s.v86_fp - s.v85_fp
        
        # P0 interception rates
        v85_p0 = [r for r in records if r.get("risk_level", "").strip() == "P0"]
        v85_p0_blocked = [r for r in v85_p0 if r.get("new_status", "").strip() == "BLOCKED"]
        s.v85_p0_interception_rate = (len(v85_p0_blocked) / len(v85_p0) * 100.0) if v85_p0 else 0.0
        
        v86_p0 = [r for r in v86_results if r.get("risk_level", "").strip() == "P0"]
        v86_p0_blocked = [r for r in v86_p0 if r.get("_v86_result", "") == "BLOCKED"]
        s.v86_p0_interception_rate = (len(v86_p0_blocked) / len(v86_p0) * 100.0) if v86_p0 else 0.0
        
        s.delta_p0_rate = s.v86_p0_interception_rate - s.v85_p0_interception_rate
        
        # Change type counts
        for c in self.comparisons:
            if c.change_type == "NEW_BLOCK":
                s.total_new_blocks += 1
                s.total_improvements += 1
            elif c.change_type == "REGRESSION":
                s.total_regressions += 1
            elif c.change_type == "NEW_FP":
                s.total_regressions += 1
            elif c.change_type == "UNCHANGED":
                s.total_unchanged += 1
            elif c.change_type == "NEW_PASS":
                s.total_new_passes += 1
                s.total_improvements += 1
        
        self.summary = s
    
    def print_report(self):
        """Print detailed comparison report."""
        s = self.summary
        
        print("=" * 80)
        print("V85 → V86 Rule Metrics Comparison Report")
        print(f"Version: {VERSION} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"V85 Baseline: {self.v85_baseline_path}")
        print(f"V86 Engine: v86.0-alpha-proto")
        print("=" * 80)
        
        # 1. Aggregate Metrics
        print("\n[1] Aggregate Metrics Comparison")
        print(f"{'Metric':<30} {'V85':>10} {'V86':>10} {'Delta':>10}")
        print("-" * 62)
        print(f"{'Total Cases':<30} {s.v85_total_cases:>10} {s.v86_total_cases:>10} {s.delta_blocked:>10}")
        print(f"{'Blocked':<30} {s.v85_blocked:>10} {s.v86_blocked:>10} {s.delta_blocked:>+10}")
        print(f"{'Passed':<30} {s.v85_passed:>10} {s.v86_passed:>10} {s.v86_passed - s.v85_passed:>+10}")
        print(f"{'Data Missing':<30} {s.v85_data_missing:>10} {s.v86_data_missing:>10} {s.v86_data_missing - s.v85_data_missing:>+10}")
        print(f"{'TP':<30} {s.v85_tp:>10} {s.v86_tp:>10} {s.delta_tp:>+10}")
        print(f"{'FP':<30} {s.v85_fp:>10} {s.v86_fp:>10} {s.delta_fp:>+10}")
        print(f"{'P0 Interception Rate':<30} {s.v85_p0_interception_rate:>9.1f}% {s.v86_p0_interception_rate:>9.1f}% {s.delta_p0_rate:>+9.1f}%")
        
        # 2. Change Summary
        print(f"\n[2] Change Type Summary")
        print(f"  New Blocks (Improvement):  {s.total_new_blocks}")
        print(f"  New Passes (Improvement):  {s.total_new_passes}")
        print(f"  Regressions (FP/Loss):     {s.total_regressions}")
        print(f"  Unchanged:                 {s.total_unchanged}")
        print(f"  Total Improvements:        {s.total_improvements}")
        print(f"  Total Regressions:         {s.total_regressions}")
        
        # 3. Per-Case Changes
        changed = [c for c in self.comparisons if c.change_type not in ("UNCHANGED",)]
        if changed:
            print(f"\n[3] Changed Cases ({len(changed)} total)")
            for c in changed:
                icon = {"NEW_BLOCK": "+", "REGRESSION": "-", "NEW_FP": "!", "NEW_PASS": "+"}.get(c.change_type, "?")
                print(f"  [{icon}] {c.change_type:12s} | {c.case_id:20s} | "
                      f"V85={c.v85_status:12s} V86={c.v86_status:12s} | "
                      f"V85_rule={c.v85_rule:15s} V86_rule={c.v86_rule or '-':15s} | "
                      f"risk={c.risk_level}")
        else:
            print(f"\n[3] No changed cases detected.")
        
        # 4. Rule-Level Impact Matrix
        print(f"\n[4] Rule-Level Impact Matrix")
        rule_impact = defaultdict(lambda: {"new_blocks": 0, "regressions": 0, "unchanged": 0, "total": 0})
        for c in self.comparisons:
            rule = c.v86_rule or "(none)"
            rule_impact[rule]["total"] += 1
            if c.change_type == "NEW_BLOCK":
                rule_impact[rule]["new_blocks"] += 1
            elif c.change_type == "REGRESSION":
                rule_impact[rule]["regressions"] += 1
            else:
                rule_impact[rule]["unchanged"] += 1
        
        print(f"  {'Rule':<15} {'Total':>6} {'NewBlock':>10} {'Regression':>10} {'Unchanged':>10}")
        print(f"  {'-'*53}")
        for rule, stats in sorted(rule_impact.items()):
            print(f"  {rule:<15} {stats['total']:>6} {stats['new_blocks']:>10} {stats['regressions']:>10} {stats['unchanged']:>10}")
        
        # 5. Regression Risk Assessment
        print(f"\n[5] Regression Risk Assessment")
        if s.total_regressions == 0:
            print(f"  Result: NO REGRESSION DETECTED")
            print(f"  Risk Level: LOW")
            print(f"  Recommendation: SAFE TO PROCEED")
        else:
            print(f"  Result: {s.total_regressions} REGRESSION(S) DETECTED")
            print(f"  Risk Level: HIGH")
            print(f"  Recommendation: REVIEW AND RESOLVE BEFORE DEPLOYMENT")
        
        print(f"\n[6] Key Findings")
        if s.delta_p0_rate > 0:
            print(f"  + P0 interception rate improved by {s.delta_p0_rate:.1f}%")
        elif s.delta_p0_rate < 0:
            print(f"  - P0 interception rate decreased by {abs(s.delta_p0_rate):.1f}%")
        else:
            print(f"  = P0 interception rate unchanged ({s.v85_p0_interception_rate:.1f}%)")
        
        if s.delta_tp > 0:
            print(f"  + TP increased by {s.delta_tp}")
        elif s.delta_tp < 0:
            print(f"  - TP decreased by {abs(s.delta_tp)}")
        
        if s.delta_fp > 0:
            print(f"  - FP increased by {s.delta_fp} (REGRESSION)")
        elif s.delta_fp == 0:
            print(f"  = FP unchanged at {s.v85_fp}")
        
        print("=" * 80)
    
    def save_json_report(self, output_path: str):
        """Save comparison report as JSON."""
        report = {
            "version": VERSION,
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "task_id": TASK_ID,
            "branch": BRANCH,
            "v85_baseline": self.v85_baseline_path,
            "summary": {
                "v85_total_cases": self.summary.v85_total_cases,
                "v85_blocked": self.summary.v85_blocked,
                "v85_tp": self.summary.v85_tp,
                "v85_fp": self.summary.v85_fp,
                "v85_p0_interception_rate": round(self.summary.v85_p0_interception_rate, 2),
                "v86_total_cases": self.summary.v86_total_cases,
                "v86_blocked": self.summary.v86_blocked,
                "v86_tp": self.summary.v86_tp,
                "v86_fp": self.summary.v86_fp,
                "v86_p0_interception_rate": round(self.summary.v86_p0_interception_rate, 2),
                "delta_blocked": self.summary.delta_blocked,
                "delta_tp": self.summary.delta_tp,
                "delta_fp": self.summary.delta_fp,
                "delta_p0_rate": round(self.summary.delta_p0_rate, 2),
                "total_improvements": self.summary.total_improvements,
                "total_regressions": self.summary.total_regressions,
                "total_new_blocks": self.summary.total_new_blocks,
                "total_new_passes": self.summary.total_new_passes,
                "total_unchanged": self.summary.total_unchanged,
            },
            "changed_cases": [
                {
                    "case_id": c.case_id,
                    "risk_id": c.risk_id,
                    "risk_level": c.risk_level,
                    "change_type": c.change_type,
                    "v85_status": c.v85_status,
                    "v85_rule": c.v85_rule,
                    "v86_status": c.v86_status,
                    "v86_rule": c.v86_rule,
                    "tp_change": c.tp_change,
                    "fp_change": c.fp_change,
                }
                for c in self.comparisons if c.change_type != "UNCHANGED"
            ],
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nJSON report saved to: {output_path}")


# =============================================================================
# Section 3: CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V85 → V86 Rule Metrics Comparison Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--v85-baseline", required=True,
                        help="Path to V85 baseline CSV (e.g. sim_sceneA_result.csv)")
    parser.add_argument("--output", type=str, default="comparison_report.json",
                        help="Output JSON report path (default: comparison_report.json)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show all cases (not just changed)")
    parser.add_argument("--version", action="version", version=VERSION)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.v85_baseline):
        print(f"Error: V85 baseline file not found: {args.v85_baseline}")
        sys.exit(1)
    
    comparator = V85V86Comparator(args.v85_baseline, os.path.dirname(args.output) or ".")
    
    # Load V85 baseline
    records = comparator.load_v85_baseline()
    print(f"Loaded {len(records)} records from V85 baseline: {args.v85_baseline}")
    
    # Run V86 engine
    print("Running V86 engine...")
    v86_results = comparator.run_v86_engine(records)
    
    # Compare
    comparator.compare(records, v86_results)
    
    # Print report
    comparator.print_report()
    
    # Save JSON report
    comparator.save_json_report(args.output)
    
    # Exit code based on regressions
    sys.exit(0 if comparator.summary.total_regressions == 0 else 1)


if __name__ == "__main__":
    main()
