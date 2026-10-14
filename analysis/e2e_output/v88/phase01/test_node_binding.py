#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_node_binding.py - V88 Node Binding engine unit tests
========================================================
TASK_ID: V88_PHASE01_DSHE_P1_NODE_BINDING_ADAPT
AGENT: DSHE
BRANCH: feature/v88-g1
PURPOSE: verify node switching, indicator mount/unmount, render fallback, binding resolution

Test matrix:
  T1: Basic load + index build
  T2: 6 validation rules
  T3: node_binding resolution
  T4: Node switching (normal + error)
  T5: Indicator mount/unmount (normal + error)
  T6: Render fallback (matchable -> simulated -> placeholder)
  T7: 16 pending charts render chain
  T8: Data status split
  T9: Chart query interface
  T10: Negative tests
"""

import json
import os
import sys
import unittest
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from node_binding_engine import (
    NodeBindingEngine, ValidationResult, ChartBinding,
    VALID_CHART_TYPES, VALID_DATA_STATUSES,
)


def make_engine():
    """Create a fresh engine instance (each test class gets its own)."""
    e = NodeBindingEngine(repo_root=REPO_ROOT)
    ok, msg = e.load()
    assert ok, "Engine load failed: " + msg
    e.validate(strict=False)
    e.resolve_all()
    return e


# ===========================================================================
# T1: Basic Load + Index
# ===========================================================================
class TestT1_LoadAndIndex(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_load_success(self):
        self.assertIsNotNone(self.e)
        self.assertGreater(len(self.e.charts), 0)

    def test_load_time_recorded(self):
        self.assertIsNotNone(self.e.load_time)
        self.assertGreater(self.e.load_time, 0)

    def test_chart_count(self):
        self.assertEqual(len(self.e.charts), 101)

    def test_node_index_built(self):
        self.assertEqual(len(self.e.node_index), 33)

    def test_commodity_index_built(self):
        self.assertEqual(len(self.e.commodity_index), 9)

    def test_chart_index_built(self):
        self.assertEqual(len(self.e.chart_index), 101)

    def test_all_chart_ids_unique(self):
        ids = [cb.chart_id for cb in self.e.charts]
        self.assertEqual(len(ids), len(set(ids)))


# ===========================================================================
# T2: 6 Validation Rules
# ===========================================================================
class TestT2_ValidationRules(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_total_validation_results(self):
        self.assertEqual(len(self.e.validation_results), 614)

    def test_zero_errors(self):
        errors = [r for r in self.e.validation_results if r.severity == "ERROR"]
        self.assertEqual(len(errors), 0)

    def test_all_rules_executed(self):
        rule_ids = set(r.rule_id for r in self.e.validation_results)
        expected = {"no_cross_node_binding", "tree_node_id_valid", "commodity_valid",
                    "auto_inherit_description", "chart_type_valid", "data_status_valid"}
        self.assertEqual(rule_ids, expected)

    def test_each_chart_has_results(self):
        chart_ids = {cb.chart_id for cb in self.e.charts}
        validated_ids = {r.chart_id for r in self.e.validation_results}
        self.assertEqual(chart_ids, validated_ids)

    def test_chart_type_valid_all_pass(self):
        rule5 = [r for r in self.e.validation_results if r.rule_id == "chart_type_valid"]
        self.assertEqual(len(rule5), 101)
        self.assertTrue(all(r.severity == "PASS" for r in rule5))

    def test_data_status_valid_all_pass(self):
        rule6 = [r for r in self.e.validation_results if r.rule_id == "data_status_valid"]
        self.assertEqual(len(rule6), 101)
        self.assertTrue(all(r.severity == "PASS" for r in rule6))

    def test_tree_node_id_valid_all_pass(self):
        rule2 = [r for r in self.e.validation_results if r.rule_id == "tree_node_id_valid"]
        self.assertEqual(len(rule2), 101)
        self.assertTrue(all(r.severity == "PASS" for r in rule2))

    def test_commodity_valid_all_pass(self):
        rule3 = [r for r in self.e.validation_results if r.rule_id == "commodity_valid"]
        self.assertEqual(len(rule3), 101)
        self.assertTrue(all(r.severity == "PASS" for r in rule3))


# ===========================================================================
# T3: node_binding Resolution
# ===========================================================================
class TestT3_NodeBindingResolution(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_resolve_single_chart(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.assertIsNotNone(cb)
        self.assertIsNotNone(cb.resolved_node)
        self.assertNotIn("error", cb.resolved_node)
        self.assertEqual(cb.resolved_node["id"], "p1")

    def test_resolve_node_has_comms(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.assertIn("comms", cb.resolved_node)
        self.assertIsInstance(cb.resolved_node["comms"], list)
        self.assertGreater(len(cb.resolved_node["comms"]), 0)

    def test_resolve_commodity(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.assertIsNotNone(cb.resolved_commodity)
        self.assertNotIn("error", cb.resolved_commodity)
        self.assertEqual(cb.resolved_commodity["code"], "CU")

    def test_resolve_indicators(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.assertGreater(len(cb.resolved_indicators), 0)

    def test_business_description_auto_inherit(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        node = self.e.node_index["p1"]
        expected = node["name"] + "(" + node["q"] + ")"
        self.assertEqual(cb.business_description, expected)

    def test_resolve_all_charts(self):
        count = self.e.resolve_all()
        self.assertEqual(count, 101)
        for cb in self.e.charts:
            self.assertIsNotNone(cb.resolved_node)

    def test_get_chart_binding_not_found(self):
        cb = self.e.get_chart_binding("nonexistent_chart")
        self.assertIsNone(cb)


# ===========================================================================
# T4: Node Switching
# ===========================================================================
class TestT4_NodeSwitching(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_switch_node_success(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.assertEqual(cb.tree_node_id, "p1")
        success, msg = self.e.switch_node("cu_p1_ts_01", "p2")
        self.assertTrue(success)
        self.assertIn("p1", msg)
        self.assertIn("p2", msg)

    def test_switch_node_updates_tree_node_id(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.e.switch_node("cu_p1_ts_01", "p2")
        self.assertEqual(cb.tree_node_id, "p2")

    def test_switch_node_updates_business_description(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.e.switch_node("cu_p1_ts_01", "p3")
        node_p3 = self.e.node_index["p3"]
        expected = node_p3["name"] + "(" + node_p3["q"] + ")"
        self.assertEqual(cb.business_description, expected)

    def test_switch_node_invalid_node(self):
        success, msg = self.e.switch_node("cu_p1_ts_01", "invalid_node")
        self.assertFalse(success)
        self.assertIn("not registered", msg.lower())

    def test_switch_node_nonexistent_chart(self):
        success, msg = self.e.switch_node("nonexistent", "p1")
        self.assertFalse(success)
        self.assertIn("not found", msg.lower())

    def test_switch_node_restores_binding(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        self.e.switch_node("cu_p1_ts_01", "p3")
        self.assertEqual(cb.tree_node_id, "p3")
        self.assertEqual(cb.resolved_node["id"], "p3")


# ===========================================================================
# T5: Indicator Mount / Unmount
# ===========================================================================
class TestT5_IndicatorMount(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_mount_indicator_success(self):
        success, msg = self.e.mount_indicator("cu_p1_ts_01", "test_ind", "TEST_IND_001")
        self.assertTrue(success)
        self.assertIn("mounted", msg.lower())

    def test_mount_indicator_adds_to_list(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        before = len(cb.indicators)
        self.e.mount_indicator("cu_p1_ts_01", "test_ind", "TEST_IND_002")
        after = len(cb.indicators)
        self.assertEqual(after, before + 1)

    def test_mount_indicator_duplicate_rejected(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        ind_id = cb.indicators[0]["indicator_id"]
        ind_name = cb.indicators[0]["indicator_name"]
        success, msg = self.e.mount_indicator("cu_p1_ts_01", ind_name, ind_id)
        self.assertFalse(success)
        self.assertIn("already", msg.lower())

    def test_mount_indicator_empty_rejected(self):
        success, msg = self.e.mount_indicator("cu_p1_ts_01", "", "TEST_IND_003")
        self.assertFalse(success)
        success, msg = self.e.mount_indicator("cu_p1_ts_01", "name", "")
        self.assertFalse(success)

    def test_mount_indicator_nonexistent_chart(self):
        success, msg = self.e.mount_indicator("nonexistent", "name", "ID_001")
        self.assertFalse(success)
        self.assertIn("not found", msg.lower())

    def test_unmount_indicator_success(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        ind_id = cb.indicators[0]["indicator_id"]
        success, msg = self.e.unmount_indicator("cu_p1_ts_01", ind_id)
        self.assertTrue(success)
        self.assertIn("removed", msg.lower())

    def test_unmount_indicator_removes_from_list(self):
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        before = len(cb.indicators)
        ind_id = cb.indicators[0]["indicator_id"]
        self.e.unmount_indicator("cu_p1_ts_01", ind_id)
        after = len(cb.indicators)
        self.assertEqual(after, before - 1)

    def test_unmount_indicator_not_found(self):
        success, msg = self.e.unmount_indicator("cu_p1_ts_01", "NONEXISTENT_IND")
        self.assertFalse(success)
        self.assertIn("not found", msg.lower())


# ===========================================================================
# T6: Render Fallback
# ===========================================================================
class TestT6_RenderFallback(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_render_matchable_with_simulated(self):
        result = self.e.render_chart("cu_p1_ts_01", use_simulated=True)
        self.assertNotIn("error", result)
        self.assertTrue(result["renderable"])
        self.assertIn(result["source"], ["real", "simulated"])

    def test_render_pending_data_with_simulated(self):
        result = self.e.render_chart("cu_p4_ts_02", use_simulated=True)
        self.assertNotIn("error", result)
        self.assertTrue(result["renderable"])
        self.assertEqual(result["source"], "simulated")
        self.assertFalse(result["placeholder"])

    def test_render_pending_data_without_simulated(self):
        result = self.e.render_chart("cu_p4_ts_02", use_simulated=False)
        self.assertNotIn("error", result)
        self.assertTrue(result["renderable"])
        self.assertEqual(result["source"], "placeholder")
        self.assertTrue(result["placeholder"])

    def test_render_with_fallback_always_renderable(self):
        for chart_id in ["cu_p1_ts_01", "cu_p4_ts_02"]:
            result = self.e.render_with_fallback(chart_id)
            self.assertNotIn("error", result)
            self.assertTrue(result["renderable"])

    def test_render_deprecated_returns_error(self):
        cb = ChartBinding({
            "chart_id": "test_deprecated",
            "tree_node_id": "p1",
            "commodity": "cu",
            "chart_type": "time_series",
            "data_status": "deprecated",
            "indicators": [{"indicator_id": "TEST", "indicator_name": "test"}],
        })
        self.e.chart_index["test_deprecated"] = cb
        self.e.charts.append(cb)
        result = self.e.render_chart("test_deprecated")
        self.assertIn("error", result)
        self.assertIn("deprecated", result["error"])

    def test_render_nonexistent_chart(self):
        result = self.e.render_chart("nonexistent_chart")
        self.assertIn("error", result)

    def test_render_simulated_data_has_points(self):
        result = self.e.render_chart("cu_p4_ts_02", use_simulated=True)
        self.assertGreater(len(result["render_data"]), 0)
        for d in result["render_data"]:
            self.assertIn("points", d)
            self.assertGreater(len(d["points"]), 0)


# ===========================================================================
# T7: Pending Render Chain (16 pending charts)
# ===========================================================================
class TestT7_PendingRenderChain(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_pending_chart_count(self):
        pending = self.e.get_pending_charts()
        self.assertEqual(len(pending), 16)

    def test_verify_pending_render_chain(self):
        results = self.e.verify_pending_render_chain()
        self.assertEqual(results["total_pending"], 16)
        self.assertEqual(results["binding_resolved"], 16)
        self.assertEqual(results["simulated_data_ok"], 16)
        self.assertEqual(results["placeholder_ok"], 16)
        self.assertEqual(results["fallback_ok"], 16)
        self.assertEqual(len(results["errors"]), 0)
        self.assertEqual(results["success_rate"], 100.0)

    def test_each_pending_chart_detail(self):
        results = self.e.verify_pending_render_chain()
        for detail in results["detail"]:
            self.assertEqual(detail["binding"], "OK")
            self.assertEqual(detail["simulated_data"], "OK")
            self.assertEqual(detail["placeholder"], "OK")
            self.assertEqual(detail["fallback"], "OK")


# ===========================================================================
# T8: Data Status Split
# ===========================================================================
class TestT8_DataStatusSplit(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_matchable_count(self):
        matchable = self.e.get_matchable_charts()
        self.assertEqual(len(matchable), 85)

    def test_pending_count(self):
        pending = self.e.get_pending_charts()
        self.assertEqual(len(pending), 16)

    def test_render_all_no_errors(self):
        results = self.e.render_all(use_simulated=True)
        self.assertEqual(len(results["errors"]), 0)

    def test_render_all_counts(self):
        results = self.e.render_all(use_simulated=True)
        self.assertEqual(len(results["matchable"]), 85)
        self.assertEqual(len(results["pending_data"]), 16)

    def test_all_matchable_renderable(self):
        for cb in self.e.get_matchable_charts():
            result = self.e.render_chart(cb.chart_id, use_simulated=True)
            self.assertNotIn("error", result, cb.chart_id + " render failed")
            self.assertTrue(result["renderable"])


# ===========================================================================
# T9: Query Interface
# ===========================================================================
class TestT9_QueryInterface(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_get_charts_by_node(self):
        charts = self.e.get_charts_by_node("p1")
        self.assertEqual(len(charts), 24)
        for cb in charts:
            self.assertEqual(cb.tree_node_id, "p1")

    def test_get_charts_by_commodity(self):
        charts = self.e.get_charts_by_commodity("cu")
        self.assertGreater(len(charts), 15)
        for cb in charts:
            self.assertEqual(cb.commodity, "cu")

    def test_get_charts_by_type(self):
        charts = self.e.get_charts_by_type("time_series")
        self.assertGreater(len(charts), 70)
        for cb in charts:
            self.assertEqual(cb.chart_type, "time_series")

    def test_get_stats(self):
        stats = self.e.get_stats()
        self.assertEqual(stats["total_charts"], 101)
        self.assertEqual(stats["validation"]["error"], 0)
        self.assertEqual(stats["validation"]["warn"], 0)
        self.assertEqual(stats["validation"]["pass"], 614)

    def test_get_stats_data_status(self):
        stats = self.e.get_stats()
        self.assertEqual(stats["data_status"]["matchable"], 85)
        self.assertEqual(stats["data_status"]["pending_data"], 16)


# ===========================================================================
# T10: Negative Tests
# ===========================================================================
class TestT10_NegativeTests(unittest.TestCase):
    def setUp(self):
        self.e = make_engine()

    def test_invalid_node_id_rejected(self):
        cb = ChartBinding({
            "chart_id": "neg_invalid_node",
            "tree_node_id": "invalid_node_999",
            "commodity": "cu",
            "chart_type": "time_series",
            "data_status": "matchable",
            "indicators": [{"indicator_id": "X", "indicator_name": "X"}],
        })
        self.e._rule_tree_node_id_valid(cb)
        last = self.e.validation_results[-1]
        self.assertEqual(last.rule_id, "tree_node_id_valid")
        self.assertEqual(last.severity, "ERROR")

    def test_invalid_commodity_rejected(self):
        cb = ChartBinding({
            "chart_id": "neg_invalid_comm",
            "tree_node_id": "p1",
            "commodity": "invalid_comm",
            "chart_type": "time_series",
            "data_status": "matchable",
            "indicators": [{"indicator_id": "X", "indicator_name": "X"}],
        })
        self.e._rule_commodity_valid(cb)
        last = self.e.validation_results[-1]
        self.assertEqual(last.rule_id, "commodity_valid")
        self.assertEqual(last.severity, "ERROR")

    def test_invalid_chart_type_rejected(self):
        cb = ChartBinding({
            "chart_id": "neg_invalid_type",
            "tree_node_id": "p1",
            "commodity": "cu",
            "chart_type": "invalid_type",
            "data_status": "matchable",
            "indicators": [{"indicator_id": "X", "indicator_name": "X"}],
        })
        self.e._rule_chart_type_valid(cb)
        last = self.e.validation_results[-1]
        self.assertEqual(last.rule_id, "chart_type_valid")
        self.assertEqual(last.severity, "ERROR")

    def test_invalid_data_status_rejected(self):
        cb = ChartBinding({
            "chart_id": "neg_invalid_status",
            "tree_node_id": "p1",
            "commodity": "cu",
            "chart_type": "time_series",
            "data_status": "invalid_status",
            "indicators": [{"indicator_id": "X", "indicator_name": "X"}],
        })
        self.e._rule_data_status_valid(cb)
        last = self.e.validation_results[-1]
        self.assertEqual(last.rule_id, "data_status_valid")
        self.assertEqual(last.severity, "ERROR")

    def test_cross_node_binding_rejected(self):
        cb = ChartBinding({
            "chart_id": "neg_cross_node",
            "tree_node_id": "p1",
            "commodity": "cu",
            "chart_type": "time_series",
            "data_status": "matchable",
            "indicators": [{"indicator_id": "X", "indicator_name": "X", "commodity": "invalid_comm"}],
        })
        self.e._rule_no_cross_node_binding(cb)
        last = self.e.validation_results[-1]
        self.assertEqual(last.rule_id, "no_cross_node_binding")
        self.assertEqual(last.severity, "ERROR")


# ===========================================================================
# Main
# ===========================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("V88 Node Binding Engine - Unit Tests")
    print("=" * 70)
    print("REPO_ROOT:", REPO_ROOT)
    print()

    # Init engine for display
    print("[INIT] Initializing engine...")
    e = make_engine()
    print("  load:", len(e.charts), "charts,", len(e.node_index), "nodes")
    print("  validation:", len(e.validation_results), "results")
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestT1_LoadAndIndex,
        TestT2_ValidationRules,
        TestT3_NodeBindingResolution,
        TestT4_NodeSwitching,
        TestT5_IndicatorMount,
        TestT6_RenderFallback,
        TestT7_PendingRenderChain,
        TestT8_DataStatusSplit,
        TestT9_QueryInterface,
        TestT10_NegativeTests,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    test_count = sum(1 for _ in suite)
    print("[RUN] Running", test_count, "test cases...")
    print()

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("ALL TESTS PASSED")
        print("  Tests run:", result.testsRun)
        print("  Failures:", len(result.failures))
        print("  Errors:", len(result.errors))
    else:
        print("TESTS FAILED")
        print("  Tests run:", result.testsRun)
        print("  Failures:", len(result.failures))
        print("  Errors:", len(result.errors))
    print("=" * 70)