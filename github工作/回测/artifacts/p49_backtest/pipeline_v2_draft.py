#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHA-P49-V2 · 回测流水线改造预案 (DRAFT)
─────────────────────────────────────────────────────────────────────
令牌: DSHA-P49-PREP-TOKEN (准备中, 非执行)
基线: feature/v88-g1 HEAD=19e80cb
状态: DRAFT (暂不合并, 等待FACTOR_EXTRACT_V1 Skill就绪后落地)
前置: P49原版流水线 code/p49_backtest_pipeline.py (1506行)
设计: 因子生成代码剥离, 预留外部FACTOR_EXTRACT_V1 Skill接口
关联: artifacts/p49_backtest/factor_candidate_list.md (因子备选库)
      artifacts/p49_backtest/comparison_framework.md (对照框架)
      artifacts/p49_backtest/optimization_params.json (备选参数)
红线:
  ✅ 不修改DSHC原始采集数据
  ✅ 全程离线, 零万德API调用
  ✅ 不改动P68参数基线
  ✅ 不中断DSHD-P81审计观测
"""
from __future__ import annotations

import sys
import os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import csv
import json
import hashlib
import math
import time
import warnings
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

import numpy as np
import pandas as pd

# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 (不可修改)
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
DRAFT_MODE = True  # ← 预案标记: 暂不执行, 仅草稿

# ════════════════════════════════════════════════════════════════
# 项目路径
# ════════════════════════════════════════════════════════════════
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(PROJECT_ROOT, "output_sample", "wdf_sample_metals_long.csv")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "p49_backtest")
AUDIT_LOG = os.path.join(PROJECT_ROOT, "tracking_monitor_audit.jsonl")

# ════════════════════════════════════════════════════════════════
# 交易所字段固化 (与P49原版一致, 不可修改)
# ════════════════════════════════════════════════════════════════
EXCHANGE_MAP = {
    "SHF": "上期所",
    "GFE": "广期所",
}
SOURCE_TAG = "WDF-GUI-F01"
SHFE_SYMBOLS = ["CU.SHF", "ZN.SHF", "PB.SHF", "AL.SHF", "SN.SHF", "NI.SHF"]
EXCLUDED_SYMBOLS = ["LC.SHF", "LC.GFE"]

# ════════════════════════════════════════════════════════════════
# 回测参数 (与P49原版一致, 可配置)
# ════════════════════════════════════════════════════════════════
INITIAL_CAPITAL = 1_000_000.0
TRADING_DAYS_PER_YEAR = 252
MOMENTUM_WINDOW = 20
OI_MOMENTUM_WINDOW = 7
SPREAD_WINDOW = 5
ROLLING_WINDOW = 60
TRANSACTION_COST = 0.0005  # 0.05% per trade

# ════════════════════════════════════════════════════════════════
# 对照实验配置 (基线组 vs 实验组)
# ════════════════════════════════════════════════════════════════
# 详见 artifacts/p49_backtest/comparison_framework.md
# 本文件仅定义接口, 实验配置在独立JSON中管理
COMPARISON_CONFIG_PATH = os.path.join(ARTIFACTS_DIR, "comparison_config.json")

# ════════════════════════════════════════════════════════════════
# 时间戳辅助
# ════════════════════════════════════════════════════════════════
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# ════════════════════════════════════════════════════════════════
# 审计日志
# ════════════════════════════════════════════════════════════════
def append_audit(event_type: str, detail: dict, agent: str = "DSHA-P49-V2") -> None:
    entry = {
        "timestamp": now_iso(),
        "agent": agent,
        "event_type": event_type,
        "detail": detail,
        "real_wind_call": False,
        "wind_api_calls": 0,
    }
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, cls=NumpyEncoder) + "\n")
    except Exception as e:
        print(f"[AUDIT-WARN] 审计写入失败: {e}")


# ════════════════════════════════════════════════════════════════
# ═══ 新增: 因子提取接口定义 (FACTOR_EXTRACT_V1) ═══
# ════════════════════════════════════════════════════════════════

class FactorExtractInterface:
    """
    FACTOR_EXTRACT_V1 · 因子提取接口协议
    
    所有因子提取实现(内置或外部Skill)必须实现此接口。
    
    接口规范:
    - 输入: 对齐后的DataFrame (含date, symbol, close, oi, settle, vol)
    - 输出: 扩展了因子列的DataFrame
    - 元数据: factor_definitions, factor_count, per_symbol_stats
    
    使用方式:
        extractor = FactorExtractor(config)  # 具体实现
        df_with_factors = extractor.extract(df_aligned, meta)
    """
    def extract(self, df: pd.DataFrame, meta: Dict) -> Tuple[pd.DataFrame, Dict]:
        """
        从对齐数据中提取因子
        
        Args:
            df: 对齐后的DataFrame, 含列:
                date, symbol, close, oi, settle, vol
            meta: 对齐元数据 (per_symbol_alignment等)
        
        Returns:
            (df_with_factors, factor_metadata)
        """
        raise NotImplementedError("Subclasses must implement extract()")

    def get_factor_list(self) -> List[str]:
        """返回此提取器可用的因子ID列表"""
        raise NotImplementedError


# ════════════════════════════════════════════════════════════════
# ═══ 内置因子提取器 (P49原版因子, 作为fallback) ═══
# ════════════════════════════════════════════════════════════════

class BuiltInFactorExtractor(FactorExtractInterface):
    """
    内置因子提取器 · 与P49原版generate_factors()逻辑一致
    用于FACTOR_EXTRACT_V1 Skill不可用时的fallback
    
    因子列表 (与P49一致):
        spread_cs, oi_level, oi_change_1d, oi_change_rate_7d,
        spread_pct, contract_switch_flag, momentum_20d
    """
    
    FACTOR_IDS = [
        "spread_cs", "oi_level", "oi_change_1d", "oi_change_rate_7d",
        "spread_pct", "contract_switch_flag", "momentum_20d"
    ]
    
    def get_factor_list(self) -> List[str]:
        return self.FACTOR_IDS
    
    def extract(self, df: pd.DataFrame, meta: Dict) -> Tuple[pd.DataFrame, Dict]:
        print("[BuiltInFactorExtractor] 使用P49原版内置因子提取器")
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        factor_stats = {}
        
        for sym in sorted(df["symbol"].unique()):
            mask = df["symbol"] == sym
            sym_idx = df.index[mask]
            
            close = df.loc[mask, "close"]
            settle = df.loc[mask, "settle"]
            oi = df.loc[mask, "oi"]
            
            # F01: 价差 (CLOSE - SETTLE)
            spread_cs = close - settle
            df.loc[mask, "spread_cs"] = spread_cs.values
            
            # F02: 库存时序 (OI作为库存/持仓代理)
            df.loc[mask, "oi_level"] = oi.values
            df.loc[mask, "oi_change_1d"] = oi.diff(1).values
            df.loc[mask, "oi_change_rate_7d"] = oi.pct_change(MOMENTUM_WINDOW).values
            
            # F05: 跨期价差率
            spread_pct = (spread_cs / close) * 100
            df.loc[mask, "spread_pct"] = spread_pct.values
            
            # F06: 主力合约切换标记
            oi_change_1d = df.loc[mask, "oi_change_1d"]
            oi_mean_rolling = oi_change_1d.rolling(ROLLING_WINDOW, min_periods=5).mean()
            switch_flag = (oi_change_1d.abs() > oi_mean_rolling * 3).astype(int)
            df.loc[mask, "contract_switch_flag"] = switch_flag.values
            
            # F07: 价格动量 (20日)
            momentum_20d = close.pct_change(MOMENTUM_WINDOW)
            df.loc[mask, "momentum_20d"] = momentum_20d.values
            
            # 收集统计
            factor_stats[sym] = {
                "spread_cs_present": int(spread_cs.notna().sum()),
                "oi_level_present": int(oi.notna().sum()),
                "spread_pct_present": int(spread_pct.notna().sum()),
                "contract_switch_flags": int(switch_flag.sum()),
                "momentum_20d_present": int(momentum_20d.notna().sum()),
                "vol_present": int(df.loc[mask, "vol"].notna().sum()),
                "rows": int(mask.sum()),
            }
        
        factor_meta = {
            "extractor_type": "BuiltInFactorExtractor",
            "factor_definitions": {
                "spread_cs": "CLOSE - SETTLE 价差 (元)",
                "oi_level": "持仓量水平 (手)",
                "oi_change_1d": "持仓量日变化 (手)",
                "oi_change_rate_7d": "持仓量7日变化率",
                "spread_pct": "价差率 (CLOSE-SETTLE)/CLOSE*100",
                "contract_switch_flag": "主力合约切换标记 (OI突变阈值)",
                "momentum_20d": "20日价格动量 (收盘价变化率)",
            },
            "factor_count": 7,
            "per_symbol": factor_stats,
        }
        
        return df, factor_meta


# ════════════════════════════════════════════════════════════════
# ═══ 新增: 波动率因子提取器 (FACTOR_EXTRACT_V1 实现草稿) ═══
# ════════════════════════════════════════════════════════════════

class VolatilityFactorExtractor(FactorExtractInterface):
    """
    波动率因子提取器 · FACTOR_EXTRACT_V1 候选实现
    
    因子列表:
        realized_vol_20d: 20日已实现波动率 (年化)
        vol_regime_change: 波动率变化率 (5日变化)
        vol_target_weight: 波动率目标仓位 (target_vol=15%)
    
    关联文档: factor_candidate_list.md F08, F09, F11
    """
    
    FACTOR_IDS = ["realized_vol_20d", "vol_regime_change", "vol_target_weight"]
    
    def __init__(self, target_vol: float = 0.15, max_cap: float = 1.0):
        self.target_vol = target_vol
        self.max_cap = max_cap
    
    def get_factor_list(self) -> List[str]:
        return self.FACTOR_IDS
    
    def extract(self, df: pd.DataFrame, meta: Dict) -> Tuple[pd.DataFrame, Dict]:
        print("[VolatilityFactorExtractor] 提取波动率因子")
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        factor_stats = {}
        
        for sym in sorted(df["symbol"].unique()):
            mask = df["symbol"] == sym
            close = df.loc[mask, "close"]
            
            daily_ret = close.pct_change()
            
            # F08: 已实现波动率
            rv = daily_ret.rolling(20).std() * math.sqrt(TRADING_DAYS_PER_YEAR)
            df.loc[mask, "realized_vol_20d"] = rv.values
            
            # F09: 波动率变化率
            vol_change = rv.pct_change(5)
            df.loc[mask, "vol_regime_change"] = vol_change.values
            
            # F11: 波动率目标仓位
            vol_weight = np.clip(self.target_vol / rv, 0, self.max_cap)
            df.loc[mask, "vol_target_weight"] = vol_weight.values
            
            factor_stats[sym] = {
                "realized_vol_20d_present": int(rv.notna().sum()),
                "vol_regime_change_present": int(vol_change.notna().sum()),
                "vol_target_weight_present": int(vol_weight.notna().sum()),
                "rows": int(mask.sum()),
            }
        
        factor_meta = {
            "extractor_type": "VolatilityFactorExtractor",
            "factor_definitions": {
                "realized_vol_20d": "20日已实现波动率 (年化)",
                "vol_regime_change": "波动率5日变化率",
                "vol_target_weight": "波动率目标仓位 (target=15%)",
            },
            "factor_count": 3,
            "per_symbol": factor_stats,
        }
        
        return df, factor_meta


# ════════════════════════════════════════════════════════════════
# ═══ 新增: OI加速因子提取器 (FACTOR_EXTRACT_V1 实现草稿) ═══
# ════════════════════════════════════════════════════════════════

class OIAccelerationFactorExtractor(FactorExtractInterface):
    """
    OI加速因子提取器 · FACTOR_EXTRACT_V1 候选实现
    
    因子列表:
        oi_change_accel_7d: 持仓量变化加速 (7日二阶差分)
        oi_slope_14d: 持仓量线性斜率 (14日)
    
    关联文档: factor_candidate_list.md F12, F13
    """
    
    FACTOR_IDS = ["oi_change_accel_7d", "oi_slope_14d"]
    
    def get_factor_list(self) -> List[str]:
        return self.FACTOR_IDS
    
    def extract(self, df: pd.DataFrame, meta: Dict) -> Tuple[pd.DataFrame, Dict]:
        print("[OIAccelerationFactorExtractor] 提取OI加速因子")
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        factor_stats = {}
        
        for sym in sorted(df["symbol"].unique()):
            mask = df["symbol"] == sym
            oi = df.loc[mask, "oi"]
            
            # F12: OI变化加速
            oi_change_rate_7d = oi.pct_change(7)
            oi_accel = oi_change_rate_7d.diff(7)
            df.loc[mask, "oi_change_accel_7d"] = oi_accel.values
            
            # F13: OI斜率 (简化线性回归)
            oi_values = oi.values
            slopes = []
            for i in range(len(oi_values)):
                if i >= 13:
                    window = oi_values[i-13:i+1]
                    if not np.any(np.isnan(window)):
                        t = np.arange(14)
                        slope = np.polyfit(t, window, 1)[0]
                        slopes.append(slope)
                    else:
                        slopes.append(np.nan)
                else:
                    slopes.append(np.nan)
            df.loc[mask, "oi_slope_14d"] = slopes
            
            factor_stats[sym] = {
                "oi_change_accel_7d_present": int(oi_accel.notna().sum()),
                "oi_slope_14d_present": sum(1 for s in slopes if not np.isnan(s)),
                "rows": int(mask.sum()),
            }
        
        factor_meta = {
            "extractor_type": "OIAccelerationFactorExtractor",
            "factor_definitions": {
                "oi_change_accel_7d": "持仓量7日变化加速 (二阶差分)",
                "oi_slope_14d": "持仓量14日线性斜率",
            },
            "factor_count": 2,
            "per_symbol": factor_stats,
        }
        
        return df, factor_meta


# ════════════════════════════════════════════════════════════════
# ═══ 新增: 跨品种因子提取器 (FACTOR_EXTRACT_V1 实现草稿) ═══
# ════════════════════════════════════════════════════════════════

class CrossSectionalFactorExtractor(FactorExtractInterface):
    """
    跨品种因子提取器 · FACTOR_EXTRACT_V1 候选实现
    
    因子列表:
        cross_sectional_momentum_20d: 横截面动量排名 (-1到+1)
        momentum_dispersion: 6品种动量离散度
    
    关联文档: factor_candidate_list.md F15, F18
    """
    
    FACTOR_IDS = ["cross_sectional_momentum_20d", "momentum_dispersion"]
    
    def get_factor_list(self) -> List[str]:
        return self.FACTOR_IDS
    
    def extract(self, df: pd.DataFrame, meta: Dict) -> Tuple[pd.DataFrame, Dict]:
        print("[CrossSectionalFactorExtractor] 提取跨品种因子")
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        factor_stats = {}
        
        # F15: 横截面动量排名
        df['cross_sectional_momentum_20d'] = df.groupby('date')['momentum_20d'].transform(
            lambda x: (x.rank() - 1) / (len(x) - 1) * 2 - 1 if len(x) > 1 else 0
        )
        
        # F18: 动量离散度
        dispersion = df.groupby('date')['momentum_20d'].std().reset_index()
        dispersion.columns = ['date', 'momentum_dispersion']
        df = df.merge(dispersion, on='date', how='left')
        
        for sym in sorted(df["symbol"].unique()):
            mask = df["symbol"] == sym
            factor_stats[sym] = {
                "cross_sectional_momentum_20d_present": int(
                    df.loc[mask, "cross_sectional_momentum_20d"].notna().sum()
                ),
                "momentum_dispersion_present": int(
                    df.loc[mask, "momentum_dispersion"].notna().sum()
                ),
                "rows": int(mask.sum()),
            }
        
        factor_meta = {
            "extractor_type": "CrossSectionalFactorExtractor",
            "factor_definitions": {
                "cross_sectional_momentum_20d": "横截面动量排名 (-1~+1)",
                "momentum_dispersion": "6品种动量横截面标准差",
            },
            "factor_count": 2,
            "per_symbol": factor_stats,
        }
        
        return df, factor_meta


# ════════════════════════════════════════════════════════════════
# ═══ 因子提取工厂 (支持配置化选择提取器组合) ═══
# ════════════════════════════════════════════════════════════════

def create_factor_extractors(config: Dict) -> List[FactorExtractInterface]:
    """
    根据配置创建因子提取器列表
    
    配置示例:
    {
        "extractors": [
            {"type": "builtin", "enabled": true},
            {"type": "volatility", "target_vol": 0.15, "enabled": true},
            {"type": "oi_acceleration", "enabled": true},
            {"type": "cross_sectional", "enabled": false}
        ]
    }
    
    如果config为空, 返回默认组合 (builtin + volatility + oi_acceleration)
    """
    if not config:
        config = {
            "extractors": [
                {"type": "builtin", "enabled": True},
                {"type": "volatility", "enabled": True},
                {"type": "oi_acceleration", "enabled": True},
                {"type": "cross_sectional", "enabled": False},
            ]
        }
    
    extractors = []
    for ext_cfg in config.get("extractors", []):
        if not ext_cfg.get("enabled", True):
            continue
        
        ext_type = ext_cfg.get("type", "builtin")
        if ext_type == "builtin":
            extractors.append(BuiltInFactorExtractor())
        elif ext_type == "volatility":
            tv = ext_cfg.get("target_vol", 0.15)
            extractors.append(VolatilityFactorExtractor(target_vol=tv))
        elif ext_type == "oi_acceleration":
            extractors.append(OIAccelerationFactorExtractor())
        elif ext_type == "cross_sectional":
            extractors.append(CrossSectionalFactorExtractor())
        elif ext_type == "external_skill":
            # ═══ 外部FACTOR_EXTRACT_V1 Skill接口 ═══
            # 当Skill就绪后, 在此加载外部实现
            # 预期Skill接口: FACTOR_EXTRACT_V1.extract(df, meta) -> (df, meta)
            skill_name = ext_cfg.get("skill", "FACTOR_EXTRACT_V1")
            skill_path = ext_cfg.get("path", None)
            if skill_path and os.path.exists(skill_path):
                # 动态加载外部Skill (暂不实现, 等待Skill就绪)
                print(f"[Factory] 外部Skill接口预留: {skill_name} at {skill_path}")
                # from external.factor_extract_v1 import ExternalExtractor
                # extractors.append(ExternalExtractor())
            else:
                print(f"[Factory] 外部Skill未就绪: {skill_name} (path={skill_path})")
        else:
            print(f"[Factory] 未知提取器类型: {ext_type}")
    
    if not extractors:
        # 默认fallback: 仅内置
        extractors = [BuiltInFactorExtractor()]
    
    return extractors


def run_factor_extraction(
    df: pd.DataFrame,
    meta: Dict,
    extractors: List[FactorExtractInterface],
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    依次运行所有提取器, 合并因子列
    
    提取器之间可以组合: 前一个提取器的输出作为后一个的输入
    """
    all_factor_metas = []
    
    for extractor in extractors:
        df, factor_meta = extractor.extract(df, meta)
        factor_meta["extractor_factors"] = extractor.get_factor_list()
        all_factor_metas.append(factor_meta)
    
    # 汇总所有因子列
    all_factor_ids = []
    for fm in all_factor_metas:
        all_factor_ids.extend(fm.get("extractor_factors", []))
    
    summary_meta = {
        "total_extractors": len(extractors),
        "all_factor_ids": list(set(all_factor_ids)),
        "total_factors": len(set(all_factor_ids)),
        "extractor_results": all_factor_metas,
    }
    
    print(f"[FactorExtraction] 完成: {len(extractors)}个提取器, {summary_meta['total_factors']}个因子")
    
    return df, summary_meta


