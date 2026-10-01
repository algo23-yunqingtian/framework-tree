# -*- coding: utf-8 -*-
"""
alias_lib_import_validate.py — T2.3 别名库导入链路校验 (可运行, 只读模拟)
=========================================================================
DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST_AND_QUALITY_SUMMARY

按 alias_lib_full_audit/alias_lib_import_guide.md 第 6 节 V1–V8 设计实现。
**只读模拟**: 加载 indicators_v1.json 与 indicator_alias_library.csv 后在内存中
构造"导入后视图", 不写回任何源文件, 不修改别名库 CSV, 不调用 zhiji API。

校验项:
  V1  CSV schema 完整性 / 主键唯一 / 空值
  V2  alias_norm 归一化口径一致性 (重算 norm_full 比对, 检测漂移)
  V3  canonical_key 存在性 (在 indicators_v1.json 中)
  V4  四层质量分层复算 (与 relation/review_flag 交叉验证)
  V5  B1 门禁 G1–G8 逐项检查, 产出剔除清单
  V6  幂等性 (导入前已存在于 iv1 name/aliases 的别名数)
  V7  冲突与循环: 重复 canonical_name / 同一 alias_norm 多 canonical / 别名互指环
  V8  非法字符与超长 alias_norm
  V9  导入后回滚预演: 模拟 B1 写入, 校验写入幂等性与行数守恒

用法:
  python alias_lib_import_validate.py            # 正常运行, 写 JSON 结果
  python alias_lib_import_validate.py --strict   # 任一门禁失败即 exit 1
退出码: 0=全绿 / 1=存在阻断级异常(仅 --strict)
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v86_kit as K

TS = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
OUTDIR = K.OUT
RESULT_JSON = os.path.join(OUTDIR, "alias_import_validation_result.json")

# 与 alias_lib_import_guide.md 第 2 节一致的 B1 门禁定义
REQUIRED_COLS = [
    "alias_id", "canonical_key", "canonical_name", "canonical_unit", "variety_family",
    "metric_noun", "variety_token", "alias_name", "alias_norm", "alias_type",
    "unit_suffix", "chart_suffix", "alias_source", "alias_origin_sample",
    "distinct_form_count", "evidence_count", "relation", "confidence",
    "blacklist_rule", "risk_case_ids", "review_flag", "review_priority",
    "confusable_neighbor_count",
]
# alias_norm 允许字符集: CJK / 拉丁 / 数字 / 常见分隔与单位符号
ALIAS_NORM_ALLOWED = re.compile(r"^[\u4e00-\u9fffA-Za-z0-9:：,，、;；()（）/\-—_\.%％~＋+*&^#@$!?？!·\"'／]+$")
ALIAS_NORM_MAXLEN = 120
# 非法字符 (控制符 / 空白)
ILLEGAL_CHARS = re.compile(r"[\s\u0000-\u001f\u007f-\u009f]")

# 质量四层与 relation 的映射 (与 quality_regression.py::quality_label 一致)
TIER_BY_RELATION = {
    "synonym_merge": "W1_可靠同义",
    "synonym_with_confusable_neighbor": "W2_存疑",
    "canonical_conflict": "W2_存疑",
    "confusable_warn": "W3_明确错误",
    "unregistered": "W0_待注册",
}


def load_all():
    M = K.load_engine()
    norm_full = M["norm_full"]
    match_norm = M["match_norm"]
    norm_light = M["norm_light"]
    alias = list(csv.DictReader(open(K.ALIAS_CSV, encoding="utf-8-sig", newline="")))
    iv1 = json.load(open(K.IV1, encoding="utf-8"))
    return M, norm_full, match_norm, norm_light, alias, iv1


def check_v1_schema(alias):
    """V1 CSV schema 完整性。"""
    f = []
    if alias:
        got = set(alias[0].keys())
        miss = [c for c in REQUIRED_COLS if c not in got]
        extra = sorted(got - set(REQUIRED_COLS))
        if miss:
            f.append({"check": "V1_missing_columns", "severity": "BLOCK",
                      "detail": "缺列: %s" % miss})
        if extra:
            f.append({"check": "V1_extra_columns", "severity": "INFO",
                      "detail": "多列: %s" % extra})
    ids = [r["alias_id"] for r in alias]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        f.append({"check": "V1_duplicate_alias_id", "severity": "BLOCK",
                  "detail": "alias_id 重复 %d 个: %s" % (len(dup), dup[:5])})
    blank_id = sum(1 for r in alias if not r["alias_id"].strip())
    blank_norm = sum(1 for r in alias if not r["alias_norm"].strip())
    blank_name = sum(1 for r in alias if not r["alias_name"].strip())
    if blank_id:
        f.append({"check": "V1_blank_alias_id", "severity": "BLOCK",
                  "detail": "alias_id 为空 %d 行" % blank_id})
    if blank_norm:
        f.append({"check": "V1_blank_alias_norm", "severity": "BLOCK",
                  "detail": "alias_norm 为空 %d 行" % blank_norm})
    if blank_name:
        f.append({"check": "V1_blank_alias_name", "severity": "WARN",
                  "detail": "alias_name 为空 %d 行" % blank_name})
    return {
        "rows": len(alias), "columns": list(alias[0].keys()) if alias else [],
        "missing_columns": [x for x in f if x["check"] == "V1_missing_columns"],
        "duplicate_alias_id": len(dup), "blank_alias_id": blank_id,
        "blank_alias_norm": blank_norm, "blank_alias_name": blank_name,
        "findings": f,
    }


def check_v2_norm(alias, norm_full, match_norm):
    """V2 alias_norm 归一化口径一致性: 重算 norm_full(alias_name) 比对。"""
    f = []
    drift = 0
    same = 0
    empty_src = 0
    samples = []
    for r in alias:
        stored = r["alias_norm"]
        recomputed = norm_full(r["alias_name"])[0] if r["alias_name"].strip() else ""
        if not r["alias_name"].strip():
            empty_src += 1
            continue
        if stored == recomputed:
            same += 1
        else:
            drift += 1
            if len(samples) < 10:
                samples.append({"alias_id": r["alias_id"],
                                "alias_name": r["alias_name"][:40],
                                "stored_norm": stored[:40],
                                "recomputed_norm": recomputed[:40]})
    if drift:
        f.append({"check": "V2_norm_drift", "severity": "WARN",
                  "detail": "alias_norm 与 norm_full(alias_name) 不一致 %d 行" % drift})
    return {"checked": len(alias), "identical": same, "drift": drift,
            "empty_alias_name": empty_src, "drift_samples": samples, "findings": f}


def check_v3_canonical(alias, iv1):
    """V3 canonical_key 存在性 (按 | 拆分多键)。"""
    f = []
    missing_keys = Counter()
    rows_with_missing = 0
    key_total = 0
    for r in alias:
        ck = r["canonical_key"].strip()
        if not ck:
            continue
        for k in ck.split("|"):
            k = k.strip()
            if not k:
                continue
            key_total += 1
            if k not in iv1:
                missing_keys[k] += 1
                rows_with_missing += 1
    if missing_keys:
        f.append({"check": "V3_canonical_key_missing", "severity": "BLOCK",
                  "detail": "%d 个 canonical_key 在 indicators_v1.json 中不存在, 涉及 %d 行"
                            % (len(missing_keys), rows_with_missing)})
    return {"canonical_keys_referenced": len(missing_keys) and 0,
            "canonical_key_tokens": key_total,
            "missing_distinct_keys": len(missing_keys),
            "rows_with_missing_key": rows_with_missing,
            "missing_key_top20": missing_keys.most_common(20),
            "iv1_total_keys": len(iv1), "findings": f}


def check_v4_tiers(alias):
    """V4 四层分层复算。"""
    f = []
    tiers = Counter()
    relation_tier_mismatch = 0
    mism_samples = []
    for r in alias:
        rel = r["relation"]
        t = TIER_BY_RELATION.get(rel)
        tiers[t or ("UNMAPPED:%s" % rel)] += 1
        # 交叉验证: canonical_conflict 行应标记 manual_review
        if rel == "canonical_conflict" and r["review_flag"] not in ("manual_review",):
            relation_tier_mismatch += 1
            if len(mism_samples) < 10:
                mism_samples.append({"alias_id": r["alias_id"], "relation": rel,
                                     "review_flag": r["review_flag"]})
        if rel == "synonym_merge" and r["review_flag"] != "auto":
            relation_tier_mismatch += 1
            if len(mism_samples) < 10:
                mism_samples.append({"alias_id": r["alias_id"], "relation": rel,
                                     "review_flag": r["review_flag"]})
        if rel not in TIER_BY_RELATION:
            relation_tier_mismatch += 1
    if relation_tier_mismatch:
        f.append({"check": "V4_tier_flag_mismatch", "severity": "WARN",
                  "detail": "relation 与 review_flag 不自洽 %d 行" % relation_tier_mismatch})
    return {"tier_dist": dict(tiers), "unmapped_relations":
            [k for k in tiers if k.startswith("UNMAPPED")],
            "relation_flag_mismatch": relation_tier_mismatch,
            "mismatch_samples": mism_samples, "findings": f}


def b1_gate(row, iv1):
    """B1 八道门禁。返回 (通过?, [失败门禁])。"""
    fails = []
    if row["relation"] != "synonym_merge":
        fails.append("G1")
    if row["review_flag"] != "auto":
        fails.append("G2")
    ck = row["canonical_key"].strip()
    if not ck:
        fails.append("G3")
    elif "|" in ck or any(k.strip() and k.strip() not in iv1 for k in ck.split("|")):
        fails.append("G3")
    if "|" in ck:
        fails.append("G4")
    if not ck.strip():
        fails.append("G4")
    if row["blacklist_rule"].strip():
        fails.append("G5")
    if row["risk_case_ids"].strip():
        fails.append("G6")
    try:
        if int(float(row["confusable_neighbor_count"] or 0)) > 2:
            fails.append("G7")
    except ValueError:
        fails.append("G7")
    # G8: canonical_name 与 iv1 现有 name 一致
    ck_keys = [k.strip() for k in ck.split("|") if k.strip()]
    cn = row["canonical_name"].split("||")
    g8_ok = True
    for k in ck_keys:
        if k in iv1:
            iv1_name = str(iv1[k].get("name", "")) if isinstance(iv1[k], dict) else ""
            if cn and iv1_name and iv1_name != cn[0]:
                g8_ok = False
                break
    if not g8_ok:
        fails.append("G8")
    return (not fails), fails


def check_v5_b1_gates(alias, iv1):
    """V5 B1 门禁 G1–G8。"""
    f = []
    cand = [r for r in alias if r["relation"] == "synonym_merge"]
    pass_rows = []
    drop = defaultdict(list)
    for r in cand:
        ok, fails = b1_gate(r, iv1)
        if ok:
            pass_rows.append(r)
        else:
            for g in fails:
                drop[g].append(r["alias_id"])
    dist = Counter()
    for r in cand:
        _, fails = b1_gate(r, iv1)
        for g in fails:
            dist[g] += 1
    if cand:
        f.append({"check": "V5_b1_gate_summary", "severity": "INFO",
                  "detail": "B1 候选 %d, 通过 %d, 剔除 %d"
                            % (len(cand), len(pass_rows), len(cand) - len(pass_rows))})
        if len(pass_rows) == len(cand):
            f.append({"check": "V5_gate_not_independent", "severity": "WARN",
                      "detail": "G1–G8 对全部 %d 条 B1 候选无一剔除: review_flag=auto 标签"
                                "已在上游等价编码了这 8 项条件, 门禁未提供额外筛查力。"
                                "导入前建议补一道独立抽检 (见 alias_import_validation_report.md)"
                                % len(cand)})
    return {"b1_candidates": len(cand), "passed": len(pass_rows),
            "dropped": len(cand) - len(pass_rows),
            "gate_fail_dist": dict(dist),
            "dropped_by_gate": {g: v[:10] for g, v in drop.items()},
            "dropped_total_unique": len(set(a for v in drop.values() for a in v)),
            "findings": f}


def check_v6_idempotency(alias, iv1):
    """V6 幂等性: 导入前已存在于 iv1 name/aliases 的别名数。"""
    f = []
    iv1_norm = set()
    iv1_aliases = set()
    for k, v in iv1.items():
        if isinstance(v, dict):
            if v.get("name"):
                iv1_norm.add(str(v["name"]))
            for a in v.get("aliases", []) or []:
                iv1_aliases.add(str(a))
    already_in_name = sum(1 for r in alias if r["alias_name"] in iv1_norm)
    already_in_alias = sum(1 for r in alias if r["alias_name"] in iv1_aliases)
    return {"iv1_names": len(iv1_norm), "iv1_existing_aliases": len(iv1_aliases),
            "alias_rows_already_in_iv1_name": already_in_name,
            "alias_rows_already_in_iv1_aliases": already_in_alias,
            "findings": f}


def check_v7_conflicts(alias, norm_full):
    """V7 冲突与循环: 重复 canonical_name / 同一 alias_norm 多 canonical / 别名互指环。

    注: canonical_key 可能为复合键 "k1|k2", 本检查统一先分解为原子键再比较,
    避免把 "k1" / "k2" / "k1|k2" 误判为三个不同 canonical 而放大冲突数。
    真循环的判定标准: 本行 alias_norm 归一后 == 另一 canonical 的正名,
    且该 canonical 的原子键集合与本子行原子键集合完全不相交。
    """
    f = []

    def atoms(ck):
        return {k.strip() for k in ck.split("|") if k.strip()}

    # 7.1 重复 canonical_name: 同一 canonical_name 的原子键集合跨多个不同原子键
    name2atoms = defaultdict(set)
    for r in alias:
        cn = r["canonical_name"].strip()
        ck = r["canonical_key"].strip()
        if cn and ck and r["relation"] != "unregistered":
            for part in cn.split("||"):
                if part.strip():
                    name2atoms[part.strip()].update(atoms(ck))
    dup_cn = {k: v for k, v in name2atoms.items() if len(v) > 1}
    # 7.2 同一 alias_norm 指向多个不同原子键集合
    norm2atoms = defaultdict(set)
    norm2ids = defaultdict(list)
    for r in alias:
        nk = r["alias_norm"].strip()
        ck = r["canonical_key"].strip()
        if nk and ck:
            norm2atoms[nk].update(atoms(ck))
            norm2ids[nk].append(r["alias_id"])
    norm_conflict = {k: v for k, v in norm2atoms.items() if len(v) > 1}
    # 7.3 别名互指环: alias_norm == 别的 canonical 正名, 且原子键集合不相交
    canon_norm2atoms = {}
    canon_norm2rows = defaultdict(list)
    for r in alias:
        for part in r["canonical_name"].split("||"):
            p = part.strip()
            if p:
                n = norm_full(p)[0]
                canon_norm2atoms.setdefault(n, set()).update(atoms(r["canonical_key"]))
                canon_norm2rows[n].append(r["alias_id"])
    alias_is_canon = []
    self_reference = 0
    for r in alias:
        an = r["alias_norm"].strip()
        own = atoms(r["canonical_key"])
        if not own:
            continue
        n = norm_full(an)[0]
        if n not in canon_norm2atoms:
            continue
        other = canon_norm2atoms[n]
        if not (other - own):
            self_reference += 1          # alias_norm 就是自己 canonical 的正名, 正常
            continue
        if not (other & own):
            alias_is_canon.append({
                "alias_id": r["alias_id"], "alias_norm": an[:36],
                "own_canonical": r["canonical_key"][:36],
                "is_canonical_of": sorted(other)[:2],
            })
    if dup_cn:
        f.append({"check": "V7_duplicate_canonical_name", "severity": "WARN",
                  "detail": "%d 个 canonical_name 对应多个不同原子键" % len(dup_cn)})
    if norm_conflict:
        f.append({"check": "V7_alias_norm_multi_canonical", "severity": "BLOCK",
                  "detail": "%d 个 alias_norm 指向多个不同原子键 (导入后歧义)" % len(norm_conflict)})
    if alias_is_canon:
        f.append({"check": "V7_alias_canonical_cycle", "severity": "BLOCK",
                  "detail": "%d 行 alias_norm 同时是别的 canonical 的正名且键集合不相交 (真互指环)"
                            % len(alias_is_canon)})
    return {
        "distinct_canonical_names": len(name2atoms),
        "duplicate_canonical_name": len(dup_cn),
        "duplicate_canonical_name_samples": {k: sorted(v)[:4] for k, v in
                                              list(dup_cn.items())[:10]},
        "distinct_alias_norm": len(norm2ids),
        "alias_norm_multi_canonical": len(norm_conflict),
        "alias_norm_multi_canonical_samples": {k: sorted(v)[:4] for k, v in
                                               list(norm_conflict.items())[:10]},
        "canonical_norm_forms": len(canon_norm2atoms),
        "alias_norm_is_self_canonical": self_reference,
        "alias_is_other_canonical": len(alias_is_canon),
        "alias_is_other_canonical_samples": alias_is_canon[:10],
        "findings": f,
    }


def check_v8_chars(alias):
    """V8 非法字符 / 超长。"""
    f = []
    illegal = []
    empty = 0
    overlong = []
    for r in alias:
        n = r["alias_norm"]
        if not n.strip():
            empty += 1
            continue
        if ILLEGAL_CHARS.search(n):
            illegal.append({"alias_id": r["alias_id"], "alias_norm": n[:40]})
        if len(n) > ALIAS_NORM_MAXLEN:
            overlong.append({"alias_id": r["alias_id"], "len": len(n),
                             "alias_norm": n[:40]})
    if illegal:
        f.append({"check": "V8_illegal_chars", "severity": "BLOCK",
                  "detail": "alias_norm 含空白或控制符 %d 行" % len(illegal)})
    if overlong:
        f.append({"check": "V8_overlong", "severity": "WARN",
                  "detail": "alias_norm 超过 %d 字符 %d 行" % (ALIAS_NORM_MAXLEN, len(overlong))})
    return {"illegal_char_rows": len(illegal), "illegal_samples": illegal[:10],
            "empty_norm_rows": empty, "overlong_rows": len(overlong),
            "overlong_samples": overlong[:10],
            "max_len_observed": max((len(r["alias_norm"]) for r in alias), default=0),
            "findings": f}


def check_v9_simulate_b1_write(alias, iv1):
    """V9 导入预演: 模拟 B1 写入 iv1 的 aliases 数组, 校验幂等与行数守恒。"""
    f = []
    ok_rows = []
    for r in alias:
        p, _ = b1_gate(r, iv1)
        if p:
            ok_rows.append(r)
    # 按 canonical_key 聚合, 单键行才允许直接写入
    single = [r for r in ok_rows if "|" not in r["canonical_key"]]
    multi = [r for r in ok_rows if "|" in r["canonical_key"]]
    by_key = defaultdict(list)
    for r in single:
        by_key[r["canonical_key"].strip()].append(r["alias_norm"].strip())
    write_plan = 0
    duplicate_in_target = 0
    missing_target = 0
    for ck, norms in by_key.items():
        if ck not in iv1:
            missing_target += 1
            continue
        if not isinstance(iv1[ck], dict):
            missing_target += 1
            continue
        existing = set(str(x) for x in (iv1[ck].get("aliases") or []))
        for n in norms:
            if n in existing or n == str(iv1[ck].get("name", "")):
                duplicate_in_target += 1
            else:
                write_plan += 1
    if multi:
        f.append({"check": "V9_multi_key_rows", "severity": "WARN",
                  "detail": "%d 行 canonical_key 含 '|', 需拆键后再入库" % len(multi)})
    if missing_target:
        f.append({"check": "V9_missing_target_key", "severity": "BLOCK",
                  "detail": "%d 个目标 key 在 indicators_v1 中缺失" % missing_target})
    return {"b1_passed": len(ok_rows), "single_key": len(single), "multi_key": len(multi),
            "distinct_target_keys": len(by_key),
            "alias_writes_planned": write_plan,
            "already_present_skipped": duplicate_in_target,
            "missing_target_keys": missing_target,
            "iv1_keys_without_aliases_before": sum(
                1 for v in iv1.values() if isinstance(v, dict) and not (v.get("aliases"))),
            "findings": f}


def main(strict=False):
    os.makedirs(OUTDIR, exist_ok=True)
    head, cut, m5, s256 = K.cut_source()
    print("=" * 78)
    print("alias_lib_import_validate.py · 别名库导入链路校验 (T2.3, 只读模拟)")
    print("执行时间(UTC+8): %s" % TS)
    print("判定引擎: build_alias_library.py 第1..%d行 MD5 %s" % (cut, m5))
    print("别名库    : %s (%d bytes, MD5 %s)"
          % (K.ALIAS_CSV, os.path.getsize(K.ALIAS_CSV), K.file_md5(K.ALIAS_CSV)))
    print("iv1      : %s (%d bytes, MD5 %s)"
          % (K.IV1, os.path.getsize(K.IV1), K.file_md5(K.IV1)))
    print("只读声明 : 不修改 indicator_alias_library.csv / indicators_v1.json; 不调用 zhiji API")
    print("=" * 78)

    M, norm_full, match_norm, norm_light, alias, iv1 = load_all()
    print("\n别名库行数 %d | indicators_v1 键数 %d" % (len(alias), len(iv1)))

    v1 = check_v1_schema(alias)
    v2 = check_v2_norm(alias, norm_full, match_norm)
    v3 = check_v3_canonical(alias, iv1)
    v4 = check_v4_tiers(alias)
    v5 = check_v5_b1_gates(alias, iv1)
    v6 = check_v6_idempotency(alias, iv1)
    v7 = check_v7_conflicts(alias, norm_full)
    v8 = check_v8_chars(alias)
    v9 = check_v9_simulate_b1_write(alias, iv1)
    checks = {"V1": v1, "V2": v2, "V3": v3, "V4": v4, "V5": v5,
              "V6": v6, "V7": v7, "V8": v8, "V9": v9}

    all_f = []
    for name, c in checks.items():
        for x in c["findings"]:
            x["check_id"] = name
            all_f.append(x)
    n_block = sum(1 for x in all_f if x["severity"] == "BLOCK")
    n_warn = sum(1 for x in all_f if x["severity"] == "WARN")
    n_info = sum(1 for x in all_f if x["severity"] == "INFO")

    print("\n%-4s %-34s %-7s %s" % ("ID", "校验项", "级别", "明细"))
    for x in sorted(all_f, key=lambda y: ({"BLOCK": 0, "WARN": 1, "INFO": 2}[y["severity"]],
                                          y["check_id"])):
        print("  %-3s %-32s %-7s %s" % (x["check_id"], x["check"], x["severity"],
                                        x["detail"][:70]))
    print("\n合计: BLOCK %d / WARN %d / INFO %d" % (n_block, n_warn, n_info))

    print("\n--- 关键结论 ---")
    print("B1 候选 %d -> 通过 %d (%.1f%%) -> 可写入别名 %d 条"
          % (v5["b1_candidates"], v5["passed"],
             100.0 * v5["passed"] / max(1, v5["b1_candidates"]),
             v9["alias_writes_planned"]))
    print("人工处理条目 (门禁剔除 + 冲突 + 互指环): %d"
          % (v5["dropped_total_unique"] + v7["alias_norm_multi_canonical"]
             + v7["alias_is_other_canonical"]))

    res = {
        "task": K.INTEGRATION_TASK, "generated_at": TS, "strict_mode": strict,
        "engine": {"source": "build_alias_library.py", "loaded_lines": "1..%d" % cut,
                   "source_md5": m5, "source_sha256": s256},
        "inputs": {
            "alias_lib_csv": {"path": K.ALIAS_CSV, "bytes": os.path.getsize(K.ALIAS_CSV),
                              "md5": K.file_md5(K.ALIAS_CSV), "rows": len(alias)},
            "indicators_v1": {"path": K.IV1, "bytes": os.path.getsize(K.IV1),
                              "md5": K.file_md5(K.IV1), "keys": len(iv1), "readonly": True},
        },
        "readonly_declaration": "未修改 indicator_alias_library.csv / indicators_v1.json; 无 zhiji API 调用",
        "checks": checks,
        "findings": all_f,
        "summary": {"total": len(all_f), "block": n_block, "warn": n_warn, "info": n_info,
                    "b1_candidates": v5["b1_candidates"], "b1_passed": v5["passed"],
                    "b1_dropped": v5["dropped"],
                    "b1_pass_rate_pct": round(100.0 * v5["passed"] / max(1, v5["b1_candidates"]), 2),
                    "alias_writes_planned": v9["alias_writes_planned"],
                    "alias_norm_multi_canonical": v7["alias_norm_multi_canonical"],
                    "alias_is_other_canonical": v7["alias_is_other_canonical"],
                    "duplicate_canonical_name": v7["duplicate_canonical_name"],
                    "manual_conflict_items": v5["dropped_total_unique"]
                    + v7["alias_norm_multi_canonical"] + v7["alias_is_other_canonical"],
                    "import_ready": n_block == 0},
    }
    with open(RESULT_JSON, "w", encoding="utf-8") as fp:
        json.dump(res, fp, ensure_ascii=False, indent=1)
    print("\n已写出: %s (%d bytes)" % (RESULT_JSON, os.path.getsize(RESULT_JSON)))
    print("=" * 78)
    if strict and n_block > 0:
        sys.exit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="任一门禁 BLOCK 即 exit 1")
    a = ap.parse_args()
    main(strict=a.strict)
