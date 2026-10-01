# -*- coding: utf-8 -*-
"""
v86_alias_engine_prototype.py
==========================================================================
V86 四层别名引擎原型实现（F1 / F2 / F3 / F4）
==========================================================================

任务: DSHE_V86_ALIAS_ENGINE_PROTOTYPE_AND_CONFLICT_REGRESSION
分支: feature/v85-chart-template
基线: DSHE B commit f313570 (V85 alias audit)
      E commit bcd64dd (V86 backend schema + task API design)

架构:
  P0 归一化  →  P1 特征提取  →  P2 规范解析(F1+F2)  →  P3 门禁裁决链  →  P4 裁决契约

四层修复档:
  F1  异常兜底       resolve_canonical 未命中返回 [] (不抛 KeyError)
  F2  确定性解析     多 canonical 交集排序取稳定序 + 结构化状态
  F3  门禁重排       R-01 → R-05(全量上报) → R-07 (alias_exact 后移)
  F4  自触发抑制     F4a 子串包含抑制 / F4b 不相交共现抑制

模式切换:
  base      = 原 V85 门禁顺序 (R-07 先, R-05 后, 首命中即返回)
  f3        = F3 单独上线 (R-05 前移+全量上报, 无 F4 自触发抑制)
  f3+f4     = F3+F4 组合上线 (推荐生产模式)

硬约束:
  - 只读加载 V85 引擎源码 (exec build_alias_library.py 1..655)
  - 不修改任何 V85 冻结数据
  - 不调用 zhiji API
  - 不覆盖 V85 交付物

用法:
  # 冒烟自测
  python v86_alias_engine_prototype.py --smoke

  # 回归 165 冲突样本 (输出 JSON)
  python v86_alias_engine_prototype.py --regression

  # 运行指定测试用例
  python v86_alias_engine_prototype.py --run-tests alias_v86_extended_test_case.json

依赖 (只读, 全部在 V85 交付物中):
  analysis/e2e_output/v85/dshe_alias_audit_design/audit_kit.py
  analysis/e2e_output/v85/dshe_alias_integrate_test/v86_kit.py
  analysis/e2e_output/v85/dshe_alias_audit_design/multi_canonical_conflicts_165.csv
  analysis/e2e_output/v85/dshe_alias_audit_design/multi_canonical_conflict_classification.csv
"""

import os
import sys
import json
import time
import datetime
import hashlib
import csv
from collections import Counter, defaultdict
from copy import deepcopy

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
CD = os.path.dirname(os.path.abspath(__file__))
REPO = r"D:\DSH_WORK\framework-tree"
V85 = os.path.join(REPO, "analysis", "e2e_output", "v85")

# V85 输入 (全部只读)
AUDIT_KIT_DIR = os.path.join(V85, "dshe_alias_audit_design")
V86_KIT_DIR = os.path.join(V85, "dshe_alias_integrate_test")
CONFLICTS_165_CSV = os.path.join(AUDIT_KIT_DIR, "multi_canonical_conflicts_165.csv")
CLASSIFICATION_CSV = os.path.join(AUDIT_KIT_DIR, "multi_canonical_conflict_classification.csv")
TEST_CASE_SET_JSON = os.path.join(AUDIT_KIT_DIR, "alias_test_case_set.json")

# V86 输出
OUT_DIR = CD

TASK_ID = "DSHE_V86_ALIAS_ENGINE_PROTOTYPE_AND_CONFLICT_REGRESSION"
BASE_COMMIT = "f313570"
E_COMMIT = "bcd64dd"

# ---------------------------------------------------------------------------
# 加载引擎
# ---------------------------------------------------------------------------


def load_engine():
    """加载 V85 线上判定引擎 + 黑名单, 返回 (M, engine_meta, guard_stat, rules, bl_lr)."""
    sys.path.insert(0, AUDIT_KIT_DIR)
    sys.path.insert(0, V86_KIT_DIR)
    import audit_kit as A
    import v86_kit as K

    M = K.load_engine()
    eng_meta = {
        "source": "analysis/e2e_output/v85/alias_match_presearch/build_alias_library.py",
        "loaded_lines": "1..%d" % (M.get("_cut_line") or 655),
        "source_md5": M.get("_src_md5", ""),
        "source_sha256": M.get("_src_sha256", ""),
    }
    guard = K.guard_resolve_canonical(M)
    BL_FINAL = os.path.join(V85, "dshb_full_integrate", "semantic_blacklist_v85_final.json")
    bl_final = json.load(open(BL_FINAL, encoding="utf-8"))
    rules = {r["rule_id"]: r for r in bl_final["rules"]}
    bl_lr, bl_lint = K.build_bl_lr(M, rules)
    old_bl_lr = K.apply_rules(M, bl_lr)
    return M, eng_meta, guard, rules, bl_lr, bl_lint


# ---------------------------------------------------------------------------
# F1: 异常兜底 (resolve_safe)
# ---------------------------------------------------------------------------