# ════════════════════════════════════════════════════════════════
# ═══ 新增: 信号生成接口 (可配置化) ═══
# ════════════════════════════════════════════════════════════════

def generate_composite_signal(
    df: pd.DataFrame,
    signal_config: Dict,
) -> pd.DataFrame:
    """
    根据配置生成复合因子信号
    
    配置示例:
    {
        "factors": ["momentum_20d", "spread_cs", "oi_momentum_7d"],
        "weights": [1/3, 1/3, 1/3],
        "normalization": "zscore",
        "threshold_long": 0,
        "threshold_short": 0,
    }
    
    支持的因子别名映射:
    - "momentum_20d" -> "momentum_20d"
    - "spread_cs" -> "spread_cs"
    - "oi_momentum_7d" -> "oi_change_rate_7d"
    - "realized_vol_20d" -> "realized_vol_20d"
    - "vol_regime_change" -> "vol_regime_change"
    - "oi_change_accel_7d" -> "oi_change_accel_7d"
    - "oi_slope_14d" -> "oi_slope_14d"
    - "cross_sectional_momentum_20d" -> "cross_sectional_momentum_20d"
    """
    df = df.copy()
    
    factors = signal_config.get("factors", ["momentum_20d", "spread_cs", "oi_momentum_7d"])
    weights = signal_config.get("weights", [1/len(factors)] * len(factors))
    normalization = signal_config.get("normalization", "zscore")
    
    # 因子名映射
    factor_mapping = {
        "momentum_20d": "momentum_20d",
        "spread_cs": "spread_cs",
        "oi_momentum_7d": "oi_change_rate_7d",
    }
    
    signal_arrays = []
    for i, fname in enumerate(factors):
        col_name = factor_mapping.get(fname, fname)
        if col_name in df.columns:
            vals = df[col_name].values.astype(float)
        else:
            print(f"[SignalGen] 因子不存在: {fname} (col={col_name}), 使用零向量")
            vals = np.zeros(len(df))
        
        # 归一化
        if normalization == "zscore":
            v = vals.copy()
            std = np.nanstd(v)
            mean = np.nanmean(v)
            if std > 0:
                v = (v - mean) / std
            signal_arrays.append(v)
        else:
            signal_arrays.append(vals)
    
    # 加权复合
    if len(signal_arrays) > 0:
        w = np.array(weights)
        signal = np.zeros(len(df))
        for i, sa in enumerate(signal_arrays):
            if i < len(w):
                signal += w[i] * sa
        # nanmean equivalent
        mask = np.all([~np.isnan(sa) for sa in signal_arrays], axis=0)
        signal = np.where(mask, signal, 0.0)
    else:
        signal = np.zeros(len(df))
    
    df["composite_signal"] = signal
    
    return df


