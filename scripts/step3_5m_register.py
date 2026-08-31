#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""五金属 Step3 Tier A 指标注册进 indicators_v1.json。

输入: analysis/iwencai/step3_5metals_final.json (Tier A 621条)
输出: data/indicators_v1.json (追加 zn_*/ni_*/si_*/sn_*/li_* 条目)

命名: <code>_<节点短码>_<slug>
去重: 若该 知几id 已注册 → 跳过
过滤: 排除明显误配(国家切片/公司切片/口径错位)
"""
import json, os, re, sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FINAL = REPO / "analysis" / "iwencai" / "step3_5metals_final.json"
IND = REPO / "data" / "indicators_v1.json"

CODES = ["ZN", "NI", "SI", "SN", "LI"]

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
    "精矿": "conc", "废": "scrap", "再生": "recycle",
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

CN_VAR = {"ZN": "锌", "NI": "镍", "SI": "硅", "SN": "锡", "LI": "锂"}
VARIETY_WORDS = {
    "ZN": ["锌", "Zn", "Zinc"],
    "NI": ["镍", "Ni", "Nickel"],
    "SI": ["硅", "Si", "Silicon", "工业硅"],
    "SN": ["锡", "Sn", "Tin"],
    "LI": ["锂", "Li", "Lithium", "碳酸锂"],
}


def infer_freq(name, path):
    s = name + " " + str(path)
    for kw, val in FREQ_CN_MAP.items():
        if kw in s:
            return val
    for k, v in FREQ_MAP.items():
        if k in name:
            return v
    return "daily"


def is_good_match(q, h, code):
    """排除明显的误配。品种词检查在命中名(hname)而非query名，因为query可能不含品种词。"""
    if not h or not h.get("name"):
        return False
    hname = h["name"]
    # 品种词必须在命中名中（而非query名）
    vw = VARIETY_WORDS.get(code, [])
    if not any(w in hname for w in vw):
        return False
    # 国家口径
    if "中国" in q and any(x in hname for x in ["美国", "澳大利亚", "秘鲁", "智利", "韩国", "巴林"]):
        return False
    if "海外" in q and any(x in hname for x in ["中国", "国内", "上海", "无锡", "重庆", "安徽"]):
        return False
    if "全球" in q and not any(x in hname for x in ["全球", "世界", "合计"]):
        return False
    # 公司切片
    macro_kw = ["总产量", "产量总量", "总消费", "总利润", "现金成本", "完全成本",
                "冶炼利润", "开工率", "产能利用率", "加工费", "TC", "社会库存", "库存", "进口量", "出口量"]
    company_kw = ["紫金", "山东", "宏桥", "神火", "云铝", "中国铝业", "南铝", "新疆众和",
                  "南山铝业", "明泰铝业", "立中集团", "索通", "中色股份", "中国宏桥",
                  "嘉能可", "托克", "麦克希", "五矿", "江铜", "铜陵"]
    if any(m in q for m in macro_kw) and any(c in hname for c in company_kw):
        return False
    return True


def slugify(name, code):
    n = re.sub(r"【[^】]*】", "", name).strip()
    n = re.sub(r"（[^）]*）$", "", n).strip()
    n = re.sub(r"\([^)]*\)$", "", n).strip()
    parts = []
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
    data = json.load(open(FINAL, encoding="utf-8"))
    doc = json.load(open(IND, encoding="utf-8"))
    ind = doc["indicators"]

    used_ids = set()
    for v in ind.values():
        for k, idv in (v.get("ids") or {}).items():
            if idv:
                used_ids.add(idv)

    new_entries = {}
    skipped = []

    for code in CODES:
        final = data.get(code, {})
        for q, v in final.items():
            if v.get("tier") != "A":
                continue
            ch = v.get("chosen")
            if not ch or not ch.get("id"):
                skipped.append((code, q, "无 chosen"))
                continue
            zhiji_id = ch["id"]
            if zhiji_id in used_ids:
                skipped.append((code, q, "id已注册:%s" % zhiji_id))
                continue
            if not is_good_match(q, ch, code):
                skipped.append((code, q, "误配过滤:%s" % ch["name"][:30]))
                continue
            nodes = v.get("nodes") or []
            node_short = nodes[0].replace(".", "") if nodes else "00"
            slug = slugify(q, code)
            base_key = "%s_%s_%s" % (code.lower(), node_short, slug)
            key = base_key
            n = 1
            while key in ind:
                n += 1
                key = "%s_%d" % (base_key, n)
            freq = infer_freq(q, ch.get("path", ""))
            new_entries[key] = {
                "name": ch["name"],
                "unit": ch.get("unit") or "",
                "freq": freq,
                "verified": False,
                "ids": {code: zhiji_id},
                "_origin": "step3_5m_%s_%s" % (code, q[:40]),
                "_tier": "A",
                "_nodes": nodes,
            }

    ind.update(new_entries)
    doc["version"] = "3.43"
    doc["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    counts = {c: sum(1 for k in new_entries if k.startswith(c.lower())) for c in CODES}
    doc["change"] = "Step3 五金属知几验证: %s TierA 指标注册 (%d条, id去重/误配过滤跳过 %d)" % (
        " + ".join(f"{c} {counts[c]}" for c in CODES),
        len(new_entries), len(skipped))

    json.dump(doc, open(IND, "w"), ensure_ascii=False, indent=1)

    print("=== 五金属 Step3 注册结果 ===")
    print(f"新增指标: {len(new_entries)}")
    for c in CODES:
        print(f"  {c}: {counts[c]}")
    print(f"跳过(去重/无chosen/误配): {len(skipped)}")
    print(f"注册后总指标数: {len(ind)}")
    print(f"\n跳过样例:")
    for code, q, why in skipped[:15]:
        print(f"  [{code}] {q[:30]} -> {why}")


if __name__ == "__main__":
    main()