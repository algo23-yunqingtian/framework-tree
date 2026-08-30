#!/usr/bin/env python3
"""把 Step3 Tier A + Tier B 指标注册进 indicators_v1.json。

命名: cu_<节点短码>_<slug> / al_<节点短码>_<slug>
    例: cu_21_lme_3m_close / al_321_refine_output
去重: 若该 知几id 已在 indicators 中注册过 → 跳过（避免重复灌库）
只注册 Tier A(人工判定) + Tier B(规则通过)，Tier C 留备用库不动。
"""
import json, os, re, sys
from datetime import datetime

REPO = "/home/ubuntu/framework-tree"
FINAL = os.path.join(REPO, "analysis/iwencai/step3_final.json")
IND = os.path.join(REPO, "data/indicators_v1.json")

SLUG_MAP = {
    "LME": "lme", "SHFE": "shfe", "COMEX": "comex", "CFTC": "cftc", "USGS": "usgs",
    "收盘价": "close", "结算价": "settle", "开盘价": "open", "最高价": "high",
    "最低价": "low", "升贴水": "premium", "基差": "basis", "价差": "spread",
    "库存": "inv", "仓单": "warrant", "注册仓单": "reg_warrant",
    "注销仓单": "unreg_warrant", "总库存": "total_inv", "社库": "social_inv",
    "社会库存": "social_inv", "厂内": "plant", "隐性": "implicit",
    "产量": "output", "开工率": "util", "检修": "shutdown", "减产": "downprod",
    "进口": "import", "出口": "export", "净进口": "net_import",
    "消费": "cons", "需求": "demand", "表观消费": "apparent_cons",
    "成本": "cost", "利润": "profit", "加工费": "tc", "TC": "tc",
    "TC加工费": "tc", "溢价": "premium", "占比": "ratio", "分位": "percentile",
    "持仓": "openinterest", "成交量": "volume", "多空": "longshort",
    "前20": "top20", "净多": "net_long", "净空": "net_short",
    "主力": "front", "近月": "near", "远月": "far", "月差": "spread",
    "铜精矿": "conc", "铝矿": "bauxite", "氧化铝": "alumina",
    "废铜": "scrap", "废铝": "scrap", "再生": "recycle", "再生铅": "recycle_pb",
    "平衡": "balance", "汇率": "fx", "人民币": "cny", "美元": "usd",
    "硫酸": "h2so4", "电力": "power", "电费": "power_cost", "现金成本": "cash_cost",
    "完全成本": "total_cost", "订单": "order", "排产": "plan", "到港": "arrival",
    "提单": "bl", "发运": "shipment", "价格": "price", "均价": "avg_price",
    "价格指数": "price_idx", "估值": "valuation", "结构": "struct",
    "关税": "tariff", "产能": "capacity", "利用率": "util", "天数": "days",
    "增速": "yoy", "产量占比": "share",
}

FREQ_MAP = {"日": "daily", "周": "weekly", "月": "monthly", "季": "quarterly",
            "半年": "halfyear", "年": "yearly"}
FREQ_CN_MAP = {"半年": "halfyear", "季度": "quarterly", "月度": "monthly",
               "年度": "yearly", "周度": "weekly", "日度": "daily"}

def infer_freq(name, path):
    # 中文频率标记 (命中 name 或 path)
    s = name + " " + str(path)
    for kw, val in FREQ_CN_MAP.items():
        if kw in s:
            return val
    # 直接匹配 日/周/月/季/年 字
    for k, v in FREQ_MAP.items():
        if k in name:
            return v
    return "daily"

def is_good_match(q, h, code):
    """排除明显的误配: 指标名说X, 命中名却是无关节点/公司/国别切片"""
    if not h or not h.get("name"):
        return False
    hname = h["name"]
    # 指标名说"中国"但命中是国家切片(非中国) → 误配
    if "中国" in q and any(x in hname for x in ["美国", "澳大利亚", "秘鲁", "智利", "韩国", "巴林"]):
        return False
    # 指标名说"海外"但命中是中国切片 → 误配
    if "海外" in q and any(x in hname for x in ["中国", "国内", "上海", "无锡", "重庆", "安徽"]):
        return False
    # 指标名说"全球"但命中是单一国别/单一公司 → 误配
    if "全球" in q and not any(x in hname for x in ["全球", "世界", "合计"]):
        return False
    # 命中是公司/品牌级切片(紫金/山东/中国宏桥) 而指标名是宏观总量 → 误配
    macro_kw = ["总产量", "产量总量", "总消费", "总利润", "现金成本", "完全成本",
                "冶炼利润", "开工率", "产能利用率", "加工费", "TC", "社会库存", "库存", "进口量", "出口量"]
    company_kw = ["紫金", "山东", "宏桥", "神火", "云铝", "中国铝业", "南铝", "新疆众和",
                  "南山铝业", "明泰铝业", "立中集团", "索通", "中色股份", "中国宏桥"]
    if any(m in q for m in macro_kw) and any(c in hname for c in company_kw):
        return False
    return True