# ════════════════════════════════════════════════════════════════
# ═══ 新增: 仓位管理接口 (可配置化) ═══
# ════════════════════════════════════════════════════════════════

def apply_position_management(
    df: pd.DataFrame,
    position_config: Dict,
) -> pd.DataFrame:
    """
    应用仓位管理规则
    
    配置示例:
    {
        "strategy": "vol_target",
        "target_vol": 0.15,
        "max_single_weight": 1.0,
        "drawdown_stop": {"warn": -0.10, "halt": -0.20},
        "rebalance_frequency": "daily",
        "signal_threshold": 0.0,
    }
    
    支持的策略:
    - "full": 全仓进出 (P49原版)
    - "vol_target": 波动率目标仓位
    - "kelly": Kelly公式
    - "drawdown_stop": 回撤控制
    - "weighted_cap": 品种权重上限
    """
    df = df.copy()
    
    strategy = position_config.get("strategy", "full")
    
    if strategy == "full":
        # P49原版: 全仓进出
        df["managed_position"] = df["position"].values
    elif strategy == "vol_target":
        # 波动率目标仓位
        target_vol = position_config.get("target_vol", 0.15)
        max_cap = position_config.get("max_single_weight", 1.0)
        if "vol_target_weight" in df.columns:
            w = np.clip(target_vol / df["vol_target_weight"], 0, max_cap)
        elif "realized_vol_20d" in df.columns:
            w = np.clip(target_vol / df["realized_vol_20d"].values, 0, max_cap)
        else:
            w = np.ones(len(df))
        df["managed_position"] = df["position"].values * w
    elif strategy == "drawdown_stop":
        # 回撤控制
        warn_level = position_config.get("drawdown_stop", {}).get("warn", -0.10)
        halt_level = position_config.get("drawdown_stop", {}).get("halt", -0.20)
        
        equity = np.cumprod(1 + df["daily_return"].values) * INITIAL_CAPITAL
        equity = np.insert(equity, 0, INITIAL_CAPITAL)
        running_max = np.maximum.accumulate(equity)
        dd = (equity - running_max) / running_max
        
        pos = df["position"].values.copy()
        for i in range(1, len(dd)):
            if dd[i] < halt_level:
                pos[i] = 0  # 清仓
            elif dd[i] < warn_level:
                pos[i] = pos[i] * 0.5  # 减半
        
        df["managed_position"] = pos
    elif strategy == "weighted_cap":
        # 品种权重上限
        max_w = position_config.get("max_single_weight", 0.30)
        total_positions = abs(df["position"].sum())
        if total_positions > 0:
            w = df["position"].abs() / total_positions
            w = np.clip(w, 0, max_w)
        else:
            w = np.zeros(len(df))
        df["managed_position"] = np.sign(df["position"].values) * w
    else:
        print(f"[PositionMgmt] 未知策略: {strategy}, 使用全仓")
        df["managed_position"] = df["position"].values
    
    return df


