#!/usr/bin/env python3
"""铜/铝 子页批量生成器 v1（Step4 建页主引擎）。

输入：data/indicators_v1.json（节点→指标映射）+ scripts/api_cache.db（时序）
输出：<品种>_<节点号>.html 到仓库根目录

设计原则（对齐样板页 cu_2_1.html 与 chart_kits.py）：
  · 零外部 fetch，数据内嵌
  · % 格式化写 JS，禁 f-string
  · 每图必有 chart-note
  · 日频指标自动聚合月频做季节视图（chart_line_t default_seasonal=True）
  · 年频(<20点) 或数据过少 → 跳过该指标
  · chart_dual 优先用于「价格 vs 价格」「量 vs 量」同主题组合
  · load_metric 必须显式传 code（CU/AL）
  · 图表 cid 加品种前缀（echart_cu_21_c1）防与铅 PB 同名串台

用法：
  python3 build_cu_al_batch.py            # 生成全部可生成节点
  python3 build_cu_al_batch.py 2.2 2.3    # 只生成指定节点
  python3 build_cu_al_batch.py --dry      # 只打印计划，不写文件
"""
import json, os, re, sqlite3, sys
from collections import OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, make_crumb, out, write_html)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODES = {"cu": "CU", "al": "AL"}
COLORS = {"cu": "#b87333", "al": "#8a9ba8"}   # 铜色 / 铝灰（主题色规范）
ALT_COLORS = ["#5b98c9", "#5fb3a1", "#c9a227", "#9b6bb5", "#e06c75"]
SECTION_NAME = {"2": "价格信号", "3": "供给", "4": "库存", "5": "需求", "6": "进出口", "7": "成本利润"}
MIN_POINTS = 20   # 年频/超短序列跳过阈值
# 按图数设 min_bytes 下限（数据内嵌量与图数正相关）
MIN_BYTES_BY_CHARTS = {1: 8000, 2: 12000, 3: 20000, 4: 30000}


# ============================================================
# 主题词库（节点 → 页面标题/主题说明/看图口径）
# ============================================================
THEMES = {
    "2.1": ("进口盈亏与贸易流", "内外盘套利窗口开合与贸易流是否支撑进口/套利"),
    "2.2": ("现货与升贴水", "现货对期货基差与平水铜升贴水，判断流通货源紧松"),
    "2.3": ("海外价格", "LME/COMEX 价格与成交量持仓，海外定价与资金参与度"),
    "2.4": ("价差体系", "月差与期限结构（近远月/沪伦/COMEX），判断 Back/Contango"),
    "2.5": ("估值与利润", "冶炼利润与 TC 加工费，矿端向冶炼端传导"),
    "2.6": ("持仓席位观察", "多空前20与净持仓集中度，资金结构"),
    "3.1.1": ("铜矿产量·澳", "澳大利亚铜矿产量与粗铜产量结构"),
    "3.1.2": ("铜矿产量·波兰", "波兰铜矿产量（年频）"),
    "3.1.3": ("铜矿产量·中国", "中国铜精矿含铜产量与产能利用率"),
    "3.1.4": ("铜精矿进口", "印尼→中国铜矿砂进口与全球到港量"),
    "3.1.5": ("TC/RC加工费", "铜精矿现货TC与TC指数，矿端紧松核心温度计"),
    "3.2.1": ("电解铜产能产量", "电解铜产能/产量/产能利用率/阳极铜进口"),
    "3.2.2": ("电解铜产量", "全球电解铜产量与产能对比"),
    "3.2.3": ("再生铜供应", "再生铜/废铜产量、进口与库存"),
    "3.2.4": ("冶炼利润", "铜冶炼厂现货冶炼利润与TC传导"),
    "4.1": ("交易所库存", "SHFE/LME 库存与仓单结构"),
    "4.2": ("仓单", "仓单总量与注销/注册占比"),
    "4.3": ("社会库存", "铝社会库存水平"),
    "4.4": ("工厂库存", "铝厂库水平"),
    "4.5": ("隐性·在途", "隐性库存与在途量"),
    "5.1": ("初级消费", "铝初级消费（表观消费/电解铝产量）"),
    "5.2": ("终端消费", "铝终端细分消费（汽车/建筑/电力）"),
    "5.3": ("消费价格", "铝价与消费的联动验证"),
    "6.1": ("原料进口", "阳极铜/废铜原料进口量"),
    "6.2": ("进出口", "精炼金属进出口量"),
    "6.3": ("制品出口", "铝制品出口量"),
    "7.1": ("电解铝成本", "氧化铝成本与TC加工费"),
    "7.2": ("铝价与成本", "铝价与成本传导验证"),
}


