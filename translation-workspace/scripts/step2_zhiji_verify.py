#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
step2_zhiji_verify.py — 指标翻译线 Step2：知几 API 验证（v2 灵活解析版）

从 Step1 audit 文件表格中提取 SMM/Mysteel/LME 精确指标名（9 种表头变体）→
清洗 → 构造知几搜索词（品种+空格+关键词，skill: 中文分词盲区解法）→
zhiji_api.py search → 输出映射表(概念名 → 知几ID → score → 置信度 A/B/C)。

表头变体处理：不依赖固定列号，识别"指标名列"（表头含 SMM官方/Mysteel官方/LME/
指标名/核心指标/推荐指标/建议指标/保留指标/平台搜索框命中名 等），取该列值作为候选名。
同时兼容 CU/AL 的"图名称|核心指标"格式（核心指标列即精确名）。

用法:
  python step2_zhiji_verify.py --all                  # 全部 4 品种
  python step2_zhiji_verify.py --variety NI --dry     # 单品种只解析
  python step2_zhiji_verify.py --all --dry            # 全量解析检查(不搜索)
  python step2_zhiji_verify.py --variety ZN           # 单品种搜索
  python step2_zhiji_verify.py --retry-failed         # 补跑 C 级

产物: translation-workspace/mapping/{品种}/step2_match_{品种}.json
状态: translation-workspace/mapping/_step2_state.json (断点续跑)
"""
import argparse, json, os, re, subprocess, sys, time, glob

BASE = "/home/ubuntu/framework-tree"
AUDIT_ROOT = os.path.join(BASE, "translation-workspace", "audit")
MAPPING_ROOT = os.path.join(BASE, "translation-workspace", "mapping")
STATE = os.path.join(MAPPING_ROOT, "_step2_state.json")
ZHJ = "/home/ubuntu/.hermes/scripts/zhiji_api.py"
RATE_LIMIT = 1.1       # 知几 API 限流 1次/秒
SCORE_A = 12           # ≥12 A命中
SCORE_B = 6            # 6-11 B弱匹配, <6 C未命中

# 表头含以下关键词的列 = 指标名列
NAME_COL_HINTS = ["SMM官方", "Mysteel官方", "LME英文", "LME常见", "LME精确", "LME官方",
                  "指标名", "核心指标", "推荐指标", "建议指标", "保留指标", "建议核心",
                  "平台搜索框命中名", "平台命名", "建议搜索名", "可能命名"]
# 表头 = 图名/子节点等 非指标列（用来跳过）
SKIP_HDR_HINTS = ["图名称", "子节点", "删除指标", "删除理由", "保留理由", "处理意见",
                  "处理方式", "处理结果", "调整", "原指标", "原归属", "使用结论",
                  "判断目的", "说明", "理由", "频率", "可得性", "单位", "备注",
                  "图表数", "变化", "作用", "目的"]


def parse_audit_tables(path):
    """解析 audit 文件表格 → [{subnode, chart, names:[]}]，names 为提取的候选指标名（去重）"""
    rows = []
    lines = open(path, encoding="utf-8").read().split("\n")
    current_sub = ""
    name_cols = None  # 当前表头下的指标名列索引集合
    chart_col = None  # 图名列索引
    for ln in lines:
        s = ln.strip()
        m = re.match(r"^(?:子节点\s*)?(\d+\.\d+)", s)
        if m and len(s) < 25:
            current_sub = m.group(1)
        if "\t" not in s:
            continue
        cells = [c.strip() for c in s.split("\t")]
        if len(cells) < 2:
            continue
        # 表头识别
        is_header = any("名称" in c or "命名" in c or "指标" in c or "图名" in c for c in cells[:6])
        if is_header and any(("官方" in c or "命名" in c or "指标" in c or "搜索框" in c) for c in cells[:6]):
            name_cols = set()
            chart_col = None
            for i, c in enumerate(cells):
                if any(h in c for h in NAME_COL_HINTS):
                    name_cols.add(i)
                if any(h in c for h in ["图名称", "子节点"]):
                    chart_col = i
            # 若表头只识别到 chart 列而没有指标列，跳过（这是删除表/理由表）
            if not name_cols:
                name_cols = None
            continue
        if name_cols is None:
            continue
        # 数据行：跳过说明性行
        first = cells[0]
        if re.match(r"^\d+$", first):
            continue
        if any(("：" in first and len(first) > 15) or len(first) > 25 for first in [cells[0]]):
            continue
        if len(first) < 2:
            continue
        names = []
        for i in name_cols:
            if i < len(cells):
                v = cells[i]
                if v and v != "无" and "无统一" not in v[:8]:
                    names.append(v)
        if not names:
            continue
        chart = cells[chart_col] if chart_col is not None and chart_col < len(cells) else first
        rows.append({"subnode": current_sub, "chart": chart, "names": names})
    return rows


def clean_name(name):
    """清洗指标名：去来源前缀/括号注释/单位/口径说明，保留可搜索的主干。
    v2: 更彻底——丢弃 '；' 分隔后的多余候选，取第一个为主干；去 'SMM研报常写'/'字段为' 等描述。"""
    n = name.strip()
    # 纯说明性行直接返回空（无需补充/已有/删除/保留等决策行）——注意 "已有" 匹配需整词
    if any(k in n for k in ["无需补充", "已有", "删除", "保留", "合并", "移动", "调整",
                            "口径", "备注", "转载", "研报", "常写", "字段为", "通常", "一般",
                            "商业终端", "终端也标", "部分终端", "说明", "理由", "结论"]) and len(n) > 12:
        # 若分号前有实质片段则取之，否则判为说明行返回空
        has_sep = False
        for sep in ["；", ";"]:
            if sep in n:
                n = n.split(sep)[0]
                has_sep = True
                break
        if not has_sep:
            return ""
    # 说明性单短句（含"已有/无需/补充/删除/保留/合并/移动"且 <25 字）→ 直接判空
    if re.search(r"(无需补充|已有|不需要|已覆盖)", n) and len(n) < 25:
        return ""
    n = re.sub(r"^(SMM|Mysteel|LME|SHFE|上期所)\s*[:：]\s*", "", n)
    n = re.sub(r"[（(][^）)]*[)）]", "", n)  # 去括号
    n = n.replace("；", " ").replace(";", " ").replace("、", " ").replace(",", " ").replace("，", " ")
    # 去说明尾
    n = re.sub(r"(为[^ ]{2,}|按[^ ]{2,}|口径[^ ]{0,6})", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    n = re.sub(r"[（(]?[0-9.]+\s*(吨|手|元/吨|美元/吨|万吨|美元|%|％)[）)]?$", "", n).strip()
    # 去掉 <2 字的碎片
    if len(n) < 2:
        return ""
    return n


def build_search_terms(variety, name):
    """构造搜索词：品种词+空格+清洗主干（skill: 空格分词解盲区）。返回最多 2 个候选词。
    v2: 纯英文名(LME)优先带品种前缀，中文名含品种词则直接用。"""
    cn = {"ZN": "锌", "CU": "铜", "AL": "铝", "NI": "镍"}[variety]
    clean = clean_name(name)
    if not clean:
        return []
    terms = []
    is_english = bool(re.search(r"[A-Za-z]", clean)) and not re.search(r"[\u4e00-\u9fff]", clean)
    # 纯英文(LME官方名) → 强制前置品种词，命中率更高
    if is_english:
        terms.append(f"{cn} {clean}")
    # 中文：已含品种词/别名 → 直接用；否则前置品种词
    elif (variety.lower() in clean.lower() or cn in clean
            or f"沪{cn}" in clean or f"电解{cn}" in clean or f"精{cn}" in clean):
        terms.append(clean)
    else:
        terms.append(f"{cn} {clean}")
    # 若清洗名仍含空格(多指标)，加一个只取第一段的变体
    if " " in clean and len(clean.split(" ")[0]) >= 2:
        first = clean.split(" ")[0]
        if not (variety.lower() in first.lower() or cn in first):
            terms.append(f"{cn} {first}")
    return terms[:2]


def grade_hit(variety, name, results):
    """不依赖 score 字段（zhiji search 不返回 score），改用命中 name/path 的品种词+关键词匹配分级。
    v2 (2026-09-01)：A=命中name含品种词且含核心关键词(或英文LME名命中英文片段)；B=只含品种词；C=未命中/错配。"""
    cn = {"ZN": "锌", "CU": "铜", "AL": "铝", "NI": "镍"}[variety]
    var_aliases = [cn, f"沪{cn}", f"电解{cn}", f"精{cn}", f"LME{cn}", f"{cn}锭", f"镍"]
    if not results:
        return "C", None, 0
    hit = results[0]
    hit_name = hit.get("name", "")
    hit_path = hit.get("path", "") + hit_name
    var_hit = any(a in hit_path for a in var_aliases)
    kw = clean_name(name)
    # 核心关键词匹配
    core_kws = [k for k in ["升贴水", "仓单", "库存", "TC", "利润", "开工率", "价差",
                            "产量", "成交量", "持仓", "价格", "基差", "月差", "进口", "出口",
                            "成本", "注册", "注销", "到港", "发运", "回收", "表观消费",
                            "竣工", "排产", "开工", "产能", "溢价", "盈亏"] if k in kw]
    kw_hit = any(k in hit_path for k in core_kws) if core_kws else False
    # 纯英文名(LME等)：要求命中含英文片段（如 Zinc/Copper/Nickel/Aluminium/Stock/Warrant）
    is_english = bool(re.search(r"[A-Za-z]", kw)) and not re.search(r"[\u4e00-\u9fff]", kw)
    if is_english:
        en_tokens = [t for t in re.split(r"[^A-Za-z]+", kw) if len(t) >= 3]
        kw_hit = any(t.lower() in hit_name.lower() or t.lower() in hit.get("path", "").lower() for t in en_tokens)
    if var_hit and kw_hit:
        return "A", hit, 1
    if var_hit:
        return "B", hit, 0.5
    return "C", hit, 0


def zhiji_search(query, limit=5):
    r = subprocess.run(["/usr/bin/python3", ZHJ, "search", query, "all", str(limit)],
                       capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"error": f"parse fail: {r.stdout[:200]}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--variety")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--retry-failed", action="store_true")
    args = ap.parse_args()

    os.makedirs(MAPPING_ROOT, exist_ok=True)
    varieties = ["ZN", "CU", "AL", "NI"] if args.all or not args.variety else [args.variety]
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}

    for v in varieties:
        print(f"\n===== {v} =====", flush=True)
        audit_files = sorted(glob.glob(os.path.join(AUDIT_ROOT, v, "audit_*.md")))
        if not audit_files:
            print("  无 audit 文件，跳过")
            continue
        all_rows = []
        for f in audit_files:
            rows = parse_audit_tables(f)
            print(f"  {os.path.basename(f)}: {len(rows)} 表行")
            all_rows.extend(rows)
        # 去重（按 子节点|图名|names 组合）
        seen = set()
        uniq = []
        for r in all_rows:
            k = (r["subnode"], r["chart"], tuple(r["names"]))
            if k in seen:
                continue
            seen.add(k)
            uniq.append(r)
        print(f"  去重后 {len(uniq)} 行")

        if args.dry:
            for r in uniq[:10]:
                for n in r["names"][:2]:
                    ts = build_search_terms(v, n)
                    print(f"    [{r['subnode']}|{r['chart'][:12]}] {n[:38]} -> {ts}")
            continue

        outdir = os.path.join(MAPPING_ROOT, v)
        os.makedirs(outdir, exist_ok=True)
        opath = os.path.join(outdir, f"step2_match_{v}.json")
        results = state.get(v, {})

        # 扁平化：每 (子节点|图名|指标名) 一条
        flat = []
        for r in uniq:
            for n in r["names"]:
                flat.append({"subnode": r["subnode"], "chart": r["chart"], "name": n})
        # 指标名去重
        seen_name = set()
        flat_uniq = []
        for f in flat:
            if (f["subnode"], f["name"]) in seen_name:
                continue
            seen_name.add((f["subnode"], f["name"]))
            flat_uniq.append(f)
        print(f"  待搜索 {len(flat_uniq)} 条")

        for i, f in enumerate(flat_uniq):
            target = f["name"]
            key = f"{f['subnode']}|{f['name'][:50]}"
            if args.retry_failed and results.get(key, {}).get("grade", "C") != "C":
                continue
            if not args.retry_failed and key in results:
                continue
            terms = build_search_terms(v, target)
            hits = None
            for t in terms:
                res = zhiji_search(t)
                if isinstance(res, dict) and res.get("results"):
                    hits = res
                    break
                time.sleep(RATE_LIMIT)
            hit_list = hits.get("results", []) if hits else []
            grade, hit, _ = grade_hit(v, target, hit_list)
            results[key] = {
                "subnode": f["subnode"], "chart": f["chart"], "name": f["name"],
                "term": terms[0] if terms else "", "grade": grade,
                "hit_id": hit.get("id") if isinstance(hit, dict) else None,
                "hit_name": hit.get("name") if isinstance(hit, dict) else None,
                "hit_score": 0,
                "hit_source": hit.get("source") if isinstance(hit, dict) else None,
            }
            state[v] = results
            json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=1)
            print(f"   [{i+1}/{len(flat_uniq)}] {grade} {target[:34]} -> {hit.get('name','未命中')[:44] if hit else '未命中'} (score={results[key]['hit_score']})", flush=True)
            time.sleep(RATE_LIMIT)

        json.dump(results, open(opath, "w"), ensure_ascii=False, indent=1)
        cnt = {}
        for k, vv in results.items():
            cnt[vv["grade"]] = cnt.get(vv["grade"], 0) + 1
        print(f"  {v} 映射完成: {cnt}")


if __name__ == "__main__":
    main()
