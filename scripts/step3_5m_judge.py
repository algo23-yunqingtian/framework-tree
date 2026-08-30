#!/usr/bin/env python3
"""Step3-5M: 规则判定器 (五金属版)。

输入: analysis/iwencai/step3_search_results_5m.json
输出: analysis/iwencai/step3_slices/verdict_rule_5m.json

泛化自 step3_judge_rules.py (CU/AL 版):
  1. 品种词: ZN锌/NI镍/SN锡/SI硅/LI锂(+英文+交易所代码), 不匹配直接淘汰
  2. 字段词: 2分/个, 覆盖≥1个
  3. 交易所前缀: LME/SHFE/COMEX/CFTC/USGS 强校验 (不匹配 -3)
  4. 口径陷阱: 每品种自己的 正/反 词表 (防"镍生铁 vs 电解镍" 这类串台)
  5. 地理口径: 中国/海外/全球 反向词淘汰
  6. 阈值: score>=5 → matched(Tier B), 否则 Tier C

阈值说明: 五金属 search 零命中仅 13/1102, 说明知几覆盖较好;
沿用 CU/AL 的阈5 (字段词+品种词+前缀), 保守优先避免误灌库。
"""
import json, os, re

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
SRC = os.path.join(ROOT, "step3_search_results_5m.json")
OUT = os.path.join(ROOT, "step3_slices", "verdict_rule_5m.json")
CODES = ["ZN", "NI", "SN", "SI", "LI"]

# 品种词: code -> 命中名必须含其一
VAR_WORDS = {
    "ZN": ["锌", "Zn", "Zinc"],
    "NI": ["镍", "Ni", "Nickel", "NPI", "高冰镍"],
    "SN": ["锡", "Sn", "Tin"],
    "SI": ["硅", "Si", "Silicon"],
    "LI": ["锂", "Li", "Lithium", "LCE"],
}

FIELD_WORDS = [
    "库存", "仓单", "价格", "收盘", "开盘", "持仓", "成交量", "产量",
    "进口", "出口", "开工率", "开工", "TC", "加工费", "升贴水", "基差",
    "消费", "需求", "成本", "利润", "溢价", "结算", "注销", "注册",
    "在途", "社会库存", "厂内", "隐性", "检修", "产能", "利用率",
    "占比", "净进口", "净持仓", "估值", "分位", "期限结构", "月差",
    "汇率", "排产", "订单", "库存天数", "平衡", "均价", "到港",
    "关税", "天数", "增速", "结构", "总产量", "开工率",
]
STOCK_WORDS = ["库存", "仓单", "在途"]
EXCHANGES = ["LME", "SHFE", "COMEX", "上期所", "中色", "CFTC", "USGS", "ILZSG"]

# 口径陷阱: code -> [(指标名含X, 命中名不得含Y)]
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

# 地理词库: 指标名含该地理 → 命中名必须含同一地理(或其上位词)
GEO_LOC = {
    "中国": ["中国", "国内", "上海", "无锡", "广东", "山东", "东北", "陕西",
             "内蒙古", "新疆", "河北", "江苏", "云南", "四川", "辽宁"],
    "国内": ["中国", "国内", "上海", "广东", "山东", "东北"],
    "全球": ["全球", "世界", "合计", "总计"],
    "美国": ["美国", "USGS"],
    "印尼": ["印尼", "印度尼西亚"],
    "菲律宾": ["菲律宾"],
    "澳大利亚": ["澳大利亚", "澳洲"],
    "日本": ["日本"],
    "南非": ["南非"],
    "欧洲": ["欧洲", "欧盟"],
    "海外": ["海外", "国际", "国外"],
    "东南亚": ["东南亚"],
    "南美": ["南美", "拉美"],
}

# 矿端/冶炼端/下游 硬区分 (串台高发区)
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

DESIGN_NOTES = ["归 7.1", "归 2.5", "归 7.2", "归 2.6", "归 2.1", "本节点按",
                "主图归", "口径为准", "管总量趋势", "管国别结构"]


def in_design(q):
    return any(n in q for n in DESIGN_NOTES)


def minus_bad(q, hname, code):
    for rule in MINUS.get(code, []):
        if rule[0] in q:
            for bad in rule[1:]:
                if bad in hname:
                    return True
    return False


