#!/usr/bin/env python3
"""check_html.py — framework-tree 静态页自动验证（P2，v1.0 2026-08-28）。

职责：build 后自动校验 4 个铅 6.x 子页，输出 PASS/FAIL 表格。消灭手工 curl+grep 的低级错误。

校验维度（每页 6 项）：
  1. 文件存在
  2. 字节数在允许区间（防止空文件/截断/异常膨胀）
  3. 图表容器数正确（chart 块数 = 图数）
  4. chart-note 图备注数正确（= 图数，每图一处）
  5. 全部图表 id 已初始化（__inst_<cid>）
  6. 公共 JS 关键函数存在（__seasonalize / __tgl / resize 监听）

用法：
  python3 check_html.py                 # 校验本地文件
  python3 check_html.py --build         # 先重新 build 4 页再校验
  python3 check_html.py --online <url>  # 从线上 URL 拉取后校验（需 --max-time）

退出码：0=全 PASS，1=有 FAIL。
"""
import os, sys, re, subprocess, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)

# 5 页的期望配置：文件名 / 最小字节 / 图数 / 图表 id 列表
PAGES = {
    "21": {
        "file": "pb_21_price_structure.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_21_c1", "echart_21_c2", "echart_21_c3"],
        "label": "2.1 盘面结构",
        "has_seasonal": True,
    },

    "22": {
        "file": "pb_22_spot_premium.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_22_c1", "echart_22_c2", "echart_22_c3"],
        "label": "2.2 现货与升贴水",
        "has_seasonal": True,
    },

    "23": {
        "file": "pb_23_overseas_price.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_23_c1", "echart_23_c2", "echart_23_c3"],
        "label": "2.3 海外价格",
        "has_seasonal": True,
    },

    "24": {
        "file": "pb_24_spread_system.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_24_c1", "echart_24_c2", "echart_24_c3"],
        "label": "2.4 价差体系",
        "has_seasonal": False,
    },

    "25": {
        "file": "pb_25_valuation_profit.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_25_c1", "echart_25_c2", "echart_25_c3"],
        "label": "2.5 估值与利润",
        "has_seasonal": False,
    },

    "26": {
        "file": "pb_26_position_holder.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_26_c1", "echart_26_c2", "echart_26_c3"],
        "label": "2.6 持仓席位观察",
        "has_seasonal": True,
    },

    "51": {
        "file": "pb_51_primary_consumption.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_51_c1", "echart_51_c2", "echart_51_c3"],
        "label": "5.1 初级消费",
        "has_seasonal": True,
    },

    "52": {
        "file": "pb_52_terminal_consumption.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_52_c1", "echart_52_c2", "echart_52_c3"],
        "label": "5.2 终端细分消费",
        "has_seasonal": True,
    },

    "61": {
        "file": "pb_61_raw_material_import.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_61_c1", "echart_61_c2", "echart_61_c3"],
        "label": "6.1 原料进口",
        "has_seasonal": True,   # 有 chart_line_t 图，需校验季节真数据
    },

    "62": {
        "file": "pb_62_import_export.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_62_c1", "echart_62_c2", "echart_62_c3"],
        "label": "6.2 精炼金属进出口",
        "has_seasonal": True,
    },

    "63": {
        "file": "pb_63_product_export.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_63_c1", "echart_63_c2", "echart_63_c3"],
        "label": "6.3 制品出口",
        "has_seasonal": True,
    },

    "64": {
        "file": "pb_64_overseas_shipping.html",
        "min_bytes": 300000,
        "charts": 3,
        "cids": ["echart_64_c1", "echart_64_c2", "echart_64_c3"],
        "label": "6.4 海外对华发运",
        "has_seasonal": False,  # 3 图全为 dual/triple，无季节切换模式
    },

    "32_3": {
        "file": "pb_32_3_regen_supply.html",
        "min_bytes": 30000,
        "charts": 4,
        "cids": ["echart_32_3_c1", "echart_32_3_c2", "echart_32_3_c3", "echart_32_3_c4"],
        "label": "3.2.3 再生/二次供应",
        "has_seasonal": True,   # 图4 chart_line_t 季节真数据
    },

    "41": {
        "file": "pb_41_exchange_stock.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_41_c1", "echart_41_c2", "echart_41_c3"],
        "label": "4.1 交易所库存",
        "has_seasonal": True,   # 图1 chart_line_t 注销占比季节
    },

    "42": {
        "file": "pb_42_warrant.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_42_c1", "echart_42_c2", "echart_42_c3"],
        "label": "4.2 仓单",
        "has_seasonal": True,   # 图1/图2 chart_line_t
    },

    "43": {
        "file": "pb_43_social_stock.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_43_c1", "echart_43_c2", "echart_43_c3"],
        "label": "4.3 社会库存",
        "has_seasonal": True,   # 图3 Mysteel全国 chart_line_t
    },

    "44": {
        "file": "pb_44_factory_stock.html",
        "min_bytes": 30000,
        "charts": 3,
        "cids": ["echart_44_c1", "echart_44_c2", "echart_44_c3"],
        "label": "4.4 工厂库存",
        "has_seasonal": False,  # 3 图全为 dual，无季节切换模式
    },

    "45": {
        "file": "pb_45_hidden_stock.html",
        "min_bytes": 20000,
        "charts": 2,
        "cids": ["echart_45_c1", "echart_45_c2"],
        "label": "4.5 隐性·在途",
        "has_seasonal": True,   # 图1 SG非仓单 chart_line_t
    },

    "71": {
        "file": "pb_71_cost_curve.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_71_c1", "echart_71_c2", "echart_71_c3"],
        "label": "7.1 成本曲线与分位",
        "has_seasonal": True,   # 图2 chart_line_t 季节真数据
    },

    "72": {
        "file": "pb_72_daily_profit.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_72_c1", "echart_72_c2", "echart_72_c3"],
        "label": "7.2 日度利润测算",
        "has_seasonal": True,   # 图2 chart_line_t 季节真数据
    },

    "73": {
        "file": "pb_73_energy_cost.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_73_c1", "echart_73_c2", "echart_73_c3"],
        "label": "7.3 能源/原料成本",
        "has_seasonal": True,   # 图2 chart_line_t 季节真数据
    },

    "cu_2_1": {
        "file": "cu_2_1.html",
        "min_bytes": 20000,
        "charts": 4,
        "cids": ["echart_cu_21_c1", "echart_cu_21_c2", "echart_cu_21_c3", "echart_cu_21_c4"],
        "label": "CU 2.1 进口盈亏与贸易流",
        "has_seasonal": True,   # 图1 进口盈亏 chart_line_t 季节真数据
    },

    "cu_2_2": {
        "file": "cu_2_2.html",
        "min_bytes": 16000,
        "charts": 2,
        "cids": ["echart_cu_22_c1", "echart_cu_22_c2"],
        "label": "现货与升贴水 2.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_2_3": {
        "file": "cu_2_3.html",
        "min_bytes": 259000,
        "charts": 3,
        "cids": ["echart_cu_23_c1", "echart_cu_23_c2", "echart_cu_23_c3"],
        "label": "海外价格 2.3",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_2_4": {
        "file": "cu_2_4.html",
        "min_bytes": 421000,
        "charts": 4,
        "cids": ["echart_cu_24_c1", "echart_cu_24_c2", "echart_cu_24_c3", "echart_cu_24_c4"],
        "label": "价差体系 2.4",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_2_5": {
        "file": "cu_2_5.html",
        "min_bytes": 62000,
        "charts": 2,
        "cids": ["echart_cu_25_c1", "echart_cu_25_c2"],
        "label": "估值与利润 2.5",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_2_6": {
        "file": "cu_2_6.html",
        "min_bytes": 14000,
        "charts": 2,
        "cids": ["echart_cu_26_c1", "echart_cu_26_c2"],
        "label": "持仓席位观察 2.6",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_2_1": {
        "file": "al_2_1.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_21_c1", "echart_al_21_c2"],
        "label": "CU→AL 2.1 盘面结构",
        "has_seasonal": True,   # 主图沪铝持仓量 chart_line_t 季节真数据
    },

    "al_2_2": {
        "file": "al_2_2.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_22_c1", "echart_al_22_c2"],
        "label": "AL 2.2 现货与升贴水",
        "has_seasonal": True,   # 主图现货升贴水 chart_line_t
    },

    "al_2_3": {
        "file": "al_2_3.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_al_23_c1", "echart_al_23_c2", "echart_al_23_c3"],
        "label": "AL 2.3 海外价格",
        "has_seasonal": True,   # 主图 LME 3M 结算价 chart_line_t
    },

    "al_2_4": {
        "file": "al_2_4.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_24_c1", "echart_al_24_c2"],
        "label": "AL 2.4 价差体系",
        "has_seasonal": True,   # 主图沪铝月差(自算) chart_line_t
    },

    "al_2_5": {
        "file": "al_2_5.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_25_c1", "echart_al_25_c2"],
        "label": "AL 2.5 估值与利润",
        "has_seasonal": True,   # 主图沪铝估值分位(自算) chart_line_t
    },

    "al_2_6": {
        "file": "al_2_6.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_al_26_c1", "echart_al_26_c2", "echart_al_26_c3"],
        "label": "AL 2.6 持仓席位观察",
        "has_seasonal": False,  # 主图为周/日混合序列，季节视图不适用
    },

    "cu_3_1_1": {
        "file": "cu_3_1_1.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_cu_311_c1", "echart_cu_311_c2"],
        "label": "铜矿产量·澳 3.1.1",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_3_1_2": {
        "file": "cu_3_1_2.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_cu_312_c1"],
        "label": "铜矿产量·波兰 3.1.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_3_1_3": {
        "file": "cu_3_1_3.html",
        "min_bytes": 13000,
        "charts": 2,
        "cids": ["echart_cu_313_c1", "echart_cu_313_c2"],
        "label": "铜矿产量·中国 3.1.3",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_3_1_4": {
        "file": "cu_3_1_4.html",
        "min_bytes": 10000,
        "charts": 1,
        "cids": ["echart_cu_314_c1"],
        "label": "铜精矿进口 3.1.4",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_3_1_5": {
        "file": "cu_3_1_5.html",
        "min_bytes": 107000,
        "charts": 3,
        "cids": ["echart_cu_315_c1", "echart_cu_315_c2", "echart_cu_315_c3"],
        "label": "TC/RC加工费 3.1.5",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_3_2_1": {
        "file": "cu_3_2_1.html",
        "min_bytes": 29000,
        "charts": 3,
        "cids": ["echart_cu_321_c1", "echart_cu_321_c2", "echart_cu_321_c3"],
        "label": "电解铜产能产量 3.2.1",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_3_2_2": {
        "file": "cu_3_2_2.html",
        "min_bytes": 20000,
        "charts": 2,
        "cids": ["echart_cu_322_c1", "echart_cu_322_c2"],
        "label": "电解铜产量 3.2.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_3_2_3": {
        "file": "al_3_2_3.html",
        "min_bytes": 17000,
        "charts": 2,
        "cids": ["echart_al_323_c1", "echart_al_323_c2"],
        "label": "再生铜供应 3.2.3",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_3_2_4": {
        "file": "cu_3_2_4.html",
        "min_bytes": 21000,
        "charts": 2,
        "cids": ["echart_cu_324_c1", "echart_cu_324_c2"],
        "label": "冶炼利润 3.2.4",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_4_1": {
        "file": "al_4_1.html",
        "min_bytes": 528000,
        "charts": 3,
        "cids": ["echart_al_41_c1", "echart_al_41_c2", "echart_al_41_c3"],
        "label": "交易所库存 4.1",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_4_2": {
        "file": "al_4_2.html",
        "min_bytes": 298000,
        "charts": 3,
        "cids": ["echart_al_42_c1", "echart_al_42_c2", "echart_al_42_c3"],
        "label": "仓单 4.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_4_3": {
        "file": "al_4_3.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_43_c1"],
        "label": "社会库存 4.3",
        "has_seasonal": False,   # 主图年跨度>=3年才有季节视图
    },

    "al_4_4": {
        "file": "al_4_4.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_44_c1"],
        "label": "工厂库存 4.4",
        "has_seasonal": False,   # 主图年跨度>=3年才有季节视图
    },

    "al_4_5": {
        "file": "al_4_5.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_45_c1"],
        "label": "隐性·在途 4.5",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_5_1": {
        "file": "al_5_1.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_51_c1", "echart_al_51_c2"],
        "label": "初级消费 5.1",
        "has_seasonal": True,   # 主图 al_51_util 月频 11 完整年，有真实历年 series
    },

    "al_5_2": {
        "file": "al_5_2.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_52_c1", "echart_al_52_c2"],
        "label": "终端消费 5.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_5_3": {
        "file": "al_5_3.html",
        "min_bytes": 10000,
        "charts": 1,
        "cids": ["echart_al_53_c1"],
        "label": "消费价格 5.3",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_6_1": {
        "file": "cu_6_1.html",
        "min_bytes": 14000,
        "charts": 2,
        "cids": ["echart_cu_61_c1", "echart_cu_61_c2"],
        "label": "原料进口 6.1",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_6_2": {
        "file": "cu_6_2.html",
        "min_bytes": 15000,
        "charts": 2,
        "cids": ["echart_cu_62_c1", "echart_cu_62_c2"],
        "label": "进出口 6.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "cu_63": {
        "file": "cu_6_3.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_cu_63_c1", "echart_cu_63_c2", "echart_cu_63_c3"],
        "label": "制品出口 6.3",
        "has_seasonal": True,
    },

    "cu_64": {
        "file": "cu_6_4.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_cu_64_c1", "echart_cu_64_c2", "echart_cu_64_c3"],
        "label": "海外发运 6.4",
        "has_seasonal": True,
    },

    "al_6_3": {
        "file": "al_6_3.html",
        "min_bytes": 10000,
        "charts": 1,
        "cids": ["echart_al_63_c1"],
        "label": "制品出口 6.3",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_7_1": {
        "file": "al_7_1.html",
        "min_bytes": 103000,
        "charts": 2,
        "cids": ["echart_al_71_c1", "echart_al_71_c2"],
        "label": "电解铝成本 7.1",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_7_2": {
        "file": "al_7_2.html",
        "min_bytes": 15000,
        "charts": 2,
        "cids": ["echart_al_72_c1", "echart_al_72_c2"],
        "label": "铝价与成本 7.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_312": {
        "file": "al_3_1_2.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_al_312_c1", "echart_al_312_c2", "echart_al_312_c3"],
        "label": "海外矿分国别 3.1.2",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_314": {
        "file": "al_3_1_4.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_al_314_c1", "echart_al_314_c2", "echart_al_314_c3"],
        "label": "矿进口分国别 3.1.4",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_61": {
        "file": "al_6_1.html",
        "min_bytes": 20000,
        "charts": 2,
        "cids": ["echart_al_61_c1", "echart_al_61_c2"],
        "label": "原料进口 6.1",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_64": {
        "file": "al_6_4.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_al_64_c1", "echart_al_64_c2", "echart_al_64_c3"],
        "label": "海外发运 6.4",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_73": {
        "file": "al_7_3.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_al_73_c1", "echart_al_73_c2", "echart_al_73_c3"],
        "label": "能源/原料成本 7.3",
        "has_seasonal": True,   # 主图年跨度>=3年才有季节视图
    },

    "al_313": {
        "file": "al_3_1_3.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_313_c1"],
        "label": "国内矿·开工率 3.1.3",
        "has_seasonal": True,
    },

    "al_315": {
        "file": "al_3_1_5.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_315_c1", "echart_al_315_c2"],
        "label": "加工费 3.1.5",
        "has_seasonal": True,
    },

    "al_321": {
        "file": "al_3_2_1.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_321_c1"],
        "label": "产能与开工 3.2.1",
        "has_seasonal": True,
    },

    "al_322": {
        "file": "al_3_2_2.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_322_c1"],
        "label": "开工率 3.2.2",
        "has_seasonal": True,
    },

    "al_324": {
        "file": "al_3_2_4.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_324_c1"],
        "label": "成本与利润 3.2.4",
        "has_seasonal": True,
    },

    "al_62": {
        "file": "al_6_2.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_al_62_c1"],
        "label": "原料进口·港口库存 6.2",
        "has_seasonal": True,
    },

    "cu_323": {
        "file": "cu_3_2_3.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_cu_323_c1"],
        "label": "再生铜供应 3.2.3",
        "has_seasonal": True,
    },

    "cu_41": {
        "file": "cu_4_1.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_cu_41_c1", "echart_cu_41_c2", "echart_cu_41_c3"],
        "label": "交易所库存 4.1",
        "has_seasonal": True,
    },

    "cu_42": {
        "file": "cu_4_2.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_cu_42_c1", "echart_cu_42_c2"],
        "label": "仓单 4.2",
        "has_seasonal": True,
    },

    "cu_43": {
        "file": "cu_4_3.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_cu_43_c1", "echart_cu_43_c2"],
        "label": "社会库存 4.3",
        "has_seasonal": True,
    },

    "cu_51": {
        "file": "cu_5_1.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_cu_51_c1", "echart_cu_51_c2"],
        "label": "初级消费 5.1",
        "has_seasonal": True,
    },

    "cu_52": {
        "file": "cu_5_2.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_cu_52_c1", "echart_cu_52_c2", "echart_cu_52_c3"],
        "label": "终端消费 5.2",
        "has_seasonal": True,
    },

    "cu_53": {
        "file": "cu_5_3.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_cu_53_c1", "echart_cu_53_c2", "echart_cu_53_c3"],
        "label": "需求先行 5.3",
        "has_seasonal": True,
    },

    "cu_44": {
        "file": "cu_4_4.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_cu_44_c1"],
        "label": "工厂库存 4.4",
        "has_seasonal": False,
    },

    "cu_45": {
        "file": "cu_4_5.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_cu_45_c1", "echart_cu_45_c2"],
        "label": "隐性在途库存 4.5",
        "has_seasonal": False,
    },

    "cu_71": {
        "file": "cu_7_1.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_cu_71_c1"],
        "label": "成本曲线 7.1",
        "has_seasonal": False,
    },

    "cu_72": {
        "file": "cu_7_2.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_cu_72_c1", "echart_cu_72_c2"],
        "label": "日度利润 7.2",
        "has_seasonal": False,
    },

    "cu_73": {
        "file": "cu_7_3.html",
        "min_bytes": 8000,
        "charts": 1,
        "cids": ["echart_cu_73_c1"],
        "label": "能源原料成本 7.3",
        "has_seasonal": False,
    },

    "al_311": {
        "file": "al_3_1_1.html",
        "min_bytes": 12000,
        "charts": 2,
        "cids": ["echart_al_311_c1", "echart_al_311_c2"],
        "label": "铝土矿产量 3.1.1",
        "has_seasonal": True,
    },

    "311": {
        "file": "pb_311_overseas_mine.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_311_c1", "echart_311_c2", "echart_311_c3"],
        "label": "3.1.1 海外矿·财报产量",
        "has_seasonal": True,
    },

    "312": {
        "file": "pb_312_overseas_by_country.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_312_c1", "echart_312_c2", "echart_312_c3"],
        "label": "3.1.2 海外矿·分国别总量",
        "has_seasonal": True,
    },

    "313": {
        "file": "pb_313_domestic_mine.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_313_c1", "echart_313_c2", "echart_313_c3"],
        "label": "3.1.3 国内矿产量",
        "has_seasonal": True,
    },

    "314": {
        "file": "pb_314_mine_import.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_314_c1", "echart_314_c2", "echart_314_c3"],
        "label": "3.1.4 矿进口量与分国别",
        "has_seasonal": True,
    },

    "315": {
        "file": "pb_315_tc_fee.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_315_c1", "echart_315_c2", "echart_315_c3"],
        "label": "3.1.5 TC加工费",
        "has_seasonal": True,
    },

    "321": {
        "file": "pb_321_refining_output.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_321_c1", "echart_321_c2", "echart_321_c3"],
        "label": "3.2.1 精炼产量",
        "has_seasonal": True,
    },

    "322": {
        "file": "pb_322_operating_rate.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_322_c1", "echart_322_c2", "echart_322_c3"],
        "label": "3.2.2 开工率与检修",
        "has_seasonal": True,
    },

    "324": {
        "file": "pb_324_profit_elasticity.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_324_c1", "echart_324_c2", "echart_324_c3"],
        "label": "3.2.4 冶炼利润→供应弹性",
        "has_seasonal": True,
    },

    "53": {
        "file": "pb_53_demand_leading.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_53_c1", "echart_53_c2", "echart_53_c3"],
        "label": "5.3 需求先行指标",
        "has_seasonal": True,
    },

    # === 五金属 ZN 锌 (2026-08-31) ===
    "zn_21": {"file": "zn_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_21_c1", "echart_zn_21_c2", "echart_zn_21_c3", "echart_zn_21_c4"], "label": "锌2.1盘面结构", "has_seasonal": True},
    "zn_22": {"file": "zn_2_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_22_c1", "echart_zn_22_c2", "echart_zn_22_c3", "echart_zn_22_c4"], "label": "锌2.2现货升贴水", "has_seasonal": True},
    "zn_23": {"file": "zn_2_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_23_c1", "echart_zn_23_c2", "echart_zn_23_c3", "echart_zn_23_c4"], "label": "锌2.3海外价格", "has_seasonal": True},
    "zn_24": {"file": "zn_2_4.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_zn_24_c1", "echart_zn_24_c2", "echart_zn_24_c3"], "label": "锌2.4价差体系", "has_seasonal": True},
    "zn_25": {"file": "zn_2_5.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_25_c1", "echart_zn_25_c2", "echart_zn_25_c3", "echart_zn_25_c4"], "label": "锌2.5估值利润", "has_seasonal": True},
    "zn_26": {"file": "zn_2_6.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_26_c1", "echart_zn_26_c2", "echart_zn_26_c3", "echart_zn_26_c4"], "label": "锌2.6持仓席位", "has_seasonal": True},
    "zn_311": {"file": "zn_3_1_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_311_c1", "echart_zn_311_c2", "echart_zn_311_c3", "echart_zn_311_c4"], "label": "锌3.1.1矿产量", "has_seasonal": True},
    "zn_312": {"file": "zn_3_1_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_312_c1", "echart_zn_312_c2", "echart_zn_312_c3", "echart_zn_312_c4"], "label": "锌3.1.2矿产量", "has_seasonal": False},
    "zn_313": {"file": "zn_3_1_3.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_313_c1", "echart_zn_313_c2"], "label": "锌3.1.3矿产量", "has_seasonal": True},
    "zn_314": {"file": "zn_3_1_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_314_c1", "echart_zn_314_c2", "echart_zn_314_c3", "echart_zn_314_c4"], "label": "锌3.1.4矿进口", "has_seasonal": True},
    "zn_315": {"file": "zn_3_1_5.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_315_c1", "echart_zn_315_c2", "echart_zn_315_c3", "echart_zn_315_c4"], "label": "锌3.1.5TC加工费", "has_seasonal": True},
    "zn_321": {"file": "zn_3_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_321_c1", "echart_zn_321_c2", "echart_zn_321_c3", "echart_zn_321_c4"], "label": "锌3.2.1冶炼产量", "has_seasonal": True},
    "zn_322": {"file": "zn_3_2_2.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_zn_322_c1", "echart_zn_322_c2", "echart_zn_322_c3"], "label": "锌3.2.2冶炼产量", "has_seasonal": True},
    "zn_323": {"file": "zn_3_2_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_323_c1", "echart_zn_323_c2", "echart_zn_323_c3", "echart_zn_323_c4"], "label": "锌3.2.3再生供应", "has_seasonal": True},
    "zn_324": {"file": "zn_3_2_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_324_c1", "echart_zn_324_c2", "echart_zn_324_c3", "echart_zn_324_c4"], "label": "锌3.2.4冶炼利润", "has_seasonal": True},
    "zn_41": {"file": "zn_4_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_zn_41_c1", "echart_zn_41_c2", "echart_zn_41_c3"], "label": "锌4.1交易所库存", "has_seasonal": True},
    "zn_42": {"file": "zn_4_2.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_42_c1", "echart_zn_42_c2"], "label": "锌4.2仓单", "has_seasonal": True},
    "zn_43": {"file": "zn_4_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_zn_43_c1", "echart_zn_43_c2", "echart_zn_43_c3"], "label": "锌4.3社会库存", "has_seasonal": True},
    "zn_44": {"file": "zn_4_4.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_zn_44_c1", "echart_zn_44_c2", "echart_zn_44_c3"], "label": "锌4.4工厂库存", "has_seasonal": True},
    "zn_45": {"file": "zn_4_5.html", "min_bytes": 8000, "charts": 1, "cids": ["echart_zn_45_c1"], "label": "锌4.5隐性在途", "has_seasonal": True},
    "zn_51": {"file": "zn_5_1.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_51_c1", "echart_zn_51_c2"], "label": "锌5.1初级消费", "has_seasonal": True},
    "zn_52": {"file": "zn_5_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_52_c1", "echart_zn_52_c2", "echart_zn_52_c3", "echart_zn_52_c4"], "label": "锌5.2终端消费", "has_seasonal": True},
    "zn_53": {"file": "zn_5_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_zn_53_c1", "echart_zn_53_c2", "echart_zn_53_c3", "echart_zn_53_c4"], "label": "锌5.3消费先行", "has_seasonal": True},
    "zn_61": {"file": "zn_6_1.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_61_c1", "echart_zn_61_c2"], "label": "锌6.1原料进口", "has_seasonal": True},
    "zn_62": {"file": "zn_6_2.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_62_c1", "echart_zn_62_c2"], "label": "锌6.2进出口", "has_seasonal": False},
    "zn_63": {"file": "zn_6_3.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_63_c1", "echart_zn_63_c2"], "label": "锌6.3制品出口", "has_seasonal": True},
    "zn_64": {"file": "zn_6_4.html", "min_bytes": 8000, "charts": 1, "cids": ["echart_zn_64_c1"], "label": "锌6.4", "has_seasonal": False},
    "zn_71": {"file": "zn_7_1.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_71_c1", "echart_zn_71_c2"], "label": "锌7.1成本曲线", "has_seasonal": True},
    "zn_72": {"file": "zn_7_2.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_zn_72_c1", "echart_zn_72_c2"], "label": "锌7.2利润", "has_seasonal": True},

    "ni_21": {"file": "ni_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_21_c1", "echart_ni_21_c2", "echart_ni_21_c3", "echart_ni_21_c4"], "label": "镍2.1盘面结构", "has_seasonal": True},
    "ni_22": {"file": "ni_2_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_22_c1", "echart_ni_22_c2", "echart_ni_22_c3", "echart_ni_22_c4"], "label": "镍2.2现货升贴水", "has_seasonal": True},
    "ni_23": {"file": "ni_2_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_ni_23_c1", "echart_ni_23_c2", "echart_ni_23_c3"], "label": "镍2.3海外价格", "has_seasonal": True},
    "ni_24": {"file": "ni_2_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_24_c1", "echart_ni_24_c2", "echart_ni_24_c3", "echart_ni_24_c4"], "label": "镍2.4价差体系", "has_seasonal": False},
    "ni_25": {"file": "ni_2_5.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_25_c1", "echart_ni_25_c2", "echart_ni_25_c3", "echart_ni_25_c4"], "label": "镍2.5估值利润", "has_seasonal": True},
    "ni_26": {"file": "ni_2_6.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_ni_26_c1", "echart_ni_26_c2"], "label": "镍2.6持仓席位", "has_seasonal": True},
    "ni_311": {"file": "ni_3_1_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_311_c1", "echart_ni_311_c2", "echart_ni_311_c3", "echart_ni_311_c4"], "label": "镍3.1.1矿产量", "has_seasonal": False},
    "ni_312": {"file": "ni_3_1_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_312_c1", "echart_ni_312_c2", "echart_ni_312_c3", "echart_ni_312_c4"], "label": "镍3.1.2矿产量", "has_seasonal": False},
    "ni_313": {"file": "ni_3_1_3.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_ni_313_c1", "echart_ni_313_c2"], "label": "镍3.1.3矿产量", "has_seasonal": True},
    "ni_314": {"file": "ni_3_1_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_314_c1", "echart_ni_314_c2", "echart_ni_314_c3", "echart_ni_314_c4"], "label": "镍3.1.4矿进口", "has_seasonal": True},
    "ni_315": {"file": "ni_3_1_5.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_ni_315_c1", "echart_ni_315_c2"], "label": "镍3.1.5TC加工费", "has_seasonal": True},
    "ni_321": {"file": "ni_3_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_321_c1", "echart_ni_321_c2", "echart_ni_321_c3", "echart_ni_321_c4"], "label": "镍3.2.1冶炼产量", "has_seasonal": True},
    "ni_322": {"file": "ni_3_2_2.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_ni_322_c1", "echart_ni_322_c2", "echart_ni_322_c3"], "label": "镍3.2.2冶炼产量", "has_seasonal": True},
    "ni_323": {"file": "ni_3_2_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_ni_323_c1", "echart_ni_323_c2", "echart_ni_323_c3"], "label": "镍3.2.3再生供应", "has_seasonal": True},
    "ni_324": {"file": "ni_3_2_4.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_ni_324_c1", "echart_ni_324_c2"], "label": "镍3.2.4冶炼利润", "has_seasonal": True},
    "ni_41": {"file": "ni_4_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_ni_41_c1", "echart_ni_41_c2", "echart_ni_41_c3"], "label": "镍4.1交易所库存", "has_seasonal": True},
    "ni_42": {"file": "ni_4_2.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_ni_42_c1", "echart_ni_42_c2", "echart_ni_42_c3"], "label": "镍4.2仓单", "has_seasonal": True},
    "ni_43": {"file": "ni_4_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_43_c1", "echart_ni_43_c2", "echart_ni_43_c3", "echart_ni_43_c4"], "label": "镍4.3社会库存", "has_seasonal": True},
    "ni_44": {"file": "ni_4_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_44_c1", "echart_ni_44_c2", "echart_ni_44_c3", "echart_ni_44_c4"], "label": "镍4.4工厂库存", "has_seasonal": True},
    "ni_45": {"file": "ni_4_5.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_45_c1", "echart_ni_45_c2", "echart_ni_45_c3", "echart_ni_45_c4"], "label": "镍4.5隐性在途", "has_seasonal": True},
    "ni_51": {"file": "ni_5_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_51_c1", "echart_ni_51_c2", "echart_ni_51_c3", "echart_ni_51_c4"], "label": "镍5.1初级消费", "has_seasonal": True},
    "ni_52": {"file": "ni_5_2.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_ni_52_c1", "echart_ni_52_c2"], "label": "镍5.2终端消费", "has_seasonal": True},
    "ni_53": {"file": "ni_5_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_ni_53_c1", "echart_ni_53_c2", "echart_ni_53_c3"], "label": "镍5.3消费先行", "has_seasonal": True},
    "ni_61": {"file": "ni_6_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_61_c1", "echart_ni_61_c2", "echart_ni_61_c3", "echart_ni_61_c4"], "label": "镍6.1原料进口", "has_seasonal": True},
    "ni_62": {"file": "ni_6_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_62_c1", "echart_ni_62_c2", "echart_ni_62_c3", "echart_ni_62_c4"], "label": "镍6.2进出口", "has_seasonal": True},
    "ni_63": {"file": "ni_6_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_ni_63_c1", "echart_ni_63_c2", "echart_ni_63_c3"], "label": "镍6.3制品出口", "has_seasonal": True},
    "ni_64": {"file": "ni_6_4.html", "min_bytes": 8000, "charts": 1, "cids": ["echart_ni_64_c1"], "label": "镍6.4", "has_seasonal": True},
    "ni_71": {"file": "ni_7_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_71_c1", "echart_ni_71_c2", "echart_ni_71_c3", "echart_ni_71_c4"], "label": "镍7.1成本曲线", "has_seasonal": True},
    "ni_72": {"file": "ni_7_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_72_c1", "echart_ni_72_c2", "echart_ni_72_c3", "echart_ni_72_c4"], "label": "镍7.2利润", "has_seasonal": True},
    "ni_73": {"file": "ni_7_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_ni_73_c1", "echart_ni_73_c2", "echart_ni_73_c3", "echart_ni_73_c4"], "label": "镍7.3原料成本", "has_seasonal": True},
    "sn_21": {"file": "sn_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_21_c1", "echart_sn_21_c2", "echart_sn_21_c3", "echart_sn_21_c4"], "label": "锡2.1盘面结构", "has_seasonal": True},
    "sn_22": {"file": "sn_2_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_22_c1", "echart_sn_22_c2", "echart_sn_22_c3", "echart_sn_22_c4"], "label": "锡2.2现货升贴水", "has_seasonal": True},
    "sn_23": {"file": "sn_2_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_sn_23_c1", "echart_sn_23_c2", "echart_sn_23_c3"], "label": "锡2.3海外价格", "has_seasonal": True},
    "sn_24": {"file": "sn_2_4.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_sn_24_c1", "echart_sn_24_c2"], "label": "锡2.4价差体系", "has_seasonal": True},
    "sn_25": {"file": "sn_2_5.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_sn_25_c1", "echart_sn_25_c2", "echart_sn_25_c3"], "label": "锡2.5估值利润", "has_seasonal": True},
    "sn_26": {"file": "sn_2_6.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_26_c1", "echart_sn_26_c2", "echart_sn_26_c3", "echart_sn_26_c4"], "label": "锡2.6持仓席位", "has_seasonal": True},
    "sn_311": {"file": "sn_3_1_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_sn_311_c1", "echart_sn_311_c2", "echart_sn_311_c3"], "label": "锡3.1.1矿产量", "has_seasonal": False},
    "sn_312": {"file": "sn_3_1_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_312_c1", "echart_sn_312_c2", "echart_sn_312_c3", "echart_sn_312_c4"], "label": "锡3.1.2矿产量", "has_seasonal": True},
    "sn_313": {"file": "sn_3_1_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_313_c1", "echart_sn_313_c2", "echart_sn_313_c3", "echart_sn_313_c4"], "label": "锡3.1.3矿产量", "has_seasonal": False},
    "sn_314": {"file": "sn_3_1_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_314_c1", "echart_sn_314_c2", "echart_sn_314_c3", "echart_sn_314_c4"], "label": "锡3.1.4矿进口", "has_seasonal": True},
    "sn_315": {"file": "sn_3_1_5.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_sn_315_c1", "echart_sn_315_c2"], "label": "锡3.1.5TC加工费", "has_seasonal": True},
    "sn_321": {"file": "sn_3_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_321_c1", "echart_sn_321_c2", "echart_sn_321_c3", "echart_sn_321_c4"], "label": "锡3.2.1冶炼产量", "has_seasonal": False},
    "sn_322": {"file": "sn_3_2_2.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_sn_322_c1", "echart_sn_322_c2"], "label": "锡3.2.2冶炼产量", "has_seasonal": True},
    "sn_323": {"file": "sn_3_2_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_323_c1", "echart_sn_323_c2", "echart_sn_323_c3", "echart_sn_323_c4"], "label": "锡3.2.3再生供应", "has_seasonal": False},
    "sn_41": {"file": "sn_4_1.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_sn_41_c1", "echart_sn_41_c2"], "label": "锡4.1交易所库存", "has_seasonal": True},
    "sn_42": {"file": "sn_4_2.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_sn_42_c1", "echart_sn_42_c2", "echart_sn_42_c3"], "label": "锡4.2仓单", "has_seasonal": True},
    "sn_43": {"file": "sn_4_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_sn_43_c1", "echart_sn_43_c2", "echart_sn_43_c3"], "label": "锡4.3社会库存", "has_seasonal": True},
    "sn_44": {"file": "sn_4_4.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_sn_44_c1", "echart_sn_44_c2"], "label": "锡4.4工厂库存", "has_seasonal": True},
    "sn_45": {"file": "sn_4_5.html", "min_bytes": 8000, "charts": 1, "cids": ["echart_sn_45_c1"], "label": "锡4.5隐性在途", "has_seasonal": True},
    "sn_51": {"file": "sn_5_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_sn_51_c1", "echart_sn_51_c2", "echart_sn_51_c3"], "label": "锡5.1初级消费", "has_seasonal": True},
    "sn_52": {"file": "sn_5_2.html", "min_bytes": 25000, "charts": 4, "cids": ["echart_sn_52_c1", "echart_sn_52_c2", "echart_sn_52_c3", "echart_sn_52_c4"], "label": "锡5.2终端消费", "has_seasonal": True},
    "sn_53": {"file": "sn_5_3.html", "min_bytes": 8000, "charts": 1, "cids": ["echart_sn_53_c1"], "label": "锡5.3消费先行", "has_seasonal": True},
    "sn_61": {"file": "sn_6_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_61_c1", "echart_sn_61_c2", "echart_sn_61_c3", "echart_sn_61_c4"], "label": "锡6.1原料进口", "has_seasonal": False},
    "sn_62": {"file": "sn_6_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_62_c1", "echart_sn_62_c2", "echart_sn_62_c3", "echart_sn_62_c4"], "label": "锡6.2进出口", "has_seasonal": True},
    "sn_63": {"file": "sn_6_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_63_c1", "echart_sn_63_c2", "echart_sn_63_c3", "echart_sn_63_c4"], "label": "锡6.3制品出口", "has_seasonal": True},
    "sn_64": {"file": "sn_6_4.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_sn_64_c1", "echart_sn_64_c2"], "label": "锡6.4", "has_seasonal": True},
    "sn_71": {"file": "sn_7_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_71_c1", "echart_sn_71_c2", "echart_sn_71_c3", "echart_sn_71_c4"], "label": "锡7.1成本曲线", "has_seasonal": True},
    "sn_72": {"file": "sn_7_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_72_c1", "echart_sn_72_c2", "echart_sn_72_c3", "echart_sn_72_c4"], "label": "锡7.2利润", "has_seasonal": True},
    "sn_73": {"file": "sn_7_3.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_sn_73_c1", "echart_sn_73_c2", "echart_sn_73_c3", "echart_sn_73_c4"], "label": "锡7.3原料成本", "has_seasonal": True},
    "si_21": {"file": "si_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_21_c1", "echart_si_21_c2", "echart_si_21_c3", "echart_si_21_c4"], "label": "硅2.1盘面结构", "has_seasonal": True},
    "si_22": {"file": "si_2_2.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_22_c1", "echart_si_22_c2", "echart_si_22_c3"], "label": "硅2.2现货升贴水", "has_seasonal": True},
    "si_23": {"file": "si_2_3.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_si_23_c1", "echart_si_23_c2"], "label": "硅2.3海外价格", "has_seasonal": True},
    "si_24": {"file": "si_2_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_24_c1", "echart_si_24_c2", "echart_si_24_c3", "echart_si_24_c4"], "label": "硅2.4价差体系", "has_seasonal": True},
    "si_25": {"file": "si_2_5.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_25_c1", "echart_si_25_c2", "echart_si_25_c3", "echart_si_25_c4"], "label": "硅2.5估值利润", "has_seasonal": True},
    "si_26": {"file": "si_2_6.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_26_c1", "echart_si_26_c2", "echart_si_26_c3", "echart_si_26_c4"], "label": "硅2.6持仓席位", "has_seasonal": True},
    "si_311": {"file": "si_3_1_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_311_c1", "echart_si_311_c2", "echart_si_311_c3"], "label": "硅3.1.1矿产量", "has_seasonal": True},
    "si_312": {"file": "si_3_1_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_312_c1", "echart_si_312_c2", "echart_si_312_c3", "echart_si_312_c4"], "label": "硅3.1.2矿产量", "has_seasonal": True},
    "si_314": {"file": "si_3_1_4.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_si_314_c1", "echart_si_314_c2"], "label": "硅3.1.4矿进口", "has_seasonal": True},
    "si_315": {"file": "si_3_1_5.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_315_c1", "echart_si_315_c2", "echart_si_315_c3"], "label": "硅3.1.5TC加工费", "has_seasonal": True},
    "si_321": {"file": "si_3_2_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_321_c1", "echart_si_321_c2", "echart_si_321_c3"], "label": "硅3.2.1冶炼产量", "has_seasonal": True},
    "si_322": {"file": "si_3_2_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_322_c1", "echart_si_322_c2", "echart_si_322_c3", "echart_si_322_c4"], "label": "硅3.2.2冶炼产量", "has_seasonal": True},
    "si_323": {"file": "si_3_2_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_323_c1", "echart_si_323_c2", "echart_si_323_c3"], "label": "硅3.2.3再生供应", "has_seasonal": True},
    "si_324": {"file": "si_3_2_4.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_324_c1", "echart_si_324_c2", "echart_si_324_c3", "echart_si_324_c4"], "label": "硅3.2.4冶炼利润", "has_seasonal": True},
    "si_41": {"file": "si_4_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_41_c1", "echart_si_41_c2", "echart_si_41_c3"], "label": "硅4.1交易所库存", "has_seasonal": True},
    "si_42": {"file": "si_4_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_42_c1", "echart_si_42_c2", "echart_si_42_c3", "echart_si_42_c4"], "label": "硅4.2仓单", "has_seasonal": True},
    "si_43": {"file": "si_4_3.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_si_43_c1", "echart_si_43_c2"], "label": "硅4.3社会库存", "has_seasonal": True},
    "si_44": {"file": "si_4_4.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_si_44_c1", "echart_si_44_c2"], "label": "硅4.4工厂库存", "has_seasonal": False},
    "si_45": {"file": "si_4_5.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_si_45_c1", "echart_si_45_c2"], "label": "硅4.5隐性在途", "has_seasonal": False},
    "si_51": {"file": "si_5_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_51_c1", "echart_si_51_c2", "echart_si_51_c3"], "label": "硅5.1初级消费", "has_seasonal": False},
    "si_52": {"file": "si_5_2.html", "min_bytes": 8000, "charts": 1, "cids": ["echart_si_52_c1"], "label": "硅5.2终端消费", "has_seasonal": True},
    "si_61": {"file": "si_6_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_61_c1", "echart_si_61_c2", "echart_si_61_c3", "echart_si_61_c4"], "label": "硅6.1原料进口", "has_seasonal": True},
    "si_62": {"file": "si_6_2.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_62_c1", "echart_si_62_c2", "echart_si_62_c3"], "label": "硅6.2进出口", "has_seasonal": True},
    "si_63": {"file": "si_6_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_63_c1", "echart_si_63_c2", "echart_si_63_c3"], "label": "硅6.3制品出口", "has_seasonal": True},
    "si_64": {"file": "si_6_4.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_si_64_c1", "echart_si_64_c2", "echart_si_64_c3"], "label": "硅6.4", "has_seasonal": True},
    "si_71": {"file": "si_7_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_71_c1", "echart_si_71_c2", "echart_si_71_c3", "echart_si_71_c4"], "label": "硅7.1成本曲线", "has_seasonal": True},
    "si_72": {"file": "si_7_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_si_72_c1", "echart_si_72_c2", "echart_si_72_c3", "echart_si_72_c4"], "label": "硅7.2利润", "has_seasonal": True},
    "li_21": {"file": "li_2_1.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_li_21_c1", "echart_li_21_c2", "echart_li_21_c3", "echart_li_21_c4"], "label": "锂2.1盘面结构", "has_seasonal": False},
    "li_22": {"file": "li_2_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_li_22_c1", "echart_li_22_c2", "echart_li_22_c3", "echart_li_22_c4"], "label": "锂2.2现货升贴水", "has_seasonal": False},
    "li_24": {"file": "li_2_4.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_li_24_c1", "echart_li_24_c2"], "label": "锂2.4价差体系", "has_seasonal": False},
    "li_25": {"file": "li_2_5.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_li_25_c1", "echart_li_25_c2", "echart_li_25_c3"], "label": "锂2.5估值利润", "has_seasonal": False},
    "li_26": {"file": "li_2_6.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_li_26_c1", "echart_li_26_c2", "echart_li_26_c3", "echart_li_26_c4"], "label": "锂2.6持仓席位", "has_seasonal": False},
    "li_311": {"file": "li_3_1_1.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_li_311_c1", "echart_li_311_c2"], "label": "锂3.1.1矿产量", "has_seasonal": True},
    "li_312": {"file": "li_3_1_2.html", "min_bytes": 8000, "charts": 1, "cids": ["echart_li_312_c1"], "label": "锂3.1.2矿产量", "has_seasonal": False},
    "li_313": {"file": "li_3_1_3.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_li_313_c1", "echart_li_313_c2"], "label": "锂3.1.3矿产量", "has_seasonal": False},
    "li_321": {"file": "li_3_2_1.html", "min_bytes": 25000, "charts": 4, "cids": ["echart_li_321_c1", "echart_li_321_c2", "echart_li_321_c3", "echart_li_321_c4"], "label": "锂3.2.1冶炼产量", "has_seasonal": True},
    "li_323": {"file": "li_3_2_3.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_li_323_c1", "echart_li_323_c2", "echart_li_323_c3"], "label": "锂3.2.3再生供应", "has_seasonal": True},
    "li_324": {"file": "li_3_2_4.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_li_324_c1", "echart_li_324_c2", "echart_li_324_c3"], "label": "锂3.2.4冶炼利润", "has_seasonal": False},
    "li_41": {"file": "li_4_1.html", "min_bytes": 20000, "charts": 3, "cids": ["echart_li_41_c1", "echart_li_41_c2", "echart_li_41_c3"], "label": "锂4.1交易所库存", "has_seasonal": False},
    "li_42": {"file": "li_4_2.html", "min_bytes": 30000, "charts": 4, "cids": ["echart_li_42_c1", "echart_li_42_c2", "echart_li_42_c3", "echart_li_42_c4"], "label": "锂4.2仓单", "has_seasonal": False},
    "li_43": {"file": "li_4_3.html", "min_bytes": 12000, "charts": 2, "cids": ["echart_li_43_c1", "echart_li_43_c2"], "label": "锂4.3社会库存", "has_seasonal": False},
    "li_44": {"file": "li_4_4.html", "min_bytes": 20000, "charts": 4, "cids": ["echart_li_44_c1", "echart_li_44_c2", "echart_li_44_c3", "echart_li_44_c4"], "label": "锂4.4工厂库存", "has_seasonal": False},
}
# 公共 JS 必须包含的函数/特征（不含季节真数据调用，那项按页类型单独校验）
COMMON_JS_TOKENS = ["function __seasonalizeByYear", "function __tgl", "addEventListener('resize'"]


