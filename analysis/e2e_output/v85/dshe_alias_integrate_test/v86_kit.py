# -*- coding: utf-8 -*-
"""
v86_kit.py — DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST 共享引导模块
================================================================

设计原则（与 alias_lib_full_audit/ 完全一致）：
  1. 不重新实现判定逻辑。原样 exec() 线上审计用的 build_alias_library.py
     源文本，截断到 '# 10. 写 indicator_alias_library.csv' 分节标记之前
     （该分节起为写文件语句），因此 new_matcher / old_pipeline_accept /
     resolve_canonical / CONF / conf_index / BL_LR 与被审计工具链字节一致。
  2. new_matcher 通过 __globals__ 解析 BL_LR，故改写 M["BL_LR"] 即可
     注入扩展黑名单，无需 patch 函数体 —— 这是"联合回放"的关键开关。
  3. 所有输入只读；本模块不写任何文件。

用法:
    from v86_kit import load_engine, build_bl_lr, load_combined_rules, apply_rules
    M = load_engine()
    base_bl = build_bl_lr(M, M["BL_RULES"])      # 25 条基线
    ext_bl  = build_bl_lr(M, load_combined_rules())  # 25 + 6 条 DSHB 扩展
    apply_rules(M, ext_bl)                        # 注入 -> new_matcher 立即生效
"""
import csv
import hashlib
import io
import json
import os
import sys
from collections import Counter, defaultdict

REPO = r"D:\DSH_WORK\framework-tree"
V85 = REPO + r"\analysis\e2e_output\v85"
OUT = os.path.join(V85, "dshe_alias_integrate_test")
AUDIT = os.path.join(V85, "alias_lib_full_audit")

SRC_BUILD = os.path.join(V85, "alias_match_presearch", "build_alias_library.py")
CUT_MARKER_TEXT = "写 indicator_alias_library.csv"
CUT_PREFIX = "# 10"

BLACKLIST_BASE = os.path.join(V85, "tonghuashun_recheck_fixed", "semantic_blacklist_fixed.json")
BLACKLIST_EXTEND = os.path.join(V85, "risk_implement_verify", "blacklist_extend_candidate.json")

# DSHB 扩展候选的采纳白名单：status != not_recommended 的全部采纳
EXTEND_ACCEPT_STATUS = ("confirmed_new", "needs_manual_review")

SEED = 20261001          # 与上一轮回归测试完全一致，保证测试集可复现
MIN_PATTERN_LEN = 2      # 与 build_alias_library.py 的 R-04 一致

THS_STAT = os.path.join(V85, "tonghuashun_recheck_fixed", "ths_updated_match_stat.csv")
RISK41_CSV = os.path.join(V85, "risk_rootcause_review", "risk_rootcause_detail.csv")
ALIAS_CSV = os.path.join(AUDIT, "indicator_alias_library.csv")
AMBIG_CSV = os.path.join(AUDIT, "ambiguous_indicator_list.csv")
HRP_CSV = os.path.join(AUDIT, "high_risk_confusion_pairs.csv")
STATS_NEW = os.path.join(AUDIT, "_stats_new.json")
QR_RESULT = os.path.join(AUDIT, "quality_regression_result.json")
REGRESSION_MD = os.path.join(AUDIT, "regression_test_report.md")
OK_LIST_MD = os.path.join(V85, "fuzzy_match_fix", "revised_full_ok_list.md")
PDF_TPL_JSON = os.path.join(V85, "pdf_template_build", "zhiji_verified_package",
                            "pdf_template_library.json")
IV1 = os.path.join(REPO, "data", "indicators_v1.json")

# DSHB / HERMES 输入（本轮 T1 声明项，实测状态见 kit_probe()）
DSHB_FINAL_BL = os.path.join(V85, "semantic_blacklist_v85_final.json")
DSHB_488_PLAYBACK = os.path.join(V85, "full_488_template_playback_result.csv")
HERMES_MAPPING = os.path.join(V85, "v85_ths_mapping_gap_prep", "ths_candidate_mapping.csv")
HERMES_REPORT = os.path.join(V85, "v85_ths_mapping_gap_prep", "ths_mapping_prep_report.md")
# 最佳可得代理（proxy）
PROXY_488_SUMMARY = os.path.join(V85, "v85_final_integrate", "ths_render_task_summary.csv")
PROXY_488_SIMLOG = os.path.join(V85, "v85_render_fix_review_package",
                                "render_simulation_log_fixed.csv")

