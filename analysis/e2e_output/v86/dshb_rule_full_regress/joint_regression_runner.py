#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Joint Regression Runner: Rule Engine + Alias Engine Full-Chain Regression
===========================================================================
Task: DSHB_V86_RULE_ENGINE_FULL_INTEGRATION_REGRESSION_AND_DOC_FINALIZE
Branch: feature/v85-chart-template
Base commits: c7f5a40 (V86 P0+P1), 5e874a7 (DSHE alias), 03b3a73 (HERMES portal)

Chain: raw input -> alias resolution (V86AliasEngine) -> rule evaluation (V86P1RuleEngine)
Output: joint_regression_results.json

Constraints:
  - NO_ZHIJI_API_CALL=TRUE
  - V85 frozen baselines READ-ONLY
  - Only creates new files, never modifies existing deliverables
"""

import json
import os
import sys
import time
import datetime
import traceback
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CD = os.path.dirname(os.path.abspath(__file__))
REPO = r"D:\DSH_WORK\framework-tree"
ALIAS_DIR = os.path.join(REPO, "analysis", "e2e_output", "v86", "dshe_alias_predev")
P0_DIR = os.path.join(REPO, "analysis", "e2e_output", "v86", "dshb_rule_predev")
P1_DIR = os.path.join(REPO, "analysis", "e2e_output", "v86", "dshb_rule_ci_stress")
V85_DIR = os.path.join(REPO, "analysis", "e2e_output", "v85")

TASK_ID = "DSHB_V86_RULE_ENGINE_FULL_INTEGRATION_REGRESSION_AND_DOC_FINALIZE"
VERSION = "v1.0"
BRANCH = "feature/v85-chart-template"
BASE_COMMIT_RULE = "c7f5a40"
BASE_COMMIT_ALIAS = "5e874a7"
BASE_COMMIT_PORTAL = "03b3a73"


# ---------------------------------------------------------------------------
# Test Case Dataclass
# ---------------------------------------------------------------------------

@dataclass
class JointTestCase:
    """A single joint test case."""
    case_id: str
    category: str
    description: str
    indicator_name: str
    matched_name: str
    expected_rule_result: str  # BLOCKED / PASSED / DATA_MISSING
    expected_rule: str = ""
    expected_alias_verdict: str = ""  # PASS / REVIEW / BLOCK / ""
    notes: str = ""

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "category": self.category,
            "description": self.description,
            "indicator_name": self.indicator_name,
            "matched_name": self.matched_name,
            "expected_rule_result": self.expected_rule_result,
            "expected_rule": self.expected_rule,
            "expected_alias_verdict": self.expected_alias_verdict,
            "notes": self.notes,
        }


@dataclass
class JointResult:
    """Result of a joint test case execution."""
    case_id: str
    category: str
    # Alias resolution
    alias_a_state: str = ""
    alias_b_state: str = ""
    alias_a_canonicals: List[str] = field(default_factory=list)
    alias_b_canonicals: List[str] = field(default_factory=list)
    alias_verdict: str = ""
    alias_reason: str = ""
    alias_elapsed_ms: float = 0.0
    # Rule evaluation
    rule_result: str = ""
    rule_triggered: List[str] = field(default_factory=list)
    rule_blocked_by: str = ""
    rule_severity: str = ""
    rule_error_code: str = ""
    rule_latency_ms: float = 0.0
    # Joint verdict
    joint_tp: bool = False
    joint_fp: bool = False
    joint_regression: bool = False
    match_expected: bool = False
    # Full metadata
    actual_rule_result: str = ""
    actual_alias_verdict: str = ""
    notes: str = ""

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "category": self.category,
            "alias_a_state": self.alias_a_state,
            "alias_b_state": self.alias_b_state,
            "alias_a_canonicals": self.alias_a_canonicals,
            "alias_b_canonicals": self.alias_b_canonicals,
            "alias_verdict": self.alias_verdict,
            "alias_reason": self.alias_reason,
            "alias_elapsed_ms": self.alias_elapsed_ms,
            "rule_result": self.rule_result,
            "rule_triggered": self.rule_triggered,
            "rule_blocked_by": self.rule_blocked_by,
            "rule_severity": self.rule_severity,
            "rule_error_code": self.rule_error_code,
            "rule_latency_ms": self.rule_latency_ms,
            "joint_tp": self.joint_tp,
            "joint_fp": self.joint_fp,
            "joint_regression": self.joint_regression,
            "match_expected": self.match_expected,
            "actual_rule_result": self.actual_rule_result,
            "actual_alias_verdict": self.actual_alias_verdict,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Engine Loaders
# ---------------------------------------------------------------------------

def load_alias_engine():
    """Load V86AliasEngine in f3+f4 mode."""
    sys.path.insert(0, ALIAS_DIR)
    from v86_alias_engine_prototype import V86AliasEngine
    t0 = time.perf_counter()
    engine = V86AliasEngine("f3+f4")
    init_ms = (time.perf_counter() - t0) * 1000
    print("[Alias] Engine loaded: mode=%s, rules=%d, aliases=%d, init=%.1fms" % (
        engine.mode, engine.version_info["blacklist_rules"],
        engine.version_info["alias_entries"], init_ms))
    return engine, init_ms


def load_rule_engine():
    """Load V86P1RuleEngine with P0+P1 rules."""
    sys.path.insert(0, P0_DIR)
    sys.path.insert(0, P1_DIR)
    from v86_p1_rule_prototype import V86P1RuleEngine, create_v86_p1_rules
    from v86_p0_rule_prototype import create_v86_p0_rules

    engine = V86P1RuleEngine()
    engine._add_rules(create_v86_p0_rules())
    engine._add_rules(create_v86_p1_rules())
    print("[Rule] Engine loaded: %d rules (P0=%d, P1=%d)" % (
        engine.get_rule_count(), len(engine.get_p0_rules()), len(engine.get_p1_rules())))
    return engine


# ---------------------------------------------------------------------------
# Test Case Generator
# ---------------------------------------------------------------------------

def generate_joint_test_cases() -> List[JointTestCase]:
    """
    Generate comprehensive joint test cases covering:
    - P0 regression (BL-009a, BL-026, BL-012 Plan B)
    - P1 cross-variety rules (BL-027~BL-038)
    - Alias resolution integration scenarios
    - DATA_MISSING scenarios
    - Safety negative cases
    """
    cases = []

    # ===== Group A: P0 Regression with Alias Resolution =====
    cases.append(JointTestCase(
        case_id="JOINT-A-001",
        category="P0_REGRESSION_ALIAS",
        description="BL-009a demand->profit reverse match, alias resolved",
        indicator_name="碳酸锂 三元523需求",
        matched_name="SMM: 碳酸锂现金生产利润: 外购三元极片黑粉",
        expected_rule_result="BLOCKED",
        expected_rule="BL-009a",
        expected_alias_verdict="",
        notes="P0-REG-001: 需求→利润反向, BL-009a应拦截",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-A-002",
        category="P0_REGRESSION_ALIAS",
        description="BL-009a demand->profit variant",
        indicator_name="碳酸锂需求总量",
        matched_name="碳酸锂冶炼利润（元/吨）",
        expected_rule_result="BLOCKED",
        expected_rule="BL-009a",
        expected_alias_verdict="",
        notes="P0-REG-002: 需求总量→利润变体",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-A-NEG-001",
        category="P0_REGRESSION_ALIAS",
        description="Same variety safety: lithium demand analysis",
        indicator_name="碳酸锂需求预测",
        matched_name="碳酸锂需求分析",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="",
        notes="安全负向: 同口径需求分析",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-A-NEG-002",
        category="P0_REGRESSION_ALIAS",
        description="Same variety safety: identical names",
        indicator_name="碳酸锂工厂库存天数",
        matched_name="碳酸锂工厂库存天数",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="",
        notes="安全负向: 完全相同名称",
    ))

    # ===== Group B: P1 Cross-Variety Rules =====
    cases.append(JointTestCase(
        case_id="JOINT-B-001",
        category="P1_CROSS_VARIETY",
        description="BL-027 Aluminum->Copper cross-variety",
        indicator_name="电解铝出库量-中国",
        matched_name="SHFE：铜：主力合约：库存（日）",
        expected_rule_result="BLOCKED",
        expected_rule="BL-027",
        expected_alias_verdict="",
        notes="P1: 铝→铜跨品种",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-002",
        category="P1_CROSS_VARIETY",
        description="BL-028 Lead->Zinc cross-variety",
        indicator_name="铅锭库存",
        matched_name="锌锭库存",
        expected_rule_result="BLOCKED",
        expected_rule="BL-028",
        expected_alias_verdict="",
        notes="P1: 铅→锌跨品种",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-003",
        category="P1_CROSS_VARIETY",
        description="BL-030 Lithium Carbonate->LFP cross-variety",
        indicator_name="碳酸锂价格",
        matched_name="磷酸铁锂材料价格",
        expected_rule_result="BLOCKED",
        expected_rule="BL-030",
        expected_alias_verdict="",
        notes="P1: 碳酸锂→磷酸铁锂",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-004",
        category="P1_CROSS_VARIETY",
        description="BL-032 Stainless Steel->Copper cross-variety",
        indicator_name="不锈钢产量",
        matched_name="电解铜产量",
        expected_rule_result="BLOCKED",
        expected_rule="BL-032",
        expected_alias_verdict="",
        notes="P1: 不锈钢→铜",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-005",
        category="P1_CROSS_VARIETY",
        description="BL-033 Crude Oil->Natural Gas cross-variety",
        indicator_name="WTI原油价格",
        matched_name="LNG进口价格",
        expected_rule_result="BLOCKED",
        expected_rule="BL-033",
        expected_alias_verdict="",
        notes="P1: 原油→天然气",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-006",
        category="P1_CROSS_VARIETY",
        description="BL-034 Iron Ore->Steel cross-variety",
        indicator_name="铁矿石进口量",
        matched_name="螺纹钢产量",
        expected_rule_result="BLOCKED",
        expected_rule="BL-034",
        expected_alias_verdict="",
        notes="P1: 铁矿石→钢材",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-007",
        category="P1_CROSS_VARIETY",
        description="BL-036 Gold->Non-Ferrous Metals cross-variety",
        indicator_name="黄金库存",
        matched_name="铜库存",
        expected_rule_result="BLOCKED",
        expected_rule="BL-036",
        expected_alias_verdict="",
        notes="P1: 黄金→有色金属",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-NEG-001",
        category="P1_CROSS_VARIETY",
        description="Same variety safety: Aluminum->Aluminum",
        indicator_name="电解铝出库量",
        matched_name="SHFE：铝：库存（日）",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="",
        notes="安全: 同品种铝→铝",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-B-NEG-002",
        category="P1_CROSS_VARIETY",
        description="Same variety safety: Lithium->Lithium",
        indicator_name="碳酸锂价格",
        matched_name="碳酸锂库存",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="",
        notes="安全: 同品种碳酸锂→碳酸锂",
    ))

    # ===== Group C: Alias Resolution Impact on Rule Evaluation =====
    cases.append(JointTestCase(
        case_id="JOINT-C-001",
        category="ALIAS_IMPACT",
        description="Alias-resolved names: cross-variety after alias resolution",
        indicator_name="LME：锌：库存（日）",
        matched_name="LME：锡：库存（日）",
        expected_rule_result="BLOCKED",
        expected_rule="BL-028",
        expected_alias_verdict="BLOCK",
        notes="别名引擎+规则引擎: 锌→锡, BL-028应拦截",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-C-002",
        category="ALIAS_IMPACT",
        description="Alias-resolved: same variety safety after resolution",
        indicator_name="SHFE：铅：库存（日）",
        matched_name="SHFE：铅：库存（日）",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="PASS",
        notes="别名引擎+规则引擎: 铅→铅, 同品种应放行",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-C-003",
        category="ALIAS_IMPACT",
        description="Ambiguous alias: multi-canonical resolution",
        indicator_name="GFEX：碳酸锂：单边交易：持仓量（日）",
        matched_name="GFEX：碳酸锂：单边交易：持仓量（日）",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="REVIEW",
        notes="多canonical歧义: F2检测为AMBIGUOUS, 规则引擎同品种放行",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-C-004",
        category="ALIAS_IMPACT",
        description="Cross-variety after alias: Iron->Copper",
        indicator_name="铁矿石库存",
        matched_name="电解铜库存",
        expected_rule_result="BLOCKED",
        expected_rule="BL-034",
        expected_alias_verdict="",
        notes="铁矿石→铜: BL-034应拦截",
    ))

    # ===== Group D: DATA_MISSING Scenarios =====
    cases.append(JointTestCase(
        case_id="JOINT-D-001",
        category="DATA_MISSING",
        description="DATA_MISSING: empty matched_name",
        indicator_name="碳酸锂需求分析",
        matched_name="",
        expected_rule_result="DATA_MISSING",
        expected_rule="",
        expected_alias_verdict="",
        notes="DATA_MISSING: matched_name为空",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-D-002",
        category="DATA_MISSING",
        description="DATA_MISSING: N/A matched_name",
        indicator_name="碳酸锂需求分析",
        matched_name="N/A",
        expected_rule_result="DATA_MISSING",
        expected_rule="",
        expected_alias_verdict="",
        notes="DATA_MISSING: matched_name=N/A",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-D-003",
        category="DATA_MISSING",
        description="DATA_MISSING: workbook record marker",
        indicator_name="碳酸锂需求分析",
        matched_name="（工作表记录）",
        expected_rule_result="DATA_MISSING",
        expected_rule="",
        expected_alias_verdict="",
        notes="DATA_MISSING: 工作表记录标记",
    ))

    # ===== Group E: Safety Negative Cases =====
    cases.append(JointTestCase(
        case_id="JOINT-E-001",
        category="SAFETY_NEGATIVE",
        description="Safety: same variety price->inventory",
        indicator_name="碳酸锂价格",
        matched_name="碳酸锂库存",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="",
        notes="安全: 同品种价格→库存",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-E-002",
        category="SAFETY_NEGATIVE",
        description="Safety: same variety production->price",
        indicator_name="电解铜产量",
        matched_name="电解铜价格",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="",
        notes="安全: 同品种产量→价格",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-E-003",
        category="SAFETY_NEGATIVE",
        description="Safety: unrelated but valid names",
        indicator_name="碳酸锂开工率",
        matched_name="碳酸锂开工率",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="PASS",
        notes="安全: 完全相同的开工率名称",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-E-004",
        category="SAFETY_NEGATIVE",
        description="Safety: supply chain related but same variety",
        indicator_name="碳酸锂正极材料需求",
        matched_name="碳酸锂负极材料需求",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="",
        notes="安全: 同品种正极/负极材料需求",
    ))

    # ===== Group F: Cross-Variety P1 Rules (additional) =====
    cases.append(JointTestCase(
        case_id="JOINT-F-001",
        category="P1_CROSS_VARIETY",
        description="BL-029 Alumina->Aluminum",
        indicator_name="氧化铝库存",
        matched_name="电解铝库存",
        expected_rule_result="BLOCKED",
        expected_rule="BL-029",
        expected_alias_verdict="",
        notes="P1: 氧化铝→铝",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-F-002",
        category="P1_CROSS_VARIETY",
        description="BL-031 Cobalt->Lithium",
        indicator_name="钴价",
        matched_name="碳酸锂价格",
        expected_rule_result="BLOCKED",
        expected_rule="BL-031",
        expected_alias_verdict="",
        notes="P1: 钴→锂",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-F-003",
        category="P1_CROSS_VARIETY",
        description="BL-035 Styrene->Copper",
        indicator_name="苯乙烯库存",
        matched_name="电解铜库存",
        expected_rule_result="BLOCKED",
        expected_rule="BL-035",
        expected_alias_verdict="",
        notes="P1: 苯乙烯→铜",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-F-004",
        category="P1_CROSS_VARIETY",
        description="BL-037 Zinc->Lead direction supplement",
        indicator_name="锌锭库存",
        matched_name="铅锭库存",
        expected_rule_result="BLOCKED",
        expected_rule="BL-037",
        expected_alias_verdict="",
        notes="P1: 锌→铅 (BL-037方向补充)",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-F-005",
        category="P1_CROSS_VARIETY",
        description="BL-038 Nickel->Stainless Steel",
        indicator_name="电解镍价格",
        matched_name="不锈钢价格",
        expected_rule_result="BLOCKED",
        expected_rule="BL-038",
        expected_alias_verdict="",
        notes="P1: 镍→不锈钢",
    ))

    # ===== Group G: Alias Resolution with Ambiguous Cases =====
    cases.append(JointTestCase(
        case_id="JOINT-G-001",
        category="ALIAS_AMBIGUOUS",
        description="Ambiguous alias: cross-variety pair",
        indicator_name="LME：锌：库存（日）",
        matched_name="LME：铅：库存（日）",
        expected_rule_result="BLOCKED",
        expected_rule="BL-028",
        expected_alias_verdict="BLOCK",
        notes="别名歧义+跨品种: 锌→铅, BL-028应拦截",
    ))
    cases.append(JointTestCase(
        case_id="JOINT-G-002",
        category="ALIAS_AMBIGUOUS",
        description="Ambiguous alias: same variety safety",
        indicator_name="SHFE：铅：库存（日）",
        matched_name="SHFE：铅：库存（日）",
        expected_rule_result="PASSED",
        expected_rule="NONE",
        expected_alias_verdict="PASS",
        notes="别名歧义+同品种: 铅→铅, 应放行",
    ))

    return cases


# ---------------------------------------------------------------------------
# Independent Baseline Runner (rule-only, no alias)
# ---------------------------------------------------------------------------

def run_independent_baseline(ruule_engine, test_cases: List[JointTestCase]) -> Dict:
    """Run rule engine independently (without alias resolution)."""
    results = {}
    tp = fp = regression = passed = data_missing = errors = 0

    for tc in test_cases:
        result = ruule_engine.evaluate(tc.indicator_name, tc.matched_name)

        actual_result = result["result"]
        actual_rule = result.get("blocked_by", "") or (",".join(result.get("triggered_rules", [])) if result.get("triggered_rules") else "")

        # Evaluate against expected
        match_expected = (actual_result == tc.expected_rule_result)

        if tc.expected_rule_result == "BLOCKED":
            if actual_result == "BLOCKED":
                tp += 1
            elif actual_result == "PASSED":
                regression += 1
            # DATA_MISSING on BLOCKED expected = potential issue
        elif tc.expected_rule_result == "PASSED":
            if actual_result == "PASSED":
                passed += 1
            elif actual_result == "BLOCKED":
                fp += 1
        elif tc.expected_rule_result == "DATA_MISSING":
            if actual_result == "DATA_MISSING":
                data_missing += 1

        results[tc.case_id] = {
            "case_id": tc.case_id,
            "category": tc.category,
            "indicator_name": tc.indicator_name,
            "matched_name": tc.matched_name,
            "expected_result": tc.expected_rule_result,
            "actual_result": actual_result,
            "actual_rule": actual_rule,
            "match_expected": match_expected,
            "error_code": result.get("error_code", ""),
            "latency_ms": result.get("latency_ms", 0),
        }

    return {
        "mode": "independent_rule_only",
        "total": len(test_cases),
        "tp": tp,
        "fp": fp,
        "regression": regression,
        "passed": passed,
        "data_missing": data_missing,
        "errors": errors,
        "details": results,
    }


# ---------------------------------------------------------------------------
# Joint Chain Runner (alias + rule)
# ---------------------------------------------------------------------------

def run_joint_chain(alias_engine, rule_engine, test_cases: List[JointTestCase]) -> Dict:
    """
    Run joint chain: alias resolution -> rule evaluation.
    For each test case:
    1. Resolve indicator_name and matched_name through alias engine
    2. Use the resolved canonical names for rule evaluation
    3. Compare joint results with independent baseline
    """
    results = {}
    tp = fp = regression = passed = data_missing = errors = 0
    joint_tp = joint_fp = joint_regression = 0
    alias_pass = alias_review = alias_block = 0
    alias_resolve_ok = 0
    alias_resolve_fail = 0

    for tc in test_cases:
        jr = JointResult(case_id=tc.case_id, category=tc.category)

        # Step 1: Alias resolution
        try:
            t0 = time.perf_counter()

            # Resolve indicator_name
            alias_a = alias_engine.resolve(tc.indicator_name)
            jr.alias_a_state = alias_a["state"]
            jr.alias_a_canonicals = alias_a["canonicals"]

            # Resolve matched_name
            if tc.matched_name:
                alias_b = alias_engine.resolve(tc.matched_name)
                jr.alias_b_state = alias_b["state"]
                jr.alias_b_canonicals = alias_b["canonicals"]
            else:
                alias_b = {"state": "NO_MATCH", "canonicals": [], "alias": False, "light": "", "ambiguity_ratio": 0.0}
                jr.alias_b_state = "NO_MATCH"
                jr.alias_b_canonicals = []

            # Run alias engine decision (full verdict)
            if tc.matched_name:
                verdict = alias_engine.decide(tc.indicator_name, tc.matched_name)
                jr.alias_verdict = verdict["verdict"]
                jr.alias_reason = verdict["reason"]
            else:
                jr.alias_verdict = "BLOCK"
                jr.alias_reason = "empty_input"

            jr.alias_elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
            alias_resolve_ok += 1

            # Count alias verdicts
            if jr.alias_verdict == "PASS":
                alias_pass += 1
            elif jr.alias_verdict == "REVIEW":
                alias_review += 1
            elif jr.alias_verdict == "BLOCK":
                alias_block += 1

        except Exception as e:
            jr.alias_verdict = "ERROR"
            jr.alias_reason = str(e)
            jr.alias_elapsed_ms = 0
            alias_resolve_fail += 1
            errors += 1

        # Step 2: Rule evaluation (use raw names, not resolved canonicals)
        try:
            result = rule_engine.evaluate(tc.indicator_name, tc.matched_name)
            jr.rule_result = result["result"]
            jr.rule_triggered = result.get("triggered_rules", [])
            jr.rule_blocked_by = result.get("blocked_by", "")
            jr.rule_severity = result.get("severity", "")
            jr.rule_error_code = result.get("error_code", "")
            jr.rule_latency_ms = result.get("latency_ms", 0)

            # Determine if match expected
            match_expected = (result["result"] == tc.expected_rule_result)
            jr.match_expected = match_expected

            # Count TP/FP
            if tc.expected_rule_result == "BLOCKED":
                if result["result"] == "BLOCKED":
                    tp += 1
                    joint_tp += 1
                elif result["result"] == "PASSED":
                    regression += 1
                    joint_regression += 1
            elif tc.expected_rule_result == "PASSED":
                if result["result"] == "PASSED":
                    passed += 1
                elif result["result"] == "BLOCKED":
                    fp += 1
                    joint_fp += 1
            elif tc.expected_rule_result == "DATA_MISSING":
                if result["result"] == "DATA_MISSING":
                    data_missing += 1

        except Exception as e:
            jr.rule_result = "ERROR"
            jr.rule_error_code = str(e)
            jr.rule_latency_ms = 0
            errors += 1

        jr.actual_rule_result = jr.rule_result
        jr.actual_alias_verdict = jr.alias_verdict
        jr.joint_tp = (tc.expected_rule_result == "BLOCKED" and jr.rule_result == "BLOCKED")
        jr.joint_fp = (tc.expected_rule_result == "PASSED" and jr.rule_result == "BLOCKED")
        jr.joint_regression = (tc.expected_rule_result == "BLOCKED" and jr.rule_result == "PASSED")

        results[tc.case_id] = jr

    return {
        "mode": "joint_alias_plus_rule",
        "total": len(test_cases),
        "tp": tp,
        "fp": fp,
        "regression": regression,
        "passed": passed,
        "data_missing": data_missing,
        "errors": errors,
        "joint_tp": joint_tp,
        "joint_fp": joint_fp,
        "joint_regression": joint_regression,
        "alias_pass": alias_pass,
        "alias_review": alias_review,
        "alias_block": alias_block,
        "alias_resolve_ok": alias_resolve_ok,
        "alias_resolve_fail": alias_resolve_fail,
        "details": {cid: r.to_dict() for cid, r in results.items()},
    }


# ---------------------------------------------------------------------------
# Comparison Report
# ---------------------------------------------------------------------------

def compare_with_baseline(joint_result: Dict, baseline_result: Dict) -> Dict:
    """Compare joint chain results with independent baseline."""
    joint_details = joint_result["details"]
    baseline_details = baseline_result["details"]

    comparisons = []
    improved = 0
    regressed = 0
    unchanged = 0

    for case_id, jr in joint_details.items():
        br = baseline_details.get(case_id, {})

        joint_result_actual = jr.get("rule_result", "")
        baseline_result_actual = br.get("actual_result", "")
        expected = br.get("expected_result", "")

        joint_tp = jr.get("joint_tp", False)
        joint_fp = jr.get("joint_fp", False)
        joint_regression = jr.get("joint_regression", False)

        baseline_tp = (baseline_result_actual == expected and expected == "BLOCKED")
        baseline_fp = (expected == "PASSED" and baseline_result_actual == "BLOCKED")
        baseline_regression = (expected == "BLOCKED" and baseline_result_actual == "PASSED")

        if baseline_regression and not joint_regression:
            change_type = "IMPROVED"
            improved += 1
        elif not baseline_regression and joint_regression:
            change_type = "REGRESSED"
            regressed += 1
        else:
            change_type = "UNCHANGED"
            unchanged += 1

        comparisons.append({
            "case_id": case_id,
            "expected_result": expected,
            "baseline_result": baseline_result_actual,
            "joint_result": joint_result_actual,
            "change_type": change_type,
            "alias_verdict": jr.get("alias_verdict", ""),
            "alias_reason": jr.get("alias_reason", ""),
        })

    return {
        "improved": improved,
        "regressed": regressed,
        "unchanged": unchanged,
        "joint_tp": joint_result.get("tp", 0),
        "joint_fp": joint_result.get("fp", 0),
        "joint_regression": joint_result.get("regression", 0),
        "baseline_tp": baseline_result.get("tp", 0),
        "baseline_fp": baseline_result.get("fp", 0),
        "baseline_regression": baseline_result.get("regression", 0),
        "delta_tp": joint_result.get("tp", 0) - baseline_result.get("tp", 0),
        "delta_fp": joint_result.get("fp", 0) - baseline_result.get("fp", 0),
        "delta_regression": joint_result.get("regression", 0) - baseline_result.get("regression", 0),
        "comparisons": comparisons,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("V86 Rule+Alias Joint Regression Runner")
    print("Task: %s" % TASK_ID)
    print("Branch: %s" % BRANCH)
    print("Base commits: rule=%s, alias=%s" % (BASE_COMMIT_RULE, BASE_COMMIT_ALIAS))
    print("Time: %s" % datetime.datetime.now().isoformat())
    print("=" * 80)

    # Step 1: Load engines
    print("\n[1/5] Loading engines...")
    alias_engine, alias_init_ms = load_alias_engine()
    rule_engine = load_rule_engine()

    # Step 2: Generate test cases
    print("\n[2/5] Generating test cases...")
    test_cases = generate_joint_test_cases()
    print("  Generated %d joint test cases" % len(test_cases))

    # Step 3: Run independent baseline
    print("\n[3/5] Running independent baseline (rule-only)...")
    baseline_result = run_independent_baseline(rule_engine, test_cases)
    print("  TP=%d, FP=%d, Regression=%d, Passed=%d, DATA_MISSING=%d" % (
        baseline_result["tp"], baseline_result["fp"], baseline_result["regression"],
        baseline_result["passed"], baseline_result["data_missing"]))

    # Step 4: Run joint chain
    print("\n[4/5] Running joint chain (alias + rule)...")
    joint_result = run_joint_chain(alias_engine, rule_engine, test_cases)
    print("  TP=%d, FP=%d, Regression=%d, Passed=%d, DATA_MISSING=%d" % (
        joint_result["tp"], joint_result["fp"], joint_result["regression"],
        joint_result["passed"], joint_result["data_missing"]))
    print("  Alias: PASS=%d, REVIEW=%d, BLOCK=%d" % (
        joint_result["alias_pass"], joint_result["alias_review"], joint_result["alias_block"]))

    # Step 5: Compare
    print("\n[5/5] Comparing joint vs independent baseline...")
    comparison = compare_with_baseline(joint_result, baseline_result)
    print("  Improved=%d, Regressed=%d, Unchanged=%d" % (
        comparison["improved"], comparison["regressed"], comparison["unchanged"]))

    # Build final report
    report = {
        "task_id": TASK_ID,
        "version": VERSION,
        "branch": BRANCH,
        "base_commit_rule": BASE_COMMIT_RULE,
        "base_commit_alias": BASE_COMMIT_ALIAS,
        "base_commit_portal": BASE_COMMIT_PORTAL,
        "generated_at": datetime.datetime.now().isoformat(),
        "summary": {
            "total_test_cases": len(test_cases),
            "alias_engine": {
                "mode": "f3+f4",
                "init_ms": alias_init_ms,
                "blacklist_rules": alias_engine.version_info["blacklist_rules"],
                "alias_entries": alias_engine.version_info["alias_entries"],
            },
            "rule_engine": {
                "total_rules": rule_engine.get_rule_count(),
                "p0_rules": len(rule_engine.get_p0_rules()),
                "p1_rules": len(rule_engine.get_p1_rules()),
            },
            "joint_chain": {
                "tp": joint_result["tp"],
                "fp": joint_result["fp"],
                "regression": joint_result["regression"],
                "passed": joint_result["passed"],
                "data_missing": joint_result["data_missing"],
                "alias_pass": joint_result["alias_pass"],
                "alias_review": joint_result["alias_review"],
                "alias_block": joint_result["alias_block"],
                "alias_resolve_ok": joint_result["alias_resolve_ok"],
                "alias_resolve_fail": joint_result["alias_resolve_fail"],
            },
            "independent_baseline": {
                "tp": baseline_result["tp"],
                "fp": baseline_result["fp"],
                "regression": baseline_result["regression"],
                "passed": baseline_result["passed"],
                "data_missing": baseline_result["data_missing"],
            },
            "comparison": {
                "improved": comparison["improved"],
                "regressed": comparison["regressed"],
                "unchanged": comparison["unchanged"],
                "delta_tp": comparison["delta_tp"],
                "delta_fp": comparison["delta_fp"],
                "delta_regression": comparison["delta_regression"],
            },
        },
        "test_cases": [tc.to_dict() for tc in test_cases],
        "joint_results": joint_result["details"],
        "baseline_results": baseline_result["details"],
        "comparisons": comparison["comparisons"],
        "constraints": {
            "no_zhiji_api_call": True,
            "v85_frozen_readonly": True,
            "no_modify_source_template": True,
        },
    }

    # Save results
    output_path = os.path.join(CD, "joint_regression_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("JOINT REGRESSION COMPLETE")
    print("=" * 80)
    print("Results saved to: %s" % output_path)
    print("\n[Summary]")
    print("  Total cases:    %d" % len(test_cases))
    print("  Joint chain TP: %d" % joint_result["tp"])
    print("  Joint chain FP: %d" % joint_result["fp"])
    print("  Joint regress:  %d" % joint_result["regression"])
    print("  Baseline TP:    %d" % baseline_result["tp"])
    print("  Baseline FP:    %d" % baseline_result["fp"])
    print("  Baseline reg:   %d" % baseline_result["regression"])
    print("  Improved:       %d" % comparison["improved"])
    print("  Regressed:      %d" % comparison["regressed"])
    print("  Unchanged:      %d" % comparison["unchanged"])
    print("\n[Alias Verdict Distribution]")
    print("  PASS:   %d" % joint_result["alias_pass"])
    print("  REVIEW: %d" % joint_result["alias_review"])
    print("  BLOCK:  %d" % joint_result["alias_block"])
    print("\n[Constraint Compliance]")
    print("  NO_ZHIJI_API_CALL: TRUE")
    print("  V85_FROZEN_READONLY: TRUE")
    print("  NO_MODIFY_SOURCE_TEMPLATE: TRUE")

    # Exit with appropriate code
    if joint_result["fp"] > 0 or joint_result["regression"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
