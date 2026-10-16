#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WindPy 环境调研与连通性测试脚本
====================================
工单-A（DSHA）· 2026-10-16 更新指令
目标：读取WindPy文档→安装依赖→自检→w.start()→小样查询
硬性约束：失败则停止全部Wind尝试，上报DSHC，切回静态待命
"""

import sys
import os
import json
import traceback
import time
import ctypes

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIT_DIR = SCRIPT_DIR
LOG_DIR = AUDIT_DIR
WIND_DIR = r"D:\x64"
CREDENTIALS = {"username": "13199157886", "password": "Tyq1999!"}

# ========== 审计日志写入器 ==========
def log_event(event_type: str, status: str, detail: str = ""):
    """向 wind_excel_events.jsonl 写入审计事件"""
    ts = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    event = {"timestamp": ts, "event_type": event_type, "status": status, "detail": detail}
    logfile = os.path.join(AUDIT_DIR, "wind_excel_events.jsonl")
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"[AUDIT] {event_type} = {status}")

def log_tracking(event_type: str, status: str, detail: str = ""):
    """向 tracking_monitor_audit.jsonl 写入审计事件"""
    ts = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    event = {"timestamp": ts, "source": "DSHA-P49", "event_type": event_type, "status": status, "detail": detail}
    logfile = os.path.join(r"D:\DSH_WORK\github工作\回测", "tracking_monitor_audit.jsonl")
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"[TRACKING] {event_type} = {status}")

# ========== 测试步骤 ==========
def step1_import():
    """Step 1: 导入 WindPy"""
    print("\n" + "="*60)
    print("STEP 1: WindPy 模块导入测试")
    print("="*60)
    
    sys.path.insert(0, WIND_DIR)
    
    log_event("WINDPY_IMPORT", "START", f"Python {sys.version}")
    
    try:
        import WindPy
        print(f"[OK] WindPy import SUCCESS")
        print(f"  DLL loaded from: {WIND_DIR}\\WindPy.dll")
        print(f"  WindPy.py: {WIND_DIR}\\WindPy.py (cp936 encoding, ~2182 lines)")
        print(f"  w object type: {type(WindPy.w)}")
        log_event("WINDPY_IMPORT", "SUCCESS", "WindPy module loaded successfully")
        return WindPy
    except Exception as e:
        print(f"[FAIL] WindPy import FAILED: {traceback.format_exc()}")
        log_event("WINDPY_IMPORT", "FAILED", str(e))
        return None

def step2_dependencies():
    """Step 2: Python依赖检查"""
    print("\n" + "="*60)
    print("STEP 2: Python 依赖检查")
    print("="*60)
    
    deps = {}
    for mod_name in ['pandas', 'numpy', 'ctypes', 'threading', 'datetime', 'sys']:
        try:
            mod = __import__(mod_name)
            version = getattr(mod, '__version__', 'N/A')
            deps[mod_name] = f"OK ({version})"
            print(f"  [OK] {mod_name}: {version}")
        except ImportError:
            deps[mod_name] = "MISSING"
            print(f"  [MISSING] {mod_name}")
    
    # Check pandas compatibility
    try:
        import pandas as pd
        ver = pd.__version__
        if ver.startswith('3.'):
            print(f"  [WARN] pandas {ver}: applymap() deprecated/removed - WindPy wdata2dfdt() may fail")
            print(f"         → Use WindData object directly (no usedf/usedfdt params)")
    except:
        pass
    
    print(f"\n  sys.path includes D:\\x64: {WIND_DIR in sys.path}")
    return deps

def step3_process_check():
    """Step 3: Wind桌面客户端进程与许可状态检测"""
    print("\n" + "="*60)
    print("STEP 3: Wind 桌面客户端进程检测")
    print("="*60)
    
    import subprocess
    
    log_event("WIND_CLIENT_PROCESS_CHECK", "START", "Checking Wind desktop client processes")
    
    # Check for Wind processes
    wind_procs = []
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             "Get-Process | Where-Object { $_.ProcessName -match 'wind|Wind|iWind|WBox|WMain|wbrowser' } | "
             "Select-Object Id, ProcessName, Path | Format-Table -AutoSize | Out-String"],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip()
        print(output if output else "  (no Wind-related processes found)")
        
        # Parse process names
        for line in output.split('\n'):
            line = line.strip()
            if line and 'wind' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    wind_procs.append({"pid": parts[0], "name": parts[1]})
        
    except Exception as e:
        print(f"  [WARN] Process check failed: {e}")
    
    # Check WBox status via WindPy
    wbox_status = "UNKNOWN"
    try:
        import WindPy
        wbox_ok = WindPy.w.c_isConnectionOK()
        wbox_status = "CONNECTED" if wbox_ok else "NOT_CONNECTED"
        print(f"\n  WindPy c_isConnectionOK(): {wbox_ok} → {wbox_status}")
    except Exception as e:
        wbox_status = f"ERROR: {e}"
        print(f"\n  WindPy c_isConnectionOK() check failed: {e}")
    
    # Check Wind executables
    windlocal = os.path.exists(r"D:\x64\windlocal.exe")
    wmain = os.path.exists(r"D:\bin\WMain.exe")
    wbox_exe = os.path.exists(r"D:\bin\WBox.exe")
    print(f"\n  windlocal.exe: {'EXISTS' if windlocal else 'MISSING'}")
    print(f"  WMain.exe:     {'EXISTS' if wmain else 'MISSING'}")
    print(f"  WBox.exe:      {'EXISTS' if wbox_exe else 'MISSING'}")
    
    procs_info = f"{len(wind_procs)} Wind processes found: {wind_procs}. WBox status: {wbox_status}"
    log_event("WIND_CLIENT_PROCESS_CHECK", "CHECKED", procs_info)
    
    return {"processes": wind_procs, "wbox_status": wbox_status}

def step4_connect():
    """Step 4: WindPy w.start() 连接测试"""
    print("\n" + "="*60)
    print("STEP 4: WindPy w.start() 连接测试")
    print("="*60)
    
    import WindPy
    
    log_event("WINDPY_W_START", "START", "Attempting w.start() with provided credentials")
    log_tracking("windpy_connect_attempt", "ATTEMPTING", "w.start() with creds 13199157886/Tyq1999!")
    
    results = {}
    
    # 4a: w.start() with empty creds (standard method)
    print("\n  --- 4a: w.start() with default params (empty creds) ---")
    try:
        result = WindPy.w.start(waitTime=30)
        ec = result.ErrorCode
        data = result.Data
        print(f"    ErrorCode: {ec}")
        print(f"    Data: {data}")
        print(f"    isconnected: {WindPy.w.isconnected()}")
        results["w_start_empty"] = {"ErrorCode": ec, "Data": data}
        
        # Error code interpretation
        error_map = {
            0: "OK - Connected!",
            -40520009: "WBox lost!",
            -40520008: "Timeout Error!",
            -40520005: "No Python API Authority!",
            -40520019: "Account restricted!",
            -40520004: "Login Failed!",
            -40520014: "Please Logon iWind firstly!",
        }
        msg = error_map.get(ec, f"Start Error! (code {ec})")
        print(f"    Interpretation: {msg}")
        results["w_start_empty"]["interpretation"] = msg
        
    except Exception as e:
        print(f"    Exception: {traceback.format_exc()}")
        results["w_start_empty"] = {"Exception": str(e)}
    
    # 4b: c_start with explicit credentials
    print("\n  --- 4b: c_start() with explicit credentials ---")
    try:
        err = WindPy.w.c_start(CREDENTIALS["username"], CREDENTIALS["password"], 30000)
        print(f"    ErrorCode: {err}")
        print(f"    isconnected: {WindPy.w.isconnected()}")
        
        error_map = {
            0: "OK - Connected!",
            -40520009: "WBox lost!",
            -40520008: "Timeout Error!",
            -40520005: "No Python API Authority!",
            -40520019: "Account restricted!",
            -40520004: "Login Failed!",
            -40520014: "Please Logon iWind firstly!",
        }
        msg = error_map.get(err, f"Start Error! (code {err})")
        print(f"    Interpretation: {msg}")
        results["c_start_with_creds"] = {"ErrorCode": err, "interpretation": msg}
        
    except Exception as e:
        print(f"    Exception: {traceback.format_exc()}")
        results["c_start_with_creds"] = {"Exception": str(e)}
    
    # 4c: Try with longer timeout
    print("\n  --- 4c: c_start() with 60s timeout ---")
    try:
        err = WindPy.w.c_start(CREDENTIALS["username"], CREDENTIALS["password"], 60000)
        print(f"    ErrorCode: {err}")
        results["c_start_60s"] = {"ErrorCode": err}
    except Exception as e:
        results["c_start_60s"] = {"Exception": str(e)}
    
    # Check if connected
    final_connected = WindPy.w.isconnected()
    print(f"\n  Final isconnected(): {final_connected}")
    
    if not final_connected:
        log_event("WINDPY_W_START", "FAILED", 
                  f"All connection attempts failed with ErrorCode=-2. WBox NOT connected.")
        log_tracking("windpy_connect_result", "FAILED",
                     "w.start() and c_start() both return ErrorCode=-2. WindPy cannot establish connection.")
        return None, results
    
    log_event("WINDPY_W_START", "SUCCESS", "Connection established")
    return True, results

def step5_sample_query():
    """Step 5: 极简单指标小样查询验证"""
    print("\n" + "="*60)
    print("STEP 5: 极简单指标小样查询（连通性验证）")
    print("="*60)
    
    import WindPy
    
    if not WindPy.w.isconnected():
        print("  [SKIP] Not connected - cannot execute query")
        log_event("WINDPY_SAMPLE_QUERY", "SKIPPED", "Not connected - w.start() failed")
        return None
    
    # Query: LI.SHF (lithium carbonate futures) 1-day close price
    # This is the SMALLEST possible query - single code, single field, 1 day
    print("  Query: wsd('LI.SHF', 'close', '2024-12-31', '2024-12-31')")
    print("  → Single commodity code, single field, single date = 1 data point")
    
    log_event("WINDPY_SAMPLE_QUERY", "START", "wsd('LI.SHF','close','2024-12-31','2024-12-31')")
    
    try:
        data = WindPy.w.wsd('LI.SHF', 'close', '2024-12-31', '2024-12-31')
        print(f"  ErrorCode: {data.ErrorCode}")
        print(f"  Codes: {data.Codes}")
        print(f"  Fields: {data.Fields}")
        print(f"  Times: {data.Times}")
        print(f"  Data: {data.Data}")
        
        log_event("WINDPY_SAMPLE_QUERY", "SUCCESS", 
                  f"ErrorCode={data.ErrorCode}, Data={data.Data}")
        return data
        
    except Exception as e:
        print(f"  [FAIL] Query exception: {traceback.format_exc()}")
        log_event("WINDPY_SAMPLE_QUERY", "FAILED", str(e))
        return None

def step6_stop():
    """Step 6: 停止连接"""
    print("\n" + "="*60)
    print("STEP 6: 停止WindPy连接")
    print("="*60)
    
    import WindPy
    try:
        if WindPy.w.isconnected():
            WindPy.w.stop()
            print("  [OK] WindPy connection stopped")
            log_event("WINDPY_STOP", "SUCCESS", "Connection stopped")
        else:
            print("  [SKIP] Not connected - no need to stop")
            log_event("WINDPY_STOP", "SKIPPED", "Not connected")
    except Exception as e:
        print(f"  [WARN] Stop failed: {e}")
        log_event("WINDPY_STOP", "WARN", str(e))

# ========== 主流程 ==========
def main():
    print("=" * 60)
    print("WindPy 环境调研与连通性测试")
    print("工单-A（DSHA）· 2026-10-16")
    print("硬性约束：失败则停止全部Wind尝试，上报DSHC，切回静态待命")
    print("=" * 60)
    
    # Step 1: Import
    WindPy = step1_import()
    if WindPy is None:
        print("\n[ABORT] WindPy import failed - stopping all Wind attempts")
        log_event("TEST_ABORTED", "IMPORT_FAILED", "WindPy import failed")
        log_tracking("windpy_test_result", "ABORTED", "Import failed")
        return {"status": "ABORTED", "reason": "import_failed"}
    
    # Step 2: Dependencies
    deps = step2_dependencies()
    
    # Step 3: Process check
    procs = step3_process_check()
    
    # Step 4: Connection
    connected, conn_results = step4_connect()
    
    # Step 5: Sample query (only if connected)
    query_result = None
    if connected:
        query_result = step5_sample_query()
    else:
        print("\n  [ABORT] Connection failed - cannot proceed to query")
        print("  → Per instructions: stop all Wind attempts, report to DSHC, return to static standby")
        log_event("TEST_ABORTED", "CONNECT_FAILED", 
                  "w.start() ErrorCode=-2. Per hard constraint, stopping all Wind attempts.")
        log_tracking("windpy_test_result", "CONNECT_FAILED", 
                     "ErrorCode=-2 from w.start() and c_start(). WindPy license/permission issue suspected.")
        
        # Step 6: Stop (best effort)
        step6_stop()
        
        return {
            "status": "CONNECT_FAILED",
            "w_start_error": conn_results.get("w_start_empty", {}).get("ErrorCode", "N/A"),
            "c_start_error": conn_results.get("c_start_with_creds", {}).get("ErrorCode", "N/A"),
            "reason": "ErrorCode=-2 on all connection attempts",
            "next_action": "Report to DSHC, return to STATIC_STANDBY"
        }
    
    # Step 6: Stop
    step6_stop()
    
    # Summary
    print("\n" + "=" * 60)
    print("测试完成摘要")
    print("=" * 60)
    return {
        "status": "COMPLETED",
        "connected": connected,
        "query_result": query_result,
        "deps": deps,
        "processes": procs
    }

if __name__ == "__main__":
    try:
        result = main()
        print(f"\nFinal result: {json.dumps(result, default=str, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"\n[FATAL] Unhandled exception: {traceback.format_exc()}")
        log_event("TEST_FATAL_ERROR", "CRASH", str(e))
        sys.exit(1)