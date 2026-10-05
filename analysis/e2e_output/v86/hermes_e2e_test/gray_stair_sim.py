#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 E2E 6 级灰度阶梯全流程 dryrun 仿真器 (gray_stair_sim.py)

工单: 工单-HERMES / T3.3 E2E 6级灰度阶梯全流程 dryrun 仿真
分支: feature/v85-chart-template @ 8fe68f3
编制方: HERMES (L3 审计方)
日期: 2026-10-15

仿真目标
--------
基于 E2E 检查清单 V2 (85 项, 6 阶段灰度) 做全阶梯 dryrun:
  G0 影子测试 (0%, 仅观测)
  G1 单品种 (1 品种 PB)
  G2 小范围 (5%)
  G3 中范围 (20%)
  G4 大范围 (50%)
  G5 全量 (100%)
在每个灰度阶段注入 5 类故障, 验证:
  1. 阶段准入阈值判定
  2. 自动暂停触发
  3. 回滚 5 类触发条件 (F1~F5)
  4. 回滚后状态正确性

故障注入
--------
  F1 链路级: 短ID HTTP 500 / 对照组失败 (致命)
  F2 审计级: CRITICAL 告警 > 0
  F3 Gate 级: G-06 未达阈值
  F4 性能级: 吞吐下降 >50% 或 p95 >200ms
  F5 稳定性级: DEP 抖动 >=3 次或断连 >5 次

用法
----
  python3 gray_stair_sim.py --self-test        # 自检
  python3 gray_stair_sim.py --run              # 全阶梯仿真
  python3 gray_stair_sim.py --fault-injection  # 故障注入仿真
  python3 gray_stair_sim.py --md <path>        # Markdown 报告

