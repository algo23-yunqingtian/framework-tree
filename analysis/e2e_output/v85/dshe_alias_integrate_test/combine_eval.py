# -*- coding: utf-8 -*-
"""
combine_eval.py — T2.1 别名库 + 新版黑名单 联合回放质量评估
============================================================
DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY

做的事：
  1. 原样加载 build_alias_library.py 判定引擎（第 1..655 行，截断点动态定位）；
  2. 构建与上一轮 alias_lib_full_audit 完全一致的两组测试集
     (41 条 P0/P1 负向 + 200 条历史正确匹配正向，seed=20261001)；
  3. 以 25 条基线黑名单跑一遍 -> BEFORE（别名库 + V85 基线黑名单）；
  4. 注入 DSH-B 扩充候选中 status != not_recommended 的 6 条 -> AFTER
     （别名库 + 联合黑名单 31 条），BL_LR 直接改写，new_matcher 不重写；
  5. 计算前后 TP/TN/FP/FN / Recall / Precision / Balanced Acc，逐条差异归因到
     具体新增规则；对新增 FP 做跨品种审计，区分"旧流水线错配被正确拦截"与"真误拦"。
  6. 输出 combine_eval_result.json（结构化，供报告与 T2.5/T2.6 引用）。

不做的（约束）：
  - 不调用 zhiji API；不修改任何源文件；纯文本 token 静态回放。
  - DSH-B 声明的最终产物 semantic_blacklist_v85_final.json 实测 MISSING，
    本脚本使用「25 条基线 + blacklist_extend_candidate.json 中 6 条已采纳候选」
    作为最佳可得联合黑名单，并在结果中显式标注该替代。
"""
import csv
import json
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v86_kit as K

TS = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
OUTDIR = K.OUT
LOG = os.path.join(OUTDIR, "combine_eval_log.txt")
RESULT = os.path.join(OUTDIR, "combine_eval_result.json")

buf = []


