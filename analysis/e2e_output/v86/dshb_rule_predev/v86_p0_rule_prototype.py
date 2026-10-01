#!/usr/bin/env python3
"""
V86 P0 Rule Engine Prototype
=============================
任务: DSHB_V86_RULE_ENGINE_PREDEV_AND_BL_REGRESSION_TEST · T2.2
分支: feature/v85-chart-template

P0必做项实现:
  1. V86-P0-001: BL-009a 正式集成 (需求→利润反向)
  2. V86-P0-002: PDF修复逻辑 (matched_name空值检测与修复模拟)
  3. V86-P0-003: BL-026 正式启用 (库存天数跨品种)
  4. V86-P0-004: BL-012方案B (品种感知前置过滤)

设计原则:
  - 完全独立于V85生产逻辑，不导入/不修改V85核心文件
  - 可独立单元测试 (python v86_p0_rule_prototype.py --self-test)
  - 不覆盖V85 production rule logic
  - 不修改任何V85冻结文件
  - 不调用zhiji API
  - 不依赖外部网络/服务

Author: DSHB Agent
Version: v86.0-alpha-proto
Date: 2026-10-01
"""

import json
import csv
import os
import sys
import argparse
import unicodedata
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


# =============================================================================
# Section 0: Version & Constants
# =============================================================================

VERSION = "v86.0-alpha-proto"
TASK_ID = "DSHB_V86_RULE_ENGINE_PREDEV_AND_BL_REGRESSION_TEST"
BRANCH = "feature/v85-chart-template"

# Variety keywords for BL-012 Plan B variety-aware pre-filter
VARIETY_KEYWORDS = {
    "LI": ["碳酸锂", "锂", "盐湖提锂", "锂矿"],
    "NI": ["镍", "电解镍", "精炼镍", "镍精矿", "高冰镍"],
    "SI": ["硅", "工业硅", "金属硅", "多晶硅", "硅矿"],
    "SN": ["锡", "锡锭", "锡矿", "焊锡", "锡精矿"],
    "ZN": ["锌", "锌锭", "锌矿"],
    "LC": ["碳酸锂", "磷酸铁锂", "三元"],
    "CU": ["铜", "电解铜", "铜锭", "铜矿"],
    "AL": ["铝", "电解铝", "铝锭"],
    "PB": ["铅", "电解铅", "铅锭"],
    "AO": ["氧化铝", "氧化铝库存"],
}

# =============================================================================
# Section 1: Data Models
# =============================================================================

