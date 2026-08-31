#!/usr/bin/env python3
"""铜(CU)缺口节点建页脚本: 4.4/4.5/7.1/7.2/7.3
独立于 indicators_v1.json，直接从 api_cache.db 读数据。
"""
import json, os, sqlite3, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, make_crumb, out, write_html)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "scripts", "api_cache.db")
CODE = "CU"
COLOR = "#b87333"
ALT_COLORS = ["#5b98c9", "#5fb3a1", "#c9a227", "#9b6bb5", "#e06c75"]
SECTION_NAME = {"4": "库存", "7": "成本利润"}
MIN_POINTS = 20

# ── 节点定义: (metric_key, zhiji_id, name, unit, freq, is_main) ──
NODES = {
    "4.4": {
        "title": "工厂库存",
        "topic": "铜加工企业的库存水平（月/周）",
        "indicators": [
            # (metric_key, zhiji_id, name, unit, freq, is_main)
            ("cu_44_smelter_stock", "a10001152", "SMM 冶炼厂电解铜库存", "吨", "月", True),
            ("cu_44_anode_days", "a12854090", "SMM 阳极铜库存天数", "天", "月", False),
        ],
    },
    "4.5": {
        "title": "隐性/在途库存",
        "topic": "看不见的库存（在途、贸易商）",
        "indicators": [
            ("cu_45_intransit", "a12839473", "SMM 冶炼厂电解铜在途库存", "吨", "周", True),
            ("cu_45_total_est", "a10001154", "SMM 估计电解铜库存总数", "吨", "月", False),
        ],
    },
    "7.1": {
        "title": "成本曲线与分位",
        "topic": "全行业成本分布，铜价在成本线什么位置",
        "indicators": [
            # 使用 indicators_v1.json 里已有的指标
            ("cu_25_tc_conc", "ID01732413", "铜精矿现货TC指导价", "美元/干吨", "季", True),
            ("cu_71_cost_fq", "ID01839347", "第一量子铜生产现金成本", "美元/吨", "季", False),
        ],
    },
    "7.2": {
        "title": "日度利润测算",
        "topic": "每天测算的冶炼利润",
        "indicators": [
            ("cu_72_smm_profit", "j02870870", "SMM 中国铜冶炼厂现货冶炼利润", "元/金属吨", "日", True),
            ("cu_72_smelt_cost", "a12855622", "SMM 铜冶炼厂冶炼成本", "元/金属吨", "月", False),
        ],
    },
    "7.3": {
        "title": "能源/原料成本",
        "topic": "电力、原料成本（先行指标）",
        "indicators": [
            ("cu_73_imp_cost", "a12819794", "中国海关 电解铜出口原料进口成本", "元/吨", "日", True),
        ],
    },
}


def cache_indicator(metric_key, zhiji_id, name, unit, freq):
    """将指标缓存到 api_cache.db。如果已存在则跳过。"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 检查是否已存在
    row = c.execute(
        "SELECT id FROM indicator_cache WHERE metric=? AND code=?",
        (metric_key, CODE)
    ).fetchone()
    if row:
        conn.close()
        return False

    # 从 api_cache 读取 data_json
    row2 = c.execute(
        "SELECT data_json FROM indicator_cache WHERE zhiji_id=? LIMIT 1",
        (zhiji_id,)
    ).fetchone()
    if not row2:
        conn.close()
        return False

    # 解析 data_json
    try:
        data = json.loads(row2[0])
    except (json.JSONDecodeError, TypeError):
        conn.close()
        return False

    if not data:
        conn.close()
        return False

    # 插入新记录
    now = datetime.datetime.now().isoformat()
    c.execute(
        "INSERT INTO indicator_cache (code, metric, zhiji_id, data_json, fetched_at, name, unit, freq) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (CODE, metric_key, zhiji_id, row2[0], now, name, unit, freq)
    )
    conn.commit()
    conn.close()
    return True


def read_metric_data(metric_key):
    """从 api_cache.db 读取指标数据，返回 (pairs_list, meta_dict)。"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute(
        "SELECT data_json, name, unit, freq FROM indicator_cache WHERE metric=? AND code=?",
        (metric_key, CODE)
    ).fetchone()
    conn.close()
    if not row:
        return None, None
    try:
        data = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None, None
    if not data:
        return None, None
    # 兼容两种格式：list of {date,value} 或 dict with "points" key
    if isinstance(data, dict):
        data = data.get("points", [])
    if not isinstance(data, list):
        return None, None
    pairs_list = [(str(p["date"]), float(p["value"])) for p in data if p.get("date") and p.get("value") is not None]
    pairs_list.sort(key=lambda x: x[0])
    meta = {"name": row[1], "unit": row[2], "freq": row[3], "n": len(pairs_list)}
    return pairs_list, meta


def is_daily(freq):
    return freq in ("日", "daily", "")


