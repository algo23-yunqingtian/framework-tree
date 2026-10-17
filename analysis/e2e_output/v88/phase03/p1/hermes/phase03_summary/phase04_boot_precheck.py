#!/usr/bin/env python3
"""
phase04_boot_precheck.py — Phase04 Bootstrap 预检查脚本
================================================================
⚠️ 仅检查、不执行:
   - 不执行 merge
   - 不打任何激活 flag
   - 不修改任何文件
   - 仅输出报告

Phase04 正式点火仍需 HERMES 签发独立的 Phase04-GO 工单。
================================================================
"""
import os, json, sys, hashlib, datetime, yaml

# FIX(V88-P6): 脚本嵌套深，dirname 层数容易数错；向上查找最近 .git 标识仓库根。
def _find_repo_root():
    p = os.path.dirname(os.path.abspath(__file__))
    for _ in range(15):
        if os.path.isdir(os.path.join(p, ".git")):
            return p
        up = os.path.dirname(p)
        if up == p:
            break
        p = up
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = _find_repo_root()

def check(path, label):
    exists = os.path.exists(path)
    return {"label": label, "path": path, "exists": exists}

def sha256(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return "ERROR"

def main():
    print("=" * 60)
    print("Phase04 Bootstrap Precheck — READ-ONLY")
    print(f"Time: {datetime.datetime.now().isoformat()}")
    print(f"Repo: {REPO}")
    print("=" * 60)

    checks = []

    # --- Phase03 gate conditions ---
    checks.append(check(
        os.path.join(REPO, "analysis/e2e_output/v88/phase03/p2/dshb/p013_watch_prep/final_archive/noise_168h_final_snapshot.json"),
        "P0-13 168h snapshot"))

    checks.append(check(
        os.path.join(REPO, "analysis/e2e_output/v88/phase03/p1/dshe/p012_final_triplefix/frozen_p012_gate_package/v88_p012_full_link_cpu_compare.json"),
        "P0-12 frozen JSON"))

    checks.append(check(
        os.path.join(REPO, "analysis/e2e_output/v88/phase03/p1/hermes/phase03_summary/global_gate_dashboard.md"),
        "Global gate dashboard"))

    # --- Baseline merge readiness ---
    checks.append(check(
        os.path.join(REPO, "analysis/e2e_output/v88/phase03/p2/dshb/p013_watch_prep/final_archive/merge_readiness_check.md"),
        "Merge readiness check"))

    # --- DSHB-DSHE variety bind ---
    checks.append(check(
        os.path.join(REPO, "framework-tree/node-mapping/dshb_p013_variety_bind.yaml"),
        "DSHB variety bind"))

    checks.append(check(
        os.path.join(REPO, "framework-tree/node-mapping/dshe_gate_variety_bind.yaml"),
        "DSHE variety bind"))

    # --- Metric JSONs ---
    checks.append(check(
        os.path.join(REPO, "framework-tree/metrics-db/weekly/dshb_v88_p013.json"),
        "DSHB metric JSON"))

    checks.append(check(
        os.path.join(REPO, "framework-tree/metrics-db/weekly/dshe_v88_gate_harden.json"),
        "DSHE metric JSON"))

    # --- Auth guard ---
    checks.append(check(
        os.path.join(REPO, "opt_auth_guard/official_trigger_arbiter.py"),
        "Trigger arbiter"))

    # --- Check baseline not prematurely merged ---
    merge_marker = os.path.join(REPO, "v88-long-stable-baseline.json")
    checks.append({"label": "NO premature merge", "path": merge_marker,
                   "exists": not os.path.exists(merge_marker)})

    # --- Check dual-key not triggered ---
    wind = os.path.join(REPO, "WIND_DATA_LINK_ONLINE.flag")
    hermes = os.path.join(REPO, "HERMES_TRIGGER_AUTHORIZED.flag")
    checks.append({"label": "Key A not present (safe)", "path": wind,
                   "exists": not os.path.exists(wind)})
    checks.append({"label": "Key B not present (safe)", "path": hermes,
                   "exists": not os.path.exists(hermes)})

    # --- Check psutil locked ---
    psutil_check = check(
        os.path.join(REPO, "analysis/e2e_output/v88/phase03/p1/dshe/phase03_p3_gate_triple_lock/psutil_package_locked_confirmation.md"),
        "psutil lock confirmation")
    checks.append(psutil_check)

    # --- Print results ---
    print(f"\n{'Check':<45} {'Result':<12}")
    print("-" * 57)
    pass_count = 0
    fail_count = 0
    for c in checks:
        result = "✅ PASS" if c["exists"] else "❌ FAIL"
        status = "pass" if c["exists"] else "fail"
        if status == "pass":
            pass_count += 1
        else:
            fail_count += 1
        label = c["label"][:43]
        print(f"  {label:<43} {result}")

    print("-" * 57)
    print(f"Total: {pass_count}/{len(checks)} PASS, {fail_count} FAIL")
    print()

    # --- SHA256 fingerprint of key files ---
    print("=== Key File Fingerprints ===")
    for c in checks:
        if c["exists"] and os.path.exists(c["path"]):
            h = sha256(c["path"])[:16]
            print(f"  {h}... {c['label']}")
    print()

    # --- Verdict ---
    print("=== VERDICT ===")
    if fail_count == 0:
        print("✅ ALL PRECHECKS PASS")
        print("Phase04 bootstrap is ready for HERMES evaluation")
        print("NOTE: Phase04 activation still requires HERMES Phase04-GO order")
    else:
        print(f"❌ {fail_count} PRECHECK(S) FAILED")
        print("Phase04 bootstrap is NOT ready")
    print()
    print("NOTE: This script ONLY checks. It does NOT:")
    print("  - Execute merge")
    print("  - Create activation flags")
    print("  - Modify any files")
    print("  - Start factor tasks")
    print("Phase04 official ignition requires a separate HERMES Phase04-GO order.")

if __name__ == "__main__":
    main()
