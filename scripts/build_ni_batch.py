#!/usr/bin/env python3
"""镍(NI) 子页批量重建引擎 v2（归属优先 + divergence 标题参考）。

策略：
  1. 以已注册 156 个 ni_ 指标的 _nodes 为锚点，按 ID 前缀确定主归属节点
     · ni_21_xxx → 主节点 2.1（消除万金油，不再扩散到 18 个节点）
     · ni_22_xxx → 主节点 2.2，以此类推
  2. 用 divergence 标准答案提供图表标题和观测用途
  3. 数据不可得的图标记「待外部源」

消除万金油：ni_21_close_front 原来 _nodes=[2.1,2.2,...,7.3]（18节点），
重建后只归 2.1；其他节点如需用沪镍价格做辅轴，从各自前缀指标取。

用法：
  python3 scripts/build_ni_batch.py            # 重建全部
  python3 scripts/build_ni_batch.py 2.1 3.1.1 # 只重建指定
  python3 scripts/build_ni_batch.py --dry      # 只打印计划
  python3 scripts/build_ni_batch.py --assign   # 只做归属 + 写 schema
"""
import json, os, re, sys, sqlite3
from collections import defaultdict, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chart_kits import (load_metric, pairs, latest, chart_line_t, chart_dual,
                        page_html, make_crumb, out, write_html)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = "NI"
COLOR = "#5b98c9"
SECTION_NAME = {"2":"价格信号","3":"供给","4":"库存","5":"需求","6":"进出口","7":"成本利润"}
MIN_POINTS = 12

# ============================================================
# 1. 归属分配：ID前缀 → 主节点（消除万金油）
# ============================================================
# ni_21_xxx → "2.1", ni_311_xxx → "3.1.1", ni_312_xxx → "3.1.2" etc.
PREFIX_TO_NODE = {
    "ni_21_": "2.1", "ni_22_": "2.2", "ni_23_": "2.3", "ni_24_": "2.4",
    "ni_25_": "2.5", "ni_26_": "2.6",
    "ni_311_": "3.1.1", "ni_312_": "3.1.2", "ni_313_": "3.1.3",
    "ni_314_": "3.1.4", "ni_315_": "3.1.5",
    "ni_321_": "3.2.1", "ni_322_": "3.2.2", "ni_323_": "3.2.3",
    "ni_41_": "4.1", "ni_42_": "4.2", "ni_43_": "4.3",
    "ni_44_": "4.4", "ni_45_": "4.5",
    "ni_51_": "5.1", "ni_52_": "5.2", "ni_53_": "5.3",
    "ni_61_": "6.1", "ni_62_": "6.2", "ni_63_": "6.3",
    "ni_71_": "7.1", "ni_72_": "7.2", "ni_73_": "7.3",
}

def prefix_to_node(metric_id):
    """从 metric_id 前缀推断主归属节点"""
    for prefix, node in sorted(PREFIX_TO_NODE.items(), key=lambda x: -len(x[0])):
        if metric_id.startswith(prefix):
            return node
    return None


def assign_by_prefix(indicators_dict):
    """
    按 ID 前缀分配归属。返回:
      primary: {node: [metric_id, ...]}  — 每指标只归一个节点
    """
    primary = defaultdict(list)
    for k in sorted(indicators_dict.keys()):
        if not k.startswith("ni_"):
            continue
        node = prefix_to_node(k)
        if node:
            primary[node].append(k)
        else:
            # Fallback: use first _nodes entry
            old_nodes = indicators_dict[k].get("_nodes", [])
            if old_nodes:
                primary[old_nodes[0]].append(k)
    return dict(primary)


# ============================================================
# 2. 解析 divergence 标准答案（图表标题 + 观测用途）
# ============================================================
def parse_divergence(node_str):
    """解析 divergence_X.md，返回 [{num, name, obs_use}]"""
    path = os.path.join(ROOT, "analysis", "iwencai", "NI",
                        "divergence_%s.md" % node_str)
    if not os.path.exists(path):
        return []
    content = open(path, encoding="utf-8").read()
    charts = []
    for m in re.finditer(
        r'\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*.+?\s*\|\s*直接相关\s*\|.+\|.+\|\s*(.+?)\s*\|',
        content
    ):
        charts.append({
            "num": int(m.group(1)),
            "name": m.group(2).strip(),
            "obs_use": m.group(3).strip()
        })
    return charts


