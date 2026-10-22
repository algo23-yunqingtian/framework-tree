#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
read_only_skill_v3_backtest_report_r02 - metric_mapper.py
指标自动映射规则 (Skill模块)
"""

# 因子评级映射
RATING_MAP = {
    "A": "A_OBS", "B": "B_OBS", "C": "C_REJECT",
    "BASE_FROZEN": "BASE_FROZEN",
}

# 评级阈值
IC_THRESHOLDS = {"A_1D": 0.03, "A_3D": 0.02, "A_5D": 0.01}

# 评级规则
RATING_RULES = {
    "BASE_FROZEN": "V3主策略基线8因子, 永久冻结",
    "A_OBS": "|IC_1d|>=0.03 AND |IC_3d|>=0.02 AND |IC_5d|>=0.01 (稳定提前预警)",
    "B_OBS": "|IC_1d|>=0.03 但3d/5d衰减 (仅阶段性有效)",
    "C_REJECT": "|IC_1d|<0.03 (无预测能力, 直接剔除)",
}

def map_rating(ic_1d, ic_3d, ic_5d):
    """根据IC值映射评级"""
    if abs(ic_1d) >= IC_THRESHOLDS["A_1D"] and abs(ic_3d) >= IC_THRESHOLDS["A_3D"] and abs(ic_5d) >= IC_THRESHOLDS["A_5D"]:
        return "A"
    if abs(ic_1d) >= IC_THRESHOLDS["A_1D"]:
        return "B"
    return "C"

def map_label(rating):
    """将评级映射为台账标签"""
    return RATING_MAP.get(rating, "C_REJECT")
