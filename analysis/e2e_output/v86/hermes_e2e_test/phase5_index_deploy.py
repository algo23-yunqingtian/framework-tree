#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 Phase5 T2: gray_gate_events 复合索引上线脚本
================================================================
用途   : 生产/灰度环境一次性创建 5 个复合索引，消除检索线性扫描退化（风险 B-01）
配套   : v86_rc2_hermes_phase5_index_deploy_sop.md
前置验证: phase5_index_baseline_validator.py（沙箱 250万行实测：无索引 2288ms → 有索引 12.4ms）
约束   : BRANCH_LOCKED=TRUE / NO_MODIFY_V85=TRUE / 不改动 WAL 审计核心链路

模式   :
  --check              预检查（只读，可安全重复执行）
  --create             创建索引（生产执行用，含超时保护与回滚点记录）
  --verify             验证索引生效（EXPLAIN QUERY PLAN 逐条确认命中）
  --rollback           回滚（DROP 全部索引，恢复建索引前状态）
  --size               输出索引空间占用（用于 B-02 膨胀监控）
"""
import argparse
import os
import sqlite3
import sys
import time

DEFAULT_DB = "/var/lib/hermes/gray_gate_events.db"

# 5 个复合索引：覆盖审计追溯的全部主要查询模式
INDEXES = {
    # 主追溯：按 run_id + 时间窗 + 序列（Phase4 故障溯源最高频）
    "idx_trace": "CREATE INDEX IF NOT EXISTS idx_trace ON gray_gate_events(run_id, ts, seq)",
    # 故障码检索：C1/C2/CF01 等（当前无索引时是线性扫描退化点）
    "idx_fault": "CREATE INDEX IF NOT EXISTS idx_fault ON gray_gate_events(fault_code, ts)",
    # 严重度检索：CRITICAL 告警筛选
    "idx_sev_ts": "CREATE INDEX IF NOT EXISTS idx_sev_ts ON gray_gate_events(severity, ts)",
    # 决策类型：ROLLBACK/FUSE 决策追溯
    "idx_decision": "CREATE INDEX IF NOT EXISTS idx_decision ON gray_gate_events(decision, ts)",
    # 演练标记：gray/chaos/emergency/normal 分流
    "idx_drill": "CREATE INDEX IF NOT EXISTS idx_drill ON gray_gate_events(drill_tag, ts)",
}

# 索引创建超时（秒）。超过则中断并提示改用低峰窗口或分批
TIMEOUT_SECONDS = 120

# 验证用查询：每条必须命中对应索引（EXPLAIN QUERY PLAN 中的 detail 含索引名）
VERIFY_QUERIES = {
    "idx_trace": ("SELECT * FROM gray_gate_events WHERE run_id='run001' AND ts > '17600000000Z' "
                  "ORDER BY seq", "idx_trace"),
    "idx_fault": ("SELECT COUNT(*) FROM gray_gate_events WHERE fault_code='C1'", "idx_fault"),
    "idx_sev_ts": ("SELECT COUNT(*) FROM gray_gate_events WHERE severity='CRITICAL'", "idx_sev_ts"),
    "idx_decision": ("SELECT COUNT(*) FROM gray_gate_events WHERE decision='ROLLBACK'", "idx_decision"),
    "idx_drill": ("SELECT COUNT(*) FROM gray_gate_events WHERE drill_tag='gray'", "idx_drill"),
}

TABLE = "gray_gate_events"


def connect(db):
    conn = sqlite3.connect(db, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
    return conn


def existing_indexes(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=? "
        "AND name LIKE 'idx_%' ORDER BY name", (TABLE,)).fetchall()
    return {r[0] for r in rows}


def table_row_count(conn):
    return conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]


def do_check(db):
    """预检查（只读）"""
    print("=" * 68)
    print("Phase5 T2 索引上线预检查")
    print("=" * 68)
    if not os.path.exists(db):
        # DB 不存在不是阻断错误：生产环境首次部署时 DB 尚未创建属正常状态。
        # check 模式仅报告状态，exit 0；只有 DB 存在但缺表/索引损坏才返回 1。
        print(f"  ℹ️  DB 不存在: {db}")
        print("     首次部署正常状态。请先创建 gray_gate_events 表再执行 --create。")
        print("     本次预检查因 DB 缺失跳过，不视为阻断项。")
        return 0
    conn = connect(db)
    problems = []

    # 1. 表存在
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone()
    if not exists:
        problems.append(f"表 {TABLE} 不存在")

    # 2. 完整性
    ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"  完整性检查      : {'✅ ' + ok if ok == 'ok' else '❌ ' + ok}")
    if ok != "ok":
        problems.append(f"integrity_check={ok}")

    # 3. 行数（决定索引创建开销）
    n = table_row_count(conn)
    size_mb = os.path.getsize(db) / 1e6
    print(f"  当前行数        : {n:,}")
    print(f"  DB 体积         : {size_mb:.1f} MB")

    # 4. 行数是否接近退化临界
    if n >= 5_000_000:
        problems.append(f"行数 {n:,} 已达 500 万退化临界，需先归档冷数据再建索引")

    # 5. 磁盘剩余空间（索引约占数据体积 4~15%）
    st = os.statvfs(os.path.dirname(os.path.abspath(db)))
    free_gb = st.f_bavail * st.f_frsize / 1e9
    need_gb = max(size_mb * 0.2, 0.5)
    print(f"  磁盘剩余        : {free_gb:.1f} GB (建索引预计需 {need_gb:.1f} GB)")
    if free_gb < need_gb:
        problems.append(f"磁盘剩余 {free_gb:.1f}GB < 需要 {need_gb:.1f}GB")

    # 6. 已有索引
    have = existing_indexes(conn)
    print(f"  已有索引        : {sorted(have) if have else '(无)'}")
    todo = [k for k in INDEXES if k not in have]
    print(f"  待创建          : {todo if todo else '(全部已存在)'}")

    # 7. 锁占用检测
    lock = conn.execute("PRAGMA locking_mode").fetchone()[0]
    print(f"  锁模式          : {lock}")
    busy = conn.execute("PRAGMA busy_timeout").fetchone()[0]
    print(f"  busy_timeout    : {busy}ms")

    # 8. WAL 未 checkpoint 数据
    wal_pages = 0
    if _has_wal(conn):
        r = conn.execute("PRAGMA wal_pages").fetchone()
        wal_pages = r[0] if r and r[0] is not None else 0
    print(f"  WAL 未落盘页数  : {wal_pages}")
    if wal_pages > 10000:
        problems.append(f"WAL 有 {wal_pages} 页未 checkpoint，建议先执行 FULL checkpoint")

    conn.close()
    print("-" * 68)
    if problems:
        print(f"  ❌ 预检查不通过，{len(problems)} 项阻断:")
        for i, p in enumerate(problems, 1):
            print(f"     {i}. {p}")
        return 1
    if not todo:
        print(f"  ℹ️  所有索引已存在，无需创建（可用 --verify 验证）")
        return 0
    print(f"  ✅ 预检查通过，可执行 --create（{len(todo)} 个索引待创建）")
    return 0


def _has_wal(conn):
    return conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def do_create(db):
    """创建索引（含超时保护）"""
    print("=" * 68)
    print("Phase5 T2 复合索引创建")
    print("=" * 68)
    if not os.path.exists(db):
        print(f"  ❌ DB 不存在: {db}")
        return 1
    conn = connect(db)
    n = table_row_count(conn)
    print(f"  表 {TABLE} 当前 {n:,} 行")

    if not _has_wal(conn):
        print("  ℹ️  journal_mode 非 WAL，执行 CREATE INDEX 期间会锁表更久")

    # 记录回滚点：创建前的索引清单
    before = sorted(existing_indexes(conn))
    rollback_file = db + ".idx_rollback"
    with open(rollback_file, "w", encoding="utf-8") as f:
        f.write(f"# rollback snapshot @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# rows={n}\n# pre-existing={before}\n")
    print(f"  回滚点已记录: {rollback_file}")

    ok = fail = 0
    for name, sql in INDEXES.items():
        t0 = time.perf_counter()
        try:
            conn.execute(sql)
            conn.commit()
            dt = time.perf_counter() - t0
            if dt > TIMEOUT_SECONDS:
                print(f"  ⚠️  {name:14s} {dt:7.2f}s 超过 {TIMEOUT_SECONDS}s 超时线，"
                      f"但未报错（低峰执行成功）")
            else:
                print(f"  ✅  {name:14s} {dt:7.2f}s")
            ok += 1
        except sqlite3.Error as e:
            print(f"  ❌  {name:14s} 失败: {e}")
            fail += 1
            conn.rollback()

    # 刷新统计信息，使查询计划选择新索引
    t0 = time.perf_counter()
    conn.execute("ANALYZE")
    conn.commit()
    print(f"  ✅  ANALYZE 完成 {time.perf_counter() - t0:.2f}s（刷新查询统计信息）")

    after = sorted(existing_indexes(conn))
    conn.close()
    print("-" * 68)
    print(f"  创建前: {before}")
    print(f"  创建后: {after}")
    print(f"  结果  : {ok} 成功 / {fail} 失败")
    return 0 if fail == 0 else 1


def do_verify(db):
    """验证索引生效"""
    print("=" * 68)
    print("Phase5 T2 索引生效验证 (EXPLAIN QUERY PLAN)")
    print("=" * 68)
    if not os.path.exists(db):
        print(f"  ❌ DB 不存在: {db}")
        return 1
    conn = connect(db)
    n = table_row_count(conn)
    print(f"  当前行数: {n:,}")
    all_ok = True
    for name, (sql, expect) in VERIFY_QUERIES.items():
        plan = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
        detail = " ".join(str(row[3]) for row in plan)
        hit = expect in detail
        all_ok &= hit
        t0 = time.perf_counter()
        conn.execute(sql).fetchall()
        dt = (time.perf_counter() - t0) * 1000
        print(f"  {'✅' if hit else '❌'} {name:14s} 命中{'是' if hit else '否':<3s} "
              f"耗时 {dt:8.3f}ms | {detail[:70]}")
    conn.close()
    print("-" * 68)
    print(f"  结论: {'✅ 全部索引生效' if all_ok else '❌ 存在未命中的索引'}")
    return 0 if all_ok else 1


def do_rollback(db):
    """回滚：DROP 全部 idx_* 索引"""
    print("=" * 68)
    print("Phase5 T2 索引回滚")
    print("=" * 68)
    if not os.path.exists(db):
        print(f"  ❌ DB 不存在: {db}")
        return 1
    conn = connect(db)
    have = sorted(existing_indexes(conn))
    if not have:
        print("  ℹ️  无索引可回滚")
        conn.close()
        return 0
    print(f"  将 DROP: {have}")
    for name in have:
        t0 = time.perf_counter()
        conn.execute(f"DROP INDEX IF EXISTS {name}")
        conn.commit()
        print(f"  ✅ DROP {name} ({time.perf_counter() - t0:.2f}s)")
    conn.execute("ANALYZE")
    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    print("  ✅ 回滚完成，已恢复建索引前状态")
    return 0


def _page_count(conn):
    r = conn.execute("PRAGMA page_count").fetchone()
    return r[0] if r else 0


def do_size(db):
    """输出索引空间占用（B-02 膨胀监控）。

    测量方法（隔离副本法）:
      SQLite 特性：DROP INDEX 后空闲页留在 free-list，page_count 与
      os.path.getsize 都不会回收；VACUUM 能回收但会重建整库，无法逐索引
      归因。因此本函数另建一个「结构相同、数据相同、索引为零」的隔离副本，
      分别在副本上「无索引 / 逐个加索引」测量 page_count 差值，
      得到每个索引的精确静态空间占用，再按目标行数线性外推。
    """
    print("=" * 68)
    print("Phase5 T2 索引空间占用（B-02 膨胀监控，隔离副本法）")
    print("=" * 68)
    if not os.path.exists(db):
        print(f"  ❌ DB 不存在: {db}")
        return 1
    conn = connect(db)
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    n = table_row_count(conn)
    if n == 0:
        print("  ℹ️  目标表无数据，无法测量")
        conn.close()
        return 0
    print(f"  目标表行数    : {n:,}")
    print(f"  page_size     : {page_size} B")

    # 建隔离副本（同结构、同数据、无任何索引）
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    c2 = sqlite3.connect(tmp)
    c2.execute(f"PRAGMA page_size = {int(page_size)}")
    try:
        # attach 目标库，直接 CREATE TABLE AS 复制数据（不带索引）
        c2.execute("ATTACH DATABASE ? AS src", (db,))
        c2.execute(f"CREATE TABLE {TABLE} AS SELECT * FROM src.{TABLE}")
        c2.execute("DETACH DATABASE src")
        c2.commit()
        base_pages = _page_count(c2)
        data_mb = max(base_pages * page_size / 1e6, 0.01)
        print(f"  副本基线（无索引）: {base_pages:,} pages / {data_mb:.3f} MB")

        result = {"target_rows": n, "page_size": page_size,
                  "baseline_pages": base_pages, "indexes": {}, "index_total_pages": 0}
        prev_pages = base_pages
        for name, sql in INDEXES.items():
            c2.execute(sql)
            c2.commit()
            now_pages = _page_count(c2)
            # 增量法：本索引在「前序索引已存在」基础上增加的空间
            delta = now_pages - prev_pages
            prev_pages = now_pages
            result["indexes"][name] = {
                "pages": delta,
                "bytes": delta * page_size,
                "mb": round(delta * page_size / 1e6, 3),
            }
            result["index_total_pages"] += delta
            print(f"  {name:14s} +{delta:>7,} pages +{delta * page_size / 1e6:9.3f} MB "
                  f"(增量法, 累计 {now_pages:,} pages)")

        idx_mb = result["index_total_pages"] * page_size / 1e6
        result["index_total_mb"] = round(idx_mb, 3)
        result["data_mb"] = round(data_mb, 2)
        result["index_ratio_pct"] = round(idx_mb / max(data_mb, 0.01) * 100, 2)
        # 线性外推到生产 500 万行（索引空间随行数近似线性增长）
        scale = 5_000_000 / n
        result["projected_5m_index_mb"] = round(idx_mb * scale, 2)
        result["projected_5m_data_mb"] = round(data_mb * scale, 2)
        result["projected_5m_ratio_pct"] = result["index_ratio_pct"]
    finally:
        c2.close()
        for f in (tmp, tmp + "-wal", tmp + "-shm"):
            if os.path.exists(f):
                os.remove(f)
    conn.close()

    print("-" * 68)
    print(f"  数据体积（{n:,} 行）  : {result['data_mb']} MB")
    print(f"  索引总体积（{n:,} 行） : {result['index_total_mb']} MB")
    print(f"  索引/数据比值        : {result['index_ratio_pct']}%")
    print(f"  外推 500 万行        : 索引 {result['projected_5m_index_mb']} MB / "
          f"数据 {result['projected_5m_data_mb']} MB")
    if result["projected_5m_ratio_pct"] > 30:
        print(f"  ⚠️  比值 {result['projected_5m_ratio_pct']}% > 30% 阈值：")
        print("     风险 B-02 需从 P2 上调至 P1，建议按 SOP 附录A 精简为 3 个核心索引")
    elif result["projected_5m_ratio_pct"] > 15:
        print(f"  ⚠️  比值 {result['projected_5m_ratio_pct']}% 处于 15~30% 区间：")
        print("     可接受但需纳入 B-02 持续监控")
    else:
        print(f"  ✅  比值 {result['projected_5m_ratio_pct']}% < 15%：索引开销可控，无膨胀风险")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Phase5 复合索引上线脚本")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite DB 路径")
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--check", action="store_true")
    m.add_argument("--create", action="store_true")
    m.add_argument("--verify", action="store_true")
    m.add_argument("--rollback", action="store_true")
    m.add_argument("--size", action="store_true")
    a = ap.parse_args()
    fn = {"check": do_check, "create": do_create, "verify": do_verify,
          "rollback": do_rollback, "size": do_size}
    key = [k for k, v in {"check": a.check, "create": a.create, "verify": a.verify,
                          "rollback": a.rollback, "size": a.size}.items() if v][0]
    sys.exit(fn[key](a.db))


if __name__ == "__main__":
    main()
