#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V86-RC2 灰度门禁自动判定脚本 (gray_gate_decider.py)

工单: 工单-HERMES / T3.4 灰度门禁自动判定逻辑落地
分支: feature/v85-chart-template @ 1d5990b
编制方: HERMES (L3 审计方)
日期: 2026-10-15

功能:
  读取Gate状态、DEP健康状态、审计性能指标、告警严重度，
  自动判定G0~G5准入/HOLD/回滚，对齐F1~F5回滚矩阵。

用法:
  python3 gray_gate_decider.py --self-test        # 自检
  python3 gray_gate_decider.py --decide INPUT.json  # 单次判定
  python3 gray_gate_decider.py --md PATH            # 生成报告

约束: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
"""

import argparse
import json
import os
import sys
import time

# ============================================================
# 灰度阶梯定义 (对齐 gray_stair_sim.py)
# ============================================================

GRAY_STAGES = {
    "G0": {"name": "影子测试", "traffic": "0%", "varieties": 0, "observe_hours": 24,
           "thresholds": {"non_zero_rate": 0.95, "p95_ms": 50, "critical": 0, "dep_flap": 2}},
    "G1": {"name": "单品种", "traffic": "1%", "varieties": 1, "observe_hours": 24,
           "thresholds": {"non_zero_rate": 0.95, "p95_ms": 30, "critical": 0, "dep_flap": 2}},
    "G2": {"name": "小范围", "traffic": "5%", "varieties": 7, "observe_hours": 24,
           "thresholds": {"non_zero_rate": 0.98, "p95_ms": 20, "critical": 0, "dep_flap": 2}},
    "G3": {"name": "中范围", "traffic": "20%", "varieties": 28, "observe_hours": 48,
           "thresholds": {"non_zero_rate": 0.99, "p95_ms": 15, "critical": 0, "dep_flap": 2}},
    "G4": {"name": "大范围", "traffic": "50%", "varieties": 42, "observe_hours": 48,
           "thresholds": {"non_zero_rate": 0.995, "p95_ms": 15, "critical": 0, "dep_flap": 2}},
    "G5": {"name": "全量", "traffic": "100%", "varieties": 56, "observe_hours": 168,
           "thresholds": {"non_zero_rate": 0.995, "p95_ms": 15, "critical": 0, "dep_flap": 2}},
}

STAGE_ORDER = ["G0", "G1", "G2", "G3", "G4", "G5"]

# ============================================================
# F1~F5 回滚矩阵 (对齐 gray_stair_sim.py)
# ============================================================

ROLLBACK_MATRIX = {
    "F1": {"name": "链路级", "severity": "FATAL", "auto_rollback": True, "need_confirm": False,
           "timeout": "0秒（立即）", "scope": "全部品种",
           "flags": ["GATE_REVIEW_PAUSED=TRUE", "JOB_READY=FALSE"]},
    "F2": {"name": "审计级", "severity": "HIGH", "auto_rollback": True, "need_confirm": True,
           "timeout": "30分钟", "scope": "当前阶段", "flags": ["暂停放量"]},
    "F3": {"name": "Gate级", "severity": "HIGH", "auto_rollback": False, "need_confirm": True,
           "timeout": "8小时", "scope": "全部", "flags": ["登记部分恢复"]},
    "F4": {"name": "性能级", "severity": "MEDIUM", "auto_rollback": False, "need_confirm": True,
           "timeout": "2小时", "scope": "当前阶段", "flags": ["暂停放量"]},
    "F5": {"name": "稳定性级", "severity": "MEDIUM", "auto_rollback": False, "need_confirm": True,
           "timeout": "1小时", "scope": "当前阶段", "flags": ["评估服务稳定性"]},
}


def check_faults(state):
    """检查5类故障触发条件，返回触发的故障列表。"""
    faults = []

    # F1 链路级: HTTP 500连续5次 或 对照组失败
    if state.get("http_500_count", 0) >= 5 or state.get("control_group_failed", False):
        faults.append("F1")

    # F2 审计级: CRITICAL告警 > 0
    if state.get("critical_alerts", 0) > 0:
        faults.append("F2")

    # F3 Gate级: G-06未通过
    if not state.get("gate_g06_pass", True):
        faults.append("F3")

    # F4 性能级: 吞吐降>50% 或 p95>200ms
    throughput_drop = state.get("throughput_drop_pct", 0)
    p95_ms = state.get("p95_ms", 0)
    if throughput_drop > 50 or p95_ms > 200:
        faults.append("F4")

    # F5 稳定性级: DEP抖动>=3次 或 断连>5次
    dep_flap = state.get("dep_flap_count", 0)
    disconnects = state.get("disconnect_count", 0)
    if dep_flap >= 3 or disconnects > 5:
        faults.append("F5")

    return faults


def check_stage_admission(state, stage_id):
    """检查指定阶段的准入条件。返回(通过, 缺口项列表)。"""
    stage = GRAY_STAGES[stage_id]
    thresholds = stage["thresholds"]
    gaps = []

    # DEP-001状态 (G0不需要DEP就绪，G1+需要)
    if stage_id != "G0":
        dep_status = state.get("dep_001_status", "BLOCKED")
        if dep_status != "RECOVERED":
            gaps.append(f"DEP-001未就绪: {dep_status} (需RECOVERED)")

    # 数据非零率
    non_zero_rate = state.get("non_zero_rate", 0)
    if non_zero_rate < thresholds["non_zero_rate"]:
        gaps.append(f"非零率{non_zero_rate:.1%} < {thresholds['non_zero_rate']:.1%}")

    # p95延迟
    p95_ms = state.get("p95_ms", 0)
    if p95_ms > thresholds["p95_ms"]:
        gaps.append(f"p95={p95_ms}ms > {thresholds['p95_ms']}ms")

    # CRITICAL告警
    critical = state.get("critical_alerts", 0)
    if critical > thresholds["critical"]:
        gaps.append(f"CRITICAL={critical} > {thresholds['critical']}")

    # DEP抖动
    dep_flap = state.get("dep_flap_count", 0)
    if dep_flap > thresholds["dep_flap"]:
        gaps.append(f"DEP抖动={dep_flap} > {thresholds['dep_flap']}")

    return len(gaps) == 0, gaps


def decide(state):
    """主判定函数。返回判定结果dict。"""
    current_stage = state.get("current_stage", "G0")
    observe_hours_elapsed = state.get("observe_hours_elapsed", 0)

    result = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "current_stage": current_stage,
        "dep_001_status": state.get("dep_001_status", "BLOCKED"),
    }

    # 1. 先检查故障
    faults = check_faults(state)
    result["faults_detected"] = faults

    if faults:
        # 取最严重的故障
        severity_order = {"F1": 0, "F2": 1, "F3": 2, "F4": 3, "F5": 4}
        worst_fault = min(faults, key=lambda f: severity_order[f])
        fault_info = ROLLBACK_MATRIX[worst_fault]

        result["decision"] = "ROLLBACK"
        result["decision_reason"] = f"触发{worst_fault}({fault_info['name']})"
        result["auto_rollback"] = fault_info["auto_rollback"]
        result["need_confirm"] = fault_info["need_confirm"]
        result["rollback_timeout"] = fault_info["timeout"]
        result["rollback_scope"] = fault_info["scope"]
        result["flags_to_set"] = fault_info["flags"]
        result["all_faults"] = [{"id": f, **ROLLBACK_MATRIX[f]} for f in faults]
        return result

    # 2. 检查当前阶段准入
    admitted, gaps = check_stage_admission(state, current_stage)
    if not admitted:
        result["decision"] = "HOLD"
        result["decision_reason"] = f"准入未通过: {', '.join(gaps)}"
        result["gaps"] = gaps
        return result

    # 3. 检查观测期是否完成
    stage = GRAY_STAGES[current_stage]
    if observe_hours_elapsed < stage["observe_hours"]:
        result["decision"] = "OBSERVE"
        remaining = stage["observe_hours"] - observe_hours_elapsed
        result["decision_reason"] = f"观测期未满: {observe_hours_elapsed}/{stage['observe_hours']}h, 剩余{remaining}h"
        result["remaining_hours"] = remaining
        return result

    # 4. 检查是否有下一阶段
    idx = STAGE_ORDER.index(current_stage)
    if idx >= len(STAGE_ORDER) - 1:
        # 已是G5，观测完成
        result["decision"] = "COMPLETE"
        result["decision_reason"] = f"{current_stage}({stage['name']})观测完成，灰度全量完成"
        return result

    # 5. 检查下一阶段准入
    next_stage = STAGE_ORDER[idx + 1]
    next_admitted, next_gaps = check_stage_admission(state, next_stage)
    if next_admitted:
        result["decision"] = "ADVANCE"
        result["decision_reason"] = f"{current_stage}观测完成，准入{next_stage}({GRAY_STAGES[next_stage]['name']})"
        result["next_stage"] = next_stage
        result["next_traffic"] = GRAY_STAGES[next_stage]["traffic"]
        result["next_varieties"] = GRAY_STAGES[next_stage]["varieties"]
    else:
        result["decision"] = "HOLD"
        result["decision_reason"] = f"{current_stage}完成但{next_stage}准入未通过: {', '.join(next_gaps)}"
        result["next_stage"] = next_stage
        result["gaps"] = next_gaps

    return result


# ============================================================
# 自检
# ============================================================

def self_test():
    """12项自检用例。"""
    tests = [
        # T01: G0完成→G1需要DEP就绪。DEP BLOCKED时G0完成后HOLD（不能进G1）
        ("T01_DEP_BLOCKED_G0", {"current_stage": "G0", "dep_001_status": "BLOCKED",
          "non_zero_rate": 0.95, "p95_ms": 50, "critical_alerts": 0, "dep_flap_count": 0,
          "observe_hours_elapsed": 24}, "HOLD"),
        ("T02_DEP_BLOCKED_G1", {"current_stage": "G1", "dep_001_status": "BLOCKED",
          "non_zero_rate": 0.95, "p95_ms": 30, "critical_alerts": 0, "dep_flap_count": 0,
          "observe_hours_elapsed": 24}, "HOLD"),
        # T03: G1完成→G2需要非零率98%和p95<20ms
        ("T03_DEP_OK_G1", {"current_stage": "G1", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.98, "p95_ms": 20, "critical_alerts": 0, "dep_flap_count": 0,
          "observe_hours_elapsed": 24}, "ADVANCE"),
        ("T04_F1_ROLLBACK", {"current_stage": "G2", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.98, "p95_ms": 20, "critical_alerts": 0, "dep_flap_count": 0,
          "http_500_count": 5, "observe_hours_elapsed": 10}, "ROLLBACK"),
        ("T05_F2_ROLLBACK", {"current_stage": "G2", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.98, "p95_ms": 20, "critical_alerts": 2, "dep_flap_count": 0,
          "observe_hours_elapsed": 10}, "ROLLBACK"),
        ("T06_F3_ROLLBACK", {"current_stage": "G3", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.99, "p95_ms": 15, "critical_alerts": 0, "dep_flap_count": 0,
          "gate_g06_pass": False, "observe_hours_elapsed": 20}, "ROLLBACK"),
        ("T07_F4_ROLLBACK", {"current_stage": "G3", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.99, "p95_ms": 250, "critical_alerts": 0, "dep_flap_count": 0,
          "throughput_drop_pct": 60, "observe_hours_elapsed": 20}, "ROLLBACK"),
        ("T08_F5_ROLLBACK", {"current_stage": "G4", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.995, "p95_ms": 15, "critical_alerts": 0, "dep_flap_count": 4,
          "disconnect_count": 6, "observe_hours_elapsed": 30}, "ROLLBACK"),
        ("T09_OBSERVE", {"current_stage": "G1", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.95, "p95_ms": 30, "critical_alerts": 0, "dep_flap_count": 0,
          "observe_hours_elapsed": 10}, "OBSERVE"),
        ("T10_G5_COMPLETE", {"current_stage": "G5", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.995, "p95_ms": 15, "critical_alerts": 0, "dep_flap_count": 0,
          "observe_hours_elapsed": 168}, "COMPLETE"),
        ("T11_NON_ZERO_LOW", {"current_stage": "G2", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.90, "p95_ms": 20, "critical_alerts": 0, "dep_flap_count": 0,
          "observe_hours_elapsed": 24}, "HOLD"),
        ("T12_MULTI_FAULT", {"current_stage": "G3", "dep_001_status": "RECOVERED",
          "non_zero_rate": 0.99, "p95_ms": 250, "critical_alerts": 3, "dep_flap_count": 0,
          "throughput_drop_pct": 60, "observe_hours_elapsed": 20}, "ROLLBACK"),
    ]

    pass_count = 0
    print("=" * 60)
    print("gray_gate_decider.py 自检 (12项)")
    print("=" * 60)

    for name, state, expected in tests:
        result = decide(state)
        actual = result["decision"]
        ok = "PASS" if actual == expected else "FAIL"
        if ok == "PASS":
            pass_count += 1
        reason = result.get("decision_reason", "")[:60]
        print(f"  {ok}  {name:25s} expected={expected:10s} actual={actual:10s} ({reason})")

    print()
    print(f"  {pass_count}/{len(tests)} PASS")
    if pass_count == len(tests):
        print("  结论: SELF-TEST PASSED")
    else:
        print("  结论: SELF-TEST FAILED")
    return pass_count == len(tests)


def main():
    parser = argparse.ArgumentParser(description="V86-RC2 灰度门禁自动判定")
    parser.add_argument("--self-test", action="store_true", help="自检")
    parser.add_argument("--decide", metavar="INPUT", help="单次判定 (JSON输入)")
    parser.add_argument("--md", metavar="PATH", help="生成Markdown报告")
    args = parser.parse_args()

    if args.self_test:
        ok = self_test()
        sys.exit(0 if ok else 1)

    if args.decide:
        with open(args.decide) as f:
            state = json.load(f)
        result = decide(state)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.md:
        report = generate_report(args.md)
        print(f"报告已生成: {args.md}")


def generate_report(path):
    """生成Markdown判定规范报告。"""
    report = """# V86-RC2 灰度门禁自动判定规范