# ============================================================
# 3. 为节点构建图表列表：指标 → 图
# ============================================================
def full_years(points):
    """完整日历年份数（points = [{date, value}, ...]）"""
    if not points:
        return 0
    ym = defaultdict(set)
    for d in points:
        ds = d["date"] if isinstance(d, dict) else str(d[0])
        if len(ds) >= 7:
            ym[ds[:4]].add(ds[5:7])
    return sum(1 for ms in ym.values() if len(ms) >= 12)


def strip_season_button(html):
    html = re.sub(r'<button onclick="window\.__tgl\([^<]*</button>', '', html)
    html = html.replace('。切季节视图可对比近5年同期位置。', '。')
    return html


def build_charts_for_node(node, metric_ids, indicators_dict, div_charts):
    """
    为一个节点构建图表列表。
    返回 [{cid, html, js, title, note, chart_type}]
    """
    compressed = node.replace(".", "")
    indicators = indicators_dict["indicators"]

    # Load all metrics for this node
    loaded = []
    for mid in metric_ids:
        if mid not in indicators:
            continue
        info = indicators[mid]
        data = load_metric(mid, CODE)
        if data and data["n"] >= MIN_POINTS:
            loaded.append({
                "id": mid,
                "name": info.get("name", mid),
                "data": data,
                "unit": info.get("unit", ""),
                "freq": info.get("freq", ""),
            })

    if not loaded:
        return []

    # Get divergence chart titles for reference
    div_titles = {c["num"]: (c["name"], c.get("obs_use", "")) for c in div_charts}

    charts = []
    used = set()

    # Strategy: pair indicators into dual-axis charts where possible,
    # remaining get single line charts
    # Sort by data richness (more points first)
    loaded.sort(key=lambda x: -x["data"]["n"])

    chart_idx = 0
    for i, item in enumerate(loaded):
        if item["id"] in used:
            continue

        chart_idx += 1
        cid = "echart_ni_%s_c%d" % (compressed, chart_idx)

        # Get divergence title/obs for this chart position
        div_title = div_titles.get(chart_idx, ("", ""))
        chart_title = div_title[0] if div_title[0] else item["name"][:40]
        obs_use = div_title[1] if div_title[1] else "观察趋势方向与边际变化。"

        # Find a pairing partner (next unused item with compatible frequency)
        partner = None
        for j in range(i + 1, len(loaded)):
            if loaded[j]["id"] not in used:
                partner = loaded[j]
                break

        if partner:
            # Dual axis chart
            used.add(item["id"])
            used.add(partner["id"])
            title = "%s vs %s" % (
                item["name"][:25], partner["name"][:25])
            note_text = "📌 %s\n怎么看：同向=共振确认；反向=背离信号。" % obs_use

            # chart_dual(cid, title, sub, data_a, color_a, name_a, unit_a, data_b, color_b, name_b, unit_b, note='')
            sub = "%s %s | %s %s" % (
                item["name"][:15], item.get("unit", ""),
                partner["name"][:15], partner.get("unit", ""))
            h, j_code = chart_dual(
                cid, title, sub,
                item["data"]["points"], COLOR, item["name"][:25], item.get("unit", ""),
                partner["data"]["points"], "#e06c75", partner["name"][:25], partner.get("unit", ""),
                note=note_text
            )
            charts.append({"cid": cid, "html": h, "js": j_code})

        else:
            # Single line chart
            used.add(item["id"])
            can_season = (full_years(item["data"].get("points", [])) >= 3
                          and item.get("freq", "") in ("daily", "日", ""))
            note_text = "📌 %s\n最新(%s)：%s%s。" % (
                obs_use,
                latest(item["data"]),
                item["data"]["values"][-1] if item["data"]["values"] else "-",
                item.get("unit", ""))
            if can_season:
                note_text += "切季节视图可对比近5年同期位置。"

            # chart_line_t(cid, title, sub, color, data, note='', default_seasonal=False, ...)
            sub = "%s · %s · 至%s" % (
                item.get("unit", ""), item.get("freq", ""),
                item["data"].get("end", ""))
            h, j_code = chart_line_t(
                cid, item["name"], sub, COLOR,
                item["data"]["points"],
                note=note_text,
                default_seasonal=can_season
            )
            if not can_season:
                h = strip_season_button(h)
            charts.append({"cid": cid, "html": h, "js": j_code})

    return charts


