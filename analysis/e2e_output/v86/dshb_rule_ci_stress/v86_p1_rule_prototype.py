#!/usr/bin/env python3
"""
V86 P1 Rule Engine Prototype
=============================
任务: DSHB_V86_RULE_ENGINE_STRESS_TEST_AND_CI_PIPELINE_PROTOTYPE · T2.3
分支: feature/v85-chart-template
基线: feature/v85-chart-template commit:128275a (V86 P0规则原型)

P1必做项实现:
  1. 跨品种风险规则扩展 (BL-027~BL-038, 新增12条跨品种规则)
  2. 别名映射一致性校验 (AliasMappingValidator)
  3. 增强容错 (空输入/损坏数据/超大文本/非法别名处理)

设计原则:
  - 完全独立于V85生产逻辑，不导入/不修改V85核心文件
  - 继承V86 P0引擎架构，扩展P1能力
  - 可独立单元测试 (python v86_p1_rule_prototype.py --self-test)
  - 不调用zhiji API
  - 不依赖外部网络/服务

Author: DSHB Agent
Version: v86.1-alpha-proto
Date: 2026-10-01
"""

import json
import csv
import os
import sys
import argparse
import unicodedata
import time
import traceback
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


# =============================================================================
# Section 0: Version & Constants
# =============================================================================

VERSION = "v86.1-alpha-proto"
TASK_ID = "DSHB_V86_RULE_ENGINE_STRESS_TEST_AND_CI_PIPELINE_PROTOTYPE"
BRANCH = "feature/v85-chart-template"
BASE_COMMIT = "128275a"

# Maximum input sizes (fault tolerance bounds)
MAX_INDICATOR_LENGTH = 2000
MAX_MATCHED_LENGTH = 2000
MAX_ALIASES_PER_INDICATOR = 50

# Variety keywords (extended for P1)
VARIETY_KEYWORDS = {
    "LI": ["碳酸锂", "锂", "盐湖提锂", "锂矿", "锂电池", "磷酸铁锂", "三元", "三元锂"],
    "NI": ["镍", "电解镍", "精炼镍", "镍精矿", "高冰镍", "镍铁", "镍板", "镍豆"],
    "SI": ["硅", "工业硅", "金属硅", "多晶硅", "硅矿"],
    "SN": ["锡", "锡锭", "锡矿", "焊锡", "锡精矿"],
    "ZN": ["锌", "锌锭", "锌矿"],
    "LC": ["碳酸锂", "磷酸铁锂", "三元", "锂电池"],
    "CU": ["铜", "电解铜", "铜锭", "铜矿", "铜杆", "铜箔", "铜管"],
    "AL": ["铝", "电解铝", "铝锭", "铝棒", "铝材"],
    "PB": ["铅", "电解铅", "铅锭"],
    "AO": ["氧化铝", "氧化铝库存", "氧化铝产量"],
    "CO": ["钴", "钴矿", "钴盐", "硫酸钴", "钴粉"],
    "SS": ["不锈钢", "不锈钢板", "不锈钢管", "铬铁", "高铬"],
    "OE": ["原油", "WTI原油", "布伦特原油", "石油"],
    "NG": ["天然气", "LNG", "页岩气"],
    "FE": ["铁矿石", "铁矿", "铁精粉", "钢材", "螺纹钢", "热卷", "冷轧", "热轧"],
    "ST": ["苯乙烯", "苯乙烯库存"],
    "GO": ["黄金", "金价", "XAU", "伦敦金"],
    "NI_2": ["镍", "镍矿"],  # Alias for BL-022/027 etc
    "SN_2": ["锡", "锡矿"],
    "AL_2": ["铝", "电解铝"],
}

# Alias consistency categories (for P1 alias validation)
ALIAS_CONFLICT_TYPES = {
    "EXACT_DUPLICATE": "完全重复别名",
    "CANONICAL_MISMATCH": "规范名不一致",
    "VARIETY_MISMATCH": "品种不一致",
    "SEMANTIC_DIVERGENCE": "语义分歧",
    "AMBIGUOUS_MAPPING": "歧义映射(多对一)",
}


# =============================================================================
# Section 1: Error Code Definitions (aligned with E backend)
# =============================================================================

class RuleErrorCode(Enum):
    """Standardized error codes aligned with E backend task API."""
    OK = "OK"
    # Rule engine errors
    RULE_ENGINE_LOAD_FAILED = "RULE_ENGINE_LOAD_FAILED"
    RULE_NOT_FOUND = "RULE_NOT_FOUND"
    RULE_CONFLICT = "RULE_CONFLICT"
    PATTERN_EMPTY = "PATTERN_EMPTY"
    VARIETY_DETECT_FAILED = "VARIETY_DETECT_FAILED"
    BIDIRECTIONAL_CHECK_ERROR = "BIDIRECTIONAL_CHECK_ERROR"
    # Input validation errors
    EMPTY_INDICATOR = "EMPTY_INDICATOR"
    EMPTY_MATCHED = "EMPTY_MATCHED"
    INDICATOR_TOO_LONG = "INDICATOR_TOO_LONG"
    MATCHED_TOO_LONG = "MATCHED_TOO_LONG"
    INVALID_ALIAS_FORMAT = "INVALID_ALIAS_FORMAT"
    ALIAS_MAP_NOT_FOUND = "ALIAS_MAP_NOT_FOUND"
    ALIAS_MAP_CORRUPT = "ALIAS_MAP_CORRUPT"
    CSV_PARSE_ERROR = "CSV_PARSE_ERROR"
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    # System errors
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATA_MISSING = "DATA_MISSING"  # Not an error, special status


# =============================================================================
# Section 2: Data Models (extends P0)
# =============================================================================