> 载体: `gray_gate_decider.py`
> 分支: `feature/v85-chart-template` @ `1d5990b`

## 1. 判定流程

```
状态输入 → 故障检查 → 准入检查 → 观测期检查 → 下一阶段检查
    │           │          │          │              │
    │           ▼          ▼          ▼              ▼
    │      ROLLBACK     HOLD      OBSERVE       ADVANCE/COMPLETE
```

## 2. 决策类型

| 决策 | 含义 | 动作 |
|------|------|------|
| ADVANCE | 当前阶段完成，准入下一阶段 | 流量提升 |
| HOLD | 准入未通过 | 维持当前流量 |
| OBSERVE | 观测期未满 | 等待观测完成 |
| ROLLBACK | 检测到故障 | 执行回滚 |
| COMPLETE | G5全量完成 | 灰度结束 |

## 3. F1~F5回滚矩阵

| 故障 | 触发条件 | 自动回滚 | 人工确认 | 超时 |
|------|----------|----------|----------|------|
| F1 | HTTP500×5+对照组失败 | ✅ | ❌ | 0秒 |
| F2 | CRITICAL>0 | ✅ | ✅ | 30分钟 |
| F3 | G-06未通过 | ❌ | ✅ | 8小时 |
| F4 | 吞吐降>50%/p95>200ms | ❌ | ✅ | 2小时 |
| F5 | DEP抖动≥3/断连>5 | ❌ | ✅ | 1小时 |
"""
    with open(path, "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()