def node_indicators(indicators):
    """节点 → [(metric_id, code, name, unit, freq)] 映射。"""
    g = defaultdict(list)
    for k, v in indicators.items():
        for c in ("cu", "al"):
            if k.startswith(c + "_"):
                for n in v.get("_nodes", []):
                    if n == "00":      # 00 = 总览占位，不生成子页
                        continue
                    g[n].append((k, CODES[c], v.get("name", ""), v.get("unit", ""), v.get("freq", "")))
    # 去重（同一指标可被多节点引用）
    out = {}
    for n, lst in g.items():
        seen, uniq = set(), []
        for item in lst:
            if item[0] not in seen:
                seen.add(item[0]); uniq.append(item)
        out[n] = uniq
    return out


def to_monthly_mean(pairs_data):
    """日频 → 月频均值（季节视图用）。"""
    d = OrderedDict()
    for date, v in pairs_data:
        if v is None: continue
        ym = date[:7]
        d.setdefault(ym, []).append(v)
    return [[ym + "-01", round(sum(vs) / len(vs), 2)] for ym, vs in d.items()]


def is_daily(freq):
    return freq in ("daily", "日", "")


def strip_season_button(html):
    """摘掉 chart_line_t 的季节切换按钮及其说明文字（数据不足3年时无效季节视图）。

    按钮紧跟 </div> 无换行，onclick 内引号是转义的 \'，故不能用换行做前缀匹配。
    """
    html = re.sub(r'<button onclick=.window\.__tgl\(.+?\)</button>', '', html)
    html = html.replace('。切季节视图可对比近5年同期位置。', '。')
    return html


def span_years(pairs_data):
    """返回序列的年跨度（含首尾年份），用于判断季节视图是否有效。"""
    if not pairs_data:
        return 0
    ys = set(str(d[0])[:4] for d in pairs_data if d[0])
    return int(max(ys)) - int(min(ys)) + 1


def code_str_of(node, meta):
    """节点 → 页面标题（取 THEMES 标题，缺省用节点号）。"""
    return THEMES.get(node, (node, ""))[0]


