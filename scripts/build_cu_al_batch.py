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
    # 2.x 主题对齐 data/tree_config.json 权威定义（category=price 的 name/q），
    # 铜铝共用同一板块定义；旧文案是铜「进口盈亏与贸易流」口径，套到铝上是错的。
    "2.1": ("盘面结构", "持仓/价/成交量，判断盘面波动是资金驱动还是现货驱动"),
    "2.2": ("现货与升贴水", "升贴水/基差，现货供需紧张程度是否领先期货 1-2 个交易日"),
    "2.3": ("海外价格", "LME/COMEX/现金，全球定价基准与海外资金参与度"),
    "2.4": ("价差体系", "月差/期限结构（近远月/LME月差），判断 Back 还是 Contango"),
    "2.5": ("估值与利润", "分位数/冶炼利润，价格所处的历史估值位置与利润弹性"),
    "2.6": ("持仓席位观察", "多空前20，机构资金方向与多空博弈结构"),
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
    "5.1": ("初级消费", "电解铝开工率（产能利用水平与供给弹性）"),
    "5.2": ("终端消费", "铝终端细分消费（汽车/建筑/电力）"),
    "5.3": ("消费价格", "铝价与消费的联动验证"),
    "6.1": ("原料进口", "阳极铜/废铜原料进口量"),
    "6.2": ("进出口", "精炼金属进出口量"),
    "6.3": ("制品出口", "铝制品出口量"),
    "7.1": ("电解铝成本", "氧化铝成本与TC加工费"),
    "7.2": ("铝价与成本", "铝价与成本传导验证"),
}


