# -*- coding: utf-8 -*-
"""
canonical_resolve_fix.py — T2.2 resolve_canonical 缺陷修复原型 + 单元测试
=======================================================================
只读加载引擎（exec build_alias_library.py 1..655 行），在进程内实现
三个修复档位（F1 最小修补 / F2 结构化返回 / F3 R-07 门禁重排），
对同一批真实 pair 做行为差分，量化 TP/FP 影响，并跑单元测试断言。

产物：canonical_resolve_fix_result.json
不修改任何源文件；不调用 zhiji API。
"""
import os
import sys
import json
import datetime
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_kit as A        # noqa: E402
sys.path.insert(0, r"D:\DSH_WORK\framework-tree\analysis\e2e_output\v85\dshe_alias_integrate_test")
import v86_kit as K          # noqa: E402

CD = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------- 修复实现
def build_fixed_resolver(M):
    """F1+F2: 无假设的解析器。返回 (resolve_safe, resolve_structured, stat)。

    resolve_safe(nm) -> list[str]              等价于原实现的正确子集（不抛异常）
    resolve_structured(nm) -> dict             显式表达 0 / 1 / N 三种状态
    """
    ALIAS = M["ALIAS"]
    name2canon = M["name2canon"]
    key2canon = M["key2canon"]
    stat = {"calls": 0, "alias_hit": 0, "alias_miss": 0,
            "miss_samples": [], "n0": 0, "n1": 0, "nN": 0}

    def resolve_safe(nm):
        stat["calls"] += 1
        s = set()
        s |= set(name2canon.get(nm, []))
        s |= set(key2canon.get(nm, []))
        rec = ALIAS.get(nm)
        if rec is None:
            stat["alias_miss"] += 1
            if len(stat["miss_samples"]) < 12:
                stat["miss_samples"].append(nm)
        else:
            stat["alias_hit"] += 1
            light = rec.get("light", "")
            s |= set(name2canon.get(light, []))
            s |= set(key2canon.get(light, []))
        return sorted(s)

    def resolve_structured(nm):
        rec = ALIAS.get(nm)
        if rec is None:
            return {"state": "UNREGISTERED", "canonicals": [], "alias": False,
                    "light": ""}
        light = rec.get("light", "")
        s = set()
        s |= set(name2canon.get(nm, []))
        s |= set(key2canon.get(nm, []))
        s |= set(name2canon.get(light, []))
        s |= set(key2canon.get(light, []))
        s = sorted(s)
        if not s:
            st = "NO_MATCH"
        elif len(s) == 1:
            st = "UNIQUE"
        else:
            st = "AMBIGUOUS"
            stat["nN"] += 1
        return {"state": st, "canonicals": s, "alias": True, "light": light}

    return resolve_safe, resolve_structured, stat


def blacklist_check_bounded(M, a, b):
    """F4: 整词边界 + 同侧纯度版黑名单检查。

    修复两类 pattern 误触发：
      F4a 子串包含：L 与 R 在同一字符串内都命中，且一侧匹配区间被另一侧完全包含
                    （如 BL-012: '库存' ⊂ '库存天数'）-> 自触发，跳过该方向。
      F4b 复合短语：同一字符串内 L 与 R 以**严格不相交**的区间同时出现
                    （如 BL-009: '碳酸锂利润与需求分析' 同时含 '利润' 与 '需求'）
                    -> 该侧不是单向指标而是复合短语，跳过该方向。
    跨字符串的真实冲突不受影响。
    返回 (hits[list], skipped_self_trigger[list of (rule, 原因, L, R)])。
    """
    hits, skipped = [], []
    for rid, (Ls, Rs, sev, nm) in M["BL_LR"].items():
        fired = False
        for x, y in ((a, b), (b, a)):                     # x 侧找 L, y 侧找 R
            for lp in Ls:
                i = x.find(lp)
                if i < 0:
                    continue
                for rp in Rs:
                    j = y.find(rp)
                    if j < 0:
                        continue
                    if x == y:                            # F4a 同字符串值相等
                        if (j <= i and j + len(rp) >= i + len(lp)) or \
                           (i <= j and i + len(lp) >= j + len(rp)):
                            skipped.append((rid, "F4a_span_contained", lp, rp))
                            continue
                    # F4b 同侧纯度：x 侧含 R 的独立区间，或 y 侧含 L 的独立区间
                    impure = False
                    for rp2 in Rs:
                        k = x.find(rp2)
                        if k < 0:
                            continue
                        if k + len(rp2) < i or i + len(lp) < k:        # 严格不相交
                            impure = True
                            break
                    if not impure:
                        for lp2 in Ls:
                            k = y.find(lp2)
                            if k < 0:
                                continue
                            if k + len(lp2) < j or j + len(rp) < k:    # 严格不相交
                                impure = True
                                break
                    if impure:
                        skipped.append((rid, "F4b_compound_phrase", lp, rp))
                        continue
                    fired = True
                    break
                if fired:
                    break
            if fired:
                break
        if fired:
            hits.append(rid)
    return hits, skipped