def build_node(node, ind_list, meta):
    """为单个节点生成 HTML。返回 (html, cids, n_charts) 或 None（数据不足）。"""
    ver, version_str = meta.get("version", "2.9"), "v2.9"
    # 加载指标数据
    data = []
    for mid, code, name, unit, freq in ind_list:
        m = load_metric(mid, code)
        if m is None: continue
        if m["n"] < MIN_POINTS: continue
        data.append({"mid": mid, "code": code, "name": name, "unit": unit,
                     "freq": freq, "m": m, "pairs": pairs(m)})
    if len(data) < 1:
        return None, [], 0, None

    code_str = data[0]["code"]
    # 板块号（混合节点按树定义，不按数据判品种）
    sec_no = node.split(".")[0]
    # 主品种（文件名/cid前缀/标题统一用）：混合节点按指标数据量判定
    main_comm = "al" if sum(1 for x in data if x["code"] == "AL") > sum(1 for x in data if x["code"] == "CU") else "cu"
    color = COLORS[main_comm]
    title, topic = THEMES.get(node, (node, "综合指标"))
    cids, js_all, html_all = [], [], []
    note_metrics = []

    # --- 图1：第一个日频指标做 时序⇄季节 主图 ---
    main = next((d for d in data if is_daily(d["freq"])), data[0])
    cid = "echart_%s_%s_c1" % (main_comm, node.replace(".", ""))
    cids.append(cid)
    if is_daily(main["freq"]):
        mdata = to_monthly_mean(main["pairs"])
    else:
        mdata = main["pairs"]
    # 季节视图降级：月频/季频数据不足 3 年时无法产出历年 series，改纯时序
    can_season = span_years(main["pairs"]) >= 3
    mdata = to_monthly_mean(main["pairs"]) if (can_season and is_daily(main["freq"])) else main["pairs"]
    h1, j1 = chart_line_t(
        cid, "%s（主图·%s）" % (main["name"], node),
        "%s · %s · %s · %d点 · %d年跨度 · 至 %s" % (main["mid"], main["freq"], main["unit"], main["m"]["n"], span_years(main["pairs"]), latest(main["m"])),
        color, mdata,
        "什么时候看：%s。<br>怎么看：负值区=压力/亏损/收紧；正值区=盈利/宽松。最新(%s)：%s%s。切季节视图可对比近5年同期位置。" % (
            topic, latest(main["m"]), main["pairs"][-1][1], main["unit"]),
        default_seasonal=can_season,
    )
    if not can_season:
        h1 = strip_season_button(h1)
    html_all.append(h1); js_all.append(j1)
    note_metrics.append("%s %s(%s,%s)" % (main["mid"], main["name"], main["freq"], main["unit"]))

    # --- 图2/3/4：剩余指标与主图做双轴复合，或彼此互组 ---
    used = {main["mid"]}
    rest = [d for d in data if d["mid"] not in used]
    ci = 2
    for a, b in [(rest[i], rest[i + 1]) for i in range(0, len(rest) - 1, 2)][:2]:
        if ci > 4: break
        cid = "echart_%s_%s_c%d" % (main_comm, node.replace(".", ""), ci)
        cids.append(cid)
        color_b = ALT_COLORS[(ci - 2) % len(ALT_COLORS)]
        h, j = chart_dual(
            cid, "%s vs %s" % (a["name"], b["name"]),
            "%s + %s · %s · 左轴%s / 右轴%s · %d/%d 点" % (
                a["mid"], b["mid"], a["freq"], a["unit"], b["unit"], a["m"]["n"], b["m"]["n"]),
            a["pairs"], color, a["name"], a["unit"],
            b["pairs"], color_b, b["name"], b["unit"],
            "什么时候看：%s 与 %s 的联动。<br>怎么看：同向走=共振趋势确认；反向走=背离信号，需判断谁主导。" % (a["name"], b["name"]),
        )
        html_all.append(h); js_all.append(j)
        note_metrics.append("%s %s(%s)" % (a["mid"], a["name"], a["unit"]))
        note_metrics.append("%s %s(%s)" % (b["mid"], b["name"], b["unit"]))
        used.add(a["mid"]); used.add(b["mid"])
        ci += 1
    # 落单指标单独出一张图
    single = [d for d in rest if d["mid"] not in used]
    for s in single[:1]:
        if ci > 4: break
        cid = "echart_%s_%s_c%d" % (main_comm, node.replace(".", ""), ci)
        cids.append(cid)
        mdata = to_monthly_mean(s["pairs"]) if is_daily(s["freq"]) else s["pairs"]
        h, j = chart_line_t(
            cid, "%s（补充·%s）" % (s["name"], node),
            "%s · %s · %s · %d点 · 至 %s" % (s["mid"], s["freq"], s["unit"], s["m"]["n"], latest(s["m"])),
            ALT_COLORS[(ci - 2) % len(ALT_COLORS)], mdata,
            "什么时候看：补充验证 %s。<br>怎么看：结合主图判断 %s 的边际变化。" % (topic, s["name"]),
            default_seasonal=is_daily(s["freq"]),
        )
        html_all.append(h); js_all.append(j)
        note_metrics.append("%s %s(%s)" % (s["mid"], s["name"], s["unit"]))
        used.add(s["mid"])
        ci += 1

    if len(html_all) < 1:
        return None, [], 0, None

    skipped = [x[0] for x in ind_list if x[0] not in used]
    NOTE = ("<strong style=\"color:#c9d1d9\">%s 定义：</strong>%s。<br>"
            "<strong style=\"color:#c9d1d9\">指标组：</strong>%s。<br>"
            "<strong style=\"color:#c9d1d9\">数据质量：</strong>按可用序列生成 %d 图，跳过 %s。") % (
        node, topic, " · ".join(note_metrics), len(html_all),
        "、".join(skipped) if skipped else "无（全指标已入图）")

    html = page_html(
        title="%s(%s) %s %s" % ("铜" if main_comm == "cu" else "铝", code_str, node, title),
        hcrumbs=make_crumb("铜" if main_comm == "cu" else "铝", code_str, sec_no,
                           SECTION_NAME.get(sec_no, ""), node, title, "1", len(html_all)),
        hright="%s + 观服务" % ("SMM" if main_comm == "cu" else "SMM/安泰"),
        h1="".join(html_all), h2="", h3="",
        note_html=NOTE,
        footer_text="有色金属产业指标树 · %s(%s) %s %s · v1（%d 图全真数据 · 自动批量生成）· indicators_v1.json %s" % (
            "铜" if main_comm == "cu" else "铝", code_str, node, title, len(html_all), version_str),
        js_body="\n".join(js_all), cids=cids,
        nav_back='<a href="%s_%s_overview.html">← 回板块%s总览</a> <a href="index.html">← 回主站</a>' % (main_comm, sec_no, sec_no),
    )
    return html, cids, len(html_all), main_comm


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    meta = json.load(open(os.path.join(ROOT, "data/indicators_v1.json"), encoding="utf-8"))
    g = node_indicators(meta["indicators"])

    plan = sorted(g.keys()) if not args else [a for a in args if a in g]
    print("=" * 70)
    print("铜/铝批量建页 v1 · 计划 %d 节点 · dry=%s" % (len(plan), dry))
    print("=" * 70)

    results = []
    if "--emit" in sys.argv:
        # 输出门禁注册代码（check_html PAGES 字典 + verify_render PAGES 数组）
        for node in plan:
            ind_list = g[node]
            html, cids, n, comm_id = build_node(node, ind_list, meta)
            if html is None: continue
            fname = "%s_%s.html" % (comm_id, node.replace(".", "_"))
            # 季节图 = 主图数据年跨度>=3年才有真实历年 series
            main_m = load_metric(ind_list[0][0], ind_list[0][1])
            seasonal = cids[:1] if (n >= 1 and span_years(pairs(main_m)) >= 3) else []
            key = "%s_%s" % (comm_id, node.replace(".", ""))
            print('    "%s": {' % node)
            print('        "file": "%s",' % fname)
            print('        "min_bytes": %d,' % MIN_BYTES_BY_CHARTS.get(n, 10000))
            print('        "charts": %d,' % n)
            print('        "cids": %s,' % json.dumps(cids))
            print('        "label": "%s %s",' % (code_str_of(node, meta), node))
            print('        "has_seasonal": %s,   # 主图 chart_line_t' % ("True" if seasonal else "False"))
            print('    },')
            print("  { key: '%s', file: '%s', charts: %d, seasonal: %s }," % (key, fname, n, json.dumps(seasonal)))
        return

    results = []
    for node in plan:
        ind_list = g[node]
        html, cids, n, comm_id = build_node(node, ind_list, meta)
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