def build_resolve_safe(M):
    """F1: resolve_canonical 未命中返回空列表, 不抛 KeyError.

    零行为变化: 只改变异常路径, 不改变任何命中路径的返回值.
    """
    ALIAS = M["ALIAS"]
    name2canon = M["name2canon"]
    key2canon = M["key2canon"]
    stat = {"calls": 0, "alias_hit": 0, "alias_miss": 0,
            "miss_samples": [], "guard_hits": 0}

    def resolve_safe(nm):
        stat["calls"] += 1
        s = set()
        s |= set(name2canon.get(nm, []))
        s |= set(key2canon.get(nm, []))
        rec = ALIAS.get(nm)
        if rec is None:
            stat["alias_miss"] += 1
            stat["guard_hits"] += 1
            if len(stat["miss_samples"]) < 12:
                stat["miss_samples"].append(nm)
            return sorted(s)
        stat["alias_hit"] += 1
        light = rec.get("light", "")
        s |= set(name2canon.get(light, []))
        s |= set(key2canon.get(light, []))
        return sorted(s)

    return resolve_safe, stat


# ---------------------------------------------------------------------------
# F2: 确定性解析 (resolve_structured)
# ---------------------------------------------------------------------------

def build_resolve_structured(M):
    """F2: 结构化解析, 显式表达 0/1/N 三种状态.

    返回 dict: {state, canonicals, alias, light, ambiguity_ratio}
    state: UNREGISTERED | NO_MATCH | UNIQUE | AMBIGUOUS
    """
    ALIAS = M["ALIAS"]
    name2canon = M["name2canon"]
    key2canon = M["key2canon"]
    stat = {"calls": 0, "n0": 0, "n1": 0, "nN": 0}

    def resolve_structured(nm):
        stat["calls"] += 1
        rec = ALIAS.get(nm)
        if rec is None:
            stat["n0"] += 1
            return {"state": "UNREGISTERED", "canonicals": [], "alias": False,
                    "light": "", "ambiguity_ratio": 0.0}
        light = rec.get("light", "")
        s = set()
        s |= set(name2canon.get(nm, []))
        s |= set(key2canon.get(nm, []))
        s |= set(name2canon.get(light, []))
        s |= set(key2canon.get(light, []))
        s = sorted(s)
        if not s:
            stat["n0"] += 1
            return {"state": "NO_MATCH", "canonicals": [], "alias": True,
                    "light": light, "ambiguity_ratio": 0.0}
        elif len(s) == 1:
            stat["n1"] += 1
            return {"state": "UNIQUE", "canonicals": s, "alias": True,
                    "light": light, "ambiguity_ratio": 0.0}
        else:
            stat["nN"] += 1
            return {"state": "AMBIGUOUS", "canonicals": s, "alias": True,
                    "light": light, "ambiguity_ratio": round(len(s) / 10.0, 4)}

    return resolve_structured, stat


# ---------------------------------------------------------------------------
# F4: 自触发抑制 (整词边界 + 同侧纯度)
# ---------------------------------------------------------------------------

def blacklist_check_bounded(M, a, b):
    """F4: 整词边界 + 同侧纯度版黑名单检查.

    修复两类 pattern 误触发:
      F4a 子串包含: L/R 在同一字符串内匹配且一侧区间被另一侧完全包含
                    (如 BL-012: '库存' ⊂ '库存天数') -> 自触发, 跳过该方向.
      F4b 复合短语: 同一字符串内 L 与 R 以严格不相交区间同时出现
                    (如 BL-009: '碳酸锂利润与需求分析' 同时含 '利润' 与 '需求')
                    -> 复合短语非单向指标, 跳过该方向.
    跨字符串的真实冲突不受影响.

    返回 (hits[list], skipped[list of (rid, reason, lp, rp)]).
    """
    hits, skipped = [], []
    for rid, (Ls, Rs, sev, nm) in M["BL_LR"].items():
        fired = False
        for x, y in ((a, b), (b, a)):
            for lp in Ls:
                i = x.find(lp)
                if i < 0:
                    continue
                for rp in Rs:
                    j = y.find(rp)
                    if j < 0:
                        continue
                    # F4a: 同字符串值相等时的子串包含
                    if x == y:
                        if (j <= i and j + len(rp) >= i + len(lp)) or \
                           (i <= j and i + len(lp) >= j + len(rp)):
                            skipped.append((rid, "F4a_span_contained", lp, rp))
                            continue
                    # F4b: 同侧纯度 - x 侧含 R 的独立区间或 y 侧含 L 的独立区间
                    impure = False
                    for rp2 in Rs:
                        k = x.find(rp2)
                        if k < 0:
                            continue
                        if k + len(rp2) < i or i + len(lp) < k:
                            impure = True
                            break
                    if not impure:
                        for lp2 in Ls:
                            k = y.find(lp2)
                            if k < 0:
                                continue
                            if k + len(lp2) < j or j + len(rp) < k:
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


def blacklist_check_plain(M, a, b):
    """F3-only 黑名单检查 (无 F4 抑制): 简单子串匹配 + 全量上报."""
    hits = []
    for rid, (Ls, Rs, sev, nm) in M["BL_LR"].items():
        if (any(p in a for p in Ls) and any(p in b for p in Rs)) or \
           (any(p in b for p in Ls) and any(p in a for p in Rs)):
            hits.append(rid)
    return hits


def blacklist_check_v85(M, a, b):
    """V85 基线黑名单检查: 首命中即返回 (无全量上报)."""
    for rid, (Ls, Rs, sev, nm) in M["BL_LR"].items():
        if (any(p in a for p in Ls) and any(p in b for p in Rs)) or \
           (any(p in b for p in Ls) and any(p in a for p in Rs)):
            return [rid]
    return []


# ---------------------------------------------------------------------------
# F3: 门禁重排 (R-01 → R-05 → R-07)
# ---------------------------------------------------------------------------

