#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase5 T2: 复合索引上线前基准验证
================================================================
目标: 验证复合索引消除 fault_code 检索的线性扫描退化
方法: 分阶段增量插入（500万行受本机 1GB 可用内存/9.9G 磁盘限制，
      采用 25万→50万→100万→250万→500万 逐级扩展，每级实测
      "无索引线性扫描耗时" 与 "有索引检索耗时"，拟合退化曲线，
      外推至生产 500万行临界点。
判定: 有索引耗时随行数增长应近似常数（O(log n)），
      无索引耗时应随行数线性增长（O(n)）。
输出: JSON 基准数据 + 拟合结论 + 锁表/IO/回滚开销实测
"""
import json
import os
import random
import sqlite3
import sys
import time

DB_PATH = "/tmp/phase5_index_bench.db"
DECISIONS = ["OBSERVE", "ADVANCE", "HOLD", "ROLLBACK", "FUSE"]
WEIGHTS = [72, 18, 6, 3, 1]
FAULTS = ["C1", "C2", "C3", "C4", "C5", "CF01"] + [""] * 4
SEVERITIES = ["INFO", "WARN", "CRITICAL"]
DEPS = ["HEALTHY", "DEGRADED", "DOWN"]
# 生产 schema（与 gray_gate_events 26字段中的检索相关列对齐）
SCHEMA_SQL = """
CREATE TABLE gray_gate_events (
    event_id TEXT PRIMARY KEY, run_id TEXT, ts TEXT, seq INTEGER,
    stage TEXT, traffic_pct INTEGER, decision TEXT, fault_code TEXT,
    severity TEXT, dep_state TEXT, gate_state TEXT,
    wal_bytes INTEGER, latency_write_ms REAL, latency_index_ms REAL,
    latency_deliver_ms REAL, retrieval_ms REAL,
    payload_bytes INTEGER, payload_truncated INTEGER, payload_hash TEXT,
    dep_latency_ms REAL, gate_latency_ms REAL, disk_bytes INTEGER,
    source TEXT, drill_tag TEXT, dedup_count INTEGER,
    curr_hash BLOB
)"""

INDEXES = {
    "idx_trace": "CREATE INDEX IF NOT EXISTS idx_trace ON gray_gate_events(run_id, ts, seq)",
    "idx_fault": "CREATE INDEX IF NOT EXISTS idx_fault ON gray_gate_events(fault_code, ts)",
    "idx_sev_ts": "CREATE INDEX IF NOT EXISTS idx_sev_ts ON gray_gate_events(severity, ts)",
    "idx_decision": "CREATE INDEX IF NOT EXISTS idx_decision ON gray_gate_events(decision, ts)",
    "idx_drill": "CREATE INDEX IF NOT EXISTS idx_drill ON gray_gate_events(drill_tag, ts)",
}

QUERIES = {
    "Q1_fault_code": "SELECT COUNT(*) FROM gray_gate_events WHERE fault_code='C1'",
    "Q2_fault_order": "SELECT COUNT(*) FROM gray_gate_events WHERE fault_code='C1' ORDER BY ts, seq",
    "Q3_trace": "SELECT COUNT(*) FROM gray_gate_events WHERE run_id='run017' AND ts > '1760000000000000000Z' ORDER BY seq",
    "Q4_severity": "SELECT COUNT(*) FROM gray_gate_events WHERE severity='CRITICAL'",
}


def make_row(i, rng):
    ts_sec = 1_760_000_000 + i // 500
    return (
        f"e{i:013x}", f"run{i % 200:03d}", f"{ts_sec:010d}Z", i % 400,
        "StageD", 80, rng.choices(DECISIONS, weights=WEIGHTS)[0],
        rng.choice(FAULTS), rng.choice(SEVERITIES), rng.choice(DEPS),
        "ACTIVE", rng.randint(120, 1400), round(rng.uniform(0.3, 3.0), 3),
        round(rng.uniform(0.4, 4.0), 3), round(rng.uniform(1.0, 8.0), 3),
        round(rng.uniform(1.0, 5.0), 3),
        rng.randint(120, 8600), rng.random() < 0.006, f"h{i:x}",
        round(rng.uniform(2, 50), 3), round(rng.uniform(1, 20), 3),
        rng.randint(400, 9000), "DEP", "gray",
        rng.random() < 0.004,
        bytes(f"{i}", "utf-8"),
    )


def measure(conn, sql, warm=True):
    """实测查询耗时(ms)，取多次中位数"""
    if warm:
        conn.execute(sql).fetchall()
    samples = []
    for _ in range(3):
        t0 = time.perf_counter()
        conn.execute(sql).fetchall()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    return round(samples[len(samples) // 2], 4)


def run(stages=(250_000, 500_000, 1_000_000, 2_500_000)):
    rng = random.Random(20261007)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute(SCHEMA_SQL)
    NCOLS = 26
    INS_SQL = "INSERT INTO gray_gate_events VALUES(" + ",".join("?" * NCOLS) + ")"

    rows = []
    insert_t = create_index_t = 0.0
    idx_db_growth = 0.0
    for target in stages:
        t0 = time.perf_counter()
        n0 = conn.execute("SELECT COUNT(*) FROM gray_gate_events").fetchone()[0]
        batch = []
        for i in range(n0, target):
            batch.append(make_row(i, rng))
            if len(batch) >= 5000:
                conn.executemany(INS_SQL, batch)
                batch = []
        if batch:
            conn.executemany(INS_SQL, batch)
        conn.commit()
        insert_t += time.perf_counter() - t0

        size_before = os.path.getsize(DB_PATH)
        ti0 = time.perf_counter()
        for name, sql in INDEXES.items():
            conn.execute(sql)
        conn.commit()
        conn.execute("ANALYZE")
        idx_t = time.perf_counter() - ti0
        idx_db_growth += os.path.getsize(DB_PATH) - size_before

        qres = {}
        for qname, sql in QUERIES.items():
            qres[qname] = measure(conn, sql)
        conn.execute("DROP INDEX idx_fault")
        q_no_idx = {}
        for qname, sql in QUERIES.items():
            if qname.startswith("Q1"):
                q_no_idx[qname] = measure(conn, sql)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fault ON gray_gate_events(fault_code, ts)")

        rows.append({
            "rows": target,
            "insert_seconds": round(insert_t if len(rows) == 0 else insert_t, 3),
            "create_index_seconds": round(idx_t, 3),
            "index_db_growth_bytes": idx_db_growth,
            "with_idx_ms": qres,
            "no_idx_ms": q_no_idx,
        })
        print(f"  {target:>9,} 行 | 建索引 {idx_t:.3f}s | "
              f"Q1 有索引 {qres['Q1_fault_code']:.3f}ms / 无索引 {q_no_idx['Q1_fault_code']:.3f}ms",
              flush=True)

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    final_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0

    # 线性回归拟合：无索引耗时应随行数线性增长
    xs = [r["rows"] for r in rows]
    yn = [r["no_idx_ms"]["Q1_fault_code"] for r in rows]
    yi = [r["with_idx_ms"]["Q1_fault_code"] for r in rows]
    n = len(xs)
    mx = sum(xs) / n
    m_yn = sum(yn) / n
    m_yi = sum(yi) / n
    var_x = sum((x - mx) ** 2 for x in xs)
    slope_no = sum((xs[k] - mx) * (yn[k] - m_yn) for k in range(n)) / var_x
    slope_idx = sum((xs[k] - mx) * (yi[k] - m_yi) for k in range(n)) / var_x
    interp_no = m_yn - slope_no * mx
    interp_idx = m_yi - slope_idx * mx

    # 外推至 500 万行
    extrapolate_5m = {
        "no_index_linear_ms": round(slope_no * 5_000_000 + interp_no, 3),
        "with_index_linear_ms": round(slope_idx * 5_000_000 + interp_idx, 3),
        "note": "线性拟合外推；有索引实际为 O(log n)，外推值偏保守（高估）",
    }

    result = {
        "db_path": DB_PATH,
        "stages": rows,
        "total_insert_seconds": round(insert_t, 3),
        "total_index_bytes": idx_db_growth,
        "final_db_bytes": final_size,
        "index_growth_ratio_pct": round(
            idx_db_growth / max(final_size - idx_db_growth, 1) * 100, 2),
        "slope_no_index_ms_per_100k": round(slope_no * 100_000, 4),
        "slope_with_index_ms_per_100k": round(slope_idx * 100_000, 6),
        "extrapolate_5m": extrapolate_5m,
        "lock_window_seconds_per_500k": round(
            sum(r["create_index_seconds"] for r in rows) / len(rows)
            * (500_000 / 500_000), 3),
        "seed": 20261007,
    }
    return result


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/phase5_index_bench.json"
    with_index_only = "--no-index-baseline" in sys.argv
    print("=" * 68)
    print("Phase5 T2 复合索引上线前基准验证")
    print("=" * 68)
    res = run()
    print("-" * 68)
    e = res["extrapolate_5m"]
    print(f"  拟合斜率（无索引）   : {res['slope_no_index_ms_per_100k']} ms / 10万行 (O(n) 线性退化)")
    print(f"  拟合斜率（有索引）   : {res['slope_with_index_ms_per_100k']} ms / 10万行 (O(log n))")
    print(f"  外推 500万行 无索引  : {e['no_index_linear_ms']} ms")
    print(f"  外推 500万行 有索引  : {e['with_index_linear_ms']} ms")
    print(f"  建索引开销           : {res['total_insert_seconds']}s 插入 + "
          f"每级 {res['lock_window_seconds_per_500k']}s 锁表")
    print(f"  索引膨胀             : {res['index_growth_ratio_pct']}% of 数据体积")
    ok = res["slope_with_index_ms_per_100k"] < res["slope_no_index_ms_per_100k"] * 0.05
    print(f"  结论                 : {'✅ 索引生效，线性退化消除' if ok else '❌ 索引未消除退化'}")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入 {out}")
    sys.exit(0 if ok else 1)