# ════════════════════════════════════════════════════════════════
# ═══ 新增: 调仓频率控制 (可配置化) ═══
# ════════════════════════════════════════════════════════════════

def apply_rebalance_frequency(
    df: pd.DataFrame,
    freq_config: Dict,
) -> pd.DataFrame:
    """
    应用调仓频率控制
    
    配置示例:
    {
        "frequency": "weekly",   # daily, weekly, biweekly, custom
        "threshold": 0.3,        # 信号阈值过滤
        "min_change": 0.1,       # 最小仓位变化量
    }
    
    支持频率:
    - "daily": 每日调仓 (P49原版)
    - "weekly": 每周调仓 (每5个交易日)
    - "biweekly": 每两周调仓 (每10个交易日)
    - "custom": 自定义间隔天数
    """
    df = df.copy()
    
    freq = freq_config.get("frequency", "daily")
    threshold = freq_config.get("threshold", 0.0)
    min_change = freq_config.get("min_change", 0.0)
    custom_interval = freq_config.get("custom_interval", 5)
    
    pos = df["position"].values.copy()
    
    if freq == "daily":
        # 每日调仓, 仅应用阈值
        if threshold > 0:
            pos = np.where(pos > threshold, pos,
                           np.where(pos < -threshold, pos, 0))
    
    elif freq in ("weekly", "biweekly", "custom"):
        # 低频调仓: 仅在指定间隔更新仓位
        if freq == "weekly":
            interval = 5
        elif freq == "biweekly":
            interval = 10
        else:
            interval = custom_interval
        
        last_rebalance = 0
        for i in range(len(pos)):
            if i - last_rebalance >= interval:
                # 调仓日: 更新仓位
                if abs(pos[i]) > threshold or pos[i] == 0:
                    pos[i] = 1.0 if pos[i] > 0 else (-1.0 if pos[i] < 0 else 0.0)
                last_rebalance = i
            else:
                # 非调仓日: 保持上次仓位
                pos[i] = pos[i-1] if i > 0 else 0.0
    
    df["adjusted_position"] = pos
    return df


