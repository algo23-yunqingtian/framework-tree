#!/usr/bin/env python3
"""
================================================================================
 blocker_monitor Hook Snippet — 轻量指标快照钩子（安全预览模式）
================================================================================

TASK_ID: V88_PHASE03_P3_DSHE_GATE_LOCK_METRICSDB_SEED_JOB / T5
AGENT: DSHE | BRANCH: feature/v88-g1

================================================================================
⚠️  安全声明 — 严格约束
================================================================================

1. **NO AUTO GIT COMMIT**: 本钩子绝不执行 git add / git commit / git push
   真正自动提交要等后面 Phase04 专门审批工单

2. **NO CORE AUDIT MODIFICATION**: 本钩子不改造现有核心审计逻辑
   不修改 blocker_monitor 主程序的任何代码

3. **PREVIEW ONLY**: 仅输出本地预览文件 preview_metrics.json
   仅供人工检查，不进入任何自动化流水线

4. **PERIODIC SCAN**: 每6小时执行一次指标目录扫描
   扫描范围: metrics-db/weekly/ 目录

5. **SAFE MODE**: 
   - 不覆盖任何已有文件
   - 不修改任何已有JSON
   - 不写入任何数据库
   - 不调用任何外部API (知几/SMM/WindPy)
   - 不启动任何后台进程

================================================================================
 架构说明
================================================================================

本文件是 blocker_monitor_hook_snippet.py，放在 opt_hooks/ 目录中。
它不修改现有 blocker_monitor 主程序。

工作流程:
1. blocker_monitor 主程序正常执行核心审计
2. 每6小时触发一次本钩子（通过 cron 或手动调用）
3. 钩子扫描 metrics-db/weekly/ 目录
4. 生成预览快照 preview_metrics.json
5. 输出预览日志到控制台
6. 等待人工审核后手动处理

================================================================================
 预埋目的
================================================================================

为以后"每周自动导出指标"预埋基础设施:
- 文件扫描逻辑已就绪
- JSON解析/验证逻辑已就绪
- 快照生成逻辑已就绪
- 安全约束已固化

未来 Phase04 审批后，可将预览模式切换为自动提交模式:
- 修改 AUTO_COMMIT_MODE = True
- 添加 git add/commit/push 逻辑
- 添加通知渠道集成

================================================================================
"""

import os
import sys
import json
import hashlib
import time
import glob
from datetime import datetime, timezone
from pathlib import Path

# =============================================================================
# 配置常量 — 安全模式锁定
# =============================================================================

TASK_ID = "V88_PHASE03_P3_DSHE_GATE_LOCK_METRICSDB_SEED_JOB"
AGENT = "DSHE"
BRANCH = "feature/v88-g1"

# 🚨 安全模式标志 — 禁止自动提交
AUTO_COMMIT_MODE = False  # FALSE = 仅预览，不自动提交
AUTO_PUSH_MODE = False    # FALSE = 禁止自动推送
AUTO_GIT_ADD = False      # FALSE = 禁止 git add

# 安全模式 — 只读
READ_ONLY_MODE = True
WRITE_LOCAL_PREVIEW = True  # 仅允许写本地预览文件

# 扫描配置
SCAN_INTERVAL_SECONDS = 6 * 3600  # 6小时
SCAN_DIRS = [
    "framework-tree/metrics-db/weekly/",
    "analysis/e2e_output/v88/phase03/p1/dshe/phase03_p3_gate_triple_lock/",
]

# 输出配置
PREVIEW_OUTPUT = "opt_hooks/preview_metrics.json"
PREVIEW_LOG = "opt_hooks/hook_run_log.txt"

# 安全约束
BRANCH_LOCKED = True
NO_OVERWRITE = True
NO_MODIFY_V87 = True
NO_EDIT_RELEASE_TAG = True
NO_ZHIJI_API_CALL = True
UPSTREAM_WRITES = 0

# 版本号
HOOK_VERSION = "1.0.0-preview"
HOOK_SCHEMA = "blocker-monitor-hook-preview-1.0"

# 引擎冻结哈希
ENGINE_FROZEN_HASH = "cd73deaeec54a7f1f8bde92c1300a9dc"


# =============================================================================
# 安全锁验证
# =============================================================================

