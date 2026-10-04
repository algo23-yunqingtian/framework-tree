#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 事件存储高可用仿真器 (event_store_ha_test.py)

工单: 工单-HERMES / T3.2 事件存储高可用仿真
分支: feature/v85-chart-template @ dd0a7f0
编制方: HERMES (L3 审计方)
日期: 2026-10-15

目的
----
对 audit_event_store.py 做高可用仿真, 验证:
  1. **并发写入**: 多源 (DSHB/DSHE/HERMES) 多实例同时推送, 无数据丢失
  2. **重复事件去重**: 同内容事件多次上报, dedup_count 累加, 不新增记录
  3. **异常断连重试**: 模拟网络闪断, 事件进入缓存, 恢复后自动续传
  4. **事件持久化**: JSONL 落盘, 进程重启后数据可恢复
  5. **检索查询**: 按 dep_registry_id / trace_id / audit_fingerprint 检索

关键设计: 断连缓存机制
----------------------
audit_event_store.py 本身是文件系统直写 (无中间件), 生产环境若存储不可达,
事件会丢失。本仿真实现 `HAStoreWrapper`:
  - 包装底层 store, 写入失败时进入内存缓存队列 (pending buffer)
  - 提供 flush_pending() 在连接恢复后续传
  - 提供 checkpoint 机制, 缓存也持久化到本地, 进程重启不丢

用法
----
  python3 event_store_ha_test.py --self-test     # 自检
  python3 event_store_ha_test.py --demo          # 全场景仿真
  python3 event_store_ha_test.py --json <out>    # JSON 输出

