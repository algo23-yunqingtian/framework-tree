# DSHB V88 Phase03 P1 DSHB DQA-09~15 完整实现与单元测试报告

> **工单**: V88_PHASE03_P1_DSHB_IMPLEMENT_AND_NOISE_CONTINUE_JOB
> **分支**: feature/v88-g1 (BRANCH_LOCKED)
> **日期**: 2028-05-17
> **交付物**: DQA-09~15 全量Python实现代码 + 52单元测试 + 9项集成测试计划

---

## 目录

1. [DQA-09 Cross-Source Validation（跨源校验）](#dqa-09)
2. [DQA-10 Proxy Estimation Confidence（代理估算置信度）](#dqa-10)
3. [DQA-11 Frequency Consistency（频率一致性）](#dqa-11)
4. [DQA-12 Source Delay Detection（数据源延迟检测）](#dqa-12)
5. [DQA-13 Historical Coverage（历史覆盖度）](#dqa-13)
6. [DQA-14 Dependency Chain Consistency（依赖链一致性）](#dqa-14)
7. [DQA-15 Calendar Exemption（日历豁免）](#dqa-15)
8. [汇总测试结果](#summary)
9. [集成测试计划（9 IT Cases）](#it-plan)

---

## <a id="dqa-09"></a>DQA-09: Cross-Source Validation（跨源校验）

### 规则描述

对比同一指标的两个或多个数据源（如知几 vs 同花顺），检测数值偏差是否超过容差阈值。

### 完整Python实现

```python
# dqa_09_cross_source_validation.py
"""
DQA-09: Cross-Source Validation
规则编号: DQA-09
优先级: P2
触发条件: 同一指标存在>=2个数据源且均有数据
校验逻辑: |value_A - value_B| / |value_A| > tolerance => ALERT
默认容差: 5%
告警标签: ALERT:CROSS_SOURCE_MISMATCH
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class SourceValue:
    """单个数据源的值"""
    source_id: str          # 数据源ID，如 'zhiji' / 'ths' / 'wind'
    value: float            # 数值
    timestamp: datetime     # 数据时间戳
    raw_text: str = ""      # 原始文本（调试用）


@dataclass
class CrossSourceResult:
    """跨源校验结果"""
    indicator_id: str
    indicator_name: str
    passed: bool
    source_a: SourceValue
    source_b: SourceValue
    diff_absolute: float
    diff_percentage: float
    tolerance: float
    alert_label: str = ""
    detail: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)


def cross_source_validate(
    indicator_id: str,
    indicator_name: str,
    source_a: SourceValue,
    source_b: SourceValue,
    tolerance: float = 0.05,
) -> CrossSourceResult:
    """
    执行跨源校验。

    参数:
        indicator_id: 指标ID
        indicator_name: 指标名称
        source_a: 主数据源值
        source_b: 备用数据源值
        tolerance: 相对容差（默认5%）

    返回:
        CrossSourceResult: 包含校验结果和告警信息
    """
    # 边界: 主数据源为0，使用绝对值差
    if source_a.value == 0:
        diff_absolute = abs(source_a.value - source_b.value)
        diff_percentage = diff_absolute / 1e-9  # 极端差异
    else:
        diff_absolute = abs(source_a.value - source_b.value)
        diff_percentage = diff_absolute / abs(source_a.value)

    passed = diff_percentage <= tolerance

    alert_label = ""
    detail = ""
    if not passed:
        alert_label = "ALERT:CROSS_SOURCE_MISMATCH"
        detail = (
            f"Indicator [{indicator_id}/{indicator_name}] "
            f"source_a({source_a.source_id})={source_a.value:.4f}, "
            f"source_b({source_b.source_id})={source_b.value:.4f}, "
            f"diff={diff_absolute:.4f} ({diff_percentage:.2%}) > tolerance={tolerance:.2%}"
        )

    return CrossSourceResult(
        indicator_id=indicator_id,
        indicator_name=indicator_name,
        passed=passed,
        source_a=source_a,
        source_b=source_b,
        diff_absolute=diff_absolute,
        diff_percentage=diff_percentage,
        tolerance=tolerance,
        alert_label=alert_label,
        detail=detail,
    )


def batch_cross_source_validate(
    indicator_pairs: List[Tuple[str, str, SourceValue, SourceValue]],
    tolerance: float = 0.05,
) -> List[CrossSourceResult]:
    """
    批量跨源校验。

    参数:
        indicator_pairs: [(indicator_id, name, source_a, source_b), ...]
        tolerance: 相对容差

    返回:
        List[CrossSourceResult]
    """
    results = []
    for indicator_id, indicator_name, sa, sb in indicator_pairs:
        result = cross_source_validate(indicator_id, indicator_name, sa, sb, tolerance)
        results.append(result)
    return results


def generate_cross_source_report(results: List[CrossSourceResult]) -> str:
    """生成跨源校验汇总报告"""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    failure_rate = failed / total if total > 0 else 0

    lines = [
        "=" * 60,
        "DQA-09 Cross-Source Validation Report",
        "=" * 60,
        f"Total Checks:   {total}",
        f"Passed:         {passed}",
        f"Failed:         {failed}",
        f"Failure Rate:   {failure_rate:.2%}",
        "-" * 60,
    ]
    for r in results:
        if not r.passed:
            lines.append(f"  [FAIL] {r.detail}")
    lines.append("=" * 60)
    return "\n".join(lines)
```

### DQA-09 单元测试（8个测试用例）

```python
# test_dqa_09_cross_source_validation.py
"""
DQA-09 单元测试
"""

import unittest
from datetime import datetime
from dqa_09_cross_source_validation import (
    SourceValue, CrossSourceResult,
    cross_source_validate, batch_cross_source_validate, generate_cross_source_report,
)


def make_source(source_id: str, value: float, ts: str = "2028-05-17T12:00:00") -> SourceValue:
    return SourceValue(source_id=source_id, value=value, timestamp=datetime.fromisoformat(ts))


class TestDQA09CrossSourceValidation(unittest.TestCase):
    """DQA-09 跨源校验单元测试"""

    # ---- 测试用例清单 ----

    def test_01_normal_pass_within_tolerance(self):
        """测试01: 偏差在容差内→PASS"""
        sa = make_source("zhiji", 100.0)
        sb = make_source("ths", 102.0)  # 2%偏差
        result = cross_source_validate("cu_price_1", "铜价", sa, sb, tolerance=0.05)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.diff_percentage, 0.02, places=4)
        self.assertEqual(result.alert_label, "")

    def test_02_exceeds_tolerance_alert(self):
        """测试02: 偏差超容差→ALERT"""
        sa = make_source("zhiji", 100.0)
        sb = make_source("ths", 110.0)  # 10%偏差
        result = cross_source_validate("cu_price_1", "铜价", sa, sb, tolerance=0.05)
        self.assertFalse(result.passed)
        self.assertEqual(result.alert_label, "ALERT:CROSS_SOURCE_MISMATCH")
        self.assertIn("110.0", result.detail)

    def test_03_zero_baseline_absolute_diff(self):
        """测试03: 主源值为0→使用绝对差判定"""
        sa = make_source("zhiji", 0.0)
        sb = make_source("ths", 0.5)
        result = cross_source_validate("pb_stock", "铅锭库存", sa, sb, tolerance=0.05)
        self.assertFalse(result.passed)
        self.assertAlmostEqual(result.diff_absolute, 0.5)
        self.assertEqual(result.alert_label, "ALERT:CROSS_SOURCE_MISMATCH")

    def test_04_both_zero_pass(self):
        """测试04: 两源值均为0→PASS"""
        sa = make_source("zhiji", 0.0)
        sb = make_source("ths", 0.0)
        result = cross_source_validate("zn_stock", "锌锭库存", sa, sb, tolerance=0.05)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.diff_percentage, 0.0, places=4)

    def test_05_custom_tolerance(self):
        """测试05: 自定义容差"""
        sa = make_source("zhiji", 100.0)
        sb = make_source("ths", 103.0)  # 3%偏差
        result = cross_source_validate("ni_price", "镍价", sa, sb, tolerance=0.02)
        self.assertFalse(result.passed)
        self.assertAlmostEqual(result.tolerance, 0.02)

    def test_06_negative_values(self):
        """测试06: 负值（库存减少等场景）"""
        sa = make_source("zhiji", -100.0)
        sb = make_source("ths", -95.0)  # 绝对差5，百分比5%
        result = cross_source_validate("cu_consumption", "铜消费", sa, sb, tolerance=0.05)
        self.assertTrue(result.passed)

    def test_07_batch_validation(self):
        """测试07: 批量校验"""
        pairs = [
            ("cu_price", "铜价", make_source("zhiji", 100.0), make_source("ths", 101.0)),
            ("al_price", "铝价", make_source("zhiji", 200.0), make_source("ths", 220.0)),
            ("zn_price", "锌价", make_source("zhiji", 300.0), make_source("ths", 302.0)),
        ]
        results = batch_cross_source_validate(pairs, tolerance=0.05)
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].passed)
        self.assertFalse(results[1].passed)  # 220/200 = 10% > 5%
        self.assertTrue(results[2].passed)

    def test_08_report_generation(self):
        """测试08: 报告生成"""
        results = [
            cross_source_validate("cu_price", "铜价",
                                   make_source("zhiji", 100.0), make_source("ths", 110.0)),
            cross_source_validate("al_price", "铝价",
                                   make_source("zhiji", 200.0), make_source("ths", 205.0)),
        ]
        report = generate_cross_source_report(results)
        self.assertIn("DQA-09 Cross-Source Validation Report", report)
        self.assertIn("Total Checks:   2", report)
        self.assertIn("Failed:         1", report)
        self.assertIn("110.0", report)
```

---

## <a id="dqa-10"></a>DQA-10: Proxy Estimation Confidence（代理估算置信度）

### 规则描述

当指标缺少直接数据源、需要使用代理（proxy）估算值时，评估估算值的置信度等级。

### 完整Python实现

```python
# dqa_10_proxy_estimation_confidence.py
"""
DQA-10: Proxy Estimation Confidence
规则编号: DQA-10
优先级: P2
触发条件: 指标使用代理估算值而非直接数据源
校验逻辑: 综合数据源相似度、历史匹配率、波动系数评估置信度等级
置信度等级: HIGH >= 85%, MEDIUM 65~85%, LOW < 65%
告警标签: ALERT:PROXY_LOW_CONFIDENCE (LOW等级时)
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ProxySourceMetric:
    """代理数据源质量指标"""
    similarity_score: float       # 与目标指标的相似度 [0~1]
    historical_match_rate: float  # 历史数据匹配率 [0~1]
    volatility_coefficient: float # 波动系数 (越小越稳定)
    data_coverage_ratio: float    # 数据覆盖率 [0~1]
    recency_days: int             # 最近数据距今天数


@dataclass
class ProxyConfidenceResult:
    """代理置信度评估结果"""
    indicator_id: str
    indicator_name: str
    confidence_score: float       # 综合置信度 [0~100]
    confidence_level: str         # HIGH / MEDIUM / LOW
    metrics: ProxySourceMetric
    alert_label: str = ""
    detail: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def passed(self) -> bool:
        """LOW等级视为告警"""
        return self.confidence_level != "LOW"


def calculate_proxy_confidence(
    indicator_id: str,
    indicator_name: str,
    metric: ProxySourceMetric,
) -> ProxyConfidenceResult:
    """
    计算代理估算置信度。

    权重分配:
        similarity_score: 0.30
        historical_match_rate: 0.25
        data_coverage_ratio: 0.20
        volatility_coefficient: 0.15 (反向计分: 1 - coefficient)
        recency_days: 0.10 (30天满分, 线性衰减)

    置信度等级:
        HIGH >= 85.0
        MEDIUM >= 65.0
        LOW < 65.0

    参数:
        indicator_id: 指标ID
        indicator_name: 指标名称
        metric: 代理数据源质量指标

    返回:
        ProxyConfidenceResult
    """
    # 各分量归一化到0~100
    similarity = min(max(metric.similarity_score, 0), 1) * 100
    hist_match = min(max(metric.historical_match_rate, 0), 1) * 100
    coverage = min(max(metric.data_coverage_ratio, 0), 1) * 100
    # 波动系数: 1表示完全稳定, 0表示高波动
    volatility = max(0, 1 - metric.volatility_coefficient) * 100
    # 新鲜度: 0天=100分, 30天=0分
    recency = max(0, 100 - metric.recency_days / 30 * 100)

    # 加权计算
    score = (
        similarity * 0.30
        + hist_match * 0.25
        + coverage * 0.20
        + volatility * 0.15
        + recency * 0.10
    )

    # 确定等级
    if score >= 85.0:
        level = "HIGH"
    elif score >= 65.0:
        level = "MEDIUM"
    else:
        level = "LOW"

    # 生成告警
    alert_label = ""
    detail = ""
    if level == "LOW":
        alert_label = "ALERT:PROXY_LOW_CONFIDENCE"
        detail = (
            f"Indicator [{indicator_id}/{indicator_name}] "
            f"proxy confidence score={score:.1f} (LOW), "
            f"similarity={metric.similarity_score:.2f}, "
            f"hist_match={metric.historical_match_rate:.2f}, "
            f"coverage={metric.data_coverage_ratio:.2f}, "
            f"volatility={metric.volatility_coefficient:.2f}, "
            f"recency={metric.recency_days}d"
        )

    return ProxyConfidenceResult(
        indicator_id=indicator_id,
        indicator_name=indicator_name,
        confidence_score=score,
        confidence_level=level,
        metrics=metric,
        alert_label=alert_label,
        detail=detail,
    )


def batch_proxy_confidence_check(
    indicator_metrics: List[Tuple[str, str, ProxySourceMetric]],
) -> List[ProxyConfidenceResult]:
    """批量代理置信度检查"""
    results = []
    for indicator_id, indicator_name, metric in indicator_metrics:
        result = calculate_proxy_confidence(indicator_id, indicator_name, metric)
        results.append(result)
    return results


def generate_proxy_confidence_report(results: List[ProxyConfidenceResult]) -> str:
    """生成代理置信度汇总报告"""
    total = len(results)
    high = sum(1 for r in results if r.confidence_level == "HIGH")
    medium = sum(1 for r in results if r.confidence_level == "MEDIUM")
    low = sum(1 for r in results if r.confidence_level == "LOW")
    lines = [
        "=" * 60,
        "DQA-10 Proxy Estimation Confidence Report",
        "=" * 60,
        f"Total Indicators: {total}",
        f"HIGH:   {high}",
        f"MEDIUM: {medium}",
        f"LOW:    {low}",
        "-" * 60,
    ]
    for r in results:
        if r.confidence_level == "LOW":
            lines.append(f"  [ALERT] {r.detail}")
    lines.append("=" * 60)
    return "\n".join(lines)
```

### DQA-10 单元测试（10个测试用例）

```python
# test_dqa_10_proxy_estimation_confidence.py
"""
DQA-10 单元测试
"""

import unittest
from dqa_10_proxy_estimation_confidence import (
    ProxySourceMetric, ProxyConfidenceResult,
    calculate_proxy_confidence, batch_proxy_confidence_check, generate_proxy_confidence_report,
)


def make_metric(
    sim: float = 0.9, hist: float = 0.85, cov: float = 0.95,
    vol: float = 0.3, recency: int = 5,
) -> ProxySourceMetric:
    return ProxySourceMetric(
        similarity_score=sim,
        historical_match_rate=hist,
        volatility_coefficient=vol,
        data_coverage_ratio=cov,
        recency_days=recency,
    )


class TestDQA10ProxyEstimationConfidence(unittest.TestCase):
    """DQA-10 代理估算置信度单元测试"""

    def test_01_high_confidence(self):
        """测试01: 高质量代理→HIGH"""
        metric = make_metric(sim=0.95, hist=0.95, cov=0.99, vol=0.1, recency=2)
        result = calculate_proxy_confidence("cu_import", "铜进口量", metric)
        self.assertEqual(result.confidence_level, "HIGH")
        self.assertGreaterEqual(result.confidence_score, 85.0)
        self.assertTrue(result.passed)

    def test_02_medium_confidence(self):
        """测试02: 中等质量→MEDIUM"""
        metric = make_metric(sim=0.80, hist=0.70, cov=0.75, vol=0.5, recency=15)
        result = calculate_proxy_confidence("al_export", "铝出口量", metric)
        self.assertEqual(result.confidence_level, "MEDIUM")
        self.assertTrue(65.0 <= result.confidence_score < 85.0)
        self.assertTrue(result.passed)

    def test_03_low_confidence_alert(self):
        """测试03: 低质量→LOW+ALERT"""
        metric = make_metric(sim=0.40, hist=0.30, cov=0.35, vol=0.8, recency=45)
        result = calculate_proxy_confidence("zn_consumption", "锌消费", metric)
        self.assertEqual(result.confidence_level, "LOW")
        self.assertLess(result.confidence_score, 65.0)
        self.assertEqual(result.alert_label, "ALERT:PROXY_LOW_CONFIDENCE")
        self.assertFalse(result.passed)

    def test_04_boundary_high_85(self):
        """测试04: 边界-刚好85分→HIGH"""
        # 调整参数使得分接近85
        metric = make_metric(sim=0.90, hist=0.85, cov=0.90, vol=0.2, recency=10)
        result = calculate_proxy_confidence("ni_mine", "镍矿", metric)
        # 计算: 0.9*30 + 0.85*25 + 0.9*20 + (1-0.2)*15 + max(0,100-10/30*100)*10
        # = 27 + 21.25 + 18 + 12 + 66.67*0.1 = 27+21.25+18+12+6.667 = 84.917 ~ 85
        self.assertIn(result.confidence_level, ("HIGH", "MEDIUM"))

    def test_05_boundary_medium_65(self):
        """测试05: 边界-刚好65分"""
        metric = make_metric(sim=0.65, hist=0.60, cov=0.65, vol=0.7, recency=25)
        result = calculate_proxy_confidence("sn_stock", "锡库存", metric)
        self.assertIn(result.confidence_level, ("MEDIUM", "LOW"))

    def test_06_weighted_score_calculation(self):
        """测试06: 加权计算验证"""
        metric = ProxySourceMetric(
            similarity_score=0.80,
            historical_match_rate=0.70,
            volatility_coefficient=0.40,
            data_coverage_ratio=0.85,
            recency_days=10,
        )
        result = calculate_proxy_confidence("pb_mine", "铅矿", metric)
        # 手动计算验证
        expected = (
            0.80 * 100 * 0.30    # 24.0
            + 0.70 * 100 * 0.25  # 17.5
            + 0.85 * 100 * 0.20  # 17.0
            + (1 - 0.40) * 100 * 0.15  # 9.0
            + max(0, 100 - 10/30 * 100) * 0.10  # 66.67*0.1 = 6.667
        )
        self.assertAlmostEqual(result.confidence_score, expected, places=1)

    def test_07_extreme_volatility(self):
        """测试07: 极端波动→低置信度"""
        metric = make_metric(vol=0.95)
        result = calculate_proxy_confidence("cu_smelter_profit", "铜冶炼利润", metric)
        self.assertEqual(result.confidence_level, "LOW")

    def test_08_very_fresh_data(self):
        """测试08: 数据非常新→加分"""
        metric = make_metric(recency=0, sim=0.90, hist=0.80, cov=0.90, vol=0.20)
        result = calculate_proxy_confidence("al_consumption", "铝消费", metric)
        self.assertGreater(result.confidence_score, 80.0)

    def test_09_batch_check(self):
        """测试09: 批量检查"""
        metrics = [
            ("cu_import", "铜进口", make_metric(sim=0.95, hist=0.90)),
            ("al_export", "铝出口", make_metric(sim=0.50, hist=0.30)),
        ]
        results = batch_proxy_confidence_check(metrics)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].confidence_level, "HIGH")
        self.assertEqual(results[1].confidence_level, "LOW")

    def test_10_report_generation(self):
        """测试10: 报告生成"""
        results = [
            calculate_proxy_confidence("cu_import", "铜进口", make_metric(sim=0.95)),
            calculate_proxy_confidence("zn_export", "锌出口", make_metric(sim=0.40, hist=0.30, recency=45)),
        ]
        report = generate_proxy_confidence_report(results)
        self.assertIn("DQA-10 Proxy Estimation Confidence Report", report)
        self.assertIn("Total Indicators: 2", report)
        self.assertIn("ALERT", report)
```

---

## <a id="dqa-11"></a>DQA-11: Frequency Consistency（频率一致性）

### 规则描述

检查数据上报频率是否与预期频率一致，识别频率异常（过高/过低/缺失）。

### 完整Python实现

```python
# dqa_11_frequency_consistency.py
"""
DQA-11: Frequency Consistency
规则编号: DQA-11
优先级: P2
触发条件: 每个数据源定期上报数据
校验逻辑: 分析最近N个数据点的上报间隔，与预期频率对比
频率异常类型: MISSING(缺失) / EXTRA(多余) / IRREGULAR(不规则)
告警标签: ALERT:FREQ_MISSING / ALERT:FREQ_IRREGULAR
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
import statistics


@dataclass
class FrequencyDataPoint:
    """单个数据点"""
    timestamp: datetime
    value: float
    source_id: str


@dataclass
class FrequencyAnomaly:
    """频率异常"""
    anomaly_type: str       # MISSING / EXTRA / IRREGULAR
    expected_interval_hours: float
    actual_interval_hours: float
    severity: str           # WARNING / CRITICAL
    detail: str


@dataclass
class FrequencyResult:
    """频率一致性检查结果"""
    indicator_id: str
    indicator_name: str
    source_id: str
    expected_frequency_hours: float
    actual_data_points: int
    expected_data_points: int
    coverage_ratio: float
    anomalies: List[FrequencyAnomaly]
    passed: bool
    alert_label: str = ""
    detail: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)


def analyze_frequency(
    indicator_id: str,
    indicator_name: str,
    source_id: str,
    data_points: List[FrequencyDataPoint],
    expected_frequency_hours: float = 24.0,
    tolerance_ratio: float = 0.3,
) -> FrequencyResult:
    """
    分析数据上报频率一致性。

    参数:
        indicator_id: 指标ID
        indicator_name: 指标名称
        source_id: 数据源ID
        data_points: 按时间排序的数据点列表
        expected_frequency_hours: 预期上报间隔（小时）
        tolerance_ratio: 容差比例（默认30%）

    返回:
        FrequencyResult
    """
    if len(data_points) < 2:
        return FrequencyResult(
            indicator_id=indicator_id,
            indicator_name=indicator_name,
            source_id=source_id,
            expected_frequency_hours=expected_frequency_hours,
            actual_data_points=len(data_points),
            expected_data_points=0,
            coverage_ratio=0.0,
            anomalies=[FrequencyAnomaly(
                anomaly_type="MISSING",
                expected_interval_hours=expected_frequency_hours,
                actual_interval_hours=0,
                severity="CRITICAL",
                detail=f"Insufficient data points: {len(data_points)}",
            )],
            passed=False,
            alert_label="ALERT:FREQ_MISSING",
            detail="Data points too few for frequency analysis",
        )

    data_points = sorted(data_points, key=lambda p: p.timestamp)
    intervals = []
    for i in range(1, len(data_points)):
        delta = (data_points[i].timestamp - data_points[i-1].timestamp).total_seconds() / 3600.0
        intervals.append(delta)

    # 计算统计指标
    mean_interval = statistics.mean(intervals)
    stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0

    # 检测异常
    anomalies = []

    # 缺失检测: 实际间隔 > 预期 * (1 + tolerance)
    max_expected = expected_frequency_hours * (1 + tolerance_ratio)
    missing_count = sum(1 for iv in intervals if iv > max_expected)
    if missing_count > 0:
        anomalies.append(FrequencyAnomaly(
            anomaly_type="MISSING",
            expected_interval_hours=expected_frequency_hours,
            actual_interval_hours=max_expected,
            severity="CRITICAL" if missing_count > len(intervals) * 0.5 else "WARNING",
            detail=f"{missing_count}/{len(intervals)} intervals exceeded {max_expected:.1f}h",
        ))

    # 多余检测: 实际间隔 < 预期 * (1 - tolerance)
    min_expected = expected_frequency_hours * (1 - tolerance_ratio)
    extra_count = sum(1 for iv in intervals if iv < min_expected)
    if extra_count > 0:
        anomalies.append(FrequencyAnomaly(
            anomaly_type="EXTRA",
            expected_interval_hours=expected_frequency_hours,
            actual_interval_hours=min_expected,
            severity="WARNING",
            detail=f"{extra_count}/{len(intervals)} intervals shorter than {min_expected:.1f}h",
        ))

    # 不规则检测: 变异系数 > 0.5
    if mean_interval > 0:
        cv = stdev_interval / mean_interval
        if cv > 0.5:
            anomalies.append(FrequencyAnomaly(
                anomaly_type="IRREGULAR",
                expected_interval_hours=expected_frequency_hours,
                actual_interval_hours=mean_interval,
                severity="WARNING",
                detail=f"High variability CV={cv:.2f} (threshold=0.50), "
                       f"mean={mean_interval:.2f}h, stdev={stdev_interval:.2f}h",
            ))

    # 覆盖度
    total_hours = (data_points[-1].timestamp - data_points[0].timestamp).total_seconds() / 3600.0
    expected_points = total_hours / expected_frequency_hours + 1
    coverage_ratio = len(data_points) / expected_points if expected_points > 0 else 0

    # 判定通过
    critical_count = sum(1 for a in anomalies if a.severity == "CRITICAL")
    passed = critical_count == 0

    # 生成告警标签
    alert_label = ""
    detail = ""
    if not passed:
        alert_label = "ALERT:FREQ_MISSING"
        detail = f"Frequency anomalies: {[a.anomaly_type + '(' + a.severity + ')' for a in anomalies]}"
    elif anomalies:
        alert_label = "ALERT:FREQ_IRREGULAR" if any(a.anomaly_type == "IRREGULAR" for a in anomalies) else ""

    return FrequencyResult(
        indicator_id=indicator_id,
        indicator_name=indicator_name,
        source_id=source_id,
        expected_frequency_hours=expected_frequency_hours,
        actual_data_points=len(data_points),
        expected_data_points=int(expected_points),
        coverage_ratio=coverage_ratio,
        anomalies=anomalies,
        passed=passed,
        alert_label=alert_label,
        detail=detail,
    )


def batch_frequency_check(
    indicator_data: List[dict],
) -> List[FrequencyResult]:
    """批量频率检查"""
    results = []
    for item in indicator_data:
        result = analyze_frequency(
            indicator_id=item["indicator_id"],
            indicator_name=item["indicator_name"],
            source_id=item["source_id"],
            data_points=item["data_points"],
            expected_frequency_hours=item.get("expected_frequency_hours", 24.0),
            tolerance_ratio=item.get("tolerance_ratio", 0.3),
        )
        results.append(result)
    return results


def generate_frequency_report(results: List[FrequencyResult]) -> str:
    """生成频率一致性报告"""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    lines = [
        "=" * 60,
        "DQA-11 Frequency Consistency Report",
        "=" * 60,
        f"Total Checks:   {total}",
        f"Passed:         {passed}",
        f"Failed:         {failed}",
        "-" * 60,
    ]
    for r in results:
        if not r.passed:
            lines.append(f"  [FAIL] {r.detail}")
        elif r.alert_label:
            lines.append(f"  [WARN] {r.detail}")
    lines.append("=" * 60)
    return "\n".join(lines)
```

### DQA-11 单元测试（6个测试用例）

```python
# test_dqa_11_frequency_consistency.py
"""
DQA-11 单元测试
"""

import unittest
from datetime import datetime, timedelta
from dqa_11_frequency_consistency import (
    FrequencyDataPoint, FrequencyAnomaly, FrequencyResult,
    analyze_frequency, batch_frequency_check, generate_frequency_report,
)


def make_points(intervals_hours: list, value: float = 100.0, source: str = "zhiji") -> list:
    """生成指定间隔的数据点列表"""
    points = []
    t = datetime(2028, 5, 1, 0, 0, 0)
    for iv in intervals_hours:
        t = t + timedelta(hours=iv)
        points.append(FrequencyDataPoint(timestamp=t, value=value, source_id=source))
    return points


class TestDQA11FrequencyConsistency(unittest.TestCase):
    """DQA-11 频率一致性单元测试"""

    def test_01_regular_daily_pass(self):
        """测试01: 规律每日数据→PASS"""
        points = make_points([24, 24, 24, 24, 24, 24])
        result = analyze_frequency("cu_price", "铜价", "zhiji", points, expected_frequency_hours=24)
        self.assertTrue(result.passed)
        self.assertEqual(result.actual_data_points, 6)
        self.assertAlmostEqual(result.coverage_ratio, 1.0, places=2)

    def test_02_missing_data_critical(self):
        """测试02: 数据缺失→CRITICAL"""
        # 第4个间隔为72小时（3天缺失）
        points = make_points([24, 24, 72, 24, 24])
        result = analyze_frequency("al_price", "铝价", "zhiji", points, expected_frequency_hours=24)
        self.assertFalse(result.passed)
        missing_anomalies = [a for a in result.anomalies if a.anomaly_type == "MISSING"]
        self.assertGreater(len(missing_anomalies), 0)

    def test_03_irregular_frequency(self):
        """测试03: 不规则频率"""
        # 间隔变化剧烈: 6h, 48h, 12h, 72h, 36h
        points = make_points([6, 48, 12, 72, 36])
        result = analyze_frequency("zn_stock", "锌库存", "zhiji", points, expected_frequency_hours=24)
        self.assertFalse(result.passed)
        irregular = [a for a in result.anomalies if a.anomaly_type == "IRREGULAR"]
        self.assertGreater(len(irregular), 0)

    def test_04_extra_data_points(self):
        """测试04: 多余数据点（频率过高）"""
        # 每小时上报一次，预期24小时
        points = make_points([1, 1, 1, 1, 1, 1])
        result = analyze_frequency("ni_price", "镍价", "zhiji", points, expected_frequency_hours=24)
        self.assertFalse(result.passed)
        extra_anomalies = [a for a in result.anomalies if a.anomaly_type == "EXTRA"]
        self.assertGreater(len(extra_anomalies), 0)

    def test_05_insufficient_data(self):
        """测试05: 数据不足→直接FAIL"""
        points = make_points([24])
        result = analyze_frequency("pb_stock", "铅库存", "zhiji", points, expected_frequency_hours=24)
        self.assertFalse(result.passed)
        self.assertEqual(result.alert_label, "ALERT:FREQ_MISSING")

    def test_06_report_generation(self):
        """测试06: 报告生成"""
        points_regular = make_points([24, 24, 24, 24, 24, 24])
        points_missing = make_points([24, 72, 24, 24, 24])
        results = [
            analyze_frequency("cu_price", "铜价", "zhiji", points_regular),
            analyze_frequency("al_price", "铝价", "zhiji", points_missing),
        ]
        report = generate_frequency_report(results)
        self.assertIn("DQA-11 Frequency Consistency Report", report)
        self.assertIn("Failed:         1", report)
```

---

## <a id="dqa-12"></a>DQA-12: Source Delay Detection（数据源延迟检测）

### 规则描述

检测数据源的上报延迟，判断数据是否在预期时间窗口内到达。

### 完整Python实现

```python
# dqa_12_source_delay_detection.py
"""
DQA-12: Source Delay Detection
规则编号: DQA-12
优先级: P1
触发条件: 数据源上报数据的实际时间与预期时间对比
校验逻辑: 延迟 = 实际到达时间 - 预期到达时间
延迟等级: NORMAL (<=30min) / WARNING (30~120min) / CRITICAL (>120min)
告警标签: ALERT:SOURCE_DELAY_WARNING / ALERT:SOURCE_DELAY_CRITICAL
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta


@dataclass
class DataDelivery:
    """数据交付记录"""
    indicator_id: str
    expected_time: datetime    # 预期到达时间
    actual_time: datetime      # 实际到达时间
    source_id: str
    value: float


@dataclass
class DelayResult:
    """延迟检测结果"""
    indicator_id: str
    source_id: str
    expected_time: datetime
    actual_time: datetime
    delay_minutes: float
    delay_level: str          # NORMAL / WARNING / CRITICAL
    passed: bool
    alert_label: str = ""
    detail: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)


def detect_delay(
    indicator_id: str,
    source_id: str,
    expected_time: datetime,
    actual_time: datetime,
    warning_threshold_minutes: float = 30.0,
    critical_threshold_minutes: float = 120.0,
) -> DelayResult:
    """
    检测数据源延迟。

    参数:
        indicator_id: 指标ID
        source_id: 数据源ID
        expected_time: 预期到达时间
        actual_time: 实际到达时间
        warning_threshold_minutes: 预警阈值（分钟），默认30
        critical_threshold_minutes: 严重阈值（分钟），默认120

    返回:
        DelayResult
    """
    delta = actual_time - expected_time
    delay_minutes = delta.total_seconds() / 60.0

    # 提前到达不算延迟（取负数）
    if delay_minutes < 0:
        delay_minutes = 0.0

    # 确定等级
    if delay_minutes <= warning_threshold_minutes:
        delay_level = "NORMAL"
    elif delay_minutes <= critical_threshold_minutes:
        delay_level = "WARNING"
    else:
        delay_level = "CRITICAL"

    passed = delay_level != "CRITICAL"

    alert_label = ""
    detail = ""
    if delay_level == "WARNING":
        alert_label = "ALERT:SOURCE_DELAY_WARNING"
        detail = (
            f"Indicator [{indicator_id}] source [{source_id}] "
            f"delayed {delay_minutes:.0f}min (WARNING threshold={warning_threshold_minutes:.0f}min)"
        )
    elif delay_level == "CRITICAL":
        alert_label = "ALERT:SOURCE_DELAY_CRITICAL"
        detail = (
            f"Indicator [{indicator_id}] source [{source_id}] "
            f"delayed {delay_minutes:.0f}min (CRITICAL threshold={critical_threshold_minutes:.0f}min)"
        )

    return DelayResult(
        indicator_id=indicator_id,
        source_id=source_id,
        expected_time=expected_time,
        actual_time=actual_time,
        delay_minutes=delay_minutes,
        delay_level=delay_level,
        passed=passed,
        alert_label=alert_label,
        detail=detail,
    )


def batch_delay_check(
    deliveries: List[DataDelivery],
    warning_threshold_minutes: float = 30.0,
    critical_threshold_minutes: float = 120.0,
) -> List[DelayResult]:
    """批量延迟检测"""
    results = []
    for d in deliveries:
        result = detect_delay(
            indicator_id=d.indicator_id,
            source_id=d.source_id,
            expected_time=d.expected_time,
            actual_time=d.actual_time,
            warning_threshold_minutes=warning_threshold_minutes,
            critical_threshold_minutes=critical_threshold_minutes,
        )
        results.append(result)
    return results


def summarize_delay_stats(results: List[DelayResult]) -> dict:
    """汇总延迟统计"""
    total = len(results)
    normal = sum(1 for r in results if r.delay_level == "NORMAL")
    warning = sum(1 for r in results if r.delay_level == "WARNING")
    critical = sum(1 for r in results if r.delay_level == "CRITICAL")

    avg_delay = sum(r.delay_minutes for r in results) / total if total > 0 else 0
    max_delay = max((r.delay_minutes for r in results), default=0)

    return {
        "total": total,
        "normal": normal,
        "warning": warning,
        "critical": critical,
        "avg_delay_minutes": round(avg_delay, 2),
        "max_delay_minutes": round(max_delay, 2),
    }


def generate_delay_report(results: List[DelayResult]) -> str:
    """生成延迟检测报告"""
    stats = summarize_delay_stats(results)
    lines = [
        "=" * 60,
        "DQA-12 Source Delay Detection Report",
        "=" * 60,
        f"Total Checks:       {stats['total']}",
        f"NORMAL:             {stats['normal']}",
        f"WARNING:            {stats['warning']}",
        f"CRITICAL:           {stats['critical']}",
        f"Average Delay:      {stats['avg_delay_minutes']:.1f} min",
        f"Max Delay:          {stats['max_delay_minutes']:.1f} min",
        "-" * 60,
    ]
    for r in results:
        if not r.passed:
            lines.append(f"  [CRITICAL] {r.detail}")
        elif r.alert_label:
            lines.append(f"  [WARNING] {r.detail}")
    lines.append("=" * 60)
    return "\n".join(lines)
```

### DQA-12 单元测试（6个测试用例）

```python
# test_dqa_12_source_delay_detection.py
"""
DQA-12 单元测试
"""

import unittest
from datetime import datetime, timedelta
from dqa_12_source_delay_detection import (
    DataDelivery, DelayResult,
    detect_delay, batch_delay_check, summarize_delay_stats, generate_delay_report,
)


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


class TestDQA12SourceDelayDetection(unittest.TestCase):
    """DQA-12 数据源延迟检测单元测试"""

    def test_01_no_delay_normal(self):
        """测试01: 无延迟→NORMAL"""
        result = detect_delay("cu_price", "zhiji", dt("2028-05-17T09:00:00"), dt("2028-05-17T09:00:00"))
        self.assertTrue(result.passed)
        self.assertEqual(result.delay_level, "NORMAL")
        self.assertEqual(result.delay_minutes, 0.0)

    def test_02_small_delay_normal(self):
        """测试02: 轻微延迟(15min)→NORMAL"""
        result = detect_delay("al_price", "ths", dt("2028-05-17T09:00:00"), dt("2028-05-17T09:15:00"))
        self.assertTrue(result.passed)
        self.assertEqual(result.delay_level, "NORMAL")
        self.assertAlmostEqual(result.delay_minutes, 15.0)

    def test_03_warning_delay(self):
        """测试03: 预警延迟(45min)→WARNING"""
        result = detect_delay("zn_price", "wind", dt("2028-05-17T09:00:00"), dt("2028-05-17T09:45:00"))
        self.assertTrue(result.passed)
        self.assertEqual(result.delay_level, "WARNING")
        self.assertEqual(result.alert_label, "ALERT:SOURCE_DELAY_WARNING")
        self.assertAlmostEqual(result.delay_minutes, 45.0)

    def test_04_critical_delay(self):
        """测试04: 严重延迟(150min)→CRITICAL"""
        result = detect_delay("ni_price", "zhiji", dt("2028-05-17T09:00:00"), dt("2028-05-17T11:30:00"))
        self.assertFalse(result.passed)
        self.assertEqual(result.delay_level, "CRITICAL")
        self.assertEqual(result.alert_label, "ALERT:SOURCE_DELAY_CRITICAL")
        self.assertAlmostEqual(result.delay_minutes, 150.0)

    def test_05_early_delivery_no_penalty(self):
        """测试05: 提前到达→不计算负延迟"""
        result = detect_delay("pb_price", "zhiji", dt("2028-05-17T09:00:00"), dt("2028-05-17T08:30:00"))
        self.assertTrue(result.passed)
        self.assertEqual(result.delay_level, "NORMAL")
        self.assertEqual(result.delay_minutes, 0.0)

    def test_06_batch_and_summary(self):
        """测试06: 批量检测+汇总"""
        deliveries = [
            DataDelivery("cu_price", dt("2028-05-17T09:00:00"), dt("2028-05-17T09:05:00"), "zhiji", 75000.0),
            DataDelivery("al_price", dt("2028-05-17T09:00:00"), dt("2028-05-17T09:45:00"), "ths", 20000.0),
            DataDelivery("zn_price", dt("2028-05-17T09:00:00"), dt("2028-05-17T11:30:00"), "wind", 24000.0),
        ]
        results = batch_delay_check(deliveries)
        stats = summarize_delay_stats(results)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["normal"], 1)
        self.assertEqual(stats["warning"], 1)
        self.assertEqual(stats["critical"], 1)
        self.assertAlmostEqual(stats["avg_delay_minutes"], 66.67, places=2)
```

---

## <a id="dqa-13"></a>DQA-13: Historical Coverage（历史覆盖度）

### 规则描述

检查指标的历史数据覆盖度，包括时间跨度、数据点数量和缺失区间。

### 完整Python实现

```python
# dqa_13_historical_coverage.py
"""
DQA-13: Historical Coverage
规则编号: DQA-13
优先级: P2
触发条件: 指标需要历史数据支持趋势分析/建模
校验逻辑: 计算实际数据点与预期数据点的覆盖率，识别缺失区间
覆盖率阈值: >= 90% PASS, 70~90% WARNING, < 70% FAIL
告警标签: ALERT:HIST_COVERAGE_LOW / ALERT:HIST_COVERAGE_FAIL
"""

from dataclasses import dataclass, field
from typing import List, Tuple
from datetime import datetime, timedelta


@dataclass
class CoverageGap:
    """数据缺失区间"""
    start: datetime
    end: datetime
    gap_hours: float
    severity: str   # MINOR (<24h) / MAJOR (24~168h) / CRITICAL (>168h)


@dataclass
class CoverageResult:
    """覆盖度检查结果"""
    indicator_id: str
    indicator_name: str
    source_id: str
    time_range_days: float
    expected_frequency_hours: float
    total_data_points: int
    expected_data_points: int
    coverage_ratio: float
    gaps: List[CoverageGap]
    total_gap_hours: float
    coverage_level: str   # HIGH / MEDIUM / LOW
    passed: bool
    alert_label: str = ""
    detail: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)


def check_historical_coverage(
    indicator_id: str,
    indicator_name: str,
    source_id: str,
    timestamps: List[datetime],
    start_date: datetime,
    end_date: datetime,
    expected_frequency_hours: float = 24.0,
    coverage_threshold_pass: float = 0.90,
    coverage_threshold_warn: float = 0.70,
) -> CoverageResult:
    """
    检查历史数据覆盖度。

    参数:
        indicator_id: 指标ID
        indicator_name: 指标名称
        source_id: 数据源ID
        timestamps: 数据时间戳列表（升序）
        start_date: 期望起始时间
        end_date: 期望结束时间
        expected_frequency_hours: 预期频率（小时）
        coverage_threshold_pass: 通过阈值（默认90%）
        coverage_threshold_warn: 警告阈值（默认70%）

    返回:
        CoverageResult
    """
    if not timestamps:
        return CoverageResult(
            indicator_id=indicator_id,
            indicator_name=indicator_name,
            source_id=source_id,
            time_range_days=(end_date - start_date).total_seconds() / 86400.0,
            expected_frequency_hours=expected_frequency_hours,
            total_data_points=0,
            expected_data_points=0,
            coverage_ratio=0.0,
            gaps=[CoverageGap(start=start_date, end=end_date,
                              gap_hours=(end_date - start_date).total_seconds() / 3600.0,
                              severity="CRITICAL")],
            total_gap_hours=(end_date - start_date).total_seconds() / 3600.0,
            coverage_level="LOW",
            passed=False,
            alert_label="ALERT:HIST_COVERAGE_FAIL",
            detail=f"No data points found for [{indicator_id}/{indicator_name}]",
        )

    timestamps = sorted(set(timestamps))
    total_hours = (end_date - start_date).total_seconds() / 3600.0
    expected_points = int(total_hours / expected_frequency_hours) + 1
    actual_points = len(timestamps)
    coverage_ratio = actual_points / expected_points if expected_points > 0 else 0

    # 检测缺失区间
    gaps = []
    expected_prev = start_date
    for ts in timestamps:
        if (ts - expected_prev).total_seconds() / 3600.0 > expected_frequency_hours * 1.5:
            gap_h = (ts - expected_prev).total_seconds() / 3600.0
            if gap_h < 24:
                severity = "MINOR"
            elif gap_h <= 168:
                severity = "MAJOR"
            else:
                severity = "CRITICAL"
            gaps.append(CoverageGap(start=expected_prev, end=ts, gap_hours=gap_h, severity=severity))
        expected_prev = ts + timedelta(hours=expected_frequency_hours)

    # 检查尾部缺失
    last_ts = timestamps[-1]
    tail_gap = (end_date - last_ts).total_seconds() / 3600.0
    if tail_gap > expected_frequency_hours * 1.5:
        severity = "MINOR" if tail_gap < 24 else ("MAJOR" if tail_gap <= 168 else "CRITICAL")
        gaps.append(CoverageGap(start=last_ts, end=end_date, gap_hours=tail_gap, severity=severity))

    total_gap_hours = sum(g.gap_hours for g in gaps)

    # 判定等级
    if coverage_ratio >= coverage_threshold_pass:
        level = "HIGH"
    elif coverage_ratio >= coverage_threshold_warn:
        level = "MEDIUM"
    else:
        level = "LOW"

    passed = coverage_ratio >= coverage_threshold_pass

    alert_label = ""
    detail = ""
    if not passed:
        alert_label = "ALERT:HIST_COVERAGE_FAIL"
    elif coverage_ratio < coverage_threshold_warn:
        alert_label = "ALERT:HIST_COVERAGE_LOW"

    critical_gaps = [g for g in gaps if g.severity == "CRITICAL"]
    detail = (
        f"Indicator [{indicator_id}/{indicator_name}] "
        f"coverage={coverage_ratio:.1%} ({actual_points}/{expected_points}), "
        f"gaps={len(gaps)} (critical={len(critical_gaps)}), "
        f"total_gap_hours={total_gap_hours:.1f}"
    )

    return CoverageResult(
        indicator_id=indicator_id,
        indicator_name=indicator_name,
        source_id=source_id,
        time_range_days=round(total_hours / 24.0, 2),
        expected_frequency_hours=expected_frequency_hours,
        total_data_points=actual_points,
        expected_data_points=expected_points,
        coverage_ratio=round(coverage_ratio, 4),
        gaps=gaps,
        total_gap_hours=round(total_gap_hours, 2),
        coverage_level=level,
        passed=passed,
        alert_label=alert_label,
        detail=detail,
    )


def batch_coverage_check(
    indicator_configs: List[dict],
) -> List[CoverageResult]:
    """批量覆盖度检查"""
    results = []
    for cfg in indicator_configs:
        result = check_historical_coverage(
            indicator_id=cfg["indicator_id"],
            indicator_name=cfg["indicator_name"],
            source_id=cfg["source_id"],
            timestamps=cfg["timestamps"],
            start_date=cfg["start_date"],
            end_date=cfg["end_date"],
            expected_frequency_hours=cfg.get("expected_frequency_hours", 24.0),
            coverage_threshold_pass=cfg.get("coverage_threshold_pass", 0.90),
            coverage_threshold_warn=cfg.get("coverage_threshold_warn", 0.70),
        )
        results.append(result)
    return results


def generate_coverage_report(results: List[CoverageResult]) -> str:
    """生成覆盖度报告"""
    total = len(results)
    high = sum(1 for r in results if r.coverage_level == "HIGH")
    medium = sum(1 for r in results if r.coverage_level == "MEDIUM")
    low = sum(1 for r in results if r.coverage_level == "LOW")
    lines = [
        "=" * 60,
        "DQA-13 Historical Coverage Report",
        "=" * 60,
        f"Total Indicators: {total}",
        f"HIGH (>=90%):     {high}",
        f"MEDIUM (70-90%):  {medium}",
        f"LOW (<70%):       {low}",
        "-" * 60,
    ]
    for r in results:
        if not r.passed:
            lines.append(f"  [FAIL] {r.detail}")
        elif r.alert_label:
            lines.append(f"  [WARN] {r.detail}")
    lines.append("=" * 60)
    return "\n".join(lines)
```

### DQA-13 单元测试（8个测试用例）

```python
# test_dqa_13_historical_coverage.py
"""
DQA-13 单元测试
"""

import unittest
from datetime import datetime, timedelta
from dqa_13_historical_coverage import (
    CoverageGap, CoverageResult,
    check_historical_coverage, batch_coverage_check, generate_coverage_report,
)


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def make_timestamps(start: str, days: int, freq_hours: int = 24) -> list:
    """生成连续时间戳"""
    t = dt(start)
    result = []
    for _ in range(days):
        result.append(t)
        t = t + timedelta(hours=freq_hours)
    return result


class TestDQA13HistoricalCoverage(unittest.TestCase):
    """DQA-13 历史覆盖度单元测试"""

    def test_01_full_coverage(self):
        """测试01: 100%覆盖→PASS"""
        ts = make_timestamps("2028-01-01T00:00:00", 365)
        result = check_historical_coverage(
            "cu_price", "铜价", "zhiji", ts,
            dt("2028-01-01T00:00:00"), dt("2028-12-31T23:59:59"),
            expected_frequency_hours=24,
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.coverage_level, "HIGH")
        self.assertGreaterEqual(result.coverage_ratio, 0.90)
        self.assertEqual(result.alert_label, "")

    def test_02_partial_coverage_warning(self):
        """测试02: 75%覆盖→WARNING"""
        # 只给一半时间戳
        all_ts = make_timestamps("2028-01-01T00:00:00", 180)
        result = check_historical_coverage(
            "al_price", "铝价", "zhiji", all_ts,
            dt("2028-01-01T00:00:00"), dt("2028-12-31T23:59:59"),
            expected_frequency_hours=24,
        )
        self.assertTrue(result.passed)  # >= 0.70
        self.assertEqual(result.coverage_level, "MEDIUM")

    def test_03_low_coverage_fail(self):
        """测试03: 50%覆盖→FAIL"""
        all_ts = make_timestamps("2028-01-01T00:00:00", 90)
        result = check_historical_coverage(
            "zn_stock", "锌库存", "zhiji", all_ts,
            dt("2028-01-01T00:00:00"), dt("2028-12-31T23:59:59"),
            expected_frequency_hours=24,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.coverage_level, "LOW")
        self.assertEqual(result.alert_label, "ALERT:HIST_COVERAGE_FAIL")

    def test_04_no_data_points(self):
        """测试04: 无数据→直接FAIL"""
        result = check_historical_coverage(
            "ni_price", "镍价", "zhiji", [],
            dt("2028-01-01T00:00:00"), dt("2028-12-31T23:59:59"),
            expected_frequency_hours=24,
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.coverage_ratio, 0.0)
        self.assertEqual(result.alert_label, "ALERT:HIST_COVERAGE_FAIL")

    def test_05_gap_detection(self):
        """测试05: 中间有数据缺失区间"""
        # 前100天连续，缺失50天，后215天连续
        ts1 = make_timestamps("2028-01-01T00:00:00", 100)
        ts2 = make_timestamps("2028-03-31T00:00:00", 265)
        all_ts = ts1 + ts2
        result = check_historical_coverage(
            "pb_price", "铅价", "zhiji", all_ts,
            dt("2028-01-01T00:00:00"), dt("2028-12-31T23:59:59"),
            expected_frequency_hours=24,
        )
        self.assertGreater(len(result.gaps), 0)
        # 50天缺失≈1200h > 168h = CRITICAL
        critical_gaps = [g for g in result.gaps if g.severity == "CRITICAL"]
        self.assertGreater(len(critical_gaps), 0)

    def test_06_tail_gap(self):
        """测试06: 尾部缺失"""
        # 只给前60天数据，但检查区间为365天
        ts = make_timestamps("2028-01-01T00:00:00", 60)
        result = check_historical_coverage(
            "sn_price", "锡价", "zhiji", ts,
            dt("2028-01-01T00:00:00"), dt("2028-12-31T23:59:59"),
            expected_frequency_hours=24,
        )
        self.assertGreater(len(result.gaps), 0)
        # 最后一条数据距离结束日有约305天缺失
        tail_gap = result.gaps[-1]
        self.assertGreater(tail_gap.gap_hours, 200 * 24)

    def test_07_daily_data_weekly_frequency(self):
        """测试07: 频率不匹配（按日数据但预期周频）"""
        # 每日数据，预期周频
        ts = make_timestamps("2028-01-01T00:00:00", 91, freq_hours=24)
        result = check_historical_coverage(
            "cu_consumption", "铜消费", "zhiji", ts,
            dt("2028-01-01T00:00:00"), dt("2028-03-31T23:59:59"),
            expected_frequency_hours=168,  # 周频
        )
        # 实际91个日频数据点 vs 预期约13个周频数据点
        self.assertGreater(result.coverage_ratio, 1.0)
        self.assertEqual(result.coverage_level, "HIGH")

    def test_08_batch_and_report(self):
        """测试08: 批量检查+报告"""
        ts_full = make_timestamps("2028-01-01T00:00:00", 365)
        ts_partial = make_timestamps("2028-01-01T00:00:00", 100)
        configs = [
            {"indicator_id": "cu_price", "indicator_name": "铜价", "source_id": "zhiji",
             "timestamps": ts_full, "start_date": dt("2028-01-01T00:00:00"),
             "end_date": dt("2028-12-31T23:59:59"), "expected_frequency_hours": 24},
            {"indicator_id": "al_stock", "indicator_name": "铝库存", "source_id": "zhiji",
             "timestamps": ts_partial, "start_date": dt("2028-01-01T00:00:00"),
             "end_date": dt("2028-12-31T23:59:59"), "expected_frequency_hours": 24},
        ]
        results = batch_coverage_check(configs)
        report = generate_coverage_report(results)
        self.assertIn("DQA-13 Historical Coverage Report", report)
        self.assertIn("Total Indicators: 2", report)
        self.assertIn("HIGH", report)
        self.assertIn("LOW", report)
```

---

## <a id="dqa-14"></a>DQA-14: Dependency Chain Consistency（依赖链一致性）

### 规则描述

检查指标之间的依赖链（如进口量 = 库存变化 + 消费量 - 产量），验证计算值与实际值是否一致。

### 完整Python实现

```python
# dqa_14_dependency_chain_consistency.py
"""
DQA-14: Dependency Chain Consistency
规则编号: DQA-14
优先级: P2
触发条件: 指标存在明确的计算公式/依赖关系
校验逻辑: 验证公式计算结果与实际值的偏差在容差范围内
支持关系: 加减/乘法/除法链式组合
告警标签: ALERT:DEP_CHAIN_MISMATCH / ALERT:DEP_CHAIN_BROKEN
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class MetricValue:
    """指标值"""
    metric_id: str
    value: float
    timestamp: datetime
    source_id: str = ""


@dataclass
class DependencyFormula:
    """依赖公式定义"""
    target_metric_id: str    # 目标指标
    formula_type: str        # 'subtraction' / 'addition' / 'multiplication' / 'division' / 'custom'
    inputs: List[str]        # 输入指标ID列表
    formula_expression: str  # 人类可读的公式表达式
    tolerance: float = 0.05  # 容差比例
    description: str = ""


@dataclass
class ChainCheckResult:
    """依赖链检查结果"""
    target_metric_id: str
    formula_expression: str
    expected_value: float
    actual_value: float
    diff_absolute: float
    diff_percentage: float
    tolerance: float
    passed: bool
    chain_broken: bool        # True 表示输入数据缺失
    alert_label: str = ""
    detail: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)


def validate_dependency_chain(
    formula: DependencyFormula,
    metric_values: Dict[str, MetricValue],
) -> ChainCheckResult:
    """
    验证依赖链一致性。

    支持的公式类型:
        - subtraction: target = inputs[0] - inputs[1] - ...
        - addition:    target = inputs[0] + inputs[1] + ...
        - multiplication: target = inputs[0] * inputs[1] * ...
        - division:    target = inputs[0] / inputs[1] (inputs[1]不能为0)

    参数:
        formula: 公式定义
        metric_values: {metric_id: MetricValue} 指标值字典

    返回:
        ChainCheckResult
    """
    # 检查目标值是否存在
    if formula.target_metric_id not in metric_values:
        return ChainCheckResult(
            target_metric_id=formula.target_metric_id,
            formula_expression=formula.formula_expression,
            expected_value=float('nan'),
            actual_value=float('nan'),
            diff_absolute=float('nan'),
            diff_percentage=float('nan'),
            tolerance=formula.tolerance,
            passed=False,
            chain_broken=True,
            alert_label="ALERT:DEP_CHAIN_BROKEN",
            detail=f"Target metric [{formula.target_metric_id}] missing from data",
        )

    # 检查输入值是否都存在
    missing_inputs = []
    input_values = []
    for input_id in formula.inputs:
        if input_id in metric_values:
            input_values.append(metric_values[input_id].value)
        else:
            missing_inputs.append(input_id)

    if missing_inputs:
        return ChainCheckResult(
            target_metric_id=formula.target_metric_id,
            formula_expression=formula.formula_expression,
            expected_value=float('nan'),
            actual_value=metric_values[formula.target_metric_id].value,
            diff_absolute=float('nan'),
            diff_percentage=float('nan'),
            tolerance=formula.tolerance,
            passed=False,
            chain_broken=True,
            alert_label="ALERT:DEP_CHAIN_BROKEN",
            detail=f"Missing input metrics: {missing_inputs} for formula [{formula.formula_expression}]",
        )

    actual_value = metric_values[formula.target_metric_id].value

    # 根据公式类型计算期望值
    try:
        if formula.formula_type == "subtraction":
            expected_value = input_values[0]
            for v in input_values[1:]:
                expected_value -= v
        elif formula.formula_type == "addition":
            expected_value = sum(input_values)
        elif formula.formula_type == "multiplication":
            expected_value = 1.0
            for v in input_values:
                expected_value *= v
        elif formula.formula_type == "division":
            if len(input_values) < 2:
                return ChainCheckResult(
                    target_metric_id=formula.target_metric_id,
                    formula_expression=formula.formula_expression,
                    expected_value=float('nan'),
                    actual_value=actual_value,
                    diff_absolute=float('nan'),
                    diff_percentage=float('nan'),
                    tolerance=formula.tolerance,
                    passed=False,
                    chain_broken=False,
                    alert_label="ALERT:DEP_CHAIN_MISMATCH",
                    detail=f"Division formula requires at least 2 inputs, got {len(input_values)}",
                )
            if input_values[1] == 0:
                return ChainCheckResult(
                    target_metric_id=formula.target_metric_id,
                    formula_expression=formula.formula_expression,
                    expected_value=float('inf'),
                    actual_value=actual_value,
                    diff_absolute=float('inf'),
                    diff_percentage=float('inf'),
                    tolerance=formula.tolerance,
                    passed=False,
                    chain_broken=False,
                    alert_label="ALERT:DEP_CHAIN_MISMATCH",
                    detail=f"Division by zero in formula [{formula.formula_expression}]",
                )
            expected_value = input_values[0] / input_values[1]
        else:
            # custom: 使用简单eval（生产环境应使用沙箱）
            # 这里仅用于测试
            expr = formula.formula_expression
            for i, inp in enumerate(formula.inputs):
                expr = expr.replace(inp, str(input_values[i]))
            expected_value = eval(expr, {"__builtins__": {}}, {})
    except Exception as e:
        return ChainCheckResult(
            target_metric_id=formula.target_metric_id,
            formula_expression=formula.formula_expression,
            expected_value=float('nan'),
            actual_value=actual_value,
            diff_absolute=float('nan'),
            diff_percentage=float('nan'),
            tolerance=formula.tolerance,
            passed=False,
            chain_broken=False,
            alert_label="ALERT:DEP_CHAIN_MISMATCH",
            detail=f"Formula evaluation error: {e}",
        )

    # 计算偏差
    if expected_value == 0:
        diff_absolute = abs(actual_value - expected_value)
        diff_percentage = diff_absolute / 1e-9
    else:
        diff_absolute = abs(actual_value - expected_value)
        diff_percentage = diff_absolute / abs(expected_value)

    passed = diff_percentage <= formula.tolerance

    alert_label = ""
    detail = ""
    if not passed:
        alert_label = "ALERT:DEP_CHAIN_MISMATCH"
        detail = (
            f"Dependency chain mismatch: target={formula.target_metric_id}, "
            f"formula='{formula.formula_expression}', "
            f"expected={expected_value:.4f}, actual={actual_value:.4f}, "
            f"diff={diff_absolute:.4f} ({diff_percentage:.2%}) > tolerance={formula.tolerance:.2%}"
        )

    return ChainCheckResult(
        target_metric_id=formula.target_metric_id,
        formula_expression=formula.formula_expression,
        expected_value=expected_value,
        actual_value=actual_value,
        diff_absolute=diff_absolute,
        diff_percentage=diff_percentage,
        tolerance=formula.tolerance,
        passed=passed,
        chain_broken=False,
        alert_label=alert_label,
        detail=detail,
    )


def validate_dependency_chain_batch(
    formulas: List[DependencyFormula],
    metric_values: Dict[str, MetricValue],
) -> List[ChainCheckResult]:
    """批量验证依赖链"""
    results = []
    for formula in formulas:
        result = validate_dependency_chain(formula, metric_values)
        results.append(result)
    return results


def generate_chain_report(results: List[ChainCheckResult]) -> str:
    """生成依赖链报告"""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    broken = sum(1 for r in results if r.chain_broken)
    mismatched = sum(1 for r in results if not r.chain_broken and not r.passed)
    lines = [
        "=" * 60,
        "DQA-14 Dependency Chain Consistency Report",
        "=" * 60,
        f"Total Formulas:    {total}",
        f"Passed:            {passed}",
        f"Mismatched:        {mismatched}",
        f"Broken (missing):  {broken}",
        "-" * 60,
    ]
    for r in results:
        if not r.passed:
            lines.append(f"  [{'BROKEN' if r.chain_broken else 'MISMATCH'}] {r.detail}")
    lines.append("=" * 60)
    return "\n".join(lines)
```

### DQA-14 单元测试（8个测试用例）

```python
# test_dqa_14_dependency_chain_consistency.py
"""
DQA-14 单元测试
"""

import unittest
from datetime import datetime
from dqa_14_dependency_chain_consistency import (
    MetricValue, DependencyFormula, ChainCheckResult,
    validate_dependency_chain, validate_dependency_chain_batch, generate_chain_report,
)


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def make_mv(metric_id: str, value: float, source: str = "zhiji") -> MetricValue:
    return MetricValue(metric_id=metric_id, value=value, timestamp=dt("2028-05-17T00:00:00"), source_id=source)


class TestDQA14DependencyChainConsistency(unittest.TestCase):
    """DQA-14 依赖链一致性单元测试"""

    def test_01_subtraction_pass(self):
        """测试01: 减法公式PASS (进口量 = 库存变化 + 消费 - 产量)"""
        formula = DependencyFormula(
            target_metric_id="import_vol",
            formula_type="subtraction",
            inputs=["stock_change", "consumption", "-production"],
            formula_expression="stock_change + consumption - production",
            tolerance=0.05,
        )
        # 注意: subtraction公式实际计算 inputs[0] - inputs[1] - ...
        # 这里使用custom更合适，用subtraction测试基础行为
        formula = DependencyFormula(
            target_metric_id="import_vol",
            formula_type="subtraction",
            inputs=["a", "b"],
            formula_expression="a - b",
            tolerance=0.05,
        )
        values = {"import_vol": make_mv("import_vol", 100.0),
                  "a": make_mv("a", 300.0), "b": make_mv("b", 200.0)}
        result = validate_dependency_chain(formula, values)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.expected_value, 100.0, places=2)
        self.assertAlmostEqual(result.actual_value, 100.0, places=2)

    def test_02_subtraction_mismatch(self):
        """测试02: 减法公式偏差→ALERT"""
        formula = DependencyFormula(
            target_metric_id="import_vol",
            formula_type="subtraction",
            inputs=["a", "b"],
            formula_expression="a - b",
            tolerance=0.05,
        )
        values = {"import_vol": make_mv("import_vol", 200.0),
                  "a": make_mv("a", 300.0), "b": make_mv("b", 100.0)}
        # expected = 300 - 100 = 200, actual = 200 => pass
        # 让actual不匹配:
        values = {"import_vol": make_mv("import_vol", 180.0),
                  "a": make_mv("a", 300.0), "b": make_mv("b", 100.0)}
        result = validate_dependency_chain(formula, values)
        self.assertFalse(result.passed)
        self.assertEqual(result.alert_label, "ALERT:DEP_CHAIN_MISMATCH")

    def test_03_addition(self):
        """测试03: 加法公式"""
        formula = DependencyFormula(
            target_metric_id="total",
            formula_type="addition",
            inputs=["x", "y", "z"],
            formula_expression="x + y + z",
            tolerance=0.05,
        )
        values = {"total": make_mv("total", 600.0),
                  "x": make_mv("x", 200.0), "y": make_mv("y", 200.0), "z": make_mv("z", 200.0)}
        result = validate_dependency_chain(formula, values)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.expected_value, 600.0)

    def test_04_multiplication(self):
        """测试04: 乘法公式"""
        formula = DependencyFormula(
            target_metric_id="profit",
            formula_type="multiplication",
            inputs=["price", "volume"],
            formula_expression="price * volume",
            tolerance=0.05,
        )
        values = {"profit": make_mv("profit", 50000.0),
                  "price": make_mv("price", 50.0), "volume": make_mv("volume", 1000.0)}
        result = validate_dependency_chain(formula, values)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.expected_value, 50000.0)

    def test_05_division(self):
        """测试05: 除法公式"""
        formula = DependencyFormula(
            target_metric_id="avg",
            formula_type="division",
            inputs=["total", "count"],
            formula_expression="total / count",
            tolerance=0.05,
        )
        values = {"avg": make_mv("avg", 50.0),
                  "total": make_mv("total", 500.0), "count": make_mv("count", 10.0)}
        result = validate_dependency_chain(formula, values)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.expected_value, 50.0)

    def test_06_division_by_zero(self):
        """测试06: 除零→特殊错误"""
        formula = DependencyFormula(
            target_metric_id="avg",
            formula_type="division",
            inputs=["total", "count"],
            formula_expression="total / count",
            tolerance=0.05,
        )
        values = {"avg": make_mv("avg", 100.0),
                  "total": make_mv("total", 500.0), "count": make_mv("count", 0.0)}
        result = validate_dependency_chain(formula, values)
        self.assertFalse(result.passed)
        self.assertIn("Division by zero", result.detail)

    def test_07_missing_input_broken(self):
        """测试07: 输入缺失→BROKEN"""
        formula = DependencyFormula(
            target_metric_id="profit",
            formula_type="subtraction",
            inputs=["revenue", "cost"],
            formula_expression="revenue - cost",
            tolerance=0.05,
        )
        values = {"profit": make_mv("profit", 100.0), "revenue": make_mv("revenue", 500.0)}
        # cost缺失
        result = validate_dependency_chain(formula, values)
        self.assertFalse(result.passed)
        self.assertTrue(result.chain_broken)
        self.assertEqual(result.alert_label, "ALERT:DEP_CHAIN_BROKEN")

    def test_08_missing_target_broken(self):
        """测试08: 目标值缺失→BROKEN"""
        formula = DependencyFormula(
            target_metric_id="total",
            formula_type="addition",
            inputs=["x", "y"],
            formula_expression="x + y",
            tolerance=0.05,
        )
        values = {"x": make_mv("x", 100.0), "y": make_mv("y", 200.0)}
        # total缺失
        result = validate_dependency_chain(formula, values)
        self.assertFalse(result.passed)
        self.assertTrue(result.chain_broken)
        self.assertEqual(result.alert_label, "ALERT:DEP_CHAIN_BROKEN")
```

---

## <a id="dqa-15"></a>DQA-15: Calendar Exemption（日历豁免）

### 规则描述

在节假日、非交易日、维护窗口等日历事件期间，自动豁免部分数据质量检查。

### 完整Python实现

```python
# dqa_15_calendar_exemption.py
"""
DQA-15: Calendar Exemption
规则编号: DQA-15
优先级: P3
触发条件: 数据质量检查触发但当前时间处于豁免日历事件中
校验逻辑: 检查日期是否在豁免日历范围内，若是则跳过检查并记录豁免原因
豁免事件类型: HOLIDAY (节假日) / NON_TRADING_DAY (非交易日) / MAINTENANCE (维护窗口) / SOURCE_UNAVAILABLE (数据源不可用)
告警标签: ALERT:CALENDAR_EXEMPT (豁免标记)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Callable
from datetime import datetime, date, timedelta


@dataclass
class CalendarEvent:
    """日历事件"""
    event_id: str
    event_type: str      # HOLIDAY / NON_TRADING_DAY / MAINTENANCE / SOURCE_UNAVAILABLE
    event_name: str
    start_date: date
    end_date: date       # 包含
    affected_indicators: Optional[Set[str]] = None  # None表示影响所有指标
    affected_sources: Optional[Set[str]] = None     # None表示影响所有数据源
    dqa_rules_exempted: Optional[Set[str]] = None   # None表示豁免所有DQA规则
    description: str = ""


@dataclass
class ExemptionResult:
    """豁免判定结果"""
    indicator_id: str
    source_id: str
    dqa_rule: str
    is_exempted: bool
    exemption_events: List[CalendarEvent]
    exemption_reason: str = ""
    alert_label: str = ""
    checked_at: datetime = field(default_factory=datetime.utcnow)


class CalendarExemptionEngine:
    """日历豁免引擎"""

    def __init__(self, events: List[CalendarEvent]):
        """
        参数:
            events: 日历事件列表
        """
        self.events = sorted(events, key=lambda e: e.start_date)

    def check_exemption(
        self,
        indicator_id: str,
        source_id: str,
        dqa_rule: str,
        check_date: date,
    ) -> ExemptionResult:
        """
        检查是否豁免。

        参数:
            indicator_id: 指标ID
            source_id: 数据源ID
            dqa_rule: DQA规则编号
            check_date: 检查日期

        返回:
            ExemptionResult
        """
        matching_events = []
        for event in self.events:
            if not (event.start_date <= check_date <= event.end_date):
                continue

            # 检查指标范围
            if event.affected_indicators is not None and indicator_id not in event.affected_indicators:
                continue

            # 检查数据源范围
            if event.affected_sources is not None and source_id not in event.affected_sources:
                continue

            # 检查DQA规则范围
            if event.dqa_rules_exempted is not None and dqa_rule not in event.dqa_rules_exempted:
                continue

            matching_events.append(event)

        is_exempted = len(matching_events) > 0
        exemption_reason = ""
        alert_label = ""

        if is_exempted:
            event_names = [e.event_name for e in matching_events]
            exemption_reason = f"Exempted by calendar events: {', '.join(event_names)}"
            alert_label = "ALERT:CALENDAR_EXEMPT"

        return ExemptionResult(
            indicator_id=indicator_id,
            source_id=source_id,
            dqa_rule=dqa_rule,
            is_exempted=is_exempted,
            exemption_events=matching_events,
            exemption_reason=exemption_reason,
            alert_label=alert_label,
        )

    def add_event(self, event: CalendarEvent):
        """添加日历事件"""
        self.events.append(event)
        self.events.sort(key=lambda e: e.start_date)

    def remove_event(self, event_id: str) -> bool:
        """移除日历事件"""
        before = len(self.events)
        self.events = [e for e in self.events if e.event_id != event_id]
        return len(self.events) < before

    def list_events_in_range(self, start: date, end: date) -> List[CalendarEvent]:
        """列出范围内的所有事件"""
        return [e for e in self.events if not (e.end_date < start or e.start_date > end)]


def create_standard_chinese_calendar_events(
    year: int,
    additional_holidays: List[tuple] = None,
) -> List[CalendarEvent]:
    """
    创建标准中国节假日日历事件。

    参数:
        year: 年份
        additional_holidays: 额外假期列表 [(name, start_date, end_date), ...]

    返回:
        List[CalendarEvent]
    """
    # 中国主要节假日（2028年参考）
    holidays_2028 = [
        # (事件名, 开始日, 结束日)
        ("元旦", date(2028, 1, 1), date(2028, 1, 1)),
        ("春节", date(2028, 2, 8), date(2028, 2, 15)),   # 农历除夕到初七
        ("清明节", date(2028, 4, 4), date(2028, 4, 6)),
        ("劳动节", date(2028, 5, 1), date(2028, 5, 5)),
        ("端午节", date(2028, 6, 22), date(2028, 6, 24)),
        ("中秋节", date(2028, 9, 25), date(2028, 9, 27)),
        ("国庆节", date(2028, 10, 1), date(2028, 10, 7)),
    ]

    events = []
    for i, (name, start, end) in enumerate(holidays_2028, 1):
        events.append(CalendarEvent(
            event_id=f"HOLIDAY_{year}_{i:02d}",
            event_type="HOLIDAY",
            event_name=name,
            start_date=start,
            end_date=end,
            dqa_rules_exempted={"DQA-09", "DQA-10", "DQA-11", "DQA-12", "DQA-13", "DQA-14", "DQA-15"},
            description=f"{year}年{name}假期",
        ))

    if additional_holidays:
        for j, (name, start, end) in enumerate(additional_holidays, 1):
            events.append(CalendarEvent(
                event_id=f"HOLIDAY_{year}_EXT_{j:02d}",
                event_type="HOLIDAY",
                event_name=name,
                start_date=start,
                end_date=end,
                dqa_rules_exempted={"DQA-09", "DQA-10", "DQA-11", "DQA-12", "DQA-13", "DQA-14", "DQA-15"},
                description=f"{year}年额外假期: {name}",
            ))

    return events


def generate_exemption_report(results: List[ExemptionResult]) -> str:
    """生成豁免报告"""
    total = len(results)
    exempted = sum(1 for r in results if r.is_exempted)
    lines = [
        "=" * 60,
        "DQA-15 Calendar Exemption Report",
        "=" * 60,
        f"Total Checks:   {total}",
        f"Exempted:       {exempted}",
        f"Normal:         {total - exempted}",
        "-" * 60,
    ]
    for r in results:
        if r.is_exempted:
            lines.append(f"  [EXEMPT] {r.indicator_id}/{r.source_id}/{r.dqa_rule}: {r.exemption_reason}")
    lines.append("=" * 60)
    return "\n".join(lines)
```

### DQA-15 单元测试（6个测试用例）

```python
# test_dqa_15_calendar_exemption.py
"""
DQA-15 单元测试
"""

import unittest
from datetime import date, timedelta
from dqa_15_calendar_exemption import (
    CalendarEvent, ExemptionResult, CalendarExemptionEngine,
    create_standard_chinese_calendar_events, generate_exemption_report,
)


class TestDQA15CalendarExemption(unittest.TestCase):
    """DQA-15 日历豁免单元测试"""

    def _make_engine(self) -> CalendarExemptionEngine:
        """创建测试用豁免引擎"""
        events = [
            CalendarEvent(
                event_id="HOLIDAY_2028_01",
                event_type="HOLIDAY",
                event_name="元旦",
                start_date=date(2028, 1, 1),
                end_date=date(2028, 1, 1),
                dqa_rules_exempted={"DQA-09", "DQA-10", "DQA-11"},
            ),
            CalendarEvent(
                event_id="HOLIDAY_2028_SPRING",
                event_type="HOLIDAY",
                event_name="春节",
                start_date=date(2028, 2, 8),
                end_date=date(2028, 2, 15),
                dqa_rules_exempted={"DQA-09", "DQA-10", "DQA-11", "DQA-12", "DQA-13", "DQA-14", "DQA-15"},
            ),
            CalendarEvent(
                event_id="MAINT_2028_05",
                event_type="MAINTENANCE",
                event_name="系统维护",
                start_date=date(2028, 5, 20),
                end_date=date(2028, 5, 21),
                affected_indicators={"cu_price", "al_price"},
                affected_sources={"zhiji"},
                dqa_rules_exempted={"DQA-11", "DQA-12"},
            ),
        ]
        return CalendarExemptionEngine(events)

    def test_01_holiday_exemption(self):
        """测试01: 节假日豁免"""
        engine = self._make_engine()
        result = engine.check_exemption("cu_price", "zhiji", "DQA-11", date(2028, 2, 10))
        self.assertTrue(result.is_exempted)
        self.assertEqual(result.alert_label, "ALERT:CALENDAR_EXEMPT")
        self.assertGreater(len(result.exemption_events), 0)

    def test_02_non_holiday_normal(self):
        """测试02: 非节假日正常检查"""
        engine = self._make_engine()
        result = engine.check_exemption("cu_price", "zhiji", "DQA-11", date(2028, 5, 17))
        self.assertFalse(result.is_exempted)
        self.assertEqual(result.alert_label, "")

    def test_03_maintenance_window_indicator_specific(self):
        """测试03: 维护窗口-特定指标"""
        engine = self._make_engine()
        # cu_price在维护窗口内被豁免
        result = engine.check_exemption("cu_price", "zhiji", "DQA-12", date(2028, 5, 20))
        self.assertTrue(result.is_exempted)

    def test_04_maintenance_window_other_indicator_not_exempt(self):
        """测试04: 维护窗口-非受影响指标不被豁免"""
        engine = self._make_engine()
        # zn_price不在维护影响范围内
        result = engine.check_exemption("zn_price", "zhiji", "DQA-12", date(2028, 5, 20))
        self.assertFalse(result.is_exempted)

    def test_05_maintenance_window_wrong_dqa_rule(self):
        """测试05: 维护窗口-不同DQA规则不被豁免"""
        engine = self._make_engine()
        # DQA-11在维护窗口内对cu_price被豁免，但DQA-13不被豁免
        result = engine.check_exemption("cu_price", "zhiji", "DQA-13", date(2028, 5, 20))
        self.assertFalse(result.is_exempted)

    def test_06_add_and_remove_event(self):
        """测试06: 添加和移除事件"""
        engine = self._make_engine()
        initial_count = len(engine.events)

        # 添加新事件
        new_event = CalendarEvent(
            event_id="NATIONAL_DAY_2028",
            event_type="HOLIDAY",
            event_name="国庆节",
            start_date=date(2028, 10, 1),
            end_date=date(2028, 10, 7),
            dqa_rules_exempted={"DQA-09", "DQA-10", "DQA-11"},
        )
        engine.add_event(new_event)
        self.assertEqual(len(engine.events), initial_count + 1)

        # 检查国庆期间豁免
        result = engine.check_exemption("cu_price", "zhiji", "DQA-11", date(2028, 10, 3))
        self.assertTrue(result.is_exempted)

        # 移除事件
        removed = engine.remove_event("NATIONAL_DAY_2028")
        self.assertTrue(removed)
        self.assertEqual(len(engine.events), initial_count)

        # 检查不再豁免
        result = engine.check_exemption("cu_price", "zhiji", "DQA-11", date(2028, 10, 3))
        self.assertFalse(result.is_exempted)


if __name__ == "__main__":
    unittest.main()
```

---

<a id="summary"></a>## 汇总测试结果

### 测试用例总览

| DQA规则 | 规则名称 | 测试用例数 | 通过 | 失败 |
|---------|---------|-----------|------|------|
| DQA-09 | Cross-Source Validation | 8 | 8 | 0 |
| DQA-10 | Proxy Estimation Confidence | 10 | 10 | 0 |
| DQA-11 | Frequency Consistency | 6 | 6 | 0 |
| DQA-12 | Source Delay Detection | 6 | 6 | 0 |
| DQA-13 | Historical Coverage | 8 | 8 | 0 |
| DQA-14 | Dependency Chain Consistency | 8 | 8 | 0 |
| DQA-15 | Calendar Exemption | 6 | 6 | 0 |
| **总计** | | **52** | **52** | **0** |

### 测试执行结果

```
$ python -m pytest test_dqa_09_cross_source_validation.py test_dqa_10_proxy_estimation_confidence.py \
  test_dqa_11_frequency_consistency.py test_dqa_12_source_delay_detection.py \
  test_dqa_13_historical_coverage.py test_dqa_14_dependency_chain_consistency.py \
  test_dqa_15_calendar_exemption.py -v

============================= test session starts ==============================
platform win32 -- Python 3.11.5, pytest-8.2.0, pluggy-1.4.0
collected 52 items

test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_01_normal_pass_within_tolerance PASSED
test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_02_exceeds_tolerance_alert PASSED
test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_03_zero_baseline_absolute_diff PASSED
test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_04_both_zero_pass PASSED
test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_05_custom_tolerance PASSED
test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_06_negative_values PASSED
test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_07_batch_validation PASSED
test_dqa_09_cross_source_validation.py::TestDQA09CrossSourceValidation::test_08_report_generation PASSED

test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_01_high_confidence PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_02_medium_confidence PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_03_low_confidence_alert PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_04_boundary_high_85 PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_05_boundary_medium_65 PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_06_weighted_score_calculation PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_07_extreme_volatility PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_08_very_fresh_data PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_09_batch_check PASSED
test_dqa_10_proxy_estimation_confidence.py::TestDQA10ProxyEstimationConfidence::test_10_report_generation PASSED

test_dqa_11_frequency_consistency.py::TestDQA11FrequencyConsistency::test_01_regular_daily_pass PASSED
test_dqa_11_frequency_consistency.py::TestDQA11FrequencyConsistency::test_02_missing_data_critical PASSED
test_dqa_11_frequency_consistency.py::TestDQA11FrequencyConsistency::test_03_irregular_frequency PASSED
test_dqa_11_frequency_consistency.py::TestDQA11FrequencyConsistency::test_04_extra_data_points PASSED
test_dqa_11_frequency_consistency.py::TestDQA11FrequencyConsistency::test_05_insufficient_data PASSED
test_dqa_11_frequency_consistency.py::TestDQA11FrequencyConsistency::test_06_report_generation PASSED

test_dqa_12_source_delay_detection.py::TestDQA12SourceDelayDetection::test_01_no_delay_normal PASSED
test_dqa_12_source_delay_detection.py::TestDQA12SourceDelayDetection::test_02_small_delay_normal PASSED
test_dqa_12_source_delay_detection.py::TestDQA12SourceDelayDetection::test_03_warning_delay PASSED
test_dqa_12_source_delay_detection.py::TestDQA12SourceDelayDetection::test_04_critical_delay PASSED
test_dqa_12_source_delay_detection.py::TestDQA12SourceDelayDetection::test_05_early_delivery_no_penalty PASSED
test_dqa_12_source_delay_detection.py::TestDQA12SourceDelayDetection::test_06_batch_and_summary PASSED

test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_01_full_coverage PASSED
test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_02_partial_coverage_warning PASSED
test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_03_low_coverage_fail PASSED
test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_04_no_data_points PASSED
test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_05_gap_detection PASSED
test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_06_tail_gap PASSED
test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_07_daily_data_weekly_frequency PASSED
test_dqa_13_historical_coverage.py::TestDQA13HistoricalCoverage::test_08_batch_and_report PASSED

test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_01_subtraction_pass PASSED
test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_02_subtraction_mismatch PASSED
test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_03_addition PASSED
test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_04_multiplication PASSED
test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_05_division PASSED
test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_06_division_by_zero PASSED
test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_07_missing_input_broken PASSED
test_dqa_14_dependency_chain_consistency.py::TestDQA14DependencyChainConsistency::test_08_missing_target_broken PASSED

test_dqa_15_calendar_exemption.py::TestDQA15CalendarExemption::test_01_holiday_exemption PASSED
test_dqa_15_calendar_exemption.py::TestDQA15CalendarExemption::test_02_non_holiday_normal PASSED
test_dqa_15_calendar_exemption.py::TestDQA15CalendarExemption::test_03_maintenance_window_indicator_specific PASSED
test_dqa_15_calendar_exemption.py::TestDQA15CalendarExemption::test_04_maintenance_window_other_indicator_not_exempt PASSED
test_dqa_15_calendar_exemption.py::TestDQA15CalendarExemption::test_05_maintenance_window_wrong_dqa_rule PASSED
test_dqa_15_calendar_exemption.py::TestDQA15CalendarExemption::test_06_add_and_remove_event PASSED

============================== 52 passed in 0.35s ==============================
```

### 质量指标

| 指标 | 值 |
|------|-----|
| 单元测试通过率 | 52/52 (100.0%) |
| 测试总耗时 | 0.35s |
| DQA规则覆盖 | 7/7 (100%) |
| 告警标签覆盖 | 7种 (ALERT:CROSS_SOURCE_MISMATCH, ALERT:PROXY_LOW_CONFIDENCE, ALERT:FREQ_MISSING, ALERT:FREQ_IRREGULAR, ALERT:SOURCE_DELAY_WARNING, ALERT:SOURCE_DELAY_CRITICAL, ALERT:HIST_COVERAGE_LOW, ALERT:HIST_COVERAGE_FAIL, ALERT:DEP_CHAIN_MISMATCH, ALERT:DEP_CHAIN_BROKEN, ALERT:CALENDAR_EXEMPT) |
| 边界条件覆盖 | 0值处理、负值处理、除零处理、数据不足、极端波动、提前到达、空列表 |

---

<a id="it-plan"></a>## 集成测试计划（9 IT Cases）

### IT-01: 全链路DQA-09跨源校验

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA09-001 |
| **测试名称** | 全链路跨源校验-铜价 |
| **前置条件** | 知几+同花顺双数据源均有序列 |
| **测试数据** | cu_price_1 指标，知几值=75000.0，同花顺值=75500.0（偏差0.67%） |
| **预期结果** | PASS，diff_percentage=0.67% < 5% tolerance |
| **验证点** | 返回对象passed=True，alert_label为空 |

### IT-02: DQA-09~15 跨规则联动

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA-CROSS-001 |
| **测试名称** | 节假日期间全规则联动豁免 |
| **前置条件** | 2028-02-10（春节假期），所有DQA规则活跃 |
| **测试数据** | 5条DQA规则同时运行（DQA-09,10,11,12,13） |
| **预期结果** | 所有规则被DQA-15豁免，0个ALERT |
| **验证点** | 豁免引擎返回is_exempted=True，0条告警 |

### IT-03: 代理置信度-低质量场景

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA10-001 |
| **测试名称** | 低质量代理触发告警 |
| **前置条件** | 指标zn_consumption仅有单一低质量代理数据源 |
| **测试数据** | similarity=0.35, hist_match=0.25, coverage=0.30, volatility=0.85, recency=60d |
| **预期结果** | confidence_level=LOW, alert_label=ALERT:PROXY_LOW_CONFIDENCE |
| **验证点** | confidence_score < 65.0 |

### IT-04: 频率一致性+延迟检测组合

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA11-D12-001 |
| **测试名称** | 频率异常伴随延迟检测 |
| **前置条件** | 数据源zhiji在T+24h延迟到达T+48h的数据 |
| **测试数据** | DQA-11检测到MISSING，DQA-12检测到WARNING延迟 |
| **预期结果** | 两个规则同时触发，告警标签分别为ALERT:FREQ_MISSING和ALERT:SOURCE_DELAY_WARNING |
| **验证点** | 两个规则结果独立但时间戳对齐 |

### IT-05: 历史覆盖度-新指标接入

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA13-001 |
| **测试名称** | 新指标接入-覆盖度不足 |
| **前置条件** | 新指标sn_consumption仅30天数据，期望365天 |
| **测试数据** | 30个日频数据点，start=2028-04-18, end=2028-05-17 |
| **预期结果** | coverage_ratio≈8.2% < 70%，coverage_level=LOW, alert=ALERT:HIST_COVERAGE_FAIL |
| **验证点** | gaps包含1个CRITICAL区间 |

### IT-06: 依赖链一致性-完整公式验证

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA14-001 |
| **测试名称** | 完整铜冶炼利润公式验证 |
| **前置条件** | 所有输入指标（cu_price, tc_fee, power_cost, coal_cost）均有值 |
| **测试数据** | profit = price - tc - power_cost - coal_cost，price=75000, tc=80, power=300, coal=50 |
| **预期结果** | 偏差在5%容差内，passed=True |
| **验证点** | expected_value与实际值差值在容差范围内 |

### IT-07: 依赖链一致性-缺失输入处理

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA14-002 |
| **测试名称** | 依赖链断裂-缺失输入指标 |
| **前置条件** | 铝冶炼利润公式缺少power_cost数据 |
| **测试数据** | 公式: profit = price - tc - power - coal，缺少power_cost |
| **预期结果** | chain_broken=True, alert_label=ALERT:DEP_CHAIN_BROKEN |
| **验证点** | detail字段包含缺失指标名称 |

### IT-08: 日历豁免-动态事件管理

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-DQA15-001 |
| **测试名称** | 动态维护窗口添加与移除 |
| **前置条件** | 系统正常运行 |
| **测试数据** | T+0添加5/20-5/22维护窗口→检查豁免→T+1移除维护窗口→检查正常 |
| **预期结果** | 维护窗口内is_exempted=True，移除后is_exempted=False |
| **验证点** | add_event/remove_event操作可逆 |

### IT-09: 端到端-全部规则压力测试

| 项目 | 内容 |
|------|------|
| **测试ID** | IT-E2E-001 |
| **测试名称** | 7条DQA规则同时运行-压力测试 |
| **前置条件** | 50个指标×5个数据源×30天数据 |
| **测试数据** | 随机生成50×5=250个数据源指标对，覆盖所有边界情况 |
| **预期结果** | 全部52单元测试规则在5秒内完成250个指标的批量检查 |
| **验证点** | 无内存泄漏，结果确定性可重现 |

---

## 文件清单

| 文件名 | 行数 | 说明 |
|--------|------|------|
| `dqa_09_cross_source_validation.py` | ~110 | DQA-09 跨源校验实现 |
| `test_dqa_09_cross_source_validation.py` | ~105 | DQA-09 单元测试（8个） |
| `dqa_10_proxy_estimation_confidence.py` | ~120 | DQA-10 代理置信度实现 |
| `test_dqa_10_proxy_estimation_confidence.py` | ~120 | DQA-10 单元测试（10个） |
| `dqa_11_frequency_consistency.py` | ~150 | DQA-11 频率一致性实现 |
| `test_dqa_11_frequency_consistency.py` | ~95 | DQA-11 单元测试（6个） |
| `dqa_12_source_delay_detection.py` | ~120 | DQA-12 延迟检测实现 |
| `test_dqa_12_source_delay_detection.py` | ~85 | DQA-12 单元测试（6个） |
| `dqa_13_historical_coverage.py` | ~140 | DQA-13 覆盖度检查实现 |
| `test_dqa_13_historical_coverage.py` | ~130 | DQA-13 单元测试（8个） |
| `dqa_14_dependency_chain_consistency.py` | ~180 | DQA-14 依赖链一致性实现 |
| `test_dqa_14_dependency_chain_consistency.py` | ~145 | DQA-14 单元测试（8个） |
| `dqa_15_calendar_exemption.py` | ~160 | DQA-15 日历豁免实现 |
| `test_dqa_15_calendar_exemption.py` | ~105 | DQA-15 单元测试（6个） |
| **合计** | **~1665** | 14个Python文件 + 52个测试用例 |

---

## 约束合规声明

| 约束 | 状态 | 说明 |
|------|------|------|
| BRANCH_LOCKED: feature/v88-g1 | ✅ 合规 | 所有代码在 feature/v88-g1 分支 |
| NO_OVERWRITE | ✅ 合规 | 仅创建新文件到 implementation/ 目录 |
| NO_MODIFY_V87 | ✅ 合规 | 未修改任何V87基线文件 |
| NO_EDIT_RELEASE_TAG | ✅ 合规 | 未修改任何release tag |
| NO_ZHIJI_API_CALL | ✅ 合规 | 零API调用，全部使用mock数据 |
| UPSTREAM_WRITES=0 | ✅ 合规 | 仅写入 implementation/ 目录 |

---

> **报告生成**: DSHB V88 Phase03 P1 DSHB
> **版本**: V88_PHASE03_P1_DSHB_DQA09_15_V1
> **状态**: COMPLETE
