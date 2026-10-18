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
DSHA-P55 · WSS 分片拼装简易时序 — 离线模拟器

══════════════════════════════════════════════════════════════
⚠️  红线警告 — 不执行真实 Wind 调用
══════════════════════════════════════════════════════════════
本脚本是离线模拟器，使用随机模拟数据演示 WSS 分片拼装流程。
REAL_WIND_CALL 常量已强制锁定为 False，本轮不可切换为 True。
没有 release_permit 许可前，不得对真实 Wind 发起任何循环请求。
══════════════════════════════════════════════════════════════

设计文档: docs/prototype_wss_shard_fetch_design.md
分支: feature/v88-g1 @ 01a022f
状态: 离线原型 · 纸上方案 + 模拟验证
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

MAX_DAYS_PER_ROUND    = 12      # 最大单轮交易日数量

MAX_RETRY_PER_POINT   = 2       # 单点最大重试次数
RETRY_BACKOFF_SEC     = 30      # 重试间隔 (秒)

MAX_CONSECUTIVE_FAIL  = 3       # 连续失败阈值 → 自动停止

EMERGENCY_STOP_FILE   = ".emergency_stop"  # 紧急停止标记文件

# ════════════════════════════════════════════════════════════
# 模拟器参数
# ════════════════════════════════════════════════════════════

SIM_DATA_POINTS       = 10      # 模拟交易日数量 (演示用)
SIM_SYMBOL            = "ZN.SHF"
SIM_INDICATOR         = "close"
SIM_PRICE_BASE        = 24500.0 # 模拟基准价 (元/吨)
SIM_PRICE_STD         = 120.0   # 模拟价格波动标准差

OUTPUT_DIR            = os.path.join(os.path.dirname(__file__), "sim_output")
OUTPUT_CSV            = os.path.join(OUTPUT_DIR, f"{SIM_SYMBOL}_{SIM_INDICATOR}_simulated.csv")
OUTPUT_STATS          = os.path.join(OUTPUT_DIR, "sim_run_stats.json")

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
# 真实 WSS 查询 (占位符 — 仅框架，不执行)
# ════════════════════════════════════════════════════════════

def real_wss_query(symbol: str, indicator: str, date: str) -> dict:
    """
    真实 WSS 查询占位符。
    
    ⚠️  此函数仅当 REAL_WIND_CALL=True 时才允许调用。
    当前被模拟函数完全替代，不会被执行。
    """
    if not REAL_WIND_CALL:
        raise RuntimeError("REAL_WIND_CALL=False: 禁止调用真实 WSS")
    
    # TODO (仅当 release_permit 收到后):
    # 1. 检查前置清单全部通过
    # 2. 启动 Excel WDF 插件
    # 3. 写入 =WSS("ZN.SHF","close","2025-01-01")
    # 4. 计算并读取结果
    # 5. 返回数值
    #
    # 框架代码:
    # import win32com.client
    # xl = win32com.client.Dispatch("Excel.Application")
    # ... (禁止在本轮执行)
    
    return {"value": None, "date": date, "error": True, "error_msg": "NOT_IMPLEMENTED"}


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
# 主模拟流程
# ════════════════════════════════════════════════════════════

def run_simulation():
    """
    执行完整 WSS 分片拼装模拟。
    
    流程:
        1. 生成模拟交易日
        2. 逐日调用模拟 WSS (带限流休眠)
        3. 检查紧急停止
        4. 处理重试和失败
        5. 拼装对齐序列
        6. 输出 CSV + 统计
    """
    print("=" * 70)
    print("DSHA-P55 · WSS 分片拼装简易时序 — 离线模拟器")
    print("=" * 70)
    print()
    print(f"🔒 REAL_WIND_CALL = {REAL_WIND_CALL}  (硬锁死)")
    print(f"📌 数据源: 模拟数据 (非真实行情)")
    print(f"📌 品种: {SIM_SYMBOL}  指标: {SIM_INDICATOR}")
    print(f"📌 模拟交易日数量: {SIM_DATA_POINTS}")
    print(f"📌 限流间隔: {MIN_INTERVAL_SEC}-{MAX_INTERVAL_SEC}s")
    print()
    
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
        return
    
    # ── 步骤 3: 逐日模拟 WSS 查询 ──
    snapshots = {}
    consecutive_failures = 0
    call_count = 0
    total_sleep_time = 0.0
    
    print(f"🔄 开始逐日模拟查询 (共 {len(trading_days)} 次请求)...")
    print("-" * 50)
    
    for i, day in enumerate(trading_days, 1):
        # 紧急停止检查
        if check_emergency_stop():
            print(f"🚨 紧急停止标记文件出现于第 {i} 轮，中止。")
            break
        
        # 连续失败检查
        if consecutive_failures >= MAX_CONSECUTIVE_FAIL:
            print(f"🚨 连续失败 {consecutive_failures} 次 (阈值 {MAX_CONSECUTIVE_FAIL})，自动停止。")
            break
        
        # 单轮限制检查
        if i > MAX_DAYS_PER_ROUND:
            print(f"⚠️  已达到单轮最大交易日数 {MAX_DAYS_PER_ROUND}，停止。")
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
    
    write_stats(OUTPUT_STATS, stats)
    
    # ── 步骤 7: 输出摘要 ──
    print()
    print("=" * 70)
    print("📊 模拟运行摘要")
    print("=" * 70)
    print(f"  数据源:      {stats['data_source']}")
    print(f"  品种/指标:   {SIM_SYMBOL} / {SIM_INDICATOR}")
    print(f"  交易日数:    {stats['total_points']}")
    print(f"  成功/失败:   {stats['success_count']}/{stats['fail_count']}")
    print(f"  成功率:      {stats['success_rate']}%")
    print(f"  价格范围:    {stats['min_value']:.2f} - {stats['max_value']:.2f}")
    print(f"  均值:        {stats['mean_value']:.2f}")
    print(f"  总调用次数:  {stats['total_calls']}")
    print(f"  限流总休眠:  {stats['total_sleep_time_sec']:.1f}s (模拟，未实际休眠)")
    print(f"  REAL_WIND_CALL: {REAL_WIND_CALL}")
    print()
    print("📌 输出文件:")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_STATS}")
    print()
    print("=" * 70)
    print("⚠️  再次提醒: 以上为模拟数据，非真实行情。")
    print("⚠️  REAL_WIND_CALL 已锁定为 False，禁止在本轮工作中修改。")
    print("⚠️  未收到 release_permit 前，不得对真实 Wind 发起循环请求。")
    print("=" * 70)
    
    return stats


# ════════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  DSHA-P55 · WSS 分片拼装简易时序 — 离线模拟器              ║")
    print("║  状态: 模拟原型 · REAL_WIND_CALL=False · 零真实调用         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    stats = run_simulation()
    
    print()
    print("✅ 模拟完成。本脚本未调用任何真实 Wind API。")
    sys.exit(0)
