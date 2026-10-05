#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 灰度决策事件持久化模块 (gray_gate_event_persist.py)

工单: 工单-HERMES / T3.2 灰度决策事件持久化模块开发
分支: feature/v85-chart-template @ 5ade5a2
编制方: HERMES (L3 审计方)
日期: 2026-10-15

功能:
  在gray_gate_decider每次决策后持久化结构化事件到SQLite WAL库，
  供DSHE聚合大盘消费。5类决策(ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE)全部覆盖。

用法:
  from gray_gate_event_persist import GrayEventPersistor
  p = GrayEventPersistor('/path/to/events.db')
  p.record_decision(decision_result, input_state)

约束: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time

SCHEMA_VERSION = "1.0"

EVENT_TABLE = "gray_gate_events"

# ============================================================
# 事件Schema定义
# ============================================================

EVENT_SCHEMA = {
    "event_id": "str - 唯一事件ID(MD5: run_id+timestamp+decision)",
    "timestamp": "str - ISO8601 UTC时间戳",
    "event_type": "str - DECISION(决策事件)/HEALTHCHECK(健康检查)/ALERT(告警)",
    "decision": "str - ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE",
    "decision_reason": "str - 决策理由(中文描述)",
    "current_stage": "str - 当前灰度阶段(G0-G5)",
    "next_stage": "str|null - 下一阶段(仅ADVANCE时非空)",
    "dep_001_status": "str - DEP状态(BLOCKED/RECOVERED)",
    "gate_status": "str - Gate状态(GATE_REVIEW_PAUSED=TRUE/...)",
    "risk_level": "str - LOW/MEDIUM/HIGH/FATAL",
    "faults": "json - 故障列表[F1..F5]",
    "auto_rollback": "bool - 是否自动回滚",
    "need_confirm": "bool - 是否需要人工确认",
    "rollback_timeout": "str - 回滚超时",
    "rollback_scope": "str - 回滚范围",
    "flags_to_set": "json - 需设置的标志",
    "all_faults": "json - 全部故障详情",
    "gaps": "json - 准入缺口项(仅HOLD时非空)",
    "remaining_hours": "float|null - 剩余观测时间",
    "input_state": "json - 决策输入状态快照",
    "schema_version": "str - schema版本(1.0)",
    "run_id": "str - 运行批次ID",
}

DECISION_TYPES = ["ADVANCE", "HOLD", "OBSERVE", "ROLLBACK", "COMPLETE"]

RISK_MAP = {
    "ADVANCE": "LOW",
    "HOLD": "MEDIUM",
    "OBSERVE": "LOW",
    "ROLLBACK": "HIGH",  # 可能升级FATAL
    "COMPLETE": "LOW",
}

FAULT_RISK = {
    "F1": "FATAL",
    "F2": "HIGH",
    "F3": "HIGH",
    "F4": "MEDIUM",
    "F5": "MEDIUM",
}


