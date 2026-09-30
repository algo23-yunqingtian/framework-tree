# -*- coding: utf-8 -*-
"""
quality_regression.py  — 别名库分层质量分析 + 高危混淆对 + 回归测试套件
=========================================================================
DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST · T2.5 / T2.6

产出:
  1. high_risk_confusion_pairs.csv   高危混淆指标对 (跨品种错配风险)
  2. quality_regression_result.json  质量分层标签 + 覆盖率 + 回归测试结构化结果
  3. 控制台逐行日志 (回归测试 TP/TN/FP/FN)

原则:
  * V86 判定引擎 new_matcher 从 build_alias_library.py 原样加载, 不重新实现,
    保证回归测试用的判定逻辑与被审对象的构建逻辑完全一致。
  * 负向测试集 = revised/risk_rootcause_review/risk_rootcause_detail.csv 全部 41 条。
  * 正向测试集 = ths_updated_match_stat.csv 中 verify_status ∈ {VALID, FILLED} 且
    match_type != none 的历史正确匹配, 分层随机抽样 200 条 (种子固定, 可复现)。
  * 不修改任何源数据; 不调用 zhiji API。
"""
import csv, json, os, re, sys, hashlib, random
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

REPO = r"D:\DSH_WORK\framework-tree"
V85 = REPO + r"\analysis\e2e_output\v85"
SRC_BUILD = V85 + r"\alias_match_presearch\build_alias_library.py"
THS = V85 + r"\tonghuashun_recheck_fixed\ths_updated_match_stat.csv"
OK_LIST = V85 + r"\fuzzy_match_fix\revised_full_ok_list.md"
RISK41 = V85 + r"\risk_rootcause_review\risk_rootcause_detail.csv"
AUDIT = V85 + r"\alias_lib_full_audit"
ALIAS_CSV = os.path.join(AUDIT, "indicator_alias_library.csv")

