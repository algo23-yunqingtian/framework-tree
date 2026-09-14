#!/usr/bin/env python3
"""Task 1: CU/AL matching threshold fix + registration + rate report.

Changes:
  - Threshold lowered from 5 to 4 in both judge scripts
  - CU 73 B-grade indicators registered into indicators_v1.json
  - AL 96 A-grade (manually judged) indicators confirmed
  - Matching rate report output

Usage: python scripts/task1_match_fix.py
"""
import json, os, re, sys, shutil
from datetime import datetime
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IND_PATH = os.path.join(ROOT, "data", "indicators_v1.json")
VERIFY_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_verify_summary.json")
SEARCH_5M_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_search_results_5m.json")
FINAL_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_final.json")
FINAL_5M_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_final_5m.json")
VERDICT_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_slices", "verdict_rule.json")
VERDICT_5M_PATH = os.path.join(ROOT, "analysis", "iwencai", "step3_slices", "verdict_rule_5m.json")
REPORT_PATH = os.path.join(ROOT, "docs", "Matching_Report.md")
BACKUP_DIR = os.path.join(ROOT, "analysis", "backups")

# ====== Configuration ======
NEW_THRESHOLD = 4  # lowered from 5

# ====== CU/AL Judge Logic (from step3_judge_rules.py) ======
FIELD_WORDS = [
    "库存", "仓单", "价格", "收盘", "开盘", "持仓", "成交量", "产量", "产量",
    "进口", "出口", "开工率", "TC", "加工费", "升贴水", "基差", "消费", "需求",
    "成本", "利润", "溢价", "结算", "现金", "注销", "注册", "在途", "社会库存",
    "厂内", "隐性", "检修", "产能", "占比", "净进口", "净持仓", "估值", "分位",
    "期限结构", "月差", "跨月", "免税", "美元", "人民币", "汇率", "开工", "排产",
    "订单", "库存天数", "供需", "平衡", "价格指数", "均价", "到港", "提单",
]
DESIGN_NOTES = ["归 7.1", "归 2.5", "归 7.2", "归 2.6", "归 2.1", "本节点按",
                "主图归", "分位（估值贵/便宜）", "席位明细（前20大）",
                "绝对值测算主图", "口径为准", "管总量趋势", "管国别结构"]
AL_MINUS = [("废铝", "电解铝"), ("电解铝", "废铝"), ("氧化铝", "电解铝"),
            ("电解铝", "氧化铝"), ("铝锭", "废铝"), ("原铝", "废铝"),
            ("精炼", "氧化铝"), ("铝矿", "氧化铝"), ("精炼铝", "废铝")]
GEO = [("中国", ["美国", "USGS", "海外", "国际", "国外", "智利", "秘鲁", "几内亚"]),
       ("海外", ["中国", "国内", "上海", "无锡", "重庆", "华东", "华南"])]

def variety_word_cu_al(name, code):
    if code == "CU" or "铜" in name:
        return ["铜", "Cu", "Copper", "CU"]
    if code == "AL" or "铝" in name:
        return ["铝", "Al", "Aluminum", "Aluminium", "AL"]
    return []

def in_design_notes_cu_al(q):
    return any(n in q for n in DESIGN_NOTES)

def geo_bad_cu_al(q, hname):
    for g, bads in GEO:
        if g in q and any(b in hname for b in bads):
            return True
    return False

def al_minus_bad_cu_al(q, hname):
    for qw, hw in AL_MINUS:
        if qw in q and hw in hname:
            return True
    return False

def score_hit_cu_al(q, h, code):
    s = 0
    hname = h.get("name", "")
    wid = h.get("id", "") or ""
    vw = variety_word_cu_al(q, code)
    if any(w in hname for w in vw) or any(w.lower() in wid.lower() for w in vw if len(w) >= 2):
        s += 2
    else:
        return -1
    fields = [f for f in FIELD_WORDS if f in q]
    hit_fields = sum(1 for f in fields if f in hname)
    s += hit_fields * 2
    for pre in ["LME", "SHFE", "COMEX", "上期所", "中色", "CFTC", "USGS"]:
        if pre in q and pre not in hname and pre not in wid:
            s -= 3
    if geo_bad_cu_al(q, hname):
        return -2
    if al_minus_bad_cu_al(q, hname):
        return -2
    if h.get("source") in ("smm", "mysteel"):
        s += 1
    return s