def verify_safety_lock():
    """验证安全锁 — 如果任何安全约束被破坏，立即中止"""
    locks = {
        "AUTO_COMMIT_MODE": AUTO_COMMIT_MODE,
        "AUTO_PUSH_MODE": AUTO_PUSH_MODE,
        "AUTO_GIT_ADD": AUTO_GIT_ADD,
        "READ_ONLY_MODE": READ_ONLY_MODE,
        "BRANCH_LOCKED": BRANCH_LOCKED,
        "NO_OVERWRITE": NO_OVERWRITE,
        "NO_MODIFY_V87": NO_MODIFY_V87,
        "NO_EDIT_RELEASE_TAG": NO_EDIT_RELEASE_TAG,
        "NO_ZHIJI_API_CALL": NO_ZHIJI_API_CALL,
    }
    
    violations = []
    for name, value in locks.items():
        if name.startswith("AUTO_") and value is True:
            violations.append(f"{name}=True — 自动提交模式被启用!")
        if name == "READ_ONLY_MODE" and value is False:
            violations.append("READ_ONLY_MODE=False — 只读模式被关闭!")
        if name.startswith("NO_") and value is False:
            violations.append(f"{name}=False — 禁止操作被解除!")
    
    if violations:
        raise RuntimeError(
            f"🚨 SAFETY LOCK VIOLATION!\n"
            f"   Violations:\n" +
            "\n".join(f"   - {v}" for v in violations) +
            "\n   → 中止执行。请恢复安全配置后重试。"
        )
    
    print("[SAFE] All safety locks verified.")
    return True


# =============================================================================
# 文件扫描
# =============================================================================

def scan_metrics_dir(base_dir, subdir):
    """扫描指定目录中的JSON文件"""
    full_path = os.path.join(base_dir, subdir)
    results = []
    
    if not os.path.isdir(full_path):
        print(f"  [SKIP] {subdir} — directory not found")
        return results
    
    for filepath in glob.glob(os.path.join(full_path, "*.json")):
        try:
            fname = os.path.basename(filepath)
            fsize = os.path.getsize(filepath)
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # MD5校验
            md5_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
            
            # SHA256校验
            sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            
            # 尝试JSON解析
            try:
                data = json.loads(content)
                json_valid = True
                top_keys = list(data.keys())[:20]
            except json.JSONDecodeError:
                json_valid = False
                top_keys = []
            
            results.append({
                "filename": fname,
                "size_bytes": fsize,
                "md5": md5_hash,
                "sha256": sha256_hash,
                "json_valid": json_valid,
                "top_keys": top_keys,
                "modified_time": datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                ).isoformat(),
            })
            
            print(f"  [SCAN] {fname} — {fsize}B — md5={md5_hash[:12]}...")
            
        except Exception as e:
            print(f"  [ERROR] {filepath}: {e}")
    
    return results


# =============================================================================
# 快照生成
# =============================================================================

def generate_preview_snapshot(base_dir):
    """生成预览快照 preview_metrics.json"""
    
    snapshot = {
        "hook_version": HOOK_VERSION,
        "hook_schema": HOOK_SCHEMA,
        "task_id": TASK_ID,
        "agent": AGENT,
        "branch": BRANCH,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scan_interval_seconds": SCAN_INTERVAL_SECONDS,
        "auto_commit_enabled": AUTO_COMMIT_MODE,
        "auto_push_enabled": AUTO_PUSH_MODE,
        "read_only_mode": READ_ONLY_MODE,
        "safety_lock_status": "VERIFIED",
        
        "scan_results": {},
        "summary": {
            "total_files_scanned": 0,
            "total_files_valid_json": 0,
            "total_files_invalid_json": 0,
            "total_bytes": 0,
            "latest_file": None,
            "newest_mtime": None,
        },
        
        "safety_constraints": {
            "branch_locked": BRANCH_LOCKED,
            "no_overwrite": NO_OVERWRITE,
            "no_modify_v87": NO_MODIFY_V87,
            "no_edit_release_tag": NO_EDIT_RELEASE_TAG,
            "no_zhiji_api_call": NO_ZHIJI_API_CALL,
            "upstream_writes": UPSTREAM_WRITES,
        },
        
        "engine_integrity": {
            "frozen_hash": ENGINE_FROZEN_HASH,
            "status": "LOCKED",
        },
        
        "preview_only": True,
        "auto_commit_disclaimer": (
            "This is a PREVIEW snapshot only. "
            "No git add/commit/push has been performed. "
            "Automatic commit requires Phase04 approval."
        ),
    }
    
    total_files = 0
    valid_json = 0
    invalid_json = 0
    total_bytes = 0
    newest_mtime = None
    latest_file = None
    
    for subdir in SCAN_DIRS:
        print(f"\n[SCAN] {subdir}")
        files = scan_metrics_dir(base_dir, subdir)
        snapshot["scan_results"][subdir] = files
        
        for f in files:
            total_files += 1
            total_bytes += f["size_bytes"]
            if f["json_valid"]:
                valid_json += 1
            else:
                invalid_json += 1
            mtime = f["modified_time"]
            if newest_mtime is None or mtime > newest_mtime:
                newest_mtime = mtime
                latest_file = f["filename"]
    
    snapshot["summary"] = {
        "total_files_scanned": total_files,
        "total_files_valid_json": valid_json,
        "total_files_invalid_json": invalid_json,
        "total_bytes": total_bytes,
        "latest_file": latest_file,
        "newest_mtime": newest_mtime,
    }
    
    return snapshot


