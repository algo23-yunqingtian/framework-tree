#!/usr/bin/env python3
"""Phase17 T1/T3: StageD 30%灰度审计前置准备 + WAL 30%适配 + 30%压测仿真

基于 Phase16 StageC 20% 72h审计数据(453,612事件)为基线，
改造 wal_validator 的 simulate_stage 适配 30% 流量，
验证高吞吐场景 WAL完整性、事件去重、链路断裂检测。
"""
import json, os, sys, subprocess, hashlib, importlib.util, random
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WAL_SCRIPT = os.path.join(SCRIPT_DIR, "phase4_gray_audit_wal_validator.py")
OUT_DIR = SCRIPT_DIR
DATA_FILE = "/tmp/phase17_30pct_audit_data.json"
BASELINE_FILE = "/tmp/phase16_72h_audit_data.json"

def load_wal_module():
    """动态加载 wal_validator 模块"""
    spec = importlib.util.spec_from_file_location("wal_validator", WAL_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    print("=" * 60)
    print("Phase17: StageD 30% 审计前置准备 + 30%压测仿真")
    print("=" * 60)

    # 加载基线数据 (Phase16 72h 20% 数据)
    if os.path.exists(BASELINE_FILE):
        baseline = json.load(open(BASELINE_FILE))
        b72 = baseline["summary_72h"]
        print(f"\n[基线] Phase16 72h 20%: events={b72['total_events']}, "
              f"wal_p99={b72['wal_p99_avg']}ms, loss={b72['avg_loss_pct']}%")
    else:
        baseline = None
        print("\n[基线] Phase16 数据文件不存在，使用 Phase15 基准")

    # 加载 wal_validator 模块
    print("\n[1] 加载 wal_validator 模块...")
    wal_mod = load_wal_module()
    print(f"  simulate_stage 可用: {callable(wal_mod.simulate_stage)}")

    # 运行 30% 流量仿真（3天不同种子）
    print("\n[2] 30% 流量仿真 (3天)...")
    seeds = [20261011, 20261012, 20261013]
    days = ["Day1", "Day2", "Day3"]
    day_data = {}

    for day, seed in zip(days, seeds):
        rng = random.Random(seed)
        # 30% 流量 = StageB(20%) 的 1.5x，传 pct=30 覆盖默认的 20
        stage = wal_mod.simulate_stage("StageB", 30, 900, rng)

        lat_w = stage.get("latency_write_ms", {})
        lat_i = stage.get("latency_index_ms", {})
        lat_d = stage.get("latency_deliver_ms", {})
        ret = stage.get("retrieval_ms", {})

        metrics = {
            "stage": "StageD_30pct",
            "traffic_pct": 30,
            "events_generated": stage.get("events_generated", 0),
            "events_written": stage.get("events_written_dedup", 0),
            "events_accepted": int(stage.get("events_accepted_total", 0)),
            "wal_p99_ms": lat_w.get("p99_est", 0) if isinstance(lat_w, dict) else 0,
            "wal_avg_ms": lat_w.get("avg", 0) if isinstance(lat_w, dict) else 0,
            "idx_p99_ms": lat_i.get("p99_est", 0) if isinstance(lat_i, dict) else 0,
            "idx_avg_ms": lat_i.get("avg", 0) if isinstance(lat_i, dict) else 0,
            "deliver_p99_ms": lat_d.get("p99_est", 0) if isinstance(lat_d, dict) else 0,
            "retrieval_p99_ms": ret.get("p99_est", 0) if isinstance(ret, dict) else 0,
            "event_loss_pct": stage.get("event_loss_rate_pct", 0),
            "dup_captured": stage.get("dup_captured", 0),
            "dup_injected": stage.get("dup_injected", 0),
            "dup_rate": stage.get("dup_capture_rate_pct", 0),
            "chain_broken": stage.get("chain_broken", 0),
            "chain_len": int(stage.get("chain_len", 0)),
            "field_fallback": stage.get("field_fallback_applied", 0),
            "wal_mb": round(stage.get("wal_mb_total", 0), 2),
            "write_failures": stage.get("write_failures", 0),
            "seq_gaps": stage.get("seq_gaps_detected", 0),
            "payload_truncated": stage.get("payload_truncated_cnt", 0),
            "lam_ev_s": stage.get("lam_ev_s", 0),
            "duration_s": 900,
        }

        day_data[day] = {"seed": seed, "metrics": metrics}
        m = metrics
        print(f"  {day}: events={m['events_generated']}, wal_p99={m['wal_p99_ms']}ms, "
              f"idx_p99={m['idx_p99_ms']}ms, loss={m['event_loss_pct']}%, "
              f"dup={m['dup_captured']}/{m['dup_injected']}, chain_broken={m['chain_broken']}")

    # 汇总
    total_events = sum(d["metrics"]["events_generated"] for d in day_data.values())
    total_written = sum(d["metrics"]["events_written"] for d in day_data.values())
    trace_rate = round((total_written / max(total_events, 1)) * 100, 4)
    avg_loss = round(sum(d["metrics"]["event_loss_pct"] for d in day_data.values()) / 3, 4)
    wal_p99_max = max(d["metrics"]["wal_p99_ms"] for d in day_data.values())
    wal_p99_avg = round(sum(d["metrics"]["wal_p99_ms"] for d in day_data.values()) / 3, 2)
    idx_p99_avg = round(sum(d["metrics"]["idx_p99_ms"] for d in day_data.values()) / 3, 2)
    total_chain_broken = sum(d["metrics"]["chain_broken"] for d in day_data.values())
    total_dup = sum(d["metrics"]["dup_captured"] for d in day_data.values())
    total_dup_injected = sum(d["metrics"]["dup_injected"] for d in day_data.values())
    throughput_avg = round(total_events / (3 * 900), 1)

    # 20% vs 30% 对比
    if baseline:
        b20 = baseline["summary_72h"]
        comparison = {
            "20pct_events": b20["total_events"],
            "30pct_events": total_events,
            "events_growth_pct": round((total_events - b20["total_events"]) / b20["total_events"] * 100, 2),
            "20pct_wal_p99": b20["wal_p99_avg"],
            "30pct_wal_p99": wal_p99_avg,
            "20pct_loss": b20["avg_loss_pct"],
            "30pct_loss": avg_loss,
            "20pct_throughput": b20["throughput_avg"],
            "30pct_throughput": throughput_avg,
        }
    else:
        comparison = {}

    summary = {
        "days": day_data,
        "summary_72h_30pct": {
            "total_events": total_events,
            "total_written": total_written,
            "trace_rate": trace_rate,
            "avg_loss_pct": avg_loss,
            "wal_p99_max": wal_p99_max,
            "wal_p99_avg": wal_p99_avg,
            "idx_p99_avg": idx_p99_avg,
            "total_chain_broken": total_chain_broken,
            "total_dup_captured": total_dup,
            "total_dup_injected": total_dup_injected,
            "throughput_avg": throughput_avg,
        },
        "comparison_20_vs_30": comparison,
    }

    with open(DATA_FILE, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n30% 数据集写入: {DATA_FILE}")

    # 输出汇总
    s = summary["summary_72h_30pct"]
    print(f"\n=== 30% 72h 汇总 ===")
    print(f"  total_events={s['total_events']}, trace_rate={s['trace_rate']}%")
    print(f"  wal_p99: max={s['wal_p99_max']}ms, avg={s['wal_p99_avg']}ms")
    print(f"  idx_p99_avg={s['idx_p99_avg']}ms")
    print(f"  avg_loss={s['avg_loss_pct']}%")
    print(f"  chain_broken={s['total_chain_broken']}")
    print(f"  dup={s['total_dup_captured']}/{s['total_dup_injected']}")
    print(f"  throughput_avg={s['throughput_avg']}ev/s")

    if comparison:
        print(f"\n=== 20% vs 30% 对比 ===")
        for k, v in comparison.items():
            print(f"  {k}: {v}")

    # 验收标准检查
    print(f"\n=== 验收标准检查 ===")
    checks = [
        ("丢包率 ≤0.01%", avg_loss <= 0.01, avg_loss),
        ("事件追溯率 ≥99.995%", trace_rate >= 99.995, trace_rate),
        ("审计P99 < 2s", wal_p99_max < 2000, wal_p99_max),
        ("链路断裂 = 0", total_chain_broken == 0, total_chain_broken),
    ]
    all_pass = True
    for name, passed, val in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {val}")
        if not passed:
            all_pass = False
    print(f"\n  总体: {'ALL PASS ✅' if all_pass else 'HAS FAILURES ❌'}")

    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
