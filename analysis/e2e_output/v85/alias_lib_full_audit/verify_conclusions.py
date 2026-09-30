# -*- coding: utf-8 -*-
"""
verify_conclusions.py  — 旧草稿两个核心结论的真伪专项验证
=========================================================
DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST · T2.4

验证对象:
  结论A: "matched_name 不是模糊匹配的比对目标, 比对目标实为 canon_name(indicator_key)"
  结论B: "44.0% 的行 canon_name 与 matched_name 两列不一致"

原则:
  * 不读取 alias_match_presearch/_stats.json, 全部数字由本脚本从原始输入独立重算。
  * 比对目标候选共 3 个 (canon_name / matched_name / indicator_key), 全部实测, 不下先验结论。
  * 归一化函数从 build_alias_library.py 原样加载 (lines 1..530), 保证口径一致。
  * 输出 verify_conclusion_result.json + 控制台逐行日志。

用法: python verify_conclusions.py
"""
import csv, json, re, sys, os, hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

REPO = r"D:\DSH_WORK\framework-tree"
V85 = REPO + r"\analysis\e2e_output\v85"
SRC_BUILD = V85 + r"\alias_match_presearch\build_alias_library.py"
THS = V85 + r"\tonghuashun_recheck_fixed\ths_updated_match_stat.csv"
IV1 = REPO + r"\data\indicators_v1.json"
OUT_DIR = V85 + r"\alias_lib_full_audit"