def build_v86_matcher(M, resolve_safe, use_f4=True):
    """V86 门禁裁决链.

    参数:
      M: 引擎命名空间
      resolve_safe: F1 安全解析器
      use_f4: True=F3+F4, False=F3-only (无自触发抑制)

    返回: 可调用的 matcher 函数 (a_raw, b_raw) -> verdict dict
    """

    def v86_matcher(a_raw, b_raw):
        # P0: 归一化
        a = M["norm_full"](a_raw)[0]
        b = M["norm_full"](b_raw)[0]

        # L0: 输入校验
        if not a or not b:
            return _verdict("BLOCK", "empty_input", dice=0.0)

        d = M["dice"](a, b)
        pa = M["primary_metric"](a)
        pb = M["primary_metric"](b)
        fa = M["metal_families"](a)
        fb = M["metal_families"](b)

        all_rules = []
        hit_fragments = []
        incomplete = False

        # L1-1: R-01 品种锚点
        if fa and fb and not (set(fa) & set(fb)):
            all_rules.append("R-01_variety_anchor")
            return _verdict("BLOCK", "variety_anchor_violation",
                            all_rules=all_rules, hit_fragments=["%s vs %s" % (fa, fb)],
                            dice=d, incomplete=incomplete)

        # L1-2: R-03-HARD 度量词硬冲突 (提前到 R-05 前, 但仅收集不裁决)
        lvl, pair = M["metric_conflict"](pa, pb)
        if lvl == "HARD":
            all_rules.append("R-03H_metric_hard")

        # L1-3: R-05 黑名单 (F3 前移)
        if use_f4:
            hits, self_trig = blacklist_check_bounded(M, a, b)
        else:
            hits = blacklist_check_plain(M, a, b)
            self_trig = []

        all_rules.extend("R-05_%s" % h for h in hits)

        if hits:
            for h in hits:
                Ls, Rs, sev, nm = M["BL_LR"][h]
                # 收集命中片段
                for lp in Ls:
                    if lp in a:
                        hit_fragments.append("%s:L:%s" % (h, lp))
                    if lp in b:
                        hit_fragments.append("%s:L:%s" % (h, lp))
                for rp in Rs:
                    if rp in a:
                        hit_fragments.append("%s:R:%s" % (h, rp))
                    if rp in b:
                        hit_fragments.append("%s:R:%s" % (h, rp))
            return _verdict("BLOCK", "blacklist_precheck",
                            all_rules=all_rules, hit_fragments=hit_fragments,
                            self_trigger_skipped=[
                                {"rule": s[0], "reason": s[1], "lp": s[2], "rp": s[3]}
                                for s in self_trig] if self_trig else None,
                            dice=d, incomplete=incomplete)

        # L2: R-07 别名精确匹配 (F3 后移)
        ca = resolve_safe(a)
        cb = resolve_safe(b)
        inter = sorted(set(ca) & set(cb))

        if ca and cb:
            if not inter:
                pass  # 无交集, 继续到 L3
            elif len(inter) == 1:
                # UNIQUE: 放行
                return _verdict("PASS", "alias_exact",
                                canonical=inter[0], dice=d,
                                all_rules=all_rules, hit_fragments=hit_fragments,
                                incomplete=incomplete)
            else:
                # AMBIGUOUS: 降级复核 (F2 确定性 + 多 canonical 不静默选键)
                return _verdict("REVIEW", "alias_ambiguous_multi_canonical",
                                canonicals=inter, dice=d,
                                all_rules=all_rules, hit_fragments=hit_fragments,
                                incomplete=incomplete)

        # L3: 兜底裁决
        # L3-1: R-03-HARD (现在才裁决)
        if lvl == "HARD":
            return _verdict("BLOCK", "metric_exclusion_hard",
                            all_rules=all_rules, hit_fragments=hit_fragments,
                            detail="%s vs %s" % pair, dice=d,
                            incomplete=incomplete)

        # L3-2: R-01b 品种中性降级
        if (fa and not fb) or (fb and not fa):
            nw = M.get("NEUTRAL_WHITELIST", set())
            nc = M.get("NEUTRAL_WHITELIST_CANON", set())
            if not (((a, b) in nw) or (b in nc) or (a in nc)):
                return _verdict("REVIEW", "variety_neutral_target_review",
                                all_rules=all_rules, hit_fragments=hit_fragments,
                                detail="query_variety=%s target_variety=%s"
                                       % (fa or ["-"], fb or ["-"]),
                                dice=d, incomplete=incomplete)

        # L3-3: R-06 dice 阈值
        soft = "metric_exclusion_soft:%s/%s" % pair if lvl == "SOFT" else ""
        TH_HIGH = M.get("TH_HIGH", 0.85)
        TH_MID = M.get("TH_MID", 0.70)
        TH_LOW = M.get("TH_LOW", 0.50)

        if d >= TH_HIGH:
            return _verdict("PASS", "high_dice", dice=d,
                            all_rules=all_rules, hit_fragments=hit_fragments,
                            soft_flag=soft, incomplete=incomplete)
        if d >= TH_MID and (not fa or not fb or set(fa) & set(fb)):
            return _verdict("PASS", "mid_dice_same_variety", dice=d,
                            all_rules=all_rules, hit_fragments=hit_fragments,
                            soft_flag=soft, incomplete=incomplete)
        if d >= TH_LOW and (not fa or not fb):
            return _verdict("PASS", "low_dice_no_variety", dice=d,
                            all_rules=all_rules, hit_fragments=hit_fragments,
                            soft_flag=soft, incomplete=incomplete)

        return _verdict("BLOCK", "below_threshold", dice=d,
                        all_rules=all_rules, hit_fragments=hit_fragments,
                        soft_flag=soft, incomplete=incomplete)

    return v86_matcher