# 地理域: 冲突检测 (宽松, 只淘汰明显打架, 不做"必须包含")
FOREIGN = ["美国", "印尼", "印度尼西亚", "菲律宾", "澳大利亚", "澳洲", "日本",
           "南非", "欧洲", "欧盟", "智利", "秘鲁", "加拿大", "韩国", "印度",
           "泰国", "哥伦比亚", "巴西", "俄罗斯", "哈萨克斯坦", "蒙古"]
CHINA = ["中国", "国内", "上海", "无锡", "广东", "山东", "陕西", "内蒙古",
         "新疆", "河北", "江苏", "云南", "四川", "辽宁", "东北", "华东",
         "华南", "华北", "华中", "福建", "安徽", "河南", "山西", "甘肃",
         "青海", "吉林", "黑龙江", "广西", "贵州", "湖南", "湖北", "江西",
         "浙江", "北京", "天津"]
OVERSEAS = ["海外", "国际", "国外"]


def geo_tokens(s):
    return {
        "foreign": [x for x in FOREIGN if x in s],
        "china": any(x in s for x in CHINA),
        "overseas": any(x in s for x in OVERSEAS),
    }


def geo_bad(q, hname):
    """地理冲突淘汰: 国内↔海外、A国↔B国 明显打架才算错。"""
    qq, hh = geo_tokens(q), geo_tokens(hname)
    # 国内 vs 海外/美国
    if qq["china"] and (hh["overseas"] or "美国" in hh["foreign"]
                        or "USGS" in hname):
        return True
    # 海外 vs 国内
    if qq["overseas"] and (hh["china"]):
        return True
    # 指定A国 vs 命中只有B国(且非A国的上位词)
    if qq["foreign"] and hh["foreign"] and not (set(qq["foreign"]) & set(hh["foreign"])):
        return True
    return False


OTHER_VAR = {
    "ZN": ["镍", "锡", "硅", "锂", "铝", "铜", "铅", "镍生铁", "高冰镍"],
    "NI": ["锌", "锡", "硅", "锂", "铝", "铜", "铅"],
    "SN": ["锌", "镍", "硅", "锂", "铝", "铜", "铅", "镀锡"],
    "SI": ["锌", "镍", "锡", "锂", "铝", "铜", "铅"],
    "LI": ["锌", "镍", "锡", "铝", "铜", "铅"],
}


def other_var_bad(q, hname, code):
    """命中名含其他品种词 → 串台淘汰 (如 锡现货升贴水 命中 电解铝升贴水)。"""
    for w in OTHER_VAR.get(code, []):
        if w in hname:
            # 豁免: 硅→硅铁/硅锰 属硅系; 锂→氢氧化锂
            if code == "SI" and w in ("铝",) and "硅" in hname:
                continue
            return True
    return False


def score_hit(q, h, code):
    hname = h.get("name", "") or ""
    wid = h.get("id", "") or ""
    s = 0
    vws = VAR_WORDS.get(code, [])
    # 品种词
    if any(w in hname for w in vws):
        s += 2
    elif any(w.lower() in wid.lower() for w in vws if len(w) >= 2):
        s += 1
    else:
        return -1
    # 字段词
    fields = [f for f in FIELD_WORDS if f in q]
    s += sum(2 for f in fields if f in hname)
    # 交易所前缀
    for pre in EXCHANGES:
        if pre in q and pre not in hname and pre not in wid:
            s -= 3
    # 口径陷阱 / 地理淘汰 / 跨品种串台
    if minus_bad(q, hname, code):
        return -2
    if geo_bad(q, hname):
        return -2
    if other_var_bad(q, hname, code):
        return -2
    # 矿端/冶炼端/下游 串台: 软惩罚 (-3, 阈值5下通常直接出局)
    for stage, allowed in STAGE.items():
        if stage in q and not any(a in hname for a in allowed):
            s -= 3
    # 官方源
    if h.get("source") in ("smm", "mysteel"):
        s += 1
    return s


def judge(q, v, code):
    hits = v.get("hits", [])
    if in_design(q):
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
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = {}
    for code in CODES:
        out[code] = {q: judge(q, v, code) for q, v in data.get(code, {}).items()}
        m = sum(1 for x in out[code].values() if x["matched"])
        print("%s: matched %d/%d (%.0f%%)" % (code, m, len(out[code]),
                                               100.0 * m / max(1, len(out[code]))))
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("->", OUT)
    tot = sum(len(out[c]) for c in CODES)
    tm = sum(1 for c in CODES for x in out[c].values() if x["matched"])
    print("合计 matched %d/%d" % (tm, tot))


if __name__ == "__main__":
    main()