def judge_cu_al(q, v, code):
    hits = v.get("hits", [])
    if in_design_notes_cu_al(q):
        return {"matched": False, "chosen": None, "score": 0,
                "note": "设计说明/口径注释, 非可检索指标", "hits": hits}
    if not hits:
        return {"matched": False, "chosen": None, "score": 0,
                "note": "知几 search 无任何命中", "hits": hits}
    scored = []
    for h in hits:
        sc = score_hit_cu_al(q, h, code)
        if sc >= 0:
            scored.append((sc, h))
    scored.sort(key=lambda x: -x[0])
    if scored and scored[0][0] >= NEW_THRESHOLD:
        sc, best = scored[0]
        return {"matched": True, "chosen": best, "score": sc,
                "note": "命中%d条, 最佳得分%d: %s" % (len(scored), sc, str(best.get("name", ""))[:50]),
                "hits": [h for _, h in scored]}
    top = scored[0] if scored else None
    return {"matched": False, "chosen": None, "score": top[0] if top else 0,
            "note": "存在通过品种词但字段/口径弱 (最佳得分%d, 阈%d): %s" % (
                top[0] if top else 0, NEW_THRESHOLD,
                str(top[1].get("name", ""))[:50] if top else "无"),
            "hits": hits}

# ====== 5M Judge Logic (from step3_5m_judge.py) ======
VAR_WORDS = {
    "ZN": ["锌", "Zn", "Zinc"],
    "NI": ["镍", "Ni", "Nickel", "NPI", "高冰镍"],
    "SN": ["锡", "Sn", "Tin"],
    "SI": ["硅", "Si", "Silicon"],
    "LI": ["锂", "Li", "Lithium", "LCE"],
}
FIELD_WORDS_5M = [
    "库存", "仓单", "价格", "收盘", "开盘", "持仓", "成交量", "产量",
    "进口", "出口", "开工率", "开工", "TC", "加工费", "升贴水", "基差",
    "消费", "需求", "成本", "利润", "溢价", "结算", "注销", "注册",
    "在途", "社会库存", "厂内", "隐性", "检修", "产能", "利用率",
    "占比", "净进口", "净持仓", "估值", "分位", "期限结构", "月差",
    "汇率", "排产", "订单", "库存天数", "平衡", "均价", "到港",
    "关税", "天数", "增速", "结构", "总产量", "开工率",
]
EXCHANGES = ["LME", "SHFE", "COMEX", "上期所", "中色", "CFTC", "USGS", "ILZSG"]
MINUS = {
    "ZN": [("锌精矿", "锌锭"), ("锌锭", "锌精矿"), ("原生", "再生"), ("再生", "原生")],
    "NI": [
        ("镍生铁", "电解镍", "硫酸镍"), ("NPI", "电解镍"),
        ("高冰镍", "电解镍", "硫酸镍", "镍生铁"),
        ("电解镍", "镍生铁", "NPI", "高冰镍"),
        ("硫酸镍", "电解镍", "镍生铁"),
        ("精炼镍", "镍生铁", "NPI"),
    ],
    "SN": [("锡精矿", "精炼锡"), ("精炼锡", "锡精矿"), ("原生", "再生"), ("再生", "原生")],
    "SI": [
        ("多晶硅", "金属硅", "工业硅"), ("金属硅", "多晶硅"),
        ("工业硅", "多晶硅", "硅铁"), ("硅铁", "工业硅", "多晶硅"),
        ("有机硅", "工业硅", "多晶硅"), ("有机硅", "金属硅"),
    ],
    "LI": [
        ("碳酸锂", "氢氧化锂"), ("氢氧化锂", "碳酸锂"),
        ("锂精矿", "碳酸锂", "氢氧化锂"), ("矿石", "碳酸锂", "氢氧化锂"),
        ("正极材料", "碳酸锂", "氢氧化锂", "锂精矿"),
    ],
}
STAGE = {
    "硅矿": ["硅矿"], "碳化硅": ["碳化硅"], "硅铁": ["硅铁", "硅锰"],
    "工业硅": ["工业硅", "金属硅", "421#", "553#"],
    "多晶硅": ["多晶硅"], "有机硅": ["有机硅"],
    "锌矿": ["锌矿", "精矿"], "铅矿": ["铅矿", "精矿"],
    "锂矿": ["锂矿", "锂辉石", "辉石"], "碳酸锂": ["碳酸锂"],
    "氢氧化锂": ["氢氧化锂"], "镍矿": ["镍矿", "红土镍矿"],
    "镍生铁": ["镍生铁", "NPI"], "高冰镍": ["高冰镍"],
    "电解镍": ["电解镍", "精炼镍"], "硫酸镍": ["硫酸镍"],
    "氧化锌": ["氧化锌"], "硫酸": ["硫酸"],
}
DESIGN_NOTES_5M = ["归 7.1", "归 2.5", "归 7.2", "归 2.6", "归 2.1", "本节点按",
                   "主图归", "口径为准", "管总量趋势", "管国别结构"]