def build_v85_matcher(M, resolve_safe):
    """V85 基线 matcher (R-07 先, R-05 后, 首命中即返回)."""

    def v85_matcher(a_raw, b_raw):
        a = M["norm_full"](a_raw)[0]
        b = M["norm_full"](b_raw)[0]
        if not a or not b:
            return _verdict("BLOCK", "empty_input", dice=0.0)

        d = M["dice"](a, b)
        pa = M["primary_metric"](a)
        pb = M["primary_metric"](b)
        fa = M["metal_families"](a)
        fb = M["metal_families"](b)

        # R-07 别名精确匹配 (V85: 放在最前面)
        ca = resolve_safe(a)
        cb = resolve_safe(b)
        inter = sorted(set(ca) & set(cb))
        if ca and cb and inter:
            # V85: 直接取 sorted()[0] 静默选键
            return _verdict("PASS", "alias_exact",
                            canonical=inter[0], dice=d)

        # R-01 品种锚点
        if fa and fb and not (set(fa) & set(fb)):
            return _verdict("BLOCK", "variety_anchor_violation",
                            dice=d)

        # R-05 黑名单 (V85: 首命中即返回, 无全量上报)
        bl_hits = blacklist_check_v85(M, a, b)
        if bl_hits:
            return _verdict("BLOCK", "blacklist_precheck",
                            rule=bl_hits[0], dice=d)

        # R-03 口径互斥
        lvl, pair = M["metric_conflict"](pa, pb)
        if lvl == "HARD":
            return _verdict("BLOCK", "metric_exclusion_hard",
                            detail="%s vs %s" % pair, dice=d)

        # R-01b 品种中性降级
        if (fa and not fb) or (fb and not fa):
            nw = M.get("NEUTRAL_WHITELIST", set())
            nc = M.get("NEUTRAL_WHITELIST_CANON", set())
            if not (((a, b) in nw) or (b in nc) or (a in nc)):
                return _verdict("REVIEW", "variety_neutral_target_review",
                                dice=d)

        # R-06 阈值
        TH_HIGH = M.get("TH_HIGH", 0.85)
        TH_MID = M.get("TH_MID", 0.70)
        TH_LOW = M.get("TH_LOW", 0.50)
        soft = "metric_exclusion_soft:%s/%s" % pair if lvl == "SOFT" else ""

        if d >= TH_HIGH:
            return _verdict("PASS", "high_dice", dice=d, soft_flag=soft)
        if d >= TH_MID and (not fa or not fb or set(fa) & set(fb)):
            return _verdict("PASS", "mid_dice_same_variety", dice=d, soft_flag=soft)
        if d >= TH_LOW and (not fa or not fb):
            return _verdict("PASS", "low_dice_no_variety", dice=d, soft_flag=soft)

        return _verdict("BLOCK", "below_threshold", dice=d, soft_flag=soft)

    return v85_matcher


# ---------------------------------------------------------------------------
# 裁决契约
# ---------------------------------------------------------------------------

def _verdict(verdict, reason, **kwargs):
    """构造标准裁决 dict."""
    base = {
        "verdict": verdict,
        "reason": reason,
        "all_rules": kwargs.pop("all_rules", []),
        "hit_fragments": kwargs.pop("hit_fragments", []),
        "incomplete": kwargs.pop("incomplete", False),
        "dice": kwargs.pop("dice", 0.0),
    }
    for k, v in kwargs.items():
        base[k] = v
    return base


# ---------------------------------------------------------------------------
# 引擎工厂
# ---------------------------------------------------------------------------