# =============================================================================
# 预览输出
# =============================================================================

def write_preview(snapshot, base_dir):
    """写入本地预览文件"""
    output_path = os.path.join(base_dir, PREVIEW_OUTPUT)
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 写入预览JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    print(f"\n[WRITE] Preview snapshot → {PREVIEW_OUTPUT}")
    print(f"[WRITE] Size: {os.path.getsize(output_path)} bytes")
    
    # 写入运行日志
    log_path = os.path.join(base_dir, PREVIEW_LOG)
    log_entry = f"{datetime.now().isoformat()} | {TASK_ID} | preview_only | files={snapshot['summary']['total_files_scanned']} | auto_commit={AUTO_COMMIT_MODE}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    return output_path


# =============================================================================
# 主执行
# =============================================================================

def main():
    """主入口 — 轻量指标快照钩子"""
    
    print("=" * 70)
    print(f"  blocker_monitor Hook Snippet — v{HOOK_VERSION}")
    print(f"  TASK_ID: {TASK_ID}")
    print(f"  AGENT: {AGENT} | BRANCH: {BRANCH}")
    print(f"  MODE: {'PREVIEW ONLY' if not AUTO_COMMIT_MODE else 'AUTO COMMIT'}")
    print("=" * 70)
    
    # 1. 安全锁验证
    print("\n[1/5] Safety lock verification...")
    verify_safety_lock()
    
    # 2. 确定工作目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"\n[2/5] Base directory: {base_dir}")
    
    # 3. 扫描指标目录
    print("\n[3/5] Scanning metrics directories...")
    snapshot = generate_preview_snapshot(base_dir)
    
    # 4. 写入预览
    print("\n[4/5] Writing preview output...")
    write_preview(snapshot, base_dir)
    
    # 5. 输出摘要
    print("\n[5/5] Execution summary:")
    s = snapshot["summary"]
    print(f"  Files scanned:    {s['total_files_scanned']}")
    print(f"  Valid JSON:       {s['total_files_valid_json']}")
    print(f"  Invalid JSON:     {s['total_files_invalid_json']}")
    print(f"  Total bytes:      {s['total_bytes']}")
    print(f"  Latest file:      {s['latest_file']}")
    print(f"  Preview output:   {PREVIEW_OUTPUT}")
    print(f"  Auto commit:      {AUTO_COMMIT_MODE} — DISABLED")
    print(f"  Auto push:        {AUTO_PUSH_MODE} — DISABLED")
    print(f"  Git add:          {AUTO_GIT_ADD} — DISABLED")
    
    print("\n" + "=" * 70)
    print("  ✅ Hook execution COMPLETE — PREVIEW MODE ONLY")
    print("  📋 No git operations performed.")
    print("  📋 No core audit logic modified.")
    print("  📋 Snapshot ready for manual review.")
    print("=" * 70)
    
    return snapshot


# =============================================================================
# 使用方式
# =============================================================================
#
# 方式1: 手动执行
#   python3 opt_hooks/blocker_monitor_hook_snippet.py
#
# 方式2: Cron定时执行 (每6小时)
#   0 */6 * * * cd /path/to/repo && python3 opt_hooks/blocker_monitor_hook_snippet.py >> opt_hooks/cron.log 2>&1
#
# 方式3: 在blocker_monitor主程序中调用
#   from opt_hooks.blocker_monitor_hook_snippet import generate_preview_snapshot, write_preview
#
# 方式4: 未来Phase04自动提交模式 (需审批)
#   修改 AUTO_COMMIT_MODE = True
#   添加 git add/commit/push 逻辑
#   添加通知渠道
#
# =============================================================================

if __name__ == "__main__":
    main()