class GrayEventPersistor:
    """灰度决策事件持久化器。"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-4000")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self._init_table()

    def _init_table(self):
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
            run_id TEXT
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
        self.conn.commit()

    def _make_event_id(self, run_id, timestamp, decision):
        raw = f"{run_id}|{timestamp}|{decision}"
        return hashlib.md5(raw.encode()).hexdigest()

    def record_decision(self, decision_result, input_state=None):
        """记录一次灰度决策事件。"""
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run_id = decision_result.get("run_id", f"RUN-{int(time.time())}")
        decision = decision_result.get("decision", "UNKNOWN")

        # 确定风险等级
        faults = decision_result.get("faults_detected", [])
        risk = RISK_MAP.get(decision, "MEDIUM")
        if faults:
            fault_risks = [FAULT_RISK.get(f, "MEDIUM") for f in faults]
            risk_priority = {"FATAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            risk = max(fault_risks, key=lambda r: risk_priority.get(r, 0))

        event_id = self._make_event_id(run_id, ts, decision)

        self.conn.execute(
            f"""INSERT OR REPLACE INTO {EVENT_TABLE} (
                event_id, timestamp, event_type, decision, decision_reason,
                current_stage, next_stage, dep_001_status, gate_status,
                risk_level, faults, auto_rollback, need_confirm,
                rollback_timeout, rollback_scope, flags_to_set, all_faults,
                gaps, remaining_hours, input_state, schema_version, run_id)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id,
                ts,
                "DECISION",
                decision,
                decision_result.get("decision_reason", ""),
                decision_result.get("current_stage", ""),
                decision_result.get("next_stage"),
                decision_result.get("dep_001_status", "UNKNOWN"),
                "GATE_REVIEW_PAUSED=TRUE" if decision == "ROLLBACK" else "ACTIVE",
                risk,
                json.dumps(faults, ensure_ascii=False),
                str(decision_result.get("auto_rollback", False)),
                str(decision_result.get("need_confirm", False)),
                decision_result.get("rollback_timeout", ""),
                decision_result.get("rollback_scope", ""),
                json.dumps(decision_result.get("flags_to_set", []), ensure_ascii=False),
                json.dumps(decision_result.get("all_faults", []), ensure_ascii=False),
                json.dumps(decision_result.get("gaps", []), ensure_ascii=False),
                decision_result.get("remaining_hours"),
                json.dumps(input_state, ensure_ascii=False) if input_state else None,
                SCHEMA_VERSION,
                run_id,
            )
        )
        self.conn.commit()
        return event_id

    def record_healthcheck(self, state, run_id=None):
        """记录健康检查事件。"""
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run_id = run_id or f"HEALTH-{int(time.time())}"
        dep_status = state.get("dep_001_status", "UNKNOWN")
        risk = "HIGH" if dep_status == "BLOCKED" else "LOW"
        event_id = self._make_event_id(run_id, ts, "HEALTHCHECK")
        self.conn.execute(
            f"""INSERT OR REPLACE INTO {EVENT_TABLE} (
                event_id, timestamp, event_type, decision, decision_reason,
                current_stage, dep_001_status, gate_status, risk_level,
                input_state, schema_version, run_id)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id, ts, "HEALTHCHECK", "HEALTHCHECK",
                f"DEP={dep_status}",
                state.get("current_stage", ""),
                dep_status,
                "ACTIVE",
                risk,
                json.dumps(state, ensure_ascii=False),
                SCHEMA_VERSION,
                run_id,
            )
        )
        self.conn.commit()
        return event_id

    def record_alert(self, alert_level, message, faults=None, run_id=None):
        """记录告警事件。"""
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run_id = run_id or f"ALERT-{int(time.time())}"
        risk = "HIGH" if alert_level == "CRITICAL" else "MEDIUM"
        event_id = self._make_event_id(run_id, ts, "ALERT")
        self.conn.execute(
            f"""INSERT OR REPLACE INTO {EVENT_TABLE} (
                event_id, timestamp, event_type, decision, decision_reason,
                risk_level, faults, input_state, schema_version, run_id)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id, ts, "ALERT", alert_level,
                message,
                risk,
                json.dumps(faults or [], ensure_ascii=False),
                json.dumps({"alert_level": alert_level, "message": message}, ensure_ascii=False),
                SCHEMA_VERSION,
                run_id,
            )
        )
        self.conn.commit()
        return event_id

    def query(self, decision=None, risk=None, run_id=None, limit=100):
        """查询事件。"""
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
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        cursor = self.conn.execute(
            f"SELECT * FROM {EVENT_TABLE} {where_sql} ORDER BY timestamp DESC LIMIT ?",
            args + [limit]
        )
        cols = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(cols, r)) for r in rows]

    def count(self, decision=None):
        where, args = [], []
        if decision:
            where.append("decision = ?")
            args.append(decision)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        return self.conn.execute(
            f"SELECT COUNT(*) FROM {EVENT_TABLE} {where_sql}", args
        ).fetchone()[0]

    def close(self):
        self.conn.close()


# ============================================================
# 集成接口: 在gray_gate_decider.decide()后调用
# ============================================================

def persist_decision(decide_fn, state, db_path):
    """包装decide函数，决策后自动持久化。"""
    result = decide_fn(state)
    p = GrayEventPersistor(db_path)
    eid = p.record_decision(result, state)
    p.close()
    return result, eid


# ============================================================
# 自检
# ============================================================