class V86AliasEngine:
    """V86 别名引擎门面类, 封装 F1/F2/F3/F4 全部修复档."""

    VALID_MODES = ("base", "f3", "f3+f4")

    def __init__(self, mode="f3+f4"):
        """初始化引擎.

        mode: "base" | "f3" | "f3+f4"
          base    = V85 原始门禁顺序 (对照组)
          f3      = F3 单独上线 (R-05 前移+全量上报, 无 F4)
          f3+f4   = F3+F4 组合上线 (推荐生产模式)
        """
        if mode not in self.VALID_MODES:
            raise ValueError("mode must be one of %s, got %r" % (self.VALID_MODES, mode))

        self.mode = mode
        t0 = time.perf_counter()
        self.M, self.eng_meta, self.guard_stat, self.rules, self.bl_lr, self.bl_lint = \
            load_engine()
        self._resolve_safe, self.f1_stat = build_resolve_safe(self.M)
        self._resolve_structured, self.f2_stat = build_resolve_structured(self.M)

        if mode == "base":
            self.matcher = build_v85_matcher(self.M, self._resolve_safe)
        elif mode == "f3":
            self.matcher = build_v86_matcher(self.M, self._resolve_safe, use_f4=False)
        else:  # f3+f4
            self.matcher = build_v86_matcher(self.M, self._resolve_safe, use_f4=True)

        self._init_time = time.perf_counter() - t0

    def decide(self, a_raw, b_raw):
        """对一对别名输入运行裁决, 返回标准裁决 dict."""
        t0 = time.perf_counter()
        result = self.matcher(a_raw, b_raw)
        result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        return result

    def resolve(self, alias_name):
        """F2 结构化解析: 返回 canonical 状态."""
        return self._resolve_structured(
            self.M["norm_full"](alias_name)[0])

    def resolve_safe(self, alias_name):
        """F1 安全解析: 返回 canonical 列表."""
        return self._resolve_safe(
            self.M["norm_full"](alias_name)[0])

    @property
    def version_info(self):
        """引擎版本信息."""
        return {
            "engine": "V86AliasEngine",
            "mode": self.mode,
            "f1_enabled": True,
            "f2_enabled": True,
            "f3_enabled": self.mode in ("f3", "f3+f4"),
            "f4_enabled": self.mode == "f3+f4",
            "blacklist_rules": len(self.bl_lr),
            "alias_entries": self.guard_stat.get("total_alias_entries", 0),
            "init_time_ms": round(self._init_time * 1000, 1),
        }

    def summary_stats(self):
        """引擎运行统计."""
        return {
            "f1": {
                "total_calls": self.f1_stat["calls"],
                "alias_hits": self.f1_stat["alias_hit"],
                "alias_misses": self.f1_stat["alias_miss"],
                "guard_hits": self.f1_stat["guard_hits"],
                "miss_rate_pct": round(
                    100.0 * self.f1_stat["alias_miss"] / max(1, self.f1_stat["calls"]), 2),
            },
            "f2": {
                "total_calls": self.f2_stat["calls"],
                "unregistered": self.f2_stat["n0"],
                "unique": self.f2_stat["n1"],
                "ambiguous": self.f2_stat["nN"],
            },
            "engine": self.version_info,
        }


# ---------------------------------------------------------------------------
# 冒烟自测
# ---------------------------------------------------------------------------

