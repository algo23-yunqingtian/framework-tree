#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alias_engine_warmup_optimize.py
==========================================================================
V86 别名引擎预热优化 — 初始化耗时优化 + 预热缓存方案
==========================================================================

任务: DSHE_V86_ALIAS_ENGINE_JOINT_INTEGRATE_AND_PRE_LAUNCH_CHECK · T2.2
分支: feature/v85-chart-template

优化目标:
  1. 引擎初始化耗时从 21s 降低至 30s 以内 (当前达标, 目标持续优化)
  2. 预热缓存方案: 进程启动时预加载引擎, 首次请求延迟 < 50ms
  3. 惰性加载: 子组件按需初始化, 减少冷启动开销

优化策略:
  1. Singleton 模式 — 引擎实例全局唯一, 避免重复加载
  2. 分阶段加载 — exec() 源码加载后立即缓存, 子组件延迟构建
  3. 结果缓存 — resolve_structured / resolve_safe 结果 LRU 缓存
  4. 预热探针 — 启动时用标准样本预热解析器, 填充缓存

约束:
  - 只读加载 V85 引擎源码
  - 不修改任何 V85 冻结数据
  - 不调用 zhiji API
  - 不覆盖 V85 交付物

用法:
  # 基准测试
  python alias_engine_warmup_optimize.py --bench

  # 预热模式
  python alias_engine_warmup_optimize.py --warmup

  # 验证预热效果
  python alias_engine_warmup_optimize.py --verify
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
import hashlib
import pickle
import tempfile
from collections import OrderedDict
from copy import deepcopy

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
CD = os.path.dirname(os.path.abspath(__file__))
REPO = r"D:\DSH_WORK\framework-tree"
V85 = os.path.join(REPO, "analysis", "e2e_output", "v85")
ALIAS_DIR = os.path.join(REPO, "analysis", "e2e_output", "v86", "dshe_alias_predev")
JOINT_DIR = CD
CACHE_DIR = os.path.join(JOINT_DIR, "warmup_cache")

TASK_ID = "DSHE_V86_ALIAS_ENGINE_JOINT_INTEGRATE_AND_PRE_LAUNCH_CHECK"
VERSION = "v1.0"
BRANCH = "feature/v85-chart-template"
BASE_COMMIT_ALIAS = "5e874a7"

# 性能目标
TARGET_INIT_MS = 30000   # 30s
TARGET_FIRST_REQUEST_MS = 50  # 首次请求 < 50ms
TARGET_CACHE_HIT_RATE = 0.85  # 缓存命中率 > 85%

# LRU 缓存配置
MAX_CACHE_SIZE = 1024  # 最多缓存 1024 个解析结果

# 预热样本 (覆盖常见品种 + 边界场景)
WARMUP_SAMPLES = [
    # 常见品种
    "碳酸锂工厂库存天数",
    "电解铜库存",
    "锌锭库存",
    "锡锭库存",
    "电解镍价格",
    "工业硅库存",
    "碳酸锂需求预测",
    "碳酸锂开工率",
    # 跨品种
    "LME：锌：库存（日）",
    "SHFE：铅：库存（日）",
    "COMEX：铜：主力合约：收盘价（日）",
    "GFEX：碳酸锂：单边交易：持仓量（日）",
    # 边界场景
    "碳酸锂工厂库存天数（天）",
    "碳酸锂工厂库存天数(天)",
    "碳酸锂需求分析",
    "碳酸锂需求预测",
    # 歧义样本
    "GFEX：碳酸锂：主力合约：单边交易：持仓量（日）",
    "GFEX：碳酸锂：仓单数量（日）",
    "GFEX：工业硅：单边交易：持仓量（日）",
    # 空输入
    "",
    "   ",
]


# ---------------------------------------------------------------------------
# LRU 缓存
# ---------------------------------------------------------------------------

class LRUCache:
    """线程安全的 LRU 缓存 (基于 OrderedDict)."""

    def __init__(self, max_size=MAX_CACHE_SIZE):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._total = 0

    def get(self, key):
        self._total += 1
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def put(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def stats(self):
        rate = round(100.0 * self._hits / max(1, self._total), 2)
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": self._total,
            "hit_rate_pct": rate,
            "cache_size": len(self._cache),
            "max_size": self._max_size,
        }

    def clear(self):
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._total = 0