约束
----
NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
纯离线仿真, 不发网络请求。
"""

import argparse
import gc
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit_event_store import (
    normalize_event, load_store, append_events, query_events,
    compute_stats, make_event_id,
)

HA_VERSION = "1.0.0"
BRANCH_BASELINE = "dd0a7f0"


# ---------------------------------------------------------------------------
# HA 存储包装器 (断连缓存 + 续传)
# ---------------------------------------------------------------------------
class HAStoreWrapper:
    """事件存储高可用包装器。

    职责:
      1. 正常模式: 直通底层 store
      2. 断连模式: 写入进入 pending buffer (同时持久化到 checkpoint 文件)
      3. 恢复模式: flush_pending() 续传, 按序重放
      4. 去重: 依赖底层 make_event_id 幂等

    pending buffer 持久化 (checkpoint):
      即使进程崩溃, pending 事件也不会丢失。
    """

    def __init__(self, store_path, checkpoint_path=None, connected=True):
        self.store_path = store_path
        self.checkpoint_path = checkpoint_path or \
            store_path + ".pending.jsonl"
        self.connected = connected
        self.pending = []          # 内存缓存
        self.flushed_total = 0     # 已成功落盘
        self.bypassed_total = 0    # 断连期间进缓存
        self._lock = threading.Lock()
        # 加载已有 checkpoint
        if os.path.exists(self.checkpoint_path):
            self.pending = self._load_checkpoint()

    def _load_checkpoint(self):
        out = []
        try:
            with open(self.checkpoint_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        out.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            return []
        return out

    def _save_checkpoint(self):
        try:
            with open(self.checkpoint_path, "w", encoding="utf-8") as f:
                for e in self.pending:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
        except OSError:
            pass  # checkpoint 写入失败不阻断主流程

    def set_connected(self, connected):
        """模拟网络闪断/恢复"""
        self.connected = connected

    def ingest(self, event_dict):
        """上报事件。返回 (event_id, accepted, pending)"""
        ev, errs = normalize_event(event_dict)
        if errs or not ev:
            return None, False, False, errs

        with self._lock:
            if self.connected:
                added, deduped = append_events(self.store_path, [ev])
                self.flushed_total += added
                return ev["event_id"], True, False, None
            else:
                # 断连: 进缓存 + 持久化 checkpoint
                self.pending.append(ev)
                self._save_checkpoint()
                self.bypassed_total += 1
                return ev["event_id"], False, True, None

    def flush_pending(self):
        """续传 pending 缓存到 store。返回 (added, deduped, remaining)"""
        if not self.connected:
            return 0, 0, len(self.pending)
        with self._lock:
            if not self.pending:
                return 0, 0, 0
            added, deduped = append_events(self.store_path, self.pending)
            self.flushed_total += added
            # 清空已续传的 pending
            self.pending = []
            self._save_checkpoint()
            return added, deduped, 0

    def stats(self):
        return {
            "connected": self.connected,
            "pending": len(self.pending),
            "flushed_total": self.flushed_total,
            "bypassed_total": self.bypassed_total,
            "store_events": len(load_store(self.store_path)),
            "checkpoint_events": len(self._load_checkpoint()),
        }


# ---------------------------------------------------------------------------
# 事件工厂 (mock 多源上报)
# ---------------------------------------------------------------------------
RULES = {
    "R-AUDIT-01": ("D01.2", "缺取数证据"),
    "R-AUDIT-02": ("D02.3", "桥接率分子虚增"),
    "R-AUDIT-03": ("D03.1", "缺 trace_id"),
    "R-AUDIT-04": ("D04.1", "脚本 search 中转"),
    "R-CONTRACT-V1": ("CV-05", "缺 md5_manifest"),
    "R-DEP-STATE": ("DS-05", "跨团队台账不一致"),
    "R-LEGACY-CAL": ("LC-01", "存量旧口径残留"),
}

TEAMS = ["DSHB", "DSHE", "DSHB", "DSHE"]  # 加权: DSHB/DSHE 各两实例


def make_event(source_instance, seq, rule_key=None):
    """生成一条模拟告警事件"""
    rule_key = rule_key or random.choice(list(RULES.keys()))
    dp, msg = RULES[rule_key]
    level = random.choice(["CRITICAL", "CRITICAL", "HIGH", "MEDIUM"])
    team = source_instance.split("_")[0]
    return {
        "level": level,
        "rule": rule_key,
        "detect_point": dp,
        "message": "%s [%s] %s" % (msg, source_instance, seq),
        "source_team": team,
        "dep_registry_id": "DEP-REG-001",
        "evidence_package_index": seq % 100,
        "trace_id": "%s-T%d" % (source_instance, seq),
        "audit_fingerprint": "%s-FP%d" % (source_instance, seq),
        "evidence_file": "%s_pkg.json" % source_instance,
        "run_id": "20261015_10000%d" % (seq % 10),
    }


def make_event_raw(source_instance, seq):
    """含 source_team 版本后缀 (测试前缀归一)"""
    e = make_event(source_instance, seq)
    e["source_team"] = "%s_V86_RC2_%s_AUDIT" % (
        source_instance.split("_")[0], source_instance.split("_")[1])
    return e


# ---------------------------------------------------------------------------
# 场景 1: 多源并发写入
# ---------------------------------------------------------------------------
def scenario_concurrent_write(wrapper, n_events=200, instances=6, concurrency=6):
    """多实例并发上报, 验证无数据丢失"""
    instances_list = ["DSHB_L1_%d" % i for i in range(3)] + \
                     ["DSHE_L2_%d" % i for i in range(3)]
    events = []
    for inst in instances_list:
        for seq in range(n_events // len(instances_list)):
            events.append((inst, seq))

    accepted = 0
    errors = 0
    results = []

    def submit(inst, seq):
        return wrapper.ingest(make_event_raw(inst, seq))

    start = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = [pool.submit(submit, inst, seq) for inst, seq in events]
        for fut in as_completed(futs):
            eid, acc, pend, err = fut.result()
            results.append((eid, acc, pend, err))
            if acc:
                accepted += 1
            if err:
                errors += 1
    elapsed = time.time() - start

    stored = len(load_store(wrapper.store_path))
    stats = compute_stats(load_store(wrapper.store_path))

    return {
        "scenario": "多源并发写入",
        "submitted": len(events),
        "accepted": accepted,
        "errors": errors,
        "stored_after": stored,
        "elapsed_seconds": round(elapsed, 4),
        "throughput_per_sec": round(len(events) / elapsed, 1) if elapsed else 0,
        "instances": len(instances_list),
        "concurrency": concurrency,
        "unique_events": stats["total_unique_events"],
        "dedup_collapsed": stats["dedup_collapsed"],
        "no_data_loss": stored >= accepted,
    }


# ---------------------------------------------------------------------------
# 场景 2: 重复事件去重
# ---------------------------------------------------------------------------
def scenario_dedup(wrapper, n_events=50, repeat_factor=4):
    """同内容事件多次上报, 验证 dedup_count 累加。

    注: 只在本次提交的 trace_id 范围内验证去重, 不受 store 已有数据影响。
    """
    base_events = [make_event("DSHB_DUP_1", i) for i in range(n_events)]
    submitted = 0
    for rep in range(repeat_factor):
        for ev in base_events:
            wrapper.ingest(ev)
            submitted += 1

    stored = load_store(wrapper.store_path)
    dedup_ok = 0
    for ev in base_events:
        q = query_events(stored, trace=ev["trace_id"])
        if len(q) == 1 and q[0].get("dedup_count", 1) == repeat_factor:
            dedup_ok += 1

    # 只统计本次提交产生的唯一记录
    this_traces = {ev["trace_id"] for ev in base_events}
    this_stored = [e for e in stored if e.get("trace_id") in this_traces]

    return {
        "scenario": "重复事件去重",
        "submitted": submitted,
        "this_run_unique_stored": len(this_stored),
        "store_total": len(stored),
        "expected_unique": n_events,
        "dedup_verified": dedup_ok,
        "dedup_accuracy": round(dedup_ok / n_events * 100, 2)
                          if n_events else 0,
        "dedup_correct": dedup_ok == n_events,
        "no_duplication": len(this_stored) == n_events,
    }


# ---------------------------------------------------------------------------
# 场景 3: 断连重试 (核心 HA 场景)
# ---------------------------------------------------------------------------
def scenario_disconnect_retry(wrapper, n_before=30, n_during=40,
                              n_after=20, pause_seconds=0.3):
    """模拟网络闪断: 断连前上报 -> 断连期间上报 -> 恢复后续传"""
    phase1 = phase2 = phase3 = 0
    pending_during = 0
    flush_result = None

    # 阶段 1: 正常上报
    wrapper.set_connected(True)
    for i in range(n_before):
        eid, acc, pend, err = wrapper.ingest(make_event("DSHB_HA_1", i))
        if acc:
            phase1 += 1

    # 阶段 2: 断连
    wrapper.set_connected(False)
    for i in range(n_during):
        eid, acc, pend, err = wrapper.ingest(make_event("DSHE_HA_1", 100 + i))
        if pend:
            pending_during += 1

    # 模拟断连持续时间
    time.sleep(pause_seconds)

    # 阶段 3: 恢复 + 续传
    wrapper.set_connected(True)
    flush_result = wrapper.flush_pending()
    for i in range(n_after):
        eid, acc, pend, err = wrapper.ingest(make_event("HERMES_HA_1", 200 + i))
        if acc:
            phase3 += 1

    final_stats = wrapper.stats()
    # 验证: 所有事件最终都在 store 中
    stored = load_store(wrapper.store_path)

    return {
        "scenario": "断连重试",
        "phase1_connected": phase1,
        "phase2_during_outage_pending": pending_during,
        "phase3_after_recovery": phase3,
        "flush_added": flush_result[0],
        "flush_deduped": flush_result[1],
        "flush_remaining": flush_result[2],
        "final_store_events": final_stats["store_events"],
        "final_pending": final_stats["pending"],
        "final_checkpoint": final_stats["checkpoint_events"],
        "no_event_lost": final_stats["store_events"] >=
            (phase1 + pending_during + phase3),
        "pending_cleared": final_stats["pending"] == 0,
    }


# ---------------------------------------------------------------------------
# 场景 4: 持久化 (进程重启恢复)
# ---------------------------------------------------------------------------
def scenario_persistence(wrapper, n_events=30):
    """上报 -> 断连 -> 新实例加载 checkpoint -> 恢复后续传"""
    # 写入并制造断连缓存
    wrapper.set_connected(True)
    for i in range(n_events):
        wrapper.ingest(make_event("DSHB_PERSIST_1", i))

    # 断连, 缓存一批
    wrapper.set_connected(False)
    cached_ids = []
    for i in range(n_events):
        eid, acc, pend, err = wrapper.ingest(
            make_event("DSHE_PERSIST_1", 500 + i))
        cached_ids.append(eid)

    # 模拟进程重启: 新建 wrapper 实例 (从 checkpoint 恢复)
    wrapper2 = HAStoreWrapper(wrapper.store_path,
                              checkpoint_path=wrapper.checkpoint_path,
                              connected=True)

    loaded_pending = len(wrapper2.pending)
    # 续传
    added, deduped, remaining = wrapper2.flush_pending()

    stored = load_store(wrapper.store_path)
    recovered = 0
    for eid in cached_ids:
        if eid in {e["event_id"] for e in stored}:
            recovered += 1

    return {
        "scenario": "持久化/进程重启",
        "events_before_disconnect": n_events,
        "cached_during_outage": len(cached_ids),
        "checkpoint_loaded": loaded_pending,
        "flush_added": added,
        "recovered_from_store": recovered,
        "recovery_rate": round(recovered / len(cached_ids) * 100, 2)
                         if cached_ids else 0,
        "checkpoint_persisted": loaded_pending == len(cached_ids),
        "full_recovery": recovered == len(cached_ids),
    }


# ---------------------------------------------------------------------------
# 场景 5: 检索查询
# ---------------------------------------------------------------------------
def scenario_query(wrapper, n_events=100):
    """按 dep/trace/fingerprint/rule/team 多维检索"""
    for i in range(n_events):
        wrapper.ingest(make_event("DSHB_QRY_1", i))

    stored = load_store(wrapper.store_path)
    checks = {
        "by_dep": len(query_events(stored, dep="DEP-REG-001")),
        "by_team_DSHB": len(query_events(stored, team="DSHB")),
        "by_rule_R-AUDIT-02": len(query_events(stored, rule="R-AUDIT-02")),
        "by_level_critical": len(
            query_events(stored, level="critical")),  # 小写不敏感
        "by_trace_exact": len(query_events(
            stored, trace="DSHB_QRY_1-T0")),
        "by_fingerprint_exact": len(query_events(
            stored, fingerprint="DSHB_QRY_1-FP0")),
        "combined_dep_and_team": len(
            query_events(stored, dep="DEP-REG-001", team="DSHB")),
        "nonexistent_trace": len(query_events(
            stored, trace="SHOULD_NOT_EXIST_9999")),
    }

    return {
        "scenario": "检索查询",
        "events_ingested": n_events,
        "store_total": len(stored),
        "checks": checks,
        "all_present_queries_hit": all(
            checks[k] > 0 for k in
            ("by_dep", "by_team_DSHB", "by_rule_R-AUDIT-02",
             "by_level_critical", "by_trace_exact", "by_fingerprint_exact",
             "combined_dep_and_team")),
        "nonexistent_returns_zero": checks["nonexistent_trace"] == 0,
    }


# ---------------------------------------------------------------------------
# 场景 6: 限流压力 (为 T3.5 铺垫)
# ---------------------------------------------------------------------------
def scenario_rate_limit(wrapper, n_events=500, burst=100):
    """突发上报, 验证存储吞吐上限"""
    results = {"accepted": 0, "failed": 0, "deduped": 0}
    start = time.time()
    # 突发 burst 条
    burst_events = [make_event("DSHB_BURST_1", i) for i in range(burst)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(wrapper.ingest, e) for e in burst_events]
        for fut in as_completed(futs):
            eid, acc, pend, err = fut.result()
            if acc:
                results["accepted"] += 1
            else:
                results["failed"] += 1

    elapsed_burst = time.time() - start
    # 常规批量
    start = time.time()
    for i in range(n_events - burst):
        eid, acc, pend, err = wrapper.ingest(make_event("DSHB_RATE_1", i))
        if acc:
            results["accepted"] += 1
    elapsed_normal = time.time() - start

    return {
        "scenario": "限流压力",
        "total_submitted": n_events,
        "burst_count": burst,
        "burst_elapsed_seconds": round(elapsed_burst, 4),
        "burst_throughput": round(burst / elapsed_burst, 1)
                            if elapsed_burst else 0,
        "normal_elapsed_seconds": round(elapsed_normal, 4),
        "normal_throughput": round(
            (n_events - burst) / elapsed_normal, 1) if elapsed_normal else 0,
        "accepted_total": results["accepted"],
        "failed_total": results["failed"],
        "final_store": len(load_store(wrapper.store_path)),
    }


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
def self_test():
    failures = []
    tmpdir = "/tmp/ha_store_selftest_%d" % os.getpid()
    os.makedirs(tmpdir, exist_ok=True)
    store = os.path.join(tmpdir, "store.jsonl")
    ckpt = store + ".pending.jsonl"

    # 1. 单条上报
    w = HAStoreWrapper(store, ckpt)
    eid, acc, pend, err = w.ingest(make_event("DSHB_ST_1", 0))
    if not (acc and eid and not err):
        failures.append("单条上报失败: acc=%s err=%s" % (acc, err))

    # 2. 并发写入无丢失
    r1 = scenario_concurrent_write(w, n_events=60, instances=6, concurrency=6)
    if not r1["no_data_loss"]:
        failures.append("并发写入数据丢失: stored=%d < accepted=%d"
                        % (r1["stored_after"], r1["accepted"]))
    if r1["errors"] > 0:
        failures.append("并发写入出现校验错误: %d" % r1["errors"])

    # 3. 去重
    r2 = scenario_dedup(w, n_events=20, repeat_factor=3)
    if not r2["dedup_correct"]:
        failures.append("去重不准确: %d/%d" % (r2["dedup_verified"], 20))
    if not r2["no_duplication"]:
        failures.append("去重产生重复记录: %d" % r2["unique_stored"])

    # 4. 断连重试
    store2 = os.path.join(tmpdir, "store2.jsonl")
    ckpt2 = store2 + ".pending.jsonl"
    w2 = HAStoreWrapper(store2, ckpt2)
    r3 = scenario_disconnect_retry(w2, n_before=10, n_during=15,
                                   n_after=5, pause_seconds=0.05)
    if not r3["no_event_lost"]:
        failures.append("断连重试丢事件: store=%d < 提交总数"
                        % r3["final_store_events"])
    if not r3["pending_cleared"]:
        failures.append("续传后 pending 未清空: %d" % r3["final_pending"])
    if r3["flush_added"] != r3["phase2_during_outage_pending"]:
        failures.append("续传数不符: flush=%d pending=%d"
                        % (r3["flush_added"],
                           r3["phase2_during_outage_pending"]))

    # 5. 持久化 (进程重启)
    store3 = os.path.join(tmpdir, "store3.jsonl")
    ckpt3 = store3 + ".pending.jsonl"
    r4 = scenario_persistence(HAStoreWrapper(store3, ckpt3), n_events=10)
    if not r4["checkpoint_persisted"]:
        failures.append("checkpoint 未持久化: loaded=%d cached=%d"
                        % (r4["checkpoint_loaded"], r4["cached_during_outage"]))
    if not r4["full_recovery"]:
        failures.append("重启后未完全恢复: %d/%d"
                        % (r4["recovered_from_store"],
                           r4["cached_during_outage"]))

    # 6. 检索
    store4 = os.path.join(tmpdir, "store4.jsonl")
    w4 = HAStoreWrapper(store4, store4 + ".pending.jsonl")
    r5 = scenario_query(w4, n_events=30)
    if not r5["all_present_queries_hit"]:
        failures.append("检索命中不全: %s" % r5["checks"])
    if not r5["nonexistent_returns_zero"]:
        failures.append("不存在的 trace 应返回 0")

    # 7. 断连时 ingest 不抛异常且进缓存
    store5 = os.path.join(tmpdir, "store5.jsonl")
    w5 = HAStoreWrapper(store5, store5 + ".pending.jsonl",
                        connected=False)
    eid, acc, pend, err = w5.ingest(make_event("DSHE_ST_1", 0))
    if not (pend and not acc and not err):
        failures.append("断连时未进缓存: acc=%s pend=%s err=%s"
                        % (acc, pend, err))
    s5 = w5.stats()
    if s5["pending"] != 1:
        failures.append("断连缓存数错误: %d" % s5["pending"])

    # 8. 限流压力无失败
    store6 = os.path.join(tmpdir, "store6.jsonl")
    w6 = HAStoreWrapper(store6, store6 + ".pending.jsonl")
    r6 = scenario_rate_limit(w6, n_events=100, burst=30)
    if r6["failed_total"] > 0:
        failures.append("限流压力出现失败: %d" % r6["failed_total"])

    # 9. 清理
    for f in os.listdir(tmpdir):
        p = os.path.join(tmpdir, f)
        if os.path.isfile(p):
            os.remove(p)
    os.rmdir(tmpdir)

    print("event_store_ha_test 自检")
    print("  场景数: 6 (并发写入/去重/断连重试/持久化/检索/限流)")
    print("-" * 52)
    if failures:
        for f in failures:
            print("  ❌ %s" % f)
        print("  结论: SELF-TEST FAILED")
        return 1
    print("  1. 并发写入: 60 包, 丢失=%s, 错误=%d"
          % (r1["no_data_loss"], r1["errors"]))
    print("  2. 去重: %d 唯一 (本次), store 总计 %d, 准确=%s"
          % (r2["this_run_unique_stored"], r2["store_total"],
             r2["dedup_correct"]))
    print("  3. 断连重试: 缓存 %d, 续传 %d, 无丢失=%s"
          % (r3["phase2_during_outage_pending"], r3["flush_added"],
             r3["no_event_lost"]))
    print("  4. 持久化: checkpoint 恢复=%s, 完全恢复=%s"
          % (r4["checkpoint_persisted"], r4["full_recovery"]))
    print("  5. 检索: 7 维命中=%s, 不存在返回0=%s"
          % (r5["all_present_queries_hit"], r5["nonexistent_returns_zero"]))
    print("  6. 限流: %d 包, 失败=%d" % (r6["total_submitted"],
                                          r6["failed_total"]))
    print("  ✅ 9 项自检全部通过")
    print("  结论: SELF-TEST PASSED")
    return 0


# ---------------------------------------------------------------------------
# Markdown 报告
# ---------------------------------------------------------------------------
def render_markdown(results, meta):
    lines = []
    lines.append("# V86-RC2 事件存储高可用仿真报告")
    lines.append("")
    lines.append("> 生成: event_store_ha_test v%s / 基线 %s"
                 % (HA_VERSION, BRANCH_BASELINE))
    lines.append("> 存储: audit_event_store.py (JSONL 追加式 + event_id 幂等去重)")
    lines.append("> 契约: EVIDENCE_CONTRACT_V1")
    lines.append("> 日期: 2026-10-15")
    lines.append("")
    lines.append("## 1. 仿真概览")
    lines.append("")
    lines.append("| 场景 | 关键指标 | 结论 |")
    lines.append("|------|---------|------|")
    r = results
    lines.append("| 多源并发写入 | %d 包, %d 实例, 丢失=%s | %s |"
                 % (r["concurrent"]["submitted"], r["concurrent"]["instances"],
                    r["concurrent"]["no_data_loss"],
                    "✅" if r["concurrent"]["no_data_loss"] else "❌"))
    lines.append("| 重复事件去重 | %d 提交 -> %d 唯一 | %s |"
                 % (r["dedup"]["submitted"], r["dedup"]["this_run_unique_stored"],
                    "✅" if r["dedup"]["dedup_correct"] else "❌"))
    lines.append("| 断连重试 | 缓存 %d, 续传 %d, 丢失=%s | %s |"
                 % (r["disconnect"]["phase2_during_outage_pending"],
                    r["disconnect"]["flush_added"],
                    not r["disconnect"]["no_event_lost"],
                    "✅" if r["disconnect"]["no_event_lost"] else "❌"))
    lines.append("| 持久化/重启 | checkpoint=%s, 恢复率 %.1f%% | %s |"
                 % (r["persistence"]["checkpoint_persisted"],
                    r["persistence"]["recovery_rate"],
                    "✅" if r["persistence"]["full_recovery"] else "❌"))
    lines.append("| 检索查询 | %d 事件, 7 维命中=%s | %s |"
                 % (r["query"]["store_total"],
                    r["query"]["all_present_queries_hit"],
                    "✅" if r["query"]["all_present_queries_hit"] else "❌"))
    lines.append("| 限流压力 | %d 包, 突发 %d, 失败=%d | %s |"
                 % (r["rate_limit"]["total_submitted"],
                    r["rate_limit"]["burst_count"],
                    r["rate_limit"]["failed_total"],
                    "✅" if r["rate_limit"]["failed_total"] == 0 else "❌"))
    lines.append("")
    lines.append("## 2. 多源并发写入")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    for k, v in r["concurrent"].items():
        if k not in ("scenario",):
            lines.append("| %s | %s |" % (k, v))
    lines.append("")
    lines.append("## 3. 重复事件去重")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    for k, v in r["dedup"].items():
        if k != "scenario":
            lines.append("| %s | %s |" % (k, v))
    lines.append("")
    lines.append("## 4. 断连重试 (核心 HA)")
    lines.append("")
    lines.append("```")
    lines.append("阶段 1 (连接正常): 上报 %d 条 -> 全部落盘"
                 % r["disconnect"]["phase1_connected"])
    lines.append("阶段 2 (网络闪断): 上报 %d 条 -> 进 pending 缓存"
                 % r["disconnect"]["phase2_during_outage_pending"])
    lines.append("阶段 3 (恢复连接): flush_pending() 续传 %d 条, "
                 "去重折叠 %d"
                 % (r["disconnect"]["flush_added"],
                    r["disconnect"]["flush_deduped"]))
    lines.append("最终状态: store=%d 条, pending=%d, checkpoint=%d"
                 % (r["disconnect"]["final_store_events"],
                    r["disconnect"]["final_pending"],
                    r["disconnect"]["final_checkpoint"]))
    lines.append("事件零丢失: %s | pending 清空: %s"
                 % (r["disconnect"]["no_event_lost"],
                    r["disconnect"]["pending_cleared"]))
    lines.append("```")
    lines.append("")
    lines.append("## 5. 持久化 / 进程重启")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    for k, v in r["persistence"].items():
        if k != "scenario":
            lines.append("| %s | %s |" % (k, v))
    lines.append("")
    lines.append("## 6. 检索查询 (多维)")
    lines.append("")
    lines.append("| 检索维度 | 命中数 |")
    lines.append("|---------|--------|")
    for k, v in r["query"]["checks"].items():
        lines.append("| %s | %d |" % (k, v))
    lines.append("")
    lines.append("## 7. 限流压力")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    for k, v in r["rate_limit"].items():
        if k != "scenario":
            lines.append("| %s | %s |" % (k, v))
    lines.append("")
    lines.append("## 8. 结论")
    lines.append("")
    all_pass = all([
        r["concurrent"]["no_data_loss"],
        r["dedup"]["dedup_correct"],
        r["disconnect"]["no_event_lost"],
        r["persistence"]["full_recovery"],
        r["query"]["all_present_queries_hit"],
        r["rate_limit"]["failed_total"] == 0,
    ])
    lines.append("**%s 高可用仿真结论: %s**"
                 % ("✅" if all_pass else "❌",
                    "PASS" if all_pass else "FAIL"))
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 事件存储高可用仿真器")
    ap.add_argument("--self-test", action="store_true", help="自检")
    ap.add_argument("--demo", action="store_true", help="全场景仿真")
    ap.add_argument("--md", help="Markdown 报告路径")
    ap.add_argument("--json", dest="json_out", help="JSON 输出路径")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.demo:
        ap.print_help()
        return 2

    print("=" * 66)
    print("  V86-RC2 事件存储高可用仿真  v%s" % HA_VERSION)
    print("=" * 66)

    tmpdir = "/tmp/ha_store_%s" % time.strftime("%Y%m%d%H%M%S")
    os.makedirs(tmpdir, exist_ok=True)
    store = os.path.join(tmpdir, "store.jsonl")
    ckpt = store + ".pending.jsonl"

    # 场景 1
    w = HAStoreWrapper(store, ckpt)
    print("\n[场景 1] 多源并发写入 (6 实例 x 200 包, 并发 6)")
    r1 = scenario_concurrent_write(w, n_events=200, instances=6, concurrency=6)
    print("  提交 %d, 落盘 %d, 丢失=%s, 吞吐 %.1f 包/秒, 去重折叠 %d"
          % (r1["submitted"], r1["accepted"], r1["no_data_loss"],
             r1["throughput_per_sec"], r1["dedup_collapsed"]))

    # 场景 2
    print("\n[场景 2] 重复事件去重 (50 事件 x 4 次重复)")
    r2 = scenario_dedup(w, n_events=50, repeat_factor=4)
    print("  提交 %d, 本次唯一 %d, 去重准确 %s (%.1f%%)"
          % (r2["submitted"], r2["this_run_unique_stored"],
             r2["dedup_correct"], r2["dedup_accuracy"]))

    # 场景 3 (独立 store, 避免污染)
    store3 = os.path.join(tmpdir, "store3.jsonl")
    w3 = HAStoreWrapper(store3, store3 + ".pending.jsonl")
    print("\n[场景 3] 断连重试 (30 前 + 40 断连中 + 20 后)")
    r3 = scenario_disconnect_retry(w3, n_before=30, n_during=40,
                                   n_after=20, pause_seconds=0.1)
    print("  阶段1=%d, 断连缓存=%d, 续传=%d, 无丢失=%s, pending清空=%s"
          % (r3["phase1_connected"], r3["phase2_during_outage_pending"],
             r3["flush_added"], r3["no_event_lost"], r3["pending_cleared"]))

    # 场景 4
    store4 = os.path.join(tmpdir, "store4.jsonl")
    print("\n[场景 4] 持久化 / 进程重启 (30 正常 + 30 断连缓存)")
    r4 = scenario_persistence(HAStoreWrapper(store4,
                                             store4 + ".pending.jsonl"),
                              n_events=30)
    print("  checkpoint恢复=%s, 完全恢复=%s (%.1f%%)"
          % (r4["checkpoint_persisted"], r4["full_recovery"],
             r4["recovery_rate"]))

    # 场景 5
    store5 = os.path.join(tmpdir, "store5.jsonl")
    w5 = HAStoreWrapper(store5, store5 + ".pending.jsonl")
    print("\n[场景 5] 检索查询 (100 事件, 7 维检索)")
    r5 = scenario_query(w5, n_events=100)
    print("  7 维命中=%s, 不存在返回0=%s"
          % (r5["all_present_queries_hit"], r5["nonexistent_returns_zero"]))

    # 场景 6
    store6 = os.path.join(tmpdir, "store6.jsonl")
    w6 = HAStoreWrapper(store6, store6 + ".pending.jsonl")
    print("\n[场景 6] 限流压力 (500 事件, 突发 100)")
    r6 = scenario_rate_limit(w6, n_events=500, burst=100)
    print("  突发吞吐 %.1f 包/秒, 常规吞吐 %.1f 包/秒, 失败 %d"
          % (r6["burst_throughput"], r6["normal_throughput"],
             r6["failed_total"]))

    results = {
        "concurrent": r1, "dedup": r2, "disconnect": r3,
        "persistence": r4, "query": r5, "rate_limit": r6,
    }
    meta = {"version": HA_VERSION, "baseline": BRANCH_BASELINE}

    all_pass = all([
        r1["no_data_loss"], r2["dedup_correct"], r3["no_event_lost"],
        r4["full_recovery"], r5["all_present_queries_hit"],
        r6["failed_total"] == 0,
    ])

    print("\n" + "-" * 66)
    print("  结论: %s %s" % ("✅" if all_pass else "❌",
                              "PASS" if all_pass else "FAIL"))

    if args.md:
        md = render_markdown(results, meta)
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
        print("  Markdown 报告: %s" % args.md)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"results": results, "meta": meta}, f,
                      ensure_ascii=False, indent=2)
        print("  JSON 报告: %s" % args.json_out)

    # 清理临时目录
    for f in os.listdir(tmpdir):
        p = os.path.join(tmpdir, f)
        if os.path.isfile(p):
            os.remove(p)
    os.rmdir(tmpdir)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
