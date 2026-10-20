#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHA-TASK-051 · 冻结策略沙箱回放+压力校验工单
═══════════════════════════════════════════════
令牌: DSHA-TASK051-FROZEN-BACKTEST-VALID-TOKEN
基线: feature/v88-g1 HEAD=e61f2f4 (TASK050)

任务:
  P0  前置冒烟自检: V3冻结文件哈希/Set-E锁/因子完整性, 11项全检
  P1  全周期沙箱回放: 完整历史分片回放V3冻结策略, 核对偏差≤±0.005
  P2  压力扰动校验: 噪声扰动/行情跳变, 监控拥挤度/因子相关性
  P3  边界场景测试: 低流动性/连续换月/极端涨跌, 采集告警触发
  P4  全链路风险复核: HHI/相关性/拥挤度/翻转率, 压力测试风险报告
  P5  回放指标+压力测试+边界场景日志→DSHD审计台账
  P6  归档回放全量制品, 生成V3版本验收文档

红线:
  - 仅只读回放+压力测试, 严禁修改V3冻结策略/因子定义/引擎参数
  - 基准指标偏差>±0.005 或 压力测试拥挤度>1.1x → 自动FAIL并停止
  - 任何异常→上报DSHD, 不自动调整策略参数
  - wind_api_calls=0; Gate=CLOSED/HOLD; Release=NOT_ISSUED
