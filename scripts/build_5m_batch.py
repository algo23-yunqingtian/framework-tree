#!/usr/bin/env python3
"""五金属(锌/镍/锡/硅/锂) 子页批量生成器 v1。

基于 build_cu_al_batch.py 改造：
  · CODES/COLORS 换成 zn/ni/sn/si/li
  · chart cid 加品种前缀（echart_zn_21_c1）
  · --zn-only / --ni-only / --si-only / --sn-only / --li-only
  · THEMES 沿用通用主题（2.x 板块定义品种无关）
  · THEME_BY_COMM / MAIN_METRIC 清空（五金属无品种专属覆盖）

用法：
  python build_5m_batch.py --dry                    # 打印计划
  python build_5m_batch.py 2.1 2.2 --zn-only        # 只建锌板块2
  python build_5m_batch.py --emit --zn-only          # 输出门禁注册代码
"""
import json, os, re, sqlite3, sys
from collections import OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, make_crumb, out, write_html, disambig_title)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODES = {"zn": "ZN", "ni": "NI", "si": "SI", "sn": "SN", "li": "LI"}
CN_NAMES = {"zn": "锌", "ni": "镍", "si": "硅", "sn": "锡", "li": "锂"}
COLORS = {"zn": "#5b7a8c", "ni": "#7a8c5b", "si": "#c08a3e", "sn": "#8c6b9c", "li": "#4f8a7a"}
ALT_COLORS = ["#5b98c9", "#5fb3a1", "#c9a227", "#9b6bb5", "#e06c75"]
SECTION_NAME = {"2": "价格信号", "3": "供给", "4": "库存", "5": "需求", "6": "进出口", "7": "成本利润"}
MIN_POINTS = 20
MIN_BYTES_BY_CHARTS = {1: 8000, 2: 12000, 3: 20000, 4: 30000}

# ============================================================
# 主题词库（节点 → 页面标题/主题说明/看图口径）
# 沿用 build_cu_al_batch.py 的通用 THEMES（2.x 品种无关）
# ============================================================
THEMES = {
    "2.1": ("盘面结构", "持仓/价/成交量，判断盘面波动是资金驱动还是现货驱动"),
    "2.2": ("现货与升贴水", "升贴水/基差，现货供需紧张程度是否领先期货 1-2 个交易日"),
    "2.3": ("海外价格", "LME/COMEX/现金，全球定价基准与海外资金参与度"),
    "2.4": ("价差体系", "月差/期限结构（近远月/LME月差），判断 Back 还是 Contango"),
    "2.5": ("估值与利润", "分位数/冶炼利润，价格所处的历史估值位置与利润弹性"),
    "2.6": ("持仓席位观察", "多空前20，机构资金方向与多空博弈结构"),
    "3.1": ("矿产量", "上游矿产量与产能"),
    "3.2": ("冶炼/精炼产量", "冶炼/精炼产量与产能利用率"),
    "3.3": ("再生供应", "再生/废金属供应"),
    "4.1": ("交易所库存", "SHFE/LME 库存与仓单结构"),
    "4.2": ("仓单", "仓单总量与注销/注册占比"),
    "4.3": ("社会库存", "社会库存水平"),
    "4.4": ("工厂库存", "厂库水平"),
    "4.5": ("隐性·在途", "隐性库存与在途量"),
    "5.1": ("初级消费", "初级加工开工率与消费"),
    "5.2": ("终端消费", "终端细分消费"),
    "5.3": ("消费先行", "需求先行指标"),
    "6.1": ("原料进口", "原料进口量"),
    "6.2": ("进出口", "精炼金属进出口量"),
    "6.3": ("制品出口", "制品出口量"),
    "7.1": ("成本曲线与分位", "成本结构与分位"),
    "7.2": ("利润", "冶炼利润"),
    "7.3": ("原料成本", "能源/原料成本"),
}

THEME_BY_COMM = {}  # 五金属无品种专属覆盖
MAIN_METRIC = {}    # 五金属无显式主图覆盖


def node_indicators(indicators):
    """节点 → [(metric_id, code, name, unit, freq)] 映射（五金属）。"""
    g = defaultdict(list)
    for k, v in indicators.items():
        for c in CODES:
            if k.startswith(c + "_"):
                for n in v.get("_nodes", []):
                    if n == "00":
                        continue
                    g[n].append((k, CODES[c], v.get("name", ""), v.get("unit", ""), v.get("freq", "")))
    out = {}
    for n, lst in g.items():
        seen, uniq = set(), []
        for item in lst:
            if item[0] not in seen:
                seen.add(item[0]); uniq.append(item)
        out[n] = uniq
    return out