# ============================================================
# 4. 页面组装
# ============================================================
THEMES_NI = {
    "2.1": ("盘面结构", "持仓/价/成交量，判断盘面波动是资金驱动还是现货驱动"),
    "2.2": ("现货与升贴水", "升贴水/基差，现货供需紧张程度是否领先期货"),
    "2.3": ("海外价格", "LME/COMEX，全球定价基准与海外资金参与度"),
    "2.4": ("价差体系", "月差/期限结构，判断 Back 还是 Contango"),
    "2.5": ("估值与利润", "分位数/冶炼利润，价格所处的历史估值位置"),
    "2.6": ("持仓席位观察", "多空前20，机构资金方向与多空博弈结构"),
    "3.1.1": ("海外镍矿产量", "印尼/菲律宾/新喀里多尼亚镍矿产量"),
    "3.1.2": ("海外精炼产量", "各国精炼镍产量与产能"),
    "3.1.3": ("国内产量", "中国精炼镍产量与结构"),
    "3.1.4": ("矿进口", "镍精矿进口总量与分国别结构"),
    "3.1.5": ("TC加工费", "镍精矿TC与分国别TC"),
    "3.2.1": ("精炼产量", "电解镍/镍铁/高冰镍产量"),
    "3.2.2": ("开工率", "电解镍/镍铁/硫酸镍开工率"),
    "3.2.3": ("再生供应", "再生镍产量与回收"),
    "3.2.4": ("冶炼利润", "各路线冶炼利润"),
    "4.1": ("交易所库存", "SHFE/LME 仓单与库存"),
    "4.2": ("仓单", "仓单总量与注销占比"),
    "4.3": ("社会库存", "社会库存总量与分地区"),
    "4.4": ("工厂库存", "厂内库存水平"),
    "4.5": ("隐性·在途", "隐性库存与在途量"),
    "5.1": ("初级消费", "不锈钢/电池/电镀开工率"),
    "5.2": ("终端消费", "终端产量"),
    "5.3": ("需求验证", "需求先行指标与价格联动"),
    "6.1": ("原料进口", "镍矿/镍生铁/高冰镍进口"),
    "6.2": ("精炼进出口", "电解镍/精炼镍进出口"),
    "6.3": ("制品出口", "不锈钢/镍制品出口"),
    "6.4": ("海外对华发运", "对华发运量"),
    "7.1": ("成本曲线", "各路线生产成本与分位"),
    "7.2": ("冶炼利润", "各路线冶炼利润"),
    "7.3": ("成本结构", "成本拆分与传导"),
}


def build_page(node, charts, dry=False):
    """组装 HTML 页面。返回 (filename, n_charts)"""
    theme = THEMES_NI.get(node, ("未知", ""))
    section = node.split(".")[0]
    section_name = SECTION_NAME.get(section, "")
    fname = "ni_%s.html" % node.replace(".", "_")

    # Chart HTML/JS
    all_html = "\n".join(c["html"] for c in charts)
    all_js = "\n".join(c["js"] for c in charts)

    # Nav/crumb
    nav_back = "ni_%s_overview.html" % section
    crumb = make_crumb([
        ("有色金属", "index.html"),
        ("镍(NI)", "ni_2_overview.html"),
        (section_name, nav_back),
        ("%s %s" % (node, theme[0]), "")
    ])

    note_html = (
        '<div class="chart-note" style="margin-bottom:16px;">'
        '<strong>%s · %s</strong><br>%s</div>'
    ) % (node, theme[0], theme[1])

    footer = (
        "有色金属产业指标树 · 镍(NI) %s %s · v2（归属优先 · %d 图）"
        " · indicators_v1.json v3.44"
    ) % (node, theme[0], len(charts))

    title_text = "镍(NI) %s %s · 有色金属研究框架" % (node, theme[0])

    html = page_html(
        title=title_text,
        h1=all_html,
        h2="",
        h3="",
        note_html=note_html,
        footer_text=footer,
        nav_back=nav_back,
        crumb_html=crumb,
        extra_js=all_js
    )

    if not dry:
        out_path = os.path.join(ROOT, fname)
        write_html(out_path, html)

    return (fname, len(charts))