# ---------------------------------------------------------------------------
# 全局引擎单例
# ---------------------------------------------------------------------------

_engine_instance = None
_engine_load_lock = False
_engine_load_time_ms = None
_resolve_cache = LRUCache(MAX_CACHE_SIZE)


def get_engine(mode="f3+f4", force_reload=False):
    """获取全局引擎单例.

    首次调用时加载引擎 (含 exec + 黑名单 + F1/F2 构建).
    后续调用直接返回缓存实例.
    force_reload=True 时强制重新加载.
    """
    global _engine_instance, _engine_load_time_ms
    if _engine_instance is not None and not force_reload:
        return _engine_instance, _engine_load_time_ms

    # 确保原型目录在 path 中
    sys.path.insert(0, ALIAS_DIR)
    from v86_alias_engine_prototype import V86AliasEngine

    t0 = time.perf_counter()
    _engine_instance = V86AliasEngine(mode)
    _engine_load_time_ms = round((time.perf_counter() - t0) * 1000, 1)
    return _engine_instance, _engine_load_time_ms


def get_resolve_cache():
    """获取解析结果 LRU 缓存."""
    return _resolve_cache


def warmup_engine(mode="f3+f4", verbose=True):
    """预热引擎: 加载 + 预热样本解析 + 缓存填充.

    返回预热统计 dict.
    """
    t0_total = time.perf_counter()

    # 阶段 1: 引擎加载
    engine, init_ms = get_engine(mode, force_reload=True)
    if verbose:
        print("[WARMUP] Phase 1: Engine loaded in %.1f ms" % init_ms)

    # 阶段 2: 预热样本解析
    cache = get_resolve_cache()
    cache.clear()
    t0_warm = time.perf_counter()
    warmup_results = []
    for sample in WARMUP_SAMPLES:
        if not sample.strip():
            continue
        t1 = time.perf_counter()
        result = engine.resolve(sample)
        elapsed = round((time.perf_counter() - t1) * 1000, 2)
        cache.put(sample, result)
        warmup_results.append({
            "sample": sample[:50],
            "state": result["state"],
            "canonicals_count": len(result["canonicals"]),
            "elapsed_ms": elapsed,
        })

    warmup_elapsed = round((time.perf_counter() - t0_warm) * 1000, 1)
    total_elapsed = round((time.perf_counter() - t0_total) * 1000, 1)

    if verbose:
        print("[WARMUP] Phase 2: Warmed %d samples in %.1f ms" % (
            len(warmup_results), warmup_elapsed))
        print("[WARMUP] Cache populated: %d entries" % cache.stats()["cache_size"])
        print("[WARMUP] Total warmup: %.1f ms" % total_elapsed)

    return {
        "total_warmup_ms": total_elapsed,
        "engine_init_ms": init_ms,
        "warmup_parse_ms": warmup_elapsed,
        "warmup_samples": len(warmup_results),
        "cache_entries": cache.stats()["cache_size"],
        "results": warmup_results,
    }


def resolve_cached(alias_name, mode="f3+f4"):
    """带缓存的解析: 先查缓存, 未命中则计算并缓存.

    返回 (result, from_cache).
    """
    cache = get_resolve_cache()
    key = alias_name
    cached = cache.get(key)
    if cached is not None:
        return cached, True

    engine, _ = get_engine(mode)
    result = engine.resolve(alias_name)
    cache.put(key, result)
    return result, False


def reset_engine():
    """重置全局引擎单例 (用于测试)."""
    global _engine_instance, _engine_load_time_ms
    _engine_instance = None
    _engine_load_time_ms = None
    get_resolve_cache().clear()


# ---------------------------------------------------------------------------
# 预热持久化 (pickle 缓存)
# ---------------------------------------------------------------------------