def to_monthly_mean(pairs_data):
    d = OrderedDict()
    for date, v in pairs_data:
        if v is None: continue
        ym = date[:7]
        d.setdefault(ym, []).append(v)
    return [[ym + "-01", round(sum(vs) / len(vs), 2)] for ym, vs in d.items()]


def is_daily(freq):
    return freq in ("daily", "日", "")


def strip_season_button(html):
    html = re.sub(r'<button onclick="window\.__tgl\([^<]*</button>', '', html)
    html = html.replace('。切季节视图可对比近5年同期位置。', '。')
    return html


def span_years(pairs_data):
    if not pairs_data:
        return 0
    ys = set(str(d[0])[:4] for d in pairs_data if d[0])
    return int(max(ys)) - int(min(ys)) + 1


def full_years(pairs_data):
    if not pairs_data:
        return 0
    from collections import defaultdict
    ym = defaultdict(set)
    for d in pairs_data:
        ds = str(d[0])
        if len(ds) >= 7:
            ym[ds[:4]].add(ds[5:7])
    return sum(1 for y, ms in ym.items() if len(ms) >= 12)


def theme_of(node, comm="zn"):
    return THEME_BY_COMM.get((comm, node)) or THEMES.get(node, (node, ""))


def code_str_of(node, meta, comm="zn"):
    return theme_of(node, comm)[0]


def pick_main(data, node):
    forced = MAIN_METRIC.get(node)
    if forced:
        hit = next((d for d in data if d["mid"] == forced), None)
        if hit:
            return hit
    return next((d for d in data if is_daily(d["freq"])), data[0])


def is_stale(points, max_gap_days=180):
    if not points:
        return True
    import datetime as _dt
    try:
        last = _dt.date.fromisoformat(str(points[-1][0])[:10])
    except (ValueError, IndexError):
        return True
    gap = (_dt.date.today() - last).days
    return gap > max_gap_days


