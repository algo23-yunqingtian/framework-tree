# -*- coding: utf-8 -*-
"""
audit_kit.py — DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN 共享模块
================================================================================

设计原则（延续 dshe_alias_integrate_test/ 的只读口径）：
  1. 判定逻辑不重实现：通过上一轮已交付的 v86_kit.load_engine() 原样
     exec() 线上审计用 build_alias_library.py 的 1..655 行，因此
     new_matcher / resolve_canonical / norm_full / dice / metal_families /
     primary_metric / BL_LR 与被审计工具链字节一致。
  2. 所有输入只读。本模块不写任何输入文件；所有产物只写
     analysis/e2e_output/v85/dshe_alias_audit_design/。
  3. 无 zhiji API 调用；无价格数据 / 策略 / PnL。

审计口径（可复现）：
  SEED = 20261001   （与上一轮回归测试一致）
  抽样：W3/W2/W1 层全量普查（层规模 6/3/2 < 抽样配额）+ W0 层 89 条
        随机抽样（按 rerate_basis 组做「每组保底 1 + 最大余数」配额）
  判定：确定性规则化审计（audit_row），逐行输出全部证据信号，
        不引入主观随机性；每条 verdict 可被人工复核推翻。
"""
import csv
import hashlib
import io
import json
import os
import random
import sys
from collections import Counter, defaultdict

REPO = r"D:\DSH_WORK\framework-tree"
V85 = REPO + r"\analysis\e2e_output\v85"
IT = os.path.join(V85, "dshe_alias_integrate_test")          # 上一轮（只读）
AUDIT = os.path.join(V85, "alias_lib_full_audit")            # 别名库原库（只读）
OUT = os.path.join(V85, "dshe_alias_audit_design")

sys.path.insert(0, IT)                                       # 复用 v86_kit，不修改它

SEED = 20261001
TASK = "DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE_DESIGN"

ALIAS_CSV = os.path.join(AUDIT, "indicator_alias_library.csv")
AMBIG_CSV = os.path.join(AUDIT, "ambiguous_indicator_list.csv")
HRP_CSV = os.path.join(AUDIT, "high_risk_confusion_pairs.csv")
RERATED_CSV = os.path.join(IT, "ambiguous_indicator_rerated.csv")
THS_GAP_CSV = os.path.join(IT, "ths_missing_alias.csv")
IV1 = os.path.join(REPO, "data", "indicators_v1.json")
BL_FINAL = os.path.join(V85, "dshb_full_integrate", "semantic_blacklist_v85_final.json")
PLAY488 = os.path.join(V85, "dshb_full_integrate", "full_488_template_playback_result.csv")
BOUNDARY = os.path.join(V85, "miss_risk_mining", "blacklist_boundary_testset.json")
DEFECT_MD = os.path.join(V85, "miss_risk_mining", "rule_defect_summary.md")
RISKDB_V2 = os.path.join(V85, "miss_risk_mining", "unified_indicator_risk_db_v2.csv")
WORKBOOK_DSHB = os.path.join(V85, "dshb_human_review_prep", "v85_p0_risk_human_workbook.csv")
WORKBOOK_HERMES = os.path.join(V85, "hermes_human_review_tool", "v85_p0_risk_human_workbook.csv")
BATCHES_V6 = os.path.join(V85, "hermes_human_review_tool", "review_batches_v6")

# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def file_md5(path):
    return md5_bytes(open(path, "rb").read())


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def read_json(path):
    return json.load(open(path, encoding="utf-8"))


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def seed_rng(seed=SEED):
    return random.Random(seed)


# ----------------------------------------------------------------------------
# 语义 token 表（用于逐条审计，独立于引擎实现，便于人工复核）
# ----------------------------------------------------------------------------
VARIETY_TOKENS = {
    "CU": ["电解铜", "阴极铜", "铜精矿", "铜管", "铜箔", "铜棒", "铜杆", "沪铜", "伦铜", "铜"],
    "AL": ["氧化铝", "铝土矿", "铝土", "电解铝", "铝合金", "再生铝", "废铝", "铝材",
           "铝板", "铝棒", "铝杆", "原铝", "铝锭", "铝"],
    "ZN": ["锌锭", "锌精矿", "锌矿", "沪锌", "伦锌", "锌"],
    "NI": ["硫酸镍", "不锈钢", "高冰镍", "低冰镍", "冰镍", "电解镍", "精炼镍",
           "镍板", "镍豆", "镍铁", "镍精矿", "镍矿", "镍生铁", "伦镍", "沪镍", "镍"],
    "SN": ["精炼锡", "再生锡", "锡精矿", "锡锭", "锡矿", "焊锡", "锡材", "沪锡", "伦锡", "锡"],
    "SI": ["多晶硅", "工业硅", "金属硅", "单晶硅", "硅片", "硅矿", "DMC", "硅"],
    "LI": ["氢氧化锂", "碳酸锂", "锂精矿", "锂辉石", "锂云母", "盐湖提锂", "锂盐",
           "三元材料", "正极材料", "磷酸铁锂", "钴酸锂", "锰酸锂", "动力电池",
           "三元极片", "黑粉", "锂电", "锂"],
    "PB": ["铅锭", "铅精矿", "铅酸电池", "铅", "沪铅", "伦铅"],
}
# 长 token 优先，避免「氧化铝」被「铝」截断、「碳酸锂」被「锂」之外的词截断
VARIETY_TOKENS_ORDERED = sorted(
    [(t, v) for v, ts in VARIETY_TOKENS.items() for t in ts],
    key=lambda x: -len(x[0]))