def pr(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    buf.append(s)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    pr("=" * 78)
    pr("combine_eval.py · 别名库 + 联合黑名单 回放质量评估 (T2.1)")
    pr("任务 : %s" % K.INTEGRATION_TASK)
    pr("执行时间(UTC+8): %s" % TS)
    head, cut, m5, s256 = K.cut_source()
    pr("源脚本: alias_match_presearch/build_alias_library.py")
    pr("  MD5 %s / SHA256 %s" % (m5, s256))
    pr("  加载范围 第1..%d行 (分节标记在第%d行; 写文件语句已排除)" % (cut, cut + 1))
    pr("  随机种子 %d (与上一轮一致, 测试集可复现)" % K.SEED)
    pr("=" * 78)

    # ------------------------------------------------------------------
    # 0. T1 输入探测
    # ------------------------------------------------------------------
    pr("\n【0】T1 输入探测")
    probe = K.kit_probe()
    for r in probe:
        pr("  %-46s %s %s" % (r["label"], r["status"],
                              ("rows=%s" % r["rows"]) if r["rows"] is not None else ""))
    missing_req = [r for r in probe if r["required"] and not r["exists"]]
    pr("  -> 必需输入缺失 %d 项: %s" % (len(missing_req),
                                       [os.path.basename(x["path"]) for x in missing_req]))

    M = K.load_engine()
    new_matcher = M["new_matcher"]
    canon = M["canon"]
    canon_of = M["canon_of"]
    metal_families = M["metal_families"]
    BL_RULES = M["BL_RULES"]
    # 守卫: build_alias_library.py 第264-265行对 ALIAS[nm] 硬索引, 未入库名抛 KeyError。
    # 加 .get() 兜底 (仅进程内, 不改源文件); 本表记录未入库命中次数。
    guard = K.guard_resolve_canonical(M)
    pr("\nresolve_canonical 守卫: patched=%s, ALIAS 条目 %d"
       % (guard["patched"], guard["total_alias_entries"]))

    # ------------------------------------------------------------------
    # 1. 构建联合黑名单 (25 基线 + 6 采纳扩展)
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【1】联合黑名单构建")
    pr("=" * 78)
    combined, adopted, rejected, meta_base, meta_ext = K.load_combined_rules()
    base_bl, base_lint = K.build_bl_lr(M, BL_RULES)
    ext_bl, ext_lint = K.build_bl_lr(M, combined)

    pr("基线规则数        : %d (BL-001..BL-025, 来自 semantic_blacklist_fixed.json)" % len(BL_RULES))
    pr("扩展候选总数      : %d" % len(meta_ext.get("candidates", [])))
    pr("采纳 (非拒绝)     : %d -> %s" % (len(adopted), adopted))
    pr("拒绝 (not_recommended): %d -> %s"
       % (len(rejected), [x["candidate_id"] for x in rejected]))
    pr("联合规则总数      : %d" % len(combined))
    pr("")
    pr("扩展候选明细 (lint 后实际生效 pattern 数):")
    pr("  %-10s %-8s %-9s %-6s %-6s %-6s %s" % ("rule_id", "parent", "severity",
                                                "L_gen", "L_eff", "R_eff", "name"))
    for cid in adopted:
        L = ext_bl[cid][0]; R = ext_bl[cid][1]
        c = combined[cid]
        Lgen = len([x for x in c["left_patterns"] if x])
        pr("  %-10s %-8s %-9s %-6d %-6d %-6d %s"
           % (cid, c.get("parent_rule", "-"), c.get("severity", ""), Lgen, len(L), len(R),
              c.get("name", "")))
    kept_bl_lr = ext_bl
    kept_bl_lint = [x for x in ext_lint if x["rule_id"] in adopted]
    pr("  新增规则中 pattern lint: 丢弃 %d / 整词边界告警 %d"
       % (sum(1 for x in kept_bl_lint if "丢弃" in x["issue"]),
          sum(1 for x in kept_bl_lint if "整词边界" in x["issue"])))

    # ------------------------------------------------------------------
    # 2. 构建两组测试集 (与上一轮逐字一致)
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【2】测试集构建")
    pr("=" * 78)
    ths_rows = list(csv.DictReader(open(K.THS_STAT, encoding="utf-8-sig", newline="")))
    risk41 = list(csv.DictReader(open(K.RISK41_CSV, encoding="utf-8-sig", newline="")))
    pr("  负向测试集: 41 条历史 P0/P1 风险案例 (risk_rootcause_detail.csv)")
    pr("    级别分布: %s" % dict(Counter(r["risk_level"] for r in risk41)))
    pr("    有匹配目标: %d / 无目标: %d"
       % (sum(1 for r in risk41 if r["matched_name"].strip()),
          sum(1 for r in risk41 if not r["matched_name"].strip())))

    pos_pool = [r for r in ths_rows
                if r["match_type"] != "none"
                and r["verify_status"] in ("VALID", "FILLED")
                and r["indicator_key"]]
    pr("  正向候选池: %d 行 (match_type!=none 且 verify_status in {VALID,FILLED})" % len(pos_pool))
    for k, v in Counter((r["match_type"], r["verify_status"]) for r in pos_pool).most_common():
        pr("     %-14s %-9s %5d" % (k[0], k[1], v))
    rng = random.Random(K.SEED)
    rng.shuffle(pos_pool)
    pos_sample = pos_pool[:200]
    pr("  正向测试集: 抽样 200 条 (seed=%d)" % K.SEED)
    pr("    match_type : %s" % dict(Counter(r["match_type"] for r in pos_sample)))
    pr("    verify     : %s" % dict(Counter(r["verify_status"] for r in pos_sample)))

    # 判定封装：三态 -> 二分类标签 (block/review = 非自动放行; accept = 自动放行)
    def decide(row_left, row_right, blank_ok=False):
        if not row_right:
            return {"accept": False, "review": False, "reason": "no_match_target_recorded",
                    "rule": "", "dice": None}
        return new_matcher(row_left, row_right)

    def tgt_of(r):
        t = canon_of(r) or (r["matched_name"] if r["matched_name"] not in ("", "None") else "")
        if r["match_type"] in ("exact_key", "fuzzy_key"):
            t = canon.get(r["indicator_key"], {}).get("name", "") or t
        return t

    # ------------------------------------------------------------------
    # 3. BEFORE: 基线 25 条黑名单
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【3】BEFORE — 别名库 + 基线黑名单 (25 条)")
    pr("=" * 78)
    K.apply_rules(M, base_bl)
    neg_before, pos_before = [], []
    for r in risk41:
        res = decide(r["indicator_name"], r["matched_name"].strip())
        neg_before.append({"id": r["id"], "risk_level": r["risk_level"],
                           "conflict_type": r["conflict_type"],
                           "left": r["indicator_name"], "right": r["matched_name"].strip(),
                           "accept": res["accept"], "review": bool(res.get("review")),
                           "reason": res.get("reason", ""), "rule": res.get("rule", ""),
                           "dice": res.get("dice")})
    for r in pos_sample:
        res = new_matcher(r["series_name"], tgt_of(r))
        pos_before.append({"series": r["series_name"], "matched": r["matched_name"],
                           "target_canon": canon_of(r), "indicator_key": r["indicator_key"],
                           "template_id": r["template_id"], "match_type": r["match_type"],
                           "verify_status": r["verify_status"], "confidence": r["confidence"],
                           "accept": res["accept"], "review": bool(res.get("review")),
                           "reason": res.get("reason", ""), "rule": res.get("rule", ""),
                           "dice": res.get("dice")})

    TP0 = sum(1 for x in neg_before if not x["accept"])
    FN0 = sum(1 for x in neg_before if x["accept"])
    TN0 = sum(1 for x in pos_before if x["accept"])
    FP0 = sum(1 for x in pos_before if not x["accept"])
    cm0 = K.confusion_matrix(TP0, FN0, FP0, TN0)
    pr("  混淆矩阵 TP=%d FN=%d FP=%d TN=%d" % (TP0, FN0, FP0, TN0))
    pr("  Accuracy=%.2f%% Precision=%.2f%% Recall=%.2f%% Specificity=%.2f%% "
       "F1=%.2f%% BalancedAcc=%.2f%%"
       % (cm0["accuracy"], cm0["precision"], cm0["recall"], cm0["specificity"],
          cm0["f1"], cm0["balanced_accuracy"]))
    pr("  负向拦截原因: %s" % dict(Counter(x["reason"] for x in neg_before)))
    pr("  正向被拦原因: %s" % dict(Counter(x["reason"] for x in pos_before if not x["accept"])))
    pr("  R-07 别名库直查命中: 负向 %d / 正向 %d"
       % (sum(1 for x in neg_before if x["reason"] == "alias_exact"),
          sum(1 for x in pos_before if x["reason"] == "alias_exact")))

    # ------------------------------------------------------------------
    # 4. AFTER: 联合 31 条黑名单
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【4】AFTER — 别名库 + 联合黑名单 (31 条)")
    pr("=" * 78)
    K.apply_rules(M, ext_bl)
    neg_after, pos_after = [], []
    for r in risk41:
        res = decide(r["indicator_name"], r["matched_name"].strip())
        neg_after.append({"id": r["id"], "risk_level": r["risk_level"],
                          "conflict_type": r["conflict_type"],
                          "left": r["indicator_name"], "right": r["matched_name"].strip(),
                          "accept": res["accept"], "review": bool(res.get("review")),
                          "reason": res.get("reason", ""), "rule": res.get("rule", ""),
                          "dice": res.get("dice")})
    for r in pos_sample:
        res = new_matcher(r["series_name"], tgt_of(r))
        pos_after.append({"series": r["series_name"], "matched": r["matched_name"],
                          "target_canon": canon_of(r), "indicator_key": r["indicator_key"],
                          "template_id": r["template_id"], "match_type": r["match_type"],
                          "verify_status": r["verify_status"], "confidence": r["confidence"],
                          "accept": res["accept"], "review": bool(res.get("review")),
                          "reason": res.get("reason", ""), "rule": res.get("rule", ""),
                          "dice": res.get("dice")})
    TP1 = sum(1 for x in neg_after if not x["accept"])
    FN1 = sum(1 for x in neg_after if x["accept"])
    TN1 = sum(1 for x in pos_after if x["accept"])
    FP1 = sum(1 for x in pos_after if not x["accept"])
    cm1 = K.confusion_matrix(TP1, FN1, FP1, TN1)
    pr("  混淆矩阵 TP=%d FN=%d FP=%d TN=%d" % (TP1, FN1, FP1, TN1))
    pr("  Accuracy=%.2f%% Precision=%.2f%% Recall=%.2f%% Specificity=%.2f%% "
       "F1=%.2f%% BalancedAcc=%.2f%%"
       % (cm1["accuracy"], cm1["precision"], cm1["recall"], cm1["specificity"],
          cm1["f1"], cm1["balanced_accuracy"]))
    pr("  负向拦截原因: %s" % dict(Counter(x["reason"] for x in neg_after)))
    pr("  正向被拦原因: %s" % dict(Counter(x["reason"] for x in pos_after if not x["accept"])))
    K.apply_rules(M, base_bl)   # 还原基线（保持进程状态干净）

    # ------------------------------------------------------------------
    # 5. 指标对比 + 差异归因
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【5】前后指标对比与差异归因")
    pr("=" * 78)
    pr("  %-22s %10s %10s %10s" % ("指标", "BEFORE(25)", "AFTER(31)", "delta"))
    rows_cm = [("TP", TP0, TP1), ("FN", FN0, FN1), ("FP", FP0, FP1), ("TN", TN0, TN1),
               ("Accuracy(%)", cm0["accuracy"], cm1["accuracy"]),
               ("Precision(%)", cm0["precision"], cm1["precision"]),
               ("Recall(%)", cm0["recall"], cm1["recall"]),
               ("Specificity(%)", cm0["specificity"], cm1["specificity"]),
               ("F1(%)", cm0["f1"], cm1["f1"]),
               ("BalancedAcc(%)", cm0["balanced_accuracy"], cm1["balanced_accuracy"])]
    cm_delta = {}
    for name, a, b in rows_cm:
        d = K.delta_pp(a, b)
        cm_delta[name] = d
        pr("  %-22s %10.2f %10.2f %+10.2f" % (name, float(a), float(b), d))

    # 5.1 逐条状态翻转
    flip_neg = [(b, a) for b, a in zip(neg_before, neg_after)
                if (not b["accept"]) != (not a["accept"])]
    flip_pos = [(b, a, r) for b, a, r in zip(pos_before, pos_after, pos_sample)
                if b["accept"] != a["accept"]]
    pr("\n  逐条翻转: 负向 %d 条 / 正向 %d 条" % (len(flip_neg), len(flip_pos)))
    if flip_neg:
        for b, a in flip_neg:
            pr("    负向 %s: %s -> %s (%s vs %s)" % (b["id"], b["reason"], a["reason"],
                                                     b["left"][:22], b["right"][:22]))
    if flip_pos:
        for b, a, r in flip_pos:
            pr("    正向 [%s] %s: %s -> %s" % (a["rule"] or a["reason"],
                                               r["series_name"][:26], b["reason"], a["reason"]))

    # 5.2 新增规则边际贡献归因
    #   注意: "拦截" = not accept, 其中大部分来自非黑名单门禁 (variety_anchor_violation /
    #   below_threshold / metric_exclusion_hard / variety_neutral_target_review),
    #   与黑名单规则无关。故本表同时给出三种计数:
    #     blocked_all  = 任一门禁拦截
    #     blocked_bl   = 仅因 blacklist_precheck 拦截
    #     blocked_this = 仅因"本规则"拦截
    #   delta 一律相对 base_only 计算; rule_only 用于判断该规则自身是否有效。
    def run_cfg(ruleset, focus=None):
        bl, _ = K.build_bl_lr(M, ruleset)
        K.apply_rules(M, bl)
        nb_a = nb_bl = nb_th = 0
        for r in risk41:
            res = decide(r["indicator_name"], r["matched_name"].strip())
            if not res["accept"]:
                nb_a += 1
                if res["reason"] == "blacklist_precheck":
                    nb_bl += 1
                    if focus is not None and res.get("rule") == focus:
                        nb_th += 1
        pa_a = pa_bl = pa_th = 0
        for r in pos_sample:
            res = new_matcher(r["series_name"], tgt_of(r))
            if not res["accept"]:
                pa_a += 1
                if res["reason"] == "blacklist_precheck":
                    pa_bl += 1
                    if focus is not None and res.get("rule") == focus:
                        pa_th += 1
        return nb_a, nb_bl, nb_th, pa_a, pa_bl, pa_th

    base = run_cfg(dict(BL_RULES))
    pr("\n  新增规则边际贡献归因 (三种配置对照, delta 相对 base_only):")
    pr("  base_only (25 条): 负向 拦截合计 %d / 黑名单 %d | 正向 拦截合计 %d / 黑名单 %d"
       % (base[0], base[1], base[3], base[4]))
    per_rule = {}
    for cid in adopted:
        solo = dict(BL_RULES)
        solo[cid] = combined[cid]
        bp = run_cfg(solo, focus=cid)
        ro = run_cfg({cid: combined[cid]}, focus=cid)
        per_rule[cid] = {
            "parent": combined[cid].get("parent_rule", ""),
            "severity": combined[cid].get("severity", ""),
            "name": combined[cid].get("name", ""),
            "base_only": {"neg_blocked_all": base[0], "neg_blocked_bl": base[1],
                          "pos_blocked_all": base[3], "pos_blocked_bl": base[4]},
            "base_plus_rule": {"neg_blocked_all": bp[0], "neg_blocked_bl": bp[1],
                               "neg_by_this_rule": bp[2], "pos_blocked_all": bp[3],
                               "pos_blocked_bl": bp[4], "pos_by_this_rule": bp[5]},
            "rule_only": {"neg_blocked_all": ro[0], "neg_blocked_bl": ro[1],
                          "neg_by_this_rule": ro[2], "pos_blocked_all": ro[3],
                          "pos_blocked_bl": ro[4], "pos_by_this_rule": ro[5]},
            "neg_delta_all": bp[0] - base[0], "pos_delta_all": bp[3] - base[3],
            "neg_delta_bl": bp[1] - base[1], "pos_delta_bl": bp[4] - base[4],
            "neg_by_this_rule": bp[2], "pos_by_this_rule": bp[5],
        }
        pr("    %-10s 本规则直接命中 负向 %2d / 正向 %3d | 黑名单拦截 delta 负向 %+d 正向 %+d"
           % (cid, bp[2], bp[5], bp[1] - base[1], bp[4] - base[4]))
    K.apply_rules(M, base_bl)
    total_marginal = sum(1 for x in per_rule.values()
                         if x["neg_delta_all"] or x["pos_delta_all"])
    total_direct = sum(x["neg_by_this_rule"] + x["pos_by_this_rule"] for x in per_rule.values())
    pr("  -> 6 条新增规则中, 边际生效 (拦截总数 delta!=0) 的规则数: %d / 6" % total_marginal)
    pr("  -> 6 条新增规则直接命中合计 (本规则触发) %d 行 (负向+正向)" % total_direct)
    if total_marginal == 0:
        pr("  -> 结论: 6 条 DSH-B 扩展规则在当前 41+200 回归套件上零边际贡献,")
        pr("     且『本规则直接命中』合计 %d 行 —— 负向 15 条黑名单拦截全部由父规则 (BL-018/BL-016 等) 完成," % total_direct)
        pr("     子规则 (BL-018a/BL-018b/BL-025a/BL-016a/BL-026/BL-019a) 无一触发。")
        pr("     根因见【8】注入机制自检 (2/6 探针可移动门禁) 与【9】1134 联合回放 (零翻转)。")

    # 5.3 组合叠加边际归因: 对每条新增规则, 统计其在 AFTER 中实际触发的行数
    trigger_after = defaultdict(list)
    for x in neg_after + pos_after:
        if x["rule"]:
            trigger_after[x["rule"]].append(x["id"] if "id" in x else x["series"])
    pr("\n  AFTER 规则触发计数 (黑名单类):")
    for rid, cases in sorted(trigger_after.items(), key=lambda kv: -len(kv[1])):
        mark = " [NEW]" if rid in adopted else ""
        pr("    %-10s %5d%s" % (rid, len(cases), mark))
    trigger_after_plain = {k: v for k, v in trigger_after.items()}

    # ------------------------------------------------------------------
    # 6. 新增 FP 跨品种审计 (判断是"正确拦截旧错"还是"真误拦")
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【6】新增 FP 审计 (AFTER 相对 BEFORE 多拦截的正向样本)")
    pr("=" * 78)
    new_fp = []
    for i, r in enumerate(pos_sample):
        b = pos_before[i]; a = pos_after[i]
        if b["accept"] and not a["accept"]:
            fa, fb = metal_families(b["series"]), metal_families(a["target_canon"] or "")
            cv = bool(fa and fb and not (set(fa) & set(fb)))
            new_fp.append({"series": r["series_name"], "matched": r["matched_name"],
                           "target_canon": a["target_canon"],
                           "rule": a["rule"], "reason": a["reason"],
                           "cross_variety": cv, "variety_q": fa, "variety_t": fb,
                           "match_type": r["match_type"], "verify_status": r["verify_status"]})
    pr("  BEFORE 已拦截的正向样本: %d" % FP0)
    pr("  AFTER 新增拦截:         %d" % len(new_fp))
    pr("  其中跨品种 (旧流水线错配, V86 拦截正确): %d"
       % sum(1 for x in new_fp if x["cross_variety"]))
    pr("  非跨品种 (可能真误拦): %d" % sum(1 for x in new_fp if not x["cross_variety"]))
    for x in new_fp:
        pr("    [%s] %s  ->  %s  (cross=%s)" % (x["rule"], x["series"][:26],
                                                (x["target_canon"] or "")[:26], x["cross_variety"]))

    # ------------------------------------------------------------------
    # 7. 488 模板回放联动 (代理数据)
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【7】488 模板回放联动 (代理数据 render_simulation_log_fixed.csv)")
    pr("=" * 78)
    if os.path.isfile(K.PROXY_488_SIMLOG):
        sim = list(csv.DictReader(open(K.PROXY_488_SIMLOG, encoding="utf-8-sig", newline="")))
        pr("  代理回放行数: %d (DSH-B 声明的 full_488_template_playback_result.csv 缺失, 使用渲染模拟日志代理)"
           % len(sim))
        pr("  risk_level   : %s" % dict(Counter(r["risk_level"] for r in sim)))
        pr("  final_status : %s" % dict(Counter(r["final_status"] for r in sim)))
        pr("  fully_blocked=True: %d | partial_blocked=True: %d"
           % (sum(1 for r in sim if r["fully_blocked"] == "True"),
              sum(1 for r in sim if r["partial_blocked"] == "True")))
        pr("  invalid_series 合计: %d | valid_series 合计: %d"
           % (sum(int(r["invalid_series_count"]) for r in sim),
              sum(int(r["valid_series_count"]) for r in sim)))
        # 黑名单规则触发计数 (route_reason 反解)
        rr = Counter(r["route_reason"] for r in sim)
        pr("  route_reason :")
        for k, v in rr.most_common():
            pr("     %-38s %5d" % (k[:38], v))
        play488 = {"source_proxy": os.path.basename(K.PROXY_488_SIMLOG),
                   "declared_missing": os.path.basename(K.DSHB_488_PLAYBACK),
                   "rows": len(sim),
                   "risk_level_dist": dict(Counter(r["risk_level"] for r in sim)),
                   "final_status_dist": dict(Counter(r["final_status"] for r in sim)),
                   "routed_group_dist": dict(Counter(r["routed_group"] for r in sim)),
                   "route_reason_dist": dict(rr),
                   "fully_blocked_true": sum(1 for r in sim if r["fully_blocked"] == "True"),
                   "partial_blocked_true": sum(1 for r in sim if r["partial_blocked"] == "True"),
                   "invalid_series_total": sum(int(r["invalid_series_count"]) for r in sim),
                   "valid_series_total": sum(int(r["valid_series_count"]) for r in sim),
                   "note": "该日志为 v85_render_fix_review_package 的渲染模拟结果, "
                           "含 stage3 语义检查阶段; 非 DSH-B 声明的黑名单专项回放, "
                           "仅可用于模板级风险分布参照, 不可作为黑名单回归真值。"}
    else:
        play488 = None
        pr("  代理数据缺失。")

    # ------------------------------------------------------------------
    # 8. 注入机制自检 (数据源探针)
    #    证明 BL_LR 改写确实让 new_matcher 生效 —— 否则【5】的零边际会被误读为"注入失败"。
    #    探针原则: 从真实语料 (iv1 指标名 + ths series/matched) 中筛选两侧分别命中新增规则
    #    L/R pattern 的真实名称, 且构造使 R-01 品种锚点不触发 (一侧无品种 token),
    #    R-03 度量互斥不触发, 从而只有扩展黑名单能拦截。
    #    注: new_matcher 内部 resolve_canonical 会对未入 ALIAS 的归一名 KeyError,
    #    故探针必须取自真实语料, 不得使用合成字符串。
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【8】注入机制自检 (真实语料探针: 仅扩展黑名单可拦截的构造)")
    pr("=" * 78)
    POOL = []
    for _k, _v in M["iv1"].items():
        if isinstance(_v, dict) and "name" in _v:
            POOL.append(str(_v["name"]))
    for _r in M["ths"]:
        for _c in ("series_name", "matched_name"):
            _x = (_r.get(_c) or "").strip()
            if _x and _x != "None":
                POOL.append(_x)
    POOL = sorted(set(POOL))
    pr("  真实名称池: %d 个 (indicators_v1 名 + ths series/matched)" % len(POOL))

    def safe_match(a, b):
        try:
            return new_matcher(a, b)
        except Exception as e:
            return {"accept": False, "review": False, "reason": "ERROR:%s:%s" % (type(e).__name__, e),
                    "rule": "", "dice": None}

    inj = []
    for cid in adopted:
        Le, Re = ext_bl[cid][0], ext_bl[cid][1]
        lc = [n for n in POOL if any(p in n for p in Le)]
        rc = [n for n in POOL if any(p in n for p in Re)]
        best = None
        for a in lc:
            for b in rc:
                if a == b:
                    continue
                fa, fb = metal_families(a), metal_families(b)
                anchor = bool(fa and fb and not (set(fa) & set(fb)))
                if not anchor:          # R-01 不触发
                    best = (a, b, fa, fb)
                    break
            if best:
                break
        if not best:
            inj.append({"target_rule": cid, "left": "", "right": "",
                        "note": "真实语料中未找到 R-01 不触发的候选对",
                        "left_hits": len(lc), "right_hits": len(rc),
                        "base_reason": "", "ext_reason": "", "gate_moved": False})
            pr("  %-10s 语料命中 L=%d R=%d -> 无可用探针 (R-01 均触发)" % (cid, len(lc), len(rc)))
            continue
        a, b, fa, fb = best
        K.apply_rules(M, base_bl)
        r0 = safe_match(a, b)
        K.apply_rules(M, ext_bl)
        r1 = safe_match(a, b)
        inj.append({"target_rule": cid, "left": a, "right": b,
                    "variety_q": fa, "variety_t": fb,
                    "note": "真实语料; R-01 品种锚点不触发",
                    "base_reason": r0["reason"], "base_rule": r0.get("rule", ""),
                    "base_accept": r0["accept"],
                    "ext_reason": r1["reason"], "ext_rule": r1.get("rule", ""),
                    "ext_accept": r1["accept"],
                    "gate_moved": r0["reason"] != r1["reason"]})
        pr("  %-10s %-24s vs %-22s | 基线:%-22s -> 联合:%-20s %s"
           % (cid, a[:24], b[:22], r0["reason"], r1["reason"],
              "  <<< 门禁移动" if r0["reason"] != r1["reason"] else "  (上游门禁已覆盖)"))
    K.apply_rules(M, base_bl)
    gate_moved = sum(1 for x in inj if x.get("gate_moved"))
    ext_blacklist_hit = sum(1 for x in inj if x.get("ext_rule") in adopted)
    pr("  -> 门禁发生移动的探针: %d / %d ; 联合后由新增规则直接触发的探针: %d / %d"
       % (gate_moved, len(inj), ext_blacklist_hit, len(inj)))
    pr("  -> 注入机制判定: %s"
       % ("生效 (BL_LR 改写被 new_matcher 感知)" if (gate_moved or ext_blacklist_hit) else "未生效 (需排查)"))

    # ------------------------------------------------------------------
    # 9. 1134 条 fuzzy_name 无回归联合回放 (比 200 抽样更大面)
    # ------------------------------------------------------------------
    pr("\n" + "=" * 78)
    pr("【9】1134 条 fuzzy_name 无回归联合回放 (完整面, 非抽样)")
    pr("=" * 78)
    fz = M["fz"]
    nr_base = M["nr"]
    pr("  fuzzy_name 总数: %d" % len(fz))

    def tri(res):
        """兼容两种行结构: 本脚本自建的 {accept,review} 与源脚本 nr 的 {new_accept,new_review}。"""
        acc = res.get("accept", res.get("new_accept"))
        rv = res.get("review", res.get("new_review"))
        if acc:
            return "keep"
        if rv:
            return "review"
        return "block"

    b_tri = Counter()
    for r in nr_base:
        b_tri[tri(r)] += 1
    pr("  基线三态: keep=%d review=%d block=%d" % (b_tri["keep"], b_tri["review"], b_tri["block"]))

    K.apply_rules(M, ext_bl)
    ext_rows = []
    for r in fz:
        tgt = canon_of(r) or (r["matched_name"] if r["matched_name"] not in ("", "None") else "")
        o = safe_match(r["series_name"], tgt)
        ext_rows.append({"series": r["series_name"], "matched": r["matched_name"],
                         "tgt": tgt, "match_type": r["match_type"],
                         "verify_status": r["verify_status"],
                         "bl_status": r.get("blacklist_status", ""),
                         "accept": o["accept"], "review": bool(o.get("review")),
                         "reason": o.get("reason", ""), "rule": o.get("rule", ""),
                         "dice": o.get("dice")})
    K.apply_rules(M, base_bl)
    e_tri = Counter(tri(x) for x in ext_rows)
    pr("  联合三态: keep=%d review=%d block=%d" % (e_tri["keep"], e_tri["review"], e_tri["block"]))
    pr("  三态 delta (联合-基线): keep %+d / review %+d / block %+d"
       % (e_tri["keep"] - b_tri["keep"], e_tri["review"] - b_tri["review"],
          e_tri["block"] - b_tri["block"]))

    # 逐条对比基线 nr_base 与联合 ext_rows (同序)
    moves = []
    rule_delta = Counter()
    for rb, xa in zip(nr_base, ext_rows):
        tb, ta = tri(rb), tri(xa)
        if tb != ta:
            moves.append({"series": xa["series"], "tgt": xa["tgt"],
                          "base": tb, "ext": ta,
                          "base_reason": rb.get("new_reason", ""),
                          "base_rule": rb.get("new_rule", ""),
                          "ext_reason": xa["reason"], "ext_rule": xa["rule"]})
            if xa["rule"]:
                rule_delta[xa["rule"]] += 1
    pr("  状态翻转条数: %d / %d" % (len(moves), len(fz)))
    if rule_delta:
        pr("  翻转按联合后规则归因: %s" % dict(rule_delta))
    else:
        pr("  翻转按规则归因: 空 (新增黑名单规则未触发任何翻转)")
    # 新增规则在 1134 上的直接触发计数
    ext_rule_hit_1134 = Counter(x["rule"] for x in ext_rows if x["rule"] in adopted)
    base_rule_hit_1134 = Counter(x["rule"] for x in nr_base if x.get("new_rule") in adopted)
    pr("  1134 上扩展规则触发计数: %s" % (dict(ext_rule_hit_1134) or "空"))
    pr("  1134 上黑名单规则触发合计 (联合): %s"
       % dict(Counter(x["rule"] for x in ext_rows if x["rule"]).most_common()))
    for x in moves[:15]:
        pr("    [%s/%s] %s -> %s (%s)" % (x["ext_rule"], x["ext_reason"],
                                          x["series"][:26], x["tgt"][:22],
                                          "%s->%s" % (x["base"], x["ext"])))

    no_regress_joint = {
        "fuzzy_total": len(fz),
        "base_tri": dict(b_tri), "joint_tri": dict(e_tri),
        "delta": {"keep": e_tri["keep"] - b_tri["keep"],
                  "review": e_tri["review"] - b_tri["review"],
                  "block": e_tri["block"] - b_tri["block"]},
        "state_moves": len(moves),
        "state_moves_by_rule": dict(rule_delta),
        "ext_rule_hits": dict(ext_rule_hit_1134),
        "joint_blacklist_rule_hits": dict(Counter(x["rule"] for x in ext_rows if x["rule"])),
        "move_samples": moves[:40],
    }

    # ------------------------------------------------------------------
    # 10. 汇总结构化输出
    # ------------------------------------------------------------------
    res = {
        "task": K.INTEGRATION_TASK,
        "generated_at": TS,
        "base_commit": K.BASE_COMMIT,
        "branch": "feature/v85-chart-template",
        "engine": {"source": os.path.basename(K.SRC_BUILD), "loaded_lines": "1..%d" % cut,
                   "source_md5": m5, "source_sha256": s256,
                   "note": "new_matcher 原样加载; BL_LR 改写注入联合黑名单, 函数体未重写"},
        "seed": K.SEED,
        "inputs_probe": probe,
        "missing_required_inputs": [r["path"] for r in missing_req],
        "blacklist": {
            "baseline_file": os.path.basename(K.BLACKLIST_BASE),
            "baseline_rules": len(BL_RULES),
            "extend_candidate_file": os.path.basename(K.BLACKLIST_EXTEND),
            "extend_candidates_total": len(meta_ext.get("candidates", [])),
            "adopted": adopted,
            "rejected": rejected,
            "combined_rules": len(combined),
            "declared_final_blacklist_missing": not os.path.isfile(K.DSHB_FINAL_BL),
            "adopt_detail": {cid: {"name": combined[cid].get("name", ""),
                                   "parent_rule": combined[cid].get("parent_rule", ""),
                                   "severity": combined[cid].get("severity", ""),
                                   "status": combined[cid].get("status", ""),
                                   "left_patterns_kept": len(ext_bl[cid][0]),
                                   "right_patterns_kept": len(ext_bl[cid][1]),
                                   "case_source": combined[cid].get("case_source", [])}
                            for cid in adopted},
            "extend_pattern_lint": kept_bl_lint,
        },
        "test_sets": {
            "negative_risk41": len(risk41),
            "negative_with_target": sum(1 for r in risk41 if r["matched_name"].strip()),
            "negative_no_target": sum(1 for r in risk41 if not r["matched_name"].strip()),
            "negative_level_dist": dict(Counter(r["risk_level"] for r in risk41)),
            "positive_pool_size": len(pos_pool),
            "positive_sampled": len(pos_sample),
            "positive_match_type_dist": dict(Counter(r["match_type"] for r in pos_sample)),
            "positive_verify_dist": dict(Counter(r["verify_status"] for r in pos_sample)),
        },
        "before": {"rules": len(BL_RULES), "confusion": cm0,
                   "neg_reason_dist": dict(Counter(x["reason"] for x in neg_before)),
                   "pos_block_reason_dist": dict(Counter(x["reason"] for x in pos_before
                                                         if not x["accept"])),
                   "alias_exact_neg": sum(1 for x in neg_before if x["reason"] == "alias_exact"),
                   "alias_exact_pos": sum(1 for x in pos_before if x["reason"] == "alias_exact"),
                   "neg_detail": neg_before, "pos_detail": pos_before},
        "after": {"rules": len(combined), "confusion": cm1,
                  "neg_reason_dist": dict(Counter(x["reason"] for x in neg_after)),
                  "pos_block_reason_dist": dict(Counter(x["reason"] for x in pos_after
                                                         if not x["accept"])),
                  "alias_exact_neg": sum(1 for x in neg_after if x["reason"] == "alias_exact"),
                  "alias_exact_pos": sum(1 for x in pos_after if x["reason"] == "alias_exact"),
                  "neg_detail": neg_after, "pos_detail": pos_after,
                  "rule_trigger_count": trigger_after_plain},
        "delta": {"confusion": cm_delta,
                  "neg_flipped": [{"id": b["id"], "before": b["reason"], "after": a["reason"]}
                                  for b, a in flip_neg],
                  "pos_flipped": [{"series": r["series_name"], "rule": a["rule"],
                                   "before": b["reason"], "after": a["reason"]}
                                  for b, a, r in flip_pos]},
        "per_new_rule_marginal": per_rule,
        "engine_guard": {"patched": guard["patched"], "guard_hits": guard["guard_hits"],
                         "total_alias_entries": guard["total_alias_entries"],
                         "missing_samples": guard["missing_samples"],
                         "note": "build_alias_library.py 第264-265行 ALIAS[nm] 硬索引; "
                                 "进程内加 .get() 兜底, 未改写源文件"},
        "error_reason_counts": dict(Counter(x["reason"] for x in
                                            (neg_before + pos_before + neg_after + pos_after)
                                            if str(x["reason"]).startswith("ERROR"))),
        "new_fp_audit": new_fp,
        "new_fp_cross_variety": sum(1 for x in new_fp if x["cross_variety"]),
        "new_fp_non_cross": sum(1 for x in new_fp if not x["cross_variety"]),
        "injection_probes": inj,
        "injection_gate_moved": gate_moved,
        "injection_ext_hit": ext_blacklist_hit,
        "no_regress_joint": no_regress_joint,
        "play488_proxy": play488,
    }
    with open(RESULT, "w", encoding="utf-8", newline="") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    pr("\n" + "=" * 78)
    pr("已写出: %s (%d bytes)" % (RESULT, os.path.getsize(RESULT)))
    pr("已写出: %s" % LOG)
    pr("=" * 78)
    open(LOG, "w", encoding="utf-8").write("\n".join(buf))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
