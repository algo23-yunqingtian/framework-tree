#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""硅/锂对照表 → indicators_v1.json 追加注册器（append-only）。

读 analysis/iwencai/correction_register_plan.json（parse_correction_register.py 产物）
→ 按 (节点, 概念, 单个 zhiji_id) 生成条目追加进 data/indicators_v1.json。

规则：
- append-only：已有 zhiji_id（全局全库）绝不覆盖；命中即跳过
- 命名: {code}_{node无点}_{slug}，重名加数字后缀
- 备份：写入前 cp 到 analysis/backups/indicators_v1_before_si_li_<时间>.json
- 版本：_meta.version 与顶层 version 同步递增并保持一致(3.43→3.44, v3.45→v3.46)
- changelog 追加记录
"""
import json, os, re, sys, shutil
from datetime import datetime
from pathlib import Path
from copy import deepcopy

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "analysis" / "iwencai" / "correction_register_plan.json"
IND = REPO / "data" / "indicators_v1.json"
BACK = REPO / "analysis" / "backups"
BACK.mkdir(parents=True, exist_ok=True)

# 品种 slug 词汇（复用 step3 风格）
SLUG_MAP = {
    "LME": "lme", "SHFE": "shfe", "COMEX": "comex",
    "收盘价": "close", "结算价": "settle", "开盘价": "open", "最高价": "high",
    "最低价": "low", "升贴水": "premium", "基差": "basis", "价差": "spread",
    "库存": "inv", "仓单": "warrant", "注销仓单": "unreg_warrant",
    "总库存": "total_inv", "社库": "social_inv", "社会库存": "social_inv",
    "产量": "output", "开工率": "util", "检修": "shutdown", "减产": "downprod",
    "进口": "import", "出口": "export", "净进口": "net_import",
    "消费": "cons", "需求": "demand", "表观消费": "apparent_cons",
    "成本": "cost", "利润": "profit", "加工费": "tc", "TC": "tc",
    "溢价": "premium", "占比": "ratio", "分位": "percentile",
    "持仓": "openinterest", "成交量": "volume",
    "前20": "top20", "净多": "net_long", "净空": "net_short",
    "主力": "front", "近月": "near", "远月": "far", "月差": "spread",
    "精矿": "conc", "废": "scrap", "再生": "recycle",
    "平衡": "balance", "汇率": "fx", "美元": "usd",
    "价格": "price", "均价": "avg_price", "关税": "tariff",
    "产能": "capacity", "利用率": "util", "电费": "power_cost",
    "现金成本": "cash_cost", "完全成本": "total_cost",
    "发运": "shipment", "到港": "arrival", "依存度": "dep",
    "盈亏": "profit_loss", "表观": "apparent", "现货": "spot",
    "期货": "futures", "基差": "basis", "结构": "struct",
    "开工": "util", "再生硅": "recycle_si", "冶炼": "smelt",
    "表观消费": "apparent_cons", "持仓量": "openinterest",
    "成交量": "volume", "持仓": "openinterest", "开工": "util",
    "硅石": "silica", "现金": "cash", "电价": "power",
    "原料": "raw", "能源": "energy", "分位": "percentile",
    "综合": "total", "总计": "total", "数量": "qty",
    "分国别": "by_country", "分省份": "by_province",
    "分产区": "by_region", "分地区": "by_region",
    "综合开工率": "util", "利用率": "util",
}

FREQ_MAP = {"日": "daily", "周": "weekly", "月": "monthly", "季": "quarterly",
            "半年": "halfyear", "年": "yearly"}
FREQ_CN = {"日度": "daily", "周度": "weekly", "月度": "monthly",
           "季度": "quarterly", "年度": "yearly"}


def slugify(name):
    n = re.sub(r"【[^】]*】", "", name).strip()
    n = re.sub(r"（[^）]*）$", "", n).strip()
    n = re.sub(r"\([^)]*$", "", n).strip()
    n = re.sub(r"\*+", "", n).strip()
    parts = []
    rest = n
    # 多到少，避免重复
    for cn, en in sorted(SLUG_MAP.items(), key=lambda x: -len(x[0])):
        while cn in rest:
            parts.append(en)
            rest = rest.replace(cn, " ", 1)
    rest = rest.strip()
    rest = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]", "", rest)
    if parts:
        # 去重保序
        seen = []
        for p in parts:
            if p not in seen:
                seen.append(p)
        return "_".join(seen[:3])[:28]
    return re.sub(r"[^a-z0-9]", "", n)[:24] or "idx"


def infer_freq(row):
    if row.get("freq"):
        return row["freq"]
    s = (row.get("unit", "") + " " + row.get("concept", ""))
    for kw, v in FREQ_CN.items():
        if kw in s:
            return v
    for k, v in FREQ_MAP.items():
        if k in s:
            return v
    return "daily"


def clean_concept(c):
    if not c:
        return ""
    c = re.sub(r"^\d+\s*\|", "", c).strip()
    c = re.sub(r"\*+", "", c).strip()
    return c


def node_short(node):
    return node.replace(".", "").replace("final", "f")


def main():
    plan = json.load(open(PLAN, encoding="utf-8"))
    doc = json.load(open(IND, encoding="utf-8"))
    ind = doc["indicators"]

    # 全库已用 zhiji_id（去重键）
    used_ids = set()
    for v in ind.values():
        for k, idv in (v.get("ids") or {}).items():
            if idv:
                used_ids.add(idv)

    new_entries = {}
    skipped = []  # (code, node, concept, id, reason)

    for code in ["SI", "LI"]:
        nodes = plan.get(code, {})
        if not nodes:
            continue
        def _key(x):
            s = re.sub(r"\.final$", "", x)
            return [int(p) for p in s.split(".") if p]
        for node in sorted(nodes, key=_key):
            block = nodes[node]
            rows = block.get("rows", [])
            nshort = node_short(node)
            for row in rows:
                concept = clean_concept(row.get("concept", ""))
                if not concept:
                    continue
                ids = row.get("ids") or []
                if not ids:
                    continue
                for zhiji_id in ids:
                    if zhiji_id in used_ids:
                        skipped.append((code, node, concept, zhiji_id, "id已注册:%s" % zhiji_id))
                        continue
                    slug = slugify(concept)
                    base_key = "%s_%s_%s" % (code.lower(), nshort, slug)
                    key = base_key
                    n = 1
                    while key in ind:
                        n += 1
                        key = "%s_%d" % (base_key, n)
                    new_entries[key] = {
                        "name": concept,
                        "unit": row.get("unit", ""),
                        "freq": infer_freq(row),
                        "verified": True,
                        "ids": {code: zhiji_id},
                        "_origin": "correction_%s_%s_%s" % (code, node, concept[:30]),
                        "_nodes": [node],
                    }
                    used_ids.add(zhiji_id)

    # 写入前备份
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    backup_path = BACK / ("indicators_v1_before_si_li_%s.json" % ts)
    shutil.copy2(IND, backup_path)
    print("备份:", backup_path)

    ind.update(new_entries)

    # 版本同步递增
    meta_ver = doc.get("_meta", {}).get("version", "0.0")
    major, minor = map(int, meta_ver.split("."))
    new_meta_ver = "%d.%d" % (major, minor + 1)
    top_ver = doc.get("version", "")  # e.g. "v3.45"
    top_num = re.sub(r"[vV]", "", top_ver)  # "v3.45" -> "3.45"（保留点号）
    tparts = top_num.split(".")
    new_top_ver = "v%s.%s" % (tparts[0], int(tparts[1]) + 1) if len(tparts) >= 2 and tparts[0] else top_ver

    doc["_meta"]["version"] = new_meta_ver
    doc["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc["version"] = new_top_ver
    doc["change"] = "硅锂对照表注册: 追加 SI+LI 正确 ID (%d条新增, id去重跳过 %d) 备份@%s" % (
        len(new_entries), len(skipped), backup_path.name)

    json.dump(doc, open(IND, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 验证 JSON 合法
    json.load(open(IND, encoding="utf-8"))

    counts = {"SI": 0, "LI": 0}
    for k in new_entries:
        for c in counts:
            if k.startswith(c.lower()):
                counts[c] += 1
                break

    print("=== 硅/锂 注册结果 ===")
    for c in counts:
        print("  新增 %s: %d 条" % (c, counts[c]))
    print("  跳过(去重): %d 条" % len(skipped))
    print("  注册后总指标数: %d" % len(ind))
    print("  _meta.version: %s  → %s" % (meta_ver, new_meta_ver))
    print("  version: %s  → %s" % (top_ver, new_top_ver))
    print("跳过样例:")
    for code, node, concept, zhiji_id, why in skipped[:20]:
        print("  [%s] %s %s -> %s" % (code, node, concept[:28], why))
    if len(skipped) > 20:
        print("  ... 共 %d 条跳过" % len(skipped))


if __name__ == "__main__":
    main()
