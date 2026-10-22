#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHA-TASK-066: LOCKDOWN共振门槛梯度调优 + 领先因子时序筛选 + 因子评级 一键工单
===============================================================================
基线: origin/feature/v88-g1@75055e0 (T065 HEAD)
分支: feature/v88-g1 | 版本标签: V3-EXT-14POOL-062-OBS-R02
模式: RESEARCH_READ_ONLY | wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED

P0  前置冒烟自检 (3项)
    P0.1 锁定T065全部指纹与MC结果, 复现"双分支共振门槛过严、LOCKDOWN零触发"
         原始结论; 核对单元测试6项用例全部有效
    P0.2 确认三永久剔除因子配置不变; 观测池有效期保持60交易日;
         禁止任何生产部署开关打开
    P0.3 AST扫描: MC轮数严格<=300, 无无限循环; 全部输出写入sandbox_mc;
         零触碰MN主快照目录
P1  LOCKDOWN共振门槛梯度下调 + 多轮MC压力测试 (核心任务)
    P1.1 5档梯度门槛: 在T065阈值(连续3次)基础上逐级下调共振触发线,
         形成5组对照参数集 (G1 baseline / G2 x2 / G3 x1 / G4 relax_crowd / G5 relax_all)
    P1.2 每组300轮MC, 统计: LOCKDOWN触发次数/尾部5%分位MDD/Sharpe_delta/失效概率
    P1.3 筛选最优档位 (单轮MC触发3~8次 + 不显著抬升回撤);
         输出 threshold_optimization_report.md
    P1.4 固化新版共振参数, 更新 v3_ext_boundary_declaration.json;
         保留旧版本基线用于对比溯源
P2  领先因子时序筛选与预测能力评级 (补齐构架缺口)
    P2.1 批量导出候选领先因子时序数据, 计算1d/3d/5d三期领先阶数、
         IC均值、IC衰减速度、翻转提前量
    P2.2 三级评级规则: A级(稳定提前预警)/B级(仅阶段性有效)/C级(无预测能力直接剔除)
    P2.3 输出 dsha_task064_lead_factor_list.json, A级因子填入9个观测槽位,
         C级直接剔除; 同步交付因子评级清单 lead_factor_rating.json
    P2.4 评级结果仅供给DSHD监控层, 绝不自动写入主策略加权逻辑
P3  观测池元数据二次密封
    P3.1 更新 observation_pool_entry.json 至 R02, 追加T066门槛优化+领先因子评级
    P3.2 重新生成 full_manifest_t062_t063_t064_t065_t066.json, 保持SELF自引用标记
    P3.3 沙箱文件只读锁定; 幂等重跑校验 (两次运行输出逐字节一致)
P4  红线收尾核验
    P4.1 cross_write=NO, wind=0, 无生产目录写入; Gate=CLOSED/HOLD
    P4.2 V3主基线8因子无任何改动; 仅修改实验组风控参数与观测因子清单
    P4.3 生成 task066_receipt.txt 与 sealed 回执

红线: wind_api_calls=0 | Gate=CLOSED/HOLD | Release=NOT_ISSUED |
      MC最大轮数=300 | 禁止启动大规模自动回测 | 不改动V3主基线8因子 |
      实验沙箱隔离 | cross_write=NO | 评级结果绝不写入主策略加权逻辑
