#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V88 Phase03 P1 BLOCKER_RESOLVE — 阻断项持续巡检 watchdog

TASK_ID : V88_PHASE03_P1_HERMES_FOLLOWUP_BLOCKER_RESOLVE_JOB (T4/T5)
AGENT   : HERMEShf | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

职责（确定性逻辑，不调用 LLM，供 no_agent cron 使用）：
  T4  轮询 DSHB P09FIX 交付物 —— 映射清单 p0_9 自报块发生变化（mtime/MD5）时，
      自动重跑 P0-9-AUDIT 并输出结论。
  T5  监听 DSHE CPU 全链路优化交付物 —— 新增/更新结构化 JSON 时，
      自动触发 P0-12 门禁核验。

输出约定（watchdog 模式）：
  - stdout 为空 = 无状态变化（cron 静默，不打扰用户）
  - stdout 非空 = 交付物落地或门禁状态跃迁（通知）

约束合规：NO_ZHIJI_API_CALL（零知几 API 调用，全部离线文件探测）/ NO_OVERWRITE。

用法：
  python3 blocker_monitor.py            # 巡检并输出状态变化
  python3 blocker_monitor.py --verbose  # 输出完整状态（含未变化项）
  python3 blocker_monitor.py --reset    # 重置基线状态文件
