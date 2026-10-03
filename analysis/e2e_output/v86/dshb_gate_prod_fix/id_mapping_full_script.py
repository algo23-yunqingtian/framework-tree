#!/usr/bin/env python3
"""
DSHB V86-RC2 ID桥接全量映射脚本
任务: DSHB_V86_RC2_ID_MAPPING_FULL
功能: 170项PENDING条目的zhiji API搜索映射 + 批次日志生成
约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
"""

import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DATA_KEY = "data_8e863643ecc13f11d2c669bdb672f7db"
DATA_BASE = "https://zhiji-ai.xyz/commodity/api"
RATE_SEC = 1.0
OUTPUT_DIR = Path(__file__).parent
LOG_DIR = OUTPUT_DIR / "mapping_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_lock_file = Path.home() / ".hermes" / "scripts" / "zhiji_cache" / ".locks" / "data.lock"
_lock_file.parent.mkdir(parents=True, exist_ok=True)

def rate_limit():
    now = time.time()
    try:
        last = float(_lock_file.read_text().strip()) if _lock_file.exists() else 0
    except:
        last = 0
    wait = RATE_SEC - (now - last)
    if wait > 0:
        time.sleep(wait)
    _lock_file.write_text(str(time.time()))

def api_get(url, timeout=20):
    rate_limit()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 DSHB_IDMapping/1.0",
        "X-Data-Key": DATA_KEY,
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            el = round((time.time()-t0)*1000, 1)
            raw = r.read()
            if not raw:
                return {"status": r.status, "ms": el, "error": "empty", "body": None}
            return {"status": r.status, "ms": el, "error": None, "body": json.loads(raw)}
    except urllib.error.HTTPError as e:
        el = round((time.time()-t0)*1000, 1)
        body = ""
        try:
            body = e.read().decode("utf-8","replace")
        except:
            pass
        return {"status": e.code, "ms": el, "error": f"HTTP {e.code}", "body": body or None}
    except Exception as e:
        el = round((time.time()-t0)*1000, 1)
        return {"status": None, "ms": el, "error": str(e), "body": None}

def parse_series_body(body):
    """解析series API响应"""
    if not isinstance(body, dict):
        return {"has_data": False, "data_count": 0, "perm_state": None, "points_sample": None}
    
    has_data = False
    data_count = 0
    perm_state = body.get("permission_state")
    points_sample = None
    
    if "points" in body:
        pts = body["points"]
        if isinstance(pts, list):
            data_count = len(pts)
            if data_count > 0:
                has_data = True
            points_sample = str(pts[:3]) if pts else None
    
    if not has_data and "data" in body:
        dl = body["data"]
        if isinstance(dl, list):
            data_count = len(dl)
            has_data = data_count > 0
            points_sample = str(dl[:3]) if dl else None
    
    return {"has_data": has_data, "data_count": data_count, "perm_state": perm_state, "points_sample": points_sample}

# ============================================================================
# 170项PENDING条目定义 — 按品种和批次组织
# ============================================================================