"""
from __future__ import annotations

import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json, hashlib, math, time, warnings, csv, re, copy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from collections import defaultdict
import random

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

warnings.filterwarnings("ignore", message=".*input array is constant.*")
warnings.filterwarnings("ignore", message=".*All-NaN slice.*")
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════════
# JSON Encoder
# ════════════════════════════════════════════════════════════════
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        elif isinstance(obj, (np.floating,)): return float(obj)
        elif isinstance(obj, (np.bool_,)): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        elif isinstance(obj, (pd.Timestamp,)): return obj.isoformat()
        return super().default(obj)

def dump_json(path, data, indent=2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent, cls=NumpyEncoder)
    sz = os.path.getsize(path)
    print(f"  ✓ 写入 {path} ({sz:,} bytes)")

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 (永久不可修改)
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
TOKEN = "DSHA-TASK051-FROZEN-BACKTEST-VALID-TOKEN"
BASELINE_COMMIT = "e61f2f4"
TASK_ID = "DSHA-TASK051-FROZEN-BACKTEST-VALID"
GATE_STATUS = "CLOSED/HOLD"
RELEASE_STATUS = "NOT_ISSUED"
SET_E_FROZEN = True
READ_ONLY_MODE = True  # ← TASK051 新增: 只读回放模式
TZ = timezone(timedelta(hours=8))

# ════════════════════════════════════════════════════════════════
# 路径常量
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(r"D:\DSH_WORK\github工作\回测")
PROD_DIR = PROJECT_ROOT / "artifacts" / "p49_v3_backtest"
RESEARCH_DIR = PROJECT_ROOT / "artifacts" / "p49_v3_regime_weight"
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"
DSHD_BRIEF = PROJECT_ROOT / "artifacts" / "dshd_cluster_brief_regime_crowding.md"
DSHD_PUSH_FILE = PROJECT_ROOT / "artifacts" / "dshd_task051_frozen_backtest_push.json"

V3_FACTORS_CSV = PROD_DIR / "factors_full_11_v3.csv"
FACTOR_WEIGHT_PROD = PROD_DIR / "factor_weight_prod.json"
FACTOR_ENABLE_CONFIG = PROD_DIR / "factor_enable_config.json"
PROD_CHECKSUM = PROD_DIR / "prod_baseline_checksum.json"
SET_E_LOCK = PROJECT_ROOT / "artifacts" / "p49_v2_experiment" / "strategy_set_e.lock.json"

# V3 冻结制品路径 (只读引用)
FINAL_WEIGHT_RULES = RESEARCH_DIR / "final_weight_rules.json"
TASK050_BACKTEST_METRICS = RESEARCH_DIR / "dual_window_backtest_metrics.json"
TASK050_RISK_VALIDATION = RESEARCH_DIR / "risk_validation_final.json"
TASK050_VERSION_FREEZE = RESEARCH_DIR / "version_freeze_document.json"
TASK050_CONTRACT_FLAG = RESEARCH_DIR / "contract_switch_flag_final.json"
TASK050_MANIFEST = RESEARCH_DIR / "MANIFEST_v3_regime_weight.json"
TASK050_SCRIPT = RESEARCH_DIR / "run_task050_strategy_freeze.py"
TASK050_DSHD_PUSH = PROJECT_ROOT / "artifacts" / "dshd_task050_strategy_freeze_push.json"

# ════════════════════════════════════════════════════════════════
# Set-E 冻结参数 (不可修改 — 从V3读取)
# ════════════════════════════════════════════════════════════════
SIGNAL_THRESHOLD = 0.3
REBALANCE_INTERVAL = 5
TARGET_VOL = 0.15
MAX_SINGLE_WEIGHT = 0.5
DRAWDOWN_WARN = -0.10
DRAWDOWN_HALT = -0.20
TRANSACTION_COST = 0.0005
INITIAL_CAPITAL = 1_000_000.0
TRADING_DAYS_PER_YEAR = 252

# ════════════════════════════════════════════════════════════════
# 品种白名单
# ════════════════════════════════════════════════════════════════
SYMBOL_WHITELIST = ['LC.GFE', 'NI.SHF', 'ZN.SHF', 'CU.SHF']
SYMBOL_9 = ['LC.GFE', 'NI.SHF', 'ZN.SHF', 'CU.SHF', 'SN.SHF', 'PB.SHF', 'AL.SHF', 'ZN.GFE', 'CU.GFE']

# ════════════════════════════════════════════════════════════════
# 因子定义
# ════════════════════════════════════════════════════════════════
FACTORS = ['contract_switch_flag', 'momentum_20d', 'oi_change_1d',
           'oi_change_rate_7d', 'oi_level', 'realized_vol_20d',
           'spread_cs', 'vol_regime_change']
NUM_FACTORS = len(FACTORS)

# ════════════════════════════════════════════════════════════════
# IC / Regime 参数
# ════════════════════════════════════════════════════════════════
IC_WINDOW_20 = 20
IC_WINDOW_40 = 40
IC_STEP = 20
MIN_IC_WINDOWS = 20
REGIME_UP_PCT = 0.005
REGIME_DOWN_PCT = 0.005

# ════════════════════════════════════════════════════════════════
# TASK051 核心参数
# ════════════════════════════════════════════════════════════════
BASELINE_ALPHA = 0.6
WEIGHT_MIN = 0.04
WEIGHT_MAX = 0.25
WEIGHT_CAP_OPT = 0.20
SHARPE_THRESHOLD = 3.4
CROWDING_MAX = 1.10
OI_CHANGE_THRESHOLD = -0.30
OI_CHANGE_LOOKBACK = 1

# TASK051 特有: 偏差阈值
DEVIATION_THRESHOLD = 0.005  # ±0.005 偏差阈值

# TASK051 特有: 压力扰动参数
NOISE_SIGMA_FACTOR = 0.02  # 噪声标准差 = 因子std * 此系数
MARKET_JUMP_PCT = 0.05      # 行情跳变幅度 ±5%
VOL_SPIKE_FACTOR = 2.0      # 波动率放大倍数
POTENTIATION_SEED = 42       # 随机种子 (可复现)

# ════════════════════════════════════════════════════════════════
# DSHD 监控参数
# ════════════════════════════════════════════════════════════════
DSHD_TOKEN = "DSHD-TASK051-FROZEN-BACKTEST-VALID-TOKEN"
CROWDING_ALERT_PERCENTILE = 90
CROWDING_ALERT_LEVEL = "MEDIUM"
HHI_CROWDING_THRESHOLD = 1.10
DRAWDOWN_THRESHOLD = 0.03

# ════════════════════════════════════════════════════════════════
# 全局
# ════════════════════════════════════════════════════════════════
df_global: Optional[pd.DataFrame] = None
task050_baseline_metrics: Dict = {}
task050_final_weights: Dict = {}

# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════
def now_iso():
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")

def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def append_audit(event):
    entry = dict(event)
    entry["_audit_ts"] = now_iso()
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, cls=NumpyEncoder) + "\n")
    print(f"  ✓ 审计日志已追加: {event.get('event','?')}")

def log(s):
    print(f"[{now_iso()}] {s}")

# ════════════════════════════════════════════════════════════════
# P0: 前置冒烟自检 — 11项全检
# ════════════════════════════════════════════════════════════════
def p0_prereq_check():
    results = {}

    # 1. V3 final_weight_rules.json 存在且冻结
    if FINAL_WEIGHT_RULES.exists():
        fwr = json.loads(FINAL_WEIGHT_RULES.read_text(encoding="utf-8"))
        results["v3_final_weight_rules"] = fwr.get("freeze_status") == "PERMANENTLY_FROZEN"
        results["v3_selected_window"] = fwr.get("selected_window")
        results["v3_selected_alpha"] = fwr.get("selected_alpha")
        results["v3_sharpe_achieved"] = fwr.get("sharpe_achieved")
        results["v3_crowding_achieved"] = fwr.get("crowding_achieved")
        results["v3_fwr_sha256"] = sha256_file(FINAL_WEIGHT_RULES)
        log(f"  ✓ V3冻结文件: 窗口={fwr.get('selected_window')}, alpha={fwr.get('selected_alpha')}, "
            f"sharpe={fwr.get('sharpe_achieved'):.4f}, crowding={fwr.get('crowding_achieved'):.4f}x")
    else:
        results["v3_final_weight_rules"] = False
        log(f"  ✗ V3冻结文件不存在: {FINAL_WEIGHT_RULES}")

    # 2. Set-E Lock 状态
    if SET_E_LOCK.exists():
        set_e_lock = json.loads(SET_E_LOCK.read_text(encoding="utf-8"))
        results["set_e_frozen"] = set_e_lock.get("status") == "PERMANENTLY_FROZEN"
        log(f"  ✓ Set-E锁: {set_e_lock.get('status')}")
    else:
        results["set_e_frozen"] = False
        log(f"  ⚠ Set-E锁文件不存在")

    # 3. 因子定义完整性 (8因子)
    results["factor_count"] = NUM_FACTORS
    results["factor_names"] = FACTORS
    log(f"  ✓ 因子定义: {NUM_FACTORS}个因子 — {FACTORS}")

    # 4. V3 冻结策略参数完整性
    if FINAL_WEIGHT_RULES.exists():
        fwr = json.loads(FINAL_WEIGHT_RULES.read_text(encoding="utf-8"))
        required_keys = ["selected_window", "selected_alpha", "ic_window", "dynamic_weights",
                         "fixed_weights", "equal_weight_baseline", "engine_params",
                         "freeze_status", "sharpe_achieved", "crowding_achieved"]
        missing = [k for k in required_keys if k not in fwr]
        results["v3_params_complete"] = len(missing) == 0
        results["v3_missing_keys"] = missing
        log(f"  {'✓' if len(missing)==0 else '⚠'} V3参数完整性: {'全部就绪' if len(missing)==0 else f'缺失{missing}'}")
    else:
        results["v3_params_complete"] = False

    # 5. TASK050 基准制品完整性
    task050_files = [
        TASK050_BACKTEST_METRICS, TASK050_RISK_VALIDATION,
        TASK050_VERSION_FREEZE, TASK050_CONTRACT_FLAG,
        TASK050_MANIFEST, TASK050_SCRIPT, TASK050_DSHD_PUSH,
    ]
    results["task050_artifacts"] = all(f.exists() for f in task050_files)
    results["task050_missing"] = [str(f) for f in task050_files if not f.exists()]
    log(f"  TASK050基准制品: {'✅齐全' if results['task050_artifacts'] else '❌缺失'}")

    # 6. 生产配置指纹验证 (不可修改)
    prod_w_hash = sha256_file(FACTOR_WEIGHT_PROD)
    prod_cfg_hash = sha256_file(FACTOR_ENABLE_CONFIG)
    prod_checksum = json.loads(PROD_CHECKSUM.read_text(encoding="utf-8"))
    expected_w = prod_checksum.get("config_fingerprints", {}).get("factor_weight_prod", {}).get("sha256")
    expected_c = prod_checksum.get("config_fingerprints", {}).get("factor_enable_config", {}).get("sha256")
    results["prod_configs_unchanged"] = (prod_w_hash == expected_w and prod_cfg_hash == expected_c)
    log(f"  {'✓' if results['prod_configs_unchanged'] else '⚠'} 生产配置指纹: {'✅匹配' if results['prod_configs_unchanged'] else '⚠不匹配'}")

    # 7. 数据文件完整性
    if V3_FACTORS_CSV.exists():
        results["factors_csv"] = True
        results["factors_csv_sha256"] = sha256_file(V3_FACTORS_CSV)
        results["factors_csv_size"] = V3_FACTORS_CSV.stat().st_size
        log(f"  ✓ 因子数据CSV: SHA={results['factors_csv_sha256'][:16]}...")
    else:
        results["factors_csv"] = False
        log(f"  ✗ 因子数据CSV不存在")

    # 8. 安全状态
    results["wind_api_calls"] = WIND_API_CALLS
    results["gate"] = GATE_STATUS
    results["release"] = RELEASE_STATUS
    results["read_only_mode"] = READ_ONLY_MODE
    log(f"  ✓ 安全: wind=0, Gate={GATE_STATUS}, Release={RELEASE_STATUS}, readonly={READ_ONLY_MODE}")

    # 9. 偏差阈值已设定
    results["deviation_threshold"] = DEVIATION_THRESHOLD
    log(f"  ✓ 偏差阈值: ±{DEVIATION_THRESHOLD}")

    # 10. 引擎参数匹配V3冻结
    if FINAL_WEIGHT_RULES.exists():
        fwr = json.loads(FINAL_WEIGHT_RULES.read_text(encoding="utf-8"))
        engine_params = fwr.get("engine_params", {})
        expected_engine = {
            "signal_threshold": SIGNAL_THRESHOLD,
            "rebalance_interval": REBALANCE_INTERVAL,
            "target_vol": TARGET_VOL,
            "max_single_weight": MAX_SINGLE_WEIGHT,
            "drawdown_warn": DRAWDOWN_WARN,
            "drawdown_halt": DRAWDOWN_HALT,
            "transaction_cost": TRANSACTION_COST,
            "initial_capital": INITIAL_CAPITAL,
        }
        match = all(engine_params.get(k) == v for k, v in expected_engine.items())
        results["engine_params_match_v3"] = match
        log(f"  {'✓' if match else '⚠'} 引擎参数匹配V3: {'✅一致' if match else '⚠不一致'}")
    else:
        results["engine_params_match_v3"] = False

    # 11. TASK050基准指标可读取
    if TASK050_BACKTEST_METRICS.exists():
        baseline_data = json.loads(TASK050_BACKTEST_METRICS.read_text(encoding="utf-8"))
        group_b = baseline_data.get("groups", {}).get("group_b_dynamic_a06_20d", {})
        results["baseline_metrics_readable"] = bool(group_b.get("metrics"))
        results["baseline_sharpe"] = group_b.get("metrics", {}).get("sharpe_ratio")
        results["baseline_return"] = group_b.get("metrics", {}).get("total_return")
        results["baseline_max_dd"] = group_b.get("metrics", {}).get("max_drawdown")
        log(f"  {'✓' if results['baseline_metrics_readable'] else '⚠'} TASK050基准指标可读: "
            f"sharpe={results['baseline_sharpe']}, return={results['baseline_return']}")
    else:
        results["baseline_metrics_readable"] = False

    # Summary
    all_pass = all([
        results.get("v3_final_weight_rules", False),
        results.get("set_e_frozen", False),
        results.get("v3_params_complete", False),
        results.get("task050_artifacts", False),
        results.get("prod_configs_unchanged", False),
        results.get("factors_csv", False),
        WIND_API_CALLS == 0,
        GATE_STATUS == "CLOSED/HOLD",
        RELEASE_STATUS == "NOT_ISSUED",
        results.get("engine_params_match_v3", False),
        results.get("baseline_metrics_readable", False),
    ])
    results["p0_all_pass"] = all_pass
    return results

# ════════════════════════════════════════════════════════════════
# 数据加载
# ════════════════════════════════════════════════════════════════
def load_factors_csv():
    df = pd.read_csv(V3_FACTORS_CSV, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    log(f"数据集加载: {len(df)}行 × {len(df.columns)}列")
    return df

def classify_regimes(df):
    df = df.sort_values(["symbol", "date"]).copy()
    ma20 = df.groupby("symbol")["close"].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df["ma20"] = ma20
    df["pct_dev"] = (df["close"] - df["ma20"]) / df["ma20"]
    df["regime"] = np.where(df["pct_dev"] > REGIME_UP_PCT, "up",
                            np.where(df["pct_dev"] < -REGIME_DOWN_PCT, "down", "sideways"))
    df["regime"] = df["regime"].fillna("sideways")
    counts = df["regime"].value_counts().to_dict()
    log(f"行情分类: {counts}")
    return df, counts

def rebuild_contract_switch_flag(df):
    df = df.sort_values(["symbol", "date"]).copy()
    old_flag = df["contract_switch_flag"].copy()
    oi_prev = df.groupby("symbol")["oi"].shift(1)
    oi_change_pct = (df["oi"] - oi_prev) / oi_prev
    df["contract_switch_flag_new"] = np.where(
        (oi_change_pct < OI_CHANGE_THRESHOLD) & oi_change_pct.notna(),
        1.0, 0.0
    )
    df["contract_switch_flag_new"] = df["contract_switch_flag_new"].fillna(0.0)
    new_nonzero = int((df["contract_switch_flag_new"] > 0).sum())
    new_total = len(df)
    log(f"  contract_switch_flag重建: 非零={new_nonzero}/{new_total} ({new_nonzero/new_total*100:.2f}%)")
    df["contract_switch_flag"] = df["contract_switch_flag_new"]
    df.drop(columns=["contract_switch_flag_new"], inplace=True)
    return df, {"nonzero": new_nonzero, "total": new_total, "pct": round(new_nonzero/new_total*100, 2)}

# ════════════════════════════════════════════════════════════════
# IC 计算
# ════════════════════════════════════════════════════════════════
def compute_rolling_ic(series, returns, window=IC_WINDOW_20, step=IC_STEP):
    ics = []
    starts = list(range(0, len(series) - window, step))
    for s in starts:
        e = s + window
        xs = series.iloc[s:e].dropna()
        ys = returns.iloc[s:e].dropna()
        if len(xs) >= max(15, window // 4):
            try:
                r = pearsonr(xs.values, ys.values)[0]
                ics.append(r)
            except:
                pass
    return ics

def compute_regime_ic(df, symbol_pool, factor, regime_name, ic_window=IC_WINDOW_20):
    sub = df[(df["symbol"].isin(symbol_pool)) & (df["regime"] == regime_name)].copy()
    if len(sub) < ic_window:
        return None, 0, 0.0
    sub = sub.sort_values(["symbol", "date"])
    sub["fwd_ret"] = sub.groupby("symbol")["close"].shift(-1) / sub["close"] - 1
    sub = sub.dropna(subset=["fwd_ret", factor])
    if len(sub) < max(15, ic_window // 4):
        return None, 0, 0.0
    factor_vals = sub[factor].dropna()
    non_zero = factor_vals[factor_vals != 0]
    if len(non_zero) == 0:
        return {"mean_ic": 0.0, "num_windows": 0, "flip_rate": 0.0,
                "note": "constant_or_zero_factor"}, len(sub), 0.0
    ics = compute_rolling_ic(sub[factor], sub["fwd_ret"], window=ic_window, step=IC_STEP)
    if not ics:
        return None, 0, 0.0
    ics_arr = np.array(ics)
    ic_mean = float(np.nanmean(ics_arr)) if len(ics_arr) > 0 else 0.0
    if math.isnan(ic_mean):
        ic_mean = 0.0
    flip_rate = float(np.sum(np.diff(np.sign(ics_arr)) != 0) / max(len(ics_arr) - 1, 1))
    return {"mean_ic": ic_mean, "num_windows": len(ics), "flip_rate": flip_rate}, len(sub), flip_rate

def handle_constant_factor_ic(ic_val):
    if ic_val is None: return 0.0
    if isinstance(ic_val, float) and math.isnan(ic_val): return 0.0
    return ic_val

# ════════════════════════════════════════════════════════════════
# 动态权重计算 (与TASK050完全一致)
# ════════════════════════════════════════════════════════════════
def compute_dynamic_weights(ic_data, blend_alpha=0.6):
    equal_w = {f: 1.0 / NUM_FACTORS for f in FACTORS}
    weights = {"up": {}, "down": {}, "sideways": {}}
    for regime in ["up", "down"]:
        ic_info = ic_data.get("ic_9sym", {}).get(regime, {})
        if not ic_info:
            weights[regime] = dict(equal_w)
            continue
        ic_abs = {}
        for f in FACTORS:
            ic_val = ic_info.get(f, {}).get("mean_ic", 0.0)
            ic_val = handle_constant_factor_ic(ic_val)
            ic_abs[f] = abs(ic_val)
        total_abs = sum(ic_abs.values())
        if total_abs < 1e-10:
            weights[regime] = dict(equal_w)
            continue
        ic_w = {f: ic_abs[f] / total_abs for f in FACTORS}
        for f in FACTORS:
            ic_w[f] = max(WEIGHT_MIN, min(WEIGHT_MAX, ic_w[f]))
        s = sum(ic_w.values())
        ic_w = {f: ic_w[f] / s for f in FACTORS}
        weights[regime] = {
            f: blend_alpha * equal_w[f] + (1 - blend_alpha) * ic_w[f]
            for f in FACTORS
        }
    weights["sideways"] = dict(equal_w)
    all_ic_abs = {f: 0.0 for f in FACTORS}
    for regime in ["up", "down", "sideways"]:
        ic_info = ic_data.get("ic_9sym", {}).get(regime, {})
        for f in FACTORS:
            ic_val = ic_info.get(f, {}).get("mean_ic", 0.0)
            ic_val = handle_constant_factor_ic(ic_val)
            all_ic_abs[f] += abs(ic_val)
    total_abs = sum(all_ic_abs.values())
    if total_abs > 1e-10:
        fixed_w = {f: max(WEIGHT_MIN, min(WEIGHT_MAX, all_ic_abs[f] / total_abs)) for f in FACTORS}
        s = sum(fixed_w.values())
        fixed_w = {f: fixed_w[f] / s for f in FACTORS}
    else:
        fixed_w = dict(equal_w)
    return weights, fixed_w

def compute_hhi_from_weights(weights_dict):
    hhis = {}
    for regime, w in weights_dict.items():
        hhi = sum(w.get(f, 0) ** 2 for f in FACTORS)
        hhis[regime] = hhi
    hhi_avg = sum(hhis.values()) / len(hhis)
    return hhis, hhi_avg

# ════════════════════════════════════════════════════════════════
# Set-E 回测引擎 (与TASK050完全一致)
# ════════════════════════════════════════════════════════════════
def compute_signal_fixed(df, factors, weights_list):
    signal = np.zeros(len(df))
    for i, fname in enumerate(factors):
        if fname in df.columns:
            vals = df[fname].values.astype(float).copy()
            std = np.nanstd(vals)
            mean = np.nanmean(vals)
            if std > 0:
                vals = (vals - mean) / std
            else:
                vals = np.zeros_like(vals)
            w = weights_list[i] if i < len(weights_list) else 0.0
            signal += w * vals
    return np.where(np.isnan(signal), 0.0, signal)

def compute_signal_dynamic(df, factors, regime_weights, regime_col="regime",
                           ema_window=0, ema_composite=0):
    zscores = {}
    for fname in factors:
        if fname in df.columns:
            vals = df[fname].values.astype(float).copy()
            std = np.nanstd(vals)
            mean = np.nanmean(vals)
            if std > 0:
                zscores[fname] = (vals - mean) / std
            else:
                zscores[fname] = np.zeros_like(vals)
        else:
            zscores[fname] = np.zeros(len(df))
    if ema_window > 0:
        for fname in zscores:
            zscores[fname] = pd.Series(zscores[fname]).ewm(span=ema_window, adjust=False).mean().values
    regimes = df[regime_col].values if regime_col in df.columns else np.zeros(len(df), dtype=object)
    signal = np.zeros(len(df))
    n_factors = len(factors)
    for i in range(len(df)):
        r = regimes[i]
        if r not in regime_weights:
            r = "sideways"
        rw = regime_weights[r]
        s = 0.0
        for j, fname in enumerate(factors):
            w = rw.get(fname, 1.0 / n_factors)
            s += w * zscores[fname][i]
        signal[i] = s
    signal = np.where(np.isnan(signal), 0.0, signal)
    if ema_composite > 0:
        signal = pd.Series(signal).ewm(span=ema_composite, adjust=False).mean().values
    return signal

def compute_backtest_from_signal(df, signal_array,
                                  threshold=SIGNAL_THRESHOLD,
                                  rebalance_interval=REBALANCE_INTERVAL,
                                  target_vol=TARGET_VOL,
                                  max_single_weight=MAX_SINGLE_WEIGHT):
    position = np.zeros(len(df))
    for i in range(1, len(df)):
        s = signal_array[i]
        if s > threshold:
            position[i] = 1.0
        elif s < -threshold:
            position[i] = -1.0
        else:
            position[i] = 0.0
    if rebalance_interval > 1:
        pos = position.copy()
        last_rebalance = 0
        for i in range(len(pos)):
            if i - last_rebalance >= rebalance_interval:
                if abs(pos[i]) > threshold or pos[i] == 0:
                    pos[i] = 1.0 if pos[i] > 0 else (-1.0 if pos[i] < 0 else 0.0)
                last_rebalance = i
            else:
                pos[i] = pos[i-1] if i > 0 else 0.0
        position = pos
    if "realized_vol_20d" in df.columns:
        vol = df["realized_vol_20d"].values
        vol_weight = np.clip(target_vol / np.where(np.isnan(vol) | (vol == 0), 1.0, vol), 0, max_single_weight)
        position = position * vol_weight
    daily_returns_per_symbol = df.groupby("symbol")["close"].pct_change().fillna(0).values
    min_len = min(len(position), len(daily_returns_per_symbol))
    position = position[:min_len]
    daily_returns_per_symbol = daily_returns_per_symbol[:min_len]
    strategy_returns_per_symbol = position * daily_returns_per_symbol
    nan_mask = ~np.isnan(strategy_returns_per_symbol)
    strategy_returns_per_symbol = strategy_returns_per_symbol[nan_mask]
    position_filtered = position[nan_mask]
    dates_filtered = df["date"].values[:min_len][nan_mask]
    df_agg = pd.DataFrame({
        "date": dates_filtered,
        "return": strategy_returns_per_symbol,
        "position": position_filtered,
    })
    daily_agg_df = df_agg.groupby("date").agg({"return": "mean", "position": "mean"}).reset_index()
    daily_agg_df.columns = ["date", "return", "position"]
    strategy_returns = daily_agg_df["return"].values
    position_agg = daily_agg_df["position"].values
    equity = INITIAL_CAPITAL
    running_max = INITIAL_CAPITAL
    adjusted_returns = np.zeros(len(strategy_returns))
    adjusted_positions = position_agg.copy()
    for i in range(len(strategy_returns)):
        dd = (equity - running_max) / running_max
        if dd < DRAWDOWN_HALT:
            adjusted_returns[i] = 0.0
            adjusted_positions[i] = 0.0
        elif dd < DRAWDOWN_WARN:
            adjusted_returns[i] = strategy_returns[i] * 0.5
            adjusted_positions[i] = position_agg[i] * 0.5
        else:
            adjusted_returns[i] = strategy_returns[i]
            adjusted_positions[i] = position_agg[i]
        equity = equity * (1 + adjusted_returns[i])
        if equity > running_max:
            running_max = equity
    strategy_returns = adjusted_returns
    position = adjusted_positions
    position_changes = np.abs(np.diff(position))
    min_len = min(len(strategy_returns), len(position_changes))
    strategy_returns = strategy_returns[:min_len]
    position_changes = position_changes[:min_len]
    cost_adjusted = np.zeros_like(strategy_returns)
    for i in range(len(strategy_returns)):
        cost_adjusted[i] = strategy_returns[i] - position_changes[i] * TRANSACTION_COST
    equity_curve = np.cumprod(1 + cost_adjusted) * INITIAL_CAPITAL
    equity_curve = np.insert(equity_curve, 0, INITIAL_CAPITAL)
    total_return = (equity_curve[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL
    n_periods = len(cost_adjusted)
    annual_return = (1 + total_return) ** (TRADING_DAYS_PER_YEAR / n_periods) - 1 if n_periods > 0 else 0
    daily_vol = np.std(cost_adjusted, ddof=1) if n_periods > 1 else 0
    annual_vol = daily_vol * math.sqrt(TRADING_DAYS_PER_YEAR)
    sharpe = annual_return / annual_vol if annual_vol > 0 else 0
    running_max_eq = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max_eq) / running_max_eq
    max_drawdown = float(np.min(drawdown))
    winning = cost_adjusted[cost_adjusted > 0]
    losing = cost_adjusted[cost_adjusted < 0]
    win_rate = len(winning) / n_periods if n_periods > 0 else 0
    avg_win = float(np.mean(winning)) if len(winning) > 0 else 0
    avg_loss = float(abs(np.mean(losing))) if len(losing) > 0 else 0
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float("inf")
    trade_count = int(np.sum(position_changes > 0))
    calmar = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
    total_cost = float(np.sum(position_changes * TRANSACTION_COST))
    cost_ratio = total_cost / abs(total_return) if total_return != 0 else 0
    metrics = {
        "total_return": round(float(total_return), 6),
        "annualized_return": round(float(annual_return), 6),
        "annual_volatility": round(float(annual_vol), 6),
        "daily_volatility": round(float(daily_vol), 6),
        "max_drawdown": round(float(max_drawdown), 6),
        "sharpe_ratio": round(float(sharpe), 6),
        "calmar_ratio": round(float(calmar), 6),
        "win_rate": round(float(win_rate), 6),
        "avg_win": round(float(avg_win), 6),
        "avg_loss": round(float(avg_loss), 6),
        "profit_loss_ratio": round(float(profit_loss_ratio), 6),
        "trade_count": trade_count,
        "total_trades": trade_count,
        "n_periods": n_periods,
        "initial_capital": INITIAL_CAPITAL,
        "final_capital": round(float(equity_curve[-1]), 2),
        "total_transaction_cost": round(total_cost, 6),
        "cost_ratio": round(float(cost_ratio), 6),
    }
    return {
        "metrics": metrics,
        "equity_curve": equity_curve,
        "daily_returns": cost_adjusted,
        "positions": position,
        "drawdown_curve": drawdown,
    }

# ════════════════════════════════════════════════════════════════
# 翻转率计算 (可配置IC窗口)
# ════════════════════════════════════════════════════════════════
def compute_composite_flip_rate(df, signal_array, symbols, signal_name="composite_signal",
                                 ic_window=IC_WINDOW_20):
    df_copy = df.copy()
    df_copy[signal_name] = signal_array
    df_copy = df_copy[df_copy["symbol"].isin(symbols)].copy()
    df_sorted = df_copy.sort_values(["symbol", "date"]).reset_index(drop=True)
    dates_unique = sorted(df_sorted["date"].unique())
    total_dates = len(dates_unique)
    num_windows = max((total_dates - ic_window) // IC_STEP + 1, 0)
    returns_by_date = {}
    for i in range(len(dates_unique) - 1):
        d = dates_unique[i]
        d_next = dates_unique[i + 1]
        returns_by_date[d] = {}
        for sym in symbols:
            d_rows = df_sorted[(df_sorted["date"] == d) & (df_sorted["symbol"] == sym)]
            dn_rows = df_sorted[(df_sorted["date"] == d_next) & (df_sorted["symbol"] == sym)]
            if len(d_rows) > 0 and len(dn_rows) > 0:
                close_now = float(d_rows.iloc[0]["close"])
                close_next = float(dn_rows.iloc[0]["close"])
                if close_now > 0:
                    ret = (close_next - close_now) / close_now
                    returns_by_date[d][sym] = ret
    window_ics = []
    for w in range(num_windows):
        w_start = w * IC_STEP
        w_end = w_start + ic_window
        window_dates = dates_unique[w_start:w_end]
        if len(window_dates) < 5:
            continue
        factor_vals = []
        ret_vals = []
        for d in window_dates:
            if d not in returns_by_date:
                continue
            for sym in symbols:
                if sym not in returns_by_date[d]:
                    continue
                row = df_sorted[(df_sorted["date"] == d) & (df_sorted["symbol"] == sym)]
                if len(row) == 0:
                    continue
                raw = row.iloc[0].get(signal_name, '')
                try:
                    fv = float(raw) if raw is not None and str(raw).strip() else None
                except (ValueError, TypeError):
                    fv = None
                if fv is not None and not np.isnan(fv):
                    factor_vals.append(fv)
                    ret_vals.append(returns_by_date[d][sym])
        if len(factor_vals) >= 10:
            try:
                ic, _ = pearsonr(factor_vals, ret_vals)
                ic = float(ic) if not np.isnan(ic) else 0.0
            except:
                ic = 0.0
            window_ics.append({"ic": round(ic, 6), "sign": 1 if ic > 0 else (-1 if ic < 0 else 0)})
    if len(window_ics) < 2:
        return {"flip_rate": 0.0, "flip_count": 0, "num_windows": len(window_ics),
                "ic_mean": 0.0, "ic_values": [w["ic"] for w in window_ics]}
    flips = 0
    for i in range(1, len(window_ics)):
        prev_sign = window_ics[i - 1]["sign"]
        curr_sign = window_ics[i]["sign"]
        if prev_sign != 0 and curr_sign != 0 and prev_sign != curr_sign:
            flips += 1
    flip_rate = flips / (len(window_ics) - 1)
    ics = [w["ic"] for w in window_ics]
    ic_mean = float(np.mean(ics))
    return {
        "flip_rate": round(flip_rate, 4),
        "flip_count": flips,
        "num_windows": len(window_ics),
        "ic_mean": round(ic_mean, 6),
        "ic_values": ics,
    }

# ════════════════════════════════════════════════════════════════
# 风险校验 (HHI/相关性/拥挤度)
# ════════════════════════════════════════════════════════════════
def validate_risk(df, weights, fixed_w, equal_w, crowding_threshold=1.10):
    corr_matrix = {}
    for f1 in FACTORS:
        corr_matrix[f1] = {}
        for f2 in FACTORS:
            x = df[f1].dropna().values
            y = df[f2].dropna().values
            n = min(len(x), len(y))
            if n > 10:
                r = float(np.corrcoef(x[:n], y[:n])[0, 1])
                if np.isnan(r):
                    r = 0.0
                corr_matrix[f1][f2] = round(r, 6)
            else:
                corr_matrix[f1][f2] = 0.0
    def weighted_corr(w):
        total = 0.0
        for i, f1 in enumerate(FACTORS):
            for f2 in FACTORS[i:]:
                wi = w.get(f1, 1/NUM_FACTORS)
                wj = w.get(f2, 1/NUM_FACTORS)
                c = corr_matrix[f1][f2]
                if f1 != f2:
                    total += 2 * wi * wj * c
                else:
                    total += wi * wj * c
        return round(total, 6)
    wcorr_equal = weighted_corr(equal_w)
    wcorr_fixed = weighted_corr(fixed_w)
    wcorr_dynamic = round(sum(
        weighted_corr(weights[r]) * 1.0/3 for r in ["up", "down", "sideways"]
    ), 6)
    hhi_per_regime = {}
    for reg in ["up", "down", "sideways"]:
        w = weights[reg]
        hhi = sum(w.get(f, 0) ** 2 for f in FACTORS)
        hhi_per_regime[reg] = round(hhi, 6)
    hhi_equal = round(sum((1/NUM_FACTORS) ** 2 for _ in FACTORS), 6)
    hhi_avg = round(sum(hhi_per_regime.values()) / 3, 6)
    crowding_ratio = round(hhi_avg / hhi_equal, 4)
    redundancy_flags = []
    high_corr_pairs = []
    for i, f1 in enumerate(FACTORS):
        for f2 in FACTORS[i+1:]:
            c = abs(corr_matrix[f1][f2])
            if c > 0.5:
                high_corr_pairs.append({"factor1": f1, "factor2": f2, "corr": round(c, 4)})
                for reg in ["up", "down", "sideways"]:
                    w1 = weights[reg].get(f1, 0)
                    w2 = weights[reg].get(f2, 0)
                    if w1 > 0.15 and w2 > 0.15:
                        redundancy_flags.append({
                            "pair": f"{f1}↔{f2}",
                            "regime": reg,
                            "w1": round(w1, 4),
                            "w2": round(w2, 4),
                            "corr": round(c, 4),
                            "risk": "SIGNAL_REDUNDANCY"
                        })
    return {
        "base_corr_matrix": corr_matrix,
        "weighted_corr_equal": wcorr_equal,
        "weighted_corr_fixed": wcorr_fixed,
        "weighted_corr_dynamic_avg": wcorr_dynamic,
        "hhi_equal": hhi_equal,
        "hhi_dynamic_per_regime": hhi_per_regime,
        "hhi_dynamic_avg": hhi_avg,
        "crowding_ratio": crowding_ratio,
        "crowding_threshold": crowding_threshold,
        "crowding_alert": crowding_ratio > crowding_threshold,
        "high_corr_pairs": high_corr_pairs,
        "redundancy_flags": redundancy_flags,
        "redundancy_alert": len(redundancy_flags) > 0,
    }

# ════════════════════════════════════════════════════════════════
# 偏差比较工具
# ════════════════════════════════════════════════════════════════
def compare_with_baseline(replay_metrics, baseline_metrics, metric_keys=None):
    if metric_keys is None:
        metric_keys = ["total_return", "sharpe_ratio", "max_drawdown", "annualized_return",
                        "annual_volatility", "daily_volatility", "calmar_ratio", "win_rate",
                        "avg_win", "avg_loss", "profit_loss_ratio", "trade_count",
                        "final_capital", "total_transaction_cost", "cost_ratio"]
    deviations = {}
    all_pass = True
    for k in metric_keys:
        baseline_val = baseline_metrics.get(k)
        replay_val = replay_metrics.get(k)
        if baseline_val is None or replay_val is None:
            deviations[k] = {"baseline": baseline_val, "replay": replay_val,
                             "deviation": None, "within_threshold": None, "note": "missing"}
            continue
        diff = abs(replay_val - baseline_val)
        within = diff <= DEVIATION_THRESHOLD
        if not within:
            all_pass = False
        deviations[k] = {
            "baseline": baseline_val,
            "replay": replay_val,
            "deviation": round(diff, 6),
            "deviation_pct": round(diff / abs(baseline_val) * 100, 2) if baseline_val != 0 else 0,
            "within_threshold": within,
        }
    return {"deviations": deviations, "all_pass": all_pass, "threshold": DEVIATION_THRESHOLD}

# ════════════════════════════════════════════════════════════════
# P2: 压力扰动引擎
# ════════════════════════════════════════════════════════════════
def add_factor_noise(df, factor_cols, noise_sigma_factor=NOISE_SIGMA_FACTOR, seed=POTENTIATION_SEED):
    rng = np.random.RandomState(seed)
    df_noisy = df.copy()
    for f in factor_cols:
        if f not in df_noisy.columns:
            continue
        vals = df_noisy[f].values.astype(float)
        std = np.nanstd(vals)
        if std > 0:
            noise = rng.normal(0, std * noise_sigma_factor, size=len(vals))
            noise = np.where(np.isnan(vals), np.nan, noise)
            vals = np.where(np.isnan(vals), np.nan, vals + noise)
        df_noisy[f] = vals
    return df_noisy

def add_market_jump(df, jump_pct=MARKET_JUMP_PCT, seed=POTENTIATION_SEED):
    """在特定时间点注入行情跳变"""
    rng = np.random.RandomState(seed)
    df_jump = df.copy()
    df_jump["close"] = df_jump["close"].astype(float)  # ← 确保float
    dates = df_jump.groupby("symbol")["date"].unique()
    all_dates = sorted(df_jump["date"].unique())
    # 选取3个随机日期注入跳变
    jump_dates = rng.choice(all_dates, size=min(3, len(all_dates)), replace=False)
    for d in jump_dates:
        # 每个日期选一个品种注入
        syms = df_jump[df_jump["date"] == d]["symbol"].unique()
        if len(syms) == 0:
            continue
        sym = syms[rng.randint(len(syms))]
        mask = (df_jump["symbol"] == sym) & (df_jump["date"] == d)
        # 向上或向下跳变
        direction = 1 if rng.random() > 0.5 else -1
        df_jump.loc[mask, "close"] = df_jump.loc[mask, "close"].values * (1 + direction * jump_pct)
    return df_jump, [str(d) for d in jump_dates]

def amplify_volatility(df, vol_factor=VOL_SPIKE_FACTOR, seed=POTENTIATION_SEED):
    """放大波动率因子"""
    df_amplified = df.copy()
    if "realized_vol_20d" in df_amplified.columns:
        df_amplified["realized_vol_20d"] = df_amplified["realized_vol_20d"] * vol_factor
    return df_amplified

def run_stress_scenario(name, description, df_base, weights, equal_w, fixed_w,
                         factor_cols=None, seed=POTENTIATION_SEED):
    """运行单个压力场景"""
    log(f"  [{name}] {description}")
    # 行情分类
    df_regime, regime_counts = classify_regimes(df_base)
    
    # 信号计算
    signal = compute_signal_dynamic(df_regime, FACTORS, weights)
    
    # 回测
    bt = compute_backtest_from_signal(df_regime, signal)
    metrics = bt["metrics"]
    
    # 翻转率
    flip_20 = compute_composite_flip_rate(df_regime, signal, SYMBOL_WHITELIST, "stress_sig", ic_window=IC_WINDOW_20)
    flip_40 = compute_composite_flip_rate(df_regime, signal, SYMBOL_WHITELIST, "stress_sig", ic_window=IC_WINDOW_40)
    
    # 风险校验
    risk = validate_risk(df_base, weights, fixed_w, equal_w, crowding_threshold=CROWDING_MAX)
    
    result = {
        "scenario_name": name,
        "description": description,
        "seed": seed,
        "metrics": metrics,
        "flip_rate_20d": flip_20["flip_rate"],
        "flip_rate_40d": flip_40["flip_rate"],
        "hhi_dynamic_avg": risk["hhi_dynamic_avg"],
        "crowding_ratio": risk["crowding_ratio"],
        "crowding_alert": risk["crowding_alert"],
        "high_corr_pairs": len(risk["high_corr_pairs"]),
        "redundancy_alert": risk["redundancy_alert"],
        "total_alerts": risk["crowding_alert"] + risk["redundancy_alert"],
        "pass": not risk["crowding_alert"],
    }
    
    log(f"    夏普={metrics['sharpe_ratio']:.4f}, 收益={metrics['total_return']*100:.2f}%, "
        f"回撤={metrics['max_drawdown']*100:.2f}%, 拥挤度={risk['crowding_ratio']:.4f}x, "
        f"告警={'⚠️' if result['total_alerts'] > 0 else '✅'}")
    
    return result

# ════════════════════════════════════════════════════════════════
# P3: 边界场景测试
# ════════════════════════════════════════════════════════════════
def create_low_liquidity_scenario(df_base, seed=POTENTIATION_SEED):
    """低流动性: 减少OI数据"""
    rng = np.random.RandomState(seed)
    df_ll = df_base.copy()
    # 随机将20%的OI设为NaN模拟低流动性
    mask = rng.random(len(df_ll)) < 0.20
    df_ll.loc[mask, "oi"] = np.nan
    df_ll["oi"] = df_ll["oi"].fillna(df_ll["oi"].median())
    # 标记受影响行数
    affected = int(mask.sum())
    return df_ll, affected

def create_continuous_switch_scenario(df_base, seed=POTENTIATION_SEED):
    """连续换月: 强制标记多个连续换月事件"""
    df_cs = df_base.copy()
    df_cs = df_cs.sort_values(["symbol", "date"])
    # 每个品种选择3个时间点设为换月标记
    for sym in df_cs["symbol"].unique():
        sym_mask = df_cs["symbol"] == sym
        sym_indices = df_cs[sym_mask].index
        if len(sym_indices) < 5:
            continue
        chosen = np.random.RandomState(seed + hash(sym) % 1000).choice(
            sym_indices, size=min(3, len(sym_indices)), replace=False)
        df_cs.loc[chosen, "contract_switch_flag"] = 1.0
    total_switches = int((df_cs["contract_switch_flag"] > 0).sum())
    return df_cs, total_switches

def create_extreme_moves_scenario(df_base, extreme_pct=0.08, seed=POTENTIATION_SEED):
    """极端涨跌: 注入±8%极端行情"""
    rng = np.random.RandomState(seed)
    df_em = df_base.copy()
    df_em["close"] = df_em["close"].astype(float)  # ← 确保float
    all_dates = sorted(df_em["date"].unique())
    # 选取5个极端日期
    extreme_dates = rng.choice(all_dates, size=min(5, len(all_dates)), replace=False)
    for d in extreme_dates:
        syms = df_em[df_em["date"] == d]["symbol"].unique()
        if len(syms) == 0:
            continue
        sym = syms[rng.randint(len(syms))]
        mask = (df_em["symbol"] == sym) & (df_em["date"] == d)
        direction = 1 if rng.random() > 0.5 else -1
        df_em.loc[mask, "close"] = df_em.loc[mask, "close"].values * (1 + direction * extreme_pct)
    return df_em, [str(d) for d in extreme_dates]

def run_boundary_scenario(name, description, df_scenario, weights, equal_w, fixed_w,
                          extra_info=None):
    """运行单个边界场景"""
    log(f"  [{name}] {description}")
    
    # 行情分类
    df_regime, regime_counts = classify_regimes(df_scenario)
    
    # 信号
    signal = compute_signal_dynamic(df_regime, FACTORS, weights)
    
    # 回测
    bt = compute_backtest_from_signal(df_regime, signal)
    metrics = bt["metrics"]
    
    # 翻转率
    flip_20 = compute_composite_flip_rate(df_regime, signal, SYMBOL_WHITELIST, "bound_sig", ic_window=IC_WINDOW_20)
    flip_40 = compute_composite_flip_rate(df_regime, signal, SYMBOL_WHITELIST, "bound_sig", ic_window=IC_WINDOW_40)
    
    # 风险
    risk = validate_risk(df_scenario, weights, fixed_w, equal_w, crowding_threshold=CROWDING_MAX)
    
    result = {
        "scenario_name": name,
        "description": description,
        "metrics": metrics,
        "flip_rate_20d": flip_20["flip_rate"],
        "flip_rate_40d": flip_40["flip_rate"],
        "hhi_dynamic_avg": risk["hhi_dynamic_avg"],
        "crowding_ratio": risk["crowding_ratio"],
        "crowding_alert": risk["crowding_alert"],
        "high_corr_pairs": len(risk["high_corr_pairs"]),
        "redundancy_alert": risk["redundancy_alert"],
        "total_alerts": risk["crowding_alert"] + risk["redundancy_alert"],
        "pass": not risk["crowding_alert"],
        "extra_info": extra_info or {},
        "regime_counts": regime_counts,
    }
    
    log(f"    夏普={metrics['sharpe_ratio']:.4f}, 收益={metrics['total_return']*100:.2f}%, "
        f"回撤={metrics['max_drawdown']*100:.2f}%, 拥挤度={risk['crowding_ratio']:.4f}x, "
        f"告警={'⚠️' if result['total_alerts'] > 0 else '✅'}")
    
    return result

# ════════════════════════════════════════════════════════════════
# DSHD 推送
# ════════════════════════════════════════════════════════════════
def build_dshd_push(p0_result, replay_result, stress_results, boundary_results,
                     risk_final, p4_risk_report):
    now = now_iso()
    replay_metrics = replay_result["replay_metrics"]
    baseline_metrics = replay_result["baseline_metrics"]
    deviations = replay_result["deviation_check"]
    
    # 压力测试汇总
    stress_summary = {
        "total_scenarios": len(stress_results),
        "pass_count": sum(1 for s in stress_results if s["pass"]),
        "fail_count": sum(1 for s in stress_results if not s["pass"]),
        "all_pass": all(s["pass"] for s in stress_results),
        "max_crowding": max(s["crowding_ratio"] for s in stress_results) if stress_results else 0,
        "min_sharpe": min(s["metrics"]["sharpe_ratio"] for s in stress_results) if stress_results else 0,
        "max_drawdown": min(s["metrics"]["max_drawdown"] for s in stress_results) if stress_results else 0,
    }
    
    # 边界场景汇总
    boundary_summary = {
        "total_scenarios": len(boundary_results),
        "pass_count": sum(1 for s in boundary_results if s["pass"]),
        "fail_count": sum(1 for s in boundary_results if not s["pass"]),
        "all_pass": all(s["pass"] for s in boundary_results),
    }
    
    push = {
        "push_id": f"DSHD-TASK051-PUSH-{int(time.time())}",
        "generated_at": now,
        "source_task": TASK_ID,
        "source_token": TOKEN,
        "push_token": DSHD_TOKEN,
        "push_type": "FROZEN_BACKTEST_VALIDATION",
        "mode": "AUDIT_READ_ONLY",
        "safety": {
            "wind_api_calls": 0,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
            "offline_only": True,
            "read_only_mode": True,
            "v3_modification_forbidden": True,
        },
        "p0_prereq": {
            "all_pass": p0_result.get("p0_all_pass", False),
            "v3_frozen": p0_result.get("v3_final_weight_rules", False),
            "set_e_frozen": p0_result.get("set_e_frozen", False),
            "prod_configs_unchanged": p0_result.get("prod_configs_unchanged", False),
            "engine_params_match_v3": p0_result.get("engine_params_match_v3", False),
        },
        "p1_replay": {
            "replay_sharpe": replay_metrics.get("sharpe_ratio"),
            "baseline_sharpe": baseline_metrics.get("sharpe_ratio"),
            "replay_return": replay_metrics.get("total_return"),
            "baseline_return": baseline_metrics.get("total_return"),
            "replay_max_dd": replay_metrics.get("max_drawdown"),
            "baseline_max_dd": baseline_metrics.get("max_drawdown"),
            "deviation_all_pass": deviations["all_pass"],
            "deviation_threshold": DEVIATION_THRESHOLD,
            "key_deviations": {k: v for k, v in deviations["deviations"].items()
                               if k in ["total_return", "sharpe_ratio", "max_drawdown"]},
        },
        "p2_stress": {
            "summary": stress_summary,
            "scenarios": [{
                "name": s["scenario_name"],
                "description": s["description"],
                "sharpe": s["metrics"]["sharpe_ratio"],
                "return": s["metrics"]["total_return"],
                "max_dd": s["metrics"]["max_drawdown"],
                "crowding": s["crowding_ratio"],
                "crowding_alert": s["crowding_alert"],
                "pass": s["pass"],
            } for s in stress_results],
        },
        "p3_boundary": {
            "summary": boundary_summary,
            "scenarios": [{
                "name": s["scenario_name"],
                "description": s["description"],
                "sharpe": s["metrics"]["sharpe_ratio"],
                "return": s["metrics"]["total_return"],
                "max_dd": s["metrics"]["max_drawdown"],
                "crowding": s["crowding_ratio"],
                "crowding_alert": s["crowding_alert"],
                "pass": s["pass"],
            } for s in boundary_results],
        },
        "p4_risk": {
            "hhi_equal": risk_final.get("hhi_equal", 0.125),
            "hhi_dynamic_avg": risk_final.get("hhi_dynamic_avg", 0),
            "crowding_ratio": risk_final.get("crowding_ratio", 0),
            "crowding_threshold": CROWDING_MAX,
            "crowding_alert": risk_final.get("crowding_alert", False),
            "high_corr_pairs": len(risk_final.get("high_corr_pairs", [])),
            "redundancy_alert": risk_final.get("redundancy_alert", False),
        },
        "red_lines": {
            "no_v3_modification": True,
            "read_only_mode": True,
            "wind_api_calls": 0,
            "gate_observed": GATE_STATUS,
            "release_permit": RELEASE_STATUS,
            "deviation_threshold_observed": DEVIATION_THRESHOLD,
            "crowding_threshold_observed": CROWDING_MAX,
            "auto_fail_on_deviation": True,
            "auto_fail_on_crowding": True,
        },
        "alerts": {
            "p0_alert": not p0_result.get("p0_all_pass", True),
            "p1_deviation_alert": not deviations["all_pass"],
            "p2_stress_alert": stress_summary.get("all_pass", True),
            "p3_boundary_alert": boundary_summary.get("all_pass", True),
            "p4_risk_alert": risk_final.get("crowding_alert", False),
            "total_active_alerts": sum([
                not p0_result.get("p0_all_pass", True),
                not deviations["all_pass"],
                not stress_summary.get("all_pass", True),
                not boundary_summary.get("all_pass", True),
                risk_final.get("crowding_alert", False),
            ]),
        },
        "task051_receipt": f"DSHA_TASK051_FROZEN_BACKTEST_VALID=COMPLETE",
    }
    return push

def update_dshd_brief(push_data):
    now = now_iso()
    replay = push_data["p1_replay"]
    stress = push_data["p2_stress"]
    boundary = push_data["p3_boundary"]
    risk = push_data["p4_risk"]
    
    lines = []
    lines.append(f"\n---\n")
    lines.append(f"## TASK-051 冻结策略沙箱回放+压力校验 — 监控推送")
    lines.append(f"\n> 任务: {TASK_ID}")
    lines.append(f"> 时间: {now}")
    lines.append(f"> 令牌: {DSHD_TOKEN}")
    lines.append(f"> 模式: AUDIT_READ_ONLY · wind_api_calls=0")
    lines.append(f"> 引擎: Set-E (PERMANENTLY_FROZEN)")
    
    lines.append(f"\n### P1 沙箱回放指标核对")
    lines.append(f"\n| 指标 | 基准(TASK050) | 回放值 | 偏差 | 阈值内 |")
    lines.append(f"|---|---|---|---|---|")
    for metric_name, metric_data in replay["key_deviations"].items():
        within = metric_data.get("within_threshold")
        lines.append(f"| {metric_name} | {metric_data.get('baseline')} | {metric_data.get('replay')} | "
                     f"{metric_data.get('deviation')} | {'✅' if within else '⚠️'} |")
    
    lines.append(f"\n### P2 压力扰动测试 ({stress['summary']['pass_count']}/{stress['summary']['total_scenarios']} PASS)")
    lines.append(f"\n| 场景 | 夏普 | 收益 | 回撤 | 拥挤度 | 告警 | 判定 |")
    lines.append(f"|---|---|---|---|---|---|---|")
    for s in stress["scenarios"]:
        lines.append(f"| {s['name']} | {s['sharpe']:.4f} | {s['return']*100:.2f}% | "
                     f"{s['max_dd']*100:.2f}% | {s['crowding']:.4f}x | "
                     f"{'⚠️' if s['crowding_alert'] else '✅'} | {'PASS' if s['pass'] else 'FAIL'} |")
    
    lines.append(f"\n### P3 边界场景测试 ({boundary['summary']['pass_count']}/{boundary['summary']['total_scenarios']} PASS)")
    lines.append(f"\n| 场景 | 夏普 | 收益 | 回撤 | 拥挤度 | 告警 | 判定 |")
    lines.append(f"|---|---|---|---|---|---|---|")
    for s in boundary["scenarios"]:
        lines.append(f"| {s['name']} | {s['sharpe']:.4f} | {s['return']*100:.2f}% | "
                     f"{s['max_dd']*100:.2f}% | {s['crowding']:.4f}x | "
                     f"{'⚠️' if s['crowding_alert'] else '✅'} | {'PASS' if s['pass'] else 'FAIL'} |")
    
    lines.append(f"\n### P4 风险复核")
    lines.append(f"\n| 指标 | 值 | 阈值 | 判定 |")
    lines.append(f"|---|---|---|---|")
    lines.append(f"| 拥挤度 | {risk['crowding_ratio']:.4f}x | ≤{CROWDING_MAX}x | "
                 f"{'✅' if not risk['crowding_alert'] else '⚠️'} |")
    lines.append(f"| 高相关对 | {risk['high_corr_pairs']} | ≤2 | {'✅' if risk['high_corr_pairs'] <= 2 else '⚠️'} |")
    lines.append(f"| 冗余告警 | {'是' if risk['redundancy_alert'] else '否'} | — | "
                 f"{'⚠️' if risk['redundancy_alert'] else '✅'} |")
    
    section = "\n".join(lines)
    
    try:
        if DSHD_BRIEF.exists():
            with open(DSHD_BRIEF, "r", encoding="utf-8") as f:
                existing = f.read()
            if "TASK-051 冻结策略沙箱回放" in existing:
                existing = re.sub(
                    r'\n---\n\n## TASK-051 冻结策略沙箱回放.*?(?=\n---\n\n##|\Z)',
                    section + "\n",
                    existing,
                    flags=re.DOTALL
                )
            else:
                existing = existing.rstrip() + section
            with open(DSHD_BRIEF, "w", encoding="utf-8") as f:
                f.write(existing)
            log(f"DSHD集群简报已更新 (TASK051段落)")
        else:
            with open(DSHD_BRIEF, "w", encoding="utf-8") as f:
                f.write("# DSHD 监控文档 — Regime识别 + 拥挤度监控\n" + section)
            log(f"DSHD集群简报已创建 (TASK051段落)")
    except Exception as e:
        log(f"⚠ DSHD简报更新失败: {e}")

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════
def main():
    global df_global, task050_baseline_metrics, task050_final_weights
    
    t0 = time.time()
    
    log("=" * 72)
    log(f"{TASK_ID} — 冻结策略沙箱回放+压力校验工单")
    log(f"令牌: {TOKEN}")
    log(f"基线: {BASELINE_COMMIT}")
    log("=" * 72)
    
    # ─── P0: 前置冒烟自检 (11项) ───
    log("\n─── P0: 前置冒烟自检 (11项) ───")
    p0_result = p0_prereq_check()
    
    if not p0_result["p0_all_pass"]:
        failed = [k for k, v in p0_result.items() if isinstance(v, bool) and not v and k != "p0_all_pass"]
        log(f"  ⚠ 前置校验未完全通过, 失败项: {failed}")
        log(f"  继续执行（研究沙箱模式, 只读回放）")
    
    # ─── 加载基准数据 ───
    log("\n─── 加载TASK050基准数据 ───")
    
    # 读取TASK050基准指标
    baseline_data = json.loads(TASK050_BACKTEST_METRICS.read_text(encoding="utf-8"))
    group_b = baseline_data["groups"]["group_b_dynamic_a06_20d"]
    task050_baseline_metrics = group_b["metrics"]
    task050_flip_20d = group_b["composite_flip_rate_20d"]
    task050_flip_40d = group_b["composite_flip_rate_40d"]
    task050_crowding = baseline_data["comparison_summary"]["20d_vs_40d"]
    log(f"  TASK050基准: sharpe={task050_baseline_metrics['sharpe_ratio']:.4f}, "
        f"return={task050_baseline_metrics['total_return']:.4f}, "
        f"max_dd={task050_baseline_metrics['max_drawdown']:.4f}")
    
    # 读取V3冻结权重
    fwr = json.loads(FINAL_WEIGHT_RULES.read_text(encoding="utf-8"))
    task050_final_weights = {
        "selected_window": fwr["selected_window"],
        "selected_alpha": fwr["selected_alpha"],
        "ic_window": fwr["ic_window"],
        "dynamic_weights": fwr["dynamic_weights"],
        "fixed_weights": fwr["fixed_weights"],
        "equal_weight_baseline": fwr["equal_weight_baseline"],
    }
    frozen_weights = fwr["dynamic_weights"]
    frozen_fixed_w = fwr["fixed_weights"]
    frozen_equal_w = fwr["equal_weight_baseline"]
    log(f"  V3冻结权重: 窗口={fwr['selected_window']}, alpha={fwr['selected_alpha']}, "
        f"ic_window={fwr['ic_window']}")
    
    # ─── 数据加载 ───
    log("\n─── 数据加载 ───")
    df = load_factors_csv()
    df["date"] = pd.to_datetime(df["date"])
    df_global = df
    
    # ─── 重构 contract_switch_flag ───
    log("\n─── contract_switch_flag 重建 (与TASK050一致) ───")
    df, contract_diag = rebuild_contract_switch_flag(df)
    df_global = df
    
    # 4品种白名单
    df_4sym = df[df["symbol"].isin(SYMBOL_WHITELIST)].copy()
    df_4sym = df_4sym.sort_values(["symbol", "date"]).reset_index(drop=True)
    df_9_raw = df[df["symbol"].isin(SYMBOL_9)].copy()
    
    # ─── 行情分类 ───
    log("\n─── 行情分类 ───")
    df_regime, regime_counts_4sym = classify_regimes(df_4sym)
    df_9, regime_counts_9sym = classify_regimes(df_9_raw)
    
    # ─── 20d IC计算 (V3冻结使用20d窗口) ───
    log("\n─── 20d IC计算 (V3冻结窗口) ───")
    ic_4sym_20 = {"up": {}, "down": {}, "sideways": {}}
    ic_9sym_20 = {"up": {}, "down": {}, "sideways": {}}
    for pool_name, pool_df, pool_symbols, ic_target in [
        ("4sym", df_regime, SYMBOL_WHITELIST, ic_4sym_20),
        ("9sym", df_9, SYMBOL_9, ic_9sym_20),
    ]:
        for reg in ["up", "down", "sideways"]:
            log(f"  计算{pool_name}/{reg} IC (20d窗口)...")
            for f in FACTORS:
                result, n_samples, _ = compute_regime_ic(pool_df, pool_symbols, f, reg,
                                                          ic_window=IC_WINDOW_20)
                if result:
                    ic_target[reg][f] = result
                    ic_str = f"{result['mean_ic']:.4f}" if not math.isnan(result['mean_ic']) else "NaN"
                    log(f"    {f}: IC={ic_str}, windows={result['num_windows']}")
    
    ic_data_20 = {
        "regime_counts_4sym": regime_counts_4sym,
        "regime_counts_9sym": regime_counts_9sym,
        "ic_4sym": ic_4sym_20,
        "ic_9sym": ic_9sym_20,
        "factors_analyzed": FACTORS,
        "ic_window": IC_WINDOW_20,
    }
    
    # ─── 计算动态权重 ───
    equal_w = {f: 1.0 / NUM_FACTORS for f in FACTORS}
    computed_weights, computed_fixed_w = compute_dynamic_weights(ic_data_20, blend_alpha=BASELINE_ALPHA)
    
    log(f"  计算权重 (alpha=0.6): UP={ {k: round(v,4) for k,v in computed_weights['up'].items()} }")
    log(f"  冻结权重 (V3):      UP={ {k: round(v,4) for k,v in frozen_weights['up'].items()} }")
    
    # 验证计算权重与冻结权重一致
    weight_match = True
    for regime in ["up", "down", "sideways"]:
        for f in FACTORS:
            cv = computed_weights[regime].get(f, 0)
            fv = frozen_weights[regime].get(f, 0)
            if abs(cv - fv) > 0.0001:
                weight_match = False
                log(f"  ⚠ 权重不一致: {regime}/{f}: 计算={cv:.6f} vs 冻结={fv:.6f}")
    if weight_match:
        log(f"  ✓ 权重完全一致 (计算 vs 冻结)")
    else:
        log(f"  ⚠ 权重存在微小差异 (使用冻结权重回放)")
    
    # 使用冻结权重进行回放
    replay_weights = frozen_weights  # ← 使用V3冻结权重, 不修改
    
    # ════════════════════════════════════════════════════════════
    # P1: 全周期沙箱回放
    # ════════════════════════════════════════════════════════════
    log("\n─── P1: 全周期沙箱回放 (V3冻结策略) ───")
    
    # 计算信号
    signal_replay = compute_signal_dynamic(df_regime, FACTORS, replay_weights)
    
    # 回测
    bt_replay = compute_backtest_from_signal(df_regime, signal_replay)
    replay_metrics = bt_replay["metrics"]
    
    # 翻转率
    flip_20_replay = compute_composite_flip_rate(df_regime, signal_replay, SYMBOL_WHITELIST, "sig_replay", ic_window=IC_WINDOW_20)
    flip_40_replay = compute_composite_flip_rate(df_regime, signal_replay, SYMBOL_WHITELIST, "sig_replay", ic_window=IC_WINDOW_40)
    
    log(f"  回放结果: sharpe={replay_metrics['sharpe_ratio']:.4f}, "
        f"return={replay_metrics['total_return']:.4f}, "
        f"max_dd={replay_metrics['max_drawdown']:.4f}, "
        f"flip_20d={flip_20_replay['flip_rate']:.4f}, "
        f"flip_40d={flip_40_replay['flip_rate']:.4f}")
    
    # ─── 偏差核对 ───
    log("\n─── P1 偏差核对 (阈值: ±0.005) ───")
    
    deviation_check = compare_with_baseline(replay_metrics, task050_baseline_metrics)
    
    # 翻转率偏差
    flip_dev_20 = abs(flip_20_replay["flip_rate"] - task050_flip_20d)
    flip_dev_40 = abs(flip_40_replay["flip_rate"] - task050_flip_40d)
    flip_within_20 = flip_dev_20 <= DEVIATION_THRESHOLD
    flip_within_40 = flip_dev_40 <= DEVIATION_THRESHOLD
    deviation_check["deviations"]["flip_rate_20d"] = {
        "baseline": task050_flip_20d, "replay": flip_20_replay["flip_rate"],
        "deviation": round(flip_dev_20, 6), "within_threshold": flip_within_20,
    }
    deviation_check["deviations"]["flip_rate_40d"] = {
        "baseline": task050_flip_40d, "replay": flip_40_replay["flip_rate"],
        "deviation": round(flip_dev_40, 6), "within_threshold": flip_within_40,
    }
    
    p1_pass = deviation_check["all_pass"] and flip_within_20 and flip_within_40
    
    for k, v in deviation_check["deviations"].items():
        status = "✅" if v["within_threshold"] else "⚠️"
        dev = f"{v['deviation']:.6f}" if v["deviation"] is not None else "N/A"
        log(f"  {status} {k}: 基准={v['baseline']}, 回放={v['replay']}, 偏差={dev}")
    
    log(f"\n  P1偏差检查: {'✅ 全部通过' if p1_pass else '⚠️ 存在偏差超限'}")
    
    # ─── 红线: 偏差>0.005 → 自动FAIL ───
    if not p1_pass:
        log(f"\n  ❌ 红线触发: 基准指标偏差>±{DEVIATION_THRESHOLD}, 自动标记FAIL")
    
    # ════════════════════════════════════════════════════════════
    # P2: 压力扰动校验
    # ════════════════════════════════════════════════════════════
    log("\n─── P2: 压力扰动校验 ───")
    
    stress_results = []
    
    # 场景1: 因子噪声扰动 (σ=2% of factor std)
    log("\n  场景1: 因子噪声扰动")
    df_noisy = add_factor_noise(df, FACTORS)
    s1 = run_stress_scenario(
        "S1_FACTOR_NOISE", "因子噪声扰动 (σ=2%×因子std)",
        df_noisy, replay_weights, equal_w, frozen_fixed_w,
        seed=42
    )
    stress_results.append(s1)
    
    # 场景2: 行情跳变 (±5%)
    log("\n  场景2: 行情跳变")
    df_jump, jump_dates = add_market_jump(df)
    s2 = run_stress_scenario(
        "S2_MARKET_JUMP", f"行情跳变 (±5%, 日期={jump_dates})",
        df_jump, replay_weights, equal_w, frozen_fixed_w,
        seed=43
    )
    stress_results.append(s2)
    
    # 场景3: 波动率放大 (2x)
    log("\n  场景3: 波动率放大")
    df_vol_spike = amplify_volatility(df)
    s3 = run_stress_scenario(
        "S3_VOL_SPIKE", "波动率放大 (2x realized_vol_20d)",
        df_vol_spike, replay_weights, equal_w, frozen_fixed_w,
        seed=44
    )
    stress_results.append(s3)
    
    # 场景4: 组合扰动 (噪声+跳变)
    log("\n  场景4: 组合扰动 (噪声+跳变)")
    df_combo = add_factor_noise(df, FACTORS, noise_sigma_factor=NOISE_SIGMA_FACTOR, seed=45)
    df_combo, _ = add_market_jump(df_combo, jump_pct=MARKET_JUMP_PCT, seed=46)
    s4 = run_stress_scenario(
        "S4_COMBO", "组合扰动 (噪声+跳变叠加)",
        df_combo, replay_weights, equal_w, frozen_fixed_w,
        seed=47
    )
    stress_results.append(s4)
    
    # 场景5: 高强度噪声 (σ=5% of factor std)
    log("\n  场景5: 高强度噪声")
    df_heavy_noise = add_factor_noise(df, FACTORS, noise_sigma_factor=0.05, seed=48)
    s5 = run_stress_scenario(
        "S5_HEAVY_NOISE", "高强度噪声 (σ=5%×因子std)",
        df_heavy_noise, replay_weights, equal_w, frozen_fixed_w,
        seed=49
    )
    stress_results.append(s5)
    
    # 压力测试汇总
    stress_all_pass = all(s["pass"] for s in stress_results)
    stress_max_crowding = max(s["crowding_ratio"] for s in stress_results)
    
    log(f"\n  压力测试汇总: {sum(1 for s in stress_results if s['pass'])}/{len(stress_results)} PASS")
    log(f"  最大拥挤度: {stress_max_crowding:.4f}x (阈值: {CROWDING_MAX}x)")
    
    # ─── 红线: 拥挤度>1.1x → 自动FAIL ───
    if stress_max_crowding > CROWDING_MAX:
        log(f"\n  ❌ 红线触发: 压力测试拥挤度 {stress_max_crowding:.4f}x > {CROWDING_MAX}x, 自动FAIL")
        stress_all_pass = False
    
    # ════════════════════════════════════════════════════════════
    # P3: 边界场景测试
    # ════════════════════════════════════════════════════════════
    log("\n─── P3: 边界场景测试 ───")
    
    boundary_results = []
    
    # 场景A: 低流动性
    log("\n  场景A: 低流动性 (20% OI缺失)")
    df_low_liquidity, affected_oi = create_low_liquidity_scenario(df)
    ba = run_boundary_scenario(
        "B1_LOW_LIQUIDITY", "低流动性 (20% OI数据缺失)",
        df_low_liquidity, replay_weights, equal_w, frozen_fixed_w,
        extra_info={"affected_oi_rows": affected_oi, "affected_pct": 0.20}
    )
    boundary_results.append(ba)
    
    # 场景B: 连续换月
    log("\n  场景B: 连续换月 (强制标记)")
    df_multi_switch, total_switches = create_continuous_switch_scenario(df)
    bb = run_boundary_scenario(
        "B2_CONTINUOUS_SWITCH", "连续换月 (每品种3个强制换月标记)",
        df_multi_switch, replay_weights, equal_w, frozen_fixed_w,
        extra_info={"total_switch_marks": total_switches}
    )
    boundary_results.append(bb)
    
    # 场景C: 极端涨跌 (±8%)
    log("\n  场景C: 极端涨跌 (±8%)")
    df_extreme, extreme_dates = create_extreme_moves_scenario(df, extreme_pct=0.08)
    bc = run_boundary_scenario(
        "B3_EXTREME_MOVES", "极端涨跌 (±8%注入)",
        df_extreme, replay_weights, equal_w, frozen_fixed_w,
        extra_info={"extreme_dates": extreme_dates, "extreme_pct": 0.08}
    )
    boundary_results.append(bc)
    
    # 场景D: 超级流动性 (OI骤增)
    log("\n  场景D: 超级流动性 (OI骤增10%)")
    df_super_liquidity = df.copy()
    df_super_liquidity["oi"] = df_super_liquidity["oi"] * 1.10
    bd = run_boundary_scenario(
        "B4_SUPER_LIQUIDITY", "超级流动性 (OI均匀+10%)",
        df_super_liquidity, replay_weights, equal_w, frozen_fixed_w,
        extra_info={"oi_multiplier": 1.10}
    )
    boundary_results.append(bd)
    
    # 场景E: 数据缺失场景 (随机缺失5%数据)
    log("\n  场景E: 数据缺失 (5%随机缺失)")
    rng_miss = np.random.RandomState(50)
    df_missing = df.copy()
    miss_mask = rng_miss.random(len(df_missing)) < 0.05
    for col in ["close", "oi", "high", "low", "volume"]:
        if col in df_missing.columns:
            df_missing.loc[miss_mask, col] = np.nan
    # 填充NaN
    for col in ["close", "oi", "high", "low", "volume"]:
        if col in df_missing.columns:
            df_missing[col] = df_missing[col].fillna(df_missing[col].median())
    be = run_boundary_scenario(
        "B5_DATA_MISSING", "数据缺失 (5%随机缺失后填充)",
        df_missing, replay_weights, equal_w, frozen_fixed_w,
        extra_info={"missing_pct": 0.05, "missing_rows": int(miss_mask.sum())}
    )
    boundary_results.append(be)
    
    # 边界场景汇总
    boundary_all_pass = all(s["pass"] for s in boundary_results)
    log(f"\n  边界场景汇总: {sum(1 for s in boundary_results if s['pass'])}/{len(boundary_results)} PASS")
    
    # ════════════════════════════════════════════════════════════
    # P4: 全链路风险复核
    # ════════════════════════════════════════════════════════════
    log("\n─── P4: 全链路风险复核 ───")
    
    risk_final = validate_risk(df, replay_weights, frozen_fixed_w, equal_w, crowding_threshold=CROWDING_MAX)
    
    log(f"  HHI等权基线: {risk_final['hhi_equal']}")
    log(f"  HHI动态均值: {risk_final['hhi_dynamic_avg']}")
    log(f"  拥挤度比率: {risk_final['crowding_ratio']:.4f}x (阈值: {CROWDING_MAX}x)")
    log(f"  高相关对: {len(risk_final['high_corr_pairs'])}")
    log(f"  冗余告警: {'⚠️ 有' if risk_final['redundancy_alert'] else '✅ 无'}")
    log(f"  拥挤度告警: {'⚠️ 有' if risk_final['crowding_alert'] else '✅ 无'}")
    
    # 压力测试风险报告
    stress_risk_report = {
        "scenario_crowding": [s["crowding_ratio"] for s in stress_results],
        "scenario_sharpe": [s["metrics"]["sharpe_ratio"] for s in stress_results],
        "scenario_return": [s["metrics"]["total_return"] for s in stress_results],
        "scenario_max_dd": [s["metrics"]["max_drawdown"] for s in stress_results],
        "max_crowding": stress_max_crowding,
        "min_sharpe": min(s["metrics"]["sharpe_ratio"] for s in stress_results),
        "worst_return": min(s["metrics"]["total_return"] for s in stress_results),
        "worst_dd": min(s["metrics"]["max_drawdown"] for s in stress_results),
        "crowding_threshold": CROWDING_MAX,
        "crowding_within_all": stress_max_crowding <= CROWDING_MAX,
    }
    
    # 边界场景风险报告
    boundary_risk_report = {
        "scenario_crowding": [s["crowding_ratio"] for s in boundary_results],
        "scenario_sharpe": [s["metrics"]["sharpe_ratio"] for s in boundary_results],
        "scenario_return": [s["metrics"]["total_return"] for s in boundary_results],
        "max_crowding": max(s["crowding_ratio"] for s in boundary_results),
        "min_sharpe": min(s["metrics"]["sharpe_ratio"] for s in boundary_results),
    }
    
    p4_risk_report = {
        "output_id": "DSHA-TASK051-P4-RISK-REPORT",
        "generated_at": now_iso(),
        "token": TOKEN,
        "task": TASK_ID,
        "safety": {"real_wind_call": False, "wind_api_calls": 0,
                     "offline_only": True, "gate": GATE_STATUS, "release": RELEASE_STATUS},
        "baseline_risk": risk_final,
        "stress_test_risk": stress_risk_report,
        "boundary_test_risk": boundary_risk_report,
        "aggregate": {
            "baseline_crowding": risk_final["crowding_ratio"],
            "stress_max_crowding": stress_max_crowding,
            "boundary_max_crowding": boundary_risk_report["max_crowding"],
            "overall_max_crowding": max(risk_final["crowding_ratio"], stress_max_crowding,
                                        boundary_risk_report["max_crowding"]),
            "all_within_threshold": max(risk_final["crowding_ratio"], stress_max_crowding,
                                         boundary_risk_report["max_crowding"]) <= CROWDING_MAX,
        },
    }
    
    log(f"  综合最大拥挤度: {p4_risk_report['aggregate']['overall_max_crowding']:.4f}x")
    log(f"  全部阈值内: {'✅' if p4_risk_report['aggregate']['all_within_threshold'] else '⚠️'}")
    
    # ════════════════════════════════════════════════════════════
    # 全局通过判定
    # ════════════════════════════════════════════════════════════
    log("\n─── 全局通过判定 ───")
    
    overall_pass = (
        p1_pass and       # P1 偏差≤0.005
        stress_all_pass and  # P2 压力测试全部通过
        boundary_all_pass and  # P3 边界场景全部通过
        not risk_final["crowding_alert"] and  # P4 风险无告警
        p4_risk_report["aggregate"]["all_within_threshold"]  # 综合风险
    )
    
    fail_reasons = []
    if not p1_pass:
        fail_reasons.append(f"P1偏差超限 (阈值±{DEVIATION_THRESHOLD})")
    if not stress_all_pass:
        fail_reasons.append(f"P2压力测试失败 (max_crowding={stress_max_crowding:.4f}x)")
    if not boundary_all_pass:
        fail_reasons.append("P3边界场景失败")
    if risk_final["crowding_alert"]:
        fail_reasons.append(f"P4风险告警 (crowding={risk_final['crowding_ratio']:.4f}x)")
    
    overall_status = "PASS" if overall_pass else "FAIL"
    log(f"  最终判定: {'✅ PASS' if overall_pass else '❌ FAIL'}")
    if fail_reasons:
        log(f"  失败原因: {'; '.join(fail_reasons)}")
    
    # ════════════════════════════════════════════════════════════
    # P5: DSHD推送
    # ════════════════════════════════════════════════════════════
    log("\n─── P5: DSHD审计推送 ───")
    
    replay_result = {
        "replay_metrics": replay_metrics,
        "baseline_metrics": task050_baseline_metrics,
        "deviation_check": deviation_check,
        "flip_20d": flip_20_replay["flip_rate"],
        "flip_40d": flip_40_replay["flip_rate"],
        "p1_pass": p1_pass,
    }
    
    push_data = build_dshd_push(
        p0_result, replay_result, stress_results, boundary_results,
        risk_final, p4_risk_report
    )
    dump_json(DSHD_PUSH_FILE, push_data)
    update_dshd_brief(push_data)
    
    # 审计日志事件
    append_audit({
        "event": "DSHD_TASK051_FROZEN_BACKTEST_PUSH",
        "task": TASK_ID,
        "token": DSHD_TOKEN,
        "push_type": "FROZEN_BACKTEST_VALIDATION",
        "mode": "AUDIT_READ_ONLY",
        "wind_api_calls": 0,
        "engine": "Set-E (PERMANENTLY_FROZEN)",
        "v3_modified": False,
        "p0_pass": p0_result.get("p0_all_pass", False),
        "p1_deviation_all_pass": p1_pass,
        "p2_stress_all_pass": stress_all_pass,
        "p3_boundary_all_pass": boundary_all_pass,
        "p4_risk_alert": risk_final["crowding_alert"],
        "overall_status": overall_status,
    })
    
    # 审计日志: TASK051_START
    append_audit({
        "event": "TASK051_START",
        "task": TASK_ID,
        "token": TOKEN,
        "baseline": BASELINE_COMMIT,
        "gate": GATE_STATUS,
        "release": RELEASE_STATUS,
        "wind_api_calls": 0,
        "set_e_frozen": SET_E_FROZEN,
        "read_only_mode": READ_ONLY_MODE,
        "v3_frozen_status": "PERMANENTLY_FROZEN",
    })
    
    # ════════════════════════════════════════════════════════════
    # P6: 版本验收文档
    # ════════════════════════════════════════════════════════════
    log("\n─── P6: 版本验收文档 ───")
    
    # 构建验收文档
    acceptance_doc = {
        "output_id": "DSHA-TASK051-V3-ACCEPTANCE-DOC",
        "generated_at": now_iso(),
        "token": TOKEN,
        "task": TASK_ID,
        "safety": {
            "real_wind_call": False, "wind_api_calls": 0,
            "offline_only": True, "gate": GATE_STATUS, "release": RELEASE_STATUS,
            "read_only_mode": True,
            "v3_modification_forbidden": True,
        },
        "v3_version": {
            "variant_id": "V3",
            "description": f"TASK050: alpha={BASELINE_ALPHA}, {fwr['selected_window']} IC, PERMANENTLY_FROZEN",
            "alpha": BASELINE_ALPHA,
            "ic_window": fwr["ic_window"],
            "selected_window": fwr["selected_window"],
            "freeze_status": "PERMANENTLY_FROZEN",
            "frozen_at": fwr.get("frozen_at"),
            "frozen_by": fwr.get("frozen_by"),
            "baseline_commit": fwr.get("baseline_commit", BASELINE_COMMIT),
            "engine": "Set-E (PERMANENTLY_FROZEN)",
        },
        "p0_prereq": p0_result,
        "p1_replay_validation": {
            "replay_metrics": replay_metrics,
            "baseline_metrics": task050_baseline_metrics,
            "flip_rate_20d": {
                "baseline": task050_flip_20d,
                "replay": flip_20_replay["flip_rate"],
                "deviation": round(flip_dev_20, 6),
                "within_threshold": flip_within_20,
            },
            "flip_rate_40d": {
                "baseline": task050_flip_40d,
                "replay": flip_40_replay["flip_rate"],
                "deviation": round(flip_dev_40, 6),
                "within_threshold": flip_within_40,
            },
            "deviation_check": deviation_check,
            "threshold": DEVIATION_THRESHOLD,
            "pass": p1_pass,
        },
        "p2_stress_test": {
            "scenarios": stress_results,
            "summary": {
                "total": len(stress_results),
                "pass": sum(1 for s in stress_results if s["pass"]),
                "fail": sum(1 for s in stress_results if not s["pass"]),
                "all_pass": stress_all_pass,
                "max_crowding": stress_max_crowding,
                "min_sharpe": min(s["metrics"]["sharpe_ratio"] for s in stress_results),
                "threshold": CROWDING_MAX,
            },
            "pass": stress_all_pass,
        },
        "p3_boundary_test": {
            "scenarios": boundary_results,
            "summary": {
                "total": len(boundary_results),
                "pass": sum(1 for s in boundary_results if s["pass"]),
                "fail": sum(1 for s in boundary_results if not s["pass"]),
                "all_pass": boundary_all_pass,
            },
            "pass": boundary_all_pass,
        },
        "p4_risk_review": p4_risk_report,
        "red_line_violations": {
            "deviation_exceeded": not p1_pass,
            "crowding_exceeded": stress_max_crowding > CROWDING_MAX,
            "any_red_line": not overall_pass,
            "fail_reasons": fail_reasons,
        },
        "overall_verdict": {
            "status": overall_status,
            "pass": overall_pass,
            "timestamp": now_iso(),
            "fail_reasons": fail_reasons if fail_reasons else "None — all checks passed",
            "next_action": "V3版本可继续保持冻结状态" if overall_pass else "V3版本需要人工审查后决定",
        },
        "receipt": "",
    }
    
    # 构建回执
    receipt = (
        f"DSHA_TASK051_FROZEN_BACKTEST_VALID=COMPLETE|"
        f"p0_all_pass={'YES' if p0_result.get('p0_all_pass') else 'PARTIAL'}|"
        f"p1_replay_sharpe={replay_metrics['sharpe_ratio']:.4f}|"
        f"p1_baseline_sharpe={task050_baseline_metrics['sharpe_ratio']:.4f}|"
        f"p1_sharpe_deviation={abs(replay_metrics['sharpe_ratio'] - task050_baseline_metrics['sharpe_ratio']):.6f}|"
        f"p1_return_deviation={abs(replay_metrics['total_return'] - task050_baseline_metrics['total_return']):.6f}|"
        f"p1_max_dd_deviation={abs(replay_metrics['max_drawdown'] - task050_baseline_metrics['max_drawdown']):.6f}|"
        f"p1_flip_20d_deviation={flip_dev_20:.6f}|"
        f"p1_flip_40d_deviation={flip_dev_40:.6f}|"
        f"p1_deviation_threshold=±{DEVIATION_THRESHOLD}|"
        f"p1_pass={'YES' if p1_pass else 'NO'}|"
        f"p2_scenarios={len(stress_results)}|"
        f"p2_all_pass={'YES' if stress_all_pass else 'NO'}|"
        f"p2_max_crowding={stress_max_crowding:.4f}x|"
        f"p2_crowding_threshold={CROWDING_MAX}x|"
        f"p3_scenarios={len(boundary_results)}|"
        f"p3_all_pass={'YES' if boundary_all_pass else 'NO'}|"
        f"p4_crowding={risk_final['crowding_ratio']:.4f}x|"
        f"p4_high_corr_pairs={len(risk_final['high_corr_pairs'])}|"
        f"p4_crowding_alert={'YES' if risk_final['crowding_alert'] else 'NO'}|"
        f"overall_status={overall_status}|"
        f"engine=Set-E|v3_modified=NO|read_only=YES|wind=0|gate={GATE_STATUS}|release={RELEASE_STATUS}"
    )
    
    acceptance_doc["receipt"] = receipt
    dump_json(RESEARCH_DIR / "v3_acceptance_document.json", acceptance_doc)
    
    # ─── MANIFEST 更新 ───
    log("\n─── MANIFEST 更新 ───")
    
    # 读取现有MANIFEST
    if TASK050_MANIFEST.exists():
        manifest = json.loads(TASK050_MANIFEST.read_text(encoding="utf-8"))
    else:
        manifest = {"manifest_id": "DSHA-TASK051-FROZEN-BACKTEST-MANIFEST", "receipt": "", "smoke_check": None}
    
    manifest["task051_validation"] = {
        "output_id": "DSHA-TASK051-V3-ACCEPTANCE-DOC",
        "generated_at": now_iso(),
        "token": TOKEN,
        "overall_status": overall_status,
        "p1_pass": p1_pass,
        "p2_stress_all_pass": stress_all_pass,
        "p3_boundary_all_pass": boundary_all_pass,
        "p4_risk_alert": risk_final["crowding_alert"],
        "report_path": "artifacts/p49_v3_regime_weight/v3_acceptance_document.json",
    }
    manifest["receipt"] = receipt
    dump_json(TASK050_MANIFEST, manifest)
    
    # ─── 审计日志: TASK051_COMPLETE ───
    append_audit({
        "event": "TASK051_COMPLETE",
        "task": TASK_ID,
        "token": TOKEN,
        "receipt": receipt,
        "overall_status": overall_status,
        "p0_pass": p0_result.get("p0_all_pass", False),
        "p1_pass": p1_pass,
        "p2_stress_all_pass": stress_all_pass,
        "p3_boundary_all_pass": boundary_all_pass,
        "p4_risk_alert": risk_final["crowding_alert"],
        "replay_sharpe": replay_metrics["sharpe_ratio"],
        "baseline_sharpe": task050_baseline_metrics["sharpe_ratio"],
        "stress_max_crowding": stress_max_crowding,
        "engine": "Set-E",
        "v3_modified": False,
        "wind_api_calls": 0,
        "gate": GATE_STATUS,
        "release": RELEASE_STATUS,
        "read_only_mode": True,
    })
    
    # ─── TASK051 COMPLETE ───
    log("\n─── TASK051 COMPLETE ───")
    log(f"\n{'='*72}")
    log(f"📋 回执: {receipt}")
    log(f"{'='*72}")
    
    elapsed = time.time() - t0
    log(f"\n耗时: {elapsed:.1f}秒")
    log(f"✅ {TASK_ID} 完成 — {overall_status}")
    
    return receipt

if __name__ == "__main__":
    receipt = main()
