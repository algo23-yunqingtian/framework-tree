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


# 图表规范/说明性短语黑名单（命中即返回空，不参与搜索）
SPEC_RULE_KEYWORDS = [
    "避免", "左右双轴", "双轴", "坐标轴", "同一图", "放同一", "不宜", "可双轴",
    "不要", "建议", "最好", "优先", "原则", "规范", "排版", "布局",
    "横轴", "纵轴", "X轴", "Y轴", "单位", "图例", "标签",
]
# 说明性/元数据短语黑名单（命中且 <30 字即返回空）
META_KEYWORDS = [
    "无需补充", "已有", "删除", "保留", "合并", "移动", "调整",
    "口径", "备注", "转载", "常写", "字段为", "通常", "一般",
    "商业终端", "终端也标", "部分终端", "说明", "理由", "结论",
    "频率", "可得性", "单位", "付费", "公开", "周度", "日度", "月频",
    "无统一", "半结构化", "描述性",
]

def clean_name(name):
    """清洗指标名 → 可搜索主干（v3 重写：分三层过滤，语义化，不再机械截断）

    过滤层：
    1. 图表规范短语（"避免双轴"等）→ 直接丢弃，不是指标
    2. 元数据/说明短语（"无需补充/已有/删除"等）→ 直接丢弃
    3. 有效指标名 → 去来源前缀/括号/单位/分隔符 → 返回主干
    """
    n = name.strip()
    # 第一层：图表规范短语（整句命中即丢弃）
    if any(k in n for k in SPEC_RULE_KEYWORDS):
        return ""
    # 第二层：元数据/说明短语（命中且整句 <30 字 → 丢弃；≥30 字尝试取分号前）
    if any(k in n for k in META_KEYWORDS):
        for sep in ["；", ";"]:
            if sep in n:
                head = n.split(sep)[0].strip()
                if len(head) >= 4 and not any(k in head for k in META_KEYWORDS):
                    n = head
                    break
        else:
            if len(n) < 30:
                return ""
    # 第三层：有效指标名清洗
    n = re.sub(r"^(SMM|Mysteel|LME|SHFE|上期所)\s*[:：\s]*", "", n)
    # 内联 SMM/Mysteel/LME/SHFE/上期所 前缀（词间出现也去掉）
    n = re.sub(r"(?:^|\s)(SMM|Mysteel|LME|SHFE|上期所)\s*[:：\s]*", " ", n).strip()
    n = re.sub(r"[（(][^）)]*[)）]", "", n)
    # 去频率词（周度/日度/月频/季度/年内/年/月/周/季）
    n = re.sub(r"(周度|日度|月频|月均|季频|季度|年内|近\d+年|近\d+月|同比|环比|均值|标准差|分位|最新|当周|当月)", "", n)
    # 去"Zn50/Zn48/CU1"等浓度代码和纯数字噪声
    n = re.sub(r"\b(?:Zn|Cu|Al|Ni|Sn|Pb|Li)\d+\b", " ", n)
    n = re.sub(r"\b\d+\s*%\b", " ", n)
    # 去分隔符
    n = n.replace("；", " ").replace(";", " ").replace("、", " ").replace(",", " ").replace("，", " ").replace("/", " ")
    n = re.sub(r"(为[^ ]{2,}|按[^ ]{2,}|口径[^ ]{0,6})", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    n = re.sub(r"[（(]?[0-9.]+\s*(吨|手|元/吨|美元/吨|万吨|美元|%|％)[）)]?$", "", n).strip()
    if len(n) < 2:
        return ""
    return n


def build_search_terms(variety, name):
    """构造搜索词（v4 重写：加查库回退 + 中文长词拆短）

    原则：
    0. 查库回退：在 indicators_v1.json 的 {variety}_ 指标中按关键词查已有 zhiji_id，命中直接返回
    1. 先 clean_name 去噪声，得到主干
    2. 主干按空格/中英文边界切成多个 token
    3. 对含核心关键词的 token 构造搜索词（优先）
    4. 中文长词拆短：≥8字切 2-5 字核心词（如"七地锌锭社会库存"→"锌锭 社会库存"）
    5. 纯英文(LME)强制带品种前缀
    """
    cn = {"ZN": "锌", "CU": "铜", "AL": "铝", "NI": "镍"}[variety]
    clean = clean_name(name)
    if not clean:
        return []

    # 策略0：查库回退（indicators_v1.json 已有 zhiji_id）
    try:
        d = json.load(open("/home/ubuntu/framework-tree/data/indicators_v1.json"))
        prefix = {"ZN": "zn_", "CU": "cu_", "AL": "al_", "NI": "ni_"}[variety]
        search_chn = clean
        core_kw_list = ["TC", "加工费", "升贴水", "库存", "仓单", "价差", "月差", "基差",
                        "产量", "开工率", "利润", "成本", "价格", "持仓", "成交量",
                        "进口", "出口", "盈亏", "注册", "注销", "现货", "冶炼", "精炼"]
        in_kw = [k for k in core_kw_list if k in search_chn]
        if in_kw:
            # 额外约束：库存类指标必须区分国内/海外（防"社会库存"命中"LME巴林"）
            is_domestic = any(k in search_chn for k in ["社会", "国内", "七地", "中国", "主要", "厂内"])
            is_overseas = any(k in search_chn for k in ["LME", "注销", "注册", "仓单"])
            # 在已有指标中找 name 含相同核心关键词 + 品种词的
            candidates = []
            for k, v in d["indicators"].items():
                if not k.startswith(prefix):
                    continue
                vname = v.get("name", "")
                if not any(kw in vname for kw in in_kw):
                    continue
                if cn not in vname and f"沪{cn}" not in vname and f"电解{cn}" not in vname:
                    continue
                zhiji_id = v.get("ids", {}).get(variety, "")
                if not zhiji_id:
                    continue
                # 库存类：国内/海外必须匹配
                if "库存" in in_kw:
                    v_is_dom = any(kw in vname for kw in ["社会", "国内", "厂内", "港口", "现货"])
                    v_is_over = any(kw in vname for kw in ["LME", "注销", "注册", "海外"])
                    if is_domestic and not v_is_dom:
                        continue
                    if is_overseas and not v_is_over:
                        continue
                candidates.append((vname, zhiji_id))
            if candidates:
                # 取最精确的第一个（名字最短 = 最贴近主干）
                candidates.sort(key=lambda x: len(x[0]))
                vname, zhiji_id = candidates[0]
                return [f"__DB__{zhiji_id}|{vname}"]
    except Exception:
        pass

    # 分词：按空格 + 中英文边界切
    tokens = []
    for part in re.split(r"\s+|(?<=[\u4e00-\u9fff])(?=[A-Za-z])|(?<=[A-Za-z])(?=[\u4e00-\u9fff])", clean):
        t = part.strip()
        if len(t) >= 2:
            tokens.append(t)

    terms = []

    # 策略1：含核心关键词的 token 优先
    CORE_KW = {"TC", "加工费", "升贴水", "库存", "仓单", "价差", "月差", "基差",
               "产量", "开工率", "利润", "成本", "价格", "持仓", "成交量",
               "进口", "出口", "盈亏", "注册", "注销", "注销仓单", "现货",
               "电解", "精炼", "冶炼", "到港", "发运", "回收", "表观消费"}
    for t in tokens:
        if any(k in t for k in CORE_KW):
            if variety.lower() in t.lower() or cn in t:
                terms.append(t)
            else:
                terms.append(f"{cn} {t}")

    # 策略2：中文长词拆短（≥8字的中文 token 切 2-5 字核心词）
    for t in tokens:
        if len(t) >= 8 and re.search(r"[\u4e00-\u9fff]", t) and not re.search(r"[A-Za-z]", t):
            # 按核心关键词位置切
            for kw in CORE_KW:
                if kw in t:
                    idx = t.index(kw)
                    # 取 kw 前 2-3 字 + kw
                    head_start = max(0, idx - 3)
                    chunk = t[head_start:idx + len(kw)]
                    if len(chunk) >= 4:
                        candidate = f"{cn} {chunk}" if cn not in chunk else chunk
                        if candidate not in terms:
                            terms.append(candidate)

    # 策略3：纯英文 token（LME 字段名），强制带品种前缀
    for t in tokens:
        if re.search(r"[A-Za-z]", t) and not re.search(r"[\u4e00-\u9fff]", t):
            candidate = f"{cn} {t}"
            if candidate not in terms:
                terms.append(candidate)

    # 策略4：兜底
    if not terms:
        for t in tokens[:1]:
            if not (variety.lower() in t.lower() or cn in t):
                terms.append(f"{cn} {t}")

    return terms[:3]


def grade_hit(variety, name, results):
    """语义分级（v3 重写：核心关键词必须匹配，仅品种词匹配不够）

    逻辑：
    - A: 命中名含品种词 AND 含核心关键词（TC命中TC/加工费，库存命中库存等）
    - B: 命中名含品种词但核心关键词弱匹配（如"锌精矿"对"锌TC"——缺TC但有关联词）
    - C: 品种词不匹配，或品种词匹配但核心关键词完全不相关
    """
    cn = {"ZN": "锌", "CU": "铜", "AL": "铝", "NI": "镍"}[variety]
    var_aliases = [cn, f"沪{cn}", f"电解{cn}", f"精{cn}", f"LME{cn}", f"{cn}锭"]
    if not results:
        return "C", None, 0
    hit = results[0]
    hit_name = hit.get("name", "")
    hit_path = hit.get("path", "") + hit_name
    var_hit = any(a in hit_path for a in var_aliases)

    clean = clean_name(name)
    if not clean:
        return "C", hit, 0

    # 提取查询侧核心关键词
    core_kws = [k for k in ["TC", "加工费", "升贴水", "库存", "仓单", "价差", "月差", "基差",
                            "产量", "开工率", "利润", "成本", "价格", "持仓", "成交量",
                            "进口", "出口", "盈亏", "注册", "注销", "注销仓单", "现货",
                            "电解", "精炼", "冶炼", "到港", "发运", "回收", "表观消费"] if k in clean]

    # 纯英文(LME等)：要求命中含英文片段
    is_english = bool(re.search(r"[A-Za-z]", clean)) and not re.search(r"[\u4e00-\u9fff]", clean)
    if is_english:
        en_tokens = [t for t in re.split(r"[^A-Za-z]+", clean) if len(t) >= 3]
        kw_hit = any(t.lower() in hit_name.lower() or t.lower() in hit.get("path", "").lower() for t in en_tokens)
        related_hit = False
    else:
        kw_hit = bool(core_kws) and any(k in hit_path for k in core_kws)
        # 弱相关：品种词匹配 + 有冶炼/精矿/仓单等衍生词（非严格匹配但相关）
        related_words = ["精矿", "冶炼", "仓单", "库存", "价格", "期货", "现货",
                        "产能", "开工", "消费", "进出口"]
        related_hit = bool(core_kws) and any(w in hit_path for w in related_words)

    if var_hit and kw_hit:
        return "A", hit, 1
    # 品种词不匹配 → 一定 C，不再用弱相关救 B
    if not var_hit:
        return "C", hit, 0
    # 品种词匹配但核心关键词不匹配 → C（v3 关键改动：之前标 B 的假命中）
    # 除非有衍生词弱相关且核心关键词确实存在（保留少量合理 B）
    if var_hit and related_hit and not kw_hit:
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
                if t.startswith("__DB__"):
                    # 查库回退：直接构造命中
                    parts = t[6:].split("|", 1)
                    db_id = parts[0]
                    db_name = parts[1] if len(parts) > 1 else ""
                    hits = {"results": [{"id": db_id, "name": db_name, "path": "", "source": "db_cache"}]}
                    break
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