# ============================================================
# 5. Schema 扩展
# ============================================================
def extend_schema(primary_map, indicators_dict):
    """为 indicators_v1.json 添加 5 个归属字段"""
    indicators = indicators_dict["indicators"]
    added = 0
    for node, mids in primary_map.items():
        board = node.split(".")[0]
        for mid in mids:
            if mid not in indicators:
                continue
            ind = indicators[mid]
            # Determine chart_role by position
            idx = mids.index(mid)
            role = "主图" if idx == 0 else ("普通" if idx < 4 else "补充")
            ind["variety"] = "NI"
            ind["board"] = board
            ind["node"] = node
            ind["chart_role"] = role
            ind["lifecycle"] = "active"
            # Clean old _nodes to just this node
            ind["_nodes"] = [node]
            added += 1
    return added


# ============================================================
# Main
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="镍 NI 批量重建引擎 v2")
    parser.add_argument("nodes", nargs="*", help="指定节点号")
    parser.add_argument("--dry", action="store_true", help="只打印计划")
    parser.add_argument("--assign", action="store_true", help="只做归属+写schema")
    args = parser.parse_args()

    # Load indicators
    json_path = os.path.join(ROOT, "data", "indicators_v1.json")
    with open(json_path, encoding="utf-8") as f:
        all_ind = json.load(f)

    indicators = all_ind["indicators"]

    # Step 1: Assign by prefix
    primary = assign_by_prefix(indicators)

    print("=== 归属分配（ID前缀 → 主节点）===")
    total_ind = 0
    for node in sorted(primary.keys(),
                       key=lambda x: [int(p) if p.isdigit() else 0
                                      for p in x.split('.')]):
        n = len(primary[node])
        total_ind += n
        print("  %s: %d indicators" % (node, n))
    print("  Total: %d indicators assigned\n" % total_ind)

    if args.assign:
        added = extend_schema(primary, all_ind)
        all_ind["version"] = "3.44"
        all_ind["updated"] = "2026-08-31"
        all_ind["change"] = "NI归属清洗：万金油消除，每指标归一节点"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_ind, f, ensure_ascii=False, indent=2)
        print("Schema extended: %d indicators updated → %s" % (added, json_path))
        return

    # Step 2: Parse divergence
    div_data = {}
    div_dir = os.path.join(ROOT, "analysis", "iwencai", "NI")
    for fname in sorted(os.listdir(div_dir)):
        if not fname.startswith("divergence_") or not fname.endswith(".md"):
            continue
        node = fname.replace("divergence_", "").replace(".md", "")
        div_data[node] = parse_divergence(node)

    # Step 3: Build pages
    target_nodes = args.nodes if args.nodes else sorted(primary.keys(),
        key=lambda x: [int(p) if p.isdigit() else 0 for p in x.split('.')])

    results = []
    for node in target_nodes:
        mids = primary.get(node, [])
        if not mids:
            print("SKIP %s: no indicators" % node)
            continue

        div_charts = div_data.get(node, [])
        charts = build_charts_for_node(node, mids, all_ind, div_charts)

        if not charts:
            print("SKIP %s: no buildable charts (%d indicators but data insufficient)"
                  % (node, len(mids)))
            continue

        if not args.dry:
            r = build_page(node, charts)
            results.append(r)
            print("OK %s → %s (%d charts from %d indicators)"
                  % (node, r[0], r[1], len(mids)))
        else:
            print("DRY %s: %d indicators → %d charts"
                  % (node, len(mids), len(charts)))

    if not args.dry:
        print("\n=== Summary ===")
        print("Built %d pages, total %d charts"
              % (len(results), sum(r[1] for r in results)))


if __name__ == "__main__":
    main()