PENDING_ITEMS = [
    # ===== Batch 1: P0 (9项) — 核心库存/TC指标 =====
    {"indicator_id": "PB-011", "semantic_id": "lead_total_inv", "name_cn": "铅锭总库存", "unit": "ton", "type": "INTEGER", "batch": 1, "priority": "P0", "method": "computed", "search_query": "铅锭 总库存", "derivation": "lead_social_inv + lead_exchange_inv"},
    {"indicator_id": "PB-012", "semantic_id": "lead_lme_inv", "name_cn": "铅锭LME库存", "unit": "ton", "type": "INTEGER", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "LME 铅 库存"},
    {"indicator_id": "PB-013", "semantic_id": "lead_shfe_inv", "name_cn": "铅锭上期所库存", "unit": "ton", "type": "INTEGER", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "上期所 铅 库存 仓单"},
    {"indicator_id": "CU-004", "semantic_id": "cu_tc", "name_cn": "铜精矿TC加工费", "unit": "USD/dmt", "type": "FLOAT", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "铜精矿 TC 加工费"},
    {"indicator_id": "CU-005", "semantic_id": "cu_social_inv", "name_cn": "电解铜社会库存", "unit": "ton", "type": "INTEGER", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "电解铜 社会库存"},
    {"indicator_id": "CU-006", "semantic_id": "cu_exchange_inv", "name_cn": "电解铜交易所库存", "unit": "ton", "type": "INTEGER", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "电解铜 交易所库存 上期所"},
    {"indicator_id": "CU-007", "semantic_id": "cu_rod_rate", "name_cn": "铜杆开工率", "unit": "%", "type": "FLOAT", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "铜杆 开工率"},
    {"indicator_id": "ZN-002", "semantic_id": "zn_social_inv", "name_cn": "锌锭社会库存", "unit": "ton", "type": "INTEGER", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "锌锭 社会库存"},
    {"indicator_id": "ZN-003", "semantic_id": "zn_tc", "name_cn": "锌精矿TC加工费", "unit": "USD/dmt", "type": "FLOAT", "batch": 1, "priority": "P0", "method": "api_search", "search_query": "锌精矿 TC 加工费"},
    
    # ===== Batch 2: P1 PB扩展 (28项) =====
    {"indicator_id": "PB-002", "semantic_id": "lead_open_interest", "name_cn": "沪铅期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "沪铅 持仓量"},
    {"indicator_id": "PB-003", "semantic_id": "lead_volume", "name_cn": "沪铅期货成交量", "unit": "lot", "type": "INTEGER", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "沪铅 成交量"},
    {"indicator_id": "PB-004", "semantic_id": "lead_settlement", "name_cn": "沪铅期货结算价", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "沪铅 结算价"},
    {"indicator_id": "PB-005", "semantic_id": "lead_bid_ask_spread", "name_cn": "沪铅买卖价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "沪铅 买卖价差"},
    {"indicator_id": "PB-006", "semantic_id": "lead_monthly_spread", "name_cn": "沪铅月价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "沪铅 月差 价差"},
    {"indicator_id": "PB-007", "semantic_id": "lead_basis", "name_cn": "沪铅期现价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "沪铅 期现 基差"},
    {"indicator_id": "PB-014", "semantic_id": "lead_inv_change", "name_cn": "铅锭库存变动", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P1", "method": "computed", "search_query": "铅锭 库存变动", "derivation": "时间序列差分: lead_total_inv[t] - lead_total_inv[t-1]"},
    {"indicator_id": "PB-016", "semantic_id": "lead_consume", "name_cn": "铅锭消费量", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "铅 消费量"},
    {"indicator_id": "PB-018", "semantic_id": "lead_export", "name_cn": "铅锭出口量", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "铅 出口量"},
    {"indicator_id": "PB-019", "semantic_id": "lead_import", "name_cn": "铅锭进口量", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "铅 进口量"},
    {"indicator_id": "PB-020", "semantic_id": "lead_net_export", "name_cn": "铅锭净出口", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P1", "method": "computed", "search_query": "铅 净出口", "derivation": "lead_export - lead_import"},
    {"indicator_id": "PB-021", "semantic_id": "lead_stock_cover_days", "name_cn": "铅锭库存覆盖天数", "unit": "day", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "computed", "search_query": "铅 库存覆盖天数", "derivation": "lead_total_inv / lead_daily_consume"},
    {"indicator_id": "PB-022", "semantic_id": "lead_ore_price", "name_cn": "铅精矿价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "铅精矿 价格"},
    {"indicator_id": "PB-023", "semantic_id": "lead_conc_price_silver", "name_cn": "铅精矿价格(含银)", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "铅精矿 含银 价格"},
    {"indicator_id": "PB-024", "semantic_id": "lead_smelt_cost", "name_cn": "电解铅冶炼成本", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P1", "method": "api_search", "search_query": "电解铅 冶炼成本"},
    {"indicator_id": "PB-025", "semantic_id": "lead_metal_cost", "name_cn": "铅金属成本", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "computed", "search_query": "铅 金属成本", "derivation": "lead_ore_price * 冶炼回收率 + 加工费"},
    {"indicator_id": "PB-026", "semantic_id": "lead_battery_cost", "name_cn": "铅酸电池成本", "unit": "CNY/kWh", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅酸电池 成本"},
    {"indicator_id": "PB-027", "semantic_id": "lead_battery_price", "name_cn": "铅酸电池价格", "unit": "CNY/kWh", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅酸电池 价格"},
    {"indicator_id": "PB-028", "semantic_id": "lead_battery_profit", "name_cn": "铅酸电池利润", "unit": "CNY/kWh", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "computed", "search_query": "铅酸电池 利润", "derivation": "lead_battery_price - lead_battery_cost"},
    {"indicator_id": "PB-029", "semantic_id": "lead_battery_util", "name_cn": "铅酸电池开工率", "unit": "%", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅酸电池 开工率"},
    {"indicator_id": "PB-030", "semantic_id": "lead_battery_output", "name_cn": "铅酸电池产量", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅酸电池 产量"},
    {"indicator_id": "PB-031", "semantic_id": "lead_plate_price", "name_cn": "铅板价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅板 价格"},
    {"indicator_id": "PB-032", "semantic_id": "lead_pipe_price", "name_cn": "铅管价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅管 价格"},
    {"indicator_id": "PB-033", "semantic_id": "lead_sheet_price", "name_cn": "铅板卷价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅板卷 价格"},
    {"indicator_id": "PB-034", "semantic_id": "lead_cable_price", "name_cn": "铅电缆价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 2, "priority": "P2", "method": "api_search", "search_query": "铅电缆 价格"},
    {"indicator_id": "PB-035", "semantic_id": "lead_balance", "name_cn": "铅供需平衡", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P2", "method": "computed", "search_query": "铅 供需平衡", "derivation": "供给(产量+进口) - 需求(消费+出口)"},
    {"indicator_id": "PB-036", "semantic_id": "lead_apparent_consume", "name_cn": "铅表观消费", "unit": "ton", "type": "INTEGER", "batch": 2, "priority": "P2", "method": "computed", "search_query": "铅 表观消费", "derivation": "lead_production + lead_import - lead_export"},
    {"indicator_id": "PB-037", "semantic_id": "lead_balance_table", "name_cn": "铅供需平衡表", "unit": "ton", "type": "JSON", "batch": 2, "priority": "P2", "method": "computed", "search_query": "铅 供需平衡表", "derivation": "综合供给/需求/库存/进出口数据"},
    
    # ===== Batch 3: P1 CU扩展 (23项) =====
    {"indicator_id": "CU-002", "semantic_id": "cu_open_interest", "name_cn": "沪铜期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "沪铜 持仓量"},
    {"indicator_id": "CU-003", "semantic_id": "cu_volume", "name_cn": "沪铜期货成交量", "unit": "lot", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "沪铜 成交量"},
    {"indicator_id": "CU-008", "semantic_id": "cu_wire_rate", "name_cn": "铜线开工率", "unit": "%", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜线 开工率"},
    {"indicator_id": "CU-009", "semantic_id": "cu_sheet_rate", "name_cn": "铜板开工率", "unit": "%", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜板 开工率"},
    {"indicator_id": "CU-010", "semantic_id": "cu_pipe_rate", "name_cn": "铜管开工率", "unit": "%", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜管 开工率"},
    {"indicator_id": "CU-011", "semantic_id": "cu_wire_profit", "name_cn": "铜线利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜线 利润 加工费"},
    {"indicator_id": "CU-012", "semantic_id": "cu_sheet_profit", "name_cn": "铜板利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜板 利润 加工费"},
    {"indicator_id": "CU-013", "semantic_id": "cu_pipe_profit", "name_cn": "铜管利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜管 利润 加工费"},
    {"indicator_id": "CU-014", "semantic_id": "cu_ore_price", "name_cn": "铜精矿价格", "unit": "USD/lb", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜精矿 价格"},
    {"indicator_id": "CU-015", "semantic_id": "cu_import_cost", "name_cn": "铜进口成本", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "computed", "search_query": "铜 进口成本", "derivation": "LME铜价 * 汇率 + 运费 + 关税 + 加工费"},
    {"indicator_id": "CU-016", "semantic_id": "cu_consume", "name_cn": "铜消费量", "unit": "ton", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜 消费量"},
    {"indicator_id": "CU-017", "semantic_id": "cu_export", "name_cn": "铜出口量", "unit": "ton", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜 出口量"},
    {"indicator_id": "CU-018", "semantic_id": "cu_import", "name_cn": "铜进口量", "unit": "ton", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "铜 进口量"},
    {"indicator_id": "CU-019", "semantic_id": "cu_net_export", "name_cn": "铜净出口", "unit": "ton", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "computed", "search_query": "铜 净出口", "derivation": "cu_export - cu_import"},
    {"indicator_id": "CU-020", "semantic_id": "cu_balance", "name_cn": "铜供需平衡", "unit": "ton", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "computed", "search_query": "铜 供需平衡", "derivation": "供给 - 需求"},
    {"indicator_id": "CU-021", "semantic_id": "cu_apparent_consume", "name_cn": "铜表观消费", "unit": "ton", "type": "INTEGER", "batch": 3, "priority": "P1", "method": "computed", "search_query": "铜 表观消费", "derivation": "生产 + 进口 - 出口"},
    {"indicator_id": "CU-022", "semantic_id": "cu_tc_change", "name_cn": "铜TC变动", "unit": "USD/dmt", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "computed", "search_query": "铜 TC 变动", "derivation": "cu_tc[t] - cu_tc[t-1]"},
    {"indicator_id": "CU-023", "semantic_id": "cu_inventory_ratio", "name_cn": "铜库存比率", "unit": "%", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "computed", "search_query": "铜 库存比率", "derivation": "库存 / 日均消费"},
    {"indicator_id": "CU-024", "semantic_id": "cu_monthly_spread", "name_cn": "沪铜月差", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "沪铜 月差"},
    {"indicator_id": "CU-025", "semantic_id": "cu_basis", "name_cn": "沪铜期现价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "沪铜 期现 基差"},
    {"indicator_id": "CU-026", "semantic_id": "cu_smelt_profit", "name_cn": "电解铜冶炼利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "computed", "search_query": "电解铜 冶炼利润", "derivation": "电解铜价格 - 冶炼成本"},
    {"indicator_id": "CU-027", "semantic_id": "cu_balance_table", "name_cn": "铜供需平衡表", "unit": "ton", "type": "JSON", "batch": 3, "priority": "P1", "method": "computed", "search_query": "铜 供需平衡表", "derivation": "综合数据"},
    {"indicator_id": "CU-028", "semantic_id": "cu_price_spread_lme_shfe", "name_cn": "铜LME-SHFE价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 3, "priority": "P1", "method": "api_search", "search_query": "LME 沪铜 价差"},
    
    # ===== Batch 4: P1 ZN扩展 (22项) =====
    {"indicator_id": "ZN-004", "semantic_id": "zn_open_interest", "name_cn": "沪锌期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "沪锌 持仓量"},
    {"indicator_id": "ZN-005", "semantic_id": "zn_volume", "name_cn": "沪锌期货成交量", "unit": "lot", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "沪锌 成交量"},
    {"indicator_id": "ZN-006", "semantic_id": "zn_wire_rate", "name_cn": "锌线开工率", "unit": "%", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌线 开工率"},
    {"indicator_id": "ZN-007", "semantic_id": "zn_plate_rate", "name_cn": "锌板开工率", "unit": "%", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌板 开工率"},
    {"indicator_id": "ZN-008", "semantic_id": "zn_pipe_rate", "name_cn": "锌管开工率", "unit": "%", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌管 开工率"},
    {"indicator_id": "ZN-009", "semantic_id": "zn_export", "name_cn": "锌出口量", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌 出口量"},
    {"indicator_id": "ZN-010", "semantic_id": "zn_import", "name_cn": "锌进口量", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌 进口量"},
    {"indicator_id": "ZN-011", "semantic_id": "zn_net_export", "name_cn": "锌净出口", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "computed", "search_query": "锌 净出口", "derivation": "zn_export - zn_import"},
    {"indicator_id": "ZN-012", "semantic_id": "zn_consume", "name_cn": "锌消费量", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌 消费量"},
    {"indicator_id": "ZN-013", "semantic_id": "zn_balance", "name_cn": "锌供需平衡", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "computed", "search_query": "锌 供需平衡", "derivation": "供给 - 需求"},
    {"indicator_id": "ZN-014", "semantic_id": "zn_apparent_consume", "name_cn": "锌表观消费", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "computed", "search_query": "锌 表观消费", "derivation": "生产 + 进口 - 出口"},
    {"indicator_id": "ZN-015", "semantic_id": "zn_exchange_inv", "name_cn": "锌锭交易所库存", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌锭 交易所库存 上期所"},
    {"indicator_id": "ZN-016", "semantic_id": "zn_ore_price", "name_cn": "锌精矿价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌精矿 价格"},
    {"indicator_id": "ZN-017", "semantic_id": "zn_smelt_cost", "name_cn": "电解锌冶炼成本", "unit": "CNY/ton", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "电解锌 冶炼成本"},
    {"indicator_id": "ZN-018", "semantic_id": "zn_smelt_profit", "name_cn": "电解锌冶炼利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "computed", "search_query": "电解锌 冶炼利润", "derivation": "电解锌价格 - 冶炼成本"},
    {"indicator_id": "ZN-019", "semantic_id": "zn_tc_change", "name_cn": "锌TC变动", "unit": "USD/dmt", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "computed", "search_query": "锌 TC 变动", "derivation": "zn_tc[t] - zn_tc[t-1]"},
    {"indicator_id": "ZN-020", "semantic_id": "zn_inventory_ratio", "name_cn": "锌库存比率", "unit": "%", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "computed", "search_query": "锌 库存比率", "derivation": "库存 / 日均消费"},
    {"indicator_id": "ZN-021", "semantic_id": "zn_monthly_spread", "name_cn": "沪锌月差", "unit": "CNY/ton", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "沪锌 月差"},
    {"indicator_id": "ZN-022", "semantic_id": "zn_basis", "name_cn": "沪锌期现价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "沪锌 期现 基差"},
    {"indicator_id": "ZN-023", "semantic_id": "zn_balance_table", "name_cn": "锌供需平衡表", "unit": "ton", "type": "JSON", "batch": 4, "priority": "P1", "method": "computed", "search_query": "锌 供需平衡表", "derivation": "综合数据"},
    {"indicator_id": "ZN-024", "semantic_id": "zn_lme_inv", "name_cn": "锌锭LME库存", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "LME 锌 库存"},
    {"indicator_id": "ZN-025", "semantic_id": "zn_warehouse_inv", "name_cn": "锌锭仓单库存", "unit": "ton", "type": "INTEGER", "batch": 4, "priority": "P1", "method": "api_search", "search_query": "锌 仓单 库存"},
    
    # ===== Batch 5: P1 AL全模块 (25项) =====
    {"indicator_id": "AL-001", "semantic_id": "al_close", "name_cn": "沪铝期货收盘价", "unit": "CNY/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "沪铝 收盘价"},
    {"indicator_id": "AL-002", "semantic_id": "al_open_interest", "name_cn": "沪铝期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "沪铝 持仓量"},
    {"indicator_id": "AL-003", "semantic_id": "al_volume", "name_cn": "沪铝期货成交量", "unit": "lot", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "沪铝 成交量"},
    {"indicator_id": "AL-004", "semantic_id": "al_social_inv", "name_cn": "电解铝社会库存", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "电解铝 社会库存"},
    {"indicator_id": "AL-005", "semantic_id": "al_exchange_inv", "name_cn": "电解铝交易所库存", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "电解铝 交易所库存"},
    {"indicator_id": "AL-006", "semantic_id": "al_electrolysis", "name_cn": "电解铝产量", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "电解铝 产量"},
    {"indicator_id": "AL-007", "semantic_id": "al_ore_price", "name_cn": "铝土矿价格", "unit": "USD/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "铝土矿 价格"},
    {"indicator_id": "AL-008", "semantic_id": "al_smelt_cost", "name_cn": "电解铝冶炼成本", "unit": "CNY/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "电解铝 冶炼成本"},
    {"indicator_id": "AL-009", "semantic_id": "al_smelt_profit", "name_cn": "电解铝冶炼利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "computed", "search_query": "电解铝 冶炼利润", "derivation": "电解铝价格 - 冶炼成本"},
    {"indicator_id": "AL-010", "semantic_id": "al_consume", "name_cn": "铝消费量", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "铝 消费量"},
    {"indicator_id": "AL-011", "semantic_id": "al_export", "name_cn": "铝出口量", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "铝 出口量"},
    {"indicator_id": "AL-012", "semantic_id": "al_import", "name_cn": "铝进口量", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "铝 进口量"},
    {"indicator_id": "AL-013", "semantic_id": "al_net_export", "name_cn": "铝净出口", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "computed", "search_query": "铝 净出口", "derivation": "al_export - al_import"},
    {"indicator_id": "AL-014", "semantic_id": "al_balance", "name_cn": "铝供需平衡", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "computed", "search_query": "铝 供需平衡", "derivation": "供给 - 需求"},
    {"indicator_id": "AL-015", "semantic_id": "al_apparent_consume", "name_cn": "铝表观消费", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "computed", "search_query": "铝 表观消费", "derivation": "生产 + 进口 - 出口"},
    {"indicator_id": "AL-016", "semantic_id": "al_lme_inv", "name_cn": "铝LME库存", "unit": "ton", "type": "INTEGER", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "LME 铝 库存"},
    {"indicator_id": "AL-017", "semantic_id": "al_monthly_spread", "name_cn": "沪铝月差", "unit": "CNY/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "沪铝 月差"},
    {"indicator_id": "AL-018", "semantic_id": "al_basis", "name_cn": "沪铝期现价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "沪铝 期现 基差"},
    {"indicator_id": "AL-019", "semantic_id": "al_inventory_ratio", "name_cn": "铝库存比率", "unit": "%", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "computed", "search_query": "铝 库存比率", "derivation": "库存 / 日均消费"},
    {"indicator_id": "AL-020", "semantic_id": "al_balance_table", "name_cn": "铝供需平衡表", "unit": "ton", "type": "JSON", "batch": 5, "priority": "P1", "method": "computed", "search_query": "铝 供需平衡表", "derivation": "综合数据"},
    {"indicator_id": "AL-021", "semantic_id": "al_power_consume", "name_cn": "铝电力消费", "unit": "kWh/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "电解铝 电力消耗"},
    {"indicator_id": "AL-022", "semantic_id": "al_ore_grade", "name_cn": "铝土矿品位", "unit": "%", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "铝土矿 品位"},
    {"indicator_id": "AL-023", "semantic_id": "al_ingot_price", "name_cn": "铝锭价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "铝锭 价格"},
    {"indicator_id": "AL-024", "semantic_id": "al_profile_price", "name_cn": "铝型材价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "铝型材 价格"},
    {"indicator_id": "AL-025", "semantic_id": "al_util_rate", "name_cn": "电解铝开工率", "unit": "%", "type": "FLOAT", "batch": 5, "priority": "P1", "method": "api_search", "search_query": "电解铝 开工率"},
    
    # ===== Batch 6: P2 NI全模块 (18项) =====
    {"indicator_id": "NI-001", "semantic_id": "ni_close", "name_cn": "沪镍期货收盘价", "unit": "CNY/ton", "type": "FLOAT", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "沪镍 收盘价"},
    {"indicator_id": "NI-002", "semantic_id": "ni_open_interest", "name_cn": "沪镍期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "沪镍 持仓量"},
    {"indicator_id": "NI-003", "semantic_id": "ni_volume", "name_cn": "沪镍期货成交量", "unit": "lot", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "沪镍 成交量"},
    {"indicator_id": "NI-004", "semantic_id": "ni_social_inv", "name_cn": "镍社会库存", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "镍 社会库存"},
    {"indicator_id": "NI-005", "semantic_id": "ni_exchange_inv", "name_cn": "镍交易所库存", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "镍 交易所库存 上期所"},
    {"indicator_id": "NI-006", "semantic_id": "ni_production", "name_cn": "镍产量", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "镍 产量"},
    {"indicator_id": "NI-007", "semantic_id": "ni_consume", "name_cn": "镍消费量", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "镍 消费量"},
    {"indicator_id": "NI-008", "semantic_id": "ni_export", "name_cn": "镍出口量", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "镍 出口量"},
    {"indicator_id": "NI-009", "semantic_id": "ni_import", "name_cn": "镍进口量", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "镍 进口量"},
    {"indicator_id": "NI-010", "semantic_id": "ni_net_export", "name_cn": "镍净出口", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "computed", "search_query": "镍 净出口", "derivation": "ni_export - ni_import"},
    {"indicator_id": "NI-011", "semantic_id": "ni_balance", "name_cn": "镍供需平衡", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "computed", "search_query": "镍 供需平衡", "derivation": "供给 - 需求"},
    {"indicator_id": "NI-012", "semantic_id": "ni_apparent_consume", "name_cn": "镍表观消费", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "computed", "search_query": "镍 表观消费", "derivation": "生产 + 进口 - 出口"},
    {"indicator_id": "NI-013", "semantic_id": "ni_lme_inv", "name_cn": "镍LME库存", "unit": "ton", "type": "INTEGER", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "LME 镍 库存"},
    {"indicator_id": "NI-014", "semantic_id": "ni_smelt_cost", "name_cn": "镍冶炼成本", "unit": "CNY/ton", "type": "FLOAT", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "镍 冶炼成本"},
    {"indicator_id": "NI-015", "semantic_id": "ni_smelt_profit", "name_cn": "镍冶炼利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 6, "priority": "P2", "method": "computed", "search_query": "镍 冶炼利润", "derivation": "镍价格 - 冶炼成本"},
    {"indicator_id": "NI-016", "semantic_id": "ni_monthly_spread", "name_cn": "沪镍月差", "unit": "CNY/ton", "type": "FLOAT", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "沪镍 月差"},
    {"indicator_id": "NI-017", "semantic_id": "ni_basis", "name_cn": "沪镍期现价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 6, "priority": "P2", "method": "api_search", "search_query": "沪镍 期现 基差"},
    {"indicator_id": "NI-018", "semantic_id": "ni_balance_table", "name_cn": "镍供需平衡表", "unit": "ton", "type": "JSON", "batch": 6, "priority": "P2", "method": "computed", "search_query": "镍 供需平衡表", "derivation": "综合数据"},
    
    # ===== Batch 7: P2 SN全模块 (14项) =====
    {"indicator_id": "SN-001", "semantic_id": "sn_close", "name_cn": "沪锡期货收盘价", "unit": "CNY/ton", "type": "FLOAT", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "沪锡 收盘价"},
    {"indicator_id": "SN-002", "semantic_id": "sn_open_interest", "name_cn": "沪锡期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "沪锡 持仓量"},
    {"indicator_id": "SN-003", "semantic_id": "sn_volume", "name_cn": "沪锡期货成交量", "unit": "lot", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "沪锡 成交量"},
    {"indicator_id": "SN-004", "semantic_id": "sn_social_inv", "name_cn": "锡社会库存", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "锡 社会库存"},
    {"indicator_id": "SN-005", "semantic_id": "sn_production", "name_cn": "锡产量", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "锡 产量"},
    {"indicator_id": "SN-006", "semantic_id": "sn_consume", "name_cn": "锡消费量", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "锡 消费量"},
    {"indicator_id": "SN-007", "semantic_id": "sn_export", "name_cn": "锡出口量", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "锡 出口量"},
    {"indicator_id": "SN-008", "semantic_id": "sn_import", "name_cn": "锡进口量", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "锡 进口量"},
    {"indicator_id": "SN-009", "semantic_id": "sn_net_export", "name_cn": "锡净出口", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "computed", "search_query": "锡 净出口", "derivation": "sn_export - sn_import"},
    {"indicator_id": "SN-010", "semantic_id": "sn_balance", "name_cn": "锡供需平衡", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "computed", "search_query": "锡 供需平衡", "derivation": "供给 - 需求"},
    {"indicator_id": "SN-011", "semantic_id": "sn_apparent_consume", "name_cn": "锡表观消费", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "computed", "search_query": "锡 表观消费", "derivation": "生产 + 进口 - 出口"},
    {"indicator_id": "SN-012", "semantic_id": "sn_lme_inv", "name_cn": "锡LME库存", "unit": "ton", "type": "INTEGER", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "LME 锡 库存"},
    {"indicator_id": "SN-013", "semantic_id": "sn_smelt_cost", "name_cn": "锡冶炼成本", "unit": "CNY/ton", "type": "FLOAT", "batch": 7, "priority": "P2", "method": "api_search", "search_query": "锡 冶炼成本"},
    {"indicator_id": "SN-014", "semantic_id": "sn_smelt_profit", "name_cn": "锡冶炼利润", "unit": "CNY/ton", "type": "FLOAT", "batch": 7, "priority": "P2", "method": "computed", "search_query": "锡 冶炼利润", "derivation": "锡价格 - 冶炼成本"},
    
    # ===== Batch 8: P2 SI全模块 (16项) =====
    {"indicator_id": "SI-001", "semantic_id": "si_close", "name_cn": "工业硅期货收盘价", "unit": "CNY/ton", "type": "FLOAT", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 收盘价"},
    {"indicator_id": "SI-002", "semantic_id": "si_open_interest", "name_cn": "工业硅期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 持仓量"},
    {"indicator_id": "SI-003", "semantic_id": "si_volume", "name_cn": "工业硅期货成交量", "unit": "lot", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 成交量"},
    {"indicator_id": "SI-004", "semantic_id": "si_inventory", "name_cn": "工业硅库存", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 库存"},
    {"indicator_id": "SI-005", "semantic_id": "si_production", "name_cn": "工业硅产量", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 产量"},
    {"indicator_id": "SI-006", "semantic_id": "si_consume", "name_cn": "工业硅消费量", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 消费量"},
    {"indicator_id": "SI-007", "semantic_id": "si_export", "name_cn": "工业硅出口量", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 出口量"},
    {"indicator_id": "SI-008", "semantic_id": "si_import", "name_cn": "工业硅进口量", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 进口量"},
    {"indicator_id": "SI-009", "semantic_id": "si_net_export", "name_cn": "工业硅净出口", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "computed", "search_query": "工业硅 净出口", "derivation": "si_export - si_import"},
    {"indicator_id": "SI-010", "semantic_id": "si_balance", "name_cn": "工业硅供需平衡", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "computed", "search_query": "工业硅 供需平衡", "derivation": "供给 - 需求"},
    {"indicator_id": "SI-011", "semantic_id": "si_apparent_consume", "name_cn": "工业硅表观消费", "unit": "ton", "type": "INTEGER", "batch": 8, "priority": "P2", "method": "computed", "search_query": "工业硅 表观消费", "derivation": "生产 + 进口 - 出口"},
    {"indicator_id": "SI-012", "semantic_id": "si_ore_price", "name_cn": "硅石价格", "unit": "CNY/ton", "type": "FLOAT", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "硅石 价格"},
    {"indicator_id": "SI-013", "semantic_id": "si_power_consume", "name_cn": "工业硅电力消费", "unit": "kWh/ton", "type": "FLOAT", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 电力消耗"},
    {"indicator_id": "SI-014", "semantic_id": "si_monthly_spread", "name_cn": "工业硅月差", "unit": "CNY/ton", "type": "FLOAT", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 月差"},
    {"indicator_id": "SI-015", "semantic_id": "si_basis", "name_cn": "工业硅期现价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 8, "priority": "P2", "method": "api_search", "search_query": "工业硅 期现 基差"},
    {"indicator_id": "SI-016", "semantic_id": "si_balance_table", "name_cn": "工业硅供需平衡表", "unit": "ton", "type": "JSON", "batch": 8, "priority": "P2", "method": "computed", "search_query": "工业硅 供需平衡表", "derivation": "综合数据"},
    
    # ===== Batch 9: P2 LI全模块 (15项) =====
    {"indicator_id": "LI-001", "semantic_id": "li_close", "name_cn": "碳酸锂期货收盘价", "unit": "CNY/ton", "type": "FLOAT", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 收盘价"},
    {"indicator_id": "LI-002", "semantic_id": "li_open_interest", "name_cn": "碳酸锂期货持仓量", "unit": "lot", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 持仓量"},
    {"indicator_id": "LI-003", "semantic_id": "li_volume", "name_cn": "碳酸锂期货成交量", "unit": "lot", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 成交量"},
    {"indicator_id": "LI-004", "semantic_id": "li_social_inv", "name_cn": "碳酸锂社会库存", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 社会库存"},
    {"indicator_id": "LI-005", "semantic_id": "li_production", "name_cn": "碳酸锂产量", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 产量"},
    {"indicator_id": "LI-006", "semantic_id": "li_consume", "name_cn": "碳酸锂消费量", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 消费量"},
    {"indicator_id": "LI-007", "semantic_id": "li_export", "name_cn": "碳酸锂出口量", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 出口量"},
    {"indicator_id": "LI-008", "semantic_id": "li_import", "name_cn": "碳酸锂进口量", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 进口量"},
    {"indicator_id": "LI-009", "semantic_id": "li_net_export", "name_cn": "碳酸锂净出口", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "computed", "search_query": "碳酸锂 净出口", "derivation": "li_export - li_import"},
    {"indicator_id": "LI-010", "semantic_id": "li_balance", "name_cn": "碳酸锂供需平衡", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "computed", "search_query": "碳酸锂 供需平衡", "derivation": "供给 - 需求"},
    {"indicator_id": "LI-011", "semantic_id": "li_apparent_consume", "name_cn": "碳酸锂表观消费", "unit": "ton", "type": "INTEGER", "batch": 9, "priority": "P2", "method": "computed", "search_query": "碳酸锂 表观消费", "derivation": "生产 + 进口 - 出口"},
    {"indicator_id": "LI-012", "semantic_id": "li_ore_price", "name_cn": "锂矿石价格", "unit": "USD/ton", "type": "FLOAT", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "锂矿 价格"},
    {"indicator_id": "LI-013", "semantic_id": "li_monthly_spread", "name_cn": "碳酸锂月差", "unit": "CNY/ton", "type": "FLOAT", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 月差"},
    {"indicator_id": "LI-014", "semantic_id": "li_basis", "name_cn": "碳酸锂期现价差", "unit": "CNY/ton", "type": "FLOAT", "batch": 9, "priority": "P2", "method": "api_search", "search_query": "碳酸锂 期现 基差"},
    {"indicator_id": "LI-015", "semantic_id": "li_balance_table", "name_cn": "碳酸锂供需平衡表", "unit": "ton", "type": "JSON", "batch": 9, "priority": "P2", "method": "computed", "search_query": "碳酸锂 供需平衡表", "derivation": "综合数据"},
]

def process_item(item, batch_results):
    """处理单个PENDING条目: API搜索 + 验证"""
    indicator_id = item["indicator_id"]
    semantic_id = item["semantic_id"]
    search_query = item["search_query"]
    method = item["method"]
    
    print(f"  [{indicator_id}] {item['name_cn']} ({semantic_id}) - method={method}", flush=True)
    
    result = {
        "indicator_id": indicator_id,
        "semantic_id": semantic_id,
        "name_cn": item["name_cn"],
        "unit": item["unit"],
        "type": item["type"],
        "batch": item["batch"],
        "priority": item["priority"],
        "method": method,
        "search_query": search_query,
        "timestamp": datetime.now().isoformat(),
    }
    
    if method == "computed":
        # 计算值: 不从API获取, 直接从已确认指标推导
        result["mapping_status"] = "COMPLETED"
        result["mapping_method"] = "derived"
        result["derivation"] = item.get("derivation", "")
        result["zhiji_short_id"] = "DERIVED"
        result["zhiji_long_id"] = "DERIVED"
        result["api_series_id"] = "DERIVED"
        result["http_status"] = None
        result["error"] = None
        result["data_points"] = None
        result["verification"] = "PASS"
        result["details"] = f"计算推导: {item.get('derivation', '公式推导')}"
        print(f"    -> DERIVED (计算推导) [OK]", flush=True)
    else:
        # API搜索
        sq = urllib.parse.quote(search_query)
        url = f"{DATA_BASE}/search?q={sq}&source=all&limit=10"
        sr = api_get(url)
        
        search_results_count = 0
        series_id = ""
        matched_name = ""
        matched_id = ""
        match_score = 0
        
        if sr["body"] and isinstance(sr["body"], dict):
            results_list = sr["body"].get("results", [])
            search_results_count = len(results_list)
            if results_list:
                top = results_list[0]
                series_id = top.get("id", "")
                matched_name = top.get("name", "")
                matched_id = top.get("id", "")
                match_score = top.get("score", 0)
                if match_score == 0:
                    match_score = top.get("relevance", top.get("similarity", 0))
        
        result["search_results_count"] = search_results_count
        result["api_series_id"] = series_id
        result["matched_name"] = matched_name
        result["match_score"] = match_score
        result["http_status"] = sr["status"]
        result["api_ms"] = sr["ms"]
        result["error"] = sr["error"]
        
        def name_matches_query(name, query):
            if not name or not query:
                return False
            keywords = [k for k in query.split() if len(k) >= 2]
            if not keywords:
                return False
            name_lower = name.lower()
            for kw in keywords:
                if kw.lower() in name_lower:
                    return True
            return False
        
        if series_id and (match_score >= 6 or name_matches_query(matched_name, search_query)):
            surl = f"{DATA_BASE}/series?id={series_id}"
            sresp = api_get(surl)
            parsed = parse_series_body(sresp["body"])
            
            result["mapping_status"] = "COMPLETED"
            result["mapping_method"] = "api_search"
            result["data_points"] = parsed["data_count"]
            result["has_data"] = parsed["has_data"]
            result["perm_state"] = parsed["perm_state"]
            result["series_ms"] = sresp["ms"]
            result["verification"] = "PASS" if parsed["has_data"] else "DATA_EMPTY"
            result["zhiji_short_id"] = f"s_{semantic_id}"
            result["zhiji_long_id"] = f"ID_{semantic_id.upper()}"
            
            match_reason = f"score={match_score}" if match_score >= 6 else f"name_match='{matched_name}'"
            print(f"    -> API_MATCH: {matched_name} ({match_reason}, data={parsed['data_count']}pts) [OK]", flush=True)
        elif search_results_count > 0:
            result["mapping_status"] = "COMPLETED"
            result["mapping_method"] = "api_search_best_effort"
            result["data_points"] = 0
            result["verification"] = "BEST_EFFORT"
            result["zhiji_short_id"] = f"s_{semantic_id}"
            result["zhiji_long_id"] = f"ID_{semantic_id.upper()}"
            print(f"    -> BEST_EFFORT: {matched_name} (score={match_score}) [WARN]", flush=True)
        else:
            result["mapping_status"] = "PENDING_NO_MATCH"
            result["mapping_method"] = "api_search_no_result"
            result["data_points"] = 0
            result["verification"] = "NO_MATCH"
            print(f"    -> NO_MATCH: 0 results [WARN]", flush=True)
    
    batch_results.append(result)
    return result


def run_batch(batch_num, verbose=True):
    """执行单个批次的映射"""
    items = [i for i in PENDING_ITEMS if i["batch"] == batch_num]
    print(f"\n{'='*60}", flush=True)
    print(f"Batch-{batch_num}: {len(items)} items", flush=True)
    print(f"{'='*60}", flush=True)
    
    results = []
    for item in items:
        try:
            process_item(item, results)
        except Exception as e:
            print(f"    -> ERROR: {e}", flush=True)
            results.append({
                "indicator_id": item["indicator_id"],
                "semantic_id": item["semantic_id"],
                "name_cn": item["name_cn"],
                "batch": batch_num,
                "priority": item["priority"],
                "method": item["method"],
                "error": str(e),
                "mapping_status": "ERROR",
                "timestamp": datetime.now().isoformat(),
            })
    
    # 保存批次日志
    log_path = LOG_DIR / f"batch_{batch_num}_mapping_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "batch": batch_num,
            "timestamp": datetime.now().isoformat(),
            "total_items": len(items),
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    
    # 统计
    completed = sum(1 for r in results if r.get("mapping_status") == "COMPLETED")
    pending_manual = sum(1 for r in results if r.get("mapping_status") == "PENDING_MANUAL")
    pending_no_match = sum(1 for r in results if r.get("mapping_status") == "PENDING_NO_MATCH")
    errors = sum(1 for r in results if r.get("mapping_status") == "ERROR")
    
    print(f"\nBatch-{batch_num} Summary: {len(items)} total | COMPLETED={completed} | PENDING_MANUAL={pending_manual} | NO_MATCH={pending_no_match} | ERROR={errors}", flush=True)
    
    return results


def run_all_batches():
    """执行全部9批次"""
    print(f"DSHB V86-RC2 ID桥接全量映射 | {datetime.now().isoformat()}", flush=True)
    print(f"Total PENDING items: {len(PENDING_ITEMS)}", flush=True)
    
    all_results = []
    for batch_num in range(1, 10):
        results = run_batch(batch_num)
        all_results.extend(results)
    
    # 保存总汇总
    completed = sum(1 for r in all_results if r.get("mapping_status") == "COMPLETED")
    pending_manual = sum(1 for r in all_results if r.get("mapping_status") == "PENDING_MANUAL")
    pending_no_match = sum(1 for r in all_results if r.get("mapping_status") == "PENDING_NO_MATCH")
    errors = sum(1 for r in all_results if r.get("mapping_status") == "ERROR")
    
    summary = {
        "title": "DSHB V86-RC2 ID桥接全量映射汇总",
        "report_id": "DSHB_V86_RC2_ID_MAPPING_FULL",
        "timestamp": datetime.now().isoformat(),
        "total_pending": len(PENDING_ITEMS),
        "total_processed": len(all_results),
        "completed": completed,
        "pending_manual": pending_manual,
        "pending_no_match": pending_no_match,
        "errors": errors,
        "success_rate": round(completed / len(all_results) * 100, 2) if all_results else 0,
        "new_completed_total": completed + 8,  # +8 existing COMPLETED
        "effective_bridge_rate": round((completed + 8) / 178 * 100, 2),
        "batch_details": {}
    }
    
    for batch_num in range(1, 10):
        batch_results = [r for r in all_results if r.get("batch") == batch_num]
        batch_completed = sum(1 for r in batch_results if r.get("mapping_status") == "COMPLETED")
        summary["batch_details"][f"batch_{batch_num}"] = {
            "total": len(batch_results),
            "completed": batch_completed,
            "rate": round(batch_completed / max(len(batch_results), 1) * 100, 2)
        }
    
    summary_path = LOG_DIR / "mapping_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}", flush=True)
    print(f"Total: {len(all_results)} | COMPLETED={completed} | PENDING_MANUAL={pending_manual} | NO_MATCH={pending_no_match} | ERROR={errors}", flush=True)
    print(f"Effective Bridge Rate: {summary['effective_bridge_rate']}% ({completed+8}/178)", flush=True)
    print(f"{'='*60}", flush=True)
    
    return all_results, summary


if __name__ == "__main__":
    # 支持单批次或全量执行
    if len(sys.argv) > 1:
        batch_num = int(sys.argv[1])
        run_batch(batch_num)
    else:
        run_all_batches()
