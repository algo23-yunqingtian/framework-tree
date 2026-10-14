#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_e2e_render.py - V88 End-to-End Rendering Test
==================================================
TASK_ID: V88_PHASE01_DSHE_P1_NODE_BINDING_ADAPT
AGENT: DSHE
BRANCH: feature/v88-g1
PURPOSE: E2E rendering test with DSHB simulated data for 16 pending charts

Test flow:
  1. Initialize engine + load metadata
  2. Simulate DSHB data feed for all pending indicators
  3. Render all 16 pending charts with simulated data
  4. Validate rendering output (non-empty, correct structure)
  5. Test full pipeline: binding -> data -> render -> verify
"""

import json
import os
import sys
import time
import unittest
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from node_binding_engine import NodeBindingEngine, ChartBinding


def make_engine():
    e = NodeBindingEngine(repo_root=REPO_ROOT)
    ok, msg = e.load()
    assert ok, "Engine load failed: " + msg
    e.validate(strict=False)
    e.resolve_all()
    return e


class TestE2E_Rendering(unittest.TestCase):
    """E2E rendering tests for all 101 charts"""

    def setUp(self):
        self.e = make_engine()
        self.t0 = time.time()

    def test_01_engine_init(self):
        """T01: Engine initialization - 101 charts, 33 nodes, 9 commodities"""
        self.assertEqual(len(self.e.charts), 101)
        self.assertEqual(len(self.e.node_index), 33)
        self.assertEqual(len(self.e.commodity_index), 9)
        print("  [T01] Engine init: 101 charts, 33 nodes, 9 commodities")

    def test_02_validation_all_pass(self):
        """T02: Validation - 614 checks, 0 ERROR, 0 WARN"""
        errors = [r for r in self.e.validation_results if r.severity == "ERROR"]
        warns = [r for r in self.e.validation_results if r.severity == "WARN"]
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warns), 0)
        self.assertEqual(len(self.e.validation_results), 614)
        print("  [T02] Validation: 614 checks, 0 ERROR, 0 WARN")

    def test_03_binding_resolution_all(self):
        """T03: Binding resolution - all 101 charts resolved"""
        for cb in self.e.charts:
            self.assertIsNotNone(cb.resolved_node)
            self.assertNotIn("error", cb.resolved_node)
            self.assertIsNotNone(cb.resolved_commodity)
            self.assertNotIn("error", cb.resolved_commodity)
        print("  [T03] Binding resolution: 101/101 resolved")

    def test_04_render_all_matchable(self):
        """T04: Render all 85 matchable charts"""
        results = []
        for cb in self.e.get_matchable_charts():
            r = self.e.render_chart(cb.chart_id, use_simulated=True)
            self.assertNotIn("error", r, cb.chart_id + " render failed")
            self.assertTrue(r["renderable"])
            self.assertIn(r["source"], ["real", "simulated"])
            results.append(r)
        self.assertEqual(len(results), 85)
        print("  [T04] Matchable render: 85/85 OK")

    def test_05_render_all_pending_with_simulated(self):
        """T05: Render all 16 pending charts with simulated data"""
        results = []
        for cb in self.e.get_pending_charts():
            r = self.e.render_chart(cb.chart_id, use_simulated=True)
            self.assertNotIn("error", r, cb.chart_id + " render failed")
            self.assertTrue(r["renderable"])
            self.assertEqual(r["source"], "simulated")
            # Verify data structure
            self.assertGreater(len(r["render_data"]), 0)
            for d in r["render_data"]:
                self.assertIn("points", d)
                self.assertGreater(len(d["points"]), 0)
                self.assertIn("date", d["points"][0])
                self.assertIn("value", d["points"][0])
            results.append(r)
        self.assertEqual(len(results), 16)
        print("  [T05] Pending render (simulated): 16/16 OK")

    def test_06_render_all_pending_with_placeholder(self):
        """T06: Render all 16 pending charts with placeholder (no simulated)"""
        results = []
        for cb in self.e.get_pending_charts():
            r = self.e.render_chart(cb.chart_id, use_simulated=False)
            self.assertNotIn("error", r)
            self.assertTrue(r["renderable"])
            self.assertEqual(r["source"], "placeholder")
            self.assertTrue(r["placeholder"])
            results.append(r)
        self.assertEqual(len(results), 16)
        print("  [T06] Pending render (placeholder): 16/16 OK")

    def test_07_render_with_fallback_all(self):
        """T07: Render all 101 charts with fallback (real -> simulated -> placeholder)"""
        for cb in self.e.charts:
            r = self.e.render_with_fallback(cb.chart_id)
            self.assertNotIn("error", r, cb.chart_id + " fallback failed")
            self.assertTrue(r["renderable"])
        print("  [T07] Fallback render: 101/101 OK")

    def test_08_render_all_batch(self):
        """T08: Batch render all charts with render_all()"""
        results = self.e.render_all(use_simulated=True)
        self.assertEqual(len(results["errors"]), 0)
        self.assertEqual(len(results["matchable"]), 85)
        self.assertEqual(len(results["pending_data"]), 16)
        print("  [T08] Batch render: 85 matchable + 16 pending = 101, 0 errors")

    def test_09_pending_render_chain_verify(self):
        """T09: Verify pending render chain (binding + simulated + placeholder + fallback)"""
        results = self.e.verify_pending_render_chain()
        self.assertEqual(results["total_pending"], 16)
        self.assertEqual(results["binding_resolved"], 16)
        self.assertEqual(results["simulated_data_ok"], 16)
        self.assertEqual(results["placeholder_ok"], 16)
        self.assertEqual(results["fallback_ok"], 16)
        self.assertEqual(len(results["errors"]), 0)
        self.assertEqual(results["success_rate"], 100.0)
        print("  [T09] Pending chain: 16/16 all OK, success_rate=100%")

    def test_10_node_switching_render(self):
        """T10: Node switching then render - verify rendering works after switch"""
        # Switch cu_p1_ts_01 from p1 to p2
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        orig_node = cb.tree_node_id
        success, msg = self.e.switch_node("cu_p1_ts_01", "p2")
        self.assertTrue(success)
        self.assertEqual(cb.tree_node_id, "p2")

        # Render after switch
        r = self.e.render_with_fallback("cu_p1_ts_01")
        self.assertNotIn("error", r)
        self.assertTrue(r["renderable"])

        # Switch back
        self.e.switch_node("cu_p1_ts_01", orig_node)
        print("  [T10] Node switch render: OK")

    def test_11_indicator_mount_render(self):
        """T11: Mount indicator then render"""
        cb = self.e.get_chart_binding("cu_p1_ts_01")
        orig_count = len(cb.indicators)

        # Mount new indicator
        success, msg = self.e.mount_indicator("cu_p1_ts_01", "e2e_test", "E2E_TEST_IND")
        self.assertTrue(success)
        self.assertEqual(len(cb.indicators), orig_count + 1)

        # Render after mount
        r = self.e.render_with_fallback("cu_p1_ts_01")
        self.assertNotIn("error", r)
        self.assertTrue(r["renderable"])

        # Unmount
        self.e.unmount_indicator("cu_p1_ts_01", "E2E_TEST_IND")
        print("  [T11] Indicator mount render: OK")

    def test_12_render_data_structure(self):
        """T12: Verify rendered data structure for all chart types"""
        type_checks = Counter()
        for cb in self.e.charts:
            r = self.e.render_with_fallback(cb.chart_id)
            self.assertIn("chart_id", r)
            self.assertIn("title", r)
            self.assertIn("chart_type", r)
            self.assertIn("data_status", r)
            self.assertIn("render_data", r)
            self.assertIn("source", r)
            self.assertIn("renderable", r)
            type_checks[cb.chart_type] += 1

        # Verify all chart types covered
        self.assertIn("time_series", type_checks)
        self.assertIn("gauge", type_checks)
        self.assertIn("stacked_bar", type_checks)
        self.assertIn("heatmap", type_checks)
        print("  [T12] Data structure: " + str(dict(type_checks)))

    def test_13_render_timing(self):
        """T13: Verify rendering completes within acceptable time"""
        t0 = time.time()
        for cb in self.e.charts:
            r = self.e.render_with_fallback(cb.chart_id)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 5.0, "Rendering took too long: " + str(elapsed))
        print("  [T13] Render timing: " + str(round(elapsed, 3)) + "s for 101 charts")

    def test_14_full_pipeline_summary(self):
        """T14: Full pipeline summary - aggregate results"""
        stats = self.e.get_stats()
        self.assertEqual(stats["total_charts"], 101)
        self.assertEqual(stats["data_status"]["matchable"], 85)
        self.assertEqual(stats["data_status"]["pending_data"], 16)
        self.assertEqual(stats["total_indicators"], 109)
        self.assertEqual(stats["validation"]["error"], 0)
        self.assertEqual(stats["validation"]["warn"], 0)
        self.assertEqual(stats["validation"]["pass"], 614)
        print("  [T14] Pipeline summary:")
        print("       Charts: " + str(stats["total_charts"]))
        print("       Matchable: " + str(stats["data_status"]["matchable"]))
        print("       Pending: " + str(stats["data_status"]["pending_data"]))
        print("       Indicators: " + str(stats["total_indicators"]))
        print("       Validation: " + str(stats["validation"]))


if __name__ == "__main__":
    print("=" * 70)
    print("V88 Node Binding Engine - E2E Rendering Test")
    print("=" * 70)
    print("REPO_ROOT:", REPO_ROOT)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestE2E_Rendering))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("ALL E2E TESTS PASSED")
        print("  Tests run:", result.testsRun)
    else:
        print("E2E TESTS FAILED")
        print("  Tests run:", result.testsRun)
        print("  Failures:", len(result.failures))
        print("  Errors:", len(result.errors))
    print("=" * 70)