#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 Phase8 T2 —— 500 万行数据集灌入（远端集群替代：本机最大可行样本）
==========================================================================
背景:
  Phase7 因本机 1GB 可用内存仅完成 250 万行实测。Phase8 工单要求
  "在远端测试集群部署 500 万行数据集"补齐大样本实测。
  T0 实测: 生产 DB `/var/lib/hermes/gray_gate_events.db` 不存在，
  `find / -name gray_gate_events.db` 0 命中，远端测试集群无访问凭据。
  故以本机最大可行样本 500 万行替代（可用内存 1.5GB + swap 6.7GB），
  并如实标注"非远端集群"口径差异（风险 B-14）。

用法:
  python3 phase8_5m_collect.py          # 建表 + 灌入 500 万行
  （若 DB 已存在且行数达标则自动跳过，可直接重跑）

后续:
  python3 phase8_5m_bench.py            # 3 状态检索压测 + 存储 + WAL P99 + 延后索引基线

产出: /tmp/p8_5m.db（5,000,000 行 / 22 列 / WAL / integrity_check=ok）
"""
import json, os, sqlite3, time

ROWS = 5_000_000
DB = "/tmp/p8_5m.db"
BATCH = 200_000
BASE_TS = 1_700_000_000.0

COLS = [
    "event_id TEXT PRIMARY KEY", "ts REAL NOT NULL", "seq INTEGER NOT NULL",
    "run_id TEXT NOT NULL", "event_type TEXT", "decision TEXT", "severity TEXT",
    "fault_code TEXT", "drill_tag TEXT", "stage TEXT", "gate_name TEXT",
    "metric_name TEXT", "metric_value REAL", "threshold REAL", "payload TEXT",
    "source_team TEXT", "audit_chain_id TEXT", "prev_hash TEXT", "hash TEXT",
    "ingest_ts REAL", "client_ts REAL", "latency_ms REAL",
]
NPARAM = len(COLS)

FAULTS = ["C1", "C2", "C3", "CF01", "CF02", None, None]
SEVS = ["INFO", "WARN", "CRITICAL", None]
DECS = ["PASS", "ROLLBACK", "FUSE", "OBSERVE"]
DRILLS = ["gray", "chaos", "prod"]
TEAMS = ["DSHB", "HERMES", "DSHE"]


def row_exists(db):
    """DB 中 gray_gate_events 行数（表不存在返回 0）"""
    try:
        c = sqlite3.connect(db)
        return c.execute("SELECT COUNT(*) FROM gray_gate_events").fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def build_table(conn):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=FILE")
    conn.execute("PRAGMA cache_size=-65536")
    conn.execute("PRAGMA page_size=4096")
    conn.execute("CREATE TABLE gray_gate_events (" + ", ".join(COLS) + ")")
    conn.commit()


def load_rows(conn, target, batch):
    """分批灌入；返回 (rows_done, elapsed)"""
    base_ts, seq, done, t0 = BASE_TS, 0, 0, time.time()
    ph = ",".join("?" * NPARAM)
    ins = f"INSERT INTO gray_gate_events VALUES ({ph})"
    while done < target:
        n = min(batch, target - done)
        data = []
        for _ in range(n):
            seq += 1
            ts = base_ts + seq * 0.02
            data.append((
                f"e{seq:09d}", ts, seq, f"run{seq % 20000:05d}",
                "GATE_PASS" if seq % 7 == 0 else "METRIC_ALERT",
                DECS[seq % 4], SEVS[seq % 4], FAULTS[seq % 7], DRILLS[seq % 3],
                "StageA" if seq % 4 == 0 else "StageB",
                f"gate_{seq % 20}", f"m_{seq % 50}",
                round(10 + (seq % 1000) / 10.0, 2), 100.0,
                json.dumps({"k": seq % 10, "v": seq % 100}),
                TEAMS[seq % 3], f"ac{seq % 5000}",
                f"h{seq:08x}", f"h{seq+1:08x}",
                ts + 0.001, ts - 0.002, round(1 + (seq % 50) / 10.0, 2),
            ))
        conn.executemany(ins, data)
        conn.commit()
        done += n
        if done % 1_000_000 == 0:
            print(f"  已灌 {done:,}/{target:,} 行  耗时 {time.time()-t0:7.1f}s  "
                  f"磁盘 {os.path.getsize(DB)/1048576:.0f}MB")
    return done, time.time() - t0


def main():
    print(f"[T2] 500 万行数据集灌入  DB={DB}  目标={ROWS:,} 行")
    if row_exists(DB) >= ROWS:
        cnt = row_exists(DB)
        print(f"[T2] ⏭️ 数据已存在（{cnt:,} 行 ≥ {ROWS:,}），跳过灌入")
        print(f"[T2] 磁盘 {os.path.getsize(DB)/1048576:.1f}MB  "
              f"完整性 {sqlite3.connect(DB).execute('PRAGMA integrity_check').fetchone()[0]}")
        return

    if os.path.exists(DB):
        os.remove(DB)
        for ext in ("_wal", "_shm"):
            if os.path.exists(DB + ext):
                os.remove(DB + ext)

    conn = sqlite3.connect(DB, timeout=120)
    print("[T2] 建表 + 配置 WAL...")
    build_table(conn)
    print("[T2] 灌数据中...")
    done, elapsed = load_rows(conn, ROWS, BATCH)

    cnt = conn.execute("SELECT COUNT(*) FROM gray_gate_events").fetchone()[0]
    ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
    raw_mb = os.path.getsize(DB) / 1048576
    cols = [r[1] for r in conn.execute("PRAGMA table_info(gray_gate_events)")]
    conn.close()

    print(f"\n[T2] ✅ 灌数据完成")
    print(f"     行数      : {cnt:,}  (目标 {ROWS:,} {'✅' if cnt == ROWS else '❌'})")
    print(f"     列数      : {len(cols)}")
    print(f"     磁盘      : {raw_mb:.1f} MB")
    print(f"     完整性    : {ok}")
    print(f"     耗时      : {elapsed:.1f} s  ({done/elapsed:,.0f} 行/s)")
    print(f"[T2] 下一步: python3 phase8_5m_bench.py")


if __name__ == "__main__":
    main()