def run_builds():
    """重新 build 4 页。"""
    scripts = ["build_pb_21.py", "build_pb_61.py", "build_pb_62_demo.py", "build_pb_63.py", "build_pb_64.py"]
    for s in scripts:
        r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, s)],
                           cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print("[BUILD FAIL] %s\n%s" % (s, r.stderr))
            return False
    return True


def fetch_online(base_url):
    """从线上拉取 4 页 HTML。返回 {key: html}。用 --max-time 90 防大文件超时。"""
    out = {}
    for k, cfg in PAGES.items():
        url = base_url.rstrip("/") + "/" + cfg["file"]
        r = subprocess.run(["curl", "-s", "--max-time", "90", url], capture_output=True, text=True)
        out[k] = r.stdout if r.returncode == 0 else ""
    return out


def check_page(cfg, html, source):
    """校验单页，返回 [(check_name, ok, detail), ...]"""
    res = []
    size = len(html.encode("utf-8"))
    # 1. 文件/内容存在
    res.append(("内容非空", bool(html.strip()), "%s (%s)" % (source, size)))
    # 2. 字节数下限
    res.append(("字节≥%d" % cfg["min_bytes"], size >= cfg["min_bytes"], "%d 字节" % size))
    # 3. 图表容器数
    n_chart = len(re.findall(r'<div class="chart">', html))
    res.append(("chart 容器=%d" % cfg["charts"], n_chart == cfg["charts"], "实际 %d" % n_chart))
    # 4. chart-note 图备注数
    n_note = html.count('class="chart-note"')
    res.append(("chart-note=%d" % cfg["charts"], n_note == cfg["charts"], "实际 %d" % n_note))
    # 5. 图表 id 初始化
    missing = [c for c in cfg["cids"] if ("__inst_%s" % c) not in html]
    res.append(("全部 cid 已 __inst", not missing, "缺 %s" % missing if missing else "3/3 OK"))
    # 6. 公共 JS 关键函数
    miss_js = [t for t in COMMON_JS_TOKENS if t not in html]
    res.append(("公共 JS 完整", not miss_js, "缺 %s" % miss_js if miss_js else "3/3 OK"))
    # 7. 季节真数据（仅含 chart_line_t 的页）
    if cfg.get("has_seasonal"):
        # v1.1+：季节视图用 __seasonalizeByYear(月度/周度) 或 __seasonalizeByDay(日度) 产出历年 series
        ok = (("window.__seasonalizeByYear" in html or "window.__seasonalizeByDay" in html)
              and "__yrs_" in html and "__pal_" in html)
        res.append(("季节真数据 历年series函数", ok,
                    "缺失：可能未用新的历年 series 函数"))
    else:
        res.append(("季节真数据", True, "本页无季节模式，跳过"))
    # 额外：echarts 引用
    res.append(("echarts.min.js 引用", "assets/echarts.min.js" in html, ""))
    # 额外：指标版本（跟随 indicators_v1.json 实际版本，v1.x/v2.x 均通过）
    has_ver = bool(re.search(r"indicators_v1\.json v\d+\.\d+", html))
    res.append(("indicators_v1.json 版本", has_ver, ""))
    return res