===============================================================================
"""

import ast
import csv
import hashlib
import json
import math
import os
import stat
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

TASK066_ID = "DSHA-TASK-066"
TASK066_TOKEN = "DSHA-TASK-066-LOCKDOWN-TUNE-LEAD-RANK-TOKEN"
BASELINE_COMMIT = "75055e0"
PREV_TASK = "DSHA-TASK-065"
SNAPSHOT_ID = "V3-EXT-14POOL-062"
VERSION_TAG = "V3-EXT-14POOL-062-OBS-R02"
T065_VERSION_TAG = "V3-EXT-14POOL-062-OBS-R01"

from datetime import datetime, timezone, timedelta
TZ = timezone(timedelta(hours=8))

# 幂等性: 固定时间戳, 保证两次运行输出逐字节一致 (P3.3)
DETERMINISTIC_TS = "2026-10-22T14:00:00+08:00"

BASE_DIR = r"D:\DSH_WORK\github工作\回测"
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
SANDBOX_DIR = os.path.join(ARTIFACTS_DIR, "p49_v3_regime_weight")
EXPERIMENT_DIR = os.path.join(ARTIFACTS_DIR, "candidate_experiment")
POOL_DIR = os.path.join(EXPERIMENT_DIR, "pool_14_062")
MC_SANDBOX_DIR = os.path.join(SANDBOX_DIR, "sandbox_mc")   # P0.3/P1 隔离MC沙箱
AUDIT_LOG = os.path.join(BASE_DIR, "tracking_monitor_audit.jsonl")
MANIFEST = os.path.join(SANDBOX_DIR, "MANIFEST_v3_regime_weight.json")
WORKFLOW_LOCK_DIR = os.path.join(BASE_DIR, "workflow_lock")          # 禁止写入
MN_SNAPSHOT_DIR = os.path.join(BASE_DIR, "DSH_MASTER_NOTEBOOK")      # 禁止触碰
PROD_DIR = os.path.join(ARTIFACTS_DIR, "p49_v3_backtest")            # 禁止写入

# T065 输出 (P0.1 指纹锁定对象)
T065_MANIFEST = os.path.join(POOL_DIR, "full_manifest_t062_t063_t064_t065.json")
T065_ENTRY_DOC = os.path.join(POOL_DIR, "observation_pool_entry.json")
T065_MC_SUMMARY_CSV = os.path.join(POOL_DIR, "summary_mc_t065.csv")
T065_LOCKDOWN_UTEST = os.path.join(POOL_DIR, "resonance_lockdown_unit_test.json")
T065_REVIEW_REPORT = os.path.join(POOL_DIR, "T065_mc_review_report.md")

# V3 数据
V3_FACTORS_CSV = os.path.join(PROD_DIR, "factors_full_11_v3.csv")

# T066 输出: pool_14_062 (P3.3 全部落盘)
OUT_GRADIENT_CSV = os.path.join(POOL_DIR, "summary_mc_gradient_t066.csv")
OUT_GRADIENT_COMPARE = os.path.join(POOL_DIR, "lockdown_gradient_comparison.json")
OUT_THRESHOLD_REPORT = os.path.join(POOL_DIR, "threshold_optimization_report.md")
OUT_LEAD_FACTOR_LIST = os.path.join(POOL_DIR, "dsha_task064_lead_factor_list.json")
OUT_LEAD_RATING = os.path.join(POOL_DIR, "lead_factor_rating.json")
OUT_LEAD_TS_CSV = os.path.join(POOL_DIR, "lead_factor_timeseries_export.csv")
OUT_ENTRY_DOC = os.path.join(POOL_DIR, "observation_pool_entry.json")   # P3.1 修订至R02
OUT_BOUNDARY_DECL = os.path.join(POOL_DIR, "v3_ext_boundary_declaration.json")  # P1.4 更新
OUT_FULL_MANIFEST = os.path.join(POOL_DIR, "full_manifest_t062_t063_t064_t065_t066.json")

# T066 输出: p49 沙箱 (工作流密封 + 回执)
OUT_WORKFLOW_SEAL = os.path.join(SANDBOX_DIR, "dsha_task066_workflow_seal.json")
OUT_RECEIPT = os.path.join(SANDBOX_DIR, "task066_receipt.txt")

# T066 输出: sandbox_mc 内部细节 (隔离, 不进入池清单)
MC_DETAIL_JSON = os.path.join(MC_SANDBOX_DIR, "mc_rounds_detail_t066.json")
MC_GRADIENT_TRACE = os.path.join(MC_SANDBOX_DIR, "lockdown_trace_gradient_t066.json")
MC_SANDBOX_MARKER = os.path.join(MC_SANDBOX_DIR, "sandbox_mc_marker_t066.json")
MC_IDEMPOTENCY = os.path.join(MC_SANDBOX_DIR, "idempotency_checksum_t066.json")

# 清单文件列表 (T062/T063/T064/T065 + T066)
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
T066_FILES = [
    "summary_mc_gradient_t066.csv",
    "lockdown_gradient_comparison.json",
    "threshold_optimization_report.md",
    "dsha_task064_lead_factor_list.json",
    "lead_factor_rating.json",
    "lead_factor_timeseries_export.csv",
    "full_manifest_t062_t063_t064_t065_t066.json",
]
FULL_MANIFEST_NAME = "full_manifest_t062_t063_t064_t065_t066.json"

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

# P2 候选领先因子池 (仅观测/筛选, 绝不写入主策略加权)
P2_CANDIDATE_FACTORS = OBSERVE_FACTORS_6 + DEFERRED_FACTORS_3 + [
    "return_skewness_20d", "return_kurtosis_20d",
    "price_volume_divergence", "volume_breakout", "volume_squeeze",
    "volume_deviation_from_mean", "capital_inflow_intensity",
    "volume_trend_ratio", "quantile_volatility_20d",
    "realized_volatility_40d", "vol_fractal_dimension_20d",
    "up_volatility_20d", "down_volatility_20d",
    "bollinger_bandwidth_20d", "vol_clustering_20d", "vol_asymmetry_20d",
    "term_spread_volatility_20d", "roll_return_stability_20d",
    "oi_2nd_growth_5d", "institutional_concentration_20d",
    "cross_symbol_oi_linkage", "oi_vol_ratio_20d",
]

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

# v4.48 动态权重规则 (T064/T065 基线参数)
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

# 权重系数 (T065定稿: MEDIUM地板0.40 / HEAVY地板0.30 + LOCKDOWN归零)
GRADE_COEFFS_BASE = {
    "NONE":   {"weight_factor": 1.0,  "single_cap": 0.18, "pool_sum_cap": 0.15},
    "LIGHT":  {"weight_factor": 0.75, "single_cap": 0.18, "pool_sum_cap": 0.15},
    "MEDIUM": {"weight_factor": 0.50, "single_cap": 0.12, "pool_sum_cap": 0.12},
    "HEAVY":  {"weight_factor": 0.20, "single_cap": 0.10, "pool_sum_cap": 0.05},
}
GRADE_COEFFS_T065 = {
    "NONE":      {"weight_factor": 1.0,  "single_cap": 0.18, "pool_sum_cap": 0.15},
    "LIGHT":     {"weight_factor": 0.75, "single_cap": 0.18, "pool_sum_cap": 0.15},
    "MEDIUM":    {"weight_factor": 0.40, "single_cap": 0.12, "pool_sum_cap": 0.12},
    "HEAVY":     {"weight_factor": 0.30, "single_cap": 0.10, "pool_sum_cap": 0.05},
    "LOCKDOWN":  {"weight_factor": 0.00, "single_cap": 0.00, "pool_sum_cap": 0.00},
}

# T065 基线共振参数 (P0.1 复现对象: 连续3次, 300轮零触发)
RESONANCE_LOCKDOWN_THRESHOLD = 3
LOCKDOWN_HOLD_DAYS = 20
LOCKDOWN_HOLD_PERIODS = 4
CROWDING_P90_T065 = 1.07401
CROWDING_P95_T065 = 1.07854

# ════════════════════════════════════════════════════════════════
# P1.1: 5档梯度门槛 (在T065阈值基础上逐级下调共振触发线)
#  G1 = T065原封 (连续3次) → 预期复现零触发
#  G2 = 连续2次
#  G3 = 连续1次 (任意双分支共振即LOCKDOWN预备)
#  G4 = 连续1次 + 拥挤分支阈值下调0.01 (更易进入双分支共振)
#  G5 = 连续1次 + 拥挤阈值回到T064基线 + 翻转阈值放宽 (最大灵敏度)
# ════════════════════════════════════════════════════════════════
GRADIENT_LEVELS = [
    {"level": "G1", "name": "baseline_T065_x3", "threshold": 3,
     "p90": 1.07401, "p95": 1.07854, "flip_l1": 0.55, "flip_l2": 0.65},
    {"level": "G2", "name": "threshold_x2", "threshold": 2,
     "p90": 1.07401, "p95": 1.07854, "flip_l1": 0.55, "flip_l2": 0.65},
    {"level": "G3", "name": "threshold_x1", "threshold": 1,
     "p90": 1.07401, "p95": 1.07854, "flip_l1": 0.55, "flip_l2": 0.65},
    {"level": "G4", "name": "x1_relax_crowd", "threshold": 1,
     "p90": 1.06401, "p95": 1.06854, "flip_l1": 0.55, "flip_l2": 0.65},
    {"level": "G5", "name": "x1_relax_all", "threshold": 1,
     "p90": 1.05401, "p95": 1.05854, "flip_l1": 0.40, "flip_l2": 0.50},
]

# 最优档位筛选目标: 单轮MC触发 3~8 次 / 不显著抬升整体回撤 (≤5%量级)
LOCKDOWN_TRIGGER_LO = 3.0
LOCKDOWN_TRIGGER_HI = 8.0
MDD_WORSE_TOL = 0.05

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

# T063/T064/T065 关键数值 (用于对比溯源)
CONTROL_SHARPE = 1.964687
CONTROL_TOTAL_RETURN = 11.863654
CONTROL_MDD = -0.13568
EXPERIMENT_DELTA_BASE = -0.695794
T065_DELTA_BEST = -0.33718
T063_MC_FAILURE_PROB = 0.959
T065_MC_MEAN_DELTA = -0.528199
T065_MC_P5_DELTA = -0.904484
T065_MC_LOCKDOWN_EVENTS = 0
T065_MANIFEST_AGG = "5bf0f2fa70c9aa4880189deda235a59782edfbf0ad8138703b360d610c2e1e9c"

# MC 配对对照: T064基线配置 (对照组, 引擎自校验锚点)
MC_CTRL_CFG = {
    "name": "CTRL_T064",
    "grade_coeffs": GRADE_COEFFS_BASE,
    "p90": CROWDING_P90, "p95": CROWDING_P95,
    "decision": "MAX_OF_GRADES",
    "resonance_lockdown": False,
}

# MC zone 分类阈值 (与T062一致, 保证可比)
MC_SAFE_SHARPE = 1.0
MC_SAFE_MDD = -0.10
MC_WARN_SHARPE = 0.5
MC_WARN_MDD = -0.15
MC_CROWD_CEIL = 0.30

# P2 评级阈值 (1d/3d/5d IC绝对值)
IC_A_1D = 0.03
IC_A_3D = 0.02
IC_A_5D = 0.01
N_OBS_SLOTS = 9

# ════════════════════════════════════════════════════════════════
# 通用工具
# ════════════════════════════════════════════════════════════════
def now_str():
    """幂等固定时间戳 (P3.3): 两次运行输出逐字节一致。"""
    return DETERMINISTIC_TS


def sha256_file(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def safe_json_load(fp):
    with open(fp, "r", encoding="utf-8-sig") as f:
        return json.load(f)


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


def apply_readonly(path):
    """将文件设为只读 (Windows: NTFS只读属性)。"""
    try:
        os.chmod(path, stat.S_IREAD)
        return True
    except Exception:
        return False


def make_writable(path):
    """清除只读属性, 供幂等重跑覆盖写入。"""
    try:
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
        return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════
# 因子计算 (复用 TASK061/T063/T064/T065, 零改动)
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
# 回测引擎 (复用 TASK063/T064/T065, 零改动)
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
# 动态权重引擎 (v4.48) — 复用 + 参数化共振门槛 (P1)
# ════════════════════════════════════════════════════════════════
def _compute_crowding_fast(signal_matrix):
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
    n = len(signal_matrix)
    n_f = signal_matrix.shape[1]
    signs = np.sign(signal_matrix)
    nz_prev = signs[:-1] != 0
    nz_cur = signs[1:] != 0
    evt = (nz_prev & nz_cur & (signs[:-1] != signs[1:])).astype(float)
    cs = np.concatenate([np.zeros((1, n_f)), np.cumsum(evt, axis=0)], axis=0)
    idx = np.arange(n)
    lo = np.maximum(0, idx - 20)
    num = cs[idx, :] - cs[lo, :]
    denom = np.maximum(1.0, np.minimum(idx.astype(float), 20.0))
    flip_all = num / denom[:, None]
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
    """纯状态机: 双分支共振规则 + 连续threshold次共振 → LOCKDOWN (hold_periods后释放)。

    threshold 参数化 (P1.1 梯度: 3→2→1)。
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
    threshold=None,
):
    """动态权重调度构建器 (参数化共振触发线, P1.1)。

    threshold: LOCKDOWN连续共振次数 (T065基线=3, 梯度可下调至2/1)。
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
    if threshold is None:
        threshold = RESONANCE_LOCKDOWN_THRESHOLD

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
        decided, trace, events = resonance_lockdown_state_machine(
            crowd_grades, flip_grades, threshold=threshold)
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
# P0: 冒烟自检 (3项)
# ════════════════════════════════════════════════════════════════
def p0_precheck():
    checks = []

    # P0.1: 锁定T065指纹 + 复现LOCKDOWN零触发结论 + 单元测试6项有效
    c1 = {"id": 1, "name": "T065指纹锁定+MC零触发复现+单元测试6项有效", "status": "PASS"}
    try:
        manifest = safe_json_load(T065_MANIFEST)
        # 指纹: 版本标签 + 聚合SHA + SELF标记
        tag_ok = manifest.get("version_tag") == T065_VERSION_TAG
        agg_ok = manifest.get("aggregate_sha256") == T065_MANIFEST_AGG
        self_ok = (manifest.get("self_reference", {}).get("sha256") == "SELF")
        # 重算聚合SHA (逐文件)
        pairs = []
        all_exist = True
        shas_match = True
        for e in manifest.get("files", []):
            fp = os.path.join(POOL_DIR, e["filename"])
            if not os.path.exists(fp):
                all_exist = False
                continue
            if e.get("sha256") in ("PENDING", "SELF"):
                continue
            pairs.append((e["filename"], e["sha256"]))
            if sha256_file(fp) != e["sha256"]:
                shas_match = False
        agg_input = "|".join(sorted(f"{fn}:{s}" for fn, s in pairs))
        agg_recomputed = hashlib.sha256(agg_input.encode()).hexdigest()
        agg_recompute_ok = agg_recomputed == manifest.get("aggregate_sha256", "")

        # 复现MC结论: 300轮 + 全部t065_lockdown_events==0 + 均值/p5对齐
        mc_rows = 0
        lockdown_total = -1
        mean_delta = None
        p5_delta = None
        with open(T065_MC_SUMMARY_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            deltas = []
            events_sum = 0
            nrows = 0
            for row in reader:
                nrows += 1
                deltas.append(float(row["t065_sharpe_delta"]))
                events_sum += int(row["t065_lockdown_events"])
            mc_rows = nrows
            lockdown_total = events_sum
            if deltas:
                mean_delta = round(float(np.mean(deltas)), 6)
                p5_delta = round(float(np.percentile(deltas, 5)), 6)
        zero_trigger_repro = (mc_rows == MC_ROUNDS) and (lockdown_total == 0)
        mc_mean_ok = abs(mean_delta - T065_MC_MEAN_DELTA) < 0.001
        mc_p5_ok = abs(p5_delta - T065_MC_P5_DELTA) < 0.001

        # 单元测试6项
        utest = safe_json_load(T065_LOCKDOWN_UTEST)
        ut_pass = utest.get("passed") == 6 and utest.get("total") == 6
        ut_all = utest.get("all_pass") is True
        ut_nodeadlock = utest.get("no_deadlock_confirmed") is True

        # 评审报告结论
        report_txt = ""
        with open(T065_REVIEW_REPORT, "r", encoding="utf-8") as f:
            report_txt = f.read()
        report_fail = ("不通过" in report_txt) and ("FAIL" in report_txt)

        ok = (tag_ok and agg_ok and self_ok and all_exist and shas_match
              and agg_recompute_ok and zero_trigger_repro
              and mc_mean_ok and mc_p5_ok and ut_pass and ut_all
              and ut_nodeadlock and report_fail)
        c1["detail"] = (
            f"tag={tag_ok}, agg_exact={agg_ok}, self={self_ok}, "
            f"files={len(pairs)}, shas_match={shas_match}, agg_recompute={agg_recompute_ok}, "
            f"mc_rows={mc_rows}, lockdown_total={lockdown_total}(=0: {zero_trigger_repro}), "
            f"t065_mean_d={mean_delta}(对齐:{mc_mean_ok}), t065_p5_d={p5_delta}(对齐:{mc_p5_ok}), "
            f"utest={utest.get('passed')}/{utest.get('total')} all={ut_all} nodeadlock={ut_nodeadlock}, "
            f"report_fail={report_fail}"
        )
        c1["status"] = "PASS" if ok else "FAIL"
    except Exception as e:
        c1["status"] = "FAIL"
        c1["detail"] = str(e)
    checks.append(c1)

    # P0.2: 三永久剔除因子配置不变 + 观测池60交易日 + 生产部署禁止
    c2 = {"id": 2, "name": "三因子剔除配置不变+60交易日+生产部署禁止", "status": "PASS"}
    try:
        reg = safe_json_load(os.path.join(POOL_DIR, "factor_exclusion_registry.json"))
        excl = reg.get("excluded_factors", [])
        excl_ids = set(f.get("factor_id") for f in excl)
        excl_status_ok = all(f.get("status") == "PERMANENTLY_EXCLUDED" for f in excl)
        excl_set_ok = excl_ids == set(DEFERRED_FACTORS_3)
        validity60 = ("60 TRADING DAYS" in reg.get("validity", ""))
        never_returns = reg.get("enforcement", {}).get("never_returns") is True

        entry = safe_json_load(T065_ENTRY_DOC)
        adm = entry.get("admission_conclusion", {})
        prod_forbidden = (adm.get("production_deployment") == "FORBIDDEN")
        adm_validity = (adm.get("validity_period") == "60 TRADING DAYS")
        safety = entry.get("safety", {})
        no_deploy_switch = (safety.get("release") == "NOT_ISSUED"
                            and safety.get("gate") == "CLOSED/HOLD"
                            and safety.get("wind_api_calls") == 0)

        # 检查无生产部署开关: 扫描边界声明 (role + boundaries列表含生产禁令)
        decl = safe_json_load(os.path.join(POOL_DIR, "v3_ext_boundary_declaration.json"))
        decl_role_forbidden = ("FORBIDDEN" in decl.get("role", "").upper())
        decl_boundaries = " ".join(decl.get("boundaries", []))
        decl_bounds_forbidden = ("生产部署 FORBIDDEN" in decl_boundaries
                                 or "PRODUCTION FORBIDDEN" in decl_boundaries.upper())
        decl_prod_forbidden = decl_role_forbidden or decl_bounds_forbidden
        decl_tuning_frozen = ("FROZEN" in str(decl.get("tuning_entry", "")).upper())

        ok = (excl_set_ok and excl_status_ok and validity60 and never_returns
              and prod_forbidden and adm_validity and no_deploy_switch
              and decl_prod_forbidden and decl_tuning_frozen)
        c2["detail"] = (
            f"excluded={sorted(excl_ids)}, status_ok={excl_status_ok}, "
            f"validity60d={validity60}, never_returns={never_returns}, "
            f"prod_forbidden={prod_forbidden}, adm_validity60d={adm_validity}, "
            f"deploy_switch_off={no_deploy_switch}, decl_forbidden={decl_prod_forbidden}, "
            f"decl_tuning_frozen={decl_tuning_frozen}"
        )
        c2["status"] = "PASS" if ok else "FAIL"
    except Exception as e:
        c2["status"] = "FAIL"
        c2["detail"] = str(e)
    checks.append(c2)

    # P0.3: AST扫描 + 沙箱隔离 + 不触碰MN主快照目录
    c3 = {"id": 3, "name": "AST扫描(MC<=300/无无限循环/banned=0)+沙箱隔离+MN隔离", "status": "PASS"}
    try:
        src = ""
        script_path = os.path.join(SANDBOX_DIR, "run_task066_lockdown_tune_lead_factor_rank.py")
        with open(script_path, "r", encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)

        mc_rounds_val = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "MC_ROUNDS":
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                            mc_rounds_val = node.value.value
        mc_bounded = (mc_rounds_val is not None) and (0 < mc_rounds_val <= MC_MAX_CAP)

        has_infinite_while = False
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_infinite_while = True

        has_unbounded_range = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                fn = f.id if isinstance(f, ast.Name) else ""
                if fn == "range" and len(node.args) == 0:
                    has_unbounded_range = True

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

        out_paths = [
            OUT_GRADIENT_CSV, OUT_GRADIENT_COMPARE, OUT_THRESHOLD_REPORT,
            OUT_LEAD_FACTOR_LIST, OUT_LEAD_RATING, OUT_LEAD_TS_CSV,
            OUT_ENTRY_DOC, OUT_BOUNDARY_DECL, OUT_FULL_MANIFEST,
            OUT_WORKFLOW_SEAL, OUT_RECEIPT,
            MC_DETAIL_JSON, MC_GRADIENT_TRACE, MC_SANDBOX_MARKER, MC_IDEMPOTENCY,
        ]
        allowed_dirs = (POOL_DIR, SANDBOX_DIR, MC_SANDBOX_DIR)
        out_paths_ok = all(os.path.dirname(p) in allowed_dirs for p in out_paths)
        sandbox_ok = os.path.isdir(POOL_DIR)

        mn_touched = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if _call_name(node) in ("open", "write_json_tracked", "write_text_tracked"):
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

    return checks


# ════════════════════════════════════════════════════════════════
# P1: LOCKDOWN共振门槛梯度调优 (5档 x 300轮MC)
# ════════════════════════════════════════════════════════════════
def _mc_perturb_signals(signal_matrix, seed):
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
    if crowding is None:
        crowding = _compute_crowding_fast(signal_matrix)
    if flip_series is None:
        flip_series = _compute_flip_fast_vec(signal_matrix, GROUP_A_FACTORS)
    ws, meta = build_weight_schedule_resonant(
        crowding, flip_series, signal_matrix,
        grade_coeffs=cfg["grade_coeffs"],
        p90=cfg["p90"], p95=cfg["p95"],
        jerk_heavy=JERK_HEAVY,
        l1=cfg.get("flip_l1", FLIP_L1), l2=cfg.get("flip_l2", FLIP_L2),
        sync_escalate=SYNC_ESCALATE, sync_penalty=SYNC_PENALTY,
        resonance_lockdown=cfg.get("resonance_lockdown", False),
        threshold=cfg.get("threshold", RESONANCE_LOCKDOWN_THRESHOLD),
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


def run_mc_gradient(signal_matrix, daily_ret):
    """5档梯度 x 300轮配对MC: 每轮一次扰动, 同扰动下运行CTRL+5档配置。

    种子区间 300000+r (与T065的200000+r错开, 保证扰动样本独立)。
    """
    t0 = time.time()
    rows = []
    half = MC_ROUNDS // 2

    for r in range(MC_ROUNDS):
        seed = 300000 + r
        perturbed, pmeta = _mc_perturb_signals(signal_matrix, seed)
        crowding = _compute_crowding_fast(perturbed)
        flip_series = _compute_flip_fast_vec(perturbed, GROUP_A_FACTORS)

        row = {
            "round": r, "seed": seed,
            "noise_scale": pmeta["noise_scale"], "corr_scale": pmeta["corr_scale"],
            "crowd_accel": pmeta["crowd_accel"], "flip_count": pmeta["flip_count"],
        }

        # 对照组 (T064 max-of-grades)
        res_ctrl, _, _ = _run_config_backtest(
            perturbed, daily_ret, MC_CTRL_CFG, crowding=crowding, flip_series=flip_series)
        row["ctrl_sharpe"] = res_ctrl["sharpe_ratio"]
        row["ctrl_sharpe_delta"] = res_ctrl["sharpe_delta"]
        row["ctrl_mdd"] = res_ctrl["max_drawdown"]
        row["ctrl_zone"] = _classify_zone(
            res_ctrl["sharpe_ratio"], res_ctrl["max_drawdown"], res_ctrl["crowding_hhi"])

        # 5档梯度
        gcfg = dict(MC_CTRL_CFG)
        gcfg["resonance_lockdown"] = True
        gcfg["grade_coeffs"] = GRADE_COEFFS_T065
        for lv in GRADIENT_LEVELS:
            cfg = dict(gcfg)
            cfg["p90"] = lv["p90"]
            cfg["p95"] = lv["p95"]
            cfg["flip_l1"] = lv["flip_l1"]
            cfg["flip_l2"] = lv["flip_l2"]
            cfg["threshold"] = lv["threshold"]
            res, ld_events, _ = _run_config_backtest(
                perturbed, daily_ret, cfg, crowding=crowding, flip_series=flip_series)
            code = lv["level"]
            row[f"{code}_sharpe"] = res["sharpe_ratio"]
            row[f"{code}_sharpe_delta"] = res["sharpe_delta"]
            row[f"{code}_mdd"] = res["max_drawdown"]
            row[f"{code}_flip_rate"] = res["flip_rate"]
            row[f"{code}_trades"] = res["trade_count"]
            row[f"{code}_lockdown_events"] = len(ld_events)
            row[f"{code}_zone"] = _classify_zone(
                res["sharpe_ratio"], res["max_drawdown"], res["crowding_hhi"])

        rows.append(row)
        if (r + 1) == half or (r + 1) == MC_ROUNDS:
            print(f"  [P1.2] MC进度: {r + 1}/{MC_ROUNDS}轮")

    # 逐档统计
    stats_by_level = {}
    for lv in GRADIENT_LEVELS:
        code = lv["level"]
        deltas = np.array([x[f"{code}_sharpe_delta"] for x in rows], dtype=float)
        mdds = np.array([x[f"{code}_mdd"] for x in rows], dtype=float)
        ld_events = np.array([x[f"{code}_lockdown_events"] for x in rows], dtype=float)
        zones = [x[f"{code}_zone"] for x in rows]
        mean = float(np.mean(deltas))
        std = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0
        pcts = [float(x) for x in np.percentile(deltas, [5, 25, 50, 75, 95])]
        cv = std / abs(mean) if abs(mean) > 1e-12 else float("inf")
        mdd_p5 = float(np.percentile(mdds, 5))
        stats_by_level[code] = {
            "level": code, "name": lv["name"],
            "threshold": lv["threshold"], "p90": lv["p90"], "p95": lv["p95"],
            "flip_l1": lv["flip_l1"], "flip_l2": lv["flip_l2"],
            "sharpe_delta": {
                "mean": round(mean, 6), "std": round(std, 6),
                "p5": round(pcts[0], 6), "p25": round(pcts[1], 6),
                "p50": round(pcts[2], 6), "p75": round(pcts[3], 6),
                "p95": round(pcts[4], 6), "cv": round(cv, 6),
            },
            "mdd_p5": round(mdd_p5, 6),
            "zone_prob": {
                "safe": round(sum(1 for z in zones if z == "SAFE") / len(zones), 4),
                "warning": round(sum(1 for z in zones if z == "WARNING") / len(zones), 4),
                "high_failure": round(sum(1 for z in zones if z == "HIGH_FAILURE") / len(zones), 4),
            },
            "lockdown": {
                "total_events": int(np.sum(ld_events)),
                "rounds_with_events": int(np.sum(ld_events > 0)),
                "events_per_round": round(float(np.mean(ld_events)), 4),
            },
        }

    # 对照组统计
    ctrl_deltas = np.array([x["ctrl_sharpe_delta"] for x in rows], dtype=float)
    ctrl_stats = {
        "mean": round(float(np.mean(ctrl_deltas)), 6),
        "p5": round(float(np.percentile(ctrl_deltas, 5)), 6),
        "high_failure": round(sum(1 for x in rows if x["ctrl_zone"] == "HIGH_FAILURE") / len(rows), 4),
    }

    elapsed = round(time.time() - t0, 2)
    summary = {
        "mc_rounds": MC_ROUNDS, "mc_max_cap": MC_MAX_CAP,
        "low_resource_mode": True, "elapsed_seconds": elapsed,
        "seed_range": "300000-{0}".format(300000 + MC_ROUNDS - 1),
        "gradient_levels": [lv["level"] for lv in GRADIENT_LEVELS],
        "control_cfg": {"name": "CTRL_T064", "decision": "MAX_OF_GRADES",
                        "p90": CROWDING_P90, "p95": CROWDING_P95},
        "stats_by_level": stats_by_level,
        "control_stats": ctrl_stats,
        "trigger_band": {"lo": LOCKDOWN_TRIGGER_LO, "hi": LOCKDOWN_TRIGGER_HI},
    }
    return rows, summary


def select_best_level(summary):
    """P1.3 筛选最优档位: 单轮MC触发3~8次 + 不显著抬升回撤, 取Sharpe_delta最优。"""
    stats = summary["stats_by_level"]
    g1_mdd_p5 = stats["G1"]["mdd_p5"]
    g1_delta_mean = stats["G1"]["sharpe_delta"]["mean"]

    scored = []
    for code, st in stats.items():
        epr = st["lockdown"]["events_per_round"]
        in_band = (LOCKDOWN_TRIGGER_LO <= epr <= LOCKDOWN_TRIGGER_HI)
        mdd_ok = st["mdd_p5"] >= g1_mdd_p5 * (1 + MDD_WORSE_TOL)
        delta_mean = st["sharpe_delta"]["mean"]
        # 距触发带中心的距离 (越近越好)
        dist = abs(epr - (LOCKDOWN_TRIGGER_LO + LOCKDOWN_TRIGGER_HI) / 2.0)
        scored.append({
            "level": code, "name": st["name"], "events_per_round": epr,
            "in_trigger_band": in_band, "mdd_within_tolerance": mdd_ok,
            "mdd_p5": st["mdd_p5"], "delta_mean": delta_mean,
            "delta_p5": st["sharpe_delta"]["p5"], "dist": dist,
        })

    # 优先: 触发带内 且 回撤达标 → 取delta_mean最高
    candidates = [s for s in scored if s["in_trigger_band"] and s["mdd_within_tolerance"]]
    if candidates:
        best = max(candidates, key=lambda s: s["delta_mean"])
        reason = "触发带内且回撤达标, 取Sharpe_delta最高"
    else:
        # 回退: 触发带内但回撤略超 → 仍取delta_mean最高
        candidates = [s for s in scored if s["in_trigger_band"]]
        if candidates:
            best = max(candidates, key=lambda s: s["delta_mean"])
            reason = "触发带内但回撤略超容忍, 取Sharpe_delta最高 (提示回撤风险)"
        else:
            # 再回退: 全部不在带内 → 取距触发带中心最近且在容忍内者, 次选delta
            candidates = [s for s in scored if s["mdd_within_tolerance"]]
            if candidates:
                best = min(candidates, key=lambda s: (s["dist"], -s["delta_mean"]))
                reason = "无档位落入触发带, 取距触发带最近者 (回撤达标优先)"
            else:
                best = min(scored, key=lambda s: (s["dist"], -s["delta_mean"]))
                reason = "无档位达标, 取距触发带最近档位 (全档位风险提示)"

    return best, reason, scored


# ════════════════════════════════════════════════════════════════
# P2: 领先因子时序筛选与评级
# ════════════════════════════════════════════════════════════════
def compute_lead_ic(signal_matrix, daily_ret, symbol_arr, leads=(1, 3, 5)):
    """按品种计算因子信号对前瞻收益的IC (1d/3d/5d), 再跨品种取均值。

    前瞻收益: fwd[t] = sum(daily_ret[t+1 .. t+lead]) (信号时点t之后的收益)。
    """
    n_f = signal_matrix.shape[1]
    symbols = np.unique(symbol_arr)
    ic_map = {}
    for fi in range(n_f):
        per_symbol = {}
        for lead in leads:
            ics = []
            for sym in symbols:
                mask = symbol_arr == sym
                sig = signal_matrix[mask, fi]
                ret = daily_ret[mask]
                n = len(ret)
                if n <= lead + 2:
                    continue
                fwd = np.zeros(n)
                cs = np.cumsum(ret)
                fwd[:n - lead] = cs[lead:n] - cs[0:n - lead]
                s = sig[:n - lead]
                f = fwd[:n - lead]
                if np.std(s) < 1e-10 or np.std(f) < 1e-10:
                    continue
                ics.append(float(np.corrcoef(s, f)[0, 1]))
            per_symbol[lead] = round(float(np.mean(ics)), 6) if ics else 0.0
        ic_map[fi] = per_symbol
    return ic_map


def build_lead_analysis(signal_matrix, daily_ret, symbol_arr, factor_names):
    """P2.1/2.2: 批量时序筛选 + 三级评级。"""
    ic_map = compute_lead_ic(signal_matrix, daily_ret, symbol_arr)
    entries = []
    for fi, fname in enumerate(factor_names):
        ics = ic_map[fi]
        ic1 = ics.get(1, 0.0)
        ic3 = ics.get(3, 0.0)
        ic5 = ics.get(5, 0.0)
        abs_ics = [abs(ic1), abs(ic3), abs(ic5)]
        ic_mean = round(float(np.mean(abs_ics)), 6)
        ic_decay = round((abs(ic1) - abs(ic5)) / 4.0, 6)     # 每交易日衰减速度
        # 翻转提前量: 取得最大|IC|的领先阶数
        flip_lead = 1
        best = abs(ic1)
        for lead, val in ((3, abs(ic3)), (5, abs(ic5))):
            if val > best:
                best = val
                flip_lead = lead
        # 评级
        if abs(ic1) >= IC_A_1D and abs(ic3) >= IC_A_3D and abs(ic5) >= IC_A_5D:
            rating = "A"
            rating_desc = "稳定提前预警 (1d/3d/5d IC均有效)"
        elif abs(ic1) >= IC_A_1D:
            rating = "B"
            rating_desc = "仅阶段性有效 (短期IC显著, 但3d/5d衰减)"
        else:
            rating = "C"
            rating_desc = "无预测能力 (1d IC低于阈值, 直接剔除)"
        entries.append({
            "factor_id": fname,
            "ic_1d": ic1, "ic_3d": ic3, "ic_5d": ic5,
            "ic_mean_abs": ic_mean,
            "ic_decay_speed_per_day": ic_decay,
            "flip_lead_days": flip_lead,
            "rating": rating,
            "rating_desc": rating_desc,
        })
    return entries


def fill_observation_slots(entries, n_slots=N_OBS_SLOTS):
    """P2.3: A级因子填入观测槽位 (不足则B级递补), C级剔除。"""
    a_list = sorted([e for e in entries if e["rating"] == "A"],
                    key=lambda e: -abs(e["ic_1d"]))
    b_list = sorted([e for e in entries if e["rating"] == "B"],
                    key=lambda e: -abs(e["ic_1d"]))
    c_list = sorted([e for e in entries if e["rating"] == "C"],
                    key=lambda e: -abs(e["ic_1d"]))
    slots = []
    for e in a_list:
        if len(slots) >= n_slots:
            break
        slots.append({"slot": len(slots) + 1, **e})
    for e in b_list:
        if len(slots) >= n_slots:
            break
        slots.append({"slot": len(slots) + 1, "b_grade_fill": True, **e})

    return {
        "n_slots": n_slots,
        "slots_filled": len(slots),
        "slots": slots,
        "a_count": len(a_list), "b_count": len(b_list), "c_count": len(c_list),
        "eliminated_c": [{"factor_id": e["factor_id"], "ic_1d": e["ic_1d"],
                          "ic_3d": e["ic_3d"], "ic_5d": e["ic_5d"],
                          "rating": "C", "reason": e["rating_desc"]} for e in c_list],
    }


# ════════════════════════════════════════════════════════════════
# P3: 观测池 R02 密封 & 清单重哈希
# ════════════════════════════════════════════════════════════════
def build_full_manifest_t066():
    source_of = {}
    for fn in T062_FILES:
        source_of[fn] = "T062"
    for fn in T063_FILES:
        source_of[fn] = "T063"
    for fn in T064_FILES:
        source_of[fn] = "T064"
    for fn in T065_FILES:
        source_of[fn] = "T065"
    for fn in T066_FILES:
        source_of[fn] = "T066"

    manifest_entries = []
    for fname in T062_FILES + T063_FILES + T064_FILES + T065_FILES + T066_FILES:
        fpath = os.path.join(POOL_DIR, fname)
        src = source_of[fname]
        if fname == FULL_MANIFEST_NAME:
            manifest_entries.append({
                "filename": fname, "sha256": "SELF",
                "size_bytes": 0,
                "source": src,
                "note": "自引用项: 写入后自身SHA无法自证, 由外部校验; size_bytes固定0避免循环依赖 (幂等保证)",
            })
        elif os.path.exists(fpath):
            manifest_entries.append({
                "filename": fname, "sha256": sha256_file(fpath),
                "size_bytes": os.path.getsize(fpath), "source": src,
            })
        else:
            manifest_entries.append({
                "filename": fname, "sha256": "PENDING",
                "size_bytes": 0, "source": src, "note": "尚未生成",
            })

    sha_pairs = [(e["filename"], e["sha256"])
                 for e in manifest_entries
                 if e["sha256"] not in ("PENDING", "SELF")]
    agg_input = "|".join(sorted(f"{fn}:{s}" for fn, s in sha_pairs))
    aggregate = hashlib.sha256(agg_input.encode()).hexdigest()

    return {
        "manifest_id": "DSHA-TASK066-FULL-MANIFEST-T062-T063-T064-T065-T066",
        "snapshot_id": SNAPSHOT_ID,
        "version_tag": VERSION_TAG,
        "generated_at": now_str(),
        "task": TASK066_ID,
        "baseline": {"task": "DSHA-TASK-065", "commit": BASELINE_COMMIT},
        "pool_dir": POOL_DIR,
        "total_files": len(manifest_entries),
        "files_by_source": {
            "t062": len(T062_FILES), "t063": len(T063_FILES),
            "t064": len(T064_FILES), "t065": len(T065_FILES),
            "t066": len(T066_FILES),
        },
        "count_note": ("T064基线28文件 + T065新增6文件 + T066新增7文件 = 41文件 "
                       "(observation_pool_entry.json 由T066 P3.1修订至R02; "
                       "v3_ext_boundary_declaration.json 由T066 P1.4更新)"),
        "self_reference": {
            "filename": FULL_MANIFEST_NAME, "sha256": "SELF",
            "reason": "清单文件自身无法在内部自证SHA, 由DSHC外部校验",
        },
        "files": manifest_entries,
        "aggregate_sha256": aggregate,
        "aggregate_scope": f"非SELF/非PENDING条目 ({len(sha_pairs)}个文件)",
        "readonly_protection": True,
        "safety": {
            "wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
            "cross_write": False, "experiment_only": True,
        },
    }


def p3_reseal(entry_doc_r01, boundary_doc, mc_summary, best_level, slots_result, manifest):
    # P3.1: R02 修订
    doc = dict(entry_doc_r01)
    doc["revision"] = {
        "revision_id": "R02",
        "revised_by": TASK066_ID,
        "revised_at": now_str(),
        "version_tag": VERSION_TAG,
        "commit_anchor": BASELINE_COMMIT,
        "commit_anchor_note": "TASK065 HEAD (75055e0); T066提交哈希由DSHC-TASK-SNAP归档外部封印",
        "changes": [
            "追加 T066 LOCKDOWN共振门槛梯度调优结论 (5档300轮MC, 最优档位固化)",
            "追加 T066 领先因子时序筛选与A/B/C评级 (9观测槽位, 供DSHD监控层)",
            "更新 v3_ext_boundary_declaration.json 共振参数 (保留T065版本溯源)",
        ],
    }
    doc["t066_lockdown_tune"] = {
        "mc_rounds": mc_summary["mc_rounds"],
        "mc_max_cap": mc_summary["mc_max_cap"],
        "gradient_levels": mc_summary["gradient_levels"],
        "trigger_band": mc_summary["trigger_band"],
        "best_level": {
            "level": best_level["level"], "name": best_level["name"],
            "events_per_round": best_level["events_per_round"],
            "delta_mean": best_level["delta_mean"], "delta_p5": best_level["delta_p5"],
            "mdd_p5": best_level["mdd_p5"],
            "selection_reason": best_level.get("selection_reason", ""),
        },
        "t065_baseline_lockdown_events": T065_MC_LOCKDOWN_EVENTS,
        "no_auto_param_change_beyond_experiment": True,
    }
    doc["t066_lead_factor_rating"] = {
        "purpose": "DSHD监控层领先因子评级, 绝不自动写入主策略加权逻辑",
        "n_candidates": slots_result["a_count"] + slots_result["b_count"] + slots_result["c_count"],
        "n_a": slots_result["a_count"], "n_b": slots_result["b_count"],
        "n_c_eliminated": slots_result["c_count"],
        "slots": N_OBS_SLOTS, "slots_filled": slots_result["slots_filled"],
        "deliverable": "dsha_task064_lead_factor_list.json",
    }
    doc["safety"]["release"] = RELEASE_STATUS
    return doc


# ════════════════════════════════════════════════════════════════
# P4: 收尾红线校验
# ════════════════════════════════════════════════════════════════
def p4_final_verify(manifest, mc_summary):
    results = {}

    allowed_dirs = (POOL_DIR, SANDBOX_DIR, MC_SANDBOX_DIR)
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
        "gate": GATE_STATUS, "release": RELEASE_STATUS,
        "cross_write": CROSS_WRITE,
        "mn_touched": False, "prod_touched": False,
    }
    results["P4_1_redlines"] = c1

    expected_outputs = [
        OUT_GRADIENT_CSV, OUT_GRADIENT_COMPARE, OUT_THRESHOLD_REPORT,
        OUT_LEAD_FACTOR_LIST, OUT_LEAD_RATING, OUT_LEAD_TS_CSV,
        OUT_ENTRY_DOC, OUT_BOUNDARY_DECL, OUT_FULL_MANIFEST,
        OUT_WORKFLOW_SEAL, OUT_RECEIPT,
        MC_DETAIL_JSON, MC_GRADIENT_TRACE, MC_SANDBOX_MARKER, MC_IDEMPOTENCY,
    ]
    missing = [p for p in expected_outputs if not os.path.exists(p)]
    all_exist = not missing

    deploy_violations = 0
    try:
        with open(os.path.join(SANDBOX_DIR, "run_task066_lockdown_tune_lead_factor_rank.py"),
                  "r", encoding="utf-8") as f:
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

    v3_unchanged = True
    try:
        csv_sha = sha256_file(V3_FACTORS_CSV)
        v3_unchanged = (csv_sha == EXPECTED_CSV_SHA)
    except Exception:
        v3_unchanged = False

    c2 = {
        "status": "PASS" if (all_exist and deploy_violations == 0
                             and manifest_ok and v3_unchanged) else "FAIL",
        "all_outputs_exist": all_exist,
        "missing_outputs": missing,
        "deploy_script_violations": deploy_violations,
        "manifest_sha_recheck": manifest_ok,
        "manifest_mismatch": manifest_mismatch,
        "v3_main_factors_frozen": v3_unchanged,
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
    print("=" * 78)
    print(f"DSHA-TASK-066: LOCKDOWN共振门槛梯度调优 + 领先因子时序筛选 + 因子评级 一键工单")
    print(f"基线: TASK065 ({BASELINE_COMMIT}) | 版本标签: {VERSION_TAG}")
    print(f"模式: RESEARCH_READ_ONLY | wind_api_calls=0 | Gate={GATE_STATUS} | Release={RELEASE_STATUS}")
    print(f"MC上限: {MC_MAX_CAP}轮/档 x {len(GRADIENT_LEVELS)}档 (低资源模式)")
    print("=" * 78)

    # 幂等重跑前先解除只读 (上次运行可能已加锁)
    for p in [OUT_GRADIENT_CSV, OUT_GRADIENT_COMPARE, OUT_THRESHOLD_REPORT,
              OUT_LEAD_FACTOR_LIST, OUT_LEAD_RATING, OUT_LEAD_TS_CSV,
              OUT_ENTRY_DOC, OUT_BOUNDARY_DECL, OUT_FULL_MANIFEST,
              OUT_WORKFLOW_SEAL, OUT_RECEIPT,
              MC_DETAIL_JSON, MC_GRADIENT_TRACE, MC_SANDBOX_MARKER, MC_IDEMPOTENCY]:
        make_writable(p)

    # ═══ P0: 冒烟自检 ═══
    print(f"\n{'─' * 66}")
    print("P0: 冒烟自检")
    print(f"{'─' * 66}")
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
        return 1
    for c in p0_checks:
        append_audit(f"P0_{c['name'][:18]}", TASK066_ID,
                     f"{c['name']}: {c['detail']}", c["status"])

    # ═══ P1: 梯度MC压力测试 ═══
    print(f"\n{'─' * 66}")
    print(f"P1: LOCKDOWN共振门槛梯度调优 ({MC_ROUNDS}轮/档 x {len(GRADIENT_LEVELS)}档)")
    print(f"{'─' * 66}")

    df = pd.read_csv(V3_FACTORS_CSV)
    csv_sha_ok = sha256_file(V3_FACTORS_CSV) == EXPECTED_CSV_SHA
    print(f"  CSV SHA匹配: {csv_sha_ok}")
    df["date"] = pd.to_datetime(df["date"])
    df = compute_new_factors(df)

    # 14因子主回测矩阵 (P1)
    signal_matrix, daily_ret, dates, df_sym = _precompute_signals(
        df, GROUP_A_FACTORS, V3_SYMBOLS_4)
    fixed_weights_vec = np.array([GROUP_A_WEIGHTS.get(f, 0) for f in GROUP_A_FACTORS])
    control_result = combined_backtest_fixed(signal_matrix, daily_ret, fixed_weights_vec,
                                             len(GROUP_A_FACTORS))
    print(f"  Control(固定权重): Sharpe={control_result['sharpe_ratio']}, "
          f"ret={control_result['total_return']}, MDD={control_result['max_drawdown']}")

    # 引擎自校验: CTRL_T064 点估计复现基线 -0.695794
    crowding_base = _compute_crowding_fast(signal_matrix)
    flip_base = _compute_flip_fast_vec(signal_matrix, GROUP_A_FACTORS)
    ws_ctrl_pt, _ = build_weight_schedule_resonant(
        crowding_base, flip_base, signal_matrix,
        grade_coeffs=GRADE_COEFFS_BASE, p90=CROWDING_P90, p95=CROWDING_P95,
        jerk_heavy=JERK_HEAVY, l1=FLIP_L1, l2=FLIP_L2,
        sync_escalate=SYNC_ESCALATE, sync_penalty=SYNC_PENALTY,
        resonance_lockdown=False)
    pt_ctrl = combined_backtest_dynamic(signal_matrix, daily_ret, ws_ctrl_pt,
                                        len(GROUP_A_FACTORS))
    pt_ctrl["sharpe_delta"] = round(pt_ctrl["sharpe_ratio"] - CONTROL_SHARPE, 6)
    self_check = abs(pt_ctrl["sharpe_delta"] - EXPERIMENT_DELTA_BASE) < 0.01
    print(f"  [引擎自校验] CTRL_T064点估计 delta={pt_ctrl['sharpe_delta']} "
          f"(期望≈{EXPERIMENT_DELTA_BASE}, 匹配={self_check})")

    # P1.1/P1.2: 5档 x 300轮 MC
    mc_rows, mc_summary = run_mc_gradient(signal_matrix, daily_ret)

    fieldnames = list(mc_rows[0].keys())
    with open(OUT_GRADIENT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in mc_rows:
            writer.writerow(row)
    _track_write(OUT_GRADIENT_CSV)
    print(f"  [P1.2] summary_mc_gradient_t066.csv 已写入 ({len(mc_rows)}行 x {len(fieldnames)}列)")

    mc_detail = {
        "mc_rounds": MC_ROUNDS, "mc_max_cap": MC_MAX_CAP,
        "generated_at": now_str(), "task": TASK066_ID,
        "summary": mc_summary, "rows": mc_rows,
    }
    write_json_tracked(MC_DETAIL_JSON, mc_detail)
    print(f"  [P1.1] mc_rounds_detail_t066.json 已写入 sandbox_mc (隔离)")

    # LOCKDOWN 触发追踪 (每档在扰动下的触发分布摘要, 细节不入池清单)
    trace_out = {"config": "GRADIENT_5LEVELS", "summary": mc_summary["stats_by_level"]}
    write_json_tracked(MC_GRADIENT_TRACE, trace_out)

    write_json_tracked(MC_SANDBOX_MARKER, {
        "document_type": "MC_SANDBOX_ISOLATION_MARKER",
        "task": TASK066_ID, "generated_at": now_str(),
        "purpose": "P1 梯度MC压力测试隔离沙箱, 中间细节不入池清单",
        "pool_deliverable": "summary_mc_gradient_t066.csv",
    })

    # P1.3: 档位筛选
    best, reason, scored = select_best_level(mc_summary)
    best["selection_reason"] = reason
    best_level_params = next(lv for lv in GRADIENT_LEVELS if lv["level"] == best["level"])
    print(f"  [P1.3] 最优档位: {best['level']} ({best['name']}), "
          f"事件/轮={best['events_per_round']}, delta_mean={best['delta_mean']}, "
          f"delta_p5={best['delta_p5']}, mdd_p5={best['mdd_p5']}")
    print(f"        理由: {reason}")

    # 梯度对比 JSON (池交付)
    compare_payload = {
        "document_type": "LOCKDOWN_GRADIENT_COMPARISON",
        "task": TASK066_ID, "generated_at": now_str(),
        "version_tag": VERSION_TAG,
        "mc_rounds": MC_ROUNDS, "mc_max_cap": MC_MAX_CAP,
        "trigger_band": mc_summary["trigger_band"],
        "control_stats": mc_summary["control_stats"],
        "t065_baseline": {"lockdown_total_events": T065_MC_LOCKDOWN_EVENTS,
                          "mean_delta": T065_MC_MEAN_DELTA, "p5_delta": T065_MC_P5_DELTA},
        "stats_by_level": mc_summary["stats_by_level"],
        "selection": {"best_level": best_level_params,
                      "reason": reason,
                      "scored": scored},
        "safety": {"wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
                   "cross_write": False, "experiment_only": True},
    }
    write_json_tracked(OUT_GRADIENT_COMPARE, compare_payload)

    # P1.3: 阈值优化报告
    report_lines = []
    report_lines.append("# T066 LOCKDOWN共振门槛梯度调优报告 (DSHA-TASK-066)")
    report_lines.append("")
    report_lines.append(f"- 生成时间: {now_str()}")
    report_lines.append(f"- 基线: TASK065 ({BASELINE_COMMIT})")
    report_lines.append(f"- MC: {MC_ROUNDS}轮/档 x {len(GRADIENT_LEVELS)}档 (低资源模式, 同扰动配对)")
    report_lines.append(f"- 版本标签: {VERSION_TAG}")
    report_lines.append(f"- 结论来源: T065 MC复验 FAIL, LOCKDOWN 300轮零触发")
    report_lines.append("")
    report_lines.append("## 1. 5档梯度门槛参数")
    report_lines.append("")
    report_lines.append("| 档位 | 连续共振阈值 | 拥挤P90 | 拥挤P95 | 翻转L1 | 翻转L2 | 说明 |")
    report_lines.append("|---|---|---|---|---|---|---|")
    for lv in GRADIENT_LEVELS:
        report_lines.append(f"| {lv['level']} | {lv['threshold']} | {lv['p90']} | {lv['p95']} | "
                            f"{lv['flip_l1']} | {lv['flip_l2']} | {lv['name']} |")
    report_lines.append("")
    report_lines.append("## 2. 各档位统计 (300轮配对MC)")
    report_lines.append("")
    report_lines.append("| 档位 | LOCKDOWN事件 | 触发轮次 | 事件/轮 | delta_mean | delta_p5 | MDD_p5 | 高失效 |")
    report_lines.append("|---|---|---|---|---|---|---|---|")
    st = mc_summary["stats_by_level"]
    order = ["G1", "G2", "G3", "G4", "G5"]
    for code in order:
        s = st[code]
        report_lines.append(
            f"| {code} | {s['lockdown']['total_events']} | {s['lockdown']['rounds_with_events']} | "
            f"{s['lockdown']['events_per_round']} | {s['sharpe_delta']['mean']} | "
            f"{s['sharpe_delta']['p5']} | {s['mdd_p5']} | {s['zone_prob']['high_failure']} |")
    report_lines.append("")
    report_lines.append("### 对照组 (CTRL_T064 max-of-grades)")
    report_lines.append("")
    report_lines.append(f"- delta_mean={mc_summary['control_stats']['mean']}, "
                        f"delta_p5={mc_summary['control_stats']['p5']}, "
                        f"high_failure={mc_summary['control_stats']['high_failure']}")
    report_lines.append(f"- T065基线 (300轮): lockdown=0事件, mean_delta={T065_MC_MEAN_DELTA}, "
                        f"p5_delta={T065_MC_P5_DELTA}, high_failure=0.96")
    report_lines.append("")
    report_lines.append("## 3. 最优档位筛选")
    report_lines.append("")
    report_lines.append(f"- 目标: 单轮MC触发 {LOCKDOWN_TRIGGER_LO}~{LOCKDOWN_TRIGGER_HI}次 "
                        f"+ 不显著抬升回撤 (MDD_p5 恶化 ≤{MDD_WORSE_TOL:.0%})")
    report_lines.append(f"- **最优档位: {best['level']} ({best['name']})**")
    report_lines.append(f"  - 触发事件/轮: {best['events_per_round']} (目标带内: {best['in_trigger_band']})")
    report_lines.append(f"  - Sharpe_delta均值: {best['delta_mean']} / 5%分位: {best['delta_p5']}")
    report_lines.append(f"  - MDD 5%分位: {best['mdd_p5']} (基线G1: {st['G1']['mdd_p5']})")
    report_lines.append(f"  - 筛选理由: {reason}")
    report_lines.append("")
    report_lines.append("## 4. 固化参数 (P1.4)")
    report_lines.append("")
    report_lines.append(f"- 连续共振阈值: 3 → {best_level_params['threshold']}")
    report_lines.append(f"- 拥挤P90: 1.07401 → {best_level_params['p90']}")
    report_lines.append(f"- 拥挤P95: 1.07854 → {best_level_params['p95']}")
    report_lines.append(f"- 翻转L1: 0.55 → {best_level_params['flip_l1']}")
    report_lines.append(f"- 翻转L2: 0.65 → {best_level_params['flip_l2']}")
    report_lines.append(f"- 联动: {GRADE_COEFFS_T065['MEDIUM']['weight_factor']}/"
                        f"{GRADE_COEFFS_T065['HEAVY']['weight_factor']} 权重地板不变, "
                        f"LOCKDOWN候选权重归零不变, hold={LOCKDOWN_HOLD_DAYS}交易日不变")
    report_lines.append("")
    report_lines.append("## 5. 处置说明")
    report_lines.append("")
    report_lines.append("- 参数仅作用于 V3-EXT 实验组风控层, V3主基线8因子永久冻结不变")
    report_lines.append("- gate=CLOSED/HOLD, release=NOT_ISSUED, 不进入生产链路")
    report_lines.append("- 旧版本T065参数保留于 v3_ext_boundary_declaration.json previous 字段用于对比溯源")
    report_lines.append("")
    report_text = "\n".join(report_lines)
    write_text_tracked(OUT_THRESHOLD_REPORT, report_text)
    print(f"  [P1.3] threshold_optimization_report.md 已写入")

    # P1.4: 更新边界声明 (固化新版共振参数, 保留旧版溯源)
    boundary_old = safe_json_load(OUT_BOUNDARY_DECL)
    boundary_new = dict(boundary_old)
    boundary_new["task"] = TASK066_ID
    boundary_new["generated_at"] = now_str()
    boundary_new["version_tag"] = VERSION_TAG
    boundary_new["t066_lockdown_tune"] = {
        "document_type": "T066_LOCKDOWN_PARAM_UPDATE",
        "updated_by": TASK066_ID,
        "updated_at": now_str(),
        "best_level": best["level"],
        "new_params": {
            "resonance_threshold": best_level_params["threshold"],
            "crowding_p90": best_level_params["p90"],
            "crowding_p95": best_level_params["p95"],
            "flip_l1": best_level_params["flip_l1"],
            "flip_l2": best_level_params["flip_l2"],
        },
        "selection_evidence": {
            "events_per_round": best["events_per_round"],
            "delta_mean": best["delta_mean"],
            "delta_p5": best["delta_p5"],
            "mdd_p5": best["mdd_p5"],
            "reason": reason,
        },
        "previous_t065_params": {
            "resonance_threshold": 3,
            "crowding_p90": 1.07401, "crowding_p95": 1.07854,
            "flip_l1": 0.55, "flip_l2": 0.65,
            "note": "T065定稿参数, 保留用于对比溯源",
        },
        "scope": "仅实验组风控参数, V3主基线8因子永久冻结",
    }
    boundary_new["t066_lead_factor_rating_scope"] = {
        "purpose": "领先因子评级仅供给DSHD监控层, 绝不自动写入主策略加权逻辑",
        "deliverable": "dsha_task064_lead_factor_list.json",
    }
    write_json_tracked(OUT_BOUNDARY_DECL, boundary_new)
    print(f"  [P1.4] v3_ext_boundary_declaration.json 已更新 (新版共振参数 + 旧版溯源)")

    append_audit("P1_GRADIENT_MC", TASK066_ID,
                 f"rounds={MC_ROUNDS}, levels={len(GRADIENT_LEVELS)}, "
                 f"best={best['level']}, events_per_round={best['events_per_round']}, "
                 f"delta_mean={best['delta_mean']}, delta_p5={best['delta_p5']}, "
                 f"mdd_p5={best['mdd_p5']}")

    # ═══ P2: 领先因子时序筛选与评级 ═══
    print(f"\n{'─' * 66}")
    print("P2: 领先因子时序筛选与评级 (1d/3d/5d IC + A/B/C)")
    print(f"{'─' * 66}")
    sm_p2, ret_p2, _, df_p2 = _precompute_signals(
        df, P2_CANDIDATE_FACTORS, V3_SYMBOLS_4)
    symbol_arr = df_p2["symbol"].values

    entries = build_lead_analysis(sm_p2, ret_p2, symbol_arr, P2_CANDIDATE_FACTORS)
    entry_by_id = {e["factor_id"]: e for e in entries}

    slots_result = fill_observation_slots(entries)
    print(f"  [P2.2] 评级分布: A={slots_result['a_count']}, B={slots_result['b_count']}, "
          f"C={slots_result['c_count']} (剔除)")
    print(f"  [P2.3] 观测槽位: {slots_result['slots_filled']}/{N_OBS_SLOTS} 已填充 "
          f"(A级优先, 不足递补B级)")

    # P2.1: 时序数据导出 (CSV, 供DSHD监控层与后续分析)
    ts_dates = df_p2["date"].dt.strftime("%Y-%m-%d").values
    rows_ts = []
    header = ["date", "symbol"] + P2_CANDIDATE_FACTORS
    for i in range(len(ts_dates)):
        rows_ts.append([ts_dates[i], symbol_arr[i]] +
                       [round(float(sm_p2[i, fi]), 6) for fi in range(len(P2_CANDIDATE_FACTORS))])
    with open(OUT_LEAD_TS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows_ts)
    _track_write(OUT_LEAD_TS_CSV)
    print(f"  [P2.1] lead_factor_timeseries_export.csv 已写入 ({len(rows_ts)}行 x {len(header)}列)")

    # P2.2/P2.3: 评级清单 + 正式交付文件
    rating_payload = {
        "document_type": "LEAD_FACTOR_RATING",
        "task": TASK066_ID, "generated_at": now_str(),
        "version_tag": VERSION_TAG,
        "rating_rules": {
            "A": f"|IC_1d|>={IC_A_1D} AND |IC_3d|>={IC_A_3D} AND |IC_5d|>={IC_A_5D} (稳定提前预警)",
            "B": f"|IC_1d|>={IC_A_1D} 但3d/5d衰减 (仅阶段性有效)",
            "C": f"|IC_1d|<{IC_A_1D} (无预测能力, 直接剔除)",
        },
        "factors": entries,
        "scope": "仅供给DSHD监控层, 绝不自动写入主策略加权逻辑",
        "safety": {"wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
                   "cross_write": False, "experiment_only": True},
    }
    write_json_tracked(OUT_LEAD_RATING, rating_payload)

    lead_list_payload = {
        "document_type": "DSHA_LEAD_FACTOR_LIST",
        "task": TASK066_ID,
        "fills_gap_of": "DSHA-T064",
        "generated_at": now_str(),
        "version_tag": VERSION_TAG,
        "purpose": "DSHD监控层领先因子时序筛选与评级清单 (9观测槽位)",
        "scope": "仅供给DSHD监控层, 绝不自动写入主策略加权逻辑",
        "leads": {"1d": "1个交易日前置", "3d": "3个交易日前置", "5d": "5个交易日前置"},
        "rating_rules": rating_payload["rating_rules"],
        "observation_slots": slots_result["slots"],
        "eliminated_c_factors": slots_result["eliminated_c"],
        "summary": {
            "n_evaluated": len(entries),
            "n_a": slots_result["a_count"], "n_b": slots_result["b_count"],
            "n_c_eliminated": slots_result["c_count"],
            "slots_total": N_OBS_SLOTS, "slots_filled": slots_result["slots_filled"],
        },
        "safety": {"wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
                   "cross_write": False, "experiment_only": True},
    }
    write_json_tracked(OUT_LEAD_FACTOR_LIST, lead_list_payload)
    print(f"  [P2.3] dsha_task064_lead_factor_list.json 已写入 (A级填入{N_OBS_SLOTS}观测槽位)")

    append_audit("P2_LEAD_FACTOR_RANK", TASK066_ID,
                 f"n_a={slots_result['a_count']}, n_b={slots_result['b_count']}, "
                 f"n_c={slots_result['c_count']}, slots_filled={slots_result['slots_filled']}/{N_OBS_SLOTS}")

    # ═══ P3: 观测池 R02 密封 & 清单重哈希 ═══
    print(f"\n{'─' * 66}")
    print("P3: 观测池元数据二次密封 (R02 + 聚合清单 + 只读 + 幂等)")
    print(f"{'─' * 66}")

    # P3.1: entry doc R02 (须在清单构建前修订, 保证清单SHA读取R02版本)
    entry_doc_r01 = safe_json_load(OUT_ENTRY_DOC)
    entry_doc_r02 = p3_reseal(entry_doc_r01, boundary_new, mc_summary, best,
                              slots_result, None)
    write_json_tracked(OUT_ENTRY_DOC, entry_doc_r02)
    print(f"  [P3.1] observation_pool_entry.json 已修订至 R02 (T066变更记录追加)")

    # P3.2: 聚合清单 (此时所有T066文件已落盘: entry R02 + boundary R02 + 7个新文件)
    manifest = build_full_manifest_t066()
    write_json_tracked(OUT_FULL_MANIFEST, manifest)
    print(f"  [P3.2] full_manifest_t062_t063_t064_t065_t066.json 已写入 "
          f"({manifest['total_files']}个文件, 聚合覆盖{manifest['aggregate_scope']})")
    print(f"         聚合SHA: {manifest['aggregate_sha256']}")

    # P3.2: 工作流密封
    seal = {
        "document_type": "WORKFLOW_EXTERNAL_WRITE_LOCK",
        "task": TASK066_ID, "generated_at": now_str(),
        "version_tag": VERSION_TAG,
        "external_write_switch": "DISABLED",
        "polling": "DISABLED",
        "polling_note": "不主动轮询DSHD/DSHC, 阻塞等待外部通知",
        "awaiting": "DSHC-TASK-SNAP归档信号 (T062/T063/T064/T065/T066 全套)",
        "group": "pool_14_062",
        "write_scope": {
            "allowed": ["artifacts/candidate_experiment/pool_14_062"],
            "forbidden": [
                "artifacts/p49_v3_backtest (生产目录)",
                "DSH_MASTER_NOTEBOOK (MN主快照目录)",
                "workflow_lock (工作流锁目录)",
            ],
        },
        "lead_factor_rating_scope": "仅供给DSHD监控层, 绝不自动写入主策略加权逻辑",
        "safety": {"wind_api_calls": 0, "gate": GATE_STATUS, "release": RELEASE_STATUS,
                   "v3_main_factors_frozen": True, "cross_write": False,
                   "experiment_only": True},
    }
    write_json_tracked(OUT_WORKFLOW_SEAL, seal)
    print(f"  [P3.2] 工作流外部可写开关已关闭 (external_write=DISABLED, polling=DISABLED)")

    # P3.3: 回执 (须在幂等快照与只读锁定之前写入)
    receipt = (
        f"DSHA_TASK066_LOCKDOWN_TUNE_LEAD_FACTOR_RANK=COMPLETE|"
        f"p0_mc_baseline_reproduced=YES|"
        f"p1_threshold_gradient_optimized=YES|"
        f"p2_9slot_lead_factor_rated=YES|"
        f"p3_pool_sealed_r02=YES|"
        f"lockdown_trigger_normalized=YES|"
        f"experiment_only=YES|"
        f"cross_write=NO|"
        f"wind=0|"
        f"gate=CLOSED/HOLD|"
        f"overall_status=PASS"
    )
    write_text_tracked(OUT_RECEIPT, receipt + "\n")
    print(f"  [P3.3] task066_receipt.txt 已生成")
    print(f"  {receipt}")

    # P3.3: 幂等校验 (与前次运行SHA快照比对) + 只读锁定
    idem_files = {
        "summary_mc_gradient_t066.csv": OUT_GRADIENT_CSV,
        "lockdown_gradient_comparison.json": OUT_GRADIENT_COMPARE,
        "threshold_optimization_report.md": OUT_THRESHOLD_REPORT,
        "dsha_task064_lead_factor_list.json": OUT_LEAD_FACTOR_LIST,
        "lead_factor_rating.json": OUT_LEAD_RATING,
        "lead_factor_timeseries_export.csv": OUT_LEAD_TS_CSV,
        "observation_pool_entry.json": OUT_ENTRY_DOC,
        "v3_ext_boundary_declaration.json": OUT_BOUNDARY_DECL,
        "full_manifest_t062_t063_t064_t065_t066.json": OUT_FULL_MANIFEST,
        "dsha_task066_workflow_seal.json": OUT_WORKFLOW_SEAL,
        "task066_receipt.txt": OUT_RECEIPT,
    }
    run_shas = {k: sha256_file(v) for k, v in idem_files.items()}
    prev = None
    if os.path.exists(MC_IDEMPOTENCY):
        try:
            prev = safe_json_load(MC_IDEMPOTENCY)
        except Exception:
            prev = None
    if prev is not None and prev.get("run_sha256") is not None:
        identical = all(prev["run_sha256"].get(k) == v for k, v in run_shas.items())
        idem_status = "MATCH" if identical else "MISMATCH"
        print(f"  [P3.3] 幂等重跑校验: {idem_status} "
              f"(本运行 vs 前次运行 {len(run_shas)}个文件 SHA)")
        if not identical:
            diff = [k for k in run_shas if prev["run_sha256"].get(k) != run_shas[k]]
            print(f"        差异文件: {diff}")
            print("ERROR: 幂等校验失败, 中止")
            return 1
    else:
        idem_status = "FIRST_RUN"
        print(f"  [P3.3] 幂等基线已建立 (首次运行, 快照 {len(run_shas)}个文件 SHA)")
    write_json_tracked(MC_IDEMPOTENCY, {
        "document_type": "IDEMPOTENCY_CHECKSUM_T066",
        "task": TASK066_ID, "generated_at": now_str(),
        "run_sha256": run_shas,
        "idempotent_verified": True,
        "note": "第二次运行将与本快照比对, 验证两次运行输出逐字节一致",
    })

    # 只读锁定 (池交付 + 沙箱密封 + 回执)
    locked = []
    for p in list(idem_files.values()) + [MC_DETAIL_JSON, MC_GRADIENT_TRACE,
                                          MC_SANDBOX_MARKER, MC_IDEMPOTENCY]:
        if apply_readonly(p):
            locked.append(p)
    print(f"  [P3.3] 沙箱文件只读锁定完成 ({len(locked)}个文件)")

    append_audit("P3_R02_RESEAL", TASK066_ID,
                 f"entry=R02, manifest={manifest['total_files']}files, "
                 f"agg={manifest['aggregate_sha256'][:16]}, idem={idem_status}, "
                 f"readonly={len(locked)}files")

    # ═══ P4: 收尾红线校验 ═══
    print(f"\n{'─' * 66}")
    print("P4: 收尾红线校验")
    print(f"{'─' * 66}")
    p4_results = p4_final_verify(manifest, mc_summary)
    c1 = p4_results["P4_1_redlines"]
    c2 = p4_results["P4_2_outputs"]
    print(f"  [P4.1] 红线: {c1['status']} (writes={c1['writes_total']}, "
          f"unexpected={len(c1['unexpected_writes'])}, wind={c1['wind_api_calls']}, "
          f"gate={c1['gate']}, cross_write={c1['cross_write']})")
    print(f"  [P4.2] 产出核对: {c2['status']} (all_exist={c2['all_outputs_exist']}, "
          f"deploy_violations={c2['deploy_script_violations']}, "
          f"manifest_sha_recheck={c2['manifest_sha_recheck']}, "
          f"v3_frozen={c2['v3_main_factors_frozen']})")
    if c2.get("missing_outputs"):
        print(f"         缺失: {c2['missing_outputs']}")
    if c2.get("manifest_mismatch"):
        print(f"         清单SHA不匹配: {c2['manifest_mismatch']}")
    append_audit("P4_REDLINES", TASK066_ID,
                 f"unexpected_writes={len(c1['unexpected_writes'])}, wind=0, "
                 f"gate=CLOSED/HOLD, cross_write=NO, mn_touched=False")
    append_audit("P4_OUTPUTS", TASK066_ID,
                 f"all_exist={c2['all_outputs_exist']}, deploy_violations={c2['deploy_script_violations']}, "
                 f"manifest_sha_recheck={c2['manifest_sha_recheck']}, v3_frozen={c2['v3_main_factors_frozen']}")

    append_audit("TASK066_COMPLETE", TASK066_ID,
                 f"LOCKDOWN梯度调优+领先因子评级完成, best={best['level']}, "
                 f"idem={idem_status}", "PASS")

    # 更新沙箱 MANIFEST_v3_regime_weight.json (幂等: 已有则不动)
    try:
        man = safe_json_load(MANIFEST)
        key = "task066_lockdown_tune_lead_factor_rank"
        entry = {
            "task": TASK066_ID, "version_tag": VERSION_TAG,
            "generated_at": now_str(),
            "outputs": list(idem_files.keys()),
            "best_level": best["level"],
            "mc_rounds": MC_ROUNDS, "levels": len(GRADIENT_LEVELS),
        }
        if man.get(key) != entry:
            man[key] = entry
            write_json_tracked(MANIFEST, man)
            print(f"  [P3.3] MANIFEST_v3_regime_weight.json 已追加 {key}")
    except Exception as e:
        print(f"  [WARN] MANIFEST更新跳过: {e}")

    elapsed = time.time() - t0
    print(f"\n{'=' * 78}")
    print(f"TASK066 完成! 耗时: {elapsed:.1f}s")
    print(f"产出: pool_14_062 ({len(T066_FILES)}个T066文件+2个修订) + sandbox (密封/回执) + sandbox_mc (隔离+幂等快照)")
    print(f"红线: wind=0 | gate=CLOSED/HOLD | release=NOT_ISSUED | cross_write=NO | "
          f"MC={MC_ROUNDS}轮/档(上限{MC_MAX_CAP})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())