class RuleSeverity(Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class RuleStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DEPRECATED = "deprecated"


class MatchResult(Enum):
    BLOCKED = "BLOCKED"
    PASSED = "PASSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    DATA_MISSING = "DATA_MISSING"


@dataclass
class BlacklistRule:
    """
    Semantic blacklist rule definition (extended from P0).
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
    extra_filter: Optional[str] = None
    variety_aware: bool = False
    parent_rule: Optional[str] = None
    is_v86_p0: bool = False
    is_v86_p1: bool = False


@dataclass
class AliasEntry:
    """
    Alias mapping entry for consistency validation.
    Maps an alias (chart name / indicator name) to its canonical name.
    """
    alias: str
    canonical: str
    variety: str = ""
    category: str = ""
    source: str = ""
    confidence: float = 1.0


@dataclass
class AliasConflict:
    """
    An alias consistency conflict found by the validator.
    """
    conflict_type: str
    entries: List[AliasEntry]
    description: str
    severity: str = "WARN"
    suggestion: str = ""


@dataclass
class MatchPair:
    """
    A pair of indicator_name and matched_name to evaluate.
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
    verdict: str = ""


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
    total_errors: int = 0
    boundary_pass: int = 0
    boundary_total: int = 0
    p0_interception_rate: float = 0.0
    p1_interception_rate: float = 0.0
    details: List[Dict] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single benchmark run."""
    total_cases: int = 0
    total_blocked: int = 0
    total_passed: int = 0
    total_errors: int = 0
    elapsed_ms: float = 0.0
    avg_ms_per_case: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    max_ms: float = 0.0
    peak_memory_mb: float = 0.0
    cases_per_sec: float = 0.0


@dataclass
class StressTestResult:
    """Aggregated stress test results."""
    scenario_name: str
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    errors: List[Dict] = field(default_factory=list)
    timestamp: str = ""
    is_passed: bool = True
    notes: str = ""


# =============================================================================
# Section 3: Fault-Tolerant Input Validator
# =============================================================================

class InputValidator:
    """
    Validates and sanitizes inputs to the rule engine.
    Handles edge cases: empty strings, overly long text, corrupted data.
    """
    
    def __init__(self, max_indicator_length: int = MAX_INDICATOR_LENGTH,
                 max_matched_length: int = MAX_MATCHED_LENGTH):
        self.max_indicator_length = max_indicator_length
        self.max_matched_length = max_matched_length
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text: NFKC normalization."""
        return unicodedata.normalize('NFKC', text).strip()

    def validate_indicator(self, indicator_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate indicator_name.
        
        Returns:
            (is_valid, sanitized_value, error_code)
        """
        if indicator_name is None:
            return False, "", RuleErrorCode.EMPTY_INDICATOR.value
        
        if not isinstance(indicator_name, str):
            indicator_name = str(indicator_name)
        
        if len(indicator_name.strip()) == 0:
            return False, "", RuleErrorCode.EMPTY_INDICATOR.value
        
        indicator_name = indicator_name.strip()
        
        if len(indicator_name) > self.max_indicator_length:
            return False, "", RuleErrorCode.INDICATOR_TOO_LONG.value
        
        # Clean control characters
        indicator_name = ''.join(c for c in indicator_name if c == '\n' or c == '\t' or c == '\r' or ord(c) >= 32)
        
        return True, indicator_name, None
    
    def validate_matched(self, matched_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate matched_name.
        
        Returns:
            (is_valid, sanitized_value, error_code)
        """
        if matched_name is None:
            return True, "", None  # matched_name can be empty (DATA_MISSING)
        
        if not isinstance(matched_name, str):
            matched_name = str(matched_name)
        
        matched_name = matched_name.strip()
        
        if len(matched_name) > self.max_matched_length:
            return False, "", RuleErrorCode.MATCHED_TOO_LONG.value
        
        return True, matched_name, None
    
    def validate_alias_map(self, alias_map: dict) -> Tuple[bool, List[AliasEntry], Optional[str]]:
        """
        Validate an alias mapping dictionary.
        
        Expected format:
            {
                "alias": "canonical_name",
                ...
            }
        or list of dicts:
            [
                {"alias": "...", "canonical": "...", "variety": "..."},
                ...
            ]
        """
        entries = []
        
        if isinstance(alias_map, dict):
            for alias, canonical in alias_map.items():
                if not isinstance(alias, str) or not isinstance(canonical, str):
                    return False, [], RuleErrorCode.INVALID_ALIAS_FORMAT.value
                if len(alias) == 0 or len(canonical) == 0:
                    return False, [], RuleErrorCode.INVALID_ALIAS_FORMAT.value
                entries.append(AliasEntry(alias=alias, canonical=canonical))
        
        elif isinstance(alias_map, list):
            for item in alias_map:
                if not isinstance(item, dict):
                    return False, [], RuleErrorCode.INVALID_ALIAS_FORMAT.value
                alias = item.get("alias", "")
                canonical = item.get("canonical", "")
                variety = item.get("variety", "")
                if not isinstance(alias, str) or not isinstance(canonical, str):
                    return False, [], RuleErrorCode.INVALID_ALIAS_FORMAT.value
                if len(alias) == 0 or len(canonical) == 0:
                    return False, [], RuleErrorCode.INVALID_ALIAS_FORMAT.value
                entries.append(AliasEntry(alias=alias, canonical=canonical, variety=variety))
        
        else:
            return False, [], RuleErrorCode.INVALID_ALIAS_FORMAT.value
        
        return True, entries, None


# =============================================================================
# Section 4: P1 Rule Engine (extends P0)
# =============================================================================

class V86P1RuleEngine:
    """
    V86 P1 Rule Engine Prototype.
    
    Extends the P0 engine with:
    - Cross-variety risk rules (BL-027~BL-038)
    - Alias mapping consistency validation
    - Enhanced fault tolerance with standardized error codes
    
    Usage:
        engine = V86P1RuleEngine()
        engine.load_p1_rules()
        result = engine.evaluate(indicator_name, matched_name)
    """
    
    def __init__(self, rules: Optional[List[BlacklistRule]] = None):
        self.rules: List[BlacklistRule] = rules or []
        self._rule_map: Dict[str, BlacklistRule] = {}
        self._variant_index: Dict[str, List[BlacklistRule]] = {}
        self._validator = InputValidator()
        self._error_history: List[Dict] = []
        self._build_indexes()
    
    def _build_indexes(self):
        """Build pattern index for fast lookup."""
        self._rule_map = {}
        self._variant_index = {}
        for rule in self.rules:
            self._rule_map[rule.rule_id] = rule
            for pat in rule.left_patterns + rule.right_patterns:
                norm_pat = self._normalize(pat)
                if norm_pat not in self._variant_index:
                    self._variant_index[norm_pat] = []
                if rule not in self._variant_index[norm_pat]:
                    self._variant_index[norm_pat].append(rule)
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for matching: NFKC normalization."""
        return unicodedata.normalize('NFKC', text).strip()
    
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
        
        Returns:
            Dict with:
                - result: BLOCKED / PASSED / NOT_APPLICABLE / DATA_MISSING
                - triggered_rules: List of rule IDs that triggered
                - blocked_by: Primary blocking rule ID
                - severity: Highest severity among triggered rules
                - error_code: Standardized error code
                - notes: Additional information
        """
        start_time = time.time()
        
        # Step 1: Validate inputs (fault tolerance)
        valid_ind, ind_val, ind_err = self._validator.validate_indicator(indicator_name)
        if not valid_ind:
            return self._error_response(ind_err, f"indicator_name validation failed: {ind_err}")
        
        valid_mtd, mtd_val, mtd_err = self._validator.validate_matched(matched_name)
        if not valid_mtd:
            return self._error_response(mtd_err, f"matched_name validation failed: {mtd_err}")
        
        # Step 2: DATA_MISSING detection (V86-P0-002)
        if mtd_val in ("N/A", "", "（工作表记录）", "N/A（工作表记录）"):
            return {
                "result": MatchResult.DATA_MISSING.value,
                "triggered_rules": [],
                "blocked_by": None,
                "severity": None,
                "error_code": RuleErrorCode.DATA_MISSING.value,
                "notes": "matched_name is empty/N/A - PDF data missing, rule cannot trigger",
                "pdf_fix_needed": True,
                "latency_ms": round((time.time() - start_time) * 1000, 3),
            }
        
        # Step 3: Evaluate against all rules
        try:
            triggered_rules = []
            highest_severity = None
            blocked_by = None
            
            for rule in self.rules:
                if rule.status.value != "active":
                    continue
                
                # BL-012 Plan B: variety-aware pre-filter
                if rule.variety_aware:
                    variety_ind = self._detect_variety(ind_val)
                    variety_match = self._detect_variety(mtd_val)
                    if variety_hint:
                        variety_match = variety_hint
                    if ("库存天数" in ind_val and "库存天数" in mtd_val
                            and variety_ind == variety_match):
                        continue
                
                # Check pattern matching
                left_match = self._pattern_match(ind_val, rule.left_patterns)
                right_match = self._pattern_match(mtd_val, rule.right_patterns)
                
                # Bidirectional containment check (only when left != right)
                left_set = set(rule.left_patterns)
                right_set = set(rule.right_patterns)
                if left_set != right_set:
                    indicator_has_right = self._pattern_match(ind_val, rule.right_patterns)
                    matched_has_left = self._pattern_match(mtd_val, rule.left_patterns)
                    if indicator_has_right and matched_has_left:
                        continue
                
                if left_match and right_match:
                    # Apply extra filter
                    if rule.extra_filter == "variety_mismatch":
                        variety_ind = self._detect_variety(ind_val)
                        variety_match = self._detect_variety(mtd_val)
                        if variety_hint:
                            variety_match = variety_hint
                        if variety_ind == variety_match:
                            continue
                    
                    triggered_rules.append(rule.rule_id)
                    
                    sev_order = {"P0": 0, "P1": 1, "P2": 2}
                    rule_sev = sev_order.get(rule.severity.value, 3)
                    if highest_severity is None or rule_sev < sev_order.get(highest_severity.value, 3):
                        highest_severity = rule.severity
                    
                    if blocked_by is None:
                        blocked_by = rule.rule_id
            
            latency_ms = round((time.time() - start_time) * 1000, 3)
            
            if triggered_rules:
                return {
                    "result": MatchResult.BLOCKED.value,
                    "triggered_rules": triggered_rules,
                    "blocked_by": blocked_by,
                    "severity": highest_severity.value if highest_severity else None,
                    "error_code": RuleErrorCode.OK.value,
                    "notes": f"Blocked by: {', '.join(triggered_rules)}",
                    "pdf_fix_needed": False,
                    "latency_ms": latency_ms,
                }
            else:
                return {
                    "result": MatchResult.PASSED.value,
                    "triggered_rules": [],
                    "blocked_by": None,
                    "severity": None,
                    "error_code": RuleErrorCode.OK.value,
                    "notes": "No rules triggered",
                    "pdf_fix_needed": False,
                    "latency_ms": latency_ms,
                }
        
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 3)
            return self._error_response(
                RuleErrorCode.INTERNAL_ERROR.value,
                f"Internal error during evaluation: {str(e)}",
                latency_ms=latency_ms,
            )
    
    def _error_response(self, error_code: str, message: str, latency_ms: float = 0.0) -> Dict:
        """
        Build a standardized error response.
        Engine never crashes — always returns a dict.
        """
        error_entry = {
            "error_code": error_code,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "stack_trace": traceback.format_exc() if error_code == RuleErrorCode.INTERNAL_ERROR.value else "",
        }
        self._error_history.append(error_entry)
        
        return {
            "result": MatchResult.NOT_APPLICABLE.value,
            "triggered_rules": [],
            "blocked_by": None,
            "severity": None,
            "error_code": error_code,
            "error_message": message,
            "notes": f"Error: {error_code} - {message}",
            "pdf_fix_needed": False,
            "latency_ms": latency_ms,
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
        Returns variety code or None.
        """
        if not text:
            return None
        text_norm = unicodedata.normalize('NFKC', text)
        for variety, keywords in VARIETY_KEYWORDS.items():
            for kw in keywords:
                kw_norm = unicodedata.normalize('NFKC', kw)
                if kw_norm in text_norm:
                    return variety
        return None
    
    def get_error_history(self) -> List[Dict]:
        """Get the error history for diagnostics."""
        return list(self._error_history)
    
    def clear_error_history(self):
        """Clear the error history."""
        self._error_history = []
    
    def get_rule(self, rule_id: str) -> Optional[BlacklistRule]:
        """Get a rule by ID."""
        return self._rule_map.get(rule_id)
    
    def get_all_rule_ids(self) -> List[str]:
        """Get all rule IDs."""
        return [r.rule_id for r in self.rules]
    
    def get_p0_rules(self) -> List[BlacklistRule]:
        """Get all P0 rules."""
        return [r for r in self.rules if getattr(r, 'is_v86_p0', False)]
    
    def get_p1_rules(self) -> List[BlacklistRule]:
        """Get all P1 rules."""
        return [r for r in self.rules if getattr(r, 'is_v86_p1', False)]
    
    def get_rule_count(self) -> int:
        """Get total rule count."""
        return len(self.rules)
    
    def load_rules_from_json(self, json_path: str) -> int:
        """Load rules from a JSON file."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return 0
        
        rules = []
        for rule_data in data.get("rules", []):
            try:
                severity = RuleSeverity(rule_data.get("severity", "P1"))
                rule_status = RuleStatus(rule_data.get("status", "active"))
                rule = BlacklistRule(
                    rule_id=rule_data["rule_id"],
                    name=rule_data.get("name", ""),
                    category=rule_data.get("category", ""),
                    severity=severity,
                    left_patterns=rule_data.get("left_patterns", []),
                    right_patterns=rule_data.get("right_patterns", []),
                    description=rule_data.get("description", ""),
                    rationale=rule_data.get("rationale", ""),
                    status=rule_status,
                    extra_filter=rule_data.get("extra_filter"),
                    variety_aware=rule_data.get("variety_aware", False),
                    parent_rule=rule_data.get("parent_rule"),
                    is_v86_p0=rule_data.get("is_v86_p0", False),
                    is_v86_p1=rule_data.get("is_v86_p1", False),
                )
                rules.append(rule)
            except (ValueError, KeyError):
                continue
        
        self.rules = rules
        self._build_indexes()
        return len(rules)


# =============================================================================
# Section 5: P1 Cross-Variety Rules (BL-027 ~ BL-038)
# =============================================================================

def create_v86_p1_rules() -> List[BlacklistRule]:
    """
    Create the V86 P1 cross-variety rule set.
    
    These rules extend the P0 cross-variety coverage (BL-018, BL-018a, BL-022, BL-020, BL-021)
    to cover additional commodity pairs that were identified in V85 boundary testing
    but not addressed in P0.
    """
    rules = []
    
    # =========================================================================
    # BL-027: 铝↔铜跨品种禁止 (aluminum vs copper)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-027",
        name="铝与铜跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["铝", "电解铝", "铝锭", "铝棒", "铝材", "氧化铝"],
        right_patterns=["铜", "电解铜", "铜锭", "铜矿", "铜杆", "铜箔", "铜管"],
        description="铝与铜是不同品种，不可互相匹配。BL-027覆盖铝↔铜跨品种场景。",
        rationale="V85边界测试发现铝库存与铜库存的误匹配。BL-027补齐P0未覆盖的铝↔铜品种对。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-028: 铅↔锌跨品种禁止 (lead vs zinc)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-028",
        name="铅与锌跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["铅", "电解铅", "铅锭"],
        right_patterns=["锌", "锌锭", "锌矿"],
        description="铅与锌是不同品种，不可互相匹配。BL-028覆盖铅↔锌跨品种场景。",
        rationale="铅锌同为有色金属，但库存口径和价格信号完全不同，需要独立规则。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-029: 氧化铝↔铝跨品种禁止 (aluminum oxide vs aluminum)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-029",
        name="氧化铝与铝跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["氧化铝"],
        right_patterns=["电解铝", "铝锭", "铝棒", "铝材", "铝"],
        description="氧化铝与电解铝是不同加工阶段的品种，不可互相匹配。",
        rationale="氧化铝是铝的上游原料，库存口径和产业链位置不同，需要独立规则。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-030: 碳酸锂↔磷酸铁锂跨品种禁止 (lithium carbonate vs LFP)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-030",
        name="碳酸锂与磷酸铁锂跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["碳酸锂", "锂"],
        right_patterns=["磷酸铁锂", "LFP", "三元"],
        description="碳酸锂与磷酸铁锂/三元是不同细分品种，不可互相匹配。",
        rationale="碳酸锂是锂盐，磷酸铁锂是正极材料，产业链位置和库存口径不同。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-031: 钴↔锂跨品种禁止 (cobalt vs lithium)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-031",
        name="钴与锂跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["钴", "钴矿", "钴盐", "硫酸钴", "钴粉"],
        right_patterns=["碳酸锂", "锂", "磷酸铁锂"],
        description="钴与锂是不同金属，不可互相匹配。BL-031覆盖钴↔锂跨品种场景。",
        rationale="钴和锂均用于新能源电池但属不同金属，库存和价格逻辑独立。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-032: 不锈钢↔铜跨品种禁止 (stainless steel vs copper)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-032",
        name="不锈钢与铜跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["不锈钢", "不锈钢板", "不锈钢管", "铬铁", "高铬"],
        right_patterns=["铜", "电解铜", "铜锭"],
        description="不锈钢与铜是不同品种，不可互相匹配。",
        rationale="不锈钢和铜虽同为金属但产业链位置完全不同。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-033: 原油↔天然气跨品种禁止 (crude oil vs natural gas)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-033",
        name="原油与天然气跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["原油", "WTI原油", "布伦特原油", "石油"],
        right_patterns=["天然气", "LNG", "页岩气"],
        description="原油与天然气是不同能源品种，不可互相匹配。",
        rationale="原油和天然气虽同为能源但价格逻辑和库存管理完全不同。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-034: 铁矿石↔钢材跨品种禁止 (iron ore vs steel)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-034",
        name="铁矿石与钢材跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["铁矿石", "铁矿", "铁精粉"],
        right_patterns=["钢材", "螺纹钢", "热卷", "冷轧", "热轧"],
        description="铁矿石与钢材是上下游不同阶段品种，不可互相匹配。",
        rationale="铁矿石是钢材的上游原料，产业链位置不同，库存口径完全不同。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-035: 苯乙烯↔铜跨品种禁止 (styrene vs copper)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-035",
        name="苯乙烯与铜跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["苯乙烯"],
        right_patterns=["铜", "电解铜", "铜锭"],
        description="苯乙烯与铜是不同品种，不可互相匹配。",
        rationale="苯乙烯是化工品，铜是有色金属，产业链完全不同。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-036: 黄金↔有色金属跨品种禁止 (gold vs non-ferrous metals)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-036",
        name="黄金与有色金属跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["黄金", "金价", "XAU", "伦敦金"],
        right_patterns=["镍", "电解镍", "精炼镍", "铜", "电解铜", "铝", "电解铝", "铅", "锌"],
        description="黄金与有色金属是不同资产类别，不可互相匹配。",
        rationale="黄金是贵金属，有色金属是工业金属，价格逻辑完全不同。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-037: 锌↔铅跨品种禁止 (zinc vs lead) - 方向反转补充
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-037",
        name="锌与铅跨品种禁止（方向补充）",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["锌", "锌锭", "锌矿"],
        right_patterns=["铅", "电解铅", "铅锭"],
        description="锌与铅跨品种禁止的方向补充。BL-028覆盖铅→锌，BL-037覆盖锌→铅。",
        rationale="BL-028为铅→锌方向，BL-037补齐锌→铅方向的覆盖。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    # =========================================================================
    # BL-038: 镍↔不锈钢跨品种禁止 (nickel vs stainless steel)
    # =========================================================================
    rules.append(BlacklistRule(
        rule_id="BL-038",
        name="镍与不锈钢跨品种禁止",
        category="品种口径",
        severity=RuleSeverity.P1,
        left_patterns=["镍", "电解镍", "精炼镍", "镍矿"],
        right_patterns=["不锈钢", "不锈钢板", "不锈钢管"],
        description="镍与不锈钢是不同品种，不可互相匹配。",
        rationale="镍是不锈钢的原料但库存口径不同，产业链位置不同。",
        status=RuleStatus.ACTIVE,
        is_v86_p1=True,
    ))
    
    return rules


# =============================================================================
# Section 6: Alias Mapping Consistency Validator
# =============================================================================

class AliasMappingValidator:
    """
    Validates alias mapping consistency.
    
    Checks:
    1. EXACT_DUPLICATE: same alias mapped to identical canonical
    2. CANONICAL_MISMATCH: same alias mapped to different canonicals
    3. VARIETY_MISMATCH: alias entries with inconsistent variety tags
    4. AMBIGUOUS_MAPPING: multiple aliases mapping to same canonical
    5. SEMANTIC_DIVERGENCE: aliases that are semantically different but map to same canonical
    
    Usage:
        validator = AliasMappingValidator()
        conflicts = validator.validate(alias_entries)
    """
    
    def __init__(self, validator: Optional[InputValidator] = None):
        self._validator = validator or InputValidator()
    
    def validate(self, alias_entries: List[AliasEntry]) -> List[AliasConflict]:
        """
        Validate a list of alias entries for consistency conflicts.
        
        Returns list of AliasConflict objects.
        """
        conflicts = []
        
        if not alias_entries:
            return conflicts
        
        # Group by alias
        alias_groups = {}
        for entry in alias_entries:
            key = self._validator._normalize(entry.alias)
            if key not in alias_groups:
                alias_groups[key] = []
            alias_groups[key].append(entry)
        
        # Check 1: EXACT_DUPLICATE (same alias, same canonical, same variety)
        for alias_key, entries in alias_groups.items():
            if len(entries) > 1:
                # Check for exact duplicates
                unique_canonicals = set()
                unique_varieties = set()
                for e in entries:
                    unique_canonicals.add(e.canonical)
                    unique_varieties.add(e.variety)
                
                if len(unique_canonicals) == 1 and len(unique_varieties) == 1:
                    # Exact duplicates - not a conflict, just redundancy
                    continue
                
                # Check 2: CANONICAL_MISMATCH (same alias, different canonicals)
                if len(unique_canonicals) > 1:
                    conflicts.append(AliasConflict(
                        conflict_type=ALIAS_CONFLICT_TYPES["CANONICAL_MISMATCH"],
                        entries=entries,
                        description=f"Alias '{alias_key}' maps to {len(unique_canonicals)} different canonicals: {unique_canonicals}",
                        severity="ERROR",
                        suggestion="Merge or disambiguate canonical mappings",
                    ))
                elif len(unique_varieties) > 1:
                    # Check 3: VARIETY_MISMATCH
                    conflicts.append(AliasConflict(
                        conflict_type=ALIAS_CONFLICT_TYPES["VARIETY_MISMATCH"],
                        entries=entries,
                        description=f"Alias '{alias_key}' has inconsistent variety tags: {unique_varieties}",
                        severity="WARN",
                        suggestion="Standardize variety tags for this alias",
                    ))
        
        # Check 4: AMBIGUOUS_MAPPING (multiple aliases → same canonical)
        canonical_groups = {}
        for entry in alias_entries:
            key = self._validator._normalize(entry.canonical)
            if key not in canonical_groups:
                canonical_groups[key] = []
            canonical_groups[key].append(entry)
        
        for canonical_key, entries in canonical_groups.items():
            unique_aliases = set(self._validator._normalize(e.alias) for e in entries)
            if len(unique_aliases) > 1:
                # Multiple aliases mapping to same canonical - may be intentional
                # Flag only if semantic divergence detected
                conflicts.append(AliasConflict(
                    conflict_type=ALIAS_CONFLICT_TYPES["AMBIGUOUS_MAPPING"],
                    entries=entries,
                    description=f"Canonical '{canonical_key}' has {len(unique_aliases)} aliases: {unique_aliases}",
                    severity="INFO",
                    suggestion="Review if all aliases are truly equivalent",
                ))
        
        # Check 5: SEMANTIC_DIVERGENCE (aliases that are very different but map to same canonical)
        for canonical_key, entries in canonical_groups.items():
            if len(entries) > 1:
                # Check pairwise semantic distance
                for i in range(len(entries)):
                    for j in range(i + 1, len(entries)):
                        if self._is_semantic_divergence(entries[i].alias, entries[j].alias):
                            conflicts.append(AliasConflict(
                                conflict_type=ALIAS_CONFLICT_TYPES["SEMANTIC_DIVERGENCE"],
                                entries=[entries[i], entries[j]],
                                description=f"Semantically divergent aliases mapped to same canonical '{canonical_key}': '{entries[i].alias}' vs '{entries[j].alias}'",
                                severity="WARN",
                                suggestion="Review if these aliases are truly equivalent",
                            ))
        
        return conflicts
    
    @staticmethod
    def _is_semantic_divergence(alias_a: str, alias_b: str) -> bool:
        """
        Simple heuristic to check if two aliases are semantically divergent.
        Uses character overlap ratio as a proxy.
        """
        import unicodedata
        a = unicodedata.normalize('NFKC', alias_a)
        b = unicodedata.normalize('NFKC', alias_b)
        
        # If one is a substring of the other, not divergent
        if a in b or b in a:
            return False
        
        # Character overlap ratio
        chars_a = set(a)
        chars_b = set(b)
        if not chars_a or not chars_b:
            return False
        
        overlap = len(chars_a & chars_b) / len(chars_a | chars_b)
        # If overlap < 30%, consider divergent
        return overlap < 0.30
    
    def validate_from_json(self, json_path: str) -> List[AliasConflict]:
        """
        Load alias entries from JSON and validate.
        
        Supports two formats:
        1. Flat dict: {"alias": "canonical", ...}
        2. List of dicts: [{"alias": "...", "canonical": "...", "variety": "..."}, ...]
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        valid, entries, error = self._validator.validate_alias_map(data)
        if not valid:
            return []
        
        return self.validate(entries)


# =============================================================================
# Section 7: P1 Test Runner
# =============================================================================

class P1RegressionTestRunner:
    """
    Regression test runner for V86 P1 rules.
    Extends P0's RegressionTestRunner with P1-specific metrics.
    """
    
    def __init__(self, engine: V86P1RuleEngine):
        self.engine = engine
        self.metrics = RegressionMetrics()
    
    def run_case(self, pair: MatchPair) -> Dict:
        """Run a single test case."""
        result = self.engine.evaluate(pair.indicator_name, pair.matched_name)
        actual_status = result["result"]
        actual_rule = result["blocked_by"]
        pair.actual_new_status = actual_status
        pair.actual_rule = actual_rule or ""
        
        # Determine verdict
        if pair.expected_new_status in ("BLOCKED",):
            expected_block = True
        elif pair.expected_new_status in ("PASS", "PASSED"):
            expected_block = False
        elif pair.expected_new_status in ("WHITELISTED",):
            expected_block = None
        elif pair.expected_new_status == "DATA_MISSING":
            expected_block = None
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
        elif actual_status == "NOT_APPLICABLE":
            self.metrics.total_errors += 1
        
        # TP/FP tracking
        if pair.expected_new_status == "BLOCKED" and actual_status == "BLOCKED":
            self.metrics.total_tp += 1
        elif pair.expected_new_status in ("PASS", "PASSED") and actual_status == "BLOCKED":
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
            "latency_ms": result.get("latency_ms", 0),
            "error_code": result.get("error_code", "OK"),
        }
        self.metrics.details.append(detail)
        
        return detail
    
    def run_cases(self, pairs: List[MatchPair]) -> RegressionMetrics:
        """Run all test cases and return aggregate metrics."""
        for pair in pairs:
            self.run_case(pair)
        
        # Calculate P0/P1 interception rates
        p0_cases = [d for d in self.metrics.details if d["risk_level"] == "P0"]
        p0_blocked = [d for d in p0_cases if d["actual"] == "BLOCKED"]
        if p0_cases:
            self.metrics.p0_interception_rate = len(p0_blocked) / len(p0_cases) * 100.0
        
        p1_cases = [d for d in self.metrics.details if d["risk_level"] == "P1"]
        p1_blocked = [d for d in p1_cases if d["actual"] == "BLOCKED"]
        if p1_cases:
            self.metrics.p1_interception_rate = len(p1_blocked) / len(p1_cases) * 100.0
        
        return self.metrics
    
    def print_summary(self, metrics: RegressionMetrics):
        """Print test summary."""
        print("=" * 70)
        print(f"V86 P1 Rule Engine Regression Test Summary")
        print(f"Version: {VERSION} | Engine: {self.engine.__class__.__name__}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        print(f"\n[统计] Total cases: {metrics.total_cases}")
        print(f"[统计] Blocked: {metrics.total_blocked}")
        print(f"[统计] Passed: {metrics.total_passed}")
        print(f"[统计] Data Missing: {metrics.total_data_missing}")
        print(f"[统计] Errors: {metrics.total_errors}")
        
        print(f"\n[TP/FP]")
        print(f"  TP (True Positive): {metrics.total_tp}")
        print(f"  FP (False Positive): {metrics.total_fp}")
        print(f"  Regression: {metrics.total_regression}")
        
        print(f"\n[拦截率]")
        print(f"  P0 Interception: {metrics.p0_interception_rate:.1f}%")
        print(f"  P1 Interception: {metrics.p1_interception_rate:.1f}%")
        
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
# Section 8: Performance Benchmark Runner
# =============================================================================

class PerformanceBenchmarkRunner:
    """
    Runs performance benchmarks on the V86 P1 rule engine.
    
    Benchmarks:
    1. Single-case latency (p50/p95/p99/max)
    2. Batch throughput (cases/sec)
    3. Memory usage (peak RSS)
    4. Concurrent evaluation (multi-threaded)
    """
    
    def __init__(self, engine: V86P1RuleEngine):
        self.engine = engine
        self._results: List[StressTestResult] = []
    
    def generate_synthetic_cases(self, count: int, complexity: str = "mixed") -> List[Dict]:
        """
        Generate synthetic test cases for benchmarking.
        
        Args:
            count: Number of cases to generate
            complexity: 'simple' / 'mixed' / 'stress'
            
        Returns:
            List of dicts with indicator_name, matched_name
        """
        import random
        
        # Sample data pools for different complexity levels
        simple_indicators = [
            "碳酸锂价格", "电解铜库存", "铝锭产量", "锌锭库存", "镍价",
            "碳酸锂产量", "铜库存", "铝产量", "锌产量", "镍库存",
        ]
        simple_matched = [
            "SMM:碳酸锂价格:日度", "SHFE:铜库存:日度", "SHFE:铝产量:月度",
            "LME:锌库存:周度", "LME:镍价格:日度",
        ]
        
        mixed_indicators = [
            "碳酸锂 三元523需求", "SMM: 碳酸锂现金生产利润", "碳酸锂需求总量",
            "碳酸锂冶炼利润", "电解镍厂库存天数", "碳酸锂工厂库存天数",
            "锡厂库存天数", "多晶硅工厂库存天数", "国内锌厂内库存天数",
            "碳酸锂工厂库存量", "中国电解镍净进口量", "工业硅样本工厂库存",
            "磷酸铁锂 电池 国内销量", "COMEX镍持仓量", "COMEX铜主力合约",
            "LME锡库存", "LME镍注册仓单", "氧化铝月度产量", "电解铝出库量",
            "铝棒出库量", "不锈钢产量", "钴矿库存", "铁矿石库存",
        ]
        mixed_matched = [
            "SMM: 碳酸锂现金生产利润: 外购三元极片黑粉", "碳酸锂冶炼利润（元/吨）",
            "碳酸锂工厂库存天数", "锡厂库存天数（天）", "碳酸锂工厂库存量",
            "中国海关:镍:净进口量:月度", "苯乙烯库存:社会库存:月度",
            "黄金供需平衡表:月度", "COMEX：铜：主力合约：持仓量（日）",
            "LME：镍：注册仓单（日）", "氧化铝：产量：中国（月）",
            "SHFE：氧化铝：加权平均价（日）", "SHFE: 铝: 库存: 日度",
            "不锈钢板：产量：中国（月）", "钴矿：库存：中国（月）",
            "铁矿石：库存：中国（月）", "钢材：产量：中国（月）",
            "原油：WTI：日度", "天然气：LNG：日度",
        ]
        
        stress_indicators = [
            "碳酸锂 三元523需求" * 50 + "测试超长文本",
            "电解铜库存" * 100,
            "锡厂库存天数（天）" * 200,
            "碳酸锂冶炼利润（元/吨）" * 150,
            "多晶硅工厂库存天数（天）",
            "国内锌厂内库存天数（天）" * 50,
        ]
        
        if complexity == "simple":
            ind_pool = simple_indicators
            mtd_pool = simple_matched
        elif complexity == "stress":
            ind_pool = stress_indicators
            mtd_pool = mixed_matched
        else:
            ind_pool = mixed_indicators
            mtd_pool = mixed_matched
        
        cases = []
        for i in range(count):
            cases.append({
                "case_id": f"BENCH-{i+1:05d}",
                "indicator_name": random.choice(ind_pool),
                "matched_name": random.choice(mtd_pool),
                "risk_id": f"BENCH-RISK-{i+1:05d}",
                "risk_level": "P1",
            })
        
        return cases
    
    def run_single_case_benchmark(self, case: Dict, iterations: int = 10) -> Dict:
        """
        Benchmark a single case with multiple iterations.
        
        Returns:
            Dict with latency stats
        """
        latencies = []
        results = []
        
        for _ in range(iterations):
            start = time.perf_counter_ns()
            result = self.engine.evaluate(
                case["indicator_name"],
                case["matched_name"],
            )
            elapsed_ns = time.perf_counter_ns() - start
            latencies.append(elapsed_ns / 1_000_000)  # ms
            results.append(result["result"])
        
        latencies.sort()
        
        return {
            "case_id": case["case_id"],
            "indicator_name": case["indicator_name"],
            "matched_name": case["matched_name"],
            "iterations": iterations,
            "avg_ms": sum(latencies) / len(latencies),
            "p50_ms": latencies[len(latencies) // 2],
            "p95_ms": latencies[int(len(latencies) * 0.95)],
            "p99_ms": latencies[int(len(latencies) * 0.99)],
            "max_ms": latencies[-1],
            "min_ms": latencies[0],
            "results": results,
        }
    
    def run_batch_benchmark(self, cases: List[Dict], workers: int = 1) -> Dict:
        """
        Benchmark a batch of cases.
        
        Args:
            cases: List of case dicts
            workers: Number of parallel workers (1 = sequential)
            
        Returns:
            Dict with throughput metrics
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        total_start = time.perf_counter_ns()
        
        if workers == 1:
            # Sequential
            results = []
            for case in cases:
                result = self.engine.evaluate(case["indicator_name"], case["matched_name"])
                results.append(result)
        else:
            # Parallel
            results = [None] * len(cases)
            
            def evaluate_case(idx_case):
                idx, case = idx_case
                result = self.engine.evaluate(case["indicator_name"], case["matched_name"])
                return idx, result
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for idx, result in executor.map(
                    evaluate_case, enumerate(cases), chunksize=10
                ):
                    results[idx] = result
        
        total_elapsed_ns = time.perf_counter_ns() - total_start
        
        total_blocked = sum(1 for r in results if r["result"] == "BLOCKED")
        total_passed = sum(1 for r in results if r["result"] == "PASSED")
        total_errors = sum(1 for r in results if r["result"] == "NOT_APPLICABLE")
        
        elapsed_ms = total_elapsed_ns / 1_000_000
        
        # Get latency distribution from individual calls
        # For sequential, we can measure per-case
        per_case_latencies = []
        for i, case in enumerate(cases[:100]):  # Sample first 100
            start = time.perf_counter_ns()
            _ = self.engine.evaluate(case["indicator_name"], case["matched_name"])
            per_case_latencies.append((time.perf_counter_ns() - start) / 1_000_000)
        
        per_case_latencies.sort()
        
        return {
            "total_cases": len(cases),
            "total_blocked": total_blocked,
            "total_passed": total_passed,
            "total_errors": total_errors,
            "elapsed_ms": round(elapsed_ms, 2),
            "cases_per_sec": round(len(cases) / (elapsed_ms / 1000), 2),
            "avg_ms_per_case": round(elapsed_ms / len(cases), 4),
            "p50_ms": per_case_latencies[len(per_case_latencies) // 2] if per_case_latencies else 0,
            "p95_ms": per_case_latencies[int(len(per_case_latencies) * 0.95)] if per_case_latencies else 0,
            "p99_ms": per_case_latencies[int(len(per_case_latencies) * 0.99)] if per_case_latencies else 0,
            "max_ms": per_case_latencies[-1] if per_case_latencies else 0,
            "workers": workers,
        }
    
    def run_stress_suite(self, scenarios: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Run a full stress test suite with multiple scenarios.
        
        Args:
            scenarios: List of scenario configs. If None, uses default scenarios.
            
        Returns:
            List of result dicts
        """
        if scenarios is None:
            scenarios = [
                {"name": "single_case", "count": 1, "iterations": 100, "workers": 1},
                {"name": "batch_100_sequential", "count": 100, "iterations": 1, "workers": 1},
                {"name": "batch_500_sequential", "count": 500, "iterations": 1, "workers": 1},
                {"name": "batch_1000_sequential", "count": 1000, "iterations": 1, "workers": 1},
                {"name": "batch_5000_sequential", "count": 5000, "iterations": 1, "workers": 1},
                {"name": "batch_100_parallel_4", "count": 100, "iterations": 1, "workers": 4},
                {"name": "batch_500_parallel_4", "count": 500, "iterations": 1, "workers": 4},
                {"name": "batch_1000_parallel_8", "count": 1000, "iterations": 1, "workers": 8},
                {"name": "stress_long_text", "count": 100, "iterations": 1, "workers": 1, "complexity": "stress"},
            ]
        
        results = []
        
        for scenario in scenarios:
            name = scenario["name"]
            count = scenario["count"]
            iterations = scenario.get("iterations", 1)
            workers = scenario.get("workers", 1)
            complexity = scenario.get("complexity", "mixed")
            
            cases = self.generate_synthetic_cases(count, complexity)
            
            if iterations > 1 and count == 1:
                # Single case, multiple iterations
                bench_result = self.run_single_case_benchmark(cases[0], iterations)
                results.append({
                    "scenario": name,
                    "type": "single_case",
                    "details": bench_result,
                })
            else:
                # Batch
                bench_result = self.run_batch_benchmark(cases, workers)
                results.append({
                    "scenario": name,
                    "type": "batch",
                    "details": bench_result,
                })
            
            print(f"  [完成] {name}: {bench_result.get('cases_per_sec', bench_result.get('avg_ms', 'N/A'))} ")
        
        self._results = results
        return results
    
    def get_results(self) -> List[Dict]:
        """Get the last benchmark results."""
        return self._results
    
    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB (via resource module if available)."""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # On Linux, ru_maxrss is in KB
            return usage.ru_maxrss / 1024
        except (ImportError, AttributeError):
            # Windows: use psutil if available
            try:
                import psutil
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024
            except ImportError:
                return 0.0


# =============================================================================
# Section 9: Self-Test (P1 Rules + Fault Tolerance + Alias Validation)
# =============================================================================

def run_p1_self_test():
    """
    Run self-test of V86 P1 rule engine.
    
    Tests:
    1. P1 cross-variety rules (BL-027~BL-038)
    2. Alias mapping consistency validation
    3. Fault tolerance (empty input, corrupted data, oversized text)
    4. Performance baseline
    """
    engine = V86P1RuleEngine()
    
    # Load P0 rules first (import from P0 prototype)
    p0_rules_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "dshb_rule_predev", "v86_p0_rule_prototype.py"
    )
    
    # Load P0 rules from the P0 module
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dshb_rule_predev"))
    
    try:
        from v86_p0_rule_prototype import create_v86_p0_rules
        p0_rules = create_v86_p0_rules()
        engine._add_rules(p0_rules)
        print(f"[加载] P0规则: {len(p0_rules)} 条")
    except ImportError:
        print("[警告] 无法加载P0规则，仅测试P1规则")
    
    # Load P1 rules
    p1_rules = create_v86_p1_rules()
    engine._add_rules(p1_rules)
    print(f"[加载] P1规则: {len(p1_rules)} 条")
    print(f"[总计] 规则总数: {engine.get_rule_count()}")
    
    runner = P1RegressionTestRunner(engine)
    test_pairs = []
    
    # =========================================================================
    # Test Group 1: BL-027 铝↔铜 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL027-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="电解铝出库量-中国",
        matched_name="SHFE：铜：主力合约：库存（日）",
        risk_id="TEST-BL027-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-027",
    ))
    test_pairs.append(MatchPair(
        case_id="BL027-002",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="铝锭库存",
        matched_name="铜库存",
        risk_id="TEST-BL027-002",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-027",
    ))
    
    # BL-027 Safety: 同品种 (should PASS)
    test_pairs.append(MatchPair(
        case_id="BL027-NEG-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="电解铝出库量",
        matched_name="SHFE：铝：库存（日）",
        risk_id="SAFE-BL027",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    
    # =========================================================================
    # Test Group 2: BL-028 铅↔锌 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL028-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="铅锭库存",
        matched_name="锌锭库存",
        risk_id="TEST-BL028-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-028",
    ))
    
    # BL-028 Safety
    test_pairs.append(MatchPair(
        case_id="BL028-NEG-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="铅锭库存",
        matched_name="铅锭产量",
        risk_id="SAFE-BL028",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    
    # =========================================================================
    # Test Group 3: BL-029 氧化铝↔铝 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL029-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="氧化铝月度产量",
        matched_name="电解铝出库量",
        risk_id="TEST-BL029-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-029",
    ))
    
    # =========================================================================
    # Test Group 4: BL-030 碳酸锂↔磷酸铁锂 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL030-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="碳酸锂价格",
        matched_name="磷酸铁锂产量",
        risk_id="TEST-BL030-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-030",
    ))
    
    # =========================================================================
    # Test Group 5: BL-031 钴↔锂 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL031-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="钴矿库存",
        matched_name="碳酸锂价格",
        risk_id="TEST-BL031-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-031",
    ))
    
    # =========================================================================
    # Test Group 6: BL-033 原油↔天然气 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL033-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="原油WTI价格",
        matched_name="LNG进口量",
        risk_id="TEST-BL033-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-033",
    ))
    
    # =========================================================================
    # Test Group 7: BL-034 铁矿石↔钢材 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL034-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="铁矿石库存",
        matched_name="螺纹钢产量",
        risk_id="TEST-BL034-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-034",
    ))
    
    # =========================================================================
    # Test Group 8: BL-036 黄金↔有色金属 (should BLOCK)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="BL036-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="黄金库存",
        matched_name="电解铜库存",
        risk_id="TEST-BL036-001",
        risk_level="P1",
        old_status="PASS",
        expected_new_status="BLOCKED",
        expected_rule="BL-036",
    ))
    
    # =========================================================================
    # Test Group 9: P1 Safety - 同品种 (should PASS)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="P1-NEG-001",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="电解铜库存",
        matched_name="铜锭产量",
        risk_id="SAFE-P1",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    test_pairs.append(MatchPair(
        case_id="P1-NEG-002",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="锌锭库存",
        matched_name="锌锭产量",
        risk_id="SAFE-P1",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    test_pairs.append(MatchPair(
        case_id="P1-NEG-003",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="铝锭库存",
        matched_name="铝锭产量",
        risk_id="SAFE-P1",
        risk_level="SAFE",
        old_status="PASS",
        expected_new_status="PASS",
        expected_rule="NONE",
    ))
    
    # =========================================================================
    # Test Group 10: P0 Rules (regression check)
    # =========================================================================
    test_pairs.append(MatchPair(
        case_id="P0-REG-001",
        source_type="p1_self_test",
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
        case_id="P0-REG-002",
        source_type="p1_self_test",
        template_id="N/A",
        indicator_name="中国电解镍净进口量",
        matched_name="N/A",
        risk_id="RISK-010",
        risk_level="P0",
        old_status="NOT_BLOCKED",
        expected_new_status="DATA_MISSING",
        expected_rule="BL-022",
    ))
    
    # =========================================================================
    # Run tests
    # =========================================================================
    metrics = runner.run_cases(test_pairs)
    runner.print_summary(metrics)
    
    # =========================================================================
    # Test Group 11: Fault Tolerance Tests
    # =========================================================================
    print("\n" + "=" * 70)
    print("故障容错测试 (Fault Tolerance Tests)")
    print("=" * 70)
    
    fault_tests = [
        {"case_id": "FAULT-001", "input": (None, "test"), "expect_error": True, "error_code": RuleErrorCode.EMPTY_INDICATOR.value},
        {"case_id": "FAULT-002", "input": ("test", None), "expect_error": False},
        {"case_id": "FAULT-003", "input": ("", "test"), "expect_error": True, "error_code": RuleErrorCode.EMPTY_INDICATOR.value},
        {"case_id": "FAULT-004", "input": ("test", ""), "expect_error": False},
        {"case_id": "FAULT-005", "input": ("test", "N/A"), "expect_error": False},
        {"case_id": "FAULT-006", "input": ("A" * 3000, "test"), "expect_error": True, "error_code": RuleErrorCode.INDICATOR_TOO_LONG.value},
        {"case_id": "FAULT-007", "input": ("test", "B" * 3000), "expect_error": True, "error_code": RuleErrorCode.MATCHED_TOO_LONG.value},
        {"case_id": "FAULT-008", "input": (12345, 67890), "expect_error": False, "note": "numeric input coerced to string"},
        {"case_id": "FAULT-009", "input": ("正常指标", "正常匹配"), "expect_error": False},
    ]
    
    fault_passed = 0
    fault_failed = 0
    
    for ft in fault_tests:
        result = engine.evaluate(ft["input"][0], ft["input"][1])
        
        # Data_MISSING is a valid non-error status (not a failure)
        is_valid_result = (result["error_code"] == RuleErrorCode.OK.value or 
                         result["error_code"] == RuleErrorCode.DATA_MISSING.value)
        
        if ft["expect_error"]:
            if not is_valid_result:
                print(f"  PASS {ft['case_id']}: error_code={result['error_code']}")
                fault_passed += 1
            else:
                print(f"  FAIL {ft['case_id']}: expected error but got {result['error_code']}")
                fault_failed += 1
        else:
            if is_valid_result:
                print(f"  PASS {ft['case_id']}: result={result['result']}")
                fault_passed += 1
            else:
                print(f"  FAIL {ft['case_id']}: unexpected error_code={result['error_code']}")
                fault_failed += 1
    
    print(f"\n[容错结果] {fault_passed}/{len(fault_tests)} passed")
    
    # =========================================================================
    # Test Group 12: Alias Mapping Validation
    # =========================================================================
    print("\n" + "=" * 70)
    print("别名映射一致性校验 (Alias Mapping Validation)")
    print("=" * 70)
    
    alias_entries = [
        AliasEntry(alias="碳酸锂价格", canonical="碳酸锂:价格:日度", variety="LI"),
        AliasEntry(alias="锂价", canonical="碳酸锂:价格:日度", variety="LI"),
        AliasEntry(alias="碳酸锂价格", canonical="碳酸锂:价格:周度", variety="LI"),  # CANONICAL_MISMATCH
        AliasEntry(alias="电解铜库存", canonical="铜:库存:日度", variety="CU"),
        AliasEntry(alias="铜库存", canonical="铜:库存:周度", variety="CU"),  # different canonical
        AliasEntry(alias="氧化铝产量", canonical="氧化铝:产量:月度", variety="AO"),
        AliasEntry(alias="氧化铝产量", canonical="氧化铝:产量:月度", variety="AL"),  # VARIETY_MISMATCH
        AliasEntry(alias="不锈钢产量", canonical="不锈钢:产量:月度", variety="SS"),
        AliasEntry(alias="黄金库存", canonical="黄金:库存:日度", variety="GO"),
        AliasEntry(alias="原油价格", canonical="原油:WTI:日度", variety="OE"),
        AliasEntry(alias="天然气价格", canonical="天然气:LNG:日度", variety="NG"),
    ]
    
    alias_validator = AliasMappingValidator()
    conflicts = alias_validator.validate(alias_entries)
    
    print(f"\n检测到的别名冲突: {len(conflicts)} 个")
    for conflict in conflicts:
        print(f"  [{conflict.severity}] {conflict.conflict_type}: {conflict.description}")
    
    # Count expected conflicts
    expected_conflict_types = set()
    for c in conflicts:
        expected_conflict_types.add(c.conflict_type)
    
    print(f"\n冲突类型: {expected_conflict_types}")
    print(f"[别名校验] 完成")
    
    # =========================================================================
    # Test Group 13: Performance Quick Check
    # =========================================================================
    print("\n" + "=" * 70)
    print("性能快速检查 (Performance Quick Check)")
    print("=" * 70)
    
    bench_runner = PerformanceBenchmarkRunner(engine)
    
    # Quick single-case benchmark
    quick_cases = [
        {"case_id": "PERF-001", "indicator_name": "碳酸锂 三元523需求", "matched_name": "SMM: 碳酸锂现金生产利润"},
        {"case_id": "PERF-002", "indicator_name": "电解铜库存", "matched_name": "铜锭产量"},
        {"case_id": "PERF-003", "indicator_name": "碳酸锂工厂库存天数", "matched_name": "碳酸锂工厂库存量"},
    ]
    
    for case in quick_cases:
        start = time.perf_counter_ns()
        for _ in range(50):
            _ = engine.evaluate(case["indicator_name"], case["matched_name"])
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        print(f"  {case['case_id']}: 50次/50.0次 = {elapsed/50:.3f}ms/case")
    
    # Batch benchmark
    batch_cases = bench_runner.generate_synthetic_cases(100)
    batch_result = bench_runner.run_batch_benchmark(batch_cases, workers=1)
    print(f"\n[批量测试] 100 cases: {batch_result['elapsed_ms']:.1f}ms total, "
          f"{batch_result['cases_per_sec']:.0f} cases/sec")
    
    # =========================================================================
    # Overall Result
    # =========================================================================
    total = len(test_pairs) + len(fault_tests)
    passed = sum(1 for p in test_pairs if p.verdict == "PASS") + fault_passed
    failed = sum(1 for p in test_pairs if p.verdict == "FAIL") + fault_failed
    skipped = sum(1 for p in test_pairs if p.verdict == "SKIP")
    
    overall_pass = failed == 0
    
    print(f"\n{'='*70}")
    print(f"P1 SELF-TEST RESULT: {'PASS' if overall_pass else 'FAIL'}")
    print(f"  Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print(f"  P0 Interception Rate: {metrics.p0_interception_rate:.1f}%")
    print(f"  P1 Interception Rate: {metrics.p1_interception_rate:.1f}%")
    print(f"  Fault Tolerance: {fault_passed}/{len(fault_tests)}")
    print(f"  Alias Conflicts Detected: {len(conflicts)}")
    print(f"{'='*70}")
    
    return overall_pass


# =============================================================================
# Section 10: CLI Entry Point
# =============================================================================

def main():
    """CLI entry point for V86 P1 rule prototype."""
    parser = argparse.ArgumentParser(
        description="V86 P1 Rule Engine Prototype",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run self-test (all P1 rules + fault tolerance + alias validation)
  python v86_p1_rule_prototype.py --self-test

  # Run performance benchmarks
  python v86_p1_rule_prototype.py --benchmark --count 1000

  # Run alias mapping validation
  python v86_p1_rule_prototype.py --alias-validate alias_map.json

  # List all rules
  python v86_p1_rule_prototype.py --list-rules

  # Evaluate a single pair
  python v86_p1_rule_prototype.py --eval "碳酸锂 三元523需求" "SMM: 碳酸锂现金生产利润"
        """,
    )
    parser.add_argument("--self-test", action="store_true", help="Run self-test")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--count", type=int, default=100, help="Number of benchmark cases")
    parser.add_argument("--alias-validate", type=str, help="Validate alias mapping from JSON")
    parser.add_argument("--list-rules", action="store_true", help="List all P1 rules")
    parser.add_argument("--eval", nargs=2, metavar=("INDICATOR", "MATCHED"), help="Evaluate a single pair")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers for benchmark")
    parser.add_argument("--output", type=str, help="Output file for benchmark results")

    args = parser.parse_args()
    
    engine = V86P1RuleEngine()
    
    # Load P0 rules
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dshb_rule_predev"))
        from v86_p0_rule_prototype import create_v86_p0_rules
        p0_rules = create_v86_p0_rules()
        engine._add_rules(p0_rules)
    except ImportError:
        pass
    
    # Load P1 rules
    p1_rules = create_v86_p1_rules()
    engine._add_rules(p1_rules)
    
    if args.self_test:
        run_p1_self_test()
    elif args.benchmark:
        bench_runner = PerformanceBenchmarkRunner(engine)
        scenarios = [
            {"name": f"batch_{args.count}_sequential", "count": args.count, "iterations": 1, "workers": 1},
        ]
        if args.workers > 1:
            scenarios.append({"name": f"batch_{args.count}_parallel_{args.workers}", "count": args.count, "iterations": 1, "workers": args.workers})
        
        results = bench_runner.run_stress_suite(scenarios)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump({"results": results, "version": VERSION, "timestamp": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
            print(f"\n[输出] 结果已保存到: {args.output}")
    elif args.alias_validate:
        validator = AliasMappingValidator()
        conflicts = validator.validate_from_json(args.alias_validate)
        print(f"\n[别名校验] 检测到 {len(conflicts)} 个冲突")
        for c in conflicts:
            print(f"  [{c.severity}] {c.conflict_type}: {c.description}")
    elif args.list_rules:
        p0 = engine.get_p0_rules()
        p1 = engine.get_p1_rules()
        print(f"\n[规则列表] P0: {len(p0)} 条, P1: {len(p1)} 条")
        print(f"\nP1规则:")
        for rule in p1:
            print(f"  {rule.rule_id}: {rule.name} ({rule.category}) - {rule.severity.value}")
    elif args.eval:
        result = engine.evaluate(args.eval[0], args.eval[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