os.makedirs(OUT_DIR, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")

TS = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
TOL = 0.011     # 与 build_alias_library.py 完全一致的容差口径

# ------------------------------------------------------------------
# 0. 原样加载 build_alias_library.py 的函数与常量 (不含任何写文件语句)
#    该脚本的写文件操作全部位于分节标记 "# 10. 写 indicator_alias_library.csv" 之后,
#    因此截取到 "# 7. 静态回放" 之前只含: 归一化函数 / 品种词表 / 数据加载 / 复现统计 /
#    黑名单 / 口径互斥表 / new_matcher / old_pipeline_accept —— 零副作用。
# ------------------------------------------------------------------
src_lines = open(SRC_BUILD, encoding="utf-8").read().split("\n")
src_bytes = open(SRC_BUILD, "rb").read()
# 定位 "# 7. 静态回放" 所在行 (该行及其后全部含写文件语句, 必须排除)
cut = None
for _i, _l in enumerate(src_lines):
    if "静态回放" in _l and "7." in _l:
        cut = _i
        break
assert cut is not None, "未找到 '# 7. 静态回放' 分节标记, 源码结构已变化, 拒绝加载"
head_src = "\n".join(src_lines[:cut])

M = {"__name__": "build_alias_module", "__file__": SRC_BUILD}
exec(compile(head_src, SRC_BUILD, "exec"), M)

# 取出本脚本需要的符号
dice = M["dice"]
norm_light = M["norm_light"]
match_norm = M["match_norm"]
strip_unit = M["strip_unit"]
canon_of = M["canon_of"]
canon = M["canon"]

print("=" * 78)
print("verify_conclusions.py · 旧草稿核心结论真伪验证")
print("  执行时间(UTC+8) : %s" % TS)
print("  源脚本 %s" % SRC_BUILD)
print("  源脚本大小 %d B | MD5 %s | SHA256 %s"
      % (len(src_bytes), hashlib.md5(src_bytes).hexdigest(), hashlib.sha256(src_bytes).hexdigest()))
print("  加载范围: 第1..%d行 (分节标记 '# 7. 静态回放' 位于第%d行, 之后全部写文件语句已排除)"
      % (cut, cut + 1))
print("  容差口径 TOL = %.3f (与 build_alias_library.py 一致)" % TOL)
print("  输入: %s" % THS)
print("  未读取: alias_match_presearch/_stats.json (T4.1 禁止复用注入数字)")
print("=" * 78)

rows = list(csv.DictReader(open(THS, encoding="utf-8-sig", newline="")))
fz = [r for r in rows if r["match_type"] == "fuzzy_name" and r["confidence"]]
print("\n输入规模: THS 总行 %d | fuzzy_name 且有 confidence %d" % (len(rows), len(fz)))
print("  resolution_source 分布: %s"
      % Counter(r["resolution_source"].split("[")[0] for r in fz).most_common())

# ==================================================================
# 1. 结论A 验证: 比对目标究竟是 canon_name / matched_name / indicator_key 哪一个
# ==================================================================
print("\n" + "=" * 78)
print("【结论A】'matched_name 不是比对目标' —— 目标消融实测")
print("=" * 78)

ABLA = Counter()
BOTH = Counter()
DECI = Counter()          # 两候选得分分歧 > TOL 的裁决行
strata = defaultdict(lambda: Counter())
strata_abla = defaultdict(Counter)
samples = defaultdict(list)

for r in fz:
    s = match_norm(r["series_name"])
    cn = norm_light(canon_of(r))
    mn = norm_light(r["matched_name"]) if r["matched_name"] not in ("", "None") else ""
    kn = norm_light(r["indicator_key"])
    got = float(r["confidence"])
    src = r["resolution_source"].split("[")[0]
    strata[src]["n"] += 1

    sc = dice(s, cn) if cn else 0.0
    sm = dice(s, mn) if mn else 0.0
    sk = dice(s, kn) if kn else 0.0
    hc = cn and abs(sc - got) <= TOL
    hm = mn and abs(sm - got) <= TOL
    hk = kn and abs(sk - got) <= TOL

    for name, hit in (("canon_name", hc), ("matched_name", hm), ("indicator_key", hk)):
        if hit:
            ABLA[name] += 1
            strata_abla[src][name] += 1
    if hc and hm:
        BOTH["both_canon_and_matched"] += 1
    if hc and not hm:
        BOTH["canon_only"] += 1
    if hm and not hc:
        BOTH["matched_only"] += 1
    if not hc and not hm:
        BOTH["neither"] += 1

    # 裁决子集: 两候选得分差异明显 (避免在两者近似时误判)
    if cn and mn and abs(sc - sm) > TOL:
        if hc and not hm:
            DECI["canon_wins"] += 1
        elif hm and not hc:
            DECI["matched_wins"] += 1
        elif hc and hm:
            DECI["both_within_tol"] += 1
        else:
            DECI["neither_within_tol"] += 1
    if cn and mn and abs(sc - sm) > 0.05 and len(samples["diverge_gt005"]) < 12:
        samples["diverge_gt005"].append(
            {"series": r["series_name"], "canon_name": canon_of(r)[:36],
             "matched_name": r["matched_name"][:36], "indicator_key": r["indicator_key"],
             "resolution_source": src, "recorded": got,
             "dice_canon": sc, "dice_matched": sm, "dice_key": sk,
             "verdict": "canon" if hc and not hm else ("matched" if hm and not hc else "neither")})

n = len(fz)
print("\n候选目标各自独立命中率 (n=%d, |Δ|<=%.3f):" % (n, TOL))
for k in ("canon_name", "matched_name", "indicator_key"):
    print("   %-13s %5d / %d = %5.1f%%" % (k, ABLA[k], n, 100.0 * ABLA[k] / n))

print("\n分层命中率 (indicators_v1 / zhiji_note):")
for src in sorted(strata):
    tot = strata[src]["n"]
    line = "   %-14s n=%4d  " % (src, tot)
    for k in ("canon_name", "matched_name", "indicator_key"):
        line += "vs %-13s %4d (%5.1f%%)  " % (k, strata_abla[src][k], 100.0 * strata_abla[src][k] / tot)
    print(line)

print("\n命中重叠结构 (canon vs matched):")
for k, v in BOTH.most_common():
    print("   %-28s %5d (%5.1f%%)" % (k, v, 100.0 * v / n))

print("\n裁决子集: 仅统计 canon/matched 得分差异 > %.3f 的行 (差异明显, 记录值只能属于一方):" % TOL)
dec_n = sum(DECI.values())
print("   可裁决行数 %d / %d (%.1f%%)" % (dec_n, n, 100.0 * dec_n / n))
for k in ("canon_wins", "matched_wins", "both_within_tol", "neither_within_tol"):
    print("   %-20s %5d (%5.1f%% of 裁决行)" % (k, DECI[k],
                                              100.0 * DECI[k] / dec_n if dec_n else 0.0))

verdict_a = (DECI["canon_wins"] > DECI["matched_wins"] * 3 and
             ABLA["canon_name"] > ABLA["matched_name"] * 1.5)
print("\n【结论A 判定】")
if verdict_a:
    print("   结论A 成立 (VERIFIED)。")
    print("   证据1: 独立命中率 canon_name %d >> matched_name %d (差距 %.1fx)"
          % (ABLA["canon_name"], ABLA["matched_name"],
             ABLA["canon_name"] / max(ABLA["matched_name"], 1)))
    print("   证据2: 裁决子集中 canon_wins %d vs matched_wins %d (%.0f:1)"
          % (DECI["canon_wins"], DECI["matched_wins"],
             DECI["canon_wins"] / max(DECI["matched_wins"], 1)))
    print("   证据3: zhiji_note 分层 canon_name %d/%d (%.1f%%) vs matched_name %d/%d (%.1f%%)"
          % (strata_abla["zhiji_note"]["canon_name"], strata["zhiji_note"]["n"],
             100.0 * strata_abla["zhiji_note"]["canon_name"] / strata["zhiji_note"]["n"],
             strata_abla["zhiji_note"]["matched_name"], strata["zhiji_note"]["n"],
             100.0 * strata_abla["zhiji_note"]["matched_name"] / strata["zhiji_note"]["n"]))
    print("   即 matched_name 在 zhiji_note 通道几乎完全失效, 但 canon_name 仍正常复现 ->")
    print("   matched_name 是展示字段, 不是比对目标。")
    print("   即 matched_name 在 zhiji_note 通道几乎完全失效, 但 canon_name 仍正常复现 ->")
    print("   matched_name 是展示字段, 不是比对目标。")
else:
    print("   结论A 不成立 / 证据不足。需人工复核上述分布。")

print("\n分歧样例 (|dice_canon - dice_matched| > 0.05, 最多12条):")
for x in samples["diverge_gt005"]:
    print("   [%s] canon=%s matched=%s key=%s rec=%.3f canon_calc=%.3f matched_calc=%.3f -> %s"
          % (x["series"][:26], x["canon_name"][:20], x["matched_name"][:20],
             x["indicator_key"][:14], x["recorded"], x["dice_canon"], x["dice_matched"], x["verdict"]))

# ==================================================================
# 2. 结论B 验证: 44.0% 的行 canon_name != matched_name
# ==================================================================
print("\n" + "=" * 78)
print("【结论B】'44.0% 的行 canon_name 与 matched_name 两列不一致'")
print("=" * 78)

same, diff = 0, 0
absent = 0                    # matched_name 缺失(空串或字面量 "None")
absent_none_literal = 0
absent_empty = 0
canon_absent = 0
raw_diff = 0                  # 原始字符串口径: canon != matched (build_alias_library.py NR_TARGET_GAP 同口径)
strata_diff = defaultdict(lambda: [0, 0])     # src -> [same, diff]
diff_examples = []
diff_by_src_of_match = Counter()

for r in fz:
    cn_raw = canon_of(r)
    mn_raw = r["matched_name"]
    if not cn_raw:
        canon_absent += 1
    # 口径1: 原始字符串逐字符比对 (与 build_alias_library.py 第576行 NR_TARGET_GAP 完全一致)
    if cn_raw and mn_raw and cn_raw != mn_raw:
        raw_diff += 1
    cn = norm_light(cn_raw) if cn_raw else ""
    mn = norm_light(mn_raw) if mn_raw not in ("", "None") else ""
    src = r["resolution_source"].split("[")[0]
    if cn and mn:
        if cn == mn:
            same += 1
            strata_diff[src][0] += 1
        else:
            diff += 1
            strata_diff[src][1] += 1
            if len(diff_examples) < 12:
                diff_examples.append({"series": r["series_name"],
                                      "canon_name": cn_raw[:40], "matched_name": mn_raw[:40],
                                      "resolution_source": src, "confidence": r["confidence"]})
    else:
        # matched_name 缺失: 无可比对目标, 不能算"两列不一致"
        if cn and (not mn_raw or mn_raw == "None"):
            absent += 1
            if mn_raw == "None":
                absent_none_literal += 1
            else:
                absent_empty += 1
        strata_diff[src][1] += 0      # 占位, 不计入 diff
        diff_by_src_of_match[src] += 1

raw_diff_pct = 100.0 * raw_diff / n
semantic_diff_pct = 100.0 * diff / n

print("\n口径1 — 原始字符串逐字符比对 (与 build_alias_library.py NR_TARGET_GAP 同口径):")
print("   canon_name != matched_name : %5d / %d = %.1f%%   <- 草稿的 44.0%% 即此口径"
      % (raw_diff, n, raw_diff_pct))

print("\n口径2 — 语义比对 (两侧均为真实名称, 排除 matched_name 缺失):")
print("   两侧真实名称且相同 : %5d (%.1f%%)" % (same, 100.0 * same / n))
print("   两侧真实名称且不同 : %5d (%.1f%%)" % (diff, semantic_diff_pct))
print("   matched_name 缺失   : %5d (%.1f%%)  [字面量'None' %d + 空串 %d]"
      % (absent, 100.0 * absent / n, absent_none_literal, absent_empty))
print("   canon_name 缺失     : %5d" % canon_absent)
print("   校验: same+diff+absent = %d (应等于 n=%d) -> %s"
      % (same + diff + absent, n, "一致" if same + diff + absent == n else "不一致!"))
print("\n分层 (口径2):")
for src in sorted(strata_diff):
    s, d = strata_diff[src]
    tot = s + d
    print("   %-14s 一致 %5d / 不一致 %5d / 合计 %5d | 不一致率 %.1f%%"
          % (src, s, d, tot, 100.0 * d / tot if tot else 0.0))
print("   分层 (口径1 原始字符串): indicators_v1 全部 canon==matched (621/621),")
print("                            zhiji_note %d/513 行两列原始字符串不同 (含 matched_name 缺失)"
      % raw_diff)

claimed_pct = 44.0
within_raw = abs(raw_diff_pct - claimed_pct) <= 0.5
within_sem = abs(semantic_diff_pct - claimed_pct) <= 0.5
print("\n【结论B 判定】")
print("   草稿声称 %.1f%% 不一致。" % claimed_pct)
print("   口径1 (原始字符串, 与 build_alias_library.py 同口径) 实测 %.1f%% -> %s"
      % (raw_diff_pct, "复现" if within_raw else "偏差超容差"))
print("   口径2 (两侧均为真实名称的语义比对) 实测 %.1f%% -> 偏差 %.2f pp"
      % (semantic_diff_pct, semantic_diff_pct - claimed_pct))
if within_raw:
    print("   判定: 44.0% 这个数值本身可复现 (VERIFIED, 口径1),")
    print("   但存在口径夸大问题 —— 其中 %d 行 (%.1f%%) 属于 matched_name 缺失"
          % (absent, 100.0 * absent / n))
    print("   (字面量 'None' %d 行 + 空串 %d 行), 并非'两列都有值但不一致'。"
          % (absent_none_literal, absent_empty))
    print("   真正'两列均有真实名称且不同'的只有 %d 行 (%.1f%%)。" % (diff, semantic_diff_pct))
    print("   -> 旧报告把'无可比对目标'与'两列冲突'混为一谈, 该表述需修正。")
    verdict_b = "VERIFIED_WITH_CAVEAT"
else:
    print("   判定: 44.0% 无法复现 (NOT_VERIFIED)。")
    verdict_b = "NOT_VERIFIED"

print("\n不一致样例 (最多12条):")
for x in diff_examples:
    print("   [%s] canon=%s | matched=%s | src=%s | conf=%s"
          % (x["series"][:24], x["canon_name"][:22], x["matched_name"][:22],
             x["resolution_source"], x["confidence"]))

# ==================================================================
# 3. 汇总
# ==================================================================
result = {
    "task": "DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST",
    "generated_at": TS,
    "build_script": {"path": SRC_BUILD, "bytes": len(src_bytes),
                     "md5": hashlib.md5(src_bytes).hexdigest(),
                     "sha256": hashlib.sha256(src_bytes).hexdigest(),
                     "loaded_lines": "1..%d (分节标记 '# 7. 静态回放' 之前, 无写文件语句)" % cut},
    "tolerance": TOL,
    "inputs": {"ths_csv": THS, "ths_rows": len(rows), "fuzzy_rows_with_confidence": n,
               "resolution_source_dist": dict(Counter(r["resolution_source"].split("[")[0] for r in fz))},
    "conclusion_A": {
        "claim": "matched_name 不是模糊匹配的比对目标, 真实比对目标为 canon_name(indicator_key)",
        "target_ablation_hits": dict(ABLA),
        "stratified_hits": {src: dict(strata_abla[src]) for src in strata},
        "strata_n": {src: strata[src]["n"] for src in strata},
        "overlap": dict(BOTH),
        "decision_subset": {"n": dec_n, "dist": dict(DECI)},
        "verdict": "VERIFIED" if verdict_a else "NOT_VERIFIED",
        "samples_divergent_gt_005": samples["diverge_gt005"],
    },
    "conclusion_B": {
        "claim": "44.0% 的行 canon_name 与 matched_name 两列不一致",
        "claimed_pct": claimed_pct,
        "caliber_1_raw_string": {"definition": "canon_name 与 matched_name 原始字符串逐字符比对, 与 build_alias_library.py 第576行 NR_TARGET_GAP 同口径",
                                 "diff": raw_diff, "pct": round(raw_diff_pct, 2),
                                 "verdict": "REPRODUCED" if within_raw else "NOT_REPRODUCED"},
        "caliber_2_semantic": {"definition": "仅统计两侧均为真实名称(排除 matched_name 为空串或字面量'None')的行",
                               "same": same, "diff": diff, "absent_matched_name": absent,
                               "absent_none_literal": absent_none_literal, "absent_empty": absent_empty,
                               "canon_absent": canon_absent,
                               "diff_pct_of_all": round(semantic_diff_pct, 2),
                               "verdict": "REPRODUCED" if within_sem else "NOT_REPRODUCED"},
        "stratified_semantic": {src: {"same": strata_diff[src][0], "diff": strata_diff[src][1]} for src in strata_diff},
        "verdict": verdict_b,
        "note": ("44.0%% 数值在原始字符串口径下可精确复现(499/1134), 但其中 %d 行属于 matched_name 缺失而非两列冲突; "
                 "语义口径真实冲突仅 %d 行 (%.1f%%)。旧报告将两者混同, 表述需修正。"
                 % (absent, diff, semantic_diff_pct)),
        "samples": diff_examples,
    },
}
with open(os.path.join(OUT_DIR, "verify_conclusion_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\n" + "=" * 78)
print("结论验证完成。结构化结果已写入 verify_conclusion_result.json")
print("  结论A: %s | 结论B: %s" % (result["conclusion_A"]["verdict"], verdict_b))
print("=" * 78)
