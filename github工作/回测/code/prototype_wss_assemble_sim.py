#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
# Force UTF-8 output for Chinese console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""
DSHA-P55/P56 · WSS 分片拼装简易时序 — 离线模拟器 (双开关保护版)

═══════════════════════════════════════════════════════════════════
⚠️  红线警告 — 不执行真实 Wind 调用
═══════════════════════════════════════════════════════════════════
本脚本是离线模拟器，使用随机模拟数据演示 WSS 分片拼装流程。

P56 双开关保护机制:
  第一层开关: 外部许可文件 artifacts/sample_fetch_allow.marker
              → 无此文件时，真实调用分支直接抛出异常
  第二层开关: REAL_WIND_CALL 常量，默认=False
              → 只有存在许可文件才允许手动切换为 True

强制硬限制 (不可修改):
  单次执行最大交易日 = 10
  请求间隔 ≥ 12 秒

COM 释放机制:
  每一次 WSS 调用结束强制销毁 Excel 实例，杜绝 COM 锁堆积。

设计文档: docs/prototype_wss_shard_fetch_design.md
分支: feature/v88-g1 @ 01a022f
状态: 离线原型 · 纸上方案 + 模拟验证 · 双开关保护
"""

import csv
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ════════════════════════════════════════════════════════════
# 🔒 安全锁: 不可切换为 True (本轮工作)
# ════════════════════════════════════════════════════════════

REAL_WIND_CALL = False  # ← 硬锁死，本轮禁止修改

# ════════════════════════════════════════════════════════════
# 限流常量 (设计文档 §4 — 写死不可修改)
# ════════════════════════════════════════════════════════════

MIN_INTERVAL_SEC      = 12      # 最小间隔 (秒)
MAX_INTERVAL_SEC      = 15      # 最大间隔 (秒)

MAX_DAYS_PER_ROUND    = 10      # 最大单轮交易日数量 (P56: 10, 不可修改)

MAX_RETRY_PER_POINT   = 2       # 单点最大重试次数
RETRY_BACKOFF_SEC     = 30      # 重试间隔 (秒)

MAX_CONSECUTIVE_FAIL  = 3       # 连续失败阈值 → 自动停止

EMERGENCY_STOP_FILE   = ".emergency_stop"  # 紧急停止标记文件

# ════════════════════════════════════════════════════════════
# P56: 双开关保护 — 外部许可文件 (第一层开关)
# ════════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERMIT_MARKER_FILE = os.path.join(PROJECT_ROOT, "artifacts", "sample_fetch_allow.marker")

# ════════════════════════════════════════════════════════════
# 模拟器参数
# ════════════════════════════════════════════════════════════

SIM_DATA_POINTS       = 10      # 模拟交易日数量 (P56 硬限制: ≤10)
SIM_SYMBOL            = "ZN.SHF"
SIM_INDICATOR         = "close"
SIM_PRICE_BASE        = 24500.0 # 模拟基准价 (元/吨)
SIM_PRICE_STD         = 120.0   # 模拟价格波动标准差

OUTPUT_DIR            = os.path.join(os.path.dirname(__file__), "sim_output")
OUTPUT_CSV            = os.path.join(OUTPUT_DIR, f"{SIM_SYMBOL}_{SIM_INDICATOR}_simulated.csv")
OUTPUT_STATS          = os.path.join(OUTPUT_DIR, "sim_run_stats.json")


# ════════════════════════════════════════════════════════════
# P56: 双开关保护 — 许可文件检查函数
# ════════════════════════════════════════════════════════════

def check_permit_marker() -> bool:
    """
    检查第一层开关: 外部许可文件是否存在。

    许可文件路径: artifacts/sample_fetch_allow.marker

    返回:
        True: 许可文件存在 (第一层开关已打开)
        False: 许可文件不存在 (第一层开关未打开)
    """
    exists = os.path.exists(PERMIT_MARKER_FILE)
    if exists:
        print(f"  📄 [SWITCH-1] 许可文件存在: {PERMIT_MARKER_FILE}")
    else:
        print(f"  🔒 [SWITCH-1] 许可文件不存在: {PERMIT_MARKER_FILE}")
    return exists


def assert_real_call_allowed():
    """
    双重安全检查: 只有同时满足以下两个条件才允许进入真实调用分支:
      1. 第一层开关: artifacts/sample_fetch_allow.marker 存在
      2. 第二层开关: REAL_WIND_CALL == True

    任一条件不满足则抛出 RuntimeError，阻止执行。
    """
    # 第二层开关检查
    if not REAL_WIND_CALL:
        raise RuntimeError(
            "🚨 [SWITCH-2] REAL_WIND_CALL=False: 禁止进入真实调用分支。\n"
            "   必须同时满足以下两个条件才可启用真实调用:\n"
            "   (1) artifacts/sample_fetch_allow.marker 文件存在\n"
            "   (2) REAL_WIND_CALL 手动切换为 True"
        )

    # 第一层开关检查
    if not os.path.exists(PERMIT_MARKER_FILE):
        raise RuntimeError(
            f"🚨 [SWITCH-1] 外部许可文件不存在: {PERMIT_MARKER_FILE}\n"
            "   请先获取人工许可 marker 文件后再次执行。"
        )

    # 硬限制检查: MAX_DAYS_PER_ROUND 不得超过 10
    if MAX_DAYS_PER_ROUND > 10:
        raise RuntimeError(
            f"🚨 [HARD-LIMIT] MAX_DAYS_PER_ROUND={MAX_DAYS_PER_ROUND} 超过硬限制 10 日。"
        )


def assert_com_cleanup(com_obj):
    """
    COM 强制释放: 确保 Excel COM 实例被销毁。

    参数:
        com_obj: COM 对象 (Excel.Application)

    返回:
        bool: True 表示释放成功，False 表示释放失败 (已尝试清理)
    """
    if com_obj is None:
        return True

    try:
        # 步骤1: 关闭所有工作簿
        try:
            com_obj.Visible = False
            for wb in list(com_obj.Workbooks):
                wb.Close(SaveChanges=False)
        except Exception:
            pass

        # 步骤2: 释放 COM 对象
        try:
            com_obj.Quit()
        except Exception:
            pass

        # 步骤3: 强制 GC
        import gc
        del com_obj
        gc.collect()

        return True

    except Exception as e:
        print(f"  ⚠️ COM 释放异常: {e}")
        import gc
        gc.collect()
        return False


# ════════════════════════════════════════════════════════════
# 交易日生成 (模拟中国期货市场交易日)
# ════════════════════════════════════════════════════════════

def generate_trading_days(start_date_str: str, count: int) -> list:
    """生成模拟交易日列表，跳过周末。"""
    days = []
    current = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    while len(days) < count:
        if current.weekday() < 5:  # 周一~周五
            days.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return days


def is_trading_day(date_str: str) -> bool:
    """判断是否为交易日 (跳过周末)。"""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return d.weekday() < 5


# ════════════════════════════════════════════════════════════
# 模拟 WSS 查询 (零真实调用)
# ════════════════════════════════════════════════════════════

def simulate_wss_query(symbol: str, indicator: str, date: str, call_count: int) -> dict:
    """
    模拟 WSS 单点快照查询。

    ⚠️  这是模拟数据，非真实行情。
    使用随机游走 + 均值回归生成模拟价格序列。

    参数:
        symbol:    品种代码 (如 ZN.SHF)
        indicator: 指标名称 (如 close)
        date:      交易日 (YYYY-MM-DD)
        call_count: 调用次数 (用于模拟价格趋势)

    返回:
        {"value": float, "date": str, "error": False}  或
        {"value": None, "date": str, "error": True}
    """
    if REAL_WIND_CALL:
        # 🔒 安全锁: 如果 REAL_WIND_CALL 被意外切换，强制中止
        raise RuntimeError(
            "🚨 安全锁: REAL_WIND_CALL 被设置为 True，本轮工作禁止修改！\n"
            "必须收到 release_permit 后才能启用真实调用。"
        )

    # 模拟偶发失败 (约 5% 概率)
    if random.random() < 0.05:
        return {
            "value": None,
            "date": date,
            "error": True,
            "error_msg": "Simulated timeout (mock failure)"
        }

    # 生成模拟价格: 随机游走 + 均值回归
    # 基准价 + 波动 + 小幅趋势
    drift = random.gauss(0, SIM_PRICE_STD)
    mean_reversion = (SIM_PRICE_BASE - (SIM_PRICE_BASE + call_count * 5)) * 0.05
    price = SIM_PRICE_BASE + drift + mean_reversion + call_count * 3.5

    # 确保价格为正
    price = max(price, SIM_PRICE_BASE * 0.8)

    # 四舍五入到 2 位小数
    price = round(price, 2)

    return {
        "value": price,
        "date": date,
        "error": False
    }


# ════════════════════════════════════════════════════════════
# P56: 真实 WSS 查询 — 双开关保护 + COM 释放
# ════════════════════════════════════════════════════════════

def real_wss_query(symbol: str, indicator: str, date: str) -> dict:
    """
    真实 WSS 查询 — 双开关保护版本。

    执行前强制检查:
      1. REAL_WIND_CALL == True (第二层开关)
      2. artifacts/sample_fetch_allow.marker 存在 (第一层开关)
      3. MAX_DAYS_PER_ROUND ≤ 10 (硬限制)

    每次调用后强制销毁 Excel COM 实例。

    ⚠️  当前 REAL_WIND_CALL=False，此函数永远不会被实际调用。
    """
    # ── 双重安全检查 ──
    assert_real_call_allowed()

    # 以下为框架代码 (REAL_WIND_CALL=True 时才会执行)
    # 当前被模拟函数完全替代，不会被执行。

    try:
        import win32com.client

        xl = None
        for attempt in range(1, 3):  # COM 重试: 最多 2 次
            try:
                # 创建 Excel COM 实例
                xl = win32com.client.Dispatch("Excel.Application")
                xl.Visible = False
                xl.DisplayAlerts = False

                wb = xl.Workbooks.Add()
                ws = wb.Sheets(1)

                # 写入 WSS 公式
                ws.Cells(1, 1).Value = f'=WSS("{symbol}","{indicator}","{date}")'
                ws.Calculate()

                value = ws.Cells(1, 1).Value
                error = False
                error_msg = None

                if isinstance(value, str) and "Fetching" in value:
                    value = None
                    error = True
                    error_msg = "WSS returned 'Fetching...' (API bridge not active)"

            except Exception as e:
                value = None
                error = True
                error_msg = f"COM error (attempt {attempt}/2): {e}"

                # COM 释放后重试
                if attempt < 2:
                    print(f"  ⚠️ COM 调用失败，尝试释放并重试...")
                    assert_com_cleanup(xl)
                    time.sleep(RETRY_BACKOFF_SEC)
                    continue

            # ── 强制 COM 释放 (每次调用后) ──
            assert_com_cleanup(xl)
            xl = None

            return {
                "value": value,
                "date": date,
                "error": error,
                "error_msg": error_msg
            }

    except ImportError:
        return {
            "value": None,
            "date": date,
            "error": True,
            "error_msg": "win32com not available"
        }


# ════════════════════════════════════════════════════════════
# 限流控制
# ════════════════════════════════════════════════════════════

def apply_rate_limit(call_count: int) -> float:
    """
    计算每次 WSS 调用后的休眠时间。

    返回: 休眠秒数 (float)
    """
    interval = random.uniform(MIN_INTERVAL_SEC, MAX_INTERVAL_SEC)
    return interval


def check_emergency_stop() -> bool:
    """
    检查紧急停止标记文件。

    返回: True 如果标记文件存在
    """
    stop_path = os.path.join(OUTPUT_DIR, EMERGENCY_STOP_FILE)
    return os.path.exists(stop_path)


def check_wmain_alive() -> bool:
    """
    P56: 检查 Wind 终端进程是否存活。
    wmain.exe 或 WBox.exe 任一存活即返回 True。
    """
    import subprocess
    try:
        r = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq wmain.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True
        )
        if 'wmain' in r.stdout.lower():
            return True
        r2 = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq WBox.exe', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True
        )
        if 'wbox' in r2.stdout.lower():
            return True
        return False
    except Exception:
        return True  # 检查失败时不阻断 (非致命)


def print_rate_limit_info(interval: float):
    """打印限流信息。"""
    print(f"  ⏳ 限流休眠: {interval:.1f}s (范围 {MIN_INTERVAL_SEC}-{MAX_INTERVAL_SEC}s)")


# ════════════════════════════════════════════════════════════
# 序列拼装与对齐
# ════════════════════════════════════════════════════════════

def align_and_deduplicate(trading_days: list, snapshots: dict) -> list:
    """
    将逐日快照按时间排序，去重，对齐。

    参数:
        trading_days: 原始交易日列表
        snapshots:    {date: value} 字典

    返回:
        按日期排序的 [{date, value}, ...] 列表
    """
    seen = set()
    aligned = []

    for date in trading_days:
        if date in seen:
            continue  # 去重
        seen.add(date)

        value = snapshots.get(date, None)
        aligned.append({
            "date": date,
            "value": value
        })

    return aligned


def calculate_statistics(snapshots: dict, trading_days: list) -> dict:
    """计算运行统计。"""
    total_points = len(trading_days)
    success_count = sum(1 for d in trading_days if snapshots.get(d) is not None)
    fail_count = total_points - success_count
    missing_count = sum(1 for d in trading_days if d not in snapshots)

    values = [s for s in snapshots.values() if s is not None]

    return {
        "total_points": total_points,
        "success_count": success_count,
        "fail_count": fail_count,
        "missing_count": missing_count,
        "success_rate": round(success_count / total_points * 100, 2) if total_points > 0 else 0,
        "min_value": min(values) if values else None,
        "max_value": max(values) if values else None,
        "mean_value": round(sum(values) / len(values), 2) if values else None,
        "date_range": [trading_days[0], trading_days[-1]] if trading_days else [],
        "symbol": SIM_SYMBOL,
        "indicator": SIM_INDICATOR,
        "data_source": "SIMULATED (NOT REAL)",
        "real_wind_call": REAL_WIND_CALL,
        "permit_marker_exists": os.path.exists(PERMIT_MARKER_FILE),
        "run_timestamp": datetime.now(timezone.utc).isoformat()
    }


# ════════════════════════════════════════════════════════════
# 输出
# ════════════════════════════════════════════════════════════

def write_csv(output_path: str, aligned_series: list):
    """将模拟结果写入 CSV。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "value",
            "symbol", "indicator", "source"
        ])

        for row in aligned_series:
            writer.writerow([
                row["date"],
                row["value"] if row["value"] is not None else "",
                SIM_SYMBOL,
                SIM_INDICATOR,
                "SIMULATED"
            ])

    print(f"  📄 CSV 已写入: {output_path}")