def slugify(name, code):
    n = re.sub(r"【[^】]*】", "", name).strip()
    # 去单位尾巴
    n = re.sub(r"（[^）]*）$", "", n).strip()
    n = re.sub(r"\([^)]*\)$", "", n).strip()
    parts = []
    # 先按关键词映射
    rest = n
    for cn, en in SLUG_MAP.items():
        if cn in rest:
            parts.append(en)
            rest = rest.replace(cn, " ")
    rest = rest.strip()
    rest = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]", "", rest)
    if len(parts) >= 1:
        return "_".join(parts[:3])[:28]
    return re.sub(r"[^a-z0-9]", "", n)[:24] or "idx"

def main():
    data = json.load(open(FINAL))
    doc = json.load(open(IND))
    ind = doc["indicators"]
    # 已注册的 知几id 集合 (用于去重)
    used_ids = set()
    for v in ind.values():
        for k, idv in (v.get("ids") or {}).items():
            if idv:
                used_ids.add(idv)

    new_entries = {}
    skipped = []
    counter = {}
    for code in ["CU", "AL"]:
        final = data.get(code, {})
        for q, v in final.items():
            if v["tier"] not in ("A", "B"):
                continue
            ch = v.get("chosen")
            if not ch or not ch.get("id"):
                skipped.append((code, q, "无 chosen"))
                continue
            zhiji_id = ch["id"]
            if zhiji_id in used_ids:
                skipped.append((code, q, "id已注册:%s" % zhiji_id))
                continue
            # 质量过滤: 排除明显的国家/公司切片误配
            if not is_good_match(q, ch, code):
                skipped.append((code, q, "误配过滤:%s" % ch["name"][:30]))
                continue
            nodes = v.get("nodes") or []
            node_short = nodes[0].replace(".", "") if nodes else "00"
            # 节点号缺失时用短码补 (如 2.1 → 21)
            if node_short == "00" and v.get("note"):
                m = re.search(r"节点([\d.]+)", v["note"])
                if m:
                    node_short = m.group(1).replace(".", "")
            slug = slugify(q, code)
            base_key = "%s_%s_%s" % (code.lower(), node_short, slug)
            key = base_key
            n = 1
            while key in ind:
                n += 1
                key = "%s_%d" % (base_key, n)
            counter[key] = 1
            freq = infer_freq(q, ch.get("path", ""))
            new_entries[key] = {
                "name": ch["name"],
                "unit": ch.get("unit") or "",
                "freq": freq,
                "verified": False,
                "ids": {code: zhiji_id},
                "_origin": "step3_%s_%s" % (code, q[:40]),
                "_tier": v["tier"],
                "_nodes": nodes,
            }

    ind.update(new_entries)
    doc["version"] = "2.8"
    doc["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc["change"] = "Step3 知几验证: 铜(CU) %d + 铝(AL) %d TierA/B 指标注册 (id去重跳过 %d)" % (
        sum(1 for k in new_entries if k.startswith("cu")),
        sum(1 for k in new_entries if k.startswith("al")),
        len(skipped))

    json.dump(doc, open(IND, "w"), ensure_ascii=False, indent=1)

    print("=== 注册结果 ===")
    print("新增指标: %d" % len(new_entries))
    print("  CU:", sum(1 for k in new_entries if k.startswith("cu")))
    print("  AL:", sum(1 for k in new_entries if k.startswith("al")))
    print("跳过(去重/无chosen):", len(skipped))
    print("注册后总指标数:", len(ind))
    print("跳过样例:")
    for code, q, why in skipped[:12]:
        print("  [%s] %s -> %s" % (code, q[:30], why))

if __name__ == "__main__":
    main()