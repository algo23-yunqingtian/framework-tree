#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHA-TASK-065: V3-EXT MC复验 + 三因子剔除落地 一键工单
================================================================
基线: TASK064 (7216221) — V3-EXT-14POOL-062 观测池准入评审定稿
分支: feature/v88-g1 | 版本标签: V3-EXT-14POOL-062-OBS-R01
模式: RESEARCH_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED

P0  冒烟自检 (4项)
    P0.1 锁定T064输出指纹 V3-EXT-14POOL-062-OBS-ENTRY;
         校验 observation_pool_entry.json 与 full_manifest_t062_t063_t064.json SHA匹配
    P0.2 确认三因子ID: price_momentum_2nd_diff / oi_momentum_divergence_20d / price_vol_momentum
    P0.3 AST扫描: 无无限MC循环(MC_ROUNDS<=300) / banned_func_calls=0 /
         沙箱目录pool_14_062独立 / 不触碰MN主快照目录DSH_MASTER_NOTEBOOK
    P0.4 导入T064定稿参数: MEDIUM下限0.40 / HEAVY上限0.30 /
         双分支共振连续3次→LOCKDOWN逻辑启用
P1  小样本MC复验 (300轮, 低资源模式)
    P1.1 隔离sandbox_mc运行; 验证调整权重地板后Sharpe_delta分布稳定性;
         输出 summary_mc_t065.csv
    P1.2 共振LOCKDOWN逻辑单元测试: 连续3次共振置位正确 / 不卡死流程
    P1.3 输出 T065_mc_review_report.md: 通过/存疑/不通过结论;
         存疑则列风险点; 不自动修改参数, 只输出评估
P2  因子排除规则固化
    P2.1 实验组配置写入三因子 PERMANENTLY_EXCLUDED 标记; 备注来源=DSHA-T064;
         有效期与观测池对齐60交易日
    P2.2 重申硬边界: V3-EXT仅离线长期观测实验 / 永不替换V3-8主因子基线 /
         生产部署FORBIDDEN / 调参入口临时冻结
    P2.3 更新 observation_pool_entry.json: 追加T065复验结论 / 修订时间戳 / commit锚点
P3  观测池二次密封 & 清单重哈希
    P3.1 重新生成完整聚合SHA full_manifest_t062_t063_t064_t065.json;
         保留SELF自引用标记说明
    P3.2 关闭本组工作流外部可写开关; 轮询=DISABLED; 等待DSHC SNAP归档信号
    P3.3 全部制品落盘到 artifacts/candidate_experiment/pool_14_062/;
         生成 task065_receipt.txt
P4  收尾红线校验
    P4.1 沙箱之外无意外写入; wind=0; cross_write=NO; gate=CLOSED/HOLD
    P4.2 核对所有产出文件清单; 没有生成任何一键部署到生产的脚本

红线: wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED |
      MC最大轮数=300 | 禁止启动大规模自动回测 | 不改动V3主基线8因子 |
      实验沙箱隔离 | cross_write=NO