def main():
    online = False
    base_url = None
    do_build = False
    for i, a in enumerate(sys.argv[1:]):
        if a == "--build":
            do_build = True
        elif a == "--online":
            online = True
            base_url = sys.argv[i + 2]
        elif a == "--help":
            print(__doc__)
            return 0

    print("=" * 74)
    print("framework-tree 静态页校验 (check_html.py v1.0)")
    print("=" * 74)

    if do_build:
        print("\n[BUILD] 重新 build 4 页 ...")
        if not run_builds():
            print("[ABORT] build 失败")
            return 1
        print("[BUILD] OK\n")

    if online:
        htmls = fetch_online(base_url)
        print("[SOURCE] 线上 %s\n" % base_url)
    else:
        htmls = {}
        for k, cfg in PAGES.items():
            p = os.path.join(ROOT, cfg["file"])
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    htmls[k] = f.read()
            else:
                htmls[k] = ""
        print("[SOURCE] 本地 %s\n" % ROOT)

    all_ok = True
    rows = []
    for k, cfg in PAGES.items():
        html = htmls.get(k, "")
        res = check_page(cfg, html, "local") if not online else check_page(cfg, html, "online")
        ok = all(r[1] for r in res)
        all_ok = all_ok and ok
        rows.append((k, cfg["label"], ok, res))

    # 输出表格
    print("%-4s %-16s %-6s %s" % ("页", "名称", "结果", "明细"))
    print("-" * 74)
    for k, label, ok, res in rows:
        print("%-4s %-16s %-6s" % (k, label, "✅PASS" if ok else "❌FAIL"))
        for name, good, detail in res:
            print("        %s %-22s %s" % ("·" if good else "!", name, detail if not good else ""))
        print()

    print("=" * 74)
    print("总结: %d/%d 页通过  →  %s" % (sum(1 for r in rows if r[2]), len(rows),
                                         "✅ 全部 PASS" if all_ok else "❌ 存在 FAIL"))
    print("=" * 74)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())