FOREIGN = ["美国", "印尼", "印度尼西亚", "菲律宾", "澳大利亚", "澳洲", "日本",
           "南非", "欧洲", "欧盟", "智利", "秘鲁", "加拿大", "韩国", "印度",
           "泰国", "哥伦比亚", "巴西", "俄罗斯", "哈萨克斯坦", "蒙古"]
CHINA = ["中国", "国内", "上海", "无锡", "广东", "山东", "陕西", "内蒙古",
         "新疆", "河北", "江苏", "云南", "四川", "辽宁", "东北", "华东",
         "华南", "华北", "华中", "福建", "安徽", "河南", "山西", "甘肃",
         "青海", "吉林", "黑龙江", "广西", "贵州", "湖南", "湖北", "江西",
         "浙江", "北京", "天津"]
OVERSEAS = ["海外", "国际", "国外"]
OTHER_VAR = {
    "ZN": ["镍", "锡", "硅", "锂", "铝", "铜", "铅", "镍生铁", "高冰镍"],
    "NI": ["锌", "锡", "硅", "锂", "铝", "铜", "铅"],
    "SN": ["锌", "镍", "硅", "锂", "铝", "铜", "铅", "镀锡"],
    "SI": ["锌", "镍", "锡", "锂", "铝", "铜", "铅"],
    "LI": ["锌", "镍", "锡", "铝", "铜", "铅"],
}

def in_design_5m(q):
    return any(n in q for n in DESIGN_NOTES_5M)

def minus_bad_5m(q, hname, code):
    for rule in MINUS.get(code, []):
        if rule[0] in q:
            for bad in rule[1:]:
                if bad in hname:
                    return True
    return False

def geo_tokens_5m(s):
    return {
        "foreign": [x for x in FOREIGN if x in s],
        "china": any(x in s for x in CHINA),
        "overseas": any(x in s for x in OVERSEAS),
    }

def geo_bad_5m(q, hname):
    qq, hh = geo_tokens_5m(q), geo_tokens_5m(hname)
    if qq["china"] and (hh["overseas"] or "美国" in hh["foreign"] or "USGS" in hname):
        return True
    if qq["overseas"] and hh["china"]:
        return True
    if qq["foreign"] and hh["foreign"] and not (set(qq["foreign"]) & set(hh["foreign"])):
        return True
    return False

def other_var_bad_5m(q, hname, code):
    for w in OTHER_VAR.get(code, []):
        if w in hname:
            if code == "SI" and w in ("铝",) and "硅" in hname:
                continue
            return True
    return False