def self_test():
    """8项自检用例。"""
    tests = []
    db = "/tmp/gray_persist_selftest.db"
    for ext in ["", "-wal", "-shm"]:
        if os.path.exists(db + ext):
            os.remove(db + ext)

    p = GrayEventPersistor(db)

    # T01: ADVANCE决策持久化
    state = {"current_stage": "G1", "dep_001_status": "RECOVERED",
             "non_zero_rate": 0.98, "p95_ms": 20, "critical_alerts": 0,
             "dep_flap_count": 0, "http_500_count": 0, "control_group_failed": False,
             "gate_g06_pass": True, "throughput_drop_pct": 0, "disconnect_count": 0,
             "observe_hours_elapsed": 24}
    sys.path.insert(0, "/home/ubuntu/framework-tree/analysis/e2e_output/v86/hermes_e2e_test")
    from gray_gate_decider import decide
    result = decide(state)
    eid = p.record_decision(result, state)
    tests.append(("T01_ADVANCE持久化", bool(eid), eid[:16]))

    # T02: ROLLBACK决策持久化
    state2 = dict(state)
    state2["http_500_count"] = 6
    state2["control_group_failed"] = True
    result2 = decide(state2)
    eid2 = p.record_decision(result2, state2)
    tests.append(("T02_ROLLBACK持久化", eid2 != eid, eid2[:16]))

    # T03: 查询验证
    adv_count = p.count(decision="ADVANCE")
    tests.append(("T03_QUERY_ADVANCE", adv_count == 1, f"count={adv_count}"))

    # T04: ROLLBACK风险等级
    rollback_events = p.query(decision="ROLLBACK", limit=1)
    risk = rollback_events[0]["risk_level"] if rollback_events else "UNKNOWN"
    tests.append(("T04_ROLLBACK_F1_FATAL", risk == "FATAL", f"risk={risk}"))

    # T05: OBSERVE决策
    state3 = dict(state)
    state3["observe_hours_elapsed"] = 10
    result3 = decide(state3)
    eid3 = p.record_decision(result3, state3)
    obs_count = p.count(decision="OBSERVE")
    tests.append(("T05_OBSERVE持久化", obs_count == 1, f"count={obs_count}"))

    # T06: HOLD决策
    state4 = dict(state)
    state4["dep_001_status"] = "BLOCKED"
    state4["current_stage"] = "G2"
    result4 = decide(state4)
    eid4 = p.record_decision(result4, state4)
    hold_count = p.count(decision="HOLD")
    tests.append(("T06_HOLD持久化", hold_count == 1, f"count={hold_count}"))

    # T07: 健康检查事件
    hc_eid = p.record_healthcheck(state, run_id="HC-001")
    tests.append(("T07_HEALTH持久化", bool(hc_eid), hc_eid[:16]))

    # T08: 告警事件
    alert_eid = p.record_alert("CRITICAL", "测试告警", faults=["F2"], run_id="AL-001")
    tests.append(("T08_ALERT持久化", bool(alert_eid), alert_eid[:16]))

    # T09: 总数验证
    total = p.count()
    tests.append(("T09_总数", total == 6, f"total={total}"))

    # T10: schema版本
    events = p.query(limit=1)
    sv = events[0]["schema_version"] if events else "?"
    tests.append(("T10_SCHEMA版本", sv == SCHEMA_VERSION, f"v={sv}"))

    p.close()

    print("=" * 60)
    print("gray_gate_event_persist.py 自检 (10项)")
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
    parser = argparse.ArgumentParser(description="V86-RC2 灰度决策事件持久化模块")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--db", default="/tmp/gray_events.db", help="数据库路径")
    parser.add_argument("--query", metavar="JSON", help="查询输入JSON")
    parser.add_argument("--decide", metavar="JSON", help="决策+持久化JSON输入")
    args = parser.parse_args()

    if args.self_test:
        ok = self_test()
        sys.exit(0 if ok else 1)

    if args.decide:
        with open(args.decide) as f:
            state = json.load(f)
        sys.path.insert(0, "/home/ubuntu/framework-tree/analysis/e2e_output/v86/hermes_e2e_test")
        from gray_gate_decider import decide
        result, eid = persist_decision(decide, state, args.db)
        print(json.dumps({"event_id": eid, "decision": result["decision"],
                          "reason": result.get("decision_reason", "")},
                         ensure_ascii=False, indent=2))

    if args.query:
        p = GrayEventPersistor(args.db)
        rows = p.query(limit=50)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        p.close()


if __name__ == "__main__":
    main()