约束
----
NO_ZHIJI_API_CALL=FALSE (全 mock) / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE
本脚本纯离线, 不发网络请求。
"""

import argparse
import json
import os
import sys
import time

BRANCH_BASELINE = "8fe68f3"
SIM_VERSION = "1.0.0"

# 品种总数 (7 大类 x 8 品种 = 56, 与检查清单 V2 一致)
TOTAL_VARIETIES = 56

# 灰度阶梯定义 (检查清单 V2 §6)
STAIRS = [
    {"stage": "G0", "name": "影子测试", "ratio": 0.0, "count": 0,
     "observe_hours": 24, "exit": "5 项放行条件全满足"},
    {"stage": "G1", "name": "单品种", "ratio": 0.01, "count": 1,
     "observe_hours": 24, "exit": "无 CRITICAL 告警"},
    {"stage": "G2", "name": "5% 小范围", "ratio": 0.05, "count": 7,
     "observe_hours": 24, "exit": "数据质量稳定"},
    {"stage": "G3", "name": "20% 中范围", "ratio": 0.20, "count": 28,
     "observe_hours": 48, "exit": "无性能退化"},
    {"stage": "G4", "name": "50% 大范围", "ratio": 0.50, "count": 42,
     "observe_hours": 48, "exit": "三方台账一致"},
    {"stage": "G5", "name": "100% 全量", "ratio": 1.00, "count": 56,
     "observe_hours": 168, "exit": "观测期无回滚"},
]

# 每阶段准入阈值 (检查清单 V2 §6.2)
THRESHOLDS = {
    "G0": {"critical_max": 0, "high_max": 999, "nonzero_min": 0.0,
           "audit_tps_min": 0, "event_tps_min": 0, "p95_max": 9999,
           "ledger_match": 0.0, "dep_flap_max": 99},
    "G1": {"critical_max": 0, "high_max": 3, "nonzero_min": 0.95,
           "audit_tps_min": 5000, "event_tps_min": 100, "p95_max": 50,
           "ledger_match": 1.0, "dep_flap_max": 2},
    "G2": {"critical_max": 0, "high_max": 2, "nonzero_min": 0.98,
           "audit_tps_min": 5000, "event_tps_min": 150, "p95_max": 30,
           "ledger_match": 1.0, "dep_flap_max": 2},
    "G3": {"critical_max": 0, "high_max": 1, "nonzero_min": 0.99,
           "audit_tps_min": 8000, "event_tps_min": 200, "p95_max": 20,
           "ledger_match": 1.0, "dep_flap_max": 2},
    "G4": {"critical_max": 0, "high_max": 0, "nonzero_min": 0.995,
           "audit_tps_min": 8000, "event_tps_min": 300, "p95_max": 15,
           "ledger_match": 1.0, "dep_flap_max": 2},
    "G5": {"critical_max": 0, "high_max": 0, "nonzero_min": 0.995,
           "audit_tps_min": 8000, "event_tps_min": 300, "p95_max": 15,
           "ledger_match": 1.0, "dep_flap_max": 2},
}

# 回滚触发条件 (检查清单 V2 §7.1)
ROLLBACK_TRIGGERS = [
    {"code": "F1", "name": "链路级", "severity": "FATAL",
     "auto_rollback": True, "manual_confirm": False,
     "condition": "短ID HTTP 500 或对照组失败",
     "limit_sec": 0, "scope": "全部品种",
     "flag": "GATE_REVIEW_PAUSED=TRUE, JOB_READY=FALSE"},
    {"code": "F2", "name": "审计级", "severity": "HIGH",
     "auto_rollback": True, "manual_confirm": True,
     "condition": "CRITICAL 告警 > 0",
     "limit_sec": 1800, "scope": "当前阶段", "flag": "暂停放量"},
    {"code": "F3", "name": "Gate 级", "severity": "HIGH",
     "auto_rollback": False, "manual_confirm": True,
     "condition": "G-06 真实可取数率未达 100%",
     "limit_sec": 28800, "scope": "全部", "flag": "登记部分恢复"},
    {"code": "F4", "name": "性能级", "severity": "MEDIUM",
     "auto_rollback": False, "manual_confirm": True,
     "condition": "吞吐下降 >50% 或 p95 >200ms",
     "limit_sec": 7200, "scope": "当前阶段", "flag": "暂停放量"},
    {"code": "F5", "name": "稳定性级", "severity": "MEDIUM",
     "auto_rollback": False, "manual_confirm": True,
     "condition": "DEP 抖动 >=3 次或断连 >5 次",
     "limit_sec": 3600, "scope": "当前阶段", "flag": "评估服务稳定性"},
]

# DEP-001 短ID 解析服务当前状态
DEP_001_STATUS = "BLOCKED"  # 未就绪, GATE_DECISION=NOT_READY


# ---------------------------------------------------------------------------
# 灰度仿真器
# ---------------------------------------------------------------------------
class GrayStairSimulator:
    """6 级灰度阶梯 dryrun 仿真器。

    每个阶段:
      1. 准入判定 (THRESHOLDS)
      2. 故障注入 (可选)
      3. 观测期模拟
      4. 暂停/回滚判定
      5. 放量/回退决策
    """

    def __init__(self, dep_ready=False):
        self.dep_ready = dep_ready
        self.history = []
        self.current_stage = None
        self.rolled_back = False
        self.rollback_reason = None
        self.rollback_code = None

    # -- 准入判定 -----------------------------------------------------------
    def check_admission(self, stage_code, metrics):
        """检查阶段准入阈值。返回 (passed, failed_conditions)。"""
        th = THRESHOLDS[stage_code]
        failed = []
        checks = [
            ("critical_max", "CRITICAL 告警数",
             metrics.get("critical", 0) <= th["critical_max"]),
            ("high_max", "HIGH 告警数",
             metrics.get("high", 0) <= th["high_max"]),
            ("nonzero_min", "数据非零率",
             metrics.get("nonzero_rate", 0) >= th["nonzero_min"]),
            ("audit_tps_min", "审计吞吐(包/秒)",
             metrics.get("audit_tps", 0) >= th["audit_tps_min"]),
            ("event_tps_min", "事件存储吞吐(包/秒)",
             metrics.get("event_tps", 0) >= th["event_tps_min"]),
            ("p95_max", "审计 p95 延迟(ms)",
             metrics.get("p95_ms", 9999) <= th["p95_max"]),
            ("ledger_match", "三方台账一致率",
             metrics.get("ledger_match", 0) >= th["ledger_match"]),
            ("dep_flap_max", "DEP 抖动次数",
             metrics.get("dep_flap", 0) <= th["dep_flap_max"]),
        ]
        for key, name, ok in checks:
            if not ok:
                failed.append({"key": key, "name": name,
                               "actual": metrics.get(
                                   {"critical_max": "critical",
                                    "high_max": "high",
                                    "nonzero_min": "nonzero_rate",
                                    "audit_tps_min": "audit_tps",
                                    "event_tps_min": "event_tps",
                                    "p95_max": "p95_ms",
                                    "ledger_match": "ledger_match",
                                    "dep_flap_max": "dep_flap"}[key]),
                               "threshold": th[key]})
        # DEP-001 未就绪时, G1~G5 全部不准入 (G-06/G-10 无法通过)
        if not self.dep_ready and stage_code in ("G1", "G2", "G3", "G4", "G5"):
            failed.append({
                "key": "DEP_001",
                "name": "DEP-001 短ID 解析服务就绪",
                "actual": DEP_001_STATUS,
                "threshold": "RECOVERED"})
        return len(failed) == 0, failed

    # -- 故障检测 -----------------------------------------------------------
    def detect_rollback_trigger(self, metrics):
        """检测回滚触发条件 F1~F5。返回触发的条件列表。"""
        triggers = []
        # F1 链路级
        if metrics.get("http_500", 0) > 0 or metrics.get("control_failed", False):
            triggers.append("F1")
        # F2 审计级
        if metrics.get("critical", 0) > 0:
            triggers.append("F2")
        # F3 Gate 级
        if metrics.get("gate_g06_pass", True) is False:
            triggers.append("F3")
        # F4 性能级
        if metrics.get("throughput_drop_ratio", 0) > 0.5 or \
                metrics.get("p95_ms", 0) > 200:
            triggers.append("F4")
        # F5 稳定性级
        if metrics.get("dep_flap", 0) >= 3 or metrics.get("disconnects", 0) > 5:
            triggers.append("F5")
        return triggers

    # -- 单阶段仿真 ---------------------------------------------------------
    def simulate_stage(self, stage_code, metrics, inject_faults=None):
        """仿真单个灰度阶段。返回阶段结果。"""
        stage = next(s for s in STAIRS if s["stage"] == stage_code)
        self.current_stage = stage_code
        result = {
            "stage": stage_code,
            "name": stage["name"],
            "ratio": stage["ratio"],
            "count": stage["count"],
            "metrics": dict(metrics),
            "admission_passed": False,
            "admission_failed": [],
            "rollback_triggers": [],
            "decision": None,
            "auto_rollback": False,
            "manual_confirm_needed": False,
        }

        # 1. 准入判定
        passed, failed = self.check_admission(stage_code, metrics)
        result["admission_passed"] = passed
        result["admission_failed"] = failed

        if not passed:
            result["decision"] = "HOLD (准入未通过)"
            self.history.append(result)
            return result

        # 2. 故障注入
        injected = []
        if inject_faults:
            for f in inject_faults:
                fm = FAULT_MAP.get(f)
                if fm:
                    metrics.update(fm)
                    injected.append(f)
            result["injected_faults"] = injected
            result["metrics"] = dict(metrics)

        # 3. 故障检测
        triggers = self.detect_rollback_trigger(metrics)
        result["rollback_triggers"] = triggers

        # 4. 决策
        if triggers:
            # 按严重度排序
            priority = {"F1": 0, "F2": 1, "F3": 2, "F4": 3, "F5": 4}
            primary = sorted(triggers, key=lambda t: priority.get(t, 9))[0]
            trig_info = next(t for t in ROLLBACK_TRIGGERS
                             if t["code"] == primary)
            result["decision"] = "ROLLBACK (%s %s)" % (primary, trig_info["name"])
            result["auto_rollback"] = trig_info["auto_rollback"]
            result["manual_confirm_needed"] = trig_info["manual_confirm"]
            result["rollback_scope"] = trig_info["scope"]
            result["rollback_limit_sec"] = trig_info["limit_sec"]
            result["rollback_flag"] = trig_info["flag"]
            self.rolled_back = True
            self.rollback_reason = "%s %s" % (primary, trig_info["name"])
            self.rollback_code = primary
        else:
            result["decision"] = "ADVANCE (准入通过, 观测期达标)"
            result["observe_hours"] = stage["observe_hours"]
            result["exit_condition"] = stage["exit"]

        self.history.append(result)
        return result

    def summary(self):
        return {
            "total_stages_simulated": len(self.history),
            "current_stage": self.current_stage,
            "rolled_back": self.rolled_back,
            "rollback_reason": self.rollback_reason,
            "rollback_code": self.rollback_code,
            "dep_ready": self.dep_ready,
            "history": self.history,
        }


# ---------------------------------------------------------------------------
# 故障定义 (mock 注入)
# ---------------------------------------------------------------------------
FAULT_MAP = {
    "F1_link": {"http_500": 5, "control_failed": True},
    "F2_audit": {"critical": 2},
    "F3_gate": {"gate_g06_pass": False},
    "F4_perf": {"throughput_drop_ratio": 0.6, "p95_ms": 250},
    "F5_stability": {"dep_flap": 4, "disconnects": 6},
}


# ---------------------------------------------------------------------------
# 健康基线指标 (DEP 就绪后的理想状态)
# ---------------------------------------------------------------------------
HEALTHY_METRICS = {
    "critical": 0,
    "high": 0,
    "nonzero_rate": 0.998,
    "audit_tps": 9000,       # 实测 v3 短路后 256call ~7.2ms = 139 包/秒
                            # 但批量调度是 9273 包/秒 (全量包混合)
    "event_tps": 350,
    "p95_ms": 12,
    "ledger_match": 1.0,
    "dep_flap": 0,
    "http_500": 0,
    "control_failed": False,
    "gate_g06_pass": True,
    "throughput_drop_ratio": 0.0,
    "disconnects": 0,
}


# ---------------------------------------------------------------------------
# 自检
# ---------------------------------------------------------------------------
def self_test():
    failures = []

    # 1. DEP 未就绪: G1~G5 全部不准入
    sim1 = GrayStairSimulator(dep_ready=False)
    r = sim1.simulate_stage("G1", dict(HEALTHY_METRICS))
    if r["admission_passed"]:
        failures.append("DEP 未就绪时 G1 应不准入")
    if "DEP_001" not in [f["key"] for f in r["admission_failed"]]:
        failures.append("DEP 未就绪应报 DEP_001 失败")

    # G0 影子测试不受 DEP 阻断
    sim0 = GrayStairSimulator(dep_ready=False)
    r0 = sim0.simulate_stage("G0", dict(HEALTHY_METRICS))
    if not r0["admission_passed"]:
        failures.append("G0 影子测试应不受 DEP 阻断")

    # 2. DEP 就绪: 健康指标下 G1~G5 全部准入
    sim2 = GrayStairSimulator(dep_ready=True)
    for sc in ["G1", "G2", "G3", "G4", "G5"]:
        r = sim2.simulate_stage(sc, dict(HEALTHY_METRICS))
        if not r["admission_passed"]:
            failures.append("DEP 就绪时 %s 应准入, 失败项: %s"
                            % (sc, r["admission_failed"]))
        if r["decision"] != "ADVANCE (准入通过, 观测期达标)":
            failures.append("%s 应 ADVANCE, 实际: %s"
                            % (sc, r["decision"]))

    # 3. 5 类故障注入全部触发回滚
    for code, fm in FAULT_MAP.items():
        sim = GrayStairSimulator(dep_ready=True)
        r = sim.simulate_stage("G2", dict(HEALTHY_METRICS),
                               inject_faults=[code])
        if not r["rollback_triggers"]:
            failures.append("故障 %s 未触发回滚" % code)
        if code.replace("_", "")[:2] not in r["rollback_triggers"]:
            # F1_link -> F1
            expected = code.split("_")[0]
            if expected not in r["rollback_triggers"]:
                failures.append("故障 %s 期望触发 %s, 实际: %s"
                                % (code, expected, r["rollback_triggers"]))

    # 4. F1 自动回滚, F3/F4/F5 需人工确认
    sim = GrayStairSimulator(dep_ready=True)
    r = sim.simulate_stage("G2", dict(HEALTHY_METRICS), inject_faults=["F1_link"])
    if not r["auto_rollback"]:
        failures.append("F1 应自动回滚")
    for fc in ["F3_gate", "F4_perf", "F5_stability"]:
        s = GrayStairSimulator(dep_ready=True)
        r = s.simulate_stage("G2", dict(HEALTHY_METRICS), inject_faults=[fc])
        if r["auto_rollback"]:
            failures.append("%s 不应自动回滚 (需人工确认)" % fc)
        if not r["manual_confirm_needed"]:
            failures.append("%s 应需人工确认" % fc)

    # 5. 准入阈值边界: HIGH 告警超限
    sim = GrayStairSimulator(dep_ready=True)
    m = dict(HEALTHY_METRICS)
    m["high"] = 4  # G2 阈值 high_max=2
    r = sim.simulate_stage("G2", m)
    if r["admission_passed"]:
        failures.append("G2 HIGH=4 超过阈值 2, 应不准入")

    # 6. 阈值逐级收紧 (G1->G5)
    strictness = []
    for sc in ["G1", "G2", "G3", "G4", "G5"]:
        strictness.append(THRESHOLDS[sc]["nonzero_min"])
    if not all(strictness[i] <= strictness[i + 1]
               for i in range(len(strictness) - 1)):
        failures.append("非零率阈值应逐级收紧: %s" % strictness)

    # 7. 阈值逐级收紧 (p95 延迟)
    p95 = [THRESHOLDS[sc]["p95_max"] for sc in ["G1", "G2", "G3", "G4", "G5"]]
    if not all(p95[i] >= p95[i + 1] for i in range(len(p95) - 1)):
        failures.append("p95 阈值应逐级收紧: %s" % p95)

    # 8. 阶梯品种数递增
    counts = [s["count"] for s in STAIRS]
    if not all(counts[i] <= counts[i + 1] for i in range(len(counts) - 1)):
        failures.append("品种数应递增: %s" % counts)
    if counts[-1] != TOTAL_VARIETIES:
        failures.append("G5 应为全量 %d 品种" % TOTAL_VARIETIES)

    # 9. 回滚触发条件完整性
    codes = {t["code"] for t in ROLLBACK_TRIGGERS}
    expected = {"F1", "F2", "F3", "F4", "F5"}
    if codes != expected:
        failures.append("回滚条件不完整: %s" % sorted(codes))

    # 10. DEP 未就绪: 全阶梯无法推进
    sim = GrayStairSimulator(dep_ready=False)
    advanced = []
    for sc in ["G0", "G1", "G2", "G3", "G4", "G5"]:
        r = sim.simulate_stage(sc, dict(HEALTHY_METRICS))
        if r["decision"].startswith("ADVANCE"):
            advanced.append(sc)
    if advanced != ["G0"]:
        failures.append("DEP 未就绪时仅 G0 可推进, 实际: %s" % advanced)

    print("gray_stair_sim 自检")
    print("-" * 56)
    if failures:
        for f in failures:
            print("  FAIL %s" % f)
        print("  结论: SELF-TEST FAILED")
        return 1
    print("  1. DEP 未就绪: G1~G5 全部不准入 (DEP_001 阻断)")
    print("  2. DEP 就绪: G1~G5 健康指标全部准入 ADVANCE")
    print("  3. 5 类故障注入全部触发回滚")
    print("  4. F1 自动回滚, F3/F4/F5 需人工确认")
    print("  5. 阈值边界判定正确 (HIGH 超限不准入)")
    print("  6. 非零率阈值逐级收紧: %s" % strictness)
    print("  7. p95 阈值逐级收紧: %s" % p95)
    print("  8. 品种数递增: %s" % counts)
    print("  9. 回滚条件 F1~F5 完整")
    print("  10. DEP 未就绪时仅 G0 可推进")
    print("  全部 10 项自检通过")
    print("  结论: SELF-TEST PASSED")
    return 0


# ---------------------------------------------------------------------------
# 全阶梯仿真
# ---------------------------------------------------------------------------
def run_full_stair(dep_ready=True, inject_faults=None, stage_to_inject=None):
    """全阶梯仿真。

    inject_faults: {stage_code: [fault_code, ...]}
    stage_to_inject: 指定在第几阶段注入故障
    """
    sim = GrayStairSimulator(dep_ready=dep_ready)
    results = []
    for stage in STAIRS:
        sc = stage["stage"]
        faults = inject_faults.get(sc, []) if inject_faults else []
        r = sim.simulate_stage(sc, dict(HEALTHY_METRICS),
                               inject_faults=faults or None)
        results.append(r)
        if r["decision"].startswith("ROLLBACK") or sim.rolled_back:
            break
    return sim.summary()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="V86-RC2 E2E 6 级灰度阶梯 dryrun 仿真器")
    ap.add_argument("--self-test", action="store_true", help="10 项自检")
    ap.add_argument("--run", action="store_true", help="全阶梯仿真")
    ap.add_argument("--fault-injection", action="store_true",
                    help="故障注入仿真 (5 类故障逐阶段注入)")
    ap.add_argument("--dep-ready", action="store_true",
                    help="模拟 DEP-001 已就绪 (默认未就绪)")
    ap.add_argument("--md", help="Markdown 报告路径")
    ap.add_argument("--json", dest="json_out", help="JSON 输出")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.run:
        print("=" * 66)
        print("  V86-RC2 E2E 6 级灰度阶梯 dryrun 仿真")
        print("  DEP-001 状态: %s  |  DEP 就绪: %s"
              % (DEP_001_STATUS, args.dep_ready))
        print("=" * 66)
        res = run_full_stair(dep_ready=args.dep_ready)
        for r in res["history"]:
            mark = "ADVANCE" if r["decision"].startswith("ADVANCE") else \
                   ("ROLLBACK" if r["decision"].startswith("ROLLBACK")
                    else "HOLD")
            print("\n[%s] %s (%.0f%%, %d 品种)"
                  % (r["stage"], r["name"], r["ratio"] * 100, r["count"]))
            print("  准入: %s" % ("通过" if r["admission_passed"] else "未通过"))
            if r["admission_failed"]:
                for f in r["admission_failed"]:
                    print("    - %s: 实际=%s 阈值=%s"
                          % (f["name"], f["actual"], f["threshold"]))
            if r["rollback_triggers"]:
                print("  故障: %s -> %s"
                      % (",".join(r["rollback_triggers"]), r["decision"]))
                print("    自动回滚=%s 需人工确认=%s 范围=%s"
                      % (r["auto_rollback"], r["manual_confirm_needed"],
                         r["rollback_scope"]))
            elif r["decision"].startswith("ADVANCE"):
                print("  决策: %s (观测 %d 小时)"
                      % (r["decision"], r.get("observe_hours", 0)))
            else:
                print("  决策: %s" % r["decision"])
        print("\n" + "-" * 66)
        print("  最终: %s 阶段 %s, 回滚=%s"
              % (res["current_stage"],
                 "完成" if not res["rolled_back"] else "回滚",
                 res["rolled_back"]))

        if args.md:
            with open(args.md, "w", encoding="utf-8") as f:
                f.write("# 灰度阶梯仿真\n\n```json\n%s\n```\n"
                        % json.dumps(res, ensure_ascii=False, indent=2))
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
        return 0

    if args.fault_injection:
        print("=" * 66)
        print("  故障注入仿真: 5 类故障逐阶段验证")
        print("=" * 66)
        all_ok = True
        for code, fm in FAULT_MAP.items():
            sim = GrayStairSimulator(dep_ready=True)
            r = sim.simulate_stage("G3", dict(HEALTHY_METRICS),
                                   inject_faults=[code])
            expected = code.split("_")[0]
            ok = expected in r["rollback_triggers"]
            all_ok = all_ok and ok
            trig = next(t for t in ROLLBACK_TRIGGERS
                        if t["code"] == expected)
            print("\n[%s] 注入 %s" % (expected, fm))
            print("  触发: %s  | 严重度: %s"
                  % (",".join(r["rollback_triggers"]), trig["severity"]))
            print("  自动回滚: %s | 人工确认: %s"
                  % (r["auto_rollback"], r["manual_confirm_needed"]))
            print("  处置时限: %d 秒 | 范围: %s"
                  % (trig["limit_sec"], trig["scope"]))
            print("  FLAG: %s" % trig["flag"])
            print("  判定: %s" % ("OK" if ok else "FAIL"))
        print("\n" + "-" * 66)
        print("  结论: %s" % ("全部 5 类故障正确触发回滚" if all_ok else "FAIL"))
        return 0 if all_ok else 1

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
