#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 Phase8 T2 —— 500 万行 3 核心索引检索压测 + WAL 写入 P99 采集
=====================================================================
前置: /tmp/p8_5m.db 已由 phase8_5m_collect.py 灌入 5,000,000 行（993MB）
本脚本: 3 状态检索对比(无索引/3核心/5索引) + 存储膨胀 + WAL写入P99 + 延后索引退化基线
产出: /tmp/phase8_5m.json
"""
import json, os, sqlite3, time, statistics, subprocess, sys

ROWS = 5_000_000
DB = "/tmp/p8_5m.db"
OUT = "/tmp/phase8_5m.json"
HERE = os.path.dirname(os.path.abspath(__file__))
DEPLOY = os.path.join(HERE, "phase5_index_deploy.py")

conn = sqlite3.connect(DB, timeout=300)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-65536")
cnt = conn.execute("SELECT COUNT(*) FROM gray_gate_events").fetchone()[0]
assert cnt == ROWS, f"行数不符: {cnt}"
raw_mb = round(os.path.getsize(DB) / 1048576, 2)
base_ts = 1_700_000_000.0
T0 = base_ts + 2_500_000 * 0.02   # 时间窗起点（覆盖后 50% 数据）

print(f"[T2] 500万行 3核心索引实测  DB={DB}  行数={cnt:,}  磁盘={raw_mb}MB")

out = {"rows": cnt, "raw_mb": raw_mb, "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
       "core_indexes": ["idx_trace", "idx_fault", "idx_sev_ts"],
       "extra_indexes": ["idx_decision", "idx_drill"],
       "time_window_start_ts": T0}

def run_script(*args):
    r = subprocess.run(["python3", DEPLOY, "--db", DB, *args],
                       capture_output=True, text=True, timeout=1800)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

# ---- 数据分布（选择性诊断） ----
dist = {}
for k, v in [("fault_code=C1", "SELECT COUNT(*) FROM gray_gate_events WHERE fault_code='C1'"),
             ("severity=CRITICAL", "SELECT COUNT(*) FROM gray_gate_events WHERE severity='CRITICAL'"),
             ("decision=ROLLBACK", "SELECT COUNT(*) FROM gray_gate_events WHERE decision='ROLLBACK'"),
             ("drill_tag=gray", "SELECT COUNT(*) FROM gray_gate_events WHERE drill_tag='gray'"),
             ("run_id=run00001", "SELECT COUNT(*) FROM gray_gate_events WHERE run_id='run00001'")]:
    dist[k] = conn.execute(v).fetchone()[0]
out["data_distribution"] = dist

Q = {
    "q_trace": "SELECT event_id, ts, seq, event_type, decision, severity FROM gray_gate_events "
               "WHERE run_id='run00001' AND ts > ? ORDER BY seq",
    "q_fault": "SELECT event_id, ts, severity, decision FROM gray_gate_events WHERE fault_code='C1'",
    "q_sev":   "SELECT event_id, ts, fault_code, decision FROM gray_gate_events WHERE severity='CRITICAL'",
    "q_decision": "SELECT event_id, ts, fault_code, severity FROM gray_gate_events WHERE decision='ROLLBACK'",
    "q_drill": "SELECT event_id, ts, fault_code FROM gray_gate_events WHERE drill_tag='gray'",
}

def bench(tag):
    r = {"tag": tag}
    for name, sql in Q.items():
        args = (T0,) if "?" in sql else ()
        times = []
        for _ in range(3):
            st = time.perf_counter()
            cur = conn.execute(sql, args)
            rows = cur.fetchall()
            times.append((time.perf_counter() - st) * 1000)
        r[name + "_ms"] = round(min(times), 3)
        r[name + "_rows"] = len(rows)
    return r

states = {}

# S1 无索引
conn.execute("ANALYZE"); conn.commit()
states["S1_no_index"] = bench("S1_无索引")
print(f"[T2] S1 无索引: { {k: v for k,v in states['S1_no_index'].items() if k.endswith('_ms')} }")
sys.stdout.flush()

# S2 3 核心
code, txt = run_script("--create")
out["create_core"] = {"exit": code, "tail": txt.strip().splitlines()[-6:]}
conn.execute("ANALYZE"); conn.commit()
states["S2_3core"] = bench("S2_3核心")
print(f"[T2] S2 3核心: { {k: v for k,v in states['S2_3core'].items() if k.endswith('_ms')} }")
sys.stdout.flush()

# S3 5 索引
code2, txt2 = run_script("--create", "--enable-extra-index")
out["create_extra"] = {"exit": code2, "tail": txt2.strip().splitlines()[-6:]}
conn.execute("ANALYZE"); conn.commit()
states["S3_5index"] = bench("S3_5索引")
print(f"[T2] S3 5索引: { {k: v for k,v in states['S3_5index'].items() if k.endswith('_ms')} }")
sys.stdout.flush()
out["states"] = states

# ---- 存储膨胀（脚本 --size 隔离副本法） ----
code3, size3 = run_script("--size")
code4, size5 = run_script("--size", "--enable-extra-index")
out["size_core"] = {"exit": code3, "tail": size3.strip().splitlines()[-20:]}
out["size_extra"] = {"exit": code4, "tail": size5.strip().splitlines()[-20:]}

# ---- WAL 写入 P99（synchronous=1 ≡ DSHB synchronous_commit=on） ----
conn.execute("PRAGMA synchronous=1")
wt = []
for bs in (100, 200, 500):
    samples = []
    for i in range(10):
        data = [("w%d_%d_%d" % (bs, i, j), T0 + i*0.01, -bs, "runwrite", "WRITE_TEST",
                 "PASS", "INFO", "C1", "gray", "StageA", "gate_0", "m_0", 1.0, 100.0,
                 "{}", "HERMES", "ac1", "h1", "h2", T0+i*0.01, T0+i*0.01-0.001, 1.0)
                for j in range(bs)]
        st = time.perf_counter()
        conn.executemany("INSERT INTO gray_gate_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", data)
        conn.commit()
        samples.append((time.perf_counter() - st) * 1000)
    wt.append({"batch_size": bs,
               "p50_ms": round(statistics.median(samples), 3),
               "p99_ms": round(max(samples), 3),
               "min_ms": round(min(samples), 3),
               "max_ms": round(max(samples), 3),
               "throughput_events_s": round(bs / (sum(samples)/1000), 1)})
    print(f"[T2] WAL写入 批次{bs}: P50={wt[-1]['p50_ms']}ms P99={wt[-1]['p99_ms']}ms "
          f"吞吐={wt[-1]['throughput_events_s']:.0f} ev/s")
    conn.execute("DELETE FROM gray_gate_events WHERE run_id='runwrite'"); conn.commit()
out["write_test"] = wt

# ---- 全量 5 索引 verify ----
code5, vf = run_script("--verify", "--enable-extra-index")
out["verify_full"] = {"exit": code5, "tail": vf.strip().splitlines()[-14:]}

# ---- 回滚校验（表结构零改动） ----
code6, rb = run_script("--rollback", "--enable-extra-index")
out["rollback_check"] = {"exit": code6,
                         "integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
                         "rows_after": conn.execute("SELECT COUNT(*) FROM gray_gate_events").fetchone()[0],
                         "tail": rb.strip().splitlines()[-8:]}

json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=2)
print(f"\n[T2] ✅ 结果已写入 {OUT}")
