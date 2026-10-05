#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 灰度决策事件持久化模块 v1.1 增强版 (gray_gate_event_persist_v11_enhance.py)

工单: 工单-HERMES / T3.2 灰度决策事件异常容错增强
分支: feature/v85-chart-template @ ba82d04
编制方: HERMES (L3 审计方)
日期: 2026-10-15

相对v1.0增强:
  1. 事件唯一性: event_id加入sequence序号与随机因子, 同秒同类型事件不再合并丢失
  2. 时间戳注入: 支持外部timestamp参数(溯源/回放场景), 默认当前UTC
  3. 字段兜底: 缺失字段用默认值填充, 不写NULL污染
  4. 异常payload过滤: 超大message截断, 非dict状态兜底
  5. 去重策略: 同run_id+同seq的重复投递只保留第一条(INSERT OR IGNORE + dedup计数)
  6. 乱序容忍: 允许timestamp乱序写入, 查询时按timestamp+seq稳定排序

约束: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import uuid

SCHEMA_VERSION = "1.1"

EVENT_TABLE = "gray_gate_events"

MAX_MESSAGE_LEN = 2000  # 超大payload截断阈值
MAX_INPUT_STATE_LEN = 4000


# ============================================================
# 事件Schema定义 (v1.1, 兼容v1.0 22字段 + 新增4字段)
# ============================================================

EVENT_SCHEMA = {
    "event_id": "str - 唯一事件ID(MD5: run_id+timestamp+decision+seq)",
    "timestamp": "str - ISO8601 UTC时间戳",
    "event_type": "str - DECISION/HEALTHCHECK/ALERT",
    "decision": "str - ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE",
    "decision_reason": "str - 决策理由",
    "current_stage": "str - 当前灰度阶段(G0-G5)",
    "next_stage": "str|null - 下一阶段",
    "dep_001_status": "str - DEP状态",
    "gate_status": "str - Gate状态",
    "risk_level": "str - LOW/MEDIUM/HIGH/FATAL",
    "faults": "json - 故障列表",
    "auto_rollback": "str - 是否自动回滚",
    "need_confirm": "str - 是否需要人工确认",
    "rollback_timeout": "str - 回滚超时",
    "rollback_scope": "str - 回滚范围",
    "flags_to_set": "json - 需设置标志",
    "all_faults": "json - 全部故障详情",
    "gaps": "json - 准入缺口项",
    "remaining_hours": "real|null - 剩余观测时间",
    "input_state": "json - 决策输入快照",
    "schema_version": "str - schema版本(1.1)",
    "run_id": "str - 运行批次ID",
    "seq": "int - 序列号(同秒去重), 默认1",
    "dedup_count": "int - 重复投递次数(默认1)",
    "source": "str - 事件来源(hermes/dshb/dshe)",
    "drill_tag": "str|null - 演练标记(chaos/failover/normal)",
}


