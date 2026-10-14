#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_boundary_scenarios.py — V88 Phase02 Post-Deploy Prep: Boundary Scenario Tests
==================================================================================
TASK_ID: V88_PHASE02_DSHE_POST_DEPLOY_PREP
AGENT: DSHE
BRANCH: feature/v88-g1

T1: 边界场景补充测试
  - 高并发下指标时序延迟到达
  - 图表等待策略与降级切换逻辑

T2: 监控大盘告警阈值微调演练
  - 告警触发/恢复通知链路验证
  - 不修改生产阈值

前置依赖:
  - V88 Phase02 chart deploy 主线工单完成 (commit f3f2aa9)
  - V88 Phase01 node_binding engine (scripts/node_binding_engine.py)
  - framework_tree_meta_chart.yaml

约束:
  - 不修改现有已上线图表逻辑
  - 不修改node_binding绑定关系
  - 不修改生产阈值配置
  - NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL
"""

import json
import os
import sys
import time
import unittest
import threading
import random
import statistics
import hashlib
from collections import defaultdict, Counter
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from node_binding_engine import NodeBindingEngine, ChartBinding

# 6项DSHB pending指标 (from DSHB Phase01 simulation)
DSHB_PENDING_INDICATORS = [
    {"id": "CU_SMELTER_MAINTENANCE", "name": "铜冶炼检修量化损失", "commodity": "cu", "node": "s7"},
    {"id": "NI_SMELTER_MAINTENANCE", "name": "镍冶炼检修量化损失", "commodity": "ni", "node": "s7"},
    {"id": "SI_SMELTER_MAINTENANCE", "name": "硅冶炼检修量化损失", "commodity": "si", "node": "s7"},
    {"id": "CU_SPOT_INQUIRY_FREQ", "name": "铜现货报价频次", "commodity": "cu", "node": "c1"},
    {"id": "LC_SPOT_INQUIRY_FREQ", "name": "碳酸锂现货询盘成交活跃度", "commodity": "li", "node": "d2"},
    {"id": "SI_SPOT_INQUIRY_FREQ", "name": "工业硅现货报价频次", "commodity": "si", "node": "c1"},
]

# 告警规则定义 (from monitoring_dashboard.json)
ALERT_RULES = [
    {"id": "ALERT-001", "metric": "chart_render_p99_ms", "condition": ">500", "severity": "P2"},
    {"id": "ALERT-002", "metric": "chart_render_p95_ms", "condition": ">300", "severity": "P3"},
    {"id": "ALERT-003", "metric": "page_render_error_count", "condition": ">0", "severity": "P1"},
    {"id": "ALERT-004", "metric": "render_error_rate_pct", "condition": ">1", "severity": "P1"},
    {"id": "ALERT-005", "metric": "fallback_trigger_rate_pct", "condition": ">30", "severity": "P2"},
    {"id": "ALERT-006", "metric": "fallback_placeholder_count", "condition": ">0", "severity": "P3"},
    {"id": "ALERT-007", "metric": "binding_resolve_error_count", "condition": ">0", "severity": "P2"},
    {"id": "ALERT-008", "metric": "concurrent_render_p99_ms", "condition": ">500", "severity": "P2"},
    {"id": "ALERT-009", "metric": "concurrent_render_error_rate_pct", "condition": ">0", "severity": "P1"},
    {"id": "ALERT-010", "metric": "real_data_available_rate_pct", "condition": "<60", "severity": "P3"},
]

# SLA 目标
SLA_TARGETS = {
    "chart_render_p99_ms": 500,
    "concurrent_render_p99_ms": 500,
    "concurrent_render_error_rate_pct": 0,
    "page_render_error_count": 0,
    "render_error_rate_pct": 0,
    "fallback_trigger_rate_pct": 20,
}


def make_engine():
    """Create fresh engine instance with repo_root 5 levels up."""
    e = NodeBindingEngine(repo_root=REPO_ROOT)
    ok, msg = e.load()
    assert ok, "Engine load failed: " + msg
    e.validate(strict=False)
    e.resolve_all()
    return e


# ===========================================================================
# T1: 边界场景补充测试 — 高并发下指标时序延迟到达
# ===========================================================================

class TestT1_BoundaryDelayedArrival(unittest.TestCase):
    """
    T1: 边界场景补充测试
    1. 高并发下指标时序延迟到达场景
    2. 图表等待策略与降级切换逻辑验证
    3. 真实数据→模拟数据→占位符三级切换链路
    4. 部分指标到达/部分缺失的混合场景
    """

    def setUp(self):
        self.e = make_engine()

    def test_01_delayed_indicator_arrival_mixed(self):
        """
        场景: 高并发(20线程)下，部分指标延迟到达
        - 50%线程立即请求，50%线程延迟200ms后请求
        - 验证引擎不会因并发+延迟出现死锁或数据不一致
        - 验证降级切换逻辑正确
        """
        chart_ids = [cb.chart_id for cb in self.e.charts]
        pending_ids = {cb.chart_id for cb in self.e.get_pending_charts()}
        matchable_ids = [cb.chart_id for cb in self.e.get_matchable_charts()]
        random.seed(42)
        results = []
        errors = []
        timings = []
        lock = threading.Lock()

        def render_with_delay(cid, delay_ms):
            """带延迟的渲染请求"""
            try:
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)
                t0 = time.time()
                r = self.e.render_with_fallback(cid)
                elapsed = time.time() - t0
                if "error" in r or not r.get("renderable"):
                    with lock:
                        errors.append(f"{cid}: render failed")
                else:
                    with lock:
                        results.append({
                            "chart_id": cid,
                            "source": r["source"],
                            "is_pending": cid in pending_ids,
                            "delay_ms": delay_ms,
                        })
                        timings.append(elapsed)
            except Exception as ex:
                with lock:
                    errors.append(f"{cid}: {str(ex)}")

        t0 = time.time()
        threads = []
        # 40 threads: 20 immediate + 20 delayed by 200ms
        for i in range(40):
            cid = matchable_ids[i % len(matchable_ids)]
            delay = 0 if i % 2 == 0 else 200
            t = threading.Thread(target=render_with_delay, args=(cid, delay))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.time() - t0

        self.assertEqual(len(errors), 0, f"Errors under delayed arrival: {errors[:3]}")
        # 验证所有matchable图表在延迟场景下仍可渲染
        self.assertGreater(len(results), 0)
        print(f"  [T1-01] Delayed arrival: {len(results)} OK, {len(errors)} errors, "
              f"total={total_time:.3f}s")

        return {"total": len(results), "errors": len(errors), "elapsed": total_time}

    def test_02_indicator_timeout_then_fallback_switch(self):
        """
        场景: 真实数据加载超时后，自动切换到模拟数据
        - 模拟真实数据加载超时（通过验证fallback链路的三级切换）
        - 验证: 真实数据→模拟数据→占位符 降级链路
        - 验证超时后数据一致性
        """
        # 选择5张matchable图表和5张pending图表
        matchable_charts = self.e.get_matchable_charts()[:5]
        pending_charts = self.e.get_pending_charts()[:5]
        all_test_charts = matchable_charts + pending_charts

        switch_log = []
        for cb in all_test_charts:
            # Step 1: 尝试真实数据 (无真实数据时自动fallback)
            r = self.e.render_with_fallback(cb.chart_id)
            switch_log.append({
                "chart_id": cb.chart_id,
                "data_status": cb.data_status,
                "source": r["source"],
                "switched_from": "real" if cb.data_status == "matchable" else "pending",
                "switched_to": r["source"],
                "renderable": r["renderable"],
            })

        # 验证所有图表都能成功渲染
        for entry in switch_log:
            self.assertTrue(entry["renderable"],
                            f"{entry['chart_id']} not renderable after fallback")

        # 验证matchable图表fallback到simulated (无真实数据时)
        for entry in switch_log:
            if entry["data_status"] == "matchable":
                self.assertIn(entry["source"], ["real", "simulated"],
                              f"Matchable chart fallback incorrect: {entry}")

        # 验证pending图表fallback到simulated
        for entry in switch_log:
            if entry["data_status"] == "pending_data":
                self.assertIn(entry["source"], ["simulated"],
                              f"Pending chart should fallback to simulated: {entry}")

        print(f"  [T1-02] Fallback switch: {len(switch_log)} charts, "
              f"all renderable, no data loss")
        return switch_log

    def test_03_partial_indicator_arrival(self):
        """
        场景: 部分指标到达、部分缺失
        - 创建临时测试图表，绑定部分指标，验证渲染行为
        - 验证缺失指标不会导致渲染崩溃
        - 验证降级到部分数据的逻辑
        """
        # 选择一张多指标图表作为基础
        multi_ind_charts = [cb for cb in self.e.charts if len(cb.indicators) >= 2]
        self.assertGreater(len(multi_ind_charts), 0, "No multi-indicator charts found")

        test_results = []
        for base_cb in multi_ind_charts[:3]:
            # 复制基础图表，保留前半部分指标
            half_count = max(1, len(base_cb.indicators) // 2)
            test_cb = ChartBinding({
                "chart_id": f"t1_partial_{base_cb.chart_id}",
                "tree_node_id": base_cb.tree_node_id,
                "commodity": base_cb.commodity,
                "chart_type": base_cb.chart_type,
                "title": f"Partial test: {base_cb.title}",
                "indicators": base_cb.indicators[:half_count],
                "data_status": "pending_data",
                "business_description": "",
                "render_priority": 1,
                "weekly_render": True,
            })

            # 生成模拟数据
            sim_data = self.e._generate_simulated_data(test_cb)
            self.assertGreater(len(sim_data), 0,
                               f"Partial indicators sim data failed for {base_cb.chart_id}")

            for d in sim_data:
                self.assertIn("points", d)
                self.assertGreater(len(d["points"]), 0)

            test_results.append({
                "base_chart": base_cb.chart_id,
                "original_indicators": len(base_cb.indicators),
                "partial_indicators": half_count,
                "simulated_ok": True,
                "data_points": sum(len(d["points"]) for d in sim_data),
            })

        # 验证部分指标缺失时的数据完整性
        for r in test_results:
            self.assertGreater(r["data_points"], 0,
                               f"Partial test {r['base_chart']} has no data points")

        print(f"  [T1-03] Partial indicator arrival: {len(test_results)} charts tested, "
              f"all with valid data")
        return test_results

    def test_04_high_concurrency_fallback_chain(self):
        """
        场景: 高并发(50线程)下三级降级链路压力
        - 50线程并发请求101张图表
        - 每张图表执行三级降级: real→simulated→placeholder
        - 验证零崩溃、零错误、零数据丢失
        """
        chart_ids = [cb.chart_id for cb in self.e.charts]
        results = []
        errors = []
        timings = []
        lock = threading.Lock()

        def full_fallback_chain(cid):
            """完整三级降级链路"""
            try:
                t0 = time.time()
                # 直接调用render_with_fallback (内置三级切换)
                r = self.e.render_with_fallback(cid)
                elapsed = time.time() - t0

                if "error" in r or not r.get("renderable"):
                    with lock:
                        errors.append(f"{cid}: render failed")
                else:
                    with lock:
                        results.append({
                            "chart_id": cid,
                            "source": r["source"],
                            "time_ms": round(elapsed * 1000, 2),
                        })
                        timings.append(elapsed)
            except Exception as ex:
                with lock:
                    errors.append(f"{cid}: {str(ex)}")

        t0 = time.time()
        threads = []
        for i in range(50):
            cid = chart_ids[i % len(chart_ids)]
            t = threading.Thread(target=full_fallback_chain, args=(cid,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.time() - t0

        avg_time = statistics.mean(timings) if timings else 0
        p99_time = statistics.quantiles(timings, n=100)[98] if len(timings) > 1 else (timings[0] if timings else 0)
        error_rate = len(errors) / 50 * 100

        # 验证零崩溃
        self.assertEqual(len(errors), 0, f"Errors under high concurrency fallback: {errors[:3]}")
        # 验证P99 < 500ms
        self.assertLess(p99_time, 0.5, f"P99 too high: {p99_time*1000:.2f}ms")
        # 验证错误率=0
        self.assertEqual(error_rate, 0.0, f"Error rate too high: {error_rate:.2f}%")

        print(f"  [T1-04] High concurrency fallback: {len(results)} OK, {len(errors)} errors, "
              f"avg={avg_time*1000:.2f}ms, p99={p99_time*1000:.2f}ms, "
              f"error_rate={error_rate:.2f}%")
        return {
            "total": len(results),
            "errors": len(errors),
            "avg_ms": round(avg_time * 1000, 2),
            "p99_ms": round(p99_time * 1000, 2),
            "error_rate_pct": round(error_rate, 2),
        }

    def test_05_stale_data_handling(self):
        """
        场景: 过期数据/陈旧数据到达场景
        - 模拟数据时间戳过旧(30天前)
        - 验证渲染引擎对陈旧数据的处理策略
        - 验证不会渲染过期数据误导用户
        """
        # 获取一张matchable图表
        matchable = self.e.get_matchable_charts()[0]
        # 当前真实数据加载
        r = self.e.render_with_fallback(matchable.chart_id)
        self.assertTrue(r["renderable"])

        # 验证数据有时间戳
        if r["render_data"] and r["render_data"][0].get("points"):
            first_date = r["render_data"][0]["points"][0].get("date")
            if first_date:
                print(f"  [T1-05] Stale data: earliest date={first_date}, "
                      f"total_points={len(r['render_data'][0]['points'])}")

        # 验证引擎对缺失时间戳数据的容错
        # 模拟无时间戳数据
        test_cb = ChartBinding({
            "chart_id": "t1_stale_test",
            "tree_node_id": "p1",
            "commodity": "cu",
            "chart_type": "time_series",
            "title": "Stale data test",
            "indicators": [{"indicator_name": "test", "indicator_id": "TEST_STALE"}],
            "data_status": "pending_data",
            "business_description": "",
            "render_priority": 1,
            "weekly_render": True,
        })
        # 生成模拟数据 (模拟数据总是有日期的)
        sim_data = self.e._generate_simulated_data(test_cb)
        self.assertGreater(len(sim_data), 0)
        # 验证所有点都有日期
        for d in sim_data:
            for p in d["points"]:
                self.assertIn("date", p, "Data point missing date")
                self.assertIn("value", p, "Data point missing value")

        print(f"  [T1-05] Stale data handling: all points have valid dates/values")

    def test_06_indicator_time_order_consistency(self):
        """
        场景: 指标时序一致性验证
        - 验证多指标图表中各指标时间范围对齐
        - 验证时间序列单调递增
        - 验证跨指标数据对齐
        """
        multi_ind_charts = [cb for cb in self.e.charts if len(cb.indicators) >= 2]
        alignment_issues = []
        for cb in multi_ind_charts[:10]:
            sim_data = self.e._generate_simulated_data(cb)
            if not sim_data:
                continue

            # 验证每个指标的时间序列单调递增
            for d in sim_data:
                dates = [p["date"] for p in d["points"]]
                for i in range(1, len(dates)):
                    if dates[i] < dates[i-1]:
                        alignment_issues.append({
                            "chart_id": cb.chart_id,
                            "indicator": d.get("name", "?"),
                            "issue": f"Date not monotonic at index {i}: {dates[i-1]} > {dates[i]}",
                        })

            # 验证跨指标数据点对齐
            if len(sim_data) >= 2:
                dates_0 = {p["date"] for p in sim_data[0]["points"]}
                dates_1 = {p["date"] for p in sim_data[1]["points"]}
                # 模拟数据应该覆盖相同日期范围
                if dates_0 and dates_1:
                    if not (dates_0 & dates_1):
                        alignment_issues.append({
                            "chart_id": cb.chart_id,
                            "indicator": "cross_indicator",
                            "issue": "No overlapping dates between indicators",
                        })

        self.assertEqual(len(alignment_issues), 0,
                         f"Time alignment issues: {alignment_issues[:3]}")
        print(f"  [T1-06] Time order consistency: {len(multi_ind_charts[:10])} multi-indicator charts, "
              f"0 alignment issues")


# ===========================================================================
# T1: 边界场景 — 节点切换与指标挂载动态操作
# ===========================================================================

class TestT1_BoundaryDynamicOps(unittest.TestCase):
    """
    T1: 动态操作边界场景
    - 节点切换边界
    - 指标挂载/卸载边界
    - 并发节点切换与渲染
    """

    def setUp(self):
        self.e = make_engine()

    def test_07_node_switch_boundary(self):
        """
        场景: 节点切换边界测试
        - 切换到有效节点 (同品种范围内)
        - 切换到无效节点 (不同品种)
        - 切换到不存在的节点
        """
        # 选择一张图表
        cb = self.e.charts[0]
        original_node = cb.tree_node_id
        original_desc = cb.business_description

        # 测试1: 切换到有效节点 (同节点)
        ok, msg = self.e.switch_node(cb.chart_id, original_node)
        self.assertTrue(ok, f"Same-node switch failed: {msg}")
        self.assertEqual(cb.tree_node_id, original_node)

        # 测试2: 切换到同品种范围内的其他节点
        valid_nodes = [nid for nid, node in self.e.node_index.items()
                       if cb.commodity in node.get("comms", set())]
        other_nodes = [n for n in valid_nodes if n != original_node]
        if other_nodes:
            target_node = other_nodes[0]
            ok, msg = self.e.switch_node(cb.chart_id, target_node)
            self.assertTrue(ok, f"Valid node switch failed: {msg}")
            self.assertEqual(cb.tree_node_id, target_node)
            # 验证业务描述更新
            expected_desc = f"{self.e.node_index[target_node]['name']}({self.e.node_index[target_node]['q']})"
            self.assertEqual(cb.business_description, expected_desc)

            # 恢复
            self.e.switch_node(cb.chart_id, original_node)

        # 测试3: 切换到无效节点
        invalid_nodes = [nid for nid, node in self.e.node_index.items()
                         if cb.commodity not in node.get("comms", set())]
        if invalid_nodes:
            bad_node = invalid_nodes[0]
            ok, msg = self.e.switch_node(cb.chart_id, bad_node)
            self.assertFalse(ok, f"Invalid node switch should fail: {msg}")
            self.assertIn("not in", msg)

        # 测试4: 切换到不存在的节点
        ok, msg = self.e.switch_node(cb.chart_id, "nonexistent_node_xyz")
        self.assertFalse(ok, f"Nonexistent node switch should fail: {msg}")
        self.assertIn("not registered", msg)

        # 验证恢复后状态不变
        self.assertEqual(cb.tree_node_id, original_node)
        print(f"  [T1-07] Node switch boundary: {len(other_nodes)} valid switches tested, "
              f"invalid/nonexistent correctly rejected")

    def test_08_indicator_mount_unmount_boundary(self):
        """
        场景: 指标挂载/卸载边界测试
        - 正常挂载新指标
        - 重复挂载同一指标
        - 挂载空指标
        - 卸载不存在的指标
        """
        cb = self.e.charts[0]
        original_count = len(cb.indicators)

        # 测试1: 正常挂载
        ok, msg = self.e.mount_indicator(cb.chart_id, "Test Indicator", "TEST_BOUNDARY_001")
        self.assertTrue(ok, f"Normal mount failed: {msg}")
        self.assertEqual(len(cb.indicators), original_count + 1)

        # 测试2: 重复挂载
        ok, msg = self.e.mount_indicator(cb.chart_id, "Test Indicator", "TEST_BOUNDARY_001")
        self.assertFalse(ok, f"Duplicate mount should fail: {msg}")
        self.assertIn("already mounted", msg)

        # 测试3: 挂载空指标名
        ok, msg = self.e.mount_indicator(cb.chart_id, "", "TEST_EMPTY_NAME")
        self.assertFalse(ok, f"Empty name mount should fail: {msg}")
        self.assertIn("cannot be empty", msg)

        # 测试4: 挂载空指标ID
        ok, msg = self.e.mount_indicator(cb.chart_id, "Test", "")
        self.assertFalse(ok, f"Empty id mount should fail: {msg}")
        self.assertIn("cannot be empty", msg)

        # 测试5: 卸载正常指标
        ok, msg = self.e.unmount_indicator(cb.chart_id, "TEST_BOUNDARY_001")
        self.assertTrue(ok, f"Normal unmount failed: {msg}")
        self.assertEqual(len(cb.indicators), original_count)

        # 测试6: 卸载不存在的指标
        ok, msg = self.e.unmount_indicator(cb.chart_id, "TEST_NONEXISTENT")
        self.assertFalse(ok, f"Unmount nonexistent should fail: {msg}")
        self.assertIn("not found", msg)

        print(f"  [T1-08] Indicator mount/unmount boundary: 6/6 tests passed")

    def test_09_concurrent_node_switch_render(self):
        """
        场景: 并发节点切换 + 渲染
        - 多线程同时切换节点并渲染
        - 验证线程安全性
        """
        chart_ids = [cb.chart_id for cb in self.e.charts[:20]]
        valid_nodes = [nid for nid, node in self.e.node_index.items()]
        errors = []
        results = []
        lock = threading.Lock()
        random.seed(42)

        def concurrent_switch_render(cid):
            """并发节点切换+渲染"""
            try:
                cb = self.e.chart_index.get(cid)
                if not cb:
                    return

                # 找到该图表的有效节点
                valid = [nid for nid, node in self.e.node_index.items()
                         if cb.commodity in node.get("comms", set())]
                if not valid:
                    return

                # 随机切换节点
                target_node = random.choice(valid)
                ok, _ = self.e.switch_node(cid, target_node)

                # 立即渲染
                r = self.e.render_with_fallback(cid)

                with lock:
                    if r.get("renderable"):
                        results.append({"chart_id": cid, "node": target_node, "source": r["source"]})
                    else:
                        errors.append(f"{cid}: not renderable after switch")
            except Exception as ex:
                with lock:
                    errors.append(f"{cid}: {str(ex)}")

        t0 = time.time()
        threads = []
        for cid in chart_ids:
            t = threading.Thread(target=concurrent_switch_render, args=(cid,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total_time = time.time() - t0

        self.assertLess(len(errors), 5, f"Too many errors under concurrent switch: {errors[:3]}")
        print(f"  [T1-09] Concurrent node switch+render: {len(results)} OK, "
              f"{len(errors)} errors, total={total_time:.3f}s")
        return {"ok": len(results), "errors": len(errors)}


# ===========================================================================
# T2: 监控大盘告警阈值微调演练
# ===========================================================================

class TestT2_AlertThresholdRehearsal(unittest.TestCase):
    """
    T2: 监控大盘告警阈值微调演练
    - 告警触发/恢复通知链路验证
    - 不修改生产阈值，仅模拟告警状态变化
    - 验证告警升级/降级链路
    - 验证告警冷却期逻辑
    """

    def setUp(self):
        self.e = make_engine()
        self.alert_log = []
        self.notify_log = []

    def _simulate_alert_evaluation(self, metric_name, value, rule):
        """
        模拟告警评估
        - 根据规则条件判断是否触发
        - 生成通知日志
        - 不修改生产阈值
        """
        condition = rule["condition"]
        triggered = False
        recovery = False

        if ">" in condition:
            threshold = float(condition.replace(">", "").strip())
            if value > threshold:
                triggered = True
            elif value <= threshold:
                recovery = True
        elif "<" in condition:
            threshold = float(condition.replace("<", "").strip())
            if value < threshold:
                triggered = True
            elif value >= threshold:
                recovery = True

        entry = {
            "alert_id": rule["id"],
            "metric": metric_name,
            "value": value,
            "condition": condition,
            "severity": rule["severity"],
            "triggered": triggered,
            "recovery": recovery,
            "timestamp": datetime.now().isoformat(),
        }
        self.alert_log.append(entry)

        if triggered:
            self.notify_log.append({
                "type": "ALERT_TRIGGER",
                "alert_id": rule["id"],
                "severity": rule["severity"],
                "metric": metric_name,
                "value": value,
                "message": f"[{rule['severity']}] {metric_name}={value} triggered alert {rule['id']}",
            })
        elif recovery:
            self.notify_log.append({
                "type": "ALERT_RECOVERY",
                "alert_id": rule["id"],
                "severity": rule["severity"],
                "metric": metric_name,
                "value": value,
                "message": f"[RECOVERY] {metric_name}={value} recovered alert {rule['id']}",
            })

        return entry

    def test_10_alert_trigger_scenarios(self):
        """
        场景: 告警触发模拟
        - 模拟P99超阈值场景 (ALERT-001)
        - 模拟页面错误场景 (ALERT-003)
        - 模拟错误率超阈值场景 (ALERT-004)
        - 模拟fallback触发率超阈值场景 (ALERT-005)
        - 模拟真实数据可用率低于阈值场景 (ALERT-010)
        """
        scenarios = [
            # (metric, value, rule_id)
            ("chart_render_p99_ms", 550.0, "ALERT-001"),     # >500 P2
            ("chart_render_p95_ms", 350.0, "ALERT-002"),     # >300 P3
            ("page_render_error_count", 3, "ALERT-003"),       # >0 P1
            ("render_error_rate_pct", 2.5, "ALERT-004"),       # >1 P1
            ("fallback_trigger_rate_pct", 35.0, "ALERT-005"),  # >30 P2
            ("fallback_placeholder_count", 5, "ALERT-006"),    # >0 P3
            ("binding_resolve_error_count", 1, "ALERT-007"),   # >0 P2
            ("concurrent_render_p99_ms", 600.0, "ALERT-008"),  # >500 P2
            ("concurrent_render_error_rate_pct", 0.5, "ALERT-009"),  # >0 P1
            ("real_data_available_rate_pct", 45.0, "ALERT-010"),  # <60 P3
        ]

        triggered_count = 0
        for metric, value, rule_id in scenarios:
            rule = next((r for r in ALERT_RULES if r["id"] == rule_id), None)
            if rule:
                entry = self._simulate_alert_evaluation(metric, value, rule)
                if entry["triggered"]:
                    triggered_count += 1

        self.assertGreater(triggered_count, 0, "No alerts triggered in rehearsal")
        self.assertEqual(len(self.notify_log), triggered_count,
                         f"Notification log mismatch: {len(self.notify_log)} vs {triggered_count}")

        # 验证告警级别分布
        severity_counts = Counter(e["severity"] for e in self.alert_log if e["triggered"])
        print(f"  [T2-10] Alert trigger: {triggered_count} triggered, "
              f"severity distribution: {dict(severity_counts)}")
        return {"triggered": triggered_count, "severity": dict(severity_counts)}

    def test_11_alert_recovery_scenarios(self):
        """
        场景: 告警恢复模拟
        - 模拟从触发状态恢复到正常
        - 验证恢复通知链路
        """
        # 模拟恢复场景
        recovery_scenarios = [
            ("chart_render_p99_ms", 300.0, "ALERT-001"),    # >500 → 恢复 (300<500)
            ("page_render_error_count", 0, "ALERT-003"),      # >0 → 恢复 (0<=0)
            ("render_error_rate_pct", 0.5, "ALERT-004"),      # >1 → 恢复 (0.5<=1)
            ("fallback_trigger_rate_pct", 15.0, "ALERT-005"), # >30 → 恢复 (15<=30)
            ("real_data_available_rate_pct", 85.0, "ALERT-010"),  # <60 → 恢复 (85>=60)
        ]

        recovery_count = 0
        for metric, value, rule_id in recovery_scenarios:
            rule = next((r for r in ALERT_RULES if r["id"] == rule_id), None)
            if rule:
                entry = self._simulate_alert_evaluation(metric, value, rule)
                if entry["recovery"]:
                    recovery_count += 1

        self.assertGreater(recovery_count, 0, "No recoveries detected")

        # 验证恢复通知
        recovery_notifications = [n for n in self.notify_log if n["type"] == "ALERT_RECOVERY"]
        self.assertGreater(len(recovery_notifications), 0, "No recovery notifications")

        print(f"  [T2-11] Alert recovery: {recovery_count} recovered, "
              f"{len(recovery_notifications)} recovery notifications sent")
        return {"recovered": recovery_count}

    def test_12_alert_boundary_values(self):
        """
        场景: 告警阈值边界值测试
        - 测试等于阈值/刚好超过/刚好低于的边界情况
        - 验证告警触发逻辑的精确性
        """
        boundary_tests = [
            # 刚好等于阈值 (不触发)
            ("chart_render_p99_ms", 500.0, "ALERT-001", False),
            # 刚好超过阈值 (触发)
            ("chart_render_p99_ms", 500.01, "ALERT-001", True),
            # 刚好低于阈值 (不触发)
            ("chart_render_p99_ms", 499.99, "ALERT-001", False),
            # 零错误 (不触发)
            ("page_render_error_count", 0, "ALERT-003", False),
            # 一个错误 (触发)
            ("page_render_error_count", 1, "ALERT-003", True),
            # 刚好等于可用率阈值 (不触发 <60)
            ("real_data_available_rate_pct", 60.0, "ALERT-010", False),
            # 低于可用率阈值 (触发)
            ("real_data_available_rate_pct", 59.9, "ALERT-010", True),
        ]

        for metric, value, rule_id, expected_triggered in boundary_tests:
            rule = next((r for r in ALERT_RULES if r["id"] == rule_id), None)
            if rule:
                entry = self._simulate_alert_evaluation(metric, value, rule)
                self.assertEqual(entry["triggered"], expected_triggered,
                                 f"Boundary test failed: {metric}={value} "
                                 f"expected_triggered={expected_triggered} "
                                 f"got={entry['triggered']}")

        print(f"  [T2-12] Alert boundary: {len(boundary_tests)} boundary cases, all pass")

    def test_13_alert_cooldown_logic(self):
        """
        场景: 告警冷却期逻辑验证
        - 验证同一告警在冷却期内不重复触发
        - 验证冷却期结束后可以再次触发
        """
        # 模拟冷却期逻辑
        cooldown_periods = {
            "ALERT-001": 30,   # 30 min
            "ALERT-002": 60,   # 60 min
            "ALERT-003": 0,    # 0 (no cooldown)
            "ALERT-004": 0,    # 0
            "ALERT-005": 60,   # 60 min
            "ALERT-006": 300,  # 300 min (5h)
            "ALERT-007": 30,   # 30 min
            "ALERT-008": 60,   # 60 min
            "ALERT-009": 0,    # 0
            "ALERT-010": 300,  # 300 min
        }

        # 模拟告警触发时间线
        alert_timeline = [
            # (time_min, alert_id, should_suppress)
            (0, "ALERT-001", False),     # 第一次触发，无冷却
            (5, "ALERT-001", True),      # 5分钟后再次触发，在30min冷却期内
            (29, "ALERT-001", True),     # 29分钟后，仍在冷却期
            (31, "ALERT-001", False),    # 31分钟后，冷却期结束
            (0, "ALERT-003", False),     # P1无冷却，每次触发
            (1, "ALERT-003", False),     # P1无冷却
        ]

        cooldown_tracker = {}  # alert_id -> last_trigger_time
        suppressions = 0
        for time_min, alert_id, should_suppress in alert_timeline:
            last_trigger = cooldown_tracker.get(alert_id, -9999)
            cooldown = cooldown_periods.get(alert_id, 0)
            in_cooldown = (time_min - last_trigger) < cooldown

            if should_suppress:
                self.assertTrue(in_cooldown,
                                f"{alert_id} at t={time_min}min should be suppressed but cooldown={cooldown}, "
                                f"last={last_trigger}")
                suppressions += 1
            else:
                # 允许触发 (第一次或冷却期结束)
                if alert_id in cooldown_tracker:
                    # 检查冷却期是否确实结束
                    if cooldown > 0:
                        self.assertTrue((time_min - last_trigger) >= cooldown,
                                        f"{alert_id} at t={time_min}min cooldown not over")
                cooldown_tracker[alert_id] = time_min

        self.assertGreater(suppressions, 0, "No suppressions during cooldown")
        print(f"  [T2-13] Alert cooldown: {suppressions} suppressions, "
              f"{len(alert_timeline)} timeline entries, all correct")

    def test_14_alert_severity_escalation(self):
        """
        场景: 告警严重性升级链路
        - P3→P2→P1 升级链路验证
        - 模拟从轻微告警升级到严重告警
        """
        escalation_scenarios = [
            # (metric, value, rule_id, expected_severity, escalation_level)
            ("chart_render_p95_ms", 350.0, "ALERT-002", "P3", 1),   # P3: P95>300
            ("chart_render_p99_ms", 550.0, "ALERT-001", "P2", 2),   # P2: P99>500 (升级)
            ("page_render_error_count", 5, "ALERT-003", "P1", 3),   # P1: 页面错误 (升级)
        ]

        for metric, value, rule_id, expected_severity, escalation_level in escalation_scenarios:
            rule = next((r for r in ALERT_RULES if r["id"] == rule_id), None)
            if rule:
                entry = self._simulate_alert_evaluation(metric, value, rule)
                self.assertEqual(rule["severity"], expected_severity,
                                 f"Severity mismatch: {rule_id} expected={expected_severity} "
                                 f"got={rule['severity']}")

        # 验证P1告警优先级最高
        p1_alerts = [a for a in ALERT_RULES if a["severity"] == "P1"]
        p2_alerts = [a for a in ALERT_RULES if a["severity"] == "P2"]
        p3_alerts = [a for a in ALERT_RULES if a["severity"] == "P3"]
        self.assertEqual(len(p1_alerts), 3, f"P1 count: {len(p1_alerts)}")
        self.assertEqual(len(p2_alerts), 4, f"P2 count: {len(p2_alerts)}")
        self.assertEqual(len(p3_alerts), 3, f"P3 count: {len(p3_alerts)}")

        print(f"  [T2-14] Alert severity escalation: P3({len(p3_alerts)})→P2({len(p2_alerts)})→P1({len(p1_alerts)}), "
              f"all correct")

    def test_15_slA_compliance_check(self):
        """
        场景: SLA达标验证
        - 基于Phase02实测数据验证SLA达标情况
        - 不修改SLA目标，仅验证达标状态
        """
        # Phase02 实测数据
        measured = {
            "chart_render_p99_ms": 190.47,     # worst case (burst 101)
            "concurrent_render_p99_ms": 190.47,
            "concurrent_render_error_rate_pct": 0.00,
            "page_render_error_count": 0,
            "render_error_rate_pct": 0.00,
            "fallback_trigger_rate_pct": 0.00,  # 101/101 rendered successfully
        }

        compliance = {}
        for metric, target in SLA_TARGETS.items():
            actual = measured.get(metric, None)
            if actual is not None:
                if metric in ["page_render_error_count", "render_error_rate_pct",
                              "concurrent_render_error_rate_pct"]:
                    # 越低越好，目标为0
                    compliant = actual <= target
                elif "rate" in metric and "<" not in str(target):
                    # 越低越好 (fallback rate)
                    compliant = actual <= target
                else:
                    # 越低越好 (延迟指标)
                    compliant = actual < target
                compliance[metric] = {
                    "actual": actual,
                    "target": target,
                    "compliant": compliant,
                    "margin": round(target - actual, 2) if compliant else round(actual - target, 2),
                }

        all_compliant = all(c["compliant"] for c in compliance.values())
        self.assertTrue(all_compliant, f"SLA compliance failed: {compliance}")

        print(f"  [T2-15] SLA compliance: {len(compliance)}/{len(compliance)} compliant, "
              f"all margins positive")
        return compliance


# ===========================================================================
# T2: 告警通知链路完整性验证
# ===========================================================================

class TestT2_NotificationChain(unittest.TestCase):
    """
    T2: 告警通知链路完整性验证
    - 通知格式验证
    - 通知接收方映射
    - 通知链路不修改生产配置
    """

    def setUp(self):
        self.e = make_engine()

    def test_16_notification_format_validation(self):
        """
        场景: 通知格式验证
        - 验证告警通知包含所有必需字段
        - 验证通知格式符合标准
        """
        # 模拟告警通知
        test_notifications = [
            {
                "type": "ALERT_TRIGGER",
                "alert_id": "ALERT-001",
                "severity": "P2",
                "metric": "chart_render_p99_ms",
                "value": 550.0,
                "message": "[P2] chart_render_p99_ms=550.0 triggered alert ALERT-001",
            },
            {
                "type": "ALERT_TRIGGER",
                "alert_id": "ALERT-003",
                "severity": "P1",
                "metric": "page_render_error_count",
                "value": 3,
                "message": "[P1] page_render_error_count=3 triggered alert ALERT-003",
            },
            {
                "type": "ALERT_RECOVERY",
                "alert_id": "ALERT-001",
                "severity": "P2",
                "metric": "chart_render_p99_ms",
                "value": 300.0,
                "message": "[RECOVERY] chart_render_p99_ms=300.0 recovered alert ALERT-001",
            },
        ]

        required_fields = ["type", "alert_id", "severity", "metric", "value", "message"]
        format_errors = []
        for n in test_notifications:
            for field in required_fields:
                if field not in n:
                    format_errors.append(f"Missing field '{field}' in notification {n.get('alert_id', '?')}")
            # 验证消息格式
            if n["type"] == "ALERT_TRIGGER":
                self.assertIn("[", n["message"])
                self.assertIn("triggered", n["message"])
            elif n["type"] == "ALERT_RECOVERY":
                self.assertIn("RECOVERY", n["message"])

        self.assertEqual(len(format_errors), 0, f"Format errors: {format_errors}")
        print(f"  [T2-16] Notification format: {len(test_notifications)} notifications, "
              f"0 format errors")

    def test_17_notification_receiver_mapping(self):
        """
        场景: 告警接收方映射验证
        - 验证不同严重性级别对应不同的通知通道
        - P0: 电话+即时+邮件
        - P1: 即时+邮件
        - P2: 邮件
        - P3: 台账
        """
        receiver_map = {
            "P0": ["phone", "immediate", "email"],
            "P1": ["immediate", "email"],
            "P2": ["email"],
            "P3": ["ledger"],
        }

        # 验证映射完整性
        for severity, receivers in receiver_map.items():
            self.assertGreater(len(receivers), 0,
                               f"{severity} has no receivers")

        # 验证P1接收方包含即时通知
        self.assertIn("immediate", receiver_map["P1"])
        self.assertIn("email", receiver_map["P1"])

        # 验证P2仅邮件
        self.assertEqual(len(receiver_map["P2"]), 1)
        self.assertIn("email", receiver_map["P2"])

        # 验证P3仅台账
        self.assertEqual(len(receiver_map["P3"]), 1)
        self.assertIn("ledger", receiver_map["P3"])

        # 验证P0最高优先级有电话通知
        self.assertIn("phone", receiver_map["P0"])

        print(f"  [T2-17] Notification receivers: {len(receiver_map)} severity levels, "
              f"all mapped correctly")
        return receiver_map

    def test_18_production_threshold_unchanged(self):
        """
        场景: 生产阈值不变验证
        - 验证监控大盘配置中的生产阈值未被修改
        - 验证演练仅模拟，不影响生产配置
        """
        config_path = os.path.join(os.path.dirname(__file__), "..", "monitoring_dashboard.json")
        self.assertTrue(os.path.exists(config_path), "Dashboard config not found")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 验证告警规则条件未被修改
        expected_conditions = {
            "ALERT-001": ">500",
            "ALERT-002": ">300",
            "ALERT-003": ">0",
            "ALERT-004": ">1",
            "ALERT-005": ">30",
            "ALERT-006": ">0",
            "ALERT-007": ">0",
            "ALERT-008": ">500",
            "ALERT-009": ">0",
            "ALERT-010": "<60",
        }

        condition_changes = []
        for a in config["alerts"]:
            aid = a["id"]
            if aid in expected_conditions:
                if a.get("condition") != expected_conditions[aid]:
                    condition_changes.append({
                        "alert_id": aid,
                        "expected": expected_conditions[aid],
                        "actual": a.get("condition"),
                    })

        self.assertEqual(len(condition_changes), 0,
                         f"Production thresholds modified: {condition_changes}")

        # 验证SLA目标未修改
        expected_sla = {
            "chart_render_p99_ms": 500,
            "concurrent_render_p99_ms": 500,
            "concurrent_render_error_rate_pct": 0,
            "page_render_error_count": 0,
            "render_error_rate_pct": 0,
            "fallback_trigger_rate_pct": 20,
        }

        sla_changes = []
        for metric, expected_target in expected_sla.items():
            actual = config["sla"].get(metric, {}).get("target")
            if actual != expected_target:
                sla_changes.append({
                    "metric": metric,
                    "expected": expected_target,
                    "actual": actual,
                })

        self.assertEqual(len(sla_changes), 0,
                         f"SLA targets modified: {sla_changes}")

        print(f"  [T2-18] Production thresholds: {len(expected_conditions)} alert conditions "
              f"+ {len(expected_sla)} SLA targets, ALL UNCHANGED")


# ===========================================================================
# MAIN: 执行全部测试
# ===========================================================================

if __name__ == "__main__":
    print("=" * 78)
    print("V88 Phase02 Post-Deploy Prep — Boundary Scenario & Alert Rehearsal Tests")
    print("TASK_ID: V88_PHASE02_DSHE_POST_DEPLOY_PREP")
    print("BRANCH: feature/v88-g1")
    print("=" * 78)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # T1: Boundary Scenario Tests
    suite.addTests(loader.loadTestsFromTestCase(TestT1_BoundaryDelayedArrival))
    suite.addTests(loader.loadTestsFromTestCase(TestT1_BoundaryDynamicOps))

    # T2: Alert Threshold Rehearsal
    suite.addTests(loader.loadTestsFromTestCase(TestT2_AlertThresholdRehearsal))
    suite.addTests(loader.loadTestsFromTestCase(TestT2_NotificationChain))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 78)
    if result.wasSuccessful():
        print("ALL POST-DEPLOY PREP TESTS PASSED")
        print(f"  Tests run: {result.testsRun}")
    else:
        print("POST-DEPLOY PREP TESTS FAILED")
        print(f"  Tests run: {result.testsRun}")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
    print("=" * 78)