def write_stats(output_path: str, stats: dict):
    """将运行统计写入 JSON。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"  📊 统计已写入: {output_path}")


# ════════════════════════════════════════════════════════════
# P56: 小样测试告警日志
# ════════════════════════════════════════════════════════════

ALERT_LOG_PATH = os.path.join(PROJECT_ROOT, "artifacts", "wss_small_sample_alerts.jsonl")


def log_alert(alert_type: str, severity: str, message: str, details: dict = None):
    """
    P56: 写入告警日志 (JSONL 格式)。

    参数:
        alert_type: 告警类型标识
        severity: 严重级别 (CRITICAL / WARNING / INFO)
        message: 告警描述
        details: 附加信息字典
    """
    os.makedirs(os.path.dirname(ALERT_LOG_PATH), exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "details": details or {},
        "phase": "DSHA-P56",
        "wind_api_calls": 0,
    }

    with open(ALERT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"  🚨 [ALERT:{severity}] {alert_type}: {message}")


# ════════════════════════════════════════════════════════════
# 主模拟流程
# ════════════════════════════════════════════════════════════

def run_simulation():
    """
    执行完整 WSS 分片拼装模拟。

    流程:
        1. 生成模拟交易日 (≤10日硬限制)
        2. 逐日调用模拟 WSS (带限流休眠)
        3. 检查紧急停止 / wmain 存活
        4. 处理重试和失败
        5. 拼装对齐序列
        6. 输出 CSV + 统计 + 告警日志
    """
    print("=" * 70)
    print("DSHA-P56 · WSS 分片拼装简易时序 — 离线模拟器 (双开关保护版)")
    print("=" * 70)
    print()
    print(f"🔒 [SWITCH-2] REAL_WIND_CALL = {REAL_WIND_CALL}  (硬锁死)")
    permit_exists = check_permit_marker()
    print(f"📌 数据源: 模拟数据 (非真实行情)")
    print(f"📌 品种: {SIM_SYMBOL}  指标: {SIM_INDICATOR}")
    print(f"📌 交易日数量: {SIM_DATA_POINTS} (硬限制: ≤{MAX_DAYS_PER_ROUND})")
    print(f"📌 限流间隔: {MIN_INTERVAL_SEC}-{MAX_INTERVAL_SEC}s (不可修改)")
    print(f"📌 COM 释放: 每次调用后强制销毁 Excel 实例")
    print()

    # ── 步骤 0: 硬限制验证 ──
    assert SIM_DATA_POINTS <= MAX_DAYS_PER_ROUND, \
        f"SIM_DATA_POINTS={SIM_DATA_POINTS} 超过硬限制 {MAX_DAYS_PER_ROUND}"
    assert MAX_DAYS_PER_ROUND == 10, \
        f"MAX_DAYS_PER_ROUND={MAX_DAYS_PER_ROUND} 不等于硬限制 10"
    assert MIN_INTERVAL_SEC == 12, \
        f"MIN_INTERVAL_SEC={MIN_INTERVAL_SEC} 不等于硬限制 12"

    # ── 步骤 1: 生成交易日 ──
    start_date = "2025-01-02"
    trading_days = generate_trading_days(start_date, SIM_DATA_POINTS)
    print(f"📅 交易日列表 ({len(trading_days)} 天):")
    for d in trading_days:
        print(f"   - {d}")
    print()

    # ── 步骤 2: 检查紧急停止 ──
    if check_emergency_stop():
        print("🚨 紧急停止标记文件已存在，中止模拟。")
        log_alert("EMERGENCY_STOP_PREEXISTING", "CRITICAL",
                  "紧急停止标记文件已存在，模拟中止",
                  {"stop_file": EMERGENCY_STOP_FILE})
        return

    # ── 步骤 3: 逐日模拟 WSS 查询 ──
    snapshots = {}
    consecutive_failures = 0
    call_count = 0
    total_sleep_time = 0.0
    alert_count = 0

    print(f"🔄 开始逐日模拟查询 (共 {len(trading_days)} 次请求)...")
    print("-" * 50)

    for i, day in enumerate(trading_days, 1):
        # 紧急停止检查
        if check_emergency_stop():
            print(f"🚨 紧急停止标记文件出现于第 {i} 轮，中止。")
            log_alert("EMERGENCY_STOP_TRADE_DATE", "CRITICAL",
                      f"紧急停止标记文件出现于第 {i} 轮 ({day})",
                      {"trade_date": day, "round": i})
            alert_count += 1
            break

        # P56: Wind 终端进程存活检查 (真实调用前必须)
        if REAL_WIND_CALL and not check_wmain_alive():
            print(f"🚨 wmain/WBox 进程不存在于第 {i} 轮，触发紧急停止。")
            log_alert("WMAIN_WINDOW_LOST", "CRITICAL",
                      f"Wind 终端进程不存在，第 {i} 轮 ({day}) 紧急停止",
                      {"trade_date": day, "round": i})
            alert_count += 1
            break

        # 连续失败检查
        if consecutive_failures >= MAX_CONSECUTIVE_FAIL:
            print(f"🚨 连续失败 {consecutive_failures} 次 (阈值 {MAX_CONSECUTIVE_FAIL})，自动停止。")
            log_alert("CONSECUTIVE_FAIL_STOP", "CRITICAL",
                      f"连续 {consecutive_failures} 次失败，自动停止",
                      {"failures": consecutive_failures, "round": i, "date": day})
            alert_count += 1
            break

        # 单轮限制检查
        if i > MAX_DAYS_PER_ROUND:
            print(f"⚠️  已达到单轮最大交易日数 {MAX_DAYS_PER_ROUND}，停止。")
            log_alert("MAX_DAYS_LIMIT_REACHED", "WARNING",
                      f"已达到单轮最大交易日数 {MAX_DAYS_PER_ROUND}",
                      {"round": i})
            alert_count += 1
            break

        print(f"\n  [{i}/{len(trading_days)}] 查询 {day}...", end=" ")

        # 重试循环
        result = None
        for attempt in range(1, MAX_RETRY_PER_POINT + 1):
            # 实际查询 (模拟)
            result = simulate_wss_query(SIM_SYMBOL, SIM_INDICATOR, day, call_count)
            call_count += 1

            if not result["error"]:
                break  # 成功，退出重试

            # 失败，检查是否需要重试
            if attempt < MAX_RETRY_PER_POINT:
                print(f" ⚠️ 失败 (尝试 {attempt}/{MAX_RETRY_PER_POINT})", end=" ")
                # 重试退避
                time.sleep(min(RETRY_BACKOFF_SEC, 1))  # 模拟中用最小退避
            else:
                print(f" ❌ 最终失败 (尝试 {MAX_RETRY_PER_POINT} 次)")
                consecutive_failures += 1

        # 记录结果
        if result and not result["error"]:
            snapshots[day] = result["value"]
            consecutive_failures = 0
            print(f"   ✅ {result['value']:.2f}")
        else:
            print(f"   ⚠️ 缺失")

        # 限流休眠
        if i < len(trading_days):
            interval = apply_rate_limit(call_count)
            total_sleep_time += interval
            print_rate_limit_info(interval)
            # 模拟模式：不实际休眠，仅记录
            # time.sleep(interval)  # ← 模拟中跳过实际休眠

    # ── 步骤 4: 拼装对齐 ──
    print("\n" + "=" * 50)
    print("📦 序列拼装与对齐...")

    # 确保所有日期都在对齐结果中
    all_days = set(trading_days)
    for day in all_days:
        if day not in snapshots:
            snapshots[day] = None  # 缺失标记

    aligned = align_and_deduplicate(trading_days, snapshots)

    print(f"   对齐后数据点: {len(aligned)}")
    print(f"   有效数据: {sum(1 for r in aligned if r['value'] is not None)}")
    print(f"   缺失数据: {sum(1 for r in aligned if r['value'] is None)}")

    # ── 步骤 5: 输出结果 ──
    print("\n📁 写入输出文件...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    write_csv(OUTPUT_CSV, aligned)

    # ── 步骤 6: 统计 ──
    stats = calculate_statistics(snapshots, trading_days)
    stats["total_sleep_time_sec"] = round(total_sleep_time, 1)
    stats["total_calls"] = call_count
    stats["min_interval_sec"] = MIN_INTERVAL_SEC
    stats["max_interval_sec"] = MAX_INTERVAL_SEC
    stats["max_days_per_round"] = MAX_DAYS_PER_ROUND
    stats["emergency_stop_file"] = EMERGENCY_STOP_FILE
    stats["simulation_note"] = "SIMULATED DATA — NOT REAL MARKET DATA"
    stats["permit_marker_exists"] = permit_exists
    stats["alert_count"] = alert_count
    stats["phase"] = "DSHA-P56"

    write_stats(OUTPUT_STATS, stats)

    # ── 步骤 7: 输出摘要 ──
    print()
    print("=" * 70)
    print("📊 模拟运行摘要")
    print("=" * 70)
    print(f"  数据源:              {stats['data_source']}")
    print(f"  品种/指标:           {SIM_SYMBOL} / {SIM_INDICATOR}")
    print(f"  交易日数:            {stats['total_points']}")
    print(f"  成功/失败:           {stats['success_count']}/{stats['fail_count']}")
    print(f"  成功率:              {stats['success_rate']}%")
    print(f"  价格范围:            {stats['min_value']:.2f} - {stats['max_value']:.2f}")
    print(f"  均值:                {stats['mean_value']:.2f}")
    print(f"  总调用次数:          {stats['total_calls']}")
    print(f"  限流总休眠:          {stats['total_sleep_time_sec']:.1f}s (模拟，未实际休眠)")
    print(f"  REAL_WIND_CALL:      {REAL_WIND_CALL}")
    print(f"  许可文件(SWITCH-1): {'✅ 存在' if permit_exists else '🔒 不存在'}")
    print(f"  告警数:              {alert_count}")
    print()
    print("📌 输出文件:")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_STATS}")
    print(f"  - {ALERT_LOG_PATH} (告警日志)")
    print()
    print("=" * 70)
    print("⚠️  再次提醒:")
    print("   1. 以上为模拟数据，非真实行情。")
    print("   2. REAL_WIND_CALL 已锁定为 False，禁止在本轮工作中修改。")
    print("   3. 双重开关: 许可文件 + REAL_WIND_CALL=True 缺一不可。")
    print("   4. 硬限制: 单次≤10个交易日, 间隔≥12秒, 不可修改。")
    print("   5. 每次 WSS 调用后强制销毁 Excel COM 实例。")
    print("   6. 小样测试完成后必须人工复核数据，才可申请更大权限。")
    print("=" * 70)

    return stats


# ════════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  DSHA-P56 · WSS 分片拼装简易时序 — 离线模拟器 (双开关版)    ║")
    print("║  状态: 模拟原型 · REAL_WIND_CALL=False · 零真实调用         ║")
    print("║  硬限制: ≤10交易日 · 间隔≥12s · COM强制释放               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    stats = run_simulation()

    print()
    print("✅ 模拟完成。本脚本未调用任何真实 Wind API。")
    sys.exit(0)