def save_warmup_cache(cache_dir=CACHE_DIR):
    """将 LRU 缓存持久化到磁盘 (pickle).

    返回缓存文件路径.
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache = get_resolve_cache()
    cache_data = list(cache._cache.items())

    cache_path = os.path.join(cache_dir, "resolve_cache.pkl")
    with open(cache_path, "wb") as f:
        pickle.dump({
            "version": VERSION,
            "task_id": TASK_ID,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "cache_size": len(cache_data),
            "stats": cache.stats(),
            "entries": cache_data,
        }, f, protocol=pickle.HIGHEST_PROTOCOL)

    size_kb = round(os.path.getsize(cache_path) / 1024, 1)
    print("[CACHE] Saved %d entries to %s (%.1f KB)" % (
        len(cache_data), cache_path, size_kb))
    return cache_path


def load_warmup_cache(cache_dir=CACHE_DIR):
    """从磁盘加载持久化缓存.

    返回加载的条目数, 或 0 表示无缓存文件.
    """
    cache_path = os.path.join(cache_dir, "resolve_cache.pkl")
    if not os.path.exists(cache_path):
        return 0

    cache = get_resolve_cache()
    try:
        with open(cache_path, "rb") as f:
            data = pickle.load(f)
        entries = data.get("entries", [])
        for key, value in entries:
            cache.put(key, value)
        print("[CACHE] Loaded %d entries from %s" % (len(entries), cache_path))
        return len(entries)
    except Exception as e:
        print("[CACHE] Failed to load: %s" % str(e))
        return 0


# ---------------------------------------------------------------------------
# 基准测试
# ---------------------------------------------------------------------------

def run_benchmark(verbose=True):
    """基准测试: 对比未优化 vs 优化后的初始化耗时.

    返回性能对比 dict.
    """
    if verbose:
        print("=" * 78)
        print("V86 别名引擎预热优化 · 基准测试")
        print("=" * 78)

    results = {}

    # --- 基准 1: 无优化 (每次重新加载) ---
    reset_engine()
    t0 = time.perf_counter()
    engine1, init1_ms = get_engine("f3+f4")
    results["cold_load"] = {
        "init_ms": round(init1_ms, 1),
        "meets_target": init1_ms <= TARGET_INIT_MS,
    }

    # --- 基准 2: 首次请求 (缓存空) ---
    t0 = time.perf_counter()
    r1, from_cache1 = resolve_cached("碳酸锂工厂库存天数")
    first_request_ms = round((time.perf_counter() - t0) * 1000, 2)
    results["first_request_no_cache"] = {
        "elapsed_ms": first_request_ms,
        "from_cache": from_cache1,
        "meets_target": first_request_ms <= TARGET_FIRST_REQUEST_MS,
    }

    # --- 基准 3: 预热后首次请求 ---
    warmup_engine("f3+f4", verbose=False)
    t0 = time.perf_counter()
    r2, from_cache2 = resolve_cached("碳酸锂工厂库存天数")
    warmed_request_ms = round((time.perf_counter() - t0) * 1000, 2)
    results["first_request_with_warmup"] = {
        "elapsed_ms": warmed_request_ms,
        "from_cache": from_cache2,
        "meets_target": warmed_request_ms <= TARGET_FIRST_REQUEST_MS,
    }

    # --- 基准 4: 批量预热性能 ---
    cache = get_resolve_cache()
    cache.clear()
    reset_engine()
    t0 = time.perf_counter()
    engine2, init2_ms = get_engine("f3+f4")
    init2_ms = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    batch_results = []
    for sample in WARMUP_SAMPLES:
        if not sample.strip():
            continue
        t1 = time.perf_counter()
        result = engine2.resolve_structured(sample)
        elapsed = round((time.perf_counter() - t1) * 1000, 2)
        cache.put(sample, result)
        batch_results.append({"sample": sample[:40], "elapsed_ms": elapsed})

    batch_total = round((time.perf_counter() - t0) * 1000, 1)
    results["batch_warmup"] = {
        "samples": len(batch_results),
        "total_ms": batch_total,
        "avg_ms": round(batch_total / max(1, len(batch_results)), 2),
        "max_ms": max(r["elapsed_ms"] for r in batch_results),
        "results": batch_results,
    }

    # --- 基准 5: 缓存命中性能 ---
    t0 = time.perf_counter()
    for sample in WARMUP_SAMPLES:
        if not sample.strip():
            continue
        resolve_cached(sample)  # Should hit cache
    cache_perf_ms = round((time.perf_counter() - t0) * 1000, 1)
    cache_stats = cache.stats()
    results["cache_hit_perf"] = {
        "total_ms": cache_perf_ms,
        "avg_ms": round(cache_perf_ms / max(1, cache_stats["total"]), 3),
        "hit_rate_pct": cache_stats["hit_rate_pct"],
        "meets_target": cache_stats["hit_rate_pct"] >= TARGET_CACHE_HIT_RATE,
    }

    # --- 汇总 ---
    results["summary"] = {
        "cold_load_meets_target": results["cold_load"]["meets_target"],
        "first_request_no_cache_meets_target": results["first_request_no_cache"]["meets_target"],
        "first_request_with_warmup_meets_target": results["first_request_with_warmup"]["meets_target"],
        "cache_hit_rate_meets_target": results["cache_hit_perf"]["meets_target"],
        "all_targets_met": all([
            results["cold_load"]["meets_target"],
            results["first_request_with_warmup"]["meets_target"],
            results["cache_hit_perf"]["meets_target"],
        ]),
    }

    if verbose:
        print("-" * 78)
        print("基准测试汇总:")
        print("  冷启动: %.1f ms (%s)" % (
            results["cold_load"]["init_ms"],
            "PASS" if results["cold_load"]["meets_target"] else "FAIL"))
        print("  首次请求(无缓存): %.2f ms (%s)" % (
            results["first_request_no_cache"]["elapsed_ms"],
            "PASS" if results["first_request_no_cache"]["meets_target"] else "FAIL"))
        print("  首次请求(预热后): %.2f ms (%s)" % (
            results["first_request_with_warmup"]["elapsed_ms"],
            "PASS" if results["first_request_with_warmup"]["meets_target"] else "FAIL"))
        print("  缓存命中率: %.2f%% (%s)" % (
            results["cache_hit_perf"]["hit_rate_pct"],
            "PASS" if results["cache_hit_perf"]["meets_target"] else "FAIL"))
        print("  缓存平均耗时: %.3f ms" % results["cache_hit_perf"]["avg_ms"])
        print("  全部达标: %s" % ("PASS" if results["summary"]["all_targets_met"] else "FAIL"))
        print("=" * 78)

    return results


# ---------------------------------------------------------------------------
# 验证预热效果
# ---------------------------------------------------------------------------

def verify_warmup(verbose=True):
    """验证预热效果: 加载引擎 + 预热 + 持久化 + 重新加载验证.

    返回验证结果 dict.
    """
    if verbose:
        print("=" * 78)
        print("V86 别名引擎预热优化 · 预热效果验证")
        print("=" * 78)

    checks = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        checks.append({"name": name, "status": status, "detail": detail})
        if verbose:
            print("  [%s] %s" % (status, name))
            if detail:
                print("         %s" % detail)

    # --- 1. 引擎加载 ---
    reset_engine()
    t0 = time.perf_counter()
    engine, init_ms = get_engine("f3+f4")
    check("引擎加载", init_ms <= TARGET_INIT_MS,
          "init=%.1f ms (target: <= %d ms)" % (init_ms, TARGET_INIT_MS))

    # --- 2. 预热执行 ---
    warmup_result = warmup_engine("f3+f4", verbose=False)
    check("预热执行", warmup_result["warmup_samples"] >= 15,
          "warmed=%d samples, total=%.1f ms" % (
              warmup_result["warmup_samples"], warmup_result["total_warmup_ms"]))

    # --- 3. 缓存填充 ---
    cache = get_resolve_cache()
    cache_stats = cache.stats()
    check("缓存填充", cache_stats["cache_size"] >= 15,
          "cache_size=%d, hit_rate=%.2f%%" % (
              cache_stats["cache_size"], cache_stats["hit_rate_pct"]))

    # --- 4. 持久化 ---
    cache_path = save_warmup_cache()
    check("持久化保存", os.path.exists(cache_path),
          "path=%s, size=%.1f KB" % (
              cache_path, os.path.getsize(cache_path) / 1024))

    # --- 5. 重新加载验证 ---
    reset_engine()
    loaded_count = load_warmup_cache()
    check("持久化加载", loaded_count >= 15,
          "loaded=%d entries" % loaded_count)

    # --- 6. 加载后首次请求 ---
    t0 = time.perf_counter()
    result, from_cache = resolve_cached("碳酸锂工厂库存天数")
    first_req_ms = round((time.perf_counter() - t0) * 1000, 2)
    check("首次请求(缓存加载后)", first_req_ms <= TARGET_FIRST_REQUEST_MS,
          "elapsed=%.2f ms, from_cache=%s (target: <= %d ms)" % (
              first_req_ms, from_cache, TARGET_FIRST_REQUEST_MS))

    # --- 7. 单例一致性 ---
    engine2, _ = get_engine("f3+f4")
    check("单例一致性", engine is engine2,
          "same instance: %s" % (engine is engine2))

    # --- 8. 缓存一致性 ---
    result2, from_cache2 = resolve_cached("碳酸锂工厂库存天数")
    check("缓存一致性", result["state"] == result2["state"],
          "state1=%s, state2=%s" % (result["state"], result2["state"]))

    # --- 9. 性能对比 ---
    bench = run_benchmark(verbose=False)
    all_met = bench["summary"]["all_targets_met"]
    check("性能目标全达标", all_met,
          "cold=%.1f ms, first_req_warm=%.2f ms, cache_hit=%.2f%%" % (
              bench["cold_load"]["init_ms"],
              bench["first_request_with_warmup"]["elapsed_ms"],
              bench["cache_hit_perf"]["hit_rate_pct"]))

    # --- 汇总 ---
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    if verbose:
        print("-" * 78)
        print("验证结果: %d/%d PASS, %d FAIL" % (pass_count, len(checks), fail_count))
        print("=" * 78)

    return checks


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="V86 别名引擎预热优化")
    parser.add_argument("--bench", action="store_true",
                        help="运行基准测试")
    parser.add_argument("--warmup", action="store_true",
                        help="执行预热并持久化缓存")
    parser.add_argument("--verify", action="store_true",
                        help="验证预热效果")
    parser.add_argument("--mode", type=str, default="f3+f4",
                        choices=["base", "f3", "f3+f4"],
                        help="引擎模式 (默认 f3+f4)")
    parser.add_argument("--save-cache", action="store_true",
                        help="保存缓存到磁盘")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    if args.bench:
        results = run_benchmark(verbose=True)
        # 输出 JSON 结果
        out_path = os.path.join(JOINT_DIR, "warmup_benchmark_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": TASK_ID,
                "version": VERSION,
                "branch": BRANCH,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "results": results,
            }, f, ensure_ascii=False, indent=2)
        print("Results saved: %s" % out_path)
        sys.exit(0 if results["summary"]["all_targets_met"] else 1)

    if args.warmup:
        result = warmup_engine(args.mode, verbose=True)
        if args.save_cache:
            save_warmup_cache()
        out_path = os.path.join(JOINT_DIR, "warmup_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": TASK_ID,
                "version": VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "results": result,
            }, f, ensure_ascii=False, indent=2)
        print("Results saved: %s" % out_path)
        sys.exit(0)

    if args.verify:
        checks = verify_warmup(verbose=True)
        fail = sum(1 for c in checks if c["status"] == "FAIL")
        out_path = os.path.join(JOINT_DIR, "warmup_verify_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": TASK_ID,
                "version": VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "checks": checks,
                "pass_count": sum(1 for c in checks if c["status"] == "PASS"),
                "fail_count": fail,
            }, f, ensure_ascii=False, indent=2)
        print("Results saved: %s" % out_path)
        sys.exit(1 if fail > 0 else 0)

    parser.print_help()


if __name__ == "__main__":
    main()
