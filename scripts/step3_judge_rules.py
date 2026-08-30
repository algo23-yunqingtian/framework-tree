#!/usr/bin/env python3
"""Step3 语义判定 · 规则版自动判定器。

输入: analysis/iwencai/step3_verify_summary.json (CU/AL 全部指标+hits)
输出: analysis/iwencai/step3_slices/verdict_rule.json

逻辑:
 1. 品种词匹配: 指标名含"铜"→命中名须含 铜/Cu/Copper; 含"铝"→须含 铝/Al/Aluminum
 2. 字段词匹配: 从指标名提取 库存/仓单/价格/收盘价/持仓/产量/进口/出口/开工率/TC/升贴水/消费/成本/利润 等字段词,
    要求命中名覆盖≥1个字段词 (排除纯偶然)
 3. 口径修正: LME/SHFE/COMEX/上期所/中色 等交易所前缀强校验: 指标名含LME → 命中名须含LME (豁免: 命中"电解铜"等裸品种时若指标名无前缀则宽松)
 4. 得分排序: score = 品种词命中(2) + 字段词(2/个,命中多加分) + 前缀强匹配(3) + 官方源(smm/mysteel: +1)
 5. 选择 top1: score>=4 → matched; 否则 unmatched(即使有命中, 语义弱)
 6. note 记录: 命中数/最佳命中名/得分/判定理由
"""
import json, re, os

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
SRC = os.path.join(ROOT, "step3_verify_summary.json")
OUT = os.path.join(ROOT, "step3_slices", "verdict_rule.json")

FIELD_WORDS = [
    "库存", "仓单", "价格", "收盘", "开盘", "持仓", "成交量", "产量", "产量",
    "进口", "出口", "开工率", "TC", "加工费", "升贴水", "基差", "消费", "需求",
    "成本", "利润", "溢价", "结算", "现金", "注销", "注册", "在途", "社会库存",
    "厂内", "隐性", "检修", "产能", "占比", "净进口", "净持仓", "估值", "分位",
    "期限结构", "月差", "跨月", "免税", "美元", "人民币", "汇率", "开工", "排产",
    "订单", "库存天数", "供需", "平衡", "价格指数", "均价", "到港", "提单",
]
STOCK_WORDS = ["库存", "仓单", "在途"]

def variety_word(name, code):
    if code == "CU" or "铜" in name:
        return ["铜", "Cu", "Copper", "CU"]
    if code == "AL" or "铝" in name:
        return ["铝", "Al", "Aluminum", "Aluminium", "AL"]
    return []

# 说明文字/设计注释 vs 指标名
DESIGN_NOTES = ["归 7.1", "归 2.5", "归 7.2", "归 2.6", "归 2.1", "本节点按",
                "主图归", "分位（估值贵/便宜）", "席位明细（前20大）",
                "绝对值测算主图", "口径为准", "管总量趋势", "管国别结构"]

# 铝口径错位陷阱: 指标名含X → 命中名不得含Y
AL_MINUS = [("废铝", "电解铝"), ("电解铝", "废铝"), ("氧化铝", "电解铝"),
            ("电解铝", "氧化铝"), ("铝锭", "废铝"), ("原铝", "废铝"),
            ("精炼", "氧化铝"), ("铝矿", "氧化铝"), ("精炼铝", "废铝")]
# 国家口径: 指标名含中国 → 命中不要美国/海外; 含海外 → 不要中国/国内
GEO = [("中国", ["美国", "USGS", "海外", "国际", "国外", "智利", "秘鲁", "几内亚"]),
       ("海外", ["中国", "国内", "上海", "无锡", "重庆", "华东", "华南"])]

def in_design_notes(q):
    return any(n in q for n in DESIGN_NOTES)

def geo_bad(q, hname):
    for g, bads in GEO:
        if g in q and any(b in hname for b in bads):
            return True
    return False

def al_minus_bad(q, hname):
    for qw, hw in AL_MINUS:
        if qw in q and hw in hname:
            return True
    return False

def score_hit(q, h, code):
    s = 0
    hname = h.get("name", "")
    wid = h.get("id", "") or ""
    # 品种词
    vw = variety_word(q, code)
    if any(w in hname for w in vw) or any(w.lower() in wid.lower() for w in vw if len(w) >= 2):
        s += 2
    else:
        return -1  # 品种不匹配直接淘汰
    # 字段词 (取指标名里的字段词, 命中名里也出现)
    fields = [f for f in FIELD_WORDS if f in q]
    hit_fields = sum(1 for f in fields if f in hname)
    s += hit_fields * 2
    # 交易所前缀强校验
    for pre in ["LME", "SHFE", "COMEX", "上期所", "中色", "CFTC", "USGS"]:
        if pre in q and pre not in hname and pre not in wid:
            s -= 3
    # 国家口径 / 铝口径错位 直接淘汰
    if geo_bad(q, hname):
        return -2
    if al_minus_bad(q, hname):
        return -2
    # 官方源
    if h.get("source") in ("smm", "mysteel"):
        s += 1
    return s

def judge(q, v, code):
    hits = v.get("hits", [])
    if in_design_notes(q):
        return {"matched": False, "chosen": None,
                "note": "设计说明/口径注释, 非可检索指标", "hits": hits}
    if not hits:
        return {"matched": False, "chosen": None,
                "note": "知几 search 无任何命中", "hits": hits}
    scored = []
    for h in hits:
        sc = score_hit(q, h, code)
        if sc >= 0:
            scored.append((sc, h))
    scored.sort(key=lambda x: -x[0])
    if scored and scored[0][0] >= 5:
        sc, best = scored[0]
        return {"matched": True, "chosen": best,
                "note": "命中%d条, 最佳得分%d: %s" % (len(scored), sc,
                    str(best.get("name", ""))[:50]),
                "hits": [h for _, h in scored]}
    top = scored[0] if scored else None
    return {"matched": False, "chosen": None,
            "note": "存在通过品种词但字段/口径弱 (最佳得分%d, 阈5): %s" % (
                top[0] if top else 0,
                str(top[1].get("name", ""))[:50] if top else "无"),
            "hits": hits}

def main():
    data = json.load(open(SRC, encoding="utf-8"))
    out = {}
    for code in ["CU", "AL"]:
        d = data.get(code, {})
        out[code] = {}
        for q, v in d.items():
            out[code][q] = judge(q, v, code)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    for code in ["CU", "AL"]:
        m = sum(1 for x in out[code].values() if x["matched"])
        print(f"{code}: matched {m}/{len(out[code])}")

if __name__ == "__main__":
    main()