def full_years(pairs_data):
    """返回完整日历年份数。"""
    if not pairs_data:
        return 0
    from collections import defaultdict
    ym = defaultdict(set)
    for d, v in pairs_data:
        ds = str(d)
        if len(ds) >= 7:
            ym[ds[:4]].add(ds[5:7])
    return sum(1 for y, ms in ym.items() if len(ms) >= 12)


def span_years(pairs_data):
    if not pairs_data:
        return 0
    ys = set(str(d[0])[:4] for d in pairs_data if d[0])
    return int(max(ys)) - int(min(ys)) + 1


def latest_of(pairs_data):
    if not pairs_data:
        return "?"
    return str(pairs_data[-1][0])[:10]


def to_monthly_mean(pairs_data):
    """日频 → 月频均值。"""
    d = {}
    for date, v in pairs_data:
        if v is None:
            continue
        ym = date[:7]
        d.setdefault(ym, []).append(v)
    return [[ym + "-01", round(sum(vs) / len(vs), 2)] for ym, vs in sorted(d.items())]


def strip_season_button(html):
    import re
    html = re.sub(r'<button onclick="window\.__tgl\([^<]*</button>', '', html)
    html = html.replace('。切季节视图可对比近5年同期位置。', '。')
    return html


def build_node(node_id, node_def):
    """为单个节点生成 HTML。"""
    title = node_def["title"]
    topic = node_def["topic"]
    ind_list = node_def["indicators"]
    sec_no = node_id.split(".")[0]

    # 加载所有指标
    data = []
    for mid, zid, name, unit, freq, is_main in ind_list:
        pairs_list, meta = read_metric_data(mid)
        if not pairs_list:
            print(f"  ⚠️  {mid} 无数据，跳过")
            continue
        if meta["n"] < MIN_POINTS:
            print(f"  ⚠️  {mid} 数据点不足 ({meta['n']})，跳过")
            continue
        data.append({
            "mid": mid, "zid": zid, "name": name, "unit": unit,
            "freq": freq, "is_main": is_main,
            "pairs": pairs_list, "n": meta["n"]
        })

    if not data:
        return None, [], 0

    # 选主图
    main = next((d for d in data if d["is_main"]), data[0])
    cid_base = "echart_cu_%s" % node_id.replace(".", "")
    cids = []
    html_all = []
    js_all = []
    note_metrics = []

    # --- 图1: 主图 ---
    cid = "%s_c1" % cid_base
    cids.append(cid)
    can_season = full_years(main["pairs"]) >= 3
    if is_daily(main["freq"]) and can_season:
        mdata = to_monthly_mean(main["pairs"])
    else:
        mdata = main["pairs"]

    if main["unit"] in ("百分比", "百分比(%)", "%"):
        howto = "高位=产能利用充分；低位=开工不足。最新(%s)：%s%%。" % (
            latest_of(main["pairs"]), main["pairs"][-1][1])
    else:
        howto = "负值区=压力/亏损；正值区=盈利/宽松。最新(%s)：%s%s。" % (
            latest_of(main["pairs"]), main["pairs"][-1][1], main["unit"])

    h1, j1 = chart_line_t(
        cid, "%s（主图·%s）" % (main["name"], node_id),
        "%s · %s · %s · %d点 · %d年跨度 · 至 %s" % (
            main["mid"], main["freq"], main["unit"], main["n"], span_years(main["pairs"]), latest_of(main["pairs"])),
        COLOR, mdata,
        "什么时候看：%s。<br>怎么看：%s切季节视图可对比近5年同期位置。" % (topic, howto),
        default_seasonal=can_season,
    )
    if not can_season:
        h1 = strip_season_button(h1)
    html_all.append(h1)
    js_all.append(j1)
    note_metrics.append("%s %s(%s,%s)" % (main["mid"], main["name"], main["freq"], main["unit"]))

    # --- 图2/3: 辅助指标 ---
    used = {main["mid"]}
    rest = [d for d in data if d["mid"] not in used]
    ci = 2

    # 成对组合
    for i in range(0, len(rest) - 1, 2):
        if ci > 4:
            break
        a, b = rest[i], rest[i + 1]
        cid = "%s_c%d" % (cid_base, ci)
        cids.append(cid)
        color_b = ALT_COLORS[(ci - 2) % len(ALT_COLORS)]
        h, j = chart_dual(
            cid, "%s vs %s" % (a["name"], b["name"]),
            "%s + %s · %s · 左轴%s / 右轴%s · %d/%d 点" % (
                a["mid"], b["mid"], a["freq"], a["unit"], b["unit"], a["n"], b["n"]),
            a["pairs"], COLOR, a["name"], a["unit"],
            b["pairs"], color_b, b["name"], b["unit"],
            "什么时候看：%s 与 %s 的联动。<br>怎么看：同向走=共振确认；反向走=背离信号。" % (a["name"], b["name"]),
        )
        html_all.append(h)
        js_all.append(j)
        note_metrics.append("%s %s(%s)" % (a["mid"], a["name"], a["unit"]))
        note_metrics.append("%s %s(%s)" % (b["mid"], b["name"], b["unit"]))
        used.add(a["mid"])
        used.add(b["mid"])
        ci += 1

    # 落单指标
    single = [d for d in rest if d["mid"] not in used]
    for s in single[:1]:
        if ci > 4:
            break
        cid = "%s_c%d" % (cid_base, ci)
        s_can_season = full_years(s["pairs"]) >= 3
        if is_daily(s["freq"]) and s_can_season:
            mdata = to_monthly_mean(s["pairs"])
        else:
            mdata = s["pairs"]
        if s["freq"] in ("周", "week", "weekly"):
            st = "什么时候看：主图为月度口径、发布滞后，本图周度口径用于提前捕捉边际变化。<br>怎么看：周度先拐而月度未变=领先信号。"
        else:
            st = "什么时候看：主图的高频补充，用于验证边际变化。<br>怎么看：与主图同向=趋势确认；反向=背离信号。"
        cids.append(cid)
        h, j = chart_line_t(
            cid, "%s（补充·%s）" % (s["name"], node_id),
            "%s · %s · %s · %d点 · %d年跨度 · 至 %s" % (
                s["mid"], s["freq"], s["unit"], s["n"], span_years(s["pairs"]), latest_of(s["pairs"])),
            ALT_COLORS[(ci - 2) % len(ALT_COLORS)], mdata,
            st,
            default_seasonal=s_can_season,
        )
        if not s_can_season:
            h = strip_season_button(h)
        html_all.append(h)
        js_all.append(j)
        note_metrics.append("%s %s(%s)" % (s["mid"], s["name"], s["unit"]))
        used.add(s["mid"])
        ci += 1

    # 生成 NOTE
    skipped = [x[0] for x in ind_list if x[0] not in used]
    quality = "按可用序列生成 %d 图" % len(html_all)
    if skipped:
        quality += "，未入图 %s" % "、".join(skipped)

    NOTE = ("<strong style=\"color:#c9d1d9\">%s 定义：</strong>%s。<br>"
            "<strong style=\"color:#c9d1d9\">指标组：</strong>%s。<br>"
            "<strong style=\"color:#c9d1d9\">数据质量：</strong>%s。") % (
        node_id, topic, " · ".join(note_metrics), quality)

    # 生成页面
    version = "3.43"
    html = page_html(
        title="铜(CU) %s %s" % (node_id, title),
        hcrumbs=make_crumb("铜", title, sec_no,
                           SECTION_NAME.get(sec_no, ""), node_id, title, "1", len(html_all)),
        hright="SMM + 观服务",
        h1="".join(html_all), h2="", h3="",
        note_html=NOTE,
        footer_text="有色金属产业指标树 · 铜(CU) %s %s · v1（%d 图全真数据）· indicators_v1.json %s" % (
            node_id, title, len(html_all), "v" + version),
        js_body="\n".join(js_all), cids=cids,
        nav_back='<a href="cu_%s_overview.html">← 回板块%s总览</a> <a href="index.html">← 回主站</a>' % (
            sec_no, sec_no),
    )
    return html, cids, len(html_all)