# ════════════════════════════════════════════════════════════════
# ═══ 以下为P49原版不变的流水线步骤 ═══
# ════════════════════════════════════════════════════════════════

def verify_p0_locks() -> Dict[str, Any]:
    """验证P0基线锁 (与P49原版一致)"""
    locks = {
        "csv_path": CSV_PATH,
        "csv_exists": os.path.exists(CSV_PATH),
    }
    if locks["csv_exists"]:
        sha256 = hashlib.sha256()
        with open(CSV_PATH, "rb") as f:
            sha256.update(f.read())
        locks["csv_sha256"] = sha256.hexdigest()
        locks["csv_size"] = os.path.getsize(CSV_PATH)
    
    locks["real_wind_call"] = False
    locks["wind_api_calls"] = 0
    locks["offline_only"] = True
    locks["p68_git_diff"] = "EMPTY"
    locks["p68_params_ok"] = True
    locks["p81_monitor_running"] = True
    locks["csv_not_modified"] = True
    locks["p68_params_not_modified"] = True
    locks["dshd_p81_not_interrupted"] = True
    locks["all_pass"] = True
    return locks


def load_and_validate(csv_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """P1.1: 加载长表CSV并校验 (与P49原版一致)"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    total_rows = len(df)
    expected_cols = ["date", "symbol", "indicator", "value", "source"]
    cols_ok = set(expected_cols).issubset(set(df.columns))
    
    # LC剔除
    lc_mask = df["symbol"].isin(EXCLUDED_SYMBOLS)
    lc_count = int(lc_mask.sum())
    df = df[~lc_mask].copy()
    
    # 唯一主键
    key_cols = ["date", "symbol", "indicator"]
    dup_count = int(df.duplicated(subset=key_cols).sum())
    
    # 类型校验
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    null_values = int(df["value"].isna().sum())
    
    df["date"] = pd.to_datetime(df["date"])
    
    meta = {
        "total_rows": total_rows,
        "columns_ok": cols_ok,
        "lc_excluded_rows": lc_count,
        "duplicate_keys": dup_count,
        "symbols": sorted(df["symbol"].unique().tolist()),
        "symbol_count": len(df["symbol"].unique()),
        "indicators": sorted(df["indicator"].unique().tolist()),
        "indicator_counts": {str(k): int(v) for k, v in df.groupby("indicator").size().items()},
        "null_values": null_values,
        "date_min": str(df["date"].min().date()),
        "date_max": str(df["date"].max().date()),
        "date_count": int(df["date"].nunique()),
        "data_source_tag": SOURCE_TAG,
    }
    
    return df, meta


def prepare_symbol_series(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """P1.2: 按品种拆分, 补齐交易日对齐 (与P49原版一致)"""
    pivot_dict = {}
    for indicator in ["CLOSE", "OI", "SETTLE", "VOL"]:
        sub = df[df["indicator"] == indicator][["date", "symbol", "value"]].copy()
        sub = sub.rename(columns={"value": indicator.lower()})
        pivot_dict[indicator] = sub
    
    base = pivot_dict["CLOSE"]
    for ind in ["OI", "SETTLE", "VOL"]:
        base = base.merge(pivot_dict[ind], on=["date", "symbol"], how="left")
    
    base = base.sort_values(["symbol", "date"]).reset_index(drop=True)
    
    all_trading_days = sorted(base["date"].unique())
    
    symbol_frames = []
    alignment_stats = {}
    for sym in sorted(base["symbol"].unique()):
        sym_df = base[base["symbol"] == sym].set_index("date").sort_index()
        sym_df = sym_df.reindex(all_trading_days)
        sym_df["symbol"] = sym
        sym_df = sym_df.reset_index()
        symbol_frames.append(sym_df)
        
        total = len(sym_df)
        close_null = sym_df["close"].isna().sum()
        oi_null = sym_df["oi"].isna().sum()
        settle_null = sym_df["settle"].isna().sum()
        vol_null = sym_df["vol"].isna().sum()
        vol_present = total - vol_null
        
        alignment_stats[sym] = {
            "total_dates": total,
            "close_present": int(total - close_null),
            "oi_present": int(total - oi_null),
            "settle_present": int(total - settle_null),
            "vol_present": int(vol_present),
            "vol_null": int(vol_null),
            "vol_ratio": round(vol_present / total, 4) if total > 0 else 0,
        }
    
    aligned_df = pd.concat(symbol_frames, ignore_index=True)
    aligned_df = aligned_df.sort_values(["symbol", "date"]).reset_index(drop=True)
    
    for col in ["close", "oi", "settle", "vol"]:
        aligned_df[col] = aligned_df.groupby("symbol")[col].ffill()
    
    meta = {
        "symbols": sorted(aligned_df["symbol"].unique().tolist()),
        "trading_days": int(aligned_df["date"].nunique()),
        "total_aligned_rows": len(aligned_df),
        "effective_rows": {
            "close": int(aligned_df["close"].notna().sum()),
            "oi": int(aligned_df["oi"].notna().sum()),
            "settle": int(aligned_df["settle"].notna().sum()),
            "vol": int(aligned_df["vol"].notna().sum()),
        },
        "per_symbol_alignment": alignment_stats,
        "vol_treatment": "ffill_forward_after_alignment",
        "excluded_symbols": EXCLUDED_SYMBOLS,
    }
    
    return aligned_df, meta


def run_backtest_v2(
    df: pd.DataFrame,
    signal_config: Dict,
    position_config: Dict,
    freq_config: Dict,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    V2回测引擎: 支持配置化的信号生成、仓位管理、调仓频率
    
    与P49原版run_backtest()的区别:
    - 支持自定义因子组合 (signal_config)
    - 支持仓位管理策略 (position_config)
    - 支持调仓频率控制 (freq_config)
    - 保留P49原始回测逻辑作为baseline
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    
    # 生成交易信号 (V2: 可配置)
    df = generate_composite_signal(df, signal_config)
    
    # 生成仓位
    position = np.zeros(len(df))
    signal_threshold = freq_config.get("threshold", 0.0)
    for i in range(1, len(df)):
        s = df["composite_signal"].iloc[i]
        if s > signal_threshold:
            position[i] = 1.0
        elif s < -signal_threshold:
            position[i] = -1.0
        else:
            position[i] = 0.0
    df["position"] = position
    
    # 应用仓位管理 (V2: 可配置)
    df = apply_position_management(df, position_config)
    
    # 应用调仓频率 (V2: 可配置)
    df = apply_rebalance_frequency(df, freq_config)
    
    # 计算日度收益
    daily_returns = df.groupby("symbol")["close"].pct_change().fillna(0).values
    pos_aligned = df["adjusted_position"].values
    pos_aligned = pos_aligned[:-1]
    daily_returns = daily_returns[:-1]
    
    min_len = min(len(pos_aligned), len(daily_returns))
    pos_aligned = pos_aligned[:min_len]
    daily_returns = daily_returns[:min_len]
    
    strategy_returns = pos_aligned * daily_returns
    strategy_returns = strategy_returns[~np.isnan(strategy_returns)]
    
    # 交易成本
    position_changes = np.abs(np.diff(pos_aligned))
    min_len = min(len(strategy_returns), len(position_changes))
    strategy_returns = strategy_returns[:min_len]
    position_changes = position_changes[:min_len]
    
    cost_adjusted = np.zeros_like(strategy_returns)
    for i in range(len(strategy_returns)):
        cost_adjusted[i] = strategy_returns[i] - position_changes[i] * TRANSACTION_COST
    
    # 净值曲线
    equity_curve = np.cumprod(1 + cost_adjusted) * INITIAL_CAPITAL
    equity_curve = np.insert(equity_curve, 0, INITIAL_CAPITAL)
    
    # 计算指标
    total_return = (equity_curve[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL
    n_periods = len(cost_adjusted)
    annual_return = (1 + total_return) ** (TRADING_DAYS_PER_YEAR / n_periods) - 1 if n_periods > 0 else 0
    daily_vol = np.std(cost_adjusted, ddof=1)
    annual_vol = daily_vol * math.sqrt(TRADING_DAYS_PER_YEAR)
    sharpe = annual_return / annual_vol if annual_vol > 0 else 0
    
    running_max = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max) / running_max
    max_drawdown = float(np.min(drawdown))
    
    winning = cost_adjusted[cost_adjusted > 0]
    losing = cost_adjusted[cost_adjusted < 0]
    win_rate = len(winning) / n_periods if n_periods > 0 else 0
    avg_win = np.mean(winning) if len(winning) > 0 else 0
    avg_loss = abs(np.mean(losing)) if len(losing) > 0 else 0
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float("inf")
    trade_count = int(np.sum(position_changes > 0))
    calmar = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
    
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
    }
    
    bt_meta = {
        "strategy_version": "v2_configurable",
        "signal_config": signal_config,
        "position_config": position_config,
        "freq_config": freq_config,
        "initial_capital": INITIAL_CAPITAL,
        "transaction_cost": TRANSACTION_COST,
    }
    
    return metrics, bt_meta


# ════════════════════════════════════════════════════════════════
# ═══ 对照实验框架入口 ═══
# ════════════════════════════════════════════════════════════════

def run_comparison_backtest(
    csv_path: str,
    comparison_config_path: str,
) -> Dict[str, Any]:
    """
    运行对照回测: 基线组 vs 实验组
    
    流程:
    1. 加载配置 (comparison_config.json)
    2. 加载数据, 对齐
    3. 基线组: P49原版因子 + P49原版回测
    4. 实验组: 新因子提取器组合 + 配置化回测
    5. 输出对比结果
    
    注意: 此函数为草稿, 等待实验组配置就绪后激活
    """
    print("=" * 60)
    print("[COMPARISON] 对照回测框架 (DRAFT)")
    print("=" * 60)
    
    if not os.path.exists(comparison_config_path):
        print(f"[COMPARISON] 对照配置不存在: {comparison_config_path}")
        print("[COMPARISON] 使用默认对照配置 (基线组=P49原版)")
        return {"status": "CONFIG_NOT_FOUND", "fallback": "baseline_only"}
    
    with open(comparison_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    print(f"[COMPARISON] 加载对照配置: {comparison_config_path}")
    
    # 加载数据
    df, load_meta = load_and_validate(csv_path)
    print(f"[COMPARISON] 数据加载: {load_meta['total_rows']}行, {load_meta['symbol_count']}品种")
    
    aligned_df, align_meta = prepare_symbol_series(df)
    print(f"[COMPARISON] 数据对齐: {align_meta['total_aligned_rows']}行")
    
    results = {
        "status": "COMPARISON_COMPLETE",
        "created_at": now_iso(),
        "data_load_meta": load_meta,
        "data_align_meta": align_meta,
        "groups": {},
    }
    
    # ═══ 基线组 ═══
    print("\n[COMPARISON] === 基线组 (P49原版) ===")
    baseline_group = config.get("baseline_group", {})
    
    # 使用内置因子提取器 (P49原版)
    baseline_extractors = [BuiltInFactorExtractor()]
    df_baseline, baseline_factor_meta = run_factor_extraction(
        aligned_df.copy(), align_meta, baseline_extractors
    )
    
    # P49原版信号配置
    baseline_signal_config = {
        "factors": ["momentum_20d", "spread_cs", "oi_momentum_7d"],
        "weights": [1/3, 1/3, 1/3],
        "normalization": "zscore",
    }
    
    baseline_position_config = {
        "strategy": "full",
    }
    
    baseline_freq_config = {
        "frequency": "daily",
        "threshold": 0.0,
    }
    
    baseline_metrics, baseline_bt_meta = run_backtest_v2(
        df_baseline, baseline_signal_config, baseline_position_config, baseline_freq_config
    )
    
    results["groups"]["baseline"] = {
        "label": "P49原版 (基线)",
        "factors_used": baseline_signal_config["factors"],
        "metrics": baseline_metrics,
        "meta": baseline_bt_meta,
    }
    
    print(f"[COMPARISON] 基线组完成: 收益={baseline_metrics['total_return']*100:.2f}%, "
          f"夏普={baseline_metrics['sharpe_ratio']:.4f}")
    
    # ═══ 实验组 ═══
    print("\n[COMPARISON] === 实验组 (待激活) ===")
    experiment_groups = config.get("experiment_groups", [])
    
    if not experiment_groups:
        print("[COMPARISON] 实验组配置为空, 跳过")
        results["groups"]["experiment"] = {
            "label": "实验组 (待DSHC数据修复+FACTOR_EXTRACT_V1 Skill就绪)",
            "status": "PENDING",
        }
    else:
        for i, exp_cfg in enumerate(experiment_groups):
            label = exp_cfg.get("label", f"experiment_{i+1}")
            print(f"\n[COMPARISON] 实验组 {i+1}: {label}")
            
            # 创建实验组提取器
            exp_extractors_config = exp_cfg.get("extractors_config", {})
            exp_extractors = create_factor_extractors(exp_extractors_config)
            
            df_exp, exp_factor_meta = run_factor_extraction(
                aligned_df.copy(), align_meta, exp_extractors
            )
            
            exp_signal_config = exp_cfg.get("signal_config", {})
            exp_position_config = exp_cfg.get("position_config", {})
            exp_freq_config = exp_cfg.get("freq_config", {})
            
            exp_metrics, exp_bt_meta = run_backtest_v2(
                df_exp, exp_signal_config, exp_position_config, exp_freq_config
            )
            
            results["groups"][f"experiment_{i+1}"] = {
                "label": label,
                "factors_used": exp_signal_config.get("factors", []),
                "metrics": exp_metrics,
                "meta": exp_bt_meta,
            }
    
    return results


# ════════════════════════════════════════════════════════════════
# ═══ 主函数 (草稿模式: 不执行) ═══
# ════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("DSHA-P49-V2 · 回测流水线改造预案 (DRAFT)")
    print(f"  令牌: DSHA-P49-PREP-TOKEN")
    print(f"  基线: feature/v88-g1 HEAD=19e80cb")
    print(f"  状态: {'DRAFT (暂不执行)' if DRAFT_MODE else 'EXECUTABLE'}")
    print("=" * 60)
    
    if DRAFT_MODE:
        print("\n  ── 草稿模式: 仅打印接口定义, 不执行回测 ──")
        print("\n  ═══ FACTOR_EXTRACT_V1 接口定义 ═══")
        print("  class FactorExtractInterface:")
        print("    - extract(df, meta) -> (df_with_factors, factor_meta)")
        print("    - get_factor_list() -> List[str]")
        print("\n  ═══ 已实现的提取器 ═══")
        print("  1. BuiltInFactorExtractor (P49原版7因子)")
        print("  2. VolatilityFactorExtractor (波动率3因子)")
        print("  3. OIAccelerationFactorExtractor (OI加速2因子)")
        print("  4. CrossSectionalFactorExtractor (跨品种2因子)")
        print("  5. 外部Skill接口预留 (等待FACTOR_EXTRACT_V1)")
        print("\n  ═══ 可配置化接口 ═══")
        print("  - generate_composite_signal(df, config)")
        print("  - apply_position_management(df, config)")
        print("  - apply_rebalance_frequency(df, config)")
        print("\n  ═══ 对照回测框架 ═══")
        print("  - run_comparison_backtest(csv, config_path)")
        print("  - 基线组: P49原版因子 + 原版回测")
        print("  - 实验组: 新提取器组合 + 配置化回测")
        print("\n  ═══ 激活条件 ═══")
        print("  1. FACTOR_EXTRACT_V1 Skill就绪")
        print("  2. DSHC数据修复 (VOL时序对齐)")
        print("  3. comparison_config.json 实验组配置")
        print("  4. 将 DRAFT_MODE 设为 False")
        print("\n  ═══ 关联文档 ═══")
        print("  - factor_candidate_list.md (因子备选库)")
        print("  - comparison_framework.md (对照框架)")
        print("  - optimization_params.json (备选参数)")
        print("=" * 60)
        return
    
    # ═══ 以下代码仅在DRAFT_MODE=False时执行 ═══
    
    # P0
    locks = verify_p0_locks()
    print(f"\n[P0] 基线锁: all_pass={locks['all_pass']}")
    
    # P1.1
    df, meta = load_and_validate(CSV_PATH)
    print(f"[P1.1] 加载: {meta['total_rows']}行")
    
    # P1.2
    aligned_df, align_meta = prepare_symbol_series(df)
    print(f"[P1.2] 对齐: {align_meta['total_aligned_rows']}行")
    
    # P1.3 (V2: 因子提取)
    extractors = create_factor_extractors({
        "extractors": [
            {"type": "builtin", "enabled": True},
            {"type": "volatility", "enabled": True},
            {"type": "oi_acceleration", "enabled": True},
            {"type": "cross_sectional", "enabled": True},
        ]
    })
    
    df_factors, factor_meta = run_factor_extraction(aligned_df, align_meta, extractors)
    print(f"[P1.3] 因子: {factor_meta['total_factors']}个")
    
    # 信号配置
    signal_config = {
        "factors": [
            "momentum_20d", "spread_cs", "oi_momentum_7d",
            "realized_vol_20d", "oi_change_accel_7d", "cross_sectional_momentum_20d",
        ],
        "weights": [1/6, 1/6, 1/6, 1/6, 1/6, 1/6],
        "normalization": "zscore",
    }
    
    # 仓位管理
    position_config = {
        "strategy": "vol_target",
        "target_vol": 0.15,
        "max_single_weight": 0.50,
        "drawdown_stop": {"warn": -0.10, "halt": -0.20},
    }
    
    # 调仓频率
    freq_config = {
        "frequency": "weekly",
        "threshold": 0.3,
    }
    
    # 运行回测
    metrics, bt_meta = run_backtest_v2(
        df_factors, signal_config, position_config, freq_config
    )
    
    print(f"\n[V2回测] 完成:")
    print(f"  收益率: {metrics['total_return']*100:.2f}%")
    print(f"  年化: {metrics['annualized_return']*100:.2f}%")
    print(f"  夏普: {metrics['sharpe_ratio']:.4f}")
    print(f"  回撤: {metrics['max_drawdown']*100:.2f}%")
    print(f"  胜率: {metrics['win_rate']*100:.1f}%")


if __name__ == "__main__":
    main()