METRIC_NOUNS = [
    "库存天数", "供需平衡", "库存量", "社会库存", "注册仓单", "非仓单库存", "仓单量", "仓单注册量",
    "仓单注销量", "出库量", "入库量", "库存", "产量", "销量", "消费量", "需求", "价格", "均价",
    "结算价", "收盘价", "开仓价", "加工费", "TC", "完全成本", "成本", "利润", "盈利", "毛利",
    "产能", "开工率", "产能利用率", "持仓", "持仓量", "仓单", "进出口", "出口", "进口", "净进口",
    "净出口", "基差", "升贴水", "月差", "成交量", "开工", "库存天数", "占比", "结构", "预测",
    "现货", "长约", "长单", "仓单量", "库存周转", "加工量",
]
METRIC_NOUNS_ORDERED = sorted(METRIC_NOUNS, key=lambda x: -len(x))

# 口径粒度 token：区分「同一度量词但不同口径」的近似对（E1 的证据）
QUALIFIER_TOKENS = [
    "主力合约", "近月合约", "3个月合约", "3月合约", "期货", "现货", "连续", "主力连续",
    "注册仓单", "非仓单", "社会库存", "厂库", "社会", "交易所", "场内", "场外",
    "同比", "环比", "累计", "月累计", "年累计", "移动平均", "预测", "预估", "估算",
    "中国", "美国", "欧洲", "全球", "日本", "韩国", "东南亚", "澳洲", "俄罗斯", "印尼",
    "SMM", "IAI", "IA", "LME", "SHFE", "COMEX", "GFEX", "上期所", "大商所", "郑商所",
]


def variety_of(s):
    """返回字符串中出现的品种代码集合（长 token 优先，去重）。
    注意：本函数只识别中文品种词，不识别 AO/LI/SI 之类的品种代码。"""
    t = str(s or "")
    out = set()
    for tok, code in VARIETY_TOKENS_ORDERED:
        if tok in t:
            out.add(code)
    return out


VARIETY_CODES = ["CU", "AL", "ZN", "NI", "SN", "SI", "LI", "PB", "LC", "AO"]


def variety_code(s):
    """识别列值本身即品种代码的情形（如 ths_missing_alias.csv 的 variety 列 = 'AL'）。"""
    t = str(s or "").strip().upper()
    for code in VARIETY_CODES:
        if t == code:
            return {code}
        if t.startswith(code + ":") or t.startswith(code + "|") or \
           t.startswith(code + "-") or t.startswith(code + " "):
            return {code}
    return set()


def variety_of_any(s):
    """品种代码优先，其次中文品种词。用于同时处理代码列与中文名。"""
    return variety_code(s) or variety_of(s)


def metric_nouns(s):
    """返回字符串中出现的度量词集合。"""
    t = str(s or "")
    return set(x for x in METRIC_NOUNS_ORDERED if x in t)


def qualifiers(s):
    """返回字符串中出现的口径粒度 token 集合。"""
    t = str(s or "")
    return set(x for x in QUALIFIER_TOKENS if x in t)


def jaccard(a, b):
    a, b = set(a or ()), set(b or ())
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return round(len(a & b) / float(len(a | b)), 4)