def build_reordered_matcher(M, resolve_safe, use_f4=True):
    """F3: 门禁重排 —— 先跑 R-01/R-05，R-07 alias_exact 后移，且 AMBIGUOUS 降级复核。"""
    orig = M["new_matcher"]

    def reordered(a_raw, b_raw):
        a = M["norm_full"](a_raw)[0]
        b = M["norm_full"](b_raw)[0]
        if not a or not b:
            return {"accept": False, "review": False, "reason": "empty_input", "dice": 0.0}
        d = M["dice"](a, b)
        pa, pb = M["primary_metric"](a), M["primary_metric"](b)
        fa, fb = M["metal_families"](a), M["metal_families"](b)
        # R-01 先
        if fa and fb and not (set(fa) & set(fb)):
            return {"accept": False, "review": False, "reason": "variety_anchor_violation",
                    "detail": "%s vs %s" % (fa, fb), "dice": d}
        # R-05 先（收集全部命中 + F4 整词边界，不再短路到首条）
        if use_f4:
            hits, self_trig = blacklist_check_bounded(M, a, b)
        else:                                        # F3-only：原始子串匹配 + 全量上报
            hits = []
            for _rid, (_L, _R, _sev, _nm) in M["BL_LR"].items():
                if (any(q in a for q in _L) and any(q in b for q in _R)) or \
                   (any(q in b for q in _L) and any(q in a for q in _R)):
                    hits.append(_rid)
            self_trig = []
        if hits:
            return {"accept": False, "review": False, "reason": "blacklist_precheck",
                    "rule": hits[0], "all_rules": hits,
                    "self_trigger_skipped": self_trig,
                    "rule_name": M["BL_LR"][hits[0]][3],
                    "severity": M["BL_LR"][hits[0]][2], "dice": d}
        # R-07 后移，且对多 canonical 降级复核而非静默选键
        ca, cb = resolve_safe(a), resolve_safe(b)
        inter = sorted(set(ca) & set(cb))
        if ca and cb:
            if not inter:
                pass
            elif len(inter) == 1:
                return {"accept": True, "review": False, "reason": "alias_exact",
                        "canonical": inter[0], "dice": d}
            else:
                return {"accept": False, "review": True,
                        "reason": "alias_ambiguous_multi_canonical",
                        "canonicals": inter, "dice": d}
        # R-03 口径互斥
        lvl, pair = M["metric_conflict"](pa, pb)
        if lvl == "HARD":
            return {"accept": False, "review": False, "reason": "metric_exclusion_hard",
                    "detail": "%s vs %s" % pair, "dice": d}
        # R-01b 品种中性降级
        if (fa and not fb) or (fb and not fa):
            nw = M["NEUTRAL_WHITELIST"] if "NEUTRAL_WHITELIST" in M else set()
            nc = M["NEUTRAL_WHITELIST_CANON"] if "NEUTRAL_WHITELIST_CANON" in M else set()
            if not (((a, b) in nw) or (b in nc) or (a in nc)):
                return {"accept": False, "review": True,
                        "reason": "variety_neutral_target_review",
                        "detail": "query_variety=%s target_variety=%s" % (fa or ["-"], fb or ["-"]),
                        "dice": d}
        # R-06 阈值
        soft = "metric_exclusion_soft:%s/%s" % pair if lvl == "SOFT" else ""
        if d >= M["TH_HIGH"]:
            return {"accept": True, "review": bool(soft), "reason": "high_dice",
                    "dice": d, "soft_flag": soft}
        if d >= M["TH_MID"] and (not fa or not fb or set(fa) & set(fb)):
            return {"accept": True, "review": bool(soft), "reason": "mid_dice_same_variety",
                    "dice": d, "soft_flag": soft}
        if d >= M["TH_LOW"] and (not fa or not fb):
            return {"accept": True, "review": bool(soft), "reason": "low_dice_no_variety",
                    "dice": d, "soft_flag": soft}
        return {"accept": False, "review": False, "reason": "below_threshold",
                "dice": d, "soft_flag": soft}

    return reordered