"""
import hashlib
import json
import os
import sys
import time

# blocker_fix → hermes → p1 → phase03 → v88 → e2e_output → analysis → framework-tree（7 级 parent）
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", ".."))
P1_DIR = os.path.join(REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p1")
STATE_DIR = os.path.join(P1_DIR, "hermes", "blocker_fix")
STATE_FILE = os.path.join(STATE_DIR, "blocker_monitor_state.json")
LOG_FILE = os.path.join(STATE_DIR, "v88_phase03_p1_blocker_monitor.shurl")
GATE_CHECKER = os.path.join(
    REPO_ROOT, "analysis", "e2e_output", "v88", "phase03", "p0", "scripts", "p0_gate_checker.py")
GATE_OUT = os.path.join(STATE_DIR, "p0_gate_last_check.json")

VERBOSE = "--verbose" in sys.argv
RESET = "--reset" in sys.argv

# T4: DSHB P09FIX 交付物（P0-9-AUDIT 审计源）
P09_FIX_ARTIFACTS = [
    "p1/dshb/v88_phase03_p1_metric_indicator_code_mapping.json",
    "p1/dshb/p09_fix_metric_indicator_code_mapping.json",
    "p0/v88_phase03_p0_metric_indicator_code_mapping.json",
]
# T5: DSHE CPU 全链路优化交付物（P0-12 判定源，结构化 JSON 优先）
CPU_FIX_ARTIFACTS = [
    "p1/dshb/p0_10_cpu_optimization_compare.json",
    "p1/dshb/cpu_optimization_comparison.json",
    "p1/dshb/cpu_optimization_compare.json",
    "p1/dshb/p0_10_cpu_compare.json",
    "p1/dshb/cpu_peak_pct.json",
    "p1/dshe/p0_10_cpu_optimization_compare.json",
    "p1/dshe/cpu_optimization_comparison.json",
    "p1/dshe/cpu_optimization_compare.json",
    "p1/dshe/cpu_peak_pct.json",
    "p1/dshe/longrun_perf_results.json",
    "p1/dshe/cpu_baseline_p1_results.json",
]
# P0-13 噪声率观测（观测窗口满 7 天方可 PASS）
NOISE_ARTIFACTS = [
    "p1/dshb/noise_rate_data.json",
    "p1/dshb/alert_noise_rate_report.json",
    "p1/dshe/noise_rate_data.json",
]


def _abs(rel):
    return os.path.join(REPO_ROOT, rel)


def _fingerprint(rel):
    """文件指纹：mtime_ns + size + md5(前 64KB)。任一变化即视为交付物更新。"""
    p = _abs(rel)
    if not os.path.exists(p):
        return None
    st = os.stat(p)
    with open(p, "rb") as f:
        head = f.read(65536)
    return {
        "path": rel,
        "exists": True,
        "mtime_ns": st.st_mtime_ns,
        "size": st.st_size,
        "md5_head": hashlib.md5(head).hexdigest(),
    }


def _read_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _write_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _append_log(text):
    if not text:
        return
    os.makedirs(STATE_DIR, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 72 + "\n[%s] BLOCKER_MONITOR\n%s\n" % (ts, text))


def _run_gate_checker():
    """
    运行门禁脚本并返回关键门禁状态摘要。

    注意：p0_gate_checker.py 在 verdict 为 FAIL/BLOCKED 时按设计返回 exit 2
    （见脚本尾部 sys.exit(0 if verdict in (...) else 2)）。这是**门禁判定结果**，
    不是脚本异常 —— 真实阻断期本 watchdog 必须能读到该输出，否则无法检测
    FAIL → PASS 的跃迁。故用 check_output + 显式捕获 CalledProcessError。
    """
    import subprocess
    try:
        out = subprocess.check_output(
            ["python3", GATE_CHECKER, "--json"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL, timeout=600)
    except subprocess.CalledProcessError as e:
        if not e.output:
            return {"error": "gate_checker_failed: exit=%s（无输出）" % e.returncode}
        out = e.output  # exit 2 = 门禁判 FAIL，输出有效
    try:
        with open(GATE_OUT, "w", encoding="utf-8") as f:
            f.write(out.decode("utf-8"))
        d = json.loads(out.decode("utf-8"))
    except Exception as e:
        return {"error": "gate_checker_parse_failed: %s" % e}
    return d


def main():
    if RESET:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        print("[RESET] 基线状态已重置: %s" % STATE_FILE)
        return 0

    os.makedirs(STATE_DIR, exist_ok=True)
    state = _read_state()
    changes = []
    groups = {
        "T4_P09FIX": P09_FIX_ARTIFACTS,
        "T5_CPU_FIX": CPU_FIX_ARTIFACTS,
        "T13_NOISE": NOISE_ARTIFACTS,
    }

    new_state = {}
    for group, arts in groups.items():
        new_state[group] = {}
        for rel in arts:
            fp = _fingerprint(rel)
            prev = state.get(group, {}).get(rel)
            new_state[group][rel] = fp
            if fp and not prev:
                changes.append("[%s] 交付物新增: %s (%d 字节)" % (group, rel, fp["size"]))
            elif fp and prev and (fp["md5_head"] != prev["md5_head"]):
                changes.append("[%s] 交付物更新: %s (md5 %s→%s)" % (
                    group, rel, prev["md5_head"][:8], fp["md5_head"][:8]))

    gate_triggered = False
    # 任一关键交付物变化 → 触发门禁复算
    prev_keys = {}
    for group in groups:
        prev_keys.update(state.get(group, {}))
    changed_any = any(
        (prev_keys.get(k) is None) != (v is None) or
        (v and prev_keys.get(k) and v["md5_head"] != prev_keys[k]["md5_head"])
        for k, v in new_state.get("T4_P09FIX", {}).items()
    ) or any(
        (prev_keys.get(k) is None) != (v is None) or
        (v and prev_keys.get(k) and v["md5_head"] != prev_keys[k]["md5_head"])
        for k, v in new_state.get("T5_CPU_FIX", {}).items()
    )
    if VERBOSE or changed_any:
        gate_triggered = True

    if gate_triggered:
        d = _run_gate_checker()
        if d.get("error"):
            changes.append("[GATE] ❌ 门禁复算失败: %s" % d["error"])
        else:
            prev_status = state.get("gate_status") or {}
            for r in d.get("results", []):
                gid = r.get("gate_id")
                if gid in ("P0-9-AUDIT", "P0-12", "P0-13", "P0-14"):
                    status = r.get("status")
                    prev_s = prev_status.get(gid)
                    if VERBOSE or status != prev_s:
                        changes.append(
                            "[GATE] %-12s %s%s | %s" % (
                                gid, status,
                                (" ← %s" % prev_s) if prev_s and prev_s != status else "",
                                str(r.get("actual"))[:60]))
            new_status = {}
            for r in d.get("results", []):
                if r.get("gate_id") in ("P0-9-AUDIT", "P0-12", "P0-13", "P0-14"):
                    new_status[r["gate_id"]] = r.get("status")
            new_state["gate_status"] = new_status
            new_state["gate_verdict"] = d.get("verdict")
            new_state["gate_last_check"] = time.strftime("%Y-%m-%d %H:%M:%S")

    _write_state(new_state)

    if changes:
        body = "\n".join(changes)
        _append_log(body)
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