# 节点 × 品种 主题覆盖：铜 2.x 六个页面已全部验收上线，其主题文案沿用
# decision_2.x.md 的口径（与 tree_config 通用名不同），锁定防止批量重跑改口径。
THEME_BY_COMM = {
    ("cu", "2.1"): ("进口盈亏与贸易流", "内外盘套利窗口开合与贸易流是否支撑进口/套利"),
    ("cu", "2.2"): ("现货与升贴水", "现货对期货基差与平水铜升贴水，判断流通货源紧松"),
    ("cu", "2.3"): ("海外价格", "LME/COMEX 价格与成交量持仓，海外定价与资金参与度"),
    ("cu", "2.4"): ("价差体系", "月差与期限结构（近远月/沪伦/COMEX），判断 Back/Contango"),
    ("cu", "2.5"): ("估值与利润", "冶炼利润与 TC 加工费，矿端向冶炼端传导"),
    ("cu", "2.6"): ("持仓席位观察", "多空前20与净持仓集中度，资金结构"),
    # ── 铜需求/进出口主题（2026-08-31 补：THEMES 5.x/6.3 词库是铝口径，铜页套用会出「铝价与消费」错配）──
    ("cu", "5.2"): ("终端细分消费", "铜终端细分消费（家电/汽车/电网投资），滞后验证铜实物需求"),
    ("cu", "5.3"): ("需求先行", "铜需求先行指标（精铜杆开工率/线杆库存/LME注销占比），领先需求确认1-2月"),
    ("cu", "6.3"): ("制品出口", "铜加工制品出口量（铜杆/铜箔/铜管等），海外铜加工需求"),
    # ── 铝专属主题（2026-08-31 补：原 THEMES 词库是铜口径，铝页套用会出「铜矿产量·中国」错配）──
    ("al", "3.1.1"): ("铝土矿产量", "国内铝土矿分省产量（广西/山西等），矿端供给核心"),
    ("al", "3.1.3"): ("国内矿·开工率", "国内铝上游开工率（原铝系铝合金锭/氧化铝），矿端-冶炼端供给节奏"),
    ("al", "3.1.5"): ("加工费", "铝加工费（铝棒等）与加工利润，反映铝中间品供需紧松"),
    ("al", "3.2.1"): ("产能与开工", "电解铝上游产能/开工率，供给端弹性观测"),
    ("al", "3.2.2"): ("开工率", "原铝系铝合金锭开工率，冶炼端产能利用率"),
    ("al", "3.2.4"): ("成本与利润", "氧化铝现金成本，电解铝成本端压力与利润传导"),
    ("al", "6.2"): ("原料进口·港口库存", "铝土矿进口与港口库存，原料保障度"),
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
    html = re.sub(r'<button onclick="window\.__tgl\([^<]*</button>', '', html)
    html = html.replace('。切季节视图可对比近5年同期位置。', '。')
    return html


def span_years(pairs_data):
    """返回序列的年跨度（含首尾年份），用于显示标注。"""
    if not pairs_data:
        return 0
    ys = set(str(d[0])[:4] for d in pairs_data if d[0])
    return int(max(ys)) - int(min(ys)) + 1


def full_years(pairs_data):
    """返回【完整日历年份数】：该年内 12 个月都有数据才算完整。

    季节视图（chart_line_t 的 __seasonalizeByYear）为每个年份产出一条历年 series，
    verify_render 门禁要求历年 series 数量 ≥3，因此判定阈值必须是「完整年份数 ≥3」，
    而非 span_years（跨越年份数）。例：2025-03 → 2026-08 跨越 3 个年份，
    但 2025/2026 都不满 12 个月 → 完整年份数=0，span_years>=3 会误判为可建季节视图，
    导致页面保留季节按钮却只有 2 条历年线（cu_25/cu_324 的 FAIL 根因）。
    """
    if not pairs_data:
        return 0
    from collections import defaultdict
    ym = defaultdict(set)
    for d in pairs_data:
        ds = str(d[0])
        if len(ds) >= 7:
            ym[ds[:4]].add(ds[5:7])
    return sum(1 for y, ms in ym.items() if len(ms) >= 12)



def theme_of(node, comm="cu"):
    """节点 × 品种 → (标题, 主题说明)。先查 THEME_BY_COMM 品种覆盖，再退回 THEMES。

    tree_config.json 里 2.x 通用名是「盘面结构/现货与升贴水/...」，但铜 2.1 的手写样板页
    cu_2_1.html 主题是「进口盈亏与贸易流」(decision_2.1.md + 已注册 cu_21_import)，
    两者冲突时按品种覆盖走，避免批量重跑把样板页口径改掉。
    """
    return THEME_BY_COMM.get((comm, node)) or THEMES.get(node, (node, ""))


def code_str_of(node, meta, comm="cu"):
    """节点 → 页面标题。"""
    return theme_of(node, comm)[0]


# 显式主图覆盖：节点 → 指标key。批量引擎默认取「第一个日频指标」作主图，
# 但混合节点上 ind_list 排序会把断更序列或跨品种指标误选为正主，此处按 decision 文档强制指定。
MAIN_METRIC = {
    "2.3": "al_23_lme_settle",    # LME铝3M结算价正主（避免被 JSON 排序靠前的 al_00_comex_inv 抢占）
    "2.4": "al_24_shfe_spread",   # 沪铝月差正主（避免被断更的 al_22_spot 抢占）
    "2.5": "al_25_close_quantile",# 估值分位正主（decision_2.5「分位是估值类唯一正主」）
    "2.6": "al_26_long_top20",    # 沪铝前20多单正主（避免选到 COMEX CFTC 周度）
    "5.3": "cu_53_rod_oprate",    # CU 5.3 需求先行正主=精铜杆开工率（decision_5.3；避免被日频 LME 注销仓单抢占）
}


def pick_main(data, node):
    """主图选择：优先按 MAIN_METRIC 显式指定，否则第一个日频指标，兜底取首个。"""
    forced = MAIN_METRIC.get(node)
    if forced:
        hit = next((d for d in data if d["mid"] == forced), None)
        if hit:
            return hit
    return next((d for d in data if is_daily(d["freq"])), data[0])


def is_stale(points, max_gap_days=180):
    """断更判定：序列最后一个点距今超过阈值天数。

    al_22_spot（上海华通现货价）实测 n=1913 但 latest=2022-10-13，
    被选为主图会把 2.2/2.4 页面降级成只到 2022 年的死图。
    建页时跳过断更序列，主图改由下一条非断更指标承担。
    """
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
    """为单个节点生成 HTML。返回 (html, cids, n_charts) 或 None（数据不足）。"""
    ver, version_str = meta.get("version", "3.4"), "v" + str(meta.get("version", "3.4"))
    # 加载指标数据
    data = []
    for mid, code, name, unit, freq in ind_list:
        m = load_metric(mid, code)
        if m is None: continue
        if m["n"] < MIN_POINTS: continue
        _pairs = pairs(m)
        # 断更序列剔除：末点距今超 180 天的序列不进任何图（否则降级整页），仍列入 skipped 可追溯
        if is_stale(_pairs):
            continue
        data.append({"mid": mid, "code": code, "name": name, "unit": unit,
                     "freq": freq, "m": m, "pairs": _pairs})
    if len(data) < 1:
        return None, [], 0, None

    # comm_only: 混合节点（如 2.3/2.4/2.5 铜铝指标共存）按品种分别建页，避免两品种互相覆盖。
    if comm_only:
        data = [x for x in data if x["code"] == comm_only]
        if not data:
            return None, [], 0, None
    code_str = data[0]["code"]
    # 板块号（混合节点按树定义，不按数据判品种）
    sec_no = node.split(".")[0]
    # 主品种（文件名/cid前缀/标题统一用）：以本节点「主图指标」的品种为准。
    # 旧逻辑按指标条数投票，在 2.3/2.4/2.5 这类铜铝共存节点上会把节点误判给铜，
    # 重跑时覆盖掉铜已有页面（cu_2_3/cu_2_4/cu_2_5 被铝数据覆盖）。
    main_pick = pick_main(data, node)
    main_comm = "al" if main_pick["code"] == "AL" else "cu"
    color = COLORS[main_comm]
    title, topic = theme_of(node, main_comm)
    cids, js_all, html_all = [], [], []
    note_metrics = []

    # --- 图1：第一个日频指标做 时序⇄季节 主图 ---
    main = pick_main(data, node)
    cid = "echart_%s_%s_c1" % (main_comm, node.replace(".", ""))
    cids.append(cid)
    if is_daily(main["freq"]):
        mdata = to_monthly_mean(main["pairs"])
    else:
        mdata = main["pairs"]
    # 季节视图降级：完整日历年份数不足 3 个时无法产出 3 条历年 series，改纯时序
    can_season = full_years(main["pairs"]) >= 3
    mdata = to_monthly_mean(main["pairs"]) if (can_season and is_daily(main["freq"])) else main["pairs"]
    # 看图口径按单位分派：价格/利润类走「负值=亏损」，百分比（开工率/利用率/占比）走区间解读
    # 否则开工率页会被贴上「负值区=亏损」的错误解读（al_51_util 正主坑）
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
        # 辅助图口径：高频指标看边际，低频看确认；避免生成「结合主图判断<主图主题>」的泛化解读
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
        # 落单图同样做季节降级：完整年份<3 时无法产出 3 条历年 series
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

    # 跳过原因分类：本品种已加载但未入图的才是「真跳过」；
    # comm_only 过滤掉的另一品种指标不是跳过（那是本页设计外的品种），断更序列单列。
    loaded_mids = set(x["mid"] for x in data)
    skipped = [x[0] for x in ind_list if x[0] not in used and x[0] in loaded_mids]
    # 断更排除项（在 data 加载阶段被 is_stale 剔除，仍在 ind_list 里）
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
    # 混合节点按品种单独建页：--al-only 只建铝页，--cu-only 只建铜页
    comm_only = "AL" if "--al-only" in sys.argv else ("CU" if "--cu-only" in sys.argv else None)
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
            html, cids, n, comm_id = build_node(node, ind_list, meta, comm_only)
            if html is None: continue
            fname = "%s_%s.html" % (comm_id, node.replace(".", "_"))
            # 季节图 = 主图完整日历年份数>=3 才有 3 条真实历年 series
            # 主图选择必须与 build_node 一致：第一个日频指标，而非 ind_list[0]
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
            print('        "label": "%s %s",' % (code_str_of(node, meta), node))
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