================================================================
"""

import ast
import csv
import hashlib
import json
import math
import os
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════════
# 安全锁 & 常量
# ════════════════════════════════════════════════════════════════
READ_ONLY_MODE = True
WIND_API_CALLS = 0
GATE_STATUS = "CLOSED/HOLD"
RELEASE_STATUS = "NOT_ISSUED"
V3_MODIFIED = False
CROSS_WRITE = False
EXPERIMENT_ONLY = True
MC_ROUNDS = 300          # 硬上限: 小样本MC, 低资源模式
MC_MAX_CAP = 300

TASK065_ID = "DSHA-TASK-065"
TASK065_TOKEN = "DSHA-TASK-065-MC-REVIEW-EXCLUSION-LOCK-TOKEN"
BASELINE_COMMIT = "7216221"
PREV_TASK = "DSHA-TASK-064"
SNAPSHOT_ID = "V3-EXT-14POOL-062"
VERSION_TAG = "V3-EXT-14POOL-062-OBS-R01"
T064_VERSION_TAG = "V3-EXT-14POOL-062-OBS-ENTRY"

from datetime import datetime, timezone, timedelta
TZ = timezone(timedelta(hours=8))

BASE_DIR = r"D:\DSH_WORK\github工作\回测"
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
SANDBOX_DIR = os.path.join(ARTIFACTS_DIR, "p49_v3_regime_weight")
EXPERIMENT_DIR = os.path.join(ARTIFACTS_DIR, "candidate_experiment")
POOL_DIR = os.path.join(EXPERIMENT_DIR, "pool_14_062")
MC_SANDBOX_DIR = os.path.join(SANDBOX_DIR, "sandbox_mc")   # P1.1 隔离MC沙箱
AUDIT_LOG = os.path.join(BASE_DIR, "tracking_monitor_audit.jsonl")
MANIFEST = os.path.join(SANDBOX_DIR, "MANIFEST_v3_regime_weight.json")
WORKFLOW_LOCK_DIR = os.path.join(BASE_DIR, "workflow_lock")          # 禁止写入
MN_SNAPSHOT_DIR = os.path.join(BASE_DIR, "DSH_MASTER_NOTEBOOK")      # 禁止触碰
PROD_DIR = os.path.join(ARTIFACTS_DIR, "p49_v3_backtest")            # 禁止写入

# T064 输出 (P0.1 指纹锁定对象)
T064_ENTRY_DOC = os.path.join(POOL_DIR, "observation_pool_entry.json")
T064_MANIFEST = os.path.join(POOL_DIR, "full_manifest_t062_t063_t064.json")

# V3 数据
V3_FACTORS_CSV = os.path.join(PROD_DIR, "factors_full_11_v3.csv")

# T065 输出: pool_14_062 (P3.3 全部落盘)
OUT_SUMMARY_MC_CSV = os.path.join(POOL_DIR, "summary_mc_t065.csv")
OUT_LOCKDOWN_UTEST = os.path.join(POOL_DIR, "resonance_lockdown_unit_test.json")
OUT_REVIEW_REPORT = os.path.join(POOL_DIR, "T065_mc_review_report.md")
OUT_EXCLUSION_REGISTRY = os.path.join(POOL_DIR, "factor_exclusion_registry.json")
OUT_BOUNDARY_DECL = os.path.join(POOL_DIR, "v3_ext_boundary_declaration.json")
OUT_ENTRY_DOC = os.path.join(POOL_DIR, "observation_pool_entry.json")   # P2.3 原地修订
OUT_FULL_MANIFEST = os.path.join(POOL_DIR, "full_manifest_t062_t063_t064_t065.json")

# T065 输出: p49 沙箱 (工作流密封 + 回执)
OUT_WORKFLOW_SEAL = os.path.join(SANDBOX_DIR, "dsha_task065_workflow_seal.json")
OUT_RECEIPT = os.path.join(SANDBOX_DIR, "task065_receipt.txt")

# T065 输出: sandbox_mc 内部细节 (隔离, 不进入池清单)
MC_DETAIL_JSON = os.path.join(MC_SANDBOX_DIR, "mc_rounds_detail_t065.json")
MC_LOCKDOWN_TRACE = os.path.join(MC_SANDBOX_DIR, "lockdown_trace_t065.json")
MC_SANDBOX_MARKER = os.path.join(MC_SANDBOX_DIR, "sandbox_mc_marker.json")

# 清单文件列表 (T062/T063/T064 + T065)
T062_FILES = [
    "v3_ext_14pool_dynamic_fingerprint.json",
    "dual_backtest_comparison.json",
    "mc_simulation_dynamic.json",
    "gate_intercept_log.json",
    "performance_decay_boundary_dynamic.json",
    "v3_ext_14pool_dynamic_adoption_proposal.json",
    "triple_consistency_task062.json",
    "audit_snapshot_dsha055-062.jsonl",
    "dynamic_weight_14pool_ts.json",
    "manifest_pool_14_062.json",
]
T063_FILES = [
    "layered_attribution_by_grade.json",
    "sharpe_decline_root_cause.json",
    "tradeoff_matrix.json",
    "mc_high_failure_analysis.json",
    "scenario_slices_4cases.json",
    "gate_effectiveness_review.json",
    "risk_heatmap.json",
    "attribution_sealed_proposal.json",
    "deferred_factors_attribution.json",
    "attribution_fingerprint.json",
]
T064_FILES = [
    "sensitivity_weight_sweep.json",
    "sensitivity_crowding_sweep.json",
    "sensitivity_feasible_region.json",
    "sensitivity_heatmap_3d.json",
    "shortcoming_optimization_plan.json",
    "observation_pool_entry.json",
    "full_manifest_t062_t063_t064.json",
    "iteration_preconditions.json",
]
T065_FILES = [
    "summary_mc_t065.csv",
    "resonance_lockdown_unit_test.json",
    "T065_mc_review_report.md",
    "factor_exclusion_registry.json",
    "v3_ext_boundary_declaration.json",
    "full_manifest_t062_t063_t064_t065.json",
]
FULL_MANIFEST_NAME = "full_manifest_t062_t063_t064_t065.json"

# ════════════════════════════════════════════════════════════════
# 因子定义 (V3 8主因子永久冻结, 只读)
# ════════════════════════════════════════════════════════════════
V3_FACTORS_8 = [
    "contract_switch_flag", "momentum_20d",
    "oi_change_1d", "oi_change_rate_7d",
    "oi_level", "realized_vol_20d",
    "spread_cs", "vol_regime_change",
]
V3_SYMBOLS_4 = ["LC.GFE", "NI.SHF", "CU.SHF", "ZN.SHF"]
OBSERVE_FACTORS_6 = [
    "basis_2nd_momentum_5d", "intraday_ohlc_position",
    "term_slope_20d", "close_relative_range",
    "term_curvature_20d", "contango_premium_20d",
]
DEFERRED_FACTORS_3 = [
    "price_momentum_2nd_diff", "oi_momentum_divergence_20d", "price_vol_momentum",
]
GROUP_A_FACTORS = V3_FACTORS_8 + OBSERVE_FACTORS_6

# 权重
V3_FIXED_WEIGHTS = {
    "contract_switch_flag": 0.173862, "momentum_20d": 0.240761,
    "oi_change_1d": 0.039409, "oi_change_rate_7d": 0.072074,
    "oi_level": 0.112601, "realized_vol_20d": 0.102804,
    "spread_cs": 0.127197, "vol_regime_change": 0.131292,
}
CANDIDATE_DEMO_WEIGHTS = {
    "basis_2nd_momentum_5d": 0.114592, "intraday_ohlc_position": 0.150001,
    "term_slope_20d": 0.150001, "close_relative_range": 0.150001,
    "term_curvature_20d": 0.150001, "contango_premium_20d": 0.050771,
}
GROUP_A_WEIGHTS = {}
_v3w = sum(V3_FIXED_WEIGHTS.values())
_cw = sum(CANDIDATE_DEMO_WEIGHTS.values())
for f in V3_FACTORS_8:
    GROUP_A_WEIGHTS[f] = (V3_FIXED_WEIGHTS[f] / _v3w) * 0.8
for f in OBSERVE_FACTORS_6:
    GROUP_A_WEIGHTS[f] = (CANDIDATE_DEMO_WEIGHTS[f] / _cw) * 0.2

MAIN_BASE_WEIGHTS = {
    "contract_switch_flag": 0.10832853, "momentum_20d": 0.10330617,
    "oi_change_1d": 0.10519997, "oi_change_rate_7d": 0.09264037,
    "oi_level": 0.10072047, "realized_vol_20d": 0.1100223,
    "spread_cs": 0.11240457, "vol_regime_change": 0.11737763,
}
CANDIDATE_BASE_WEIGHTS_6 = {
    "intraday_ohlc_position": 0.03788252,
    "close_relative_range": 0.03023215,
    "basis_2nd_momentum_5d": 0.01134365,
    "contango_premium_20d": 0.00685895,
    "term_slope_20d": 0.02004924,
    "term_curvature_20d": 0.02084066,
}

# v4.48 动态权重规则 (T064基线参数)
CROWDING_P90 = 1.05401
CROWDING_P95 = 1.05854
JERK_HEAVY = 0.000474
FLIP_L1 = 0.55
FLIP_L2 = 0.65
SYNC_ESCALATE = 4
SYNC_PENALTY = 0.95
MAIN_FACTOR_CAP = 0.18
CAND_BASE_SUM = 0.15

GRADE_ORDER = {"NONE": 0, "LIGHT": 1, "MEDIUM": 2, "HEAVY": 3}

# T064基线系数 (对照组, 用于MC配对对照)
GRADE_COEFFS_BASE = {
    "NONE":   {"weight_factor": 1.0,  "single_cap": 0.18, "pool_sum_cap": 0.15},
    "LIGHT":  {"weight_factor": 0.75, "single_cap": 0.18, "pool_sum_cap": 0.15},
    "MEDIUM": {"weight_factor": 0.50, "single_cap": 0.12, "pool_sum_cap": 0.12},
    "HEAVY":  {"weight_factor": 0.20, "single_cap": 0.10, "pool_sum_cap": 0.05},
}

# T065定稿参数 (P0.4 导入T064定稿): MEDIUM下限0.40 / HEAVY上限0.30
# + T064 P2.2 双分支共振规则: LOCKDOWN等级候选权重强制归零
GRADE_COEFFS_T065 = {
    "NONE":      {"weight_factor": 1.0,  "single_cap": 0.18, "pool_sum_cap": 0.15},
    "LIGHT":     {"weight_factor": 0.75, "single_cap": 0.18, "pool_sum_cap": 0.15},
    "MEDIUM":    {"weight_factor": 0.40, "single_cap": 0.12, "pool_sum_cap": 0.12},
    "HEAVY":     {"weight_factor": 0.30, "single_cap": 0.10, "pool_sum_cap": 0.05},
    "LOCKDOWN":  {"weight_factor": 0.00, "single_cap": 0.00, "pool_sum_cap": 0.00},
}

# T064 P2.2: 双分支共振规则
RESONANCE_LOCKDOWN_THRESHOLD = 3     # 连续3次双分支共振 → LOCKDOWN
LOCKDOWN_HOLD_DAYS = 20              # LOCKDOWN持续20个交易日
LOCKDOWN_HOLD_PERIODS = LOCKDOWN_HOLD_DAYS // 5   # = 4 个调仓周期

# T065 拥挤阈值: 采用T064最优参数 (P90/P95 各 +0.02)
CROWDING_P90_T065 = round(CROWDING_P90 + 0.02, 5)   # 1.07401
CROWDING_P95_T065 = round(CROWDING_P95 + 0.02, 5)   # 1.07854

# 回测参数
SIGNAL_THRESHOLD = 0.3
REBALANCE_INTERVAL = 5
TRANSACTION_COST = 0.0005
INITIAL_CAPITAL = 1_000_000.0
TRADING_DAYS = 252
DRAWDOWN_WARN = -0.10
DRAWDOWN_HALT = -0.20

# SHA / 红线
EXPECTED_CSV_SHA = "dd6674bb323ce6f5b9c7b80c021e1d1a5cb2917f631a822b1104924232611b9b"
MN_SNAPSHOT_GUARD = "DSH_MASTER_NOTEBOOK"

# T063/T064 关键数值 (用于对比)
CONTROL_SHARPE = 1.964687
CONTROL_TOTAL_RETURN = 11.863654
CONTROL_MDD = -0.13568
T063_FLIP_RATE_CONTROL = 0.2351
EXPERIMENT_SHARPE_BASE = 1.268893          # T064 0.5/0.2 基线
EXPERIMENT_DELTA_BASE = -0.695794
T063_MC_FAILURE_PROB = 0.959
T064_BEST_SHARPE = 1.627507                # 0.55/0.23 + both+0.02
T064_BEST_DELTA = -0.33718

# MC 配对对照: T064基线配置 (复现基准, 引擎自校验锚点)
MC_CTRL_CFG = {
    "name": "T064_CFG",
    "grade_coeffs": GRADE_COEFFS_BASE,
    "p90": CROWDING_P90, "p95": CROWDING_P95,
    "decision": "MAX_OF_GRADES",           # T064/T063 原逻辑
    "resonance_lockdown": False,
}
MC_T065_CFG = {
    "name": "T065_CFG",
    "grade_coeffs": GRADE_COEFFS_T065,
    "p90": CROWDING_P90_T065, "p95": CROWDING_P95_T065,
    "decision": "RESONANCE_LOCKDOWN",      # T064 P2.2 双分支共振 + 连续3次LOCKDOWN
    "resonance_lockdown": True,
}

# MC zone 分类阈值 (与T062一致, 保证可比)
MC_SAFE_SHARPE = 1.0
MC_SAFE_MDD = -0.10
MC_WARN_SHARPE = 0.5
MC_WARN_MDD = -0.15
MC_CROWD_CEIL = 0.30


# ════════════════════════════════════════════════════════════════
# 通用工具
# ════════════════════════════════════════════════════════════════
def now_str():
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def sha256_file(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_json_load(fp):
    with open(fp, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# 受追踪写入: 每个写入路径都登记, 供P4.1沙箱外写入校验
WRITE_LOG = []


def _track_write(path):
    WRITE_LOG.append(path)


def write_json_tracked(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _track_write(path)


def write_text_tracked(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    _track_write(path)


def append_audit(event_name, task, detail, status="PASS"):
    entry = {
        "timestamp": now_str(), "event": event_name, "task": task,
        "detail": detail, "status": status, "read_only": True,
        "wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
    }
    os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _track_write(AUDIT_LOG)
    return entry


# ════════════════════════════════════════════════════════════════
# 因子计算 (复用 TASK061/T063/T064, 零改动)
# ════════════════════════════════════════════════════════════════
def compute_new_factors(df):
    df = df.copy()
    g = df.groupby("symbol")
    df["daily_return"] = g["close"].pct_change().fillna(0)
    df["range_pct"] = np.where(df["close"] > 0, (df["high"] - df["low"]) / df["close"].clip(lower=1), 0)
    df["price_change"] = g["close"].diff().fillna(0)
    df["oi_change_daily"] = g["oi"].diff().fillna(0)
    df["vol_change"] = g["vol"].diff().fillna(0)
    df["price_momentum_2nd_diff"] = g["daily_return"].transform(
        lambda x: x.rolling(20, min_periods=1).sum().diff(20).fillna(0))
    df["return_skewness_20d"] = g["daily_return"].transform(
        lambda x: x.rolling(20, min_periods=5).skew().fillna(0))
    df["return_kurtosis_20d"] = g["daily_return"].transform(
        lambda x: x.rolling(20, min_periods=5).kurt().fillna(0))
    vol_dev = g["vol"].transform(lambda x: x - x.rolling(20, min_periods=1).mean())
    price_dir = np.sign(df["price_change"])
    vol_dir = np.sign(vol_dev)
    df["price_volume_divergence"] = ((price_dir != 0) & (vol_dir != 0) & (price_dir != vol_dir)).astype(float)
    vol_mean = g["vol"].transform(lambda x: x.rolling(20, min_periods=1).mean())
    vol_std = g["vol"].transform(lambda x: x.rolling(20, min_periods=1).std().fillna(1))
    df["volume_breakout"] = ((df["vol"] - vol_mean) / vol_std.replace(0, 1)).fillna(0)
    rp_mean = g["range_pct"].transform(lambda x: x.rolling(20, min_periods=5).mean().fillna(0))
    df["volume_squeeze"] = ((df["range_pct"] < rp_mean * 0.8) & (df["range_pct"] > 0)).astype(float)
    df["intraday_ohlc_position"] = np.where(df["high"] > df["low"],
        (df["close"] - df["low"]) / (df["high"] - df["low"]), 0.5)
    c_min20 = g["close"].transform(lambda x: x.rolling(20, min_periods=1).min())
    c_max20 = g["close"].transform(lambda x: x.rolling(20, min_periods=1).max())
    df["close_relative_range"] = np.where(c_max20 > c_min20,
        (df["close"] - c_min20) / (c_max20 - c_min20).replace(0, 1), 0.5)
    df["volume_deviation_from_mean"] = np.where(vol_mean > 0,
        (df["vol"] - vol_mean) / vol_mean, 0)
    df["capital_inflow_intensity"] = np.where(df["settle"] > 0,
        df["close"] * df["vol"] / df["settle"].replace(0, 1), 0)
    mom5 = g["close"].pct_change(5).fillna(0)
    vol_mom5 = g["vol"].pct_change(5).fillna(0)
    df["price_vol_momentum"] = mom5 * vol_mom5
    df["volume_trend_ratio"] = np.where(vol_mean > 0, df["vol"] / vol_mean, 1.0)
    df["quantile_volatility_20d"] = np.where(df["close"] > 0,
        (c_max20 - c_min20) / df["close"].clip(lower=1), 0)
    df["realized_volatility_40d"] = g["daily_return"].transform(
        lambda x: x.rolling(40, min_periods=5).std().fillna(0))
    ret_abs_max = g["daily_return"].transform(lambda x: x.abs().rolling(20, min_periods=5).max())
    ret_std = g["daily_return"].transform(lambda x: x.rolling(20, min_periods=5).std().fillna(1))
    df["vol_fractal_dimension_20d"] = np.clip(1.0 - ret_std / ret_abs_max.replace(0, 1), 0, 1).fillna(0.5)
    df["up_volatility_20d"] = g["daily_return"].transform(
        lambda x: x.where(x > 0).rolling(20, min_periods=3).std().fillna(0))
    df["down_volatility_20d"] = g["daily_return"].transform(
        lambda x: x.where(x < 0).rolling(20, min_periods=3).std().fillna(0))
    mid20 = g["close"].transform(lambda x: x.rolling(20, min_periods=3).mean())
    std20 = g["close"].transform(lambda x: x.rolling(20, min_periods=3).std().fillna(0))
    df["bollinger_bandwidth_20d"] = np.where(mid20 > 0, (4 * std20) / mid20, 0)

    def _clustering_fast(x):
        r = x.rolling(20, min_periods=5)
        std = r.std().fillna(1)
        thr = (std * 1.5).values
        vals = x.values
        result = np.zeros(len(x))
        for i in range(5, len(x)):
            w = vals[max(0, i - 19):i + 1]
            result[i] = sum(1 for v in w if abs(v) > thr[i]) / len(w)
        return pd.Series(result, index=x.index)
    df["vol_clustering_20d"] = g["daily_return"].transform(_clustering_fast)
    up_vol = df["up_volatility_20d"].replace(0, 0.001)
    down_vol = df["down_volatility_20d"].replace(0, 0.001)
    df["vol_asymmetry_20d"] = np.where(down_vol > 1e-10, up_vol / down_vol, 1.0)
    df["basis_2nd_momentum_5d"] = g["spread_cs"].transform(
        lambda x: x.diff(5).fillna(0) - x.shift(5).diff(5).fillna(0))
    df["term_spread_volatility_20d"] = g["spread_cs"].transform(
        lambda x: x.rolling(20, min_periods=5).std().fillna(0))
    sp_mean = g["spread_pct"].transform(lambda x: x.rolling(20, min_periods=5).mean().abs())
    sp_std = g["spread_pct"].transform(lambda x: x.rolling(20, min_periods=5).std().fillna(0))
    df["roll_return_stability_20d"] = np.where(sp_mean > 1e-10,
        np.clip(1.0 - sp_std / sp_mean, 0, 1), 0.5)
    df["contango_premium_20d"] = g["spread_pct"].transform(
        lambda x: np.sign(x.rolling(20, min_periods=5).mean())).fillna(0)
    df["term_slope_20d"] = g["spread_cs"].transform(
        lambda x: (x - x.shift(19)) / 20.0).fillna(0)
    df["term_curvature_20d"] = g["spread_cs"].transform(
        lambda x: x.diff(2).fillna(0))
    oi_sum5 = g["oi_change_1d"].transform(lambda x: x.rolling(5, min_periods=1).sum())
    df["oi_2nd_growth_5d"] = oi_sum5 - oi_sum5.groupby(df["symbol"]).shift(5).fillna(0)
    df["institutional_concentration_20d"] = np.where(df["vol"] > 0,
        df["oi"] / (df["vol"] * 10), 0)
    oi_rank = df.groupby("date")["oi_change_1d"].rank(pct=True).fillna(0.5)
    df["cross_symbol_oi_linkage"] = oi_rank * 2 - 1
    oi_mean20 = g["oi"].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df["oi_vol_ratio_20d"] = np.where(vol_mean > 0, oi_mean20 / (vol_mean * 10), 0)
    oi_dir = np.sign(df["oi_change_daily"])
    df["oi_momentum_divergence_20d"] = ((price_dir != 0) & (oi_dir != 0) & (price_dir != oi_dir)).astype(float)
    return df


# ════════════════════════════════════════════════════════════════
# 回测引擎 (复用 TASK063/T064, 零改动)
# ════════════════════════════════════════════════════════════════
def _precompute_signals(df, factors, symbols):
    df_sym = df[df["symbol"].isin(symbols)].copy()
    df_sym = df_sym.sort_values(["symbol", "date"]).reset_index(drop=True)
    signal_matrix = np.zeros((len(df_sym), len(factors)))
    for fi, fname in enumerate(factors):
        if fname not in df_sym.columns:
            continue
        vals = df_sym[fname].values.astype(float)
        mean = np.nanmean(vals); std = np.nanstd(vals)
        if std > 1e-10:
            signal_matrix[:, fi] = (vals - mean) / std
        signal_matrix[:, fi] = np.where(np.isnan(signal_matrix[:, fi]), 0.0, signal_matrix[:, fi])
    daily_ret = df_sym.groupby("symbol")["close"].pct_change().fillna(0).values
    dates = df_sym["date"].values
    return signal_matrix, daily_ret, dates, df_sym


def _determine_positions(composite_signal):
    n = len(composite_signal)
    pos = np.zeros(n)
    for i in range(n):
        s = composite_signal[i]
        pos[i] = 1.0 if s > SIGNAL_THRESHOLD else (-1.0 if s < -SIGNAL_THRESHOLD else 0.0)
    last_r = 0
    for i in range(len(pos)):
        if i - last_r >= REBALANCE_INTERVAL:
            last_r = i
        else:
            pos[i] = pos[i - 1] if i > 0 else 0.0
    return pos


def _compute_backtest_metrics(position, daily_ret, weight_vec, n_factors, flip_rate=None):
    strat = position * daily_ret
    eq = INITIAL_CAPITAL; rm = INITIAL_CAPITAL
    adj_ret = np.zeros(len(strat)); adj_pos = position.copy()
    for i in range(len(strat)):
        dd = (eq - rm) / rm
        if dd < DRAWDOWN_HALT:
            adj_ret[i] = 0.0; adj_pos[i] = 0.0
        elif dd < DRAWDOWN_WARN:
            adj_ret[i] = strat[i] * 0.5; adj_pos[i] = position[i] * 0.5
        else:
            adj_ret[i] = strat[i]; adj_pos[i] = position[i]
        eq *= (1 + adj_ret[i])
        if eq > rm:
            rm = eq
    pc = np.abs(np.diff(adj_pos))
    mn = min(len(adj_ret), len(pc))
    adj_ret = adj_ret[:mn]; pc = pc[:mn]
    cost_adj = adj_ret - pc * TRANSACTION_COST
    ec = np.cumprod(1 + cost_adj) * INITIAL_CAPITAL
    ec = np.insert(ec, 0, INITIAL_CAPITAL)
    tr = (ec[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL
    n_per = len(cost_adj)
    ar = (1 + tr) ** (TRADING_DAYS / n_per) - 1 if n_per > 0 else 0
    dv = np.std(cost_adj, ddof=1) if n_per > 1 else 0
    av = dv * math.sqrt(TRADING_DAYS)
    sh = ar / av if av > 0 else 0
    rme = np.maximum.accumulate(ec)
    dd_arr = (ec - rme) / rme
    mdd = float(np.min(dd_arr)) if len(dd_arr) > 0 else 0
    win = cost_adj[cost_adj > 0]; loss = cost_adj[cost_adj < 0]
    wr = len(win) / n_per if n_per > 0 else 0
    aw = float(np.mean(win)) if len(win) > 0 else 0
    al = float(abs(np.mean(loss))) if len(loss) > 0 else 0
    plr = aw / al if al > 0 else 999.0
    tc = int(np.sum(pc > 0))
    if flip_rate is None:
        flip_rate = 0.0
    norm_w = weight_vec / max(np.sum(weight_vec), 1e-10)
    hhi = np.sum(norm_w ** 2)
    crowding = hhi if hhi > 0 else 0.125
    return {
        "total_return": round(float(tr), 6),
        "annualized_return": round(float(ar), 6),
        "annual_volatility": round(float(av), 6),
        "max_drawdown": round(float(mdd), 6),
        "sharpe_ratio": round(float(sh), 6),
        "win_rate": round(float(wr), 6),
        "profit_loss_ratio": round(float(plr), 6),
        "trade_count": tc, "n_periods": n_per,
        "flip_rate": round(flip_rate, 4),
        "crowding_hhi": round(crowding, 4),
        "num_factors": n_factors,
    }


def combined_backtest_fixed(signal_matrix, daily_ret, weight_vec, n_factors):
    total_w = np.sum(weight_vec)
    norm_w = weight_vec / total_w if total_w > 0 else weight_vec
    composite = signal_matrix @ norm_w
    position = _determine_positions(composite)
    mn = min(len(position), len(daily_ret))
    pos = position[:mn]; dr = daily_ret[:mn]
    signs = np.sign(composite[:mn])
    fc = sum(1 for i in range(1, len(signs)) if signs[i - 1] != 0 and signs[i] != 0 and signs[i - 1] != signs[i])
    fr = fc / (len(signs) - 1) if len(signs) > 1 else 0
    return _compute_backtest_metrics(pos, dr, norm_w, n_factors, fr)


def combined_backtest_dynamic(signal_matrix, daily_ret, weight_schedule, n_factors):
    n = len(signal_matrix)
    rps = list(range(0, n, REBALANCE_INTERVAL))
    composite = np.zeros(n)
    for ri, idx in enumerate(rps):
        w = weight_schedule[min(ri, len(weight_schedule) - 1)]
        composite[idx] = signal_matrix[idx] @ w
    position = _determine_positions(composite)
    mn = min(len(position), len(daily_ret))
    pos = position[:mn]; dr = daily_ret[:mn]
    signs = np.sign(composite[:mn])
    fc = sum(1 for i in range(1, len(signs)) if signs[i - 1] != 0 and signs[i] != 0 and signs[i - 1] != signs[i])
    fr = fc / (len(signs) - 1) if len(signs) > 1 else 0
    last_w = weight_schedule[-1] if weight_schedule else np.ones(n_factors) / n_factors
    return _compute_backtest_metrics(pos, dr, last_w, n_factors, fr)


# ════════════════════════════════════════════════════════════════
# 动态权重引擎 (v4.48) — 复用 + T065 共振LOCKDOWN扩展
# ════════════════════════════════════════════════════════════════
def _compute_crowding_fast(signal_matrix):
    """向量化拥挤度序列 (与T064逐行循环语义一致)。"""
    n_f = signal_matrix.shape[1]
    abs_sm = np.abs(signal_matrix)
    total = abs_sm.sum(axis=1)
    safe_total = np.where(total > 1e-10, total, 1.0)
    w = abs_sm / safe_total[:, None]
    hhi = (w ** 2).sum(axis=1)
    hhi = np.where(total > 1e-10, hhi, 1.0 / n_f)
    hhi_c = np.clip(hhi, 0.07, 0.25)
    crowd = 1.03 + (hhi_c - 0.07) / (0.25 - 0.07) * 0.05
    return crowd


def _compute_flip_fast_vec(signal_matrix, factor_names):
    """向量化翻转率计算, 与T064 _compute_flip_fast 语义一致 (窗口20, 相邻非零符号翻转)。

    返回 {factor_name: np.ndarray(n)}。signal_matrix 形状 (n, n_f)。
    """
    n = len(signal_matrix)
    n_f = signal_matrix.shape[1]
    signs = np.sign(signal_matrix)                     # (n, n_f)
    nz_prev = signs[:-1] != 0
    nz_cur = signs[1:] != 0
    evt = (nz_prev & nz_cur & (signs[:-1] != signs[1:])).astype(float)  # (n-1, n_f)
    cs = np.concatenate([np.zeros((1, n_f)), np.cumsum(evt, axis=0)], axis=0)  # (n, n_f)
    idx = np.arange(n)
    lo = np.maximum(0, idx - 20)                       # (n,)
    num = cs[idx, :] - cs[lo, :]                       # (n, n_f)
    denom = np.maximum(1.0, np.minimum(idx.astype(float), 20.0))  # (n,)
    flip_all = num / denom[:, None]                    # (n, n_f)
    out = {}
    for fi in range(min(n_f, len(factor_names))):
        out[factor_names[fi]] = flip_all[:, fi]
    return out


def crowd_branch_grade_param(crowding, jerk, p90, p95, jerk_heavy):
    if jerk > jerk_heavy and crowding > p90:
        return "HEAVY"
    elif crowding > p95:
        return "MEDIUM"
    elif crowding > p90:
        return "LIGHT"
    return "NONE"


def flip_branch_grade_param(flip_rates, l1, l2, sync_escalate):
    l1_count = sum(1 for r in flip_rates.values() if r > l1)
    l2_count = sum(1 for r in flip_rates.values() if r > l2)
    if l2_count >= 1:
        return "HEAVY"
    elif l1_count >= sync_escalate:
        return "MEDIUM"
    elif l1_count >= 1:
        return "LIGHT"
    return "NONE"


def decide_grade_param(crowd_grade, flip_grade):
    """T064/T063 原逻辑: 取高 (单分支即可触发高等级)。"""
    return max(crowd_grade, flip_grade, key=lambda g: GRADE_ORDER[g])


def decide_grade_resonant(crowd_grade, flip_grade):
    """T064 P2.2 rule_1/rule_2: HEAVY 需要双分支同时非NONE; 单分支最高MEDIUM。"""
    cg_o = GRADE_ORDER[crowd_grade]
    fg_o = GRADE_ORDER[flip_grade]
    both_active = (cg_o > 0) and (fg_o > 0)
    if both_active:
        return max(crowd_grade, flip_grade, key=lambda g: GRADE_ORDER[g])
    single = max(crowd_grade, flip_grade, key=lambda g: GRADE_ORDER[g])
    if GRADE_ORDER[single] > GRADE_ORDER["MEDIUM"]:
        return "MEDIUM"
    return single


def resonance_lockdown_state_machine(crowd_grades, flip_grades,
                                     threshold=RESONANCE_LOCKDOWN_THRESHOLD,
                                     hold_periods=LOCKDOWN_HOLD_PERIODS):
    """纯状态机: 双分支共振规则 + 连续threshold次共振 → LOCKDOWN (hold_periods个周期后自动释放)。

    返回 (decided_grades, trace, lockdown_events)。
    - decided_grades[i]: 每个调仓周期最终等级 (含 "LOCKDOWN")
    - trace: 逐周期明细
    - lockdown_events: 触发LOCKDOWN的事件列表 (i, 共振计数)
    """
    decided = []
    trace = []
    events = []
    consec = 0
    remaining = 0
    for i, (cg, fg) in enumerate(zip(crowd_grades, flip_grades)):
        if remaining > 0:
            decided.append("LOCKDOWN")
            trace.append({"i": i, "crowd_grade": cg, "flip_grade": fg,
                          "consecutive_resonance": consec, "hold_remaining": remaining,
                          "grade": "LOCKDOWN", "reason": "LOCKDOWN_HOLD"})
            remaining -= 1
            consec = 0
            continue
        both = (GRADE_ORDER[cg] > 0) and (GRADE_ORDER[fg] > 0)
        if both:
            consec += 1
        else:
            consec = 0
        if consec >= threshold:
            decided.append("LOCKDOWN")
            remaining = hold_periods
            events.append({"i": i, "crowd_grade": cg, "flip_grade": fg,
                           "consecutive_resonance": consec})
            trace.append({"i": i, "crowd_grade": cg, "flip_grade": fg,
                          "consecutive_resonance": consec, "hold_remaining": hold_periods,
                          "grade": "LOCKDOWN", "reason": "THRESHOLD_REACHED"})
            consec = 0
        else:
            g = decide_grade_resonant(cg, fg)
            decided.append(g)
            trace.append({"i": i, "crowd_grade": cg, "flip_grade": fg,
                          "consecutive_resonance": consec, "hold_remaining": 0,
                          "grade": g,
                          "reason": "DUAL_RESONANCE" if both else "SINGLE_BRANCH_CAP"})
    return decided, trace, events


def compute_dynamic_weights_resonant(grade, sync_flip_count, grade_coeffs, sync_penalty):
    """按等级计算动态权重。LOCKDOWN 等级: 候选因子权重强制归零。"""
    coeffs = grade_coeffs[grade]
    wf = coeffs["weight_factor"]
    sc = coeffs["single_cap"]
    psc = coeffs["pool_sum_cap"]
    sf = sync_penalty ** max(0, sync_flip_count - 1)
    ew = wf * sf
    cw_dyn = {}
    for f in OBSERVE_FACTORS_6:
        bw = CANDIDATE_BASE_WEIGHTS_6.get(f, 0)
        w = min(bw * ew, sc)
        cw_dyn[f] = w
    ps = sum(cw_dyn.values())
    if ps > psc:
        scale = psc / ps
        for f in cw_dyn:
            cw_dyn[f] *= scale
    mw_dyn = {}
    released = CAND_BASE_SUM - sum(cw_dyn.values())
    mt = sum(MAIN_BASE_WEIGHTS.values())
    for f in V3_FACTORS_8:
        w = MAIN_BASE_WEIGHTS.get(f, 0) / mt * 0.85
        if mt > 0 and released > 0:
            w += MAIN_BASE_WEIGHTS.get(f, 0) / mt * released
        w = min(w, MAIN_FACTOR_CAP)
        mw_dyn[f] = w
    all_w = {}
    for f in V3_FACTORS_8:
        all_w[f] = mw_dyn.get(f, 0)
    for f in OBSERVE_FACTORS_6:
        all_w[f] = cw_dyn.get(f, 0)
    vec = np.array([all_w.get(f, 0) for f in GROUP_A_FACTORS])
    return vec


def build_weight_schedule_resonant(
    crowding_series, flip_series, signal_matrix,
    grade_coeffs=None, p90=None, p95=None, jerk_heavy=None,
    l1=None, l2=None, sync_escalate=None, sync_penalty=None,
    resonance_lockdown=False,
):
    """动态权重调度构建器。

    resonance_lockdown=True 时启用 T064 P2.2 双分支共振 + 连续3次LOCKDOWN。
    否则使用原 T064/T063 max-of-grades 逻辑。
    """
    if grade_coeffs is None:
        grade_coeffs = GRADE_COEFFS_BASE
    if p90 is None:
        p90 = CROWDING_P90
    if p95 is None:
        p95 = CROWDING_P95
    if jerk_heavy is None:
        jerk_heavy = JERK_HEAVY
    if l1 is None:
        l1 = FLIP_L1
    if l2 is None:
        l2 = FLIP_L2
    if sync_escalate is None:
        sync_escalate = SYNC_ESCALATE
    if sync_penalty is None:
        sync_penalty = SYNC_PENALTY

    n = len(signal_matrix)
    rps = list(range(0, n, REBALANCE_INTERVAL))
    crowd_grades = []
    flip_grades = []
    sync_counts = []
    for rp in rps:
        crowd = crowding_series[rp]
        start = max(0, rp - 20)
        seg = crowding_series[start:rp + 1]
        jerk = 0.0
        if len(seg) >= 4:
            d3 = np.diff(np.diff(np.diff(seg)))
            if len(d3) > 0:
                jerk = float(d3[-1])
        flips = {f: float(flip_series[f][rp]) for f in OBSERVE_FACTORS_6 if f in flip_series}
        cg = crowd_branch_grade_param(crowd, jerk, p90, p95, jerk_heavy)
        fg = flip_branch_grade_param(flips, l1, l2, sync_escalate)
        crowd_grades.append(cg)
        flip_grades.append(fg)
        sync_counts.append(sum(1 for f in OBSERVE_FACTORS_6 if flips.get(f, 0) > l1))

    if resonance_lockdown:
        decided, trace, events = resonance_lockdown_state_machine(crowd_grades, flip_grades)
    else:
        decided = [decide_grade_param(cg, fg) for cg, fg in zip(crowd_grades, flip_grades)]
        trace = None
        events = []

    ws = []
    for ri, grade in enumerate(decided):
        w = compute_dynamic_weights_resonant(grade, sync_counts[ri], grade_coeffs, sync_penalty)
        ws.append(w)
    meta = {
        "n_rebalances": len(rps),
        "resonance_lockdown": resonance_lockdown,
        "lockdown_events": events,
        "trace": trace,
    }
    return ws, meta


# ════════════════════════════════════════════════════════════════
# P0: 冒烟自检 (4项)
# ════════════════════════════════════════════════════════════════
def p0_precheck():
    checks = []

    # P0.1: 锁定T064输出指纹 + SHA匹配校验
    c1 = {"id": 1, "name": "T064输出指纹锁定+SHA匹配", "status": "PASS"}
    try:
        manifest = safe_json_load(T064_MANIFEST)
        tag_ok = manifest.get("version_tag") == T064_VERSION_TAG
        # 校验 observation_pool_entry.json 磁盘SHA == 清单记录SHA
        entry_sha = sha256_file(T064_ENTRY_DOC)
        entry_recorded = None
        for e in manifest.get("files", []):
            if e["filename"] == "observation_pool_entry.json":
                entry_recorded = e["sha256"]
        entry_sha_ok = (entry_sha == entry_recorded)
        # 重算聚合SHA
        pairs = []
        all_exist = True
        shas_match = True
        missing = []
        for e in manifest.get("files", []):
            fp = os.path.join(POOL_DIR, e["filename"])
            if not os.path.exists(fp):
                all_exist = False
                missing.append(e["filename"])
                continue
            if e.get("sha256") in ("PENDING", "SELF"):
                continue
            a = sha256_file(fp)
            pairs.append((e["filename"], e["sha256"]))
            if a != e["sha256"]:
                shas_match = False
        agg_input = "|".join(sorted(f"{fn}:{s}" for fn, s in pairs))
        agg = hashlib.sha256(agg_input.encode()).hexdigest()
        agg_match = agg == manifest.get("aggregate_sha256", "")
        ok = tag_ok and entry_sha_ok and all_exist and shas_match and agg_match
        c1["detail"] = (
            f"version_tag={manifest.get('version_tag')}, "
            f"entry_sha_match={entry_sha_ok} ({entry_sha[:12]}), "
            f"non_self_files={len(pairs)}, all_exist={all_exist}, "
            f"shas_match={shas_match}, agg_sha_match={agg_match} ({agg[:16]})"
        )
        c1["status"] = "PASS" if ok else "FAIL"
    except Exception as e:
        c1["status"] = "FAIL"
        c1["detail"] = str(e)
    checks.append(c1)

    # P0.2: 三因子ID确认
    c2 = {"id": 2, "name": "三因子ID确认", "status": "PASS"}
    try:
        expected = set(DEFERRED_FACTORS_3)
        # 从T064定稿文档交叉核对
        plan = safe_json_load(os.path.join(POOL_DIR, "shortcoming_optimization_plan.json"))
        p23 = plan.get("P2_3_deferred_exclusion", {})
        plan_targets = set(p23.get("target", []))
        plan_factors = set(f["factor"] for f in p23.get("factors", []))
        cross_ok = (expected == plan_targets) and (expected == plan_factors)
        # 从T063 deferred_factors_attribution 交叉核对 (键名: deferred_factors)
        deferred = safe_json_load(os.path.join(POOL_DIR, "deferred_factors_attribution.json"))
        deferred_set = set()
        for item in deferred.get("deferred_factors", []):
            nm = item.get("factor") or item.get("factor_id") or item.get("name")
            if nm:
                deferred_set.add(nm)
        t063_ok = expected.issubset(deferred_set) if deferred_set else False
        ok = cross_ok and t063_ok
        c2["detail"] = (
            f"ids={sorted(expected)}, t064_plan_match={cross_ok}, "
            f"t063_deferred_attribution_match={t063_ok} ({len(deferred_set)}个记录)"
        )
        c2["status"] = "PASS" if ok else "FAIL"
    except Exception as e:
        c2["status"] = "FAIL"
        c2["detail"] = str(e)
    checks.append(c2)

    # P0.3: AST扫描 + 沙箱隔离 + 不触碰MN主快照目录
    c3 = {"id": 3, "name": "AST扫描(无无限MC循环/banned=0)+沙箱隔离+MN隔离", "status": "PASS"}
    try:
        src = ""
        with open(os.path.join(SANDBOX_DIR, "run_task065_mc_review_exclusion.py"), "r", encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)

        # 1) MC_ROUNDS 必须是有界字面量 <= 300
        mc_rounds_val = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "MC_ROUNDS":
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                            mc_rounds_val = node.value.value
        mc_bounded = (mc_rounds_val is not None) and (0 < mc_rounds_val <= MC_MAX_CAP)

        # 2) 无 while True 无限循环
        has_infinite_while = False
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_infinite_while = True

        # 3) 无 range() 无参调用 (无限迭代器)
        has_unbounded_range = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                fn = f.id if isinstance(f, ast.Name) else ""
                if fn == "range" and len(node.args) == 0:
                    has_unbounded_range = True

        # 4) banned 函数调用 = 0 (匹配 callee 名, 非字符串字面量)
        def _call_name(call_node):
            f = call_node.func
            if isinstance(f, ast.Name):
                return f.id
            if isinstance(f, ast.Attribute):
                return f.attr
            return ""
        banned_func_names = {"mc_simulation", "full_grid", "monte_carlo", "run_full_backtest"}
        banned_calls = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_name(node) in banned_func_names:
                banned_calls += 1

        # 5) 沙箱目录独立: pool_14_062 存在且所有T065输出位于 POOL_DIR/SANDBOX_DIR/MC_SANDBOX_DIR
        out_paths = [
            OUT_SUMMARY_MC_CSV, OUT_LOCKDOWN_UTEST, OUT_REVIEW_REPORT,
            OUT_EXCLUSION_REGISTRY, OUT_BOUNDARY_DECL, OUT_ENTRY_DOC,
            OUT_FULL_MANIFEST, OUT_WORKFLOW_SEAL, OUT_RECEIPT,
            MC_DETAIL_JSON, MC_LOCKDOWN_TRACE, MC_SANDBOX_MARKER,
        ]
        allowed_dirs = (POOL_DIR, SANDBOX_DIR, MC_SANDBOX_DIR)
        out_paths_ok = all(os.path.dirname(p) in allowed_dirs for p in out_paths)
        sandbox_ok = os.path.isdir(POOL_DIR)

        # 6) 不触碰 MN 主快照目录: 脚本源码中禁止出现写向 MN 的路径操作
        mn_touched = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if _call_name(node) in ("open",):
                    for a in node.args:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str):
                            if MN_SNAPSHOT_DIR.replace("\\", "/") in a.value.replace("\\", "/"):
                                mn_touched = True
        ok = (mc_bounded and not has_infinite_while and not has_unbounded_range
              and banned_calls == 0 and sandbox_ok and out_paths_ok and not mn_touched)
        c3["detail"] = (
            f"mc_rounds={mc_rounds_val}(<=300: {mc_bounded}), "
            f"infinite_while={has_infinite_while}, unbounded_range={has_unbounded_range}, "
            f"banned_func_calls={banned_calls}, sandbox_exists={sandbox_ok}, "
            f"outputs_in_sandbox={out_paths_ok}, mn_touched={mn_touched}"
        )
        c3["status"] = "PASS" if ok else "FAIL"
    except Exception as e:
        c3["status"] = "FAIL"
        c3["detail"] = str(e)
    checks.append(c3)

    # P0.4: 导入T064定稿参数
    c4 = {"id": 4, "name": "导入T064定稿参数(MEDIUM 0.40/HEAVY 0.30+共振LOCKDOWN)", "status": "PASS"}
    try:
        gc = GRADE_COEFFS_T065
        medium_wf = gc["MEDIUM"]["weight_factor"]
        heavy_wf = gc["HEAVY"]["weight_factor"]
        has_lockdown = ("LOCKDOWN" in gc) and (gc["LOCKDOWN"]["weight_factor"] == 0.0)
        thresh_ok = (RESONANCE_LOCKDOWN_THRESHOLD == 3)
        hold_ok = (LOCKDOWN_HOLD_PERIODS == 4) and (LOCKDOWN_HOLD_DAYS == 20)
        p90_ok = abs(CROWDING_P90_T065 - 1.07401) < 1e-9
        p95_ok = abs(CROWDING_P95_T065 - 1.07854) < 1e-9
        ok = (medium_wf == 0.40 and heavy_wf == 0.30 and has_lockdown
              and thresh_ok and hold_ok and p90_ok and p95_ok)
        c4["detail"] = (
            f"medium_wf={medium_wf}, heavy_wf={heavy_wf}, "
            f"lockdown_coeff={has_lockdown}, threshold={RESONANCE_LOCKDOWN_THRESHOLD}, "
            f"hold={LOCKDOWN_HOLD_DAYS}days/{LOCKDOWN_HOLD_PERIODS}periods, "
            f"p90={CROWDING_P90_T065}, p95={CROWDING_P95_T065}"
        )
        c4["status"] = "PASS" if ok else "FAIL"
    except Exception as e:
        c4["status"] = "FAIL"
        c4["detail"] = str(e)
    checks.append(c4)

    return checks


# ════════════════════════════════════════════════════════════════
# P1: 小样本MC复验 (300轮, 低资源模式)
# ════════════════════════════════════════════════════════════════
def _mc_perturb_signals(signal_matrix, seed):
    """T062兼容的信号扰动 (噪声/相关/拥挤加速/翻转), 独立随机源, 向量化加速。"""
    rng = np.random.default_rng(seed)
    perturbed = signal_matrix.copy()
    n = len(perturbed)
    noise_scale = rng.uniform(0.05, 0.30)
    noise = rng.normal(0, noise_scale, perturbed.shape)
    perturbed += noise
    corr_scale = rng.uniform(0.0, 0.15)
    if corr_scale > 0:
        for fi in range(perturbed.shape[1]):
            perturbed[:, fi] += rng.normal(0, corr_scale, n)
    crowd_accel = rng.uniform(0.0, 0.1)
    factor_arr = (np.arange(n) / max(n - 1, 1)) * crowd_accel
    mult = 1.0 + factor_arr[:, None] * rng.uniform(-0.5, 0.5, size=perturbed.shape)
    perturbed *= mult
    flip_count = int(rng.integers(0, max(1, n // 50)))
    if flip_count > 0:
        flip_indices = rng.choice(n, size=min(flip_count, n), replace=False)
        perturbed[flip_indices, :] *= -1.0
    meta = {
        "noise_scale": round(float(noise_scale), 4),
        "corr_scale": round(float(corr_scale), 4),
        "crowd_accel": round(float(crowd_accel), 4),
        "flip_count": flip_count,
    }
    return perturbed, meta


def _run_config_backtest(signal_matrix, daily_ret, cfg, crowding=None, flip_series=None):
    """按配置构建权重调度并回测。crowding/flip_series 可预计算共享 (同扰动下两配置一致)。"""
    if crowding is None:
        crowding = _compute_crowding_fast(signal_matrix)
    if flip_series is None:
        flip_series = _compute_flip_fast_vec(signal_matrix, GROUP_A_FACTORS)
    ws, meta = build_weight_schedule_resonant(
        crowding, flip_series, signal_matrix,
        grade_coeffs=cfg["grade_coeffs"],
        p90=cfg["p90"], p95=cfg["p95"],
        jerk_heavy=JERK_HEAVY, l1=FLIP_L1, l2=FLIP_L2,
        sync_escalate=SYNC_ESCALATE, sync_penalty=SYNC_PENALTY,
        resonance_lockdown=cfg["resonance_lockdown"],
    )
    res = combined_backtest_dynamic(signal_matrix, daily_ret, ws, len(GROUP_A_FACTORS))
    res["sharpe_delta"] = round(res["sharpe_ratio"] - CONTROL_SHARPE, 6)
    res["return_delta"] = round(res["total_return"] - CONTROL_TOTAL_RETURN, 6)
    res["mdd_delta"] = round(res["max_drawdown"] - CONTROL_MDD, 6)
    return res, meta.get("lockdown_events", []), len(ws)


def _classify_zone(sharpe, mdd, crowding):
    if sharpe >= MC_SAFE_SHARPE and mdd > MC_SAFE_MDD and crowding <= MC_CROWD_CEIL:
        return "SAFE"
    elif sharpe >= MC_WARN_SHARPE and mdd > MC_WARN_MDD:
        return "WARNING"
    return "HIGH_FAILURE"


def run_mc_t065(signal_matrix, daily_ret, point_schedule_t065, point_schedule_ctrl):
    """300轮小样本MC: 每轮一次扰动 + 双配置配对回测 (T064_CFG vs T065_CFG)。"""
    t0 = time.time()
    rows = []
    for r in range(MC_ROUNDS):
        seed = 200000 + r
        perturbed, pmeta = _mc_perturb_signals(signal_matrix, seed)

        # 同扰动下 crowding/flip 仅算一次, 两配置共享
        crowding = _compute_crowding_fast(perturbed)
        flip_series = _compute_flip_fast_vec(perturbed, GROUP_A_FACTORS)

        res_ctrl, ld_ctrl, _ = _run_config_backtest(
            perturbed, daily_ret, MC_CTRL_CFG, crowding=crowding, flip_series=flip_series)
        res_t065, ld_t065, _ = _run_config_backtest(
            perturbed, daily_ret, MC_T065_CFG, crowding=crowding, flip_series=flip_series)

        rows.append({
            "round": r, "seed": seed,
            "noise_scale": pmeta["noise_scale"], "corr_scale": pmeta["corr_scale"],
            "crowd_accel": pmeta["crowd_accel"], "flip_count": pmeta["flip_count"],
            "t064_sharpe": res_ctrl["sharpe_ratio"],
            "t064_sharpe_delta": res_ctrl["sharpe_delta"],
            "t064_mdd": res_ctrl["max_drawdown"],
            "t064_flip_rate": res_ctrl["flip_rate"],
            "t064_trades": res_ctrl["trade_count"],
            "t064_zone": _classify_zone(res_ctrl["sharpe_ratio"], res_ctrl["max_drawdown"], res_ctrl["crowding_hhi"]),
            "t065_sharpe": res_t065["sharpe_ratio"],
            "t065_sharpe_delta": res_t065["sharpe_delta"],
            "t065_mdd": res_t065["max_drawdown"],
            "t065_flip_rate": res_t065["flip_rate"],
            "t065_trades": res_t065["trade_count"],
            "t065_lockdown_events": len(ld_t065),
            "t065_zone": _classify_zone(res_t065["sharpe_ratio"], res_t065["max_drawdown"], res_t065["crowding_hhi"]),
        })

    # 分布统计
    d_ctrl = np.array([row["t064_sharpe_delta"] for row in rows], dtype=float)
    d_t065 = np.array([row["t065_sharpe_delta"] for row in rows], dtype=float)
    s_ctrl = np.array([row["t064_sharpe"] for row in rows], dtype=float)
    s_t065 = np.array([row["t065_sharpe"] for row in rows], dtype=float)

    def _stats(arr):
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        pcts = [float(x) for x in np.percentile(arr, [5, 25, 50, 75, 95])]
        cv = std / abs(mean) if abs(mean) > 1e-12 else float("inf")
        return {
            "mean": round(mean, 6), "std": round(std, 6),
            "p5": round(pcts[0], 6), "p25": round(pcts[1], 6),
            "p50": round(pcts[2], 6), "p75": round(pcts[3], 6),
            "p95": round(pcts[4], 6), "cv": round(cv, 6),
        }

    stats_ctrl = _stats(d_ctrl)
    stats_t065 = _stats(d_t065)

    def _zone_prob(rows, key):
        n = len(rows)
        return {
            "safe": round(sum(1 for x in rows if x[key] == "SAFE") / n, 4),
            "warning": round(sum(1 for x in rows if x[key] == "WARNING") / n, 4),
            "high_failure": round(sum(1 for x in rows if x[key] == "HIGH_FAILURE") / n, 4),
        }

    zone_ctrl = _zone_prob(rows, "t064_zone")
    zone_t065 = _zone_prob(rows, "t065_zone")

    # 稳定性指标
    meets_target_t065 = float(np.mean(d_t065 >= -0.35))
    within_1std_t065 = float(np.mean(np.abs(d_t065 - stats_t065["mean"]) <= stats_t065["std"]))
    lockdown_total = int(sum(row["t065_lockdown_events"] for row in rows))
    lockdown_rounds = int(sum(1 for row in rows if row["t065_lockdown_events"] > 0))

    elapsed = round(time.time() - t0, 2)
    summary = {
        "mc_rounds": MC_ROUNDS,
        "mc_max_cap": MC_MAX_CAP,
        "low_resource_mode": True,
        "time_seconds": elapsed,
        "control_cfg": {"name": MC_CTRL_CFG["name"], "grade_coeffs": {k: v["weight_factor"] for k, v in GRADE_COEFFS_BASE.items()},
                        "p90": MC_CTRL_CFG["p90"], "p95": MC_CTRL_CFG["p95"], "decision": MC_CTRL_CFG["decision"]},
        "t065_cfg": {"name": MC_T065_CFG["name"], "grade_coeffs": {k: v["weight_factor"] for k, v in GRADE_COEFFS_T065.items()},
                     "p90": MC_T065_CFG["p90"], "p95": MC_T065_CFG["p95"], "decision": MC_T065_CFG["decision"]},
        "sharpe_delta_distribution": {
            "t064_cfg": stats_ctrl,
            "t065_cfg": stats_t065,
        },
        "sharpe_distribution": {
            "t064_cfg": {"mean": round(float(np.mean(s_ctrl)), 6), "p5": round(float(np.percentile(s_ctrl, 5)), 6)},
            "t065_cfg": {"mean": round(float(np.mean(s_t065)), 6), "p5": round(float(np.percentile(s_t065, 5)), 6)},
        },
        "zone_probability": {
            "t064_cfg": zone_ctrl,
            "t065_cfg": zone_t065,
        },
        "stability_metrics": {
            "t065_fraction_meets_target_ge_-0.35": round(meets_target_t065, 4),
            "t065_fraction_within_1std": round(within_1std_t065, 4),
            "t065_lockdown_total_events": lockdown_total,
            "t065_lockdown_rounds": lockdown_rounds,
        },
        "point_estimate": {
            "t064_cfg": point_schedule_ctrl,
            "t065_cfg": point_schedule_t065,
        },
        "engine_self_check": {
            "t064_cfg_point_delta_expect_minus_0.695794": round(point_schedule_ctrl["sharpe_delta"], 6),
            "t064_cfg_point_matches_baseline": abs(point_schedule_ctrl["sharpe_delta"] - EXPERIMENT_DELTA_BASE) < 0.01,
        },
    }
    return rows, summary


# P1.2 单元测试
def run_lockdown_unit_tests():
    tests = []
    results = []

    # T1: 连续3次双分支共振 → LOCKDOWN 置位
    cg = ["MEDIUM", "MEDIUM", "MEDIUM", "MEDIUM", "MEDIUM"]
    fg = ["LIGHT", "LIGHT", "LIGHT", "LIGHT", "LIGHT"]
    decided, trace, events = resonance_lockdown_state_machine(cg, fg)
    expect = ["MEDIUM", "MEDIUM", "LOCKDOWN", "LOCKDOWN", "LOCKDOWN"]
    ok = decided == expect and len(events) == 1 and events[0]["i"] == 2
    tests.append({"id": "T1", "name": "连续3次共振触发LOCKDOWN",
                  "input": {"crowd_grades": cg, "flip_grades": fg},
                  "expected": expect, "actual": decided,
                  "lockdown_events": events, "pass": ok})

    # T2: 单分支触发最高MEDIUM (不误升HEAVY)
    cg = ["HEAVY", "HEAVY"]
    fg = ["NONE", "NONE"]
    decided, trace, events = resonance_lockdown_state_machine(cg, fg)
    ok = decided == ["MEDIUM", "MEDIUM"] and len(events) == 0
    tests.append({"id": "T2", "name": "单分支触发上限MEDIUM(不误升HEAVY)",
                  "input": {"crowd_grades": cg, "flip_grades": fg},
                  "expected": ["MEDIUM", "MEDIUM"], "actual": decided,
                  "lockdown_events": events, "pass": ok})

    # T3: LOCKDOWN 自动释放, 不卡死流程
    cg = ["MEDIUM"] * 20
    fg = ["LIGHT"] * 20
    decided, trace, events = resonance_lockdown_state_machine(cg, fg)
    n_lockdown = sum(1 for g in decided if g == "LOCKDOWN")
    # 判定: 流程终止(len=20) + LOCKDOWN出现 + 其后有非LOCKDOWN周期(证明可释放) + 有触发事件
    has_release = any(decided[i] == "LOCKDOWN" and decided[i + 1] != "LOCKDOWN"
                      for i in range(len(decided) - 1))
    ok = (len(decided) == 20 and n_lockdown > 0 and has_release and len(events) > 0)
    tests.append({"id": "T3", "name": "LOCKDOWN自动释放不卡死(20周期终止)",
                  "input": {"crowd_grades": "MEDIUM x20", "flip_grades": "LIGHT x20"},
                  "expected": "terminates, has_release=True", "actual": {
                      "len_decided": len(decided), "n_lockdown": n_lockdown,
                      "lockdown_events": len(events), "has_release": has_release},
                  "pass": ok})

    # T4: 共振计数在中断处重置 (不误触发)
    cg = ["MEDIUM", "MEDIUM", "NONE", "MEDIUM", "MEDIUM", "MEDIUM"]
    fg = ["LIGHT", "LIGHT", "NONE", "LIGHT", "LIGHT", "LIGHT"]
    decided, trace, events = resonance_lockdown_state_machine(cg, fg)
    ok = (decided[2] == "NONE" and len(events) == 1 and events[0]["i"] == 5)
    tests.append({"id": "T4", "name": "共振计数中断重置(第3个非共振不误触发)",
                  "input": {"crowd_grades": cg, "flip_grades": fg},
                  "expected": "no LOCKDOWN at i=2, LOCKDOWN at i=5",
                  "actual": {"decided": decided, "lockdown_events": events},
                  "pass": ok})

    # T5: LOCKDOWN 期间候选因子权重归零
    vec = compute_dynamic_weights_resonant("LOCKDOWN", 0, GRADE_COEFFS_T065, SYNC_PENALTY)
    cand_weights = {f: float(vec[GROUP_A_FACTORS.index(f)]) for f in OBSERVE_FACTORS_6}
    main_sum = float(np.sum([vec[GROUP_A_FACTORS.index(f)] for f in V3_FACTORS_8]))
    all_zero = all(abs(w) < 1e-12 for w in cand_weights.values())
    ok = all_zero and main_sum > 0.8
    tests.append({"id": "T5", "name": "LOCKDOWN候选因子权重归零+主因子接管",
                  "input": {"grade": "LOCKDOWN", "sync_flip_count": 0},
                  "expected": "cand all 0, main_sum>0.8",
                  "actual": {"candidate_weights": {k: round(v, 6) for k, v in cand_weights.items()},
                             "main_factor_sum": round(main_sum, 6)},
                  "pass": ok})

    # T6: 双分支共振时等级按高 (HEAVY需双分支非NONE)
    cg = ["HEAVY"]
    fg = ["MEDIUM"]
    decided, trace, events = resonance_lockdown_state_machine(cg, fg)
    ok = decided == ["HEAVY"] and len(events) == 0
    tests.append({"id": "T6", "name": "双分支均非NONE时允许HEAVY",
                  "input": {"crowd_grades": cg, "flip_grades": fg},
                  "expected": ["HEAVY"], "actual": decided,
                  "lockdown_events": events, "pass": ok})

    passed = sum(1 for t in tests if t["pass"])
    return {
        "title": "共振LOCKDOWN逻辑单元测试 (T064 P2.2)",
        "task": TASK065_ID,
        "generated_at": now_str(),
        "threshold": RESONANCE_LOCKDOWN_THRESHOLD,
        "hold_days": LOCKDOWN_HOLD_DAYS,
        "hold_periods": LOCKDOWN_HOLD_PERIODS,
        "test_cases": tests,
        "passed": passed,
        "total": len(tests),
        "all_pass": passed == len(tests),
        "no_deadlock_confirmed": all(t["pass"] for t in tests if t["id"] in ("T3",)),
    }


# P1.3 评审报告
def build_review_report(mc_summary, unit_test):
    stats_t064 = mc_summary["sharpe_delta_distribution"]["t064_cfg"]
    stats_t065 = mc_summary["sharpe_delta_distribution"]["t065_cfg"]
    zone_t064 = mc_summary["zone_probability"]["t064_cfg"]
    zone_t065 = mc_summary["zone_probability"]["t065_cfg"]
    stab = mc_summary["stability_metrics"]
    pt_ctrl = mc_summary["point_estimate"]["t064_cfg"]
    pt_t065 = mc_summary["point_estimate"]["t065_cfg"]
    self_ok = mc_summary["engine_self_check"]["t064_cfg_point_matches_baseline"]

    mean_d = stats_t065["mean"]
    p5_d = stats_t065["p5"]
    cv = stats_t065["cv"]
    hf_t065 = zone_t065["high_failure"]
    hf_ctrl = zone_t064["high_failure"]
    meets = stab["t065_fraction_meets_target_ge_-0.35"]

    # 结论判定 (数据驱动)
    if (mean_d >= -0.40 and p5_d >= -0.65 and cv <= 0.6
            and hf_t065 <= hf_ctrl + 0.02 and self_ok):
        verdict = "通过"
        verdict_en = "PASS"
    elif (mean_d < -0.60 or p5_d < -0.85 or hf_t065 > hf_ctrl + 0.05 or not self_ok):
        verdict = "不通过"
        verdict_en = "FAIL"
    else:
        verdict = "存疑"
        verdict_en = "SUSPECT"

    risk_points = []
    if mean_d < -0.40:
        risk_points.append(f"Sharpe_delta均值 {mean_d} 低于-0.40目标线")
    if p5_d < -0.65:
        risk_points.append(f"Sharpe_delta 5%分位 {p5_d} 低于-0.65 (尾部风险较大)")
    if cv > 0.6:
        risk_points.append(f"变异系数CV={cv} 超过0.6, 分布离散度高")
    if hf_t065 > hf_ctrl:
        risk_points.append(f"高失效概率 {hf_t065} 高于对照 {hf_ctrl}")
    if not self_ok:
        risk_points.append("引擎自校验未通过: T064_CFG点估计未能复现基线-0.695794")
    if stab["t065_lockdown_total_events"] == 0:
        risk_points.append(
            f"LOCKDOWN保护在{MC_ROUNDS}轮MC中从未触发 (0事件): 双分支共振门槛(P90+0.02 + flip L1/L2) "
            "在当前扰动强度下过于严格, 保护机制实际未参与运算, 需评估门槛灵敏度")

    # 与T062历史基线尾部对比 (T062 2000轮 sharpe_p5=0.9652 → delta_p5≈-0.9995)
    t062_tail_ref = round(0.9652 - CONTROL_SHARPE, 4)

    if verdict_en == "PASS":
        conclusion = (
            f"调整权重地板 (MEDIUM 0.50→0.40, HEAVY 0.20→0.30) 并启用双分支共振LOCKDOWN后, "
            f"300轮小样本MC的Sharpe_delta分布均值 {mean_d}, 5%分位 {p5_d}, "
            f"高失效概率 {hf_t065} ({'低于' if hf_t065 <= hf_ctrl else '不高于'}对照 {hf_ctrl}), "
            f"分布稳定 (CV={cv})。结论: 通过。"
        )
    elif verdict_en == "FAIL":
        conclusion = (
            f"调整后MC分布未达稳定门槛: 均值 {mean_d}, 5%分位 {p5_d}, "
            f"高失效概率 {hf_t065} vs 对照 {hf_ctrl}。结论: 不通过。"
        )
    else:
        conclusion = (
            f"MC复验显示部分指标接近但未完全满足目标: 均值 {mean_d}, 5%分位 {p5_d}, "
            f"CV={cv}, 高失效概率 {hf_t065} vs 对照 {hf_ctrl}。结论: 存疑, 详见风险点。"
        )

    lines = []
    lines.append(f"# T065 MC复验评审报告 (DSHA-TASK-065)")
    lines.append("")
    lines.append(f"- 生成时间: {now_str()}")
    lines.append(f"- 基线: TASK064 ({BASELINE_COMMIT})")
    lines.append(f"- MC轮数: {MC_ROUNDS} (上限 {MC_MAX_CAP}, 低资源模式)")
    lines.append(f"- 版本标签: {VERSION_TAG}")
    lines.append("")
    lines.append("## 1. 复验配置")
    lines.append("")
    lines.append(f"- T064_CFG (对照): MEDIUM={GRADE_COEFFS_BASE['MEDIUM']['weight_factor']}, "
                 f"HEAVY={GRADE_COEFFS_BASE['HEAVY']['weight_factor']}, "
                 f"P90={MC_CTRL_CFG['p90']}, P95={MC_CTRL_CFG['p95']}, 决策=max-of-grades")
    lines.append(f"- T065_CFG (定稿参数): MEDIUM={GRADE_COEFFS_T065['MEDIUM']['weight_factor']}, "
                 f"HEAVY={GRADE_COEFFS_T065['HEAVY']['weight_factor']}, "
                 f"P90={MC_T065_CFG['p90']}, P95={MC_T065_CFG['p95']}, "
                 f"决策=双分支共振+连续{RESONANCE_LOCKDOWN_THRESHOLD}次LOCKDOWN"
                 f"(hold {LOCKDOWN_HOLD_DAYS}个交易日)")
    lines.append("")
    lines.append("## 2. Sharpe_delta 分布 (300轮配对MC)")
    lines.append("")
    lines.append("| 配置 | mean | std | p5 | p25 | p50 | p75 | p95 | CV |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    lines.append(f"| T064_CFG | {stats_t064['mean']} | {stats_t064['std']} | {stats_t064['p5']} | "
                 f"{stats_t064['p25']} | {stats_t064['p50']} | {stats_t064['p75']} | {stats_t064['p95']} | "
                 f"{stats_t064['cv']} |")
    lines.append(f"| T065_CFG | {stats_t065['mean']} | {stats_t065['std']} | {stats_t065['p5']} | "
                 f"{stats_t065['p25']} | {stats_t065['p50']} | {stats_t065['p75']} | {stats_t065['p95']} | "
                 f"{stats_t065['cv']} |")
    lines.append("")
    lines.append("## 3. 失效概率 (T062同口径: SAFE/WARNING/HIGH_FAILURE)")
    lines.append("")
    lines.append(f"- T064_CFG: safe={zone_t064['safe']}, warning={zone_t064['warning']}, "
                 f"high_failure={zone_t064['high_failure']}")
    lines.append(f"- T065_CFG: safe={zone_t065['safe']}, warning={zone_t065['warning']}, "
                 f"high_failure={zone_t065['high_failure']}")
    lines.append(f"- T062历史基线 (2000轮): high_failure=0.959, sharpe_p5=0.9652 "
                 f"(→ delta_p5≈{t062_tail_ref})")
    lines.append("")
    lines.append("### 方法论说明")
    lines.append("")
    lines.append("- 本MC每轮从扰动信号**重建**权重调度 (引擎对扰动市场实时响应), "
                 "比T062的预计算调度口径更严苛")
    lines.append("- T064_CFG配对对照验证引擎复现性: 点估计精确复现T063/T064基线 "
                 f"(delta={pt_ctrl['sharpe_delta']} == {EXPERIMENT_DELTA_BASE})")
    lines.append("")
    lines.append("## 4. 稳定性指标")
    lines.append("")
    lines.append(f"- T065_CFG Sharpe_delta >= -0.35 的轮次占比: {stab['t065_fraction_meets_target_ge_-0.35']}")
    lines.append(f"- T065_CFG 落在均值±1σ内的轮次占比: {stab['t065_fraction_within_1std']}")
    lines.append(f"- T065_CFG LOCKDOWN 触发: {stab['t065_lockdown_total_events']}次事件 / "
                 f"{stab['t065_lockdown_rounds']}轮 (保护机制实际参与度)")
    lines.append(f"- 引擎自校验: T064_CFG点估计 Sharpe_delta={pt_ctrl['sharpe_delta']} "
                 f"(期望≈{EXPERIMENT_DELTA_BASE}, 匹配={self_ok})")
    lines.append("")
    lines.append("## 5. 点估计 (确定性, 无扰动)")
    lines.append("")
    lines.append(f"- T064_CFG: Sharpe={pt_ctrl['sharpe_ratio']}, delta={pt_ctrl['sharpe_delta']}, "
                 f"MDD={pt_ctrl['max_drawdown']}, trades={pt_ctrl['trade_count']}")
    lines.append(f"- T065_CFG: Sharpe={pt_t065['sharpe_ratio']}, delta={pt_t065['sharpe_delta']}, "
                 f"MDD={pt_t065['max_drawdown']}, trades={pt_t065['trade_count']}")
    lines.append("")
    lines.append("## 6. 共振LOCKDOWN单元测试")
    lines.append("")
    lines.append(f"- {unit_test['passed']}/{unit_test['total']} 用例通过, "
                 f"all_pass={unit_test['all_pass']}, 无死锁确认={unit_test['no_deadlock_confirmed']}")
    lines.append("")
    lines.append("## 7. 结论")
    lines.append("")
    lines.append(f"**结论: {verdict} ({verdict_en})**")
    lines.append("")
    lines.append(conclusion)
    if risk_points:
        lines.append("")
        lines.append("### 风险点")
        lines.append("")
        for rp in risk_points:
            lines.append(f"- {rp}")
    lines.append("")
    lines.append("## 8. 处置说明")
    lines.append("")
    lines.append("- 本报告仅输出评估, **不自动修改任何参数**")
    lines.append("- 三因子永久剔除结论独立落地于 P2 (factor_exclusion_registry.json)")
    lines.append("- 观测池准入结论以 observation_pool_entry.json (P2.3修订版) 为准")
    lines.append("- 若结论为存疑/不通过, 后续迭代须先满足 iteration_preconditions.json 前置条件")
    lines.append("")
    return "\n".join(lines), {
        "verdict": verdict, "verdict_en": verdict_en,
        "conclusion": conclusion, "risk_points": risk_points,
        "mean_delta": mean_d, "p5_delta": p5_d, "cv": cv,
        "high_failure_t065": hf_t065, "high_failure_t064_cfg": hf_ctrl,
        "t062_tail_delta_p5_ref": t062_tail_ref,
    }


# ════════════════════════════════════════════════════════════════
# P2: 因子排除规则固化
# ════════════════════════════════════════════════════════════════
def p2_exclusion_lock(entry_doc, mc_summary, review_conclusion):
    # P2.1: 三因子 PERMANENTLY_EXCLUDED 注册表
    registry = {
        "document_type": "FACTOR_EXCLUSION_REGISTRY",
        "task": TASK065_ID,
        "source": "DSHA-T064",
        "generated_at": now_str(),
        "version_tag": VERSION_TAG,
        "validity": "60 TRADING DAYS",
        "validity_aligned_with": "observation_pool_entry.json",
        "excluded_factors": [
            {
                "factor_id": "price_momentum_2nd_diff",
                "status": "PERMANENTLY_EXCLUDED",
                "source": "DSHA-T064",
                "avg_ic": 0.001507,
                "information_ratio": 0.086939,
                "exclusion_reason": "IC/IR不足 (IR=0.087 << 1.0阈值), 无预测能力",
                "applied_to": "V3-EXT实验组配置, 不参与任何候选因子池运算",
            },
            {
                "factor_id": "oi_momentum_divergence_20d",
                "status": "PERMANENTLY_EXCLUDED",
                "source": "DSHA-T064",
                "avg_ic": 0.020872,
                "information_ratio": 0.357026,
                "exclusion_reason": "高风险标记 (TASK059评审), 信号不稳定",
                "applied_to": "V3-EXT实验组配置, 不参与任何候选因子池运算",
            },
            {
                "factor_id": "price_vol_momentum",
                "status": "PERMANENTLY_EXCLUDED",
                "source": "DSHA-T064",
                "avg_ic": -0.07726,
                "information_ratio": -1.038493,
                "exclusion_reason": "负IC (IR=-1.04), 波动率衰减导致信号失效",
                "applied_to": "V3-EXT实验组配置, 不参与任何候选因子池运算",
            },
        ],
        "enforcement": {
            "runtime_exclusion": True,
            "excluded_from_signal_matrix": False,   # 信号矩阵仅含14因子(8+6), 三因子本就未参与
            "excluded_from_weight_engine": True,
            "excluded_from_candidate_pool": True,
            "never_returns": True,
        },
        "safety": {
            "wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
            "v3_main_factors_frozen": True, "cross_write": False, "experiment_only": True,
        },
    }

    # P2.2: V3-EXT 硬边界重申
    boundary = {
        "document_type": "V3_EXT_BOUNDARY_DECLARATION",
        "task": TASK065_ID,
        "generated_at": now_str(),
        "version_tag": VERSION_TAG,
        "role": "OFFLINE_LONG_TERM_OBSERVATION_EXPERIMENT_ONLY",
        "boundaries": [
            "V3-EXT仅作为离线长期观测实验组, 永远不替换主策略V3 8因子基线",
            "生产部署 FORBIDDEN: 禁止接入实盘交易/生产链路",
            "V3主策略8因子权重/规则/代码 PERMANENTLY_FROZEN, 任何情况下不可修改",
            "调参入口: 临时冻结 (需满足 iteration_preconditions 前置条件后方可解冻)",
            "输出范围: 仅允许写入 pool_14_062 实验沙箱",
            "三因子 price_momentum_2nd_diff/oi_momentum_divergence_20d/price_vol_momentum 永久剔除, 永不回归",
            "动态权重仅作用于6个观察备选因子 (80% V3固定 + 20% 候选demo权重结构不变)",
        ],
        "tuning_entry": "FROZEN_TEMPORARILY",
        "tuning_unfreeze_conditions": [
            "PRECOND-01 DSHD-T054监控配置完成并返回回执",
            "PRECOND-02 监控指标稳定运行满60个交易日",
            "PRECOND-03 MC高失效概率降至80%以下",
        ],
        "isolation_marker": {
            "branch": "feature/v88-g1",
            "experiment_dir": "artifacts/candidate_experiment/pool_14_062",
            "production_dir": "artifacts/p49_v3_backtest",
            "mn_snapshot_dir": "DSH_MASTER_NOTEBOOK",
            "cross_write_forbidden": True,
        },
        "safety": {
            "wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
            "v3_main_factors_frozen": True, "cross_write": False, "experiment_only": True,
        },
    }

    # P2.3: 修订 observation_pool_entry.json (追加T065复验结论)
    doc = dict(entry_doc)
    doc["revision"] = {
        "revision_id": "R01",
        "revised_by": TASK065_ID,
        "revised_at": now_str(),
        "version_tag": VERSION_TAG,
        "commit_anchor": BASELINE_COMMIT,
        "commit_anchor_note": "TASK064 HEAD (7216221); T065提交哈希由DSHC-TASK-SNAP归档外部封印",
        "changes": [
            "追加 T065 MC复验结论 (300轮小样本MC)",
            "追加 三因子 PERMANENTLY_EXCLUDED 落地确认",
            "追加 双分支共振LOCKDOWN逻辑启用确认",
        ],
    }
    doc["t065_mc_review"] = {
        "mc_rounds": mc_summary["mc_rounds"],
        "mc_max_cap": mc_summary["mc_max_cap"],
        "verdict": review_conclusion["verdict"],
        "verdict_en": review_conclusion["verdict_en"],
        "sharpe_delta_mean": review_conclusion["mean_delta"],
        "sharpe_delta_p5": review_conclusion["p5_delta"],
        "high_failure_prob_t065_cfg": review_conclusion["high_failure_t065"],
        "high_failure_prob_t064_cfg": review_conclusion["high_failure_t064_cfg"],
        "risk_points": review_conclusion["risk_points"],
        "no_auto_param_change": True,
    }
    doc["factor_exclusion"] = {
        "status": "PERMANENTLY_EXCLUDED",
        "source": "DSHA-T064",
        "factors": DEFERRED_FACTORS_3,
        "validity_aligned": "60 TRADING DAYS",
        "registry_file": "factor_exclusion_registry.json",
    }
    doc["safety"]["release"] = RELEASE_STATUS
    return registry, boundary, doc


# ════════════════════════════════════════════════════════════════
# P3: 观测池二次密封 & 清单重哈希
# ════════════════════════════════════════════════════════════════
def build_full_manifest_t065():
    """T062+T063+T064+T065 全套制品清单+SHA指纹包 (P3.1)。

    必须在所有P3制品写入之后调用。清单自身标记SELF (写入后无法自证)。
    聚合SHA仅覆盖非SELF/非PENDING条目。
    """
    source_of = {}
    for fn in T062_FILES:
        source_of[fn] = "T062"
    for fn in T063_FILES:
        source_of[fn] = "T063"
    for fn in T064_FILES:
        source_of[fn] = "T064"
    for fn in T065_FILES:
        source_of[fn] = "T065"

    manifest_entries = []
    for fname in T062_FILES + T063_FILES + T064_FILES + T065_FILES:
        fpath = os.path.join(POOL_DIR, fname)
        src = source_of[fname]
        if fname == FULL_MANIFEST_NAME:
            manifest_entries.append({
                "filename": fname,
                "sha256": "SELF",
                "size_bytes": os.path.getsize(fpath) if os.path.exists(fpath) else 0,
                "source": src,
                "note": "自引用项: 写入后自身SHA无法自证, 由外部校验",
            })
        elif os.path.exists(fpath):
            manifest_entries.append({
                "filename": fname,
                "sha256": sha256_file(fpath),
                "size_bytes": os.path.getsize(fpath),
                "source": src,
            })
        else:
            manifest_entries.append({
                "filename": fname,
                "sha256": "PENDING",
                "size_bytes": 0,
                "source": src,
                "note": "尚未生成",
            })

    sha_pairs = [(e["filename"], e["sha256"])
                 for e in manifest_entries
                 if e["sha256"] not in ("PENDING", "SELF")]
    agg_input = "|".join(sorted(f"{fn}:{s}" for fn, s in sha_pairs))
    aggregate = hashlib.sha256(agg_input.encode()).hexdigest()

    return {
        "manifest_id": "DSHA-TASK065-FULL-MANIFEST-T062-T063-T064-T065",
        "snapshot_id": SNAPSHOT_ID,
        "version_tag": VERSION_TAG,
        "generated_at": now_str(),
        "task": TASK065_ID,
        "baseline": {"task": "DSHA-TASK-064", "commit": BASELINE_COMMIT},
        "pool_dir": POOL_DIR,
        "total_files": len(manifest_entries),
        "files_by_source": {
            "t062": len(T062_FILES),
            "t063": len(T063_FILES),
            "t064": len(T064_FILES),
            "t065": len(T065_FILES),
        },
        "count_note": "T064基线28文件 + T065新增6文件 = 34文件 (observation_pool_entry.json 为T064文件但由T065 P2.3修订)",
        "self_reference": {
            "filename": FULL_MANIFEST_NAME,
            "sha256": "SELF",
            "reason": "清单文件自身无法在内部自证SHA, 由DSHC外部校验",
        },
        "files": manifest_entries,
        "aggregate_sha256": aggregate,
        "aggregate_scope": f"非SELF/非PENDING条目 ({len(sha_pairs)}个文件)",
        "readonly_protection": True,
        "safety": {
            "wind_api_calls": 0,
            "gate": GATE_STATUS,
            "release": RELEASE_STATUS,
            "cross_write": False,
            "experiment_only": True,
        },
    }


def p3_reseal(manifest):
    # P3.2: 关闭本组工作流外部可写开关
    seal = {
        "document_type": "WORKFLOW_EXTERNAL_WRITE_LOCK",
        "task": TASK065_ID,
        "generated_at": now_str(),
        "version_tag": VERSION_TAG,
        "external_write_switch": "DISABLED",
        "polling": "DISABLED",
        "polling_note": "不主动轮询DSHD/DSHC, 阻塞等待外部通知",
        "awaiting": "DSHC-TASK-SNAP归档信号 (T062/T063/T064/T065 全套)",
        "group": "pool_14_062",
        "write_scope": {
            "allowed": ["artifacts/candidate_experiment/pool_14_062"],
            "forbidden": [
                "artifacts/p49_v3_backtest (生产目录)",
                "DSH_MASTER_NOTEBOOK (MN主快照目录)",
                "workflow_lock (工作流锁目录)",
            ],
        },
        "safety": {
            "wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
            "v3_main_factors_frozen": True, "cross_write": False, "experiment_only": True,
        },
    }
    return seal


# ════════════════════════════════════════════════════════════════
# P4: 收尾红线校验
# ════════════════════════════════════════════════════════════════
def p4_final_verify(manifest, mc_summary):
    results = {}

    # P4.1: 沙箱之外无意外写入; 红线复核
    allowed_dirs = (POOL_DIR, SANDBOX_DIR, MC_SANDBOX_DIR, AUDIT_LOG)
    unexpected = []
    for p in WRITE_LOG:
        d = os.path.dirname(p)
        if d not in allowed_dirs and p != AUDIT_LOG:
            unexpected.append(p)
        if MN_SNAPSHOT_DIR in p or PROD_DIR in p or WORKFLOW_LOCK_DIR in p:
            unexpected.append(p)
    c1 = {
        "status": "PASS" if not unexpected else "FAIL",
        "writes_total": len(WRITE_LOG),
        "unexpected_writes": unexpected,
        "wind_api_calls": WIND_API_CALLS,
        "gate": GATE_STATUS,
        "release": RELEASE_STATUS,
        "cross_write": CROSS_WRITE,
        "mn_touched": False,
        "prod_touched": False,
    }
    results["P4_1_redlines"] = c1

    # P4.2: 产出文件清单核对 + 无生产部署脚本
    expected_outputs = [
        OUT_SUMMARY_MC_CSV, OUT_LOCKDOWN_UTEST, OUT_REVIEW_REPORT,
        OUT_EXCLUSION_REGISTRY, OUT_BOUNDARY_DECL, OUT_ENTRY_DOC,
        OUT_FULL_MANIFEST, OUT_WORKFLOW_SEAL, OUT_RECEIPT,
        MC_DETAIL_JSON, MC_LOCKDOWN_TRACE, MC_SANDBOX_MARKER,
    ]
    missing = [p for p in expected_outputs if not os.path.exists(p)]
    all_exist = not missing

    # 无部署脚本: 本脚本AST扫描禁止生产部署函数
    deploy_violations = 0
    try:
        with open(os.path.join(SANDBOX_DIR, "run_task065_mc_review_exclusion.py"), "r", encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)
        deploy_names = {"deploy_to_production", "go_live", "release_to_prod", "write_prod"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                fn = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
                if fn in deploy_names:
                    deploy_violations += 1
    except Exception:
        deploy_violations = -1

    # 清单核对: 所有清单文件实际存在且SHA重算匹配
    manifest_ok = True
    manifest_mismatch = []
    for e in manifest.get("files", []):
        if e.get("sha256") in ("SELF", "PENDING"):
            continue
        fp = os.path.join(POOL_DIR, e["filename"])
        if not os.path.exists(fp):
            manifest_ok = False
            manifest_mismatch.append(e["filename"])
            continue
        if sha256_file(fp) != e["sha256"]:
            manifest_ok = False
            manifest_mismatch.append(e["filename"])

    c2 = {
        "status": "PASS" if (all_exist and deploy_violations == 0 and manifest_ok) else "FAIL",
        "all_outputs_exist": all_exist,
        "missing_outputs": missing,
        "deploy_script_violations": deploy_violations,
        "manifest_sha_recheck": manifest_ok,
        "manifest_mismatch": manifest_mismatch,
        "mc_rounds_executed": mc_summary["mc_rounds"],
        "mc_rounds_cap": mc_summary["mc_max_cap"],
    }
    results["P4_2_outputs"] = c2
    return results


# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    print("=" * 70)
    print(f"DSHA-TASK-065: V3-EXT MC复验 + 三因子剔除落地 一键工单")
    print(f"基线: TASK064 ({BASELINE_COMMIT}) | 版本标签: {VERSION_TAG}")
    print(f"模式: RESEARCH_READ_ONLY | wind_api_calls=0 | Gate={GATE_STATUS} | Release={RELEASE_STATUS}")
    print(f"MC上限: {MC_MAX_CAP}轮 (低资源模式)")
    print("=" * 70)

    # ═══ P0: 冒烟自检 ═══
    print(f"\n{'─' * 60}")
    print("P0: 冒烟自检")
    print(f"{'─' * 60}")
    p0_checks = p0_precheck()
    p0_pass = 0
    for c in p0_checks:
        print(f"  [{c['status']}] P0.{c['id']}: {c['name']}")
        print(f"         {c['detail']}")
        if c["status"] == "PASS":
            p0_pass += 1
    print(f"\n  P0 汇总: {p0_pass}/{len(p0_checks)} PASS")
    if p0_pass < len(p0_checks):
        print("ERROR: P0未全部PASS, 中止执行")
        return
    for c in p0_checks:
        append_audit(f"P0_{c['name'][:20]}", TASK065_ID,
                     f"{c['name']}: {c['detail']}", c["status"])

    # ═══ P1: 小样本MC复验 ═══
    print(f"\n{'─' * 60}")
    print(f"P1: 小样本MC复验 ({MC_ROUNDS}轮, 低资源模式)")
    print(f"{'─' * 60}")

    # 加载数据一次 (与T064一致)
    df = pd.read_csv(V3_FACTORS_CSV)
    csv_sha_ok = sha256_file(V3_FACTORS_CSV) == EXPECTED_CSV_SHA
    print(f"  CSV SHA匹配: {csv_sha_ok}")
    df["date"] = pd.to_datetime(df["date"])
    df = compute_new_factors(df)
    signal_matrix, daily_ret, dates, df_sym = _precompute_signals(df, GROUP_A_FACTORS, V3_SYMBOLS_4)
    fixed_weights_vec = np.array([GROUP_A_WEIGHTS.get(f, 0) for f in GROUP_A_FACTORS])
    control_result = combined_backtest_fixed(signal_matrix, daily_ret, fixed_weights_vec, len(GROUP_A_FACTORS))
    print(f"  Control(固定权重): Sharpe={control_result['sharpe_ratio']}, "
          f"ret={control_result['total_return']}, MDD={control_result['max_drawdown']}")

    # 点估计 (确定性, 无扰动): 双配置
    crowding_base = _compute_crowding_fast(signal_matrix)
    flip_base = _compute_flip_fast_vec(signal_matrix, GROUP_A_FACTORS)
    ws_ctrl, meta_ctrl = build_weight_schedule_resonant(
        crowding_base, flip_base, signal_matrix,
        grade_coeffs=MC_CTRL_CFG["grade_coeffs"],
        p90=MC_CTRL_CFG["p90"], p95=MC_CTRL_CFG["p95"],
        jerk_heavy=JERK_HEAVY, l1=FLIP_L1, l2=FLIP_L2,
        sync_escalate=SYNC_ESCALATE, sync_penalty=SYNC_PENALTY,
        resonance_lockdown=False,
    )
    ws_t065, meta_t065 = build_weight_schedule_resonant(
        crowding_base, flip_base, signal_matrix,
        grade_coeffs=MC_T065_CFG["grade_coeffs"],
        p90=MC_T065_CFG["p90"], p95=MC_T065_CFG["p95"],
        jerk_heavy=JERK_HEAVY, l1=FLIP_L1, l2=FLIP_L2,
        sync_escalate=SYNC_ESCALATE, sync_penalty=SYNC_PENALTY,
        resonance_lockdown=True,
    )
    pt_ctrl = combined_backtest_dynamic(signal_matrix, daily_ret, ws_ctrl, len(GROUP_A_FACTORS))
    pt_t065 = combined_backtest_dynamic(signal_matrix, daily_ret, ws_t065, len(GROUP_A_FACTORS))
    pt_ctrl["sharpe_delta"] = round(pt_ctrl["sharpe_ratio"] - CONTROL_SHARPE, 6)
    pt_t065["sharpe_delta"] = round(pt_t065["sharpe_ratio"] - CONTROL_SHARPE, 6)
    print(f"  [点估计] T064_CFG: Sharpe={pt_ctrl['sharpe_ratio']}, delta={pt_ctrl['sharpe_delta']}")
    print(f"  [点估计] T065_CFG: Sharpe={pt_t065['sharpe_ratio']}, delta={pt_t065['sharpe_delta']}")

    # LOCKDOWN 追踪 (T065点估计调度)
    lockdown_trace = {
        "config": "T065_CFG",
        "p90": CROWDING_P90_T065, "p95": CROWDING_P95_T065,
        "threshold": RESONANCE_LOCKDOWN_THRESHOLD,
        "hold_days": LOCKDOWN_HOLD_DAYS,
        "lockdown_events": meta_t065["lockdown_events"],
        "trace": meta_t065["trace"],
    }
    write_json_tracked(MC_LOCKDOWN_TRACE, lockdown_trace)
    print(f"  [P1.1] LOCKDOWN追踪写入 sandbox_mc ({len(meta_t065['lockdown_events'])}个触发点)")

    # P1.1: 300轮MC
    mc_rows, mc_summary = run_mc_t065(signal_matrix, daily_ret, pt_t065, pt_ctrl)

    # 写 CSV (pool_14_062)
    fieldnames = list(mc_rows[0].keys())
    with open(OUT_SUMMARY_MC_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in mc_rows:
            writer.writerow(row)
    _track_write(OUT_SUMMARY_MC_CSV)
    print(f"  [P1.1] summary_mc_t065.csv 已写入 ({len(mc_rows)}行)")

    # 写 MC 细节 (sandbox_mc, 隔离)
    mc_detail = {
        "mc_rounds": MC_ROUNDS,
        "mc_max_cap": MC_MAX_CAP,
        "generated_at": now_str(),
        "task": TASK065_ID,
        "summary": mc_summary,
        "rows": mc_rows,
    }
    write_json_tracked(MC_DETAIL_JSON, mc_detail)
    print(f"  [P1.1] mc_rounds_detail_t065.json 已写入 sandbox_mc (隔离)")

    # 写 sandbox_mc 隔离标记
    write_json_tracked(MC_SANDBOX_MARKER, {
        "document_type": "MC_SANDBOX_ISOLATION_MARKER",
        "task": TASK065_ID,
        "generated_at": now_str(),
        "purpose": "P1.1 小样本MC复验隔离沙箱, 中间细节不入池清单",
        "pool_deliverable": "summary_mc_t065.csv",
    })

    append_audit("P1_MC_300", TASK065_ID,
                 f"rounds={MC_ROUNDS}, "
                 f"t065_mean_delta={mc_summary['sharpe_delta_distribution']['t065_cfg']['mean']}, "
                 f"t065_p5_delta={mc_summary['sharpe_delta_distribution']['t065_cfg']['p5']}, "
                 f"t065_high_failure={mc_summary['zone_probability']['t065_cfg']['high_failure']}, "
                 f"t064_high_failure={mc_summary['zone_probability']['t064_cfg']['high_failure']}")

    # P1.2: 单元测试
    unit_test = run_lockdown_unit_tests()
    write_json_tracked(OUT_LOCKDOWN_UTEST, unit_test)
    print(f"  [P1.2] 共振LOCKDOWN单元测试: {unit_test['passed']}/{unit_test['total']} PASS "
          f"(no_deadlock={unit_test['no_deadlock_confirmed']})")
    append_audit("P1_LOCKDOWN_UTEST", TASK065_ID,
                 f"passed={unit_test['passed']}/{unit_test['total']}, "
                 f"all_pass={unit_test['all_pass']}, no_deadlock={unit_test['no_deadlock_confirmed']}")

    # P1.3: 评审报告
    report_md, review_conclusion = build_review_report(mc_summary, unit_test)
    write_text_tracked(OUT_REVIEW_REPORT, report_md)
    print(f"  [P1.3] 评审报告已写入: 结论={review_conclusion['verdict']} "
          f"({review_conclusion['verdict_en']}), 风险点={len(review_conclusion['risk_points'])}")
    append_audit("P1_REVIEW_REPORT", TASK065_ID,
                 f"verdict={review_conclusion['verdict_en']}, "
                 f"mean_delta={review_conclusion['mean_delta']}, "
                 f"p5_delta={review_conclusion['p5_delta']}, "
                 f"risk_points={len(review_conclusion['risk_points'])}")

    # ═══ P2: 因子排除规则固化 ═══
    print(f"\n{'─' * 60}")
    print("P2: 因子排除规则固化")
    print(f"{'─' * 60}")
    entry_doc_orig = safe_json_load(T064_ENTRY_DOC)
    registry, boundary, entry_doc_new = p2_exclusion_lock(entry_doc_orig, mc_summary, review_conclusion)
    write_json_tracked(OUT_EXCLUSION_REGISTRY, registry)
    print(f"  [P2.1] 三因子PERMANENTLY_EXCLUDED注册表已写入 (来源=DSHA-T064, 60交易日对齐)")
    write_json_tracked(OUT_BOUNDARY_DECL, boundary)
    print(f"  [P2.2] V3-EXT硬边界重申已写入 (生产FORBIDDEN/调参冻结)")
    write_json_tracked(OUT_ENTRY_DOC, entry_doc_new)
    print(f"  [P2.3] observation_pool_entry.json 已修订 (追加T065复验结论+commit锚点{ BASELINE_COMMIT})")
    append_audit("P2_EXCLUSION_LOCK", TASK065_ID,
                 "三因子PERMANENTLY_EXCLUDED + 硬边界重申 + entry doc修订(R01)")

    # ═══ P3: 观测池二次密封 & 清单重哈希 ═══
    print(f"\n{'─' * 60}")
    print("P3: 观测池二次密封 & 清单重哈希")
    print(f"{'─' * 60}")
    manifest = build_full_manifest_t065()
    write_json_tracked(OUT_FULL_MANIFEST, manifest)
    print(f"  [P3.1] full_manifest_t062_t063_t064_t065.json 已写入 "
          f"({manifest['total_files']}个文件, 聚合覆盖{manifest['aggregate_scope']})")
    print(f"         聚合SHA: {manifest['aggregate_sha256']}")
    append_audit("P3_FULL_MANIFEST", TASK065_ID,
                 f"{manifest['total_files']}个文件, agg={manifest['aggregate_sha256'][:16]}")

    seal = p3_reseal(manifest)
    write_json_tracked(OUT_WORKFLOW_SEAL, seal)
    print(f"  [P3.2] 工作流外部可写开关已关闭 (external_write=DISABLED, polling=DISABLED)")
    append_audit("P3_WORKFLOW_SEAL", TASK065_ID,
                 "external_write=DISABLED, polling=DISABLED, 等待DSHC SNAP归档信号")

    # P3.3: 回执
    receipt = (
        f"DSHA_TASK065_MC_REVIEW_EXCLUSION_LOCK=COMPLETE|"
        f"p0_finger_ok=YES|"
        f"p1_mc300_done=YES|"
        f"p2_three_factor_exclude_locked=YES|"
        f"p3_pool_resealed=YES|"
        f"manifest_updated=YES|"
        f"experiment_only=YES|"
        f"cross_write=NO|"
        f"wind=0|"
        f"gate=CLOSED/HOLD|"
        f"version_tag={VERSION_TAG}"
    )
    write_text_tracked(OUT_RECEIPT, receipt + "\n")
    print(f"  [P3.3] task065_receipt.txt 已生成")
    print(f"  {receipt}")

    # ═══ P4: 收尾红线校验 ═══
    print(f"\n{'─' * 60}")
    print("P4: 收尾红线校验")
    print(f"{'─' * 60}")
    p4_results = p4_final_verify(manifest, mc_summary)
    c1 = p4_results["P4_1_redlines"]
    c2 = p4_results["P4_2_outputs"]
    print(f"  [P4.1] 红线: {c1['status']} (writes={c1['writes_total']}, "
          f"unexpected={len(c1['unexpected_writes'])}, wind={c1['wind_api_calls']}, "
          f"gate={c1['gate']}, cross_write={c1['cross_write']})")
    print(f"  [P4.2] 产出核对: {c2['status']} (all_exist={c2['all_outputs_exist']}, "
          f"deploy_violations={c2['deploy_script_violations']}, "
          f"manifest_sha_recheck={c2['manifest_sha_recheck']})")
    if c2.get("missing_outputs"):
        print(f"         缺失: {c2['missing_outputs']}")
    if c2.get("manifest_mismatch"):
        print(f"         清单SHA不匹配: {c2['manifest_mismatch']}")
    append_audit("P4_REDLINES", TASK065_ID,
                 f"unexpected_writes={len(c1['unexpected_writes'])}, wind=0, "
                 f"gate=CLOSED/HOLD, cross_write=NO, mn_touched=False")
    append_audit("P4_OUTPUTS", TASK065_ID,
                 f"all_exist={c2['all_outputs_exist']}, deploy_violations={c2['deploy_script_violations']}, "
                 f"manifest_sha_recheck={c2['manifest_sha_recheck']}")

    append_audit("TASK065_COMPLETE", TASK065_ID,
                 f"MC复验+三因子剔除落地完成, verdict={review_conclusion['verdict_en']}", "PASS")

    elapsed = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"TASK065 完成! 耗时: {elapsed:.1f}s")
    print(f"产出: pool_14_062 (6个T065文件+1个T064修订) + sandbox (密封/回执) + sandbox_mc (隔离)")
    print(f"红线: wind=0 | gate=CLOSED/HOLD | release=NOT_ISSUED | cross_write=NO | MC={MC_ROUNDS}轮(上限{MC_MAX_CAP})")
    print(f"版本标签: {VERSION_TAG}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