class RuleSeverity(Enum):
    """Rule severity levels."""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class RuleStatus(Enum):
    """Rule lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DEPRECATED = "deprecated"


class MatchResult(Enum):
    """Blacklist evaluation result."""
    BLOCKED = "BLOCKED"
    PASSED = "PASSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    DATA_MISSING = "DATA_MISSING"


@dataclass
class BlacklistRule:
    """
    Semantic blacklist rule definition.
    
    Represents a mutual exclusion rule between two groups of patterns.
    If indicator_name matches left_patterns AND matched_name matches right_patterns,
    the pair is BLOCKED.
    
    For V86:
    - BL-009a: left=[需求,需求量,需求侧], right=[利润,盈利,盈亏,毛利]
    - BL-026: left=[库存天数], right=[库存天数] + variety_mismatch filter
    - BL-012 Plan B: variety-aware pre-filter on BL-012
    """
    rule_id: str
    name: str
    category: str
    severity: RuleSeverity
    left_patterns: List[str]
    right_patterns: List[str]
    description: str = ""
    rationale: str = ""
    status: RuleStatus = RuleStatus.ACTIVE
    extra_filter: Optional[str] = None  # e.g. "variety_mismatch"
    variety_aware: bool = False         # BL-012 Plan B: variety-aware pre-filter
    parent_rule: Optional[str] = None   # e.g. BL-009a parent is BL-009
    is_v86_p0: bool = False            # Marked as V86 P0 item


@dataclass
class MatchPair:
    """
    A pair of indicator_name and matched_name to evaluate.
    
    Fields match the V85 CSV schema:
    - source_type: cross_variety_p0 / boundary_test / p0_workbook_extra
    - case_id: e.g. RISK-002, BOUNDARY-001
    - template_id: e.g. TPL-LC-054
    - indicator_name: raw indicator name
    - matched_name: matched name (may be "N/A" for data-missing cases)
    - risk_id: risk identifier
    - risk_level: P0/P1/P2/SAFE/N/A
    - old_status: original status before rule change
    - expected: what we expect the rule engine to produce
    """
    case_id: str
    source_type: str
    template_id: str
    indicator_name: str
    matched_name: str
    risk_id: str
    risk_level: str
    old_status: str
    expected_new_status: str
    expected_rule: str = ""
    notes: str = ""
    actual_new_status: str = ""
    actual_rule: str = ""
    verdict: str = ""  # PASS / FAIL


@dataclass
class RegressionMetrics:
    """Aggregate regression test metrics."""
    total_cases: int = 0
    total_blocked: int = 0
    total_passed: int = 0
    total_data_missing: int = 0
    total_tp: int = 0
    total_fp: int = 0
    total_regression: int = 0
    boundary_pass: int = 0
    boundary_total: int = 0
    p0_interception_rate: float = 0.0
    details: List[Dict] = field(default_factory=list)


# =============================================================================
# Section 2: Rule Engine Core
# =============================================================================

class V86RuleEngine:
    """
    V86 P0 Rule Engine Prototype.
    
    Independent implementation, does not import or modify V85 production code.
    Implements:
    - BL-009a (demand-profit reverse mutual exclusion)
    - BL-026 (inventory days cross-variety prohibition)
    - BL-012 Plan B (variety-aware pre-filter)
    - PDF data-missing detection and fix simulation
    
    Usage:
        engine = V86RuleEngine(rules=[rule1, rule2, ...])
        result = engine.evaluate(indicator_name, matched_name)
    """
    
    def __init__(self, rules: Optional[List[BlacklistRule]] = None):
        """Initialize engine with a set of blacklist rules."""
        self.rules: List[BlacklistRule] = rules or []
        self._rule_map: Dict[str, BlacklistRule] = {}
        self._variant_index: Dict[str, List[BlacklistRule]] = {}
        self._build_indexes()
    
    def _build_indexes(self):
        """Build pattern index for fast lookup."""
        self._rule_map = {}
        self._variant_index = {}
        for rule in self.rules:
            self._rule_map[rule.rule_id] = rule
            # Index all left+right patterns
            for pat in rule.left_patterns + rule.right_patterns:
                norm_pat = self._normalize(pat)
                if norm_pat not in self._variant_index:
                    self._variant_index[norm_pat] = []
                if rule not in self._variant_index[norm_pat]:
                    self._variant_index[norm_pat].append(rule)
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for matching: lowercase, strip, NFKC-like cleaning."""
        import unicodedata
        # NFKC normalization (fullwidth to halfwidth, compatibility decomposition)
        norm = unicodedata.normalize('NFKC', text)
        return norm.strip()
    
    def _add_rules(self, rules: List[BlacklistRule]):
        """Add rules to the engine."""
        for rule in rules:
            if rule.rule_id not in self._rule_map:
                self.rules.append(rule)
        self._build_indexes()
    
    def evaluate(
        self,
        indicator_name: str,
        matched_name: str,
        variety_hint: Optional[str] = None,
    ) -> Dict:
        """
        Evaluate a single (indicator_name, matched_name) pair against all rules.
        
        Args:
            indicator_name: The raw indicator name to check
            matched_name: The matched name (may be "N/A" for data-missing)
            variety_hint: Optional variety hint (e.g. "LI") for BL-026 variety check
            
        Returns:
            Dict with:
                - result: BLOCKED / PASSED / NOT_APPLICABLE / DATA_MISSING
                - triggered_rules: List of rule IDs that triggered
                - blocked_by: Primary blocking rule ID
                - severity: Highest severity among triggered rules
                - notes: Additional information
        """
        # Data-missing detection (V86-P0-002: PDF fix logic)
        if matched_name in ("N/A", "", "（工作表记录）", "N/A（工作表记录）"):
            return {
                "result": MatchResult.DATA_MISSING.value,
                "triggered_rules": [],
                "blocked_by": None,
                "severity": None,
                "notes": "matched_name is empty/N/A - PDF data missing, rule cannot trigger",
                "pdf_fix_needed": True,
            }
        
        triggered_rules = []
        highest_severity = None
        blocked_by = None
        
        for rule in self.rules:
            if rule.status != RuleStatus.ACTIVE:
                continue
            
            # BL-012 Plan B: variety-aware pre-filter
            if rule.variety_aware:
                variety_ind = self._detect_variety(indicator_name)
                variety_match = self._detect_variety(matched_name)
                if variety_hint:
                    variety_match = variety_hint
                # Plan B: if both contain "库存天数" AND same variety, SKIP this rule
                if ("库存天数" in indicator_name and "库存天数" in matched_name
                        and variety_ind == variety_match):
                    continue  # Same variety with same metric - skip (this is the FP fix)
            
            # Check pattern matching
            left_match = self._pattern_match(indicator_name, rule.left_patterns)
            right_match = self._pattern_match(matched_name, rule.right_patterns)
            
            # Bidirectional containment check: if BOTH indicator and matched
            # contain patterns from BOTH left and right sides, it means they
            # are discussing the same combined topic (e.g. "利润与需求分析"
            # vs "利润与需求预测"), not a cross-pattern violation.
            # This handles BOUNDARY-018 correctly.
            # Only applies when left and right patterns are DIFFERENT sets.
            left_set = set(rule.left_patterns)
            right_set = set(rule.right_patterns)
            if left_set != right_set:
                indicator_has_right = self._pattern_match(indicator_name, rule.right_patterns)
                matched_has_left = self._pattern_match(matched_name, rule.left_patterns)
                if indicator_has_right and matched_has_left:
                    continue  # Same context - both sides discuss the same combined topic
            
            if left_match and right_match:
                # Apply extra filter
                if rule.extra_filter == "variety_mismatch":
                    variety_ind = self._detect_variety(indicator_name)
                    variety_match = self._detect_variety(matched_name)
                    if variety_hint:
                        variety_match = variety_hint
                    # BL-026: only trigger if varieties DIFFER
                    if variety_ind == variety_match:
                        continue  # Same variety - not a cross-variety violation
                
                triggered_rules.append(rule.rule_id)
                
                # Track severity
                sev_order = {"P0": 0, "P1": 1, "P2": 2}
                rule_sev = sev_order.get(rule.severity.value, 3)
                if highest_severity is None or rule_sev < sev_order.get(highest_severity.value, 3):
                    highest_severity = rule.severity
                
                if blocked_by is None:
                    blocked_by = rule.rule_id
        
        if triggered_rules:
            return {
                "result": MatchResult.BLOCKED.value,
                "triggered_rules": triggered_rules,
                "blocked_by": blocked_by,
                "severity": highest_severity.value if highest_severity else None,
                "notes": f"Blocked by: {', '.join(triggered_rules)}",
                "pdf_fix_needed": False,
            }
        else:
            return {
                "result": MatchResult.PASSED.value,
                "triggered_rules": [],
                "blocked_by": None,
                "severity": None,
                "notes": "No rules triggered",
                "pdf_fix_needed": False,
            }
    
    @staticmethod
    def _pattern_match(text: str, patterns: List[str]) -> bool:
        """Check if text contains any of the patterns (substring match)."""
        text_norm = unicodedata.normalize('NFKC', text)
        for pat in patterns:
            pat_norm = unicodedata.normalize('NFKC', pat)
            if pat_norm in text_norm:
                return True
        return False
    
    @staticmethod
    def _detect_variety(text: str) -> Optional[str]:
        """
        Detect the variety (commodity type) from text using keyword matching.
        
        Returns variety code (e.g. "LI", "NI", "SI", "SN", "ZN", "CU") or None.
        """
        text_norm = unicodedata.normalize('NFKC', text)
        for variety, keywords in VARIETY_KEYWORDS.items():
            for kw in keywords:
                kw_norm = unicodedata.normalize('NFKC', kw)
                if kw_norm in text_norm:
                    return variety
        return None
    
    def load_rules_from_json(self, json_path: str):
        """Load rules from a JSON file (V85 blacklist JSON format)."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rules = []
        for rule_data in data.get("rules", []):
            severity = RuleSeverity(rule_data.get("severity", "P1"))
            rule = BlacklistRule(
                rule_id=rule_data["rule_id"],
                name=rule_data.get("name", ""),
                category=rule_data.get("category", ""),
                severity=severity,
                left_patterns=rule_data.get("left_patterns", []),
                right_patterns=rule_data.get("right_patterns", []),
                description=rule_data.get("description", ""),
                rationale=rule_data.get("rationale", ""),
            )
            rules.append(rule)
        
        self.rules = rules
        self._build_indexes()
        return len(rules)
    
    def get_rule(self, rule_id: str) -> Optional[BlacklistRule]:
        """Get a rule by ID."""
        return self._rule_map.get(rule_id)
    
    def get_all_rule_ids(self) -> List[str]:
        """Get all rule IDs."""
        return [r.rule_id for r in self.rules]


# =============================================================================
# Section 3: V86 P0 Rules Definition
# =============================================================================

def create_v86_p0_rules() -> List[BlacklistRule]:
    """
    Create the V86 P0 rule set.
    
    V86 P0 items:
    1. V86-P0-001: BL-009a (需求→利润反向, confirmed_new → 正式集成)
    2. V86-P0-003: BL-026 (库存天数跨品种, needs_manual_review → 正式启用)
    3. V86-P0-004: BL-012方案B (品种感知前置过滤, 已验证 → 正式落地)
    
    PDF fix logic (V86-P0-002) is handled in evaluate() via DATA_MISSING detection.
    """
    import unicodedata
    
    rules = []
    
    # =========================================================================
    # V86-P0-001: BL-009a — 需求与利润互斥（反向）
    # 父规则: BL-009 (利润→需求正向)
    # left_patterns = [需求, 需求量, 需求侧]
    # right_patterns = [利润, 盈利, 盈亏, 毛利]
    # 修复: RISK-002 (碳酸锂三元523需求 → 碳酸锂现金生产利润)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-009a",
        name="需求与利润互斥（反向）",
        category="经济口径",
        severity=RuleSeverity.P0,
        left_patterns=["需求", "需求量", "需求侧"],
        right_patterns=["利润", "盈利", "盈亏", "毛利"],
        description="需求与利润是不同经济指标，不可互相匹配。BL-009a是BL-009的反向版本。",
        rationale="BL-009检查利润→需求方向，BL-009a补齐需求→利润方向的缺口。两条规则互补不重叠。",
        status=RuleStatus.ACTIVE,
        parent_rule="BL-009",
        is_v86_p0=True,
    ))
    
    # =========================================================================
    # V86-P0-003: BL-026 — 库存天数跨品种禁止
    # 父规则: BL-012
    # left_patterns = [库存天数]
    # right_patterns = [库存天数]
    # 额外过滤: variety_mismatch (品种不一致时才触发)
    # 修复: RISK-040~050 (9条P1库存天数跨品种)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-026",
        name="库存天数跨品种禁止",
        category="库存口径",
        severity=RuleSeverity.P0,
        left_patterns=["库存天数"],
        right_patterns=["库存天数"],
        description="库存天数指标跨品种匹配禁止。仅当indicator和matched均为库存天数但品种不一致时触发。",
        rationale="不同品种的库存天数无经济含义，属于跨品种误匹配。需BL-012方案B前置过滤配合。",
        status=RuleStatus.ACTIVE,
        extra_filter="variety_mismatch",
        variety_aware=False,
        parent_rule="BL-012",
        is_v86_p0=True,
    ))
    
    # =========================================================================
    # V86-P0-004: BL-012方案B — 品种感知前置过滤
    # 修改类型: fix_version: v86-bl012-planB
    # 修复: RISK-038/039 (同品种FP消除), 保留RISK-040~050 (跨品种TP)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-012",
        name="库存天数与库存量互斥（方案B前置过滤）",
        category="库存口径",
        severity=RuleSeverity.P1,
        left_patterns=["库存天数"],
        right_patterns=["库存", "库存量", "库存总计"],
        description="库存天数与库存量是不同度量，不可互相匹配。方案B增加品种感知前置过滤。",
        rationale="BL-012原始版本会误报同品种库存天数→库存量的匹配（RISK-038/039）。"
                  "方案B在触发前检查品种一致性，同品种时跳过。",
        status=RuleStatus.ACTIVE,
        variety_aware=True,  # Plan B: variety-aware pre-filter
        parent_rule="BL-012",
        is_v86_p0=True,
    ))
    
    # =========================================================================
    # V86-P0-002: PDF数据修复支持
    # BL-022/020/021 规则在V85已存在但因matched_name为空无法触发。
    # V86 P0-002 增加 matched_name 空值检测和修复模拟。
    # 以下为BL-022/020/021规则定义（保持V85原定义，仅确保在V86引擎中可用）
    # =========================================================================
    
    # BL-022: 镍与铜跨品种禁止 (修复RISK-010)
    rules.append(BlacklistRule(
        rule_id="BL-022",
        name="镍与铜跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P0,
        left_patterns=["镍", "电解镍", "精炼镍", "净进口量"],
        right_patterns=["铜", "电解铜", "铜锭", "铜矿"],
        description="镍与铜是不同品种，不可互相匹配。数据修复后RISK-010可被正确拦截。",
        rationale="RISK-010(中国电解镍净进口量)因matched_name为空无法触发BL-022。数据修复后规则可正常触发。",
        status=RuleStatus.ACTIVE,
        is_v86_p0=True,
    ))
    
    # BL-020: 硅与苯乙烯跨品种禁止 (修复RISK-011)
    rules.append(BlacklistRule(
        rule_id="BL-020",
        name="硅与苯乙烯跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P0,
        left_patterns=["工业硅", "金属硅", "硅"],
        right_patterns=["苯乙烯", "苯乙烯库存"],
        description="硅与苯乙烯是不同品种，不可互相匹配。数据修复后RISK-011可被正确拦截。",
        rationale="RISK-011(工业硅样本工厂库存)因matched_name为空无法触发BL-020。数据修复后规则可正常触发。",
        status=RuleStatus.ACTIVE,
        is_v86_p0=True,
    ))
    
    # BL-021: 硅与黄金跨品种禁止 (修复RISK-013)
    rules.append(BlacklistRule(
        rule_id="BL-021",
        name="硅与黄金跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P0,
        left_patterns=["工业硅", "金属硅", "硅"],
        right_patterns=["黄金"],
        description="硅与黄金是不同品种，不可互相匹配。数据修复后RISK-013可被正确拦截。",
        rationale="RISK-013(工业硅供需平衡)因matched_name为空无法触发BL-021。数据修复后规则可正常触发。",
        status=RuleStatus.ACTIVE,
        is_v86_p0=True,
    ))
    
    return rules


# =============================================================================
# Section 4: Test Runner
# =============================================================================

class RegressionTestRunner:
    """
    Regression test runner for V86 P0 rules.
    
    Evaluates test cases against the V86 rule engine and compares
    with expected results.
    """
    
    def __init__(self, engine: V86RuleEngine):
        self.engine = engine
        self.metrics = RegressionMetrics()
    
    def run_case(self, pair: MatchPair) -> Dict:
        """
        Run a single test case.
        
        Returns:
            Dict with case_id, expected, actual, verdict (PASS/FAIL)
        """
        result = self.engine.evaluate(
            pair.indicator_name,
            pair.matched_name,
        )
        
        actual_status = result["result"]
        actual_rule = result["blocked_by"]
        pair.actual_new_status = actual_status
        pair.actual_rule = actual_rule or ""
        
        # Determine verdict
        if pair.expected_new_status in ("BLOCKED", "BLOCKED", "BLOCKED"):
            expected_block = True
        elif pair.expected_new_status in ("PASS", "PASS", "PASSED"):
            expected_block = False
        elif pair.expected_new_status in ("WHITELISTED", "WHITELISTED"):
            expected_block = None  # Whitelist - skip rule check
        elif pair.expected_new_status == "DATA_MISSING":
            expected_block = None  # Data missing - skip
        else:
            expected_block = None
        
        if expected_block is True:
            verdict = "PASS" if actual_status == "BLOCKED" else "FAIL"
        elif expected_block is False:
            verdict = "PASS" if actual_status == "PASSED" else "FAIL"
        else:
            verdict = "SKIP"
        
        pair.verdict = verdict
        
        # Update metrics
        self.metrics.total_cases += 1
        if actual_status == "BLOCKED":
            self.metrics.total_blocked += 1
        elif actual_status == "PASSED":
            self.metrics.total_passed += 1
        elif actual_status == "DATA_MISSING":
            self.metrics.total_data_missing += 1
        
        # TP/FP tracking
        if pair.expected_new_status == "BLOCKED" and actual_status == "BLOCKED":
            self.metrics.total_tp += 1
        elif pair.expected_new_status == "PASS" and actual_status == "BLOCKED":
            self.metrics.total_fp += 1
        
        if pair.source_type == "boundary_test":
            self.metrics.boundary_total += 1
            if verdict == "PASS":
                self.metrics.boundary_pass += 1
        
        # Detail record
        detail = {
            "case_id": pair.case_id,
            "source_type": pair.source_type,
            "indicator_name": pair.indicator_name,
            "matched_name": pair.matched_name,
            "risk_id": pair.risk_id,
            "risk_level": pair.risk_level,
            "expected": pair.expected_new_status,
            "actual": actual_status,
            "expected_rule": pair.expected_rule,
            "actual_rule": actual_rule,
            "verdict": verdict,
        }
        self.metrics.details.append(detail)
        
        return detail
    
    def run_cases(self, pairs: List[MatchPair]) -> RegressionMetrics:
        """Run all test cases and return aggregate metrics."""
        for pair in pairs:
            self.run_case(pair)
        
        # Calculate P0 interception rate
        p0_cases = [d for d in self.metrics.details if d["risk_level"] == "P0"]
        p0_blocked = [d for d in p0_cases if d["actual"] == "BLOCKED"]
        if p0_cases:
            self.metrics.p0_interception_rate = len(p0_blocked) / len(p0_cases) * 100.0
        
        return self.metrics
    
    def print_summary(self, metrics: RegressionMetrics):
        """Print test summary."""
        print("=" * 70)
        print(f"V86 P0 Rule Engine Regression Test Summary")
        print(f"Version: {VERSION} | Engine: {self.engine.__class__.__name__}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        print(f"\n[统计] Total cases: {metrics.total_cases}")
        print(f"[统计] Blocked: {metrics.total_blocked}")
        print(f"[统计] Passed: {metrics.total_passed}")
        print(f"[统计] Data Missing: {metrics.total_data_missing}")
        
        print(f"\n[TP/FP]")
        print(f"  TP (True Positive): {metrics.total_tp}")
        print(f"  FP (False Positive): {metrics.total_fp}")
        print(f"  Regression: {metrics.total_regression}")
        
        print(f"\n[P0拦截率]")
        print(f"  {metrics.p0_interception_rate:.1f}%")
        
        print(f"\n[边界测试]")
        print(f"  {metrics.boundary_pass}/{metrics.boundary_total} passed")
        if metrics.boundary_total > 0:
            rate = metrics.boundary_pass / metrics.boundary_total * 100
            print(f"  Boundary pass rate: {rate:.1f}%")
        
        print(f"\n[详细结果]")
        for detail in metrics.details:
            status_icon = {"PASS": "PASS", "FAIL": "FAIL", "SKIP": "SKIP"}
            print(f"  {status_icon.get(detail['verdict'], '?')} {detail['case_id']:20s} "
                  f"expected={detail['expected']:15s} actual={detail['actual']:15s} "
                  f"rule={detail['actual_rule'] or '-'}")
        
        print("=" * 70)


# =============================================================================
# Section 5: Test Data Loader
# =============================================================================

def load_test_cases_from_csv(csv_path: str) -> List[MatchPair]:
    """
    Load test cases from a CSV file (V85 sim_sceneA/B format).
    
    CSV columns:
    source_type,case_id,template_id,indicator_name,matched_name,risk_id,
    risk_level,old_status,scene_action,rule_applied,new_status,tp_change,fp_change,notes
    """
    pairs = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pair = MatchPair(
                case_id=row.get("case_id", "").strip(),
                source_type=row.get("source_type", "").strip(),
                template_id=row.get("template_id", "").strip(),
                indicator_name=row.get("indicator_name", "").strip(),
                matched_name=row.get("matched_name", "").strip(),
                risk_id=row.get("risk_id", "").strip(),
                risk_level=row.get("risk_level", "").strip(),
                old_status=row.get("old_status", "").strip(),
                expected_new_status=row.get("new_status", "").strip(),
                expected_rule=row.get("rule_applied", "").strip(),
                notes=row.get("notes", "").strip(),
            )
            pairs.append(pair)
    return pairs


def load_boundary_testset(testset_path: str) -> List[MatchPair]:
    """
    Load boundary test cases from JSON testset file.
    """
    pairs = []
    with open(testset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for case in data.get("cases", []):
        pair = MatchPair(
            case_id=case["case_id"],
            source_type="boundary_test",
            template_id="N/A",
            indicator_name=case["indicator_name"],
            matched_name=case["matched_name"],
            risk_id=case.get("case_source", ""),
            risk_level=case.get("risk_level", "N/A"),
            old_status="N/A",
            expected_new_status="BLOCKED" if case.get("expected_blocked", False) else "PASS",
            expected_rule=case.get("expected_rule", ""),
            notes=case.get("description", ""),
        )
        pairs.append(pair)
    return pairs


# =============================================================================
# Section 6: PDF Data-Missing Detection (V86-P0-002)
# =============================================================================

class PDFDataMissingDetector:
    """
    V86-P0-002: PDF Template Data-Missing Detection.
    
    Detects cases where matched_name is empty/N/A, indicating PDF template
    data is missing. These cases cannot be evaluated by blacklist rules
    until upstream PDF data is fixed.
    
    This module:
    1. Identifies all data-missing cases
    2. Maps each to the intended rule that SHOULD trigger after fix
    3. Simulates the post-fix evaluation
    4. Reports which rules become functional after fix
    """
    
    # Known data-missing cases and their intended rules
    KNOWN_DATA_MISSING = {
        "RISK-010": {
            "template_id": "TPL-NI-008",
            "indicator_name": "中国电解镍净进口量",
            "intended_rule": "BL-022",
            "variety": "NI",
            "fix_description": "PDF模板matched_name为空，修复后镍进口→铜进口规则可触发",
        },
        "RISK-011": {
            "template_id": "TPL-SI-014",
            "indicator_name": "工业硅样本工厂库存(SMM)",
            "intended_rule": "BL-020",
            "variety": "SI",
            "fix_description": "PDF模板matched_name为空，修复后硅库存→苯乙烯库存规则可触发",
        },
        "RISK-013": {
            "template_id": "TPL-SI-019",
            "indicator_name": "工业硅供需平衡",
            "intended_rule": "BL-021",
            "variety": "SI",
            "fix_description": "PDF模板matched_name为空，修复后硅供需平衡→黄金供需平衡规则可触发",
        },
        "RISK-005": {
            "template_id": "TPL-LC-087",
            "indicator_name": "磷酸铁锂 电池 国内销量",
            "intended_rule": "BL-015",
            "variety": "LC",
            "fix_description": "PDF模板matched_name为空，修复后国内销量→出口规则可触发",
        },
    }
    
    def __init__(self, engine: V86RuleEngine):
        self.engine = engine
        self.detected_missing: List[Dict] = []
    
    def detect(self, pairs: List[MatchPair]) -> List[Dict]:
        """
        Detect all data-missing cases from a set of match pairs.
        
        Returns list of dicts with:
            - risk_id, indicator_name, matched_name, intended_rule, 
              status (DATA_MISSING / FIXED_SIMULATED), verdict
        """
        results = []
        for pair in pairs:
            result = self.engine.evaluate(pair.indicator_name, pair.matched_name)
            
            if result["result"] == "DATA_MISSING":
                # Check if this is a known data-missing case
                risk_id = pair.risk_id
                known = self.KNOWN_DATA_MISSING.get(risk_id)
                
                if known:
                    # Simulate what happens after data fix
                    simulated = self._simulate_post_fix(pair, known)
                    results.append({
                        "risk_id": risk_id,
                        "template_id": pair.template_id,
                        "indicator_name": pair.indicator_name,
                        "matched_name": pair.matched_name,
                        "intended_rule": known["intended_rule"],
                        "status": "DATA_MISSING",
                        "fix_description": known["fix_description"],
                        "post_fix_simulated": simulated,
                        "verdict": "DATA_MISSING - needs upstream fix",
                    })
                else:
                    results.append({
                        "risk_id": risk_id,
                        "template_id": pair.template_id,
                        "indicator_name": pair.indicator_name,
                        "matched_name": pair.matched_name,
                        "intended_rule": None,
                        "status": "DATA_MISSING",
                        "fix_description": "Unknown data-missing case",
                        "post_fix_simulated": None,
                        "verdict": "DATA_MISSING",
                    })
        
        self.detected_missing = results
        return results
    
    def _simulate_post_fix(self, pair: MatchPair, known: Dict) -> Dict:
        """
        Simulate what happens after PDF data fix.
        
        For known data-missing cases, we know what the matched_name
        should be after fix. This simulation is for reference only.
        """
        # Simulated post-fix matched names
        post_fix_matched = {
            "RISK-010": "中国海关:镍:净进口量:月度",
            "RISK-011": "苯乙烯库存:社会库存:月度",
            "RISK-013": "黄金供需平衡表:月度",
            "RISK-005": "中国海关:磷酸铁锂电池出口量:月度",
        }
        
        simulated_matched = post_fix_matched.get(pair.risk_id, "")
        
        if simulated_matched:
            result = self.engine.evaluate(pair.indicator_name, simulated_matched)
            return {
                "simulated_matched_name": simulated_matched,
                "simulated_result": result["result"],
                "simulated_rule": result["blocked_by"],
                "will_trigger": result["result"] == "BLOCKED",
            }
        
        return {"simulated_matched_name": None, "will_trigger": False}
    
    def print_report(self, results: List[Dict]):
        """Print data-missing detection report."""
        print("\n" + "=" * 70)
        print("V86-P0-002: PDF Data-Missing Detection Report")
        print("=" * 70)
        print(f"\nDetected {len(results)} data-missing cases:")
        
        for r in results:
            print(f"\n  Risk: {r['risk_id']}")
            print(f"    Template: {r['template_id']}")
            print(f"    Indicator: {r['indicator_name']}")
            print(f"    Matched: {r['matched_name']}")
            print(f"    Intended Rule: {r['intended_rule']}")
            print(f"    Fix Desc: {r['fix_description']}")
            
            if r.get("post_fix_simulated"):
                sim = r["post_fix_simulated"]
                print(f"    Post-Fix Simulation:")
                print(f"      Simulated matched: {sim.get('simulated_matched_name', 'N/A')}")
                print(f"      Simulated result: {sim.get('simulated_result', 'N/A')}")
                print(f"      Will trigger: {'YES' if sim.get('will_trigger') else 'NO'}")
            
            print(f"    Verdict: {r['verdict']}")
        
        print("\n" + "=" * 70)


# =============================================================================
# Section 7: Self-Test (Independent Unit Tests)
# =============================================================================

def run_self_test():
    """
    Run independent self-test of V86 P0 rule engine.
    
    Tests:
    1. BL-009a forward/reverse matching
    2. BL-026 cross-variety detection
    3. BL-012 Plan B variety-aware pre-filter
    4. PDF data-missing detection
    5. Boundary test cases
    6. Negative cases (should not trigger)
    """
    import unicodedata
    
    engine = V86RuleEngine(rules=create_v86_p0_rules())
    
    # Add complementarity rules (BL-009) and cross-variety rules (BL-018/018a)
    complement_rules = [
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
    ]
    engine._add_rules(complement_rules)
    
    runner = RegressionTestRunner(engine)
    
    test_pairs = []
    
    # =========================================================================
    # Test Group 1: BL-009a — 需求→利润 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL009A-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂 三元523需求",
        matched_name="SMM: 碳酸锂现金生产利润: 外购三元极片黑粉",
        risk_id="RISK-002",
        risk_level="P0",
        old_status="NOT_BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-009a",
    ))
    test_pairs.append(MatchPair(
        case_id="BL009A-002",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂需求总量",
        matched_name="碳酸锂冶炼利润（元/吨）",
        risk_id="RISK-002",
        risk_level="P0",
        old_status="NOT_BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-009a",
    ))
    test_pairs.append(MatchPair(
        case_id="BL009A-003",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂需求量（万吨）",
        matched_name="碳酸锂现金生产利润: 外购三元极片黑粉",
        risk_id="RISK-002",
        risk_level="P0",
        old_status="NOT_BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-009a",
    ))
    
    # =========================================================================
    # Test Group 2: BL-009 — 利润→需求 (should BLOCK, complement of BL-009a)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL009-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂利润（元/吨）",
        matched_name="碳酸锂三元523需求",
        risk_id="RISK-002",
        risk_level="P0",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-009",
    ))
    
    # =========================================================================
    # Test Group 3: BL-009a Safety — 同口径 (should PASS)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL009A-NEG-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂需求预测",
        matched_name="碳酸锂需求分析",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    test_pairs.append(MatchPair(
        case_id="BL009A-NEG-002",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂利润分析",
        matched_name="碳酸锂利润预测",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    test_pairs.append(MatchPair(
        case_id="BL009A-NEG-003",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂利润与需求分析",
        matched_name="碳酸锂利润与需求预测",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    
    # =========================================================================
    # Test Group 4: BL-026 — 库存天数跨品种 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL026-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="电解镍厂库存天数（天）",
        matched_name="碳酸锂工厂库存天数",
        risk_id="RISK-040",
        risk_level="P1",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-026",
    ))
    test_pairs.append(MatchPair(
        case_id="BL026-002",
        source_type="self_test",
        template_id="N/A",
        indicator_name="锡厂库存天数（天）",
        matched_name="碳酸锂工厂库存天数",
        risk_id="RISK-045",
        risk_level="P1",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-026",
    ))
    test_pairs.append(MatchPair(
        case_id="BL026-003",
        source_type="self_test",
        template_id="N/A",
        indicator_name="多晶硅工厂库存天数（天）",
        matched_name="碳酸锂工厂库存天数",
        risk_id="RISK-042",
        risk_level="P1",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-026",
    ))
    test_pairs.append(MatchPair(
        case_id="BL026-004",
        source_type="self_test",
        template_id="N/A",
        indicator_name="国内锌厂内库存天数（天）",
        matched_name="碳酸锂工厂库存天数",
        risk_id="RISK-050",
        risk_level="P1",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-026",
    ))
    
    # =========================================================================
    # Test Group 5: BL-026 Safety — 同品种同指标 (should PASS)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL026-NEG-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂工厂库存天数",
        matched_name="碳酸锂工厂库存天数",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    test_pairs.append(MatchPair(
        case_id="BL026-NEG-002",
        source_type="self_test",
        template_id="N/A",
        indicator_name="锡厂库存天数（天）",
        matched_name="锡厂库存天数（天）",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    
    # =========================================================================
    # Test Group 6: BL-012 Plan B — 库存天数→库存量 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL012B-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂工厂库存天数",
        matched_name="碳酸锂工厂库存量",
        risk_id="RISK-038",
        risk_level="P1",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-012",
    ))
    
    # =========================================================================
    # Test Group 7: BL-012 Plan B Safety — 同品种库存天数→库存天数 (should PASS)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL012B-NEG-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="碳酸锂工厂库存天数",
        matched_name="碳酸锂工厂库存天数",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    
    # =========================================================================
    # Test Group 8: PDF Data-Missing Cases
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="PDF-001",
        source_type="self_test",
        template_id="TPL-NI-008",
        indicator_name="中国电解镍净进口量",
        matched_name="N/A",
        risk_id="RISK-010",
        risk_level="P0",
        old_status="NOT_BLOCKED",
        expected_new_status="DATA_MISSING",
        expected_rule="BL-022",
    ))
    test_pairs.append(MatchPair(
        case_id="PDF-002",
        source_type="self_test",
        template_id="TPL-SI-014",
        indicator_name="工业硅样本工厂库存(SMM)",
        matched_name="N/A",
        risk_id="RISK-011",
        risk_level="P0",
        old_status="NOT_BLOCKED",
        expected_new_status="DATA_MISSING",
        expected_rule="BL-020",
    ))
    test_pairs.append(MatchPair(
        case_id="PDF-003",
        source_type="self_test",
        template_id="TPL-SI-019",
        indicator_name="工业硅供需平衡",
        matched_name="N/A",
        risk_id="RISK-013",
        risk_level="P0",
        old_status="NOT_BLOCKED",
        expected_new_status="DATA_MISSING",
        expected_rule="BL-021",
    ))
    
    # =========================================================================
    # Test Group 9: Cross-Variety Safety (should PASS - same variety)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="CROSS-NEG-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="COMEX镍持仓量（手）",
        matched_name="COMEX：镍：主力合约：持仓量（日）",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    test_pairs.append(MatchPair(
        case_id="CROSS-NEG-002",
        source_type="self_test",
        template_id="N/A",
        indicator_name="LME锡库存（吨）",
        matched_name="LME：锡：库存：中国（日）",
        risk_id="SAFE",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    
    # =========================================================================
    # Test Group 10: Cross-Variety Positive (should BLOCK - different variety)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="CROSS-POS-001",
        source_type="self_test",
        template_id="N/A",
        indicator_name="COMEX镍持仓量（手）",
        matched_name="COMEX：铜：主力合约：持仓量（日）",
        risk_id="SAFE",
        risk_level="P0",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-022",
    ))
    test_pairs.append(MatchPair(
        case_id="CROSS-POS-002",
        source_type="self_test",
        template_id="N/A",
        indicator_name="LME锡库存（吨）",
        matched_name="LME：镍：注册仓单（日）",
        risk_id="SAFE",
        risk_level="P0",
        old_status="BLOCKED",
        expected_new_status="BLOCKED",
        expected_rule="BL-018; BL-018a",
    ))
    
    # =========================================================================
    # Run tests
    # =========================================================================
    metrics = runner.run_cases(test_pairs)
    runner.print_summary(metrics)
    
    # =========================================================================
    # PDF Data-Missing Detection Report
    # =========================================================================
    detector = PDFDataMissingDetector(engine)
    detector_results = detector.detect(test_pairs)
    detector.print_report(detector_results)
    
    # =========================================================================
    # Return overall result
    # =========================================================================
    total = len(test_pairs)
    passed = sum(1 for p in test_pairs if p.verdict == "PASS")
    failed = sum(1 for p in test_pairs if p.verdict == "FAIL")
    skipped = sum(1 for p in test_pairs if p.verdict == "SKIP")
    
    overall_pass = failed == 0
    
    print(f"\n{'='*70}")
    print(f"SELF-TEST RESULT: {'PASS' if overall_pass else 'FAIL'}")
    print(f"  Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print(f"  P0 Interception Rate: {metrics.p0_interception_rate:.1f}%")
    print(f"  Boundary Pass: {metrics.boundary_pass}/{metrics.boundary_total}")
    print(f"{'='*70}")
    
    return overall_pass


# =============================================================================
# Section 8: CLI Entry Point
# =============================================================================

def main():
    """CLI entry point for V86 P0 rule prototype."""
    parser = argparse.ArgumentParser(
        description="V86 P0 Rule Engine Prototype",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run self-test
  python v86_p0_rule_prototype.py --self-test

  # Run with V85 CSV data
  python v86_p0_rule_prototype.py --csv path/to/sim_sceneA_result.csv

  # Run with boundary testset
  python v86_p0_rule_prototype.py --testset path/to/blacklist_boundary_testset.json

  # Load V85 blacklist and evaluate
  python v86_p0_rule_prototype.py --blacklist path/to/semantic_blacklist_v85_final.json

  # List all rules
  python v86_p0_rule_prototype.py --list-rules
        """,
    )
    parser.add_argument("--self-test", action="store_true",
                        help="Run built-in self-test suite")
    parser.add_argument("--csv", type=str,
                        help="Path to CSV file with test cases")
    parser.add_argument("--testset", type=str,
                        help="Path to JSON boundary testset")
    parser.add_argument("--blacklist", type=str,
                        help="Path to V85 blacklist JSON")
    parser.add_argument("--list-rules", action="store_true",
                        help="List all V86 P0 rules")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose output")
    parser.add_argument("--version", action="version", version=VERSION)
    
    args = parser.parse_args()
    
    # Self-test mode
    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    # List rules mode
    if args.list_rules:
        rules = create_v86_p0_rules()
        print(f"V86 P0 Rule Set ({VERSION})")
        print("=" * 60)
        for rule in rules:
            marker = " [V86-P0]" if rule.is_v86_p0 else ""
            extra = ""
            if rule.variety_aware:
                extra += " [variety-aware]"
            if rule.extra_filter:
                extra += f" [filter:{rule.extra_filter}]"
            print(f"  {rule.rule_id:10s} | {rule.name:30s} | {rule.severity.value} | {len(rule.left_patterns)}L/{len(rule.right_patterns)}R{marker}{extra}")
        print(f"\nTotal: {len(rules)} rules")
        return
    
    # Build engine
    engine = V86RuleEngine(rules=create_v86_p0_rules())
    
    # Also load V85 blacklist if provided
    if args.blacklist:
        if os.path.exists(args.blacklist):
            count = engine.load_rules_from_json(args.blacklist)
            print(f"Loaded {count} rules from {args.blacklist}")
        else:
            print(f"Error: File not found: {args.blacklist}")
            sys.exit(1)
    
    # Add BL-009 for complementarity
    bl009 = BlacklistRule(
        rule_id="BL-009",
        name="利润与需求互斥",
        category="经济口径",
        severity=RuleSeverity.P0,
        left_patterns=["利润", "盈利", "盈亏", "毛利"],
        right_patterns=["需求", "需求量", "需求侧"],
        status=RuleStatus.ACTIVE,
    )
    engine._add_rules([bl009])
    
    runner = RegressionTestRunner(engine)
    
    # Load test cases
    pairs = []
    if args.csv:
        if os.path.exists(args.csv):
            csv_pairs = load_test_cases_from_csv(args.csv)
            pairs.extend(csv_pairs)
            print(f"Loaded {len(csv_pairs)} cases from CSV")
        else:
            print(f"Error: CSV file not found: {args.csv}")
            sys.exit(1)
    
    if args.testset:
        if os.path.exists(args.testset):
            test_pairs = load_boundary_testset(args.testset)
            pairs.extend(test_pairs)
            print(f"Loaded {len(test_pairs)} cases from testset")
        else:
            print(f"Error: Testset file not found: {args.testset}")
            sys.exit(1)
    
    if not pairs:
        print("No test cases loaded. Use --self-test, --csv, or --testset.")
        print("Try: python v86_p0_rule_prototype.py --self-test")
        sys.exit(1)
    
    # Run tests
    metrics = runner.run_cases(pairs)
    runner.print_summary(metrics)
    
    # PDF Data-Missing Detection
    detector = PDFDataMissingDetector(engine)
    detector_results = detector.detect(pairs)
    if detector_results:
        detector.print_report(detector_results)
    
    # Exit code
    failed = sum(1 for d in metrics.details if d["verdict"] == "FAIL")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