def smoke_test():
    """冒烟自测: 验证 F1/F2/F3/F4 全部修复档工作正常."""
    print("=" * 78)
    print("V86 别名引擎原型 · 冒烟自测")
    print("=" * 78)

    checks = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        checks.append({"name": name, "status": status, "detail": detail})
        print("  [%s] %s" % (status, name))
        if detail:
            print("         %s" % detail)

    # --- 引擎加载 ---
    eng = V86AliasEngine("f3+f4")
    check("引擎加载", eng.M is not None,
          "mode=%s, %d rules, %d alias entries, init %.1fms"
          % (eng.mode, eng.version_info["blacklist_rules"],
             eng.version_info["alias_entries"], eng.version_info["init_time_ms"]))

    # --- F1: 异常兜底 ---
    r1 = eng.resolve_safe("产量")  # 未注册名
    check("F1: 未注册名返回空列表", isinstance(r1, list) and r1 == [],
          "resolve_safe('产量') -> %s" % r1)

    r1b = eng.resolve_safe("碳酸锂工厂库存天数")  # 已注册名
    check("F1: 已注册名正常解析", isinstance(r1b, list) and len(r1b) >= 1,
          "resolve_safe('碳酸锂工厂库存天数') -> %d canonicals" % len(r1b))

    # --- F2: 确定性解析 ---
    r2a = eng.resolve("产量")
    check("F2: 未注册名 state=UNREGISTERED", r2a["state"] == "UNREGISTERED",
          "state=%s" % r2a["state"])

    r2b = eng.resolve("碳酸锂工厂库存天数")
    check("F2: 已注册名 state=UNIQUE 或 AMBIGUOUS",
          r2b["state"] in ("UNIQUE", "AMBIGUOUS"),
          "state=%s, canonicals=%d" % (r2b["state"], len(r2b["canonicals"])))

    _gfex = eng.M["norm_full"]("GFEX：工业硅：主力合约：单边交易：持仓量（日）")[0]
    r2c = eng.resolve(_gfex)
    check("F2: 多 canonical 冲突 state=AMBIGUOUS",
          r2c["state"] == "AMBIGUOUS" and len(r2c["canonicals"]) > 1,
          "state=%s, %d canonicals" % (r2c["state"], len(r2c["canonicals"])))

    # --- F3: 门禁重排 ---
    # R-01: 跨品种应被阻断
    r3a = eng.decide("LME：锌：库存（日）", "LME：锡：库存（日）")
    check("F3: R-01 跨品种阻断", r3a["verdict"] == "BLOCK" and
          r3a["reason"] == "variety_anchor_violation",
          "verdict=%s reason=%s" % (r3a["verdict"], r3a["reason"]))

    # R-05 黑名单阻断 (用跨字符串 pair: "碳酸锂利润" 含 L=利润, "碳酸锂需求" 含 R=需求 -> BL-009)
    r3b = eng.decide("碳酸锂利润", "碳酸锂需求")
    check("F3: R-05 黑名单阻断 (BL-009 利润vs需求)",
          r3b["verdict"] == "BLOCK" and r3b["reason"] == "blacklist_precheck",
          "verdict=%s reason=%s all_rules=%s"
          % (r3b["verdict"], r3b["reason"], r3b.get("all_rules", [])))

    # R-07: 多键别名降级复核 (用 165 冲突样本的第一条)
    _single = None
    for r in _read_csv(CONFLICTS_165_CSV):
        if r.get("alias_norm"):
            _single = r["alias_norm"]
            break
    if _single:
        ca = eng.resolve_safe(_single)
        if len(ca) == 1:
            r3c = eng.decide(_single, _single)
            check("F3: R-07 单键别名放行", r3c["verdict"] == "PASS",
                  "verdict=%s reason=%s" % (r3c["verdict"], r3c["reason"]))
        else:
            r3c = eng.decide(_single, _single)
            check("F3: R-07 多键别名降级复核", r3c["verdict"] == "REVIEW",
                  "verdict=%s reason=%s canonicals=%d"
                  % (r3c["verdict"], r3c["reason"], len(r3c.get("canonicals", []))))
    else:
        check("F3: R-07 测试数据缺失", False, "无可用单键别名样本")

    # --- F4: 自触发抑制 ---
    r4a = eng.decide("锡厂库存天数（天）", "锡厂库存天数（天）")
    check("F4a: 同名对自触发抑制 (BL-012)",
          r4a["verdict"] == "PASS",
          "verdict=%s reason=%s (BL-012 库存天数⊃库存 自触发被抑制)"
          % (r4a["verdict"], r4a["reason"]))

    # F4b: 复合短语自触发抑制
    r4b = eng.decide("碳酸锂利润与需求分析", "碳酸锂利润与需求预测")
    check("F4b: 复合短语自触发抑制 (BL-009)",
          r4b["verdict"] in ("PASS", "REVIEW"),
          "verdict=%s reason=%s (BL-009 利润+需求同现被抑制)"
          % (r4b["verdict"], r4b["reason"]))

    # --- F3-only vs F3+F4 模式切换 ---
    eng_f3 = V86AliasEngine("f3")
    eng_base = V86AliasEngine("base")

    # 同名对: base=PASS(alias_exact), f3=BLOCK(blacklist), f3+f4=PASS(F4抑制)
    r_base_self = eng_base.decide("碳酸锂工厂库存天数", "碳酸锂工厂库存天数")
    r_f3_self = eng_f3.decide("碳酸锂工厂库存天数", "碳酸锂工厂库存天数")
    r_f3f4_self = eng.decide("碳酸锂工厂库存天数", "碳酸锂工厂库存天数")

    check("模式切换: base 同名对走 alias_exact 放行",
          r_base_self["verdict"] == "PASS" and r_base_self["reason"] == "alias_exact",
          "base: verdict=%s reason=%s" % (r_base_self["verdict"], r_base_self["reason"]))
    check("模式切换: f3 同名对走 blacklist_precheck 阻断",
          r_f3_self["verdict"] == "BLOCK" and r_f3_self["reason"] == "blacklist_precheck",
          "f3: verdict=%s reason=%s" % (r_f3_self["verdict"], r_f3_self["reason"]))
    check("模式切换: f3+f4 同名对走 alias_exact 放行 (F4 抑制自触发)",
          r_f3f4_self["verdict"] == "PASS",
          "f3+f4: verdict=%s reason=%s" % (r_f3f4_self["verdict"], r_f3f4_self["reason"]))

    # --- all_rules 全量上报 (用跨字符串 pair 确保黑名单命中) ---
    r_rules = eng.decide("碳酸锂利润", "碳酸锂需求")
    check("F3: all_rules 全量上报",
          len(r_rules.get("all_rules", [])) >= 1,
          "all_rules=%s" % r_rules.get("all_rules", []))

    # --- INV-1: L1 命中 -> 永远不是 PASS ---
    inv1_ok = True
    for v in (r3a, r3b):
        if v["verdict"] == "PASS" and v.get("all_rules"):
            inv1_ok = False
    check("INV-1: L1 命中 -> 永远不是 PASS", inv1_ok)

    # --- 空输入 ---
    r_empty = eng.decide("碳酸锂工厂库存天数", "")
    check("L0: 空输入阻断", r_empty["verdict"] == "BLOCK" and
          r_empty["reason"] == "empty_input",
          "verdict=%s reason=%s" % (r_empty["verdict"], r_empty["reason"]))

    # --- 统计 ---
    stats = eng.summary_stats()
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")

    print("-" * 78)
    print("冒烟结果: %d/%d PASS, %d FAIL" % (pass_count, len(checks), fail_count))
    print("F1 统计: %s" % stats["f1"])
    print("F2 统计: %s" % stats["f2"])
    print("=" * 78)

    return checks, stats


# ---------------------------------------------------------------------------
# 回归: 165 冲突样本
# ---------------------------------------------------------------------------