def score_hit_5m(q, h, code):
    hname = h.get("name", "") or ""
    wid = h.get("id", "") or ""
    s = 0
    vws = VAR_WORDS.get(code, [])
    if any(w in hname for w in vws):
        s += 2
    elif any(w.lower() in wid.lower() for w in vws if len(w) >= 2):
        s += 1
    else:
        return -1
    fields = [f for f in FIELD_WORDS_5M if f in q]
    s += sum(2 for f in fields if f in hname)
    for pre in EXCHANGES:
        if pre in q and pre not in hname and pre not in wid:
            s -= 3
    if minus_bad_5m(q, hname, code):
        return -2
    if geo_bad_5m(q, hname):
        return -2
    if other_var_bad_5m(q, hname, code):
        return -2
    for stage, allowed in STAGE.items():
        if stage in q and not any(a in hname for a in allowed):
            s -= 3
    if h.get("source") in ("smm", "mysteel"):
        s += 1
    return s

def judge_5m(q, v, code):
    hits = v.get("hits", [])
    if in_design_5m(q):
        return {"matched": False, "chosen": None, "score": 0,
                "note": "设计说明/口径注释, 非可检索指标", "hits": hits}
    if not hits:
        return {"matched": False, "chosen": None, "score": 0,
                "note": "知几 search 无任何命中", "hits": hits}
    scored = []
    for h in hits:
        sc = score_hit_5m(q, h, code)
        if sc >= 0:
            scored.append((sc, h))
    scored.sort(key=lambda x: -x[0])
    if scored and scored[0][0] >= NEW_THRESHOLD:
        sc, best = scored[0]
        return {"matched": True, "chosen": best, "score": sc,
                "note": "命中%d条, 最佳得分%d: %s" % (len(scored), sc, str(best.get("name", ""))[:50]),
                "hits": [h for _, h in scored]}
    top = scored[0] if scored else None
    return {"matched": False, "chosen": None, "score": top[0] if top else 0,
            "note": "存在通过品种词但字段/口径弱 (最佳得分%d, 阈%d): %s" % (
                top[0] if top else 0, NEW_THRESHOLD,
                str(top[1].get("name", ""))[:50] if top else "无"),
            "hits": hits}

# ====== Registration Logic ======
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