INTEGRATION_TASK = "DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY"
BASE_COMMIT = "bc33e8c"


def md5(b):
    return hashlib.md5(b).hexdigest()


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def file_md5(path):
    return md5(open(path, "rb").read())


def read_text(path, encoding="utf-8-sig"):
    return open(path, encoding=encoding, errors="replace").read()


def cut_source():
    """返回 (head_src, cut_line_no_1based, src_bytes_md5, src_bytes_sha256)。
    截断点 = '# 10. 写 indicator_alias_library.csv' 所在行之首（0-based）。"""
    text = read_text(SRC_BUILD)
    lines = text.split("\n")
    cut = None
    for i, l in enumerate(lines):
        if CUT_MARKER_TEXT in l and l.strip().startswith(CUT_PREFIX):
            cut = i
            break
    if cut is None:
        raise SystemExit("FATAL: 未找到分节标记 '%s ...', 拒绝加载源脚本" % CUT_PREFIX)
    return "\n".join(lines[:cut]), cut, md5(open(SRC_BUILD, "rb").read()), \
        sha256(open(SRC_BUILD, "rb").read())


def load_engine():
    """exec() 截断后的源脚本，返回命名空间 dict。"""
    head, cut, m5, s256 = cut_source()
    M = {"__name__": "build_alias_module", "__file__": SRC_BUILD}
    exec(compile(head, SRC_BUILD, "exec"), M)
    M["_cut_line"] = cut
    M["_src_md5"] = m5
    M["_src_sha256"] = s256
    return M


def build_bl_lr(M, rules, min_pat_len=MIN_PATTERN_LEN):
    """与 build_alias_library.py 第 387-409 行逐字一致的 BL_LR 构建。
    rules: {rule_id: {"left_patterns": [...], "right_patterns": [...],
                      "severity": str, "name": str}}
    返回 (BL_LR, BL_LINT) —— BL_LINT 记录被丢弃 / 需整词边界的 pattern。"""
    norm_light = M["norm_light"]
    ENTITY_ALL = M["ENTITY_ALL"]
    METRIC_ORDERED = M["METRIC_ORDERED"]
    BL_LR, BL_LINT = {}, []
    for rid, rule in rules.items():
        L_raw = [norm_light(x) for x in rule.get("left_patterns", [])]
        R_raw = [norm_light(x) for x in rule.get("right_patterns", [])]
        for side, lst in (("left", L_raw), ("right", R_raw)):
            for x in lst:
                if not x:
                    continue
                if len(x) < min_pat_len:
                    BL_LINT.append({"rule_id": rid, "rule_name": rule.get("name", ""),
                                    "side": side, "pattern": x, "len": len(x),
                                    "issue": "pattern过短(<%d字), 已丢弃" % min_pat_len})
                    continue
                emb = [t for t in ENTITY_ALL + METRIC_ORDERED
                       if len(t) > len(x) and x in t]
                if emb:
                    BL_LINT.append({"rule_id": rid, "rule_name": rule.get("name", ""),
                                    "side": side, "pattern": x, "len": len(x),
                                    "issue": "为更长token子串, 需整词边界: %s"
                                             % "/".join(emb[:4])})
        BL_LR[rid] = ({x for x in L_raw if len(x) >= min_pat_len},
                      {x for x in R_raw if len(x) >= min_pat_len},
                      rule.get("severity", ""), rule.get("name", ""))
    return BL_LR, BL_LINT


def load_baseline_rules():
    """DSH-B V85 基线黑名单 25 条 (BL-001..BL-025)。"""
    d = json.load(open(BLACKLIST_BASE, encoding="utf-8"))
    return {r["rule_id"]: r for r in d["rules"]}, d


def load_extend_candidates():
    """DSH-B 黑名单扩充候选 (8 条)；返回 (候选列表, 元数据)。"""
    d = json.load(open(BLACKLIST_EXTEND, encoding="utf-8"))
    return d.get("candidates", []), d