# ----------------------------------------------------------------------------
# 判定：确定性规则化审计
# ----------------------------------------------------------------------------
# 判定优先级（越靠前越先定案，避免多标签叠加）：
#   0. NO_TARGET  候选为空 -> 无法判定别名正确性（数据缺失）
#   1. E2_品种混淆 品种族非空且无交集
#   2. E3_语义不匹配 主度量词不同 + (黑名单命中 或 dice>=0.75)
#   3. E1_文本近似 字符相似度极高(>=0.90) 但口径粒度 token 不一致
#   4. OK         其余
# ----------------------------------------------------------------------------
VERDICT_LABELS = {
    "OK": "OK_正确别名",
    "E1": "E1_文本近似",
    "E2": "E2_品种混淆",
    "E3": "E3_语义不匹配",
    "NO_TARGET": "NO_TARGET_数据缺失不可判",
}


def adjudicate(left, right, dice_score="", blacklist_hit="", primary_left="",
               primary_right=""):
    """对一条别名/匹配关系给出 verdict + error_type + 证据。

    left/right 为原始展示名；dice_score 为上游 dice（缺省时返回 None 由调用方补算）。
    返回 dict：verdict, verdict_label, error_type, error_reason, evidence(dict)。
    """
    L = str(left or "")
    R = str(right or "")
    vl, vr = variety_of(L), variety_of(R)
    ml, mr = metric_nouns(L), metric_nouns(R)
    ql, qr = qualifiers(L), qualifiers(R)
    bl = str(blacklist_hit or "").strip().upper()
    bl_hit = bl not in ("", "NONE", "NO", "无", "FALSE", "0")

    ev = {
        "variety_left": "|".join(sorted(vl)),
        "variety_right": "|".join(sorted(vr)),
        "variety_disjoint": (1 if (vl and vr and not (vl & vr)) else 0),
        "metric_left": "|".join(sorted(ml)),
        "metric_right": "|".join(sorted(mr)),
        "metric_equal": (1 if ml == mr else 0),
        "primary_left": str(primary_left or ""),
        "primary_right": str(primary_right or ""),
        "qualifier_left": "|".join(sorted(ql)),
        "qualifier_right": "|".join(sorted(qr)),
        "qualifier_equal": (1 if ql == qr else 0),
        "blacklist_hit": bl_hit,
        "dice_upstream": str(dice_score or ""),
    }

    if not R.strip():
        return {"verdict": "NO_TARGET", "verdict_label": VERDICT_LABELS["NO_TARGET"],
                "error_type": "数据缺失(候选匹配为空)",
                "error_reason": "candidate_match/matched_name 为空，别名映射不可判定",
                "evidence": ev}

    if vl and vr and not (vl & vr):
        return {"verdict": "E2", "verdict_label": VERDICT_LABELS["E2"],
                "error_type": "品种混淆",
                "error_reason": "品种族 %s vs %s 无交集" % (sorted(vl), sorted(vr)),
                "evidence": ev}

    if primary_left and primary_right and primary_left != primary_right:
        if bl_hit or (str(dice_score or "").replace(".", "", 1).isdigit() and
                      float(dice_score) >= 0.75):
            return {"verdict": "E3", "verdict_label": VERDICT_LABELS["E3"],
                    "error_type": "语义不匹配",
                    "error_reason": "主度量词 %s vs %s 不同%s"
                                    % (primary_left, primary_right,
                                       "，且黑名单命中" if bl_hit else
                                       "，且 dice=%.4f>=0.75" % float(dice_score)),
                    "evidence": ev}

    d = dice_score if str(dice_score or "").replace(".", "", 1).isdigit() else None
    if d is not None and float(d) >= 0.90 and ql != qr:
        return {"verdict": "E1", "verdict_label": VERDICT_LABELS["E1"],
                "error_type": "文本近似",
                "error_reason": "字符相似度 %.4f>=0.90 但口径粒度不一致: %s vs %s"
                                % (float(d), sorted(ql), sorted(qr)),
                "evidence": ev}

    return {"verdict": "OK", "verdict_label": VERDICT_LABELS["OK"],
            "error_type": "无",
            "error_reason": "同品种 + 同主度量词 + 无黑名单命中%s"
                            % ("，口径粒度一致" if ql == qr else "，口径粒度差异未达阈值"),
            "evidence": ev}


# ----------------------------------------------------------------------------
# 引擎接入（复用 v86_kit，不重实现判定）
# ----------------------------------------------------------------------------


