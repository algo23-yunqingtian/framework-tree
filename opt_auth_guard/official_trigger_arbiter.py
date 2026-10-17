#!/usr/bin/env python3
"""
official_trigger_arbiter.py — HERMEShf 双钥匙触发器仲裁器
================================================================
⚠️ 本脚本**仅检查文件存在性**，不主动拉数据、不自动执行merge、不自动启动因子任务。
   两把钥匙同时存在时才输出 AUTHORIZED 判定。

KEY A: WIND_DATA_LINK_ONLINE.flag (外部事实钥匙，由DSHB或外部系统放置)
KEY B: HERMES_TRIGGER_AUTHORIZED.flag (HERMEShf仲裁签名钥匙，仅当A存在+5项预检通过后才生成)
================================================================
"""
import os, json, sys, hashlib, datetime

WIND_FLAG = "WIND_DATA_LINK_ONLINE.flag"
HERMES_FLAG = "HERMES_TRIGGER_AUTHORIZED.flag"
AUTH_GUARD_DIR = os.path.dirname(os.path.abspath(__file__))

def check_key_a(path):
    a_path = os.path.join(path, WIND_FLAG)
    if not os.path.exists(a_path):
        return {"present": False, "path": a_path, "md5": None, "size": 0, "mtime": None}
    with open(a_path, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest().upper()
    return {"present": True, "path": a_path, "md5": md5, "size": os.path.getsize(a_path),
            "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(a_path)).isoformat()}

def check_key_b(path):
    b_path = os.path.join(path, HERMES_FLAG)
    if not os.path.exists(b_path):
        return {"present": False, "path": b_path, "md5": None, "size": 0, "mtime": None}
    with open(b_path, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest().upper()
    return {"present": True, "path": b_path, "md5": md5, "size": os.path.getsize(b_path),
            "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(b_path)).isoformat()}

def _check_baseline_switch_free(base):
    """#2 BASELINE-SWITCH-FREE: 读取 phase03_summary_asset_re_seal.md，校验包含无静默切换确认"""
    seal_path = os.path.join(base,
        "analysis/e2e_output/v88/phase03/p1/hermes/phase03_summary/phase03_summary_asset_re_seal.md")
    if not os.path.exists(seal_path):
        return False, f"seal file missing: {seal_path}"
    try:
        with open(seal_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # 查找关键确认语（防止只读文档存在但内容不含确认）
        if "无静默切换" in content and "✅ NO" in content:
            return True, "phase03_summary_asset_re_seal.md confirms no silent baseline switch"
        return False, "seal file exists but missing confirmation keywords"
    except Exception as e:
        return False, f"read error: {e}"

def _check_phase03_blockers_zero(base):
    """#3 PHASE03-BLOCKERS-ZERO: 读取 global_gate_dashboard.md，校验全部阻断清零"""
    dash_path = os.path.join(base,
        "analysis/e2e_output/v88/phase03/p1/hermes/phase03_summary/global_gate_dashboard.md")
    if not os.path.exists(dash_path):
        return False, f"dashboard file missing: {dash_path}"
    try:
        with open(dash_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if "全部阻断清零" in content and "🔴 FAIL" in content and "**0**" in content:
            return True, "global_gate_dashboard.md confirms Phase03 blockers=0"
        return False, "dashboard exists but missing zero-blocker confirmation"
    except Exception as e:
        return False, f"read error: {e}"

def _check_dshe_auto_commit_off(base):
    """#5 DSHE-AUTO-COMMIT-OFF: 读取 blocker_monitor_hook_snippet.py 源码，校验 AUTO_COMMIT_MODE = False"""
    hook_path = os.path.join(base, "opt_hooks/blocker_monitor_hook_snippet.py")
    if not os.path.exists(hook_path):
        return False, f"hook file missing: {hook_path}"
    try:
        with open(hook_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # 查找赋值行：AUTO_COMMIT_MODE = False（允许 # 注释）
        import re
        m = re.search(r'^AUTO_COMMIT_MODE\s*=\s*False\b', content, re.MULTILINE)
        if m:
            return True, "blocker_monitor_hook_snippet.py: AUTO_COMMIT_MODE=False (source verified)"
        return False, "hook file exists but AUTO_COMMIT_MODE != False"
    except Exception as e:
        return False, f"read error: {e}"

def run_5_point_safety_precheck():
    checks = []
    # FIX(V88-P6): AUTH_GUARD_DIR=/repo/opt_auth_guard，剥一层即仓库根；
    # 原 dirname 两层误指到 /home/ubuntu，导致 5 项预检路径全部失效。
    base = os.path.dirname(AUTH_GUARD_DIR)
    # 1. P0-13 closed
    p013 = os.path.join(base, "analysis/e2e_output/v88/phase03/p2/dshb/p013_watch_prep/final_archive/noise_168h_final_snapshot.json")
    checks.append({"id": "P0-13-CLOSED", "passed": os.path.exists(p013), "detail": os.path.exists(p013)})
    # 2. No silent baseline switch — FIX(V88-P7/R-V88-P6-001): 静态True→真实文件校验
    ok2, detail2 = _check_baseline_switch_free(base)
    checks.append({"id": "BASELINE-SWITCH-FREE", "passed": ok2, "detail": detail2})
    # 3. Phase03 blockers = 0 — FIX(V88-P7/R-V88-P6-001): 静态True→真实文件校验
    ok3, detail3 = _check_phase03_blockers_zero(base)
    checks.append({"id": "PHASE03-BLOCKERS-ZERO", "passed": ok3, "detail": detail3})
    # 4. DSHB merge not yet executed
    merge_marker = os.path.join(base, "v88-long-stable-baseline.json")
    checks.append({"id": "NO-PREMATUROUS-MERGE", "passed": not os.path.exists(merge_marker), "detail": "no v88-long-stable-baseline.json"})
    # 5. DSHE AUTO_COMMIT_MODE=false — FIX(V88-P7/R-V88-P6-001): 静态True→真实源码校验
    ok5, detail5 = _check_dshe_auto_commit_off(base)
    checks.append({"id": "DSHE-AUTO-COMMIT-OFF", "passed": ok5, "detail": detail5})
    return checks

def main():
    repo_path = os.path.dirname(AUTH_GUARD_DIR)
    print(f"=== HERMEShf Trigger Arbiter ===")
    print(f"Check time: {datetime.datetime.now().isoformat()}")
    print(f"Repo path: {repo_path}")
    print()
    a = check_key_a(repo_path)
    b = check_key_b(repo_path)
    print(f"Key A ({WIND_FLAG}): {'✅ PRESENT' if a['present'] else '❌ ABSENT'}")
    if a['present']:
        print(f"  MD5: {a['md5']}, Size: {a['size']}B, Modified: {a['mtime']}")
    print(f"Key B ({HERMES_FLAG}): {'✅ PRESENT' if b['present'] else '❌ ABSENT'}")
    if b['present']:
        print(f"  MD5: {b['md5']}, Size: {b['size']}B, Modified: {b['mtime']}")
    print()
    both = a['present'] and b['present']
    print(f"=== TWO-KEY VERDICT ===")
    print(f"AUTHORIZED: {'✅ YES' if both else '❌ NO'}")
    if not both:
        missing = []
        if not a['present']: missing.append("Key A")
        if not b['present']: missing.append("Key B")
        print(f"Missing: {', '.join(missing)}")
        print("Action: Log only, REFUSE to start factor tasks")
    elif both:
        print("Action: Both keys present — factor tasks MAY proceed")
        print("Note: This does NOT auto-start anything; DSHB/DSHE must still check both keys")
    print()
    print("=== 5-Point Safety Precheck ===")
    if both or a['present']:
        prechecks = run_5_point_safety_precheck()
        for c in prechecks:
            print(f"  {'✅' if c['passed'] else '❌'} {c['id']}: {c['detail']}")
        all_pass = all(c['passed'] for c in prechecks)
        print(f"\nPrecheck Result: {'✅ ALL PASS' if all_pass else '❌ SOME FAILED'}")
        if not all_pass:
            print("WARNING: Key B should NOT be generated if prechecks fail")
    else:
        print("  Skipped (no keys present)")
    print()
    print("=== ARBITER STATE ===")
    print(f"ARBITER_STATE=OBSERVING")
    print(f"KEY_A={'PRESENT' if a['present'] else 'ABSENT'}")
    print(f"KEY_B={'PRESENT' if b['present'] else 'ABSENT'}")
    print(f"AUTHORIZED={'YES' if both else 'NO'}")
    print(f"TIMESTAMP={datetime.datetime.now().isoformat()}")
    print(f"NEXT_ACTION={'LOG_ONLY_REFUSE_START' if not both else 'AUTHORIZED_PROCEED'}")
    print()
    print("NOTE: HERMES never auto-generates Key B. HERMES runs this script")
    print("to verify Key A exists + 5-point precheck passes, then HERMES")
    print("manually decides to create HERMES_TRIGGER_AUTHORIZED.flag.")
    print("DSHB/DSHE must ALWAYS check both keys before starting factor tasks.")

if __name__ == "__main__":
    main()