os.makedirs(AUDIT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")

TS = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
SEED = 20261001

# ------------------------------------------------------------------
# 0. 原样加载 build_alias_library.py 的判定引擎 (到 "# 10. 写..." 之前, 无写文件语句)
# ------------------------------------------------------------------
src_lines = open(SRC_BUILD, encoding="utf-8").read().split("\n")
src_bytes = open(SRC_BUILD, "rb").read()
cut = None
for _i, _l in enumerate(src_lines):
    if "写 indicator_alias_library.csv" in _l and _l.strip().startswith("# 10"):
        cut = _i
        break
assert cut is not None, "未找到 '# 10. 写 indicator_alias_library.csv' 分节标记, 拒绝加载"
head_src = "\n".join(src_lines[:cut])

M = {"__name__": "build_alias_module", "__file__": SRC_BUILD}
exec(compile(head_src, SRC_BUILD, "exec"), M)

new_matcher = M["new_matcher"]
old_pipeline_accept = M["old_pipeline_accept"]
canon_of = M["canon_of"]
canon = M["canon"]
norm_light = M["norm_light"]
match_norm = M["match_norm"]
dice = M["dice"]
metal_families = M["metal_families"]
hit_metric = M["hit_metric"]
primary_metric = M["primary_metric"]
resolve_canonical = M["resolve_canonical"]
conf_index = M["conf_index"]
CONF = M["CONF"]

print("=" * 78)
print("quality_regression.py · 质量分层 + 高危混淆对 + 回归测试")
print("  执行时间(UTC+8) : %s" % TS)
print("  源脚本 MD5 %s (SHA256 %s)"
      % (hashlib.md5(src_bytes).hexdigest(), hashlib.sha256(src_bytes).hexdigest()))
print("  加载范围: 第1..%d行 (分节标记 '# 10.' 位于第%d行, 之后写文件语句已排除)" % (cut, cut + 1))
print("  随机种子: %d (正向测试集抽样可复现)" % SEED)
print("  判定引擎: build_alias_library.py::new_matcher (原样加载, 未重新实现)")
print("=" * 78)

# ==================================================================
# 1. 别名库分层质量标签
# ==================================================================
print("\n" + "=" * 78)
print("【T2.5.3】别名库质量分层: 可靠同义 / 存疑 / 明确错误 / 待注册")
print("=" * 78)

ALIAS = list(csv.DictReader(open(ALIAS_CSV, encoding="utf-8-sig")))

def quality_label(r):
    """四层质量标签 + 判定依据。"""
    rel = r["relation"]
    flag = r["review_flag"]
    bl = r["blacklist_rule"].strip()
    risk = r["risk_case_ids"].strip()
    conf = float(r["confidence"]) if r["confidence"] else 0.0
    ncn = int(r["confusable_neighbor_count"] or 0)
    srcs = r["alias_source"]

    # W3 明确错误: 黑名单已命中且属于已验证错误匹配家族
    if bl:
        return ("W3_明确错误", "黑名单规则 %s 命中 (已发生的错配模式), 禁止入库" % bl)
    # W3' 已关联风险案例且为冲突类
    if rel == "canonical_conflict" and risk:
        return ("W3_明确错误", "relation=canonical_conflict 且已关联风险案例 %s" % risk)

    # W2 存疑: 需要人工复核的一切
    if flag == "manual_review":
        if rel == "canonical_conflict":
            return ("W2_存疑", "canonical 冲突: 同一 canonical 名被多个 key 声明, conf=%.2f" % conf)
        if rel == "synonym_with_confusable_neighbor":
            return ("W2_存疑", "存在 %d 个混淆邻居, 需确认同义关系是否成立" % ncn)
        return ("W2_存疑", "review_flag=manual_review (conf=%.2f)" % conf)
    if risk:
        return ("W2_存疑", "关联风险案例 %s, 需人工确认口径" % risk)
    if ncn >= 3:
        return ("W2_存疑", "混淆邻居数 %d >= 3, 相似度密度过高" % ncn)

    # W1 可靠: 自动通过的同义合并
    if rel == "synonym_merge" and flag == "auto":
        multi = len(set(srcs.split("|"))) > 1
        return ("W1_可靠同义",
                "synonym_merge + auto + conf=%.2f%s" % (
                    conf, ", 跨数据源(%s)交叉印证" % srcs.replace("|", "/") if multi
                    else ", 单源归一化合并"))

    # W0 待注册: 尚无 canonical 绑定
    if rel == "unregistered":
        return ("W0_待注册", "未注册: 尚无 canonical 绑定 (conf=%.2f 为占位值)" % conf)

    return ("W2_存疑", "未命中任何明确规则, 默认存疑 (rel=%s flag=%s)" % (rel, flag))

LAB = []
for r in ALIAS:
    lab, why = quality_label(r)
    LAB.append({"alias_id": r["alias_id"], "alias_norm": r["alias_norm"],
                "canonical_key": r["canonical_key"], "canonical_name": r["canonical_name"][:60],
                "variety_family": r["variety_family"], "alias_source": r["alias_source"],
                "alias_type": r["alias_type"], "relation": r["relation"],
                "confidence": r["confidence"], "blacklist_rule": r["blacklist_rule"],
                "risk_case_ids": r["risk_case_ids"], "review_flag": r["review_flag"],
                "review_priority": r["review_priority"],
                "confusable_neighbor_count": r["confusable_neighbor_count"],
                "quality_tier": lab, "quality_reason": why})

tier_c = Counter(x["quality_tier"] for x in LAB)
print("\n质量分层分布 (总 %d 行):" % len(LAB))
for k in ("W1_可靠同义", "W2_存疑", "W3_明确错误", "W0_待注册"):
    print("   %-12s %6d (%5.1f%%)" % (k, tier_c[k], 100.0 * tier_c[k] / len(LAB)))

print("\n分层 x relation 交叉:")
cr = defaultdict(Counter)
for x in LAB:
    cr[x["quality_tier"]][x["relation"]] += 1
for t in ("W1_可靠同义", "W2_存疑", "W3_明确错误", "W0_待注册"):
    print("   %-12s %s" % (t, dict(cr[t])))

print("\n分层 x 品种族 (前12):")
cf = defaultdict(Counter)
for x in LAB:
    cf[x["quality_tier"]][x["variety_family"]] += 1
for t in ("W1_可靠同义", "W2_存疑", "W3_明确错误", "W0_待注册"):
    print("   %-12s %s" % (t, cf[t].most_common(12)))

print("\nW2/W3 条目中人工审核优先级分布:")
prio = Counter(x["review_priority"] for x in LAB if x["quality_tier"] in ("W2_存疑", "W3_明确错误"))
for k, v in prio.most_common():
    print("   %-12s %5d" % (k, v))

# ==================================================================
# 2. 覆盖率: PDF 来源 / THS 同花顺
# ==================================================================
print("\n" + "=" * 78)
print("【T2.5.1】别名库覆盖率: PDF 模板来源 vs THS 同花顺来源")
print("=" * 78)

ths_rows = list(csv.DictReader(open(THS, encoding="utf-8-sig", newline="")))
n_ths = len(ths_rows)

# THS 侧: 以 series_name 归一化为键, 看别名库是否收录
alias_norm_set = set(x["alias_norm"] for x in ALIAS)
alias_norm_by_canon = defaultdict(set)
for x in ALIAS:
    for ck in x["canonical_key"].split("|"):
        if ck:
            alias_norm_by_canon[ck].add(x["alias_norm"])
canonical_keys_covered = set(alias_norm_by_canon.keys())

covered = 0
uncovered_kinds = Counter()
for r in ths_rows:
    nm = norm_light(r["series_name"])
    hit_alias = nm in alias_norm_set
    hit_canon = r["indicator_key"] in canonical_keys_covered
    if hit_alias or hit_canon:
        covered += 1
    else:
        uncovered_kinds[(r["match_type"], r["verify_status"])] += 1

print("\nTHS 同花顺来源 (%d 行 series):" % n_ths)
print("   别名库已覆盖 (alias_norm 命中 或 indicator_key 已注册) : %d (%.1f%%)"
      % (covered, 100.0 * covered / n_ths))
print("   未覆盖                                                    : %d (%.1f%%)"
      % (n_ths - covered, 100.0 * (n_ths - covered) / n_ths))
print("   未覆盖行的 (match_type, verify_status) 分布:")
for k, v in uncovered_kinds.most_common():
    print("      %-14s %-9s %5d" % (k[0], k[1], v))

# 按 match_type 分层覆盖率
print("\n   按 match_type 分层覆盖率:")
mt_cov = defaultdict(lambda: [0, 0])
for r in ths_rows:
    nm = norm_light(r["series_name"])
    mt_cov[r["match_type"]][1] += 1
    if nm in alias_norm_set or r["indicator_key"] in canonical_keys_covered:
        mt_cov[r["match_type"]][0] += 1
for mt, (c, t) in sorted(mt_cov.items(), key=lambda x: -x[1][1]):
    print("      %-14s %5d / %5d = %5.1f%%" % (mt, c, t, 100.0 * c / t if t else 0.0))

# PDF 侧: revised_full_ok_list.md 中的 FULL_OK 模板 (实际表格行, 非全文正则)
# 注意: ths_updated_match_stat.csv 的 template_id 是 THS-XX-N.N 格式,
#       与 ok_list 的 TPL-XX-NNN 格式完全不同 (实测交集为 0),
#       故 PDF 覆盖率必须按"模板图表标题"口径统计, 不能按 template_id 关联。
ok_md = open(OK_LIST, encoding="utf-8").read()
ok_rows = []
for _line in ok_md.split("\n"):
    _m = re.match(r"\|\s*\d+\s*\|\s*(TPL-[A-Z]{2}-\d{3})\s*\|\s*([A-Z]{2})\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|", _line)
    if _m:
        ok_rows.append((_m.group(1), _m.group(2), _m.group(3).strip(), int(_m.group(4))))
tpl_ids_unique = sorted({r[0] for r in ok_rows})
pdf_titles = sorted({r[2] for r in ok_rows})
alias_name_norm = set(norm_light(x["alias_name"]) for x in ALIAS)
alias_norm_only = set(x["alias_norm"] for x in ALIAS)

tpl_cov = tpl_miss = 0
tpl_miss_list = []
for t in pdf_titles:
    if norm_light(t) in alias_name_norm or norm_light(t) in alias_norm_only:
        tpl_cov += 1
    else:
        tpl_miss += 1
        tpl_miss_list.append(t)

print("\nPDF 模板来源 (revised_full_ok_list.md 实际表格):")
print("   表格行数 %d | 模板ID去重 %d | 图表标题去重 %d | series 合计 %d"
      % (len(ok_rows), len(tpl_ids_unique), len(pdf_titles), sum(r[3] for r in ok_rows)))
print("   口径: 以'模板图表标题'归一化后在别名库 alias_name/alias_norm 中命中")
print("   覆盖 %d / %d = %.1f%%" % (tpl_cov, len(pdf_titles), 100.0 * tpl_cov / len(pdf_titles)))
print("   未覆盖 %d 条: %s" % (tpl_miss, tpl_miss_list[:6]))

# PDF 侧别名条目数
pdf_alias = [x for x in ALIAS if "PDF_TEMPLATE" in x["alias_source"]]
pdf_keys = set()
for x in pdf_alias:
    for ck in x["canonical_key"].split("|"):
        if ck:
            pdf_keys.add(ck)
print("\n   别名库中 alias_source 含 PDF_TEMPLATE 的条目: %d 行, 绑定 %d 个 distinct canonical key"
      % (len(pdf_alias), len(pdf_keys)))
ths_alias = [x for x in ALIAS if "THS" in x["alias_source"]]
ths_keys = set()
for x in ths_alias:
    for ck in x["canonical_key"].split("|"):
        if ck:
            ths_keys.add(ck)
print("   别名库中 alias_source 含 THS 的条目      : %d 行, 绑定 %d 个 distinct canonical key"
      % (len(ths_alias), len(ths_keys)))
iv1_alias = [x for x in ALIAS if "INDICATORS_V1" in x["alias_source"]]
print("   别名库中 alias_source 含 INDICATORS_V1 的条目: %d 行" % len(iv1_alias))

# ==================================================================
# 3. 高危混淆对 high_risk_confusion_pairs.csv
# ==================================================================
print("\n" + "=" * 78)
print("【T2.5.2】高危混淆指标对 (极易跨品种错配)")
print("=" * 78)

HIGH = []
seen = set()

def add_high(left, right, fam_l, fam_r, dice_v, evidence, category, severity, extra=""):
    key = (norm_light(left), norm_light(right))
    if key in seen:
        return
    seen.add(key)
    HIGH.append({"left": str(left).strip(), "right": str(right).strip(),
                 "variety_left": fam_l, "variety_right": fam_r,
                 "cross_variety": ("YES" if fam_l != fam_r else "NO"),
                 "dice": round(dice_v, 4) if dice_v is not None else "",
                 "evidence": evidence, "category": category,
                 "severity": severity, "extra": extra})

# 来源1: 已发生的错配 (风险库 41 条) —— 最高优先
risk41 = list(csv.DictReader(open(RISK41, encoding="utf-8-sig", newline="")))
for r in risk41:
    if not r["matched_name"].strip():
        continue
    fl = metal_families(norm_light(r["indicator_name"]))
    fr = metal_families(norm_light(r["matched_name"]))
    add_high(r["indicator_name"], r["matched_name"],
             "|".join(fl) or "-", "|".join(fr) or "-",
             dice(norm_light(r["indicator_name"]), norm_light(r["matched_name"])),
             "RISK_DB %s/%s (%s)" % (r["id"], r["risk_level"], r["blacklist_id"]),
             r["conflict_type"], r["risk_level"],
             r["conflict_reason"][:60])

# 来源2: CONF 中跨品种 + 高 Dice 的对
for c in CONF:
    fl = metal_families(c["left_norm"])
    fr = metal_families(c["right_norm"])
    if not (fl and fr):
        continue
    if set(fl) & set(fr):
        continue                                  # 同族不算跨品种混淆
    if c["dice"] < 0.60:
        continue
    add_high(c["left"], c["right"], "|".join(fl), "|".join(fr), c["dice"],
             c["evidence"], c["category"],
             "P0" if c["dice"] >= 0.85 else "P1", c["extra"])

HIGH.sort(key=lambda x: (0 if x["cross_variety"] == "YES" else 1,
                         -(x["dice"] or 0), 0 if x["severity"] == "P0" else 1))
with open(os.path.join(AUDIT, "high_risk_confusion_pairs.csv"), "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(HIGH[0].keys()))
    w.writeheader()
    w.writerows(HIGH)

cross = sum(1 for x in HIGH if x["cross_variety"] == "YES")
print("\n高危混淆对总数 %d (跨品种 %d / 同族 %d)" % (len(HIGH), cross, len(HIGH) - cross))
print("   按证据来源:")
for k, v in Counter(x["evidence"].split(" ")[0] for x in HIGH).most_common():
    print("      %-12s %5d" % (k, v))
print("   按严重级别:", dict(Counter(x["severity"] for x in HIGH)))
print("   跨品种族 TOP12:")
pair_c = Counter()
for x in HIGH:
    if x["cross_variety"] == "YES":
        a, b = x["variety_left"].split("|")[0], x["variety_right"].split("|")[0]
        pair_c[tuple(sorted((a, b)))] += 1
for k, v in pair_c.most_common(12):
    print("      %-14s %5d" % ("%s~%s" % k, v))
print("\n   TOP12 高危对 (按 Dice):")
for x in HIGH[:12]:
    print("      %-34s vs %-34s dice=%s [%s/%s] %s"
          % (x["left"][:33], x["right"][:33], x["dice"], x["variety_left"],
             x["variety_right"], x["evidence"][:28]))

# ==================================================================
# 4. 回归测试套件
# ==================================================================
print("\n" + "=" * 78)
print("【T2.6】回归测试套件: 41 负向 (应拦截) + 200 正向 (不应误拦)")
print("=" * 78)

# ---- 测试集1: 41 条历史风险案例 (负向) ----
neg = []
for r in risk41:
    l_raw = r["indicator_name"]
    m_raw = r["matched_name"].strip()
    if not m_raw:
        res = {"accept": False, "review": False, "reason": "no_match_target_recorded", "dice": None}
    else:
        res = new_matcher(l_raw, m_raw)
    caught = not res["accept"]          # 预测为"风险" = 未自动放行
    neg.append({"id": r["id"], "risk_level": r["risk_level"],
                "conflict_type": r["conflict_type"],
                "left": l_raw, "right": m_raw,
                "verify_status": r["verify_status"],
                "old_pipeline_fire": "YES" if m_raw else "N/A",
                "new_accept": res["accept"], "new_review": bool(res.get("review")),
                "new_reason": res.get("reason", ""), "new_rule": res.get("rule", ""),
                "dice": res.get("dice"), "caught": caught})

TP = sum(1 for x in neg if x["caught"])
FN = sum(1 for x in neg if not x["caught"])

# ---- 测试集2: 200 条历史正确匹配 (正向) ----
pos_pool = [r for r in ths_rows
            if r["match_type"] != "none"
            and r["verify_status"] in ("VALID", "FILLED")
            and r["indicator_key"]]
print("\n正向候选池: %d 行 (match_type!=none 且 verify_status∈{VALID,FILLED})" % len(pos_pool))
pool_kind = Counter((r["match_type"], r["verify_status"]) for r in pos_pool)
for k, v in pool_kind.most_common():
    print("   %-14s %-9s %5d" % (k[0], k[1], v))

rng = random.Random(SEED)
rng.shuffle(pos_pool)
pos_sample = pos_pool[:200]

pos = []
for r in pos_sample:
    tgt = canon_of(r) or (r["matched_name"] if r["matched_name"] not in ("", "None") else "")
    if r["match_type"] == "exact_key" or (r["match_type"] == "fuzzy_key"):
        tgt = canon.get(r["indicator_key"], {}).get("name", "") or tgt
    res = new_matcher(r["series_name"], tgt)
    kept = res["accept"]
    pos.append({"series": r["series_name"], "matched": r["matched_name"],
                "target_canon": canon_of(r), "indicator_key": r["indicator_key"],
                "template_id": r["template_id"], "match_type": r["match_type"],
                "verify_status": r["verify_status"], "confidence": r["confidence"],
                "new_accept": res["accept"], "new_review": bool(res.get("review")),
                "new_reason": res.get("reason", ""), "new_rule": res.get("rule", ""),
                "dice": res.get("dice"), "kept": kept})

TN = sum(1 for x in pos if x["kept"])
FP = sum(1 for x in pos if not x["kept"])

print("\n正向测试集 (抽样 200, seed=%d):" % SEED)
for k, v in Counter(x["match_type"] for x in pos_sample).most_common():
    print("   %-14s %5d" % (k, v))
for k, v in Counter(x["verify_status"] for x in pos_sample).most_common():
    print("   verify %-8s %5d" % (k, v))

# ---- 混淆矩阵 ----
print("\n" + "-" * 78)
print("回归测试结果 (二分类: 预测'风险/拦截' vs 真实标签)")
print("-" * 78)
print("   类别定义:")
print("     真实正类 = 41 条历史风险案例 (应被拦截)")
print("     真实负类 = 200 条历史正确匹配 (不应被拦截)")
print("     预测正类 = V86 new_matcher 返回 accept=False (block 或 review)")
print()
print("                    预测:拦截   预测:放行")
print("   真实:风险      |  TP=%4d   |  FN=%4d  |   <- 41 条负向样例" % (TP, FN))
print("   真实:正确      |  FP=%4d   |  TN=%4d  |   <- 200 条正向样例" % (FP, TN))
print()
tpfp = TP + FP
tpfn = TP + FN
fpfn = FN + FP
acc = 100.0 * (TP + TN) / (TP + TN + FP + FN) if (TP + TN + FP + FN) else 0.0
prec = 100.0 * TP / tpfp if tpfp else 0.0
rec = 100.0 * TP / tpfn if tpfn else 0.0
spec = 100.0 * TN / fpfn if fpfn else 0.0
f1 = 2.0 * prec * rec / (prec + rec) if (prec + rec) else 0.0
bal = (rec + spec) / 2.0
print("   Accuracy      = %.1f%%  (%d / %d)" % (acc, TP + TN, TP + TN + FP + FN))
print("   Precision     = %.1f%%  (TP %d / (TP+FP) %d)" % (prec, TP, tpfp))
print("   Recall        = %.1f%%  (TP %d / (TP+FN) %d)   <- 风险案例拦截率" % (rec, TP, tpfn))
print("   Specificity   = %.1f%%  (TN %d / (TN+FP) %d)   <- 正确匹配保留率" % (spec, TN, fpfn))
print("   F1            = %.1f%%" % f1)
print("   Balanced Acc  = %.1f%%" % bal)

print("\n   误放行 (FN) 明细 —— 历史风险案例被 V86 自动通过:")
if FN == 0:
    print("      无。41 条风险案例全部被拦截。")
else:
    for x in neg:
        if not x["caught"]:
            print("      !! [%s] %s | %s -> %s | reason=%s dice=%s"
                  % (x["id"], x["risk_level"], x["left"][:30], x["right"][:30],
                     x["new_reason"], x["dice"]))

print("\n   误拦截 (FP) 明细 —— 历史正确匹配被 V86 降级或拦截 (最多25条):")
if FP == 0:
    print("      无。200 条正确匹配全部自动通过。")
else:
    for x in pos[:25]:
        if not x["kept"]:
            print("      !! [%s/%s] %s -> %s | reason=%s rule=%s dice=%s"
                  % (x["match_type"], x["verify_status"], x["series"][:30],
                     (x["target_canon"] or "-")[:26], x["new_reason"], x["new_rule"], x["dice"]))
    if FP > 25:
        print("      ... 另有 %d 条未列出" % (FP - 25))

# 三态细分
print("\n   三态细分 (V86 返回 accept/review/block):")
def tri(x):
    if x["new_accept"]:
        return "accept"
    return "review" if x["new_review"] else "block"
print("      负向41 : %s" % dict(Counter(tri(x) for x in neg)))
print("      正向200: %s" % dict(Counter(tri(x) for x in pos)))

# review 单独统计: review 是"禁止自动放行"而非硬拦截
neg_review = sum(1 for x in neg if x["caught"] and x["new_review"])
pos_review = sum(1 for x in pos if not x["kept"] and x["new_review"])
print("      其中 review (降级人工复核, 非硬拦截): 负向 %d / 正向 %d" % (neg_review, pos_review))
print("      硬拦截 (block): 负向 %d / 正向 %d"
      % (sum(1 for x in neg if x["caught"] and not x["new_review"]),
         sum(1 for x in pos if not x["kept"] and not x["new_review"])))

# 按拦截原因归因
print("\n   拦截原因归因:")
print("      负向41 被拦截原因 : %s" % dict(Counter(x["new_reason"] for x in neg if x["caught"])))
print("      正向200 被拦原因 : %s" % dict(Counter(x["new_reason"] for x in pos if not x["kept"])))
print("      负向41 放行原因 : %s" % dict(Counter(x["new_reason"] for x in neg if not x["caught"])) or "无")

# ---- 正向集标签噪声审计 ----
# verify_status∈{VALID,FILLED} 并非干净正类: FILLED 表示"旧流水线自动填入数据",
# 可能本身就是错误匹配。对 140 条 FP 做跨品种审计, 区分"真误拦"与"正确拦截了旧错误"。
print("\n   [正向集标签噪声审计] verify_status∈{VALID,FILLED} 不等于'匹配正确'")
fp_rows = [x for x in pos if not x["kept"]]
fp_cross = fp_same = fp_neutral = 0
for x in fp_rows:
    fl = metal_families(norm_light(x["series"]))
    fr = metal_families(norm_light(x["target_canon"] or ""))
    if fl and fr and not (set(fl) & set(fr)):
        fp_cross += 1
    elif (fl and not fr) or (fr and not fl):
        fp_neutral += 1
    else:
        fp_same += 1
print("      FP %d 条中: 跨品种错配 %d (旧流水线本身匹配错误, V86 拦截正确) |" % (len(fp_rows), fp_cross))
print("                    品种中性 %d | 同族/无品种标记 %d" % (fp_neutral, fp_same))
print("      -> 扣除跨品种错配后的'疑似真误拦' %d 条, 疑似真误拦率 %.1f%%"
      % (len(fp_rows) - fp_cross, 100.0 * (len(fp_rows) - fp_cross) / len(pos)))
print("      同族/无标记类 FP 抽样 (前12):")
_show = 0
for x in fp_rows:
    fl = metal_families(norm_light(x["series"]))
    fr = metal_families(norm_light(x["target_canon"] or ""))
    if fl and fr and set(fl) & set(fr):
        if _show < 12:
            print("         %s -> %s [%s] dice=%s"
                  % (x["series"][:30], (x["target_canon"] or "-")[:26], x["new_reason"], x["dice"]))
        _show += 1

# 规则触发分布
print("\n   规则触发 (new_rule) 分布:")
print("      负向41 : %s" % dict(Counter(x["new_rule"] for x in neg if x["new_rule"])))
print("      正向200: %s" % dict(Counter(x["new_rule"] for x in pos if x["new_rule"])))

# ---- 旧流水线对照 ----
old_fire_neg = sum(1 for x in neg if x["old_pipeline_fire"] == "YES")
print("\n   旧流水线对照:")
print("      旧流水线对 41 条风险案例: %d 条已被触发并通过 (事后才跑黑名单)" % old_fire_neg)
print("      V86 前置规则集: 其中 %d 条被拦截, %d 条漏放" % (TP, FN))

# ==================================================================
# 5. 写结构化结果
# ==================================================================
result = {
    "task": "DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST",
    "generated_at": TS,
    "build_script": {"path": SRC_BUILD, "bytes": len(src_bytes),
                     "md5": hashlib.md5(src_bytes).hexdigest(),
                     "sha256": hashlib.sha256(src_bytes).hexdigest(),
                     "loaded_lines": "1..%d" % cut},
    "random_seed": SEED,
    "quality_tiers": {"counts": dict(tier_c), "by_relation": {t: dict(cr[t]) for t in cr},
                      "by_family": {t: dict(cf[t]) for t in cf},
                      "review_priority_of_w2_w3": dict(prio)},
    "coverage": {
        "ths": {"total_series": n_ths, "covered": covered,
                "covered_pct": round(100.0 * covered / n_ths, 2),
                "uncovered": n_ths - covered,
                "uncovered_dist": {("%s/%s" % k): v for k, v in uncovered_kinds.items()},
                "by_match_type": {mt: {"covered": mt_cov[mt][0], "total": mt_cov[mt][1]}
                                  for mt in mt_cov}},
        "pdf": {"ok_list_table_rows": len(ok_rows), "templates_unique": len(tpl_ids_unique),
                "chart_titles_unique": len(pdf_titles),
                "series_total": sum(r[3] for r in ok_rows),
                "titles_covered": tpl_cov,
                "titles_covered_pct": round(100.0 * tpl_cov / len(pdf_titles), 2),
                "titles_missing": tpl_miss_list,
                "note": "PDF 模板以'图表标题'为口径; THS template_id(THS-XX-N.N) 与 TPL-XX-NNN 格式无交集, 不可按 template_id 关联",
                "pdf_alias_rows": len(pdf_alias), "pdf_canonical_keys": len(pdf_keys),
                "ths_alias_rows": len(ths_alias), "ths_canonical_keys": len(ths_keys),
                "iv1_alias_rows": len(iv1_alias)},
    },
    "high_risk_confusion_pairs": {
        "total": len(HIGH), "cross_variety": cross,
        "by_evidence": dict(Counter(x["evidence"].split(" ")[0] for x in HIGH)),
        "by_severity": dict(Counter(x["severity"] for x in HIGH)),
        "cross_family_pairs": {("%s~%s" % k): v for k, v in pair_c.most_common()},
        "rows": HIGH,
    },
    "regression": {
        "test_sets": {"negative_risk41": len(neg), "positive_ok200": len(pos),
                      "positive_pool_size": len(pos_pool)},
        "confusion_matrix": {"TP": TP, "FN": FN, "FP": FP, "TN": TN},
        "metrics": {"accuracy_pct": round(acc, 2), "precision_pct": round(prec, 2),
                    "recall_pct": round(rec, 2), "specificity_pct": round(spec, 2),
                    "f1_pct": round(f1, 2), "balanced_accuracy_pct": round(bal, 2)},
        "three_state": {"negative": dict(Counter(tri(x) for x in neg)),
                        "positive": dict(Counter(tri(x) for x in pos)),
                        "negative_review": neg_review, "positive_review": pos_review,
                        "negative_block": sum(1 for x in neg if x["caught"] and not x["new_review"]),
                        "positive_block": sum(1 for x in pos if not x["kept"] and not x["new_review"])},
        "reason_dist": {"negative_caught": dict(Counter(x["new_reason"] for x in neg if x["caught"])),
                        "positive_blocked": dict(Counter(x["new_reason"] for x in pos if not x["kept"]))},
        "rule_fire": {"negative": dict(Counter(x["new_rule"] for x in neg if x["new_rule"])),
                      "positive": dict(Counter(x["new_rule"] for x in pos if x["new_rule"]))},
        "positive_label_noise": {
            "note": "verify_status∈{VALID,FILLED} 不是干净正类: FILLED 仅表示旧流水线自动填入, 可能本身即错误匹配",
            "fp_total": len(fp_rows),
            "fp_cross_variety_old_wrong": fp_cross,
            "fp_variety_neutral": fp_neutral,
            "fp_same_or_unmarked": fp_same,
            "suspected_true_false_positive": len(fp_rows) - fp_cross,
            "suspected_true_fp_rate_pct": round(100.0 * (len(fp_rows) - fp_cross) / len(pos), 2),
            "corrected_specificity_pct": round(100.0 * (TN + fp_cross) / len(pos), 2)},
        "old_pipeline_fired_negative": old_fire_neg,
        "false_negatives": [x for x in neg if not x["caught"]],
        "false_positives": [x for x in pos if not x["kept"]],
        "negative_detail": neg,
        "positive_detail": pos,
    },
}
with open(os.path.join(AUDIT, "quality_regression_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print("\n" + "=" * 78)
print("质量分析 + 回归测试完成。")
print("  high_risk_confusion_pairs.csv  : %d 行" % len(HIGH))
print("  quality_regression_result.json : 已写入")
print("  回归: TP=%d FN=%d FP=%d TN=%d | Acc=%.1f%% Prec=%.1f%% Recall=%.1f%% Spec=%.1f%% F1=%.1f%%"
      % (TP, FN, FP, TN, acc, prec, rec, spec, f1))
print("  标签噪声修正后 Specificity = %.1f%% (扣除 %d 条旧流水线自身错配)"
      % (round(100.0 * (TN + fp_cross) / len(pos), 2), fp_cross))
print("=" * 78)