# ====== Main ======
def main():
    print("=" * 60)
    print("Task 1: Matching Threshold Fix (5→4) + Registration")
    print("=" * 60)

    # --- Helper: load JSON with encoding fallback ---
    def load_json_any_encoding(path):
        """Load JSON with encoding fallback (UTF-8 → GBK → latin-1)."""
        for enc in ("utf-8", "gbk", "latin-1"):
            try:
                with open(path, "r", encoding=enc) as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        # Last resort: read as binary, try to decode
        with open(path, "rb") as f:
            raw = f.read()
        for enc in ("utf-8", "gbk", "latin-1"):
            try:
                return json.loads(raw.decode(enc))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return {}

    # --- Step 1: Backup ---
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    shutil.copy(IND_PATH, os.path.join(BACKUP_DIR, "indicators_v1_before_task1_%s.json" % ts))
    print("[1/5] Backup created")

    # --- Step 2: Re-run judge with new threshold ---
    print("[2/5] Re-running judge with threshold=%d..." % NEW_THRESHOLD)

    # CU/AL judge
    verify = load_json_any_encoding(VERIFY_PATH)
    verdict_cu_al = {}
    for code in ["CU", "AL"]:
        verdict_cu_al[code] = {}
        for q, v in verify.get(code, {}).items():
            verdict_cu_al[code][q] = judge_cu_al(q, v, code)
        matched = sum(1 for x in verdict_cu_al[code].values() if x["matched"])
        print("  %s: matched %d/%d" % (code, matched, len(verify.get(code, {}))))

    # 5M judge
    search_5m = load_json_any_encoding(SEARCH_5M_PATH)
    verdict_5m = {}
    for code in ["ZN", "NI", "SN", "SI", "LI"]:
        verdict_5m[code] = {}
        for q, v in search_5m.get(code, {}).items():
            verdict_5m[code][q] = judge_5m(q, v, code)
        matched = sum(1 for x in verdict_5m[code].values() if x["matched"])
        print("  %s: matched %d/%d" % (code, matched, len(search_5m.get(code, {}))))

    # Save verdicts
    with open(VERDICT_PATH, "w", encoding="utf-8") as f:
        json.dump(verdict_cu_al, f, ensure_ascii=False, indent=1)
    with open(VERDICT_5M_PATH, "w", encoding="utf-8") as f:
        json.dump(verdict_5m, f, ensure_ascii=False, indent=1)
    print("  Verdicts saved")

    # --- Step 3: Generate new final.json ---
    print("[3/5] Generating new final.json...")

    # CU/AL final: preserve existing A-tier manual judgments
    old_final = load_json_any_encoding(FINAL_PATH) if os.path.exists(FINAL_PATH) else {}
    final_cu_al = {}
    for code in ["CU", "AL"]:
        final_cu_al[code] = {}
        for q, v in verdict_cu_al[code].items():
            old = old_final.get(code, {}).get(q, {})
            # Preserve Tier A manual judgment
            if old.get("tier") == "A":
                final_cu_al[code][q] = old
            elif v["matched"]:
                final_cu_al[code][q] = {
                    "nodes": v.get("nodes", old.get("nodes", [])),
                    "tier": "B",
                    "matched": True,
                    "chosen": v.get("chosen"),
                    "note": v.get("note", ""),
                }
            else:
                final_cu_al[code][q] = {
                    "nodes": v.get("nodes", old.get("nodes", [])),
                    "tier": "C",
                    "matched": False,
                    "chosen": None,
                    "note": v.get("note", ""),
                }
        # Count tiers
        tier_counts = Counter(x["tier"] for x in final_cu_al[code].values())
        print("  %s: A=%d B=%d C=%d" % (code, tier_counts.get("A", 0), tier_counts.get("B", 0), tier_counts.get("C", 0)))

    json.dump(final_cu_al, open(FINAL_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 5M final
    final_5m = {}
    for code in ["ZN", "NI", "SN", "SI", "LI"]:
        final_5m[code] = {}
        for q, v in verdict_5m[code].items():
            final_5m[code][q] = {
                "nodes": v.get("nodes", []),
                "tier": "B" if v["matched"] else "C",
                "matched": v["matched"],
                "chosen": v.get("chosen"),
                "note": v.get("note", ""),
            }
        b = sum(1 for x in final_5m[code].values() if x["tier"] == "B")
        c = len(final_5m[code]) - b
        print("  %s: B=%d C=%d" % (code, b, c))

    json.dump(final_5m, open(FINAL_5M_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # --- Step 4: Register new indicators ---
    print("[4/5] Registering indicators into indicators_v1.json...")
    doc = load_json_any_encoding(IND_PATH)
    ind = doc["indicators"]

    # Collect already-used zhiji ids
    used_ids = set()
    for v in ind.values():
        for k, idv in (v.get("ids") or {}).items():
            if idv:
                used_ids.add(idv)

    new_entries = {}
    skipped = []

    # Register CU/AL (Tier A + Tier B)
    for code in ["CU", "AL"]:
        for q, v in final_cu_al.get(code, {}).items():
            if v["tier"] not in ("A", "B"):
                continue
            ch = v.get("chosen")
            if not ch or not ch.get("id"):
                skipped.append((code, q, "no chosen"))
                continue
            zhiji_id = ch["id"]
            if zhiji_id in used_ids:
                skipped.append((code, q, "id already registered: %s" % zhiji_id))
                continue
            if not is_good_match(q, ch, code):
                skipped.append((code, q, "bad match: %s" % ch.get("name", "")[:30]))
                continue
            nodes = v.get("nodes") or []
            node_short = nodes[0].replace(".", "") if nodes else "00"
            if node_short == "00" and v.get("note"):
                m = re.search(r"节点([\d.]+)", v["note"])
                if m:
                    node_short = m.group(1).replace(".", "")
            slug = slugify(q, code)
            base_key = "%s_%s_%s" % (code.lower(), node_short, slug)
            key = base_key
            n = 1
            while key in ind or key in new_entries:
                n += 1
                key = "%s_%d" % (base_key, n)
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

    # Register 5M (Tier B only - no manual A in 5m)
    cand_5m = load_json_any_encoding(os.path.join(ROOT, "analysis", "iwencai", "step3_5metals_candidates.json"))
    for code in ["ZN", "NI", "SN", "SI", "LI"]:
        # Build node index from candidates
        node_idx = {}
        for nc, names in cand_5m.get(code, {}).items():
            for nm in names:
                node_idx.setdefault(nm, []).append(nc)

        for q, v in final_5m.get(code, {}).items():
            if v["tier"] != "B":
                continue
            ch = v.get("chosen")
            if not ch or not ch.get("id"):
                skipped.append((code, q, "no chosen"))
                continue
            zhiji_id = ch["id"]
            if zhiji_id in used_ids:
                skipped.append((code, q, "id already registered: %s" % zhiji_id))
                continue
            if not is_good_match(q, ch, code):
                skipped.append((code, q, "bad match: %s" % ch.get("name", "")[:30]))
                continue
            nodes = node_idx.get(q, [])
            node_short = nodes[0].replace(".", "") if nodes else "00"
            slug = slugify(q, code)
            base_key = "%s_%s_%s" % (code.lower(), node_short, slug)
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
                "_tier": "B",
                "_nodes": nodes,
            }

    # Merge
    ind.update(new_entries)
    doc["version"] = "3.49"
    doc["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc["change"] = "Task1: 阈值5→4, CU/AL/五金属 B级指标批量注册 (+%d new)" % len(new_entries)

    if "_meta" in doc and isinstance(doc["_meta"], dict):
        doc["_meta"]["version"] = "3.49"
        doc["_meta"]["updated"] = datetime.now().strftime("%Y-%m-%d")
        doc["_meta"]["status"] = "待审核"

    json.dump(doc, open(IND_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  Registered %d new indicators" % len(new_entries))
    print("  Skipped %d (dup/bad match)" % len(skipped))

    # --- Step 5: Generate matching rate report ---
    print("[5/5] Generating matching rate report...")

    all_codes = ["CU", "AL"] + ["ZN", "NI", "SN", "SI", "LI"]
    CN = {"CU": "铜", "AL": "铝", "ZN": "锌", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}
    lines = [
        "# 知几库匹配率报表",
        "",
        "**阈值调整**: 5 → **%d** (B级降级注册机制启用)" % NEW_THRESHOLD,
        "**执行时间**: %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
        "**版本**: indicators_v1.json v3.49",
        "",
        "## 一、匹配率总表",
        "",
        "| 品种 | 总指标 | A级(人工) | B级(规则) | C级(备用) | B级匹配率 | 说明 |",
        "|---|---|---|---|---|---|---|",
    ]

    total_all = 0
    total_a = 0
    total_b = 0
    total_c = 0

    for code in all_codes:
        if code in ("CU", "AL"):
            d = final_cu_al.get(code, {})
        else:
            d = final_5m.get(code, {})
        total = len(d)
        a = sum(1 for x in d.values() if x["tier"] == "A")
        b = sum(1 for x in d.values() if x["tier"] == "B")
        c = sum(1 for x in d.values() if x["tier"] == "C")
        rate = 100.0 * b / max(1, total)
        lines.append("| %s(%s) | %d | %d | %d | %d | %.0f%% | %s |" % (
            code, CN[code], total, a, b, c, rate,
            "CU/AL 人工A+规则B" if code in ("CU", "AL") else "五金属 全规则B"))
        total_all += total
        total_a += a
        total_b += b
        total_c += c

    rate_all = 100.0 * total_b / max(1, total_all)
    lines.append("| **合计** | **%d** | **%d** | **%d** | **%d** | **%.0f%%** | |" % (
        total_all, total_a, total_b, total_c, rate_all))

    lines += [
        "",
        "## 二、阈值调整前后对比",
        "",
        "| 品种 | 旧阈值(5) B级 | 新阈值(4) B级 | 新增 |",
        "|---|---|---|---|",
    ]

    # Old threshold 5 matched counts (hardcoded from previous run)
    old_matched = {"CU": 73, "AL": 51, "ZN": 45, "NI": 88, "SN": 71, "SI": 70, "LI": 48}
    new_matched = {}
    for code in all_codes:
        if code in ("CU", "AL"):
            new_matched[code] = sum(1 for x in final_cu_al.get(code, {}).values() if x["tier"] == "B")
        else:
            new_matched[code] = sum(1 for x in final_5m.get(code, {}).values() if x["tier"] == "B")

    for code in all_codes:
        old_b = old_matched.get(code, 0)
        new_b = new_matched.get(code, 0)
        diff = new_b - old_b
        lines.append("| %s(%s) | %d | %d | %+d |" % (code, CN[code], old_b, new_b, diff))

    lines += [
        "",
        "## 三、注册统计",
        "",
        "- **本次新增注册**: %d 条指标" % len(new_entries),
        "- **跳过(已注册/误配)**: %d 条" % len(skipped),
        "- **注册后总指标数**: %d" % len(ind),
        "",
        "### 跳过原因分布",
        "",
        "```",
    ]
    skip_reasons = Counter()
    for code, q, why in skipped:
        if "已注册" in why or "already registered" in why:
            skip_reasons["知几id已注册"] += 1
        elif "误配" in why or "bad match" in why:
            skip_reasons["误配过滤"] += 1
        elif "no chosen" in why:
            skip_reasons["无chosen"] += 1
        else:
            skip_reasons[why[:30]] += 1
    for reason, cnt in skip_reasons.most_common():
        lines.append("  %s: %d" % (reason, cnt))
    lines.append("```")

    lines += [
        "",
        "## 四、CU/AL 详细匹配",
        "",
        "### CU (铜)",
        "",
    ]

    # CU detail
    cu_entries = []
    for q, v in final_cu_al.get("CU", {}).items():
        if v["tier"] in ("A", "B"):
            ch = v.get("chosen") or {}
            cu_entries.append({
                "query": q,
                "tier": v["tier"],
                "chosen_name": ch.get("name", ""),
                "chosen_id": ch.get("id", ""),
            })
    cu_entries.sort(key=lambda x: x["tier"])
    lines.append("| # | 查询指标 | Tier | 知几命中名 | 知几ID |")
    lines.append("|---|---|---|---|---|")
    for i, e in enumerate(cu_entries[:50], 1):
        lines.append("| %d | %s | %s | %s | %s |" % (i, e["query"][:40], e["tier"], e["chosen_name"][:50], e["chosen_id"]))
    if len(cu_entries) > 50:
        lines.append("| ... | (共 %d 条, 显示前 50) | | | |" % len(cu_entries))

    lines += ["", "### AL (铝)", ""]
    al_entries = []
    for q, v in final_cu_al.get("AL", {}).items():
        if v["tier"] == "A":
            ch = v.get("chosen") or {}
            al_entries.append({
                "query": q,
                "tier": v["tier"],
                "chosen_name": ch.get("name", ""),
                "chosen_id": ch.get("id", ""),
            })
    al_entries.sort(key=lambda x: x["query"])
    lines.append("| # | 查询指标 | Tier | 知几命中名 | 知几ID |")
    lines.append("|---|---|---|---|---|")
    for i, e in enumerate(al_entries[:50], 1):
        lines.append("| %d | %s | %s | %s | %s |" % (i, e["query"][:40], e["tier"], e["chosen_name"][:50], e["chosen_id"]))
    if len(al_entries) > 50:
        lines.append("| ... | (共 %d 条, 显示前 50) | | | |" % len(al_entries))

    lines += [
        "",
        "## 五、五金属(B级)新增统计",
        "",
        "| 品种 | 旧B级 | 新B级 | 新增 |",
        "|---|---|---|---|",
    ]
    for code in ["ZN", "NI", "SN", "SI", "LI"]:
        old_b = old_matched.get(code, 0)
        new_b = sum(1 for x in final_5m.get(code, {}).values() if x["tier"] == "B")
        lines.append("| %s(%s) | %d | %d | %+d |" % (code, CN[code], old_b, new_b, new_b - old_b))

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("  Report saved to %s" % REPORT_PATH)

    print("\n" + "=" * 60)
    print("Task 1 complete!")
    print("  New indicators registered: %d" % len(new_entries))
    print("  Total indicators: %d" % len(ind))
    print("=" * 60)

if __name__ == "__main__":
    main()
