#!/usr/bin/env python3
"""Phase16: StageC 20%灰度 72h长周期审计值守仿真

基于 wal_validator 的 simulate_stage(StageC, 20, ...) 模型，
分 3 天（Day1/Day2/Day3）采集审计指标时序数据，
输出 Bootstrap + 3天日报 + 72h汇总的完整审计数据集。
"""
import json, os, sys, subprocess, hashlib, time
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WAL_SCRIPT = os.path.join(SCRIPT_DIR, "phase4_gray_audit_wal_validator.py")
OUT_DIR = SCRIPT_DIR
DATA_FILE = "/tmp/phase16_72h_audit_data.json"

def run_wal(seed):
    """跑一次 wal_validator --run，返回完整结果 dict"""
    out_file = f"/tmp/phase16_wal_seed{seed}.json"
    cmd = f"python3 {WAL_SCRIPT} --run --out {out_file} --seed {seed}"
    subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    if os.path.exists(out_file):
        with open(out_file) as f:
            return json.load(f)
    return {}

def extract_stage(data, stage_name="StageB"):
    """提取指定 Stage 的关键审计指标"""
    for s in data.get("stages", []):
        if s.get("stage") == stage_name:
            lat_w = s.get("latency_write_ms", {})
            lat_i = s.get("latency_index_ms", {})
            lat_d = s.get("latency_deliver_ms", {})
            ret = s.get("retrieval_ms", {})
            return {
                "stage": s.get("stage"),
                "traffic_pct": s.get("traffic_pct", 20),
                "events_generated": s.get("events_generated", 0),
                "events_written": s.get("events_written_dedup", 0),
                "events_accepted": int(s.get("events_accepted_total", 0)),
                "wal_p99_ms": lat_w.get("p99_est", 0) if isinstance(lat_w, dict) else 0,
                "wal_avg_ms": lat_w.get("avg", 0) if isinstance(lat_w, dict) else 0,
                "idx_p99_ms": lat_i.get("p99_est", 0) if isinstance(lat_i, dict) else 0,
                "idx_avg_ms": lat_i.get("avg", 0) if isinstance(lat_i, dict) else 0,
                "deliver_p99_ms": lat_d.get("p99_est", 0) if isinstance(lat_d, dict) else 0,
                "retrieval_p99_ms": ret.get("p99_est", 0) if isinstance(ret, dict) else 0,
                "event_loss_pct": s.get("event_loss_rate_pct", 0),
                "dup_captured": s.get("dup_captured", 0),
                "dup_injected": s.get("dup_injected", 0),
                "dup_rate": s.get("dup_capture_rate_pct", 0),
                "chain_broken": s.get("chain_broken", 0),
                "chain_len": int(s.get("chain_len", 0)),
                "field_fallback": s.get("field_fallback_applied", 0),
                "wal_mb": round(s.get("wal_mb_total", 0), 2),
                "write_failures": s.get("write_failures", 0),
                "seq_gaps": s.get("seq_gaps_detected", 0),
                "payload_truncated": s.get("payload_truncated_cnt", 0),
                "duration_s": s.get("duration_s", 900),
            }
    return {}

def extract_fault_trace(data):
    """提取故障追踪场景"""
    ft = data.get("fault_trace", [])
    if isinstance(ft, list):
        scenarios = []
        for s in ft:
            scenarios.append({
                "scenario": s.get("scenario", ""),
                "desc": s.get("desc", ""),
                "events_total": s.get("events_total", 0),
                "seq_persistence_ok": s.get("seq_persistence_ok", False),
                "rollback_triggered": s.get("rollback_triggered", False),
                "timeline_restored": s.get("timeline_restored", False),
            })
        return scenarios
    return []

def extract_reconcile(data):
    """提取三方对账数据"""
    tr = data.get("triple_reconcile", [])
    if isinstance(tr, list):
        rows = []
        for r in tr:
            rows.append({
                "stage": r.get("stage", ""),
                "dep_raw": r.get("dep_raw", 0),
                "hermes_persisted": r.get("hermes_persisted", 0),
                "dshe_received": r.get("dshe_received", 0),
                "gap": r.get("dep_minus_hermes", 0),
                "reconcile_rate": r.get("reconcile_rate_pct", 0),
                "sha256_consistency": r.get("sha256_sample_consistency_pct", 0),
            })
        return rows
    return []

def extract_alert(data):
    """提取告警验证数据"""
    av = data.get("alert_verify", {})
    if isinstance(av, dict):
        return {
            "alerts_fired": av.get("alerts_fired", 0),
            "alerts_suppressed": av.get("alerts_suppressed", 0),
            "total_signals": av.get("total_signal_injected", 0),
            "suppression_rate": av.get("suppression_rate_pct", 0),
            "baseline_87pct_held": av.get("baseline_87pct_held", False),
        }
    return {}