def load_engine():
    """加载线上判定引擎（build_alias_library.py 1..655 行），并加 resolve_canonical 守卫。

    返回 (M, engine_meta, guard_stat)。
    """
    import v86_kit as K
    M = K.load_engine()
    meta = {
        "source": "analysis/e2e_output/v85/alias_match_presearch/build_alias_library.py",
        "loaded_lines": "1..%d" % (M.get("_cut_line") or 655),
        "source_md5": M.get("_src_md5", ""),
        "source_sha256": M.get("_src_sha256", ""),
        "note": "new_matcher / resolve_canonical / norm_full / dice / metal_families "
                "原样 exec()；BL_LR 通过 __globals__ 注入",
    }
    guard = K.guard_resolve_canonical(M)
    # 注入 DSH-B 终版 31 条黑名单（本轮 T1 已确认可得）
    bl_final = read_json(BL_FINAL)
    rules = {r["rule_id"]: r for r in bl_final["rules"]}
    bl_lr, bl_lint = K.build_bl_lr(M, rules)
    old = K.apply_rules(M, bl_lr)
    return M, meta, guard, rules, bl_lr, bl_lint


def black_hit(M, a, b):
    """直接跑 31 条黑名单的 R-05 前置检查，返回 (hits[list], rule_names[list])。"""
    norm_full = M["norm_full"]
    hits, names = [], []
    x = norm_full(a)[0]
    y = norm_full(b)[0]
    for rid, (Ls, Rs, sev, nm) in M["BL_LR"].items():
        (lf, rf) = (any(p in x for p in Ls) and any(p in y for p in Rs),
                    any(p in y for p in Ls) and any(p in x for p in Rs))
        if lf or rf:
            hits.append(rid)
            names.append("%s:%s" % (rid, nm))
    return hits, names


def engine_decide(M, a, b):
    """跑 new_matcher，返回三态 dict（缺省异常时返回 empty_input 形状）。"""
    try:
        return M["new_matcher"](a, b)
    except Exception as e:                                          # 守卫之外的异常也要可观测
        return {"accept": False, "review": False,
                "reason": "engine_error:%s" % type(e).__name__,
                "detail": str(e)[:120], "dice": 0.0}


def primary_metric_of(M, s):
    try:
        return M["primary_metric"](M["norm_full"](s)[0])
    except Exception:
        return ""


def metal_families_of(M, s):
    try:
        return M["metal_families"](M["norm_full"](s)[0])
    except Exception:
        return []


def input_manifest(*paths):
    """输入清单：路径 + 字节 + MD5 + 行数/键数 + 只读声明。"""
    out = []
    for p in paths:
        ex = os.path.isfile(p)
        r = {"path": p, "exists": ex, "bytes": 0, "md5": "", "rows": None, "cols": None}
        if ex:
            b = open(p, "rb").read()
            r["bytes"] = len(b)
            r["md5"] = md5_bytes(b)
            if p.endswith(".csv"):
                with open(p, encoding="utf-8-sig", newline="") as f:
                    rr = list(csv.reader(f))
                r["rows"], r["cols"] = max(0, len(rr) - 1), (len(rr[0]) if rr else 0)
            elif p.endswith(".json"):
                try:
                    d = json.loads(b.decode("utf-8"))
                    r["rows"] = len(d) if hasattr(d, "__len__") else None
                except Exception:
                    r["rows"] = None
        out.append(r)
    return out


def largest_remainder(weights, quota, min_one=False):
    """按权重做 quota 配额分配（最大余数法）；min_one=True 时每组保底 1。"""
    groups = sorted(weights.items(), key=lambda x: -x[1])
    names = [g for g, w in groups]
    ws = [float(w) for _, w in groups]
    total = float(sum(ws)) if sum(ws) else 1.0
    alloc = {}
    if min_one:
        n = len(names)
        if n == 0 or quota < n:
            raise ValueError("quota %d 小于组数 %d，无法每组保底 1" % (quota, n))
        for nm in names:
            alloc[nm] = 1
        remaining = quota - n
        ws_rest = [float(weights[nm]) - 1.0 for nm in names]
        tot_rest = float(sum(ws_rest)) if sum(ws_rest) > 0 else 1.0
        shares = [(remaining * w / tot_rest) if tot_rest else 0.0 for w in ws_rest]
    else:
        remaining = quota
        shares = [remaining * w / total for w in ws]
    floors = [int(s) for s in shares]
    rem = remaining - sum(floors)
    order = sorted(range(len(shares)), key=lambda i: (-(shares[i] - floors[i]), -ws[i]))
    for i in order[:max(0, rem)]:
        floors[i] += 1
    for nm, f in zip(names, floors):
        alloc[nm] = alloc.get(nm, 0) + f
    return alloc


def dice_chars(a, b):
    """字符多重集 Sørensen-Dice（与 build_alias_library.py L85-91 同口径）。"""
    from collections import Counter as C
    if not a or not b:
        return 0.0
    ca, cb = C(a), C(b)
    inter = sum((ca & cb).values())
    return round(2.0 * inter / float(sum(ca.values()) + sum(cb.values())), 4)