def main():
    # Step 1: 缓存新指标
    print("=" * 70)
    print("铜(CU)缺口节点建页 · 缓存阶段")
    print("=" * 70)
    for node_id, node_def in sorted(NODES.items()):
        for mid, zid, name, unit, freq, is_main in node_def["indicators"]:
            ok = cache_indicator(mid, zid, name, unit, freq)
            print("  %s %s → %s" % (mid, "已缓存" if not ok else "新缓存", "✅" if ok else "⏭️"))

    # Step 2: 建页
    print("\n" + "=" * 70)
    print("铜(CU)缺口节点建页 · 建页阶段")
    print("=" * 70)
    results = []
    for node_id in ["4.4", "4.5", "7.1", "7.2", "7.3"]:
        node_def = NODES[node_id]
        print("\n  Building %s (%s)..." % (node_id, node_def["title"]))
        html, cids, n = build_node(node_id, node_def)
        if html is None:
            print("  ⚠️  %s 跳过（数据不足）" % node_id)
            results.append((node_id, "SKIP", 0, []))
            continue
        fname = "cu_%s.html" % node_id.replace(".", "_")
        out_path = os.path.join(ROOT, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("  ✅ %s → %s (%d 图, cids=%s)" % (node_id, fname, n, cids))
        results.append((node_id, "OK", n, cids))

    print("\n" + "-" * 70)
    ok = sum(1 for r in results if r[1] == "OK")
    print("汇总: %d/%d 生成成功 · %d 跳过" % (ok, len(results), len(results) - ok))
    for r in results:
        print("  %s: %s (%d 图)" % (r[0], r[1], r[2]))


if __name__ == "__main__":
    main()