def build_node(node, ind_list, meta, comm_only=None):
    ver, version_str = meta.get("version", "3.4"), "v" + str(meta.get("version", "3.4")).lstrip("v")
    data = []
    for mid, code, name, unit, freq in ind_list:
        m = load_metric(mid, code)
        if m is None: continue
        if m["n"] < MIN_POINTS: continue
        _pairs = pairs(m)
        if is_stale(_pairs):
            continue
        data.append({"mid": mid, "code": code, "name": name, "unit": unit,
                     "freq": freq, "m": m, "pairs": _pairs})
    if len(data) < 1:
        return None, [], 0, None

    if comm_only:
        data = [x for x in data if x["code"] == comm_only]
        if not data:
            return None, [], 0, None
    code_str = data[0]["code"]
    sec_no = node.split(".")[0]
    main_pick = pick_main(data, node)
    main_comm = main_pick["code"].lower()
    if main_comm not in CODES:
        main_comm = "zn"
    color = COLORS[main_comm]
    title, topic = theme_of(node, main_comm)
    cids, js_all, html_all = [], [], []
    note_metrics = []

    # 图1：主图
    main = pick_main(data, node)
    cid = "echart_%s_%s_c1" % (main_comm, node.replace(".", ""))
    cids.append(cid)
    if is_daily(main["freq"]):
        mdata = to_monthly_mean(main["pairs"])
    else:
        mdata = main["pairs"]
    can_season = full_years(main["pairs"]) >= 3
    mdata = to_monthly_mean(main["pairs"]) if (can_season and is_daily(main["freq"])) else main["pairs"]
    if main["unit"] in ("百分比", "百分比(%)", "%"):
        howto = ("高位(接近或超过长期均值)=产能利用充分、供给刚性增强；低位=开工不足、"
                 "产能闲置，供给弹性释放。最新(%s)：%s%%。") % (latest(main["m"]), main["pairs"][-1][1])
    else:
        howto = ("负值区=压力/亏损/收紧；正值区=盈利/宽松。最新(%s)：%s%s。") % (
            latest(main["m"]), main["pairs"][-1][1], main["unit"])
    h1, j1 = chart_line_t(
        cid, "%s（主图·%s）" % (main["name"], node),
        "%s · %s · %s · %d点 · %d年跨度 · 至 %s" % (main["mid"], main["freq"], main["unit"], main["m"]["n"], span_years(main["pairs"]), latest(main["m"])),
        color, mdata,
        "什么时候看：%s。<br>怎么看：%s切季节视图可对比近5年同期位置。" % (topic, howto),
        default_seasonal=can_season,
    )
    if not can_season:
        h1 = strip_season_button(h1)
    html_all.append(h1); js_all.append(j1)
    note_metrics.append("%s %s(%s,%s)" % (main["mid"], main["name"], main["freq"], main["unit"]))

    # 图2/3/4
    used = {main["mid"]}
    rest = [d for d in data if d["mid"] not in used]
    ci = 2
    for a, b in [(rest[i], rest[i + 1]) for i in range(0, len(rest) - 1, 2)][:2]:
        if ci > 4: break
        cid = "echart_%s_%s_c%d" % (main_comm, node.replace(".", ""), ci)
        cids.append(cid)
        color_b = ALT_COLORS[(ci - 2) % len(ALT_COLORS)]
        h, j = chart_dual(
            cid, "%s vs %s" % disambig_title(a["mid"], a["name"], b["mid"], b["name"]),
            "%s + %s · %s · 左轴%s / 右轴%s · %d/%d 点" % (
                a["mid"], b["mid"], a["freq"], a["unit"], b["unit"], a["m"]["n"], b["m"]["n"]),
            a["pairs"], color, a["name"], a["unit"],
            b["pairs"], color_b, b["name"], b["unit"],
            "什么时候看：%s 与 %s 的联动。<br>怎么看：同向走=共振趋势确认；反向走=背离信号，需判断谁主导。" % disambig_title(a["mid"], a["name"], b["mid"], b["name"]),
        )
        html_all.append(h); js_all.append(j)
        note_metrics.append("%s %s(%s)" % (a["mid"], a["name"], a["unit"]))
        note_metrics.append("%s %s(%s)" % (b["mid"], b["name"], b["unit"]))
        used.add(a["mid"]); used.add(b["mid"])
        ci += 1
    single = [d for d in rest if d["mid"] not in used]
    for s in single[:1]:
        if ci > 4: break
        cid = "echart_%s_%s_c%d" % (main_comm, node.replace(".", ""), ci)
        if s["freq"] in ("周", "week", "weekly"):
            st = ("什么时候看：主图为月度口径、发布滞后，本图周度口径用于提前捕捉边际变化。<br>"
                  "怎么看：周度与月度同向=趋势确认；周度先拐而月度未变=领先信号，需连续2-3周验证后确认。")
        elif s["freq"] in ("年", "annual"):
            st = ("什么时候看：本图为年度口径，用于确认中期趋势而非追踪边际。<br>"
                  "怎么看：年度值与主图趋势一致=中期方向确认；明显偏离=结构变化，需查统计口径是否调整。")
        else:
            st = ("什么时候看：主图的高频补充，用于验证边际变化。<br>"
                  "怎么看：与主图同向=趋势确认；反向=背离信号，需判断谁主导。")
        cids.append(cid)
        s_can_season = full_years(s["pairs"]) >= 3
        mdata = to_monthly_mean(s["pairs"]) if (s_can_season and is_daily(s["freq"])) else s["pairs"]
        h, j = chart_line_t(
            cid, "%s（补充·%s）" % (s["name"], node),
            "%s · %s · %s · %d点 · %d年跨度 · 至 %s" % (s["mid"], s["freq"], s["unit"], s["m"]["n"], span_years(s["pairs"]), latest(s["m"])),
            ALT_COLORS[(ci - 2) % len(ALT_COLORS)], mdata,
            st,
            default_seasonal=s_can_season,
        )
        if not s_can_season:
            h = strip_season_button(h)
        html_all.append(h); js_all.append(j)
        note_metrics.append("%s %s(%s)" % (s["mid"], s["name"], s["unit"]))
        used.add(s["mid"])
        ci += 1

    if len(html_all) < 1:
        return None, [], 0, None

    loaded_mids = set(x["mid"] for x in data)
    skipped = [x[0] for x in ind_list if x[0] not in used and x[0] in loaded_mids]
    stale_excluded = []
    for mid, code, name, unit, freq in ind_list:
        if mid in loaded_mids:
            continue
        mm = load_metric(mid, code)
        if mm is not None and is_stale(pairs(mm)):
            stale_excluded.append(mid)
    quality = "按可用序列生成 %d 图" % len(html_all)
    if skipped:
        quality += "，未入图 %s" % "、".join(skipped)
    if stale_excluded:
        quality += "，断更剔除 %s（末点距今>180天，避免整页降级）" % "、".join(stale_excluded)
    if not skipped and not stale_excluded:
        quality += "，全指标已入图"
    NOTE = ("<strong style=\"color:#c9d1d9\">%s 定义：</strong>%s。<br>"
            "<strong style=\"color:#c9d1d9\">指标组：</strong>%s。<br>"
            "<strong style=\"color:#c9d1d9\">数据质量：</strong>%s。") % (
        node, topic, " · ".join(note_metrics), quality)

    cn_name = CN_NAMES.get(main_comm, main_comm)
    html = page_html(
        title="%s(%s) %s %s" % (cn_name, code_str, node, title),
        hcrumbs=make_crumb(cn_name, code_str, sec_no,
                           SECTION_NAME.get(sec_no, ""), node, title, "1", len(html_all)),
        hright="SMM",
        h1="".join(html_all), h2="", h3="",
        note_html=NOTE,
        footer_text="有色金属产业指标树 · %s(%s) %s %s · v1（%d 图全真数据 · 自动批量生成）· indicators_v1.json %s" % (
            cn_name, code_str, node, title, len(html_all), version_str),
        js_body="\n".join(js_all), cids=cids,
        nav_back='<a href="%s_%s_overview.html">← 回板块%s总览</a> <a href="index.html">← 回主站</a>' % (main_comm, sec_no, sec_no),
    )
    return html, cids, len(html_all), main_comm


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    comm_flags = {c: "--%s-only" % c in sys.argv for c in CODES}
    comm_only_codes = [c.upper() for c, v in comm_flags.items() if v]
    comm_only = comm_only_codes[0] if len(comm_only_codes) == 1 else (comm_only_codes[0] if comm_only_codes else None)
    meta = json.load(open(os.path.join(ROOT, "data/indicators_v1.json"), encoding="utf-8"))
    g = node_indicators(meta["indicators"])

    plan = sorted(g.keys()) if not args else [a for a in args if a in g]
    print("=" * 70)
    print("五金属批量建页 v1 · 计划 %d 节点 · dry=%s · comm_only=%s" % (len(plan), dry, comm_only))
    print("=" * 70)

    results = []
    if "--emit" in sys.argv:
        for node in plan:
            ind_list = g[node]
            html, cids, n, comm_id = build_node(node, ind_list, meta, comm_only)
            if html is None: continue
            fname = "%s_%s.html" % (comm_id, node.replace(".", "_"))
            md = []
            for mid, code, name, unit, freq in ind_list:
                if comm_only and code != comm_only:
                    continue
                mm = load_metric(mid, code)
                if mm is None or mm["n"] < MIN_POINTS:
                    continue
                _p = pairs(mm)
                if is_stale(_p):
                    continue
                md.append({"mid": mid, "freq": freq, "m": mm, "pairs": _p})
            main_m = pick_main(md, node)
            seasonal = cids[:1] if (n >= 1 and full_years(main_m["pairs"]) >= 3) else []
            key = "%s_%s" % (comm_id, node.replace(".", ""))
            print('    "%s": {' % node)
            print('        "file": "%s",' % fname)
            print('        "min_bytes": %d,' % MIN_BYTES_BY_CHARTS.get(n, 10000))
            print('        "charts": %d,' % n)
            print('        "cids": %s,' % json.dumps(cids))
            print('        "label": "%s %s",' % (code_str_of(node, meta, comm_id), node))
            print('        "has_seasonal": %s,   # 主图 chart_line_t' % ("True" if seasonal else "False"))
            print('    },')
            print("  { key: '%s', file: '%s', charts: %d, seasonal: %s }," % (key, fname, n, json.dumps(seasonal)))
        return

    results = []
    for node in plan:
        ind_list = g[node]
        html, cids, n, comm_id = build_node(node, ind_list, meta, comm_only)
        if html is None:
            print("  ⚠️  %-8s 跳过（数据不足，%d 指标）" % (node, len(ind_list)))
            results.append((node, "SKIP", 0))
            continue
        fname = "%s_%s.html" % (comm_id, node.replace(".", "_"))
        if not dry:
            write_html(fname, html)
        print("  ✅ %-8s → %s (%d 图, %d 指标)" % (node, fname, n, len(ind_list)))
        results.append((node, "OK", n))

    print("-" * 70)
    ok = sum(1 for r in results if r[1] == "OK")
    print("汇总: %d/%d 生成成功 · %d 跳过" % (ok, len(results), len(results) - ok))
    return results


if __name__ == "__main__":
    main()