def candidate_to_rule(c):
    """把 blacklist_extend_candidate.json 的一条候选映射为 BL_RULES 条目结构。"""
    return {
        "rule_id": c["candidate_id"],
        "name": c.get("name", ""),
        "severity": c.get("severity", ""),
        "left_patterns": c.get("left_patterns", []),
        "right_patterns": c.get("right_patterns", []),
        "category": c.get("category", ""),
        "rationale": c.get("rationale", ""),
        "status": c.get("status", ""),
        "priority": c.get("priority", ""),
        "parent_rule": c.get("parent_rule", ""),
        "case_source": c.get("case_source", []),
        "replay_result": c.get("replay_result", ""),
    }


def load_combined_rules():
    """基线 25 条 + DSHB 扩展候选 (status != not_recommended)。
    返回 (rules, adopted, rejected)。"""
    base, meta_base = load_baseline_rules()
    rules = dict(base)
    cand, meta_ext = load_extend_candidates()
    adopted, rejected = [], []
    for c in cand:
        st = c.get("status", "")
        if st in EXTEND_ACCEPT_STATUS:
            rules[c["candidate_id"]] = candidate_to_rule(c)
            adopted.append(c["candidate_id"])
        else:
            rejected.append({"candidate_id": c["candidate_id"], "status": st,
                             "name": c.get("name", "")})
    return rules, adopted, rejected, meta_base, meta_ext


def apply_rules(M, bl_lr):
    """注入 BL_LR；new_matcher 立即使用新规则。返回旧 BL_LR 引用（便于还原）。"""
    old = M["BL_LR"]
    M["BL_LR"] = bl_lr
    return old


def guard_resolve_canonical(M):
    """给 resolve_canonical 加守卫: 原实现对 ALIAS[nm] 硬索引, 对未入库的归一名抛
    KeyError (build_alias_library.py 第 264-265 行)。本函数用 .get() 兜底替换,
    行为等价于"未入库则跳过别名侧解析", 不改写源文件, 只在当前进程内生效。

    new_matcher 通过 __globals__ 解析 resolve_canonical, 故重绑定 M 中的名字即生效。
    返回 {"patched": bool, "guard_hits": int, "missing_samples": [..]}
    """
    orig = M["resolve_canonical"]
    ALIAS = M["ALIAS"]
    name2canon = M["name2canon"]
    key2canon = M["key2canon"]
    stat = {"guard_hits": 0, "missing_samples": []}

    def guarded(nm):
        s = set()
        s |= set(name2canon.get(nm, []))
        s |= set(key2canon.get(nm, []))
        rec = ALIAS.get(nm)
        if rec is None:
            stat["guard_hits"] += 1
            if len(stat["missing_samples"]) < 12:
                stat["missing_samples"].append(nm)
            return sorted(s)
        light = rec.get("light")
        s |= set(name2canon.get(light, []))
        s |= set(key2canon.get(light, []))
        return sorted(s)

    patched = orig is not None and orig is not M.get("_resolve_canonical_guarded")
    if patched:
        M["resolve_canonical"] = guarded
        M["_resolve_canonical_guarded"] = orig
    stat["patched"] = patched
    stat["total_alias_entries"] = len(ALIAS)
    return stat