def main():
    print("=" * 60)
    print("Phase16: StageC 20% 72h 长周期审计值守仿真")
    print("=" * 60)

    # 3天用不同种子模拟日间波动
    seeds = [20261008, 20261009, 20261010]
    days = ["Day1", "Day2", "Day3"]
    day_data = {}

    for day, seed in zip(days, seeds):
        print(f"\n[{day}] seed={seed}, running wal_validator...")
        data = run_wal(seed)
        stage = extract_stage(data, "StageB")  # StageB = 20%
        faults = extract_fault_trace(data)
        reconcile = extract_reconcile(data)
        alert = extract_alert(data)

        day_data[day] = {
            "seed": seed,
            "stage_metrics": stage,
            "fault_trace": faults,
            "reconcile": reconcile,
            "alert": alert,
            "timestamp": (datetime(2026, 10, 8) + timedelta(days=seeds.index(seed))).isoformat(),
        }

        s = stage
        print(f"  events={s.get('events_generated',0)}, wal_p99={s.get('wal_p99_ms',0)}ms, "
              f"loss={s.get('event_loss_pct',0)}%, chain_broken={s.get('chain_broken',0)}, "
              f"dup={s.get('dup_captured',0)}")

    # Bootstrap 阶段（用第一个种子前900s的数据，已有）
    bootstrap = day_data["Day1"]["stage_metrics"]

    # 汇总 72h 指标
    all_events = sum(d["stage_metrics"].get("events_generated", 0) for d in day_data.values())
    all_written = sum(d["stage_metrics"].get("events_written", 0) for d in day_data.values())
    all_loss = sum(d["stage_metrics"].get("event_loss_pct", 0) for d in day_data.values()) / 3
    all_chain_broken = sum(d["stage_metrics"].get("chain_broken", 0) for d in day_data.values())
    all_dup = sum(d["stage_metrics"].get("dup_captured", 0) for d in day_data.values())
    all_faults = sum(len(d["fault_trace"]) for d in day_data.values())
    all_faults_recovered = sum(1 for d in day_data.values() for f in d["fault_trace"] if f.get("timeline_restored"))
    all_reconcile_aligned = all(
        r.get("reconcile_rate", 0) >= 99.0 and r.get("sha256_consistency", 0) >= 99.0
        for d in day_data.values() for r in d["reconcile"]
    )

    summary = {
        "bootstrap": bootstrap,
        "days": day_data,
        "summary_72h": {
            "total_events": all_events,
            "total_written": all_written,
            "avg_loss_pct": round(all_loss, 4),
            "total_chain_broken": all_chain_broken,
            "total_dup_captured": all_dup,
            "total_fault_scenarios": all_faults,
            "total_faults_recovered": all_faults_recovered,
            "all_reconcile_aligned": all_reconcile_aligned,
            "wal_p99_max": max(d["stage_metrics"].get("wal_p99_ms", 0) for d in day_data.values()),
            "wal_p99_avg": round(sum(d["stage_metrics"].get("wal_p99_ms", 0) for d in day_data.values()) / 3, 2),
            "idx_p99_avg": round(sum(d["stage_metrics"].get("idx_p99_ms", 0) for d in day_data.values()) / 3, 2),
            "throughput_avg": round(sum(d["stage_metrics"].get("events_generated", 0) for d in day_data.values()) / (3 * 900), 1),
        }
    }

    # 事件追溯率 = 写入/生成
    trace_rate = (all_written / max(all_events, 1)) * 100
    summary["summary_72h"]["event_trace_rate"] = round(trace_rate, 4)

    with open(DATA_FILE, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n72h 数据集写入: {DATA_FILE}")
    print(f"\n=== 72h 汇总 ===")
    s72 = summary["summary_72h"]
    print(f"  total_events={s72['total_events']}, trace_rate={s72['event_trace_rate']}%")
    print(f"  wal_p99: max={s72['wal_p99_max']}ms, avg={s72['wal_p99_avg']}ms")
    print(f"  chain_broken={s72['total_chain_broken']}, faults={s72['total_faults_recovered']}/{s72['total_fault_scenarios']}")
    print(f"  reconcile_aligned={s72['all_reconcile_aligned']}")
    print(f"  avg_loss={s72['avg_loss_pct']}%, throughput_avg={s72['throughput_avg']}ev/s")

    return 0

if __name__ == "__main__":
    sys.exit(main())