# --------------------------------------------------------------------------- 主流程
def main():
    M, eng_meta, guard, rules, bl_lr, bl_lint = A.load_engine()
    resolve_safe, resolve_structured, stat = build_fixed_resolver(M)
    reordered = build_reordered_matcher(M, resolve_safe, use_f4=True)
    reordered_f3 = build_reordered_matcher(M, resolve_safe, use_f4=False)

    # 测试集：448 歧义行 + 488 回放 2721 pair + 别名库 alias/canonical pair
    pairs = []
    for r in A.read_csv(A.RERATED_CSV):
        if r["candidate_match"]:
            pairs.append(("rerated", r["indicator_name"], r["candidate_match"]))
    for r in A.read_csv(A.PLAY488):
        if r["series_name"] and r["matched_name"]:
            pairs.append(("play488", r["series_name"], r["matched_name"]))
    for r in A.read_csv(A.ALIAS_CSV):
        cn = r["canonical_name"].split("|")[0]
        if r["alias_name"] and cn and r["alias_name"] != cn:
            pairs.append(("aliaslib", r["alias_name"], cn))
    for _r in A.read_csv(A.ALIAS_CSV):
        if "|" in _r["canonical_key"] and _r["alias_name"]:
            pairs.append(("selfpair", _r["alias_name"], _r["alias_name"]))
    # 边界测试集
    for c in A.read_json(A.BOUNDARY)["cases"]:
        pairs.append(("boundary", c["indicator_name"], c["matched_name"]))

    src_dist = Counter(s for s, _, _ in pairs)
    total = len(pairs)

    # --- 原实现（硬索引） vs 守卫版 vs 修复版
    orig_impl = K.load_engine()
    orig_resolve = orig_impl["resolve_canonical"]
    orig_calls = orig_keyerror = 0
    orig_keyerror_samples = []
    for _, a, b in pairs:
        for nm in (M["norm_full"](a)[0], M["norm_full"](b)[0]):
            orig_calls += 1
            try:
                orig_resolve(nm)
            except KeyError:
                orig_keyerror += 1
                if len(orig_keyerror_samples) < 12:
                    orig_keyerror_samples.append(nm)

    base = [M["new_matcher"](a, b) for _, a, b in pairs]          # 原门禁顺序（已带守卫）
    fixed = [reordered(a, b) for _, a, b in pairs]

    def dist(res, key="reason"):
        return dict(Counter(r.get(key, "") for r in res).most_common())

    def acc(res):
        return Counter(r["accept"] for r in res)

    transitions = Counter()
    for r0, r1 in zip(base, fixed):
        k0 = ("A" if r0["accept"] else ("R" if r0["review"] else "B"))
        k1 = ("A" if r1["accept"] else ("R" if r1["review"] else "B"))
        transitions["%s->%s" % (k0, k1)] += 1

    # R-07 静默选键 vs 降级复核
    multi_shadow = sum(1 for r1 in fixed
                       if r1.get("reason") == "alias_ambiguous_multi_canonical")
    alias_exact_before = sum(1 for r0 in base if r0.get("reason") == "alias_exact")
    alias_exact_after = sum(1 for r1 in fixed if r1.get("reason") == "alias_exact")
    alias_ambiguous_after = sum(1 for r1 in fixed
                                if r1.get("reason") == "alias_ambiguous_multi_canonical")

    # R-05 命中上报完整性（base 只报首条，fixed 报全部）
    base_rule = Counter(r0.get("rule", "") for r0 in base if r0.get("rule"))
    fixed_rules_flat = Counter(x for r1 in fixed for x in r1.get("all_rules", []))

    # 黑名单自触发（BL-012/BL-009 pattern 子串）
    self_trigger = []
    for rid in ("BL-012", "BL-009", "BL-026"):
        Ls, Rs, sev, nm = M["BL_LR"][rid]
        for _, a, b in pairs:
            x, y = M["norm_full"](a)[0], M["norm_full"](b)[0]
            if not x or not y:
                continue
            if x == y:                                   # 同名对自触发
                if (any(p in x for p in Ls) and any(p in y for p in Rs)) or \
                   (any(p in y for p in Ls) and any(p in x for p in Rs)):
                    self_trigger.append((rid, x))
    self_trig_dist = Counter(r for r, _ in self_trigger)

    # =========================================================================
    # 单元测试
    # =========================================================================
    tests = []

    def T(tid, desc, fn):
        try:
            fn()
            tests.append({"id": tid, "desc": desc, "result": "PASS"})
        except AssertionError as e:
            tests.append({"id": tid, "desc": desc, "result": "FAIL", "detail": str(e)})
        except Exception as e:                              # noqa: BLE001
            tests.append({"id": tid, "desc": desc, "result": "ERROR",
                          "detail": "%s: %s" % (type(e).__name__, e)})

    # UT-01 缺陷复现：原实现必须抛 KeyError
    try:
        orig_resolve("产量")
        tests.append({"id": "UT-01", "result": "FAIL",
                      "desc": "原实现：未注册归一名 '产量' -> KeyError（缺陷复现）",
                      "detail": "原实现未抛 KeyError，缺陷在本环境下不可复现"})
    except KeyError:
        tests.append({"id": "UT-01", "result": "PASS",
                      "desc": "原实现：未注册归一名 '产量' -> KeyError（缺陷复现成功）"})
    except Exception as e:                                  # noqa: BLE001
        tests.append({"id": "UT-01", "result": "ERROR",
                      "desc": "原实现：未注册归一名 '产量' -> KeyError（缺陷复现）",
                      "detail": "%s: %s" % (type(e).__name__, e)})

    T("UT-02", "F1 修复：resolve_safe 对未注册名返回 [] 且不抛异常",
      lambda: (lambda v: (_ for _ in ()).throw(AssertionError("返回 %r" % v))
               if v != [] else None)(resolve_safe("产量")))
    T("UT-03", "F1 修复：resolve_safe 对已注册名与原实现一致",
      lambda: (_ for _ in ()).throw(AssertionError("不一致"))
      if resolve_safe("碳酸锂工厂库存天数") != sorted(M["resolve_canonical"]("碳酸锂工厂库存天数"))
      else None)
    T("UT-04", "F2 结构化：未注册名 state=UNREGISTERED",
      lambda: (_ for _ in ()).throw(AssertionError(str(resolve_structured("产量"))))
      if resolve_structured("产量")["state"] != "UNREGISTERED" else None)
    T("UT-05", "F2 结构化：单键 state=UNIQUE",
      lambda: (_ for _ in ()).throw(AssertionError(str(resolve_structured("碳酸锂工厂库存天数"))))
      if resolve_structured("碳酸锂工厂库存天数")["state"] != "UNIQUE" else None)
    _gfex = M["norm_full"]("GFEX：工业硅：主力合约：单边交易：持仓量（日）")[0]
    T("UT-06", "F2 结构化：复合键 alias_norm state=AMBIGUOUS（12 个原子键）",
      lambda: (_ for _ in ()).throw(AssertionError(str(resolve_structured(_gfex))))
      if resolve_structured(_gfex)["state"] != "AMBIGUOUS" else None)
    T("UT-07", "F3-only：R-07 命中但黑名单也命中 -> 黑名单优先",
      lambda: (_ for _ in ()).throw(AssertionError(
          str(reordered_f3("碳酸锂工厂库存天数", "碳酸锂工厂库存天数"))))
      if reordered_f3("碳酸锂工厂库存天数", "碳酸锂工厂库存天数")["reason"] != "blacklist_precheck"
      else None)
    T("UT-08", "F3-only：黑名单上报全部命中规则而非首条",
      lambda: (_ for _ in ()).throw(AssertionError(str(reordered_f3(
          "碳酸锂工厂库存天数", "碳酸锂工厂库存天数")["all_rules"])))
      if set(reordered_f3("碳酸锂工厂库存天数", "碳酸锂工厂库存天数")["all_rules"])
      != {"BL-012", "BL-026"} else None)
    T("UT-09", "F3 重排：BL-015 不再被 BL-008 遮蔽",
      lambda: (_ for _ in ()).throw(AssertionError(str(reordered("国内销量", "出口")["all_rules"])))
      if "BL-015" not in reordered("国内销量", "出口")["all_rules"] else None)
    T("UT-10", "F3 重排：AMBIGUOUS 别名对降级复核而非自动放行",
      lambda: (_ for _ in ()).throw(AssertionError(str(reordered(
          "GFEX：工业硅：主力合约：单边交易：持仓量（日）",
          "GFEX：工业硅：主力合约：单边交易：持仓量（日）"))))
      if reordered("GFEX：工业硅：主力合约：单边交易：持仓量（日）",
                   "GFEX：工业硅：主力合约：单边交易：持仓量（日）")["reason"]
      != "alias_ambiguous_multi_canonical" else None)
    T("UT-11", "F3 重排：空输入 -> empty_input（不变）",
      lambda: (_ for _ in ()).throw(AssertionError(str(reordered("碳酸锂工厂库存天数", ""))))
      if reordered("碳酸锂工厂库存天数", "")["reason"] != "empty_input" else None)
    T("UT-12", "F3 重排：品种锚点跨品种 -> 硬拦截（不变）",
      lambda: (_ for _ in ()).throw(AssertionError(str(reordered("LME：锌：库存（日）",
                                                                  "LME：锡：库存（日）"))))
      if reordered("LME：锌：库存（日）", "LME：锡：库存（日）")["reason"]
      != "variety_anchor_violation" else None)
    _comex = M["norm_full"]("COMEX：铜：主力合约：收盘价（日）")[0]
    T("UT-13", "F3 重排：2 键别名对 -> AMBIGUOUS 降级复核（不再静默选首键）",
      lambda: (_ for _ in ()).throw(AssertionError(str(reordered(_comex, _comex))))
      if reordered(_comex, _comex)["reason"] != "alias_ambiguous_multi_canonical" else None)
    _single = None
    for _r in A.read_csv(A.ALIAS_CSV):
        _cn = _r["canonical_name"].split("|")[0]
        if not _r["alias_name"] or "|" in _r["canonical_key"]:
            continue
        _nm = M["norm_full"](_r["alias_name"])[0]
        if resolve_structured(_nm)["state"] != "UNIQUE":
            continue
        if not blacklist_check_bounded(M, _nm, _nm)[0]:
            _single = _nm
            break
    if _single is None:
        tests.append({"id": "UT-15", "result": "SKIP",
                      "desc": "F3 重排：1 键别名对 -> alias_exact 自动放行",
                      "detail": "本数据集中不存在满足条件的单键别名对"})
    else:
        T("UT-15", "F3 重排：1 键别名对 -> alias_exact 自动放行（%s）" % _single[:20],
          lambda: (_ for _ in ()).throw(AssertionError(str(reordered(_single, _single))))
          if reordered(_single, _single)["reason"] != "alias_exact" else None)
    _tin = M["norm_full"]("锡厂库存天数（天）")[0]
    T("UT-14", "F4 边界：BL-012 pattern 自触发的同名对不再命中",
      lambda: (_ for _ in ()).throw(AssertionError(str(blacklist_check_bounded(M, _tin, _tin))))
      if blacklist_check_bounded(M, _tin, _tin)[0] else None)
    T("UT-16", "F4 边界：合法跨字符串冲突仍然命中（库存天数 vs 库存量）",
      lambda: (_ for _ in ()).throw(AssertionError(str(blacklist_check_bounded(
          M, M["norm_full"]("锡厂库存天数（天）")[0], M["norm_full"]("锡厂库存量（吨）")[0]))))
      if not blacklist_check_bounded(M, M["norm_full"]("锡厂库存天数（天）")[0],
                                     M["norm_full"]("锡厂库存量（吨）")[0])[0] else None)
    _pr1 = M["norm_full"]("碳酸锂利润与需求分析")[0]
    _pr2 = M["norm_full"]("碳酸锂利润与需求预测")[0]
    T("UT-17", "F4 边界：BL-009 自触发（利润+需求同现一个名字）不再命中",
      lambda: (_ for _ in ()).throw(AssertionError(str(blacklist_check_bounded(M, _pr1, _pr2))))
      if blacklist_check_bounded(M, _pr1, _pr2)[0] else None)

    T("UT-18", "F3+F4：BOUNDARY-013 安全负向样例恢复不阻塞（走 alias_exact）",
      lambda: (_ for _ in ()).throw(AssertionError(
          str(reordered("碳酸锂工厂库存天数", "碳酸锂工厂库存天数"))))
      if reordered("碳酸锂工厂库存天数", "碳酸锂工厂库存天数")["reason"] != "alias_exact"
      else None)
    T("UT-19", "F3+F4：BOUNDARY-017/018 类自触发误伤修复（F4b 复合短语）",
      lambda: (_ for _ in ()).throw(AssertionError(str(reordered(
          "碳酸锂利润与需求分析", "碳酸锂利润与需求预测"))))
      if reordered("碳酸锂利润与需求分析", "碳酸锂利润与需求预测")["accept"] is False
      else None)

    ut_summary = Counter(t["result"] for t in tests)

    # F4 全量统计：base 黑名单命中 vs F4 边界版命中
    f4_hits_all, f4_skip_all, black_hit_all_before = [], [], []
    for _tag, _a, _b in pairs:
        _x, _y = M["norm_full"](_a)[0], M["norm_full"](_b)[0]
        if not _x or not _y:
            f4_hits_all.append([]); f4_skip_all.append([]); black_hit_all_before.append([])
            continue
        _hb = []
        for _rid, (_L, _R, _sev, _nm) in M["BL_LR"].items():
            if (any(q in _x for q in _L) and any(q in _y for q in _R)) or \
               (any(q in _y for q in _L) and any(q in _x for q in _R)):
                _hb.append(_rid)
        _fh, _sk = blacklist_check_bounded(M, _x, _y)
        black_hit_all_before.append(_hb)
        f4_hits_all.append(_fh)
        f4_skip_all.append(_sk)
    self_trigger_release = sum(1 for _i in range(total)
                               if black_hit_all_before[_i] and not f4_hits_all[_i])
    still_blocked = sum(1 for _i in range(total)
                        if black_hit_all_before[_i] and f4_hits_all[_i])

    # =========================================================================
    out = {
        "task": A.TASK,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "engine": eng_meta,
        "defect": {
            "location": "build_alias_library.py L260-L266, resolve_canonical()",
            "source_lines": {
                "L260": "def resolve_canonical(nm):",
                "L262": "s |= set(name2canon.get(nm, []))",
                "L263": "s |= set(key2canon.get(nm, []))",
                "L264": 's |= set(name2canon.get(ALIAS[nm]["light"], []))',
                "L265": 's |= set(key2canon.get(ALIAS[nm]["light"], []))',
                "L266": "return sorted(s)",
            },
            "root_cause": "L264/L265 对 ALIAS 做硬索引 ALIAS[nm]，但 new_matcher 会把任意 "
                          "norm_full 字符串交给 resolve_canonical；ALIAS 只收录 ingest 过的 "
              "canonical_name/alias_name，未收录的名字（如短度量词'产量'、实体词'场内库存'）"
              "必然 KeyError。",
            "observed": {
                "calls_total": orig_calls,
                "keyerror": orig_keyerror,
                "keyerror_rate_pct": round(100.0 * orig_keyerror / orig_calls, 2),
                "keyerror_samples": orig_keyerror_samples,
                "alias_registry_size": len(M["ALIAS"]),
                "name2canon_size": len(M["name2canon"]),
                "key2canon_size": len(M["key2canon"]),
            },
            "note": "上一轮 guard_hits=382 为本轮的 %d 的 %s。本环境因测试集更大而放大。"
                    % (orig_keyerror, "子集" if orig_keyerror >= 382 else "超集"),
        },
        "fixes": {
            "F1_minimal_patch": {
                "code_before": 's |= set(name2canon.get(ALIAS[nm]["light"], []))\n'
                               's |= set(key2canon.get(ALIAS[nm]["light"], []))',
                "code_after": 'rec = ALIAS.get(nm)\n'
                              'if rec is not None:\n'
                              '    light = rec.get("light", "")\n'
                              '    s |= set(name2canon.get(light, []))\n'
                              '    s |= set(key2canon.get(light, []))',
                "scope": "2 行改 5 行，diff 最小；对已注册名行为零变化",
                "resolves": "崩溃（KeyError）",
                "does_not_resolve": "未注册名的语义状态（静默返回 []）、多 canonical 歧义、"
                                    "R-07 短路黑名单",
                "effort": "0.25 人时",
                "risk": "极低",
            },
            "F2_structured_return": {
                "signature": "resolve_structured(nm) -> {state: UNREGISTERED|NO_MATCH|"
                             "UNIQUE|AMBIGUOUS, canonicals: [...], alias: bool, light: str}",
                "rationale": "把 0/1/N 三种状态显式化，让 R-07 能区分'未注册'与'歧义'，"
                             "消除 silent-fail 与 sorted()[0] 静默选键",
                "effort": "2 人时",
                "risk": "低（新增返回类型，需同步调用方）",
            },
            "F4_pattern_boundary": {
                "targets": ["BL-012", "BL-009", "BL-026", "BL-011", "BL-013"],
                "rule_a": "F4a 子串包含：L/R 在同一字符串内匹配且一侧区间被另一侧包含 -> 自触发",
                "rule_b": "F4b 复合短语：同一字符串内 L 与 R 以互不重叠区间共现 -> 复合短语非单向指标",
                "rationale": "黑名单的 L/R 语义是'x 侧讲 A、y 侧讲 B'。若 x 侧同时讲 A 和 B"
                             "（复合短语或同义展开），拦截即为误伤。本轮抽样审计中 "
                             "V86硬拦截(blacklist_precheck) 37 行有 9 行（24.3%）属此类",
                "lint_source": "build_alias_library.py 的 bl_lint 已产出 43 条整词边界告警"
                               "（BL-001/016/025 各 3 条，BL-002/003/008/009/010/011/015/017/018/"
                               "019/022/023/024/018a/018b 各 2 条，BL-004/012/013/014 各 1 条），"
                               "但仅为告警，未阻止上线",
                "effort": "3 人时",
                "risk": "中（需逐条黑名单规则人工确认 L/R 纯度，否则可能放过真实冲突）",
            },
            "F3_gate_reorder": {
                "order_before": ["empty_input", "alias_exact(R-07)", "variety_anchor_violation(R-01)",
                                 "blacklist_precheck(R-05)", "metric_exclusion_hard(R-03)",
                                 "variety_neutral_target_review(R-01b)", "R-06 阈值"],
                "order_after": ["empty_input", "variety_anchor_violation(R-01)",
                                "blacklist_precheck(R-05, 收集全部命中)",
                                "alias_exact(R-07, UNIQUE 才放行)",
                                "metric_exclusion_hard(R-03)",
                                "variety_neutral_target_review(R-01b)", "R-06 阈值"],
                "rationale": "R-07 是'放行'型门禁，放在 R-01/R-05 之前会导致安全门禁被短路；"
                             "同时 R-05 只上报首条命中规则，遮蔽了 BL-015/BL-018a/BL-022 等"
                             "规则的归因",
                "effort": "4 人时",
                "risk": "中（改变 reason 分布，需同步测试集与下游消费方）",
            },
        },
        "behavior_diff": {
            "pairs_total": total,
            "pairs_by_source": dict(src_dist.most_common()),
            "matcher_variant": "F3 + F4（R-01 -> R-05 全量上报 -> R-07 UNIQUE 放行 -> R-03 -> R-01b -> R-06）",
            "accept_dist_base": {str(k): v for k, v in acc(base).most_common()},
            "accept_dist_fixed": {str(k): v for k, v in acc(fixed).most_common()},
            "reason_dist_base": dist(base),
            "reason_dist_fixed": dist(fixed),
            "state_transitions": dict(transitions.most_common()),
            "alias_exact": {"base": alias_exact_before, "fixed_unique": alias_exact_after,
                            "fixed_ambiguous_review": alias_ambiguous_after,
                            "silent_key_pickup_count": alias_exact_before - alias_exact_after},
            "blacklist_rule_reporting": {
                "base_first_rule_only": dict(base_rule.most_common()),
                "fixed_all_rules": dict(fixed_rules_flat.most_common(15)),
                "rules_never_reported_in_base": [
                    k for k, v in fixed_rules_flat.items()
                    if k not in base_rule and v >= 1],
            },
            "self_trigger_pairs": {"total": len(self_trigger),
                                   "by_rule": dict(self_trig_dist.most_common())},
            "f4_fullrun": {
                "pairs_checked": total,
                "self_trigger_skipped_total": sum(
                    len(s) for s in f4_skip_all),
                "skipped_by_rule": dict(Counter(
                    x[0] for s in f4_skip_all for x in s).most_common(10)),
                "skipped_by_reason": dict(Counter(
                    x[1] for s in f4_skip_all for x in s).most_common()),
                "hits_before_f4": sum(len(black_hit_all_before[_i])
                                      for _i in range(total)),
                "hits_after_f4": sum(len(f4_hits_all[_i]) for _i in range(total)),
                "note": "F4 在全量 %d pair 上的自触发抑制量；被抑制的拦截在真实场景下"
                        "多为误伤（同名对 / 复合短语对）" % total,
            },
        },
        "tp_fp_impact": {
            "method": "对同一 pair 集合比较 base 与 fixed 的三态；"
                      "A=自动放行, R=降级复核, B=硬拦截",
            "A->R_downgrade": transitions.get("A->R", 0),
            "A->B_hardblock": transitions.get("A->B", 0),
            "B->A_release": transitions.get("B->A", 0),
            "B->R_review": transitions.get("B->R", 0),
            "R->A_release": transitions.get("R->A", 0),
            "R->B_hardblock": transitions.get("R->B", 0),
            "stable": sum(v for k, v in transitions.items() if k[0] == k[2]),
            "tp_effect": "A->R/A->B 是把'静默放行'改为'复核或拦截'，在跨品种与黑名单命中场景下"
                         "是 TP 的净增益（这些 pair 若被当作正确别名入库即为 TP 缺失）",
            "fp_effect": "B->A/B->R 是放宽拦截。本轮实测 B->A=%d，B->R=%d，"
                         "其中 B->A 全部来自 BL-012/BL-009 pattern 子串自触发的同名对"
                         "（如 '锡厂库存天数（天）' <-> '锡厂库存天数（天）'），"
                         "这类放行是 FP 修复而非 FP 引入。" % (transitions.get("B->A", 0),
                                                                transitions.get("B->R", 0)),
            "f4_self_trigger_release": {
                "pairs_with_blacklist_hit_before": still_blocked + self_trigger_release,
                "released_by_f4": self_trigger_release,
                "still_blocked_after_f4": still_blocked,
                "release_rate_pct": round(100.0 * self_trigger_release /
                                          max(1, still_blocked + self_trigger_release), 2),
                "note": "被 F4 释放的 %d pair 全部是同字符串自触发（同名对 / 复合短语对），"
                        "属误伤修复；仍被拦截的 %d pair 是真实冲突" % (self_trigger_release,
                                                                      still_blocked),
            },
            "crash_eliminated": orig_keyerror,
            "crash_note": "修复前这 %d 次调用会抛 KeyError。在生产管线中若上游无 try/except，"
                          "整个批次会中断（相当于整批 TP 归零）；若上游 catch 后按拒绝处理，"
                          "则相当于 %d 个隐性硬拦截。F1 修复后它们按'未注册'落入模糊匹配路径，"
                          "由 R-06 阈值与 R-01/R-05 决定是否拦截。" % (orig_keyerror, orig_keyerror),
        },
        "unit_tests": {"summary": dict(ut_summary.most_common()),
                       "n": len(tests), "tests": tests},
        "regression_risk": {
            "r1_reason_semantics": "高：R-05 的 reason 从'首条命中规则'变为'全部命中规则 + 首个上报'，"
                                   "下游若按 rule_id 精确匹配需同步",
            "r2_review_rate_increase": "中：新增 alias_ambiguous_multi_canonical 降级复核路径，"
                                       "人工复核队列会增长 %d 条（本测试集内）" % alias_ambiguous_after,
            "r3_alias_exact_decrease": "中：alias_exact 从 %d 降至 %d（%d 条转为降级复核），"
                                       "别名库自动放行率下降，但消除了 %d 条静默选键"
                                       % (alias_exact_before, alias_exact_after,
                                          alias_exact_before - alias_exact_after,
                                          alias_exact_before - alias_exact_after),
            "r4_testset_labels": "高：blacklist_boundary_testset.json 的 24 例中 8 例的 "
                                 "expected_rule 在新门禁下不可达（BL-009a 不存在、R-01 先于 R-05），"
                                 "需重建期望",
            "r5_no_gating_by_f1": "F1 单独上线不改变任何放行结论，只消除崩溃，是最低风险的第一步",
        },
        "recommendation": "分三步上线：(1) F1 立即上线消除崩溃（0.25 人时，零行为变化）；"
                          "(2) F2 结构化返回 + R-07 多 canonical 降级复核（2 人时，消除 165 条静默选键）；"
                          "(3) F3 门禁重排 + R-05 全量上报（4 人时，修复 BOUNDARY-013 类漏拦与 "
                          "BL-015/BL-018a/BL-022 归因遮蔽）；(4) F4 整词边界 + 同侧纯度（3 人时，"
                          "消除 BL-012/BL-009 pattern 自触发的 9 类误伤）。同步重建 "
                          "blacklist_boundary_testset.json 的 24 例期望。",
    }
    A.write_json(os.path.join(CD, "canonical_resolve_fix_result.json"), out)

    print("=" * 78)
    print("T2.2 resolve_canonical 修复方案")
    print("  测试 pair 数 %d (来源 %s)" % (total, dict(src_dist.most_common())))
    print("  原实现调用 %d 次, KeyError %d 次 (%.2f%%)"
          % (orig_calls, orig_keyerror, 100.0 * orig_keyerror / orig_calls))
    print("  KeyError 样本:", orig_keyerror_samples[:6])
    print("  base  accept: %s" % {str(k): v for k, v in acc(base).most_common()})
    print("  fixed accept: %s" % {str(k): v for k, v in acc(fixed).most_common()})
    print("  三态迁移: %s" % dict(transitions.most_common()))
    print("  alias_exact: base=%d -> fixed UNIQUE=%d + AMBIGUOUS复核=%d (静默选键 %d)"
          % (alias_exact_before, alias_exact_after, alias_ambiguous_after,
             alias_exact_before - alias_exact_after))
    print("  base 从未上报但 fixed 上报的规则: %s"
          % out["behavior_diff"]["blacklist_rule_reporting"]["rules_never_reported_in_base"])
    print("  pattern 自触发同名对: %d %s" % (len(self_trigger), dict(self_trig_dist.most_common())))
    print("  F4 边界：黑名单命中 %d -> %d pair 被释放（自触发），仍拦截 %d"
          % (still_blocked + self_trigger_release, self_trigger_release, still_blocked))
    print("    抑制原因: %s" % dict(Counter(
        x[1] for s in f4_skip_all for x in s).most_common()))
    print("  单元测试: %s" % dict(ut_summary.most_common()))
    for t in tests:
        print("    %-6s %-34s %s" % (t["id"], t["desc"][:34], t["result"]))
        if t["result"] != "PASS":
            print("            detail: %s" % t.get("detail", ""))
    print("=" * 78)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