def kit_probe():
    """探测本轮 T1 声明输入的实测可用性（存在性 + 行数 + MD5）。"""
    def rec(path, label, required):
        ex = os.path.isfile(path)
        r = {"label": label, "path": path, "required": required,
             "exists": ex, "bytes": 0, "md5": "", "rows": None, "cols": None,
        }
        if ex:
            b = open(path, "rb").read()
            r["bytes"], r["md5"] = len(b), md5(b)
            if path.endswith(".csv"):
                with open(path, encoding="utf-8-sig", newline="") as f:
                    rr = list(csv.reader(f))
                r["rows"] = max(0, len(rr) - 1)
                r["cols"] = len(rr[0]) if rr else 0
            elif path.endswith(".json"):
                try:
                    d = json.loads(b.decode("utf-8"))
                    r["rows"] = len(d) if hasattr(d, "__len__") else None
                except Exception:
                    r["rows"] = None
        r["status"] = ("FOUND" if ex else "MISSING") + (
            "" if not required else (" (REQUIRED - BLOCKING)" if not ex else ""))
        return r

    return [
        rec(ALIAS_CSV, "别名库 indicator_alias_library.csv", True),
        rec(AMBIG_CSV, "歧义清单 ambiguous_indicator_list.csv", True),
        rec(HRP_CSV, "高危混淆对 high_risk_confusion_pairs.csv", True),
        rec(REGRESSION_MD, "上一轮回归报告 regression_test_report.md", True),
        rec(STATS_NEW, "上一轮 _stats_new.json", True),
        rec(QR_RESULT, "上一轮 quality_regression_result.json", True),
        rec(BLACKLIST_BASE, "V85 基线黑名单 semantic_blacklist_fixed.json", True),
        rec(BLACKLIST_EXTEND, "DSH-B 黑名单扩充候选 blacklist_extend_candidate.json", True),
        rec(DSHB_FINAL_BL, "DSH-B semantic_blacklist_v85_final.json", True),
        rec(DSHB_488_PLAYBACK, "DSH-B full_488_template_playback_result.csv", True),
        rec(PROXY_488_SUMMARY, "代理: ths_render_task_summary.csv (488行)", False),
        rec(PROXY_488_SIMLOG, "代理: render_simulation_log_fixed.csv (488行)", False),
        rec(HERMES_MAPPING, "HERMES ths_candidate_mapping.csv", True),
        rec(HERMES_REPORT, "HERMES ths_mapping_prep_report.md", True),
        rec(IV1, "data/indicators_v1.json (只读)", True),
    ]


def confusion_matrix(TP, FN, FP, TN):
    tpfp = TP + FP
    tpfn = TP + FN
    fpfn = FN + FP
    tot = TP + TN + FP + FN
    acc = 100.0 * (TP + TN) / tot if tot else 0.0
    prec = 100.0 * TP / tpfp if tpfp else 0.0
    rec = 100.0 * TP / tpfn if tpfn else 0.0
    spec = 100.0 * TN / fpfn if fpfn else 0.0
    f1 = 2.0 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    bal = (rec + spec) / 2.0
    return {"TP": TP, "FN": FN, "FP": FP, "TN": TN,
            "total": tot, "accuracy": round(acc, 2), "precision": round(prec, 2),
            "recall": round(rec, 2), "specificity": round(spec, 2),
            "f1": round(f1, 2), "balanced_accuracy": round(bal, 2)}


def delta_pp(a, b):
    """百分点差 (b - a)，保留 2 位。"""
    return round(b - a, 2)


def main():
    """自检: 打印 kit 探测结果。"""
    print("=" * 78)
    print("v86_kit.py · 自检 / T1 输入探测")
    print("=" * 78)
    print("源脚本: %s" % SRC_BUILD)
    head, cut, m5, s256 = cut_source()
    print("截断行  : 第 1..%d 行 (分节标记位于第 %d 行)" % (cut, cut + 1))
    print("源 MD5  : %s" % m5)
    print("源 SHA256: %s" % s256)
    M = load_engine()
    print("new_matcher      : %s" % (callable(M.get("new_matcher")),))
    print("BL_RULES 条数    : %d" % len(M["BL_RULES"]))
    print("BL_LR  rule_id   : %s" % sorted(M["BL_LR"].keys()))
    print("risk_replay 行数 : %d" % len(M.get("risk_replay", [])))
    print("nr (1134) 行数  : %d" % len(M.get("nr", [])))
    print("CONF / conf_index: %d / %d" % (len(M.get("CONF", [])), len(M.get("conf_index", {}))))
    print("-" * 78)
    for r in kit_probe():
        print("%-6s %-52s %8s" % (r["status"], os.path.basename(r["path"]),
                                  r["rows"] if r["rows"] is not None else "-"))
    rules, adopted, rejected, mb, me = load_combined_rules()
    print("-" * 78)
    print("扩展黑名单采纳 %d 条: %s" % (len(adopted), adopted))
    print("扩展黑名单拒绝 %d 条: %s" % (len(rejected), [x["candidate_id"] for x in rejected]))
    print("合并后 rule 总数 : %d" % len(rules))
    print("=" * 78)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