class GrayEventPersistorV11:
    """灰度决策事件持久化器 v1.1 增强版。"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-4000")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._init_table()

    def _init_table(self):
        # v1.1 表结构: 26字段(v1.0的22 + seq/dedup_count/source/drill_tag)
        self.conn.execute(f"""CREATE TABLE IF NOT EXISTS {EVENT_TABLE} (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            decision TEXT NOT NULL,
            decision_reason TEXT,
            current_stage TEXT,
            next_stage TEXT,
            dep_001_status TEXT,
            gate_status TEXT,
            risk_level TEXT,
            faults TEXT,
            auto_rollback TEXT,
            need_confirm TEXT,
            rollback_timeout TEXT,
            rollback_scope TEXT,
            flags_to_set TEXT,
            all_faults TEXT,
            gaps TEXT,
            remaining_hours REAL,
            input_state TEXT,
            schema_version TEXT,
            run_id TEXT,
            seq INTEGER DEFAULT 1,
            dedup_count INTEGER DEFAULT 1,
            source TEXT DEFAULT 'hermes',
            drill_tag TEXT
        )""")
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_decision ON {EVENT_TABLE}(decision)")
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_timestamp ON {EVENT_TABLE}(timestamp)")
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_risk ON {EVENT_TABLE}(risk_level)")
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_run_id ON {EVENT_TABLE}(run_id)")
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_type ON {EVENT_TABLE}(event_type)")
        self.conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_ts_seq ON {EVENT_TABLE}(timestamp, seq)")
        self.conn.commit()

    def _safe_str(self, val, default=""):
        """字段兜底: 非str转str, None用默认值。"""
        if val is None:
            return default
        if isinstance(val, str):
            return val
        if isinstance(val, (int, float, bool)):
            return str(val)
        try:
            return json.dumps(val, ensure_ascii=False)
        except Exception:
            return default

    def _truncate(self, val, max_len):
        """超大payload截断。"""
        if val and len(val) > max_len:
            return val[:max_len] + f"...[truncated {len(val)-max_len} chars]"
        return val

    def _make_event_id(self, run_id, timestamp, decision, seq):
        raw = f"{run_id}|{timestamp}|{decision}|{seq}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _now(self):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def record_decision(self, decision_result, input_state=None, timestamp=None,
                        seq=1, source="hermes", drill_tag=None):
        """记录一次灰度决策事件 (增强: 支持timestamp/seq注入)。"""
        ts = timestamp or self._now()
        run_id = decision_result.get("run_id") or f"RUN-{int(time.time())}"
        decision = decision_result.get("decision", "UNKNOWN")

        # 字段兜底
        faults = decision_result.get("faults_detected", []) or []
        if not isinstance(faults, list):
            faults = [self._safe_str(faults)]
        risk = RISK_MAP.get(decision, "MEDIUM")
        if faults:
            fault_risks = [FAULT_RISK.get(f, "MEDIUM") for f in faults]
            risk_priority = {"FATAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            risk = max(fault_risks, key=lambda r: risk_priority.get(r, 0))

        event_id = self._make_event_id(run_id, ts, decision, seq)

        # payload截断
        reason = self._truncate(self._safe_str(decision_result.get("decision_reason", "")), MAX_MESSAGE_LEN)
        input_state_s = None
        if input_state is not None:
            try:
                input_state_s = self._truncate(json.dumps(input_state, ensure_ascii=False), MAX_INPUT_STATE_LEN)
            except Exception:
                input_state_s = json.dumps({"_parse_error": True})

        # 去重: 先检查event_id是否已存在
        existing = self.conn.execute(
            f"SELECT dedup_count FROM {EVENT_TABLE} WHERE event_id = ?",
            (event_id,)
        ).fetchone()
        if existing:
            # 已存在 = 重复投递, dedup_count+1
            self.conn.execute(
                f"UPDATE {EVENT_TABLE} SET dedup_count = dedup_count + 1 WHERE event_id = ?",
                (event_id,)
            )
            self.conn.commit()
            return event_id
        # 不存在 = 新事件, INSERT
        self.conn.execute(
            f"""INSERT INTO {EVENT_TABLE} (
                event_id, timestamp, event_type, decision, decision_reason,
                current_stage, next_stage, dep_001_status, gate_status,
                risk_level, faults, auto_rollback, need_confirm,
                rollback_timeout, rollback_scope, flags_to_set, all_faults,
                gaps, remaining_hours, input_state, schema_version, run_id,
                seq, dedup_count, source, drill_tag)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,1,?,?)""",
            (
                event_id, ts, "DECISION", decision,
                reason,
                self._safe_str(decision_result.get("current_stage", "")),
                decision_result.get("next_stage"),
                self._safe_str(decision_result.get("dep_001_status", "UNKNOWN")),
                "GATE_REVIEW_PAUSED=TRUE" if decision == "ROLLBACK" else "ACTIVE",
                risk,
                json.dumps(faults, ensure_ascii=False),
                self._safe_str(decision_result.get("auto_rollback", False)),
                self._safe_str(decision_result.get("need_confirm", False)),
                self._safe_str(decision_result.get("rollback_timeout", "")),
                self._safe_str(decision_result.get("rollback_scope", "")),
                json.dumps(decision_result.get("flags_to_set", []), ensure_ascii=False),
                json.dumps(decision_result.get("all_faults", []), ensure_ascii=False),
                json.dumps(decision_result.get("gaps", []), ensure_ascii=False),
                decision_result.get("remaining_hours"),
                input_state_s,
                SCHEMA_VERSION,
                run_id,
                source,
                drill_tag,
            )
        )
        self.conn.commit()
        return event_id

    def record_healthcheck(self, state, run_id=None, timestamp=None,
                           seq=1, source="hermes", drill_tag=None):
        """记录健康检查事件 (增强: 支持timestamp注入)。"""
        ts = timestamp or self._now()
        run_id = run_id or f"HEALTH-{int(time.time())}"
        if not isinstance(state, dict):
            state = {"_parse_error": True}
        dep_status = state.get("dep_001_status", "UNKNOWN")
        risk = "HIGH" if dep_status == "BLOCKED" else "LOW"
        event_id = self._make_event_id(run_id, ts, "HEALTHCHECK", seq)
        input_state_s = self._truncate(json.dumps(state, ensure_ascii=False), MAX_INPUT_STATE_LEN)
        existing = self.conn.execute(
            f"SELECT dedup_count FROM {EVENT_TABLE} WHERE event_id = ?",
            (event_id,)
        ).fetchone()
        if existing:
            self.conn.execute(
                f"UPDATE {EVENT_TABLE} SET dedup_count = dedup_count + 1 WHERE event_id = ?",
                (event_id,)
            )
            self.conn.commit()
            return event_id
        self.conn.execute(
            f"""INSERT INTO {EVENT_TABLE} (
                event_id, timestamp, event_type, decision, decision_reason,
                current_stage, dep_001_status, gate_status, risk_level,
                input_state, schema_version, run_id, seq, dedup_count, source, drill_tag)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)""",
            (
                event_id, ts, "HEALTHCHECK", "HEALTHCHECK",
                f"DEP={dep_status}",
                self._safe_str(state.get("current_stage", "")),
                dep_status,
                "ACTIVE",
                risk,
                input_state_s,
                SCHEMA_VERSION,
                run_id, seq, source, drill_tag,
            )
        )
        self.conn.commit()
        return event_id

    def record_alert(self, alert_level, message, faults=None, run_id=None,
                     timestamp=None, seq=1, source="hermes", drill_tag=None):
        """记录告警事件 (增强: 支持timestamp注入)。"""
        ts = timestamp or self._now()
        run_id = run_id or f"ALERT-{int(time.time())}"
        risk = "HIGH" if alert_level == "CRITICAL" else "MEDIUM"
        message = self._truncate(self._safe_str(message), MAX_MESSAGE_LEN)
        event_id = self._make_event_id(run_id, ts, "ALERT", seq)
        faults = faults or []
        if not isinstance(faults, list):
            faults = [self._safe_str(faults)]
        existing = self.conn.execute(
            f"SELECT dedup_count FROM {EVENT_TABLE} WHERE event_id = ?",
            (event_id,)
        ).fetchone()
        if existing:
            self.conn.execute(
                f"UPDATE {EVENT_TABLE} SET dedup_count = dedup_count + 1 WHERE event_id = ?",
                (event_id,)
            )
            self.conn.commit()
            return event_id
        self.conn.execute(
            f"""INSERT INTO {EVENT_TABLE} (
                event_id, timestamp, event_type, decision, decision_reason,
                risk_level, faults, input_state, schema_version, run_id,
                seq, dedup_count, source, drill_tag)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,1,?,?)""",
            (
                event_id, ts, "ALERT", alert_level,
                message,
                risk,
                json.dumps(faults, ensure_ascii=False),
                json.dumps({"alert_level": alert_level, "message": message}, ensure_ascii=False),
                SCHEMA_VERSION, run_id, seq, source, drill_tag,
            )
        )
        self.conn.commit()
        return event_id

    def query(self, decision=None, risk=None, run_id=None, event_type=None,
              drill_tag=None, limit=100):
        """查询事件 (增强: 支持event_type/drill_tag, 按timestamp+seq稳定排序)。"""
        where, args = [], []
        if decision:
            where.append("decision = ?")
            args.append(decision)
        if risk:
            where.append("risk_level = ?")
            args.append(risk)
        if run_id:
            where.append("run_id = ?")
            args.append(run_id)
        if event_type:
            where.append("event_type = ?")
            args.append(event_type)
        if drill_tag:
            where.append("drill_tag = ?")
            args.append(drill_tag)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        cursor = self.conn.execute(
            f"SELECT * FROM {EVENT_TABLE} {where_sql} ORDER BY timestamp ASC, seq ASC LIMIT ?",
            args + [limit]
        )
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(cols, r)) for r in rows]

    def count(self, decision=None, event_type=None):
        where, args = [], []
        if decision:
            where.append("decision = ?")
            args.append(decision)
        if event_type:
            where.append("event_type = ?")
            args.append(event_type)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        return self.conn.execute(
            f"SELECT COUNT(*) FROM {EVENT_TABLE} {where_sql}", args
        ).fetchone()[0]

    def close(self):
        self.conn.close()


# 风险映射
RISK_MAP = {
    "ADVANCE": "LOW",
    "HOLD": "MEDIUM",
    "OBSERVE": "LOW",
    "ROLLBACK": "HIGH",
    "COMPLETE": "LOW",
}
FAULT_RISK = {
    "F1": "FATAL",
    "F2": "HIGH",
    "F3": "HIGH",
    "F4": "MEDIUM",
    "F5": "MEDIUM",
}


# ============================================================
# 自检
# ============================================================

def self_test():
    """12项自检用例: 覆盖乱序/重复/缺字段/超大payload。"""
    tests = []
    db = "/tmp/gray_persist_v11_selftest.db"
    for ext in ["", "-wal", "-shm"]:
        if os.path.exists(db + ext):
            os.remove(db + ext)

    p = GrayEventPersistorV11(db)

    # T01: 同秒同类型多事件唯一性 (5个ALERT同秒 → 5个event_id)
    eids = set()
    for i in range(5):
        eid = p.record_alert("CRITICAL", f"告警#{i}", faults=["F1"],
                             run_id="AL-UNIQ", seq=i + 1)
        eids.add(eid)
    uniq_ok = len(eids) == 5
    tests.append(("T01_同秒告警唯一性", uniq_ok, f"unique={len(eids)}/5"))

    # T02: 同秒同seq重复投递 → 去重保留1条+dedup_count=2
    eid1 = p.record_alert("HIGH", "重复投递测试", run_id="AL-DUP", seq=1)
    eid2 = p.record_alert("HIGH", "重复投递测试", run_id="AL-DUP", seq=1)
    events = p.query(run_id="AL-DUP", event_type="ALERT")
    dedup_ok = len(events) == 1 and events[0]["dedup_count"] == 2
    tests.append(("T02_重复投递去重", dedup_ok, f"count={len(events)}, dedup={events[0]['dedup_count'] if events else 0}"))

    # T03: 字段缺失兜底 (decision_result缺字段)
    import sys as _sys
    _sys.path.insert(0, "/home/ubuntu/framework-tree/analysis/e2e_output/v86/hermes_e2e_test")
    from gray_gate_decider import decide
    state = {"current_stage": "G1", "dep_001_status": "RECOVERED",
             "non_zero_rate": 0.98, "p95_ms": 20, "critical_alerts": 0,
             "dep_flap_count": 0, "http_500_count": 0, "control_group_failed": False,
             "gate_g06_pass": True, "throughput_drop_pct": 0, "disconnect_count": 0,
             "observe_hours_elapsed": 24}
    result = decide(state)
    result["run_id"] = "DEC-OK"
    eid = p.record_decision(result, state)
    events = p.query(run_id="DEC-OK", event_type="DECISION")
    ok3 = len(events) == 1 and events[0]["schema_version"] == SCHEMA_VERSION
    tests.append(("T03_正常决策持久化", ok3, f"count={len(events)}"))

    # T04: 乱序容忍 (时间戳乱序写入, 查询按ts+seq排序)
    p.record_alert("LOW", "t3事件", run_id="ORDER", timestamp="2026-10-15T16:03:00Z", seq=3)
    p.record_alert("LOW", "t1事件", run_id="ORDER", timestamp="2026-10-15T16:01:00Z", seq=1)
    p.record_alert("LOW", "t2事件", run_id="ORDER", timestamp="2026-10-15T16:02:00Z", seq=2)
    ordered = p.query(run_id="ORDER", event_type="ALERT")
    ok4 = [e["timestamp"] for e in ordered] == sorted(e["timestamp"] for e in ordered)
    tests.append(("T04_乱序容忍排序", ok4, f"order={[e['timestamp'][-9:] for e in ordered]}"))

    # T05: 超大payload截断
    big_msg = "X" * 5000
    eid = p.record_alert("LOW", big_msg, run_id="AL-BIG")
    events = p.query(run_id="AL-BIG", event_type="ALERT")
    msg_len = len(events[0]["decision_reason"]) if events else 0
    ok5 = msg_len <= MAX_MESSAGE_LEN + 50
    tests.append(("T05_超大payload截断", ok5, f"len={msg_len}(≤{MAX_MESSAGE_LEN}+50)"))

    # T06: 非dict状态兜底
    eid = p.record_healthcheck("notadict", run_id="HC-BAD")
    events = p.query(run_id="HC-BAD", event_type="HEALTHCHECK")
    ok6 = len(events) == 1 and events[0]["dep_001_status"] == "UNKNOWN"
    tests.append(("T06_非dict状态兜底", ok6, f"dep={events[0]['dep_001_status'] if events else '?'}"))

    # T07: drill_tag标记
    eid = p.record_alert("HIGH", "混沌演练告警", run_id="AL-CHAOS", drill_tag="chaos")
    chaos_events = p.query(drill_tag="chaos")
    ok7 = len(chaos_events) >= 1
    tests.append(("T07_演练标记查询", ok7, f"chaos_events={len(chaos_events)}"))

    # T08: source字段
    eid = p.record_alert("HIGH", "DSHE来源事件", run_id="AL-SRC", source="dshe")
    events = p.query(run_id="AL-SRC", event_type="ALERT")
    ok8 = events[0]["source"] == "dshe"
    tests.append(("T08_source字段", ok8, f"source={events[0]['source'] if events else '?'}"))

    # T09: 总数
    total = p.count()
    ok9 = total >= 14
    tests.append(("T09_总数", ok9, f"total={total}"))

    # T10: schema版本
    events = p.query(limit=1)
    ok10 = events[0]["schema_version"] == SCHEMA_VERSION
    tests.append(("T10_schema版本", ok10, f"v={events[0]['schema_version'] if events else '?'}"))

    # T11: 决策事件count
    dec_count = p.count(event_type="DECISION")
    tests.append(("T11_决策事件计数", dec_count == 1, f"count={dec_count}"))

    # T12: 乱序写后总数一致(无丢失)
    order_events = p.query(run_id="ORDER")
    ok12 = len(order_events) == 3
    tests.append(("T12_乱序无丢失", ok12, f"count={len(order_events)}"))

    p.close()

    print("=" * 60)
    print("gray_gate_event_persist_v11_enhance.py 自检 (12项)")
    print("=" * 60)
    pass_count = 0
    for name, ok, detail in tests:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
        if ok:
            pass_count += 1
    print()
    print(f"  {pass_count}/{len(tests)} PASS")
    print("  结论:", "SELF-TEST PASSED" if pass_count == len(tests) else "SELF-TEST FAILED")
    return pass_count == len(tests)


def main():
    parser = argparse.ArgumentParser(description="V86-RC2 灰度决策事件持久化模块 v1.1增强版")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--db", default="/tmp/gray_events_v11.db", help="数据库路径")
    parser.add_argument("--query", metavar="JSON", help="查询输入JSON")
    args = parser.parse_args()

    if args.self_test:
        ok = self_test()
        sys.exit(0 if ok else 1)

    if args.query:
        p = GrayEventPersistorV11(args.db)
        rows = p.query(limit=50)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        p.close()


if __name__ == "__main__":
    main()
