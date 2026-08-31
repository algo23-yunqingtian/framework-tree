#!/usr/bin/env python3
"""Step3-5M: 五金属(ZN/NI/SN/SI/LI) Tier A 指标注册进 indicators_v1.json。

复用 step3_register.py 的 slugify/infer_freq/is_good_match 逻辑，三处适配：
1. 输入文件 = analysis/iwencai/step3_5metals_final.json (Tier A 判定真源)
2. 节点映射 = analysis/iwencai/step3_5metals_candidates.json 反查
   (final.json 的 _nodes 字段为空 [], 需从 candidates 注入)
3. 品种前缀 = zn/ni/sn/si/li (原 cu/al)

安全性：
- append-only: 只新增键, 零覆盖已注册指标
- 知几 id 去重: 已注册的 id 跳过, 避免重复灌库
- 误配过滤: 国家切片/公司切片 排除
- 写前备份: 备份 indicators_v1.json 到 analysis/backups/

命名: <code>_<节点短码>_<slug>  例: zn_21_close / ni_31_output
"""
import json, os, re, shutil
from datetime import datetime

REPO = "/home/ubuntu/framework-tree"
FINAL = os.path.join(REPO, "analysis/iwencai/step3_5metals_final.json")
CAND = os.path.join(REPO, "analysis/iwencai/step3_5metals_candidates.json")
IND = os.path.join(REPO, "data/indicators_v1.json")
BACKUP_DIR = os.path.join(REPO, "analysis/backups")

CODES = ["ZN", "NI", "SN", "SI", "LI"]

# 复用 step3_register.py 的 SLUG_MAP
SLUG_MAP = {
    "LME": "lme", "SHFE": "shfe", "COMEX": "comex", "CFTC": "cftc", "USGS": "usgs",
    "GFEX": "gfex",
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
    "锌精矿": "conc", "镍矿": "nickel_ore", "锡矿": "tin_ore",
    "废铜": "scrap", "废铝": "scrap", "再生": "recycle", "再生铅": "recycle_pb",
    "平衡": "balance", "汇率": "fx", "人民币": "cny", "美元": "usd",
    "硫酸": "h2so4", "电力": "power", "电费": "power_cost", "现金成本": "cash_cost",
    "完全成本": "total_cost", "订单": "order", "排产": "plan", "到港": "arrival",
    "提单": "bl", "发运": "shipment", "价格": "price", "均价": "avg_price",
    "价格指数": "price_idx", "估值": "valuation", "结构": "struct",
    "关税": "tariff", "产能": "capacity", "利用率": "util", "天数": "days",
    "增速": "yoy", "产量占比": "share", "冰镍": "nickel_powder",
    "碳酸锂": "carbonate", "电池级": "battery", "工业级": "industrial",
    "工业硅": "industrial_si", "多晶硅": "polysilicon", "有机硅": "organosilicon",
}
FREQ_MAP = {"日": "daily", "周": "weekly", "月": "monthly", "季": "quarterly",
            "半年": "halfyear", "年": "yearly"}
FREQ_CN_MAP = {"半年": "halfyear", "季度": "quarterly", "月度": "monthly",
               "年度": "yearly", "周度": "weekly", "日度": "daily"}

CN = {"ZN": "锌", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}


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
    """排除明显的误配: 指标名说X, 命中名却是无关节点/公司/国别切片"""
    if not h or not h.get("name"):
        return False
    hname = h["name"]
    if "中国" in q and any(x in hname for x in ["美国", "澳大利亚", "秘鲁", "智利", "韩国", "巴林"]):
        return False
    if "海外" in q and any(x in hname for x in ["中国", "国内", "上海", "无锡", "重庆", "安徽"]):
        return False
    if "全球" in q and not any(x in hname for x in ["全球", "世界", "合计"]):
        return False
    macro_kw = ["总产量", "产量总量", "总消费", "总利润", "现金成本", "完全成本",
                "冶炼利润", "开工率", "产能利用率", "加工费", "TC", "社会库存",
                "库存", "进口量", "出口量"]
    company_kw = ["紫金", "山东", "宏桥", "神火", "云铝", "中国铝业", "南铝",
                  "新疆众和", "南山铝业", "明泰铝业", "立中集团", "索通",
                  "中色股份", "中国宏桥"]
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


def build_node_index(code):
    """从 candidates.json 构建 指标名 -> [节点号] 反查索引。
    CAND 是文件路径字符串, 需 json.load 后使用。"""
    cand = json.load(open(CAND, encoding="utf-8"))
    nodes_by_q = {}
    for nc, names in cand.get(code, {}).items():
        for nm in names:
            nodes_by_q.setdefault(nm, []).append(nc)
    return nodes_by_q


def main():
    data = json.load(open(FINAL, encoding="utf-8"))
    doc = json.load(open(IND, encoding="utf-8"))
    ind = doc["indicators"]

    # 写前备份
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    backup = os.path.join(BACKUP_DIR, "indicators_v1_before_5m_%s.json" % ts)
    shutil.copy(IND, backup)

    # 已注册的 知几id 集合 (去重)
    used_ids = set()
    for v in ind.values():
        for k, idv in (v.get("ids") or {}).items():
            if idv:
                used_ids.add(idv)

    new_entries = {}
    skipped = []
    per_code = {}
    for code in CODES:
        node_idx = build_node_index(code)
        n = 0
        for q, v in data.get(code, {}).items():
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
            # 节点反查注入 (final.json 的 nodes 为空)
            nodes = node_idx.get(q, [])
            node_short = nodes[0].replace(".", "") if nodes else "00"
            slug = slugify(q, code)
            base_key = "%s_%s_%s" % (code.lower(), node_short, slug)
            # 去重: 同时查原文件 ind 和本次新增 new_entries (防 slug 冲突覆盖)
            key = base_key
            k = 1
            while key in ind or key in new_entries:
                k += 1
                key = "%s_%d" % (base_key, k)
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
            n += 1
        per_code[code] = n

    # append-only 合并
    ind.update(new_entries)
    doc["version"] = "3.43"
    doc["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc["change"] = "Step3 五金属 TierA 指标注册: ZN %d + NI %d + SN %d + SI %d + LI %d (id去重跳过 %d)" % (
        per_code["ZN"], per_code["NI"], per_code["SN"], per_code["SI"], per_code["LI"],
        len(skipped))
    # 同步 _meta.version (若有)
    if "_meta" in doc and isinstance(doc["_meta"], dict):
        doc["_meta"]["version"] = "3.43"
    json.dump(doc, open(IND, "w"), ensure_ascii=False, indent=1)

    print("=== 五金属 Step3 注册结果 ===")
    print("新增指标: %d" % len(new_entries))
    for c in CODES:
        print("  %s(%s): %d" % (c, CN[c], per_code[c]))
    print("跳过(去重/误配):", len(skipped))
    print("  id去重:", sum(1 for x in skipped if "id已注册" in x[2]))
    print("  误配过滤:", sum(1 for x in skipped if "误配" in x[2]))
    print("  无chosen:", sum(1 for x in skipped if "无 chosen" in x[2]))
    print("注册后总指标数:", len(ind))
    print("备份:", backup)
    print("\n跳过样例(前10):")
    for code, q, why in skipped[:10]:
        print("  [%s] %s -> %s" % (code, q[:28], why))


if __name__ == "__main__":
    main()