def _read_csv(path):
    """读取 CSV (utf-8-sig)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run_regression():
    """对 165 条多 canonical 冲突样本运行 V85 base vs V86 f3+f4 回归.

    输出 JSON: regression_results.json
    """
    print("=" * 78)
    print("V86 别名引擎原型 · 165 条冲突样本回归")
    print("=" * 78)

    conflicts = _read_csv(CONFLICTS_165_CSV)
    classification = _read_csv(CLASSIFICATION_CSV) if os.path.isfile(
        CLASSIFICATION_CSV) else []
    # 按 alias_id 索引分类信息
    class_map = {r["alias_id"]: r for r in classification if r.get("alias_id")}

    # 初始化三种模式的引擎
    eng_base = V86AliasEngine("base")
    eng_f3 = V86AliasEngine("f3")
    eng_f3f4 = V86AliasEngine("f3+f4")

    results = []
    t0 = time.perf_counter()

    for row in conflicts:
        alias_norm = row.get("alias_norm", "")
        if not alias_norm:
            continue

        aid = row.get("alias_id", "")
        cls = class_map.get(aid, {})
        review_priority = row.get("review_priority", "")
        conflict_class = cls.get("conflict_class", "")
        n_unique_base = int(cls.get("n_unique_base", 0) or 0)
        atomic_keys = row.get("atomic_keys", "").split("|") if row.get("atomic_keys") else []
        canonical_composite = row.get("canonical_key_composite", "")

        # base (V85): alias_norm vs alias_norm (自配对)
        r_base = eng_base.decide(alias_norm, alias_norm)

        # f3 (F3-only)
        r_f3 = eng_f3.decide(alias_norm, alias_norm)

        # f3+f4 (F3+F4 combined)
        r_f3f4 = eng_f3f4.decide(alias_norm, alias_norm)

        # F2 解析状态
        resolve_st = eng_f3f4.resolve(alias_norm)

        # 判定差异
        base_state = _verdict_to_state(r_base)
        f3_state = _verdict_to_state(r_f3)
        f3f4_state = _verdict_to_state(r_f3f4)

        # 是否 F3 改变了 base 的裁决
        diff_base_f3 = base_state != f3_state
        diff_base_f3f4 = base_state != f3f4_state

        rec = {
            "seq": row.get("seq", ""),
            "alias_id": aid,
            "alias_norm": alias_norm[:80],
            "review_priority": review_priority,
            "conflict_class": conflict_class,
            "n_atomic_keys": len(atomic_keys),
            "n_unique_base": n_unique_base,
            "resolve_state": resolve_st["state"],
            "resolve_canonicals_count": len(resolve_st["canonicals"]),

            "base_verdict": base_state,
            "base_reason": r_base.get("reason", ""),
            "base_dice": r_base.get("dice", 0.0),

            "f3_verdict": f3_state,
            "f3_reason": r_f3.get("reason", ""),
            "f3_all_rules": r_f3.get("all_rules", []),

            "f3f4_verdict": f3f4_state,
            "f3f4_reason": r_f3f4.get("reason", ""),
            "f3f4_all_rules": r_f3f4.get("all_rules", []),
            "f3f4_hit_fragments": r_f3f4.get("hit_fragments", []),

            "diff_base_f3": diff_base_f3,
            "diff_base_f3f4": diff_base_f3f4,
            "transition": "%s->%s" % (base_state, f3f4_state),
        }
        results.append(rec)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    # 统计
    total = len(results)
    p_dist = Counter(r["review_priority"] for r in results)
    cls_dist = Counter(r["conflict_class"] for r in results)
    base_dist = Counter(r["base_verdict"] for r in results)
    f3_dist = Counter(r["f3_verdict"] for r in results)
    f3f4_dist = Counter(r["f3f4_verdict"] for r in results)
    reason_dist_f3f4 = Counter(r["f3f4_reason"] for r in results)
    resolve_dist = Counter(r["resolve_state"] for r in results)
    transitions = Counter(r["transition"] for r in results)
    diffs_base_f3 = sum(1 for r in results if r["diff_base_f3"])
    diffs_base_f3f4 = sum(1 for r in results if r["diff_base_f3f4"])

    # P0/P1/P2 子集统计
    p0_results = [r for r in results if r["review_priority"] == "P0_manual"]
    p1_results = [r for r in results if r["review_priority"] in ("P1_auto", "P1_review")]
    p2_results = [r for r in results if r["review_priority"] in ("P2_auto", "P2_merge")]

    summary = {
        "task": TASK_ID,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "engine": {
            "base_commit": BASE_COMMIT,
            "e_commit": E_COMMIT,
            "engine_meta": eng_f3f4.eng_meta,
            "mode_f3f4": eng_f3f4.version_info,
            "mode_f3": eng_f3.version_info,
            "mode_base": eng_base.version_info,
        },
        "regression": {
            "pairs_total": total,
            "elapsed_ms": elapsed,
            "priority_distribution": dict(p_dist.most_common()),
            "conflict_class_distribution": dict(cls_dist.most_common()),
            "base_verdict_distribution": dict(base_dist.most_common()),
            "f3_verdict_distribution": dict(f3_dist.most_common()),
            "f3f4_verdict_distribution": dict(f3f4_dist.most_common()),
            "f3f4_reason_distribution": dict(reason_dist_f3f4.most_common()),
            "resolve_state_distribution": dict(resolve_dist.most_common()),
            "transitions": dict(transitions.most_common()),
            "diffs_base_vs_f3": diffs_base_f3,
            "diffs_base_vs_f3f4": diffs_base_f3f4,
        },
        "p0_subset": {
            "count": len(p0_results),
            "base_dist": dict(Counter(r["base_verdict"] for r in p0_results).most_common()),
            "f3f4_dist": dict(Counter(r["f3f4_verdict"] for r in p0_results).most_common()),
            "reason_dist": dict(Counter(r["f3f4_reason"] for r in p0_results).most_common()),
            "transition_dist": dict(Counter(r["transition"] for r in p0_results).most_common()),
            "diffs_base_vs_f3f4": sum(1 for r in p0_results if r["diff_base_f3f4"]),
        },
        "details": results,
    }

    out_path = os.path.join(OUT_DIR, "regression_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    # 打印摘要
    print("回归完成: %d 条, 耗时 %.1fms" % (total, elapsed))
    print("优先级分布: %s" % dict(p_dist.most_common()))
    print("冲突类分布: %s" % dict(cls_dist.most_common()))
    print()
    print("裁决分布:")
    print("  base: %s" % dict(base_dist.most_common()))
    print("  f3:   %s" % dict(f3_dist.most_common()))
    print("  f3+f4: %s" % dict(f3f4_dist.most_common()))
    print("裁决理由 (f3+f4): %s" % dict(reason_dist_f3f4.most_common()))
    print("解析状态: %s" % dict(resolve_dist.most_common()))
    print()
    print("三态迁移: %s" % dict(transitions.most_common()))
    print("base vs f3 差异: %d / %d (%.1f%%)"
          % (diffs_base_f3, total, 100.0 * diffs_base_f3 / max(1, total)))
    print("base vs f3+f4 差异: %d / %d (%.1f%%)"
          % (diffs_base_f3f4, total, 100.0 * diffs_base_f3f4 / max(1, total)))
    print()
    print("P0 子集 (%d 条):" % len(p0_results))
    print("  base: %s" % dict(Counter(r["base_verdict"] for r in p0_results).most_common()))
    print("  f3+f4: %s" % dict(Counter(r["f3f4_verdict"] for r in p0_results).most_common()))
    print("  迁移: %s" % dict(Counter(r["transition"] for r in p0_results).most_common()))
    print("  base vs f3+f4 差异: %d"
          % sum(1 for r in p0_results if r["diff_base_f3f4"]))
    print()
    print("结果已保存: %s" % out_path)
    print("=" * 78)

    return summary


def _verdict_to_state(v):
    """将裁决 dict 的 verdict 字段标准化为单字符: A/R/B."""
    if v["verdict"] == "PASS":
        return "A"
    elif v["verdict"] == "REVIEW":
        return "R"
    else:
        return "B"


# ---------------------------------------------------------------------------
# 运行测试用例集
# ---------------------------------------------------------------------------

def run_test_cases(test_path):
    """加载并运行 JSON 格式的测试用例集."""
    if not os.path.isfile(test_path):
        print("测试用例文件不存在: %s" % test_path)
        return None

    with open(test_path, encoding="utf-8") as f:
        test_data = json.load(f)

    cases = test_data.get("cases", [])
    print("加载 %d 条测试用例: %s" % (len(cases), os.path.basename(test_path)))

    eng = V86AliasEngine(test_data.get("engine_mode", "f3+f4"))
    results = []
    pass_count = fail_count = skip_count = 0

    for case in cases:
        cid = case.get("case_id", "")
        a = case.get("a", "")
        b = case.get("b", "")
        expected = case.get("expected_verdict", "")
        skip = case.get("skip", False)

        if skip or not a.strip():
            skip_count += 1
            results.append({"case_id": cid, "status": "SKIP",
                            "a": a[:40], "b": b[:40],
                            "expected": expected, "expected_state": "SKIP",
                            "actual_state": "SKIP", "actual_verdict": "SKIP",
                            "reason": ""})
            continue

        r = eng.decide(a, b)
        actual = _verdict_to_state(r)
        actual_verdict = r["verdict"]

        # 支持 expected_verdict 用 "PASS"/"REVIEW"/"BLOCK" 或 "A"/"R"/"B"
        exp_upper = expected.upper().strip()
        expected_state = {"PASS": "A", "REVIEW": "R", "BLOCK": "B"}.get(
            exp_upper, exp_upper[:1].upper())

        if expected_state == actual:
            status = "PASS"
            pass_count += 1
        else:
            status = "FAIL"
            fail_count += 1

        results.append({
            "case_id": cid,
            "status": status,
            "a": a[:40],
            "b": b[:40],
            "expected": expected,
            "expected_state": expected_state,
            "actual_state": actual,
            "actual_verdict": actual_verdict,
            "reason": r["reason"],
            "dice": r.get("dice", 0.0),
            "all_rules": r.get("all_rules", []),
        })

    total = len(results)
    rate = round(100.0 * pass_count / max(1, total), 2)

    print("结果: %d PASS / %d FAIL / %d SKIP = %.2f%%" % (pass_count, fail_count, skip_count, rate))

    for r in results:
        if r["status"] == "FAIL":
            print("  [%s] %s: expected=%s actual=%s (%s)"
                  % (r["status"], r["case_id"], r["expected_state"],
                     r["actual_state"], r.get("reason", "")))

    out_path = os.path.join(OUT_DIR, "test_run_results.json")
    out_data = {
        "task": TASK_ID,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "engine_mode": test_data.get("engine_mode", "f3+f4"),
        "summary": {
            "total": total,
            "pass": pass_count,
            "fail": fail_count,
            "skip": skip_count,
            "pass_rate_pct": rate,
        },
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2, default=str)

    print("结果已保存: %s" % out_path)
    return out_data


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="V86 别名引擎原型")
    parser.add_argument("--smoke", action="store_true", help="运行冒烟自测")
    parser.add_argument("--regression", action="store_true", help="运行 165 条冲突样本回归")
    parser.add_argument("--run-tests", type=str, default="", help="运行指定测试用例集")
    parser.add_argument("--mode", type=str, default="f3+f4",
                        choices=["base", "f3", "f3+f4"],
                        help="引擎模式 (默认 f3+f4)")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    if args.smoke:
        checks, stats = smoke_test()
        fail = sum(1 for c in checks if c["status"] == "FAIL")
        sys.exit(1 if fail > 0 else 0)

    if args.regression:
        run_regression()
        return

    if args.run_tests:
        run_test_cases(args.run_tests)
        return

    # 无参数: 打印帮助
    parser.print_help()


if __name__ == "__main__":
    main()
